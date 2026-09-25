# Gradle Build

Run [Gradle](https://gradle.org/) builds with caching and configurable tasks.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `java-version` | no | `17` | Java version to use |
| `tasks` | no | `build` | Gradle tasks to run |
| `gradle-args` | no | `--build-cache` | Additional Gradle arguments |
| `working-directory` | no | `.` | Directory of the Gradle project |

## Outputs

This action has no outputs.
<!-- END GENERATED REFERENCE -->

## Example

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/gradle-build@v1
  with:
    java-version: '17'
    tasks: build test
    gradle-args: '--build-cache --info'
    working-directory: backend/
```

## Security Considerations

- Third-party actions are pinned by commit SHA to mitigate supply-chain attacks.
- Review and update the pinned commits for
  `actions/setup-java` and `gradle/actions/setup-gradle` periodically.

## Configuration Tips

- Modify `tasks` to run custom Gradle goals (e.g., `assemble`, `check`).
- Use `gradle-args` for flags like `--scan` or `--parallel`.
- Caching of Gradle dependencies and wrappers is automatically handled by `setup-gradle`.
