![agent-skills](assets/banner.svg)

# agent-skills

> shengyy 的 AI agent skills 合集 —— 给 Claude Code、Codex 等编码 agent 用的可复用技能。

[English](README.md) | **简体中文**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![validate-skills](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml)
[![install: npx skills](https://img.shields.io/badge/install-npx%20skills-black)](https://skills.sh/)

遵循通用 [Agent Skills](https://github.com/anthropics/skills) 格式（每个 skill 一个 `SKILL.md`），用 [`skills`](https://www.npmjs.com/package/skills) CLI 一条命令即可安装，跨 Claude Code / Codex / Cursor 等多种 agent 通用。

## 安装

```bash
# 安装全部 skill（全局，所有项目可用）
npx skills add shengyy/agent-skills -g --all

# 只装某一个
npx skills add shengyy/agent-skills -g --skill codex-dev

# 先看看仓库里有哪些 skill（不安装）
npx skills add shengyy/agent-skills -l
```

- `-g` 装到用户全局；去掉 `-g` 则只装进**当前项目**的 `.claude/skills/`。
- 安装后新开一个会话即可生效，在 Claude Code 里用 `/<skill-name>` 或自然语言触发。
- 更新：`npx skills update -g`；卸载：`npx skills remove -g -s <skill-name>`。

## Available Skills

| Skill | 说明 | 前置依赖 |
|---|---|---|
| [`codex-dev`](skills/codex-dev/) | 把开发任务派发给 OpenAI Codex CLI 实施的通用闭环：Claude 出方案写任务书、编排并发、机械验收 + 评审 + 合并提交；codex 在 `workspace-write` 沙箱里写代码。 | `codex` CLI（必需）、`omegacode`（并发轨可选） |

### codex-dev

派工开发闭环：Claude 负责出方案、写任务书、编排（串行 `codex exec` / 并发 `omegacode` + worktree 物理隔离）、验收评审、合并提交；codex 只负责在沙箱里实施。流程自动推进，只在 BLOCKED、合并冲突需裁决或越权时停下来问人。

**前置依赖**（skill 本身只是编排器，真正干活的工具需自行装好）：

```bash
# 1. codex CLI（必需）
npm install -g @openai/codex
codex login

# 2. omegacode（仅并发轨需要，可选）
npm install -g omegacode
omegacode doctor   # 验证 codex worker 就绪
```

> 沙箱说明：派工命令内部已强制 `-s workspace-write`，不依赖全局默认。若本机 `~/.codex/config.toml` 设了 `danger-full-access`，知悉即可，skill 会显式覆盖。

> 模型说明：任务默认跑在 **`gpt-5.5`**，推理力度按任务分档（`medium` / `high` / `xhigh`）。要换模型，直接改 skill 里的 `model` / `defaultModel` 即可。

并发轨是 **detached 后台任务，自带实时 dashboard**——关掉终端 run 照样在跑，任何新会话凭落盘的 runId 就能重连（不靠 watcher 进程续命）。

![omegacode dashboard — 并发 codex 任务](assets/dashboard.png)

## Usage

```bash
# 安装后，在 Claude Code 会话里：
/codex-dev 把 src/auth 的登录流程重构成 OAuth
# 或自然语言："丢给 codex 实现 XXX" / "并发派几个 codex 做 A、B、C"
```

## 仓库结构

```
agent-skills/
├── README.md               # English
├── README.zh-CN.md         # 简体中文
├── CONTRIBUTING.md         # 加新 skill 的规范流程
├── CHANGELOG.md
├── LICENSE
├── assets/banner.svg
├── scripts/
│   └── validate_skills.py  # 本地 / CI 共用的 SKILL.md 校验
├── .github/
│   ├── workflows/validate-skills.yml
│   └── pull_request_template.md
└── skills/
    └── codex-dev/
        └── SKILL.md        # 单个自包含 skill（frontmatter: name + description）
```

每个 skill 自成一个 `skills/<name>/` 目录，至少含一个 `SKILL.md`；如有需要可附 `scripts/`、`references/` 等子目录，随安装一起带走。

## 添加新 skill

```bash
# 1. 初始化骨架
npx skills init skills/<new-skill-name>

# 2. 编辑 SKILL.md（name 必须等于目录名，description 写清触发场景）

# 3. 本地校验
python3 scripts/validate_skills.py
```

完整规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。提交推送后，任何人都能用
`npx skills add shengyy/agent-skills -g --skill <new-skill-name>` 装上。

## 贡献

欢迎提 PR。流程与约定见 [CONTRIBUTING.md](CONTRIBUTING.md)，变更历史见 [CHANGELOG.md](CHANGELOG.md)。

## License

[MIT](LICENSE) © 2026 shengyy
