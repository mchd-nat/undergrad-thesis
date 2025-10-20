import urllib.robotparser
from urllib.parse import urlparse, urljoin

def check_permission(url, user_agent="*"):    # checks if the target website allows web crawlers
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(base, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        return False
    return rp.can_fetch(user_agent, url)