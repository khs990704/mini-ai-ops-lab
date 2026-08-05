# Codex Project Guide

## Project Purpose

This repository is the working folder for Mini AI Ops Lab. The self-contained project plan is in `docs/project-plan.md`.

The user will work on this project from WSL. Do not depend on Obsidian wikilinks, Windows-only paths, or vault-only notes when giving project instructions. Treat this repository as the source of truth.

The goal is to build a small AI operations system while learning the underlying concepts through implementation.

The project should demonstrate:

- training job execution
- experiment tracking
- model artifact management
- structured logs
- failure handling
- Agent tool execution control
- audit logs
- security, backup, and runbook documentation
- project-local technical wiki notes

## Operating Principle

Every project day must produce evidence.

Evidence means at least one of the following:

- working code
- runnable command
- structured log example
- documented failure scenario
- README update
- runbook update
- security or backup checklist update
- technical wiki update
- daily implementation log

Avoid work that is technically interesting but does not move the project forward.

The user wants to review the day's work plan before implementation starts. Codex must not begin file edits for a daily project task until it has presented the day's goal, a numbered step breakdown, planned changes, verification commands, expected docs/wiki updates, and received explicit user approval.

Daily implementation uses a per-step review gate. Initial plan approval authorizes only Step 1. Execute one planned step, run that step's verification, present its changes and code intent, and stop for user review. Continue to the next step only after a new explicit instruction such as "진행". Never combine multiple planned steps under one approval. If the user asks questions, answer them and remain at the current gate until they explicitly approve the next step. If scope changes, revise the remaining steps and obtain approval again.

Wiki and work-log updates have a separate review gate. After implementation and verification, show all changes and results to the user, answer their questions, and wait for explicit finalization approval such as "정리해줘" or "기록해줘". Do not update `docs/wiki/` or create the day's work-log file before that approval. Keep the daily task open until these records are finalized.

## Scope Rules

Stay focused on the core project:

1. A Python training job runner
2. JSONL-based run and failure logs
3. config-based experiment tracking
4. model artifact storage
5. allowlist-based Agent tool runner
6. timeout and audit logging
7. operational documentation
8. technical wiki notes created while building

Do not spend time on:

- advanced model accuracy tuning
- complex frontend dashboards
- large Kubernetes setup
- real GPU dependency as a blocker
- complex LLM Agent behavior
- decorative UI

If a feature is optional, finish the required operational behavior first.

## Daily Workflow

When the user asks to work on this project, Codex should:

1. Read `docs/project-plan.md` for the project context.
2. Read `docs/daily-codex-workflow.md` for the day-by-day work plan.
3. Identify the current project day from `docs/work-logs/README.md` and the files in `docs/work-logs/`.
4. Inspect the repository state.
5. Present the proposed day plan as small numbered steps for user review, including each verification command's purpose, effect, and success evidence.
6. Wait for explicit approval to execute Step 1.
7. Implement only the currently approved step with concise comments or docstrings that explain the purpose of important code.
8. Run the smallest useful verification command for that step.
9. Present that step's changes, code intent, verification result, command purpose and effect, any user-run verification instructions, and remaining steps.
10. Answer the user's review questions and wait for a new explicit approval before executing the next step.
11. Repeat Steps 7-10 until every planned implementation step is reviewed.
12. After the final step, gather any remaining Q&A and the user's reflection when available, then wait for explicit approval to finalize records.
13. After finalization approval, update relevant docs and categorize technical concepts or Q&A into the matching files under `docs/wiki/`.
14. Create one work-log file under `docs/work-logs/` using `YYYY-MM-DD-DayN.md`.
15. Update `docs/work-logs/README.md` and summarize what changed, what was verified, what to do next, and a recommended Git commit message for the finalized day.

If `docs/work-logs/` does not exist, create it with an index at `docs/work-logs/README.md` and use the template in `docs/daily-codex-workflow.md` for each dated entry.

## Documentation Rules

Use concise Markdown.

Write user-facing project documentation in Korean, including `README.md`, pages under `docs/wiki/`, and files under `docs/work-logs/`. Keep source-code identifiers, commands, file paths, protocol fields, library names, and external API terms in their original form when translation would reduce clarity.

Do not rely on Obsidian wikilinks inside this project. Use relative Markdown links for repository documents.

Examples:

- `[Project Plan](docs/project-plan.md)`
- `[Daily Workflow](docs/daily-codex-workflow.md)`
- `[Work Logs](docs/work-logs/README.md)`

Always leave a blank line before Markdown tables so the same files render correctly in Markdown viewers and Obsidian.

Use `$...$` for inline math and `$$...$$` for display math if math is needed.

## Technical Wiki Rules

Codex should maintain a project-local technical wiki under `docs/wiki/`.

The wiki exists so the user can learn the concepts needed for the project while building it. It should explain only concepts that directly support this repository.

Core files:

- `docs/wiki/README.md`: wiki index
- `docs/wiki/template.md`: standard page template
- `docs/wiki/mlops.md`
- `docs/wiki/linux-ops.md`
- `docs/wiki/docker.md`
- `docs/wiki/gpu-infra.md`
- `docs/wiki/agent-runtime.md`
- `docs/wiki/logging-monitoring.md`
- `docs/wiki/security-backup.md`

When to create or update a wiki page:

- a new concept appears in code
- the user asks what something means
- a daily task introduces a technology
- an error reveals an operational concept
- a concept is needed to understand the project

