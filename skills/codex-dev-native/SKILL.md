---
name: codex-dev-native
description: Full loop for delegating development tasks to the OpenAI Codex CLI on the official Codex plugin's native codex-companion engine. Claude orchestrates (decompose, isolate, dispatch, accept, review, merge); codex only implements under a workspace-write sandbox where writes are confined to its cwd and network is on. The native engine owns launch / background / status / result / cancel / same-thread resume, so Claude never hand-rolls dispatch or reconnect. Use when the user says "delegate" / "hand it to codex" / "have codex implement|build <task>" / "fan out several codex tasks", or runs /codex-dev-native. This is the native-engine sibling of codex-dev (which runs on the omegacode engine) — prefer this one when the official codex plugin (codex@openai-codex) is installed. For review/consultation only use gstack-codex; for a bare one-off rescue with no acceptance/merge loop, the plugin's /codex:rescue is enough.
---

# /codex-dev-native — delegate-to-codex development loop (native engine)

**Engine = the official Codex plugin's `codex-companion` runtime** (plugin `codex@openai-codex`). Claude does NOT hand-roll dispatch, background jobs, reconnect, or crash recovery — the native per-repo job registry owns all of that. Claude's job is the orchestration + governance shell around it: decompose, isolate, dispatch, accept, **review personally**, rework, merge. The flow advances on its own and only stops to ask the user when BLOCKED, when a merge conflict needs a ruling, or when something would cross the role boundary. Report a one-line progress update on every task state change.

**Restrictions follow exactly what the native engine enforces, plus brief red-lines for the rest.** codex runs under **workspace-write** — the only sandbox codex-companion gives a write task: the OS confines writes to its cwd and blocks escape, and network is on so codex can fetch docs / install project deps (this is what removes the offline pain). Anything the sandbox does NOT cover — no git writes, the write-scope allowlist *within* the cwd, no global installs — is enforced through the brief's hard constraints + post-hoc verification. **Never pass `danger-full-access`.**

## Native vs Claude — never rebuild the native side

| Concern | Owner |
|---|---|
| launch codex, background exec, running/stuck/done state, fetch result, cancel, resume-same-thread | **native** `codex-companion` — `task` / `status` / `result` / `cancel` / `task --resume-last` |
| reconnect & crash recovery | **native** — the per-repo job registry persists across turns/sessions; a new session just runs `status` / `result` |
| decompose & tiers, concurrency decision, worktree isolation, mechanical acceptance, **personal review**, rework loop, merge | **Claude** |

## Step 0: Engine resolution & preflight

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
CC=$(ls -td "$HOME"/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | head -1)
[ -n "$CC" ] || { echo "CODEX_PLUGIN_NOT_FOUND"; exit 1; }   # install: claude plugin install codex@openai-codex --scope user
( cd "$REPO_ROOT" && node "$CC" setup --json )               # verifies codex CLI present + authenticated
command -v git >/dev/null || echo "GIT_NOT_FOUND"
git -C "$REPO_ROOT" status --porcelain | head -5
mkdir -p "$REPO_ROOT/.runtime/codex-dev"
```

- `CODEX_PLUGIN_NOT_FOUND` → stop; install the plugin first (`claude plugin install codex@openai-codex --scope user`).
- `setup --json` reports codex readiness; if it says unauthenticated → stop and have the user run `codex login`.
- **Sandbox/network config (one-time per machine):** codex-companion forces `workspace-write` for write tasks, which is offline by default. To let codex fetch docs / install deps, `~/.codex/config.toml` needs network enabled under workspace-write:
  ```toml
  [sandbox_workspace_write]
  network_access = true
  ```
  This only takes effect when workspace-write is the active sandbox, so it does not change the user's interactive codex behavior. If it is missing, add it before dispatching.
- `.runtime/` and `.claude/worktrees/` should be in the project's `.gitignore`; add them if not.

## Step 1: Task decomposition & tiers (orchestration — Claude's, first anti-collision gate)

1. **Independence check**: estimate the files/modules each candidate task will touch. Disjoint file sets with no import/interface coupling → may run as **parallel background jobs**; any overlap or coupling → split into **separate ordered dispatches**, or merge into one task.
2. **Dependency ordering**: B depends on A's output → dispatch B only after A is merged back to the main branch.
3. **Concurrency**: Claude fires at most ~8 `task --background` jobs at once; the rest queue (Claude holds them and dispatches as slots free). Each is a real codex agent on API rate-limit budget.
4. **Tiers** — set `--effort` per task (the model stays the config default unless the user names one; pass `--model` only when they do):

| Tier | When | `--effort` |
|---|---|---|
| chore | config edits, mechanical refactors, docs | `low` |
| normal (default) | single-module features, bug fixes, adding tests | `high` |
| hard | cross-module design, money/accounting/matching core, concurrency & timing, performance | `xhigh` |

Claude decides the tier and notes it in the dispatch progress report (e.g. "T9 backfill pipeline → xhigh").

## Step 2: Write the task brief (red-lines become hard constraints)

Write the brief to `$REPO_ROOT/.runtime/codex-dev/<slug>/brief.md` (slug = task id or a short English kebab-case name). **First read the project's CLAUDE.md / AGENTS.md / relevant spec docs and distill the project's red lines and quality constraints into the "Hard constraints" section** — the brief must be self-contained. Shape the prompt with the official **`codex:gpt-5-4-prompting`** guidance (XML-tagged task / output contract / verification loop / grounding rules).

Because the sandbox only confines writes to the cwd, the brief carries everything else:

```markdown
# Task: <one-line goal>

