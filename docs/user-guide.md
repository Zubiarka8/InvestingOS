# InvestingOS

InvestingOS helps you organize knowledge as a local, reusable graph. Create topics, connect them, arrange them in different views, and export notes for Obsidian. The current engine works with any subject, including investing.

**Project status:** early development. The core runs locally and can record sources and claims. Optional searches of open scholarly sources retrieve metadata online (see the [research tools guide](research-tools.md)); source verification, personalized lessons, and financial analysis are not implemented.

The project name is **InvestingOS**, and the Python package, command, skill, data folder (`InvestingOS-data`), export marker (`.InvestingOS-export.json`) and history folder (`.InvestingOS-history`) all use that spelling. Existing project JSON files remain usable. Exports, history folders and import folders created earlier under the lowercase names (`.investing-os-export.json`, `.investing-os-history`, `investing-os-data`) are not recognized: rename them by hand before using `update-export` or restoring history.

## Not a substitute for a professional

InvestingOS organizes knowledge and finds sources. It does not replace a qualified professional of any kind, and neither does an AI assistant that uses it, whether or not that kind of professional is named here. For a decision that affects your health, mental health, legal position, money, safety, work, property or anything else where a qualified person is responsible for the advice, ask that person. Doctors, psychologists, lawyers, financial advisers and engineers are only examples. The studies it finds describe groups of people, can be preprints, registry entries or retracted papers, and may not apply to you. Use them to prepare better questions for the professional, not to replace the conversation. If you or someone else is in danger or in crisis, contact your local emergency services or a crisis line now.

## Get started

With Git installed, clone the repository and enter its directory:

```text
git clone https://github.com/Zubiarka8/InvestingOS.git
cd InvestingOS
```

### Requirements

You need Git and Python on macOS, Linux, or Windows. The engine needs no additional runtime packages or external services. Project entry points are Python scripts; optional integrations and vendored third-party materials may have additional runtime requirements.

