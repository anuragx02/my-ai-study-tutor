import pytest
from rest_framework.test import APIClient

from backend.apps.core.models import ChatMessage, User
from backend.apps.core.services.ai_service import AIResponse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="chat-student@example.com",
        password="test-password-123",
        name="Chat Student",
    )


@pytest.mark.django_db
def test_normal_chat_accepts_plain_text_ai_response(api_client, user, monkeypatch):
    api_client.force_authenticate(user=user)
    monkeypatch.setattr(
        "backend.apps.core.views.ask_ai",
        lambda *args, **kwargs: AIResponse(answer="Photosynthesis converts light into chemical energy.", examples=[], related_topics=[]),
    )

    response = api_client.post("/api/ai/ask", {"question": "Explain photosynthesis"}, format="json")

    assert response.status_code == 200
    assert response.data["answer"] == "Photosynthesis converts light into chemical energy."
    assert ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT, text=response.data["answer"]).exists()


@pytest.mark.django_db
def test_image_only_chat_request_is_accepted(api_client, user, monkeypatch):
    api_client.force_authenticate(user=user)
    monkeypatch.setattr(
        "backend.apps.core.views.ask_ai",
        lambda *args, **kwargs: AIResponse(answer="The image shows a quadratic equation.", examples=[], related_topics=[]),
    )

    response = api_client.post("/api/ai/ask", {"question": "", "image_context": "x^2 + 5x + 6 = 0"}, format="json")

    assert response.status_code == 200
    assert response.data["answer"] == "The image shows a quadratic equation."
    assert ChatMessage.objects.filter(role=ChatMessage.Role.USER, text="Image attached").exists()


@pytest.mark.django_db
def test_empty_chat_request_is_rejected(api_client, user):
    api_client.force_authenticate(user=user)

    response = api_client.post("/api/ai/ask", {"question": ""}, format="json")

    assert response.status_code == 400
    assert str(response.data["detail"][0]) == "Ask a question or attach an image."
