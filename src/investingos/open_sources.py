"""Search open scholarly and scientific data sources through their official, keyless interfaces.

Every result is a lead, not a verified claim: the status is always "unverified". Records keep a
`kind` so that a preprint, a registry entry, a protein record or a statistic is not mistaken for a
peer-reviewed article. No source here needs an API key. Each command makes the fewest requests it
can and sends an honest User-Agent. Nothing from these services is treated as instructions.
"""
import datetime
import html
import json
import re
from urllib import error, parse, request
from xml.etree import ElementTree

USER_AGENT = 'InvestingOS/0.1 (https://github.com/Zubiarka8/InvestingOS)'
MAX_BYTES = 5 * 1024 * 1024
ABSTRACT_LIMIT = 2000
AUTHOR_LIMIT = 25


# ---------------------------------------------------------------- shared helpers

def _fetch(url, accept='application/json', not_found=None):
    req = request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': accept})
    try:
        with request.urlopen(req, timeout=25) as response:
            data = response.read(MAX_BYTES + 1)
    except error.HTTPError as exc:
        if exc.code == 404 and not_found:
            raise ValueError(not_found) from None
        if exc.code == 429:
            raise ValueError('the service reported too many requests; wait a moment and try again') from None
        raise ValueError(f'the service answered with HTTP status {exc.code}') from None
    except error.URLError as exc:
        raise ValueError(f'the request failed: {exc.reason}') from None
    if len(data) > MAX_BYTES:
        raise ValueError('the service response is too large')
    return data


def _json(url, **kwargs):
    try:
        return json.loads(_fetch(url, **kwargs))
    except json.JSONDecodeError:
        raise ValueError('the service did not return valid JSON') from None


def _xml(url, accept='application/atom+xml'):
    data = _fetch(url, accept=accept)
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('the service response contains a DTD; refusing to parse it')
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError:
        raise ValueError('the service did not return valid XML') from None


def _text(value, limit=None):
    """Plain text: strip markup and collapse whitespace."""
    value = re.sub(r'<[^>]+>', ' ', str(value or ''))
    value = re.sub(r'\s+', ' ', value).strip()
    return value[:limit].rstrip() + '...' if limit and len(value) > limit else value


def _check(query, limit, maximum=100):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if not isinstance(limit, int) or not 1 <= limit <= maximum:
        raise ValueError(f'limit must be between 1 and {maximum}')


def _names(values):
    names = [n for n in (_text(v) for v in values) if n]
    return names[:AUTHOR_LIMIT]


def _record(source, kind, title, **fields):
    """Normalised result; absent values stay empty instead of being guessed."""
    result = {'source': source, 'kind': kind, 'title': _text(title), 'authors': [], 'published': '',
              'journal': '', 'doi': '', 'url': '', 'abstract': ''}
    result.update(fields)
    result['abstract'] = _text(result['abstract'], ABSTRACT_LIMIT)
    result['status'] = 'unverified'
    return result


def _dig(obj, *path, default=None):
    for part in path:
        try:
            obj = obj[part]
        except (KeyError, IndexError, TypeError):
            return default
    return obj


# ---------------------------------------------------------------- keyword search adapters

def europepmc(query, limit=10, preprints=False):
    _check(query, limit)
    term = f'({query}) AND SRC:PPR' if preprints else query
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + parse.urlencode(
        {'query': term, 'format': 'json', 'pageSize': limit, 'resultType': 'core'})
    results = []
    for item in _dig(_json(url), 'resultList', 'result', default=[]):
        source, ident = item.get('source', ''), item.get('id', '')
        authors = [a.strip(' .') for a in item.get('authorString', '').split(', ')]
        results.append(_record(
            'Europe PMC', 'preprint' if source == 'PPR' else 'article', item.get('title', ''),
            authors=_names(authors), published=item.get('firstPublicationDate') or item.get('pubYear', ''),
            journal=_dig(item, 'journalInfo', 'journal', 'title', default='') or item.get('journalTitle', ''),
            doi=item.get('doi', ''), url=f'https://europepmc.org/article/{source}/{ident}' if ident else '',
            abstract=item.get('abstractText', ''), pmid=item.get('pmid', ''),
            open_access=item.get('isOpenAccess') == 'Y',
            publication_types=list(_dig(item, 'pubTypeList', 'pubType', default=[]))))
    return results


def arxiv(query, limit=10):
    _check(query, limit)
    # Plain words are combined with AND; a query that already uses field syntax (ti:, au:) is passed on.
    search = query if ':' in query else ' AND '.join('all:' + word for word in query.split())
    url = 'https://export.arxiv.org/api/query?' + parse.urlencode({'search_query': search, 'max_results': limit})
    ns = {'a': 'http://www.w3.org/2005/Atom', 'x': 'http://arxiv.org/schemas/atom'}
    results = []
    for entry in _xml(url).findall('a:entry', ns):
        link = next((l.get('href') for l in entry.findall('a:link', ns) if l.get('rel') == 'alternate'), '')
        results.append(_record(
            'arXiv', 'preprint', entry.findtext('a:title', '', ns),
            authors=_names(a.findtext('a:name', '', ns) for a in entry.findall('a:author', ns)),
            published=(entry.findtext('a:published', '', ns) or '')[:10], doi=entry.findtext('x:doi', '', ns),
            url=link or entry.findtext('a:id', '', ns), abstract=entry.findtext('a:summary', '', ns),
            journal=entry.findtext('x:journal_ref', '', ns)))
    return results


def doaj(query, limit=10):
    _check(query, limit)
    url = f'https://doaj.org/api/search/articles/{parse.quote(query, safe="")}?' + parse.urlencode({'pageSize': limit})
    results = []
    for item in _json(url).get('results', []):
        bib = item.get('bibjson', {})
        doi = next((i.get('id', '') for i in bib.get('identifier', []) if i.get('type') == 'doi'), '')
        link = next((l.get('url', '') for l in bib.get('link', [])), '')
        results.append(_record(
            'DOAJ', 'article', bib.get('title', ''), authors=_names(a.get('name', '') for a in bib.get('author', [])),
            published=str(bib.get('year', '')), journal=_dig(bib, 'journal', 'title', default=''), doi=doi,
            url=link or f'https://doaj.org/article/{item.get("id", "")}', abstract=bib.get('abstract', '')))
    return results


def plos(query, limit=10):
    _check(query, limit)
    url = 'https://api.plos.org/search?' + parse.urlencode({
        'q': query, 'rows': limit, 'wt': 'json',
        'fl': 'id,title,author_display,journal,publication_date,abstract'})
    results = []
    for item in _dig(_json(url), 'response', 'docs', default=[]):
        abstract = item.get('abstract', '')
        results.append(_record(
            'PLOS', 'article', item.get('title', ''), authors=_names(item.get('author_display', [])),
            published=(item.get('publication_date') or '')[:10], journal=item.get('journal', ''),
            doi=item.get('id', ''), url='https://doi.org/' + item['id'] if item.get('id') else '',
            abstract=' '.join(abstract) if isinstance(abstract, list) else abstract))
    return results


def inspire(query, limit=10):
    _check(query, limit)
    url = 'https://inspirehep.net/api/literature?' + parse.urlencode({
        'q': query, 'size': limit,
        'fields': 'titles,authors.full_name,dois,arxiv_eprints,control_number,preprint_date,publication_info,abstracts'})
    results = []
    for hit in _dig(_json(url), 'hits', 'hits', default=[]):
        meta = hit.get('metadata', {})
        eprint = _dig(meta, 'arxiv_eprints', 0, 'value', default='')
        results.append(_record(
            'INSPIRE-HEP', 'article', _dig(meta, 'titles', 0, 'title', default=''),
            authors=_names(a.get('full_name', '') for a in meta.get('authors', [])),
            published=meta.get('preprint_date', ''), journal=_dig(meta, 'publication_info', 0, 'journal_title', default=''),
            doi=_dig(meta, 'dois', 0, 'value', default=''), url=f'https://inspirehep.net/literature/{hit.get("id", "")}',
            abstract=_dig(meta, 'abstracts', 0, 'value', default=''), arxiv_id=eprint))
    return results


def zenodo(query, limit=10):
    _check(query, limit)
    url = 'https://zenodo.org/api/records?' + parse.urlencode({'q': query, 'size': limit})
    results = []
    for hit in _dig(_json(url), 'hits', 'hits', default=[]):
        meta = hit.get('metadata', {})
        results.append(_record(
            'Zenodo', 'deposit', meta.get('title', ''), authors=_names(c.get('name', '') for c in meta.get('creators', [])),
            published=meta.get('publication_date', ''), doi=hit.get('doi', ''),
            url=_dig(hit, 'links', 'self_html', default=''), abstract=meta.get('description', ''),
            resource_type=_dig(meta, 'resource_type', 'title', default=''),
            license=_dig(meta, 'license', 'id', default='')))
    return results


