# Managing imported sources and Markdown

Read the root README and `docs/research-tools.md` for current commands, optional dependencies and format-specific limitations. Do not infer a source was accessed, verified or successfully imported from its mere presence in a plan.

## Import and storage

1. Inspect the project, the selected input and the destination. Keep project data and user files outside the repository where practical. Preserve every original.
2. For local PDF, DOCX, XLSX, CSV, HTML, text or Markdown, `import-markdown PROJECT INPUT OUTPUT.md` converts the source, records its original and extracted paths and SHA-256, and refuses to overwrite the output. PDF and some other formats require optional dependencies; OCR is separate. The conversion does not establish the truth of the content. `import-document` extracts text separately and does not add a Markdown source section.
3. `import-web PROJECT URL OUTPUT.md` fetches supported public HTTPS HTML and saves a local HTML sidecar. `import-youtube PROJECT URL OUTPUT.md` saves available English or Spanish captions as a VTT sidecar; it does not download the video or transcribe absent captions. Both record the URL. Network access and any necessary tools must be available and authorized; never pretend a search or download occurred. The project records paths and provenance, not automatic fact-checking.
4. In the local web viewer's Import form, choose a source and optionally a storage root and slash-separated topic folders. With no root supplied, files go next to the project under `investing-os-data/<project-id>/temporary/`, followed by `pdf`, `documents`, `web` or `youtube`, optional user-chosen topics and a unique folder per import. Topics are user-defined, not a fixed taxonomy. Only the web form allocates this structure automatically; CLI import commands require an explicit output path.
5. Despite its name, this `temporary` directory is persistent and is not the system temporary directory. Keep outputs and sidecars until explicitly authorized to remove them. There is currently no cleanup interface or automatic promotion into permanent storage. Before removing or moving generated files, inspect project references and explain the impact; never delete original documents. The project can retain broken paths if files are removed. Where appropriate use `rebase-paths` after moving files and check the command's requirements.

## Sources in Markdown

- New `import-markdown`, `import-web` and `import-youtube` outputs include a `Sources` section linking the local original or recorded URL. Local links are relative where possible; moving files can break them and paths may disclose private information. Existing Markdown is not rewritten automatically.
- Obsidian export creates node notes and an index. A node note's `Sources` section contains sources linked through claims attached to that node. The index lists recorded sources. Notes without linked sources say so; do not invent references to fill the gap.
- To make a source appear on a node, register it with `add-source` or import it, and record a claim with both the node and source IDs using `add-claim`; consult `--help` for exact arguments. Preserve locators when known. A recorded link supports traceability, not verification; claims default to unverified and `supported` is a manual assessment, not an automated check.
- The exported source list does not assert that every statement is supported. Distinguish source provenance, claim-level evidence and confidence. Record contradictions and uncertainty; never fabricate authors, citations, links or page numbers.
- Export to a new directory; `update-export` updates only eligible managed notes and reports conflicts. Never silently overwrite user edits. A manual source list in unrelated or previously created Markdown is not automatically synchronized.

## Finding and presenting results

- `search PROJECT QUERY` searches project records. `search --documents` scans available extracted files, not a prebuilt index. The web search filters the selected section and does not search document bodies. The web superindex follows hierarchical relationships assigned to views; its numbering represents positions, not stable IDs.
- The viewer can preview and export the current page to Word, or open a browser print dialog for PDF. Word preview is approximate; direct PDF download and export of complete projects are not implemented. Do not claim visual fidelity or successful client/browser integration without verification.
- Report the project, output paths, source locations, any missing dependencies and unresolved verification. Before sharing, review local paths and source permissions; never publish private files or credentials without authorization.
