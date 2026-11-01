"""Export an isolated, non-destructive Markdown snapshot."""
import json
from pathlib import Path
from .core import audit
from .source_links import local_link, web_link


def _source_lines(sources, destination):
    lines = ['', '## Sources', '']
    if not sources:
        return lines + ['No sources are linked to this note.']
    for source in sources:
        title = str(source.get('title', 'Source')).replace('\n', ' ').replace('[', r'\[').replace(']', r'\]')
        url = web_link(source.get('url', ''))
        if not url and source.get('local_path'):
            url = local_link(source['local_path'], destination)
        lines.append('- [' + title + '](' + url + ')' if url else '- ' + title + ' (no location recorded)')
    return lines


def export(project, directory):
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    names = {n["id"]: n["title"] for n in project["nodes"]}
    for node in project["nodes"]:
        lines = ["---", f'id: {json.dumps(node["id"])}', f'title: {json.dumps(node["title"], ensure_ascii=False)}',
                 'status: "unverified"', "---", "", "# " + node["title"], "", node["description"], "", "## Relationships", ""]
        for edge in project["edges"]:
            if edge["source"] == node["id"]:
                lines.append(f'- {edge["type"]}: [[{edge["target"]}|{names[edge["target"]]}]]')
        sources = {source["id"]: source for source in project.get("sources", [])}
        claims = [claim for claim in project.get("claims", []) if node["id"] in claim.get("nodes", [])]
        if claims:
            lines.extend(["", "## Claims", ""])
            for claim in claims:
                lines.append(f'- {claim["text"]} (status: {claim["status"]}; id: {claim["id"]})')
                for source_id in claim["sources"]:
                    source = sources[source_id]
                    lines.append(f'  - Source: {source["title"]}; {source["url"]}; {source["locator"]}')
        linked_ids = {source_id for claim in claims for source_id in claim['sources']}
        lines.extend(_source_lines([sources[source_id] for source_id in sorted(linked_ids)], directory / (node['id'] + '.md')))
        (directory / (node["id"] + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = ["# " + project["title"], "", project["description"], "", "## Nodes", ""]
    lines.extend(f'- [[{n["id"]}|{n["title"]}]]' for n in project["nodes"])
    lines.extend(["", "## Views", ""])
    for view in project["views"]:
        lines.append(f'### {view["title"]} ({view["kind"]})')
        for edge in project["edges"]:
            if edge["view"] == view["id"]:
                lines.append(f'- [[{edge["source"]}|{names[edge["source"]]}]] — {edge["type"]} → [[{edge["target"]}|{names[edge["target"]]}]]')
    lines.extend(_source_lines(project.get('sources', []), directory / 'index.md'))
    (directory / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (directory / ".investing-os-export.json").write_text(json.dumps(_manifest(project, directory), indent=2) + "\n", encoding="utf-8")


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
    marker = directory / '.investing-os-export.json'
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
                fd, tmpname = tempfile.mkstemp(dir=directory, prefix='.investingos-')
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
        fd, tmpname = tempfile.mkstemp(dir=directory, prefix='.investingos-manifest-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump({'project_id': project['id'], 'files': baseline}, handle, indent=2)
                handle.write('\n')
            os.replace(tmpname, marker)
        finally:
            if os.path.exists(tmpname):
                os.unlink(tmpname)
        return report
