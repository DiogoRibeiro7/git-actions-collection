import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default defineConfig([
  { ignores: ['**/node_modules/**', '**/dist/**'] },
  {
    files: ['**/*.{ts,mts}'],
    extends: [js.configs.recommended, tseslint.configs.recommended],
    languageOptions: { globals: globals.node }
  },
  {
    files: ['eslint.config.mjs'],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node }
  }
]);
