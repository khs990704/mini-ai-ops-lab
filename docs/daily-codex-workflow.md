# Daily Codex Workflow

## Purpose

This document is the day-by-day execution guide for Mini AI Ops Lab.

The goal is to build the project while learning the required technical concepts through implementation.

## How To Use This Document

At the start of each session:

1. Read `AGENTS.md`.
2. Read `docs/project-plan.md`.
3. Check `docs/daily-log.md`.
4. Find the latest completed day.
5. Prepare the next unfinished day plan, or the day explicitly requested by the user.
6. Present the plan for user review before file edits.
7. Start implementation only after explicit user approval.
8. Keep the work small enough to finish, verify, and document in one session.

At the end of each session:

1. Run a useful verification command.
2. Update the README or relevant docs.
3. Update `docs/wiki/` when the day introduced or used a concept the user should learn.
4. Append a daily log entry.
5. State the next recommended task.

## User Review Gate

Before implementing a daily task, Codex must show a short plan:

- day number and goal
- files likely to be created or changed
- verification commands to run
- wiki pages likely to be updated
- expected daily-log entry topics

Then Codex must wait for the user to approve, revise, or stop the plan.

If the user says "진행", "승인", "좋아", "해줘", or gives equivalent approval, Codex can proceed.

If the user changes the scope, Codex must revise the plan and confirm the new scope before editing.

## Project Outcome

By the end of the plan, the repository should contain:

- runnable training job management
- experiment config and run logs
- model artifact storage
- failure logs
- Agent tool runner with allowlist and timeout
- audit log examples
- runbook
- failure scenario document
- security and backup checklist
- project-local technical wiki

## Daily Log Rules

The file `docs/daily-log.md` is the project diary. It should be updated every day.

Each entry must use this format:

```markdown
## Day N - YYYY-MM-DD

### Goal

### Work Done

### Commands Run

### Verification Result

### Problems Found

### Fixes or Decisions

### Reflection

### What I Learned

### Wiki Updated

### Next Step
```

Rules:

- Keep each entry factual.
- Include command outputs only when they matter.
- Record failures instead of hiding them.
- Include errors, confusing parts, and decisions made during troubleshooting.
- `Reflection` should explain what went wrong, why it mattered, and what will be handled differently next time.
- Explain technical decisions in plain language.
- If work is partial, mark it clearly.
- In `Wiki Updated`, list wiki pages created or changed. Write `None` only if no project-relevant concept was introduced.

## Technical Wiki Workflow

The project-local technical wiki lives in `docs/wiki/`.

Use the wiki to teach the user concepts as they become necessary for the project. Do not wait until the end of the project to write theory notes.

Daily rule:

- If the day introduces a concept, create or update the matching wiki page.
- If the day only applies a concept already documented, add a short project-specific note to the existing page.
- If the day is mostly documentation or cleanup, wiki updates are optional.

Initial wiki topics:

- `docs/wiki/mlops.md`
- `docs/wiki/linux-ops.md`
- `docs/wiki/docker.md`
- `docs/wiki/gpu-infra.md`
- `docs/wiki/agent-runtime.md`
- `docs/wiki/logging-monitoring.md`
- `docs/wiki/security-backup.md`

Each wiki page should answer:

1. What is this?
2. Why does it matter here?
3. Where is it used in this repo?
4. What commands or files should I know?
5. What can go wrong?
6. How should I understand it in practice?

## Day 1: Repository Skeleton And Project Framing

Goal:

Create the project skeleton and make the project runnable and understandable.

Tasks:

- Create base folders: `configs/`, `src/`, `docs/`, `logs/`, `artifacts/`.
- Create `.gitignore`.
- Create `.env.example`.
- Create `requirements.txt`.
- Create initial `README.md`.
- Create placeholder `.gitkeep` files in `logs/` and `artifacts/`.
- Write a short project overview focused on the system being built.

Study While Building:

- What an AI operations project is
- Why logs and artifacts matter
- Difference between code execution and job operation

Completion Criteria:

- Repository structure exists.
- README explains why the project exists.
- Logs and artifacts folders are ready.
- Daily log has Day 1 entry.

## Day 2: Basic Training Job

Goal:

Create a simple training job that can run from the command line.

Tasks:

- Implement `src/train_job.py`.
- Use a small scikit-learn dataset.
- Train a simple model.
- Print or return metrics.
- Keep the model simple enough to explain.

Study While Building:

- What a training job is
- What a metric is
- What a model artifact is

Completion Criteria:

- A command can run the training job.
- The output includes at least one metric.
- Code is simple and readable.

Verification Example:

```bash
python src/train_job.py
```

## Day 3: Artifact Storage

Goal:

