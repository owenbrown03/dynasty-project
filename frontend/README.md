# Dynasty Base frontend

This frontend is a React + TypeScript + Vite application for Dynasty Base.

Core structure:

- [src/pages](/Users/owen/Code/dynasty/project/frontend/src/pages) for route-level composition
- [src/components](/Users/owen/Code/dynasty/project/frontend/src/components) for reusable UI
- [src/hooks](/Users/owen/Code/dynasty/project/frontend/src/hooks) for query and mutation hooks
- [src/api/v1](/Users/owen/Code/dynasty/project/frontend/src/api/v1) for typed endpoint wrappers
- [src/context](/Users/owen/Code/dynasty/project/frontend/src/context) for bootstrap, auth, and theme state

## Development

Install dependencies:

```sh
npm install
```

Run the dev server:

```sh
npm run dev
```

API base URL configuration:

```sh
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

If `VITE_API_BASE_URL` is omitted, the frontend defaults to:

- `http://localhost:8000/api/v1` during localhost development
- `/api/v1` in non-localhost environments

Build for production:

```sh
npm run build
```

Preview the build:

```sh
npm run preview
```

## Verification

Lint:

```sh
npm run lint
```

Unit tests:

```sh
npm run test
```

## Repository-specific conventions

- Keep server state in TanStack Query hooks.
- Do not call Axios directly from page components.
- Use the existing bootstrap/auth/theme contexts instead of introducing parallel app state.
- Keep route pages focused on composition; move request logic into hooks and reusable components.
- Follow existing compact, data-dense UI patterns rather than introducing a separate design system.
