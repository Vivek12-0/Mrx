import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def split_title(text, max_chars=28):
    words = text.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1) + len(w) <= max_chars:
            line1 += w + " "
        else:
            line2 += w + " "
    return line1.strip(), line2.strip()


async def get_thumb(videoid, user_id):
    try:
        final = f"cache/{videoid}_{user_id}.png"
        raw = f"cache/raw_{videoid}.jpg"

        if os.path.exists(final):
            return final

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        r = (await search.next())["result"][0]

        title = re.sub(r"\s+", " ", r.get("title", "Unknown Title"))
        channel = r.get("channel", {}).get("name", "Unknown Channel")
        duration = r.get("duration", "0:00")

        t1, t2 = split_title(title)

        thumb_url = r["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw, "wb") as f:
                    await f.write(await resp.read())

        yt = Image.open(raw).convert("RGBA")

        # 🌑 BACKGROUND
        bg = yt.resize((1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(26))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)

        # 🧊 PLAYER BOX
        box_x, box_y = 200, 120
        box_w, box_h = 880, 500

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius=36,
            fill=(15, 15, 15, 235)
        )

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # 🎵 COVER
        cover = yt.resize((240, 240))
        bg.paste(cover, (box_x + 40, box_y + 40))

        # 🔤 FONTS
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 32)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
            icon_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 60)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()

        text_x = box_x + 320

        # 📝 TITLE (2 LINES – INSIDE BOX)
        draw.text((text_x, box_y + 55), t1, fill="white", font=title_font)
        draw.text((text_x, box_y + 95), t2, fill="white", font=title_font)

        # 👤 CHANNEL (MORE DOWN)
        draw.text(
            (text_x, box_y + 145),
            channel,
            fill=(180, 180, 180),
            font=small_font
        )

        # 🎶 MUSIC ICON (EMPTY SPACE FILL)
        draw.text(
            (box_x + box_w - 110, box_y + 140),
            "🎵",
            fill=(90, 90, 90),
            font=icon_font
        )

        # ⏳ PROGRESS BAR (LOWER)
        bar_y = box_y + 215
        draw.line(
            (text_x, bar_y, box_x + box_w - 60, bar_y),
            fill=(120, 120, 120),
            width=6
        )
        draw.line(
            (text_x, bar_y, text_x + 220, bar_y),
            fill="white",
            width=6
        )
        draw.ellipse(
            (text_x + 210, bar_y - 8, text_x + 230, bar_y + 12),
            fill="white"
        )

        # ⏱ TIME
        draw.text((text_x, bar_y + 18), "0:00", fill="white", font=small_font)
        draw.text(
            (box_x + box_w - 110, bar_y + 18),
            duration,
            fill="white",
            font=small_font
        )

        # ⏯ BUTTONS (MORE DOWN)
        btn_y = box_y + 290

        # Prev
        draw.polygon(
            [(text_x+40, btn_y+15), (text_x+70, btn_y), (text_x+70, btn_y+30)],
            fill="white"
        )
        draw.polygon(
            [(text_x+20, btn_y+15), (text_x+40, btn_y), (text_x+40, btn_y+30)],
            fill="white"
        )

        # Pause
        draw.rectangle((text_x+100, btn_y, text_x+110, btn_y+30), fill="white")
        draw.rectangle((text_x+120, btn_y, text_x+130, btn_y+30), fill="white")

        # Next
        draw.polygon(
            [(text_x+170, btn_y), (text_x+170, btn_y+30), (text_x+200, btn_y+15)],
            fill="white"
        )
        draw.polygon(
            [(text_x+200, btn_y), (text_x+200, btn_y+30), (text_x+230, btn_y+15)],
            fill="white"
        )

        # 🤖 BOT NAME (TOP RIGHT INSIDE BOX)
        draw.text(
            (box_x + box_w - 190, box_y + 25),
            unidecode(app.name),
            fill=(150, 150, 150),
            font=small_font
        )

        bg.convert("RGB").save(final)
        os.remove(raw)

        return final

    except Exception:
        return YOUTUBE_IMG_URL