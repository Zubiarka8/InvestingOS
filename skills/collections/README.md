# Third-party skills

Downloaded from the main branches on November 1, 2026. Each collection was compared file by file (Git blob hashes) with the commit named in the [redistribution review](../../docs/skill-redistribution-review.md); the only differences are the ones listed below. Consult each repository and license before redistributing or modifying them. The `.agents/skills` and `.claude/skills` links, when created, share these files.

- [Education Agent Skills](https://github.com/GarethManning/education-agent-skills): 165 skills, commit `135d627`. Educational materials are CC BY-SA 4.0 (credit Gareth Manning, link the license, indicate changes, share alike). Skill files are unmodified. The code and generated files that the notice does not clearly cover were removed from this copy; see [the attribution and modification notice](education-agent-skills-main/NOTICE-INVESTINGOS.md).
- [Course Builder](https://github.com/klausners/course-builder): one skill, MIT, commit `09bdafb`. Its Bash transcript helper was locally replaced by Python and three instruction files were updated (`CONTRIBUTING.md`, `agents/course-builder.md`, `agents/source-reader.md`); the upstream LICENSE is retained. The Python helper requires `youtube-transcript-api` 1.x, and has not been tested against YouTube. It requires companion agents and is designed as a Claude plugin; linking the skill alone does not guarantee it works in Codex or Claude.
- [Obsidian Skills](https://github.com/kepano/obsidian-skills): six skills, MIT, commit `3ccff53`, unmodified. Some features require Obsidian tools or other utilities.

## Not in the public package

[VaultForge](https://github.com/Easonnotsing/VaultForge) (commit `759a289`) and Vercel's `writing-guidelines` (from [agent-skills](https://github.com/vercel-labs/agent-skills), commit `1a2c79d`) are not bundled. Their upstream repositories state only "MIT" in a README, with no license file or copyright holder, and GitHub detects no license. A copy is kept locally in the git-ignored `local-only/` directory. To obtain them, use the upstream repositories at those commits and check their license yourself.

No dependencies were installed and no external scripts were run. These are third-party instructions and code; review them before execution. ClassBuild is an application and was not installed as a skill.
