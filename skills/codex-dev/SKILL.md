---
name: codex-dev
description: Full loop for delegating development tasks to the OpenAI Codex CLI. Claude plans the approach, writes the task brief, orchestrates (serial or concurrent via omegacode + physical worktree isolation), runs mechanical acceptance + review + merge; codex only writes code inside a workspace-write sandbox. Use when the user says "delegate"/"hand it to codex"/"have codex implement|build <task>"/"fan out several codex tasks", or runs /codex-dev. For review/consultation only (no code-writing) use gstack-codex instead, not this skill.
---

# /codex-dev — delegate-to-codex development loop

Division of labor: Claude plans, writes the task brief, orchestrates, runs acceptance + review + merge; codex only implements. The flow advances on its own and only stops to ask the user when BLOCKED, when a merge conflict needs a ruling, or when something would cross the role boundary. Report a one-line progress update on every task state change. **After dispatching, print the task's tracking address to the user**: the concurrent track gives the omega dashboard URL; the serial track gives the `tail -f` path to its `events.jsonl`.

Two tracks, sharing one set of brief / acceptance / review / merge discipline:

| Track | When | Tool |
|---|---|---|
| A — serial | single task, or tasks with dependencies | `codex exec` + `resume <thread_id>` (rework keeps session context) |
| B — concurrent | ≥2 mutually independent tasks | `omegacode` workflow (deterministic orchestration + watchdog + journal + live dashboard) + Claude-prebuilt worktrees |

