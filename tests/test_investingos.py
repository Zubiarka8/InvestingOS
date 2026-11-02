import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from investingos.core import add_edge, add_node, add_view, audit, create_project
from investingos.export import export
from investingos.storage import load, save


class InvestingOSTests(unittest.TestCase):
    def test_three_domains_and_roundtrip(self):
        for subject in ("History", "Sport", "Psychology"):
            with self.subTest(subject=subject), tempfile.TemporaryDirectory() as tmp:
                p = create_project(subject)
                nodes = [add_node(p, subject + str(i)) for i in range(8)]
                first = add_view(p, "Chronological")
                second = add_view(p, "Conceptual")
                for a, b in zip(nodes, nodes[1:]):
                    add_edge(p, a["id"], b["id"], "contains", first["id"])
                add_edge(p, nodes[0]["id"], nodes[7]["id"], "contains", second["id"])
                old = copy.deepcopy(p)
                extra = add_node(p, "Expansion")
                add_edge(p, nodes[1]["id"], extra["id"], "contains", first["id"])
                self.assertEqual(p["nodes"][:8], old["nodes"])
                self.assertEqual(p["edges"][:8], old["edges"])
                path = Path(tmp) / "project.json"
                save(p, path)
                self.assertEqual(load(path), p)
                with self.assertRaises(FileExistsError):
                    save(p, path)
                out = Path(tmp) / "vault"
                export(p, out)
                text = (out / (nodes[0]["id"] + ".md")).read_text()
                self.assertIn('status: "unverified"', text)
                self.assertIn("[[" + nodes[1]["id"], text)
                self.assertIn("Conceptual", (out / "index.md").read_text())
                with self.assertRaises(FileExistsError):
                    export(p, out)

    def test_cycles_and_missing_references(self):
        p = create_project("Test")
        a, b = add_node(p, "A"), add_node(p, "B")
        add_edge(p, a["id"], b["id"], "requires")
        with self.assertRaises(ValueError):
            add_edge(p, b["id"], a["id"], "requires")
        with self.assertRaises(ValueError):
            add_edge(p, a["id"], "missing", "related_to")
        p["edges"][0]["target"] = "missing"
        self.assertTrue(any("broken edge" in e for e in audit(p)))

    def test_duplicates_and_malformed(self):
        p = create_project("Test")
        add_node(p, "Same")
        add_node(p, " same ")
        self.assertTrue(any("duplicate title" in e for e in audit(p)))
        self.assertTrue(audit({"schema_version": 1}))

    def test_shared_skill(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "skills/investingos/SKILL.md").resolve()
        self.assertTrue(source.read_text().startswith("---\nname: InvestingOS\n"))


if __name__ == "__main__":
    unittest.main()
