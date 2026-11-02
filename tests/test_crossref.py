import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class CrossrefTests(unittest.TestCase):
    def test_search_returns_metadata_without_claiming_verification(self):
        from investingos.crossref import search
        data = {'message': {'items': [{'title': ['Example'], 'DOI': '10.1/example', 'URL': 'https://doi.org/10.1/example'}]}}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(data).encode())):
            results = search('Example')
        self.assertEqual(results[0]['title'], 'Example')
        self.assertEqual(results[0]['url'], 'https://doi.org/10.1/example')
        self.assertEqual(results[0]['status'], 'unverified')

    def test_rejects_empty_query(self):
        from investingos.crossref import search
        with self.assertRaises(ValueError):
            search('  ')
