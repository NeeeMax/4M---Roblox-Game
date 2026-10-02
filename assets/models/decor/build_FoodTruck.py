"""Final low-poly decor models for the theme FoodTruck (15 parts around the fourth Shiba, Food Truck Plaza).

Usage: blender --background --factory-startup --python build_FoodTruck.py -- <outdir> [PartId ...]
Writes Decor_FoodTruck_<PartId>.fbx, preview_<PartId>.png and stage_FoodTruck.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "FoodTruck"))
ONLY = ARGS[1:]
KEY = "FoodTruck"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_FoodTruck.json"))

# ---- palette (shared by all 15 parts) -------------------------------------------------------------------------------
WHT = (240, 240, 236)
CRM = (238, 226, 196)
RED = (205, 50, 45)
DRED = (150, 36, 34)
YEL = (255, 205, 60)
TEAL = (60, 170, 165)
DTEAL = (36, 120, 115)
ORG = (235, 135, 45)
STL = (170, 175, 185)
DST = (112, 118, 130)
DRK = (45, 48, 55)
BLK = (28, 28, 34)
WOOD = (150, 105, 65)
DWOOD = (95, 65, 40)
GLS = (120, 170, 215)
GLD = (62, 100, 140)
SLT = (35, 55, 45)
GRN = (70, 150, 70)
DGRN = (48, 110, 52)
PNK = (250, 190, 205)
DPNK = (200, 90, 130)
BRK = (165, 90, 60)
STN = (190, 190, 195)
DSTN = (150, 150, 158)
WTR = (110, 175, 220)
WTR2 = (160, 210, 242)
BUN = (220, 155, 72)
PATTY = (100, 58, 38)
TAN = (205, 140, 70)
CHZ = (250, 195, 55)
DIRT = (70, 45, 30)


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (absolute stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def bar(p, a, b, t, col, jit=0.04):
    """Square bar of thickness t between two 3D points (stage coordinates)."""
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


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.04):
    """Bar in the x-y plane from (x1,y1) to (x2,y2), thickness t, depth along z centred on z."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def ext(p, pts, z0, z1, col, jit=0.04):
    """Convex polygon in the x-y plane (pts = (x, y) list) extruded along z from z0 to z1 (faces +z)."""
    n = len(pts)
    P = [(a, b, z1) for a, b in pts] + [(a, b, z0) for a, b in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return dk.poly(p, (0, 0, 0), P, faces, col, jit)


def lathe(p, cx, cz, prof, col, verts=16, jit=0.04, closed=False):
    """Solid of revolution around the vertical axis through (cx, cz). prof = [(radius, y)...] from axis to axis
    (or a closed loop with closed=True for a ring)."""
    pts, rows = [], []
    for r, y in prof:
        if r < 1e-6:
            pts.append((0, y, 0))
            rows.append([len(pts) - 1] * verts)
        else:
            base = len(pts)
            for i in range(verts):
                a = 2 * math.pi * i / verts
                pts.append((r * math.cos(a), y, r * math.sin(a)))
            rows.append([base + i for i in range(verts)])
    faces = []
    pairs = list(zip(rows, rows[1:]))
    if closed:
        pairs.append((rows[-1], rows[0]))
    for a, b in pairs:
        for i in range(verts):
            j = (i + 1) % verts
            q = []
            for v in (a[i], a[j], b[j], b[i]):
                if v not in q:
                    q.append(v)
            if len(q) >= 3:
                faces.append(tuple(q))
    return dk.poly(p, (cx, 0, cz), pts, faces, col, jit)


def star_disc(p, cx, cz, y0, y1, r_out, r_in, n, col, jit=0.05):
    """Ruffled disc (alternating radii) standing on y0, top y1 (lettuce, frills)."""
    pts = []
    for k in range(2 * n):
        a = math.pi * k / n
        r = r_out if k % 2 == 0 else r_in
        pts.append((r * math.cos(a), y1, r * math.sin(a)))
    for k in range(2 * n):
        a = math.pi * k / n
        r = r_out if k % 2 == 0 else r_in
        pts.append((r * math.cos(a), y0, r * math.sin(a)))
    m = 2 * n
    pts += [(0, y1, 0), (0, y0, 0)]
    faces = []
    for k in range(m):
        q = (k + 1) % m
        faces += [(2 * m, k, q), (2 * m + 1, m + q, m + k), (k, q, m + q, m + k)]
    return dk.poly(p, (cx, 0, cz), pts, faces, col, jit)


def letter(p, ch, x0, y0, z0, z1, w, h, t, col):
    """Block letter in the x-y plane (readable from +z), box strokes."""
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zc, x0 + c, y0 + e, t, d, col, 0.03)
    if ch == 'P':
        r(0, 0, t, h); r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(w - t, h / 2, w, h - t)
    elif ch == 'B':
        r(0, 0, t, h); r(0, h - t, w - t * 0.6, h); r(0, h / 2 - t / 2, w - t * 0.3, h / 2 + t / 2); r(0, 0, w - t * 0.6, t)
        r(w - t, h / 2, w, h - t * 0.5); r(w - t, t * 0.5, w, h / 2)
    elif ch == 'R':
        r(0, 0, t, h); r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(w - t, h / 2, w, h - t)
        dg(t * 0.6, h / 2, w - t * 0.4, t * 0.3)
    elif ch == 'O':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'I':
        r(0, 0, w, t); r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h)
    elif ch == 'C':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t)
    elif ch == 'E':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2); r(t, 0, w, t)
    elif ch == 'A':
        r(0, 0, t, h - t); r(w - t, 0, w, h - t); r(0, h - t, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'D':
        r(0, 0, t, h); r(t, h - t, w - t, h); r(t, 0, w - t, t); r(w - t, t, w, h - t)
    elif ch == 'N':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w - t * 0.5, t * 0.5)
    elif ch == 'U':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, 0, w - t, t)
    elif ch == 'T':
        r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h - t)
    elif ch == 'S':
        r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(0, 0, w, t); r(0, h / 2, t, h - t); r(w - t, t, w, h / 2)
    elif ch == 'K':
        r(0, 0, t, h); dg(t, h / 2, w - t * 0.3, h - t * 0.4); dg(t, h / 2, w - t * 0.3, t * 0.4)
    elif ch == 'W':
        r(0, 0, t, h); r(w - t, 0, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h * 0.6); r(0, 0, w, t)
    elif ch == 'G':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t); r(w - t, t, w, h / 2); r(w / 2, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'Z':
        r(0, h - t, w, h); r(0, 0, w, t); dg(w - t * 0.5, h - t * 0.5, t * 0.5, t * 0.5)
    elif ch == 'M':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w / 2, h * 0.4); dg(w / 2, h * 0.4, w - t * 0.5, h - t * 0.5)
    elif ch == 'F':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.8, h / 2 + t / 2)
    elif ch == 'Y':
        r(w / 2 - t / 2, 0, w / 2 + t / 2, h / 2); dg(t * 0.5, h - t * 0.5, w / 2, h / 2); dg(w - t * 0.5, h - t * 0.5, w / 2, h / 2)
    elif ch == 'L':
        r(0, 0, t, h); r(0, 0, w, t)