def datacite(query, limit=10):
    _check(query, limit)
    url = 'https://api.datacite.org/dois?' + parse.urlencode({'query': query, 'page[size]': limit})
    results = []
    for item in _json(url).get('data', []):
        attr = item.get('attributes', {})
        results.append(_record(
            'DataCite', 'record', _dig(attr, 'titles', 0, 'title', default=''),
            authors=_names(c.get('name', '') for c in attr.get('creators', [])),
            published=str(attr.get('publicationYear') or ''), publisher=attr.get('publisher') or '',
            doi=item.get('id', ''), url=attr.get('url') or ('https://doi.org/' + item.get('id', '')),
            resource_type=_dig(attr, 'types', 'resourceTypeGeneral', default='')))
    return results


def clinicaltrials(query, limit=10):
    _check(query, limit)
    url = 'https://clinicaltrials.gov/api/v2/studies?' + parse.urlencode({
        'query.term': query, 'pageSize': limit, 'format': 'json',
        'fields': 'NCTId,BriefTitle,OverallStatus,StartDate,LeadSponsorName,StudyType,HasResults'})
    results = []
    for study in _json(url).get('studies', []):
        proto = study.get('protocolSection', {})
        nct = _dig(proto, 'identificationModule', 'nctId', default='')
        results.append(_record(
            'ClinicalTrials.gov', 'registry record', _dig(proto, 'identificationModule', 'briefTitle', default=''),
            published=_dig(proto, 'statusModule', 'startDateStruct', 'date', default=''),
            sponsor=_dig(proto, 'sponsorCollaboratorsModule', 'leadSponsor', 'name', default=''),
            url=f'https://clinicaltrials.gov/study/{nct}' if nct else '', nct_id=nct,
            overall_status=_dig(proto, 'statusModule', 'overallStatus', default=''),
            study_type=_dig(proto, 'designModule', 'studyType', default=''),
            has_results=bool(study.get('hasResults'))))
    return results


OSF_PROVIDER = re.compile(r'^[a-z0-9-]{2,40}$')


def osf(query, limit=10, provider=None):
    _check(query, limit)
    params = {'filter[title]': query, 'page[size]': limit}
    if provider:
        if not OSF_PROVIDER.match(provider):
            raise ValueError('provider must be a preprint server id such as psyarxiv or socarxiv')
        params['filter[provider]'] = provider
    results = []
    for item in _json('https://api.osf.io/v2/preprints/?' + parse.urlencode(params)).get('data', []):
        attr = item.get('attributes', {})
        results.append(_record(
            'OSF Preprints', 'preprint', attr.get('title', ''), published=(attr.get('date_published') or '')[:10],
            server=_dig(item, 'relationships', 'provider', 'data', 'id', default=''), doi=attr.get('doi') or '',
            url=_dig(item, 'links', 'html', default=''), abstract=attr.get('description', ''),
            tags=list(attr.get('tags', []))[:10]))
    return results


def eric(query, limit=10):
    _check(query, limit)
    url = 'https://api.ies.ed.gov/eric/?' + parse.urlencode({'search': query, 'format': 'json', 'rows': limit})
    results = []
    for doc in _dig(_json(url), 'response', 'docs', default=[]):
        flag = doc.get('peerreviewed')
        results.append(_record(
            'ERIC', 'record', doc.get('title', ''), authors=_names(doc.get('author', [])),
            published=str(doc.get('publicationdateyear', '')), publisher=doc.get('publisher', '') or '',
            url=f'https://eric.ed.gov/?id={doc["id"]}' if doc.get('id') else '', abstract=doc.get('description', ''),
            eric_id=doc.get('id', ''), peer_reviewed={'T': True, 'F': False}.get(flag)))
    return results


def zbmath(query, limit=10):
    _check(query, limit)
    url = 'https://api.zbmath.org/v1/document/_search?' + parse.urlencode(
        {'search_string': query, 'page': 0, 'results_per_page': limit})
    results = []
    for doc in _json(url).get('result', []):
        results.append(_record(
            'zbMATH Open', 'record', _dig(doc, 'title', 'title', default=''),
            authors=_names(a.get('name', '') for a in _dig(doc, 'contributors', 'authors', default=[])),
            published=str(doc.get('year', '')), url=doc.get('zbmath_url', ''),
            journal=_dig(doc, 'source', 'series', 0, 'title', default=''), zbmath_id=str(doc.get('id', ''))))
    return results


def uniprot(query, limit=10):
    _check(query, limit)
    url = 'https://rest.uniprot.org/uniprotkb/search?' + parse.urlencode({
        'query': query, 'size': limit, 'format': 'json',
        'fields': 'accession,protein_name,gene_names,organism_name,length'})
    results = []
    for item in _json(url).get('results', []):
        desc = item.get('proteinDescription', {})
        name = (_dig(desc, 'recommendedName', 'fullName', 'value')
                or _dig(desc, 'submissionNames', 0, 'fullName', 'value', default=''))
        accession = item.get('primaryAccession', '')
        results.append(_record(
            'UniProt', 'protein', name, url=f'https://www.uniprot.org/uniprotkb/{accession}/entry' if accession else '',
            accession=accession, gene=_dig(item, 'genes', 0, 'geneName', 'value', default=''),
            organism=_dig(item, 'organism', 'scientificName', default=''), length=_dig(item, 'sequence', 'length'),
            reviewed=str(item.get('entryType', '')).startswith('UniProtKB reviewed')))
    return results


def pubchem(query, limit=1):
    """Look up a compound by name. PubChem returns one best match, so the limit is ignored."""
    _check(query, 1)
    name = parse.quote(query.strip(), safe='')
    url = ('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/' + name +
           '/property/MolecularFormula,MolecularWeight,IUPACName,InChIKey/JSON')
    data = _json(url, not_found='PubChem has no compound with that name')
    results = []
    for prop in _dig(data, 'PropertyTable', 'Properties', default=[]):
        cid = prop.get('CID')
        results.append(_record(
            'PubChem', 'compound', query.strip(), url=f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}' if cid else '',
            cid=cid, molecular_formula=prop.get('MolecularFormula', ''), molecular_weight=prop.get('MolecularWeight', ''),
            iupac_name=prop.get('IUPACName', ''), inchi_key=prop.get('InChIKey', '')))
    return results


def rcsb(query, limit=5):
    """Full-text search of the Protein Data Bank; one extra request per structure, so the limit is 10."""
    _check(query, limit, maximum=10)
    search = {'query': {'type': 'terminal', 'service': 'full_text', 'parameters': {'value': query}},
              'return_type': 'entry', 'request_options': {'paginate': {'start': 0, 'rows': limit}}}
    url = 'https://search.rcsb.org/rcsbsearch/v2/query?' + parse.urlencode({'json': json.dumps(search)})
    body = _fetch(url)
    if not body.strip():  # RCSB answers 204 with an empty body when nothing matches
        return []
    try:
        found = json.loads(body)
    except json.JSONDecodeError:
        raise ValueError('the service did not return valid JSON') from None
    results = []
    for hit in found.get('result_set', []):
        entry = _json('https://data.rcsb.org/rest/v1/core/entry/' + parse.quote(hit['identifier'], safe=''))
        cite = entry.get('rcsb_primary_citation', {})
        ident = entry.get('rcsb_id', hit['identifier'])
        results.append(_record(
            'RCSB PDB', 'structure', _dig(entry, 'struct', 'title', default=''),
            authors=_names(a.get('name', '') for a in entry.get('audit_author', [])),
            published=(_dig(entry, 'rcsb_accession_info', 'initial_release_date', default='') or '')[:10],
            journal=cite.get('journal_abbrev', ''), doi=cite.get('pdbx_database_id_DOI', '') or '',
            url=f'https://www.rcsb.org/structure/{ident}', pdb_id=ident,
            method=_dig(entry, 'exptl', 0, 'method', default=''),
            resolution=_dig(entry, 'rcsb_entry_info', 'resolution_combined', 0)))
    return results


# ---------------------------------------------------------------- lookups and statistics

PREPRINT_DOI = re.compile(r'^10\.1101/[A-Za-z0-9._-]{4,80}$')


def preprint(doi, server='biorxiv'):
    """Fetch one bioRxiv or medRxiv preprint by DOI; the API cannot search by keyword."""
    if server not in ('biorxiv', 'medrxiv'):
        raise ValueError('server must be biorxiv or medrxiv')
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', (doi or '').strip())
    if not PREPRINT_DOI.match(doi):
        raise ValueError('expected a bioRxiv or medRxiv DOI such as 10.1101/2020.03.22.002386')
    data = _json(f'https://api.biorxiv.org/details/{server}/{doi}/na/json')
    versions = data.get('collection') or []
    if not versions:
        raise ValueError(f'{server} has no preprint with that DOI')
    latest = versions[-1]
    published = latest.get('published') or ''
    return _record(
        latest.get('server', server), 'preprint', latest.get('title', ''),
        authors=_names(a for a in (latest.get('authors') or '').split(';')), published=latest.get('date', ''),
        doi=latest.get('doi', doi), url=f'https://www.{server}.org/content/{doi}v{latest.get("version", "1")}',
        abstract=latest.get('abstract', ''), version=latest.get('version', ''), category=latest.get('category', ''),
        published_version_doi='' if published in ('', 'NA') else published)


