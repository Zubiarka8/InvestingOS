# Project operations

Use the root `README.md` as the current source for installation, supported Python versions, examples, test status, third-party credits and license notices. Consult `--help` for exact command arguments and `references/source-management.md` for source imports, storage, Markdown provenance and viewer details. Do not claim a platform, integration or version has been tested unless the README or an actual check confirms it.

## Installation and clients

- Run `scripts/install.py` with a supported Python interpreter. Its default activates the main skill in the shared discovery path; opt into other clients or skills only as requested. The installer checks the manifest and does not replace existing files or remove earlier links. Restart the chosen client and independently verify discovery. Windows needs suitable symbolic-link permissions. Client paths are adapters, not engine dependencies.
- For another skill or collection, follow `docs/skills-management.md`: inspect and pin the source, check licenses, select requested skills, preserve attribution, configure only requested clients, and update the index and credits. Consult `docs/ai-clients.md`, `skills/INDEX.md` and `docs/research-tools.md` as needed. Optional integrations and third-party dependencies are not automatically installed. Review unresolved third-party provenance and licenses before redistribution.

## Create, structure and inspect

- Use `create` to initialize a project and `show` to inspect it. For a simple UTF-8 topic list, `create --outline` makes one node per nonempty line and does not interpret indentation. For an indented hierarchy added to an existing project, `import-outline` expects two spaces per level and rejects duplicate titles and skipped levels. Preserve the input.
- Create concepts with `add-node`, views with `add-view`, and relationships with `add-edge`; use returned stable IDs. `contains` points parent to child, `part_of` child to parent, and `requires` topic to prerequisite. Reuse nodes across views. Expand only the requested branch and avoid concurrent project writers.
- Run `audit` to check integrity, duplicate titles and IDs, and cycles; it cannot identify every semantic duplicate or verify claims. `suggest-duplicates` proposes title matches; inspect them before any explicit `merge-nodes`. A merge preserves removed metadata and ID in the retained node, but the removed ID is not a lookup alias.

## Research and competencies

- Register sources and claims with `add-source` and `add-claim`; link relevant nodes and source IDs. Claims default to `unverified`; `supported`, `disputed`, and `outdated` are user assessments. Supported claims require a source but this is not automatic verification.
- `add-research-task` and `set-task-status` track investigations. `add-evidence` records a locator for a source already linked to a claim; `review-source` records a manual review date, and `schedule-review` tracks a future review. None automatically verifies claims or establishes freshness. Use `research-report` to inspect recorded gaps and contradiction edges, not to claim automatic contradiction discovery.
- `search-crossref` retrieves online scholarly metadata leads when network access is available and authorized; verify the sources. `export-csl` and `export-bibtex` output recorded bibliographic fields without inventing missing information.
- Use `add-competency` to describe a capability, node, configurable level and expected evidence; use `add-learning-path` for an ordered competency sequence. These levels are not official qualifications and are separate from thematic depth. Personalized lessons, progress tracking and financial analysis are not implemented.

## Local viewer and export

- `web PROJECT` starts a local-only viewer; use `--port` as needed and stop it with Ctrl+C. The viewer displays topics, relationships, indexes, sources, claims, evidence, competencies, paths and tasks. Editing outside import uses the CLI; refresh after changes. Its search filters the selected section and does not search document bodies.
- The superindex numbers the `contains` and `part_of` relationships assigned to each view; it can show the same concept in several branches. Numbers reflect positions and may change; node IDs remain stable. Views without hierarchical relationships have no indexed topics.
- For the selected page, Word export provides an approximate preview and editable DOCX. PDF uses browser print/save, with final pagination controlled by the browser. Neither provides a full-project export or verified pixel-identical rendering. See the source management reference for import form storage and source sections.
- `export` writes an Obsidian-compatible Markdown snapshot to a new directory. `update-export` only updates eligible unchanged managed notes; it reports conflicts, preserves user edits and deletions, and does not remove notes for removed nodes. Older snapshots lacking a manifest cannot be updated. Back up the vault and avoid concurrent edits.

## History, backup and diagnostics

- Project overwrites retain a previous JSON snapshot in `.investing-os-history/<project-id>/` beside the project. History can contain private data, grows with edits and is not automatically pruned. `compare` compares snapshots from the same project; `restore` writes a selected snapshot to a new destination.
- `doctor` reports available Python and optional executables; it does not verify their versions or connectivity. `backup` and `restore` cover project JSON only and refuse existing destinations.
- `backup-bundle` includes the project plus only explicitly selected files or folders; it refuses symlinks and existing destinations. `restore-bundle` validates and restores to a new directory. Archives are unencrypted and do not preserve empty directories. Stored paths continue pointing at original locations; `rebase-paths` requires existing targets, checks available hashes and uses the current OS path format.
- Keep personal data and credentials outside the public repository, inspect what a backup includes, and never publish or delete user files without authorization. Use the README's development and test instructions for verification, reporting skipped checks and actual interpreter versions.
