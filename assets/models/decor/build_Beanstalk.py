"""Final low-poly decor models for the theme Beanstalk (30 parts around the 27th Shiba, Giant Shiba, 16 studs tall).

Usage: blender --background --factory-startup --python build_Beanstalk.py -- <outdir> [PartId,PartId,...]
Writes Decor_Beanstalk_<PartId>.fbx, preview_<PartId>.png and stage_Beanstalk.png into <outdir>.
Every model is written in STAGE coordinates (the numbers of DecorTheme27.luau) and fitted to the union box of its blueprint
pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it). Give part ids (comma
separated) after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "Beanstalk"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "Beanstalk"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_Beanstalk.json"))

# ---- palette (one for all 30 parts: meadow greens, grey stone, warm wood, bean greens, gold) --------------------------------
GRASS = (112, 176, 84)
GRASS2 = (86, 148, 70)
LGRASS = (150, 204, 100)
DIRT = (146, 110, 74)
DDIRT = (110, 80, 56)
STONE = (150, 152, 158)
DSTONE = (110, 112, 120)
LSTONE = (188, 190, 192)
MOSS = (100, 138, 78)
LMOSS = (132, 172, 92)
WOOD = (156, 108, 66)
DWOOD = (108, 72, 46)
LWOOD = (196, 150, 96)
THATCH = (222, 184, 92)
DTHATCH = (190, 150, 70)
CREAM = (244, 232, 204)
RED = (206, 72, 60)
DRED = (160, 50, 46)
ROOFRED = (184, 92, 70)
BEAN = (96, 180, 70)
DBEAN = (56, 132, 62)
PBEAN = (150, 96, 170)
LBEAN = (158, 214, 104)
GOLD = (244, 198, 58)
DGOLD = (200, 148, 40)
LGOLD = (255, 228, 130)
WHITE = (248, 248, 244)
BLACK = (46, 44, 52)
IRON = (84, 88, 98)
LIRON = (118, 122, 134)
WATER = (110, 176, 228)
HAY = (232, 196, 92)
DHAY = (198, 156, 62)
BROWN = (140, 92, 60)
COWBROWN = (168, 104, 66)
PINK = (240, 170, 170)
TAN = (214, 184, 130)
DTAN = (176, 142, 94)
SKY = (150, 200, 238)
CASTLE = (236, 228, 214)
DCASTLE = (206, 196, 186)
SLATEBLUE = (92, 112, 176)
ORANGE = (240, 150, 50)
FLAME = (252, 214, 80)
SUN = (255, 226, 120)
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
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv + 1, jitter=jit)


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



# ---- helpers of the beanstalk theme -------------------------------------------------------------------------------------------
def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)


def blob(p, x, y, z, sx, sy, sz, col, sub=2, jit=0.06, rot=(0, 0, 0)):
    """Low-poly ellipsoid by centre and full size (sub 1 = 80 triangles, 2 = 320)."""
    return dk.ball(p, (x, y, z), 1.0, col, scale=(sx / 2, sy / 2, sz / 2), subdiv=sub, rot=rot, jitter=jit)


def lbox(p, cx, cz, deg, lx, y, lz, sx, sy, sz, col, jit=0.04):
    """Box placed by an offset (lx, lz) in the local frame of a group turned by deg about its centre (cx, cz)."""
    a, b = ry(lx, lz, deg)
    return dk.box(p, (cx + a, y, cz + b), (sx, sy, sz), col, rot=(0, deg, 0), jitter=jit)


def lathe(p, cx, cz, prof, col, segs=12, jit=0.04, sx=1.0, sz=1.0, a0=0.0):
    """Surface of revolution about the vertical axis through (cx, cz). prof = [(radius, y), ...] from bottom to top;
    radius 0 closes an end (pole), otherwise the end is capped flat."""
    pts, rings, faces = [], [], []
    for (r, y) in prof:
        if r < 1e-6:
            rings.append((True, len(pts)))
            pts.append((cx, y, cz))
        else:
            rings.append((False, len(pts)))
            for k in range(segs):
                a = a0 + 2 * math.pi * k / segs
                pts.append((cx + r * math.cos(a) * sx, y, cz + r * math.sin(a) * sz))
    for i in range(len(prof) - 1):
        (pole0, i0), (pole1, i1) = rings[i], rings[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            if pole0 and pole1:
                continue
            if pole0:
                faces.append((i0, i1 + k2, i1 + k))
            elif pole1:
                faces.append((i0 + k, i0 + k2, i1))
            else:
                faces.append((i0 + k, i0 + k2, i1 + k2, i1 + k))
    if not rings[0][0]:
        faces.append(tuple(rings[0][1] + k for k in range(segs)))
    if not rings[-1][0]:
        faces.append(tuple(rings[-1][1] + k for k in range(segs)))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def tube(p, pts, radii, col, sides=8, jit=0.04, caps=True, rib=0.0, ribs=3, twist=0.0):
    """Closed tube along a 3D polyline (stage coordinates), radius per point. rib = depth of lengthwise ridges (fraction of the radius)."""
    n = len(pts)
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * n
    P = [Vector(q) for q in pts]
    T = [(P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    N = (ref - T[0] * ref.dot(T[0])).normalized()
    points, faces = [], []
    for i in range(n):
        if i:
            N = (N - T[i] * N.dot(T[i])).normalized()
        Bv = T[i].cross(N)
        for k in range(sides):
            a = 2 * math.pi * k / sides + twist * i
            rr = radii[i] * (1.0 - rib * (1 - math.cos(ribs * a)) / 2)
            points.append(tuple(P[i] + (N * math.cos(a) + Bv * math.sin(a)) * rr))
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k2, (i + 1) * sides + k2, (i + 1) * sides + k))
    if caps:
        faces.append(tuple(range(sides)))
        faces.append(tuple((n - 1) * sides + k for k in range(sides)))
    return dk.poly(p, (0, 0, 0), points, faces, col, jit)


def rock(p, x, y0, z, sx, sy, sz, col, seed=1, jit=0.07, sub=1, flat=-0.5):
    """Lumpy low-poly rock with a flat foot, exactly sx x sy x sz, standing on y0 at (x, z)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        v.co *= 1.0 + (rng.random() - 0.5) * 0.36
        v.co.z = max(v.co.z, flat)
    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    for v in bm.verts:
        v.co.x = (v.co.x - lo.x) / (hi.x - lo.x) * sx - sx / 2
        v.co.y = (v.co.y - lo.y) / (hi.y - lo.y) * sz - sz / 2
        v.co.z = (v.co.z - lo.z) / (hi.z - lo.z) * sy
    return dk._object(p, "Rock", bm, S(x, y0, z), (0, 0, 0), col, jit)


def stone(p, cx, y0, cz, w, h, d, col, yaw=0, seed=1, jit=0.06, taper=0.78, rough=0.1, lean=0.0):
    """Rough standing stone w x d at the foot, h tall, narrowing to the top, yaw = Roblox rotation about the vertical axis."""
    rng = random.Random(seed)
    levels = [(0.0, 1.0), (0.5, 1.0 - (1 - taper) * 0.3), (1.0, taper)]
    pts = []
    for li, (fy, sc) in enumerate(levels):
        for (sxn, szn) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            dx = (rng.random() - 0.5) * rough * w * (0 if li == 0 else 1)
            dz = (rng.random() - 0.5) * rough * d * (0 if li == 0 else 1)
            y = h * fy
            if li == 2:
                y = h * (1.0 - 0.07 * rng.random() - (0.05 if sxn * szn < 0 else 0))
            x = sxn * w / 2 * sc + dx + lean * fy * h
            z = szn * d / 2 * sc + dz
            a, b = ry(x, z, yaw)
            pts.append((cx + a, y0 + y, cz + b))
    faces = [(0, 1, 2, 3), (8, 11, 10, 9)]
    for l in range(2):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((l * 4 + k, l * 4 + k2, (l + 1) * 4 + k2, (l + 1) * 4 + k))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def blade(p, base, ang, L, W, tilt, col, vcol, droop=1.0, th=0.5, jit=0.05, veins=2, n=7, cup=0.3):
    """Leaf blade: base point (x, y, z), direction ang (Roblox ry: dir = (cos a, -sin a) in x, z), tilted `tilt` degrees upward,
    length L, width W, pointed at both ends, tip drooping, edges slightly raised. Midrib and side veins in vcol."""
    a = math.radians(ang)
    t = math.radians(tilt)
    dh = Vector((math.cos(a), 0, -math.sin(a)))
    sd = Vector((math.sin(a), 0, math.cos(a)))
    up = Vector((0, 1, 0))
    b0 = Vector(base)
    top, bot = [], []
    mids = []
    for i in range(n):
        u = i / (n - 1)
        along = L * u
        c = b0 + dh * (along * math.cos(t)) + up * (along * math.sin(t) - droop * u * u)
        hw = max(0.06, W / 2 * math.sin(math.pi * min(0.999, u ** 0.8)) ** 0.85)
        e = cup * hw
        mids.append((c, hw))
        top.append((c + sd * (-hw) + up * e, c + up * 0.0, c + sd * hw + up * e))
        bot.append((c + sd * (-hw) + up * (e - th), c + up * (-th), c + sd * hw + up * (e - th)))
    pts = []
    for i in range(n):
        pts += [tuple(v) for v in top[i]] + [tuple(v) for v in bot[i]]
    # per station: 0 TL, 1 TM, 2 TR, 3 BL, 4 BM, 5 BR
    def ix(i, k):
        return i * 6 + k
    faces = []
    for i in range(n - 1):
        faces += [(ix(i, 0), ix(i, 1), ix(i + 1, 1), ix(i + 1, 0)), (ix(i, 1), ix(i, 2), ix(i + 1, 2), ix(i + 1, 1)),
                  (ix(i, 3), ix(i + 1, 3), ix(i + 1, 4), ix(i, 4)), (ix(i, 4), ix(i + 1, 4), ix(i + 1, 5), ix(i, 5)),
                  (ix(i, 0), ix(i + 1, 0), ix(i + 1, 3), ix(i, 3)), (ix(i, 2), ix(i, 5), ix(i + 1, 5), ix(i + 1, 2))]
    faces.append((ix(0, 0), ix(0, 1), ix(0, 2), ix(0, 5), ix(0, 4), ix(0, 3)))
    faces.append((ix(n - 1, 0), ix(n - 1, 3), ix(n - 1, 4), ix(n - 1, 5), ix(n - 1, 2), ix(n - 1, 1)))
    out = [dk.poly(p, (0, 0, 0), pts, faces, col, jit)]
    if vcol is not None:
        lift = Vector((0, 0.1, 0))
        out.append(bar(p, tuple(mids[0][0] + lift), tuple(mids[-2][0] + lift), 0.32, vcol, 0.02))
        for j in range(veins):
            i = 2 + j * 2
            if i >= n - 1:
                break
            c, hw = mids[i]
            for sgn in (-1, 1):
                a1 = c + lift
                a2 = c + dh * (L * 0.12 * math.cos(t)) + sd * (sgn * hw * 0.92) + Vector((0, cup * hw + 0.1, 0))
                out.append(bar(p, tuple(a1), tuple(a2), 0.22, vcol, 0.02))
    return out


def tuft(p, x, z, h, col, n=5, y0=0.0, spread=0.5, seed=1):
    """Little grass tuft: n thin 3-sided blades leaning outwards."""
    rng = random.Random(seed)
    lo, hi = BOX
    m = spread + 0.6
    if not (lo[0] + m <= x <= hi[0] - m and lo[2] + m <= z <= hi[2] - m):
        return
    for k in range(n):
        a = 2 * math.pi * k / n + rng.random()
        lean = 12 + rng.random() * 14
        hh = h * (0.7 + rng.random() * 0.5)
        ox, oz = math.cos(a) * spread * 0.4, math.sin(a) * spread * 0.4
        dk.cyl(p, (x + ox + math.sin(math.radians(lean)) * hh * 0.4 * math.cos(a), y0 + hh / 2, z + oz + math.sin(math.radians(lean)) * hh * 0.4 * math.sin(a)),
               spread * 0.22, hh, col, axis='y', verts=3, top_radius=0.01, jitter=0.1)


