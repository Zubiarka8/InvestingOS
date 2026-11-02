"""Export an isolated, non-destructive Markdown snapshot."""
import json
from collections import defaultdict
from pathlib import Path
from .core import audit
from .source_links import local_link, web_link
from .superindex import outline


def _source_lines(sources, destination):
    lines = ['', '## Sources', '']
    if not sources:
        return lines + ['No sources are linked to this note.']
    for source in sources:
        title = str(source.get('title', 'Source')).replace('\n', ' ').replace('[', r'\[').replace(']', r'\]')
        source_note = '[[%s|%s]]' % (source['id'], title.replace('|', r'\|'))
        url = web_link(source.get('url', ''))
        if url:
            lines.append('- ' + source_note + ' — [' + title + '](' + url + ')')
        elif source.get('local_path'):
            path = local_link(source['local_path'], destination)
            lines.append('- ' + source_note + ' — [local original](' + path + ')')
        else:
            lines.append('- ' + source_note + ' (no location recorded)')
    return lines


def _source_note(project, source, claims, nodes, destination):
    lines = ["---", f'id: {json.dumps(source["id"])}', 'type: "source"',
             f'title: {json.dumps(source["title"], ensure_ascii=False)}',
             f'project_id: {json.dumps(project["id"])}',
             f'project_title: {json.dumps(project["title"], ensure_ascii=False)}',
             f'library_status: {json.dumps(source.get("library_status", "inbox"))}',
             f'review_status: {json.dumps("reviewed" if source.get("reviewed_at") else "not-reviewed")}',
             "---", "", "# " + source["title"], "", f'**Project:** [[index|{project["title"]}]]', "", "## Bibliographic details", ""]
    for label, key in (("Author", "author"), ("Year", "year"), ("Publisher", "publisher"),
                       ("Media type", "media_type"),
                       ("Publication type", "publication_type"), ("Accessed", "accessed"),
                       ("Reviewed", "reviewed_at"), ("Review due", "review_due"),
                       ("Locator", "locator"), ("SHA-256", "sha256")):
        if source.get(key):
            lines.append(f"- {label}: {source[key]}")
    if source.get('url'):
        url = web_link(source['url'])
        if url:
            lines.extend(["", f"- URL: [{source['url']}]({url})"])
    if source.get('local_path'):
        lines.extend(["", f"- Local original: [{Path(source['local_path']).name}]({local_link(source['local_path'], destination)})"])
    if source.get('extracted_path'):
        lines.append(f"- Extracted text: [{Path(source['extracted_path']).name}]({local_link(source['extracted_path'], destination)})")
    linked_claims = [claim for claim in claims if source['id'] in claim.get('sources', [])]
    lines.extend(["", "## Linked claims", ""])
    if linked_claims:
        for claim in linked_claims:
            lines.append(f"- {claim['text']} (status: {claim['status']})")
            for node_id in claim.get('nodes', []):
                if node_id in nodes:
                    lines.append(f"  - Knowledge node: [[{node_id}|{nodes[node_id]}]]")
    else:
        lines.append("No claims are linked to this source.")
    lines.extend(["", "Source metadata and review dates do not establish that its contents are accurate."])
    return "\n".join(lines) + "\n"


