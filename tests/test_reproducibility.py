"""Rendering regression tests using the existing synthetic and legacy fixtures."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import test_editorial
from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]


class ReproducibilityTests(unittest.TestCase):
    def test_svg_bytes_are_stable_in_both_renderers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editorial, _ = test_editorial.EditorialTests().fixture(root)
            legacy = ROOT / 'tests/fixtures/legacy/posts/ecb-2022-2025.json'
            for name, spec in [('editorial', editorial), ('legacy', legacy)]:
                with self.subTest(renderer=name):
                    first, second = root / name / 'first', root / name / 'second'
                    render_post(spec, first, ROOT / 'brand/palette-a.json')
                    render_post(spec, second, ROOT / 'brand/palette-a.json')
                    for path in sorted(first.glob('*.svg')):
                        self.assertEqual(
                            hashlib.sha256(path.read_bytes()).hexdigest(),
                            hashlib.sha256((second / path.name).read_bytes()).hexdigest(),
                            f'{name}/{path.name} changed between identical renders',
                        )
