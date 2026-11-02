# Architecture and evolution

## Current model

InvestingOS is a local, discipline-independent knowledge graph. Python's standard library supports the core. A project is a versioned JSON document with stable UUIDs, study-profile metadata, knowledge nodes, typed edges, views, source records, claims, evidence, competencies, learning paths and research tasks. Existing v1 projects are migrated additively to v2 when loaded; `migrate` saves the new format and keeps a v1 history snapshot. The versioned schemas are in `schemas/`.

Nodes represent reusable concepts. Views provide independent hierarchies, networks and pathways over those concepts. Classification edges are scoped to a view; prerequisite edges are checked for cycles globally. The audit catches broken references, invalid IDs, duplicate titles and structural cycles. Duplicate detection is title based and cannot establish semantic equivalence. The superindex is recursive and has no fixed depth limit; its numbers represent current positions, while UUIDs remain stable.

Projects can store learner context and goal separately from topic depth. Each node may hold a Markdown study note; claims and source records keep provenance separate from authored explanations. Imported documents remain external files with recorded paths and checksums. Conversion and source registration do not establish that a claim is true.

The Obsidian adapter exports one note per node and source, a `sources.md` library grouped by media type, stable IDs, internal links, citations and a view-aware nested index. `update-export` refreshes unchanged generated files and reports conflicts for user-edited or removed notes. It is a one-way managed export, not bidirectional synchronization. Arbitrary Obsidian edits do not flow back into the JSON project.

## Storage and safety

Atomic JSON writes, recoverable snapshots, explicit schema migrations and optimistic revision checks support local use. An exclusive lock prevents overlapping InvestingOS writers; a stale lock left by a crash needs manual inspection. This does not provide shared editing or remote synchronization. Extracted text can be indexed incrementally in a local SQLite FTS5 sidecar; it contains private text and is git-ignored. JSON remains the source of truth. Imported files are preserved; project records can point to unavailable paths if files are moved or removed. Backups include only paths selected by the user.

Research, source records and claims can be stored. Available importers handle selected local document formats, supported public HTML and available YouTube captions. External retrieval uses explicitly invoked tools; no unattended or automatic fact verification is implied. Web and client integrations are adapters over the local core, not mandatory services.

## Next expansion areas

1. **Source-library lifecycle:** review-before-delete/relocate operations, richer user-defined collection metadata and source facets. Preserve originals and never infer a fixed subject taxonomy.
2. **Study-note authoring:** goal-specific template customization and note revision history. Five optional Markdown authoring templates are available now; the current source-aware scaffold surfaces linked claims, but the AI assistant must read sources and write the synthesis.
3. **Large-library retrieval:** metadata filters, index progress reporting and configurable resource limits. Keep extracted text and private originals outside Git.
4. **Obsidian views:** optional Canvas or Bases output when it can be generated from the same graph without creating a second source of truth. Preserve the simple Markdown export as the portable baseline.
5. **Collaboration:** shared editing, remote synchronization and merge behavior are not implemented. A database or remote sync would require a separate design and explicit security review.

Do not add an MCP server, cloud backend or discipline-specific taxonomy to the core without a demonstrated need. A future local stdio MCP adapter should call the same core operations; it should not duplicate their logic.
