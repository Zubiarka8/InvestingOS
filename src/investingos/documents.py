"""Extract text from local files without changing originals."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1
        elif tag in {'p', 'br', 'div', 'h1', 'h2', 'h3', 'li'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _write_new(path, content):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(content)


def extract_text(source, destination, *, ocr=False, language='eng'):
    source = Path(source)
    if Path(destination).exists():
        raise FileExistsError(destination)
    if ocr:
        if source.suffix.lower() == '.pdf':
            with tempfile.TemporaryDirectory() as tmp:
                prefix = str(Path(tmp) / 'page')
                subprocess.run(['pdftoppm', '-png', str(source), prefix], check=True, capture_output=True)
                pages = sorted(Path(tmp).glob('page-*.png'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
                if not pages:
                    raise ValueError('PDF rendering produced no pages')
                chunks = []
                for i, page in enumerate(pages, 1):
                    result = subprocess.run(['tesseract', str(page), 'stdout', '-l', language], check=True, capture_output=True, text=True)
                    chunks.append(f'--- Page {i} ---\n{result.stdout}')
                text = '\n'.join(chunks)
        elif source.suffix.lower() in {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}:
            result = subprocess.run(['tesseract', str(source), 'stdout', '-l', language], check=True, capture_output=True, text=True)
            text = result.stdout
        else:
            raise ValueError('OCR accepts PDF and image files')
    elif source.suffix.lower() == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError('PDF extraction requires pypdf; see docs/research-tools.md') from exc
        text = '\n\n'.join(f'--- Page {i} ---\n{page.extract_text() or ""}' for i, page in enumerate(PdfReader(str(source)).pages, 1))
    elif source.suffix.lower() in {'.html', '.htm'}:
        parser = TextHTML()
        parser.feed(source.read_text(encoding='utf-8'))
        text = ''.join(parser.parts)
    elif source.suffix.lower() in {'.txt', '.md'}:
        text = source.read_text(encoding='utf-8')
    else:
        raise ValueError('supported inputs: PDF, HTML, text, Markdown, or images with OCR')
    _write_new(destination, text)


def transcribe(source, destination, *, model_path):
    source, model_path = Path(source), Path(model_path)
    if not source.is_file() or not model_path.is_dir():
        raise ValueError('audio file and local model directory must exist')
    if Path(destination).exists():
        raise FileExistsError(destination)
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ValueError('transcription requires faster-whisper; see docs/research-tools.md') from exc
    model = WhisperModel(str(model_path), device='cpu', compute_type='int8', local_files_only=True)
    segments, _ = model.transcribe(str(source))
    lines = ['Machine-generated transcript; verify against the original.', '']
    lines.extend(f'[{segment.start:.2f}–{segment.end:.2f}] {segment.text.strip()}' for segment in segments)
    _write_new(destination, '\n'.join(lines) + '\n')
