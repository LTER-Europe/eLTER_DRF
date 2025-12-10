import rdflib
from rdflib.namespace import SKOS, RDF, DCTERMS
from jinja2 import Template

TTL_FILE = "eLTER_DRF.ttl"
OUTPUT = "docs/index.html"

g = rdflib.Graph()
g.parse(TTL_FILE, format="turtle")

SCHEMA = rdflib.Namespace("http://schema.org/")
POV = rdflib.Namespace("https://w3id.org/pov/")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")

# ----------------------------------------------------
# Load HTML template
# ----------------------------------------------------
with open("templates/page.html", "r") as f:
    template = Template(f.read())

# ----------------------------------------------------
# Extract ConceptScheme metadata
# ----------------------------------------------------
scheme = next(g.subjects(RDF.type, SKOS.ConceptScheme))

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
        "concepts": []     # verrà riempito dopo
    })

# Helper: build breadcrumb
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

# All concepts
all_concepts = []
for c in g.subjects(RDF.type, SKOS.Concept):
    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    broader = g.value(c, SKOS.broader)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)

    breadcrumb = build_breadcrumb(c)

    all_concepts.append({
        "id": str(c).split("/")[-1],
        "uri": str(c),
        "label": str(label),
        "definition": str(definition or ""),
        "example": str(example or ""),
        "broader": str(broader) if broader else "",
        "unit": str(unit or ""),
        "breadcrumb": breadcrumb
    })

# Map class → concepts using breadcrumb[0]
class_map = {c["id"]: [] for c in classes}

for concept in all_concepts:
    if not concept["breadcrumb"]:
        continue

    top = concept["breadcrumb"][0]["id"]
    if top in class_map:
        class_map[top].append(concept)

# Attach mapped concepts to classes
for cls in classes:
    cls_id = cls["id"]
    cls["concepts"] = sorted(class_map.get(cls_id, []), key=lambda x: x["label"].lower())

# Full vocabulary sorted alphabetically
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

with open(OUTPUT, "w") as f:
    f.write(html)

print(f"HTML written to {OUTPUT}")
