# Agent Runtime

## Short Definition

An Agent runtime is the environment that receives tool call requests, validates them, executes allowed tools, and records results.

## Why It Matters In This Project

NST mentions Agent execution environments, including tool calls, execution, isolation, and logs. This project demonstrates those ideas with a small allowlist-based tool runner.

## Where It Appears In This Repository

- `configs/tools.yaml`
- `src/tool_runner.py`
- `src/audit_logger.py`
- `logs/audit.jsonl`

## Commands Or Code To Know

```bash
python src/tool_runner.py --tool echo --input "hello"
python src/tool_runner.py --tool unknown
tail -n 5 logs/audit.jsonl
```

## Common Failure Cases

- Failure: unauthorized tool request
- Symptom: unknown or dangerous tool name is requested
- What to check: `configs/tools.yaml`, `logs/audit.jsonl`
- Recovery: reject by default and record the attempt in the audit log

## Practical Explanation

Agent tool execution should be controlled because unrestricted tools can create reliability and security risks. In this project, the runner uses an allowlist, input handling, timeout, and audit logs so tool calls can be traced and limited.

## Related Docs

- [Project Plan](../project-plan.md)
- [Failure Scenarios](../failure-scenarios.md)
