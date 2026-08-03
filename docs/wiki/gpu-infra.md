# GPU Infrastructure

## Short Definition

GPU infrastructure includes GPU devices, drivers, CUDA compatibility, memory usage, utilization, scheduling, and operational checks.

## Why It Matters In This Project

The project does not require a real GPU at first, but it should still document how GPU-based training jobs would be inspected and operated. This matters because the NST role includes GPU infrastructure operation and failure response.

## Where It Appears In This Repository

- `docs/runbook.md`
- `docs/failure-scenarios.md`
- future GPU check notes or scripts

## Commands Or Code To Know

```bash
nvidia-smi
watch -n 1 nvidia-smi
```

If a GPU is not available in WSL, document that limitation and keep the project CPU-runnable.

## Common Failure Cases

- Failure: GPU out of memory
- Symptom: training process fails with CUDA OOM
- What to check: `nvidia-smi`, batch size, model size, other processes
- Recovery: reduce batch size, stop unused processes, move job to another GPU, or adjust scheduling

## Practical Explanation

GPU operations require checking both utilization and memory, not just whether a GPU exists. Even when this project runs on CPU, the runbook should explain how GPU jobs would be inspected with `nvidia-smi` and how OOM failures would be handled.

## Related Docs

- [Failure Scenarios](../failure-scenarios.md)
- [Runbook](../runbook.md)
