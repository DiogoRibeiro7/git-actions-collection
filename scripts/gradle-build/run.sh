#!/usr/bin/env bash
set -euo pipefail

tasks="${INPUT_TASKS:-build}"
gradle_args="${INPUT_GRADLE_ARGS:---build-cache}"
working_directory="${INPUT_WORKING_DIRECTORY:-.}"

if [ -z "$tasks" ]; then
  echo "tasks input must not be empty" >&2
  exit 1
fi

cd "$working_directory"
IFS=' ' read -r -a task_arr <<< "$tasks"
IFS=' ' read -r -a arg_arr <<< "$gradle_args"
./gradlew "${task_arr[@]}" "${arg_arr[@]}"
