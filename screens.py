import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from agent import CardGenerator
from deck import FlashCard
from decorators import handle_errors, log_action
from parser import parse_file
from widgets import AnimatedProgress, FlipCard, FONT, RoundedButton, _lighten, _darken


BG      = "#111118"
SURFACE = "#1c1c28"
CARD_S  = "#252535"
BORDER  = "#38384f"
ACCENT  = "#7b7fff"
TEXT    = "#e6e6f0"
MUTED   = "#6a6a8a"
GREEN   = "#4ade80"
RED     = "#f87171"
YELLOW  = "#facc15"
ENTRY   = "#1c1c28"


def _rbtn(parent, text: str, command=None, *,
          primary: bool = False,
          danger: bool = False,
          green: bool = False,
          muted: bool = False,
          min_width: int = 0,
          font_spec=None,
          radius: int = 11,
          padx: int = 18,
          pady: int = 9) -> RoundedButton:
    """Factory for consistently styled RoundedButton instances."""
    if primary:
        bg, fg = ACCENT, "#ffffff"
        fs = font_spec or (FONT, 10, "bold")
    elif danger:
        bg, fg = "#3a1a1a", RED
        fs = font_spec or (FONT, 10)
    elif green:
        bg, fg = "#1a3828", GREEN
        fs = font_spec or (FONT, 10)
    elif muted:
        bg, fg = SURFACE, MUTED
        fs = font_spec or (FONT, 10)
    else:
        bg, fg = SURFACE, TEXT
        fs = font_spec or (FONT, 10)
    return RoundedButton(parent, text=text, command=command,
                         bg=bg, fg=fg, font_spec=fs, radius=radius,
                         min_width=min_width, padx=padx, pady=pady)


class ApiKeyDialog(tk.Toplevel):
    def __init__(self, master, current_key: str = "", on_save=None):
        super().__init__(master)
        self.title("API Key")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._on_save = on_save
        self._build(current_key)
        self.transient(master)
        self.wait_visibility()
        self.focus_force()

    def _build(self, key: str) -> None:
        tk.Label(self, text="LLM API Key", bg=BG, fg=ACCENT,
                 font=(FONT, 15, "bold")).pack(padx=36, pady=(26, 4))
        tk.Label(self, text="paste key from your provider dashboard",
                 bg=BG, fg=MUTED, font=(FONT, 10)).pack(padx=36, pady=(0, 14))

        self._entry = tk.Entry(self, width=50, bg=SURFACE, fg=TEXT,
                               insertbackground=TEXT, font=(FONT, 11),
                               relief="flat", show="•", bd=0,
                               highlightthickness=1, highlightcolor=ACCENT,
                               highlightbackground=BORDER)
        self._entry.pack(padx=36, ipady=8)
        self._entry.insert(0, key)

        show = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Show key", variable=show, bg=BG, fg=MUTED,
                       selectcolor=SURFACE, activebackground=BG,
                       font=(FONT, 10),
                       command=lambda: self._entry.configure(
                           show="" if show.get() else "•")).pack(
            padx=36, pady=6, anchor="w")

        row = tk.Frame(self, bg=BG)
        row.pack(pady=(8, 26))
        cancel = _rbtn(row, "Cancel", self.destroy, min_width=96)
        cancel.pack(side="left", padx=6)
        save = _rbtn(row, "Save", self._save, primary=True, min_width=96)
        save.pack(side="left", padx=6)
        self._entry.bind("<Return>", lambda _: self._save())

    def _save(self) -> None:
        if self._on_save:
            self._on_save(self._entry.get().strip())
        self.destroy()