COUNTRY = re.compile(r'^([A-Za-z]{2,3}|all)$')
INDICATOR = re.compile(r'^[A-Za-z0-9._]{3,40}$')


def worldbank(country, indicator, limit=10):
    """Annual values of one World Bank indicator for a country (statistics, not studies)."""
    if not COUNTRY.match(country or ''):
        raise ValueError('country must be a 2 or 3 letter ISO code, for example ESP, or all')
    if not INDICATOR.match(indicator or ''):
        raise ValueError('indicator must look like NY.GDP.MKTP.CD')
    _check('x', limit)
    url = (f'https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?' +
           parse.urlencode({'format': 'json', 'per_page': limit}))
    data = _json(url)
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        detail = _dig(data, 0, 'message', 0, 'value', default='') if isinstance(data, list) else ''
        raise ValueError('World Bank returned no data' + (f': {detail}' if detail else ''))
    updated = _dig(data, 0, 'lastupdated', default='')
    return [{'source': 'World Bank', 'kind': 'indicator', 'country': _dig(row, 'country', 'value', default=''),
             'country_code': row.get('countryiso3code', ''), 'indicator_id': _dig(row, 'indicator', 'id', default=''),
             'indicator': _dig(row, 'indicator', 'value', default=''), 'year': row.get('date', ''),
             'value': row.get('value'), 'last_updated': updated,
             'url': f'https://data.worldbank.org/indicator/{indicator}', 'status': 'unverified'} for row in data[1]]


def hal(query, limit=10):
    _check(query, limit)
    url = 'https://api.archives-ouvertes.fr/search/?' + parse.urlencode({
        'q': query, 'rows': limit, 'wt': 'json',
        'fl': 'title_s,abstract_s,journalTitle_s,authFullName_s,uri_s,doiId_s,docType_s,producedDateY_i'})
    results = []
    for doc in _dig(_json(url), 'response', 'docs', default=[]):
        first = lambda key: (doc.get(key) or [''])[0] if isinstance(doc.get(key), list) else doc.get(key, '')
        results.append(_record(
            'HAL', 'article' if doc.get('docType_s') == 'ART' else 'repository record', first('title_s'),
            authors=_names(doc.get('authFullName_s') or []), published=str(doc.get('producedDateY_i', '')),
            journal=first('journalTitle_s'), doi=doc.get('doiId_s', ''), url=doc.get('uri_s', ''),
            abstract=first('abstract_s'), document_type=doc.get('docType_s', '')))
    return results


def openaire(query, limit=10):
    _check(query, limit)
    url = 'https://api.openaire.eu/graph/v1/researchProducts?' + parse.urlencode({
        'search': query, 'pageSize': limit, 'type': 'publication'})
    results = []
    for item in _json(url).get('results', []):
        doi = next((p.get('value', '') for p in item.get('pids') or [] if p.get('scheme') == 'doi'), '')
        instance = (item.get('instances') or [{}])[0]
        link = next(iter(instance.get('urls') or []), '')
        results.append(_record(
            'OpenAIRE', 'article', item.get('mainTitle', ''),
            authors=_names(a.get('fullName', '') for a in item.get('authors') or []),
            published=item.get('publicationDate') or '', journal=_dig(item, 'container', 'name', default=''),
            doi=doi, url=link or (f'https://doi.org/{doi}' if doi else ''),
            abstract=' '.join(item.get('descriptions') or []), publisher=item.get('publisher') or '',
            refereed=instance.get('refereed', '')))
    return results


def chembl(query, limit=5):
    _check(query, limit, maximum=20)
    url = 'https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?' + parse.urlencode({'q': query, 'limit': limit})
    results = []
    for item in _json(url).get('molecules', []):
        cid = item.get('molecule_chembl_id', '')
        props = item.get('molecule_properties') or {}
        results.append(_record(
            'ChEMBL', 'compound', item.get('pref_name') or cid,
            url=f'https://www.ebi.ac.uk/chembl/compound_report_card/{cid}/' if cid else '', chembl_id=cid,
            molecule_type=item.get('molecule_type') or '', max_phase=item.get('max_phase'),
            first_approval=item.get('first_approval'), molecular_formula=props.get('full_molformula', ''),
            molecular_weight=props.get('full_mwt', ''),
            inchi_key=(item.get('molecule_structures') or {}).get('standard_inchi_key', '')))
    return results


def gbif(query, limit=10):
    _check(query, limit)
    url = 'https://api.gbif.org/v1/species/search?' + parse.urlencode({'q': query, 'limit': limit})
    results = []
    for item in _json(url).get('results', []):
        key = item.get('key')
        results.append(_record(
            'GBIF', 'taxon', item.get('scientificName', ''), url=f'https://www.gbif.org/species/{key}' if key else '',
            rank=item.get('rank', ''), taxonomic_status=item.get('taxonomicStatus', ''),
            kingdom=item.get('kingdom', ''), family=item.get('family', '')))
    return results


def openlibrary(query, limit=10):
    _check(query, limit)
    url = 'https://openlibrary.org/search.json?' + parse.urlencode({
        'q': query, 'limit': limit, 'fields': 'key,title,author_name,first_publish_year,publisher,subject'})
    results = []
    for doc in _json(url).get('docs', []):
        key = doc.get('key', '')
        results.append(_record(
            'Open Library', 'book', doc.get('title', ''), authors=_names(doc.get('author_name') or []),
            published=str(doc.get('first_publish_year', '')), url=f'https://openlibrary.org{key}' if key else '',
            publisher=_text((doc.get('publisher') or [''])[0]), subjects=[_text(x) for x in (doc.get('subject') or [])[:8]]))
    return results


def gutenberg(query, limit=10):
    _check(query, limit)
    data = _json('https://gutendex.com/books/?' + parse.urlencode({'search': query}))
    results = []
    for book in data.get('results', [])[:limit]:
        authors = [a.get('name', '') for a in book.get('authors') or []]
        results.append(_record(
            'Project Gutenberg', 'book', book.get('title', ''), authors=_names(authors),
            url=f'https://www.gutenberg.org/ebooks/{book.get("id")}', abstract=' '.join(book.get('summaries') or [])[:2000],
            subjects=[_text(x) for x in (book.get('subjects') or [])[:8]], languages=book.get('languages') or [],
            copyright=book.get('copyright')))
    return results


def econbiz(query, limit=10):
    _check(query, limit)
    url = 'https://api.econbiz.de/v1/search?' + parse.urlencode({'q': query, 'size': limit})
    results = []
    for item in _dig(_json(url), 'hits', 'hits', default=[]):
        links = item.get('identifier_url') or []
        results.append(_record(
            'EconBiz', 'working paper or book' if item.get('type') == 'book' else str(item.get('type') or 'record'),
            (item.get('title') or [''])[0] if isinstance(item.get('title'), list) else item.get('title', ''),
            authors=_names(item.get('creator') or []), published=_text((item.get('date') or [''])[0]),
            url=links[0] if links else f'https://www.econbiz.de/Record/{item.get("id", "")}',
            publisher=_text((item.get('publisher') or [''])[0]), subjects=[_text(x) for x in (item.get('subject') or [])[:8]],
            series=_text((item.get('series') or [''])[0])))
    return results


def ntrs(query, limit=10):
    _check(query, limit)
    url = 'https://ntrs.nasa.gov/api/citations/search?' + parse.urlencode({'q': query, 'page.size': limit})
    results = []
    for item in _json(url).get('results', []):
        names = [_dig(a, 'meta', 'author', 'name', default='') for a in item.get('authorAffiliations') or []]
        ident = item.get('id')
        results.append(_record(
            'NASA NTRS', 'technical report', item.get('title', ''), authors=_names(names),
            published=str(item.get('distributionDate') or item.get('submittedDate') or '')[:10],
            url=f'https://ntrs.nasa.gov/citations/{ident}' if ident else '', abstract=item.get('abstract', ''),
            document_type=item.get('stiType', ''), review=item.get('technicalReviewType', ''),
            subjects=list(item.get('subjectCategories') or [])[:8]))
    return results


def dataverse(query, limit=10):
    _check(query, limit)
    url = 'https://dataverse.harvard.edu/api/search?' + parse.urlencode({'q': query, 'per_page': limit, 'type': 'dataset'})
    results = []
    for item in _dig(_json(url), 'data', 'items', default=[]):
        results.append(_record(
            'Harvard Dataverse', 'dataset', item.get('name', ''), authors=_names(item.get('authors') or []),
            published=str(item.get('published_at', ''))[:10], url=item.get('url', ''),
            doi=str(item.get('global_id', '')).replace('doi:', ''), abstract=item.get('description', ''),
            publisher=item.get('name_of_dataverse', ''), deposit_not_curated=True))
    return results


