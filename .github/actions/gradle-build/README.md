# Gradle Build

Run [Gradle](https://gradle.org/) builds with caching and configurable tasks.

<!-- BEGIN GENERATED REFERENCE: python scripts/action_docs.py --write -->
## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `java-version` | no | `17` | Java version to use |
| `tasks` | no | `build` | Gradle tasks to run, separated by spaces or newlines |
| `gradle-args` | no | `--build-cache` | Additional Gradle arguments, separated by spaces or newlines |
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

## How it runs Gradle

The action installs `java-version` (Temurin) and sets up
`gradle/actions/setup-gradle`, then runs the project's wrapper:
`./gradlew <tasks> <gradle-args>` in `working-directory`. The project must
commit its Gradle wrapper (`gradlew` and `gradle/wrapper/`). The wrapper decides
the Gradle version, so choose a `java-version` that version can run on; Gradle 9
needs Java 17 or newer.

`tasks` and `gradle-args` may list their entries on one line or one per line:

```yaml
- uses: DiogoRibeiro7/git-actions-collection/.github/actions/gradle-build@v1
  with:
    tasks: |
      clean
      build
```

Each entry is passed to Gradle as its own argument, so an argument cannot contain
spaces. A `tasks` value with no task in it fails the step.

## Security Considerations

- Third-party actions are pinned by commit SHA to mitigate supply-chain attacks.
- Review and update the pinned commits for
  `actions/setup-java` and `gradle/actions/setup-gradle` periodically.

## Configuration Tips

- Modify `tasks` to run custom Gradle goals (e.g., `assemble`, `check`).
- Use `gradle-args` for flags like `--scan` or `--parallel`.
- Caching of Gradle dependencies and wrappers is automatically handled by `setup-gradle`.
