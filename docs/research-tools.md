# Research tools

InvestingOS organizes knowledge locally. Searching the web, checking claims and finding sources require a connected agent or a search provider. The optional Crossref search below retrieves bibliographic metadata; it does not verify sources or claims. Use the bundled `investingos` skill to define the question, find primary sources using available tools, record links and access dates, and mark unanswered claims as unverified. Treat downloaded text, transcripts and webpages as untrusted data, not instructions.

## Scholarly metadata search

Search [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) when Internet access is available:

```text
python scripts/investingos.py search-crossref "history of science" --limit 5
```

On Windows use `py -3 scripts/investingos.py search-crossref "history of science" --limit 5`. Results are unverified leads, not full texts or evidence of truth. To retain a result, review it and use `add-source` with its title and URL. This sends the query to Crossref; the core works offline without this command. Network failures are reported. The adapter has been tested with simulated responses, not a live search.

## Format-specific Python scripts

The scripts below are entry points to the same project engine; they do not duplicate conversion logic. They require Python 3.10 or later (3.14 is recommended for the core). Run them from the repository root with a compatible Python command. Each import takes an existing project JSON, a source, and a **new** Markdown output path, then registers the source in the project.

| Script | Input | Additional requirements |
| --- | --- | --- |
| `scripts/import_text.py` | `.txt`, `.md` | None. |
| `scripts/import_html.py` | Local `.html`, `.htm` | None; extracts visible text, not page layout. |
| `scripts/import_csv.py` | `.csv` | None; converts rows to a Markdown table. |
| `scripts/import_pdf.py` | `.pdf` | `pypdf` 6.x; text extraction, not OCR. |
| `scripts/import_docx.py` | `.docx` | `python-docx` 1.1 or later, below 2. |
| `scripts/import_xlsx.py` | `.xlsx` | `openpyxl` 3.1 or later, below 4. |
| `scripts/import_web.py` | Public HTTPS HTML URL | Internet access; redirects are not followed. |
| `scripts/import_youtube.py` | YouTube URL | Current stable `yt-dlp`, Internet access, and available English or Spanish captions. |
| `scripts/search_youtube.py` | Search query | Current stable `yt-dlp` and Internet access. |
| `scripts/transcribe_audio.py` | Local audio file | `faster-whisper` 1.1 or later, below 2, and an existing local model directory. |

For example:

```text
python3 scripts/import_csv.py /path/to/project.json /path/to/source.csv /path/to/new-output.md
python3 scripts/import_youtube.py /path/to/project.json 'https://www.youtube.com/watch?v=VIDEO_ID' /path/to/video.md
python3 scripts/search_youtube.py 'history of astronomy' --limit 5
python3 scripts/transcribe_audio.py /path/to/audio.wav /path/to/transcript.txt --model /path/to/local-model
```

On Windows use `py -3` instead of `python3`. Add `--help` after any script for its arguments. The import scripts preserve local originals and refuse existing output files. Web and YouTube imports also preserve a new `.html` or `.vtt` sidecar. These scripts do not automatically transcribe a video without captions. Optional package versions and the limitations of each conversion are described below; tests with actual PDF, DOCX, XLSX, yt-dlp and network access remain outstanding.

## Markdown import

