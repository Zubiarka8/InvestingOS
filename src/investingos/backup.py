"""Create and restore explicit, non-destructive ZIP backups."""
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

from .storage import load


def backup_bundle(project, destination, paths):
    project, destination = Path(project), Path(destination)
    load(project)
    inputs = [Path(path) for path in paths]
    for path in inputs:
        if path.is_symlink() or not path.exists():
            raise ValueError(f'invalid backup input: {path}')
        if path.is_dir() and any(item.is_symlink() for item in path.rglob('*')):
            raise ValueError(f'symbolic links are not supported: {path}')
        if path.is_dir() and destination.resolve().is_relative_to(path.resolve()):
            raise ValueError('backup destination must be outside input directories')
    with destination.open('xb') as handle:
        try:
            with zipfile.ZipFile(handle, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(project, 'project.json')
                archive.writestr('manifest.json', json.dumps({'version': 1, 'inputs': [p.name for p in inputs]}))
                for index, path in enumerate(inputs):
                    if path.is_file():
                        archive.write(path, f'data/{index}/{path.name}')
                    else:
                        for item in path.rglob('*'):
                            if item.is_file():
                                archive.write(item, f'data/{index}/{item.relative_to(path).as_posix()}')
        except Exception:
            handle.close()
            destination.unlink(missing_ok=True)
            raise


def restore_bundle(backup, destination):
    destination = Path(destination)
    with zipfile.ZipFile(backup) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries]
        if len(names) != len(set(names)) or not {'manifest.json', 'project.json'} <= set(names):
            raise ValueError('invalid backup')
        for item in entries:
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename or any(':' in part for part in path.parts) or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('invalid backup path')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('version') != 1:
            raise ValueError('unsupported backup')
        destination.mkdir(parents=True, exist_ok=False)
        try:
            for item in entries:
                if item.is_dir():
                    continue
                target = destination.joinpath(*PurePosixPath(item.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
            load(destination / 'project.json')
        except Exception:
            shutil.rmtree(destination)
            raise
