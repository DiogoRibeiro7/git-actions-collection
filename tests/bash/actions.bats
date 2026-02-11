load ./helpers.bash

@test "aws-lambda-build builds with pip version and outputs zip" {
  make_logger python
  make_logger pip
  make_logger rsync
  make_fake zip 'touch "${2}"; echo "zip $@" >> "$COMMAND_LOG"'

  mkdir -p "$TEST_TMPDIR/lambda"
  echo "" > "$TEST_TMPDIR/lambda/requirements.txt"

  INPUT_SRC="$TEST_TMPDIR/lambda" INPUT_OUTPUT_ZIP="artifact/lambda.zip" INPUT_PIP_VERSION="23.0.1" \
    bash "$REPO_ROOT/scripts/aws-lambda-build/build.sh"

  [ -f "$TEST_TMPDIR/artifact/lambda.zip" ]
  run grep -q "pip install" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "check-imports writes missing output" {
  make_logger pip
  make_fake python '
if [ "$1" = "-c" ]; then
  echo "foo bar"
  exit 0
fi
if echo "$@" | grep -q "--format json"; then
  echo "{\"missing\":[\"foo\",\"bar\"]}"
  exit 0
fi
exit 0
'

  INPUT_PATHS="src" INPUT_FAIL_ON="missing" INPUT_FORMAT="json" INPUT_UPDATE_PYPROJECT="false" \
    INPUT_PIP_VERSION="24.3.1" bash "$REPO_ROOT/scripts/actions/check-imports/check.sh"

  run grep -q "missing=foo bar" "$GITHUB_OUTPUT"
  [ "$status" -eq 0 ]
}

@test "check-imports update runs smart update" {
  make_fake python 'echo "python $@" >> "$COMMAND_LOG"'

  INPUT_PATHS="src" INPUT_SMART_UPDATE="true" bash "$REPO_ROOT/scripts/actions/check-imports/update.sh"

  run grep -q "smart_dependency_update.py --manifests pyproject.toml --apply" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "benchmark-smoke run composes pytest flags" {
  make_logger python
  make_logger pip
  make_fake pytest 'echo "pytest $@" >> "$COMMAND_LOG"'

  INPUT_PIP_VERSION="24.3.1" bash "$REPO_ROOT/scripts/benchmark-smoke/install.sh"
  INPUT_PYTEST_ARGS="-k fast" bash "$REPO_ROOT/scripts/benchmark-smoke/run.sh"

  run grep -q "pytest -k fast --benchmark-only --benchmark-json=benchmark.json" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "apm-integration rejects invalid provider" {
  run env INPUT_PROVIDER="bad" INPUT_API_KEY="token" bash "$REPO_ROOT/scripts/apm-integration/notify.sh"
  [ "$status" -ne 0 ]
  [[ "$output" == *"Unsupported provider"* ]]
}

@test "apm-integration datadog calls curl" {
  make_logger curl
  make_fake jq 'echo ""'

  INPUT_PROVIDER="datadog" INPUT_API_KEY="token" INPUT_ENVIRONMENT="prod" INPUT_DEPLOYMENT_ID="abc" \
    bash "$REPO_ROOT/scripts/apm-integration/notify.sh"

  run grep -q "https://api.datadoghq.com/api/v1/events" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "apm-integration warns when latency exceeds threshold" {
  metrics="$REPO_ROOT/tests/bash/fixtures/metrics.json"
  warning="$(cat "$REPO_ROOT/tests/bash/fixtures/apm_warning.txt")"
  make_logger curl
  make_fake jq 'if [ "$2" = ".latency // empty" ]; then echo 200; else echo 100; fi'

  run env INPUT_PROVIDER="datadog" INPUT_API_KEY="token" INPUT_DEPLOYMENT_ID="abc" INPUT_METRICS_FILE="$metrics" \
    bash "$REPO_ROOT/scripts/apm-integration/notify.sh"

  [ "$status" -eq 0 ]
  [[ "$output" == *"$warning"* ]]
}

@test "r-lint package inputs include extras" {
  INPUT_ADDITIONAL_PACKAGES="testthat" bash "$REPO_ROOT/scripts/r-lint/package-inputs.sh"
  run grep -q "packages=lintr,testthat" "$GITHUB_OUTPUT"
  [ "$status" -eq 0 ]
}

@test "r-lint run invokes Rscript with args" {
  make_logger Rscript
  INPUT_CONFIG_FILE=".lintr" INPUT_TARGETS="R" INPUT_WORKING_DIRECTORY="/tmp" \
    bash "$REPO_ROOT/scripts/r-lint/run-lint.sh"
  run grep -q "Rscript" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "smart-dependency-update requires manifests" {
  run env INPUT_MANIFESTS="" bash "$REPO_ROOT/scripts/actions/smart-dependency-update/run.sh"
  [ "$status" -ne 0 ]
}

@test "smart-dependency-update writes report output" {
  make_fake python 'echo "{}"'
  make_logger pip

  INPUT_MANIFESTS="pyproject.toml" INPUT_APPLY="false" INPUT_BATCH_SIZE="5" INPUT_DEPENDABOT="false" \
    INPUT_REPO="" INPUT_PIP_VERSION="24.3.1" bash "$REPO_ROOT/scripts/actions/smart-dependency-update/run.sh"

  run grep -q "report={}" "$GITHUB_OUTPUT"
  [ "$status" -eq 0 ]
}

@test "python-type-check installs requirements and runs mypy" {
  make_fake python 'echo "python $@" >> "$COMMAND_LOG"'
  make_fake mypy 'echo "mypy $@" >> "$COMMAND_LOG"'

  INPUT_REQUIREMENTS_FILE="requirements.txt" INPUT_EXTRA_DEPENDENCIES="" INPUT_MYPY_ARGS="src" \
    INPUT_PIP_VERSION="24.3.1" bash "$REPO_ROOT/scripts/python-type-check/run.sh"

  run grep -q "python -m pip install -r requirements.txt" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
  run grep -q "mypy src" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "pr-template-enforcer fails on missing sections" {
  run env PR_BODY="" bash "$REPO_ROOT/scripts/pr-template-enforcer/enforce.sh"
  [ "$status" -ne 0 ]
}

@test "gradle-build requires tasks" {
  run env INPUT_TASKS="" INPUT_GRADLE_ARGS="" INPUT_WORKING_DIRECTORY="." bash "$REPO_ROOT/scripts/gradle-build/run.sh"
  [ "$status" -ne 0 ]
}

@test "gradle-build runs gradlew in working directory" {
  mkdir -p "$TEST_TMPDIR/project"
  cat > "$TEST_TMPDIR/project/gradlew" <<'EOF'
#!/usr/bin/env bash
echo "gradlew $@" >> "$COMMAND_LOG"
EOF
  chmod +x "$TEST_TMPDIR/project/gradlew"

  INPUT_TASKS="build" INPUT_GRADLE_ARGS="--info" INPUT_WORKING_DIRECTORY="$TEST_TMPDIR/project" \
    bash "$REPO_ROOT/scripts/gradle-build/run.sh"

  run grep -q "gradlew build --info" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "python-lint runs mypy when enabled" {
  make_fake python 'echo "python $@" >> "$COMMAND_LOG"'
  make_logger pip
  make_fake ruff 'echo "ruff $@" >> "$COMMAND_LOG"'
  make_fake mypy 'echo "mypy $@" >> "$COMMAND_LOG"'

  INPUT_ENABLE_MYPY="true" INPUT_PIP_VERSION="24.3.1" bash "$REPO_ROOT/scripts/python-lint/run.sh"

  run grep -q "ruff check ." "$COMMAND_LOG"
  [ "$status" -eq 0 ]
  run grep -q "mypy ." "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "markdown-lint respects config flag" {
  make_fake npm 'echo "npm $@" >> "$COMMAND_LOG"'
  make_fake markdownlint 'echo "markdownlint $@" >> "$COMMAND_LOG"'

  INPUT_PATHS="README.md" INPUT_CONFIG_FILE=".markdownlint.yml" bash "$REPO_ROOT/scripts/markdown-lint/run.sh"

  run grep -q "markdownlint -c .markdownlint.yml README.md" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "setup-poetry writes cache env" {
  bash "$REPO_ROOT/scripts/setup-poetry/configure-cache.sh"
  run grep -q "POETRY_CACHE_DIR" "$GITHUB_ENV"
  [ "$status" -eq 0 ]
}

@test "setup-poetry install uses pip version" {
  make_logger python
  make_logger pip

  INPUT_PIP_VERSION="24.0.0" bash "$REPO_ROOT/scripts/setup-poetry/install.sh"

  run grep -q "pip==24.0.0" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "setup-yarn corepack and install" {
  make_fake corepack 'echo "corepack $@" >> "$COMMAND_LOG"'
  make_fake yarn 'echo "yarn $@" >> "$COMMAND_LOG"'

  mkdir -p "$TEST_TMPDIR/project"
  touch "$TEST_TMPDIR/project/yarn.lock"

  bash "$REPO_ROOT/scripts/setup-yarn/corepack.sh"
  INPUT_WORKING_DIRECTORY="$TEST_TMPDIR/project" bash "$REPO_ROOT/scripts/setup-yarn/install.sh"

  run grep -q "corepack enable" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
  run grep -q "yarn install --immutable" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "secret-scan uses gitleaks action" {
  run grep -q "gitleaks/gitleaks-action" "$REPO_ROOT/.github/actions/secret-scan/action.yml"
  [ "$status" -eq 0 ]
}

@test "setup-r skips when no packages" {
  make_logger Rscript
  INPUT_PACKAGES="" bash "$REPO_ROOT/scripts/setup-r/install-packages.sh"
  run grep -q "Rscript" "$COMMAND_LOG"
  [ "$status" -ne 0 ]
}

@test "setup-r calls Rscript with packages" {
  make_logger Rscript
  INPUT_PACKAGES="lintr" INPUT_CRAN_MIRROR="https://example.com" INPUT_WORKING_DIRECTORY="/tmp" \
    bash "$REPO_ROOT/scripts/setup-r/install-packages.sh"
  run grep -q "Rscript" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}

@test "r-testthat package inputs include devtools" {
  INPUT_USE_DEVTOOLS="true" INPUT_ADDITIONAL_PACKAGES="" bash "$REPO_ROOT/scripts/r-testthat/package-inputs.sh"
  run grep -q "packages=remotes,testthat,devtools" "$GITHUB_OUTPUT"
  [ "$status" -eq 0 ]
}

@test "r-testthat run invokes Rscript" {
  make_logger Rscript
  INPUT_TEST_DIRECTORY="tests/testthat" INPUT_INSTALL_DEPENDENCIES="true" INPUT_USE_DEVTOOLS="false" \
    INPUT_WORKING_DIRECTORY="/tmp" bash "$REPO_ROOT/scripts/r-testthat/run-tests.sh"
  run grep -q "Rscript" "$COMMAND_LOG"
  [ "$status" -eq 0 ]
}
