"""Final low-poly decor models for the theme DJStage (15 parts around the fifth Shiba).

Usage: blender --background --factory-startup --python build_DJStage.py -- <outdir> [Part,Part]
Writes Decor_DJStage_<PartId>.fbx, preview_<PartId>.png and stage_DJStage*.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height).
Text is flat pixel lettering that reads correctly from +z (road side) in the game.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "DJStage"))
ONLY = ARGS[1].split(",") if len(ARGS) > 1 else None
KEY = "DJStage"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_DJStage.json"))
RNG = random.Random(11)

# ---- palette (one for all 15 parts) ---------------------------------------------------------------------------------
BLK = (22, 22, 30)
DRK = (45, 45, 60)
DRK2 = (34, 34, 46)
MET = (150, 155, 168)
LMET = (195, 200, 212)
DMET = (100, 105, 118)
PNK = (255, 70, 165)
DPNK = (190, 40, 120)
CYN = (50, 205, 255)
DCYN = (30, 140, 185)
PUR = (150, 80, 230)
DPUR = (95, 50, 160)
YEL = (255, 215, 60)
WHT = (240, 240, 245)
RED = (200, 40, 60)
DRED = (140, 25, 45)
GLD = (255, 195, 40)
DGLD = (205, 150, 30)
WOOD = (130, 90, 55)
DWOOD = (88, 60, 38)
SKIN = (230, 190, 150)
JEAN = (50, 60, 110)


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vc(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xc(p, x0, x1, cy, cz, r, col, verts=10, jit=0.04):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zc(p, cx, cy, z0, z1, r, col, verts=10, top_r=None, jit=0.04):
    """Cylinder along z; radius r sits at the +z end, top_r (if given) at the -z end."""
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, top_radius=top_r, jitter=jit)


def bl(p, c, r, col, scale=(1, 1, 1), sub=1, jit=0.05):
    return dk.ball(p, c, r, col, scale=scale, subdiv=sub, jitter=jit)


def bar(p, a, b, t, col, jit=0.04):
    """Square bar of thickness t between two stage points."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized() * (t / 2)
    v = d.cross(u).normalized() * (t / 2)
    pts = []
    for q in (a, b):
        for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            pts.append(tuple(q + u * su + v * sv))
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def facets(o, palette):
    """Repaint every face of an object with a random pick of the palette (disco-ball look)."""
    attr = o.data.color_attributes.get("Col")
    for poly in o.data.polygons:
        c = RNG.choice(palette)
        cc = dk.srgb(*dk.shade(c, 1 + (RNG.random() - 0.5) * 0.18))
        for li in poly.loop_indices:
            attr.data[li].color = (*cc, 1.0)


FONT = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'J': ["..###", "....#", "....#", "....#", "....#", "#...#", ".###."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
}


def pix(p, text, x0, y0, z, ps, col, plane='xy'):
    """Flat pixel lettering. plane 'xy': on a wall, bottom-left (x0, y0) at depth z, reads from +z.
    plane 'xz': on the floor at height y0, bottom edge at z (front), top toward -z, reads from the road. Returns total width."""
    quads, cx = [], 0
    for ch in text:
        g = FONT[ch]
        for r in range(7):
            row, c = g[r], 0
            while c < 5:
                if row[c] == '#':
                    c2 = c
                    while c2 + 1 < 5 and row[c2 + 1] == '#':
                        c2 += 1
                    lo = (6 - r) * ps
                    quads.append((x0 + (cx + c) * ps, x0 + (cx + c2 + 1) * ps, lo, lo + ps))
                    c = c2 + 1
                else:
                    c += 1
        cx += 6
    bm = bmesh.new()
    for xa, xb, lo, hi in quads:
        if plane == 'xy':
            pts = [(xa, y0 + lo, z), (xb, y0 + lo, z), (xb, y0 + hi, z), (xa, y0 + hi, z)]
            want = Vector((0, 1, 0))
        else:
            pts = [(xa, y0, z - lo), (xb, y0, z - lo), (xb, y0, z - hi), (xa, y0, z - hi)]
            want = Vector((0, 0, 1))
        f = bm.faces.new([bm.verts.new((q[0], q[2], q[1])) for q in pts])
        bm.normal_update()
        if f.normal.dot(want) < 0:
            f.normal_flip()
    dk._object(p, "Text", bm, Vector((0, 0, 0)), (0, 0, 0), col, 0.0)
    return cx * ps - ps


def star4(p, c, axis, r, col):
    """Flat four-point sparkle around c, facing +z ('z'), +x ('x'), -x ('-x') or +y ('y')."""
    cx, cy, cz = c
    ring = []
    for k in range(8):
        a = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.26
        ring.append((rr * math.cos(a), rr * math.sin(a)))
    bm = bmesh.new()

    def at(a, b):
        if axis == 'z':
            q = (cx + a, cy + b, cz)
        elif axis in ('x', '-x'):
            q = (cx, cy + b, cz + (a if axis == 'x' else -a))
        else:
            q = (cx + a, cy, cz - b)
        return bm.verts.new((q[0], q[2], q[1]))
    mid = at(0, 0)
    vs = [at(*q) for q in ring]
    want = {'z': Vector((0, 1, 0)), 'x': Vector((1, 0, 0)), '-x': Vector((-1, 0, 0)), 'y': Vector((0, 0, 1))}[axis]
    for k in range(8):
        f = bm.faces.new([mid, vs[k], vs[(k + 1) % 8]])
        bm.normal_update()
        if f.normal.dot(want) < 0:
            f.normal_flip()
    dk._object(p, "Spark", bm, Vector((0, 0, 0)), (0, 0, 0), col, 0.0)


def zig_xy(p, xa, xb, y0, y1, z, n, t, depth, col, vertical=True):
    """Zigzag lattice braces in the x-y plane. vertical: braces climb along y (n steps), else run along x."""
    for i in range(n):
        if vertical:
            ya, yb = y0 + (y1 - y0) * i / n, y0 + (y1 - y0) * (i + 1) / n
            a, b = ((xa, ya), (xb, yb)) if i % 2 == 0 else ((xb, ya), (xa, yb))
        else:
            xl, xr = xa + (xb - xa) * i / n, xa + (xb - xa) * (i + 1) / n
            a, b = ((xl, y0), (xr, y1)) if i % 2 == 0 else ((xl, y1), (xr, y0))
        bar(p, (a[0], a[1], z), (b[0], b[1], z), t, col)


def zig_zy(p, x, za, zb, y0, y1, n, t, col):
    """Zigzag braces in the z-y plane at x (a side face of a vertical tower)."""
    for i in range(n):
        ya, yb = y0 + (y1 - y0) * i / n, y0 + (y1 - y0) * (i + 1) / n
        a, b = ((za, ya), (zb, yb)) if i % 2 == 0 else ((zb, ya), (za, yb))
        bar(p, (x, a[1], a[0]), (x, b[1], b[0]), t, col)


def woofer(p, cx, cy, z, r, verts=10, cap=True, ring=DMET, cone=DRK2):
    """Speaker driver on a front face at z (+z side): metal ring, dark cone, small cap."""
    zc(p, cx, cy, z - 0.02, z + 0.14, r, ring, verts)
    zc(p, cx, cy, z + 0.14, z + 0.22, r * 0.84, cone, verts)
    if cap:
        zc(p, cx, cy, z + 0.22, z + 0.36, r * 0.32, MET, 8)


