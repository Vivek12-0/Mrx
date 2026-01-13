import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def resize_fit(w, h, img):
    img.thumbnail((w, h))
    return img


def clean_title(text, max_len=60):
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


async def get_thumb(videoid, user_id):
    try:
        final_path = f"cache/{videoid}_{user_id}.png"
        raw_thumb = f"cache/raw_{videoid}.png"

        if os.path.isfile(final_path):
            return final_path

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = (await search.next())["result"][0]

        title = clean_title(data.get("title", "Unknown Title"))
        channel = data.get("channel", {}).get("name", "Unknown Channel")
        duration = data.get("duration", "0:00")
        views = data.get("viewCount", {}).get("short", "")

        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw_thumb, "wb") as f:
                    await f.write(await resp.read())

        yt_img = Image.open(raw_thumb).convert("RGBA")

        # 🎨 Background
        bg = yt_img.resize((1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # 🎵 Center Album Card
        card = resize_fit(360, 360, yt_img.copy())
        card_x = 460
        card_y = 150
        bg.paste(card, (card_x, card_y))

        # Fonts (SAFE)
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 36)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 26)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # 🎧 Title
        draw.text((420, 530), title, fill="white", font=title_font)

        # 👤 Channel + Views
        draw.text(
            (420, 575),
            f"{channel} • {views}",
            fill=(200, 200, 200),
            font=small_font
        )

        # ⏳ Progress Bar
        bar_y = 620
        draw.line((300, bar_y, 980, bar_y), fill=(120, 120, 120), width=6)
        draw.line((300, bar_y, 600, bar_y), fill="white", width=6)
        draw.ellipse((590, bar_y - 8, 610, bar_y + 12), fill="white")

        # ⏱ Time
        draw.text((300, 650), "0:00", fill="white", font=small_font)
        draw.text((940, 650), duration, fill="white", font=small_font)

        # 🤖 Bot Name (small clean)
        draw.text(
            (1100, 20),
            unidecode(app.name),
            fill=(180, 180, 180),
            font=small_font
        )

        bg.save(final_path)
        os.remove(raw_thumb)

        return final_path

    except Exception:
        return YOUTUBE_IMG_URL