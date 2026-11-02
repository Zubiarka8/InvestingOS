import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

UUID = 'b279b3f0-a041-4c60-bf4d-f48a36a45733'
OAI = ('<?xml version="1.0"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><GetRecord><record>'
       '<header><identifier>oai:ora.ox.ac.uk:uuid:%s</identifier></header><metadata>'
       '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/">'
       '<dc:title>A thesis</dc:title><dc:creator>Lockwood, J</dc:creator><dc:subject>Music</dc:subject>'
       '<dc:subject>History</dc:subject><dc:date>2023</dc:date><dc:description>About Handel.</dc:description>'
       '<dc:relation></dc:relation></oai_dc:dc></metadata></record></GetRecord></OAI-PMH>') % UUID


def reply(text):
    return io.BytesIO(text.encode())


class OraTests(unittest.TestCase):
    def test_accepts_uuid_oai_identifier_and_ora_url_only(self):
        from InvestingOS.ora import record_uuid
        for reference in (UUID, 'uuid:' + UUID, 'oai:ora.ox.ac.uk:uuid:' + UUID.upper(),
                          f'https://ora.ox.ac.uk/objects/uuid:{UUID}'):
            self.assertEqual(record_uuid(reference), UUID)
        for bad in ('', 'not an id', f'https://evil.example/objects/uuid:{UUID}'):
            with self.assertRaises(ValueError):
                record_uuid(bad)

    def test_lookup_returns_unverified_metadata_and_public_url(self):
        from InvestingOS.ora import lookup
        with patch('urllib.request.urlopen', return_value=reply(OAI)) as opened:
            result = lookup(UUID)
        self.assertIn('identifier=oai:ora.ox.ac.uk:uuid:' + UUID, opened.call_args[0][0].full_url)
        self.assertEqual(result['title'], 'A thesis')
        self.assertEqual(result['creator'], ['Lockwood, J'])
        self.assertEqual(result['subject'], ['Music', 'History'])
        self.assertEqual(result['relation'], [])
        self.assertEqual(result['url'], f'https://ora.ox.ac.uk/objects/uuid:{UUID}')
        self.assertEqual(result['status'], 'unverified')

    def test_unknown_record_and_deleted_record_are_reported(self):
        from InvestingOS.ora import lookup
        missing = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="idDoesNotExist">x</error></OAI-PMH>'
        with patch('urllib.request.urlopen', return_value=reply(missing)):
            with self.assertRaisesRegex(ValueError, 'no ORA record'):
                lookup(UUID)
        deleted = OAI.replace('<header>', '<header status="deleted">')
        with patch('urllib.request.urlopen', return_value=reply(deleted)):
            with self.assertRaisesRegex(ValueError, 'deleted'):
                lookup(UUID)

    def test_refuses_dtd_entities_oversize_and_bad_xml(self):
        from InvestingOS import ora
        bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]>' + OAI
        for body, message in ((bomb, 'DTD'), ('<not xml', 'not valid XML')):
            with patch('urllib.request.urlopen', return_value=reply(body)):
                with self.assertRaisesRegex(ValueError, message):
                    ora.lookup(UUID)
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'x' * (ora.MAX_BYTES + 5))):
            with self.assertRaisesRegex(ValueError, 'too large'):
                ora.lookup(UUID)

    def test_network_errors_become_value_errors(self):
        from InvestingOS.ora import lookup
        with patch('urllib.request.urlopen', side_effect=error.HTTPError('u', 503, 'x', {}, None)):
            with self.assertRaisesRegex(ValueError, '503'):
                lookup(UUID)


if __name__ == '__main__':
    unittest.main()