# ================================================================================================================================
# 1. Floor: 4 x 3 coloured tiles, each split into four shaded quadrants
def build_Floor(p):
    cols = [PNK, CYN, PUR, YEL]
    bx(p, (13.2, 56.8), (0, 0.1), (29.2, 58.8), BLK, 0.02)
    for i in range(4):
        for j in range(3):
            x0, z0 = 18.5 + i * 11 - 5.3, 34 + j * 10 - 4.8
            c = cols[(i + j) % 4]
            bx(p, (x0, x0 + 10.6), (0.1, 0.2), (z0, z0 + 9.6), dk.shade(c, 0.78), 0.02)
            xm, zm = x0 + 5.3, z0 + 4.8
            for a in range(2):
                for b in range(2):
                    xa = (x0 + 0.45) if a == 0 else (xm + 0.2)
                    za = (z0 + 0.45) if b == 0 else (zm + 0.2)
                    f = 1.16 if (a + b) % 2 == 0 else 0.92
                    bx(p, (xa, xa + 4.65), (0.2, 0.26), (za, za + 4.15), dk.shade(c, f), 0.02)
            bx(p, (xm - 1.5, xm + 1.5), (0.26, 0.3), (zm - 1.5, zm + 1.5), dk.shade(c, 1.45), 0.0, rot=(0, 45, 0))


# 2. BigStage
def build_BigStage(p):
    # platform
    bx(p, (25.3, 74.7), (0, 2.2), (-55, -25.3), BLK)
    bx(p, (25.4, 74.6), (2.2, 2.5), (-54.6, -25.4), DRK2)
    bx(p, (25.0, 75.0), (2.1, 2.5), (-25.4, -25.0), MET)          # front lip
    bx(p, (25.0, 25.3), (0, 2.5), (-55, -25.0), DMET)             # side trims
    bx(p, (74.7, 75.0), (0, 2.5), (-55, -25.0), DMET)
    for k in range(10):   # LED strip on the front skirt
        c = PNK if k % 2 == 0 else CYN
        bx(p, (26.0 + k * 4.8, 26.0 + k * 4.8 + 4.2), (0.7, 1.5), (-25.3, -25.0), c, 0.0)
    for x in (26, 74):    # foot uplights
        bx(p, (x - 1, x + 1), (2.5, 3.0), (-27.4, -25.4), PNK if x < 50 else CYN, 0.02)
        bx(p, (x - 0.7, x + 0.7), (3.0, 3.06), (-27.1, -25.7), WHT, 0.0)
    pix(p, "BONK", 39.65, 2.52, -28.6, 0.9, PNK, plane="xz")
    for zz in (-38.2, -43.6):
        bx(p, (28, 72), (2.5, 2.53), (zz, zz + 0.3), DCYN, 0.0)
    # DJ riser at the back
    bx(p, (38, 62), (2.5, 3.4), (-54, -46), DRK)
    bx(p, (38, 62), (3.4, 3.5), (-54, -46), DMET)
    for k in range(6):
        bx(p, (38.6 + k * 4, 38.6 + k * 4 + 3.0), (2.8, 3.1), (-46.05, -46.0), PNK if k % 2 == 0 else CYN, 0.0)
    # back wall with screen
    bx(p, (25, 75), (2.5, 16.5), (-55, -54), DRK)
    bx(p, (25, 75), (16.5, 17.0), (-55, -53.7), BLK)
    bx(p, (25, 27.6), (2.5, 16.5), (-54, -53.6), BLK)
    bx(p, (72.4, 75), (2.5, 16.5), (-54, -53.6), BLK)
    bx(p, (32.6, 67.4), (5.2, 13.8), (-54, -53.6), BLK)           # screen frame
    bx(p, (33.2, 66.8), (5.8, 13.2), (-53.6, -53.5), DPUR, 0.0)   # screen
    hs = [0.35, 0.55, 0.8, 0.5, 0.9, 0.65, 0.4, 0.75, 1.0, 0.6, 0.85, 0.45, 0.7, 0.5, 0.3]
    for k, h in enumerate(hs):
        c = PNK if h > 0.7 else (PUR if h > 0.5 else CYN)
        x = 34.2 + k * 2.1
        bx(p, (x, x + 1.6), (6.1, 6.1 + 6.4 * h), (-53.5, -53.4), c, 0.0)
    # truss towers and top beam
    for x in (27, 73):
        bx(p, (x - 1.2, x + 1.2), (2.5, 3.0), (-51.2, -48.8), BLK)
        for sx in (-0.6, 0.6):
            for sz in (-0.6, 0.6):
                bx(p, (x + sx - 0.14, x + sx + 0.14), (3.0, 20.4), (-50 + sz - 0.14, -50 + sz + 0.14), MET, 0.03)
        zig_xy(p, x - 0.6, x + 0.6, 3.0, 20.4, -49.4, 6, 0.12, 0.12, DMET)
    for sy in (20.6, 21.4):
        for sz in (-50.5, -49.5):
            bx(p, (26, 74), (sy - 0.14, sy + 0.14), (sz - 0.14, sz + 0.14), MET, 0.03)
    zig_xy(p, 26, 74, 20.6, 21.4, -49.4, 8, 0.12, 0.12, DMET, vertical=False)
    # stage lights under the beam
    for k, (x, c) in enumerate(((33, PNK), (41.5, CYN), (50, YEL), (58.5, PUR), (67, PNK))):
        bx(p, (x - 0.35, x + 0.35), (19.9, 20.4), (-50.35, -49.65), BLK)
        bx(p, (x - 0.9, x + 0.9), (18.7, 19.9), (-50.4, -49.6), DRK2)
        zc(p, x, 19.1, -49.7, -48.7, 0.8, DRK2, 6, top_r=0.7)
        zc(p, x, 19.1, -48.7, -48.45, 0.6, c, 6)


