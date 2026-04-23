# API Spec

## Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `GET /api/auth/profile`
- `PUT /api/auth/profile`

## AI Tutor
- `POST /api/ai/ask`
- `GET /api/ai/sessions`
- `GET /api/ai/sessions/<session_id>`
- `DELETE /api/ai/sessions/<session_id>`
- `POST /api/ai/ocr`

Ask request body:
```json
{
  "question": "Explain photosynthesis",
  "image_context": "",
  "session_id": 1,
  "force_web": false
}
```

Ask response body:
```json
{
  "answer": "",
  "examples": [],
  "related_topics": [],
  "citations": [],
  "retrieval_confidence": 0,
  "source_type": "none",
  "session_id": 1
}
```

## Quiz
- `GET /api/quiz/`
- `POST /api/quiz/generate`
- `POST /api/quiz/submit`

Generate request body:
```json
{
  "focus": "Algebra",
  "difficulty": "easy",
  "total_questions": 5
}
```

Generate response body:
```json
{
  "id": 1,
  "focus": "Algebra",
  "difficulty": "easy",
  "total_questions": 5,
  "created_by": 1,
  "created_at": "2026-04-23T00:00:00Z",
  "questions": []
}
```

Submit request body:
```json
{
  "quiz_id": 1,
  "completion_time": 120,
  "answers": [
    { "question_id": 11, "selected_option": "A" }
  ]
}
```

## Analytics
- `GET /api/analytics/progress`
- `DELETE /api/analytics/history`

## Recommendations
- `GET /api/recommendations/`