class AddCardDialog(tk.Toplevel):
    _DECK_PATH = "data/deck.json"

    def __init__(self, master, deck, on_saved=None):
        super().__init__(master)
        self.title("Add card")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._deck = deck
        self._on_saved = on_saved
        self._build()
        self.transient(master)
        self.wait_visibility()
        self.focus_force()

    def _build(self) -> None:
        tk.Label(self, text="Add card", bg=BG, fg=ACCENT,
                 font=(FONT, 15, "bold")).pack(padx=24, pady=(20, 12))

        body = tk.Frame(self, bg=BG)
        body.pack(padx=24, pady=(0, 6), fill="x")

        for label, attr in [("Front", "_front"), ("Back", "_back"), ("Topic", "_topic")]:
            tk.Label(body, text=label, bg=BG, fg=MUTED,
                     font=(FONT, 10)).pack(anchor="w")
            e = tk.Entry(body, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                         font=(FONT, 11), relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.pack(fill="x", ipady=6, pady=(0, 10))
            setattr(self, attr, e)
            e.bind("<Return>", lambda _: self._save())

        row = tk.Frame(self, bg=BG)
        row.pack(pady=(4, 20))
        cancel = _rbtn(row, "Cancel", self.destroy, min_width=96)
        cancel.pack(side="left", padx=6)
        save = _rbtn(row, "Save", self._save, primary=True, min_width=96)
        save.pack(side="left", padx=6)

    def _save(self) -> None:
        front = self._front.get().strip()
        back  = self._back.get().strip()
        topic = self._topic.get().strip()
        if not self._has_required_fields(front, back):
            messagebox.showwarning("Missing fields", "Front and Back are required.")
            return
        card = self._build_manual_card(front=front, back=back, topic=topic)
        self._deck.add(card)
        self._deck.save(self._DECK_PATH)
        self.destroy()
        if self._on_saved:
            self._on_saved()

    @staticmethod
    def _has_required_fields(front: str, back: str) -> bool:
        return bool(front and back)

    @staticmethod
    def _build_manual_card(front: str, back: str, topic: str) -> FlashCard:
        card = FlashCard(front=front, back=back, topic=topic,
                         difficulty="medium", source_file="manual")
        card.status = "new"
        card.times_reviewed = 0
        card.correct_answers = 0
        card.created_at = datetime.now().isoformat(timespec="seconds")
        return card


class GenerateScreen(tk.Frame):
    def __init__(self, master, api_key, on_cards_added, on_study, on_key_change):
        super().__init__(master, bg=BG)
        self._on_cards_added = on_cards_added
        self._on_study = on_study
        self._on_key_change = on_key_change
        self._generator = CardGenerator(api_key)
        self._q: queue.Queue = queue.Queue()
        self._source = "pasted text"
        self._poll_start = 0.0
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="QuizMaster ⚡", bg=BG, fg=ACCENT,
                 font=(FONT, 24, "bold")).pack(pady=(24, 2))
        tk.Label(self, text="Paste lecture text or open a file",
                 bg=BG, fg=MUTED, font=(FONT, 11)).pack(pady=(0, 12))

        self._text = tk.Text(self, height=13, bg=SURFACE, fg=TEXT,
                             insertbackground=TEXT, font=(FONT, 11),
                             relief="flat", padx=12, pady=10,
                             wrap="word", bd=0,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        self._text.pack(fill="x", padx=28, pady=(0, 14))

        row = tk.Frame(self, bg=BG)
        row.pack()

        open_b = _rbtn(row, "📂  Open lecture…", self._open_file)
        open_b.pack(side="left", padx=5)

        gen_b = _rbtn(row, "⚡  Generate", self._generate, primary=True)
        gen_b.pack(side="left", padx=5)

        key_b = _rbtn(row, "⚙", self._open_key_dialog, min_width=44)
        key_b.pack(side="left", padx=5)

        self._status = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self._status.pack(pady=8)

        self._study_btn = _rbtn(self, "Study cards  →", self._on_study, primary=True)

        if not self._generator.api_key:
            self._status.configure(text="No API key — click ⚙", fg=YELLOW)

    def set_api_key(self, key: str) -> None:
        self._generator.api_key = key

    def _open_key_dialog(self) -> None:
        ApiKeyDialog(self, self._generator.api_key, on_save=self._key_saved)

    def _key_saved(self, key: str) -> None:
        self._generator.api_key = key
        self._on_key_change(key)
        self._status.configure(
            text="Key saved ✓" if key else "Key cleared",
            fg=GREEN if key else RED)

    @handle_errors
    @log_action
    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open lecture file",
            filetypes=[("Lecture files", "*.pdf *.docx *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self._status.configure(text="Parsing file…", fg=MUTED)
        pq: queue.Queue = queue.Queue()

        def worker():
            try:
                pq.put(("ok", parse_file(path)))
            except Exception as e:
                pq.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                r, p = pq.get_nowait()
            except queue.Empty:
                self.after(80, poll)
                return
            if r == "ok":
                self._source = path
                self._text.delete("1.0", "end")
                self._text.insert("1.0", p)
                name = path.replace("\\", "/").split("/")[-1]
                self._status.configure(text=f"✓  {name}", fg=GREEN)
            else:
                self._status.configure(text=f"Error: {p}", fg=RED)

        poll()

    @handle_errors
    def _generate(self) -> None:
        if not self._generator.api_key:
            self._open_key_dialog()
            return
        text = self._text.get("1.0", "end").strip()
        if not text:
            self._status.configure(text="Paste or open a lecture first.", fg=YELLOW)
            return
        self._status.configure(text="Generating…  0s", fg=YELLOW)
        self.update_idletasks()
        self._run(text)

    @log_action
    def _run(self, text: str) -> None:
        src = self._source

        def worker():
            try:
                self._q.put(("ok", self._generator.generate(text, src)))
            except Exception as e:
                self._q.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        import time
        self._poll_start = time.monotonic()
        self._poll()

    def _poll(self) -> None:
        import time
        try:
            r, p = self._q.get_nowait()
        except queue.Empty:
            s = int(time.monotonic() - self._poll_start)
            self._status.configure(text=f"Generating…  {s}s", fg=YELLOW)
            self.after(200, self._poll)
            return
        if r == "ok":
            self._on_cards_added(p)
            if p:
                self._status.configure(text=f"✓  {len(p)} cards added!", fg=GREEN)
                self._study_btn.pack(pady=4)
            else:
                self._status.configure(text="No cards returned. Try different text.", fg=RED)
        else:
            self._status.configure(text=f"Error: {p}", fg=RED)


class DeckScreen(tk.Frame):
    def __init__(self, master, deck, on_delete):
        super().__init__(master, bg=BG)
        self._deck = deck
        self._on_delete = on_delete
        self._sel_id = None
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Deck", bg=BG, fg=ACCENT,
                 font=(FONT, 20, "bold")).pack(pady=(18, 10))

        search_row = tk.Frame(self, bg=BG)
        search_row.pack(fill="x", padx=28, pady=(0, 8))

        tk.Label(search_row, text="🔍", bg=BG, fg=MUTED,
                 font=(FONT, 12)).pack(side="left")
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self.refresh())
        e = tk.Entry(search_row, textvariable=self._sv,
                     bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                     font=(FONT, 11), relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT)
        e.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=5)

        add_b = _rbtn(search_row, "+ Add card", self._open_add_dialog,
                      primary=True, padx=14, pady=6)
        add_b.pack(side="left", padx=(10, 0))

        lf = tk.Frame(self, bg=BG)
        lf.pack(fill="both", expand=True, padx=28, pady=(0, 4))

        sb = ttk.Scrollbar(lf, orient="vertical")
        sb.pack(side="right", fill="y")

        self._lb = tk.Listbox(lf, bg=SURFACE, fg=TEXT, selectbackground=ACCENT,
                              selectforeground="#fff", font=(FONT, 11),
                              relief="flat", bd=0, yscrollcommand=sb.set,
                              activestyle="none", highlightthickness=0)
        self._lb.pack(fill="both", expand=True)
        sb.configure(command=self._lb.yview)
        self._lb.bind("<<ListboxSelect>>", self._sel)

        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=28, pady=8)

        del_b = _rbtn(bot, "🗑  Delete", self._delete, danger=True, padx=14, pady=7)
        del_b.pack(side="left")

        self._info = tk.Label(bot, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self._info.pack(side="right")

        self._ids = []
        self.refresh()

    def refresh(self) -> None:
        q = self._sv.get().strip()
        cards = self._deck.search(q) if q else list(self._deck.cards.values())
        self._ids = [c.id for c in cards]
        self._lb.delete(0, "end")
        diff_icons = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        for c in cards:
            icon = diff_icons.get(c.difficulty, "⚪")
            front = c.front[:58] + ("…" if len(c.front) > 58 else "")
            self._lb.insert("end", f"  {icon}  {front}")
        st = self._deck.stats()
        self._info.configure(
            text=f"Total: {st['total']}  •  Known: {st['known']}  •  {st['accuracy']}%")

    def _sel(self, _) -> None:
        s = self._lb.curselection()
        self._sel_id = self._ids[s[0]] if s else None

    @handle_errors
    def _delete(self) -> None:
        if not self._sel_id:
            return
        self._deck.remove(self._sel_id)
        self._on_delete()
        self._sel_id = None
        self.refresh()

    def _open_add_dialog(self) -> None:
        AddCardDialog(self, deck=self._deck, on_saved=self.refresh)


class StudyScreen(tk.Frame):
    def __init__(self, master, deck, on_done):
        super().__init__(master, bg=BG)
        self._deck = deck
        self._on_done = on_done
        self._cards = []
        self._idx = 0
        self._build()

    def _build(self) -> None:
        self._prog = AnimatedProgress(self, width=540, height=5)
        self._prog.pack(pady=(16, 2))

        self._counter = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self._counter.pack()

        self._card = FlipCard(self, width=540, height=300)
        self._card.pack(pady=(10, 4))

        tk.Label(self, text="Click card to flip  •  Space",
                 bg=BG, fg="#3a3a55", font=(FONT, 9)).pack()

        row = tk.Frame(self, bg=BG)
        row.pack(pady=14)

        self._forgot_b = _rbtn(row, "✗  Forgot", self._forgot,
                                danger=True, min_width=110)
        self._forgot_b.pack(side="left", padx=10)

        self._knew_b = _rbtn(row, "✓  Knew it", self._knew_it,
                              green=True, min_width=110)
        self._knew_b.pack(side="left", padx=10)

        self.bind_all("<space>", lambda _: self._card.flip())

    def start(self) -> None:
        self._cards = sorted(list(self._deck.due_cards()),
                             key=lambda c: c.times_reviewed)
        self._idx = 0
        if not self._cards:
            self._empty()
            return
        self._show()

    def _show(self) -> None:
        c = self._cards[self._idx]
        self._card.load(c)
        total = len(self._cards)
        self._counter.configure(text=f"{self._idx + 1} / {total}")
        self._prog.set_progress(self._idx / total)

    @handle_errors
    def _forgot(self) -> None:
        self._ans(False)

    @handle_errors
    def _knew_it(self) -> None:
        self._ans(True)

    def _ans(self, knew: bool) -> None:
        if self._idx >= len(self._cards):
            return
        self._deck.mark(self._cards[self._idx].id, knew)
        self._idx += 1
        if self._idx >= len(self._cards):
            self._prog.set_progress(1.0)
            self.after(350, self._stats)
        else:
            self._show()

    def _empty(self) -> None:
        for w in self.winfo_children():
            w.pack_forget()
        tk.Label(self, text="Nothing to study", bg=BG, fg=ACCENT,
                 font=(FONT, 20, "bold")).pack(pady=(80, 8))
        tk.Label(self, text="Go to Generate and add flashcards first.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack()
        if self._deck.stats()["total"] > 0:
            tk.Label(self, text="All cards already known — great job!",
                     bg=BG, fg=GREEN, font=(FONT, 11)).pack(pady=6)
        b = _rbtn(self, "Back", self._on_done, primary=True, min_width=110)
        b.pack(pady=20)

    def _stats(self) -> None:
        for w in self.winfo_children():
            w.pack_forget()

        st  = self._deck.stats()
        acc = st["accuracy"]

        outer = tk.Frame(self, bg=BG)
        outer.pack(expand=True, fill="both", padx=60, pady=30)

        tk.Label(outer, text="Session complete!", bg=BG, fg=ACCENT,
                 font=(FONT, 22, "bold")).pack(pady=(20, 16))

        rows = [
            (f"{len(self._cards)}", "cards studied"),
            (f"{st['known']}", "marked Known"),
            (f"{acc}%", "accuracy"),
        ]
        for val, lbl in rows:
            f = tk.Frame(outer, bg=SURFACE, padx=20, pady=12)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=val, bg=SURFACE,
                     fg=GREEN if "%" not in val or acc >= 50 else RED,
                     font=(FONT, 20, "bold")).pack(side="left")
            tk.Label(f, text=f"  {lbl}", bg=SURFACE, fg=MUTED,
                     font=(FONT, 12)).pack(side="left", anchor="s", pady=4)

        by = "  •  ".join(f"{t}: {n}" for t, n in st["by_topic"].items())
        if by:
            tk.Label(outer, text=by, bg=BG, fg=MUTED, font=(FONT, 9),
                     wraplength=480, justify="center").pack(pady=8)

        b = _rbtn(outer, "Back to deck", self._on_done, primary=True, min_width=130)
        b.pack(pady=12)


# ──────────────────────────────────────────────────────────────
#  QuizScreen — MAD exam quiz mode (Learn + Mock Exam tabs)
# ──────────────────────────────────────────────────────────────

class QuizScreen(tk.Frame):
    TOPICS = ["all", "equivalence", "partial_order", "countable", "combinatorics",
              "logic", "set_algebra", "relations", "big_o", "probability",
              "pigeonhole", "predicates", "well_order"]

    def __init__(self, master, engine):
        super().__init__(master, bg=BG)
        self._engine = engine
        self._queue: list = []
        self._idx = 0
        self._selected: set = set()
        self._checked = False
        self._mode = "learn"
        self._topic_var = tk.StringVar(value="all")
        self._build()
        self._load_learn_queue()

    # ── layout ──────────────────────────────────────────────

    def _build(self) -> None:
        # ── top bar ──
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=18, pady=(12, 0))

        tab_f = tk.Frame(top, bg=BG)
        tab_f.pack(side="left")

        self._tab_learn = RoundedButton(tab_f, text="Learn",
                                        command=self._switch_learn,
                                        bg=ACCENT, fg="#fff",
                                        font_spec=(FONT, 10, "bold"),
                                        padx=14, pady=6)
        self._tab_learn.pack(side="left", padx=(0, 4))

        self._tab_mock = RoundedButton(tab_f, text="Mock Exam",
                                       command=self._switch_mock,
                                       bg=SURFACE, fg=MUTED,
                                       font_spec=(FONT, 10),
                                       padx=14, pady=6)
        self._tab_mock.pack(side="left")

        # topic filter (learn mode only)
        topic_f = tk.Frame(top, bg=BG)
        topic_f.pack(side="right")
        tk.Label(topic_f, text="Topic:", bg=BG, fg=MUTED,
                 font=(FONT, 10)).pack(side="left", padx=(0, 4))
        self._topic_cb = ttk.Combobox(topic_f, textvariable=self._topic_var,
                                      values=self.TOPICS, state="readonly",
                                      width=14, font=(FONT, 10))
        self._topic_cb.pack(side="left")
        self._topic_cb.bind("<<ComboboxSelected>>", lambda _: self._load_learn_queue())

        # ── progress bar area ──
        prog_f = tk.Frame(self, bg=BG)
        prog_f.pack(fill="x", padx=18, pady=(8, 4))

        self._prog_canvas = tk.Canvas(prog_f, height=6, bg=BORDER,
                                      highlightthickness=0, relief="flat")
        self._prog_canvas.pack(fill="x")
        self._prog_label = tk.Label(prog_f, text="", bg=BG, fg=MUTED,
                                    font=(FONT, 9))
        self._prog_label.pack(anchor="e")

        # ── question meta (year · topic) ──
        self._meta_lbl = tk.Label(self, text="", bg=BG, fg=MUTED,
                                  font=(FONT, 9))
        self._meta_lbl.pack(pady=(4, 0))

        # ── question text ──
        self._q_lbl = tk.Label(self, text="", bg=BG, fg=TEXT,
                               font=(FONT, 12, "bold"),
                               wraplength=560, justify="left")
        self._q_lbl.pack(padx=24, pady=(6, 10), anchor="w")

        # ── option buttons (3 slots, tk.Button with macOS fix) ──
        self._opt_frames: list[tk.Frame] = []
        self._opt_btns: list[tk.Button] = []
        opt_grid = tk.Frame(self, bg=BG)
        opt_grid.pack(padx=18, fill="x")

        for i in range(3):
            row = i // 2
            col = i % 2
            f = tk.Frame(opt_grid, bg=BORDER, padx=2, pady=2)
            f.grid(row=row, column=col, padx=6, pady=4, sticky="ew")
            opt_grid.columnconfigure(col, weight=1)
            b = tk.Button(f, text="", bg=CARD_S, fg=TEXT,
                          anchor="w", wraplength=240,
                          font=(FONT, 10), relief="flat",
                          padx=10, pady=8, cursor="hand2",
                          bd=0, highlightthickness=0,
                          highlightbackground=CARD_S,
                          command=lambda idx=i: self._toggle(idx))
            b.pack(fill="both", expand=True)
            self._opt_frames.append(f)
            self._opt_btns.append(b)

        # "Don't know" button — 4th slot
        dont_f = tk.Frame(opt_grid, bg=BG)
        dont_f.grid(row=1, column=1, padx=6, pady=4, sticky="e")
        self._dont_btn = _rbtn(dont_f, "Don't know", self._dont_know,
                                muted=True, padx=12, pady=7)
        self._dont_btn.pack()

        # ── check button ──
        self._check_btn = _rbtn(self, "CHECK ANSWER", self._check,
                                 primary=True, min_width=180,
                                 font_spec=(FONT, 11, "bold"),
                                 padx=22, pady=10)
        self._check_btn.pack(pady=(14, 6))

        # ── explanation ──
        self._expl_frame = tk.Frame(self, bg=SURFACE, padx=14, pady=10)
        self._expl_lbl = tk.Label(self._expl_frame, text="",
                                  bg=SURFACE, fg=TEXT,
                                  font=(FONT, 10), wraplength=540,
                                  justify="left")
        self._expl_lbl.pack(anchor="w")

        # ── got it / still learning buttons ──
        self._feedback_frame = tk.Frame(self, bg=BG)
        still = _rbtn(self._feedback_frame, "✗  Still learning",
                      lambda: self._feedback(False),
                      danger=True, min_width=140)
        still.pack(side="left", padx=10)

        got = _rbtn(self._feedback_frame, "✓  Got it",
                    lambda: self._feedback(True),
                    green=True, min_width=110)
        got.pack(side="left", padx=10)

        # ── empty state ──
        self._empty_frame = tk.Frame(self, bg=BG)
        tk.Label(self._empty_frame, text="No questions found",
                 bg=BG, fg=ACCENT, font=(FONT, 18, "bold")).pack(pady=(60, 8))
        tk.Label(self._empty_frame, text="Check that data/mad_questions.json exists.",
                 bg=BG, fg=MUTED, font=(FONT, 11)).pack()

    # ── mode switching ──────────────────────────────────────

    def _switch_learn(self) -> None:
        self._mode = "learn"
        self._tab_learn.configure(bg=ACCENT, fg="#fff")
        self._tab_mock.configure(bg=SURFACE, fg=MUTED)
        self._topic_cb.configure(state="readonly")
        self._load_learn_queue()

    def _switch_mock(self) -> None:
        self._mode = "mock"
        self._tab_learn.configure(bg=SURFACE, fg=MUTED)
        self._tab_mock.configure(bg=ACCENT, fg="#fff")
        self._topic_cb.configure(state="disabled")
        screen = MockExamScreen(self.master,
                                questions=self._engine.mock_exam(),
                                engine=self._engine,
                                on_back=self._switch_learn)
        self.pack_forget()
        screen.pack(fill="both", expand=True)

    # ── data loading ────────────────────────────────────────

    def _load_learn_queue(self) -> None:
        topic = self._topic_var.get()
        self._queue = self._engine.learn_queue(topic)
        self._idx = 0
        self._update_progress()
        if self._queue:
            self._show_question()
        else:
            self._show_empty()

    def _update_progress(self) -> None:
        topic = self._topic_var.get()
        stats = self._engine.stats()
        if topic == "all":
            known = stats["known"]
            total = stats["total"]
        else:
            bt = stats["by_topic"].get(topic, {"total": 0, "known": 0})
            known = bt["known"]
            total = bt["total"]
        self._prog_label.configure(text=f"{known} / {total} known")
        self._prog_canvas.update_idletasks()
        w = self._prog_canvas.winfo_width() or 560
        ratio = known / max(total, 1)
        self._prog_canvas.delete("bar")
        self._prog_canvas.create_rectangle(0, 0, int(w * ratio), 6,
                                           fill=ACCENT, tags="bar")

    # ── question display ────────────────────────────────────

    def _show_question(self) -> None:
        self._empty_frame.pack_forget()
        self._expl_frame.pack_forget()
        self._feedback_frame.pack_forget()
        self._checked = False
        self._selected = set()

        q = self._queue[self._idx % len(self._queue)]
        self._meta_lbl.configure(
            text=f"{q.year}  ·  {q.topic.replace('_', ' ')}")
        self._q_lbl.configure(text=q.question)

        options = list(q.options.items())
        for i, btn in enumerate(self._opt_btns):
            frame = self._opt_frames[i]
            if i < len(options):
                key, text = options[i]
                btn.configure(text=f"{key})  {text}",
                              bg=CARD_S, fg=TEXT, state="normal",
                              highlightbackground=CARD_S)
                frame.configure(bg=BORDER)
                btn.pack(fill="both", expand=True)
                frame.grid()
            else:
                frame.grid_remove()

        self._check_btn.configure(state="normal", bg=ACCENT)
        self._dont_btn.configure(state="normal")

    def _show_empty(self) -> None:
        self._empty_frame.pack(fill="both", expand=True)

    # ── interaction ─────────────────────────────────────────

    def _toggle(self, idx: int) -> None:
        if self._checked:
            return
        q = self._queue[self._idx % len(self._queue)]
        options = list(q.options.keys())
        if idx >= len(options):
            return
        key = options[idx]
        if key in self._selected:
            self._selected.discard(key)
            self._opt_btns[idx].configure(bg=CARD_S, highlightbackground=CARD_S)
            self._opt_frames[idx].configure(bg=BORDER)
        else:
            self._selected.add(key)
            self._opt_btns[idx].configure(bg="#2a2a55", highlightbackground="#2a2a55")
            self._opt_frames[idx].configure(bg=ACCENT)

    def _dont_know(self) -> None:
        self._selected = set()
        self._check()

    def _check(self) -> None:
        if self._checked:
            return
        self._checked = True
        self._check_btn.configure(state="disabled", bg=MUTED)
        self._dont_btn.configure(state="disabled")

        q = self._queue[self._idx % len(self._queue)]
        options = list(q.options.keys())
        correct_set = set(q.correct)

        for i, key in enumerate(options):
            if i >= len(self._opt_btns):
                break
            btn   = self._opt_btns[i]
            frame = self._opt_frames[i]
            selected = key in self._selected
            if key in correct_set and selected:
                frame.configure(bg=GREEN)
                btn.configure(bg="#1a3828", highlightbackground="#1a3828")
            elif key not in correct_set and selected:
                frame.configure(bg=RED)
                btn.configure(bg="#3a1a1a", highlightbackground="#3a1a1a")
            elif key in correct_set and not selected:
                frame.configure(bg=YELLOW)
                btn.configure(bg="#3a3010", highlightbackground="#3a3010")

        self._expl_lbl.configure(text=q.explanation)
        self._expl_frame.pack(fill="x", padx=18, pady=(8, 4))
        self._feedback_frame.pack(pady=6)

    def _feedback(self, knew: bool) -> None:
        q = self._queue[self._idx % len(self._queue)]
        q.update(knew)
        self._engine.save_progress()
        self._idx += 1
        self._update_progress()
        if self._idx >= len(self._queue):
            self._load_learn_queue()
        else:
            self._show_question()


