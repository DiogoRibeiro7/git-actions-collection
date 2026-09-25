# PyTorch Train and Deploy Workflow

This experimental reusable workflow trains a PyTorch model inside the
`pytorch/pytorch` CUDA container, optionally logs the model to MLflow, runs a
benchmark script, and uploads the model as an artifact.

## Features

- Runs in `pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime` on `ubuntu-latest` by
  default, without GPU access, because GitHub-hosted Linux runners have no GPU.
- For GPU training, set `runs-on` to a runner with NVIDIA drivers (a GPU larger
  runner or a self-hosted runner) and `gpu: true`, which passes `--gpus all` to
  the container.
- Caches pip downloads and the `data/` directory.
- Logs the model file to an MLflow tracking server when `mlflow-uri` is set.
- Uploads the model file as the `trained-model` artifact.
- `deploy: true` runs a placeholder step that only logs the commit. Deploy from
  your own job that downloads the `trained-model` artifact.

## Inputs

| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| `python-version` | string | no (default `3.10`) | Python version installed with setup-python for training |
| `train-script` | string | no (default `train.py`) | Training script, relative to the repository root |
| `benchmark-script` | string | no (default `benchmark.py`) | Benchmark script run after training |
| `model-artifact` | string | no (default `model.pt`) | Model file the training script writes |
| `deploy` | boolean | no (default `false`) | Run the placeholder deploy step |
| `mlflow-uri` | string | no | MLflow tracking server URL |
| `runs-on` | string | no (default `ubuntu-latest`) | Runner label; choose a GPU runner when `gpu` is true |
| `gpu` | boolean | no (default `false`) | Give the container the runner GPUs (`--gpus all`) |
| `hf-token` | secret | no | Token exposed to the deploy step as `HF_TOKEN` |

## Example

```yaml
name: Train
on: [push]

permissions:
  contents: read

jobs:
  train:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/pytorch-train-deploy.yml@v1
    with:
      python-version: '3.11'
      # Omit both lines to train on the CPU of a GitHub-hosted runner.
      runs-on: gpu-runner
      gpu: true
```

## Security Considerations

- Pin all actions to commit SHAs for supply-chain security
- Store MLflow and deployment credentials in encrypted secrets
- Run benchmarks on isolated runners to avoid leaking model data
