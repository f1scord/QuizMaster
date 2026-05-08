# screens module — all ui screens for the app
# uses tkinter for gui, customtkinter for modern look

import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from deck import FlashCard
from exceptions import FileNotSupportedError

# ── color palette: black + mint ─────────────────────────────
BG = "#0a0a0a"
SURFACE = "#111111"
CARD = "#181818"
BORDER = "#252525"
MINT = "#3dd68c"
MINT_HOVER = "#2db46d"
TEXT = "#f0f0f0"
MUTED = "#666666"
RED = "#ff5555"
YELLOW = "#f0c040"
FONT = "Segoe UI"


# ── helper functions ──────────────────────────────────────────


def _primary_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=MINT,
        hover_color=MINT_HOVER,
        text_color=BG,
        font=(FONT, 11, "bold"),
        corner_radius=8,
        height=32,
    )


def _secondary_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=CARD,
        hover_color=BORDER,
        text_color=TEXT,
        font=(FONT, 10),
        corner_radius=8,
        height=28,
    )


def _danger_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color="#2a1515",
        hover_color="#3d2020",
        text_color=RED,
        font=(FONT, 10),
        corner_radius=6,
        height=24,
        width=70,
        border_width=1,
        border_color="#3d2020",
    )


# ═══════════════════════════════════════════════════════════════
#  API KEY DIALOG
# ═══════════════════════════════════════════════════════════════


class ApiKeyDialog(ctk.CTkToplevel):
    """small popup to enter or update the api key and url"""

    def __init__(
        self, master, current_key: str = "", current_url: str = "", on_save=None
    ):
        super().__init__(master)
        self.title("API Settings")
        self.geometry("400x220")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.on_save = on_save
        self._build(current_key, current_url)

    def _build(self, current_key, current_url):
        ctk.CTkLabel(self, text="API Key:", text_color=MUTED, font=(FONT, 10)).pack(
            anchor="w", padx=20, pady=(12, 2)
        )

        self.key_entry = ctk.CTkEntry(
            self,
            width=340,
            height=28,
            corner_radius=6,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            show="*",
        )
        self.key_entry.insert(0, current_key)
        self.key_entry.pack(pady=2)

        ctk.CTkLabel(
            self,
            text="API URL (optional — leave blank for OpenRouter):",
            text_color=MUTED,
            font=(FONT, 10),
        ).pack(anchor="w", padx=20, pady=(8, 2))

        self.url_entry = ctk.CTkEntry(
            self,
            width=340,
            height=28,
            corner_radius=6,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
        )
        self.url_entry.insert(0, current_url)
        self.url_entry.pack(pady=2)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=14)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save,
            fg_color=MINT,
            hover_color=MINT_HOVER,
            text_color=BG,
            font=(FONT, 10, "bold"),
            corner_radius=8,
            width=90,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=MUTED,
            font=(FONT, 10),
            corner_radius=8,
            width=90,
        ).pack(side="left", padx=6)

    def _save(self):
        key = self.key_entry.get().strip()
        url = self.url_entry.get().strip()
        if self.on_save:
            self.on_save(key, url)
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  GENERATE SCREEN
# ═══════════════════════════════════════════════════════════════


