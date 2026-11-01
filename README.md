# InvestingOS

InvestingOS helps you organize knowledge about any subject. Build a map of topics, connect ideas, keep track of sources and explore your work locally.

**Status:** Early development. The core runs locally. Sources and claims can be recorded, but their accuracy must be checked by a person.

## Get started

With Git installed, download the project:

```text
git clone https://github.com/Zubiarka8/investingOS.git
cd investingOS
```

You need **Python 3.10 or later** on macOS, Windows or Linux. Python 3.14 is recommended. The core does not require an online service or additional Python packages.

The test suite has run on macOS with Python 3.11.12 and 3.14.7, with one test skipped because local network access was blocked. Other versions and operating systems have not yet been verified. See the [version details](docs/user-guide.md#python-test-status).

Install the main skill:

```text
python scripts/install.py
```

On Windows, use `py -3 scripts/install.py`. Windows may require permission to create symbolic links. If `python` points to an older version, use a supported interpreter such as `python3.14` or `py -3.14`.

To create a project and open the local viewer:

```text
python scripts/investingos.py create ../my-project.json "My knowledge"
python scripts/investingos.py web ../my-project.json
```

Open the local address printed by the command in your browser. On Windows, replace `python` with `py -3`. Keep personal projects and documents outside the repository.

## What you can do

- Organize topics into reusable maps and explore them through search and an expandable index.
- Import outlines and supported documents, web pages and YouTube captions. Some formats require optional tools or internet access.
- Record sources, claims, research tasks, competencies and learning paths; check the structure for common problems.
- Export notes for Obsidian and preview the current viewer page for Word or PDF. Saving a PDF uses the browser's print dialog.
- Back up projects and inspect earlier versions. Imported files stay on disk until you remove them.

See the [user guide](docs/user-guide.md) for commands, import locations, requirements and limitations. Generated text and linked sources are not automatically verified.

## AI skills

The main `investingos` skill guides a compatible AI assistant through the project. The repository also contains a catalog of 178 skills, including Humanizer and educational collections. Browse the [skills index](skills/INDEX.md) to see their purposes and groups.

The default installer activates only the main skill. To make the full catalog available in the shared discovery folder, run:

```text
python scripts/install.py --all-skills
```

For Claude Code, add `--client claude`; on Windows use `py -3` instead of `python`. Restart your assistant and check which skills it discovers. Some skills require additional tools, companion components or specific clients; these are not installed automatically. See [AI client compatibility](docs/ai-clients.md) and [skill management](docs/skills-management.md).

## Skill credits and versions

Project links point to local copies; installation does not install external dependencies or guarantee client discovery. Upstream names do not imply sole authorship. VaultForge and writing-guidelines are not part of the public package because their licenses could not be verified.

| Skill or collection | Author or upstream | Installed version or revision | License and notes |
| --- | --- | --- | --- |
| InvestingOS | InvestingOS contributors | Project version 0.1.0; skill has no separate version | MIT; [skill](skills/investingos/SKILL.md). |
| Education Agent Skills (165 skills) | [Gareth Manning and contributors](https://github.com/GarethManning/education-agent-skills) | Commit `135d6275e7db0657d70b147f46d3191c5430677d` | CC BY-SA 4.0, shared alike; unmodified skills, with the code that is not clearly licensed removed. See the [notice](skills/collections/education-agent-skills-main/NOTICE-INVESTINGOS.md) and its LICENSE. |
| Course Builder | [klausners and contributors](https://github.com/klausners/course-builder) | Based on commit `09bdafb5f723db71238481d1b157a564a94d131f`; locally modified transcript helper | MIT; companion agents are required and client compatibility is not verified. |
| Obsidian Skills (6 skills) | [kepano and contributors](https://github.com/kepano/obsidian-skills) | Commit `3ccff5338ea700537839b21900aa5358a0402c98` | MIT; individual skills may require external tools. |
| Scrapling skill | [Karim Shoair / Scrapling](https://github.com/D4Vinci/Scrapling) | Commit `95cf9019ab5a5d6f3e9654b7ef1c6a26e29dc5c0` | BSD-3-Clause; notice included. Optional dependencies. |
| Humanizer | [Siqi Chen and contributors](https://github.com/blader/humanizer) | Commit `0ef9fe5bc3572734fd3ae6c448fe00a30cd5dcf0`; plugin manifest modified | MIT; notice included. |
| copy-editing | [Corey Haines and contributors](https://github.com/coreyhaines31/marketingskills) | Commit `158bd3af27b00323d5a950c033efa0256f7aa426` | MIT; notice included. |
| context7-mcp | [Upstash](https://github.com/upstash/context7) | Commit `7836c583918374fbecffacf866afb7594b919466` | MIT; notice included; requires Context7 tools. |
| investigate-first | [Julius Brussee and contributors](https://github.com/JuliusBrussee/caveman) | Commit `9b68f7ed12b05e7efaff18e65c5a3fc2849fd0a4` | Apache-2.0; license and notice included. |

See the [individual redistribution review](docs/skill-redistribution-review.md) for exact source matches, license conditions and unresolved publication checks.

## More information

- [User guide](docs/user-guide.md): features, examples and limitations.
- [Research tools](docs/research-tools.md): optional tools for documents, web research and YouTube.
- [Architecture](docs/architecture.md) and [development plan](docs/plan.md): how the project works and what is planned.
- [Project instructions](AGENTS.md): shared guidelines for contributors and agents.

## License

InvestingOS is licensed under the [MIT License](LICENSE). Bundled third-party materials may have different licenses; consult their included notices.
