"""Generates the GET BONKED UI icon set: bold cartoony shapes, thick dark outline, 256x256, transparent."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 1024  # drawn at 4x, downsampled for smooth edges
OUT = 256
DARK = (28, 22, 36, 255)
OUTLINE = 34  # outline thickness at S


def canvas():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def finish(img, name, out_dir):
    alpha = img.getchannel("A")
    # Dilate the silhouette: blur then threshold gives a rounded outline.
    grown = alpha.filter(ImageFilter.GaussianBlur(OUTLINE / 2)).point(lambda a: 255 if a > 6 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(2))
    # Soft drop shadow under the outline.
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.putalpha(grown.point(lambda a: int(a * 0.35)))
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    base.alpha_composite(shadow, (0, 18))
    outline = Image.new("RGBA", (S, S), DARK)
    outline.putalpha(grown)
    base.alpha_composite(outline)
    base.alpha_composite(img)
    base = base.resize((OUT, OUT), Image.LANCZOS)
    base.save(os.path.join(out_dir, f"{name}.png"))
    return base


def shine(d, box, radius, color):
    """A soft white highlight bar near the top of a shape."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=color)


def font(size):
    for path in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arial.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def star(cx, cy, r_out, r_in, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def hexagon(cx, cy, r, rot=0):
    return [
        (cx + r * math.cos(math.radians(rot + 60 * i)), cy + r * math.sin(math.radians(rot + 60 * i)))
        for i in range(6)
    ]


def thick_line(d, pts, width, color):
    d.line(pts, fill=color, width=width, joint="curve")
    for x, y in pts:
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)


# ---------------------------------------------------------------- icons

def cash():
    img, d = canvas()
    green, light, darkg = (70, 200, 80, 255), (150, 235, 140, 255), (30, 130, 50, 255)
    for i, (dx, dy, ang) in enumerate(((0, 70, -8), (0, -40, 6))):
        bill = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        b = ImageDraw.Draw(bill)
        b.rounded_rectangle((170, 330, 854, 694), radius=40, fill=green, outline=DARK, width=18)
        b.rounded_rectangle((220, 380, 804, 644), radius=26, outline=darkg, width=14)
        b.ellipse((412, 412, 612, 612), fill=light, outline=darkg, width=14)
        b.text((512, 512), "$", fill=darkg, font=font(170), anchor="mm")
        b.ellipse((250, 480, 314, 544), fill=light)
        b.ellipse((710, 480, 774, 544), fill=light)
        bill = bill.rotate(ang, resample=Image.BICUBIC, center=(512, 512), translate=(dx, dy))
        img.alpha_composite(bill)
    return img


def coin():
    img, d = canvas()
    d.ellipse((150, 150, 874, 874), fill=(225, 160, 20, 255))
    d.ellipse((150, 120, 874, 844), fill=(255, 205, 40, 255))
    d.ellipse((215, 185, 809, 779), fill=(255, 225, 90, 255))
    d.polygon(hexagon(512, 482, 250, 30), fill=(230, 165, 20, 255))
    d.polygon(hexagon(512, 482, 165, 30), fill=(255, 225, 90, 255))
    d.polygon(hexagon(512, 482, 95, 30), fill=(230, 165, 20, 255))
    shine(d, (300, 230, 520, 270), 20, (255, 245, 190, 255))
    return img


def clipboard():
    img, d = canvas()
    d.rounded_rectangle((220, 170, 804, 900), radius=60, fill=(215, 120, 50, 255))
    d.rounded_rectangle((280, 250, 744, 850), radius=26, fill=(250, 245, 230, 255))
    d.rounded_rectangle((380, 120, 644, 260), radius=40, fill=(255, 200, 40, 255))
    d.ellipse((472, 90, 552, 170), fill=(255, 200, 40, 255))
    d.ellipse((494, 112, 530, 148), fill=DARK)
    for i in range(4):
        y = 350 + i * 118
        d.ellipse((320, y - 22, 364, y + 22), fill=DARK)
        d.rounded_rectangle((400, y - 20, 700 - (i % 2) * 70, y + 20), radius=20, fill=(60, 60, 70, 255))
    return img


def menu():
    img, d = canvas()
    for i in range(3):
        y = 280 + i * 232
        d.ellipse((150, y - 65, 280, y + 65), fill=(255, 255, 255, 255))
        d.rounded_rectangle((330, y - 65, 874, y + 65), radius=65, fill=(255, 255, 255, 255))
    return img


def settings():
    img, d = canvas()
    cx = cy = 512
    pts = []
    teeth = 8
    for i in range(teeth * 4):
        a = math.radians(i * 360 / (teeth * 4) + 5.6)
        r = 390 if (i % 4) in (1, 2) else 300
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(170, 175, 190, 255))
    d.ellipse((cx - 300, cy - 300, cx + 300, cy + 300), fill=(170, 175, 190, 255))
    d.ellipse((cx - 250, cy - 250, cx + 250, cy + 250), fill=(205, 210, 222, 255))
    d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), fill=(0, 0, 0, 0))
    return img


