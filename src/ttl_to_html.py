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
DWC = rdflib.Namespace("http://rs.tdwg.org/dwc/terms/")


# ----------------------------------------------------
# Extract localname robustly from URI or QNAME
# ----------------------------------------------------
def localname(uri):
    uri = str(uri)
    if "#" in uri:
        return uri.split("#")[-1]
    if "/" in uri:
        return uri.split("/")[-1]
    if ":" in uri:
        return uri.split(":")[-1]
    return uri


# ----------------------------------------------------
# Load template
# ----------------------------------------------------
with open("templates/page.html", "r") as f:
    template = Template(f.read())


# ----------------------------------------------------
# ConceptScheme metadata
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
# Languages
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
# Extract classes (SKOS top concepts)
# ----------------------------------------------------
classes = []
for cls in g.objects(scheme, SKOS.hasTopConcept):
    label = next(g.objects(cls, SKOS.prefLabel))
    classes.append({
        "id": localname(cls),
        "uri": str(cls),
        "label": str(label),
        "concepts": [],
        "definition": str(g.value(cls, SKOS.definition) or "-"),
        "match": str(g.value(cls, SKOS.closeMatch) or "-")
    })


# ----------------------------------------------------
# Breadcrumb builder
# ----------------------------------------------------
def build_breadcrumb(concept):
    breadcrumb = []
    current = concept
    while True:
        label = next(g.objects(current, SKOS.prefLabel))
        breadcrumb.append({
            "id": localname(current),
            "label": str(label)
        })
        broader = list(g.objects(current, SKOS.broader))
        if not broader:
            break
        current = broader[0]
    breadcrumb.reverse()
    return breadcrumb


# ----------------------------------------------------
# Extract all concepts
# ----------------------------------------------------
all_concepts = []
for c in g.subjects(RDF.type, SKOS.Concept):

    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    broader = g.value(c, SKOS.broader)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)
    creat = g.value(c, DCTERMS.created)
    modif = g.value(c, DCTERMS.modified)
    match = g.value(c, SKOS.closeMatch)

    breadcrumb = build_breadcrumb(c)

    # Build broader anchor link
    broader_local = localname(broader) if broader else "-"
    broader_anchor = f"#class-{broader_local}" if broader else "-"

    all_concepts.append({
        "id": localname(c),
        "uri": str(c),
        "label": str(label),
        "definition": str(definition or "-"),
        "example": str(example or "-"),
        "broader": broader_anchor,
        "broader_label": broader_local,
        "unit": str(unit or "-"),
        "creat": str(creat or "-"),
        "modif": str(modif or "-"),
        "match": str(match or "-"),
        "breadcrumb": breadcrumb
    })


# ----------------------------------------------------
# Map concepts to each class (first breadcrumb element)
# ----------------------------------------------------
class_map = {c["id"]: [] for c in classes}

for concept in all_concepts:
    if not concept["breadcrumb"]:
        continue
    top = concept["breadcrumb"][0]["id"]
    if top in class_map:
        class_map[top].append(concept)

# Attach to classes
for cls in classes:
    cls_id = cls["id"]
    cls["concepts"] = sorted(class_map.get(cls_id, []), key=lambda x: x["label"].lower())


# ----------------------------------------------------
# Vocabulary (concepts + classes)
# ----------------------------------------------------
vocabulary_classes = sorted(classes, key=lambda x: x["label"].lower())
vocabulary_concepts = sorted(all_concepts, key=lambda x: x["label"].lower())


# ----------------------------------------------------
# Render
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
    vocabulary_classes=vocabulary_classes,
    vocabulary_concepts=vocabulary_concepts
)

with open(OUTPUT, "w") as f:
    f.write(html)

print(f"HTML written to", OUTPUT)
