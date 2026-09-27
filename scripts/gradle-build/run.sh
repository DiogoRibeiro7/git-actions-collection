#!/usr/bin/env bash
set -euo pipefail

if [ -z "${INPUT_TASKS+x}" ]; then
  tasks="build"
else
  tasks="${INPUT_TASKS}"
fi
gradle_args="${INPUT_GRADLE_ARGS:---build-cache}"
working_directory="${INPUT_WORKING_DIRECTORY:-.}"

# Tasks and arguments are separated by spaces or newlines. Splitting on spaces
# alone kept only the first line of a `tasks: |` block, so later tasks never ran.
read -r -d '' -a task_arr <<< "$tasks" || true
read -r -d '' -a arg_arr <<< "$gradle_args" || true
if [ "${#task_arr[@]}" -eq 0 ]; then
  echo "tasks input must not be empty" >&2
  exit 1
fi

cd "$working_directory"
./gradlew "${task_arr[@]}" "${arg_arr[@]}"
