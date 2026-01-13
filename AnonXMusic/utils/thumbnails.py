import os, random, aiofiles, aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from ytSearch import VideosSearch

from config import YOUTUBE_IMG_URL


def short(txt):
    return txt[:7]


def rand_time():
    m = random.randint(0,4)
    s = random.randint(10,59)
    return f"{m}:{s}"


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

        # BLUR BACKGROUND
        bg = base.resize((1280,720))
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        draw = ImageDraw.Draw(bg)

        # CLEAR RECTANGLE
        rect = base.resize((620,330))
        rx = (1280-620)//2
        ry = 60
        bg.paste(rect,(rx,ry))

        # BORDER
        draw.rounded_rectangle(
            (rx-5,ry-5,rx+625,ry+335),
            radius=25,
            outline="white",
            width=4
        )

        # WAVEFORM DESIGN
        cx = 640
        cy = 225

        for i in range(-230,230,18):
            h = abs(i)%90+20
            draw.line(
                [(cx+i,cy-h),(cx+i,cy+h)],
                fill="white",
                width=3
            )

        # FONTS
        title_f = ImageFont.truetype("AnonXMusic/assets/font.ttf",32)
        small = ImageFont.truetype("AnonXMusic/assets/font2.ttf",20)

        # TITLE
        draw.text(
            (640,410),
            short(title),
            fill="white",
            font=title_f,
            anchor="mm"
        )

        # CHANNEL
        draw.text(
            (640,440),
            channel,
            fill="white",
            font=small,
            anchor="mm"
        )

        # DURATION
        t1 = rand_time()
        t2 = rand_time()

        draw.text((350,480),t1,fill="white",font=small)
        draw.text((900,480),t2,fill="white",font=small)

        # PROGRESS BAR
        bar_x1 = 380
        bar_x2 = 900
        y = 500

        draw.line([(bar_x1,y),(bar_x2,y)],fill="#555",width=8)
        draw.line([(bar_x1,y),(bar_x1+200,y)],fill="white",width=8)

        draw.ellipse(
            (bar_x1+190,y-10,bar_x1+210,y+10),
            fill="white"
        )

        # CONTROLS
        f = ImageFont.truetype("AnonXMusic/assets/font2.ttf",30)

        draw.text((520,535),"⏮",fill="white",font=f)
        draw.text((600,530),"▶",fill="white",font=f)
        draw.text((680,535),"⏭",fill="white",font=f)

        # VOLUME BAR
        vy = 580

        draw.text((430,570),"🔊",fill="white",font=f)
        draw.text((800,570),"🔇",fill="white",font=f)

        draw.line([(480,580),(780,580)],fill="white",width=4)
        draw.ellipse((610,570,630,590),fill="white")

        bg.save(file)
        os.remove("cache/temp.jpg")

        return file

    except:
        return YOUTUBE_IMG_URL
