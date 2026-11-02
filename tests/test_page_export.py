import io
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from investingos.core import create_project, add_node

class PageExportTests(unittest.TestCase):
    def test_current_page_has_export_controls_and_print_styles(self):
        from investingos.web_viewer import render
        project = create_project('Knowledge')
        html = render(project, query='rome', section='topics')
        self.assertIn('Export PDF', html)
        self.assertIn('Export Word', html)
        self.assertIn('@media print', html)
        self.assertIn('section%3Dtopics', html)
        self.assertIn('q%3Drome', html)

    def test_previews_preserve_filtered_content_and_have_format_actions(self):
        from investingos.web_viewer import render_preview
        project = create_project('Knowledge')
        add_node(project, 'Rome & Empire')
        add_node(project, 'Athens')
        target = '/?section=topics&q=rome'
        for format_name in ('word', 'pdf'):
            with self.subTest(format=format_name):
                html = render_preview(project, target, format_name)
                self.assertIn('Rome &amp; Empire', html)
                self.assertNotIn('Athens', html)
                self.assertIn(format_name.upper() + ' preview', html)
                self.assertIn('Back to page', html)
        self.assertIn('Download Word', render_preview(project, target, 'word'))
        self.assertIn('Print or save as PDF', render_preview(project, target, 'pdf'))

    def test_preview_rejects_invalid_targets_and_formats(self):
        from investingos.web_viewer import render_preview
        project = create_project('Knowledge')
        for target, format_name in (('/import', 'word'), ('//example.com/', 'pdf'), ('/', 'other')):
            with self.subTest(target=target, format=format_name):
                with self.assertRaises(ValueError):
                    render_preview(project, target, format_name)

    def test_word_contains_current_page_content_not_unrelated_nodes(self):
        from investingos.page_export import word_document
        from investingos.web_viewer import render
        project = create_project('Knowledge')
        add_node(project, 'Rome & Empire')
        add_node(project, 'Athens')
        data = word_document(render(project, query='rome', section='topics'))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read('word/document.xml').decode('utf-8')
            self.assertIn('Rome &amp; Empire', xml)
            self.assertNotIn('Athens', xml)
            self.assertIn('word/styles.xml', archive.namelist())

    def test_import_form_does_not_expose_export_with_token(self):
        from investingos.web_viewer import render_import
        html = render_import(create_project('Knowledge'), 'SECRET')
        self.assertNotIn('Export Word', html)

    def test_export_target_must_be_an_existing_local_content_page(self):
        from investingos.web_viewer import render_page
        project = create_project('Knowledge')
        for target in ('https://example.com/', '//example.com/', '/import', '/export/word', '/node/unknown'):
            with self.subTest(target=target):
                with self.assertRaises((ValueError, KeyError)):
                    render_page(project, target)

    def test_word_contains_valid_xml(self):
        import xml.etree.ElementTree as ET
        from investingos.page_export import word_document
        from investingos.web_viewer import render
        with zipfile.ZipFile(io.BytesIO(word_document(render(create_project('Example'))))) as archive:
            for name in ('[Content_Types].xml', '_rels/.rels', 'word/document.xml', 'word/styles.xml', 'word/_rels/document.xml.rels'):
                ET.fromstring(archive.read(name))

    def test_download_endpoint_returns_docx(self):
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from urllib.parse import urlencode
        from investingos.storage import save
        from investingos.web_viewer import create_server
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'project.json'
            project = create_project('History')
            add_node(project, 'Rome')
            save(project, path)
            with patch('investingos.web_viewer.ThreadingHTTPServer', side_effect=lambda addr, handler: handler):
                handler_type = create_server(path, 8000)
            handler = object.__new__(handler_type)
            handler.path = '/export/word?' + urlencode({'from': '/?section=topics&q=Rome'})
            handler.headers = {'Host': '127.0.0.1:8000'}
            handler.server = SimpleNamespace(server_port=8000)
            handler.wfile = io.BytesIO()
            handler.send_response, handler.send_header, handler.end_headers = Mock(), Mock(), Mock()
            handler.do_GET()
            handler.send_response.assert_called_once_with(200)
            with zipfile.ZipFile(io.BytesIO(handler.wfile.getvalue())) as archive:
                self.assertIn(b'Rome', archive.read('word/document.xml'))
