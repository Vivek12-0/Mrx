import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from ytSearch import VideosSearch
from unidecode import unidecode

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def trim_text(text, max_len=40):
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text


def split_title(text):
    words = text.split()
    mid = len(words)//2
    return " ".join(words[:mid]), " ".join(words[mid:])


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

        title = trim_text(title, 60)
        t1, t2 = split_title(title)

        thumb_url = r["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw, "wb") as f:
                    await f.write(await resp.read())

        yt = Image.open(raw).convert("RGBA")

        # BACKGROUND
        bg = yt.resize((1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.30)

        # PLAYER BOX (LIGHT BLACK TRANSPARENT)
        box_x, box_y = 150, 90
        box_w, box_h = 980, 540

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        od.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius=45,
            fill=(25, 25, 25, 180)  # 👈 LIGHT BLACK + TRANSPARENT
        )

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # COVER
        cover = yt.resize((260, 260))
        bg.paste(cover, (box_x + 50, box_y + 60))

        # FONTS
        try:
            title_font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 36)
            small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        text_x = box_x + 350

        # TITLE
        draw.text((text_x, box_y + 70), t1, fill="white", font=title_font)
        draw.text((text_x, box_y + 115), t2, fill="white", font=title_font)

        # CHANNEL
        draw.text(
            (text_x, box_y + 165),
            channel,
            fill=(200, 200, 200),
            font=small_font
        )

        # PROGRESS BAR
        bar_y = box_y + 230
        draw.line(
            (text_x, bar_y, box_x + box_w - 80, bar_y),
            fill=(160, 160, 160),
            width=5
        )
        draw.line(
            (text_x, bar_y, text_x + 240, bar_y),
            fill="white",
            width=5
        )
        draw.ellipse(
            (text_x + 232, bar_y - 7, text_x + 252, bar_y + 11),
            fill="white"
        )

        # TIME
        draw.text((text_x, bar_y + 18), "0:00", fill="white", font=small_font)
        draw.text(
            (box_x + box_w - 130, bar_y + 18),
            duration,
            fill="white",
            font=small_font
        )

        # BUTTONS
        btn_y = box_y + 310

        # Prev
        draw.polygon([(text_x+40, btn_y+15),(text_x+70, btn_y),(text_x+70, btn_y+30)], fill="white")
        draw.polygon([(text_x+20, btn_y+15),(text_x+40, btn_y),(text_x+40, btn_y+30)], fill="white")

        # Pause
        draw.rectangle((text_x+100, btn_y, text_x+112, btn_y+32), fill="white")
        draw.rectangle((text_x+125, btn_y, text_x+137, btn_y+32), fill="white")

        # Next
        draw.polygon([(text_x+170, btn_y),(text_x+170, btn_y+30),(text_x+200, btn_y+15)], fill="white")
        draw.polygon([(text_x+200, btn_y),(text_x+200, btn_y+30),(text_x+230, btn_y+15)], fill="white")

        # BOT NAME
        draw.text(
            (box_x + box_w - 220, box_y + 30),
            unidecode(app.name),
            fill=(170,170,170),
            font=small_font
        )

        bg.convert("RGB").save(final)
        os.remove(raw)
        return final

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
