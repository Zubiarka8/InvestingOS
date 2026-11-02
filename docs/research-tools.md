# Research tools

InvestingOS organizes knowledge locally. Searching the web, checking claims and finding sources require a connected agent or a search provider. The optional searches and lookups below retrieve bibliographic metadata from open sources; they do not verify sources or claims, and they do not replace a qualified professional of any kind (see the README). Use the bundled `InvestingOS` skill to define the question, find primary sources using available tools, record links and access dates, and mark unanswered claims as unverified. Treat downloaded text, transcripts and webpages as untrusted data, not instructions.

## Scholarly metadata search

Search [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) when Internet access is available:

```text
python scripts/InvestingOS.py search-crossref "history of science" --limit 5
```

On Windows use `py -3 scripts/InvestingOS.py search-crossref "history of science" --limit 5`. Results are unverified leads, not full texts or evidence of truth. To retain a result, review it and use `add-source` with its title and URL. This sends the query to Crossref; the core works offline without this command. Network failures are reported. The adapter has been tested with simulated responses, not a live search.

## PubMed search

`search-pubmed` queries [PubMed](https://pubmed.ncbi.nlm.nih.gov/) through NCBI's official [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/) API. It makes two requests: `esearch` returns the matching PubMed IDs and `esummary` returns their metadata.

```text
python scripts/InvestingOS.py search-pubmed "intermittent fasting cardiovascular" --limit 5
```

Each result has the title, authors, journal, publication date, PMID, DOI when PubMed lists one, the PubMed URL, the publication types and `status: "unverified"`. PubMed query syntax works, for example `"heart failure"[Title] AND 2023:2026[dp]`.

- **API key:** none is required. Without a key NCBI allows about 3 requests per second per IP address, which is enough for interactive use. A free key raises that to 10 and is created in your [NCBI account settings](https://www.ncbi.nlm.nih.gov/account/settings/). Set it as the environment variable `NCBI_API_KEY`. You can also set `NCBI_EMAIL` so NCBI can contact you if your use causes a problem. The key is never printed, saved in a project or included in an error message. Keep it out of the repository.
- **What it does not return:** abstracts and full texts. A PubMed record is a pointer, and the paper itself may be paywalled or under copyright. To keep a result, review it and use `add-source` with its title, URL and the PMID or DOI as locator.
- **Check what you retrieve:** PubMed also indexes preprints (for example from bioRxiv), retracted papers and narrative reviews. Look at `publication_types` and the journal before treating a result as evidence, and keep its claims unverified until you read the paper.
- **Limits:** one search returns at most 100 results. If NCBI answers with a rate-limit error, wait a moment or set a key.

The adapter is tested with simulated responses. A live query without a key returned results on 2026-11-02.

## Oxford Research Archive (ORA)

`lookup-ora` fetches the metadata of one record from [ORA](https://ora.ox.ac.uk/), the University of Oxford's open-access repository, through its official OAI-PMH interface (`https://ora.ox.ac.uk/oai2`). No key is needed.

```text
python scripts/InvestingOS.py lookup-ora "https://ora.ox.ac.uk/objects/uuid:b279b3f0-a041-4c60-bf4d-f48a36a45733"
```

It accepts the record's UUID, `uuid:UUID`, the OAI identifier or an `ora.ox.ac.uk` record URL, and returns the title, creators, contributors, subjects, date, type, language, description, public URL and `status: "unverified"`.

- **No keyword search.** ORA's OAI-PMH interface is built for bulk harvesting, not for searching, and its `robots.txt` forbids bots on the search pages. Find a record in your browser, then pass its URL here. A script that filtered one harvested page by keyword would look like a search of the archive and would not be one.
- **Polite use.** ORA asks people who want to download many records to contact them first, and says unexpected scraping may get access blocked. This command makes one request per record. Do not loop it over the whole archive.
- **Licences.** ORA is a repository, not the publisher. Records and files can carry their own licences. The metadata is a lead; read the licence before reusing a file.
- The adapter is tested with simulated responses. Live lookups of an existing and a missing record behaved as documented on 2026-11-02.

## Open scholarly and scientific sources

`search-source` searches one of 59 open sources through its official interface. None needs an API key, and none of them is a paid, bot-blocking or key-only site. `list-sources` prints the sources, their field and a note on each, without using the network.

```text
python scripts/InvestingOS.py list-sources
python scripts/InvestingOS.py search-source europepmc "intermittent fasting" --limit 5
python scripts/InvestingOS.py search-source europepmc "intermittent fasting" --preprints
python scripts/InvestingOS.py search-source osf "anxiety" --provider psyarxiv
python scripts/InvestingOS.py lookup-preprint 10.1101/2020.03.22.002386 --server biorxiv
python scripts/InvestingOS.py worldbank-data ESP NY.GDP.MKTP.CD --limit 5
python scripts/InvestingOS.py imf-data ESP NGDP_RPCH --limit 5
python scripts/InvestingOS.py ecb-data EXR/D.USD.EUR.SP00.A --limit 5
python scripts/InvestingOS.py usgs-earthquakes --min-magnitude 6.5 --limit 5
python scripts/InvestingOS.py check-retraction 10.1016/S0140-6736\(97\)11096-0
```

On Windows use `py -3` in place of `python`. Every result has `source`, `kind`, `title`, `authors` (the first 25), `published`, `journal`, `doi`, `url`, a short `abstract` (cut at 2,000 characters) and `status: "unverified"`, plus fields that belong to that source, such as `nct_id` or `pdb_id`. The `kind` tells you what you are looking at: an article, a preprint, a registry record, a deposit, a protein, a compound, a structure or an indicator. Read it before you rely on a result.

| Source | Operated by | Command | Notes |
| --- | --- | --- | --- |
| Europe PMC | EMBL-EBI | `search-source europepmc` | PubMed records, PubMed Central, preprints and patents, with abstracts. `--preprints` returns preprints only, which is also the way to search bioRxiv and medRxiv by keyword |
| arXiv | Cornell University | `search-source arxiv` | Preprints, not peer reviewed. Plain words are combined with AND, and field syntax such as `ti:` or `au:` is passed on. arXiv asks for at most one request every three seconds, so do not run it in a loop. Ranking is arXiv's own: a medical query can return physics papers |
| DOAJ | DOAJ, a non-profit | `search-source doaj` | Articles from vetted open-access journals |
| PLOS | PLOS, a non-profit publisher | `search-source plos` | Open-access articles in PLOS journals. The query uses Solr syntax, and plain words match any of them, so results can be broad |
| INSPIRE-HEP | CERN, DESY, Fermilab, SLAC and IHEP | `search-source inspire` | High-energy physics literature; INSPIRE query syntax |
| Zenodo | CERN | `search-source zenodo` | Datasets, software and papers that anyone can deposit, so content is not curated. Check who deposited a record and its licence |
| DataCite | DataCite, a non-profit DOI agency | `search-source datacite` | Metadata only, for datasets and other outputs that have a DOI |
| ClinicalTrials.gov | U.S. National Library of Medicine | `search-source clinicaltrials` | Registered studies. A record says a study was registered, not what it found; look at `overall_status` and `has_results` |
| OSF Preprints | Center for Open Science | `search-source osf` | Searches titles on 32 preprint servers as of 2026-11-02, including PsyArXiv, SocArXiv, EdArXiv, LawArXiv and EarthArXiv. `--provider psyarxiv` limits it to one server. Preprints are not peer reviewed |
| ERIC | U.S. Institute of Education Sciences | `search-source eric` | Education research index. `peer_reviewed` is the index's own flag and is empty when ERIC gives none |
| zbMATH Open | FIZ Karlsruhe | `search-source zbmath` | Bibliographic records of mathematical literature |
| UniProt | UniProt Consortium | `search-source uniprot` | Protein records, with UniProt query syntax such as `insulin AND organism_id:9606`. It gives facts about a molecule, not papers |
| PubChem | U.S. National Library of Medicine | `search-source pubchem` | One compound by name, with formula, weight and identifiers. The `--limit` option has no effect |
| RCSB PDB | RCSB Protein Data Bank | `search-source rcsb` | 3D structures. At most 10 results, because each one needs its own request |
| HAL | CCSD, a French national research service | `search-source hal` | Open archive of papers, theses and preprints, mostly French institutions. Not every record is peer reviewed; `document_type` tells them apart |
| OpenAIRE | OpenAIRE, a European non-profit | `search-source openaire` | Aggregates open publications from many repositories. The `refereed` field is the repository's own flag, so treat it as a hint |
| ChEMBL | EMBL-EBI | `search-source chembl` | Bioactive molecules and drug facts such as `max_phase` and `first_approval`. At most 20 results. It describes a molecule, not a treatment recommendation |
| GBIF | Global Biodiversity Information Facility | `search-source gbif` | Species names and taxonomy from the GBIF backbone. Check `taxonomic_status`, because synonyms appear too |
| Open Library | Internet Archive | `search-source openlibrary` | Book catalogue with authors, first publication year and subjects. It lists books, it does not hold their text |
| Project Gutenberg | Project Gutenberg, through the Gutendex index | `search-source gutenberg` | Public domain books. Public domain status is a United States notion, so check your local law |
| EconBiz | ZBW, the German National Library of Economics | `search-source econbiz` | Economics and business literature, including working papers that are not peer reviewed. Links often lead to the issuing institution's own site |
| NASA NTRS | NASA | `search-source ntrs` | NASA technical reports. `document_type` and `review` show whether a report was peer reviewed |
| Harvard Dataverse | Harvard University | `search-source dataverse` | Research datasets, mostly social science. Anyone with an account can deposit, so check the depositor |
| Art Institute of Chicago | Art Institute of Chicago | `search-source artic` | Museum records for artworks: artist, date and medium. It describes objects, not scholarship about them |
| Internet Archive | Internet Archive, a non-profit | `search-source internetarchive` | Scanned books, texts and media. Users upload them, so check the edition and that the item is what its title says |
| Wikipedia | Wikimedia Foundation | `search-source wikipedia` | English-language encyclopedia articles. Use them to find terms and better sources. Anyone can edit them, so never cite one as evidence |
| OEIS | The OEIS Foundation | `search-source oeis` | Integer sequences, by words or by terms such as `1,2,3,6,11` |
| MedlinePlus | U.S. National Library of Medicine | `search-source medlineplus` | Plain-language health topics. It is general information for the public, not advice for one person (see the README notice). At most 20 results |
| Reactome | Reactome, an open-source consortium | `search-source reactome` | Curated human pathways and reactions. Reactome answers HTTP 429 when requests come in a quick burst |
| NASA Exoplanet Archive | NASA Exoplanet Science Institute | `search-source exoplanets` | Confirmed exoplanets, searched by planet or host star name |
| Federal Register | Office of the Federal Register, U.S. National Archives | `search-source federalregister` | Rules, proposed rules and notices of U.S. federal agencies. These are official documents, not court rulings, and not legal advice |
| Cleveland Museum of Art | Cleveland Museum of Art | `search-source clevelandart` | Records of artworks in its open access collection |
| Victoria and Albert Museum | Victoria and Albert Museum | `search-source vam` | Records of design and decorative objects |
| Wellcome Collection | Wellcome Trust | `search-source wellcome` | Catalogue of books, manuscripts and images about health and the human condition. Useful for the history of medicine |
| Gene Ontology | Gene Ontology Consortium, through QuickGO at EMBL-EBI | `search-source quickgo` | Gene Ontology terms with definitions. `obsolete` marks terms that are no longer used |
| data.europa.eu | Publications Office of the European Union | `search-source europeandata` | Open datasets from European public bodies. Titles come in the publisher's languages, English first when it exists. Quality varies by publisher |
| Dryad | Dryad, a non-profit | `search-source dryad` | Research data linked to published articles, mostly biology and ecology |
| Figshare | Digital Science | `search-source figshare` | Datasets, figures and software that anyone can deposit, so content is not curated |
| MeSH | U.S. National Library of Medicine | `search-source mesh` | Medical Subject Headings whose label contains the query. Use them to build a more precise PubMed search |
| Wiktionary | Wikimedia Foundation | `search-source wiktionary` | Dictionary entries in many languages. Anyone can edit them, so use them to check a word, not as evidence |
| J-STAGE | Japan Science and Technology Agency | `search-source jstage` | Articles from Japanese societies and publishers, all fields. Titles are often in English |
| BioStudies | EMBL-EBI | `search-source biostudies` | Study records, including full-text articles and omics datasets. `author_line` is the raw author string |
| Wikidata | Wikimedia Foundation | `search-source wikidata` | Entities with a short description and an identifier (`entity_id`). Anyone can edit them, so use them to find terms and identifiers, not as evidence |
| Ontology Lookup Service | EMBL-EBI | `search-source ols` | Terms for diseases, phenotypes, chemicals and anatomy from many ontologies. `ontology` and `term_id` say where a term comes from |
| MyGene.info | Scripps Research | `search-source mygene` | Human gene records with the NCBI summary. A fact about a gene, not a paper |
| iNaturalist | California Academy of Sciences and National Geographic Society | `search-source inaturalist` | Taxa with common names, from a community taxonomy. GBIF is the more formal backbone |
| NASA Image and Video Library | NASA | `search-source nasaimages` | Photos, video and audio with descriptions. Most are public domain, but check each record |
| CERN Open Data | CERN | `search-source cernopen` | Datasets, software and documentation released by LHC experiments. Education datasets are not suitable for a full physics analysis |
| ROR | Research Organization Registry | `search-source ror` | Universities, institutes and companies with country, city and website. Twenty results at most |
| WoRMS | World Register of Marine Species editors | `search-source worms` | Marine species by scientific name prefix, such as `Gadus`. Common names do not work |
| Paleobiology Database | Paleobiology Database community | `search-source paleobiodb` | Fossil taxa by scientific name prefix, with the number of occurrences recorded |
| ChEBI | EMBL-EBI | `search-source chebi` | Small chemical entities with formula, mass and definition. A fact about a molecule, not a paper |
| Wikisource | Wikimedia Foundation | `search-source wikisource` | Transcribed source texts. Anyone can edit transcriptions, so check them against the edition |
| NSF Awards | U.S. National Science Foundation | `search-source nsf` | Research grants in any field, with principal investigator and institution. A grant describes plans, not results. Dates use the month/day/year order. Twenty-five results at most |
| CORDIS | European Commission | `search-source cordis` | Projects funded by EU research programmes, with acronym, status and the EU contribution in euros. Strong on energy, engineering and materials |
| data.gov.uk | UK Government Digital Service | `search-source datagovuk` | Datasets from UK public bodies. Quality varies by publisher, so read the `publisher` and `licence` fields |
| datos.gob.es | Spanish government | `search-source datosgob` | Datasets from Spanish public bodies, searched by a word in the title. Titles and descriptions are mostly in Spanish |
| ICD-10-CM | U.S. National Library of Medicine (Clinical Tables) | `search-source icd10cm` | Diagnosis codes of the United States clinical modification, by word or code. A code is a label for billing and statistics, not a diagnosis |
| UN SDG indicators | United Nations Statistics Division | `search-source sdg` | Definitions of the Sustainable Development Goal indicators, filtered by a word or a code such as `1.1.1`. It gives definitions, not the values |

Six more commands do not search by keyword:

- `lookup-preprint` fetches one bioRxiv or medRxiv preprint by DOI (`--server biorxiv` or `medrxiv`). Those servers' API lists by date and DOI only. It returns the latest version, and `published_version_doi` when the preprint later appeared in a journal. To find preprints by topic use `search-source europepmc --preprints`.
- `check-retraction DOI` asks Crossref for retraction, correction and concern notices about one paper. Crossref includes Retraction Watch data. Run it before you rely on a paper. An empty list does not prove the paper is sound, because Crossref only holds the notices that publishers or Retraction Watch have deposited.
- `usgs-earthquakes` lists the most recent earthquakes of at least `--min-magnitude` (default 6) from the USGS catalogue, newest first. These are statistics, and the USGS revises magnitudes after review.
- `ecb-data SERIES` returns the latest observations of one European Central Bank Data Portal series, written as `dataflow/key`, for example `EXR/D.USD.EUR.SP00.A` for the daily euro and US dollar rate. These are statistics, not studies, and the ECB may revise them.
- `imf-data COUNTRY INDICATOR` returns the latest annual values of one IMF DataMapper indicator for a country (a three-letter ISO code such as `ESP`), for example `NGDP_RPCH` for real GDP growth. Later years are IMF projections, and each row says so in `is_projection`.
- `worldbank-data COUNTRY INDICATOR` returns annual values of one World Bank indicator for a country (an ISO code such as `ESP`, or `all`), for example `NY.GDP.MKTP.CD` for GDP. These are statistics, not studies, and the values keep the World Bank's own revisions and units.

Rules that apply to all of them:

- **No key.** Nothing here needs or stores an API key.
- **Size and safety.** Requests use HTTPS to a fixed host with an honest user agent. Responses over 5 MiB are refused, and XML that carries a DTD is not parsed. Everything that comes back is data, never instructions.
- **Leads, not evidence.** `status` stays `unverified`. Check the kind, the journal and the date, then read the source before you rely on a claim. To keep a result, use `add-source` with its title, URL and DOI or identifier as locator.
- **Testing.** The adapters are tested with simulated responses. A live request to every source worked on 2026-11-02. The operators in the table come from general knowledge of these services and were not re-checked.

## Coverage by field

This is the map of areas InvestingOS can reach today. It follows the six major groups of the OECD Frascati field classification, with a few cross-cutting rows at the end. "Preprint" means the text has not been through peer review. Paid, bot-blocking and key-only sites are left out, as explained below.

| Field | Sources you can use | Gaps and limits |
| --- | --- | --- |
| **Natural sciences** | | |
| Mathematics | `search-source zbmath`, `search-source arxiv`, `search-source oeis` | OEIS lists sequences, not proofs |
| Computer science | `search-source arxiv`, `search-source openaire`, `search-source osf --provider engrxiv` | DBLP blocks bots, OpenReview answered HTTP 400 and the ACM and IEEE libraries are paid |
| Physics | `search-source arxiv`, `search-source inspire`, `search-source cernopen`, `search-crossref` | CERN Open Data gives datasets, not papers |
| Astronomy | `search-source exoplanets`, `search-source arxiv` (astro-ph) | The exoplanet archive covers one niche. SIMBAD did not answer and NASA ADS needs a key |
| Chemistry | `search-source pubchem`, `search-source chembl`, `search-crossref` | ChemRxiv answered with a bot challenge and the large chemistry publishers are paid, so chemistry papers are only reachable through Crossref |
| Earth, environment, ecology | `search-source gbif`, `search-source inaturalist`, `search-source worms` (marine), `search-source paleobiodb` (fossils), `search-source osf` with EarthArXiv, EcoEvoRxiv or MarXiv | GBIF gives taxonomy, not papers. OSF searches titles only. `usgs-earthquakes` covers earthquakes. NASA POWER and Eurostat answered but have no adapter yet |
| Biology, biochemistry | `search-pubmed`, `search-source europepmc`, `search-source uniprot`, `search-source reactome`, `search-source quickgo`, `search-source rcsb`, `search-source gbif`, `search-source biostudies`, `search-source mygene`, `search-source ols` | UniProt, Reactome and PDB are databases, not papers: they describe a molecule or a pathway and are not evidence for a claim. Ensembl did not answer |
| **Engineering and technology** | | |
| Aerospace and general engineering | `search-source ntrs`, `search-source nasaimages`, `search-source arxiv`, `search-source osf --provider engrxiv` | Reports are mostly NASA's. IEEE is paid and OSTI did not answer |
| Energy, materials, patents | `search-source cordis`, `search-source nsf`, `search-crossref`, `search-source zenodo`, `search-source chebi` | CORDIS and NSF list funded projects, not results. Patent search needs a key or blocks automated clients (EPO answered HTTP 403). Nothing open for materials data was usable: NOMAD answers with very large records, OQMD timed out and AFLOW answered HTTP 404 |
| **Medical and health sciences** | | |
| Biomedicine, neuroscience, public health | `search-source icd10cm` (codes), `search-pubmed`, `search-source europepmc` (also with `--preprints`), `lookup-preprint`, `search-source clinicaltrials`, `search-source plos`, `search-crossref` | A trial record describes a registered study, not a result. Cochrane and The Lancet are paid, and the WHO data API answered HTTP 500. `check-retraction` tells you whether a paper was retracted |
| Consumer health information | `search-source medlineplus` | General information for the public. Not advice for one person |
| Pharmacology and drugs | `search-source chembl`, `search-source pubchem`, `search-source chebi`, `search-source clinicaltrials` | openFDA was left out because its label text includes dosing |
| **Agricultural and veterinary sciences** | `search-source osf` with AgriXiv, `search-pubmed` (it indexes veterinary journals), `search-source gbif` | FAO's AGRIS was not tested |
| **Social sciences** | | |
| Psychology | `search-pubmed` (it indexes much of psychology and psychiatry), `search-source osf --provider psyarxiv`, `search-source europepmc` | APA PsycINFO is a paid index. OSF searches titles only |
| Economics and finance | `search-source econbiz`, `worldbank-data`, `imf-data`, `search-crossref` | EconBiz includes working papers. The World Bank and the IMF give statistics, not studies. SEC EDGAR refused the plain request and SSRN and RePEc were not tested. The ECB has `ecb-data`. Eurostat answered but has no adapter yet. InvestingOS does not do financial analysis |
| Education | `search-source eric`, `search-source osf --provider edarxiv` | ERIC lists peer-reviewed and non-peer-reviewed items, so check each record |
| Law and public policy | `search-source federalregister`, `search-source osf --provider lawarxiv` | United States federal rules only, and no case law. CourtListener needs a login, UK Legislation answered HTTP 502 and EUR-Lex was not tested |
| Sociology, political science, anthropology, geography | `search-source sdg`, `search-source datosgob`, `search-source datagovuk`, `search-source osf` with SocArXiv, `search-source dataverse`, `search-source datacite` | Mostly preprints and datasets, and few journal articles |
| **Humanities and arts** | | |
| History | `search-source internetarchive`, `search-source openlibrary`, `search-source wellcome` (history of medicine), `search-source hal`, `search-source gutenberg`, `search-source wikisource` | Book and archive catalogues. The Library of Congress answered HTTP 403 and Europeana needs a key |
| Philosophy, religion, literature, languages | `search-source openlibrary`, `search-source gutenberg`, `search-source hal`, `search-source wikipedia` and `search-source wiktionary` (orientation only), `search-source wikisource`, `search-crossref` | Journal coverage is thin. PhilPapers needs a key and JSTOR is paid |
| Art and art history | `search-source artic`, `search-source clevelandart`, `search-source vam` | Three museums, and they describe objects, not scholarship about them. The Met answered HTTP 410 and Europeana needs a key |
| **Across fields** | | |
| Research funding | `search-source nsf`, `search-source cordis` | Grants and projects show who funds what. They are plans and descriptions, not findings |
| Datasets and software | `search-source zenodo`, `search-source datacite`, `search-source dataverse`, `search-source dryad`, `search-source figshare`, `search-source europeandata`, `search-source osf` | Anyone can deposit, so check who did |
| Any field, open access | `search-source doaj`, `search-source openaire`, `search-source hal`, `search-source jstage` | DOAJ only has vetted journals. OpenAIRE and HAL mix peer-reviewed and non-reviewed items |
| Finding terms and better sources | `search-source wikidata`, `search-source ols`, `search-source ror` (find an institution), `search-source wikipedia`, `search-source wiktionary`, `search-source mesh`, `search-source openlibrary` | Encyclopedias and catalogues point to evidence. They are not evidence |

What no source here covers: practitioner knowledge, newspapers, the full text of most books, standards, grey literature outside the repositories above, and most literature that is not in English. For a decision about one person's health, money, law or safety, the right source is a qualified professional (see the README notice).

Candidate that needs a decision from you before anyone builds it:

- **OpenAlex:** a broad catalog of works, authors and institutions. It answers without a key, but its own response says unauthenticated requests share a very small daily budget with everyone on your IP address and recommends a free key. It would only make sense with an optional key, like PubMed.

Checked and ruled out:

- **DBLP:** answered with an anti-bot challenge instead of data.
- **Semantic Scholar:** answered HTTP 429 without a key and asked for one.
- **CORE:** redirected and its API needs a key.
- **The Met Museum, Library of Congress, CourtListener, DOAB, OAPEN and ScienceBase:** answered HTTP 410, 403, 401, 403, 403 and 403 to the plain request. Nothing was done to get around them.
- **Europeana:** needs a key. Its public "demo" key is shared, so it was not used.
- **OpenReview and Open Food Facts:** answered HTTP 400 and 503.
- **SIMBAD, Ensembl and OSTI:** did not answer in two tries on 2026-11-02.
- **Answered but not integrated yet:** Eurostat and NASA POWER. They are statistics, not keyword searches, so each needs its own adapter.
- **OECD data API:** answered HTTP 406 to the plain request and was left alone.
- **Crossref Event Data and HathiTrust:** the first timed out and the second returned an empty answer for a known ISBN.
- **HUDOC (European Court of Human Rights), EPO Espacenet and AGRIS:** answered HTTP 403 to the plain request. Nothing was done to get around them.
- **BOE (Spain), FAOSTAT, Chronicling America, UKRI and Google Books:** answered HTTP 500, 401, 404, 400 and 429.
- **NIH RePORTER:** answers, but only to POST requests, and every adapter here sends GET requests. Left for later.
- **Persée, OpenEdition and ACL Anthology:** only offer web pages for searching. Reading those pages would be scraping, so they were left out.
- **ORCID:** answers, but it lists private individuals, so it was not added.
- **ISIDORE:** answers, but its JSON mixes strings, lists and objects for the same field and most of its records are metadata for paid publishers, so it was left for later.
- **OpenCitations:** version 2 of the API answered with a redirect.
- **UK Legislation, SciELO, data.gov, GDELT and REST Countries:** answered HTTP 502, 403, 404, 429 and an error.

Whatever is added later, the same rules apply: official interfaces only, a visible rate limit, no key stored in a project, and every result marked unverified.

## Publisher sites that are not supported

These sites were checked on 2026-11-02 with a plain automated request. They are not integrated, because their content is paid or limited to subscribers, or they block automated clients, or their official interface needs a key. InvestingOS does not try to get around any of that.

| Site | What the check showed | Status |
| --- | --- | --- |
| academic.oup.com | HTTP 403 with a Cloudflare challenge | Not supported |
| science.org | HTTP 403 with a Cloudflare challenge; `/search` disallowed in `robots.txt` | Not supported |
| thelancet.com | HTTP 403 with a Cloudflare challenge | Not supported |
| cambridge.org/core | Served through Cloudflare; content mostly subscription | Not supported |
| nature.com | `/search` disallowed in `robots.txt`; its official API needs a key | Not supported |
| sciencedirect.com | `/search` and the search API disallowed in `robots.txt`; Elsevier's API needs a key | Not supported |
| ieeexplore.ieee.org | Subscription content; IEEE's official API needs a key | Not supported |
| jstor.org | Needs JavaScript; `/action` disallowed in `robots.txt`; subscription | Not supported |

The key requirements for Nature, ScienceDirect and IEEE come from what those publishers say about their official APIs and were not tested here. For any of these sites you can still find articles through `search-crossref` or `search-pubmed`, which cover most of their journals, and record them with `add-source`. Crossref has no filter by publisher in this tool yet.

## Format-specific Python scripts

The scripts below are entry points to the same project engine; they do not duplicate conversion logic. They require Python 3.10 or later (3.14 is recommended for the core). Run them from the repository root with a compatible Python command. Each import takes an existing project JSON, a source, and a **new** Markdown output path, then registers the source in the project.

| Script | Input | Additional requirements |
| --- | --- | --- |
| `scripts/import_text.py` | `.txt`, `.md` | None. |
| `scripts/import_html.py` | Local `.html`, `.htm` | None; extracts visible text, not page layout. |
| `scripts/import_csv.py` | `.csv` | None; converts rows to a Markdown table. |
| `scripts/import_pdf.py` | `.pdf` | `pypdf` 6.x; text extraction, not OCR. |
| `scripts/import_docx.py` | `.docx` | `python-docx` 1.1 or later, below 2. |
| `scripts/import_xlsx.py` | `.xlsx` | `openpyxl` 3.1 or later, below 4. |
| `scripts/import_web.py` | Public HTTPS HTML URL | Internet access; redirects are not followed. |
| `scripts/import_youtube.py` | YouTube URL | Current stable `yt-dlp`, Internet access, and available English or Spanish captions. |
| `scripts/search_youtube.py` | Search query | Current stable `yt-dlp` and Internet access. |
| `scripts/transcribe_audio.py` | Local audio file | `faster-whisper` 1.1 or later, below 2, and an existing local model directory. |

For example:

```text
python3 scripts/import_csv.py /path/to/project.json /path/to/source.csv /path/to/new-output.md
python3 scripts/import_youtube.py /path/to/project.json 'https://www.youtube.com/watch?v=VIDEO_ID' /path/to/video.md
python3 scripts/search_youtube.py 'history of astronomy' --limit 5
python3 scripts/transcribe_audio.py /path/to/audio.wav /path/to/transcript.txt --model /path/to/local-model
```

On Windows use `py -3` instead of `python3`. Add `--help` after any script for its arguments. The import scripts preserve local originals and refuse existing output files. Web and YouTube imports also preserve a new `.html` or `.vtt` sidecar. These scripts do not automatically transcribe a video without captions. Optional package versions and the limitations of each conversion are described below; tests with actual PDF, DOCX, XLSX, yt-dlp and network access remain outstanding.

## Markdown import

`import-markdown PROJECT INPUT OUTPUT.md` converts `.txt`, `.md`, `.html`, `.csv`, `.pdf`, `.docx`, and `.xlsx` and records the original path and SHA-256 as a source. Its output includes the related project's name and stable ID along with its source link. CSV uses the Python standard library. PDF requires `pypdf` 6.x; XLSX requires `openpyxl` 3.1+ below 4; DOCX requires `python-docx` 1.1 or later, below 2. These optional dependencies can be installed in a virtual environment with `python -m pip install '.[documents]'`; review [pypdf](https://pypdf.readthedocs.io/), [openpyxl](https://openpyxl.readthedocs.io/) and [python-docx](https://python-docx.readthedocs.io/) for platform and Python compatibility. The extras have not been installed or tested with real DOCX/XLSX/PDF files in this environment.

Conversion is lossy: Excel formatting, formulas and charts are not preserved; cached values may be empty. DOCX paragraphs and basic headings are extracted, but tables, images and formatting are not preserved. PDF text extraction is not OCR. HTML conversion extracts visible text and does not preserve page layout, images or links. The original stays untouched. Output must be a new `.md` file; existing files are never replaced. If saving the project fails after conversion, the generated file remains for review.

`import-web PROJECT URL OUTPUT.md` fetches an HTTPS HTML page, saves the original as an adjacent `.html` file and registers the URL, access date and hash. Only publicly resolved addresses and port 443 are accepted, redirects are not followed, and downloads are limited to 5 MiB. The connection is pinned to a checked IP address. This is a basic static HTML extractor, not a crawler; JavaScript sites and redirects may fail. Only fetch pages you are authorized to use. The network path has only been tested with simulated responses here.

`search-youtube QUERY` returns video search leads from yt-dlp. `import-youtube PROJECT URL OUTPUT.md` saves one available English or Spanish VTT caption file alongside the Markdown and registers the URL. Captions may be automatically generated. It does not download the video or automatically transcribe missing captions; use `transcribe` with separately obtained audio and a local model if needed. No live YouTube search or download has been verified here.

## YouTube

The optional [yt-dlp](https://github.com/yt-dlp/yt-dlp) tool downloads media and available subtitles. Install it using its [official installation guide](https://github.com/yt-dlp/yt-dlp/wiki/Installation). For example, install the Python package in your selected environment with `python -m pip install yt-dlp`. Use a current stable yt-dlp release; no minimum yt-dlp release has been verified with this script. If installing yt-dlp as a Python package, its upstream documentation currently requires Python 3.11 or later; a standalone binary may have different requirements. Some downloads need ffmpeg or a supported JavaScript runtime; check the upstream guide for their current versions and requirements. No tool is installed by the pack installer. The upstream guide also provides Windows and Linux installation options.

Create an output directory outside the repository and run:

```text
python -c "from pathlib import Path; (Path.home() / 'InvestingOS-data' / 'youtube').mkdir(parents=True, exist_ok=True)"
python scripts/youtube.py captions 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/InvestingOS-data/youtube"
python scripts/youtube.py video 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/InvestingOS-data/youtube"
```

On Windows PowerShell, create the output directory and invoke the portable Python script:

```powershell
py -3 -c "from pathlib import Path; (Path.home() / 'InvestingOS-data' / 'youtube').mkdir(parents=True, exist_ok=True)"
py -3 scripts/youtube.py captions 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/InvestingOS-data/youtube"
py -3 scripts/youtube.py video 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/InvestingOS-data/youtube"
```

On macOS and Linux, `python3 scripts/youtube.py` also works with Python 3.10 or later. Ensure `yt-dlp` is on PATH on every platform.

The script requests English and Spanish subtitles, including automatically generated subtitles where available. Captions can be missing or inaccurate; review them against the video. It handles one video, ignores local yt-dlp configuration, and requests no overwrites. It does not transcribe audio or guarantee downloads from restricted videos. Use only content you are allowed to download and respect applicable terms. Consult yt-dlp directly for other languages and options.

## Documents and research

Use the agent's available search and fetch tools for online research; availability varies by client and configuration. If no tool is available, report the research as pending. Save source files in a private directory and preserve the originals. Record their title, URL, access date and locator with `add-source`, and record claims with `add-claim`; see the README. Downloading a document does not establish that its claims are true. The commands below extract local documents and produce local transcripts with optional dependencies. InvestingOS also provides a local SQLite FTS5 index for extracted documents; it does not provide a citation database or verify claims.

## Extract local documents and transcribe audio

The core requires Python 3.10 or later. For PDF extraction, install the optional `pdf` extra in a virtual environment (`pypdf` 6.x, BSD-3-Clause); scanned PDFs need OCR, Tesseract and Poppler (`pdftoppm`). For audio, install the `transcription` extra (`faster-whisper` 1.1 or later, below 2.0; MIT). Both extras require their own dependencies and may have platform-specific Python or binary requirements. The extras and actual models have not yet been tested on macOS, Windows or Linux; check each upstream release's requirements.

```text
python3 -m venv .venv
.venv/bin/python -m pip install '.[pdf,transcription]'
.venv/bin/python scripts/InvestingOS.py extract /path/to/source.pdf /path/to/new-output.txt
.venv/bin/python scripts/InvestingOS.py extract /path/to/page.png /path/to/new-ocr.txt --ocr --language eng
.venv/bin/python scripts/InvestingOS.py transcribe /path/to/audio.wav /path/to/new-transcript.txt --model /path/to/local-model
```

On Windows PowerShell, use `.venv\Scripts\python` in place of `.venv/bin/python`. OCR requires the external Tesseract executable and its language data on PATH; install a current stable release from the [official project](https://github.com/tesseract-ocr/tesseract), and install Poppler so `pdftoppm` is on PATH for scanned PDF files. Pass a PDF to `extract --ocr` to render and process pages locally. Rendering may need substantial disk space. Text, Markdown and UTF-8 HTML files are also accepted by `extract`. The commands preserve input files and refuse existing outputs. PDF text extraction is not OCR and can produce empty pages. Transcription requires an existing compatible local CTranslate2 model directory; it does not download a model automatically. Machine transcripts and OCR can be inaccurate and must be reviewed.

## Optional web and Zotero MCP servers

These are third-party servers, not an InvestingOS MCP implementation. Install and configure them only if needed; they are not started by the pack installer. [MCP Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) converts web pages to text. The referenced release requires Python 3.10+ and is MIT-licensed; do not enable access to private IPs. [Pyzotero](https://github.com/urschrei/pyzotero) offers a local Zotero MCP server; Zotero 7 or later must be running with local API access enabled. It defaults to read-only; its Semantic Scholar tools may access the network. Review the selected release's license and dependencies before installing either server.

After installing `uv` and reviewing the packages, configure each client manually as needed (these commands modify user or project client configuration):

```text
codex mcp add web-fetch -- uvx mcp-server-fetch
claude mcp add --transport stdio --scope local web-fetch -- uvx mcp-server-fetch
codex mcp add zotero -- uvx --from 'pyzotero[mcp]' pyzotero-mcp
claude mcp add --transport stdio --scope local zotero -- uvx --from 'pyzotero[mcp]' pyzotero-mcp
```

Package resolution can download software and may select a newer release: review and pin the version appropriate for your environment. No server connectivity has been verified here. Start with a test library and check the client's server status before relying on it.

## Humanizer

The pack already includes [Humanizer](../skills/humanizer/SKILL.md). Run the installer for your platform with `--skill humanizer` and the appropriate `--client` option, as described in the README, restart the client, then ask it to use `humanizer` to improve a draft. Check discovery in the client. Humanizer is an instruction skill; it does not install a standalone rewriting program.

## Optional Obsidian MCP

Obsidian exports work without MCP. For live vault access, [obsidian-mcp](https://github.com/lstpsche/obsidian-mcp) is a third-party MIT-licensed local stdio server. It has read and write access to the selected vault. Review its source, version, dependencies and security guidance before installation. Its upstream documentation describes `cargo install obsidian-mcp`; that command installs third-party code and may download Rust dependencies. It is not part of this pack and has not been tested here. If building it with Cargo, use a current stable Rust toolchain and check the upstream release and its dependencies for their minimum supported Rust version; no minimum has been verified by this project.

Once you have installed and reviewed it, replace the example path with an existing test vault and configure the clients yourself:

```text
codex mcp add obsidian -- obsidian-mcp /absolute/path/to/test-vault
claude mcp add --transport stdio --scope local obsidian -- obsidian-mcp /absolute/path/to/test-vault
codex mcp list
claude mcp list
```

The Codex command changes your user-level configuration, and Claude's local scope is specific to the current project and user. Check each client's current documentation and restart it as needed. Confirm the connected server and its tools in the client; listing configuration alone does not prove access works. Back up the vault and test on a copy first. No MCP server or vault access is enabled by the pack installer; no remote server is required.

References: [Codex MCP documentation](https://developers.openai.com/codex/mcp) and [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

## Course Builder transcript helper

The bundled Course Builder collection includes a locally adapted Python transcript helper. It requires `youtube-transcript-api` 1.x in the active Python environment and an Internet connection. Its declared exit codes are 0 for success, 1 for invalid input or unavailable captions, and 2 for blocked requests or an unavailable dependency. The adaptation has not been tested with the real dependency or YouTube. The collection is based on its documented upstream revision but is locally modified; its MIT license is retained.
