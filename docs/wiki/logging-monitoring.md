# Logging And Monitoring

## Short Definition

Logging records events that happened. Monitoring tracks system or application state over time so operators can detect problems.

## Why It Matters In This Project

This project starts with structured logs because they are the simplest operational evidence. Logs show which job ran, whether it succeeded, how long it took, what metric it produced, and what failed.

## Where It Appears In This Repository

- `logs/runs.jsonl`
- `logs/audit.jsonl`
- `logs/errors.jsonl`
- `src/run_job.py`
- `src/tool_runner.py`

## Commands Or Code To Know

```bash
tail -n 5 logs/runs.jsonl
tail -n 5 logs/audit.jsonl
wc -l logs/runs.jsonl
```

## Common Failure Cases

- Failure: logs are unstructured or missing fields
- Symptom: a failure happened but the cause cannot be traced
- What to check: log schema, exception handling, run id consistency
- Recovery: record structured fields such as status, timestamps, duration, error, and artifact path

## Practical Explanation

Logs are the first tool for understanding operational failures. In this project, run logs and audit logs are written as JSONL so each training job and tool call can be inspected and traced.

## Related Docs

- [Runbook](../runbook.md)
- [Failure Scenarios](../failure-scenarios.md)
