# agent-skills · Agent 指引

公开的 Agent Skills 合集（MIT），用 `skills` CLI 一键分发到 Claude Code、Codex、Cursor 等。本文件是各编码 Agent 共用的仓库级规则；`CLAUDE.md` 导入本文件。人类贡献流程、发版步骤见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，不在这里复制。

优先级：用户当次指令 > 本文件 > 其它文档。`skills/<name>/SKILL.md` 与 `scripts/validate_skills.py` 是事实。

## 硬约束

- **一个 skill 一个目录。** `skills/<name>/` 目录名即 skill 名（小写、`-` 连字），`SKILL.md` frontmatter 的 `name` 必须与目录名一致，`description` 写清触发场景与触发词。附带脚本、模板、参考资料放该目录下的 `scripts/`、`references/`、`assets/`，用相对路径引用。
- **唯一 owner。** 版本号只在 `VERSION` 与 `CHANGELOG.md` 版本段；README 徽章读 git tag。`README.md` 与 `README.zh-CN.md` 同步更新，不让两份说法漂移。
- **禁补丁、禁兼容。** skill 面向当前一代模型（GPT‑6 / Claude 5+）：少约束、多放权，只保留分工、边界、验收三类内容；旧模型时代的护栏、沙箱管道、并发注册表之类的过程控制一律删掉，不保留兼容版本。
- **单文件规模。** `SKILL.md` 保持在几百行内；超过 800 行先按职责拆到 `references/`。
- **公开仓库。** 不把机密、令牌、个人路径、客户信息写进任何文件。
- **门禁。** 改动后运行 `python3 scripts/validate_skills.py`（CI 跑同一个脚本）；改了 skill 行为就在 `CHANGELOG.md` 的 `[Unreleased]` 记一笔。

## 自主权与交付

在上述边界内默认放权，可以大改；只在真实的范围变更、发版打 tag 或只有用户能给的输入时停下来。用户在描述问题或提问而不是要求改动时，交付物是你的判断。中文回复，标识符与命令保持英文；交付说明改了什么、跑了什么校验、未验证项。
