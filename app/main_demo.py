"""SnapShield AI — full pipeline: capture, detection, overlay, auto-arm,
and system tray control.

Blur boxes persist for exactly as long as the secret keeps being
re-detected — 10 seconds, 20 minutes, doesn't matter — and clear out
within about one OCR pass after you switch away. There is no fixed
timer anywhere in this logic.

Run: python -m app.main_demo
"""

import datetime
import threading
import time
from capture.triggers import CaptureLoop
from inference.session import OCRSession
from detection.scoring import score_text_region, should_blur
from overlay.overlay_window import ProtectionOverlay
from app.share_detector import detect_active_share_app
from app.tray import start_tray_icon, is_paused

ocr = OCRSession()
overlay = ProtectionOverlay()

LOG_FILE = "snapshield_log.txt"
DEBUG_LOG_FILE = "snapshield_raw_ocr.txt"
_seen_recent = {}
DEDUPE_SECONDS = 15
DEBUG = True

_frame_generation = 0  # increments once per OCR pass


def mask(value: str) -> str:
    if len(value) <= 6:
        return "*" * len(value)
    return value[:3] + "*" * (len(value) - 6) + value[-3:]


def log(msg: str):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def debug_log(msg: str):
    if DEBUG:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def handle_frame(frame):
    global _frame_generation

    if is_paused():
        return

    _frame_generation += 1
    this_gen = _frame_generation

    results = ocr.read(frame)
    now = datetime.datetime.now()
    ts = now.strftime("%H:%M:%S")

    for bbox, text, conf in results:
        if not text.strip():
            continue
        debug_log(f"[{ts}] ocr_conf={conf:.2f} text='{text}'")

        findings = score_text_region(text, bbox)
        if should_blur(findings):
            for f in findings:
                key = (f["label"], f["value"])
                last_seen = _seen_recent.get(key)
                if last_seen and (now - last_seen).total_seconds() < DEDUPE_SECONDS:
                    overlay.add_box(bbox, this_gen, f["label"])
                    continue
                _seen_recent[key] = now
                log(f"🔴 [{ts}] SENSITIVE: [{f['label']}] confidence={f['confidence']:.2f} "
                    f"masked='{mask(f['value'])}'")
                overlay.add_box(bbox, this_gen, f["label"])

    # Remove any box that wasn't re-confirmed in this pass (or the one
    # before it) — this is what makes boxes clear quickly on app switch
    # while staying rock-solid for as long as the secret is still there.
    overlay.prune_stale(this_gen, grace=1)


def run_capture_thread():
    loop = CaptureLoop(baseline_fps=4.0, change_threshold=0.02)
    loop.run(on_frame=handle_frame)


def check_share_status():
    last_state = False
    while True:
        active_app = detect_active_share_app()
        is_sharing = active_app is not None
        if is_sharing != last_state:
            if is_sharing:
                log(f"🛡️ Presentation Mode auto-activated — detected {active_app} running")
            else:
                log("🛡️ Presentation Mode deactivated — no screen-share app detected")
            last_state = is_sharing
        time.sleep(3)


def main():
    open(LOG_FILE, "w").close()
    open(DEBUG_LOG_FILE, "w").close()

    t1 = threading.Thread(target=run_capture_thread, daemon=True)
    t2 = threading.Thread(target=check_share_status, daemon=True)
    t3 = threading.Thread(target=start_tray_icon, daemon=True)
    t1.start()
    t2.start()
    t3.start()

    overlay.start()
    overlay.run_blocking()


if __name__ == "__main__":
    main()