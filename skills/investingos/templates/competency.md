---
id: "{{existing_or_new_competency_uuid}}"
type: "competency"
title: "{{observable_capability}}"
project_id: "{{project_uuid}}"
project_title: "{{project_title}}"
node_id: "{{primary_knowledge_node_uuid_or_empty}}"
level: "{{project_defined_level_or_unspecified}}"
status: "draft"
---

# {{observable_capability}}

> This is an InvestingOS competency note. Keep its UUID and project metadata aligned with the canonical competency record. `node_id` is the knowledge node the competency is attached to in the JSON record; leave it empty if there is none. `level` and `status` live only in this frontmatter.

> A competency describes demonstrated capability. Topic coverage, attendance, confidence and time spent are not evidence of mastery by themselves.

## Outcome

After the relevant preparation, a learner can **{{observable_action}}** {{object_or_task}} **under {{conditions_and_context}}**, meeting **{{observable_quality_threshold}}**.

Use a specific action verb and observable result. Avoid vague outcomes such as “understand,” “know” or “be familiar with” unless followed by a task that makes the capability observable. Keep one primary capability per record; split it if the outcomes can be demonstrated independently.

## Competency dimensions

Keep only dimensions that apply. Do not infer practical or professional competence from theory alone.

- **Theoretical knowledge:** {{concepts_the_learner_can_explain_or_apply_or_not_applicable}}
- **Practical performance:** {{procedure_or_skill_the_learner_can_demonstrate_or_not_applicable}}
- **Professional context:** {{responsibility_constraints_or_work_context_or_not_applicable}}

## Related knowledge

- [[{{existing_node_uuid}}|{{knowledge_node_title}}]]: {{role_of_this_knowledge}}
- [[{{existing_related_node_uuid}}|{{related_node_title}}]]: {{optional_relationship}}

Link canonical knowledge nodes. Do not copy their explanations into this competency note. The first link should match `node_id`.

## Prerequisites

- [[{{existing_prerequisite_competency_uuid}}|{{prerequisite_competency_title}}]]: {{why_it_is_needed}}

List only necessary prerequisites, not every useful related skill. The JSON project has no competency prerequisite field and `audit` does not check these links, so read the prerequisites of each linked competency yourself and make sure none leads back to this one. If no prerequisite is established, write `None identified` and remove the example link.

## Demonstration and evidence

- **Task:** {{authentic_task_or_assessment_prompt}}
- **Context and resources:** {{conditions_tools_time_or_allowed_support}}
- **Evidence artifact:** {{observable_result_performance_or_explanation}}
- **Success criteria:**
  1. {{criterion_one_that_can_be_observed}}
  2. {{criterion_two_that_can_be_observed}}
  3. {{criterion_three_or_remove}}
- **Evidence source or rubric:** [[{{source_or_rubric_uuid}}|{{existing_reference_title}}]]: {{locator_or_not_applicable}}
- **What this evidence does not establish:** {{limits_of_the_assessment}}

Criteria should be specific enough that two reviewers can understand what counts as success. State the number and quality of demonstrations required if consistency matters. Do not imply that one task establishes capability in every context.

## Level and scope

- **Level description:** {{what_this_level_means_in_this_project}}
- **Transfer limits:** {{contexts_where_the_skill_has_not_been_demonstrated}}
- **Official standard:** {{linked_authoritative_standard_or_none}}

The level name is in the frontmatter. Levels are configurable descriptions, not official qualifications. If an official standard is relevant, cite the issuing body, version and exact section; do not imply endorsement or equivalence.

## Review

The workflow state is the `status` field in the frontmatter (for example draft, proposed, assessed, or another state your project defines).

- **Assessment method:** {{method_or_not_defined}}
- **Assessor:** {{name_role_or_not_recorded}}
- **Last reviewed:** {{YYYY-MM-DD_or_unknown}}
- **Open questions:** {{questions_or_none}}

### Before saving

- Search the project's competencies by meaning, not only title (`audit` does not look for duplicate competencies). Reuse the UUID if this one already exists.
- Check the outcome is observable, appropriately scoped and not a bundle of unrelated skills.
- Confirm prerequisites are real and check by hand that they do not create a cycle.
- Ensure evidence and criteria measure this capability and state their limits.
- Keep level descriptions configurable and separate from topic depth or formal credentials.
- Verify linked notes and references; remove unsupported claims and all placeholders.
