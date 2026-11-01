"""Fetch a public HTML page as an untrusted source and local Markdown."""
from datetime import date
from html import escape
import ipaddress
import http.client
import ssl
from pathlib import Path
import socket
from urllib.parse import urlsplit

from .core import add_source
from .documents import TextHTML
from .knowledge_tools import _hash
from .source_links import imported_source_section


def _fetch_pinned(hostname, address, target):
    class PinnedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            sock = socket.create_connection((address, 443), self.timeout)
            try:
                self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
            except Exception:
                sock.close()
                raise

    connection = PinnedHTTPS(hostname, timeout=20, context=ssl.create_default_context())
    try:
        connection.request('GET', target, headers={'User-Agent': 'InvestingOS/0.1', 'Accept': 'text/html'})
        response = connection.getresponse()
        if not 200 <= response.status < 300:
            raise ValueError(f'HTTP status {response.status}; redirects are not followed')
        if 'text/html' not in response.getheader('Content-Type', '').lower():
            raise ValueError('response is not HTML')
        return response.read(5 * 1024 * 1024 + 1)
    finally:
        connection.close()


def import_web(project, url, destination):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None or
            parsed.password is not None or parsed.port not in (None, 443)):
        raise ValueError('provide a public HTTPS URL without credentials or a custom port')
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('URL must resolve only to public addresses')
    destination = Path(destination).resolve()
    if destination.suffix.lower() != '.md':
        raise ValueError('destination must be a Markdown file')
    original = destination.with_suffix('.html')
    if destination.exists() or original.exists():
        raise FileExistsError('Markdown or HTML destination already exists')
    target = parsed.path or '/'
    if parsed.query:
        target += '?' + parsed.query
    raw = _fetch_pinned(parsed.hostname, addresses[0][4][0], target)
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError('HTML exceeds the 5 MiB limit')
    parser = TextHTML()
    parser.feed(raw.decode('utf-8', errors='replace'))
    with original.open('xb') as handle:
        handle.write(raw)
    try:
        with destination.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write('# Web page\n\nSource: ' + escape(url) + '\n\n' + escape(''.join(parser.parts)) + '\n')
            handle.write(imported_source_section(url=url))
    except Exception:
        original.unlink()
        raise
    source = add_source(project, 'Web page', url=url, accessed=date.today().isoformat())
    source.update(local_path=str(original), extracted_path=str(destination), sha256=_hash(original))
    return source
