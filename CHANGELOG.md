# Changelog

本项目的所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed

- `codex-dev`：修复 SKILL.md frontmatter 的 YAML 报错——`description` 里 `multi-agent: parallel`
  的 `: `（冒号+空格）被严格 YAML（GitHub frontmatter 渲染器）当成嵌套映射，报
  "mapping values are not allowed"；去掉冒号后的空格即可（skills CLI / 本仓校验脚本解析宽松，故功能未受影响）。
- `validate_skills.py`：新增严格 YAML 安全检查——frontmatter 值含未加引号的 `: ` 直接 CI 拦下，防再犯。

## [0.2.0] - 2026-06-13

### Added

- SVG 仓库横幅 `assets/banner.svg`，展示在 README 顶部。
- 英文 `README.md`（主）与中文 `README.zh-CN.md`，顶部互相切换。
- README 加 omegacode dashboard 截图 `assets/dashboard.png`。

### Changed

- `codex-dev`：**统一为单一 omega 引擎**——取消"串行/并发"双轨。所有 codex 派活（单任务或多任务）
  都跑成 omega workflow（N 个任务 = N 个 agent，独立则 `parallel`、有依赖则分批按序），因此
  **每次派活都有 dashboard + 完成通知 + 重连 + 跟踪地址**，解决"单任务跑几小时看不到进度"的黑箱。
  omega 改为必需依赖；返工统一为在 worktree 内再派一个 1-agent omega run；移除 `codex exec` 串行轨
  及其 stdin/超时雷区。已对 omegacode 源码验证：单 agent run 也有 dashboard、viewer 覆盖 every run、
  omega 本身无 serial/concurrent 概念（并发靠 `parallel`/`pipeline`）。
- `codex-dev`：并发轨改用 Bash `run_in_background` 跑 omega（不再 nohup detached）——omega 无 executor daemon、
  `run` 阻塞至完成（已对 omegacode 源码 + DESIGN.md 验证），进程退出即由 harness 通知 Claude 推进验收，
  与串行轨同机制、免 watcher；会话中途挂掉的场景由 `<BATCH>-run.json` + `--resume` 接管。
- `codex-dev`：SKILL.md 整本翻译为英文（含 `description` 与触发词，指令对 agent 更精确、更通用）；
  触发改用英文自然语 + `/codex-dev`。代码、流程、技术细节保持不变。
- `codex-dev`：并发轨新增「后台运行与重连」小节——detached 起跑即落盘
  runId/dashboard/pid，任何新会话（含终端已关）凭 `omega-run.json` +
  `omegacode runs` + `--resume` 重连，不依赖 watcher 进程存活。
- `codex-dev`：派单后把跟踪地址打印给用户（并发轨 dashboard 地址、串行轨 `events.jsonl` 路径）。
- `codex-dev`：并发编排脚本改名为 `<任务名>-fanout.workflow.js`——omega 看板按文件名显示 run，
  这样按项目/任务认出是哪个，不再千篇一律叫 `fanout`；重连从落盘的 `omega-run.json` 读回 workflow 路径。

### Fixed

- `codex-dev`：第三轮 codex 源码评审（对照本地 omegacode 源码）再修三处——
  ① **卡住→上报**显式化 + 防卡死 backstop：watchdog 措辞改准（30min 无进展 → 失败 stalled turn →
  失败任务 → 完成通知 → 按名上报），并补病态卡死（子进程吞 interrupt/SIGTERM）兜底：
  超 watchdog 窗口（~45min）且看板无进展即查 `runs`/日志、上报、`--prune-stale`，绝不无限等；
  ② **并发真正强制**：dispatch 加 `--concurrency 10`（omega 默认 100，原先文字写"3"也没生效）；
  CLI agent 内存占用小，固定上限 10 足够，不做机器探测，任务更多就排队；
  ③ `BATCH` 唯一性守卫**也查 `omega runs` 同名 run**（防"已注册但 run.json 未写"的窗口选错 run）。
  评审确认大部分保证 HOLD；移除 codex-exec 串行轨（无 omega 兜底 / 返工丢 codex 会话上下文）为既定取舍，按设计保留。
- `codex-dev`：第二轮 codex 联网源码评审修复（codex 自行 clone omegacode 逐条核对）——
  ① 空 `view:` 行不再误判为"omega 没起来"（viewer 起不来但 run 照常完成，验自 `cli.ts:439/448`）：
  runId 改从 `omega runs` 按唯一文件名权威获取，无 dashboard 时也始终打印日志跟踪地址，不再派单后自杀；
  ② `BATCH` 名加唯一性守卫（防同名批次覆盖 run.json/log/args）；
  ③ 重连 `J()` 把路径作为 argv 传入（不再插值进 Python 源码，路径含特殊字符也不崩）；
  ④ `~/.omegacode` 改 `${OMEGACODE_HOME:-~/.omegacode}`（尊重 omega 数据根覆盖）。
- `codex-dev`：去掉写死的 `~/.npm-global` 路径——omega 检测改用 `command -v omegacode`，
  安装口径统一为标准 `npm install -g omegacode`，可移植到任意机器。
- `codex-dev`：并发轨 runId 改为从 `omega-run.log` 的 `view:` 行解析（含真实端口），
  替代按 workflow 文件名匹配 `omegacode runs`（多个同名 run 会认错）。
- `codex-dev`：重连片段补回 `OMEGA` 探测使其自包含；`codex --version` 仅在 codex 存在时执行。
- `codex-dev`：codex 评审修复一批并发轨健壮性问题（均对 omegacode 源码验证）——
  resume 改用 `--args-file` 带回原 args（否则 `checkResumePreconditions` 因 args 不一致拒绝续跑）；
  `VIEW` 解析失败时硬停、不写空记录；重连的 `serve` 改后台起（前台会阻塞 `--resume`）；
  omega 检测/重连找不到即停；并发产物按 `<BATCH>` 前缀每批独立（不再互相覆盖）；
  `omega-run.json` 改用 python3 安全生成（路径含特殊字符不再损坏）；Step 0 增检 `python3`。

## [0.1.0] - 2026-06-13

### Added

- 首个公开发布。
- `codex-dev` skill：把开发任务派发给 OpenAI Codex CLI 实施的通用闭环
  （串行 `codex exec` / 并发 `omegacode` + worktree 物理隔离、机械验收、评审、合并）。
- 标准仓库骨架：`README`、`LICENSE`(MIT)、`CONTRIBUTING`、`.gitignore`。
- `scripts/validate_skills.py` 校验脚本 + `validate-skills` GitHub Action，
  自动校验每个 `SKILL.md` 的 frontmatter。

[Unreleased]: https://github.com/shengyy/agent-skills/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/shengyy/agent-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/shengyy/agent-skills/releases/tag/v0.1.0
