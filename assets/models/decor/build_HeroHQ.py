"""Final low-poly decor models for the theme HeroHQ (25 parts around the fifteenth Shiba, Superhero Shiba).

Usage: blender --background --factory-startup --python build_HeroHQ.py -- <outdir> [PartId ...]
Writes Decor_HeroHQ_<PartId>.fbx, preview_<PartId>.png and stage_HeroHQ.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then). Models are built WITHOUT the part's Yaw (the game applies it).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "HeroHQ"))
ONLY = ARGS[1:]
KEY = "HeroHQ"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_HeroHQ.json"))

# ---- palette (shared by all 25 parts) ------------------------------------------------------------------------------
WHT = (236, 240, 246)
OFF = (205, 210, 222)
NAVY = (28, 44, 100)
BLU = (40, 80, 200)
LBL = (92, 140, 225)
RED = (214, 44, 52)
DRED = (150, 30, 42)
YEL = (250, 205, 50)
GLD = (255, 195, 40)
GLD_ = (200, 150, 30)
GLS = (120, 215, 240)
DGR = (58, 62, 78)
BLK = (30, 30, 40)
MET = (160, 168, 182)
STE = MET
MDK = (118, 124, 140)
PAV = (96, 106, 132)
PAVD = (80, 90, 116)
GRS = (88, 150, 84)
GRD = (66, 122, 70)
STN = (150, 152, 160)
STL = (180, 182, 190)
WOOD = (130, 92, 58)
WAT = (90, 180, 240)
ROK = (90, 84, 98)
ROD = (64, 60, 74)
CRM = (232, 220, 190)
ORG = (240, 140, 40)
SKIN = (255, 205, 160)
GRN = (62, 150, 80)
PNK = (240, 120, 160)


# ---- helpers ---------------------------------------------------------------------------------------------------------
# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=10, jit=0.04):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, rot=(0, 0, 0)):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit, rot=rot)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (absolute stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def prism_z(p, tri, z0, z1, col, jit=0.04):
    """Triangular prism: tri = three (x, y) points, extruded along z from z0 to z1."""
    pts = [(a, b, z0) for a, b in tri] + [(a, b, z1) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
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


def star_poly(p, c, plane, ro, ri, thick, col, n=5, rot0=90, jit=0.03):
    """Flat n-pointed star around centre c. plane: 'xy' (faces +z), 'xz' (lies flat), 'yz' (faces +x)."""
    cx, cy, cz = c
    ring = []
    for k in range(2 * n):
        a = math.radians(rot0) + k * math.pi / n
        r = ro if k % 2 == 0 else ri
        ring.append((r * math.cos(a), r * math.sin(a)))

    def at(a, b, d):
        if plane == 'xy':
            return (cx + a, cy + b, cz + d)
        if plane == 'xz':
            return (cx + a, cy + d, cz + b)
        return (cx + d, cy + a, cz + b)
    h = thick / 2
    pts = [at(a, b, h) for a, b in ring] + [at(a, b, -h) for a, b in ring] + [at(0, 0, h), at(0, 0, -h)]
    m = 2 * n
    faces = []
    for k in range(m):
        q = (k + 1) % m
        faces += [(2 * m, k, q), (2 * m + 1, m + q, m + k), (k, m + k, m + q, q)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def torus(p, c, R, r, col, segs=16, sides=8, arc=None, scale_y=1.0, jit=0.04):
    """Ring lying flat (axis up) around centre c; arc=(b0, b1) in radians gives an open part of the tube (e.g. the top half)."""
    pts, faces = [], []
    full = arc is None
    b0, b1 = (0.0, 2 * math.pi) if full else arc
    ns = sides if full else sides + 1
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(ns):
            b = b0 + (b1 - b0) * j / sides
            rr = R + r * math.cos(b)
            pts.append((rr * math.cos(a), r * scale_y * math.sin(b), rr * math.sin(a)))
    for i in range(segs):
        for j in range(ns if full else ns - 1):
            i2 = (i + 1) % segs
            j2 = (j + 1) % ns if full else j + 1
            faces.append((i * ns + j, i2 * ns + j, i2 * ns + j2, i * ns + j2))
    return dk.poly(p, c, pts, faces, col, jit)


def letter(p, ch, x0, y0, z0, z1, w, h, t, col, mirror=False):
    """Block letter in the x-y plane (readable from +z), box strokes."""
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        if mirror:
            a, c = w - c, w - a
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        if mirror:
            a, c = w - a, w - c
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
    elif ch == 'L':
        r(0, 0, t, h); r(0, 0, w, t)
    elif ch == 'I':
        r(0, 0, w, t); r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h)
    elif ch == 'C':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t)
    elif ch == 'E':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2); r(t, 0, w, t)
    elif ch == 'J':
        r(w - t, 0, w, h); r(0, 0, w - t, t); r(0, 0, t, h * 0.32)
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
    elif ch == '9':
        r(0, h / 2, t, h); r(w - t, 0, w, h); r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(0, 0, w, t)
    elif ch == 'W':
        r(0, 0, t, h); r(w - t, 0, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h * 0.6); r(0, 0, w, t)
    elif ch == 'H':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == '-':
        r(w * 0.1, h / 2 - t / 2, w * 0.9, h / 2 + t / 2)


def text(p, s, cx, y0, z0, z1, w, h, t, gap, col, mirror=False):
    """Row of block letters centred on cx. mirror=True is for a face looking toward -z (reads left to right for a viewer there)."""
    total = len(s) * w + (len(s) - 1) * gap
    x = cx + total / 2 - w if mirror else cx - total / 2
    for ch in s:
        if ch != ' ':
            letter(p, ch, x, y0, z0, z1, w, h, t, col, mirror)
        x += -(w + gap) if mirror else (w + gap)


def window_z(p, x0, x1, y0, y1, z, d=0.16, mull=True, frame=NAVY, glass=GLS):
    """Window on a wall facing +z (wall plane at z, protrudes toward +z) or -z (negative d)."""
    zz = (z, z + d) if d > 0 else (z + d, z)
    bx(p, (x0 - 0.28, x1 + 0.28), (y0 - 0.28, y1 + 0.28), (zz[0], zz[0] + (zz[1] - zz[0]) * 0.7), frame, 0.02)
    bx(p, (x0, x1), (y0, y1), zz, glass, 0.05)
    if mull:
        xm = (x0 + x1) / 2
        bx(p, (xm - 0.1, xm + 0.1), (y0, y1), (zz[0], zz[1] + (0.04 if d > 0 else -0.04)), frame, 0.02)


def window_x(p, x, sgn, y0, y1, z0, z1, d=0.16, frame=NAVY, glass=GLS):
    """Window on a wall facing +x (sgn=1) or -x (sgn=-1), wall plane at x."""
    xx = (x, x + d * sgn)
    xx = (min(xx), max(xx))
    bx(p, xx, (y0 - 0.28, y1 + 0.28), (z0 - 0.28, z1 + 0.28), frame, 0.02)
    bx(p, (xx[0] + (0.05 if sgn > 0 else 0), xx[1] - (0 if sgn > 0 else 0.05)), (y0, y1), (z0, z1), glass, 0.05)


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




def extrude_z(p, pts, z0, z1, col, jit=0.04):
    """Convex polygon pts (x, y) extruded along z from z0 to z1."""
    n = len(pts)
    P = [(a, b, z0) for a, b in pts] + [(a, b, z1) for a, b in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return dk.poly(p, (0, 0, 0), P, faces, col, jit)


def extrude_x(p, pts, x0, x1, col, jit=0.04):
    """Convex polygon pts (y, z) extruded along x from x0 to x1."""
    n = len(pts)
    P = [(x0, a, b) for a, b in pts] + [(x1, a, b) for a, b in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return dk.poly(p, (0, 0, 0), P, faces, col, jit)


def xtaper(p, x0, x1, cy, cz, r0, r1, col, verts=10, jit=0.04):
    """Cone frustum lying along x: radius r0 at x0, r1 at x1."""
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r0, x1 - x0, col, axis='x', verts=verts, top_radius=r1, jitter=jit)


def dish(p, cx, cy, z0, z1, r_front, r_back, col, verts=12, jit=0.03):
    """Cone frustum along z (radius r_front at z1, the +z side, r_back at z0)."""
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r_front, z1 - z0, col, axis='z', verts=verts, top_radius=r_back, jitter=jit)


_letter0 = letter


def letter(p, ch, x0, y0, z0, z1, w, h, t, col, mirror=False):
    if ch not in "GMQVYX!":
        return _letter0(p, ch, x0, y0, z0, z1, w, h, t, col, mirror)
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zc, x0 + c, y0 + e, t, d, col, 0.03)
    if ch == 'G':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t); r(w - t, t, w, h / 2); r(w / 2, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'M':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * .5, h - t * .5, w / 2, h * .45); dg(w / 2, h * .45, w - t * .5, h - t * .5)
    elif ch == 'Q':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t); dg(w * .55, h * .4, w * .95, t * .2)
    elif ch == 'V':
        dg(t * .5, h, w / 2, 0); dg(w - t * .5, h, w / 2, 0)
    elif ch == 'Y':
        dg(t * .5, h, w / 2, h * .5); dg(w - t * .5, h, w / 2, h * .5); r(w / 2 - t / 2, 0, w / 2 + t / 2, h * .5)
    elif ch == 'X':
        dg(0, h, w, 0); dg(0, 0, w, h)
    elif ch == '!':
        r(w / 2 - t / 2, h * .3, w / 2 + t / 2, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, t)


def crystal(p, x, z, h, r, col, tilt=(0.0, 0.0), y0=0.0, jit=0.08):
    """Six-sided crystal: prism with a pointed, slightly leaning tip (apex at height h)."""
    pts = []
    for k in range(6):
        a = math.radians(60 * k + 15)
        pts.append((x + r * math.cos(a), y0, z + r * math.sin(a)))
    for k in range(6):
        a = math.radians(60 * k + 15)
        pts.append((x + 0.35 * tilt[0] + r * 0.9 * math.cos(a), y0 + h * 0.72, z + 0.35 * tilt[1] + r * 0.9 * math.sin(a)))
    pts.append((x + tilt[0], y0 + h, z + tilt[1]))
    faces = [tuple(range(6))]
    for k in range(6):
        q = (k + 1) % 6
        faces.append((k, q, 6 + q, 6 + k))
        faces.append((6 + k, 6 + q, 12))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


# ---- 1. Ground ---------------------------------------------------------------------------------------------------------
def build_Ground(p):
    bx(p, (-95, 95), (0, 0.3), (-65, 65), PAV, 0.05)
    # paving joints
    for x in range(-90, 95, 20):
        bx(p, (x - 0.15, x + 0.15), (0.3, 0.34), (-65, 65), PAVD, 0.02)
    for z in range(-60, 65, 20):
        bx(p, (-95, 95), (0.3, 0.34), (z - 0.15, z + 0.15), PAVD, 0.02)
    # the emblem plaza under the Shiba: navy square, red square, yellow ring, blue disc, white star
    bx(p, (2, 38), (0.3, 0.38), (-22, 14), NAVY, 0.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (20 + sx * 15.5 - 1.2, 20 + sx * 15.5 + 1.2), (0.38, 0.41), (-4 + sz * 15.5 - 1.2, -4 + sz * 15.5 + 1.2), YEL, 0.02)
    bx(p, (5.5, 34.5), (0.38, 0.42), (-18.5, 10.5), RED, 0.02)
    vcyl(p, 20, 0.42, 0.45, -4, 10.2, YEL, verts=24, jit=0.02)
    vcyl(p, 20, 0.45, 0.47, -4, 8.2, BLU, verts=24, jit=0.02)
    vcyl(p, 20, 0.47, 0.49, -4, 7.4, NAVY, verts=24, jit=0.02)
    star_poly(p, (20, 0.48, -4), 'xz', 6.8, 2.8, 0.04, WHT, n=5, rot0=90)
    # lawns with kerb, flower beds and stepping stones
    for (x0, x1, z0, z1) in ((-47, 11, -16, 20), (-75, -45, -14, 10)):
        bx(p, (x0, x1), (0.3, 0.46), (z0, z1), GRS, 0.07)
        bx(p, (x0 - 0.5, x1 + 0.5), (0.3, 0.5), (z0 - 0.5, z0), STN, 0.03)
        bx(p, (x0 - 0.5, x1 + 0.5), (0.3, 0.5), (z1, z1 + 0.5), STN, 0.03)
        bx(p, (x0 - 0.5, x0), (0.3, 0.5), (z0, z1), STN, 0.03)
        bx(p, (x1, x1 + 0.5), (0.3, 0.5), (z0, z1), STN, 0.03)
    for (x, z, c) in ((-40, -9, RED), (-28, 14, YEL), (-8, -10, PNK), (4, 12, WHT), (-14, 4, RED), (-68, 4, YEL), (-52, -8, PNK)):
        vcyl(p, x, 0.46, 0.5, z, 1.7, c, verts=8, jit=0.05)
    for i in range(6):
        bx(p, (-44 + i * 8.5, -42 + i * 8.5), (0.46, 0.5), (-4 + (i % 2) * 5, -2 + (i % 2) * 5), STL, 0.03)
    for i in range(4):
        bx(p, (-73 + i * 7, -71 + i * 7), (0.46, 0.5), (-4 + (i % 2) * 4, -2 + (i % 2) * 4), STL, 0.03)


# ---- 2. EmblemWall ---------------------------------------------------------------------------------------------------
def build_EmblemWall(p):
    bx(p, (2, 38), (0, 1), (-25, -19), STE, 0.04)
    bx(p, (4, 36), (1, 2), (-24.5, -19.5), STL, 0.04)
    bx(p, (4, 36), (1.5, 1.8), (-19.55, -19.45), YEL, 0.02)
    bx(p, (12, 28), (2, 17), (-25, -23.5), NAVY, 0.04)                      # buttress behind the shield
    # gold rim, red field, blue field, golden star
    extrude_z(p, [(11.5, 18.6), (28.5, 18.6), (28.5, 10), (20, 1.5), (11.5, 10)], -23.5, -20.7, YEL, 0.03)
    extrude_z(p, [(12.8, 17.4), (27.2, 17.4), (27.2, 10.4), (20, 3.6), (12.8, 10.4)], -20.7, -20.4, RED, 0.03)
    extrude_z(p, [(14.4, 15.8), (25.6, 15.8), (25.6, 11), (20, 5.8), (14.4, 11)], -20.4, -20.1, BLU, 0.03)
    star_poly(p, (20, 11.4, -19.95), 'xy', 3.9, 1.6, 0.3, YEL, n=5)
    # swept wings made of feathers
    roots = [10.6, 8.7, 6.9, 5.1]
    lens = [7.4, 6.9, 5.9, 4.8]
    for i in range(4):
        for s in (-1, 1):
            r, L = roots[i], lens[i]
            pts = [(11.6, r + 1.1), (11.6 - L, r + 3.4), (11.6 - L, r + 1.3), (11.6, r - 1.1)]
            if s > 0:
                pts = [(40 - a, b) for a, b in pts][::-1]
            col = NAVY if i % 2 == 0 else BLU
            extrude_z(p, pts, -23.2, -21.6 - 0.15 * i, col, 0.04)
            tip = [(11.6 - L, r + 3.4), (11.6 - L, r + 1.3), (11.6 - L + 0.9, r + 1.4), (11.6 - L + 0.9, r + 3.0)]
            if s > 0:
                tip = [(40 - a, b) for a, b in tip][::-1]
            extrude_z(p, tip, -23.2, -21.6 - 0.15 * i, LBL, 0.04)
    # golden crest
    bx(p, (16, 24), (18.6, 19.2), (-23, -21.2), YEL, 0.03)
    for k in range(3):
        a = 16 + k * 2.667
        extrude_z(p, [(a, 19.2), (a + 2.667, 19.2), (a + 1.333, 20)], -23, -21.2, YEL, 0.03)


# ---- 3. Tower ------------------------------------------------------------------------------------------------------------
def build_Tower(p):
    bx(p, (63, 89), (0, 11.2), (-58, -34), NAVY, 0.04)
    bx(p, (63, 89), (11.2, 12), (-58, -34), RED, 0.03)
    bx(p, (66, 86), (12, 25.2), (-55, -37), BLU, 0.04)
    bx(p, (66, 86), (25.2, 26), (-55, -37), YEL, 0.03)
    bx(p, (69, 83), (26, 33), (-53, -39), BLU, 0.04)
    # entrance
    bx(p, (72.2, 79.8), (0, 5.2), (-34.3, -34), STE, 0.03)
    bx(p, (73, 79), (0, 4.6), (-34.6, -34.3), GLS, 0.04)
    bx(p, (75.85, 76.15), (0, 4.6), (-34.65, -34.3), NAVY, 0.02)
    bx(p, (72.2, 79.8), (5.2, 5.7), (-35.4, -34), RED, 0.03)
    # window ribbons (front and both sides) on the base
    for (xa, xb) in ((64.5, 71.5), (80.5, 87.5)):
        for (ya, yb) in ((5.6, 7.6), (8.6, 10.4)):
            bx(p, (xa, xb), (ya, yb), (-34.15, -34), GLS, 0.05)
    for sx in (63, 89):
        for (ya, yb) in ((5.6, 7.6), (8.6, 10.4)):
            for zc in (-52, -46, -40):
                bx(p, (sx - 0.15, sx + 0.15) if sx == 63 else (sx - 0.15, sx + 0.15), (ya, yb), (zc - 2, zc + 2), GLS, 0.05)
    # middle block: HQ letters and window strips
    text(p, "HQ", 76, 16.4, -37.35, -37.0, 3.4, 5.0, 1.0, 1.0, YEL)
    for xa in (68, 82):
        bx(p, (xa, xa + 2.2), (14, 24), (-37.15, -37), GLS, 0.05)
    for sx in (66, 86):
        for zc in (-51, -46, -41):
            bx(p, (sx - 0.15, sx + 0.15), (14, 24), (zc - 1, zc + 1), GLS, 0.05)
    # crown block
    bx(p, (70.2, 81.8), (28, 31.4), (-39.15, -39), GLS, 0.05)
    for sx in (69, 83):
        bx(p, (sx - 0.15, sx + 0.15), (28, 31.4), (-50, -42), GLS, 0.05)
    # helipad with H
    bx(p, (67.5, 84.5), (33, 33.8), (-54.5, -37.5), STE, 0.03)
    vcyl(p, 76, 33.8, 33.84, -46, 6.4, WHT, verts=20, jit=0.01)
    vcyl(p, 76, 33.84, 33.88, -46, 5.7, DGR, verts=20, jit=0.01)
    for (xa, xb, za, zb) in ((73.4, 74.2, -49, -43), (77.8, 78.6, -49, -43), (74.2, 77.8, -46.4, -45.6)):
        bx(p, (xa, xb), (33.88, 33.95), (za, zb), YEL, 0.01)
    for (x, z) in ((68.2, -53.2), (83.8, -53.2), (68.2, -38.8), (83.8, -38.8)):
        bx(p, (x - 0.35, x + 0.35), (33.8, 34.5), (z - 0.35, z + 0.35), RED, 0.02)
    # radio spire with bands, dish and a golden tip
    for k, (y0, y1, c) in enumerate(((33.8, 36, WHT), (36, 38, RED), (38, 40, WHT), (40, 42, RED), (42, 44.4, WHT))):
        vcyl(p, 76, y0, y1, -46, 0.5, c, verts=8, jit=0.02)
    bx(p, (75.2, 76.8), (36.5, 37.1), (-46.8, -45.2), STE, 0.02)
    ball(p, (76, 44.4, -46), 0.6, YEL, subdiv=1, jit=0.02)


# ---- 4. Billboard ---------------------------------------------------------------------------------------------------------
def build_Billboard(p):
    bx(p, (-90, -66), (10.45, 20.4), (55.6, 56.7), BLU, 0.04)           # board
    bx(p, (-90, -66), (10.3, 10.6), (55.3, 56.6), DGR, 0.03)           # rear ribs
    for x in (-87, -81, -75, -69):
        bx(p, (x - 0.25, x + 0.25), (10.45, 20.4), (55.3, 55.6), DGR, 0.03)
    bx(p, (-90, -66), (9.95, 10.45), (55.4, 58.4), DGR, 0.03)           # catwalk
    bx(p, (-90, -66), (10.45, 11.2), (58.25, 58.4), MDK, 0.03)
    for x in (-90, -84, -78, -72, -66.25):
        bx(p, (x, x + 0.25), (10.45, 11.2), (58.15, 58.4), MDK, 0.03)
    bx(p, (-90, -66), (20.4, 21.2), (55.4, 57.8), DGR, 0.03)            # lamp canopy
    for x in (-87, -80, -73, -67.8):
        bx(p, (x - 0.5, x + 0.5), (19.7, 20.4), (57.3, 57.8), YEL, 0.02)
    # red frame on the face
    bx(p, (-90, -66), (10.45, 11.0), (56.7, 56.95), RED, 0.02)
    bx(p, (-90, -66), (19.85, 20.4), (56.7, 56.95), RED, 0.02)
    bx(p, (-90, -89.5), (11.0, 19.85), (56.7, 56.95), RED, 0.02)
    bx(p, (-66.5, -66), (11.0, 19.85), (56.7, 56.95), RED, 0.02)
    text(p, "HERO HQ", -78, 12.7, 56.7, 57.1, 2.2, 5.0, 0.95, 0.6, YEL)
    star_poly(p, (-87.4, 15.2, 56.8), 'xy', 1.1, 0.5, 0.2, WHT, n=5)
    star_poly(p, (-68.6, 15.2, 56.8), 'xy', 1.1, 0.5, 0.2, WHT, n=5)
    for x in (-85, -71):                                                   # legs, plates, braces
        vcyl(p, x, 0.4, 10, 56, 0.8, STE, verts=8, jit=0.03)
        bx(p, (x - 1.6, x + 1.6), (0, 0.4), (55.3, 56.9), DGR, 0.03)
        bx(p, (x - 0.15, x + 0.15), (3, 9), (57.0, 57.4), MDK, 0.02)
    bar(p, (-85, 0.6, 56.9), (-78, 9.9, 56.6), 0.4, MDK)
    bar(p, (-71, 0.6, 56.9), (-78, 9.9, 56.6), 0.4, MDK)


# ---- 5. Jet --------------------------------------------------------------------------------------------------------------
def build_Jet(p):
    bx(p, (60, 84), (0, 0.5), (18, 38), DGR, 0.05)
    for k in range(6):
        bx(p, (61 + k * 3.7, 63.4 + k * 3.7), (0.5, 0.55), (27.85, 28.15), YEL, 0.02)
    for z in (18.7, 37.3):
        bx(p, (60.5, 83.5), (0.5, 0.55), (z - 0.15, z + 0.15), WHT, 0.02)
    for x in (60.7, 83.3):
        bx(p, (x - 0.15, x + 0.15), (0.5, 0.55), (18.7, 37.3), WHT, 0.02)
    # fuselage
    xtaper(p, 59.8, 66, 4.2, 28, 0.7, 1.8, WHT, verts=10)
    xcyl(p, 66, 75, 4.2, 28, 1.8, WHT, verts=10)
    xtaper(p, 75, 82.5, 4.2, 28, 1.8, 0.4, RED, verts=10)
    bx(p, (62, 75), (3.2, 3.7), (26.15, 29.85), BLU, 0.03)
    bx(p, (67, 74), (4.7, 5.3), (26.1, 29.9), GLS, 0.05)
    ball(p, (76.2, 5.6, 28), 1.25, GLS, scale=(1.5, 0.75, 0.9), subdiv=1, jit=0.04)
    # swept wings, engines
    for s in (-1, 1):
        zr, zt = 28 + s * 1.6, 28 + s * 8.5
        pts = [(75, 3.6, zr), (67, 3.6, zr), (64.5, 3.6, zt), (68.5, 3.6, zt)]
        top = [(a, 4.0, c) for a, _, c in pts]
        hexa(p, pts + top, WHT, 0.03)
        pts2 = [(68.6, 3.55, 28 + s * 5.2), (65.7, 3.55, 28 + s * 5.2), (64.5, 3.55, zt), (68.5, 3.55, zt)]
        hexa(p, pts2 + [(a, 4.05, c) for a, _, c in pts2], BLU, 0.03)
        bx(p, (64.5, 68.5), (3.5, 4.2), (zt - 0.3 if s > 0 else zt, zt if s > 0 else zt + 0.3), RED, 0.02)
        xcyl(p, 67, 72, 3.0, 28 + s * 3.6, 0.8, DGR, verts=8, jit=0.03)
        xcyl(p, 72, 72.4, 3.0, 28 + s * 3.6, 0.6, BLK, verts=8, jit=0.02)
        xcyl(p, 66.6, 67, 3.0, 28 + s * 3.6, 0.85, RED, verts=8, jit=0.02)
        # tail plane
        pt = [(63.5, 5.0, 28 + s * 0.6), (61, 5.0, 28 + s * 0.6), (60.2, 5.0, 28 + s * 3.6), (61.6, 5.0, 28 + s * 3.6)]
        hexa(p, pt + [(a, 5.3, c) for a, _, c in pt], BLU, 0.03)
    extrude_z(p, [(65, 5.4), (61.5, 5.4), (59.5, 10.7), (61.3, 10.7)], 27.6, 28.4, RED, 0.03)
    extrude_z(p, [(62.6, 8.6), (60.6, 8.6), (60.2, 9.9), (61.2, 9.9)], 27.5, 28.5, BLU, 0.03)
    # landing gear
    bx(p, (75.6, 76.4), (0.5, 2.5), (27.6, 28.4), DGR, 0.02)
    zcyl(p, 76, 0.95, 27.3, 28.7, 0.45, BLK, verts=8, jit=0.02)
    for zc in (24.5, 31.5):
        bx(p, (65.6, 66.4), (0.5, 3.6), (zc - 0.4, zc + 0.4), DGR, 0.02)
        zcyl(p, 66, 0.95, zc - 0.5, zc + 0.5, 0.45, BLK, verts=8, jit=0.02)
    # star on the tail fin side
    star_poly(p, (63, 7.4, 28.45), 'xy', 0.9, 0.4, 0.1, WHT, n=5)


# ---- 6. Garage ---------------------------------------------------------------------------------------------------------------
def build_Garage(p):
    bx(p, (-57, -35), (0, 0.5), (35, 53), (168, 170, 180), 0.05)
    bx(p, (-55, -37), (0.5, 0.54), (37.6, 50), (122, 128, 144), 0.03)
    bx(p, (-56, -36), (0.5, 10), (37, 38.2), STE, 0.04)                            # back wall
    bx(p, (-56, -54.8), (0.5, 10), (37, 50.6), STE, 0.04)                          # side walls
    bx(p, (-37.2, -36), (0.5, 10), (37, 50.6), STE, 0.04)
    bx(p, (-57, -35), (10, 10.8), (36.6, 50.2), RED, 0.04)                         # roof
    bx(p, (-57, -35), (10, 10.8), (50.2, 50.6), YEL, 0.03)
    bx(p, (-55.4, -36.6), (7.2, 10), (50.2, 50.6), NAVY, 0.03)                     # header with the sign
    text(p, "GARAGE", -46, 7.7, 50.6, 50.9, 1.5, 1.8, 0.4, 0.45, WHT)
    bx(p, (-54, -38), (3.4, 9), (38.2, 38.4), DGR, 0.03)                           # tool wall
    for k, c in enumerate((RED, YEL, STE, ORG, BLU, YEL, RED, STE)):
        bx(p, (-53.4 + k * 1.9, -52.4 + k * 1.9), (5.0 + (k % 3) * 0.9, 7.6 + (k % 3) * 0.5), (38.4, 38.6), c, 0.03)
    bx(p, (-55.2, -52.4), (0.5, 3.4), (38.6, 41.2), RED, 0.04)                     # tool chest
    for y in (1.2, 2.0, 2.8):
        bx(p, (-55.0, -52.6), (y, y + 0.1), (41.2, 41.3), DGR, 0.02)
    for k in range(3):
        vcyl(p, -39.4, 0.5 + k * 0.95, 1.45 + k * 0.95, 40.2, 1.15, BLK, verts=9, jit=0.03)
    # the blue sports car, nose toward the road
    bx(p, (-48.9, -43.1), (1.0, 1.5), (39.8, 50.2), BLK, 0.02)
    bx(p, (-48.9, -43.1), (1.5, 2.8), (39.6, 50.4), BLU, 0.03)
    hexa(p, [(-48.1, 2.8, 41.4), (-43.9, 2.8, 41.4), (-43.9, 2.8, 46.6), (-48.1, 2.8, 46.6),
             (-47.5, 4.1, 42.4), (-44.5, 4.1, 42.4), (-44.5, 4.1, 45.2), (-47.5, 4.1, 45.2)], GLS, 0.03)
    bx(p, (-47.6, -44.4), (4.1, 4.25), (42.3, 45.3), BLU, 0.03)
    bx(p, (-46.5, -45.5), (2.8, 2.86), (45.5, 50.2), YEL, 0.02)
    bx(p, (-46.5, -45.5), (2.8, 2.86), (40, 42), YEL, 0.02)
    bx(p, (-48.3, -43.7), (3.5, 3.7), (39.6, 40.9), BLU, 0.03)
    for x in (-48.0, -44.0):
        bx(p, (x - 0.15, x + 0.15), (2.8, 3.5), (40.0, 40.3), DGR, 0.02)
    for x in (-48.5, -43.5):
        bx(p, (x - 0.5, x + 0.5), (2.0, 2.5), (50.3, 50.45), YEL, 0.02)
        bx(p, (x - 0.5, x + 0.5), (2.0, 2.5), (39.55, 39.7), RED, 0.02)
    for (xa, xb) in ((-49.0, -48.1), (-43.9, -43.0)):
        for zc in (42.2, 48.2):
            xcyl(p, xa, xb, 1.45, zc, 0.95, BLK, verts=8, jit=0.02)
            xcyl(p, xa - 0.04 if xa < -46 else xa, xb if xa < -46 else xb + 0.04, 1.45, zc, 0.5, MET, verts=6, jit=0.02)


# ---- 7. Course ---------------------------------------------------------------------------------------------------------------
def build_Course(p):
    bx(p, (-92, -68), (0, 0.3), (26, 42), RED, 0.05)
    for (xa, xb, za, zb) in ((-91.5, -68.5, 26.5, 26.9), (-91.5, -68.5, 41.1, 41.5), (-91.5, -91.1, 26.5, 41.5), (-68.9, -68.5, 26.5, 41.5)):
        bx(p, (xa, xb), (0.3, 0.34), (za, zb), WHT, 0.02)
    # climbing wall with holds
    bx(p, (-90, -88), (0, 3.2), (33, 39), YEL, 0.05)
    bx(p, (-90.4, -87.6), (3.2, 3.5), (32.8, 39.2), DGR, 0.03)
    for k, (z, y, c) in enumerate(((33.8, 0.8, RED), (35.2, 1.5, BLU), (36.6, 0.7, GRN), (37.9, 1.6, ORG), (34.5, 2.4, WHT),
                                   (36.0, 2.7, RED), (37.6, 2.5, BLU), (38.4, 0.9, YEL))):
        bx(p, (-88, -87.55), (y - 0.25, y + 0.25), (z - 0.3, z + 0.3), c, 0.03)
    # pull-up frame
    for x in (-84, -76):
        bx(p, (x - 0.4, x + 0.4), (0, 6), (27.6, 28.4), STE, 0.03)
        bx(p, (x - 1.1, x + 1.1), (0.3, 0.8), (27, 29), DGR, 0.03)
    xcyl(p, -84.4, -75.6, 6.0, 28, 0.3, MDK, verts=8, jit=0.02)
    # tyres
    for (x, z) in ((-84, 33), (-81, 36), (-86, 38.8)):
        torus(p, (x, 0.7, z), 1.0, 0.5, DGR, segs=10, sides=6, scale_y=1.4, jit=0.04)
    # balance beam
    bx(p, (-82, -72), (0.5, 1.3), (37.3, 38.7), WOOD, 0.05)
    for x in (-81.5, -77, -72.6):
        bx(p, (x - 0.5, x + 0.5), (0.3, 0.5), (37, 39), DGR, 0.03)
    # punching bag with its gantry
    vcyl(p, -70, 0.8, 4.4, 30, 0.9, ORG, verts=10, jit=0.05)
    vcyl(p, -70, 4.2, 4.4, 30, 0.95, DGR, verts=10, jit=0.02)
    bx(p, (-70.1, -69.9), (4.4, 5.1), (29.9, 30.1), MDK, 0.02)
    bx(p, (-70.4, -69.6), (0.3, 5.5), (31.2, 32), DGR, 0.03)
    bx(p, (-70.4, -69.6), (5.0, 5.5), (29.8, 32), DGR, 0.03)
    # dumbbell rack and cones
    bx(p, (-91, -89), (0.3, 1.3), (27, 30), DGR, 0.03)
    for k in range(3):
        xcyl(p, -90.8, -89.2, 1.6, 27.5 + k * 1.0, 0.3, MDK, verts=6, jit=0.02)
        ball(p, (-90.8, 1.6, 27.5 + k * 1.0), 0.45, BLK, subdiv=1, jit=0.02)
        ball(p, (-89.2, 1.6, 27.5 + k * 1.0), 0.45, BLK, subdiv=1, jit=0.02)
    for (x, z) in ((-72, 27.5), (-74.5, 27.5), (-72, 40.5), (-74.5, 40.5)):
        dk.cone(p, (x, 0.3, z), 0.55, 1.2, ORG, verts=7, jitter=0.03)


# ---- 8. Lab -------------------------------------------------------------------------------------------------------------------
def build_Lab(p):
    bx(p, (-78, -62), (0, 4.4), (3, 17), WHT, 0.04)
    bx(p, (-78, -62), (4.4, 5), (3, 17), BLU, 0.03)
    vcyl(p, -70, 5, 5.4, 10, 6.8, MDK, verts=16, jit=0.03)
    ball(p, (-70, 5.2, 10), 6.5, STE, scale=(1, 4.8 / 6.5, 1), subdiv=2, jit=0.05)
    bx(p, (-70.8, -69.2), (5.6, 9.8), (11.5, 16.4), DGR, 0.03)                    # observatory slit
    bx(p, (-70.5, -69.5), (5.9, 9.5), (12, 16.55), GLS, 0.03)
    vcyl(p, -70, 5.2, 15.5, 10, 0.4, STE, verts=8, jit=0.02)
    ball(p, (-70, 15.5, 10), 0.5, RED, subdiv=1, jit=0.02)
    dish(p, -70, 12.6, 10.3, 11.3, 1.3, 0.3, WHT, verts=10)
    # annex
    bx(p, (-79.5, -74.5), (0, 3.6), (12.5, 17.5), BLU, 0.04)
    bx(p, (-79.5, -74.5), (3.6, 4), (12.5, 17.5), STE, 0.03)
    bx(p, (-78.3, -75.7), (0, 2.8), (17.5, 17.7), DGR, 0.03)
    # main building details
    bx(p, (-71.6, -68.4), (0.5, 3.2), (17, 17.2), NAVY, 0.03)
    bx(p, (-71.2, -68.8), (0.5, 3.0), (17.2, 17.28), GLS, 0.04)
    window_z(p, -74, -72.6, 1.5, 3.3, 17, d=0.15, mull=False)
    window_z(p, -67.6, -66.5, 1.5, 3.3, 17, d=0.15, mull=False)
    window_x(p, -78, -1, 1.3, 3.4, 5, 8, d=0.15)
    window_x(p, -78, -1, 1.3, 3.4, 11, 14, d=0.15)
    window_x(p, -62, 1, 1.3, 3.4, 5, 8, d=0.15)
    # water tank
    vcyl(p, -64, 0, 6.8, 16, 1.65, DGR, verts=10, jit=0.04)
    vcyl(p, -64, 1.4, 1.9, 16, 1.7, STE, verts=10, jit=0.02)
    vcyl(p, -64, 4.4, 4.9, 16, 1.7, STE, verts=10, jit=0.02)
    ball(p, (-64, 6.7, 16), 1.65, DGR, scale=(1, 0.3, 1), subdiv=1, jit=0.03)
    bx(p, (-63.9, -63.4), (0, 6), (14.3, 14.6), MDK, 0.02)
    bx(p, (-67.5, -65, ), (2.0, 2.4), (15.8, 16.2), MDK, 0.02)                    # pipe to the building


# ---- 9. Fountain -----------------------------------------------------------------------------------------------------------
def build_Fountain(p):
    vcyl(p, -6, 0, 1.2, 2, 9, STN, verts=16, jit=0.04)
    torus(p, (-6, 1.0, 2), 8.5, 0.45, STL, segs=16, sides=6, jit=0.03)
    vcyl(p, -6, 1.0, 1.3, 2, 8.0, WAT, verts=16, jit=0.03)
    vcyl(p, -6, 1.2, 2.2, 2, 2.2, STN, verts=10, jit=0.03)
    vcyl(p, -6, 2.2, 5.8, 2, 1.2, STN, verts=8, jit=0.03)
    vcyl(p, -6, 5.8, 6.8, 2, 1.2, STN, verts=12, top_r=3.5, jit=0.03)
    vcyl(p, -6, 6.6, 6.85, 2, 3.2, WAT, verts=12, jit=0.02)
    ball(p, (-6, 8.6, 2), 1.5, WAT, scale=(1, 4 / 3, 1), subdiv=1, jit=0.03)
    for k in range(6):                                                            # arching jets
        a = math.radians(60 * k + 20)
        bar(p, (-6 + 0.5 * math.cos(a), 9.4, 2 + 0.5 * math.sin(a)), (-6 + 3.1 * math.cos(a), 6.9, 2 + 3.1 * math.sin(a)), 0.35, WAT, 0.03)
    for k in range(8):
        a = math.radians(45 * k)
        dk.cone(p, (-6 + 5.6 * math.cos(a), 1.3, 2 + 5.6 * math.sin(a)), 0.4, 1.5, WAT, verts=6, jitter=0.03)
    for (xa, xb, back) in ((-18.3, -16.7, -18.3), (4.7, 6.3, 6.3)):
        for z0, z1 in ((-2, -1.2), (5.2, 6)):
            bx(p, (xa, xb), (0, 0.9), (z0, z1), STN, 0.03)
        for k in range(3):
            bx(p, (xa, xb), (0.9 + 0.0, 1.05), (-1.2 + k * 2.13, -0.4 + k * 2.13), WOOD, 0.05)
        bx(p, (back, back + (0.3 if back < 0 else -0.3)) if back < 0 else (back - 0.3, back), (1.05, 1.4), (-2, 6), WOOD, 0.05)


# ---- 10. Banners -----------------------------------------------------------------------------------------------------------
def build_Banners(p):
    for k, (x, z, c) in enumerate(((-6, 44, RED), (0, 41, BLU), (5, 43, RED), (10, 40.5, BLU))):
        vcyl(p, x, 0, 13.5, z, 0.35, STE, verts=8, jit=0.03)
        ball(p, (x, 13.6, z), 0.4, GLD, subdiv=1, jit=0.02)
        bx(p, (x, x + 3.6), (13.1, 13.4), (z - 0.1, z + 0.1), STE, 0.02)
        extrude_z(p, [(x + 0.1, 13.1), (x + 3.5, 13.1), (x + 3.5, 9.4), (x + 1.8, 8.5), (x + 0.1, 9.4)], z - 0.1, z + 0.1, c, 0.04)
        bx(p, (x + 0.1, x + 3.5), (12.1, 12.5), (z - 0.12, z + 0.12), YEL, 0.02)
        star_poly(p, (x + 1.8, 10.6, z + 0.1), 'xy', 1.1, 0.5, 0.06, WHT, n=5)
        star_poly(p, (x + 1.8, 10.6, z - 0.1), 'xy', 1.1, 0.5, 0.06, WHT, n=5)


# ---- 11. Comic -----------------------------------------------------------------------------------------------------------------
def build_Comic(p):
    bx(p, (-31, -17), (0, 8), (51, 61), YEL, 0.04)
    bx(p, (-31.7, -16.3), (8, 8.8), (50.3, 61.7), RED, 0.04)
    bx(p, (-31.7, -16.3), (8.0, 8.25), (61.7, 61.95), WHT, 0.02)
    # door, windows with posters
    bx(p, (-26.7, -23.3), (0, 5.2), (61, 61.15), NAVY, 0.03)
    bx(p, (-26.3, -23.7), (0, 4.8), (61.15, 61.3), BLU, 0.03)
    bx(p, (-26.0, -24.0), (2.2, 4.4), (61.3, 61.4), GLS, 0.04)
    window_z(p, -29.8, -27.4, 1.8, 5.4, 61, d=0.15, mull=False)
    window_z(p, -20.6, -18.2, 1.8, 5.4, 61, d=0.15, mull=False)
    for (x0, c0, c1) in ((-29.6, RED, WHT), (-20.4, BLU, YEL)):
        bx(p, (x0, x0 + 1.0), (2.2, 4.6), (61.15, 61.22), c0, 0.03)
        bx(p, (x0 + 1.2, x0 + 2.0), (2.6, 4.2), (61.15, 61.22), c1, 0.03)
    # striped awning
    for i in range(6):
        x0 = -30 + 2 * i
        c = RED if i % 2 == 0 else WHT
        bot = [(x0, 5.75, 60.5), (x0 + 2, 5.75, 60.5), (x0 + 2, 5.1, 63.5), (x0, 5.1, 63.5)]
        hexa(p, bot + [(a, b + 0.2, c2) for a, b, c2 in bot], c, 0.03)
    # roof-top speech bubble with COMIC
    ring = [(-28.4, 13), (-19.6, 13), (-19, 12.4), (-19, 10.4), (-19.6, 9.8), (-28.4, 9.8), (-29, 10.4), (-29, 12.4)]
    extrude_z(p, ring, 56.0, 56.8, NAVY, 0.02)
    inner = [(-28.2, 12.8), (-19.8, 12.8), (-19.2, 12.3), (-19.2, 10.5), (-19.8, 10.0), (-28.2, 10.0), (-28.8, 10.5), (-28.8, 12.3)]
    extrude_z(p, inner, 56.8, 57.1, WHT, 0.02)
    extrude_z(p, [(-27.4, 10.0), (-25.2, 10.0), (-27.9, 9.0)], 56.0, 57.1, NAVY, 0.02)
    extrude_z(p, [(-27.2, 10.1), (-25.5, 10.1), (-27.5, 9.3)], 57.0, 57.12, WHT, 0.02)
    text(p, "COMIC", -23.9, 10.5, 57.1, 57.4, 1.55, 2.0, 0.42, 0.35, RED)
    bx(p, (-19, -17.4), (8.8, 9.8), (52, 54), DGR, 0.03)                           # roof vent
    vcyl(p, -28.4, 0, 3, 62.2, 0.35, DGR, verts=6, jit=0.02)                       # comic rack
    for k, c in enumerate((RED, BLU, YEL, GRN)):
        bx(p, (-29.1, -27.7), (0.9 + k * 0.5, 1.3 + k * 0.5), (62.0 + (k % 2) * 0.2, 62.4 + (k % 2) * 0.2), c, 0.03)


# ---- 12. Truck -----------------------------------------------------------------------------------------------------------------
def build_Truck(p):
    bx(p, (38.5, 53.5), (0.7, 1.9), (7.4, 12.6), DGR, 0.04)
    bx(p, (39, 41), (1.9, 6.9), (7, 13), YEL, 0.04)                                # body around the serving window
    bx(p, (47, 49), (1.9, 6.9), (7, 13), YEL, 0.04)
    bx(p, (41, 47), (1.9, 3.4), (7, 13), YEL, 0.04)
    bx(p, (41, 47), (5.6, 6.9), (7, 13), YEL, 0.04)
    bx(p, (41, 47), (3.4, 5.6), (7, 7.4), CRM, 0.03)
    bx(p, (41, 47), (3.3, 3.5), (13, 13.9), WOOD, 0.04)                            # counter
    for (xa, xb, ya, yb) in ((40.8, 47.2, 5.6, 5.9), (40.8, 47.2, 3.1, 3.3), (40.8, 41, 3.3, 5.6), (47, 47.2, 3.3, 5.6)):
        bx(p, (xa, xb), (ya, yb), (13, 13.15), RED, 0.02)
    ball(p, (43, 3.9, 13.5), 0.45, ORG, subdiv=1, jit=0.04)                        # snacks on the counter
    ball(p, (44.6, 3.85, 13.5), 0.4, RED, subdiv=1, jit=0.04)
    bx(p, (45.5, 46.5), (3.5, 3.9), (13.2, 13.7), CRM, 0.03)
    bx(p, (47.3, 48.7), (3.2, 6.2), (13, 13.1), DGR, 0.02)                         # menu board
    for k in range(3):
        bx(p, (47.5, 48.5), (3.6 + k * 0.8, 3.8 + k * 0.8), (13.1, 13.15), WHT, 0.02)
    bx(p, (39, 49), (6.9, 7.2), (7, 13), DRED, 0.03)                               # roof and sign
    bx(p, (41, 47), (7.3, 8.7), (9.6, 10.4), RED, 0.03)
    text(p, "SNACK", 44, 7.5, 10.4, 10.6, 0.95, 1.0, 0.25, 0.18, WHT)
    bx(p, (47.8, 48.8), (7.2, 7.8), (8, 9.5), MDK, 0.03)                           # roof vent
    for i in range(4):                                                             # awning
        x0 = 40 + 2 * i
        c = RED if i % 2 == 0 else WHT
        bot = [(x0, 6.5, 13), (x0 + 2, 6.5, 13), (x0 + 2, 5.8, 15.1), (x0, 5.8, 15.1)]
        hexa(p, bot + [(a, b + 0.4, c2) for a, b, c2 in bot], c, 0.03)
    # cab
    bx(p, (49.8, 54.2), (1.6, 5.2), (7.2, 12.8), BLU, 0.04)
    bx(p, (54.2 - 0.1, 54.2), (3.2, 4.8), (7.8, 12.2), GLS, 0.04)
    bx(p, (50.4, 53.4), (3.2, 4.8), (12.8, 12.92), GLS, 0.04)
    bx(p, (50.4, 53.4), (3.2, 4.8), (7.08, 7.2), GLS, 0.04)
    bx(p, (53.6, 54.2), (1.6, 2.4), (7.4, 12.6), DGR, 0.03)
    for z in (7.9, 12.1):
        bx(p, (53.9, 54.2), (2.5, 3.0), (z - 0.4, z + 0.4), YEL, 0.02)
    # wheels
    for x in (41.5, 51):
        for (za, zb, ha, hb) in ((6.85, 7.6, 6.8, 7.0), (12.4, 13.15, 13.0, 13.2)):
            zcyl(p, x, 1.2, za, zb, 1.2, BLK, verts=10, jit=0.02)
            zcyl(p, x, 1.2, ha, hb, 0.6, MET, verts=7, jit=0.02)


# ---- 13. Ring -----------------------------------------------------------------------------------------------------------------
def build_Ring(p):
    cx, cz = -20, 38
    bx(p, (-26.5, -13.5), (0, 0.9), (31.5, 44.5), NAVY, 0.04)
    for x in (-24, -20, -16):
        bx(p, (x - 0.15, x + 0.15), (0.2, 0.7), (44.4, 44.55), WHT, 0.02)
    bx(p, (-26.2, -13.8), (0.9, 1.5), (31.8, 44.2), LBL, 0.04)
    vcyl(p, cx, 1.5, 1.53, cz, 4.6, WHT, verts=20, jit=0.01)
    vcyl(p, cx, 1.53, 1.56, cz, 4.0, BLU, verts=20, jit=0.01)
    star_poly(p, (cx, 1.58, cz), 'xz', 3.5, 1.5, 0.04, RED, n=5, rot0=90)
    posts = ((-25.8, 32.2, BLU), (-14.2, 32.2, RED), (-25.8, 43.8, RED), (-14.2, 43.8, BLU))
    for (x, z, c) in posts:
        bx(p, (x - 0.4, x + 0.4), (1.5, 6.5), (z - 0.4, z + 0.4), STE, 0.03)
        bx(p, (x - 0.55, x + 0.55), (1.9, 5.9), (z - 0.55, z + 0.55), c, 0.04)
    rc = (RED, WHT, BLU)
    for k, y in enumerate((2.8, 4.0, 5.2)):
        c = rc[k]
        bx(p, (-25.4, -14.6), (y - 0.15, y + 0.15), (32.05, 32.35), c, 0.02)
        bx(p, (-25.4, -14.6), (y - 0.15, y + 0.15), (43.65, 43.95), c, 0.02)
        bx(p, (-25.95, -25.65), (y - 0.15, y + 0.15), (32.6, 43.4), c, 0.02)
        bx(p, (-14.35, -14.05), (y - 0.15, y + 0.15), (32.6, 43.4), c, 0.02)
    for (x, z) in ((-23, 40.4), (-22.1, 41.2)):
        ball(p, (x, 2.1, z), 0.55, RED, scale=(1, 0.8, 1.2), subdiv=1, jit=0.04)


# ---- 14. Searchlight -------------------------------------------------------------------------------------------------------
def build_Searchlight(p):
    bx(p, (-12, -4), (0, 1), (-32, -24), STE, 0.04)
    cx, cz = -8, -28

    def hw(y):
        return 3.3 - 1.1 * (y - 1) / 15.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            bar(p, (cx + sx * 3.3, 1, cz + sz * 3.3), (cx + sx * 2.2, 16, cz + sz * 2.2), 0.7, DGR)
    levels = (1, 5, 9, 13, 16)
    for y in levels[1:4]:
        w = hw(y)
        bar(p, (cx - w, y, cz - w), (cx + w, y, cz - w), 0.4, MDK)
        bar(p, (cx - w, y, cz + w), (cx + w, y, cz + w), 0.4, MDK)
        bar(p, (cx - w, y, cz - w), (cx - w, y, cz + w), 0.4, MDK)
        bar(p, (cx + w, y, cz - w), (cx + w, y, cz + w), 0.4, MDK)
    for i in range(4):
        y0, y1 = levels[i], levels[i + 1]
        w0, w1 = hw(y0), hw(y1)
        f = 1 if i % 2 == 0 else -1
        bar(p, (cx - f * w0, y0, cz + w0), (cx + f * w1, y1, cz + w1), 0.3, YEL)
        bar(p, (cx + f * w0, y0, cz - w0), (cx - f * w1, y1, cz - w1), 0.3, YEL)
        bar(p, (cx - w0, y0, cz - f * w0), (cx - w1, y1, cz + f * w1), 0.3, YEL)
        bar(p, (cx + w0, y0, cz + f * w0), (cx + w1, y1, cz - f * w1), 0.3, YEL)
    bx(p, (-12, -4), (16, 16.8), (-32, -24), STE, 0.04)
    for (x, z) in ((-11.7, -31.7), (-4.3, -31.7), (-11.7, -24.3), (-4.3, -24.3)):
        bx(p, (x - 0.15, x + 0.15), (16.8, 17.8), (z - 0.15, z + 0.15), YEL, 0.02)
    bx(p, (-11.85, -4.15), (17.5, 17.7), (-31.85, -31.55), YEL, 0.02)
    bx(p, (-11.85, -11.55), (17.5, 17.7), (-31.55, -24.15), YEL, 0.02)
    bx(p, (-4.45, -4.15), (17.5, 17.7), (-31.55, -24.15), YEL, 0.02)
    # lamp
    for x in (-11.0, -5.5):
        bx(p, (x, x + 0.5), (16.8, 19.4), (-28.4, -27.6), DGR, 0.02)
    zcyl(p, cx, 19.4, -30.5, -25.6, 2.5, DGR, verts=12, jit=0.03)
    zcyl(p, cx, 19.4, -25.6, -24.5, 2.4, STE, verts=12, jit=0.02)
    zcyl(p, cx, 19.4, -24.9, -24.4, 1.9, YEL, verts=12, jit=0.02)
    bx(p, (-11.5, -9.2), (1, 2.8), (-26.2, -24.4), RED, 0.04)                      # generator at the foot
    bx(p, (-11.3, -9.4), (2.2, 2.5), (-24.45, -24.3), DGR, 0.02)


# ---- 15. Dishes ---------------------------------------------------------------------------------------------------------------
def build_Dishes(p):
    bx(p, (-52.5, -43.5), (0, 4.4), (-61, -55), WHT, 0.04)
    bx(p, (-53, -43), (4.4, 5), (-61.3, -54.7), STE, 0.03)
    bx(p, (-49.2, -46.8), (0, 3.4), (-55.2, -55), NAVY, 0.03)
    bx(p, (-48.9, -47.1), (0, 3.2), (-55.3, -55.2), BLU, 0.03)
    window_z(p, -51.7, -50.0, 1.6, 3.4, -55, d=0.15, mull=False)
    window_z(p, -46.0, -44.3, 1.6, 3.4, -55, d=0.15, mull=False)
    bx(p, (-48.4, -47.6), (5, 5.6), (-58.5, -57.7), RED, 0.02)
    bx(p, (-52, -50), (5, 5.8), (-60.5, -58.5), MDK, 0.03)
    bx(p, (-52.5, -43.5), (3.6, 3.9), (-55.05, -55), STE, 0.02)
    for x in (-52.4, -43.6):
        vcyl(p, x, 0, 6, -53, 0.7, STE, verts=8, jit=0.03)
        dish(p, x, 7, -53.7, -52.5, 2.7, 1.1, WHT, verts=12)
        zcyl(p, x, 7, -52.55, -52.4, 2.1, LBL, verts=12, jit=0.02)
        zcyl(p, x, 7, -52.45, -52.3, 0.4, RED, verts=6, jit=0.02)
    cols = (WHT, RED, WHT, RED, WHT)
    for k in range(5):
        vcyl(p, -48, k * 2.4, (k + 1) * 2.4, -61, 0.7, cols[k], verts=8, jit=0.02)
    dish(p, -48, 11.5, -61.6, -60.4, 2.5, 1.0, RED, verts=12)
    zcyl(p, -48, 11.5, -60.55, -60.4, 1.9, WHT, verts=12, jit=0.02)
    zcyl(p, -48, 11.5, -60.5, -60.35, 0.4, YEL, verts=6, jit=0.02)
    for x in (-44.5, -51.5):
        bx(p, (x - 0.1, x + 0.1), (5, 8), (-59.1, -58.9), STE, 0.02)
        ball(p, (x, 8.1, -59), 0.3, RED, subdiv=1, jit=0.02)


# ---- 16. Newsroom --------------------------------------------------------------------------------------------------------------
def build_Newsroom(p):
    bx(p, (-92, -80), (0, 17.2), (-14, -2), CRM, 0.04)
    bx(p, (-92, -80), (17.2, 18), (-14, -2), STN, 0.03)
    bx(p, (-90.5, -81.5), (18, 22.6), (-12.5, -3.5), STN, 0.04)
    bx(p, (-90.7, -81.3), (22.6, 23), (-12.7, -3.3), NAVY, 0.03)
    # entrance and awning
    bx(p, (-87.2, -84.8), (0, 3.6), (-2.15, -2), NAVY, 0.03)
    bx(p, (-86.9, -85.1), (0, 3.3), (-2.3, -2.15), GLS, 0.04)
    for i in range(4):
        x0 = -90 + 2 * i
        c = RED if i % 2 == 0 else WHT
        bot = [(x0, 4.5, -1.6), (x0 + 2, 4.5, -1.6), (x0 + 2, 3.9, 0.4), (x0, 3.9, 0.4)]
        hexa(p, bot + [(a, b + 0.4, c2) for a, b, c2 in bot], c, 0.03)
    # banner NEWS
    bx(p, (-91, -81), (10.5, 13.5), (-1.9, -1.3), NAVY, 0.03)
    bx(p, (-91.2, -80.8), (13.5, 13.8), (-1.95, -1.25), RED, 0.02)
    bx(p, (-91.2, -80.8), (10.2, 10.5), (-1.95, -1.25), RED, 0.02)
    text(p, "NEWS", -86, 11.0, -1.3, -1.0, 1.9, 2.0, 0.45, 0.5, YEL)
    # windows
    for (x0, x1) in ((-90.6, -88.6), (-83.4, -81.4)):
        window_z(p, x0, x1, 5.8, 8.4, -2, d=0.15, mull=False)
    for (x0, x1) in ((-90.4, -88.4), (-87, -85), (-83.6, -81.6)):
        window_z(p, x0, x1, 14.4, 16.8, -2, d=0.15, mull=False)
    for (sx, sg) in ((-92, -1), (-80, 1)):
        for (y0, y1) in ((6, 8.5), (12, 14.5)):
            for zc in (-11, -8, -5):
                window_x(p, sx, sg, y0, y1, zc - 1, zc + 1, d=0.15)
    bx(p, (-90.5, -89), (0, 1.4), (-1.9, -0.5), RED, 0.04)                         # newspaper stand
    # globe on a cradle
    vcyl(p, -86, 23, 24, -8, 2.5, STE, verts=10, jit=0.03)
    vcyl(p, -86, 22.6, 35.0, -8, 0.3, STE, verts=6, jit=0.02)
    ball(p, (-86, 26.5, -8), 4, BLU, subdiv=2, jit=0.03)
    for d in ((0.0, 0.5, 1.0), (0.9, 0.2, -0.4), (-0.8, 0.35, -0.5), (0.1, -0.6, 0.8), (-0.6, 0.8, 0.2)):
        l = math.sqrt(sum(c * c for c in d))
        ball(p, (-86 + 3.7 * d[0] / l, 26.5 + 3.7 * d[1] / l, -8 + 3.7 * d[2] / l), 1.0, GRN, subdiv=1, jit=0.05)
    torus(p, (-86, 26.5, -8), 4.5, 0.22, GLD, segs=18, sides=4, jit=0.02)
    ball(p, (-86, 35.0, -8), 0.5, RED, subdiv=1, jit=0.02)


# ---- 17. Heli ---------------------------------------------------------------------------------------------------------------------
def build_Heli(p):
    vcyl(p, 60, 0, 0.5, -10, 11, DGR, verts=24, jit=0.04)
    vcyl(p, 60, 0.5, 0.54, -10, 10.5, YEL, verts=24, jit=0.01)
    vcyl(p, 60, 0.5, 0.58, -10, 9.9, DGR, verts=24, jit=0.02)
    vcyl(p, 60, 0.58, 0.62, -10, 7.2, WHT, verts=24, jit=0.01)
    vcyl(p, 60, 0.58, 0.66, -10, 6.7, DGR, verts=24, jit=0.02)
    for (xa, xb, za, zb) in ((57.3, 58.1, -13, -7), (61.9, 62.7, -13, -7), (58.1, 61.9, -10.4, -9.6)):
        bx(p, (xa, xb), (0.66, 0.72), (za, zb), YEL, 0.01)
    # body
    ball(p, (59, 4.2, -10), 2.5, RED, scale=(2, 1, 1), subdiv=2, jit=0.04)
    bx(p, (55, 63), (2.3, 2.9), (-12.2, -7.8), WHT, 0.03)
    ball(p, (55.7, 4.8, -10), 1.5, GLS, scale=(0.9, 0.8, 0.95), subdiv=1, jit=0.04)
    bx(p, (56.8, 59.0), (4.3, 5.5), (-12.48, -12.2), GLS, 0.04)
    bx(p, (56.8, 59.0), (4.3, 5.5), (-7.8, -7.52), GLS, 0.04)
    bx(p, (59.6, 62.0), (3.8, 5.6), (-12.46, -12.25), WHT, 0.03)
    # tail
    bx(p, (62.5, 70.5), (4.3, 5.3), (-10.5, -9.5), RED, 0.04)
    extrude_x(p, [(4.6, -10.8), (7.5, -10.2), (7.5, -9.8), (4.6, -9.2)], 69.7, 70.3, WHT, 0.03)
    bx(p, (68.4, 70.2), (5.1, 5.3), (-11.5, -8.5), BLU, 0.03)
    # rotor
    vcyl(p, 59, 6.2, 7.8, -10, 0.4, STE, verts=8, jit=0.02)
    bx(p, (50, 68), (7.55, 7.85), (-10.6, -9.4), STE, 0.03)
    bx(p, (58.4, 59.6), (7.55, 7.85), (-18, -2), STE, 0.03)
    for (xa, xb, za, zb) in ((50, 52.2, -10.6, -9.4), (65.8, 68, -10.6, -9.4), (58.4, 59.6, -18, -16), (58.4, 59.6, -4, -2)):
        bx(p, (xa, xb), (7.52, 7.85), (za, zb), RED, 0.02)
    # skids
    for z in (-12.2, -7.8):
        bx(p, (55, 63), (0.4, 0.8), (z - 0.2, z + 0.2), DGR, 0.03)
        for x in (57.0, 61.0):
            bx(p, (x - 0.2, x + 0.2), (0.8, 2.3), (z - 0.15, z + 0.15), DGR, 0.02)


# ---- 18. Coil ----------------------------------------------------------------------------------------------------------------------
def build_Coil(p):
    bx(p, (81, 91), (0, 2), (-1, 9), DGR, 0.04)
    bx(p, (81.7, 90.3), (2, 2.5), (-0.3, 8.3), STE, 0.03)
    vcyl(p, 86, 2.5, 16, 4, 1.7, STE, verts=12, top_r=1.2, jit=0.04)
    vcyl(p, 86, 2.5, 4.4, 4, 2.2, MDK, verts=12, top_r=1.7, jit=0.03)
    for (y, r) in ((6, 3.5), (10, 3.0), (14, 2.5)):
        vcyl(p, 86, y - 0.6, y + 0.6, 4, r, YEL, verts=14, jit=0.03)
        vcyl(p, 86, y - 0.8, y - 0.6, 4, r - 0.4, DGR, verts=14, jit=0.02)
    ball(p, (86, 18.5, 4), 3.0, GLS, subdiv=2, jit=0.04)
    vcyl(p, 86, 15.9, 16.4, 4, 1.4, STE, verts=10, jit=0.02)
    pyl = ((82, 0), (90, 8), (82, 8), (90, 0))
    for (x, z) in pyl:
        bx(p, (x - 0.6, x + 0.6), (0, 6), (z - 0.6, z + 0.6), STE, 0.03)
        bx(p, (x - 0.8, x + 0.8), (5.6, 6.2), (z - 0.8, z + 0.8), DGR, 0.03)
        ball(p, (x, 6.6, z), 0.55, YEL, subdiv=1, jit=0.02)
        # lightning from the pylon tip to the middle ring
        ux, uz = x - 86, z - 4
        l = math.hypot(ux, uz)
        a = (x, 6.8, z)
        e = (86 + 3.0 * ux / l, 10.0, 4 + 3.0 * uz / l)
        m = ((a[0] + e[0]) / 2 - uz / l * 0.7, 8.6, (a[2] + e[2]) / 2 + ux / l * 0.7)
        bar(p, a, m, 0.28, YEL, 0.02)
        bar(p, m, e, 0.28, YEL, 0.02)


# ---- 19. Vault -----------------------------------------------------------------------------------------------------------------------
def build_Vault(p):
    bx(p, (-38, -22), (0, 9), (-63, -51), DGR, 0.04)
    bx(p, (-38.5, -21.5), (9, 9.8), (-63.5, -50.9), STE, 0.03)
    for k in range(8):
        bx(p, (-38.5 + k * 2.125, -38.5 + (k + 1) * 2.125), (9, 9.8), (-50.9, -50.5), YEL if k % 2 == 0 else BLK, 0.02)
    for x in (-37, -23, -30):
        bx(p, (x - 0.15, x + 0.15), (0, 9), (-51.15, -51), MDK, 0.02)
    # round vault door
    zcyl(p, -30, 4, -51.1, -50.3, 3.2, STE, verts=16, jit=0.03)
    zcyl(p, -30, 4, -50.35, -50.2, 2.5, MDK, verts=16, jit=0.03)
    for k in range(10):
        a = math.radians(36 * k)
        bx(p, (-30 + 2.85 * math.cos(a) - 0.2, -30 + 2.85 * math.cos(a) + 0.2), (4 + 2.85 * math.sin(a) - 0.2, 4 + 2.85 * math.sin(a) + 0.2),
           (-50.4, -50.15), DGR, 0.02)
    for (x1, y1, x2, y2) in ((-32, 4, -28, 4), (-31, 2.27, -29, 5.73), (-31, 5.73, -29, 2.27)):
        diag(p, x1, y1, -50.0, x2, y2, 0.45, 0.3, YEL, 0.02)
    ball(p, (-30, 4, -50.0), 0.6, YEL, subdiv=1, jit=0.02)
    # sign
    bx(p, (-34, -26), (7.6, 8.8), (-51, -50.8), DGR, 0.02)
    text(p, "VAULT", -30, 7.85, -50.8, -50.55, 1.2, 0.9, 0.25, 0.3, YEL)
    # barred windows
    for x in (-36, -24):
        bx(p, (x - 1.5, x + 1.5), (4.5, 7.5), (-51, -50.7), STE, 0.03)
        bx(p, (x - 1.2, x + 1.2), (4.8, 7.2), (-50.7, -50.62), GLS, 0.04)
        for k in range(3):
            bx(p, (x - 0.95 + k * 0.95, x - 0.75 + k * 0.95), (4.8, 7.2), (-50.75, -50.5), DGR, 0.02)
    # watch posts with platforms
    for x in (-38, -22):
        vcyl(p, x, 0, 14, -51, 0.7, STE, verts=8, jit=0.03)
        vcyl(p, x, 6, 6.8, -51, 0.74, YEL, verts=8, jit=0.02)
        bx(p, (x - 1.5, x + 1.5), (13.4, 14.4), (-52.5, -49.5), YEL, 0.04)
        bar(p, (x, 10.5, -51), (x - 1.4, 13.4, -49.6), 0.25, MDK)
        bar(p, (x, 10.5, -51), (x + 1.4, 13.4, -49.6), 0.25, MDK)
        for (xa, xb, za, zb) in ((x - 1.5, x + 1.5, -52.5, -52.25), (x - 1.5, x + 1.5, -49.75, -49.5), (x - 1.5, x - 1.25, -52.25, -49.75), (x + 1.25, x + 1.5, -52.25, -49.75)):
            bx(p, (xa, xb), (14.4, 14.9), (za, zb), DGR, 0.02)
    bx(p, (-38.4, -37.6), (14.4, 14.9), (-51.4, -50.6), YEL, 0.02)
    bx(p, (-22.4, -21.6), (14.4, 14.9), (-51.4, -50.6), YEL, 0.02)


# ---- 20. Rocket ----------------------------------------------------------------------------------------------------------------------
def build_Rocket(p):
    bx(p, (77, 91), (0, 0.8), (-29, -15), DGR, 0.04)
    for k in range(6):
        bx(p, (77.3 + k * 2.3, 77.3 + (k + 1) * 2.3), (0.8, 0.88), (-15.7, -15.1), YEL if k % 2 == 0 else BLK, 0.02)
    vcyl(p, 84, 0.8, 0.85, -22, 6.5, STE, verts=18, jit=0.02)
    cx, cz = 84, -22
    vcyl(p, cx, 0.85, 3, cz, 2.5, DGR, verts=12, jit=0.03)
    for (y0, y1, c) in ((3, 9, WHT), (9, 11, RED), (11, 17, WHT), (17, 18.5, BLU), (18.5, 20.5, WHT)):
        vcyl(p, cx, y0, y1, cz, 2.5, c, verts=12, jit=0.03)
    dk.cone(p, (cx, 20.5, cz), 2.5, 6, RED, verts=12, jitter=0.03)
    for y in (14, 6.5):
        zcyl(p, cx, y, -19.7, -19.4, 0.95, YEL, verts=8, jit=0.02)
        zcyl(p, cx, y, -19.6, -19.35, 0.65, GLS, verts=8, jit=0.02)
    star_poly(p, (cx, 4.6, -19.5), 'xy', 0.9, 0.4, 0.1, RED, n=5)
    for s in (-1, 1):                                                              # four swept fins
        pts = [(cx + s * 2.4, 8), (cx + s * 5.5, 1), (cx + s * 2.4, 1)]
        if s < 0:
            pts = pts[::-1]
        extrude_z(p, pts, cz - 0.3, cz + 0.3, BLU, 0.03)
        pts2 = [(8, cz + s * 2.4), (1, cz + s * 5.5), (1, cz + s * 2.4)]
        if s > 0:
            pts2 = pts2[::-1]
        extrude_x(p, pts2, cx - 0.3, cx + 0.3, BLU, 0.03)
    # launch gantry
    for (x, z) in ((78, -23), (80, -23), (78, -21), (80, -21)):
        bx(p, (x - 0.2, x + 0.2), (0, 24), (z - 0.2, z + 0.2), STE, 0.03)
    for y in (4, 9, 14, 19, 24):
        bx(p, (77.8, 80.2), (y - 0.2, y + 0.2), (-23.2, -22.8), MDK, 0.02)
        bx(p, (77.8, 80.2), (y - 0.2, y + 0.2), (-21.2, -20.8), MDK, 0.02)
        bx(p, (77.8, 78.2), (y - 0.2, y + 0.2), (-22.8, -21.2), MDK, 0.02)
        bx(p, (79.8, 80.2), (y - 0.2, y + 0.2), (-22.8, -21.2), MDK, 0.02)
    for i, (ya, yb) in enumerate(((0, 4), (4, 9), (9, 14), (14, 19), (19, 24))):
        f = 1 if i % 2 == 0 else -1
        bar(p, (78.0 if f > 0 else 80.0, ya, -20.9), (80.0 if f > 0 else 78.0, yb, -20.9), 0.22, YEL, 0.02)
    bx(p, (77.8, 80.2), (23.6, 24.0), (-23.2, -20.8), STE, 0.03)
    bx(p, (78.4, 79.6), (24, 24.6), (-22.6, -21.4), RED, 0.02)
    bx(p, (79.4, 83.4), (15.6, 16.4), (-22.6, -21.4), STE, 0.03)
    bx(p, (82.6, 83.4), (15.3, 16.7), (-22.8, -21.2), YEL, 0.02)


# ---- 21. Statue ------------------------------------------------------------------------------------------------------------------------
def build_Statue(p):
    bx(p, (-37, -23), (0, 2.6), (-13, 1), STN, 0.04)
    bx(p, (-37, -23), (2.6, 3), (-13, 1), GLD_, 0.03)
    bx(p, (-34.5, -25.5), (3, 7), (-10.5, -1.5), STL, 0.04)
    bx(p, (-34.5, -25.5), (6.6, 7), (-10.5, -1.5), GLD_, 0.03)
    bx(p, (-32, -28), (4.0, 5.8), (-1.5, -1.38), NAVY, 0.02)
    text(p, "HERO", -30, 4.5, -1.38, -1.2, 0.8, 0.9, 0.2, 0.25, YEL)
    # legs, boots, belt
    for (xa, xb) in ((-33, -30.3), (-29.7, -27)):
        bx(p, (xa, xb), (8.3, 14.8), (-7.7, -4.3), BLU, 0.04)
        bx(p, (xa - 0.1, xb + 0.1), (7, 8.5), (-8, -4), RED, 0.04)
    bx(p, (-33, -27), (14.6, 15.9), (-7.9, -4.1), YEL, 0.03)
    bx(p, (-30.8, -29.2), (14.7, 15.8), (-4.15, -3.95), RED, 0.02)
    # torso, chest emblem
    pts = [(-32.6, 15.8, -7.6), (-27.4, 15.8, -7.6), (-27.4, 15.8, -4.6), (-32.6, 15.8, -4.6),
           (-33.5, 23.6, -8.2), (-26.5, 23.6, -8.2), (-26.5, 23.6, -3.8), (-33.5, 23.6, -3.8)]
    hexa(p, pts, BLU, 0.04)
    extrude_z(p, [(-31.6, 22.6), (-28.4, 22.6), (-28.4, 19.8), (-30, 18.2), (-31.6, 19.8)], -4.5, -3.85, YEL, 0.03)
    star_poly(p, (-30, 20.6, -3.8), 'xy', 1.15, 0.5, 0.1, RED, n=5)
    # shoulders, arms, fists
    for x in (-33.7, -26.3):
        ball(p, (x, 23.0, -6), 1.5, BLU, subdiv=1, jit=0.04)
    bar(p, (-26.4, 23.0, -6), (-25.2, 29.8, -6), 1.7, BLU)
    ball(p, (-25.2, 31, -6), 1.1, RED, subdiv=1, jit=0.04)
    bar(p, (-33.7, 22.8, -6), (-34.2, 18.6, -6.5), 1.6, BLU)
    bar(p, (-34.2, 18.6, -6.5), (-33.0, 15.4, -5.6), 1.5, BLU)
    ball(p, (-32.8, 15.2, -5.6), 0.95, RED, subdiv=1, jit=0.04)
    # head with mask
    bx(p, (-30.6, -29.4), (23.6, 24.5), (-6.5, -5.5), SKIN, 0.03)
    ball(p, (-30, 26, -6), 1.8, SKIN, subdiv=2, jit=0.03)
    bx(p, (-31.8, -28.2), (26.0, 26.9), (-7.4, -4.2), BLU, 0.03)
    for x in (-30.9, -29.1):
        bx(p, (x - 0.3, x + 0.3), (26.2, 26.6), (-4.25, -4.15), WHT, 0.02)
    ball(p, (-30, 27.4, -6.5), 1.45, DGR, scale=(1, 0.7, 1), subdiv=1, jit=0.04)
    # flowing cape
    bot = [(-34.8, 14.5, -10.6), (-25.2, 14.5, -10.6), (-25.2, 14.5, -9.8), (-34.8, 14.5, -9.8)]
    top = [(-33.6, 24, -8.4), (-26.4, 24, -8.4), (-26.4, 24, -8.0), (-33.6, 24, -8.0)]
    hexa(p, bot + top, RED, 0.04)
    mid_b = [(-34.4, 14.7, -10.35), (-25.6, 14.7, -10.35), (-25.6, 14.7, -9.2), (-34.4, 14.7, -9.2)]
    hexa(p, mid_b + [(a * 0.92 + -30 * 0.08, 19.5, c * 0.9 - 8.9 * 0.1) for a, b, c in mid_b], DRED, 0.04)


# ---- 22. Hall -------------------------------------------------------------------------------------------------------------------------
def build_Hall(p):
    bx(p, (-87, -57), (0, 1.2), (-63, -45), STN, 0.04)
    bx(p, (-74.5, -69.5), (1.2, 1.6), (-47.5, -45), STL, 0.03)
    bx(p, (-74.5, -69.5), (1.6, 2.0), (-49.2, -47.5), STL, 0.03)
    bx(p, (-84, -60), (1.2, 11.8), (-62, -52), WHT, 0.04)
    bx(p, (-85, -59), (11.8, 12.4), (-62.5, -51.5), STE, 0.03)
    extrude_z(p, [(-73.6, 2.0), (-70.4, 2.0), (-70.4, 6.8), (-72, 8.4), (-73.6, 6.8)], -52.2, -52.0, NAVY, 0.03)
    extrude_z(p, [(-73.1, 2.0), (-70.9, 2.0), (-70.9, 6.5), (-72, 7.7), (-73.1, 6.5)], -52.25, -52.2, GLD_, 0.03)
    for (y0, y1) in ((4.5, 9),):
        window_x(p, -84, -1, y0, y1, -60.5, -58.3, d=0.15)
        window_x(p, -84, -1, y0, y1, -56, -53.8, d=0.15)
        window_x(p, -60, 1, y0, y1, -60.5, -58.3, d=0.15)
        window_x(p, -60, 1, y0, y1, -56, -53.8, d=0.15)
    # portico: columns with bases and capitals, entablature and pediment
    for x in (-83, -76, -68, -61):
        bx(p, (x - 1.25, x + 1.25), (1.2, 1.6), (-50.75, -48.25), STN, 0.03)
        vcyl(p, x, 1.6, 11.4, -49.5, 0.9, WHT, verts=8, jit=0.03)
        bx(p, (x - 1.2, x + 1.2), (11.4, 11.8), (-50.7, -48.3), STN, 0.03)
    bx(p, (-86, -58), (11.8, 13.4), (-52.5, -47.5), BLU, 0.03)
    prism_z(p, [(-85.5, 13.4), (-58.5, 13.4), (-72, 16.8)], -52.4, -47.6, WHT, 0.03)
    prism_z(p, [(-83.5, 13.9), (-60.5, 13.9), (-72, 16.1)], -47.6, -47.45, STL, 0.02)
    star_poly(p, (-72, 14.5, -47.4), 'xy', 1.0, 0.45, 0.15, YEL, n=5)
    # statues in the niches
    for x in (-79.5, -64.5):
        bx(p, (x - 0.9, x + 0.9), (1.2, 2.4), (-51.4, -50.0), STN, 0.03)
        bx(p, (x - 0.5, x + 0.5), (2.4, 4.6), (-51.0, -50.4), BLU, 0.03)
        ball(p, (x, 5.1, -50.7), 0.5, SKIN, subdiv=1, jit=0.03)
    # drum and golden dome
    vcyl(p, -72, 12.4, 14.4, -57, 4.5, WHT, verts=16, jit=0.03)
    ball(p, (-72, 16, -57), 5, YEL, scale=(1, 0.8, 1), subdiv=2, jit=0.04)
    ball(p, (-72, 19.55, -57), 0.45, RED, subdiv=1, jit=0.02)


# ---- 23. Crystal ---------------------------------------------------------------------------------------------------------------------
def build_Crystal(p):
    vcyl(p, 50, 0, 0.8, -54, 7.5, ROK, verts=14, jit=0.05)
    vcyl(p, 50, 0.8, 0.86, -54, 6.0, ROD, verts=14, jit=0.04)
    for k in range(7):
        a = math.radians(360 / 7 * k + 10)
        ball(p, (50 + 6.4 * math.cos(a), 0.9, -54 + 6.4 * math.sin(a)), 1.2, ROK, scale=(1.2, 0.7, 1.0), subdiv=1, jit=0.07)
    ball(p, (45, 1.2, -57), 1.6, ROK, scale=(1, 0.75, 0.94), subdiv=1, jit=0.07)
    ball(p, (55, 1.4, -52), 1.5, ROK, scale=(1, 0.93, 1.13), subdiv=1, jit=0.07)
    for (x, z, h, r, c, t) in ((50, -54, 14, 1.9, GLS, (0.6, 0.3)), (46, -52, 9, 1.35, BLU, (-0.8, 0.5)), (54, -56, 10, 1.55, GLS, (0.9, -0.4)),
                               (47, -57, 4.4, 1.0, BLU, (-0.3, -0.5)), (53, -51, 4, 0.9, GLS, (0.4, 0.4)), (51.8, -57.3, 3.0, 0.8, LBL, (0.3, -0.3)),
                               (44.4, -53.5, 2.4, 0.7, GLS, (-0.2, 0.2))):
        crystal(p, x, z, h, r, c, t, y0=0.4)


# ---- 24. Mech --------------------------------------------------------------------------------------------------------------------------
def build_Mech(p):
    for (xa, xb) in ((74.5, 78.5), (81.5, 85.5)):
        bx(p, (xa, xb), (0, 2.4), (49, 55), DGR, 0.04)
        bx(p, (xa + 0.1, xb - 0.1), (0, 1.2), (54.2, 55), YEL, 0.03)
        bx(p, (xa + 0.8, xb - 0.8), (2.4, 10.6), (50.8, 53.2), STE, 0.04)
        bx(p, (xa + 0.6, xb - 0.6), (5.8, 7.4), (52.8, 53.6), BLU, 0.03)
        bx(p, (xa + 0.8, xb - 0.8), (2.4, 3.6), (50.8, 53.2), DGR, 0.03)
    bx(p, (75.5, 84.5), (10.2, 12.6), (49.5, 54.5), DGR, 0.04)
    bx(p, (79.2, 80.8), (10.2, 12.0), (54.5, 54.8), YEL, 0.02)
    hexa(p, [(75.5, 12.5, 49), (84.5, 12.5, 49), (84.5, 12.5, 54.5), (75.5, 12.5, 54.5),
             (74, 20.5, 48.5), (86, 20.5, 48.5), (86, 20.5, 55.5), (74, 20.5, 55.5)], BLU, 0.04)
    bx(p, (77.2, 82.8), (14, 19), (54.9, 55.4), YEL, 0.03)
    for k in range(3):
        bx(p, (77.6, 79.0), (14.4 + k * 0.5, 14.65 + k * 0.5), (55.4, 55.5), DGR, 0.02)
    star_poly(p, (80.7, 16.8, 55.4), 'xy', 1.4, 0.6, 0.1, RED, n=5)
    for (xa, xb, cx) in ((71.8, 75.2, 73.5), (84.8, 88.2, 86.5)):                 # shoulder cannons
        bx(p, (xa, xb), (16.5, 20.5), (49.8, 54.2), YEL, 0.04)
        zcyl(p, cx, 19.0, 54.2, 55.5, 0.7, DGR, verts=8, jit=0.02)
        bx(p, (xa + 0.3, xb - 0.3), (16.5, 17.0), (49.8, 54.2), DGR, 0.02)
    for (xa, xb) in ((71.3, 73.5), (86.5, 88.7)):                                  # arms and fists
        bx(p, (xa, xb), (9.5, 16.5), (50.8, 53.2), STE, 0.04)
        bx(p, (xa, xb), (8.0, 9.8), (50.6, 53.4), DGR, 0.03)
        bx(p, (xa + 0.2, xb - 0.2), (9.6, 10.2), (53.2, 53.5), YEL, 0.02)
    bx(p, (78.5, 81.5), (20.5, 21), (50.5, 53.5), DGR, 0.03)                       # neck, head
    bx(p, (77.5, 82.5), (21, 24.2), (49.8, 54.2), STE, 0.04)
    bx(p, (78, 82), (22.2, 23.2), (54.2, 54.35), GLS, 0.03)
    for x in (78.6, 80.6):
        bx(p, (x, x + 0.8), (22.5, 22.9), (54.35, 54.42), WHT, 0.02)
    bx(p, (79.4, 80.6), (24.2, 24.9), (50.2, 53.8), YEL, 0.02)
    for x in (77.2, 82.5):
        bx(p, (x, x + 0.3), (21.6, 23.6), (51, 53.4), YEL, 0.02)
    bx(p, (79.7, 80.3), (24.1, 27.1), (51.7, 52.3), RED, 0.02)
    bx(p, (76, 84), (13.5, 19.5), (48.5, 49.4), DGR, 0.03)                         # backpack thrusters
    for x in (77.3, 82.7):
        bx(p, (x - 0.7, x + 0.7), (12.0, 13.5), (48.6, 49.4), YEL, 0.02)


# ---- 25. Shield ------------------------------------------------------------------------------------------------------------------------
def build_Shield(p):
    bx(p, (-88, -72), (0, 1.4), (-35, -25), ROK, 0.05)
    for (x, y, z, r, sc) in ((-84, 1.4, -31, 2.6, (1.3, 0.6, 1.1)), (-77, 1.3, -29.5, 2.4, (1.2, 0.6, 1.2)), (-80.5, 1.8, -33.2, 2.3, (1.5, 0.7, 0.9)),
                             (-86, 1.0, -27.5, 1.9, (1.1, 0.6, 1.0)), (-74.5, 0.9, -32, 1.7, (1.0, 0.7, 1.0)), (-87, 1.0, -33, 1.6, (1.0, 0.8, 1.0))):
        ball(p, (x, y, z), r, ROK, scale=sc, subdiv=1, jit=0.07)
    bx(p, (-83, -77), (1.8, 6), (-32, -28), STE, 0.04)
    bx(p, (-81, -79), (6, 15), (-32, -31.1), STE, 0.04)
    bar(p, (-85.5, 2.0, -33.5), (-81.5, 11.0, -31.4), 1.0, MDK)
    bar(p, (-74.5, 2.0, -33.5), (-78.5, 11.0, -31.4), 1.0, MDK)
    zcyl(p, -80, 15, -31.1, -28.9, 10, RED, verts=24, jit=0.03)
    zcyl(p, -80, 15, -30.6, -27.8, 7.5, WHT, verts=24, jit=0.02)
    zcyl(p, -80, 15, -30.1, -26.7, 5.0, BLU, verts=24, jit=0.02)
    for k in range(12):
        a = math.radians(30 * k)
        x, y = -80 + 8.8 * math.cos(a), 15 + 8.8 * math.sin(a)
        bx(p, (x - 0.35, x + 0.35), (y - 0.35, y + 0.35), (-28.9, -28.55), YEL, 0.02)
    star_poly(p, (-80, 15, -26.5), 'xy', 3.7, 1.55, 0.3, YEL, n=5)
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




ORDER = ["Ground", "EmblemWall", "Tower", "Billboard", "Jet", "Garage", "Course", "Lab", "Fountain", "Banners", "Comic", "Truck", "Ring",
         "Searchlight", "Dishes", "Newsroom", "Heli", "Coil", "Vault", "Rocket", "Statue", "Hall", "Crystal", "Mech", "Shield"]
PARTS = [(n, globals()["build_" + n]) for n in ORDER]
AZ = {"Dishes": 160, "Vault": 150}
ELEV = {"Ground": 45, "Tower": 22}
MULT = {"Ground": 1.3, "Tower": 2.2, "Rocket": 2.3, "Newsroom": 2.3, "Statue": 2.3, "Billboard": 2.0, "Searchlight": 2.2}
SHIBA_AT = {"Ground": (-30, 30, 270, 0.5), "Tower": (76, -28, 270, 0), "Rocket": (84, -12, 270, 0), "Heli": (60, 4, 270, 0)}


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
        x, z, f, lift = SHIBA_AT.get(pid, ((lo[0] + hi[0]) / 2, hi[2] + 3.8, 270, 0))
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0.5)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 42, 2.5, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_HeroHQ.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        os.remove(os.path.join(OUT, f))


main()
