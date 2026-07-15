"""
Service functions for YouTube-based quiz generation.

This module contains the complete quiz-generation workflow:

1. Download audio from a YouTube video with yt_dlp.
2. Transcribe the downloaded audio with Whisper.
3. Generate structured quiz data with Gemini.
4. Validate and normalize the generated data.
5. Save the quiz and its questions in the database.

External-service and processing errors are converted into controlled
`ValueError` or `RuntimeError` exceptions so that the API layer can return
appropriate HTTP responses.
"""

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
    """
    Return the value of a required environment variable.

    This helper centralizes access to mandatory configuration values.
    A missing or empty variable is treated as a server-configuration error
    and converted into a `RuntimeError`.

    Args:
        name: Name of the required environment variable.

    Returns:
        str: The configured environment-variable value.

    Raises:
        RuntimeError: If the requested variable is missing or empty.
    """
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is missing.")

    return value


def get_gemini_model_name():
    """
    Return the configured Gemini model name.

    The value is read from `GEMINI_MODEL`. When the variable is not set,
    the application uses `gemini-2.5-flash` as its default model.

    Returns:
        str: The Gemini model name used for quiz generation.
    """
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_whisper_model_name():
    """
    Return the configured Whisper model name.

    The value is read from `WHISPER_MODEL`. When the variable is not set,
    the application loads the `base` Whisper model.

    Returns:
        str: The Whisper model name used for transcription.
    """
    return os.getenv("WHISPER_MODEL", "base")


def get_gemini_client():
    """
    Create and return an authenticated Gemini API client.

    The required API key is loaded through `get_env_value()`. Keeping client
    creation in one function prevents the Gemini key from being repeated
    throughout the service layer.

    Returns:
        genai.Client: An authenticated Google GenAI client.

    Raises:
        RuntimeError: If `GEMINI_API_KEY` is not configured.
    """
    api_key = get_env_value("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def get_whisper_model():
    """
    Load and cache the configured Whisper model.

    Loading a Whisper model is resource-intensive. The module-level
    `_whisper_model` variable ensures that the model is loaded only once
    per running Python process and reused for later transcriptions.

    Returns:
        whisper.model.Whisper: The loaded Whisper transcription model.
    """
    global _whisper_model

    if _whisper_model is None:
        _whisper_model = whisper.load_model(get_whisper_model_name())

    return _whisper_model


def get_audio_file_path(temp_dir):
    """
    Return the path of the downloaded audio file.

    After yt_dlp completes, the temporary directory is inspected for the
    generated audio file. The first file is returned because each temporary
    directory is created specifically for one video-processing request.

    Args:
        temp_dir: Path of the temporary download directory.

    Returns:
        str: Absolute or relative path to the downloaded audio file.

    Raises:
        RuntimeError: If yt_dlp did not create an audio file.
    """
    file_names = os.listdir(temp_dir)

    if not file_names:
        raise RuntimeError("Audio file could not be downloaded.")

    return os.path.join(temp_dir, file_names[0])


def get_ydl_options(tmp_filename):
    """
    Build the yt_dlp configuration used for audio downloading.

    The configuration selects the best available audio format, prevents
    playlist downloads, suppresses normal console output, and stores the
    downloaded file under the supplied temporary filename template.

    Args:
        tmp_filename: yt_dlp output template for the temporary audio file.

    Returns:
        dict: Configuration options for `yt_dlp.YoutubeDL`.
    """
    return {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }


def download_audio_from_youtube(video_url, temp_dir):
    """
    Download the best available audio stream from a YouTube video.

    A temporary output template is created inside `temp_dir` and passed to
    yt_dlp. After the download finishes, `get_audio_file_path()` locates the
    generated file.

    yt_dlp can fail because a video is unavailable, private, restricted,
    region-locked, or no longer supported. Such errors are converted into
    a user-facing `ValueError`.

    Args:
        video_url: Normalized YouTube watch URL.
        temp_dir: Directory in which the temporary audio file is stored.

    Returns:
        str: Path to the downloaded audio file.

    Raises:
        ValueError: If yt_dlp cannot process or download the video.
        RuntimeError: If no downloaded audio file can be found.
    """
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
    """
    Transcribe a downloaded audio file with Whisper.

    The cached model returned by `get_whisper_model()` processes the supplied
    audio file. The text value is extracted from Whisper's result and stripped
    of surrounding whitespace.

    Args:
        audio_path: Path to the downloaded audio file.

    Returns:
        str: The cleaned spoken-content transcript.

    Raises:
        RuntimeError: If Whisper cannot process the audio file.
        ValueError: If transcription succeeds but contains no spoken text.
    """
    try:
        result = get_whisper_model().transcribe(audio_path)
    except Exception as error:
        raise RuntimeError("Audio transcription failed.") from error

    transcript = result.get("text", "").strip()

    if not transcript:
        raise ValueError(
            "The video transcript is empty. "
            "Please use a video with spoken content."
        )

    return transcript


def build_quiz_prompt(transcript):
    """
    Insert a transcript into the Gemini quiz-generation prompt.

    The prompt defines the required JSON structure and instructs Gemini to
    create exactly ten questions with four distinct answer options each.

    Args:
        transcript: Spoken content extracted from the YouTube video.

    Returns:
        str: The complete prompt sent to Gemini.
    """
    return PROMPT_TEMPLATE.format(transcript=transcript)


def remove_markdown_fences(response_text):
    """
    Remove optional Markdown code fences from Gemini output.

    Although Gemini is instructed to return plain JSON, some responses may
    still be wrapped in `json` or generic Markdown code blocks. This helper
    removes those wrappers before JSON parsing.

    Args:
        response_text: Raw text returned by Gemini.

    Returns:
        str: Cleaned response text without surrounding Markdown fences.
    """
    cleaned_text = response_text.strip()

    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]

    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]

    return cleaned_text.strip()


