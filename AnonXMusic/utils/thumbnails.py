import os
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def resize_img(w, h, img):
    return img.resize((w, h))


def short_title(text):
    return text[:7]   # sirf 6-7 letter


async def get_thumb(videoid, user_id):

    try:
        file = f"cache/{videoid}_{user_id}.png"

        if os.path.isfile(file):
            return file

        # Youtube info
        url = f"https://www.youtube.com/watch?v={videoid}"
        search = VideosSearch(url, limit=1)

        for r in (await search.next())["result"]:
            title = r.get("title", "Music")
            duration = r.get("duration", "00:00")
            thumb = r["thumbnails"][0]["url"].split("?")[0]
            channel = r.get("channel", {}).get("name", "Unknown")
            views = r.get("viewCount", {}).get("short", "0")

        # download thumb
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb) as resp:
                async with aiofiles.open(f"cache/temp{videoid}.jpg", "wb") as f:
                    await f.write(await resp.read())

        img = Image.open(f"cache/temp{videoid}.jpg").convert("RGBA")

        # Background
        bg = resize_img(1280, 720, img)
        bg = bg.filter(ImageFilter.GaussianBlur(15))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)

        draw = ImageDraw.Draw(bg)

        # Center rectangle
        rect = resize_img(520, 300, img)
        rx = (1280 - 520) // 2
        ry = 140
        bg.paste(rect, (rx, ry))

        # Fonts
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 30)
        small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)

        # Bot name
        draw.text((1030, 20), unidecode(app.name), fill="white", font=small)

        # Title (short)
        draw.text(
            (640, 470),
            short_title(title),
            fill="white",
            font=font,
            anchor="mm"
        )

        # Channel
        draw.text((80, 520), f"{channel} | {views}", fill="white", font=small)

        # Progress bar
        draw.line([(100, 580), (1180, 580)], fill="white", width=4)

        # Dot
        draw.ellipse([(700, 570), (720, 590)], fill="white")

        # Time
        draw.text((80, 610), "00:00", fill="white", font=small)
        draw.text((1130, 610), duration, fill="white", font=small)

        # Save
        bg.save(file)

        os.remove(f"cache/temp{videoid}.jpg")

        return file

    except:
        return YOUTUBE_IMG_URL
