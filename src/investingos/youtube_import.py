"""Import available YouTube captions as local Markdown with provenance."""
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from .core import add_source
from .knowledge_tools import _hash
from .source_links import imported_source_section


def import_youtube(project, url, destination):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'}
            or parsed.username is not None or parsed.password is not None or parsed.port is not None):
        raise ValueError('provide an HTTPS YouTube video URL')
    destination = Path(destination).resolve()
    if destination.suffix.lower() != '.md':
        raise ValueError('destination must be a Markdown file')
    captions = destination.with_suffix('.vtt')
    if destination.exists() or captions.exists():
        raise FileExistsError('Markdown or caption destination already exists')
    executable = shutil.which('yt-dlp')
    if not executable:
        raise ValueError('yt-dlp is required; see docs/research-tools.md')
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([executable, '--ignore-config', '--no-playlist', '--no-overwrites', '--skip-download',
                        '--write-subs', '--write-auto-subs', '--sub-format', 'vtt', '--sub-langs', 'en.*,es.*',
                        '-P', tmp, '-o', 'captions.%(ext)s', '--', url], check=True, capture_output=True, text=True)
        files = sorted(Path(tmp).glob('captions.*.vtt'))
        if not files:
            raise ValueError('no English or Spanish captions available; transcription is a separate step')
        raw = files[0].read_text(encoding='utf-8')
    with captions.open('x', encoding='utf-8') as handle:
        handle.write(raw)
    try:
        with destination.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write('# YouTube captions\n\nSource: ' + escape(url) + '\n\nCaptions may be automatically generated; verify against the video.\n\n')
            handle.write('```vtt\n' + raw.replace('```', '` ` `') + '\n```\n')
            handle.write(imported_source_section(url=url, project=project))
    except Exception:
        captions.unlink()
        raise
    source = add_source(project, 'YouTube captions', url=url, media_type='youtube')
    source.update(local_path=str(captions), extracted_path=str(destination), sha256=_hash(captions))
    return source


def search_youtube(query, limit=5):
    import json
    import re
    if not isinstance(query, str) or not query.strip() or not 1 <= limit <= 20:
        raise ValueError('provide a query and a limit between 1 and 20')
    executable = shutil.which('yt-dlp')
    if not executable:
        raise ValueError('yt-dlp is required; see docs/research-tools.md')
    result = subprocess.run([executable, '--ignore-config', '--flat-playlist', '--dump-json',
                             '--', f'ytsearch{limit}:{query.strip()}'], check=True, capture_output=True, text=True)
    videos = []
    for line in result.stdout.splitlines():
        item = json.loads(line)
        video_id = item.get('id', '')
        if isinstance(video_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            videos.append({'title': item.get('title', ''), 'url': 'https://www.youtube.com/watch?v=' + video_id})
    return videos
