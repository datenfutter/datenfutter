"""Build canonical projects in disposable workspaces without changing final posts."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .render import _publish, render_post

NAME = re.compile(r'[a-z0-9][a-z0-9_-]*')


def select_projects(root, project=None, *, all_projects=False):
    root = Path(root).resolve()
    if bool(project) == bool(all_projects):
        raise ValueError('Choose one project or --all.')
    names = (sorted({p.parents[2].name for p in (root / 'projects').glob('*/specs/*/*.json')})
             if all_projects else [project])
    if not names:
        raise ValueError('No canonical project specifications found.')
    for name in names:
        if not NAME.fullmatch(name):
            raise ValueError(f'Invalid project name: {name!r}.')
        path = root / 'projects' / name
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f'Project not found or is a symlink: {name}.')
        post_specs(path)
    return names


def post_specs(project):
    specs = []
    for path in sorted(Path(project).glob('specs/*/*.json')):
        language, post = path.parent.name, path.stem
        if language not in ('de', 'en') or not NAME.fullmatch(post):
            raise ValueError(f'Invalid canonical specification path: {path}.')
        spec = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(spec, dict):
            raise ValueError(f'Specification must be a JSON object: {path}.')
        if spec.get('schema_version') not in ('0.3', '0.4') or spec.get('language') != language:
            raise ValueError(f'Specification must use schema 0.4 and match its language folder: {path}.')
        specs.append((path, language, post, spec))
    if not specs:
        raise ValueError(f'No canonical specifications in {project}.')
    return specs


def _preview_destination(path, build):
    if not path.resolve().is_relative_to(build.resolve()):
        raise ValueError('Preview destination escapes build/.')
    current = path
    while current != build:
        if current.is_symlink():
            raise ValueError('Preview destinations must not contain symlinks.')
        current = current.parent


def build_projects(root, names):
    root = Path(root).resolve()
    build = root / 'build'
    if build.is_symlink():
        raise ValueError('build/ must not be a symlink.')
    build.mkdir(exist_ok=True)
    pending = []
    with tempfile.TemporaryDirectory(prefix='.work-', dir=build) as temporary:
        workspace = Path(temporary)
        shutil.copytree(root / 'brand', workspace / 'brand')
        for name in names:
            select_projects(root, name)
            project = root / 'projects' / name
            staged = workspace / 'projects' / name

            def ignore(directory, entries):
                excluded = {'__pycache__', '.venv', '.git'}
                if Path(directory) == project:
                    excluded.add('posts')
                return set(entries) & excluded

            shutil.copytree(project, staged, ignore=ignore)
            prepare = staged / 'prepare.py'
            if prepare.exists():
                env = dict(os.environ)
                env['PYTHONPATH'] = str(root) + os.pathsep + env.get('PYTHONPATH', '')
                result = subprocess.run([sys.executable, str(prepare)], cwd=workspace,
                                        env=env, capture_output=True, text=True)
                if result.returncode:
                    detail = result.stderr.strip().splitlines()
                    raise ValueError(f'Preparation failed for {name}: '
                                     f'{detail[-1] if detail else result.returncode}')
            for spec_path, language, post, spec in post_specs(staged):
                out = staged / 'posts' / language / post
                files = render_post(spec_path, out, workspace / 'brand/brand.json')
                destination = build / 'projects' / name / 'posts' / language / post
                _preview_destination(destination, build)
                pending.append((out, destination, files, spec['id'], language))
        # Finish every render before replacing any previous preview.
        published = []
        for staged, destination, files, post_id, language in pending:
            published.extend(_publish(staged, destination, files, post_id, language=language))
        return published
