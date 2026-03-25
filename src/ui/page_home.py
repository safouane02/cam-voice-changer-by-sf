import os
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

from src.theme import COLORS, FONTS, make_button, make_card, make_label, make_status_dot
from src.audio import AUDIO_OK, find_vbcable
from src.vcam import CV2_OK, VCAM_OK
from src.installer import prompt_install_vbcable


class HomePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._build()

    def _build(self):
        title_row = tk.Frame(self, bg=COLORS["bg"])
        title_row.pack(fill="x", pady=(0, 14))
        tk.Label(title_row, text="Dashboard",
                 font=("Segoe UI Semibold", 16), fg=COLORS["white"],
                 bg=COLORS["bg"]).pack(side="left")
        tk.Label(title_row, text="Audio & Camera Control",
                 font=FONTS["body"], fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left", padx=12, pady=3)

        self._build_status_card()
        self._build_steps_card()
        self._build_volume_card()

    def _build_status_card(self):
        card, inner = make_card(self, "System Status")
        card.pack(fill="x", pady=(0, 12))

        self.cable_dot  = make_status_dot(inner, COLORS["muted"])
        self.camera_dot = make_status_dot(inner, COLORS["muted"])
        self.audio_dot  = make_status_dot(inner, COLORS["muted"])

        for label, dot_widget in [
            ("VB-Cable  (Audio Bridge)", self.cable_dot),
            ("Virtual Camera",           self.camera_dot),
            ("Audio Backend",            self.audio_dot),
        ]:
            row = tk.Frame(inner, bg=COLORS["card"])
            row.pack(fill="x", pady=4)
            dot_widget.pack(in_=row, side="left", pady=4)
            dot_widget.config(bg=COLORS["card"])
            tk.Label(row, text=label, font=FONTS["body"],
                     fg=COLORS["text"], bg=COLORS["card"]).pack(side="left", padx=10)

        self.cable_label   = make_label(inner, "", fg=COLORS["muted"], font=FONTS["small"])
        self.cable_label.pack(anchor="w", pady=(6, 0))
        self.device_label  = make_label(inner, "", fg=COLORS["muted"], font=FONTS["small"])
        self.device_label.pack(anchor="w")

        copy_row = tk.Frame(inner, bg=COLORS["card"])
        copy_row.pack(anchor="w", pady=(8, 0))
        make_button(copy_row, "Copy Device Name for Discord",
                    self._copy_device_name, COLORS["border"], COLORS["text"],
                    padx=12, pady=5).pack(side="left")

    def _build_steps_card(self):
        card, inner = make_card(self, "Quick Start  —  3 Steps")
        card.pack(fill="both", expand=True, pady=(0, 12))

        s1 = tk.Frame(inner, bg=COLORS["step_bg"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        s1.pack(fill="x", pady=5, ipady=10, ipadx=10)
        tk.Label(s1, text="1", font=("Segoe UI Semibold", 22),
                 fg=COLORS["accent"], bg=COLORS["step_bg"], width=3).pack(side="left")
        info1 = tk.Frame(s1, bg=COLORS["step_bg"])
        info1.pack(side="left", fill="x", expand=True)
        tk.Label(info1, text="Choose Audio Files", font=FONTS["title"],
                 fg=COLORS["white"], bg=COLORS["step_bg"], anchor="w").pack(anchor="w")
        self.step1_label = tk.Label(info1, text="No files loaded",
                                    font=FONTS["small"], fg=COLORS["muted"],
                                    bg=COLORS["step_bg"], anchor="w")
        self.step1_label.pack(anchor="w")
        btn_col = tk.Frame(s1, bg=COLORS["step_bg"])
        btn_col.pack(side="right", padx=12)
        make_button(btn_col, "Add Files", self._add_files,
                    COLORS["accent"], COLORS["white"]).pack(pady=2)
        self.resume_frame = tk.Frame(btn_col, bg=COLORS["step_bg"])
        self.resume_frame.pack()

        self.progress_canvas = tk.Canvas(inner, bg=COLORS["bg"], height=4,
                                          highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x", pady=(0, 4))
        self.progress_canvas.bind("<Configure>", lambda e: self.draw_progress())

        s2 = tk.Frame(inner, bg=COLORS["step_bg"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        s2.pack(fill="x", pady=5, ipady=10, ipadx=10)
        tk.Label(s2, text="2", font=("Segoe UI Semibold", 22),
                 fg=COLORS["green"], bg=COLORS["step_bg"], width=3).pack(side="left")
        info2 = tk.Frame(s2, bg=COLORS["step_bg"])
        info2.pack(side="left", fill="x", expand=True)
        tk.Label(info2, text="Play Audio", font=FONTS["title"],
                 fg=COLORS["white"], bg=COLORS["step_bg"], anchor="w").pack(anchor="w")
        self.step2_label = tk.Label(info2, text="Stopped",
                                    font=FONTS["small"], fg=COLORS["muted"],
                                    bg=COLORS["step_bg"], anchor="w")
        self.step2_label.pack(anchor="w")
        ctrl2 = tk.Frame(s2, bg=COLORS["step_bg"])
        ctrl2.pack(side="right", padx=12)
        self.play_btn = make_button(ctrl2, "Play", self.app.play_current,
                                    COLORS["green"], COLORS["white"])
        self.play_btn.pack(side="left", padx=2)
        make_button(ctrl2, "Pause", self.app.toggle_pause,
                    COLORS["border"], COLORS["text"], padx=10, pady=7).pack(side="left", padx=2)
        make_button(ctrl2, "Stop", self.app.stop_audio,
                    COLORS["red"], COLORS["white"], padx=10, pady=7).pack(side="left", padx=2)

        s3 = tk.Frame(inner, bg=COLORS["step_bg"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        s3.pack(fill="x", pady=5, ipady=10, ipadx=10)
        tk.Label(s3, text="3", font=("Segoe UI Semibold", 22),
                 fg=COLORS["orange"], bg=COLORS["step_bg"], width=3).pack(side="left")
        info3 = tk.Frame(s3, bg=COLORS["step_bg"])
        info3.pack(side="left", fill="x", expand=True)
        tk.Label(info3, text="Set Discord Input", font=FONTS["title"],
                 fg=COLORS["white"], bg=COLORS["step_bg"], anchor="w").pack(anchor="w")
        tk.Label(info3, text='Discord Settings  >  Voice & Video  >  Input: "CABLE Output"',
                 font=FONTS["small"], fg=COLORS["muted"], bg=COLORS["step_bg"],
                 anchor="w").pack(anchor="w")
        make_button(s3, "Open Discord",
                    lambda: webbrowser.open("discord://"),
                    COLORS["accent"], COLORS["white"]).pack(side="right", padx=12)

    def _build_volume_card(self):
        card, inner = make_card(self, "Volume")
        card.pack(fill="x")
        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")
        self.vol_var = tk.IntVar(value=self.app.config.get("volume", 80))
        tk.Scale(row, from_=0, to=200, orient="horizontal",
                 variable=self.vol_var, showvalue=False,
                 bg=COLORS["card"], fg=COLORS["text"], troughcolor=COLORS["border"],
                 activebackground=COLORS["accent"], highlightthickness=0,
                 length=260, command=self._on_volume_change).pack(side="left")
        self.vol_label = make_label(row, f"{self.vol_var.get()}%",
                                    fg=COLORS["accent"], font=FONTS["title"])
        self.vol_label.pack(side="left", padx=10)

    def _copy_device_name(self):
        name = "CABLE Output (VB-Audio Virtual Cable)"
        self.app.clipboard_clear()
        self.app.clipboard_append(name)
        self.app.set_status("Copied!  Paste in Discord > Voice & Video > Input Device")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Audio", "*.wav *.mp3 *.ogg *.flac *.aac"), ("All", "*.*")])
        for path in paths:
            if path not in list(self.app.playlist_box.get(0, "end")):
                self.app.playlist_box.insert("end", path)
        self.app.save_playlist()
        self.update_step1_label()

    def _on_volume_change(self, _=None):
        v = self.vol_var.get()
        self.app.player.set_volume(v)
        self.vol_label.config(text=f"{v}%")
        self.app.config["volume"] = v
        self.app.save_config()

    def refresh_status(self):
        idx, name = find_vbcable() if AUDIO_OK else (None, None)
        has_cable = idx is not None

        def _redraw_dot(dot_widget, color):
            dot_widget.delete("all")
            dot_widget.create_oval(1, 1, 9, 9, fill=color, outline="")

        _redraw_dot(self.cable_dot,  COLORS["green"] if has_cable else COLORS["red"])
        _redraw_dot(self.audio_dot,  COLORS["green"] if AUDIO_OK else COLORS["red"])
        _redraw_dot(self.camera_dot, COLORS["green"] if (CV2_OK and VCAM_OK) else COLORS["yellow"])

        if has_cable and self.app.player.device_idx is not None:
            self.cable_label.config(
                text=f"Auto-detected: {self.app.player.device_name}", fg=COLORS["green"])
            self.device_label.config(
                text="Discord input  >  CABLE Output (VB-Audio Virtual Cable)",
                fg=COLORS["muted"])
        elif has_cable:
            self.cable_label.config(text=f"VB-Cable available: {name}", fg=COLORS["green"])
            self.device_label.config(text="", fg=COLORS["muted"])
        else:
            self.cable_label.config(
                text="VB-Cable not found  —  download from vb-audio.com",
                fg=COLORS["red"])
            self.device_label.config(text="", fg=COLORS["muted"])

    def update_step1_label(self):
        n = self.app.playlist_box.size()
        if n == 0:
            self.step1_label.config(text="No files loaded", fg=COLORS["muted"])
        else:
            self.step1_label.config(text=f"{n} file(s) ready", fg=COLORS["green"])

    def draw_progress(self):
        c = self.progress_canvas
        c.delete("all")
        w = c.winfo_width()
        if w <= 1:
            return
        c.create_rectangle(0, 0, w, 4, fill=COLORS["border"], outline="")
        filled = int(w * self.app.progress)
        if filled > 0:
            c.create_rectangle(0, 0, filled, 4, fill=COLORS["accent"], outline="")

    def on_tick(self, playing, paused, name):
        if playing:
            state = "Paused" if paused else "Playing"
            fg    = COLORS["yellow"] if paused else COLORS["green"]
            self.step2_label.config(text=f"{state}:  {name}", fg=fg)
        else:
            self.step2_label.config(text="Stopped", fg=COLORS["muted"])
