import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ImportScriptTests(unittest.TestCase):
    def test_csv_script_registers_source_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, source, dest = root / 'project.json', root / 'table.csv', root / 'table.md'
            subprocess.run([sys.executable, str(ROOT / 'scripts/InvestingOS.py'), 'create', str(project), 'Topic'], check=True, capture_output=True)
            source.write_text('Name,Value\nA,1\n', encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/import_csv.py'), str(project), str(source), str(dest)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('| A | 1 |', dest.read_text(encoding='utf-8'))
            self.assertEqual(len(json.loads(project.read_text(encoding='utf-8'))['sources']), 1)
            self.assertEqual(source.read_text(encoding='utf-8'), 'Name,Value\nA,1\n')

    def test_pdf_script_rejects_wrong_input_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'wrong.csv'
            source.write_text('x', encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/import_pdf.py'), str(root / 'project.json'), str(source), str(root / 'out.md')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('.pdf', result.stderr)
            self.assertFalse((root / 'out.md').exists())

    def test_all_scripts_offer_help_without_optional_dependencies(self):
        for name in ('html', 'pdf', 'docx', 'xlsx', 'csv', 'text', 'youtube', 'web'):
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, str(ROOT / f'scripts/import_{name}.py'), '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_search_and_transcription_scripts_offer_help(self):
        for name in ('search_youtube', 'transcribe_audio'):
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, str(ROOT / f'scripts/{name}.py'), '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_archive_reports_error_without_traceback(self):
        import io
        import zipfile
        from contextlib import redirect_stderr
        from unittest.mock import patch
        sys.path.insert(0, str(ROOT / 'src'))
        from investingos.cli import main
        from investingos.core import create_project
        from investingos.storage import save
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, source, dest = root / 'project.json', root / 'bad.xlsx', root / 'out.md'
            save(create_project('Topic'), project)
            source.write_bytes(b'not an archive')
            stderr = io.StringIO()
            with patch('sys.argv', ['InvestingOS', 'import-markdown', str(project), str(source), str(dest)]), \
                 patch('investingos.markdown_import.convert', side_effect=zipfile.BadZipFile('invalid archive')), \
                 redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as error:
                    main()
            self.assertEqual(error.exception.code, 1)
            self.assertIn('invalid archive', stderr.getvalue())
            self.assertFalse(dest.exists())
