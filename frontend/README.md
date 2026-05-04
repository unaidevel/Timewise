# Frontend

React + TypeScript SPA for the TimeWise platform.

## Stack

| | |
|---|---|
| Framework | React 19 |
| Language | TypeScript 6 |
| Bundler | Vite |
| Package manager | pnpm |
| API client | @hey-api/openapi-ts (auto-generated) |

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
| `pnpm lint` | Run Biome — reports warnings and errors |
| `pnpm lint:fix` | Run Biome and auto-fix safe issues |
| `pnpm format` | Format all files with Biome |
| `pnpm generate-client` | Regenerate API client from live backend schema |

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

## Project structure

```
frontend/
├── src/
│   ├── client/       # Auto-generated API client (do not edit)
│   └── ...           # App code
├── package.json
└── vite.config.ts
```
