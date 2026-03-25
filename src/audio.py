import threading
import time

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_OK = True
except ImportError:
    AUDIO_OK = False


def get_output_devices():
    if not AUDIO_OK:
        return []
    try:
        return [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_output_channels"] > 0
        ]
    except Exception:
        return []


def find_vbcable():
    devices = get_output_devices()
    best = None
    for idx, name in devices:
        lower = name.lower()
        if "cable input" in lower and "16ch" not in lower:
            best = best or (idx, name)
    if best:
        return best
    for idx, name in devices:
        if "cable input" in name.lower():
            return idx, name
    return None, None


def is_vbcable_installed():
    idx, _ = find_vbcable()
    return idx is not None


def get_device_info(device_idx):
    try:
        info = sd.query_devices(device_idx, "output")
        return int(info["max_output_channels"]), int(info["default_samplerate"])
    except Exception:
        return 2, 44100


class AudioPlayer:
    def __init__(self):
        self.device_idx  = None
        self.device_name = ""
        self.playing     = False
        self.paused      = False
        self.looping     = False
        self.volume      = 0.8
        self.current     = ""

        self._stop_event  = threading.Event()
        self._start_time  = 0.0

        self.on_done  = None
        self.on_tick  = None
        self.on_error = None

    def play(self, filepath, start_time=0.0):
        self.stop()
        time.sleep(0.08)
        self._stop_event.clear()
        self.current     = filepath
        self._start_time = max(0.0, float(start_time))
        threading.Thread(target=self._playback_loop, args=(filepath,), daemon=True).start()

    def _playback_loop(self, filepath):
        wav_path, err = self._to_wav(filepath)
        if not wav_path:
            self.playing = False
            if self.on_error:
                self.on_error(f"Cannot load file.\n\nDetails: {err}")
            return

        n_channels, sample_rate = get_device_info(self.device_idx)

        while True:
            self.playing = True
            try:
                self._stream_audio(wav_path, n_channels, sample_rate)
            except Exception as e:
                self.playing = False
                if self.on_error:
                    self.on_error(f"Playback error:\n\n{e}")
                return

            if self._stop_event.is_set() or not self.looping:
                break

        self.playing = False
        if self.on_tick:
            self.on_tick(0.0)
        if self.on_done:
            self.on_done()

    def _stream_audio(self, wav_path, n_channels, target_sr):
        data, file_sr = sf.read(wav_path, dtype="float32", always_2d=True)

        if data.shape[1] == 1:
            mono = data[:, 0]
        else:
            mono = data[:, :2].mean(axis=1)

        if file_sr != target_sr:
            n    = int(len(mono) * target_sr / file_sr)
            xold = np.linspace(0, 1, len(mono))
            xnew = np.linspace(0, 1, n)
            mono = np.interp(xnew, xold, mono).astype("float32")

        total     = len(mono)
        start_idx = int(round(self._start_time * target_sr))
        start_idx = max(0, min(start_idx, total - 1)) if total > 0 else 0

        frame       = np.zeros((total, n_channels), dtype="float32")
        frame[:, 0] = mono
        if n_channels >= 2:
            frame[:, 1] = mono

        pos       = start_idx
        chunk     = 1024
        stream    = sd.OutputStream(
            samplerate=target_sr, channels=n_channels,
            dtype="float32", device=self.device_idx,
            blocksize=chunk, latency="low"
        )
        stream.start()

        try:
            while pos < total:
                if self._stop_event.is_set():
                    break
                while self.paused:
                    time.sleep(0.05)
                    if self._stop_event.is_set():
                        break

                block = frame[pos:pos + chunk].copy()
                if len(block) < chunk:
                    block = np.pad(block, ((0, chunk - len(block)), (0, 0)))

                block *= self.volume
                np.clip(block, -1.0, 1.0, out=block)
                stream.write(block)

                pos += chunk
                if self.on_tick and total > 0:
                    self.on_tick(min(pos / total, 1.0))
        finally:
            stream.stop()
            stream.close()

    def _to_wav(self, path):
        if path.lower().endswith(".wav"):
            return path, None
        out = path.rsplit(".", 1)[0] + "_vc_tmp.wav"
        try:
            from pydub import AudioSegment
            AudioSegment.from_file(path).export(out, format="wav")
            return out, None
        except Exception as e:
            return None, str(e)

    def stop(self):
        self._stop_event.set()
        self.playing = False
        self.paused  = False

    def toggle_pause(self):
        self.paused = not self.paused

    def set_volume(self, percent):
        self.volume = max(0.0, min(2.0, percent / 100.0))
