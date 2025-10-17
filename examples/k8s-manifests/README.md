# Kubernetes Manifests Example

Demonstrates the `k8s-manifests-lint` workflow which validates Kubernetes YAML using kubeconform.

```yaml
jobs:
  lint:
    uses: DiogoRibeiro7/gh-actions-collection/.github/workflows/k8s-manifests-lint.yml@main
    with:
      paths: .
```
