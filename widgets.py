import tkinter as tk

FONT = "Segoe UI"


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3  # cubic ease-out


def _ease_in(t: float) -> float:
    return t * t * t  # cubic ease-in


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rounded_pts(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
    return [
        x0 + r, y0,  x1 - r, y0,
        x1, y0 + r,  x1, y1 - r,
        x1 - r, y1,  x0 + r, y1,
        x0, y1 - r,  x0, y0 + r,
    ]


class FlipCard(tk.Canvas):
    FRONT_BG     = "#1e2048"
    FRONT_BORDER = "#4a4aff"
    BACK_BG      = "#1a3828"
    BACK_BORDER  = "#2dba6b"
    TEXT_COLOR   = "#e8e8f4"
    LABEL_FRONT  = "#7b7fff"
    LABEL_BACK   = "#2dba6b"
    CANVAS_BG    = "#111118"

    _GLOW = [(18, 0.10), (11, 0.22), (5, 0.42)]  # (pad, border_strength)
    _STEPS = 9
    _MS    = 13  # ~75fps cadence

    def __init__(self, master, width=560, height=300, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg=self.CANVAS_BG, highlightthickness=0, **kwargs)
        self._cw = width
        self._ch = height
        self._card = None
        self._showing_front = True
        self._animating = False
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def load(self, card) -> None:
        self._card = card
        self._showing_front = True
        self._animating = False
        self._redraw(1.0)

    def flip(self) -> None:
        if self._animating or self._card is None:
            return
        self._animating = True
        self._animate(0, going_back=False)

    def _animate(self, step: int, going_back: bool) -> None:
        n = self._STEPS
        frac = step / n
        if not going_back:
            # squash down: ease-in so it accelerates into the fold
            scale = 1.0 - _ease_in(frac)
            self._redraw(scale)
            if step < n:
                self.after(self._MS, self._animate, step + 1, False)
            else:
                self._showing_front = not self._showing_front
                self._animate(0, going_back=True)
        else:
            # expand back: ease-out so it decelerates softly
            scale = _ease_out(frac)
            self._redraw(scale)
            if step < n:
                self.after(self._MS, self._animate, step + 1, True)
            else:
                self._animating = False

    def _redraw(self, scale_y: float = 1.0) -> None:
        self.delete("all")
        if self._card is None:
            return

        cx  = self._cw // 2
        cy  = self._ch // 2
        cw  = int(self._cw * 0.92)
        ch  = max(2, int(self._ch * 0.88 * scale_y))
        x0, x1 = cx - cw // 2, cx + cw // 2
        y0, y1 = cy - ch // 2, cy + ch // 2
        r = 14

        border = self.FRONT_BORDER if self._showing_front else self.BACK_BORDER
        bg     = self.FRONT_BG     if self._showing_front else self.BACK_BG

        # glow rings (outermost → innermost, strongest last)
        if scale_y > 0.12:
            for pad, strength in self._GLOW:
                glow = _lerp_hex(self.CANVAS_BG, border, strength * scale_y)
                pts = _rounded_pts(x0 - pad, y0 - pad, x1 + pad, y1 + pad, r + pad)
                self.create_polygon(pts, fill="", outline=glow, width=1, smooth=True)

        # card body
        if cw > r * 2:
            self.create_polygon(_rounded_pts(x0, y0, x1, y1, r),
                                fill=bg, outline=border, width=2, smooth=True)
        else:
            self.create_rectangle(x0, y0, x1, y1, fill=bg, outline=border, width=2)

        if scale_y > 0.22:
            label = "QUESTION" if self._showing_front else "ANSWER"
            lc    = self.LABEL_FRONT if self._showing_front else self.LABEL_BACK
            self.create_text(cx, y0 + 20, text=label, fill=lc,
                             font=(FONT, 9, "bold"))

            text = self._card.front if self._showing_front else self._card.back
            self.create_text(cx, cy + 6, text=text,
                             fill=self.TEXT_COLOR, font=(FONT, 13),
                             width=cw - 60, justify="center")

            diff   = self._card.difficulty
            colors = {"easy": "#4ade80", "medium": "#facc15", "hard": "#f87171"}
            self.create_text(x1 - 10, y1 - 10, text=diff.upper(),
                             fill=colors.get(diff, "#aaa"),
                             font=(FONT, 8, "bold"), anchor="se")

    def _on_click(self, _) -> None:
        self.flip()


def _lighten(color: str, amount: int = 22) -> str:
    r = min(255, int(color[1:3], 16) + amount)
    g = min(255, int(color[3:5], 16) + amount)
    b = min(255, int(color[5:7], 16) + amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(color: str, amount: int = 18) -> str:
    r = max(0, int(color[1:3], 16) - amount)
    g = max(0, int(color[3:5], 16) - amount)
    b = max(0, int(color[5:7], 16) - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


class RoundedButton(tk.Canvas):
    """Canvas-drawn button with rounded corners — works correctly on macOS."""

    _SKIP = frozenset({
        "activebackground", "activeforeground", "relief", "bd", "borderwidth",
        "anchor", "wraplength", "justify", "highlightthickness",
        "highlightcolor", "highlightbackground",
    })

    def __init__(self, master, text="", command=None,
                 bg="#7b7fff", fg="#ffffff",
                 font_spec=None, radius=11,
                 padx=18, pady=9, min_width=0, **kwargs):
        import tkinter.font as tkfont

        self._text     = text
        self._command  = command
        self._bg_norm  = bg
        self._bg_hov   = _lighten(bg, 22)
        self._bg_press = _darken(bg, 18)
        self._fg       = fg
        self._r        = radius
        self._enabled  = True
        self._fs       = font_spec or (FONT, 10, "bold")

        fobj = tkfont.Font(family=self._fs[0], size=abs(self._fs[1]),
                           weight=self._fs[2] if len(self._fs) > 2 else "normal")
        tw = fobj.measure(text) + 6   # +6 for emoji/kerning headroom
        th = fobj.metrics("linespace")
        w  = max(min_width, tw + padx * 2)
        h  = th + pady * 2

        try:
            pbg = master.cget("bg")
        except Exception:
            pbg = "#111118"

        super().__init__(master, width=w, height=h,
                         bg=pbg, highlightthickness=0, **kwargs)
        self._w, self._h = w, h

        self._draw(self._bg_norm)
        self.bind("<Enter>",           lambda _: self._on_enter())
        self.bind("<Leave>",           lambda _: self._on_leave())
        self.bind("<Button-1>",        lambda _: self._on_press())
        self.bind("<ButtonRelease-1>", lambda _: self._on_release())
        super().configure(cursor="hand2")

    def _draw(self, bg: str) -> None:
        self.delete("all")
        w, h, r = self._w, self._h, self._r
        pts = _rounded_pts(1, 1, w - 1, h - 1, r)
        self.create_polygon(pts, fill=bg, outline="", smooth=True)
        weight = self._fs[2] if len(self._fs) > 2 else "normal"
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=self._fg if self._enabled else "#55556a",
                         font=(self._fs[0], self._fs[1], weight))

    def _on_enter(self):
        if self._enabled:
            self._draw(self._bg_hov)

    def _on_leave(self):
        if self._enabled:
            self._draw(self._bg_norm)

    def _on_press(self):
        if self._enabled:
            self._draw(self._bg_press)

    def _on_release(self):
        if self._enabled:
            self._draw(self._bg_norm)
            if self._command:
                self._command()

    def configure(self, **kw):
        for k in list(kw):
            if k in self._SKIP:
                kw.pop(k)
        redraw = False
        if "text"    in kw: self._text = kw.pop("text"); redraw = True
        if "command" in kw: self._command = kw.pop("command")
        if "state"   in kw:
            self._enabled = kw.pop("state") == "normal"
            super().configure(cursor="hand2" if self._enabled else "")
            redraw = True
        if "bg"      in kw:
            self._bg_norm  = kw.pop("bg")
            self._bg_hov   = _lighten(self._bg_norm, 22)
            self._bg_press = _darken(self._bg_norm, 18)
            redraw = True
        if "fg"      in kw: self._fg = kw.pop("fg"); redraw = True
        if "font"    in kw: kw.pop("font")
        if kw: super().configure(**kw)
        if redraw: self._draw(self._bg_norm)

    config = configure

    def cget(self, key):
        if key == "text":  return self._text
        if key == "state": return "normal" if self._enabled else "disabled"
        if key == "fg":    return self._fg
        if key == "bg":    return self._bg_norm
        return super().cget(key)


class AnimatedProgress(tk.Canvas):
    def __init__(self, master, width=540, height=5, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg="#111118", highlightthickness=0, **kwargs)
        self._cw = width
        self._ch = height
        self._current = 0.0
        self._target = 0.0
        self._draw(0.0)

    def set_progress(self, value: float) -> None:
        self._target = max(0.0, min(1.0, value))
        self._step()

    def _step(self) -> None:
        diff = self._target - self._current
        if abs(diff) < 0.004:
            self._current = self._target
            self._draw(self._current)
            return
        self._current += diff * 0.25
        self._draw(self._current)
        self.after(12, self._step)

    def _draw(self, value: float) -> None:
        self.delete("all")
        self.create_rectangle(0, 0, self._cw, self._ch, fill="#252535", outline="")
        w = int(self._cw * value)
        if w > 0:
            self.create_rectangle(0, 0, w, self._ch, fill="#7b7fff", outline="")
