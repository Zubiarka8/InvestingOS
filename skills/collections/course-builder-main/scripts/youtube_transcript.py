"""Fetch one YouTube transcript; adapted from Course Builder's Bash helper.

Copyright (c) 2026 Klaus Heringer. See the collection's MIT LICENSE.
Exit 0 on success, 1 for unavailable transcripts, and 2 for blocked requests
or missing dependencies. No dependencies are installed automatically.
"""
import argparse
import re
import sys
from urllib.parse import parse_qs, urlsplit


def video_id(value):
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        return value
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        raise ValueError('provide a YouTube HTTPS URL or 11-character video ID')
    host = (parsed.hostname or '').lower()
    if host == 'youtu.be':
        candidate = parsed.path.strip('/')
    elif host in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
        parts = parsed.path.strip('/').split('/')
        candidate = parts[1] if len(parts) == 2 and parts[0] in {'shorts', 'embed', 'live'} else parse_qs(parsed.query).get('v', [''])[0]
    else:
        raise ValueError('URL must be from YouTube')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate):
        raise ValueError('invalid YouTube video ID')
    return candidate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', help='YouTube URL or video ID')
    parser.add_argument('languages', nargs='*', help='Preferred language codes in order (default: en)')
    args = parser.parse_args(argv)
    try:
        identifier = video_id(args.video)
        languages = args.languages or ['en']
        if any(not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', lang) for lang in languages):
            raise ValueError('invalid language code')
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, RequestBlocked, IpBlocked, CouldNotRetrieveTranscript
        from requests import RequestException
    except ImportError:
        print('Install youtube-transcript-api 1.x in the active Python environment.', file=sys.stderr)
        return 2
    try:
        transcript = YouTubeTranscriptApi().fetch(identifier, languages=languages)
        for segment in transcript:
            print(segment.text)
        return 0
    except (RequestBlocked, IpBlocked, RequestException) as exc:
        print(f'YouTube request unavailable: {exc}', file=sys.stderr)
        return 2
    except CouldNotRetrieveTranscript as exc:
        print(f'Transcript unavailable: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
