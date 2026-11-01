# Research Tooling Implementation Plan

**Goal:** Extend the local knowledge project with traceable research records and practical optional tooling.

**Architecture:** Keep the version 1 graph backward compatible, adding optional validated source and claim collections. Integrations use explicit local commands and do not mutate original documents or private vaults implicitly.

**Tech Stack:** Python 3.10+ standard library; optional third-party tools documented separately.

## Constraints

- Work across macOS, Windows and Linux; no mandatory service or API key.
- Do not claim unverified information is verified, overwrite user files silently, or install unreviewed dependencies.
- Preserve existing project IDs and files. Validate all references.

## Slices

1. Add source and claim records, validated references and CLI commands; test persistence and missing references.
2. Add local environment diagnostics and non-destructive project backup/restore; test success and collision handling.
3. Evaluate document import, external search, transcription and managed vault updates with their dependencies and safety requirements. Implement only integrations that can be verified end-to-end; report any remaining gaps explicitly.
4. Document requirements and run the existing suite and focused checks.
