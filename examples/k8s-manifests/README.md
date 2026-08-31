# Kubernetes Manifests Example

Demonstrates the `k8s-manifests-lint` workflow which validates Kubernetes YAML using kubeconform.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/k8s-manifests-lint.yml@develop
    with:
      paths: .
```

Until the first stable release is cut, examples use `@develop`. For production adoption, pin an exact commit SHA.
