"""Versioned knowledge projects and integrity checks."""
from collections import defaultdict
import copy
from uuid import UUID, uuid4

RELATIONS = {"contains", "part_of", "requires", "related_to", "supports", "contradicts", "alternative_to"}
PROFILE_FIELDS = ("goal", "audience", "prior_knowledge", "scope", "depth", "constraints", "language")
SCHEMA_VERSION = 2


def identifier():
    return str(uuid4())


def create_project(title, description="", *, study_profile=None):
    if not title.strip():
        raise ValueError("title must not be empty")
    project = {"schema_version": SCHEMA_VERSION, "id": identifier(), "title": title, "description": description,
            "study_profile": {field: "" for field in PROFILE_FIELDS},
            "nodes": [], "edges": [], "views": []}
    if study_profile:
        set_study_profile(project, **study_profile)
    return project


def add_node(project, title, description=""):
    if not title.strip():
        raise ValueError("title must not be empty")
    node = {"id": identifier(), "title": title, "description": description, "notes": ""}
    project["nodes"].append(node)
    return node


def set_study_profile(project, **values):
    unknown = set(values) - set(PROFILE_FIELDS)
    if unknown:
        raise ValueError("unknown study profile fields: " + ", ".join(sorted(unknown)))
    if any(not isinstance(value, str) for value in values.values()):
        raise ValueError("study profile values must be text")
    profile = project.setdefault("study_profile", {field: "" for field in PROFILE_FIELDS})
    profile.update(values)
    return profile


def set_node_notes(project, node_id, notes):
    if not isinstance(notes, str):
        raise ValueError("study notes must be text")
    node = next((item for item in project["nodes"] if item["id"] == node_id), None)
    if node is None:
        raise ValueError("node not found")
    node["notes"] = notes
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
    if kind in {"contains", "part_of"} and view is not None:
        parent, child = (source, target) if kind == "contains" else (target, source)
        hierarchy = next(item for item in project["views"] if item["id"] == view)
        hierarchy["root_order"] = [item for item in hierarchy.get("root_order", []) if item != child]
        parent_has_parent = any(edge.get("view") == view and edge["type"] in {"contains", "part_of"} and
                                (edge["target"] if edge["type"] == "contains" else edge["source"]) == parent
                                for edge in project["edges"])
        if not parent_has_parent and parent not in hierarchy["root_order"]:
            hierarchy["root_order"].append(parent)
    return edge


def add_view(project, title, kind="hierarchy"):
    if not title.strip() or kind not in {"hierarchy", "network", "pathway"}:
        raise ValueError("invalid view")
    view = {"id": identifier(), "title": title, "kind": kind, "root_order": []}
    project["views"].append(view)
    return view


def rename_node(project, node_id, title, description=None):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must not be empty")
    node = next((item for item in project["nodes"] if item["id"] == node_id), None)
    if node is None:
        raise ValueError("node not found")
    if any(item["id"] != node_id and item["title"].strip().casefold() == title.strip().casefold()
           for item in project["nodes"]):
        raise ValueError("a node with this title already exists")
    if description is not None and not isinstance(description, str):
        raise ValueError("description must be text")
    node["title"] = title
    if description is not None:
        node["description"] = description
    return node


def move_node(project, node_id, view_id, *, parent_id=None, position=None):
    work = copy.deepcopy(project)
    node_ids = {node["id"] for node in work["nodes"]}
    view = next((item for item in work["views"] if item["id"] == view_id), None)
    if node_id not in node_ids or view is None:
        raise ValueError("node or view not found")
    if view["kind"] != "hierarchy":
        raise ValueError("nodes can only be moved in a hierarchy view")
    if parent_id is not None and parent_id not in node_ids:
        raise ValueError("parent node not found")
    if parent_id == node_id:
        raise ValueError("a node cannot contain itself")
    if position is not None and (not isinstance(position, int) or position < 1):
        raise ValueError("position must be a positive integer")

    def hierarchy_parent(edge):
        if edge.get("view") != view_id or edge["type"] not in {"contains", "part_of"}:
            return None
        return edge["source"] if edge["type"] == "contains" else edge["target"]

    incoming = [edge for edge in work["edges"]
                if edge.get("view") == view_id and edge["type"] in {"contains", "part_of"}
                and (edge["target"] if edge["type"] == "contains" else edge["source"]) == node_id]
    if len(incoming) > 1:
        raise ValueError("this node has multiple parents in the view; choose a parent relationship explicitly first")

    if parent_id is None:
        if incoming:
            work["edges"].remove(incoming[0])
        root_ids = [item[1]["id"] for item in outline(work, view_id) if len(item[0]) == 1]
        if node_id not in root_ids:
            root_ids.append(node_id)
        root_ids.remove(node_id)
        if position is not None and position > len(root_ids) + 1:
            raise ValueError("root position exceeds the available positions")
        index = len(root_ids) if position is None else position - 1
        root_ids.insert(index, node_id)
        view["root_order"] = root_ids
        moved = None
    else:
        if incoming:
            moved = incoming[0]
            moved.update(source=parent_id, target=node_id, type="contains")
        else:
            moved = {"id": identifier(), "source": parent_id, "target": node_id,
                     "type": "contains", "view": view_id}
            work["edges"].append(moved)
        view["root_order"] = [item for item in view.get("root_order", []) if item != node_id]
        problems = audit(work)
        if any(problem.startswith("cycle:") for problem in problems):
            raise ValueError("move would create a hierarchy cycle")
        siblings = [edge for edge in work["edges"] if hierarchy_parent(edge) == parent_id and
                    (edge["target"] if edge["type"] == "contains" else edge["source"]) != parent_id]
        siblings.sort(key=work["edges"].index)
        siblings = [edge for edge in siblings if edge["id"] != moved["id"]]
        if position is not None and position > len(siblings) + 1:
            raise ValueError("sibling position exceeds the available positions")
        index = len(siblings) if position is None else position - 1
        siblings.insert(index, moved)
        slots = [i for i, edge in enumerate(work["edges"]) if hierarchy_parent(edge) == parent_id]
        for slot, edge in zip(slots, siblings):
            work["edges"][slot] = edge

    project.clear()
    project.update(work)
    return moved


