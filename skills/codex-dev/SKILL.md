---
name: codex-dev
description: 把开发任务派发给 OpenAI Codex CLI 实施的通用闭环。Claude 出方案写任务书、编排并发（omegacode/worktree 物理隔离）、机械验收 + 评审 + 合并提交；codex 在 workspace-write 沙箱里写代码。用户说"派工"、"丢给 codex"、"codex 实施/开发 <任务>"、"并发派几个 codex"或 /codex-dev 时使用。仅评审/咨询（不写代码）走 gstack-codex，不用本 skill。
---

# /codex-dev — codex 派工开发闭环

分工：Claude 出方案、写任务书、编排、验收评审、合并提交；codex 只实施。整个流程自动推进，只在 BLOCKED、合并冲突需裁决、或突破角色分工时停下来问用户。每个任务状态变化时向用户报一行进度。**派单后把该任务的跟踪地址打印给用户**：并发轨给 omega dashboard 地址，串行轨给 `tail -f` 的 `events.jsonl` 路径。

两条轨道，共享同一套任务书/验收/评审/合并纪律：

| 轨道 | 适用 | 工具 |
|---|---|---|
| A 串行 | 单任务，或任务间有依赖 | `codex exec` + `resume <thread_id>`（返工保留会话上下文） |
| B 并发 | ≥2 个互相独立的任务 | `omegacode` workflow（确定性编排 + watchdog + journal + 实时 dashboard）+ Claude 预建 worktree |

