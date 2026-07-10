from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Allows editing quiz questions inside the quiz admin page."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for quizzes."""

    list_display = ("id", "title", "user", "created_at", "updated_at")
    search_fields = ("title", "description", "video_url", "user__username")
    list_filter = ("created_at", "updated_at")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for quiz questions."""

    list_display = ("id", "question_title", "quiz", "answer")
    search_fields = ("question_title", "answer", "quiz__title")