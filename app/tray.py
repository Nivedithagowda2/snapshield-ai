"""System tray icon for SnapShield AI. Replaces the raw terminal as the
user-facing surface — right-click for Pause/Resume Protection and Exit."""

import threading
from PIL import Image, ImageDraw
import pystray

_paused = threading.Event()


def is_paused() -> bool:
    return _paused.is_set()


def _make_icon_image(color="#00c853"):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(
        [(32, 4), (58, 16), (58, 34), (32, 60), (6, 34), (6, 16)],
        fill=color,
    )
    return img


def _on_toggle_pause(icon, item):
    if _paused.is_set():
        _paused.clear()
        icon.icon = _make_icon_image("#00c853")
    else:
        _paused.set()
        icon.icon = _make_icon_image("#888888")


def _on_exit(icon, item):
    icon.stop()
    import os
    os._exit(0)


def _pause_label(item):
    return "Resume Protection" if _paused.is_set() else "Pause Protection"


def start_tray_icon():
    print(">>> [tray] starting tray icon thread...")
    try:
        menu = pystray.Menu(
            pystray.MenuItem(_pause_label, _on_toggle_pause),
            pystray.MenuItem("Exit SnapShield", _on_exit),
        )
        icon = pystray.Icon("SnapShield AI", _make_icon_image(), "SnapShield AI — Protecting your screen", menu)
        print(">>> [tray] icon created, calling icon.run()...")
        icon.run()
        print(">>> [tray] icon.run() returned (icon closed)")
    except Exception as e:
        print(f">>> [tray] FAILED TO START: {e!r}")
        import traceback
        traceback.print_exc()
