"""Look up one record in the Oxford University Research Archive (ORA) through its OAI-PMH interface.

ORA is open access and asks harvesters not to scrape its pages. Its OAI-PMH endpoint cannot search
by keyword, so this module fetches a single record by identifier. Results are metadata leads, not
verified claims, and individual files may carry their own licences.
"""
import re
from urllib import error, request
from xml.etree import ElementTree

ENDPOINT = 'https://ora.ox.ac.uk/oai2'
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
MAX_BYTES = 2 * 1024 * 1024
DC = '{http://purl.org/dc/elements/1.1/}'
OAI = '{http://www.openarchives.org/OAI/2.0/}'
LIST_FIELDS = ('creator', 'contributor', 'subject', 'type', 'language', 'publisher', 'rights', 'relation')


def record_uuid(reference):
    """Accept a bare UUID, 'uuid:...', an OAI identifier or an ORA /objects/ URL."""
    match = UUID.search(reference) if isinstance(reference, str) else None
    if not match or ('/' in reference and 'ora.ox.ac.uk' not in reference):
        raise ValueError('expected an ORA record UUID or an ora.ox.ac.uk URL')
    return match.group(0).lower()


def lookup(reference):
    uuid = record_uuid(reference)
    query = f'?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:ora.ox.ac.uk:uuid:{uuid}'
    req = request.Request(ENDPOINT + query, headers={
        'User-Agent': 'InvestingOS/0.1 (https://github.com/Zubiarka8/InvestingOS)', 'Accept': 'text/xml'})
    try:
        with request.urlopen(req, timeout=20) as response:
            data = response.read(MAX_BYTES + 1)
    except error.HTTPError as exc:
        raise ValueError(f'ORA request failed with HTTP status {exc.code}') from None
    except error.URLError as exc:
        raise ValueError(f'ORA request failed: {exc.reason}') from None
    if len(data) > MAX_BYTES:
        raise ValueError('ORA response is too large')
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('ORA response contains a DTD; refusing to parse it')
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        raise ValueError('ORA returned a response that is not valid XML') from None
    problem = root.find(OAI + 'error')
    if problem is not None:
        if problem.get('code') == 'idDoesNotExist':
            raise ValueError('no ORA record has that identifier')
        raise ValueError('ORA reported an error: ' + (problem.get('code') or 'unknown'))
    header = root.find(f'{OAI}GetRecord/{OAI}record/{OAI}header')
    metadata = root.find(f'{OAI}GetRecord/{OAI}record/{OAI}metadata')
    if header is None or header.get('status') == 'deleted' or metadata is None:
        raise ValueError('the ORA record is deleted or has no metadata')

    def values(name):
        return [(node.text or '').strip() for node in metadata.iter(DC + name) if (node.text or '').strip()]

    title = values('title')
    result = {'title': title[0] if title else '', 'date': (values('date') or [''])[0],
              'description': (values('description') or [''])[0],
              'url': f'https://ora.ox.ac.uk/objects/uuid:{uuid}', 'oai_identifier': f'oai:ora.ox.ac.uk:uuid:{uuid}',
              'repository': 'ORA - Oxford University Research Archive'}
    for field in LIST_FIELDS:
        result[field] = values(field)
    result['status'] = 'unverified'
    return result
