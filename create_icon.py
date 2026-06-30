try:
    from PIL import Image, ImageDraw, ImageFont
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, size - 8, size - 8], fill="#1565C0", outline="#BBDEFB", width=6)
    try:
        font = ImageFont.truetype("segoeui.ttf", 140)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "Q", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 15), "Q", fill="white", font=font)
    img.save("app_icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Icon created: app_icon.ico")
except ImportError:
    print("Pillow not installed, skipping icon generation.")
