"""Final low-poly decor models for the theme VoidPortal (30 parts around the 30th Shiba, Void Shiba).

Usage: blender --background --factory-startup --python build_VoidPortal.py -- <outdir> [PartId,PartId,...]
Writes Decor_VoidPortal_<PartId>.fbx, preview_<PartId>.png and stage_VoidPortal.png into <outdir>.
Every model is written in STAGE coordinates (the numbers of DecorTheme30.luau) and fitted to the union box of its blueprint
pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it). Give part ids (comma
separated) after the out folder to rebuild only those parts (no stage render then).
Style: black stone, bright flat purple / cyan colours for the glow (no Neon), one mesh per part, flat vertex colours.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "VoidPortal"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "VoidPortal"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_VoidPortal.json"))
RND = random.Random(30)

# ---- palette: black stone, purple and cyan glow ---------------------------------------------------------------------------
BLACK = (18, 14, 28)
OBS = (34, 28, 48)
DSTONE = (54, 46, 74)
STONE = (80, 70, 104)
MSTONE = (68, 60, 96)
LSTONE = (112, 100, 142)
DVIOLET = (84, 36, 156)
VIOLET = (120, 56, 210)
PURPLE = (160, 80, 255)
LPURPLE = (200, 150, 255)
MAGENTA = (226, 84, 236)
CYAN = (72, 228, 255)
DCYAN = (28, 150, 190)
LCYAN = (176, 246, 255)
PALE = (226, 214, 255)


# ---- basic helpers ----------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, top_r=None):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit, top_radius=top_r)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv + 1, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (absolute stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def frustum(p, cx, y0, y1, cz, wb, db, wt, dt, col, jit=0.04, yaw=0):
    """Box that narrows from wb x db at y0 to wt x dt at y1; yaw turns it about its own vertical axis."""
    pts = [(-wb / 2, y0, -db / 2), (wb / 2, y0, -db / 2), (wb / 2, y0, db / 2), (-wb / 2, y0, db / 2),
           (-wt / 2, y1, -dt / 2), (wt / 2, y1, -dt / 2), (wt / 2, y1, dt / 2), (-wt / 2, y1, dt / 2)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (cx, 0, cz), pts, faces, col, jit, rot=(0, yaw, 0))


def lathe(p, cx, cz, prof, col, verts=10, jit=0.04, sx=1.0, sz=1.0, rot0=0.0, shear=(0.0, 0.0), caps=True, loop=False):
    """Solid of revolution about the vertical axis through (cx, cz). prof = [(radius, y), ...] bottom to top; radius 0 makes a
    point. Closed with caps. shear = (dx, dz) per unit of height leans the whole thing."""
    pts, rings = [], []
    y_first = prof[0][1]
    for (r, y) in prof:
        ox, oz = shear[0] * (y - y_first), shear[1] * (y - y_first)
        if r < 1e-6:
            rings.append([len(pts)])
            pts.append((cx + ox, y, cz + oz))
        else:
            idx = []
            for k in range(verts):
                a = rot0 + 2 * math.pi * k / verts
                idx.append(len(pts))
                pts.append((cx + ox + r * math.cos(a) * sx, y, cz + oz + r * math.sin(a) * sz))
            rings.append(idx)
    faces = []
    pairs = list(range(len(rings) - 1)) + ([len(rings) - 1] if loop else [])
    for i in pairs:
        a, b = rings[i], rings[(i + 1) % len(rings)]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            faces += [(a[0], b[(k + 1) % verts], b[k]) for k in range(verts)]
        elif len(b) == 1:
            faces += [(a[k], a[(k + 1) % verts], b[0]) for k in range(verts)]
        else:
            faces += [(a[k], a[(k + 1) % verts], b[(k + 1) % verts], b[k]) for k in range(verts)]
    if caps and len(rings[0]) > 1:
        faces.append(tuple(reversed(rings[0])))
    if caps and len(rings[-1]) > 1:
        faces.append(tuple(rings[-1]))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def xf(p, i0, pivot=(0, 0, 0), rot=(0, 0, 0), shift=(0, 0, 0), sc=1.0):
    """Scale, rotate (degrees, Roblox order about the stage axes) and move everything added to the part since index i0, about pivot."""
    rx, ry, rz = (math.radians(a) for a in rot)
    r_stage = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
    r_bl = dk.SWAP @ r_stage @ dk.SWAP.transposed()
    pv = S(*pivot)
    scl = Matrix.Scale(sc, 4) if not isinstance(sc, tuple) else Matrix.Diagonal((sc[0], sc[2], sc[1], 1.0))
    M = Matrix.Translation(S(*shift)) @ Matrix.Translation(pv) @ r_bl.to_4x4() @ scl @ Matrix.Translation(-pv)
    for o in p.objs[i0:]:
        o.matrix_world = M @ o.matrix_world


def crystal(p, cx, y0, cz, r, h, col, sides=6, lean=(0.0, 0.0), jit=0.08, tipf=0.3, rot0=0.0):
    """Pointed crystal standing on y0: faceted prism with a pyramid tip; lean = (dx, dz) offset of the tip."""
    return lathe(p, cx, cz, [(r * 0.8, y0), (r, y0 + 0.12 * h), (r, y0 + (1 - tipf) * h), (0, y0 + h)], col, verts=sides,
                 jit=jit, shear=(lean[0] / h, lean[1] / h), rot0=rot0)


def shard(p, c, w, h, d, col, rot=(0, 0, 0), sides=5, jit=0.08):
    """Floating shard: double pyramid about centre c, w x d wide, h tall, turned by rot."""
    i0 = len(p.objs)
    lathe(p, c[0], c[2], [(0, c[1] - h / 2), (0.5, c[1] - h * 0.18), (0.5, c[1] + h * 0.08), (0, c[1] + h / 2)], col, verts=sides,
          jit=jit, sx=w, sz=d)
    xf(p, i0, pivot=c, rot=rot)


def seg(p, a, b, w, y0, y1, col, jit=0.04):
    """Flat bar on the floor from a = (x, z) to b, width w, from y0 to y1."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dz)
    return dk.box(p, ((a[0] + b[0]) / 2, (y0 + y1) / 2, (a[1] + b[1]) / 2), (ln, y1 - y0, w), col,
                  rot=(0, -math.degrees(math.atan2(dz, dx)), 0), jitter=jit)


def tube(p, pts, radii, col, sides=8, jit=0.05, cap_start=True, cap_end=True, tip=False):
    """Pipe along a polyline of 3D points with a radius per point (stage coordinates). tip=True closes the end in a point."""
    ring_pts, faces = [], []
    n = len(pts)
    for i, c in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, n - 1)])
        t = (b - a).normalized()
        ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        v = t.cross(u).normalized()
        for k in range(sides):
            ang = 2 * math.pi * k / sides
            q = Vector(c) + (u * math.cos(ang) + v * math.sin(ang)) * radii[i]
            ring_pts.append(tuple(q))
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k2, (i + 1) * sides + k2, (i + 1) * sides + k))
    if cap_start:
        faces.append(tuple(reversed(range(sides))))
    if tip:
        apex = len(ring_pts)
        last = Vector(pts[-1])
        d = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
        ring_pts.append(tuple(last + d * radii[-1] * 1.6))
        faces += [((n - 1) * sides + k, (n - 1) * sides + (k + 1) % sides, apex) for k in range(sides)]
    elif cap_end:
        faces.append(tuple(range((n - 1) * sides, n * sides)))
    return dk.poly(p, (0, 0, 0), ring_pts, faces, col, jit)


def torus(p, c, R, r, col, segs=16, sides=6, scale_y=1.0, jit=0.04, rot=(0, 0, 0)):
    """Ring lying flat (axis up) around centre c, tube radius r (scale_y flattens it); rot turns it about its centre."""
    pts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(sides):
            b = 2 * math.pi * j / sides + math.pi / sides
            rr = R + r * math.cos(b)
            pts.append((rr * math.cos(a), r * scale_y * math.sin(b), rr * math.sin(a)))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2))
    return dk.poly(p, c, pts, faces, col, jit, rot=rot)


