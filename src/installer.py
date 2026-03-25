import ctypes
import os
import tempfile
import threading
import urllib.request
import zipfile
import tkinter as tk
from tkinter import messagebox

from src.theme import COLORS, FONTS, make_button
from src.audio import is_vbcable_installed


VBCABLE_DOWNLOAD_URL = "https://download.vb-audio.com/Download_vbcable/VBCable_Setup_Pack43.zip"


def prompt_install_vbcable(parent):
    if is_vbcable_installed():
        messagebox.showinfo(
            "Already Installed",
            "VB-Cable is already installed on this system.\n\n"
            "If Discord still doesn't detect it, try restarting your PC.",
            parent=parent
        )
        return
    VBCableInstaller(parent)


class VBCableInstaller(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Installing VB-Cable")
        self.configure(bg=COLORS["bg"])
        self.geometry("420x210")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self._center()

        self._cancelled = threading.Event()
        self._tmp_dir   = tempfile.mkdtemp(prefix="vbcable_")
        self._zip_path  = os.path.join(self._tmp_dir, "vbcable.zip")

        self._build()
        threading.Thread(target=self._run, daemon=True).start()

    def _center(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"420x210+{(sw - 420) // 2}+{(sh - 210) // 2}")

    def _build(self):
        tk.Frame(self, bg=COLORS["accent"], height=3).pack(fill="x")

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(body, text="VB-Cable Setup",
                 font=FONTS["big"], fg=COLORS["white"], bg=COLORS["bg"]).pack(anchor="w")

        self._status_label = tk.Label(body, text="Starting download...",
                                      font=FONTS["body"], fg=COLORS["muted"], bg=COLORS["bg"])
        self._status_label.pack(anchor="w", pady=(6, 10))

        bar_track = tk.Frame(body, bg=COLORS["border"], height=6)
        bar_track.pack(fill="x")
        bar_track.pack_propagate(False)

        self._progress_bar = tk.Frame(bar_track, bg=COLORS["accent"], height=6, width=0)
        self._progress_bar.place(x=0, y=0, relheight=1.0)

        self._pct_label = tk.Label(body, text="0%",
                                   font=FONTS["small"], fg=COLORS["muted"], bg=COLORS["bg"])
        self._pct_label.pack(anchor="e", pady=(4, 0))

        self._cancel_btn = make_button(body, "Cancel", self._on_cancel,
                                       COLORS["border"], COLORS["text"], padx=16, pady=6)
        self._cancel_btn.pack(anchor="e", pady=(10, 0))

    def _set_status(self, text, color=None):
        self.after(0, lambda: self._status_label.config(
            text=text, fg=color or COLORS["muted"]
        ))

    def _set_progress(self, pct):
        def _update():
            total_w = self._progress_bar.master.winfo_width()
            self._progress_bar.place(x=0, y=0, relheight=1.0,
                                     width=int(total_w * pct / 100))
            self._pct_label.config(text=f"{int(pct)}%")
        self.after(0, _update)

    def _on_cancel(self):
        self._cancelled.set()
        self.destroy()

    def _run(self):
        try:
            self._download()
            if self._cancelled.is_set():
                return
            self._extract()
            if self._cancelled.is_set():
                return
            self._launch_installer()
        except Exception as e:
            self._set_status(f"Error: {e}", COLORS["red"])
            self.after(0, lambda: messagebox.showerror(
                "Install Failed", f"Could not install VB-Cable:\n\n{e}", parent=self
            ))

    def _download(self):
        self._set_status("Downloading VB-Cable...", COLORS["yellow"])

        def _on_progress(block_count, block_size, total_size):
            if self._cancelled.is_set():
                raise Exception("Cancelled")
            if total_size > 0:
                pct = min(block_count * block_size / total_size * 100, 100)
                self._set_progress(pct * 0.7)

        urllib.request.urlretrieve(VBCABLE_DOWNLOAD_URL, self._zip_path, _on_progress)
        self._set_progress(70)

    def _extract(self):
        self._set_status("Extracting files...", COLORS["yellow"])
        with zipfile.ZipFile(self._zip_path, "r") as z:
            z.extractall(self._tmp_dir)
        self._set_progress(90)

    def _launch_installer(self):
        self._set_status("Launching installer (Admin required)...", COLORS["yellow"])

        exe_name  = "VBCABLE_Setup_x64.exe"
        setup_exe = os.path.join(self._tmp_dir, exe_name)
        if not os.path.exists(setup_exe):
            exe_name  = "VBCABLE_Setup.exe"
            setup_exe = os.path.join(self._tmp_dir, exe_name)

        if not os.path.exists(setup_exe):
            raise FileNotFoundError("Installer not found in the downloaded package.")

        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", setup_exe, None, self._tmp_dir, 1
        )
        if result <= 32:
            raise OSError(f"Windows could not launch the installer (code {result}).")

        self._set_progress(100)
        self._set_status("Installer launched!", COLORS["green"])
        self.after(0, self._show_success)

    def _show_success(self):
        self._cancel_btn.config(text="Close")
        messagebox.showinfo(
            "Installer Launched",
            "The VB-Cable installer is now open.\n\n"
            "Steps:\n"
            "  1. Click 'Install Driver'\n"
            "  2. Restart your PC if asked\n"
            "  3. Re-open VC Changer\n\n"
            "Discord Input Device should then show\n"
            "  'CABLE Output (VB-Audio Virtual Cable)'",
            parent=self
        )
