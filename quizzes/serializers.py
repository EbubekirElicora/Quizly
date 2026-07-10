from rest_framework import serializers

from .models import Question, Quiz
from .utils import normalize_youtube_url


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes quiz questions."""

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
    """Serializes quizzes with nested questions."""

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
    """Validates quiz creation requests."""

    url = serializers.URLField()

    def validate_url(self, value):
        try:
            return normalize_youtube_url(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Validates quiz update requests."""

    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = Quiz
        fields = ["title", "description"]