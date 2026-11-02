import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS.core import add_claim, add_node, add_source, audit, create_project

class ResearchWorkflowTests(unittest.TestCase):
    def test_task_and_evidence_have_checked_references(self):
        from InvestingOS.research import add_task, add_evidence
        p = create_project('Topic')
        node = add_node(p, 'Area')
        source = add_source(p, 'Source')
        claim = add_claim(p, 'Claim', sources=[source['id']])
        task = add_task(p, 'Find primary sources', node=node['id'])
        evidence = add_evidence(p, claim['id'], source['id'], 'Page 7', 'Excerpt')
        self.assertEqual(task['status'], 'pending')
        self.assertEqual(evidence['locator'], 'Page 7')
        self.assertFalse(audit(p))
        p['sources'].clear()
        self.assertTrue(audit(p))

    def test_indented_outline_creates_parent_child_relations(self):
        from InvestingOS.research import import_outline
        p = create_project('Topic')
        import_outline(p, 'A\n  B\n    C\n  D\n')
        self.assertEqual(len(p['nodes']), 4)
        self.assertEqual(len(p['edges']), 3)
        self.assertFalse(audit(p))

    def test_outline_bad_indent_does_not_mutate_project(self):
        from InvestingOS.research import import_outline
        p = create_project('Topic')
        with self.assertRaises(ValueError):
            import_outline(p, 'A\n   B\n  C')
        self.assertEqual(p['nodes'], [])

class ResearchWorkflowCLITests(unittest.TestCase):
    def test_import_and_task_commands(self):
        import json, subprocess, tempfile
        runner = Path(__file__).resolve().parents[1] / 'scripts/InvestingOS.py'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, outline = root / 'project.json', root / 'outline.txt'
            outline.write_text('A\n  B\n', encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable, str(runner), *map(str, args)], check=True, capture_output=True, text=True).stdout.strip()
            run('create', project, 'Topic')
            run('import-outline', project, outline)
            node = json.loads(run('show', project))['nodes'][0]['id']
            run('add-research-task', project, 'Find sources', '--node', node)
            self.assertEqual(len(json.loads(run('show', project))['research_tasks']), 1)

class ExtraWorkflowTests(unittest.TestCase):
    def test_search_extracted_documents_and_missing_files(self):
        import tempfile
        from InvestingOS.knowledge_tools import search_project
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'extracted.txt'
            path.write_text('Rare discovery', encoding='utf-8')
            p = create_project('Topic')
            source = add_source(p, 'Paper')
            source['extracted_path'] = str(path)
            self.assertTrue(any(r['id'] == source['id'] for r in search_project(p, 'discovery', documents=True)))
            path.unlink()
            with self.assertRaises(ValueError):
                search_project(p, 'discovery', documents=True)

    def test_export_csl_citation_without_invented_authors(self):
        from InvestingOS.research import export_csl
        p = create_project('Topic')
        source = add_source(p, 'A paper', author='A. Author', url='https://example.org')
        records = export_csl(p)
        self.assertEqual(records[0]['id'], source['id'])
        self.assertEqual(records[0]['title'], 'A paper')
        self.assertEqual(records[0]['author'], [{'literal': 'A. Author'}])

class ReviewWorkflowTests(unittest.TestCase):
    def test_record_review_and_task_status(self):
        from InvestingOS.research import add_task, review_source, set_task_status
        p = create_project('Topic')
        source = add_source(p, 'Paper')
        task = add_task(p, 'Verify')
        review_source(p, source['id'], '2026-11-01')
        set_task_status(p, task['id'], 'done')
        self.assertEqual(source['reviewed_at'], '2026-11-01')
        self.assertEqual(task['status'], 'done')
        with self.assertRaises(ValueError):
            review_source(p, source['id'], 'invalid')

class ComparisonTests(unittest.TestCase):
    def test_compare_reports_changes_by_stable_id(self):
        import copy
        from InvestingOS.research import compare_projects
        before = create_project('Topic')
        node = add_node(before, 'A')
        after = copy.deepcopy(before)
        after['nodes'][0]['description'] = 'Changed'
        added = add_node(after, 'B')
        result = compare_projects(before, after)
        self.assertIn(node['id'], result['changed'])
        self.assertIn(added['id'], result['added'])
        with self.assertRaises(ValueError):
            compare_projects(before, create_project('Other'))
