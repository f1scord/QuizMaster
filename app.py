import os
import tkinter as tk
import traceback
from tkinter import ttk, messagebox

from deck import Deck
from screens import ApiKeyDialog, DeckScreen, GenerateScreen, QuizScreen, StudyScreen
from storage import load_config, load_deck, save_config, save_deck

BG     = "#111118"
NAV_BG = "#16161f"
FG     = "#e6e6f0"
ACCENT = "#7b7fff"
MUTED  = "#6a6a8a"
FONT   = "Segoe UI"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuizMaster")
        self.root.geometry("640x590")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        _apply_scrollbar_theme(self.root)

        self.deck: Deck = load_deck()
        self._api_key = self._load_api_key()
        self._current_screen = None
        self._nav_btns = {}

        self._build_nav()
        self._show_generate()

        if not self._api_key:
            ApiKeyDialog(self.root, current_key="", on_save=self._save_key)

    def _load_api_key(self) -> str:
        env = os.environ.get("LLM_API_KEY", "") or os.environ.get("API_KEY", "")
        return env if env else load_config().get("api_key", "")

    def _save_key(self, key: str) -> None:
        self._api_key = key
        cfg = load_config()
        cfg["api_key"] = key
        save_config(cfg)
        if self._current_screen and hasattr(self._current_screen, "set_api_key"):
            self._current_screen.set_api_key(key)

    def _build_nav(self) -> None:
        nav = tk.Frame(self.root, bg=NAV_BG, height=46)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        sep = tk.Frame(self.root, bg="#2a2a3f", height=1)
        sep.pack(fill="x")

        for name, cmd in [("Generate", self._show_generate),
                          ("Deck", self._show_deck),
                          ("Quiz", self._show_quiz),
                          ("Study", self._show_study)]:
            b = tk.Button(nav, text=name, command=cmd,
                          bg=NAV_BG, fg=MUTED, relief="flat",
                          font=(FONT, 11), padx=20, pady=10,
                          cursor="hand2", bd=0,
                          activebackground=NAV_BG,
                          activeforeground=ACCENT,
                          highlightthickness=0)
            b.pack(side="left")
            self._nav_btns[name] = b

    def _set_active(self, name: str) -> None:
        for n, b in self._nav_btns.items():
            b.configure(fg=ACCENT if n == name else MUTED,
                        font=(FONT, 11, "bold" if n == name else "normal"))

    def _switch(self, screen: tk.Frame) -> None:
        if self._current_screen:
            self._current_screen.pack_forget()
        self._current_screen = screen
        screen.pack(fill="both", expand=True)

    def _show_generate(self) -> None:
        try:
            s = GenerateScreen(self.root, api_key=self._api_key,
                               on_cards_added=self._cards_added,
                               on_study=self._show_study,
                               on_key_change=self._save_key)
            self._switch(s)
            self._set_active("Generate")
        except Exception:
            messagebox.showerror("Error", traceback.format_exc())

    def _show_deck(self) -> None:
        try:
            s = DeckScreen(self.root, self.deck, on_delete=self._save)
            self._switch(s)
            self._set_active("Deck")
        except Exception:
            messagebox.showerror("Error", traceback.format_exc())

    def _show_quiz(self) -> None:
        try:
            from quiz import QuizEngine
            engine = QuizEngine()
            s = QuizScreen(self.root, engine=engine)
            self._switch(s)
            self._set_active("Quiz")
        except Exception:
            messagebox.showerror("Error", traceback.format_exc())

    def _show_study(self) -> None:
        try:
            s = StudyScreen(self.root, self.deck, on_done=self._show_deck)
            self._switch(s)
            self._set_active("Study")
            s.start()
        except Exception:
            messagebox.showerror("Error", traceback.format_exc())

    def _cards_added(self, cards: list) -> None:
        for c in cards:
            self.deck.add(c)
        self._save()

    def _save(self) -> None:
        save_deck(self.deck)

    def run(self) -> None:
        self.root.mainloop()


def _apply_scrollbar_theme(root: tk.Tk) -> None:
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("Vertical.TScrollbar",
                background="#252535", troughcolor="#1c1c28",
                arrowcolor="#6a6a8a", bordercolor="#111118")
