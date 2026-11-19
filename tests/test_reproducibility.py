"""Rendering regression tests using the existing synthetic and legacy fixtures."""
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import test_editorial
from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]


class ReproducibilityTests(unittest.TestCase):
    def test_complete_outputs_match_in_relocated_checkouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            left, right = Path(tmp) / 'left', Path(tmp) / 'right'
            left.mkdir()
            shutil.copytree(ROOT / 'brand', left / 'brand')
            shutil.copytree(ROOT / 'tests/fixtures/legacy', left / 'legacy')
            (left / 'editorial').mkdir()
            path, spec = test_editorial.EditorialTests().fixture(left / 'editorial')
            spec['logo_file'] = '../brand/df-circle-white.png'
            path.write_text(json.dumps(spec, ensure_ascii=False))
            shutil.copytree(left, right)
            for relative in ['editorial/post.json', 'legacy/posts/ecb-2022-2025.json']:
                with self.subTest(spec=relative):
                    outputs = []
                    for index, checkout in enumerate([left, right]):
                        out = checkout / f'output-{index}' / Path(relative).parent.name
                        render_post(checkout / relative, out, checkout / 'brand/palette-a.json')
                        outputs.append({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in out.iterdir()})
                    self.assertEqual(outputs[0], outputs[1])

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
