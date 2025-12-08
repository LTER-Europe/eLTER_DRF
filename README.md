# 🧩 eLTER-RI Controlled Vocabulary – Field Specification Vocabulary for the Data Reporting Format (DRF)

[![FAIR RDF Generation](https://github.com/LTER-Europe/elter_cl/actions/workflows/sheet2rdf.yml/badge.svg?branch=main)](https://github.com/LTER-Europe/elter_cl/actions/workflows/sheet2rdf.yml)

The **DRF Field Specification Vocabulary** defines the controlled set of fields used in the **eLTER Data fields specification**.
It provides a harmonised and machine-actionable reference for describing the structure, meaning, and expected content of each field included in eLTER Data fields specification data products.

This vocabulary supports **semantic interoperability** across eLTER data workflows by ensuring that eLTER Data fields specification fields—such as identifiers, taxonomic information, temporal and spatial attributes, methodological descriptors, and measurement characteristics—are used consistently across sites, domains, and data providers

📘 **Vocabulary access:** [https://vocabs.lter-europe.net/...](https://vocabs.lter-europe.net/.../en/)

---

## ⚙️ Automated FAIR Workflow — *sheet2rdf*

This repository is automatically updated through the [**sheet2rdf**](https://github.com/nikokaoja/sheet2rdf) workflow, which ensures that the vocabulary remains FAIR and synchronised with its authoritative Google Sheet source.

The workflow automatically:

1. Fetches the Google Sheet source as `.xlsx` and `.csv` files  
2. Converts the sheet to RDF (Turtle) using [**xls2rdf**](https://github.com/sparna-git/xls2rdf)  
3. Commits the generated `.ttl`, `.xlsx`, and log files to this repository  
4. Publishes the resulting RDF to the [**Skosmos vocabulary server**](https://vocabs.lter-europe.net)

This workflow extends [**excel2rdf**](https://github.com/fair-data-collective/excel2rdf-template) and is licensed under the [Apache 2.0 License](https://github.com/nikokaoja/sheet2rdf/blob/main/License.md).

🧾 **Workflow provenance:**  
> This file has been modified from its originally licensed version by *WillOnGit* – see [README.md](https://github.com/LTER-Europe/CL) at repository root for license information.

📚 **Citation:**  
> Nikola Vasiljevic. (2021, January 11). *sheet2rdf: First release* (Version v0.1). Zenodo. [https://doi.org/10.5281/zenodo.4432136](https://doi.org/10.5281/zenodo.4432136)

---

## 🧠 Repository contents

| File | Description |
|------|--------------|
| [elter_drf.ttl](https://github.com/LTER-Europe/eLTER_DRF/blob/main/elter_drf.ttl) | RDF (Turtle) representation of the eLTER Field Specification Vocabulary for the Data Reporting Format |
| [elter_cl.xlsx](https://github.com/LTER-Europe/eLTER_DRF/blob/main/elter_drf.xlsx) | Source spreadsheet fetched from Google Sheets |
| [elter_cl.csv](https://github.com/LTER-Europe/eLTER_DRF/blob/main/elter_drf.csv) | CSV export of the vocabulary |
| [logs/](https://github.com/LTER-Europe/eLTER_DRF/tree/main/logs) | Conversion logs produced during RDF generation |
| [.github/workflows/sheet2rdf.yml](https://github.com/LTER-Europe/eLTER_CL/blob/main/.github/workflows/sheet2rdf.yml) | GitHub Action workflow automating the FAIR publication process |

---

## 🧭 Acknowledgements

This work builds on the efforts of the [eLTER-RI](https://elter-ri.eu/) communities, with support from multiple projects contributing to the development of interoperable and FAIR semantic resources for environmental research infrastructures.

---

## 💡 Related vocabularies

| Vocabulary | Description | Access |
|-------------|--------------|--------|
| **[SO – Standard Observations](https://github.com/LTER-Europe/SO)** | Controlled vocabulary describing eLTER Standard Observations (SOs) variables, methods, and protocols | [View in Skosmos](https://vocabs.lter-europe.net/so/en/) |
| **[EnvThes – Environmental Thesaurus](https://github.com/LTER-Europe/EnvThes)** | Common semantic framework for environmental parameters and concepts | [View in Skosmos](https://vocabs.elter-ri.eu/EnvThes/en/) |
| **[CL – Controlled Lists](https://github.com/LTER-Europe/eLTER_CL)** | Standardised lists of values used across eLTER metadata systems | [View in Skosmos](https://vocabs.lter-europe.net/cl/en/) |
