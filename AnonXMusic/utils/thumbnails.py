async def get_thumb(videoid, user_id):
    try:
        path = f"cache/{videoid}_{user_id}.png"
        if os.path.isfile(path):
            return path

        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        result = (await search.next())["result"][0]

        title = result.get("title", "Unknown Title")
        title = " ".join(title.split()[:6])
        duration = result.get("duration", "00:00")
        channel = result.get("channel", {}).get("name", "")
        thumb_url = result["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open("cache/temp.png", "wb") as f:
                    await f.write(await r.read())

        yt = Image.open("cache/temp.png").convert("RGBA")

        # Background
        base = changeImageSize(1280, 720, yt)
        bg = base.filter(ImageFilter.GaussianBlur(20))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)

        draw = ImageDraw.Draw(bg)

        # Glass Player Bar
        bar = (180, 160, 1100, 520)
        draw.rounded_rectangle(bar, radius=45, fill=(25, 25, 25, 220))

        # Song Thumbnail
        thumb = changeImageSize(220, 220, yt)
        mask = Image.new("L", thumb.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, thumb.size[0], thumb.size[1]), radius=30, fill=255
        )
        bg.paste(thumb, (220, 200), mask)

        # Fonts
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 36)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 26)

        # Text
        draw.text((480, 210), "Now Playing", fill="gray", font=font_small)

        safe_title = fit_text(draw, title, font_title, 520)
        draw.text((480, 250), safe_title, fill="white", font=font_title)
        draw.text((480, 295), channel, fill="lightgray", font=font_small)

        # Progress Bar
        draw.rounded_rectangle(
            (480, 350, 980, 360), radius=6, fill=(100, 100, 100)
        )
        draw.rounded_rectangle(
            (480, 350, 720, 360), radius=6, fill=(255, 255, 255)
        )

        draw.text((480, 370), "0:00", fill="white", font=font_small)
        draw.text((950, 370), duration, fill="white", font=font_small)

        # Controls
        cy = 440

        # Shuffle
        draw.arc((480, cy - 15, 520, cy + 15), 0, 300, fill="white", width=3)

        # Prev
        draw.polygon([(580, cy), (610, cy - 15), (610, cy + 15)], fill="white")
        draw.polygon([(610, cy), (640, cy - 15), (640, cy + 15)], fill="white")

        # Play
        draw.ellipse((690, cy - 22, 730, cy + 22), outline="white", width=3)
        draw.polygon([(705, cy - 12), (705, cy + 12), (725, cy)], fill="white")

        # Next
        draw.polygon([(780, cy), (750, cy - 15), (750, cy + 15)], fill="white")
        draw.polygon([(810, cy), (780, cy - 15), (780, cy + 15)], fill="white")

        # Bot Name
        draw.text(
            (1050, 25),
            unidecode(app.name),
            fill="white",
            font=font_small,
        )

        bg.save(path)
        os.remove("cache/temp.png")
        return path

    except Exception:
        return YOUTUBE_IMG_URL