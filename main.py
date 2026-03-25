"""
VC Changer - Discord Audio & Virtual Camera Tool
Author: safouane02
"""

import tkinter as tk

from src.audio import AUDIO_OK
from src.ui.splash import IntroScreen
from src.app import App


def launch():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    if not AUDIO_OK:
        print("Missing audio libraries.")
        print("Run:  pip install sounddevice soundfile numpy")

    root = tk.Tk()
    root.withdraw()

    IntroScreen(on_done=lambda: (root.destroy(), launch()))
    root.mainloop()
