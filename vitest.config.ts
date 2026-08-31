import path from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: {
      '@actions/core': path.resolve(process.cwd(), 'tests/__mocks__/@actions/core.ts'),
      '@actions/github': path.resolve(process.cwd(), 'tests/__mocks__/@actions/github.ts')
    }
  },
  test: {
    environment: 'node',
    globals: true,
    restoreMocks: true,
    clearMocks: true,
    mockReset: true,
    include: ['tests/**/*.test.ts']
  },
  coverage: {
    reporter: ['text', 'lcov'],
    reportsDirectory: 'coverage',
    include: ['tests/**/*.test.ts'],
    exclude: ['**/node_modules/**', '**/dist/**'],
    thresholds: {
      lines: 70,
      functions: 70,
      statements: 70,
      branches: 70
    }
  }
});
