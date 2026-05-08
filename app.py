# app module — main application with navigation
# ties everything together: generate, deck, study

import os

import customtkinter as ctk

from deck import Deck
from screens import ApiKeyDialog, DeckScreen, GenerateScreen, StudyScreen
from storage import load_config, load_deck, save_config, save_deck

# ── theme setup ───────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── colors: black + mint ──────────────────────────────────────
BG = "#0a0a0a"
SURFACE = "#111111"
CARD = "#181818"
BORDER = "#252525"
MINT = "#3dd68c"
MINT_HOVER = "#2db46d"
TEXT = "#f0f0f0"
MUTED = "#666666"
FONT = "Segoe UI"
NAV_H = 44


class App:
    """main app class — manages window, navigation and data"""

    def __init__(self):
        # create main window
        self.root = ctk.CTk()
        self.root.title("Flashcards AI")
        self.root.geometry("620x460")
        self.root.minsize(500, 380)
        self.root.configure(fg_color=BG)
        self.root.resizable(True, True)

        # load data
        self.deck: Deck = load_deck()
        self._cfg = load_config()
        self._api_key = self._load_api_key()
        self._api_url = self._cfg.get("api_url", "")
        self._current_screen = None
        self._nav_btns: dict = {}

        # build ui
        self._build_nav()
        self._frame = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self._frame.pack(fill="both", expand=True)

        # show generate screen first
        self._show_generate()

        # prompt for api key if missing
        if not self._api_key:
            ApiKeyDialog(
                self.root,
                current_key="",
                current_url=self._api_url,
                on_save=self._save_key,
            )

    # ── api key handling ──────────────────────────────────────

    def _load_api_key(self) -> str:
        # try .env file first, then env vars, then config file
        self._load_dotenv()
        env = os.environ.get("LLM_API_KEY", "") or os.environ.get("API_KEY", "")
        return env if env else load_config().get("api_key", "")

    def _load_dotenv(self) -> None:
        # load key=value pairs from .env file into os.environ
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.isfile(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val

    def _save_key(self, key: str, url: str = "") -> None:
        self._api_key = key
        self._api_url = url
        cfg = load_config()
        cfg["api_key"] = key
        if url:
            cfg["api_url"] = url
        save_config(cfg)
        # update current screen if it needs the key
        if self._current_screen and hasattr(self._current_screen, "set_api_key"):
            self._current_screen.set_api_key(key)
        if self._current_screen and hasattr(self._current_screen, "set_api_url"):
            self._current_screen.set_api_url(url)

    # ── navigation bar ────────────────────────────────────────

    def _build_nav(self) -> None:
        nav = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0, height=NAV_H)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        # separator line
        ctk.CTkFrame(self.root, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x"
        )

        # logo
        ctk.CTkLabel(
            nav,
            text="◆",
            font=(FONT, 16),
            text_color=MINT,
            fg_color=CARD,
            corner_radius=6,
            width=30,
            height=30,
        ).pack(side="left", padx=(12, 4), pady=6)

        # nav buttons
        for name, cmd in [
            ("Generate", self._show_generate),
            ("Deck", self._show_deck),
            ("Study", self._show_study),
        ]:
            b = ctk.CTkButton(
                nav,
                text=name,
                command=cmd,
                width=80,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color=CARD,
                text_color=MUTED,
                font=(FONT, 11),
                border_width=0,
            )
            b.pack(side="left", padx=2, pady=8)
            self._nav_btns[name] = b

    def _set_active(self, name: str) -> None:
        # highlight active tab
        for n, b in self._nav_btns.items():
            if n == name:
                b.configure(fg_color=CARD, text_color=MINT, font=(FONT, 11, "bold"))
            else:
                b.configure(fg_color="transparent", text_color=MUTED, font=(FONT, 11))

    # ── screen switching ────────────────────────────────────────

    def navigate(self, screen) -> None:
        # switch to a new screen
        if self._current_screen is not None:
            self._current_screen.pack_forget()
        self._current_screen = screen
        screen.pack(in_=self._frame, fill="both", expand=True)

    def _show_generate(self) -> None:
        s = GenerateScreen(
            self._frame,
            api_key=self._api_key,
            api_url=self._api_url,
            on_cards_added=self._cards_added,
            on_key_change=self._save_key,
        )
        self.navigate(s)
        self._set_active("Generate")

    def _show_deck(self) -> None:
        s = DeckScreen(self._frame, self.deck, on_delete=self._save)
        self.navigate(s)
        self._set_active("Deck")

    def _show_study(self) -> None:
        s = StudyScreen(self._frame, self.deck, on_done=self._show_deck)
        self.navigate(s)
        self._set_active("Study")
        s.start()

    # ── data handling ─────────────────────────────────────────

    def _cards_added(self, cards: list) -> None:
        # add generated cards to deck and save
        for c in cards:
            self.deck.add(c)
        self._save()

    def _save(self) -> None:
        # persist deck to disk
        save_deck(self.deck)

    def run(self) -> None:
        # start the app
        self.root.mainloop()
