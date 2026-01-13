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


def resize_ratio(img, mw, mh):
    r = min(mw / img.width, mh / img.height)
    return img.resize((int(img.width * r), int(img.height * r)))


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def shorten(draw, text, font, width):
    if draw.textlength(text, font=font) <= width:
        return text
    while draw.textlength(text + "...", font=font) > width:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid, user_id):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        out = f"{CACHE_DIR}/{videoid}_{user_id}.png"
        if os.path.exists(out):
            return out

        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        data = (await search.next())["result"][0]

        title = data.get("title", "Unknown Song")
        channel = data.get("channel", {}).get("name", "YouTube")
        duration = data.get("duration", "00:00")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        temp = f"{CACHE_DIR}/temp.png"
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

        cover = Image.open(temp).convert("RGBA")

        base = resize_ratio(cover, 1280, 720)

        # 🔆 LIGHTER BACKGROUND (75% DARK)
        bg = base.filter(ImageFilter.GaussianBlur(16))
        bg = ImageEnhance.Brightness(bg).enhance(0.62)  # 🔥 main change

        draw = ImageDraw.Draw(bg)

        # Player Card (lighter than before)
        draw.rounded_rectangle(
            (200, 150, 1080, 560),
            radius=42,
            fill=(35, 35, 35, 210),
        )

        # Album Art
        art = resize_ratio(cover, 230, 230)
        mask = Image.new("L", art.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, art.width, art.height), 30, fill=255
        )
        bg.paste(art, (250, 220), mask)

        # Fonts
        font_title = load_font(FONT_BOLD, 34)
        font_small = load_font(FONT_REG, 26)

        title = shorten(draw, title, font_title, 440)

        # Text
        draw.text((520, 235), "Now Playing", fill="#E0E0E0", font=font_small)
        draw.text((520, 275), title, fill="white", font=font_title)
        draw.text((520, 320), channel, fill="#D0D0D0", font=font_small)

        # Progress Bar
        draw.rounded_rectangle((520, 375, 950, 392), 10, fill=(120, 120, 120))
        draw.rounded_rectangle((520, 375, 735, 392), 10, fill=(255, 255, 255))

        draw.text((520, 402), "0:00", fill="white", font=font_small)
        draw.text((905, 402), duration, fill="white", font=font_small)

        # Controls
        y = 465
        draw.polygon([(660, y), (690, y - 16), (690, y + 16)], fill="white")
        draw.polygon([(690, y), (720, y - 16), (720, y + 16)], fill="white")

        draw.polygon([(760, y - 20), (760, y + 20), (800, y)], fill="white")

        draw.polygon([(845, y), (815, y - 16), (815, y + 16)], fill="white")
        draw.polygon([(875, y), (845, y - 16), (845, y + 16)], fill="white")

        # Bot Name
        draw.text(
            (30, 20),
            unidecode(app.name),
            fill="white",
            font=font_small,
        )

        bg.save(out)
        os.remove(temp)
        return out

    except Exception:
        return YOUTUBE_IMG_URL