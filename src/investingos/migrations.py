"""Sequential, additive migrations for persisted project schemas."""
from copy import deepcopy

from .core import PROFILE_FIELDS, SCHEMA_VERSION

CURRENT_SCHEMA_VERSION = SCHEMA_VERSION


def _v1_to_v2(project):
    profile = {field: "" for field in PROFILE_FIELDS}
    legacy_profile = project.get("study_profile", {})
    if not isinstance(legacy_profile, dict):
        raise ValueError("cannot migrate an invalid study profile")
    profile.update(legacy_profile)
    project["study_profile"] = profile
    for node in project.get("nodes", []):
        node.setdefault("notes", "")
    for view in project.get("views", []):
        view.setdefault("root_order", [])
    for source in project.get("sources", []):
        source.setdefault("library_status", "inbox")
        source.setdefault("media_type", "")
    project["schema_version"] = 2
    return project


MIGRATIONS = {1: _v1_to_v2}


def migrate_project(project):
    migrated = deepcopy(project)
    version = migrated.get("schema_version")
    if not isinstance(version, int):
        raise ValueError("project schema version is missing or invalid")
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(f"project schema version {version} is newer than supported version {CURRENT_SCHEMA_VERSION}")
    while version < CURRENT_SCHEMA_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(f"no migration is available from schema version {version}")
        migrated = migration(migrated)
        version = migrated.get("schema_version")
    return migrated
