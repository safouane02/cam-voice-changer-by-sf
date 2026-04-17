import os
import tkinter as tk
from tkinter import filedialog, messagebox

from src.theme import COLORS, FONTS, make_button, make_card, make_label
from src.audio import AUDIO_OK, get_output_devices, find_vbcable, get_device_info


class PlaylistPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._last_tick_state = None
        self._build()

    def _build(self):
        tk.Label(self, text="Playlist",
                 font=("Segoe UI Semibold", 16), fg=COLORS["white"],
                 bg=COLORS["bg"]).pack(anchor="w", pady=(0, 14))

        self._build_device_card()
        self._build_tracklist_card()
        self._build_controls_card()

    def _build_device_card(self):
        card, inner = make_card(self, "Output Device  (auto-selected)")
        card.pack(fill="x", pady=(0, 10))

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")

        self.device_var  = tk.StringVar(value="Scanning...")
        self.device_menu = tk.OptionMenu(row, self.device_var, "")
        self.device_menu.config(
            bg=COLORS["border"], fg=COLORS["text"], font=FONTS["body"],
            relief="flat", highlightthickness=0, width=46,
            activebackground=COLORS["accent"], activeforeground=COLORS["white"]
        )
        self.device_menu["menu"].config(
            bg=COLORS["border"], fg=COLORS["text"], font=FONTS["body"],
            activebackground=COLORS["accent"], activeforeground=COLORS["white"]
        )
        self.device_menu.pack(side="left")
        make_button(row, "Refresh", self.refresh_devices, padx=10, pady=6).pack(side="left", padx=8)

        self.vbc_label = make_label(inner, "", fg=COLORS["green"], font=FONTS["small"])
        self.vbc_label.pack(anchor="w", pady=(4, 0))
        self.ch_label  = make_label(inner, "", fg=COLORS["muted"],  font=FONTS["small"])
        self.ch_label.pack(anchor="w", pady=(2, 0))

    def _build_tracklist_card(self):
        card, inner = make_card(self, "Track List")
        card.pack(fill="both", expand=True, pady=(0, 10))

        toolbar = tk.Frame(inner, bg=COLORS["card"])
        toolbar.pack(fill="x", pady=(0, 8))

        make_button(toolbar, "+ Add",     self._add_files,   COLORS["accent"], COLORS["white"]).pack(side="left", padx=(0, 4))
        make_button(toolbar, "Remove",    self._remove_file, COLORS["red"],    COLORS["white"]).pack(side="left", padx=4)
        make_button(toolbar, "Clear All", self._clear_list,  COLORS["red"],    COLORS["white"]).pack(side="left", padx=4)

        self.loop_var = tk.BooleanVar()
        tk.Checkbutton(toolbar, text="Loop", variable=self.loop_var,
                       bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["border"],
                       activebackground=COLORS["card"], font=FONTS["body"]).pack(side="right")

        list_frame = tk.Frame(inner, bg=COLORS["bg"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, bg=COLORS["border"], troughcolor=COLORS["bg"])
        scrollbar.pack(side="right", fill="y")

        self.app.playlist_box = tk.Listbox(
            list_frame, bg=COLORS["bg"], fg=COLORS["text"],
            selectbackground=COLORS["accent"], selectforeground=COLORS["white"],
            font=FONTS["mono"], relief="flat", borderwidth=0,
            highlightthickness=0, activestyle="none",
            yscrollcommand=scrollbar.set
        )
        self.app.playlist_box.pack(fill="both", expand=True)
        self.app.playlist_box.bind("<Double-Button-1>", lambda e: self._play_selected())
        scrollbar.config(command=self.app.playlist_box.yview)

    def _build_controls_card(self):
        card, inner = make_card(self, "Player Controls")
        card.pack(fill="x")

        ctrl = tk.Frame(inner, bg=COLORS["card"])
        ctrl.pack(fill="x", pady=(0, 6))

        make_button(ctrl, "Play",  self._play_selected,    COLORS["green"],  COLORS["white"]).pack(side="left", padx=(0, 4))
        make_button(ctrl, "Pause", self.app.toggle_pause,  COLORS["yellow"], "#0d0d0d").pack(side="left", padx=4)
        make_button(ctrl, "Stop",  self.app.stop_audio,    COLORS["red"],    COLORS["white"]).pack(side="left", padx=4)

        self.now_label = make_label(inner, "Stopped", fg=COLORS["muted"], font=FONTS["small"])
        self.now_label.pack(anchor="w")

    def _play_selected(self):
        if not AUDIO_OK:
            messagebox.showerror("Missing", "pip install sounddevice soundfile numpy")
            return
        if self.app.player.device_idx is None:
            messagebox.showwarning("No Device", "No output device selected.")
            return

        box = self.app.playlist_box
        sel = box.curselection()
        if not sel:
            if box.size():
                box.selection_set(0)
                sel = (0,)
            else:
                messagebox.showinfo("Empty", "Add audio files first.")
                return

        path = box.get(sel[0])
        self.app.player.looping = self.loop_var.get()
        self.app.progress       = 0.0
        self.app.player.play(path)
        self.app.set_status(f"Playing: {os.path.basename(path)}")

    def refresh_devices(self):
        if not AUDIO_OK:
            self.device_var.set("sounddevice missing")
            return

        devices = get_output_devices()
        menu    = self.device_menu["menu"]
        menu.delete(0, "end")
        for idx, name in devices:
            menu.add_command(
                label=f"[{idx}]  {name}",
                command=lambda i=idx, n=name: self.app.select_device(i, n)
            )

        saved = self.app.config.get("device")
        for idx, name in devices:
            if idx == saved:
                self.app.select_device(idx, name)
                return

        idx, name = find_vbcable()
        if idx is not None:
            self.app.select_device(idx, name)
        elif devices:
            self.app.select_device(devices[0][0], devices[0][1])
        else:
            self.device_var.set("No devices found")

    def update_device_display(self, idx, name):
        self.device_var.set(f"[{idx}]  {name}")
        n_ch, sr = get_device_info(idx)
        is_vbc   = "cable input" in name.lower()

        self.vbc_label.config(
            text=f"VB-Cable: {name}" if is_vbc else "", fg=COLORS["green"])
        self.ch_label.config(
            text=f"Channels: {n_ch}  |  Sample rate: {sr} Hz",
            fg=COLORS["yellow"] if n_ch > 2 else COLORS["muted"]
        )

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Audio", "*.wav *.mp3 *.ogg *.flac *.aac"), ("All", "*.*")])
        for path in paths:
            self.app.playlist_box.insert("end", path)
        self.app.save_playlist()
        self.app.home_page.update_step1_label()

    def _remove_file(self):
        for i in reversed(self.app.playlist_box.curselection()):
            self.app.playlist_box.delete(i)
        self.app.save_playlist()
        self.app.home_page.update_step1_label()

    def _clear_list(self):
        if messagebox.askyesno("Confirm", "Clear entire playlist?"):
            self.app.playlist_box.delete(0, "end")
            self.app.config["playlist"] = []
            self.app.save_config()
            self.app.home_page.update_step1_label()

    def on_tick(self, playing, paused, name):
        state = (playing, paused, name)
        if state == self._last_tick_state:
            return
        self._last_tick_state = state

        if playing:
            label_text = f"{'Paused' if paused else 'Playing'}:  {name}"
            fg         = COLORS["yellow"] if paused else COLORS["green"]
        else:
            label_text = "Stopped"
            fg         = COLORS["muted"]

        self.now_label.config(text=label_text, fg=fg)
