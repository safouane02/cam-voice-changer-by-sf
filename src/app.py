import json
import os
import tkinter as tk
from tkinter import messagebox
import webbrowser

from src.theme import COLORS, FONTS, make_button
from src.audio import AUDIO_OK, AudioPlayer, find_vbcable, get_output_devices
from src.vcam import VCamEngine
from src.installer import prompt_install_vbcable
from src.ui.page_home     import HomePage
from src.ui.page_playlist import PlaylistPage
from src.ui.page_camera   import CameraPage
from src.ui.page_guide    import GuidePage


CONFIG_FILE = "vc_config.json"
TICK_MS     = 100


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VC Changer  —  by safouane02")
        self.geometry("980x680")
        self.minsize(880, 600)
        self.configure(bg=COLORS["bg"])

        self.player   = AudioPlayer()
        self.vcam     = VCamEngine()
        self.config   = self._load_config()
        self.progress = 0.0

        self.playlist_box = None

        self._current_page = ""
        self._pages        = {}
        self._nav_refs     = {}

        self._build_ui()
        self.after(50, self._auto_setup)
        self._tick()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"playlist": [], "volume": 80, "device": None, "first_run": True}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save_playlist(self):
        if self.playlist_box:
            self.config["playlist"] = list(self.playlist_box.get(0, "end"))
            self.save_config()

    def set_status(self, text):
        self._status_var.set(text)

    def _auto_setup(self):
        if AUDIO_OK:
            saved = self.config.get("device")
            if saved is not None:
                for di, dn in get_output_devices():
                    if di == saved:
                        self.select_device(di, dn)
                        break
            else:
                idx, name = find_vbcable()
                if idx is not None:
                    self.select_device(idx, name)

        self.home_page.refresh_status()

        if self.config.get("playlist"):
            self._restore_playlist()

        if self.config.get("first_run", True):
            self.after(200, self._show_welcome)
            self.config["first_run"] = False
            self.save_config()

        self.playlist_page.refresh_devices()

    def _restore_playlist(self):
        valid = [f for f in self.config.get("playlist", []) if os.path.exists(f)]
        if not valid:
            return
        self.playlist_box.delete(0, "end")
        for path in valid:
            self.playlist_box.insert("end", path)
        self.config["playlist"] = valid
        self.home_page.update_step1_label()

        for w in self.home_page.resume_frame.winfo_children():
            w.destroy()
        make_button(
            self.home_page.resume_frame, "Resume Last Session",
            self.play_current, COLORS["card2"], COLORS["text"],
            padx=8, pady=4
        ).pack()

    def _show_welcome(self):
        dlg = tk.Toplevel(self)
        dlg.title("Welcome")
        dlg.configure(bg=COLORS["bg"])
        dlg.geometry("500x390")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self)

        tk.Frame(dlg, bg=COLORS["accent"], height=3).pack(fill="x")

        header = tk.Frame(dlg, bg=COLORS["bg"])
        header.pack(fill="x", padx=30, pady=(24, 0))
        tk.Label(header, text="Welcome to VC Changer",
                 font=FONTS["huge"], fg=COLORS["white"], bg=COLORS["bg"]).pack(anchor="w")
        tk.Label(header, text="by safouane02",
                 font=FONTS["body"], fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w")

        tk.Frame(dlg, bg=COLORS["border"], height=1).pack(fill="x", padx=30, pady=16)

        idx, name = find_vbcable()
        has_cable = idx is not None

        status = tk.Frame(dlg, bg=COLORS["card"],
                          highlightbackground=COLORS["border"], highlightthickness=1)
        status.pack(fill="x", padx=30, pady=(0, 12))
        cable_text  = f"VB-Cable found: {name}" if has_cable else "VB-Cable not installed"
        cable_color = COLORS["green"] if has_cable else COLORS["red"]
        tk.Label(status, text=f"  {cable_text}",
                 font=FONTS["title"], fg=cable_color, bg=COLORS["card"],
                 pady=10).pack(anchor="w")

        if not has_cable:
            make_button(dlg, "Install VB-Cable Automatically",
                        lambda: prompt_install_vbcable(dlg),
                        COLORS["accent"], COLORS["white"]).pack(pady=(0, 8))
            make_button(dlg, "Manual Download",
                        lambda: webbrowser.open("https://vb-audio.com/Cable/"),
                        COLORS["border"], COLORS["muted"], padx=10, pady=4).pack(pady=(0, 8))

        steps = tk.Frame(dlg, bg=COLORS["bg"])
        steps.pack(fill="x", padx=30)
        for i, step_text in enumerate([
            "Add audio files  (MP3 / WAV)",
            "Press Play",
            'In Discord:  Input Device  >  "CABLE Output"',
        ], 1):
            row = tk.Frame(steps, bg=COLORS["bg"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=str(i), font=("Segoe UI Semibold", 11),
                     fg=COLORS["accent"], bg=COLORS["bg"], width=2).pack(side="left")
            tk.Label(row, text=step_text, font=FONTS["body"],
                     fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left", padx=8)

        make_button(dlg, "Let's Go", dlg.destroy,
                    COLORS["green"], COLORS["white"], padx=28, pady=11).pack(pady=24)

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        self._build_sidebar_and_content()
        self._build_pages()
        self._show_page("home")

    def _build_topbar(self):
        bar = tk.Frame(self, bg=COLORS["sidebar"], height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Frame(bar, bg=COLORS["accent"], width=4).pack(side="left", fill="y")

        brand = tk.Frame(bar, bg=COLORS["sidebar"])
        brand.pack(side="left", padx=14)
        tk.Label(brand, text="VC Changer",
                 font=("Segoe UI Semibold", 15), fg=COLORS["white"],
                 bg=COLORS["sidebar"]).pack(anchor="w")
        tk.Label(brand, text="by safouane02",
                 font=FONTS["small"], fg=COLORS["muted"],
                 bg=COLORS["sidebar"]).pack(anchor="w")

        self._status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self._status_var,
                 font=FONTS["small"], fg=COLORS["muted"],
                 bg=COLORS["sidebar"]).pack(side="right", padx=18)

        tk.Frame(self, bg=COLORS["accent"], height=2).pack(fill="x")

    def _build_sidebar_and_content(self):
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=172)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=COLORS["sidebar"], height=12).pack(fill="x")
        tk.Label(sidebar, text="NAVIGATION",
                 font=("Segoe UI", 7), fg=COLORS["muted"],
                 bg=COLORS["sidebar"]).pack(anchor="w", padx=16, pady=(0, 4))

        self._sidebar = sidebar

        self._content = tk.Frame(body, bg=COLORS["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        for key, label in [("home", "Home"), ("audio", "Playlist"),
                             ("camera", "Camera"), ("guide", "Guide")]:
            self._add_nav_item(key, label)

        tk.Frame(sidebar, bg=COLORS["sidebar"]).pack(fill="both", expand=True)
        tk.Label(sidebar, text="v3.1",
                 font=FONTS["small"], fg=COLORS["border"],
                 bg=COLORS["sidebar"]).pack(pady=(0, 10))

    def _add_nav_item(self, key, text):
        frame = tk.Frame(self._sidebar, bg=COLORS["sidebar"], cursor="hand2")
        frame.pack(fill="x", pady=1)

        indicator = tk.Frame(frame, bg=COLORS["sidebar"], width=3)
        indicator.pack(side="left", fill="y")

        inner = tk.Frame(frame, bg=COLORS["sidebar"])
        inner.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        label = tk.Label(inner, text=text, font=("Segoe UI Semibold", 9),
                          bg=COLORS["sidebar"], fg=COLORS["muted"], anchor="w")
        label.pack(side="left")

        self._nav_refs[key] = (label, indicator, frame, inner)

        for widget in (frame, inner, label):
            widget.bind("<Button-1>", lambda e, k=key: self._show_page(k))
            widget.bind("<Enter>",    lambda e, k=key: self._nav_hover(k, True))
            widget.bind("<Leave>",    lambda e, k=key: self._nav_hover(k, False))

    def _nav_hover(self, key, active):
        if key == self._current_page:
            return
        label, _, frame, inner = self._nav_refs[key]
        bg    = COLORS["card2"] if active else COLORS["sidebar"]
        color = COLORS["text"]  if active else COLORS["muted"]
        for widget in (label, frame, inner):
            widget.config(bg=bg)
        label.config(fg=color)

    def _show_page(self, key):
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()

        self._pages[key].pack(fill="both", expand=True, padx=18, pady=16)
        self._current_page = key

        for k, (label, indicator, frame, inner) in self._nav_refs.items():
            if k == key:
                label.config(fg=COLORS["white"], bg=COLORS["card2"])
                indicator.config(bg=COLORS["accent"])
                frame.config(bg=COLORS["card2"])
                inner.config(bg=COLORS["card2"])
            else:
                label.config(fg=COLORS["muted"], bg=COLORS["sidebar"])
                indicator.config(bg=COLORS["sidebar"])
                frame.config(bg=COLORS["sidebar"])
                inner.config(bg=COLORS["sidebar"])

    def _build_pages(self):
        self.home_page     = HomePage(self._content, self)
        self.playlist_page = PlaylistPage(self._content, self)
        self.camera_page   = CameraPage(self._content, self)
        guide_page         = GuidePage(self._content, self)

        self._pages = {
            "home":   self.home_page,
            "audio":  self.playlist_page,
            "camera": self.camera_page,
            "guide":  guide_page,
        }

        self.player.on_done  = lambda: setattr(self, "progress", 0.0)
        self.player.on_tick  = lambda v: setattr(self, "progress", v)
        self.player.on_error = self._on_audio_error
        self.player.set_volume(self.config.get("volume", 80))

    # ── Player Actions ───────────────────────────────────────────────────────

    def play_current(self):
        if not AUDIO_OK:
            messagebox.showerror("Missing Library",
                                 "Run:  pip install sounddevice soundfile numpy")
            return

        if self.player.device_idx is None:
            idx, name = find_vbcable()
            if idx is not None:
                self.select_device(idx, name)
            else:
                messagebox.showwarning("No VB-Cable",
                                       "VB-Cable not found.\n\nDownload: https://vb-audio.com/Cable/")
                return

        box = self.playlist_box
        if box.size() == 0:
            messagebox.showinfo("No Files", "Add audio files first (Step 1).")
            return

        sel       = box.curselection()
        idx_track = sel[0] if sel else 0
        box.selection_set(idx_track)
        path = box.get(idx_track)

        self.player.looping = False
        self.progress       = 0.0
        self.player.play(path)

        name = os.path.basename(path)[:50]
        self.home_page.step2_label.config(text=f"Playing: {name}", fg=COLORS["green"])
        self.set_status(f"Playing: {name}")

    def toggle_pause(self):
        self.player.toggle_pause()

    def stop_audio(self):
        self.player.stop()
        self.progress = 0.0
        self.home_page.step2_label.config(text="Stopped", fg=COLORS["muted"])
        self.set_status("Stopped")

    def select_device(self, idx, name):
        self.player.device_idx  = idx
        self.player.device_name = name
        self.config["device"]   = idx
        self.save_config()

        if hasattr(self, "playlist_page"):
            self.playlist_page.update_device_display(idx, name)

        self.set_status(f"Device [{idx}]: {name}")
        if hasattr(self, "home_page"):
            self.home_page.refresh_status()

    def _on_audio_error(self, msg):
        self.after(0, lambda: messagebox.showerror("Audio Error", msg))
        self.after(0, lambda: self.set_status("Audio error"))

    # ── Tick Loop ────────────────────────────────────────────────────────────

    def _tick(self):
        self.home_page.draw_progress()

        playing = self.player.playing
        paused  = self.player.paused
        name    = os.path.basename(self.player.current)[:50] if self.player.current else ""

        self.home_page.on_tick(playing, paused, name)
        if hasattr(self, "playlist_page"):
            self.playlist_page.on_tick(playing, paused, name)

        self.after(TICK_MS, self._tick)

    def destroy(self):
        self.player.stop()
        self.vcam.stop()
        super().destroy()    def destroy(self):
        self.player.stop()
        self.vcam.stop()
        super().destroy()