def shop():
    img, d = canvas()
    blue, light = (60, 160, 255, 255), (150, 210, 255, 255)
    thick_line(d, [(110, 230), (230, 230), (300, 640)], 60, (120, 120, 135, 255))
    d.polygon([(250, 300), (900, 300), (820, 640), (320, 640)], fill=blue)
    for x in (410, 530, 650, 770):
        d.line([(x, 320), (x - 15, 620)], fill=light, width=26)
    d.line([(290, 470), (860, 470)], fill=light, width=26)
    d.rounded_rectangle((300, 660, 820, 720), radius=30, fill=(120, 120, 135, 255))
    for x in (380, 740):
        d.ellipse((x - 80, 740, x + 80, 900), fill=(60, 60, 70, 255))
        d.ellipse((x - 30, 790, x + 30, 850), fill=(200, 200, 210, 255))
    return img


def gift():
    img, d = canvas()
    red, lid, ribbon = (235, 60, 80, 255), (250, 90, 105, 255), (255, 215, 50, 255)
    d.ellipse((300, 150, 520, 360), fill=ribbon)
    d.ellipse((504, 150, 724, 360), fill=ribbon)
    d.ellipse((370, 215, 470, 305), fill=(220, 170, 20, 255))
    d.ellipse((554, 215, 654, 305), fill=(220, 170, 20, 255))
    d.rounded_rectangle((210, 470, 814, 890), radius=30, fill=red)
    d.rounded_rectangle((170, 330, 854, 490), radius=34, fill=lid)
    d.rectangle((452, 330, 572, 890), fill=ribbon)
    d.ellipse((440, 290, 584, 400), fill=ribbon)
    shine(d, (210, 350, 420, 380), 15, (255, 170, 180, 255))
    return img


def quest():
    img, d = canvas()
    paper, roll = (250, 230, 175, 255), (215, 175, 105, 255)
    d.rectangle((230, 230, 794, 800), fill=paper)
    d.rounded_rectangle((180, 150, 844, 270), radius=60, fill=roll)
    d.ellipse((150, 150, 270, 270), fill=(190, 145, 80, 255))
    d.ellipse((754, 150, 874, 270), fill=(190, 145, 80, 255))
    d.rounded_rectangle((180, 760, 844, 880), radius=60, fill=roll)
    d.ellipse((150, 760, 270, 880), fill=(190, 145, 80, 255))
    d.ellipse((754, 760, 874, 880), fill=(190, 145, 80, 255))
    for i, w in enumerate((420, 340, 400, 260)):
        y = 340 + i * 100
        d.rounded_rectangle((300, y - 18, 300 + w, y + 18), radius=18, fill=(150, 110, 60, 255))
    d.polygon(star(700, 690, 70, 30), fill=(235, 70, 60, 255))
    return img


def spin():
    img, d = canvas()
    cx, cy, r = 512, 540, 360
    colors = [(235, 70, 80), (255, 200, 40), (70, 190, 90), (60, 160, 255)]
    d.ellipse((cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30), fill=(250, 250, 255, 255))
    for i in range(8):
        d.pieslice((cx - r, cy - r, cx + r, cy + r), i * 45 - 90, (i + 1) * 45 - 90, fill=colors[i % 4] + (255,))
    for i in range(8):
        a = math.radians(i * 45 - 90)
        d.line([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))], fill=DARK, width=12)
    d.ellipse((cx - 80, cy - 80, cx + 80, cy + 80), fill=(250, 250, 255, 255))
    d.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=(255, 200, 40, 255))
    d.polygon([(cx - 70, 90), (cx + 70, 90), (cx, 230)], fill=(235, 50, 60, 255))
    return img


def index():
    img, d = canvas()
    purple, dark = (140, 90, 240, 255), (100, 60, 190, 255)
    d.rounded_rectangle((250, 170, 830, 880), radius=40, fill=(245, 245, 250, 255))
    d.rounded_rectangle((200, 130, 780, 850), radius=40, fill=purple)
    d.rounded_rectangle((200, 130, 300, 850), radius=40, fill=dark)
    d.rectangle((260, 130, 300, 850), fill=dark)
    for i in range(3):
        d.line([(790, 250 + i * 200), (830, 250 + i * 200)], fill=(200, 200, 210, 255), width=12)
    d.polygon(star(540, 470, 190, 80), fill=(255, 210, 40, 255))
    d.rounded_rectangle((380, 700, 700, 740), radius=20, fill=(190, 160, 255, 255))
    return img


