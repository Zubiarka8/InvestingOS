# Development roadmap

InvestingOS is being developed as a universal, local knowledge workspace. This roadmap describes implementation status and the next useful extensions; it does not promise dates.

## Available now

- Create and persist local knowledge projects with stable UUIDs.
- Store learner goals and context, reusable concepts, multiple hierarchy/network/pathway views, relationships, competencies and learning paths.
- Rename nodes, detach relationships, move topics between parents and order roots or siblings without changing node IDs.
- Import indented outlines and supported local documents, public web pages and available YouTube captions while preserving originals and recording source metadata.
- Batch-import supported files from a folder, skip byte-identical sources and track workflow states from inbox to processed or archived.
- Build an incremental local SQLite FTS5 index for extracted document text and search it without a network service.
- Record claims, source links, evidence, research tasks and review dates; these records support traceability but do not automatically verify claims.
- Generate source-aware study-note scaffolds, add Markdown notes to individual nodes and inspect profiles and notes in the local viewer. The AI assistant writes the synthesis.
- Provide five optional Markdown templates for a project home, knowledge node, source record, competency and learning path, with UUID reuse and cross-linking rules.
- Export nested numbered hierarchy views, node notes, source notes and a source library grouped by media type to Obsidian-compatible Markdown; update managed exports without silently overwriting edited notes.
- Audit structural integrity, search project records and extracted documents, and explicitly migrate v1 projects to v2 with a history snapshot.
- Protect local saves with exclusive locks and stale-revision checks; this prevents lost updates among InvestingOS processes but is not shared collaboration.
- Install the universal project skill and selected bundled skills through the manifest.

## Next: content and source library management

1. Add review-before-delete/relocate operations and richer user-defined source metadata filters for large collections.
2. Add goal-specific template customization and note revision history while retaining source-linked claims and user-authored content.
3. Add search filters, index progress reporting and configurable resource controls for large libraries.
4. Consider richer Obsidian Canvas or Bases views as optional exports generated from the existing graph.

## Later

- Add shared editing, merge-aware collaboration and remote synchronization only after a separate data and security design.
- Add a local stdio MCP adapter that reuses core operations, with explicit write controls.
- Add personalized lessons, exercises, evaluation and progress tracking using the existing competency model.
- Evaluate plugin packaging only when the core and skill workflows demonstrate a need.

Keep the core provider independent, offline-capable for local work, and free of fixed subject taxonomies. Any online research must use tools that are actually available and authorized, and clearly distinguish recorded evidence from verified conclusions.
