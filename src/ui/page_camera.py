import os
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from src.theme import COLORS, FONTS, make_button, make_card, make_label
from src.audio import AUDIO_OK, find_vbcable
from src.vcam import CV2_OK, VCAM_OK


class CameraPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app             = app
        self._vid_audio_tmp  = None
        self._is_dragging    = False
        self._pending_seek   = None
        self._build()

    def _build(self):
        tk.Label(self, text="Virtual Camera",
                 font=("Segoe UI Semibold", 16), fg=COLORS["white"],
                 bg=COLORS["bg"]).pack(anchor="w", pady=(0, 14))

        self._build_status_card()
        self._build_source_card()
        self._build_resolution_card()
        self._build_timeline()
        self._build_deps_card()

    def _build_status_card(self):
        card, inner = make_card(self, "Camera Status")
        card.pack(fill="x", pady=(0, 10))

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")
        self.status_label = make_label(row, "Stopped", font=FONTS["title"], fg=COLORS["red"])
        self.status_label.pack(side="left")
        self.device_label = make_label(row, "", fg=COLORS["muted"], font=FONTS["small"])
        self.device_label.pack(side="left", padx=14)

        make_button(row, "Stop",         self._stop_camera,  COLORS["red"],   COLORS["white"]).pack(side="right", padx=4)
        make_button(row, "Start Camera", self._start_camera, COLORS["green"], COLORS["white"]).pack(side="right", padx=4)

        self.audio_label = make_label(inner, "", fg=COLORS["muted"], font=FONTS["small"])
        self.audio_label.pack(anchor="w", pady=(4, 0))

    def _build_source_card(self):
        card, inner = make_card(self, "Source")
        card.pack(fill="x", pady=(0, 10))

        self.source_var = tk.StringVar(value="color")
        rb_row = tk.Frame(inner, bg=COLORS["card"])
        rb_row.pack(fill="x", pady=(0, 8))

        for value, label in [("color", "Solid Color"), ("image", "Image"),
                               ("video", "Video"),       ("screen", "Screen")]:
            tk.Radiobutton(
                rb_row, text=label, variable=self.source_var, value=value,
                bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["border"],
                activebackground=COLORS["card"], font=FONTS["body"],
                command=self._on_source_change
            ).pack(side="left", padx=12)

        self.options_frame = tk.Frame(inner, bg=COLORS["card"])
        self.options_frame.pack(fill="x")
        self._build_color_options()

    def _build_resolution_card(self):
        card, inner = make_card(self, "Resolution & FPS")
        card.pack(fill="x", pady=(0, 10))

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")

        make_label(row, "Resolution", fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")
        self.res_var = tk.StringVar(value="1280x720")
        res_menu = tk.OptionMenu(row, self.res_var, "640x480", "854x480", "1280x720", "1920x1080")
        res_menu.config(bg=COLORS["border"], fg=COLORS["text"], font=FONTS["small"],
                        relief="flat", highlightthickness=0, activebackground=COLORS["accent"])
        res_menu["menu"].config(bg=COLORS["border"], fg=COLORS["text"], font=FONTS["small"],
                                activebackground=COLORS["accent"])
        res_menu.pack(side="left", padx=10)

        make_label(row, "FPS", fg=COLORS["muted"], font=FONTS["small"]).pack(side="left", padx=(14, 0))
        self.fps_var = tk.StringVar(value="30")
        fps_menu = tk.OptionMenu(row, self.fps_var, "15", "24", "30", "60")
        fps_menu.config(bg=COLORS["border"], fg=COLORS["text"], font=FONTS["small"],
                        relief="flat", highlightthickness=0, activebackground=COLORS["accent"])
        fps_menu["menu"].config(bg=COLORS["border"], fg=COLORS["text"], font=FONTS["small"],
                                activebackground=COLORS["accent"])
        fps_menu.pack(side="left", padx=8)

    def _build_timeline(self):
        self.seek_var  = tk.DoubleVar(value=0.0)
        self.time_label = make_label(self, "00:00 / 00:00", fg=COLORS["muted"], font=FONTS["small"])
        self.time_label.pack(anchor="w", pady=(0, 4), padx=14)

        self.seek_scale = tk.Scale(
            self, variable=self.seek_var,
            from_=0, to=1, resolution=0.1,
            orient="horizontal", showvalue=False,
            bg=COLORS["card"], fg=COLORS["text"], troughcolor=COLORS["border"],
            length=660, command=self._on_seek_drag
        )
        self.seek_scale.bind("<ButtonPress-1>",   lambda e: setattr(self, "_is_dragging", True))
        self.seek_scale.bind("<ButtonRelease-1>",  self._on_seek_release)
        self.seek_scale.config(state="disabled")
        self.seek_scale.pack(fill="x", padx=14, pady=(0, 10))

        self.after(250, self._update_timeline)

    def _build_deps_card(self):
        card, inner = make_card(self, "Dependencies")
        card.pack(fill="x")

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")
        for dep_name, ok in [("sounddevice", AUDIO_OK),
                               ("opencv-python", CV2_OK),
                               ("pyvirtualcam", VCAM_OK)]:
            color = COLORS["green"] if ok else COLORS["red"]
            make_label(row, f"{'OK' if ok else 'Missing'}  {dep_name}",
                       fg=color, font=FONTS["mono"]).pack(side="left", padx=(0, 18))

    def _build_color_options(self):
        for w in self.options_frame.winfo_children():
            w.destroy()
        make_label(self.options_frame, "Color:", fg=COLORS["muted"],
                   font=FONTS["small"]).pack(side="left", padx=(0, 10))
        for hex_c, rgb in [
            ("#5865f2", (88, 101, 242)),
            ("#23a55a", (35, 165, 90)),
            ("#ed4245", (237, 66, 69)),
            ("#000000", (0, 0, 0)),
            ("#ffffff", (255, 255, 255)),
            ("#1a1a2e", (26, 26, 46)),
        ]:
            tk.Button(
                self.options_frame, bg=hex_c, width=2, relief="flat", cursor="hand2",
                command=lambda r=rgb: setattr(self.app.vcam, "color", r)
            ).pack(side="left", padx=2, pady=2)

    def _build_image_options(self):
        for w in self.options_frame.winfo_children():
            w.destroy()
        self.img_var = tk.StringVar()
        make_label(self.options_frame, "Image:", fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")
        tk.Entry(self.options_frame, textvariable=self.img_var, bg=COLORS["bg"],
                 fg=COLORS["text"], font=FONTS["mono"], insertbackground=COLORS["white"],
                 relief="flat", width=36).pack(side="left", padx=8)
        make_button(self.options_frame, "Browse",
                    lambda: self._browse(self.img_var, [("Images", "*.png *.jpg *.jpeg *.bmp")]),
                    COLORS["accent"], COLORS["white"]).pack(side="left")

    def _build_video_options(self):
        for w in self.options_frame.winfo_children():
            w.destroy()
        self.vid_var = tk.StringVar()
        make_label(self.options_frame, "Video:", fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")
        tk.Entry(self.options_frame, textvariable=self.vid_var, bg=COLORS["bg"],
                 fg=COLORS["text"], font=FONTS["mono"], insertbackground=COLORS["white"],
                 relief="flat", width=36).pack(side="left", padx=8)
        make_button(self.options_frame, "Browse",
                    lambda: self._browse(self.vid_var, [("Video", "*.mp4 *.avi *.mkv *.mov")]),
                    COLORS["accent"], COLORS["white"]).pack(side="left")

    def _build_screen_options(self):
        for w in self.options_frame.winfo_children():
            w.destroy()
        make_label(self.options_frame, "Captures full screen  (pip install mss)",
                   fg=COLORS["muted"], font=FONTS["small"]).pack(side="left")

    def _on_source_change(self):
        src = self.source_var.get()
        builders = {
            "color":  self._build_color_options,
            "image":  self._build_image_options,
            "video":  self._build_video_options,
            "screen": self._build_screen_options,
        }
        builders.get(src, self._build_color_options)()

    def _start_camera(self):
        if not (CV2_OK and VCAM_OK):
            messagebox.showerror("Missing", "pip install opencv-python pyvirtualcam")
            return

        src  = self.source_var.get()
        vcam = self.app.vcam
        vcam.source      = src
        vcam.video_frame  = 0
        vcam.total_frames = 0
        vcam._seek_to     = None

        if src == "image" and hasattr(self, "img_var"):
            vcam.image_path = self.img_var.get()
        if src == "video" and hasattr(self, "vid_var"):
            vcam.video_path = self.vid_var.get()

        w, h = self.res_var.get().split("x")
        vcam.width  = int(w)
        vcam.height = int(h)
        vcam.fps    = self._detect_fps(src, vcam.video_path)

        def _on_status(state, msg):
            if state == "ok":
                self.status_label.config(text="Running", fg=COLORS["green"])
                self.device_label.config(text=f"  {msg}")
                self.app.set_status(f"Camera: {msg}")
            elif state == "error":
                self.status_label.config(text="Error", fg=COLORS["red"])
                self.device_label.config(text=f"  {msg}")
                self.after(0, lambda: messagebox.showerror("Camera Error", msg))

        vcam.on_status = _on_status

        if src == "video" and hasattr(self, "vid_var") and self.vid_var.get() and AUDIO_OK:
            vid_path = self.vid_var.get()
            if os.path.exists(vid_path):
                self._start_with_video_audio(vid_path)
                return

        self._launch_camera()

    def _detect_fps(self, src, video_path):
        if src == "video" and video_path and os.path.exists(video_path):
            try:
                import cv2
                cap = cv2.VideoCapture(video_path)
                src_fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                if src_fps and src_fps > 0:
                    return int(round(src_fps))
            except Exception:
                pass
        return int(self.fps_var.get())

    def _start_with_video_audio(self, vid_path):
        player = self.app.player
        if player.device_idx is None:
            idx, name = find_vbcable()
            if idx is not None:
                self.app.select_device(idx, name)

        if player.device_idx is None:
            self._launch_camera()
            return

        self.status_label.config(text="Extracting audio...", fg=COLORS["yellow"])
        self.update_idletasks()

        def _extract_thread():
            wav, err = self._extract_audio(vid_path)
            self._vid_audio_tmp = wav
            self.after(0, lambda: self._launch_camera(audio_wav=wav, audio_err=err))

        threading.Thread(target=_extract_thread, daemon=True).start()

    def _launch_camera(self, audio_wav=None, audio_err=None):
        if audio_wav:
            self.app.player.looping = True
            self.app.player.play(audio_wav)
            self.audio_label.config(text="Video audio  >  VB-Cable", fg=COLORS["green"])
        elif audio_err:
            self.audio_label.config(text=f"Audio extract failed: {audio_err}", fg=COLORS["yellow"])

        self.app.vcam.start()
        self.status_label.config(text="Starting...", fg=COLORS["yellow"])

    def _stop_camera(self):
        self.app.vcam.stop()
        self.app.player.stop()
        self.app.player.looping = False
        self.audio_label.config(text="", fg=COLORS["muted"])

        if self._vid_audio_tmp and os.path.exists(self._vid_audio_tmp):
            try:
                os.remove(self._vid_audio_tmp)
            except Exception:
                pass
        self._vid_audio_tmp = None

        self.status_label.config(text="Stopped", fg=COLORS["red"])
        self.device_label.config(text="")
        self.app.set_status("Camera stopped")

    def _extract_audio(self, video_path):
        tmp = tempfile.mktemp(suffix="_vcam_audio.wav")
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", video_path,
                 "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", tmp],
                capture_output=True, timeout=30
            )
            if result.returncode == 0 and os.path.exists(tmp):
                return tmp, None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            from pydub import AudioSegment
            AudioSegment.from_file(video_path).export(tmp, format="wav")
            if os.path.exists(tmp):
                return tmp, None
        except Exception as e:
            return None, str(e)

        return None, "ffmpeg not found and pydub failed"

    def _on_seek_drag(self, value):
        vcam = self.app.vcam
        if not (vcam.running and vcam.source == "video" and vcam.total_frames and vcam.fps):
            return
        try:
            self._pending_seek = float(value)
        except Exception:
            pass

    def _on_seek_release(self, event=None):
        self._is_dragging = False
        if self._pending_seek is None:
            return

        sec = self._pending_seek
        self._pending_seek = None

        self.app.vcam.seek(int(sec * self.app.vcam.fps))

        if self._vid_audio_tmp:
            self.app.player.stop()
            self.app.player.looping = True
            self.app.player.play(self._vid_audio_tmp, start_time=sec)

    def _update_timeline(self):
        vcam = self.app.vcam
        if vcam.running and vcam.source == "video" and vcam.fps > 0 and vcam.total_frames > 0:
            current_sec = vcam.video_frame / vcam.fps
            total_sec   = vcam.total_frames / vcam.fps

            self.time_label.config(
                text=f"{self._fmt_time(current_sec)} / {self._fmt_time(total_sec)}")
            self.seek_scale.config(state="normal", to=total_sec)
            if not self._is_dragging:
                self.seek_var.set(min(current_sec, total_sec))
        else:
            self.time_label.config(text="00:00 / 00:00")
            self.seek_scale.config(state="disabled")

        self.after(250, self._update_timeline)

    def _fmt_time(self, seconds):
        try:
            seconds = max(0.0, float(seconds))
        except Exception:
            return "00:00"
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

    def _browse(self, var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)
