const globals = require("globals");
const pluginJs = require("@eslint/js");
const pluginReactHooks = require("eslint-plugin-react-hooks");
const tsParser = require("@typescript-eslint/parser");
const tsPlugin = require("@typescript-eslint/eslint-plugin");
const nextPlugin = require("@next/eslint-plugin-next");

module.exports = [
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
    ],
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "react-hooks": pluginReactHooks,
      "@next/next": nextPlugin,
    },
    rules: {
      ...pluginJs.configs.recommended.rules,
      ...tsPlugin.configs.recommended.rules,
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "react/no-unescaped-entities": "off",
      "no-empty": "off",
      "no-undef": "off",
      "no-extra-boolean-cast": "off",
      "no-useless-escape": "off",
    },
  },
];