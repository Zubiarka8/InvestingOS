"""Create a source-aware study-note scaffold for a knowledge node."""
import json


def draft_note(project, node_id):
    node = next((item for item in project['nodes'] if item['id'] == node_id), None)
    if node is None:
        raise ValueError('node not found')
    sources = {item['id']: item for item in project.get('sources', [])}
    claims = [item for item in project.get('claims', []) if node_id in item.get('nodes', [])]
    lines = ["---", f'project_id: {json.dumps(project["id"])}',
             f'project_title: {json.dumps(project["title"], ensure_ascii=False)}',
             f'node_id: {json.dumps(node_id)}', 'status: "draft-unverified"',
             "---", "", "# " + node['title'], "", f'**Project:** [[index|{project["title"]}]]', "",
             "> Draft scaffold. Complete it from reviewed sources and keep claims linked to their evidence.", "",
             "## Summary", "", "<!-- Write a concise, source-grounded summary. -->", "",
             "## Explanation", "", "<!-- Explain the ideas in the learner's requested context and depth. -->", "",
             "## Examples", "", "<!-- Add examples only when supported or clearly marked as illustrative. -->", "",
             "## Review questions", "", "<!-- Add questions that check understanding, not just recall. -->", "",
             "## Evidence to incorporate", ""]
    if claims:
        for claim in claims:
            lines.append(f'- {claim["text"]} (status: {claim["status"]})')
            for source_id in claim.get('sources', []):
                source = sources[source_id]
                locator = f" — {source['locator']}" if source.get('locator') else ''
                lines.append(f'  - [[{source_id}|{source["title"]}]]{locator}')
    else:
        lines.append("No source-linked claims are attached to this node yet. Do not present its summary as verified.")
    return "\n".join(lines) + "\n"
