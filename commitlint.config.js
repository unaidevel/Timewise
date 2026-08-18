export default {
  extends: ["@commitlint/config-conventional"],
  prompt: {
    scopes: ["INFRA-0017"],   // Include project scopes
  },
};
