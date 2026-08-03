# MLOps

## Short Definition

MLOps is the practice of operating machine learning work so that experiments, training runs, models, logs, and deployment-related artifacts can be tracked and reproduced.

## Why It Matters In This Project

Mini AI Ops Lab uses MLOps ideas to turn a training script into an operational job. The important point is not model accuracy. The important point is whether a reviewer can see which config produced which metric and artifact.

## Where It Appears In This Repository

- `configs/train.yaml`
- `src/train_job.py`
- `src/run_job.py`
- `logs/runs.jsonl`
- `artifacts/`

## Commands Or Code To Know

```bash
python src/run_job.py --config configs/train.yaml
tail -n 3 logs/runs.jsonl
find artifacts -maxdepth 2 -type f
```

## Common Failure Cases

- Failure: a run cannot be reproduced
- Symptom: old metrics exist but the config or artifact path is missing
- What to check: `logs/runs.jsonl`, `configs/train.yaml`, `artifacts/`
- Recovery: store config, metrics, and artifact path together for each run

## Practical Explanation

MLOps is important because model results are not useful if the team cannot trace how they were produced. In this project, each training run records parameters, metrics, status, and artifact paths so that results can be compared and reproduced.

## Related Docs

- [Project Plan](../project-plan.md)
- [Daily Workflow](../daily-codex-workflow.md)
