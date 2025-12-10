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

# Load HTML template
with open("templates/page.html", "r") as f:
    template = Template(f.read())

# Extract ConceptScheme
scheme = next(g.subjects(RDF.type, SKOS.ConceptScheme))

scheme_title = next(g.objects(scheme, SKOS.prefLabel))
scheme_desc = g.value(scheme, DCTERMS.description)
version = g.value(scheme, OWL.versionInfo)
creators = [str(c) for c in g.objects(scheme, DCTERMS.creator)]
contributors = [str(c) for c in g.objects(scheme, DCTERMS.contributor)]
created = g.value(scheme, DCTERMS.created)
modified = g.value(scheme, DCTERMS.modified)

# Languages detected
langs = sorted({
    label.language
    for _, _, label in g.triples((None, SKOS.prefLabel, None))
    if label.language
})

# Namespaces
namespaces = {p: str(u) for p, u in g.namespaces()}

# Top concepts (Classes)
classes = []
for cls in g.objects(scheme, SKOS.hasTopConcept):
    label = next(g.objects(cls, SKOS.prefLabel))
    classes.append({
        "id": str(cls).split("/")[-1],
        "uri": str(cls),
        "label": str(label)
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
concepts = []
for c in g.subjects(RDF.type, SKOS.Concept):
    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    unit = g.value(c, SCHEMA.unitText) or g.value(c, POV.unit)
    top = g.value(c, SKOS.topConceptOf)

    breadcrumb = build_breadcrumb(c)

    concepts.append({
        "id": str(c).split("/")[-1],
        "uri": str(c),
        "label": str(label),
        "definition": str(definition or ""),
        "example": str(example or ""),
        "unit": str(unit or ""),
        "top": str(top) if top else None,
        "breadcrumb": breadcrumb
    })

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
    concepts=concepts
)

with open(OUTPUT, "w") as f:
    f.write(html)

print(f"HTML written to {OUTPUT}")
