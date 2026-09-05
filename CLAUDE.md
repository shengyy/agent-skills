@AGENTS.md

## Claude Code

- 同一仓库的各 worktree 共用一份设备本地 auto memory；它不是分支、工作树或跨设备事实源，规则、架构决定和验收口径写回 `AGENTS.md` 或对应文档 owner。
- 跨设备共享的项目设置归 Git 跟踪的 `.claude/settings.json`，设备专属覆盖归 `.claude/settings.local.json`。
- Claude 专属且确需按路径延迟加载的细则归 `.claude/rules/*.md`，并用 `paths:` frontmatter 限定作用域；多 Agent 共用的规则写在适用范围内最近的 `AGENTS.md`，不在两处复制。
