"""Final low-poly decor models for the theme Observatory (30 parts around the 24th Shiba, Galaxy Shiba).

Usage: blender --background --factory-startup --python build_Observatory.py -- <outdir> [PartId,PartId ...]
Writes Decor_Observatory_<PartId>.fbx, preview_<PartId>.png and stage_Observatory.png into <outdir>.
Every model is built in the stage frame at the position of its part (y up, +z toward the road), then fitted to the union box of its
blueprint pieces (same footprint, same height). Give part ids after the out folder (one argument,
comma separated, or several arguments) to rebuild only those parts (no stage render then). Models are built WITHOUT the part's Yaw.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "Observatory"))
ONLY = [a for arg in ARGS[1:] for a in arg.split(",") if a]
KEY = "Observatory"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_Observatory.json"))

# ---- palette (one for all 30 parts) ---------------------------------------------------------------------------------
NAVY = (24, 30, 70)
DNAVY = (16, 20, 48)
PAVE = (44, 50, 92)
INDIGO = (60, 66, 140)
PURPLE = (118, 86, 186)
DPURPLE = (84, 58, 140)
LILAC = (170, 146, 226)
SILVER = (200, 206, 222)
LSILVER = (226, 230, 242)
STEEL = (128, 138, 160)
DSTEEL = (86, 94, 116)
DARK = (46, 50, 72)
BRASS = (196, 146, 58)
DBRASS = (150, 108, 40)
GOLD = (246, 204, 76)
WHITE = (238, 240, 250)
TEAL = (72, 190, 204)
DTEAL = (40, 130, 150)
MOSS = (58, 112, 98)
LMOSS = (80, 140, 112)
STONE = (146, 150, 168)
DSTONE = (112, 116, 134)
ROCK = (86, 80, 100)
COPPER = (190, 108, 72)
RED = (212, 72, 76)
CREAM = (236, 224, 198)
WOOD = (122, 86, 60)
DWOOD = (90, 62, 44)
SOLAR = (50, 90, 190)
PINK = (236, 150, 180)
LANT = (255, 226, 150)
LGOLD = (252, 226, 130)
AMBERC = (226, 170, 40)


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def cb(p, c, s, col, jit=0.04, rot=(0, 0, 0)):
    """Box from centre and size."""
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


def ry(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


def rod(p, a, b, r, col, verts=8, r2=None, jit=0.04):
    """Round bar (or cone frustum) from stage point a to stage point b, radius r at a, r2 at b."""
    a, b = Vector(S(*a)), Vector(S(*b))
    d = b - a
    ln = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r, radius2=r if r2 is None else r2,
                          depth=ln)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    return dk._object(p, "Rod", bm, (a + b) / 2, (0, 0, 0), col, jit)


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


def dome(p, cx, y0, cz, rx, h, col, rz=None, seg=16, rings=4, jit=0.03, cut=None):
    """Hemisphere (squashed to height h) standing on y0. cut = (a0, a1): degrees of azimuth to leave out (an open slit)."""
    rz = rx if rz is None else rz
    pts, faces = [], []
    for j in range(rings + 1):
        el = (math.pi / 2) * j / rings
        rr = math.cos(el)
        yy = h * math.sin(el)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            pts.append((rx * rr * math.cos(a), yy, rz * rr * math.sin(a)))
    top = len(pts)
    pts.append((0, h, 0))
    for j in range(rings):
        for i in range(seg):
            i2 = (i + 1) % seg
            a, b = j * seg + i, j * seg + i2
            if j == rings - 1:
                faces.append((a, b, top))
            else:
                faces.append((a, b, b + seg, a + seg))
    return dk.poly(p, (cx, y0, cz), pts, faces, col, jit)


def ring(p, c, R, r, col, axis='y', segs=18, sides=6, jit=0.03, rot=(0, 0, 0)):
    """Torus: major radius R, tube radius r, axis 'y' (flat), 'z' (standing, faces the road) or 'x'."""
    pts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(sides):
            b = 2 * math.pi * j / sides
            rr = R + r * math.cos(b)
            u, v, w = rr * math.cos(a), r * math.sin(b), rr * math.sin(a)
            if axis == 'y':
                pts.append((u, v, w))
            elif axis == 'z':
                pts.append((u, w, v))
            else:
                pts.append((v, u, w))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2))
    return dk.poly(p, c, pts, faces, col, jit, rot=rot)


def star_poly(p, c, plane, ro, ri, thick, col, n=5, rot0=90, jit=0.03):
    """Flat n-pointed star around centre c. plane: 'xy' (faces +z), 'xz' (lies flat), 'yz' (faces +x)."""
    cx, cy, cz = c
    rg = []
    for k in range(2 * n):
        a = math.radians(rot0) + k * math.pi / n
        r = ro if k % 2 == 0 else ri
        rg.append((r * math.cos(a), r * math.sin(a)))

    def at(a, b, d):
        if plane == 'xy':
            return (cx + a, cy + b, cz + d)
        if plane == 'xz':
            return (cx + a, cy + d, cz + b)
        return (cx + d, cy + a, cz + b)
    h = thick / 2
    pts = [at(a, b, h) for a, b in rg] + [at(a, b, -h) for a, b in rg] + [at(0, 0, h), at(0, 0, -h)]
    m = 2 * n
    faces = []
    for k in range(m):
        q = (k + 1) % m
        faces += [(2 * m, k, q), (2 * m + 1, m + q, m + k), (k, m + k, m + q, q)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


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
    if ch == 'B':
        r(0, 0, t, h); r(0, h - t, w - t * 0.6, h); r(0, h / 2 - t / 2, w - t * 0.3, h / 2 + t / 2); r(0, 0, w - t * 0.6, t)
        r(w - t, h / 2, w, h - t * 0.5); r(w - t, t * 0.5, w, h / 2)
    elif ch == 'R':
        r(0, 0, t, h); r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(w - t, h / 2, w, h - t)
        dg(t * 0.6, h / 2, w - t * 0.4, t * 0.3)
    elif ch == 'O':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'E':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2); r(t, 0, w, t)
    elif ch == 'A':
        r(0, 0, t, h - t); r(w - t, 0, w, h - t); r(0, h - t, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'T':
        r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h - t)
    elif ch == 'S':
        r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(0, 0, w, t); r(0, h / 2, t, h - t); r(w - t, t, w, h / 2)
    elif ch == 'V':
        dg(t * 0.5, h, w / 2, t * 0.4)
        dg(w - t * 0.5, h, w / 2, t * 0.4)
    elif ch == 'Y':
        dg(t * 0.5, h, w / 2, h * 0.45)
        dg(w - t * 0.5, h, w / 2, h * 0.45)
        r(w / 2 - t / 2, 0, w / 2 + t / 2, h * 0.5)


def text(p, s, cx, y0, z0, z1, w, h, t, gap, col, mirror=False):
    """Row of block letters centred on cx."""
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
    sc = [(th[i] - tl[i]) / (bh[i] - bl[i]) for i in range(3)]
    print(f"BOX {part.id}: target {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f}  built {bh.x-bl.x:.1f} x {bh.z-bl.z:.1f} x {bh.y-bl.y:.1f}"
          f"  scale x{sc[0]:.2f} y{sc[2]:.2f} z{sc[1]:.2f}")
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)


def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s, o, r = q["Size"], q["Offset"], q.get("Rotation") or (0, 0, 0)
        shape = q.get("Shape") or ""
        cyl = "Cylinder" in shape
        rx, ry_, rz = (math.radians(a) for a in r)
        R = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry_, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append(R @ Vector((sx * s[0] / 2, sy * s[1] / 2, sz * s[2] / 2)))
        if "Ball" in shape or cyl:
            ext = [0, 0, 0]
            for i in range(3):
                if "Ball" in shape:
                    ext[i] = math.sqrt(sum((R[i][j] * s[j] / 2) ** 2 for j in range(3)))
                else:
                    ext[i] = abs(R[i][0]) * s[0] / 2 + math.sqrt(R[i][1] ** 2 + R[i][2] ** 2) * s[1] / 2
        else:
            ext = [max(abs(v[i]) for v in pts) for i in range(3)]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - ext[i])
            hi[i] = max(hi[i], o[i] + ext[i])
    return lo, hi


# ==== PARTS ====
REG = {}


def part(pid):
    def deco(fn):
        REG[pid] = fn
        return fn
    return deco


def along(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def L(cx, cz, yaw, lx, lz):
    """Local (lx, lz) of something turned by yaw about (cx, cz) -> stage x, z."""
    dx, dz = ry(lx, lz, yaw)
    return cx + dx, cz + dz


def rl(cx, cy, lx, ly, deg):
    """Point (lx, ly) in the frame of something turned by deg about z at (cx, cy) -> stage x, y."""
    a = math.radians(deg)
    return cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a)


def prism_yz(p, x0, x1, tri, col, jit=0.04):
    """Triangular prism with the triangle (z, y) x3 in the y-z plane, from x0 to x1."""
    pts = [(x0, y, z) for z, y in tri] + [(x1, y, z) for z, y in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def disc(p, cx, y0, y1, cz, r, col, verts=16, top_r=None, jit=0.04):
    return vcyl(p, cx, y0, y1, cz, r, col, verts=verts, top_r=top_r, jit=jit)


# ---- 1. Ground ---------------------------------------------------------------------------------------------------------
@part("Ground")
def build_Ground(p):
    SEAM = (60, 68, 116)
    bx(p, (-80, 80), (0, 0.3), (-57.5, 57.5), PAVE, 0.05)
    for x in range(-70, 80, 20):
        bx(p, (x - 0.12, x + 0.12), (0.3, 0.34), (-56.5, 56.5), SEAM, 0.02)
    for z in range(-50, 60, 20):
        bx(p, (-79, 79), (0.3, 0.34), (z - 0.12, z + 0.12), SEAM, 0.02)
    for a, c in (((-80, 80), (-57.5, -56.3)), ((-80, 80), (56.3, 57.5)), ((-80, -78.8), (-56.3, 56.3)), ((78.8, 80), (-56.3, 56.3))):
        bx(p, a, (0.3, 0.4), c, INDIGO, 0.03)
    lawns = [((-77, -43), (37, 55)), ((29, 59), (44, 56)), ((45, 71), (-38, -18)), ((-5, 25), (3, 25))]
    for (x0, x1), (z0, z1) in lawns:
        bx(p, (x0, x1), (0.3, 0.5), (z0, z1), (66, 126, 104), 0.05)
        for a, c in (((x0 - 0.6, x1 + 0.6), (z0 - 0.6, z0)), ((x0 - 0.6, x1 + 0.6), (z1, z1 + 0.6)),
                     ((x0 - 0.6, x0), (z0, z1)), ((x1, x1 + 0.6), (z0, z1))):
            bx(p, a, (0.3, 0.58), c, STONE, 0.04)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        for k, (dx, dz, s) in enumerate(((-0.28, -0.15, 1.6), (0.2, 0.18, 1.3), (0.0, -0.3, 1.1))):
            cb(p, (cx + (x1 - x0) * dx, 0.53, cz + (z1 - z0) * dz), (s * 3.2, 0.06, s * 2.4), LMOSS, 0.06, rot=(0, 25 * k, 0))
        for k, (dx, dz) in enumerate(((0.3, -0.2), (-0.12, 0.25))):
            cb(p, (cx + (x1 - x0) * dx, 0.54, cz + (z1 - z0) * dz), (0.9, 0.08, 0.9), LILAC if k else WHITE, 0.05, rot=(0, 45, 0))
    # star medallion under the Shiba
    mx, mz = -34, -14
    disc(p, mx, 0.3, 0.38, mz, 17, INDIGO, 28)
    disc(p, mx, 0.38, 0.46, mz, 13, PURPLE, 28)
    disc(p, mx, 0.46, 0.52, mz, 9, NAVY, 24)
    star_poly(p, (mx, 0.55, mz), 'xz', 8.2, 3.4, 0.06, GOLD, n=5, rot0=90, jit=0.02)
    for k in range(12):
        a = math.radians(k * 30)
        cb(p, (mx + 15 * math.cos(a), 0.42, mz + 15 * math.sin(a)), (1.4, 0.1, 0.45), GOLD, 0.03, rot=(0, -k * 30, 0))
    # star dust on the paving
    for k, (x, z) in enumerate(((-70, 20), (-20, 30), (40, 30), (70, 10), (70, -50), (30, -50), (-10, -50), (-75, -30),
                                (-60, -8), (20, -8), (-42, 20), (0, -22), (75, 35), (52, 6), (-8, 50), (0, 38))):
        s = 0.9 if k % 3 else 1.4
        cb(p, (x, 0.38, z), (s, 0.12, s), LILAC if k % 2 else WHITE, 0.04, rot=(0, 45, 0))


# ---- 2. Sign -----------------------------------------------------------------------------------------------------------
@part("Sign")
def build_Sign(p):
    for px in (-50, -30):
        bx(p, (px - 1.5, px + 1.5), (0, 0.5), (52.5, 55.5), STONE, 0.04)
        bx(p, (px - 1.1, px + 1.1), (0.5, 0.9), (52.9, 55.1), DSTONE, 0.04)
        vcyl(p, px, 0.9, 9.0, 54, 0.7, DARK, verts=8)
        vcyl(p, px, 2.0, 2.8, 54, 0.95, BRASS, verts=8)
        vcyl(p, px, 8.6, 9.3, 54, 0.95, BRASS, verts=8)
        star_poly(p, (px, 10.2, 54), 'xy', 1.4, 0.65, 0.45, GOLD, jit=0.02)
    bx(p, (-51, -29), (5.7, 10.7), (53.5, 54.5), NAVY, 0.03)
    bx(p, (-51.3, -28.7), (5.55, 5.9), (53.3, 54.7), LILAC, 0.03)
    bx(p, (-51.3, -50.8), (5.55, 10.85), (53.3, 54.7), LILAC, 0.03)
    bx(p, (-29.2, -28.7), (5.55, 10.85), (53.3, 54.7), LILAC, 0.03)
    bx(p, (-51.3, -28.7), (10.85, 11.55), (53.2, 54.8), GOLD, 0.03)
    text(p, "OBSERVATORY", -40, 7.0, 54.5, 54.95, 1.5, 2.6, 0.45, 0.42, GOLD)
    for k in range(9):
        cb(p, (-47.4 + k * 2.2, 6.25, 54.6), (0.55, 0.55, 0.15), WHITE if k % 2 else LILAC, 0.03, rot=(0, 0, 45))


# ---- 3. Telescope ------------------------------------------------------------------------------------------------------
@part("Telescope")
def build_Telescope(p):
    bx(p, (9.5, 18.5), (0, 0.35), (41.5, 50.5), STONE, 0.04)
    bx(p, (10.3, 17.7), (0.35, 0.8), (42.3, 49.7), DSTONE, 0.04)
    bx(p, (12.4, 16.6), (0.2, 0.6), (50.5, 50.7), BRASS, 0.02)
    vcyl(p, 14.8, 0.8, 6.0, 46, 1.35, WHITE, verts=10, top_r=1.05)
    vcyl(p, 14.8, 1.6, 2.2, 46, 1.55, BRASS, verts=10)
    vcyl(p, 14.8, 5.2, 5.7, 46, 1.35, BRASS, verts=10)
    for z in (44.6, 47.0):
        bx(p, (14.0, 15.6), (5.9, 8.6), (z, z + 0.4), BRASS, 0.03)
    zcyl(p, 14.8, 7.9, 44.4, 47.6, 0.35, DBRASS, verts=8)
    A, B = (17.4, 6.1), (8.3, 12.4)
    rod(p, (A[0], A[1], 46), (B[0], B[1], 46), 1.05, WHITE, verts=10)
    for t in (0.18, 0.5, 0.8):
        a, b = along(A, B, t - 0.025), along(A, B, t + 0.025)
        rod(p, (a[0], a[1], 46), (b[0], b[1], 46), 1.2, BRASS, verts=10)
    a, b = along(A, B, 0.9), along(A, B, 1.0)
    rod(p, (a[0], a[1], 46), (b[0], b[1], 46), 1.4, STEEL, verts=10)
    a, b = along(A, B, 0.0), (A[0] + 0.9, A[1] - 0.6)
    rod(p, (A[0], A[1], 46), (b[0], b[1], 46), 0.45, BRASS, verts=8)
    n, d = (0.57, 0.82), (-0.82, 0.57)
    C = along(A, B, 0.55)
    Cf = (C[0] + n[0] * 1.9, C[1] + n[1] * 1.9)
    F0, F1 = (Cf[0] - d[0] * 2.7, Cf[1] - d[1] * 2.7), (Cf[0] + d[0] * 2.7, Cf[1] + d[1] * 2.7)
    rod(p, (F0[0], F0[1], 46), (F1[0], F1[1], 46), 0.42, BRASS, verts=8)
    rod(p, (F1[0], F1[1], 46), (F1[0] - 0.3, F1[1] - 0.0, 46), 0.62, DBRASS, verts=8)
    for t in (0.35, 0.75):
        c = along(A, B, t)
        cb(p, (c[0] + n[0] * 1.0, c[1] + n[1] * 1.0, 46), (0.3, 1.4, 0.3), DBRASS, 0.03, rot=(0, 0, -35))
    zcyl(p, 17.85, 4.9, 45.1, 46.9, 0.95, DARK, verts=8)
    rod(p, (15.6, 6.4, 46), (17.7, 5.0, 46), 0.28, STEEL, verts=6)


# ---- 4. Sundial --------------------------------------------------------------------------------------------------------
@part("Sundial")
def build_Sundial(p):
    cx, cz = -4, -28
    bx(p, (-8.5, 0.5), (0, 0.4), (-32.5, -23.5), STONE, 0.04)
    bx(p, (-7.3, -0.7), (0.4, 0.9), (-31.3, -24.7), DSTONE, 0.04)
    disc(p, cx, 0.9, 1.4, cz, 2.3, STONE, 8)
    disc(p, cx, 1.4, 2.7, cz, 1.3, DSTONE, 8, top_r=1.1)
    disc(p, cx, 2.7, 3.1, cz, 3.0, BRASS, 16)
    disc(p, cx, 3.1, 3.2, cz, 2.5, (226, 180, 84), 16)
    for k in range(12):
        a = math.radians(k * 30)
        cb(p, (cx + 2.05 * math.cos(a), 3.26, cz + 2.05 * math.sin(a)), (0.9 if k % 3 == 0 else 0.5, 0.12, 0.22), DARK, 0.02,
           rot=(0, -k * 30, 0))
    prism_yz(p, -3.95, -3.45, [(-30.2, 3.15), (-30.2, 5.5), (-27, 3.15)], GOLD, 0.03)
    for x, z in ((-7.8, -31.8), (-0.2, -31.8), (-7.8, -24.2), (-0.2, -24.2)):
        cb(p, (x, 0.62, z), (0.6, 0.45, 0.6), GOLD, 0.03, rot=(0, 45, 0))


# ---- 5. Lamps ----------------------------------------------------------------------------------------------------------
def lamp_at(p, x, z, y_lantern, y_top, wid=1.5):
    bx(p, (x - 0.7, x + 0.7), (0, 0.5), (z - 0.7, z + 0.7), STONE, 0.04)
    vcyl(p, x, 0.5, y_lantern, z, 0.3, DARK, verts=8)
    vcyl(p, x, 0.5, 1.1, z, 0.55, BRASS, verts=8, top_r=0.3)
    h = (y_top - y_lantern) * 0.72
    bx(p, (x - wid / 2 - 0.12, x + wid / 2 + 0.12), (y_lantern, y_lantern + 0.18), (z - wid / 2 - 0.12, z + wid / 2 + 0.12), BRASS, 0.03)
    bx(p, (x - wid / 2, x + wid / 2), (y_lantern + 0.18, y_lantern + h), (z - wid / 2, z + wid / 2), LANT, 0.03)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (x + sx * wid / 2 - 0.1, x + sx * wid / 2 + 0.1), (y_lantern, y_lantern + h + 0.1),
               (z + sz * wid / 2 - 0.1, z + sz * wid / 2 + 0.1), DBRASS, 0.02)
    dk.cone(p, (x, y_lantern + h, z), wid * 0.85, y_top - y_lantern - h, BRASS, verts=4, jitter=0.03)


@part("Lamps")
def build_Lamps(p):
    lamp_at(p, 29, 51.5, 6.2, 7.8, 1.4)
    lamp_at(p, 35, 55.5, 7.7, 9.5, 1.6)
    lamp_at(p, 41, 50.5, 5.6, 7.2, 1.4)
    lamp_at(p, 44.4, 54.5, 6.6, 8.2, 1.4)
    cx, cz, yw = 38.2, 52, 15
    for lx in (-2.0, 2.0):
        x, z = L(cx, cz, yw, lx, 0)
        cb(p, (x, 0.5, z), (0.8, 1.0, 1.3), STONE, 0.04, rot=(0, yw, 0))
    x, z = L(cx, cz, yw, 0, 0)
    cb(p, (x, 1.15, z), (5.0, 0.28, 1.4), WOOD, 0.06, rot=(0, yw, 0))
    x, z = L(cx, cz, yw, 0, -0.6)
    cb(p, (x, 1.95, z), (5.0, 0.7, 0.22), DWOOD, 0.06, rot=(0, yw, 0))
    for lx in (-2.0, 2.0):
        x, z = L(cx, cz, yw, lx, -0.6)
        cb(p, (x, 1.5, z), (0.3, 1.5, 0.3), STONE, 0.04, rot=(0, yw, 0))


# ---- 6. Rover ----------------------------------------------------------------------------------------------------------
@part("Rover")
def build_Rover(p):
    hexa(p, [(13.4, 1.5, -7.8), (18.6, 1.5, -7.8), (18.6, 1.5, -4.2), (13.4, 1.5, -4.2),
             (13.9, 3.3, -7.4), (18.1, 3.3, -7.4), (18.1, 3.3, -4.6), (13.9, 3.3, -4.6)], WHITE, 0.03)
    bx(p, (13.6, 18.4), (1.3, 1.7), (-7.6, -4.4), DSTEEL, 0.03)
    hexa(p, [(16.6, 3.3, -7.0), (18.1, 3.3, -7.0), (18.1, 3.3, -5.0), (16.6, 3.3, -5.0),
             (17.0, 4.3, -6.7), (17.7, 4.2, -6.7), (17.7, 4.2, -5.3), (17.0, 4.3, -5.3)], DTEAL, 0.03)
    bx(p, (14.2, 15.8), (3.3, 3.55), (-6.9, -6.0), STEEL, 0.03)
    bx(p, (13.8, 18.2), (2.6, 2.95), (-7.62, -7.5), TEAL, 0.02)
    bx(p, (13.8, 18.2), (2.6, 2.95), (-4.5, -4.38), TEAL, 0.02)
    for x in (13.8, 18.2):
        for z, hz in ((-8.3, -8.75), (-3.7, -3.35)):
            zcyl(p, x, 1.1, z - 0.4, z + 0.4, 1.1, DARK, verts=10, jit=0.03)
            zcyl(p, x, 1.1, min(hz, z), max(hz, z), 0.55, STEEL, verts=8, jit=0.03)
            zcyl(p, x, 1.1, hz - 0.03, hz + 0.03, 0.25, GOLD, verts=6, jit=0.02)
        bx(p, (x - 0.25, x + 0.25), (1.0, 1.6), (-7.9, -4.1), DSTEEL, 0.03)
    pc = (14.8, 4.0)
    dk.box(p, (pc[0], pc[1], -6), (3.8, 0.3, 3.2), SOLAR, rot=(0, 0, 10), jitter=0.03)
    for lx in (-0.9, 0.0, 0.9):
        x, y = rl(pc[0], pc[1], lx, 0.17, 10)
        dk.box(p, (x, y, -6), (0.12, 0.06, 3.2), LILAC, rot=(0, 0, 10), jitter=0.02)
    x, y = rl(pc[0], pc[1], 0, 0.17, 10)
    dk.box(p, (x, y, -6), (3.8, 0.06, 0.12), LILAC, rot=(0, 0, 10), jitter=0.02)
    for z in (-7.0, -5.0):
        bx(p, (14.0, 14.3), (3.3, 3.9), (z - 0.1, z + 0.1), STEEL, 0.03)
    vcyl(p, 17.6, 3.3, 6.2, -6.6, 0.2, STEEL, verts=6)
    bx(p, (17.2, 18.1), (5.7, 6.3), (-7.1, -6.1), DARK, 0.03)
    bx(p, (18.1, 18.25), (5.85, 6.15), (-6.9, -6.6), TEAL, 0.02)
    dk.cyl(p, (17.6, 6.55, -6.6), 1.0, 0.5, WHITE, axis='x', verts=10, top_radius=0.25, rot=(0, 0, 60), jitter=0.03)
    rod(p, (17.55, 6.5, -6.6), (17.9, 7.25, -6.6), 0.1, STEEL, verts=5)
    rod(p, (14.0, 3.3, -4.8), (14.0, 5.6, -4.8), 0.08, STEEL, verts=5)
    cb(p, (14.0, 5.7, -4.8), (0.3, 0.3, 0.3), RED, 0.03)
    for z in (-6.9, -5.1):
        cb(p, (18.65, 2.5, z), (0.2, 0.4, 0.4), GOLD, 0.02)
    rod(p, (18.4, 1.9, -6.0), (19.2, 1.0, -6.0), 0.18, DSTEEL, verts=6)


# ---- 7. Loungers -------------------------------------------------------------------------------------------------------
def lounger(p, cx, cz, yw, cush):
    def at(lx, lz, y, size, col, jit=0.05, tilt=0):
        x, z = L(cx, cz, yw, lx, lz)
        cb(p, (x, y, z), size, col, jit, rot=(0, yw, tilt))
    for lx in (-2.1, 2.1):
        for lz in (-0.85, 0.85):
            at(lx, lz, 0.3, (0.3, 0.6, 0.3), DWOOD)
    for lz in (-1.0, 1.0):
        at(0, lz, 0.8, (4.8, 0.4, 0.28), DWOOD)
    for k in range(5):
        at(-1.9 + k * 0.95, 0, 1.1, (0.8, 0.2, 2.2), WOOD, 0.08)
    at(0.5, 0, 1.38, (3.3, 0.36, 1.9), cush, 0.04)
    for lx in (-0.4, 1.4):
        at(lx, 0, 1.58, (0.4, 0.06, 1.95), LILAC, 0.03)
    hx, hy = -2.4, 1.4
    t = 38
    cxb, cyb = hx - 1.1 * math.cos(math.radians(t)), hy + 1.1 * math.sin(math.radians(t))
    at(cxb, 0, cyb, (2.2, 0.28, 2.1), DWOOD, 0.05, tilt=-t)
    ox, oy = rl(0, 0, 0, 0.3, -t)
    at(cxb + ox, 0, cyb + oy, (2.0, 0.3, 1.8), cush, 0.04, tilt=-t)
    at(cxb + ox - 0.4, 0, cyb + oy + 0.3, (0.7, 0.3, 1.2), LILAC, 0.04, tilt=-t)
    at(-2.9, 0, 0.7, (0.25, 1.4, 0.25), DWOOD)


@part("Loungers")
def build_Loungers(p):
    lounger(p, -38.6, 6.5, 22, PURPLE)
    lounger(p, -33.8, 4.4, -14, INDIGO)
    lounger(p, -29.0, 7.2, 30, PURPLE)
    vcyl(p, -33.4, 0, 1.5, 8.6, 0.9, STONE, verts=8)
    vcyl(p, -33.4, 1.5, 1.7, 8.6, 1.05, DSTONE, verts=8)
    vcyl(p, -33.6, 1.7, 2.15, 8.6, 0.25, WHITE, verts=8)
    star_poly(p, (-33.1, 1.75, 8.6), 'xz', 0.5, 0.22, 0.06, GOLD, jit=0.02)


# ---- 8. Cart -----------------------------------------------------------------------------------------------------------
@part("Cart")
def build_Cart(p):
    bx(p, (-39.5, -32.5), (0.5, 3.5), (42, 46), PURPLE, 0.04)
    bx(p, (-39.6, -32.4), (0.5, 1.1), (41.9, 46.1), DPURPLE, 0.03)
    bx(p, (-39.6, -32.4), (3.1, 3.5), (41.9, 46.1), DPURPLE, 0.03)
    bx(p, (-39.3, -32.7), (1.5, 2.9), (46.0, 46.12), INDIGO, 0.03)
    star_poly(p, (-36, 2.2, 46.18), 'xy', 1.05, 0.46, 0.14, GOLD, jit=0.02)
    for x in (-38.6, -33.4):
        cb(p, (x, 1.5, 46.18), (0.35, 0.35, 0.12), GOLD, 0.02, rot=(0, 0, 45))
        cb(p, (x, 2.9, 46.18), (0.35, 0.35, 0.12), GOLD, 0.02, rot=(0, 0, 45))
    bx(p, (-39.7, -32.3), (3.45, 3.95), (45.5, 46.7), CREAM, 0.03)
    for x in (-38.2, -36.6, -35.0):
        star_poly(p, (x, 4.05, 46.1), 'xz', 0.6, 0.27, 0.12, GOLD, jit=0.03)
    vcyl(p, -33.4, 3.95, 4.55, 46.3, 0.3, WHITE, verts=8, top_r=0.38)
    for x in (-38.6, -33.4):
        for z in (46.3, 41.7):
            zcyl(p, x, 0.9, z - 0.3, z + 0.3, 0.9, DARK, verts=10, jit=0.03)
            zcyl(p, x, 0.9, z - 0.34, z + 0.34, 0.4, STEEL, verts=8, jit=0.03)
    bx(p, (-38.9, -33.1), (0.7, 1.0), (41.9, 46.1), DSTEEL, 0.03)
    for x in (-39.2, -32.8):
        vcyl(p, x, 3.95, 6.8, 46.4, 0.2, STEEL, verts=6)
        vcyl(p, x, 3.5, 6.2, 42.4, 0.2, STEEL, verts=6)
    for k in range(6):
        x0 = -39.5 + k * 1.2
        col = RED if k % 2 == 0 else WHITE
        dk.box(p, (x0 + 0.6, 7.0, 45.6), (1.2, 0.35, 3.4), col, rot=(14, 0, 0), jitter=0.03)
        bx(p, (x0 + 0.05, x0 + 1.15), (5.9, 6.5), (47.15, 47.3), col, 0.03)
    for x in (-37.4, -34.6):
        cb(p, (x, 6.1, 45.6), (0.4, 0.4, 0.4), GOLD, 0.03, rot=(0, 45, 0))
    bx(p, (-38.4, -36.6), (3.95, 5.7), (42.2, 43.8), STEEL, 0.04)
    bx(p, (-38.3, -36.7), (4.4, 5.2), (43.8, 43.95), DARK, 0.03)
    bx(p, (-38.0, -37.0), (5.7, 6.2), (42.5, 43.5), GOLD, 0.03)
    cb(p, (-37.5, 4.2, 44.1), (0.3, 0.4, 0.3), BRASS, 0.03)
    cb(p, (-35.2, 4.3, 43.0), (0.8, 0.7, 0.8), WHITE, 0.03)


import random


def rockb(p, c, r, col, scale=(1, 1, 1), seed=1, jag=0.22, subdiv=1, rot=(0, 0, 0), jit=0.06):
    """Faceted boulder: an ico sphere with every vertex pushed in or out a little."""
    o = dk.ball(p, c, r, col, scale=scale, subdiv=subdiv, rot=rot, jitter=jit)
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co *= 1 + (rnd.random() - 0.5) * 2 * jag
    o.data.update()
    return o


def stone(p, cx, cz, yaw, w, d, h, col, taper=0.78, lean=(0, 0), jit=0.05, y0=0.0):
    """Tapered slab: w x d at the bottom, taper times that at the top (leaning by `lean`), turned by yaw."""
    def pt(lx, lz, y):
        x, z = ry(lx, lz, yaw)
        return (cx + x, y, cz + z)
    bw, bd, tw, td = w / 2, d / 2, w / 2 * taper, d / 2 * taper
    bot = [pt(-bw, -bd, y0), pt(bw, -bd, y0), pt(bw, bd, y0), pt(-bw, bd, y0)]
    top = [pt(-tw + lean[0], -td + lean[1], y0 + h), pt(tw + lean[0], -td + lean[1], y0 + h),
           pt(tw + lean[0], td + lean[1], y0 + h), pt(-tw + lean[0], td + lean[1], y0 + h)]
    return hexa(p, bot + top, col, jit)


def crystal(p, x, z, y0, h, r, col, tilt=(0, 0), yaw=0, tip=0.3, jit=0.08):
    """Six-sided crystal with a pointed tip; tilt = (rx, rz) lean in degrees."""
    n = 6
    pts = [(r * math.cos(2 * math.pi * k / n), 0, r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    pts += [(r * math.cos(2 * math.pi * k / n), h * (1 - tip), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    pts.append((0, h, 0))
    faces = [tuple(range(n))]
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k, k2, n + k2, n + k))
        faces.append((n + k, n + k2, 2 * n))
    return dk.poly(p, (x, y0, z), pts, faces, col, jit, rot=(tilt[0], yaw, tilt[1]))


def lathe(p, cx, cz, prof, col, sx=1.0, sz=1.0, segs=16, jit=0.04):
    """Surface of revolution: prof = [(radius, y), ...] swept around the vertical axis (open at both ends of the profile)."""
    pts, faces = [], []
    for r, y in prof:
        for i in range(segs):
            a = 2 * math.pi * i / segs
            pts.append((r * sx * math.cos(a), y, r * sz * math.sin(a)))
    for j in range(len(prof) - 1):
        for i in range(segs):
            i2 = (i + 1) % segs
            faces.append((j * segs + i, j * segs + i2, (j + 1) * segs + i2, (j + 1) * segs + i))
    return dk.poly(p, (cx, 0, cz), pts, faces, col, jit)


# ---- 9. Crater ---------------------------------------------------------------------------------------------------------
@part("Crater")
def build_Crater(p):
    cx, cz = 66, 48
    bx(p, (55, 77), (0, 0.4), (41, 55), ROCK, 0.05)
    lathe(p, cx, cz, [(7.6, 0.4), (6.5, 1.15), (5.1, 1.2), (3.9, 0.45)], (158, 146, 164), sx=1.22, sz=0.84, segs=18, jit=0.07)
    disc(p, cx, 0.4, 0.5, cz, 4.4, (84, 72, 90), 18)
    disc(p, cx, 0.5, 0.56, cz, 3.4, (128, 74, 60), 14)
    hs = (3.4, 2.1, 2.9, 2.4, 3.2, 1.9, 2.8, 3.1, 2.2, 3.0, 2.0, 2.7, 3.3, 2.3)
    for k in range(14):
        a = math.radians(k * 360 / 14 + 8)
        x, z = cx + 7.3 * math.cos(a), cz + 5.0 * math.sin(a)
        col = ((104, 98, 120), STONE, (130, 124, 148), (172, 172, 190))[k % 4]
        stone(p, x, z, -(math.degrees(a) + 90), 3.6 if k % 2 else 3.0, 2.6, hs[k], col, 0.7, (0.2, 0.0), 0.06, y0=0.7)
    rockb(p, (cx, 2.1, cz), 2.2, (62, 54, 70), scale=(1.2, 0.85, 1.05), seed=4, jag=0.2, subdiv=2)
    for k, (dx, dy, dz, s) in enumerate(((0.6, 3.6, 0.2, 0.55), (-1.3, 2.9, 1.0, 0.45), (1.0, 2.8, -1.1, 0.5), (-0.4, 2.3, -1.7, 0.45), (1.9, 2.0, 0.9, 0.4))):
        rockb(p, (cx + dx, dy, cz + dz), s * 1.5, (232, 128, 58) if k != 1 else (214, 84, 60), scale=(1.2, 0.6, 1.2), seed=7 + k, jag=0.2, jit=0.08)
    for k, (x, z, s) in enumerate(((57, 42.5, 1.3), (75, 43, 1.0), (58, 53.5, 0.9), (74.5, 53.5, 1.4), (63, 42, 0.8), (70, 54, 0.9))):
        cb(p, (x, 0.4 + s * 0.3, z), (s, s * 0.6, s * 0.9), STONE if k % 2 else ROCK, 0.06, rot=(0, 20 + 35 * k, 0))


# ---- 10. Meteorite -----------------------------------------------------------------------------------------------------
@part("Meteorite")
def build_Meteorite(p):
    bx(p, (38.5, 45.5), (0, 0.6), (0.5, 7.5), STONE, 0.04)
    bx(p, (39.2, 44.8), (0.6, 1.0), (1.2, 6.8), DSTONE, 0.04)
    bx(p, (39.5, 44.5), (1.0, 1.45), (1.5, 6.5), DARK, 0.04)
    bx(p, (40.3, 43.7), (0.2, 0.5), (7.5, 7.68), BRASS, 0.02)
    rockb(p, (42, 3.65, 4), 2.3, (62, 56, 74), scale=(1.1, 1.0, 1.08), seed=11, jag=0.2, subdiv=2)
    for k, (dx, dy, dz, s, col) in enumerate(((1.7, 0.9, 1.2, 0.8, COPPER), (-1.5, 0.3, 1.6, 0.7, RED), (0.6, 2.0, -1.4, 0.75, COPPER),
                                              (-1.9, 1.4, -0.6, 0.6, COPPER))):
        rockb(p, (42 + dx, 3.65 + dy, 4 + dz), s, col, scale=(1.1, 0.55, 1.1), seed=20 + k, jag=0.18, jit=0.08)
    crystal(p, 43.6, 4.6, 5.0, 1.8, 0.45, TEAL, tilt=(8, 14), yaw=20)
    crystal(p, 41.2, 3.2, 5.4, 1.3, 0.36, LILAC, tilt=(-10, -16), yaw=40)
    rockb(p, (43.9, 1.9, 6.4), 0.85, (58, 52, 66), scale=(1.2, 0.9, 1.0), seed=31, jag=0.22, subdiv=1)
    crystal(p, 44.4, 6.0, 2.4, 0.9, 0.25, TEAL, tilt=(-12, 18), yaw=10)


# ---- 11. Orrery --------------------------------------------------------------------------------------------------------
@part("Orrery")
def build_Orrery(p):
    cx, cz, ym = -52, 10, 5.2
    disc(p, cx, 0, 0.7, cz, 7.0, STONE, 16)
    disc(p, cx, 0.7, 1.2, cz, 6.2, DSTONE, 16)
    for k in range(8):
        a = math.radians(k * 45 + 22)
        cb(p, (cx + 6.6 * math.cos(a), 0.74, cz + 6.6 * math.sin(a)), (0.5, 0.1, 0.5), GOLD, 0.02, rot=(0, 45, 0))
    disc(p, cx, 1.2, 3.6, cz, 1.6, BRASS, 10, top_r=1.0)
    disc(p, cx, 3.6, 3.9, cz, 2.2, DBRASS, 10)
    vcyl(p, cx, 3.9, ym, cz, 0.35, BRASS, 8)
    ball(p, (cx, ym, cz), 1.72, GOLD, subdiv=1, jit=0.05)
    for k in range(8):
        a = math.radians(k * 45)
        rod(p, (cx + 1.5 * math.cos(a), ym, cz + 1.5 * math.sin(a)), (cx + 2.3 * math.cos(a), ym, cz + 2.3 * math.sin(a)), 0.28, LGOLD, verts=4, r2=0.0)
    vcyl(p, cx, ym + 1.5, 6.9, cz, 0.2, BRASS, 6)
    for R in (3.8, 5.2, 5.9):
        ring(p, (cx, ym, cz), R, 0.13, BRASS, axis='y', segs=20, sides=4, jit=0.03)
    planets = ((0, 3.8, 0.8, TEAL), (107, 5.2, 1.1, COPPER), (217, 5.2, 0.7, LILAC), (329, 5.9, 1.1, PURPLE))
    for ang, R, s, col in planets:
        a = math.radians(ang)
        px, pz = cx + R * math.cos(a), cz + R * math.sin(a)
        rod(p, (cx + 1.8 * math.cos(a), ym, cz + 1.8 * math.sin(a)), (px, ym, pz), 0.1, BRASS, verts=4)
        ball(p, (px, ym, pz), s, col, subdiv=1, jit=0.07)
    a = math.radians(329)
    ring(p, (cx + 5.9 * math.cos(a), ym, cz + 5.9 * math.sin(a)), 1.7, 0.12, LILAC, axis='y', segs=14, sides=4, jit=0.03, rot=(18, 0, 14))
    for ang in (50, 160, 270):
        a = math.radians(ang)
        rod(p, (cx + 6.3 * math.cos(a), 1.2, cz + 6.3 * math.sin(a)), (cx + 5.55 * math.cos(a), ym - 0.1, cz + 5.55 * math.sin(a)), 0.15, BRASS, verts=5)


# ---- 12. Henge ---------------------------------------------------------------------------------------------------------
@part("Henge")
def build_Henge(p):
    disc(p, -70, 0, 0.22, 6, 7.9, MOSS, 14, jit=0.05)
    specs = ((-62.8, 6.0, 0, 6.4, STONE), (-65, 0.8, 36, 7.6, STONE), (-71, -1.4, 78, 6.8, ROCK), (-76.4, 2.4, -40, 8.4, STONE),
             (-77.4, 8.2, -80, 6.4, ROCK), (-73, 12.6, -24, 7.2, STONE), (-66.6, 12.4, 24, 6.0, ROCK))
    for k, (x, z, yw, h, col) in enumerate(specs):
        stone(p, x, z, yw, 1.9, 2.8, h, col, 0.8, (0.0, 0.0), 0.06, y0=0.1)
        x2, z2 = L(x, z, yw, 0, 1.35)
        if k % 2 == 0:
            xr, zr = L(x, z, yw, 0, 1.3)
            cb(p, (xr, 3.0, zr), (0.28, 2.0, 0.16), LILAC, 0.03, rot=(0, yw, 0))
            cb(p, (xr, 4.4, zr), (0.7, 0.7, 0.16), LILAC, 0.03, rot=(0, yw, 45))
    bar(p, (-62.8, 6.55, 6.0), (-65, 7.85, 0.8), 1.15, DSTONE, 0.05)
    bar(p, (-71, 6.95, -1.4), (-76.4, 8.65, 2.4), 1.1, DSTONE, 0.05)
    cb(p, (-70, 0.6, 6), (6.0, 1.0, 4.0), DARK, 0.05, rot=(0, 20, 0))
    cb(p, (-70, 1.25, 6), (4.6, 0.3, 3.0), DSTEEL, 0.04, rot=(0, 20, 0))
    star_poly(p, (-70, 1.45, 6), 'xz', 1.3, 0.55, 0.1, GOLD, jit=0.02)
    for k, (x, z) in enumerate(((-67, 3), (-73.5, 8), (-68, 9.5), (-72, 2.5))):
        cb(p, (x, 0.45, z), (0.9, 0.5, 0.8), STONE if k % 2 else ROCK, 0.06, rot=(0, 25 * k + 10, 0))


# ---- 13. Lander --------------------------------------------------------------------------------------------------------
@part("Lander")
def build_Lander(p):
    cx, cz = 30, -8
    hexa(p, [(27.4, 2.6, -10.6), (32.6, 2.6, -10.6), (32.6, 2.6, -5.4), (27.4, 2.6, -5.4),
             (27.5, 5.8, -10.5), (32.5, 5.8, -10.5), (32.5, 5.8, -5.5), (27.5, 5.8, -5.5)], GOLD, 0.1)
    for y in (3.4, 4.9):
        bx(p, (27.35, 32.65), (y, y + 0.22), (-10.65, -5.35), DBRASS, 0.04)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (cx + sx * 2.5 - 0.22, cx + sx * 2.5 + 0.22), (2.6, 5.8), (cz + sz * 2.5 - 0.22, cz + sz * 2.5 + 0.22), STEEL, 0.04)
    hexa(p, [(28.2, 5.8, -9.8), (31.8, 5.8, -9.8), (31.8, 5.8, -6.2), (28.2, 5.8, -6.2),
             (28.4, 7.5, -9.4), (31.6, 7.5, -9.4), (31.6, 7.5, -6.6), (28.4, 7.5, -6.6)], SILVER, 0.04)
    bx(p, (29.0, 31.0), (6.1, 7.0), (-6.25, -6.0), DTEAL, 0.03)
    dk.cone(p, (30, 1.0, -8), 1.1, 1.6, DARK, verts=8, jitter=0.03)
    for k, x in enumerate((28.5, 30.0, 31.5)):
        for z in (-5.34, -10.66):
            bx(p, (x - 0.5, x + 0.5), (3.76, 4.76), (z - 0.06, z + 0.06), LGOLD if k % 2 == 0 else DBRASS, 0.05)
        for xx in (27.34, 32.66):
            bx(p, (xx - 0.06, xx + 0.06), (3.76, 4.76), (-9.5 + k * 1.5 - 0.5, -9.5 + k * 1.5 + 0.5), LGOLD if k % 2 == 0 else DBRASS, 0.05)
    for sx in (-1, 1):
        for sz in (-1, 1):
            top = (cx + sx * 2.3, 4.7, cz + sz * 2.3)
            foot = (cx + sx * 4.4, 0.6, cz + sz * 4.4)
            rod(p, top, foot, 0.36, STEEL, verts=6)
            rod(p, (cx + sx * 2.5, 2.9, cz + sz * 0.0), (cx + sx * 4.1, 0.9, cz + sz * 3.6), 0.17, DSTEEL, verts=5)
            disc(p, foot[0], 0, 0.55, foot[2], 1.15, DARK, 8)
    for z in (-8.7, -7.3):
        rod(p, (32.55, 5.1, z), (34.6, 0.6, z), 0.1, SILVER, verts=4)
    for k in range(5):
        t = 0.1 + k * 0.2
        a, b = along((32.55, 5.1), (34.6, 0.6), t), None
        bx(p, (a[0] - 0.1, a[0] + 0.5), (a[1] - 0.07, a[1] + 0.07), (-8.75, -7.25), SILVER, 0.03)
    for sx in (-1, 1):
        cb(p, (30 + sx * 1.9, 7.2, -9.5), (0.5, 0.5, 0.5), STEEL, 0.03)
    dk.cyl(p, (30, 6.9, -10.2), 0.9, 0.3, WHITE, axis='z', verts=10, top_radius=0.2, jitter=0.03)
    cb(p, (31.0, 5.5, -5.45), (0.9, 0.6, 0.1), RED, 0.02)
    cb(p, (31.0, 5.2, -5.45), (0.9, 0.2, 0.1), WHITE, 0.02)


# ---- 14. Terrace -------------------------------------------------------------------------------------------------------
def mini_scope(p, x, z, az_deg, el_deg, col):
    yh = 3.2
    for k in range(3):
        a = math.radians(90 + 120 * k + 20)
        rod(p, (x, yh, z), (x + 1.2 * math.cos(a), 0.6, z + 1.2 * math.sin(a)), 0.13, DARK, verts=5)
    cb(p, (x, yh, z), (0.8, 0.4, 0.8), BRASS, 0.03)
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
    c = (x, yh + 0.45, z)
    a0 = tuple(c[i] - d[i] * 1.0 for i in range(3))
    a1 = tuple(c[i] + d[i] * 2.4 for i in range(3))
    rod(p, a0, a1, 0.48, col, verts=8)
    m = tuple(c[i] + d[i] * 1.4 for i in range(3))
    m2 = tuple(c[i] + d[i] * 1.7 for i in range(3))
    rod(p, m, m2, 0.56, BRASS, verts=8)
    e0 = tuple(c[i] - d[i] * 1.0 for i in range(3))
    e1 = tuple(c[i] - d[i] * 1.5 for i in range(3))
    rod(p, e0, e1, 0.22, DARK, verts=6)
    a2 = tuple(c[i] + d[i] * 2.55 for i in range(3))
    rod(p, a1, a2, 0.56, DARK, verts=8)


@part("Terrace")
def build_Terrace(p):
    bx(p, (22, 34), (0, 0.3), (35.5, 44.5), DWOOD, 0.04)
    for k in range(10):
        z0 = 35.5 + k * 0.9
        bx(p, (22, 34), (0.3, 0.6), (z0 + 0.04, z0 + 0.86), WOOD, 0.1)
    for a, c in (((22, 34), (35.5, 35.8)), ((22, 22.3), (35.5, 44.5)), ((33.7, 34), (35.5, 44.5))):
        bx(p, a, (0.6, 0.95), c, DWOOD, 0.05)
    star_poly(p, (28, 0.64, 40), 'xz', 2.0, 0.85, 0.06, GOLD, jit=0.02)
    mini_scope(p, 24.2, 38.6, 190, 40, WHITE)
    mini_scope(p, 28.2, 41.6, 75, 60, BRASS)
    mini_scope(p, 32, 38.2, 300, 28, WHITE)


# ---- 15. Crystals ------------------------------------------------------------------------------------------------------
@part("Crystals")
def build_Crystals(p):
    bx(p, (-49, -39), (0, 0.6), (-54.5, -47.5), ROCK, 0.06)
    stone(p, -44.5, -51, 12, 8.4, 5.4, 1.2, (100, 94, 116), 0.78, (0.3, 0), 0.07, y0=0.5)
    for k, (x, z, w, h) in enumerate(((-47.6, -49.2, 2.2, 1.4), (-41.2, -48.7, 2.0, 1.1), (-40.6, -53.6, 2.4, 1.5), (-47.8, -53.9, 2.1, 1.2))):
        stone(p, x, z, 25 * k, w, w * 0.9, h, (ROCK, STONE)[k % 2], 0.7, (0, 0), 0.07, y0=0.4)
    cs = ((-44.4, -51, 1.0, 9.3, 1.3, PURPLE, (0, 6), 30), (-47.2, -52, 1.0, 6.4, 1.0, LILAC, (0, -12), 10),
          (-41.2, -50.4, 1.0, 7.6, 1.1, INDIGO, (0, 10), 55), (-43.4, -48.6, 1.0, 5.0, 0.8, LILAC, (8, 0), 20),
          (-45.6, -53.4, 1.0, 4.6, 0.9, PURPLE, (-8, 0), 40), (-40, -52.2, 1.0, 3.6, 0.7, TEAL, (0, 14), 15),
          (-46.4, -50.0, 1.0, 3.4, 0.7, TEAL, (10, -18), 70), (-42.4, -53.2, 1.0, 4.2, 0.8, PURPLE, (-10, 8), 5),
          (-48.0, -50.6, 1.0, 2.4, 0.55, LILAC, (0, -22), 0), (-39.8, -49.6, 1.0, 2.6, 0.55, LILAC, (12, 20), 35))
    for x, z, y0, h, r, col, tilt, yaw in cs:
        crystal(p, x, z, y0, h, r, col, tilt, yaw, 0.28, 0.1)


# ---- 16. Comet ---------------------------------------------------------------------------------------------------------
@part("Comet")
def build_Comet(p):
    bx(p, (-34, -22), (0, 0.6), (25, 29), STONE, 0.04)
    bx(p, (-33, -23), (0.6, 1.2), (25.6, 28.4), DSTONE, 0.04)
    bx(p, (-32, -30.2), (1.2, 1.35), (26.2, 27.8), BRASS, 0.03)
    rod(p, (-24.6, 1.2, 27), (-24.6, 5.4, 27), 0.38, DARK, verts=8)
    rod(p, (-29.6, 1.2, 27), (-29.6, 3.8, 27), 0.3, DARK, verts=8)
    rockb(p, (-24.6, 7.4, 27), 2.3, GOLD, seed=3, jag=0.1, subdiv=2, jit=0.07)
    rockb(p, (-23.7, 8.5, 27.8), 1.0, LGOLD, scale=(1, 0.8, 1), seed=9, jag=0.2, jit=0.06)
    for k, (x, y, r, col) in enumerate(((-27.4, 6.2, 1.6, CREAM), (-29.8, 5.2, 1.3, LILAC), (-31.8, 4.4, 1.0, TEAL), (-33.4, 3.8, 0.7, INDIGO))):
        rockb(p, (x, y, 27), r, col, seed=40 + k, jag=0.14, subdiv=1, jit=0.07)
    for dz, col in ((-1.5, LILAC), (1.5, TEAL), (0.0, CREAM)):
        rod(p, (-26.0, 7.0 if dz else 8.3, 27 + dz), (-33.6, 4.3 if dz else 5.0, 27 + dz * 1.4), 0.55, col, verts=4, r2=0.0)
    for k, (x, y, z) in enumerate(((-22.6, 5.6, 28.5), (-26, 9.8, 26.2), (-31, 7.6, 28.2), (-29, 2.4, 25.8))):
        star_poly(p, (x, y, z), 'xy', 0.55, 0.22, 0.12, WHITE if k % 2 else GOLD, jit=0.02)


def v3(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def dish(p, c, R, depth, az, el, col, inner=LSILVER, feed=None, jit=0.03, beacon=None):
    """Parabolic dish (a shallow cone with a lighter face) centred on c, facing azimuth az (stage x-z plane, deg) and elevation el."""
    az, el = math.radians(az), math.radians(el)
    d = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
    u = (-math.sin(el) * math.cos(az), math.cos(el), -math.sin(el) * math.sin(az))
    w = (-math.sin(az), 0.0, math.cos(az))
    a, b = v3(c, d, -depth * 0.5), v3(c, d, depth * 0.5)
    rod(p, a, b, R * 0.14, col, verts=14, r2=R, jit=jit)
    rod(p, b, v3(b, d, 0.1), R * 0.9, inner, verts=14, jit=jit)
    f = R * 0.72 if feed is None else feed
    F = v3(b, d, f)
    for k in range(4):
        th = math.radians(45 + 90 * k)
        rim = v3(v3(b, u, R * 0.95 * math.cos(th)), w, R * 0.95 * math.sin(th))
        rod(p, rim, F, max(0.07, R * 0.018), DSTEEL, verts=4)
    rod(p, v3(F, d, -R * 0.1), v3(F, d, R * 0.12), max(0.15, R * 0.05), DARK, verts=6)
    if beacon:
        cb(p, v3(F, d, R * 0.2), (R * 0.1 + 0.2,) * 3, beacon, 0.03)
    return d, u, w


def fin(p, cx, cz, ang, prof, thick, col, jit=0.04):
    """Rocket fin: profile [(radial, y)] x4 extruded sideways, around the vertical axis at (cx, cz), pointing out at angle ang."""
    a = math.radians(ang)
    rx, rz = math.cos(a), math.sin(a)
    tx, tz = -rz, rx
    pts = []
    for s in (thick / 2, -thick / 2):
        for r, y in prof:
            pts.append((cx + rx * r + tx * s, y, cz + rz * r + tz * s))
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def slit_dome(p, cx, y0, cz, r, h, col, seg=24, rings=4, cut=(), jit=0.03, cut_top=False):
    pts, faces = [], []
    for j in range(rings + 1):
        el = (math.pi / 2) * j / rings
        rr, yy = math.cos(el), h * math.sin(el)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            pts.append((r * rr * math.cos(a), yy, r * rr * math.sin(a)))
    top = len(pts)
    pts.append((0, h, 0))
    for j in range(rings):
        for i in range(seg):
            if i in cut and (j < rings - 1 or cut_top):
                continue
            i2 = (i + 1) % seg
            a, b = j * seg + i, j * seg + i2
            faces.append((a, b, top) if j == rings - 1 else (a, b, b + seg, a + seg))
    return dk.poly(p, (cx, y0, cz), pts, faces, col, jit)


# ---- 17. Satellite -----------------------------------------------------------------------------------------------------
@part("Satellite")
def build_Satellite(p):
    cx, cz = 20, -51
    bx(p, (15.5, 24.5), (0, 0.4), (-55.5, -46.5), STONE, 0.04)
    bx(p, (16.5, 23.5), (0.4, 0.8), (-54.5, -47.5), DSTONE, 0.04)
    bx(p, (18.2, 21.8), (0.15, 0.55), (-46.5, -46.3), BRASS, 0.02)
    vcyl(p, cx, 0.8, 4.2, cz, 0.9, STEEL, verts=8)
    vcyl(p, cx, 3.7, 4.4, cz, 1.7, BRASS, verts=8)
    vcyl(p, cx, 0.8, 1.4, cz, 1.5, DSTEEL, verts=8, top_r=0.9)
    hexa(p, [(18.2, 4.4, -52.8), (21.8, 4.4, -52.8), (21.8, 4.4, -49.2), (18.2, 4.4, -49.2),
             (18.0, 8.0, -53.0), (22.0, 8.0, -53.0), (22.0, 8.0, -49.0), (18.0, 8.0, -49.0)], GOLD, 0.1)
    for y in (5.2, 6.9):
        bx(p, (17.9, 22.1), (y, y + 0.2), (-53.1, -48.9), DBRASS, 0.04)
    for k in range(3):
        bx(p, (18.7 + k * 1.15, 19.5 + k * 1.15), (5.5, 6.7), (-49.0, -48.85), LGOLD if k % 2 == 0 else DBRASS, 0.05)
    bx(p, (19.0, 21.0), (8.0, 8.4), (-52.2, -51.2), DARK, 0.03)
    for side, x0, rz in ((-1, 14.4, -10), (1, 25.6, 10)):
        bx(p, (min(x0, 20 + side * 1.9), max(x0, 20 + side * 1.9)), (6.3, 6.5), (cz - 0.15, cz + 0.15), STEEL, 0.03)
        for k, lx in enumerate((-2.4, 0.0, 2.4)):
            x, y = rl(x0, 6.4, lx, 0, rz)
            dk.box(p, (x, y, cz), (2.2, 0.26, 3.2), SOLAR, rot=(0, 0, rz), jitter=0.03)
            x, y = rl(x0, 6.4, lx, 0.15, rz)
            dk.box(p, (x, y, cz), (0.1, 0.05, 3.2), LILAC, rot=(0, 0, rz), jitter=0.02)
            dk.box(p, (x, y, cz), (2.2, 0.05, 0.1), LILAC, rot=(0, 0, rz), jitter=0.02)
        for lx in (-3.5, 3.5):
            x, y = rl(x0, 6.4, lx, 0, rz)
            dk.box(p, (x, y, cz), (0.14, 0.3, 3.3), DSTEEL, rot=(0, 0, rz), jitter=0.02)
    rod(p, (20.2, 8.0, -50.2), (20.4, 8.7, -49.8), 0.12, STEEL, verts=5)
    dish(p, (20.4, 8.9, -49.8), 1.3, 0.5, 25, 50, WHITE, feed=1.0)
    rod(p, (19.0, 8.0, -52), (19.0, 10.0, -52), 0.09, STEEL, verts=5)
    ball(p, (19.0, 10.05, -52), 0.22, GOLD, subdiv=1, jit=0.02)


# ---- 18. Dishes --------------------------------------------------------------------------------------------------------
@part("Dishes")
def build_Dishes(p):
    specs = ((57, 6, 5.2, 4.0, 40, 62, 3.0), (67.4, 7.6, 4.4, 3.0, 125, 52, 2.6), (72, 4.4, 3.6, 2.3, -35, 70, 2.6))
    for x, z, h, R, az, el, bs in specs:
        bx(p, (x - bs / 2, x + bs / 2), (0, 0.8), (z - bs / 2, z + bs / 2), STONE, 0.04)
        vcyl(p, x, 0.8, h, z, 0.5, STEEL, verts=8)
        vcyl(p, x, 0.8, 1.6, z, 0.9, DSTEEL, verts=8, top_r=0.5)
        cy = h + R * 0.35
        a = math.radians(az)
        side = (-math.sin(a), math.cos(a))
        rod(p, (x - side[0] * R * 0.22, h + 0.1, z - side[1] * R * 0.22), (x + side[0] * R * 0.22, h + 0.1, z + side[1] * R * 0.22), 0.3, BRASS, verts=6)
        rod(p, (x, h, z), (x, cy, z), 0.3, STEEL, verts=6)
        dish(p, (x, cy, z), R, R * 0.28, az, el, WHITE if R > 2.5 else SILVER)
    bx(p, (61, 66), (0, 2.4), (10.7, 14.1), WHITE, 0.03)
    bx(p, (60.8, 66.2), (2.4, 2.8), (10.5, 14.3), STEEL, 0.03)
    bx(p, (62.0, 63.4), (0.1, 1.8), (14.1, 14.22), DARK, 0.03)
    bx(p, (64.0, 65.6), (1.2, 1.9), (14.1, 14.22), TEAL, 0.03)
    bx(p, (60.9, 61.0), (1.0, 2.0), (11.6, 13.2), DSTEEL, 0.03)
    rod(p, (65.2, 2.8, 11.5), (65.2, 4.6, 11.5), 0.08, STEEL, verts=5)
    cb(p, (65.2, 4.7, 11.5), (0.3, 0.3, 0.3), RED, 0.03)
    for (x, z) in ((57, 6), (67.4, 7.6), (72, 4.4)):
        bx(p, (min(x, 62.5), max(x, 62.5)), (0.0, 0.12), (min(z, 10.6) - 0.1, min(z, 10.6) + 0.1), DARK, 0.02)


# ---- 19. Rocket --------------------------------------------------------------------------------------------------------
@part("Rocket")
def build_Rocket(p):
    cx, cz = 72.4, 31
    bx(p, (68.5, 77.5), (0, 1.0), (26.5, 35.5), DARK, 0.04)
    bx(p, (69.3, 76.7), (1.0, 1.2), (27.3, 34.7), DSTEEL, 0.04)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        bx(p, (cx + 2.6 * math.cos(a) - 0.4, cx + 2.6 * math.cos(a) + 0.4), (1.2, 2.3), (cz + 2.6 * math.sin(a) - 0.4, cz + 2.6 * math.sin(a) + 0.4), STEEL, 0.04)
    for dx, dz in ((0, 0), (0.9, 0.5), (-0.9, 0.5), (0, -1.0)):
        rod(p, (cx + dx, 1.2, cz + dz), (cx + dx, 2.1, cz + dz), 0.5, DSTEEL, verts=8, r2=0.85)
    vcyl(p, cx, 2.0, 11.6, cz, 1.9, WHITE, verts=12, jit=0.03)
    vcyl(p, cx, 4.3, 5.0, cz, 1.96, INDIGO, verts=12, jit=0.03)
    vcyl(p, cx, 8.6, 9.0, cz, 1.96, GOLD, verts=12, jit=0.03)
    dk.cone(p, (cx, 11.6, cz), 1.9, 5.2, RED, verts=12, jitter=0.03)
    vcyl(p, cx, 11.6, 11.9, cz, 1.95, DARK, verts=12, jit=0.03)
    for y in (7.0, 10.0):
        zcyl(p, cx, y, cz + 1.7, cz + 2.0, 0.55, TEAL, verts=8, jit=0.02)
        zcyl(p, cx, y, cz + 1.95, cz + 2.05, 0.7, DSTEEL, verts=8, jit=0.02)
    for ang in (0, 90, 180, 270):
        fin(p, cx, cz, ang, [(1.7, 1.9), (1.7, 5.4), (3.7, 2.5), (3.7, 1.8)], 0.55, RED, 0.04)
    # gantry tower
    gx, gz = 76.4, 31
    for sx in (-0.5, 0.5):
        for sz in (-0.5, 0.5):
            bx(p, (gx + sx - 0.17, gx + sx + 0.17), (1.0, 14.0), (gz + sz - 0.17, gz + sz + 0.17), STEEL, 0.03)
    for k in range(6):
        y0, y1 = 1.0 + k * 2.2, 3.2 + k * 2.2
        for zz in (gz - 0.5, gz + 0.5):
            if k % 2 == 0:
                bar(p, (gx - 0.5, y0, zz), (gx + 0.5, y1, zz), 0.12, DSTEEL, 0.03)
            else:
                bar(p, (gx + 0.5, y0, zz), (gx - 0.5, y1, zz), 0.12, DSTEEL, 0.03)
        bx(p, (gx - 0.6, gx + 0.6), (y0 - 0.05, y0 + 0.07), (gz - 0.6, gz + 0.6), DSTEEL, 0.03)
    bx(p, (gx - 0.7, gx + 0.7), (14.0, 14.3), (gz - 0.7, gz + 0.7), DARK, 0.03)
    cb(p, (gx, 14.6, gz), (0.45, 0.5, 0.45), RED, 0.03)
    for y in (10.5, 5.5):
        bx(p, (74.2, 76.0), (y - 0.3, y + 0.3), (gz - 0.4, gz + 0.4), STEEL, 0.03)
        bx(p, (73.5, 74.4), (y - 0.45, y + 0.45), (gz - 0.55, gz + 0.55), DSTEEL, 0.03)
    rod(p, (74.0, 10.0, gz + 0.3), (74.0, 3.0, gz + 0.3), 0.09, DARK, verts=5)
    for k in range(5):
        cb(p, (gx + 0.78, 2.2 + k * 2.4, gz), (0.2, 0.12, 1.0), STEEL, 0.02)


# ---- 20. Fountain ------------------------------------------------------------------------------------------------------
@part("Fountain")
def build_Fountain(p):
    cx, cz = -14, 16
    disc(p, cx, 0, 1.4, cz, 7.0, STONE, 20)
    disc(p, cx, 1.4, 1.5, cz, 6.4, DSTONE, 20)
    disc(p, cx, 1.5, 1.6, cz, 5.9, TEAL, 20)
    disc(p, cx, 1.6, 1.65, cz, 3.6, (120, 214, 226), 16)
    for k in range(14):
        a = math.radians(k * 360 / 14)
        cb(p, (cx + 6.55 * math.cos(a), 1.65, cz + 6.55 * math.sin(a)), (0.9, 0.5, 1.3), STONE if k % 2 else DSTONE, 0.05, rot=(0, -k * 360 / 14, 0))
    disc(p, cx, 1.6, 2.2, cz, 2.0, STONE, 10, top_r=1.5)
    disc(p, cx, 2.2, 5.0, cz, 1.0, STONE, 10)
    disc(p, cx, 4.2, 4.5, cz, 1.5, BRASS, 10)
    vcyl(p, cx, 4.85, 5.55, cz, 2.8, STONE, verts=14, top_r=2.8)
    disc(p, cx, 4.85, 5.0, cz, 1.6, DSTONE, 12)
    disc(p, cx, 5.55, 5.7, cz, 2.5, TEAL, 14)
    ball(p, (cx, 6.9, cz), 1.45, GOLD, subdiv=1, jit=0.05)
    for k in range(8):
        a = math.radians(k * 45 + 20)
        rod(p, (cx + 1.3 * math.cos(a), 6.9 + 0.35 * math.sin(a * 2), cz + 1.3 * math.sin(a)),
            (cx + 2.0 * math.cos(a), 6.9 + 0.35 * math.sin(a * 2), cz + 2.0 * math.sin(a)), 0.25, LGOLD, verts=4, r2=0.0)
    ring(p, (cx, 6.2, cz), 4.8, 0.14, BRASS, axis='y', segs=22, sides=4, jit=0.03)
    for ang, s, col, y in ((0, 0.8, LILAC, 6.4), (215, 0.7, TEAL, 6.4), (115, 0.9, COPPER, 6.4)):
        a = math.radians(ang)
        px, pz = cx + 4.8 * math.cos(a), cz + 4.8 * math.sin(a)
        rod(p, (cx + 1.0 * math.cos(a), 6.2, cz + 1.0 * math.sin(a)), (px, 6.2, pz), 0.1, BRASS, verts=4)
        ball(p, (px, y + (0.5 if col == COPPER else 0.2), pz), s, col, subdiv=1, jit=0.07)
    for k in range(8):
        a = math.radians(k * 45 + 22)
        rod(p, (cx + 2.5 * math.cos(a), 5.8, cz + 2.5 * math.sin(a)), (cx + 4.3 * math.cos(a), 1.7, cz + 4.3 * math.sin(a)), 0.2, (170, 232, 240), verts=4, r2=0.08)


# ---- 21. Astronaut -----------------------------------------------------------------------------------------------------
@part("Astronaut")
def build_Astronaut(p):
    cx, cz = 38, -24
    bx(p, (34.5, 41.5), (0, 1.0), (-27, -21), STONE, 0.04)
    bx(p, (35.2, 40.8), (1.0, 2.0), (-26.4, -21.6), DSTONE, 0.04)
    bx(p, (36.2, 39.8), (0.3, 0.75), (-21.0, -20.85), BRASS, 0.02)
    for x in (37.0, 39.0):
        bx(p, (x - 0.8, x + 0.8), (3.0, 6.4), (cz - 0.9, cz + 0.9), WHITE, 0.03)
        bx(p, (x - 0.85, x + 0.85), (2.0, 3.0), (cz - 1.15, cz + 1.4), DSTEEL, 0.03)
        bx(p, (x - 0.85, x + 0.85), (3.9, 4.3), (cz - 0.95, cz + 0.95), STEEL, 0.03)
    hexa(p, [(36.0, 6.2, -25.2), (40.0, 6.2, -25.2), (40.0, 6.2, -22.8), (36.0, 6.2, -22.8),
             (35.9, 9.8, -25.3), (40.1, 9.8, -25.3), (40.1, 9.8, -22.7), (35.9, 9.8, -22.7)], WHITE, 0.03)
    bx(p, (36.8, 39.2), (7.2, 8.8), (-22.8, -22.6), DSTEEL, 0.03)
    for k, col in enumerate((RED, TEAL, GOLD)):
        bx(p, (37.2 + k * 0.7, 37.7 + k * 0.7), (8.0, 8.5), (-22.62, -22.48), col, 0.02)
    bx(p, (36.6, 39.4), (6.5, 7.0), (-22.82, -22.7), BRASS, 0.03)
    bx(p, (36.6, 39.4), (6.2, 9.4), (-27.0, -25.2), STEEL, 0.04)
    bx(p, (36.8, 39.2), (6.4, 6.7), (-27.1, -25.1), DSTEEL, 0.03)
    ball(p, (38, 11.3, -24), 1.95, WHITE, scale=(1.0, 1.0, 1.0), subdiv=2, jit=0.03)
    ball(p, (38, 11.1, -22.55), 1.45, GOLD, scale=(1.05, 0.78, 0.4), subdiv=1, jit=0.03)
    vcyl(p, 38, 9.6, 10.0, cz, 1.7, DSTEEL, verts=10)
    bx(p, (34.1, 35.7), (6.8, 9.6), (-24.8, -23.2), WHITE, 0.03)
    ball(p, (34.9, 6.4, -24), 0.85, STEEL, subdiv=1, jit=0.03)
    rod(p, (40.3, 9.0, -24), (41.9, 12.6, -24), 0.75, WHITE, verts=6)
    ball(p, (42.0, 13.0, -24), 0.85, STEEL, subdiv=1, jit=0.03)
    rod(p, (34.4, 2.0, -26.4), (34.4, 13.6, -26.4), 0.2, STEEL, verts=5)
    bx(p, (34.6, 36.6), (11.9, 13.4), (-26.2, -26.0), RED, 0.03)
    star_poly(p, (35.6, 12.65, -25.95), 'xy', 0.5, 0.22, 0.06, WHITE, jit=0.02)
    bx(p, (34.0, 34.8), (2.0, 2.3), (-21.9, -20.9), DSTONE, 0.03)


# ---- 23. Dish ----------------------------------------------------------------------------------------------------------
@part("Dish")
def build_Dish(p):
    bx(p, (51, 65), (0, 1.0), (20, 32), STONE, 0.04)
    bx(p, (51.6, 64.4), (1.0, 1.15), (20.6, 31.4), DSTONE, 0.04)
    for k in range(7):
        bx(p, (52 + k * 1.2, 52.7 + k * 1.2), (1.15, 1.25), (20.6, 21.4), AMBERC if k % 2 else DARK, 0.02)
    tx, tz = 57, 24.6
    vcyl(p, tx, 1.0, 9.0, tz, 1.8, STEEL, verts=10, top_r=1.45)
    for y in (2.2, 4.6, 7.0):
        vcyl(p, tx, y, y + 0.35, tz, 1.95 - (y - 2.2) * 0.07, DSTEEL, verts=10)
    for k in range(6):
        a = math.radians(k * 60)
        bar(p, (tx + 1.7 * math.cos(a), 1.2, tz + 1.7 * math.sin(a)), (tx + 1.5 * math.cos(a + 0.5), 8.8, tz + 1.5 * math.sin(a + 0.5)), 0.14, DSTEEL, 0.03)
    vcyl(p, tx, 9.0, 9.4, tz, 1.9, DSTEEL, verts=10)
    for dz in (-1.1, 1.1):
        bx(p, (tx - 0.9, tx + 0.9), (9.4, 11.4), (tz + dz - 0.2, tz + dz + 0.2), BRASS, 0.03)
    zcyl(p, tx, 10.4, tz - 1.6, tz + 1.6, 0.4, DBRASS, verts=8)
    d, u, w = dish(p, (tx, 10.4, tz), 6.5, 2.0, 0, 62, WHITE, feed=4.6, beacon=RED)
    cb(p, v3((tx, 10.4, tz), d, -2.0), (1.6, 1.6, 1.6), DSTEEL, 0.03, rot=(0, 0, 62))
    cb(p, (61.6, 2.6, 28.8), (5, 3.2, 4), WHITE, 0.03)
    bx(p, (59.0, 64.2), (4.2, 4.5), (26.6, 31.0), STEEL, 0.03)
    bx(p, (60.2, 61.6), (1.0, 3.0), (30.8, 30.95), DARK, 0.03)
    bx(p, (62.2, 64.0), (1.9, 3.1), (30.8, 30.95), TEAL, 0.03)
    bx(p, (62.5, 63.9), (4.5, 5.3), (27.6, 29.0), DSTEEL, 0.03)
    rod(p, (59.5, 4.5, 27.2), (59.5, 6.0, 27.2), 0.07, STEEL, verts=5)
    rod(p, (59.0, 3.2, 26.8), (57.8, 2.0, 25.4), 0.12, DARK, verts=5)


# ---- 24. SilverDome ----------------------------------------------------------------------------------------------------
@part("SilverDome")
def build_SilverDome(p):
    cx, cz = 42, -46
    bx(p, (34, 50), (0, 1.0), (-54, -38), STONE, 0.04)
    bx(p, (35, 49), (1.0, 1.2), (-53, -39), DSTONE, 0.04)
    vcyl(p, cx, 1.2, 12.0, cz, 6.0, SILVER, verts=18, jit=0.03)
    for y in (4.5, 8.2):
        vcyl(p, cx, y, y + 0.35, cz, 6.2, STEEL, verts=18, jit=0.03)
    for k in range(9):
        a = math.radians(k * 40 + 20)
        if abs(math.degrees(a) - 90) < 25:
            continue
        cb(p, (cx + 6.02 * math.cos(a), 10.0, cz + 6.02 * math.sin(a)), (0.7, 1.4, 0.4), DNAVY, 0.03, rot=(0, -math.degrees(a) + 90 - 90, 0))
    vcyl(p, cx, 12.0, 12.4, cz, 6.7, STEEL, verts=18, jit=0.03)
    vcyl(p, cx, 12.4, 12.6, cz, 6.5, DSTEEL, verts=18, jit=0.03)
    dome_in = slit_dome(p, cx, 12.4, cz, 5.6, 6.9, DNAVY, seg=24, rings=4)
    slit_dome(p, cx, 12.4, cz, 6.2, 7.1, WHITE, seg=24, rings=4, cut=(6,))
    for i in (0, 4, 8, 12, 16, 20):
        a = math.radians(i * 15)
        if i == 6:
            continue
        cb(p, (cx + 6.2 * math.cos(a), 12.5, cz + 6.2 * math.sin(a)), (0.35, 0.35, 0.35), DSTEEL, 0.03)
    rod(p, (cx, 19.4, cz), (cx, 22.0, cz), 0.16, STEEL, verts=5)
    ball(p, (cx, 22.0, cz), 0.3, GOLD, subdiv=1, jit=0.02)
    bx(p, (cx - 2.2, cx + 2.2), (1.2, 7.2), (-40.7, -37.3), SILVER, 0.03)
    bx(p, (cx - 1.0, cx + 1.0), (1.2, 4.6), (-37.4, -37.2), DNAVY, 0.03)
    bx(p, (cx - 1.3, cx + 1.3), (4.6, 5.0), (-37.5, -37.2), BRASS, 0.03)
    bx(p, (cx - 2.5, cx + 2.5), (7.2, 7.6), (-41.0, -37.0), STEEL, 0.03)
    for x in (35.2, 48.8):
        bx(p, (x - 0.6, x + 0.6), (1.2, 13.0), (-42.6, -41.4), STEEL, 0.04)
        bx(p, (x - 0.8, x + 0.8), (12.6, 13.0), (-42.8, -41.2), DSTEEL, 0.04)
    for x in (cx - 2.0, cx + 2.0):
        bx(p, (x - 0.3, x + 0.3), (1.2, 7.2), (-40.9, -40.6), STEEL, 0.03)


# ---- 22. Greenhouse -----------------------------------------------------------------------------------------------
@part("Greenhouse")
def build_Greenhouse(p):
    GL = (160, 220, 230)
    GL2 = (186, 232, 238)
    bx(p, (-73, -51), (0, 1.0), (-55.5, -46.5), STONE, 0.04)
    bx(p, (-72.5, -51.5), (1.0, 1.25), (-54.9, -47.1), DSTONE, 0.04)
    posts = (-72.0, -67.0, -62.0, -57.0, -52.0)
    zf, zb = -47.5, -54.5
    for z in (zf, zb):
        for x in posts:
            bx(p, (x - 0.22, x + 0.22), (1.25, 7.0), (z - 0.22, z + 0.22), WHITE, 0.03)
    for k in range(4):
        x0, x1 = posts[k] + 0.22, posts[k + 1] - 0.22
        bx(p, (x0, x1), (1.25, 7.0), (zb - 0.1, zb + 0.1), GL, 0.04)
        bx(p, (x0, x1), (3.9, 4.15), (zb - 0.18, zb + 0.18), WHITE, 0.03)
        if k != 2:
            bx(p, (x0, x1), (1.25, 7.0), (zf - 0.1, zf + 0.1), GL, 0.04)
            bx(p, (x0, x1), (3.9, 4.15), (zf - 0.18, zf + 0.18), WHITE, 0.03)
    bx(p, (-62.2, -56.8), (5.6, 5.9), (zf - 0.25, zf + 0.25), WHITE, 0.03)
    bx(p, (-62.1, -56.9), (5.9, 7.0), (zf - 0.1, zf + 0.1), GL, 0.04)
    cb(p, (-59.5, 6.35, zf + 0.5), (0.55, 0.55, 0.55), LANT, 0.03)
    for xe in (-72.2, -51.8):
        bx(p, (xe - 0.1, xe + 0.1), (1.25, 7.0), (zb + 0.22, zf - 0.22), GL, 0.04)
        bx(p, (xe - 0.18, xe + 0.18), (1.25, 7.0), (-51.15, -50.85), WHITE, 0.03)
        bx(p, (xe - 0.18, xe + 0.18), (3.9, 4.15), (zb + 0.22, zf - 0.22), WHITE, 0.03)
    bx(p, (-72.4, -51.6), (7.0, 7.35), (zb - 0.3, zb + 0.3), WHITE, 0.03)
    bx(p, (-72.4, -51.6), (7.0, 7.35), (zf - 0.3, zf + 0.3), WHITE, 0.03)
    for xe in (-72.2, -51.8):
        bx(p, (xe - 0.3, xe + 0.3), (7.0, 7.35), (zb, zf), WHITE, 0.03)
    dk.prism(p, (-62, 7.3, -51), 21.4, 8.2, 1.3, GL, ridge='x', jitter=0.04)
    dk.prism(p, (-62, 8.1, -51), 15.0, 5.4, 0.95, GL2, ridge='x', jitter=0.04)
    for x in posts:
        bar(p, (x, 7.45, -55.0), (x, 8.72, -51.0), 0.22, WHITE, 0.03)
        bar(p, (x, 7.45, -47.0), (x, 8.72, -51.0), 0.22, WHITE, 0.03)
    bx(p, (-73, -51), (8.55, 9.05), (-51.35, -50.65), WHITE, 0.03)
    for x0 in (-69.6, -56.0):
        bx(p, (x0 - 2.6, x0 + 2.6), (1.25, 2.1), (-54.0, -52.6), DWOOD, 0.04)
        bx(p, (x0 - 2.6, x0 + 2.6), (1.25, 2.1), (-49.8, -48.4), DWOOD, 0.04)
        for k in range(6):
            col = (PURPLE, LILAC, PINK, INDIGO, LILAC, PURPLE)[k]
            for zz in (-53.3, -49.1):
                cb(p, (x0 - 2.1 + k * 0.84, 2.5, zz + (0.2 if k % 2 else -0.2)), (0.6, 0.8, 0.6), col, 0.06, rot=(0, 20 * k, 0))
    bx(p, (-66.3, -57.7), (1.0, 1.55), (-47.0, -46.5), DWOOD, 0.04)
    for k in range(10):
        col = (PURPLE, LILAC, PINK, INDIGO, LILAC, PURPLE, PINK, LILAC, INDIGO, PURPLE)[k]
        cb(p, (-65.8 + k * 0.88, 1.95, -46.75), (0.5, 0.8, 0.45), col, 0.06, rot=(0, 15 * k, 0))


# ---- 25. Planetarium ---------------------------------------------------------------------------------------------------
@part("Planetarium")
def build_Planetarium(p):
    cx, cz = -62, 31
    bx(p, (-75, -49), (0, 0.8), (21, 43), STONE, 0.04)
    bx(p, (-67.6, -56.4), (0, 0.8), (43, 44.4), STONE, 0.04)
    bx(p, (-73.4, -50.6), (0.8, 1.6), (21.6, 40.4), STEEL, 0.03)
    bx(p, (-73, -51), (1.6, 12.8), (22, 40), CREAM, 0.03)
    bx(p, (-73.4, -50.6), (12.2, 12.9), (21.6, 40.4), LSILVER, 0.03)
    for k in range(7):
        x = -71.7 + k * 3.55
        if -67.0 < x < -57.0:
            continue
        bx(p, (x - 0.4, x + 0.4), (1.6, 12.2), (39.9, 40.5), LSILVER, 0.03)
        bx(p, (x - 0.4, x + 0.4), (1.6, 12.2), (21.5, 22.1), LSILVER, 0.03)
    for k in range(5):
        z = 24.0 + k * 3.4
        for xe in (-73.0, -51.0):
            bx(p, (xe - 0.45, xe + 0.45), (3.4, 9.0), (z - 0.5, z + 0.5), DNAVY, 0.03)
    for k in range(5):
        bx(p, (-70.6 + k * 3.6, -69.4 + k * 3.6), (4.6, 8.4), (21.8, 22.0), DNAVY, 0.03)
    bx(p, (-73.2, -50.8), (12.8, 13.2), (21.8, 40.2), STEEL, 0.03)
    vcyl(p, cx, 13.0, 13.5, cz, 8.9, BRASS, verts=24, jit=0.03)
    slit_dome(p, cx, 13.4, cz, 8.5, 6.7, WHITE, seg=24, rings=4, jit=0.03)
    slit_dome(p, cx, 13.4, cz, 8.58, 6.78, LILAC, seg=24, rings=4, cut=tuple(i for i in range(24) if i % 3 != 0), jit=0.02, cut_top=True)
    rod(p, (cx, 19.9, cz), (cx, 23.2, cz), 0.16, STEEL, verts=5)
    star_poly(p, (cx, 24.0, cz), 'xy', 1.1, 0.5, 0.3, GOLD, jit=0.02)
    star_poly(p, (cx, 24.0, cz), 'yz', 1.1, 0.5, 0.3, GOLD, jit=0.02)
    bx(p, (-66.3, -57.7), (0.8, 9.7), (40.0, 41.2), CREAM, 0.03)
    bx(p, (-64.2, -59.8), (0.8, 6.6), (41.15, 41.35), DNAVY, 0.03)
    bx(p, (-64.6, -59.4), (6.6, 7.0), (41.1, 41.4), BRASS, 0.03)
    star_poly(p, (cx, 8.2, 41.45), 'xy', 1.0, 0.45, 0.14, GOLD, jit=0.02)
    for x in (-66.2, -63.4, -60.6, -57.8):
        bx(p, (x - 0.55, x + 0.55), (0.8, 1.2), (43.0, 44.0), LSILVER, 0.03)
        vcyl(p, x, 1.2, 9.0, 43.5, 0.45, LSILVER, verts=8)
        bx(p, (x - 0.6, x + 0.6), (9.0, 9.5), (43.0, 44.0), LSILVER, 0.03)
    bx(p, (-67.0, -57.0), (9.5, 10.3), (40.4, 44.4), INDIGO, 0.03)
    bx(p, (-67.2, -56.8), (10.0, 10.3), (44.2, 44.4), GOLD, 0.03)
    for x in (-74.2, -49.8):
        bx(p, (x - 0.5, x + 0.5), (0.4, 1.2), (30.5, 31.5), STONE, 0.03)
        vcyl(p, x, 1.2, 6.8, 31, 0.25, DARK, verts=6)
        bx(p, (x - 0.7, x + 0.7), (6.8, 7.6), (30.3, 31.7), LANT, 0.03)


# ---- 26. Control -------------------------------------------------------------------------------------------------------
@part("Control")
def build_Control(p):
    bx(p, (49, 75), (0, 1.0), (-22, -6), STONE, 0.04)
    bx(p, (49.4, 71.4), (1.0, 12.6), (-20, -8), WHITE, 0.03)
    bx(p, (49.2, 71.6), (12.2, 12.9), (-20.2, -7.8), LSILVER, 0.03)
    bx(p, (49.2, 71.6), (1.0, 1.6), (-20.2, -7.8), STEEL, 0.03)
    bx(p, (51.4, 65.6), (3.2, 6.8), (-8.15, -7.75), TEAL, 0.03)
    for k in range(5):
        x = 51.4 + k * 3.5
        bx(p, (x - 0.15, x + 0.15), (3.1, 6.9), (-8.25, -7.7), STEEL, 0.03)
    bx(p, (51.2, 65.8), (6.8, 7.1), (-8.3, -7.7), STEEL, 0.03)
    bx(p, (51.2, 65.8), (3.0, 3.3), (-8.3, -7.7), STEEL, 0.03)
    bx(p, (66.6, 70.2), (1.0, 8.0), (-8.1, -7.7), DNAVY, 0.03)
    bx(p, (66.4, 70.4), (8.0, 8.5), (-8.3, -7.6), BRASS, 0.03)
    bx(p, (67.0, 69.8), (5.2, 7.2), (-7.75, -7.62), TEAL, 0.03)
    bx(p, (66.2, 70.6), (8.5, 9.0), (-9.0, -7.4), STEEL, 0.03)
    for k, col in enumerate((RED, TEAL, GOLD)):
        bx(p, (66.9 + k * 1.1, 67.7 + k * 1.1), (9.1, 9.7), (-8.0, -7.85), col, 0.02)
    star_poly(p, (58.5, 9.8, -8.05), 'xy', 1.7, 0.75, 0.2, GOLD, jit=0.02)
    for k in range(4):
        bx(p, (50.6 + k * 4.6, 51.6 + k * 4.6), (8.4, 11.6), (-8.05, -7.95), LSILVER, 0.02) if k != 2 else None
    for k in range(4):
        z = -18.2 + k * 2.8
        for x in (49.4, 71.4):
            bx(p, (x - 0.1, x + 0.1), (4.2, 8.4), (z - 0.5, z + 0.5), TEAL, 0.03)
    bx(p, (52, 64), (12.6, 16.2), (-19, -11), WHITE, 0.03)
    bx(p, (52.3, 63.7), (13.5, 15.4), (-11.2, -10.85), TEAL, 0.03)
    for k in range(4):
        x = 52.3 + k * 3.85
        bx(p, (x - 0.15, x + 0.15), (13.4, 15.5), (-11.3, -10.8), STEEL, 0.03)
    for xs in (52, 64):
        bx(p, (xs - 0.1, xs + 0.1), (13.5, 15.4), (-18.6, -11.4), TEAL, 0.03)
    bx(p, (51.5, 64.5), (16.2, 16.9), (-19.5, -10.5), DARK, 0.03)
    for x in (52.2, 54.2, 56.2, 58.2, 60.2, 62.2, 64.2):
        bx(p, (x - 0.07, x + 0.07), (16.9, 17.6), (-10.7, -10.55), STEEL, 0.02)
    bx(p, (51.9, 64.4), (17.4, 17.6), (-10.75, -10.5), STEEL, 0.02)
    bx(p, (53.5, 56.5), (16.9, 18.0), (-17.5, -15.0), STEEL, 0.03)
    bx(p, (59.0, 61.0), (16.9, 17.6), (-16.2, -14.8), DSTEEL, 0.03)
    bx(p, (69, 73), (12.6, 14.8), (-18.6, -14.6), STEEL, 0.03)
    bx(p, (69.3, 72.7), (14.8, 15.1), (-18.3, -14.9), DSTEEL, 0.03)
    vcyl(p, 71, 15.1, 19.7, -16.6, 0.4, STEEL, verts=6)
    dish(p, (71.0, 18.8, -16.6), 2.0, 0.6, 35, 55, WHITE, feed=1.6, beacon=RED)
    vcyl(p, 51, 1.0, 9.0, -7, 0.3, STEEL, verts=6)
    bx(p, (51.3, 53.6), (7.3, 8.8), (-7.15, -6.95), RED, 0.03)
    star_poly(p, (52.3, 8.05, -6.9), 'xy', 0.5, 0.22, 0.06, WHITE, jit=0.02)
    cb(p, (51, 9.2, -7), (0.4, 0.4, 0.4), GOLD, 0.03, rot=(0, 45, 45))
    for k in range(3):
        bx(p, (72.2, 73.2), (1.0, 2.2), (-14.0 - k * 1.6, -13.0 - k * 1.6), DSTEEL, 0.03)


# ---- 27. Armillary -----------------------------------------------------------------------------------------------------
@part("Armillary")
def build_Armillary(p):
    cx, cz, cy = -17, -27, 8.8
    bx(p, (-21, -13), (0, 0.6), (-31, -23), STONE, 0.04)
    bx(p, (-20.2, -13.8), (0.6, 1.2), (-30.2, -23.8), DSTONE, 0.04)
    vcyl(p, cx, 1.2, 1.8, cz, 1.7, BRASS, verts=8)
    vcyl(p, cx, 1.8, 4.2, cz, 0.7, BRASS, verts=8, top_r=0.5)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        rod(p, (cx + 0.5 * math.cos(a), 2.6, cz + 0.5 * math.sin(a)), (cx + 2.9 * math.cos(a), 1.2, cz + 2.9 * math.sin(a)), 0.2, DBRASS, verts=5)
    ring(p, (cx, cy, cz), 5.7, 0.26, BRASS, axis='y', segs=26, sides=4, jit=0.03)
    ring(p, (cx, cy, cz), 5.7, 0.26, BRASS, axis='z', segs=26, sides=4, jit=0.03)
    ring(p, (cx, cy, cz), 5.7, 0.26, COPPER, axis='y', segs=26, sides=4, jit=0.03, rot=(0, 0, 50))
    rod(p, (cx, 4.0, cz), (cx, 15.2, cz), 0.2, STEEL, verts=6)
    ball(p, (cx, cy, cz), 1.45, GOLD, subdiv=1, jit=0.05)
    star_poly(p, (cx, cy, cz), 'xy', 2.4, 0.9, 0.35, GOLD, n=8, rot0=90, jit=0.02)
    star_poly(p, (cx, cy, cz), 'yz', 2.4, 0.9, 0.35, LGOLD, n=8, rot0=90, jit=0.02)
    cb(p, (cx, 15.4, cz), (0.6, 1.0, 0.6), GOLD, 0.03, rot=(0, 45, 0))
    for dx, dy in ((5.7, 0), (-5.7, 0), (0, 5.7), (0, -5.7)):
        ball(p, (cx + dx, cy + dy, cz), 0.45, LGOLD, subdiv=1, jit=0.03)
    for a in (50, 230):
        ball(p, (cx + 5.7 * math.cos(math.radians(a)), cy + 5.7 * math.sin(math.radians(a)), cz), 0.5, TEAL, subdiv=1, jit=0.04)


# ---- 28. GreatDome -----------------------------------------------------------------------------------------------------
@part("GreatDome")
def build_GreatDome(p):
    cx, cz = -62, -22
    bx(p, (-75, -49), (0, 1.6), (-35, -9), STONE, 0.04)
    bx(p, (-74.2, -49.8), (1.6, 1.9), (-34.2, -9.8), DSTONE, 0.04)
    vcyl(p, cx, 1.9, 15.6, cz, 11.0, SILVER, verts=24, jit=0.03)
    for y in (5.6, 10.6):
        vcyl(p, cx, y, y + 0.4, cz, 11.25, STEEL, verts=24, jit=0.03)
    for row, y in enumerate((7.2, 12.4)):
        for k in range(14):
            a = math.radians(k * 360 / 14 + (10 if row else 0))
            if 50 < math.degrees(a) % 360 < 130:
                continue
            cb(p, (cx + 11.05 * math.cos(a), y, cz + 11.05 * math.sin(a)), (1.0, 2.6, 0.4), DNAVY, 0.03, rot=(0, -math.degrees(a) + 90, 0))
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        if 60 < math.degrees(a) < 120:
            continue
        cb(p, (cx + 11.1 * math.cos(a), 8.8, cz + 11.1 * math.sin(a)), (1.2, 13.8, 1.2), STEEL, 0.03, rot=(0, -math.degrees(a) + 90, 0))
    vcyl(p, cx, 15.6, 16.2, cz, 11.7, BRASS, verts=24, jit=0.03)
    slit_dome(p, cx, 16.1, cz, 11.0, 11.5, WHITE, seg=36, rings=5, cut=(8, 9), jit=0.03)
    slit_dome(p, cx, 16.1, cz, 10.3, 10.8, DNAVY, seg=18, rings=3)
    A, B = (-62, 17.6, -19.6), (-62, 25.6, -10.4)
    rod(p, A, B, 1.4, COPPER, verts=10)
    for t in (0.35, 0.62):
        a, b = along(A, B, t - 0.03), along(A, B, t + 0.03)
        rod(p, a, b, 1.55, BRASS, verts=10)
    a, b = along(A, B, 0.85), along(A, B, 1.0)
    rod(p, a, b, 1.7, STEEL, verts=10)
    rod(p, b, along(A, B, 1.02), 1.2, DARK, verts=10)
    rod(p, (cx, 27.4, cz), (cx, 32.1, cz), 0.25, STEEL, verts=5)
    ball(p, (cx, 32.1, cz), 0.5, GOLD, subdiv=1, jit=0.03)
    bx(p, (-66.5, -57.5), (0, 9.5), (-11.8, -7.4), CREAM, 0.03)
    dk.prism(p, (cx, 9.5, -9.6), 9.8, 5.0, 1.6, STEEL, ridge='z', jitter=0.03)
    bx(p, (-64.2, -59.8), (1.5, 7.0), (-7.55, -7.35), DNAVY, 0.03)
    bx(p, (-64.6, -59.4), (7.0, 7.4), (-7.6, -7.3), BRASS, 0.03)
    star_poly(p, (cx, 8.4, -7.3), 'xy', 0.9, 0.4, 0.12, GOLD, jit=0.02)
    bx(p, (-65.4, -58.6), (0, 0.8), (-7.4, -5.9), DSTONE, 0.04)
    bx(p, (-64.8, -59.2), (0.8, 1.4), (-7.4, -6.6), STONE, 0.04)
    for x in (-66.0, -58.0):
        bx(p, (x - 0.3, x + 0.3), (1.4, 5.4), (-7.55, -7.25), STEEL, 0.03)
        bx(p, (x - 0.5, x + 0.5), (5.4, 5.9), (-7.7, -7.1), BRASS, 0.03)


# ---- 29. Spire ---------------------------------------------------------------------------------------------------------
@part("Spire")
def build_Spire(p):
    cx, cz = 62, -46
    bx(p, (55, 69), (0, 1.2), (-53, -39), STONE, 0.04)
    bx(p, (55.8, 68.2), (1.2, 1.5), (-52.2, -39.8), DSTONE, 0.04)
    legs = [(sx * 4.4, sz * 4.4) for sx in (-1, 1) for sz in (-1, 1)]
    for dx, dz in legs:
        bx(p, (cx + dx - 0.6, cx + dx + 0.6), (1.2, 17.0), (cz + dz - 0.6, cz + dz + 0.6), STEEL, 0.03)
    for (y0, y1) in ((1.5, 6.5), (6.5, 11.8), (11.8, 17.0)):
        for (x0, z0, x1, z1) in ((-4.4, -4.4, 4.4, -4.4), (-4.4, 4.4, 4.4, 4.4), (-4.4, -4.4, -4.4, 4.4), (4.4, -4.4, 4.4, 4.4)):
            bar(p, (cx + x0, y0, cz + z0), (cx + x1, y1, cz + z1), 0.3, DSTEEL, 0.03)
        for (x0, z0, x1, z1) in ((-4.4, -4.4, 4.4, -4.4), (-4.4, 4.4, 4.4, 4.4), (-4.4, -4.4, -4.4, 4.4), (4.4, -4.4, 4.4, 4.4)):
            bx(p, (cx + min(x0, x1) - 0.3, cx + max(x0, x1) + 0.3), (y1 - 0.2, y1 + 0.2), (cz + min(z0, z1) - 0.3, cz + max(z0, z1) + 0.3), DSTEEL, 0.03)
    bx(p, (cx - 5.5, cx + 5.5), (17.0, 18.2), (cz - 5.5, cz + 5.5), DARK, 0.03)
    for k in range(6):
        t = -5.2 + k * 2.08
        for (x, z) in ((cx + t, cz - 5.3), (cx + t, cz + 5.3), (cx - 5.3, cz + t), (cx + 5.3, cz + t)):
            bx(p, (x - 0.08, x + 0.08), (18.2, 19.0), (z - 0.08, z + 0.08), STEEL, 0.02)
    bx(p, (cx - 5.4, cx + 5.4), (18.9, 19.1), (cz - 5.4, cz + 5.4), STEEL, 0.03)
    sh = 1.7
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (cx + sx * sh - 0.2, cx + sx * sh + 0.2), (18.2, 37.5), (cz + sz * sh - 0.2, cz + sz * sh + 0.2), STEEL, 0.03)
    for k in range(5):
        y0, y1 = 18.2 + k * 3.86, 18.2 + (k + 1) * 3.86
        for (x0, z0, x1, z1) in ((-sh, -sh, sh, -sh), (-sh, sh, sh, sh), (-sh, -sh, -sh, sh), (sh, -sh, sh, sh)):
            if k % 2 == 0:
                bar(p, (cx + x0, y0, cz + z0), (cx + x1, y1, cz + z1), 0.16, DSTEEL, 0.03)
            else:
                bar(p, (cx + x1, y0, cz + z1), (cx + x0, y1, cz + z0), 0.16, DSTEEL, 0.03)
        bx(p, (cx - sh - 0.25, cx + sh + 0.25), (y1 - 0.1, y1 + 0.1), (cz - sh - 0.25, cz + sh + 0.25), DSTEEL, 0.03)
    vcyl(p, cx, 37.3, 38.4, cz, 2.2, SILVER, verts=14, top_r=4.5)
    vcyl(p, cx, 38.4, 39.7, cz, 4.5, LSILVER, verts=14)
    vcyl(p, cx, 39.7, 40.8, cz, 4.5, SILVER, verts=14, top_r=3.1)
    vcyl(p, cx, 40.8, 43.6, cz, 3.1, NAVY, verts=12)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        cb(p, (cx + 3.12 * math.cos(a), 42.2, cz + 3.12 * math.sin(a)), (0.5, 1.4, 0.3), TEAL, 0.03, rot=(0, -math.degrees(a) + 90, 0))
    vcyl(p, cx, 43.6, 44.0, cz, 3.5, DSTEEL, verts=12)
    vcyl(p, cx, 44.0, 46.7, cz, 3.2, WHITE, verts=8, top_r=2.7)
    vcyl(p, cx, 46.7, 47.0, cz, 2.9, DSTEEL, verts=8)
    rod(p, (cx, 47.0, cz), (cx, 52.0, cz), 0.3, STEEL, verts=6)
    bx(p, (cx - 1.6, cx + 1.6), (49.0, 49.3), (cz - 0.15, cz + 0.15), STEEL, 0.03)
    bx(p, (cx - 1.0, cx + 1.0), (50.2, 50.4), (cz - 0.15, cz + 0.15), STEEL, 0.03)
    cb(p, (cx, 52.0, cz), (1.2, 1.2, 1.2), RED, 0.03, rot=(0, 45, 0))


# ---- 30. Galaxy --------------------------------------------------------------------------------------------------------
@part("Galaxy")
def build_Galaxy(p):
    cx, cz, cy = -24, -46, 6.8
    tilt = 12
    bx(p, (-33, -15), (0, 0.8), (-55, -37), DARK, 0.04)
    bx(p, (-31.8, -16.2), (0.8, 1.6), (-53.8, -38.2), DSTEEL, 0.04)
    vcyl(p, cx, 1.6, 5.6, cz, 3.5, STONE, verts=10, top_r=2.6)
    vcyl(p, cx, 1.6, 2.3, cz, 3.9, DSTONE, verts=10)

    def at(r, ang, dy=0.0):
        a = math.radians(ang)
        dx, dz = r * math.cos(a), r * math.sin(a)
        t = math.radians(tilt)
        return (cx + dx, cy + dy * math.cos(t) - dz * math.sin(t), cz + dz * math.cos(t) + dy * math.sin(t))
    dk.cyl(p, (cx, cy - 0.35, cz), 8.2, 0.7, (30, 36, 92), axis='y', verts=24, rot=(tilt, 0, 0), jitter=0.04)
    dk.cyl(p, (cx, cy - 0.28, cz), 6.4, 0.7, (44, 52, 124), axis='y', verts=20, rot=(tilt, 0, 0), jitter=0.04)
    pal = (LGOLD, GOLD, (228, 176, 108), (210, 150, 170), LILAC, PURPLE, INDIGO)
    for k in range(3):
        for i in range(15):
            t = i / 14.0
            r = 2.8 + t * 5.0
            phi = k * 120 + t * 250
            x, y, z = at(r, phi, 0.28)
            col = pal[min(len(pal) - 1, int(t * len(pal)))]
            ln, wd = 2.5 - t * 0.5, 2.0 - t * 1.1
            dk.box(p, (x, y, z), (ln, 0.55, wd), col, rot=(tilt, -(phi + 90 - 22), 0), jitter=0.06)
    ball(p, (cx, cy + 0.5, cz), 2.6, GOLD, scale=(1, 0.72, 1), subdiv=2, jit=0.05)
    cb(p, (cx, cy + 1.7, cz), (1.2, 1.2, 1.2), LGOLD, 0.04, rot=(0, 30, 0))
    rod(p, (cx, cy + 2.2, cz), (cx, 15.2, cz), 0.3, STEEL, verts=6)
    ball(p, (cx, 15.2, cz), 0.8, WHITE, subdiv=1, jit=0.03)
    for k, (r, ang, dy) in enumerate(((7.4, 20, 1.6), (6.0, 150, -1.0), (8.0, 250, 1.0), (4.6, 80, 1.8), (7.0, 330, -0.8), (5.5, 200, 2.0))):
        x, y, z = at(r, ang, dy)
        cb(p, (x, y, z), (0.55, 0.55, 0.55), WHITE if k % 2 else LILAC, 0.04, rot=(0, 30 * k, 45))


# ==== PARTS_END ====


# ==== MAIN ====
MISSING = []
AZ = {}
ELEV = {}
MULT = {"Ground": 1.9, "Sign": 2.9}
SHIBA_AT = {"Ground": None}


def shiba_for(x, z, facing, lift=0.0):
    # the meshes are mirrored in x before export (decorkit), so the reference Shiba is placed mirrored too
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}}, studs=7.0)
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
    stats = {}
    for pj in BP["Parts"]:
        pid = pj["Id"]
        if ONLY and pid not in ONLY:
            continue
        fn = REG.get(pid)
        if fn is None:
            MISSING.append(pid)
            continue
        part = dk.Part(pid)
        groups = fn(part)
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        stats[pid] = (len(meshes), sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons))
        built[pid] = meshes
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        if pid == "Ground":
            x, z, f = BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"]
        else:
            x = hi[0] + 5 if hi[0] + 5 < 78 else lo[0] - 5
            z = hi[2] - 3
            x, z, f = SHIBA_AT.get(pid) or (x, z, 270)
        sb = shiba_for(x, z, f)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 160), ELEV.get(pid, 28),
             MULT.get(pid, 2.3), (1400, 1000))
        drop(sb)
    print("STATS", json.dumps(stats))
    print("MISSING", MISSING)
    if stats:
        print("SUMMARY parts", len(stats), "max tris", max(v[1] for v in stats.values()), "max meshes", max(v[0] for v in stats.values()))
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"])
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 160, 40, 2.5, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.1, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_Observatory.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        os.remove(os.path.join(OUT, f))


main()
