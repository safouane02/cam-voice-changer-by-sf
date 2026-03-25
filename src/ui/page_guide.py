import tkinter as tk

from src.theme import COLORS, FONTS


GUIDE_TEXT = """\
AUDIO SETUP  (Automatic — done for you)
════════════════════════════════════════════════════════

1. Install VB-Cable (one-time):
   https://vb-audio.com/Cable/
   Run as Admin  >  Restart PC

2. Open this app  >  Home  >  auto-detects CABLE Input
   (If missing, use the "Install Automatically" button in the Welcome dialog)

3. Discord Settings  >  Voice & Video
   Input Device: "CABLE Output (VB-Audio Virtual Cable)"
   Use the  Copy Device Name  button on the Home page

Signal flow:
   This App  >  CABLE Input  >  CABLE Output  >  Discord mic


TEST (without Discord open)
════════════════════════════════════════════════════════
   mmsys.cpl  >  Recording  >  CABLE Output  >  Listen tab
   "Listen to this device"  >  pick your speakers
   Play a file  >  you should hear it from speakers


DEPENDENCIES
════════════════════════════════════════════════════════
   pip install sounddevice soundfile numpy
   pip install pydub                       (MP3 support)
   pip install opencv-python pyvirtualcam  (virtual camera)
   pip install mss                         (screen capture)
   winget install ffmpeg                   (MP3 support)


TROUBLESHOOTING
════════════════════════════════════════════════════════
No sound in Discord?
   Make sure Discord Input = "CABLE Output"  (not CABLE Input!)
   Run diagnose.py to test each VB-Cable device

Camera not showing?
   Restart Discord after clicking Start Camera
   Discord  >  Video  >  "OBS Virtual Camera"


Author: safouane02
github.com/safouane02
"""


class GuidePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self._build()

    def _build(self):
        tk.Label(self, text="Guide",
                 font=("Segoe UI Semibold", 16), fg=COLORS["white"],
                 bg=COLORS["bg"]).pack(anchor="w", pady=(0, 14))

        text_widget = tk.Text(
            self, bg=COLORS["card"], fg=COLORS["text"], font=FONTS["mono"],
            relief="flat", borderwidth=0, highlightthickness=0,
            padx=20, pady=18, wrap="word",
            selectbackground=COLORS["accent"], spacing1=2, spacing3=2
        )
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("end", GUIDE_TEXT)
        text_widget.config(state="disabled")
