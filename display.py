from __future__ import annotations

from pathlib import Path

from PIL import Image


try:
    from inky.auto import auto
except ImportError:
    auto = None


def detect_resolution(default: tuple[int, int] = (800, 480)) -> tuple[int, int]:
    if auto is None:
        return default
    try:
        display = auto(ask_user=False, verbose=False)
        return tuple(display.resolution)
    except Exception:
        return default


def save_preview(image: Image.Image, path: Path) -> None:
    image.save(path)
    print(f"Simulation gespeichert: {path}")


def show_on_inky(image: Image.Image, skip_display: bool) -> None:
    if skip_display:
        print("Display-Ausgabe durch lokalen Testmodus uebersprungen.")
        return

    if auto is None:
        print("Inky-Library nicht gefunden. Display-Ausgabe wird uebersprungen.")
        return

    try:
        display = auto(ask_user=True, verbose=True)
        resized = image.resize(display.resolution)
        display.set_image(resized)
        display.show()
    except Exception as exc:
        print(f"Fehler beim Anzeigen auf dem Inky Display: {exc}")

