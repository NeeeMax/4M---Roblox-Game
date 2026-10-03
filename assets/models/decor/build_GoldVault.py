"""Final low-poly decor models for the theme GoldVault (25 parts around the sixteenth Shiba, Gold Shiba).

Usage: blender --background --factory-startup --python build_GoldVault.py -- <outdir> [PartId ...]
Writes Decor_GoldVault_<PartId>.fbx, preview_<PartId>.png and stage_GoldVault.png into <outdir>.
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
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "GoldVault"))
ONLY = ARGS[1:]
KEY = "GoldVault"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_GoldVault.json"))

# ---- palette (one for all 25 parts) ---------------------------------------------------------------------------------
GOLD = (240, 190, 52)
LGOLD = (252, 224, 112)
DGOLD = (190, 140, 36)
STEEL = (150, 158, 172)
LSTEEL = (190, 198, 210)
DSTEEL = (72, 78, 90)
CHAR = (42, 46, 56)
RED = (200, 48, 52)
VELVET = (150, 30, 44)
MARBLE = (226, 222, 214)
DMARBLE = (70, 66, 74)
GREEN = (70, 150, 90)
GLASS = (150, 200, 230)
AMBER = (226, 170, 40)
PINK = (240, 150, 170)
WATER = (80, 170, 230)
LWATER = (150, 214, 245)
WOOD = (120, 80, 50)
DWOOD = (84, 56, 36)
ORANGE = (236, 140, 30)
CREAM = (250, 236, 190)
WHITE = (240, 244, 250)
BLUE = (60, 100, 200)

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



# ---- extra helpers ------------------------------------------------------------------------------------------------------
_letter0 = letter


def letter(p, ch, x0, y0, z0, z1, w, h, t, col, mirror=False):
    if ch not in "VGF$":
        return _letter0(p, ch, x0, y0, z0, z1, w, h, t, col, mirror)
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        if mirror:
            a, c = w - c, w - a
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        if mirror:
            a, c = w - a, w - c
        diag(p, x0 + a, y0 + b, zc, x0 + c, y0 + e, t, d, col, 0.03)
    if ch == 'V':
        dg(t * 0.5, h, w / 2, t * 0.4)
        dg(w - t * 0.5, h, w / 2, t * 0.4)
    elif ch == 'G':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t); r(w - t, t, w, h / 2); r(w / 2, h / 2 - t / 2, w, h / 2 + t / 2)
    elif ch == 'F':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2)
    elif ch == '$':
        _letter0(p, 'S', x0, y0 + h * 0.08, z0, z1, w, h * 0.84, t, col, mirror)
        r(w / 2 - t / 2, 0, w / 2 + t / 2, h)


def ry(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


def ingot(p, cx, y0, cz, w, h, d, col, yaw=0, top=0.82, jit=0.05):
    """Gold bar: a trapezoid block, wider at the bottom."""
    hw, hd = w / 2, d / 2
    tw, td = hw * top, hd * top
    loc = [(-hw, 0, -hd), (hw, 0, -hd), (hw, 0, hd), (-hw, 0, hd), (-tw, h, -td), (tw, h, -td), (tw, h, td), (-tw, h, td)]
    pts = []
    for (x, y, z) in loc:
        a, b = ry(x, z, yaw)
        pts.append((cx + a, y0 + y, cz + b))
    return hexa(p, pts, col, jit)


def gem(p, cx, y0, cz, r, hp, hc, col, verts=8, table=0.5, jit=0.1):
    """Cut gem: pointed pavilion of height hp under a crown of height hc with a flat table."""
    dk.cyl(p, (cx, y0 + hp / 2, cz), 0.04, hp, col, axis='y', verts=verts, top_radius=r, jitter=jit)
    dk.cyl(p, (cx, y0 + hp + hc / 2, cz), r, hc, col, axis='y', verts=verts, top_radius=r * table, jitter=jit)


def coin(p, cx, cy, z0, z1, r, col=GOLD, rim=DGOLD, verts=14):
    """A coin facing the road (+z): raised rim ring and a recessed face."""
    zcyl(p, cx, cy, z0, z1, r, rim, verts=verts, jit=0.03)
    zcyl(p, cx, cy, z0 + 0.0, z1 + 0.04, r * 0.78, col, verts=verts, jit=0.03)


def sparkle(p, c, r, col=WHITE):
    """Four-point sparkle star facing +z."""
    star_poly(p, c, 'xy', r, r * 0.28, 0.12, col, n=4, rot0=90)


def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s, o, r = q["Size"], q["Offset"], q.get("Rotation") or (0, 0, 0)
        shape = q.get("Shape") or ""
        cyl = "Cylinder" in shape
        if cyl:
            # Roblox cylinder: axis along the piece's x
            pass
        rx, ry_, rz = (math.radians(a) for a in r)
        R = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry_, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append(R @ Vector((sx * s[0] / 2, sy * s[1] / 2, sz * s[2] / 2)))
        if "Ball" in shape or cyl:
            # ellipsoid / cylinder: use the exact extents of the rotated shape
            ext = [0, 0, 0]
            for i in range(3):
                if "Ball" in shape:
                    ext[i] = math.sqrt(sum((R[i][j] * s[j] / 2) ** 2 for j in range(3)))
                else:
                    # axis (x) half length, round (y, z) radius s[1]/2
                    ext[i] = abs(R[i][0]) * s[0] / 2 + math.sqrt(R[i][1] ** 2 + R[i][2] ** 2) * s[1] / 2
        else:
            ext = [max(abs(v[i]) for v in pts) for i in range(3)]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - ext[i])
            hi[i] = max(hi[i], o[i] + ext[i])
    return lo, hi


def stage_up(*a, **k):
    pass


# ---- 1. Floor ------------------------------------------------------------------------------------------------------------
def build_Floor(p):
    bx(p, (-95, 95), (0, 0.3), (-65, 65), DSTEEL, 0.05)
    for x in range(-85, 90, 20):                       # panel seams
        bx(p, (x - 0.15, x + 0.15), (0.3, 0.34), (-62, 62), (92, 98, 112), 0.02)
    for z in range(-50, 55, 20):
        bx(p, (-92, 92), (0.3, 0.34), (z - 0.15, z + 0.15), (92, 98, 112), 0.02)
    bx(p, (-95, 95), (0.3, 0.42), (62, 65), GOLD, 0.03)          # gold edging
    bx(p, (-95, 95), (0.3, 0.42), (-65, -62), GOLD, 0.03)
    bx(p, (-95, -92), (0.3, 0.42), (-62, 62), GOLD, 0.03)
    bx(p, (92, 95), (0.3, 0.42), (-62, 62), GOLD, 0.03)
    # coin medallion under the Gold Shiba
    vcyl(p, -40, 0.3, 0.44, 6, 12, GOLD, verts=16, jit=0.03)
    vcyl(p, -40, 0.44, 0.48, 6, 10.4, DGOLD, verts=16, jit=0.03)
    vcyl(p, -40, 0.48, 0.5, 6, 8.6, GOLD, verts=16, jit=0.03)
    star_poly(p, (-40, 0.52, 6), 'xz', 7.2, 3.2, 0.04, DGOLD, n=8, rot0=90)
    vcyl(p, -40, 0.5, 0.54, 6, 2.6, LGOLD, verts=12, jit=0.02)
    # marble yard with a checker
    bx(p, (-88, -48), (0.3, 0.44), (-35, -21), MARBLE, 0.03)
    for i in range(5):
        for j in range(2):
            if (i + j) % 2 == 0:
                bx(p, (-88 + i * 8, -80 + i * 8), (0.44, 0.48), (-35 + j * 7, -28 + j * 7), DMARBLE, 0.03)
    # laser pad with a hazard border
    bx(p, (69, 91), (0.3, 0.42), (0, 22), AMBER, 0.03)
    for k in range(10):
        a = 69 + k * 2.2
        bx(p, (a, a + 1.1), (0.42, 0.46), (0, 1.4), CHAR, 0.02)
        bx(p, (a, a + 1.1), (0.42, 0.46), (20.6, 22), CHAR, 0.02)
    for k in range(9):
        a = k * 2.2 + 1.4
        bx(p, (69, 70.4), (0.42, 0.46), (a, a + 1.1), CHAR, 0.02)
        bx(p, (89.6, 91), (0.42, 0.46), (a, a + 1.1), CHAR, 0.02)
    # stepping tiles along the walkway
    pts = [(v[0], v[1]) for v in BP["Path"]]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        n = max(1, int(L // 7))
        ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        for k in range(n):
            u = (k + 0.5) / n
            cx, cz = x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
            dk.box(p, (cx, 0.34, cz), (5.2, 0.08, 4.2), LSTEEL, rot=(0, ang, 0), jitter=0.05)


# ---- 2. Chamber ----------------------------------------------------------------------------------------------------------
def build_Chamber(p):
    bx(p, (-90, -46), (0, 12), (-62, -59), STEEL, 0.03)
    bx(p, (-90, -87), (0, 12), (-62, -36), STEEL, 0.03)
    bx(p, (-49, -46), (0, 12), (-62, -36), STEEL, 0.03)
    bx(p, (-90, -74), (0, 12), (-39, -36), STEEL, 0.03)
    bx(p, (-62, -46), (0, 12), (-39, -36), STEEL, 0.03)
    bx(p, (-74, -62), (9, 12), (-39, -36), DSTEEL, 0.03)
    bx(p, (-91, -45), (12, 13.2), (-63, -35), DSTEEL, 0.04)
    bx(p, (-91, -45), (13.2, 14), (-36.6, -35.2), GOLD, 0.03)
    # darker plating bands and pillars on the road side
    for y in (3.2, 6.4):
        bx(p, (-90, -74.5), (y, y + 0.7), (-36.3, -36), DSTEEL, 0.03)
        bx(p, (-61.5, -46), (y, y + 0.7), (-36.3, -36), DSTEEL, 0.03)
    for (a, b) in ((-90.6, -88), (-48, -45.4), (-75.4, -74.6), (-62, -61.2)):
        bx(p, (a, b), (0, 12.2), (-36.8, -35.6), DSTEEL, 0.03)
    bx(p, (-91, -45), (10.8, 11.4), (-36.3, -36), GOLD, 0.03)
    for x in (-86, -80, -52, -57):                      # rivets
        for y in (2, 5, 8):
            bx(p, (x - 0.4, x + 0.4), (y, y + 0.8), (-36.5, -36), LSTEEL, 0.02)
    # door frame trim
    bx(p, (-74.6, -73.8), (0, 9.4), (-39.4, -35.6), GOLD, 0.03)
    bx(p, (-62.2, -61.4), (0, 9.4), (-39.4, -35.6), GOLD, 0.03)
    bx(p, (-74.6, -61.4), (9.4, 10.2), (-39.4, -35.6), GOLD, 0.03)
    # roof vents with louvre slits
    for x in (-80, -56):
        vcyl(p, x, 13.2, 15.4, -52, 3, STEEL, verts=12)
        vcyl(p, x, 15.4, 15.8, -52, 3.4, DSTEEL, verts=12)
        for yy in (13.9, 14.7):
            bx(p, (x - 2.0, x + 2.0), (yy, yy + 0.4), (-49.1, -48.8), CHAR, 0.02)
    # VAULT sign
    bx(p, (-75, -61), (13.2, 16.6), (-37.5, -36.5), CHAR, 0.03)
    bx(p, (-75.4, -60.6), (16.6, 17.2), (-37.7, -36.3), GOLD, 0.03)
    text(p, "VAULT", -68, 14.3, -36.5, -36.2, 2.0, 2.0, 0.5, 0.35, GOLD)
    # inside: shelves with gold bars, visible through the doorway
    bx(p, (-86, -50), (0, 0.4), (-58.8, -37), DSTEEL, 0.03)
    for y in (2.2, 5.2, 8.2):
        bx(p, (-86, -50), (y, y + 0.4), (-58.8, -53), DSTEEL, 0.03)
        for i in range(8):
            ingot(p, -84 + i * 4.6, y + 0.4, -56, 3.6, 1.4, 2.6, GOLD if i % 2 else LGOLD, jit=0.04)
    for x in (-86, -68, -50):
        bx(p, (x - 0.3, x + 0.3), (0.4, 9.8), (-58.8, -58.2), DSTEEL, 0.03)


# ---- 3. VaultDoor --------------------------------------------------------------------------------------------------------
def build_VaultDoor(p):
    bx(p, (-43, -17), (0, 1), (-47, -39), DSTEEL, 0.04)
    for k in range(6):                                   # hazard stripes on the plinth front
        bx(p, (-42 + k * 4.2, -40 + k * 4.2), (1, 1.15), (-40.6, -39.2), AMBER if k % 2 else CHAR, 0.02)
    bx(p, (-42, -18), (1, 20), (-46.5, -43.5), STEEL, 0.03)
    bx(p, (-41, -19), (1.4, 19.6), (-43.7, -43.4), DSTEEL, 0.03)
    # door: gold bezel, steel disc, bolts, hub, spokes
    zcyl(p, -30, 10.5, -44, -42.4, 9.2, DGOLD, verts=24, jit=0.03)
    zcyl(p, -30, 10.5, -43.8, -41, 8, STEEL, verts=24, jit=0.04)
    zcyl(p, -30, 10.5, -41, -40.7, 6.6, LSTEEL, verts=20, jit=0.03)
    for k in range(12):
        a = math.radians(k * 30)
        bx(p, (-30 + 7.2 * math.cos(a) - 0.45, -30 + 7.2 * math.cos(a) + 0.45), (10.5 + 7.2 * math.sin(a) - 0.45, 10.5 + 7.2 * math.sin(a) + 0.45),
           (-41.3, -40.6), DGOLD, 0.03)
    zcyl(p, -30, 10.5, -41, -39.6, 3, GOLD, verts=14, jit=0.03)
    zcyl(p, -30, 10.5, -39.7, -39.2, 1.2, LGOLD, verts=10, jit=0.03)
    for k in range(3):                                   # six-arm wheel
        dk.box(p, (-30, 10.5, -39.9), (13, 1.2, 1.1), GOLD, rot=(0, 0, 60 * k), jitter=0.03)
    for k in range(6):
        a = math.radians(60 * k)
        ball(p, (-30 + 6.5 * math.cos(a), 10.5 + 6.5 * math.sin(a), -39.9), 0.85, DGOLD, subdiv=1, jit=0.03)
    # hinges (left), locking bolts (right), status lights, dial
    for y in (4, 10.5, 17):
        xcyl(p, -42.8, -41, y, -44.6, 0.8, DSTEEL, verts=8)
    for y in (6, 10.5, 15):
        bx(p, (-21.3, -18.3), (y - 0.5, y + 0.5), (-44.4, -43.7), GOLD, 0.03)
    bx(p, (-24, -22), (18, 19), (-43.6, -43.0), RED, 0.02)
    bx(p, (-27, -25), (18, 19), (-43.6, -43.0), GREEN, 0.02)
    zcyl(p, -20.2, 5, -43.6, -42.9, 1.1, CHAR, verts=10)
    bx(p, (-20.35, -20.05), (5, 5.9), (-42.9, -42.8), WHITE, 0.02)


# ---- 4. Arch -------------------------------------------------------------------------------------------------------------
def build_Arch(p):
    for z in (-6, 18):
        bx(p, (-57, -51), (0, 1.2), (z - 3, z + 3), DMARBLE, 0.03)
        bx(p, (-56.4, -51.6), (1.2, 2.2), (z - 2.4, z + 2.4), MARBLE, 0.03)
        bx(p, (-55.7, -52.3), (2.2, 14.8), (z - 1.7, z + 1.7), MARBLE, 0.03)
        for dz in (-0.9, 0.9):                               # flutes
            bx(p, (-52.5, -52.2), (3, 13.5), (z + dz - 0.25, z + dz + 0.25), (196, 192, 186), 0.02)
        bx(p, (-56.2, -51.8), (14.8, 16), (z - 2.2, z + 2.2), GOLD, 0.03)
    bx(p, (-56, -52), (16, 19), (-8, 20), GOLD, 0.03)
    bx(p, (-56.4, -51.6), (19, 19.6), (-8.4, 20.4), DGOLD, 0.03)
    # gold lattice screen between the posts
    bx(p, (-56.5, -54.5), (1.2, 2.2), (-4, 16), DGOLD, 0.03)
    for k in range(9):
        bx(p, (-56.3, -54.7), (2.2, 9.2), (-3.2 + k * 2.4, -2.4 + k * 2.4), DGOLD, 0.03)
    bx(p, (-56.5, -54.5), (8.4, 9.2), (-4, 16), GOLD, 0.03)
    # halo above the beam: disc, ring, rays, ruby
    xcyl(p, -55.2, -53.2, 23, 6, 3.7, GOLD, verts=20, jit=0.03)
    xcyl(p, -54.6, -52.9, 23, 6, 2.6, LGOLD, verts=16, jit=0.03)
    for k in range(14):
        a = 360 / 14 * k
        cy, cz = 23 + 4.25 * math.cos(math.radians(a)), 6 + 4.25 * math.sin(math.radians(a))
        dk.box(p, (-54.2, cy, cz), (1.6, 1.5, 0.95), GOLD if k % 2 else DGOLD, rot=(a, 0, 0), jitter=0.03)
    bx(p, (-55, -53.4), (19.6, 20.6), (4.6, 7.4), GOLD, 0.03)
    ball(p, (-52.8, 23, 6), 1.7, RED, subdiv=1, jit=0.1)
    for z in (-6, 18):
        ball(p, (-54, 17.0, z), 1.0, AMBER, subdiv=1, jit=0.05)


# ---- 5. GoldStacks -------------------------------------------------------------------------------------------------------
def stack(p, x, z, w, d, tiers):
    for i in range(tiers):
        k = 1 - i * 0.3
        n = max(2, int(round(w * k / 2.0)))
        iw = w * k / n
        for j in range(n):
            xx = x - w * k / 2 + iw * (j + 0.5)
            col = GOLD if (i + j) % 2 == 0 else (LGOLD if i == tiers - 1 else DGOLD)
            ingot(p, xx, i * 2.4, z, iw - 0.12, 2.4, d - 0.15 * i, col, top=0.9, jit=0.05)


def build_GoldStacks(p):
    stack(p, -84, 18, 8, 5, 2)
    stack(p, -73, 17, 8, 5, 2)
    stack(p, -79, 29, 10, 6, 3)
    ingot(p, -70, 0, 26, 3, 0.8, 1.6, GOLD, yaw=30, top=0.8)
    ingot(p, -88, 0, 27, 3, 0.8, 1.6, DGOLD, yaw=-20, top=0.8)
    ingot(p, -72, 0, 22.4, 2.4, 0.8, 1.4, LGOLD, yaw=-40, top=0.8)
    ingot(p, -86, 0, 23.0, 2.6, 0.8, 1.4, GOLD, yaw=15, top=0.8)


# ---- 6. CoinHeap ---------------------------------------------------------------------------------------------------------
def build_CoinHeap(p):
    import random
    rnd = random.Random(11)
    def stack(x, z, r, n, y0=0.0, bh=1.0):
        for k in range(n):
            vcyl(p, x + rnd.uniform(-0.25, 0.25), y0 + k * bh, y0 + (k + 1) * bh - 0.06, z + rnd.uniform(-0.25, 0.25),
                 r - 0.12 * (k % 2), GOLD if k % 2 else DGOLD, verts=8, jit=0.05)
    stack(-78, -12, 4.0, 7)                                 # a mound of coin stacks, tallest in the middle
    for i in range(5):
        a = i * 6.2832 / 5 + 0.4
        stack(-78 + 6.2 * math.cos(a), -12 + 4.6 * math.sin(a), 2.8, 5 if i % 2 else 4)
    for i in range(6):
        a = i * 6.2832 / 6 + 0.2
        stack(-78 + 9.0 * math.cos(a), -12 + 6.4 * math.sin(a), 2.2, 2 if i % 2 else 3)
    for i in range(3):                                      # coins leaning on the mound and one on top
        a = 1.0 + i * 2.1
        dk.cyl(p, (-78 + 3.6 * math.cos(a), 5.2, -12 + 2.6 * math.sin(a)), 2.0, 0.6, LGOLD, axis='y', verts=8,
               rot=(30 * math.sin(a), 20 * i, -30 * math.cos(a)), jitter=0.05)
    dk.cyl(p, (-78, 7.6, -12), 2.2, 0.6, LGOLD, axis='y', verts=8, rot=(14, 30, 8), jitter=0.04)


# ---- 7. Lasers -----------------------------------------------------------------------------------------------------------
def build_Lasers(p):
    bx(p, (69, 91), (0, 0.4), (0, 22), AMBER, 0.03)
    for k in range(10):
        a = 69 + k * 2.2
        bx(p, (a, a + 1.1), (0.4, 0.5), (0, 1.0), CHAR, 0.02)
        bx(p, (a, a + 1.1), (0.4, 0.5), (21, 22), CHAR, 0.02)
    heights = {3: (2, 6), 11: (3.5, 7), 19: (2.5, 5.5)}
    for z, hs in heights.items():
        for x in (71, 89):
            bx(p, (x - 1.3, x + 1.3), (0.4, 1.0), (z - 1.3, z + 1.3), DSTEEL, 0.03)
            bx(p, (x - 1, x + 1), (1.0, 8.4), (z - 1, z + 1), STEEL, 0.03)
            bx(p, (x - 1.15, x + 1.15), (8.4, 9), (z - 1.15, z + 1.15), DSTEEL, 0.03)
            bx(p, (x - 1.02, x + 1.02), (7.4, 7.9), (z - 1.02, z + 1.02), AMBER, 0.02)
            for h in hs:
                if x == 71:
                    bx(p, (x + 0.8, x + 1.5), (h - 0.55, h + 0.55), (z - 0.55, z + 0.55), CHAR, 0.02)
                else:
                    bx(p, (x - 1.5, x - 0.8), (h - 0.55, h + 0.55), (z - 0.55, z + 0.55), CHAR, 0.02)
        for h in hs:
            xcyl(p, 72.3, 87.7, h, z, 0.28, RED, verts=6, jit=0.03)
    for z in heights:
        for x in (71, 89):
            ball(p, (x, 8.75, z), 0.3, RED, subdiv=1)


# ---- 8. Truck ------------------------------------------------------------------------------------------------------------
def build_Truck(p):
    bx(p, (60.5, 82.5), (1.6, 2.6), (46, 54), DSTEEL, 0.03)
    bx(p, (59, 73), (2.6, 9.7), (45.6, 54.4), STEEL, 0.03)
    bx(p, (59.2, 72.8), (9.7, 10.0), (45.8, 54.2), DSTEEL, 0.03)
    bx(p, (58.9, 73.1), (6.4, 7.4), (45.55, 54.45), GOLD, 0.03)
    bx(p, (58.95, 59.45), (3, 9), (47, 53), GOLD, 0.03)
    bx(p, (58.8, 59.1), (5.8, 6.2), (47.2, 52.8), DGOLD, 0.03)         # door split
    bx(p, (58.8, 59.1), (5.0, 7.0), (47.2, 47.7), DSTEEL, 0.02)
    bx(p, (58.8, 59.1), (5.0, 7.0), (52.3, 52.8), DSTEEL, 0.02)
    # plating ribs and roof hatch
    for x in (62, 66, 70):
        bx(p, (x - 0.25, x + 0.25), (2.6, 6.4), (54.4, 54.6), DSTEEL, 0.03)
        bx(p, (x - 0.25, x + 0.25), (2.6, 6.4), (45.4, 45.6), DSTEEL, 0.03)
        bx(p, (x - 0.25, x + 0.25), (7.4, 9.7), (54.4, 54.6), DSTEEL, 0.03)
    text(p, "GOLD", 66, 3.1, 54.6, 54.85, 2.0, 2.6, 0.5, 0.5, GOLD)
    for k in range(3):                                                # gun ports
        bx(p, (61 + k * 4.4, 63 + k * 4.4), (8.2, 8.9), (54.4, 54.75), CHAR, 0.02)
    # cab: sloped windscreen, side windows, bumper, headlights, grille
    bx(p, (73.5, 81.5), (2.6, 5.4), (45.8, 54.2), STEEL, 0.03)
    hexa(p, [(73.5, 5.4, 46.2), (81.5, 5.4, 46.2), (81.5, 5.4, 53.8), (73.5, 5.4, 53.8),
             (74.5, 7.6, 46.6), (79.0, 7.6, 46.6), (79.0, 7.6, 53.4), (74.5, 7.6, 53.4)], GLASS, 0.03)
    bx(p, (74.5, 79.6), (5.6, 7.1), (54.2, 54.45), GLASS, 0.03)
    bx(p, (74.5, 79.6), (5.6, 7.1), (45.55, 45.8), GLASS, 0.03)
    bx(p, (73.4, 79.8), (7.6, 7.95), (46.4, 53.6), GOLD, 0.03)
    bx(p, (81.4, 82.5), (1.8, 3.2), (46, 54), DSTEEL, 0.03)
    for z in (47, 53):
        bx(p, (81.5, 82.0), (3.8, 4.8), (z - 0.7, z + 0.7), CREAM, 0.02)
    bx(p, (81.5, 81.9), (2.8, 4.8), (49.2, 50.8), CHAR, 0.02)
    for z in (47.6, 52.4):                                              # roof beacons
        bx(p, (75.2, 76.4), (7.95, 8.6), (z - 0.5, z + 0.5), RED, 0.02)
    # wheels: tyre, hub, axles, mud flaps
    for x in (62, 70, 78.5):
        zcyl(p, x, 1.8, 45.4, 46.8, 1.8, CHAR, verts=10, jit=0.02)
        zcyl(p, x, 1.8, 53.2, 54.6, 1.8, CHAR, verts=10, jit=0.02)
        zcyl(p, x, 1.8, 45.2, 45.5, 0.9, LSTEEL, verts=6, jit=0.02)
        zcyl(p, x, 1.8, 54.5, 54.8, 0.9, LSTEEL, verts=6, jit=0.02)
        zcyl(p, x, 1.8, 46.8, 53.2, 0.5, DSTEEL, verts=6, jit=0.02)


# ---- 9. Desk -------------------------------------------------------------------------------------------------------------
def build_Desk(p):
    bx(p, (-33, -19), (0, 3.2), (46, 50), DSTEEL, 0.03)
    bx(p, (-32.2, -19.8), (1.0, 1.5), (50, 50.2), GOLD, 0.03)
    bx(p, (-33, -19), (0, 0.5), (45.9, 50.1), CHAR, 0.02)
    for x in (-29.5, -26, -22.5):                                 # drawer fronts
        bx(p, (x - 1.4, x + 1.4), (1.9, 2.9), (50, 50.12), STEEL, 0.03)
        bx(p, (x - 0.5, x + 0.5), (2.3, 2.5), (50.12, 50.3), GOLD, 0.02)
    bx(p, (-33.5, -18.5), (3.2, 3.7), (45.5, 50.5), MARBLE, 0.03)
    # glass screen with a gold frame
    bx(p, (-33.5, -18.5), (3.7, 7.7), (50.05, 50.35), GLASS, 0.03)
    bx(p, (-33.5, -18.5), (7.3, 7.7), (49.95, 50.45), GOLD, 0.03)
    bx(p, (-33.5, -33.1), (3.7, 7.3), (49.95, 50.45), GOLD, 0.03)
    bx(p, (-18.9, -18.5), (3.7, 7.3), (49.95, 50.45), GOLD, 0.03)
    # three monitors facing the guard (-z), keyboard, lamp
    for x in (-30, -26, -22):
        bx(p, (x - 0.3, x + 0.3), (3.7, 4.2), (46.8, 47.2), CHAR, 0.02)
        bx(p, (x - 1.3, x + 1.3), (3.9, 5.7), (46.8, 47.2), CHAR, 0.03)
        bx(p, (x - 1.1, x + 1.1), (4.1, 5.5), (46.6, 46.8), (60, 120, 190), 0.05)
        bx(p, (x - 0.8, x + 0.4), (4.5, 4.7), (46.5, 46.6), (150, 240, 170), 0.03)
        bx(p, (x - 0.8, x + 0.8), (5.0, 5.15), (46.5, 46.6), (150, 240, 170), 0.03)
    bx(p, (-28, -24), (3.7, 3.95), (45.8, 46.6), CHAR, 0.02)
    bx(p, (-21, -19.4), (3.7, 4.1), (46, 46.9), CHAR, 0.02)          # phone
    vcyl(p, -32.2, 3.7, 3.9, 48.6, 0.8, DGOLD, verts=8)
    bx(p, (-32.4, -32.0), (3.9, 6.0), (48.4, 48.8), GOLD, 0.03)
    bx(p, (-33.2, -31.2), (5.8, 6.3), (47.8, 49.4), CREAM, 0.02)
    # swivel chair
    vcyl(p, -26, 0.6, 1.8, 43.6, 0.35, DSTEEL, verts=6)
    bx(p, (-27.4, -24.6), (0.4, 0.8), (43.4, 43.8), DSTEEL, 0.02)
    bx(p, (-26.2, -25.8), (0.4, 0.8), (42.2, 45.0), DSTEEL, 0.02)
    for (x, z) in ((-27.3, 42.3), (-24.7, 42.3), (-27.3, 44.9), (-24.7, 44.9)):
        vcyl(p, x, 0, 0.5, z, 0.3, CHAR, verts=6)
    bx(p, (-27.5, -24.5), (1.8, 2.6), (42.1, 45.1), VELVET, 0.03)
    bx(p, (-27.4, -24.6), (2.6, 5.6), (42.1, 42.7), VELVET, 0.03)
    bx(p, (-27.6, -24.4), (5.0, 5.6), (42.0, 42.8), GOLD, 0.03)
    for x in (-27.8, -24.2):
        bx(p, (x - 0.2, x + 0.2), (2.6, 3.8), (43.0, 44.6), GOLD, 0.03)


# ---- 10. Statue ----------------------------------------------------------------------------------------------------------
def build_Statue(p):
    bx(p, (75, 89), (0, 3), (-59, -45.3), DMARBLE, 0.03)
    bx(p, (77, 87), (3, 5), (-57, -47), MARBLE, 0.03)
    bx(p, (76.6, 87.4), (3.7, 4.2), (-57.4, -46.6), GOLD, 0.03)
    bx(p, (79, 85), (0.8, 2.2), (-45.3, -45.05), GOLD, 0.03)
    # sitting Shiba (faces the road, +z)
    ball(p, (82, 9.6, -52.3), 1, GOLD, scale=(3.5, 4.4, 3.2), subdiv=2, jit=0.06)
    ball(p, (79.5, 6.6, -52.4), 1, DGOLD, scale=(1.7, 2.0, 2.3), subdiv=1, jit=0.05)
    ball(p, (84.5, 6.6, -52.4), 1, DGOLD, scale=(1.7, 2.0, 2.3), subdiv=1, jit=0.05)
    ball(p, (82, 10.2, -49.4), 1, LGOLD, scale=(2.1, 2.8, 1.3), subdiv=1, jit=0.05)
    ball(p, (82, 16.4, -51), 1, GOLD, scale=(3.2, 2.8, 2.9), subdiv=2, jit=0.06)
    ball(p, (82, 15.6, -48.9), 1, LGOLD, scale=(1.5, 1.2, 1.2), subdiv=1, jit=0.04)
    bx(p, (80.9, 83.1), (15.0, 16.6), (-49.7, -47.5), LGOLD, 0.03)
    ball(p, (82, 16.5, -47.4), 0.55, CHAR, subdiv=1, jit=0.02)
    for x in (80.6, 83.0):
        bx(p, (x, x + 0.5), (17.2, 17.8), (-48.4, -48.0), CHAR, 0.02)
    prism_z(p, [(79.5, 17.8), (81.5, 17.8), (80.2, 20.8)], -52.4, -50.8, GOLD, 0.04)
    prism_z(p, [(82.5, 17.8), (84.5, 17.8), (83.8, 20.8)], -52.4, -50.8, GOLD, 0.04)
    prism_z(p, [(80.0, 18.0), (81.2, 18.0), (80.4, 19.8)], -50.9, -50.7, DGOLD, 0.03)
    prism_z(p, [(82.8, 18.0), (84.0, 18.0), (83.6, 19.8)], -50.9, -50.7, DGOLD, 0.03)
    for x in (80.6, 83.4):                                       # front legs and paws
        bx(p, (x - 0.9, x + 0.9), (5.4, 10.0), (-50.3, -48.5), GOLD, 0.03)
        bx(p, (x - 1.1, x + 1.1), (5, 5.8), (-50.5, -48.2), LGOLD, 0.03)
    # curled tail
    for (x, y, z, r) in ((84.8, 6.2, -54.4, 1.2), (85.9, 7.6, -54.9, 1.25), (86.1, 9.2, -54.9, 1.25), (85.2, 10.6, -54.7, 1.1)):
        ball(p, (x, y, z), r, DGOLD, subdiv=1, jit=0.05)
    # ruby collar with a gold tag
    vcyl(p, 82, 13.3, 14.3, -51, 3.35, RED, verts=12, jit=0.04)
    zcyl(p, 82, 13.0, -48.2, -47.8, 0.8, GOLD, verts=8, jit=0.03)
    ball(p, (82, 13.0, -47.7), 0.45, (255, 90, 100), subdiv=1, jit=0.05)


# ---- 11. CrownCase -------------------------------------------------------------------------------------------------------
def build_CrownCase(p):
    bx(p, (52.5, 59.5), (0, 4), (-59.5, -52.5), DMARBLE, 0.03)
    bx(p, (52.2, 59.8), (2.0, 2.6), (-59.5, -52.2), GOLD, 0.03)
    bx(p, (54.2, 57.8), (0.8, 1.8), (-52.5, -52.25), GOLD, 0.03)
    # glass case: gold corner posts, top, back and side panes (front open to see the crown)
    for x in (52.9, 59.1):
        for z in (-59.1, -52.9):
            bx(p, (x - 0.3, x + 0.3), (4, 10), (z - 0.3, z + 0.3), GOLD, 0.03)
    bx(p, (52.7, 59.3), (10, 10.5), (-59.3, -52.7), GOLD, 0.03)
    bx(p, (53.2, 58.8), (4, 10), (-59.0, -58.8), GLASS, 0.03)
    bx(p, (52.9, 53.1), (4, 10), (-58.8, -53.2), GLASS, 0.03)
    bx(p, (58.9, 59.1), (4, 10), (-58.8, -53.2), GLASS, 0.03)
    bx(p, (53, 59), (4, 4.3), (-59, -53), GOLD, 0.03)
    # cushion and crown
    bx(p, (54.1, 57.9), (4.3, 5.4), (-57.9, -54.1), VELVET, 0.03)
    for (dx, dz) in ((-1.9, -1.9), (1.9, -1.9), (-1.9, 1.9), (1.9, 1.9)):
        ball(p, (56 + dx, 5.1, -56 + dz), 0.35, GOLD, subdiv=1)
    vcyl(p, 56, 5.4, 6.5, -56, 1.75, GOLD, verts=12)
    vcyl(p, 56, 5.5, 5.9, -56, 1.85, DGOLD, verts=12)
    for k in range(6):
        a = math.radians(60 * k)
        dk.cone(p, (56 + 1.45 * math.cos(a), 6.5, -56 + 1.45 * math.sin(a)), 0.5, 1.5, GOLD, verts=4, jitter=0.04)
        ball(p, (56 + 1.75 * math.cos(a), 5.9, -56 + 1.75 * math.sin(a)), 0.28, RED if k % 2 else WHITE, subdiv=1, jit=0.03)
    ball(p, (56, 7.0, -56), 0.7, RED, subdiv=1, jit=0.08)
    # rope posts with velvet rope
    for x in (51, 61):
        vcyl(p, x, 0, 0.3, -52, 0.4, DGOLD, verts=10)
        vcyl(p, x, 0.3, 3.2, -52, 0.4, GOLD, verts=8)
        ball(p, (x, 3.4, -52), 0.4, GOLD, subdiv=1)
    pts = [(51, 2.8), (53.5, 2.35), (56, 2.2), (58.5, 2.35), (61, 2.8)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        bar(p, (xa, ya, -52), (xb, yb, -52), 0.32, VELVET, 0.04)


# ---- 12. Trolley ---------------------------------------------------------------------------------------------------------
def bundle(p, x0, x1, y0, y1, z0, z1, col=GREEN):
    bx(p, (x0, x1), (y0, y1), (z0, z1), col, 0.06)
    xm = (x0 + x1) / 2
    bx(p, (xm - 0.3, xm + 0.3), (y0 - 0.01, y1 + 0.01), (z0 - 0.06, z1 + 0.06), CREAM, 0.02)


def build_Trolley(p):
    bx(p, (-63, -53), (1.6, 2.2), (49, 55), STEEL, 0.03)
    bx(p, (-62, -54), (1.2, 1.6), (49.6, 54.4), DSTEEL, 0.03)
    bx(p, (-53.5, -53), (2.2, 3.4), (49, 55), STEEL, 0.03)
    for (x, z) in ((-62, 49), (-54, 49), (-62, 55), (-54, 55)):      # casters
        zcyl(p, x, 0.8, z - 0.4, z + 0.4, 0.8, CHAR, verts=8, jit=0.02)
        zcyl(p, x, 0.8, z - 0.45, z + 0.45, 0.35, LSTEEL, verts=6, jit=0.02)
        bx(p, (x - 0.5, x + 0.5), (1.3, 1.6), (z - 0.5, z + 0.5), DSTEEL, 0.02)
    # cash bundles
    for k in range(3):
        bundle(p, -61.8, -60.0, 2.2 + k * 0.87, 3.0 + k * 0.87, 50, 54, GREEN)
        bundle(p, -60.0, -58.2, 2.2 + k * 0.87, 3.0 + k * 0.87, 50, 54, (84, 168, 104))
    for k in range(4):
        bundle(p, -58.0, -56.4, 2.2 + k * 0.85, 2.95 + k * 0.85, 50, 54, (84, 168, 104) if k % 2 else GREEN)
        bundle(p, -56.4, -54.8, 2.2 + k * 0.85, 2.95 + k * 0.85, 50, 54, GREEN if k % 2 else (84, 168, 104))
    ingot(p, -58, 4.8, 52, 4, 1.0, 1.8, LGOLD, top=0.8, jit=0.04)
    # push handle with grip
    for z in (49.6, 54.4):
        bx(p, (-63.05, -62.55), (2.2, 7.2), (z - 0.25, z + 0.25), STEEL, 0.03)
    bx(p, (-63.05, -62.55), (7.2, 7.7), (49.35, 54.65), STEEL, 0.03)
    bx(p, (-63.1, -62.5), (7.2, 7.7), (50.6, 53.4), CHAR, 0.02)


# ---- 13. Diamond ---------------------------------------------------------------------------------------------------------
def build_Diamond(p):
    bx(p, (-17.5, -8.5), (0, 1.6), (-61.5, -52.5), DMARBLE, 0.03)
    bx(p, (-16.6, -9.4), (1.6, 1.8), (-60.6, -53.4), GOLD, 0.03)
    bx(p, (-16, -10), (1.8, 4), (-60, -54), MARBLE, 0.03)
    for (x, z) in ((-16.8, -60.8), (-9.2, -60.8), (-16.8, -53.2), (-9.2, -53.2)):
        ball(p, (x, 2.0, z), 0.6, GOLD, subdiv=1)
    # brilliant-cut gem: pointed pavilion, crown, table, sparkles
    dk.cyl(p, (-13, 6.3, -57), 0.05, 4.6, GLASS, axis='y', verts=8, top_radius=4.45, rot=(0, 22.5, 0), jitter=0.1)
    dk.cyl(p, (-13, 10.4, -57), 4.45, 3.6, (200, 230, 248), axis='y', verts=8, top_radius=2.3, rot=(0, 22.5, 0), jitter=0.1)
    dk.cyl(p, (-13, 12.3, -57), 2.3, 0.3, WHITE, axis='y', verts=8, rot=(0, 22.5, 0), jitter=0.04)
    sparkle(p, (-13, 13.3, -56.9), 0.8)
    star_poly(p, (-13, 13.3, -57), 'yz', 0.8, 0.22, 0.12, WHITE, n=4, rot0=90)
    for (x, y, z, r) in ((-16.4, 8.4, -53.6, 0.7), (-9.6, 9.6, -53.6, 0.55)):
        sparkle(p, (x, y, z), r)


# ---- 14. Safe ------------------------------------------------------------------------------------------------------------
def build_Safe(p):
    for x0, x1 in ((-89.5, -86.5), (-81.5, -78.5)):
        bx(p, (x0, x1), (0, 1.5), (45.5, 54.5), DSTEEL, 0.03)
    bx(p, (-91, -77), (1.5, 15.1), (44.5, 55.5), DSTEEL, 0.03)
    bx(p, (-91, -77), (15.1, 15.5), (44.5, 55.5), STEEL, 0.03)
    bx(p, (-91, -77), (1.5, 2.1), (44.5, 55.5), STEEL, 0.03)
    # door with inner panel and gold frame
    bx(p, (-90, -78), (2.7, 15.3), (55.4, 56.4), STEEL, 0.03)
    bx(p, (-89, -79), (3.7, 14.3), (56.4, 56.65), LSTEEL, 0.03)
    for (x0, x1, y0, y1) in ((-89.3, -78.7, 3.4, 3.9), (-89.3, -78.7, 14.1, 14.6), (-89.3, -88.8, 3.4, 14.6), (-79.2, -78.7, 3.4, 14.6)):
        bx(p, (x0, x1), (y0, y1), (56.4, 56.9), GOLD, 0.03)
    for (x, y) in ((-88.2, 4.7), (-79.8, 4.7), (-88.2, 11.2), (-79.8, 11.2)):
        ball(p, (x, y, 56.75), 0.35, DGOLD, subdiv=1, jit=0.02)
    # combination dial with ticks and a six-spoke wheel
    zcyl(p, -84, 8, 56.65, 57.35, 2.5, DGOLD, verts=16, jit=0.03)
    zcyl(p, -84, 8, 57.3, 57.5, 1.8, CHAR, verts=14, jit=0.02)
    for k in range(12):
        a = math.radians(30 * k)
        bx(p, (-84 + 2.1 * math.cos(a) - 0.15, -84 + 2.1 * math.cos(a) + 0.15), (8 + 2.1 * math.sin(a) - 0.15, 8 + 2.1 * math.sin(a) + 0.15),
           (57.45, 57.6), LGOLD, 0.02)
    zcyl(p, -84, 8, 57.4, 57.8, 0.8, GOLD, verts=8, jit=0.03)
    for k in range(3):
        dk.box(p, (-84, 8, 57.3), (8, 0.8, 0.6), GOLD, rot=(0, 0, 60 * k + 30), jitter=0.03)
    for k in range(6):
        a = math.radians(60 * k + 30)
        ball(p, (-84 + 4 * math.cos(a), 8 + 4 * math.sin(a), 57.3), 0.55, DGOLD, subdiv=1, jit=0.03)
    # SAFE nameplate, hinges, bolts
    bx(p, (-88.2, -79.8), (12.0, 13.6), (56.65, 56.85), CHAR, 0.03)
    text(p, "SAFE", -84, 12.25, 56.85, 57.1, 1.4, 1.1, 0.3, 0.4, GOLD)
    for y0, y1 in ((3.5, 5.7), (7.5, 9.5), (11, 13.2)):
        vcyl(p, -90.5, y0, y1, 56, 0.55, DGOLD, verts=8, jit=0.03)
    for y in (4.5, 8.3, 12.1):
        bx(p, (-78.5, -76.9), (y, y + 1.0), (55.0, 56.5), GOLD, 0.03)


# ---- 15. Mint ------------------------------------------------------------------------------------------------------------
def build_Mint(p):
    bx(p, (76, 92), (0, 4), (-35, -25), DSTEEL, 0.03)
    bx(p, (77, 91), (3.3, 3.9), (-25.25, -25), GOLD, 0.03)
    for x in (77, 90):
        bx(p, (x - 0.3, x + 1.3), (0, 3), (-25.2, -25), CHAR, 0.02)
    for (a, b) in ((77, 80), (88, 91)):
        bx(p, (a, b), (4, 14), (-32, -28), STEEL, 0.03)
        bx(p, (a - 0.2, b + 0.2), (4, 4.7), (-32.2, -27.8), GOLD, 0.03)
    bx(p, (77, 91), (12, 15.2), (-32.5, -27.5), STEEL, 0.03)
    bx(p, (77, 91), (14.5, 15.2), (-32.7, -27.3), GOLD, 0.03)
    bx(p, (81.5, 86.5), (15.2, 17.4), (-32.5, -27.5), DGOLD, 0.03)
    for x in (82.3, 84, 85.7):
        bx(p, (x - 0.25, x + 0.25), (16.2, 16.8), (-27.5, -27.3), CHAR, 0.02)
    ball(p, (84, 17.4, -30), 0.8, RED, subdiv=1, jit=0.05)
    # ram, die and a stamped coin
    vcyl(p, 84, 8, 12, -30, 1.5, DGOLD, verts=10)
    vcyl(p, 84, 5.9, 8, -30, 0.8, LSTEEL, verts=8)
    bx(p, (83, 85), (5.3, 5.9), (-31, -29), STEEL, 0.03)
    bx(p, (81, 87), (4, 5), (-32.5, -27.5), GOLD, 0.03)
    vcyl(p, 84, 5, 5.3, -30, 1.2, LGOLD, verts=10)
    # gauges and buttons on the beam
    for x in (79.2, 82.6):
        zcyl(p, x, 13.6, -27.5, -27.2, 0.85, CREAM, verts=10, jit=0.02)
        bx(p, (x - 0.08, x + 0.08), (13.6, 14.3), (-27.2, -27.1), CHAR, 0.02)
    bx(p, (86.5, 87.4), (13.2, 14.1), (-27.5, -27.2), RED, 0.02)
    bx(p, (88.0, 88.9), (13.2, 14.1), (-27.5, -27.2), GREEN, 0.02)
    # conveyor belt toward the road with coins and a pile
    bx(p, (77, 91), (2, 2.6), (-25, -22), STEEL, 0.03)
    bx(p, (77.5, 90.5), (2.6, 3.0), (-24.7, -22.3), CHAR, 0.03)
    bx(p, (77, 91), (2.6, 3.4), (-25, -24.7), STEEL, 0.03)
    bx(p, (77, 91), (2.6, 3.4), (-22.3, -22), STEEL, 0.03)
    for k in range(6):
        bx(p, (78 + k * 2.2, 78.3 + k * 2.2), (3.0, 3.06), (-24.7, -22.3), DSTEEL, 0.02)
    for x in (77.9, 90.1):
        bx(p, (x - 0.4, x + 0.4), (0, 2), (-24.6, -22.4), DSTEEL, 0.02)
    for x in (80, 83.5, 87):
        vcyl(p, x, 3.06, 3.4, -23.5, 1.0, GOLD, verts=10, jit=0.04)
    ball(p, (90, 3.6, -23.5), 1, GOLD, scale=(2, 1.3, 1.5), subdiv=1, jit=0.1)


# ---- 16. Cameras -----------------------------------------------------------------------------------------------------------
def camera_at(p, x, z, turn):
    vcyl(p, x, 0, 0.8, z, 1.2, DSTEEL, verts=10)
    vcyl(p, x, 0.8, 1.6, z, 0.75, STEEL, verts=8)
    vcyl(p, x, 1.6, 9.8, z, 0.4, STEEL, verts=8)
    vcyl(p, x, 4.0, 4.5, z, 0.62, DSTEEL, verts=8)
    vcyl(p, x, 7.0, 7.5, z, 0.62, DSTEEL, verts=8)
    vcyl(p, x, 9.0, 9.5, z, 0.7, DSTEEL, verts=8)
    r = (0, turn, 0)

    def loc(dx, y, dz):
        a, b = ry(dx, dz, turn)
        return (x + a, y, z + b)
    dk.box(p, loc(0, 10.0, 0), (3.2, 1.4, 1.7), CHAR, rot=r, jitter=0.03)
    dk.box(p, loc(0.1, 10.7, 0), (3.5, 0.2, 2.0), STEEL, rot=r, jitter=0.03)
    dk.cyl(p, loc(1.9, 10.0, 0), 0.55, 0.7, GLASS, axis='x', verts=8, rot=r, jitter=0.03)
    dk.cyl(p, loc(1.55, 10.0, 0), 0.75, 0.3, DSTEEL, axis='x', verts=8, rot=r, jitter=0.02)
    dk.box(p, loc(-1.2, 10.15, 0.9), (0.4, 0.3, 0.2), RED, rot=r, jitter=0.02)
    dk.box(p, loc(-1.2, 10.15, -0.9), (0.4, 0.3, 0.2), GREEN, rot=r, jitter=0.02)


def build_Cameras(p):
    camera_at(p, 52, 22, 20)
    camera_at(p, 62, 31, -30)
    camera_at(p, 55, 40, 25)


# ---- 17. Lamps -------------------------------------------------------------------------------------------------------------
def lamp_at(p, x, z):
    vcyl(p, x, 0, 0.4, z, 1.3, DGOLD, verts=10)
    vcyl(p, x, 0.4, 0.8, z, 0.9, GOLD, verts=10)
    vcyl(p, x, 0.8, 8.4, z, 0.35, GOLD, verts=8)
    for y in (2.6, 5.8):
        vcyl(p, x, y, y + 0.5, z, 0.6, DGOLD, verts=8)
    ball(p, (x, 4.2, z), 0.55, LGOLD, subdiv=1, jit=0.03)
    dk.cyl(p, (x, 9.5, z), 1.7, 2.2, CREAM, axis='y', verts=10, top_radius=1.2, jitter=0.03)
    vcyl(p, x, 8.4, 8.75, z, 1.85, GOLD, verts=10)
    vcyl(p, x, 10.4, 10.6, z, 1.3, GOLD, verts=10)
    ball(p, (x, 10.9, z), 0.8, AMBER, subdiv=1, jit=0.05)


def build_Lamps(p):
    lamp_at(p, -36, 25)
    lamp_at(p, -29, 29)
    lamp_at(p, -22, 24)


# ---- 18. Piggy -----------------------------------------------------------------------------------------------------------
def build_Piggy(p):
    ball(p, (82, 6.2, 32), 1, GOLD, scale=(7.5, 5.8, 5.2), subdiv=2, jit=0.06)
    ball(p, (82.2, 7.4, 36.5), 1, LGOLD, scale=(2.8, 2.0, 0.7), subdiv=1, jit=0.04)      # shine on the flanks
    ball(p, (82.2, 7.4, 27.5), 1, LGOLD, scale=(2.8, 2.0, 0.7), subdiv=1, jit=0.04)
    xcyl(p, 86.0, 90.6, 6.3, 32, 2.7, GOLD, verts=10, jit=0.05)
    xcyl(p, 90.4, 91.5, 6.3, 32, 2.2, PINK, verts=10, jit=0.03)
    for z in (31.2, 32.8):
        bx(p, (91.4, 91.6), (6.2, 7.3), (z - 0.25, z + 0.25), CHAR, 0.02)
    for z in (30.0, 34.0):                                                              # ears
        prism_z(p, [(86.6, 10.4), (89.2, 10.4), (88.4, 12.0)], z - 0.6, z + 0.6, GOLD, 0.04)
        prism_z(p, [(87.1, 10.5), (88.7, 10.5), (88.3, 11.5)], z - 0.62, z + 0.62, PINK, 0.03)
    for z in (28.6, 35.4):                                                              # eyes and cheeks
        ball(p, (87.6, 8.6, z), 0.5, CHAR, subdiv=1, jit=0.02)
        ball(p, (86.6, 6.2, z + (0.4 if z > 32 else -0.4)), 0.75, PINK, subdiv=1, jit=0.03)
    for x, z in ((77.4, 29.2), (77.4, 34.8), (86.2, 29.2), (86.2, 34.8)):                 # legs
        vcyl(p, x, 0, 3.8, z, 1.25, GOLD, verts=8)
        vcyl(p, x, 0, 0.7, z, 1.35, DGOLD, verts=8)
    bar(p, (76.0, 7.0, 32), (74.4, 8.5, 32), 0.7, DGOLD, 0.04)                           # curly tail
    bar(p, (74.4, 8.5, 32), (74.0, 7.0, 32), 0.6, DGOLD, 0.04)
    ball(p, (74.0, 6.8, 32), 0.55, DGOLD, subdiv=1, jit=0.04)
    bx(p, (79.5, 84.5), (11.7, 12.1), (31.4, 32.6), CHAR, 0.02)                          # coin slot and coin
    coin(p, 82.4, 12.6, 31.6, 32.4, 2.0, GOLD, DGOLD, verts=12)


# ---- 19. Chests ----------------------------------------------------------------------------------------------------------
def chest_at(p, x, z, w, d, kind):
    bx(p, (x - w / 2, x + w / 2), (0, 2.2), (z - d / 2, z + d / 2), WOOD, 0.05)
    for k in range(3):                                                   # planks
        bx(p, (x - w / 2 - 0.02, x + w / 2 + 0.02), (0.55 + k * 0.6, 0.65 + k * 0.6), (z + d / 2 - 0.0, z + d / 2 + 0.06), DWOOD, 0.03)
    for dx in (-w / 2 + 0.5, w / 2 - 0.5):                                 # gold corner straps
        bx(p, (x + dx - 0.3, x + dx + 0.3), (0, 2.3), (z - d / 2 - 0.08, z + d / 2 + 0.08), GOLD, 0.03)
    bx(p, (x - w / 2, x + w / 2), (0, 0.35), (z - d / 2 - 0.1, z + d / 2 + 0.1), DGOLD, 0.03)
    bx(p, (x - w / 2 - 0.1, x + w / 2 + 0.1), (1.9, 2.3), (z - d / 2 - 0.1, z + d / 2 + 0.1), DGOLD, 0.03)
    if kind == 'closed':
        xcyl(p, x - w / 2 - 0.1, x + w / 2 + 0.1, 2.2, z, d / 2 - 0.2, WOOD, verts=8, jit=0.05)
        for dx in (-w / 2 + 0.6, w / 2 - 0.6):
            xcyl(p, x + dx - 0.3, x + dx + 0.3, 2.2, z, d / 2 - 0.1, GOLD, verts=8, jit=0.03)
        bx(p, (x - 0.5, x + 0.5), (1.5, 2.8), (z + d / 2 + 0.05, z + d / 2 + 0.25), GOLD, 0.03)
        bx(p, (x - 0.15, x + 0.15), (1.9, 2.4), (z + d / 2 + 0.25, z + d / 2 + 0.32), CHAR, 0.02)
    else:
        ball(p, (x, 2.3, z), 1, GOLD, scale=(w / 2 - 0.15, 1.3, d / 2 - 0.1), subdiv=2, jit=0.1)
        for k, (dx, dz) in enumerate(((-0.9, 0.4), (0.8, -0.3), (0.0, 0.9), (1.4, 0.7))):
            dk.cyl(p, (x + dx * w / 5, 3.3 + 0.1 * (k % 2) - abs(dx) * 0.15, z + dz * d / 5), 0.8, 0.3,
                   LGOLD if k % 2 else GOLD, axis='y', verts=8, rot=(15 * dz, 30 * k, 15 * dx), jitter=0.06)
        ball(p, (x - 0.4, 3.3, z - 0.2), 0.45, RED if kind == 'open' else WHITE, subdiv=1, jit=0.1)
        bx(p, (x - w / 2 + 0.3, x - w / 2 + 1.5), (2.3, 2.7), (z + 0.4, z + 1.3), LGOLD, 0.04)


def build_Chests(p):
    chest_at(p, -72, -52, 5, 3.4, 'closed')
    chest_at(p, -60, -54, 5, 3.4, 'open')
    chest_at(p, -66, -58, 7, 4.4, 'big')
    ball(p, (-66, 1, -49.6), 1, GOLD, scale=(3, 1, 1.5), subdiv=1, jit=0.1)
    for k, (dx, dz) in enumerate(((-1.6, 0.6), (0.5, -0.5), (1.8, 0.3), (-0.4, 0.9))):
        dk.cyl(p, (-66 + dx, 1.5, -49.6 + dz), 0.7, 0.25, LGOLD if k % 2 else GOLD, axis='y', verts=8,
               rot=(10 * dz, 25 * k, 10 * dx), jitter=0.05)


# ---- 20. Scale -----------------------------------------------------------------------------------------------------------
def build_Scale(p):
    bx(p, (-50.5, -41.5), (0, 1.2), (31.5, 36.5), DGOLD, 0.03)
    bx(p, (-49, -43), (1.2, 1.9), (32.2, 35.8), GOLD, 0.03)
    vcyl(p, -46, 1.9, 13.2, 34, 0.8, GOLD, verts=8)
    for y in (3.0, 7.5, 11.5):
        vcyl(p, -46, y, y + 0.7, 34, 1.2, DGOLD, verts=8)
    ball(p, (-46, 13.7, 34), 1.2, GOLD, subdiv=1, jit=0.05)
    bx(p, (-47, -45), (12.7, 14.7), (33.4, 34.6), DGOLD, 0.03)
    dk.box(p, (-46, 13.8, 34), (18, 0.8, 1), GOLD, rot=(0, 0, 6), jitter=0.03)
    for sx, sy in ((-1, 12.86), (1, 14.74)):
        ball(p, (-46 + sx * 8.95, sy, 34), 0.5, DGOLD, subdiv=1, jit=0.04)
    # pans with three chains each
    for (px, py, hy) in ((-54, 5.2, 12.95), (-38, 8.4, 14.5)):
        dk.cyl(p, (px, py + 0.45, 34), 1.4, 0.9, DGOLD, axis='y', verts=12, top_radius=3.2, jitter=0.04)
        vcyl(p, px, py + 0.8, py + 1.0, 34, 3.3, GOLD, verts=12)
        for k in range(3):
            a = math.radians(90 + 120 * k)
            bar(p, (px, hy, 34), (px + 3.0 * math.cos(a), py + 0.9, 34 + 3.0 * math.sin(a)), 0.25, GOLD, 0.03)
        ball(p, (px, hy, 34), 0.35, GOLD, subdiv=1)
    # gold in the heavy pan, a feather in the light one
    ball(p, (-54, 6.6, 34), 1, GOLD, scale=(2.2, 1.5, 1.8), subdiv=1, jit=0.08)
    ingot(p, -55, 7.0, 33.2, 2.2, 1.0, 1.2, LGOLD, yaw=20, top=0.8)
    ingot(p, -52.8, 7.3, 34.8, 2.0, 0.9, 1.1, GOLD, yaw=-30, top=0.8)
    for dx, dz in ((-1.4, 1.4), (1.2, -1.6), (1.6, 1.3)):
        dk.cyl(p, (-54 + dx, 7.4, 34 + dz), 0.6, 0.2, LGOLD, axis='y', verts=8, jitter=0.05)
    dk.ball(p, (-38, 9.8, 34), 1, WHITE, scale=(2.5, 0.35, 0.9), subdiv=1, rot=(0, 25, 8), jitter=0.03)
    dk.ball(p, (-37.6, 9.95, 34.2), 1, PINK, scale=(1.4, 0.3, 0.55), subdiv=1, rot=(0, 25, 8), jitter=0.03)
    bar(p, (-40.6, 9.4, 34.9), (-35.4, 10.1, 33.2), 0.18, DGOLD, 0.03)


# ---- 21. Forklift --------------------------------------------------------------------------------------------------------
def build_Forklift(p):
    bx(p, (49, 57), (0.8, 1.6), (3.5, 8.5), CHAR, 0.03)
    bx(p, (49, 57), (1.0, 4.0), (3.5, 8.5), ORANGE, 0.04)
    bx(p, (54.2, 57), (1.0, 4.6), (3.4, 8.6), (200, 112, 24), 0.04)                    # counterweight
    for k in range(4):
        bx(p, (56.8, 57.0), (1.3 + k * 0.8, 1.8 + k * 0.8), (3.4, 8.6), CHAR if k % 2 == 0 else AMBER, 0.02)
    bx(p, (51.2, 54.2), (4.0, 4.4), (3.9, 8.1), ORANGE, 0.04)                          # engine cover
    bx(p, (51.2, 53.0), (4.0, 4.6), (4.7, 7.3), CHAR, 0.03)                            # seat + back
    bx(p, (52.8, 53.3), (4.6, 6.4), (4.7, 7.3), CHAR, 0.03)
    bx(p, (49.9, 50.4), (4.0, 5.8), (5.7, 6.3), CHAR, 0.03)                            # steering column + wheel
    bx(p, (49.4, 50.9), (5.6, 5.9), (5.0, 7.0), CHAR, 0.03)
    for x in (50.0, 54.8):                                                              # roof guard
        for z in (3.6, 7.9):
            bx(p, (x, x + 0.5), (4, 8), (z, z + 0.5), CHAR, 0.03)
    bx(p, (49, 55), (8, 8.5), (3.5, 8.5), CHAR, 0.03)
    for k in range(5):
        bx(p, (49.3 + k * 1.2, 49.8 + k * 1.2), (8.5, 8.7), (3.5, 8.5), DSTEEL, 0.03)
    bx(p, (52, 53), (8.5, 9.0), (5.6, 6.4), AMBER, 0.03)
    for z in (4.3, 7.7):                                                                # headlights
        bx(p, (48.7, 49.0), (3.0, 3.8), (z - 0.5, z + 0.5), CREAM, 0.02)
    # mast with carriage
    for z0, z1 in ((4.0, 4.9), (7.1, 8.0)):
        bx(p, (47.4, 48.2), (0, 9), (z0, z1), STEEL, 0.03)
    for y in (0.4, 4.6, 8.4):
        bx(p, (47.4, 48.2), (y, y + 0.5), (4.0, 8.0), DSTEEL, 0.03)
    bx(p, (46.6, 47.4), (0.6, 4.4), (3.8, 8.2), LSTEEL, 0.03)
    for z in (4.6, 7.4):
        bx(p, (42, 46.6), (0.8, 1.2), (z - 0.35, z + 0.35), STEEL, 0.03)
        bx(p, (46.6, 47.4), (0.8, 3.2), (z - 0.35, z + 0.35), STEEL, 0.03)
    # pallet and gold pyramid
    for k in range(5):
        bx(p, (41.6, 47.6), (1.5, 1.8), (3.5 + k * 1.0, 4.4 + k * 1.0), WOOD, 0.06)
    for z in (3.5, 5.75, 8.0):
        bx(p, (41.6, 47.6), (1.2, 1.5), (z, z + 0.5), DWOOD, 0.04)
    for i in range(3):
        for j in range(2):
            ingot(p, 42.4 + i * 1.8, 1.8, 4.7 + j * 2.2 + 0.6 - 0.6, 1.7, 2.4, 2.1, GOLD if (i + j) % 2 else DGOLD, top=0.92, jit=0.05)
    for i in range(2):
        for j in range(2):
            ingot(p, 43.3 + i * 1.8, 4.2, 4.7 + j * 2.2, 1.7, 1.6, 2.1, LGOLD if (i + j) % 2 else GOLD, top=0.9, jit=0.05)
    # wheels
    for x in (50.4, 55):
        for z0, z1 in ((2.8, 3.6), (8.4, 9.2)):
            zcyl(p, x, 1.2, z0, z1, 1.2, CHAR, verts=10, jit=0.02)
            zcyl(p, x, 1.2, z0 - 0.0, z1 - 0.0, 0.55, LSTEEL, verts=6, jit=0.02)
        zcyl(p, x, 1.2, 3.6, 8.4, 0.35, DSTEEL, verts=6)


# ---- 22. Fountain --------------------------------------------------------------------------------------------------------
def build_Fountain(p):
    vcyl(p, 2, 0, 1.6, -32, 7.5, MARBLE, verts=16, jit=0.03)
    vcyl(p, 2, 0.5, 0.95, -32, 7.65, GOLD, verts=16, jit=0.03)
    vcyl(p, 2, 1.6, 1.8, -32, 6.3, WATER, verts=16, jit=0.04)
    vcyl(p, 2, 1.8, 1.85, -32, 4.0, LWATER, verts=14, jit=0.04)
    for k in range(8):                                               # coins in the basin
        a = math.radians(45 * k + 12)
        vcyl(p, 2 + 5.2 * math.cos(a), 1.85, 2.05, -32 + 5.2 * math.sin(a), 0.7, GOLD, verts=8, jit=0.04)
    dk.cyl(p, (2, 3.4, -32), 1.5, 3.2, GOLD, axis='y', verts=8, top_radius=0.9, jitter=0.04)
    dk.cyl(p, (2, 5.45, -32), 2.0, 0.9, GOLD, axis='y', verts=14, top_radius=4.0, jitter=0.04)
    vcyl(p, 2, 5.8, 5.95, -32, 3.5, WATER, verts=14, jit=0.04)
    dk.cyl(p, (2, 4.5, -32), 3.9, 1.5, LWATER, axis='y', verts=14, top_radius=3.2, jitter=0.05)
    vcyl(p, 2, 5.9, 8.9, -32, 0.9, GOLD, verts=8)
    dk.cyl(p, (2, 8.4, -32), 0.9, 0.9, GOLD, axis='y', verts=10, top_radius=2.3, jitter=0.04)
    vcyl(p, 2, 8.7, 8.85, -32, 2.1, WATER, verts=10, jit=0.04)
    for k in range(4):                                               # jets on the lower basin
        a = math.radians(90 * k + 45)
        dk.cone(p, (2 + 5.1 * math.cos(a), 1.8, -32 + 5.1 * math.sin(a)), 0.6, 2.0, LWATER, verts=5, jitter=0.05)
        ball(p, (2 + 5.1 * math.cos(a), 4.0, -32 + 5.1 * math.sin(a)), 0.35, LWATER, subdiv=1)
    coin(p, 2, 11.2, -32.4, -31.6, 2.3, GOLD, DGOLD, verts=16)
    text(p, "$", 2, 10.15, -31.62, -31.45, 1.2, 2.1, 0.35, 0.2, DGOLD)


# ---- 23. Vitrines --------------------------------------------------------------------------------------------------------
def vitrine_at(p, x, z, col, verts):
    bx(p, (x - 2.5, x + 2.5), (0, 2.8), (z - 2.5, z + 2.5), DSTEEL, 0.03)
    bx(p, (x - 2.55, x + 2.55), (1.5, 1.9), (z - 2.55, z + 2.55), GOLD, 0.03)
    bx(p, (x - 2.55, x + 2.55), (2.6, 2.9), (z - 2.55, z + 2.55), GOLD, 0.03)
    for dx in (-2.1, 2.1):
        for dz in (-2.1, 2.1):
            bx(p, (x + dx - 0.25, x + dx + 0.25), (2.9, 6.4), (z + dz - 0.25, z + dz + 0.25), GOLD, 0.03)
    bx(p, (x - 2.4, x + 2.4), (6.0, 6.4), (z - 2.4, z + 2.4), GOLD, 0.03)
    bx(p, (x - 2.0, x + 2.0), (2.9, 6.0), (z - 2.1, z - 1.95), GLASS, 0.03)
    bx(p, (x - 2.1, x - 1.95), (2.9, 6.0), (z - 2.0, z + 2.0), GLASS, 0.03)
    bx(p, (x + 1.95, x + 2.1), (2.9, 6.0), (z - 2.0, z + 2.0), GLASS, 0.03)
    bx(p, (x - 1.2, x + 1.2), (2.9, 3.4), (z - 1.2, z + 1.2), VELVET, 0.03)
    gem(p, x, 3.4, z, 1.0, 0.8, 1.0, col, verts=verts, table=0.55, jit=0.1)
    bx(p, (x - 1.0, x + 1.0), (0.7, 1.2), (z + 2.5, z + 2.62), GOLD, 0.03)


def build_Vitrines(p):
    bx(p, (-14, 6), (0, 0.2), (36, 44), VELVET, 0.03)
    for (x0, x1, z0, z1) in ((-14, 6, 36, 36.5), (-14, 6, 43.5, 44), (-14, -13.5, 36, 44), (5.5, 6, 36, 44)):
        bx(p, (x0, x1), (0.2, 0.26), (z0, z1), GOLD, 0.02)
    vitrine_at(p, -12, 42, RED, 8)
    vitrine_at(p, -4, 36, GREEN, 6)
    vitrine_at(p, 4, 43, (170, 215, 245), 10)


# ---- 24. Throne ----------------------------------------------------------------------------------------------------------
def build_Throne(p):
    bx(p, (59, 73), (0, 1.6), (-30, -18), DMARBLE, 0.03)
    bx(p, (59.4, 72.6), (1.6, 1.8), (-29.6, -18.4), GOLD, 0.03)
    bx(p, (61.5, 70.5), (1.8, 3.2), (-29.5, -22.5), MARBLE, 0.03)
    bx(p, (61.4, 70.6), (2.9, 3.2), (-29.6, -22.4), GOLD, 0.03)
    bx(p, (63.8, 68.2), (3.2, 4.4), (-29, -25), GOLD, 0.03)                              # seat
    bx(p, (64.2, 67.8), (4.4, 5.4), (-28.6, -25.4), VELVET, 0.03)
    bx(p, (63.5, 68.5), (3.2, 13.2), (-29.9, -28.5), GOLD, 0.03)                         # back
    bx(p, (64.3, 67.7), (5.6, 12.2), (-28.5, -28.3), VELVET, 0.03)
    for (x, y) in ((64.7, 6.2), (67.3, 6.2), (64.7, 11.6), (67.3, 11.6)):
        ball(p, (x, y, -28.2), 0.3, GOLD, subdiv=1)
    dk.cone(p, (66, 13.2, -29.2), 1.3, 2.3, DGOLD, verts=4, jitter=0.04)
    for x in (64.2, 67.8):
        dk.cone(p, (x, 13.2, -29.2), 0.8, 1.4, DGOLD, verts=4, jitter=0.04)
    ball(p, (63.4, 13.5, -29.2), 0.7, GOLD, subdiv=1, jit=0.05)
    ball(p, (68.6, 13.5, -29.2), 0.7, GOLD, subdiv=1, jit=0.05)
    for x0 in (63.15, 67.95):                                                            # armrests with lion knobs
        bx(p, (x0, x0 + 0.9), (4.5, 5.2), (-28.6, -25.3), GOLD, 0.03)
        bx(p, (x0, x0 + 0.9), (3.2, 4.5), (-26.4, -25.5), GOLD, 0.03)
        ball(p, (x0 + 0.45, 5.4, -25.8), 0.5, LGOLD, subdiv=1, jit=0.04)
    bx(p, (64, 68), (0, 0.15), (-20, -14), VELVET, 0.03)                                 # carpet
    for x0 in (64, 67.6):
        bx(p, (x0, x0 + 0.4), (0.15, 0.2), (-20, -14), GOLD, 0.02)
    bx(p, (64, 68), (0.15, 0.2), (-14.4, -14), GOLD, 0.02)
    for x in (60.6, 71.4):                                                               # urns with flames
        vcyl(p, x, 1.6, 2.2, -19.6, 0.9, DGOLD, verts=8)
        dk.cyl(p, (x, 3.0, -19.6), 0.5, 1.6, GOLD, axis='y', verts=8, top_radius=0.95, jitter=0.04)
        dk.cone(p, (x, 3.8, -19.6), 0.55, 1.3, AMBER, verts=5, jitter=0.05)


# ---- 25. MegaCoin --------------------------------------------------------------------------------------------------------
def build_MegaCoin(p):
    bx(p, (26, 42), (0, 1.6), (-59, -53), DSTEEL, 0.03)
    bx(p, (26.6, 41.4), (1.6, 2.0), (-58.4, -53.6), DGOLD, 0.03)
    for x0 in (26, 40):
        bx(p, (x0, x0 + 2), (1.6, 7.6), (-57.5, -54.5), DGOLD, 0.03)
    for x0 in (27.6, 38.4):
        bx(p, (x0, x0 + 2.0), (6.4, 7.6), (-57.0, -55.0), GOLD, 0.03)
    # the coin: reeded rim, face with a ring and a dollar sign
    zcyl(p, 34, 11.8, -57.2, -54.6, 8.6, DGOLD, verts=32, jit=0.04)
    zcyl(p, 34, 11.8, -57.05, -54.95, 8.0, GOLD, verts=32, jit=0.03)
    zcyl(p, 34, 11.8, -54.95, -54.8, 6.5, CHAR, verts=28, jit=0.03)
    zcyl(p, 34, 11.8, -54.95, -54.75, 5.9, LGOLD, verts=28, jit=0.03)
    text(p, "$", 34, 7.9, -54.76, -54.4, 4.6, 7.8, 1.1, 0.2, CHAR)
    for k in range(12):                                              # studs round the rim
        a = math.radians(30 * k + 15)
        ball(p, (34 + 7.25 * math.cos(a), 11.8 + 7.25 * math.sin(a), -54.9), 0.3, LGOLD, subdiv=1, jit=0.03)
    bx(p, (32.6, 35.4), (20.1, 20.9), (-56.8, -55.2), GOLD, 0.03)
    ball(p, (34, 21, -56), 1.3, RED, subdiv=1, jit=0.1)


PARTS = [("Floor", build_Floor), ("Chamber", build_Chamber), ("VaultDoor", build_VaultDoor), ("Arch", build_Arch),
         ("GoldStacks", build_GoldStacks), ("CoinHeap", build_CoinHeap), ("Lasers", build_Lasers), ("Truck", build_Truck),
         ("Desk", build_Desk), ("Statue", build_Statue), ("CrownCase", build_CrownCase), ("Trolley", build_Trolley),
         ("Diamond", build_Diamond), ("Safe", build_Safe), ("Mint", build_Mint), ("Cameras", build_Cameras),
         ("Lamps", build_Lamps), ("Piggy", build_Piggy), ("Chests", build_Chests), ("Scale", build_Scale),
         ("Forklift", build_Forklift), ("Fountain", build_Fountain), ("Vitrines", build_Vitrines),
         ("Throne", build_Throne), ("MegaCoin", build_MegaCoin)]

AZ = {}
ELEV = {}
MULT = {"Floor": 1.5, "Chamber": 2.4, "VaultDoor": 2.4, "Arch": 2.6}
SHIBA_AT = {"Floor": (-40, 6, 270, 0)}


# ---- previews ----------------------------------------------------------------------------------------------------------
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
        if pid in SHIBA_AT:
            x, z, f, lift = SHIBA_AT[pid]
        else:
            x = hi[0] + 5 if hi[0] + 5 < 88 else lo[0] - 5
            z = hi[2] - 3
            x, z, f, lift = x, z, 270, 0
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_GoldVault.png"))


main()