Wiki timing and categorization:

- Do not update the wiki immediately after implementation.
- Wait until the user has reviewed all work, finished asking questions, and explicitly approves finalization.
- Classify concepts and useful user Q&A by topic and add them to the most appropriate existing Markdown page under `docs/wiki/`.
- Create a new category page only when no existing page fits, and then add it to `docs/wiki/README.md`.
- Codex is responsible for choosing the category; the user does not need to name a wiki page.

Each wiki page should include:

1. Short definition
2. Why it matters for this project
3. How it appears in this repository
4. Commands or code references when useful
5. Common failure cases
6. Practical explanation
7. Links to related project docs

Rules:

- Keep pages practical and concise.
- Prefer project-specific examples over general textbook explanations.
- Do not copy long external documentation.
- Do not create wiki pages for concepts unrelated to the project.
- If a daily task uses a new concept, add or update at least one wiki page before finalizing the day after user approval.
- Link wiki pages with relative Markdown links, not Obsidian wikilinks.

## Skills

This project uses these workflow skills:

Required skills:

- `start-day`: start the next day or a specified day after user review
- `update-wiki`: record concepts learned so far into `docs/wiki/`
- `record-daily-log`: after user review and finalization approval, write the user's project-day record, including step-by-step progress, code intent, command purposes and effects, user verification instructions, issues, errors, fixes, Q&A, and user-grounded reflection

The project also keeps copies of these skill files under `skills/` for reference.

## Implementation Rules

Prefer simple, explainable Python.

Code intent and comment rules:

- Add short comments or docstrings where they help the user understand a module, function, operational decision, or non-obvious control flow.
- Explain why the code exists and what operational behavior it protects; do not merely restate the syntax.
- Keep comments concise and avoid commenting every obvious line.
- Write explanatory comments and docstrings in Korean so the user can understand them easily. Keep required identifiers, protocol fields, and external API terms unchanged.
- During review, summarize the purpose of each important file or function. After finalization approval, preserve that summary under `코드 및 설정 의도` in the day's work log.

User-facing project command and verification rules:

- Explain commands that the user can reuse to set up, run, verify, inspect, troubleshoot, recover, or operate this project.
- For each user-facing project command, explain why it is run, what it reads or changes, and what output or file proves success.
- Distinguish read-only inspection commands from commands that install dependencies, generate files, start services, or otherwise change state.
- When the user should verify behavior directly, provide the working directory, prerequisites, an exact copy-paste command, expected output or generated file, and any relevant side effect or cleanup note.
- Clearly separate commands Codex already ran from commands the user still needs to run. Never imply that the user executed a command unless they report doing so.
- Do not ask the user to repeat a verification Codex can reliably perform unless their local observation is necessary or educationally useful.
- Omit Codex-only navigation, search, formatting, diff inspection, and one-off orchestration commands from the work log unless they exposed a project-relevant failure or became a reusable troubleshooting procedure.
- When an internal Codex command exposes a project-relevant failure, record the failure, effect, and fix briefly under `발견한 문제` or `검증 결과`; do not turn the internal command into a user tutorial.

Work-log ownership and voice rules:

- The work log is the user's project and learning record, not a report about what Codex did.
- Write accomplishments from the user's perspective: the user built, verified, decided, and learned with Codex assistance.
- Keep `Codex Q&A` as the explicit place to distinguish the user's question from Codex's answer.
- Base `회고` on the user's actual questions, decisions, corrections, and stated experience. Never invent the user's feelings or claim a personal experience they did not express.
- If a personal reflection would add value but the user has not provided one, ask for it before finalization or write a neutral factual reflection about the workflow and decisions.

Git commit handoff rules:

- After the wiki and work log are finalized, recommend one concise Git commit message that summarizes the completed day's actual changes.
- Prefer the repository's existing commit style and use a conventional prefix such as `feat:`, `fix:`, `docs:`, or `chore:` when appropriate.
- Present the message as a copyable command, but do not create the commit unless the user explicitly asks or approves it.

Recommended structure:

```text
mini-ai-ops-lab/
  README.md
  AGENTS.md
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  configs/
    train.yaml
    tools.yaml
  src/
    train_job.py
    run_job.py
    tool_runner.py
    audit_logger.py
    storage.py
  artifacts/
    .gitkeep
  logs/
    .gitkeep
  docs/
    daily-codex-workflow.md
    work-logs/
      README.md
      YYYY-MM-DD-DayN.md
    project-plan.md
    architecture.md
    runbook.md
    failure-scenarios.md
    security-backup-checklist.md
    wiki/
      README.md
      template.md
  skills/
    start-day/
      SKILL.md
    update-wiki/
      SKILL.md
    record-daily-log/
      SKILL.md
```

Prefer JSONL logs for operational evidence:

- `logs/runs.jsonl`
- `logs/audit.jsonl`
- `logs/errors.jsonl`

Do not commit real secrets, API keys, private credentials, large model files, or local environment files.

## Verification Rule

Each work session should verify at least one useful behavior.

For each user-facing project verification command, report:

- purpose
- whether it is read-only or changes state
- expected behavior or output
- actual result and exit code when Codex ran it
- exact user verification steps when the user needs to run it directly

Examples:

```bash
python src/run_job.py --config configs/train.yaml
python src/tool_runner.py --tool echo --input "hello"
python src/tool_runner.py --tool forbidden_command
```

When verification fails, Codex should record:

- command
- error message
- likely cause
- fix applied or next action
