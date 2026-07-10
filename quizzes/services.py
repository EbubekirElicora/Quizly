import json
import os
import tempfile

import whisper
import yt_dlp
from django.db import transaction
from google import genai

from .models import Question, Quiz


PROMPT_TEMPLATE = """
Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }}
  ]
}}

Requirements:
- Generate exactly 10 questions.
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question.
- The correct answer must be present in "question_options".
- The output must be valid JSON and parsable as-is.
- Do not include explanations, comments, markdown, or text outside the JSON.

Transcript:
{transcript}
"""

_whisper_model = None


def get_env_value(name):
    """Returns a required environment variable."""

    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is missing.")

    return value


def get_gemini_model_name():
    """Returns the configured Gemini model name."""

    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_whisper_model_name():
    """Returns the configured Whisper model name."""

    return os.getenv("WHISPER_MODEL", "base")


def get_gemini_client():
    """Returns a Gemini client instance."""

    api_key = get_env_value("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def get_whisper_model():
    """Loads and caches the Whisper model."""

    global _whisper_model

    if _whisper_model is None:
        _whisper_model = whisper.load_model(get_whisper_model_name())

    return _whisper_model


def get_audio_file_path(temp_dir):
    """Returns the downloaded audio file path."""

    file_names = os.listdir(temp_dir)

    if not file_names:
        raise RuntimeError("Audio file could not be downloaded.")

    return os.path.join(temp_dir, file_names[0])


def get_ydl_options(tmp_filename):
    """Returns yt_dlp options for audio download."""

    return {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }


def download_audio_from_youtube(video_url, temp_dir):
    """Downloads a YouTube video as an audio file."""

    tmp_filename = os.path.join(temp_dir, "audio.%(ext)s")
    ydl_opts = get_ydl_options(tmp_filename)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as error:
        raise ValueError(
            "The YouTube video could not be processed. "
            "Please use a standard YouTube URL like "
            "https://www.youtube.com/watch?v=VIDEO_ID."
        ) from error

    return get_audio_file_path(temp_dir)


def transcribe_audio(audio_path):
    """Transcribes an audio file using Whisper."""

    try:
        result = get_whisper_model().transcribe(audio_path)
    except Exception as error:
        raise RuntimeError("Audio transcription failed.") from error

    transcript = result.get("text", "").strip()

    if not transcript:
        raise ValueError(
            "The video transcript is empty. Please use a video with spoken content.")

    return transcript


def build_quiz_prompt(transcript):
    """Builds the Gemini prompt for quiz generation."""

    return PROMPT_TEMPLATE.format(transcript=transcript)


def remove_markdown_fences(response_text):
    """Removes markdown fences from Gemini output."""

    cleaned_text = response_text.strip()

    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]

    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]

    return cleaned_text.strip()


def parse_quiz_json(response_text):
    """Parses Gemini output into JSON data."""

    cleaned_text = remove_markdown_fences(response_text)

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini did not return valid JSON.") from error


def validate_question_structure(question):
    """Validates one generated quiz question."""

    required_fields = {"question_title", "question_options", "answer"}

    if not required_fields.issubset(question):
        raise ValueError("A generated question has missing fields.")

    validate_question_options(question)


def validate_question_options(question):
    """Validates answer options of one question."""

    options = question["question_options"]
    answer = question["answer"]

    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("Each question must have exactly 4 options.")

    if len(set(options)) != 4:
        raise ValueError("Question options must be distinct.")

    if answer not in options:
        raise ValueError("Answer must be one of the question options.")


def validate_quiz_data(quiz_data):
    """Validates the complete generated quiz data."""

    if not quiz_data.get("title") or not quiz_data.get("description"):
        raise ValueError("Generated quiz title or description is missing.")

    questions = quiz_data.get("questions")

    if not isinstance(questions, list) or len(questions) != 10:
        raise ValueError("Generated quiz must contain exactly 10 questions.")

    for question in questions:
        validate_question_structure(question)

    return quiz_data


def generate_quiz_with_gemini(transcript):
    """Generates quiz JSON data using Gemini."""

    prompt = build_quiz_prompt(transcript)
    client = get_gemini_client()

    try:
        response = client.models.generate_content(
            model=get_gemini_model_name(),
            contents=prompt,
        )
    except Exception as error:
        raise RuntimeError("Gemini quiz generation failed.") from error

    return validate_quiz_data(parse_quiz_json(response.text))


def normalize_description(description):
    """Returns a database-safe quiz description."""

    return str(description).strip()[:150]


def normalize_text(value):
    """Returns a stripped string value."""

    return str(value).strip()


def create_questions(quiz, questions):
    """Creates all questions for a quiz."""

    question_objects = [
        Question(
            quiz=quiz,
            question_title=normalize_text(question["question_title"]),
            question_options=question["question_options"],
            answer=normalize_text(question["answer"]),
        )
        for question in questions
    ]
    Question.objects.bulk_create(question_objects)


@transaction.atomic
def save_generated_quiz(user, video_url, quiz_data):
    """Saves a generated quiz with its questions."""

    quiz = Quiz.objects.create(
        user=user,
        title=normalize_text(quiz_data["title"]),
        description=normalize_description(quiz_data["description"]),
        video_url=video_url,
    )
    create_questions(quiz, quiz_data["questions"])
    return quiz


def create_quiz_from_youtube_url(user, video_url):
    """Creates a quiz from a YouTube URL."""

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = download_audio_from_youtube(video_url, temp_dir)
        transcript = transcribe_audio(audio_path)

    quiz_data = generate_quiz_with_gemini(transcript)
    return save_generated_quiz(user, video_url, quiz_data)