import random
import string
from django.db.models import Exists, OuterRef
from .models import Link

ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9

def generate_short_code(length: int = 7) -> str:
    """
    Генерирует уникальный short_code длиной length
    """
    while True:
        code = "".join(random.choice(ALPHABET) for _ in range(length))
        exists = Link.objects.filter(short_code=code).only("id").exists()
        if not exists:
            return code

def detect_device(ua: str) -> tuple[str, str, str]:
    """
    device_type, os, browser
    """
    ua_l = (ua or "").lower()
    device = "phone" if "mobile" in ua_l or "iphone" in ua_l or "android" in ua_l else "pc"
    if "windows" in ua_l:
        os = "Windows"
    elif "mac os" in ua_l or "macintosh" in ua_l:
        os = "macOS"
    elif "android" in ua_l:
        os = "Android"
    elif "linux" in ua_l:
        os = "Linux"
    else:
        os = ""

    if "chrome" in ua_l and "safari" in ua_l:
        browser = "Chrome"
    elif "safari" in ua_l and "chrome" not in ua_l:
        browser = "Safari"
    elif "firefox" in ua_l:
        browser = "Firefox"
    elif "edge" in ua_l:
        browser = "Edge"
    else:
        browser = ""
    return device, os, browser