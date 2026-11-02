import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from InvestingOS import core
from InvestingOS.storage import load, save


class ResearchTests(unittest.TestCase):
    def test_source_and_claim_round_trip(self):
        project = core.create_project('Research')
        source = core.add_source(project, 'Paper', url='https://example.org/paper', author='Author')
        claim = core.add_claim(project, 'A claim', sources=[source['id']])
        self.assertEqual(claim['status'], 'unverified')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'project.json'
            save(project, path)
            self.assertEqual(load(path), project)

    def test_missing_source_rejected(self):
        project = core.create_project('Research')
        with self.assertRaises(ValueError):
            core.add_claim(project, 'A claim', sources=['missing'])

    def test_broken_reference_detected(self):
        project = core.create_project('Research')
        source = core.add_source(project, 'Paper')
        core.add_claim(project, 'Claim', sources=[source['id']])
        project['sources'].clear()
        self.assertTrue(any('broken source' in message for message in core.audit(project)))


if __name__ == '__main__':
    unittest.main()

class ResearchCLITests(unittest.TestCase):
    def test_source_and_claim_cli(self):
        import subprocess
        runner = Path(__file__).resolve().parents[1] / 'scripts/InvestingOS.py'
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'project.json')
            def run(*args):
                return subprocess.run([sys.executable, str(runner), *args], check=True, capture_output=True, text=True).stdout.strip()
            run('create', path, 'Research')
            source = run('add-source', path, 'Paper', '--url', 'https://example.org')
            run('add-claim', path, 'Claim', '--source', source)
            self.assertEqual(load(path)['claims'][0]['sources'], [source])
