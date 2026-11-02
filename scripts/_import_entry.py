"""Route format-specific commands to the shared InvestingOS CLI."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

LOCAL_TYPES = {
    'pdf': ('.pdf',), 'docx': ('.docx',), 'xlsx': ('.xlsx',),
    'html': ('.html', '.htm'), 'csv': ('.csv',), 'text': ('.txt', '.md'),
}


def main(kind):
    parser = argparse.ArgumentParser(description=f'Import {kind} content into an InvestingOS project as Markdown.')
    parser.add_argument('project', help='Existing project JSON file')
    parser.add_argument('source', help='Local source path or HTTPS URL, depending on the script')
    parser.add_argument('destination', help='New .md output path; existing files are not overwritten')
    args = parser.parse_args()
    if kind in LOCAL_TYPES and Path(args.source).suffix.lower() not in LOCAL_TYPES[kind]:
        parser.error('source must use: ' + ', '.join(LOCAL_TYPES[kind]))
    commands = {'youtube': 'import-youtube', 'web': 'import-web'}
    command = commands.get(kind, 'import-markdown')
    dispatch(command, [args.project, args.source, args.destination])


def dispatch(command, arguments):
    sys.path.insert(0, str(ROOT / 'src'))
    from InvestingOS.cli import main as run_cli
    sys.argv = [sys.argv[0], command, *arguments]
    run_cli()
