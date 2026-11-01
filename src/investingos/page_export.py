"""Create an editable Word document from the visible page content."""
from html.parser import HTMLParser
import io
import re
from xml.sax.saxutils import escape
import zipfile


class PageBlocks(HTMLParser):
    """Collect textual content from the main region, excluding controls."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.skip = 0
        self.capture = None
        self.depth = 0
        self.buffer = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.in_main = True
            return
        if not self.in_main:
            return
        if self.skip:
            if tag not in {'input', 'br', 'img', 'meta', 'link'}:
                self.skip += 1
            return
        if tag in {'form', 'script', 'style'} or 'back' in attrs.get('class', '').split():
            self.skip = 1
            return
        if self.capture:
            if tag not in {'input', 'br', 'img', 'meta', 'link'}:
                self.depth += 1
            return
        if tag in {'h1', 'h2', 'h3', 'p', 'li'} or (tag == 'div' and any(c in attrs.get('class', '').split() for c in ('row', 'metric'))):
            self.capture = tag
            self.depth = 0
            self.buffer = []

    def handle_endtag(self, tag):
        if not self.in_main:
            return
        if self.skip:
            self.skip -= 1
            return
        if self.capture:
            if self.depth:
                self.depth -= 1
            elif tag == self.capture:
                text = ' '.join(' '.join(self.buffer).split())
                if text:
                    self.blocks.append((self.capture, text))
                self.capture = None
            return
        if tag == 'main':
            self.in_main = False

    def handle_data(self, data):
        if self.in_main and not self.skip and self.capture:
            self.buffer.append(data)


def _xml_text(value):
    return escape(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]', '', value))


def page_blocks(html):
    parser = PageBlocks()
    parser.feed(html)
    return parser.blocks


def word_document(html):
    paragraphs = ['<w:p><w:pPr><w:pStyle w:val="Brand"/></w:pPr><w:r><w:t>INVESTING / OS</w:t></w:r></w:p>']
    for tag, value in page_blocks(html):
        style = {'h1': 'Title', 'h2': 'Heading1', 'h3': 'Heading2'}.get(tag, 'Normal')
        paragraphs.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{_xml_text(value)}</w:t></w:r></w:p>')
    document = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>''' + ''.join(paragraphs) + '''<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1200" w:right="1200" w:bottom="1200" w:left="1200"/></w:sectPr></w:body></w:document>'''
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="140"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:color w:val="20352D"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Brand"><w:name w:val="Brand"/><w:pPr><w:spacing w:after="480"/></w:pPr><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="30644E"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="120" w:after="260"/></w:pPr><w:rPr><w:rFonts w:ascii="Georgia" w:hAnsi="Georgia"/><w:sz w:val="48"/><w:color w:val="20352D"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="180"/></w:pPr><w:rPr><w:rFonts w:ascii="Georgia" w:hAnsi="Georgia"/><w:sz w:val="32"/><w:color w:val="30644E"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="220" w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="25"/></w:rPr></w:style></w:styles>'''
    types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in (('[Content_Types].xml', types), ('_rels/.rels', root_rels), ('word/document.xml', document), ('word/styles.xml', styles), ('word/_rels/document.xml.rels', doc_rels)):
            archive.writestr(name, content.encode('utf-8'))
    return output.getvalue()
