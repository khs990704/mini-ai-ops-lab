# Docker

## Short Definition

Docker packages an application with its runtime dependencies so it can run in a more reproducible environment.

## Why It Matters In This Project

The project should be easy for another reviewer to run. Docker is useful because the training job and tool runner can be executed with known Python dependencies instead of relying on a hidden local setup.

## Where It Appears In This Repository

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `.env.example`

## Commands Or Code To Know

```bash
docker build -t mini-ai-ops-lab .
docker run --rm mini-ai-ops-lab python src/run_job.py --config configs/train.yaml
```

## Common Failure Cases

- Failure: dependencies differ between local and container environments
- Symptom: code works locally but fails in Docker
- What to check: `requirements.txt`, Python version, file paths
- Recovery: pin dependencies and verify the same command in Docker

## Practical Explanation

Docker helps make the training and operations environment reproducible. In this project, Docker is used to show that the job runner does not depend only on one local machine setup.

## Related Docs

- [Project Plan](../project-plan.md)
- [Runbook](../runbook.md)