def parse_quiz_json(response_text):
    """
    Parse Gemini's response into Python quiz data.

    Markdown fences are removed before the cleaned response is passed to
    `json.loads()`.

    Args:
        response_text: Raw quiz-generation response returned by Gemini.

    Returns:
        dict: Parsed quiz data containing title, description, and questions.

    Raises:
        ValueError: If Gemini's response is not valid JSON.
    """
    cleaned_text = remove_markdown_fences(response_text)

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini did not return valid JSON.") from error


def validate_question_structure(question):
    """
    Validate the required fields of one generated question.

    Every question must contain a title, an answer-options collection, and
    the correct answer. Option-specific validation is delegated to
    `validate_question_options()`.

    Args:
        question: Generated question data returned by Gemini.

    Returns:
        None.

    Raises:
        ValueError: If required question fields are missing or the answer
            options are invalid.
    """
    required_fields = {"question_title", "question_options", "answer"}

    if not required_fields.issubset(question):
        raise ValueError("A generated question has missing fields.")

    validate_question_options(question)


def validate_question_options(question):
    """
    Validate the options and correct answer of one question.

    A valid generated question must contain exactly four distinct options.
    The configured correct answer must also be one of those options.

    Args:
        question: Generated question data containing options and an answer.

    Returns:
        None.

    Raises:
        ValueError: If the options are not a four-item list, contain
            duplicates, or do not include the correct answer.
    """
    options = question["question_options"]
    answer = question["answer"]

    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("Each question must have exactly 4 options.")

    if len(set(options)) != 4:
        raise ValueError("Question options must be distinct.")

    if answer not in options:
        raise ValueError("Answer must be one of the question options.")


