"""Search Crossref metadata; results are leads, not verified claims."""
import json
from urllib import parse, request


def search(query, limit=10):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must not be empty')
    if not 1 <= limit <= 100:
        raise ValueError('limit must be between 1 and 100')
    url = 'https://api.crossref.org/works?' + parse.urlencode({'query': query, 'rows': limit})
    req = request.Request(url, headers={'User-Agent': 'InvestingOS/0.1 (https://github.com/Zubiarka8/InvestingOS)'})
    with request.urlopen(req, timeout=20) as response:
        result = json.load(response)
    items = result['message']['items']
    return [{'title': (item.get('title') or [''])[0], 'url': item.get('URL', ''),
             'doi': item.get('DOI', ''), 'status': 'unverified'} for item in items]
