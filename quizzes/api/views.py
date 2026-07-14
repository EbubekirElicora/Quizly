from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from quizzes.selectors import get_owned_quiz, get_user_quizzes
from quizzes.services import create_quiz_from_youtube_url
from .serializers import (
    QuizCreateSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)

class QuizListCreateView(APIView):
    """Lists user quizzes or creates a new quiz."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = get_user_quizzes(request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return self.create_quiz_response(request, serializer)

    def create_quiz_response(self, request, serializer):
        try:
            quiz = create_quiz_from_youtube_url(
                request.user,
                serializer.validated_data["url"],
            )
        except ValueError as error:
            return self.get_bad_request_response(error)
        except RuntimeError as error:
            return self.get_server_error_response(error)

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_201_CREATED,
        )

    def get_bad_request_response(self, error):
        return Response(
            {"detail": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_server_error_response(self, error):
        return Response(
            {"detail": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QuizDetailView(APIView):
    """Retrieves, updates, or deletes a quiz."""

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        quiz = get_owned_quiz(request.user, quiz_id)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def patch(self, request, quiz_id):
        quiz = get_owned_quiz(request.user, quiz_id)
        serializer = QuizUpdateSerializer(quiz, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def delete(self, request, quiz_id):
        quiz = get_owned_quiz(request.user, quiz_id)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)