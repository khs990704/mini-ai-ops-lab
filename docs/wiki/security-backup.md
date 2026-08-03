# Security And Backup

## Short Definition

Security controls who can access or execute what. Backup and recovery ensure that important data can be restored after loss or failure.

## Why It Matters In This Project

The NST role includes backup, recovery, access audit records, and security operations. This project should show that logs, artifacts, configs, and secrets are handled deliberately.

## Where It Appears In This Repository

- `.env.example`
- `.gitignore`
- `configs/`
- `logs/audit.jsonl`
- `artifacts/`
- `docs/security-backup-checklist.md`

## Commands Or Code To Know

```bash
ls -la
find artifacts -maxdepth 2 -type f
du -sh logs artifacts
```

## Common Failure Cases

- Failure: secret accidentally committed
- Symptom: API key or password appears in Git history or logs
- What to check: `.gitignore`, `.env`, logs, repository diff
- Recovery: remove the secret, rotate it, and document the prevention rule

## Practical Explanation

Operations work should consider security and recovery from the start. In this project, secrets are separated from code, audit logs record tool calls, and artifact/log backup rules are documented so the system can be reviewed and recovered.

## Related Docs

- [Security Backup Checklist](../security-backup-checklist.md)
- [Runbook](../runbook.md)
