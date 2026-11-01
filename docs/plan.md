# Implementation plan

Goal: a verifiable local core for knowledge projects without a fixed discipline.

1. Model a versioned graph with UUIDs, independent views, and typed relationships; validate references and cycles.
2. Add atomic JSON persistence, a CLI, and Markdown export without silent overwrites.
3. Provide one shared skill, architecture documentation, examples, and tests across three disciplines.

Acceptance: run `python3 -m unittest discover -s tests -v` and check persistence, depth, views, reuse, cycles, references, duplicates, export, and skill paths. No external services are required. The initial import treats each line as a topic; research, structured competencies, and MCP are later phases.