# 3. MerchStand
def build_MerchStand(p):
    # stock boxes behind
    bx(p, (-66.5, -63.5), (0, 1.8), (43.55, 44.6), DWOOD)
    bx(p, (-65.8, -63.8), (1.8, 3.0), (43.7, 44.6), WOOD)
    bx(p, (-57, -54), (0, 1.4), (43.6, 44.6), WOOD)
    # back wall + header board
    bx(p, (-67, -53), (1, 9), (44.5 - 0.6, 44.5), DRK)
    bx(p, (-66, -54), (8.2, 8.5), (44.5, 44.62), PNK, 0.0)
    # rail + shirts
    bx(p, (-66, -54), (6.7, 6.9), (44.7, 44.9), MET)
    for x, c in ((-63.5, CYN), (-60, YEL), (-56.5, PUR)):
        bx(p, (x - 1.0, x + 1.0), (3.9, 6.5), (44.9, 45.1), c)
        bx(p, (x - 1.8, x - 1.0), (5.4, 6.5), (44.9, 45.1), dk.shade(c, 0.85), rot=(0, 0, 0))
        bx(p, (x + 1.0, x + 1.8), (5.4, 6.5), (44.9, 45.1), dk.shade(c, 0.85))
        bx(p, (x - 0.4, x + 0.4), (6.3, 6.5), (45.1, 45.15), DRK2)
    # counter
    bx(p, (-67, -53), (0, 3.4), (46.5, 49.5), DWOOD)
    for k in (0, 1, 5, 6):
        bx(p, (-66.4 + k * 2.0, -65.0 + k * 2.0), (0.4, 3.0), (49.5, 49.6), WOOD, 0.05)
    bx(p, (-63.6, -56.4), (0.7, 2.9), (49.5, 49.66), BLK, 0.0)
    pix(p, "MERCH", -63.3, 1.15, 49.69, 0.23, PNK)
    bx(p, (-67.2, -52.8), (3.4, 3.6), (46.3, 49.7), BLK)
    bx(p, (-67, -53), (0.0, 0.4), (49.5, 49.6), PNK, 0.0)
    # canopy
    for k in range(6):
        c = PNK if k % 2 == 0 else WHT
        bx(p, (-67.5 + k * 2.5, -65.0 + k * 2.5), (10.4, 10.8), (43.75, 49.25), c)
    for k in range(12):
        c = PNK if (k // 2) % 2 == 0 else WHT
        bx(p, (-67.5 + k * 1.25, -66.25 + k * 1.25), (9.7, 10.4), (49.25, 49.4), c, 0.03)
    for x in (-67, -53):
        bx(p, (x - 0.4, x + 0.4), (0, 10.4), (44.6, 45.4), MET)
        bx(p, (x - 0.25, x + 0.25), (3.6, 10.4), (48.85, 49.35), GLD)
    # goods on the counter
    for z in (47.2, 48.4):
        bx(p, (-64.8, -61.2), (3.6, 3.6 + 0.4 + 0.0), (z - 0.5, z + 0.5), WHT)
    bx(p, (-64.8, -61.2), (4.0, 4.4), (46.7, 47.7), WHT)
    bx(p, (-64.6, -61.4), (4.4, 4.8), (46.8, 47.6), CYN)
    bx(p, (-58.8, -55.2), (3.6, 4.0), (46.7, 47.9), RED)
    bx(p, (-58.6, -55.4), (4.0, 4.4), (46.8, 47.8), WHT)
    bx(p, (-58.6, -55.4), (4.4, 4.8), (46.8, 47.8), PUR)
    # register
    bx(p, (-54.6, -53.4), (3.6, 4.6), (47.0, 48.0), DRK2)
    bx(p, (-54.5, -53.5), (4.6, 5.3), (47.0, 47.1), CYN, 0.0)


# 4. Speakers: two stacks
def speaker_stack(p, cx):
    z0, z1 = -35.0, -29.0
    bx(p, (cx - 3.0, cx + 3.0), (0, 0.5), (z0, z1), DRK2)
    bx(p, (cx - 2.82, cx + 2.82), (0.5, 6.0), (z0, z1), BLK)               # sub
    bx(p, (cx - 2.6, cx + 2.6), (6.0, 11.0), (z0 + 0.3, z1 - 0.3), DRK)    # mid
    bx(p, (cx - 2.3, cx + 2.3), (11.0, 13.4), (z0 + 0.6, z1 - 0.6), BLK)   # top
    for sx in (-2.82, 2.82):   # metal corners
        bx(p, (cx + sx - 0.18, cx + sx + 0.18), (0.5, 6.0), (z1 - 0.1, z1 + 0.05), DMET, 0.02)
    woofer(p, cx, 3.1, z1 - 0.1, 2.0, verts=12)
    bx(p, (cx - 1.8, cx + 1.8), (0.9, 1.3), (z1, z1 + 0.15), DRK2, 0.02)
    for sx in (-1.35, 1.35):
        woofer(p, cx + sx, 7.6, z1 - 0.3, 1.0, verts=8)
    bx(p, (cx - 2.1, cx + 2.1), (9.5, 10.7), (z1 - 0.3, z1 - 0.05), DMET)    # horn frame
    bx(p, (cx - 1.8, cx + 1.8), (9.75, 10.45), (z1 - 0.05, z1 + 0.1), DRK2)
    woofer(p, cx - 1.15, 12.2, z1 - 0.6, 0.7, verts=8, cap=False)
    woofer(p, cx + 1.15, 12.2, z1 - 0.6, 0.7, verts=8, cap=False)
    bx(p, (cx - 0.35, cx + 0.35), (11.7, 12.7), (z1 - 0.6, z1 - 0.35), PNK)
    bx(p, (cx - 2.5, cx + 2.5), (1.0, 1.25), (z1 + 0.15, z1 + 0.3), PNK, 0.0)   # LED strip, goes to -28.7
    bx(p, (cx - 2.2, cx + 2.2), (5.6, 5.8), (z1, z1 + 0.1), PNK, 0.0)
    for sy in (3.4, 8.2):
        bx(p, (cx - 3.0, cx - 2.82), (sy - 0.5, sy + 0.5), (-32.6, -31.4), MET, 0.02)
        bx(p, (cx + 2.82, cx + 3.0), (sy - 0.5, sy + 0.5), (-32.6, -31.4), MET, 0.02)


def build_Speakers(p):
    speaker_stack(p, 18)
    speaker_stack(p, 83)


# 5. Booth
def build_Booth(p):
    # side monitors
    for x in (-32.5, -17.5):
        bx(p, (x - 1.25, x + 1.25), (0, 4.0), (6.75, 9.25), BLK)
        woofer(p, x, 1.6, 9.25, 0.75, verts=8, cap=False)
        woofer(p, x, 3.1, 9.25, 0.45, verts=6, cap=False)
    # backdrop with waveform
    bx(p, (-32, -18), (2, 10), (1.2, 1.8), DRK)
    bx(p, (-31.3, -18.7), (2.6, 9.4), (1.8, 2.0), BLK)
    for k in range(13):
        h = (0.4, 0.75, 1.1, 0.6, 1.5, 0.9, 1.8, 1.0, 1.4, 0.7, 1.2, 0.5, 0.3)[k]
        c = PNK if k % 2 == 0 else CYN
        x = -30.6 + k * 0.95
        bx(p, (x, x + 0.6), (6.0 - h, 6.0 + h), (2.0, 2.1), c, 0.0)
    # desk
    bx(p, (-32, -18), (0, 3.4), (5.75, 10.25), BLK)
    bx(p, (-31.6, -18.4), (0.5, 3.0), (10.25, 10.3), DRK, 0.03)
    bx(p, (-32, -18), (0.2, 0.55), (10.25, 10.35), PNK, 0.0)
    pix(p, "DJ", -26.0, 1.0, 10.33, 0.27, WHT)
    bx(p, (-32.2, -17.8), (3.4, 3.5), (5.55, 10.45), PNK, 0.0)
    bx(p, (-32.0, -18.0), (3.5, 3.6), (5.75, 10.25), DRK2)
    # turntables
    for x in (-28.6, -21.4):
        bx(p, (x - 2.0, x + 2.0), (3.6, 3.85), (6.1, 9.9), DRK)
        vc(p, x, 3.85, 4.0, 8.0, 1.5, MET, 12)
        vc(p, x, 4.0, 4.1, 8.0, 1.35, BLK, 12)
        vc(p, x, 4.1, 4.16, 8.0, 0.45, CYN if x < -25 else PNK, 8)
        bar(p, (x + 1.55, 3.95, 9.2), (x + 0.4, 4.2, 8.3), 0.12, LMET)
        bx(p, (x + 1.35, x + 1.75), (3.85, 4.2), (9.0, 9.5), DMET)
        bx(p, (x - 1.85, x - 1.55), (3.85, 3.95), (6.4, 9.2), MET, 0.02)
    # mixer
    bx(p, (-26.4, -23.6), (3.6, 4.25), (6.1, 9.9), DRK2)
    bx(p, (-26.1, -23.9), (4.25, 4.3), (6.4, 9.6), BLK, 0.0)
    for k, c in enumerate((CYN, PNK, YEL, CYN, PNK, YEL)):
        bx(p, (-26.0 + k * 0.4, -25.75 + k * 0.4), (4.3, 4.5), (9.0, 9.25), c, 0.0)
    for k in range(3):
        bx(p, (-25.9 + k * 0.7, -25.7 + k * 0.7), (4.3, 4.45), (7.0, 8.4), MET, 0.0)
    bx(p, (-25.5, -24.5), (4.3, 4.5), (6.5, 6.8), WHT, 0.0)
    # laptop on the left monitor
    bx(p, (-33.5, -31.5), (4.0, 4.12), (7.0, 8.6), MET)
    bx(p, (-33.5, -31.5), (4.12, 5.2), (6.88, 7.0), MET)
    bx(p, (-33.3, -31.7), (4.2, 5.0), (7.0, 7.04), CYN, 0.0)
    # cup on the right monitor
    vc(p, -17.5, 4.0, 4.7, 8.0, 0.35, PNK, 8)
    # the DJ
    bx(p, (-26.0, -24.0), (0.0, 3.9), (4.3, 5.7), JEAN)
    bx(p, (-26.0, -24.0), (3.9, 6.5), (4.2, 5.8), PUR)
    bx(p, (-26.2, -23.8), (5.9, 6.5), (4.2, 5.8), DPUR)
    bar(p, (-25.8, 6.1, 5.9), (-27.4, 4.6, 7.4), 0.55, PUR)
    bar(p, (-24.2, 6.1, 5.9), (-22.6, 4.6, 7.4), 0.55, PUR)
    bl(p, (-27.5, 4.45, 7.5), 0.38, SKIN, sub=1)
    bl(p, (-22.5, 4.45, 7.5), 0.38, SKIN, sub=1)
    bl(p, (-25, 7.6, 5.0), 0.85, SKIN, sub=1)
    bx(p, (-25.95, -24.05), (7.9, 8.35), (4.15, 5.85), PNK)               # cap
    bx(p, (-25.6, -24.4), (7.82, 8.0), (5.7, 6.2), PNK)                  # brim
    xc(p, -26.1, -23.9, 8.0, 5.0, 0.12, BLK, 6)                            # headphone band
    for x in (-26.15, -23.85):
        bx(p, (x - 0.2, x + 0.2), (7.3, 8.1), (4.6, 5.4), BLK)
    bx(p, (-25.4, -25.15), (7.2, 7.42), (5.82, 5.9), BLK, 0.0)
    bx(p, (-24.85, -24.6), (7.2, 7.42), (5.82, 5.9), BLK, 0.0)


# 6. Bar
def build_Bar(p):
    # back bar
    bx(p, (65, 83), (0, 4.2), (9.1, 10.9), DWOOD)
    bx(p, (64.8, 83.2), (4.2, 4.4), (9.1, 11.1), BLK)
    bx(p, (65, 83), (4.4, 10), (9.1, 10.1), DRK)
    bx(p, (66.6, 81.4), (5.2, 9.7), (10.1, 10.2), DCYN)
    for x0, x1, y0, y1 in ((66.4, 81.6, 9.6, 9.9), (66.4, 81.6, 5.0, 5.3)):
        bx(p, (x0, x1), (y0, y1), (10.1, 10.25), MET)
    for x in (66.4, 81.3):
        bx(p, (x, x + 0.3), (5.0, 9.9), (10.1, 10.25), MET)
    for y in (6.0, 8.4):
        bx(p, (66.0, 82.0), (y - 0.15, y + 0.15), (10.1, 11.0), WOOD)
        bx(p, (66.0, 82.0), (y - 0.3, y - 0.15), (10.1, 10.9), PNK if y < 7 else CYN, 0.0)
    cols = [CYN, PNK, YEL, RED, PUR, WHT]
    for k in range(7):
        x = 67.6 + k * 2.2
        c = cols[k % 6]
        bx(p, (x - 0.4, x + 0.4), (6.15, 7.4), (10.35, 11.0 - 0.15), c)
        bx(p, (x - 0.15, x + 0.15), (7.4, 8.0), (10.55, 10.85), c)
    for k in range(6):
        x = 68.7 + k * 2.2
        c = cols[(k + 2) % 6]
        bx(p, (x - 0.35, x + 0.35), (8.55, 9.4), (10.4, 10.95 - 0.1), c)
        bx(p, (x - 0.13, x + 0.13), (9.4, 9.9), (10.55, 10.8), c)
    # counter
    bx(p, (65.2, 82.8), (0.5, 4.0), (12.5, 15.5), WOOD)
    bx(p, (65.2, 82.8), (0, 0.5), (12.7, 15.3), BLK)
    for k in range(9):
        bx(p, (65.5 + k * 1.95, 66.9 + k * 1.95), (0.8, 3.7), (15.5, 15.6), DWOOD, 0.05)
    bx(p, (69.4, 78.6), (0.9, 3.6), (15.6, 15.66), BLK, 0.0)
    pix(p, "BAR", 70.6, 1.5, 15.7, 0.36, PNK)
    bx(p, (64.7, 83.3), (4.0, 4.3), (12.2, 15.8), BLK)
    bx(p, (64.9, 83.1), (3.8, 4.0), (15.5, 15.75), CYN, 0.0)
    xc(p, 66, 82, 0.9, 16.2, 0.18, LMET, 8)
    for x in (67, 74, 81):
        bx(p, (x - 0.1, x + 0.1), (0.7, 1.1), (15.6, 16.1), MET, 0.0)
    # taps and glasses on the counter
    for x in (71.5, 76.5):
        bx(p, (x - 0.5, x + 0.5), (4.3, 4.5), (13.4, 14.4), MET)
        vc(p, x, 4.5, 6.0, 13.9, 0.22, LMET, 8)
        bx(p, (x - 0.15, x + 0.15), (5.4, 5.7), (13.9, 14.5), PNK if x < 74 else CYN)
    for x, c in ((68.5, WHT), (79.5, CYN), (80.6, PNK)):
        vc(p, x, 4.3, 5.1, 14.3, 0.42, c, 8, top_r=0.5)
    # stools
    for x in (68, 74, 80):
        vc(p, x, 0, 0.35, 18.5, 0.95, DRK2, 10)
        vc(p, x, 0.35, 1.95, 18.5, 0.18, LMET, 6)
        vc(p, x, 1.95, 2.2, 18.5, 0.85, BLK, 10)
        vc(p, x, 2.2, 2.65, 18.5, 1.0, RED, 10, top_r=0.88)
        xc(p, x - 0.6, x + 0.6, 0.9, 18.5, 0.1, LMET, 6)


# 7. Lounge
def sofa(p, cx, col):
    dcol = dk.shade(col, 0.72)
    for sx in (-4.6, 4.6):
        for sz in (6.6, 9.4):
            bx(p, (cx + sx - 0.2, cx + sx + 0.2), (0, 0.4), (sz - 0.2, sz + 0.2), GLD, 0.0)
    bx(p, (cx - 4.7, cx + 4.7), (0.4, 1.3), (6.2, 9.8), dcol)
    bx(p, (cx - 4.7, cx + 4.7), (1.3, 4.7), (5.95, 6.85), col)
    for sx in (-2.3, 2.3):
        bx(p, (cx + sx - 2.2, cx + sx + 2.2), (1.3, 2.1), (6.85, 9.8), col)
        bx(p, (cx + sx - 2.0, cx + sx + 2.0), (2.1, 4.5), (6.85, 7.7), dk.shade(col, 1.12), rot=(0, 0, 0))
    for sx in (-5.2, 5.2):
        bx(p, (cx + sx - 0.5, cx + sx + 0.5), (0.4, 3.0), (6.0, 9.8), dcol)
        bx(p, (cx + sx - 0.55, cx + sx + 0.55), (3.0, 3.6), (6.1, 9.8), col)


def build_Lounge(p):
    # rug
    bx(p, (-84, -64), (0, 0.2), (9.5, 16.5), DRK2, 0.02)
    bx(p, (-83.4, -64.6), (0.2, 0.25), (10.1, 15.9), CYN, 0.0)
    bx(p, (-83.0, -65.0), (0.2, 0.28), (10.5, 15.5), DRK2, 0.0)
    bx(p, (-79, -69), (0.28, 0.32), (11.2, 14.8), DPNK, 0.0)
    bx(p, (-78.5, -69.5), (0.32, 0.35), (11.6, 14.4), DPUR, 0.0)
    sofa(p, -82, RED)
    sofa(p, -66, PUR)
    # pillows
    bx(p, (-85.8, -84.2), (2.1, 3.7), (7.7, 8.3), YEL, rot=(0, 0, 14))
    bx(p, (-80.4, -78.8), (2.1, 3.6), (7.7, 8.3), CYN, rot=(0, 0, -12))
    bx(p, (-69.6, -68.0), (2.1, 3.7), (7.7, 8.3), PNK, rot=(0, 0, 12))
    bx(p, (-64.0, -62.4), (2.1, 3.6), (7.7, 8.3), YEL, rot=(0, 0, -14))
    # coffee table
    vc(p, -74, 0.2, 1.4, 13, 0.7, MET, 8)
    vc(p, -74, 1.4, 1.8, 13, 2.2, DRK, 12)
    vc(p, -74, 1.8, 1.86, 13, 1.9, CYN, 12)
    vc(p, -75.0, 1.86, 2.0, 13.3, 0.55, BLK, 10)
    vc(p, -75.0, 2.0, 2.02, 13.3, 0.2, PNK, 8)
    vc(p, -72.8, 1.86, 2.5, 12.6, 0.3, WHT, 8)
    vc(p, -73.4, 1.86, 2.4, 14.0, 0.3, YEL, 8)
    # floor lamp
    vc(p, -88, 0, 0.3, 12, 0.75, DMET, 8)
    vc(p, -88, 0.3, 9.6, 12, 0.2, MET, 6)
    vc(p, -88, 9.6, 11.1, 12, 1.2, YEL, 8, top_r=0.6)
    vc(p, -88, 11.0, 11.1, 12, 0.5, DGLD, 8)


# 8. LightTruss
def build_LightTruss(p):
    for x in (11, 59):
        bx(p, (x - 1.5, x + 1.5), (0, 0.8), (29.5, 32.5), BLK)
        bx(p, (x - 1.0, x + 1.0), (0.8, 1.2), (30.0, 32.0), DMET)
        for sx in (-0.6, 0.6):
            for sz in (-0.6, 0.6):
                bx(p, (x + sx - 0.16, x + sx + 0.16), (1.2, 16.9), (31 + sz - 0.16, 31 + sz + 0.16), MET, 0.03)
        zig_xy(p, x - 0.6, x + 0.6, 1.2, 16.9, 31.6, 7, 0.13, 0.13, DMET)
        zig_zy(p, x + (0.6 if x < 35 else -0.6), 30.4, 31.6, 1.2, 16.9, 7, 0.13, DMET)
    for sy in (17.1, 17.9):
        for sz in (30.5, 31.5):
            bx(p, (9.8, 60.2), (sy - 0.15, sy + 0.15), (sz - 0.15, sz + 0.15), MET, 0.03)
    zig_xy(p, 10, 60, 17.1, 17.9, 31.5, 14, 0.13, 0.13, DMET, vertical=False)
    for x, c in ((17, PNK), (26, CYN), (35, YEL), (44, PUR), (53, PNK)):
        bx(p, (x - 0.3, x + 0.3), (16.4, 16.95), (30.7, 31.3), BLK)
        for sx in (-1.15, 1.15):
            bx(p, (x + sx - 0.12, x + sx + 0.12), (14.6, 16.6), (30.8, 31.2), BLK)
        zc(p, x, 15.5, 29.95, 31.8, 0.95, DRK2, 8, top_r=0.75)
        zc(p, x, 15.5, 31.8, 32.2, 0.78, c, 8)
        bx(p, (x - 1.15, x + 1.15), (14.75, 14.9), (30.7, 31.3), BLK, 0.0)
    for k, x in enumerate((13.5, 21.5, 30.5, 39.5, 48.5, 56.5)):
        bx(p, (x - 0.3, x + 0.3), (16.55, 16.95), (30.95, 31.55), PNK if k % 2 == 0 else CYN, 0.0)


# 9. MirrorBall
def build_MirrorBall(p):
    vc(p, 35, 0, 0.5, 44, 2.0, DRK2, 12)
    vc(p, 35, 0.5, 1.2, 44, 1.4, DMET, 10)
    vc(p, 35, 1.2, 11.8, 44, 0.5, MET, 8)
    vc(p, 35, 11.0, 11.6, 44, 0.9, DMET, 8)
    o = bl(p, (35, 15.5, 44), 4.0, (225, 230, 240), sub=3, jit=0.0)
    facets(o, [(235, 238, 248)] * 4 + [(255, 255, 255)] * 2 + [(190, 196, 214)] * 3 + [(130, 140, 165)] * 2 + [(120, 220, 255)] * 2 + [(255, 150, 210)] * 2 + [(255, 230, 120)])
    vc(p, 35, 19.2, 19.75, 44, 0.45, GLD, 8)
    star4(p, (35, 15.5, 48.22), 'z', 1.5, WHT)
    star4(p, (39.22, 15.5, 44), 'x', 1.5, CYN)
    star4(p, (30.78, 15.5, 44), '-x', 1.5, PNK)


# 10. VipRope
def build_VipRope(p):
    bx(p, (-88, -64), (0, 0.2), (31, 41), RED, 0.02)
    for x0, x1, z0, z1 in ((-87.5, -64.5, 31.5, 31.9), (-87.5, -64.5, 40.1, 40.5)):
        bx(p, (x0, x1), (0.2, 0.26), (z0, z1), GLD, 0.0)
    for x0, x1 in ((-87.5, -87.1), (-64.9, -64.5)):
        bx(p, (x0, x1), (0.2, 0.26), (31.5, 40.5), GLD, 0.0)
    pix(p, "VIP", -81.4, 0.27, 38.6, 0.78, GLD, plane='xz')
    for x in (-88, -82, -76, -70, -64):
        vc(p, x, 0, 0.25, 30, 0.4, DGLD, 10)
        vc(p, x, 0.25, 2.65, 30, 0.14, GLD, 8)
        bl(p, (x, 2.62, 30), 0.36, GLD, sub=1)
        vc(p, x, 0.25, 0.7, 30, 0.24, DGLD, 8, top_r=0.14)
    for xa, xb in ((-88, -82), (-82, -76), (-70, -64)):
        n = 4
        pts = []
        for k in range(n + 1):
            t = k / n
            pts.append((xa + (xb - xa) * t, 2.35 - 0.55 * math.sin(math.pi * t), 30))
        for k in range(n):
            bar(p, pts[k], pts[k + 1], 0.24, RED, 0.03)


# 11. FogMachine
def build_FogMachine(p):
    for sx in (82, 86):
        for sz in (-9.5, -6.5):
            bx(p, (sx - 0.5, sx + 0.5), (0, 0.3), (sz - 0.5, sz + 0.5), BLK, 0.0)
    bx(p, (81, 87), (0.3, 3.0), (-10, -6), DRK)
    bx(p, (80.9, 87.1), (3.0, 3.4), (-10.1, -5.9), MET)
    for k in range(4):
        bx(p, (81.5, 83.5), (1.0 + k * 0.45, 1.25 + k * 0.45), (-6.0, -5.92), BLK, 0.0)
    bx(p, (85.0, 86.6), (1.0, 2.5), (-6.0, -5.9), DRK2)
    bx(p, (85.2, 85.6), (2.0, 2.3), (-5.9, -5.82), RED, 0.0)
    bx(p, (85.9, 86.3), (2.0, 2.3), (-5.9, -5.82), CYN, 0.0)
    vc(p, 85.6, 1.3, 1.6, -5.85, 0.22, MET, 6)
    bx(p, (82.0, 82.4), (3.4, 4.4), (-8.5, -7.5), BLK)
    bx(p, (85.6, 86.0), (3.4, 4.4), (-8.5, -7.5), BLK)
    bx(p, (82.0, 86.0), (4.2, 4.5), (-8.5, -7.5), DRK2)
    zc(p, 84, 1.8, -6.2, -4.8, 0.95, BLK, 10, top_r=0.6)
    zc(p, 84, 1.8, -5.0, -4.8, 1.05, MET, 10)
    bx(p, (81.0, 87.0), (0.45, 0.8), (-6.0, -5.94), PNK, 0.0)
    puffs = [((84.0, 2.2, -3.0), 1.8), ((86.0, 2.8, 0.0), 2.5), ((82.0, 2.4, 1.5), 2.0), ((88.0, 1.85, 4.0), 2.2),
             ((84.0, 2.6, 5.0), 1.7), ((83.0, 1.2, -1.5), 1.2), ((88.2, 1.8, 0.8), 1.6),
             ((84.0, 4.3, -0.6), 0.9)]
    for k, (c, r) in enumerate(puffs):
        col = [(255, 255, 255), (255, 226, 244), (226, 244, 255), (244, 236, 255)][k % 4]
        bl(p, c, r, col, scale=(1, 0.9, 1), sub=2, jit=0.05)
        for k2, (dx, dy, dz, f) in enumerate(((0.55, 0.7, 0.25, 0.5), (-0.5, 0.65, -0.3, 0.45), (0.1, 0.2, 0.85, 0.5))):
            sx, sy, sz, sr = c[0] + dx * r, c[1] + dy * r, c[2] + dz * r, f * r
            if sy + sr * 0.9 <= 5.25 and sx + sr <= 90.1 and sz + sr <= 6.6 and sx - sr >= 80.0:
                bl(p, (sx, sy, sz), sr, col, scale=(1, 0.9, 1), sub=1, jit=0.05)


# 12. Stairs
def build_Stairs(p):
    steps = (-20, -22, -24)
    for k, z in enumerate(steps):
        h = 0.8 * (k + 1)
        bx(p, (46.0, 54.0), (0, h - 0.12), (z - 1, z + 0.9), DRK)
        bx(p, (46.0, 54.0), (h - 0.12, h), (z - 1, z + 0.9), MET, 0.0)
        for j in range(3):   # anti-slip strips
            bx(p, (46.4, 53.6), (h, h + 0.03), (z - 0.7 + j * 0.45, z - 0.5 + j * 0.45), DMET, 0.0)
        bx(p, (46.2, 53.8), (h - 0.6, h - 0.3), (z + 0.9, z + 1.0), CYN if k != 1 else PNK, 0.0)   # riser LED
        bx(p, (46.0, 54.0), (0, h - 0.6), (z + 0.9, z + 1.0), BLK, 0.0)
        bx(p, (46.0, 54.0), (h - 0.3, h), (z + 0.9, z + 1.0), BLK, 0.0)
    # side cheeks
    for sx in (45.4, 54.0):
        bx(p, (sx, sx + 0.6), (0, 0.8), (-21, -19), BLK)
        bx(p, (sx, sx + 0.6), (0, 1.6), (-23, -21), BLK)
        bx(p, (sx, sx + 0.6), (0, 2.4), (-25, -23), BLK)
    # gold rails following the steps
    for sx in (45.7, 54.3):
        pts = [(-19.3, 1.4), (-20.6, 1.6), (-22.6, 1.95), (-24.7, 2.2)]
        for a, b in zip(pts, pts[1:]):
            bar(p, (sx, a[1], a[0]), (sx, b[1], b[0]), 0.3, GLD, 0.02)
        for zz, hh in ((-19.3, 1.4), (-21.6, 1.8), (-24.7, 2.2)):
            bx(p, (sx - 0.15, sx + 0.15), (0.2, hh), (zz - 0.15, zz + 0.15), GLD, 0.02)
        bl(p, (sx, 1.4, -19.3), 0.26, GLD, sub=1)


# 13. Drums (kit facing the road; drummer behind, on the -z side)
def drum(p, cx, y0, y1, cz, r, shell, head=WHT, verts=10, rim=DMET):
    vc(p, cx, y0, y1, cz, r, shell, verts)
    vc(p, cx, y1 - 0.02, y1 + 0.1, cz, r * 1.02, rim, verts)
    vc(p, cx, y1 + 0.1, y1 + 0.14, cz, r * 0.92, head, verts)
    vc(p, cx, y0 - 0.0, y0 + 0.1, cz, r * 1.02, rim, verts)


def cymbal(p, cx, y, cz, r, stand_y0, tilt=8):
    vc(p, cx, stand_y0, y, cz, 0.13, MET, 6)
    dk.cyl(p, (cx, y + 0.12, cz), r, 0.16, GLD, axis='y', verts=10, top_radius=r, rot=(tilt, 0, tilt), jitter=0.04)
    vc(p, cx, y + 0.08, y + 0.34, cz, 0.28, DGLD, 8)


def build_Drums(p):
    bx(p, (1, 15), (0, 0.4), (-49, -39), DRK)
    bx(p, (1, 15), (0.4, 0.45), (-49, -39), BLK, 0.0)
    bx(p, (2.5, 13.5), (0.45, 0.5), (-48, -40), DRED, 0.0)
    for x0, x1 in ((1, 1.4), (14.6, 15)):
        bx(p, (x0, x1), (0.4, 0.5), (-49, -39), GLD, 0.0)
    for z0 in (-49, -39.4):
        bx(p, (1, 15), (0.4, 0.5), (z0, z0 + 0.4), GLD, 0.0)
    # bass drum facing +z
    zc(p, 8, 2.9, -43.4, -40.4, 2.2, RED, 12)
    zc(p, 8, 2.9, -40.4, -40.25, 2.3, DMET, 12)
    zc(p, 8, 2.9, -40.25, -40.2, 2.0, WHT, 12)
    zc(p, 8, 2.9, -40.2, -40.15, 1.2, PNK, 10)
    pix(p, "DJ", 6.15, 2.2, -40.1, 0.25, BLK)
    for sx in (-2.0, 2.0):
        bx(p, (8 + sx - 0.12, 8 + sx + 0.12), (0.4, 1.0), (-40.7, -40.2), MET, 0.0)
    # rack toms on the bass drum
    drum(p, 6, 5.0, 6.0, -42.0, 1.0, RED, verts=8)
    drum(p, 10, 5.0, 6.0, -42.0, 1.0, RED, verts=8)
    bx(p, (7.6, 8.4), (5.1, 5.5), (-42.25, -41.75), MET, 0.0)
    bx(p, (7.8, 8.2), (4.9, 5.2), (-42.2, -41.8), DMET, 0.0)
    # snare and floor tom
    drum(p, 4.2, 3.3, 4.0, -43.6, 1.3, WHT, head=WHT, verts=10)
    vc(p, 4.2, 0.4, 3.3, -43.6, 0.12, MET, 6)
    drum(p, 12.0, 1.6, 3.8, -43.2, 1.3, RED, verts=10)
    for a in (0, 120, 240):
        ax = 12.0 + 1.2 * math.cos(math.radians(a))
        az = -43.2 + 1.2 * math.sin(math.radians(a))
        vc(p, ax, 0.4, 1.6, az, 0.1, MET, 6)
    # hi-hat and crashes
    cymbal(p, 2.0, 5.2, -45.0, 1.45, 0.4, tilt=0)
    vc(p, 2.0, 4.5, 4.7, -45.0, 1.4, GLD, 12)
    cymbal(p, 12.9, 6.2, -46.4, 1.6, 0.4, tilt=7)
    cymbal(p, 5.0, 6.2, -46.9, 1.6, 0.4, tilt=-7)
    # stool
    vc(p, 8, 0.4, 1.8, -46.6, 0.18, MET, 6)
    vc(p, 8, 1.8, 2.25, -46.6, 0.95, BLK, 12)
    vc(p, 8, 2.25, 2.4, -46.6, 0.8, RED, 12)
    for a in (0, 120, 240):
        bx(p, (8 + 0.7 * math.cos(math.radians(a)) - 0.12, 8 + 0.7 * math.cos(math.radians(a)) + 0.12), (0.4, 0.55),
           (-46.6 + 0.7 * math.sin(math.radians(a)) - 0.12, -46.6 + 0.7 * math.sin(math.radians(a)) + 0.12), MET, 0.0)


# 14. FoodTruck (cab at +x, serving window to the road)
def build_FoodTruck(p):
    # chassis, cargo box, roof
    bx(p, (72, 88), (0.9, 3.4), (41.2, 48.8), DRK)
    bx(p, (72.5, 85.5), (3.4, 6.5), (41, 49), YEL)
    bx(p, (72.5, 85.5), (6.5, 6.68), (41, 49), WHT)
    for z0, c in ((41.5, PNK), (44.0, CYN), (46.6, PNK)):
        bx(p, (72.5, 85.5), (6.68, 6.72), (z0, z0 + 0.5), c, 0.0)
    bx(p, (72.5, 85.5), (3.4, 3.75), (49.0, 49.05), PNK, 0.0)
    for x in (76.5, 81.5):    # roof vents
        bx(p, (x - 1.2, x + 1.2), (6.72, 7.3), (42.2, 44.4), DRK2)
        bx(p, (x - 0.9, x + 0.9), (7.25, 7.3), (42.5, 44.1), MET, 0.0)
    # roof sign
    bx(p, (73.4, 83.6), (6.68, 7.8), (47.7, 48.1), DRK2)
    bx(p, (73.3, 83.7), (7.7, 7.8), (47.65, 48.15), CYN, 0.0)
    bx(p, (73.3, 83.7), (6.68, 6.78), (47.65, 48.15), CYN, 0.0)
    pix(p, "SNACKS", 74.3, 6.9, 48.14, 0.125, PNK)
    # cab
    bx(p, (85.5, 88.85), (1.2, 3.8), (41.3, 48.7), YEL)
    bx(p, (85.5, 87.4), (3.8, 6.0), (41.5, 48.5), YEL)
    bx(p, (85.4, 87.5), (5.9, 6.1), (41.4, 48.6), WHT)
    bx(p, (87.5, 87.62), (3.9, 5.9), (42.0, 48.0), CYN, 0.0, rot=(0, 0, 18))
    for z in (41.45, 48.55):
        bx(p, (85.9, 87.1), (4.1, 5.7), (z - 0.06, z + 0.06), CYN, 0.0)
    bx(p, (88.6, 89.0), (1.0, 1.6), (41.3, 48.7), LMET)
    for z in (42.2, 47.8):
        bx(p, (88.85, 89.0), (2.5, 3.1), (z - 0.4, z + 0.4), WHT, 0.0)
    bx(p, (88.85, 89.0), (1.7, 2.4), (43.4, 46.6), DRK2, 0.0)
    for k in range(3):
        bx(p, (88.85, 89.0), (1.8 + k * 0.22, 1.9 + k * 0.22), (43.6, 46.4), MET, 0.0)
    # serving window (+z side)
    bx(p, (73.6, 83.0), (4.2, 6.2), (49.0, 49.1), CYN)
    bx(p, (73.9, 82.7), (4.5, 5.9), (49.1, 49.16), BLK, 0.0)
    pix(p, "OPEN", 76.9, 4.85, 49.2, 0.14, PNK)
    bx(p, (73.5, 83.1), (3.75, 4.1), (49.0, 49.9), LMET)
    bx(p, (74.2, 75.8), (4.1, 4.9), (49.3, 49.8), WHT, 0.03)
    bx(p, (79.0, 80.4), (4.1, 4.6), (49.3, 49.8), RED, 0.03)
    bx(p, (80.6, 81.6), (4.1, 4.5), (49.4, 49.7), YEL, 0.03)
    bx(p, (76.4, 77.6), (4.1, 4.4), (49.4, 49.7), PNK, 0.03)
    # burger board on the side
    bx(p, (83.4, 85.3), (3.9, 6.2), (49.0, 49.1), DRK2)
    bx(p, (83.6, 85.1), (4.2, 4.55), (49.1, 49.25), DGLD, 0.03)
    bx(p, (83.6, 85.1), (4.55, 4.8), (49.1, 49.27), RED, 0.03)
    bx(p, (83.6, 85.1), (4.8, 5.0), (49.1, 49.27), YEL, 0.03)
    bx(p, (83.6, 85.1), (5.0, 5.3), (49.1, 49.28), DWOOD, 0.03)
    bx(p, (83.7, 85.0), (5.3, 5.8), (49.1, 49.24), GLD, 0.03)
    for x in (84.0, 84.35, 84.7):
        bx(p, (x - 0.05, x + 0.05), (5.45, 5.6), (49.24, 49.28), WHT, 0.0)
    # slanted awning with valance
    for k in range(8):
        c = PNK if k % 2 == 0 else WHT
        x0 = 73.0 + k * 1.25
        dk.box(p, (x0 + 0.625, 6.15, 50.45), (1.25, 0.15, 2.9), c, rot=(13.5, 0, 0), jitter=0.03)
        bx(p, (x0, x0 + 1.25), (5.35, 5.85), (51.78, 51.9), c, 0.03)
    # wheels
    for x in (74, 86):
        zc(p, x, 1.4, 41.0, 41.8, 1.5, BLK, 12)
        zc(p, x, 1.4, 48.2, 49.0, 1.5, BLK, 12)
        zc(p, x, 1.4, 49.0, 49.06, 0.8, LMET, 8)
    bx(p, (84.2, 87.8), (2.9, 3.0), (48.7, 48.74), DRK2, 0.0)


# 15. GoldHammer
def build_GoldHammer(p):
    bx(p, (-77.5, -62.5), (0, 2.0), (-57.5, -42.5), BLK)
    bx(p, (-77.5, -62.5), (1.7, 2.0), (-42.9, -42.5), DGLD, 0.02)
    bx(p, (-75.0, -65.0), (2.0, 4.0), (-55.0, -45.0), DMET)
    bx(p, (-75.2, -64.8), (3.6, 4.0), (-55.2, -44.8), MET)
    bx(p, (-75.2, -64.8), (2.0, 2.3), (-55.2, -44.8), DGLD)
    bx(p, (-73.0, -67.0), (4.0, 4.5), (-53.0, -47.0), DGLD)
    # plaque on the base
    bx(p, (-74, -66), (0.4, 1.7), (-42.62, -42.5), DRK2)
    # corner lamps
    for (x, z), c in zip(((-76, -44), (-64, -44), (-76, -56), (-64, -56)), (PNK, CYN, PUR, YEL)):
        vc(p, x, 2.0, 2.8, z, 0.5, MET, 8)
        bl(p, (x, 3.4, z), 0.95, c, sub=1)
    # handle
    vc(p, -70, 4.5, 18.4, -50, 0.9, WOOD, 8)
    for y in (6.0, 7.2, 8.4, 9.6):
        vc(p, -70, y, y + 0.5, -50, 0.98, RED, 8)
    vc(p, -70, 4.5, 5.2, -50, 1.25, DGLD, 8)
    vc(p, -70, 17.6, 18.4, -50, 1.25, DGLD, 8)
    # head
    bx(p, (-75, -73.8), (17, 22), (-52.5, -47.5), DGLD)
    bx(p, (-66.2, -65), (17, 22), (-52.5, -47.5), DGLD)
    bx(p, (-73.8, -66.2), (17.3, 21.7), (-52.2, -47.8), GLD)
    bx(p, (-73.8, -66.2), (21.7, 22), (-52.5, -47.5), DGLD)
    bx(p, (-73.8, -66.2), (17, 17.3), (-52.5, -47.5), DGLD)
    bx(p, (-73.5, -66.5), (18.0, 21.0), (-47.82, -47.7), YEL)
    pix(p, "BONK", -73.2, 18.5, -47.66, 0.3, BLK)


PARTS = [("Floor", build_Floor), ("BigStage", build_BigStage), ("MerchStand", build_MerchStand),
         ("Speakers", build_Speakers), ("Booth", build_Booth), ("Bar", build_Bar), ("Lounge", build_Lounge),
         ("LightTruss", build_LightTruss), ("MirrorBall", build_MirrorBall), ("VipRope", build_VipRope),
         ("FogMachine", build_FogMachine), ("Stairs", build_Stairs), ("Drums", build_Drums),
         ("FoodTruck", build_FoodTruck), ("GoldHammer", build_GoldHammer)]

# where the reference Shiba stands in each preview: (x, z, facing, lift) and a camera distance multiplier
MULT = {"Floor": 2.3, "BigStage": 2.4, "Speakers": 2.6, "LightTruss": 2.6, "Stairs": 2.4, "FogMachine": 2.6}
SHIBA_AT = {"Floor": (5, 52, 0, 0), "BigStage": (18, -22, 180, 0), "MerchStand": (-44, 48, 180, 0),
            "Speakers": (50, -30, 180, 0), "Booth": (-12, 9, 180, 0), "Bar": (62, 22, 180, 0),
            "Lounge": (-56, 12, 180, 0), "LightTruss": (35, 37, 180, 0), "MirrorBall": (24, 46, 180, 0),
            "VipRope": (-58, 36, 180, 0), "FogMachine": (74, -2, 180, 0), "Stairs": (40, -20, 180, 0),
            "Drums": (-6, -43, 0, 0), "FoodTruck": (66, 48, 0, 0), "GoldHammer": (-58, -48, 180, 0)}


# ---- fit to the union box of the blueprint pieces --------------------------------------------------------------------------
def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = list(q["Size"])
        o = q["Offset"]
        r = q.get("Rotation")
        if r:
            if r[2] == 90:
                s = [s[1], s[0], s[2]]
            if r[1] == 90:
                s = [s[2], s[1], s[0]]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - s[i] / 2)
            hi[i] = max(hi[i], o[i] + s[i] / 2)
    return lo, hi


