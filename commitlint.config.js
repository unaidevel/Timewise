export default {
  extends: ["@commitlint/config-conventional"],
  prompt: {
    scopes: ["INFRA-0025"],   // Include project scopes
  },
};
