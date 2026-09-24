import * as core from '@actions/core';
import * as github from '@actions/github';

function getInputWithDefault(name: string, fallback: string) {
  const value = core.getInput(name);
  return value || fallback;
}

function composeCommand(tool: string, args: string[]) {
  return [tool, ...args].join(' ');
}

export function runAction() {
  try {
    const owner = getInputWithDefault('owner', github.context.repo.owner);
    const repo = getInputWithDefault('repo', github.context.repo.repo);
    const message = core.getInput('message', { required: true });
    const command = composeCommand('echo', [owner, repo, message]);
    core.setOutput('command', command);
  } catch (err) {
    core.setFailed((err as Error).message);
  }
}
