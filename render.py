#!/usr/bin/env python3
"""Usage: python render.py posts/ecb-2022-2025.json --out outputs/ecb-2022-2025"""
import argparse
from pathlib import Path
from datenfutter.render import render_post


def main():
    parser = argparse.ArgumentParser(description='Render a datenfutter chart post.')
    parser.add_argument('spec', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--brand', type=Path, default=Path(__file__).parent / 'brand/brand.json')
    args = parser.parse_args()
    try:
        for path in render_post(args.spec, args.out, args.brand):
            print(path)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        parser.exit(2, f'Render failed: {exc}\n')


if __name__ == '__main__':
    main()
