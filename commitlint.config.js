export default {
  extends: ["@commitlint/config-conventional"],
  prompt: {
    scopes: ["INFRA-0010"],   // Include project scopes
  },
};