def fit(part, lo, hi):
    objs = part.objs
    for o in objs:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    pts = [v.co.copy() for o in objs for v in o.data.vertices]
    bl_ = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
    bh = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
    tl, th = S(*lo), S(*hi)
    for o in objs:
        ws = [v.co for v in o.data.vertices]
        for i, nm in enumerate("xzy"):
            if min(v[i] for v in ws) < tl[i] - 0.05 or max(v[i] for v in ws) > th[i] + 0.05:
                print(f"  WARN {part.id}: {o.name} sticks out on {nm}: {min(v[i] for v in ws):.2f}..{max(v[i] for v in ws):.2f} vs {tl[i]:.2f}..{th[i]:.2f}")
    sc = [(th[i] - tl[i]) / (bh[i] - bl_[i]) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl_)
    for o in objs:
        o.data.transform(m)
    print(f"FIT {part.id}: raw size {[round(bh[0]-bl_[0],2), round(bh[2]-bl_[2],2), round(bh[1]-bl_[1],2)]} "
          f"scale stage xyz = {sc[0]:.3f} {sc[2]:.3f} {sc[1]:.3f}")


# ---- previews --------------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}})  # scene is x-mirrored (see decorkit.finish)
    bpy.context.view_layer.update()
    for o in sb:
        if o.parent is None:
            o.location.z += lift
    bpy.context.view_layer.update()
    return sb