def remove_edge(project, edge_id):
    edge = next((item for item in project["edges"] if item["id"] == edge_id), None)
    if edge is None:
        raise ValueError("relationship not found")
    project["edges"].remove(edge)
    if edge.get("view") is not None and edge["type"] in {"contains", "part_of"}:
        parent, child = (edge["source"], edge["target"]) if edge["type"] == "contains" else (edge["target"], edge["source"])
        view = next(item for item in project["views"] if item["id"] == edge["view"])
        root_order = view.setdefault("root_order", [])
        if child not in root_order:
            root_order.append(child)
        parent_has_parent = any(other.get("view") == edge["view"] and other["type"] in {"contains", "part_of"} and
                                (other["target"] if other["type"] == "contains" else other["source"]) == parent
                                for other in project["edges"])
        if not parent_has_parent and parent not in root_order:
            root_order.append(parent)
    return edge


CLAIM_STATUSES = {"unverified", "supported", "disputed", "outdated"}
SOURCE_LIBRARY_STATUSES = {"inbox", "processed", "archived"}


def add_source(project, title, *, url="", author="", accessed="", locator="", media_type=""):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("source title must not be empty")
    if not all(isinstance(value, str) for value in (url, author, accessed, locator, media_type)):
        raise ValueError("source fields must be text")
    source = {"id": identifier(), "title": title, "url": url, "author": author,
              "accessed": accessed, "locator": locator, "library_status": "inbox",
              "media_type": media_type}
    project.setdefault("sources", []).append(source)
    return source


def set_source_status(project, source_id, status):
    if status not in SOURCE_LIBRARY_STATUSES:
        raise ValueError("invalid source library status")
    source = next((item for item in project.get("sources", []) if item["id"] == source_id), None)
    if source is None:
        raise ValueError("source not found")
    source["library_status"] = status
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
        if project["schema_version"] != SCHEMA_VERSION:
            return ["unsupported schema version"]
        nodes, edges, views = project["nodes"], project["edges"], project["views"]
        profile = project.get("study_profile", {})
        if not isinstance(profile, dict) or set(profile) != set(PROFILE_FIELDS) or any(not isinstance(value, str) for value in profile.values()):
            errors.append("invalid study profile")
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
        for view in views:
            root_order = view.get("root_order")
            if (not isinstance(root_order, list) or len(root_order) != len(set(root_order)) or
                    any(node not in ids for node in root_order)):
                errors.append("invalid root order: " + view["id"])
        titles = set()
        for node in nodes:
            title = node["title"].strip().casefold()
            if not title:
                errors.append("empty node title")
            if title in titles:
                errors.append("duplicate title: " + node["title"])
            titles.add(title)
            if not isinstance(node.get("notes"), str):
                errors.append("invalid study notes: " + node["id"])
        source_ids = {source["id"] for source in sources}
        required_source_fields = ("title", "url", "author", "accessed", "locator")
        optional_source_fields = ("local_path", "extracted_path", "sha256", "reviewed_at", "year", "media_type",
                                  "publisher", "publication_type", "review_due", "library_status")
        for source in sources:
            if (not all(isinstance(source[key], str) for key in required_source_fields) or
                    any(key in source and not isinstance(source[key], str) for key in optional_source_fields) or
                    not source["title"].strip() or "media_type" not in source or "library_status" not in source):
                errors.append("invalid source: " + source["id"])
            if source.get("library_status") not in SOURCE_LIBRARY_STATUSES:
                errors.append("invalid source library status: " + source["id"])
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
