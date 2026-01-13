import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def fit(img, size):
    img.thumbnail(size)
    return img


def clean(text, max_len=45):
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


async def get_thumb(videoid, user_id):
    try:
        final = f"cache/{videoid}_{user_id}.png"
        raw = f"cache/raw_{videoid}.png"

        if os.path.isfile(final):
            return final

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = (await search.next())["result"][0]

        title = clean(data.get("title", "Unknown Song"))
        channel = data.get("channel", {}).get("name", "Unknown Channel")
        duration = data.get("duration", "0:00")

        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                if r.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw, "wb") as f:
                    await f.write(await r.read())

        yt = Image.open(raw).convert("RGBA")

        # 🎨 BACKGROUND
        bg = yt.resize((1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(22))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)

        draw = ImageDraw.Draw(bg)

        # 🧊 PLAYER RECTANGLE
        box_x, box_y = 240, 120
        box_w, box_h = 800, 480
        radius = 30

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)

        odraw.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius,
            fill=(20, 20, 20, 220)
        )

        bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

        # 🎵 SONG IMAGE (INSIDE BOX)
        cover = fit(yt.copy(), (260, 260))
        bg.paste(cover, (box_x + 40, box_y + 40))

        # 🔤 FONTS (SAFE)
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 32)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # 📝 TEXT (ALL INSIDE BOX)
        tx = box_x + 330
        draw.text((tx, box_y + 60), title, fill="white", font=title_font)
        draw.text((tx, box_y + 105), channel, fill=(180, 180, 180), font=small_font)

        # ⏳ PROGRESS BAR (INSIDE BOX)
        bar_y = box_y + 180
        draw.line((tx, bar_y, box_x + box_w - 60, bar_y), fill=(120, 120, 120), width=6)
        draw.line((tx, bar_y, tx + 180, bar_y), fill="white", width=6)
        draw.ellipse((tx + 170, bar_y - 7, tx + 190, bar_y + 13), fill="white")

        # ⏱ TIME
        draw.text((tx, bar_y + 18), "0:00", fill="white", font=small_font)
        draw.text((box_x + box_w - 100, bar_y + 18), duration, fill="white", font=small_font)

        # ⏯ BUTTONS (STATIC DESIGN)
        by = box_y + 260
        draw.polygon([(tx+40,by),(tx+40,by+30),(tx+15,by+15)], fill="white")   # prev
        draw.rectangle((tx+70,by,tx+78,by+30), fill="white")                  # pause
        draw.rectangle((tx+90,by,tx+98,by+30), fill="white")
        draw.polygon([(tx+135,by),(tx+160,by+15),(tx+135,by+30)], fill="white") # next

        # 🤖 BOT NAME (INSIDE BOX, SMALL)
        draw.text(
            (box_x + box_w - 160, box_y + 20),
            unidecode(app.name),
            fill=(150, 150, 150),
            font=small_font
        )

        bg.convert("RGB").save(final)
        os.remove(raw)

        return final

    except Exception:
        return YOUTUBE_IMG_URL