def text(p, s, cx, y0, z0, z1, w, h, t, gap, col):
    """Row of block letters centred on cx, reading left to right for a viewer on the +z side."""
    total = len(s) * w + (len(s) - 1) * gap
    x = cx - total / 2
    for ch in s:
        if ch != ' ':
            letter(p, ch, x, y0, z0, z1, w, h, t, col)
        x += w + gap


# ---- food truck ----------------------------------------------------------------------------------------------------------
def emblem(p, kind, ex, ey, z0):
    """Round badge with a food icon on the rear part of the serving side (faces +z)."""
    zcyl(p, ex, ey, z0, z0 + 0.1, 1.25, CRM, verts=14, jit=0.02)
    a, b = z0 + 0.1, z0 + 0.22
    if kind == 'burger':
        bx(p, (ex - 0.85, ex + 0.85), (ey - 0.78, ey - 0.5), (a, b), BUN, 0.03)
        bx(p, (ex - 0.95, ex + 0.95), (ey - 0.5, ey - 0.22), (a, b), PATTY, 0.03)
        bx(p, (ex - 0.9, ex + 0.9), (ey - 0.22, ey - 0.08), (a, b), CHZ, 0.02)
        bx(p, (ex - 1.0, ex + 1.0), (ey - 0.08, ey + 0.12), (a, b), GRN, 0.03)
        bx(p, (ex - 0.9, ex + 0.9), (ey + 0.12, ey + 0.3), (a, b), RED, 0.03)
        ext(p, [(ex + 0.9 * math.cos(t), ey + 0.3 + 0.78 * math.sin(t)) for t in [math.pi * k / 7 for k in range(8)]], a, b, BUN, 0.03)
        for dx, dy in ((-0.4, 0.62), (0.1, 0.8), (0.5, 0.55)):
            bx(p, (ex + dx - 0.12, ex + dx + 0.12), (ey + dy - 0.06, ey + dy + 0.06), (b, b + 0.03), CRM, 0.02)
    elif kind == 'taco':
        ext(p, [(ex + 1.05 * math.cos(math.pi + math.pi * k / 8), ey + 0.3 + 1.05 * math.sin(math.pi + math.pi * k / 8)) for k in range(9)], a, b, YEL, 0.03)
        for i, dx in enumerate((-0.65, -0.22, 0.22, 0.65)):
            bx(p, (ex + dx - 0.2, ex + dx + 0.2), (ey + 0.28, ey + 0.62), (a, b), GRN if i % 2 == 0 else RED, 0.03)
    elif kind == 'pizza':
        ext(p, [(ex - 0.95, ey + 0.55), (ex + 0.95, ey + 0.55), (ex, ey - 0.95)], a, b, CHZ, 0.03)
        bx(p, (ex - 1.02, ex + 1.02), (ey + 0.5, ey + 0.84), (a, b), TAN, 0.03)
        for dx, dy in ((-0.35, 0.15), (0.3, 0.05), (0.0, -0.4)):
            zcyl(p, ex + dx, ey + dy, b, b + 0.04, 0.18, RED, verts=8, jit=0.02)
    else:   # dessert
        ext(p, [(ex - 0.55, ey - 0.05), (ex + 0.55, ey - 0.05), (ex, ey - 1.0)], a, b, TAN, 0.03)
        zcyl(p, ex, ey + 0.2, a, b, 0.6, DPNK, verts=10, jit=0.03)
        zcyl(p, ex, ey + 0.78, b, b + 0.05, 0.48, WHT, verts=10, jit=0.02)
        zcyl(p, ex, ey + 1.1, b + 0.05, b + 0.1, 0.17, RED, verts=8, jit=0.02)


