import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.import_storage import allocate_import


class ImportStorageTests(unittest.TestCase):
    def test_types_topics_and_unique_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = allocate_import(tmp, 'local', 'report.pdf', 'area/topic')
            second = allocate_import(tmp, 'local', 'report.pdf', 'area/topic')
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent.parent.relative_to(Path(tmp).resolve()).as_posix(), 'pdf/area/topic')
            self.assertEqual(first.name, 'extracted.md')
            self.assertTrue(first.parent.is_dir())
            self.assertIn('/documents/', allocate_import(tmp, 'local', 'report.docx').as_posix())
            self.assertIn('/youtube/', allocate_import(tmp, 'youtube', 'https://example.com').as_posix())
            self.assertIn('/web/', allocate_import(tmp, 'web', 'https://example.com').as_posix())

    def test_rejects_unsafe_and_nonportable_topics(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in ('../outside', '/absolute', 'x//y', 'x\\y', 'CON', 'x/..'):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    allocate_import(tmp, 'local', 'source.pdf', value)
