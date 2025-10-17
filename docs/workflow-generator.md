# Workflow Generator

The `workflow_generator.py` script creates starter GitHub Actions workflows with
sane defaults and pinned action versions. It helps new projects adopt workflows
without copying boilerplate.

## Usage

```bash
python scripts/workflow_generator.py python
```

This writes `.github/workflows/python-ci.yml` for the `main` branch. Override the
branch or output path if needed:

```bash
python scripts/workflow_generator.py node --branch develop --output .github/workflows/ci.yml
```

## Features

- validates arguments before writing files
- prevents accidental overwrites
- provides defaults for branch and output path
- emits security-hardened templates with pinned action SHAs

## Troubleshooting

- **File exists**: choose a different `--output` path or delete the existing
  file
- **Unsupported language**: only `python` and `node` workflows are currently
  generated
