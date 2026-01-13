import os, aiofiles, aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from ytSearch import VideosSearch

from config import YOUTUBE_IMG_URL


async def get_thumb(videoid, user_id):

    try:
        file = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(file):
            return file

        url = f"https://youtube.com/watch?v={videoid}"
        search = VideosSearch(url, limit=1)

        for r in (await search.next())["result"]:
            title = r["title"][:10]
            thumb = r["thumbnails"][0]["url"].split("?")[0]

        # Download
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

        # MAIN PLAYER RECTANGLE
        x1,y1,x2,y2 = 340,80,940,430
        draw.rounded_rectangle(
            (x1,y1,x2,y2),
            radius=30,
            outline="white",
            width=5
        )

        # WAVEFORM
        cx = (x1+x2)//2
        cy = (y1+y2)//2

        for i in range(-200,200,15):
            h = abs(i)%80+20
            draw.line(
                [(cx+i,cy-h),(cx+i,cy+h)],
                fill="white",
                width=3
            )

        # HEART ICON
        draw.text((360,460),"♡",fill="white")

        # TITLE
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf",28)
        draw.text((640,465),title,fill="white",anchor="mm",font=font)

        # 3 DOTS
        draw.text((900,460),"⋯",fill="white",font=font)

        # PROGRESS BAR
        bar_x1 = 380
        bar_x2 = 900
        bar_y = 510

        draw.line(
            [(bar_x1,bar_y),(bar_x2,bar_y)],
            fill="#555",
            width=8
        )

        # FILLED PART
        draw.line(
            [(bar_x1,bar_y),(bar_x1+200,bar_y)],
            fill="white",
            width=8
        )

        # SLIDER DOT
        draw.ellipse(
            (bar_x1+190,bar_y-10,bar_x1+210,bar_y+10),
            fill="white"
        )

        # CONTROL ICONS
        f = ImageFont.truetype("AnonXMusic/assets/font2.ttf",30)

        draw.text((520,560),"⟲",fill="white",font=f)
        draw.text((580,560),"⏮",fill="white",font=f)
        draw.text((640,555),"▶",fill="white",font=f)
        draw.text((700,560),"⏭",fill="white",font=f)
        draw.text((760,560),"🔁",fill="white",font=f)

        bg.save(file)
        os.remove("cache/temp.jpg")

        return file

    except:
        return YOUTUBE_IMG_URL
