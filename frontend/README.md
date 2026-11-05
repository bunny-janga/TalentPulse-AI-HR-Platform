# TalentPulse AI — frontend

React 18 + plain JavaScript + hand-written CSS. Vite is used only as a bundler.
Runtime dependencies: `react`, `react-dom`. Nothing else.

## Commands

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, API calls proxied to http://127.0.0.1:8000
npm run build    # writes index.html + hashed assets into ../backend/static
```

Start the backend with `uvicorn app.main:app --reload` from `backend/`, then open `http://127.0.0.1:8000/ui`.

> `npm run build` empties `backend/static` (it replaces the old `index.html`, `app.js`, `style.css`).
> Back that folder up first if you want to keep the legacy UI.

(The full README with design decisions, motion/3D techniques and reduced-motion behaviour is completed in the final part.)