## Step 0：前置检查

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
command -v codex >/dev/null && codex --version || echo "CODEX_NOT_FOUND"
[ -f "${CODEX_HOME:-$HOME/.codex}/auth.json" ] || [ -n "$CODEX_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || echo "AUTH_MISSING"
OMEGA=$(command -v omegacode || echo "")
git -C "$REPO_ROOT" status --porcelain | head -5
mkdir -p "$REPO_ROOT/.runtime/codex-dev"
```

- `CODEX_NOT_FOUND` → 停：`npm install -g @openai/codex`。`AUTH_MISSING` → 停：`codex login`。
- codex 0.120.0–0.120.2 有 stdin 死锁缺陷 → 警告升级，不阻塞。
- `$OMEGA` 为空且本次需要并发轨 → **不要自动安装**（用户环境级修改且走网络），把标准全局安装命令给用户确认：`npm install -g omegacode`（装到用户 npm 全局 prefix；若该目录需权限，提示用 sudo 或先 `npm config set prefix <可写目录>` 并把其 `bin` 加进 PATH），同意后再装并跑 `omegacode doctor` 确认 codex worker OK；不同意则退回串行轨逐个跑。
- **沙箱铁律**：用户 `~/.codex/config.toml` 全局可能是 `sandbox_mode = "danger-full-access"`（桌面版配置）。派工命令必须显式传 `-s workspace-write`（omegacode 侧 `defaultSandbox: "workspace-write"`），永不依赖全局默认；发现漏传视为事故，立即终止重派。
- `.runtime/`、`.omegacode/`、`.claude/worktrees/` 应在项目 .gitignore 里；不在则补上再开工。

## Step 1：任务分解与档位（防打架第一道闸门）

并发冲突的根治在派发前的编排，不在事后调解：

1. **独立性检查**：为每个候选任务预估"将改动的文件/模块集合"（依据项目规约文档与现有代码结构）。任两个任务文件集相交、或存在 import 依赖/接口耦合 → 不得并发，改串行或合并为一个任务。
2. **依赖排序**：B 依赖 A 的产出 → A 合并回主分支后才派发 B。
3. **并发上限 3**：codex 任务吃 API 配额 + 本机测试资源，超出排队。
4. **模型与推理力度分级**（显式传参，不吃全局默认；用户点名时照办）：

| 档位 | 适用 | 参数 |
|---|---|---|
| 杂活 | 改配置、机械重构、补文档 | `gpt-5.5` + `medium` |
| 普通（默认） | 单模块功能、修 bug、补测试 | `gpt-5.5` + `high` |
| 困难 | 跨模块设计、资金/账务/撮合类核心逻辑、并发与时序、性能 | `gpt-5.5` + `xhigh` |

档位由 Claude 评估后定，派发进度汇报里注明（如"T9 回填管线 → xhigh"）。

## Step 2：写任务书

任务书写到 `$REPO_ROOT/.runtime/codex-dev/<slug>/brief.md`（slug 用任务编号或短英文 kebab-case）。**先读当前项目的 CLAUDE.md / AGENTS.md / 相关规约文档，把项目红线与质量约束提炼进"硬约束"段**——任务书必须自包含，不假设 codex 读过对话历史。

模板（正文跟随项目语言习惯，代码标识符/路径英文）：

```markdown
# 任务：<一句话目标>

## 目标与验收标准
- <可机械验证的验收点，逐条>

## 规约依据
- <项目 spec 文档 §节：关键原文引用，不能只给节号>
- <任务清单条目原文>

## 环境说明
- 工作目录是 <主仓库 / 本仓库的独立 worktree>，构建/测试环境已就绪。
- 禁止安装依赖与任何联网操作（沙箱通常断网，但这是行为红线不是技术兜底）；缺依赖或确需网络时停下，在最终报告里说明，不要绕过。

## 硬约束
1. 禁止一切 git 写操作（commit/push/rebase/checkout/stash）。只改工作区文件，版本操作由评审方完成。git 写操作可能被沙箱拦截，属预期，不要重试。
2. 写入范围仅限 <项目定义的实施方写入白名单；无定义则"本仓库内"，并列出明确禁区>，越界即任务失败。
3. <从项目 AGENTS.md/CLAUDE.md 提炼的质量约束与红线，逐条>
4. 新增逻辑必须带测试；自行运行 <项目 lint/test 命令> 通过后才算完成。

## 完成报告要求
最终消息列出：改动文件清单、新增测试清单、lint/test 运行结果、未尽事项与已知限制。
```

## Step 3：执行环境（防打架第二道闸门）

**默认一个任务一个分支，永不直接在主分支上开发**（用户明确说"就在当前分支改"才例外）。

**主工作区有未提交改动 → 先分类再决定 base**：改动如果正是本任务依赖的基线（用户改到一半让 codex 接力），从主分支开 worktree 会让 codex 基于旧代码开发、合并错位——必须停下来和用户确认（先提交、或以当前状态建任务分支作 base）；改动与任务无关 → 才按下面流程从主分支隔离。

**单任务且工作区干净** → 主工作区直接建任务分支跑（省 worktree 与环境重建开销）：

```bash
git -C "$REPO_ROOT" checkout -b "codex/$SLUG"   # 派工期间主工作区归该任务
```

**并发任务，或工作区脏（无关改动）** → 每任务一个 worktree，物理隔离。同工作区并发必然互踩：git 状态无法归属、测试缓存冲突、返工时 codex 看到他人改动会"顺手修复"。约定不可靠，隔离才可靠：

```bash
SLUG=<slug>
WT="$REPO_ROOT/.claude/worktrees/codex-$SLUG"
git -C "$REPO_ROOT" worktree add "$WT" -b "codex/$SLUG" <主分支>
```

然后**按项目构建方式在 worktree 里重建环境**（codex 沙箱断网，环境必须 Claude 预装）。Python 项目警告：若主仓库 venv 内项目是 editable 安装（site-packages 有 `__editable__*.pth`），其路径硬编码指向主仓库——worktree **必须全新建 venv 重装**，共享或复制会让测试跑到主仓库代码：

```bash
python3 -m venv "$WT/<pkg>/.venv" && "$WT/<pkg>/.venv/bin/pip" install -q -e "$WT/<pkg>[dev]"
```

最后在 worktree 里跑一遍项目 lint/test：**基线必须绿**，红着派工无法归因；基线红 → 先修主分支，不派工。

## Step 4A：串行轨（codex exec）

```bash
RUN="$REPO_ROOT/.runtime/codex-dev/$SLUG"; WORK=${WT:-$REPO_ROOT}
codex exec -s workspace-write \
  -C "$WORK" \
  -m gpt-5.5 -c 'model_reasoning_effort="<档位>"' \
  --json -o "$RUN/report.md" \
  "$(cat "$RUN/brief.md")" \
  </dev/null 2>"$RUN/stderr.log" > "$RUN/events.jsonl"
```

派单后把跟踪地址打印给用户：`tail -f "$RUN/events.jsonl"`（事件流逐步更新）。

执行雷区（违反即翻车）：

- **stdin 必须 `</dev/null`**：codex 总是读 stdin，不关闭就永久阻塞（症状：零输出、零 CPU、貌似挂起）。**管道陷阱**：`echo "..." | codex ... </dev/null` 里 `</dev/null` 会覆盖管道，codex 收到空输入——prompt 一律走位置参数，永不走管道。
- 思考 token 走 stderr，落盘到 `$RUN/stderr.log`（不要丢 /dev/null，排障要用；最终汇报只摘关键错误，不直接外传内容）。
- codex **无中间输出**：进程被提前杀掉时 `report.md` 为空且不报错。空文件 = 超时/被杀，不是"没改东西"。
- 用 Bash `run_in_background` 跑；超时按档位：medium 300s / high 600s / xhigh 1200s。预计超 15 分钟的任务先拆小。
- `-C` 指向仓库根（或 worktree 根）时整个目录可写——目录级白名单靠 Step 5 越界检查兜底。`workspace-write` 通常默认断网，但**不要把"无网络"当成技术保证**（config 可覆盖）——联网禁令以任务书行为约束为准。

派发后立即写 `$RUN/state.json`（崩溃恢复用）：

```json
{"slug":"...","phase":"dispatched|accepted|rework-N|merged|failed|blocked",
 "track":"exec|omega","thread_id":"...","worktree":"...","branch":"...","tier":"high"}
```

完成后取会话 id 与用量（返工必用；**严禁 `resume --last`**，并发或多会话时会指错）：

```bash
THREAD_ID=$(head -1 "$RUN/events.jsonl" | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4)
grep '"type":"turn.completed"' "$RUN/events.jsonl" | tail -1
```

失败隔离：非零退出或 events 为空 → 先读 `$RUN/stderr.log` 定位（auth、限流、版本缺陷），可修则修后重跑一次；连续两次失败 → 标 `failed`，不拖垮其他任务，汇总时报告。

## Step 4B：并发轨（omegacode）

前提：各任务 worktree 与环境已按 Step 3 备好。把 workflow 写到 `$REPO_ROOT/.runtime/codex-dev/<本次任务名>-fanout.workflow.js`——**前缀用本次派工的任务/项目名**（omega 看板按文件名显示 run，这样一眼认出是哪个，而非千篇一律的 fanout）；`-fanout.workflow.js` 后缀固定，标明这是编排脚本：

```js
export const meta = {
  name: "codex-dev-fanout",
  description: "并发派工：每任务一个 codex agent，在预建 worktree 内实施",
  defaultProvider: "codex", defaultModel: "gpt-5.5",
  defaultSandbox: "workspace-write",
  phases: [{ title: "Implement" }],
}
const REPORT = {
  type: "object", required: ["files_changed", "tests_added", "test_result", "notes"],
  properties: {
    files_changed: { type: "array", items: { type: "string" } },
    tests_added: { type: "array", items: { type: "string" } },
    test_result: { type: "string" }, notes: { type: "string" },
  },
}
phase("Implement")
return await parallel(args.tasks.map((t) => () =>
  agent(t.brief, { label: t.slug, cwd: t.worktree, effort: t.effort, schema: REPORT })
    .then((r) => ({ slug: t.slug, report: r }))
))
```

调用（`tasks[].brief` 传任务书全文）。**后台 detached 起跑，并把可重连的真相落盘**——omega 是 nohup detached 进程，本会话/终端关掉它照样在后台跑（优点：不占会话），但正因如此，起跑就要记下 runId / dashboard / pid，断了才找得回（见下「后台运行与重连」）：

```bash
RUN_DIR="$REPO_ROOT/.runtime/codex-dev"; mkdir -p "$RUN_DIR"
WF="$RUN_DIR/<本次任务名>-fanout.workflow.js"     # 上面的 workflow 就写到这里；文件名即看板 run 名
ARGS=$(python3 -c 'import json;print(json.dumps({"tasks":[...]}))')

nohup "$OMEGA" run "$WF" --args "$ARGS" >"$RUN_DIR/omega-run.log" 2>&1 &
OMEGA_PID=$!

# omega 起跑即把 view URL 写进日志（**别加 --json**，会抑制该行）；从日志解析出本次 run 的地址
for _ in $(seq 1 20); do
  VIEW=$(grep -oE 'http://127\.0\.0\.1:[0-9]+/#/run/wf_[0-9a-f]+' "$RUN_DIR/omega-run.log" | head -1)
  [ -n "$VIEW" ] && break; sleep 0.5
done
printf '{"runId":"%s","pid":%s,"dashboard":"%s","workflow":"%s","log":"%s/omega-run.log"}\n' \
  "${VIEW##*/}" "$OMEGA_PID" "$VIEW" "$WF" "$RUN_DIR" > "$RUN_DIR/omega-run.json"
echo "▶ omega dashboard: $VIEW"   # 派单后把这个地址打印给用户
```

- **把 dashboard 地址（`$VIEW`）打印给用户**——只读 web 看板，实时看各 codex 的 phase / 进度 / token；是完整 per-run 地址（带 `/#/run/<runId>`），多次派单也认得对那个。
- 关键设计：**不用 omegacode 的 `worktree:` 选项**（它自建 worktree 时 Claude 插不进装环境这步），用 `cwd:` 指向预建 worktree——omegacode 纯做确定性编排（并发调度、30 分钟无进展 watchdog、journal、token 统计），worktree 生命周期归 Claude。
- 它经 `codex app-server` JSON-RPC 驱动 codex，串行轨的 stdin/超时雷区不适用。
- runId 起跑时就由 omega 写进 `omega-run.log` 的 `view:` 行（上面已解析落盘，含真实端口）；完成后从 `omega-run.log` 或 `~/.omegacode/runs/<runId>/` 读结构化结果。
- 单个 agent 失败在结果数组里是 null/failed 状态——只打回该任务，不影响其余。
- 附加玩法（用户点名才用）：困难任务可跑内置 `bake-off`（codex 与 claude-code 在隔离 worktree 各自实现，盲评出胜者）或 `multi-provider-review`（双模型独立评审再合成）。

### 后台运行与重连

omega 起跑后是 detached 进程，会话/终端关掉它仍在后台跑。这是并发轨的核心优点（不占会话），但要求**真相落盘、绝不依赖某个 watcher 进程活着**——否则会话一死就只剩孤儿 run、没人通知，下次进来又得满世界找它。

- **真相来源**（断会话也在）：`$RUN_DIR/omega-run.json`（runId / dashboard / pid）+ omega 自身的 `~/.omegacode/runs/<runId>/` journal。
- **watcher 是可选的即时提醒**：在线时可另起后台轮询 `"$OMEGA" runs`、结束时通知用户；但它只是锦上添花，**不是真相来源**，死了不影响重连。
- **任何新会话重连**（哪怕原终端已关）：

  ```bash
  OMEGA=$(command -v omegacode) || echo "omegacode 不在 PATH → 先 npm install -g omegacode"
  RUN_DIR="$(git rev-parse --show-toplevel)/.runtime/codex-dev"
  cat "$RUN_DIR/omega-run.json"                 # 取 runId / dashboard（含真实端口）
  "$OMEGA" runs                                 # 还在跑？看 status / agents 数
  "$OMEGA" serve                                # 重开 dashboard（自动选端口，已起则复用）
  WF=$(grep -oE '"workflow":"[^"]*"' "$RUN_DIR/omega-run.json" | cut -d'"' -f4)
  "$OMEGA" run "$WF" --resume <runId>           # 崩/中断 → 只续跑未完成部分（workflow 路径从落盘记录读）
  ```

- 收尾后清理：`"$OMEGA" runs --prune-stale` 清掉已死的 run。

## Step 5：机械验收（每任务独立；任一失败 → Step 7 打回）

1. **越界检查**（沙箱只隔离 worktree 之间，不隔离其内部目录，事后校验是硬闸门）：

```bash
git -C "$WORK" status --porcelain | cut -c4- | grep -vE '^(<项目写入白名单正则>)' || echo SCOPE_OK
```

越界文件：已跟踪 `git -C "$WORK" checkout -- <file>` 还原，未跟踪删除，打回意见中点名。

2. **lint + test**：在 `$WORK` 里跑项目命令，失败输出原样留作打回材料。
3. codex 的完成报告（report.md / 结构化 REPORT）只当线索，**不当结论**。

## Step 6：评审（Claude 亲自做，不得委托回 codex）

对 `git -C "$WORK" diff` + 新增文件逐项过：

- 项目评审清单（从项目 CLAUDE.md 提炼，如本仓库的"撮合规则逐条对应 / agentio 时间闸门无泄漏 / journal 只插不改"三件事）。
- 项目红线扫描（如自动化路径禁 `dry_run=false`）；无静默 fallback / 吞异常 / 捏造默认值。
- 质量阈值（如 AGENTS.md 的文件/函数行数、禁泛名模块）。
- 任务书验收标准逐条对照实现与测试；缺测试 = 未完成。

独立判断：关键断言到代码里核实，不轻信 codex 的自我声明。

## Step 7：打回返工（每任务最多 3 轮）

评审意见写到 `$RUN/rework-brief.md`：逐条"问题、位置 file:line、期望行为、引用的规约条目"；若评审方动过工作区（如还原越界文件），明确告知。**评审意见一律走位置参数**——`echo "..." | codex ... </dev/null` 的 `</dev/null` 会覆盖管道，codex 收到的是空输入。

- 串行轨（resume 保留原会话上下文；resume 子命令没有 `-s`/`-C` flag，沙箱继承行为不赌——用 `-c` 显式钉死）：

```bash
codex exec resume "$THREAD_ID" -c 'sandbox_mode="workspace-write"' --json \
  "$(cat "$RUN/rework-brief.md")" </dev/null 2>"$RUN/stderr-rework-<N>.log" > "$RUN/rework-<N>.jsonl"
```

resume 找不到会话或 cwd 不符 → 退回新会话（同并发轨命令，`-C` 指向原工作目录）。

- 并发轨（worktree 内起新会话，工作区状态就是上下文）：

```bash
codex exec -s workspace-write -C "$WT" -m gpt-5.5 -c 'model_reasoning_effort="<原档位>"' \
  --json "$(cat "$RUN/rework-brief.md")" </dev/null 2>"$RUN/stderr-rework-<N>.log" > "$RUN/rework-<N>.jsonl"
```

每轮返工后回到 Step 5。3 轮不过 → 标 `blocked`，停该任务，向用户汇报：尝试过什么、卡在哪、两条出路（人工介入 / Claude 直接修——后者突破角色分工，须用户点头）。

## Step 8：合并与提交（全局唯一串行点）

评审通过的任务逐个合并，**一次只合一个**（codex 永不碰 git）。单任务主工作区分支模式：在 `codex/$SLUG` 分支上提交（同第 2 条纪律）→ 切回原分支 `merge --ff-only` → 删任务分支，不涉及 worktree 步骤。worktree 模式走完整流程：

1. 把最新主分支合进任务分支并复验——保证"组合后"依然成立（integration 验证）：

```bash
git -C "$WT" merge <主分支>   # 简单冲突 Claude 直接解；语义冲突打回该任务（告知 base 已变）；拿不准 → 问用户
(cd "$WT" && <项目 lint/test 命令>)
```

2. 在任务分支上提交：只 `git add` 本任务相关文件，永不 `git add -A`；项目有结构自检脚本的，add 后跑一遍；提交信息遵循项目惯例。
3. 回主分支合并并清理：

```bash
git -C "$REPO_ROOT" merge --ff-only "codex/$SLUG" || git -C "$REPO_ROOT" merge --no-ff "codex/$SLUG"
git -C "$REPO_ROOT" worktree remove "$WT" && git -C "$REPO_ROOT" branch -d "codex/$SLUG"
```

4. 更新 `state.json` 为 `merged`；依赖此产出的后续任务此刻才可派发。

全部收口后统一汇报：每任务档位与返工轮次、改动文件与测试结果、commit hash、token 用量（exec 轨汇总 events.jsonl 的 `turn.completed`，omega 轨用其 usage 统计）、failed/blocked 原因与建议、任务清单状态更新建议。

## 恢复协议

会话中断后再进入：扫 `$REPO_ROOT/.runtime/codex-dev/*/state.json` 按 phase 续跑（`dispatched` 且 events 无 `turn.completed` → 查 codex 进程是否还在；`rework-N` → 重新验收；`accepted` → 进合并）。omega 轨读 `.runtime/codex-dev/omega-run.json` 拿 runId/dashboard，`"$OMEGA" runs` 看是否在跑，`--resume <runId>` 续跑未完成部分（详见「后台运行与重连」）。worktree 与 thread_id 都在状态文件里，无需重派。
