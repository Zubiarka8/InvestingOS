"""Build numbered, view-specific outlines without a recursion depth limit."""


def outline(project, view_id, root=None):
    nodes = {node['id']: node for node in project['nodes']}
    if view_id not in {view['id'] for view in project['views']}:
        raise ValueError('unknown view')
    children, incoming = {}, set()
    for edge in project['edges']:
        if edge.get('view') != view_id or edge['type'] not in ('contains', 'part_of'):
            continue
        parent, child = ((edge['source'], edge['target']) if edge['type'] == 'contains'
                         else (edge['target'], edge['source']))
        if parent not in nodes or child not in nodes:
            raise ValueError('hierarchy references a missing node')
        if child not in children.setdefault(parent, []):
            children[parent].append(child)
            incoming.add(child)
    if root is not None:
        if root not in nodes:
            raise ValueError('unknown root')
        roots = [root]
    else:
        roots = [node for node in children if node not in incoming]
    result, active, visited = [], set(), set()
    stack = [('enter', node, (index,)) for index, node in reversed(list(enumerate(roots, 1)))]
    while stack:
        action, node, number = stack.pop()
        if action == 'leave':
            active.remove(node)
            continue
        if node in active:
            raise ValueError('cycle in hierarchy')
        active.add(node)
        visited.add(node)
        result.append((number, nodes[node]))
        stack.append(('leave', node, number))
        for index, child in reversed(list(enumerate(children.get(node, ()), 1))):
            stack.append(('enter', child, number + (index,)))
    if root is None and any(node not in visited for node in children):
        raise ValueError('cycle in hierarchy')
    return result
