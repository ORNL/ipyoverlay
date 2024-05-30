module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
  },
  extends: [
    // add more generic rulesets here, such as:
    "eslint:recommended",
    "plugin:vue/essential",
    "plugin:vue/base",
    "plugin:vue/recommended", // Use this if you are using Vue.js 2.x.
    "plugin:jsdoc/recommended"
  ],
  rules: {
    // override/add rules settings here, such as:
    // 'vue/no-unused-vars': 'error'
    "vue/no-side-effects-in-computed-properties": "warn",
    "vue/html-indent": ["error", 2],
    "vue/no-v-html": ["off"],
    "vue/max-attributes-per-line": ["error", {"singleline": { "max": 4 }}],
    "vue/singleline-html-element-content-newline": ["off"],
    "vue/valid-v-slot": ["off"],
    "vue/valid-v-for": ["off"],
    "vue/require-v-for-key": ["off"],
    "vue/no-use-v-if-with-v-for": ["off"],
    "vue/multi-word-component-names": ["off"],
    indent: ["error", 2],
    "brace-style": ["error", "stroustrup", { allowSingleLine: true }],
    "block-spacing": ["error", "always"],
    camelcase: ["warn"],
    "comma-spacing": ["error", { before: false, after: true }],
    "comma-style": ["error", "last"],
    "func-call-spacing": ["error", "never"],
    "key-spacing": ["error", { beforeColon: false, afterColon: true }],
    "no-trailing-spaces": ["error"],
    "no-multiple-empty-lines": ["error", { "max": 2 }],
    quotes: ["error", "double"],
    eqeqeq: ["error"],
    semi: ["error", "always"],
    //"newline-per-chained-call": ["warn", { ignoreChainWithDepth: 4 }],
  },
};
