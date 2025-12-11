import sys
import rdflib
from rdflib.namespace import SKOS, RDF, DCTERMS
from jinja2 import Template

# Default paths (usati se non passati come argomenti)
DEFAULT_TTL_FILE = "eLTER_DRF.ttl"
DEFAULT_OUTPUT = "docs/index.html"

# Prende eventuali argomenti da CLI, altrimenti usa i default
ttl_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TTL_FILE
output_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT

g = rdflib.Graph()
g.parse(ttl_file, format="turtle")

SCHEMA = rdflib.Namespace("http://schema.org/")
POV = rdflib.Namespace("https://w3id.org/pov/")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
DWC = rdflib.Namespace("http://rs.tdwg.org/dwc/terms/")
UNIT = rdflib.Namespace("http://qudt.org/vocab/unit/")

# ----------------------------------------------------
# Load HTML template
# ----------------------------------------------------
with open("templates/page.html", "r") as f:
    template = Template(f.read())

# ----------------------------------------------------
# Extract ConceptScheme metadata
# ----------------------------------------------------
scheme = next(g.subjects(RDF.type, SKOS.ConceptScheme))

# Titolo: prova prima dct:title, se non c'è usa skos:prefLabel
scheme_title = g.value(scheme, DCTERMS.title)
if scheme_title is None:
    scheme_title = next(g.objects(scheme, SKOS.prefLabel))

scheme_desc = g.value(scheme, DCTERMS.description)
version = g.value(scheme, OWL.versionInfo)
creators = [str(c) for c in g.objects(scheme, DCTERMS.creator)]
contributors = [str(c) for c in g.objects(scheme, DCTERMS.contributor)]
created = g.value(scheme, DCTERMS.created)
modified = g.value(scheme, DCTERMS.modified)

# ----------------------------------------------------
# Languages detected
# ----------------------------------------------------
langs = sorted({
    label.language
    for _, _, label in g.triples((None, SKOS.prefLabel, None))
    if label.language
})

# ----------------------------------------------------
# Namespaces
# ----------------------------------------------------
namespaces = {p: str(u) for p, u in g.namespaces()}

# ----------------------------------------------------
# Extract top concepts (classes)
# ----------------------------------------------------
classes = []
for cls in g.objects(scheme, SKOS.hasTopConcept):
    label = next(g.objects(cls, SKOS.prefLabel))
    classes.append({
        "id": str(cls).split("/")[-1],
        "uri": str(cls),
        "label": str(label),
        "concepts": []  # verrà riempito dopo
    })


# ----------------------------------------------------
# Helper: breadcrumb (catena broader -> top concept)
# ----------------------------------------------------
def build_breadcrumb(concept):
    breadcrumb = []
    current = concept
    while True:
        label = next(g.objects(current, SKOS.prefLabel))
        breadcrumb.append({
            "id": str(current).split("/")[-1],
            "label": str(label)
        })
        broader = list(g.objects(current, SKOS.broader))
        if not broader:
            break
        current = broader[0]
    breadcrumb.reverse()
    return breadcrumb


# ----------------------------------------------------
# All concepts (base per "List of terms" e "Vocabulary")
# ----------------------------------------------------
all_concepts = []

for c in g.subjects(RDF.type, SKOS.Concept):
    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    broader = g.value(c, SKOS.broader)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)
    created_c = g.value(c, DCTERMS.created)
    modified_c = g.value(c, DCTERMS.modified)
    match = g.value(c, SKOS.closeMatch)

    breadcrumb = build_breadcrumb(c)

    all_concepts.append({
        "id": str(c).split("/")[-1],
        "uri": str(c),
        "label": str(label),
        "definition": str(definition) if definition else "",
        "example": str(example) if example else "",
        "broader": str(broader) if broader else "",
        "unit": str(unit) if unit else "",
        "created": str(created_c) if created_c else "",
        "modified": str(modified_c) if modified_c else "",
        "match": str(match) if match else "",
        "breadcrumb": breadcrumb
    })

# ----------------------------------------------------
# Map class → concepts using first breadcrumb element
# ----------------------------------------------------
class_map = {c["id"]: [] for c in classes}

for concept in all_concepts:
    if not concept["breadcrumb"]:
        continue
    top = concept["breadcrumb"][0]["id"]
    if top in class_map:
        class_map[top].append(concept)

# Attach mapped concepts to classes, ordinati per label
for cls in classes:
    cls_id = cls["id"]
    cls["concepts"] = sorted(
        class_map.get(cls_id, []),
        key=lambda x: x["label"].lower()
    )

# Full vocabulary sorted alphabetically (per sezione "3 Vocabulary")
vocabulary = sorted(all_concepts, key=lambda x: x["label"].lower())

# ----------------------------------------------------
# Render page
# ----------------------------------------------------
html = template.render(
    scheme_title=str(scheme_title),
    scheme_desc=str(scheme_desc or ""),
    version=str(version or ""),
    creators=", ".join(creators),
    contributors=", ".join(contributors),
    created=str(created or ""),
    modified=str(modified or ""),
    languages=langs,
    namespaces=namespaces,
    classes=classes,
    vocabulary=vocabulary
)

with open(output_file, "w") as f:
    f.write(html)

print(f"HTML written to {output_file}")
