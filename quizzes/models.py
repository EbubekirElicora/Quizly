from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """
    Store one generated quiz belonging to a user.

    Each quiz contains a title, a short description, and the normalized
    YouTube URL from which the quiz was generated.

    The `user` foreign key defines the owner of the quiz. When a user account
    is deleted, all quizzes belonging to that account are removed through
    Django's cascade behavior.

    Related questions can be accessed through the `questions` relationship.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=150)
    video_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """
        Return the quiz title as its human-readable representation.

        Django uses this value in the admin interface, shell output, and
        other places where a quiz instance is converted into text.

        Returns:
            str: The title of the quiz.
        """
        return self.title


class Question(models.Model):
    """
    Store one generated question belonging to a quiz.

    The question options are stored as JSON because each question contains
    a list of exactly four generated answer choices. The correct answer is
    stored separately and must match one of those options.

    When the parent quiz is deleted, all related questions are removed
    automatically through Django's cascade behavior.
    """

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return the question text as its human-readable representation.

        Django uses this value when displaying question instances in the
        admin interface, shell output, and debugging information.

        Returns:
            str: The title or text of the question.
        """
        return self.question_title