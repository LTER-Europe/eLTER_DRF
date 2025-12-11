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
# Extract CLASSES = SKOS:Collection in TTL ORDER
# ----------------------------------------------------

# Read TTL raw to preserve order
with open(TTL_FILE, "r") as f:
    ttl_raw = f.read()

import re

# Find all SKOS:Collection declarations in TTL order
collection_pattern = r"(\w+:\w+)\s+a\s+skos:Collection"
collections_in_order = re.findall(collection_pattern, ttl_raw)

classes = []

for qname in collections_in_order:
    prefix, name = qname.split(":")
    ns = dict(namespaces).get(prefix)
    if not ns:
        continue

    uri = rdflib.URIRef(ns + name)

    label = g.value(uri, SKOS.prefLabel)
    definition = g.value(uri, SKOS.definition)
    match = g.value(uri, SKOS.closeMatch)

    classes.append({
        "id": name,
        "uri": str(uri),
        "label": str(label or name),
        "definition": str(definition or "-"),
        "match": str(match or "-"),
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
# Extract all concepts
# ----------------------------------------------------
all_concepts = []

for c in g.subjects(RDF.type, SKOS.Concept):

    label = next(g.objects(c, SKOS.prefLabel))
    definition = g.value(c, SKOS.definition)
    example = g.value(c, SKOS.example)
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)
    creat = g.value(c, DCTERMS.created)
    modif = g.value(c, DCTERMS.modified)
    match = g.value(c, SKOS.closeMatch)

    # MULTI-BROADER SUPPORT
    broaders = []
    for b in g.objects(c, SKOS.broader):
        b_id = localname(b)
        broaders.append({
            "id": b_id,
            "uri": str(b),
            "anchor": f"#class-{b_id}"
        })

    # Breadcrumb
    breadcrumb = build_breadcrumb(c)
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
        "broaders": broaders,
        "breadcrumb_html": breadcrumb_html,
        "breadcrumb": breadcrumb
    })


# ----------------------------------------------------
# Map concepts to SKOS:Collections via skos:broader
# ----------------------------------------------------

# Create mapping class_id → list of concepts
class_map = {cls["id"]: [] for cls in classes}

for c in g.subjects(RDF.type, SKOS.Concept):

    cid = localname(c)
    concept_rec = next((x for x in all_concepts if x["id"] == cid), None)
    if not concept_rec:
        continue

    # For each broader, check if it's a class
    for b in g.objects(c, SKOS.broader):
        bid = localname(b)
        if bid in class_map:
            class_map[bid].append(concept_rec)

# Attach concepts to class objects
for cls in classes:
    cls["concepts"] = class_map.get(cls["id"], [])


# ----------------------------------------------------
# Organize vocabulary
# ----------------------------------------------------

vocabulary_classes = classes

# Concepts = all SKOS:Concept NOT classes
class_ids = {cls["id"] for cls in classes}

vocabulary_concepts = [
    c for c in all_concepts if c["id"] not in class_ids
]

# Sort concepts alphabetically
vocabulary_concepts = sorted(vocabulary_concepts, key=lambda x: x["label"].lower())

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
    vocabulary_classes=vocabulary_classes,
    vocabulary_concepts=vocabulary_concepts
)

with open(OUTPUT, "w") as f:
    f.write(html)

print(f"HTML written to", OUTPUT)
