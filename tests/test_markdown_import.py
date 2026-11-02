import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.core import create_project

class MarkdownImportTests(unittest.TestCase):
    def test_csv_to_markdown_registers_source(self):
        from InvestingOS.markdown_import import import_to_markdown
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'data.csv', root / 'data.md'
            source.write_text('Name,Value\nAlpha,42\n', encoding='utf-8')
            project = create_project('Project')
            record = import_to_markdown(project, source, target)
            result = target.read_text(encoding='utf-8')
            self.assertIn('| Name | Value |', result)
            self.assertIn('| Alpha | 42 |', result)
            self.assertEqual(source.read_text(encoding='utf-8'), 'Name,Value\nAlpha,42\n')
            self.assertEqual(project['sources'][0]['id'], record['id'])
            with self.assertRaises(FileExistsError):
                import_to_markdown(project, source, target)

    def test_xlsx_sheet_data_to_markdown(self):
        from InvestingOS.markdown_import import import_to_markdown
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / 'data.xlsx', root / 'data.md'
            source.write_bytes(b'placeholder')
            sheet = SimpleNamespace(title='Sheet one', iter_rows=lambda **kw: iter([('Item', 'Value'), ('A', 10)]))
            workbook = SimpleNamespace(worksheets=[sheet], close=lambda: None)
            with patch.dict(sys.modules, {'openpyxl': SimpleNamespace(load_workbook=lambda *a, **kw: workbook)}):
                import_to_markdown(create_project('Project'), source, target)
            self.assertIn('## Sheet one', target.read_text(encoding='utf-8'))
            self.assertIn('| A | 10 |', target.read_text(encoding='utf-8'))

    def test_cli_markdown_import(self):
        import subprocess, json
        runner = Path(__file__).resolve().parents[1] / 'scripts/InvestingOS.py'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, source, dest = root / 'project.json', root / 'input.csv', root / 'out.md'
            source.write_text('A,B\n1,2\n', encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable, str(runner), *map(str, args)], check=True, text=True, capture_output=True)
            run('create', project, 'Topic')
            run('import-markdown', project, source, dest)
            self.assertEqual(len(json.loads(project.read_text())['sources']), 1)
            self.assertIn('| 1 | 2 |', dest.read_text())

class YouTubeImportTests(unittest.TestCase):
    def test_imports_available_captions_and_records_url(self):
        from InvestingOS.youtube_import import import_youtube
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'video.md'
            project = create_project('Project')
            def run(command, **kwargs):
                folder = Path(command[command.index('-P') + 1])
                (folder / 'captions.en.vtt').write_text('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n', encoding='utf-8')
                return SimpleNamespace(returncode=0)
            with patch('InvestingOS.youtube_import.shutil.which', return_value='yt-dlp'), patch('InvestingOS.youtube_import.subprocess.run', side_effect=run):
                source = import_youtube(project, 'https://youtu.be/example', target)
            self.assertIn('Hello', target.read_text())
            self.assertEqual(source['url'], 'https://youtu.be/example')
            self.assertTrue(Path(source['local_path']).is_file())

    def test_no_captions_fails_without_creating_output(self):
        from InvestingOS.youtube_import import import_youtube
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'video.md'
            with patch('InvestingOS.youtube_import.shutil.which', return_value='yt-dlp'), patch('InvestingOS.youtube_import.subprocess.run'):
                with self.assertRaises(ValueError):
                    import_youtube(create_project('Project'), 'https://youtu.be/example', target)
            self.assertFalse(target.exists())

class WebImportTests(unittest.TestCase):
    def test_web_import_saves_original_and_markdown(self):
        import io
        from InvestingOS.web_import import import_web
        class Response(io.BytesIO):
            headers = {'Content-Type': 'text/html; charset=utf-8'}
        class Opener:
            def open(self, *args, **kwargs):
                return Response(b'<html><body><h1>Example</h1><p>Text</p></body></html>')
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'page.md'
            project = create_project('Project')
            addresses = [(2, 1, 6, '', ('93.184.216.34', 443))]
            with patch('InvestingOS.web_import.socket.getaddrinfo', return_value=addresses), patch('InvestingOS.web_import._fetch_pinned', return_value=b'<html><body><h1>Example</h1><p>Text</p></body></html>'):
                source = import_web(project, 'https://example.com/page', destination)
            self.assertIn('Example', destination.read_text())
            self.assertTrue(Path(source['local_path']).is_file())
            self.assertEqual(source['url'], 'https://example.com/page')

    def test_private_network_is_rejected(self):
        from InvestingOS.web_import import import_web
        with tempfile.TemporaryDirectory() as tmp:
            addresses = [(2, 1, 6, '', ('127.0.0.1', 443))]
            with patch('InvestingOS.web_import.socket.getaddrinfo', return_value=addresses):
                with self.assertRaises(ValueError):
                    import_web(create_project('Project'), 'https://example.com/', Path(tmp) / 'page.md')

    def test_search_youtube_returns_real_video_identifiers(self):
        from InvestingOS.youtube_import import search_youtube
        result = SimpleNamespace(stdout='{"id":"abcdefghijk","title":"Example"}\n')
        with patch('InvestingOS.youtube_import.shutil.which', return_value='yt-dlp'), patch('InvestingOS.youtube_import.subprocess.run', return_value=result):
            videos = search_youtube('history')
        self.assertEqual(videos[0]['url'], 'https://www.youtube.com/watch?v=abcdefghijk')