def truck(p, cx, cz, body, trim, awnA, awnB, kind, label, txt, w, gap):
    """A food truck 16 long (x) and 7 deep (z), cab toward +x, serving window and awning toward +z (the road side)."""
    def B(u0, u1, y0, y1, v0, v1, col, jit=0.04):
        return bx(p, (cx + u0, cx + u1), (y0, y1), (cz + v0, cz + v1), col, jit)

    roof = dk.shade(body, 0.86) if body[0] + body[1] + body[2] > 700 else dk.shade(body, 0.9)
    # chassis and wheels
    B(-7.6, 7.7, 0.7, 1.5, -3.2, 3.2, DRK, 0.03)
    for u in (-6, 5):
        zcyl(p, cx + u, 1.2, cz + 3.3, cz + 4.1, 1.2, BLK, verts=10, jit=0.03)
        zcyl(p, cx + u, 1.2, cz + 4.1, cz + 4.15, 0.65, STL, verts=8, jit=0.02)
        zcyl(p, cx + u, 1.2, cz - 4.1, cz - 3.3, 1.2, BLK, verts=10, jit=0.03)
        zcyl(p, cx + u, 1.2, cz - 4.15, cz - 4.1, 0.65, STL, verts=8, jit=0.02)
    # box body, dark skirt, stripe, roof cap
    B(-8, 2, 1.2, 6.8, -3.5, 3.5, body, 0.03)
    B(-8, 2, 1.2, 2.0, 3.5, 3.55, DRK, 0.03)
    B(-8, 2, 1.2, 2.0, -3.55, -3.5, DRK, 0.03)
    B(-8, 2, 2.2, 3.0, 3.5, 3.62, trim, 0.02)
    B(-8, 2, 2.2, 3.0, -3.62, -3.5, trim, 0.02)
    B(-8, 2, 6.8, 7.2, -3.65, 3.65, roof, 0.03)
    # serving window: frame, dark glass, mullion, counter with a few items
    B(-5.5, -0.5, 3.4, 5.4, 3.5, 3.58, GLD, 0.05)
    B(-3.05, -2.95, 3.4, 5.4, 3.5, 3.66, trim, 0.02)
    B(-5.8, -0.2, 5.4, 5.7, 3.5, 3.75, trim, 0.03)
    B(-5.8, -5.5, 3.2, 5.4, 3.5, 3.75, trim, 0.03)
    B(-0.5, -0.2, 3.2, 5.4, 3.5, 3.75, trim, 0.03)
    B(-5.9, -0.1, 3.0, 3.3, 3.5, 4.85, WOOD, 0.05)
    B(-5.9, -0.1, 2.65, 3.0, 4.55, 4.85, DWOOD, 0.04)
    for u, col in ((-4.6, WHT), (-4.0, RED)):
        vcyl(p, cx + u, 3.3, 3.8, cz + 4.2, 0.2, col, verts=6, jit=0.02)
    B(-2.2, -1.5, 3.3, 3.45, 4.0, 4.7, STL, 0.02)
    B(-1.1, -0.7, 3.3, 3.65, 4.0, 4.4, YEL, 0.02)
    # awning with scalloped valance and two poles
    cols = (awnA, awnB)
    for i in range(6):
        x0, x1 = -6.6 + i * 1.6, -5.0 + i * 1.6
        hexa(p, [(cx + x0, 5.95, cz + 3.5), (cx + x1, 5.95, cz + 3.5), (cx + x1, 5.05, cz + 6.1), (cx + x0, 5.05, cz + 6.1),
                 (cx + x0, 6.2, cz + 3.5), (cx + x1, 6.2, cz + 3.5), (cx + x1, 5.3, cz + 6.1), (cx + x0, 5.3, cz + 6.1)],
             cols[i % 2], 0.03)
        B(x0, x1, 4.85, 5.3, 5.95, 6.1, cols[i % 2], 0.03)
    for u in (-6.4, 2.8):
        vcyl(p, cx + u, 0, 5.1, cz + 5.95, 0.14, STL, verts=6, jit=0.02)
    # rear badge
    emblem(p, kind, cx - 6.7, 4.7, cz + 3.5)
    # roof sign with bulbs, roof unit and exhaust
    B(-6.2, 0.2, 7.2, 8.6, -0.3, 0.3, trim, 0.03)
    B(-6.2, 0.2, 8.45, 8.6, -0.32, 0.32, DRK, 0.02)
    B(-6.2, 0.2, 7.2, 7.35, -0.32, 0.32, DRK, 0.02)
    text(p, label, cx - 3.0, 7.48, cz + 0.3, cz + 0.42, w, 0.9, 0.2, gap, txt)
    B(0.5, 1.9, 7.2, 7.9, -1.5, 1.5, DST, 0.04)
    B(0.6, 1.8, 7.9, 8.0, -1.4, 1.4, STL, 0.03)
    vcyl(p, cx - 7.1, 7.2, 8.4, cz - 2.4, 0.26, DRK, verts=6, jit=0.02)
    # cab: lower block, glass cabin with pillars, roof, headlights, grille, bumper, mirror
    B(2, 8, 1.2, 3.0, -3.5, 3.5, body, 0.03)
    hexa(p, [(cx + 2.0, 3.0, cz - 3.4), (cx + 8.0, 3.0, cz - 3.4), (cx + 8.0, 3.0, cz + 3.4), (cx + 2.0, 3.0, cz + 3.4),
             (cx + 2.0, 4.8, cz - 3.4), (cx + 7.0, 4.8, cz - 3.4), (cx + 7.0, 4.8, cz + 3.4), (cx + 2.0, 4.8, cz + 3.4)], GLS, 0.04)
    B(2, 7.2, 4.8, 5.0, -3.55, 3.55, roof, 0.03)
    for v in (3.4, -3.5):
        B(2.0, 2.45, 3.0, 4.8, v, v + 0.1, body, 0.03)
        B(4.45, 4.75, 3.0, 4.8, v, v + 0.1, body, 0.03)
    B(7.0, 8.0, 3.0, 3.2, -3.5, 3.5, body, 0.03)
    for v in (-2.4, 2.4):
        B(7.9, 8.0, 2.0, 2.7, v - 0.5, v + 0.5, YEL, 0.02)
    B(7.85, 8.0, 1.5, 2.5, -1.2, 1.2, DRK, 0.03)
    for y in (1.8, 2.2):
        B(7.88, 8.05, y, y + 0.1, -1.2, 1.2, STL, 0.02)
    B(7.9, 8.55, 1.0, 1.6, -3.7, 3.7, STL, 0.03)
    B(6.5, 6.8, 3.6, 4.3, 3.5, 4.1, DRK, 0.03)
    B(6.5, 6.8, 3.6, 4.3, -4.1, -3.5, DRK, 0.03)
    # rear: tail lights, door seam, bumper
    for v in (-2.7, 2.7):
        B(-8, -7.9, 1.8, 2.5, v - 0.5, v + 0.5, RED, 0.02)
    B(-8, -7.9, 1.4, 6.6, -0.06, 0.06, DRK, 0.02)
    B(-8, -7.5, 1.0, 1.5, -3.4, 3.4, DRK, 0.03)


# ---- 1. Paving -------------------------------------------------------------------------------------------------------------
def build_Paving(p):
    bx(p, (5, 35), (0, 0.1), (36, 54), (150, 142, 130), 0.05)
    for c in range(5):
        for r in range(3):
            even = (c + r) % 2 == 0
            x0, z0 = 5 + c * 6, 36 + r * 6
            bx(p, (x0 + 0.15, x0 + 5.85), (0.1, 0.15), (z0 + 0.15, z0 + 5.85), (225, 215, 195) if even else (190, 70, 60), 0.05)
            bx(p, (x0 + 1.6, x0 + 4.4), (0.15, 0.18), (z0 + 1.6, z0 + 4.4), (190, 70, 60) if even else (225, 215, 195), 0.03,
               rot=(0, 45, 0))
            bx(p, (x0 + 2.45, x0 + 3.55), (0.18, 0.2), (z0 + 2.45, z0 + 3.55), YEL, 0.02, rot=(0, 45, 0))


