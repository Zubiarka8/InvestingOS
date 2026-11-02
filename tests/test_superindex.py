import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.core import create_project, add_node, add_view
from InvestingOS.superindex import outline
from InvestingOS.web_viewer import render


class SuperindexTests(unittest.TestCase):
    def test_deep_outline_and_shared_concept(self):
        project = create_project('Knowledge')
        view = add_view(project, 'Structure')
        nodes = [add_node(project, f'Topic {i}') for i in range(1100)]
        for i in range(len(nodes) - 1):
            project['edges'].append({'source': nodes[i]['id'], 'target': nodes[i + 1]['id'],
                                     'type': 'contains', 'view': view['id']})
        items = outline(project, view['id'])
        self.assertEqual(len(items), 1100)
        self.assertEqual(len(items[-1][0]), 1100)
        html = render(project, section='superindex')
        self.assertIn('Topic 1099', html)
        self.assertIn('/node/' + nodes[-1]['id'], html)

    def test_multiple_parents_and_cycles(self):
        project = create_project('Knowledge')
        view = add_view(project, 'Structure')
        a, b, c = [add_node(project, title) for title in ('A', 'B', 'C')]
        def edge(parent, child):
            project['edges'].append({'source': parent['id'], 'target': child['id'], 'type': 'contains', 'view': view['id']})
        edge(a, c)
        edge(b, c)
        items = outline(project, view['id'])
        self.assertEqual([number for number, node in items if node['id'] == c['id']], [(1, 1), (2, 1)])
        edge(c, a)
        with self.assertRaisesRegex(ValueError, 'cycle'):
            outline(project, view['id'])

    def test_part_of_direction_and_branch(self):
        project = create_project('Knowledge')
        view = add_view(project, 'Structure')
        parent, child = [add_node(project, title) for title in ('Parent', 'Child')]
        project['edges'].append({'source': child['id'], 'target': parent['id'], 'type': 'part_of', 'view': view['id']})
        self.assertEqual([node['title'] for _, node in outline(project, view['id'])], ['Parent', 'Child'])
        self.assertEqual([node['title'] for _, node in outline(project, view['id'], child['id'])], ['Child'])
