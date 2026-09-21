# PyTorch Train and Deploy Workflow

This reusable workflow trains a PyTorch model with GPU acceleration, tracks experiments, and optionally deploys the resulting artifact.

## Features

- Caches dependencies and datasets to handle large model files efficiently
- Runs inside a CUDA-enabled container with `--gpus all` to access runner GPUs
- Logs metrics and artifacts to an optional MLflow server for experiment tracking
- Uploads the trained model as a versioned artifact and can trigger custom deployment steps
- Executes a separate benchmark script to record performance metrics

## Inputs

| Name | Type | Required | Description |
| ---- | ---- | -------- | ----------- |
| `python-version` | string | no (default `3.10`) | Python version used for training |
| `train-script` | string | no (default `train.py`) | Path to the training script |
| `benchmark-script` | string | no (default `benchmark.py`) | Script that measures inference performance |
| `model-artifact` | string | no (default `model.pt`) | Output model file to upload |
| `deploy` | boolean | no (default `false`) | Whether to run the deployment step |
| `mlflow-uri` | string | no | MLflow tracking server URL |
| `pip-version` | string | no (default `24.3.1`) | pip release installed before training; set to `latest` to follow upstream |
| `hf-token` | secret | no | Token used by the example deployment step |

## Example

```yaml
name: Train and Deploy
on: [push]

jobs:
  train:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/pytorch-train-deploy.yml@develop
    with:
      python-version: '3.11'
      deploy: true
    secrets:
      hf-token: ${{ secrets.HF_TOKEN }}
```

## Security Considerations

- Pin all actions to commit SHAs for supply-chain security
- Store MLflow and deployment credentials in encrypted secrets
- Run benchmarks on isolated runners to avoid leaking model data
- Python environments in this workflow respect the shared pip upgrade policy—the default installer (`24.3.1`) is validated by the repository test suite, and you can override `pip-version` if a newer pip is required.
