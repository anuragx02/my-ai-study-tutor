from collections import Counter

from django.db import DatabaseError, transaction
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.core.models import (
    ChatMessage,
    ChatSession,
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
from backend.apps.core.services.retrieval_service import retrieve_context


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


def _quiz_option_text(question: Question, option: str | None) -> str:
    if option == "A":
        return question.option_a
    if option == "B":
        return question.option_b
    if option == "C":
        return question.option_c
    if option == "D":
        return question.option_d
    return ""


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


class TopicListCreateView(generics.ListCreateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Topic.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
        quiz_topic = focus or "General Study"
        payload = generate_ai_quiz(topic=quiz_topic, difficulty=difficulty, total_questions=total_questions)

        if not isinstance(payload, dict):
            return Response(
                {"detail": "Quiz generation failed: AI response was not a JSON object."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        question_items = payload.get("questions")
        if not isinstance(question_items, list) or not question_items:
            return Response(
                {"detail": "Quiz generation failed: AI response did not include questions."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        topic = Topic.objects.filter(user=request.user).order_by("id").first()
        if not topic:
            return Response(
                {"detail": "Create a topic before generating a quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_keys = {
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "explanation",
        }

        for index, item in enumerate(question_items, start=1):
            if not isinstance(item, dict):
                return Response(
                    {"detail": f"Quiz generation failed: question {index} is not an object."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            missing = [key for key in required_keys if key not in item]
            if missing:
                return Response(
                    {"detail": f"Quiz generation failed: question {index} missing fields: {', '.join(sorted(missing))}."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            normalized_correct_option = _normalize_quiz_option(item.get("correct_option"))
            if normalized_correct_option not in {"A", "B", "C", "D"}:
                return Response(
                    {"detail": f"Quiz generation failed: question {index} has invalid correct_option."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        try:
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    topic=topic,
                    difficulty=difficulty,
                    total_questions=total_questions,
                    created_by=request.user,
                )

                for item in question_items:
                    Question.objects.create(
                        quiz=quiz,
                        question_text=item["question_text"],
                        option_a=item["option_a"],
                        option_b=item["option_b"],
                        option_c=item["option_c"],
                        option_d=item["option_d"],
                        correct_option=_normalize_quiz_option(item.get("correct_option")),
                        explanation=str(item["explanation"]).strip(),
                    )
        except DatabaseError:
            return Response(
                {"detail": "Quiz generation failed due to a database schema mismatch. Run latest migrations on the server and retry."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        question_reviews = []
        for question in questions:
            selected_option = answer_map.get(question.id)
            correct_option = _normalize_quiz_option(question.correct_option)
            is_correct = bool(selected_option and correct_option and selected_option == correct_option)
            if is_correct:
                correct_count += 1
            else:
                incorrect_questions.append(
                    {
                        "question_id": question.id,
                        "topic": quiz.topic.title,
                    }
                )

            question_reviews.append(
                {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "selected_option": selected_option,
                    "selected_option_text": _quiz_option_text(question, selected_option),
                    "correct_option": correct_option,
                    "correct_option_text": _quiz_option_text(question, correct_option),
                    "is_correct": is_correct,
                    "explanation": question.explanation,
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

        weak_topics = sorted({item["topic"] for item in incorrect_questions})
        if weak_topics:
            recommendation = f"Focus next on: {', '.join(weak_topics)}. Review the incorrect questions and retake a quiz on these topics."
        else:
            recommendation = "Great work. Try a harder quiz or a new topic to keep improving."

        return Response(
            {
                "performance": UserPerformanceSerializer(performance).data,
                "score": score,
                "accuracy": score,
                "correct_count": correct_count,
                "incorrect_count": len(incorrect_questions),
                "weak_topics": weak_topics,
                "incorrect_questions": incorrect_questions,
                "question_reviews": question_reviews,
                "study_recommendation": recommendation,
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
        force_web = serializer.validated_data.get("force_web", False)

        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            title = question_text.strip()[:48]
            session = ChatSession.objects.create(
                user=request.user,
                title=title,
            )

        recent_messages = list(session.messages.order_by("-created_at", "-id")[:20])
        recent_messages.reverse()
        conversation_history = [
            {
                "role": message.role,
                "content": message.text,
            }
            for message in recent_messages
        ]

        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            text=question_text,
        )

        retrieval = retrieve_context(question=question_text, user=request.user, force_web=force_web)
        # Default to academic tutoring even when KB has no match,
        # so the model can still answer directly without web lookup.
        is_academic = True
        result = ask_ai(
            question_text,
            topic_context=retrieval.context,
            conversation_history=conversation_history,
            is_academic=is_academic,
        )
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
                "study_time_minutes": int((performances.aggregate(total=Sum("completion_time"))["total"] or 0) / 60),
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
                    "suggested_material": f"Revisit {topic_title} concepts in chat and retake a quiz.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
                for index, topic_title in enumerate(selected_topics)
            ]
            return Response(items)

        return Response(
            [
                {
                    "id": 1,
                    "topic": "Getting Started",
                    "suggested_material": "Start with a short chat session and then take a quiz to get personalized recommendations.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
            ]
        )
