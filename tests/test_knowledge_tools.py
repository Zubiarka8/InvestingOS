import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from investingos.core import add_claim, add_edge, add_node, create_project


class KnowledgeToolsTests(unittest.TestCase):
    def test_import_registers_source_and_preserves_original(self):
        from investingos.knowledge_tools import import_document
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / 'source.txt'
            original.write_text('Ancient history', encoding='utf-8')
            project = create_project('Research')
            source = import_document(project, original, root / 'extracted.txt')
            self.assertEqual(original.read_text(encoding='utf-8'), 'Ancient history')
            self.assertEqual(project['sources'][0]['id'], source['id'])
            self.assertEqual(source['local_path'], str(original.resolve()))
            self.assertEqual(source['extracted_path'], str((root / 'extracted.txt').resolve()))
            self.assertEqual(len(source['sha256']), 64)

    def test_search_and_research_report(self):
        from investingos.knowledge_tools import search_project, research_report
        project = create_project('History')
        first = add_node(project, 'Rome')
        second = add_node(project, 'Empire')
        add_edge(project, first['id'], second['id'], 'contradicts')
        claim = add_claim(project, 'Roman claim')
        self.assertEqual(search_project(project, 'rom')[0]['id'], first['id'])
        report = research_report(project)
        self.assertIn(claim['id'], report['claims_without_sources'])
        self.assertEqual(len(report['contradictory_edges']), 1)

    def test_full_backup_restore_and_reject_collision(self):
        from investingos.backup import backup_bundle, restore_bundle
        from investingos.storage import save
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project.json'
            save(create_project('Project'), project)
            documents = root / 'documents'
            documents.mkdir()
            (documents / 'document.txt').write_text('original', encoding='utf-8')
            backup = root / 'backup.zip'
            backup_bundle(project, backup, [documents])
            restored = root / 'restored'
            restore_bundle(backup, restored)
            self.assertEqual((restored / 'data/0/document.txt').read_text(), 'original')
            with self.assertRaises(FileExistsError):
                restore_bundle(backup, restored)

class KnowledgeCLITests(unittest.TestCase):
    def test_import_search_report_and_backup_commands(self):
        import json
        import subprocess
        runner = Path(__file__).resolve().parents[1] / 'scripts/investingos.py'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, source, extracted, archive = (root / name for name in ('project.json', 'source.txt', 'out.txt', 'backup.zip'))
            source.write_text('Example document', encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable, str(runner), *map(str, args)], check=True, capture_output=True, text=True).stdout
            run('create', project, 'Test')
            run('import-document', project, source, extracted)
            self.assertEqual(json.loads(run('search', project, 'source'))[0]['type'], 'source')
            self.assertIn('claims_without_sources', json.loads(run('research-report', project)))
            run('backup-bundle', project, archive, '--include', source)
            run('restore-bundle', archive, root / 'restore')
            self.assertEqual((root / 'restore/data/0/source.txt').read_text(), 'Example document')

class BackupSafetyTests(unittest.TestCase):
    def test_rejects_traversal_without_creating_destination(self):
        import json
        import zipfile
        from investingos.backup import restore_bundle
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'malicious.zip'
            with zipfile.ZipFile(archive, 'w') as zip_file:
                zip_file.writestr('manifest.json', json.dumps({'version': 1, 'inputs': []}))
                zip_file.writestr('project.json', '{}')
                zip_file.writestr('../escape.txt', 'bad')
            with self.assertRaises(ValueError):
                restore_bundle(archive, root / 'restored')
            self.assertFalse((root / 'restored').exists())
            self.assertFalse((root / 'escape.txt').exists())
