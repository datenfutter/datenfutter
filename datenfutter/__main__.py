"""Command-line entrypoint for offline project work."""
import argparse
import sys
from pathlib import Path

from .projects import build_projects, select_projects


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m datenfutter')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('build', help='Prepare and render into ignored build/.')
    build.add_argument('project', nargs='?')
    build.add_argument('--all', action='store_true', dest='all_projects')
    args = parser.parse_args(argv)
    try:
        names = select_projects(args.root, args.project, all_projects=args.all_projects)
        files = build_projects(args.root, names)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(f'Built {len(names)} project(s), {len(files)} files in {args.root.resolve() / "build"}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
