# Architecture

AI Study Tutor uses a three-tier architecture.

## Presentation Layer
- React/Vite SPA built from `frontend/`
- Served by Django/WhiteNoise from `frontend/dist`
- Talks to the backend through Axios

## Application Layer
- Django REST Framework API
- JWT authentication for student users
- AI orchestration service in `apps/core/services/ai_service.py`

## Deployment Layer
- Single Render web service for the full app
- Django serves both the API and the React entrypoint

## Data Layer
- SQLite for development
- PostgreSQL for production on Render

## Main flows
- Students authenticate and access learning pages
- Course, topic, and material management is restricted to staff users
- Students ask the AI tutor questions and generate quizzes
- Analytics and recommendations are derived from quiz performance
