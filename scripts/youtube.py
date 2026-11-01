"""Download one YouTube video's captions or media with an installed yt-dlp."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("captions", "video"))
    parser.add_argument("url", help="HTTPS YouTube video URL")
    parser.add_argument("destination", type=Path, help="Existing output directory")
    args = parser.parse_args()
    try:
        url = urlsplit(args.url)
        valid_url = (url.scheme == "https" and url.hostname in
                     {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"} and
                     url.username is None and url.password is None and url.port is None)
    except ValueError:
        valid_url = False
    if not valid_url:
        parser.error("provide an HTTPS YouTube video URL")
    if not args.destination.is_dir():
        parser.error("output directory must already exist")
    executable = shutil.which("yt-dlp")
    if not executable:
        parser.error("yt-dlp is required; see docs/research-tools.md")
    command = [executable, "--ignore-config", "--no-playlist", "--no-overwrites"]
    if args.mode == "captions":
        command += ["--skip-download", "--write-subs", "--write-auto-subs",
                    "--sub-langs", "en.*,es.*"]
    command += ["-P", str(args.destination), "-o", "%(title).120B [%(id)s].%(ext)s",
                "--", args.url]
    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
