"""Domain-neutral competency records and ordered paths."""
from .core import identifier


def add_competency(project, title, *, node=None, level='', evidence=''):
    if not isinstance(title, str) or not title.strip() or not all(isinstance(v, str) for v in (level, evidence)):
        raise ValueError('invalid competency')
    if node is not None and node not in {n['id'] for n in project['nodes']}:
        raise ValueError('competency references a missing node')
    item = {'id': identifier(), 'title': title, 'node': node, 'level': level, 'evidence': evidence}
    project.setdefault('competencies', []).append(item)
    return item


def add_path(project, title, competencies):
    competencies = list(competencies)
    if not isinstance(title, str) or not title.strip() or not competencies:
        raise ValueError('path requires a title and competencies')
    if len(competencies) != len(set(competencies)) or any(c not in {v['id'] for v in project.get('competencies', [])} for c in competencies):
        raise ValueError('path contains duplicate or missing competencies')
    item = {'id': identifier(), 'title': title, 'competencies': competencies}
    project.setdefault('learning_paths', []).append(item)
    return item
