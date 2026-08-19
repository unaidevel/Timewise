export default {
  extends: ["@commitlint/config-conventional"],
  prompt: {
    scopes: ["INFRA-0020"],   // Include project scopes
  },
};
