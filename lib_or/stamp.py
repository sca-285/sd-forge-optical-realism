"""Date stamp: the orange LED date a compact camera burns into the frame.

Drawn as slanted seven-segment digits, so no font file is needed and it looks
the same on every machine. Digits, spaces and the separators ' / . - : are
drawn; anything else becomes a space.
"""

import datetime

from PIL import Image, ImageDraw

FORMATS = ["'YY MM DD", "DD/MM/YYYY", "MM/DD/YYYY", "YYYY.MM.DD"]
POSITIONS = ["Bottom right", "Bottom left", "Top right", "Left edge (vertical)"]

# Segments a-g, lit per digit.
_DIGITS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g",
}


def today_text(fmt):
    d = datetime.date.today()
    if fmt == "DD/MM/YYYY":
        return d.strftime("%d/%m/%Y")
    if fmt == "MM/DD/YYYY":
        return d.strftime("%m/%d/%Y")
    if fmt == "YYYY.MM.DD":
        return d.strftime("%Y.%m.%d")
    return d.strftime("'%y %m %d")


def _segments(x, y, w, h, t):
    """Rectangles of the seven segments of a cell at (x, y), size w x h."""
    m = h / 2
    return {
        "a": (x + t, y, x + w - t, y + t),
        "b": (x + w - t, y + t, x + w, y + m),
        "c": (x + w - t, y + m, x + w, y + h - t),
        "d": (x + t, y + h - t, x + w - t, y + h),
        "e": (x, y + m, x + t, y + h - t),
        "f": (x, y + t, x + t, y + m),
        "g": (x + t, y + m - t / 2, x + w - t, y + m + t / 2),
    }


def render_mask(text, height):
    """The stamp as an 'L' mask, upright, `height` pixels tall."""
    h = max(8, int(height))
    w = h * 0.55
    t = max(1.0, h * 0.12)
    gap = h * 0.22
    slant = h * 0.18
    advances = []
    for ch in text:
        if ch in _DIGITS or ch == " ":
            advances.append(w + gap)
        else:
            advances.append(h * 0.35 + gap if ch in "/" else h * 0.2 + gap)
    width = int(sum(advances) + slant + 4)
    img = Image.new("L", (max(width, 1), h + 4), 0)
    draw = ImageDraw.Draw(img)

    def shear(pts):
        # Italic: the top of each cell leans right, as on the real stamps.
        return [(px + slant * (1 - (py - 2) / h), py) for px, py in pts]

    x = 2.0
    for ch, adv in zip(text, advances):
        if ch in _DIGITS:
            segs = _segments(x, 2, w, h, t)
            for s in _DIGITS[ch]:
                x0, y0, x1, y1 = segs[s]
                draw.polygon(shear([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), fill=255)
        elif ch == "/":
            sw = h * 0.35
            draw.polygon(shear([(x + sw - t, 2), (x + sw, 2), (x + t, 2 + h), (x, 2 + h)]), fill=255)
        elif ch in ".:'":
            dots = {".": [h - t], ":": [h * 0.3, h * 0.7 - t], "'": [0]}[ch]
            for dy in dots:
                draw.polygon(shear([(x, 2 + dy), (x + t, 2 + dy), (x + t, 2 + dy + t), (x, 2 + dy + t)]),
                             fill=255)
        x += adv
    return img


def place(mask, size, position):
    """The stamp mask on a frame of `size`, in the corner `position` names."""
    fw, fh = size
    if position == "Left edge (vertical)":
        # Reads top to bottom, as on the side of a photo turned to portrait.
        mask = mask.rotate(-90, expand=True)
    mw, mh = mask.size
    margin = int(round(min(fw, fh) * 0.045))
    if position == "Bottom left":
        xy = (margin, fh - mh - margin)
    elif position == "Top right":
        xy = (fw - mw - margin, margin)
    elif position == "Left edge (vertical)":
        xy = (margin, (fh - mh) // 2)
    else:
        xy = (fw - mw - margin, fh - mh - margin)
    out = Image.new("L", size, 0)
    out.paste(mask, xy)
    return out


def stamp_mask(size, text, fmt, position, scale=1.0):
    """Full-frame 'L' mask of the stamp, or None if there is nothing to draw."""
    text = (text or "").strip() or today_text(fmt)
    if not any(ch in _DIGITS for ch in text):
        return None
    height = min(size) * 0.035 * scale
    return place(render_mask(text, height), size, position)
