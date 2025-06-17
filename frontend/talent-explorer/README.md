# Talent Explorer Frontend

This is the Talent Explorer tab of the KnowThee Talent Intelligence Platform. It is a modern React + TypeScript app, styled with TailwindCSS, and built with Vite.

## Structure

```
frontend/
  talent-explorer/
    src/
      pages/
        TalentExplorer.tsx
      components/
        TalentTable.tsx
      hooks/
        useEmployees.ts
      services/
        api.ts
      types/
        employee.ts
      index.css
      main.tsx
    public/
      index.html
    package.json
    tailwind.config.js
    postcss.config.js
    tsconfig.json
    vite.config.ts
    Dockerfile
```

## Development (via Docker)

All dependencies are installed via Docker. Do **not** run `npm install` manually.

To build and run the app:

```
docker build -t talent-explorer .
docker run --rm -p 5173:5173 talent-explorer
```

The app will be available at http://localhost:5173

## Features
- Fetches employees from `/api/employees`
- Displays a table of employees
- Ready for further feature development

## Styling
- Uses TailwindCSS for all styling

## Notes
- This app is intended to be run as part of a larger docker-compose setup with the backend and database. 