from urllib.parse import parse_qs, urlparse


def get_video_id_from_query(parsed_url):
    """Extracts the video id from a YouTube watch URL."""

    query_params = parse_qs(parsed_url.query)
    video_ids = query_params.get("v")

    if not video_ids:
        return None

    return video_ids[0]


def get_video_id_from_path(parsed_url):
    """Extracts the video id from short, embed, or shorts URLs."""

    path_parts = parsed_url.path.strip("/").split("/")

    if parsed_url.netloc == "youtu.be" and path_parts:
        return path_parts[0]

    if path_parts and path_parts[0] in ["embed", "shorts"]:
        return path_parts[1] if len(path_parts) > 1 else None

    return None


def extract_youtube_video_id(url):
    """Extracts a YouTube video id from supported URL formats."""

    parsed_url = urlparse(url)
    allowed_hosts = ["www.youtube.com", "youtube.com", "youtu.be"]

    if parsed_url.netloc not in allowed_hosts:
        raise ValueError("Only YouTube URLs are allowed.")

    return get_video_id_from_query(parsed_url) or get_video_id_from_path(
        parsed_url
    )


def normalize_youtube_url(url):
    """Returns a canonical YouTube watch URL."""

    video_id = extract_youtube_video_id(url)

    if not video_id:
        raise ValueError("Invalid YouTube video URL.")

    return f"https://www.youtube.com/watch?v={video_id}"