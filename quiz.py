from __future__ import annotations
import json, random, re
from dataclasses import dataclass, field
from datetime import date
from exceptions import StorageError

QUESTIONS_PATH = "data/mad_questions.json"
PROGRESS_PATH  = "data/quiz_progress.json"


@dataclass
class Question:
    id: str
    year: str
    topic: str
    question: str
    options: dict          # {"a": "...", "b": "...", "c": "..."}
    correct: list[str]     # e.g. ["a", "c"] or [] for "no answer"
    explanation: str
    mastery: int = 0       # 0=unseen, 1-2=learning, 3+=known
    streak: int = 0
    attempts: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "mastery": self.mastery,
            "streak": self.streak, "attempts": self.attempts
        }

    @property
    def status(self) -> str:
        if self.mastery == 0: return "unseen"
        if self.mastery >= 3: return "known"
        return "learning"

    def check(self, selected: list[str]) -> bool:
        """Return True if selected matches correct exactly."""
        return set(selected) == set(self.correct)

    def update(self, correct: bool) -> None:
        self.attempts += 1
        if correct:
            self.streak += 1
            self.mastery = min(self.mastery + 1, 5)
        else:
            self.streak = 0
            self.mastery = max(self.mastery - 1, 0)


class QuizEngine:
    # Loaded from meta.mock_exam_distribution in mad_questions.json (must sum to 20)
    TOPIC_WEIGHTS: dict = {}

    def __init__(self):
        self.questions: list[Question] = []
        self._load_questions()
        self._load_progress()

    def _load_questions(self) -> None:
        try:
            with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.TOPIC_WEIGHTS = data.get("meta", {}).get(
                "mock_exam_distribution", QuizEngine.TOPIC_WEIGHTS
            )
            self.questions = [
                Question(**{k: v for k, v in q.items()
                            if k in Question.__dataclass_fields__})
                for q in data["cards"]
            ]
        except FileNotFoundError:
            self.questions = []
        except (json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"Corrupt questions file: {e}") from e

    def _load_progress(self) -> None:
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                progress = json.load(f)
            index = {q.id: q for q in self.questions}
            for entry in progress.get("cards", []):
                q = index.get(entry["id"])
                if q:
                    q.mastery  = entry.get("mastery", 0)
                    q.streak   = entry.get("streak", 0)
                    q.attempts = entry.get("attempts", 0)
        except FileNotFoundError:
            pass

    def save_progress(self) -> None:
        import os
        os.makedirs("data", exist_ok=True)
        data = {"cards": [q.to_dict() for q in self.questions]}
        try:
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise StorageError(f"Cannot save quiz progress: {e}") from e

    def learn_queue(self, topic: str = "all") -> list[Question]:
        """
        Returns questions sorted for learn mode.
        Priority: learning > unseen > known.
        Uses lambda for sort key.
        """
        pool = self.questions if topic == "all" else [
            q for q in self.questions if q.topic == topic
        ]
        priority = lambda q: (0 if q.status == "learning"
                              else 1 if q.status == "unseen"
                              else 2)
        return sorted(pool, key=priority)

    def mock_exam(self) -> list[Question]:
        """
        Generate a 20-question mock exam matching real exam topic distribution.
        Uses generator expression + lambda for filtering.
        """
        exam: list[Question] = []
        for topic, count in self.TOPIC_WEIGHTS.items():
            pool = list(filter(lambda q: q.topic == topic, self.questions))
            weak_first = sorted(pool, key=lambda q: q.mastery)
            exam.extend(weak_first[:count])
        random.shuffle(exam)
        return exam[:20]

    def stats(self) -> dict:
        total    = len(self.questions)
        known    = sum(1 for q in self.questions if q.status == "known")
        learning = sum(1 for q in self.questions if q.status == "learning")
        unseen   = sum(1 for q in self.questions if q.status == "unseen")
        by_topic = {
            t: {"total": 0, "known": 0}
            for t in {q.topic for q in self.questions}
        }
        for q in self.questions:
            by_topic[q.topic]["total"] += 1
            if q.status == "known":
                by_topic[q.topic]["known"] += 1
        return {
            "total": total, "known": known,
            "learning": learning, "unseen": unseen,
            "by_topic": by_topic
        }

    def search(self, query: str) -> list[Question]:
        """Regex search over question text and options."""
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        return [
            q for q in self.questions
            if pattern.search(q.question)
            or any(pattern.search(v) for v in q.options.values())
        ]

    def weak_topics(self) -> list[str]:
        """Return topics sorted by mastery (worst first)."""
        by_topic = self.stats()["by_topic"]
        ratio    = lambda t: by_topic[t]["known"] / max(by_topic[t]["total"], 1)
        return sorted(by_topic.keys(), key=ratio)
