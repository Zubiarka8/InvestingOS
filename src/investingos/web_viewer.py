"""Local interface for browsing and importing into one knowledge project."""
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import base64
import hashlib
import http.client
import zipfile
import secrets
import subprocess
from urllib.parse import parse_qs, urlencode, urlsplit

from .storage import load, save


def _text(value):
    return escape(str(value), quote=True)


def _link(path, label):
    return f'<a href="{_text(path)}">{_text(label)}</a>'


PRINT_SCRIPT = "document.getElementById('export-pdf').addEventListener('click', function () { window.print(); });"
PRINT_HASH = base64.b64encode(hashlib.sha256(PRINT_SCRIPT.encode('utf-8')).digest()).decode('ascii')


def _layout(project, content, section='overview', query='', export_target=None):
    nav = [('overview', 'Overview'), ('topics', 'Topics'), ('views', 'Indexes'),
           ('superindex', 'Superindex'), ('sources', 'Sources'), ('claims', 'Claims & evidence'),
           ('learning', 'Learning'), ('research', 'Research'), ('import', 'Import')]
    menu = ''.join('<a class="nav-item {}" href="{}"{}><span class="nav-dot"></span>{}</a>'.format(
        'active' if section == key else '', '/import' if key == 'import' else '/?section=' + key, ' aria-current="page"' if section == key else '', label)
        for key, label in nav)
    if section == 'import':
        toolbar, script = '', ''
    else:
        target = export_target or ('/?' + urlencode({'section': section, 'q': query}))
        word_preview = '/preview/word?' + urlencode({'from': target})
        pdf_preview = '/preview/pdf?' + urlencode({'from': target})
        toolbar = f'<div class="export-tools"><span>Export this page</span><a class="export-link" href="{_text(word_preview)}">Export Word</a><a class="export-pdf" href="{_text(pdf_preview)}">Export PDF</a></div>'
        script = ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_text(project['title'])} · InvestingOS</title><style>
