# Getting Started — Frontend

## Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/)

## Local setup

```bash
cd frontend
pnpm install
pnpm dev
```

The app is available at `http://localhost:3000`. The backend must be running for API calls to work — see [Backend Getting Started](../backend/getting-started.md).

## Testing

Tests are co-located with the source they cover.

```bash
pnpm test          # run all tests once
pnpm test:watch    # watch mode
```

The test setup uses:

- **Vitest** as the test runner
- **Testing Library** for DOM assertions and user interaction
- **MSW** (Mock Service Worker in Node mode) to intercept fetch calls at the network level
- **`createRouterWrapper()`** — helper that wraps components in `QueryClientProvider` + `MemoryRouter` with a fresh, no-retry `QueryClient` per test

## Regenerating the API client

The backend must be running first:

```bash
# from the project root
docker compose up -d

# then from frontend/
pnpm generate-client
```

This overwrites `src/client/`. Commit the result alongside any backend changes that triggered it.
