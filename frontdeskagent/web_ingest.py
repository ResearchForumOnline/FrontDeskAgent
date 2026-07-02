from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

import requests


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str):
        text = " ".join(data.split())
        if not text or self.skip_depth:
            return
        if self._in_title:
            self.title = text
        elif len(text) > 2:
            self.parts.append(text)


def import_url(url: str, max_chars: int = 12000) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must start with http:// or https://")
    response = requests.get(url, timeout=15, headers={"User-Agent": "FrontDeskAgent/1.0 (+https://frontdeskagent.online/)"})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise ValueError(f"URL did not return HTML: {content_type or 'unknown content type'}")
    parser = TextExtractor()
    parser.feed(response.text[: max_chars * 4])
    body = "\n".join(parser.parts)
    body = body[:max_chars]
    title = parser.title or parsed.netloc
    return {"title": title, "body": body, "tags": f"website,{parsed.netloc}", "url": url}
