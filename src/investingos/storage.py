"""Safe local JSON persistence."""
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from .core import audit


def load(path):
    with open(path, encoding="utf-8") as handle:
        project = json.load(handle)
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    return project


def save(project, path, *, overwrite=False):
    errors = audit(project)
    if errors:
        raise ValueError("invalid project: " + "; ".join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".investingos-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            if path.exists():
                previous = load(path)
                if previous['id'] != project['id']:
                    raise ValueError('cannot overwrite a different project')
                history = path.parent / '.investing-os-history' / project['id']
                history.mkdir(parents=True, exist_ok=True)
                snapshot = history / (str(uuid4()) + '.json')
                with path.open('rb') as original, snapshot.open('xb') as backup:
                    import shutil
                    shutil.copyfileobj(original, backup)
                    backup.flush()
                    os.fsync(backup.fileno())
            os.replace(tmp, path)
        else:
            os.link(tmp, path)
            os.unlink(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
