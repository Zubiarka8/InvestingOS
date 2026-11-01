"""Command-line interface; all mutations are explicit."""
import argparse
import http.client
import zipfile
import shutil
import subprocess
import sys
from pathlib import Path
from .core import CLAIM_STATUSES, RELATIONS, add_claim, add_edge, add_node, add_source, add_view, audit, create_project
from .export import export, update_export
from .storage import load, save


def main():
    parser = argparse.ArgumentParser(prog="investingos")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("file")
    create.add_argument("title")
    create.add_argument("--description", default="")
    create.add_argument("--outline", help="UTF-8 text file; one topic per nonempty line")
    node = commands.add_parser("add-node")
    node.add_argument("file")
    node.add_argument("title")
    node.add_argument("--description", default="")
    view = commands.add_parser("add-view")
    view.add_argument("file")
    view.add_argument("title")
    view.add_argument("--kind", choices=["hierarchy", "network", "pathway"], default="hierarchy")
    edge = commands.add_parser("add-edge")
    edge.add_argument("file")
    edge.add_argument("source")
    edge.add_argument("target")
    edge.add_argument("type", choices=sorted(RELATIONS))
    edge.add_argument("--view")
    source = commands.add_parser("add-source")
    source.add_argument("file")
    source.add_argument("title")
    for option in ("url", "author", "accessed", "locator"):
        source.add_argument("--" + option, default="")
    for option in ("year", "publisher", "publication-type"):
        source.add_argument("--" + option, default="")
    claim = commands.add_parser("add-claim")
    claim.add_argument("file")
    claim.add_argument("text")
    claim.add_argument("--source", action="append", default=[])
    claim.add_argument("--node", action="append", default=[])
    claim.add_argument("--status", choices=sorted(CLAIM_STATUSES), default="unverified")
    for command in ("show", "audit"):
        sub = commands.add_parser(command)
        sub.add_argument("file")
    out = commands.add_parser("export")
    out.add_argument("file")
    out.add_argument("directory")
    update = commands.add_parser("update-export", help="Update unchanged managed notes")
    update.add_argument("file")
    update.add_argument("directory")
    search = commands.add_parser("search-crossref", help="Search scholarly metadata online")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    extract = commands.add_parser("extract", help="Extract text from a local document")
    extract.add_argument("source_file")
    extract.add_argument("destination_file")
    extract.add_argument("--ocr", action="store_true")
    extract.add_argument("--language", default="eng")
    transcribe = commands.add_parser("transcribe", help="Transcribe audio with a local model")
    transcribe.add_argument("source_file")
    transcribe.add_argument("destination_file")
    transcribe.add_argument("--model", required=True, help="Existing local model directory")
    local_search = commands.add_parser("search", help="Search project records")
    local_search.add_argument("file")
    local_search.add_argument("query")
    local_search.add_argument("--documents", action="store_true")
    report = commands.add_parser("research-report", help="Report research gaps")
    report.add_argument("file")
    importer = commands.add_parser("import-document", help="Extract and register a local source")
    importer.add_argument("file")
    importer.add_argument("source_file")
    importer.add_argument("destination_file")
    markdown = commands.add_parser("import-markdown", help="Convert a local document and register its source")
    markdown.add_argument("file")
    markdown.add_argument("source_file")
    markdown.add_argument("destination_file")
    youtube = commands.add_parser("import-youtube", help="Import available YouTube captions")
    youtube.add_argument("file")
    youtube.add_argument("url")
    youtube.add_argument("destination_file")
    webpage = commands.add_parser("import-web", help="Fetch a public HTML page into Markdown")
    webpage.add_argument("file")
    webpage.add_argument("url")
    webpage.add_argument("destination_file")
    find_video = commands.add_parser("search-youtube", help="Find YouTube videos using yt-dlp")
    find_video.add_argument("query")
    find_video.add_argument("--limit", type=int, default=5)
    bundle = commands.add_parser("backup-bundle", help="Back up a project and selected files")
    bundle.add_argument("file")
    bundle.add_argument("destination_file")
    bundle.add_argument("--include", action="append", default=[])
    restore_bundle = commands.add_parser("restore-bundle", help="Restore to a new directory")
    restore_bundle.add_argument("source_file")
    restore_bundle.add_argument("destination_file")
    outline = commands.add_parser("import-outline", help="Import an indented outline")
    outline.add_argument("file")
    outline.add_argument("outline")
    task = commands.add_parser("add-research-task")
    task.add_argument("file")
    task.add_argument("question")
    task.add_argument("--node")
    task.add_argument("--priority", choices=["low", "normal", "high"], default="normal")
    evidence = commands.add_parser("add-evidence")
    evidence.add_argument("file")
    evidence.add_argument("claim")
    evidence.add_argument("source")
    evidence.add_argument("locator")
    evidence.add_argument("--note", default="")
    citations = commands.add_parser("export-csl", help="Export bibliography as CSL JSON")
    citations.add_argument("file")
    citations.add_argument("destination_file")
    task_status = commands.add_parser("set-task-status")
    task_status.add_argument("file")
    task_status.add_argument("task")
    task_status.add_argument("status", choices=["pending", "in_progress", "done"])
    reviewed = commands.add_parser("review-source")
    reviewed.add_argument("file")
    reviewed.add_argument("source")
    reviewed.add_argument("date", help="YYYY-MM-DD")
    compare = commands.add_parser("compare", help="Compare two project snapshots")
    compare.add_argument("before")
    compare.add_argument("after")
    comp = commands.add_parser("add-competency")
    comp.add_argument("file")
    comp.add_argument("title")
    comp.add_argument("--node")
    comp.add_argument("--level", default="")
    comp.add_argument("--evidence", default="")
    path = commands.add_parser("add-learning-path")
    path.add_argument("file")
    path.add_argument("title")
    path.add_argument("competencies", nargs="+")
    due = commands.add_parser("schedule-review")
    due.add_argument("file")
    due.add_argument("source")
    due.add_argument("date")
    bib = commands.add_parser("export-bibtex")
    bib.add_argument("file")
    bib.add_argument("destination_file")
    duplicates = commands.add_parser("suggest-duplicates")
    duplicates.add_argument("file")
    merge = commands.add_parser("merge-nodes")
    merge.add_argument("file")
    merge.add_argument("keep")
    merge.add_argument("remove")
    rebase = commands.add_parser("rebase-paths")
    rebase.add_argument("file")
    rebase.add_argument("old_root")
    rebase.add_argument("new_root")
    web = commands.add_parser("web", help="Browse and import sources using a local web page")
    web.add_argument("file")
    web.add_argument("--port", type=int, default=8000)
    commands.add_parser("doctor")
    for name in ("backup", "restore"):
        sub = commands.add_parser(name)
        sub.add_argument("source_file")
        sub.add_argument("destination_file")
    args = parser.parse_args()
    try:
        if args.command == "web":
            from .web_viewer import create_server
            if not 0 <= args.port <= 65535:
                raise ValueError("port must be between 0 and 65535")
            server = create_server(args.file, args.port)
            print(f"Local workspace: http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nViewer stopped.")
            finally:
                server.server_close()
            return
        if args.command == "search-youtube":
            import json
            from .youtube_import import search_youtube
            print(json.dumps(search_youtube(args.query, args.limit), ensure_ascii=False, indent=2))
            return
        if args.command == "compare":
            import json
            from .research import compare_projects
            print(json.dumps(compare_projects(load(args.before), load(args.after)), indent=2))
            return
        if args.command in {"backup-bundle", "restore-bundle"}:
            from .backup import backup_bundle, restore_bundle
            if args.command == "backup-bundle":
                backup_bundle(args.file, args.destination_file, args.include)
            else:
                restore_bundle(args.source_file, args.destination_file)
            print(args.destination_file)
            return
        if args.command in {"extract", "transcribe"}:
            from .documents import extract_text, transcribe
            if args.command == "extract":
                extract_text(args.source_file, args.destination_file, ocr=args.ocr, language=args.language)
            else:
                transcribe(args.source_file, args.destination_file, model_path=args.model)
            print(args.destination_file)
            return
        if args.command == "search-crossref":
            import json
            from .crossref import search
            print(json.dumps(search(args.query, args.limit), ensure_ascii=False, indent=2))
            return
        if args.command == "doctor":
            print(f"Python {sys.version.split()[0]}: {'OK' if sys.version_info >= (3, 10) else 'requires 3.10+'}")
            for tool in ("git", "yt-dlp", "ffmpeg", "codex", "claude", "obsidian-mcp"):
                print(f"{tool}: {shutil.which(tool) or 'not found'}")
            return
        if args.command in {"backup", "restore"}:
            save(load(args.source_file), args.destination_file)
            print(args.destination_file)
            return
        if args.command == "create":
            project = create_project(args.title, args.description)
            if args.outline:
                for line in Path(args.outline).read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        add_node(project, line.strip())
            save(project, args.file)
            print(project["id"])
            return
        project = load(args.file)
        if args.command == "rebase-paths":
            from .knowledge_tools import rebase_paths
            count = rebase_paths(project, args.old_root, args.new_root)
            save(project, args.file, overwrite=True)
            print(count)
        elif args.command == "suggest-duplicates":
            import json
            from .dedup import suggest_nodes
            print(json.dumps(suggest_nodes(project), indent=2))
        elif args.command == "merge-nodes":
            from .dedup import merge_nodes
            result = merge_nodes(project, args.keep, args.remove)
            save(project, args.file, overwrite=True)
            print(result)
        elif args.command in {"add-competency", "add-learning-path", "schedule-review"}:
            from .competencies import add_competency, add_path
            from .research import schedule_review
            if args.command == "add-competency":
                result = add_competency(project, args.title, node=args.node, level=args.level, evidence=args.evidence)
            elif args.command == "add-learning-path":
                result = add_path(project, args.title, args.competencies)
            else:
                result = schedule_review(project, args.source, args.date)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "export-bibtex":
            from .research import export_bibtex
            with open(args.destination_file, 'x', encoding='utf-8') as handle:
                handle.write(export_bibtex(project))
            print(args.destination_file)
        elif args.command in {"review-source", "set-task-status"}:
            from .research import review_source, set_task_status
            result = review_source(project, args.source, args.date) if args.command == "review-source" else set_task_status(project, args.task, args.status)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "export-csl":
            import json
            from .research import export_csl
            with open(args.destination_file, 'x', encoding='utf-8') as handle:
                json.dump(export_csl(project), handle, ensure_ascii=False, indent=2)
                handle.write('\n')
            print(args.destination_file)
        elif args.command in {"import-outline", "add-research-task", "add-evidence"}:
            from .research import add_evidence, add_task, import_outline
            if args.command == "import-outline":
                result = import_outline(project, Path(args.outline).read_text(encoding="utf-8"))
            elif args.command == "add-research-task":
                result = add_task(project, args.question, node=args.node, priority=args.priority)
            else:
                result = add_evidence(project, args.claim, args.source, args.locator, args.note)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command in {"search", "research-report"}:
            import json
            from .knowledge_tools import research_report, search_project
            result = search_project(project, args.query, documents=args.documents) if args.command == "search" else research_report(project)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "import-web":
            from .web_import import import_web
            result = import_web(project, args.url, args.destination_file)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "import-youtube":
            from .youtube_import import import_youtube
            result = import_youtube(project, args.url, args.destination_file)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "import-markdown":
            from .markdown_import import import_to_markdown
            result = import_to_markdown(project, args.source_file, args.destination_file)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "import-document":
            from .knowledge_tools import import_document
            result = import_document(project, args.source_file, args.destination_file)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "show":
            import json
            print(json.dumps(project, ensure_ascii=False, indent=2))
        elif args.command == "audit":
            print("OK" if not audit(project) else "\n".join(audit(project)))
        elif args.command == "export":
            export(project, args.directory)
            print(args.directory)
        elif args.command == "update-export":
            import json
            print(json.dumps(update_export(project, args.directory), indent=2))
        else:
            if args.command == "add-node":
                result = add_node(project, args.title, args.description)
            elif args.command == "add-view":
                result = add_view(project, args.title, args.kind)
            elif args.command == "add-source":
                result = add_source(project, args.title, url=args.url, author=args.author, accessed=args.accessed, locator=args.locator)
                result.update(year=args.year, publisher=args.publisher, publication_type=args.publication_type)
            elif args.command == "add-claim":
                result = add_claim(project, args.text, sources=args.source, nodes=args.node, status=args.status)
            else:
                result = add_edge(project, args.source, args.target, args.type, args.view)
            save(project, args.file, overwrite=True)
            print(result["id"])
    except (OSError, ValueError, zipfile.BadZipFile, http.client.HTTPException, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
