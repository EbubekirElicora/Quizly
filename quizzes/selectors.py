from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Quiz


def get_user_quizzes(user):
    """Returns all quizzes owned by the given user."""

    return user.quizzes.prefetch_related("questions").all()


def get_quiz_by_id(quiz_id):
    """Returns a quiz by id or None."""

    return (
        Quiz.objects.select_related("user")
        .prefetch_related("questions")
        .filter(id=quiz_id)
        .first()
    )


def ensure_quiz_owner(user, quiz):
    """Raises an error if the quiz is not owned by the user."""

    if quiz.user_id != user.id:
        raise PermissionDenied(
            "You do not have permission to access this quiz."
        )


def get_owned_quiz(user, quiz_id):
    """Returns a quiz only if it belongs to the given user."""

    quiz = get_quiz_by_id(quiz_id)

    if quiz is None:
        raise NotFound("Quiz not found.")

    ensure_quiz_owner(user, quiz)
    return quiz