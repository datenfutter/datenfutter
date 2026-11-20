"""Reproduce this project's current tables and posts from raw evidence offline.

Run from any directory with ``python projects/unemployment-de-ch-dk-no/verify.py``.
Preparation starts with sources and prepare.py only. Existing tables, chart
specifications and posts are unavailable until the raw-to-table gate passes.
All generated files live in a disposable directory under ignored build/.
"""
from contextlib import ExitStack, chdir
import hashlib
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from datenfutter.projects import post_specs
from datenfutter.render import render_post


def _deny_network(*args, **kwargs):
    raise RuntimeError('Network access is disabled during offline verification.')


def _files(directory):
    """Read the complete regular-file set; reject redirected comparisons."""
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError(f'Verification paths must not be symlinks: {directory}.')
    if not directory.is_dir():
        raise ValueError(f'Missing verification directory: {directory}.')
    files = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Verification paths must not be symlinks: {path}.')
        if path.is_file():
            files[path.relative_to(directory)] = path
        elif not path.is_dir():
            raise ValueError(f'Expected a regular file or directory: {path}.')
    return files


def _compare(rebuilt, current, label):
    expected, actual = _files(rebuilt), _files(current)
    if not expected or not actual:
        raise ValueError(f'No {label} outputs to compare; empty output sets fail.')
    differences = []
    for path in sorted(expected.keys() - actual.keys()):
        differences.append(f'missing: {label}/{path}')
    for path in sorted(actual.keys() - expected.keys()):
        differences.append(f'extra: {label}/{path}')
    for path in sorted(expected.keys() & actual.keys()):
        rebuilt_hash = hashlib.sha256(expected[path].read_bytes()).digest()
        current_hash = hashlib.sha256(actual[path].read_bytes()).digest()
        if rebuilt_hash != current_hash:
            differences.append(f'changed: {label}/{path}')
    if differences:
        raise ValueError('Current files do not match the raw-evidence rebuild:\n'
                         + '\n'.join(differences))
    return len(expected)


def verify(project_dir=None):
    """Verify every derived byte and current post without promoting outputs."""
    project = Path(project_dir) if project_dir is not None else Path(__file__).parent
    if project.is_symlink():
        raise ValueError('The project directory must not be a symlink.')
    project = project.resolve()
    root = project.parents[1]
    _files(project / 'sources')
    prepare = project / 'prepare.py'
    if prepare.is_symlink() or not prepare.is_file():
        raise ValueError('A regular project prepare.py is required.')
    build = root / 'build'
    if build.is_symlink():
        raise ValueError('build/ must not be a symlink.')
    build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.verify-unemployment-', dir=build) as temporary:
        workspace = Path(temporary)
        staged = workspace / 'projects' / project.name
        staged.mkdir(parents=True)
        shutil.copytree(project / 'sources', staged / 'sources')
        shutil.copyfile(prepare, staged / 'prepare.py')
        # This initial workspace deliberately has no processed data, specs,
        # current posts or brand files. Do not replace it with a project copy.
        with ExitStack() as offline:
            for name in ('socket.socket.connect', 'socket.socket.connect_ex',
                         'socket.create_connection'):
                offline.enter_context(patch(name, _deny_network))
            offline.enter_context(chdir(workspace))
            namespace = runpy.run_path(str(staged / 'prepare.py'))
            prepare_function = namespace.get('prepare')
            if not callable(prepare_function):
                raise ValueError('prepare.py must expose prepare(project_dir).')
            prepare_function(staged)
            derived_count = _compare(staged / 'data/processed',
                                     project / 'data/processed', 'data/processed')

            _files(project / 'specs')
            _files(root / 'brand')
            shutil.copytree(project / 'specs', staged / 'specs')
            shutil.copytree(root / 'brand', workspace / 'brand')
            specifications = post_specs(staged)
            for spec_path, language, post, _ in specifications:
                render_post(spec_path, staged / 'posts' / language / post,
                            workspace / 'brand/brand.json')
            output_count = _compare(staged / 'posts', project / 'posts', 'posts')
    return {'derived_files': derived_count, 'posts': len(specifications),
            'output_files': output_count}


def main():
    try:
        result = verify()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f'Offline verification failed: {exc}', file=sys.stderr)
        return 1
    print('Offline raw-evidence reproduction passed: '
          f"{result['derived_files']} derived files and "
          f"{result['output_files']} output files across {result['posts']} post(s) "
          'match current files byte for byte. Current files were not changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
