# Changelog

本项目的所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- SVG 仓库横幅 `assets/banner.svg`，展示在 README 顶部。
- 英文 `README.md`（主）与中文 `README.zh-CN.md`，顶部互相切换。
- README 加 omegacode dashboard 截图 `assets/dashboard.png`。

### Changed

- `codex-dev`：并发轨新增「后台运行与重连」小节——detached 起跑即落盘
  runId/dashboard/pid，任何新会话（含终端已关）凭 `omega-run.json` +
  `omegacode runs` + `--resume` 重连，不依赖 watcher 进程存活。
- `codex-dev`：并发派单后第一时间把 omega dashboard 地址报给用户，便于实时跟踪进度。

### Fixed

- `codex-dev`：去掉写死的 `~/.npm-global` 路径——omega 检测改用 `command -v omegacode`，
  安装口径统一为标准 `npm install -g omegacode`，可移植到任意机器。
- `codex-dev`：并发轨 runId 改为从 `omega-run.log` 的 `view:` 行解析（含真实端口），
  替代按 workflow 文件名匹配 `omegacode runs`（多个同名 run 会认错）。
- `codex-dev`：重连片段补回 `OMEGA` 探测使其自包含；`codex --version` 仅在 codex 存在时执行。

## [0.1.0] - 2026-06-13

### Added

- 首个公开发布。
- `codex-dev` skill：把开发任务派发给 OpenAI Codex CLI 实施的通用闭环
  （串行 `codex exec` / 并发 `omegacode` + worktree 物理隔离、机械验收、评审、合并）。
- 标准仓库骨架：`README`、`LICENSE`(MIT)、`CONTRIBUTING`、`.gitignore`。
- `scripts/validate_skills.py` 校验脚本 + `validate-skills` GitHub Action，
  自动校验每个 `SKILL.md` 的 frontmatter。

[Unreleased]: https://github.com/shengyy/agent-skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/shengyy/agent-skills/releases/tag/v0.1.0
