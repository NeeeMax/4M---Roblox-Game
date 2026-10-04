"""Final low-poly decor models for the theme CloudTemple (30 parts around the 25th Shiba, Angel Shiba).

Usage: blender --background --factory-startup --python build_CloudTemple.py -- <outdir> [PartId,PartId,...]
Writes Decor_CloudTemple_<PartId>.fbx, preview_<PartId>.png and stage_CloudTemple.png into <outdir>.
Every model is written in STAGE coordinates (the numbers of DecorTheme25.luau) and fitted to the union box of its blueprint
pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it). Give part ids (comma
separated) after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "CloudTemple"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "CloudTemple"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_CloudTemple.json"))

# ---- palette (one for all 30 parts: pearl white, marble, gold, pastel pink/rose/lavender/mint, sky blue) -------------------
WHITE = (246, 248, 253)
CLOUD = (216, 228, 246)
CLOUD2 = (196, 212, 238)
SKY = (140, 196, 242)
LSKY = (190, 224, 250)
MARBLE = (238, 232, 220)
STONE = (196, 190, 184)
DSTONE = (160, 154, 150)
GOLD = (238, 190, 64)
DGOLD = (192, 140, 44)
LGOLD = (255, 224, 126)
PINK = (248, 196, 210)
ROSE = (232, 130, 150)
DROSE = (196, 96, 122)
LAV = (186, 172, 226)
MINT = (168, 222, 198)
GREEN = (120, 190, 130)
DGREEN = (84, 150, 100)
SUN = (255, 226, 120)
WOOD = (176, 130, 90)
DWOOD = (132, 92, 62)
CREAM = (250, 240, 214)
RAIN1 = (236, 100, 108)
RAIN2 = (250, 220, 90)
RAIN3 = (130, 210, 150)
RAIN4 = (110, 170, 235)
SKIN = (252, 218, 196)
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



# ---- extra helpers for the cloud theme ----------------------------------------------------------------------------------
def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)


def puff(p, x, y, z, sx, sy, sz, col=WHITE, subdiv=1, jit=0.05, rot=(0, 0, 0)):
    """Low-poly cloud blob / ellipsoid by centre and full size."""
    return dk.ball(p, (x, y, z), 1.0, col, scale=(sx / 2, sy / 2, sz / 2), subdiv=subdiv + 1, jitter=jit, rot=rot)


def cloud(p, x, y0, z, w, h, d, col=WHITE, n=4, jit=0.05):
    """A fluffy cloud standing on y0: a wide core with smaller puffs around it. (x, z) centre, w x h x d overall size."""
    puff(p, x, y0 + h * 0.42, z, w * 0.62, h * 0.84, d * 0.7, col, jit=jit)
    offs = [(-0.3, 0.3, 0.1, 0.62), (0.3, 0.25, -0.1, 0.56), (0.0, 0.2, 0.3, 0.5), (0.05, 0.22, -0.32, 0.5)]
    for (ox, oy, oz, s) in offs[:n]:
        puff(p, x + ox * w, y0 + h * oy, z + oz * d, w * s * 0.75, h * s * 1.1, d * s * 0.75, col, jit=jit)


def vcol(p, cx, cz, y0, y1, r, col, verts=10, base=True, cap=True, jit=0.03):
    """Marble column with a slightly wider foot and capital (stays inside radius r * 1.18)."""
    vcyl(p, cx, y0, y1, cz, r, col, verts=verts, jit=jit)
    if base:
        vcyl(p, cx, y0, y0 + r * 0.5, cz, r * 1.18, STONE, verts=verts, jit=jit)
    if cap:
        vcyl(p, cx, y1 - r * 0.5, y1, cz, r * 1.18, STONE, verts=verts, jit=jit)


def halo(p, c, R, r, col, segs=18, sides=4, jit=0.03):
    """Ring standing in the x-y plane (faces +z) around centre c, tube radius r."""
    pts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(sides):
            b = 2 * math.pi * j / sides + math.pi / 4
            rr = R + r * math.cos(b)
            pts.append((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2))
    return dk.poly(p, c, pts, faces, col, jit)


def arc_strip(p, cx, cy, ao, bo, ai, bi, z0, z1, col, n=10, t0=0.0, t1=math.pi, jit=0.03):
    """Solid band between two ellipse arcs (outer half-axes ao, bo, inner ai, bi) around (cx, cy), extruded from z0 to z1."""
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((cx + ao * math.cos(t), cy + bo * math.sin(t), z0))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((cx + ai * math.cos(t), cy + bi * math.sin(t), z0))
    m = n + 1
    pts += [(x, y, z1) for (x, y, _) in pts]
    off = 2 * m
    faces = []
    for i in range(n):
        faces += [(i, i + 1, m + i + 1, m + i), (off + i, off + i + 1, off + m + i + 1, off + m + i),
                  (i, i + 1, off + i + 1, off + i), (m + i, m + i + 1, off + m + i + 1, off + m + i)]
    faces += [(0, m, off + m, off), (n, m + n, off + m + n, off + n)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def sparkle4(p, c, r, col=SUN):
    star_poly(p, c, 'xy', r, r * 0.3, 0.14, col, n=4, rot0=90)


# ---- more helpers ---------------------------------------------------------------------------------------------------------
def frustum(p, cx, y0, y1, cz, wb, db, wt, dt, col, jit=0.04):
    """Box that narrows from wb x db at y0 to wt x dt at y1 (roof tier)."""
    pts = [(cx - wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz + db / 2), (cx - wb / 2, y0, cz + db / 2),
           (cx - wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz + dt / 2), (cx - wt / 2, y1, cz + dt / 2)]
    return hexa(p, pts, col, jit)


def edisc(p, cx, y0, y1, cz, rx, rz, col, n=16, jit=0.03):
    """Flat elliptical slab."""
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), y0, cz + rz * math.sin(2 * math.pi * i / n)) for i in range(n)]
    pts += [(x, y1, z) for (x, _, z) in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


WING_OUTLINE = [(0, 0), (0.5, -0.14), (1.0, 0.04), (0.82, 0.38), (0.98, 0.70), (0.62, 0.86), (0.42, 1.0), (0.16, 0.66)]


def wing(p, x, y, z, side, w, h, t, col=WHITE, tilt=0.0, jit=0.03):
    """Feathered wing in the x-y plane with its root at (x, y, z); side +1 reaches toward +x, -1 toward -x; tilt leans it outward."""
    th = -side * math.radians(tilt)
    c, s = math.cos(th), math.sin(th)
    pts = []
    for zz in (z + t / 2, z - t / 2):
        for (u, v) in WING_OUTLINE:
            a, b = u * w * side, v * h
            pts.append((x + a * c - b * s, y + a * s + b * c, zz))
    n = len(WING_OUTLINE)
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def lbox(p, cx, cz, deg, lx, y, lz, sx, sy, sz, col, jit=0.04):
    """Box placed by an offset (lx, lz) in the local frame of a group turned by deg about its centre (cx, cz)."""
    a, b = ry(lx, lz, deg)
    return dk.box(p, (cx + a, y, cz + b), (sx, sy, sz), col, rot=(0, deg, 0), jitter=jit)


def angel(p, x, z, deg, plw, plh, body_h, rb, head_r, wing_h, kneel=False):
    """A marble angel statue on a plinth (plinth turned by deg, the figure faces the road)."""
    dk.box(p, (x, plh / 2, z), (plw, plh, plw), STONE, rot=(0, deg, 0), jitter=0.04)
    dk.box(p, (x, plh - 0.15, z), (plw + 0.4, 0.3, plw + 0.4), MARBLE, rot=(0, deg, 0), jitter=0.03)
    y0 = plh
    if kneel:
        vcyl(p, x, y0, y0 + body_h, z, rb * 1.25, MARBLE, verts=10, top_r=rb * 0.6)
        dk.box(p, (x, y0 + 0.6, z + rb * 0.95), (rb * 1.4, 1.0, rb * 1.2), MARBLE, jitter=0.03)
    else:
        vcyl(p, x, y0, y0 + body_h, z, rb, MARBLE, verts=10, top_r=rb * 0.62)
    f = 0.62
    rwaist = (rb if not kneel else rb * 1.25) * (1 - f) + rb * 0.62 * f + 0.1
    vcyl(p, x, y0 + body_h * f - 0.18, y0 + body_h * f + 0.18, z, rwaist, GOLD, verts=10, jit=0.03)
    hy = y0 + body_h + head_r * 0.85
    ball(p, (x, hy, z), head_r, WHITE, subdiv=1, jit=0.03)
    halo(p, (x, hy + 0.1, z - head_r * 0.85), head_r * 1.1, 0.11, GOLD, segs=12, sides=3)
    dk.box(p, (x, y0 + body_h * 0.8, z + rb * 0.55), (rb * 1.0, 0.45, 0.5), MARBLE, jitter=0.03)    # folded arms
    for side in (-1, 1):
        wing(p, x + side * rb * 0.35, y0 + body_h * 0.5, z - rb * 0.75, side, rb * 2.0, wing_h, 0.5, WHITE, tilt=14)


def wing_y(p, x, y, z, side, w, h, t, yaw, col=WHITE, tilt=14.0, jit=0.03):
    """Like wing() but turned about the vertical axis through (x, z) by yaw degrees (so a cherub can face any way)."""
    th = -side * math.radians(tilt)
    c, s = math.cos(th), math.sin(th)
    pts = []
    for dz in (t / 2, -t / 2):
        for (u, v) in WING_OUTLINE:
            a, b = u * w * side, v * h
            px, py = a * c - b * s, a * s + b * c
            ox, oz = ry(px, dz, yaw)
            pts.append((x + ox, y + py, z + oz))
    n = len(WING_OUTLINE)
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def ribbon(p, x, z, deg, w, ytop, yb0, yb1, col, amp, t, n=7, phase=0.0, jit=0.04):
    """Waving flag cloth hanging from x (local +x of the pole turned by deg): a closed strip with a wave in z, bottom edge sloping yb0 -> yb1."""
    rings = []
    for i in range(n + 1):
        u = w * i / n
        zw = amp * (i / n) ** 0.8 * math.sin(i * 0.95 + phase)
        yb = yb0 + (yb1 - yb0) * i / n
        ring = []
        for (yy, dz) in ((ytop, t / 2), (ytop, -t / 2), (yb, -t / 2), (yb, t / 2)):
            a, b = ry(u + 0.25, zw + dz, deg)
            ring.append((x + a, yy, z + b))
        rings.append(ring)
    pts = [q for r in rings for q in r]
    faces = [(0, 1, 2, 3), tuple(4 * n + k for k in (3, 2, 1, 0))]
    for i in range(n):
        o, q = 4 * i, 4 * i + 4
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((o + k, o + k2, q + k2, q + k))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def flag(p, x, z, y_top, w, h, col, deg, trim=GOLD):
    ribbon(p, x, z, deg, w, y_top, y_top - h, y_top - h * 0.78, col, 0.7, 0.22)
    ribbon(p, x, z, deg, w, y_top, y_top - 0.45, y_top - 0.45, trim, 0.7, 0.32)
    ribbon(p, x, z, deg, w, y_top - h * 0.8, y_top - h * 0.8 - 0.35, y_top - h * 0.58 - 0.35, trim, 0.7, 0.32)
    i = 2
    zw = 0.7 * (i / 7) ** 0.8 * math.sin(i * 0.95)
    a, b = ry(w * i / 7 + 0.25, zw, deg)
    dk.cyl(p, (x + a, y_top - h * 0.5, z + b), h * 0.2, 0.5, trim, axis='z', verts=8, rot=(0, deg, 0), jitter=0.03)


BIG_WING = [(0, 0), (0.06, 0.45), (0.2, 0.8), (0.45, 1.0), (0.78, 0.96), (1.0, 0.66), (0.86, 0.6), (0.98, 0.40), (0.82, 0.36),
            (0.88, 0.14), (0.7, 0.14), (0.7, -0.07), (0.54, 0.02), (0.44, -0.16), (0.3, -0.04), (0.14, -0.1)]


def wing_shape(p, x, y, z, side, w, h, t, col, outline=None, jit=0.03):
    """Flat wing silhouette (outline in u outward / v up units) with its root at (x, y), standing in the x-y plane."""
    outline = outline or BIG_WING
    pts = []
    for zz in (z + t / 2, z - t / 2):
        for (u, v) in outline:
            pts.append((x + u * w * side, y + v * h, zz))
    n = len(outline)
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


# ---- 1. Ground ------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    bx(p, (-80, 80), (0, 0.3), (-57.5, 57.5), CLOUD, 0.04)
    # tonal patches in the cloud floor
    for (x0, x1, z0, z1, col) in ((-76, -40, -50, -20, LSKY), (10, 46, 14, 50, CLOUD2), (-30, 8, 38, 54, LSKY), (40, 76, -52, -34, CLOUD2),
                                  (-8, 30, -52, -40, LSKY)):
        bx(p, (x0, x1), (0.3, 0.34), (z0, z1), col, 0.05)
    # white drifts
    for (x, z, w, d, col) in ((-48, 26, 34, 20, WHITE), (56, -30, 30, 18, WHITE), (-30, -40, 28, 14, WHITE), (36, 44, 26, 12, WHITE),
                              (-10, 5, 20, 10, WHITE), (62, 6, 16, 10, SKY), (-62, -10, 22, 14, WHITE)):
        puff(p, x, 0.3, z, w, 0.5, d, col, subdiv=0, jit=0.05)
        puff(p, x + w * 0.12, 0.32, z - d * 0.12, w * 0.6, 0.5, d * 0.62, WHITE, subdiv=0, jit=0.05)
    # gold-ringed marble plaza under the Angel Shiba
    bx(p, (7, 33), (0.3, 0.5), (-27, -1), MARBLE, 0.03)
    bx(p, (11.5, 28.5), (0.5, 0.58), (-22.5, -21.5), GOLD, 0.02)
    bx(p, (11.5, 28.5), (0.5, 0.58), (-6.5, -5.5), GOLD, 0.02)
    bx(p, (11.5, 12.5), (0.5, 0.58), (-21.5, -6.5), GOLD, 0.02)
    bx(p, (27.5, 28.5), (0.5, 0.58), (-21.5, -6.5), GOLD, 0.02)
    bx(p, (12.5, 27.5), (0.5, 0.54), (-21.5, -6.5), WHITE, 0.02)
    star_poly(p, (20, 0.54, -14), 'xz', 6.0, 2.6, 0.08, GOLD, n=8, rot0=90)
    vcyl(p, 20, 0.55, 0.585, -14, 2.2, SKY, verts=16, jit=0.02)
    vcyl(p, 20, 0.56, 0.59, -14, 1.0, LGOLD, verts=10, jit=0.02)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bx(p, (20 + sx * 7.5 - 0.9, 20 + sx * 7.5 + 0.9), (0.5, 0.585), (-14 + sz * 7.5 - 0.9, -14 + sz * 7.5 + 0.9), GOLD, 0.02)
    for k in range(6):                                                        # cloud puffs round the plaza
        a = math.radians(60 * k + 20)
        puff(p, 20 + 18.5 * math.cos(a), 0.3, -14 + 17.0 * math.sin(a), 6.0, 0.5, 4.2, WHITE, subdiv=0, jit=0.05)
    # second marble pad
    bx(p, (-72, -52), (0.3, 0.5), (-14, 6), MARBLE, 0.03)
    bx(p, (-70, -54), (0.5, 0.56), (-12, -11.2), STONE, 0.02)
    bx(p, (-70, -54), (0.5, 0.56), (4.2, 5), STONE, 0.02)
    star_poly(p, (-62, 0.5, -4), 'xz', 5.0, 2.6, 0.06, LAV, n=6, rot0=30)
    star_poly(p, (-62, 0.54, -4), 'xz', 4.2, 1.8, 0.07, GOLD, n=6, rot0=90)
    # stepping cloud tiles along the walkway
    pts = [(v[0], v[1]) for v in BP["Path"]]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        n = max(1, int(L // 9))
        ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        for k in range(n):
            u = (k + 0.5) / n
            cx, cz = x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
            dk.box(p, (cx, 0.34, cz), (6.0, 0.08, 4.6), WHITE, rot=(0, ang, 0), jitter=0.04)


# ---- 2. PearlyGate --------------------------------------------------------------------------------------------------------
def gate_leaf(p, xa, xb, z):
    w = xb - xa
    B(p, (xa + xb) / 2, 1.0, z, w, 0.5, 0.5, GOLD)
    B(p, (xa + xb) / 2, 9.75, z, w, 0.5, 0.5, GOLD)
    B(p, xa + 0.25, 5.4, z, 0.5, 9.0, 0.5, GOLD)
    B(p, xb - 0.25, 5.4, z, 0.5, 9.0, 0.5, GOLD)
    for k in range(1, 4):
        x = xa + w * k / 4
        B(p, x, 5.4, z, 0.3, 8.6, 0.4, LGOLD)
        B(p, x, 10.3, z, 0.4, 0.9, 0.4, GOLD)
    B(p, (xa + xb) / 2, 5.6, z, w * 0.55, 0.35, 0.4, DGOLD)
    ball(p, ((xa + xb) / 2, 5.6, z), 0.55, ROSE, subdiv=0)


def build_PearlyGate(p):
    for z in (24, 45):
        B(p, -2, 0.9, z, 4.2, 1.8, 4.2, STONE)
        vcyl(p, -2, 1.8, 14.0, z, 1.6, MARBLE, verts=12)
        vcyl(p, -2, 1.8, 3.0, z, 1.95, STONE, verts=12)
        vcyl(p, -2, 12.6, 14.0, z, 1.9, STONE, verts=12)
        B(p, -2, 14.6, z, 4.4, 1.2, 4.4, GOLD)
        ball(p, (-2, 18.6, z), 1.2, GOLD, subdiv=1)
    B(p, -2, 16.2, 34.5, 3.2, 2.2, 26, MARBLE)
    B(p, -2, 15.35, 34.5, 3.6, 0.5, 26, GOLD)
    for z in (28.5, 34.5, 40.5):                                           # pink panels on both faces of the lintel
        B(p, -3.7, 16.2, z, 0.3, 1.2, 3.6, PINK)
        B(p, -0.3, 16.2, z, 0.3, 1.2, 3.6, PINK)
    for x in (-3.75, -0.25):                                               # gold sun stars on both faces of the lintel
        star_poly(p, (x, 16.2, 34.5), "yz", 1.05, 0.45, 0.2, GOLD, n=8, rot0=90)
        star_poly(p, (x + (-0.08 if x < -2 else 0.08), 16.2, 34.5), "yz", 0.5, 0.22, 0.2, LGOLD, n=8, rot0=90)
    gate_leaf(p, -6.1, -2.3, 25.6)
    gate_leaf(p, -1.7, 2.1, 43.4)
    puff(p, -2, 1.2, 21, 6, 2.4, 4.4, WHITE)
    puff(p, -2, 0.9, 46.0, 5, 1.8, 3.0, WHITE)
    puff(p, -4.4, 0.7, 26.6, 2.8, 1.4, 2.4, WHITE)
    puff(p, 0.4, 0.7, 42.4, 2.8, 1.4, 2.4, WHITE)


# ---- 3. HeavenSign --------------------------------------------------------------------------------------------------------
def build_HeavenSign(p):
    puff(p, -37, 0.7, 32, 13, 1.4, 5, WHITE)
    puff(p, -41, 0.9, 32, 5, 1.8, 4.2, WHITE)
    puff(p, -33, 0.9, 32, 5, 1.8, 4.2, CLOUD)
    for x in (-41, -33):
        vcyl(p, x, 0.8, 7.4, 32, 0.45, MARBLE, verts=8)
        vcyl(p, x, 0.8, 1.8, 32, 0.8, STONE, verts=8)
    B(p, -37, 7.4, 31.55, 11.8, 4.8, 0.5, GOLD)
    B(p, -37, 7.4, 32.0, 11.0, 4.0, 0.8, SKY)
    for (cx, cy, sx, sy) in ((-37, 9.55, 11.8, 0.5), (-37, 5.25, 11.8, 0.5), (-42.65, 7.4, 0.5, 4.8), (-31.35, 7.4, 0.5, 4.8)):
        B(p, cx, cy, 32.4, sx, sy, 0.6, GOLD)
    text(p, "HEAVEN", -37, 6.3, 32.4, 32.8, 1.45, 2.2, 0.42, 0.3, WHITE)
    B(p, -34.5, 3.4, 32.7, 5, 1.6, 0.5, PINK)
    for (cx, cy, sx, sy) in ((-34.5, 4.25, 5.0, 0.2), (-34.5, 2.55, 5.0, 0.2)):
        B(p, cx, cy, 33.0, sx, sy, 0.3, GOLD)
    star_poly(p, (-34.5, 3.4, 33.0), 'xy', 0.6, 0.25, 0.2, GOLD, n=5)
    for x in (-42.65, -31.35):                                  # gold finials on the top corners of the frame
        ball(p, (x, 9.6, 31.8), 0.5, GOLD, subdiv=1)


# ---- 4. CloudMounds -------------------------------------------------------------------------------------------------------
def build_CloudMounds(p):
    puff(p, 20, 2.6, 47, 10, 5.2, 8.5, WHITE, jit=0.03)
    puff(p, 27, 3.6, 45, 13, 7.2, 10, WHITE, jit=0.03)
    puff(p, 34, 2.2, 48, 8.5, 4.4, 7, CLOUD, jit=0.03)
    puff(p, 29, 1.6, 52, 7, 3.2, 6, WHITE, jit=0.03)
    puff(p, 25, 6.6, 45, 6, 4, 5, WHITE, jit=0.03)
    puff(p, 22.5, 1.2, 51, 5, 2.4, 4.2, CLOUD)
    puff(p, 31.5, 4.6, 44, 5, 3.4, 4.2, WHITE)
    puff(p, 36, 1.0, 44.5, 4.4, 2.0, 4.0, WHITE)
    puff(p, 17.5, 1.0, 43.5, 4.0, 2.0, 3.6, CLOUD)
    puff(p, 27, 7.6, 46, 3.4, 2.0, 3.0, WHITE)
    puff(p, 31, 0.9, 54, 4.2, 1.8, 3.6, WHITE)
    for s in (-1, 1):                                                    # a sleepy smile on the big mound
        B(p, 27 + s * 2.2, 4.7, 49.75, 1.0, 0.22, 0.4, DSTONE, jit=0.02)
        ball(p, (27 + s * 3.7, 3.7, 49.2), 0.7, PINK, scale=(1, 0.7, 0.6), subdiv=0, jit=0.03)
    B(p, 27, 3.4, 50.1, 1.4, 0.22, 0.4, DROSE, jit=0.02)
    sparkle4(p, (21, 6.2, 51.0), 1.3, SUN)
    sparkle4(p, (33.5, 6.9, 51.4), 1.0, SUN)
    sparkle4(p, (25.5, 8.4, 50.4), 0.8, PINK)


# ---- 5. GoldenLamps -------------------------------------------------------------------------------------------------------
def lamp(p, x, z):
    vcyl(p, x, 0, 1.0, z, 1.15, STONE, verts=10)
    vcyl(p, x, 1.0, 1.5, z, 0.75, MARBLE, verts=10)
    vcyl(p, x, 0.6, 8.5, z, 0.32, GOLD, verts=8)
    vcyl(p, x, 2.5, 3.1, z, 0.58, DGOLD, verts=8)
    vcyl(p, x, 5.8, 6.2, z, 0.5, DGOLD, verts=8)
    vcyl(p, x, 8.4, 8.9, z, 1.15, GOLD, verts=8)
    vcyl(p, x, 8.9, 10.2, z, 0.95, SUN, verts=8)
    vcyl(p, x, 10.2, 10.7, z, 1.3, GOLD, verts=8, top_r=0.12)
    for a in range(4):
        ang = math.radians(45 + 90 * a)
        B(p, x + 1.02 * math.cos(ang), 9.55, z + 1.02 * math.sin(ang), 0.16, 1.5, 0.16, GOLD, jit=0.02)
    puff(p, x + 0.4, 0.5, z - 0.3, 2.8, 1.0, 2.4, WHITE)


def build_GoldenLamps(p):
    for (x, z) in ((-6, 10), (-18, 6.5), (-30, -19)):
        lamp(p, x, z)


# ---- 6. WishingWell -------------------------------------------------------------------------------------------------------
def build_WishingWell(p):
    puff(p, -19.5, 0.9, 18, 4, 1.8, 3, WHITE)
    puff(p, -12.5, 0.8, 13.5, 3.6, 1.6, 3, WHITE)
    vcyl(p, -16, 0, 2.6, 16, 3.3, MARBLE, verts=12)
    vcyl(p, -16, 2.3, 2.8, 16, 3.55, STONE, verts=12)
    vcyl(p, -16, 2.6, 2.8, 16, 2.5, SKY, verts=12)
    for x in (-18.4, -13.6):
        B(p, x, 5.2, 16, 0.8, 5.2, 0.8, WOOD)
        B(p, x, 2.9, 16, 1.0, 0.6, 1.0, DWOOD)
    xcyl(p, -18.4, -13.6, 6.6, 16, 0.5, DWOOD, verts=8)
    B(p, -16, 5.4, 16, 0.1, 2.4, 0.1, CREAM)
    B(p, -16, 4.0, 16, 0.9, 0.8, 0.9, DWOOD)
    # little pink gable roof
    pts = [(-3.7, 7.85, -2.7), (3.7, 7.85, -2.7), (3.7, 7.85, 2.7), (-3.7, 7.85, 2.7), (-3.7, 9.4, 0), (3.7, 9.4, 0)]
    dk.poly(p, (-16, 0, 16), pts, [(0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)], PINK, 0.04)
    B(p, -16, 9.35, 16, 7.6, 0.25, 0.4, ROSE)
    B(p, -16, 8.0, 18.7, 7.6, 0.3, 0.3, ROSE)
    B(p, -16, 8.0, 13.3, 7.6, 0.3, 0.3, ROSE)
    ball(p, (-16, 10.0, 16), 0.7, GOLD, subdiv=1)
    for a in range(5):                                                       # petal stones round the rim
        ang = math.radians(20 + 72 * a)
        ball(p, (-16 + 3.9 * math.cos(ang), 0.6, 16 + 3.9 * math.sin(ang)), 0.6, WHITE, scale=(1, 0.6, 1), subdiv=1)


# ---- 7. FlowerBeds --------------------------------------------------------------------------------------------------------
def bloom(p, x, y, z, col, h=0.0):
    B(p, x, 1.6 + (y - 1.6) / 2, z, 0.18, y - 1.6, 0.18, DGREEN, jit=0.02)
    dk.cyl(p, (x, y, z), 0.8, 0.3, col, axis='y', verts=7, jitter=0.05)
    dk.box(p, (x, y + 0.2, z), (0.5, 0.25, 0.5), SUN, jitter=0.02)


def flower_bed(p, cx, cz, w, d, deg, cols, tops):
    c = (cx, 0.5, cz)
    dk.box(p, c, (w, 1.0, d), WOOD, rot=(0, deg, 0), jitter=0.05)
    dk.box(p, (cx, 1.25, cz), (w - 0.5, 0.7, d - 0.5), GREEN, rot=(0, deg, 0), jitter=0.06)
    n = len(cols)
    for i in range(n):
        u = -w / 2 + 0.9 + (w - 1.8) * i / (n - 1)
        v = d * 0.2 * (1 if i % 2 else -1)
        a, b = ry(u, v, deg)
        bloom(p, cx + a, tops[i], cz + b, cols[i])


def build_FlowerBeds(p):
    flower_bed(p, -42, 12, 8, 3.2, 20, (PINK, LAV, SUN, ROSE, PINK), (3.0, 3.2, 2.8, 3.25, 2.9))
    flower_bed(p, -35, 8, 7, 3.0, -15, (ROSE, SUN, PINK, LAV, ROSE), (3.1, 2.8, 3.25, 3.0, 2.9))
    flower_bed(p, -39, 4, 6, 2.8, 30, (LAV, ROSE, SUN, PINK), (3.2, 2.9, 3.25, 3.0))


# ---- 8. CloudFountain -----------------------------------------------------------------------------------------------------
def build_CloudFountain(p):
    puff(p, 60, 1.0, 38, 14, 2.0, 14, WHITE)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        puff(p, 60 + 7.2 * math.cos(a), 0.9, 38 + 6.2 * math.sin(a), 5.6, 1.8, 5.6, WHITE if k % 2 else CLOUD)
    vcyl(p, 60, 1.0, 3.4, 38, 6.5, MARBLE, verts=14)
    vcyl(p, 60, 3.1, 3.6, 38, 6.9, STONE, verts=14)
    vcyl(p, 60, 3.4, 3.6, 38, 5.7, SKY, verts=14)
    vcyl(p, 60, 3.5, 7.4, 38, 1.5, MARBLE, verts=10)
    vcyl(p, 60, 7.2, 8.0, 38, 2.0, MARBLE, verts=12, top_r=3.4)
    vcyl(p, 60, 8.0, 8.9, 38, 3.4, MARBLE, verts=12)
    vcyl(p, 60, 8.7, 8.9, 38, 2.8, SKY, verts=12)
    vcyl(p, 60, 8.9, 11.0, 38, 0.8, MARBLE, verts=8)
    ball(p, (60, 12.0, 38), 1.3, GOLD, subdiv=1)
    for k in range(4):                                                      # little sky-blue arcs of water falling into the bowl
        a = math.radians(45 + 90 * k)
        bar(p, (60 + 0.5 * math.cos(a), 11.2, 38 + 0.5 * math.sin(a)), (60 + 2.5 * math.cos(a), 9.0, 38 + 2.5 * math.sin(a)), 0.35, LSKY, 0.03)
    for k in range(6):
        a = math.radians(60 * k)
        ball(p, (60 + 6.7 * math.cos(a), 3.9, 38 + 6.7 * math.sin(a)), 0.45, GOLD, subdiv=0)


# ---- 9. CloudTrees --------------------------------------------------------------------------------------------------------
def tree(p, x, z, th, trunk_r, crowns, dots, base_col=WOOD):
    vcyl(p, x, 0, th, z, trunk_r, base_col, verts=7, top_r=trunk_r * 0.6)
    vcyl(p, x, 0, 0.7, z, trunk_r * 1.7, DWOOD, verts=7, top_r=trunk_r)
    for (cx, cy, cz, sx, sy, sz, col) in crowns:
        puff(p, cx, cy, cz, sx, sy, sz, col, jit=0.06, rot=(17 * len(crowns), 31 * (int(cx) % 5), 11 * (int(cz) % 4)))
    for (dx, dy, dz, col) in dots:
        ball(p, (dx, dy, dz), 0.42, col, subdiv=0, jit=0.05)


def build_CloudTrees(p):
    tree(p, -46, 24, 7.8, 0.7, [(-46, 9, 24, 9, 8, 9, MINT), (-48, 7.5, 26, 6, 5, 6, MINT), (-44, 8.2, 22.4, 5, 4.4, 5, MINT)],
         [(-44.2, 12.3, 24, PINK), (-47.5, 10.8, 27.0, PINK), (-42.2, 8.6, 22.8, PINK), (-49.2, 8.0, 25.0, LAV), (-46, 7.4, 28.0, PINK)])
    tree(p, -52, 30, 5.6, 0.6, [(-52, 7, 30, 7, 6.4, 7, PINK), (-54, 6.0, 31.5, 4.5, 4, 4.5, PINK), (-50, 5.8, 28.5, 4, 3.6, 4, PINK)],
         [(-52, 10.0, 30, SUN), (-54.8, 6.0, 32.6, MINT), (-49.4, 5.6, 28.2, MINT), (-51, 8.0, 33.2, WHITE)])
    tree(p, -40, 20, 5.0, 0.55, [(-40, 6.6, 20, 6.4, 5.6, 6.4, MINT), (-42, 5.4, 22, 4, 3.4, 4, PINK)],
         [(-40, 9.2, 20, PINK), (-37.2, 6.2, 20.6, PINK), (-42.5, 5.2, 23.2, ROSE)])
    puff(p, -44, 0.4, 28, 4, 0.9, 3, WHITE)
    puff(p, -49, 0.4, 32.5, 3.6, 0.9, 2.6, WHITE)
    puff(p, -41.5, 0.4, 17, 3.2, 0.9, 2.4, WHITE)


# ---- 10. Benches ----------------------------------------------------------------------------------------------------------
def bench(p, cx, cz, deg):
    lbox(p, cx, cz, deg, 0, 2.2, 0, 2.2, 0.7, 6, MARBLE)
    lbox(p, cx, cz, deg, 1.7, 3.6, 0, 0.7, 2.6, 6, MARBLE)
    lbox(p, cx, cz, deg, 0, 3.0, 0, 1.7, 0.3, 5.2, PINK)                        # cushion
    for lz in (-2.0, 2.0):
        lbox(p, cx, cz, deg, 0, 1.0, lz, 1.8, 1.4, 0.8, STONE)
        lbox(p, cx, cz, deg, 0.2, 3.35, lz * 1.45, 2.4, 0.5, 0.7, MARBLE)       # arm rests
        lbox(p, cx, cz, deg, 0.2, 2.9, lz * 1.45, 0.9, 0.9, 0.7, STONE)
    lbox(p, cx, cz, deg, 1.7, 4.85, 0, 0.9, 0.2, 6.2, GOLD)                    # gold rail on top of the back


def build_Benches(p):
    bench(p, 66.5, 14, 0)
    bench(p, 64, 24, 15)
    vcyl(p, 61, 0, 2.6, 19, 1.5, MARBLE, verts=10)
    vcyl(p, 61, 0, 0.6, 19, 2.0, STONE, verts=10)
    vcyl(p, 61, 2.55, 2.85, 19, 2.0, PINK, verts=12)
    vcyl(p, 61, 2.85, 3.1, 19, 0.5, GOLD, verts=8)
    vcyl(p, 61.8, 2.85, 3.3, 19.6, 0.32, WHITE, verts=8)
    ball(p, (60.0, 3.15, 18.2), 0.3, GOLD, subdiv=0)


# ---- 11. AngelStatues -----------------------------------------------------------------------------------------------------
def build_AngelStatues(p):
    angel(p, -62, -10, 25, 4.4, 2.4, 6.0, 1.4, 1.2, 4.6)
    angel(p, -67, -2, -20, 3.6, 2.0, 4.8, 1.15, 1.0, 3.8)
    angel(p, -58, -3, 35, 3.0, 1.6, 2.8, 1.0, 0.85, 3.0, kneel=True)
    puff(p, -62, 0.3, -9, 5.6, 0.6, 5.0, WHITE)
    puff(p, -66.5, 0.3, -1, 5.0, 0.6, 4.4, WHITE)


# ---- 12. HarpGarden -------------------------------------------------------------------------------------------------------
def build_HarpGarden(p):
    puff(p, -32.5, 1.2, 24, 5, 2.4, 4, WHITE)
    puff(p, -23.5, 1.0, 20, 4.4, 2.0, 3.6, WHITE)
    B(p, -28, 0.6, 22, 8, 1.2, 4, STONE)
    B(p, -28, 1.35, 22, 8.6, 0.3, 4.6, MARBLE)
    neck = [(-31.8, 13.2), (-30.4, 13.8), (-28.4, 13.6), (-26.6, 12.8), (-24.8, 11.4)]
    B(p, -31.2, 7.0, 22, 1.2, 12.0, 1.2, GOLD)                                  # tall pillar
    B(p, -24.8, 6.0, 22, 1.8, 10.0, 1.4, GOLD)                                  # sound-box column
    B(p, -24.8, 3.2, 22, 2.2, 0.5, 1.8, DGOLD)
    for k in range(3):
        ball(p, (-24.8, 4.6 + k * 2.2, 22.8), 0.34, ROSE, subdiv=0)
    for (a, b) in zip(neck, neck[1:]):
        bar(p, (a[0], a[1], 22), (b[0], b[1], 22), 1.1, GOLD, 0.03)
    ball(p, (-31.8, 13.5, 22), 0.8, GOLD, subdiv=1)
    ball(p, (-31.2, 1.6, 22), 0.9, DGOLD, subdiv=0)
    for i in range(6):
        x = -30.1 + i * 0.95
        ytop = 12.6 - (x + 30.1) * 0.28 + (0.7 if i < 3 else 0.0)
        ytop = 13.4 - (x + 30.4) * 0.34
        B(p, x, (1.4 + ytop) / 2, 22, 0.14, ytop - 1.4, 0.14, WHITE, jit=0.02)
    for k in range(3):                                                         # little sparkles around the harp
        sparkle4(p, (-34.0 + k * 1.6, 4.5 + k * 3.2, 24.2), 0.9, SUN)


# ---- 13. CloudCottage -----------------------------------------------------------------------------------------------------
def build_CloudCottage(p):
    puff(p, -64, 1.4, 38, 17, 2.8, 14, WHITE)
    for k in range(5):
        a = math.radians(40 + 72 * k)
        puff(p, -64 + 8.6 * math.cos(a), 1.2, 38 + 7.0 * math.sin(a), 8.4, 2.4, 7.0, WHITE if k % 2 else CLOUD)
    bx(p, (-70.5, -57.5), (1.5, 11.5), (33, 43), CREAM, 0.04)
    bx(p, (-70.9, -57.1), (1.5, 2.6), (32.6, 43.4), STONE, 0.04)
    for x in (-70.5, -57.5):
        for z in (33, 43):
            B(p, x, 6.5, z, 0.8, 10, 0.8, MARBLE, jit=0.03)
    frustum(p, -64, 11.5, 13.5, 38, 15.6, 12.0, 13.2, 10.2, ROSE)
    frustum(p, -64, 13.5, 15.5, 38, 11.4, 8.6, 9.4, 7.2, PINK)
    frustum(p, -64, 15.5, 17.5, 38, 6.4, 5.6, 4.2, 3.4, ROSE)
    ball(p, (-64, 18.2, 38), 1.0, GOLD, subdiv=1)
    # door
    B(p, -64, 4.6, 43.1, 2.8, 4.4, 0.4, GOLD)
    B(p, -64, 4.6, 43.0, 3.6, 5.0, 0.3, WHITE)
    B(p, -64, 1.8, 44.2, 4.2, 0.6, 1.6, STONE)
    ball(p, (-63.1, 4.5, 43.45), 0.25, ROSE, subdiv=0)
    for x in (-68.4, -59.6):
        B(p, x, 7.4, 43.0, 2.8, 2.8, 0.3, WHITE)
        B(p, x, 7.4, 43.15, 2.0, 2.0, 0.3, SKY)
        B(p, x, 7.4, 43.4, 0.2, 2.0, 0.2, WHITE)
        B(p, x, 7.4, 43.4, 2.0, 0.2, 0.2, WHITE)
        B(p, x - 1.7, 7.4, 43.3, 0.7, 2.8, 0.25, ROSE)
        B(p, x + 1.7, 7.4, 43.3, 0.7, 2.8, 0.25, ROSE)
        B(p, x, 5.7, 43.7, 2.8, 0.55, 0.9, WOOD)
        for dx in (-0.8, 0, 0.8):
            ball(p, (x + dx, 6.2, 43.8), 0.35, PINK if dx else SUN, subdiv=0)
    B(p, -60, 15.4, 36, 1.6, 3.0, 1.6, STONE)
    B(p, -60, 17.0, 36, 2.0, 0.4, 2.0, DSTONE)
    puff(p, -60, 17.9, 36, 1.8, 1.4, 1.8, WHITE)
    puff(p, -59.4, 19.0, 36.2, 1.3, 0.9, 1.3, WHITE)


# ---- 14. Pavilion ---------------------------------------------------------------------------------------------------------
def build_Pavilion(p):
    vcyl(p, -58, 0, 1.0, 16, 6.5, MARBLE, verts=14)
    vcyl(p, -58, 0.8, 1.0, 16, 6.7, STONE, verts=14)
    cols = [(-58, 21.2), (-53.5, 18.6), (-53.5, 13.4), (-58, 10.8), (-62.5, 13.4), (-62.5, 18.6)]
    for (x, z) in cols:
        vcol(p, x, z, 1.0, 9.9, 0.55, MARBLE, verts=8)
    for (a, b) in zip(cols, cols[1:] + cols[:1]):
        bar(p, (a[0], 9.55, a[1]), (b[0], 9.55, b[1]), 0.7, GOLD, 0.03)
    vcyl(p, -58, 9.9, 10.6, 16, 6.75, ROSE, verts=12)
    vcyl(p, -58, 10.6, 13.1, 16, 6.2, PINK, verts=12, top_r=1.5)
    vcyl(p, -58, 10.6, 11.2, 16, 6.4, ROSE, verts=12)
    vcyl(p, -58, 11.9, 12.3, 16, 4.0, ROSE, verts=12)
    vcyl(p, -58, 13.1, 13.4, 16, 1.2, GOLD, verts=8)
    ball(p, (-58, 13.9, 16), 0.8, GOLD, subdiv=1)
    vcyl(p, -58, 1.0, 2.2, 16, 1.2, STONE, verts=10)
    vcyl(p, -58, 2.2, 2.5, 16, 1.5, MARBLE, verts=10)
    ball(p, (-58, 3.5, 16), 0.9, SUN, subdiv=1)
    for k in range(6):                                                         # petals on the floor
        a = math.radians(30 + 60 * k)
        ball(p, (-58 + 4.6 * math.cos(a), 1.15, 16 + 4.6 * math.sin(a)), 0.4, PINK, scale=(1, 0.5, 1), subdiv=0)


# ---- 15. RuinColumns ------------------------------------------------------------------------------------------------------
def build_RuinColumns(p):
    B(p, 62, 0.4, -4, 15, 0.8, 9, STONE)
    B(p, 62, 0.75, -4, 13.4, 0.2, 7.6, DSTONE, jit=0.05)
    for x in (55, 63):
        vcol(p, x, -4, 0.8, 12.8, 1.1, MARBLE, verts=10)
        vcyl(p, x, 4.6, 4.8, -4, 1.25, STONE, verts=10)                         # drum joints
        vcyl(p, x, 8.6, 8.8, -4, 1.25, STONE, verts=10)
    B(p, 59, 13.4, -4, 11, 1.4, 2.4, MARBLE)
    B(p, 59, 12.78, -4, 11.4, 0.3, 2.8, STONE)
    B(p, 63.4, 14.35, -4.2, 2.6, 0.7, 1.6, MARBLE, rot=(0, 20, 8))             # chipped bit on the lintel
    # broken columns
    vcyl(p, 67, 0.8, 6.6, -2, 1.1, MARBLE, verts=10)
    B(p, 67.0, 7.0, -2, 1.6, 0.9, 1.2, MARBLE, rot=(0, 25, 12))
    vcyl(p, 70, 0.8, 4.2, -6, 1.1, MARBLE, verts=10)
    B(p, 70.2, 4.6, -6, 1.3, 0.7, 1.0, MARBLE, rot=(0, -20, -14))
    vcyl(p, 67, 0.8, 1.4, -2, 1.5, STONE, verts=10)
    # fallen column drums
    for k, dx in enumerate((-3.0, 0.0, 3.1)):
        a = math.radians(25)
        cx, cz = 60 + dx * math.cos(a), 0 - dx * math.sin(a)
        dk.cyl(p, (cx, 1.7, cz), 1.1, 2.7, MARBLE, axis='x', verts=10, rot=(0, 25, 0), jitter=0.04)
    B(p, 69, 1.1, 1, 2.6, 1.6, 2.6, STONE, rot=(0, 30, 0))
    B(p, 54, 1, -8, 2, 1.4, 2.4, STONE, rot=(0, -20, 0))
    for (x, z, s) in ((57.5, -6.6, 1.1), (65.2, -1.2, 1.4), (61.2, -6.0, 0.9)):
        puff(p, x, 1.0, z, s * 2, s * 0.8, s * 1.6, MINT, jit=0.08)             # moss tufts


# ---- 16. CloudPond --------------------------------------------------------------------------------------------------------
def build_CloudPond(p):
    edisc(p, 6, 0.3, 0.6, 15, 8, 8, SKY, n=16)
    edisc(p, 7, 0.3, 0.6, 15, 6, 9.5, SKY, n=16)
    edisc(p, 6.5, 0.6, 0.64, 15, 5.4, 6.8, LSKY, n=14)
    for (x, z, sx, sz) in ((-0.5, 15, 4, 3.6), (6, 22, 4.4, 3.4), (12.5, 14, 3.8, 3.6), (4, 8.5, 3.6, 3.2)):
        puff(p, x, 1.0, z, sx, 2.0 if sz > 3.2 else 1.8, sz, WHITE)
    for (x, z, c) in ((3, 12, PINK), (9, 17.5, LAV)):
        vcyl(p, x, 0.6, 0.78, z, 1.2, MINT, verts=8)
        ball(p, (x + 0.1, 0.95, z), 0.4, c, subdiv=0)
    # arch bridge
    B(p, 1, 1.3, 15, 2, 2.6, 3.2, MARBLE)
    B(p, 11, 1.3, 15, 2, 2.6, 3.2, MARBLE)
    B(p, 6, 2.6, 15, 12, 0.8, 3.2, MARBLE)
    arc_strip(p, 6, 0.4, 4.2, 2.0, 3.3, 1.4, 13.5, 16.5, STONE, n=8)
    for z in (13.5, 16.5):
        B(p, 6, 3.7, z, 12, 0.7, 0.5, GOLD)
        for x in (0.5, 3.5, 6, 8.5, 11.5):
            B(p, x, 3.2, z, 0.4, 0.5, 0.4, DGOLD, jit=0.02)
    for (x, z) in ((-1.5, 18.5), (13.0, 11.0), (2.0, 21.0)):                   # reeds
        for k in range(2):
            B(p, x + k * 0.5, 1.4, z + k * 0.3, 0.14, 1.9, 0.14, GREEN, jit=0.02)
        B(p, x, 2.5, z, 0.35, 0.8, 0.35, DWOOD, jit=0.02)


# ---- 17. Banners ----------------------------------------------------------------------------------------------------------
def banner_pole(p, x, z, ph, flag_col, deg, fy, fh=3.0, fw=4.6):
    vcyl(p, x, 0, 1.0, z, 1.1, STONE, verts=10)
    vcyl(p, x, 1.0, 1.5, z, 0.8, MARBLE, verts=10)
    vcyl(p, x, 0.5, 0.5 + ph, z, 0.3, MARBLE, verts=8)
    vcyl(p, x, 2.2, 2.6, z, 0.5, GOLD, verts=8)
    ball(p, (x, 0.5 + ph + 0.4, z), 0.6, GOLD, subdiv=1)
    flag(p, x, z, fy, fw, fh, flag_col, deg)
    puff(p, x - 0.3, 0.45, z + 0.3, 3.4, 0.9, 3.0, WHITE)


def build_Banners(p):
    banner_pole(p, 29, 36, 12, SKY, 20, 11.6)
    banner_pole(p, 36, 33, 10, GOLD, -22, 9.8)
    banner_pole(p, 43, 27, 11, PINK, 14, 10.8)


# ---- 18. RainbowArch ------------------------------------------------------------------------------------------------------
def build_RainbowArch(p):
    cols = [RAIN1, RAIN2, RAIN3, RAIN4]
    z0, z1 = -44.2, -41.8
    for k, col in enumerate(cols):
        ao, bo = 13.2 - 1.2 * k, 4.8 - 1.2 * k
        arc_strip(p, -37, 9.0, ao, bo, ao - 1.2, bo - 1.2, z0, z1, col, n=12)
        bx(p, (-37 - ao, -37 - ao + 1.2), (0, 9.0), (z0, z1), col, 0.04)
        bx(p, (-37 + ao - 1.2, -37 + ao), (0, 9.0), (z0, z1), col, 0.04)
    for x in (-48.5, -25.5):
        puff(p, x, 1.1, -43, 5.4, 2.2, 4.4, WHITE)
        puff(p, x + (1.8 if x < -40 else -1.8), 0.8, -42.2, 3.4, 1.6, 3.0, CLOUD)
        puff(p, x + (-1.4 if x < -40 else 1.4), 0.7, -43.8, 3.0, 1.4, 2.8, WHITE)
    for k in range(3):
        sparkle4(p, (-41.5 + k * 4.5, 11.0 + (0.9 if k == 1 else 0), -41.6), 0.0 + 0.0 + 0.8, WHITE)


# ---- 19. WingsBackdrop ----------------------------------------------------------------------------------------------------
def big_wing(p, side):
    root = (20 + side * 1.2, 4.2)
    wing_shape(p, root[0], root[1], -26.35, side, 11.2, 9.6, 0.5, WHITE)
    wing_shape(p, root[0], root[1] + 0.2, -25.9, side, 8.2, 7.0, 0.5, CLOUD)
    wing_shape(p, root[0], root[1] + 0.4, -25.45, side, 5.2, 4.4, 0.5, WHITE)


def build_WingsBackdrop(p):
    B(p, 20, 0.5, -26, 22, 1.0, 3.4, CLOUD)
    for (x, w, d) in ((13, 5, 3.0), (20, 8, 3.6), (27, 6, 3.0), (9.5, 3, 2.4), (30.5, 3.4, 2.4)):
        puff(p, x, 1.3, -26, w, 1.6, d, WHITE)
    B(p, 20, 5.5, -26, 2.4, 9.0, 1.6, GOLD)
    B(p, 20, 1.6, -26, 3.4, 1.2, 2.6, DGOLD)
    B(p, 20, 9.4, -26, 3.0, 0.5, 2.2, DGOLD)
    ball(p, (20, 6.4, -25.0), 0.7, ROSE, subdiv=1)
    B(p, 20, 10.9, -26, 0.7, 1.8, 0.7, GOLD)
    halo(p, (20, 12.4, -26), 1.95, 0.3, GOLD, segs=16, sides=4)
    big_wing(p, 1)
    big_wing(p, -1)


# ---- 20. SkyTemple --------------------------------------------------------------------------------------------------------
def build_SkyTemple(p):
    bx(p, (8, 44), (0, 0.8), (-53, -31), STONE, 0.04)                       # three steps up to the platform
    bx(p, (9, 43), (0.8, 1.4), (-52.5, -31.6), MARBLE, 0.03)
    bx(p, (10, 42), (1.4, 2.0), (-52, -32.2), STONE, 0.03)
    for x in (12, 17.6, 23.2, 28.8, 34.4, 40):
        vcyl(p, x, 2.0, 14.0, -34, 1.2, MARBLE, verts=10)
        vcyl(p, x, 2.0, 2.8, -34, 1.5, STONE, verts=10)
        vcyl(p, x, 13.2, 14.0, -34, 1.6, STONE, verts=10)
    bx(p, (10, 42), (14.0, 15.6), (-41, -31), MARBLE, 0.03)                  # architrave
    bx(p, (9.6, 42.4), (15.2, 15.6), (-41.4, -30.6), GOLD, 0.02)
    # pediment: marble triangle with a pink tympanum and a gold sun
    prism_z(p, [(9.6, 15.6), (42.4, 15.6), (26, 20.4)], -40.5, -31.4, MARBLE, 0.03)
    prism_z(p, [(12.8, 16.0), (39.2, 16.0), (26, 19.6)], -31.5, -31.1, PINK, 0.03)
    bar(p, (9.6, 15.6, -31.0), (26, 20.4, -31.0), 0.6, GOLD, 0.02)
    bar(p, (42.4, 15.6, -31.0), (26, 20.4, -31.0), 0.6, GOLD, 0.02)
    dk.cyl(p, (26, 17.6, -31.0), 1.5, 0.4, SUN, axis='z', verts=12, jitter=0.03)
    for k in range(8):
        a = math.radians(45 * k)
        B(p, 26 + 2.1 * math.cos(a), 17.6 + 2.1 * math.sin(a), -31.0, 0.5, 0.5, 0.4, GOLD, rot=(0, 0, math.degrees(a)), jit=0.02)
    ball(p, (26, 21.8, -36), 1.3, GOLD, subdiv=1)
    for x in (10.4, 41.6):
        ball(p, (x, 16.4, -36), 0.7, GOLD, subdiv=0)
    # cella
    bx(p, (13, 39), (2.0, 14.4), (-52, -42), CREAM, 0.04)
    bx(p, (12, 40), (14.2, 16.2), (-53, -41), GOLD, 0.03)
    bx(p, (14, 38), (16.2, 17.0), (-51.5, -42.5), DGOLD, 0.03)
    B(p, 26, 5.2, -41.8, 5, 6.4, 0.5, GOLD)
    B(p, 26, 5.2, -41.6, 6.0, 7.2, 0.3, MARBLE)
    for x in (17, 35):                                                          # pilasters + windows on the cella front
        B(p, x, 8.5, -41.8, 3.0, 4.0, 0.4, SKY)
        B(p, x, 8.5, -41.7, 3.8, 4.8, 0.3, MARBLE)
    puff(p, 14, 0.9, -31.9, 6, 1.8, 1.6, WHITE)
    puff(p, 38.5, 0.9, -31.9, 6, 1.8, 1.6, WHITE)


# ---- 21. StarLanterns -----------------------------------------------------------------------------------------------------
def star_lantern(p, x, z, ph, yl):
    vcyl(p, x, 0, 1.2, z, 1.2, STONE, verts=10)
    vcyl(p, x, 1.2, 1.7, z, 0.8, MARBLE, verts=10)
    vcyl(p, x, 1.0, 1.0 + ph, z, 0.4, MARBLE, verts=8)
    vcyl(p, x, 3.6, 4.1, z, 0.65, GOLD, verts=8)
    vcyl(p, x, 1.0 + ph - 0.4, 1.0 + ph, z, 0.65, GOLD, verts=8)
    B(p, x, 1.0 + ph + 0.35, z, 3.4, 0.7, 0.7, GOLD)
    star_poly(p, (x, yl, z - 0.55), 'xy', 1.5, 0.7, 0.7, DGOLD, n=5, rot0=90 + 36)
    star_poly(p, (x, yl, z), 'xy', 1.5, 0.62, 1.1, SUN, n=5, rot0=90)
    star_poly(p, (x, yl, z + 0.6), 'xy', 0.8, 0.36, 0.3, LGOLD, n=5, rot0=90)
    bx(p, (x - 0.35, x + 0.35), (yl - 0.35, yl + 0.35), (z - 0.5, z + 0.5), LGOLD, 0.02)
    puff(p, x + 0.3, 0.5, z - 0.3, 3.2, 1.0, 2.8, WHITE)


def build_StarLanterns(p):
    star_lantern(p, 53, -52, 12, 15.2)
    star_lantern(p, 60, -46, 9, 12.3)
    star_lantern(p, 49, -42, 8, 10.9)


# ---- 22. DawnGong ---------------------------------------------------------------------------------------------------------
def build_DawnGong(p):
    for x in (42, 50):
        B(p, x, 0.6, -8, 3, 1.2, 3, STONE)
        B(p, x, 1.3, -8, 3.4, 0.3, 3.4, MARBLE)
        vcyl(p, x, 1.2, 11.6, -8, 0.55, MARBLE, verts=8)
        vcyl(p, x, 1.2, 2.2, -8, 0.8, STONE, verts=8)
        ball(p, (x, 11.6, -8), 0.75, GOLD, subdiv=1)
        puff(p, x + (-0.9 if x < 46 else 0.9), 0.4, -7.2, 3.0, 0.9, 2.6, WHITE)
    B(p, 46, 11.6, -8, 10, 1.0, 1.2, GOLD)
    B(p, 46, 12.3, -8, 10.4, 0.3, 1.5, DGOLD)
    for x in (44.4, 47.6):
        B(p, x, 10.7, -8, 0.14, 1.0, 0.14, DWOOD, jit=0.02)
    dk.cyl(p, (46, 7.2, -8.4), 3.8, 0.4, STONE, axis='z', verts=20, jitter=0.03)
    dk.cyl(p, (46, 7.2, -8.0), 3.3, 0.6, GOLD, axis='z', verts=20, jitter=0.03)
    dk.cyl(p, (46, 7.2, -7.7), 2.4, 0.2, DGOLD, axis='z', verts=16, jitter=0.03)
    dk.cyl(p, (46, 7.2, -7.55), 1.5, 0.3, SUN, axis='z', verts=12, jitter=0.03)
    B(p, 51.4, 1.6, -5, 0.5, 3.2, 0.5, WOOD, rot=(0, 0, 20))
    ball(p, (51.95, 3.4, -5), 0.7, DWOOD, subdiv=1)
    sparkle4(p, (43.5, 10.0, -6.8), 0.8, SUN)


# ---- 23. CherubPerches ----------------------------------------------------------------------------------------------------
def cherub(p, x, z, y0, cw, ch, cd, bw, bh, hd, face):
    puff(p, x, y0 + ch / 2, z, cw, ch, cd, WHITE)
    by = y0 + ch + bh * 0.35
    ball(p, (x, by, z), 1.0, SKIN, scale=(bw / 2, bh / 2, bw / 2), subdiv=1, jit=0.04)
    hy = by + bh / 2 + hd * 0.35
    ball(p, (x, hy, z), hd / 2, SKIN, subdiv=1, jit=0.04)
    fx, fz = ry(0, 1, face)
    rx, rz = ry(1, 0, face)
    for s in (-1, 1):                                                      # cheeks
        ball(p, (x + fx * hd * 0.45 + rx * s * hd * 0.3, hy - hd * 0.05, z + fz * hd * 0.45 + rz * s * hd * 0.3), hd * 0.12, ROSE, subdiv=0)
        ball(p, (x + fx * hd * 0.47 + rx * s * hd * 0.2, hy + hd * 0.12, z + fz * hd * 0.47 + rz * s * hd * 0.2), hd * 0.07, DWOOD, subdiv=0)
        ball(p, (x + rx * s * bw * 0.52 + fx * 0.2, by + bh * 0.1, z + rz * s * bw * 0.52 + fz * 0.2), bw * 0.16, SKIN, subdiv=0)   # arms
        wing_y(p, x + rx * s * bw * 0.25, by + bh * 0.1, z - fz * 0.45 * bw, s, bw * 1.35, bh * 1.5, 0.4, face, tilt=22)
    torus(p, (x, hy + hd * 0.78, z), hd * 0.5, 0.11, GOLD, segs=10, sides=4)                  # little halo


def build_CherubPerches(p):
    cherub(p, -18, -18, 0, 6, 2.4, 5, 2.6, 3.0, 2.2, 0)
    cherub(p, -25, -22, 0, 6.4, 3.4, 5.4, 2.8, 3.2, 2.3, 70)
    cherub(p, -11, -25, 0, 5, 2.0, 4.4, 2.3, 2.6, 2.0, -55)


# ---- 24. HaloMonument -----------------------------------------------------------------------------------------------------
def build_HaloMonument(p):
    bx(p, (-34.5, -25.5), (0, 1.8), (-33, -27), STONE, 0.04)
    bx(p, (-34.7, -25.3), (1.6, 2.1), (-33, -27), MARBLE, 0.03)
    bx(p, (-33, -27), (2.1, 4.0), (-32, -28), MARBLE, 0.03)
    bx(p, (-33.3, -26.7), (3.8, 4.2), (-32.3, -27.7), GOLD, 0.03)
    vcyl(p, -30, 4.0, 16.0, -30, 1.5, MARBLE, verts=8, top_r=1.1)
    for y in (6.0, 9.5):
        vcyl(p, -30, y, y + 0.5, -30, 1.5 - (y - 4) * 0.033 + 0.2, GOLD, verts=8)
    for y in (7.4, 8.4):
        B(p, -30, y, -28.45, 0.6, 0.6, 0.15, ROSE, jit=0.02)
    halo(p, (-30, 19, -30), 5.65, 0.85, GOLD, segs=22, sides=4)
    dk.cyl(p, (-30, 19, -29.9), 4.7, 0.2, LSKY, axis='z', verts=20, jitter=0.03)
    for (gx, gy) in ((-30, 13.9), (-23.9, 19), (-36.1, 19), (-30, 24.1)):
        ball(p, (gx, gy, -29.3), 0.75, ROSE, subdiv=1)
    ball(p, (-30, 25.6, -30), 0.8, GOLD, subdiv=1)
    sparkle4(p, (-32.2, 20.4, -29.6), 1.1, WHITE)
    sparkle4(p, (-28.2, 17.4, -29.6), 0.7, WHITE)
    puff(p, -34, 0.3, -30.0, 2.6, 0.7, 2.0, WHITE)
    puff(p, -26, 0.3, -30.0, 2.6, 0.7, 2.0, WHITE)


# ---- 25. Observatory ------------------------------------------------------------------------------------------------------
def build_Observatory(p):
    cx, cz = 68, -42
    vcyl(p, cx, 0, 1.0, cz, 8.5, STONE, verts=16)
    vcyl(p, cx, 1.0, 9.0, cz, 6.5, CREAM, verts=16)
    vcyl(p, cx, 1.0, 1.8, cz, 6.9, MARBLE, verts=16)
    vcyl(p, cx, 8.9, 9.9, cz, 7.0, GOLD, verts=16)
    for k in range(6):                                                         # tall slit windows round the drum
        a = math.radians(30 + 60 * k + 15)
        if math.sin(a) > 0.95:
            continue
        wx, wz = cx + 6.45 * math.cos(a), cz + 6.45 * math.sin(a)
        dk.box(p, (wx, 5.2, wz), (1.3, 3.0, 0.4), SKY, rot=(0, -math.degrees(a) + 90, 0), jitter=0.03)
    ball(p, (cx, 9.5, cz), 1.0, ROSE, scale=(6.7, 5.5, 6.7), subdiv=2, jit=0.04)
    for k in range(6):                                                         # gold ribs over the dome
        a = math.radians(60 * k + 30)
        pts = []
        for j in range(5):
            t = math.radians(j * 20)
            r = 6.75 * math.cos(t)
            pts.append((cx + r * math.cos(a), 9.5 + 5.55 * math.sin(t), cz + r * math.sin(a)))
        for (a0, b0) in zip(pts, pts[1:]):
            bar(p, a0, b0, 0.3, GOLD, 0.02)
    B(p, cx, 5.0, -35.4, 3.0, 5.0, 0.5, GOLD)
    B(p, cx, 5.0, -35.55, 3.8, 5.8, 0.2, WHITE)
    B(p, cx, 1.4, -35.0, 4.6, 0.5, 1.6, STONE)
    B(p, cx, 11.5, -36.2, 1.6, 6.0, 1.0, SKY)                                  # the slit
    B(p, cx, 11.5, -36.0, 2.4, 6.8, 0.4, WHITE)
    t0, t1 = Vector((68.8, 10.6, -37.6)), Vector((71.6, 17.2, -37.6))                    # telescope poking out of the slit
    bar(p, tuple(t0), tuple(t1), 1.3, GOLD, 0.03)
    for f0, f1, th, col in ((0.18, 0.27, 1.7, DGOLD), (0.5, 0.58, 1.7, DGOLD), (0.84, 1.0, 1.9, DGOLD)):
        bar(p, tuple(t0 + (t1 - t0) * f0), tuple(t0 + (t1 - t0) * f1), th, col, 0.02)
    bar(p, tuple(t0 - (t1 - t0) * 0.12), tuple(t0), 0.7, DSTONE, 0.02)
    ball(p, tuple(t1 + (t1 - t0).normalized() * 0.05), 0.62, SKY, subdiv=1)
    B(p, 68.8, 10.0, -37.6, 2.4, 0.6, 1.8, DGOLD)
    B(p, 68.8, 9.4, -37.2, 0.6, 1.4, 0.6, GOLD)
    ball(p, (cx, 15.3, cz), 0.8, GOLD, subdiv=1)


# ---- 26. ChoirRiser -------------------------------------------------------------------------------------------------------
def singer(p, x, y0, z, rb=1.0, h=3.2):
    vcyl(p, x, y0, y0 + h, z, rb, WHITE, verts=8, top_r=rb * 0.55)
    vcyl(p, x, y0 + h - 0.35, y0 + h, z, rb * 0.62, GOLD, verts=8)
    ball(p, (x, y0 + h + 0.8, z), 0.9, SKIN, subdiv=1, jit=0.03)
    dk.box(p, (x, y0 + h + 0.55, z + 0.82), (0.3, 0.26, 0.2), DROSE, jitter=0.02)               # singing mouth
    for s in (-1, 1):
        ball(p, (x + s * 0.34, y0 + h + 1.0, z + 0.8), 0.14, DWOOD, subdiv=0)
    ball(p, (x, y0 + h + 1.55, z - 0.1), 0.5, SUN, scale=(1.4, 0.7, 1.4), subdiv=0)           # hair tuft
    dk.box(p, (x, y0 + h * 0.62, z + rb * 0.5), (rb * 1.0, 0.5, 0.55), WHITE, jitter=0.02)    # folded hands + hymnal
    dk.box(p, (x, y0 + h * 0.7, z + rb * 0.85), (0.9, 0.7, 0.14), CREAM, jitter=0.02)
    for s in (-1, 1):
        wing(p, x + s * 0.35, y0 + h * 0.55, z - rb * 0.8, s, 1.3, 1.9, 0.3, WHITE, tilt=16)


def build_ChoirRiser(p):
    for (cy, ch, cz, sx, sz, w) in ((0.6, 1.2, -30, 14, 8, 0), (1.8, 1.2, -32, 11, 5.5, 1), (3.0, 1.2, -33.5, 8, 3, 2)):
        B(p, 0, cy, cz, sx, ch, sz, MARBLE)
        B(p, 0, cy + 0.45, cz + sz / 2 + 0.05, sx + 0.2, 0.3, 0.3, GOLD, jit=0.02)
        B(p, 0, cy - 0.3, cz + sz / 2 + 0.02, sx - 0.4, 0.5, 0.2, STONE, jit=0.02)
    for (x, z) in ((-4, -31), (-0.6, -32), (2.8, -31)):
        singer(p, x, 2.4, z)
    singer(p, -2, 3.6, -33.5)
    B(p, 1, 2.6, -27, 0.25, 2.4, 0.25, GOLD)
    B(p, 1, 1.6, -27, 1.4, 0.3, 1.0, DGOLD)
    B(p, 1, 3.9, -27, 2.6, 0.3, 1.4, GOLD, rot=(-25, 0, 0))
    B(p, 1, 4.1, -27.25, 2.0, 0.1, 1.0, CREAM, rot=(-25, 0, 0), jit=0.02)
    puff(p, -5.8, 0.4, -27.4, 3.0, 0.8, 1.6, WHITE)
    puff(p, 5.6, 0.4, -27.4, 3.0, 0.8, 1.6, WHITE)


# ---- 27. HeavenBell -------------------------------------------------------------------------------------------------------
def build_HeavenBell(p):
    B(p, -14, 0.5, -37, 10, 1.0, 5, STONE)
    B(p, -14, 1.05, -37, 9.4, 0.2, 4.4, MARBLE)
    for x in (-17.4, -10.6):
        vcol(p, x, -37, 1.0, 11.0, 0.6, MARBLE, verts=8)
        vcyl(p, x, 6.0, 6.4, -37, 0.78, GOLD, verts=8)
    B(p, -14, 10.3, -37, 7.2, 0.6, 0.7, DGOLD)                                  # beam the bell hangs from
    frustum(p, -14, 10.7, 11.7, -37, 10.6, 3.6, 8.4, 3.0, ROSE)
    frustum(p, -14, 11.7, 13.0, -37, 6.0, 2.4, 3.0, 1.4, PINK)
    B(p, -14, 11.2, -35.1, 10.6, 0.3, 0.3, GOLD, jit=0.02)
    vcyl(p, -14, 8.4, 9.0, -37, 0.35, GOLD, verts=8)
    B(p, -14, 9.7, -37, 0.2, 1.2, 0.2, DGOLD, jit=0.02)
    vcyl(p, -14, 7.9, 8.4, -37, 1.4, GOLD, verts=10, top_r=0.6)                # crown of the bell
    vcyl(p, -14, 6.3, 7.9, -37, 1.9, GOLD, verts=10, top_r=1.4)
    vcyl(p, -14, 4.9, 6.3, -37, 2.2, GOLD, verts=10, top_r=1.9)
    vcyl(p, -14, 4.7, 5.0, -37, 2.35, DGOLD, verts=10)
    B(p, -14, 5.8, -34.7, 0.3, 0.8, 0.2, DGOLD, jit=0.02)
    B(p, -14, 5.8, -39.3, 0.3, 0.8, 0.2, DGOLD, jit=0.02)
    B(p, -14, 4.5, -37, 0.14, 1.2, 0.14, DSTONE, jit=0.02)
    ball(p, (-14, 4.3, -37), 0.7, STONE, subdiv=1)
    for s in (-1, 1):
        puff(p, -14 + s * 4.5, 0.5, -37, 2.2, 1.0, 3.0, WHITE)


# ---- 28. CloudThrone ------------------------------------------------------------------------------------------------------
def build_CloudThrone(p):
    vcyl(p, 52, 0, 1.6, -25, 5.5, WHITE, verts=16)
    vcyl(p, 52, 1.6, 2.6, -25, 4.0, MARBLE, verts=16)
    vcyl(p, 52, 1.5, 1.8, -25, 5.7, GOLD, verts=16)
    puff(p, 46.6, 1.2, -23, 5, 2.4, 4, WHITE)
    puff(p, 57.6, 1.0, -28, 4.6, 2.0, 4, WHITE)
    puff(p, 50.0, 0.8, -29.6, 4.0, 1.6, 3.0, CLOUD)
    wing_shape(p, 49.6, 5.4, -28.1, -1, 5.6, 7.6, 0.5, WHITE)
    wing_shape(p, 54.4, 5.4, -28.1, 1, 5.6, 7.6, 0.5, WHITE)
    wing_shape(p, 49.6, 5.6, -27.7, -1, 3.6, 4.8, 0.4, CLOUD)
    wing_shape(p, 54.4, 5.6, -27.7, 1, 3.6, 4.8, 0.4, CLOUD)
    B(p, 52, 3.9, -25, 5, 2.6, 4.6, GOLD)
    B(p, 52, 2.9, -22.65, 5.2, 0.5, 0.3, DGOLD, jit=0.02)
    B(p, 52, 5.0, -25, 4.0, 0.9, 3.6, ROSE)
    B(p, 52, 5.5, -25, 3.6, 0.3, 3.2, PINK, jit=0.03)
    B(p, 52, 8.0, -27, 5.4, 8.0, 1.0, GOLD)
    B(p, 52, 8.0, -26.4, 4.2, 6.4, 0.3, DGOLD)
    B(p, 52, 9.0, -26.2, 3.0, 4.0, 0.3, ROSE)
    for s in (-1, 1):
        B(p, 52 + s * 2.65, 5, -25, 0.7, 2.0, 4.0, GOLD)
        ball(p, (52 + s * 2.65, 6.3, -23.3), 0.55, LGOLD, subdiv=1)
        ball(p, (52 + s * 2.65, 12.0, -27), 0.45, GOLD, subdiv=0)
        vcyl(p, 52 + s * 2.2, 8.0, 12.0, -27, 0.28, DGOLD, verts=6)
    ball(p, (52, 12.6, -27), 0.9, GOLD, subdiv=1)
    ball(p, (52, 8.6, -26.0), 0.55, SKY, subdiv=1)


# ---- 29. SkySpire ---------------------------------------------------------------------------------------------------------
def build_SkySpire(p):
    cx, cz = -66, -22
    bx(p, (cx - 7.5, cx + 7.5), (0, 2.4), (cz - 7.5, cz + 7.5), STONE, 0.04)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        ball(p, (cx + sx * 6.7, 2.9, cz + sz * 6.7), 0.6, GOLD, subdiv=1)
    bx(p, (cx - 5.7, cx + 5.7), (2.4, 14.4), (cz - 5.7, cz + 5.7), MARBLE, 0.03)
    bx(p, (cx - 6.0, cx + 6.0), (2.4, 3.2), (cz - 6.0, cz + 6.0), STONE, 0.03)
    bx(p, (cx - 6.5, cx + 6.5), (14.4, 15.6), (cz - 6.5, cz + 6.5), GOLD, 0.03)
    bx(p, (cx - 4.4, cx + 4.4), (16, 36), (cz - 4.4, cz + 4.4), CREAM, 0.04)
    bx(p, (cx - 5.0, cx + 5.0), (15.6, 16.6), (cz - 5.0, cz + 5.0), MARBLE, 0.03)
    bx(p, (cx - 6.0, cx + 6.0), (35.6, 37.2), (cz - 6.0, cz + 6.0), GOLD, 0.03)
    bx(p, (cx - 3.8, cx + 3.8), (37.2, 46.4), (cz - 3.8, cz + 3.8), CLOUD, 0.04)
    bx(p, (cx - 5.0, cx + 5.0), (46.4, 47.6), (cz - 5.0, cz + 5.0), ROSE, 0.03)
    frustum(p, cx, 47.6, 51.2, cz, 6.4, 6.4, 1.0, 1.0, ROSE)
    vcyl(p, cx, 51.2, 55.0, cz, 0.55, GOLD, verts=8, top_r=0.1)
    ball(p, (cx, 51.9, cz), 0.7, GOLD, subdiv=1)
    # front door and windows (road side = +z), side windows on +-x
    B(p, cx, 5.4, cz + 5.75, 3.0, 6.0, 0.4, GOLD)
    B(p, cx, 5.4, cz + 5.7, 3.8, 6.6, 0.3, WHITE)
    B(p, cx, 8.9, cz + 6.0, 4.4, 0.5, 0.6, GOLD)
    for y in (19.5, 25.5, 31.5):
        B(p, cx, y, cz + 4.45, 2.0, 3.4, 0.3, WHITE)
        B(p, cx, y, cz + 4.55, 1.4, 2.8, 0.3, SKY)
        B(p, cx, y, cz + 4.7, 0.2, 2.8, 0.2, WHITE)
    for s in (-1, 1):
        for y in (22.5, 29.0):
            B(p, cx + s * 4.45, y, cz, 0.3, 3.4, 2.0, WHITE)
            B(p, cx + s * 4.55, y, cz, 0.3, 2.8, 1.4, SKY)
    # belfry openings with a gold bell
    for y in (41.8,):
        B(p, cx, y, cz + 3.85, 2.8, 5.6, 0.3, DSTONE)
        B(p, cx, y + 3.1, cz + 3.9, 3.4, 0.6, 0.4, GOLD)
        for s in (-1, 1):
            B(p, cx + s * 3.85, y, cz, 0.3, 5.6, 2.8, DSTONE)
            B(p, cx + s * 3.9, y + 3.1, cz, 0.4, 0.6, 3.4, GOLD)
    vcyl(p, cx, 40.6, 42.4, cz, 1.0, GOLD, verts=8, top_r=0.5)
    star_poly(p, (cx, 12.0, cz + 5.8), 'xy', 1.3, 0.55, 0.3, GOLD, n=5)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        B(p, cx + sx * 4.4, 26.0, cz + sz * 4.4, 0.9, 20.0, 0.9, MARBLE, jit=0.03)                    # corner pilasters
        ball(p, (cx + sx * 4.9, 47.9, cz + sz * 4.9), 0.55, GOLD, subdiv=1)                         # roof corner finials
    for y in (22.6, 28.4, 34.2):
        bx(p, (cx - 4.75, cx + 4.75), (y, y + 0.4), (cz - 4.75, cz + 4.75), GOLD, 0.02)              # gold belts round the shaft
    puff(p, -70, 1.4, -17, 6, 2.8, 5, WHITE)
    puff(p, -61.5, 1.2, -27, 5, 2.4, 4.4, WHITE)


# ---- 30. Stairway ---------------------------------------------------------------------------------------------------------
def build_Stairway(p):
    puff(p, 70, 1.2, -22, 8, 2.4, 7, WHITE)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        puff(p, 70 + 3.9 * math.cos(a), 0.9, -22 + 3.4 * math.sin(a), 3.6, 1.8, 3.2, WHITE if k % 2 else CLOUD)
    vcyl(p, 70, 0.5, 22, -22, 0.6, GOLD, verts=8)
    for y in (4.5, 9.0, 13.5, 18.0):
        vcyl(p, 70, y, y + 0.4, -22, 0.85, DGOLD, verts=8)
    steps = [(72.8, 1.6, -22, 0), (72.2, 3.4, -19.4, 60), (70, 5.2, -17.8, 120), (67.4, 7, -17.8, 180), (65.2, 8.8, -19.4, 240),
             (64.4, 10.6, -22, 300), (65.2, 12.4, -24.6, 0), (67.4, 14.2, -26.2, 60), (70, 16, -26.2, 120), (72.2, 17.8, -24.6, 180)]
    for i, (x, y, z, r) in enumerate(steps):
        dk.box(p, (x, y, z), (4.6, 0.9, 2.6), MARBLE, rot=(0, r, 0), jitter=0.03)
        a, b = ry(2.2, 0, r)
        dk.box(p, (x + a, y + 0.1, z + b), (0.3, 0.7, 2.7), GOLD, rot=(0, r, 0), jitter=0.02)
        a, b = ry(-0.3, 0, r)
        puff(p, x + a, y - 0.85, z + b, 3.6, 1.0, 2.2, WHITE if i % 2 else CLOUD, subdiv=0, jit=0.04, rot=(0, r, 0))
    puff(p, 70, 23.4, -22, 5, 3.4, 5, WHITE)
    puff(p, 68.4, 22.4, -23.4, 3.4, 2.2, 3.0, CLOUD)
    ball(p, (70, 25.0, -22), 0.8, GOLD, subdiv=1)
    sparkle4(p, (73.5, 21.0, -20.0), 1.0, SUN)
    sparkle4(p, (66.5, 19.5, -23.5), 0.8, SUN)


PART_IDS = ["Ground", "PearlyGate", "HeavenSign", "CloudMounds", "GoldenLamps", "WishingWell", "FlowerBeds", "CloudFountain",
            "CloudTrees", "Benches", "AngelStatues", "HarpGarden", "CloudCottage", "Pavilion", "RuinColumns", "CloudPond",
            "Banners", "RainbowArch", "WingsBackdrop", "SkyTemple", "StarLanterns", "DawnGong", "CherubPerches", "HaloMonument",
            "Observatory", "ChoirRiser", "HeavenBell", "CloudThrone", "SkySpire", "Stairway"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

AZ = {"PearlyGate": 100}
ELEV = {}
MULT = {"Ground": 1.7, "SkySpire": 2.6, "SkyTemple": 2.2}
SHIBA_AT = {"Ground": (20, -14, 270, 0)}


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
            x = hi[0] + 5 if hi[0] + 5 < 76 else lo[0] - 5
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_CloudTemple.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
