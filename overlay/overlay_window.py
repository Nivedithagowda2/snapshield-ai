"""Transparent, click-through, always-on-top overlay window that draws
blur boxes over detected sensitive regions on screen.

Boxes are NOT time-based. A box stays visible for as long as it keeps
getting re-detected on each OCR pass — regardless of how long that
takes, or how long the person stays on the same screen. It disappears
only once an OCR pass completes and did NOT see it again."""

import ctypes
import tkinter as tk 
import threading
    
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: 
    try: 
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class ProtectionOverlay:
    def __init__(self):
        self._boxes = {}  # box_id -> (coords, last_seen_generation)
        self._lock = threading.Lock()
        self._root = None
        self._canvas = None

    def start(self):
        self._root = tk.Tk()
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.99)
        self._root.attributes("-transparentcolor", "black")
        self._root.overrideredirect(True)
        self._root.config(bg="black")
        self._root.bind("<Escape>", lambda e: self._root.destroy())

        self._canvas = tk.Canvas(self._root, bg="black", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._tick()

    def add_box(self, box, generation: int, label: str = ""):
        """box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] in screen coordinates.
        generation: the current OCR pass number, so we know when this
        box was last actually re-confirmed as still present."""
        with self._lock:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            box_id = f"{x1}_{y1}_{x2}_{y2}"
            self._boxes[box_id] = ((x1, y1, x2, y2), generation)

    def prune_stale(self, current_generation: int, grace: int = 1):
        """Call this once after each OCR pass finishes. Removes any box
        that was NOT re-detected in this pass or the previous one
        (grace=1 tolerates a single missed/flaky detection so the box
        doesn't flicker off from one bad OCR read)."""
        with self._lock:
            stale = [
                k for k, (_, last_gen) in self._boxes.items()
                if current_generation - last_gen > grace
            ]
            for k in stale:
                del self._boxes[k]

    def _tick(self):
        with self._lock:
            self._canvas.delete("all")
            for (x1, y1, x2, y2), _ in self._boxes.values():
                self._canvas.create_rectangle(
                    x1, y1, x2, y2, fill="#1a1a1a", outline="#ff3333", width=2
                )
        self._root.after(150, self._tick)

    def run_blocking(self):
        self._root.mainloop()
