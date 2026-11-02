"""Safe local JSON persistence."""
import json
import hashlib
import os
from pathlib import Path
import tempfile
import weakref
from uuid import uuid4
from .core import audit


class Project(dict):
    """Dictionary-compatible project carrying a non-serialized load revision."""
    __hash__ = object.__hash__
    __eq__ = object.__eq__

    def __init__(self, value):
        super().__init__(value)
        self.migrated_from = None


_REVISIONS = weakref.WeakKeyDictionary()


def _digest(path):
    import hashlib
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load(path):
    path = Path(path)
    raw = path.read_bytes()
    original = json.loads(raw.decode('utf-8'))
    if not isinstance(original, dict):
        raise ValueError("project file must contain a JSON object")
    original_version = original.get('schema_version')
    from .migrations import CURRENT_SCHEMA_VERSION, migrate_project
    project = Project(migrate_project(original))
    project.migrated_from = original_version if original_version != CURRENT_SCHEMA_VERSION else None
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    _REVISIONS[project] = (str(path.resolve()), hashlib.sha256(raw).hexdigest())
    return project


def save(project, path, *, overwrite=False):
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".InvestingOS-")
    lock = path.with_name('.' + path.name + '.lock')
    lock_fd = None
    lock_owned = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            lock_owned = True
        except FileExistsError as exc:
            raise ValueError(f'project is being written or has a stale lock: {lock}') from exc
        with os.fdopen(lock_fd, 'w', encoding='utf-8') as handle:
            lock_fd = None
            handle.write(str(os.getpid()))
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise ValueError('refusing to overwrite a symbolic link')
        revision = _REVISIONS.get(project) if isinstance(project, Project) else None
        resolved_path = str(path.resolve())
        if overwrite:
            if path.exists():
                if revision and revision[0] == resolved_path and _digest(path) != revision[1]:
                    raise ValueError('project changed after it was loaded; reload it before saving')
                previous = load(path)
                if previous['id'] != project['id']:
                    raise ValueError('cannot overwrite a different project')
                history = path.parent / '.InvestingOS-history' / project['id']
                history.mkdir(parents=True, exist_ok=True)
                snapshot = history / (str(uuid4()) + '.json')
                with path.open('rb') as original, snapshot.open('xb') as backup:
                    import shutil
                    shutil.copyfileobj(original, backup)
                    backup.flush()
                    os.fsync(backup.fileno())
            elif revision and revision[0] == resolved_path:
                raise ValueError('project was removed after it was loaded; reload before saving')
            os.replace(tmp, path)
        else:
            os.link(tmp, path)
            os.unlink(tmp)
        if isinstance(project, Project):
            _REVISIONS[project] = (resolved_path, hashlib.sha256(data.encode('utf-8')).hexdigest())
            project.migrated_from = None
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_owned:
            try:
                lock.unlink()
            except FileNotFoundError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)
