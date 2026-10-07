![agent-skills](assets/banner.svg)

# agent-skills

> Reusable AI agent skills for coding agents like Claude Code and Codex.

**English** | [简体中文](README.zh-CN.md)

[![version](https://img.shields.io/github/v/tag/shengyy/agent-skills?label=version&sort=semver&color=blue)](https://github.com/shengyy/agent-skills/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![validate-skills](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml)
[![install: npx skills](https://img.shields.io/badge/install-npx%20skills-black)](https://skills.sh/)

Built on the common [Agent Skills](https://github.com/anthropics/skills) format (one `SKILL.md` per skill) and installable with a single [`skills`](https://www.npmjs.com/package/skills) CLI command — works across Claude Code, Codex, Cursor, and other agents.

This README covers the project, installation, and document and directory maps. Each skill's `SKILL.md` owns its behavior; [CONTRIBUTING.md](CONTRIBUTING.md) owns contribution and release procedures.

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
| [`codex-construction`](skills/codex-construction/SKILL.md) | Brief-driven delegation: the main agent writes a brief (background, deliverable, focus, quality & resources, style & taste), then lets Codex build via bare `codex exec` — effort on a medium / high / xhigh ladder, background monitoring, acceptance against the brief, build-review cycles. Codex owns implementation; the main agent owns the brief and acceptance. | `codex` CLI (logged in) |

### codex-construction

**Prerequisites:**

```bash
npm install -g @openai/codex
codex login
```

For model selection and CLI invocation, see [Launch](skills/codex-construction/SKILL.md#启动);
for reasoning effort, see [Effort tiers](skills/codex-construction/SKILL.md#档位).

## Design philosophy

Current-generation coding models have capability to spare. Pinning down implementation detail
mostly forces them into second-best solutions; what still moves the result is **a clear goal
and a high bar**. So the main agent's effort goes into the brief and acceptance, not process control.

- **Write the brief like you'd brief a top engineer**: background and motivation, what the
  deliverable looks like, what matters most, the quality bar plus the resources to reach it,
  and the style and taste you expect. Add only true red lines and a fixed run protocol.
- **Let go**: within a batch Codex makes every implementation call — read, design, build,
  run gates, commit, write the acceptance packet. Real problems found mid-build are
  root-cause-fixed in scope and recorded.
- **Accept against the brief**: verify the deliverable yourself, check the focus actually
  landed, and read the diff for quality and taste. Product decisions come back as BLOCKED.

The operational rules behind these live in the skill: [Division of labor](skills/codex-construction/SKILL.md#分工),
[Writing the brief](skills/codex-construction/SKILL.md#写简报),
[Acceptance](skills/codex-construction/SKILL.md#验收), and
[Build-review cycle](skills/codex-construction/SKILL.md#改-审循环).

## Documentation

| File | Responsibility |
|---|---|
| [README.md](README.md) | English project overview, installation entry point, and document and directory maps. |
| [README.zh-CN.md](README.zh-CN.md) | Synchronized Chinese version of the README. |
| [AGENTS.md](AGENTS.md) | Shared repository conventions and task routing. |
| [CLAUDE.md](CLAUDE.md) | Imports the shared conventions and covers Claude Code's local memory boundary. |
| [codex-construction/SKILL.md](skills/codex-construction/SKILL.md) | Brief structure, delegation, effort tiers, CLI operations, and acceptance. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Adding skills, local installation checks, contributions, and releases. |
| [pull_request_template.md](.github/pull_request_template.md) | PR change description and checklist; contribution procedures live in CONTRIBUTING.md. |
| [CHANGELOG.md](CHANGELOG.md) | Version history and unreleased changes. |
| [VERSION](VERSION) | Current release number. |
| [LICENSE](LICENSE) | MIT license terms. |

## Repository layout

| Directory | Responsibility |
|---|---|
| [Repository root](.) | Repository entry documents and declarations: Agent guidance, READMEs, contribution guide, changelog, version, license, and local artifact ignore rules. |
| [`.github/`](.github/) | GitHub collaboration and automation: the PR template and validation workflow. |
| [`.github/workflows/`](.github/workflows/) | CI definitions; the current workflow runs the repository's skill validation script. |
| [`assets/`](assets/) | README display assets. Assets shipped with a skill belong in that skill's package. |
| [`scripts/`](scripts/) | Repository-level validation (`validate_skills.py` checks skill structure and frontmatter). Scripts shipped with a skill belong in that skill's package. |
| [`skills/`](skills/) | Installable skill packages; their internal layout follows the [repository conventions](AGENTS.md#仓库约定). |
| [`skills/codex-construction/`](skills/codex-construction/) | The codex-construction package. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every skill must pass
`python3 scripts/validate_skills.py`.

## License

[MIT](LICENSE)
