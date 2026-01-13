import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def wrap_text(draw, text, font, max_width):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


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
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.33)

        # 🧊 PLAYER BOX
        box_x, box_y = 160, 120
        box_w, box_h = 960, 500

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius=38,
            fill=(15, 15, 15, 235)
        )

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # 🎵 COVER
        cover = yt.resize((230, 230))
        bg.paste(cover, (box_x + 40, box_y + 40))

        # 🔤 FONTS
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 32)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        text_x = box_x + 310
        max_text_width = box_x + box_w - text_x - 40

        # 📝 TITLE (AUTO MULTI-LINE, NEVER OUTSIDE)
        lines = wrap_text(draw, title, title_font, max_text_width)
        y = box_y + 50
        for line in lines[:4]:   # max 4 lines (Apple style)
            draw.text((text_x, y), line, fill="white", font=title_font)
            y += 36

        # 👤 CHANNEL
        draw.text(
            (text_x, y + 5),
            channel,
            fill=(180, 180, 180),
            font=small_font
        )

        # ⏳ PROGRESS BAR
        bar_y = box_y + 235
        draw.line((text_x, bar_y, box_x + box_w - 60, bar_y), fill=(120,120,120), width=6)
        draw.line((text_x, bar_y, text_x + 260, bar_y), fill="white", width=6)
        draw.ellipse((text_x + 250, bar_y - 9, text_x + 270, bar_y + 13), fill="white")

        # ⏱ TIME
        draw.text((text_x, bar_y + 18), "0:00", fill="white", font=small_font)
        draw.text((box_x + box_w - 120, bar_y + 18), duration, fill="white", font=small_font)

        # 🎛 CONTROLS (SECOND IMAGE STYLE)
        cy = box_y + 315
        cx = box_x + box_w // 2

        # Shuffle
        draw.arc((cx-260,cy-10,cx-220,cy+30),0,270,fill="white",width=3)

        # Prev
        draw.polygon([(cx-140,cy),(cx-110,cy+15),(cx-140,cy+30)], fill="white")
        draw.rectangle((cx-150,cy,cx-145,cy+30), fill="white")

        # Play (BIG)
        draw.ellipse((cx-25,cy-10,cx+25,cy+40), outline="white", width=4)
        draw.polygon([(cx-8,cy),(cx+12,cy+15),(cx-8,cy+30)], fill="white")

        # Next
        draw.polygon([(cx+110,cy),(cx+110,cy+30),(cx+140,cy+15)], fill="white")
        draw.rectangle((cx+145,cy,cx+150,cy+30), fill="white")

        # Repeat
        draw.arc((cx+220,cy-10,cx+260,cy+30),180,450,fill="white",width=3)

        # 🤖 BOT NAME
        draw.text(
            (box_x + box_w - 200, box_y + 22),
            unidecode(app.name),
            fill=(150,150,150),
            font=small_font
        )

        bg.convert("RGB").save(final)
        os.remove(raw)
        return final

    except Exception:
        return YOUTUBE_IMG_URL