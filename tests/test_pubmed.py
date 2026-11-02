import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

SEARCH = {'esearchresult': {'idlist': ['111', '222']}}
SUMMARY = {'result': {'uids': ['111', '222'],
    '111': {'title': 'First study. ', 'authors': [{'name': 'Smith J'}, {'name': 'Lee K'}],
            'fulljournalname': 'Journal of Examples', 'pubdate': '2020 Jan',
            'articleids': [{'idtype': 'pubmed', 'value': '111'}, {'idtype': 'doi', 'value': '10.1/first'}],
            'pubtype': ['Randomized Controlled Trial']},
    '222': {'title': 'Second study', 'source': 'J Ex', 'pubdate': '2021', 'articleids': [], 'pubtype': []}}}


def reply(data):
    return io.BytesIO(json.dumps(data).encode())


class PubMedTests(unittest.TestCase):
    def test_search_returns_leads_in_search_order_without_claiming_verification(self):
        from investingos.pubmed import search
        with patch('urllib.request.urlopen', side_effect=[reply(SEARCH), reply(SUMMARY)]):
            results = search('example', 2)
        self.assertEqual([r['pmid'] for r in results], ['111', '222'])
        first = results[0]
        self.assertEqual(first['title'], 'First study.')
        self.assertEqual(first['doi'], '10.1/first')
        self.assertEqual(first['authors'], ['Smith J', 'Lee K'])
        self.assertEqual(first['url'], 'https://pubmed.ncbi.nlm.nih.gov/111/')
        self.assertEqual(first['status'], 'unverified')
        self.assertEqual(results[1]['journal'], 'J Ex')
        self.assertEqual(results[1]['doi'], '')

    def test_no_results_makes_only_one_request(self):
        from investingos.pubmed import search
        with patch('urllib.request.urlopen', side_effect=[reply({'esearchresult': {'idlist': []}})]) as opened:
            self.assertEqual(search('nothing matches'), [])
        self.assertEqual(opened.call_count, 1)

    def test_rejects_bad_arguments(self):
        from investingos.pubmed import search
        for query, limit in (('  ', 5), ('ok', 0), ('ok', 101)):
            with self.assertRaises(ValueError):
                search(query, limit)

    def test_api_key_is_optional_and_sent_only_when_set(self):
        from investingos.pubmed import search
        for env, expected in (({}, False), ({'NCBI_API_KEY': 'secret-key', 'NCBI_EMAIL': 'a@example.org'}, True)):
            with patch.dict(os.environ, env, clear=False), \
                    patch('urllib.request.urlopen', side_effect=[reply({'esearchresult': {'idlist': []}})]) as opened:
                if not expected:
                    os.environ.pop('NCBI_API_KEY', None)
                    os.environ.pop('NCBI_EMAIL', None)
                search('x')
            url = opened.call_args[0][0].full_url
            self.assertEqual('api_key=secret-key' in url, expected)
            self.assertEqual('email=a%40example.org' in url, expected)
            self.assertIn('tool=InvestingOS', url)

    def test_errors_do_not_leak_the_key(self):
        from investingos.pubmed import search
        failure = error.HTTPError('https://x/?api_key=secret-key', 429, 'Too Many', {}, None)
        with patch.dict(os.environ, {'NCBI_API_KEY': 'secret-key'}), \
                patch('urllib.request.urlopen', side_effect=failure):
            with self.assertRaises(ValueError) as caught:
                search('x')
        self.assertNotIn('secret-key', str(caught.exception))
        self.assertIn('rate limit', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
