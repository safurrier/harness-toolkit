import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    ignores: ["dist/", "node_modules/", "test-results/"],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: { "no-empty": ["error", { allowEmptyCatch: true }] },
  },
];