def prism_x(p, tri, x0, x1, col, jit=0.04):
    """Triangular prism extruded along x: tri = three (y, z) points."""
    pts = [(x0, a, b) for a, b in tri] + [(x1, a, b) for a, b in tri]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def disc(p, cx, y0, y1, cz, rx, rz, col, n=16, jit=0.05):
    """Flat elliptical slab (like the old edisc) between y0 and y1."""
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), y0, cz + rz * math.sin(2 * math.pi * i / n)) for i in range(n)]
    pts += [(x, y1, z) for (x, _, z) in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def spots(p, cx, cy, cz, prof_fn, count, rmax, col, seed=3, size=0.9):
    """White spots on a dome: prof_fn(r) -> y of the dome surface at horizontal radius r."""
    rng = random.Random(seed)
    for k in range(count):
        a = 2 * math.pi * k / count + rng.random() * 0.6
        r = rmax * (0.25 + 0.6 * rng.random())
        y = prof_fn(r)
        dk.cyl(p, (cx + r * math.cos(a), y - size * 0.1, cz + r * math.sin(a)), size * (0.8 + 0.5 * rng.random()), size * 0.5, col,
               axis='y', verts=6, jitter=0.03)


# ---- 1. Ground ------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    xs = [-90 + 20 * i for i in range(10)]
    zs = [-65 + 130 / 7 * j for j in range(8)]
    for i in range(9):
        for j in range(7):
            col = GRASS if (i + j) % 2 else (102, 168, 80)
            bx(p, (xs[i], xs[i + 1]), (0, 0.3), (zs[j], zs[j + 1]), col, 0.05)
    # slate plaza under the Shiba: outer ring of flagstones, lighter inner square
    for i in range(4):
        for j in range(4):
            x0, z0 = 14 + 7 * i, -38 + 7 * j
            if 18 <= x0 and x0 + 7 <= 38 + 1 and -34 <= z0 and z0 + 7 <= -14 + 1:
                continue
            bx(p, (x0 + 0.08, x0 + 6.92), (0.3, 0.5), (z0 + 0.08, z0 + 6.92), STONE if (i + j) % 2 else DSTONE, 0.06)
    for i in range(3):
        for j in range(3):
            x0, z0 = 18 + 20 / 3 * i, -34 + 20 / 3 * j
            bx(p, (x0 + 0.08, x0 + 6.6), (0.3, 0.59), (z0 + 0.08, z0 + 6.6), LSTONE if (i + j) % 2 else (200, 202, 204), 0.04)
    # ring of bare earth for the stones with a moss disc inside
    disc(p, -52, 0.3, 0.5, 28, 23, 23, DIRT, n=20)
    disc(p, -52, 0.3, 0.56, 28, 15, 15, MOSS, n=18)
    # churned dark earth where the beanstalk will grow, with a few cracks
    disc(p, 62, 0.3, 0.52, -44, 17, 17, DDIRT, n=20)
    for k in range(7):
        a = math.radians(25 + 51 * k)
        bx(p, (62 + 9 * math.cos(a) - 0.2, 62 + 9 * math.cos(a) + 0.2), (0.3, 0.56), (-44 - 9 * math.sin(a) - 0.2, -44 - 9 * math.sin(a) + 0.2),
           (84, 58, 40), 0.02)
    # darker grass patches
    disc(p, -10, 0.3, 0.45, -52, 15, 8, GRASS2, n=14)
    disc(p, 60, 0.3, 0.45, 30, 17, 10, GRASS2, n=14)
    disc(p, -26, 0.3, 0.45, 40, 13, 7, GRASS2, n=14)


# ---- 2. Signpost ----------------------------------------------------------------------------------------------------------
def build_Signpost(p):
    for x in (7.2, 20.8):
        rock(p, x, 0, 52, 3.4, 1.0, 3.2, STONE, seed=int(x))
        vcyl(p, x, 0.5, 11.5, 52, 0.8, DWOOD, verts=8)
    for k, c in enumerate((LWOOD, (206, 160, 104), LWOOD)):
        bx(p, (5.5, 22.5), (6.6 + 2 * k, 8.6 + 2 * k - 0.05), (51.4, 52.4), c, 0.05)
    bx(p, (4.8, 23.2), (12.5, 13.5), (51.0, 53.0), DWOOD, 0.04)
    for x in (4.8, 23.2):
        bx(p, (x - 0.4, x + 0.4), (13.5, 13.9), (51.4, 52.6), DWOOD, 0.03)
    text(p, "GIANTS", 14, 7.9, 52.4, 52.8, 2.2, 3.4, 0.55, 0.45, DWOOD)
    arrow = [(7.0, 4.6), (9.0, 5.9), (15, 5.9), (15, 3.3), (9.0, 3.3)]
    pts = [(a, b, 52.0) for a, b in arrow] + [(a, b, 52.9) for a, b in arrow]
    faces = [(0, 1, 2, 3, 4), (5, 9, 8, 7, 6), (0, 1, 6, 5), (1, 2, 7, 6), (2, 3, 8, 7), (3, 4, 9, 8), (4, 0, 5, 9)]
    dk.poly(p, (0, 0, 0), pts, faces, WOOD, 0.05)
    text(p, "GO", 12, 4.1, 52.9, 53.0, 1.4, 1.4, 0.35, 0.3, DWOOD)
    # a bean vine climbing the right post
    pts = []
    for i in range(22):
        t = i / 21
        a = t * 5.2 * math.pi
        pts.append((20.8 + 0.95 * math.cos(a), 1.0 + 5.3 * t, 52 + 0.95 * math.sin(a)))
    tube(p, pts, [0.24 * (1 - 0.5 * i / 21) for i in range(22)], LBEAN, sides=4, caps=True)
    blade(p, (21.6, 3.2, 52.2), 20, 2.6, 1.3, 25, BEAN, None, n=4, droop=0.3)
    blade(p, (20.0, 6.0, 52.9), 160, 2.4, 1.2, 25, BEAN, None, n=4, droop=0.3)
    for x in (9.5, 18.5):
        tuft(p, x, 53.0, 0.9, GRASS2, n=4, seed=int(x))


# ---- 3. FieldWall ---------------------------------------------------------------------------------------------------------
def drywall(p, x0, x1, z0, z1, h, seed, courses=3):
    rng = random.Random(seed)
    along_x = (x1 - x0) >= (z1 - z0)
    if along_x:
        bx(p, (x0 + 0.1, x1 - 0.1), (0, h), (z0 + 0.25, z1 - 0.25), (84, 86, 92), 0.03)
    else:
        bx(p, (x0 + 0.25, x1 - 0.25), (0, h), (z0 + 0.1, z1 - 0.1), (84, 86, 92), 0.03)
    ch = h / courses
    for c in range(courses):
        a = (x0 if along_x else z0) + (0 if c % 2 == 0 else -1.2)
        end = x1 if along_x else z1
        start = x0 if along_x else z0
        pos = a
        while pos < end - 0.05:
            ln = 2.0 + rng.random() * 1.6
            lo, hi = max(pos, start), min(pos + ln, end)
            pos += ln
            if hi - lo < 0.5:
                continue
            col = (STONE, DSTONE, (166, 168, 172), (136, 138, 144))[rng.randrange(4)]
            inset = rng.random() * 0.18
            if along_x:
                bx(p, (lo + 0.05, hi - 0.05), (c * ch + 0.04, (c + 1) * ch - 0.04), (z0 + inset, z1 - rng.random() * 0.18), col, 0.07)
            else:
                bx(p, (x0 + inset, x1 - rng.random() * 0.18), (c * ch + 0.04, (c + 1) * ch - 0.04), (lo + 0.05, hi - 0.05), col, 0.07)


def build_FieldWall(p):
    drywall(p, 55, 67, 56.7, 59.3, 3.2, 2)
    drywall(p, 78, 88, 56.7, 59.3, 3.2, 5)
    drywall(p, 85.4, 88.0, 45, 57, 3.2, 8)
    for x0, x1, z0, z1 in ((54.7, 67.3, 56.4, 59.6), (77.7, 88.3, 56.4, 59.6), (85.1, 88.3, 44.7, 57.3)):
        n = int((max(x1 - x0, z1 - z0)) // 3.2) + 1
        ln = max(x1 - x0, z1 - z0) / n
        for k in range(n):
            col = LSTONE if k % 2 else (176, 178, 182)
            if x1 - x0 > z1 - z0:
                bx(p, (x0 + k * ln + 0.05, x0 + (k + 1) * ln - 0.05), (3.2, 3.8), (z0, z1), col, 0.06)
            else:
                bx(p, (x0, x1), (3.2, 3.8), (z0 + k * ln + 0.05, z0 + (k + 1) * ln - 0.05), col, 0.06)
    for cx in (68.2, 77.6):
        for k in range(3):
            bx(p, (cx - 1.2, cx + 1.2), (k * 1.5, k * 1.5 + 1.45), (56.8, 59.2), DSTONE if k % 2 else (126, 128, 136), 0.05)
        bx(p, (cx - 1.2, cx + 1.2), (4.5, 5.0), (56.8, 59.2), LSTONE, 0.04)
        dk.cyl(p, (cx, 5.3, 58), 0.9, 0.6, LSTONE, axis='y', verts=4, top_radius=0.1, jitter=0.04, rot=(0, 45, 0))
    # the gate swung open (turned 50 degrees about its middle)
    gx, gz, gd = 71, 56.6, 50
    for ly in (2.4, 3.6, 4.8):
        lbox(p, gx, gz, gd, 0, ly, 0, 5.2, 0.4, 0.5, WOOD, 0.05)
    for lx in (-2.4, 2.4):
        lbox(p, gx, gz, gd, lx, 3.6, 0, 0.4, 3.4, 0.5, DWOOD, 0.04)
    for lx in (-1.2, 0, 1.2):
        lbox(p, gx, gz, gd, lx, 3.6, 0.05, 0.3, 3.0, 0.4, LWOOD, 0.05)
    # moss and tufts
    for (x, z, s) in ((58, 56.5, 2.4), (82, 56.5, 2.0), (72, 59.5, 1.4)):
        blob(p, x, 1.2, z, s, 0.7, 0.5, LMOSS, sub=1, jit=0.05)
    blob(p, 60.5, 3.9, 58, 3.0, 0.5, 2.0, LMOSS, sub=1, jit=0.05)
    blob(p, 83.5, 3.9, 58, 2.4, 0.5, 2.0, MOSS, sub=1, jit=0.05)
    for (x, z) in ((56, 55.6), (66, 55.8), (79, 55.8), (86, 60.0), (84.8, 47)):
        tuft(p, x, z, 1.1, GRASS2, n=5, seed=int(x + z))


# ---- 4. Boulders ----------------------------------------------------------------------------------------------------------
def build_Boulders(p):
    rock(p, -84, 0, 57, 9, 6.4, 8, STONE, seed=3, jit=0.09, sub=2)
    rock(p, -76, 0, 54, 6.4, 4.8, 6, DSTONE, seed=5, jit=0.09)
    rock(p, -80, 0, 60, 7, 4, 5.6, STONE, seed=7, jit=0.09)
    rock(p, -72, 0, 60, 4.4, 3, 4, LSTONE, seed=9, jit=0.09)
    rock(p, -86, 0, 50, 5, 3.6, 4.4, DSTONE, seed=11, jit=0.09)
    rock(p, -70, 0, 53.6, 2.4, 1.6, 2.2, STONE, seed=13)
    blob(p, -84, 6.1, 57, 6, 2.4, 5.2, MOSS, sub=2, jit=0.07)
    blob(p, -82, 6.5, 56, 3, 1.4, 2.6, LMOSS, sub=1, jit=0.07)
    for (x, z, s) in ((-87.5, 53.5, 1), (-74, 51.5, 2), (-78.5, 63, 3), (-70.5, 57, 4), (-88, 59.5, 5)):
        tuft(p, x, z, 1.4, GRASS2, n=5, seed=s)
    for (x, z, c) in ((-74.6, 57.2, WHITE), (-82.5, 51.4, SUN), (-72.8, 62.2, WHITE)):
        vcyl(p, x, 0, 1.2, z, 0.08, GRASS2, verts=3)
        blob(p, x, 1.35, z, 0.7, 0.35, 0.7, c, sub=1, jit=0.02)


# ---- 5. Daisies -----------------------------------------------------------------------------------------------------------
def petal(p, c, phi, tilt, r0, ln, w, col):
    """Flat diamond petal around head centre c, radial direction phi (Roblox ry), the head tilted by `tilt` about x."""
    a = math.radians(phi)
    t = math.radians(tilt)
    dx, dz = math.cos(a), -math.sin(a)
    sx, sz = math.sin(a), math.cos(a)
    loc = [(r0, 0, 0), (r0 + ln * 0.38, 0, w), (r0 + ln, 0, 0), (r0 + ln * 0.38, 0, -w)]
    pts = []
    for th in (0.12, -0.12):
        for (u, _, v) in loc:
            x, y, z = dx * u + sx * v, th, dz * u + sz * v
            y2, z2 = y * math.cos(t) - z * math.sin(t), y * math.sin(t) + z * math.cos(t)
            pts.append((c[0] + x, c[1] + y2, c[2] + z2))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, 0.04)


def daisy(p, x, z, hy, tilt=22):
    stem = [(x, 0.5, z), (x + 0.25, hy * 0.35, z + 0.1), (x + 0.4, hy * 0.7, z + 0.25), (x + 0.2, hy - 0.4, z + 0.55)]
    tube(p, stem, [0.5, 0.45, 0.4, 0.38], GRASS2, sides=5)
    c = (x + 0.2, hy, z + 0.6)
    t = math.radians(tilt)
    for k in range(10):
        petal(p, c, k * 36, tilt, 1.4, 2.9, 0.6, WHITE if k % 2 else (240, 242, 248))
    dk.cyl(p, (c[0], c[1] + 0.35 * math.cos(t), c[2] + 0.35 * math.sin(t)), 1.9, 0.9, GOLD, axis='y', verts=8, jitter=0.04, rot=(tilt, 0, 0))
    dk.cyl(p, (c[0], c[1] + 0.8 * math.cos(t), c[2] + 0.8 * math.sin(t)), 1.2, 0.8, DGOLD, axis='y', verts=7, jitter=0.05, rot=(tilt, 0, 0))
    blade(p, (x + 0.3, 0.8, z + 0.1), 25 + x * 7, 4.2, 1.5, 30, GRASS2, None, n=4, droop=0.8)
    blade(p, (x - 0.1, 0.9, z), 200 + x * 5, 3.6, 1.3, 30, GRASS, None, n=4, droop=0.7)


def build_Daisies(p):
    daisy(p, 72, 40, 10.6)
    daisy(p, 80, 46, 12.6)
    daisy(p, 66, 46, 8.6)
    for (x, z) in ((70, 43.5), (76, 38.5), (83, 43), (63, 44)):
        tuft(p, x, z, 1.3, GRASS2, n=5, seed=int(x))


# ---- 6. HayBales ----------------------------------------------------------------------------------------------------------
def round_bale(p, cx, cy, cz):
    xcyl(p, cx - 4, cx + 4, cy, cz, 3.0, HAY, verts=12, jit=0.06)
    for ln, r, c in ((8.04, 2.2, DHAY), (8.08, 1.4, HAY), (8.12, 0.6, DHAY)):
        xcyl(p, cx - ln / 2, cx + ln / 2, cy, cz, r, c, verts=12, jit=0.03)
    for dx in (-2.6, 0, 2.6):
        xcyl(p, cx + dx - 0.18, cx + dx + 0.18, cy, cz, 3.08, (150, 110, 50), verts=12, jit=0.03)


def square_bale(p, cx, cz, deg):
    lbox(p, cx, cz, deg, 0, 1.7, 0, 5, 3.4, 3.6, HAY, 0.06)
    for lx in (-1.4, 1.4):
        lbox(p, cx, cz, deg, lx, 1.7, 0, 0.3, 3.5, 3.7, (150, 110, 50), 0.03)
    lbox(p, cx, cz, deg, 0, 3.45, 0, 4.6, 0.12, 3.3, DHAY, 0.05)


def build_HayBales(p):
    round_bale(p, 74, 3, -12)
    round_bale(p, 82, 3, -12)
    round_bale(p, 78, 8.6, -12.2)
    square_bale(p, 76, -20, 0)
    square_bale(p, 80.6, -19.4, 20)
    vcyl(p, 86, 0.4, 9.6, -17, 0.25, DWOOD, verts=6)
    bx(p, (85.1, 86.9), (9.2, 9.6), (-17.2, -16.8), IRON, 0.03)
    for dx in (-0.8, 0, 0.8):
        bx(p, (86 + dx - 0.1, 86 + dx + 0.1), (9.6, 11.0), (-17.1, -16.9), IRON, 0.03)
    rng = random.Random(4)
    for k in range(16):
        x, z = 69 + rng.random() * 19, -23 + rng.random() * 14
        if (70 < x < 86 and -16 < z < -8):
            continue
        dk.box(p, (x, 0.12, z), (1.6 + rng.random() * 1.2, 0.12, 0.14), DHAY if k % 2 else HAY, rot=(0, rng.random() * 180, 0), jitter=0.04)
    for (x, z) in ((70, -9), (87, -23), (72, -22)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(x))


# ---- 7. Beans -------------------------------------------------------------------------------------------------------------
def bean(p, x, y, z, ln, col, deg, sub=1):
    blob(p, x, y, z, ln, ln * 0.52, ln * 0.64, col, sub=sub, jit=0.06, rot=(0, deg, 0))


def build_Beans(p):
    prof = [(0, 0.0), (2.6, 0.1), (3.1, 1.2), (2.9, 2.6), (1.9, 3.8), (1.2, 4.5), (1.1, 4.9), (1.9, 5.5), (1.2, 5.3), (0, 5.0)]
    lathe(p, 40, -14, prof, TAN, segs=10, jit=0.05, sz=0.85)
    vcyl(p, 40, 4.6, 5.1, -14, 1.25, BROWN, verts=10, jit=0.03)
    for a in (0.5, 2.0, 3.6, 5.2):
        bx(p, (40 + 2.5 * math.cos(a) - 0.1, 40 + 2.5 * math.cos(a) + 0.1), (0.4, 3.0), (-14 + 2.1 * math.sin(a) - 0.1, -14 + 2.1 * math.sin(a) + 0.1), DTAN, 0.03)
    # beans spilling out of the sack mouth and over the grass
    bean(p, 40.5, 5.6, -14.4, 2.2, PBEAN, 20, 2)
    bean(p, 39.4, 5.5, -13.4, 2.0, BEAN, 100, 2)
    for (x, z, c, d) in ((45, -11, BEAN, 10), (47.6, -13, PBEAN, 70), (44.4, -15.8, LBEAN, 130), (42.6, -9.6, PBEAN, 30),
                          (37.6, -9.4, BEAN, 160), (49.6, -9.8, LBEAN, 80), (43.4, -18.8, BEAN, 120), (46.4, -9.0, LBEAN, 15)):
        bean(p, x, 0.8, z, 2.8, c, d, 2)
    # the first sprout
    stem = [(48, 0.2, -17.4), (48.1, 1.6, -17.3), (48.5, 3.2, -17.4), (49.2, 4.4, -17.4), (50.0, 4.9, -17.4)]
    tube(p, stem, [0.35, 0.3, 0.27, 0.22, 0.14], BEAN, sides=5)
    blade(p, (48.4, 3.9, -17.4), 0, 3.0, 1.7, 15, LBEAN, GRASS2, n=4, droop=0.5, veins=0)
    blade(p, (48.3, 3.9, -17.4), 180, 3.0, 1.7, 15, LBEAN, GRASS2, n=4, droop=0.5, veins=0)
    for (x, z) in ((38, -19), (42, -8.6), (50, -12), (45, -19.5)):
        tuft(p, x, z, 1.1, GRASS2, n=4, seed=int(x))


# ---- 8. Cottage -----------------------------------------------------------------------------------------------------------
def build_Cottage(p):
    X0, X1, Z0, Z1 = -78.8, -65.2, -11.3, -0.7
    # cobble footing
    bx(p, (-79.3, -64.7), (0, 1.0), (-11.8, -0.2), (126, 128, 136), 0.04)
    rng = random.Random(6)
    for k in range(9):
        x0 = -79.3 + k * 1.51
        bx(p, (x0 + 0.06, x0 + 1.45), (0.05, 0.95), (-0.45, -0.1), (STONE, DSTONE, LSTONE)[k % 3], 0.07)
    for k in range(6):
        z0 = -11.8 + k * 1.93
        for xx in (-79.55, -64.45):
            bx(p, (xx - 0.15, xx + 0.15), (0.05, 0.95), (z0 + 0.06, z0 + 1.85), (STONE, DSTONE, LSTONE)[k % 3], 0.07)
    # plaster walls and timber frame
    bx(p, (X0, X1), (1.0, 6.8), (Z0, Z1), CREAM, 0.03)
    for xx in (X0, X1 - 0.35):
        for zz in (Z0, Z1 - 0.35):
            bx(p, (xx - 0.05, xx + 0.4), (1.0, 6.8), (zz - 0.05, zz + 0.4), DWOOD, 0.03)
    bx(p, (X0 - 0.05, X1 + 0.05), (6.35, 6.85), (Z1 - 0.2, Z1 + 0.05), DWOOD, 0.03)
    bx(p, (X0 - 0.05, X1 + 0.05), (1.0, 1.4), (Z1 - 0.2, Z1 + 0.05), DWOOD, 0.03)
    bx(p, (X0 - 0.05, X1 + 0.05), (6.35, 6.85), (Z0 - 0.05, Z0 + 0.2), DWOOD, 0.03)
    for zz in (Z0 - 0.05, Z1 - 0.2):
        for xx in (X0 - 0.05, X1 - 0.2):
            pass
    bx(p, (X0 - 0.05, X0 + 0.2), (6.35, 6.85), (Z0, Z1), DWOOD, 0.03)
    bx(p, (X1 - 0.2, X1 + 0.05), (6.35, 6.85), (Z0, Z1), DWOOD, 0.03)
    # braces on the front
    for sx in (-1, 1):
        cx = -72 + sx * 5.6
        dk.box(p, (cx, 5.3, Z1 + 0.0), (2.4, 0.3, 0.3), DWOOD, rot=(0, 0, 40 * sx), jitter=0.03)
    # gable ends and roof
    prism_x(p, [(6.8, Z0), (6.8, Z1), (11.0, -6.0)], X0, X1, CREAM, 0.03)
    th = math.radians(35)
    for side in (1, -1):
        for k in range(3):
            u = 1.3 + k * 2.6
            zc = (0.395 - u * math.cos(th)) if side == 1 else (-12 - (0.395 - u * math.cos(th)))
            yc = 6.76 + u * math.sin(th)
            n = (0, math.cos(th), math.sin(th) * side)
            thick = 0.62 + 0.1 * (2 - k)
            dk.box(p, (-72, yc + n[1] * thick / 2, zc + n[2] * thick / 2), (15.6, thick, 2.7), THATCH if k % 2 == 0 else DTHATCH,
                   rot=(35 * side, 0, 0), jitter=0.05)
    dk.box(p, (-72, 11.35, -6.0), (15.8, 0.8, 0.9), DTHATCH, rot=(45, 0, 0), jitter=0.04)
    # chimney
    for k in range(5):
        bx(p, (-68.1, -65.9), (6.6 + k * 1.3, 6.6 + (k + 1) * 1.3 - 0.04), (-10.1, -7.9), (STONE, DSTONE)[k % 2], 0.05)
    bx(p, (-68.4, -65.6), (13.0, 13.8), (-10.4, -7.6), DSTONE, 0.04)
    bx(p, (-67.7, -66.3), (13.7, 13.84), (-9.7, -8.3), BLACK, 0.02)
    # door, steps, windows
    bx(p, (-73.65, -70.35), (1.0, 5.5), (-0.78, -0.4), DWOOD, 0.03)
    for k in range(3):
        bx(p, (-73.3 + k * 0.867 + 0.03, -73.3 + (k + 1) * 0.867 - 0.03), (1.05, 5.3), (-0.62, -0.38), (WOOD, LWOOD, WOOD)[k], 0.05)
    bx(p, (-72.0, -71.8), (3.0, 3.5), (-0.4, -0.3), BLACK, 0.02)
    ball(p, (-71.2, 3.2, -0.3), 0.18, GOLD, subdiv=1)
    bx(p, (-74, -70), (0, 0.8), (-0.3, 2.4), STONE, 0.05)
    for xx in (-76.5, -67.5):
        bx(p, (xx - 1.35, xx + 1.35), (3.35, 5.85), (-0.7, -0.35), DWOOD, 0.03)
        bx(p, (xx - 1.0, xx + 1.0), (3.6, 5.6), (-0.45, -0.3), SKY, 0.03)
        bx(p, (xx - 0.07, xx + 0.07), (3.6, 5.6), (-0.4, -0.27), DWOOD, 0.02)
        bx(p, (xx - 1.0, xx + 1.0), (4.53, 4.67), (-0.4, -0.27), DWOOD, 0.02)
        for sx in (-1, 1):
            bx(p, (xx + sx * 1.35 - (0.0 if sx > 0 else 0.7), xx + sx * 1.35 + (0.7 if sx > 0 else 0.0)), (3.35, 5.85), (-0.7, -0.5), GRASS2, 0.05)
        bx(p, (xx - 1.5, xx + 1.5), (2.6, 3.3), (-1.4, -0.7), WOOD, 0.04)
        for k, c in enumerate((RED, SUN, PINK, RED)):
            blob(p, xx - 1.1 + k * 0.73, 3.55, -1.0, 0.75, 0.6, 0.65, c, sub=1, jit=0.03)
        bx(p, (xx - 1.5, xx + 1.5), (3.3, 3.5), (-1.2, -0.8), GRASS2, 0.03)
    for xx in (X0, X1):
        s = -1 if xx == X0 else 1
        bx(p, (xx - (0.0 if s > 0 else 0.3), xx + (0.3 if s > 0 else 0.0)), (3.4, 5.6), (-7.1, -4.9), DWOOD, 0.03)
        bx(p, (xx - (0.0 if s > 0 else 0.2), xx + (0.2 if s > 0 else 0.0)), (3.65, 5.35), (-6.85, -5.15), SKY, 0.03)
    for (x, z) in ((-79.4, 1.0), (-64.6, 1.2), (-70, 3.5)):
        tuft(p, x, z, 1.1, GRASS2, n=5, seed=int(abs(x)))


# ---- 9. OakTree -----------------------------------------------------------------------------------------------------------
def ring_blocks(p, cx, cz, R, n, w, depth, y0, y1, cols, off=0.0, jit=0.06):
    for k in range(n):
        a = math.radians(360 * k / n + off)
        x, z = cx + R * math.cos(a), cz + R * math.sin(a)
        ryd = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        dk.box(p, (x, (y0 + y1) / 2, z), (w, y1 - y0, depth), cols[k % len(cols)], rot=(0, ryd, 0), jitter=jit)


def gable_roof(p, xa, xb, z_ridge, y_eave, run, rise, cols, rows=3, thick=0.6):
    th = math.atan2(rise, run)
    S_len = math.hypot(run, rise)
    rl = S_len / rows
    for side in (1, -1):
        for k in range(rows):
            u = rl * (k + 0.5)
            zc = z_ridge + side * (run - u * math.cos(th))
            yc = y_eave + u * math.sin(th)
            n = (0, math.cos(th), side * math.sin(th))
            dk.box(p, (cx_of(xa, xb), yc + n[1] * thick / 2, zc + n[2] * thick / 2), (xb - xa, thick, rl + 0.08), cols[k % len(cols)],
                   rot=(math.degrees(th) * side, 0, 0), jitter=0.05)


def cx_of(a, b):
    return (a + b) / 2


def build_OakTree(p):
    X, Z = -80, -30
    tube(p, [(X, 0.0, Z), (X + 0.2, 3.5, Z - 0.1), (X, 7.0, Z), (X - 0.3, 10.2, Z + 0.1)], [2.3, 1.7, 1.5, 1.3], DWOOD, sides=8, rib=0.12, ribs=4)
    for k in range(5):
        a = math.radians(30 + 72 * k)
        tube(p, [(X + 0.8 * math.cos(a), 2.0, Z - 0.8 * math.sin(a)), (X + 2.0 * math.cos(a), 0.9, Z - 2.0 * math.sin(a)),
                 (X + 3.0 * math.cos(a), 0.0, Z - 3.0 * math.sin(a))], [1.0, 0.8, 0.5], DWOOD, sides=5)
    # branches into the crown
    for (dx, dz, ex, ey, ez) in ((-0.5, 0.3, -4.5, 13.0, -3.0), (0.4, 0.2, 3.8, 12.8, 3.0), (0.0, -0.4, -4.0, 12.0, 2.6)):
        tube(p, [(X + dx, 8.4, Z + dz), (X + dx + ex * 0.4, 10.4, Z + dz + ez * 0.4), (X + ex, ey, Z + ez)], [0.8, 0.6, 0.4], DWOOD, sides=5)
    for (x, y, z, sx, sy, sz, c) in ((-80, 15, -30, 14, 9, 13, GRASS2), (-84, 13, -33, 10, 7, 9, GRASS), (-76, 13.5, -27, 10, 7, 9, GRASS2),
                                     (-80, 19.5, -30, 9, 6, 8.4, GRASS), (-85, 14.2, -27, 8, 6, 7.4, GRASS2), (-77, 17.5, -33, 7, 5, 6.5, LGRASS),
                                     (-82.5, 18, -26, 6.5, 4.6, 6, GRASS), (-73.8, 12, -31, 5, 4, 5, GRASS2)):
        blob(p, x, y, z, sx, sy, sz, c, sub=2, jit=0.09)
    # tyre swing on the south branch
    tube(p, [(X + 0.5, 8.6, Z + 0.4), (X + 2.6, 9.6, Z + 1.5), (X + 4.0, 10.2, Z + 1.8)], [0.6, 0.5, 0.4], DWOOD, sides=5)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        bar(p, (X + 4.0, 10.0, Z + 1.8), (X + 4.0 + 0.9 * math.cos(a), 5.2, Z + 1.8 + 0.9 * math.sin(a)), 0.14, TAN, 0.02)
    torus(p, (X + 4.0, 4.9, Z + 1.8), 1.3, 0.55, (46, 46, 54), segs=12, sides=5, jit=0.03)
    for (x, z) in ((-84, -26), (-76, -34), (-86, -32), (-75, -26.5)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 10. Well -------------------------------------------------------------------------------------------------------------
def build_Well(p):
    X, Z = -26, -30
    ring_blocks(p, X, Z, 3.75, 12, 2.3, 1.1, 0.0, 2.4, (STONE, DSTONE, LSTONE), 0.0, 0.07)
    ring_blocks(p, X, Z, 3.75, 12, 2.3, 1.1, 2.4, 4.8, (DSTONE, STONE, LSTONE), 15.0, 0.07)
    vcyl(p, X, 0.0, 4.7, Z, 3.3, (96, 98, 106), verts=12, jit=0.03)
    disc(p, X, 4.35, 4.6, Z, 3.15, 3.15, WATER, n=12)
    for k in range(12):
        a = math.radians(30 * k + 7)
        bx(p, (X + 4.2 * math.cos(a) - 0.4, X + 4.2 * math.cos(a) + 0.4), (4.8, 5.1), (Z + 4.2 * math.sin(a) - 0.4, Z + 4.2 * math.sin(a) + 0.4),
           LSTONE, 0.06) if False else None
    for x in (-29.6, -22.4):
        bx(p, (x - 0.4, x + 0.4), (4.8, 12.0), (Z - 0.4, Z + 0.4), WOOD, 0.04)
        bx(p, (x - 0.6, x + 0.6), (4.8, 5.4), (Z - 0.6, Z + 0.6), DWOOD, 0.04)
    xcyl(p, -30.2, -21.8, 10.4, Z, 0.35, WOOD, verts=6)
    bx(p, (-21.8, -21.4), (8.2, 10.4), (Z - 0.15, Z + 0.15), DWOOD, 0.03)
    bx(p, (-21.8, -20.6), (8.1, 8.5), (Z - 0.18, Z + 0.18), DWOOD, 0.03)
    vcyl(p, X, 6.9, 10.3, Z, 0.11, TAN, verts=4, jit=0.02)
    lathe(p, X, Z, [(0, 5.0), (0.7, 5.0), (0.95, 5.8), (0.95, 6.5), (0, 6.5)], DWOOD, segs=8, jit=0.05)
    vcyl(p, X, 5.45, 5.6, Z, 1.0, IRON, verts=8, jit=0.02)
    tube(p, [(X - 0.9, 6.5, Z), (X, 7.5, Z), (X + 0.9, 6.5, Z)], 0.07, IRON, sides=4)
    gable_roof(p, -30.5, -21.5, Z, 11.3, 3.76, 2.64, (ROOFRED, (170, 82, 62), (196, 104, 78)), rows=3, thick=0.6)
    prism_x(p, [(11.3, Z - 3.76), (11.3, Z + 3.76), (13.9, Z)], -30.2, -29.6, WOOD, 0.03)
    prism_x(p, [(11.3, Z - 3.76), (11.3, Z + 3.76), (13.9, Z)], -22.4, -21.8, WOOD, 0.03)
    bx(p, (-30.5, -21.5), (13.7, 14.0), (Z - 0.3, Z + 0.3), DRED, 0.03)
    for (x, z) in ((-31.6, -28), (-20.6, -32.5), (-28.5, -35), (-23.5, -25.6)):
        tuft(p, x, z, 1.1, GRASS2, n=5, seed=int(abs(x + z)))
    for (x, z) in ((-30.5, -25.8), (-21.5, -34.2)):
        rock(p, x, 0, z, 1.8, 1.0, 1.6, STONE, seed=int(abs(x)))


# ---- 11. Cow --------------------------------------------------------------------------------------------------------------
def build_Cow(p):
    Z = -34
    blob(p, -6, 6.4, Z, 11, 5.4, 5.6, CREAM, sub=2, jit=0.03)
    blob(p, -8, 8.7, Z, 3.8, 1.7, 3.9, COWBROWN, sub=2, jit=0.04)
    blob(p, -3.2, 6.6, Z + 2.5, 3.2, 3.0, 1.2, COWBROWN, sub=2, jit=0.04)
    blob(p, -9.2, 6.0, Z - 2.6, 3.4, 3.0, 1.2, COWBROWN, sub=2, jit=0.04)
    blob(p, -8, 3.8, Z, 2.4, 1.5, 2.4, PINK, sub=2, jit=0.03)
    blob(p, -1.0, 7.4, Z, 3.6, 3.8, 3.8, CREAM, sub=2, jit=0.03)
    hexa(p, [(-0.4, 5.9, Z - 1.7), (3.2, 6.1, Z - 1.2), (3.2, 6.1, Z + 1.2), (-0.4, 5.9, Z + 1.7),
             (-0.4, 9.3, Z - 1.7), (3.2, 8.0, Z - 1.2), (3.2, 8.0, Z + 1.2), (-0.4, 9.3, Z + 1.7)], CREAM, 0.03)
    hexa(p, [(0.1, 8.6, Z - 1.72), (1.9, 8.1, Z - 1.3), (1.9, 8.1, Z + 0.4), (0.1, 8.6, Z + 0.4),
             (0.1, 9.32, Z - 1.72), (1.9, 8.35, Z - 1.3), (1.9, 8.35, Z + 0.4), (0.1, 9.32, Z + 0.4)], COWBROWN, 0.03)
    bx(p, (2.7, 4.1), (5.9, 7.7), (Z - 1.3, Z + 1.3), PINK, 0.03)
    for dz in (-0.5, 0.5):
        bx(p, (4.0, 4.14), (6.8, 7.1), (Z + dz - 0.12, Z + dz + 0.12), (150, 90, 90), 0.02)
    for dz in (-1.45, 1.45):
        bx(p, (2.2, 2.55), (8.2, 8.6), (Z + dz - 0.2, Z + dz + 0.2), BLACK, 0.02)
        bx(p, (0.3, 1.5), (8.9, 9.4), (Z + dz * 1.15 - 0.45, Z + dz * 1.15 + 0.45), CREAM, 0.03)
    for dz in (-1, 1):
        bx(p, (-0.15, 0.55), (9.0, 9.4), (Z + dz * 2.3 - 0.35, Z + dz * 2.3 + 0.35), COWBROWN, 0.03)
        dk.cyl(p, (1.6, 9.8, Z + dz * 1.8), 0.32, 1.0, WHITE, axis='y', verts=5, top_radius=0.12, jitter=0.03, rot=(dz * 12, 0, 0))
    bx(p, (-1.2, -0.8), (5.3, 9.2), (Z - 1.9, Z + 1.9), RED, 0.03)
    ball(p, (-0.7, 5.5, Z), 0.5, GOLD, subdiv=1)
    for lx in (-10.2, -1.8):
        for lz in (-2.4, 2.4):
            dk.cyl(p, (lx, 2.6, Z + lz), 0.98, 4.4, CREAM, axis='y', verts=6, top_radius=0.8, jitter=0.03)
            bx(p, (lx - 0.7, lx + 0.7), (0.0, 0.7), (Z + lz - 0.7, Z + lz + 0.7), (70, 60, 56), 0.03)
    tube(p, [(-11.4, 8.4, Z), (-12.0, 7.6, Z), (-12.2, 5.4, Z), (-12.0, 3.8, Z)], [0.3, 0.25, 0.22, 0.2], COWBROWN, sides=4)
    blob(p, -12.0, 3.4, Z, 0.9, 1.5, 0.9, (90, 60, 40), sub=1, jit=0.03)
    for (x, z) in ((-12, -38), (2, -31), (-8, -30.5), (4, -37)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 12. Footprints -------------------------------------------------------------------------------------------------------
def footprint(p, x, z):
    disc(p, x, 0.0, 0.42, z, 3.0, 4.9, DIRT, n=12)
    disc(p, x, 0.42, 0.5, z, 2.3, 4.2, DDIRT, n=12)
    disc(p, x + 0.4, 0.5, 0.54, z - 0.6, 1.1, 2.1, (120, 150, 170), n=10)
    disc(p, x, 0.0, 0.42, z + 5.6, 2.8, 1.8, DIRT, n=12)
    disc(p, x, 0.42, 0.5, z + 5.6, 2.1, 1.2, DDIRT, n=10)
    for (dx, dz, r) in ((-1.6, 7.3, 1.1), (0.2, 7.4, 0.8), (1.5, 7.1, 0.72), (2.7, 6.5, 0.66)):
        disc(p, x + dx, 0.0, 0.52, z + dz, r, r * 1.05, DDIRT, n=8)
        disc(p, x + dx, 0.5, 0.58, z + dz, r * 0.55, r * 0.55, DIRT, n=6)


def build_Footprints(p):
    footprint(p, 12, 8)
    footprint(p, 22, 22)
    footprint(p, 32, 36)
    for (x, z) in ((8, 6), (17, 4), (18, 24), (27.5, 20), (28, 38), (37.5, 34)):
        tuft(p, x, z, 0.55, GRASS2, n=4, spread=0.3, seed=int(x + z))


# ---- 13. Toadstools -------------------------------------------------------------------------------------------------------
def toadstool(p, x, z, r, h_stem, y_cap, cap_h, seed, spots_n=5):
    rs = max(0.7, r * 0.3)
    lathe(p, x, z, [(0, 0.0), (rs * 1.35, 0.0), (rs * 1.1, 0.5), (rs * 0.85, h_stem * 0.5), (rs * 0.75, y_cap + 0.4), (0, y_cap + 0.4)],
          CREAM, segs=8, jit=0.04)
    lathe(p, x, z, [(0, h_stem * 0.62), (rs * 1.7, h_stem * 0.6), (rs * 1.5, h_stem * 0.52), (0, h_stem * 0.5)], WHITE, segs=8, jit=0.03)
    prof = [(0, y_cap + 0.35), (r * 0.62, y_cap), (r, y_cap + cap_h * 0.18), (r * 0.9, y_cap + cap_h * 0.52), (r * 0.58, y_cap + cap_h * 0.82),
            (0, y_cap + cap_h)]
    lathe(p, x, z, prof, RED, segs=10, jit=0.05)

    def dome_y(rr):
        for i in range(len(prof) - 1):
            r0, y0 = prof[i]
            r1, y1 = prof[i + 1]
            if min(r0, r1) <= rr <= max(r0, r1) and abs(r1 - r0) > 1e-6 and y1 >= y0 + 0.01 and i >= 1:
                return y0 + (y1 - y0) * (rr - r0) / (r1 - r0)
        return y_cap + cap_h * 0.9
    spots(p, x, 0, z, dome_y, spots_n, r * 0.8, WHITE, seed=seed, size=max(0.5, r * 0.15))


def build_Toadstools(p):
    toadstool(p, -22, 20, 5.5, 6, 4, 6, 1, 7)
    toadstool(p, -14, 16, 4, 4.4, 3.4, 4.4, 2, 5)
    toadstool(p, -17, 24, 3, 3.2, 2.6, 3.4, 3, 4)
    for (x, z, r, s) in ((-26, 24.5, 1.2, 4), (-12, 20, 1.0, 5), (-20, 15, 0.9, 6)):
        toadstool(p, x, z, r, 1.4, 1.0, 1.1, s, 0)
    for (x, z) in ((-26, 17), (-17, 19.5), (-10, 12), (-24, 26.5), (-12, 25)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 14. Scarecrow --------------------------------------------------------------------------------------------------------
def build_Scarecrow(p):
    X, Z = 82, -28
    disc(p, X, 0.0, 1.0, Z, 2.5, 2.5, DIRT, n=10)
    vcyl(p, X, 0.6, 14.0, Z, 0.6, DWOOD, verts=6)
    xcyl(p, 76, 88, 9.4, Z, 0.5, DWOOD, verts=6)
    bx(p, (80, 84), (6.1, 10.7), (Z - 1.1, Z + 1.1), SLATEBLUE, 0.04)
    for k in range(3):
        bx(p, (80.4 + k * 1.3, 80.9 + k * 1.3), (6.1, 10.7), (Z + 1.05, Z + 1.15), (130, 160, 222), 0.02)
    for sx in (-1, 1):
        a, b = (77.2, 80.0) if sx < 0 else (84.0, 86.8)
        bx(p, (a, b), (8.7, 10.1), (Z - 0.9, Z + 0.9), SLATEBLUE, 0.04)
        blob(p, 76.6 if sx < 0 else 87.4, 9.4, Z, 1.8, 1.6, 1.8, HAY, sub=1, jit=0.04)
        for k in range(4):
            dz = (k - 1.5) * 0.45
            bx(p, ((75.6, 76.9)[0] if sx < 0 else 87.3, (76.9 if sx < 0 else 88.4)), (9.2 + 0.05 * k, 9.3 + 0.05 * k), (Z + dz - 0.06, Z + dz + 0.06), DHAY, 0.02)
    blob(p, X, 5.6, Z, 4.4, 2.0, 2.8, HAY, sub=1, jit=0.05)
    for k in range(7):
        a = k * 0.9
        bx(p, (X - 2 + k * 0.62, X - 1.8 + k * 0.62), (4.4, 5.8), (Z + 0.3 * math.sin(a) - 0.1, Z + 0.3 * math.sin(a) + 0.1), DHAY if k % 2 else HAY, 0.02)
    blob(p, X, 12.6, Z, 3.8, 3.8, 3.8, TAN, sub=2, jit=0.04)
    for dx in (-0.8, 0.8):
        dk.cyl(p, (X + dx, 12.9, Z + 1.88), 0.32, 0.2, BLACK, axis='z', verts=6, jitter=0.02)
    dk.cyl(p, (X, 12.3, Z + 2.3), 0.35, 1.0, ORANGE, axis='z', verts=6, top_radius=0.05, jitter=0.03)
    for k in range(4):
        bx(p, (X - 1.0 + k * 0.55, X - 0.75 + k * 0.55), (11.2 + 0.1 * (k % 2), 11.45 + 0.1 * (k % 2)), (Z + 1.8, Z + 1.95), BLACK, 0.02)
    vcyl(p, X, 14.0, 14.4, Z, 2.7, DWOOD, verts=10, jit=0.03)
    vcyl(p, X, 14.4, 16.5, Z, 1.6, DWOOD, verts=10, top_r=1.15, jit=0.03)
    vcyl(p, X, 14.5, 15.1, Z, 1.72, RED, verts=10, jit=0.02)
    blob(p, X + 1.2, 15.2, Z + 1.5, 0.9, 0.9, 0.5, GOLD, sub=1, jit=0.02)
    blob(p, 86.4, 10.8, Z, 1.6, 1.4, 2.4, BLACK, sub=1, jit=0.03)
    blob(p, 86.4, 11.5, Z + 1.3, 1.0, 1.0, 1.0, BLACK, sub=1, jit=0.03)
    dk.cyl(p, (86.4, 11.5, Z + 2.1), 0.2, 0.7, ORANGE, axis='z', verts=4, top_radius=0.02, jitter=0.02)
    bx(p, (86.1, 86.7), (10.6, 10.8), (Z - 2.0, Z - 1.1), BLACK, 0.02)
    for (x, z) in ((78.5, -26), (85.5, -30.5), (80, -30.6)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(x))


# ---- 15. Boots ------------------------------------------------------------------------------------------------------------
def boot(p, cx, z):
    LB = (122, 80, 52)
    # sole and heel
    bx(p, (cx - 6.8, cx + 6.8), (0, 1.0), (z - 3.1, z + 3.1), DWOOD, 0.04)
    bx(p, (cx - 6.8, cx - 4.0), (0, 1.8), (z - 2.9, z + 2.9), (78, 52, 34), 0.03)
    # rounded foot: long ellipsoid plus a toe cap
    blob(p, cx - 0.2, 3.3, z, 13.0, 5.4, 5.8, BROWN, sub=2, jit=0.04)
    blob(p, cx + 4.6, 2.9, z, 4.0, 3.6, 5.2, LB, sub=2, jit=0.04)
    # tapered round shaft
    lathe(p, cx - 3.0, z, [(0, 4.5), (3.0, 4.5), (2.9, 8.0), (2.85, 12.0), (3.05, 14.4), (0, 14.4)], BROWN, segs=10, jit=0.05, sz=0.92)
    # folded cuff with dark opening
    lathe(p, cx - 3.0, z, [(0, 14.2), (3.5, 14.2), (3.5, 15.7), (2.7, 15.7), (2.6, 15.1), (0, 15.1)], LWOOD, segs=10, jit=0.04, sz=0.92)
    lathe(p, cx - 3.0, z, [(0, 15.05), (2.55, 15.05), (2.55, 15.2), (0, 15.2)], (50, 34, 26), segs=10, jit=0.02, sz=0.92)
    # tongue and laces down the front of the shaft
    bx(p, (cx - 0.25, cx + 0.35), (5.0, 14.4), (z - 0.8, z + 0.8), LWOOD, 0.03)
    for k in range(6):
        y = 6.0 + k * 1.4
        bx(p, (cx - 0.1, cx + 0.5), (y - 0.1, y + 0.1), (z - 1.4, z + 1.4), TAN, 0.02)
        for sz in (-1.4, 1.4):
            bx(p, (cx - 0.1, cx + 0.5), (y - 0.18, y + 0.18), (z + sz - 0.18, z + sz + 0.18), IRON, 0.02)
    # seam stitching and mud splashes
    for zz in (z - 2.5, z + 2.5):
        bx(p, (cx - 3.1, cx - 2.9), (6.0, 14.0), (zz - 0.1, zz + 0.1), (92, 60, 40), 0.02)
    blob(p, cx + 5.8, 1.1, z + 2.7, 1.8, 0.8, 0.8, (96, 72, 50), sub=1, jit=0.03)
    blob(p, cx - 5.6, 3.0, z - 2.8, 1.6, 1.4, 0.8, (96, 72, 50), sub=1, jit=0.03)
    blob(p, cx + 1.0, 0.7, z + 3.0, 2.2, 0.8, 0.9, (96, 72, 50), sub=1, jit=0.03)


def build_Boots(p):
    boot(p, -5, -27.5)
    boot(p, -3.5, -20.5)
    for (x, z) in ((-13, -24), (4, -24.5), (-9, -17), (2, -16)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 16. Cauldron ---------------------------------------------------------------------------------------------------------
def build_Cauldron(p):
    X, Z = 14, -48
    for ang, c in ((0, DWOOD), (60, WOOD), (-60, DWOOD)):
        dx, dz = ry(5.0, 0, ang)
        dk.cyl(p, (X, 0.8, Z + 1.0), 0.8, 10, c, axis='x', verts=6, rot=(0, ang, 0), jitter=0.05)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        lx, lz = X + 4.9 * math.cos(a), Z + 4.9 * math.sin(a)
        dk.cyl(p, (lx, 0.8, lz), 0.95, 1.6, IRON, axis='y', verts=6, top_radius=0.55, jitter=0.04)
    # flames licking round the belly
    for k, (c, r) in enumerate(((ORANGE, 1.3), (FLAME, 1.0), (RED, 1.2), (ORANGE, 1.0), (FLAME, 0.9), (RED, 1.1), (ORANGE, 0.9))):
        a = math.radians(40 + 52 * k)
        blob(p, X + 3.2 * math.cos(a), 0.6, Z + 3.0 * math.sin(a), r * 2, 0.9, r * 2, c, sub=1, jit=0.05)
    for (dx, dz, h, c) in ((0.0, 5.4, 1.4, FLAME), (-1.2, 5.6, 1.0, ORANGE), (1.3, 5.5, 1.1, ORANGE)):
        cone(p, (X + dx, 0.3, Z + dz), 0.7, h, c, verts=4, jitter=0.05)
    prof = [(0, 1.5), (3.0, 1.5), (5.2, 2.3), (6.4, 4.4), (6.5, 6.4), (5.9, 8.6), (6.4, 9.3), (6.4, 9.9), (5.5, 9.9), (5.5, 9.15), (0, 9.15)]
    lathe(p, X, Z, prof, IRON, segs=14, jit=0.04)
    vcyl(p, X, 9.2, 9.9, Z, 6.45, (62, 66, 76), verts=14, jit=0.03) if False else None
    disc(p, X, 9.1, 9.4, Z, 5.45, 5.45, LBEAN, n=14)
    for (dx, dz, r, c) in ((-2.0, 1.0, 0.9, (190, 232, 130)), (1.5, -2.2, 0.7, (190, 232, 130)), (2.8, 1.8, 0.6, LBEAN), (-1.0, -3.0, 0.5, LBEAN)):
        blob(p, X + dx, 9.45, Z + dz, r * 2, r * 1.3, r * 2, c, sub=2, jit=0.04)
    for sx in (-1, 1):
        bx(p, (X + sx * 6.5 - 0.55, X + sx * 6.5 + 0.55), (8.0, 9.4), (Z - 0.6, Z + 0.6), (62, 66, 76), 0.03)
    # bail handle
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        pts.append((X + 6.5 * math.cos(a), 9.0 + 4.0 * math.sin(a), Z))
    tube(p, pts, 0.28, (62, 66, 76), sides=5)
    # ladle
    bar(p, (17.3, 9.4, -45), (19.9, 15.0, -45), 0.5, WOOD, 0.04)
    lathe(p, 17.0, -45, [(0, 8.8), (0.9, 9.0), (1.2, 9.6), (1.15, 10.0), (0, 9.8)], LIRON, segs=8, jit=0.04)
    blob(p, 19.6, 9.9, -45, 2, 1, 2, (190, 232, 130), sub=1, jit=0.04)


# ---- 17. Harp -------------------------------------------------------------------------------------------------------------
def build_Harp(p):
    cz = -20
    for i in range(2):
        for j in range(2):
            bx(p, (-70 + i * 5 + 0.06, -65 + i * 5 - 0.06), (0, 0.6), (-23 + j * 3 + 0.06, -20 + j * 3 - 0.06), STONE if (i + j) % 2 else DSTONE, 0.05)
    bx(p, (-70, -62), (0.6, 1.5), (cz - 2.2, cz + 2.2), DGOLD, 0.04)
    bx(p, (-69.8, -62.2), (1.5, 1.8), (cz - 1.9, cz + 1.9), GOLD, 0.04)
    # pillar: fluted column with base and capital
    vcyl(p, -69, 1.8, 13.4, cz, 0.72, GOLD, verts=8, jit=0.05)
    bx(p, (-69.9, -68.1), (1.5, 2.6), (cz - 0.9, cz + 0.9), DGOLD, 0.03)
    bx(p, (-69.8, -68.2), (12.8, 13.8), (cz - 0.8, cz + 0.8), DGOLD, 0.03)
    ball(p, (-69, 14.4, cz), 1.0, GOLD, subdiv=1)
    # soundbox on the right, leaning a little
    pts = [(-63.2, 0.8, cz - 1.1), (-61.4, 0.8, cz - 1.1), (-61.4, 0.8, cz + 1.1), (-63.2, 0.8, cz + 1.1),
           (-61.4, 13.2, cz - 0.8), (-59.9, 13.2, cz - 0.8), (-59.9, 13.2, cz + 0.8), (-61.4, 13.2, cz + 0.8)]
    hexa(p, pts, DGOLD, 0.04)
    for k in range(4):
        y = 2.5 + k * 2.6
        f = y / 13.2
        dk.box(p, (-61.4 + 1.2 * f - 0.05 + 0.8 * (1 - f) * 0.0, y, cz + 1.05 - 0.2 * f), (1.2 - 0.3 * f, 0.7, 0.2), LGOLD, jitter=0.03)
    for k in range(3):
        y = 4.0 + k * 3.0
        f = y / 13.2
        dk.cyl(p, (-62.3 + 2.0 * f, y, cz + 1.25 - 0.2 * f), 0.32, 0.2, (150, 100, 30), axis='z', verts=6, jitter=0.02)
    # curved neck from the pillar to the soundbox
    neck = []
    for i in range(11):
        t = i / 10
        neck.append((-69 + 8.1 * t, 13.4 + 1.0 * math.sin(math.pi * t) - 0.6 * t, cz))
    tube(p, neck, [0.78 - 0.18 * i / 10 for i in range(11)], GOLD, sides=6, jit=0.04)
    # bottom rail and strings
    bar(p, (-69, 2.4, cz), (-62.6, 2.4, cz), 0.55, DGOLD, 0.03)
    for k in range(9):
        t = (k + 0.7) / 9.6
        x = -69 + 7.2 * t
        ytop = 13.4 + 1.0 * math.sin(math.pi * t * 0.95) - 0.6 * t - 0.5
        bar(p, (x, 2.5, cz), (x, ytop, cz), 0.14, WHITE if k % 2 else (236, 236, 224), 0.02)
    for x in (-62.7, -66.0):
        pass
    star_poly(p, (-65.3, 15.0, cz + 0.4), 'xy', 0.8, 0.25, 0.1, LGOLD, n=4)
    star_poly(p, (-61.5, 14.2, cz + 0.4), 'xy', 0.6, 0.2, 0.1, LGOLD, n=4)
    for (x, z) in ((-70.6, -17.2), (-59.6, -22.4), (-64, -16.2)):
        tuft(p, x, z, 1.0, GRASS2, n=4, seed=int(abs(x)))


# ---- 18. GoldHoard --------------------------------------------------------------------------------------------------------
def build_GoldHoard(p):
    blob(p, 82, 2.8, 6, 13, 5.6, 11, GOLD, sub=2, jit=0.1)
    blob(p, 79, 2.0, 2, 8, 4, 7, LGOLD, sub=2, jit=0.1)
    blob(p, 86, 1.8, 9, 7, 3.6, 6, GOLD, sub=2, jit=0.1)
    rng = random.Random(8)
    for k in range(9):
        x, z = 77.5 + rng.random() * 9.5, 0.8 + rng.random() * 10
        y = 3.2 + rng.random() * 2.2 if 79 < x < 85 and 2 < z < 10 else 2.2 + rng.random() * 1.2
        c = (GOLD, LGOLD, DGOLD)[k % 3]
        dk.cyl(p, (x, y, z), 1.0 + rng.random() * 0.4, 0.28, c, axis='y', verts=7, rot=(rng.random() * 50 - 25, 0, rng.random() * 50 - 25), jitter=0.04)
    # two big coins on edge
    for (x, y, z, c) in ((84.6, 5.6, 5.0, GOLD), (79.6, 5.8, 4.8, LGOLD)):
        zcyl(p, x, y, z - 0.3, z + 0.3, 1.7, DGOLD, verts=10, jit=0.03)
        zcyl(p, x, y, z - 0.32, z + 0.34, 1.35, c, verts=10, jit=0.03)
    # open chest
    bx(p, (73.2, 78.8), (0, 4.2), (9.6, 13.2), WOOD, 0.05)
    for x in (73.4, 78.4):
        bx(p, (x - 0.1, x + 0.5), (0, 4.3), (9.55, 13.25), IRON, 0.03)
    bx(p, (73.2, 78.8), (2.3, 2.7), (13.15, 13.3), IRON, 0.03)
    bx(p, (75.5, 76.5), (2.2, 3.3), (13.15, 13.35), GOLD, 0.03)
    dk.box(p, (76, 5.7, 8.5), (5.6, 0.6, 3.6), DWOOD, rot=(-110, 0, 0), jitter=0.05)
    dk.box(p, (76, 5.9, 8.3), (5.7, 0.7, 0.5), IRON, rot=(-110, 0, 0), jitter=0.03)
    blob(p, 76, 4.3, 11.4, 5.0, 1.6, 3.2, GOLD, sub=2, jit=0.1)
    for k in range(5):
        dk.cyl(p, (74.5 + k * 0.9, 5.0, 10.8 + (k % 2) * 0.8), 0.7, 0.2, LGOLD, axis='y', verts=6, rot=(15 * (k % 3 - 1), 0, 20 * (k % 2)), jitter=0.04)
    # gems, crown and ingots
    gem(p, 84.6, 4.6, 9.2, 1.1, 0.9, 0.8, RED)
    gem(p, 79.4, 5.1, 8.6, 1.0, 0.9, 0.8, WATER)
    gem(p, 82.4, 5.3, 6.0, 1.0, 0.9, 0.8, LBEAN)
    lathe(p, 81, 7.3, [(0, 4.9), (1.5, 4.9), (1.6, 6.0), (1.4, 6.0), (0, 5.8)], DGOLD, segs=8, jit=0.03) if False else None
    vcyl(p, 81.6, 4.6, 6.0, 7.4, 1.6, DGOLD, verts=8, jit=0.03)
    vcyl(p, 81.6, 4.7, 5.9, 7.4, 1.7, GOLD, verts=8, jit=0.03)
    for k in range(6):
        a = 2 * math.pi * k / 6
        cone(p, (81.6 + 1.45 * math.cos(a), 5.9, 7.4 + 1.45 * math.sin(a)), 0.55, 1.5, GOLD, verts=4, jitter=0.03)
        ball(p, (81.6 + 1.45 * math.cos(a), 7.5, 7.4 + 1.45 * math.sin(a)), 0.22, RED, subdiv=1)
    ingot(p, 86.6, 0, 3.0, 2.6, 1.0, 1.3, GOLD, yaw=8)
    ingot(p, 86.4, 0, 4.6, 2.6, 1.0, 1.3, LGOLD, yaw=-6)
    ingot(p, 86.5, 1.0, 3.8, 2.6, 1.0, 1.3, GOLD, yaw=2)


# ---- 19. Dolmen -----------------------------------------------------------------------------------------------------------
def build_Dolmen(p):
    for i in range(2):
        for j in range(2):
            bx(p, (27 + i * 9 + 0.1, 36 + i * 9 - 0.1), (0.1, 0.6), (48 + j * 6 + 0.1, 54 + j * 6 - 0.1), DSTONE if (i + j) % 2 else (124, 126, 134), 0.05)
    stone(p, 30, 0, 54, 3.6, 11.6, 5.6, STONE, seed=3, jit=0.13, taper=0.85, rough=0.2)
    stone(p, 42, 0, 54, 3.6, 11.6, 5.6, STONE, seed=4, jit=0.13, taper=0.85, rough=0.2)
    stone(p, 36, 0, 56.6, 8, 9.2, 2.6, DSTONE, seed=5, jit=0.13, taper=0.8, rough=0.2)
    stone(p, 36, 11.3, 54, 16, 3.0, 8.4, LSTONE, seed=6, jit=0.13, taper=0.85, rough=0.14)
    blob(p, 36, 14.45, 54, 9, 0.6, 5, LMOSS, sub=2, jit=0.07)
    tube(p, [(40.6, 0.3, 57.0), (41.3, 3, 57.0), (40.8, 6, 57.0), (41.6, 9, 57.0), (41.0, 11.4, 57.0)], [0.26, 0.24, 0.22, 0.2, 0.16], LBEAN, sides=4)
    blade(p, (41.3, 3.2, 57.0), 340, 2.2, 1.2, 20, BEAN, None, n=4, droop=0.3)
    blade(p, (40.8, 6.2, 57.0), 200, 2.2, 1.2, 20, BEAN, None, n=4, droop=0.3)
    blade(p, (41.6, 9.2, 57.0), 350, 2.0, 1.1, 20, BEAN, None, n=4, droop=0.3)
    for (x, y, z, sx, sy) in ((33.4, 5.0, 57.95, 1.6, 1.0), (38.6, 7.4, 57.95, 1.4, 0.8), (36, 3.2, 57.95, 2.4, 1.0), (34.5, 8.2, 57.95, 1.2, 0.7)):
        blob(p, x, y, z, sx, sy, 0.3, (186, 192, 120), sub=1, jit=0.06)
    for y in (2.5, 4.5, 6.5, 8.0):
        bx(p, (33.0, 36.4 + 0.3 * (y % 3)), (y, y + 0.2), (57.85, 58.05), (80, 82, 92), 0.02)
    bx(p, (36.8, 37.0), (3.0, 8.0), (57.85, 58.05), (80, 82, 92), 0.02)
    stone(p, 26.4, 0, 50.4, 2.4, 3.2, 2.2, STONE, seed=7, taper=0.8)
    stone(p, 45.6, 0, 57.6, 2.4, 2.4, 2.2, STONE, seed=8, taper=0.8)
    for x in (30, 42):
        blob(p, x, 0.5, 51.4, 3.8, 1.2, 1.4, MOSS, sub=1, jit=0.05)
        for k in range(3):
            bx(p, (x - 1.0 + k * 0.7, x - 0.8 + k * 0.7), (3.5 + k * 1.2, 4.7 + k * 1.2), (51.1, 51.25), (84, 86, 94), 0.02)
    blob(p, 36, 12.8, 49.7, 6, 1.0, 0.8, MOSS, sub=1, jit=0.05)
    for (x, z, c) in ((33, 49, WHITE), (39, 48.6, SUN), (28, 49.4, PINK), (44, 50, WHITE)):
        vcyl(p, x, 0.3, 1.5, z, 0.07, GRASS2, verts=3)
        blob(p, x, 1.65, z, 0.7, 0.4, 0.7, c, sub=1, jit=0.02)
    for (x, z) in ((27, 47.8), (36, 47.8), (45, 48.6), (47, 59)):
        tuft(p, x, z, 1.1, GRASS2, n=5, seed=int(x))


# ---- 20. Obelisk ----------------------------------------------------------------------------------------------------------
def build_Obelisk(p):
    X, Z = -38, 4
    bx(p, (X - 5, X + 5), (0, 1.6), (Z - 5, Z + 5), STONE, 0.05)
    bx(p, (X - 3.8, X + 3.8), (1.6, 3.2), (Z - 3.8, Z + 3.8), LSTONE, 0.05)
    y0, y1, w0, w1 = 3.2, 26.8, 2.5, 1.7
    pts = [(X - w0, y0, Z - w0), (X + w0, y0, Z - w0), (X + w0, y0, Z + w0), (X - w0, y0, Z + w0),
           (X - w1, y1, Z - w1), (X + w1, y1, Z - w1), (X + w1, y1, Z + w1), (X - w1, y1, Z + w1)]
    hexa(p, pts, (138, 140, 150), 0.05)

    def hw(y):
        return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    for y, c in ((8.0, LBEAN), (14.0, WATER), (20.0, LBEAN)):
        h = hw(y) + 0.1
        bx(p, (X - h, X + h), (y - 0.3, y + 0.3), (Z - h, Z + h), c, 0.03)
    # carved runes on the four faces, pale blue
    RUNE = (150, 212, 252)

    def mark(face, ym, u, wu, hy, ang, nrm):
        if face in (0, 2):
            dk.box(p, (X + u, ym, Z + (nrm if face == 0 else -nrm)), (wu, hy, 0.26), RUNE, rot=(0, 0, ang), jitter=0.02)
        else:
            dk.box(p, (X + (nrm if face == 1 else -nrm), ym, Z + u), (0.26, hy, wu), RUNE, rot=(ang, 0, 0), jitter=0.02)
    for face in range(4):
        for k, (ya, yb) in enumerate(((5.0, 7.2), (9.5, 12.5), (15.5, 19.0), (21.0, 25.0))):
            ym = (ya + yb) / 2
            nrm = hw(ym) + 0.02
            ln = yb - ya
            kind = (face + k) % 4
            if kind == 0:      # H
                mark(face, ym, -0.7, 0.2, ln, 0, nrm)
                mark(face, ym, 0.7, 0.2, ln, 0, nrm)
                mark(face, ym, 0.0, 1.5, 0.2, 0, nrm)
            elif kind == 1:    # X
                mark(face, ym, 0.0, 0.2, ln * 1.15, 32, nrm)
                mark(face, ym, 0.0, 0.2, ln * 1.15, -32, nrm)
            elif kind == 2:    # bar with three dots
                mark(face, ym, 0.0, 0.22, ln, 0, nrm)
                for d in (-0.9, 0.0, 0.9):
                    mark(face, ym + d * ln * 0.3, 0.8, 0.35, 0.35, 0, nrm)
                    mark(face, ym + d * ln * 0.3, -0.8, 0.35, 0.35, 0, nrm)
            else:              # Y shape
                mark(face, ym - ln * 0.2, 0.0, 0.22, ln * 0.6, 0, nrm)
                mark(face, ym + ln * 0.22, -0.4, 0.2, ln * 0.55, 28, nrm)
                mark(face, ym + ln * 0.22, 0.4, 0.2, ln * 0.55, -28, nrm)
    dk.cyl(p, (X, 26.8 + 1.4, Z), 2.45, 2.8, GOLD, axis='y', verts=4, top_radius=0.02, rot=(0, 45, 0), jitter=0.04)
    for (dx, dz, s) in ((-4.2, -4.2, 1.6), (4.2, 3.8, 1.3), (4.4, -4.0, 1.0), (-4.0, 4.2, 1.2)):
        blob(p, X + dx, 0.9, Z + dz, s * 1.6, 1.2, s * 1.6, MOSS, sub=1, jit=0.05)
    blob(p, X, 3.3, Z + 3.7, 5.8, 0.5, 1.0, MOSS, sub=1, jit=0.05)
    for (dx, dz) in ((-6, -2), (6, 3), (-2, 6), (3, -6)):
        tuft(p, X + dx, Z + dz, 1.2, GRASS2, n=5, seed=int(abs(dx * dz) + 1))


# ---- 21. Table ------------------------------------------------------------------------------------------------------------
def build_Table(p):
    X, Z = -62, -52
    for k in range(4):
        z0 = -59 + k * 3.5
        bx(p, (X - 12, X + 12), (12.4, 14.0), (z0 + 0.04, z0 + 3.46), (WOOD, LWOOD, (170, 120, 76), WOOD)[k], 0.05)
    bx(p, (X - 11.5, X - 10.7), (12.0, 12.4), (-58.6, -45.4), DWOOD, 0.04)
    bx(p, (X + 10.7, X + 11.5), (12.0, 12.4), (-58.6, -45.4), DWOOD, 0.04)
    for (lx, lz) in ((-72.4, -57.2), (-51.6, -57.2), (-72.4, -46.8), (-51.6, -46.8)):
        lathe(p, lx, lz, [(0, 0.0), (1.25, 0.0), (1.0, 0.8), (0.95, 2.4), (1.25, 3.4), (1.25, 4.2), (0.9, 5.2), (0.85, 8.0), (1.15, 9.0), (1.15, 10.0),
                          (1.25, 10.6), (1.25, 12.4), (0, 12.4)], DWOOD, segs=8, jit=0.05)
    bar(p, (-72.4, 3.4, -46.8), (-51.6, 3.4, -46.8), 1.0, DWOOD, 0.04)
    bar(p, (-72.4, 3.4, -57.2), (-51.6, 3.4, -57.2), 1.0, DWOOD, 0.04)
    bar(p, (-72.4, 3.4, -57.2), (-72.4, 3.4, -46.8), 1.0, DWOOD, 0.04)
    bar(p, (-51.6, 3.4, -57.2), (-51.6, 3.4, -46.8), 1.0, DWOOD, 0.04)
    # runner cloth with white trim and gold tassels
    bx(p, (X - 12.2, X + 12.2), (14.0, 14.2), (-54.5, -49.5), RED, 0.03)
    for z in (-54.4, -49.7):
        bx(p, (X - 12.2, X + 12.2), (14.2, 14.26), (z - 0.1, z + 0.1), WHITE, 0.02)
    for sx in (-1, 1):
        for k in range(5):
            bx(p, (X + sx * 12.15 - 0.15, X + sx * 12.15 + 0.15), (13.3, 14.0), (-54.2 + k * 1.1, -53.9 + k * 1.1), GOLD, 0.03)
    # plate, cheese, goblet, loaf
    lathe(p, -66, -52, [(0, 14.2), (2.0, 14.2), (3.5, 14.9), (3.1, 14.9), (2.0, 14.5), (0, 14.5)], WHITE, segs=12, jit=0.03)
    cx, cz = -66, -52
    pts = [(cx - 2.0, 14.85, cz - 1.8), (cx + 2.0, 14.85, cz - 1.8), (cx + 2.0, 14.85, cz + 1.8),
           (cx - 2.0, 17.5, cz - 1.8), (cx + 2.0, 17.5, cz - 1.8), (cx + 2.0, 17.5, cz + 1.8)]
    dk.poly(p, (0, 0, 0), pts, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], (252, 214, 90), 0.04)
    for (dx, dy, r) in ((-1.0, 16.2, 0.45), (0.5, 15.5, 0.35), (1.2, 16.9, 0.3)):
        dk.cyl(p, (cx + dx, dy, cz - 1.82), r, 0.1, (214, 170, 50), axis='z', verts=6, jitter=0.02)
    lathe(p, -55, -50, [(0, 14.2), (1.1, 14.2), (0.4, 15.0), (0.35, 16.0), (1.2, 16.9), (1.4, 17.9), (1.15, 17.9), (1.15, 17.4), (0, 17.4)], GOLD,
          segs=10, jit=0.03)
    disc(p, -55, 17.35, 17.5, -50, 1.12, 1.12, DRED, n=10)
    blob(p, -58.4, 15.6, -55, 5, 2.8, 3, TAN, sub=2, jit=0.05)
    for k in range(3):
        dk.box(p, (-60.0 + k * 1.6, 17.0, -55), (0.2, 0.15, 2.0), DTAN, rot=(0, 30, 0), jitter=0.02)
    # candle in a gold holder with a small flame
    vcyl(p, -70, 14.2, 14.7, -49, 0.9, DGOLD, verts=8)
    vcyl(p, -70, 14.7, 16.8, -49, 0.45, CREAM, verts=8)
    cone(p, (-70, 16.8, -49), 0.3, 0.9, FLAME, verts=5, jitter=0.03)
    for (x, z) in ((-76.5, -50), (-47.5, -55), (-62, -62)):
        tuft(p, x, z, 1.3, GRASS2, n=5, seed=int(abs(x)))


# ---- 22. StandingStones ---------------------------------------------------------------------------------------------------
STONE_SPOTS = [(-38.14, 33.74, -112.5, 13), (-46.26, 41.86, -157.5, 14), (-57.74, 41.86, 157.5, 14), (-65.86, 33.74, 112.5, 14),
               (-65.86, 22.26, 67.5, 15), (-57.74, 14.14, 22.5, 13), (-46.26, 14.14, -22.5, 14), (-38.14, 22.26, -67.5, 14)]


def build_StandingStones(p):
    cx, cz = -52, 28
    for k, (x, z, yaw, h) in enumerate(STONE_SPOTS):
        stone(p, x, 0, z, 5, h, 3.4, (STONE, DSTONE, (136, 138, 146), STONE)[k % 4], yaw=yaw, seed=20 + k, taper=0.8, rough=0.1)
        blob(p, x, 0.6, z, 5.8, 1.5, 4.2, MOSS, sub=1, jit=0.05)
        # carved marks on the face that looks to the middle
        inward = Vector((cx - x, cz - z)).normalized()
        a = math.radians(yaw)
        sgn = 1 if (math.sin(a) * inward.x + math.cos(a) * inward.y) > 0 else -1
        for j in range(3):
            ya = 2.4 + j * 2.6
            lbox(p, x, z, yaw, -0.5 + 0.5 * j, ya + 0.6, sgn * (1.7 * 0.84 + 0.05), 0.22, 1.0, 0.12, (84, 86, 94), 0.02)
            lbox(p, x, z, yaw, 0.3 + 0.2 * j, ya + 0.3, sgn * (1.7 * 0.84 + 0.05), 1.0, 0.2, 0.12, (84, 86, 94), 0.02)
    for (x, z, yaw) in ((-61.8, 37.8, 135), (-42.2, 18.2, -45)):
        stone(p, x, 13.4, z, 13.6, 2.4, 3.4, LSTONE, yaw=yaw, seed=int(abs(x)), taper=0.95, rough=0.05)
        blob(p, x, 15.8, z, 8, 0.6, 2.6, LMOSS, sub=1, jit=0.05)
    # rune slab in the middle
    bx(p, (-56.5, -47.5), (0.3, 0.6), (23.5, 32.5), DSTONE, 0.04)
    disc(p, -52, 0.6, 0.64, 28, 3.7, 3.7, (170, 172, 178), n=16)
    disc(p, -52, 0.64, 0.68, 28, 3.2, 3.2, DSTONE, n=16)
    star_poly(p, (-52, 0.7, 28), 'xz', 2.9, 1.2, 0.05, (150, 212, 252), n=6, rot0=90)
    for (x, z) in ((-52, 24), (-49, 31), (-56, 31), (-57, 26)):
        tuft(p, x, z, 0.5, GRASS2, n=3, spread=0.25, seed=int(abs(x + z)))
    for (x, z) in ((-72, 28), (-52, 50.5), (-33, 28), (-52, 7)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 23. GiantStool -------------------------------------------------------------------------------------------------------
def build_GiantStool(p):
    X, Z = 70, 24
    lathe(p, X, Z, [(0, 13.2), (8.6, 13.2), (9.5, 13.7), (9.5, 15.3), (9.0, 16.0), (0, 16.0)], WOOD, segs=16, jit=0.05)
    lathe(p, X, Z, [(0, 14.1), (9.58, 14.1), (9.58, 14.7), (0, 14.7)], DWOOD, segs=16, jit=0.03)
    lathe(p, X, Z, [(0, 15.6), (5.0, 15.7), (6.0, 16.5), (5.5, 17.3), (3.0, 17.7), (0, 17.7)], RED, segs=12, jit=0.04)
    torus(p, (X, 16.3, Z), 5.9, 0.3, GOLD, segs=16, sides=4, jit=0.02)
    ball(p, (X, 17.7, Z), 0.55, GOLD, subdiv=1)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        tx, tz = X + 5.5 * math.cos(a), Z + 5.5 * math.sin(a)
        blob(p, tx, 15.8, tz, 1.1, 0.9, 1.1, GOLD, sub=1, jit=0.03)
        vcyl(p, tx, 14.9, 15.5, tz, 0.15, GOLD, verts=4)
    legs = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        top = (X + 6.2 * math.cos(a), 13.4, Z + 6.2 * math.sin(a))
        bot = (X + 7.4 * math.cos(a), 0.0, Z + 7.4 * math.sin(a))
        mid = (X + 6.8 * math.cos(a), 6.7, Z + 6.8 * math.sin(a))
        tube(p, [bot, (bot[0], 0.9, bot[2]), mid, top], [1.45, 1.2, 1.1, 1.5], DWOOD, sides=8, rib=0.1, ribs=4)
        legs.append(mid)
        blob(p, mid[0] + 0.5 * math.cos(a), 8.2, mid[2] + 0.5 * math.sin(a), 0.9, 1.6, 0.9, (70, 46, 30), sub=1, jit=0.03)
    for i in range(3):
        a, b = legs[i], legs[(i + 1) % 3]
        bar(p, (a[0], 5.0, a[2]), (b[0], 5.0, b[2]), 0.8, WOOD, 0.04)
    for k in range(3):
        a = math.radians(90 + 120 * k + 60)
        tuft(p, X + 8.4 * math.cos(a), Z + 8.4 * math.sin(a), 1.4, GRASS2, n=5, seed=k)


# ---- 24. GiantClub --------------------------------------------------------------------------------------------------------
def build_GiantClub(p):
    X, Z = 62, -4
    disc(p, X, 0.3, 0.5, Z, 9, 9, DDIRT, n=16)
    disc(p, X, 0.3, 0.56, Z, 6, 6, (92, 66, 46), n=14)
    for k in range(8):
        a = math.radians(20 + 45 * k)
        dk.box(p, (X + 6.2 * math.cos(a), 0.4, Z - 6.2 * math.sin(a)), (5.0, 0.12, 0.3), (70, 50, 36), rot=(0, math.degrees(a), 0), jitter=0.02)
    rock(p, 57, 0, -1, 4, 2.4, 3.6, STONE, seed=31)
    rock(p, 67, 0, -7, 3.6, 2.0, 3.4, STONE, seed=32)
    rock(p, 58.5, 0, -8.5, 2.2, 1.2, 2.0, DSTONE, seed=33)
    rock(p, 66.5, 0, 1.0, 2.0, 1.1, 1.8, STONE, seed=34)
    lathe(p, X, Z, [(0, 0.0), (1.55, 0.0), (1.5, 8.0), (1.6, 14.0), (0, 14.0)], WOOD, segs=10, jit=0.05)
    for k in range(5):
        lathe(p, X, Z, [(0, 5.4 + k * 1.6), (1.72, 5.4 + k * 1.6), (1.72, 6.2 + k * 1.6), (0, 6.2 + k * 1.6)], TAN if k % 2 else DWOOD, segs=10, jit=0.03)
    prof = [(1.5, 14.0), (2.1, 16.0), (3.0, 20.0), (4.0, 24.0), (4.7, 28.0), (4.8, 32.0), (4.4, 35.5), (3.2, 38.0), (0, 39.2)]
    lathe(p, X, Z, [(0, 14.0)] + prof, WOOD, segs=12, jit=0.07)
    for (y0, y1, r) in ((21.8, 22.8, 3.75), (29.0, 30.0, 4.95), (34.0, 34.9, 4.6)):
        lathe(p, X, Z, [(0, y0), (r, y0), (r, y1), (0, y1)], IRON, segs=12, jit=0.03)
    for (y, rr, n, off) in ((26.0, 4.2, 6, 0), (31.0, 4.9, 6, 30), (36.0, 3.6, 5, 15)):
        for k in range(n):
            a = math.radians(off + 360 * k / n)
            dx, dz = math.cos(a), -math.sin(a)
            ln = 2.4
            dk.cyl(p, (X + dx * (rr + ln / 2 - 0.4), y + ln * 0.15, Z + dz * (rr + ln / 2 - 0.4)), 0.85, ln, LIRON, axis='y', verts=5, top_radius=0.05,
                   rot=(0, math.degrees(a), -72), jitter=0.04)
    for (x, z) in ((54.5, -10), (70, 4), (56, 3), (68, -11)):
        tuft(p, x, z, 1.2, GRASS2, n=5, seed=int(abs(x + z)))


# ---- 25. Roots ------------------------------------------------------------------------------------------------------------
SX, SZ = 62, -44


def build_Roots(p):
    lathe(p, SX, SZ, [(0, 0.0), (10, 0.0), (9.2, 1.4), (6.5, 3.4), (3.2, 4.6), (0, 4.8)], DIRT, segs=14, jit=0.07)
    for k in range(9):
        a = math.radians(40 * k + 10)
        blob(p, SX + 7.0 * math.cos(a), 1.5, SZ - 7.0 * math.sin(a), 2.4, 1.6, 2.2, DDIRT, sub=1, jit=0.06)
    lathe(p, SX, SZ, [(0, 0.0), (3.6, 0.3), (5.0, 3.0), (5.0, 5.5), (3.6, 7.8), (1.6, 8.8), (0, 8.8)], BEAN, segs=10, jit=0.06)
    for k in range(5):
        a = math.radians(72 * k + 20)
        blob(p, SX + 3.9 * math.cos(a), 5.2, SZ - 3.9 * math.sin(a), 2.0, 5.0, 2.0, LBEAN, sub=2, jit=0.05, rot=(0, 72 * k + 20, 0))
    blob(p, SX, 8.4, SZ, 2.6, 1.4, 2.6, LBEAN, sub=2, jit=0.05)
    for k in range(6):
        a = math.radians(15 + 60 * k)
        c, s = math.cos(a), -math.sin(a)
        pts, rr = [], []
        for i in range(9):
            t = i / 8
            ang = a + 0.22 * math.sin(t * 6 + k)
            rad = 3.4 + 11.0 * t
            pts.append((SX + rad * math.cos(ang), 0.5 + 4.0 * (1 - t) ** 1.3 + 0.7 * math.sin(t * 9 + k) * (1 - t), SZ - rad * math.sin(ang)))
            rr.append(2.9 * (1 - t) ** 0.8 + 0.6)
        tube(p, pts, rr, (112, 92, 58) if k % 2 else (92, 120, 62), sides=7, rib=0.16, ribs=3)
        blob(p, SX + 4.4 * c, 3.5, SZ + 4.4 * s, 3.8, 3.2, 3.8, (98, 112, 60), sub=1, jit=0.05)
        a2 = a + 0.5
        c2, s2 = math.cos(a2), -math.sin(a2)
        tube(p, [(SX + 7.5 * c, 3.0, SZ + 7.5 * s), (SX + 9.5 * c2, 1.2, SZ + 9.5 * s2), (SX + 11.0 * c2, 0.2, SZ + 11.0 * s2)], [0.6, 0.4, 0.2],
             BEAN, sides=4)
    rock(p, 51, 0, -50, 3.6, 2.4, 3.2, STONE, seed=41)
    rock(p, 73, 0, -50, 3.2, 2.0, 3.0, DSTONE, seed=42)
    rock(p, 57, 0, -33, 2.4, 1.4, 2.2, STONE, seed=43)


# ---- 26. GooseCoop --------------------------------------------------------------------------------------------------------
def goose(p, x, z, s):
    blob(p, x, 2.2, z, 3.6, 2.8, 2.2, WHITE, sub=2, jit=0.03)
    blob(p, x, 2.45, z + 1.0, 2.4, 1.5, 0.5, (226, 228, 232), sub=1, jit=0.03)
    blob(p, x, 2.45, z - 1.0, 2.4, 1.5, 0.5, (226, 228, 232), sub=1, jit=0.03)
    cone(p, (x - s * 1.7, 2.0, z), 0.0, 0.0, WHITE, verts=3) if False else None
    bx(p, (min(x - s * 2.4, x - s * 1.2), max(x - s * 2.4, x - s * 1.2)), (2.1, 2.9), (z - 0.5, z + 0.5), WHITE, 0.03)
    tube(p, [(x + s * 1.2, 2.6, z), (x + s * 1.6, 3.6, z), (x + s * 1.3, 4.6, z), (x + s * 1.5, 5.2, z)], [0.5, 0.4, 0.35, 0.35], WHITE, sides=5)
    blob(p, x + s * 1.7, 5.4, z, 1.4, 1.2, 1.2, WHITE, sub=1, jit=0.03)
    dk.cyl(p, (x + s * 2.6, 5.3, z), 0.3, 0.9, ORANGE, axis='x', verts=4, top_radius=0.08, jitter=0.03)
    for dz in (-0.45, 0.45):
        bx(p, (x + s * 1.9 - 0.05, x + s * 1.9 + 0.05), (5.5, 5.7), (z + dz - 0.05, z + dz + 0.05), BLACK, 0.01)
    for dz in (-0.5, 0.5):
        bx(p, (x - 0.5, x + 0.5), (0.7, 1.0), (z + dz - 0.1, z + dz + 0.1), ORANGE, 0.02)
        bx(p, (x - 0.1, x + 0.1), (0.0, 0.8), (z + dz - 0.1, z + dz + 0.1), ORANGE, 0.02)


def build_GooseCoop(p):
    disc(p, 0, 0.0, 0.5, 16, 8, 6.5, HAY, n=14)
    rng = random.Random(9)
    for k in range(16):
        x, z = -7 + rng.random() * 14, 10.5 + rng.random() * 11
        dk.box(p, (x, 0.55, z), (1.3, 0.1, 0.12), DHAY if k % 2 else HAY, rot=(0, rng.random() * 180, 0), jitter=0.03)
    # coop
    for k in range(6):
        bx(p, (-5.6 + k, -5.6 + k + 0.97), (0.5, 5.9), (9.9, 14.9), RED if k % 2 else DRED, 0.04)
    bx(p, (-5.7, 0.5), (0.5, 0.9), (9.8, 15.0), DWOOD, 0.03)
    gable_roof(p, -6.1, 0.9, 12.4, 5.8, 3.2, 1.85, (DWOOD, WOOD), rows=2, thick=0.55)
    prism_x(p, [(5.8, 9.9), (5.8, 14.9), (7.6, 12.4)], -5.5, 0.3, DRED, 0.03)
    bx(p, (-3.4, -1.8), (0.5, 3.4), (14.85, 15.1), DWOOD, 0.03)
    bx(p, (-3.2, -2.0), (0.7, 3.2), (14.9, 15.15), (50, 36, 30), 0.02)
    dk.box(p, (-2.6, 1.3, 16.3), (1.4, 0.2, 3.0), WOOD, rot=(28, 0, 0), jitter=0.04)
    for dz in (15.6, 16.4, 17.2):
        bx(p, (-3.3, -1.9), (0.5, 1.0), (dz - 0.05, dz + 0.05), DWOOD, 0.02)
    bx(p, (0.4, 1.6), (2.4, 4.0), (11.2, 13.6), DWOOD, 0.04)
    # fence
    def picket(x, z):
        bx(p, (x - 0.22, x + 0.22), (0.5, 3.6), (z - 0.2, z + 0.2), WOOD, 0.05)
        cone(p, (x, 3.6, z), 0.3, 0.7, WOOD, verts=4, jitter=0.04) if False else None
    for k in range(14):
        picket(-6.3 + k * 0.97, 21.2)
    for k in range(6):
        picket(-6.4, 20.2 - k * 1.7)
        picket(6.4, 20.2 - k * 1.7)
    for (x0, x1, z0, z1) in ((-6.7, 6.7, 21.0, 21.4), (-6.6, -6.2, 11.0, 21.4), (6.2, 6.6, 11.0, 21.4)):
        bx(p, (x0, x1), (2.9, 3.3), (z0, z1), DWOOD, 0.03)
        bx(p, (x0, x1), (1.5, 1.9), (z0, z1), DWOOD, 0.03)
    goose(p, 2, 17, 1)
    goose(p, -3.4, 18.4, -1)
    for (x, z) in ((-7.5, 9.8), (7.4, 10.2), (-7.6, 22.4), (7.5, 22.0)):
        tuft(p, x, z, 1.1, GRASS2, n=4, seed=int(abs(x * z)))


# ---- 27. Stem -------------------------------------------------------------------------------------------------------------
STEM_C = [(62.9, -44.0), (62.4, -43.2), (61.5, -43.0), (60.9, -43.8), (61.2, -44.9), (62.0, -45.4), (62.9, -44.9), (63.4, -43.8), (63.1, -43.0),
          (62.4, -43.2), (61.7, -44.1), (61.3, -45.0)]
LEAF_Y = [14, 20, 26, 32, 38, 44, 50, 56, 62, 67]


def stem_centre(y):
    """Centre line of the stalk at height y: smooth interpolation of the 12 blueprint segment centres (every 6.2 studs, first at 3.1)."""
    u = max(0.0, min(len(STEM_C) - 1.0001, (y - 3.1) / 6.2))
    i = int(math.floor(u))
    f = u - i
    f = f * f * (3 - 2 * f)
    return (STEM_C[i][0] + (STEM_C[i + 1][0] - STEM_C[i][0]) * f, STEM_C[i][1] + (STEM_C[i + 1][1] - STEM_C[i][1]) * f)


def stem_r(y):
    return (4.2 - 2.2 * (y / 74.4)) * 0.93


def build_Stem(p):
    ys = [y * 2.0 for y in range(0, 38)] + [74.4]
    pts = [(stem_centre(y)[0], y, stem_centre(y)[1]) for y in ys]
    rad = []
    for y in ys:
        bump = sum(0.07 * math.exp(-((y - ly) / 0.9) ** 2) for ly in LEAF_Y)
        rad.append(stem_r(y) * (1 + bump))
    tube(p, pts, rad, BEAN, sides=10, jit=0.07, rib=0.12, ribs=5, twist=0.14)
    for ly in LEAF_Y:
        c = stem_centre(ly)
        lathe(p, c[0], c[1], [(0, ly - 0.4), (stem_r(ly) * 1.07, ly - 0.4), (stem_r(ly) * 1.07, ly + 0.4), (0, ly + 0.4)], DBEAN, segs=10, jit=0.04)
    # tendril winding up the stalk and curling away at the end
    tp = []
    for i in range(60):
        t = i / 59
        y = 4 + 62 * t
        c = stem_centre(y)
        a = t * 4.5 * 2 * math.pi
        r = stem_r(y) * 0.98
        tp.append((c[0] + r * math.cos(a), y, c[1] + r * math.sin(a)))
    for k in range(1, 8):
        t = k / 7
        y = 66 + 1.5 * t
        c = stem_centre(y)
        a = 4.5 * 2 * math.pi + t * 2.2 * math.pi
        r = stem_r(y) + 0.6 + 2.0 * t
        tp.append((c[0] + r * math.cos(a), y + 1.0 * t, c[1] + r * math.sin(a)))
    n = len(tp)
    tube(p, tp, [0.42 * (1 - 0.7 * (i / (n - 1)) ** 2) for i in range(n)], LBEAN, sides=4, jit=0.04)


# ---- 28. Leaves -----------------------------------------------------------------------------------------------------------
LEAVES = [(14, 20, 14), (20, 150, 15), (26, 275, 16), (32, 60, 16), (38, 200, 17), (44, 320, 16), (50, 110, 15), (56, 235, 14), (62, 15, 13),
          (67, 140, 11)]


def build_Leaves(p):
    t = math.radians(16)
    for i, (y, a, L) in enumerate(LEAVES):
        ar = math.radians(a)
        base = (SX + 3.0 * math.cos(ar), y + 0.4, SZ - 3.0 * math.sin(ar))
        r0 = 3.2 + L / 2 * math.cos(t)
        yc = y + 1.9 + L / 2 * math.sin(t)
        base = (SX + 3.2 * math.cos(ar), yc - L / 2 * math.sin(t), SZ - 3.2 * math.sin(ar))
        tube(p, [(SX + 1.5 * math.cos(ar), base[1] - 0.8, SZ - 1.5 * math.sin(ar)), base], [0.55, 0.45], DBEAN, sides=5, jit=0.04)
        blade(p, base, a, L, L * 0.55, 16, BEAN if i % 2 == 0 else LBEAN, DBEAN, droop=0.8, th=0.5, jit=0.06, veins=1, n=6)
    # two fat hanging pods
    for (x, y0, z, col, lc) in ((56, 29.0, -47.4, DBEAN, BEAN), (68, 43.0, -42.0, PBEAN, (176, 130, 196))):
        lathe(p, x, z, [(0, y0), (1.0, y0 + 0.4), (1.6, y0 + 2.0), (1.6, y0 + 6.0), (1.0, y0 + 7.6), (0, y0 + 8.0)], col, segs=8, jit=0.05)
        for k in range(4):
            blob(p, x, y0 + 1.6 + k * 1.6, z + 1.3, 1.5, 1.6, 0.7, lc, sub=1, jit=0.04)
        tube(p, [(x, y0 + 7.6, z), (x + 0.5, y0 + 8.8, z + 0.4), (x + 1.8, y0 + 9.6, z + 1.0)], [0.35, 0.3, 0.25], DBEAN, sides=4)


# ---- 29. CloudCastle ------------------------------------------------------------------------------------------------------
def build_CloudCastle(p):
    for (x, y, z, sx, sy, sz, c) in ((26, 55, -50, 34, 9, 24, WHITE), (15, 52.5, -46, 14, 7, 12, (226, 236, 250)), (36, 52.8, -54, 16, 7, 12, WHITE),
                                     (26, 52.5, -41, 12, 5, 6, (226, 236, 250)), (10.5, 52, -55, 3 + 3, 5, 8, WHITE)):
        blob(p, x, y, z, sx, sy, sz, c, sub=2, jit=0.05)
    # keep with hipped roof
    bx(p, (20, 32), (58.0, 72.0), (-56, -46), CASTLE, 0.03)
    for y in (62.0, 66.0, 70.0):
        bx(p, (19.9, 32.1), (y, y + 0.35), (-56.1, -45.9), DCASTLE, 0.03)
    frustum(p, 26, 72, 76.5, -51, 13.2, 11.2, 3.2, 2.4, SLATEBLUE, 0.04)
    bx(p, (25.9, 26.1), (76.5, 80.0), (-51.1, -50.9), DWOOD, 0.02)
    bx(p, (26.1, 28.6), (78.6, 79.9), (-51.0, -50.95), RED, 0.02)
    bx(p, (24.6, 27.4), (60.2, 64.6), (-46.1, -45.6), DWOOD, 0.03)
    bx(p, (24.2, 27.8), (64.4, 64.9), (-46.15, -45.55), DCASTLE, 0.03)
    for k in range(3):
        bx(p, (24.9 + k * 0.9, 25.0 + k * 0.9), (60.3, 64.4), (-45.62, -45.5), IRON, 0.02)
    for (x, y) in ((22.0, 68.0), (30.0, 68.0)):
        bx(p, (x - 0.5, x + 0.5), (y - 1.0, y + 1.0), (-46.1, -45.9), (60, 76, 120), 0.02)
    # round towers with cone roofs and low walls with merlons
    for (tx, tz) in ((15, -44), (37, -44), (15, -58), (37, -58)):
        lathe(p, tx, tz, [(0, 58.0), (2.7, 58.0), (2.5, 60.0), (2.5, 74.3), (3.1, 74.8), (3.1, 75.2), (0, 75.2)], CASTLE, segs=8, jit=0.04)
        lathe(p, tx, tz, [(0, 75.2), (3.6, 75.2), (0.0, 80.0)], SLATEBLUE, segs=8, jit=0.05)
        for y in (65.0, 70.0):
            bx(p, (tx - 0.35, tx + 0.35), (y, y + 1.6), (tz + (2.52 if tz < -50 else 2.52) - 0.1 if False else tz + 2.45, tz + 2.6), (60, 76, 120), 0.02)
    def wall(x0, x1, z0, z1):
        bx(p, (x0, x1), (58.0, 65.0), (z0, z1), DCASTLE, 0.03)
        along_x = (x1 - x0) > (z1 - z0)
        L = (x1 - x0) if along_x else (z1 - z0)
        n = max(2, int(L // 3))
        for k in range(n):
            a = (x0 if along_x else z0) + L * (k + 0.25) / n
            b = a + L / n * 0.5
            if along_x:
                bx(p, (a, b), (65.0, 66.2), (z0, z1), CASTLE, 0.03)
            else:
                bx(p, (x0, x1), (65.0, 66.2), (a, b), CASTLE, 0.03)
    wall(17.8, 23.6, -44.8, -43.2)
    wall(28.4, 34.2, -44.8, -43.2)
    bx(p, (23.6, 28.4), (63.0, 66.0), (-44.8, -43.2), DCASTLE, 0.03)
    wall(14.2, 15.8, -57.2, -45.2)
    wall(36.2, 37.8, -57.2, -45.2)
    wall(17.8, 34.2, -58.8, -57.2)
    for (x, z) in ((8.5, -51), (43, -49)):
        pass


# ---- 30. Nest -------------------------------------------------------------------------------------------------------------
def build_Nest(p):
    prof = [(0, 73.5), (5.0, 73.8), (8.2, 75.6), (9.0, 77.4), (8.6, 78.5), (7.3, 78.3), (6.0, 76.8), (0, 76.1)]
    lathe(p, SX, SZ, prof, (150, 108, 64), segs=14, jit=0.08)
    rng = random.Random(12)
    for k in range(16):
        a1 = 2 * math.pi * k / 16 + rng.random() * 0.2
        a2 = a1 + 0.9 + rng.random() * 0.4
        y1, y2 = 74.8 + rng.random() * 2.6, 74.8 + rng.random() * 2.6
        r1, r2 = 8.3 - (77 - y1) * 0.0 - 0.9 * (1 - (y1 - 73.8) / 4.6), 8.3 - 0.9 * (1 - (y2 - 73.8) / 4.6)
        bar(p, (SX + r1 * math.cos(a1), y1, SZ - r1 * math.sin(a1)), (SX + r2 * math.cos(a2), y2, SZ - r2 * math.sin(a2)), 0.6,
            (WOOD, DWOOD, LWOOD)[k % 3], 0.06)
    for k in range(8):
        a1 = 2 * math.pi * k / 8
        a2 = a1 + 1.0
        bar(p, (SX + 8.5 * math.cos(a1), 78.2, SZ - 8.5 * math.sin(a1)), (SX + 8.5 * math.cos(a2), 78.4, SZ - 8.5 * math.sin(a2)), 0.7,
            (WOOD, LWOOD)[k % 2], 0.05)
    for (x, z, c) in ((60, -40, GOLD), (64.5, -39.5, LGOLD), (57.5, -43.5, DGOLD)):
        lathe(p, x, z, [(0, 76.3), (1.2, 76.4), (1.9, 77.7), (2.0, 78.7), (1.5, 80.3), (0.7, 81.3), (0, 81.6)], c, segs=8, jit=0.04)
    # the golden goose, facing +x
    gx, gy, gz = 62, 82.2, -45
    blob(p, gx, gy, gz, 9, 6.4, 5.4, GOLD, sub=2, jit=0.05)
    blob(p, gx + 1.0, gy + 0.3, gz + 2.4, 5.5, 3.6, 0.9, LGOLD, sub=2, jit=0.04)
    blob(p, gx + 1.0, gy + 0.3, gz - 2.4, 5.5, 3.6, 0.9, DGOLD, sub=2, jit=0.04)
    for k, a in enumerate((165, 180, 195)):
        blade(p, (gx - 4.0, gy + 0.6 + 0.3 * k, gz), a, 3.6, 1.4, 20 + 5 * k, DGOLD if k % 2 == 0 else GOLD, None, th=0.5, n=4, droop=0.2)
    tube(p, [(gx + 3.2, gy + 1.0, gz), (gx + 4.2, gy + 3.0, gz), (gx + 3.6, gy + 4.8, gz), (gx + 4.2, gy + 6.0, gz)], [1.4, 1.1, 0.95, 0.9], GOLD, sides=6, jit=0.04)
    blob(p, gx + 4.2, 88.4, gz, 3, 2.6, 2.6, GOLD, sub=2, jit=0.04)
    dk.cyl(p, (68.3, 88.2, gz), 0.7, 1.8, ORANGE, axis='x', verts=5, top_radius=0.12, jitter=0.03)
    for dz in (-1.1, 1.1):
        dk.cyl(p, (66.7, 88.8, gz + dz), 0.25, 0.2, BLACK, axis='z', verts=5, jitter=0.01)
    for (x, y, s, c) in ((54.5, 87.0, 1.1, LGOLD), (69.0, 85.0, 0.8, LGOLD), (58.0, 89.0, 0.7, SUN), (64.5, 90.0 - 0.6, 0.6, LGOLD), (70.0, 80.5, 0.7, SUN)):
        star_poly(p, (x, y, -41.0), 'xy', s, s * 0.28, 0.12, c, n=4)


def cone(p, base, r, h, col, verts=8, jitter=0.04):
    return dk.cone(p, base, r, h, col, verts=verts, jitter=jitter)


def frustum(p, cx, y0, y1, cz, wb, db, wt, dt, col, jit=0.04):
    """Box that narrows from wb x db at y0 to wt x dt at y1."""
    pts = [(cx - wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz + db / 2), (cx - wb / 2, y0, cz + db / 2),
           (cx - wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz + dt / 2), (cx - wt / 2, y1, cz + dt / 2)]
    return hexa(p, pts, col, jit)


BOX = ((0, 0, 0), (0, 0, 0))

PART_IDS = ["Ground", "Signpost", "FieldWall", "Boulders", "Daisies", "HayBales", "Beans", "Cottage", "OakTree", "Well", "Cow",
            "Footprints", "Toadstools", "Scarecrow", "Boots", "Cauldron", "Harp", "GoldHoard", "Dolmen", "Obelisk", "Table",
            "StandingStones", "GiantStool", "GiantClub", "Roots", "GooseCoop", "Stem", "Leaves", "CloudCastle", "Nest"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

AZ = {}
ELEV = {}
MULT = {"Ground": 1.7, "Stem": 3.0, "Leaves": 3.0, "CloudCastle": 2.6, "Nest": 3.0}
SHIBA_AT = {"Ground": (28, -24, 270, 0), "Nest": (84, -41, 270, 73.5), "CloudCastle": (46, -48, 270, 49.0)}

# ---- previews ----------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    # the meshes are mirrored in x before export (decorkit), so the reference Shiba is placed mirrored too
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}}, studs=16.0)
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
        lo, hi = union(pj)
        global BOX
        BOX = (lo, hi)
        groups = fn(part)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        built[pid] = meshes
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        if pid in SHIBA_AT:
            x, z, f, lift = SHIBA_AT[pid]
        else:
            x = hi[0] + 12 if hi[0] + 12 < 84 else lo[0] - 12
            z = hi[2] - 3
            x, z, f, lift = x, z, 270, 0
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 165), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 165, 40, 2.8, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.1, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_Beanstalk.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
