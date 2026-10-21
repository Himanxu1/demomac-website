#!/usr/bin/env python3
"""Draws the 1200×630 cover for every blog post into media/blog/<slug>.jpg.

Each post's JSON header names its cover: a short title (words between *stars*
come out orange) and one of the real ScreenToast frames in media/poster-*.jpg.
The same image is the figure at the top of the post, its card on /blog, and
its og:image — one picture per post, all in the site's palette.

    python3 pages/covers.py

Needs Pillow. Fonts are in pages/fonts (SIL Open Font Licence).
"""
import json
import pathlib
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "pages" / "fonts"
OUT = ROOT / "media" / "blog"
W, H = 1200, 630
INK, INK2, LINE = (8, 8, 10), (18, 18, 22), (38, 38, 46)
REC, BONE, BONE3 = (255, 91, 4), (242, 239, 233), (142, 138, 132)


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_name(weight)
    return f


def wrap(draw, words, f, width):
    """Greedy word wrap; each word is (text, is_orange)."""
    lines, cur = [], []
    for w in words:
        trial = " ".join(t for t, _ in cur + [w])
        if cur and draw.textlength(trial, font=f) > width:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    return lines + ([cur] if cur else [])


def render(slug, category, title, shot):
    img = Image.new("RGB", (W, H), INK)

    # A soft orange glow behind the frame, the only colour on the card.
    glow = Image.new("RGB", (W, H), INK)
    ImageDraw.Draw(glow).ellipse((760, 330, 1340, 860), fill=(110, 38, 4))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(120)), 0.75)

    # The real app frame, bleeding off the right edge.
    frame = Image.open(ROOT / "media" / shot).convert("RGB")
    fh = 440
    fw = round(frame.width * fh / frame.height)
    frame = frame.resize((fw, fh), Image.LANCZOS)
    x, y = 668, 112
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x + 10, y + 24, x + fw, y + fh + 24), 22, fill=170)
    img.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(26)))
    mask = Image.new("L", (fw, fh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw - 1, fh - 1), 18, fill=255)
    img.paste(frame, (x, y), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y, x + fw - 1, y + fh - 1), 18, outline=LINE, width=2)

    # Kicker: the brand dot, the blog, the topic.
    mono = font("IBMPlexMono-SemiBold.ttf", 19)
    d.ellipse((64, 70, 80, 86), fill=REC)
    d.text((94, 66), "SCREENTOAST BLOG", font=mono, fill=BONE)
    kx = 94 + d.textlength("SCREENTOAST BLOG", font=mono) + 18
    tw = d.textlength(category.upper(), font=mono)
    d.rounded_rectangle((kx, 62, kx + tw + 20, 92), 7, outline=(150, 60, 14), width=2)
    d.text((kx + 10, 66), category.upper(), font=mono, fill=REC)

    # Title: biggest size that fits four lines in the left column.
    words = split_stars(title)
    for size in (66, 60, 56, 52, 48, 44):
        f = font("Archivo.ttf", size, "ExtraBold")
        lines = wrap(d, words, f, 560)
        if len(lines) <= 4:
            break
    lh = round(size * 1.08)
    ty = 140 + (4 - len(lines)) * lh // 3
    for line in lines:
        lx = 64
        for i, (t, orange) in enumerate(line):
            piece = t + (" " if i < len(line) - 1 else "")
            d.text((lx, ty), piece, font=f, fill=REC if orange else BONE)
            lx += d.textlength(piece, font=f)
        ty += lh

    d.text((64, 548), "screentoast.com", font=font("IBMPlexSans-Medium.ttf", 22, "Medium"), fill=BONE3)

    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{slug}.jpg", quality=84, optimize=True, progressive=True)


def split_stars(title):
    """'Best *Screen Studio* alternatives' → words, each flagged if starred."""
    out, inside = [], False
    for w in title.split():
        # A closing star may sit before punctuation: "*ScreenToast*:".
        starts, ends = w.startswith("*"), w.rstrip(":;,.?!").endswith("*") and len(w.strip("*:;,.?!")) > 0
        out.append((w.replace("*", ""), inside or starts))
        if starts and not ends:
            inside = True
        elif ends:
            inside = False
    return out


def main():
    for src in sorted((ROOT / "pages").glob("blog-*.html")):
        meta = json.loads(re.match(r"\s*<!--\s*(\{.*?\})\s*-->", src.read_text(), re.S).group(1))
        b = meta["blog"]
        slug = meta["path"].removeprefix("/blog/")
        if b["image"] != f"/media/blog/{slug}.jpg":
            raise SystemExit(f"{src.name}: image should be /media/blog/{slug}.jpg")
        render(slug, b["category"], b["cover"]["title"], b["cover"]["shot"])
        print(f"{src.name:52} → media/blog/{slug}.jpg")


if __name__ == "__main__":
    main()
