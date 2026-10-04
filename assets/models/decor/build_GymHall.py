"""Final low-poly decor models for the theme GymHall (10 parts around the third Shiba).

Usage: blender --background --factory-startup --python build_GymHall.py -- <outdir>
Writes Decor_GymHall_<PartId>.fbx, preview_<PartId>.png and stage_GymHall*.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = ARGS[0] if ARGS else os.path.join(HERE, "out", "GymHall")
KEY = "GymHall"
OUT = os.path.abspath(OUT)
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_GymHall.json"))

# ---- palette (shared by all 10 parts) ------------------------------------------------------------------------------
BLK = (40, 40, 46)       # black rubber / vinyl
DGR = (60, 60, 70)       # dark steel
STL = (150, 150, 160)    # steel
LST = (190, 190, 200)    # polished steel
RED = (200, 40, 40)
DRED = (150, 30, 34)
GLD = (255, 200, 40)
DGLD = (205, 150, 30)
WHT = (240, 240, 240)
BLU = (50, 90, 160)
CON = (78, 78, 90)       # concrete
CONL = (98, 98, 112)
WOOD = (120, 80, 45)
DWOOD = (40, 30, 25)
MWOOD = (70, 55, 40)
GLS = (70, 130, 170)


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.05, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.05):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=10, jit=0.05):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.05):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit)


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.05):
    """Bar in the x-y plane from (x1,y1) to (x2,y2), thickness t, depth along z centred on z."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def letter(p, ch, x0, y0, z0, z1, w, h, t, col):
    """Block letter in the x-y plane (readable from +z), box strokes."""
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.04)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zc, x0 + c, y0 + e, t, d, col, 0.04)
    if ch == 'B':
        r(0, 0, t, h); r(0, h - t, w - t * 0.6, h); r(0, h / 2 - t / 2, w - t * 0.3, h / 2 + t / 2); r(0, 0, w - t * 0.6, t)
        r(w - t, h / 2, w, h - t * 0.5); r(w - t, t * 0.5, w, h / 2)
    elif ch == 'O':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'N':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w - t * 0.5, t * 0.5)
    elif ch == 'K':
        r(0, 0, t, h); dg(t, h / 2, w - t * 0.3, h - t * 0.4); dg(t, h / 2, w - t * 0.3, t * 0.4)
    elif ch == 'G':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t); r(w - t, t, w, h / 2); r(w / 2, h / 2 - t, w - t, h / 2)
    elif ch == 'Y':
        r(w / 2 - t / 2, 0, w / 2 + t / 2, h / 2); dg(t * 0.4, h - t * 0.4, w / 2, h / 2); dg(w - t * 0.4, h - t * 0.4, w / 2, h / 2)
    elif ch == 'M':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w / 2, h * 0.35); dg(w - t * 0.5, h - t * 0.5, w / 2, h * 0.35)


def star(p, cx, cy, z0, z1, ro, ri, col):
    pts, faces = [], []
    zc, d = (z0 + z1) / 2, (z1 - z0) / 2
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = ro if k % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), d))
    for k in range(10):
        pts.append((pts[k][0], pts[k][1], -d))
    pts += [(cx, cy, d), (cx, cy, -d)]
    for k in range(10):
        n = (k + 1) % 10
        faces += [(20, k, n), (21, 10 + n, 10 + k), (k, 10 + k, 10 + n, n)]
    return dk.poly(p, (0, 0, zc), pts, faces, col, 0.03)


def dumbbell(p, cx, cy, cz, length, hr, pr, pt, pcol, hcol=STL, verts=6, axis_x=True):
    """Hex dumbbell lying along x: handle + two plates."""
    h = length / 2
    xcyl(p, cx - h + pt, cx + h - pt, cy, cz, hr, hcol, verts=6)
    for s in (-1, 1):
        x0 = cx + s * h - (pt if s > 0 else 0)
        xcyl(p, x0, x0 + pt, cy, cz, pr, pcol, verts=verts)


def kettlebell(p, cx, y0, cz, r, col):
    dk.ball(p, (cx, y0 + r, cz), r, col, subdiv=1, jitter=0.06)
    top = y0 + r * 1.75
    bx(p, (cx - r * 0.55, cx - r * 0.55 + 0.17), (y0 + r * 1.4, top), (cz - 0.09, cz + 0.09), col, 0.04)
    bx(p, (cx + r * 0.55 - 0.17, cx + r * 0.55), (y0 + r * 1.4, top), (cz - 0.09, cz + 0.09), col, 0.04)
    bx(p, (cx - r * 0.55, cx + r * 0.55), (top - 0.17, top), (cz - 0.09, cz + 0.09), col, 0.04)


def plate(p, x0, x1, cy, cz, r, col, hub=STL, verts=10, hr=None, ring=None):
    """Weight plate along x with a hub disc (and optional embossed ring)."""
    xcyl(p, x0, x1, cy, cz, r, col, verts=verts, jit=0.07)
    e = 0.02
    if ring:
        xcyl(p, x0 - e, x1 + e, cy, cz, r * 0.78, ring, verts=verts, jit=0.04)
    xcyl(p, x0 - e * 2, x1 + e * 2, cy, cz, hr or r * 0.36, hub, verts=8, jit=0.03)


