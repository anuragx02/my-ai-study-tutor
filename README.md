# AI Study Tutor

AI Study Tutor is a three-tier learning platform with a Django REST API, a React/Vite frontend, and PostgreSQL for production.

Groq powers the AI tutor and quiz generation layer when `GROQ_API_KEY` is configured.

## Architecture
- Presentation layer: React SPA in `frontend/`, served from Django in production
- Application layer: Django REST API in `backend/`
- Data layer: SQLite locally, PostgreSQL in production

## Local setup
1. Create a Python virtual environment at the project root: `.venv`.
2. Install backend dependencies from root: `./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt`.
3. Install frontend dependencies from root: `npm --prefix frontend install`.
4. Copy `backend/.env` values as needed for your local environment.

## Run From Project Root (No cd)
Use these commands from the repository root:

```bash
npm run dev
```

- Starts backend in a separate PowerShell window.
- Starts frontend in the current terminal.

```bash
npm run backend
npm run frontend
npm run build
```

- `npm run backend`: Django dev server.
- `npm run frontend`: Vite dev server.
- `npm run build`: Frontend production build.
- `npm run migrate`: Apply Django migrations.

## Deploy on Render
This project is configured to run on Render without Docker.

### Single Web Service
- Root Directory: repository root
- Build Command: `npm --prefix frontend install && npm run build && pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start Command: `python manage.py migrate && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT`

Required environment variables:
- `DEBUG=False`
- `SECRET_KEY=<your-secret>`
- `DATABASE_URL=<render-postgres-url>`
- `ALLOWED_HOSTS=<your-render-domain>`
- `CORS_ALLOWED_ORIGINS=https://<your-render-domain>`
- `CSRF_TRUSTED_ORIGINS=https://<your-render-domain>`
- `GROQ_API_KEY=<your-groq-key>`
- `GROQ_API_BASE=https://api.groq.com`
- `GROQ_MODEL=llama-3.3-70b-versatile`

The React app is built into `frontend/dist` and served by Django/WhiteNoise.

## Root-only Workflow
No directory switching is required for day-to-day development.

```bash
npm run migrate
npm run backend
npm run frontend
```

The root `manage.py` is the Django entrypoint; it loads the `backend/` package path automatically.

## API endpoints
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/profile`
- `PUT /api/auth/profile`
- `POST /api/ai/ask`
- `POST /api/quiz/generate`
- `POST /api/quiz/submit`
- `GET /api/analytics/progress`
- `GET /api/recommendations/`

### Example quiz submit body
```json
{
	"quiz_id": 1,
	"completion_time": 120,
	"answers": [
		{ "question_id": 11, "selected_option": "A" }
	]
}
```

## Notes
The backend has been consolidated into `apps/core`, and the React frontend is the active UI.