# ---- 2. TicketBooth --------------------------------------------------------------------------------------------------------
def build_TicketBooth(p):
    bx(p, (-51.3, -44.7), (0, 0.6), (49.2, 54.8), STN, 0.05)
    bx(p, (-51, -45), (0.6, 7.0), (49.5, 54.5), RED, 0.03)
    bx(p, (-51.04, -44.96), (0.6, 1.9), (49.46, 54.55), WHT, 0.03)
    # yellow band with the lettering
    bx(p, (-51.04, -44.96), (5.35, 6.4), (49.46, 54.56), YEL, 0.03)
    text(p, "TICKET", -48, 5.55, 54.56, 54.7, 0.76, 0.7, 0.17, 0.2, DRED)
    # service window: frame, glass, mullion, counter, items
    bx(p, (-50.0, -46.0), (3.3, 5.2), (54.5, 54.62), YEL, 0.03)
    bx(p, (-49.7, -46.3), (3.5, 5.0), (54.55, 54.7), GLD, 0.05)
    bx(p, (-48.1, -47.9), (3.5, 5.0), (54.55, 54.78), YEL, 0.02)
    bx(p, (-50.2, -45.8), (2.8, 3.1), (54.5, 55.5), WOOD, 0.05)
    bx(p, (-50.2, -45.8), (2.4, 2.8), (54.9, 55.5), DWOOD, 0.04)
    vcyl(p, -49.2, 3.1, 3.5, 55.0, 0.22, RED, verts=8, jit=0.02)
    vcyl(p, -49.2, 3.5, 3.58, 55.0, 0.22, WHT, verts=8, jit=0.02)
    bx(p, (-47.2, -46.4), (3.1, 3.2), (54.8, 55.3), YEL, 0.02)
    bx(p, (-47.2, -46.9), (3.2, 3.3), (54.8, 55.3), RED, 0.02)
    ball(p, (-46.4, 3.35, 55.1), 0.26, YEL, subdiv=1, jit=0.02)
    # poster and lamp on the wall beside the window
    bx(p, (-50.85, -50.2), (3.7, 5.3), (54.5, 54.6), CRM, 0.03)
    bx(p, (-50.7, -50.35), (4.6, 5.1), (54.6, 54.66), RED, 0.02)
    bx(p, (-45.8, -45.2), (3.6, 4.4), (54.5, 54.6), DRED, 0.03)
    bx(p, (-45.65, -45.35), (3.8, 4.2), (54.6, 54.66), YEL, 0.02)
    # side door
    bx(p, (-45.0, -44.9), (0.6, 5.0), (50.4, 52.3), DWOOD, 0.03)
    bx(p, (-44.9, -44.84), (0.9, 4.7), (50.55, 52.15), WOOD, 0.03)
    bx(p, (-44.84, -44.78), (2.6, 2.9), (51.8, 52.0), YEL, 0.02)
    # roof: slab, striped fascia, hip roof, finial
    bx(p, (-51.8, -44.2), (7.0, 7.4), (48.7, 55.3), DWOOD, 0.03)
    for i in range(8):
        x0 = -51.8 + i * 0.95
        bx(p, (x0, x0 + 0.95), (6.6, 7.0), (55.0, 55.3), RED if i % 2 else WHT, 0.02)
    dk.poly(p, (0, 0, 0), [(-51.5, 7.4, 49.0), (-44.5, 7.4, 49.0), (-44.5, 7.4, 55.0), (-51.5, 7.4, 55.0),
                           (-49.5, 8.5, 52.0), (-46.5, 8.5, 52.0)],
            [(0, 1, 2, 3), (0, 1, 5, 4), (3, 2, 5, 4), (0, 3, 4), (1, 2, 5)], DRED, 0.05)
    bx(p, (-49.6, -46.4), (8.4, 8.6), (51.9, 52.1), YEL, 0.02)
    vcyl(p, -48, 8.5, 9.05, 52, 0.12, STL, verts=6, jit=0.02)
    ball(p, (-48, 9.0, 52), 0.3, YEL, subdiv=1, jit=0.02)


# ---- 3. TruckBurger --------------------------------------------------------------------------------------------------------
def build_TruckBurger(p):
    truck(p, -65, 22, WHT, RED, RED, WHT, 'burger', "BURGER", WHT, 0.78, 0.16)


# ---- 4. TruckTaco ---------------------------------------------------------------------------------------------------------
def build_TruckTaco(p):
    truck(p, 70, 20, TEAL, YEL, ORG, WHT, 'taco', "TACO", DTEAL, 1.0, 0.25)


# ---- 5. Tables --------------------------------------------------------------------------------------------------------------
def picnic(p, x, z, cloth):
    # top planks and checkered runner
    for k, dz in enumerate((-1.05, 0.0, 1.05)):
        bx(p, (x - 3, x + 3), (2.3, 2.55), (z + dz - 0.5, z + dz + 0.5), WOOD if k != 1 else (170, 120, 75), 0.06)
    for i in range(6):
        for j in range(2):
            bx(p, (x - 3 + i, x - 2 + i), (2.55, 2.6), (z - 0.7 + j * 0.7, z + j * 0.7), cloth[(i + j) % 2], 0.02)
    # frame beams, A-frame legs, benches
    for sx in (-2, 2):
        bx(p, (x + sx - 0.2, x + sx + 0.2), (1.95, 2.3), (z - 1.5, z + 1.5), DWOOD, 0.04)
        for sv in (-1, 1):
            bar(p, (x + sx, 2.2, z + sv * 0.7), (x + sx, 0.2, z + sv * 3.0), 0.38, DWOOD, 0.04)
    bx(p, (x - 2, x + 2), (1.0, 1.25), (z - 0.2, z + 0.2), DWOOD, 0.04)
    for sv in (-1, 1):
        zc = z + sv * 3
        bx(p, (x - 3, x + 3), (1.3, 1.55), (zc - 0.6, zc - 0.05), WOOD, 0.06)
        bx(p, (x - 3, x + 3), (1.3, 1.55), (zc + 0.05, zc + 0.6), (170, 120, 75), 0.06)
    # table items: ketchup, mustard, napkin holder
    vcyl(p, x - 1.5, 2.6, 2.9, z + 0.3, 0.17, RED, verts=6, jit=0.02)
    vcyl(p, x - 1.1, 2.6, 2.85, z - 0.2, 0.15, YEL, verts=6, jit=0.02)
    bx(p, (x + 0.8, x + 1.4), (2.6, 2.85), (z - 0.3, z + 0.3), STL, 0.02)
    vcyl(p, x + 2.0, 2.6, 2.8, z + 0.3, 0.3, WHT, verts=8, jit=0.02)


def build_Tables(p):
    picnic(p, -18, 4, (WHT, RED))
    picnic(p, -30, 4, (WHT, DGRN))


