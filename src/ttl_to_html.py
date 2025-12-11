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
# Extract localname robustly from URI
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
# Load HTML template
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

# ----------------------------------------------------
# Extract classes (SKOS top concepts) — IN ORDER OF APPEARANCE
# ----------------------------------------------------
classes = []
for cls in g.objects(scheme, SKOS.hasTopConcept):
    label = next(g.objects(cls, SKOS.prefLabel))
    classes.append({
        "id": localname(cls),
        "uri": str(cls),
        "label": str(label),
        "definition": str(g.value(cls, SKOS.definition) or "-"),
        "match": str(g.value(cls, SKOS.closeMatch) or "-"),
        "concepts": []
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
# Extract all concepts (supporting multi-broader)
# ----------------------------------------------------
all_concepts = []

for c in g.subjects(RDF.type, SKOS.Concept):

    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    creat = g.value(c, DCTERMS.created)
    modif = g.value(c, DCTERMS.modified)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)
    match = g.value(c, SKOS.closeMatch)

    breadcrumb = build_breadcrumb(c)

    # -------- MULTI-BROADER SUPPORT --------
    broader_nodes = list(g.objects(c, SKOS.broader))
    broaders = []
    for b in broader_nodes:
        broaders.append({
            "id": bid,
            "label": label,
            "uri": uri,
            "anchor": f"#vclass-{bid}"
        })

    # Breadcrumb HTML
    breadcrumb_html = " / ".join(
        f'<a href="#class-{item["id"]}">{item["label"]}</a>'
        for item in breadcrumb
    )

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
        "breadcrumb_html": breadcrumb_html,
        "broaders": broaders
    })

# ----------------------------------------------------
# Map concepts to each class (first breadcrumb element)
# ----------------------------------------------------
class_map = {c["id"]: [] for c in classes}

for concept in all_concepts:
    top = concept["breadcrumb_html"].split('">')[1].split("<")[0] \
          if concept["breadcrumb_html"] else None

    # top = first breadcrumb element id
    if concept["broaders"]:
        # NO: broader ≠ class membership
        pass

    if concept["breadcrumb_html"]:
        first_id = concept["breadcrumb_html"].split('href="#class-')[1].split('"')[0]
        if first_id in class_map:
            class_map[first_id].append(concept)

# Apply sorted concepts to classes
for cls in classes:
    cls["concepts"] = sorted(class_map.get(cls["id"], []), key=lambda x: x["label"].lower())

# Vocabulary lists
vocabulary_classes = classes
vocabulary_concepts = sorted(all_concepts, key=lambda x: x["label"].lower())

# ----------------------------------------------------
# Render HTML
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

print("HTML written to", OUTPUT)
