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
| [`codex-construction`](skills/codex-construction/) | Lightweight delegation loop: the main agent owns the plan, Codex builds via bare `codex exec` — batched dispatch, three-state background monitoring, per-stage commits + acceptance packets, build-review cycles. Delegate fully, supervise only for over-engineering. | `codex` CLI (logged in) |

### codex-construction

**Prerequisites:**

```bash
npm install -g @openai/codex
codex login
```

Hardened during a real full-day architecture overhaul (6 stages, 10k+ lines net deleted,
three long unattended construction runs with zero hangs), then distilled into a skill.
To switch model or reasoning effort, edit the single invocation line in SKILL.md.

## Design philosophy (since v0.3)

v0.2's `codex-dev` / `codex-dev-native` were written for the previous model generation:
sandbox plumbing, write allowlists, brief templates, concurrency registries — most of that
volume re-did work the engine and the model can now do themselves, and it was the root
cause of the constant hangs and silent stalls.

Current-generation models (GPT‑5.6+ / Claude 5+) have capability to spare. Orchestration
value collapses to three things: **division of labor, boundaries, acceptance**. So v0.3
replaces both old skills with one ~100-line `codex-construction`:

- **Delegate**: Codex is fully autonomous within a batch (read the contract, implement,
  run gates, commit, write the acceptance packet). The prompt carries only five elements:
  site / contract pointer / scope / true red lines / boundaries & delivery protocol.
- **Supervise**: the systematic failure mode of unsupervised Codex is over-engineering —
  the main agent intervenes only at plan rulings, per-batch acceptance, and BLOCKED
  decisions. Never process management.
- **Fewer constraints win**: the more implementation detail you pin down, the more often
  the model is forced into second-best solutions. Real problems found mid-build may be
  root-cause-fixed in scope, recorded in the acceptance packet.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every skill must pass
`python scripts/validate_skills.py`.

## License

[MIT](LICENSE)