# ---- 6. Lights ---------------------------------------------------------------------------------------------------------------
def build_Lights(p):
    for z in (14, -8):
        vcyl(p, -46, 0, 0.3, z, 0.34, STN, verts=8, jit=0.03)
        vcyl(p, -46, 0.3, 0.9, z, 0.32, DRK, verts=8, jit=0.03)
        vcyl(p, -46, 0.9, 7.6, z, 0.3, DWOOD, verts=8, top_r=0.22, jit=0.06)
        vcyl(p, -46, 7.6, 8.0, z, 0.34, STL, verts=8, top_r=0.1, jit=0.03)
        bx(p, (-46.12, -45.88), (7.0, 7.5), (z - 0.15, z + 0.15), DRK, 0.02)

    def wy(z):
        return 7.5 - 1.15 * (1 - ((z - 3) / 11.0) ** 2)
    n = 12
    for i in range(n):
        za, zb = 14 - 22.0 * i / n, 14 - 22.0 * (i + 1) / n
        bar(p, (-46, wy(za), za), (-46, wy(zb), zb), 0.14, DRK, 0.02)
    for k in range(7):
        z = 10.5 - 2.5 * k
        y = wy(z)
        vcyl(p, -46, y - 0.28, y - 0.02, z, 0.12, DRK, verts=6, jit=0.02)
        lathe(p, -46, z, [(0, y - 1.05), (0.28, y - 0.92), (0.45, y - 0.62), (0.42, y - 0.36), (0.2, y - 0.22), (0.0, y - 0.22)],
              (255, 240, 170) if k % 2 == 0 else (255, 214, 120), verts=8, jit=0.02)


# ---- 7. Fountain -------------------------------------------------------------------------------------------------------------
def arc(p, cx, cz, a, pts, t, col):
    for (r0, y0), (r1, y1) in zip(pts, pts[1:]):
        bar(p, (cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)), (cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)), t, col, 0.02)


def build_Fountain(p):
    cx, cz = 62, -34
    lathe(p, cx, cz, [(7.2, 0.0), (8.0, 0.0), (8.0, 1.7), (7.6, 1.95), (7.2, 1.95)], STN, verts=16, jit=0.05, closed=True)
    vcyl(p, cx, 0, 1.3, cz, 7.25, DSTN, verts=16, jit=0.03)
    vcyl(p, cx, 1.3, 1.6, cz, 7.2, WTR, verts=16, jit=0.03)
    for k in range(8):
        a = math.pi * k / 4 + math.pi / 8
        bx(p, (cx + 7.6 * math.cos(a) - 0.4, cx + 7.6 * math.cos(a) + 0.4), (1.95, 2.45),
           (cz + 7.6 * math.sin(a) - 0.4, cz + 7.6 * math.sin(a) + 0.4), STN, 0.05, rot=(0, -math.degrees(a), 0))
    # pedestal and lower bowl
    lathe(p, cx, cz, [(0, 1.5), (1.9, 1.5), (1.9, 1.95), (1.15, 2.4), (0.85, 3.0), (0.85, 4.1), (0, 4.1)], STN, verts=12, jit=0.05)
    lathe(p, cx, cz, [(0, 4.1), (1.2, 4.1), (2.7, 4.5), (3.8, 5.25), (3.9, 5.6), (0, 5.6)], STN, verts=16, jit=0.05)
    lathe(p, cx, cz, [(3.4, 5.6), (3.9, 5.6), (3.9, 5.9), (3.4, 5.9)], DSTN, verts=16, jit=0.04, closed=True)
    vcyl(p, cx, 5.6, 5.78, cz, 3.45, WTR, verts=16, jit=0.03)
    # column, upper basin and the top water ball
    vcyl(p, cx, 5.78, 7.2, cz, 0.55, STN, verts=8, jit=0.04)
    lathe(p, cx, cz, [(0, 6.9), (1.0, 7.1), (1.3, 7.45), (0.5, 7.5), (0, 7.5)], DSTN, verts=10, jit=0.04)
    ball(p, (cx, 7.8, cz), 0.9, WTR, subdiv=1, jit=0.03)
    for k in range(6):
        a = k * math.pi / 3
        arc(p, cx, cz, a, [(0.7, 8.1), (1.7, 8.0), (2.5, 7.2), (3.1, 5.85)], 0.17, WTR2)


# ---- 8. Umbrellas -------------------------------------------------------------------------------------------------------------
def umbrella_set(p, cx, cz, canopy):
    vcyl(p, cx, 0, 0.25, cz, 1.3, STL, verts=8, jit=0.03)
    vcyl(p, cx, 0.25, 2.5, cz, 0.4, STL, verts=8, jit=0.03)
    vcyl(p, cx, 2.5, 2.74, cz, 2.0, canopy, verts=12, jit=0.03)
    vcyl(p, cx, 2.74, 2.8, cz, 1.7, WHT, verts=12, jit=0.02)
    vcyl(p, cx, 2.8, 8.2, cz, 0.15, STL, verts=6, jit=0.02)
    for k in range(8):
        a0, a1 = math.pi * k / 4, math.pi * (k + 1) / 4
        pts = [(0, 8.35, 0), (0, 7.8, 0), (4.5 * math.cos(a0), 7.8, 4.5 * math.sin(a0)), (4.5 * math.cos(a1), 7.8, 4.5 * math.sin(a1))]
        dk.poly(p, (cx, 0, cz), pts, [(0, 2, 3), (1, 3, 2), (0, 1, 2), (0, 3, 1)], canopy if k % 2 == 0 else WHT, 0.03)
    vcyl(p, cx, 8.3, 8.6, cz, 0.22, STL, verts=6, jit=0.02)
    # stools and table items
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        vcyl(p, cx + dx, 0, 1.1, cz + dz, 0.2, STL, verts=6, jit=0.02)
        vcyl(p, cx + dx, 1.1, 1.4, cz + dz, 0.7, canopy, verts=8, jit=0.04)
    vcyl(p, cx + 0.9, 2.8, 3.3, cz + 0.8, 0.2, RED, verts=6, jit=0.02)
    vcyl(p, cx - 0.9, 2.8, 3.2, cz - 0.7, 0.18, YEL, verts=6, jit=0.02)
    bx(p, (cx - 0.3, cx + 0.3), (2.8, 3.1), (cz - 0.2, cz + 0.2), STL, 0.02)


def build_Umbrellas(p):
    umbrella_set(p, 24, -12, ORG)
    umbrella_set(p, 34, -16, TEAL)


# ---- 9. TruckPizza ------------------------------------------------------------------------------------------------------------
def build_TruckPizza(p):
    truck(p, -70, -15, RED, WHT, GRN, WHT, 'pizza', "PIZZA", RED, 0.85, 0.2)


