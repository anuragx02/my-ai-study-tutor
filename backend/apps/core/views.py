from collections import Counter
from pathlib import Path

from django.conf import settings
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
    ChatMessage,
    ChatSession,
    Course,
    KnowledgeBase,
    Question,
    Quiz,
    StudyMaterial,
    Topic,
    UserPerformance,
)
from backend.apps.core.permissions import IsStaffUser
from backend.apps.core.serializers import (
    AskSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
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
from backend.apps.core.services.ai_service import ask_ai, generate_chat_title, generate_quiz as generate_ai_quiz
from backend.apps.core.services.chunk_service import sync_document_chunks
from backend.apps.core.services.retrieval_service import retrieve_context

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


def _normalize_quiz_option(value: str | None) -> str | None:
    if not value:
        return None

    normalized = str(value).strip().upper()
    if normalized in {"A", "B", "C", "D"}:
        return normalized

    compact = normalized.replace(" ", "")
    mappings = {
        "OPTIONA": "A",
        "OPTIONB": "B",
        "OPTIONC": "C",
        "OPTIOND": "D",
        "A)": "A",
        "B)": "B",
        "C)": "C",
        "D)": "D",
        "A.": "A",
        "B.": "B",
        "C.": "C",
        "D.": "D",
    }
    if compact in mappings:
        return mappings[compact]

    if compact.startswith("OPTION") and len(compact) > 6 and compact[6] in {"A", "B", "C", "D"}:
        return compact[6]

    if compact and compact[0] in {"A", "B", "C", "D"}:
        return compact[0]

    return None


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
        difficulty = serializer.validated_data["difficulty"]
        total_questions = serializer.validated_data["total_questions"]

        focus = serializer.validated_data.get("focus", "").strip()
        kb_seed = " ".join(
            KnowledgeBase.objects.filter(user=request.user).values_list("title", flat=True)[:5]
        )
        quiz_topic = focus or kb_seed or "General Study"
        payload = generate_ai_quiz(topic=quiz_topic, difficulty=difficulty, total_questions=total_questions)

        fallback_topic = Topic.objects.order_by("id").first()
        if not fallback_topic:
            fallback_course, _ = Course.objects.get_or_create(
                title="General Study",
                defaults={
                    "description": "Auto-created course for KB-first quiz generation.",
                    "created_by": request.user,
                },
            )
            fallback_topic, _ = Topic.objects.get_or_create(
                course=fallback_course,
                title="General Practice",
                defaults={"difficulty": Topic.Difficulty.EASY},
            )

        quiz = Quiz.objects.create(
            topic=fallback_topic,
            difficulty=difficulty,
            total_questions=total_questions,
            created_by=request.user,
        )

        for item in payload["questions"]:
            normalized_correct_option = _normalize_quiz_option(item.get("correct_option")) or "A"
            Question.objects.create(
                quiz=quiz,
                question_text=item["question_text"],
                option_a=item["option_a"],
                option_b=item["option_b"],
                option_c=item["option_c"],
                option_d=item["option_d"],
                correct_option=normalized_correct_option,
            )

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
            answer["question_id"]: _normalize_quiz_option(answer["selected_option"])
            for answer in serializer.validated_data["answers"]
        }

        correct_count = 0
        incorrect_questions = []
        for question in questions:
            selected_option = answer_map.get(question.id)
            correct_option = _normalize_quiz_option(question.correct_option)
            if selected_option and correct_option and selected_option == correct_option:
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
        question_text = serializer.validated_data["question"]
        session_id = serializer.validated_data.get("session_id")

        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=generate_chat_title(question_text),
            )

        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            text=question_text,
        )

        retrieval = retrieve_context(question=question_text, user=request.user)
        is_academic = bool(retrieval.context or retrieval.source_type in {"kb", "web", "mixed"})
        result = ask_ai(question_text, topic_context=retrieval.context, is_academic=is_academic)
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            text=result.answer,
            examples=result.examples,
            related_topics=result.related_topics,
            citations=retrieval.citations,
            retrieval_confidence=retrieval.confidence,
            source_type=retrieval.source_type,
        )
        return Response(
            {
                "answer": result.answer,
                "examples": result.examples,
                "related_topics": result.related_topics,
                "citations": retrieval.citations,
                "retrieval_confidence": retrieval.confidence,
                "source_type": retrieval.source_type,
                "fallback_used": retrieval.fallback_used,
                "session_id": session.id,
            },
            status=status.HTTP_200_OK,
        )


class ChatSessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user).prefetch_related("messages")
        return Response(ChatSessionSerializer(sessions, many=True).data, status=status.HTTP_200_OK)


class ChatSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession.objects.prefetch_related("messages"), id=session_id, user=request.user)
        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "messages": ChatMessageSerializer(session.messages.all(), many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        sync_document_chunks(
            kb,
            chunk_size_chars=getattr(settings, "KB_CHUNK_SIZE_CHARS", 1200),
            overlap_chars=getattr(settings, "KB_CHUNK_OVERLAP_CHARS", 200),
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
        performances = (
            UserPerformance.objects.select_related("quiz__topic")
            .filter(user=request.user)
            .order_by("attempt_date")
        )
        score_values = [round(float(score), 2) for score in performances.values_list("score", flat=True)]
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


class HistoryDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = UserPerformance.objects.filter(user=request.user).delete()
        return Response(
            {"deleted_records": deleted_count, "message": "Quiz history cleared"},
            status=status.HTTP_200_OK,
        )


class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        performances = UserPerformance.objects.select_related("quiz__topic").filter(user=request.user)
        weak_topics = []
        for performance in performances:
            if performance.score < 70:
                weak_topics.append(performance.quiz.topic.title)

        if weak_topics:
            selected_topics = list(dict.fromkeys(weak_topics))[:5]
            items = [
                {
                    "id": index + 1,
                    "topic": topic_title,
                    "suggested_material": f"Revisit your uploaded study material for {topic_title} and retake a quiz.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
                for index, topic_title in enumerate(selected_topics)
            ]
            return Response(items)

        kb_titles = list(KnowledgeBase.objects.filter(user=request.user).values_list("title", flat=True)[:3])
        if kb_titles:
            items = [
                {
                    "id": index + 1,
                    "topic": "Knowledge Base",
                    "suggested_material": f"Review {title} and ask 3 tutor questions to reinforce retention.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
                for index, title in enumerate(kb_titles)
            ]
            return Response(items)

        return Response(
            [
                {
                    "id": 1,
                    "topic": "Getting Started",
                    "suggested_material": "Upload at least one PDF or TXT file to generate personalized recommendations.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
            ]
        )
