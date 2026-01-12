import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


# ---------- helpers ----------

def changeImageSize(maxWidth, maxHeight, image):
    ratio = min(maxWidth / image.size[0], maxHeight / image.size[1])
    return image.resize((int(image.size[0] * ratio), int(image.size[1] * ratio)))


def clear(text):
    out = ""
    for w in text.split():
        if len(out) + len(w) < 80:
            out += " " + w
    return out.strip()


def fit_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    while draw.textlength(text + "...", font=font) > max_width and len(text) > 0:
        text = text[:-1]
    return text + "..."


# ---------- main ----------

async def get_thumb(videoid, user_id):
    try:
        path = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(path):
            return path

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        result = (await search.next())["result"][0]

        title = clear(result.get("title", "Unknown Title"))
        title = " ".join(title.split()[:4])   # ✅ sirf 3–4 words
        duration = result.get("duration", "00:00")
        channel = result.get("channel", {}).get("name", "YouTube")

        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open("cache/temp.png", "wb") as f:
                    await f.write(await r.read())

        yt = Image.open("cache/temp.png").convert("RGBA")

        base = changeImageSize(1280, 720, yt)
        bg = base.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # ---------- PLAYER BAR ----------
        bar = (200, 160, 1080, 520)
        draw.rounded_rectangle(bar, radius=40, fill=(40, 40, 40, 210))

        # ---------- SONG THUMB ----------
        song = changeImageSize(220, 220, yt)
        mask = Image.new("L", song.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, song.size[0], song.size[1]), radius=30, fill=255
        )
        bg.paste(song, (240, 220), mask)

        # ---------- FONTS ----------
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 32)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 26)

        # ---------- TEXT ----------
        safe_title = fit_text(draw, title, font_title, 420)

        draw.text((520, 235), safe_title, fill="white", font=font_title)
        draw.text((520, 275), channel, fill="lightgray", font=font_small)

        # ---------- PROGRESS BAR ----------
        draw.rounded_rectangle((520, 330, 980, 346), radius=10, fill=(120, 120, 120))
        draw.rounded_rectangle((520, 330, 740, 346), radius=10, fill=(255, 255, 255))

        draw.text((520, 355), "00:00", fill="white", font=font_small)
        draw.text((940, 355), duration, fill="white", font=font_small)

        # ---------- BUTTONS ----------
        cy = 420

        # Prev
        draw.polygon([(620, cy), (640, cy - 15), (640, cy + 15)], fill="white")
        draw.polygon([(640, cy), (660, cy - 15), (660, cy + 15)], fill="white")

        # Play
        draw.polygon([(720, cy - 18), (720, cy + 18), (760, cy)], fill="white")

        # Next
        draw.polygon([(840, cy), (820, cy - 15), (820, cy + 15)], fill="white")
        draw.polygon([(860, cy), (840, cy - 15), (840, cy + 15)], fill="white")

        # ---------- BOT NAME ----------
        draw.text((1040, 20), unidecode(app.name), fill="white", font=font_small)

        bg.save(path)
        os.remove("cache/temp.png")
        return path

    except Exception:
        return YOUTUBE_IMG_URL