# ---- 10. Planters ----------------------------------------------------------------------------------------------------------------
def planter(p, x, z, flowers):
    for k in range(4):
        bx(p, (x - 3, x + 3), (k * 0.4, k * 0.4 + 0.4), (z - 1.2, z + 1.2), BRK if k % 2 == 0 else (150, 78, 52), 0.1)
    bx(p, (x - 3, x + 3), (1.6, 1.85), (z - 1.2, z - 0.8), (190, 105, 72), 0.04)
    bx(p, (x - 3, x + 3), (1.6, 1.85), (z + 0.8, z + 1.2), (190, 105, 72), 0.04)
    bx(p, (x - 3.0, x - 2.5), (1.6, 1.85), (z - 0.8, z + 0.8), (190, 105, 72), 0.04)
    bx(p, (x + 2.5, x + 3.0), (1.6, 1.85), (z - 0.8, z + 0.8), (190, 105, 72), 0.04)
    bx(p, (x - 2.5, x + 2.5), (1.6, 2.0), (z - 0.8, z + 0.8), DIRT, 0.05)
    for i, (dx, dz) in enumerate(((-2.0, 0.0), (-1.1, 0.4), (0.0, -0.3), (1.0, 0.3), (2.0, -0.1))):
        vcyl(p, x + dx, 2.0, 2.0 + 1.0 + 0.1 * (i % 2), z + dz, 0.75, DGRN if i % 2 else GRN, verts=6, top_r=0.25, jit=0.06)
    spots = ((-2.0, 3.25, 0.1), (-1.0, 3.4, 0.5), (0.0, 3.3, -0.3), (1.0, 3.4, 0.3), (2.0, 3.25, -0.1), (-0.5, 3.0, 0.7), (0.9, 3.0, -0.6))
    for i, (dx, y, dz) in enumerate(spots):
        vcyl(p, x + dx, y - 0.1, y + 0.12, z + dz, 0.5, flowers[i % len(flowers)], verts=5, jit=0.03)
        vcyl(p, x + dx, y + 0.12, y + 0.2, z + dz, 0.17, (255, 215, 80) if flowers[i % len(flowers)] != YEL else (150, 85, 40), verts=5, jit=0.02)


def build_Planters(p):
    planter(p, -56, -40, (RED, YEL))
    planter(p, -49, -40, (DPNK, WHT, YEL))
    planter(p, -42, -40, (YEL, ORG, DPNK))


# ---- 11. Bins ---------------------------------------------------------------------------------------------------------------------
def build_Bins(p):
    for x in (10, 14):
        lathe(p, x, -30, [(0, 0), (0.95, 0), (1.2, 0.25), (1.2, 3.0), (0, 3.0)], STL, verts=12, jit=0.05)
        for y0 in (0.7, 2.2):
            vcyl(p, x, y0, y0 + 0.2, -30, 1.26, DST, verts=12, jit=0.03)
        lathe(p, x, -30, [(0, 3.0), (1.35, 3.0), (1.35, 3.2), (1.0, 3.55), (0.4, 3.72), (0, 3.72)], DRK, verts=12, jit=0.04)
        bx(p, (x - 0.5, x + 0.5), (3.3, 3.5), (-29.1, -28.7), BLK, 0.02)
        vcyl(p, x, 3.7, 3.8, -30, 0.28, STL, verts=6, jit=0.02)
        bx(p, (x - 0.3, x + 0.3), (0.05, 0.25), (-28.95, -28.58), DRK, 0.02)
        bx(p, (x - 0.5, x + 0.5), (1.3, 2.1), (-28.82, -28.75), CRM, 0.02)
        bx(p, (x - 0.15, x + 0.15), (1.45, 1.95), (-28.75, -28.7), GRN, 0.02)
    # blue recycling bin with the arrows sign
    bx(p, (16.7, 19.3), (0, 3.4), (-31.3, -28.7), (50, 110, 200), 0.04)
    bx(p, (16.6, 19.4), (0, 0.3), (-31.4, -28.6), DRK, 0.03)
    dk.poly(p, (0, 0, 0), [(16.55, 3.4, -31.45), (19.45, 3.4, -31.45), (19.45, 3.4, -28.55), (16.55, 3.4, -28.55),
                           (16.8, 3.8, -31.0), (19.2, 3.8, -31.0), (19.2, 3.8, -28.9), (16.8, 3.8, -28.9)],
            [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], (30, 70, 150), 0.03)
    bx(p, (17.2, 18.8), (3.55, 3.72), (-29.6, -29.1), BLK, 0.02)
    ext(p, [(18.0 - 0.6, 1.0), (18.0 + 0.6, 1.0), (18.0, 2.1)], -28.7, -28.62, WHT, 0.02)
    ext(p, [(18.0 - 0.28, 1.3), (18.0 + 0.28, 1.3), (18.0, 1.78)], -28.62, -28.58, (50, 110, 200), 0.02)
    bx(p, (16.8, 19.2), (2.4, 2.9), (-28.7, -28.62), WHT, 0.02)


# ---- 12. Menus -----------------------------------------------------------------------------------------------------------------------
def menu_frame(p, x):
    for dx in (-2, 2):
        bx(p, (x + dx - 0.2, x + dx + 0.2), (0, 1.2), (-12.2, -11.8), WOOD, 0.05)
    bx(p, (x - 2.5, x + 2.5), (1.2, 4.8), (-12.2, -11.8), SLT, 0.04)
    bx(p, (x - 2.5, x + 2.5), (1.2, 1.45), (-12.3, -11.7), WOOD, 0.04)
    bx(p, (x - 2.5, x - 2.25), (1.2, 4.8), (-12.3, -11.7), WOOD, 0.04)
    bx(p, (x + 2.25, x + 2.5), (1.2, 4.8), (-12.3, -11.7), WOOD, 0.04)
    bx(p, (x - 2.7, x + 2.7), (4.8, 5.1), (-12.35, -11.65), DWOOD, 0.04)


def build_Menus(p):
    z0, z1 = -11.8, -11.7
    menu_frame(p, -33)
    text(p, "MENU", -33, 3.55, z0, z1, 0.8, 0.95, 0.2, 0.22, WHT)
    bx(p, (-34.8, -31.2), (3.3, 3.4), (z0, z1), WHT, 0.02)
    for i, (col, ln) in enumerate(((BUN, 1.9), (RED, 1.5), (TEAL, 1.7))):
        y = 2.7 - i * 0.5
        bx(p, (-34.8, -34.4), (y, y + 0.32), (z0, z1), col, 0.02)
        bx(p, (-34.1, -34.1 + ln), (y + 0.1, y + 0.22), (z0, z1), WHT, 0.02)
        bx(p, (-32.0, -31.4), (y + 0.02, y + 0.3), (z0, z1), YEL, 0.02)
    menu_frame(p, -27)
    text(p, "TODAY", -27, 3.7, z0, z1, 0.7, 0.8, 0.17, 0.15, YEL)
    ext(p, [(-28.9, 3.2), (-26.1, 3.2), (-27.5, 1.6)], z0, z1, CHZ, 0.02)
    bx(p, (-29.0, -26.0), (3.1, 3.3), (z0, z1), TAN, 0.02)
    for dx, dy in ((-0.5, 0.35), (0.4, 0.45), (-0.1, -0.2)):
        zcyl(p, -27.5 + dx, 2.8 + dy, z0, z1 + 0.03, 0.2, RED, verts=8, jit=0.02)
    bx(p, (-25.6, -24.9), (1.7, 3.0), (z0, z1), WHT, 0.02)
    bx(p, (-25.5, -25.0), (2.4, 2.9), (z0, z1 + 0.03), RED, 0.02)
    bx(p, (-25.8, -24.7), (1.55, 1.7), (z0, z1), WHT, 0.02)


