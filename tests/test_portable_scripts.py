import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PortableScriptTests(unittest.TestCase):
    def test_project_entry_points_are_python_only(self):
        for old in ('install.sh', 'scripts/python.sh', 'scripts/youtube.sh', 'bin/investingos'):
            with self.subTest(old=old):
                self.assertFalse((ROOT / old).exists())
        for script in ('scripts/install.py', 'scripts/investingos.py', 'scripts/youtube.py'):
            with self.subTest(script=script):
                result = subprocess.run([sys.executable, str(ROOT / script), '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_course_transcript_helper_is_python_and_extracts_video_id(self):
        import importlib.util
        script = ROOT / 'skills/collections/course-builder-main/scripts/youtube_transcript.py'
        spec = importlib.util.spec_from_file_location('course_transcript', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.video_id('https://youtu.be/abcdefghijk'), 'abcdefghijk')
        self.assertEqual(module.video_id('https://www.youtube.com/watch?v=abcdefghijk'), 'abcdefghijk')
        with self.assertRaises(ValueError):
            module.video_id('https://example.com/abcdefghijk')

    def test_course_transcript_rejects_invalid_data_and_missing_dependency(self):
        import importlib.util
        from unittest.mock import patch
        script = ROOT / 'skills/collections/course-builder-main/scripts/youtube_transcript.py'
        spec = importlib.util.spec_from_file_location('course_transcript_validation', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(['https://example.org/video']), 1)
        self.assertEqual(module.main(['abcdefghijk', 'not a language']), 1)
        with patch.dict(sys.modules, {'youtube_transcript_api': None}):
            self.assertEqual(module.main(['abcdefghijk']), 2)