Save the trained model as an artifact with a unique run id.

Tasks:

- Generate a `run_id`.
- Create `artifacts/{run_id}/`.
- Save the model file there.
- Return the artifact path.
- Document where artifacts are stored.

Study While Building:

- Model artifact
- Run id
- Reproducible output path

Completion Criteria:

- Each run creates a separate artifact folder.
- The model file can be found after training.
- README describes artifact storage.

Verification Example:

```bash
python src/train_job.py
find artifacts -maxdepth 2 -type f
```

## Day 4: Run Log

Goal:

Record each training execution as a structured JSONL log.

Tasks:

- Implement or update `src/run_job.py`.
- Write logs to `logs/runs.jsonl`.
- Include `run_id`, `status`, `started_at`, `ended_at`, `duration_seconds`, `metrics`, and `artifact_path`.
- Make successful run logs easy to inspect.

Study While Building:

- Structured logging
- JSONL
- Job status
- Duration measurement

Completion Criteria:

- Every successful run appends one JSONL line.
- Log fields are consistent.
- README explains how to inspect logs.

Verification Example:

```bash
python src/run_job.py
tail -n 3 logs/runs.jsonl
```

## Day 5: Failure Log And Recovery Note

Goal:

Make failure visible and explainable.

Tasks:

- Add controlled failure mode.
- Record failed status.
- Capture error message and stack trace.
- Write `docs/failure-scenarios.md` first draft.
- Add one recovery procedure.

Study While Building:

- Exception handling
- Failure reproduction
- Incident note

Completion Criteria:

- A failure can be intentionally triggered.
- Failure is logged.
- A recovery procedure is documented.

Verification Example:

```bash
python src/run_job.py --fail
tail -n 3 logs/runs.jsonl
```

## Day 6: Docker Or Reproducible Setup

Goal:

Make the project runnable in a repeatable environment.

Tasks:

- Add `Dockerfile`, or document local setup if Docker is not available.
- Add dependency installation instructions.
- Confirm the training job runs from a clean setup.
- Update README quick start.

Study While Building:

- Reproducible environment
- Dependency pinning
- Container basics

Completion Criteria:

- Another person can follow the README to run the project.
- Dependencies are listed.
- Environment setup is documented.

## Day 7: Week 1 Review

Goal:

Turn the first week of code into a clean project baseline.

Tasks:

- Clean README.
- Add architecture overview.
- Update daily log.
- Create `docs/architecture.md`.
- Write what each component does.

Study While Building:

- How to explain architecture
- How training jobs, logs, and artifacts fit together

Completion Criteria:

- README has a clear overview.
- Architecture doc exists.
- Week 1 daily logs are complete.

## Day 8: Config-Based Training

Goal:

Move training parameters into a config file.

Tasks:

- Create `configs/train.yaml`.
- Load config in the training runner.
- Save config content or config path in the run log.
- Document how to change parameters.

Study While Building:

- Config management
- Reproducibility
- Parameter tracking

Completion Criteria:

- Training uses a config file.
- Run logs show which config was used.
- README documents config-based execution.

## Day 9: Experiment Tracking

Goal:

Make runs comparable.

Tasks:

- Add experiment name.
- Store metrics, parameters, and artifact path together.
- Add a simple script or command for listing recent runs.
- Update README with an experiment tracking example.

Study While Building:

- Experiment tracking
- Metric comparison
- Model version traceability

Completion Criteria:

- Recent runs can be compared.
- Each run has parameters and metrics.
- It is clear which run produced which artifact.

## Day 10: Reproduction Procedure

Goal:

Document how to reproduce a previous run.

Tasks:

- Pick one run id.
- Record the config and command used.
- Add a reproduction section to `docs/runbook.md`.
- Confirm the command works again.

Study While Building:

- Reproducibility
- Runbook writing
- Operational handoff

Completion Criteria:

- `docs/runbook.md` includes reproduction steps.
- At least one previous run can be repeated.

## Day 11: Tool Allowlist

Goal:

Define which Agent tools are allowed.

Tasks:

- Create `configs/tools.yaml`.
- Define `echo`, `list_artifacts`, `read_log_summary`, and `run_train_job`.
- Document why allowlists matter.

Study While Building:

- Agent tool call
- Allowlist
- Least privilege

Completion Criteria:

- Tool definitions exist.
- The config clearly says what each tool is allowed to do.

## Day 12: Tool Runner

Goal:

Implement the first Agent tool runner.

Tasks:

- Implement `src/tool_runner.py`.
- Accept a tool name and input.
- Execute only allowlisted tools.
- Reject unknown tools.
- Return structured result.

Study While Building:

- Input validation
- Command dispatch
- Controlled execution

