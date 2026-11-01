import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_links_are_created_and_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills/example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("example")
            (root / "skills/manifest.json").write_text(json.dumps({"example": "skills/example"}))
            installer.install(root, clients=("shared", "claude"))
            installer.install(root, clients=("shared", "claude"))
            for client in (".agents", ".claude"):
                self.assertEqual((root / client / "skills/example").resolve(), skill.resolve())

    def test_conflict_does_not_create_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills/example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("example")
            (root / "skills/manifest.json").write_text(json.dumps({"example": "skills/example"}))
            conflict = root / ".claude/skills/example"
            conflict.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "destination already exists"):
                installer.install(root, clients=("shared", "claude"))
            self.assertFalse((root / ".agents/skills/example").exists())
            self.assertTrue(conflict.is_dir())


if __name__ == "__main__":
    unittest.main()

class ClientSelectionTests(unittest.TestCase):
    def test_shared_install_does_not_create_claude_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / 'skills/example'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('example')
            (root / 'skills/manifest.json').write_text(json.dumps({'example': 'skills/example'}))
            installer.install(root, clients=('shared',))
            self.assertTrue((root / '.agents/skills/example').is_symlink())
            self.assertFalse((root / '.claude').exists())

    def test_claude_install_does_not_create_shared_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / 'skills/example'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('example')
            (root / 'skills/manifest.json').write_text(json.dumps({'example': 'skills/example'}))
            installer.install(root, clients=('claude',))
            self.assertTrue((root / '.claude/skills/example').is_symlink())
            self.assertFalse((root / '.agents').exists())

class SkillSelectionTests(unittest.TestCase):
    def test_can_install_one_skill_without_unrelated_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {}
            for name in ('investingos', 'other'):
                directory = root / 'skills' / name
                directory.mkdir(parents=True)
                (directory / 'SKILL.md').write_text('example')
                manifest[name] = f'skills/{name}'
            (root / 'skills/manifest.json').write_text(json.dumps(manifest))
            installer.install(root, clients=('shared',), names=('investingos',))
            self.assertTrue((root / '.agents/skills/investingos').is_symlink())
            self.assertFalse((root / '.agents/skills/other').exists())