## Step 0: Preflight checks

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
command -v codex >/dev/null && codex --version || echo "CODEX_NOT_FOUND"
command -v python3 >/dev/null || echo "PYTHON3_NOT_FOUND"
[ -f "${CODEX_HOME:-$HOME/.codex}/auth.json" ] || [ -n "$CODEX_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || echo "AUTH_MISSING"
OMEGA=$(command -v omegacode || echo "")
git -C "$REPO_ROOT" status --porcelain | head -5
mkdir -p "$REPO_ROOT/.runtime/codex-dev"
```

- `CODEX_NOT_FOUND` → stop: `npm install -g @openai/codex`. `AUTH_MISSING` → stop: `codex login`. `PYTHON3_NOT_FOUND` → stop: install python3 (used by the concurrent track for dispatch and args/state persistence).
- codex 0.120.0–0.120.2 has a stdin-deadlock bug → warn to upgrade, don't block.
- `$OMEGA` empty and this run needs the concurrent track → **do NOT auto-install** (env-level change + network); show the standard global-install command for the user to confirm: `npm install -g omegacode` (installs into the user's npm global prefix; if that dir needs permissions, suggest sudo, or `npm config set prefix <writable-dir>` and add its `bin` to PATH), install only after consent then run `omegacode doctor` to confirm the codex worker is OK; if declined, fall back to the serial track one task at a time.
- **Sandbox iron rule**: the user's global `~/.codex/config.toml` may be `sandbox_mode = "danger-full-access"` (desktop config). Dispatch commands MUST pass `-s workspace-write` explicitly (omegacode side: `defaultSandbox: "workspace-write"`), never relying on the global default; a missing flag is an incident — abort immediately and re-dispatch.
- `.runtime/`, `.omegacode/`, `.claude/worktrees/` should be in the project's `.gitignore`; if not, add them before starting.

## Step 1: Task decomposition & tiers (first anti-collision gate)

Concurrency collisions are prevented at dispatch-time orchestration, not patched up afterward:

1. **Independence check**: for each candidate task, estimate the set of files/modules it will touch (from the project's spec docs and existing code structure). If any two tasks' file sets intersect, or there's an import dependency / interface coupling → not concurrent; make them serial or merge into one task.
2. **Dependency ordering**: B depends on A's output → dispatch B only after A is merged back to the main branch.
3. **Concurrency cap 3**: codex tasks consume API quota + local test resources; queue beyond that.
4. **Model & reasoning-effort tiers** (pass explicitly, don't rely on global defaults; honor the user's request when named):

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

**Single task and clean working tree** → create the task branch in the main working tree directly (saves worktree + env-rebuild overhead):

```bash
git -C "$REPO_ROOT" checkout -b "codex/$SLUG"   # the main working tree belongs to this task during dispatch
```

**Concurrent tasks, or a dirty working tree (unrelated changes)** → one worktree per task, physical isolation. Concurrency in the same working tree inevitably collides: git status can't be attributed, test caches conflict, and on rework codex will "helpfully fix" others' changes it sees. Conventions are unreliable; isolation is reliable:

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

## Step 4A: Serial track (codex exec)

```bash
RUN="$REPO_ROOT/.runtime/codex-dev/$SLUG"; WORK=${WT:-$REPO_ROOT}
codex exec -s workspace-write \
  -C "$WORK" \
  -m gpt-5.5 -c 'model_reasoning_effort="<tier>"' \
  --json -o "$RUN/report.md" \
  "$(cat "$RUN/brief.md")" \
  </dev/null 2>"$RUN/stderr.log" > "$RUN/events.jsonl"
```

After dispatching, print the tracking address to the user: `tail -f "$RUN/events.jsonl"` (event stream, updates incrementally).

Execution minefield (violate and it crashes):

- **stdin must be `</dev/null`**: codex always reads stdin; not closing it blocks forever (symptom: zero output, zero CPU, looks hung). **Pipe trap**: in `echo "..." | codex ... </dev/null`, the `</dev/null` overrides the pipe and codex gets empty input — always pass the prompt as a positional arg, never via a pipe.
- Thinking tokens go to stderr, persisted to `$RUN/stderr.log` (don't drop to /dev/null — needed for debugging; in the final report only summarize key errors, don't forward the content verbatim).
- codex has **no intermediate output**: if the process is killed early, `report.md` is empty with no error. Empty file = timeout/killed, not "nothing changed".
- Run via Bash `run_in_background`; timeout by tier: medium 300s / high 600s / xhigh 1200s. Split tasks expected to exceed 15 min.
- When `-C` points at the repo root (or worktree root) the whole dir is writable — the directory-level allowlist is backstopped by the Step 5 out-of-scope check. `workspace-write` is usually offline by default, but **don't treat "no network" as a technical guarantee** (config can override) — the network ban is enforced by the brief's behavioral constraint.

Right after dispatch, write `$RUN/state.json` (for crash recovery):

```json
{"slug":"...","phase":"dispatched|accepted|rework-N|merged|failed|blocked",
 "track":"exec|omega","thread_id":"...","worktree":"...","branch":"...","tier":"high"}
```

On completion, grab the session id and usage (required for rework; **never `resume --last`** — it points wrong under concurrency or multiple sessions):

```bash
THREAD_ID=$(head -1 "$RUN/events.jsonl" | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4)
grep '"type":"turn.completed"' "$RUN/events.jsonl" | tail -1
```

Failure isolation: non-zero exit or empty events → first read `$RUN/stderr.log` to localize (auth, rate-limit, version bug); fix and rerun once if fixable; two consecutive failures → mark `failed`, don't drag down other tasks, report at the summary.

## Step 4B: Concurrent track (omegacode)

Prerequisite: each task's worktree and env are ready per Step 3. **First pick a name `BATCH` for this batch** (lowercase kebab-case, e.g. `oauth-migration`) — the workflow, log, state, and args all use it as prefix; **set it once and reuse the same variable throughout so names can't drift apart**. Write the workflow below to `$RUN_DIR/$BATCH-fanout.workflow.js` (omega shows the run on the dashboard by filename, so you can tell which batch at a glance; the `-fanout.workflow.js` suffix is fixed, marking it the orchestration script):

```js
export const meta = {
  name: "codex-dev-fanout",
  description: "Concurrent dispatch: one codex agent per task, implementing inside its prebuilt worktree",
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

Invoke (`tasks[].brief` carries the full brief text). **Launch detached in the background and persist the reconnect truth** — omega is an nohup-detached process; closing this session/terminal leaves it running (upside: doesn't occupy the session), but exactly for that reason record the runId / dashboard / pid at launch so you can find it again if disconnected (see "Background runs & reconnect" below):

```bash
RUN_DIR="$REPO_ROOT/.runtime/codex-dev"; mkdir -p "$RUN_DIR"
BATCH=<batch-name>                               # lowercase kebab-case; the only variable used throughout, so names can't drift
WF="$RUN_DIR/$BATCH-fanout.workflow.js"          # the workflow above MUST be written to this file
LOG="$RUN_DIR/$BATCH.log"; RUNJSON="$RUN_DIR/$BATCH-run.json"; ARGSFILE="$RUN_DIR/$BATCH-args.json"

python3 -c 'import json;print(json.dumps({"tasks":[...]}))' > "$ARGSFILE"     # persist args; reused verbatim on resume
[ -s "$ARGSFILE" ] || { echo "ARGS generation failed, stop"; exit 1; }

nohup "$OMEGA" run "$WF" --args-file "$ARGSFILE" >"$LOG" 2>&1 &     # use --args-file (so resume can replay the original args); **don't add --json** (it suppresses the view: line)
OMEGA_PID=$!

for _ in $(seq 1 20); do          # omega writes the view URL to the log at startup; parse this run's address (with the real port) from it
  VIEW=$(grep -oE 'http://127\.0\.0\.1:[0-9]+/#/run/wf_[0-9a-f]+' "$LOG" | head -1)
  [ -n "$VIEW" ] && break; sleep 0.5
done
[ -n "$VIEW" ] || { echo "omega didn't come up (no view: line within 10s), check $LOG:"; tail -20 "$LOG"; exit 1; }   # hard stop, don't write an empty record

python3 - "$VIEW" "$OMEGA_PID" "$WF" "$LOG" "$ARGSFILE" "$RUNJSON" <<'PY'   # build JSON safely with python (won't break on special chars in paths)
import json,sys
v,pid,wf,log,af,out=sys.argv[1:7]
json.dump({"runId":v.rsplit("/",1)[-1],"pid":int(pid),"dashboard":v,"workflow":wf,"log":log,"argsFile":af}, open(out,"w"))
PY
echo "▶ omega dashboard: $VIEW"   # after dispatch, print this address to the user
```

- **Print the dashboard address (`$VIEW`) to the user** — a read-only web board to watch each codex's phase / progress / token use live; it's the full per-run URL (with `/#/run/<runId>`), so it stays unambiguous across multiple dispatches.
- Key design: **don't use omegacode's `worktree:` option** (when it builds its own worktree, Claude can't inject the env-setup step); use `cwd:` pointing at the prebuilt worktree — omegacode does pure deterministic orchestration (concurrency scheduling, 30-min no-progress watchdog, journal, token stats), and the worktree lifecycle belongs to Claude.
- It drives codex over `codex app-server` JSON-RPC; the serial track's stdin/timeout minefield doesn't apply.
- The runId is written by omega into the `view:` line of the log at startup (parsed and persisted above, with the real port); on completion read the structured result from the log or `~/.omegacode/runs/<runId>/`.
- A single failed agent shows as null/failed in the results array — rework only that task, the rest are unaffected.
- Extras (only when the user asks): hard tasks can run the built-in `bake-off` (codex and claude-code each implement in isolated worktrees, blind-judged for a winner) or `multi-provider-review` (two models review independently, then synthesize).

### Background runs & reconnect

After launch omega is a detached process; closing the session/terminal leaves it running. This is the concurrent track's core strength (doesn't occupy the session), but it requires **persisting the truth to disk and never depending on some watcher process staying alive** — otherwise once the session dies you're left with an orphan run, no notification, and a hunt to find it next time.

- **Source of truth** (survives session death): `$RUN_DIR/<BATCH>-run.json` (runId / dashboard / pid / workflow / argsFile, **per-batch, never overwriting each other**) + omega's own `~/.omegacode/runs/<runId>/` journal.
- **A watcher is an optional live notifier**: while online you can spin up a background poller of `"$OMEGA" runs` and notify the user on completion; but it's a nice-to-have, **not the source of truth** — if it dies, reconnect still works.
- **Reconnect from any new session** (even if the original terminal is closed):

  ```bash
  OMEGA=$(command -v omegacode) || { echo "omegacode not on PATH → first npm install -g omegacode"; exit 1; }   # stop if not found, don't run on with an empty command
  RUN_DIR="$(git rev-parse --show-toplevel)/.runtime/codex-dev"
  ls "$RUN_DIR"/*-run.json                         # list each batch's record, pick the one to recover
  RUNJSON="$RUN_DIR/<BATCH>-run.json"
  J() { python3 -c "import json,sys;print(json.load(open('$RUNJSON'))[sys.argv[1]])" "$1"; }   # read fields safely (handles spaces/special chars)
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

2. **lint + test**: run the project commands in `$WORK`; keep failing output verbatim as rework material.
3. codex's completion report (report.md / structured REPORT) is only a lead, **not a conclusion**.

## Step 6: Review (Claude does it personally; must not delegate back to codex)

Go through `git -C "$WORK" diff` + new files item by item:

- Project review checklist (distilled from the project's CLAUDE.md, e.g. this repo's three: "matching rules each map through / agentio time-gate no leak / journal insert-only").
- Project red-line scan (e.g. automation paths forbid `dry_run=false`); no silent fallback / swallowed exceptions / fabricated defaults.
- Quality thresholds (e.g. AGENTS.md's file/function line limits, no generic-name modules).
- Check the implementation and tests against each acceptance criterion in the brief; missing tests = not done.

Independent judgment: verify key assertions in the code; don't take codex's self-report at face value.

## Step 7: Rework (≤3 rounds per task)

Write review notes to `$RUN/rework-brief.md`: one per line "issue, location file:line, expected behavior, cited spec item"; if the reviewer touched the working tree (e.g. restored out-of-scope files), state it clearly. **Review notes always go through a positional arg** — in `echo "..." | codex ... </dev/null` the `</dev/null` overrides the pipe and codex gets empty input.

- Serial track (resume keeps the original session context; the resume subcommand has no `-s`/`-C` flag — don't gamble on inherited sandbox behavior, pin it explicitly with `-c`):

```bash
codex exec resume "$THREAD_ID" -c 'sandbox_mode="workspace-write"' --json \
  "$(cat "$RUN/rework-brief.md")" </dev/null 2>"$RUN/stderr-rework-<N>.log" > "$RUN/rework-<N>.jsonl"
```

resume can't find the session or cwd mismatch → fall back to a new session (same as the concurrent-track command, `-C` pointing at the original working dir).

- Concurrent track (start a new session inside the worktree; the working-tree state is the context):

```bash
codex exec -s workspace-write -C "$WT" -m gpt-5.5 -c 'model_reasoning_effort="<original-tier>"' \
  --json "$(cat "$RUN/rework-brief.md")" </dev/null 2>"$RUN/stderr-rework-<N>.log" > "$RUN/rework-<N>.jsonl"
```

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

After everything is wrapped up, report together: each task's tier and rework rounds, changed files and test results, commit hashes, token usage (serial track: sum events.jsonl's `turn.completed`; omega track: use its usage stats), failed/blocked reasons and suggestions, task-list status update suggestions.

## Recovery protocol

Re-entering after a session interruption: scan `$REPO_ROOT/.runtime/codex-dev/*/state.json` and continue by phase (`dispatched` with no `turn.completed` in events → check whether the codex process is still alive; `rework-N` → re-run acceptance; `accepted` → go to merge). For the omega track, read `.runtime/codex-dev/<BATCH>-run.json` for runId/dashboard/argsFile, `"$OMEGA" runs` to see if it's still running, `run <workflow> --args-file <argsFile> --resume <runId>` to continue the unfinished part (resume must replay the original args, or precondition mismatch; see "Background runs & reconnect"). Worktrees and thread_ids are all in the state files, no re-dispatch needed.