def artic(query, limit=10):
    _check(query, limit)
    url = 'https://api.artic.edu/api/v1/artworks/search?' + parse.urlencode({
        'q': query, 'limit': limit, 'fields': 'id,title,artist_display,date_display,medium_display,department_title'})
    results = []
    for item in _json(url).get('data', []):
        results.append(_record(
            'Art Institute of Chicago', 'artwork', item.get('title', ''), authors=_names([item.get('artist_display') or '']),
            published=item.get('date_display') or '', url=f'https://www.artic.edu/artworks/{item.get("id")}',
            medium=item.get('medium_display') or '', department=item.get('department_title') or ''))
    return results


def internetarchive(query, limit=10):
    _check(query, limit)
    fields = ('identifier', 'title', 'creator', 'year', 'description', 'mediatype')
    url = 'https://archive.org/advancedsearch.php?' + parse.urlencode(
        [('q', query), ('rows', limit), ('output', 'json')] + [('fl[]', f) for f in fields])
    results = []
    for doc in _dig(_json(url), 'response', 'docs', default=[]):
        creator = doc.get('creator') or []
        creator = [creator] if isinstance(creator, str) else creator
        desc = doc.get('description') or ''
        desc = ' '.join(desc) if isinstance(desc, list) else desc
        results.append(_record(
            'Internet Archive', 'archive item', doc.get('title', ''), authors=_names(creator),
            published=str(doc.get('year', '')), url=f'https://archive.org/details/{doc.get("identifier", "")}',
            abstract=desc, media_type=doc.get('mediatype', ''), user_uploaded_content=True))
    return results


def wikipedia(query, limit=10):
    """Encyclopedia articles for orientation only. Anyone can edit them, so they are never evidence."""
    _check(query, limit)
    url = 'https://en.wikipedia.org/w/rest.php/v1/search/page?' + parse.urlencode({'q': query, 'limit': limit})
    return [_record('Wikipedia', 'encyclopedia article', page.get('title', ''),
                    url='https://en.wikipedia.org/wiki/' + parse.quote(page.get('key', ''), safe=''),
                    abstract=page.get('excerpt', ''), description=page.get('description') or '')
            for page in _json(url).get('pages', [])]


def oeis(query, limit=10):
    """Integer sequences. A query can be words or comma-separated terms such as 1,2,3,6,11."""
    _check(query, limit)
    data = _json('https://oeis.org/search?' + parse.urlencode({'q': query, 'fmt': 'json', 'start': 0}))
    results = []
    for item in (data if isinstance(data, list) else _dig(data, 'results', default=[]) or [])[:limit]:
        number = f'A{int(item.get("number", 0)):06d}'
        results.append(_record(
            'OEIS', 'integer sequence', item.get('name', ''), authors=_names([_text(item.get('author', '')).strip('_ ')]),
            published=str(item.get('time', ''))[:10], url=f'https://oeis.org/{number}', oeis_id=number,
            first_terms=_text(item.get('data', ''))[:200]))
    return results


def medlineplus(query, limit=10):
    """Plain-language health topics from the U.S. National Library of Medicine. General information only."""
    _check(query, limit, maximum=20)
    root = _xml('https://wsearch.nlm.nih.gov/ws/query?' + parse.urlencode(
        {'db': 'healthTopics', 'term': query, 'retmax': limit}), accept='text/xml')
    results = []
    for doc in root.iter('document'):
        content = {}
        for node in doc.findall('content'):
            content.setdefault(node.get('name'), (node.text or ''))
        results.append(_record(
            'MedlinePlus', 'health topic', content.get('title', ''), url=doc.get('url', ''),
            abstract=content.get('FullSummary') or content.get('snippet', ''),
            publisher=content.get('organizationName', '')))
    return results[:limit]


def reactome(query, limit=10):
    _check(query, limit)
    url = 'https://reactome.org/ContentService/search/query?' + parse.urlencode(
        {'query': query, 'cluster': 'true', 'rows': limit, 'species': 'Homo sapiens'})
    results = []
    for group in _json(url).get('results', []):
        for entry in group.get('entries', []):
            stid = entry.get('stId', '')
            results.append(_record(
                'Reactome', str(entry.get('exactType') or group.get('typeName') or 'entry').lower(), entry.get('name', ''),
                url=f'https://reactome.org/content/detail/{stid}' if stid else '', abstract=entry.get('summation', ''),
                reactome_id=stid, species=list(entry.get('species') or [])))
    return results[:limit]


def exoplanets(query, limit=10):
    """Confirmed exoplanets by planet or host star name, from the NASA Exoplanet Archive."""
    _check(query, limit)
    safe = re.sub(r'[^A-Za-z0-9 .+-]', '', query).strip().lower()
    if not re.search(r'[a-z0-9]', safe):
        raise ValueError('query must contain letters or digits')
    adql = (f'select top {limit} pl_name,hostname,disc_year,discoverymethod,pl_orbper,pl_rade,pl_masse '
            f"from pscomppars where lower(pl_name) like '%{safe}%' or lower(hostname) like '%{safe}%'")
    data = _json('https://exoplanetarchive.ipac.caltech.edu/TAP/sync?' + parse.urlencode({'query': adql, 'format': 'json'}))
    return [_record(
        'NASA Exoplanet Archive', 'exoplanet', row.get('pl_name', ''), published=str(row.get('disc_year') or ''),
        url='https://exoplanetarchive.ipac.caltech.edu/overview/' + parse.quote(str(row.get('pl_name', '')), safe=''),
        host_star=row.get('hostname', ''), discovery_method=row.get('discoverymethod') or '',
        orbital_period_days=row.get('pl_orbper'), radius_earth=row.get('pl_rade'), mass_earth=row.get('pl_masse'))
        for row in (data if isinstance(data, list) else [])]


ECB_SERIES = re.compile(r'^[A-Z0-9_]{2,12}/[A-Za-z0-9_.+]{1,80}$')
IMF_COUNTRY = re.compile(r'^[A-Za-z]{3}$')
IMF_INDICATOR = re.compile(r'^[A-Za-z0-9_]{2,40}$')


def imf(country, indicator, limit=10):
    """Latest annual values of one IMF DataMapper indicator for a country. Later years are IMF projections."""
    if not IMF_COUNTRY.match(country or ''):
        raise ValueError('country must be a 3 letter ISO code, for example ESP')
    if not IMF_INDICATOR.match(indicator or ''):
        raise ValueError('indicator must look like NGDP_RPCH')
    _check('x', limit)
    country, indicator = country.upper(), indicator.upper()
    data = _json(f'https://www.imf.org/external/datamapper/api/v1/{indicator}/{country}',
                 not_found='the IMF has no such indicator or country')
    values = _dig(data, 'values', indicator, country, default=None)
    if not values:
        raise ValueError('the IMF returned no data for that indicator and country')
    this_year = datetime.date.today().year
    rows = sorted(values.items(), reverse=True)[:limit]
    return [{'source': 'IMF DataMapper', 'kind': 'indicator', 'country_code': country, 'indicator_id': indicator,
             'year': year, 'value': value, 'is_projection': int(year) >= this_year,
             'url': f'https://www.imf.org/external/datamapper/{indicator}@WEO', 'status': 'unverified'}
            for year, value in rows]


def _lang(value):
    """Pick the English text from a {language: text} mapping, else the first one."""
    if isinstance(value, dict):
        return value.get('en') or next((v for v in value.values() if v), '')
    return value or ''


def federalregister(query, limit=10):
    _check(query, limit)
    fields = ('title', 'abstract', 'html_url', 'publication_date', 'type', 'agencies', 'document_number')
    url = 'https://www.federalregister.gov/api/v1/documents.json?' + parse.urlencode(
        [('conditions[term]', query), ('per_page', limit), ('order', 'relevance')] + [('fields[]', f) for f in fields])
    return [_record(
        'Federal Register', 'regulatory document', doc.get('title', ''), published=doc.get('publication_date', ''),
        url=doc.get('html_url', ''), abstract=doc.get('abstract') or '', document_type=doc.get('type', ''),
        agencies=[_text(a.get('name') or a.get('raw_name', '')) for a in doc.get('agencies') or []][:6],
        document_number=doc.get('document_number', '')) for doc in _json(url).get('results', [])]


def clevelandart(query, limit=10):
    _check(query, limit)
    url = 'https://openaccess-api.clevelandart.org/api/artworks/?' + parse.urlencode({'q': query, 'limit': limit})
    return [_record(
        'Cleveland Museum of Art', 'artwork', item.get('title', ''),
        authors=_names(c.get('description', '') for c in item.get('creators') or []),
        published=item.get('creation_date') or '', url=item.get('url', ''), medium=item.get('technique') or '',
        department=item.get('department') or '', object_type=item.get('type') or '')
        for item in _json(url).get('data', [])]


