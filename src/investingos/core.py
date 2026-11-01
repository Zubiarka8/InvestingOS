"""Versioned knowledge projects and integrity checks."""
from collections import defaultdict
from uuid import UUID, uuid4

RELATIONS = {"contains", "part_of", "requires", "related_to", "supports", "contradicts", "alternative_to"}


def identifier():
    return str(uuid4())


def create_project(title, description=""):
    if not title.strip():
        raise ValueError("title must not be empty")
    return {"schema_version": 1, "id": identifier(), "title": title, "description": description,
            "nodes": [], "edges": [], "views": []}


def add_node(project, title, description=""):
    if not title.strip():
        raise ValueError("title must not be empty")
    node = {"id": identifier(), "title": title, "description": description}
    project["nodes"].append(node)
    return node


def add_edge(project, source, target, kind, view=None):
    if kind not in RELATIONS:
        raise ValueError("unknown relation")
    ids = {n["id"] for n in project["nodes"]}
    if source not in ids or target not in ids:
        raise ValueError("edge references a missing node")
    if view is not None and view not in {v["id"] for v in project["views"]}:
        raise ValueError("edge references a missing view")
    edge = {"id": identifier(), "source": source, "target": target, "type": kind, "view": view}
    project["edges"].append(edge)
    problems = audit(project)
    if any(p.startswith("cycle:") for p in problems):
        project["edges"].pop()
        raise ValueError("edge creates a cycle")
    return edge


def add_view(project, title, kind="hierarchy"):
    if not title.strip() or kind not in {"hierarchy", "network", "pathway"}:
        raise ValueError("invalid view")
    view = {"id": identifier(), "title": title, "kind": kind}
    project["views"].append(view)
    return view


CLAIM_STATUSES = {"unverified", "supported", "disputed", "outdated"}


def add_source(project, title, *, url="", author="", accessed="", locator=""):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("source title must not be empty")
    if not all(isinstance(value, str) for value in (url, author, accessed, locator)):
        raise ValueError("source fields must be text")
    source = {"id": identifier(), "title": title, "url": url, "author": author,
              "accessed": accessed, "locator": locator}
    project.setdefault("sources", []).append(source)
    return source


def add_claim(project, text, *, sources=(), nodes=(), status="unverified"):
    if not isinstance(text, str) or not text.strip() or status not in CLAIM_STATUSES:
        raise ValueError("invalid claim")
    sources = list(sources)
    if any(source not in {item["id"] for item in project.get("sources", [])} for source in sources):
        raise ValueError("claim references a missing source")
    nodes = list(nodes)
    if any(node not in {item["id"] for item in project["nodes"]} for node in nodes):
        raise ValueError("claim references a missing node")
    if status == "supported" and not sources:
        raise ValueError("supported claims require a source")
    claim = {"id": identifier(), "text": text, "sources": sources, "status": status}
    if nodes:
        claim["nodes"] = nodes
    project.setdefault("claims", []).append(claim)
    return claim


