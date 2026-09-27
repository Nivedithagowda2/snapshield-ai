"""Capture loop that runs in its own thread, continuously watching the
screen and queueing changed frames. A separate worker thread processes
the queue with OCR, so a slow OCR pass never causes the capture loop to
miss what's currently on screen."""

import threading
import queue
import time
from capture.screen_capture import ScreenCapturer
from capture.diff import FrameDiffer


class CaptureLoop:
    def __init__(self, baseline_fps: float = 3.0, change_threshold: float = 0.02,
                 max_queue_size: int = 1):
        self.capturer = ScreenCapturer()
        self.differ = FrameDiffer(threshold=change_threshold)
        self.interval = 1.0 / baseline_fps
        self.frame_queue = queue.Queue(maxsize=max_queue_size)
        self._stop = threading.Event()

    def _capture_thread(self):
        while not self._stop.is_set():
            start = time.time()
            frame = self.capturer.capture()
            if self.differ.has_changed(frame):
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.frame_queue.put_nowait(frame)
            elapsed = time.time() - start
            time.sleep(max(0.0, self.interval - elapsed))

    def _worker_thread(self, on_frame):
        while not self._stop.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            on_frame(frame)

    def run(self, on_frame):
        print(f"Capture loop starting — baseline {1/self.interval:.1f} fps, "
              f"change threshold {self.differ.threshold*100:.0f}% "
              f"(async — capture and OCR run independently)")
        capture_t = threading.Thread(target=self._capture_thread, daemon=True)
        worker_t = threading.Thread(target=self._worker_thread, args=(on_frame,), daemon=True)
        capture_t.start()
        worker_t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCapture loop stopped.")
            self._stop.set()
        finally:
            self.capturer.close()