def vam(query, limit=10):
    _check(query, limit)
    url = 'https://api.vam.ac.uk/v2/objects/search?' + parse.urlencode({'q': query, 'page_size': limit})
    results = []
    for item in _json(url).get('records', []):
        number = item.get('systemNumber', '')
        results.append(_record(
            'Victoria and Albert Museum', 'museum object', item.get('_primaryTitle') or item.get('objectType', ''),
            authors=_names([_dig(item, '_primaryMaker', 'name', default='')]), published=item.get('_primaryDate') or '',
            url=f'https://collections.vam.ac.uk/item/{number}/' if number else '', object_type=item.get('objectType', ''),
            place=item.get('_primaryPlace') or ''))
    return results


def wellcome(query, limit=10):
    _check(query, limit)
    url = 'https://api.wellcomecollection.org/catalogue/v2/works?' + parse.urlencode({'query': query, 'pageSize': limit})
    return [_record(
        'Wellcome Collection', 'library or archive item', item.get('title', ''),
        url=f'https://wellcomecollection.org/works/{item.get("id")}', object_type=_dig(item, 'workType', 'label', default=''),
        reference=item.get('referenceNumber', ''), description=item.get('physicalDescription', ''))
        for item in _json(url).get('results', [])]


def quickgo(query, limit=10):
    _check(query, limit)
    url = 'https://www.ebi.ac.uk/QuickGO/services/ontology/go/search?' + parse.urlencode({'query': query, 'limit': limit})
    return [_record(
        'Gene Ontology', 'ontology term', item.get('name', ''), url=f'https://www.ebi.ac.uk/QuickGO/term/{item.get("id")}',
        abstract=_dig(item, 'definition', 'text', default=''), go_id=item.get('id', ''), aspect=item.get('aspect', ''),
        obsolete=bool(item.get('isObsolete'))) for item in _json(url).get('results', [])]


def europeandata(query, limit=10):
    _check(query, limit)
    url = 'https://data.europa.eu/api/hub/search/search?' + parse.urlencode({'q': query, 'limit': limit})
    results = []
    for item in _dig(_json(url), 'result', 'results', default=[]):
        ident = item.get('id', '')
        results.append(_record(
            'data.europa.eu', 'dataset', _lang(item.get('title')), published=str(item.get('issued', ''))[:10],
            url=f'https://data.europa.eu/data/datasets/{ident}' if ident else '', abstract=_lang(item.get('description')),
            publisher=_dig(item, 'publisher', 'name', default=''), deposit_not_curated=True))
    return results


def dryad(query, limit=10):
    _check(query, limit)
    url = 'https://datadryad.org/api/v2/search?' + parse.urlencode({'q': query, 'per_page': limit})
    results = []
    for item in _dig(_json(url), '_embedded', 'stash:datasets', default=[]):
        doi = str(item.get('identifier', '')).replace('doi:', '')
        names = [f'{a.get("firstName", "")} {a.get("lastName", "")}'.strip() for a in item.get('authors') or []]
        results.append(_record(
            'Dryad', 'dataset', item.get('title', ''), authors=_names(names), published=item.get('publicationDate', ''),
            doi=doi, url=f'https://doi.org/{doi}' if doi else '', abstract=item.get('abstract', ''),
            field_of_science=item.get('fieldOfScience', '')))
    return results


def figshare(query, limit=10):
    _check(query, limit)
    url = 'https://api.figshare.com/v2/articles?' + parse.urlencode({'search_for': query, 'page_size': limit})
    data = _json(url)
    return [_record(
        'Figshare', str(item.get('defined_type_name') or 'deposit'), item.get('title', ''),
        published=str(item.get('published_date', ''))[:10], doi=item.get('doi', ''),
        url=item.get('url_public_html') or item.get('url', ''), deposit_not_curated=True)
        for item in (data if isinstance(data, list) else [])]


def mesh(query, limit=10):
    """Medical Subject Headings whose label contains the query. Useful for building PubMed searches."""
    _check(query, limit)
    data = _json('https://id.nlm.nih.gov/mesh/lookup/descriptor?' + parse.urlencode(
        {'label': query, 'match': 'contains', 'limit': limit}))
    results = []
    for item in data if isinstance(data, list) else []:
        ident = str(item.get('resource', '')).rsplit('/', 1)[-1]
        results.append(_record('MeSH', 'vocabulary term', item.get('label', ''),
                               url=f'https://meshb.nlm.nih.gov/record/ui?ui={ident}' if ident else '', mesh_id=ident))
    return results


def wiktionary(query, limit=10):
    """Dictionary entries for orientation about words. Anyone can edit them."""
    _check(query, limit)
    url = 'https://en.wiktionary.org/w/rest.php/v1/search/page?' + parse.urlencode({'q': query, 'limit': limit})
    return [_record('Wiktionary', 'dictionary entry', page.get('title', ''),
                    url='https://en.wiktionary.org/wiki/' + parse.quote(page.get('key', ''), safe=''),
                    abstract=page.get('excerpt', ''), description=page.get('description') or '')
            for page in _json(url).get('pages', [])]


def jstage(query, limit=10):
    """Articles from Japanese scholarly societies and publishers on J-STAGE."""
    _check(query, limit)
    root = _xml('https://api.jstage.jst.go.jp/searchapi/do?' + parse.urlencode(
        {'service': 3, 'text': query, 'count': limit}), accept='text/xml')
    prism = '{http://prismstandard.org/namespaces/basic/2.0/}'
    atom = '{http://www.w3.org/2005/Atom}'
    results = []
    for entry in root.findall(atom + 'entry')[:limit]:
        def get(path):
            return (entry.findtext('/'.join(atom + part for part in path.split('/'))) or '').strip()
        results.append(_record(
            'J-STAGE', 'article', get('title') or get('article_title/en'),
            authors=_names(n.text or '' for n in entry.findall('/'.join(atom + part for part in 'author/en/name'.split('/')))),
            published=get('pubyear'), journal=get('material_title/en'),
            doi=(entry.findtext(prism + 'doi') or '').strip(), url=get('article_link/en')))
    return results


def biostudies(query, limit=10):
    _check(query, limit)
    url = 'https://www.ebi.ac.uk/biostudies/api/v1/search?' + parse.urlencode({'query': query, 'pageSize': limit})
    results = []
    for hit in _json(url).get('hits', []):
        acc = hit.get('accession', '')
        results.append(_record(
            'BioStudies', str(hit.get('type') or 'study'), hit.get('title', ''),
            published=hit.get('release_date', ''), author_line=_text(hit.get('author', ''))[:300],
            url=f'https://www.ebi.ac.uk/biostudies/studies/{acc}' if acc else '', accession=acc, deposit_not_curated=True))
    return results


RETRACTION_NOTE = ('Crossref lists only the notices that publishers or Retraction Watch have deposited. '
                   'No notice found does not prove that a paper is sound.')
DOI_PATTERN = re.compile(r'^10\.\d{4,9}/\S+$')


def retractions(doi):
    """Notices of retraction, correction or concern that Crossref holds for one DOI."""
    doi = (doi or '').strip()
    doi = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:)', '', doi, flags=re.I)
    if not DOI_PATTERN.match(doi):
        raise ValueError('expected a DOI such as 10.1016/S0140-6736(97)11096-0')
    url = 'https://api.crossref.org/works?' + parse.urlencode({
        'filter': f'updates:{doi}', 'rows': 20, 'select': 'DOI,title,update-to'})
    notices = []
    for item in _dig(_json(url), 'message', 'items', default=[]):
        for update in item.get('update-to') or []:
            if str(update.get('DOI', '')).lower() != doi.lower():
                continue
            notices.append({'type': update.get('type', ''), 'label': update.get('label', ''),
                            'source': update.get('source', ''), 'date': _dig(update, 'updated', 'date-time', default='')[:10],
                            'notice_doi': item.get('DOI', ''), 'notice_title': _text((item.get('title') or [''])[0])})
    return {'doi': doi, 'retracted': any(n['type'] == 'retraction' for n in notices), 'notices': notices,
            'source': 'Crossref, including Retraction Watch data', 'note': RETRACTION_NOTE, 'status': 'unverified'}


def wikidata(query, limit=10):
    """Entities in the Wikidata knowledge base. Anyone can edit it, so it is for orientation only."""
    _check(query, limit, 50)
    url = 'https://www.wikidata.org/w/api.php?' + parse.urlencode({
        'action': 'wbsearchentities', 'search': query, 'language': 'en', 'format': 'json', 'limit': limit})
    return [_record('Wikidata', 'knowledge base entity', item.get('label') or item.get('id', ''),
                    url=item.get('concepturi', ''), abstract=item.get('description') or '', entity_id=item.get('id', ''))
            for item in _json(url).get('search', [])]


