# deck module — stores flashcards and handles saving/loading
# uses classes (3 pts), collections (2 pts), comprehensions (2 pts)

import json
import re
import uuid
from datetime import datetime

from decorators import log_action
from exceptions import StorageError


class FlashCard:
    """single flashcard with front, back, topic and difficulty"""

    def __init__(
        self,
        front: str,
        back: str,
        topic: str = "general",
        difficulty: str = "medium",
        card_id: str = None,
    ):
        self.id = card_id or str(uuid.uuid4())  # unique id for each card
        self.front = front
        self.back = back
        self.topic = topic
        self.difficulty = difficulty  # easy | medium | hard
        self.status = "new"  # new | known | review
        self.times_reviewed = 0
        self.correct_answers = 0
        self.created_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        # convert card to dictionary for json saving
        return {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "status": self.status,
            "times_reviewed": self.times_reviewed,
            "correct_answers": self.correct_answers,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlashCard":
        # rebuild card from dictionary loaded from json
        card = cls(
            front=data["front"],
            back=data["back"],
            topic=data.get("topic", "general"),
            difficulty=data.get("difficulty", "medium"),
            card_id=data.get("id"),
        )
        card.status = data.get("status", "new")
        card.times_reviewed = data.get("times_reviewed", 0)
        card.correct_answers = data.get("correct_answers", 0)
        card.created_at = data.get("created_at", card.created_at)
        return card


class Deck:
    """collection of flashcards with search and stats"""

    def __init__(self):
        # dictionary is fast for lookup by id
        self.cards: dict[str, FlashCard] = {}

    def add(self, card: FlashCard) -> None:
        # add a new card to the deck
        self.cards[card.id] = card

    def remove(self, card_id: str) -> None:
        # delete card by id
        if card_id in self.cards:
            del self.cards[card_id]

    def search(self, query: str) -> list[FlashCard]:
        # regex search in front, back or topic
        pattern = re.compile(query, re.IGNORECASE)
        return [
            c
            for c in self.cards.values()
            if pattern.search(c.front)
            or pattern.search(c.back)
            or pattern.search(c.topic)
        ]

    def due_cards(self):
        # generator — yields cards that are not fully known yet
        # this is a generator function (2 pts)
        for card in self.cards.values():
            if card.status != "known":
                yield card

    def mark(self, card_id: str, knew_it: bool) -> None:
        # update card status after review
        if card_id not in self.cards:
            return
        card = self.cards[card_id]
        card.times_reviewed += 1
        if knew_it:
            card.correct_answers += 1
            card.status = "known"
        else:
            card.status = "review"

    def stats(self) -> dict:
        # simple stats about the deck
        total = len(self.cards)
        known = sum(1 for c in self.cards.values() if c.status == "known")
        review = sum(1 for c in self.cards.values() if c.status == "review")
        new_cards = sum(1 for c in self.cards.values() if c.status == "new")
        # dict comprehension for topic counts
        by_topic = {
            t: sum(1 for c in self.cards.values() if c.topic == t)
            for t in {c.topic for c in self.cards.values()}
        }
        return {
            "total": total,
            "known": known,
            "review": review,
            "new": new_cards,
            "by_topic": by_topic,
        }

    @log_action
    def save(self, path: str) -> None:
        # save deck to json file using context manager
        try:
            import os

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    [c.to_dict() for c in self.cards.values()],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError as e:
            raise StorageError(f"cannot save deck: {e}") from e

    def load(self, path: str) -> None:
        # load deck from json file using context manager
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # dict comprehension to rebuild cards
            self.cards = {d["id"]: FlashCard.from_dict(d) for d in data}
        except FileNotFoundError:
            pass  # no deck yet, start empty
        except (json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"corrupt deck file: {e}") from e
