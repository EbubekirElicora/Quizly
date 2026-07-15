# Quizly

Quizly is a full-stack quiz application that generates interactive quizzes from YouTube videos.

Users can register, log in, submit a YouTube URL, generate a quiz with AI, manage their quizzes, play them, and review their results.

The frontend was provided as part of the project assignment. The Django REST backend, authentication system, YouTube processing, Whisper integration, Gemini integration, database models, API endpoints, permissions, and deployment were implemented for this project.

---

## Table of Contents

- [Live Demo](#live-demo)
- [Features](#features)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Local Setup](#local-setup)
  - [Requirements](#requirements)
  - [Environment Variables](#environment-variables)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [CORS Configuration](#cors-configuration)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Example Requests](#example-requests)
- [Quiz Generation Flow](#quiz-generation-flow)
- [YouTube Processing](#youtube-processing)
- [Permissions and Ownership](#permissions-and-ownership)
- [Admin Panel](#admin-panel)
- [Postman Testing](#postman-testing)
- [Production Deployment](#production-deployment)
- [Security Notes](#security-notes)
- [Local Development Workflow](#local-development-workflow)
- [Notes for Reviewers](#notes-for-reviewers)

---

## Live Demo

- **Application:** https://quizly.ebubekir-elicora.de/
- **API:** https://quizly.ebubekir-elicora.de/api/
- **Admin panel:** https://quizly.ebubekir-elicora.de/admin/

The deployed frontend and backend are served through the same HTTPS domain.

---

## Features

### Authentication

- User registration
- User login and logout
- JWT authentication
- HttpOnly cookie-based authentication
- Access and refresh tokens
- Automatic access-token refresh
- Protected API endpoints

### Quiz Management

- Generate a quiz from a YouTube URL
- Display all quizzes belonging to the authenticated user
- Display individual quiz details
- Edit quiz title and description
- Delete quizzes
- Protect quizzes through ownership checks
- Prevent users from accessing quizzes belonging to other users

### AI Quiz Generation

- Extract and normalize YouTube video IDs
- Download YouTube audio using `yt_dlp`
- Process audio using FFmpeg
- Transcribe spoken content using Whisper AI
- Generate quiz data using Gemini Flash
- Remove possible Markdown formatting from AI responses
- Validate generated quiz data
- Save quizzes and questions in the database

### Quiz Experience

- Exactly 10 questions per generated quiz
- Exactly 4 answer options per question
- One correct answer per question
- Embedded YouTube video
- Quiz result evaluation
- Display of correct and incorrect answers
- Quiz history and overview

### Administration

- Django admin panel
- Manage users
- Manage quizzes
- Manage questions
- Manage outstanding and blacklisted JWT tokens

---

## Architecture

```text
Browser
   │
   ▼
Nginx
   ├── Frontend files
   ├── /api/    → Gunicorn → Django REST Framework
   ├── /admin/  → Gunicorn → Django
   └── /static/ → Django static files
                         │
                         ▼
               YouTube / Whisper / Gemini
```

The production application uses:

- Nginx as web server and reverse proxy
- Gunicorn as WSGI application server
- Supervisor for process management
- Certbot and Let’s Encrypt for HTTPS
- FFmpeg installed globally
- Google Cloud virtual machine
- ALL-INKL DNS management

---

## Repository Structure

This GitHub repository contains the custom Django backend.

```text
Quizly/
├── accounts/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── migrations/
│   ├── authentication.py
│   ├── apps.py
│   └── utils.py
│
├── core/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── quizzes/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── selectors.py
│   ├── services.py
│   └── utils.py
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

The provided frontend is maintained separately and is not included in this backend repository.

---

## Tech Stack

### Frontend

- HTML
- CSS
- JavaScript
- Fetch API

### Backend

- Python
- Django
- Django REST Framework
- Django REST Framework Simple JWT
- Django CORS Headers
- SQLite
- Gunicorn

### AI and Media Processing

- `yt_dlp`
- FFmpeg
- OpenAI Whisper
- Google GenAI
- Gemini Flash
- PyTorch

### Deployment

- Google Cloud
- Ubuntu
- Nginx
- Gunicorn
- Supervisor
- Certbot
- Let’s Encrypt
- HTTPS
- DNS through ALL-INKL

---

## Local Setup

The following sections explain how to configure and run Quizly locally.

## Requirements

Before running the project locally, make sure the following tools are installed:

- Python
- Git
- FFmpeg
- A Gemini API key
- A modern browser
- VS Code Live Server or another local frontend server

Check whether FFmpeg is available globally:

```bash
ffmpeg -version
```

On Windows, the FFmpeg `bin` directory must be included in the system PATH.

Example:

```text
C:\ffmpeg\bin
```

---

### Environment Variables

Create a `.env` file in the backend project root:

```text
Quizly/.env
```

Example:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

WHISPER_MODEL=base
```

For production, use:

```env
DEBUG=False
ALLOWED_HOSTS=quizly.ebubekir-elicora.de,34.185.157.73,localhost,127.0.0.1
WHISPER_MODEL=tiny
```

The production `.env` file must never be committed to GitHub.

---

### Backend Setup

Clone the repository:

```bash
git clone https://github.com/EbubekirElicora/Quizly.git
```

Open the project:

```bash
cd Quizly
```

Create a virtual environment:

```bash
python -m venv env
```

Activate it on Windows:

```bash
env\Scripts\activate
```

Activate it on Linux or macOS:

```bash
source env/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create the [`.env` file](#environment-variables) and add the required environment variables listed in the Environment Variables section.

Run the migrations:

```bash
python manage.py migrate
```

Create an administrator account if required:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

The local backend is then available at:

```text
http://127.0.0.1:8000/
```

The local admin panel is available at:

```text
http://127.0.0.1:8000/admin/
```

---

### Frontend Setup

> The frontend was provided separately and is not included in this backend repository.

The frontend folder contains approximately:

```text
Projekt_Quizly_FrontEnd/
├── assets/
├── pages/
├── shared/
├── index.html
├── script.js
└── styles.css
```

Open the frontend folder in VS Code and start Live Server from:

```text
index.html
```

The frontend usually runs at:

```text
http://127.0.0.1:5500/
```

or:

```text
http://127.0.0.1:5501/
```

For local development, the frontend API base URL must point to:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000/api/";
```

For production, it must point to:

```javascript
const API_BASE_URL = "https://quizly.ebubekir-elicora.de/api/";
```

Authenticated frontend requests use:

```javascript
credentials: "include"
```

---

## CORS Configuration

During local development, the backend must allow the frontend origins.

Example:

```python
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
]

CORS_ALLOW_CREDENTIALS = True
```

In production, the frontend and backend are served through the same domain:

```text
https://quizly.ebubekir-elicora.de/
```

This avoids cross-site authentication issues between the frontend and backend.

---

## Authentication

The backend uses JWT authentication with HttpOnly cookies.

After a successful login, the backend sets:

```text
access_token
refresh_token
```

The frontend cannot directly read these cookies because they are marked as HttpOnly.

Tokens are not stored in:

- `localStorage`
- `sessionStorage`
- JavaScript variables

Protected requests automatically send the cookies using:

```javascript
credentials: "include"
```

When the access token expires, the frontend can request a new access token through:

```text
POST /api/token/refresh/
```

The production cookies are transmitted securely over HTTPS.

---

## API Endpoints

Base URL:

```text
https://quizly.ebubekir-elicora.de/api/
```

### Authentication

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| POST | `/api/register/` | No | Register a new user |
| POST | `/api/login/` | No | Log in and set JWT cookies |
| POST | `/api/logout/` | Yes | Log out, remove cookies, and blacklist the refresh token |
| POST | `/api/token/refresh/` | Refresh cookie | Create a new access token |

### Quizzes

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| GET | `/api/quizzes/` | Yes | Get all quizzes belonging to the authenticated user |
| POST | `/api/quizzes/` | Yes | Generate a quiz from a YouTube URL |
| GET | `/api/quizzes/{id}/` | Yes | Get one quiz |
| PATCH | `/api/quizzes/{id}/` | Yes | Update quiz title and description |
| DELETE | `/api/quizzes/{id}/` | Yes | Delete a quiz |

---

## Example Requests

### Register

```http
POST /api/register/
Content-Type: application/json
```

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Testpass123!",
  "confirmed_password": "Testpass123!"
}
```

Successful response:

```json
{
  "detail": "User created successfully!"
}
```

### Login

```http
POST /api/login/
Content-Type: application/json
```

```json
{
  "username": "testuser",
  "password": "Testpass123!"
}
```

The response sets the access and refresh cookies.

### Create Quiz

```http
POST /api/quizzes/
Content-Type: application/json
```

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

A successful request returns the generated quiz with exactly 10 questions.

---

## Quiz Generation Flow

```text
YouTube URL
    ↓
Extract video ID
    ↓
Normalize URL
    ↓
Download audio with yt_dlp
    ↓
Process audio with FFmpeg
    ↓
Transcribe audio with Whisper
    ↓
Create prompt for Gemini
    ↓
Generate quiz JSON
    ↓
Remove possible Markdown code blocks
    ↓
Validate title, description, questions and answers
    ↓
Save quiz and questions in the database
```

The normalized YouTube URL uses this format:

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

Each generated quiz contains:

- exactly 10 questions
- exactly 4 distinct answer options per question
- exactly one correct answer per question
- a title
- a description
- the normalized YouTube URL

---

## YouTube Processing

The configured `yt_dlp` options include:

```python
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": tmp_filename,
    "quiet": True,
    "noplaylist": True,
}
```

Temporary audio files are removed automatically after processing.

Some YouTube videos may not be processable because of:

- age restrictions
- private visibility
- regional restrictions
- unavailable videos
- download restrictions
- missing audio
- missing spoken content
- unsupported YouTube changes

---

## Permissions and Ownership

Users can only access their own quizzes.

The backend verifies quiz ownership before allowing:

- detail access
- updates
- deletion

Expected responses include:

| Status | Meaning |
|---:|---|
| `200 OK` | Request completed successfully |
| `201 Created` | User or quiz created successfully |
| `400 Bad Request` | Invalid or missing input |
| `401 Unauthorized` | Authentication is missing or expired |
| `403 Forbidden` | The user does not own the requested quiz |
| `404 Not Found` | The requested quiz does not exist |
| `500 Internal Server Error` | Audio transcription, AI generation, or another server operation failed |

---

## Admin Panel

### Local

```text
http://127.0.0.1:8000/admin/
```

### Production

```text
https://quizly.ebubekir-elicora.de/admin/
```

The admin panel allows administrators to manage:

- users
- quizzes
- questions
- outstanding JWT tokens
- blacklisted JWT tokens

Questions can be edited directly within their associated quiz through the Django admin interface.

---

## Postman Testing

The backend API was tested with Postman using happy-path and unhappy-path scenarios.

Recommended collection structure:

```text
Quizly Backend API
├── happy-path
│   ├── Authentication
│   └── Quizzes
│
└── unhappy-path
    ├── Authentication
    └── Quizzes
```

### Authentication Tests

- Register a valid user
- Login with valid credentials
- Refresh the access token
- Logout an authenticated user
- Register with missing fields
- Register with an existing username
- Register with an existing email address
- Login with invalid credentials
- Refresh without a refresh cookie
- Logout without authentication

### Quiz Tests

- Generate a quiz from a valid YouTube URL
- Get all quizzes
- Get one quiz
- Update title and description
- Delete a quiz
- Submit a missing URL
- Submit an invalid URL
- Submit a non-YouTube URL
- Access quizzes without authentication
- Access another user’s quiz
- Access a non-existing quiz

---

## Production Deployment

The application is deployed on a Google Cloud Ubuntu virtual machine.

### Production Stack

```text
Internet
   ↓
Nginx
   ↓
Gunicorn
   ↓
Django
```

Supervisor keeps the Gunicorn process running.

Nginx serves:

```text
/          → Static frontend
/api/      → Django REST API
/admin/    → Django admin panel
/static/   → Django static files
```

HTTPS is provided by:

- Certbot
- Let’s Encrypt

The deployed URLs are:

```text
Application: https://quizly.ebubekir-elicora.de/
API:         https://quizly.ebubekir-elicora.de/api/
Admin:       https://quizly.ebubekir-elicora.de/admin/
```

FFmpeg is installed globally on the server and must be available in the Gunicorn process PATH.

Example production PATH:

```text
/var/www/projects/quizly/env/bin:/usr/local/bin:/usr/bin:/bin
```

The production Gunicorn process is managed by Supervisor and uses one worker because Whisper and PyTorch require significant memory.

---

## Security Notes

The following files and directories must not be committed:

```text
env/
.env
db.sqlite3
__pycache__/
*.pyc
media/
staticfiles/
```

Recommended `.gitignore`:

```gitignore
env/
.env
db.sqlite3

__pycache__/
*.pyc

media/
staticfiles/

.vscode/
.DS_Store
```

Additional security measures:

- JWT tokens are stored in HttpOnly cookies
- Production cookies use HTTPS
- Secrets are stored in environment variables
- Users cannot access quizzes belonging to other users
- Django debug mode is disabled in production
- Nginx handles HTTPS termination
- The Gemini API key is never exposed to the frontend
- Temporary audio files are deleted after processing

---

## Local Development Workflow

Start the backend:

```bash
cd Quizly
```

Windows:

```bash
env\Scripts\activate
python manage.py runserver
```

Linux or macOS:

```bash
source env/bin/activate
python manage.py runserver
```

Start the provided frontend separately using Live Server.

Backend:

```text
http://127.0.0.1:8000/
```

Frontend:

```text
http://127.0.0.1:5500/
```

The local frontend API base URL must be:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000/api/";
```

---

## Notes for Reviewers

This repository contains the custom Django REST backend.

The provided frontend is deployed together with the backend on the production server but is maintained separately from this repository.

The backend is responsible for:

- registration and authentication
- JWT cookie management
- token refreshing and blacklisting
- YouTube URL validation and normalization
- YouTube audio download
- FFmpeg audio processing
- Whisper transcription
- Gemini quiz generation
- AI response cleanup and validation
- database persistence
- quiz ownership validation
- CRUD operations
- API permissions
- administration

Users can only access, edit, and delete their own quizzes.

Foreign quiz access returns:

```text
403 Forbidden
```

Missing quizzes return:

```text
404 Not Found
```

Invalid quiz creation input returns:

```text
400 Bad Request
```

Successful quiz creation returns:

```text
201 Created
```