---
name: codex-dev
description: Full loop for delegating development tasks to the OpenAI Codex CLI. Claude plans the approach, writes the task brief, orchestrates, runs mechanical acceptance + review + merge; codex only writes code inside a workspace-write sandbox. Every codex task runs as an omegacode agent (one task = a 1-agent run, several = multi-agent: parallel if independent, ordered if dependent), so every dispatch gets a live dashboard, a completion notification, and disk-persisted reconnect. Use when the user says "delegate"/"hand it to codex"/"have codex implement|build <task>"/"fan out several codex tasks", or runs /codex-dev. For review/consultation only (no code-writing) use gstack-codex instead, not this skill.
---

# /codex-dev — delegate-to-codex development loop

Division of labor: Claude plans, writes the task brief, orchestrates, runs acceptance + review + merge; codex only implements. The flow advances on its own and only stops to ask the user when BLOCKED, when a merge conflict needs a ruling, or when something would cross the role boundary. Report a one-line progress update on every task state change.

**One engine: every codex task runs as an `omegacode` agent.** There is no "serial vs concurrent" split — *N tasks are N agents*. How many, and whether they run in parallel or in sequence, is an orchestration decision you make in Step 1, not a separate tool:

- **One task** → a 1-agent run.
- **Several independent tasks** → one run, agents in `parallel()`.
- **Dependent tasks** → separate runs in dependency order (dispatch B after A merges).

Because everything goes through omega, **every dispatch — even a single hours-long task — gets a live web dashboard, a completion notification (the run is a Bash `run_in_background` job, so the harness wakes you when it exits), and disk-persisted reconnect.** **Right after dispatching, always print the run's dashboard address to the user** — a long task with no visible progress is a black box; never leave the user blind.