# ──────────────────────────────────────────────────────────────
#  MockExamScreen — timed 20-question test
# ──────────────────────────────────────────────────────────────

class MockExamScreen(tk.Frame):
    def __init__(self, master, questions, engine, on_back):
        super().__init__(master, bg=BG)
        self._questions = questions
        self._engine    = engine
        self._on_back   = on_back
        self._answers: dict[int, set] = {i: set() for i in range(len(questions))}
        self._current = 0
        self._elapsed = 0
        self._running = True
        self._build()
        self._show_question(0)
        self._tick()

    # ── layout ──────────────────────────────────────────────

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=18, pady=(10, 4))
        tk.Label(hdr, text="Mock Exam", bg=BG, fg=ACCENT,
                 font=(FONT, 13, "bold")).pack(side="left")
        self._q_counter = tk.Label(hdr, text="", bg=BG, fg=MUTED,
                                   font=(FONT, 11))
        self._q_counter.pack(side="left", padx=14)
        self._timer_lbl = tk.Label(hdr, text="⏱ 0:00", bg=BG, fg=TEXT,
                                   font=(FONT, 11))
        self._timer_lbl.pack(side="right")

        # dot navigation
        dot_scroll = tk.Frame(self, bg=BG)
        dot_scroll.pack(fill="x", padx=18, pady=(2, 6))
        self._dot_canvas = tk.Canvas(dot_scroll, height=18, bg=BG,
                                     highlightthickness=0)
        self._dot_canvas.pack(fill="x")
        self._dot_canvas.bind("<Button-1>", self._dot_click)
        self._dot_ids: list = []

        self._q_lbl = tk.Label(self, text="", bg=BG, fg=TEXT,
                               font=(FONT, 12, "bold"),
                               wraplength=560, justify="left")
        self._q_lbl.pack(padx=24, pady=(6, 10), anchor="w")

        # 4 option slots (2×2 grid including "No answer")
        self._opt_frames: list[tk.Frame] = []
        self._opt_btns: list[tk.Button] = []
        grid_f = tk.Frame(self, bg=BG)
        grid_f.pack(padx=18, fill="x")

        for i in range(4):
            row = i // 2
            col = i % 2
            f = tk.Frame(grid_f, bg=BORDER, padx=2, pady=2)
            f.grid(row=row, column=col, padx=6, pady=4, sticky="ew")
            grid_f.columnconfigure(col, weight=1)
            b = tk.Button(f, text="", bg=CARD_S, fg=TEXT,
                          anchor="w", wraplength=240,
                          font=(FONT, 10), relief="flat",
                          padx=10, pady=8, cursor="hand2",
                          bd=0, highlightthickness=0,
                          highlightbackground=CARD_S,
                          command=lambda idx=i: self._toggle(idx))
            b.pack(fill="both", expand=True)
            self._opt_frames.append(f)
            self._opt_btns.append(b)

        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=18, pady=(12, 4))

        prev_b = _rbtn(nav, "← Prev", self._prev, padx=14, pady=7)
        prev_b.pack(side="left")

        next_b = _rbtn(nav, "Next →", self._next, padx=14, pady=7)
        next_b.pack(side="right")

        submit_b = _rbtn(self, "SUBMIT EXAM", self._submit,
                          danger=True, min_width=160,
                          font_spec=(FONT, 11, "bold"), padx=22, pady=10)
        submit_b.pack(pady=8)

    # ── timer ───────────────────────────────────────────────

    def _tick(self) -> None:
        if not self._running:
            return
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        self._timer_lbl.configure(text=f"⏱ {m}:{s:02d}")
        self.after(1000, self._tick)

    # ── dot nav ─────────────────────────────────────────────

    def _draw_dots(self) -> None:
        self._dot_canvas.delete("all")
        self._dot_ids.clear()
        n = len(self._questions)
        r = 7
        spacing = 18
        for i in range(n):
            x = 10 + i * spacing
            y = 9
            answered = bool(self._answers[i])
            fill = ACCENT if i == self._current else (GREEN if answered else MUTED)
            oid = self._dot_canvas.create_oval(x - r, y - r, x + r, y + r,
                                               fill=fill, outline="")
            self._dot_ids.append(oid)

    def _dot_click(self, event) -> None:
        spacing = 18
        idx = (event.x - 10 + spacing // 2) // spacing
        if 0 <= idx < len(self._questions):
            self._show_question(idx)

    # ── question display ────────────────────────────────────

    def _show_question(self, idx: int) -> None:
        self._current = idx
        q = self._questions[idx]
        self._q_counter.configure(text=f"Q {idx + 1} / {len(self._questions)}")
        self._q_lbl.configure(text=q.question)

        options = list(q.options.items())
        saved   = self._answers[idx]

        for i in range(4):
            btn   = self._opt_btns[i]
            frame = self._opt_frames[i]
            if i < len(options):
                key, text = options[i]
                selected  = key in saved
                fill      = "#2a2a55" if selected else CARD_S
                btn.configure(text=f"{key})  {text}", state="normal",
                              bg=fill, highlightbackground=fill)
                frame.configure(bg=ACCENT if selected else BORDER)
                frame.grid()
            elif i == 3:
                selected = "none" in saved
                fill     = "#2a2a55" if selected else CARD_S
                btn.configure(text="⊘  No answer", state="normal",
                              bg=fill, highlightbackground=fill)
                frame.configure(bg=ACCENT if selected else BORDER)
                frame.grid()
            else:
                frame.grid_remove()

        self._draw_dots()

    # ── interaction ─────────────────────────────────────────

    def _toggle(self, slot: int) -> None:
        q       = self._questions[self._current]
        options = list(q.options.keys())
        if slot < len(options):
            key = options[slot]
        elif slot == 3:
            key = "none"
        else:
            return
        saved = self._answers[self._current]
        if key == "none":
            saved.clear()
            saved.add("none")
        else:
            saved.discard("none")
            if key in saved:
                saved.discard(key)
            else:
                saved.add(key)
        self._show_question(self._current)

    def _prev(self) -> None:
        if self._current > 0:
            self._show_question(self._current - 1)

    def _next(self) -> None:
        if self._current < len(self._questions) - 1:
            self._show_question(self._current + 1)

    def _submit(self) -> None:
        self._running = False
        self.pack_forget()
        screen = ResultsScreen(self.master,
                               questions=self._questions,
                               answers=self._answers,
                               elapsed=self._elapsed,
                               engine=self._engine,
                               on_back=self._on_back)
        screen.pack(fill="both", expand=True)


# ──────────────────────────────────────────────────────────────
#  ResultsScreen — shown after mock exam submission
# ──────────────────────────────────────────────────────────────

class ResultsScreen(tk.Frame):
    def __init__(self, master, questions, answers, elapsed, engine, on_back):
        super().__init__(master, bg=BG)
        self._questions      = questions
        self._answers        = answers
        self._elapsed        = elapsed
        self._engine         = engine
        self._on_back        = on_back
        self._wrong_expanded = False
        self._update_mastery()
        self._build()

    def _update_mastery(self) -> None:
        for i, q in enumerate(self._questions):
            selected   = [k for k in self._answers[i] if k != "none"]
            is_correct = q.check(selected)
            q.update(is_correct)
        self._engine.save_progress()

    def _build(self) -> None:
        m, s = divmod(self._elapsed, 60)
        n    = len(self._questions)
        correct_count = sum(
            1 for i, q in enumerate(self._questions)
            if q.check([k for k in self._answers[i] if k != "none"])
        )
        wrong_questions = [
            (i, q) for i, q in enumerate(self._questions)
            if not q.check([k for k in self._answers[i] if k != "none"])
        ]

        scroll_f = tk.Frame(self, bg=BG)
        scroll_f.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(scroll_f, orient="vertical")
        sb.pack(side="right", fill="y")
        canvas = tk.Canvas(scroll_f, bg=BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.configure(command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(event):
            canvas.itemconfigure(win, width=event.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        pad = {"padx": 28, "pady": 4}

        tk.Label(inner, text="Mock Exam Results", bg=BG, fg=ACCENT,
                 font=(FONT, 20, "bold")).pack(pady=(20, 6))

        pct   = int(correct_count / n * 100) if n else 0
        color = GREEN if pct >= 60 else (YELLOW if pct >= 40 else RED)
        tk.Label(inner, text=f"Score: {correct_count} / {n}  ({pct}%)",
                 bg=BG, fg=color, font=(FONT, 16, "bold")).pack(pady=(0, 10))

        stats_row = tk.Frame(inner, bg=BG)
        stats_row.pack(**pad)
        for txt, clr in [(f"Correct: {correct_count} ✓", GREEN),
                         (f"Wrong: {n - correct_count} ✗",  RED),
                         (f"Time: {m}:{s:02d}",              TEXT)]:
            f = tk.Frame(stats_row, bg=SURFACE, padx=12, pady=8)
            f.pack(side="left", padx=6)
            tk.Label(f, text=txt, bg=SURFACE, fg=clr,
                     font=(FONT, 11, "bold")).pack()

        weak = self._weak_topics_this_session(wrong_questions)
        if weak:
            tk.Label(inner, text="Weak topics this session:",
                     bg=BG, fg=MUTED, font=(FONT, 10, "bold")).pack(
                anchor="w", padx=28, pady=(12, 2))
            for topic, info in weak.items():
                tk.Label(inner,
                         text=f"  {topic.replace('_', ' ')}: "
                              f"{info['correct']}/{info['total']} ✗",
                         bg=BG, fg=YELLOW, font=(FONT, 10)).pack(
                    anchor="w", padx=28)

        self._wrong_frame = tk.Frame(inner, bg=BG)
        self._wrong_frame.pack(fill="x", padx=18, pady=(8, 0))

        if wrong_questions:
            show_btn = _rbtn(inner, "▶  Show wrong answers", None,
                              min_width=220, padx=12, pady=6)
            show_btn.configure(command=lambda: self._toggle_wrong(
                wrong_questions, show_btn))
            show_btn.pack(anchor="w", padx=28, pady=(6, 0))

        btn_row = tk.Frame(inner, bg=BG)
        btn_row.pack(pady=18)

        weak_topics = list(weak.keys()) if weak else []
        if weak_topics:
            prac = _rbtn(btn_row, "Practice weak topics",
                          lambda: self._practice_weak(weak_topics),
                          min_width=160)
            prac.pack(side="left", padx=6)

        new_mock = _rbtn(btn_row, "New mock exam", self._new_mock, min_width=130)
        new_mock.pack(side="left", padx=6)

        back = _rbtn(btn_row, "Back to learn", self._back,
                      primary=True, min_width=120)
        back.pack(side="left", padx=6)

    def _weak_topics_this_session(self, wrong_questions) -> dict:
        by_topic: dict = {}
        for _, q in enumerate(self._questions):
            t = q.topic
            if t not in by_topic:
                by_topic[t] = {"total": 0, "correct": 0}
            by_topic[t]["total"] += 1

        wrong_topics = {}
        for _, q in wrong_questions:
            wrong_topics[q.topic] = wrong_topics.get(q.topic, 0) + 1

        weak = {}
        for t, cnt in wrong_topics.items():
            total = by_topic.get(t, {}).get("total", cnt)
            weak[t] = {"total": total, "correct": total - cnt}
        return weak

    def _toggle_wrong(self, wrong_questions, btn) -> None:
        if self._wrong_expanded:
            for w in self._wrong_frame.winfo_children():
                w.destroy()
            btn.configure(text="▶  Show wrong answers")
            self._wrong_expanded = False
        else:
            btn.configure(text="▼  Hide wrong answers")
            self._wrong_expanded = True
            for _, q in wrong_questions:
                f = tk.Frame(self._wrong_frame, bg=SURFACE, padx=12, pady=8)
                f.pack(fill="x", pady=3)
                tk.Label(f, text=q.question, bg=SURFACE, fg=TEXT,
                         font=(FONT, 10, "bold"), wraplength=500,
                         justify="left").pack(anchor="w")
                correct_text = ", ".join(
                    f"{k}) {q.options[k]}" for k in q.correct if k in q.options
                )
                tk.Label(f, text=f"✓ {correct_text}",
                         bg=SURFACE, fg=GREEN,
                         font=(FONT, 10), wraplength=500,
                         justify="left").pack(anchor="w", pady=(4, 0))
                tk.Label(f, text=q.explanation, bg=SURFACE, fg=MUTED,
                         font=(FONT, 9), wraplength=500,
                         justify="left").pack(anchor="w", pady=(2, 0))

    def _practice_weak(self, weak_topics: list) -> None:
        self.pack_forget()
        screen = QuizScreen(self.master, engine=self._engine)
        if weak_topics:
            first_weak = weak_topics[0]
            if first_weak in QuizScreen.TOPICS:
                screen._topic_var.set(first_weak)
                screen._load_learn_queue()
        screen.pack(fill="both", expand=True)

    def _new_mock(self) -> None:
        self.pack_forget()
        screen = MockExamScreen(self.master,
                                questions=self._engine.mock_exam(),
                                engine=self._engine,
                                on_back=self._on_back)
        screen.pack(fill="both", expand=True)

    def _back(self) -> None:
        self.pack_forget()
        self._on_back()
