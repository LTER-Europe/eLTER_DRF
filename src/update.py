import os
import requests

FILE_NAME = os.environ['FILE_NAME']

RENDERING_UPDATE = """@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix schema: <http://schema.org/>.
@prefix iop:   <https://w3id.org/iadopt/ont/> .
@prefix puv: <https://w3id.org/env/puv#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix dwc: <http://rs.tdwg.org/dwc/terms/> .
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix qudt: <http://qudt.org/vocab/> .
@prefix drf: <http://vocabs.lter-europe.net/elter_drf/> .

puv:uom
  a owl:ObjectProperty ;
  rdfs:comment "scale or unit of measurement" ;
  rdfs:label "unit-of-measurement " ;
  rdfs:range puv:UnitOfMeasurement .
"""

vocab_file = open(f"./{FILE_NAME}.ttl", "r")
vocab = vocab_file.read()
vocab_file.close()

vocab = vocab.replace("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .", RENDERING_UPDATE)

vocab_file = open(f"./{FILE_NAME}.ttl", "w")
vocab_file.write(vocab)
vocab_file.close()
