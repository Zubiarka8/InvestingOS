"""Render recorded source locations as safe Markdown links."""
import os
from pathlib import Path
from urllib.parse import quote, urlsplit


def web_link(url):
    parts = urlsplit(url)
    if parts.scheme not in ('https', 'http') or not parts.hostname or parts.username is not None or parts.password is not None:
        return None
    return quote(url, safe=':/?&=%#@+;,~-._')


def local_link(source, destination):
    try:
        relative = os.path.relpath(source, Path(destination).parent)
        return quote(Path(relative).as_posix(), safe='/.-_~')
    except ValueError:
        return Path(source).resolve().as_uri()


def imported_source_section(*, url=None, source=None, destination=None, project=None):
    target = web_link(url) if url else local_link(source, destination)
    if not target:
        raise ValueError('invalid source URL')
    lines = ['', '## Sources', '', '- [Original source](' + target + ')', '',
             'Source content is not automatically verified.']
    if project:
        title = str(project.get('title', '')).replace('\r', ' ').replace('\n', ' ')
        lines.extend(['', '## InvestingOS project', '', '- Name: ' + title,
                      '- Project ID: `' + str(project.get('id', '')) + '`'])
    return '\n'.join(lines) + '\n'
