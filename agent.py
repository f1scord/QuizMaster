# agent module — talks to the ai api to generate flashcards
# uses json serialization (2 pts) and requests for http

import json
import os
import re

from deck import FlashCard
from exceptions import ApiError

# default settings for openrouter api (openai-compatible)
DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

# prompt template telling the ai exactly what format we want
PROMPT = (
    "you generate study flashcards from lecture material.\n"
    "return ONLY a json array. no extra text. no markdown fences.\n"
    'each item must have: {"front": str, "back": str, "topic": str, "difficulty": "easy"|"medium"|"hard"}\n'
    "generate 8-12 cards from this text:\n"
)


class CardGenerator:
    """handles api calls to generate flashcards from text"""

    def __init__(self, api_key: str = "", api_url: str = "", model: str = ""):
        self.api_key = api_key
        self.api_url = api_url or os.environ.get("LLM_API_URL", DEFAULT_URL)
        self.model = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)

    def generate(self, text: str) -> list[FlashCard]:
        # check we have a key before wasting time
        if not self.api_key:
            raise ApiError("No API key set. Click the Key button to add one.")
        # limit text length so we dont hit token limits
        excerpt = text[:6000]
        return self._call_api(excerpt)

    def _call_api(self, text: str) -> list[FlashCard]:
        try:
            import requests
        except ModuleNotFoundError:
            raise ApiError("requests not installed. run: pip install requests")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Flashcards AI",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": PROMPT + text}],
            "temperature": 0.7,
        }

        try:
            resp = requests.post(
                self.api_url, headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
        except requests.Timeout:
            raise ApiError("API request timed out. Check your internet.")
        except requests.HTTPError as e:
            raise ApiError(
                f"API error {e.response.status_code}: {e.response.text[:200]}"
            )
        except requests.RequestException as e:
            raise ApiError(f"Network error: {e}")

        # parse the json response
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # sometimes models wrap json in markdown fences, strip them
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()

        if not raw:
            raise ApiError("API returned empty response.")

        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ApiError(f"API returned bad JSON: {e}\n\n{raw[:300]}")

        # build flashcard objects from the parsed json
        cards = []
        for item in items:
            if "front" in item and "back" in item:
                cards.append(
                    FlashCard(
                        front=item["front"],
                        back=item["back"],
                        topic=item.get("topic", "general"),
                        difficulty=item.get("difficulty", "medium"),
                    )
                )
        return cards
