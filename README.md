# Quizly

## Project Overview

Quizly is a full-stack quiz application that allows users to generate interactive quizzes from YouTube videos.

Users can register, log in, create quizzes from YouTube URLs, manage their generated quizzes, play quizzes, and review their results.

The project consists of a provided frontend and a custom Django REST backend.

The backend processes a YouTube video by downloading its audio, transcribing the audio with Whisper AI, generating quiz data with Gemini Flash, and saving the generated quiz with its questions in the database.

---

## Features

- User registration
- User login and logout
- JWT authentication with HttpOnly cookies
- Token refresh via refresh cookie
- Quiz generation from YouTube URLs
- YouTube audio download with `yt_dlp`
- Audio processing with FFmpeg
- Audio transcription with Whisper AI
- Quiz generation with Gemini Flash
- Quiz overview for authenticated users
- Quiz detail view with embedded YouTube video
- Edit quiz title and description
- Delete quizzes
- Play quizzes with 10 multiple-choice questions
- Result review with correct answers
- Django admin panel for quizzes and questions

---

## Project Structure

```text
Projekt_Quizly_Ebubekir_Elicora/
├── Projekt_Quizly_BackEnd/
│   ├── accounts/
│   ├── config/
│   ├── quizzes/
│   ├── manage.py
│   ├── requirements.txt
│   ├── README.md
│   └── .env
│
└── Projekt_Quizly_FrontEnd/
    ├── assets/
    ├── pages/
    ├── shared/
    ├── index.html
    ├── styles.css
    └── README.md
```

---

## Tech Stack

### Frontend

- HTML
- CSS
- JavaScript
- VS Code Live Server

### Backend

- Python
- Django
- Django REST Framework
- Django REST Framework Simple JWT
- JWT authentication with HttpOnly cookies
- SQLite for local development
- `yt_dlp`
- Whisper AI
- Google GenAI / Gemini Flash
- FFmpeg

---

## Requirements

Before running the project, make sure the following tools are installed:

- Python
- FFmpeg installed globally
- A Gemini API key
- A modern browser
- VS Code Live Server or another local web server

FFmpeg must be available globally. You can check this with:

```bash
ffmpeg -version
```

If FFmpeg is not found, install FFmpeg and add the `bin` folder to your system PATH.

Example Windows path:

```text
C:\ffmpeg\bin
```

---

## Backend Setup

Open the backend folder:

```bash
cd Projekt_Quizly_BackEnd
```

Create a virtual environment:

```bash
python -m venv env
```

Activate the virtual environment on Windows:

```bash
env\Scripts\activate
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the backend folder:

```text
Projekt_Quizly_BackEnd/.env
```

Add the following variables:

```env
SECRET_KEY=your_django_secret_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
WHISPER_MODEL=base
```

Run the migrations:

```bash
python manage.py migrate
```

Start the backend server:

```bash
python manage.py runserver
```

The backend runs at:

```text
http://127.0.0.1:8000
```

---

## Frontend Setup

Open the frontend folder:

```bash
cd Projekt_Quizly_FrontEnd
```

Start the frontend with Live Server from:

```text
index.html
```

The frontend usually runs at:

```text
http://127.0.0.1:5500
```

or:

```text
http://127.0.0.1:5501
```

The backend must allow the frontend origin in the CORS settings.

Example:

```python
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
]
```

---

## Authentication

The backend uses JWT authentication with HttpOnly cookies.

After a successful login, the backend sets two cookies:

```text
access_token
refresh_token
```

The frontend does not store tokens in `localStorage` or `sessionStorage`.

Protected API routes are authenticated through the HttpOnly access token cookie.

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Register a new user |
| POST | `/api/login/` | Log in and set JWT cookies |
| POST | `/api/logout/` | Log out and delete authentication cookies |
| POST | `/api/token/refresh/` | Refresh the access token |

### Quizzes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/quizzes/` | Get all quizzes of the authenticated user |
| POST | `/api/quizzes/` | Create a new quiz from a YouTube URL |
| GET | `/api/quizzes/{id}/` | Get one quiz by ID |
| PATCH | `/api/quizzes/{id}/` | Update quiz title and description |
| DELETE | `/api/quizzes/{id}/` | Delete a quiz |

---

## Quiz Generation Flow

```text
YouTube URL
→ Extract YouTube video ID
→ Normalize URL to https://www.youtube.com/watch?v=VIDEO_ID
→ Download audio with yt_dlp
→ Process audio with FFmpeg
→ Transcribe audio with Whisper AI
→ Generate quiz JSON with Gemini Flash
→ Remove possible markdown formatting from AI output
→ Validate quiz JSON structure
→ Save quiz and questions in the database
```

Each generated quiz contains exactly 10 questions.

Each question contains:

- one question title
- exactly 4 distinct answer options
- exactly one correct answer

---

## YouTube URL Format

For best results, use standard YouTube URLs:

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

The backend also normalizes supported YouTube URL formats to this structure.

Some videos may not be processable because of:

- age restrictions
- private videos
- unavailable videos
- region restrictions
- download restrictions
- videos without spoken content

---

## Admin Panel

The Django admin panel is available at:

```text
http://127.0.0.1:8000/admin/
```

The admin panel allows managing:

- users
- quizzes
- quiz questions
- blacklisted tokens
- outstanding tokens

To create an admin user:

```bash
python manage.py createsuperuser
```

---

## Postman Testing

The API was tested with Postman using happy-path and unhappy-path collections.

Recommended collection structure:

```text
Quizly Backend API
├── happy-path
│   ├── Authentication
│   └── Quizzes
└── unhappy-path
    ├── Authentication
    └── Quizzes
```

Important test cases:

### Authentication

- Register user
- Login user
- Refresh access token
- Logout user
- Register with missing fields
- Register with duplicate username or email
- Login with wrong credentials
- Refresh without token
- Logout without login

### Quizzes

- Create quiz from YouTube URL
- Get all user quizzes
- Get quiz detail
- Update quiz title and description
- Delete quiz
- Create quiz with missing URL
- Create quiz with invalid URL
- Create quiz with non-YouTube URL
- Access quiz without login
- Access foreign quiz
- Access non-existing quiz

---

## Security Notes

The `.env` file must never be committed to GitHub.

The following files and folders should be ignored:

```text
env/
.env
db.sqlite3
__pycache__/
*.pyc
media/
staticfiles/
```

Example `.gitignore`:

```gitignore
env/
__pycache__/
*.pyc
db.sqlite3
.env
media/
staticfiles/
```

---

## Local Development Workflow

Start the backend first:

```bash
cd Projekt_Quizly_BackEnd
env\Scripts\activate
python manage.py runserver
```

Then start the frontend with Live Server from:

```text
Projekt_Quizly_FrontEnd/index.html
```

Backend:

```text
http://127.0.0.1:8000
```

Frontend:

```text
http://127.0.0.1:5500
```

or:

```text
http://127.0.0.1:5501
```

---

## Notes for Reviewers

This project uses a provided frontend and a custom Django REST backend.

The backend handles:

- authentication
- cookie-based JWT sessions
- YouTube URL validation
- audio download
- transcription
- AI quiz generation
- database persistence
- quiz ownership checks

Users can only access, edit, and delete their own quizzes.

Foreign quiz access returns `403 Forbidden`.

Missing quizzes return `404 Not Found`.

Invalid quiz creation data returns `400 Bad Request`.