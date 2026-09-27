"""Detects whether a screen-sharing app is likely active — by process
name for native apps (Zoom, Teams, OBS), and by browser WINDOW TITLE
for browser-based apps (Google Meet), since process name alone can't
distinguish 'Chrome open on Meet' from 'Chrome open on anything else'."""

import psutil
import pygetwindow as gw

CONFIDENT_SHARE_PROCESSES = {
    "zoom.exe": "Zoom",
    "teams.exe": "Microsoft Teams",
    "ms-teams.exe": "Microsoft Teams",
    "obs64.exe": "OBS Studio",
    "obs32.exe": "OBS Studio",
}

BROWSER_TITLE_KEYWORDS = {
    "Google Meet": "Google Meet",
    "Meet -": "Google Meet",
    "Zoom Meeting": "Zoom (web)",
    "Microsoft Teams": "Microsoft Teams (web)",
}


def detect_active_share_app() -> str | None:
    """Returns the name of a likely screen-sharing app if one appears
    active, else None."""
    running = {p.name().lower() for p in psutil.process_iter(["name"])}
    for proc_name, label in CONFIDENT_SHARE_PROCESSES.items():
        if proc_name in running:
            return label

    try:
        for window in gw.getAllTitles():
            for keyword, label in BROWSER_TITLE_KEYWORDS.items():
                if keyword.lower() in window.lower():
                    return label
    except Exception:
        pass

    return None
