"""Set up bundled project skill links without changing global configuration."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


CLIENT_DIRS = {"shared": ".agents", "claude": ".claude"}
HELD_BACK_DIR = "local-only"


def install(root, clients=("shared",), names=None):
    if not clients or any(client not in CLIENT_DIRS for client in clients):
        raise ValueError("choose at least one supported client path")
    clients = tuple(dict.fromkeys(clients))
    if sys.version_info < (3, 10):
        raise ValueError("Python 3.10 or later is required")
    root = root.resolve()
    manifest = json.loads((root / "skills/manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("invalid skill manifest")
    if names is not None:
        missing = set(names) - manifest.keys()
        if missing:
            raise ValueError("unknown skills: " + ", ".join(sorted(missing)))
        manifest = {name: manifest[name] for name in dict.fromkeys(names)}
    pending = []
    for name, relative in manifest.items():
        if not isinstance(name, str) or not name or name in {".", ".."} or Path(name).name != name:
            raise ValueError(f"invalid skill name: {name!r}")
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError(f"invalid source for {name}")
        target = (root / relative).resolve()
        # local-only/ holds third-party material excluded from the public package.
        if target.is_relative_to(root / HELD_BACK_DIR):
            raise ValueError(f"{name} points to held-back material ({relative}); it cannot be installed")
        if not target.is_relative_to(root) or not (target / "SKILL.md").is_file():
            raise ValueError(f"missing or invalid source for {name}: {relative}")
        for client in clients:
            directory = root / CLIENT_DIRS[client] / "skills"
            # Do not follow a client directory outside the checkout.
            if not directory.resolve().is_relative_to(root):
                raise ValueError(f"invalid skills directory: {directory}")
            link = directory / name
            if link.is_symlink():
                if link.resolve() != target:
                    raise ValueError(f"conflicting link: {link}")
            elif link.exists():
                raise ValueError(f"destination already exists: {link}")
            else:
                pending.append((link, target))
    for link, target in pending:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=True)
    print(f"Ready: {len(manifest)} skills for {', '.join(clients)} ({len(pending)} links created).")
    print("Run python scripts/investingos.py --help from this repository (Python 3.10+).")
    print("Restart your AI client and verify discovery; see docs/ai-clients.md.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", action="append", choices=sorted(CLIENT_DIRS),
                        help="Select a project skill discovery path; repeat to select both (default: shared).")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--skill", action="append", help="Install only the named skill; repeat to select more.")
    selection.add_argument("--all-skills", action="store_true", help="Install every skill in the manifest.")
    args = parser.parse_args()
    try:
        install(ROOT, clients=args.client or ("shared",), names=None if args.all_skills else (args.skill or ("investingos",)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        if os.name == "nt":
            print("Windows requires working symbolic links; see README.md.", file=sys.stderr)
        raise SystemExit(1) from exc
