from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.apps.core.managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default="student", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["-created_at"]
        db_table = "users_user"

    def __str__(self):
        return self.email


class Topic(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.EASY)

    class Meta:
        ordering = ["user", "title"]
        db_table = "courses_topic"

    def __str__(self):
        return self.title


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="quizzes")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    total_questions = models.PositiveIntegerField(default=5)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "quiz_quiz"

    def __str__(self) -> str:
        return f"{self.topic.title} - {self.difficulty}"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1)

    class Meta:
        ordering = ["id"]
        db_table = "quiz_question"


class UserPerformance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="performances")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="performances")
    score = models.FloatField(default=0)
    attempt_date = models.DateTimeField(auto_now_add=True)
    completion_time = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-attempt_date"]
        db_table = "quiz_userperformance"


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "chat_session"

    def __str__(self) -> str:
        return f"{self.user.email}: {self.title}"


class ChatMessage(models.Model):
    class SourceType(models.TextChoices):
        NONE = "none", "None"
        WEB = "web", "Web"

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    text = models.TextField()
    examples = models.JSONField(default=list, blank=True)
    related_topics = models.JSONField(default=list, blank=True)
    citations = models.JSONField(default=list, blank=True)
    retrieval_confidence = models.FloatField(null=True, blank=True)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.NONE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        db_table = "chat_message"