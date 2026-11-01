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


def imported_source_section(*, url=None, source=None, destination=None):
    target = web_link(url) if url else local_link(source, destination)
    if not target:
        raise ValueError('invalid source URL')
    return '\n\n## Sources\n\n- [Original source](' + target + ')\n\nSource content is not automatically verified.\n'
