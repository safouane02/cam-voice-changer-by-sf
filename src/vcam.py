import threading
import os

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    import pyvirtualcam
    VCAM_OK = True
except ImportError:
    VCAM_OK = False

try:
    import numpy as np
    NP_OK = True
except ImportError:
    NP_OK = False


class VCamEngine:
    def __init__(self):
        self.running      = False
        self.source       = "color"
        self.color        = (88, 101, 242)
        self.image_path   = ""
        self.video_path   = ""
        self.width        = 1280
        self.height       = 720
        self.fps          = 30
        self.video_frame  = 0
        self.total_frames = 0

        self._stop_event  = threading.Event()
        self._seek_to     = None
        self._seek_lock   = threading.Lock()

        self.on_status = None

    def start(self):
        if self.running:
            return
        self._stop_event.clear()
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._stop_event.set()
        self.running = False

    def seek(self, frame_index):
        with self._seek_lock:
            if self.total_frames > 0:
                self._seek_to = max(0, min(int(frame_index), self.total_frames - 1))
            else:
                self._seek_to = max(0, int(frame_index))

    def _run(self):
        if not (CV2_OK and VCAM_OK and NP_OK):
            if self.on_status:
                self.on_status("error", "opencv / pyvirtualcam not installed")
            return

        cap = self._open_video_capture()

        try:
            with pyvirtualcam.Camera(
                width=self.width, height=self.height,
                fps=self.fps, fmt=pyvirtualcam.PixelFormat.BGR
            ) as cam:
                self.running = True
                if self.on_status:
                    self.on_status("ok", cam.device)

                while not self._stop_event.is_set():
                    self._apply_pending_seek(cap)
                    frame = self._next_frame(cap)
                    if frame is None:
                        break
                    cam.send(frame)
                    cam.sleep_until_next_frame()

        except Exception as e:
            if self.on_status:
                self.on_status("error", str(e))
        finally:
            if cap:
                cap.release()
            self.running = False

    def _open_video_capture(self):
        if self.source != "video" or not self.video_path:
            return None
        cap = cv2.VideoCapture(self.video_path)
        if cap.isOpened():
            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            self.video_frame  = 0
        return cap

    def _apply_pending_seek(self, cap):
        with self._seek_lock:
            if self._seek_to is not None and cap is not None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._seek_to)
                self.video_frame = self._seek_to
                self._seek_to    = None

    def _next_frame(self, cap=None):
        w, h = self.width, self.height

        if self.source == "color":
            return self._solid_color_frame(w, h)

        if self.source == "image":
            return self._image_frame(w, h)

        if self.source == "video" and cap and cap.isOpened():
            return self._video_frame(cap, w, h)

        if self.source == "screen":
            return self._screen_capture_frame(w, h)

        return self._blank_frame(w, h)

    def _solid_color_frame(self, w, h):
        frame      = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:]   = (self.color[2], self.color[1], self.color[0])
        cv2.putText(frame, "Virtual Camera Active",
                    (w // 2 - 190, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        return frame

    def _image_frame(self, w, h):
        if os.path.exists(self.image_path):
            img = cv2.imread(self.image_path)
            if img is not None:
                return cv2.resize(img, (w, h))
        return self._blank_frame(w, h)

    def _video_frame(self, cap, w, h):
        ret, frame = cap.read()
        if ret:
            self.video_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or self.video_frame)
            return cv2.resize(frame, (w, h))

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.video_frame = 0
        ret, frame = cap.read()
        if ret:
            self.video_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or self.video_frame)
            return cv2.resize(frame, (w, h))

        return self._blank_frame(w, h)

    def _screen_capture_frame(self, w, h):
        try:
            import mss
            with mss.mss() as sct:
                raw = np.array(sct.grab(sct.monitors[1]))
                return cv2.resize(cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR), (w, h))
        except Exception:
            return self._blank_frame(w, h)

    def _blank_frame(self, w, h):
        frame    = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (15, 15, 25)
        return frame
