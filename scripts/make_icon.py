from pathlib import Path

from PIL import Image, ImageDraw


def make_icon() -> None:
    output = Path(__file__).resolve().parents[1] / "assets" / "app.ico"
    output.parent.mkdir(parents=True, exist_ok=True)

    size = 256
    image = Image.new("RGBA", (size, size), (20, 31, 57, 255))
    draw = ImageDraw.Draw(image)

    for inset in range(16):
        alpha = 255 - inset * 5
        draw.rounded_rectangle(
            (18 + inset, 18 + inset, 238 - inset, 238 - inset),
            radius=52 - inset,
            fill=(32 + inset, 94 + inset, 215 + inset, alpha),
        )

    draw.rounded_rectangle((42, 54, 214, 202), radius=30, fill=(11, 26, 55, 210))
    points = [
        (58, 130), (75, 130), (86, 92), (102, 172), (119, 110),
        (136, 150), (151, 78), (169, 162), (181, 118), (200, 118),
    ]
    draw.line(points, fill=(255, 255, 255, 255), width=12, joint="curve")
    draw.ellipse((52, 124, 64, 136), fill=(255, 255, 255, 255))
    draw.ellipse((194, 112, 206, 124), fill=(255, 255, 255, 255))

    image.save(
        output,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(output)


if __name__ == "__main__":
    make_icon()
