"""
VC Changer - Discord Audio & Virtual Camera Tool
github.com/safouane02
"""

from src.audio import AUDIO_OK
from src.app import App


def main():
    if not AUDIO_OK:
        print("[warn] sounddevice / soundfile / numpy not installed")
        print("       pip install sounddevice soundfile numpy")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()        print("Run:  pip install sounddevice soundfile numpy")

    root = tk.Tk()
    root.withdraw()

    IntroScreen(on_done=lambda: (root.destroy(), launch()))
    root.mainloop()
