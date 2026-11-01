# Architecture and evolution

Python's standard library is sufficient for a local MVP, tests, and simple distribution. A database would provide querying and concurrency but would add migrations before the model has been validated. JSON makes small projects easy to inspect and exchange; it does not solve concurrent writes. Writes use a temporary file and atomic replacement, and creation rejects existing destinations.

A version 1 project contains an ID, title, description, nodes, edges, and views. Every entity has a stable UUID. An edge connects IDs, has a type, and may belong to a view. A view may be a hierarchy, network, or pathway; a node can participate in multiple views without duplication. Prerequisite cycles are rejected globally and classification cycles per view. Broken references and identical titles are detected. Duplicate detection is literal and does not establish semantic equivalence.

Logical responsibilities: the user or agent initially handles context and competencies; the core stores nodes, edges, and views; the auditor checks integrity; storage persists JSON; and export generates Markdown. Instructions in sources are not executed. An imported description or line is not considered a verified claim.

Planned, not implemented: Curriculum references views and goals; Competency references abilities and evidence of mastery; Source preserves provenance and locators; Evidence links claims to sources and statuses such as established, limited, interpretation, pending, contradicted, or outdated; ResearchTask tracks research and its status; AuditResult records findings. These concepts are distinct from hierarchical depth. Their schemas and migrations must be defined before implementation.

Phase 2: authorized research, source traceability, and review of contradictions. Phase 3: a local stdio MCP adapter reusing the core, with no network or remote server; proposed tools are analyze_curriculum, create_knowledge_map, expand_knowledge_node, get_knowledge_node, search_knowledge, get_related_nodes, list_research_tasks, audit_curriculum, and export_to_obsidian. Phase 4: personalized pathways, exercises, and assessment. A Codex plugin and ChatGPT connection are future possibilities.

Project skill paths follow the official documentation for [Codex](https://developers.openai.com/blog/skills-agents-sdk) and [Claude Code](https://code.claude.com/docs/en/skills). Both symbolic links point to one source. Filesystem resolution is tested; actual discovery depends on the client version and restart.
