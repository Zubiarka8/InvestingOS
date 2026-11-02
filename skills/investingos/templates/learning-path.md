---
id: "{{existing_or_new_learning_path_uuid}}"
type: "learning-path"
title: "{{path_title}}"
project_id: "{{project_uuid}}"
project_title: "{{project_title}}"
status: "draft"
---

# {{path_title}}

> This is an InvestingOS learning-path note. Keep its UUID and project metadata aligned with the canonical path record. Inside tables, write the wikilink separator as `\|`, as in the rows below.

> A learning path is a proposed order for reaching a goal. It is a view over canonical competencies and knowledge notes, not a second copy of their content or proof that a learner completed them.

## Intended learner and outcome

- **Audience:** {{who_this_path_is_for}}
- **Goal:** {{observable_end_capability_or_outcome}}
- **Scope:** {{included_topics_or_competencies}}
- **Exclusions:** {{what_this_path_does_not_cover}}
- **Assumed prior knowledge:** {{entry_knowledge_or_none_identified}}
- **Constraints:** {{time_access_language_tools_or_other_constraints}}
- **Estimated effort:** {{estimate_with_basis_or_not_estimated}}

State assumptions explicitly. Do not present a time estimate as a promise; explain the assumed pace and prior experience or omit it.

## Entry criteria

- **Required before starting:** {{knowledge_or_capability_and_how_to_check}}
- **If not met:** {{preparatory_step_or_no_route_defined}}

Do not add prerequisites just to create a longer route. Link to canonical nodes or competencies when available.

## Ordered stages

Add or remove rows to match the goal. Each competency should appear once in the main sequence unless repetition is intentional and explained. Reuse competency IDs and keep their definitions and evidence in their own canonical notes.

| Order | Competency | Why this stage is here | Suggested activity or resource | Readiness evidence / exit criterion |
| --- | --- | --- | --- | --- |
| 1 | [[{{existing_competency_uuid}}\|{{competency_title}}]] | {{foundation_or_dependency_reason}} | {{linked_resource_or_activity_or_not_defined}} | {{observable_check_or_not_defined}} |
| 2 | [[{{existing_competency_uuid}}\|{{competency_title}}]] | {{dependency_or_progression_reason}} | {{linked_resource_or_activity_or_not_defined}} | {{observable_check_or_not_defined}} |

The rationale should explain dependency or progression, not just repeat the competency title. If stages are alternatives, show them as branches rather than implying every learner must complete all of them.

## Branches and adaptations

| If the learner... | Recommended route | Reason and trade-off |
| --- | --- | --- |
| {{condition_or_none}} | [[{{alternative_path_uuid}}\|{{alternative_path_title}}]] | {{why_this_route_fits_and_what_it_omits}} |

Remove this table if there are no supported alternatives. Do not imply personalization or progress tracking is automatic.

## Supporting knowledge and sources

- **Knowledge node:** [[{{existing_node_uuid}}|{{knowledge_node_title}}]]: {{how_it_supports_the_path}}
- **Source or learning resource:** [[{{existing_source_uuid}}|{{source_title}}]]: {{specific_section_or_use}}

Link only resources that exist and are suitable for this audience. State if a resource has not been reviewed. Avoid copying its material into the path.

## Completion and limitations

- **Completion evidence:** {{evidence_needed_for_the_goal}}
- **Quality threshold:** {{criteria_or_not_defined}}
- **What completion does not establish:** {{unassessed_skills_contexts_or_credential_limits}}
- **Further progression:** [[{{next_path_or_competency_uuid}}|{{next_step_title_or_none}}]]

Completion means the listed evidence was reviewed against the stated criteria. It does not automatically establish broad professional competence, formal accreditation or transfer to unassessed contexts.

## Maintenance

- **Path owner or reviewer:** {{role_or_not_recorded}}
- **Last reviewed:** {{YYYY-MM-DD_or_unknown}}
- **Review trigger:** {{goal_changed_evidence_changed_resource_unavailable_or_none}}
- **Open questions:** {{questions_or_none}}

### Before saving

- Confirm the path is not a duplicate with a different title but the same audience, goal and sequence. `audit` does not compare paths.
- Check every competency is canonical, linked correctly and ordered for a stated reason.
- Check by hand that the stages do not contradict the competencies' own prerequisites. `audit` checks that a stored path has no repeated or missing competencies and that node `requires` edges have no cycle; it does not read these Markdown tables or competency prerequisites.
- Keep optional branches distinct from required stages and explain any estimated time.
- Remove unavailable links, unsupported claims, unused sections and all placeholders.