def ols(query, limit=10):
    """Ontology terms (diseases, phenotypes, chemicals, anatomy) from the EMBL-EBI Ontology Lookup Service."""
    _check(query, limit)
    url = 'https://www.ebi.ac.uk/ols4/api/search?' + parse.urlencode({
        'q': query, 'rows': limit, 'fieldList': 'iri,label,description,ontology_name,obo_id'})
    return [_record('Ontology Lookup Service', 'ontology term', doc.get('label', ''), url=doc.get('iri', ''),
                    abstract=' '.join(doc.get('description') or [])[:ABSTRACT_LIMIT], term_id=doc.get('obo_id', ''),
                    ontology=doc.get('ontology_name', ''))
            for doc in _dig(_json(url), 'response', 'docs', default=[])]


def mygene(query, limit=10):
    """Human gene records with the NCBI summary."""
    _check(query, limit)
    url = 'https://mygene.info/v3/query?' + parse.urlencode({
        'q': query, 'size': limit, 'species': 'human', 'fields': 'symbol,name,summary,entrezgene'})
    results = []
    for hit in _json(url).get('hits', []):
        gene = hit.get('entrezgene') or hit.get('_id', '')
        results.append(_record('MyGene.info', 'gene', f"{hit.get('symbol', '')}: {hit.get('name', '')}",
                               url=f'https://www.ncbi.nlm.nih.gov/gene/{gene}' if gene else '',
                               abstract=hit.get('summary', ''), gene_id=str(gene)))
    return results


def inaturalist(query, limit=10):
    """Taxa from iNaturalist. Names and ranks follow its own community taxonomy."""
    _check(query, limit, 50)
    url = 'https://api.inaturalist.org/v1/taxa?' + parse.urlencode({'q': query, 'per_page': limit})
    return [_record('iNaturalist', 'taxon', item.get('name', ''), url=f"https://www.inaturalist.org/taxa/{item.get('id')}",
                    rank=item.get('rank', ''), common_name=item.get('preferred_common_name') or '',
                    group=item.get('iconic_taxon_name') or '', extinct=item.get('extinct'))
            for item in _json(url).get('results', [])]


def nasaimages(query, limit=10):
    """NASA image, video and audio library records. Most media are public domain; check each record."""
    _check(query, limit)
    url = 'https://images-api.nasa.gov/search?' + parse.urlencode({'q': query, 'page_size': limit})
    results = []
    for item in _dig(_json(url), 'collection', 'items', default=[]):
        data = (item.get('data') or [{}])[0]
        nasa_id = data.get('nasa_id', '')
        results.append(_record('NASA Image and Video Library', 'media item', data.get('title', ''),
                               url='https://images.nasa.gov/details/' + parse.quote(nasa_id, safe='') if nasa_id else '',
                               published=(data.get('date_created') or '')[:10], abstract=data.get('description_508') or data.get('description') or '',
                               media_type=data.get('media_type', ''), nasa_id=nasa_id))
    return results


def cernopen(query, limit=10):
    """Datasets, software and documentation released by CERN experiments."""
    _check(query, limit)
    url = 'https://opendata.cern.ch/api/records/?' + parse.urlencode({'q': query, 'size': limit})
    results = []
    for hit in _dig(_json(url), 'hits', 'hits', default=[]):
        meta = hit.get('metadata') or {}
        doi = meta.get('doi') or ''
        results.append(_record('CERN Open Data', _dig(meta, 'type', 'primary', default='') .lower() or 'record',
                               meta.get('title', ''), published=str(meta.get('date_published') or ''), doi=doi,
                               url=f"https://opendata.cern.ch/record/{hit.get('id')}",
                               abstract=_dig(meta, 'abstract', 'description', default=''),
                               experiment=', '.join(meta.get('experiment') or [])))
    return results


def ror(query, limit=10):
    """Research organizations from the Research Organization Registry (names, type, country, website)."""
    _check(query, limit, 20)
    url = 'https://api.ror.org/v2/organizations?' + parse.urlencode({'query': query})
    results = []
    for item in _json(url).get('items', [])[:limit]:
        names = item.get('names') or []
        display = next((n['value'] for n in names if 'ror_display' in (n.get('types') or [])), '') or (names[0]['value'] if names else '')
        place = _dig(item, 'locations', 0, 'geonames_details', default={}) or {}
        site = next((l['value'] for l in item.get('links') or [] if l.get('type') == 'website'), '')
        results.append(_record('ROR', 'organization', display, url=item.get('id', ''), website=site,
                               org_types=item.get('types') or [], country=place.get('country_name', ''),
                               city=place.get('name', ''), org_status=item.get('status', '')))
    return results


def worms(query, limit=10):
    """Marine species names from the World Register of Marine Species (exact genus or species name, prefix match)."""
    _check(query, limit, 50)
    if not re.search(r'[A-Za-z]', query):
        raise ValueError('query must be a scientific name such as Gadus')
    url = ('https://www.marinespecies.org/rest/AphiaRecordsByName/' + parse.quote(query.strip(), safe='') +
           '?' + parse.urlencode({'like': 'true', 'marine_only': 'true', 'offset': 1}))
    try:
        rows = _json(url)
    except ValueError as exc:
        if 'HTTP status 204' in str(exc):
            return []
        raise
    return [_record('WoRMS', 'taxon', row.get('scientificname', ''), url=row.get('url', '').replace('\\/', '/'),
                    rank=row.get('rank', ''), taxonomic_status=row.get('status', ''), valid_name=row.get('valid_name', ''),
                    family=row.get('family') or '', kingdom=row.get('kingdom') or '')
            for row in (rows if isinstance(rows, list) else [])[:limit]]


def paleobiodb(query, limit=10):
    """Fossil taxa from the Paleobiology Database (scientific name, prefix match)."""
    _check(query, limit)
    if not re.fullmatch(r'[A-Za-z .%*-]+', query.strip()):
        raise ValueError('query must be a scientific name such as Tyrannosaurus')
    url = 'https://paleobiodb.org/data1.2/taxa/list.json?' + parse.urlencode({'name': query.strip().rstrip('*') + '%', 'limit': limit})
    return [_record('Paleobiology Database', 'fossil taxon', row.get('nam', ''),
                    url='https://paleobiodb.org/classic/basicTaxonInfo?taxon_no=' + str(row.get('oid', '')).replace('txn:', ''),
                    authority=row.get('att', ''), occurrences=row.get('noc'))
            for row in _json(url).get('records', [])]


def chebi(query, limit=10):
    """Small chemical entities (formula, mass, definition) from ChEBI."""
    _check(query, limit, 50)
    url = 'https://www.ebi.ac.uk/chebi/backend/api/public/es_search/?' + parse.urlencode({'term': query, 'size': limit})
    results = []
    for hit in _json(url).get('results', []):
        row = hit.get('_source') or {}
        accession = row.get('chebi_accession', '')
        results.append(_record('ChEBI', 'chemical entity', row.get('name', ''),
                               url=f'https://www.ebi.ac.uk/chebi/searchId.do?chebiId={accession}' if accession else '',
                               abstract=row.get('definition') or '', chebi_id=accession, formula=row.get('formula') or '',
                               mass=row.get('mass')))
    return results


def wikisource(query, limit=10):
    """Source texts hosted on Wikisource. Anyone can edit transcriptions, so check them against the edition."""
    _check(query, limit, 50)
    url = 'https://en.wikisource.org/w/api.php?' + parse.urlencode({
        'action': 'query', 'list': 'search', 'srsearch': query, 'srlimit': limit, 'format': 'json'})
    return [_record('Wikisource', 'source text', row.get('title', ''),
                    url='https://en.wikisource.org/wiki/' + parse.quote(row.get('title', '').replace(' ', '_'), safe='/:'),
                    abstract=html.unescape(_text(row.get('snippet', ''))), published=(row.get('timestamp') or '')[:10])
            for row in _dig(_json(url), 'query', 'search', default=[])]


def ecb(series, limit=10):
    """Latest observations of one ECB Data Portal series, for example EXR/D.USD.EUR.SP00.A."""
    if not ECB_SERIES.match(series or ''):
        raise ValueError('series must look like EXR/D.USD.EUR.SP00.A (dataflow/key)')
    _check('x', limit)
    url = (f'https://data-api.ecb.europa.eu/service/data/{series}?' +
           parse.urlencode({'lastNObservations': limit, 'format': 'jsondata'}))
    data = _json(url, not_found='the ECB has no such series')
    sets = data.get('dataSets') or []
    structure = _dig(data, 'structure', 'dimensions', 'observation', 0, 'values', default=[])
    series_data = _dig(sets, 0, 'series', default={}) or {}
    if not series_data:
        raise ValueError('the ECB returned no observations for that series')
    title = _dig(data, 'structure', 'name', default='')
    rows = []
    for item in series_data.values():
        for position, values in (item.get('observations') or {}).items():
            period = _dig(structure, int(position), 'id', default='')
            rows.append({'source': 'ECB Data Portal', 'kind': 'indicator', 'series': series, 'dataset': title,
                         'period': period, 'value': values[0] if values else None,
                         'url': 'https://data.ecb.europa.eu/data/datasets/' + series.split('/')[0], 'status': 'unverified'})
    return sorted(rows, key=lambda r: r['period'], reverse=True)[:limit]


