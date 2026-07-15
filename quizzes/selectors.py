from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Quiz


def get_user_quizzes(user):
    """
    Return all quizzes owned by the supplied user.

    The reverse `quizzes` relationship is used to restrict the queryset to
    the authenticated user's records. Related questions are prefetched in a
    separate optimized query so that serializing multiple quizzes does not
    trigger an additional database query for every quiz.

    Args:
        user: The Django user whose quizzes should be retrieved.

    Returns:
        QuerySet: All quizzes owned by the user, including prefetched
            question relationships.
    """
    return user.quizzes.prefetch_related("questions").all()


def get_quiz_by_id(quiz_id):
    """
    Retrieve one quiz by its database ID.

    The related user is loaded with `select_related()` because it is required
    for the ownership check. Associated questions are loaded with
    `prefetch_related()` for later serialization.

    The function uses `first()` instead of raising an exception directly.
    This allows `get_owned_quiz()` to distinguish a missing quiz from an
    ownership violation and return the appropriate API error.

    Args:
        quiz_id: The database ID of the requested quiz.

    Returns:
        Quiz | None: The matching quiz with its related user and questions,
            or `None` when no quiz with that ID exists.
    """
    return (
        Quiz.objects.select_related("user")
        .prefetch_related("questions")
        .filter(id=quiz_id)
        .first()
    )


def ensure_quiz_owner(user, quiz):
    """
    Verify that the supplied user owns the requested quiz.

    The ownership check compares the quiz's stored `user_id` directly with
    the current user's ID. Comparing IDs avoids an unnecessary retrieval of
    the related user object.

    Args:
        user: The authenticated Django user requesting access.
        quiz: The quiz whose ownership should be verified.

    Returns:
        None: The function completes silently when the user owns the quiz.

    Raises:
        PermissionDenied: If the quiz belongs to another user.
    """
    if quiz.user_id != user.id:
        raise PermissionDenied(
            "You do not have permission to access this quiz."
        )


def get_owned_quiz(user, quiz_id):
    """
    Return a quiz only when it exists and belongs to the supplied user.

    The quiz is first retrieved through `get_quiz_by_id()`. A missing record
    produces a `NotFound` exception. Existing records are passed to
    `ensure_quiz_owner()` before being returned.

    Keeping lookup and ownership validation in this selector ensures that
    detail, update, and delete API operations apply the same access rules.

    Args:
        user: The authenticated Django user requesting the quiz.
        quiz_id: The database ID of the requested quiz.

    Returns:
        Quiz: The requested quiz after successful ownership validation.

    Raises:
        NotFound: If no quiz exists with the supplied ID.
        PermissionDenied: If the quiz exists but belongs to another user.
    """
    quiz = get_quiz_by_id(quiz_id)

    if quiz is None:
        raise NotFound("Quiz not found.")

    ensure_quiz_owner(user, quiz)
    return quiz