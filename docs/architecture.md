# Architecture

AI Study Tutor uses a three-tier architecture.

## Presentation Layer
- React/Vite frontend
- Talks to the backend through Axios

## Application Layer
- Django REST Framework API
- JWT authentication and role-based permissions
- AI orchestration service in `apps/core/services/ai_service.py`

## Data Layer
- SQLite for development
- PostgreSQL for production on Render

## Main flows
- Students authenticate and access learning pages
- Tutors and admins manage courses, topics, and materials
- Students ask the AI tutor questions and generate quizzes
- Analytics and recommendations are derived from quiz performance
