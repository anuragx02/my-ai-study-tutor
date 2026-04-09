from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from backend.apps.core.models import (
    Course,
    KnowledgeChunk,
    KnowledgeDocument,
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
    topic_id = serializers.IntegerField(required=True)
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
    topic_id = serializers.IntegerField(required=False, allow_null=True)


class KnowledgeDocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeChunk
        fields = ["id", "chunk_index", "content", "created_at"]


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(source="chunks.count", read_only=True)

    class Meta:
        model = KnowledgeDocument
        fields = [
            "id",
            "title",
            "source_type",
            "tags",
            "original_filename",
            "status",
            "error_message",
            "chunk_count",
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
