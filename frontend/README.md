# Frontend

React + TypeScript SPA for the TimeWise platform.

## Stack

| | |
|---|---|
| Framework | React 19 |
| Language | TypeScript 6 |
| Bundler | Vite 8 |
| Package manager | pnpm |
| Routing | React Router 7 |
| Server state | TanStack Query v5 |
| Client state | Zustand |
| UI components | shadcn/ui + Radix primitives |
| Styling | Tailwind CSS v4 |
| API client | @hey-api/openapi-ts (auto-generated) |
| Linting / formatting | Biome |
| Testing | Vitest + Testing Library + MSW |

## Getting started

```bash
pnpm install
pnpm dev          # http://localhost:3000
```

## Commands

| Command | Description |
|---|---|
| `pnpm dev` | Start dev server at http://localhost:3000 |
| `pnpm build` | Type-check and produce production bundle |
| `pnpm preview` | Serve the production bundle locally |
| `pnpm test` | Run all tests once |
| `pnpm test:watch` | Run tests in watch mode |
| `pnpm lint` | Run Biome — reports warnings and errors |
| `pnpm lint:fix` | Run Biome and auto-fix safe issues |
| `pnpm format` | Format all files with Biome |
| `pnpm generate-client` | Regenerate API client from live backend schema |

## Features

- **Employees** — searchable table with status filter, slide-over detail sheet, and inline create form
- **Time reports** — cross-period list with search and status filter
- **Approvals** — tabbed inbox (pending / approved / rejected) with inline approve and reject actions
- **Command palette** — ⌘K / Ctrl+K global search wired to real employee data and navigation shortcuts
- **Empty state** — reusable component with optional action slot used across all pages

## API client

The API client is auto-generated from the FastAPI OpenAPI schema. Import from `src/client/`:

```ts
import { getEmployee, createTimeReport } from "@/client";

const { data } = await getEmployee({
  path: { tenant_id: "abc", employee_id: "xyz" },
});
```

<details>
<summary>How the generation works</summary>

FastAPI automatically publishes its full OpenAPI schema at `/openapi.json`. The `@hey-api/openapi-ts` tool reads that schema and generates three things into `src/client/`:

- **`types.gen.ts`** — TypeScript interfaces for every request body and response, derived directly from the Python Pydantic models.
- **`sdk.gen.ts`** — One typed async function per endpoint. Each function accepts a structured `{ path, query, body }` argument instead of raw strings.
- **`client.ts`** — The underlying fetch wrapper (configurable base URL, auth headers, etc.).

If a backend schema changes (a field is renamed, a new endpoint is added, a response type changes), running the generator again will surface the mismatch as a TypeScript compile error — the contract between backend and frontend is enforced at build time, not at runtime.

### Regenerating the client

The backend must be running first:

```bash
# from the project root
docker compose up -d

# then from frontend/
pnpm generate-client
```

This overwrites `src/client/`. Commit the result alongside any backend changes that triggered it.

### What goes in src/client/ vs what you write yourself

`src/client/` is fully generated — never edit it by hand. Write your own data-fetching hooks, query wrappers (e.g. React Query), or state slices on top of the generated functions.

</details>

## Testing

Tests are co-located with the source they cover. The setup uses:

- **Vitest** as the test runner
- **Testing Library** (`@testing-library/react`, `@testing-library/user-event`) for DOM assertions and user interaction
- **MSW** (Mock Service Worker in Node mode) to intercept real fetch calls at the network level — no mocking of hooks or modules
- **`createRouterWrapper()`** — test helper that wraps a component in `QueryClientProvider` + `MemoryRouter` with a fresh, no-retry `QueryClient` per test

```bash
pnpm test          # run all tests
pnpm test:watch    # watch mode
```

## Project structure

```
frontend/
├── src/
│   ├── app/              # Root layout, router
│   ├── client/           # Auto-generated API client (do not edit)
│   ├── components/       # Shared UI components
│   │   └── shadcn/       # Radix-based primitives (button, dialog, sheet, …)
│   ├── features/
│   │   ├── approvals/
│   │   ├── employees/
│   │   ├── tenants/
│   │   └── time-reports/
│   └── test/             # MSW server + test wrapper helpers
├── package.json
└── vite.config.ts
```
