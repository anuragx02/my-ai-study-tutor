from collections import Counter
from pathlib import Path

from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.core.models import (
    Course,
    KnowledgeBase,
    Question,
    Quiz,
    StudyMaterial,
    StudyRecommendation,
    Topic,
    UserPerformance,
)
from backend.apps.core.permissions import IsStaffUser
from backend.apps.core.serializers import (
    AskSerializer,
    CourseSerializer,
    KnowledgeBaseSerializer,
    KnowledgeBaseUploadSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    QuizGenerateSerializer,
    QuizSerializer,
    QuizSubmitSerializer,
    StudyMaterialSerializer,
    TopicSerializer,
    UserPerformanceSerializer,
    UserSerializer,
)
from backend.apps.core.services.ai_service import ask_ai, generate_quiz as generate_ai_quiz

from pypdf import PdfReader


def _detect_file_type(filename: str) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension in {"pdf", "txt"}:
        return extension
    raise ValueError("Unsupported file type. Allowed types: PDF, TXT.")


def _extract_text_from_file(uploaded_file, file_type: str) -> str:
    if file_type == "txt":
        return uploaded_file.read().decode("utf-8", errors="ignore")

    if file_type == "pdf":
        reader = PdfReader(uploaded_file)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    raise ValueError(f"Unsupported file type: {file_type}")


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": ProfileSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": ProfileSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            refresh.blacklist()
        except TokenError:
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.select_related("created_by").prefetch_related("topics")
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [IsAuthenticated(), IsStaffUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TopicListCreateView(generics.ListCreateAPIView):
    queryset = Topic.objects.select_related("course")
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]


class StudyMaterialListCreateView(generics.ListCreateAPIView):
    queryset = StudyMaterial.objects.select_related("topic")
    serializer_class = StudyMaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [IsAuthenticated(), IsStaffUser()]
        return super().get_permissions()


class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuizGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = get_object_or_404(Topic.objects.select_related("course"), pk=serializer.validated_data["topic_id"])
        difficulty = serializer.validated_data["difficulty"]
        total_questions = serializer.validated_data["total_questions"]
        payload = generate_ai_quiz(topic=topic.title, difficulty=difficulty, total_questions=total_questions)

        quiz = Quiz.objects.create(
            topic=topic,
            difficulty=difficulty,
            total_questions=total_questions,
            created_by=request.user,
        )

        for item in payload["questions"]:
            Question.objects.create(quiz=quiz, **item)

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizSubmitView(generics.CreateAPIView):
    serializer_class = UserPerformanceSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quiz = get_object_or_404(Quiz.objects.prefetch_related("questions"), pk=serializer.validated_data["quiz_id"])
        questions = list(quiz.questions.all())
        answer_map = {
            answer["question_id"]: answer["selected_option"]
            for answer in serializer.validated_data["answers"]
        }

        correct_count = 0
        incorrect_questions = []
        for question in questions:
            selected_option = answer_map.get(question.id)
            if selected_option == question.correct_option:
                correct_count += 1
            else:
                incorrect_questions.append(
                    {
                        "question_id": question.id,
                        "topic": quiz.topic.title,
                    }
                )

        total_questions = len(questions) or 1
        score = round((correct_count / total_questions) * 100, 2)
        performance = UserPerformance.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            completion_time=serializer.validated_data["completion_time"],
        )

        return Response(
            {
                "performance": UserPerformanceSerializer(performance).data,
                "score": score,
                "accuracy": score,
                "correct_count": correct_count,
                "incorrect_count": len(incorrect_questions),
                "weak_topics": sorted({item["topic"] for item in incorrect_questions}),
                "incorrect_questions": incorrect_questions,
            },
            status=status.HTTP_201_CREATED,
        )


class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.select_related("topic", "created_by").prefetch_related("questions")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]


class AskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic_context = None
        topic_id = serializer.validated_data.get("topic_id")
        if topic_id:
            topic = get_object_or_404(Topic.objects.select_related("course").prefetch_related("materials"), pk=topic_id)
            material_summaries = [material.summary or material.title for material in topic.materials.all()[:5]]
            topic_context = f"{topic.course.title} > {topic.title}. Materials: {' | '.join(material_summaries)}"

        question_text = serializer.validated_data["question"]
        kb_hits = KnowledgeBase.objects.filter(user=request.user, file_text__icontains=question_text[:40])[:3]
        if kb_hits:
            kb_context = "\n".join(
                f"[{item.title}] {item.file_text[:500]}"
                for item in kb_hits
            )
            topic_context = f"{topic_context or 'knowledge base context'}\nKB:\n{kb_context}"

        result = ask_ai(question_text, topic_context=topic_context)
        return Response(
            {
                "answer": result.answer,
                "examples": result.examples,
                "related_topics": result.related_topics,
            },
            status=status.HTTP_200_OK,
        )


class KnowledgeBaseListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        documents = KnowledgeBase.objects.filter(user=request.user)
        return Response(KnowledgeBaseSerializer(documents, many=True).data)

    def post(self, request):
        serializer = KnowledgeBaseUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        title = serializer.validated_data.get("title") or uploaded_file.name

        try:
            file_type = _detect_file_type(uploaded_file.name)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_text = _extract_text_from_file(uploaded_file, file_type)
        except Exception as exc:
            return Response({"detail": f"Failed to extract text: {str(exc)}"}, status=status.HTTP_400_BAD_REQUEST)

        kb = KnowledgeBase.objects.create(
            user=request.user,
            title=title,
            file_type=file_type,
            original_filename=uploaded_file.name,
            file_text=file_text,
        )

        return Response(KnowledgeBaseSerializer(kb).data, status=status.HTTP_201_CREATED)


class KnowledgeBaseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, document_id):
        document = get_object_or_404(KnowledgeBase, id=document_id, user=request.user)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class KnowledgeBasePurgeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = KnowledgeBase.objects.filter(user=request.user).delete()
        return Response({"deleted_documents": deleted_count}, status=status.HTTP_200_OK)


class ProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        performances = UserPerformance.objects.select_related("quiz__topic").filter(user=request.user)
        score_values = list(performances.values_list("score", flat=True))
        weak_topics_counter = Counter()
        for performance in performances:
            if performance.score < 70:
                weak_topics_counter[performance.quiz.topic.title] += 1

        return Response(
            {
                "quiz_score_trend": score_values[-5:],
                "accuracy": round(performances.aggregate(avg=Avg("score"))["avg"] or 0, 2),
                "weak_topics": [topic for topic, _ in weak_topics_counter.most_common(5)],
                "study_time_minutes": int(performances.aggregate(total=Sum("completion_time"))["total"] or 0),
            }
        )


class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        performances = UserPerformance.objects.select_related("quiz__topic").filter(user=request.user)
        weak_topics = []
        for performance in performances:
            if performance.score < 70:
                weak_topics.append(performance.quiz.topic)

        if not weak_topics:
            weak_topics = list(Topic.objects.order_by("title")[:3])

        recommendations = []
        for topic in weak_topics[:5]:
            recommendation, _ = StudyRecommendation.objects.get_or_create(
                user=request.user,
                topic=topic,
                defaults={
                    "suggested_material": f"Review {topic.title} lessons and complete practice questions.",
                    "date_generated": timezone.now(),
                },
            )
            recommendations.append(
                {
                    "id": recommendation.id,
                    "topic": topic.title,
                    "suggested_material": recommendation.suggested_material,
                    "date_generated": recommendation.date_generated.isoformat().replace("+00:00", "Z"),
                }
            )

        return Response(recommendations)
