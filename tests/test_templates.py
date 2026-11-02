"""Checks the Markdown authoring templates: structure, placeholders, links and agreement with the engine."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from InvestingOS.core import CLAIM_STATUSES, SOURCE_LIBRARY_STATUSES, add_claim, add_node, add_source, create_project
from InvestingOS.export import export

DIR = ROOT / "skills/InvestingOS/templates"
README = (DIR / "README.md").read_text(encoding="utf-8")
EXPECTED_KEYS = {
    "project-home": {"type", "project_id", "project_title", "status"},
    "knowledge-node": {"id", "type", "title", "project_id", "project_title", "status", "aliases"},
    "source-record": {"id", "type", "title", "project_id", "project_title", "library_status", "review_status", "media_type"},
    "competency": {"id", "type", "title", "project_id", "project_title", "node_id", "level", "status"},
    "learning-path": {"id", "type", "title", "project_id", "project_title", "status"},
}
# Fields that belong to the frontmatter only; the body must not repeat them as a bullet.
NOT_IN_BODY = {
    "competency": ("**Status:**", "**Project-defined level:**"),
    "knowledge-node": ("**Aliases:**",),
    "source-record": ("**Review status:**", "**Title:**"),
}


def split(name):
    text = (DIR / f"{name}.md").read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, name
    pairs = [line.partition(":")[::2] for line in match.group(1).splitlines()]
    return text, {k.strip(): v.strip() for k, v in pairs}, text[match.end():]


def frontmatter_of(path):
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    return {k.strip(): v.strip().strip('"') for k, _, v in (l.partition(":") for l in match.group(1).splitlines())}


class StructureTests(unittest.TestCase):
    def test_readme_lists_every_template_and_links_resolve(self):
        files = {p.stem for p in DIR.glob("*.md")} - {"README"}
        self.assertEqual(files, set(EXPECTED_KEYS))
        for name in files:
            self.assertIn(f"]({name}.md)", README)

    def test_frontmatter_keys_are_the_documented_ones(self):
        for name, keys in EXPECTED_KEYS.items():
            _, front, _ = split(name)
            self.assertEqual(set(front), keys, name)
            self.assertEqual(front["type"].strip('"'), name if name != "source-record" else "source")

    def test_headings_have_one_h1_no_skips_and_no_repeats(self):
        for name in EXPECTED_KEYS:
            _, _, body = split(name)
            heads = [(len(m.group(1)), m.group(2)) for m in re.finditer(r"^(#{1,6}) (.+)$", body, re.M)]
            self.assertEqual(sum(1 for level, _ in heads if level == 1), 1, name)
            levels = [level for level, _ in heads]
            self.assertTrue(all(b <= a + 1 for a, b in zip(levels, levels[1:])), name)
            titles = [t for _, t in heads]
            self.assertEqual(len(titles), len(set(titles)), name)

    def test_placeholders_are_balanced_snake_case(self):
        for name in EXPECTED_KEYS:
            text, _, _ = split(name)
            self.assertEqual(text.count("{{"), text.count("}}"), name)
            for token in re.findall(r"\{\{([^{}]*)\}\}", text):
                self.assertRegex(token, r"^[a-zA-Z0-9_\-]+$", f"{name}: {token}")

    def test_wikilinks_have_aliases_and_table_pipes_are_escaped(self):
        for name in EXPECTED_KEYS:
            text, _, _ = split(name)
            for target in re.findall(r"\[\[([^\]]*)\]\]", text):
                self.assertRegex(target, r"\\?\|", f"{name}: {target}")
            for line in text.splitlines():
                if line.startswith("|"):
                    self.assertNotRegex(line, r"\[\[[^\]\\]*[^\\\]]\|", f"{name}: {line}")

    def test_facts_kept_in_frontmatter_are_not_repeated_in_the_body(self):
        for name, banned in NOT_IN_BODY.items():
            _, _, body = split(name)
            for text in banned:
                self.assertNotIn(text, body, f"{name}: {text}")

    def test_no_dash_separators_in_prose(self):
        for path in DIR.glob("*.md"):
            self.assertNotIn("\u2014", path.read_text(encoding="utf-8"), path.name)

    def test_templates_do_not_claim_audit_checks_it_does_not_make(self):
        for name in EXPECTED_KEYS:
            text, _, _ = split(name)
            self.assertNotIn("run InvestingOS `audit`", text, name)
        self.assertIn("does not read Markdown notes", README)


class EngineAgreementTests(unittest.TestCase):
    def test_status_vocabulary_matches_engine_constants(self):
        for status in CLAIM_STATUSES:
            self.assertIn(status, README)
        for status in SOURCE_LIBRARY_STATUSES:
            self.assertIn(status, README)

    def test_exported_notes_use_template_keys_and_documented_values(self):
        project = create_project("Example")
        node = add_node(project, "Node", "Description")
        source = add_source(project, "Source", url="https://example.com", author="A", accessed="2026-01-01", locator="p. 1")
        add_claim(project, "A claim", sources=[source["id"]], nodes=[node["id"]])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "export"
            export(project, out)
            node_front = frontmatter_of(out / f"{node['id']}.md")
            source_front = frontmatter_of(out / f"{source['id']}.md")
        self.assertLessEqual(set(node_front), EXPECTED_KEYS["knowledge-node"])
        self.assertLessEqual(set(source_front), EXPECTED_KEYS["source-record"])
        _, node_template, _ = split("knowledge-node")
        self.assertEqual(node_front["status"], node_template["status"].strip('"'))
        _, source_template, _ = split("source-record")
        for key in ("library_status", "review_status"):
            self.assertEqual(source_front[key], source_template[key].strip('"'))


if __name__ == "__main__":
    unittest.main()
