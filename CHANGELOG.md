# Changelog

本项目的所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-07-28

### Changed

- **整体替换：`codex-dev` / `codex-dev-native` → `codex-construction`**。旧两个 skill 是给上一代模型写的
  （沙箱管道、写权限 allowlist、任务书模板、并发 registry），大量篇幅在替引擎和模型做它们如今自己能做好的事，
  也是「总断、不反馈」的根源。新一代模型（GPT‑5.6+ / Claude 5+）下编排价值收敛为**分工、边界、验收**三件事，
  用一个约百行的轻量 skill 整体替换：裸调 `codex exec -s danger-full-access`（不走插件受限沙箱）、
  launch-only nohup 启动、三态监控（`tokens used` 收尾 / 进程消失 / 日志静默）、prompt 五要素
  （现场 / 合同指针 / 范围 / 真红线 / 边界与交付协议）、分阶段 commit + 验收包、改-审循环
  （审查用全新会话保独立性、修复轮 `resume --last`）、主代理抽验门禁。
  核心机制：**放权 + 监工过度工程**——codex 独干的系统性偏差是过度工程，主代理只在方案裁决、
  分批验收、BLOCKED 三点介入；自主权条款允许 codex 对施工中发现的真实问题在范围内根因修复。
  在一次真实整日架构重构（6 阶段、净删万余行、三轮长时施工零卡死）中打磨成型。

### Removed

- `skills/codex-dev/`、`skills/codex-dev-native/`（被 `codex-construction` 取代，历史见 git）。

## 更早版本

0.2.x 及更早的记录（含已删除的 skill）见 git tag 与提交历史，本文件不保留。
