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
    UserPerformance,
)
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
    UserPerformanceSerializer,
    UserSerializer,
    OCRSerializer,
)
from backend.apps.core.services.ai_service import (
    ask_ai,
    generate_answer_explanation,
    generate_quiz as generate_ai_quiz,
    extract_text_from_image,
)
from backend.apps.core.services.retrieval_service import retrieve_context


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

class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuizGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        difficulty = serializer.validated_data["difficulty"]
        total_questions = serializer.validated_data["total_questions"]

        focus = serializer.validated_data.get("focus", "").strip()
        quiz_focus = focus or "General Study"
        try:
            payload = generate_ai_quiz(focus=quiz_focus, difficulty=difficulty, total_questions=total_questions)
        except ValueError:
            return Response(
                {"detail": "Quiz generation failed: AI returned invalid JSON. Retry once."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"detail": "Quiz generation failed: AI provider request failed. Retry once."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

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

        required_keys = {
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
        }
        option_letters = {"A", "B", "C", "D"}
        option_mappings = {
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

            option_value = item.get("correct_option")
            normalized = str(option_value or "").strip().upper()
            compact = normalized.replace(" ", "")
            normalized_correct_option = (
                normalized if normalized in option_letters
                else option_mappings.get(compact)
                or (compact[6] if compact.startswith("OPTION") and len(compact) > 6 and compact[6] in option_letters else None)
                or (compact[0] if compact and compact[0] in option_letters else None)
                or next((char for char in normalized if char in option_letters), None)
            )
            if normalized_correct_option not in option_letters:
                return Response(
                    {"detail": f"Quiz generation failed: question {index} has invalid correct_option."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        try:
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    focus=quiz_focus,
                    difficulty=difficulty,
                    total_questions=total_questions,
                    created_by=request.user,
                )

                for item in question_items:
                    option_value = item.get("correct_option")
                    normalized = str(option_value or "").strip().upper()
                    compact = normalized.replace(" ", "")
                    normalized_correct_option = (
                        normalized if normalized in option_letters
                        else option_mappings.get(compact)
                        or (compact[6] if compact.startswith("OPTION") and len(compact) > 6 and compact[6] in option_letters else None)
                        or (compact[0] if compact and compact[0] in option_letters else None)
                        or next((char for char in normalized if char in option_letters), None)
                    )
                    Question.objects.create(
                        quiz=quiz,
                        question_text=item["question_text"],
                        option_a=item["option_a"],
                        option_b=item["option_b"],
                        option_c=item["option_c"],
                        option_d=item["option_d"],
                        correct_option=normalized_correct_option,
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
        option_letters = {"A", "B", "C", "D"}
        option_mappings = {
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
        answer_map = {}
        for answer in serializer.validated_data["answers"]:
            option_value = answer["selected_option"]
            normalized = str(option_value or "").strip().upper()
            compact = normalized.replace(" ", "")
            normalized_selected_option = (
                normalized if normalized in option_letters
                else option_mappings.get(compact)
                or (compact[6] if compact.startswith("OPTION") and len(compact) > 6 and compact[6] in option_letters else None)
                or (compact[0] if compact and compact[0] in option_letters else None)
                or next((char for char in normalized if char in option_letters), None)
            )
            answer_map[answer["question_id"]] = normalized_selected_option

        correct_count = 0
        incorrect_questions = []
        question_reviews = []
        for question in questions:
            selected_option = answer_map.get(question.id)
            option_value = question.correct_option
            normalized = str(option_value or "").strip().upper()
            compact = normalized.replace(" ", "")
            correct_option = (
                normalized if normalized in option_letters
                else option_mappings.get(compact)
                or (compact[6] if compact.startswith("OPTION") and len(compact) > 6 and compact[6] in option_letters else None)
                or (compact[0] if compact and compact[0] in option_letters else None)
                or next((char for char in normalized if char in option_letters), None)
            )
            option_text_by_key = {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
            }
            correct_option_text = option_text_by_key.get(correct_option, "")
            is_correct = bool(selected_option and correct_option and selected_option == correct_option)
            if is_correct:
                correct_count += 1
            else:
                incorrect_questions.append(
                    {
                        "question_id": question.id,
                        "topic": quiz.focus,
                    }
                )

            explanation_text = ""
            if correct_option and correct_option_text:
                try:
                    explanation_text = generate_answer_explanation(
                        question_text=question.question_text,
                        correct_option=correct_option,
                        correct_option_text=correct_option_text,
                    )
                except Exception:
                    explanation_text = ""

            question_reviews.append(
                {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "selected_option": selected_option,
                    "selected_option_text": option_text_by_key.get(selected_option, ""),
                    "correct_option": correct_option,
                    "correct_option_text": correct_option_text,
                    "is_correct": is_correct,
                    "explanation": explanation_text,
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

        weak_focuses = sorted({item["topic"] for item in incorrect_questions})
        if weak_focuses:
            recommendation = f"Focus next on: {', '.join(weak_focuses)}. Review the incorrect questions and retake a quiz on these focus areas."
        else:
            recommendation = "Great work. Try a harder quiz or a new topic to keep improving."

        return Response(
            {
                "performance": UserPerformanceSerializer(performance).data,
                "score": score,
                "accuracy": score,
                "correct_count": correct_count,
                "incorrect_count": len(incorrect_questions),
                "incorrect_questions": incorrect_questions,
                "question_reviews": question_reviews,
                "study_recommendation": recommendation,
            },
            status=status.HTTP_201_CREATED,
        )

class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.select_related("created_by").prefetch_related("questions")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

class AskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question_text = serializer.validated_data.get("question", "")
        image_context = serializer.validated_data.get("image_context", "")
        session_id = serializer.validated_data.get("session_id")
        force_web = serializer.validated_data.get("force_web", False)
        ai_question = f"{question_text}\n\nImage content:\n{image_context}".strip() if image_context else question_text

        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            title = (question_text.strip() or "Image question")[:48]
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
            text=question_text or "Image attached",
        )

        retrieval = retrieve_context(question=question_text or image_context, user=request.user, force_web=force_web)
        is_academic = True
        result = ask_ai(
            ai_question,
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
            UserPerformance.objects.select_related("quiz")
            .filter(user=request.user)
            .order_by("attempt_date")
        )
        score_values = [round(float(score), 2) for score in performances.values_list("score", flat=True)]

        return Response(
            {
                "quiz_score_trend": score_values[-5:],
                "accuracy": round(performances.aggregate(avg=Avg("score"))["avg"] or 0, 2),
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
        performances = UserPerformance.objects.select_related("quiz").filter(user=request.user)
        weak_focuses = []
        for performance in performances:
            if performance.score < 70:
                weak_focuses.append(performance.quiz.focus)

        if weak_focuses:
            selected_focuses = list(dict.fromkeys(weak_focuses))[:5]
            items = [
                {
                    "id": index + 1,
                    "topic": focus_label,
                    "suggested_material": f"Revisit {focus_label} concepts in chat and retake a quiz.",
                    "date_generated": timezone.now().isoformat().replace("+00:00", "Z"),
                }
                for index, focus_label in enumerate(selected_focuses)
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

class OCRView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OCRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_url = serializer.validated_data["image_url"]
        instruction = serializer.validated_data.get("instruction", "Extract all text from this image")
        extracted_text = extract_text_from_image(image_url, instruction)
        return Response({"success": True, "text": extracted_text, "image_url": image_url}, status=status.HTTP_200_OK)
