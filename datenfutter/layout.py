"""Check current output locations without discarding historical source evidence."""
import os
import re
from pathlib import Path

from .projects import NAME, post_specs

OBSOLETE = re.compile(r'(?:archives?|backups?|exports?|outputs?|previews?)(?:[-_].*)?', re.I)
DERIVATIVES = {'.png', '.svg', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.zip'}


def _check_project_files(project):
    for directory, folders, files in os.walk(project):
        directory = Path(directory)
        for name in folders + files:
            path = directory / name
            if path.is_symlink():
                raise ValueError(f'Project paths must not be symlinks: {path}.')
        # Source snapshots may be dated, archived, or images. Do not inspect or
        # reinterpret original evidence as plot revisions.
        if directory == project / 'sources':
            folders[:] = [name for name in folders if name != 'raw']
        if directory == project:
            folders[:] = [name for name in folders if name != 'posts']
        folders[:] = [name for name in folders if name != '__pycache__']
        for name in folders:
            if OBSOLETE.fullmatch(name):
                raise ValueError(f'Obsolete output directory: {directory / name}. Use ignored build/.')
        for name in files:
            path = directory / name
            if path.suffix.lower() in DERIVATIVES:
                raise ValueError(f'Artifact outside canonical posts or sources/raw: {path}.')
            if name.endswith(('~', '.bak', '.old')):
                raise ValueError(f'Backup file outside raw evidence: {path}.')


def _check_posts(project, specifications):
    posts = project / 'posts'
    if not posts.exists():
        return 0
    if not posts.is_dir():
        raise ValueError(f'Current posts must be a directory: {posts}.')
    count = 0
    for language in sorted(posts.iterdir()):
        if language.is_symlink() or not language.is_dir() or language.name not in ('de', 'en'):
            raise ValueError(f'Invalid current language directory: {language}.')
        for post in sorted(language.iterdir()):
            key = (language.name, post.name)
            if post.is_symlink() or not post.is_dir() or key not in specifications:
                raise ValueError(f'Current post has no canonical specification: {post}.')
            slides = specifications[key]['slides']
            expected = {'caption.md', 'alt-text.md', 'manifest.json'}
            expected.update(f'{i:02d}.{ext}' for i in range(1, len(slides) + 1)
                            for ext in ('png', 'svg'))
            paths = list(post.iterdir())
            if any(path.is_symlink() or not path.is_file() for path in paths):
                raise ValueError(f'Current post contains a symlink or nested directory: {post}.')
            actual = {path.name for path in paths}
            if actual != expected:
                missing, extra = sorted(expected - actual), sorted(actual - expected)
                raise ValueError(f'Incomplete or unmanaged current output set: {post}; '
                                 f'missing={missing}, extra={extra}.')
            count += 1
    return count


def check_layout(root):
    """Return project/post counts; this is a layout check, not reproduction."""
    root = Path(root).resolve()
    if not (root / 'brand/brand.json').is_file():
        raise ValueError(f'Not a Datenfutter root: {root}.')
    for path in root.iterdir():
        if (path.name == 'posts' or OBSOLETE.fullmatch(path.name)
                or (path.is_file() and path.suffix.lower() in DERIVATIVES)):
            raise ValueError(f'Noncanonical root artifact: {path}. Use projects/ or ignored build/.')
    projects = root / 'projects'
    if projects.is_symlink():
        raise ValueError('projects/ must not be a symlink.')
    if not projects.exists():
        return 0, 0
    count, current_posts = 0, 0
    for project in sorted(projects.iterdir()):
        if project.is_symlink() or not project.is_dir() or not NAME.fullmatch(project.name):
            raise ValueError(f'Invalid project directory: {project}.')
        _check_project_files(project)
        specifications = {}
        if (project / 'specs').exists():
            for path in (project / 'specs').rglob('*.json'):
                relative = path.relative_to(project / 'specs')
                if len(relative.parts) != 2:
                    raise ValueError(f'Noncanonical specification: {path}.')
            specifications = {(language, post): spec
                              for _, language, post, spec in post_specs(project)}
            for key, spec in specifications.items():
                if not isinstance(spec.get('slides'), list) or not 1 <= len(spec['slides']) <= 10:
                    raise ValueError(f'Expected one to ten slides for {project.name}/{key}.')
        current_posts += _check_posts(project, specifications)
        count += 1
    return count, current_posts
