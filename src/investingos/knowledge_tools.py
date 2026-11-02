"""Local document provenance, search, and research reports."""
import hashlib
from pathlib import Path

from .core import add_source
from .documents import extract_text


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def import_document(project, original, extracted):
    original, extracted = Path(original).resolve(), Path(extracted).resolve()
    digest = _hash(original)
    extract_text(original, extracted)
    if _hash(original) != digest:
        extracted.unlink()
        raise ValueError('original changed during import')
    source = add_source(project, original.name, media_type=original.suffix.lower().lstrip('.'))
    source.update(local_path=str(original), extracted_path=str(extracted), sha256=digest)
    return source


def search_project(project, query, *, documents=False):
    query = query.strip().casefold()
    if not query:
        raise ValueError('search query must not be empty')
    results = []
    for kind, collection, fields in (
        ('node', 'nodes', ('title', 'description')),
        ('source', 'sources', ('title', 'author', 'url', 'locator', 'local_path')),
        ('claim', 'claims', ('text',)),
    ):
        for item in project.get(collection, []):
            if any(query in str(item.get(field, '')).casefold() for field in fields):
                results.append({'type': kind, 'id': item['id'], 'text': item.get('title', item.get('text', ''))})
    if documents:
        for source in project.get('sources', []):
            if not source.get('extracted_path'):
                continue
            try:
                with Path(source['extracted_path']).open(encoding='utf-8') as handle:
                    matches = any(query in line.casefold() for line in handle)
            except OSError as exc:
                raise ValueError(f"cannot search extracted file for {source['id']}: {exc}") from exc
            if matches:
                results.append({'type': 'document', 'id': source['id'], 'text': source['title']})
    return results


def research_report(project, *, today=None):
    from datetime import date
    today = today or date.today().isoformat()
    claims = project.get('claims', [])
    return {
        'sources_due': [item['id'] for item in project.get('sources', []) if item.get('review_due') and item['review_due'] <= today],
        'pending_tasks': [item['id'] for item in project.get('research_tasks', []) if item['status'] != 'done'],
        'sources_not_reviewed': [item['id'] for item in project.get('sources', []) if not item.get('reviewed_at')],
        'claims_without_sources': [item['id'] for item in claims if not item['sources']],
        'unverified_claims': [item['id'] for item in claims if item['status'] == 'unverified'],
        'disputed_claims': [item['id'] for item in claims if item['status'] == 'disputed'],
        'sources_without_location': [item['id'] for item in project.get('sources', []) if not item['url'] and not item.get('local_path')],
        'contradictory_edges': [item['id'] for item in project['edges'] if item['type'] == 'contradicts'],
    }


def rebase_paths(project, old_root, new_root):
    old_root, new_root = Path(old_root).resolve(), Path(new_root).resolve()
    changes = []
    for source in project.get('sources', []):
        for field in ('local_path', 'extracted_path'):
            if not source.get(field):
                continue
            old_path = Path(source[field]).resolve()
            try:
                relative = old_path.relative_to(old_root)
            except ValueError:
                continue
            new_path = (new_root / relative).resolve()
            if not new_path.is_relative_to(new_root) or not new_path.is_file():
                raise ValueError(f'missing or invalid target: {new_path}')
            if field == 'local_path' and source.get('sha256') and _hash(new_path) != source['sha256']:
                raise ValueError(f'source checksum differs: {new_path}')
            changes.append((source, field, str(new_path)))
    for source, field, value in changes:
        source[field] = value
    return len(changes)