def nsf(query, limit=10):
    """Research grants awarded by the U.S. National Science Foundation. Awards describe plans, not results."""
    _check(query, limit, 25)
    url = 'https://api.nsf.gov/services/v1/awards.json?' + parse.urlencode({
        'keyword': query, 'rpp': limit, 'printFields': 'id,title,abstractText,startDate,piFirstName,piLastName,awardeeName'})
    results = []
    for award in _dig(_json(url), 'response', 'award', default=[]):
        pi = ' '.join(x for x in (award.get('piFirstName'), award.get('piLastName')) if x)
        results.append(_record('NSF Awards', 'research grant', award.get('title', ''), authors=_names([pi]) if pi else [],
                               published=award.get('startDate', ''), abstract=award.get('abstractText', ''),
                               url='https://www.nsf.gov/awardsearch/showAward?AWD_ID=' + str(award.get('id', '')),
                               institution=award.get('awardeeName', '')))
    return results


def cordis(query, limit=10):
    """Research projects funded by the European Union (Horizon 2020, Horizon Europe and earlier programmes)."""
    _check(query, limit, 50)
    words = re.sub(r"[^\w ]", ' ', query, flags=re.U).split()
    if not words:
        raise ValueError('query must contain letters or digits')
    expression = "contenttype='project' AND '" + ' '.join(words) + "'"
    data = _json('https://cordis.europa.eu/search?' + parse.urlencode({'q': expression, 'format': 'json', 'num': limit}))
    hits = _dig(data, 'hits', 'hit', default=[])
    results = []
    for hit in hits if isinstance(hits, list) else [hits]:
        project = (hit or {}).get('project') or {}
        results.append(_record('CORDIS', 'funded project', project.get('title', ''), published=project.get('startDate', ''),
                               abstract=project.get('teaser') or project.get('objective', ''),
                               url=f"https://cordis.europa.eu/project/id/{project.get('id', '')}" if project.get('id') else '',
                               acronym=project.get('acronym', ''), project_status=project.get('status', ''),
                               eu_contribution_eur=project.get('ecMaxContribution'), end_date=project.get('endDate', '')))
    return results


def datagovuk(query, limit=10):
    """Datasets published by United Kingdom public bodies (CKAN catalogue)."""
    _check(query, limit)
    data = _json('https://data.gov.uk/api/action/package_search?' + parse.urlencode({'q': query, 'rows': limit}))
    return [_record('data.gov.uk', 'dataset', item.get('title', ''), abstract=item.get('notes', ''),
                    published=(item.get('metadata_modified') or '')[:10],
                    url='https://www.data.gov.uk/dataset/' + str(item.get('id', '')),
                    publisher=_dig(item, 'organization', 'title', default=''), licence=item.get('license_title') or '')
            for item in _dig(data, 'result', 'results', default=[])]


def datosgob(query, limit=10):
    """Datasets published by Spanish public bodies (datos.gob.es), by a word in the title."""
    _check(query, limit)
    url = ('https://datos.gob.es/apidata/catalog/dataset/title/' + parse.quote(query.strip(), safe='') +
           '?' + parse.urlencode({'_pageSize': limit, '_page': 0}))
    results = []
    for item in _dig(_json(url), 'result', 'items', default=[]):
        title = item.get('title')
        description = item.get('description')
        about = item.get('_about', '')
        results.append(_record('datos.gob.es', 'dataset', _pick(title) if isinstance(title, list) else title,
                               abstract=_pick(description) if isinstance(description, list) else description,
                               url=about if about.startswith('https://datos.gob.es/') else ''))
    return results


def _pick(values):
    """Choose the Spanish or English text from a list of {_value, _lang} entries, else the first."""
    by_lang = {v.get('_lang'): v.get('_value', '') for v in values if isinstance(v, dict)}
    return by_lang.get('es') or by_lang.get('en') or next(iter(by_lang.values()), '')


def icd10cm(query, limit=10):
    """ICD-10-CM diagnosis codes (the United States clinical modification) by word or code. A code is a label, not a diagnosis."""
    _check(query, limit, 50)
    data = _json('https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?' + parse.urlencode({
        'terms': query, 'maxList': limit, 'sf': 'code,name'}))
    rows = data[3] if isinstance(data, list) and len(data) > 3 and data[3] else []
    return [_record('ICD-10-CM', 'diagnosis code', row[1], term_id=row[0], url='https://icd10cmtool.cdc.gov/?fy=FY2026&q=' + parse.quote(row[0]))
            for row in rows if isinstance(row, list) and len(row) >= 2]


def sdg(query, limit=10):
    """United Nations Sustainable Development Goal indicators whose wording or code contains the query."""
    _check(query, limit)
    needle = query.strip().lower()
    results = []
    for row in _json('https://unstats.un.org/sdgapi/v1/sdg/Indicator/List'):
        text = str(row.get('description', ''))
        if needle in text.lower() or needle == str(row.get('code', '')).lower():
            results.append(_record('UN SDG indicators', 'indicator definition', text, term_id=str(row.get('code', '')),
                                   goal=str(row.get('goal', '')), tier=str(row.get('tier', '')),
                                   url='https://unstats.un.org/sdgs/metadata/?Text=&Goal=' + str(row.get('goal', '')) + '&Target=' + str(row.get('target', ''))))
            if len(results) >= limit:
                break
    return results


