"""Command-line interface; all mutations are explicit."""
import argparse
import http.client
import zipfile
import shutil
import subprocess
import sys
from pathlib import Path
from .core import CLAIM_STATUSES, PROFILE_FIELDS, RELATIONS, SOURCE_LIBRARY_STATUSES, add_claim, add_edge, add_node, add_source, add_view, audit, create_project, move_node, remove_edge, rename_node, set_node_notes, set_source_status, set_study_profile
from .export import export, update_export
from .storage import load, save


def main():
    parser = argparse.ArgumentParser(prog="InvestingOS")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("file")
    create.add_argument("title")
    create.add_argument("--description", default="")
    create.add_argument("--outline", help="UTF-8 text file; one topic per nonempty line")
    for field in PROFILE_FIELDS:
        create.add_argument("--" + field.replace("_", "-"), default="")
    profile = commands.add_parser("set-profile", help="Set study goals and learner context")
    profile.add_argument("file")
    for field in PROFILE_FIELDS:
        profile.add_argument("--" + field.replace("_", "-"))
    note = commands.add_parser("set-note", help="Set Markdown study notes for a knowledge node")
    note.add_argument("file")
    note.add_argument("node")
    note_input = note.add_mutually_exclusive_group(required=True)
    note_input.add_argument("--text", help="Markdown text to store")
    note_input.add_argument("--input-file", help="UTF-8 Markdown file to read")
    note_draft = commands.add_parser("draft-note", help="Create a source-aware Markdown study-note scaffold")
    note_draft.add_argument("file")
    note_draft.add_argument("node")
    note_draft.add_argument("destination_file")
    rename = commands.add_parser("rename-node", help="Rename a node without changing its stable ID")
    rename.add_argument("file")
    rename.add_argument("node")
    rename.add_argument("title")
    rename.add_argument("--description")
    move = commands.add_parser("move-node", help="Move or reorder a node in one hierarchy view")
    move.add_argument("file")
    move.add_argument("node")
    move.add_argument("view")
    move.add_argument("--parent", help="New parent node; omit to make the node a root")
    move.add_argument("--position", type=int, help="1-based sibling or root position")
    unlink = commands.add_parser("remove-edge", help="Remove a relationship without deleting its nodes")
    unlink.add_argument("file")
    unlink.add_argument("edge")
    migrate = commands.add_parser("migrate", help="Upgrade an older project schema and retain a history snapshot")
    migrate.add_argument("file")
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
    for option in ("year", "publisher", "publication-type", "media-type"):
        source.add_argument("--" + option, default="")
    source.add_argument("--library-status", choices=sorted(SOURCE_LIBRARY_STATUSES), default="inbox")
    source_status = commands.add_parser("set-source-status", help="Change a source's library workflow status")
    source_status.add_argument("file")
    source_status.add_argument("source")
    source_status.add_argument("status", choices=sorted(SOURCE_LIBRARY_STATUSES))
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
    pubmed = commands.add_parser("search-pubmed", help="Search PubMed (NCBI E-utilities) online")
    pubmed.add_argument("query")
    pubmed.add_argument("--limit", type=int, default=10)
    ora = commands.add_parser("lookup-ora", help="Fetch one Oxford Research Archive (ORA) record by UUID or URL")
    ora.add_argument("reference")
    from .open_sources import SOURCES as open_sources
    commands.add_parser("list-sources", help="List the open scholarly sources and what each one covers")
    source = commands.add_parser("search-source", help="Search one open scholarly or scientific source online")
    source.add_argument("source", choices=sorted(open_sources))
    source.add_argument("query")
    source.add_argument("--limit", type=int, default=10)
    source.add_argument("--provider", help="osf only: preprint server id such as psyarxiv or socarxiv")
    source.add_argument("--preprints", action="store_true", help="europepmc only: preprints only")
    preprint = commands.add_parser("lookup-preprint", help="Fetch one bioRxiv or medRxiv preprint by DOI")
    preprint.add_argument("doi")
    preprint.add_argument("--server", choices=("biorxiv", "medrxiv"), default="biorxiv")
    bank = commands.add_parser("worldbank-data", help="Fetch annual values of a World Bank indicator for a country")
    bank.add_argument("country")
    bank.add_argument("indicator")
    bank.add_argument("--limit", type=int, default=10)
    fund = commands.add_parser("imf-data", help="Fetch annual values of an IMF DataMapper indicator for a country")
    fund.add_argument("country")
    fund.add_argument("indicator")
    fund.add_argument("--limit", type=int, default=10)
    bce = commands.add_parser("ecb-data", help="Fetch the latest observations of a European Central Bank series")
    bce.add_argument("series", help="dataflow/key, for example EXR/D.USD.EUR.SP00.A")
    bce.add_argument("--limit", type=int, default=10)
    quakes = commands.add_parser("usgs-earthquakes", help="List recent earthquakes above a magnitude from the USGS catalogue")
    quakes.add_argument("--min-magnitude", type=float, default=6.0)
    quakes.add_argument("--limit", type=int, default=10)
    retraction = commands.add_parser("check-retraction", help="Look for retraction or correction notices for one DOI")
    retraction.add_argument("doi")
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
    folder_import = commands.add_parser("import-folder", help="Batch-import supported files from a source folder")
    folder_import.add_argument("file")
    folder_import.add_argument("source_directory")
    folder_import.add_argument("output_directory")
    index_docs = commands.add_parser("index-documents", help="Build or refresh the local full-text document index")
    index_docs.add_argument("file")
    index_docs.add_argument("--rebuild", action="store_true")
    search_docs = commands.add_parser("search-documents", help="Search indexed extracted documents")
    search_docs.add_argument("file")
    search_docs.add_argument("query")
    search_docs.add_argument("--limit", type=int, default=20)
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
        if args.command in {"list-sources", "search-source", "lookup-preprint", "worldbank-data", "imf-data", "ecb-data", "usgs-earthquakes", "check-retraction"}:
            import json
            from . import open_sources as sources
            if args.command == "list-sources":
                output = [{"id": key, "name": item["name"], "field": item["field"], "about": item["about"],
                           "api_key": "not needed"} for key, item in sorted(sources.SOURCES.items())]
            elif args.command == "search-source":
                options = {}
                if args.provider is not None:
                    if args.source != "osf":
                        raise ValueError("--provider only applies to the osf source")
                    options["provider"] = args.provider
                if args.preprints:
                    if args.source != "europepmc":
                        raise ValueError("--preprints only applies to the europepmc source")
                    options["preprints"] = True
                output = sources.SOURCES[args.source]["func"](args.query, args.limit, **options)
            elif args.command == "lookup-preprint":
                output = sources.preprint(args.doi, args.server)
            elif args.command == "check-retraction":
                output = sources.retractions(args.doi)
            elif args.command == "usgs-earthquakes":
                output = sources.earthquakes(args.min_magnitude, args.limit)
            elif args.command == "ecb-data":
                output = sources.ecb(args.series, args.limit)
            elif args.command == "imf-data":
                output = sources.imf(args.country, args.indicator, args.limit)
            else:
                output = sources.worldbank(args.country, args.indicator, args.limit)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return
        if args.command == "lookup-ora":
            import json
            from .ora import lookup
            print(json.dumps(lookup(args.reference), ensure_ascii=False, indent=2))
            return
        if args.command == "search-pubmed":
            import json
            from .pubmed import search
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
            project = create_project(args.title, args.description,
                                     study_profile={field: getattr(args, field) for field in PROFILE_FIELDS if getattr(args, field)})
            if args.outline:
                for line in Path(args.outline).read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        add_node(project, line.strip())
            save(project, args.file)
            print(project["id"])
            return
        project = load(args.file)
        if args.command == "draft-note":
            from .study_notes import draft_note
            with open(args.destination_file, "x", encoding="utf-8", newline="\n") as handle:
                handle.write(draft_note(project, args.node))
            print(args.destination_file)
        elif args.command == "migrate":
            if getattr(project, "migrated_from", None) is None:
                print(f"Project already uses schema version {project['schema_version']}")
            else:
                old_version = project.migrated_from
                save(project, args.file, overwrite=True)
                print(f"Migrated schema version {old_version} to {project['schema_version']}")
        elif args.command == "import-folder":
            import json
            from .source_library import import_folder
            result = import_folder(project, args.source_directory, args.output_directory)
            if result["imported"]:
                save(project, args.file, overwrite=True)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "index-documents":
            import json
            from .document_index import index_documents
            print(json.dumps(index_documents(args.file, project, rebuild=args.rebuild), ensure_ascii=False, indent=2))
        elif args.command == "search-documents":
            import json
            from .document_index import search_documents
            print(json.dumps(search_documents(args.file, project, args.query, limit=args.limit), ensure_ascii=False, indent=2))
        elif args.command == "set-profile":
            values = {field: getattr(args, field) for field in PROFILE_FIELDS if getattr(args, field) is not None}
            if not values:
                raise ValueError("provide at least one study profile field")
            set_study_profile(project, **values)
            save(project, args.file, overwrite=True)
            print("Study profile updated")
        elif args.command == "set-note":
            notes = Path(args.input_file).read_text(encoding="utf-8") if args.input_file else args.text
            result = set_node_notes(project, args.node, notes)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "rename-node":
            result = rename_node(project, args.node, args.title, args.description)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "move-node":
            result = move_node(project, args.node, args.view, parent_id=args.parent, position=args.position)
            save(project, args.file, overwrite=True)
            print(result["id"] if result else "Node moved to hierarchy root")
        elif args.command == "remove-edge":
            result = remove_edge(project, args.edge)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "set-source-status":
            result = set_source_status(project, args.source, args.status)
            save(project, args.file, overwrite=True)
            print(result["id"])
        elif args.command == "rebase-paths":
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
                result = add_source(project, args.title, url=args.url, author=args.author, accessed=args.accessed,
                                    locator=args.locator, media_type=args.media_type)
                result.update(year=args.year, publisher=args.publisher, publication_type=args.publication_type,
                              library_status=args.library_status)
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
