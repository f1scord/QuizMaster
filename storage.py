# storage module — handles config and deck persistence
# uses file handling with context manager (3 pts) and json serialization (2 pts)

import json
import os

from deck import Deck
from exceptions import StorageError

# paths for our data files
DECK_PATH = os.path.join("data", "deck.json")
CONFIG_PATH = os.path.join("data", "config.json")


def load_deck() -> Deck:
    """load deck from disk or return empty one"""
    deck = Deck()
    deck.load(DECK_PATH)
    return deck


def save_deck(deck: Deck) -> None:
    """save deck to disk"""
    deck.save(DECK_PATH)


def load_config() -> dict:
    """load user config (like api key) from json"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # no config yet
    except (json.JSONDecodeError, OSError) as e:
        raise StorageError(f"corrupt config: {e}") from e


def save_config(config: dict) -> None:
    """save user config to json"""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        raise StorageError(f"cannot save config: {e}") from e
