"""Research tasks, source-linked evidence, and outline import."""
import copy
from .core import add_edge, add_node, add_view, identifier


def add_task(project, question, *, node=None, priority='normal'):
    if not isinstance(question, str) or not question.strip() or priority not in {'low', 'normal', 'high'}:
        raise ValueError('invalid research task')
    if node is not None and node not in {n['id'] for n in project['nodes']}:
        raise ValueError('task references a missing node')
    item = {'id': identifier(), 'question': question, 'node': node, 'priority': priority, 'status': 'pending'}
    project.setdefault('research_tasks', []).append(item)
    return item


def add_evidence(project, claim, source, locator, note=''):
    claims = {c['id']: c for c in project.get('claims', [])}
    if claim not in claims or source not in {s['id'] for s in project.get('sources', [])}:
        raise ValueError('evidence references a missing claim or source')
    if source not in claims[claim]['sources']:
        raise ValueError('source must be linked to the claim')
    if not isinstance(locator, str) or not locator.strip() or not isinstance(note, str):
        raise ValueError('evidence requires a locator')
    item = {'id': identifier(), 'claim': claim, 'source': source, 'locator': locator, 'note': note}
    project.setdefault('evidence', []).append(item)
    return item


def import_outline(project, text):
    work = copy.deepcopy(project)
    lines = []
    for line in text.splitlines():
        if not line.strip():
            continue
        prefix = line[:len(line) - len(line.lstrip())]
        if '\t' in prefix or len(prefix) % 2:
            raise ValueError('use multiples of two spaces for outline indentation')
        depth = len(prefix) // 2
        if (not lines and depth) or (lines and depth > lines[-1][0] + 1):
            raise ValueError('outline skips a level')
        lines.append((depth, line.strip()))
    if not lines:
        raise ValueError('outline is empty')
    existing = {item['title'].strip().casefold() for item in work['nodes']}
    for _, title in lines:
        if title.casefold() in existing:
            raise ValueError('duplicate title in outline or project: ' + title)
        existing.add(title.casefold())
    view = add_view(work, 'Imported outline')
    parents = []
    root_order = []
    for depth, title in lines:
        node = add_node(work, title)
        parents = parents[:depth]
        if depth:
            add_edge(work, parents[-1], node['id'], 'contains', view['id'])
        else:
            root_order.append(node['id'])
        parents.append(node['id'])
    view['root_order'] = root_order
    project.clear()
    project.update(work)
    return view


def export_csl(project):
    records = []
    for source in project.get('sources', []):
        entry = {'id': source['id'], 'type': 'document', 'title': source['title']}
        if source['author']:
            entry['author'] = [{'literal': source['author']}]
        if source['url']:
            entry['URL'] = source['url']
        if source.get('year', '').isdigit() and len(source['year']) == 4:
            entry['issued'] = {'date-parts': [[int(source['year'])]]}
        if source.get('publisher'):
            entry['publisher'] = source['publisher']
        records.append(entry)
    return records


def review_source(project, source_id, date):
    from datetime import date as date_type
    try:
        if date_type.fromisoformat(date).isoformat() != date:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('review date must be YYYY-MM-DD') from None
    source = next((s for s in project.get('sources', []) if s['id'] == source_id), None)
    if source is None:
        raise ValueError('source not found')
    source['reviewed_at'] = date
    return source


def set_task_status(project, task_id, status):
    if status not in {'pending', 'in_progress', 'done'}:
        raise ValueError('invalid task status')
    task = next((t for t in project.get('research_tasks', []) if t['id'] == task_id), None)
    if task is None:
        raise ValueError('task not found')
    task['status'] = status
    return task


def compare_projects(before, after):
    if before['id'] != after['id']:
        raise ValueError('projects have different identifiers')
    collections = ('nodes', 'edges', 'views', 'sources', 'claims', 'research_tasks', 'evidence', 'competencies', 'learning_paths')
    def entries(project):
        return {item['id']: item for name in collections for item in project.get(name, [])}
    old, new = entries(before), entries(after)
    return {'added': sorted(new.keys() - old.keys()), 'removed': sorted(old.keys() - new.keys()),
            'changed': sorted(key for key in old.keys() & new.keys() if old[key] != new[key]),
            'project_metadata_changed': any(before.get(key) != after.get(key) for key in ('title', 'description', 'study_profile'))}


def schedule_review(project, source_id, date):
    from datetime import date as date_type
    try:
        if date_type.fromisoformat(date).isoformat() != date:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('review date must be YYYY-MM-DD') from None
    source = next((s for s in project.get('sources', []) if s['id'] == source_id), None)
    if source is None:
        raise ValueError('source not found')
    source['review_due'] = date
    return source


def export_bibtex(project):
    def escape(value):
        return value.replace('\\', r'\textbackslash{}').replace('{', r'\{').replace('}', r'\}').replace('\n', ' ')
    records = []
    for source in project.get('sources', []):
        fields = [f"  title = {{{escape(source['title'])}}}"]
        for name, field in [('author', 'author'), ('url', 'url'), ('year', 'year'), ('publisher', 'publisher')]:
            if source.get(field):
                fields.append(f"  {name} = {{{escape(source[field])}}}")
        records.append('@misc{' + source['id'] + ',\n' + ',\n'.join(fields) + '\n}')
    return '\n\n'.join(records) + ('\n' if records else '')