# ---- 13. TruckDessert ------------------------------------------------------------------------------------------------------------------
def build_TruckDessert(p):
    truck(p, 35, -45, PNK, DPNK, ORG, WHT, 'dessert', "SWEETS", WHT, 0.78, 0.16)


# ---- 14. Stage ------------------------------------------------------------------------------------------------------------------------
def build_Stage(p):
    # deck: dark skirt, planks, yellow and red trim
    bx(p, (-81, -59), (0, 1.0), (-55, -41.1), DRK, 0.04)
    for k in range(5):
        bx(p, (-81, -59), (1.0, 1.2), (-55 + 2.8 * k, -52.25 + 2.8 * k), WOOD if k % 2 == 0 else (125, 88, 55), 0.05)
    bx(p, (-81, -59), (0.45, 0.75), (-41.1, -41.0), YEL, 0.02)
    bx(p, (-81, -59), (0.0, 0.2), (-41.1, -41.0), RED, 0.02)
    # backdrop with curtain folds, header and banner
    for k in range(7):
        bx(p, (-81 + 22 * k / 7, -81 + 22 * (k + 1) / 7), (1.2, 8.5), (-54.85, -54.35), RED if k % 2 == 0 else DRED, 0.03)
    bx(p, (-81, -59), (8.5, 9.2), (-54.85, -54.2), DRED, 0.03)
    bx(p, (-81, -59), (8.4, 8.5), (-54.85, -54.2), YEL, 0.02)
    bx(p, (-77.4, -62.6), (5.0, 7.0), (-54.35, -54.05), YEL, 0.03)
    bx(p, (-77.2, -62.8), (5.15, 6.85), (-54.05, -53.98), (255, 225, 120), 0.02)
    text(p, "FOOD", -70, 5.4, -53.98, -53.86, 2.4, 1.2, 0.34, 0.7, DRED)
    # cutlery icons beside the word
    # light truss on two poles, with spotlights
    for x in (-80, -60):
        vcyl(p, x, 1.2, 8.2, -52, 0.3, STL, verts=8, jit=0.03)
        vcyl(p, x, 1.2, 1.5, -52, 0.6, DST, verts=8, jit=0.03)
    bx(p, (-80.5, -59.5), (8.2, 8.3), (-52.3, -51.7), STL, 0.03)
    bx(p, (-80.5, -59.5), (8.5, 8.6), (-52.3, -51.7), STL, 0.03)
    n = 10
    for i in range(n):
        xa, xb = -80.5 + 21.0 * i / n, -80.5 + 21.0 * (i + 1) / n
        if i % 2 == 0:
            diag(p, xa, 8.25, -52, xb, 8.55, 0.12, 0.12, DST, 0.02)
        else:
            diag(p, xa, 8.55, -52, xb, 8.25, 0.12, 0.12, DST, 0.02)
    for x in (-76, -72, -68, -64):
        bx(p, (x - 0.5, x + 0.5), (7.2, 8.2), (-51.9, -51.1), DRK, 0.03)
        bx(p, (x - 0.35, x + 0.35), (7.35, 8.05), (-51.1, -50.9), (255, 235, 150), 0.02)
    # speaker stacks with woofers
    for x in (-78, -62):
        bx(p, (x - 1, x + 1), (1.2, 4.7), (-45, -43), DRK, 0.04)
        zcyl(p, x, 2.4, -43.0, -42.88, 0.7, BLK, verts=10, jit=0.02)
        zcyl(p, x, 2.4, -42.88, -42.82, 0.32, DST, verts=8, jit=0.02)
    # drum kit
    zcyl(p, -70, 2.3, -50.2, -48.8, 1.0, TEAL, verts=12, jit=0.03)
    zcyl(p, -70, 2.3, -48.8, -48.74, 0.85, WHT, verts=12, jit=0.02)
    zcyl(p, -70, 2.3, -50.3, -50.2, 1.02, YEL, verts=12, jit=0.02)
    for x in (-71.4, -68.6):
        zcyl(p, x, 3.7, -50.2, -49.5, 0.55, TEAL, verts=10, jit=0.03)
        zcyl(p, x, 3.7, -49.5, -49.46, 0.45, WHT, verts=10, jit=0.02)
    zcyl(p, -66.8, 2.4, -49.4, -48.6, 0.7, TEAL, verts=10, jit=0.03)
    for x, y in ((-73.0, 4.9), (-66.2, 4.6)):
        vcyl(p, x, 1.2, y, -50.6, 0.06, STL, verts=5, jit=0.02)
        vcyl(p, x, y, y + 0.06, -50.6, 0.9, YEL, verts=10, jit=0.02)
    vcyl(p, -70, 1.2, 1.9, -46.8, 0.5, DRK, verts=8, jit=0.03)
    # mic stand and amps
    vcyl(p, -66, 1.2, 4.0, -45.5, 0.07, STL, verts=5, jit=0.02)
    vcyl(p, -66, 1.2, 1.3, -45.5, 0.5, DST, verts=8, jit=0.02)
    vcyl(p, -66, 4.0, 4.4, -45.5, 0.25, DRK, verts=6, top_r=0.35, jit=0.02)
    for x in (-75.0, -73.0):
        bx(p, (x - 0.9, x + 0.9), (1.2, 2.7), (-51.2, -49.8), DRK, 0.04)
        bx(p, (x - 0.7, x + 0.7), (1.5, 2.3), (-49.8, -49.74), DST, 0.02)
        bx(p, (x - 0.4, x + 0.4), (2.4, 2.55), (-49.8, -49.7), RED, 0.02)


