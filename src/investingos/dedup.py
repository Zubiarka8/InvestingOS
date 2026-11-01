"""Suggest and explicitly merge similar nodes without losing their metadata."""
import copy
from difflib import SequenceMatcher
from .core import audit


def suggest_nodes(project, threshold=0.8):
    nodes = project['nodes']
    return [{'first': a['id'], 'second': b['id'], 'similarity': round(score, 3)}
            for i, a in enumerate(nodes) for b in nodes[i + 1:]
            if (score := SequenceMatcher(None, a['title'].casefold(), b['title'].casefold()).ratio()) >= threshold]


def merge_nodes(project, keep, remove):
    work = copy.deepcopy(project)
    nodes = {n['id']: n for n in work['nodes']}
    if keep == remove or keep not in nodes or remove not in nodes:
        raise ValueError('select two distinct existing nodes')
    target, old = nodes[keep], nodes[remove]
    target.setdefault('merged_ids', []).extend([remove, *old.get('merged_ids', [])])
    target.setdefault('merged_nodes', []).append(old)
    work['nodes'] = [n for n in work['nodes'] if n['id'] != remove]
    for edge in work['edges']:
        for field in ('source', 'target'):
            if edge[field] == remove:
                edge[field] = keep
    for claim in work.get('claims', []):
        if 'nodes' in claim:
            claim['nodes'] = list(dict.fromkeys(keep if n == remove else n for n in claim['nodes']))
    for name in ('research_tasks', 'competencies'):
        for item in work.get(name, []):
            if item['node'] == remove:
                item['node'] = keep
    problems = audit(work)
    if problems:
        raise ValueError('merge violates project integrity: ' + '; '.join(problems))
    project.clear()
    project.update(work)
    return keep
