"""ImageKit hosting for sneak-peek GIFs (same account, folder convention and cache key as loomgif).

URL shape: https://ik.imagekit.io/motiontheagency/outreach/sneakpeek-gif/<prefix>-sp-<domain>.gif?v=<sha1[:12]>
The ?v= key is a hash of the file's bytes: an overwrite keeps the path, and the CDN would go on
serving the old bytes without it.
"""
import hashlib
import os

UPLOAD_ENDPOINT = "https://upload.imagekit.io/api/v1/files/upload"
DEFAULT_FOLDER = "/outreach/sneakpeek-gif"


def content_key(path, length=12):
    h = hashlib.sha1()  # noqa: S324 - cache key, not security
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def configured():
    return bool(os.environ.get("IMAGEKIT_PRIVATE_KEY")) and bool(os.environ.get("IMAGEKIT_URL_ENDPOINT"))


def upload(path, file_name, folder=None):
    """Upload (overwrite, stable name) and return the versioned public URL."""
    import requests

    key = os.environ.get("IMAGEKIT_PRIVATE_KEY", "")
    if not key:
        raise RuntimeError("IMAGEKIT_PRIVATE_KEY is not set (.env)")
    folder = folder or os.environ.get("SNEAKPEEK_IMAGEKIT_FOLDER", DEFAULT_FOLDER)
    with open(path, "rb") as fh:
        r = requests.post(UPLOAD_ENDPOINT, auth=(key, ""), timeout=300,
                          files={"file": (file_name, fh, "image/gif")},
                          data={"fileName": file_name, "folder": folder, "useUniqueFileName": "false", "overwriteFile": "true"})
    if r.status_code >= 400:
        raise RuntimeError(f"ImageKit upload failed [{r.status_code}]: {r.text[:300]}")
    url = r.json()["url"]
    return f"{url}{'&' if '?' in url else '?'}v={content_key(path)}"


def check(url):
    """HTTP status of a hosted URL (200 means a prospect would see it)."""
    import requests

    try:
        return requests.head(url, timeout=30, allow_redirects=True).status_code
    except Exception:
        return 0
