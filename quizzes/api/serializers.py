from rest_framework import serializers

from quizzes.models import Question, Quiz
from quizzes.utils import normalize_youtube_url


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serialize quiz questions for API responses.

    The serializer returns the question text, the available answer options,
    the correct answer, and the creation and update timestamps.

    Question instances are included as nested data inside quiz responses.
    """

    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """
    Serialize a quiz together with all associated questions.

    The related questions are serialized through `QuestionSerializer`.
    They are read-only because quiz questions are created by the quiz
    generation service and cannot be submitted directly through this
    serializer.
    """

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]


class QuizCreateSerializer(serializers.Serializer):
    """
    Validate the data required to generate a new quiz.

    The serializer expects a YouTube URL. Before the URL is passed to the
    quiz generation service, it is validated and converted into the
    standardized YouTube watch-URL format.
    """

    url = serializers.URLField()

    def validate_url(self, value):
        """
        Validate and normalize the submitted YouTube URL.

        The URL is passed to `normalize_youtube_url()`. That utility extracts
        the video ID from supported YouTube URL formats and returns a
        canonical URL in the following format:

        `https://www.youtube.com/watch?v=VIDEO_ID`

        Args:
            value: The YouTube URL submitted by the user.

        Returns:
            str: The validated and normalized YouTube URL.

        Raises:
            serializers.ValidationError: If the URL is not a supported
                YouTube URL or does not contain a valid video ID.
        """
        try:
            return normalize_youtube_url(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error


class QuizUpdateSerializer(serializers.ModelSerializer):
    """
    Validate partial updates to an existing quiz.

    Only the title and description can be changed. The generated questions
    and original YouTube URL are deliberately excluded from update requests.

    Both fields are optional because the corresponding API endpoint uses
    partial updates.
    """

    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = Quiz
        fields = ["title", "description"]