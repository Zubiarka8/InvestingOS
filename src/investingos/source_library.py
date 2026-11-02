"""Organize local source imports without modifying originals."""
from pathlib import Path

from .knowledge_tools import _hash
from .markdown_import import import_to_markdown

SUPPORTED_SUFFIXES = {".csv", ".docx", ".html", ".htm", ".md", ".pdf", ".txt", ".xlsx"}


def import_folder(project, source_directory, output_directory):
    source_root = Path(source_directory).resolve()
    output_root = Path(output_directory).resolve()
    if not source_root.is_dir():
        raise ValueError("source directory does not exist")
    if output_root == source_root or output_root.is_relative_to(source_root):
        raise ValueError("output directory must be outside the source directory")
    files = sorted(path for path in source_root.rglob("*")
                   if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUPPORTED_SUFFIXES)
    existing_hashes = {source.get("sha256") for source in project.get("sources", []) if source.get("sha256")}
    report = {"imported": [], "duplicates": [], "failed": []}
    for path in files:
        try:
            digest = _hash(path)
            if digest in existing_hashes:
                report["duplicates"].append(str(path.relative_to(source_root)))
                continue
            destination = output_root / path.relative_to(source_root).with_suffix(".md")
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = import_to_markdown(project, path, destination)
            existing_hashes.add(digest)
            report["imported"].append({"source_id": source["id"], "path": str(destination)})
        except Exception as exc:
            report["failed"].append({"path": str(path.relative_to(source_root)), "error": str(exc)})
    return report
