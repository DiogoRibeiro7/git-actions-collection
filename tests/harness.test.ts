import { describe, it, expect, beforeEach } from 'vitest';
import * as core from '@actions/core';
import { runAction } from './helpers/action';

beforeEach(() => {
  core.__reset();
});

describe('JS/TS action test harness', () => {
  it('fails when required input is missing', () => {
    core.__setInputs({});
    runAction();
    const state = core.__getState();
    expect(state.failedMessage).toContain('Input required');
  });

  it('applies defaults when inputs are not provided', () => {
    core.__setInputs({ message: 'hello' });
    runAction();
    const state = core.__getState();
    expect(state.outputs.get('command')).toContain('demo repo');
  });

  it('composes command from inputs', () => {
    core.__setInputs({ owner: 'acme', repo: 'widget', message: 'hi' });
    runAction();
    const state = core.__getState();
    expect(state.outputs.get('command')).toBe('echo acme widget hi');
  });

  it('sets outputs on happy path', () => {
    core.__setInputs({ message: 'ok' });
    runAction();
    const state = core.__getState();
    expect(state.outputs.get('command')).toMatch('echo');
    expect(state.failedMessage).toBeNull();
  });

  it('sets failed on error path', () => {
    core.__setInputs({ message: '' });
    runAction();
    const state = core.__getState();
    expect(state.failedMessage).not.toBeNull();
  });
});
