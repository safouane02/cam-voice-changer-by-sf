import tkinter as tk

from src.theme import COLORS, FONTS
from src.audio import AUDIO_OK, is_vbcable_installed


class IntroScreen(tk.Toplevel):
    STAGES = [
        (0.00, "Initializing..."),
        (0.25, "Loading audio backend..."),
        (0.55, "Detecting VB-Cable..."),
        (0.80, "Setting up interface..."),
        (0.95, "Ready!"),
    ]

    def __init__(self, on_done):
        super().__init__()
        self.on_done = on_done
        self.overrideredirect(True)
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)

        w, h = 480, 320
        sw   = self.winfo_screenwidth()
        sh   = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.lift()
        self.attributes("-topmost", True)

        self._alpha   = 0.0
        self._bar_pct = 0.0
        self._phase   = "fade_in"

        self._build()
        self.attributes("-alpha", 0.0)
        self.after(30, self._animate)

    def _build(self):
        self._canvas = tk.Canvas(
            self, width=480, height=320,
            bg=COLORS["bg"], highlightthickness=0, bd=0
        )
        self._canvas.pack(fill="both", expand=True)

        self._canvas.create_rectangle(0, 0, 480, 4, fill=COLORS["accent"], outline="")
        self._canvas.create_text(240, 108, text="VC Changer",
                                  font=FONTS["brand"], fill=COLORS["white"], anchor="center")
        self._canvas.create_text(240, 148, text="by safouane02",
                                  font=FONTS["sub"], fill=COLORS["muted"], anchor="center")
        self._canvas.create_text(240, 172, text="v3.0  |  Discord Audio & Camera Tool",
                                  font=FONTS["small"], fill=COLORS["muted"], anchor="center")

        self._canvas.create_rectangle(80, 210, 400, 218, fill=COLORS["border"], outline="")
        self._bar_rect = self._canvas.create_rectangle(
            80, 210, 80, 218, fill=COLORS["accent"], outline=""
        )
        self._status_text = self._canvas.create_text(
            240, 235, text="Initializing...",
            font=FONTS["small"], fill=COLORS["muted"], anchor="center"
        )
        self._canvas.create_text(240, 300, text="github.com/safouane02",
                                  font=FONTS["small"], fill=COLORS["border"], anchor="center")

    def _animate(self):
        if self._phase == "fade_in":
            self._alpha = min(self._alpha + 0.06, 1.0)
            self.attributes("-alpha", self._alpha)
            if self._alpha >= 1.0:
                self._phase = "load"
            self.after(20, self._animate)

        elif self._phase == "load":
            self._bar_pct = min(self._bar_pct + 0.012, 1.0)
            filled_x = 80 + int(320 * self._bar_pct)
            self._canvas.coords(self._bar_rect, 80, 210, filled_x, 218)

            status = "Starting..."
            for threshold, text in self.STAGES:
                if self._bar_pct >= threshold:
                    status = text
            self._canvas.itemconfig(self._status_text, text=status)

            if self._bar_pct >= 1.0:
                if AUDIO_OK and not is_vbcable_installed():
                    self._canvas.itemconfig(self._status_text,
                                            text="VB-Cable missing!", fill=COLORS["red"])
                self._phase = "hold"
                self.after(500, self._animate)
            else:
                self.after(18, self._animate)

        elif self._phase == "hold":
            self._phase = "fade_out"
            self.after(20, self._animate)

        elif self._phase == "fade_out":
            self._alpha = max(self._alpha - 0.07, 0.0)
            self.attributes("-alpha", self._alpha)
            if self._alpha <= 0.0:
                self.destroy()
                self.on_done()
                return
            self.after(18, self._animate)
