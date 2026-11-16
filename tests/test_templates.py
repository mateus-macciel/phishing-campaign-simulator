"""Safety and quality guards for the e-mail templates.

These tests exist so the templates can never drift into something harmful:
no forms or scripts (nothing collects data), only reserved `.test` domains.
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from catalog import TEMPLATES  # noqa: E402
from render_templates import render_all  # noqa: E402

TEMPLATE_FILES = sorted((ROOT / "templates").glob("*.html"))


class TemplateSafety(unittest.TestCase):
    def test_templates_exist(self):
        self.assertEqual(len(TEMPLATE_FILES), len(TEMPLATES) + 1)  # + landing page
        for t in TEMPLATES:
            self.assertTrue((ROOT / "templates" / t["file"]).exists(), t["file"])

    def test_no_forms_inputs_or_scripts(self):
        for f in TEMPLATE_FILES:
            html = f.read_text(encoding="utf-8").lower()
            for tag in ("<form", "<input", "<script", "<iframe", "type=\"password\""):
                self.assertNotIn(tag, html, f"{f.name} contains {tag}")

    def test_only_reserved_test_domains_everywhere(self):
        sources = [(f.name, f.read_text(encoding="utf-8")) for f in TEMPLATE_FILES]
        for t in TEMPLATES:
            sources.append((t["template_id"], t["link"] + " " + t["sender_address"]))
        for name, text in sources:
            hosts = re.findall(r"https?://([^/\s\"'<>]+)", text)
            hosts += re.findall(r"[\w.+-]+@([\w.-]+)", text)
            for host in hosts:
                self.assertTrue(host.endswith(".test"), f"{name}: {host} is not a .test domain")

    def test_templates_have_placeholders_and_red_flags(self):
        for t in TEMPLATES:
            html = (ROOT / "templates" / t["file"]).read_text(encoding="utf-8")
            self.assertIn("{{nome}}", html)
            self.assertIn("{{link}}", html)
            self.assertIn("MODELO DE TREINAMENTO", html)
            self.assertGreaterEqual(len(t["red_flags"]), 4)

    def test_render_replaces_every_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in render_all(ROOT / "templates", Path(tmp)):
                self.assertNotIn("{{", path.read_text(encoding="utf-8"), path.name)


if __name__ == "__main__":
    unittest.main()
