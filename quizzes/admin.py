"""
Django admin configuration for quizzes and questions.

Quiz questions can be edited directly inside the related quiz through a
tabular inline. Quizzes and questions are also registered separately so
that administrators can search, filter, and manage them individually.
"""

from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """
    Display and edit questions inside the associated quiz admin page.

    No additional empty question rows are displayed because generated
    questions already exist when a quiz is opened in the admin interface.
    """

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    Configure the Django admin interface for generated quizzes.

    The list view displays ownership and timestamps. Search and filter
    options make it easier to locate quizzes by their metadata or owner.
    Related questions are editable through `QuestionInline`.
    """

    list_display = ("id", "title", "user", "created_at", "updated_at")
    search_fields = ("title", "description", "video_url", "user__username")
    list_filter = ("created_at", "updated_at")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Configure the Django admin interface for individual quiz questions.

    Administrators can search questions by their text, correct answer, or
    the title of the related quiz.
    """

    list_display = ("id", "question_title", "quiz", "answer")
    search_fields = ("question_title", "answer", "quiz__title")