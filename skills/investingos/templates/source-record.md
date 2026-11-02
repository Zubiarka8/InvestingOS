---
id: "{{existing_or_new_source_uuid}}"
type: "source"
title: "{{source_title_as_published}}"
project_id: "{{project_uuid}}"
project_title: "{{project_title}}"
library_status: "inbox"
review_status: "not-reviewed"
media_type: "{{media_type_or_unknown}}"
---

# {{source_title_as_published}}

> This is an InvestingOS source note. Keep its UUID and project metadata aligned with the canonical source record. `library_status` (`inbox`, `processed` or `archived`) and `review_status` (`not-reviewed` or `reviewed`) use the same fields and values as exported source notes. Both live only in this frontmatter.

> One record identifies one source. Do not create multiple records for the same edition or file just because it supports several topics. Use the source UUID to link it from all relevant notes.

## Bibliographic identity

- **Author or issuing organization:** {{as_credited_or_unknown}}
- **Publication date:** {{YYYY-MM-DD_or_year_or_unknown}}
- **Publisher, journal or platform:** {{as_listed_or_unknown}}
- **Edition, version or identifier:** {{edition_version_doi_isbn_or_not_listed}}
- **Source type and format:** {{primary_secondary_review_dataset_video_etc_and_media_type}}
- **Language:** {{language_or_unknown}}
- **Stable URL:** {{canonical_url_or_not_available}}
- **Accessed or acquired:** {{YYYY-MM-DD_or_unknown}}
- **Local original:** {{private_relative_link_or_not_recorded}}
- **SHA-256:** {{recorded_checksum_or_not_recorded}}

Record only information actually available from the source or a trustworthy catalog. Preserve spelling and authorship as credited. Never guess DOI, author order, publication date, publisher or edition. Keep private absolute paths out of public notes.

## Scope and content

- **What it covers:** {{brief_neutral_description_of_scope}}
- **What it does not cover:** {{important_scope_limits_or_unknown}}
- **Relevant section or locator:** {{page_chapter_timestamp_table_or_unknown}}
- **Source role:** {{primary_evidence_background_review_methodology_dataset_or_other}}

Describe the material, not whether it is true. Do not reproduce long copyrighted passages; summarize briefly and cite precise locations.

## Linked knowledge and claims

- [[{{existing_node_uuid}}|{{knowledge_node_title}}]]: {{specific_relevance}}
- **Claim:** {{short_precise_claim_or_none_yet}}
  - **Locator:** {{locator_or_unknown}}
  - **Assessment:** {{unverified_supported_disputed_or_outdated}}
  - **Qualification:** {{limitations_or_interpretation}}

Use separate bullets for separate claims when they need different locators or assessments. A source-level review must not automatically mark every claim supported.

## Critical appraisal

- **Provenance:** {{who_created_it_and_under_what_context_or_unknown}}
- **Method or evidence base:** {{brief_description_or_not_applicable_or_unknown}}
- **Relevant strengths:** {{specific_strengths_or_not_assessed}}
- **Limitations, bias or conflicts:** {{specific_caveats_or_not_assessed}}
- **Currency:** {{whether_date_matters_and_why_or_not_assessed}}
- **Corroboration or disagreement:** [[{{other_source_uuid}}|{{other_source_title}}]]: {{agreement_conflict_or_not_checked}}

Do not assign a numeric quality score without a defined, relevant rubric. Clearly separate what the document says from the assistant's appraisal.

## Review record

Set `review_status` in the frontmatter. Use `reviewed` only when this record's metadata was checked against the source.

- **Reviewed by or method:** {{person_or_tool_and_scope_or_unknown}}
- **Last reviewed:** {{YYYY-MM-DD_or_unknown}}
- **Review due:** {{YYYY-MM-DD_or_not_scheduled}}
- **Remaining checks:** {{unverified_metadata_missing_full_text_or_none}}

Access, downloading, a checksum and a review date establish traceability or process history; they do not establish accuracy. Preserve the original file and update source metadata through InvestingOS when the JSON record is canonical.

### Before saving

- Search for this source by URL, title, DOI/ISBN or checksum and reuse the existing source ID if it is the same edition or file. `audit` does not detect duplicate sources.
- Distinguish a new edition or materially different document from a duplicate record.
- Verify every bibliographic field and locator against the source or a reliable catalog.
- Ensure links resolve, uncertainty is visible, private paths are protected and all placeholders are removed.
