![agent-skills](assets/banner.svg)

# agent-skills

> Reusable AI agent skills for coding agents like Claude Code and Codex.

**English** | [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![validate-skills](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml)
[![install: npx skills](https://img.shields.io/badge/install-npx%20skills-black)](https://skills.sh/)

Built on the common [Agent Skills](https://github.com/anthropics/skills) format (one `SKILL.md` per skill) and installable with a single [`skills`](https://www.npmjs.com/package/skills) CLI command — works across Claude Code, Codex, Cursor, and other agents.

## Install

```bash
# Install every skill (global — available in all projects)
npx skills add shengyy/agent-skills -g --all

# Install just one
npx skills add shengyy/agent-skills -g --skill codex-dev

# List the skills in this repo without installing
npx skills add shengyy/agent-skills -l
```

- `-g` installs to the user-global scope; drop it to install only into the current project's `.claude/skills/`.
- Open a new session after installing. In Claude Code, trigger with `/<skill-name>` or natural language.
- Update: `npx skills update -g` · Uninstall: `npx skills remove -g -s <skill-name>`.

## Available Skills

| Skill | What it does | Requires |
|---|---|---|
| [`codex-dev`](skills/codex-dev/) | A full loop for delegating dev tasks to the OpenAI Codex CLI: Claude plans, writes the task brief, orchestrates concurrency, runs mechanical acceptance + review + merge; Codex writes the code in a `workspace-write` sandbox. | `codex` CLI (required), `omegacode` (optional — concurrent track) |

### codex-dev

A delegation loop: Claude plans, writes the task brief, orchestrates (serial `codex exec` / concurrent `omegacode` + worktree isolation), reviews, and merges; Codex only implements inside the sandbox. The flow advances automatically and pauses for you only when BLOCKED, when a merge conflict needs a ruling, or when something would cross role boundaries.

**Prerequisites** (the skill is only the orchestrator — install the tools that do the real work yourself):

```bash
# 1. codex CLI (required)
npm install -g @openai/codex
codex login

# 2. omegacode (optional — only for the concurrent track)
npm install -g --prefix ~/.npm-global omegacode
omegacode doctor   # verify the codex worker is ready
```

> Sandbox note: the delegation commands force `-s workspace-write` internally and don't rely on your global default. If your `~/.codex/config.toml` sets `danger-full-access`, just be aware — the skill overrides it explicitly.

The concurrent track runs as a **detached background job with a live dashboard** — close your terminal and the run keeps going; any new session reattaches via the recorded run ID (no babysitting process required).

![omegacode dashboard — concurrent codex tasks](assets/dashboard.png)

## Usage

```bash
# After installing, in a Claude Code session:
/codex-dev refactor the login flow in src/auth to OAuth
# or natural language: "hand this to codex" / "fan out a few codex tasks for A, B, C"
```

## Repository layout

```
agent-skills/
├── README.md               # English
├── README.zh-CN.md         # 简体中文
├── CONTRIBUTING.md         # how to add a new skill
├── CHANGELOG.md
├── LICENSE
├── assets/banner.svg
├── scripts/
│   └── validate_skills.py  # SKILL.md validation, shared by local + CI
├── .github/
│   ├── workflows/validate-skills.yml
│   └── pull_request_template.md
└── skills/
    └── codex-dev/
        └── SKILL.md        # a single self-contained skill (frontmatter: name + description)
```

Each skill lives in its own `skills/<name>/` directory with at least a `SKILL.md`; add `scripts/`, `references/`, etc. as needed — they travel with the install.

## Adding a new skill

```bash
# 1. scaffold
npx skills init skills/<new-skill-name>

# 2. edit SKILL.md (name must equal the directory name; description must spell out when to trigger)

# 3. validate locally
python3 scripts/validate_skills.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full conventions. Once pushed, anyone can install it with `npx skills add shengyy/agent-skills -g --skill <new-skill-name>`.

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and conventions, and [CHANGELOG.md](CHANGELOG.md) for the history.

## License

[MIT](LICENSE) © 2026 shengyy
