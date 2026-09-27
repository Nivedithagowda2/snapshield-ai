"""Frame differencing — decides whether the screen has changed enough
to bother running OCR again. This is what keeps the app from wastefully
re-analyzing a static screen at full rate."""

import numpy as np


class FrameDiffer:
    def __init__(self, threshold: float = 0.02):
        """threshold: fraction of pixels that must change to count as
        'the screen changed' (0.02 = 2%)."""
        self.threshold = threshold
        self._last_frame = None

    def has_changed(self, frame: np.ndarray) -> bool:
        if self._last_frame is None or self._last_frame.shape != frame.shape:
            self._last_frame = frame
            return True

        small_new = frame[::8, ::8]
        small_old = self._last_frame[::8, ::8]
        diff = np.abs(small_new.astype(int) - small_old.astype(int))
        changed_fraction = float(np.mean(diff > 20))

        self._last_frame = frame
        return changed_fraction > self.threshold
