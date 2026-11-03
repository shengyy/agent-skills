# Changelog

本文记录版本历史与待发布变更；当前发布版本号见 [`VERSION`](VERSION)，发版流程见 [`CONTRIBUTING.md`](CONTRIBUTING.md#发布新版本)。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

方向：审查换成实证。一个发现要有一次运行证明才算数；读代码推出来的意见每轮都能再挑出一批，照着改只会堆防御代码和抽象，是过度工程的主要来源。省下的预算投到让真实应用可被驱动、在测试够不着的地方做穷举检查。思路与两个新 skill 改编自 [pstack](https://github.com/cursor/plugins/tree/main/pstack)（MIT，授权见各 skill 的 `NOTICE.md`）。

### Added

- **`app-verification`**：为项目生成并维护项目本地的 `verify-<app>` skill——启动、体检、驱动、证据、清理五节加功能地图，交付前完整跑一遍并确认证据熬过清理；维护流程（逐功能源码核对 + 一次实测、只改 verify skill 自己、结局 clean / changed / blocked）在 `references/maintain.md`。
- **`formal-verification`**：选出错代价最高、测试最难覆盖的承诺，按问题选工具（模型检查器默认 TLA+、代码级验证器、基于属性的测试、证明），要求每个性质先在坏变体上失败、发现不削弱、写明界与假设、记录覆盖与同步点，生成项目本地 verify skill 并用一次破坏性改动证明它抓得到；维护流程（代码变化后判漂移还是 bug）在 `references/maintain.md`。

### Changed

- **`codex-construction` 以运行结果为准**：新增原则「以运行结果为准」。简报的交付写成能跑的检查；运行约定要求每项交付按用户的方式真正跑过，验收包的「测试状态」改为「验证证据」（命令与关键输出）。验收读 diff 只做减法，测试用「行为改坏会失败、只重构内部仍通过」检验。
- **「改-审循环」改为独立验证**（`references/verification.md`）：全新会话的任务从读 diff 列问题改为把改动跑起来、设法让它违背意图；每个发现要附命令、实际输出和应有输出，风格、命名、结构和「将来可能」不报。主代理重跑裁定，只有用户会碰到的 bug、失败的门禁、写错的文档进修复轮，基线已有的问题不算这批。完整验证一批一次，修复后只重跑失败的命令。结尾标记 `REVIEW DONE` 改为 `VERIFY DONE`。档位删去「最终态对抗审」与「审查档不低于施工档」，独立验证参考 `high`。
- **用法不变**：`/codex-construction` 或「安排 codex 施工」照旧直接用，不需要任何项目准备；`app-verification` / `formal-verification` 是可选增强，主代理只在值得时向用户提议，用户同意才作为额外一批去做。
- **`codex-construction` 渐进式披露**：主文件保留每次派工都走的主路径；独立验证与 nohup 回退拆到 `references/`，在用到的位置写明何时读。`resume` 的 CLI 事实提成独立的「续接」一节，供 BLOCKED、无交付、额度耗尽、崩溃和修复轮共用；nohup 回退补上续接的包法。
- 仓库约定：「超过 800 行才拆」改为渐进式披露原则（按用不用得上拆，references 只引一层，参照 Anthropic skill 编写指南）；改编的 skill 用 `NOTICE.md` 保留原授权。
- `validate_skills.py` 新增链接检查：skill 内 `.md` 的相对链接必须指向 skill 目录内存在的文件（跳过代码块与行内代码）。

### Fixed

发布前的端到端试跑暴露、已修复并重跑确认：

- 运行约定：Astra 把验收包另存为 `ACCEPTANCE.md` 提交进产品仓库。改为验收包只写在最终消息里，过程记录不进仓库。
- 独立验证：验证会话为旧代码登记的 `git worktree` 用完未拆。结尾补上「拆掉自己起的进程和 worktree，证据留着」。
- `app-verification`：生成的 verify skill 只有一键全量回归，换到加了新功能的代码上照样报 PASS、看不见新行为。改为驱动必须能单独走一个功能、换自己的输入并留证；证据目录不进版本控制。
- `formal-verification`：生成的 verify skill 与 `verify-<app>` 同名会互相覆盖，一次性运行输出被提交。改为名字带上验证区域，仓库只放能重跑出结果的东西。

试跑环境：Claude Code（主代理）+ codex-cli 0.166.0 / `gpt-6-astra`，在一个预埋领取竞态的 SQLite 队列玩具项目上。施工（`medium`）→ 主代理用真实 CLI 验收 → `resume` 修复轮（session id 一致）→ 全新会话独立验证（`high`）：末行 `VERIFY DONE`、每项交付附命令与输出、发现为无、验证前后 HEAD 与工作树一致。`app-verification` 生成的 skill 由冷读者照做跑通，并单步验证了它没见过的新功能。`formal-verification` 在没有 Java 时改用有界穷举，抓到预埋竞态并在两个真实进程上复现，产品代码未改，范围如实写明。

## [0.7.0] - 2026-10-31

### Changed

- **`codex-construction` 适配「Claude 当主代理、Codex 施工」**：启动拆成两条路径。主代理的工具能后台运行命令并在退出时唤醒（如 Claude Code Bash 的 `run_in_background`）时，把 `codex exec` 直接交给后台任务，退出即收到通知，不再轮询；否则走 `nohup` 回退，`exec`、`$!`、组杀这几条只属于这条路径。已在 Claude Code 2.1.314 + codex-cli 0.166.0 上端到端跑通（后台审查、退出唤醒、`-o` 落盘、`REVIEW DONE`）。
- **其余盯梢也交给后台任务**：卡死不会退出、也就没有通知，配一个看门狗后台任务兜底，盯这一次调用的日志和 `-o` 文件（超时未动或 `-o` 文件出现即退出）；额度耗尽用后台 `sleep` 当定时器，到点按启动一节续接、看门狗随之重起；`BLOCKED` 要用户拍板时用推送通知叫回用户；并行批次各起一个后台任务、到一批验收一批。
- **写明后台任务的时限**（Claude Code 官方文档）：本地交互会话不限时；无人值守会话默认 30 分钟、最长 2 小时（`-p` 文本 prompt 默认 10 分钟），可用环境变量调高；覆盖不了整批施工就走 nohup 回退。
- 修复轮模板改为 stdin 传要求，并给出独立的 `-o` 文件和日志。
- **模型口径统一**：默认 `gpt-6-astra` 并每次显式传 `-m`，删去与启动命令矛盾的「以 `config.toml` 为准」——config 的默认模型和档位是给交互用的，各机不同。
- **档位保持 `medium` / `high` / `xhigh` 三档并写明理由**：`low` 撑不起无人值守的施工，`max` / `ultra`（codex-cli 0.166.0 实测都接受）多花的钱换不来相应的提升，只在用户点名时用；已在 `xhigh` 还不行就回头改简报。resume 模板不再写死档位枚举。
- **写简报**：篇幅花在仓库给不了的东西上（为什么做、完成条件、重点、红线、品味）；仓库里查得到的只给能省掉大量摸索的线索。红线明确为完整权限之外唯一的边界，每条附一句外部代价。
- `description` 补英文触发词 delegate to Codex。

## [0.6.0] - 2026-10-08

### Changed

- **`codex-construction` 统一口径为「事实写死，判断放开」**，参照 Anthropic（Claude Fable 5.1 / Opus 5.5）与 OpenAI（GPT-6 Astra）的提示指南。新增「原则」一节：硬规则只留不可逆的动作边界与 CLI 实测事实，其余写成原则和理由；放开怎么做、写清做什么；用户明确要求优先于 skill。
- **给 Codex 放权**：设计、实现、验证方式、commit 切分与可逆取舍自主决定、不必请示，假设写进验收包；新抽象、配置项、兼容层从禁止改为说明为什么值得；路上发现的小而明确的问题可以顺手修，单独 commit 供主代理核实撤回。
- **写清边界**：交付即完成条件，只交初版或以「下一步」收尾不算完成；`BLOCKED` 用于不可逆决定、越红线或排除不了的阻塞，停下前先做完不依赖它的部分；简报排除的部分不顺手改。
- **给主代理放权**：简报五段改为检查清单、篇幅随任务；档位改为按推理预算分配的原则加参考；删去固定拆批切法、审查与熔断轮数、卡死时长。
- **审查与监控**：审查改用自己的结尾（只审不改、末行 `REVIEW DONE`）；平时只判活，疑似卡住再看日志；自我监控死锁限定为轮询 codex 自己的 pid。验收增加范围检查、逐条核实自主判断与顺手修复。
- 仓库约定同步上述口径。本版改动经 GPT-6 Astra 两轮全新会话审查。

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
