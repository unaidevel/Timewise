# Frontend Overview

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

## Project structure

```
frontend/
├── src/
│   ├── app/              # Root layout, router
│   ├── client/           # Auto-generated API client (do not edit)
│   ├── components/       # Shared UI components
│   │   └── shadcn/       # Radix-based primitives
│   ├── features/
│   │   ├── approvals/
│   │   ├── employees/
│   │   ├── tenants/
│   │   └── time-reports/
│   └── test/             # MSW server + test wrapper helpers
├── package.json
└── vite.config.ts
```

## API client

The client is auto-generated from the FastAPI OpenAPI schema. Import directly from `src/client/`:

```ts
import { getEmployee, createTimeReport } from "@/client";

const { data } = await getEmployee({
  path: { tenant_id: "abc", employee_id: "xyz" },
});
```

Never edit `src/client/` by hand — regenerate it with `pnpm generate-client` when the backend schema changes. This surfaces contract mismatches as TypeScript compile errors at build time.
