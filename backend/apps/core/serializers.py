from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from backend.apps.core.models import ChatMessage, ChatSession, Question, Quiz, Topic, UserPerformance
User = get_user_model()
class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "title", "difficulty"]
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "quiz", "question_text", "option_a", "option_b", "option_c", "option_d"]
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
        read_only_fields = ["attempt_date"]
class QuizGenerateSerializer(serializers.Serializer):
    focus = serializers.CharField(max_length=255, required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=Quiz.Difficulty.choices)
    total_questions = serializers.IntegerField(min_value=1, max_value=20, default=5)
class QuizSubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option = serializers.ChoiceField(choices=["A", "B", "C", "D"])
class QuizSubmitSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    completion_time = serializers.IntegerField(min_value=0)
    answers = QuizSubmitAnswerSerializer(many=True)
class ProgressSerializer(serializers.Serializer):
    quiz_score_trend = serializers.ListField(child=serializers.FloatField())
    accuracy = serializers.FloatField()
    study_time_minutes = serializers.IntegerField()
class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)
    image_context = serializers.CharField(required=False, allow_blank=True)
    session_id = serializers.IntegerField(required=False)
    force_web = serializers.BooleanField(default=False)
class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "text", "examples", "related_topics", "citations", "retrieval_confidence", "source_type", "created_at"]
class ChatSessionSerializer(serializers.ModelSerializer):
    last_message_preview = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "message_count", "last_message_preview"]

    def get_last_message_preview(self, obj):
        last_message = obj.messages.order_by("-created_at", "-id").first()
        return "" if not last_message else (last_message.text or "")[:120]
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "created_at"]
        read_only_fields = ["created_at"]

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
        user = authenticate(request=self.context.get("request"), email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        attrs["user"] = user
        return attrs
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "is_staff", "created_at"]
        read_only_fields = ["email", "is_staff", "created_at"]
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
class OCRSerializer(serializers.Serializer):
    image_url = serializers.CharField()
    instruction = serializers.CharField(max_length=2000, default="Extract all text from this image")
