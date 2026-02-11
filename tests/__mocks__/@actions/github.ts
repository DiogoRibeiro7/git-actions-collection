export function getOctokit(token: string) {
  return {
    token,
    rest: {
      repos: {
        get: async () => ({ data: { id: 1, name: 'demo' } })
      },
      issues: {
        createComment: async () => ({ data: { id: 123 } })
      }
    }
  };
}

export const context = {
  repo: { owner: 'demo', repo: 'repo' },
  sha: 'deadbeef',
  eventName: 'pull_request',
  payload: {
    pull_request: {
      number: 42
    }
  }
};
