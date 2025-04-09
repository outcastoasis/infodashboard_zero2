import os

ICON_DIR = "icons"  # PNG statt SVG

def get_icon_path(icon_code):
    filename = f"{icon_code}.png"
    path = os.path.join(ICON_DIR, filename)
    if not os.path.exists(path):
        return os.path.join(ICON_DIR, "01d.png")  # Fallback
    return path