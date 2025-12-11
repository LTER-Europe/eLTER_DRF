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
# Extract top concepts IN TTL ORDER
# ----------------------------------------------------

# 1. Read TTL as raw text
with open(TTL_FILE, "r") as f:
    ttl_raw = f.read()

import re

# 2. Regex to extract hasTopConcept URIs in correct order
pattern = r"skos:hasTopConcept\s+([^.;]+)"
matches = re.findall(pattern, ttl_raw)

top_concepts_ordered = []

for m in matches:
    # split by comma if multiple entries
    uris = re.findall(r"[\w:\/#.-]+", m)
    for u in uris:
        if u not in top_concepts_ordered:
            top_concepts_ordered.append(u)

# 3. Convert URIs or QNames to rdflib nodes
def resolve_node(u):
    try:
        return g.namespace_manager.compute_qname(u)[1]
    except:
        return rdflib.URIRef(u)

top_nodes = []
for item in top_concepts_ordered:
    if ":" in item and not item.startswith("http"):
        prefix, name = item.split(":")
        ns = dict(namespaces).get(prefix)
        if ns:
            top_nodes.append(rdflib.URIRef(ns + name))
        else:
            top_nodes.append(rdflib.URIRef(item))
    else:
        top_nodes.append(rdflib.URIRef(item))

# 4. Build class objects in this EXACT order
classes = []
for cls in top_nodes:
    if (cls, RDF.type, SKOS.Concept) in g:
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
    unit = g.value(c, SCHEMA.unitCode) or g.value(c, POV.unit)
    creat = g.value(c, DCTERMS.created)
    modif = g.value(c, DCTERMS.modified)
    match = g.value(c, SKOS.closeMatch)

    # ------------------------------------------
    # Broader concept (URI + link interno)
    # ------------------------------------------
    broader_node = g.value(c, SKOS.broader)

    if broader_node:
        broader_label = localname(broader_node)
        broader_uri = str(broader_node)
        broader_anchor = f"#class-{broader_label}"
    else:
        broader_label = "-"
        broader_uri = "-"
        broader_anchor = "-"

    # ------------------------------------------
    # Breadcrumb HTML
    # ------------------------------------------
    breadcrumb = build_breadcrumb(c)

    breadcrumb_html = " / ".join(
        f'<a href="#class-{item["id"]}">{item["label"]}</a>'
        for item in breadcrumb
    )

    # ------------------------------------------
    # Append concept object
    # ------------------------------------------
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

        # NEW broader fields
        "broader_label": broader_label,
        "broader_uri": broader_uri,
        "broader_anchor": broader_anchor,

        # breadcrumb
        "breadcrumb_html": breadcrumb_html
    })


# ----------------------------------------------------
# Map concepts to each class (first breadcrumb element)
# ----------------------------------------------------

class_map = {c["id"]: [] for c in classes}

for c in g.subjects(RDF.type, SKOS.Concept):

    breadcrumb = build_breadcrumb(c)
    if not breadcrumb:
        continue

    top = breadcrumb[0]["id"]  # id della classe (top concept)

    # Trova il record del concept dentro all_concepts
    cid = localname(c)
    concept_rec = next((x for x in all_concepts if x["id"] == cid), None)

    if concept_rec and top in class_map:
        class_map[top].append(concept_rec)

# Attach to classes
for cls in classes:
    cls_id = cls["id"]
    cls["concepts"] = class_map.get(cls_id, [])


# ----------------------------------------------------
# Organize vocabulary into Classes and Concepts
# ----------------------------------------------------

# "Classes" = top concepts
vocabulary_classes = []
for cls in classes:
    definition = g.value(cnode, SKOS.definition)
    match = g.value(cnode, SKOS.closeMatch)

    vocabulary_classes.append({
        "id": cls["id"],
        "uri": cls["uri"],
        "label": cls["label"],
        "definition": str(definition or "-"),
        "match": str(match or "-")
    })

# "Concepts" = all_concepts except classes
vocabulary_concepts = [
    c for c in all_concepts
    if c["id"] not in {cls["id"] for cls in classes}
]

# Sort both lists
vocabulary_classes = classes
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