def validate_quiz_data(quiz_data):
    """
    Validate the complete quiz structure generated by Gemini.

    The quiz requires a non-empty title and description as well as exactly
    ten questions. Each question is validated through
    `validate_question_structure()`.

    Args:
        quiz_data: Parsed Gemini response containing the generated quiz.

    Returns:
        dict: The validated quiz data.

    Raises:
        ValueError: If required quiz metadata is missing, the number of
            questions is incorrect, or a question is structurally invalid.
    """
    if not quiz_data.get("title") or not quiz_data.get("description"):
        raise ValueError("Generated quiz title or description is missing.")

    questions = quiz_data.get("questions")

    if not isinstance(questions, list) or len(questions) != 10:
        raise ValueError("Generated quiz must contain exactly 10 questions.")

    for question in questions:
        validate_question_structure(question)

    return quiz_data


def generate_quiz_with_gemini(transcript):
    """
    Generate and validate quiz data from a transcript with Gemini.

    The transcript is inserted into the prompt through `build_quiz_prompt()`.
    An authenticated Gemini client then generates the response using the
    configured model.

    The returned text is parsed by `parse_quiz_json()` and validated through
    `validate_quiz_data()` before it can be stored in the database.

    Args:
        transcript: Spoken-content transcript created by Whisper.

    Returns:
        dict: Parsed and validated quiz data.

    Raises:
        RuntimeError: If the Gemini request cannot be completed.
        ValueError: If Gemini returns invalid JSON or invalid quiz data.
    """
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
    """
    Normalize a generated description for database storage.

    The value is converted to text, stripped of surrounding whitespace, and
    limited to the model's maximum length of 150 characters.

    Args:
        description: Description value generated by Gemini.

    Returns:
        str: Cleaned description limited to 150 characters.
    """
    return str(description).strip()[:150]


def normalize_text(value):
    """
    Convert a generated value into cleaned text.

    Args:
        value: Value that should be converted to a string.

    Returns:
        str: String value without surrounding whitespace.
    """
    return str(value).strip()


def create_questions(quiz, questions):
    """
    Create all generated questions for one quiz.

    The generated dictionaries are converted into unsaved `Question`
    instances. `bulk_create()` then inserts all questions in one database
    operation instead of executing one insert query per question.

    Args:
        quiz: The saved quiz to which the questions belong.
        questions: Validated question dictionaries generated by Gemini.

    Returns:
        None.
    """
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
    """
    Save a generated quiz and all associated questions atomically.

    The quiz record is created first, followed by its related questions
    through `create_questions()`.

    The `transaction.atomic` decorator ensures that the complete database
    operation succeeds or fails as one unit. If question creation fails,
    the previously created quiz is rolled back.

    Args:
        user: Authenticated user who owns the new quiz.
        video_url: Normalized YouTube URL used to generate the quiz.
        quiz_data: Validated quiz data returned by Gemini.

    Returns:
        Quiz: The newly created quiz instance.
    """
    quiz = Quiz.objects.create(
        user=user,
        title=normalize_text(quiz_data["title"]),
        description=normalize_description(quiz_data["description"]),
        video_url=video_url,
    )

    create_questions(quiz, quiz_data["questions"])
    return quiz


def create_quiz_from_youtube_url(user, video_url):
    """
    Execute the complete YouTube-to-quiz generation workflow.

    A temporary directory is created for the downloaded audio. The file is
    downloaded through `download_audio_from_youtube()` and transcribed with
    Whisper through `transcribe_audio()`.

    After leaving the temporary-directory context, the audio file is removed
    automatically. The transcript is sent to Gemini, and the validated result
    is saved with `save_generated_quiz()`.

    Args:
        user: Authenticated user who will own the generated quiz.
        video_url: Validated and normalized YouTube URL.

    Returns:
        Quiz: The saved quiz containing ten generated questions.

    Raises:
        ValueError: If the YouTube video, transcript, or generated quiz data
            is invalid.
        RuntimeError: If audio transcription, Gemini communication, or
            another processing operation fails.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = download_audio_from_youtube(video_url, temp_dir)
        transcript = transcribe_audio(audio_path)

    quiz_data = generate_quiz_with_gemini(transcript)
    return save_generated_quiz(user, video_url, quiz_data)