def trophy():
    img, d = canvas()
    gold, dgold = (255, 200, 40, 255), (225, 150, 20, 255)
    for x0 in (130, 674):
        d.ellipse((x0, 220, x0 + 220, 470), fill=dgold)
        d.ellipse((x0 + 55, 275, x0 + 165, 415), fill=(0, 0, 0, 0))
    d.chord((230, 0, 794, 640), 0, 180, fill=gold)
    d.rectangle((230, 150, 794, 330), fill=gold)
    d.rectangle((452, 600, 572, 760), fill=dgold)
    d.rounded_rectangle((300, 740, 724, 820), radius=20, fill=dgold)
    d.rounded_rectangle((250, 800, 774, 900), radius=26, fill=(150, 90, 50, 255))
    d.polygon(star(512, 380, 120, 50), fill=(255, 240, 150, 255))
    shine(d, (290, 180, 370, 460), 40, (255, 235, 140, 255))
    return img


def bonk_rain():
    img, d = canvas()
    cloud = (240, 248, 255, 255)
    shadow = (190, 210, 235, 255)
    for box in ((150, 330, 450, 610), (330, 180, 690, 540), (560, 280, 870, 590), (230, 420, 800, 640)):
        d.ellipse(box, fill=shadow)
    for box in ((150, 310, 450, 580), (330, 160, 690, 510), (560, 260, 870, 560), (230, 400, 800, 600)):
        d.ellipse(box, fill=cloud)
    for x, y in ((300, 760), (512, 820), (724, 760)):
        d.polygon([(x, y - 130), (x - 55, y), (x + 55, y)], fill=(60, 160, 255, 255))
        d.ellipse((x - 58, y - 60, x + 58, y + 58), fill=(60, 160, 255, 255))
        d.ellipse((x - 30, y - 30, x - 5, y), fill=(190, 230, 255, 255))
    return img


def speed():
    img, d = canvas()
    white = (255, 255, 255, 255)
    for i, y in enumerate((440, 560, 680)):
        d.rounded_rectangle((90 + i * 30, y - 22, 300 + i * 30, y + 22), radius=22, fill=(200, 215, 235, 255))
    d.ellipse((560, 110, 740, 290), fill=white)
    thick_line(d, [(600, 330), (500, 560)], 110, white)  # body
    thick_line(d, [(600, 360), (740, 470), (840, 380)], 70, white)  # front arm
    thick_line(d, [(580, 370), (450, 400), (380, 500)], 70, white)  # back arm
    thick_line(d, [(500, 560), (660, 670), (640, 860)], 80, white)  # front leg
    thick_line(d, [(500, 560), (400, 720), (270, 760)], 80, white)  # back leg
    return img


def paw():
    img, d = canvas()
    pad, toe = (245, 150, 60, 255), (250, 175, 90, 255)
    d.ellipse((270, 450, 754, 860), fill=pad)
    d.ellipse((330, 470, 694, 780), fill=toe)
    for box in ((140, 330, 320, 560), (330, 170, 510, 420), (514, 170, 694, 420), (704, 330, 884, 560)):
        d.ellipse(box, fill=pad)
    for box in ((180, 370, 280, 500), (370, 210, 470, 360), (554, 210, 654, 360), (744, 370, 844, 500)):
        d.ellipse(box, fill=(255, 205, 150, 255))
    return img


def lock():
    img, d = canvas()
    d.arc((300, 110, 724, 560), 180, 360, fill=(170, 175, 190, 255), width=90)
    d.rectangle((300, 330, 390, 480), fill=(170, 175, 190, 255))
    d.rectangle((634, 330, 724, 480), fill=(170, 175, 190, 255))
    d.rounded_rectangle((200, 430, 824, 900), radius=60, fill=(255, 200, 40, 255))
    d.rounded_rectangle((200, 430, 824, 520), radius=40, fill=(255, 225, 110, 255))
    d.ellipse((452, 560, 572, 680), fill=DARK)
    d.polygon([(470, 650), (554, 650), (580, 800), (444, 800)], fill=DARK)
    return img


def arrow_up():
    img, d = canvas()
    yellow = (255, 225, 20, 255)
    d.polygon([(512, 110), (880, 520), (660, 520), (660, 900), (364, 900), (364, 520), (144, 520)], fill=yellow)
    d.polygon([(512, 190), (760, 470), (610, 470), (610, 540), (414, 540), (414, 470), (264, 470)],
              fill=(255, 245, 140, 255))
    return img


ICONS = [
    ("cash", cash), ("coin", coin), ("clipboard", clipboard), ("menu", menu), ("settings", settings),
    ("shop", shop), ("gift", gift), ("quest", quest), ("spin", spin), ("index", index), ("trophy", trophy),
    ("bonk_rain", bonk_rain), ("speed", speed), ("paw", paw), ("lock", lock), ("arrow_up", arrow_up),
]


def main():
    out_dir, sheet_path = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    tiles = [finish(fn(), name, out_dir) for name, fn in ICONS]
    # Contact sheet on a mid-grey background, to check the icons.
    cols = 8
    sheet = Image.new("RGBA", (cols * OUT, 2 * OUT), (90, 140, 90, 255))
    for i, tile in enumerate(tiles):
        sheet.alpha_composite(tile, ((i % cols) * OUT, (i // cols) * OUT))
    sheet.save(sheet_path)


if __name__ == "__main__":
    main()
