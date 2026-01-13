import os, random, aiofiles, aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from ytSearch import VideosSearch

from config import YOUTUBE_IMG_URL


def short(txt):
    return txt[:22]


def rand_time():
    return f"{random.randint(0,2)}:{random.randint(10,59)}"


async def get_thumb(videoid, user_id):

    try:
        file = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(file):
            return file

        url = f"https://youtube.com/watch?v={videoid}"
        search = VideosSearch(url, limit=1)

        for r in (await search.next())["result"]:
            title = r["title"]
            channel = r["channel"]["name"]
            thumb = r["thumbnails"][0]["url"].split("?")[0]

        # download
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb) as r:
                async with aiofiles.open("cache/temp.jpg","wb") as f:
                    await f.write(await r.read())

        base = Image.open("cache/temp.jpg").convert("RGBA")

        # BACKGROUND
        bg = base.resize((1280,720))
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # GLASS CARD
        card = Image.new("RGBA",(900,350),(0,0,0,160))
        bg.paste(card,(190,185),card)

        # ALBUM THUMB
        album = base.resize((220,220))
        bg.paste(album,(220,215))

        # FONTS
        title_f = ImageFont.truetype("AnonXMusic/assets/font.ttf",34)
        small = ImageFont.truetype("AnonXMusic/assets/font2.ttf",22)

        # TITLE
        draw.text(
            (480,240),
            short(title),
            fill="white",
            font=title_f
        )

        # CHANNEL
        draw.text(
            (480,280),
            channel,
            fill="#cccccc",
            font=small
        )

        # TIME
        t1 = rand_time()
        t2 = rand_time()

        draw.text((480,315),t1,fill="white",font=small)
        draw.text((900,315),f"-{t2}",fill="white",font=small)

        # PROGRESS BAR
        x1,x2,y = 480,900,340
        draw.line([(x1,y),(x2,y)],fill="#777",width=6)
        draw.line([(x1,y),(x1+160,y)],fill="white",width=6)

        draw.ellipse((x1+150,y-8,x1+166,y+8),fill="white")

        # CONTROLS
        f = ImageFont.truetype("AnonXMusic/assets/font2.ttf",36)

        draw.text((520,370),"⏮",fill="white",font=f)
        draw.text((600,365),"⏸",fill="white",font=f)
        draw.text((680,370),"⏭",fill="white",font=f)

        # VOLUME
        draw.text((760,370),"🔊",fill="white",font=small)
        draw.text((870,370),"🔇",fill="white",font=small)

        draw.line([(800,390),(860,390)],fill="white",width=4)
        draw.ellipse((825,382,837,394),fill="white")

        bg.save(file)
        os.remove("cache/temp.jpg")

        return file

    except:
        return YOUTUBE_IMG_URL