class GenerateScreen(ctk.CTkFrame):
    """screen where user pastes text and generates flashcards with ai"""

    def __init__(
        self,
        master,
        api_key: str = "",
        api_url: str = "",
        on_cards_added=None,
        on_key_change=None,
    ):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.api_key = api_key
        self.api_url = api_url
        self.on_cards_added = on_cards_added
        self.on_key_change = on_key_change
        self._build()

    def set_api_key(self, key: str):
        self.api_key = key

    def set_api_url(self, url: str):
        self.api_url = url

    def _build(self):
        # header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header, text="Generate Flashcards", text_color=TEXT, font=(FONT, 16, "bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Key",
            width=50,
            height=24,
            command=self._open_key_dialog,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=MUTED,
            font=(FONT, 9),
            corner_radius=6,
        ).pack(side="right")

        # instruction
        ctk.CTkLabel(
            self,
            text="Paste your lecture notes or open a file, then click Generate.",
            text_color=MUTED,
            font=(FONT, 10),
        ).pack(anchor="w", padx=16)

        # text area
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=SURFACE,
            text_color=TEXT,
            border_color=BORDER,
            corner_radius=10,
            font=(FONT, 11),
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=16, pady=8)

        # bottom buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        _secondary_btn(btn_row, "Open File", self._open_file).pack(
            side="left", padx=(0, 6)
        )
        self.gen_btn = _primary_btn(btn_row, "Generate", self._generate)
        self.gen_btn.pack(side="left")

        # status label
        self.status = ctk.CTkLabel(self, text="", text_color=MUTED, font=(FONT, 10))
        self.status.pack(anchor="w", padx=16, pady=(0, 8))

    def _open_key_dialog(self):
        ApiKeyDialog(
            self,
            current_key=self.api_key,
            current_url=self.api_url,
            on_save=self.on_key_change,
        )

    def _open_file(self):
        # open file dialog and read text
        path = filedialog.askopenfilename(
            title="Select file",
            filetypes=[("Supported files", "*.pdf *.docx *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            from parser import parse_file

            text = parse_file(path)
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", text)
            self.status.configure(text=f"Loaded: {path.split('/')[-1]}")
        except FileNotSupportedError as e:
            self.status.configure(text=str(e), text_color=RED)

    def _generate(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            self.status.configure(text="Paste some text first!", text_color=RED)
            return

        self.status.configure(text="Generating... please wait", text_color=YELLOW)
        self.gen_btn.configure(state="disabled")

        # run generation in background so ui doesnt freeze
        import threading

        def worker():
            try:
                from agent import CardGenerator

                gen = CardGenerator(self.api_key, self.api_url)
                cards = gen.generate(text)
                self.after(0, lambda: self._done(cards))
            except Exception as e:
                self.after(0, lambda: self._error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _done(self, cards: list[FlashCard]):
        self.gen_btn.configure(state="normal")
        if not cards:
            self.status.configure(text="No cards generated. Try again.", text_color=RED)
            return
        if self.on_cards_added:
            self.on_cards_added(cards)
        self.status.configure(
            text=f"Generated {len(cards)} cards! Go to Deck or Study.", text_color=MINT
        )
        self.textbox.delete("1.0", "end")

    def _error(self, msg: str):
        self.gen_btn.configure(state="normal")
        self.status.configure(text=msg, text_color=RED)


# ═══════════════════════════════════════════════════════════════
#  DECK SCREEN
# ═══════════════════════════════════════════════════════════════


class DeckScreen(ctk.CTkFrame):
    """screen to browse, search and manage flashcards"""

    def __init__(self, master, deck, on_delete=None):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.deck = deck
        self.on_delete = on_delete
        self._build()

    def _build(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header, text="Your Deck", text_color=TEXT, font=(FONT, 16, "bold")
        ).pack(side="left")

        # search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            width=180,
            height=26,
            corner_radius=6,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            placeholder_text="Search...",
        )
        search.pack(side="right")

        # stats row
        self.stats_label = ctk.CTkLabel(
            self, text="", text_color=MUTED, font=(FONT, 10)
        )
        self.stats_label.pack(anchor="w", padx=16, pady=(0, 4))

        # scrollable card list
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=2)

        self.refresh()

    def refresh(self):
        # clear current list
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip()
        if query:
            cards = self.deck.search(query)
        else:
            cards = list(self.deck.cards.values())

        # sort by status: new first, then review, then known
        # using lambda for sort key (functions + lambda requirement)
        cards = sorted(
            cards,
            key=lambda c: (
                c.status != "new",
                c.status != "review",
                c.status != "known",
            ),
        )

        # update stats
        stats = self.deck.stats()
        self.stats_label.configure(
            text=f"Total: {stats['total']}  |  New: {stats['new']}  |  Review: {stats['review']}  |  Known: {stats['known']}"
        )

        if not cards:
            ctk.CTkLabel(
                self.list_frame,
                text="No cards yet. Go generate some!",
                text_color=MUTED,
                font=(FONT, 11),
            ).pack(pady=30)
            return

        for card in cards:
            self._card_row(card)

    def _card_row(self, card: FlashCard):
        row = ctk.CTkFrame(self.list_frame, fg_color=SURFACE, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        row.configure(height=56)

        # color dot for difficulty
        diff_colors = {"easy": MINT, "medium": YELLOW, "hard": RED}
        dot_color = diff_colors.get(card.difficulty, MUTED)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(
            left,
            text=card.front[:50] + ("..." if len(card.front) > 50 else ""),
            text_color=TEXT,
            font=(FONT, 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        topic_text = f"{card.topic}  •  {card.difficulty}  •  {card.status}"
        ctk.CTkLabel(
            left, text=topic_text, text_color=MUTED, font=(FONT, 9), anchor="w"
        ).pack(anchor="w")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=8, pady=6)

        ctk.CTkLabel(right, text="●", text_color=dot_color, font=(FONT, 12)).pack(
            side="left", padx=(0, 6)
        )

        _danger_btn(right, "Delete", lambda cid=card.id: self._delete(cid)).pack(
            side="left"
        )

    def _delete(self, card_id: str):
        self.deck.remove(card_id)
        if self.on_delete:
            self.on_delete()
        self.refresh()


# ═══════════════════════════════════════════════════════════════
#  STUDY SCREEN
# ═══════════════════════════════════════════════════════════════


class StudyScreen(ctk.CTkFrame):
    """screen to study flashcards one by one"""

    def __init__(self, master, deck, on_done=None):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.deck = deck
        self.on_done = on_done
        self.queue: list[FlashCard] = []
        self.index = 0
        self.showing_back = False
        self._build()

    def _build(self):
        # progress bar at top
        self.progress = ctk.CTkProgressBar(
            self, height=4, corner_radius=2, fg_color=SURFACE, progress_color=MINT
        )
        self.progress.pack(fill="x", padx=16, pady=(12, 2))
        self.progress.set(0)

        self.count_label = ctk.CTkLabel(
            self, text="", text_color=MUTED, font=(FONT, 10)
        )
        self.count_label.pack(anchor="center", pady=(0, 6))

        # card display area
        self.card_frame = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=12,
            border_color=BORDER,
            border_width=1,
        )
        self.card_frame.pack(fill="both", expand=True, padx=16, pady=6)
        self.card_frame.pack_propagate(False)

        self.card_label = ctk.CTkLabel(
            self.card_frame,
            text="",
            text_color=TEXT,
            font=(FONT, 15, "bold"),
            wraplength=500,
            justify="center",
        )
        self.card_label.pack(expand=True)

        # click to flip hint
        self.hint_label = ctk.CTkLabel(
            self.card_frame,
            text="Click card to flip",
            text_color=MUTED,
            font=(FONT, 9),
        )
        self.hint_label.pack(pady=(0, 12))

        # bind click to flip
        self.card_frame.bind("<Button-1>", lambda _: self._flip())
        self.card_label.bind("<Button-1>", lambda _: self._flip())

        # buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 12))

        self.forgot_btn = _danger_btn(btn_row, "Didn't know", self._forgot)
        self.forgot_btn.pack(side="left", padx=(0, 8))

        self.knew_btn = ctk.CTkButton(
            btn_row,
            text="Knew it!",
            command=self._knew,
            fg_color=MINT,
            hover_color=MINT_HOVER,
            text_color=BG,
            font=(FONT, 11, "bold"),
            corner_radius=8,
            height=32,
        )
        self.knew_btn.pack(side="left")

        _secondary_btn(btn_row, "Back to Deck", self._back).pack(side="right")

        # disable buttons until we start
        self.forgot_btn.configure(state="disabled")
        self.knew_btn.configure(state="disabled")

    def start(self):
        # get cards that are not known using generator
        self.queue = list(self.deck.due_cards())
        if not self.queue:
            self.card_label.configure(
                text="All cards learned!\nGenerate more or reset in Deck."
            )
            self.hint_label.configure(text="")
            self.forgot_btn.configure(state="disabled")
            self.knew_btn.configure(state="disabled")
            return

        self.index = 0
        self.showing_back = False
        self._show()

    def _show(self):
        if self.index >= len(self.queue):
            self._finish()
            return

        card = self.queue[self.index]
        self.showing_back = False
        self.card_label.configure(text=card.front)
        self.hint_label.configure(text="Click card to flip")

        # update progress
        self.progress.set(self.index / len(self.queue))
        self.count_label.configure(text=f"Card {self.index + 1} of {len(self.queue)}")

        self.forgot_btn.configure(state="normal")
        self.knew_btn.configure(state="normal")

    def _flip(self):
        if not self.queue or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.showing_back = not self.showing_back
        if self.showing_back:
            self.card_label.configure(text=card.back)
            self.hint_label.configure(text="Click card to flip back")
        else:
            self.card_label.configure(text=card.front)
            self.hint_label.configure(text="Click card to flip")

    def _forgot(self):
        if not self.queue or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.deck.mark(card.id, knew_it=False)
        self.index += 1
        self._show()

    def _knew(self):
        if not self.queue or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.deck.mark(card.id, knew_it=True)
        self.index += 1
        self._show()

    def _finish(self):
        self.progress.set(1.0)
        self.count_label.configure(text="Session complete!")
        self.card_label.configure(text="Great job! You reviewed all due cards.")
        self.hint_label.configure(text="")
        self.forgot_btn.configure(state="disabled")
        self.knew_btn.configure(state="disabled")

    def _back(self):
        if self.on_done:
            self.on_done()
