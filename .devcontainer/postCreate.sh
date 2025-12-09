#!/bin/bash
set -euxo pipefail

# Name of the TTL file in the repository (change if needed)
FILE_NAME="${FILE_NAME:-eLTER_DRF}"

# Remove the "ready" flag
rm -f /workspaces/.postcreate_done

# --- Clone or reset Skosmos ---------------------------------------------------
if [ ! -d "skosmos-src" ]; then
  git clone --depth 1 https://github.com/NatLibFi/Skosmos.git skosmos-src
else
  git -C skosmos-src restore -- dockerfiles/config/config-docker-compose.ttl
  rm -f skosmos-src/dockerfiles/config/config-docker-compose.ttl.bak
fi

# --- Compute baseHref from Codespace name -------------------------------------
BASEHREF="https://${CODESPACE_NAME//_/-}-9090.app.github.dev/"

# Generate the vocabulary block for Skosmos
# (use your custom script if present, otherwise comment this line)
python src/generate_vocab_block.py "./${FILE_NAME}.ttl" > /tmp/vocab-block.ttl

# Update the baseHref in Skosmos configuration
sed -i.bak \
  -e 's|^[[:space:]]*# *skosmos:baseHref "http://localhost/Skosmos/" ;|    skosmos:baseHref "'"${BASEHREF}"'" ;|' \
  skosmos-src/dockerfiles/config/config-docker-compose.ttl

# Remove demo vocabularies (UNESCO and STW)
sed -i.bak -e '/^:unesco /,/^ *\.$/d' -e '/^:stw /,/^ *\.$/d' skosmos-src/dockerfiles/config/config-docker-compose.ttl

# Append your vocabulary block
cat /tmp/vocab-block.ttl >> skosmos-src/dockerfiles/config/config-docker-compose.ttl

# --- Ensure Docker is ready ---------------------------------------------------
ensure_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo "[INFO] Starting Docker daemon…"
    sudo /usr/local/share/docker-init.sh || true
  fi
  for i in {1..90}; do
    if docker info >/dev/null 2>&1; then
      echo "[INFO] Docker is ready."
      return 0
    fi
    echo "[INFO] Waiting for Docker…"
    sleep 1
  done
  echo "[ERROR] Docker daemon did not become ready."
  ps -ef | grep -E '[d]ockerd' || true
  sudo tail -n 200 /var/log/dockerd.log 2>/dev/null || true
  exit 1
}

ensure_docker

# --- Start Skosmos with Docker Compose ----------------------------------------
for a in 1 2 3; do
  if docker compose -f skosmos-src/docker-compose.yml up -d --build; then
    break
  fi
  echo "[WARN] docker compose failed (attempt $a), retrying in 3s…"
  sleep 3
  ensure_docker
done

# --- Wait until the SPARQL endpoint is ready ---------------------------------
for i in {1..60}; do
  if curl -sS -G 'http://localhost:9030/skosmos/sparql' \
    --data-urlencode 'query=ASK{}' \
    -H 'Accept: text/boolean' -o /dev/null; then
    break
  fi
  echo "[INFO] Waiting for SPARQL endpoint…"
  sleep 1
done

# --- Load the TTL file into the graph ----------------------------------------
if [ ! -f "${FILE_NAME}.ttl" ]; then
  echo "[ERROR] TTL file not found: ${FILE_NAME}.ttl"
  exit 1
fi

curl --retry 6 --retry-delay 2 --retry-connrefused -sSf \
  -X PUT -H "Content-Type: text/turtle;charset=utf-8" \
  --data-binary @"${FILE_NAME}.ttl" \
  "http://localhost:9030/skosmos/data?graph=http://example.org/graph/dev"

# --- Signal successful completion ---------------------------------------------
touch /workspaces/.postcreate_done
echo "[OK] postCreate finished, Skosmos should be available."

# Automatically run postAttach after creation
bash /workspaces/.devcontainer/postAttach.sh || true