:root{{--bg:#f5f6f1;--surface:#fff;--ink:#20352d;--muted:#5f7267;--line:#dbe4da;--accent:#30644e;--soft:#e6efe5}}*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}a:focus-visible,button:focus-visible,input:focus-visible{{outline:3px solid #719c81;outline-offset:3px}}.shell{{display:grid;grid-template-columns:240px minmax(0,1fr);min-height:100vh}}.sidebar{{background:#fff;border-right:1px solid var(--line);padding:26px 18px;display:flex;flex-direction:column;gap:30px}}.brand{{font-weight:800;font-size:20px;letter-spacing:-.045em;color:var(--ink)}}.brand b{{color:#79a784}}.workspace{{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin:0 10px 10px}}.nav-item{{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:8px;color:#53685c;font-weight:550;min-height:44px}}.nav-item.active{{background:var(--soft);color:#224f3b}}.nav-dot{{width:7px;height:7px;border-radius:50%;background:#aebeb0}}.active .nav-dot{{background:#3e7d59}}.sidebar-note{{margin-top:auto;color:var(--muted);font-size:12px;padding:10px}}.main{{min-width:0}}.export-tools{{display:flex;align-items:center;justify-content:flex-end;gap:10px;margin-bottom:28px;flex-wrap:wrap}}.export-tools span{{font-size:12px;color:var(--muted);margin-right:4px}}.export-link,.export-pdf{{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 14px;border:1px solid var(--line);border-radius:8px;font:600 13px system-ui;cursor:pointer}}.export-link{{color:var(--ink);background:#fff}}.export-pdf{{color:#fff;background:var(--accent);border-color:var(--accent)}}.topbar{{background:#fff;border-bottom:1px solid var(--line);padding:18px 36px;display:flex;justify-content:space-between;align-items:center;gap:20px}}.topbar strong{{overflow-wrap:anywhere}}.status{{font-size:12px;color:var(--muted)}}.status:before{{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#70a57b;margin-right:7px}}main{{max-width:1300px;margin:auto;padding:40px 40px 80px}}.crumb{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:700}}h1{{font:500 clamp(36px,4vw,56px)/1.08 Georgia,serif;letter-spacing:-.045em;margin:14px 0 12px}}h2{{font:500 27px/1.2 Georgia,serif;letter-spacing:-.03em;margin:0}}h3{{font-size:17px;margin:0 0 7px;letter-spacing:-.02em}}p{{margin:0;color:var(--muted)}}.subtitle{{max-width:680px;font-size:16px}}.search{{display:flex;gap:10px;margin:28px 0 34px;max-width:760px}}.search label{{position:absolute;left:-10000px}}.field{{display:block;margin:18px 0}}.field label{{display:block;font-weight:600;margin-bottom:6px}}.field input,.field select{{width:100%;min-height:46px;border:1px solid #cbd9cb;border-radius:9px;padding:10px 12px;background:#fff;font:inherit}}.search input{{width:100%;height:48px;border:1px solid #cbd9cb;border-radius:9px;padding:0 15px;background:#fff;font:inherit;color:var(--ink)}}button{{border:0;border-radius:9px;background:#315e48;color:white;padding:0 20px;font:600 14px system-ui;cursor:pointer;min-height:48px}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:38px}}.metric,.card,.panel{{background:var(--surface);border:1px solid var(--line);border-radius:11px}}.metric{{padding:17px 19px}}.metric strong{{font-size:25px;display:block;line-height:1.15;letter-spacing:-.05em}}.metric span{{font-size:12px;color:var(--muted)}}.heading{{display:flex;justify-content:space-between;align-items:baseline;gap:15px;margin:0 0 18px}}.hint{{font-size:12px;color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,245px),1fr));gap:13px}}.card{{padding:21px;min-width:0;overflow-wrap:anywhere}}.label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:14px}}.card p{{font-size:14px}}.card-foot{{margin-top:20px;padding-top:14px;border-top:1px solid #edf1ec;color:var(--muted);font-size:12px}}.panel{{padding:5px 20px;margin-bottom:22px}}.row{{display:flex;justify-content:space-between;gap:20px;padding:15px 0;border-bottom:1px solid #edf1ec;overflow-wrap:anywhere}}.row:last-child{{border:0}}.row small{{color:var(--muted)}}.empty{{padding:24px 0;color:var(--muted)}}.badge{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#315d48;background:#eaf2e9;border-radius:20px;padding:5px 9px;height:max-content}}.back{{display:inline-block;margin-bottom:25px;font-weight:600}}.detail-section{{margin-top:34px}}.detail-section h2{{margin-bottom:15px}}.details p{{white-space:pre-wrap}}.tree,.tree ul{{list-style:none;margin:0;padding-left:20px}}.tree{{padding:10px 0}}.tree li{{border-left:1px solid var(--line);padding:8px 0 0 16px}}.tree li:last-child{{padding-bottom:8px}}.note{{border-left:3px solid #83ad8c;background:#edf4ea;padding:13px 16px;margin:20px 0;color:#435d4a;font-size:13px}}@page{{size:A4;margin:15mm}}@media print{{:root{{--bg:#fff}}body{{background:#fff;font-size:11pt;print-color-adjust:exact;-webkit-print-color-adjust:exact}}.shell{{display:block;min-height:0}}.sidebar,.topbar,.export-tools,.search,.back{{display:none!important}}main{{max-width:none;padding:0;margin:0}}h1{{font-size:32pt}}h2{{font-size:20pt}}.card,.metric,.panel{{break-inside:avoid}}a{{color:inherit;text-decoration:none}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:800px){{.shell{{display:block}}.sidebar{{padding:15px 18px;gap:14px;border-right:0;border-bottom:1px solid var(--line)}}.sidebar-note,.workspace{{display:none}}nav{{display:flex;overflow:auto;gap:4px}}.nav-item{{white-space:nowrap}}.topbar{{padding:14px 20px}}main{{padding:30px 20px 60px}}.metrics{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:420px){{.search{{flex-wrap:wrap}}.search button{{width:100%}}}}
</style></head><body><div class="shell"><aside class="sidebar"><div class="brand">investing <b>/</b> os</div><div><div class="workspace">Workspace</div><nav aria-label="Project sections">{menu}</nav></div><div class="sidebar-note">Local workspace<br>Local project</div></aside><div class="main"><header class="topbar"><strong>{_text(project['title'])}</strong><span class="status">Local project</span></header><main>{toolbar}{content}</main></div></div>{script}</body></html>'''


def _matches(item, query):
    return not query or query.casefold() in ' '.join(str(value) for value in item.values()).casefold()


def _row(title, meta='', href=None):
    label = _link(href, title) if href else _text(title)
    return f'<div class="row"><strong>{label}</strong><small>{_text(meta)}</small></div>'


def render(project, query='', section='overview'):
    valid = {'overview', 'topics', 'views', 'superindex', 'sources', 'claims', 'learning', 'research'}
    if section not in valid:
        raise ValueError('unknown section')
    query = query.strip()
    nodes = {item['id']: item for item in project['nodes']}
    sources = {item['id']: item for item in project.get('sources', [])}
    nav_label = {'overview': 'Overview', 'topics': 'Topics', 'views': 'Indexes', 'superindex': 'Superindex', 'sources': 'Sources', 'claims': 'Claims & evidence', 'learning': 'Learning', 'research': 'Research'}[section]
    search = f'''<form class="search" method="get" action="/"><input type="hidden" name="section" value="{section}"><label for="search">Search this project</label><input id="search" name="q" value="{_text(query)}" placeholder="Search topics, sources, claims…"><button type="submit">Search</button></form>'''
    intro = f'<div class="crumb">Knowledge workspace / {_text(nav_label)}</div><h1>{_text(project["title"] if section == "overview" else nav_label)}</h1><p class="subtitle">{_text(project["description"]) if section == "overview" and project["description"] else "Explore the knowledge, sources, and connections in this project."}</p>{search}'
    stats = [('Topics', len(nodes)), ('Connections', len(project['edges'])), ('Sources', len(sources)), ('Claims', len(project.get('claims', [])))]
    metrics = '<div class="metrics">' + ''.join(f'<div class="metric"><strong>{count:02}</strong><span>{name}</span></div>' for name, count in stats) + '</div>'
    def collection(title, rows):
        body = ''.join(rows) if rows else '<p class="empty">No matching items.</p>'
        return f'<section class="detail-section"><div class="heading"><h2>{title}</h2><span class="hint">{len(rows)} items</span></div><div class="panel">{body}</div></section>'
    cards = []
    for node in nodes.values():
        if not _matches(node, query):
            continue
        links = sum(1 for edge in project['edges'] if node['id'] in (edge['source'], edge['target']))
        cards.append(f'<article class="card"><div class="label">Knowledge node</div><h3>{_link("/node/" + node["id"], node["title"])}</h3><p>{_text(node["description"]) or "No description yet."}</p><div class="card-foot">{links} connections · {_text(node["id"][:8])}</div></article>')
    content = ''
    if section in ('overview', 'topics'):
        content += (metrics if section == 'overview' else '')
        card_content = ''.join(cards) if cards else '<p class="empty">No matching topics.</p>'
        content += f'<div class="heading"><h2>Knowledge map</h2><span class="hint">{len(cards)} matching topics</span></div><div class="grid">{card_content}</div>'
    if section in ('overview', 'views'):
        rows = [_row(v['title'], v['kind'], '/view/' + v['id']) for v in project['views'] if _matches(v, query)]
        content += collection('Indexes and views', rows)
    if section == 'superindex':
        from .superindex import outline
        for view_number, view in enumerate(project['views'], 1):
            rows = []
            for number, node in outline(project, view['id']):
                if _matches(node, query):
                    label = '.'.join(str(part) for part in (view_number,) + number)
                    rows.append(_row(label + ' ' + node['title'], '', '/node/' + node['id']))
            content += collection(str(view_number) + '. ' + _text(view['title']), rows)
        if not project['views']:
            content += '<p class="empty">Create a view and add hierarchical relationships to build an index.</p>'
    if section in ('overview', 'sources'):
        rows = [_row(s['title'], s.get('author', ''), '/source/' + s['id']) for s in sources.values() if _matches(s, query)]
        content += collection('Sources', rows)
    if section in ('overview', 'claims'):
        rows = [_row(c['text'], c['status']) for c in project.get('claims', []) if _matches(c, query)]
        content += collection('Claims', rows)
        rows = [_row(sources[e['source']]['title'], e['locator'] + ' · ' + e['note']) for e in project.get('evidence', []) if _matches(e, query)]
        content += collection('Evidence', rows)
    if section in ('overview', 'learning'):
        rows = [_row(c['title'], c['level']) for c in project.get('competencies', []) if _matches(c, query)]
        content += collection('Competencies', rows)
        rows = [_row(p['title'], f"{len(p['competencies'])} competencies") for p in project.get('learning_paths', []) if _matches(p, query)]
        content += collection('Learning paths', rows)
    if section in ('overview', 'research'):
        rows = [_row(t['question'], t['status']) for t in project.get('research_tasks', []) if _matches(t, query)]
        content += collection('Research tasks', rows)
    return _layout(project, intro + content, section, query)


def render_node(project, node_id):
    nodes = {item['id']: item for item in project['nodes']}
    node = nodes[node_id]
    relations = []
    for edge in project['edges']:
        if edge['source'] == node_id:
            relations.append(_row(nodes[edge['target']]['title'], edge['type'], '/node/' + edge['target']))
        elif edge['target'] == node_id:
            relations.append(_row(nodes[edge['source']]['title'], 'incoming · ' + edge['type'], '/node/' + edge['source']))
    sources = {item['id']: item for item in project.get('sources', [])}
    claims = []
    for claim in project.get('claims', []):
        if node_id in claim.get('nodes', []):
            citations = ', '.join(_link('/source/' + source_id, sources[source_id]['title']) for source_id in claim['sources'])
            claims.append(_row(claim['text'], claim['status']) + (f'<p class="hint">Sources: {citations}</p>' if citations else ''))
    content = f'''<a class="back" href="/?section=topics">← Back to topics</a><div class="crumb">Topic / {_text(node_id[:8])}</div><h1>{_text(node['title'])}</h1><p class="subtitle">{_text(node['description']) or 'No description yet.'}</p>
<section class="detail-section"><h2>Connections</h2><div class="panel">{''.join(relations) or '<p class="empty">No connections yet.</p>'}</div></section><section class="detail-section"><h2>Claims</h2><div class="panel">{''.join(claims) or '<p class="empty">No claims linked to this topic.</p>'}</div></section>'''
    return _layout(project, content, 'topics', export_target='/node/' + node_id)


def render_view(project, view_id):
    view = next(item for item in project['views'] if item['id'] == view_id)
    nodes = {item['id']: item for item in project['nodes']}
    edges = [edge for edge in project['edges'] if edge['view'] == view_id]
    hierarchical = [edge for edge in edges if edge['type'] in ('contains', 'part_of')]
    children, descendants = {}, set()
    for edge in hierarchical:
        parent, child = (edge['source'], edge['target']) if edge['type'] == 'contains' else (edge['target'], edge['source'])
        children.setdefault(parent, []).append(child)
        descendants.add(child)
    roots = [node for node in children if node not in descendants]
    if hierarchical and roots:
        parts = ['<ul class="tree">']
        stack = [('close', '</ul>')] + [('node', node) for node in reversed(roots)]
        while stack:
            action, value = stack.pop()
            if action == 'close':
                parts.append(value)
                continue
            parts.append('<li>' + _link('/node/' + value, nodes[value]['title']))
            stack.append(('close', '</li>'))
            if children.get(value):
                parts.append('<ul>')
                stack.append(('close', '</ul>'))
                stack.extend(('node', child) for child in reversed(children[value]))
        rows_content = ''.join(parts)
        other = [edge for edge in edges if edge not in hierarchical]
    else:
        rows_content = ''
        other = edges
    rows_content += ''.join(_row(nodes[edge['source']]['title'] + ' → ' + nodes[edge['target']]['title'], edge['type'], '/node/' + edge['target']) for edge in other)
    rows_content = rows_content or '<p class="empty">No relationships in this view.</p>'
    content = f'<a class="back" href="/?section=views">← Back to indexes</a><div class="crumb">Index / {_text(view["kind"])}</div><h1>{_text(view["title"])}</h1><p class="subtitle">Relationships in this view.</p><section class="detail-section"><div class="panel">{rows_content}</div></section>'
    return _layout(project, content, 'views', export_target='/view/' + view_id)


def render_source(project, source_id):
    source = next(item for item in project.get('sources', []) if item['id'] == source_id)
    content = f'''<a class="back" href="/?section=sources">← Back to sources</a><div class="crumb">Source / {_text(source_id[:8])}</div><h1>{_text(source['title'])}</h1><section class="detail-section"><div class="panel">{_row('Author', source.get('author') or 'Not recorded')}{_row('URL', source.get('url') or 'Not recorded')}{_row('Locator', source.get('locator') or 'Not recorded')}{_row('Reviewed', source.get('reviewed_at') or 'Not recorded')}</div></section><p class="note">A recorded source does not automatically verify a claim.</p>'''
    return _layout(project, content, 'sources', export_target='/source/' + source_id)


def render_import(project, token, message=''):
    notice = f'<p class="note">{_text(message)}</p>' if message else ''
    content = f'''<div class="crumb">Knowledge workspace / Import</div><h1>Import a source</h1>
<p class="subtitle">Convert a local file or fetch a public webpage or YouTube captions into a new Markdown file. Your original is preserved.</p>{notice}
<form method="post" action="/import" class="panel"><input type="hidden" name="token" value="{_text(token)}">
<div class="field"><label for="mode">Source type</label><select id="mode" name="mode"><option value="local">Local file</option><option value="web">Public webpage URL</option><option value="youtube">YouTube video URL</option></select></div>
<div class="field"><label for="source">Local file path or URL</label><input id="source" name="source" required></div>
<div class="field"><label for="storage_root">Temporary storage folder (optional)</label><input id="storage_root" name="storage_root" placeholder="Default: next to the project"></div>
<div class="field"><label for="category">Topic folders (optional, separated by /)</label><input id="category" name="category" placeholder="topic/subtopic"></div>
<p class="note">Each import gets its own folder under pdf, documents, web or youtube. Files remain until you remove them. Local originals are never moved or deleted.</p>
<p class="note">Local files must already be on this computer. PDF, DOCX and XLSX may require optional dependencies. Web imports need Internet access; YouTube imports need yt-dlp and available captions. Imported content is untrusted and is not automatically verified.</p>
<button type="submit">Import source</button></form>'''
    return _layout(project, content, 'import')


def render_page(project, target):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or parts.fragment or len(target) > 4096:
        raise ValueError('invalid page')
    if parts.path == '/':
        params = parse_qs(parts.query, keep_blank_values=True)
        return render(project, params.get('q', [''])[0], params.get('section', ['overview'])[0])
    if parts.query:
        raise ValueError('invalid page query')
    if parts.path.startswith('/node/'):
        return render_node(project, parts.path.removeprefix('/node/'))
    if parts.path.startswith('/view/'):
        return render_view(project, parts.path.removeprefix('/view/'))
    if parts.path.startswith('/source/'):
        return render_source(project, parts.path.removeprefix('/source/'))
    raise ValueError('unknown page')



def render_preview(project, target, format_name):
    """Show the selected page before export; Word preview uses the export blocks."""
    page = render_page(project, target)
    if format_name not in {'word', 'pdf'}:
        raise ValueError('unknown export format')
    back = _text(target)
    if format_name == 'word':
        from .page_export import page_blocks
        tags = {'h1': 'h1', 'h2': 'h2', 'h3': 'h3'}
        content = '<div class="word-brand">INVESTING / OS</div>' + ''.join(
            f'<{tags.get(tag, "p")}>{_text(value)}</{tags.get(tag, "p")}>'
            for tag, value in page_blocks(page))
        action = '<a class="export-pdf" href="{}">Download Word</a>'.format(
            _text('/export/word?' + urlencode({'from': target})))
        description = 'Editable Word document. The preview is approximate; pagination and fonts depend on your Word application.'
        page = _layout(project, content, 'import')
    else:
        action = '<button type="button" id="export-pdf" class="export-pdf">Print or save as PDF</button>'
        description = 'Print-ready layout. The browser print preview determines the final pages, margins and colors.'
    controls = f'<div class="preview-controls"><a href="{back}">← Back to page</a><div><strong>{format_name.upper()} preview</strong><p>{description}</p></div>{action}</div>'
    preview_css = """<style>
    body{background:#e8ede7}.shell{display:block;min-height:0}.sidebar,.topbar,.export-tools,.search,.back{display:none!important}
    main{max-width:794px;margin:32px auto;padding:64px;background:#fff;min-height:1000px;box-shadow:0 8px 32px #1e34231a;overflow-wrap:anywhere}
    .preview-controls{max-width:1050px;margin:24px auto 0;padding:0 20px;display:flex;align-items:center;gap:24px;justify-content:space-between}
    .preview-controls div{flex:1}.preview-controls p{font-size:13px}.preview-controls a,.preview-controls button{flex-shrink:0}
    .word-brand{font:700 13px system-ui;color:#30644e;margin-bottom:38px}.word-preview p{color:#20352d;margin:0 0 9px;white-space:pre-wrap}
    .word-preview h1{font:24pt Georgia,serif;margin:12px 0 18px}.word-preview h2{font:16pt Georgia,serif;color:#30644e;margin:24px 0 12px}.word-preview h3{font:700 12.5pt system-ui;margin:16px 0 8px}
    @media(max-width:800px){main{margin:16px;padding:28px;min-height:0}.preview-controls{align-items:flex-start;flex-wrap:wrap}.preview-controls div{flex-basis:70%}}
    @media print{.preview-controls{display:none!important}main{box-shadow:none;margin:0;padding:0;min-height:0;max-width:none}}
    </style>"""
    page = page.replace('</head>', preview_css + '</head>', 1)
    page = page.replace('<body>', '<body class="' + format_name + '-preview">' + controls, 1)
    if format_name == 'pdf':
        page = page.replace('</body>', '<script>' + PRINT_SCRIPT + '</script></body>', 1)
    return page


def create_server(project_file, port=8000):
    load(project_file)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get('Host', '') not in {f'127.0.0.1:{self.server.server_port}', '127.0.0.1'}:
                self.send_error(400)
                return
            parts = urlsplit(self.path)
            try:
                project = load(project_file)
                if parts.path in {'/preview/word', '/preview/pdf'}:
                    target = parse_qs(parts.query, keep_blank_values=True).get('from', [''])[0]
                    body = render_preview(project, target, parts.path.rsplit('/', 1)[-1])
                elif parts.path == '/export/word':
                    from .page_export import word_document
                    target = parse_qs(parts.query, keep_blank_values=True).get('from', [''])[0]
                    body = word_document(render_page(project, target))
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    self.send_header('Content-Disposition', 'attachment; filename="investingos-page.docx"')
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.end_headers()
                    self.wfile.write(body)
                    return
                elif parts.path == '/import':
                    body = render_import(project, token)
                else:
                    body = render_page(project, self.path)
            except (KeyError, StopIteration, ValueError):
                self.send_error(404)
                return
            except OSError:
                self.send_error(500, 'Unable to load project')
                return
            body = body.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-" + PRINT_HASH + "'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            if (self.path != '/import' or self.headers.get('Host') != expected or
                    self.headers.get('Origin') != 'http://' + expected or
                    self.headers.get('Content-Type', '').split(';')[0] != 'application/x-www-form-urlencoded'):
                self.send_error(403)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8192:
                    raise ValueError('Invalid request size')
                fields = parse_qs(self.rfile.read(length).decode('utf-8'), keep_blank_values=True)
                if not hmac.compare_digest(fields.get('token', [''])[0].encode('utf-8'), token.encode('ascii')):
                    self.send_error(403)
                    return
                mode, source = (fields.get(k, [''])[0] for k in ('mode', 'source'))
                if not source:
                    raise ValueError('Source is required')
                project = load(project_file)
                # Keep explicit destinations supported for existing callers.
                destination = fields.get('destination', [''])[0]
                allocated = None
                if not destination:
                    from pathlib import Path
                    from .import_storage import allocate_import
                    root = fields.get('storage_root', [''])[0] or str(Path(project_file).resolve().parent / 'investing-os-data' / project['id'] / 'temporary')
                    allocated = allocate_import(root, mode, source, fields.get('category', [''])[0])
                    destination = str(allocated)

                try:
                    if mode == 'local':
                        from .markdown_import import import_to_markdown
                        result = import_to_markdown(project, source, destination)
                    elif mode == 'web':
                        from .web_import import import_web
                        result = import_web(project, source, destination)
                    elif mode == 'youtube':
                        from .youtube_import import import_youtube
                        result = import_youtube(project, source, destination)
                    else:
                        raise ValueError('Unknown source type')
                except (OSError, ValueError, zipfile.BadZipFile, http.client.HTTPException, subprocess.CalledProcessError):
                    if allocated is not None:
                        import shutil
                        shutil.rmtree(allocated.parent, ignore_errors=True)
                    raise
                save(project, project_file, overwrite=True)
                message = 'Imported source ' + result['id'] + ' to ' + destination + '. Refresh Sources to view it.'
            except (OSError, ValueError, zipfile.BadZipFile, http.client.HTTPException, subprocess.CalledProcessError) as exc:
                project = load(project_file)
                message = 'Import failed: ' + str(exc)
            body = render_import(project, token, message).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-" + PRINT_HASH + "'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
