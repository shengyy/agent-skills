# nohup 回退

主代理的工具不能后台运行命令并在退出时唤醒、后台任务的寿命覆盖不了整批施工，或主代理会话可能先结束时，走这条路径。codex 命令、启动要点、终态判定和续接规则都与 SKILL.md 相同，区别只在怎么起、怎么判活、怎么中止。

## 启动

用 nohup 起后台并立即返回，之后靠 pid 判活。不能在前台等：外层工具超时会按进程组 SIGKILL，`nohup` 挡不住。`exec` 不能省：有它 `$!` 才是 codex 本身；没有它 `$!` 是 bash 包装，杀掉包装会留下 codex 孤儿继续跑。

```bash
nohup bash -c 'exec codex exec -m gpt-6-astra -c model_reasoning_effort="medium" \
  --dangerously-bypass-approvals-and-sandbox -o LAST.md - < BRIEF_FILE' > RUN.log 2>&1 & echo "pid=$!"
```

续接同样包一层：

```bash
nohup bash -c 'exec codex exec resume <session-id> -m gpt-6-astra -c model_reasoning_effort="<effort>" \
  --dangerously-bypass-approvals-and-sandbox -o LAST2.md - < FIX_FILE' > RUN2.log 2>&1 & echo "pid=$!"
```

## 判活与中止

- 没有退出通知，用 `kill -0 <pid>` 判活，间隔按任务规模和档位定；每次等待都要短于外层工具的超时。
- 进程退出后按 SKILL.md 监控一节看 `LAST.md` 定终态；进程活着但日志长时间不动，再看日志判断是否卡死。
- 中止用 `kill <pid>`：有 `exec`，这个 pid 就是 codex 本身。
- 额度耗尽时到点前不必判活，到点后按 SKILL.md 续接一节续上，仍用这里的包法起。
