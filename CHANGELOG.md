# Changelog

本项目的所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- SVG 仓库横幅 `assets/banner.svg`，展示在 README 顶部。
- 英文 `README.md`（主）与中文 `README.zh-CN.md`，顶部互相切换。

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
