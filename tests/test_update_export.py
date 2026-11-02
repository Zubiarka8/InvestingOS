import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.core import add_node, create_project
from InvestingOS.export import export


class ExportUpdateTests(unittest.TestCase):
    def test_update_preserves_user_edits_and_updates_unchanged(self):
        from InvestingOS.export import update_export
        p = create_project('Project')
        a, b = add_node(p, 'A'), add_node(p, 'B')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'notes'
            export(p, out)
            edited = out / (a['id'] + '.md')
            edited.write_text('My personal edits', encoding='utf-8')
            b['description'] = 'Updated description'
            report = update_export(p, out)
            self.assertEqual(edited.read_text(encoding='utf-8'), 'My personal edits')
            self.assertIn(a['id'] + '.md', report['conflicts'])
            self.assertIn('Updated description', (out / (b['id'] + '.md')).read_text(encoding='utf-8'))

    def test_update_rejects_unmanaged_directory(self):
        from InvestingOS.export import update_export
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                update_export(create_project('Project'), tmp)