# ---- 15. GiantBurger ------------------------------------------------------------------------------------------------------------------------
def build_GiantBurger(p):
    cx, cz = 78, -49
    lathe(p, cx, cz, [(0, 0), (7.0, 0), (7.0, 0.5), (6.6, 0.8), (0, 0.8)], STL, verts=20, jit=0.04)
    for k in range(8):
        a = math.pi * k / 4 + math.pi / 8
        vcyl(p, cx + 6.2 * math.cos(a), 0.8, 1.0, cz + 6.2 * math.sin(a), 0.28, YEL, verts=6, jit=0.02)
    lathe(p, cx, cz, [(0, 0.8), (5.3, 0.8), (6.0, 1.4), (6.0, 2.4), (5.5, 2.85), (0, 2.85)], BUN, verts=20, jit=0.06)
    lathe(p, cx, cz, [(0, 2.85), (6.1, 2.85), (6.3, 3.4), (6.2, 3.9), (5.8, 4.2), (0, 4.2)], PATTY, verts=20, jit=0.12)
    bx(p, (cx - 6.4, cx + 6.4), (4.2, 4.5), (cz - 6.4, cz + 6.4), CHZ, 0.03)
    bx(p, (cx - 4.55, cx + 4.55), (4.2, 4.45), (cz - 4.55, cz + 4.55), (245, 185, 45), 0.03, rot=(0, 45, 0))
    for sx, sz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        dk.poly(p, (cx + sx * 6.4, 0, cz + sz * 6.4), [(0, 4.2, 0), (-sx * 2.2, 4.2, 0), (0, 4.2, -sz * 2.2), (-sx * 0.8, 3.3, -sz * 0.8)],
                [(0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)], CHZ, 0.03)
    star_disc(p, cx, cz, 4.5, 5.25, 6.95, 6.0, 12, GRN, 0.07)
    lathe(p, cx, cz, [(0, 5.25), (5.5, 5.25), (5.7, 5.55), (5.5, 5.85), (0, 5.85)], RED, verts=20, jit=0.05)
    prof = [(0, 5.85), (6.2, 5.85), (6.4, 6.7), (6.1, 8.2), (5.2, 9.8), (3.8, 11.0), (2.0, 11.75), (0, 12.0)]
    lathe(p, cx, cz, prof, (225, 158, 72), verts=20, jit=0.06)

    def dome_y(r):
        for (r0, y0), (r1, y1) in zip(prof[::-1], prof[::-1][1:]):
            if r0 <= r <= r1:
                return y0 + (y1 - y0) * (r - r0) / (r1 - r0)
        return 6.0
    for k, (rr, a) in enumerate(((0.0, 0.0), (2.0, 0.3), (2.0, 2.4), (2.2, 4.4), (3.6, 1.2), (3.6, 3.3), (3.5, 5.3), (4.7, 0.5),
                                 (4.7, 2.0), (4.8, 3.6), (4.6, 5.1), (5.4, 1.2), (5.5, 4.2), (5.4, 5.6))):
        sx, sz = cx + rr * math.cos(a), cz + rr * math.sin(a)
        y = dome_y(rr)
        bx(p, (sx - 0.5, sx + 0.5), (y - 0.1, y + 0.3), (sz - 0.28, sz + 0.28), (255, 240, 205), 0.02, rot=(0, math.degrees(a) + 40, 0))


PARTS = [("Paving", build_Paving), ("TruckBurger", build_TruckBurger), ("TicketBooth", build_TicketBooth),
         ("TruckTaco", build_TruckTaco), ("Tables", build_Tables), ("Lights", build_Lights), ("Fountain", build_Fountain),
         ("Umbrellas", build_Umbrellas), ("TruckPizza", build_TruckPizza), ("Planters", build_Planters), ("Bins", build_Bins),
         ("Menus", build_Menus), ("TruckDessert", build_TruckDessert), ("Stage", build_Stage), ("GiantBurger", build_GiantBurger)]


# ---- fit to the union box of the blueprint pieces --------------------------------------------------------------------
def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = list(q["Size"]); o = q["Offset"]; r = q.get("Rotation")
        if r:
            if r[2] == 90:
                s = [s[1], s[0], s[2]]
            elif r[1] == 90:
                s = [s[2], s[1], s[0]]
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
    print(f"BOX {part.id}: target stage x {lo[0]:.2f}..{hi[0]:.2f} y {lo[1]:.2f}..{hi[1]:.2f} z {lo[2]:.2f}..{hi[2]:.2f}")
    print(f"BOX {part.id}: built  stage x {bl.x:.2f}..{bh.x:.2f} y {bl.z:.2f}..{bh.z:.2f} z {bl.y:.2f}..{bh.y:.2f}")
    sc = [(th[i] - tl[i]) / (bh[i] - bl[i]) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    print(f"FIT {part.id}: scale stage xyz = {sc[0]:.3f} {sc[2]:.3f} {sc[1]:.3f}")


# reference Shiba in each preview: (x, z, facing, lift); the Shiba stands on the road side (+z) facing the camera
AZ = {}
ELEV = {"Paving": 38}
MULT = {"Paving": 1.5, "Fountain": 2.2, "Stage": 2.3, "GiantBurger": 2.4, "Lights": 2.6, "Tables": 2.2, "Planters": 2.2,
        "Bins": 2.2, "Menus": 2.2, "TicketBooth": 2.4}
SHIBA_AT = {"Paving": (30, 57, 270, 0), "TruckBurger": (-60, 33, 270, 0), "TicketBooth": (-42, 59, 270, 0),
            "TruckTaco": (75, 31, 270, 0), "Tables": (-24, 11, 270, 0), "Lights": (-41, 3, 270, 0),
            "Fountain": (62, -22, 270, 0), "Umbrellas": (29, -4, 270, 0), "TruckPizza": (-65, -4, 270, 0),
            "Planters": (-49, -36, 270, 0), "Bins": (24, -26, 270, 0), "Menus": (-21, -8, 270, 0),
            "TruckDessert": (40, -34, 270, 0), "Stage": (-70, -37, 270, 1.2), "GiantBurger": (78, -38, 270, 0)}


# ---- previews --------------------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    # the meshes are mirrored in x before export (decorkit), so the reference Shiba is placed mirrored too
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}})
    bpy.context.view_layer.update()
    for o in sb:
        if o.parent is None:
            o.location.z += lift
    bpy.context.view_layer.update()
    return sb


def drop(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def snap(objs, extra, filename, az, el, mult, size, top=False):
    low, high = dk._bounds(list(objs) + list(extra))
    g = dk.ground(low, high)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 6)
    cam = dk._camera(centre, radius * mult, az, 89 if top else el)
    cam.data.clip_start = max(0.5, radius * mult * 0.08)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    path = os.path.join(OUT, filename)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    # no flip: the mirrored scene seen from the road side is what the game shows (text reads correctly)
    print("RENDERED", path)


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


def main():
    dk.start(OUT)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    built = {}
    for pid, fn in PARTS:
        if ONLY and pid not in ONLY:
            continue
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
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 40, 2.7, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_FoodTruck.png"))


main()
