import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from InvestingOS.core import create_project, add_node, add_claim, add_source
from InvestingOS.export import export
from InvestingOS.markdown_import import import_to_markdown
from InvestingOS.source_links import web_link


class SourceLinksTests(unittest.TestCase):
    def test_imported_document_links_original_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / 'source with spaces.txt'
            original.write_text('Example', encoding='utf-8')
            folder = root / 'output'
            folder.mkdir()
            target = folder / 'note.md'
            import_to_markdown(create_project('Project'), original, target)
            content = target.read_text(encoding='utf-8')
            self.assertIn('## Sources', content)
            self.assertIn('../source%20with%20spaces.txt', content)
            self.assertIn('not automatically verified', content)

    def test_export_links_recorded_sources_and_identifies_missing_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project('Project')
            node = add_node(project, 'Topic')
            source = add_source(project, 'Reference', url='https://example.org/source')
            add_claim(project, 'Statement', nodes=[node['id']], sources=[source['id']])
            no_source = add_node(project, 'Unlinked')
            out = Path(tmp) / 'export'
            export(project, out)
            self.assertIn('[Reference](https://example.org/source)', (out / (node['id'] + '.md')).read_text())
            self.assertIn('No sources are linked', (out / (no_source['id'] + '.md')).read_text())
            self.assertIn('[[sources|Browse the source library]]', (out / 'index.md').read_text())
            self.assertIn('[[' + source['id'] + '|Reference]]', (out / 'sources.md').read_text())

    def test_disallows_unsafe_link_schemes(self):
        self.assertIsNone(web_link('javascript:alert(1)'))
        self.assertIsNone(web_link('https://user:password@example.org/'))
