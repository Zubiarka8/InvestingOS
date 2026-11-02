---
id: "{{existing_or_new_node_uuid}}"
type: "knowledge-node"
title: "{{canonical_title}}"
project_id: "{{project_uuid}}"
project_title: "{{project_title}}"
status: "unverified"
aliases: []
---

# {{canonical_title}}

> This is an InvestingOS knowledge note. Keep its UUID and project metadata aligned with the canonical project record. `status` uses the same values as exported notes: `unverified`, or `draft-unverified` while the text is still a scaffold. `aliases` exists only in this frontmatter; the JSON project has no alias field.

> Use one note for one reusable knowledge item. Keep the title specific enough to distinguish it from neighboring concepts. The node UUID, not this title, is its identity.

## Short definition

{{one_or_two_sentence_definition_stating_what_it_is_and_the_context_of_use}}

If meanings vary by field or author, identify the usage instead of presenting one definition as universal.

## Explanation

{{how_or_why_the_item_works_matters_or_is_interpreted}}

Expand only when a detail deserves its own note, and link to that note instead of copying a long explanation.

## Scope and distinctions

- **Included:** {{ideas_or_features_that_belong_to_this_node}}
- **Excluded:** {{nearby_ideas_that_belong_in_other_nodes}}
- **Distinguish from:** [[{{different_node_uuid}}|{{similar_but_distinct_concept}}]]: {{key_difference}}

Alternate names for the same concept go in the `aliases` frontmatter list. A related or contrasting concept must have its own node and link.

## Examples and counterexamples

- **Example:** {{brief_concrete_example_and_why_it_fits}}
- **Non-example:** {{near_miss_and_why_it_does_not_fit}}

Use examples appropriate to the subject and learner. Do not present a hypothetical example as a real event, dataset or case.

## Structure and cross-links

- **Parent in this view:** [[{{existing_parent_node_uuid}}|{{parent_title}}]]
- **Related concepts:** [[{{existing_related_node_uuid}}|{{related_title}}]]
- **Prerequisite:** [[{{existing_prerequisite_node_uuid}}|{{prerequisite_title}}]]
- **Application or method:** [[{{existing_application_node_uuid}}|{{application_title}}]]
- **Further detail:** [[{{existing_complementary_note_uuid}}|{{detail_title}}]]

Keep only links that exist and add a short reason if the relationship is not clear from its context. Use InvestingOS relationship edges for changes to the project graph. Different classifications should reuse this node's ID, not make another copy.

## Claims and sources

<!-- Use one bullet per material claim. Add a source locator so a reader can find the supporting passage. -->

- **Claim:** {{precise_checkable_claim}}
  - **Source:** [[{{existing_source_uuid}}|{{source_title}}]]
  - **Locator:** {{page_section_timestamp_or_unknown}}
  - **Status:** {{unverified_supported_disputed_or_outdated}}
  - **Qualification:** {{limits_context_or_competing_interpretation}}

Separate a source's statement from your interpretation. When evidence disagrees, record the competing accounts and their provenance instead of combining them into false certainty. A linked source does not prove a claim.

## Study notes

### Core takeaway

{{one_concise_point_a_learner_should_remember}}

### Common confusion

{{likely_misconception_and_correction_or_remove}}

### Recall or application prompt

{{question_or_small_task_that_checks_understanding}}

Use only the subsections that help the learner. Put full exercises, lessons or assessments in the appropriate learning materials rather than duplicating them here.

## Open questions and review

- **Unresolved questions:** {{questions_or_none}}
- **Known limitations:** {{scope_or_evidence_limitations_or_none}}
- **Last reviewed:** {{YYYY-MM-DD_or_unknown}}
- **Review trigger:** {{new_evidence_changed_definition_or_none}}

### Before saving

- Confirm the ID and project match the canonical JSON entity.
- Search for an existing node with the same meaning, not only the same title (`audit` flags identical titles only); reuse it if appropriate.
- Ensure this note explains one item and points to related detail rather than repeating it.
- Check that every source link and locator is real, and preserve uncertainty.
- Remove unused sections, instructional text and all `{{placeholders}}`.
