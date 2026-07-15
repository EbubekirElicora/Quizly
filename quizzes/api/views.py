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
    """
    List the authenticated user's quizzes or generate a new quiz.

    GET requests use `get_user_quizzes()` to retrieve only the quizzes that
    belong to the current user. The results are serialized with
    `QuizSerializer`.

    POST requests validate a submitted YouTube URL through
    `QuizCreateSerializer`. After successful validation, the URL and the
    authenticated user are passed to `create_quiz_from_youtube_url()`, which
    handles audio processing, transcription, AI generation, and database
    persistence.

    Authentication is required for both operations.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all quizzes owned by the authenticated user.

        The selector `get_user_quizzes()` restricts the database query to the
        current user. The resulting queryset is serialized with nested
        question data.

        Args:
            request: The authenticated Django REST Framework request.

        Returns:
            Response: A list of the user's serialized quizzes with HTTP 200.
        """
        quizzes = get_user_quizzes(request.user)
        serializer = QuizSerializer(quizzes, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Validate a YouTube URL and start quiz generation.

        The request data is passed to `QuizCreateSerializer`, which validates
        and normalizes the submitted YouTube URL. Valid data is forwarded to
        `create_quiz_response()` for the resource-intensive quiz-generation
        process.

        Args:
            request: The authenticated Django REST Framework request
                containing a YouTube URL.

        Returns:
            Response: The generated quiz with HTTP 201, validation errors
                with HTTP 400, or a handled service error.
        """
        serializer = QuizCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.create_quiz_response(request, serializer)

    def create_quiz_response(self, request, serializer):
        """
        Generate a quiz and convert service results into an API response.

        The normalized URL from the validated serializer is passed together
        with the authenticated user to `create_quiz_from_youtube_url()`.

        That service downloads the YouTube audio, transcribes it with
        Whisper, creates quiz content with Gemini, validates the generated
        data, and saves the quiz and its questions in the database.

        Args:
            request: The authenticated Django REST Framework request.
            serializer: A validated `QuizCreateSerializer` instance.

        Returns:
            Response: The serialized quiz with HTTP 201 when generation
                succeeds, HTTP 400 for invalid or unusable input, or HTTP 500
                when media processing or AI generation fails.
        """
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
        """
        Convert a validation or input error into an HTTP 400 response.

        This helper keeps error-response creation separate from the quiz
        generation flow and returns the original error message to the client.

        Args:
            error: The caught `ValueError` describing invalid input or
                unusable video content.

        Returns:
            Response: An error message with HTTP 400.
        """
        return Response(
            {"detail": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_server_error_response(self, error):
        """
        Convert a processing failure into an HTTP 500 response.

        This response is used when the quiz-generation service cannot
        complete an operation such as audio downloading, transcription, or
        AI-based quiz generation.

        Args:
            error: The caught `RuntimeError` describing the failed operation.

        Returns:
            Response: An error message with HTTP 500.
        """
        return Response(
            {"detail": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class QuizDetailView(APIView):
    """
    Retrieve, partially update, or delete one owned quiz.

    Every operation uses `get_owned_quiz()` to ensure that the requested quiz
    exists and belongs to the authenticated user. This prevents users from
    reading or modifying quizzes owned by other accounts.

    Authentication is required for all operations.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        """
        Return one quiz owned by the authenticated user.

        The selector `get_owned_quiz()` performs the ownership check before
        the quiz and its nested questions are serialized.

        Args:
            request: The authenticated Django REST Framework request.
            quiz_id: The database ID of the requested quiz.

        Returns:
            Response: The serialized quiz with HTTP 200.
        """
        quiz = get_owned_quiz(request.user, quiz_id)

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, quiz_id):
        """
        Partially update an owned quiz's title or description.

        The quiz is retrieved through `get_owned_quiz()` before the submitted
        data is validated by `QuizUpdateSerializer`. The serializer allows
        only the editable metadata fields and leaves generated questions and
        the video URL unchanged.

        Args:
            request: The authenticated request containing the update data.
            quiz_id: The database ID of the quiz to update.

        Returns:
            Response: The updated serialized quiz with HTTP 200, or
                validation errors with HTTP 400.
        """
        quiz = get_owned_quiz(request.user, quiz_id)
        serializer = QuizUpdateSerializer(
            quiz,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, quiz_id):
        """
        Delete one quiz owned by the authenticated user.

        The ownership selector runs before deletion. Deleting the quiz also
        removes its related questions according to the model relationship.

        Args:
            request: The authenticated Django REST Framework request.
            quiz_id: The database ID of the quiz to delete.

        Returns:
            Response: An empty response with HTTP 204 after successful
                deletion.
        """
        quiz = get_owned_quiz(request.user, quiz_id)
        quiz.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)