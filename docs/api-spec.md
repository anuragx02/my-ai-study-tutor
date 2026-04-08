# API Spec

## Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/profile`
- `PUT /api/auth/profile`

## Courses
- `GET /api/courses/`
- `POST /api/courses/`
- `GET /api/courses/topics`
- `POST /api/courses/topics`

## Materials
- `GET /api/materials/`
- `POST /api/materials/`

## AI Tutor
- `POST /api/ai/ask`

Request body:
```json
{
  "question": "Explain photosynthesis",
  "topic_id": 12
}
```

Response body:
```json
{
  "answer": "",
  "examples": [],
  "related_topics": []
}
```

## Quiz
- `GET /api/quiz/`
- `POST /api/quiz/generate`
- `POST /api/quiz/submit`

## Analytics
- `GET /api/analytics/progress`

## Recommendations
- `GET /api/recommendations/`
