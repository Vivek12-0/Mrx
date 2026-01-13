import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def clean(text, limit=40):
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


async def get_thumb(videoid, user_id):
    try:
        final = f"cache/{videoid}_{user_id}.png"
        raw = f"cache/raw_{videoid}.jpg"

        if os.path.exists(final):
            return final

        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        result = (await search.next())["result"][0]

        title = clean(result.get("title", "Unknown Title"))
        channel = result.get("channel", {}).get("name", "Unknown Channel")
        duration = result.get("duration", "0:00")

        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                if r.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw, "wb") as f:
                    await f.write(await r.read())

        # 🎨 BASE IMAGE
        yt = Image.open(raw).convert("RGBA")
        bg = yt.resize((1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)

        # 🧊 PLAYER BOX
        box_x, box_y = 200, 120
        box_w, box_h = 880, 480

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius=35,
            fill=(15, 15, 15, 230)
        )

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # 🎵 COVER IMAGE (INSIDE BOX)
        cover = yt.resize((240, 240))
        bg.paste(cover, (box_x + 40, box_y + 40))

        # 🔤 FONTS (SAFE)
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 34)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        text_x = box_x + 320

        # 📝 TITLE + CHANNEL
        draw.text((text_x, box_y + 60), title, fill="white", font=title_font)
        draw.text((text_x, box_y + 105), channel, fill=(180, 180, 180), font=small_font)

        # ⏳ PROGRESS BAR
        bar_y = box_y + 180
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
        draw.text((box_x + box_w - 110, bar_y + 18), duration, fill="white", font=small_font)

        # ⏯ BUTTONS (APPLE STYLE)
        btn_y = box_y + 260

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

        # 🤖 BOT NAME (INSIDE BOX)
        draw.text(
            (box_x + box_w - 180, box_y + 25),
            unidecode(app.name),
            fill=(150, 150, 150),
            font=small_font
        )

        bg.convert("RGB").save(final)
        os.remove(raw)

        return final

    except Exception:
        return YOUTUBE_IMG_URL