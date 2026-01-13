from PIL import Image, ImageDraw
import random

WIDTH, HEIGHT = 1280, 720
FRAMES = 20
BAR_COUNT = 24
BAR_WIDTH = 14
BAR_MAX_HEIGHT = 120
BAR_BASE_Y = 520

def generate_thumbnail_gif(output="thumbnail.gif"):
    frames = []

    for frame in range(FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), "#2f2f2f")
        draw = ImageDraw.Draw(img)

        # Main rounded rectangle
        draw.rounded_rectangle(
            [(140, 180), (1140, 560)],
            radius=50,
            fill="#4a4a4a"
        )

        # 🎶 Animated Equalizer Bars
        start_x = 300
        for i in range(BAR_COUNT):
            height = random.randint(30, BAR_MAX_HEIGHT)
            x1 = start_x + i * (BAR_WIDTH + 6)
            y1 = BAR_BASE_Y - height
            x2 = x1 + BAR_WIDTH
            y2 = BAR_BASE_Y

            color = random.choice([
                "#ff4d4d", "#ffa64d",
                "#4dd2ff", "#4dff88",
                "#c77dff"
            ])

            draw.rounded_rectangle(
                [(x1, y1), (x2, y2)],
                radius=6,
                fill=color
            )

        frames.append(img)

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0
    )

    return output


if __name__ == "__main__":
    generate_thumbnail_gif()