| Component | Requirement | Recommendation and verification |
| --- | --- | --- |
| Python (core, installer and scripts) | Python **3.10 or later**, as declared in `pyproject.toml`. | Use **Python 3.14**, with the latest maintenance release. The local test suite has passed on Python 3.11.12 and 3.14.7 on macOS; see the version matrix below. Python 3.10 is a compatibility minimum and is no longer maintained upstream; see [Python's version status](https://devguide.python.org/versions/). |
| Git | Required to clone the repository. | Use a current supported release; no minimum version has been verified for this project. |
| yt-dlp and Obsidian MCP | Optional; not installed by the pack. | See [research tools](research-tools.md) for version requirements and limitations. |

### Python test status

Project-owned scripts are written in Python for macOS, Windows, and Linux. Select a supported Python interpreter for your system.

The project declares Python 3.10 as its minimum; a declared minimum does not mean every version has already been tested. The results below are from this macOS environment on November 1, 2026. Optional PDF, OCR, transcription, MCP, and external-service integrations are not verified by these results.

| Python version | Status |
| --- | --- |
| 3.9 and earlier | Unsupported; the installer requires 3.10 or later. |
| 3.10 | Declared minimum; not tested here. |
| 3.11 | **Passed with one skipped test:** 3.11.12 on macOS; local socket binding is blocked in this environment. |
| 3.12 | Not tested here. |
| 3.13 | Not tested here. |
| 3.14 | **Passed with one skipped test:** 3.14.7 on macOS; local socket binding is blocked in this environment. |
| Later versions | Not yet tested; compatibility is not guaranteed. |

The [CI workflow](../.github/workflows/tests.yml) is configured to test Python 3.10–3.14 on macOS, Windows, and Linux, but has not yet run. Update this table only after checking actual results. The default `python3` on some systems can be an older version even when a supported version is installed.

Check your version with `python3 --version` on macOS/Linux or `py -3 --version` on Windows. If necessary, select the recommended interpreter explicitly, for example `python3.14` or `py -3.14`.

### Install the skill

From the repository directory, run:

```text
python scripts/install.py
```

On **Windows**, enable Developer Mode or otherwise grant your account permission to create symbolic links, ensure Git is configured to preserve links, and use PowerShell from the repository directory:

```powershell
py -3 scripts/install.py
py -3 scripts/InvestingOS.py --help
```

Select Python 3.10 or later: use `python3.14` on macOS or Linux, or `py -3.14` on Windows when necessary. In the examples below, `python` means a compatible Python interpreter; substitute the appropriate command if your system uses another name. Windows needs symbolic-link permission when creating skill discovery links. The core Python scripts do not require a platform-specific shell, although optional tools and third-party materials may have their own requirements.

By default, the installer activates only the `InvestingOS` skill using the shared `.agents/skills/` discovery path, used by supported versions of Codex, Cursor, Gemini CLI, OpenCode and Copilot. It does not create Claude-specific files. For Claude Code, select its directory explicitly:

```text
python scripts/install.py --client claude
```

On Windows use `py -3 scripts/install.py --client claude`. Repeat `--client shared --client claude` only if you use both. To activate a specific extra skill, use `python scripts/install.py --skill humanizer`; repeat `--skill` to select others. `python scripts/install.py --all-skills` activates the full bundle, including client-specific third-party skills. The same options work with `py -3 scripts/install.py` on Windows. The installer checks the manifest and does not replace existing files. It does not remove links from a previous installation; see [AI client compatibility](ai-clients.md). Restart your client and check that it discovers the skills; link setup does not prove client discovery. Some third-party skills need additional tools, and no third-party scripts or dependencies are installed automatically.

Create a project outside the repository and add two topics. A study profile can be recorded at creation or updated later:

```text
python -c "from pathlib import Path; (Path.home() / 'InvestingOS-data').mkdir(parents=True, exist_ok=True)"
python scripts/InvestingOS.py create "$HOME/InvestingOS-data/my-project.json" "Investing basics"
python scripts/InvestingOS.py set-profile "$HOME/InvestingOS-data/my-project.json" --goal "Understand risk" --audience "Independent learners" --prior-knowledge "Basic arithmetic" --scope "Core concepts" --depth "Introductory" --language "English"
python scripts/InvestingOS.py add-node "$HOME/InvestingOS-data/my-project.json" "Investing"
python scripts/InvestingOS.py add-node "$HOME/InvestingOS-data/my-project.json" "Risk"
python scripts/InvestingOS.py add-view "$HOME/InvestingOS-data/my-project.json" "Topics"
```

Each command prints a stable ID. To connect the two topics in the view, replace the placeholders below with the IDs printed above. You can also find them later with `show`.

```text
python scripts/InvestingOS.py add-edge "$HOME/InvestingOS-data/my-project.json" INVESTING_NODE_ID RISK_NODE_ID contains --view VIEW_ID
python scripts/InvestingOS.py show "$HOME/InvestingOS-data/my-project.json"
python scripts/InvestingOS.py audit "$HOME/InvestingOS-data/my-project.json"
```

`contains` points from the parent to the child. `part_of` points from the child to the parent. `requires` points from a topic to its prerequisite. The same node can appear in several views without being copied.

For command options, run `python scripts/InvestingOS.py --help` or add `--help` after a command.

Maintain hierarchies without recreating concepts: `rename-node` preserves a node's ID, `move-node FILE NODE_ID VIEW_ID --parent PARENT_ID --position 2` changes the parent and sibling order in that view, and `remove-edge FILE EDGE_ID` removes only a relationship. Omit `--parent` to place a node among the view roots; use `--position` for root order. Other views and node IDs remain intact. A node with multiple parents in the same view must be disentangled explicitly before moving.

The profile fields are optional and discipline-independent: goal, audience, prior knowledge, scope, desired depth, constraints and language. They guide the learner-facing plan without turning topic depth into a competence level. The viewer shows the profile on the overview page.

## Write study notes

Each node can hold flexible Markdown study notes separately from its short description. Load a note from a UTF-8 Markdown file or pass text directly:

```text
python scripts/InvestingOS.py set-note "$HOME/InvestingOS-data/my-project.json" NODE_ID --input-file "$HOME/InvestingOS-data/notes.md"
python scripts/InvestingOS.py set-note "$HOME/InvestingOS-data/my-project.json" NODE_ID --text "A concise study note."
```

Notes may use any headings or layout. Keep source-backed claims linked through `add-source` and `add-claim`; a Markdown note alone does not record its evidence. The local viewer displays saved notes, and Obsidian export creates one linked note for each knowledge node.

## View a project in your browser

Start the local workspace for a project:

```text
python scripts/InvestingOS.py web "$HOME/InvestingOS-data/my-project.json"
```

Open `http://127.0.0.1:8000/` in your browser. On Windows use `py -3 scripts/InvestingOS.py web "$HOME/InvestingOS-data/my-project.json"`. Use `--port 8080` to choose another port and press Ctrl+C in the terminal to stop the server.

The viewer binds only to the local machine and has no external runtime dependencies. It provides a search field and sections for topics, indexes, sources, claims, evidence, competencies, learning paths and research tasks. Open a topic to explore incoming and outgoing connections and its claim sources; open an index to browse its hierarchy. Search filters records in the selected section; it does not search extracted document contents. Refresh the page after editing the project.

New Markdown imports include a **Sources** section with a link to the original local file or the recorded web or YouTube URL. Exported node notes list the sources linked through their claims, and the exported index lists recorded sources; notes without linked sources say so. A source link does not verify its content. Local links can reveal file locations and may stop working if files are moved. Existing Markdown files are not changed automatically.

### Superindex

Open **Superindex** in the web viewer to see all views and their numbered hierarchy, including deeply nested topics and concepts reused in multiple branches. Numbers describe positions in a view and can change when its order changes; node IDs remain stable. The index follows `contains` and `part_of` relationships assigned to each view. A view with no hierarchical relationships has no indexed topics. Search filters displayed topics. Use the page export controls to export the visible superindex.

### Export the current web page

On a topic, index, source or overview page, choose **Export Word** to review the content, then download it as an editable `.docx`. The preview shares the document content and approximates its styling; it does not reproduce Word pagination. The document uses matching colors and typography, but Word reflows the content and does not reproduce the screen layout pixel for pixel. The current search filter is respected. The Import form is not exportable.

Choose **Export PDF** to review the print layout, then choose **Print or save as PDF** and select **Save as PDF** in the browser dialog. The browser dialog shows the final page breaks. The print layout hides navigation and controls while retaining the page content. Browser print settings can change page size, margins and background colors. Both options work locally and do not require a third-party Python package. Actual print appearance depends on the browser and has not been visually verified in this environment.

The **Import** section accepts an existing local file path, a public HTTPS page, or a YouTube video URL. It registers the result as a source and creates a separate folder under `pdf`, `documents`, `web` or `youtube`, optionally followed by user-defined topic folders (for example `topic/subtopic`). By default these files are saved beside the project in `InvestingOS-data/<project-id>/temporary`; you can choose another storage folder in the form. Each import gets a unique folder. These files persist until removed manually; this is not the operating system temporary directory and no cleanup manager is currently provided. Originals are not moved or deleted. It does not provide a file picker: the file must already be on the same machine and its path must be entered. Other project edits use the CLI. The import form changes the project; do not expose the local server to other machines. Local server startup and form submission have not been verified in a browser in environments that block socket binding.

## Import an outline

Save a plain UTF-8 text file with one topic per line, then create a new project from it:

```text
python scripts/InvestingOS.py create "$HOME/InvestingOS-data/imported.json" "My outline" --outline examples/history.txt
```

The importer preserves the original file and creates one node per nonempty line. It does not interpret indentation or build a hierarchy. Add views and relationships afterward.

## Export to Obsidian

Export to a **new directory** inside or outside an Obsidian vault:

```text
python scripts/InvestingOS.py export "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/my-notes"
```

Open the generated Markdown files in Obsidian or any text editor. Export creates a snapshot and refuses to use an existing directory. Each hierarchy is shown as a nested numbered index, each node and source receives its own stable-ID note, and `sources.md` groups sources by their user-defined publication type. Notes link to the index and related records and are marked as unverified. New exports include a manifest that lets you later update generated notes:

```text
python scripts/InvestingOS.py update-export "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/my-notes"
```

On Windows PowerShell, use a supported Python interpreter with the same Python script:

```text
py -3 scripts/InvestingOS.py update-export "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/my-notes"
```

The update preserves notes edited or deleted since the last export and reports them as conflicts. It does not delete removed nodes or merge manual Obsidian edits back into project JSON. Source notes record bibliographic fields and review dates; a review date does not mean a claim is verified. Existing snapshots created before this feature have no manifest and cannot be updated. Back up your vault first and do not edit notes concurrently with the update.

## Record sources and claims

Register a source and a claim (replace `SOURCE_ID` and `NODE_ID` with IDs from your project):

```text
python scripts/InvestingOS.py add-source "$HOME/InvestingOS-data/my-project.json" "Source title" --url "https://example.org/source" --author "Author" --accessed "2026-11-01" --locator "Page 12"
python scripts/InvestingOS.py add-claim "$HOME/InvestingOS-data/my-project.json" "A claim to review" --source SOURCE_ID --node NODE_ID
python scripts/InvestingOS.py show "$HOME/InvestingOS-data/my-project.json"
```

Claims default to `unverified`. You may manually specify `--status supported`, `disputed`, or `outdated`; `supported` requires at least one source. A source link is not proof that the claim is correct, and the tool does not verify it. Claims can refer to multiple nodes and sources; linked claims and their source details appear in exported node notes. Existing projects remain readable.

## Import and search documents

`import-document` extracts a local PDF, HTML, Markdown, or text file into a new text file and registers the original path, extracted path, and SHA-256 in the project. PDF extraction needs the optional dependency described in [research tools](research-tools.md). It preserves the original and refuses to overwrite an extraction file.

```text
python scripts/InvestingOS.py import-document "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/source.txt" "$HOME/InvestingOS-data/source-extracted.txt"
python scripts/InvestingOS.py search "$HOME/InvestingOS-data/my-project.json" "source"
python scripts/InvestingOS.py research-report "$HOME/InvestingOS-data/my-project.json"
```

Search matches project node, source and claim fields; add `--documents` to scan extracted text files. This scan requires the files to remain available and does not build an index. The report lists unverified or unsourced claims, source records without a location, and explicitly recorded contradiction edges. It does not discover contradictions or verify sources automatically. Paths are stored as local absolute paths and can reveal private information if the project file is shared. If saving the project fails after extraction, the extracted output remains on disk for review.

### Convert sources to Markdown

```text
python scripts/InvestingOS.py import-markdown "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/source.csv" "$HOME/InvestingOS-data/source.md"
python scripts/InvestingOS.py search-youtube "history of astronomy" --limit 5
python scripts/InvestingOS.py import-youtube "$HOME/InvestingOS-data/my-project.json" "https://www.youtube.com/watch?v=VIDEO_ID" "$HOME/InvestingOS-data/video.md"
python scripts/InvestingOS.py import-web "$HOME/InvestingOS-data/my-project.json" "https://example.org/article" "$HOME/InvestingOS-data/article.md"
```

Each generated Markdown import ends with a source link and the related project's name and stable ID. This helps identify the project when imported files are stored in larger source folders. See [format-specific Python scripts](research-tools.md#format-specific-python-scripts) and [research tools](research-tools.md) for optional dependencies, accepted formats, provenance and limitations. Downloading or converting a source never verifies its claims.

To import a local collection in one operation, keep the output directory outside the input directory:

```text
python scripts/InvestingOS.py import-folder "$HOME/InvestingOS-data/my-project.json" "$HOME/Documents/sources" "$HOME/InvestingOS-data/imported-sources"
python scripts/InvestingOS.py set-source-status "$HOME/InvestingOS-data/my-project.json" SOURCE_ID processed
```

The importer preserves subfolders, imports supported local formats, skips hashes already recorded in the project, and reports per-file failures. Sources start in `inbox`; `processed` and `archived` are organizational states, not verification states. Originals are unchanged.

Build a local full-text index and search extracted documents:

```text
python scripts/InvestingOS.py index-documents "$HOME/InvestingOS-data/my-project.json"
python scripts/InvestingOS.py search-documents "$HOME/InvestingOS-data/my-project.json" "source query" --limit 20
```

Index refreshes are incremental; pass `--rebuild` to recreate it. The SQLite FTS5 sidecar sits beside the project JSON, is git-ignored and contains extracted text. `search --documents` remains available as a direct scan. A Python SQLite build without FTS5 cannot provide indexed search.

To create a scaffold for source-aware study notes, then save the completed note to its node:

```text
python scripts/InvestingOS.py draft-note "$HOME/InvestingOS-data/my-project.json" NODE_ID "$HOME/InvestingOS-data/draft.md"
python scripts/InvestingOS.py set-note "$HOME/InvestingOS-data/my-project.json" NODE_ID --input-file "$HOME/InvestingOS-data/draft.md"
```

The scaffold includes the project identity and claims linked to that node. It does not summarize sources or verify claims; read the source material before writing a synthesis.

## Research workflows

Use an indented UTF-8 outline with two spaces per level to add a hierarchy to an existing project. The original is preserved; duplicate titles or skipped levels are rejected.

```text
python scripts/InvestingOS.py import-outline "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/outline.txt"
python scripts/InvestingOS.py add-research-task "$HOME/InvestingOS-data/my-project.json" "Find a primary source" --node NODE_ID --priority high
python scripts/InvestingOS.py set-task-status "$HOME/InvestingOS-data/my-project.json" TASK_ID done
python scripts/InvestingOS.py add-evidence "$HOME/InvestingOS-data/my-project.json" CLAIM_ID SOURCE_ID "Page 7" --note "Relevant observation"
python scripts/InvestingOS.py review-source "$HOME/InvestingOS-data/my-project.json" SOURCE_ID 2026-11-01
python scripts/InvestingOS.py export-csl "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/bibliography.json"
python scripts/InvestingOS.py compare "$HOME/InvestingOS-data/older.json" "$HOME/InvestingOS-data/my-project.json"
```

Replace IDs with values from your project. Evidence requires a source already linked to the claim and a locator; recording it does not verify the claim. Review dates record a manual action and do not establish freshness. CSL output uses only recorded fields and does not infer publication dates or author name parts. `compare` reports changed, added and removed IDs between snapshots of the same project; use `backup` to create snapshots explicitly. `suggest-duplicates` proposes similar node titles, and `merge-nodes PROJECT KEEP_ID REMOVE_ID` explicitly merges two nodes when integrity checks pass. The retained node records the removed node's metadata and ID; the old ID is not a lookup alias. Similarity is not proof of equivalence.

Use `add-competency PROJECT "Capability" --node NODE_ID --level "beginner" --evidence "Demonstration"` and `add-learning-path PROJECT "Path" COMPETENCY_ID ...` for configurable skills and an ordered sequence. Levels are descriptions, not official qualifications. Use `schedule-review PROJECT SOURCE_ID YYYY-MM-DD` to flag reviews due in `research-report`, and `export-bibtex PROJECT OUTPUT` for a basic bibliography. Source fields `--year`, `--publisher` and `--publication-type` can be supplied to `add-source`.

Each project overwrite preserves the previous JSON in `.InvestingOS-history/PROJECT_ID/` next to the project. History can contain sensitive data, grows with each edit, and is not automatically pruned. Use `compare` and `restore` with a chosen history file to inspect or restore a version to a new path.

Version 1 projects migrate additively to version 2. Run `python scripts/InvestingOS.py migrate PATH_TO_PROJECT.json` to write the upgrade; the v1 file is saved in history. Saves reject stale project snapshots if another InvestingOS process has written since they were loaded. Exclusive lock files prevent overlapping saves. After a crash, inspect the hidden `.<filename>.lock` and confirm no writer is active before removing it.

## Check tools and back up a project

```text
python scripts/InvestingOS.py doctor
python scripts/InvestingOS.py backup "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/my-project-backup.json"
python scripts/InvestingOS.py restore "$HOME/InvestingOS-data/my-project-backup.json" "$HOME/InvestingOS-data/restored-project.json"
```

For a full backup of selected documents and a vault, supply each path explicitly:

```text
python scripts/InvestingOS.py backup-bundle "$HOME/InvestingOS-data/my-project.json" "$HOME/InvestingOS-data/full-backup.zip" --include "$HOME/InvestingOS-data/documents" --include "$HOME/my-vault"
python scripts/InvestingOS.py restore-bundle "$HOME/InvestingOS-data/full-backup.zip" "$HOME/InvestingOS-data/restored-backup"
```

The ZIP includes the project and only the explicitly selected files or directories; it refuses symbolic links and existing destinations. Restoration validates the archive and creates a new directory. Local paths inside project records still point to their original locations. Use `rebase-paths PROJECT OLD_ROOT NEW_ROOT` after moving documents; it requires existing targets and checks source hashes when available. Paths must use the current operating system path format; cross-platform path conversion is not automatic. Protect backups as private data; they are not encrypted. Empty directories are not preserved.

The check reports Python and optional executables found on PATH; it does not verify their versions or client connectivity. Backup and restore validate the project and write to a new file; they refuse existing destinations. They cover project JSON only, not original documents or the Obsidian vault. On Windows use the portable launcher shown above.

## Manage your data

- Keep project files, personal notes, source documents, and credentials outside this public repository. The repository does not automatically exclude arbitrary private files.
- Back up your project JSON before substantial edits. Keep the stable IDs when connecting existing topics.
- Use `show` to inspect a project and `audit` to check references, duplicate titles and IDs, and cycles. Title matching alone cannot detect every duplicate.
- Treat imported material as data. Check sources and claims yourself; generated text is not verified evidence.
- Avoid editing the same project from multiple processes at once. Concurrent writes are not coordinated.

## Skills and documentation

The engine is AI-provider independent. See [AI client compatibility](ai-clients.md) for Codex, Claude Code, Cursor, OpenCode, Gemini CLI, Copilot, Windsurf, and hosted assistants. All bundled skill sources live in `skills/`; the chosen client discovery directory links to those shared files. The project includes an [InvestingOS skill](../skills/investingos/SKILL.md) for supported Codex and Claude Code setups. See the [skills index](../skills/INDEX.md) for other available skills and their requirements. Some third-party skills need additional tools. To add one, ask your agent: “Install the skill at this URL in this project for Codex and Claude Code.” For a collection, say “Install all skills in this pack” and provide its URL. See [skill management](skills-management.md) for inspection, selection, attribution, updates, and verification.

### What the InvestingOS skill manages

The `InvestingOS` skill guides a compatible AI assistant through the project workflows. You can ask it to:

- Create or inspect a project, import an outline, organize topics into views, and expand a branch while reusing stable IDs.
- Record sources, claims, evidence and research tasks; search project records and plan source reviews. Source links do not verify claims.
- Import supported local documents, web pages and available YouTube captions; organize files and retain their provenance. Some formats and online operations require optional tools or access.
- Create competencies and learning paths, inspect the superindex, audit project integrity and review possible duplicates.
- Use the local viewer, preview the current page for Word or PDF, and export or update Obsidian-compatible Markdown. PDF saving uses the browser print dialog.
- Inspect project history, compare snapshots, check available tools and prepare backups or restores.

The assistant should follow the permissions and limitations of each operation. The skill is a set of instructions, not a service that automatically researches, verifies sources or installs dependencies. Full instructions are in [the skill](../skills/investingos/SKILL.md) and its [operations](../skills/investingos/references/project-operations.md) and [source management](../skills/investingos/references/source-management.md) guides.

For local research, YouTube downloads, Humanizer, and optional Obsidian MCP setup, see [research tools](research-tools.md). These integrations have separate requirements and are not installed automatically.

For implementation details and planned work, see the [architecture](architecture.md), [development plan](plan.md), and [project evaluation](alternatives.md).

## Skill credits and versions

Project links point to local copies; installation does not install external dependencies or guarantee client discovery. Upstream names do not imply sole authorship. VaultForge and writing-guidelines are not part of the public package because their licenses could not be verified.

| Skill or collection | Author or upstream | Installed version or revision | License and notes |
| --- | --- | --- | --- |
| InvestingOS | InvestingOS contributors | Project version 0.1.0; skill has no separate version | MIT; [skill](../skills/investingos/SKILL.md). |
| Education Agent Skills (165 skills) | [Gareth Manning and contributors](https://github.com/GarethManning/education-agent-skills) | Commit `135d6275e7db0657d70b147f46d3191c5430677d` | CC BY-SA 4.0, shared alike; unmodified skills, with the code that is not clearly licensed removed. See the [notice](../skills/collections/education-agent-skills-main/NOTICE-INVESTINGOS.md) and its LICENSE. |
| Course Builder | [klausners and contributors](https://github.com/klausners/course-builder) | Based on commit `09bdafb5f723db71238481d1b157a564a94d131f`; locally modified transcript helper | MIT; companion agents are required and client compatibility is not verified. |
| Obsidian Skills (6 skills) | [kepano and contributors](https://github.com/kepano/obsidian-skills) | Commit `3ccff5338ea700537839b21900aa5358a0402c98` | MIT; individual skills may require external tools. |
| Scrapling skill | [Karim Shoair / Scrapling](https://github.com/D4Vinci/Scrapling) | Commit `95cf9019ab5a5d6f3e9654b7ef1c6a26e29dc5c0` | BSD-3-Clause; notice included. Optional dependencies. |
| Humanizer | [Siqi Chen and contributors](https://github.com/blader/humanizer) | Commit `0ef9fe5bc3572734fd3ae6c448fe00a30cd5dcf0`; plugin manifest modified | MIT; notice included. |
| copy-editing | [Corey Haines and contributors](https://github.com/coreyhaines31/marketingskills) | Commit `158bd3af27b00323d5a950c033efa0256f7aa426` | MIT; notice included. |
| context7-mcp | [Upstash](https://github.com/upstash/context7) | Commit `7836c583918374fbecffacf866afb7594b919466` | MIT; notice included; requires Context7 tools. |
| investigate-first | [Julius Brussee and contributors](https://github.com/JuliusBrussee/caveman) | Commit `9b68f7ed12b05e7efaff18e65c5a3fc2849fd0a4` | Apache-2.0; license and notice included. |

See the [individual redistribution review](skill-redistribution-review.md) for exact source matches, license conditions and unresolved publication checks.

## Development

Run the tests from the repository root with Python 3.10 or later. If `python3` is older, replace it with the command for a compatible version:

```text
python3 -m unittest discover -s tests -v
```

A [GitHub Actions workflow](../.github/workflows/tests.yml) is configured for Python 3.10 through 3.14 on Linux, macOS and Windows. It has not yet run in this repository; Windows skill links require symbolic-link support.

Contributions should keep the core independent of any discipline or AI provider, preserve stable IDs and user data, and include appropriate verification. See [AGENTS.md](../AGENTS.md) for shared project instructions.

## License

The project is licensed under the [MIT License](../LICENSE). Bundled third-party materials may have different licenses; consult their included notices before reuse or redistribution.