def export(project, directory):
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    names = {n["id"]: n["title"] for n in project["nodes"]}
    sources = {source["id"]: source for source in project.get("sources", [])}
    for node in project["nodes"]:
        lines = ["---", f'id: {json.dumps(node["id"])}', 'type: "knowledge-node"', f'title: {json.dumps(node["title"], ensure_ascii=False)}',
                 f'project_id: {json.dumps(project["id"])}', f'project_title: {json.dumps(project["title"], ensure_ascii=False)}',
                 'status: "unverified"', "---", "", "# " + node["title"], "", node["description"]]
        lines.extend(["", f'**Project:** [[index|{project["title"]}]]'])
        if node.get('notes'):
            lines.extend(["", "## Study notes", "", node['notes']])
        lines.extend(["", "## Relationships", ""])
        for edge in project["edges"]:
            if edge["source"] == node["id"] and edge["target"] in names:
                lines.append(f'- {edge["type"]}: [[{edge["target"]}|{names[edge["target"]]}]]')
            elif edge["target"] == node["id"] and edge["source"] in names:
                lines.append(f'- {edge["type"]} from: [[{edge["source"]}|{names[edge["source"]]}]]')
        claims = [claim for claim in project.get("claims", []) if node["id"] in claim.get("nodes", [])]
        if claims:
            lines.extend(["", "## Claims", ""])
            for claim in claims:
                lines.append(f'- {claim["text"]} (status: {claim["status"]}; id: {claim["id"]})')
                for source_id in claim["sources"]:
                    source = sources[source_id]
                    lines.append(f'  - Source: [[{source_id}|{source["title"]}]]; {source["url"]}; {source["locator"]}')
        linked_ids = {source_id for claim in claims for source_id in claim['sources']}
        lines.extend(_source_lines([sources[source_id] for source_id in sorted(linked_ids)], directory / (node['id'] + '.md')))
        (directory / (node["id"] + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    for source in sources.values():
        (directory / (source['id'] + '.md')).write_text(
            _source_note(project, source, project.get('claims', []), names, directory / (source['id'] + '.md')),
            encoding='utf-8')
    lines = ["---", f'project_id: {json.dumps(project["id"])}',
             f'project_title: {json.dumps(project["title"], ensure_ascii=False)}',
             'type: "project-index"', "---", "", "# " + project["title"], "", project["description"], "", "## Nodes", ""]
    lines.extend(f'- [[{n["id"]}|{n["title"]}]]' for n in project["nodes"])
    profile = project.get('study_profile', {})
    profile_values = [(label, profile.get(key, '')) for label, key in (
        ('Goal', 'goal'), ('Audience', 'audience'), ('Prior knowledge', 'prior_knowledge'),
        ('Scope', 'scope'), ('Desired depth', 'depth'), ('Constraints', 'constraints'),
        ('Language', 'language')) if profile.get(key)]
    if profile_values:
        lines.extend(["", "## Study profile", ""])
        lines.extend(f'- **{label}:** {value}' for label, value in profile_values)
    lines.extend(["", "## Views", ""])
    for view in project["views"]:
        lines.append(f'### {view["title"]} ({view["kind"]})')
        if view['kind'] == 'hierarchy':
            indexed = outline(project, view['id'])
            for number, node in indexed:
                indent = '  ' * (len(number) - 1)
                position = '.'.join(map(str, number))
                title = node['title'].replace('|', r'\|')
                lines.append(f'{indent}- **{position}** [[{node["id"]}|{title}]]')
            if not indexed:
                lines.append('- No hierarchical relationships assigned yet.')
            for edge in project['edges']:
                if edge['view'] == view['id'] and edge['type'] not in {'contains', 'part_of'}:
                    lines.append(f'- [[{edge["source"]}|{names[edge["source"]]}]] — {edge["type"]} → [[{edge["target"]}|{names[edge["target"]]}]]')
        else:
            for edge in project["edges"]:
                if edge["view"] == view["id"]:
                    lines.append(f'- [[{edge["source"]}|{names[edge["source"]]}]] — {edge["type"]} → [[{edge["target"]}|{names[edge["target"]]}]]')
    lines.extend(["", "## Sources", ""])
    if sources:
        lines.append('- [[sources|Browse the source library]]')
    else:
        lines.append("No sources have been recorded.")
    (directory / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    source_groups = defaultdict(list)
    for source in sources.values():
        group = (source.get('media_type') or source.get('publication_type') or '').strip() or 'Uncategorized'
        source_groups[group].append(source)
    library_lines = ["---", f'project_id: {json.dumps(project["id"])}',
                     f'project_title: {json.dumps(project["title"], ensure_ascii=False)}',
                     'type: "source-library"', "---", "", "# Source library", "",
                     f'**Project:** [[index|{project["title"]}]]', "",
                     "Recorded sources grouped by media type, falling back to publication type. Review dates do not verify source contents.", ""]
    for group in sorted(source_groups, key=str.casefold):
        library_lines.extend([f"## {group}", ""])
        for source in sorted(source_groups[group], key=lambda item: item['title'].casefold()):
            meta = ' · '.join(value for value in (source.get('author', ''), source.get('year', ''),
                                                    source.get('library_status', 'inbox')) if value)
            library_lines.append(f"- [[{source['id']}|{source['title']}]]" + (f" — {meta}" if meta else ""))
        library_lines.append("")
    if not sources:
        library_lines.append("No sources have been recorded.")
    (directory / "sources.md").write_text("\n".join(library_lines).rstrip() + "\n", encoding="utf-8")
    (directory / ".InvestingOS-export.json").write_text(json.dumps(_manifest(project, directory), indent=2) + "\n", encoding="utf-8")


def _digest(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(project, directory):
    files = {path.name: _digest(path) for path in directory.glob('*.md') if path.is_file()}
    return {'project_id': project['id'], 'files': files}


def update_export(project, directory):
    """Update unchanged generated notes; leave edits and deleted notes untouched."""
    import os
    import tempfile
    directory = Path(directory)
    marker = directory / '.InvestingOS-export.json'
    if directory.is_symlink() or marker.is_symlink() or not marker.is_file() or marker.stat().st_nlink != 1:
        raise ValueError('directory is not a managed export')
    old = json.loads(marker.read_text(encoding='utf-8'))
    if old.get('project_id') != project['id'] or not isinstance(old.get('files'), dict):
        raise ValueError('export manifest does not match project')
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / 'fresh'
        export(project, fresh)
        new = json.loads((fresh / marker.name).read_text(encoding='utf-8'))
        report = {'updated': [], 'conflicts': []}
        baseline = dict(old['files'])
        for name, digest in new['files'].items():
            target = directory / name
            prior = baseline.get(name)
            if target.is_symlink() or (target.exists() and (not target.is_file() or prior is None or _digest(target) != prior or target.stat().st_nlink != 1)) or (not target.exists() and prior is not None):
                report['conflicts'].append(name)
                continue
            data = (fresh / name).read_bytes()
            if prior is None:
                with target.open('xb') as handle:
                    handle.write(data)
            elif prior != digest:
                fd, tmpname = tempfile.mkstemp(dir=directory, prefix='.InvestingOS-')
                try:
                    with os.fdopen(fd, 'wb') as handle:
                        handle.write(data)
                    os.replace(tmpname, target)
                finally:
                    if os.path.exists(tmpname):
                        os.unlink(tmpname)
            baseline[name] = digest
            report['updated'].append(name)
        # Deleted nodes are retained; this operation never removes user notes.
        fd, tmpname = tempfile.mkstemp(dir=directory, prefix='.InvestingOS-manifest-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump({'project_id': project['id'], 'files': baseline}, handle, indent=2)
                handle.write('\n')
            os.replace(tmpname, marker)
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)
        return report
