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

The user wants to review the day's work plan before implementation starts. Codex must not begin file edits for a daily project task until it has presented the day's goal, planned changes, verification commands, expected docs/wiki updates, and received explicit user approval.

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
3. Identify the current project day from `docs/daily-log.md`.
4. Inspect the repository state.
5. Present the proposed day plan for user review.
6. Wait for explicit approval before editing files.
7. Implement the approved day task.
8. Run the smallest useful verification command.
9. Update relevant docs inside this repository.
10. Update the technical wiki when new concepts are learned or used.
11. Append a daily log entry to `docs/daily-log.md`.
12. Summarize what changed, what was verified, and what to do next.

If `docs/daily-log.md` does not exist, create it using the template in `docs/daily-codex-workflow.md`.

## Documentation Rules

Use concise Markdown.

Do not rely on Obsidian wikilinks inside this project. Use relative Markdown links for repository documents.

Examples:

- `[Project Plan](docs/project-plan.md)`
- `[Daily Workflow](docs/daily-codex-workflow.md)`
- `[Daily Log](docs/daily-log.md)`

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
- If a daily task uses a new concept, add or update at least one wiki page before finishing the session.
- Link wiki pages with relative Markdown links, not Obsidian wikilinks.

## Skills

This project uses these workflow skills:

Required skills:

- `start-day`: start the next day or a specified day after user review
- `update-wiki`: record concepts learned so far into `docs/wiki/`
- `record-daily-log`: write the day's implementation log, including issues, errors, fixes, and reflection

The project also keeps copies of these skill files under `skills/` for reference.

## Implementation Rules

Prefer simple, explainable Python.

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
    daily-log.md
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
