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
| [`codex-construction`](skills/codex-construction/) | Lightweight delegation loop: the main agent owns the plan, Codex builds via bare `codex exec` — batched dispatch, effort dispatched on a medium / high / xhigh ladder, background monitoring, per-stage commits + acceptance packets, build-review cycles. Delegate fully, supervise only for over-engineering. | `codex` CLI (logged in) |

### codex-construction

**Prerequisites:**

```bash
npm install -g @openai/codex
codex login
```

Default model is `gpt-6-astra`. Reasoning effort uses only three tiers — medium / high / xhigh —
chosen by the criteria in SKILL.md's tier table: the tier follows how much design latitude the
contract leaves to Codex and the cost of being wrong; construction defaults to medium, review
never runs below the construction tier. To switch model, edit the launch line in SKILL.md.

## Design philosophy

Current-generation coding models have capability to spare, so what orchestration still adds
collapses to three things: **division of labor, boundaries, acceptance**.

- **Delegate**: Codex is fully autonomous within a batch — read the contract, implement, run
  gates, commit, write the acceptance packet. The prompt carries only five elements:
  site / contract pointer / scope / true red lines / boundaries & delivery protocol.
- **Supervise**: the systematic failure mode of unsupervised Codex is over-engineering, so the
  main agent intervenes only at plan rulings, per-batch acceptance, and BLOCKED decisions —
  never process management.
- **Fewer constraints win**: the more implementation detail you pin down, the more often the
  model is forced into a second-best solution. Real problems found mid-build may be
  root-cause-fixed in scope and recorded in the acceptance packet.

Version history, including the skills this one replaced, lives in [CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every skill must pass
`python3 scripts/validate_skills.py`.

## License

[MIT](LICENSE)
