# Gradle Build

Run [Gradle](https://gradle.org/) builds with caching and configurable tasks.

## Inputs

| Name | Description | Default |
|------|-------------|---------|
| `java-version` | Java version to use | `17` |
| `tasks` | Gradle tasks to run | `build` |
| `gradle-args` | Additional Gradle arguments | `--build-cache` |
| `working-directory` | Directory of the Gradle project | `.` |

## Outputs

None

## Example

```yaml
- uses: DiogoRibeiro7/gh-actions-collection/.github/actions/gradle-build@main
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
