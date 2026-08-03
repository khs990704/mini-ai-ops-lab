# Linux Operations

## Short Definition

Linux operations means checking processes, files, logs, disk usage, permissions, and runtime behavior on a Linux system.

## Why It Matters In This Project

The project will be developed in WSL and should behave like a small operational system. The user needs to know how to inspect generated logs, artifacts, running processes, and file permissions.

## Where It Appears In This Repository

- `logs/`
- `artifacts/`
- `docs/runbook.md`
- shell commands used for verification

## Commands Or Code To Know

```bash
pwd
ls -la
find artifacts -maxdepth 2 -type f
tail -n 5 logs/runs.jsonl
du -sh logs artifacts
```

## Common Failure Cases

- Failure: output file is missing
- Symptom: command ran but no log or artifact appears
- What to check: current working directory, relative paths, write permissions
- Recovery: run from the project root and confirm required directories exist

## Practical Explanation

For operations work, code behavior must be checked through the runtime environment. In this project, Linux commands are used to inspect logs, artifacts, paths, and file sizes so that failures can be diagnosed from observable evidence.

## Related Docs

- [Daily Workflow](../daily-codex-workflow.md)
- [Runbook](../runbook.md)
