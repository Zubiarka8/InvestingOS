# Managing project skills

Skills are instructions and may include scripts or network access. Read the skill and its supporting files, review the source and license, and follow the user's permissions before using them. Installing a skill does not authorize its scripts, network access, or changes to personal data.

## How this project stores skills

- `skills/` is the single source directory for the project skill, individual third-party skills, and the original collections in `skills/collections/`.
- The selected `.agents/skills/` or `.claude/skills/` directory contains generated symbolic links to those sources. Several clients document the shared path; see [AI client compatibility](ai-clients.md). Claude Code uses its own links. Discovery depends on each client and version.
- `skills/manifest.json` records the source path for each bundled skill; `python scripts/install.py` checks it and creates the core skill link; use `--skill NAME` for selected extras or `--all-skills` for the whole bundle.
- [The index](../skills/INDEX.md) helps select a skill. The [README](../README.md#skill-credits-and-versions) records attribution and available versions.

The directories `.agents/skills/` and `.claude/skills/`, when selected, are discovery adapters, not separate collections: the project entries are links to the sources in `skills/`. The global directories in a user's home folder are independent installations shared with other projects; the installer does not move or remove them. A relevant global skill is not automatically safe to redistribute: check its complete license, provenance, companion files, and dependencies before adding it to this public repository. `research`, `find-docs`, and `find-skills` were identified as potentially relevant, but the inspected local copies did not identify a redistribution license. `last30days` declares MIT and version 3.30.0, but its complete local file set and accompanying notices have not been matched to an upstream revision. These are not bundled.

The installer creates links on systems with symbolic-link support; generated discovery directories are not tracked. Check that a link resolves, then restart the client and check its available skills. Link resolution alone does not prove that a client has loaded a skill. Some skills require tools, plugins, companion agents, or services that are not installed by copying the files.

## Add a skill from a URL

Ask your agent, for example: “Install the skill at `https://github.com/OWNER/REPO` in this project for my selected AI client. Review its instructions, license, dependencies, and version; preserve attribution; and verify the links.” The agent must use available authorized tools and report anything it cannot verify. The request does not itself make every script in the repository trustworthy.

### Agent workflow for one skill or a pack

When the user asks to install a skill, carry out the installation in this project; do not stop at describing the procedure. Use the URL, name, and requested scope to determine the selection:

- A URL or path pointing to one `SKILL.md` or skill directory selects that skill. Preserve any companion files it actually needs.
- A request for a pack, collection, or all skills selects the discoverable skills in that collection. Inventory the `SKILL.md` files and retain their relative paths, shared resources, attribution, and license notices. Group the pack under one named source directory; do not flatten its contents.
- A repository URL with exactly one skill selects it. If it contains multiple skills and the user has not indicated whether to install one or all, inspect the repository and ask which selection they want before installing. If it contains no skill, explain what it provides and do not label it a skill.

For every selected skill, check its declared name and requirements, and create discovery links for the shared and Claude-compatible paths pointing to the same project-owned source only for requested clients. Check for name collisions before changing anything: never overwrite an existing skill. Report any conflicting names and resolve them only when the intended behavior is clear. A pack may have shared dependencies or plugin-specific components; do not claim full compatibility merely because a link exists. Do not automatically install dependencies or execute third-party scripts.

After installation, add the selected discovery names and project-relative source directories to `skills/manifest.json`, then run `python scripts/install.py --skill NAME` for the selected skill or `python scripts/install.py --all-skills` for the complete bundle, with the appropriate `--client` option. Record the source URL, author or upstream, exact commit or release where verified, license, installed skill names and known limitations. Update the index and README credits. Verify that every selected skill has a readable `SKILL.md` through each requested link, and separately test client discovery if available. Report the selection and any unverified steps. If access, license, permissions, or a required client capability blocks the work, explain the blocker rather than fabricating a successful installation.

For a manual installation:

1. Identify the exact repository and skill directory. Download or clone it into a temporary directory; record the repository URL and exact commit or release. Do not execute downloaded scripts.
2. Inspect `SKILL.md`, supporting files, symlinks, dependencies, and the complete license. Check that redistribution is permitted and preserve required notices. A repository can contain several skills or depend on a plugin rather than a standalone skill.
3. Copy the reviewed source and its required files into a new, clearly named location under `skills/` (keep collections together in `skills/collections/`). Preserve the license and attribution. Do not overwrite an existing skill or use a link to a temporary directory. If redistribution is unclear, do not copy it into this public repository until resolved.
4. Add the reviewed skill to `skills/manifest.json`, then use `python scripts/install.py --skill NAME` with the requested `--client` option to create discovery links. Run the installer from the repository root. On Windows, `py -3` can select Python. Never overwrite an existing destination.

5. Add its purpose to [the index](../skills/INDEX.md), and its source, author, license, exact revision or declared version, and any limitations to the README. Mark unknown information explicitly.
6. Confirm each requested link resolves to the intended `SKILL.md`. Restart the selected client and check discovery when possible. Report separately whether filesystem links and actual client discovery were tested.

## Update or remove a skill

For an update, review the new revision, license, dependencies, and changes before replacing the source. Preserve a backup, keep the directory name stable where possible, update credits and the index, and recheck the selected links. Do not claim a version without evidence tying the installed files to it.

To remove a skill, first identify whether other links or workflows depend on its source. Remove its selected project links and its source only when no other skill needs it; then update the manifest, index, and credits. Never remove user data or global skills as part of project cleanup.

## Material held back from the public package

Third-party material whose redistribution cannot be verified stays on disk in the git-ignored `local-only/` directory, with its original relative path. It is never listed in `skills/manifest.json`, and `scripts/install.py` refuses to link it. `tests/test_skill_distribution.py` checks this. To release something from `local-only/`, confirm the license file and copyright holder at the upstream commit, move it back, then restore its manifest entry, index entry, credits and review row.
