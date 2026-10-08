"""Headless Edge/Chrome screenshot of a saved page, for the smoke script."""

import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

BROWSER_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]
TIMEOUT = 120  # seconds to wait for the PNG


def find_browser(env: Mapping[str, str], candidates: list[Path]) -> str | None:
    """BROWSER_PATH if that file exists, else the first installed Chromium-family browser."""
    paths = [Path(env["BROWSER_PATH"])] if env.get("BROWSER_PATH") else []
    return next((str(p) for p in paths + candidates if p.is_file()), None)


def take_screenshot(
    html_path: Path,
    browser: str | None,
    launch: Callable[..., Any] = subprocess.Popen,
    settle: float = 1.0,
) -> str:
    """Renders html_path with a headless browser into a PNG beside it.

    Waits for the PNG rather than for the browser: on pages whose network
    requests hang (web fonts), Edge writes the PNG and then keeps running."""
    if browser is None:
        return "screenshot: skipped (no browser found; set BROWSER_PATH)"
    png_path = html_path.with_suffix(".png")
    png_path.unlink(missing_ok=True)
    # A throwaway profile keeps the headless run off the user's open browser session.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        try:
            proc = launch(
                [
                    browser,
                    "--headless",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--window-size=1280,1600",
                    f"--user-data-dir={profile}",
                    f"--screenshot={png_path.resolve()}",
                    html_path.resolve().as_uri(),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            return f"screenshot: failed ({exc.strerror or exc})"
        try:
            deadline = time.monotonic() + TIMEOUT
            while not png_written(png_path, settle):
                if proc.poll() is not None or time.monotonic() > deadline:
                    break
                time.sleep(0.5)
        finally:
            if proc.poll() is None:
                proc.terminate()
    if not png_written(png_path, 0):
        return "screenshot: failed (browser produced no PNG)"
    return f"screenshot: {png_path}"


def png_written(path: Path, settle: float) -> bool:
    """True once the file exists and its size holds steady for `settle` seconds."""
    if not path.is_file():
        return False
    size = path.stat().st_size
    time.sleep(settle)
    return size > 0 and path.stat().st_size == size
