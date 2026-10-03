"""Final low-poly decor models for the theme Volcano (25 parts around the twenty-first Shiba, Magma Shiba).

Usage: blender --background --factory-startup --python build_Volcano.py -- <outdir> [PartId,PartId,...]
Writes Decor_Volcano_<PartId>.fbx, preview_<PartId>.png and stage_Volcano.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give a comma-separated part
list after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S, shade

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "Volcano"))
ONLY = [a for s in ARGS[1:] for a in s.split(",") if a]
KEY = "Volcano"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_Volcano.json"))

# ---- palette (one for all 25 parts) ---------------------------------------------------------------------------------
BASALT = (52, 48, 58)
LBASALT = (78, 72, 84)
DBASALT = (34, 32, 42)
OBS = (22, 22, 32)
ROCK = (104, 80, 70)
LROCK = (140, 112, 96)
LAVA = (255, 102, 24)
EMBER = (206, 52, 24)
FLAME = (255, 190, 64)
RUBY = (214, 48, 68)
STEAM = (252, 252, 255)
WOOD = (130, 88, 54)
DWOOD = (84, 56, 38)
THATCH = (204, 164, 74)
BONE = (228, 216, 188)
TEAL = (70, 190, 190)
LTEAL = (130, 224, 214)
METAL = (76, 80, 94)
LMETAL = (130, 136, 150)
TENTR = (180, 44, 40)
GRASS = (62, 138, 72)
DGRASS = (44, 106, 56)
WHITE = (240, 244, 250)
ASHC = (66, 58, 62)
BAS1 = (92, 88, 104)
BAS2 = (124, 120, 136)
BAMBOO = (178, 166, 86)
DBAMBOO = (120, 104, 48)
DMETAL = (52, 54, 66)
SAND = (176, 150, 100)

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



def rock(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.06):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv, jitter=jit)


def cone(p, cx, y0, cz, r, h, col, verts=8, jit=0.05):
    return dk.cyl(p, (cx, y0 + h / 2, cz), r, h, col, axis='y', verts=verts, top_radius=0.0, jitter=jit)


def stack(p, cx, cz, parts, verts=12):
    """Stack of cylinders (y0, y1, r0, r1, colour) centred on cx, cz."""
    for (y0, y1, r0, r1, col) in parts:
        vcyl(p, cx, y0, y1, cz, r0, col, verts=verts, top_r=r1)


# ==== PARTS =================================================================================================================
# ---- shared helpers of this theme ----
SULFUR = (226, 196, 70)


def seg(p, x1, z1, x2, z2, w, y0, y1, col, jit=0.04):
    """Flat strip in the ground plane from (x1, z1) to (x2, z2), width w, from y0 to y1."""
    ln = math.hypot(x2 - x1, z2 - z1)
    ang = math.degrees(math.atan2(-(z2 - z1), x2 - x1))
    return dk.box(p, ((x1 + x2) / 2, (y0 + y1) / 2, (z1 + z2) / 2), (ln, y1 - y0, w), col, rot=(0, ang, 0), jitter=jit)


def taper(p, cx, cz, w0, d0, w1, d1, y0, y1, col, yaw=0, jit=0.04):
    """Four-sided frustum (box that narrows toward the top), optionally turned by yaw about y."""
    loc = [(-w0 / 2, y0, -d0 / 2), (w0 / 2, y0, -d0 / 2), (w0 / 2, y0, d0 / 2), (-w0 / 2, y0, d0 / 2),
           (-w1 / 2, y1, -d1 / 2), (w1 / 2, y1, -d1 / 2), (w1 / 2, y1, d1 / 2), (-w1 / 2, y1, d1 / 2)]
    a = math.radians(yaw)
    pts = []
    for (x, y, z) in loc:
        pts.append((cx + x * math.cos(a) + z * math.sin(a), y, cz - x * math.sin(a) + z * math.cos(a)))
    return hexa(p, pts, col, jit)


def pile(p, cx, cz, y0, items, col, jit=0.07):
    """Cluster of rocks: items = (dx, dy, dz, r, sx, sy, sz)."""
    for (dx, dy, dz, r, sx, sy, sz) in items:
        rock(p, (cx + dx, y0 + dy, cz + dz), r, col, scale=(sx, sy, sz), jit=jit)


# ---- 1. AshGround -------------------------------------------------------------------------------------------------------
# ---- 2. Volcano -----------------------------------------------------------------------------------------------------------
VOL = (58.0, -37.0)
VTIER = [(0, 8, 19.0, 16.4), (8, 16, 15.6, 13.0), (16, 24, 12.2, 10.0), (24, 32, 9.2, 7.6), (32, 37.0, 6.6, 5.6)]


def vrad(y):
    for (a, b, r0, r1) in VTIER:
        if y <= b:
            return r0 + (r1 - r0) * max(0.0, (y - a)) / (b - a)
    return 5.6


# ---- 3. Sign ----------------------------------------------------------------------------------------------------------------
def build_Sign(p):
    bx(p, (6.6, 7.4), (0, 6.2), (49.6, 50.4), DWOOD, 0.05)
    bx(p, (16.6, 17.4), (0, 6.2), (49.6, 50.4), DWOOD, 0.05)
    bx(p, (6.0, 18.0), (4.3, 9.3), (49.7, 50.3), DBASALT, 0.04)           # board
    bx(p, (5.7, 18.3), (9.25, 9.75), (49.4, 50.6), EMBER, 0.03)           # ember top edge
    bx(p, (5.7, 6.15), (4.3, 9.25), (49.5, 50.5), BASALT, 0.04)           # side frames
    bx(p, (17.85, 18.3), (4.3, 9.25), (49.5, 50.5), BASALT, 0.04)
    bx(p, (5.7, 18.3), (4.1, 4.5), (49.5, 50.5), BASALT, 0.04)            # bottom rail
    text(p, "GET", 12.0, 7.25, 50.3, 50.62, 1.9, 1.85, 0.46, 0.5, FLAME)
    text(p, "BONKED", 12.0, 4.95, 50.3, 50.62, 1.45, 1.85, 0.4, 0.3, LAVA)
    bx(p, (6.3, 8.5), (8.6, 9.0), (50.3, 50.45), OBS, 0.04)               # scorch marks
    bx(p, (15.0, 17.6), (4.55, 4.85), (50.3, 50.45), OBS, 0.04)
    for (x, z, s) in ((5.0, 51.0, 1.45), (19.0, 49.0, 1.3), (11.5, 51.6, 0.9)):
        rock(p, (x, 0.75, z), s, ROCK, scale=(1.3, 0.6, 1.1), jit=0.08)
    for (x, z) in ((8.5, 51.2), (14.5, 50.9)):
        bx(p, (x, x + 0.7), (0.0, 0.25), (z, z + 0.5), LAVA, 0.04)
    for x in (7.0, 17.0):                                                 # little flame on each post top
        rock(p, (x, 6.6, 50), 0.55, FLAME, scale=(1, 1.4, 1), jit=0.04)


# ---- 4. Basalt Columns ----------------------------------------------------------------------------------------------------
# ---- 5. Steam Vents ------------------------------------------------------------------------------------------------------------
# ---- 6. Lava River ----------------------------------------------------------------------------------------------------------------
# ---- 7. Tiki Hut ---------------------------------------------------------------------------------------------------------------------
# ---- 8. Hot Spring -----------------------------------------------------------------------------------------------------------------------
# ---- batch 2 helpers ----
def tface(p, cx, y0, y1, zf, w, eye=BONE, teeth=True, col=DWOOD):
    """Carved face on the +z side of a totem section: eyes, brow, nose and a toothy mouth."""
    h = y1 - y0
    e = max(0.3, h * 0.2)
    for s in (-1, 1):
        ex = cx + s * w * 0.23
        bx(p, (ex - e * 0.6, ex + e * 0.6), (y0 + h * 0.55, y0 + h * 0.55 + e), (zf, zf + 0.14), eye, 0.02)
        bx(p, (ex - e * 0.25, ex + e * 0.25), (y0 + h * 0.55 + e * 0.2, y0 + h * 0.55 + e * 0.8), (zf + 0.14, zf + 0.24), OBS, 0.02)
        bx(p, (ex - e * 0.8, ex + e * 0.8), (y0 + h * 0.55 + e * 1.1, y0 + h * 0.55 + e * 1.4), (zf, zf + 0.22), col, 0.03)
    bx(p, (cx - w * 0.08, cx + w * 0.08), (y0 + h * 0.3, y0 + h * 0.62), (zf, zf + 0.42), col, 0.03)
    bx(p, (cx - w * 0.3, cx + w * 0.3), (y0 + h * 0.1, y0 + h * 0.3), (zf, zf + 0.12), OBS, 0.02)
    if teeth:
        for k in range(4):
            tx = cx - w * 0.22 + k * w * 0.147
            bx(p, (tx, tx + w * 0.08), (y0 + h * 0.18, y0 + h * 0.3), (zf + 0.12, zf + 0.22), eye, 0.02)


def bamboo(p, x, z, h, r=0.4, node=0.9):
    """Bamboo pole with darker node rings, base on the ground."""
    n = max(2, int(h / node))
    seg_h = h / n
    for i in range(n):
        vcyl(p, x, i * seg_h, (i + 1) * seg_h - 0.03, z, r, BAMBOO if i % 2 == 0 else shade(BAMBOO, 0.9), verts=6, jit=0.04)
        vcyl(p, x, (i + 1) * seg_h - 0.1, (i + 1) * seg_h + 0.06, z, r * 1.25, DBAMBOO, verts=6, jit=0.03)


def crystal(p, x, z, h, r, col, tilt=(0, 0), twist=0.0, y0=0.0, jit=0.1):
    """Hexagonal crystal: prism with a pointed tip, tilted (degrees about x and z) around its base centre."""
    n = 6
    ring0 = [(r * math.cos(math.radians(60 * i + twist)), 0.0, r * math.sin(math.radians(60 * i + twist))) for i in range(n)]
    ring1 = [(r * 0.86 * math.cos(math.radians(60 * i + twist)), h * 0.68, r * 0.86 * math.sin(math.radians(60 * i + twist))) for i in range(n)]
    loc = ring0 + ring1 + [(0.0, h, 0.0)]
    ax, az = math.radians(tilt[0]), math.radians(tilt[1])
    pts = []
    for (a, b, c) in loc:
        b1, c1 = b * math.cos(ax) - c * math.sin(ax), b * math.sin(ax) + c * math.cos(ax)
        a2, b2 = a * math.cos(az) - b1 * math.sin(az), a * math.sin(az) + b1 * math.cos(az)
        pts.append((x + a2, y0 + b2, z + c1))
    faces = [tuple(range(n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((n + i, n + j, 2 * n))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def bone(p, a, b, t, col=BONE, jit=0.05):
    return bar(p, a, b, t, col, jit)


# ---- 9. Tiki Totems ---------------------------------------------------------------------------------------------------------------
def build_Totems(p):
    # tall totem (bird)
    cx, cz = 8.0, 25.0
    bx(p, (6.4, 9.6), (0, 1.0), (23.4, 26.6), BAS1, 0.05)
    bx(p, (6.8, 9.2), (1.0, 8.0), (23.8, 26.2), WOOD, 0.05)
    for y in (1.0, 3.3, 5.7):
        bx(p, (6.7, 9.3), (y, y + 0.3), (23.7, 26.3), TEAL if y < 2 else FLAME, 0.03)
    tface(p, cx, 1.3, 3.2, 26.2, 2.4)
    tface(p, cx, 3.6, 5.6, 26.2, 2.4)
    tface(p, cx, 6.0, 7.9, 26.2, 2.4)
    bx(p, (6.3, 9.7), (7.9, 10.1), (23.4, 26.6), RUBY, 0.04)                    # head block
    bx(p, (6.3, 9.7), (7.9, 10.1), (23.4, 26.6), RUBY, 0.04)
    for s in (-1, 1):
        ex = cx + s * 0.8
        bx(p, (ex - 0.4, ex + 0.4), (8.6, 9.4), (26.6, 26.78), BONE, 0.02)
        bx(p, (ex - 0.17, ex + 0.17), (8.8, 9.2), (26.78, 26.9), OBS, 0.02)
    prism_z(p, [(cx - 0.45, 8.4), (cx + 0.45, 8.4), (cx, 7.95)], 26.6, 27.0, FLAME, 0.03)   # beak
    bx(p, (7.0, 9.0), (10.1, 11.2), (23.7, 26.3), FLAME, 0.04)                   # crown
    for dx in (-0.8, 0.0, 0.8):
        bx(p, (cx + dx - 0.25, cx + dx + 0.25), (10.5, 11.2), (26.3, 26.45), RUBY, 0.03)
    # medium totem (bear)
    cx, cz = 14.0, 28.0
    bx(p, (12.5, 15.5), (0, 1.0), (26.5, 29.5), BAS1, 0.05)
    bx(p, (12.9, 15.1), (1.0, 6.0), (26.9, 29.1), DWOOD, 0.05)
    bx(p, (12.8, 15.2), (3.4, 3.7), (26.8, 29.2), TEAL, 0.03)
    tface(p, cx, 1.3, 3.3, 29.1, 2.2, col=WOOD)
    tface(p, cx, 3.8, 5.9, 29.1, 2.2, col=WOOD)
    bx(p, (12.3, 15.7), (5.9, 7.7), (27.0, 29.0), RUBY, 0.04)                    # head
    for s in (-1, 1):
        bx(p, (cx + s * 1.3 - 0.35, cx + s * 1.3 + 0.35), (7.7, 8.3 - 0.0), (27.4, 28.0), RUBY, 0.04)   # ears
        ex = cx + s * 0.75
        bx(p, (ex - 0.35, ex + 0.35), (6.7, 7.4), (29.0, 29.15), BONE, 0.02)
        bx(p, (ex - 0.15, ex + 0.15), (6.85, 7.25), (29.15, 29.27), OBS, 0.02)
    bx(p, (cx - 0.5, cx + 0.5), (6.1, 6.7), (29.0, 29.5), DWOOD, 0.03)
    bx(p, (cx - 0.9, cx + 0.9), (5.95, 6.2), (29.0, 29.3), OBS, 0.03)
    # short totem (sun)
    cx, cz = 18.5, 23.5
    bx(p, (17.0, 20.0), (0, 1.0), (22.0, 25.0), BAS1, 0.05)
    bx(p, (17.4, 19.6), (1.0, 6.6), (22.4, 24.6), WOOD, 0.05)
    bx(p, (17.3, 19.7), (2.4, 2.7), (22.3, 24.7), FLAME, 0.03)
    bx(p, (17.3, 19.7), (4.4, 4.7), (22.3, 24.7), TEAL, 0.03)
    tface(p, cx, 1.3, 2.3, 24.6, 2.2)
    tface(p, cx, 2.9, 4.3, 24.6, 2.2)
    bx(p, (17.1, 19.9), (6.4, 8.0), (22.1, 24.9), FLAME, 0.04)                   # sun head
    for dx in (-1.0, 0.0, 1.0):
        bx(p, (cx + dx - 0.25, cx + dx + 0.25), (7.7, 8.0), (23.0, 24.0), LAVA, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * 0.55 - 0.25, cx + s * 0.55 + 0.25), (7.0, 7.5), (24.9, 25.0), OBS, 0.02)
    bx(p, (cx - 0.5, cx + 0.5), (6.6, 6.8), (24.9, 25.0), OBS, 0.02)
    rock(p, (11.0, 0.35, 25.5), 0.7, BAS1, scale=(1, 0.6, 1), jit=0.08)


# ---- 10. Obsidian Forge -----------------------------------------------------------------------------------------------------------
# ---- 11. Explorer Camp ------------------------------------------------------------------------------------------------------------
def tent(p, cx, z0, z1, hw, h, col, door=True):
    """A-frame tent, ridge along z, open door on the +z side."""
    prism_z(p, [(cx - hw, 0), (cx + hw, 0), (cx, h)], z0, z1, col, 0.04)
    bx(p, (cx - hw, cx + hw), (-0.05, 0.12), (z0 - 0.1, z1 + 0.5), DBASALT, 0.03)
    if door:
        prism_z(p, [(cx - hw * 0.38, 0.1), (cx + hw * 0.38, 0.1), (cx, h * 0.72)], z1, z1 + 0.12, OBS, 0.02)
        diag(p, cx - hw * 0.9, 0.1, z1 + 0.06, cx - hw * 0.34, h * 0.68, 0.18, 0.1, shade(col, 0.7), 0.03)
        diag(p, cx + hw * 0.9, 0.1, z1 + 0.06, cx + hw * 0.34, h * 0.68, 0.18, 0.1, shade(col, 0.7), 0.03)
    bx(p, (cx - 0.12, cx + 0.12), (h - 0.1, h + 0.3), (z0, z1), DWOOD, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * hw - 0.2, cx + s * hw + 0.2), (0, 0.5), (z1 + 0.7, z1 + 1.1), DWOOD, 0.03)


# ---- 12. Tiki Torches -------------------------------------------------------------------------------------------------------------
# ---- 13. Fossil Garden -------------------------------------------------------------------------------------------------------------
# ---- 14. Old Mine ------------------------------------------------------------------------------------------------------------------
def build_Mine(p):
    # rocky hill built from stacked, differently coloured rocks
    rock(p, (-64, 4.6, 6), 5.0, ROCK, scale=(2.1, 1.0, 1.35), subdiv=2, jit=0.08)
    rock(p, (-55, 2.8, 4), 5.0, BAS1, scale=(1.2, 0.6, 1.0), subdiv=1, jit=0.08)
    rock(p, (-71.5, 3.2, 5), 3.6, BAS2, scale=(1.0, 0.85, 1.2), subdiv=1, jit=0.08)
    rock(p, (-62.5, 8.2, 3.5), 2.6, LROCK, scale=(1.4, 0.7, 1.1), subdiv=1, jit=0.08)
    rock(p, (-56.5, 5.8, 7.5), 2.0, ROCK, scale=(1.2, 0.8, 1.0), subdiv=1, jit=0.08)
    rock(p, (-52.5, 1.8, 11), 2.3, BAS2, scale=(1.2, 0.7, 1.0), subdiv=1, jit=0.08)
    rock(p, (-72, 1.6, 12), 2.2, BAS1, scale=(1.2, 0.7, 1.0), subdiv=1, jit=0.08)
    # entrance: dark opening, timber frame with a cross brace and a hanging lantern
    bx(p, (-67.0, -61.0), (0, 6.4), (11.8, 12.9), OBS, 0.02)
    bx(p, (-68.5, -67.0), (0, 7.2), (12.6, 13.8), DWOOD, 0.04)
    bx(p, (-61.0, -59.5), (0, 7.2), (12.6, 13.8), DWOOD, 0.04)
    bx(p, (-69.2, -58.8), (7.0, 8.2), (12.4, 14.0), WOOD, 0.05)
    diag(p, -67.0, 6.2, 13.9, -65.0, 7.0, 0.4, 0.3, WOOD, 0.04)
    diag(p, -61.2, 6.2, 13.9, -63.2, 7.0, 0.4, 0.3, WOOD, 0.04)
    bx(p, (-64.2, -63.8), (5.4, 7.0), (13.2, 13.5), METAL, 0.03)
    rock(p, (-64.0, 5.2, 13.5), 0.5, FLAME, scale=(1, 1.2, 1), jit=0.04)
    rock(p, (-58.4, 6.2, 14.2), 0.5, FLAME, jit=0.04)
    # rails with sleepers and the ore cart
    for z in [14.4 + i * 1.3 for i in range(8)]:
        bx(p, (-66.0, -62.0), (0.0, 0.2), (z, z + 0.45), DWOOD, 0.03)
    for x in (-65.1, -62.9):
        bx(p, (x - 0.2, x + 0.2), (0.2, 0.45), (14.0, 24.0), LMETAL, 0.03)
    bx(p, (-65.8, -62.2), (0.9, 1.0), (15.8, 20.2), DMETAL, 0.03)
    taper(p, -64, 18, 3.4, 4.4, 3.8, 4.8, 0.95, 2.2, METAL, jit=0.04)
    bx(p, (-66.0, -62.0), (2.0, 2.3), (15.5, 20.5), LMETAL, 0.03)
    for (x, z) in ((-65.5, 16.5), (-62.5, 16.5), (-65.5, 19.5), (-62.5, 19.5)):
        dk.cyl(p, (x + (-0.15 if x < -64 else 0.15), 0.75, z), 0.7, 0.28, OBS, axis='x', verts=8, jitter=0.03)
    for (dx, dz, r, col) in ((0, 0, 1.2, FLAME), (-0.8, 0.9, 0.9, RUBY), (0.8, -0.8, 0.9, FLAME), (0.2, 1.4, 0.6, LAVA), (-0.2, -1.4, 0.7, RUBY)):
        rock(p, (-64 + dx, 2.5, 18 + dz), r, col, scale=(1, 0.8, 1), jit=0.08)
    # pickaxe leaning on the frame and an ore heap
    bar(p, (-59.0, 0.0, 15.2), (-59.8, 4.2, 14.4), 0.22, DWOOD, 0.04)
    bar(p, (-60.6, 4.5, 14.4), (-59.0, 4.1, 14.4), 0.35, LMETAL, 0.04)
    for (x, z, r, col) in ((-60.0, 16.8, 0.8, FLAME), (-59.2, 17.6, 0.55, RUBY), (-67.5, 15.5, 0.7, BAS2)):
        rock(p, (x, 0.5, z), r, col, scale=(1, 0.7, 1), jit=0.08)


# ---- 15. Ruby Crystals -----------------------------------------------------------------------------------------------------------------
def build_Crystals(p):
    for (x, z, sx, sy, sz, rot, col) in ((18.5, -52, 1.9, 0.9, 1.7, 18, DBASALT), (28, -54.5, 1.7, 0.8, 1.5, -22, BASALT),
                                          (24.5, -46.2, 1.8, 0.7, 1.5, 30, DBASALT), (22.0, -50.5, 2.6, 0.5, 2.3, 5, BAS1),
                                          (26.8, -49.0, 2.0, 0.55, 1.8, -10, BAS1)):
        rock(p, (x, sy * 0.7, z), 1.0, col, scale=(sx, sy, sz), subdiv=1, jit=0.1)
    for (x, z, h, r, col, tl, tw) in ((24, -50, 10.0, 1.5, RUBY, (0, 8), 20), (20.5, -48.5, 6.8, 1.2, LAVA, (6, -8), 0),
                                      (27.6, -51.2, 6.0, 1.1, RUBY, (-10, 10), 35), (22.5, -53.8, 4.4, 0.95, FLAME, (-8, 6), 10),
                                      (25.8, -46.4, 4.0, 0.95, LAVA, (10, -12), 40), (30.0, -48.0, 2.8, 0.75, RUBY, (4, -14), 5),
                                      (18.3, -50.6, 3.0, 0.7, FLAME, (0, 14), 15), (26.2, -52.8, 2.3, 0.6, LAVA, (-12, 4), 25)):
        crystal(p, x, z, h, r, col, tl, tw, y0=0.1, jit=0.1)
    for (x, z) in ((21.5, -45.8), (29.0, -46.5), (17.2, -54.5)):
        crystal(p, x, z, 1.3, 0.38, FLAME, (6, 6), 0, y0=0.1, jit=0.08)


# ---- 16. Seismo Station ---------------------------------------------------------------------------------------------------------------
# ---- batch 3 helpers ----
def panel(p, pts, thick, col, jit=0.04):
    """Flat polygon (3D points, roughly planar, convex) extruded by `thick` along its normal (wings, leaves, flags)."""
    a, b, c = Vector(pts[0]), Vector(pts[1]), Vector(pts[2])
    n = (b - a).cross(c - a)
    if n.length < 1e-6:
        n = Vector((0, 1, 0))
    n = n.normalized() * (thick / 2)
    top = [tuple(Vector(q) + n) for q in pts]
    bot = [tuple(Vector(q) - n) for q in pts]
    m = len(pts)
    faces = [tuple(range(m)), tuple(range(m, 2 * m))]
    for i in range(m):
        j = (i + 1) % m
        faces.append((i, j, m + j, m + i))
    return dk.poly(p, (0, 0, 0), top + bot, faces, col, jit)


def leaf(p, base, yaw, length, width, rise, droop, col, jit=0.06, t=0.16):
    """Palm frond: pointed leaf that rises a little then droops. yaw in degrees (0 = +x, 90 = -z)."""
    prof = [(0.0, -0.12), (0.28, -0.5), (0.62, -0.46), (1.0, 0.0), (0.62, 0.46), (0.28, 0.5), (0.0, 0.12)]
    a = math.radians(yaw)
    pts = []
    for (u, v) in prof:
        d = u * length
        y = rise * u - droop * u * u
        x = base[0] + d * math.cos(a) - v * width * math.sin(a) * -1
        z = base[2] - d * math.sin(a) + v * width * math.cos(a) * -1
        pts.append((x, base[1] + y, z))
    return panel(p, pts, t, col, jit)


# ---- 17. Lookout Tower --------------------------------------------------------------------------------------------------------------
# ---- 18. Palm Grove -----------------------------------------------------------------------------------------------------------------
# ---- 19. Dragon Nest --------------------------------------------------------------------------------------------------------------------------
# ---- 20. Geothermal Drill -----------------------------------------------------------------------------------------------------------------
def build_Drill(p):
    bx(p, (3.0, 13.0), (0, 1.2), (-48.0, -38.0), DBASALT, 0.04)
    bx(p, (3.4, 12.6), (1.2, 1.4), (-47.6, -38.4), BAS1, 0.03)
    base = [(4.4, -46.6), (11.6, -46.6), (4.4, -39.4), (11.6, -39.4)]
    topl = [(6.5, -44.5), (9.5, -44.5), (6.5, -41.5), (9.5, -41.5)]
    def at(i, y):
        t = (y - 1.2) / 21.3
        return (base[i][0] + (topl[i][0] - base[i][0]) * t, y, base[i][1] + (topl[i][1] - base[i][1]) * t)
    for i in range(4):
        bar(p, at(i, 1.2), at(i, 22.5), 0.8, LMETAL, 0.04)
    levels = [1.2, 6.5, 11.5, 16.5, 22.0]
    for (i, j) in ((0, 1), (2, 3), (0, 2), (1, 3)):
        for (y0, y1) in zip(levels[:-1], levels[1:]):
            bar(p, at(i, y0), at(j, y1), 0.3, METAL, 0.04)
            bar(p, at(j, y0), at(i, y1), 0.3, METAL, 0.04)
    for y in levels[1:-1]:
        for (i, j) in ((0, 1), (2, 3), (0, 2), (1, 3)):
            bar(p, at(i, y), at(j, y), 0.4, LMETAL, 0.04)
    for y in (6.5, 16.5):                                                              # work platforms with yellow edge
        bx(p, (5.3, 10.7), (y, y + 0.3), (-45.7, -40.3), METAL, 0.04)
        bx(p, (5.2, 10.8), (y + 0.3, y + 0.42), (-45.8, -40.2), FLAME, 0.03)
    vcyl(p, 8, 1.2, 22.4, -43, 0.75, METAL, verts=8, jit=0.04)                         # drill pipe with collars
    for y in (4.0, 8.0, 12.0, 16.0, 20.0):
        vcyl(p, 8, y, y + 0.55, -43, 1.0, LMETAL, verts=8, jit=0.04)
    vcyl(p, 8, 1.2, 2.0, -43, 1.4, LAVA, verts=8, top_r=0.9, jit=0.03)                 # glow at the borehole
    bx(p, (5.0, 11.0), (22.5, 23.9), (-46.0, -40.0), LMETAL, 0.04)                      # crown block
    zcyl(p, 8, 23.1, -44.4, -41.6, 1.0, METAL, verts=10, jit=0.04)
    bx(p, (7.0, 9.0), (22.0, 22.6), (-44.2, -41.8), DMETAL, 0.04)
    bx(p, (5.2, 10.8), (23.7, 23.9), (-46.2, -39.8), FLAME, 0.03)
    # pump tank, red engine house, pipes, barrels
    vcyl(p, 14.8, 1.2, 4.4, -40.5, 1.8, METAL, verts=10, jit=0.04)
    vcyl(p, 14.8, 4.35, 4.5, -40.5, 1.4, LMETAL, verts=10, jit=0.04)
    vcyl(p, 14.8, 2.4, 2.6, -40.5, 1.85, DMETAL, verts=10, jit=0.03)
    xcyl(p, 12.0, 14.0, 1.9, -40.5, 0.28, LMETAL, verts=6, jit=0.03)
    bx(p, (0.9, 3.5), (1.2, 3.4), (-47.7, -45.1), TENTR, 0.04)
    bx(p, (1.0, 3.4), (3.4, 3.7), (-47.8, -45.0), DMETAL, 0.04)
    bx(p, (1.2, 2.4), (1.9, 2.9), (-45.1, -44.95), TEAL, 0.03)
    vcyl(p, 3.0, 3.7, 5.0, -46.4, 0.28, DMETAL, verts=6, jit=0.03)
    bx(p, (15.2, 16.6), (1.2, 2.6), (-45.6, -44.2), TENTR, 0.04)
    bx(p, (15.4, 16.4), (1.2, 1.5), (-45.8, -44.0), FLAME, 0.03)


# ---- 21. Dragon Statue ---------------------------------------------------------------------------------------------------------------------
# ---- 22. Obsidian Temple --------------------------------------------------------------------------------------------------------------------------
def build_Temple(p):
    cx, cz = -60.0, -43.0
    tiers = [(24, 0.0, 3.0, BASALT), (19, 3.0, 8.0, DBASALT), (14, 8.0, 13.0, BASALT), (9, 13.0, 18.0, DBASALT)]
    for (w, y0, y1, col) in tiers:
        bx(p, (cx - w / 2, cx + w / 2), (y0, y1), (cz - w / 2, cz + w / 2), col, 0.05)
        bx(p, (cx - w / 2 - 0.3, cx + w / 2 + 0.3), (y1 - 0.5, y1), (cz - w / 2 - 0.3, cz + w / 2 + 0.3), BAS1, 0.04)      # cap slab
        bx(p, (cx - w / 2 - 0.05, cx + w / 2 + 0.05), (y0 + (y1 - y0) * 0.45, y0 + (y1 - y0) * 0.45 + 0.35), (cz - w / 2 - 0.05, cz + w / 2 + 0.05), LAVA, 0.03)
        for k in range(3):                                                                                                  # meander zig on the front
            xk = cx - w * 0.3 + k * w * 0.3
            bx(p, (xk - 0.8, xk + 0.8), (y0 + (y1 - y0) * 0.62, y0 + (y1 - y0) * 0.62 + 0.3), (cz + w / 2, cz + w / 2 + 0.1), FLAME, 0.03)
    # front stairs: slabs reaching out from each tier face
    for (zf, ytop, ybot, n, d, wd) in ((-31.0, 3.0, 0.0, 3, 0.8, 7.0), (-33.5, 8.0, 3.0, 5, 0.5, 6.0), (-36.0, 13.0, 8.0, 5, 0.5, 5.0), (-38.5, 18.0, 13.0, 5, 0.5, 4.0)):
        for i in range(n):
            hgt = ybot + (ytop - ybot) * (i + 1) / n
            bx(p, (cx - wd / 2, cx + wd / 2), (ybot, hgt), (zf, zf + (n - i) * d), BAS2 if i % 2 else BAS1, 0.04)
    # shrine with glowing doorway and a red roof
    bx(p, (cx - 3, cx + 3), (18.0, 20.8), (cz - 3, cz + 3), OBS, 0.04)
    bx(p, (cx - 1.1, cx + 1.1), (18.0, 20.0), (cz + 3.0, cz + 3.12), LAVA, 0.03)
    bx(p, (cx - 0.6, cx + 0.6), (18.0, 19.5), (cz + 3.12, cz + 3.2), FLAME, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * 2.6 - 0.25, cx + s * 2.6 + 0.25), (18.0, 20.8), (cz + 3.0, cz + 3.4), BAS1, 0.04)
    bx(p, (cx - 4.0, cx + 4.0), (20.8, 21.6), (cz - 4.0, cz + 4.0), EMBER, 0.04)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pass
    # braziers at the corners of the first and third terrace
    for (x, y, z) in ((-70.5, 3.0, -32.5), (-49.5, 3.0, -32.5), (-66.0, 8.0, -36.0), (-54.0, 8.0, -36.0)):
        vcyl(p, x, y, y + 1.6, z, 0.55, METAL, verts=7, top_r=0.9, jit=0.04)
        flame(p, x, y + 1.5, z, 0.8, 1.9 if y < 5 else 1.6)
    # obsidian spikes along the first terrace edge
    for k in range(7):
        x = cx - 10.5 + k * 3.5
        if abs(x - cx) < 3.8:
            continue
        cone(p, x, 3.0, -31.2, 0.55, 1.6, OBS, verts=4, jit=0.04)


# ---- 23. Magma Heart ---------------------------------------------------------------------------------------------------------------------------------
# ---- 24. Obsidian Throne ----------------------------------------------------------------------------------------------------------------------------
def build_Throne(p):
    cx, cz = 72.0, 47.0
    vcyl(p, cx, 0, 1.6, cz, 4.6, BAS1, verts=10, top_r=4.4, jit=0.05)
    vcyl(p, cx, 1.5, 1.7, cz, 4.0, DBASALT, verts=10, jit=0.04)
    for k in range(10):                                                                  # lava studs round the dais
        a = math.radians(k * 36 + 18)
        bx(p, (cx + 4.55 * math.cos(a) - 0.2, cx + 4.55 * math.cos(a) + 0.2), (0.7, 1.1), (cz + 4.55 * math.sin(a) - 0.2, cz + 4.55 * math.sin(a) + 0.2), LAVA, 0.03)
    bx(p, (69.0, 75.0), (0, 1.0), (51.4, 54.1), BAS2, 0.04)                               # steps
    bx(p, (69.5, 74.5), (0, 0.5), (53.2, 54.1), BAS1, 0.04)
    bx(p, (69.7, 74.3), (1.7, 9.2), (43.3, 44.7), OBS, 0.04)                              # tall back
    bx(p, (69.3, 74.7), (1.7, 3.2), (43.2, 45.0), OBS, 0.04)
    bx(p, (70.4, 73.6), (4.0, 8.4), (44.7, 44.85), DBASALT, 0.03)
    bx(p, (71.7, 72.3), (3.2, 8.0), (44.85, 44.95), LAVA, 0.03)                           # glowing vein
    bx(p, (70.9, 71.2), (5.0, 7.0), (44.85, 44.95), LAVA, 0.03)
    bx(p, (72.8, 73.1), (4.6, 6.4), (44.85, 44.95), LAVA, 0.03)
    for (x, h, w, tilt) in ((69.9, 2.8, 0.9, 8), (74.1, 2.8, 0.9, -8), (71.0, 3.4, 0.8, 4), (73.0, 3.4, 0.8, -4), (72.0, 3.5, 1.0, 0)):
        crystal(p, x, 44.0, h + 0.2, w * 0.7, OBS, (0, -tilt), 45, y0=9.2, jit=0.06)
    bx(p, (70.0, 74.0), (1.7, 4.2), (44.7, 48.8), OBS, 0.04)                              # seat
    bx(p, (70.6, 73.4), (4.2, 5.0), (45.0, 48.0), EMBER, 0.04)                            # cushion
    bx(p, (70.4, 73.6), (4.2, 4.5), (47.9, 48.3), RUBY, 0.04)
    for s in (-1, 1):
        bx(p, (cx + s * 2.8 - 0.4, cx + s * 2.8 + 0.4), (1.7, 3.8), (45.0, 48.6), OBS, 0.04)       # armrests
        bx(p, (cx + s * 2.8 - 0.45, cx + s * 2.8 + 0.45), (3.8, 4.1), (45.0, 48.8), BAS1, 0.04)
        ball(p, (cx + s * 2.8, 4.4, 48.9), 0.5, FLAME, subdiv=1, jit=0.04)
    for x in (65.4, 78.6):                                                                 # braziers
        vcyl(p, x, 0.2, 0.9, 49.6, 0.85, BAS1, verts=8, jit=0.04)
        vcyl(p, x, 0.9, 4.5, 49.6, 0.4, METAL, verts=8, jit=0.04)
        vcyl(p, x, 4.2, 5.3, 49.6, 0.55, METAL, verts=8, top_r=1.0, jit=0.04)
        flame(p, x, 5.2, 49.6, 0.8, 1.8)
        pass
    for s in (-1, 1):
        pass


# ---- 25. Great Eruption --------------------------------------------------------------------------------------------------------------------------------
# ---- revised helpers (round 2) ----
def flame(p, x, y0, z, r, h, outer=LAVA, inner=FLAME, verts=5):
    """Flickering flame: tall bright centre tongue with shorter side tongues and a glowing base."""
    cone(p, x, y0, z, r * 0.55, h, inner, verts=verts, jit=0.04)
    for k in range(3):
        a = math.radians(k * 120 + (x * 37) % 60)
        cone(p, x + r * 0.55 * math.cos(a), y0, z + r * 0.55 * math.sin(a), r * 0.5, h * (0.62 + 0.1 * k), outer if k != 1 else EMBER, verts=verts, jit=0.04)
    vcyl(p, x, y0, y0 + h * 0.12, z, r * 0.85, outer, verts=6, jit=0.03)


def ribbon(p, pts, w, y0, y1, col, jit=0.04):
    """Closed ribbon (river, crack) of width w along a polyline of (x, z) points, from y0 up to y1."""
    n = len(pts)
    left, right = [], []
    for i, q in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / ln, dx / ln
        left.append((q[0] + nx * w / 2, q[1] + nz * w / 2))
        right.append((q[0] - nx * w / 2, q[1] - nz * w / 2))
    verts = []
    for (x, z) in left:
        verts.append((x, y1, z))
    for (x, z) in right:
        verts.append((x, y1, z))
    for (x, z) in left:
        verts.append((x, y0, z))
    for (x, z) in right:
        verts.append((x, y0, z))
    faces = []
    for i in range(n - 1):
        faces.append((i, i + 1, n + i + 1, n + i))                 # top
        faces.append((i, 2 * n + i, 2 * n + i + 1, i + 1))         # left wall
        faces.append((n + i, n + i + 1, 3 * n + i + 1, 3 * n + i)) # right wall
        faces.append((2 * n + i, 3 * n + i, 3 * n + i + 1, 2 * n + i + 1))
    faces.append((0, n, 3 * n, 2 * n))
    faces.append((n - 1, 3 * n - 1, 4 * n - 1, 2 * n + n - 1))
    return dk.poly(p, (0, 0, 0), verts, faces, col, jit)


def zig(p, pts, w, y0, y1, col, wob=0.5, step=5.0, jit=0.04, seed=1):
    """Winding ribbon along a polyline: the path wobbles sideways every `step` studs (cracks, rivers)."""
    import random
    rnd = random.Random(seed)
    path = []
    for (a, b) in zip(pts[:-1], pts[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(ln / step)))
        nx, nz = -(b[1] - a[1]) / ln, (b[0] - a[0]) / ln
        for i in range(n):
            t = i / n
            o = 0.0 if i == 0 else (rnd.random() - 0.5) * 2 * wob
            path.append((a[0] + (b[0] - a[0]) * t + nx * o, a[1] + (b[1] - a[1]) * t + nz * o))
    path.append(pts[-1])
    ribbon(p, path, w, y0, y1, col, jit)
    return path


def hexcol(p, cx, cz, r, h, col, slope=(0.0, 0.0), rot=0, jit=0.05, sides=6, cap=True, y0=0.0):
    """Prism column with a sloped top (slope = rise per stud along x and z); the base is at y 0. A lighter cap plate tops it."""
    bot, top = [], []
    for i in range(sides):
        a = math.radians(rot + 360.0 * i / sides)
        x, z = r * math.cos(a), r * math.sin(a)
        bot.append((cx + x, y0, cz + z))
        top.append((cx + x, y0 + h + slope[0] * x + slope[1] * z, cz + z))
    pts = bot + top
    faces = [tuple(range(sides)), tuple(range(sides, 2 * sides))]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    o = dk.poly(p, (0, 0, 0), pts, faces, col, jit)
    if cap:
        pts2 = [(x, y, z) for (x, y, z) in top] + [(x, y + 0.14, z) for (x, y, z) in top]
        pts2 = [(cx + (x - cx) * 0.9, y, cz + (z - cz) * 0.9) for (x, y, z) in pts2]
        dk.poly(p, (0, 0, 0), pts2, faces, shade(col, 1.45), jit)
    return o


def puff(p, x, y, z, r, col=STEAM, n=3):
    """Billowing steam: a cluster of smooth blobs, biggest at the bottom."""
    offs = [(0.0, 0.0, 0.0, 1.0), (0.75, 0.75, 0.15, 0.8), (-0.45, 1.35, -0.3, 0.62), (0.4, 1.85, 0.25, 0.45)]
    for k in range(n):
        dx, dy, dz, s = offs[k]
        ball(p, (x + dx * r, y + dy * r, z + dz * r), r * s, col, scale=(1.2, 0.66, 1.2), subdiv=2, jit=0.015)


# ---- 1. AshGround (round 2) ------------------------------------------------------------------------------------------------
def build_AshGround(p):
    import random
    rnd = random.Random(11)
    bx(p, (-80, 80), (-0.05, 0.2), (-57.5, 57.5), ASHC, 0.05)
    for i in range(5):                                                       # ash drifts
        x, z = rnd.uniform(-72, 72), rnd.uniform(-50, 50)
        r = rnd.uniform(3.0, 7.0)
        vcyl(p, x, 0.18, 0.24, z, r, shade(ASHC, rnd.choice((0.7, 1.35, 1.5))), verts=6, jit=0.05)
    cracks = [([(-30, -26), (-30, -2), (-22, -2), (-22, 18)], 1), ([(-52, -44), (-52, -24), (-40, -24)], 2),
              ([(12, 47), (12, 21), (24, 22)], 3), ([(58, 37), (58, 18), (68, 18)], 4),
              ([(-8, -53), (-8, -35), (4, -35)], 5), ([(-66, 12), (-66, 32)], 6)]
    for pts, sd in cracks:
        zig(p, pts, 3.4, 0.2, 0.34, EMBER, 0.7, 6.5, 0.04, sd)
        zig(p, pts, 2.0, 0.3, 0.42, LAVA, 0.5, 6.5, 0.04, sd + 20)
        if sd <= 3:
            zig(p, pts, 0.7, 0.38, 0.47, FLAME, 0.3, 6.5, 0.03, sd + 40)
        for k in (0,):                                                        # molten pool at the head
            vcyl(p, pts[k][0], 0.2, 0.4, pts[k][1], 2.2, LAVA, verts=6, jit=0.04)
        a = rnd.uniform(0, 6.28)
        q = pts[1]
        seg(p, q[0], q[1], q[0] + 4.5 * math.cos(a), q[1] + 4.5 * math.sin(a), 0.9, 0.22, 0.40, LAVA, 0.04)
    for (x, z, r) in ((-12, 14, 3.2), (44, -40, 3.8), (-58, -10, 3.0)):      # molten pools

        vcyl(p, x, 0.3, 0.44, z, r * 0.62, LAVA, verts=7, jit=0.04)
    for (pts, sd) in (([(42, -8), (48, -14), (46, -22)], 31), ([(-14, 14), (-20, 24), (-18, 34)], 32), ([(-46, 38), (-40, 46), (-44, 54)], 33), ([(36, 54), (28, 48), (30, 40)], 34)):

        zig(p, pts, 0.8, 0.3, 0.42, LAVA, 0.3, 6.0, 0.04, sd + 5)
    vcyl(p, 30, 0.2, 0.34, -12, 8.6, BAS2, verts=10, jit=0.04)             # basalt plate under the Magma Shiba
    vcyl(p, 30, 0.34, 0.47, -12, 6.2, BAS1, verts=10, jit=0.04)
    for i in range(8):
        a = math.radians(i * 45 + 10)
        bx(p, (30 + 5.4 * math.cos(a) - 0.45, 30 + 5.4 * math.cos(a) + 0.45), (0.45, 0.47), (-12 + 5.4 * math.sin(a) - 0.45, -12 + 5.4 * math.sin(a) + 0.45), LAVA if i % 2 else FLAME, 0.03)
    for i in range(4):
        x, z = rnd.uniform(-76, 76), rnd.uniform(-54, 54)
        if abs(x - 30) < 10 and abs(z + 12) < 10:
            continue
        s = rnd.uniform(0.7, 1.4)
        taper(p, x, z, s, s * 0.8, s * 0.6, s * 0.5, 0.2, 0.2 + rnd.uniform(0.12, 0.25), rnd.choice((BAS1, BASALT, BAS2)), yaw=rnd.uniform(0, 90), jit=0.08)
    for i in range(3):
        x, z = rnd.uniform(-78, 78), rnd.uniform(-55, 55)
        bx(p, (x, x + 0.5), (0.2, 0.34), (z, z + 0.5), FLAME, 0.05)


# ---- 2. Volcano (round 2) --------------------------------------------------------------------------------------------------
def build_Volcano(p):
    cx, cz = VOL
    for i, (a, b, r0, r1) in enumerate(VTIER):
        vcyl(p, cx, a, b, cz, r0, BASALT if i % 2 == 0 else BAS1, verts=14, top_r=r1, jit=0.07)
    for k in range(9):                                                            # jagged crater rim
        a = math.radians(k * 40 + 10)
        cone(p, cx + 5.0 * math.cos(a), 35.4, cz + 5.0 * math.sin(a), 1.3, 2.1 if k % 2 else 1.5, BAS2 if k % 2 else LBASALT, verts=5, jit=0.06)
    vcyl(p, cx, 36.0, 37.0, cz, 5.2, DBASALT, verts=14, top_r=4.8, jit=0.05)
    vcyl(p, cx, 36.8, 37.5, cz, 4.3, LAVA, verts=14, jit=0.03)
    vcyl(p, cx, 37.3, 37.5, cz, 2.4, FLAME, verts=10, jit=0.03)
    for k in range(7):                                                            # ribs of lighter basalt
        phi = math.radians(k * 360 / 7 + 10)
        a = (cx + (vrad(1) - 0.2) * math.cos(phi), 0.6, cz + (vrad(1) - 0.2) * math.sin(phi))
        b = (cx + (vrad(34) - 0.2) * math.cos(phi + 0.1), 34, cz + (vrad(34) - 0.2) * math.sin(phi + 0.1))
        bar(p, a, b, 1.5, BAS2 if k % 2 else LBASALT, 0.06)
    # lava streams: strips that hug the cone (ember rim, lava body, bright core), widening toward the foot
    def lstrip(levels, w, dr, col):
        verts = []
        for (y, ph, ww) in levels:
            r = vrad(y)
            for (sg, rr) in ((1, r + dr), (-1, r + dr), (-1, r - 0.25), (1, r - 0.25)):
                a = ph + sg * (w * ww / 2) / r
                verts.append((cx + rr * math.cos(a), y, cz + rr * math.sin(a)))
        faces = [(0, 1, 2, 3), (4 * len(levels) - 4, 4 * len(levels) - 3, 4 * len(levels) - 2, 4 * len(levels) - 1)]
        for i in range(len(levels) - 1):
            b = 4 * i
            for (u, v) in ((0, 1), (1, 2), (2, 3), (3, 0)):
                faces.append((b + u, b + v, b + 4 + v, b + 4 + u))
        return dk.poly(p, (0, 0, 0), verts, faces, col, 0.03)
    for (phi0, wig, wd) in ((85, 8, 1.0), (140, -7, 0.9), (35, 7, 0.9), (200, 6, 0.8)):
        ys = [36.4 - i * 4.5 for i in range(8)] + [0.4]
        lv = []
        for j, y in enumerate(ys):
            lv.append((y, math.radians(phi0 + wig * math.sin(j * 0.9)), 0.6 + 0.07 * j))
        lstrip(lv, 2.2 * wd, 0.12, EMBER)
        lstrip(lv, 1.3 * wd, 0.3, LAVA)
        lstrip(lv[:5], 0.5 * wd, 0.45, FLAME)
        e = lv[-1]
        rock(p, (cx + (vrad(0.5) + 1.0) * math.cos(e[1]), 0.5, cz + (vrad(0.5) + 1.0) * math.sin(e[1])), 2.3, LAVA, scale=(1.3, 0.25, 1.0), subdiv=1, jit=0.03)
    rock(p, (49, 3, -25), 4.4, ROCK, scale=(1.4, 0.7, 1.05), jit=0.08)           # boulders at the foot
    rock(p, (72, 2.5, -27), 3.9, ROCK, scale=(1.3, 0.7, 1.0), jit=0.08)
    rock(p, (70, 2.5, -51), 4.2, BAS1, scale=(1.4, 0.65, 1.1), jit=0.08)
    rock(p, (45.5, 1.6, -29.5), 1.9, BAS2, scale=(1.2, 0.8, 1.0), jit=0.08)
    rock(p, (75.5, 1.4, -31), 1.6, BAS1, jit=0.08)


# ---- 4. Basalt Columns (round 2) ----------------------------------------------------------------------------------------
def build_Basalt(p):
    bx(p, (-70.4, -54.0), (0, 0.5), (25.2, 36.4), BAS1, 0.05)
    cols = [(-62, 31, 2.0, 12.0, BAS1, (0.10, -0.06), 5), (-66.5, 32.5, 1.8, 9.0, BAS2, (-0.1, 0.08), 20),
            (-57.8, 30, 1.7, 7.0, BAS1, (0.12, 0.1), 40), (-64, 26.5, 1.5, 6.0, BAS2, (-0.12, -0.1), 10),
            (-59.5, 35, 1.5, 5.0, BAS2, (0.1, -0.14), 30), (-69, 28, 1.5, 4.0, BAS1, (0.08, 0.1), 0),
            (-55, 34, 1.4, 3.0, BASALT, (-0.1, 0.12), 15)]
    for (x, z, r, h, col, sl, rot) in cols:
        hexcol(p, x, z, r, h, col, sl, rot, 0.06)
    for (x, z, r, h, col, sl, rot) in cols:                                       # fracture rings
        for k in range(1, int(h // 2.6) + 1):
            hexcol(p, x, z, r * 1.035, 0.16, shade(col, 0.72), (0, 0), rot, 0.04, cap=False, y0=k * 2.6)
    for (x, z, r, h, col, sl, rot) in cols[:4]:                                  # glowing band at the foot
        hexcol(p, x, z, r * 1.04, h * 0.1 + 0.4, LAVA, (0, 0), rot, 0.04, cap=False)
    for (x, z, r, h) in ((-60.5, 27.5, 1.1, 1.8), (-67.5, 35.3, 1.0, 1.4), (-55.5, 29.5, 1.0, 1.2), (-63, 35.5, 0.9, 2.2), (-68.5, 25.8, 0.9, 1.0)):
        hexcol(p, x, z, r, h, LBASALT, (0.05, 0.05), 12, 0.06)
    pile(p, -62.5, 29.5, 0.5, [(-5, 0.3, 4.5, 0.7, 1, 0.7, 1), (4.5, 0.3, 5.5, 0.6, 1, 0.7, 1), (-2.0, 0.3, -4.4, 0.8, 1, 0.6, 1), (5, 0.3, -0.5, 0.6, 1, 0.8, 1), (-7.3, 0.3, 0, 0.7, 1, 0.7, 1)], BAS2, 0.1)
    for (x, z) in ((-63.8, 28.8), (-58.6, 32.6), (-60.4, 29.0), (-66.0, 29.5)):   # lava glints between the columns
        bx(p, (x, x + 0.8), (0.5, 1.4), (z, z + 0.6), LAVA, 0.04)


# ---- 5. Steam Vents (round 2) ------------------------------------------------------------------------------------------------
def build_Vents(p):
    for (x, z, rb, hb, rm, hm, rp, yp, npf) in ((32, 31, 4.0, 1.8, 2.3, 1.1, 1.8, 3.5, 4), (41, 28, 3.0, 1.4, 1.75, 0.9, 1.05, 2.7, 2), (37, 36, 2.5, 1.2, 1.5, 0.8, 0.9, 2.4, 2)):
        vcyl(p, x, 0, hb, z, rb, ROCK, verts=10, top_r=rb * 0.62, jit=0.08)
        vcyl(p, x, hb - 0.1, hb + hm, z, rm, BAS1, verts=10, top_r=rm * 0.7, jit=0.06)
        vcyl(p, x, hb + hm - 0.05, hb + hm + 0.1, z, rm * 0.5, EMBER, verts=8, jit=0.02)
        vcyl(p, x, hb + hm + 0.0, hb + hm + 0.14, z, rm * 0.62, SULFUR, verts=8, jit=0.03)
        vcyl(p, x, hb + hm + 0.1, hb + hm + 0.2, z, rm * 0.34, LAVA, verts=8, jit=0.03)
        for k in range(3):
            a = math.radians(k * 120 + x)
            rock(p, (x + (rb * 0.8) * math.cos(a), 0.4, z + (rb * 0.8) * math.sin(a)), 0.55, SULFUR if k % 2 == 0 else BAS2, scale=(1, 0.6, 1), jit=0.08)
        puff(p, x, yp, z, rp, STEAM, npf)
        for k in range(4):                                                       # glowing cracks running down the mound
            a = math.radians(k * 90 + 30 + x)
            bar(p, (x + (rm * 0.85) * math.cos(a), hb + hm * 0.8, z + (rm * 0.85) * math.sin(a)), (x + (rb * 0.97) * math.cos(a + 0.15), 0.15, z + (rb * 0.97) * math.sin(a + 0.15)), 0.32, LAVA, 0.03)
        for k in range(3):                                                       # dark rock spikes round the foot
            a = math.radians(k * 120 + 70 + z)
            cone(p, x + (rb + 0.3) * math.cos(a), 0.0, z + (rb + 0.3) * math.sin(a), 0.5, 1.4 + 0.3 * k, BAS1, verts=5, jit=0.06)


# ---- 6. Lava River (round 2) -------------------------------------------------------------------------------------------------
def build_LavaRiver(p):
    bed = [(70, -25), (70, -15), (77, -14), (77, -3), (72, -2.5), (69, -1), (69, 9), (71, 12)]
    zig(p, bed, 5.6, 0.05, 0.4, EMBER, 0.5, 3.5, 0.04, 3)
    zig(p, bed, 3.8, 0.15, 0.55, LAVA, 0.4, 3.5, 0.04, 8)
    zig(p, bed, 1.3, 0.3, 0.62, FLAME, 0.35, 3.5, 0.03, 9)
    vcyl(p, 71, 0.05, 0.4, 15, 5.4, EMBER, verts=12, jit=0.03)
    vcyl(p, 71, 0.2, 0.55, 15, 4.3, LAVA, verts=12, jit=0.03)
    vcyl(p, 71, 0.4, 0.62, 15, 2.4, FLAME, verts=10, jit=0.03)
    for (dx, dz, r) in ((-1.5, -1, 0.75), (1.7, 1.2, 0.65), (0.3, 2.2, 0.55), (-1.8, 2, 0.5), (1.8, -1.3, 0.45)):
        rock(p, (71 + dx, 0.7, 15 + dz), r, FLAME, scale=(1, 0.9, 1), jit=0.04)
        rock(p, (71 + dx, 0.85, 15 + dz), r * 0.45, STEAM, scale=(1, 0.7, 1), subdiv=1, jit=0.03)
    banks = [(76, -18, 2, 1.6, 2.2), (67, -6, 2.4, 1.6, 2), (75, 6, 2, 1.4, 2.4), (66, 14, 2.2, 1.4, 2), (67.5, -21, 1.8, 1.0, 1.8),
             (72.5, -19, 1.4, 0.8, 1.6), (73, -11, 2.0, 1.1, 1.8), (77.8, -8.5, 1.6, 1.0, 1.8), (73.5, -7, 1.8, 1.0, 1.4), (66.5, 1.5, 1.8, 1.0, 1.6),
             (73.5, 1.0, 2.0, 1.2, 1.6), (67.4, 7.5, 1.6, 0.9, 1.5), (76.5, 12, 1.8, 1.1, 1.8), (72, 19.6, 2.4, 1.0, 1.6), (65.6, 18.5, 1.6, 0.9, 1.6),
             (74.5, 18.5, 1.5, 0.8, 1.4)]
    for i, (x, z, sx, sy, sz) in enumerate(banks):
        rock(p, (x, sy * 0.5, z), 1.0, BAS1 if i % 3 else BAS2 if i % 2 else BASALT, scale=(sx * 0.6, sy * 0.5, sz * 0.6), subdiv=1, jit=0.08)
    for (x, z) in ((70.8, -22.5), (77.2, -9), (68.3, 4)):
        rock(p, (x, 0.9, z), 0.8, BAS2, scale=(1.1, 0.8, 1.0), jit=0.08)


# ---- 7. Tiki Hut (round 2) -----------------------------------------------------------------------------------------------------
def build_TikiHut(p):
    cx, cz = -62.0, 47.0
    for (x, z) in ((-67, 42), (-57, 42), (-67, 52), (-57, 52)):
        vcyl(p, x, 0, 3.4, z, 0.55, DWOOD, verts=7, jit=0.05)
        vcyl(p, x, 0, 0.5, z, 0.8, ROCK, verts=7, jit=0.05)
    for z in (42, 52):
        bx(p, (-67, -57), (1.4, 1.8), (z - 0.2, z + 0.2), WOOD, 0.04)
    bx(p, (-68, -56), (2.9, 3.5), (41, 53), WOOD, 0.05)
    for i in range(6):
        bx(p, (-68, -56), (3.5, 3.55), (41.5 + i * 2 - 0.05, 41.5 + i * 2 + 0.05), DWOOD, 0.02)
    bx(p, (-66.5, -57.5), (3.5, 8.7), (42.5, 51.5), DWOOD, 0.05)
    for i in range(5):
        bx(p, (-66.6, -57.4), (4.3 + i * 0.95, 4.45 + i * 0.95), (51.5, 51.65), WOOD, 0.04)
    bx(p, (-64.4, -59.6), (3.5, 7.0), (51.5, 51.7), OBS, 0.03)
    for (x0, x1, y0, y1) in ((-64.8, -64.4, 3.5, 7.3), (-59.6, -59.2, 3.5, 7.3), (-64.8, -59.2, 7.0, 7.4)):
        bx(p, (x0, x1), (y0, y1), (51.5, 51.9), WOOD, 0.04)
    # tiki mask above the door: red face, gold eyes, horns and a tongue
    bx(p, (-64.0, -60.0), (7.4, 8.7), (51.55, 51.9), RUBY, 0.03)
    for s in (-1, 1):
        bx(p, (-62.0 + s * 1.1 - 0.4, -62.0 + s * 1.1 + 0.4), (8.0, 8.5), (51.9, 52.05), FLAME, 0.02)
        bx(p, (-62.0 + s * 1.1 - 0.15, -62.0 + s * 1.1 + 0.15), (8.1, 8.4), (52.05, 52.15), OBS, 0.02)
        bar(p, (-62.0 + s * 1.8, 8.6, 51.7), (-62.0 + s * 2.3, 9.2, 51.7), 0.3, BONE, 0.03)
    bx(p, (-62.6, -61.4), (7.5, 7.8), (51.9, 52.05), OBS, 0.02)
    bx(p, (-62.2, -61.8), (7.2, 7.6), (51.95, 52.1), LAVA, 0.02)
    for x in (-67.6, -56.4):
        for z in (41.4, 52.6):
            bx(p, (x - 0.2, x + 0.2), (3.5, 5.0), (z - 0.2, z + 0.2), DWOOD, 0.04)
    bx(p, (-67.8, -56.2), (4.7, 5.0), (41.25, 41.55), WOOD, 0.04)
    for x in (-67.6, -56.4):
        bx(p, (x - 0.15, x + 0.15), (4.7, 5.0), (41.4, 52.6), WOOD, 0.04)
    bx(p, (-67.8, -65.2), (4.7, 5.0), (52.45, 52.75), WOOD, 0.04)
    bx(p, (-58.8, -56.2), (4.7, 5.0), (52.45, 52.75), WOOD, 0.04)
    taper(p, cx, cz, 13.0, 13.0, 9.6, 9.6, 8.4, 10.4, THATCH, jit=0.08)
    taper(p, cx, cz, 9.6, 9.6, 6.0, 6.0, 10.2, 12.0, shade(THATCH, 0.92), jit=0.08)
    taper(p, cx, cz, 6.0, 6.0, 0.8, 0.8, 11.8, 13.5, THATCH, jit=0.08)
    for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for j in (-2, -1, 0, 1, 2):
            o = j * 2.2
            a = (cx + sx * 6.5 + (o if sz else 0), 8.5, cz + sz * 6.5 + (o if sx else 0))
            b = (cx + sx * 4.85 + (o * 0.72 if sz else 0), 10.45, cz + sz * 4.85 + (o * 0.72 if sx else 0))
            bar(p, a, b, 0.22, shade(THATCH, 0.7), 0.04)
    for i in range(8):
        t = -5.6 + i * 1.6
        for (x, z, w, d) in ((cx + t, cz + 6.35, 0.9, 0.3), (cx + t, cz - 6.35, 0.9, 0.3), (cx - 6.35, cz + t, 0.3, 0.9), (cx + 6.35, cz + t, 0.3, 0.9)):
            bx(p, (x - w / 2, x + w / 2), (7.8, 8.6), (z - d / 2, z + d / 2), shade(THATCH, 0.78 if i % 2 else 0.95), 0.05)
    bx(p, (-63.2, -62.8), (0, 3.4), (53.9, 54.3), WOOD, 0.04)
    bx(p, (-61.2, -60.8), (0, 3.4), (53.9, 54.3), WOOD, 0.04)
    for i in range(5):
        bx(p, (-63.2, -60.8), (0.4 + i * 0.65, 0.6 + i * 0.65), (54.1, 54.8), WOOD, 0.04)
    bx(p, (-63.2, -60.8), (2.9, 3.5), (52.6, 54.3), WOOD, 0.04)
    bx(p, (-59.2, -58.8), (0, 2.6), (54.2, 54.6), DWOOD, 0.04)
    flame(p, -59.0, 2.6, 54.4, 0.5, 1.0)


# ---- 8. Hot Spring (round 2) -------------------------------------------------------------------------------------------------
def build_HotSpring(p):
    cx, cz = -16.5, 28.0
    vcyl(p, cx, 0, 1.2, cz, 7.5, ROCK, verts=14, top_r=7.1, jit=0.07)
    vcyl(p, cx, 1.0, 1.35, cz, 6.4, BONE, verts=14, jit=0.03)
    vcyl(p, cx, 0.95, 1.4, cz, 5.9, TEAL, verts=14, jit=0.03)
    vcyl(p, cx, 1.2, 1.45, cz, 3.6, LTEAL, verts=12, jit=0.03)
    for (dx, dz, r) in ((-2.5, 1.5, 0.45), (2.2, -2, 0.4), (1.0, 3.0, 0.35), (-1.0, -3.2, 0.35), (3.4, 1.6, 0.3)):
        rock(p, (cx + dx, 1.5, cz + dz), r, WHITE, scale=(1, 0.5, 1), subdiv=1, jit=0.03)
    boul = [(-23, 30, 1.9, 1.5, 1.6), (-10, 24, 1.6, 1.3, 1.8), (-14, 35, 2.1, 1.55, 1.6), (-19, 21, 1.7, 1.3, 1.6), (-9.5, 30.5, 1.3, 1.1, 1.4),
            (-23.3, 25, 1.3, 1.0, 1.4), (-21.5, 34, 1.4, 1.0, 1.4), (-11.5, 20.8, 1.3, 1.1, 1.3), (-17.2, 36, 1.0, 0.8, 1.0)]
    for i, (x, z, rx, ry_, rz) in enumerate(boul):
        rock(p, (x, ry_ * 0.7, z), 1.0, ROCK if i % 3 else LROCK, scale=(rx, ry_, rz), subdiv=1, jit=0.08)
    puff(p, -16.5, 2.7, 28.5, 1.7, STEAM, 4)
    puff(p, -12.0, 2.4, 25.5, 1.0, STEAM, 3)
    # bamboo spout over the pool with a thin stream of water
    bar(p, (-22.6, 2.2, 28.5), (-19.6, 2.5, 28.5), 0.7, BAMBOO, 0.04)
    bar(p, (-19.6, 2.5, 28.5), (-19.5, 1.5, 28.5), 0.25, TEAL, 0.03)
    vcyl(p, -22.0, 0.0, 1.0, 22.2, 0.8, WOOD, verts=8, top_r=0.95, jit=0.05)
    vcyl(p, -22.0, 0.95, 1.05, 22.2, 0.6, DWOOD, verts=8, jit=0.03)


# ---- 10. Obsidian Forge (round 2) --------------------------------------------------------------------------------------------
def build_Forge(p):
    bx(p, (43, 61), (0, 10), (36, 48), BAS1, 0.05)
    for i in range(8):
        y = 0.6 + i * 1.2
        bx(p, (42.8, 61.2), (y, y + 0.14), (35.8, 48.2), DBASALT, 0.03)
    for i in range(5):
        for k in range(6):
            x = 44.2 + k * 3.0 + (1.5 if i % 2 else 0)
            bx(p, (x, x + 0.12), (0.7 + i * 1.8, 1.9 + i * 1.8), (48.0, 48.25), DBASALT, 0.03)
    bx(p, (42, 62), (10, 10.8), (35, 49), DBASALT, 0.04)                        # roof: slab plus hipped slate
    taper(p, 52.0, 42.0, 19.6, 13.6, 12.0, 6.0, 10.7, 13.4, BAS2, jit=0.05)
    taper(p, 52.0, 42.0, 19.8, 13.8, 19.6, 13.6, 10.6, 11.0, DBASALT, jit=0.04)
    bx(p, (55.3, 58.7), (11.2, 19.4), (38.3, 41.7), BAS1, 0.05)                    # chimney
    for i in range(4):
        bx(p, (55.2, 58.8), (13.2 + i * 1.6, 13.4 + i * 1.6), (38.2, 41.8), DBASALT, 0.03)
    bx(p, (54.8, 59.2), (19.4, 20.2), (37.8, 42.2), DBASALT, 0.04)
    flame(p, 57, 19.8, 40, 0.8, 0.4, EMBER, LAVA)
    bx(p, (55.2, 58.8), (17.6, 18.2), (38.2, 41.8), LAVA, 0.03)                    # glowing band round the chimney
    bx(p, (46.0, 58.0), (13.3, 13.8), (40.2, 43.8), DBASALT, 0.04)
    bx(p, (45.4, 50.6), (0.8, 5.6), (48.0, 48.3), OBS, 0.02)                        # furnace mouth, bigger and brighter
    bx(p, (45.9, 50.1), (1.2, 5.2), (48.3, 48.45), LAVA, 0.03)
    bx(p, (46.5, 49.5), (1.2, 3.6), (48.45, 48.55), FLAME, 0.03)
    for (x0, x1) in ((44.8, 45.9), (50.1, 51.2)):
        bx(p, (x0, x1), (0.6, 6.0), (48.0, 48.7), BAS2, 0.04)
    bx(p, (44.8, 51.2), (5.6, 6.4), (48.0, 48.7), BAS2, 0.04)
    for k in range(4):
        rock(p, (46.5 + k * 1.0, 0.9, 48.8), 0.4, EMBER if k % 2 else FLAME, scale=(1, 0.7, 1), jit=0.06)
    bx(p, (43.2, 44.8), (0, 0.7), (50.3, 51.7), DWOOD, 0.04)                        # anvil on a stump
    bx(p, (43.3, 44.7), (0.7, 1.7), (50.5, 51.5), METAL, 0.04)
    bx(p, (42.4, 45.6), (1.7, 2.6), (50.4, 51.6), LMETAL, 0.04)
    bx(p, (45.6, 46.7), (2.0, 2.6), (50.6, 51.4), LMETAL, 0.04)
    for (x, z) in ((60, 50), (62.8, 49)):
        vcyl(p, x, 0, 2.4, z, 1.2, WOOD, verts=9, top_r=1.1, jit=0.05)
        for y in (0.45, 1.8):
            vcyl(p, x, y, y + 0.25, z, 1.24, METAL, verts=9, jit=0.03)
        vcyl(p, x, 2.35, 2.45, z, 0.95, TEAL if x < 61 else EMBER, verts=9, jit=0.03)
    bx(p, (51.0, 62), (7.7, 8.3), (48, 52), DWOOD, 0.04)                        # awning over the barrels, the furnace stays open
    for x in (51.6, 61.4):
        bx(p, (x - 0.4, x + 0.4), (0, 7.7), (51.2, 52.0), WOOD, 0.04)
    for i in range(4):
        bx(p, (51.2 + i * 2.7, 51.2 + i * 2.7 + 1.2), (8.3, 8.4), (48.0, 52.0), WOOD if i % 2 else DWOOD, 0.04)
    bx(p, (52.6, 53.0), (3.8, 7.0), (48.5, 48.8), DWOOD, 0.03)
    bx(p, (52.0, 54.2), (6.2, 7.0), (48.5, 48.8), METAL, 0.03)
    bx(p, (55.4, 55.7), (3.5, 6.8), (48.5, 48.8), DWOOD, 0.03)
    bx(p, (55.0, 56.2), (5.0, 5.4), (48.45, 48.8), LMETAL, 0.03)
    bx(p, (57.6, 58.4), (4.0, 6.8), (48.5, 48.7), LMETAL, 0.03)
    for (x, z) in ((47.5, 50.8), (49.0, 50.4)):
        rock(p, (x, 0.5, z), 0.8, DBASALT, scale=(1, 0.7, 1), jit=0.1)
    rock(p, (49.6, 0.35, 49.3), 0.4, LAVA, jit=0.06)


# ---- 11. Explorer Camp (round 2) ---------------------------------------------------------------------------------------------
def build_Campsite(p):
    tent(p, 65.1, 26.7, 32.6, 3.3, 4.29, TENTR)
    tent(p, 65.8, 32.8, 37.5, 3.0, 3.9, THATCH)
    vcyl(p, 72.5, 0, 0.5, 32.5, 1.7, BAS1, verts=9, top_r=1.5, jit=0.06)
    vcyl(p, 72.5, 0.4, 0.55, 32.5, 1.2, DBASALT, verts=9, jit=0.04)
    for k in range(8):
        a = math.radians(k * 45)
        rock(p, (72.5 + 1.65 * math.cos(a), 0.45, 32.5 + 1.65 * math.sin(a)), 0.5, BAS2 if k % 2 else BAS1, scale=(1, 0.8, 1), jit=0.08)
    bar(p, (71.7, 0.8, 32.0), (73.3, 1.3, 33.0), 0.42, DWOOD, 0.05)
    bar(p, (71.7, 0.8, 33.0), (73.3, 1.3, 32.0), 0.42, WOOD, 0.05)
    flame(p, 72.5, 0.9, 32.5, 1.3, 2.7)
    for (x, z, ax) in ((72.5, 36.3, 'x'), (76.0, 30.4, 'z')):
        if ax == 'x':
            dk.cyl(p, (x, 0.55, z), 0.55, 3.6, WOOD, axis='x', verts=8, jitter=0.05)
            dk.cyl(p, (x + 1.8, 0.55, z), 0.4, 0.1, BONE, axis='x', verts=8, jitter=0.03)
        else:
            dk.cyl(p, (x, 0.55, z), 0.55, 3.6, WOOD, axis='z', verts=8, jitter=0.05)
            dk.cyl(p, (x, 0.55, z + 1.8), 0.4, 0.1, BONE, axis='z', verts=8, jitter=0.03)
    bx(p, (68.3, 69.7), (0, 1.4), (26.3, 27.7), WOOD, 0.05)                           # crate with lantern
    bx(p, (68.3, 69.7), (0.6, 0.75), (27.68, 27.78), DWOOD, 0.03)
    bx(p, (68.6, 69.4), (1.4, 2.0), (26.6, 27.4), TENTR, 0.04)
    rock(p, (69.0, 2.35, 27.0), 0.35, FLAME, scale=(1, 1.2, 1), jit=0.04)
    for k in range(2):                                                                  # two roasting sticks leaning over the fire
        bar(p, (70.4 + k * 0.5, 0.0, 30.6 - k * 0.5), (72.0 + k * 0.4, 2.6, 32.0 - k * 0.2), 0.14, DWOOD, 0.03)
        rock(p, (72.0 + k * 0.4, 2.7, 32.0 - k * 0.2), 0.28, BONE, subdiv=1, jit=0.03)
    dk.cyl(p, (75.6, 0.5, 36.6), 0.5, 1.4, TENTR, axis='x', verts=8, jitter=0.04)       # bedroll
    bx(p, (74.8, 75.6), (0.0, 0.3), (36.0, 37.2), shade(TENTR, 0.7), 0.04)
    rock(p, (76.2, 0.8, 27.5), 0.7, WOOD, scale=(1, 1.2, 0.8), jit=0.06)                 # backpack
    rock(p, (76.2, 1.4, 27.2), 0.3, FLAME, scale=(1, 0.6, 1), jit=0.04)


# ---- 12. Tiki Torches (round 2) ------------------------------------------------------------------------------------------------
def build_Torches(p):
    for (x, z, hh, big) in ((10, -33, 4.4, 0), (14, -28, 5.2, 1), (19, -32, 3.8, 0), (22, -27, 4.8, 1), (12.5, -37.5, 3.4, 0)):
        bamboo(p, x, z, hh, 0.36, 1.45)
        vcyl(p, x, hh - 0.05, hh + 0.85, z, 0.55, METAL, verts=8, top_r=0.95, jit=0.04)
        vcyl(p, x, hh + 0.75, hh + 0.88, z, 0.8, LAVA, verts=8, jit=0.03)
        flame(p, x, hh + 0.8, z, 0.95, 2.0 if big else 1.6)
        bx(p, (x - 0.5, x + 0.5), (hh - 0.5, hh - 0.25), (z - 0.5, z + 0.5), DWOOD, 0.03)
        for (dx, dz) in ((0.9, 0.4), (-0.7, 0.8), (0.1, -0.9)):
            rock(p, (x + dx, 0.25, z + dz), 0.35, BAS1, scale=(1, 0.6, 1), jit=0.1)
    for (x, z) in ((11.5, -31.5), (16.5, -30.0), (20.5, -29.5), (14.5, -35.5)):
        bx(p, (x, x + 0.45), (0.0, 0.12), (z, z + 0.45), FLAME, 0.05)


# ---- 13. Fossil Garden (round 2) ---------------------------------------------------------------------------------------------
def build_Fossil(p):
    zc = -24.0
    bx(p, (-39.0, -21.0), (6.5, 7.1), (zc - 0.4, zc + 0.4), BONE, 0.04)                 # spine beam
    for i in range(10):                                                                  # vertebra bumps
        x = -38.2 + i * 1.75
        bx(p, (x, x + 1.0), (7.1, 7.6), (zc - 0.3, zc + 0.3), shade(BONE, 0.9 if i % 2 else 1.0), 0.04)
    for (x, r0) in ((-35.2, 2.3), (-32.4, 2.35), (-29.6, 2.2), (-26.8, 1.9), (-24.0, 1.4)):
        for s in (-1, 1):
            prev = (x, 6.7, zc + s * 0.3)
            for k in range(1, 6):
                t = k / 5.0
                ang = t * math.pi * 0.55
                zz = zc + s * (0.3 + (r0 - 0.3) * math.sin(ang) / math.sin(math.pi * 0.55))
                yy = 6.7 * (1 - (1 - math.cos(ang)) / (1 - math.cos(math.pi * 0.55))) + 0.2
                cur = (x + 0.12 * k, yy, zz)
                bone(p, prev, cur, 0.8 - 0.1 * t, BONE if k % 2 else shade(BONE, 0.92))
                prev = cur
    prev = (-21.0, 6.8, zc)                                                              # tail curling down
    for (x, y, t) in ((-19.8, 5.7, 0.7), (-18.8, 4.2, 0.6), (-18.0, 2.6, 0.5), (-17.7, 1.0, 0.4)):
        bone(p, prev, (x, y, zc), t, BONE)
        prev = (x, y, zc)
    bar(p, (-39.6, 4.4, zc), (-37.6, 6.8, zc), 1.0, BONE, 0.04)                          # neck
    ball(p, (-41.2, 3.4, zc), 2.1, BONE, scale=(1.1, 0.95, 1.0), subdiv=1, jit=0.04)     # skull
    bx(p, (-44.5, -41.8), (1.9, 3.9), (zc - 1.0, zc + 1.0), BONE, 0.04)
    bx(p, (-44.2, -41.5), (0.5, 1.8), (zc - 0.9, zc + 0.9), shade(BONE, 0.88), 0.04)
    bx(p, (-44.5, -41.0), (3.9, 4.3), (zc - 1.4, zc + 1.4), shade(BONE, 0.95), 0.04)      # brow ridge
    for k in range(5):
        x = -44.2 + k * 0.62
        for s in (-1, 1):
            bx(p, (x, x + 0.28), (1.5, 2.1), (zc + s * 0.78 - 0.14, zc + s * 0.78 + 0.14), WHITE, 0.02)
    for s in (-1, 1):
        bx(p, (-42.9, -41.9), (3.0, 3.9), (zc + s * 1.0 - 0.25, zc + s * 1.0 + 0.25), OBS, 0.02)
        rock(p, (-42.5, 3.4, zc + s * 1.1), 0.28, FLAME, subdiv=1, jit=0.04)
        bar(p, (-41.0, 4.3, zc + s * 1.0), (-39.9, 7.0, zc + s * 1.8), 0.8, shade(BONE, 0.85), 0.04)
        bar(p, (-39.9, 7.0, zc + s * 1.8), (-38.8, 7.6, zc + s * 2.1), 0.45, shade(BONE, 0.8), 0.04)
    for (x, s) in ((-41.5, 1), (-31.0, -1), (-27.0, 1), (-22.5, -1)):
        rock(p, (x, 0.2, zc + s * 1.9), 1.6, BAS1, scale=(1.5, 0.16, 0.55), jit=0.05)
    rock(p, (-43.4, 0.4, zc + 1.7), 1.3, BAS1, scale=(1.3, 0.25, 0.6), jit=0.05)
    for (x, z0, z1) in ((-33.5, -25.9, -25.0), (-28.0, -22.3, -21.9), (-24.5, -25.9, -25.2), (-37.5, -22.4, -22.0)):     # ember cracks in the ash
        seg(p, x, z0, x + 1.2, (z0 + z1) / 2 + 0.3, 0.45, 0.0, 0.14, EMBER, 0.03)
        seg(p, x + 1.2, (z0 + z1) / 2 + 0.3, x + 0.4, z1, 0.45, 0.0, 0.14, LAVA, 0.03)
    for (x, z) in ((-32.2, zc + 0.6), (-29.0, zc - 0.7), (-36.4, zc + 0.6), (-19.5, zc + 0.5)):
        rock(p, (x, 0.3, z), 0.45, BONE, scale=(1, 0.7, 1), jit=0.08)


# ---- 16. Seismo Station (round 2) ----------------------------------------------------------------------------------------------
def build_Station(p):
    bx(p, (37.0, 47.0), (0, 5.0), (14.5, 21.5), BONE, 0.03)
    bx(p, (36.8, 47.2), (0, 0.5), (14.3, 21.7), BAS2, 0.03)
    dk.prism(p, (42.0, 5.0, 18.0), 11.2, 8.2, 2.4, TENTR, ridge='x', jitter=0.04)
    bx(p, (36.4, 47.6), (4.9, 5.2), (13.9, 22.1), DBASALT, 0.03)
    bx(p, (40.8, 43.2), (0.5, 4.2), (21.5, 21.75), DWOOD, 0.03)
    bx(p, (41.0, 41.2), (1.0, 3.6), (21.75, 21.85), WOOD, 0.03)
    bx(p, (43.5, 46.0), (1.6, 3.4), (21.5, 21.7), METAL, 0.03)
    bx(p, (43.7, 45.8), (1.8, 3.2), (21.7, 21.8), TEAL, 0.03)
    bx(p, (44.6, 44.9), (1.8, 3.2), (21.8, 21.88), METAL, 0.02)
    pts = [(37.6, 3.0), (38.3, 3.6), (39.0, 2.2), (39.7, 4.0), (40.4, 2.4), (41.1, 3.4)]
    for (a, b) in zip(pts[:-1], pts[1:]):
        diag(p, a[0], a[1], 21.6, b[0], b[1], 0.22, 0.15, RUBY, 0.03)
    bx(p, (43.4, 46.4), (6.8, 7.0), (16.2, 18.2), TEAL, 0.03)
    bx(p, (43.4, 46.4), (6.7, 6.8), (16.2, 18.2), LMETAL, 0.03)
    vcyl(p, 38.5, 0, 12.8, 16.5, 0.4, LMETAL, verts=6, jit=0.03)
    for y in (4.0, 7.5, 11.0):
        bx(p, (37.6, 39.4), (y, y + 0.22), (16.35, 16.65), METAL, 0.03)
    bar(p, (38.5, 10.0, 16.5), (36.9, 5.2, 14.6), 0.14, METAL, 0.03)
    bar(p, (38.5, 10.0, 16.5), (40.1, 5.2, 14.6), 0.14, METAL, 0.03)
    # satellite dish: bowl tilted up and toward the road, on an arm
    dk.cyl(p, (38.5, 10.9, 17.9), 0.3, 1.0, WHITE, axis="z", verts=12, top_radius=1.7, jitter=0.03, rot=(-38, 0, 0))    # concave dish: narrow at the back
    dk.cyl(p, (38.5, 11.35, 18.45), 1.75, 0.18, LMETAL, axis="z", verts=12, jitter=0.03, rot=(-38, 0, 0))             # rim
    dk.cyl(p, (38.5, 11.45, 18.55), 0.6, 0.16, DMETAL, axis="z", verts=8, jitter=0.03, rot=(-38, 0, 0))
    bar(p, (38.5, 10.0, 16.5), (38.5, 10.9, 17.6), 0.3, METAL, 0.03)
    bar(p, (38.5, 11.3, 18.2), (38.5, 12.4, 19.0), 0.14, METAL, 0.03)
    # yagi antenna on the roof ridge and warning stripes round the foot of the hut
    vcyl(p, 44.0, 7.3, 9.6, 18.0, 0.14, LMETAL, verts=5, jit=0.03)
    bx(p, (43.9, 44.1), (9.3, 9.5), (16.4, 19.6), LMETAL, 0.03)
    for k, (zz, ww) in enumerate(((16.6, 1.7), (17.4, 1.3), (18.2, 1.5), (19.0, 1.1))):
        bx(p, (44.0 - ww / 2, 44.0 + ww / 2), (9.35, 9.45), (zz - 0.06, zz + 0.06), METAL, 0.03)
    for k in range(5):
        x = 37.4 + k * 2.0
        bx(p, (x, x + 1.0), (0.5, 1.0), (21.5, 21.62), FLAME if k % 2 == 0 else DBASALT, 0.03)
    rock(p, (38.5, 13.2, 16.5), 0.55, RUBY, jit=0.04)
    bx(p, (46.6, 48.2), (0, 1.6), (15.2, 16.8), METAL, 0.04)
    bx(p, (46.8, 48.0), (1.6, 1.9), (15.4, 16.6), LMETAL, 0.04)
    bx(p, (47.0, 47.8), (1.9, 2.5), (15.7, 16.3), TEAL, 0.04)
    bx(p, (36.6, 38.0), (0, 0.9), (19.6, 21.0), WOOD, 0.04)
    vcyl(p, 47.4, 2.5, 3.3, 16.0, 0.12, LMETAL, verts=5, jit=0.03)                      # weather vane on the instrument box
    bx(p, (47.0, 47.8), (3.2, 3.5), (15.9, 16.1), RUBY, 0.03)


# ---- 18. Palm Grove (round 2) --------------------------------------------------------------------------------------------------
def build_Palms(p):
    vcyl(p, 17.6, 0, 0.12, 39.5, 7.0, SAND, verts=14, jit=0.04)
    vcyl(p, 17.6, 0.1, 0.2, 39.5, 5.0, shade(SAND, 0.88), verts=12, jit=0.04)
    for (bx0, bz0, tx, tz, hh, L, yaw0) in ((14.5, 38.5, 14.1, 38.5, 8.1, 3.4, 20), (21.0, 41.0, 21.4, 41.0, 7.1, 3.0, 10),
                                            (18.5, 35.0, 18.5, 35.0, 6.1, 2.8, 45), (18.0, 44.5, 18.0, 44.5, 4.9, 2.3, 0)):
        n = 5
        prev = (bx0, 0.0, bz0)
        for k in range(1, n + 1):
            t = k / n
            cur = (bx0 + (tx - bx0) * t + 0.25 * math.sin(t * 3.1), hh * t, bz0 + (tz - bz0) * t)
            bar(p, prev, cur, 1.2 - 0.45 * t, WOOD if k % 2 else shade(WOOD, 0.88), 0.05)
            prev = cur
        cr = prev
        ball(p, (cr[0], cr[1] - 0.15, cr[2]), 0.62, DWOOD, subdiv=1, jit=0.05)
        for k in range(8):
            yaw = yaw0 + k * 45 + (8 if k % 2 else -8)
            leaf(p, (cr[0], cr[1] + 0.05, cr[2]), yaw, L * (1.0 if k % 2 else 0.85), L * 0.42, 0.45, 1.5, GRASS if k % 2 else DGRASS, 0.06)
        for (dx, dz) in ((0.4, 0.3), (-0.35, 0.4), (0.0, -0.45)):
            ball(p, (cr[0] + dx, cr[1] - 0.45, cr[2] + dz), 0.32, DWOOD, subdiv=1, jit=0.05)


# ---- 17. Lookout Tower (ladder fix) ------------------------------------------------------------------------------------------
def build_Watchtower(p):
    cx, cz = -58.0, -22.0
    base = [(-62.4, -26.4), (-53.6, -26.4), (-62.4, -17.6), (-53.6, -17.6)]
    topl = [(-60.6, -24.6), (-55.4, -24.6), (-60.6, -19.4), (-55.4, -19.4)]
    for (a, b) in zip(base, topl):
        bar(p, (a[0], 0.0, a[1]), (b[0], 14.2, b[1]), 1.0, DWOOD, 0.04)
        bx(p, (a[0] - 0.6, a[0] + 0.6), (0, 0.5), (a[1] - 0.6, a[1] + 0.6), BAS1, 0.04)

    def at(i, y):
        t = y / 14.2
        return (base[i][0] + (topl[i][0] - base[i][0]) * t, y, base[i][1] + (topl[i][1] - base[i][1]) * t)
    for (i, j) in ((0, 1), (2, 3), (0, 2), (1, 3)):
        for (y0, y1) in ((0.6, 5.0), (5.0, 9.5), (9.5, 14.0)):
            bar(p, at(i, y0), at(j, y1), 0.38, WOOD, 0.04)
            bar(p, at(j, y0), at(i, y1), 0.38, WOOD, 0.04)
        for y in (5.0, 9.5):
            bar(p, at(i, y), at(j, y), 0.45, DWOOD, 0.04)
    bx(p, (-63.0, -53.0), (14.0, 14.8), (-27.0, -17.0), WOOD, 0.05)
    for i in range(5):
        bx(p, (-63.0 + i * 2.0 + 0.9, -63.0 + i * 2.0 + 1.1), (14.8, 14.85), (-27.0, -17.0), DWOOD, 0.03)
    for (x, z) in ((-62.6, -26.6), (-53.4, -26.6), (-62.6, -17.4), (-53.4, -17.4), (-58, -17.4), (-62.6, -22), (-53.4, -22)):
        bx(p, (x - 0.2, x + 0.2), (14.8, 16.2), (z - 0.2, z + 0.2), DWOOD, 0.04)
    bx(p, (-62.8, -53.2), (15.8, 16.1), (-26.8, -26.4), WOOD, 0.04)
    bx(p, (-62.8, -59.2), (15.8, 16.1), (-17.6, -17.2), WOOD, 0.04)
    bx(p, (-56.8, -53.2), (15.8, 16.1), (-17.6, -17.2), WOOD, 0.04)
    bx(p, (-62.8, -62.4), (15.8, 16.1), (-26.8, -17.2), WOOD, 0.04)
    bx(p, (-53.6, -53.2), (15.8, 16.1), (-26.8, -17.2), WOOD, 0.04)
    bx(p, (-61.5, -54.5), (14.8, 19.0), (-25.5, -18.5), DWOOD, 0.05)
    for i in range(4):
        bx(p, (-61.6, -54.4), (15.5 + i * 1.0, 15.65 + i * 1.0), (-18.5, -18.35), WOOD, 0.04)
    bx(p, (-59.8, -56.2), (16.4, 18.0), (-18.5, -18.3), OBS, 0.02)
    bx(p, (-60.0, -59.7), (16.3, 18.1), (-18.5, -18.15), WOOD, 0.03)
    bx(p, (-56.3, -56.0), (16.3, 18.1), (-18.5, -18.15), WOOD, 0.03)
    bx(p, (-60.0, -56.0), (16.2, 16.5), (-18.5, -18.1), WOOD, 0.03)
    taper(p, cx, cz, 10.0, 10.0, 1.2, 1.2, 18.8, 21.0, TENTR, jit=0.04)
    taper(p, cx, cz, 10.0, 10.0, 9.6, 9.6, 18.6, 18.9, shade(TENTR, 0.7), jit=0.04)
    bar(p, (cx, 20.9, cz), (cx, 21.2, cz), 0.25, DWOOD, 0.03)
    for x in (-58.9, -57.1):                                                            # ladder up the front, inside the footprint
        bar(p, (x, 0.0, -17.1), (x, 14.6, -17.6), 0.32, WOOD, 0.04)
    for i in range(12):
        y = 0.6 + i * 1.18
        z = -17.1 - 0.5 * y / 14.6
        bx(p, (-58.9, -57.1), (y, y + 0.18), (z - 0.22, z + 0.22), WOOD, 0.04)
    vcyl(p, -54.2, 14.8, 15.5, -25.8, 0.6, METAL, verts=6, top_r=0.8, jit=0.04)
    flame(p, -54.2, 15.4, -25.8, 0.6, 1.1)
    bx(p, (-62.0, -61.0), (14.8, 15.0), (-20.9, -19.9), METAL, 0.03)
    dk.cyl(p, (-61.5, 15.6, -20.4), 0.22, 1.4, LMETAL, axis='x', verts=6, jitter=0.03, rot=(0, 0, 35))


# ---- 19. Dragon Nest (round 2) -------------------------------------------------------------------------------------------------
def build_Eggs(p):
    import random
    rnd = random.Random(5)
    cx, cz = -14.0, -12.0
    vcyl(p, cx, 0, 0.35, cz, 5.6, EMBER, verts=14, jit=0.04)
    vcyl(p, cx, 0.3, 0.55, cz, 3.8, LAVA, verts=12, jit=0.04)
    for i in range(18):
        a = math.radians(i * 360 / 18 + rnd.uniform(-6, 6))
        r0, r1 = 4.2 + rnd.uniform(-0.2, 0.3), 5.0 + rnd.uniform(-0.2, 0.3)
        a2 = a + math.radians(rnd.uniform(24, 40))
        bar(p, (cx + r0 * math.cos(a), 0.7 + rnd.uniform(0, 0.8), cz + r0 * math.sin(a)), (cx + r1 * math.cos(a2), 0.9 + rnd.uniform(0, 0.9), cz + r1 * math.sin(a2)), 0.36, DWOOD if i % 2 else WOOD, 0.05)
    for i in range(14):
        a = math.radians(i * 360 / 14 + 5)
        bar(p, (cx + 3.4 * math.cos(a), 0.9, cz + 3.4 * math.sin(a)), (cx + 4.7 * math.cos(a + 0.6), 1.3, cz + 4.7 * math.sin(a + 0.6)), 0.4, BAS1, 0.05)
    eggs = [(-16.3, -12.4, 2.0, 2.15, EMBER, FLAME), (-11.5, -11.8, 1.9, 2.0, FLAME, EMBER), (-14.0, -9.7, 1.75, 1.85, RUBY, FLAME), (-14.0, -14.6, 1.65, 1.75, LAVA, RUBY)]
    for (x, z, rx, ry_, col, spot) in eggs:
        ball(p, (x, 0.5 + ry_ * 0.95, z), 1.0, col, scale=(rx * 0.78, ry_, rx * 0.78), subdiv=2, jit=0.03)
        for k in range(3):
            a = math.radians(k * 120 + x * 20)
            h = 0.5 + ry_ * (0.95 + 0.55 * math.sin(k * 1.7))
            rr = rx * 0.78 * math.sqrt(max(0.0, 1 - ((h - 0.5 - ry_ * 0.95) / ry_) ** 2)) + 0.03
            ball(p, (x + rr * math.cos(a), h, z + rr * math.sin(a)), 0.22, spot, subdiv=1, jit=0.03)
    for (a, b) in zip([(-16.4, 3.4), (-15.9, 3.0), (-15.4, 3.5), (-14.9, 3.1)], [(-15.9, 3.0), (-15.4, 3.5), (-14.9, 3.1), (-14.5, 3.5)]):
        bar(p, (a[0], a[1], -11.5), (b[0], b[1], -11.5), 0.18, OBS, 0.02)
    for (x, z, sx, sz) in ((-19.6, -12, 1.8, 2.4), (-8.6, -10.6, 1.8, 2.2), (-13, -17.2, 2.2, 1.6), (-9.5, -15.2, 1.5, 1.4), (-18.5, -8.4, 1.4, 1.3)):
        rock(p, (x, 0.6, z), 1.0, BAS1, scale=(sx * 0.6, 0.85, sz * 0.6), subdiv=1, jit=0.08)
    for (x, y, z) in ((-17.5, 3.6, -9.5), (-10.5, 4.0, -13.0), (-12.5, 4.4, -16.0)):       # floating embers
        ball(p, (x, y, z), 0.28, FLAME, subdiv=1, jit=0.04)


# ---- 21. Dragon Statue (round 2) -----------------------------------------------------------------------------------------------
def build_Dragon(p):
    cx = -35.0
    bx(p, (-39.0, -31.0), (0, 2.4), (-15.0, -1.0), BAS1, 0.04)
    bx(p, (-39.4, -30.6), (0, 0.6), (-15.4, -0.6), BASALT, 0.04)
    bx(p, (-39.1, -30.9), (1.5, 1.8), (-15.1, -0.9), LAVA, 0.03)
    ball(p, (cx, 5.3, -8.0), 1.0, BASALT, scale=(2.6, 2.3, 4.9), subdiv=2, jit=0.05)
    for k in range(5):                                                                    # belly plates
        z = -4.5 - k * 1.5
        bx(p, (cx - 1.0, cx + 1.0), (3.2, 3.5), (z - 0.5, z + 0.5), BAS2, 0.04)
    for k in range(6):
        z = -4.5 - k * 1.55
        cone(p, cx, 7.4 - k * 0.12, z, 0.6, 1.4 - 0.1 * k, LAVA if k % 2 else EMBER, verts=5, jit=0.04)
    for s in (-1, 1):
        bx(p, (cx + s * 2.0 - 0.9, cx + s * 2.0 + 0.9), (2.4, 5.0), (-5.6, -3.6), BAS1, 0.05)
        bx(p, (cx + s * 2.0 - 1.0, cx + s * 2.0 + 1.0), (2.4, 2.9), (-4.4, -2.2), BAS2, 0.05)
        bx(p, (cx + s * 1.9 - 0.9, cx + s * 1.9 + 0.9), (2.4, 4.3), (-11.5, -9.6), BAS1, 0.05)
        for k in range(3):
            bx(p, (cx + s * 2.0 - 0.8 + k * 0.55, cx + s * 2.0 - 0.45 + k * 0.55), (2.4, 2.85), (-2.6, -2.0), BONE, 0.03)
        bx(p, (cx + s * 2.62, cx + s * 2.7), (3.0, 4.6), (-5.2, -4.0), LAVA, 0.03)       # glowing veins on the legs
    for (y0, y1) in ((4.4, 5.6), (3.6, 4.4)):
        bx(p, (cx - 0.25, cx + 0.25), (y0, y1), (-3.15, -2.95), LAVA, 0.03)
    for k in range(4):                                                                    # flank veins
        for s in (-1, 1):
            bx(p, (cx + s * 2.55, cx + s * 2.7), (4.0 + (k % 2) * 0.8, 5.6 + (k % 2) * 0.5), (-5.5 - k * 1.2, -5.0 - k * 1.2), LAVA, 0.03)
    prev = (cx, 6.2, -4.4)
    for k, (y, z) in enumerate(((7.6, -3.7), (9.0, -3.0), (10.2, -2.3))):
        bar(p, prev, (cx, y, z), 2.7 - 0.3 * k, BAS1 if k % 2 else BASALT, 0.05)
        prev = (cx, y, z)
    bx(p, (cx - 1.7, cx + 1.7), (10.5, 12.5), (-3.6, -0.9), BASALT, 0.05)
    bx(p, (cx - 1.1, cx + 1.1), (10.7, 11.9), (-0.9, 1.1), BAS1, 0.05)
    bx(p, (cx - 1.0, cx + 1.0), (10.3, 10.7), (-0.8, 0.9), BAS2, 0.04)
    bx(p, (cx - 0.7, cx + 0.7), (10.7, 11.1), (-0.8, 0.9), LAVA, 0.03)                    # glowing mouth
    for k in range(3):
        for s in (-1, 1):
            bx(p, (cx + s * 0.85 - 0.12, cx + s * 0.85 + 0.12), (10.0, 10.3), (-0.5 + k * 0.45, -0.3 + k * 0.45), WHITE, 0.02)
    for s in (-1, 1):
        bx(p, (cx + s * 0.9 - 0.3, cx + s * 0.9 + 0.3), (11.7, 12.3), (-0.1, 0.35), FLAME, 0.02)
        bar(p, (cx + s * 1.1, 12.3, -3.2), (cx + s * 2.2, 12.7, -4.6), 0.55, BONE, 0.04)
        bx(p, (cx + s * 0.45 - 0.18, cx + s * 0.45 + 0.18), (11.6, 11.9), (1.0, 1.1), OBS, 0.02)
    for s in (-1, 1):
        sh = (cx + s * 1.8, 8.0, -6.5)
        el = (cx + s * 5.0, 11.4, -7.0)
        tip = (cx + s * 8.7, 12.4, -9.0)
        bar(p, sh, el, 0.6, BAS2, 0.04)
        bar(p, el, tip, 0.45, BAS2, 0.04)
        f1 = (cx + s * 8.2, 5.0, -10.5)
        f2 = (cx + s * 5.3, 4.6, -12.0)
        f3 = (cx + s * 2.2, 5.0, -11.0)
        bar(p, el, f1, 0.3, BAS2, 0.04)
        bar(p, el, f2, 0.3, BAS2, 0.04)
        panel(p, [sh, el, f2, f3], 0.2, EMBER, 0.05)
        panel(p, [el, tip, f1, f2], 0.2, LAVA, 0.05)
    prev = (cx, 4.2, -12.2)
    for k, (y, z, t) in enumerate(((3.9, -14.5, 1.8), (3.5, -16.8, 1.4), (3.2, -19.0, 1.1), (3.0, -21.3, 0.8))):
        bar(p, prev, (cx + (0.9 if k % 2 else -0.9) * 0.5, y, z), t, BAS1 if k % 2 else BASALT, 0.05)
        prev = (cx + (0.9 if k % 2 else -0.9) * 0.5, y, z)
        cone(p, cx, y + t / 2, z + 0.4, 0.4, 0.9, LAVA, verts=5, jit=0.04)
    cone(p, cx, 2.8, -21.3, 0.55, 1.1, FLAME, verts=5, jit=0.04)


# ---- 23. Magma Heart (rocks) ---------------------------------------------------------------------------------------------------
def build_Heart(p):
    cx, cz = 56.0, 4.0
    vcyl(p, cx, 0, 1.2, cz, 6.5, DBASALT, verts=12, top_r=6.1, jit=0.05)
    vcyl(p, cx, 1.1, 1.45, cz, 5.4, BAS1, verts=12, jit=0.04)
    vcyl(p, cx, 1.4, 1.65, cz, 4.4, EMBER, verts=12, jit=0.03)
    vcyl(p, cx, 1.6, 1.75, cz, 3.0, LAVA, verts=12, jit=0.03)
    for k in range(12):
        a = math.radians(k * 30)
        bx(p, (cx + 5.7 * math.cos(a) - 0.25, cx + 5.7 * math.cos(a) + 0.25), (1.0, 1.4), (cz + 5.7 * math.sin(a) - 0.25, cz + 5.7 * math.sin(a) + 0.25), FLAME if k % 2 else LAVA, 0.03)
    crystal(p, cx, cz, 10.2, 2.7, LAVA, (0, 0), 45, y0=1.5, jit=0.12)
    for (dx, dz, h, r, col, tl, tw) in ((-3.4, 1.0, 6.4, 1.15, RUBY, (6, 14), 20), (3.4, -1.0, 5.6, 1.1, EMBER, (-6, -14), 40), (1.0, 3.6, 5.0, 1.05, RUBY, (14, 4), 10), (-1.0, -3.6, 4.4, 1.0, EMBER, (-14, 6), 35),
                                        (-3.0, -2.6, 3.4, 0.8, FLAME, (-10, 10), 25), (3.0, 3.0, 3.0, 0.75, FLAME, (10, -10), 5)):
        crystal(p, cx + dx, cz + dz, h, r, col, tl, tw, y0=1.5, jit=0.1)
    for (x, y, z, r) in ((53, 10.5, 6, 0.65), (59.2, 12.2, 3, 0.7), (56.5, 13.4, 7, 0.5), (60.0, 8.4, 6.4, 0.45), (52.4, 7.6, 2.2, 0.4)):
        ball(p, (x, y, z), r, FLAME if r > 0.5 else LAVA, subdiv=1, jit=0.06)
    for (x, z, sx, sy, sz) in ((50.4, 1, 1.2, 1.1, 1.3), (61.4, 7, 1.2, 1.1, 1.3)):
        rock(p, (x, sy * 0.6, z), 1.0, BAS1, scale=(sx, sy, sz), subdiv=1, jit=0.08)


# ---- 25. Great Eruption (round 2) ---------------------------------------------------------------------------------------------
def build_Eruption(p):
    cx, cz = 58.5, -38.5
    vcyl(p, cx, 37.4, 38.6, cz, 5.4, EMBER, verts=12, top_r=4.2, jit=0.04)
    vcyl(p, cx, 38.5, 41.0, cz, 3.4, LAVA, verts=10, top_r=2.8, jit=0.04)
    vcyl(p, cx, 40.8, 43.4, cz, 2.8, FLAME, verts=10, top_r=2.4, jit=0.04)
    vcyl(p, cx, 43.2, 46.4, cz, 2.4, LAVA, verts=10, top_r=4.0, jit=0.04)
    for k in range(6):
        a = math.radians(k * 60 + 20)
        cone(p, cx + 2.4 * math.cos(a), 38.4 + (k % 2) * 0.8, cz + 2.4 * math.sin(a), 0.95, 5.0 + (k % 3), FLAME if k % 2 else LAVA, verts=5, jit=0.05)
    puffs = [(58.5, 47.0, -38.5, 4.6, 3.0, EMBER), (53.0, 49.8, -37.0, 3.6, 2.8, RUBY), (64.2, 49.5, -39.5, 4.0, 3.0, EMBER), (58.5, 52.4, -38.0, 4.8, 3.2, DBASALT),
             (51.0, 52.6, -40.0, 3.2, 2.4, BASALT), (66.6, 53.0, -37.0, 3.2, 2.4, BAS1), (58.5, 53.8, -43.0, 3.4, 2.2, DBASALT), (62.5, 54.0, -33.8, 3.0, 1.6, BAS1),
             (55.0, 54.0, -33.4, 2.6, 1.4, BASALT), (49.2, 47.8, -37.6, 2.2, 1.8, EMBER), (68.4, 47.6, -35.6, 2.0, 1.6, RUBY)]
    for (x, y, z, rx, ry_, col) in puffs:
        ball(p, (x, y, z), 1.0, col, scale=(rx, ry_, rx * 0.9), subdiv=2, jit=0.05)
    bolt = [(66.0, 51.0, -31.9), (65.0, 48.8, -31.9), (66.2, 47.4, -31.9), (64.8, 45.2, -31.9)]
    for (a, b) in zip(bolt[:-1], bolt[1:]):
        bar(p, a, b, 0.4, FLAME, 0.03)
    for (x, y, z, r, col, tx, ty, tz) in ((48.0, 44.0, -41.0, 1.1, LAVA, 50.6, 41.8, -40.2), (69.2, 46.0, -35.0, 1.2, EMBER, 67.2, 43.4, -36.0),
                                           (66.0, 40.0, -45.0, 0.9, FLAME, 64.4, 38.6, -43.6), (48.6, 49.6, -43.5, 0.7, FLAME, 50.0, 48.4, -42.4)):
        ball(p, (x, y, z), r, col, subdiv=1, jit=0.05)
        bar(p, (x, y, z), (tx, ty, tz), r * 0.9, EMBER, 0.04)
        ball(p, (tx, ty, tz), r * 0.5, FLAME, subdiv=1, jit=0.05)
    for (x, y, z) in ((52.0, 38.4, -44.0), (63.6, 42.8, -32.4), (47.5, 40.4, -33.4), (69.7, 41.0, -41.0)):
        ball(p, (x, y, z), 0.35, FLAME, subdiv=1, jit=0.04)


# ==== END PARTS =============================================================================================================

ORDER = [pp["Id"] for pp in BP["Parts"]]
PARTS = [(pid, globals()["build_" + pid]) for pid in ORDER if ("build_" + pid) in globals()]
AZ = {}
ELEV = {}
MULT = {"AshGround": 1.5, "Volcano": 2.2, "Eruption": 2.4}
GROUND_Y = {"Eruption": 37.4}
SHIBA_AT = {"AshGround": (-40, 6, 270, 0), "Volcano": (36, -20, 270, 0), "Eruption": (46, -28, 270, 37.4)}


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


def snap(objs, extra, filename, az, el, mult, size, top=False, gy=0.0):
    low, high = dk._bounds(list(objs) + list(extra))
    g = dk.ground(low, high)
    g.location.z += gy
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
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000), gy=GROUND_Y.get(pid, 0.0))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 40, 3.2, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_Volcano.png"))


main()