def drop(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def flip_image(path):
    """Mirror a render left-right: the stage frame is a reflection of the Blender frame, so this is the in-game handedness."""
    import numpy as np
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[:, ::-1, :].copy()
    im.pixels.foreach_set(px.reshape(-1))
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


def snap(objs, extra, filename, az, el, mult, size, top=False):
    low, high = dk._bounds(list(objs) + list(extra))
    g = dk.ground(low, high)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 6)
    cam = dk._camera(centre, radius * mult, az, 89 if top else el)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    path = os.path.join(OUT, filename)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    pass  # meshes are already mirrored for export, so the render shows the stage frame as seen from the road
    print("RENDERED", path)


def combine(a, b, out):
    import numpy as np
    ia, ib = bpy.data.images.load(a), bpy.data.images.load(b)
    w, h = ia.size
    pa = np.empty(w * h * 4, dtype=np.float32)
    ia.pixels.foreach_get(pa)
    pb = np.empty(w * h * 4, dtype=np.float32)
    ib.pixels.foreach_get(pb)
    both = np.concatenate([pb, pa])      # image rows start at the bottom: top view below, 3/4 view above
    img = bpy.data.images.new("stage", w, h * 2, alpha=False)
    img.pixels.foreach_set(both)
    img.filepath_raw = out
    img.file_format = 'PNG'
    img.save()
    print("RENDERED", out)


def main():
    dk.start(OUT)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    built = {}
    for pid, fn in PARTS:
        if ONLY and pid not in ONLY:
            continue
        pj = dk.blueprint_part(BP, pid)
        part = dk.Part(pid)
        fn(part)
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY)
        built[pid] = meshes
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        x, z, f, lift = SHIBA_AT[pid]
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", 150, 28, MULT.get(pid, 2.5), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sh = BP["Shiba"]
    sbs = shiba_for(sh["Position"][0], sh["Position"][1], sh["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 36, 2.3, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_DJStage.png"))


main()
