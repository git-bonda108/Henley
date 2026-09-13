"""Fetch home design URLs — live, no cache."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)[:25_000]


def fetch_url(url: str) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if tavily_key:
        return _fetch_tavily(url, tavily_key)

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": "BuilderQuoteAgent/1.0"})
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return {"url": url, "text": resp.text[:25_000], "title": url}
        text = _clean_html(resp.text)
        title = BeautifulSoup(resp.text, "lxml").title
        return {
            "url": url,
            "text": text,
            "title": title.string.strip() if title and title.string else url,
        }


def _fetch_tavily(url: str, api_key: str) -> dict[str, Any]:
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            "https://api.tavily.com/extract",
            json={"urls": [url], "include_images": False},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        if not results:
            raise ValueError(f"Tavily returned no content for {url}")
        r0 = results[0]
        return {
            "url": url,
            "text": (r0.get("raw_content") or r0.get("content") or "")[:25_000],
            "title": r0.get("title") or url,
        }
