from __future__ import annotations

import numpy as np
import sounddevice as sd

from .engines import AudioEngine
from .engines.base import CHANNELS, SAMPLE_RATE


class RealtimeAudioOutput:
    def __init__(self) -> None:
        self.engine: AudioEngine | None = None
        self.playing = False
        self.volume = 1.0
        self._stream: sd.OutputStream | None = None

    def set_engine(self, engine: AudioEngine | None) -> None:
        self.playing = False
        self.engine = engine

    def start(self) -> None:
        if self._stream:
            return
        self._stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=1024,
            latency="low",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if not self._stream:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None

    def _callback(self, outdata: np.ndarray, frames: int, _time, status) -> None:
        if not self.playing:
            outdata.fill(0)
            return

        try:
            if not self.engine:
                outdata.fill(0)
                return
            raw = self.engine.render(frames)
            pcm = np.ctypeslib.as_array(raw).reshape(frames, CHANNELS)
            if self.volume >= 0.999:
                outdata[:] = pcm
            else:
                outdata[:] = np.clip(pcm.astype(np.float32) * self.volume, -32768, 32767).astype(np.int16)
        except Exception:
            outdata.fill(0)
            self.playing = False