Completion Criteria:

- Allowed tool works.
- Unknown tool is rejected.
- Result is structured.

Verification Example:

```bash
python src/tool_runner.py --tool echo --input "hello"
python src/tool_runner.py --tool unknown
```

## Day 13: Timeout And Audit Log

Goal:

Add operational controls to tool execution.

Tasks:

- Add timeout handling.
- Record `tool_name`, `status`, `started_at`, `duration_seconds`, and error fields.
- Write audit logs to `logs/audit.jsonl`.
- Add timeout failure scenario.

Study While Building:

- Timeout
- Audit log
- Operational traceability

Completion Criteria:

- Each tool call writes an audit log.
- Timeout is handled cleanly.
- Failure scenario is documented.

## Day 14: Week 2 Review

Goal:

Connect MLOps and Agent execution into one coherent system.

Tasks:

- Update README architecture section.
- Update `docs/architecture.md`.
- Add a short explanation of MLOps and Agent components.
- Review all logs for consistency.

Study While Building:

- System boundaries
- Operational story
- Component responsibilities

Completion Criteria:

- README explains both training jobs and tool runner.
- Architecture doc is clear.
- Daily logs are complete through Day 14.

## Day 15: Failure Scenarios

Goal:

Document realistic failure cases.

Tasks:

- Complete `docs/failure-scenarios.md`.
- Include at least five failure cases.
- For each case, write symptoms, logs to check, likely cause, recovery, and prevention.

Required Cases:

- training job failure
- artifact save failure
- config load failure
- tool timeout
- unauthorized tool request

Completion Criteria:

- Failure scenarios are specific.
- Each scenario maps to project logs or code.

## Day 16: Runbook

Goal:

Create the operator manual.

Tasks:

- Complete `docs/runbook.md`.
- Include setup, run, inspect logs, reproduce run, recover failure, and cleanup.
- Use commands that actually work in this repository.

Completion Criteria:

- The project can be operated using only the runbook.
- Commands are verified.

## Day 17: Security And Backup Checklist

Goal:

Show security and backup awareness.

Tasks:

- Complete `docs/security-backup-checklist.md`.
- Include secret handling, `.env.example`, ignored files, log retention, artifact backup, and access control.
- Add RPO/RTO basics if useful.

Completion Criteria:

- The checklist is practical.
- It explains what should not be committed.
- It includes backup and restore test ideas.

## Day 18: README Cleanup

Goal:

Make the project easy to understand and run.

Tasks:

- Rewrite README for a technical reader.
- Put the project purpose near the top.
- Add quick start.
- Add architecture summary.
- Link docs.
- Include sample log snippets.

Completion Criteria:

- A reader can understand the project quickly.
- README emphasizes operations, not model accuracy.

## Day 19: Code And Log Review

Goal:

Review implementation quality before final cleanup.

Tasks:

- Review code paths for avoidable duplication.
- Check log schemas for consistency.
- Check error messages for clarity.
- Add or update small tests if useful.
- Document any tradeoffs.

Completion Criteria:

- Major code paths are understandable.
- Log fields are consistent.
- Known tradeoffs are documented.

## Day 20: Technical Wiki Review

Goal:

Make the technical wiki useful for continued learning.

Tasks:

- Review all pages under `docs/wiki/`.
- Add missing project-specific examples.
- Remove vague theory.
- Link wiki pages to relevant docs and files.

Completion Criteria:

- Wiki pages explain the concepts used in the project.
- Pages are practical and connected to the repository.

## Day 21: Final Project Check

Goal:

Make the repository technically complete for the current project scope.

Tasks:

- Run all verification commands.
- Remove accidental large files or secrets.
- Check README links.
- Check docs completeness.
- Add final daily log.

Completion Criteria:

- Project runs.
- Logs are generated.
- Docs are linked.
- Technical wiki is coherent.
- The project is ready for continued use or later application-material preparation.

## Daily Log Template

Create `docs/daily-log.md` with this content when starting Day 1:

```markdown
# Daily Log

## Project Goal

Mini AI Ops Lab은 학습 작업 관리, 실험 기록, Agent 실행환경, 로그, 장애 대응, 보안/백업 문서를 갖춘 작은 AI 운영 시스템을 만드는 프로젝트다.

## Day 1 - YYYY-MM-DD

### Goal

### Work Done

### Commands Run

### Verification Result

### Problems Found

### Fixes or Decisions

### What I Learned

### Wiki Updated

### Next Step
```

## Codex Response Rule

When Codex finishes a daily task, the final response should include:

- what was implemented
- what was verified
- which files changed
- what the user should understand technically
- the next recommended day task

Keep the response concise and practical.
