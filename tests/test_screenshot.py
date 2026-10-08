"""The smoke script's headless-browser screenshot, with a fake browser launcher."""

from pathlib import Path

from scripts.screenshot import find_browser, take_screenshot

HTML = "<!DOCTYPE html><html><body><section id='hero'></section></body></html>"


class FakeBrowser:
    """Writes the PNG like a headless browser, then keeps running the way Edge
    does on pages whose network requests hang."""

    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        self.terminated = False
        png = next(a for a in cmd if a.startswith("--screenshot="))
        Path(png.removeprefix("--screenshot=")).write_bytes(b"\x89PNG fake")

    def poll(self):
        return 0 if self.terminated else None

    def terminate(self):
        self.terminated = True


def test_screenshot_closes_the_browser_once_the_png_is_written(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(HTML, encoding="utf-8")
    (tmp_path / "page.png").write_bytes(b"stale from an earlier run")
    launched = []

    def launch(cmd, **kwargs):
        launched.append(FakeBrowser(cmd, **kwargs))
        return launched[-1]

    line = take_screenshot(page, "fake-browser", launch=launch, settle=0)

    [browser] = launched
    assert browser.cmd[0] == "fake-browser"
    assert "--headless" in browser.cmd
    assert f"--screenshot={page.with_suffix('.png').resolve()}" in browser.cmd
    assert browser.cmd[-1] == page.resolve().as_uri()
    assert browser.terminated
    assert (tmp_path / "page.png").read_bytes() == b"\x89PNG fake"
    assert line == f"screenshot: {page.with_suffix('.png')}"


def test_screenshot_is_skipped_when_no_browser_is_found(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(HTML, encoding="utf-8")

    def never_launch(cmd, **kw):
        raise AssertionError("no browser should run")

    line = take_screenshot(page, None, launch=never_launch)

    assert line == "screenshot: skipped (no browser found; set BROWSER_PATH)"


def test_screenshot_reports_a_browser_that_fails_to_launch(tmp_path):
    page = tmp_path / "page.html"
    page.write_text(HTML, encoding="utf-8")

    def broken_launch(cmd, **kw):
        raise PermissionError("Access is denied")

    line = take_screenshot(page, "fake-browser", launch=broken_launch)

    assert line == "screenshot: failed (Access is denied)"


def test_find_browser_prefers_browser_path_then_known_installs(tmp_path):
    custom = tmp_path / "chrome.exe"
    custom.write_text("")
    installed = tmp_path / "msedge.exe"
    installed.write_text("")

    assert find_browser({"BROWSER_PATH": str(custom)}, [installed]) == str(custom)
    assert find_browser({}, [tmp_path / "missing.exe", installed]) == str(installed)
    assert find_browser({}, [tmp_path / "missing.exe"]) is None


def test_find_browser_ignores_a_browser_path_that_does_not_exist(tmp_path):
    installed = tmp_path / "msedge.exe"
    installed.write_text("")
    env = {"BROWSER_PATH": str(tmp_path / "typo.exe")}

    assert find_browser(env, [installed]) == str(installed)
    assert find_browser(env, []) is None
