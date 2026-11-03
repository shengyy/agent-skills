# agent-skills · Agent 指引

公开的 Agent Skills 合集（MIT），用 `skills` CLI 分发到 Claude Code、Codex、Cursor 等。提交的提示词会影响安装者的 Agent 行为；本文件存放各 Agent 共用的仓库约定，`CLAUDE.md` 导入本文件。

Skill 行为以各目录的 `SKILL.md` 为准，结构校验以 [`scripts/validate_skills.py`](scripts/validate_skills.py) 为准；其它文档作为入口，冲突时修正对应 owner。

## 按任务读取

| 范围 | 先读 |
|---|---|
| 派工 skill 的简报结构、分工、档位、CLI 操作与验收 | [`skills/codex-construction/SKILL.md`](skills/codex-construction/SKILL.md) |
| 实证验证：生成与维护驱动真实应用的项目本地 verify skill | [`skills/app-verification/SKILL.md`](skills/app-verification/SKILL.md) |
| 形式化验证：选目标与工具、生成与维护项目本地 verify skill | [`skills/formal-verification/SKILL.md`](skills/formal-verification/SKILL.md) |
| 新增 skill、本地试装、贡献与发版流程 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| PR 改动说明与检查清单 | [`.github/pull_request_template.md`](.github/pull_request_template.md) |
| 仓库介绍、安装入口与文档和目录地图 | [`README.md`](README.md)、[`README.zh-CN.md`](README.zh-CN.md) |
| 变更记录与版本 | [`CHANGELOG.md`](CHANGELOG.md)、[`VERSION`](VERSION) |
| 结构校验与 CI | [`scripts/validate_skills.py`](scripts/validate_skills.py)、[校验 workflow](.github/workflows/validate-skills.yml) |

## 仓库约定

- 一个 skill 一个 `skills/<name>/` 目录，名字用小写和 `-` 连字，frontmatter 的 `name` 与目录名一致，`description` 写清触发场景与触发词，便于 CLI 识别和 Agent 路由。脚本、参考资料、模板与素材放在该目录的 `scripts/`、`references/`、`assets/`，用相对路径引用，让安装包自包含。
- 一个事实一个 owner，调用方链接它，减少口径漂移。同步点是版本号（`VERSION` 与 `CHANGELOG.md` 版本段，README 徽章读 git tag）和双语 README（两份同步更新）。
- Skill 面向当前一代模型（GPT‑6 / Claude 5+），围绕目标、边界、验收编写，判断交给模型。硬规则只留两类：不可逆的动作边界，以及模型推不出来的实测事实（CLI 契约与易错操作的精确命令）；其余写成原则和理由，担心的偏差写成「说明为什么值得」而非禁令。替代方案落地即删除旧路径，保持唯一执行路径。
- 只留最新事实：过期内容、旧口径、过程记录和已经不再是事实的旧文档、旧记录直接删除，不在仓库里留噪音，历史由 Git 追溯；文档与代码冲突时以代码为准修正文档。
- 渐进式披露：`SKILL.md` 放每次触发都要走的主路径和硬事实；只在部分场景用到的内容（备用路径、另一种模式、长示例）拆到 `references/`，在主文件里用到它的位置写明什么时候读。拆分按「用不用得上」而不是按篇幅：拆出去多一次读取，也多一分漏读的可能，反复被读的内容应留在主文件。references 只从 `SKILL.md` 引一层，超过 100 行的开头放目录，`SKILL.md` 正文控制在 500 行以内（Anthropic skill 编写指南）。
- 改编自其它开源项目的 skill，在该 skill 目录放 `NOTICE.md` 保留原授权，让单独安装的包也带着它。
- 公开内容不含机密、令牌、个人路径或客户信息；安装和传播会把这些内容带到其它项目。
- Skill 行为改动记入 `CHANGELOG.md` 的 `[Unreleased]`，供安装者判断更新影响。

## 检查与协作

改动后运行 `python3 scripts/validate_skills.py`；[CI](.github/workflows/validate-skills.yml) 使用同一脚本，skill 目录内的相对链接由它检查，仓库级文档的路径与链接改动后人工核对；安装入口改动的本地试装方法见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

中文回复，标识符、命令、路径与服务名保持英文。贡献与 PR 流程见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。发版打 tag 先取得用户确认，因为 tag 对外标识可安装版本。