def earthquakes(min_magnitude=6.0, limit=10):
    """Most recent earthquakes of at least the given magnitude, from the USGS catalogue (statistics, not studies)."""
    if not isinstance(min_magnitude, (int, float)) or isinstance(min_magnitude, bool) or not 0 <= min_magnitude <= 10:
        raise ValueError('minimum magnitude must be a number between 0 and 10')
    _check('x', limit, 200)
    url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?' + parse.urlencode({
        'format': 'geojson', 'limit': limit, 'minmagnitude': min_magnitude, 'orderby': 'time'})
    rows = []
    for feature in _json(url).get('features', []):
        props = feature.get('properties') or {}
        millis = props.get('time')
        when = datetime.datetime.fromtimestamp(millis / 1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if isinstance(millis, (int, float)) else ''
        rows.append({'source': 'USGS Earthquake Catalog', 'kind': 'event', 'place': props.get('place', ''), 'magnitude': props.get('mag'),
                     'time': when, 'event_status': props.get('status', ''), 'tsunami_flag': props.get('tsunami'),
                     'url': props.get('url', ''), 'status': 'unverified'})
    return rows


# ---------------------------------------------------------------- registry

SOURCES = {
    'europepmc': {'func': europepmc, 'name': 'Europe PMC', 'field': 'Life sciences, medicine',
                  'about': 'PubMed records, PubMed Central, preprints and patents; use --preprints for preprints only'},
    'arxiv': {'func': arxiv, 'name': 'arXiv', 'field': 'Physics, mathematics, computer science',
              'about': 'Preprints, not peer reviewed; one request every three seconds at most'},
    'doaj': {'func': doaj, 'name': 'DOAJ', 'field': 'All fields',
             'about': 'Articles from vetted open-access journals'},
    'plos': {'func': plos, 'name': 'PLOS', 'field': 'Biology, medicine, science',
             'about': 'Open-access articles in PLOS journals; Solr query syntax'},
    'inspire': {'func': inspire, 'name': 'INSPIRE-HEP', 'field': 'High-energy physics',
                'about': 'Literature of the high-energy physics community'},
    'zenodo': {'func': zenodo, 'name': 'Zenodo', 'field': 'All fields',
               'about': 'Datasets, software and papers that anyone can deposit; not curated'},
    'datacite': {'func': datacite, 'name': 'DataCite', 'field': 'All fields',
                 'about': 'Metadata for datasets and other outputs with a DOI'},
    'clinicaltrials': {'func': clinicaltrials, 'name': 'ClinicalTrials.gov', 'field': 'Clinical research',
                       'about': 'Registered studies, not published results'},
    'osf': {'func': osf, 'name': 'OSF Preprints', 'field': 'Psychology, social science, law, education, earth science',
            'about': 'Preprint servers such as PsyArXiv and SocArXiv; title search; use --provider to pick one'},
    'eric': {'func': eric, 'name': 'ERIC', 'field': 'Education',
             'about': 'U.S. education research index; peer_reviewed shows the index flag'},
    'zbmath': {'func': zbmath, 'name': 'zbMATH Open', 'field': 'Mathematics',
               'about': 'Bibliographic records and reviews of mathematical literature'},
    'uniprot': {'func': uniprot, 'name': 'UniProt', 'field': 'Biochemistry, molecular biology',
                'about': 'Protein records; facts about a molecule, not papers'},
    'pubchem': {'func': pubchem, 'name': 'PubChem', 'field': 'Chemistry',
                'about': 'One compound by name with formula, weight and identifiers'},
    'rcsb': {'func': rcsb, 'name': 'RCSB PDB', 'field': 'Structural biology',
             'about': '3D structures; at most 10 results because each needs its own request'},
    'hal': {'func': hal, 'name': 'HAL', 'field': 'All fields, strong in French research',
            'about': 'French national open archive of papers, theses and preprints'},
    'openaire': {'func': openaire, 'name': 'OpenAIRE', 'field': 'All fields',
                 'about': 'European aggregator of open publications; refereed shows the repository flag'},
    'chembl': {'func': chembl, 'name': 'ChEMBL', 'field': 'Medicinal chemistry, pharmacology',
               'about': 'Bioactive molecules and drug facts (20 results at most); not papers'},
    'gbif': {'func': gbif, 'name': 'GBIF', 'field': 'Biodiversity, ecology, taxonomy',
             'about': 'Species names and taxonomy from the global backbone'},
    'openlibrary': {'func': openlibrary, 'name': 'Open Library', 'field': 'Humanities, books of any field',
                    'about': 'Book catalogue: titles, authors and first publication year'},
    'gutenberg': {'func': gutenberg, 'name': 'Project Gutenberg', 'field': 'Humanities, literature, history',
                  'about': 'Public domain books in the United States; check your local copyright law'},
    'econbiz': {'func': econbiz, 'name': 'EconBiz', 'field': 'Economics, business, finance',
                'about': 'Economics literature from the ZBW library, including working papers that are not peer reviewed'},
    'ntrs': {'func': ntrs, 'name': 'NASA NTRS', 'field': 'Aerospace, engineering, space science',
             'about': 'NASA technical reports; document_type shows whether one was peer reviewed'},
    'dataverse': {'func': dataverse, 'name': 'Harvard Dataverse', 'field': 'Social science and any field with datasets',
                  'about': 'Research datasets that anyone can deposit; not curated'},
    'artic': {'func': artic, 'name': 'Art Institute of Chicago', 'field': 'Art and art history',
              'about': 'Museum collection records for artworks, not scholarship about them'},
    'internetarchive': {'func': internetarchive, 'name': 'Internet Archive', 'field': 'History, humanities, any field',
                        'about': 'Scanned books, texts and media that anyone can upload; check the edition'},
    'wikipedia': {'func': wikipedia, 'name': 'Wikipedia', 'field': 'Orientation in any field',
                  'about': 'Encyclopedia articles anyone can edit; use them to find terms and sources, never as evidence'},
    'oeis': {'func': oeis, 'name': 'OEIS', 'field': 'Mathematics',
             'about': 'Integer sequences by words or terms such as 1,2,3,6,11'},
    'medlineplus': {'func': medlineplus, 'name': 'MedlinePlus', 'field': 'Consumer health information',
                    'about': 'Plain-language health topics from the U.S. National Library of Medicine; general information, not advice'},
    'reactome': {'func': reactome, 'name': 'Reactome', 'field': 'Biochemistry, cell biology',
                 'about': 'Curated human biological pathways and reactions'},
    'exoplanets': {'func': exoplanets, 'name': 'NASA Exoplanet Archive', 'field': 'Astronomy',
                   'about': 'Confirmed exoplanets by planet or host star name'},
    'federalregister': {'func': federalregister, 'name': 'Federal Register', 'field': 'Law and public policy (United States)',
                        'about': 'Rules, proposed rules and notices of U.S. federal agencies; not court rulings and not legal advice'},
    'clevelandart': {'func': clevelandart, 'name': 'Cleveland Museum of Art', 'field': 'Art and art history',
                     'about': 'Museum records for artworks in its open access collection'},
    'vam': {'func': vam, 'name': 'Victoria and Albert Museum', 'field': 'Art, design, decorative arts',
            'about': 'Museum records for design and decorative objects'},
    'wellcome': {'func': wellcome, 'name': 'Wellcome Collection', 'field': 'History of medicine and health',
                 'about': 'Library and archive catalogue of books, manuscripts and images on health and the human condition'},
    'quickgo': {'func': quickgo, 'name': 'Gene Ontology', 'field': 'Biology, genetics',
                'about': 'Gene Ontology terms with their definitions, through QuickGO'},
    'europeandata': {'func': europeandata, 'name': 'data.europa.eu', 'field': 'Public data, any field',
                     'about': 'Open datasets published by European public bodies; quality varies by publisher'},
    'dryad': {'func': dryad, 'name': 'Dryad', 'field': 'Biology, ecology, any field with datasets',
              'about': 'Research data linked to published articles'},
    'figshare': {'func': figshare, 'name': 'Figshare', 'field': 'Datasets, figures and software in any field',
                 'about': 'Research outputs that anyone can deposit; not curated'},
    'mesh': {'func': mesh, 'name': 'MeSH', 'field': 'Medicine, vocabulary',
             'about': 'Medical Subject Headings by label, for building better PubMed searches'},
    'wiktionary': {'func': wiktionary, 'name': 'Wiktionary', 'field': 'Languages and linguistics',
                   'about': 'Dictionary entries anyone can edit; use them to check words, not as evidence'},
    'jstage': {'func': jstage, 'name': 'J-STAGE', 'field': 'All fields, Japanese research',
               'about': 'Articles from Japanese scholarly societies and publishers'},
    'biostudies': {'func': biostudies, 'name': 'BioStudies', 'field': 'Life sciences data and articles',
                   'about': 'Study records from EMBL-EBI, including full-text articles and omics datasets'},
    'wikidata': {'func': wikidata, 'name': 'Wikidata', 'field': 'Orientation in any field',
                 'about': 'Knowledge base entities anyone can edit; use them to find identifiers and terms, never as evidence'},
    'ols': {'func': ols, 'name': 'Ontology Lookup Service', 'field': 'Biomedicine, vocabulary',
            'about': 'Terms for diseases, phenotypes, chemicals and anatomy across many ontologies'},
    'mygene': {'func': mygene, 'name': 'MyGene.info', 'field': 'Genetics, molecular biology',
               'about': 'Human gene records with the NCBI summary; facts about a gene, not papers'},
    'inaturalist': {'func': inaturalist, 'name': 'iNaturalist', 'field': 'Biodiversity, natural history',
                    'about': 'Taxa with common names from a community taxonomy; GBIF is the more formal backbone'},
    'nasaimages': {'func': nasaimages, 'name': 'NASA Image and Video Library', 'field': 'Space, astronomy, history of science',
                   'about': 'NASA photos, video and audio with descriptions; check the licence note on each record'},
    'cernopen': {'func': cernopen, 'name': 'CERN Open Data', 'field': 'Particle physics',
                 'about': 'Datasets, software and documentation released by LHC experiments'},
    'ror': {'func': ror, 'name': 'ROR', 'field': 'Research organizations, any field',
            'about': 'Universities, institutes and companies with country and website (20 results at most)'},
    'worms': {'func': worms, 'name': 'WoRMS', 'field': 'Marine biology',
              'about': 'Marine species by scientific name prefix, such as Gadus; not common names'},
    'paleobiodb': {'func': paleobiodb, 'name': 'Paleobiology Database', 'field': 'Paleontology',
                   'about': 'Fossil taxa by scientific name prefix, such as Tyrannosaurus'},
    'chebi': {'func': chebi, 'name': 'ChEBI', 'field': 'Chemistry, biochemistry',
              'about': 'Small chemical entities with formula, mass and definition; facts about a molecule, not papers'},
    'wikisource': {'func': wikisource, 'name': 'Wikisource', 'field': 'Humanities, primary texts',
                   'about': 'Transcribed source texts anyone can edit; check them against the edition'},
    'nsf': {'func': nsf, 'name': 'NSF Awards', 'field': 'Research funding, any field (United States)',
            'about': 'Grants of the U.S. National Science Foundation (25 results at most); a grant describes plans, not results'},
    'cordis': {'func': cordis, 'name': 'CORDIS', 'field': 'EU-funded research, energy, engineering, any field',
               'about': 'Projects funded by European Union research programmes, with EU contribution and dates'},
    'datagovuk': {'func': datagovuk, 'name': 'data.gov.uk', 'field': 'Public data (United Kingdom)',
                  'about': 'Datasets published by UK public bodies; quality varies by publisher'},
    'datosgob': {'func': datosgob, 'name': 'datos.gob.es', 'field': 'Public data (Spain)',
                 'about': 'Datasets published by Spanish public bodies, searched by a word in the title; titles are mostly in Spanish'},
    'icd10cm': {'func': icd10cm, 'name': 'ICD-10-CM', 'field': 'Medicine, clinical coding',
                'about': 'Diagnosis codes of the U.S. clinical modification by word or code; a code is a label, not a diagnosis'},
    'sdg': {'func': sdg, 'name': 'UN SDG indicators', 'field': 'Development, sustainability, social science',
            'about': 'Definitions of the United Nations Sustainable Development Goal indicators'},
}
