from urllib.parse import parse_qs, urlparse


def get_video_id_from_query(parsed_url):
    """
    Extract the video ID from a standard YouTube watch URL.

    Standard YouTube links store the video ID in the `v` query parameter,
    for example:

    `https://www.youtube.com/watch?v=VIDEO_ID`

    The parsed URL is inspected with `parse_qs()`, which returns every query
    parameter as a list of values.

    Args:
        parsed_url: A parsed URL object returned by `urlparse()`.

    Returns:
        str | None: The first video ID from the `v` query parameter,
            or `None` when the parameter is missing.
    """
    query_params = parse_qs(parsed_url.query)
    video_ids = query_params.get("v")

    if not video_ids:
        return None

    return video_ids[0]


def get_video_id_from_path(parsed_url):
    """
    Extract the video ID from a supported YouTube URL path.

    This function handles YouTube links where the video ID is stored in the
    URL path instead of the query parameters.

    Supported examples include:

    - `https://youtu.be/VIDEO_ID`
    - `https://www.youtube.com/embed/VIDEO_ID`
    - `https://www.youtube.com/shorts/VIDEO_ID`

    Args:
        parsed_url: A parsed URL object returned by `urlparse()`.

    Returns:
        str | None: The extracted video ID, or `None` when the URL path does
            not match a supported YouTube format.
    """
    path_parts = parsed_url.path.strip("/").split("/")

    if parsed_url.netloc == "youtu.be" and path_parts:
        return path_parts[0]

    if path_parts and path_parts[0] in ["embed", "shorts"]:
        return path_parts[1] if len(path_parts) > 1 else None

    return None


def extract_youtube_video_id(url):
    """
    Extract a video ID from a supported YouTube URL.

    The supplied URL is parsed with `urlparse()`. Before extracting the video
    ID, the hostname is checked against the supported YouTube domains.

    Standard watch URLs are processed through `get_video_id_from_query()`.
    Short, embedded, and Shorts URLs are processed through
    `get_video_id_from_path()`.

    Args:
        url: The YouTube URL submitted by the user.

    Returns:
        str | None: The extracted YouTube video ID, or `None` when the domain
            is valid but no supported video ID can be found.

    Raises:
        ValueError: If the URL does not belong to an allowed YouTube domain.
    """
    parsed_url = urlparse(url)
    allowed_hosts = ["www.youtube.com", "youtube.com", "youtu.be"]

    if parsed_url.netloc not in allowed_hosts:
        raise ValueError("Only YouTube URLs are allowed.")

    return get_video_id_from_query(parsed_url) or get_video_id_from_path(
        parsed_url
    )


def normalize_youtube_url(url):
    """
    Validate a YouTube URL and return its canonical watch-URL format.

    The video ID is extracted through `extract_youtube_video_id()`. Supported
    URL formats are normalized into the standard format expected by the
    quiz-generation service:

    `https://www.youtube.com/watch?v=VIDEO_ID`

    Args:
        url: The YouTube URL submitted by the user.

    Returns:
        str: A normalized YouTube watch URL.

    Raises:
        ValueError: If the URL is not from YouTube or does not contain a valid
            video ID in a supported format.
    """
    video_id = extract_youtube_video_id(url)

    if not video_id:
        raise ValueError("Invalid YouTube video URL.")

    return f"https://www.youtube.com/watch?v={video_id}"