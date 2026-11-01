# AI client compatibility

The knowledge engine is a local Python CLI and does not require an AI provider. `skills/` contains its portable `SKILL.md` instructions. By default the installer activates only the `investingos` skill in the chosen discovery path: `shared` (default) uses `.agents/skills/`, and `claude` uses `.claude/skills/`. It does not configure accounts, client permissions, MCP servers, or external dependencies.

The following locations are documented by the respective vendors. These are discovery paths, not a guarantee that every bundled third-party skill works in every client. Versions, workspace trust, link handling, naming rules, permissions, and supported features can affect discovery. Actual client discovery has not been tested for this pack.

| Client | Documented project skill locations | Notes |
| --- | --- | --- |
| Codex | `.agents/skills/` | Use the shared links created by the installer. [Documentation](https://developers.openai.com/codex/skills). |
| Claude Code | `.claude/skills/` | Run `python scripts/install.py --client claude` (or `py -3 scripts/install.py --client claude` on Windows). [Documentation](https://code.claude.com/docs/en/skills). |
| Cursor | `.agents/skills/`, `.cursor/skills/` | The shared path is documented. [Documentation](https://cursor.com/docs/skills). |
| OpenCode | `.agents/skills/`, `.claude/skills/`, `.opencode/skills/` | Check name constraints and duplicate definitions. The `VaultForge-main` name used by the locally held VaultForge skill, which is not in the public package, does not meet OpenCode's documented naming rules. [Documentation](https://opencode.ai/docs/skills/). |
| Gemini CLI | `.agents/skills/`, `.gemini/skills/` | Workspace trust and enabled skills may be required; use `/skills list` or `gemini skills list`. [Documentation](https://geminicli.com/docs/cli/skills/). |
| GitHub Copilot | `.agents/skills/`, `.github/skills/`, `.claude/skills/` | Availability depends on the Copilot surface and version. [Documentation](https://docs.github.com/en/copilot/concepts/customizations/agent-skills). |
| Windsurf / Devin Desktop | Not confirmed | The prior official documentation URL redirected to a page unavailable during this review. Check the current product documentation for your installed version; use the manual method below if discovery is unavailable. |
| ChatGPT and other hosted assistants | Client-specific | A local checkout is not automatically available to a hosted conversation. Follow the product's supported file, workspace, or plugin workflow. No ChatGPT integration is configured by the installer. |

Run `python scripts/install.py --client shared` for the shared path, or `python scripts/install.py --client claude` for Claude Code. The flags can be repeated when both paths are actually needed. On Windows use `py -3 scripts/install.py` with the same flags. Use `--skill NAME` to activate a specific additional skill, or `--all-skills` for the full bundle; select third-party skills only when needed. These paths are generated locally and ignored by Git; a clean checkout does not carry them. The installer does not delete previously generated links or modify global installations. Remove an old discovery directory manually only after confirming it contains no personal files.

Clients that do not discover project skills can still use the engine. If the client can access local files, ask it to read `skills/investingos/SKILL.md` and the README, then use `python scripts/investingos.py --help` with Python 3.10 or later. If local execution or file access is unavailable, the assistant cannot run the engine without an appropriate integration.

The core skill is provider-neutral. Third-party collections may require a specific client, companion agents, software, or services. In particular, Course Builder requires companion agents; linking its skill alone does not implement them. Review each skill and its license before use or redistribution. Do not assume an MCP server is present or send local data to a remote service without authorization.