def audit(project):
    errors = []
    try:
        if project["schema_version"] != 1:
            return ["unsupported schema version"]
        nodes, edges, views = project["nodes"], project["edges"], project["views"]
        sources, claims = project.get("sources", []), project.get("claims", [])
        tasks, evidence = project.get("research_tasks", []), project.get("evidence", [])
        competencies, paths = project.get("competencies", []), project.get("learning_paths", [])
        if not isinstance(competencies, list) or not isinstance(paths, list):
            raise ValueError("competencies and paths must be lists")
        if not isinstance(tasks, list) or not isinstance(evidence, list):
            raise ValueError("research tasks and evidence must be lists")
        if not isinstance(sources, list) or not isinstance(claims, list):
            raise ValueError("sources and claims must be lists")
        all_ids = [project["id"]] + [x["id"] for x in nodes + edges + views + sources + claims + tasks + evidence + competencies + paths]
        for value in all_ids:
            try:
                if not isinstance(value, str) or str(UUID(value)) != value:
                    raise ValueError("noncanonical UUID")
            except (ValueError, TypeError, AttributeError):
                errors.append("invalid identifier: " + str(value))
        if len(all_ids) != len(set(all_ids)):
            errors.append("duplicate identifier")
        ids = {n["id"] for n in nodes}
        view_ids = {v["id"] for v in views}
        titles = set()
        for node in nodes:
            title = node["title"].strip().casefold()
            if not title:
                errors.append("empty node title")
            if title in titles:
                errors.append("duplicate title: " + node["title"])
            titles.add(title)
        source_ids = {source["id"] for source in sources}
        for source in sources:
            if not all(isinstance(source[key], str) for key in ("title", "url", "author", "accessed", "locator")) or not source["title"].strip():
                errors.append("invalid source: " + source["id"])
        for claim in claims:
            if (not isinstance(claim["text"], str) or not claim["text"].strip() or
                    claim["status"] not in CLAIM_STATUSES or not isinstance(claim["sources"], list)):
                errors.append("invalid claim: " + claim["id"])
                continue
            if any(source not in source_ids for source in claim["sources"]):
                errors.append("broken source: " + claim["id"])
            if not isinstance(claim.get("nodes", []), list) or any(node not in ids for node in claim.get("nodes", [])):
                errors.append("broken claim node: " + claim["id"])
            if claim["status"] == "supported" and not claim["sources"]:
                errors.append("unsupported claim: " + claim["id"])
        claim_ids = {claim["id"] for claim in claims}
        for task in tasks:
            if (not isinstance(task["question"], str) or not task["question"].strip() or
                    task["priority"] not in {"low", "normal", "high"} or
                    task["status"] not in {"pending", "in_progress", "done"} or
                    (task["node"] is not None and task["node"] not in ids)):
                errors.append("invalid research task: " + task["id"])
        for item in evidence:
            if (item["claim"] not in claim_ids or item["source"] not in source_ids or
                    not isinstance(item["locator"], str) or not item["locator"].strip() or
                    not isinstance(item["note"], str)):
                errors.append("invalid evidence: " + item["id"])
            elif item["source"] not in next(c for c in claims if c["id"] == item["claim"])["sources"]:
                errors.append("evidence source not linked to claim: " + item["id"])
        competency_ids = {item["id"] for item in competencies}
        for item in competencies:
            if (not all(isinstance(item[k], str) for k in ("title", "level", "evidence")) or not item["title"].strip() or
                    (item["node"] is not None and item["node"] not in ids)):
                errors.append("invalid competency: " + item["id"])
        for item in paths:
            if (not isinstance(item["title"], str) or not item["title"].strip() or
                    not isinstance(item["competencies"], list) or not item["competencies"] or
                    len(item["competencies"]) != len(set(item["competencies"])) or
                    any(c not in competency_ids for c in item["competencies"])):
                errors.append("invalid learning path: " + item["id"])
        graphs = defaultdict(lambda: defaultdict(list))
        for edge in edges:
            source, target, kind, view = edge["source"], edge["target"], edge["type"], edge["view"]
            if source not in ids or target not in ids:
                errors.append("broken edge: " + edge["id"])
            if view is not None and view not in view_ids:
                errors.append("broken view: " + edge["id"])
            if kind not in RELATIONS:
                errors.append("unknown relation: " + str(kind))
            if kind == "requires":
                graphs[("requires", None)][source].append(target)
            if kind in {"contains", "part_of"}:
                a, b = (source, target) if kind == "contains" else (target, source)
                graphs[("hierarchy", view)][a].append(b)
        for (kind, view), graph in graphs.items():
            done, active = set(), set()
            for start in list(graph):
                stack = [(start, False)]
                while stack:
                    node, leaving = stack.pop()
                    if leaving:
                        active.discard(node)
                        done.add(node)
                    elif node in active:
                        errors.append(f"cycle: {kind} {view or 'global'}")
                        stack.clear()
                        active.clear()
                        break
                    elif node not in done:
                        active.add(node)
                        stack.append((node, True))
                        stack.extend((child, False) for child in graph.get(node, []))
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        errors.append("malformed project: " + str(exc))
    return errors
