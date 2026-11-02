"""Search PubMed through NCBI E-utilities; results are leads, not verified claims.

An API key is optional. If NCBI_API_KEY is set it is sent with each request, which raises NCBI's
rate limit from 3 to 10 requests per second. NCBI_EMAIL, if set, is sent so NCBI can contact the
operator. The key is never printed, stored in a project or included in an error message.
"""
import json
import os
from urllib import error, parse, request

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
TOOL = 'InvestingOS'


def _get(endpoint, params):
    params = dict(params, tool=TOOL, retmode='json')
    if os.environ.get('NCBI_API_KEY'):
        params['api_key'] = os.environ['NCBI_API_KEY']
    if os.environ.get('NCBI_EMAIL'):
        params['email'] = os.environ['NCBI_EMAIL']
    req = request.Request(BASE + endpoint + '?' + parse.urlencode(params),
                          headers={'User-Agent': 'InvestingOS/0.1 (https://github.com/Zubiarka8/InvestingOS)'})
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except error.HTTPError as exc:
        if exc.code == 429:
            raise ValueError('NCBI rate limit reached; wait a moment or set NCBI_API_KEY') from None
        raise ValueError(f'NCBI request failed with HTTP status {exc.code}') from None
    except error.URLError as exc:
        raise ValueError(f'NCBI request failed: {exc.reason}') from None


def search(query, limit=10):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if not 1 <= limit <= 100:
        raise ValueError('limit must be between 1 and 100')
    found = _get('esearch.fcgi', {'db': 'pubmed', 'term': query, 'retmax': limit})
    ids = [str(item) for item in found.get('esearchresult', {}).get('idlist', [])]
    if not ids:
        return []
    summary = _get('esummary.fcgi', {'db': 'pubmed', 'id': ','.join(ids)}).get('result', {})
    results = []
    for pmid in ids:
        item = summary.get(pmid)
        if not isinstance(item, dict):
            continue
        doi = next((entry.get('value', '') for entry in item.get('articleids', [])
                    if entry.get('idtype') == 'doi'), '')
        results.append({
            'title': str(item.get('title', '')).strip(),
            'authors': [a.get('name', '') for a in item.get('authors', []) if a.get('name')],
            'journal': item.get('fulljournalname') or item.get('source', ''),
            'published': item.get('pubdate', ''),
            'pmid': pmid,
            'doi': doi,
            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
            'publication_types': list(item.get('pubtype', [])),
            'status': 'unverified',
        })
    return results
