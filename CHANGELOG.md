# Changelog

本文记录版本历史与待发布变更；当前发布版本号见 [`VERSION`](VERSION)，发版流程见 [`CONTRIBUTING.md`](CONTRIBUTING.md#发布新版本)。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed

- **`codex-construction` 统一口径为「事实写死，判断放开」**，参照 Anthropic 对 Claude Fable 5.1 / Opus 5.5 与 OpenAI 对 GPT-6 Astra 的提示指南：新增「原则」一节，硬规则只留不可逆的动作边界与 CLI 实测事实，其余写成原则和理由；放开怎么做、写清做什么；用户明确要求优先于 skill。给 Codex 放权：设计、实现、验证方式、commit 切分与可逆取舍自主决定、不必请示，假设写进验收包；新抽象、配置项、兼容层从禁止改为说明为什么值得；BLOCKED 用于需要不可逆决定或排除不了的阻塞，停下前先做完不依赖它的部分；审查改用自己的结尾（只审不改、末行 `REVIEW DONE`），不再照抄施工运行约定；验收包骨架并入运行约定；监控平时只判活、疑似卡住再看日志，自我监控死锁限定为轮询 codex 自己的 pid。路上发现的小而明确的问题可以顺手修，单独 commit、列入验收包由主代理核实，大的或需要取舍的写成后续建议。同时写清边界：交付即完成条件，只交初版或以「下一步」收尾不算完成；测试规模参照相邻测试、临时验证脚本不必留下。给主代理放权：简报五段改为检查清单、篇幅随任务；档位改为按推理预算分配的原则加参考；删去固定拆批切法、审查与熔断轮数、卡死时长，保留不收敛就重写简报的原则。验收增加范围检查与逐条审视 Codex 的自主判断。删去重复表述，description 收短。CLI 命令与易错点不变；改动经 GPT-6 Astra 两轮全新会话审查。
- 仓库约定同步：skill 的硬规则只留不可逆边界与实测事实，偏差用「说明理由」约束而非禁令。

## [0.5.0] - 2026-10-07

### Changed

- **`codex-construction` 按「简报」重构**：「Prompt 五要素」（现场 / 合同指针 / 范围 / 红线 / 交付）改为「写简报」——正文五段：背景、交付、重点、质量与资源、风格与品味，结尾固定红线与可照抄的运行约定；附完整示例和派工前自检（简报填不出的段落先问用户，不替用户编）。新增「验收」一节，按简报的交付、重点、质量与品味验收。档位、监控、批次、改-审循环压缩为判据，删去不再必要的施工者身份声明（stdin 传简报已消除误认根因）。CLI 契约不变：stdin 传入、`exec` 启动、`-o LAST.md` 判终态、显式 session id 续接、resume 重传 effort。
- 仓库指引补齐按任务读取的路由，双语 README 增加文档地图；贡献流程引用仓库约定的唯一 owner。
- 文档职责审计：双语 README 补齐逐文件地图，skill 执行细则改为链接其 owner；贡献指南明确结构校验 owner，PR 模板按贡献流程链接适用检查项。
- 目录职责审计：双语 README 登记全部被跟踪的顶层目录与第二层目录，区分仓库级脚本和展示素材与各 skill 安装包的内容；Agent 路由同步指向目录地图。

## [0.4.1] - 2026-09-05

### Fixed

- **启动行加 `exec`**：`nohup bash -c 'exec codex …'`。没有 exec 时 `$!` 是 bash 包装进程、codex 是它的子进程，
  `kill -0` 判活仍对，但「自我监控死锁立杀重派」只杀包装会留下 codex 孤儿继续跑。监控一节补了说明。
- 长修复轮的 resume 同样按启动一节后台起，不在前台等。

0.4.0 的改动已在 gpt-6-astra 上实测通过。冒烟：xhigh 服务端接受；`--dangerously-bypass-approvals-and-sandbox`
在 exec / resume 下头部均回显 `sandbox: danger-full-access` + `approval: never`；`-o` 在正常结束和 BLOCKED 时写出、
进程被杀时不写；resume 重传 effort 生效。端到端（全 medium，五次运行合计 4 分钟）：stdin 合同 + XML 五要素施工并
commit，验收包五项齐全；产品级裁决点老实打 `BLOCKED[批2]` 停在边界零改动；显式 session id resume 下裁决后续做到
`STAGE 2 DONE`；全新会话审查只审不改，自行用只读方式跑门禁；修复轮无问题时 `STAGE 3 DONE no-op`；五次日志里
自我监控轮询 0 行；全权核验通过（仓库外写文件、curl 外网）。

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
