"""Convert local source documents to Markdown and record provenance."""
import csv
from html import escape
from pathlib import Path

from .core import add_source
from .documents import TextHTML
from .knowledge_tools import _hash
from .source_links import imported_source_section


def _cell(value):
    return escape(str(value if value is not None else '')).replace('|', r'\|').replace('\n', ' ')


def _table(rows):
    rows = list(rows)
    if not rows:
        return '_Empty sheet._\n'
    width = max(len(row) for row in rows)
    if width == 0:
        return '_Empty sheet._\n'
    def line(row):
        return '| ' + ' | '.join(_cell(row[i] if i < len(row) else '') for i in range(width)) + ' |'
    return '\n'.join([line(rows[0]), '| ' + ' | '.join(['---'] * width) + ' |'] + [line(row) for row in rows[1:]]) + '\n'


def convert(source):
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix == '.md':
        return source.read_text(encoding='utf-8')
    if suffix == '.csv':
        with source.open(encoding='utf-8-sig', newline='') as handle:
            return _table(csv.reader(handle))
    if suffix == '.xlsx':
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ValueError('XLSX import requires openpyxl; see docs/research-tools.md') from exc
        workbook = load_workbook(source, read_only=True, data_only=True)
        try:
            return '\n'.join('## ' + escape(sheet.title) + '\n\n' + _table(sheet.iter_rows(values_only=True)) for sheet in workbook.worksheets)
        finally:
            workbook.close()
    if suffix == '.docx':
        try:
            from docx import Document
        except ImportError as exc:
            raise ValueError('DOCX import requires python-docx; see docs/research-tools.md') from exc
        paragraphs = []
        for paragraph in Document(source).paragraphs:
            name = paragraph.style.name if paragraph.style else ''
            level = int(name[-1]) if name in ('Heading 1', 'Heading 2', 'Heading 3') else 0
            paragraphs.append(('#' * level + ' ' if level else '') + escape(paragraph.text))
        return '\n\n'.join(paragraphs) + '\n'
    if suffix == '.pdf':
        try:
            from pypdf import PdfReader
            from pypdf.errors import PyPdfError
        except ImportError as exc:
            raise ValueError('PDF import requires pypdf; see docs/research-tools.md') from exc
        try:
            return '\n\n'.join(f'## Page {i}\n\n{escape(page.extract_text() or "")}' for i, page in enumerate(PdfReader(str(source)).pages, 1)) + '\n'
        except (PyPdfError, EOFError) as exc:
            raise ValueError(f'Unable to read PDF: {exc}') from exc
    if suffix in ('.html', '.htm'):
        parser = TextHTML()
        parser.feed(source.read_text(encoding='utf-8'))
        return escape(''.join(parser.parts))
    if suffix == '.txt':
        return escape(source.read_text(encoding='utf-8'))
    raise ValueError('supported types: .md, .txt, .html, .pdf, .docx, .csv, .xlsx')


def import_to_markdown(project, original, destination):
    original, destination = Path(original).resolve(), Path(destination).resolve()
    if destination.suffix.lower() != '.md':
        raise ValueError('destination must be a Markdown file')
    before = _hash(original)
    content = convert(original)
    if _hash(original) != before:
        raise ValueError('original changed during import')
    with destination.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(content)
        handle.write(imported_source_section(source=original, destination=destination, project=project))
    source = add_source(project, original.name, media_type=original.suffix.lower().lstrip('.'))
    source.update(local_path=str(original), extracted_path=str(destination), sha256=before)
    return source
