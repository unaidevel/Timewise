export default {
  extends: ["@commitlint/config-conventional"],
  prompt: {
    scopes: ["INFRA-0015"],   // Include project scopes
  },
};
