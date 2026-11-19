"""Command-line entrypoint for offline project work."""
import argparse
import sys
from pathlib import Path

from .projects import build_projects, check_projects, select_projects


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m datenfutter')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command', required=True)
    for command, help_text in [('build', 'Prepare and render into ignored build/.'),
                               ('check', 'Rebuild and compare all current output files.')]:
        action = commands.add_parser(command, help=help_text)
        action.add_argument('project', nargs='?')
        action.add_argument('--all', action='store_true', dest='all_projects')
    args = parser.parse_args(argv)
    try:
        names = select_projects(args.root, args.project, all_projects=args.all_projects)
        if args.command == 'build':
            files = build_projects(args.root, names)
            print(f'Built {len(names)} project(s), {len(files)} files in {args.root.resolve() / "build"}.')
        else:
            checked, drafts = check_projects(args.root, names, allow_drafts=args.all_projects)
            print(f'Current outputs match for {len(checked)} project(s).')
            if drafts:
                print('Draft-only projects skipped: ' + ', '.join(drafts))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
