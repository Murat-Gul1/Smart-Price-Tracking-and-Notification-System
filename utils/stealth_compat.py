"""
playwright-stealth uyumluluk yardimcilari.

Python 3.14 ile bazi ortamlarda `pkg_resources` modulu bulunmadigi icin
`playwright-stealth` paketinin kendi import'u patlayabiliyor. Bu modul,
paketin JS stealth script'lerini dogrudan site-packages altindan okuyup
Playwright page objesine uygular.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_ORDER = [
    "utils.js",
    "generate.magic.arrays.js",
    "chrome.app.js",
    "chrome.csi.js",
    "chrome.hairline.js",
    "chrome.load.times.js",
    "chrome.runtime.js",
    "iframe.contentWindow.js",
    "media.codecs.js",
    "navigator.languages.js",
    "navigator.permissions.js",
    "navigator.platform.js",
    "navigator.plugins.js",
    "navigator.vendor.js",
    "window.outerdimensions.js",
    "webgl.vendor.js",
]


def _find_js_dir() -> Path:
    for base in [Path(p) for p in sys.path if p]:
        candidate = base / "playwright_stealth" / "js"
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "playwright_stealth JS dosyalari bulunamadi. "
        "Bagimliliklarin .venv icine kuruldugundan emin olun."
    )


def _build_opts_script() -> str:
    opts = {
        "webgl_vendor": "Intel Inc.",
        "webgl_renderer": "Intel Iris OpenGL Engine",
        "navigator_vendor": "Google Inc.",
        "navigator_platform": None,
        "navigator_user_agent": None,
        "languages": ["en-US", "en"],
        "runOnInsecureOrigins": None,
    }
    return f"const opts = {json.dumps(opts)}"


def _load_scripts() -> list[str]:
    js_dir = _find_js_dir()
    scripts = [_build_opts_script()]

    for filename in SCRIPT_ORDER:
        scripts.append((js_dir / filename).read_text(encoding="utf-8"))

    # Paket icindeki webdriver script'i dosya degil, inline bir ifade.
    scripts.append("delete Object.getPrototypeOf(navigator).webdriver")
    return scripts


async def apply_stealth(page) -> None:
    """Verilen Playwright page objesine stealth script'lerini uygular."""
    for script in _load_scripts():
        await page.add_init_script(script)
