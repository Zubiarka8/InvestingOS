"""Allocate separate, user-organized folders for imported source files."""
from pathlib import Path
import re
from uuid import uuid4


_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


def allocate_import(root, mode, source, category=''):
    if mode not in {'local', 'web', 'youtube'}:
        raise ValueError('Unknown source type')
    pieces = category.split('/') if category else []
    for part in pieces:
        if (not part or len(part) > 80 or not part[0].isalnum() or part[-1] == ' '
                or not all(char.isalnum() or char in ' _-' for char in part)
                or part.upper() in _RESERVED):
            raise ValueError('Topic folders must use letters, numbers, spaces, hyphens or underscores, separated by /')
    kind = ('pdf' if Path(source).suffix.lower() == '.pdf' else 'documents') if mode == 'local' else mode
    # Use a portable, bounded label; identity comes from a random identifier.
    label = Path(source).stem if mode == 'local' else mode
    label = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')[:48] or 'source'
    identifier = uuid4().hex
    base = Path(root).expanduser().resolve()
    parent = base.joinpath(kind, *pieces)
    parent.mkdir(parents=True, exist_ok=True)
    folder = parent / (label + '-' + identifier)
    folder.mkdir(exist_ok=False)
    return folder / 'extracted.md'
