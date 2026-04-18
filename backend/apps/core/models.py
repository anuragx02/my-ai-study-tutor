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


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        db_table = "courses_course"

    def __str__(self):
        return self.title


class Topic(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.EASY)

    class Meta:
        ordering = ["course", "title"]
        db_table = "courses_topic"

    def __str__(self):
        return self.title


class StudyMaterial(models.Model):
    class MaterialType(models.TextChoices):
        PDF = "pdf", "PDF"
        VIDEO = "video", "Video"
        NOTES = "notes", "Notes"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices)
    content_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        db_table = "materials_studymaterial"

    def __str__(self) -> str:
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


class StudyRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="recommendations")
    suggested_material = models.CharField(max_length=255)
    date_generated = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendations_studyrecommendation"


class KnowledgeBase(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        TXT = "txt", "TXT"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_bases")
    title = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    original_filename = models.CharField(max_length=255)
    file_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "kb_knowledge_base"
        verbose_name_plural = "Knowledge Bases"


class KnowledgeBaseChunk(models.Model):
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    chunk_text = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "kb_knowledge_base_chunk"
        ordering = ["knowledge_base_id", "chunk_index"]
        unique_together = ("knowledge_base", "chunk_index")


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
        KB = "kb", "Knowledge Base"
        WEB = "web", "Web"
        MIXED = "mixed", "Mixed"

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