## Step 0: Preflight checks

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
command -v codex >/dev/null && codex --version || echo "CODEX_NOT_FOUND"
OMEGA=$(command -v omegacode) || echo "OMEGA_NOT_FOUND"
command -v python3 >/dev/null || echo "PYTHON3_NOT_FOUND"
[ -f "${CODEX_HOME:-$HOME/.codex}/auth.json" ] || [ -n "$CODEX_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || echo "AUTH_MISSING"
git -C "$REPO_ROOT" status --porcelain | head -5
mkdir -p "$REPO_ROOT/.runtime/codex-dev"
```

- `CODEX_NOT_FOUND` → stop: `npm install -g @openai/codex`. `AUTH_MISSING` → stop: `codex login`.
- `OMEGA_NOT_FOUND` → stop. omega is the execution engine — without it there is no dispatch. **Don't auto-install** (env-level change + network); show the standard global-install command for the user to confirm: `npm install -g omegacode` (installs into the user's npm global prefix; if that dir needs permissions, suggest sudo, or `npm config set prefix <writable-dir>` and add its `bin` to PATH). After consent, install and run `omegacode doctor` to confirm the codex worker is OK.
- `PYTHON3_NOT_FOUND` → stop: install python3 (used to build args and persist run state).
- codex 0.120.0–0.120.2 has a stdin-deadlock bug → warn to upgrade, don't block.
- **Sandbox iron rule**: the user's global `~/.codex/config.toml` may be `sandbox_mode = "danger-full-access"` (desktop config). The workflow MUST set `defaultSandbox: "workspace-write"` and never rely on the global default; a missing setting is an incident — abort and re-dispatch.
- `.runtime/`, `.omegacode/`, `.claude/worktrees/` should be in the project's `.gitignore`; if not, add them before starting.

## Step 1: Task decomposition & tiers (first anti-collision gate)

Collisions are prevented at dispatch-time orchestration, not patched up afterward:

1. **Independence check**: for each candidate task, estimate the set of files/modules it will touch (from the project's spec docs and existing code structure). Tasks whose file sets are disjoint and have no import/interface coupling may run in the **same run** as parallel agents; any overlap or coupling → split into **separate ordered runs**, or merge into one task.
2. **Dependency ordering**: B depends on A's output → dispatch B only after A is merged back to the main branch.
3. **Concurrency auto-scales to the machine**: each agent runs a full local build/test in its worktree + consumes codex API rate-limit budget — so unlike a fan-out of lightweight/read-only agents, the binding limit is this machine's build/test headroom and your codex plan's rate limits, not an agent-count ceiling. The dispatch derives `--concurrency` from the box (`cores − 2`, bounded by ~2 GB RAM per agent, capped 16; omega's own default is 100 — far too many heavy local agents). Override with `CODEX_DEV_CONCURRENCY=<N>` for a big box + high codex limits.
4. **Model & reasoning-effort tiers** (set per agent; honor the user's request when named):

| Tier | When | Params |
|---|---|---|
| chore | config edits, mechanical refactors, docs | `gpt-5.5` + `medium` |
| normal (default) | single-module features, bug fixes, adding tests | `gpt-5.5` + `high` |
| hard | cross-module design, money/accounting/matching core logic, concurrency & timing, performance | `gpt-5.5` + `xhigh` |

Claude decides the tier and notes it in the dispatch progress report (e.g. "T9 backfill pipeline → xhigh").

## Step 2: Write the task brief

Write the brief to `$REPO_ROOT/.runtime/codex-dev/<slug>/brief.md` (slug = task id or a short English kebab-case name). **First read the project's CLAUDE.md / AGENTS.md / relevant spec docs and distill the project's red lines and quality constraints into the "Hard constraints" section** — the brief must be self-contained; do not assume codex has read the conversation history.

Template (prose follows the project's language convention; code identifiers/paths in English):

```markdown
# Task: <one-line goal>

## Goals & acceptance criteria
- <mechanically verifiable acceptance points, one per line>

## Spec basis
- <project spec doc §section: quote the key text, not just the section number>
- <verbatim task-list item>

## Environment
- Working directory is <main repo / this repo's dedicated worktree>; build/test env is ready.
- No installing dependencies and no network operations (the sandbox is usually offline, but this is a behavioral red line, not a technical backstop); if a dependency is missing or network is genuinely needed, stop and explain it in the final report — do not work around it.

## Hard constraints
1. No git write operations whatsoever (commit/push/rebase/checkout/stash). Only edit working-tree files; version operations are done by the reviewer. Git writes may be blocked by the sandbox — that's expected, don't retry.
2. Write scope is limited to <project-defined implementer write-allowlist; if none, "within this repo" plus explicit no-go areas>; going out of scope = task failure.
3. <quality constraints and red lines distilled from the project's AGENTS.md/CLAUDE.md, one per line>
4. New logic must come with tests; run <project lint/test command> yourself and pass before considering it done.

## Completion report
The final message must list: changed-files list, added-tests list, lint/test results, open items and known limitations.
```

## Step 3: Execution environment (second anti-collision gate)

**Default to one branch per task; never develop directly on the main branch** (exception only if the user explicitly says "just change it on the current branch").

**Main working tree has uncommitted changes → classify before choosing the base**: if those changes ARE the baseline this task depends on (the user got halfway and wants codex to continue), opening a worktree off the main branch would make codex build on stale code and misalign the merge — you MUST stop and confirm with the user (commit first, or build the task branch on the current state as base); if the changes are unrelated to the task → then isolate off the main branch per the flow below.

**A single task with a clean working tree** → create the task branch in the main working tree directly; the agent's `cwd` is the repo root (saves worktree + env-rebuild overhead):

```bash
git -C "$REPO_ROOT" checkout -b "codex/$SLUG"   # the main working tree belongs to this task during dispatch
```

**Multiple tasks (parallel agents), or a dirty working tree (unrelated changes)** → one worktree per task, physical isolation; each agent's `cwd` is its own worktree. Several agents in one working tree inevitably collide: git status can't be attributed, test caches conflict, and on rework codex will "helpfully fix" others' changes it sees. Conventions are unreliable; isolation is reliable:

```bash
SLUG=<slug>
WT="$REPO_ROOT/.claude/worktrees/codex-$SLUG"
git -C "$REPO_ROOT" worktree add "$WT" -b "codex/$SLUG" <main-branch>
```

Then **rebuild the environment inside the worktree per the project's build method** (codex's sandbox is offline; the env must be pre-installed by Claude). Python caveat: if the project inside the main repo's venv is an editable install (site-packages has `__editable__*.pth`), its path is hard-coded to the main repo — the worktree **must build a fresh venv and reinstall**; sharing or copying makes tests run against the main-repo code:

```bash
python3 -m venv "$WT/<pkg>/.venv" && "$WT/<pkg>/.venv/bin/pip" install -q -e "$WT/<pkg>[dev]"
```

Finally run the project's lint/test once inside the worktree: **the baseline must be green** — dispatching on red makes failures unattributable; if the baseline is red → fix the main branch first, don't dispatch.

## Step 4: Dispatch via omega

One agent per task. A single task is just a one-element `tasks` array; independent tasks are multiple elements (omega runs them in `parallel`, capped at its concurrency). **Pick a name `BATCH` for this run** (lowercase kebab-case, e.g. `oauth-migration`) — the workflow, log, state, and args all use it as prefix; **set it once and reuse the same variable throughout so names can't drift apart**. Write the workflow to `$RUN_DIR/$BATCH-fanout.workflow.js` (omega shows the run on the dashboard by filename, so you can tell which one at a glance; the `-fanout.workflow.js` suffix is fixed, marking it the orchestration script):

```js
export const meta = {
  name: "codex-dev-fanout",
  description: "Dispatch one codex agent per task, implementing inside its prebuilt worktree (or the repo root for a single task)",
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

`tasks[].brief` carries the full brief text; `tasks[].worktree` is the task's cwd (its worktree, or the repo root for a single main-tree task). First set per-batch names and write the args:

```bash
RUN_DIR="$REPO_ROOT/.runtime/codex-dev"; mkdir -p "$RUN_DIR"
BATCH=<batch-name>                               # lowercase kebab-case; the only variable used throughout, so names can't drift
WF="$RUN_DIR/$BATCH-fanout.workflow.js"          # the workflow above MUST be written to this file
LOG="$RUN_DIR/$BATCH.log"; RUNJSON="$RUN_DIR/$BATCH-run.json"; ARGSFILE="$RUN_DIR/$BATCH-args.json"
# refuse if this BATCH is already in use — locally (run.json) OR as an omega run with the same filename (a prior dispatch may have registered before its run.json was written)
{ [ -e "$RUNJSON" ] || "$OMEGA" runs 2>/dev/null | awk -v f="$BATCH-fanout.workflow.js" '$NF==f{seen=1} END{exit seen?0:1}'; } && { echo "batch name '$BATCH' already in use — pick a unique BATCH"; exit 1; }
python3 -c 'import json;print(json.dumps({"tasks":[...]}))' > "$ARGSFILE"   # persist args; reused verbatim on resume
[ -s "$ARGSFILE" ] || { echo "ARGS generation failed, stop"; exit 1; }
# concurrency auto-scales to THIS machine: cores-2, bounded by ~2GB RAM/agent (each runs a full build/test), capped 16; override with CODEX_DEV_CONCURRENCY
read CORES MEMGB <<<"$(python3 - <<'PY'
import os
try: m = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") // (1024**3)
except Exception: m = 8
print(os.cpu_count() or 4, m)
PY
)"
CONC=$(( CORES>2 ? CORES-2 : 1 )); [ $((MEMGB/2)) -lt "$CONC" ] && CONC=$((MEMGB/2)); [ "$CONC" -lt 1 ] && CONC=1; [ "$CONC" -gt 16 ] && CONC=16
CONC=${CODEX_DEV_CONCURRENCY:-$CONC}; echo "concurrency for this run: $CONC"
```

**Dispatch this command as a Bash `run_in_background` job** (NOT `nohup`/detached): `omega run` blocks until the run finishes — omega has no executor daemon by design, the run lives in one process — so when it exits the harness fires a completion notification, which is your cue to go to Step 5. **Don't add `--json`** (it suppresses the `view:` line):

```bash
"$OMEGA" run "$WF" --args-file "$ARGSFILE" --concurrency "$CONC" > "$LOG" 2>&1
```

Right after (foreground; reads the log the background run is writing), capture the dashboard URL and persist the reconnect record:

```bash
# runId is authoritative from `omega runs` (matched by our unique filename); the dashboard URL is best-effort — only present if the viewer came up
RID=""; VIEW=""
for _ in $(seq 1 20); do
  [ -z "$VIEW" ] && VIEW=$(grep -oE 'http://127\.0\.0\.1:[0-9]+/#/run/wf_[0-9a-f]+' "$LOG" | head -1)
  RID=$("$OMEGA" runs 2>/dev/null | awk -v f="$BATCH-fanout.workflow.js" '$NF==f{print $1; exit}')
  [ -n "$RID" ] && break; sleep 0.5
done
# hard-fail ONLY if the run never registered; a missing viewer (no view: line) is NOT a failure — omega runs fine without one
[ -n "$RID" ] || { echo "omega run never registered, check $LOG:"; tail -20 "$LOG"; exit 1; }
python3 - "$RID" "$VIEW" "$WF" "$LOG" "$ARGSFILE" "$RUNJSON" <<'PY'   # build JSON safely with python
import json,sys
rid,v,wf,log,af,out=sys.argv[1:7]
json.dump({"runId":rid,"dashboard":v,"workflow":wf,"log":log,"argsFile":af}, open(out,"w"))
PY
# ALWAYS print a tracking address — dashboard if the viewer is up, else the log
[ -n "$VIEW" ] && echo "▶ omega dashboard: $VIEW" || echo "(viewer not up — no web dashboard for this run)"
echo "▶ track: tail -f $LOG    (status: \"$OMEGA\" runs)"
```

Also write a per-task state file for crash recovery, one per task in the batch — `$RUN_DIR/<slug>/state.json`:

```json
{"slug":"...","phase":"dispatched|accepted|rework-N|merged|failed|blocked",
 "batch":"<batch>","worktree":"...","branch":"...","tier":"high"}
```

- **Print the dashboard address (`$VIEW`) to the user** — a read-only web board to watch each codex's phase / progress / token use live; it's the full per-run URL (with `/#/run/<runId>`), so it stays unambiguous across multiple dispatches.
- Key design: **don't use omegacode's `worktree:` option** (when it builds its own worktree, Claude can't inject the env-setup step); use `cwd:` pointing at the prebuilt worktree — omegacode does pure deterministic orchestration (concurrency scheduling, 30-min no-progress watchdog, journal, token stats), and the worktree lifecycle belongs to Claude.
- It drives codex over `codex app-server` JSON-RPC (no stdin/timeout pitfalls of a raw `codex exec`).
- The runId comes from `omega runs` (matched by the unique filename — authoritative even if the viewer never started); the dashboard URL, when the viewer is up, is the `view:` line in the log. On completion read the structured result from the log or `${OMEGACODE_HOME:-~/.omegacode}/runs/<runId>/`.
- A single failed agent shows as null/failed in the results array — rework only that task, the rest are unaffected.
- Extras (only when the user asks): hard tasks can run the built-in `bake-off` (codex and claude-code each implement in isolated worktrees, blind-judged for a winner) or `multi-provider-review` (two models review independently, then synthesize).

### Completion & reconnect

**You get woken automatically.** Because the dispatch is a Bash `run_in_background` job and `omega run` blocks until the run finishes (omega has **no executor daemon** by design — a run lives and dies with its one process), the harness fires a completion notification when that process exits. That is your cue to proceed to Step 5 — no watcher or polling needed.

**A stuck task surfaces — it does not hang silently.** omega arms a 30-min no-progress watchdog per agent: a stalled turn is failed (`turn_stalled`), its result becomes `null`, the run settles, and `omega run` exits — so within ~30 min a stall becomes an ordinary completion notification carrying a failed task, which you **report by name** ("task X stalled") and then rework or mark `blocked`. The always-printed dashboard/log also lets the user watch a stall live. Residual edge: a wedged `codex app-server` that ignores both interrupt and SIGTERM could keep `omega run` from exiting — so **if the completion notification hasn't arrived well past the watchdog window (~45 min) and the dashboard shows no progress, stop waiting**: run `"$OMEGA" runs` + `tail` the log, report the stuck run to the user, and `"$OMEGA" runs --prune-stale` (or kill its pid) to clear it. Never wait indefinitely.

**If the session died before omega finished** (the background run dies with the session; omega's recovery model is "the run dir is the truth, `--resume` continues"), reconnect from a new session via the persisted record:

- **Source of truth**: `$RUN_DIR/<BATCH>-run.json` (runId / dashboard / workflow / argsFile, **per-batch, never overwriting each other**) + omega's own `${OMEGACODE_HOME:-~/.omegacode}/runs/<runId>/` journal.
- **Reconnect from any new session** (even if the original terminal is closed):

  ```bash
  OMEGA=$(command -v omegacode) || { echo "omegacode not on PATH → first npm install -g omegacode"; exit 1; }   # stop if not found, don't run on with an empty command
  RUN_DIR="$(git rev-parse --show-toplevel)/.runtime/codex-dev"
  ls "$RUN_DIR"/*-run.json                         # list each batch's record, pick the one to recover
  RUNJSON="$RUN_DIR/<BATCH>-run.json"
  J() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$RUNJSON" "$1"; }   # read fields safely (path passed as argv, not interpolated into source)
  echo "dashboard: $(J dashboard)"                 # print the address to the user
  "$OMEGA" runs                                    # still running? check status / agent count
  # resume (run auto-starts the board and re-prints the view: line); **must replay the original --args-file**, or args precondition mismatch:
  "$OMEGA" run "$(J workflow)" --args-file "$(J argsFile)" --resume "$(J runId)"
  # only want to watch, not resume: start the board in the background then open the dashboard URL above (a foreground serve blocks): "$OMEGA" serve >/dev/null 2>&1 &
  ```

- Cleanup when done: `"$OMEGA" runs --prune-stale` clears dead runs.

## Step 5: Mechanical acceptance (per task; any failure → Step 7 rework)

1. **Out-of-scope check** (the sandbox only isolates between worktrees, not within one; post-hoc verification is the hard gate):

```bash
git -C "$WORK" status --porcelain | cut -c4- | grep -vE '^(<project write-allowlist regex>)' || echo SCOPE_OK
```

Out-of-scope files: tracked → restore with `git -C "$WORK" checkout -- <file>`, untracked → delete, and name them in the rework notes.

2. **lint + test**: run the project commands in `$WORK` (the task's worktree, or repo root for a single main-tree task); keep failing output verbatim as rework material.
3. codex's completion report (the structured REPORT) is only a lead, **not a conclusion**.

## Step 6: Review (Claude does it personally; must not delegate back to codex)

Go through `git -C "$WORK" diff` + new files item by item:

- Project review checklist (distilled from the project's CLAUDE.md, e.g. this repo's three: "matching rules each map through / agentio time-gate no leak / journal insert-only").
- Project red-line scan (e.g. automation paths forbid `dry_run=false`); no silent fallback / swallowed exceptions / fabricated defaults.
- Quality thresholds (e.g. AGENTS.md's file/function line limits, no generic-name modules).
- Check the implementation and tests against each acceptance criterion in the brief; missing tests = not done.

Independent judgment: verify key assertions in the code; don't take codex's self-report at face value.

## Step 7: Rework (≤3 rounds per task)

Write review notes to `$RUN_DIR/<slug>/rework-<N>.md`: one per line "issue, location file:line, expected behavior, cited spec item"; if the reviewer touched the working tree (e.g. restored out-of-scope files), state it clearly.

Re-dispatch as a fresh **1-task omega run** (Step 4) whose single `tasks[].brief` is the rework notes and whose `cwd` is the task's worktree — the working-tree state is the context (codex sees its prior changes on disk). Use `BATCH=<slug>-rework-<N>` so it gets its own dashboard address, completion notification, and reconnect record, exactly like any other dispatch. The same effort tier as the original.

After each rework round return to Step 5. 3 rounds without passing → mark `blocked`, stop that task, report to the user: what was tried, where it's stuck, two ways out (human intervention / Claude fixes it directly — the latter crosses the role boundary and needs the user's nod).

## Step 8: Merge & commit (the single global serialization point)

Merge passed tasks one at a time, **only one at a time** (codex never touches git). Single-task main-working-tree branch mode: commit on the `codex/$SLUG` branch (same as discipline #2) → switch back to the original branch and `merge --ff-only` → delete the task branch, no worktree steps. Worktree mode runs the full flow:

1. Merge the latest main branch into the task branch and re-verify — ensure it still holds "after combining" (integration check):

```bash
git -C "$WT" merge <main-branch>   # simple conflicts: Claude resolves directly; semantic conflicts: rework that task (tell it the base moved); unsure → ask the user
(cd "$WT" && <project lint/test command>)
```

2. Commit on the task branch: only `git add` files for this task, never `git add -A`; if the project has a structure self-check script, run it after add; follow the project's commit-message convention.
3. Merge back to the main branch and clean up:

```bash
git -C "$REPO_ROOT" merge --ff-only "codex/$SLUG" || git -C "$REPO_ROOT" merge --no-ff "codex/$SLUG"
git -C "$REPO_ROOT" worktree remove "$WT" && git -C "$REPO_ROOT" branch -d "codex/$SLUG"
```

4. Update `state.json` to `merged`; downstream tasks depending on this output can only be dispatched now.

After everything is wrapped up, report together: each task's tier and rework rounds, changed files and test results, commit hashes, token usage (from each omega run's usage stats), failed/blocked reasons and suggestions, task-list status update suggestions.

## Recovery protocol

Re-entering after a session interruption: scan `$REPO_ROOT/.runtime/codex-dev/*/state.json` and continue by phase (`dispatched` → check whether the run is still going, below; `rework-N` → re-run acceptance; `accepted` → go to merge). For the run itself, read `.runtime/codex-dev/<BATCH>-run.json` for runId/dashboard/argsFile, `"$OMEGA" runs` to see if it's still running, and `run <workflow> --args-file <argsFile> --resume <runId>` to continue the unfinished part (resume must replay the original args, or precondition mismatch; see "Completion & reconnect"). Worktrees and the batch runId are all in the state/record files, no re-dispatch needed.
