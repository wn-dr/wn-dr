"""Testes de regressão para as falhas que a validação precisa detectar."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generate_readme_icons as generator
import validate_readme_assets as validator

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path id="p" d="M0 0h1"/></svg>'


class AssetValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".icon-test-", dir=validator.ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "assets/python.svg"
        self.image.parent.mkdir()
        self.image.write_text(SVG, encoding="utf-8")

    def readme(self, content):
        (self.root / "README.md").write_text(content, encoding="utf-8")
        return validator.validate(self.root)

    def test_html_markdown_and_external_images(self):
        self.assertEqual(self.readme('<p><img src="assets/python.svg" alt="Python" /></p>\n![Python](assets/python.svg)\n![Externa](https://example.com/a.svg)'), [])

    def test_reference_and_parenthesized_filename(self):
        (self.image.parent / "data (1).svg").write_text(SVG, encoding="utf-8")
        self.assertEqual(self.readme('![Python][py]\n\n[py]: assets/python.svg\n\n![Dados](<assets/data (1).svg>)\n![Dados](assets/data%20(1).svg)'), [])

    def test_code_examples_are_ignored(self):
        self.assertEqual(self.readme('```html\n<img src="absent.svg">\n```\n`![Exemplo](absent.svg)`'), [])

    def test_missing_asset(self):
        self.assertIn("Missing: missing.svg", self.readme('![Python](missing.svg)'))

    def test_exit_codes_and_messages(self):
        for source, code, message in [('assets/python.svg', 0, 'README asset validation: OK'), ('missing.svg', 1, 'README asset validation: FAILED')]:
            self.readme(f'![Python]({source})')
            output = io.StringIO()
            with patch('sys.argv', ['validate', '--root', str(self.root)]), contextlib.redirect_stdout(output):
                self.assertEqual(validator.main(), code)
            self.assertIn(message, output.getvalue())

    def test_case_mismatch_on_every_platform(self):
        self.assertTrue(any('Case mismatch' in e for e in self.readme('![Python](Assets/Python.svg)')))

    def test_missing_alt(self):
        self.assertTrue(self.readme('<img src="assets/python.svg">'))

    def test_unclosed_html(self):
        self.assertTrue(self.readme('<p><img src="assets/python.svg" alt="Python">'))

    def test_reference_missing(self):
        self.assertTrue(self.readme('![Python][missing]'))

    def test_path_escape(self):
        self.assertTrue(self.readme('![Python](../outside.svg)'))

    def test_unsafe_scheme(self):
        self.assertTrue(self.readme('![Python](javascript:alert)'))

    def test_viewbox_and_xml(self):
        for bad in [SVG.replace(' viewBox="0 0 64 64"', ''), SVG[:-6], SVG.replace('0 0 64 64', '0 0 -1 64')]:
            with self.subTest(bad=bad):
                self.image.write_text(bad, encoding="utf-8")
                self.assertTrue(validator.validate_svg(self.image))

    def test_active_svg_content(self):
        for bad in ['<script>alert(1)</script>', '<g onload="alert(1)"/>', '<foreignObject/>', '<set attributeName="href" to="https://example.com"/>']:
            with self.subTest(bad=bad):
                self.image.write_text(SVG.replace('</svg>', bad+'</svg>'), encoding='utf-8')
                self.assertTrue(validator.validate_svg(self.image))

    def test_svg_external_and_broken_references(self):
        for bad in ['<use href="#missing"/>', '<image href="https://example.com/image.png"/>', '<g fill="url(https://example.com/a.svg)"/>', '<style>@import "external.css";</style>']:
            with self.subTest(bad=bad):
                self.image.write_text(SVG.replace('</svg>', bad+'</svg>'), encoding='utf-8')
                self.assertTrue(validator.validate_svg(self.image))

    def test_svg_valid_internal_reference(self):
        self.image.write_text(SVG.replace('</svg>', '<use href="#p"/></svg>'), encoding='utf-8')
        self.assertEqual(validator.validate_svg(self.image), [])

    def test_dtd_rejected(self):
        self.image.write_text('<!DOCTYPE svg [<!ENTITY a "x">]>'+SVG, encoding='utf-8')
        self.assertTrue(validator.validate_svg(self.image))

    def test_generator_preserves_brand_and_is_deterministic(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        entries = [dict(slug='python', kind='brand'), dict(slug='sql', name='SQL', label='SQL', accent='#276A9A', kind='custom')]
        (scripts / 'icon_manifest.json').write_text(json.dumps(entries), encoding='utf-8')
        original = self.image.read_bytes()
        with patch.object(generator, 'ROOT', self.root), patch.object(generator, 'ICONS', self.image.parent), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.generate(), 0)
            self.assertEqual(generator.generate(check=True), 0)
            generated = (self.image.parent / 'sql.svg').read_bytes()
            self.assertEqual(generator.generate(), 0)
            self.assertEqual((self.image.parent / 'sql.svg').read_bytes(), generated)
            self.assertEqual(self.image.read_bytes(), original)
            (self.image.parent / 'sql.svg').write_text('outdated', encoding='utf-8')
            self.assertEqual(generator.generate(check=True), 1)


if __name__ == '__main__':
    unittest.main()
