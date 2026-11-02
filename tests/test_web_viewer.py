import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.core import create_project, add_node, add_source, add_claim
from InvestingOS.storage import save


class WebViewerTests(unittest.TestCase):
    def test_server_displays_project_and_escapes_content(self):
        from InvestingOS.web_viewer import create_server
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project('History')
            node = add_node(project, '<script>alert(1)</script>')
            source = add_source(project, 'Archive')
            add_claim(project, 'Claim', nodes=[node['id']], sources=[source['id']])
            path = Path(tmp) / 'project.json'
            save(project, path)
            try:
                server = create_server(path, 0)
            except PermissionError:
                self.skipTest('local socket binding is blocked in this environment')
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f'http://127.0.0.1:{server.server_port}/'
                with urlopen(url) as response:
                    html = response.read().decode('utf-8')
                self.assertIn('History', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertNotIn('<script>alert(1)</script>', html)
                self.assertIn('Archive', html)
                self.assertIn('unverified', html)
                with self.assertRaises(HTTPError) as error:
                    urlopen(url + 'missing')
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_render_escapes_untrusted_content(self):
        from InvestingOS.web_viewer import render
        project = create_project('History')
        add_node(project, '<script>alert(1)</script>')
        html = render(project)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)

    def test_search_filters_results_and_escapes_query(self):
        from InvestingOS.web_viewer import render
        project = create_project('History')
        add_node(project, 'Rome')
        add_node(project, 'Athens')
        result = render(project, query='rome')
        self.assertIn('Rome', result)
        self.assertNotIn('Athens', result)
        self.assertIn('Search', result)
        self.assertIn('&lt;script&gt;', render(project, query='<script>'))

    def test_node_detail_contains_navigation_and_connections(self):
        from InvestingOS.web_viewer import render_node
        from InvestingOS.core import add_edge
        project = create_project('History')
        first = add_node(project, 'Rome')
        second = add_node(project, 'Empire')
        add_edge(project, first['id'], second['id'], 'contains')
        html = render_node(project, first['id'])
        self.assertIn('Empire', html)
        self.assertIn('/node/' + second['id'], html)
        self.assertIn('Back', html)
        with self.assertRaises(KeyError):
            render_node(project, 'missing')

    def test_hierarchical_view_displays_nested_topics(self):
        from InvestingOS.web_viewer import render_view
        from InvestingOS.core import add_edge, add_view
        project = create_project('History')
        parent = add_node(project, 'Ancient history')
        child = add_node(project, 'Rome')
        view = add_view(project, 'Chronological')
        add_edge(project, parent['id'], child['id'], 'contains', view['id'])
        html = render_view(project, view['id'])
        self.assertIn('class="tree"', html)
        self.assertIn('/node/' + parent['id'], html)
        self.assertIn('/node/' + child['id'], html)
        self.assertLess(html.index('Ancient history'), html.index('Rome'))

    def test_node_detail_links_claim_sources(self):
        from InvestingOS.web_viewer import render_node
        project = create_project('History')
        node = add_node(project, 'Rome')
        source = add_source(project, 'Historical archive')
        add_claim(project, 'Claim text', nodes=[node['id']], sources=[source['id']])
        html = render_node(project, node['id'])
        self.assertIn('/source/' + source['id'], html)
        self.assertIn('Historical archive', html)
        self.assertIn('unverified', html)

    def test_import_form_has_explicit_modes_and_token(self):
        from InvestingOS.web_viewer import render_import
        html = render_import(create_project('History'), 'test-token')
        self.assertIn('name="token" value="test-token"', html)
        self.assertIn('name="source"', html)
        self.assertIn('name="storage_root"', html)
        self.assertIn('name="category"', html)
        self.assertIn('value="local"', html)
        self.assertIn('value="web"', html)
        self.assertIn('value="youtube"', html)

    def test_import_post_rejects_foreign_origin(self):
        from unittest.mock import patch, Mock
        from types import SimpleNamespace
        from InvestingOS.web_viewer import create_server
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'project.json'
            save(create_project('History'), path)
            with patch('InvestingOS.web_viewer.ThreadingHTTPServer', side_effect=lambda addr, handler: handler):
                handler_type = create_server(path, 8000)
            handler = object.__new__(handler_type)
            handler.path = '/import'
            handler.server = SimpleNamespace(server_port=8000)
            handler.headers = {'Host': '127.0.0.1:8000', 'Origin': 'https://attacker.example', 'Content-Type': 'application/x-www-form-urlencoded'}
            handler.send_error = Mock()
            handler.do_POST()
            handler.send_error.assert_called_once_with(403)

    def test_local_import_post_registers_source(self):
        import io
        from urllib.parse import urlencode
        from unittest.mock import patch, Mock
        from types import SimpleNamespace
        from InvestingOS.web_viewer import create_server
        from InvestingOS.storage import load
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, source, destination = root / 'project.json', root / 'doc.csv', root / 'doc.md'
            save(create_project('History'), project)
            source.write_text('Topic,Year\nRome,1\n', encoding='utf-8')
            with patch('InvestingOS.web_viewer.secrets.token_urlsafe', return_value='safe-token'), patch('InvestingOS.web_viewer.ThreadingHTTPServer', side_effect=lambda addr, handler: handler):
                handler_type = create_server(project, 8000)
            body = urlencode({'token': 'safe-token', 'mode': 'local', 'source': str(source), 'destination': str(destination)}).encode()
            handler = object.__new__(handler_type)
            handler.path = '/import'
            handler.server = SimpleNamespace(server_port=8000)
            handler.headers = {'Host': '127.0.0.1:8000', 'Origin': 'http://127.0.0.1:8000', 'Content-Type': 'application/x-www-form-urlencoded', 'Content-Length': str(len(body))}
            handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
            handler.send_response, handler.send_header, handler.end_headers = Mock(), Mock(), Mock()
            handler.do_POST()
            self.assertIn('| Rome | 1 |', destination.read_text())
            self.assertEqual(len(load(project)['sources']), 1)

    def test_organized_import_creates_and_records_destination(self):
        import io
        from urllib.parse import urlencode
        from unittest.mock import patch, Mock
        from types import SimpleNamespace
        from InvestingOS.web_viewer import create_server
        from InvestingOS.storage import load
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_file, source = root / 'project.json', root / 'file.csv'
            project = create_project('Example')
            save(project, project_file)
            source.write_text('A,B\nx,y\n', encoding='utf-8')
            with patch('InvestingOS.web_viewer.secrets.token_urlsafe', return_value='safe-token'), patch('InvestingOS.web_viewer.ThreadingHTTPServer', side_effect=lambda addr, handler: handler):
                handler_type = create_server(project_file, 8000)
            body = urlencode({'token': 'safe-token', 'mode': 'local', 'source': str(source), 'category': 'topic/subtopic'}).encode()
            handler = object.__new__(handler_type)
            handler.path = '/import'
            handler.server = SimpleNamespace(server_port=8000)
            handler.headers = {'Host': '127.0.0.1:8000', 'Origin': 'http://127.0.0.1:8000', 'Content-Type': 'application/x-www-form-urlencoded', 'Content-Length': str(len(body))}
            handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
            handler.send_response, handler.send_header, handler.end_headers = Mock(), Mock(), Mock()
            handler.do_POST()
            record = load(project_file)['sources'][0]
            output = Path(record['extracted_path'])
            self.assertIn('/temporary/documents/topic/subtopic/', output.as_posix())
            self.assertIn('| x | y |', output.read_text())
            self.assertTrue(source.exists())
