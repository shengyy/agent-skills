![agent-skills](assets/banner.svg)

# agent-skills

> shengyy 的 AI agent skills 合集 —— 给 Claude Code、Codex 等编码 agent 用的可复用技能。

[English](README.md) | **简体中文**

[![version](https://img.shields.io/github/v/tag/shengyy/agent-skills?label=version&sort=semver&color=blue)](https://github.com/shengyy/agent-skills/tags)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![validate-skills](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/shengyy/agent-skills/actions/workflows/validate-skills.yml)
[![install: npx skills](https://img.shields.io/badge/install-npx%20skills-black)](https://skills.sh/)

遵循通用 [Agent Skills](https://github.com/anthropics/skills) 格式（每个 skill 一个 `SKILL.md`），用 [`skills`](https://www.npmjs.com/package/skills) CLI 一条命令即可安装，跨 Claude Code / Codex / Cursor 等多种 agent 通用。

本文负责仓库介绍、安装入口与文档和目录地图。各 skill 的行为由其 `SKILL.md` 拥有，贡献与发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 安装

```bash
# 安装全部 skill（全局，所有项目可用）
npx skills add shengyy/agent-skills -g --all

# 只装某一个
npx skills add shengyy/agent-skills -g --skill codex-construction

# 先看看仓库里有哪些 skill（不安装）
npx skills add shengyy/agent-skills -l
```

- `-g` 装到用户全局；去掉 `-g` 则只装进**当前项目**的 `.claude/skills/`。
- 安装后新开一个会话即可生效，在 Claude Code 里用 `/<skill-name>` 或自然语言触发。
- 更新：`npx skills update -g`；卸载：`npx skills remove -g -s <skill-name>`。

## Available Skills

| Skill | 说明 | 前置依赖 |
|---|---|---|
| [`codex-construction`](skills/codex-construction/SKILL.md) | 简报驱动的派工编排：主代理写好简报（背景、交付、重点、质量与资源、风格与品味）后放手，判断交给模型、只守红线与 CLI 实测事实，Codex 裸调 `codex exec` 施工；effort 按 medium / high / xhigh 三档派（更高档只在用户点名时用）、后台运行（有退出通知就不轮询）、把改动跑起来验收，按需独立验证且只认运行证明的发现。Codex 负责实现，主代理负责简报与验收。 | `codex` CLI（已登录） |
| [`app-verification`](skills/app-verification/SKILL.md) | 生成并维护项目本地的 `verify-<app>` skill，让任何 agent 都能启动真实应用、像用户一样驱动它（Web/桌面 UI、CLI/TUI、服务、库），留下熬得过清理的证据，并配一份功能地图。 | 无，使用项目自己的工具链 |
| [`formal-verification`](skills/formal-verification/SKILL.md) | 选出出错代价最高、测试最难覆盖的承诺（并发、重试、租约、状态机、解析器），用问题所需的工具验证它、证明检查会失败，并留下项目本地的 verify skill，让检查跟着代码走。 | 它选用的验证器（如 TLA+ 工具），按项目安装 |

### codex-construction

**前置依赖：**

```bash
npm install -g @openai/codex
codex login
```

模型选择与 CLI 调用见 skill 的[「启动」](skills/codex-construction/SKILL.md#启动)，推理力度见[「档位」](skills/codex-construction/SKILL.md#档位)。

## 设计哲学

当前一代编码模型能力有富余，把实现细节钉得越死，越容易逼它选次级方案；真正决定结果的是**清楚的目标和足够高的门槛**。所以主代理的功夫花在简报和验收上，不花在过程管控上。

- **事实写死，判断放开**：硬规则只有不可逆的动作边界和 CLI 实测事实；简报篇幅、拆批、档位、要不要独立验证由主代理判断，设计、实现、测试和可逆取舍由 Codex 判断。担心的偏差写成「说明为什么值得」，不写成禁令。
- **像给顶尖工程师交代任务那样写简报**：背景与动机、交付物长什么样、什么最重要、质量门槛和达到它所需的资源与授权、期望的风格与品味；另附红线和固定的运行约定。
- **对照简报验收**：亲自验证交付，确认重点真的落地，读 diff 判断质量与品味，逐条看 Codex 自主做出的判断；只有不可逆的决定和排除不了的阻塞通过 BLOCKED 交回主代理。
- **以运行结果为准，不以意见为准**：一个发现要有一次运行证明才算数——失败的命令、复现脚本、违背意图的输出。读代码推出来的意见每轮都能再挑出一批，照着改只会往代码里堆防御和抽象，过度工程多半由此而来。所以功夫花在让真实应用可被驱动（[`app-verification`](skills/app-verification/SKILL.md)）和在测试够不着的地方做穷举检查（[`formal-verification`](skills/formal-verification/SKILL.md)），不花在加审查轮次上。这个方向和两个验证 skill 改编自 [pstack](https://github.com/cursor/plugins/tree/main/pstack)。
- **渐进式披露**：每个 `SKILL.md` 只放每次都要走的主路径；只在部分场景用到的内容放进 `references/`，从用到它的位置链接过去。

执行规则由 skill 的[「原则」](skills/codex-construction/SKILL.md#原则)、[「分工」](skills/codex-construction/SKILL.md#分工)、[「写简报」](skills/codex-construction/SKILL.md#写简报)、[「验收」](skills/codex-construction/SKILL.md#验收)与[「独立验证」](skills/codex-construction/references/verification.md)负责。

## 文档地图

| 文件 | 职责 |
|---|---|
| [README.md](README.md) | 英文仓库介绍、安装入口与文档和目录地图。 |
| [README.zh-CN.md](README.zh-CN.md) | README 的中文同步版本。 |
| [AGENTS.md](AGENTS.md) | 共用的仓库约定与任务路由。 |
| [CLAUDE.md](CLAUDE.md) | 导入共用约定，补充 Claude Code 的本地 memory 边界。 |
| [codex-construction/SKILL.md](skills/codex-construction/SKILL.md) | 简报结构、派工、effort 档位、CLI 操作、续接与验收；独立验证与 nohup 回退在 `references/`。 |
| [app-verification/SKILL.md](skills/app-verification/SKILL.md) | 创建驱动真实应用的项目本地 verify skill；维护流程与功能地图示例在 `references/`。 |
| [formal-verification/SKILL.md](skills/formal-verification/SKILL.md) | 选目标与工具、可信检查的标准、生成 verify skill；维护流程在 `references/`。 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 新增 skill、本地试装、贡献与发版流程。 |
| [pull_request_template.md](.github/pull_request_template.md) | PR 改动说明与检查清单；贡献流程由 CONTRIBUTING.md 负责。 |
| [CHANGELOG.md](CHANGELOG.md) | 版本历史与待发布变更。 |
| [VERSION](VERSION) | 当前发布版本号。 |
| [LICENSE](LICENSE) | MIT 授权条款。 |

## 目录地图

| 目录 | 职责 |
|---|---|
| [仓库根目录](.) | 仓库入口与声明：Agent 指引、双语 README、贡献指南、变更记录、版本、授权与本地产物忽略规则。 |
| [`.github/`](.github/) | GitHub 协作与自动化：PR 模板和校验 workflow。 |
| [`.github/workflows/`](.github/workflows/) | CI 定义；当前 workflow 调用仓库的 skill 校验脚本。 |
| [`assets/`](assets/) | README 展示素材；随 skill 分发的素材归各 skill 安装包。 |
| [`scripts/`](scripts/) | 仓库级门禁（`validate_skills.py` 校验 skill 结构与 frontmatter）；随 skill 分发的脚本归各 skill 安装包。 |
| [`skills/`](skills/) | 可安装的 skill 包；包内结构见[仓库约定](AGENTS.md#仓库约定)。 |
| [`skills/codex-construction/`](skills/codex-construction/) | codex-construction 安装包。 |
| [`skills/app-verification/`](skills/app-verification/) | app-verification 安装包；`NOTICE.md` 保留所改编的 pstack skill 的授权。 |
| [`skills/formal-verification/`](skills/formal-verification/) | formal-verification 安装包；`NOTICE.md` 保留所改编的 pstack skill 的授权。 |

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。每个 skill 必须通过
`python3 scripts/validate_skills.py` 的结构校验。

## License

[MIT](LICENSE)
