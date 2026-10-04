"""Final low-poly decor models for the theme DogeAltar (30 parts around the 28th Shiba, Cheems God).

Usage: blender --background --factory-startup --python build_DogeAltar.py -- <outdir> [PartId,PartId ...]
Writes Decor_DogeAltar_<PartId>.fbx, preview_<PartId>.png and stage_DogeAltar.png into <outdir>.
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
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "DogeAltar"))
ONLY = [a for arg in ARGS[1:] for a in arg.split(",") if a]
KEY = "DogeAltar"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_DogeAltar.json"))

# ---- palette (one for all 30 parts) ---------------------------------------------------------------------------------
MARBLE = (238, 232, 214)
WHITE = (248, 246, 238)
CREAM = (250, 238, 200)
BONE = (240, 232, 208)
GOLD = (244, 196, 56)
DGOLD = (190, 140, 40)
LGOLD = (252, 226, 130)
SAND = (222, 204, 156)
DSAND = (190, 166, 118)
STONE = (170, 160, 146)
LSTONE = (196, 188, 172)
DSTONE = (112, 104, 96)
RED = (186, 48, 52)
DRED = (140, 34, 40)
LAPIS = (52, 92, 176)
TEAL = (60, 170, 170)
GREEN = (84, 140, 70)
DGREEN = (52, 104, 56)
LGREEN = (120, 176, 90)
WOOD = (122, 84, 52)
DWOOD = (84, 58, 40)
LWOOD = (160, 114, 70)
PINK = (232, 130, 150)
LPINK = (246, 184, 198)
FUR = (240, 170, 60)
WATER = (90, 170, 210)
LWATER = (150, 208, 232)
PALE = (255, 232, 130)
GLOW = (255, 255, 240)
LANT = (255, 226, 150)
DARK = (46, 42, 40)
BLACK = (30, 28, 30)
FLAME = (255, 150, 40)
YFLAME = (255, 214, 80)


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


# ---- extra helpers for this theme -----------------------------------------------------------------------------------
def pyramid(p, cx, y0, cz, hx, h, col, hz=None, top=0.0, jit=0.04):
    """Square pyramid (top = 0) or frustum (top = fraction of the base kept at the top), axis aligned, base half sizes hx, hz."""
    hz = hx if hz is None else hz
    if top <= 0:
        pts = [(-hx, 0, -hz), (hx, 0, -hz), (hx, 0, hz), (-hx, 0, hz), (0, h, 0)]
        faces = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
    else:
        a, b = hx * top, hz * top
        pts = [(-hx, 0, -hz), (hx, 0, -hz), (hx, 0, hz), (-hx, 0, hz), (-a, h, -b), (a, h, -b), (a, h, b), (-a, h, b)]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (cx, y0, cz), pts, faces, col, jit)


def ear(p, x, y0, z, w, h, d, col, lean=0.0, jit=0.03):
    """Dog ear: a tapered wedge standing on y0, base w x d, tip leaning by `lean` along x."""
    pts = [(-w / 2, 0, -d / 2), (w / 2, 0, -d / 2), (w / 2, 0, d / 2), (-w / 2, 0, d / 2),
           (lean - 0.12, h, -d * 0.18), (lean + 0.12, h, -d * 0.18), (lean + 0.12, h, d * 0.18), (lean - 0.12, h, d * 0.18)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (x, y0, z), pts, faces, col, jit)


def bone(p, a, b, r, col, kr=None, spread=None, off=(1, 0, 0), kcol=None, verts=8, sub=1, jit=0.03):
    """A bone from stage point a to b: round shaft with two knobs at each end (knobs spread along `off`)."""
    rod(p, a, b, r, col, verts=verts, jit=jit)
    kr = kr or r * 1.25
    sp = spread or r * 0.9
    for e in (a, b):
        for s in (-1, 1):
            ball(p, (e[0] + off[0] * sp * s, e[1] + off[1] * sp * s, e[2] + off[2] * sp * s), kr, kcol or col, subdiv=sub, jit=jit)


def flame(p, cx, y0, cz, s=1.0):
    dk.cone(p, (cx, y0, cz), 0.7 * s, 1.5 * s, FLAME, verts=6, jitter=0.05)
    for k in range(4):
        a = math.radians(k * 90 + 20)
        dk.cone(p, (cx + 0.38 * s * math.cos(a), y0 + 0.1 * s, cz + 0.38 * s * math.sin(a)), 0.36 * s, (1.7 + 0.6 * (k % 2)) * s, RED if k % 2 else FLAME, verts=5, jitter=0.05)
    dk.cone(p, (cx, y0 + 0.1 * s, cz), 0.42 * s, 2.4 * s, YFLAME, verts=6, jitter=0.05)


def fluted(p, cx, cz, y0, y1, r, col, ribcol=None, n=8, verts=16, rib=0.16, top_r=None):
    vcyl(p, cx, y0, y1, cz, r, col, verts=verts, top_r=top_r)
    for k in range(n):
        a = 2 * math.pi * k / n
        cb(p, (cx + (r + 0.02) * math.cos(a), (y0 + y1) / 2, cz + (r + 0.02) * math.sin(a)), (rib, y1 - y0 - 0.1, rib),
           ribcol or col, 0.03, rot=(0, -math.degrees(a), 0))


def coin_heap(p, cx, cz, r0, levels, y0=0.0, th=0.5, col=GOLD, col2=DGOLD, verts=10, seed=0):
    """Pile of stacked gold coins (discs), shrinking and drifting as it rises."""
    import random
    rnd = random.Random(seed)
    for i in range(levels):
        t = i / max(1, levels - 1)
        r = r0 * (1 - 0.82 * t) + 0.5
        ox, oz = rnd.uniform(-0.5, 0.5) * r0 * 0.3 * (1 - t), rnd.uniform(-0.5, 0.5) * r0 * 0.3 * (1 - t)
        vcyl(p, cx + ox, y0 + i * th, y0 + (i + 1) * th, cz + oz, r, col if (i + seed) % 2 == 0 else col2, verts=verts, jit=0.05)


def paw(p, cx, y, cz, s, col):
    """Flat paw print (one pad and four toes) lying at height y."""
    cb(p, (cx, y, cz + 0.2 * s), (0.9 * s, 0.1, 0.8 * s), col, 0.02)
    for k, (dx, dz) in enumerate(((-0.6, -0.5), (-0.2, -0.85), (0.2, -0.85), (0.6, -0.5))):
        cb(p, (cx + dx * s, y, cz + dz * s), (0.36 * s, 0.1, 0.36 * s), col, 0.02)


def stairs(p, x0, x1, z0, z1, y0, n, rise, col, dirz=1, jit=0.03, col2=None):
    """n steps rising toward -dirz (the lowest step is nearest to z1 when dirz = 1)."""
    d = (z1 - z0) / n
    for i in range(n):
        if dirz == 1:
            za, zb = z0 + i * d, z1
        else:
            za, zb = z0, z1 - i * d
        bx(p, (x0, x1), (y0, y0 + rise * (n - i)), (za, zb), col if (col2 is None or i % 2 == 0) else col2, jit)


# ---- 1. Ground ---------------------------------------------------------------------------------------------------------
@part("Ground")
def build_Ground(p):
    bx(p, (-80, 80), (0, 0.3), (-57.5, 57.5), SAND, 0.05)
    for x in (-64, -32, 0, 32, 64):
        bx(p, (x - 0.15, x + 0.15), (0.3, 0.33), (-57, 57), DSAND, 0.02)
    for z in (-48, -16, 16, 48):
        bx(p, (-79.5, 79.5), (0.3, 0.33), (z - 0.15, z + 0.15), DSAND, 0.02)
    for a, c in (((-80, 80), (-57.5, -56.5)), ((-80, 80), (56.5, 57.5)), ((-80, -79), (-56.5, 56.5)), ((79, 80), (-56.5, 56.5))):
        bx(p, a, (0.3, 0.5), c, MARBLE, 0.03)
    # two darker plazas
    for (cx, cz, sx, sz) in ((-58, -2, 14, 14), (50, 30, 16, 10)):
        cb(p, (cx, 0.36, cz), (sx, 0.12, sz), DSAND, 0.04)
        cb(p, (cx, 0.4, cz), (sx - 1.6, 0.12, sz - 1.6), SAND, 0.04)
    # marble stepping stones along the winding walkway
    path = BP["Path"]
    k = 0
    for (ax, az), (cx_, cz_) in zip(path[:-1], path[1:]):
        L = math.hypot(cx_ - ax, cz_ - az)
        n = max(1, int(L / 5.2))
        yaw = math.degrees(math.atan2(-(cz_ - az), cx_ - ax))
        px, pz = -(cz_ - az) / L, (cx_ - ax) / L
        for i in range(n):
            t = (i + 0.5) / n
            off = 0.45 * (1 if k % 2 else -1)
            col = (MARBLE, CREAM, LSTONE)[k % 3]
            cb(p, (ax + (cx_ - ax) * t + px * off, 0.44, az + (cz_ - az) * t + pz * off), (4.0, 0.28, 4.8), col, 0.05, rot=(0, yaw, 0))
            k += 1
    # golden sun mosaic under the Shiba
    mx, mz = 28, -10
    disc(p, mx, 0.3, 0.4, mz, 15, DGOLD, 24)
    star_poly(p, (mx, 0.43, mz), 'xz', 14.6, 11.2, 0.06, LGOLD, n=12, rot0=90, jit=0.02)
    disc(p, mx, 0.4, 0.48, mz, 10.8, GOLD, 24)
    disc(p, mx, 0.48, 0.53, mz, 6.4, CREAM, 28)
    star_poly(p, (mx, 0.55, mz), 'xz', 5.8, 3.0, 0.04, GOLD, n=8, rot0=90, jit=0.02)
    disc(p, mx, 0.53, 0.58, mz, 2.0, RED, 16)
    for a in range(0, 360, 45):
        r_ = math.radians(a)
        cb(p, (mx + 8.6 * math.cos(r_), 0.5, mz + 8.6 * math.sin(r_)), (1.0, 0.06, 1.0), DGOLD, 0.03, rot=(0, -a + 45, 0))


# ---- 2. Gate -----------------------------------------------------------------------------------------------------------
@part("Gate")
def build_Gate(p):
    z = 54
    for s in (-1, 1):
        x = s * 10
        bx(p, (x - 2.8, x + 2.8), (0, 1), (z - 2.8, z + 2.8), STONE, 0.04)
        bx(p, (x - 2.3, x + 2.3), (1, 2), (z - 2.3, z + 2.3), MARBLE, 0.03)
        fluted(p, x, z, 2, 13.4, 1.7, MARBLE, CREAM, n=8, verts=16)
        vcyl(p, x, 2.0, 2.7, z, 2.0, GOLD, verts=16)
        vcyl(p, x, 12.7, 13.4, z, 2.0, GOLD, verts=16)
        vcyl(p, x, 13.4, 14.8, z, 1.7, DGOLD, verts=16, top_r=2.4)
        bx(p, (x - 2.5, x + 2.5), (14.8, 16), (z - 2.5, z + 2.5), GOLD, 0.03)
        # dog ears (outer ear leans outward, inner ear straight) with a pink inside
        ear(p, x + s * 1.3, 16, z, 2.0, 3.6, 1.4, GOLD, lean=s * 0.6)
        ear(p, x + s * 1.3, 16, z + 0.6, 1.1, 2.7, 0.5, PINK, lean=s * 0.45)
        ear(p, x - s * 1.0, 16, z, 1.5, 3.0, 1.3, GOLD, lean=-s * 0.2)
        ball(p, (x, 16.8, z + 1.6), 0.5, LGOLD, subdiv=1)
    bx(p, (-12, 12), (11.2, 13.6), (z - 1.6, z + 1.6), MARBLE, 0.03)
    bx(p, (-13, 13), (13.6, 15), (z - 1.9, z + 1.9), GOLD, 0.03)
    bx(p, (-12.2, 12.2), (10.8, 11.2), (z - 1.8, z + 1.8), DGOLD, 0.03)
    for i in range(-7, 8):
        if abs(i) > 2:
            cb(p, (i * 1.55, 12.4, z + 1.75), (0.8, 1.2, 0.3), CREAM, 0.04)
    bx(p, (-4.4, 4.4), (11.5, 13.3), (z + 1.6, z + 2.0), LAPIS, 0.03)
    bx(p, (-4.7, 4.7), (11.3, 11.5), (z + 1.6, z + 2.1), GOLD, 0.03)
    bx(p, (-4.7, 4.7), (13.3, 13.5), (z + 1.6, z + 2.1), GOLD, 0.03)
    bone(p, (-1.9, 12.4, z + 2.1), (1.9, 12.4, z + 2.1), 0.28, LGOLD, kr=0.42, spread=0.4, off=(0, 1, 0))
    # golden bone crowning the gate
    bone(p, (-3.2, 16.4, z), (3.2, 16.4, z), 0.5, GOLD, kr=0.8, spread=0.6, off=(0, 0, 1), kcol=LGOLD)


# ---- 3. Lanterns -------------------------------------------------------------------------------------------------------
def lantern(p, x, z, h):
    bx(p, (x - 1.4, x + 1.4), (0, 0.7), (z - 1.4, z + 1.4), STONE, 0.04)
    vcyl(p, x, 0.7, h, z, 0.8, LSTONE, verts=8, top_r=0.62)
    vcyl(p, x, 0.7, 1.4, z, 1.1, STONE, verts=8, top_r=0.8)
    bx(p, (x - 1.7, x + 1.7), (h, h + 0.35), (z - 1.7, z + 1.7), DGOLD, 0.03)
    bx(p, (x - 1.4, x + 1.4), (h + 0.35, h + 2.2), (z - 1.4, z + 1.4), LANT, 0.03)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (x + sx * 1.4 - 0.18, x + sx * 1.4 + 0.18), (h + 0.35, h + 2.2), (z + sz * 1.4 - 0.18, z + sz * 1.4 + 0.18), DGOLD, 0.02)
    bx(p, (x - 0.5, x + 0.5), (h + 0.35, h + 2.2), (z - 0.5, z + 0.5), GLOW, 0.02)
    bx(p, (x - 1.46, x + 1.46), (h + 1.15, h + 1.4), (z - 1.46, z + 1.46), DGOLD, 0.02)
    bx(p, (x - 2.2, x + 2.2), (h + 2.2, h + 2.6), (z - 2.2, z + 2.2), GOLD, 0.03)
    pyramid(p, x, h + 2.6, z, 1.9, 1.0, GOLD, top=0.12)
    ball(p, (x, h + 3.65, z), 0.35, LGOLD, subdiv=1)


@part("Lanterns")
def build_Lanterns(p):
    for x, z, h in ((-24, 48.5, 8), (-19, 53, 6), (-19, 47, 5), (-31, 51, 7)):
        lantern(p, x, z, h)


# ---- 4. Stall ----------------------------------------------------------------------------------------------------------
@part("Stall")
def build_Stall(p):
    z = 48
    bx(p, (-66, -54), (0, 3.2), (z - 2.5, z + 2.5), WOOD, 0.05)
    bx(p, (-66.3, -53.7), (3.2, 3.5), (z - 2.8, z + 2.8), LWOOD, 0.04)
    for i in range(6):
        bx(p, (-65.6 + i * 2.0, -64.2 + i * 2.0), (0.4, 2.8), (z + 2.5, z + 2.6), DWOOD, 0.04)
    bx(p, (-62, -58), (1.0, 2.6), (z + 2.6, z + 2.75), CREAM, 0.02)
    bone(p, (-61, 1.8, z + 2.8), (-59, 1.8, z + 2.8), 0.16, GOLD, kr=0.25, spread=0.25, off=(0, 1, 0))
    for sx in (-1, 1):
        for zz in (z - 2.6, z + 3.0):
            vcyl(p, -60 + sx * 6, 0, 10, zz, 0.45, DWOOD, verts=6)
            ball(p, (-60 + sx * 6, 10.2, zz), 0.4, GOLD, subdiv=1)
    # awning: red and cream stripes sloping down to the road, with a scalloped valance
    for i in range(7):
        x0 = -67 + i * 2
        col = RED if i % 2 == 0 else CREAM
        pts = [(x0, 11.7, z - 4), (x0 + 2, 11.7, z - 4), (x0 + 2, 10.5, z + 4), (x0, 10.5, z + 4),
               (x0, 12.3, z - 4), (x0 + 2, 12.3, z - 4), (x0 + 2, 11.1, z + 4), (x0, 11.1, z + 4)]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        dk.poly(p, (0, 0, 0), pts, faces, col, 0.03)
        cb(p, (x0 + 1, 9.9, z + 4.05), (2.0, 1.0, 0.25), col if i % 2 else CREAM, 0.03)
    # treats on the counter
    for dx, dz, c in ((-3.5, 0.2, GOLD), (-1.2, -0.6, LGOLD), (1.4, 0.3, GOLD), (3.2, -0.5, DGOLD)):
        cb(p, (-60 + dx, 4.0, z + dz), (1.3, 0.8, 1.0), c, 0.04, rot=(0, 20 * dx, 0))
    ball(p, (-60, 4.0, z + 0.2), 1.4, GOLD, scale=(1.6, 0.6, 1.0), subdiv=1)
    # crates with bones
    for (cx, cz, s, rot) in ((-53.6, 51.4, 3, 20), (-66, 52, 3.4, -25)):
        sy = 2.8 if s == 3 else 2.4
        cb(p, (cx, sy / 2, cz), (s, sy, s), WOOD, 0.05, rot=(0, rot, 0))
        cb(p, (cx, sy + 0.05, cz), (s + 0.2, 0.2, s + 0.2), LWOOD, 0.04, rot=(0, rot, 0))
        for k in range(3):
            a = math.radians(rot)
            ox, oz = (k - 1) * 0.8 * math.cos(a), -(k - 1) * 0.8 * math.sin(a)
            bone(p, (cx + ox - 0.3, sy + 0.2, cz + oz), (cx + ox + 0.3, sy + 1.5, cz + oz), 0.18, BONE, kr=0.3, spread=0.28, off=(0, 0, 1))


# ---- 5. Coins ----------------------------------------------------------------------------------------------------------
@part("Coins")
def build_Coins(p):
    import random
    rnd = random.Random(3)
    heaps = ((-62, 3, 12, 7.0, 0.46, 0.86, 2, 11), (-55, 2, 17, 4.6, 0.44, 0.9, 1, 6), (-68, 2, 6, 4.0, 0.5, 1.0, 1, 5))
    for (cx, cy, cz, r, sy, sz, sub, n) in heaps:
        ball(p, (cx, cy, cz), r, GOLD, scale=(1, sy, sz), subdiv=sub, jit=0.08)
        for i in range(n):
            ph = rnd.uniform(0, 2 * math.pi)
            u = rnd.uniform(0.1, 0.9)
            x, z = cx + r * u * math.cos(ph), cz + r * sz * u * math.sin(ph)
            y = cy + r * sy * math.sqrt(1 - u * u) + 0.1
            col = (LGOLD, GOLD, LGOLD, DGOLD)[i % 4]
            dk.cyl(p, (x, y, z), rnd.uniform(0.9, 1.3), 0.3, col, axis='y', verts=8,
                   rot=(rnd.uniform(-40, 40), rnd.uniform(0, 90), rnd.uniform(-40, 40)), jitter=0.04)
    for x, z, r in ((-58.5, 6.6, 0.9), (-64.8, 17.4, 0.8), (-52, 13, 0.8), (-70, 9, 0.7), (-59.2, 20, 0.7)):
        vcyl(p, x, -0.2, 0.15, z, r, GOLD if x > -60 else DGOLD, verts=8)
    # treasure chest (turned 25 degrees), lid open, gold inside
    cx, cz = -57, 8
    a = 25
    cb(p, (cx, 1.0, cz), (4, 2.0, 2.8), WOOD, 0.04, rot=(0, a, 0))
    for dx in (-1.4, 1.4):
        px, pz = ry(dx, 0, a)
        cb(p, (cx + px, 1.0, cz + pz), (0.4, 2.1, 2.9), DGOLD, 0.03, rot=(0, a, 0))
    cb(p, (cx, 2.05, cz), (3.6, 0.2, 2.4), GOLD, 0.03, rot=(0, a, 0))
    px, pz = ry(0, -1.3, a)
    cb(p, (cx + px, 2.9, cz + pz), (4, 0.4, 1.3), DWOOD, 0.04, rot=(35, a, 0))
    ball(p, (cx, 2.2, cz), 1.3, GOLD, scale=(1.3, 0.5, 1.0), subdiv=1)
    # giant standing coin leaning on the heap: rim, face disc and a paw
    xcyl(p, -70.6, -69.4, 5.4, 14, 4.0, DGOLD, verts=16)
    xcyl(p, -70.9, -69.1, 5.4, 14, 3.3, GOLD, verts=16)
    xcyl(p, -71.0, -69.0, 5.4, 14, 2.2, LGOLD, verts=14)
    for k, (dz, dy) in enumerate(((-0.9, 0.9), (0.0, 1.3), (0.9, 0.9), (0, -0.4))):
        ball(p, (-71.15, 5.4 + dy, 14 + dz), 0.42 if k < 3 else 0.7, DGOLD, scale=(0.4, 1, 1), subdiv=1)
    for (x, z, n, r) in ((-52, 11, 5, 1.3), (-51, 14, 4, 1.1)):
        for i in range(n):
            vcyl(p, x + 0.12 * (i % 2), i * 0.5 - 0.1, i * 0.5 + 0.4, z, r, GOLD if i % 2 else DGOLD, verts=10)


# ---- 6. Fountain -------------------------------------------------------------------------------------------------------
@part("Fountain")
def build_Fountain(p):
    cx, cz = 28, 40
    vcyl(p, cx, -0.0, 2.0, cz, 8, STONE, verts=20)
    vcyl(p, cx, 1.5, 2.0, cz, 8.25, LSTONE, verts=20)
    vcyl(p, cx, 0.5, 0.9, cz, 8.3, DGOLD, verts=20)
    vcyl(p, cx, 1.9, 2.15, cz, 6.9, WATER, verts=20)
    vcyl(p, cx, 2.0, 7.2, cz, 1.5, MARBLE, verts=12, top_r=1.1)
    vcyl(p, cx, 2.0, 3.0, cz, 2.6, STONE, verts=12, top_r=1.5)
    vcyl(p, cx, 6.8, 7.4, cz, 1.9, GOLD, verts=12)
    vcyl(p, cx, 7.4, 8.4, cz, 4.0, MARBLE, verts=16, top_r=4.0)
    vcyl(p, cx, 8.4, 9.2, cz, 4.0, MARBLE, verts=16, top_r=4.3)
    vcyl(p, cx, 9.2, 9.6, cz, 4.3, GOLD, verts=16)
    vcyl(p, cx, 9.4, 9.85, cz, 3.5, WATER, verts=16)
    # golden bone spout
    rod(p, (cx, 9.8, cz), (cx, 13.2, cz), 0.5, GOLD, verts=8)
    for sx in (-1, 1):
        ball(p, (cx + sx * 0.75, 13.4, cz), 0.95, GOLD, subdiv=1)
        ball(p, (cx + sx * 0.75, 9.9, cz), 0.8, DGOLD, subdiv=1)
    ball(p, (cx, 14.3, cz), 0.8, LGOLD, subdiv=1)
    # curved sprays from the bone into the bowl, and from the bowl over the rim into the basin
    for k in range(3):
        a = math.radians(k * 120 + 20)
        c_, s_ = math.cos(a), math.sin(a)
        pts = [(0.5, 13.0), (1.7, 12.7), (2.8, 11.6), (3.4, 9.9)]
        for (r0, y0_), (r1, y1_) in zip(pts[:-1], pts[1:]):
            bar(p, (cx + r0 * c_, y0_, cz + r0 * s_), (cx + r1 * c_, y1_, cz + r1 * s_), 0.28, LWATER, 0.02)
        b = a + 0.9
        c2, s2 = math.cos(b), math.sin(b)
        pts = [(4.2, 9.4), (5.0, 8.9), (5.8, 7.4), (6.3, 4.8), (6.5, 2.2)]
        for (r0, y0_), (r1, y1_) in zip(pts[:-1], pts[1:]):
            bar(p, (cx + r0 * c2, y0_, cz + r0 * s2), (cx + r1 * c2, y1_, cz + r1 * s2), 0.28, LWATER, 0.02)
    # four golden dog-head gargoyles on the rim
    for k in range(4):
        a = math.radians(k * 90 + 45)
        gx, gz = cx + 8.05 * math.cos(a), cz + 8.05 * math.sin(a)
        ball(p, (gx, 2.9, gz), 0.75, GOLD, subdiv=1)
        cb(p, (gx + 0.5 * math.cos(a), 2.7, gz + 0.5 * math.sin(a)), (0.6, 0.45, 0.6), CREAM, 0.03, rot=(0, -math.degrees(a), 0))
        for s_ in (-1, 1):
            ear(p, gx - s_ * 0.45 * math.sin(a), 3.4, gz + s_ * 0.45 * math.cos(a), 0.4, 0.6, 0.3, DGOLD)
    # coins in the basin
    for k, (r, a) in enumerate(((5.2, 20), (4.6, 100), (5.6, 170), (5.0, 240), (3.5, 300), (6.0, 330), (4.0, 60))):
        vcyl(p, cx + r * math.cos(math.radians(a)), 2.15, 2.4, cz + r * math.sin(math.radians(a)), 0.7, GOLD if k % 2 else LGOLD, verts=8)


# ---- 7. Hall -----------------------------------------------------------------------------------------------------------
@part("Hall")
def build_Hall(p):
    cx = -62
    bx(p, (cx - 16, cx + 16), (0, 2), (-56, -34), STONE, 0.04)
    bx(p, (cx - 14, cx + 14), (2, 4), (-54, -36), MARBLE, 0.03)
    for i in range(5):                      # steps up to the porch
        bx(p, (cx - 4.5, cx + 4.5), (2.0, 2.0 + 0.4 * (5 - i)), (-36 + i * 0.4, -34.0), LSTONE, 0.03)
    # cella
    bx(p, (cx - 11, cx + 11), (4, 19), (-54, -42), MARBLE, 0.03)
    bx(p, (cx - 11.3, cx + 11.3), (4, 5), (-54.3, -41.7), GOLD, 0.03)
    bx(p, (cx - 11.3, cx + 11.3), (17.6, 19), (-54.3, -41.7), GOLD, 0.03)
    bx(p, (cx - 3.5, cx + 3.5), (4, 12), (-42.3, -41.6), DWOOD, 0.03)
    bx(p, (cx - 3.9, cx + 3.9), (11.6, 12.3), (-42.4, -41.5), GOLD, 0.02)
    bx(p, (cx - 0.15, cx + 0.15), (4, 11.6), (-42.4, -41.5), GOLD, 0.02)
    ball(p, (cx, 12.0, -42.0), 1.8, DWOOD, scale=(1.9, 0.6, 0.12), subdiv=1)
    for sx in (-1, 1):                      # lapis windows on the side walls and beside the door
        bx(p, (cx + sx * 11 - 0.15, cx + sx * 11 + 0.15), (9, 15), (-50, -46), LAPIS, 0.03)
        bx(p, (cx + sx * 7.5 - 1.2, cx + sx * 7.5 + 1.2), (8.5, 14.5), (-42.2, -41.7), LAPIS, 0.03)
        bx(p, (cx + sx * 7.5 - 1.5, cx + sx * 7.5 + 1.5), (14.5, 15.0), (-42.3, -41.6), GOLD, 0.03)
    # colonnade
    for k in range(6):
        x = cx - 10 + k * 4
        bx(p, (x - 1.5, x + 1.5), (4, 4.6), (-41, -38), GOLD, 0.03)
        vcyl(p, x, 4.6, 18.2, -39.5, 1.2, MARBLE if k % 2 else CREAM, verts=12, top_r=1.0)
        vcyl(p, x, 17.4, 18.2, -39.5, 1.5, GOLD, verts=12)
        bx(p, (x - 1.7, x + 1.7), (18.2, 19), (-41.2, -37.8), GOLD, 0.03)
    # entablature and gable
    bx(p, (cx - 14, cx + 14), (19, 21), (-53, -36), GOLD, 0.03)
    dk.prism(p, (cx, 21, -46), 22, 13, 4.1, DGOLD, ridge='z', jitter=0.03)
    dk.prism(p, (cx, 21, -46), 18, 11, 3.1, GOLD, ridge='z', jitter=0.03)
    for sx in (-1, 1):                      # acroteria: golden dog ears at the roof corners
        ear(p, cx + sx * 10.5, 21, -52, 1.8, 3.0, 1.6, GOLD, lean=sx * 0.3)
        ear(p, cx + sx * 10.5, 21, -40, 1.8, 3.0, 1.6, GOLD, lean=sx * 0.3)
    ball(p, (cx, 22.4, -39.4), 1.5, LAPIS, scale=(1, 1, 0.3), subdiv=1)
    # drum and dome
    vcyl(p, cx, 24.5, 27.5, -47, 4.9, GOLD, verts=12)
    vcyl(p, cx, 27.3, 27.8, -47, 5.2, DGOLD, verts=12)
    for k in range(6):
        a = math.radians(k * 60 + 30)
        bx(p, (cx + 4.9 * math.cos(a) - 0.5, cx + 4.9 * math.cos(a) + 0.5), (25.2, 26.9), (-47 + 4.9 * math.sin(a) - 0.5, -47 + 4.9 * math.sin(a) + 0.5), LAPIS, 0.03)
    dome(p, cx, 27.7, -47, 4.5, 4.7, GOLD, seg=12, rings=3, jit=0.04)
    vcyl(p, cx, 32.2, 32.8, -47, 0.35, DGOLD, verts=6)
    ball(p, (cx, 32.7, -47), 0.3, LGOLD, subdiv=1)


# ---- 8. Torches --------------------------------------------------------------------------------------------------------
def torch_pillar(p, x, z, h):
    bx(p, (x - 1.5, x + 1.5), (0, 0.8), (z - 1.5, z + 1.5), DSTONE, 0.04)
    vcyl(p, x, 0.8, h, z, 0.9, STONE, verts=8, top_r=0.75)
    vcyl(p, x, 0.8, 1.8, z, 1.2, LSTONE, verts=8)
    vcyl(p, x, h - 1.0, h, z, 1.1, GOLD, verts=8)
    vcyl(p, x, h, h + 0.5, z, 1.2, DGOLD, verts=10)
    vcyl(p, x, h + 0.5, h + 1.1, z, 1.3, GOLD, verts=10, top_r=1.95)
    vcyl(p, x, h + 1.0, h + 1.25, z, 1.95, DGOLD, verts=10)
    vcyl(p, x, h + 1.1, h + 1.2, z, 1.5, DARK, verts=10)
    flame(p, x, h + 1.2, z, 1.25)
    for k in range(3):
        a = k * 2.1
        cb(p, (x + 0.7 * math.cos(a), h + 1.4, z + 0.7 * math.sin(a)), (0.4, 0.4, 0.4), YFLAME, 0.03, rot=(0, 20 * k, 0))


@part("Torches")
def build_Torches(p):
    for x, z, h in ((40, 22, 9), (46, 27, 7), (49.5, 20.5, 10), (43, 31, 6)):
        torch_pillar(p, x, z, h)


# ---- 9. Wall -----------------------------------------------------------------------------------------------------------
@part("Wall")
def build_Wall(p):
    z0 = -12
    bx(p, (40.5, 49.5), (0, 1), (-23, -1), STONE, 0.04)
    bx(p, (41.5, 49.5), (1, 2), (-22.4, -1.6), MARBLE, 0.03)
    bx(p, (44.5, 49.5), (2, 17), (-22, -2), MARBLE, 0.03)
    bx(p, (44.3, 49.5), (2, 2.8), (-22.2, -1.8), GOLD, 0.03)
    bx(p, (44.4, 49.5), (3.6, 4.0), (-22.1, -1.9), DGOLD, 0.02)
    bx(p, (44.4, 49.5), (16.0, 16.4), (-22.1, -1.9), DGOLD, 0.02)
    bx(p, (42.9, 49.9), (17, 19.2), (-23, -1), GOLD, 0.03)
    for i in range(10):                     # dentils under the cornice
        bx(p, (43.6, 44.4), (16.6, 17.0), (-21.6 + i * 2.0, -20.8 + i * 2.0), CREAM, 0.03)
    for i in range(6):                      # golden dog-ear finials along the top
        ear(p, 46.4, 19.0, -20.5 + i * 3.7, 2.4, 2.0, 1.4, GOLD, lean=0.0)
    # the sun niche
    xcyl(p, 43.0, 44.5, 10, z0, 5.5, GOLD, verts=24)
    star_poly(p, (42.9, 10, z0), 'yz', 5.5, 4.0, 0.2, LGOLD, n=12, rot0=90, jit=0.02)
    xcyl(p, 42.6, 43.6, 10, z0, 3.7, CREAM, verts=20)
    xcyl(p, 42.4, 43.2, 10, z0, 1.9, RED, verts=14)
    for sz in (-1, 1):
        fluted(p, 43.5, z0 + sz * 9, 2, 15.8, 1.2, DGOLD, GOLD, n=6, verts=12, rib=0.14)
        bx(p, (41.8, 45.2), (15.8, 17.0), (z0 + sz * 9 - 1.7, z0 + sz * 9 + 1.7), GOLD, 0.03)
        bx(p, (41.8, 45.2), (2, 2.8), (z0 + sz * 9 - 1.7, z0 + sz * 9 + 1.7), GOLD, 0.03)
        bx(p, (44.0, 46.8), (2.0, 10.0), (z0 + sz * 5 - 0.4, z0 + sz * 5 + 0.4), LAPIS, 0.03)
        bx(p, (43.9, 46.9), (9.6, 10.0), (z0 + sz * 5 - 0.6, z0 + sz * 5 + 0.6), GOLD, 0.03)
        bx(p, (43.9, 46.9), (8.2, 8.6), (z0 + sz * 5 - 0.6, z0 + sz * 5 + 0.6), GOLD, 0.03)
    for sz in (-1, 1):
        for k in range(3):
            bx(p, (43.9, 44.3), (3.0 + k * 1.6, 3.5 + k * 1.6), (z0 + sz * 5 - 0.25, z0 + sz * 5 + 0.25), GOLD, 0.02)


# ---- 10. Pond ----------------------------------------------------------------------------------------------------------
@part("Pond")
def build_Pond(p):
    cx, cz = 56, 47
    bx(p, (43, 69), (0.15, 0.4), (40, 54), WATER, 0.03)
    bx(p, (44, 68), (0.4, 0.5), (41, 53), LWATER, 0.05)
    # rim: a ring of rocks around the oval
    import random
    rnd = random.Random(5)
    n = 18
    for i in range(n):
        a = 2 * math.pi * i / n
        x = cx + 13.6 * math.cos(a)
        z = cz + 7.3 * math.sin(a)
        s = rnd.uniform(1.6, 2.4)
        h = rnd.uniform(0.9, 1.5)
        col = (STONE, LSTONE, MARBLE, STONE)[i % 4]
        cb(p, (x, h / 2, z), (s * 1.3, h, s), col, 0.06, rot=(0, -math.degrees(a) + rnd.uniform(-15, 15), 0))
    # arched wooden bridge: planks following an arc, red rails with gold posts
    for i in range(7):
        t = -1 + 2 * (i + 0.5) / 7
        x = cx + t * 6.8
        y = 1.55 + (1 - t * t) * 0.75
        ang = math.degrees(math.atan2(-2 * t * 0.75 / 6.8, 1))
        cb(p, (x, y, cz), (2.1, 0.35, 4.0), WOOD if i % 2 else LWOOD, 0.05, rot=(0, 0, ang))
    for sz in (-1, 1):
        prev = None
        for i in range(10):
            t = -1 + 2 * i / 9
            pt = (cx + t * 6.8, 2.2 + (1 - t * t) * 0.75 + 0.9, cz + sz * 1.95)
            if prev:
                rod(p, prev, pt, 0.17, RED, verts=6)
            if i % 3 == 0:
                rod(p, (pt[0], pt[1] - 1.1, pt[2]), pt, 0.14, DWOOD, verts=6)
                ball(p, (pt[0], pt[1] + 0.1, pt[2]), 0.28, GOLD, subdiv=1)
            prev = pt
    # lily pads, lotus flowers and koi
    for (x, z, r) in ((48, 50, 1.7), (51, 51.5, 1.3), (63, 43, 1.5), (60, 41.6, 1.2), (65.5, 49.5, 1.4), (46.8, 44, 1.3)):
        vcyl(p, x, 0.45, 0.6, z, r, GREEN, verts=8)
    for (x, z, c) in ((48.4, 50.3, PINK), (63.3, 43.3, LPINK), (65.2, 49.8, PINK)):
        for k in range(5):
            a = k * 72
            ear(p, x + 0.5 * math.cos(math.radians(a)), 0.6, z + 0.5 * math.sin(math.radians(a)), 0.5, 0.8, 0.3, c, lean=0.1)
        ball(p, (x, 0.9, z), 0.25, GOLD, subdiv=1)
    for (x, z, a, c) in ((52, 43, 20, FUR), (58.5, 51.2, 160, WHITE), (46.5, 47.5, 300, GOLD)):
        ball(p, (x, 0.62, z), 0.9, c, scale=(1.9, 0.55, 0.7), subdiv=1)
        ex, ez = ry(-1.9, 0, a)
        ear(p, x + ex, 0.5, z + ez, 0.9, 0.9, 0.2, RED if c != GOLD else DGOLD, lean=0.0)
        cb(p, (x, 0.95, z), (0.9, 0.12, 0.2), RED if c == WHITE else DGOLD, 0.03)


# ---- 11. Pagoda --------------------------------------------------------------------------------------------------------
@part("Pagoda")
def build_Pagoda(p):
    cx, cz = 68, 8
    bx(p, (cx - 8, cx + 8), (0, 1.6), (cz - 8, cz + 8), STONE, 0.04)
    bx(p, (cx - 7.4, cx + 7.4), (1.6, 1.9), (cz - 7.4, cz + 7.4), LSTONE, 0.03)
    levels = [(1.9, 8.0, 4.4, 14.4), (9.3, 14.7, 3.2, 11.2), (15.8, 20.6, 2.3, 8.0)]
    for i, (y0, y1, hw, roof_w) in enumerate(levels):
        bx(p, (cx - hw, cx + hw), (y0, y1), (cz - hw, cz + hw), CREAM, 0.03)
        for sx in (-1, 1):
            for sz in (-1, 1):
                vcyl(p, cx + sx * hw, y0, y1, cz + sz * hw, 0.38 + 0.05 * (2 - i), RED, verts=6)
        bx(p, (cx - hw - 0.1, cx + hw + 0.1), (y1 - 0.5, y1), (cz - hw - 0.1, cz + hw + 0.1), RED, 0.03)
        # windows on the four faces
        for s in (-1, 1):
            bx(p, (cx - hw * 0.45, cx + hw * 0.45), (y0 + (y1 - y0) * 0.35, y0 + (y1 - y0) * 0.8), (cz + s * hw, cz + s * hw + s * 0.12), LAPIS, 0.03)
            bx(p, (cx + s * hw, cx + s * hw + s * 0.12), (y0 + (y1 - y0) * 0.35, y0 + (y1 - y0) * 0.8), (cz - hw * 0.45, cz + hw * 0.45), LAPIS, 0.03)
        # roof: red frustum with gold edge and upturned corner horns
        rw = roof_w / 2
        pyramid(p, cx, y1, cz, rw, 1.3, RED, top=0.42, jit=0.03)
        bx(p, (cx - rw, cx + rw), (y1, y1 + 0.25), (cz - rw, cz + rw), GOLD, 0.03)
        for sx in (-1, 1):
            for sz in (-1, 1):
                ear(p, cx + sx * (rw - 0.5), y1 + 0.2, cz + sz * (rw - 0.5), 0.9, 1.5, 0.9, GOLD, lean=0.0)
    # door
    bx(p, (cx - 1.4, cx + 1.4), (1.9, 5.5), (cz + 4.4, cz + 4.55), DWOOD, 0.03)
    bx(p, (cx - 1.6, cx + 1.6), (5.4, 5.8), (cz + 4.4, cz + 4.6), GOLD, 0.03)
    # spire with coin rings
    vcyl(p, cx, 21.7, 26.5, cz, 0.35, DGOLD, verts=6)
    for k, y in enumerate((22.6, 23.8, 25.0)):
        vcyl(p, cx, y, y + 0.5, cz, 1.05 - 0.15 * k, GOLD, verts=10)
    ball(p, (cx, 27.5, cz), 1.0, LGOLD, subdiv=1)


# ---- 12. Guardians -----------------------------------------------------------------------------------------------------
def sitdog(p, x, z, k, fur=MARBLE, trim=GOLD, face=(0, 1)):
    fx, fz = face
    bx(p, (x - 3 * k, x + 3 * k), (0, 1.4), (z - 3 * k, z + 3 * k), STONE, 0.04)
    bx(p, (x - 2.6 * k, x + 2.6 * k), (1.4, 2.0), (z - 2.6 * k, z + 2.6 * k), GOLD, 0.03)
    # haunches, torso, chest
    ball(p, (x, 2.0 + 2.6 * k, z - 0.5 * k * fz), 2.6 * k, fur, scale=(1.0, 1.0, 1.05), subdiv=1)
    cb(p, (x, 2.0 + 5.4 * k, z + 0.2 * k * fz), (3.2 * k, 6.0 * k, 3.0 * k), fur, 0.03)
    ball(p, (x, 2.0 + 7.4 * k, z + 0.5 * k * fz), 1.9 * k, fur, subdiv=1)
    for sx in (-1, 1):                      # front legs
        cb(p, (x + sx * 1.0 * k, 2.0 + 2.8 * k, z + 1.5 * k * fz), (1.0 * k, 5.2 * k, 1.1 * k), fur, 0.03)
        cb(p, (x + sx * 1.0 * k, 2.15, z + 1.9 * k * fz), (1.2 * k, 0.5, 1.5 * k), fur, 0.03)
    # head
    hy = 2.0 + 11.4 * k
    ball(p, (x, hy, z + 0.4 * k * fz), 2.3 * k, fur, scale=(1.0, 0.95, 1.0), subdiv=1)
    cb(p, (x, hy - 0.5 * k, z + 2.3 * k * fz), (1.8 * k, 1.2 * k, 2.0 * k), fur, 0.03)
    cb(p, (x, hy - 0.1 * k, z + 3.3 * k * fz), (0.8 * k, 0.6 * k, 0.5 * k), DARK, 0.02)
    for sx in (-1, 1):
        cb(p, (x + sx * 0.8 * k, hy + 0.5 * k, z + 2.35 * k * fz), (0.5 * k, 0.5 * k, 0.3 * k), DARK, 0.02)
        ear(p, x + sx * 1.5 * k, hy + 1.6 * k, z + 0.1 * k * fz, 1.3 * k, 2.6 * k, 0.9 * k, trim, lean=sx * 0.2 * k)
        ear(p, x + sx * 1.5 * k, hy + 1.7 * k, z + 0.5 * k * fz, 0.7 * k, 1.8 * k, 0.3 * k, PINK, lean=sx * 0.15 * k)
    # collar with medallion
    ball(p, (x, 2.0 + 9.4 * k, z + 0.5 * k * fz), 2.15 * k, trim, scale=(1, 0.28, 1), subdiv=1)
    ball(p, (x, 2.0 + 9.0 * k, z + 2.0 * k * fz), 0.55 * k, LGOLD, subdiv=1)
    # tail curling behind
    ball(p, (x - 1.2 * k, 2.0 + 1.8 * k, z - 2.6 * k * fz), 1.3 * k, fur, scale=(0.6, 1.3, 1.5), subdiv=1)
    ball(p, (x - 1.2 * k, 2.0 + 3.4 * k, z - 3.2 * k * fz), 0.8 * k, trim, subdiv=1)


@part("Guardians")
def build_Guardians(p):
    sitdog(p, -17, 6, 1.0)
    sitdog(p, -8, 13, 0.85)


# ---- 13. Banners -------------------------------------------------------------------------------------------------------
@part("Banners")
def build_Banners(p):
    for x, z, h, col in ((-48, 3, 16, RED), (-43, -1, 13, LAPIS), (-40, 5, 15, RED)):
        bx(p, (x - 1.2, x + 1.2), (0, 1.2), (z - 1.2, z + 1.2), STONE, 0.04)
        bx(p, (x - 0.9, x + 0.9), (1.2, 1.7), (z - 0.9, z + 0.9), GOLD, 0.03)
        vcyl(p, x, 1.7, h, z, 0.35, DWOOD, verts=8)
        rod(p, (x - 1.9, h - 1.0, z), (x + 1.9, h - 1.0, z), 0.2, GOLD, verts=6)
        ball(p, (x, h + 0.6, z), 0.7, GOLD, subdiv=1)
        bz = z + 1.9
        bx(p, (x - 1.7, x + 1.7), (h - 7.4, h - 1.0), (bz - 0.15, bz + 0.15), col, 0.03)
        # swallowtail
        pts = [(x - 1.7, h - 7.4, bz - 0.15), (x + 1.7, h - 7.4, bz - 0.15), (x, h - 8.4, bz - 0.15),
               (x - 1.7, h - 7.4, bz + 0.15), (x + 1.7, h - 7.4, bz + 0.15), (x, h - 8.4, bz + 0.15)]
        dk.poly(p, (0, 0, 0), pts, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], col, 0.03)
        bx(p, (x - 1.7, x - 1.4), (h - 7.4, h - 1.0), (bz + 0.15, bz + 0.25), GOLD, 0.02)
        bx(p, (x + 1.4, x + 1.7), (h - 7.4, h - 1.0), (bz + 0.15, bz + 0.25), GOLD, 0.02)
        bx(p, (x - 1.7, x + 1.7), (h - 1.4, h - 1.0), (bz + 0.15, bz + 0.25), GOLD, 0.02)
        bone(p, (x - 0.8, h - 4.2, bz + 0.3), (x + 0.8, h - 4.2, bz + 0.3), 0.18, CREAM, kr=0.3, spread=0.28, off=(0, 1, 0))
        for sx in (-1, 1):
            ball(p, (x + sx * 1.5, h - 1.1, bz + 0.1), 0.25, GOLD, subdiv=1)


# ---- 14. BoneArch ------------------------------------------------------------------------------------------------------
@part("BoneArch")
def build_BoneArch(p):
    z = -12
    for x in (-73, -59):
        vcyl(p, x, 1.0, 18.0, z, 1.35, BONE, verts=10, top_r=1.2)
        vcyl(p, x, 4.0, 4.5, z, 1.5, GOLD, verts=10)
        for s in (-1, 1):
            ball(p, (x, 1.2, z + s * 1.4), 1.7, BONE, subdiv=1)
    for s in (-1, 1):
        for x in (-75, -57):
            ball(p, (x, 19.6, z + s * 1.4), 1.7, BONE, subdiv=1)
    for x in (-73, -59):
        ball(p, (x, 17.8, z), 1.9, BONE, scale=(1, 1, 1.4), subdiv=1)
    xcyl(p, -75, -57, 18.4, z, 1.7, BONE, verts=10)
    for x in (-69.5, -62.5):
        xcyl(p, x - 0.25, x + 0.25, 18.4, z, 1.85, GOLD, verts=10)
    # golden skull charm
    ball(p, (-66, 21.6, z), 1.5, GOLD, scale=(1, 0.95, 0.95), subdiv=1)
    cb(p, (-66, 20.4, z + 0.7), (1.4, 0.8, 1.2), DGOLD, 0.03)
    for s in (-1, 1):
        cb(p, (-66 + s * 0.55, 21.8, z + 1.35), (0.5, 0.55, 0.2), DARK, 0.02)
    cb(p, (-66, 21.0, z + 1.4), (0.3, 0.4, 0.2), DARK, 0.02)
    for k in range(4):
        cb(p, (-66.45 + k * 0.3, 20.1, z + 1.3), (0.2, 0.35, 0.2), CREAM, 0.02)
    rod(p, (-66, 19.9, z), (-66, 20.6, z), 0.3, DGOLD, verts=6)


# ---- 15. BonePillars ---------------------------------------------------------------------------------------------------
@part("BonePillars")
def build_BonePillars(p):
    bx(p, (11, 25), (0, 1.2), (-45, -31), MARBLE, 0.04)
    bx(p, (11.6, 24.4), (1.2, 1.35), (-44.4, -31.6), GOLD, 0.03)
    disc(p, 18, 1.35, 1.45, -38, 4.2, DGOLD, 20)
    for x, z, h in ((14, -34, 14), (22, -34, 18), (18, -42, 22)):
        top = 1.2 + h
        vcyl(p, x, 2.3, top, z, 0.95, GOLD, verts=10, top_r=0.8)
        for y in (top * 0.3, top * 0.55, top * 0.8):
            vcyl(p, x, y, y + 0.35, z, 1.15, DGOLD, verts=10)
        for yy, sy in ((top, 1), (2.3, 1)):
            for s in (-1, 1):
                ball(p, (x + s * 0.9, yy, z), 1.25, LGOLD, subdiv=1)
        ball(p, (x, top, z), 0.95, GOLD, scale=(1.4, 1.0, 1.0), subdiv=1)
        ball(p, (x, 2.3, z), 0.95, GOLD, scale=(1.4, 1.0, 1.0), subdiv=1)
        bx(p, (x - 1.5, x + 1.5), (1.35, 1.9), (z - 1.5, z + 1.5), STONE, 0.03)


# ---- 16. Garden --------------------------------------------------------------------------------------------------------
def hedge(p, x0, x1, z0, z1, h):
    bx(p, (x0, x1), (0, h), (z0, z1), GREEN, 0.06)
    n = max(2, int((x1 - x0) / 2.0)) if (x1 - x0) > (z1 - z0) else max(2, int((z1 - z0) / 2.0))
    for i in range(n):
        t = (i + 0.5) / n
        c = (x0 + (x1 - x0) * t, h, z0 + (z1 - z0) * t) if (x1 - x0) > (z1 - z0) else ((x0 + x1) / 2, h, z0 + (z1 - z0) * t)
        ball(p, c, min(x1 - x0, z1 - z0) * 0.6 if min(x1 - x0, z1 - z0) < 4 else 1.4, LGREEN if i % 2 else GREEN, scale=(1, 0.7, 1), subdiv=1)


def blossom_tree(p, x, z, th, trunk_r, cw, ch, cy, col, col2):
    vcyl(p, x, 0, th, z, trunk_r, WOOD, verts=8, top_r=trunk_r * 0.7)
    ball(p, (x, cy, z), cw / 2, col, scale=(1, ch / cw, 1), subdiv=2)
    for k in range(5):
        a = k * 72 + 20
        ball(p, (x + cw * 0.28 * math.cos(math.radians(a)), cy - ch * 0.12 + (k % 2) * ch * 0.2, z + cw * 0.28 * math.sin(math.radians(a))),
             cw * 0.22, col2, subdiv=1)


@part("Garden")
def build_Garden(p):
    hedge(p, -56, -44, 22.7, 25.3, 4)
    hedge(p, -42, -34, 22.7, 25.3, 4)
    hedge(p, -35.3, -32.7, 24, 32, 3)
    bx(p, (-52, -44), (0, 1.6), (26, 31), (110, 78, 52), 0.05)
    bx(p, (-52.3, -43.7), (1.6, 1.8), (25.7, 31.3), STONE, 0.04)
    for k, (dx, dz, c) in enumerate(((-50.6, 27, PINK), (-49.2, 29.6, GOLD), (-47.6, 27.4, PINK), (-46.2, 29.8, LPINK), (-51, 29.8, LPINK), (-45, 27.2, GOLD))):
        rod(p, (dx, 1.6, dz), (dx, 2.3, dz), 0.08, GREEN, verts=4)
        ball(p, (dx, 2.45, dz), 0.55, c, subdiv=1)
    blossom_tree(p, -40, 32.5, 6, 0.8, 7, 6, 8, LGREEN, GREEN)
    blossom_tree(p, -54, 31.5, 6.8, 0.9, 8, 7, 9, GREEN, LGREEN)
    blossom_tree(p, -44, 21, 7.6, 0.8, 7.4, 6.4, 9.6, PINK, LPINK)
    for i in range(8):
        cb(p, (-43 + (0.5 if i % 2 else -0.5), 0.3, 21.8 + i * 2.0), (1.8, 0.2, 1.4), STONE if i % 2 else LSTONE, 0.05, rot=(0, 10 * (i % 3) - 10, 0))
    for (x, z) in ((-38.8, 28), (-40.2, 27), (-36.8, 34.5)):
        ball(p, (x, 0.5, z), 0.5, PINK, subdiv=1)


# ---- 17. Tablets -------------------------------------------------------------------------------------------------------
@part("Tablets")
def build_Tablets(p):
    z = -17
    bx(p, (-55, -39), (0, 1), (z - 3.5, z + 3.5), STONE, 0.04)
    bx(p, (-54.5, -39.5), (1, 1.25), (z - 3.1, z + 3.1), LSTONE, 0.03)

    def tablet(x, h, w, zz, rot, glyph):
        cb(p, (x, 1.2 + h / 2 - 0.3, zz), (w, h - 0.6, 1.2), MARBLE, 0.03, rot=(0, rot, 0))
        zcyl(p, x, 1.2 + h - 0.6, zz - 0.6, zz + 0.6, w / 2, MARBLE, verts=10, rot=(0, rot, 0))
        a = math.radians(rot)
        ox, oz = ry(0, 0.75, rot)
        # carved border and glyph on the road side
        cb(p, (x + ox, 1.2 + h * 0.5, zz + oz), (w - 0.8, h * 0.8, 0.1), DGOLD, 0.02, rot=(0, rot, 0))
        cb(p, (x + ox * 1.1, 1.2 + h * 0.5, zz + oz * 1.1), (w - 1.2, h * 0.7, 0.1), MARBLE, 0.02, rot=(0, rot, 0))
        gx, gz = ry(0, 0.95, rot)
        if glyph == 0:
            ball(p, (x + gx, 1.2 + h * 0.62, zz + gz), 0.8, GOLD, scale=(1, 1, 0.2), subdiv=1)
            for s in (-1, 1):
                dx, dz = ry(s * 0.55, 0, rot)
                ear(p, x + gx + dx, 1.2 + h * 0.62 + 0.4, zz + gz + dz, 0.5, 0.8, 0.12, GOLD)
        elif glyph == 1:
            bone(p, (x - 0.9, 1.2 + h * 0.6, zz + 0.95), (x + 0.9, 1.2 + h * 0.6, zz + 0.95), 0.18, GOLD, kr=0.32, spread=0.3, off=(0, 1, 0))
        else:
            for k in range(3):
                cb(p, (x, 1.2 + h * 0.75 - k * 0.9, zz + oz + 0.2), (1.6 - 0.3 * k, 0.28, 0.12), GOLD, 0.02, rot=(0, rot, 0))
    tablet(-52, 9, 4.6, z, 12, 1)
    tablet(-47, 12, 5.4, z, 0, 0)
    tablet(-42, 8, 4.2, z - 1, -14, 2)
    bx(p, (-50, -44), (13.0, 13.8), (z - 0.9, z + 0.9), GOLD, 0.03)
    for x in (-53.5, -41):
        xcyl(p, x - 0.2, x + 0.2, 1.5, z + 2.4, 0.7, GOLD, verts=10)
    bone(p, (-48.5, 1.5, z + 2.4), (-45.5, 1.5, z + 2.4), 0.2, BONE, kr=0.35, spread=0.3, off=(0, 0, 1))
    ball(p, (-47, 14.0, z), 0.5, LGOLD, subdiv=1)


# ---- 18. Throne --------------------------------------------------------------------------------------------------------
@part("Throne")
def build_Throne(p):
    z = -48.5
    bx(p, (12.5, 27.5), (0, 1.2), (z - 6, z + 6), STONE, 0.04)
    bx(p, (14, 26), (1.2, 2.4), (z - 4.7, z + 4.7), MARBLE, 0.03)
    bx(p, (14.0, 16.5), (2.4, 3.2), (z - 2.2, z + 2.2), MARBLE, 0.03)  # step in front of the seat
    bx(p, (16.5, 23.5), (2.4, 6.0), (z - 3, z + 3), GOLD, 0.03)
    bx(p, (16.2, 23.8), (5.6, 6.0), (z - 3.3, z + 3.3), DGOLD, 0.03)
    bx(p, (16.6, 22.0), (6.0, 6.9), (z - 2.4, z + 2.4), RED, 0.03)
    for s in (-1, 1):
        bx(p, (16.5, 23.5), (6.0, 7.2), (z + s * 3.0 - 0.7, z + s * 3.0 + 0.7), DGOLD, 0.03)
        ball(p, (16.4, 7.4, z + s * 3.0), 0.8, GOLD, subdiv=1)
        bone(p, (17.5, 7.9, z + s * 3.0), (22.5, 7.9, z + s * 3.0), 0.2, LGOLD, kr=0.38, spread=0.32, off=(0, 0, 1))
    bx(p, (22, 24), (3, 17.5), (z - 4, z + 4), GOLD, 0.03)
    bx(p, (21.6, 22.0), (7, 16.5), (z - 3.2, z + 3.2), RED, 0.03)
    for s in (-1, 1):
        bx(p, (21.8, 24.2), (6, 16), (z + s * 4.0 - 0.3, z + s * 4.0 + 0.3), DGOLD, 0.03)
        ear(p, 23, 17.5, z + s * 2.2, 1.7, 3.6, 1.6, GOLD, lean=0)
        ear(p, 22.7, 17.6, z + s * 2.2, 0.8, 2.4, 0.5, PINK, lean=0)
    ball(p, (21.5, 15.4, z), 1.0, LAPIS, subdiv=1)
    ball(p, (21.3, 12.2, z), 0.7, LAPIS, subdiv=1)
    for sy in (9.5, 12.8):
        ball(p, (21.45, sy, z), 0.4, LGOLD, subdiv=1)


# ---- 19. AltarTable ----------------------------------------------------------------------------------------------------
@part("AltarTable")
def build_AltarTable(p):
    z = 16
    bx(p, (-31, -17), (2.8, 4.0), (z - 3, z + 3), MARBLE, 0.03)
    bx(p, (-31.2, -16.8), (2.5, 2.8), (z - 3.2, z + 3.2), GOLD, 0.03)
    bx(p, (-31, -17), (4.0, 4.3), (z - 1.4, z + 1.4), RED, 0.03)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (-24 + sx * 6 - 0.6, -24 + sx * 6 + 0.6), (0, 2.8), (z + sz * 2 - 0.6, z + sz * 2 + 0.6), DGOLD, 0.03)
            ball(p, (-24 + sx * 6, 2.8, z + sz * 2), 0.5, GOLD, subdiv=1)
    vcyl(p, -28, 4.3, 5.5, z, 1.6, GOLD, verts=10, top_r=1.8)
    ball(p, (-28, 5.5, z), 1.4, PALE, scale=(1, 0.4, 1), subdiv=1)
    vcyl(p, -24, 4.3, 6.4, z, 1.7, CREAM, verts=12)
    vcyl(p, -24, 6.2, 6.6, z, 1.75, PINK, verts=12)
    ball(p, (-24, 7.1, z), 0.7, RED, subdiv=1)
    for sx in (-1, 1):
        x = -24 + sx * 5.4
        vcyl(p, x, 4.3, 5.0, z, 0.8, GOLD, verts=8, top_r=0.4)
        vcyl(p, x, 5.0, 8.1, z, 0.25, GOLD, verts=6)
        vcyl(p, x, 7.4, 8.1, z, 0.6, DGOLD, verts=8)
        flame(p, x, 8.1, z, 0.55)
    bone(p, (-21.5, 4.5, z + 1.9), (-19.0, 4.5, z + 1.9), 0.18, BONE, kr=0.3, spread=0.28, off=(0, 0, 1))
    bone(p, (-28.5, 4.5, z + 1.9), (-26.5, 4.5, z + 1.9), 0.18, BONE, kr=0.3, spread=0.28, off=(0, 0, 1))
    for zz in (11.4, 20.6):
        bx(p, (-30.5, -17.5), (1.2, 2.0), (zz - 0.9, zz + 0.9), MARBLE, 0.03)
        for sx in (-1, 1):
            bx(p, (-24 + sx * 5.6 - 0.5, -24 + sx * 5.6 + 0.5), (0, 1.2), (zz - 0.8, zz + 0.8), DGOLD, 0.03)
        bx(p, (-30.5, -17.5), (2.0, 2.15), (zz - 0.6, zz + 0.6), RED, 0.03)


# ---- 20. Kennel --------------------------------------------------------------------------------------------------------
@part("Kennel")
def build_Kennel(p):
    cx, cz = 62, -22
    bx(p, (cx - 6, cx + 6), (0, 0.8), (cz - 6, cz + 6), DWOOD, 0.04)
    bx(p, (cx - 5, cx + 5), (0.8, 8.8), (cz - 5, cz + 5), WOOD, 0.04)
    for i in range(10):                      # planks
        c = LWOOD if i % 2 else WOOD
        bx(p, (cx - 5.05, cx - 4.95), (0.8, 8.8), (cz - 5 + i, cz - 4.1 + i), c, 0.04)
        bx(p, (cx + 4.95, cx + 5.05), (0.8, 8.8), (cz - 5 + i, cz - 4.1 + i), c, 0.04)
    # roof: gable with ridge along x
    dk.prism(p, (cx, 8.7, cz), 12.8, 12.6, 4.6, GOLD, ridge='x', jitter=0.03)
    bx(p, (cx - 6.4, cx + 6.4), (13.1, 13.5), (cz - 0.5, cz + 0.5), DGOLD, 0.03)
    for s in (-1, 1):
        bx(p, (cx - 6.6, cx - 6.3), (8.6, 9.0), (cz + s * 6.4 - 0.1, cz + s * 6.4 + 0.1), DGOLD, 0.02)
        ear(p, cx - 6.0, 13.0, cz, 1.0, 1.2, 1.0, LGOLD) if s == 1 else None
    # doorway on the -x side (facing the Shiba)
    x0 = cx - 5.0
    bx(p, (x0 - 0.35, x0), (0.8, 6.8), (cz - 2.7, cz + 2.7), GOLD, 0.03)
    bx(p, (x0 - 0.45, x0 - 0.05), (0.8, 5.8), (cz - 2.1, cz + 2.1), DSTONE, 0.03)
    ball(p, (x0 - 0.3, 5.8, cz), 2.1, DSTONE, scale=(0.18, 0.9, 1.0), subdiv=1)
    bx(p, (x0 - 0.55, x0 - 0.2), (7.0, 8.4), (cz - 2.5, cz + 2.5), CREAM, 0.03)
    bone(p, (x0 - 0.6, 7.7, cz - 1.5), (x0 - 0.6, 7.7, cz + 1.5), 0.2, GOLD, kr=0.36, spread=0.3, off=(0, 1, 0))
    # food bowl with kibble, and a bone
    vcyl(p, 53.5, 0, 1.4, -17, 1.2, GOLD, verts=12, top_r=1.7)
    vcyl(p, 53.5, 1.3, 1.45, -17, 1.5, DGOLD, verts=12)
    for k in range(5):
        ball(p, (53.5 + 0.6 * math.cos(k * 1.3), 1.55, -17 + 0.6 * math.sin(k * 1.3)), 0.4, WOOD, subdiv=1)
    bone(p, (50.95, 0.6, -20), (54.05, 0.6, -20), 0.35, BONE, kr=0.55, spread=0.5, off=(0, 0, 1))
    bx(p, (cx - 2, cx + 2), (0.8, 1.0), (cz + 5.0, cz + 6.0), RED, 0.03)


# ---- 21. Bells ---------------------------------------------------------------------------------------------------------
def bell(p, x, y_top, z, r, h, col=GOLD):
    vcyl(p, x, y_top - h, y_top - h * 0.12, z, r, col, verts=12, top_r=r * 0.62)
    vcyl(p, x, y_top - h, y_top - h + 0.4, z, r * 1.08, DGOLD, verts=12)
    dome(p, x, y_top - h * 0.12, z, r * 0.62, h * 0.12 + 0.2, col, seg=12, rings=2)
    ball(p, (x, y_top - h * 0.4 + 0.2, z + r * 0.55), r * 0.22, LGOLD, subdiv=1)
    ball(p, (x, y_top - h - 0.1, z), r * 0.28, DGOLD, subdiv=1)


@part("Bells")
def build_Bells(p):
    z = 4
    bx(p, (-36.5, -19.5), (0, 1), (z - 2.5, z + 2.5), STONE, 0.04)
    bx(p, (-35.5, -20.5), (1, 1.4), (z - 2.0, z + 2.0), LSTONE, 0.03)
    for x in (-34, -22):
        vcyl(p, x, 1.4, 15.4, z, 0.8, RED, verts=10)
        vcyl(p, x, 1.4, 2.3, z, 1.1, GOLD, verts=10)
        vcyl(p, x, 13.8, 14.4, z, 1.05, GOLD, verts=10)
    bx(p, (-35.5, -20.5), (14.4, 16.0), (z - 0.9, z + 0.9), RED, 0.03)
    for x in (-35.6, -20.4):
        ball(p, (x, 15.2, z), 1.1, GOLD, subdiv=1)
    for x in (-31, -28, -25):
        bx(p, (x - 0.3, x + 0.3), (14.4, 15.0), (z - 0.4, z + 0.4), DGOLD, 0.02)
    # upturned golden roof
    dk.prism(p, (-28, 16.0, z), 18.4, 5.6, 1.4, GOLD, ridge='x', jitter=0.03)
    bx(p, (-37, -19), (16.0, 16.4), (z - 2.6, z + 2.6), DGOLD, 0.03)
    for sx in (-1, 1):
        ear(p, -28 + sx * 8.2, 16.2, z, 1.4, 1.1, 3.2, GOLD, lean=sx * 0.8)
    bell(p, -31, 12.9, z, 1.7, 4.2)
    bell(p, -28, 13.0, z, 2.2, 5.2, DGOLD)
    bell(p, -25, 12.9, z, 1.7, 4.2)
    for x in (-31, -28, -25):
        rod(p, (x, 14.4, z), (x, 12.8, z), 0.12, RED, verts=4)
    rod(p, (-28, 7.0, z + 0.5), (-28, 3.0, z + 1.2), 0.14, RED, verts=4)
    ball(p, (-28, 2.8, z + 1.3), 0.35, GOLD, subdiv=1)


# ---- 22. Sun -----------------------------------------------------------------------------------------------------------
@part("Sun")
def build_Sun(p):
    cz = -10
    bx(p, (69, 77), (0, 1), (cz - 10, cz + 10), STONE, 0.04)
    bx(p, (69.6, 76.4), (1, 2), (cz - 9.4, cz + 9.4), MARBLE, 0.03)
    bx(p, (71, 75), (2, 6), (cz - 3, cz + 3), MARBLE, 0.03)
    bx(p, (70.6, 75.4), (5.4, 6.0), (cz - 3.4, cz + 3.4), GOLD, 0.03)
    bx(p, (70.6, 75.4), (2, 2.5), (cz - 3.4, cz + 3.4), GOLD, 0.03)
    # rays behind, disc in front
    star_poly(p, (72.2, 15, cz), 'yz', 14.5, 10.0, 0.5, DGOLD, n=12, rot0=90, jit=0.03)
    star_poly(p, (71.8, 15, cz), 'yz', 12.0, 9.6, 0.5, GOLD, n=12, rot0=105, jit=0.03)
    xcyl(p, 70.6, 72.4, 15, cz, 10, GOLD, verts=32)
    xcyl(p, 70.2, 71.2, 15, cz, 8.8, LGOLD, verts=32)
    xcyl(p, 69.9, 70.8, 15, cz, 6.6, CREAM, verts=28)
    xcyl(p, 69.7, 70.5, 15, cz, 4.6, GOLD, verts=24)
    ball(p, (69.8, 15, cz), 2.4, RED, scale=(0.5, 1, 1), subdiv=2)
    for k in range(12):
        a = math.radians(k * 30 + 15)
        cb(p, (70.1, 15 + 7.7 * math.cos(a), cz + 7.7 * math.sin(a)), (0.3, 0.8, 0.8), DGOLD, 0.03, rot=(math.degrees(a), 0, 0))
    for s in (-1, 1):
        bx(p, (71.6, 73.4), (5.6, 8.0), (cz + s * 1.0 - 0.5, cz + s * 1.0 + 0.5), GOLD, 0.03)


# ---- 23. Crown ---------------------------------------------------------------------------------------------------------
@part("Crown")
def build_Crown(p):
    cx, cz = 0, -26
    bx(p, (-5, 5), (0, 1.2), (cz - 5, cz + 5), STONE, 0.04)
    bx(p, (-4.2, 4.2), (1.2, 2), (cz - 4.2, cz + 4.2), MARBLE, 0.03)
    fluted(p, cx, cz, 2, 12, 1.9, MARBLE, CREAM, n=8, verts=12, rib=0.2)
    vcyl(p, cx, 2, 2.8, cz, 2.5, GOLD, verts=12)
    vcyl(p, cx, 11.4, 12.2, cz, 2.5, GOLD, verts=12)
    vcyl(p, cx, 12, 13.2, cz, 2.4, DGOLD, verts=12, top_r=4.3)
    # the crown: band, gems, five points with pearls, red velvet inside
    vcyl(p, cx, 13.2, 15.0, cz, 4.8, GOLD, verts=20)
    vcyl(p, cx, 13.0, 13.4, cz, 5.0, DGOLD, verts=20)
    vcyl(p, cx, 14.8, 15.1, cz, 5.0, DGOLD, verts=20)
    dome(p, cx, 15.0, cz, 3.9, 2.4, RED, seg=14, rings=2)
    for k in range(10):
        a = math.radians(k * 36 + 18)
        cb(p, (cx + 4.85 * math.cos(a), 14.1, cz + 4.85 * math.sin(a)), (0.7, 0.8, 0.7), RED if k % 2 else LAPIS, 0.03, rot=(0, -math.degrees(a), 0))
    for k in range(5):
        a = math.radians(k * 72 + 36)
        x, z = cx + 4.0 * math.cos(a), cz + 4.0 * math.sin(a)
        pyramid(p, x, 15.1, z, 1.1, 4.2, GOLD, top=0.15)
        ball(p, (x, 19.7, z), 0.55, WHITE, subdiv=1)
    ball(p, (cx, 17.0, cz), 1.0, LGOLD, subdiv=1)
    ball(p, (cx, 19.4, cz), 0.8, LAPIS, subdiv=1)


# ---- doge statue (used for Cheems and the Colossus) --------------------------------------------------------------------
def doge(p, ox, oz, s, y0, hk=1.0, gem=False):
    """Seated golden Doge facing -x. Colossus coordinates (centre ox, oz of its base, y=4 = top of the base) times s."""
    def P(x, y, z):
        return (ox + x * s, y0 + (y - 4) * s, oz + z * s)

    def Bx(x0, x1, ya, yb, z0, z1, col, j=0.04):
        bx(p, (ox + x0 * s, ox + x1 * s), (y0 + (ya - 4) * s, y0 + (yb - 4) * s), (oz + z0 * s, oz + z1 * s), col, j)
    ball(p, P(2, 11, 0), 8 * s, GOLD, scale=(1, 1, 0.94), subdiv=1)
    for sz in (-1, 1):
        ball(p, P(1, 8, sz * 6.2), 4.2 * s, GOLD, scale=(1.5, 1.2, 0.8), subdiv=1)
        Bx(-5.5, -1.5, 4, 7, sz * 6.2 - 2.2, sz * 6.2 + 2.2, CREAM)         # hind paws
    Bx(-5, 3.5, 8, 33, -4.6, 4.6, GOLD, 0.05)
    ball(p, P(-1, 19, 0), 6.2 * s, GOLD, scale=(1.0, 1.7, 0.95), subdiv=1)
    ball(p, P(-5.2, 19, 0), 4.8 * s, CREAM, scale=(0.55, 1.6, 0.85), subdiv=1)
    for sz in (-1, 1):                                                       # front legs and paws
        Bx(-7.8, -4.2, 5, 23, sz * 4 - 1.8, sz * 4 + 1.8, GOLD)
        Bx(-10.4, -5.0, 4, 6.8, sz * 4 - 2.2, sz * 4 + 2.2, CREAM)
        for t in (-1, 0, 1):
            Bx(-10.5, -10.3, 4.3, 6.2, sz * 4 + t * 1.3 - 0.12, sz * 4 + t * 1.3 + 0.12, DGOLD, 0.02)
    Bx(-6.2, -1.8, 27.0, 30.4, -7.2, 7.2, RED, 0.03)                       # red collar
    ball(p, P(-6.4, 27.6, 0), 1.3 * s, LGOLD, subdiv=1)
    Bx(-6.6, -6.2, 24.6, 27.2, -0.5, 0.5, GOLD, 0.02)
    ball(p, P(-6.7, 24.2, 0), 1.0 * s, GOLD, scale=(0.4, 1, 1), subdiv=1)
    # head
    ball(p, P(-4, 38, 0), 7.5 * s * hk, GOLD, scale=(1, 0.93, 0.87), subdiv=2)
    for sz in (-1, 1):
        ball(p, P(-7.6, 35.5, sz * 4.4), 3.0 * s * hk, CREAM, subdiv=1)      # cheek fur
    Bx(-14, -7, 33.4, 38.4, -2.9, 2.9, CREAM, 0.03)                          # snoot
    Bx(-13.4, -8, 38.4, 39.0, -2.2, 2.2, CREAM, 0.03)
    Bx(-15.4, -13.8, 36.2, 38.2, -1.3, 1.3, DARK, 0.02)                     # nose
    Bx(-13.6, -7.2, 34.2, 34.6, -2.4, 2.4, DARK, 0.02)                      # smile
    for sz in (-1, 1):
        Bx(-10.9, -9.8, 40.0, 42.4, sz * 3.6 - 0.6, sz * 3.6 + 0.6, DARK, 0.02)      # eyes
        Bx(-11.0, -10.6, 41.3, 42.2, sz * 3.6 - 0.15, sz * 3.6 + 0.2, WHITE, 0.02)   # glint
        cb(p, P(-10.6, 43.6, sz * 3.6), (0.5 * s, 0.5 * s, 1.8 * s), DGOLD, 0.02, rot=(sz * 14, 0, 0))   # brows
        ear(p, ox + 0 * s, y0 + (44 - 4) * s, oz + sz * 5.6 * s, 3.4 * s, 7.5 * s, 3.0 * s, DGOLD, lean=sz * 0.5 * s)
        ear(p, ox - 1.3 * s, y0 + (44.5 - 4) * s, oz + sz * 5.6 * s, 1.4 * s, 5.2 * s, 1.4 * s, PINK, lean=sz * 0.3 * s)
    Bx(-11, -10, 40.5, 46, -0.7, 0.7, CREAM, 0.03)                           # blaze
    # tail curling up behind
    ball(p, P(11, 9, 0), 3.0 * s, GOLD, scale=(0.9, 1.7, 1.2), subdiv=1)
    ball(p, P(12.4, 16, 0), 2.6 * s, GOLD, scale=(0.9, 1.3, 1.0), subdiv=1)
    ball(p, P(11.5, 20.6, 0), 1.6 * s, CREAM, subdiv=1)
    # back ridge
    for k in range(3):
        cb(p, P(4.6, 16 + k * 6.4, 0), (0.7 * s, 1.6 * s, 2.0 * s), DGOLD, 0.03)


@part("Cheems")
def build_Cheems(p):
    bx(p, (32, 44), (0, 1.2), (-52, -40), STONE, 0.04)
    bx(p, (33, 43), (1.2, 2.0), (-51, -41), MARBLE, 0.03)
    bx(p, (33.4, 42.6), (2.0, 2.2), (-50.6, -41.4), GOLD, 0.03)
    doge(p, 38.5, -46, 0.43, 2.2, hk=1.12)


# ---- 25. AltarSteps ----------------------------------------------------------------------------------------------------
@part("AltarSteps")
def build_AltarSteps(p):
    cx, cz = -35, -50
    tiers = [(0, 2.4, 9, 5.5, MARBLE), (2.8, 6.0, 7, 4.4, WHITE), (6.4, 9.6, 5, 3.3, MARBLE)]
    for i, (y0, y1, hx, hz, col) in enumerate(tiers):
        bx(p, (cx - hx, cx + hx), (y0, y1), (cz - hz, cz + hz), col, 0.03)
        gy = y1
        bx(p, (cx - hx - 0.4, cx + hx + 0.4), (gy, gy + 0.4), (cz - hz - 0.4, cz + hz + 0.4), GOLD, 0.03)
        for k in range(int(hx)):                       # gold inlay stripes on the riser
            bx(p, (cx - hx + 1.0 + k * 2.0, cx - hx + 1.4 + k * 2.0), (y0 + 0.4, y1 - 0.3), (cz + hz, cz + hz + 0.06), DGOLD, 0.02)
    # front stair with a red runner
    bx(p, (cx - 4, cx + 4), (0, 0.8), (cz + 5.5, cz + 8.3), MARBLE, 0.03)
    bx(p, (cx - 4, cx + 4), (0, 1.6), (cz + 5.5, cz + 6.9), WHITE, 0.03)
    bx(p, (cx - 1.4, cx + 1.4), (0.8, 0.9), (cz + 5.5, cz + 8.3), RED, 0.03)
    # altar block, gold top and a bone relief
    bx(p, (cx - 3, cx + 3), (10, 14), (cz - 2, cz + 2), CREAM, 0.03)
    bx(p, (cx - 3.5, cx + 3.5), (14, 14.6), (cz - 2.5, cz + 2.5), GOLD, 0.03)
    bx(p, (cx - 3.2, cx + 3.2), (10, 10.5), (cz - 2.2, cz + 2.2), GOLD, 0.03)
    bone(p, (cx - 1.3, 12.1, cz + 2.1), (cx + 1.3, 12.1, cz + 2.1), 0.22, GOLD, kr=0.4, spread=0.35, off=(0, 1, 0))
    ball(p, (cx, 15.2, cz), 0.8, LGOLD, subdiv=1)
    # fire bowls
    for s in (-1, 1):
        x, z = cx + s * 4.2, cz + 2.4
        vcyl(p, x, 9.6, 11.0, z, 0.7, DGOLD, verts=8)
        vcyl(p, x, 11.0, 12.0, z, 1.0, GOLD, verts=10, top_r=1.35)
        flame(p, x, 12.0, z, 0.8)
        x2 = cx + s * 6.2
        vcyl(p, x2, 6.0, 6.8, cz + 3.0, 0.5, GOLD, verts=8)
        flame(p, x2, 6.8, cz + 3.0, 0.5)


# ---- 26. HaloArch ------------------------------------------------------------------------------------------------------
@part("HaloArch")
def build_HaloArch(p):
    cx, cz = 67, 27
    for s in (-1, 1):
        x = cx + s * 9
        bx(p, (x - 2.2, x + 2.2), (0, 2.4), (cz - 2, cz + 2), STONE, 0.04)
        bx(p, (x - 1.8, x + 1.8), (2.4, 3.0), (cz - 1.6, cz + 1.6), GOLD, 0.03)
        fluted(p, x, cz, 3.0, 19.0, 1.3, MARBLE, CREAM, n=8, verts=12, rib=0.16)
        vcyl(p, x, 18.6, 19.4, cz, 1.7, GOLD, verts=12)
        bx(p, (x - 1.7, x + 1.7), (19.4, 20.2), (cz - 1.7, cz + 1.7), GOLD, 0.03)
        ear(p, x, 20.2, cz, 1.4, 1.0, 1.2, LGOLD)
    ring(p, (cx, 19.5, cz), 9.0, 0.9, GOLD, axis='z', segs=28, sides=6)
    ring(p, (cx, 19.5, cz), 7.4, 0.4, LGOLD, axis='z', segs=24, sides=4)
    for k in range(16):                      # light rays pointing outward from the ring
        a = math.radians(k * 22.5 + 11)
        r_ = 10.1
        if k % 4 == 3:
            continue
        x, y = cx + r_ * math.cos(a), 19.5 + r_ * math.sin(a)
        if y + 0.6 > 29.4:
            continue
        cb(p, (x, y, cz), (0.5, 0.9, 0.5), LGOLD, 0.03, rot=(0, 0, math.degrees(a) - 90))
    for k, c in enumerate((RED, LAPIS, RED, LAPIS)):
        a = math.radians(k * 90 + 45)
        ball(p, (cx + 9 * math.cos(a), 19.5 + 9 * math.sin(a), cz + 1.0), 0.65, c, subdiv=1)
    ball(p, (cx, 28.4, cz + 0.4), 0.8, WHITE, subdiv=1)


# ---- 27. Vault ---------------------------------------------------------------------------------------------------------
@part("Vault")
def build_Vault(p):
    cx, cz = -71, 28
    bx(p, (cx - 6, cx + 6), (0, 12), (cz - 5, cz + 5), STONE, 0.05)
    for k in range(6):                       # brick courses
        y = 1.6 + k * 2.0
        bx(p, (cx - 6.05, cx + 6.05), (y, y + 0.14), (cz - 5.05, cz + 5.05), DSTONE, 0.02)
    bx(p, (cx - 7, cx + 7), (12, 13.6), (cz - 6, cz + 6), DGOLD, 0.03)
    dk.prism(p, (cx, 13.6, cz), 12.6, 11.0, 2.4, GOLD, ridge='x', jitter=0.03)
    for s in (-1, 1):
        ear(p, cx + s * 6.2, 13.6, cz - 5.4, 1.5, 2.2, 1.4, GOLD, lean=s * 0.3)
        ear(p, cx + s * 6.2, 13.6, cz + 5.4, 1.5, 2.2, 1.4, GOLD, lean=s * 0.3)
    ball(p, (cx, 15.0, cz), 1.5, GOLD, subdiv=1)
    # the round vault door on the +x face
    fx = cx + 6
    bx(p, (fx, fx + 0.8), (0.6, 9.0), (cz - 3.3, cz + 3.3), DSTONE, 0.03)
    xcyl(p, fx + 0.8, fx + 1.2, 4.6, cz, 3.0, GOLD, verts=20)
    xcyl(p, fx + 1.2, fx + 1.5, 4.6, cz, 2.3, DGOLD, verts=16)
    xcyl(p, fx + 1.5, fx + 1.9, 4.6, cz, 0.7, LGOLD, verts=10)
    for k in range(4):
        a = math.radians(k * 45)
        cb(p, (fx + 1.6, 4.6, cz), (0.2, 4.4, 0.3), LGOLD, 0.02, rot=(math.degrees(a), 0, 0))
    for s in (-1, 1):
        fluted(p, fx - 0.6 + 0.0, cz + s * 3.4, 0.0, 10.0, 0.8, MARBLE, CREAM, n=6, verts=10, rib=0.12)
    # coins and bars in front
    coin_heap(p, -63, 24, 1.5, 4, y0=0.0, th=0.5, verts=10, seed=4)
    coin_heap(p, -62, 32, 1.5, 4, y0=0.0, th=0.5, verts=10, seed=5)
    for k in range(3):
        cb(p, (-62.4 + k * 0.0, 0.5 + k * 0.6, 28 + 0.3 * k), (1.8 - 0.2 * k, 0.55, 0.9), LGOLD, 0.03)
    for s in (-1, 1):
        ball(p, (-62.5, 0.9, 28 + s * 2.0), 0.9, DSAND, scale=(1, 1.1, 1), subdiv=1)


# ---- 28. WishTree ------------------------------------------------------------------------------------------------------
@part("WishTree")
def build_WishTree(p):
    cx, cz = -43, 49.5
    vcyl(p, cx, 0, 10, cz, 1.8, WOOD, verts=10, top_r=1.2)
    vcyl(p, cx, 3.0, 3.6, cz, 1.95, RED, verts=10)
    vcyl(p, cx, 3.6, 4.0, cz, 1.9, GOLD, verts=10)
    for k in range(5):
        a = math.radians(k * 72 + 10)
        rod(p, (cx + 1.5 * math.cos(a), 0.2, cz + 1.5 * math.sin(a)), (cx + 3.2 * math.cos(a), 0.0, cz + 3.2 * math.sin(a)), 0.6, DWOOD, verts=6, r2=0.25)
    rod(p, (cx, 8, cz), (cx - 3.5, 12.5, cz), 0.5, WOOD, verts=6)
    rod(p, (cx, 8, cz), (cx + 3.5, 12.5, cz), 0.5, WOOD, verts=6)
    ball(p, (cx, 14, cz), 7, PINK, scale=(1, 0.57, 0.93), subdiv=2)
    for (dx, dy, dz, r, c) in ((5, -1.5, 2, 3.0, LPINK), (-5, -1.5, -2, 3.0, LPINK), (-2, 1.8, 3, 2.6, PINK), (3, 2.0, -3, 2.4, LPINK),
                              (-6, 0, 3, 2.4, PINK), (0, -2, -4.5, 2.6, LPINK), (4, -2.2, 4, 2.2, PINK)):
        ball(p, (cx + dx, 14 + dy, cz + dz), r, c, subdiv=1)
    for k in range(14):                      # blossoms on the canopy
        a = k * 2.4
        ball(p, (cx + 6.2 * math.cos(a) * (0.5 + 0.5 * ((k * 7) % 5) / 4), 14 + 3.4 * math.sin(a * 1.7), cz + 5.6 * math.sin(a) * 0.8),
             0.55, WHITE if k % 3 == 0 else LPINK, subdiv=1)
    ribs = ((6, 8.6, -3, RED), (2.5, 8.8, 6, GOLD), (-4, 9.0, -5, RED), (-6, 9.2, 3, GOLD), (0, 9.1, -6, GOLD), (4, 9.3, 2.5, RED))
    for (dx, y, dz, c) in ribs:
        bx(p, (cx + dx - 0.35, cx + dx + 0.35), (y - 0.2, y + 3.2), (cz + dz - 0.06, cz + dz + 0.06), c, 0.03)
        bx(p, (cx + dx - 0.35, cx + dx + 0.35), (y - 0.2, y + 0.1), (cz + dz - 0.1, cz + dz + 0.1), DGOLD, 0.03)
        rod(p, (cx + dx * 0.9, y + 3.2, cz + dz * 0.9), (cx + dx, y + 3.2, cz + dz), 0.08, DWOOD, verts=4)
        cb(p, (cx + dx, y - 0.8, cz + dz), (0.7, 0.9, 0.06), CREAM, 0.03)
    for k, (dx, dz) in enumerate(((4, 0), (-4, 1), (0, -4))):
        cb(p, (cx + dx * 1.2, 0.25, cz + dz * 1.2 + 3.5), (1.2, 0.5, 1.0), STONE, 0.05, rot=(0, 30 * k, 0))
    for k in range(7):
        a = math.radians(k * 51)
        ball(p, (cx + 5 * math.cos(a), 0.15, cz + 5.5 * math.sin(a)), 0.4, LPINK, subdiv=1)


# ---- 29. HolyLight -----------------------------------------------------------------------------------------------------
@part("HolyLight")
def build_HolyLight(p):
    cx, cz = 14, 36
    vcyl(p, cx, 0, 1.2, cz, 5, MARBLE, verts=20)
    vcyl(p, cx, 1.2, 1.6, cz, 4.0, GOLD, verts=20)
    vcyl(p, cx, 1.6, 2.8, cz, 3.0, CREAM, verts=16, top_r=2.6)
    star_poly(p, (cx, 2.9, cz), 'xz', 4.9, 2.6, 0.1, LGOLD, n=8, rot0=90, jit=0.02)
    # the column of light: a bright core and two crossing blades of pale gold that narrow toward the sky
    vcyl(p, cx, 2.8, 4.0, cz, 2.4, PALE, verts=16, top_r=1.5)
    vcyl(p, cx, 4.0, 30.4, cz, 1.5, GLOW, verts=12, top_r=0.8)
    vcyl(p, cx, 30.4, 32.0, cz, 0.8, GLOW, verts=12, top_r=0.15)
    for (wx, wz) in ((1, 0), (0, 1), (0.7071, 0.7071), (0.7071, -0.7071)):
        for (y0, y1, w0, w1, col) in ((2.8, 12.0, 4.6, 3.4, PALE), (12.0, 22.0, 3.4, 2.4, LGOLD), (22.0, 31.0, 2.4, 0.4, PALE)):
            pts = [(cx - wx * w0 - wz * 0.12, y0, cz - wz * w0 - wx * 0.12), (cx + wx * w0 - wz * 0.12, y0, cz + wz * w0 - wx * 0.12),
                   (cx + wx * w1 - wz * 0.12, y1, cz + wz * w1 - wx * 0.12), (cx - wx * w1 - wz * 0.12, y1, cz - wz * w1 - wx * 0.12),
                   (cx - wx * w0 + wz * 0.12, y0, cz - wz * w0 + wx * 0.12), (cx + wx * w0 + wz * 0.12, y0, cz + wz * w0 + wx * 0.12),
                   (cx + wx * w1 + wz * 0.12, y1, cz + wz * w1 + wx * 0.12), (cx - wx * w1 + wz * 0.12, y1, cz - wz * w1 + wx * 0.12)]
            dk.poly(p, (0, 0, 0), pts, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], col, 0.02)
    for y, r in ((10, 4.5), (18, 3.5), (26, 2.7)):
        ring(p, (cx, y, cz), r, 0.28, GOLD, axis='y', segs=14, sides=4)
        for k in range(5):
            a = math.radians(k * 72 + y * 7)
            ball(p, (cx + r * math.cos(a), y, cz + r * math.sin(a)), 0.42, LGOLD, subdiv=1)
    star_poly(p, (cx, 31.5, cz), 'xy', 1.7, 0.6, 0.2, WHITE, n=4, rot0=90, jit=0.02)
    star_poly(p, (cx, 31.5, cz), 'yz', 1.7, 0.6, 0.2, WHITE, n=4, rot0=90, jit=0.02)
    ball(p, (cx, 31.5, cz), 0.9, WHITE, subdiv=1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cb(p, (cx + sx * 3.8, 21 + 0.8 * sx * sz, cz + sz * 3.8), (0.9, 2.4, 0.9), LGOLD, 0.03, rot=(0, 45, 0))
    for k in range(8):                      # motes of light spiralling up
        a = math.radians(k * 137)
        cb(p, (cx + 3.0 * math.cos(a), 4 + k * 3.2, cz + 3.0 * math.sin(a)), (0.4, 0.4, 0.4), GLOW, 0.02, rot=(0, 45, 45))


# ---- 30. Colossus ------------------------------------------------------------------------------------------------------
@part("Colossus")
def build_Colossus(p):
    cx, cz = 60, -43
    bx(p, (cx - 11, cx + 11), (0, 2), (cz - 10, cz + 10), STONE, 0.04)
    bx(p, (cx - 9, cx + 9), (2, 4), (cz - 8, cz + 8), MARBLE, 0.03)
    bx(p, (cx - 9.4, cx + 9.4), (3.7, 4.0), (cz - 8.4, cz + 8.4), GOLD, 0.03)
    doge(p, cx, cz, 1.0, 4.0, hk=1.0)
    # halo and sun rays behind the head
    ring(p, (cx + 5.5, 38, cz), 9.2, 0.55, GOLD, axis='x', segs=24, sides=6)
    star_poly(p, (cx + 7, 38, cz), 'yz', 10.2, 8.0, 0.5, LGOLD, n=12, rot0=90, jit=0.03)
    # golden bones at the pedestal corners
    for sx in (-1, 1):
        for sz in (-1, 1):
            bone(p, (cx + sx * 9.8, 4.0, cz + sz * 7.4), (cx + sx * 9.8, 9.0, cz + sz * 7.4), 0.6, GOLD, kr=0.9, spread=0.7, off=(0, 0, 1), kcol=LGOLD)
# ==== MAIN ====
MISSING = []
AZ = {"Wall": 110, "Sun": 100, "Throne": 100, "Cheems": 100, "Colossus": 110, "Kennel": 110, "Vault": 250, "Hall": 160}
ELEV = {}
MULT = {"Ground": 1.9, "Colossus": 3.0, "Hall": 2.0, "HolyLight": 2.6, "HaloArch": 2.4}
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_DogeAltar.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        os.remove(os.path.join(OUT, f))


main()