def halo(p, c, R, r, col, segs=18, sides=4, jit=0.03, rot=(0, 0, 0), sq=1.0):
    """Ring standing in the x-y plane (faces +z) around centre c, tube radius r (sq stretches the tube along z)."""
    pts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(sides):
            b = 2 * math.pi * j / sides + math.pi / 4
            rr = R + r * math.cos(b)
            pts.append((rr * math.cos(a), rr * math.sin(a), r * sq * math.sin(b)))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2))
    return dk.poly(p, c, pts, faces, col, jit, rot=rot)


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


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.04):
    """Bar in the x-y plane from (x1,y1) to (x2,y2), thickness t, depth along z centred on z."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def letter(p, ch, x0, y0, z0, z1, w, h, t, col):
    """Block letter in the x-y plane (readable from +z)."""
    zc, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zc, x0 + c, y0 + e, t, d, col, 0.03)
    if ch == 'T':
        r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h - t)
    elif ch == 'H':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'E':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2); r(t, 0, w, t)
    elif ch == 'V':
        dg(t * 0.5, h, w / 2, t * 0.4); dg(w - t * 0.5, h, w / 2, t * 0.4)
    elif ch == 'O':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'I':
        r(0, 0, w, t); r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h)
    elif ch == 'D':
        r(0, 0, t, h); r(t, h - t, w - t, h); r(t, 0, w - t, t); r(w - t, t, w, h - t)


def text(p, s, cx, y0, z0, z1, w, h, t, gap, col):
    total = len(s) * w + (len(s) - 1) * gap
    x = cx - total / 2
    for ch in s:
        if ch != ' ':
            letter(p, ch, x, y0, z0, z1, w, h, t, col)
        x += w + gap


def rune(p, cx, cy, cz, s, col, seed=0, depth=0.16):
    """A small abstract glyph (3 to 4 thin bars) of height s on the plane z = cz, facing +z."""
    rr = random.Random(seed)
    t = s * 0.14
    bx(p, (cx - t / 2, cx + t / 2), (cy - s / 2, cy + s / 2), (cz, cz + depth), col, 0.0)
    k = rr.randint(0, 3)
    if k == 0:
        diag(p, cx - s * 0.35, cy + s * 0.05, cz + depth / 2, cx, cy + s * 0.45, t, depth, col, 0.0)
        bx(p, (cx, cx + s * 0.3), (cy - s * 0.3 - t / 2, cy - s * 0.3 + t / 2), (cz, cz + depth), col, 0.0)
    elif k == 1:
        bx(p, (cx - s * 0.3, cx + s * 0.3), (cy + s * 0.2 - t / 2, cy + s * 0.2 + t / 2), (cz, cz + depth), col, 0.0)
        diag(p, cx, cy - s * 0.1, cz + depth / 2, cx + s * 0.35, cy - s * 0.45, t, depth, col, 0.0)
    elif k == 2:
        diag(p, cx - s * 0.35, cy - s * 0.45, cz + depth / 2, cx, cy, t, depth, col, 0.0)
        diag(p, cx, cy, cz + depth / 2, cx + s * 0.35, cy + s * 0.45, t, depth, col, 0.0)
    else:
        bx(p, (cx - s * 0.3, cx + s * 0.3), (cy - s * 0.2 - t / 2, cy - s * 0.2 + t / 2), (cz, cz + depth), col, 0.0)
        bx(p, (cx - s * 0.3 - t / 2, cx - s * 0.3 + t / 2), (cy - s * 0.2, cy + s * 0.3), (cz, cz + depth), col, 0.0)
    bx(p, (cx + t, cx + t * 3), (cy + s * 0.32, cy + s * 0.32 + t * 2), (cz, cz + depth), col, 0.0)


def spiky(p, cx, y0, cz, r, h, col, sides=4, lean=(0, 0), jit=0.08):
    """Plain cone / spike."""
    return lathe(p, cx, cz, [(r, y0), (0, y0 + h)], col, verts=sides, jit=jit, shear=(lean[0] / h, lean[1] / h))


def orb(p, c, r, col, subdiv=1, jit=0.03):
    return ball(p, c, r, col, subdiv=subdiv, jit=jit)


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
    sc = [(th[i] - tl[i]) / max(1e-6, (bh[i] - bl[i])) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    print(f"FIT {part.id}: scale stage xyz = {sc[0]:.3f} {sc[2]:.3f} {sc[1]:.3f}")


# ---- 1. Ground --------------------------------------------------------------------------------------------------------------
PATH = [(0, 95), (-6, 72), (40, 56), (62, 24), (24, 6), (-8, -18), (-12, -42), (-56, -58), (-22, -78), (0, -95)]


def build_Ground(p):
    B(p, 0, 0.09, 0, 190, 0.18, 190, DVIOLET, jit=0.0)                       # glowing seams show between the tiles
    n = 4
    w = 190 / n
    for i in range(n):
        for j in range(n):
            B(p, -95 + w * (i + 0.5), 0.24, -95 + w * (j + 0.5), w - 1.3, 0.12, w - 1.3, BLACK, jit=0.5)
    # dark plaza under the Shiba with a violet rune ring and an eight-pointed star
    B(p, -26, 0.4, -30, 32, 0.2, 32, DSTONE, jit=0.1)
    torus(p, (-26, 0.53, -30), 11.5, 0.5, VIOLET, segs=24, sides=4, scale_y=0.12)
    star_poly(p, (-26, 0.51, -30), 'xz', 9.0, 5.2, 0.06, PURPLE, n=8, rot0=90)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        B(p, -26 + 14.2 * math.cos(a), 0.53, -30 + 14.2 * math.sin(a), 1.2, 0.1, 1.2, CYAN, rot=(0, -45 * k, 0), jit=0.0)
    # flagstones along the whole walkway, every third one with a cyan rune dot
    k = 0
    for i in range(len(PATH) - 1):
        a, b = PATH[i], PATH[i + 1]
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = int(ln // 6.8)
        for s in range(steps):
            t = (s + 0.5) / steps
            cx, cz = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            dx, dz = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
            seg(p, (cx - dx * 3.0, cz - dz * 3.0), (cx + dx * 3.0, cz + dz * 3.0), 6.4 + RND.uniform(-0.6, 0.2), 0.3, 0.42,
                STONE, jit=0.3)
            if k % 4 == 0:
                B(p, cx, 0.45, cz, 0.9, 0.06, 0.9, CYAN, rot=(0, 45, 0), jit=0.0)
            k += 1
    # cracks of violet light in the tiles
    for _ in range(7):
        x, z = RND.uniform(-85, 85), RND.uniform(-85, 85)
        for _s in range(3):
            nx, nz = x + RND.uniform(-9, 9), z + RND.uniform(-9, 9)
            seg(p, (x, z), (nx, nz), 0.45, 0.3, 0.34, PURPLE, jit=0.1)
            x, z = nx, nz


# ---- 2. Gate ----------------------------------------------------------------------------------------------------------------
def pylon(p, cx, cz):
    B(p, cx, 0.9, cz, 7, 1.8, 7, STONE)
    frustum(p, cx, 1.8, 14.2, cz, 4.8, 4.8, 3.8, 3.8, OBS, jit=0.08)
    for y in (4.8, 9.0):                                           # carved bands
        B(p, cx, y, cz, 5.2, 0.55, 5.2, DSTONE)
    for sx in (-1, 1):                                             # corner ribs
        for sz in (-1, 1):
            B(p, cx + sx * 2.1, 8, cz + sz * 2.1, 0.7, 12.4, 0.7, STONE)
    for y, s in ((7.0, 1), (11.6, 2)):                             # glowing glyphs on the road side
        rune(p, cx, y, cz + 2.45, 2.0, CYAN, seed=int(cx) + s)
    bx(p, (cx - 2.9, cx - 2.35), (3.0, 13.5), (cz - 0.3, cz + 0.3), CYAN, 0.0)
    bx(p, (cx + 2.35, cx + 2.9), (3.0, 13.5), (cz - 0.3, cz + 0.3), CYAN, 0.0)
    B(p, cx, 14.8, cz, 6, 1.2, 6, VIOLET)
    frustum(p, cx, 15.4, 16.4, cz, 3.8, 3.8, 2.4, 2.4, DSTONE)
    for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):            # prongs holding the orb
        spiky(p, cx + sx * 1.3, 15.4, cz + sz * 1.3, 0.35, 3.6, VIOLET, sides=4, lean=(-sx * 0.7, -sz * 0.7))
    orb(p, (cx, 18.0, cz), 1.6, CYAN, subdiv=1)
    orb(p, (cx, 18.0, cz), 0.8, LCYAN, subdiv=0)


def build_Gate(p):
    pylon(p, -15, 90)
    pylon(p, 15, 90)
    # floating arch of shards between the pylons
    for i in range(9):
        t = 180 * i / 8
        col = CYAN if i == 4 else (PURPLE if i % 2 == 0 else VIOLET)
        h = 4.4 if i == 4 else 3.8
        shard(p, (11.0 * math.cos(math.radians(t)), 7.6 + 11.0 * math.sin(math.radians(t)), 90), 1.5, h, 1.2, col, rot=(0, 0, t), sides=4)
    for i in range(8):                                             # small chips between the shards
        t = 180 * (i + 0.5) / 8
        B(p, 11.0 * math.cos(math.radians(t)), 7.6 + 11.0 * math.sin(math.radians(t)), 90, 0.5, 0.5, 0.5, LPURPLE, rot=(30, 30, t), jit=0.1)


# ---- 3. Sign ----------------------------------------------------------------------------------------------------------------
def build_Sign(p):
    cx, cz = -26, 84
    B(p, cx, 3.8, cz, 22, 6.4, 1.4, OBS, jit=0.06)                  # board y 0.6..7.0
    for x0, x1, y0, y1 in ((cx - 11, cx + 11, 0.6, 1.1), (cx - 11, cx + 11, 6.5, 7.0), (cx - 11, cx - 10.5, 0.6, 7.0),
                           (cx + 10.5, cx + 11, 0.6, 7.0)):
        bx(p, (x0, x1), (y0, y1), (cz + 0.6, cz + 0.9), VIOLET, 0.0)
    text(p, "THE VOID", cx, 2.1, cz + 0.7, cz + 1.05, 1.85, 3.4, 0.5, 0.5, CYAN)
    B(p, cx, 7.8, cz, 23, 1.2, 2.2, VIOLET)                         # top bar
    for dx in (-8.5, -4.2, 0, 4.2, 8.5):                            # teeth along the top bar
        crystal(p, cx + dx, 8.4, cz, 0.55, 1.5 + (0.5 if dx == 0 else 0), PURPLE, sides=4)
    for sx in (-1, 1):
        px = cx + sx * 9.0
        frustum(p, px, 0, 3.6, cz - 0.9, 2.2, 1.0, 1.6, 0.8, STONE)
        B(p, px, 0.3, cz - 0.3, 3.2, 0.6, 2.0, LSTONE)
        ex = cx + sx * 12.5                                         # orb on a little crystal cradle at the end of the bar
        for k in range(4):
            a = math.radians(45 + 90 * k)
            spiky(p, ex + 0.9 * math.cos(a), 7.4, cz + 0.9 * math.sin(a), 0.3, 2.6, VIOLET, sides=4, lean=(-0.5 * math.cos(a), -0.5 * math.sin(a)))
        orb(p, (ex, 8.6, cz), 1.3, CYAN, subdiv=1)


# ---- 4. RuneStones ----------------------------------------------------------------------------------------------------------
def build_RuneStones(p):
    cx, cz = -64, 78
    B(p, cx, 0.35, cz, 13, 0.2, 13, DVIOLET, jit=0.0)                # y 0.25..0.45
    lathe(p, cx, cz, [(6.2, 0.4), (6.2, 0.6), (5.2, 0.6), (5.2, 0.4)], DSTONE, verts=24, jit=0.1)
    torus(p, (cx, 0.6, cz), 4.4, 0.3, CYAN, segs=24, sides=4, scale_y=0.5)
    star_poly(p, (cx, 0.52, cz), 'xz', 3.3, 1.5, 0.08, PURPLE, n=6, rot0=90)
    for k in range(6):
        a = math.radians(k * 60)
        sx, sz = cx + 9.5 * math.cos(a), cz + 9.5 * math.sin(a)
        i0 = len(p.objs)
        top = (7.0, 6.1) if k % 2 == 0 else (6.2, 7.0)
        pts = [(sx - 1.7, 0, sz - 0.8), (sx + 1.7, 0, sz - 0.8), (sx + 1.7, 0, sz + 0.8), (sx - 1.7, 0, sz + 0.8),
               (sx - 1.3, top[0], sz - 0.6), (sx + 1.3, top[1], sz - 0.6), (sx + 1.3, top[1], sz + 0.6), (sx - 1.3, top[0], sz + 0.6)]
        hexa(p, pts, DSTONE, jit=0.12)
        B(p, sx, 0.4, sz, 4.0, 0.8, 2.0, STONE)
        rune(p, sx, 3.8, sz + 0.62, 2.4, CYAN if k % 2 == 0 else LPURPLE, seed=k + 3)
        rune(p, sx, 1.6, sz + 0.62, 1.0, PURPLE, seed=k + 9)
        xf(p, i0, pivot=(sx, 0, sz), rot=(0, -(k * 60 + 90), 0))
    orb(p, (cx, 10, cz), 1.7, CYAN, subdiv=1)
    orb(p, (cx, 10, cz), 0.9, LCYAN, subdiv=0)
    for k in range(3):                                              # tiny rocks circling the orb
        a = math.radians(120 * k + 20)
        B(p, cx + 2.6 * math.cos(a), 10 + 0.8 * math.sin(3 * a), cz + 2.6 * math.sin(a), 0.7, 0.7, 0.7, VIOLET, rot=(20, 20 * k, 30), jit=0.1)


# ---- 5. Braziers ------------------------------------------------------------------------------------------------------------
def build_Braziers(p):
    for (x, z) in ((28, 86), (40, 81), (52, 86)):
        frustum(p, x, 0, 1.8, z, 3.6, 3.6, 3.0, 3.0, LSTONE)
        lathe(p, x, z, [(1.1, 1.8), (1.4, 2.1), (2.3, 2.5), (2.3, 2.7), (1.8, 2.7), (1.8, 2.45), (0, 2.4)], OBS, verts=8, jit=0.08)
        lathe(p, x, z, [(2.3, 2.62), (2.3, 2.75), (1.85, 2.75), (1.85, 2.62)], VIOLET, verts=8, jit=0.0)
        lathe(p, x, z, [(1.55, 2.6), (1.3, 3.5), (0.95, 4.7), (0.45, 5.9), (0, 6.6)], PURPLE, verts=8, jit=0.12)
        lathe(p, x, z, [(1.0, 2.62), (0.85, 3.4), (0.5, 4.5), (0, 5.4)], MAGENTA, verts=6, jit=0.1)
        lathe(p, x, z, [(0.5, 2.65), (0.4, 3.2), (0, 4.0)], PALE, verts=6, jit=0.05)
        for k in range(3):
            a = math.radians(120 * k + x)
            spiky(p, x + 1.2 * math.cos(a), 2.6, z + 1.2 * math.sin(a), 0.35, 3.3, VIOLET, sides=4, lean=(0.5 * math.cos(a), 0.5 * math.sin(a)))
        for k in range(3):                                          # embers
            a = math.radians(90 * k + 40 + x)
            B(p, x + 1.0 * math.cos(a), 5.0 + 0.5 * k, z + 1.0 * math.sin(a), 0.28, 0.28, 0.28, LPURPLE, rot=(20, 30, 10), jit=0.0)
        for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):          # studs on the base
            B(p, x + sx * 1.6, 1.95, z + sz * 1.6, 0.4, 0.3, 0.4, CYAN, jit=0.0)


# ---- 6. Crystals ------------------------------------------------------------------------------------------------------------
def build_Crystals(p):
    lathe(p, 76, 84, [(10, 0.0), (10, 0.35), (7.5, 0.9), (0, 1.1)], OBS, verts=12, sz=0.8, jit=0.2)
    for (x, z, r) in ((70, 80, 1.2), (83, 80, 1.0), (85, 87, 0.9), (70, 88, 1.0), (79, 91, 0.9)):          # rubble
        B(p, x, 0.5, z, r * 2, 0.9, r * 1.6, DSTONE, rot=(0, x * 11, 0), jit=0.2)
    specs = [(76, 84, 2.5, 16.0, 1.0, VIOLET, (0.6, 0.0)), (70.5, 85.5, 2.0, 10.4, 0.8, PURPLE, (-0.6, 0.4)),
             (81.5, 82.5, 1.9, 10.0, 0.5, MAGENTA, (0.5, -0.3)), (73, 80, 1.3, 6.0, 0.5, CYAN, (-0.3, -0.2)),
             (79, 87.5, 1.4, 5.6, 0.2, VIOLET, (0.3, 0.4)), (83.5, 86, 1.1, 4.8, 0.2, PURPLE, (0.3, 0.0)),
             (68, 82.5, 1.2, 5.0, 0.3, DCYAN, (-0.3, 0.1))]
    for (x, z, r, h, y0, col, lean) in specs:
        crystal(p, x, y0, z, r, h, col, sides=6, lean=lean, jit=0.1)
    for (x, z, h, col) in ((74.5, 86.5, 2.6, LPURPLE), (77.5, 80.5, 2.2, CYAN), (72, 83.5, 1.8, PURPLE), (80, 84.8, 2.4, LPURPLE),
                           (76, 88.5, 1.6, VIOLET), (82, 79.5, 1.6, CYAN)):                        # little shoots
        crystal(p, x, 0.4, z, 0.5, h, col, sides=5, lean=(0.2, 0.1))


# ---- 7. Spikes --------------------------------------------------------------------------------------------------------------
def build_Spikes(p):
    lathe(p, -80, 18, [(13, 0.0), (13, 0.4), (10, 0.8), (0, 0.8)], DSTONE, verts=14, sz=0.85, jit=0.2)
    big = [(-80, 18, 11.0, (0.4, 0.3)), (-74, 12, 8.0, (0.6, -0.4)), (-86, 12, 7.0, (-0.6, -0.3)), (-72, 24, 9.0, (0.5, 0.5)),
           (-86, 24, 10.0, (-0.6, 0.4)), (-79, 27, 6.0, (0.0, 0.6)), (-79, 8, 5.5, (0.1, -0.6))]
    for (x, z, h, lean) in big:
        lathe(p, x, z, [(1.6, 0.0), (1.15, 0.3 * h), (0.55, 0.7 * h), (0, h)], MSTONE, verts=5, jit=0.3, shear=(lean[0] / h, lean[1] / h))
        crystal(p, x + 1.5, 0.3, z - 0.6, 0.45, 1.8 + 0.1 * h, VIOLET, sides=4, lean=(0.3, 0.0), jit=0.1)
        orb(p, (x + lean[0], h + 0.25, z + lean[1]), 0.28, CYAN, subdiv=0)
    for (x, z, h) in ((-77, 15, 3.5), (-83, 15, 3.0), (-83, 21, 4.2), (-76, 19, 2.8), (-89, 18, 3.6), (-69, 18, 2.4), (-80, 12, 2.5), (-89, 9, 2.2)):
        lathe(p, x, z, [(0.85, 0.0), (0, h)], MSTONE, verts=4, jit=0.3, shear=(0.1, 0.1))
    for (x, z, h, col) in ((-75, 28, 1.8, PURPLE), (-90, 17, 1.4, CYAN), (-70, 12, 1.5, MAGENTA)):
        crystal(p, x, 0.3, z, 0.4, h, col, sides=4, jit=0.1)


# ---- 8. Rift ----------------------------------------------------------------------------------------------------------------
def build_Rift(p):
    lines = [[(4, 29.5), (11, 31.2), (17, 28.6), (24, 31.5), (31, 29.0), (40, 30.5)],
             [(10, 30), (8.7, 35), (11, 38.5), (9.2, 43)],
             [(34, 30.5), (35.4, 25), (32.8, 21), (34.2, 17)],
             [(21, 37.8), (27, 39.0), (31, 36.9), (35, 38.4)]]
    for pl in lines:
        for i in range(len(pl) - 1):
            seg(p, pl[i], pl[i + 1], 3.3, 0.0, 0.2, VIOLET, jit=0.05)
            seg(p, pl[i], pl[i + 1], 1.7, 0.0, 0.3, PURPLE, jit=0.05)
            seg(p, pl[i], pl[i + 1], 0.6, 0.0, 0.4, PALE, jit=0.0)
    for pl in lines:                                               # broken rim rocks on both sides
        for i in range(len(pl) - 1):
            mx, mz = (pl[i][0] + pl[i + 1][0]) / 2, (pl[i][1] + pl[i + 1][1]) / 2
            for sgn in (-1, 1):
                h = RND.uniform(0.4, 1.1)
                B(p, mx + sgn * RND.uniform(2.0, 2.8), h / 2, mz + sgn * RND.uniform(1.6, 2.4), RND.uniform(1.0, 1.9), h, RND.uniform(0.9, 1.6),
                  DSTONE, rot=(0, RND.uniform(0, 90), 0), jit=0.25)
    for (x, y, z, r, col) in ((14, 9, 33, 1.1, DSTONE), (24, 11.5, 28, 0.9, CYAN), (30, 8.5, 36, 1.2, DSTONE), (19, 13, 25, 0.8, PURPLE)):
        ball(p, (x, y, z), r, col, subdiv=1, jit=0.12)
    for (x, z, h) in ((7, 33, 3.2), (33, 23, 3.0), (26, 38.2, 2.4), (16, 30.2, 2.0)):
        spiky(p, x, 0.3, z, 0.4, h, LPURPLE, sides=4, jit=0.0)


# ---- 9. Lanterns ------------------------------------------------------------------------------------------------------------
def build_Lanterns(p):
    for (x, z) in ((2, 46), (34, 40), (38, 32), (4, 20)):
        frustum(p, x, 0, 0.8, z, 2.2, 2.2, 1.5, 1.5, STONE)
        lathe(p, x, z, [(0.7, 0.8), (0.42, 1.6), (0.32, 6.0), (0.5, 7.6), (0.7, 8.0)], OBS, verts=6, jit=0.1)
        for k in range(4):                                         # cage: corner posts, glass, floor, roof
            a = math.radians(45 + 90 * k)
            B(p, x + 1.0 * math.cos(a), 8.8, z + 1.0 * math.sin(a), 0.3, 1.6, 0.3, DSTONE, jit=0.05)
        B(p, x, 8.8, z, 1.6, 1.3, 1.6, DCYAN, jit=0.05)
        B(p, x, 8.8, z, 0.8, 0.9, 0.8, LCYAN, jit=0.0, rot=(0, 45, 0))
        B(p, x, 8.1, z, 2.6, 0.3, 2.6, STONE)
        lathe(p, x, z, [(1.9, 9.6), (1.1, 10.1), (0.35, 10.5)], VIOLET, verts=4, jit=0.08, rot0=math.pi / 4)
        for k in range(4):                                         # prongs up to the floating orb
            a = math.radians(90 * k)
            spiky(p, x + 0.5 * math.cos(a), 10.0, z + 0.5 * math.sin(a), 0.16, 1.2, VIOLET, sides=4, lean=(0.2 * math.cos(a), 0.2 * math.sin(a)))
        orb(p, (x, 11.2, z), 1.2, CYAN, subdiv=1)
        torus(p, (x, 11.2, z), 1.9, 0.12, LPURPLE, segs=10, sides=4, rot=(25, x * 7, 0))


# ---- 10. VoidTrees ----------------------------------------------------------------------------------------------------------
def dead_tree(p, x, z, h, seed):
    rr = random.Random(seed)
    pts = [(x, 0, z), (x + 0.4, h * 0.3, z - 0.3), (x - 0.3, h * 0.6, z + 0.3), (x + 0.3, h * 0.85, z), (x, h, z)]
    tube(p, pts, [1.05, 0.8, 0.65, 0.5, 0.35], OBS, sides=6, jit=0.12)
    for k in range(4):                                             # roots
        a = math.radians(90 * k + 30 + seed)
        lathe(p, x + 0.9 * math.cos(a), z + 0.9 * math.sin(a), [(0.8, 0), (0, 2.0)], OBS, verts=4, jit=0.1,
              shear=(0.45 * math.cos(a), 0.45 * math.sin(a)))
    for sgn, hy in ((1, 0.8), (-1, 0.85), (1, 0.55)):                # three bent branches
        y0 = h * hy
        b = [(x, y0, z), (x + sgn * 1.6, y0 + 1.0, z + 0.4), (x + sgn * 3.4, y0 + 1.8, z - 0.2), (x + sgn * 4.4, y0 + 3.0, z)]
        tube(p, b, [0.38, 0.3, 0.22, 0.12], OBS, sides=5, jit=0.1, tip=True)
    cols = [VIOLET, PURPLE, MAGENTA]
    for k, (dx, dy, dz, r) in enumerate(((0, h + 1.6, 0, 3.0), (-1.7, h + 0.5, 1.1, 2.0), (1.9, h + 0.8, -0.9, 2.2))):
        ball(p, (x + dx, dy, z + dz), r, cols[k % 3], scale=(1.1, 0.75, 1.1), subdiv=1, jit=0.12)
    for k in range(3):                                             # glowing fruits under the leaves
        a = math.radians(120 * k + 60 + seed)
        orb(p, (x + 1.8 * math.cos(a), h - 0.1 + 0.3 * k, z + 1.8 * math.sin(a)), 0.4, CYAN, subdiv=0)


def build_VoidTrees(p):
    dead_tree(p, -26, 44, 11, 1)
    dead_tree(p, -37, 52, 9, 2)
    dead_tree(p, -19, 57, 8, 3)


# ---- 11. Altar --------------------------------------------------------------------------------------------------------------
def build_Altar(p):
    x, z = 86, -28
    frustum(p, x, 0, 1.4, z, 13, 13, 12, 12, STONE, jit=0.1)
    frustum(p, x, 1.4, 2.8, z, 9, 9, 8.2, 8.2, DSTONE, jit=0.1)
    for sx in (-1, 1):                                             # cyan runes along the lower step
        for sz in (-1, 1):
            B(p, x + sx * 5.8, 1.5, z + sz * 5.8, 0.9, 0.2, 0.9, CYAN, rot=(0, 45, 0), jit=0.0)
    frustum(p, x, 2.8, 6.2, z, 5.6, 5.0, 4.6, 4.2, OBS, jit=0.08)
    B(p, x, 4.1, z, 5.8, 0.4, 5.2, VIOLET)
    rune(p, x, 4.6, z + 2.45, 2.0, CYAN, seed=11)
    B(p, x, 6.5, z, 6.4, 0.8, 6.4, VIOLET)
    lathe(p, x, z, [(2.4, 6.9), (1.6, 7.3), (0.6, 7.6)], DSTONE, verts=8, jit=0.05)
    for (px, pz) in ((81, -28), (91, -28)):                        # cyan crystal pillars
        crystal(p, px, 0, pz, 0.85, 3.6, CYAN, sides=6, jit=0.08)
    for k in range(4):                                             # corner shards
        a = math.radians(90 * k + 45)
        crystal(p, x + 3.9 * math.cos(a), 1.4, z + 3.9 * math.sin(a), 0.5, 2.4, PURPLE, sides=4, lean=(0.3 * math.cos(a), 0.3 * math.sin(a)))
    orb(p, (x, 11, z), 2.2, PURPLE, subdiv=2)
    orb(p, (x, 11, z), 1.2, LPURPLE, subdiv=1)
    torus(p, (x, 11, z), 2.9, 0.15, CYAN, segs=18, sides=4, rot=(70, 0, 20))
    torus(p, (x, 11, z), 2.9, 0.15, MAGENTA, segs=18, sides=4, rot=(-40, 0, -60))
    for k in range(4):
        a = math.radians(90 * k + 10)
        shard(p, (x + 4.0 * math.cos(a), 9.5 + 1.5 * (k % 2), z + 4.0 * math.sin(a)), 0.6, 1.4, 0.6, LCYAN, rot=(10, 20 * k, 15), sides=4)


# ---- 12. Shrooms ------------------------------------------------------------------------------------------------------------
def shroom(p, x, z, h, diam, capcol, seed):
    R = diam / 2
    cy = h + 0.5
    lathe(p, x, z, [(1.25, 0), (0.95, 0.25 * h), (0.85, 0.6 * h), (1.15, h)], PALE, verts=8, jit=0.06)
    lathe(p, x, z, [(R * 0.35, cy - 0.5 * R), (R * 0.9, cy - 0.45 * R), (R, cy - 0.25 * R), (R * 0.88, cy + 0.12 * R), (R * 0.55, cy + 0.42 * R),
                    (0, cy + 0.55 * R)], capcol, verts=9, jit=0.1)
    lathe(p, x, z, [(0, cy - 0.5 * R), (R * 0.9, cy - 0.45 * R)], DVIOLET, verts=9, jit=0.0, caps=False)
    for k in range(4):
        a = math.radians(72 * k + seed * 20)
        rr = R * (0.45 + 0.1 * (k % 2))
        yy = cy + 0.55 * R * math.sqrt(max(0.05, 1 - (rr / R) ** 2)) * 0.92
        orb(p, (x + rr * math.cos(a), yy, z + rr * math.sin(a)), R * 0.1 + 0.15, PALE if k % 2 == 0 else CYAN, subdiv=0)


def build_Shrooms(p):
    shroom(p, -44, 72, 9, 12, PURPLE, 1)
    shroom(p, -35, 68, 6, 8, MAGENTA, 2)
    shroom(p, -37, 78, 7.5, 9, VIOLET, 3)
    for (x, z, h, d, col) in ((-48.5, 69, 2.4, 3.0, CYAN), (-40, 74.5, 2.0, 2.6, PURPLE)):
        shroom(p, x, z, h, d, col, 5)


# ---- 13. Statues ------------------------------------------------------------------------------------------------------------
def knight(p, x, z, yaw):
    i0 = len(p.objs)
    frustum(p, x, 0, 2.0, z, 5.0, 5.0, 4.2, 4.2, STONE, jit=0.1)
    B(p, x, 0.25, z, 5.0, 0.5, 5.0, DSTONE)
    lathe(p, x, z, [(1.9, 2.0), (1.7, 4.0), (1.35, 7.0), (1.55, 9.0)], OBS, verts=8, sx=0.95, sz=0.72, jit=0.1)
    B(p, x, 9.1, z, 3.6, 1.0, 2.0, DSTONE, jit=0.05)                # shoulders
    lathe(p, x, z - 0.15, [(1.3, 9.4), (1.55, 10.4), (1.3, 11.7), (0.5, 12.5), (0, 12.7)], OBS, verts=8, sx=0.95, sz=1.0, jit=0.1, shear=(0, -0.22))
    B(p, x, 10.7, z + 0.9, 1.5, 1.7, 0.5, BLACK, jit=0.0)           # shadowed face
    B(p, x - 0.4, 10.9, z + 1.2, 0.4, 0.22, 0.2, CYAN, jit=0.0)
    B(p, x + 0.4, 10.9, z + 1.2, 0.4, 0.22, 0.2, CYAN, jit=0.0)
    B(p, x, 5.6, z - 1.35, 3.0, 6.2, 0.4, DVIOLET, jit=0.08)         # cape
    B(p, x - 1.9, 6.6, z + 0.5, 1.0, 3.4, 1.3, OBS, jit=0.05)        # left arm
    B(p, x + 1.9, 6.6, z + 0.7, 1.1, 3.0, 1.3, OBS, jit=0.05)        # right arm holding the sword upright beside the body
    B(p, x + 2.1, 5.2, z + 1.3, 1.0, 0.9, 1.0, DSTONE, jit=0.05)     # fist
    B(p, x + 2.1, 8.6, z + 1.3, 0.55, 6.0, 0.16, CYAN, jit=0.0)      # blade
    B(p, x + 2.1, 8.6, z + 1.3, 0.18, 5.6, 0.22, LCYAN, jit=0.0)
    spiky(p, x + 2.1, 11.55, z + 1.3, 0.3, 0.9, CYAN, sides=4, jit=0.0)
    B(p, x + 2.1, 5.9, z + 1.3, 1.9, 0.35, 0.45, PURPLE, jit=0.0)    # crossguard
    orb(p, (x + 2.1, 4.6, z + 1.3), 0.3, PALE, subdiv=0)
    xf(p, i0, pivot=(x, 0, z), rot=(0, yaw, 0))


def build_Statues(p):
    knight(p, -52, -86, -12)
    knight(p, -44, -90, 0)
    knight(p, -36, -86, 12)


# ---- 14. Pool ---------------------------------------------------------------------------------------------------------------
def build_Pool(p):
    x, z = 84, 40
    B(p, x, 0.3, z, 20, 0.6, 20, STONE, jit=0.12)
    B(p, x, 0.55, z, 17, 0.2, 17, VIOLET, jit=0.0)
    star_poly(p, (x, 0.68, z), "xz", 6.4, 3.0, 0.1, LPURPLE, n=6, rot0=30)
    for R, col in ((3.0, LPURPLE), (5.2, PURPLE), (7.4, MAGENTA)):    # ripples
        torus(p, (x, 0.7, z), R, 0.18, col, segs=18, sides=4, scale_y=0.8)
    for (cx, cz, sx, sz) in ((84, 30, 22, 2.4), (84, 50, 22, 2.4), (74, 40, 2.4, 18), (92, 40, 2.4, 18)):   # rim blocks
        n = 5
        for i in range(n):
            if sx > sz:
                bxx, bzz, bw, bd = cx - sx / 2 + sx * (i + 0.5) / n, cz, sx / n * 0.93, sz
            else:
                bxx, bzz, bw, bd = cx, cz - sz / 2 + sz * (i + 0.5) / n, sx, sz / n * 0.93
            hh = 1.0 + 0.6 * ((i * 7 + int(cx)) % 3) / 2
            B(p, bxx, 0.3 + hh / 2, bzz, bw, hh, bd, LSTONE if i % 2 == 0 else STONE, jit=0.15)
            B(p, bxx, 0.3 + hh + 0.05, bzz, 0.5, 0.12, 0.5, CYAN, jit=0.0)
    for (lx, lz, r) in ((80, 38, 2.0), (88, 43, 1.6), (84, 46, 1.2)):  # cyan lilies
        lathe(p, lx, lz, [(r, 0.62), (r * 0.9, 0.82), (0, 0.9)], CYAN, verts=7, jit=0.05)
        lathe(p, lx, lz, [(r * 0.3, 0.85), (0, 1.1)], PALE, verts=5, jit=0.0)
    for (bx_, bz_, by_) in ((81, 41, 1.2), (87, 37, 1.5), (85, 44, 1.0), (79, 44, 1.4)):
        orb(p, (bx_, by_, bz_), 0.22, LPURPLE, subdiv=0)


# ---- 15. Ruins --------------------------------------------------------------------------------------------------------------
def build_Ruins(p):
    for (x, z, h, seed) in ((-60, -12, 12, 1), (-52, -4, 9, 2), (-44, -12, 14, 3), (-37, -5, 6, 4)):
        rr = random.Random(seed)
        frustum(p, x, 0, 1.2, z, 4.4, 4.4, 3.8, 3.8, STONE, jit=0.1)
        top = h + 1.0
        lathe(p, x, z, [(1.55, 1.2), (1.45, 2.0), (1.45, top - 2.6)], STONE, verts=8, jit=0.12, caps=False)
        for k in range(8):                                         # jagged broken top: separate stumps of different height
            a = math.radians(45 * k + 22)
            hh = top - 2.6 + rr.uniform(0.6, 2.4)
            lathe(p, x + 0.75 * math.cos(a), z + 0.75 * math.sin(a), [(0.65, top - 2.7), (0.5, hh)], STONE, verts=4, jit=0.15)
        bx(p, (x - 0.15, x + 0.15), (1.2, top - 2.5), (z + 1.4, z + 1.7), PURPLE, 0.0)    # a crack of violet light
        for k in range(3):                                         # fallen chunks
            a = math.radians(120 * k + seed * 40)
            B(p, x + 3.0 * math.cos(a), 0.5, z + 3.0 * math.sin(a), rr.uniform(0.9, 1.5), 0.8, rr.uniform(0.9, 1.4), DSTONE, rot=(0, 30 * k, 0), jit=0.2)
        cy = h + 5
        i0 = len(p.objs)
        B(p, x, cy, z, 4.6, 1.4, 4.6, LSTONE, jit=0.1)
        B(p, x, cy - 0.9, z, 3.4, 0.6, 3.4, STONE, jit=0.1)
        B(p, x, cy + 0.85, z, 3.8, 0.4, 3.8, DSTONE, jit=0.1)
        for k in range(4):
            a = math.radians(90 * k)
            B(p, x + 2.35 * math.cos(a), cy, z + 2.35 * math.sin(a), 0.4, 0.5, 0.4, CYAN, jit=0.0)
        xf(p, i0, pivot=(x, cy, z), rot=(rr.uniform(-10, 10), rr.uniform(0, 90), rr.uniform(-10, 10)))
        for k in range(3):                                         # pebbles drifting between shaft and capital
            orb(p, (x + rr.uniform(-1.5, 1.5), top + 1.2 + k * 0.9, z + rr.uniform(-1.5, 1.5)), 0.3, PURPLE if k % 2 == 0 else CYAN, subdiv=0)


# ---- 16. Tentacles ----------------------------------------------------------------------------------------------------------
def tentacle(p, x, z, s, h, reach, seed):
    n = 8
    pts, rad = [], []
    for i in range(n + 1):
        t = i / n
        pts.append((x + s * reach * t ** 2 + 0.6 * math.sin(t * 5 + seed), h * t * 0.97, z + 0.8 * math.sin(t * 4 + seed * 2)))
        rad.append(2.4 * (1 - t) ** 0.8 + 0.4)
    tube(p, pts, rad, DSTONE, sides=6, jit=0.12, tip=True)
    for i in (2, 4, 6):                                            # glowing bands
        c = pts[i]
        lathe(p, c[0], c[2], [(rad[i] * 1.06, c[1] - 0.25), (rad[i] * 1.06, c[1] + 0.25)], VIOLET, verts=6, jit=0.0, caps=False)
    for i in range(1, n - 1):                                      # suckers along the inner side
        c = pts[i]
        orb(p, (c[0] - s * rad[i] * 0.85, c[1], c[2] + rad[i] * 0.7), 0.4 * (1 - i / n) + 0.25, PURPLE, subdiv=0)
    c = pts[-1]
    orb(p, (c[0], c[1] - 0.2, c[2]), 0.8, MAGENTA, subdiv=1)


def build_Tentacles(p):
    tentacle(p, 24, -50, 1, 19, 6.0, 1)
    tentacle(p, 36, -56, -1, 17, 6.0, 2)
    tentacle(p, 30, -46, 1, 14, 5.0, 3)
    for (x, z, r) in ((28, -52, 1.2), (33, -50, 1.0), (27, -45, 0.9)):    # blobs of shadow at the foot
        ball(p, (x, 0.5, z), r, OBS, scale=(1.4, 0.5, 1.0), subdiv=1, jit=0.15)


# ---- 17. Obelisks -----------------------------------------------------------------------------------------------------------
def build_Obelisks(p):
    for k, (x, z, h) in enumerate(((88, 22, 20), (88, 10, 15), (76, 15, 24))):
        frustum(p, x, 0, 0.6, z, 5.6, 5.6, 5.0, 5.0, STONE)
        frustum(p, x, 0.6, 1.2, z, 4.6, 4.6, 4.0, 4.0, DSTONE)
        top = h + 1.0
        frustum(p, x, 1.0, top, z, 3.2, 3.2, 2.1, 2.1, MSTONE, jit=0.1)
        for f in (0.28, 0.6):                                      # carved bands
            y = 1.0 + (top - 1.0) * f
            w = 3.2 - 1.1 * f + 0.35
            B(p, x, y, z, w, 0.5, w, DSTONE)
        for f, s in ((0.42, 1), (0.78, 2)):                        # glowing runes on the road side
            y = 1.0 + (top - 1.0) * f
            rune(p, x, y, z + (3.2 - 1.1 * f) / 2 - 0.02, 1.6, CYAN, seed=k * 5 + s)
        lathe(p, x, z, [(1.5, top), (1.5, top + 0.6), (0, top + 3.4)], CYAN, verts=4, jit=0.06, rot0=math.pi / 4)
        lathe(p, x, z, [(0.7, top + 0.7), (0, top + 2.4)], LCYAN, verts=4, jit=0.0, rot0=math.pi / 4)
        ry_ = 0.62 * h + 2
        torus(p, (x, ry_, z), 3.1, 0.22, PURPLE, segs=16, sides=4, rot=(8, 0, 6))
        for j in range(3):
            a = math.radians(120 * j + 30 * k)
            orb(p, (x + 3.1 * math.cos(a), ry_ + 0.3 * math.sin(a + 1), z + 3.1 * math.sin(a)), 0.38, CYAN if j else LPURPLE, subdiv=0)


# ---- 18. Throne -------------------------------------------------------------------------------------------------------------
def build_Throne(p):
    x, z = 34, -26
    frustum(p, x, 0, 1.6, z, 16, 14, 15, 13, STONE, jit=0.1)
    frustum(p, x, 1.6, 2.8, z, 12, 10, 11, 9, DSTONE, jit=0.1)
    B(p, x, 2.2, z + 6.6, 7, 1.0, 1.2, MSTONE)                         # steps in front
    B(p, x, 1.8, z + 7.6, 9, 0.4, 1.2, DSTONE)
    frustum(p, x, 2.8, 4.6, z, 5.6, 5.0, 5.4, 4.8, MSTONE)
    B(p, x, 4.9, z + 0.1, 5.2, 0.6, 4.6, VIOLET)                       # cushion
    for sx in (-1, 1):
        B(p, x + sx * 3.1, 4.6, z, 1.2, 3.6, 5.0, OBS, jit=0.08)         # armrests y 2.8..6.4
        orb(p, (x + sx * 3.1, 6.7, z + 2.3), 0.55, CYAN, subdiv=0)
        B(p, x + sx * 3.1, 3.2, z + 2.55, 0.8, 0.8, 0.3, PURPLE)
    B(p, x, 9.0, z - 2.4, 6.4, 12.0, 1.6, MSTONE, jit=0.08)              # backrest y 3..15
    B(p, x, 9.0, z - 1.55, 4.6, 9.4, 0.25, OBS, jit=0.0)
    rune(p, x, 9.2, z - 1.4, 3.0, CYAN, seed=18)
    rune(p, x, 5.5, z - 1.4, 1.2, PURPLE, seed=19)
    for sx in (-1, 1):                                                 # frame ribs
        B(p, x + sx * 3.0, 9.0, z - 2.4, 0.4, 12.0, 1.8, DSTONE)
    crystal(p, x, 14.6, z - 2.4, 0.9, 6.4, VIOLET, sides=4)
    for sx, hh in ((-1, 4.0), (1, 4.0)):
        crystal(p, x + sx * 3.0, 14.4, z - 2.4, 0.75, hh, PURPLE, sides=4, lean=(sx * 0.5, 0))
    for sx in (-1, 1):
        crystal(p, x + sx * 1.6, 14.9, z - 2.4, 0.6, 2.6, MAGENTA, sides=4)
    torus(p, (x, 21, z), 3.2, 0.35, CYAN, segs=18, sides=4, scale_y=1.0)
    for k in range(5):
        a = math.radians(72 * k + 20)
        orb(p, (x + 3.2 * math.cos(a), 21.0, z + 3.2 * math.sin(a)), 0.5, LCYAN, subdiv=0)


# ---- 19. Watchtower ---------------------------------------------------------------------------------------------------------
def build_Watchtower(p):
    x, z = -86, -46
    frustum(p, x, 0, 1.0, z, 14, 14, 13, 13, STONE)
    frustum(p, x, 1.0, 2.0, z, 12, 12, 11, 11, DSTONE)
    frustum(p, x, 2.0, 22.0, z, 9, 9, 7.6, 7.6, MSTONE, jit=0.1)
    for y, w in ((7.0, 9.0), (13.0, 8.4), (19.0, 7.9)):
        B(p, x, y, z, w, 0.6, w, DSTONE)
    for k in range(4):                                                 # windows on all four faces
        i0 = len(p.objs)
        hw = 4.08
        B(p, x, 14.0, z + hw, 2.4, 3.8, 0.3, CYAN, jit=0.0)
        B(p, x, 14.0, z + hw + 0.05, 1.0, 3.2, 0.3, LCYAN, jit=0.0)
        lathe(p, x, z + hw, [(1.5, 15.9), (0, 17.0)], CYAN, verts=4, jit=0.0, sx=0.9, sz=0.25, rot0=math.pi / 4)
        B(p, x, 6.0, z + hw + 0.4, 1.2, 2.0, 0.3, PURPLE, jit=0.0)
        xf(p, i0, pivot=(x, 0, z), rot=(0, 90 * k, 0))
    frustum(p, x, 22.0, 25.0, z, 8.2, 8.2, 12.0, 12.0, DSTONE, jit=0.1)      # corbelled platform
    for k in range(8):
        a = math.radians(45 * k + 22)
        B(p, x + 5.3 * math.cos(a), 25.6, z + 5.3 * math.sin(a), 1.4, 1.2, 1.4, STONE, rot=(0, -45 * k, 0), jit=0.1)
    frustum(p, x, 25.0, 32.0, z, 8, 8, 7.2, 7.2, MSTONE, jit=0.1)
    for k in range(4):
        i0 = len(p.objs)
        B(p, x, 28.5, z + 3.75, 3.4, 3.4, 0.3, CYAN, jit=0.0)
        B(p, x, 28.5, z + 3.8, 0.4, 3.4, 0.3, DSTONE, jit=0.0)
        B(p, x, 28.5, z + 3.8, 3.4, 0.4, 0.3, DSTONE, jit=0.0)
        xf(p, i0, pivot=(x, 0, z), rot=(0, 90 * k, 0))
    frustum(p, x, 32.0, 34.4, z, 10.4, 10.4, 8.4, 8.4, VIOLET)
    lathe(p, x, z, [(2.2, 34.4), (2.2, 35.0), (1.6, 35.0), (1.6, 34.6)], OBS, verts=8, jit=0.05, caps=False, loop=True)
    lathe(p, x, z, [(1.7, 34.4), (1.5, 35.8), (0.8, 37.6), (0, 39.0)], PURPLE, verts=8, jit=0.12)
    lathe(p, x, z, [(0.9, 34.6), (0.7, 35.8), (0, 37.2)], MAGENTA, verts=6, jit=0.1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            crystal(p, x + sx * 4.4, 34.4, z + sz * 4.4, 0.6, 2.4, CYAN, sides=4, lean=(sx * 0.4, sz * 0.4))


# ---- 20. Shards -------------------------------------------------------------------------------------------------------------
def build_Shards(p):
    cx, cz = 22, 30
    for k in range(9):
        a = k * 40
        r = 15 if k % 2 == 0 else 9
        y = 15 + ((k * 7) % 5) * 3.5
        s = 5 + (k % 3) * 1.6
        col = (PURPLE, VIOLET, CYAN)[k % 3]
        pos = (cx + r * math.cos(math.radians(a)), y, cz + r * math.sin(math.radians(a)))
        shard(p, pos, 3.4, s + 4, 3.0, col, rot=(0, a, (k % 3 - 1) * 14), sides=6, jit=0.12)
        shard(p, (pos[0], pos[1] + 0.2, pos[2]), 1.5, (s + 4) * 0.65, 1.3, (LPURPLE, LPURPLE, LCYAN)[k % 3],
              rot=(0, a, (k % 3 - 1) * 14), sides=4, jit=0.0)
    shard(p, (cx, 22, cz), 2.4, 7, 2.4, LCYAN, rot=(0, 20, 0), sides=4, jit=0.05)
    for k in range(14):                                                # chips drifting between the shards
        a = math.radians(26 * k + 7)
        rr = 11.5 + 2.5 * math.sin(k * 2.1)
        shard(p, (cx + rr * math.cos(a), 12 + (k * 5 % 9) * 1.6, cz + rr * math.sin(a)), 0.6, 1.5, 0.6, (LPURPLE, CYAN, MAGENTA)[k % 3],
              rot=(20, 30 * k, 15), sides=4, jit=0.05)


# ---- 21. Orrery -------------------------------------------------------------------------------------------------------------
def build_Orrery(p):
    x, z = -32, 18
    frustum(p, x, 0, 1.4, z, 12, 12, 10.5, 10.5, STONE, jit=0.1)
    lathe(p, x, z, [(2.6, 1.4), (1.5, 2.2), (1.2, 4.6), (1.7, 5.4)], MSTONE, verts=8, jit=0.1)
    B(p, x, 0.7, z + 4.5, 1.2, 0.18, 1.2, CYAN, jit=0.0)
    for k in range(3):                                                 # arms up to the rings
        a = math.radians(120 * k + 20)
        tube(p, [(x + 1.2 * math.cos(a), 5.2, z + 1.2 * math.sin(a)), (x + 3.0 * math.cos(a), 7.4, z + 3.0 * math.sin(a)),
                 (x + 4.8 * math.cos(a), 10.0, z + 4.8 * math.sin(a))], [0.3, 0.25, 0.2], DSTONE, sides=4, jit=0.05)
    orb(p, (x, 11, z), 2.5, PURPLE, subdiv=2)
    orb(p, (x, 11, z), 1.4, LPURPLE, subdiv=1)
    torus(p, (x, 11, z), 8.2, 0.3, VIOLET, segs=24, sides=4, rot=(6, 0, 4))
    torus(p, (x, 11, z), 5.8, 0.26, CYAN, segs=20, sides=4, rot=(-12, 40, -8))
    orb(p, (x + 8.2, 11, z), 1.1, CYAN, subdiv=1)
    orb(p, (x - 3.0, 11, z + 6.4), 0.9, MAGENTA, subdiv=1)
    orb(p, (x - 6.6, 11, z - 5.0), 0.8, PALE, subdiv=1)
    for k in range(6):
        a = math.radians(60 * k + 15)
        B(p, x + 8.2 * math.cos(a), 11, z + 8.2 * math.sin(a), 0.5, 0.4, 0.5, LPURPLE, rot=(0, -60 * k, 0), jit=0.0)


# ---- 22. Sentinel -----------------------------------------------------------------------------------------------------------
def build_Sentinel(p):
    x, z = 80, 66
    frustum(p, x, 0, 2.4, z, 20, 20, 18.6, 18.6, STONE, jit=0.1)
    B(p, x, 2.45, z + 8.5, 14, 0.2, 2, DSTONE, jit=0.0)
    for sx in (-1, 1):
        lx = x + sx * 4.0
        B(p, lx, 3.2, z + 0.8, 6.0, 1.6, 7.6, DSTONE, jit=0.08)                       # boot
        frustum(p, lx, 4.0, 15.0, z, 5.8, 6.0, 4.8, 5.2, LSTONE, jit=0.08)             # greave
        B(p, lx, 9.0, z + 3.05, 3.4, 0.5, 0.3, CYAN, jit=0.0)
        ball(p, (lx, 15.6, z), 2.7, DSTONE, scale=(1, 0.8, 1), subdiv=1, jit=0.1)
        spiky(p, lx, 15.4, z + 2.2, 0.9, 2.2, PURPLE, sides=4, lean=(0, 1.0))
    frustum(p, x, 16.0, 24.0, z, 15.6, 9.6, 14.0, 8.6, DSTONE, jit=0.08)               # tassets
    for k in range(5):
        px = x - 5.6 + 2.8 * k
        B(p, px, 17.4, z + 4.5, 2.5, 3.2, 0.5, LSTONE if k % 2 == 0 else OBS, jit=0.08)
    B(p, x, 23.6, z, 14.0, 1.4, 9.0, VIOLET)                                          # belt
    B(p, x, 23.6, z + 4.55, 2.6, 2.0, 0.5, CYAN)
    frustum(p, x, 24.0, 34.0, z, 12.6, 8.0, 15.6, 9.0, LSTONE, jit=0.08)               # chest
    B(p, x, 30.0, z + 4.4, 3.2, 3.2, 0.9, PURPLE, rot=(0, 0, 45), jit=0.0)
    halo(p, (x, 30.0, z + 4.5), 2.5, 0.22, CYAN, segs=14, sides=4)
    for sx in (-1, 1):
        px = x + sx * 8.5
        ball(p, (px, 33.2, z), 3.5, LSTONE, scale=(1.15, 0.75, 1.1), subdiv=1, jit=0.1)       # pauldron
        for j in range(3):
            spiky(p, px + sx * (-0.8 + 0.9 * j), 34.5, z, 0.6, 2.4 + 0.3 * j, PURPLE, sides=4, lean=(sx * 0.4 * j, 0))
        frustum(p, px, 27.6, 32.0, z, 4.6, 5.0, 4.2, 4.6, DSTONE, jit=0.08)             # upper arm
        ball(p, (px, 27.2, z), 2.0, LSTONE, subdiv=1, jit=0.1)
        frustum(p, px, 19.0, 26.8, z, 4.0, 4.4, 4.8, 5.0, LSTONE, jit=0.08)             # forearm
        B(p, px, 19.2, z, 4.2, 1.6, 4.6, DSTONE, jit=0.08)                              # fist
        B(p, px, 23.0, z + 2.4, 2.4, 0.4, 0.3, CYAN, jit=0.0)
    lathe(p, x, z, [(1.5, 32.0), (2.2, 33.2), (3.6, 35.0), (4.0, 37.6), (3.2, 40.0), (0, 41.6)], LSTONE, verts=10, jit=0.1)     # helmet
    B(p, x, 37.8, z + 3.65, 6.2, 1.1, 0.6, BLACK, jit=0.0)
    for sx in (-1, 1):
        B(p, x + sx * 1.9, 37.9, z + 4.0, 1.8, 0.5, 0.3, CYAN, jit=0.0)
        tube(p, [(x + sx * 3.4, 38.6, z), (x + sx * 5.2, 40.4, z), (x + sx * 5.6, 43.0, z), (x + sx * 4.4, 45.2, z)],
             [0.7, 0.6, 0.45, 0.3], OBS, sides=5, jit=0.1, tip=True)
    B(p, x, 40.4, z + 3.0, 0.8, 2.4, 0.6, VIOLET, rot=(-20, 0, 0), jit=0.0)            # crest
    orb(p, (x, 48, z), 3.5, VIOLET, subdiv=2)
    orb(p, (x, 48, z), 2.0, PURPLE, subdiv=1)
    torus(p, (x, 48, z), 4.6, 0.2, CYAN, segs=16, sides=4, rot=(60, 0, 20))
    for k in range(3):
        a = math.radians(120 * k)
        orb(p, (x + 5.0 * math.cos(a), 48.0, z + 5.0 * math.sin(a)), 0.45, LCYAN, subdiv=0)
    # the floating sword beside the right fist
    sx_ = 91.5
    B(p, sx_, 16.2, z, 0.9, 0.8, 0.9, OBS, jit=0.0)
    B(p, sx_, 17.0, z, 4.0, 1.2, 2.2, PURPLE, jit=0.0)
    B(p, sx_, 28.0, z, 1.2, 20.0, 2.2, CYAN, jit=0.0)
    B(p, sx_, 28.0, z + 1.1, 0.4, 19.0, 0.2, LCYAN, jit=0.0)
    orb(p, (sx_, 15.8, z), 0.5, LPURPLE, subdiv=0)


# ---- 23. PortalFrame --------------------------------------------------------------------------------------------------------
def build_PortalFrame(p):
    cx, cy, cz = 66, 24, -4
    halo(p, (cx, cy, cz), 17.0, 2.4, LSTONE, segs=16, sides=4, jit=0.15, sq=1.35)
    halo(p, (cx, cy, cz + 0.3), 15.2, 0.3, CYAN, segs=32, sides=4, sq=3.0)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        B(p, cx + 17.0 * math.cos(a), cy + 17.0 * math.sin(a), cz, 3.2, 4.2, 5.2, OBS if k % 2 else MSTONE,
          rot=(0, 0, 45 * k + 22.5 + 90), jit=0.1)
    for k in (0, 2, 4, 6):                                             # runes between the joints
        a = math.radians(45 * k)
        rune(p, cx + 17.0 * math.cos(a), cy + 17.0 * math.sin(a), cz + 2.3, 2.0, CYAN if k % 4 == 0 else LPURPLE, seed=k + 40)
    crystal(p, cx, 38.8, cz, 2.2, 4.0, PURPLE, sides=4, jit=0.06)
    crystal(p, cx, 36.0, cz + 1.2, 0.9, 2.6, CYAN, sides=4)
    frustum(p, cx, 0, 3.0, cz, 14, 6, 13, 5.6, STONE, jit=0.1)
    frustum(p, cx, 3.0, 7.0, cz, 12, 5.4, 10, 5.0, DSTONE, jit=0.1)
    B(p, cx, 7.4, cz, 9, 0.8, 5, VIOLET)
    for sx in (-1, 1):
        crystal(p, cx + sx * 5.4, 0, cz + 0.8, 1.0, 4.4, CYAN, sides=5, lean=(sx * 0.4, 0))
    B(p, cx, 0.5, cz + 2.3, 11, 0.3, 0.9, MSTONE)


# ---- 24. PortalSwirl --------------------------------------------------------------------------------------------------------
def build_PortalSwirl(p):
    cx, cy = 66, 24
    zcyl(p, cx, cy, -4.5, -4.1, 15.0, DVIOLET, verts=26, jit=0.05)
    zcyl(p, cx, cy, -4.5, -3.8, 2.8, PALE, verts=10, jit=0.0)
    arms = 5
    for a in range(arms):
        th0 = a * 2 * math.pi / arms
        n = 13
        pts = []
        for i in range(n + 1):
            t = i / n
            r = 2.4 + 12.0 * t
            th = th0 + 3.6 * t ** 0.85
            pts.append((cx + r * math.cos(th), cy + r * math.sin(th), -4.0 + 2.8 * (r / 15.0), t))
        for i in range(n):
            A, Bp = pts[i], pts[i + 1]
            dx, dy = Bp[0] - A[0], Bp[1] - A[1]
            ln = math.hypot(dx, dy)
            nx, ny = -dy / ln, dx / ln
            wa, wb = 2.6 * (1 - 0.45 * A[3]), 2.6 * (1 - 0.45 * Bp[3])
            ex, ey = dx / ln * 0.25, dy / ln * 0.25
            c = [(A[0] - ex + nx * wa / 2, A[1] - ey + ny * wa / 2, A[2]), (A[0] - ex - nx * wa / 2, A[1] - ey - ny * wa / 2, A[2]),
                 (Bp[0] + ex - nx * wb / 2, Bp[1] + ey - ny * wb / 2, Bp[2]), (Bp[0] + ex + nx * wb / 2, Bp[1] + ey + ny * wb / 2, Bp[2])]
            pts8 = [(q[0], q[1], q[2] - 0.2) for q in c] + [(q[0], q[1], q[2] + 0.25) for q in c]
            t = (A[3] + Bp[3]) / 2
            col = PALE if t < 0.12 else (CYAN if t < 0.32 else (MAGENTA if t < 0.55 else (PURPLE if t < 0.8 else VIOLET)))
            hexa(p, pts8, col, jit=0.06)
    for k in range(10):                                                # sparks on the rim
        a = math.radians(36 * k + 10)
        star_poly(p, (cx + 14.4 * math.cos(a), cy + 14.4 * math.sin(a), -1.7), 'xy', 0.7, 0.25, 0.15, LCYAN if k % 2 else LPURPLE, n=4)


# ---- 25. Citadel ------------------------------------------------------------------------------------------------------------
def citadel_tower(p, x, z):
    lathe(p, x, z, [(3.9, 2.4), (3.5, 4.0), (3.3, 20.5), (4.2, 21.3), (4.2, 23.2), (3.4, 23.4)], LSTONE, verts=8, jit=0.1)
    lathe(p, x, z, [(4.6, 23.2), (3.8, 24.6), (0, 28.7)], VIOLET, verts=8, jit=0.1)
    for y in (9.0, 15.0):
        B(p, x, y, z + 3.3, 0.7, 2.4, 0.3, CYAN, jit=0.0)
    for k in range(4):
        a = math.radians(90 * k + 45)
        B(p, x + 3.9 * math.cos(a), 22.4, z + 3.9 * math.sin(a), 0.9, 0.9, 0.9, DSTONE, jit=0.05)
    crystal(p, x, 28.0, z, 0.35, 0.9, CYAN, sides=4, jit=0.0)
    B(p, x + 0.9, 27.0, z, 1.8, 1.0, 0.1, MAGENTA, jit=0.0)
    B(p, x + 0.9, 26.0, z, 1.4, 0.8, 0.1, PURPLE, jit=0.0)


def build_Citadel(p):
    frustum(p, -62, 0, 2.4, 50, 42, 30, 40, 28.4, STONE, jit=0.1)
    towers = [(-80, 38), (-44, 38), (-80, 62), (-44, 62)]
    for (x, z) in towers:
        citadel_tower(p, x, z)

    def wall(x0, x1, z0, z1):
        n = max(2, int(max(abs(x1 - x0), abs(z1 - z0)) // 7))
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        sx, sz = max(abs(x1 - x0), 2.2), max(abs(z1 - z0), 2.2)
        B(p, cx, 6.9, cz, sx, 9.0, sz, MSTONE, jit=0.08)
        for i in range(n):
            f = (i + 0.5) / n
            mx, mz = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            B(p, mx, 12.1, mz, 2.0 if sx > sz else 2.4, 1.4, 2.4 if sx > sz else 2.0, MSTONE, jit=0.08)
    wall(-76.5, -47.5, 38, 38)
    wall(-80, -80, 41.5, 58.5)
    wall(-44, -44, 41.5, 58.5)
    wall(-76.5, -66, 62, 62)
    wall(-58, -47.5, 62, 62)
    for sx in (-66.5, -57.5):                                          # gatehouse pillars + glowing door in the wall gap
        B(p, sx, 7.4, 62, 1.8, 10, 2.6, MSTONE)
    B(p, -62, 12.6, 62, 10.4, 1.8, 2.6, VIOLET)
    B(p, -62, 6.6, 61.2, 6.4, 8.4, 0.4, CYAN, jit=0.0)
    B(p, -62, 6.6, 61.3, 0.4, 8.4, 0.3, DSTONE, jit=0.0)
    # great hall, cornice, keep, roof, spire
    B(p, -62, 11, 50, 22, 17, 16, MSTONE, jit=0.06)
    for sx in (-10.6, 10.6):
        B(p, -62 + sx, 10.5, 58.3, 1.6, 16, 1.2, MSTONE)
    B(p, -62, 7, 58.2, 8, 9, 0.6, CYAN, jit=0.0)
    B(p, -62, 7, 58.35, 0.5, 9, 0.5, DSTONE, jit=0.0)
    B(p, -62, 11.6, 58.35, 8, 0.5, 0.5, DSTONE, jit=0.0)
    lathe(p, -62, 58.3, [(4.0, 11.5), (0, 14.0)], VIOLET, verts=4, jit=0.0, sz=0.3, rot0=math.pi / 4)
    for k in range(3):
        B(p, -67 + 5 * k, 15, 58.3, 1.4, 2.6, 0.4, CYAN, jit=0.0)
    B(p, -62, 21, 50, 24, 3, 18, DSTONE, jit=0.08)
    B(p, -62, 29, 50, 12, 13, 10, MSTONE, jit=0.08)
    for dx in (-3.2, 0, 3.2):
        B(p, -62 + dx, 28, 55.1, 1.6, 4.2, 0.3, CYAN, jit=0.0)
    B(p, -62, 37, 50, 14, 3, 12, VIOLET, jit=0.06)
    lathe(p, -62, 50, [(2.5, 38.0), (2.2, 44.0), (0, 52.0)], PURPLE, verts=6, jit=0.1)
    lathe(p, -62, 50, [(1.2, 40.0), (0.9, 45.0), (0, 49.0)], LPURPLE, verts=4, jit=0.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            crystal(p, -62 + sx * 5.6, 38.5, 50 + sz * 4.4, 0.8, 4.0, CYAN, sides=4, lean=(sx * 0.3, sz * 0.3))
    B(p, -62, 3, 63.4, 10, 1, 2, DSTONE)


# ---- 26. Comets -------------------------------------------------------------------------------------------------------------
def comet(p, x, y, z, col, light):
    d = Vector((-0.907, 0.375, 0.193)).normalized()
    ball(p, (x, y, z), 2.5, col, subdiv=1, jit=0.1)
    ball(p, (x - 0.3, y + 0.3, z + 0.3), 1.5, light, subdiv=0, jit=0.0)
    h = Vector((x, y, z))
    tube(p, [tuple(h + d * t) for t in (1.0, 4.0, 8.0, 11.5, 13.5)], [2.0, 1.55, 1.0, 0.55, 0.2], col, sides=5, jit=0.06, cap_start=False, tip=True)
    side = d.cross(Vector((0, 1, 0))).normalized()
    for sgn in (-1, 1):
        base = h + side * sgn * 1.6
        tube(p, [tuple(base + d * t) for t in (1.0, 5.0, 9.0, 12.0)], [0.7, 0.5, 0.3, 0.1], light, sides=4, jit=0.0, cap_start=False, tip=True)
    for t in (3.0, 6.5, 9.5):
        B(p, x + d.x * (t + 1.5) + 0.9, y + d.y * (t + 1.5) + 1.3, z + d.z * (t + 1.5), 0.45, 0.45, 0.45, light, rot=(20, 20, 20), jit=0.0)


def build_Comets(p):
    for (x, y, z, col, light) in ((-20, 40, 52, CYAN, LCYAN), (0, 30, 60, PURPLE, LPURPLE), (24, 44, 48, MAGENTA, PALE),
                                  (-40, 28, 40, VIOLET, LPURPLE), (8, 52, 70, CYAN, LCYAN)):
        comet(p, x, y, z, col, light)


# ---- 27. Island -------------------------------------------------------------------------------------------------------------
def dspike(p, cx, ytop, cz, r, h, col, sides=5, lean=(0, 0)):
    return lathe(p, cx, cz, [(0, ytop - h), (r, ytop)], col, verts=sides, jit=0.12, shear=(-lean[0] / h, -lean[1] / h))


def build_Island(p):
    cx, cz = -58, 6
    # underside: a ragged hanging rock
    lathe(p, cx, cz, [(0, 9.5), (3.0, 12.0), (7.0, 16.5), (13.0, 21.5), (19.0, 26.5), (24.0, 30.8)], STONE, verts=9, jit=0.18, caps=False)
    lathe(p, cx, cz, [(0, 9.5), (2.2, 13.0), (4.5, 18.0), (7.0, 23.0)], DSTONE, verts=7, jit=0.15, caps=False, rot0=0.3)
    for k in range(7):
        a = math.radians(360 / 7 * k + 20)
        rr = 17 + 4 * math.sin(k * 2.3)
        dspike(p, cx + rr * math.cos(a), 29.0 - (k % 3) * 2.0, cz + rr * math.sin(a), 1.6, 6.5 + (k % 3) * 2.2, VIOLET, lean=(0.4 * math.cos(a), 0.4 * math.sin(a)))
    # the top disc
    lathe(p, cx, cz, [(24.2, 30.6), (26.0, 31.6), (26.0, 33.6), (24.5, 34.2), (0, 34.2)], STONE, verts=16, jit=0.1)
    lathe(p, cx, cz, [(0, 34.1), (23.0, 34.1), (23.0, 34.9), (0, 34.9)], LSTONE, verts=16, jit=0.12, caps=False)
    lathe(p, cx, cz, [(23.0, 34.9), (24.4, 34.9), (24.4, 34.1)], PURPLE, verts=16, jit=0.05, caps=False)
    # ruined temple
    B(p, -58, 35.4, 6, 17, 1.0, 13, DSTONE, jit=0.08)
    B(p, -58, 41, 0.5, 16, 11, 1.4, LSTONE, jit=0.1)                    # back wall
    B(p, -58, 43.6, 0.5, 10, 4.2, 0.3, OBS, jit=0.0)
    for k, x in enumerate((-65, -61, -55, -51)):
        h = 10.6 if k != 2 else 6.5
        lathe(p, x, 11.4, [(1.2, 35.9), (1.05, 36.4), (1.05, 35.9 + h - 0.6), (1.2, 35.9 + h)], LSTONE, verts=6, jit=0.1)
    B(p, -61, 47.9, 11.4, 9.5, 1.5, 2.6, DSTONE, jit=0.08)                  # broken beam
    B(p, -52.5, 48.6, 10.6, 5, 1.6, 2.6, DSTONE, rot=(0, 0, -12), jit=0.08)
    for dx, dy in ((-6, 0), (6, 0)):
        B(p, -58 + dx, 48.0, 1.0, 5.6, 3.0, 1.6, DSTONE, jit=0.08)
    B(p, -58, 46.8, 0.5, 5, 0.6, 1.9, VIOLET)
    for (x, z, h) in ((-48, 14, 10), (-68, 14, 10), (-70, -6, 7), (-44, -6, 6)):
        lathe(p, x, z, [(1.5, 35.0), (1.3, 35.6), (1.3, 35.0 + h - 0.8), (1.5, 35.0 + h)], STONE, verts=6, jit=0.1)
        for j in range(3):
            B(p, x + RND.uniform(-2.2, 2.2), 35.4, z + RND.uniform(-2.2, 2.2), 1.0, 0.8, 1.0, DSTONE, rot=(0, 30 * j, 0), jit=0.2)
    crystal(p, -58, 36.9, -12, 2.4, 12.0, PURPLE, sides=6, lean=(0.6, 0.0))
    crystal(p, -61.5, 36.0, -10.5, 1.3, 6.5, VIOLET, sides=5, lean=(-0.5, 0.0))
    crystal(p, -54.8, 36.0, -10.0, 1.1, 5.5, CYAN, sides=5, lean=(0.4, 0.0))
    for k in range(16):                                                # purple grass tufts and cyan blooms on the top
        a = math.radians(360 / 16 * k + 7)
        rr = 17 + 4 * math.sin(k * 1.7)
        crystal(p, cx + rr * math.cos(a), 34.8, cz + rr * math.sin(a), 0.4, 1.6 + 0.6 * (k % 3), (PURPLE, CYAN, MAGENTA)[k % 3], sides=4, lean=(0.2, 0.1))
    B(p, -58, 38.8, 1.35, 4.4, 5.6, 0.3, CYAN, jit=0.0)
    B(p, -58, 38.8, 1.45, 0.4, 5.6, 0.3, LSTONE, jit=0.0)
    for k, x in enumerate((-65, -61, -55, -51)):
        B(p, x, 36.6, 11.4 + 1.25, 1.5, 0.35, 0.3, VIOLET, jit=0.0)
    B(p, -81.2, 17.0, 10, 2.6, 6.0, 5.6, LCYAN, jit=0.0)
    # waterfall off the west rim
    B(p, -82, 22.0, 10, 1.6, 22.0, 4.4, VIOLET, jit=0.04)
    B(p, -82.4, 22.5, 10, 0.8, 21.0, 3.0, PURPLE, jit=0.0)
    B(p, -82.1, 24.0, 10, 0.5, 18.0, 1.0, LCYAN, jit=0.0)
    for k in range(6):
        ball(p, (-82 + RND.uniform(-0.5, 0.5), 11.6 + k * 0.4, 10 + RND.uniform(-2, 2)), 0.9 + 0.3 * (k % 3), PALE if k % 2 else LPURPLE, subdiv=0, jit=0.1)
    orb(p, (-58, 53, 6), 2.4, VIOLET, subdiv=1)
    orb(p, (-58, 53, 6), 1.4, LPURPLE, subdiv=0)
    torus(p, (-58, 53, 6), 3.4, 0.18, CYAN, segs=14, sides=4, rot=(70, 0, 10))
    for k in range(4):                                                 # small rocks floating below the island
        a = math.radians(90 * k + 40)
        ball(p, (cx + 22 * math.cos(a), 20 - 2 * (k % 2), cz + 22 * math.sin(a)), 1.2 + 0.4 * (k % 2), DSTONE, subdiv=0, jit=0.2)


# ---- 28. Spire --------------------------------------------------------------------------------------------------------------
def build_Spire(p):
    x, z = -80, -78
    frustum(p, x, 0, 3, z, 22, 22, 19.4, 19.4, STONE, jit=0.1)
    frustum(p, x, 3, 7, z, 17.4, 17.4, 14.4, 14.4, DSTONE, jit=0.1, yaw=8)
    y = 7.0
    for k in range(7):
        w = 12 - 1.3 * k
        yaw = 14 * k
        frustum(p, x, y, y + 10, z, w, w, w - 1.0, w - 1.0, LSTONE if k % 2 == 0 else MSTONE, jit=0.1, yaw=yaw)
        frustum(p, x, y + 9.6, y + 10.4, z, w + 0.5, w + 0.5, w + 0.5, w + 0.5, VIOLET, jit=0.0, yaw=yaw)
        for sgn in (-1, 1):
            a = math.radians(-yaw) + (0 if k % 2 == 0 else math.pi / 2)
            cxk = x + sgn * (w / 2) * math.cos(a)
            czk = z + sgn * (w / 2) * math.sin(a)
            crystal(p, cxk, y + 1.5, czk, 0.55, 2.8, CYAN if k % 2 else PURPLE, sides=4, lean=(sgn * 0.3 * math.cos(a), sgn * 0.3 * math.sin(a)))
        y += 10
    crystal(p, x, y, z, 2.0, 6.0, VIOLET, sides=4)
    crystal(p, x, y + 5.0, z, 2.2, 8.0, PURPLE, sides=6)
    for k in range(4):
        a = math.radians(90 * k + 20)
        crystal(p, x + 2.4 * math.cos(a), y, z + 2.4 * math.sin(a), 0.6, 4.4, CYAN, sides=4, lean=(1.0 * math.cos(a), 1.0 * math.sin(a)))
    torus(p, (x, 52, z), 12.6, 0.4, CYAN, segs=26, sides=4)
    for k in range(8):
        a = math.radians(45 * k + 10)
        B(p, x + 12.6 * math.cos(a), 52, z + 12.6 * math.sin(a), 1.4, 0.9, 1.4, PURPLE, rot=(0, -45 * k, 0), jit=0.0)


# ---- 29. BlackHole ----------------------------------------------------------------------------------------------------------
def build_BlackHole(p):
    x, z = 66, -64
    frustum(p, x, 0, 0.5, z, 12, 12, 10, 10, DSTONE, jit=0.1)
    torus(p, (x, 0.5, z), 3.6, 0.28, CYAN, segs=16, sides=4, scale_y=0.8)
    lathe(p, x, z, [(0, 4.0), (0.9, 12.0), (1.5, 19.5)], CYAN, verts=6, jit=0.05, caps=False)          # lower jet
    lathe(p, x, z, [(1.5, 36.5), (0.9, 44.0), (0, 54.0)], CYAN, verts=6, jit=0.05, caps=False)         # upper jet
    lathe(p, x, z, [(0.7, 37.0), (0.45, 44.0), (0, 51.0)], LCYAN, verts=4, jit=0.0, caps=False)
    ball(p, (x, 28, z), 9.0, BLACK, subdiv=2, jit=0.05)
    halo(p, (x, 28, z), 12.5, 0.3, CYAN, segs=16, sides=4, rot=(0, 40, 0))
    halo(p, (x, 28, z), 14.5, 0.3, LPURPLE, segs=16, sides=4, rot=(0, -35, 0))
    torus(p, (x, 28.4, z), 9.8, 0.4, LCYAN, segs=20, sides=4, scale_y=0.8)
    for (r0, r1, y0, y1, col) in ((11.0, 15.0, 28.3, 29.5, PALE), (15.0, 20.0, 28.0, 29.0, MAGENTA), (20.0, 26.0, 27.4, 28.4, PURPLE)):
        lathe(p, x, z, [(r0, y0), (r1, y0), (r1, y1), (r0, y1)], col, verts=20, jit=0.06, caps=False, loop=True)
    for a in range(3):                                                 # bright spiral arms riding on the disc
        th0 = a * 2 * math.pi / 3
        pts = []
        for i in range(10):
            t = i / 9
            r = 11.5 + 13.5 * t
            th = th0 + 2.2 * t
            pts.append((x + r * math.cos(th), z + r * math.sin(th), t))
        for i in range(9):
            A, Bp = pts[i], pts[i + 1]
            dx, dz = Bp[0] - A[0], Bp[1] - A[1]
            ln = math.hypot(dx, dz)
            nx, nz = -dz / ln, dx / ln
            w = 1.4 * (1 - 0.5 * A[2])
            y_a = 29.0 - 0.9 * A[2]
            c = [(A[0] + nx * w / 2, A[1] + nz * w / 2), (A[0] - nx * w / 2, A[1] - nz * w / 2),
                 (Bp[0] - nx * w / 2, Bp[1] - nz * w / 2), (Bp[0] + nx * w / 2, Bp[1] + nz * w / 2)]
            pts8 = [(q[0], y_a - 0.15, q[1]) for q in c] + [(q[0], y_a + 0.45, q[1]) for q in c]
            hexa(p, pts8, LPURPLE if i % 2 == 0 else LCYAN, jit=0.04)
    for (dx, dy, dz, r, col) in ((-16, 36, 14, 1.5, DSTONE), (16, 20, -14, 1.7, DSTONE), (12, 38, 14, 1.2, PURPLE), (-12, 17, -12, 1.3, MAGENTA)):
        ball(p, (x + dx, dy, z + dz), r, col, subdiv=1, jit=0.15)


# ---- 30. VoidEye ------------------------------------------------------------------------------------------------------------
def build_VoidEye(p):
    x, z = 24, -86
    frustum(p, x, 0, 2.4, z, 14, 10, 12.4, 8.6, STONE, jit=0.1)
    frustum(p, x, 2.4, 26, z, 6, 5, 4.4, 4.0, MSTONE, jit=0.1)
    for y in (6, 12, 18, 23):
        B(p, x, y, z, 7.0 - 0.07 * y, 0.5, 6.0 - 0.06 * y, DSTONE)
    for y, col in ((9, CYAN), (15, PURPLE), (21, CYAN)):
        torus(p, (x, y, z), 5.0, 0.3, col, segs=16, sides=4, rot=(6, 0, 4))
    for sx in (-1, 1):
        rune(p, x + sx * 0.0, 15 + sx * 1.0, z + 2.0, 1.8, CYAN, seed=60 + sx) if sx == 1 else None
    frustum(p, x, 26, 34, z, 4.4, 4.0, 9.0, 7.0, DSTONE, jit=0.1)
    # lower eyelid: a crescent of blocks, upper lid: heavy arc with a crown of lashes
    for i in range(7):
        t = -1 + 2 * i / 6
        bx_ = x + 19.0 * t
        by_ = 33.2 + 1.8 * (1 - t * t) * 0.0 + 1.2 * t * t
        B(p, bx_, by_, z, 6.0, 2.4, 8.0, OBS, rot=(0, 0, -10 * t), jit=0.08)
    for i in range(7):
        t = -1 + 2 * i / 6
        bx_ = x + 21.0 * t
        by_ = 62.6 - 3.0 * t * t
        B(p, bx_, by_, z, 6.6, 3.0, 8.0, OBS, rot=(0, 0, 14 * t), jit=0.08)
        B(p, bx_, by_ - 1.45, z + 3.6, 6.0, 0.4, 0.5, VIOLET, rot=(0, 0, 14 * t), jit=0.0)
    for (px, py, hh, col, lean) in ((5, 55, 12, VIOLET, -3.6), (43, 55, 12, VIOLET, 3.6), (12, 62, 10, CYAN, -4.0), (36, 62, 10, CYAN, 4.0),
                                    (24, 64, 12, PURPLE, 0.0), (18, 63.5, 8, MAGENTA, -1.5), (30, 63.5, 8, MAGENTA, 1.5)):
        crystal(p, px, py - 5 if px in (5, 43) else py, z, 1.6, hh, col, sides=5, lean=(lean, 0))
    # the eyeball
    dk.ball(p, (x, 48, z), 1.0, PALE, scale=(23, 14, 6), subdiv=3, jitter=0.03)
    for k in range(10):                                                # veins on the white
        th = math.radians(36 * k + 12)
        pts = []
        for r in (11.0, 13.5, 16.0, 18.5, 20.5):
            dx, dy = r * math.cos(th), r * 0.6 * math.sin(th)
            q = 1 - (dx / 23) ** 2 - (dy / 14) ** 2
            if q <= 0.02:
                break
            pts.append((x + dx, 48 + dy, z + 6.0 * math.sqrt(q) * 1.02))
        if len(pts) >= 3:
            tube(p, pts, [0.28, 0.24, 0.2, 0.16, 0.12][:len(pts)], VIOLET, sides=3, jit=0.0, cap_start=False, tip=True)
    zcyl(p, x, 48, -81.5, -79.7, 9.5, DVIOLET, verts=20, jit=0.04)
    zcyl(p, x, 48, -81.5, -79.5, 7.6, PURPLE, verts=18, jit=0.06)
    for k in range(10):
        a = math.radians(360 / 10 * k)
        B(p, x + 5.6 * math.cos(a), 48 + 5.6 * math.sin(a), -79.45, 3.0, 0.5, 0.3, CYAN if k % 2 == 0 else LPURPLE, rot=(0, 0, math.degrees(a)), jit=0.0)
    zcyl(p, x, 48, -81.5, -79.3, 3.6, CYAN, verts=14, jit=0.0)
    ball(p, (x, 48, -78.8), 1.0, BLACK, scale=(1.5, 3.4, 0.6), subdiv=2, jit=0.0)
    orb(p, (x + 2.6, 51.0, -78.6), 0.7, PALE, subdiv=0)
    halo(p, (x, 48, -91.2), 21.0, 0.8, PURPLE, segs=20, sides=4)  # ring mount behind the eye
    for k in range(8):
        a = math.radians(45 * k)
        B(p, x + 21.0 * math.cos(a), 48 + 21.0 * math.sin(a), -91.2, 1.6, 1.6, 1.6, CYAN, rot=(0, 0, 45 * k), jit=0.0)


PART_IDS = ["Ground", "Gate", "Sign", "RuneStones", "Braziers", "Crystals", "Spikes", "Rift", "Lanterns", "VoidTrees",
            "Altar", "Shrooms", "Statues", "Pool", "Ruins", "Tentacles", "Obelisks", "Throne", "Watchtower", "Shards",
            "Orrery", "Sentinel", "PortalFrame", "PortalSwirl", "Citadel", "Comets", "Island", "Spire", "BlackHole", "VoidEye"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

AZ = {"Sign": 175, "Statues": 175, "Sentinel": 150, "VoidEye": 175, "PortalSwirl": 175, "PortalFrame": 175,
      "Ground": 160, "Citadel": 170, "Island": 170}
ELEV = {"Ground": 40, "Island": 20, "VoidEye": 18, "Comets": 14, "BlackHole": 22, "Spire": 14, "PortalFrame": 18,
        "PortalSwirl": 18, "Sentinel": 18, "Citadel": 22}
MULT = {"Ground": 1.9, "Sentinel": 2.4, "Island": 2.4, "Spire": 3.4, "VoidEye": 2.4, "BlackHole": 2.3, "Citadel": 2.3,
        "Comets": 2.6, "PortalFrame": 2.5, "PortalSwirl": 2.5, "Watchtower": 2.5}
# Shiba for scale: (x, z, facing, lift); default next to the part
SHIBA_AT = {"Ground": (-26, -30, 0, 0)}


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
    g = dk.ground(low, high, color=(52, 44, 70))
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
    bpy.context.scene.world.color = (0.30, 0.26, 0.42)
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
            x = hi[0] + 5 if hi[0] + 5 < 90 else lo[0] - 5
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_VoidPortal.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
