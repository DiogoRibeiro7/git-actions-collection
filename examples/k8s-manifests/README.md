# Kubernetes Manifests Example

Demonstrates the `k8s-manifests-lint` workflow which validates Kubernetes YAML using kubeconform.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/k8s-manifests-lint.yml@v1
    with:
      paths: .
```

Examples use the stable `@v1` tag. Pin an exact commit SHA when immutable reproducibility is required.
