import os
import re

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    ratio = min(widthRatio, heightRatio)
    return image.resize(
        (int(image.size[0] * ratio), int(image.size[1] * ratio))
    )


def clear(text):
    out = ""
    for word in text.split():
        if len(out) + len(word) < 60:
            out += " " + word
    return out.strip()


def rounded_rectangle(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


async def get_thumb(videoid, user_id):
    try:
        path = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(path):
            return path

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        result = (await search.next())["result"][0]

        title = clear(result.get("title", "Unknown Title"))
        duration = result.get("duration", "00:00")
        views = result.get("viewCount", {}).get("short", "")
        channel = result.get("channel", {}).get("name", "")

        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open("cache/temp.png", "wb") as f:
                    await f.write(await r.read())

        yt = Image.open("cache/temp.png").convert("RGBA")

        base = changeImageSize(1280, 720, yt)
        bg = base.filter(ImageFilter.GaussianBlur(15))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # 🎵 PLAYER BAR (ROUNDED)
        bar_x1, bar_y1 = 240, 170
        bar_x2, bar_y2 = 1040, 520
        rounded_rectangle(
            draw,
            (bar_x1, bar_y1, bar_x2, bar_y2),
            radius=40,
            fill=(20, 20, 20, 200),
        )

        # 🎶 Song thumbnail (rounded square)
        song_thumb = changeImageSize(200, 200, yt)
        mask = Image.new("L", song_thumb.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, song_thumb.size[0], song_thumb.size[1]),
            radius=25,
            fill=255,
        )
        bg.paste(song_thumb, (280, 210), mask)

        # Fonts
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 32)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 26)

        # Text
        draw.text((520, 235), title, fill="white", font=font_title)
        draw.text((520, 275), channel, fill="lightgray", font=font_small)

        # ⏳ Progress bar
        draw.rounded_rectangle(
            (520, 330, 980, 345),
            radius=10,
            fill=(120, 120, 120),
        )
        draw.rounded_rectangle(
            (520, 330, 720, 345),
            radius=10,
            fill=(255, 255, 255),
        )

        draw.text((520, 355), "00:00", fill="white", font=font_small)
        draw.text((940, 355), duration, fill="white", font=font_small)

        # ⏯ BUTTONS
        center_y = 420

        # Previous
        draw.polygon(
            [(600, center_y), (620, center_y - 15), (620, center_y + 15)],
            fill="white",
        )
        draw.polygon(
            [(620, center_y), (640, center_y - 15), (640, center_y + 15)],
            fill="white",
        )

        # Play
        draw.polygon(
            [(700, center_y - 18), (700, center_y + 18), (735, center_y)],
            fill="white",
        )

        # Next
        draw.polygon(
            [(800, center_y), (780, center_y - 15), (780, center_y + 15)],
            fill="white",
        )
        draw.polygon(
            [(820, center_y), (800, center_y - 15), (800, center_y + 15)],
            fill="white",
        )

        # Bot name
        draw.text(
            (1050, 20),
            unidecode(app.name),
            fill="white",
            font=font_small,
        )

        bg.save(path)
        os.remove("cache/temp.png")
        return path

    except Exception:
        return YOUTUBE_IMG_URL