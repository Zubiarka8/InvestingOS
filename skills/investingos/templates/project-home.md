---
type: "project-home"
project_id: "{{existing_project_uuid}}"
project_title: "{{project_title}}"
status: "active"
---

# {{project_title}}

> This page is a navigation and orientation layer. The InvestingOS JSON project is canonical for graph entities, relationships, competencies, paths and source metadata.

## Project purpose

- **Goal:** {{specific_learning_or_research_outcome}}
- **Audience:** {{intended_audience_or_unknown}}
- **Prior knowledge:** {{known_prerequisites_or_unknown}}
- **Scope:** {{included_topics_or_questions}}
- **Out of scope:** {{explicit_exclusions_or_not_defined}}
- **Desired depth:** {{requested_depth_or_not_defined}}
- **Constraints:** {{time_access_language_or_other_constraints}}
- **Project language:** {{language}}

Write the goal as an outcome, not merely a broad subject label. Keep unknown details explicit; do not fill gaps with assumptions.

## Start here

<!-- Link to actual exported index or node files. Remove rows for views that do not exist. Do not repeat the links listed under Navigation. In table cells write the wikilink separator as `\|`. -->

| View or destination | What it organizes | Entry point |
| --- | --- | --- |
| {{view_title}} | {{classification_concept_map_timeline_or_pathway_rule}} | [[{{existing_node_uuid}}\|{{entry_title}}]] |

## Navigation

- **Knowledge index:** [[index|{{project_title}} index]]
- **Source library:** [[sources|Source library]]
- **Main study path:** [[{{existing_path_note_uuid}}|{{path_title_or_no_path_yet}}]]
- **Competency map:** [[{{existing_competency_note_uuid}}|{{competency_title_or_not_recorded}}]]

Competency and learning-path notes are not part of the generated export, so link them only after you have created those notes.

Replace each placeholder link with a real target. If the relevant note does not exist, write `Not created` instead of leaving a dangling link.

## Project conventions

- **Canonical project file:** {{private_path_or_not_recorded}}
- **Canonical note identity:** Existing InvestingOS entity UUIDs
- **Source and citation policy:** {{project_specific_policy_or_default_project_rules}}
- **Naming or language conventions:** {{conventions_or_none}}

Do not put credentials or private absolute paths in notes that may be published.

## Current state

- **Completed:** {{brief_completed_work_or_none}}
- **In progress:** {{active_branches_or_tasks_or_none}}
- **Open questions:** {{important_unresolved_questions_or_none}}
- **Known limitations:** {{gaps_or_none}}

Keep this section current and concise. Link to the canonical branch, research task or decision note; do not reproduce its detail here.

## Decisions

| Decision | Reason | Date | Evidence or discussion |
| --- | --- | --- | --- |
| {{decision_or_none}} | {{reason_or_unknown}} | {{YYYY-MM-DD_or_unknown}} | [[{{source_or_note_uuid}}\|{{target_title}}]] |

Add a row only for a decision that affects how the project is structured or interpreted. Do not use this table as a general activity log.

## Review

- **Last reviewed:** {{YYYY-MM-DD_or_unknown}}
- **Review trigger:** {{goal_changed_new_evidence_or_other_trigger}}
- **Next review:** {{YYYY-MM-DD_or_not_scheduled}}

### Before saving

- Keep this note short enough to orient a new reader. Do not copy the topic tree, source list, node descriptions or competency definitions into it; link to their canonical pages and to the exported `index.md` and `sources.md`.
- Check that every link resolves or reads `Not created`.
- Remove unused rows, comments and all `{{placeholders}}`.
