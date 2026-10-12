# Grazer Gemeinderat Suche – Web

A German-language search interface for the Graz City Council document
archive. It is a React Router app in SPA mode (no server-side rendering)
that calls the [Flask search API](../api/README.md) directly from the
browser and renders results, including highlighted snippets, sorting, date
filtering, and pagination.

## Features

- 🖥️ Client-side rendered SPA (search requests are made from the browser
  via a `clientLoader`, so the Flask API must have CORS enabled — see
  [`api/README.md`](../api/README.md#cors))
- 🔍 Full-text search backed by the API's `/search` endpoint, with sorting
  (`relevance`, `date_asc`, `date_desc`) and an optional date range
- ♿ Accessible, keyboard-operable UI: semantic landmarks, a skip link,
  labelled form controls, `role="search"`/`role="alert"`/`role="status"`,
  and visible focus indicators
- 📱 Responsive layout that works from small phones to desktop
- 🇦🇹 Graz/Styria-themed design (green palette, an original Uhrturm/clock
  tower pictogram) with German-language copy throughout
- 🔒 TypeScript by default
- 🎉 TailwindCSS for styling

## Configuration

The app talks to the Flask API configured in [`api/`](../api). Set the
`VITE_API_BASE_URL` environment variable at build time to point at it; it
defaults to `http://127.0.0.1:5000` when unset. Since this is a client-side
rendered SPA, the value is baked into the client bundle (it is not a secret,
and must not be used to pass sensitive configuration):

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:5000"
```

## Getting Started

### Installation

Install the dependencies:

```bash
npm install
```

### Development

Start the API (see [`api/README.md`](../api/README.md)), then start the web
development server with HMR:

```bash
npm run dev
```

Your application will be available at `http://localhost:5173`.

### Type checking

```bash
npm run typecheck
```

## Building for Production

Create a production build:

```bash
npm run build
```

## Deployment

### Docker Deployment

To build and run using Docker. Because this is now a client-side rendered
SPA, the API base URL is baked into the bundle at **build time** via the
`VITE_API_BASE_URL` build argument (a runtime `-e` flag no longer has any
effect, since there's no server-side code reading it):

```bash
docker build -t graz-council-web \
  --build-arg VITE_API_BASE_URL=http://host.docker.internal:5000 .

docker run -p 3000:3000 graz-council-web
```

The containerized application can be deployed to any platform that supports
Docker, including:

- AWS ECS
- Google Cloud Run
- Azure Container Apps
- Digital Ocean App Platform
- Fly.io
- Railway

### DIY Deployment

If you're familiar with deploying Node applications, the built-in app server
is production-ready.

Make sure to deploy the output of `npm run build`

```
├── package.json
├── package-lock.json (or pnpm-lock.yaml, or bun.lockb)
├── build/
│   ├── client/    # Static assets
│   └── server/    # Server-side code
```

## Project layout

```text
app/
├── components/        # SearchForm, SearchResults, SiteHeader, SiteFooter, icons
├── lib/
│   ├── search.ts       # Shared types/constants (client-safe)
│   └── search-api.ts   # Client-side fetch call to the Flask API
├── routes/
│   ├── home.tsx          # clientLoader + search page
│   ├── datenschutz.tsx   # Datenschutzerklärung (GDPR declaration)
│   └── impressum.tsx     # Impressum (legal notice)
├── root.tsx
└── app.css
```

The `datenschutz.tsx` and `impressum.tsx` routes are placeholders with an
empty `<article>`; fill in the legal text directly in those files.

## Styling

This app uses [Tailwind CSS](https://tailwindcss.com/) for styling.

---

Built with ❤️ using React Router.

