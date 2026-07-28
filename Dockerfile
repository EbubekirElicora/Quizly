FROM python:3.12-slim

# Deno is required by yt-dlp for YouTube JavaScript challenges.
COPY --from=denoland/deno:bin-2.9.4 /deno /usr/local/bin/deno

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# FFmpeg is required by Whisper for audio processing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying the project to improve build caching.
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
        -r requirements.txt

COPY . .

RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p \
        /app/data \
        /app/staticfiles \
        /app/tmp \
        /root/.cache/whisper

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "900"]