def tiled_block(p, x0, x1, y0, y1, z0, z1, xs, zs, colfn, sidecol, jit=0.05):
    """Slab with a tiled top: open box for the sides plus quads for the tiles (xs/zs = grid breakpoints)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, z1 - z0, y1 - y0), verts=bm.verts)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    dk._object(p, "Side", bm, S((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (0, 0, 0), sidecol, jit)
    groups = {}
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            groups.setdefault(colfn(i, j), []).append((xs[i], xs[i + 1], zs[j], zs[j + 1]))
    for col, quads in groups.items():
        bm = bmesh.new()
        for (a, b, c, d) in quads:
            v = [bm.verts.new((a, c, y1)), bm.verts.new((b, c, y1)), bm.verts.new((b, d, y1)), bm.verts.new((a, d, y1))]
            bm.faces.new(v)
        bm.normal_update()
        dk._object(p, "Tiles", bm, Vector((0, 0, 0)), (0, 0, 0), col, 0.07)


def grid(a, b, n):
    return [a + (b - a) * i / n for i in range(n + 1)]


# ---- 1. Floor ----------------------------------------------------------------------------------------------------------
def build_Floor(p):
    DK2 = (52, 52, 60)
    G1, G2 = (60, 60, 68), (74, 74, 84)
    R1, R2, RB = (200, 40, 40), (176, 32, 36), WHT
    DRD = (110, 28, 32)

    def checker(a, b):
        return lambda i, j: a if (i + j) % 2 == 0 else b
    # main hall slab (-86..-38, 4..46) + red mat in the middle with a white border
    tiled_block(p, -86, -38, 0, 0.3, 4, 46, grid(-86, -38, 12), grid(4, 46, 10), checker(BLK, DK2), shade3(BLK, .8))
    xs = [-80, -78.5] + grid(-78.5, -45.5, 11)[1:] + [-44]
    zs = [10, 11.5] + grid(11.5, 38.5, 9)[1:] + [40]
    nx, nz = len(xs) - 1, len(zs) - 1
    tiled_block(p, -80, -44, 0.3, 0.4, 10, 40, xs, zs,
                lambda i, j: RB if i in (0, nx - 1) or j in (0, nz - 1) else (R1 if (i + j) % 2 == 0 else R2), shade3(R1, .8))
    # road-side slab with a smaller red mat
    tiled_block(p, 15, 45, 0, 0.3, 37, 51, grid(15, 45, 10), grid(37, 51, 5), checker(BLK, DK2), shade3(BLK, .8))
    tiled_block(p, 20, 40, 0.3, 0.4, 40, 48, grid(20, 40, 8), grid(40, 48, 4),
                lambda i, j: RB if i in (0, 7) or j in (0, 3) else (R1 if (i + j) % 2 == 0 else R2), shade3(R1, .8))
    # ring slab and the slab under the bags (split so they do not overlap)
    tiled_block(p, 44, 72, 0, 0.3, -8, 20, grid(44, 72, 7), grid(-8, 20, 7),
                lambda i, j: DRD if i in (0, 6) or j in (0, 6) else (BLK if (i + j) % 2 == 0 else DK2), shade3(BLK, .8))
    tiled_block(p, 22, 44, 0, 0.3, -28, -4, grid(22, 44, 6), grid(-28, -4, 6), checker(BLK, DK2), shade3(BLK, .8))
    tiled_block(p, 44, 50, 0, 0.3, -28, -8, grid(44, 50, 2), grid(-28, -8, 5), checker(BLK, DK2), shade3(BLK, .8))
    # bar slab (gray, with a lighter border row)
    xs = grid(-77, -47, 6)
    zs = grid(-46, -18, 7)
    tiled_block(p, -77, -47, 0, 0.3, -46, -18, xs, zs,
                lambda i, j: STL if i in (0, 5) or j in (0, 6) else (G1 if (i + j) % 2 == 0 else G2), shade3(G1, .8))


def shade3(c, f):
    return tuple(int(v * f) for v in c)


# ---- 2. Hall -------------------------------------------------------------------------------------------------------------
def build_Hall(p):
    walls = [(-86, -84.5, 4, 46), (-86, -69, 44.5, 46), (-55, -38, 44.5, 46), (-86, -69, 4, 5.5), (-55, -38, 4, 5.5),
             (-39.5, -38, 4, 18), (-39.5, -38, 32, 46)]
    for a, b, c, d in walls:
        bx(p, (a, b), (0, 12), (c, d), CON, 0.07)
    BASE = (56, 56, 68)
    bx(p, (-86.2, -84.5), (0, 1.2), (3.8, 46.2), BASE)
    bx(p, (-86, -69), (0, 1.2), (46, 46.2), BASE); bx(p, (-55, -38), (0, 1.2), (46, 46.2), BASE)
    bx(p, (-86, -69), (0, 1.2), (3.8, 4), BASE); bx(p, (-55, -38), (0, 1.2), (3.8, 4), BASE)
    bx(p, (-38, -37.8), (0, 1.2), (4, 18), BASE); bx(p, (-38, -37.8), (0, 1.2), (32, 46), BASE)
    # red eave band under the roof on the west, east and back sides
    bx(p, (-86.3, -84.5), (11.3, 12), (3.7, 46.3), RED, 0.03)
    bx(p, (-39.5, -37.7), (11.3, 12), (3.7, 18), RED, 0.03); bx(p, (-39.5, -37.7), (11.3, 12), (32, 46.3), RED, 0.03)
    bx(p, (-86, -69), (11.3, 12), (3.7, 5.5), RED, 0.03); bx(p, (-55, -38), (11.3, 12), (3.7, 5.5), RED, 0.03)
    # pilasters (stage frame: west wall outward = -x, front = +z, east = +x)
    for z in (5, 14.3, 25, 35.7, 45):
        bx(p, (-86.5, -85.8), (0, 11.3), (z - 0.6, z + 0.6), CONL)
    for x in (-83.5, -76.5, -48, -41):
        bx(p, (x - 0.6, x + 0.6), (0, 12), (46, 46.5), CONL)
    for z in (6.5, 12.5, 37.5, 43.5):
        bx(p, (-38, -37.5), (0, 11.3), (z - 0.6, z + 0.6), CONL)
    # red door posts on both sides of the two doorways
    for x0, x1 in ((-69.8, -69), (-55, -54.2)):
        bx(p, (x0, x1), (0, 12), (46, 46.5), RED)
        bx(p, (x0, x1), (0, 12), (3.5, 4), RED)
    bx(p, (-38, -37.5), (0, 12), (17.2, 18), RED); bx(p, (-38, -37.5), (0, 12), (32, 32.8), RED)
    # clerestory windows (west + front only): frame in Body, glass in its own mesh
    glass = []

    def win(axis, face, d, c, ln, y0=6.9, y1=10.1):
        if axis == 'x':   # wall normal along x
            bx(p, sorted((face, face + d * 0.22)), (y0, y1), (c - ln / 2 - 0.3, c + ln / 2 + 0.3), DGR)
            glass.append(bx(p, sorted((face, face + d * 0.3)), (y0 + 0.3, y1 - 0.3), (c - ln / 2, c + ln / 2), GLS, 0.04))
        else:
            bx(p, (c - ln / 2 - 0.3, c + ln / 2 + 0.3), (y0, y1), sorted((face, face + d * 0.22)), DGR)
            glass.append(bx(p, (c - ln / 2, c + ln / 2), (y0 + 0.3, y1 - 0.3), sorted((face, face + d * 0.3)), GLS, 0.04))
    for c in (9.7, 19.7, 30.3, 40.3):
        win('x', -86.2, -1, c, 5)
    for c in (-79.8, -72.8, -51.5, -44.5):
        win('z', 46.2, 1, c, 4.2, 4.2, 7.6)
    # roof: steel deck, parapet, standing-seam ribs, red centre stripe, skylights
    roof = []
    roof.append(bx(p, (-87, -37), (12, 13), (3, 47), (90, 90, 100), 0.05))
    roof.append(bx(p, (-87, -37), (13, 13.4), (3, 3.5), (70, 70, 82)))
    roof.append(bx(p, (-87, -37), (13, 13.4), (46.5, 47), (70, 70, 82)))
    roof.append(bx(p, (-87, -86.5), (13, 13.4), (3.5, 46.5), (70, 70, 82)))
    roof.append(bx(p, (-37.5, -37), (13, 13.4), (3.5, 46.5), (70, 70, 82)))
    roof.append(bx(p, (-86.5, -37.5), (13, 13.4), (22, 28), RED, 0.03))
    for z in (5.5, 8, 18.2, 20.4, 29.6, 31.8, 42, 44.5):
        roof.append(bx(p, (-86.5, -37.5), (13, 13.12), (z - 0.2, z + 0.2), (118, 118, 130), 0.04))
    for zc in (13, 37):
        for xc in (-77, -62, -47):
            roof.append(bx(p, (xc - 3.8, xc + 3.8), (13, 13.4), (zc - 1.8, zc + 1.8), GLS, 0.05))
    # red fascia banner over the front, with a white pinstripe, GYM letters and two dumbbell badges
    bx(p, (-86, -38), (8.5, 11), (45.95, 46.45), RED, 0.04)
    bx(p, (-86, -38), (8.5, 8.7), (46.4, 46.5), WHT, 0.02); bx(p, (-86, -38), (10.8, 11), (46.4, 46.5), WHT, 0.02)
    for ch, x0 in (('G', -64.75), ('Y', -62.75), ('M', -60.75)):
        letter(p, ch, x0, 8.8, 46.45, 46.75, 1.5, 1.9, 0.45, WHT)
    for bxc in (-78, -46):
        bx(p, (bxc - 1.3, bxc + 1.3), (9.65, 9.85), (46.45, 46.65), WHT, 0.02)
        for s in (-1, 1):
            bx(p, (bxc + s * 1.3 - 0.2, bxc + s * 1.3 + 0.2), (9.05, 10.45), (46.45, 46.65), WHT, 0.02)
            bx(p, (bxc + s * 0.8 - 0.15, bxc + s * 0.8 + 0.15), (9.3, 10.2), (46.45, 46.65), WHT, 0.02)
    # inside: white beams with hanging lamps
    for zc in (15, 35):
        bx(p, (-77, -47), (10.5, 11), (zc - 0.5, zc + 0.5), WHT, 0.03)
        for xc in (-72, -62, -52):
            bx(p, (xc - 1, xc + 1), (10.0, 10.5), (zc - 0.4, zc + 0.4), (255, 240, 200), 0.02)
    return {"Roof": roof, "Glass": glass}


# ---- 3. Sign ---------------------------------------------------------------------------------------------------------------
def build_Sign(p):
    for x in (60, 80):
        bx(p, (x - 0.5, x + 0.5), (0.3, 8), (37.5, 38.5), DGR)
        bx(p, (x - 1, x + 1), (0, 0.3), (37.35, 38.65), STL)
        for y in (2.2, 5.0):
            bx(p, (x - 0.65, x + 0.65), (y, y + 0.35), (37.35, 38.65), STL)
    # board with gold frame
    bx(p, (58, 82), (6, 15), (37.5, 38.5), BLK, 0.03)
    bx(p, (57.5, 82.5), (15, 15.8), (37.3, 38.7), GLD)
    bx(p, (57.5, 82.5), (5.4, 6.2), (37.3, 38.7), GLD)
    for x0, x1 in ((57.5, 58.4), (81.6, 82.5)):
        bx(p, (x0, x1), (6.2, 15), (37.3, 38.7), DGLD)
    for x in (58.0, 82.0):
        for y in (6.0, 15.0):
            bx(p, (x - 0.25, x + 0.25), (y - 0.25, y + 0.25), (38.7, 38.85), LST)
    bx(p, (59.2, 80.8), (7.0, 7.25), (38.5, 38.62), DGLD)      # thin gold lines above/below the letters
    bx(p, (59.2, 80.8), (13.75, 14.0), (38.5, 38.62), DGLD)
    for ch, xc in zip("BONK", (62.5, 67.5, 72.5, 77.5)):
        letter(p, ch, xc - 1.8, 7.5, 38.62, 39.05, 3.6, 6.0, 1.0, RED)


# ---- 4. Benches ------------------------------------------------------------------------------------------------------------
def build_Benches(p):
    for cx, acc in ((-78, GLD), (-68, RED)):
        # bench: feet, spine, padded seat
        for z0, z1 in ((33.5, 34.4), (37.6, 38.5)):
            bx(p, (cx - 1.2, cx + 1.2), (0.3, 0.55), (z0, z1), DGR)
        bx(p, (cx - 0.35, cx + 0.35), (0.55, 0.9), (33.9, 38.1), STL)
        bx(p, (cx - 1.0, cx + 1.0), (0.9, 1.3), (33.5, 38.5), BLK, 0.07)
        bx(p, (cx - 0.85, cx + 0.85), (1.3, 1.5), (33.65, 38.35), (52, 52, 60), 0.07)
        bx(p, (cx - 1.02, cx + 1.02), (0.85, 0.95), (33.5, 38.5), RED, 0.03)    # red piping
        # rack uprights with a hook cradle each
        for s in (-1, 1):
            ux = cx + s * 1.6
            bx(p, (ux - 0.2, ux + 0.2), (0.3, 3.3), (35.8, 36.2), DGR)
            bx(p, (ux - 0.35, ux + 0.35), (0.3, 0.55), (34.2, 37.8), DGR)
            for zz in (35.45, 36.25):
                bx(p, (ux - 0.2, ux + 0.2), (3.0, 3.75), (zz, zz + 0.3), STL)
        # barbell: chrome bar, knurled grips, collars, plates
        xcyl(p, cx - 3.5, cx + 3.5, 3.4, 36, 0.2, LST, verts=8)
        for s in (-1, 1):
            xcyl(p, *sorted((cx + s * 0.5, cx + s * 1.3)), 3.4, 36, 0.24, DGR, verts=8)
            xcyl(p, *sorted((cx + s * 2.3, cx + s * 2.5)), 3.4, 36, 0.36, STL, verts=8)
            plate(p, *sorted((cx + s * 2.9, cx + s * 3.5)), 3.4, 36, 1.2, BLK, hr=0.45)
            xcyl(p, *sorted((cx + s * 2.52, cx + s * 2.9)), 3.4, 36, 0.9, acc, verts=10, jit=0.05)


# ---- 5. Racks --------------------------------------------------------------------------------------------------------------
def build_Racks(p):
    X0, X1 = -83.7, -80.7
    xc = -82.2
    bx(p, (X0, X1), (0.3, 0.7), (8, 22), DGR)
    bx(p, (X0, X1), (2.4, 2.8), (8, 22), DGR)
    bx(p, (X1 - 0.12, X1), (2.45, 2.75), (8, 22), RED, 0.03)       # red edge on the upper shelf
    bx(p, (X1 - 0.12, X1), (0.35, 0.65), (8, 22), RED, 0.03)
    # end frames (solid) with red caps, middle frame as open posts
    for z0, z1 in ((8, 8.4), (21.6, 22)):
        bx(p, (X0, X1), (0.3, 3.9), (z0, z1), DGR)
        bx(p, (X0, X1), (3.6, 3.9), (z0, z1), RED, 0.04)
    for x0, x1 in ((X0, X0 + 0.5), (X1 - 0.5, X1)):
        bx(p, (x0, x1), (0.3, 3.9), (14.8, 15.2), DGR)
    bx(p, (X0, X1), (3.6, 3.9), (14.8, 15.2), RED, 0.04)
    # top shelf: six red dumbbells that grow to the right
    rs = (0.36, 0.42, 0.48, 0.52, 0.55, 0.55)
    zs = (9.6, 11.7, 13.7, 16.3, 18.35, 20.4)
    for r, z in zip(rs, zs):
        dumbbell(p, xc, 2.8 + r, z, 2.4, 0.13, r, 0.5, RED if r < 0.5 else DRED)
    # lower shelf: kettlebells on the left half, heavy black dumbbells on the right
    for z, r, c in zip((9.6, 11.7, 13.7), (0.55, 0.6, 0.62), (GLD, BLU, GLD)):
        kettlebell(p, xc, 0.7, z, r, c)
    for z, r in zip((16.4, 18.4, 20.4), (0.6, 0.7, 0.8)):
        dumbbell(p, xc, 0.7 + r, z, 2.4, 0.15, r, 0.5, (118, 118, 130), hcol=LST)


# ---- 6. Treadmills -----------------------------------------------------------------------------------------------------------
def build_Treadmills(p):
    screens = [(70, 140, 180), (80, 170, 120), (230, 150, 50)]
    for k, tc in enumerate((-54, -48.5, -43)):
        for s in (-1, 1):   # side rails + handrails
            x0, x1 = (tc + s * 1.1, tc + s * 1.5) if s > 0 else (tc - 1.5, tc - 1.1)
            bx(p, (x0, x1), (0.3, 1.1), (7.8, 13.5), DGR)
            bx(p, (x0 + 0.05, x1 - 0.05), (2.6, 2.9), (6.9, 10.1), STL)
            bx(p, (x0 + 0.05, x1 - 0.05), (1.1, 2.6), (9.8, 10.1), STL)
        bx(p, (tc - 1.1, tc + 1.1), (0.3, 0.95), (8, 13.2), BLK, 0.04)                   # belt
        bx(p, (tc - 0.12, tc + 0.12), (0.95, 0.99), (8.3, 13.0), (80, 80, 90), 0.02)
        bx(p, (tc - 1.5, tc + 1.5), (0.3, 0.9), (13.2, 13.5), DGR)                       # rear end
        xcyl(p, tc - 1.1, tc + 1.1, 0.8, 13.0, 0.28, STL, verts=8)
        bx(p, (tc - 1.5, tc + 1.5), (0.3, 1.9), (6.5, 8.0), DGR)                         # motor hood
        bx(p, (tc - 1.3, tc + 1.3), (1.9, 2.3), (6.5, 7.6), BLK)
        bx(p, (tc - 1.0, tc + 1.0), (0.7, 1.0), (8.0, 8.1), RED, 0.03)
        for s in (-1, 1):                                                                # console posts
            bx(p, (tc + s * 1.0 - 0.17, tc + s * 1.0 + 0.17), (2.3, 3.2), (6.55, 6.9), STL)
        bx(p, (tc - 1.2, tc + 1.2), (3.1, 4.5), (6.5, 6.9), BLK, 0.03)                   # console
        bx(p, (tc - 1.0, tc + 1.0), (3.5, 4.35), (6.9, 7.05), screens[k], 0.03)          # screen
        bx(p, (tc - 1.1, tc + 1.1), (4.35, 4.5), (6.9, 7.0), DGR)
        for dx, c in ((-0.6, RED), (0, GLD), (0.6, (70, 170, 100))):
            bx(p, (tc + dx - 0.18, tc + dx + 0.18), (3.2, 3.42), (6.9, 7.05), c, 0.02)
    # a towel over one handrail
    bx(p, (-43 + 0.95, -43 + 1.45), (2.35, 3.2), (8.0, 8.6), WHT, 0.04)
    bx(p, (-43 + 0.95, -43 + 1.45), (2.35, 3.2), (8.35, 8.6), RED, 0.04)


# ---- 7. Ring -----------------------------------------------------------------------------------------------------------------
def build_Ring(p):
    X0, X1, Z0, Z1 = 48, 68, -4, 16
    bx(p, (X0, X1), (0, 0.4), (Z0, Z1), DGR)
    bx(p, (X0 + 0.3, X1 - 0.3), (0.4, 1.3), (Z0 + 0.3, Z1 - 0.3), RED, 0.06)           # apron
    for i in range(1, 8):                                                              # white apron stripes
        xx = X0 + 0.3 + (X1 - X0 - 0.6) * i / 8
        bx(p, (xx - 0.3, xx + 0.3), (0.4, 1.3), (Z1 - 0.35, Z1 - 0.25), WHT, 0.02)
        bx(p, (xx - 0.3, xx + 0.3), (0.4, 1.3), (Z0 + 0.25, Z0 + 0.35), WHT, 0.02)
    for i in range(1, 8):
        zz = Z0 + 0.3 + (Z1 - Z0 - 0.6) * i / 8
        bx(p, (X1 - 0.35, X1 - 0.25), (0.4, 1.3), (zz - 0.3, zz + 0.3), WHT, 0.02)
        bx(p, (X0 + 0.25, X0 + 0.35), (0.4, 1.3), (zz - 0.3, zz + 0.3), WHT, 0.02)
    bx(p, (X0, X1), (1.3, 1.5), (Z0, Z1), STL)                                         # deck edge
    bx(p, (X0 + 0.5, X1 - 0.5), (1.5, 1.7), (Z0 + 0.5, Z1 - 0.5), RED, 0.04)           # canvas
    vcyl(p, 58, 1.7, 1.76, 6, 3.4, WHT, verts=14, jit=0.02)
    vcyl(p, 58, 1.76, 1.82, 6, 2.6, RED, verts=14, jit=0.04)
    for s in (-1, 1):
        bx(p, (58 - 8.6, 58 + 8.6), (1.7, 1.76), (6 + s * 8.0 - 0.15, 6 + s * 8.0 + 0.15), WHT, 0.02)
        bx(p, (58 + s * 8.0 - 0.15, 58 + s * 8.0 + 0.15), (1.7, 1.76), (6 - 8.5, 6 + 8.5), WHT, 0.02)
    corners = [(48.6, -3.4, RED), (67.4, -3.4, BLU), (48.6, 15.4, BLU), (67.4, 15.4, RED)]
    for cx, cz, pc in corners:
        vcyl(p, cx, 1.7, 6.3, cz, 0.4, DGR, verts=8)
        vcyl(p, cx, 1.7, 2.1, cz, 0.6, DGR, verts=8)
        vcyl(p, cx, 6.0, 6.3, cz, 0.5, STL, verts=8)
        bx(p, (cx - 0.62, cx + 0.62), (2.9, 5.4), (cz - 0.62, cz + 0.62), pc, 0.05)       # corner pad
    for y in (3.3, 4.1, 4.9):
        for cz in (-3.4, 15.4):
            xcyl(p, 49.2, 66.8, y, cz, 0.13, WHT, verts=6, jit=0.02)
        for cx in (48.6, 67.4):
            zcyl(p, cx, y, -2.8, 14.8, 0.13, RED, verts=6, jit=0.02)
    for t in (0.33, 0.66):                                                              # rope spacers
        xx, zz = 49.2 + 17.6 * t, -3.0 + 17.8 * t
        for cz in (-3.4, 15.4):
            bx(p, (xx - 0.07, xx + 0.07), (3.3, 4.9), (cz - 0.1, cz + 0.1), WHT, 0.02)
        for cx in (48.6, 67.4):
            bx(p, (cx - 0.1, cx + 0.1), (3.3, 4.9), (zz - 0.07, zz + 0.07), WHT, 0.02)


# ---- 8. Bags -------------------------------------------------------------------------------------------------------------------
def build_Bags(p):
    # heavy bag rig
    for x in (23, 45):
        bx(p, (x - 0.4, x + 0.4), (0.3, 7), (-20.4, -19.6), DGR)
        bx(p, (x - 0.95, x + 0.95), (0, 0.3), (-20.4, -19.6), STL)
    bx(p, (22, 46), (7.0, 7.6), (-20.3, -19.7), STL)
    diag(p, 23.4, 5.7, -20, 24.9, 7.0, 0.3, 0.4, DGR)
    diag(p, 44.6, 5.7, -20, 43.1, 7.0, 0.3, 0.4, DGR)
    for x in (28, 34, 40):
        xs = x
        bx(p, (xs - 0.1, xs + 0.1), (6.3, 7.0), (-20.1, -19.9), STL)                       # chain
        vcyl(p, xs, 6.2, 6.4, -20, 1.3, DRED, verts=10, top_r=0.5)                           # cap
        vcyl(p, xs, 1.2, 6.2, -20, 1.3, RED, verts=10, jit=0.08)                             # body
        vcyl(p, xs, 1.0, 1.2, -20, 1.3, DRED, verts=10, top_r=1.3)
        vcyl(p, xs, 5.55, 5.95, -20, 1.34, BLK, verts=10, jit=0.04)                          # straps
        vcyl(p, xs, 1.4, 1.8, -20, 1.34, BLK, verts=10, jit=0.04)
        vcyl(p, xs, 3.4, 3.7, -20, 1.33, GLD, verts=10, jit=0.03)                            # gold band
    # pull-up rig
    for x in (25, 37):
        bx(p, (x - 0.4, x + 0.4), (0.3, 9), (-32.4, -31.6), DGR)
        bx(p, (x - 1.2, x + 1.2), (0, 0.3), (-32.4, -31.6), STL)
        bx(p, (x - 0.5, x + 0.5), (8.6, 9), (-32.4, -31.6), STL)
    xcyl(p, 24.5, 37.5, 8.6, -32, 0.2, LST, verts=8)
    xcyl(p, 25.2, 36.8, 7.0, -32, 0.18, STL, verts=8)
    for a, b in ((26.2, 29.0), (33.0, 35.8)):
        xcyl(p, a, b, 8.6, -32, 0.26, RED, verts=8, jit=0.03)
    # floor props: kettlebells and a chalk bucket
    kettlebell(p, 31.0, 0.0, -29.2, 0.7, BLK)
    kettlebell(p, 33.2, 0.0, -29.6, 0.55, RED)
    vcyl(p, 35.8, 0.0, 1.0, -29.4, 0.6, DGR, verts=8, top_r=0.7)
    vcyl(p, 35.8, 0.95, 1.05, -29.4, 0.55, WHT, verts=8, jit=0.03)


# ---- 9. Bar ---------------------------------------------------------------------------------------------------------------------
def build_Bar(p):
    # counter
    bx(p, (-72, -52), (0, 3.6), (-32, -28), WOOD, 0.07)
    for i in range(6):
        xx = -69 + i * 3.0
        bx(p, (xx - 0.08, xx + 0.08), (0.4, 3.2), (-28.05, -27.93), DWOOD, 0.03)
    bx(p, (-72.3, -51.7), (3.6, 4.0), (-32.4, -27.6), DWOOD, 0.05)
    xcyl(p, -71, -53, 0.9, -27.7, 0.15, STL, verts=8)
    for x in (-70, -62, -54):
        bx(p, (x - 0.15, x + 0.15), (0.75, 1.05), (-28, -27.7), STL)
    # protein tubs, shakers
    for x, c in zip((-69, -64.4, -59.8, -55.2), (RED, GLD, RED, GLD)):
        vcyl(p, x, 4.0, 5.6, -30, 0.8, c, verts=8, jit=0.06)
        vcyl(p, x, 5.6, 6.0, -30, 0.86, WHT, verts=8, jit=0.03)
        vcyl(p, x, 4.5, 5.2, -30, 0.84, WHT, verts=8, jit=0.03)
    for x in (-66.7, -62.1, -57.5):
        vcyl(p, x, 4.0, 5.3, -30.5, 0.36, BLU, verts=6)
        vcyl(p, x, 5.3, 5.55, -30.5, 0.4, WHT, verts=6, jit=0.02)
    # stools
    for x in (-66, -58):
        vcyl(p, x, 0, 0.15, -26.5, 0.7, DGR, verts=6)
        vcyl(p, x, 0.15, 2.1, -26.5, 0.17, STL, verts=5)
        vcyl(p, x, 2.1, 2.6, -26.5, 0.8, RED, verts=8, jit=0.07)
    # back wall with wainscot, menu board, shelves
    bx(p, (-72, -52), (0, 8), (-36.5, -35.5), CON, 0.07)
    bx(p, (-72, -52), (0, 3.2), (-35.5, -35.25), MWOOD, 0.05)
    bx(p, (-72, -52), (3.2, 3.5), (-35.5, -35.2), DWOOD, 0.03)
    bx(p, (-72, -52), (7.4, 7.9), (-35.5, -35.3), RED, 0.03)
    bx(p, (-67.2, -56.8), (4.2, 7.0), (-35.5, -35.3), GLD)
    bx(p, (-66.9, -57.1), (4.45, 6.75), (-35.3, -35.2), BLK, 0.02)
    for i, (w, y) in enumerate(((7.0, 6.2), (5.4, 5.6), (6.2, 5.0))):
        bx(p, (-62 - w / 2, -62 + w / 2), (y, y + 0.22), (-35.2, -35.1), WHT, 0.02)
    for x0, x1 in ((-71.6, -68.2), (-55.8, -52.4)):
        bx(p, (x0, x1), (5.4, 5.6), (-35.5, -34.4), DWOOD, 0.04)
        for k, x in enumerate((x0 + 0.9, x0 + 2.5)):
            vcyl(p, x, 5.6, 6.9, -35.0, 0.45, (RED, GLD)[k % 2], verts=6)
    # lockers + bench
    bx(p, (-87.6, -70), (0, 0.45), (-48, -46), DGR)
    for k, x in enumerate((-86, -82.4, -78.8, -75.2, -71.6)):
        c = BLU if k % 2 == 0 else (170, 50, 50)
        bx(p, (x - 1.6, x + 1.6), (0.45, 7), (-48, -46), c, 0.05)
        bx(p, (x - 1.6, x + 1.6), (7, 7.35), (-48.1 + 0.1, -45.9), DGR, 0.03)
        bx(p, (x - 1.4, x + 1.4), (0.8, 6.8), (-46.12, -46), shade3(c, 1.18), 0.04)
        bx(p, (x - 1.4, x + 1.4), (3.5, 3.7), (-46.15, -46.1), (25, 25, 32), 0.02)
        for y in (6.0, 6.35):
            bx(p, (x - 0.9, x + 0.9), (y, y + 0.14), (-46.2, -46.1), (25, 25, 32), 0.02)
        bx(p, (x + 0.9, x + 1.15), (3.5 - 0.1, 4.3), (-46.3, -46.1), LST, 0.02)
    bx(p, (-87.2, -70.4), (1.5, 1.9), (-44.8, -43.4), WOOD, 0.06)
    for x in (-86.6, -71.0):
        bx(p, (x - 0.2, x + 0.2), (0, 1.5), (-44.6, -44.2), DGR)
        bx(p, (x - 0.2, x + 0.2), (0, 1.5), (-44.0, -43.6), DGR)


# ---- 10. Trophy -----------------------------------------------------------------------------------------------------------------
def build_Trophy(p):
    bx(p, (12, 28), (0, 1.2), (-49.5, -42.5), DWOOD, 0.05)
    for x in (12.4, 27.6):
        for z in (-49.1, -42.9):
            bx(p, (x - 0.4, x + 0.4), (1.2, 1.6), (z - 0.4, z + 0.4), GLD, 0.03)
    bx(p, (14, 26), (1.2, 2.4), (-48.5, -43.5), MWOOD, 0.05)
    bx(p, (13.7, 26.3), (2.4, 2.6), (-48.8, -43.2), DGLD, 0.03)
    bx(p, (17, 23), (2.4 + 0.0, 3.8), (-43.5, -43.2), GLD, 0.03)                       # plaque
    star(p, 20, 3.1, -43.2, -43.0, 0.5, 0.22, RED)
    for x in (15, 25):                                                                  # pillars
        vcyl(p, x, 2.6, 3.4, -46, 1.05, GLD, verts=10, top_r=0.7, jit=0.03)
        vcyl(p, x, 3.4, 6.3, -46, 0.7, GLD, verts=10)
        vcyl(p, x, 6.3, 6.8, -46, 0.9, DGLD, verts=10, jit=0.03)
    xcyl(p, 10.2, 29.8, 7.0, -46, 0.45, GLD, verts=10, jit=0.03)                         # bar
    for x in (15, 25):
        xcyl(p, x - 0.45, x + 0.45, 7.0, -46, 0.58, DGLD, verts=10, jit=0.03)
    for s in (-1, 1):
        xc = 20 + s * 7.8
        xi = 20 + s * 9.2
        plate(p, *sorted((xc - 0.6, xc + 0.6)), 7.0, -46, 3.0, GLD, hub=GLD, verts=12, hr=1.0, ring=DGLD)
        plate(p, *sorted((xi - 0.6 + (0.04 if s < 0 else -0.04), xi + 0.6 + (0.04 if s < 0 else -0.04))), 7.0, -46, 2.3, GLD,
              hub=GLD, verts=12, hr=0.9, ring=DGLD)


PARTS = [("Floor", build_Floor), ("Hall", build_Hall), ("Sign", build_Sign), ("Benches", build_Benches),
         ("Racks", build_Racks), ("Treadmills", build_Treadmills), ("Ring", build_Ring), ("Bags", build_Bags),
         ("Bar", build_Bar), ("Trophy", build_Trophy)]

# where the reference Shiba stands in each preview: (x, z, facing, lift)
MULT = {"Racks": 3.1, "Hall": 2.7, "Floor": 2.2, "Bar": 2.6}
SHIBA_AT = {"Floor": (-62, 25, 180, 0.4), "Hall": (-30, 26, 180, 0), "Sign": (90, 38, 180, 0), "Benches": (-60, 36, 180, 0),
            "Racks": (-77, 15, 180, 0), "Treadmills": (-37, 10, 180, 0), "Ring": (74, 6, 180, 0), "Bags": (50, -25, 180, 0),
            "Bar": (-47, -28, 180, 0), "Trophy": (35, -46, 180, 0)}


# ---- fit to the union box of the blueprint pieces ---------------------------------------------------------------------------------
def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = list(q["Size"]); o = q["Offset"]; r = q.get("Rotation")
        if r:
            assert r[0] == 0 and r[1] == 0 and r[2] in (0, 90)
            if r[2] == 90:
                s = [s[1], s[0], s[2]]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - s[i] / 2); hi[i] = max(hi[i], o[i] + s[i] / 2)
    return lo, hi


def fit(part, lo, hi):
    objs = part.objs
    for o in objs:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    pts = [v.co.copy() for o in objs for v in o.data.vertices]
    bl = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
    bh = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
    tl, th = S(*lo), S(*hi)
    for o in objs:   # report objects that stick out of the target box by more than 0.05 studs
        ws = [v.co for v in o.data.vertices]
        for i, nm in enumerate("xzy"):
            if min(v[i] for v in ws) < tl[i] - 0.05 or max(v[i] for v in ws) > th[i] + 0.05:
                print(f"  WARN {part.id}: {o.name} sticks out on {nm}: {min(v[i] for v in ws):.2f}..{max(v[i] for v in ws):.2f} vs {tl[i]:.2f}..{th[i]:.2f}")
    sc = [(th[i] - tl[i]) / (bh[i] - bl[i]) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    sx, sy, sz = sc[0], sc[2], sc[1]    # back to stage order
    print(f"FIT {part.id}: raw size {[round(bh[0]-bl[0],2), round(bh[2]-bl[2],2), round(bh[1]-bl[1],2)]} "
          f"scale stage xyz = {sx:.3f} {sy:.3f} {sz:.3f}")


# ---- previews -----------------------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    sb = dk.add_reference_shiba({"Shiba": {"Position": [x, z], "Facing": facing}})
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
    flip_image(path)
    print("RENDERED", path)


def main():
    dk.start(OUT)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    built = {}
    for pid, fn in PARTS:
        pj = dk.blueprint_part(BP, pid)
        part = dk.Part(pid)
        groups = fn(part)
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        built[pid] = meshes
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        x, z, f, lift = SHIBA_AT[pid]
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", 150, 28, MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    # whole stage
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 36, 2.7, (1600, 1000))
    roof = [m for ms in built.values() for m in ms if m.name.endswith(("Hall_Roof",))]
    dk.hide(roof, True)
    snap([m for m in allm if m not in roof], shm, "stage_top.png", 180, 89, 2.7, (1600, 1000), top=True)
    dk.hide(roof, False)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_GymHall.png"))


def combine(a, b, out):
    import numpy as np
    ia, ib = bpy.data.images.load(a), bpy.data.images.load(b)
    w, h = ia.size
    pa = np.empty(w * h * 4, dtype=np.float32); ia.pixels.foreach_get(pa)
    pb = np.empty(w * h * 4, dtype=np.float32); ib.pixels.foreach_get(pb)
    both = np.concatenate([pb, pa])      # image rows start at the bottom: top view below, 3/4 view above
    img = bpy.data.images.new("stage", w, h * 2, alpha=False)
    img.pixels.foreach_set(both)
    img.filepath_raw = out
    img.file_format = 'PNG'
    img.save()
    print("RENDERED", out)


main()
