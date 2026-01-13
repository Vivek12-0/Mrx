import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def resize(img, w, h):
    img.thumbnail((w, h))
    return img


async def get_thumb(videoid, user_id):
    try:
        path = f"cache/{videoid}_{user_id}.png"
        if os.path.exists(path):
            return path

        search = VideosSearch(f"https://youtube.com/watch?v={videoid}", limit=1)
        data = (await search.next())["result"][0]

        title = " ".join(data["title"].split()[:5])
        duration = data.get("duration", "00:00")
        channel = data.get("channel", {}).get("name", "")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                async with aiofiles.open("cache/temp.png", "wb") as f:
                    await f.write(await r.read())

        img = Image.open("cache/temp.png").convert("RGBA")

        bg = resize(img.copy(), 1280, 720)
        bg = bg.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # Player box
        draw.rounded_rectangle(
            (180, 160, 1100, 520),
            radius=40,
            fill=(30, 30, 30, 220)
        )

        # Song thumb
        thumb = resize(img.copy(), 220, 220)
        mask = Image.new("L", thumb.size, 255)
        bg.paste(thumb, (220, 210), mask)

        # Fonts
        title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 36)
        small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)

        # Text
        draw.text((500, 215), "Now Playing", fill="gray", font=small_font)
        draw.text((500, 255), title, fill="white", font=title_font)
        draw.text((500, 300), channel, fill="lightgray", font=small_font)

        # Progress bar
        draw.rectangle((500, 350, 980, 360), fill=(100, 100, 100))
        draw.rectangle((500, 350, 720, 360), fill="white")

        draw.text((500, 370), "0:00", fill="white", font=small_font)
        draw.text((940, 370), duration, fill="white", font=small_font)

        # Buttons (simple & safe)
        y = 440
        draw.text((620, y), "⏮", fill="white", font=title_font)
        draw.text((700, y), "▶", fill="white", font=title_font)
        draw.text((780, y), "⏭", fill="white", font=title_font)

        # Bot name
        draw.text((1050, 25), unidecode(app.nameName if hasattr(app, "name") else app.username),
                  fill="white", font=small_font)

        bg.save(path)
        os.remove("cache/temp.png")
        return path

    except Exception:
        return YOUTUBE_IMG_URL