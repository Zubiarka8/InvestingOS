import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from investingos.core import add_claim, add_node, add_source, audit, create_project
from investingos.export import export


class ClaimNodeTests(unittest.TestCase):
    def test_linked_claim_and_source_are_exported(self):
        project = create_project('Research')
        node = add_node(project, 'Topic')
        source = add_source(project, 'Paper', url='https://example.com', locator='p. 1')
        claim = add_claim(project, 'Statement', sources=[source['id']], nodes=[node['id']])
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'export'
            export(project, directory)
            text = (directory / (node['id'] + '.md')).read_text(encoding='utf-8')
            self.assertIn('Statement', text)
            self.assertIn('unverified', text)
            self.assertIn('https://example.com', text)
            self.assertIn('p. 1', text)
            self.assertIn(claim['id'], text)

    def test_missing_node_is_rejected_and_audited(self):
        project = create_project('Research')
        with self.assertRaises(ValueError):
            add_claim(project, 'Statement', nodes=['missing'])
        node = add_node(project, 'Topic')
        add_claim(project, 'Statement', nodes=[node['id']])
        project['nodes'].clear()
        self.assertTrue(any('broken claim node' in e for e in audit(project)))
