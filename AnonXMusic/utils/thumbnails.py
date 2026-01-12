import os
import re

import aiofiles
import aiohttp
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from ytSearch import VideosSearch

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


def clear(text):
    words = text.split(" ")
    title = ""
    for i in words:
        if len(title) + len(i) < 60:
            title += " " + i
    return title.strip()


async def get_thumb(videoid, user_id):
    try:
        if os.path.isfile(f"cache/{videoid}_{user_id}.png"):
            return f"cache/{videoid}_{user_id}.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)

        for result in (await results.next())["result"]:
            title = result.get("title", "Unsupported Title")
            title = re.sub("\W+", " ", title).title()
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download youtube thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{videoid}.png", "wb") as f:
                        await f.write(await resp.read())

        youtube = Image.open(f"cache/thumb{videoid}.png").convert("RGBA")

        # Background (blurred)
        base = changeImageSize(1280, 720, youtube)
        background = base.filter(ImageFilter.BoxBlur(12))
        background = ImageEnhance.Brightness(background).enhance(0.45)

        draw = ImageDraw.Draw(background)

        # 🔲 CENTER RECTANGLE THUMBNAIL
        rect_thumb = changeImageSize(640, 360, youtube)
        rect_x = int((1280 - rect_thumb.size[0]) / 2)
        rect_y = 180
        background.paste(rect_thumb, (rect_x, rect_y))

        # Fonts
        arial = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 30)

        # Bot Name (Top Right)
        draw.text(
            (1110, 10),
            unidecode(app.name),
            fill="white",
            font=arial
        )

        # Channel + Views
        draw.text(
            (55, 560),
            f"{channel} | {views[:23]}",
            fill="white",
            font=arial
        )

        # Title
        draw.text(
            (55, 600),
            clear(title),
            fill="white",
            font=font
        )

        # Progress Line
        draw.line(
            [(55, 660), (1220, 660)],
            fill="white",
            width=5
        )

        # Progress Dot
        draw.ellipse(
            [(918, 648), (942, 672)],
            fill="white"
        )

        # Time
        draw.text((36, 685), "00:00", fill="white", font=arial)
        draw.text((1185, 685), duration[:23], fill="white", font=arial)

        # Save
        background.save(f"cache/{videoid}_{user_id}.png")

        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass

        return f"cache/{videoid}_{user_id}.png"

    except Exception:
        return YOUTUBE_IMG_URL