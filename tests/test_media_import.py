import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class MediaImportTests(unittest.TestCase):
    def test_text_import_preserves_original_and_refuses_overwrite(self):
        from investingos.documents import extract_text
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'original.txt'
            destination = Path(tmp) / 'extracted.txt'
            original.write_text('Source text', encoding='utf-8')
            extract_text(original, destination)
            self.assertEqual(destination.read_text(encoding='utf-8'), 'Source text')
            self.assertEqual(original.read_text(encoding='utf-8'), 'Source text')
            with self.assertRaises(FileExistsError):
                extract_text(original, destination)

    def test_pdf_extraction_marks_pages(self):
        from investingos.documents import extract_text
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'doc.pdf', Path(tmp) / 'out.txt'
            source.write_bytes(b'%PDF')
            pages = [SimpleNamespace(extract_text=lambda: 'First'), SimpleNamespace(extract_text=lambda: 'Second')]
            with patch.dict(sys.modules, {'pypdf': SimpleNamespace(PdfReader=lambda path: SimpleNamespace(pages=pages))}):
                extract_text(source, output)
            self.assertIn('Page 2', output.read_text(encoding='utf-8'))
            self.assertIn('Second', output.read_text(encoding='utf-8'))

    def test_transcription_creates_new_file_with_timestamps(self):
        from investingos.documents import transcribe
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'audio.wav', Path(tmp) / 'out.txt'
            source.write_bytes(b'audio')
            model_dir = Path(tmp) / 'model'
            model_dir.mkdir()
            model = SimpleNamespace(transcribe=lambda path: ([SimpleNamespace(start=0.0, end=1.2, text=' Hello')], None))
            with patch.dict(sys.modules, {'faster_whisper': SimpleNamespace(WhisperModel=lambda *a, **k: model)}):
                transcribe(source, output, model_path=str(model_dir))
            self.assertIn('Hello', output.read_text(encoding='utf-8'))
            self.assertIn('1.20', output.read_text(encoding='utf-8'))

class MediaCLITests(unittest.TestCase):
    def test_extract_command(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            source, dest = Path(tmp) / 'in.txt', Path(tmp) / 'out.txt'
            source.write_text('Hello', encoding='utf-8')
            runner = Path(__file__).resolve().parents[1] / 'scripts/investingos.py'
            result = subprocess.run([sys.executable, str(runner), 'extract', str(source), str(dest)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(dest.read_text(encoding='utf-8'), 'Hello')

class PDFOCRTests(unittest.TestCase):
    def test_scanned_pdf_runs_ocr_page_by_page(self):
        from types import SimpleNamespace
        from investingos.documents import extract_text
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'scan.pdf', Path(tmp) / 'ocr.txt'
            source.write_bytes(b'%PDF')
            def run(command, **kwargs):
                if command[0] == 'pdftoppm':
                    Path(command[-1] + '-1.png').write_bytes(b'page')
                    return SimpleNamespace(stdout='')
                return SimpleNamespace(stdout='Recognized text')
            with patch('investingos.documents.subprocess.run', side_effect=run):
                extract_text(source, output, ocr=True)
            self.assertIn('Recognized text', output.read_text(encoding='utf-8'))