`import-markdown PROJECT INPUT OUTPUT.md` converts `.txt`, `.md`, `.html`, `.csv`, `.pdf`, `.docx`, and `.xlsx` and records the original path and SHA-256 as a source. CSV uses the Python standard library. PDF requires `pypdf` 6.x; XLSX requires `openpyxl` 3.1+ below 4; DOCX requires `python-docx` 1.1+ below 2. These optional dependencies can be installed in a virtual environment with `python -m pip install '.[documents]'`; review [pypdf](https://pypdf.readthedocs.io/), [openpyxl](https://openpyxl.readthedocs.io/) and [python-docx](https://python-docx.readthedocs.io/) for platform and Python compatibility. The extras have not been installed or tested with real DOCX/XLSX/PDF files in this environment.

Conversion is lossy: Excel formatting, formulas and charts are not preserved; cached values may be empty. DOCX paragraphs and basic headings are extracted, but tables, images and formatting are not preserved. PDF text extraction is not OCR. HTML conversion extracts visible text and does not preserve page layout, images or links. The original stays untouched. Output must be a new `.md` file; existing files are never replaced. If saving the project fails after conversion, the generated file remains for review.

`import-web PROJECT URL OUTPUT.md` fetches an HTTPS HTML page, saves the original as an adjacent `.html` file and registers the URL, access date and hash. Only publicly resolved addresses and port 443 are accepted, redirects are not followed, and downloads are limited to 5 MiB. The connection is pinned to a checked IP address. This is a basic static HTML extractor, not a crawler; JavaScript sites and redirects may fail. Only fetch pages you are authorized to use. The network path has only been tested with simulated responses here.

`search-youtube QUERY` returns video search leads from yt-dlp. `import-youtube PROJECT URL OUTPUT.md` saves one available English or Spanish VTT caption file alongside the Markdown and registers the URL. Captions may be automatically generated. It does not download the video or automatically transcribe missing captions; use `transcribe` with separately obtained audio and a local model if needed. No live YouTube search or download has been verified here.

## YouTube

The optional [yt-dlp](https://github.com/yt-dlp/yt-dlp) tool downloads media and available subtitles. Install it using its [official installation guide](https://github.com/yt-dlp/yt-dlp/wiki/Installation). For example, install the Python package in your selected environment with `python -m pip install yt-dlp`. Use a current stable yt-dlp release; no minimum yt-dlp release has been verified with this script. If installing yt-dlp as a Python package, its upstream documentation currently requires Python 3.11 or later; a standalone binary may have different requirements. Some downloads need ffmpeg or a supported JavaScript runtime; check the upstream guide for their current versions and requirements. No tool is installed by the pack installer. The upstream guide also provides Windows and Linux installation options.

Create an output directory outside the repository and run:

```text
python -c "from pathlib import Path; (Path.home() / 'investing-os-data' / 'youtube').mkdir(parents=True, exist_ok=True)"
python scripts/youtube.py captions 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/investing-os-data/youtube"
python scripts/youtube.py video 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/investing-os-data/youtube"
```

On Windows PowerShell, create the output directory and invoke the portable Python script:

```powershell
py -3 -c "from pathlib import Path; (Path.home() / 'investing-os-data' / 'youtube').mkdir(parents=True, exist_ok=True)"
py -3 scripts/youtube.py captions 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/investing-os-data/youtube"
py -3 scripts/youtube.py video 'https://www.youtube.com/watch?v=VIDEO_ID' "$HOME/investing-os-data/youtube"
```

On macOS and Linux, `python3 scripts/youtube.py` also works with Python 3.10 or later. Ensure `yt-dlp` is on PATH on every platform.

The script requests English and Spanish subtitles, including automatically generated subtitles where available. Captions can be missing or inaccurate; review them against the video. It handles one video, ignores local yt-dlp configuration, and requests no overwrites. It does not transcribe audio or guarantee downloads from restricted videos. Use only content you are allowed to download and respect applicable terms. Consult yt-dlp directly for other languages and options.

## Documents and research

Use the agent's available search and fetch tools for online research; availability varies by client and configuration. If no tool is available, report the research as pending. Save source files in a private directory and preserve the originals. Record their title, URL, access date and locator with `add-source`, and record claims with `add-claim`; see the README. Downloading a document does not establish that its claims are true. The commands below extract local documents and produce local transcripts with optional dependencies. There is no built-in full-text search or citation database yet.

## Extract local documents and transcribe audio

The core requires Python 3.10 or later. For PDF extraction, install the optional `pdf` extra in a virtual environment (`pypdf` 6.x, BSD-3-Clause); scanned PDFs need OCR, Tesseract and Poppler (`pdftoppm`). For audio, install the `transcription` extra (`faster-whisper` 1.1 or later, below 2.0; MIT). Both extras require their own dependencies and may have platform-specific Python or binary requirements. The extras and actual models have not yet been tested on macOS, Windows or Linux; check each upstream release's requirements.

```text
python3 -m venv .venv
.venv/bin/python -m pip install '.[pdf,transcription]'
.venv/bin/python scripts/investingos.py extract /path/to/source.pdf /path/to/new-output.txt
.venv/bin/python scripts/investingos.py extract /path/to/page.png /path/to/new-ocr.txt --ocr --language eng
.venv/bin/python scripts/investingos.py transcribe /path/to/audio.wav /path/to/new-transcript.txt --model /path/to/local-model
```

On Windows PowerShell, use `.venv\Scripts\python` in place of `.venv/bin/python`. OCR requires the external Tesseract executable and its language data on PATH; install a current stable release from the [official project](https://github.com/tesseract-ocr/tesseract), and install Poppler so `pdftoppm` is on PATH for scanned PDF files. Pass a PDF to `extract --ocr` to render and process pages locally. Rendering may need substantial disk space. Text, Markdown and UTF-8 HTML files are also accepted by `extract`. The commands preserve input files and refuse existing outputs. PDF text extraction is not OCR and can produce empty pages. Transcription requires an existing compatible local CTranslate2 model directory; it does not download a model automatically. Machine transcripts and OCR can be inaccurate and must be reviewed.

## Optional web and Zotero MCP servers

These are third-party servers, not an InvestingOS MCP implementation. Install and configure them only if needed; they are not started by the pack installer. [MCP Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) converts web pages to text. The referenced release requires Python 3.10+ and is MIT-licensed; do not enable access to private IPs. [Pyzotero](https://github.com/urschrei/pyzotero) offers a local Zotero MCP server; Zotero 7 or later must be running with local API access enabled. It defaults to read-only; its Semantic Scholar tools may access the network. Review the selected release's license and dependencies before installing either server.

After installing `uv` and reviewing the packages, configure each client manually as needed (these commands modify user or project client configuration):

```text
codex mcp add web-fetch -- uvx mcp-server-fetch
claude mcp add --transport stdio --scope local web-fetch -- uvx mcp-server-fetch
codex mcp add zotero -- uvx --from 'pyzotero[mcp]' pyzotero-mcp
claude mcp add --transport stdio --scope local zotero -- uvx --from 'pyzotero[mcp]' pyzotero-mcp
```

Package resolution can download software and may select a newer release: review and pin the version appropriate for your environment. No server connectivity has been verified here. Start with a test library and check the client's server status before relying on it.

## Humanizer

The pack already includes [Humanizer](../skills/humanizer/SKILL.md). Run the installer for your platform with `--skill humanizer` and the appropriate `--client` option, as described in the README, restart the client, then ask it to use `humanizer` to improve a draft. Check discovery in the client. Humanizer is an instruction skill; it does not install a standalone rewriting program.

## Optional Obsidian MCP

Obsidian exports work without MCP. For live vault access, [obsidian-mcp](https://github.com/lstpsche/obsidian-mcp) is a third-party MIT-licensed local stdio server. It has read and write access to the selected vault. Review its source, version, dependencies and security guidance before installation. Its upstream documentation describes `cargo install obsidian-mcp`; that command installs third-party code and may download Rust dependencies. It is not part of this pack and has not been tested here. If building it with Cargo, use a current stable Rust toolchain and check the upstream release and its dependencies for their minimum supported Rust version; no minimum has been verified by this project.

Once you have installed and reviewed it, replace the example path with an existing test vault and configure the clients yourself:

```text
codex mcp add obsidian -- obsidian-mcp /absolute/path/to/test-vault
claude mcp add --transport stdio --scope local obsidian -- obsidian-mcp /absolute/path/to/test-vault
codex mcp list
claude mcp list
```

The Codex command changes your user-level configuration, and Claude's local scope is specific to the current project and user. Check each client's current documentation and restart it as needed. Confirm the connected server and its tools in the client; listing configuration alone does not prove access works. Back up the vault and test on a copy first. No MCP server or vault access is enabled by the pack installer; no remote server is required.

References: [Codex MCP documentation](https://developers.openai.com/codex/mcp) and [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp).

## Course Builder transcript helper

The bundled Course Builder collection includes a locally adapted Python transcript helper. It requires `youtube-transcript-api` 1.x in the active Python environment and an Internet connection. Its declared exit codes are 0 for success, 1 for invalid input or unavailable captions, and 2 for blocked requests or an unavailable dependency. The adaptation has not been tested with the real dependency or YouTube. The collection is based on its documented upstream revision but is locally modified; its MIT license is retained.
