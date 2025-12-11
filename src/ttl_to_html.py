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

# ---------------------------------------------
# Utility: extract local name
# ---------------------------------------------
def localname(uri):
    uri = str(uri)
    if "#" in uri:
        return uri.split("#")[-1]
    if "/" in uri:
        return uri.split("/")[-1]
    return uri

# ---------------------------------------------
# Load HTML template
# ---------------------------------------------
with open("templates/page.html", "r") as f:
    template = Template(f.read())

# ---------------------------------------------
# ConceptScheme metadata
# ---------------------------------------------
scheme = next(g.subjects(RDF.type, SKOS.ConceptScheme))
scheme_title = next(g.objects(scheme, SKOS.prefLabel))
scheme_desc = g.value(scheme, DCTERMS.description)
version = g.value(scheme, OWL.versionInfo)
creators = [str(c) for c in g.objects(scheme, DCTERMS.creator)]
contributors = [str(c) for c in g.objects(scheme, DCTERMS.contributor)]
created = g.value(scheme, DCTERMS.created)
modified = g.value(scheme, DCTERMS.modified)

# ---------------------------------------------
# Namespaces — FIXED LIST
# ---------------------------------------------
namespaces = {
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dct": "http://purl.org/dc/terms/",
    "dwc": "http://rs.tdwg.org/dwc/terms/",
    "omv": "http://omv.ontoware.org/2005/05/ontology",
    "puv": "https://w3id.org/env/puv#",
    "qudt": "http://qudt.org/vocab/",
    "unit": "http://qudt.org/vocab/unit/"
}

# ---------------------------------------------
# CLASSES = skos:Collection (ORDER OF APPEARANCE)
# ---------------------------------------------
classes = []

for cls in g.subjects(RDF.type, SKOS.Collection):
    label = g.value(cls, SKOS.prefLabel)
    definition = g.value(cls, SKOS.definition)
    match = g.value(cls, SKOS.closeMatch)

    classes.append({
        "id": localname(cls),
        "uri": str(cls),
        "label": str(label),
        "definition": str(definition or "-"),
        "match": str(match or "-"),
        "concepts": []
    })

# ---------------------------------------------
# Extract concepts
# ---------------------------------------------
all_concepts = []

for c in g.subjects(RDF.type, SKOS.Concept):

    label = g.value(c, SKOS.prefLabel)
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    creat = g.value(c, DCTERMS.created)
    modif = g.value(c, DCTERMS.modified)
    match = g.value(c, SKOS.closeMatch)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)

    # Multi-broader
    broader_nodes = list(g.objects(c, SKOS.broader))
    broaders = [{
        "id": localname(b),
        "label": localname(b),
        "uri": str(b),
        "anchor": f"#vclass-{localname(b)}"
    } for b in broader_nodes]

    all_concepts.append({
        "id": localname(c),
        "uri": str(c),
        "label": str(label),
        "definition": str(definition or "-"),
        "example": str(example or "-"),
        "unit": str(unit or "-"),
        "creat": str(creat or "-"),
        "modif": str(modif or "-"),
        "match": str(match or "-"),
        "broaders": broaders
    })

# ---------------------------------------------
# Assign concepts to classes (via skos:narrower)
# ---------------------------------------------
class_dict = {cls["id"]: cls for cls in classes}

for cls in classes:
    cls_uri = rdflib.URIRef(cls["uri"])

    for narrower in g.objects(cls_uri, SKOS.narrower):
        nid = localname(narrower)

        for concept in all_concepts:
            if concept["id"] == nid:
                cls["concepts"].append(concept)

# keep class order, keep insertion order of concepts
for cls in classes:
    cls["concepts"].sort(key=lambda x: x["label"].lower())

# ---------------------------------------------
# Vocabulary lists
# ---------------------------------------------
vocabulary_classes = classes
vocabulary_concepts = sorted(all_concepts, key=lambda x: x["label"].lower())

# ---------------------------------------------
# Render HTML
# ---------------------------------------------
html = template.render(
    scheme_title=str(scheme_title),
    scheme_desc=str(scheme_desc or ""),
    version=str(version or ""),
    creators=", ".join(creators),
    contributors=", ".join(contributors),
    created=str(created or ""),
    modified=str(modified or ""),
    namespaces=namespaces,
    classes=classes,
    vocabulary_classes=vocabulary_classes,
    vocabulary_concepts=vocabulary_concepts
)

with open(OUTPUT, "w") as f:
    f.write(html)

print("HTML written to", OUTPUT)
