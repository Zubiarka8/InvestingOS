"""Checks that the public skill package is consistent and excludes held-back material."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

HELD_BACK_NAMES = {"VaultForge-main", "writing-guidelines"}
EDU = ROOT / "skills/collections/education-agent-skills-main"
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")


def manifest():
    return json.loads((ROOT / "skills/manifest.json").read_text(encoding="utf-8"))


def local_links(path):
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue
        yield target, (path.parent / unquote(target.split("#")[0])).resolve()


class ManifestTests(unittest.TestCase):
    def test_every_entry_resolves_to_a_skill_and_none_is_held_back(self):
        for name, relative in manifest().items():
            source = ROOT / relative
            self.assertTrue((source / "SKILL.md").is_file(), name)
            self.assertNotIn("local-only", Path(relative).parts, name)
        self.assertFalse(HELD_BACK_NAMES & manifest().keys())

    def test_education_collection_has_165_manifest_skills(self):
        education = [n for n, r in manifest().items() if "education-agent-skills-main" in r]
        self.assertEqual(len(education), 165)
        self.assertEqual(len(list((EDU / "skills").rglob("SKILL.md"))), 165)

    def test_held_back_directory_is_ignored_by_git(self):
        self.assertIn("/local-only/", (ROOT / ".gitignore").read_text().splitlines())


class EducationScopeTests(unittest.TestCase):
    def test_license_and_modification_notice_are_present(self):
        self.assertIn("Attribution-ShareAlike 4.0", (EDU / "LICENSE").read_text(encoding="utf-8"))
        notice = (EDU / "NOTICE-InvestingOS.md").read_text(encoding="utf-8")
        for needle in ("Gareth Manning", "135d6275e7db0657d70b147f46d3191c5430677d",
                       "creativecommons.org/licenses/by-sa/4.0", "removed"):
            self.assertIn(needle, notice)

    def test_code_outside_the_licensed_materials_is_not_in_the_public_tree(self):
        for held in ("mcp-server", "scripts", "tests", "requirements", "package.json",
                     "package-lock.json", "playwright.config.ts", "registry.json", "assets"):
            self.assertFalse((EDU / held).exists(), held)


class DocumentationTests(unittest.TestCase):
    def test_local_links_resolve(self):
        files = [ROOT / "skills/INDEX.md", ROOT / "README.md", ROOT / "docs/skill-redistribution-review.md",
                 ROOT / "docs/user-guide.md", ROOT / "docs/skills-management.md",
                 ROOT / "skills/collections/README.md"]
        broken = [f"{f.relative_to(ROOT)} -> {t}" for f in files for t, p in local_links(f) if not p.exists()]
        self.assertEqual(broken, [])

    def test_counts_match_the_manifest(self):
        total = len(manifest())
        self.assertIn(f"{total} skills", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(f"all {total} manifest entries", (ROOT / "docs/skill-redistribution-review.md").read_text(encoding="utf-8"))
        review = (ROOT / "docs/skill-redistribution-review.md").read_text(encoding="utf-8")
        rows = [l for l in review.splitlines() if re.match(r"^\| \[[^\]]+\]\(\.\./skills/[^)]*SKILL\.md\)", l)]
        self.assertEqual(len(rows), total)

    def test_index_does_not_offer_held_back_skills(self):
        index = (ROOT / "skills/INDEX.md").read_text(encoding="utf-8")
        self.assertNotIn("](collections/VaultForge-main", index)
        self.assertNotIn("](writing-guidelines/", index)


class InstallerGuardTests(unittest.TestCase):
    def test_installer_rejects_held_back_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            held = root / "local-only/skills/example"
            held.mkdir(parents=True)
            (held / "SKILL.md").write_text("example")
            (root / "skills").mkdir()
            (root / "skills/manifest.json").write_text(json.dumps({"example": "local-only/skills/example"}))
            with self.assertRaisesRegex(ValueError, "held-back"):
                installer.install(root)
            self.assertFalse((root / ".agents").exists())

    def test_full_bundle_installs_into_a_clean_checkout_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, relative in manifest().items():
                (root / relative).mkdir(parents=True, exist_ok=True)
                (root / relative / "SKILL.md").write_text("x")
            (root / "skills/manifest.json").write_text(json.dumps(manifest()))
            installer.install(root, clients=("shared", "claude"), names=None)
            for client in (".agents", ".claude"):
                self.assertEqual(len(list((root / client / "skills").iterdir())), len(manifest()))


if __name__ == "__main__":
    unittest.main()
