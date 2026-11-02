import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'scripts/InvestingOS.py'


class UtilityTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(RUNNER), *map(str, args)], text=True, capture_output=True)

    def test_backup_and_restore_refuse_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project.json'
            backup = Path(tmp) / 'backup.json'
            restored = Path(tmp) / 'restored.json'
            self.assertEqual(self.run_cli('create', project, 'Project').returncode, 0)
            self.assertEqual(self.run_cli('backup', project, backup).returncode, 0)
            self.assertEqual(self.run_cli('restore', backup, restored).returncode, 0)
            self.assertEqual(project.read_bytes(), restored.read_bytes())
            self.assertNotEqual(self.run_cli('restore', backup, restored).returncode, 0)

    def test_doctor_reports_python_and_optional_tools(self):
        result = self.run_cli('doctor')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Python', result.stdout)
        self.assertIn('yt-dlp', result.stdout)


if __name__ == '__main__':
    unittest.main()
