![agent-skills](assets/banner.svg)

# agent-skills

> Reusable AI agent skills for coding agents like Claude Code and Codex.

**English** | [简体中文](README.zh-CN.md)

[![version](https://img.shields.io/github/v/tag/shengyy/agent-skills?label=version&sort=semver&color=blue)](https://github.com/shengyy/agent-skills/releases)
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
| [`codex-dev-native`](skills/codex-dev-native/) | The same delegation loop on the **official Codex plugin's native `codex-companion` engine** (no omegacode): Claude orchestrates + reviews + merges, Codex implements under `workspace-write` (writes confined to cwd, network on). Launch / background / status / result / cancel / resume are all native. | `codex` CLI + the `codex@openai-codex` Claude Code plugin |

### codex-dev

A delegation loop: Claude plans, writes the task brief, orchestrates (serial `codex exec` / concurrent `omegacode` + worktree isolation), reviews, and merges; Codex only implements inside the sandbox. The flow advances automatically and pauses for you only when BLOCKED, when a merge conflict needs a ruling, or when something would cross role boundaries.

**Prerequisites** (the skill is only the orchestrator — install the tools that do the real work yourself):

```bash
# 1. codex CLI (required)
npm install -g @openai/codex
codex login

# 2. omegacode (optional — only for the concurrent track)
npm install -g omegacode
omegacode doctor   # verify the codex worker is ready
```

> Sandbox note: the delegation commands force `-s workspace-write` internally and don't rely on your global default. If your `~/.codex/config.toml` sets `danger-full-access`, just be aware — the skill overrides it explicitly.

> Model: tasks run on **`gpt-5.5`** by default, at a reasoning effort chosen per task (`medium` / `high` / `xhigh`). To use a different model, just edit `model` / `defaultModel` in the skill.

The concurrent track runs as a **detached background job with a live dashboard** — close your terminal and the run keeps going; any new session reattaches via the recorded run ID (no babysitting process required).

![omegacode dashboard — concurrent codex tasks](assets/dashboard.png)

### codex-dev-native

The same delegation loop as `codex-dev`, but the execution engine is the **official Codex plugin** (`codex@openai-codex`) instead of omegacode. Claude still owns orchestration, mechanical acceptance, personal review, and merge; Codex still only implements. The difference is everything under the hood — launch, background execution, status / result / cancel, same-thread resume, and crash recovery — is the plugin's native per-repo job registry, so the skill carries no hand-rolled dispatch or reconnect plumbing.

**Prerequisites:**

```bash
# 1. codex CLI (required)
npm install -g @openai/codex
codex login

# 2. the official Codex plugin for Claude Code (this is the engine)
claude plugin install codex@openai-codex --scope user
```

> Sandbox: Codex runs under `workspace-write` (the only mode the plugin gives a write task) — writes are confined to the task's cwd and the OS blocks escape. To let Codex fetch docs / install deps, enable network for that mode in `~/.codex/config.toml`:
>
> ```toml
> [sandbox_workspace_write]
> network_access = true
> ```
>
> This only applies when workspace-write is active, so it leaves your interactive Codex untouched.

**Parallel without a daemon:** Claude fires N native background jobs (one per worktree) and tracks them via `status` / `result`. There is no separate dashboard process — the job registry persists on disk per repo, so a new session reattaches just by running `status`.

**codex-dev vs codex-dev-native** — pick by engine:

| | `codex-dev` | `codex-dev-native` |
|---|---|---|
| Engine | omegacode | official `codex@openai-codex` plugin |
| Parallel fan-out | omega `parallel()` + live web dashboard | Claude orchestrates N native background jobs |
| Reconnect / recovery | recorded run ID + `run.json` | native per-repo job registry |
| Extra dependency | `omegacode` | the codex plugin |

Prefer `codex-dev-native` when the official plugin is installed; keep `codex-dev` when you want omega's live dashboard or already run on omega.

## Usage

```bash
# After installing, in a Claude Code session:
/codex-dev refactor the login flow in src/auth to OAuth          # omegacode engine
/codex-dev-native refactor the login flow in src/auth to OAuth   # native codex-plugin engine
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
    ├── codex-dev/
    │   └── SKILL.md        # delegation loop on the omegacode engine
    └── codex-dev-native/
        └── SKILL.md        # delegation loop on the native codex plugin engine
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
