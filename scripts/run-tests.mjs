import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { platform } from "node:os";

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { stdio: "inherit", ...opts });
  return res.status ?? 1;
}

function hasCmd(cmd) {
  if (platform() === "win32") {
    return existsSync(`${process.env.SystemRoot}\\System32\\where.exe`)
      ? run("where", [cmd], { stdio: "ignore" }) === 0
      : false;
  }
  return run("which", [cmd], { stdio: "ignore" }) === 0;
}

const isWin = platform() === "win32";
let status = 0;

status ||= run("pytest", ["-q"]);

if (isWin && !hasCmd("bats")) {
  console.warn("bats not found on Windows; skipping bats tests. Install bats or use WSL.");
  process.exit(status);
}

status ||= run("bats", ["tests/bash"]);
process.exit(status);
