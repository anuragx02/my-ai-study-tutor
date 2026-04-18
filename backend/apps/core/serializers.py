from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from backend.apps.core.models import (
    ChatMessage,
    ChatSession,
    Course,
    KnowledgeBase,
    Question,
    Quiz,
    StudyMaterial,
    StudyRecommendation,
    Topic,
    UserPerformance,
)

User = get_user_model()


class TopicSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "course", "course_title", "title", "difficulty"]


class CourseSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    topic_count = serializers.IntegerField(source="topics.count", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "created_by", "created_at", "topic_count", "topics"]
        read_only_fields = ["created_by", "created_at"]


class StudyMaterialSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)

    class Meta:
        model = StudyMaterial
        fields = ["id", "topic", "topic_title", "title", "material_type", "content_url", "summary", "created_at"]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "topic", "topic_title", "difficulty", "total_questions", "created_by", "created_at", "questions"]
        read_only_fields = ["created_by", "created_at"]


class UserPerformanceSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.topic.title", read_only=True)

    class Meta:
        model = UserPerformance
        fields = ["id", "user", "quiz", "quiz_title", "score", "attempt_date", "completion_time"]
        read_only_fields = ["id", "attempt_date"]


class QuizGenerateSerializer(serializers.Serializer):
    focus = serializers.CharField(max_length=255, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=Quiz.Difficulty.choices)
    total_questions = serializers.IntegerField(min_value=1, max_value=20, default=5)


class QuizSubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option = serializers.ChoiceField(choices=["A", "B", "C", "D"])


class QuizSubmitSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    completion_time = serializers.IntegerField(min_value=0, default=0)
    answers = QuizSubmitAnswerSerializer(many=True)


class ProgressSerializer(serializers.Serializer):
    quiz_score_trend = serializers.ListField(child=serializers.FloatField())
    accuracy = serializers.FloatField()
    weak_topics = serializers.ListField(child=serializers.CharField())
    study_time_minutes = serializers.IntegerField()


class StudyRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyRecommendation
        fields = ["id", "user", "topic", "suggested_material", "date_generated"]


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    session_id = serializers.IntegerField(required=False)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "text",
            "examples",
            "related_topics",
            "citations",
            "retrieval_confidence",
            "source_type",
            "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    last_message_preview = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "message_count", "last_message_preview"]

    def get_last_message_preview(self, obj):
        last_message = obj.messages.order_by("-created_at", "-id").first()
        if not last_message:
            return ""
        return (last_message.text or "")[:120]


class KnowledgeBaseUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            "id",
            "title",
            "file_type",
            "original_filename",
            "created_at",
            "updated_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["email"] = User.objects.normalize_email(validated_data["email"])
        validated_data["role"] = "student"
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_email(self, value):
        return User.objects.normalize_email(value)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "is_staff", "created_at"]
        read_only_fields = ["id", "email", "is_staff", "created_at"]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
