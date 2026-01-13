import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


CACHE = "cache"
FONT_BOLD = "AnonXMusic/assets/font.ttf"
FONT_REG = "AnonXMusic/assets/font2.ttf"


def ratio_resize(img, mw, mh):
    r = min(mw / img.width, mh / img.height)
    return img.resize((int(img.width * r), int(img.height * r)))


def font_safe(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def cut_text(draw, text, font, width):
    if draw.textlength(text, font=font) <= width:
        return text
    while draw.textlength(text + "...", font=font) > width:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid, user_id):
    try:
        os.makedirs(CACHE, exist_ok=True)
        out = f"{CACHE}/{videoid}_{user_id}.png"

        if os.path.exists(out):
            return out

        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        data = (await search.next())["result"][0]

        title = data.get("title", "Unknown Song")
        channel = data.get("channel", {}).get("name", "Music")
        duration = data.get("duration", "00:00")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        temp = f"{CACHE}/temp.png"
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

        cover = Image.open(temp).convert("RGBA")

        # ===== BACKGROUND =====
        base = ratio_resize(cover, 1280, 720)
        bg = base.filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.68)  # 🔥 light dark (75%)

        draw = ImageDraw.Draw(bg)

        # ===== GLASS CARD (NO BLACK BAR) =====
        card_box = (180, 160, 1100, 560)
        draw.rounded_rectangle(
            card_box,
            radius=45,
            fill=(30, 30, 30, 180)  # glass effect
        )

        # ===== ALBUM ART =====
        art = ratio_resize(cover, 210, 210)
        mask = Image.new("L", art.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, art.width, art.height), 28, fill=255
        )
        bg.paste(art, (230, 230), mask)

        # ===== FONTS =====
        title_font = font_safe(FONT_BOLD, 34)
        small_font = font_safe(FONT_REG, 26)

        title = cut_text(draw, title, title_font, 460)

        # ===== TEXT =====
        draw.text((480, 240), title, fill="white", font=title_font)
        draw.text((480, 285), channel, fill="#D5D5D5", font=small_font)

        # ===== PROGRESS BAR =====
        draw.rounded_rectangle((480, 345, 980, 360), 8, fill=(140, 140, 140))
        draw.rounded_rectangle((480, 345, 700, 360), 8, fill=(255, 255, 255))

        draw.text((480, 370), "0:00", fill="white", font=small_font)
        draw.text((940, 370), duration, fill="white", font=small_font)

        # ===== PLAYER ICONS (CLEAN & MINIMAL) =====
        y = 440

        # Previous
        draw.polygon([(610, y), (635, y - 16), (635, y + 16)], fill="white")
        draw.polygon([(635, y), (660, y - 16), (660, y + 16)], fill="white")

        # Play
        draw.polygon([(720, y - 20), (720, y + 20), (760, y)], fill="white")

        # Next
        draw.polygon([(820, y), (795, y - 16), (795, y + 16)], fill="white")
        draw.polygon([(845, y), (820, y - 16), (820, y + 16)], fill="white")

        # ===== BOT NAME (SMALL & CLEAN) =====
        draw.text(
            (40, 30),
            unidecode(app.name),
            fill="white",
            font=small_font,
        )

        bg.save(out)
        os.remove(temp)
        return out

    except Exception:
        return YOUTUBE_IMG_URL