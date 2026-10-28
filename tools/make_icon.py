"""Vẽ biểu tượng app: móng trụ rời 3D (4 trụ: lót, bản đế vát, cổ trụ, bu lông), nhìn trục đo."""
import math
import os

from PIL import Image, ImageDraw

SS = 8                 # vẽ to rồi thu nhỏ để mịn
SIZE = 48
W = SIZE * SS * 2
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
K = W / 14.5           # đơn vị -> pixel
OX, OY = W / 2, W * 0.7


def P(x, y, z):
    """Trục đo: x sang phải-xuống, y sang trái-xuống, z lên."""
    return (OX + (x - y) * C30 * K, OY + ((x + y) * S30 - z) * K)


def shade(base, f):
    return tuple(max(0, min(255, int(c * f))) for c in base) + (255,)


CON = (205, 208, 212)
EDGE = (88, 92, 100, 255)


def poly(d, pts, col):
    d.polygon([P(*p) for p in pts], fill=col, outline=EDGE, width=max(1, int(0.55 * SS)))


def box(d, x0, y0, z0, x1, y1, z1, col):
    poly(d, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], shade(col, 0.80))   # mặt trước-trái
    poly(d, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], shade(col, 0.62))   # mặt trước-phải
    poly(d, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], shade(col, 1.06))   # mặt trên


PALETTES = {
    # tên: lót, bản móng, dầm, cổ móng, bu lông, nền (None = trong suốt)
    "xam": dict(lot=(150, 150, 150), slab=CON, rib=CON, pier=CON, bolt=(40, 40, 40), bg=None),
    "cam": dict(lot=(196, 164, 116), slab=(208, 211, 216), rib=(74, 134, 196), pier=(242, 142, 44),
                bolt=(35, 35, 35), bg=None),
    "xanh": dict(lot=(150, 140, 125), slab=(176, 206, 228), rib=(44, 96, 166), pier=(22, 158, 146),
                 bolt=(30, 30, 30), bg=None),
    "nen": dict(lot=(196, 164, 116), slab=(214, 217, 222), rib=(150, 186, 222), pier=(242, 142, 44),
                bolt=(25, 25, 25), bg=(31, 58, 95)),
    "am": dict(lot=(140, 120, 100), slab=(232, 204, 146), rib=(192, 84, 62), pier=(96, 104, 116),
               bolt=(30, 30, 30), bg=None),
}
PAL = "am"                # phương án D - tông ấm (đã chọn)


def draw(pal, size=SIZE):
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a, L, hv, hb, pm = 2.3, 1.75, 0.35, 0.95, 0.62     # tim trụ, nửa cạnh bản đế, cao mép / gờ, nửa gờ
    hc, H = 0.42, 4.1                                   # nửa cạnh cổ, đỉnh cổ
    for x, y in ((-a, -a), (a, -a), (-a, a), (a, a)):  # vẽ từ xa tới gần
        box(d, x - L - 0.18, y - L - 0.18, -0.2, x + L + 0.18, y + L + 0.18, 0.0, pal["lot"])
        box(d, x - L, y - L, 0.0, x + L, y + L, hv, pal["slab"])
        # mặt vát: 2 mặt phía trước (thấy được) + gờ phẳng
        poly(d, [(x - L, y + L, hv), (x + L, y + L, hv), (x + pm, y + pm, hb), (x - pm, y + pm, hb)],
             shade(pal["slab"], 0.86))
        poly(d, [(x + L, y - L, hv), (x + L, y + L, hv), (x + pm, y + pm, hb), (x + pm, y - pm, hb)],
             shade(pal["slab"], 0.70))
        poly(d, [(x - L, y - L, hv), (x + L, y - L, hv), (x + pm, y - pm, hb), (x - pm, y - pm, hb)],
             shade(pal["slab"], 1.10))
        poly(d, [(x - L, y - L, hv), (x - L, y + L, hv), (x - pm, y + pm, hb), (x - pm, y - pm, hb)],
             shade(pal["slab"], 1.02))
        poly(d, [(x - pm, y - pm, hb), (x + pm, y - pm, hb), (x + pm, y + pm, hb), (x - pm, y + pm, hb)],
             shade(pal["slab"], 1.10))
        box(d, x - hc, y - hc, hb, x + hc, y + hc, H, pal["pier"])
        for bx, by in ((-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)):
            cx, cy = x + bx, y + by
            x0, y0 = P(cx, cy, H)
            x1, y1 = P(cx, cy, H + 0.45)
            d.line([(x0, y0), (x1, y1)], fill=pal["bolt"] + (255,), width=int(1.1 * SS))
    bb = im.getbbox()                                  # cắt sát hình rồi đặt giữa ô vuông có lề
    im = im.crop(bb)
    side = int(max(im.width, im.height) * (1.22 if pal.get("bg") else 1.04))
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    if pal.get("bg"):                                  # nền vuông bo góc
        ImageDraw.Draw(sq).rounded_rectangle([0, 0, side - 1, side - 1], radius=side // 6, fill=pal["bg"] + (255,))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return sq.resize((size, size), Image.LANCZOS)


def main(out, pal=None):
    im = draw(PALETTES[pal or PAL])
    big = draw(PALETTES[pal or PAL], 256)
    big.save(out, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    im.save(os.path.splitext(out)[0] + ".png")


if __name__ == "__main__":
    main(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.ico"))
