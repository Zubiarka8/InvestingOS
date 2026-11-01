import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from investingos.core import create_project, add_node, add_source, audit

class ExtendedModelTests(unittest.TestCase):
    def test_competency_and_path_validate_references(self):
        from investingos.competencies import add_competency, add_path
        p = create_project('Topic')
        node = add_node(p, 'Theory')
        competency = add_competency(p, 'Explain', node=node['id'], level='beginner', evidence='Demonstrate')
        path = add_path(p, 'Sequence', [competency['id']])
        self.assertFalse(audit(p))
        self.assertEqual(path['competencies'], [competency['id']])
        with self.assertRaises(ValueError):
            add_path(p, 'Invalid', ['missing'])

    def test_source_review_due_and_bibtex(self):
        from investingos.research import schedule_review, export_bibtex
        from investingos.knowledge_tools import research_report
        p = create_project('Topic')
        source = add_source(p, 'Paper', author='Jane Doe')
        schedule_review(p, source['id'], '2026-01-01')
        self.assertIn(source['id'], research_report(p, today='2026-11-01')['sources_due'])
        self.assertIn('Paper', export_bibtex(p))

    def test_overwrite_creates_recoverable_previous_version(self):
        import tempfile
        from investingos.storage import save, load
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'project.json'
            project = create_project('Original')
            save(project, path)
            project['title'] = 'Changed'
            save(project, path, overwrite=True)
            versions = list((Path(tmp) / '.investing-os-history' / project['id']).glob('*.json'))
            self.assertEqual(len(versions), 1)
            self.assertEqual(load(versions[0])['title'], 'Original')

    def test_merge_nodes_preserves_alias_and_retargets_relations(self):
        from investingos.core import add_edge
        from investingos.dedup import merge_nodes
        p = create_project('Topic')
        a = add_node(p, 'Astronomy')
        b = add_node(p, 'Astronomy science')
        c = add_node(p, 'Stars')
        add_edge(p, b['id'], c['id'], 'related_to')
        merge_nodes(p, a['id'], b['id'])
        self.assertEqual(p['edges'][0]['source'], a['id'])
        self.assertIn(b['id'], p['nodes'][0]['merged_ids'])
        self.assertFalse(audit(p))

    def test_rebase_paths_requires_existing_targets(self):
        import tempfile
        from investingos.knowledge_tools import rebase_paths
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / 'old', Path(tmp) / 'new'
            new.mkdir()
            (new / 'source.txt').write_text('data', encoding='utf-8')
            p = create_project('Topic')
            source = add_source(p, 'Source')
            source['local_path'] = str(old / 'source.txt')
            rebase_paths(p, old, new)
            self.assertEqual(source['local_path'], str((new / 'source.txt').resolve()))
