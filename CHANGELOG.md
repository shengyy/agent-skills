# Changelog

本项目的所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.4.0] - 2026-09-05

### Changed

- **codex-construction：默认模型切到 `gpt-6-astra`，effort 收敛为 `medium` / `high` / `xhigh` 三档**，
  新增「档位」一节。档位跟合同留给 codex 的裁量空间和出错代价走，不跟任务重要性走：
  `medium` 是施工默认档（合同已写明「做什么」）、`high` 用于留有设计空间的批和全批次审查、
  `xhigh` 只留给不可逆判断（架构定型、资金/并发/安全核心、最终态对抗审）。
  配套判据：升档不同档重试、审 ≥ 施工、xhigh 不因额度降档、省额度的抓手是合同粒度而非审查档、
  启动后核对日志头部 `reasoning effort:`。默认三段拆批各自标了档位。
- **终态改从 `-o LAST.md` 判，不再解析日志**：`codex exec` / `resume` 都收 `-o`，最终消息单独落盘，
  没有 prompt 回显撞标记的问题，`grep -x "tokens used"` 定位法整段删除。监控表按 `LAST.md` 有无 + 尾部标记重写。
- **权限旗标统一为 `--dangerously-bypass-approvals-and-sandbox`**：一个旗标同时关沙箱和审批，不依赖 config 里的
  `sandbox_mode` / `approval_policy`，exec 和 resume 都收（原 resume 走 `-c sandbox_mode=` 的特例删除）。
- **Prompt 按 GPT-6 官方指南调整**：五要素各用一个 XML 块；自主权条款加「无人值守、没人会回答问题、不停下来问」
  （GPT-6 更爱在多问一句能改变结果时停下提问）；明确不要求中途汇报和先出计划（会让模型 rollout 中途停）；
  过度测试列为过度工程的一种，验收时拒收镜像实现的低价值测试，并新增必写的「测试边界」条款（官方原话：可逆低影响改动不写镜像测试，过了就停）。
- 监控终态新增**额度耗尽**：无 `LAST.md`、尾部 `ERROR: You've hit your usage limit … try again at HH:MM`、
  exit 1——到时刻后续接（有进度 resume、零进度重跑），不算一轮、不升档。

### Fixed

v0.3.0 发布之后、本段之前累积的修正（此前未入 CHANGELOG）：

- 合同改走 stdin：argv 会把合同全文泄进 `ps`，诱发 codex 自我监控死锁（轮询自己零开工）。
- resume 改用显式 session id：`--last` 只在当前 cwd 找，找不到会静默新开空会话。
- resume 必须重传 effort；resume 子命令不接受 `-s`。
- 修复循环熔断：阻断性修复超 3 轮不收敛或修 A 破 B 振荡，回方案层重裁。

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
