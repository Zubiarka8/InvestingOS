import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ["record-keeper", "prospector", "follow-up", "sales-coach", "contract-writer", "researcher",
          "scheduler", "pipeline", "proposal-writer", "win-back", "forecaster"]
ABOUT = ("11 Claude skills that run your whole sales team: find leads, cold outreach, follow-ups, "
         "call coaching and contracts. Free.")
# skills that can send, book or sign something on the user's behalf carry the consent rule
SENDS = ["prospector", "follow-up", "contract-writer", "scheduler", "proposal-writer", "win-back"]


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), text


def every_text_file():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "closer")]
        for f in files:
            if f.endswith((".md", ".py", ".json", ".csv", ".txt")) or f == "LICENSE":
                yield os.path.join(base, f)


class Repo(unittest.TestCase):
    def test_root_matches_the_reel(self):
        root = sorted(d for d in os.listdir(ROOT) if d not in (".git", ".gitignore", ".DS_Store"))
        self.assertEqual(root, sorted([".claude-plugin", "LICENSE", "README.md"] + SKILLS))

    def test_frontmatter_name_and_description(self):
        for s in SKILLS:
            fm, text = frontmatter(os.path.join(ROOT, s, "SKILL.md"))
            self.assertIn("name: %s\n" % s, fm + "\n", s)
            self.assertRegex(fm, r"description: ", s)
            self.assertGreater(len(fm), 300, "%s description is too thin" % s)
            self.assertGreater(len(text.splitlines()), 60, s)
            self.assertIn("${CLAUDE_SKILL_DIR}", text, s)
            self.assertIn("## Consent and truth", text, s)

    def test_every_tool_named_in_a_skill_exists(self):
        for s in SKILLS:
            _, text = frontmatter(os.path.join(ROOT, s, "SKILL.md"))
            for script in set(re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w.-]+\.py)", text)):
                self.assertTrue(os.path.exists(os.path.join(ROOT, s, script)), "%s/%s" % (s, script))

    def test_sending_skills_ask_first(self):
        for s in SENDS:
            _, text = frontmatter(os.path.join(ROOT, s, "SKILL.md"))
            low = " ".join(text.lower().split())
            self.assertIn("reply yes or no", low, s)
            self.assertRegex(low, r"never (send|sends|books|signs)", s)

    def test_plugin_manifests(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json")) as fh:
            plugin = json.load(fh)
        self.assertEqual(plugin["name"], "closer-skill")
        self.assertEqual(plugin["description"], ABOUT)
        self.assertEqual(plugin["skills"], "./")
        with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")) as fh:
            market = json.load(fh)
        self.assertEqual(market["name"], "closer-skill")
        self.assertEqual(market["plugins"][0]["name"], "closer-skill")

    def test_readme_carries_the_reel_copy(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = " ".join(fh.read().split())
        self.assertTrue(readme.startswith("# The Closer skill"))
        for line in ("Eleven Claude skills that run your whole sales team.",
                     "https://github.com/Jakeschincariol/closer-skill install skill",
                     "/plugin marketplace add Jakeschincariol/closer-skill",
                     "/plugin install closer-skill@closer-skill",
                     "## Fine print"):
            self.assertIn(line, readme)
        for s in SKILLS:
            self.assertIn("`%s`" % s, readme, s)

    def test_no_em_dashes_and_no_personal_email(self):
        for path in every_text_file():
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            rel = os.path.relpath(path, ROOT)
            self.assertNotIn("\u2014", text, rel)
            self.assertNotIn("jakeschincariol" + "@" + "gmail.com", text, rel)


if __name__ == "__main__":
    unittest.main()
