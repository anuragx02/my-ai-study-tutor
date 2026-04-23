import pytest
from rest_framework.test import APIClient

from backend.apps.core.models import Question, Quiz, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="student@example.com",
        password="test-password-123",
        name="Student",
    )


@pytest.mark.django_db
def test_generate_quiz_uses_focus_without_existing_topic(api_client, user, monkeypatch):
    api_client.force_authenticate(user=user)

    def fake_generate_quiz(focus, difficulty, total_questions):
        return {
            "focus": focus,
            "difficulty": difficulty,
            "total_questions": total_questions,
            "questions": [
                {
                    "question_text": "What is 2 + 2?",
                    "option_a": "3",
                    "option_b": "4",
                    "option_c": "5",
                    "option_d": "6",
                    "correct_option": "B",
                }
            ],
        }

    monkeypatch.setattr("backend.apps.core.views.generate_ai_quiz", fake_generate_quiz)

    response = api_client.post(
        "/api/quiz/generate",
        {"focus": "Arithmetic", "difficulty": "easy", "total_questions": 1},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["focus"] == "Arithmetic"
    assert Quiz.objects.get(id=response.data["id"]).focus == "Arithmetic"


@pytest.mark.django_db
def test_recommendations_use_quiz_focus_for_weak_areas(api_client, user, monkeypatch):
    api_client.force_authenticate(user=user)
    monkeypatch.setattr("backend.apps.core.views.generate_answer_explanation", lambda **kwargs: "")

    quiz = Quiz.objects.create(
        focus="Geometry",
        difficulty=Quiz.Difficulty.EASY,
        total_questions=1,
        created_by=user,
    )
    question = Question.objects.create(
        quiz=quiz,
        question_text="How many degrees are in a right angle?",
        option_a="45",
        option_b="90",
        option_c="180",
        option_d="360",
        correct_option="B",
    )

    submit_response = api_client.post(
        "/api/quiz/submit",
        {
            "quiz_id": quiz.id,
            "completion_time": 30,
            "answers": [{"question_id": question.id, "selected_option": "A"}],
        },
        format="json",
    )
    recommendations_response = api_client.get("/api/recommendations/")

    assert submit_response.status_code == 201
    assert submit_response.data["score"] == 0
    assert recommendations_response.status_code == 200
    assert recommendations_response.data[0]["topic"] == "Geometry"
