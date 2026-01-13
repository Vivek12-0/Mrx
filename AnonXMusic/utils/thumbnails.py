import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


CACHE_DIR = "cache"
FONT_BOLD = "AnonXMusic/assets/font.ttf"
FONT_REG = "AnonXMusic/assets/font2.ttf"


def resize_keep_ratio(img, max_w, max_h):
    ratio = min(max_w / img.width, max_h / img.height)
    return img.resize((int(img.width * ratio), int(img.height * ratio)))


def safe_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def trim_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    while draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid, user_id):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        final_path = f"{CACHE_DIR}/{videoid}_{user_id}.png"

        if os.path.exists(final_path):
            return final_path

        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        result = (await search.next())["result"][0]

        title = result.get("title", "Unknown Song")
        channel = result.get("channel", {}).get("name", "YouTube")
        duration = result.get("duration", "00:00")
        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        temp_path = f"{CACHE_DIR}/temp.png"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(await resp.read())

        cover = Image.open(temp_path).convert("RGBA")

        base = resize_keep_ratio(cover, 1280, 720)
        bg = base.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)

        draw = ImageDraw.Draw(bg)

        # Player Card
        card = (200, 150, 1080, 560)
        draw.rounded_rectangle(card, radius=45, fill=(25, 25, 25, 230))

        # Album art
        art = resize_keep_ratio(cover, 230, 230)
        mask = Image.new("L", art.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, art.width, art.height), radius=30, fill=255
        )
        bg.paste(art, (250, 220), mask)

        # Fonts
        font_title = safe_font(FONT_BOLD, 34)
        font_small = safe_font(FONT_REG, 26)

        title = trim_text(draw, title, font_title, 430)

        draw.text((520, 240), "Now Playing", fill="#AAAAAA", font=font_small)
        draw.text((520, 280), title, fill="white", font=font_title)
        draw.text((520, 325), channel, fill="#CCCCCC", font=font_small)

        # Progress bar
        draw.rounded_rectangle((520, 380, 950, 395), 10, fill=(90, 90, 90))
        draw.rounded_rectangle((520, 380, 720, 395), 10, fill=(255, 255, 255))

        draw.text((520, 405), "0:00", fill="white", font=font_small)
        draw.text((905, 405), duration, fill="white", font=font_small)

        # Controls
        y = 465
        draw.polygon([(660, y), (690, y - 18), (690, y + 18)], fill="white")
        draw.polygon([(690, y), (720, y - 18), (720, y + 18)], fill="white")

        draw.polygon([(760, y - 22), (760, y + 22), (805, y)], fill="white")

        draw.polygon([(850, y), (820, y - 18), (820, y + 18)], fill="white")
        draw.polygon([(880, y), (850, y - 18), (850, y + 18)], fill="white")

        draw.text(
            (30, 20),
            unidecode(app.name),
            fill="white",
            font=font_small,
        )

        bg.save(final_path)
        os.remove(temp_path)

        return final_path

    except Exception:
        return YOUTUBE_IMG_URL