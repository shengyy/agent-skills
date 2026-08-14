---
name: codex-construction
description: 主代理出方案、Codex 裸调施工的轻量任务编排：分批派工、后台监控、分阶段验收、改-审循环。用户说「安排 codex 施工/干活/审」或调用 /codex-construction 时使用。
---

# codex-construction — 轻量派工编排

编排的价值在**分工、边界、验收**，不在过程管控。不替 codex 写码，不给实现细节；给合同、给自主权、验收结果。

## 分工

- **主代理**：出方案与施工合同、拆批、派工、监控、验收、终审。
- **Codex**：一批之内全自主——读合同、实现、跑门禁、分阶段 commit、写验收包。
- 互不越界：主代理不中途接管施工，codex 不做产品级裁决。

codex 独干的系统性偏差是**过度工程**，所以主代理只在三处介入：合同定稿时杀复杂度、验收时拒收合同外机制、BLOCKED 快裁快回。

## 启动

```bash
nohup bash -c 'codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" \
  -s danger-full-access "$(cat PROMPT_FILE)"' > RUN.log 2>&1 & echo "pid=$!"
```

- effort：常规施工、定点修复、收口核验用 `high`；架构重构、资金/并发核心、全面对抗审用 `xhigh`。
- 模型名以本机 `~/.codex/config.toml` 为准；换名先用 `codex exec -m <名字> "打印 ok"` 探针验证，400 即无效。
- `danger-full-access` 无沙箱兜底，边界全靠 prompt 写明。
- prompt 先写文件再 `cat`，避免引号地狱。
- **启动调用必须秒回**：同一次 Bash 里不得再带耗时前台命令——外层超时按进程组 SIGKILL，`nohup` 挡不住。
- 运行中的日志不要 truncate。

## 监控：先等进程，再读日志

`echo $!` 拿到的 pid 就是 codex 本身。**进程还在就是在跑，不解析日志**；进程消失后才判终态：

| 终态 | 判定 | 处置 |
|---|---|---|
| 完成 | 有 `tokens used` 收尾块 + 尾部 `STAGE N DONE` | 进验收 |
| 主动阻断 | 有 `tokens used` + 尾部 `BLOCKED[批N]:` | 裁决后 resume |
| 无交付 | 有 `tokens used`，两个标记都没有 | 读尾部定性，resume 收口或重派 |
| 崩溃 | 无 `tokens used`，日志停在半途 | 多为外层组杀，重跑或 resume |

- `tokens used` 只代表**会话结束**，不代表完成——BLOCKED 也打印它。
- **别直接 grep 标记**：codex 开跑会回显 prompt 原文，合同里的标记字样会在日志开头命中。用 `grep -n -x "tokens used" | tail -1` 定位收尾行，只解析其后的输出。
- 进程活着 + 日志静默 20 分钟 = 卡死告警，不是「停在阶段边界等裁决」——`codex exec` 是单轮进程，BLOCKED 后必然退出。

## Prompt 五要素

1. **现场**：仓库路径、分支、前序进度。
2. **合同**：指向方案文档路径让 codex 自己通读，不塞正文。
3. **范围**：本批做什么、明确不做什么。
4. **红线**：只写真红线，用具体动作边界表述（push / 部署 / 生产库），不写抽象绝对句，不写实现细节。
5. **交付**：分阶段 commit + 验收包；完成时末尾单独一行打印 `STAGE N DONE` + commit hash，需裁决时打印 `BLOCKED[批N]: <原因>` 停在阶段边界。标记必须带批次 token，否则与 prompt 回显撞车。

**自主权条款（必写）**：施工中发现的真实问题，允许 codex 在范围内自行根因修复并记入验收包；只有推翻合同前提或触碰红线才 BLOCKED。

验收包骨架：目标 / diff 摘要 / 物理删除项 / 测试状态（含预期 RED）/ 未验证项。

## 批次

- 同一工作树**串行**；并行只允许各自独立 worktree 且文件集不相交。
- 一批 = 一个可独立验收的工作包，验收后才放行下一批。
- 大工程默认三段：骨架（含 RED 测试）→ 重改动 → 机械收尾。
- codex 施工中不要并行跑门禁、切分支或改同树文件。

## 改-审循环

审查用**全新会话**保独立性，可换模型或换 agent 交叉审。修复轮才续上下文：

```bash
codex exec resume --last -m <model> \
  -c model_reasoning_effort="<high|xhigh>" -c sandbox_mode="danger-full-access" "<prompt>"
```

- **effort 必须重传**：resume 不继承，漏传会静默掉回 config 默认档。（resume 不收 `-s` 别名，权限改用 `-c`，不是降级进沙箱。）
- 续接一律用裸 CLI，不要改用 `/codex:*`——插件看不见裸调起的会话。
- `--last` 按 cwd 取最近一条；多会话并存时改用日志头部的 `session id:`。
- 默认**单路**：首轮无阻断即收口；有阻断则修复后换新会话复审，一轮干净即可。触及不可逆资产或反复冒新阻断，才用 until-dry（连续两轮无新发现）。
- **主代理必须抽验**：自己重跑关键门禁，不信日志里的 "passed"。
- **熔断**：阻断性修复超 3 轮不收敛，或出现修 A 破 B 的振荡，立即停——那是方案错了，回方案层重裁，不是加轮次。
