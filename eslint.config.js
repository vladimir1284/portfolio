import js from "@eslint/js";
import tseslint from "typescript-eslint";
import astro from "eslint-plugin-astro";
import globals from "globals";

// Flat config is a plain array of config objects; the spreads below are already
// arrays. Exporting the array directly avoids the deprecated `tseslint.config()`
// overload (ts 6387) while keeping identical lint behavior.
export default [
  // never lint build output / generated / deps
  { ignores: ["dist/", ".astro/", "node_modules/"] },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...astro.configs.recommended,

  // client-side scripts run in the browser; frontmatter runs in Node
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
  },

  // project rule tweaks
  {
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];
