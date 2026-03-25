# VC Changer

A Discord audio and virtual camera tool that routes audio through VB-Cable so others can hear it in voice calls.

Built with Python + Tkinter. No OBS required.

---

## Features

- Play audio files directly into Discord voice channels
- Virtual camera support (solid color, image, video, screen capture)
- Auto-detects VB-Cable on startup
- Built-in VB-Cable installer
- Playlist with loop support
- Volume control up to 200%
- Supports MP3, WAV, OGG, FLAC, AAC

---

## Requirements

**Python 3.9+**

Install dependencies:

```bash
pip install sounddevice soundfile numpy
pip install pydub
pip install opencv-python pyvirtualcam
pip install mss
```

For MP3 support you also need ffmpeg:

```bash
# Windows
winget install ffmpeg

# or download from https://ffmpeg.org/download.html
```

---

## Setup

**1. Install VB-Cable**

Download and install from https://vb-audio.com/Cable/

Run the installer as Administrator, then restart your PC.

The app also has a built-in installer — just click "Install VB-Cable Automatically" on first launch.

**2. Run the app**

```bash
python main.py
```

**3. Configure Discord**

Go to Discord Settings > Voice & Video > Input Device

Set it to: `CABLE Output (VB-Audio Virtual Cable)`

---

## How It Works

```
VC Changer  →  CABLE Input  →  CABLE Output  →  Discord mic input
```

VB-Cable creates a virtual audio device. The app sends audio to "CABLE Input", and Discord picks it up from "CABLE Output".

---

## Project Structure

```
vc_changer/
├── main.py
├── requirements.txt
├── README.md
└── src/
    ├── app.py              # main application + navigation
    ├── audio.py            # audio player + device detection
    ├── vcam.py             # virtual camera engine
    ├── theme.py            # colors, fonts, UI helpers
    ├── installer.py        # VB-Cable installer dialog
    └── ui/
        ├── splash.py       # intro/loading screen
        ├── page_home.py    # dashboard
        ├── page_playlist.py
        ├── page_camera.py
        └── page_guide.py
```

---

## Troubleshooting

**No sound in Discord?**
- Make sure Discord input is set to "CABLE Output" not "CABLE Input"
- Try restarting Discord after launching the app

**Camera not showing in Discord?**
- Click "Start Camera" first, then switch your camera in Discord to "OBS Virtual Camera"
- Restart Discord if it doesn't appear

**MP3 files not loading?**
- Install pydub: `pip install pydub`
- Install ffmpeg: `winget install ffmpeg`

---

## Author

**safouane02** — https://github.com/safouane02