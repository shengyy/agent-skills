![agent-skills](assets/banner.svg)

# agent-skills

> Reusable AI agent skills for coding agents like Claude Code and Codex.

**English** | [简体中文](README.zh-CN.md)

[![version](https://img.shields.io/github/v/tag/shengyy/agent-skills?label=version&sort=semver&color=blue)](https://github.com/shengyy/agent-skills/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![validate-skills](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml)
[![install: npx skills](https://img.shields.io/badge/install-npx%20skills-black)](https://skills.sh/)

Built on the common [Agent Skills](https://github.com/anthropics/skills) format (one `SKILL.md` per skill) and installable with a single [`skills`](https://www.npmjs.com/package/skills) CLI command — works across Claude Code, Codex, Cursor, and other agents.

This README covers the project, installation, and document map. Each skill's `SKILL.md` owns its behavior; [CONTRIBUTING.md](CONTRIBUTING.md) owns contribution and release procedures.

## Install

```bash
# Install every skill (global — available in all projects)
npx skills add shengyy/agent-skills -g --all

# Install just one
npx skills add shengyy/agent-skills -g --skill codex-construction

# List the skills in this repo without installing
npx skills add shengyy/agent-skills -l
```

- `-g` installs to the user-global scope; drop it to install only into the current project's `.claude/skills/`.
- Open a new session after installing. In Claude Code, trigger with `/<skill-name>` or natural language.
- Update: `npx skills update -g` · Uninstall: `npx skills remove -g -s <skill-name>`.

## Available Skills

| Skill | What it does | Requires |
|---|---|---|
| [`codex-construction`](skills/codex-construction/SKILL.md) | Lightweight delegation loop: the main agent owns the plan, Codex builds via bare `codex exec` — batched dispatch, effort dispatched on a medium / high / xhigh ladder, background monitoring, per-stage commits + acceptance packets, build-review cycles. Codex owns implementation; the main agent sets scope and accepts results. | `codex` CLI (logged in) |

### codex-construction

**Prerequisites:**

```bash
npm install -g @openai/codex
codex login
```

For model selection and CLI invocation, see [Launch](skills/codex-construction/SKILL.md#启动);
for reasoning effort, see [Effort tiers](skills/codex-construction/SKILL.md#档位).

## Design philosophy

Current-generation coding models have capability to spare, so what orchestration still adds
collapses to three things: **division of labor, boundaries, acceptance**.

The operational rules live in the skill: [Division of labor](skills/codex-construction/SKILL.md#分工),
[Prompt contract](skills/codex-construction/SKILL.md#prompt-五要素), and
[Build-review cycle](skills/codex-construction/SKILL.md#改-审循环).

## Documentation

| File | Responsibility |
|---|---|
| [README.md](README.md) | English project overview, installation entry point, and document map. |
| [README.zh-CN.md](README.zh-CN.md) | Synchronized Chinese version of the README. |
| [AGENTS.md](AGENTS.md) | Shared repository conventions and task routing. |
| [CLAUDE.md](CLAUDE.md) | Imports the shared conventions and covers Claude Code's local memory boundary. |
| [codex-construction/SKILL.md](skills/codex-construction/SKILL.md) | Delegation, effort tiers, CLI operations, and acceptance contracts. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Adding skills, local installation checks, contributions, and releases. |
| [pull_request_template.md](.github/pull_request_template.md) | PR change description and checklist; contribution procedures live in CONTRIBUTING.md. |
| [CHANGELOG.md](CHANGELOG.md) | Version history and unreleased changes. |
| [VERSION](VERSION) | Current release number. |
| [LICENSE](LICENSE) | MIT license terms. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every skill must pass
`python3 scripts/validate_skills.py`.

## License

[MIT](LICENSE)