## Goals & acceptance criteria
- <mechanically verifiable acceptance points, one per line>

## Spec basis
- <project spec doc §section: quote the key text, not just the number>
- <verbatim task-list item>

## Environment
- cwd is <the main repo on branch codex/<slug> | this task's dedicated worktree>; build/test env is ready.
- Network IS available — you may fetch docs or install project dependencies INTO this workspace. Do not install global tools, and do not touch anything outside the cwd.

## Hard constraints
1. No git operations whatsoever (commit/push/rebase/checkout/stash) — the reviewer owns all version control. (Git may also fail under the sandbox in a worktree; that is expected, do not retry.)
2. Write scope is limited to <project implementer write-allowlist; else "within this repo" plus explicit no-go areas>; out-of-scope edits = task failure.
3. <quality constraints and red lines distilled from the project's AGENTS.md/CLAUDE.md, one per line>
4. New logic must come with tests; run <project lint/test command> yourself and pass before considering it done.

## Completion report
List: changed files, added tests, lint/test results, open items and known limitations.
```

## Step 3: Execution environment (isolation — Claude's, second anti-collision gate)

**Single clean task (the common case)** → create the task branch in the main working tree; codex's cwd is the repo root. The real environment is already present, codex can read the whole repo, and network covers any missing deps — this sidesteps worktree env-fragility entirely:

```bash
SLUG=<slug>
git -C "$REPO_ROOT" checkout -b "codex/$SLUG"
WORK="$REPO_ROOT"
```

**Parallel batch, or a dirty tree with unrelated changes** → one worktree per task (physical write isolation; concurrent codex agents in one tree collide on files, caches, and git status); each agent's cwd is its own worktree:

```bash
WT="$REPO_ROOT/.claude/worktrees/codex-$SLUG"
git -C "$REPO_ROOT" worktree add "$WT" -b "codex/$SLUG" <main-branch>
WORK="$WT"
```

With network on, codex can build its own environment inside the worktree; or Claude pre-builds it if the project needs a specific setup. Editable-install caveat: a worktree that shares the main repo's editable venv runs tests against main-repo code — build a fresh venv in the worktree. Then run the project lint/test once inside `$WORK`: **the baseline must be green** before dispatch, or failures are unattributable.

**Dirty main tree that IS the task's baseline** (the user got halfway and wants codex to continue) → do NOT isolate off the main branch; stop and confirm with the user (commit first, or build on the current state as base).

**Default to one branch per task; never develop directly on the main branch** (exception only if the user explicitly says so).

## Step 4: Dispatch (native — no plumbing)

**Single short task** — foreground; the command prints codex's output directly and returns when done:

```bash
( cd "$WORK" && node "$CC" task --write --effort <tier> "$(cat "$REPO_ROOT/.runtime/codex-dev/$SLUG/brief.md")" )
```

**Long task, or any parallel batch** — background; returns a jobId immediately:

```bash
( cd "$WORK" && node "$CC" task --background --write --effort <tier> "$(cat "$REPO_ROOT/.runtime/codex-dev/$SLUG/brief.md")" )
# -> "Codex Task started in the background as <jobId>. Check /codex:status <jobId> for progress."
```

Track jobs — **this IS the reconnect/recovery layer**; the registry is per-repo and persists across turns and sessions, so there is no run.json/state.json to maintain:

```bash
( cd "$WORK" && node "$CC" status )            # all jobs for this workspace (id / kind / status / phase / elapsed)
( cd "$WORK" && node "$CC" status <jobId> )    # one job in full
( cd "$WORK" && node "$CC" result <jobId> )    # final output once completed
( cd "$WORK" && node "$CC" cancel <jobId> )    # kill a running job
```

- **Parallel batch**: fire one background `task` per task from its worktree cwd; keep each `{slug, worktree, jobId}`; then poll each worktree's `status` until done and pull `result`. Background jobs are independent detached workers — they run concurrently.
- **Stuck watchdog (Claude-driven):** while polling, if a job stays `running` well past a sane ceiling (~30 min) with no phase change, `cancel <jobId>`, mark the task blocked, and report it by name. Never wait indefinitely.
- A failed/blocked job is reported by name and reworked; sibling tasks are unaffected.
- The structured completion report from codex is a lead, **not a conclusion** — acceptance re-derives everything from the diff.

## Step 5: Mechanical acceptance (per task; any failure → Step 7 rework)

1. **Out-of-scope check** (workspace-write confines writes to the cwd, but scope *within* the cwd is on us):

```bash
git -C "$WORK" status --porcelain | cut -c4- | grep -vE '^(<project write-allowlist regex>)' || echo SCOPE_OK
```

Out-of-scope files: tracked → `git -C "$WORK" checkout -- <file>`, untracked → delete; name them in the rework notes. Also confirm codex made **no commits** (the no-git red line).

2. **lint + test** in `$WORK`; keep failing output verbatim as rework material.

## Step 6: Review (Claude does it personally — RED LINE: never delegate back to codex)

This is exactly why we wrap the native engine instead of just calling `/codex:review`. Go through `git -C "$WORK" diff` + new files item by item:

- Project review checklist (distilled from the project's CLAUDE.md — e.g. one repo's three: "matching rules each map through / agentio time-gate no leak / journal insert-only").
- Project red-line scan (e.g. automation paths forbid `dry_run=false`); no silent fallback / swallowed exceptions / fabricated defaults.
- Quality thresholds (e.g. AGENTS.md file/function line limits, no generic-name modules).
- Each acceptance criterion in the brief vs the implementation + tests; missing tests = not done.

Independent judgment: verify key assertions in the code yourself; don't take codex's self-report at face value.

## Step 7: Rework (≤3 rounds per task) — native same-thread resume

Write review notes to `$REPO_ROOT/.runtime/codex-dev/<slug>/rework-<N>.md`: one per line "issue, location file:line, expected behavior, cited spec item"; if the reviewer touched the working tree (e.g. restored out-of-scope files), state it. Re-dispatch on the **same codex thread** with only the delta instruction:

```bash
( cd "$WORK" && node "$CC" task --resume-last --write --effort <tier> "$(cat "$REPO_ROOT/.runtime/codex-dev/$SLUG/rework-$N.md")" )
```

codex sees its prior changes on disk plus the thread context. Return to Step 5 after each round. 3 rounds without passing → mark `blocked`, stop that task, report to the user: what was tried, where it's stuck, two ways out (human intervention / Claude fixes it directly — the latter crosses the role boundary and needs the user's nod).

## Step 8: Merge & commit (Claude only — codex never touches git; the single serialization point)

Merge passed tasks one at a time, **only one at a time**. Single-task main-tree branch mode: commit on the `codex/$SLUG` branch → switch back to the original branch and `merge --ff-only` → delete the task branch. Worktree mode runs the full flow:

1. Integration check — merge the latest main branch into the task branch and re-verify:

```bash
git -C "$WT" merge <main-branch>   # simple conflicts: Claude resolves; semantic conflicts: rework that task (tell it the base moved); unsure → ask the user
( cd "$WT" && <project lint/test command> )
```

2. Commit on the task branch: only `git add` files for this task, never `git add -A`; if the project has a structure self-check script, run it after add; follow the project's commit-message convention.
3. Merge back to the main branch and clean up:

```bash
git -C "$REPO_ROOT" merge --ff-only "codex/$SLUG" || git -C "$REPO_ROOT" merge --no-ff "codex/$SLUG"
git -C "$REPO_ROOT" worktree remove "$WT" && git -C "$REPO_ROOT" branch -d "codex/$SLUG"
```

4. Downstream tasks depending on this output can be dispatched only now.

Final report: per task — tier and rework rounds, changed files and test results, commit hash, failed/blocked reasons and suggestions; token/usage if `status` reports it; task-list status update suggestions.

## Recovery (re-entering after an interruption)

The native registry is the source of truth — no run.json/state.json scan needed:

```bash
CC=$(ls -td "$HOME"/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs | head -1)
( cd "<repo-root-or-worktree>" && node "$CC" status )          # in-flight + finished jobs for that workspace
( cd "<repo-root-or-worktree>" && node "$CC" result <jobId> )  # pull a finished job's output
```

Then resume the loop by phase: still `running` → keep polling (Step 4 watchdog); `completed` → mechanical acceptance (Step 5); mid-rework → Step 7. Worktrees live on disk; `git -C "$REPO_ROOT" worktree list` enumerates them.
