"""Screen capture using mss (fast, cross-platform screenshot library).
Captures the full screen (all monitors combined) as a numpy array."""

import mss
import numpy as np


class ScreenCapturer:
    def __init__(self, monitor_index: int = 0):
        # monitor_index=0 in mss means "all monitors combined" —
        # this ensures nothing is missed on a multi-monitor setup.
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[monitor_index]

    def capture(self) -> np.ndarray:
        shot = self.sct.grab(self.monitor)
        img = np.array(shot)  # BGRA
        return img[:, :, :3][:, :, ::-1]  # drop alpha, BGR->RGB

    def close(self):
        self.sct.close()
