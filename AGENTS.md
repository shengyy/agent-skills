# agent-skills · Agent 指引

公开的 Agent Skills 合集（MIT），用 `skills` CLI 分发到 Claude Code、Codex、Cursor 等。提交的提示词会影响安装者的 Agent 行为；本文件存放各 Agent 共用的仓库约定，`CLAUDE.md` 导入本文件。

Skill 行为以各目录的 `SKILL.md` 为准，结构校验以 [`scripts/validate_skills.py`](scripts/validate_skills.py) 为准；其它文档作为入口，冲突时修正对应 owner。

## 按任务读取

| 范围 | 先读 |
|---|---|
| 派工 skill 的分工、档位、CLI 操作与验收 | [`skills/codex-construction/SKILL.md`](skills/codex-construction/SKILL.md) |
| 新增 skill、本地试装、贡献与发版 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| 安装入口与 skill 目录 | [`README.md`](README.md)、[`README.zh-CN.md`](README.zh-CN.md) |
| 变更记录与版本 | [`CHANGELOG.md`](CHANGELOG.md)、[`VERSION`](VERSION) |
| 结构校验与 CI | [`scripts/validate_skills.py`](scripts/validate_skills.py)、[校验 workflow](.github/workflows/validate-skills.yml) |

## 仓库约定

- 一个 skill 一个 `skills/<name>/` 目录，名字用小写和 `-` 连字，frontmatter 的 `name` 与目录名一致，`description` 写清触发场景与触发词，便于 CLI 识别和 Agent 路由。脚本、参考资料、模板与素材放在该目录的 `scripts/`、`references/`、`assets/`，用相对路径引用，让安装包自包含。
- 一个事实一个 owner，调用方链接它，减少口径漂移。同步点是版本号（`VERSION` 与 `CHANGELOG.md` 版本段，README 徽章读 git tag）和双语 README（两份同步更新）。
- Skill 面向当前一代模型（GPT‑6 / Claude 5+），围绕分工、边界、验收编写，实现决策交给模型。精确命令保留 CLI 契约与易错操作的细节；替代方案落地即删除旧路径，保持唯一执行路径。
- `SKILL.md` 超过 800 行先按职责拆到 `references/`，让使用者按需读取。
- 公开内容不含机密、令牌、个人路径或客户信息；安装和传播会把这些内容带到其它项目。
- Skill 行为改动记入 `CHANGELOG.md` 的 `[Unreleased]`，供安装者判断更新影响。

## 检查与协作

改动后运行 `python3 scripts/validate_skills.py`；[CI](.github/workflows/validate-skills.yml) 使用同一脚本。文档或指令改动核对本地路径与链接；安装入口改动的本地试装方法见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

中文回复，标识符、命令、路径与服务名保持英文。贡献与 PR 流程见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。发版打 tag 先取得用户确认，因为 tag 对外标识可安装版本。
