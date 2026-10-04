"""Final low-poly decor models for the theme HellGate (30 parts around the 26th Shiba, Demon Shiba).

Usage: blender --background --factory-startup --python build_HellGate.py -- <outdir> [PartId,PartId,...]
Writes Decor_HellGate_<PartId>.fbx, preview_<PartId>.png and stage_HellGate.png into <outdir>.
Every model is built around the origin in the numbers of DecorTheme26.luau (shifted parts included) and then fitted to the union
box of its blueprint pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it). Give part
ids (comma separated) after the out folder to rebuild only those parts (no stage render then). `--boxes` prints the union boxes.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "HellGate"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "HellGate"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_HellGate.json"))

# ---- palette (black obsidian, red rock, lava orange, bone white, iron grey, a few accents) ------------------------------------
OBS = (34, 30, 40)
BLK = (22, 20, 26)
ROCK = (62, 54, 60)
LROCK = (88, 78, 84)
RROCK = (112, 40, 40)
DRED = (74, 22, 28)
RED = (178, 38, 38)
LRED = (214, 62, 48)
LAVA = (255, 104, 28)
LAVAY = (255, 178, 54)
BONE = (232, 222, 196)
DBONE = (190, 178, 150)
IRON = (88, 90, 102)
LIRON = (130, 132, 146)
ASH = (116, 112, 118)
SULF = (214, 196, 72)
GREEN = (112, 186, 72)
WOOD = (74, 52, 40)
PURP = (100, 40, 88)
LPURP = (140, 66, 120)
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



def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)



# ---- helpers for this theme -----------------------------------------------------------------------------------------------
import random
_R = random.Random(26)


def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)


def ryv(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


def tube(p, a, b, r0, r1, col, verts=6, jit=0.04):
    """Tapered round bar between two stage points (radius r0 at a, r1 at b), closed ends."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    v = d.cross(u).normalized()
    pts = []
    for q, r in ((a, r0), (b, r1)):
        for k in range(verts):
            t = 2 * math.pi * k / verts
            pts.append(tuple(q + (u * math.cos(t) + v * math.sin(t)) * r))
    faces = [(k, (k + 1) % verts, verts + (k + 1) % verts, verts + k) for k in range(verts)]
    faces.append(tuple(range(verts)))
    faces.append(tuple(range(2 * verts - 1, verts - 1, -1)))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def chain_path(p, pts, r0, col, verts=5, tip=0.07, jit=0.03):
    """A bent, tapering horn / branch / claw: a tube per segment of the point list (radius r0 at the start, tip at the end)."""
    n = len(pts) - 1
    for i in range(n):
        ra = max(tip, r0 * (1 - i / n))
        rb = max(tip, r0 * (1 - (i + 1) / n))
        tube(p, pts[i], pts[i + 1], ra, rb, col, verts, jit)


def horn(p, base, side, h, curl, r, col=BONE, yaw=0.0, n=4, lean=0.0):
    """Curved horn growing up from base = (x, y, z): side +-1 = outward direction in local x, h = height, curl = how far it bends."""
    x, y, z = base
    pts = []
    for i in range(n + 1):
        t = i / n
        dx = side * curl * (t ** 1.6 + 0.35 * t)
        dy = h * t
        dz = lean * t * t
        ox, oz = ryv(dx, dz, yaw)
        pts.append((x + ox, y + dy, z + oz))
    chain_path(p, pts, r, col, verts=5)


def cone(p, x, y0, z, r, h, col, verts=6, jit=0.05):
    return dk.cone(p, (x, y0, z), r, h, col, verts=verts, jitter=jit)


def skull(p, c, r, yaw=0.0, col=BONE, sub=1, jaw=True, eyes=BLK, glow=None):
    """Skull around centre c (cranium), facing local +z turned by yaw; sub = icosphere detail (1 = 20 tris, 2 = 80 tris)."""
    x, y, z = c

    def at(dx, dy, dz):
        ox, oz = ryv(dx, dz, yaw)
        return (x + ox, y + dy, z + oz)
    dk.ball(p, c, r, col, scale=(0.96, 0.92, 1.0), subdiv=sub, rot=(0, yaw, 0), jitter=0.04)
    if jaw:
        dk.box(p, at(0, -0.88 * r, 0.14 * r), (0.78 * r, 0.46 * r, 0.8 * r), shade(col, 0.94), rot=(0, yaw, 0), jitter=0.03)
    for sx in (-1, 1):
        dk.box(p, at(sx * 0.38 * r, 0.02 * r, 0.9 * r), (0.34 * r, 0.36 * r, 0.22 * r), eyes, rot=(0, yaw, 0), jitter=0.02)
        if glow:
            dk.box(p, at(sx * 0.38 * r, 0.02 * r, 0.99 * r), (0.16 * r, 0.16 * r, 0.1 * r), glow, rot=(0, yaw, 0), jitter=0.02)
    dk.box(p, at(0, -0.3 * r, 0.96 * r), (0.2 * r, 0.3 * r, 0.2 * r), eyes, rot=(0, yaw, 0), jitter=0.02)


def shade(col, f):
    return dk.shade(col, f)


def flame(p, x, y0, z, r, h, cols=(RED, LAVA, LAVAY), tongues=4, spread=0.55, verts=5):
    """Fire made of pointed tongues: a big core cone, lighter inner cones and small tongues round it."""
    cone(p, x, y0, z, r, h, cols[0], verts=verts + 1, jit=0.03)
    cone(p, x, y0, z, r * 0.66, h * 0.86, cols[1], verts=verts, jit=0.03)
    cone(p, x, y0, z, r * 0.34, h * 0.6, cols[2], verts=verts, jit=0.03)
    for k in range(tongues):
        a = 2 * math.pi * k / tongues + 0.5
        tx, tz = x + math.cos(a) * r * spread, z + math.sin(a) * r * spread
        hh = h * (0.5 + 0.18 * ((k * 7) % 3))
        cone(p, tx, y0, tz, r * 0.4, hh, cols[k % 2], verts=4, jit=0.04)


def shard(p, x, y0, z, w, h, col, tilt=(0, 0), verts=6, tip=0.22, jit=0.1):
    """Crystal-like spike: prism up to 0.78 h, then a point; tilt = (dx, dz) lean of the tip."""
    a = (x, y0, z)
    m = (x + tilt[0] * 0.55, y0 + h * 0.74, z + tilt[1] * 0.55)
    t = (x + tilt[0], y0 + h, z + tilt[1])
    tube(p, a, m, w / 2, w * 0.36, col, verts, jit)
    tube(p, m, t, w * 0.36, 0.05, shade(col, 1.12), verts, jit)


def rock(p, c, r, col, squash=0.75, sub=1, seed=None, jit=0.12):
    """Rough boulder: a low icosphere, randomly stretched and turned."""
    rr = random.Random(seed) if seed is not None else _R
    sx, sz = 0.85 + rr.random() * 0.4, 0.85 + rr.random() * 0.4
    return dk.ball(p, c, r, col, scale=(sx, squash, sz), subdiv=sub + 1, rot=(0, rr.random() * 360, 0), jitter=jit)


def frust(p, cx, y0, y1, cz, wb, db, wt, dt, col, jit=0.04):
    """Box that narrows (or widens) from a wb x db base to a wt x dt top."""
    hb, dbh, ht, dth = wb / 2, db / 2, wt / 2, dt / 2
    pts = [(cx - hb, y0, cz - dbh), (cx + hb, y0, cz - dbh), (cx + hb, y0, cz + dbh), (cx - hb, y0, cz + dbh),
           (cx - ht, y1, cz - dth), (cx + ht, y1, cz - dth), (cx + ht, y1, cz + dth), (cx - ht, y1, cz + dth)]
    return hexa(p, pts, col, jit)


def poly_cone(p, cx, y0, y1, cz, rb, col, verts=8, rt=0.0, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), rb, y1 - y0, col, axis='y', verts=verts, top_radius=rt, jitter=jit)


def pyramid(p, cx, y0, cz, w, d, h, col, jit=0.04):
    pts = [(cx - w / 2, y0, cz - d / 2), (cx + w / 2, y0, cz - d / 2), (cx + w / 2, y0, cz + d / 2), (cx - w / 2, y0, cz + d / 2), (cx, y0 + h, cz)]
    faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def link_chain(p, a, b, n, col=IRON, sag=0.0, size=0.55, jit=0.03):
    """Chain of small blocks from a to b with a downward sag (stage points); links alternate their orientation."""
    a, b = Vector(a), Vector(b)
    for i in range(n):
        t = (i + 0.5) / n
        q = a + (b - a) * t
        q.y -= sag * 4 * t * (1 - t)
        t2 = (i + 1.5) / n
        q2 = a + (b - a) * min(t2, 1.0)
        q2.y -= sag * 4 * min(t2, 1.0) * (1 - min(t2, 1.0))
        d = q2 - q
        ang = math.degrees(math.atan2(d.y, math.hypot(d.x, d.z)))
        yaw = math.degrees(math.atan2(-d.z, d.x))
        ln = size * 1.7
        if i % 2 == 0:
            dk.box(p, tuple(q), (ln, size * 0.6, size * 0.35), col, rot=(0, yaw, ang), jitter=jit)
        else:
            dk.box(p, tuple(q), (ln * 0.8, size * 0.35, size * 0.6), col, rot=(0, yaw, ang), jitter=jit)


def ring_xy(p, c, ro, ri, depth, col, segs=16, jit=0.04, a0=0.0, a1=2 * math.pi, rr=None):
    """Flat ring standing in the x-y plane (axis along z), outer radius ro, inner ri, thickness depth."""
    cx, cy, cz = c
    pts, faces = [], []
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    n = segs if full else segs + 1
    for i in range(n):
        a = a0 + (a1 - a0) * i / segs
        co, si = math.cos(a), math.sin(a)
        for (r, z) in ((ro, depth / 2), (ro, -depth / 2), (ri, -depth / 2), (ri, depth / 2)):
            rad = r if rr is None else r * rr(i)
            pts.append((cx + co * rad, cy + si * rad, cz + z))
    last = segs if full else segs - 0
    for i in range(segs):
        j = (i + 1) % n if full else i + 1
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, j * 4 + k, j * 4 + k2, i * 4 + k2))
    if not full:
        faces.append((0, 3, 2, 1))
        e = segs * 4
        faces.append((e, e + 1, e + 2, e + 3))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def spiral(p, c, r0, r1, a0, turns, width, z0, z1, col, n=14, jit=0.04):
    """Ribbon in the x-y plane along an Archimedean spiral (from radius r0 to r1), a swirl arm of a portal."""
    cx, cy, cz = c
    pts, faces = [], []
    for i in range(n + 1):
        t = i / n
        a = a0 + turns * 2 * math.pi * t
        r = r0 + (r1 - r0) * t
        w = width * (1.0 - 0.55 * t)
        for (dr, z) in ((-w / 2, z1), (w / 2, z1), (w / 2, z0), (-w / 2, z0)):
            rad = r + dr
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, cz + z))
    for i in range(n):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, (i + 1) * 4 + k, (i + 1) * 4 + k2, i * 4 + k2))
    faces.append((0, 1, 2, 3))
    e = n * 4
    faces.append((e + 3, e + 2, e + 1, e))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def zigzag(p, pts, w, y0, y1, col, jit=0.05, glow=None, gw=0.45):
    """A crack / stream: flat bars between the stage points (x, z), width w, from y0 to y1; optional lighter glow line on top."""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        dk.box(p, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (L + w * 0.6, y1 - y0, w), col, rot=(0, ang, 0), jitter=jit)
        if glow:
            dk.box(p, ((x0 + x1) / 2, y1 + 0.01, (z0 + z1) / 2), (L + w * 0.3, 0.06, w * gw), glow, rot=(0, ang, 0), jitter=0.03)


def cloth(p, x, ytop, z, w, h, col, teeth=3, wave=0.5, trim=None, jit=0.04, cols=5):
    """Tattered banner hanging down from ytop at (x, z), width w along x, wavy in z, torn into teeth at the bottom."""
    xs = [x - w / 2 + w * i / (cols - 1) for i in range(cols)]
    pts = []
    for i, xx in enumerate(xs):
        zz = z + wave * math.sin(i * 1.3)
        low = h * (0.78 + 0.22 * (1 if (i * teeth // cols) % 2 else 0)) if i not in (0, cols - 1) else h * 0.86
        pts.append((xx, ytop, zz))
        pts.append((xx, ytop - low, zz))
    t = 0.1
    allpts, faces = [], []
    for (xx, yy, zz) in pts:
        allpts.append((xx, yy, zz + t))
    for (xx, yy, zz) in pts:
        allpts.append((xx, yy, zz - t))
    m = len(pts)
    for i in range(cols - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        faces.append((a, b, c, d))
        faces.append((m + d, m + c, m + b, m + a))
        faces.append((a, d, m + d, m + a))
        faces.append((b, m + b, m + c, c))
    faces.append((0, m, m + 1, 1))
    faces.append((m - 2, m - 1, 2 * m - 1, 2 * m - 2))
    dk.poly(p, (0, 0, 0), allpts, faces, col, jit)
    if trim:
        B(p, x, ytop - 0.2, z, w + 0.3, 0.45, 0.4, trim, jit=0.02)


def hexa(p, pts, col, jit=0.04):
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def tri_slab(p, tri, z0, z1, col, jit=0.04):
    """Triangular plate in the x-y plane, thickness z0..z1 (a wing membrane piece)."""
    pts = [(a, b, z0) for a, b in tri] + [(a, b, z1) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def bone(p, a, b, r, col=BONE, knob=1.5, verts=5):
    """A long bone between two points with a knob at each end."""
    tube(p, a, b, r, r, col, verts, 0.04)
    for q in (a, b):
        dk.ball(p, tuple(q), r * knob, col, subdiv=1, jitter=0.04)


def rib(p, cx, cy, cz, R, h, col=BONE, segs=5, thick=0.4, yaw=0.0, side=1):
    """A half-buried rib: an arc (quarter ellipse) of bars standing in a vertical plane turned by yaw."""
    prev = None
    for i in range(segs + 1):
        a = (math.pi / 2) * i / segs
        dx = side * R * (1 - math.cos(a)) * 0.0 + side * R * math.sin(a)
        dy = h * math.cos(a)
        ox, oz = ryv(dx, 0, yaw)
        q = (cx + ox, cy + dy, cz + oz)
        if prev is not None:
            tube(p, prev, q, thick, thick * 0.9, col, 4, 0.04)
        prev = q


# ==== the 30 parts (each built around the centre of its blueprint box, then fitted to it) =====================================
# ---- 1. Ground ------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    rng = random.Random(5)
    bx(p, (-90, 90), (0, 0.3), (-70, 70), OBS, 0.05)
    # tonal obsidian slabs
    for _ in range(26):
        w, d = 7 + rng.random() * 9, 6 + rng.random() * 8
        x, z = -86 + rng.random() * 172, -66 + rng.random() * 132
        bx(p, (x - w / 2, x + w / 2), (0.3, 0.32), (z - d / 2, z + d / 2), rng.choice([BLK, ROCK, BLK, OBS]), 0.08)
    # red-veined rock fields
    for (x, z, w, d, col) in ((-58, 34, 46, 30, RROCK), (60, 30, 40, 36, DRED), (-20, -30, 44, 34, DRED), (26, -52, 52, 30, RROCK),
                              (-70, -48, 30, 24, DRED), (70, -34, 30, 22, RROCK)):
        bx(p, (x - w / 2, x + w / 2), (0.3, 0.34), (z - d / 2, z + d / 2), col, 0.07)
        bx(p, (x - w * 0.3, x + w * 0.3), (0.34, 0.36), (z - d * 0.3, z + d * 0.3), shade(col, 0.8), 0.08)
    # glowing lava cracks
    for pts in (((-60, -50), (-52, -47), (-44, -52), (-36, -49), (-28, -53), (-20, -50)),
                ((54, 23), (51, 30), (55, 36), (52, 43), (56, 50), (54, 57)),
                ((-72, -11), (-70, -4), (-74, 2), (-71, 9), (-73, 15), (-72, 19)),
                ((23, 8), (30, 6), (36, 10), (42, 7), (49, 9))):
        zigzag(p, pts, 1.7, 0.3, 0.4, LAVA, 0.04, glow=LAVAY)
    # a worn stone trail along the walkway
    path = [(v[0], v[1]) for v in BP["Path"]]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        n = max(1, int(L // 8))
        ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        for k in range(n):
            u = (k + 0.5) / n
            cx, cz = x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
            dk.box(p, (cx, 0.35, cz), (L / n * 0.8, 0.1, 4.8), ROCK if k % 2 else DRED, rot=(0, ang, 0), jitter=0.07)
    # the red-ringed plaza under the Demon Shiba
    bx(p, (7, 33), (0.3, 0.42), (-27, -1), ROCK, 0.04)
    bx(p, (9.5, 30.5), (0.42, 0.5), (-24.5, -3.5), DRED, 0.04)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bx(p, (20 + sx * 11.6 - 0.9, 20 + sx * 11.6 + 0.9), (0.42, 0.6), (-14 + sz * 11.6 - 0.9, -14 + sz * 11.6 + 0.9), BLK, 0.03)
    vcyl(p, 20, 0.5, 0.56, -14, 7.2, LAVA, verts=20, jit=0.02)
    vcyl(p, 20, 0.5, 0.57, -14, 6.5, RED, verts=20, jit=0.02)
    star_poly(p, (20, 0.54, -14), 'xz', 6.6, 2.7, 0.1, LAVA, n=5, rot0=90)
    star_poly(p, (20, 0.56, -14), 'xz', 5.3, 2.2, 0.1, LAVAY, n=5, rot0=90)
    vcyl(p, 20, 0.5, 0.6, -14, 1.4, BLK, verts=10, jit=0.02)
    for k in range(10):
        a = 2 * math.pi * k / 10
        dk.box(p, (20 + 8.4 * math.cos(a), 0.52, -14 + 8.4 * math.sin(a)), (0.7, 0.14, 0.7), BLK, rot=(0, -math.degrees(a), 0), jitter=0.02)


# ---- 2. Braziers ----------------------------------------------------------------------------------------------------------
def brazier_model(p, x, z):
    bx(p, (x - 1.8, x + 1.8), (0, 0.8), (z - 1.8, z + 1.8), ROCK, 0.05)
    bx(p, (x - 1.4, x + 1.4), (0.8, 1.4), (z - 1.4, z + 1.4), LROCK, 0.05)
    vcyl(p, x, 1.4, 7.4, z, 1.15, BLK, verts=8, top_r=0.95)
    for yy in (2.4, 6.2):
        vcyl(p, x, yy, yy + 0.6, z, 1.4, RROCK, verts=8)
    dk.ball(p, (x, 4.3, z + 1.0), 0.5, BONE, scale=(1, 1.1, 0.5), subdiv=1, jitter=0.03)
    vcyl(p, x, 7.4, 8.8, z, 1.2, IRON, verts=10, top_r=2.5)
    vcyl(p, x, 8.7, 9.0, z, 2.7, LIRON, verts=10)
    vcyl(p, x, 8.95, 9.05, z, 2.3, DRED, verts=10)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        cone(p, x + 2.55 * math.cos(a), 8.9, z + 2.55 * math.sin(a), 0.32, 1.7, BLK, verts=4)
    flame(p, x, 9.0, z, 1.95, 3.4)


def build_Braziers(p):
    brazier_model(p, 24, -2)
    brazier_model(p, -24, 2)


# ---- 3. HellSign ----------------------------------------------------------------------------------------------------------
def build_HellSign(p):
    bx(p, (-11, 11), (0, 0.8), (-2, 2), ROCK)
    bx(p, (-10, 10), (0.8, 1.2), (-1.6, 1.6), LROCK)
    for sx in (-1, 1):
        x = sx * 7
        bx(p, (x - 0.7, x + 0.7), (1.2, 10.2), (-0.7, 0.7), BLK)
        for yy in (2.6, 8.6):
            bx(p, (x - 0.95, x + 0.95), (yy, yy + 0.6), (-0.95, 0.95), IRON)
        cone(p, x, 10.2, 0, 0.85, 2.0, IRON, verts=4)
    bx(p, (-10.2, 10.2), (5.4, 11.4), (-0.45, 0.45), BLK)
    bx(p, (-9.3, 9.3), (6.1, 10.7), (0.4, 0.9), RED)
    text(p, "HELL", 0, 6.8, 0.9, 1.5, 3.4, 3.2, 0.8, 1.0, BONE)
    for sx in (-1, 1):
        for yy in (5.9, 10.9):
            dk.ball(p, (sx * 9.7, yy, 0.6), 0.45, IRON, subdiv=1)
        horn(p, (sx * 9.6, 11.4, 0), sx, 3.2, 2.2, 0.75, BONE, n=4)
    skull(p, (0, 12.9, 0), 1.5, sub=2)


# ---- 4. SpikeFence --------------------------------------------------------------------------------------------------------
def build_SpikeFence(p):
    bx(p, (-21.5, 21.5), (0, 0.8), (-1.5, 1.5), ROCK)
    for sx in (-1, 1):
        x = sx * 20
        bx(p, (x - 1.5, x + 1.5), (0.8, 8), (-1.5, 1.5), ROCK)
        bx(p, (x - 1.5, x + 1.5), (8, 8.6), (-1.5, 1.5), RROCK)
        bx(p, (x - 1.5, x + 1.5), (2.4, 3.0), (-1.5, 1.5), RROCK)
        skull(p, (x, 9.6, 0), 1.0, sub=1, yaw=0)
    bx(p, (-18.5, 18.5), (1.6, 2.2), (-0.3, 0.3), IRON)
    bx(p, (-18.5, 18.5), (4.4, 5.0), (-0.3, 0.3), IRON)
    for i in range(21):
        x = -18 + 1.8 * i
        top = 7.2 if i % 2 == 0 else 6.4
        bx(p, (x - 0.25, x + 0.25), (0.8, top), (-0.25, 0.25), BLK, 0.03)
        cone(p, x, top, 0, 0.5, 1.5, IRON, verts=4)


# ---- 5. BoneHeap ----------------------------------------------------------------------------------------------------------
def build_BoneHeap(p):
    dk.ball(p, (0, 2.4, 0), 1.0, BONE, scale=(7, 2.5, 6.2), subdiv=2, jitter=0.1)
    dk.ball(p, (1.5, 4.6, 0.4), 1.0, DBONE, scale=(4, 2.0, 3.4), subdiv=2, jitter=0.1)
    for k, (dx, dz, r) in enumerate(((-5.2, -2.2, 1.5), (5.4, 1.8, 1.4), (-1.8, 5.2, 1.6), (3.2, -5.0, 1.4), (-5.8, 2.6, 1.3),
                                     (0.0, -3.2, 1.2), (4.4, 4.4, 1.2))):
        yaw = math.degrees(math.atan2(dx, dz))
        skull(p, (dx, 1.2 + r * 0.7 + (1.4 if abs(dx) < 3 and abs(dz) < 4 else 0), dz), r, yaw=yaw, sub=2 if r > 1.45 else 1)
    # ribcage standing in the mound
    bone(p, (-3.6, 4.4, -0.8), (2.0, 4.8, -0.8), 0.32, DBONE)
    for i in range(5):
        x = -3.0 + i * 1.3
        for side in (-1, 1):
            rib(p, x, 4.5, -0.8, 2.8 - abs(i - 2) * 0.25, 2.6, BONE, segs=4, thick=0.3, yaw=90, side=side)
    # long bones criss-crossing
    bone(p, (-6.4, 1.0, 3.2), (-1.4, 3.2, 5.6), 0.34)
    bone(p, (1.4, 1.0, 5.8), (6.0, 2.6, 2.0), 0.34)
    bone(p, (-2.4, 1.4, -5.8), (3.0, 1.4, -4.4), 0.3)
    bone(p, (4.8, 1.0, -2.0), (6.6, 1.0, 1.4), 0.3)
    # spear with a skull on top
    tube(p, (0.6, 3.4, 0.2), (0.6, 12.2, 0.2), 0.28, 0.24, IRON, verts=5)
    cone(p, 0.6, 12.0, 0.2, 0.5, 1.2, LIRON, verts=4)
    skull(p, (0.6, 13.4, 0.2), 1.4, sub=2, yaw=20)
    # scattered bones on the ground
    for (x0, z0, x1, z1) in ((-6.8, -3.4, -5.2, -5.6), (6.8, 4.6, 5.4, 6.4), (-4.4, 6.0, -2.4, 6.6)):
        bone(p, (x0, 0.3, z0), (x1, 0.3, z1), 0.26, DBONE)


# ---- 6. LavaPools ---------------------------------------------------------------------------------------------------------
def lava_pool(p, x, z, r, col, rim_n=9):
    vcyl(p, x, 0, 0.5, z, r + 0.9, BLK, verts=12, jit=0.07)
    vcyl(p, x, 0.45, 0.62, z, r, LAVA, verts=12, jit=0.03)
    vcyl(p, x, 0.6, 0.7, z, r * 0.62, col, verts=10, jit=0.03)
    for k in range(rim_n):
        a = 2 * math.pi * k / rim_n + x
        rock(p, (x + (r + 0.8) * math.cos(a), 0.6, z + (r + 0.8) * math.sin(a)), 0.9 + (k % 3) * 0.25, LROCK if k % 2 else ROCK, squash=0.8)
    for k in range(3):
        a = 1.7 * k + z
        dk.ball(p, (x + r * 0.35 * math.cos(a), 0.7, z + r * 0.35 * math.sin(a)), 0.5, LAVAY, scale=(1, 0.5, 1), subdiv=1, jitter=0.03)


def build_LavaPools(p):
    lava_pool(p, -4.1, 5.6, 6.0, LAVAY)
    lava_pool(p, 5.9, -5.4, 4.6, LAVAY)
    lava_pool(p, -9.1, -8.4, 3.6, LAVAY, rim_n=7)
    for (x, z, h, col) in ((-11.1, 11.6, 4.4, ROCK), (1.9, 12.6, 3.8, OBS), (11.9, -1.4, 3.6, ROCK), (-0.1, -12.4, 4.4, OBS)):
        rock(p, (x, h * 0.35, z), h * 0.48, col, squash=0.8, sub=2)
        shard(p, x - 0.6, h * 0.4, z + 0.3, 1.5, h * 0.6, shade(col, 1.4), tilt=(-0.5, 0.3))
        shard(p, x + 0.8, h * 0.3, z - 0.4, 1.2, h * 0.5, shade(col, 1.3), tilt=(0.4, -0.2))


# ---- 7. ObsidianShards ----------------------------------------------------------------------------------------------------
def build_ObsidianShards(p):
    dk.ball(p, (0, 0.4, 0), 1.0, ROCK, scale=(9, 0.8, 7.2), subdiv=2, jitter=0.1)
    for (x, z, w, h, col, tilt) in ((-0.1, -0.8, 3.6, 16, BLK, (1.0, 0.4)), (-5.1, 2.2, 3.0, 12, OBS, (-1.4, 0.8)),
                                    (4.9, 3.2, 3.0, 11, BLK, (1.2, 0.6)), (3.9, -4.8, 3.4, 8, OBS, (1.2, -1.2)),
                                    (-4.1, -4.8, 2.6, 8.4, BLK, (-1.0, -0.8)), (7.9, -0.8, 2.4, 6, RED, (1.0, 0.3)),
                                    (-8.1, -0.8, 2.2, 5.6, RED, (-1.0, 0.4)), (-0.1, 6.2, 2.6, 4.8, BLK, (0.3, 1.3))):
        shard(p, x, 0.3, z, w, h, col, tilt=tilt, jit=0.14)
    for (x, z, h, col) in ((-2.6, 3.8, 3.6, BLK), (2.4, -2.6, 4.4, OBS), (6.0, 4.0, 3.0, OBS), (-6.6, 3.0, 2.6, BLK), (-2.2, -5.8, 3.2, OBS),
                           (1.6, 5.8, 2.4, BLK), (-7.6, -3.4, 2.4, OBS)):
        shard(p, x, 0.3, z, 1.2, h, col, tilt=(0.4 * (1 if x > 0 else -1), 0.3), verts=5, jit=0.14)


# ---- 8. DeadTrees ---------------------------------------------------------------------------------------------------------
def dead_tree(p, x, z, h, lean, yaw):
    def at(dx, dy, dz):
        ox, oz = ryv(dx, dz, yaw)
        return (x + ox, dy, z + oz)
    pts = [at(0, 0, 0), at(lean * 0.2, h * 0.3, 0), at(-lean * 0.1, h * 0.62, 0.2), at(lean * 0.3, h, 0)]
    chain_path(p, pts, 0.95, BLK, verts=6, tip=0.3, jit=0.08)
    for k in range(4):
        a = yaw + 70 * k
        ox, oz = ryv(1.7, 0, a)
        tube(p, at(0, 0.6, 0), (x + ox, 0.0, z + oz), 0.38, 0.2, BLK, 4, 0.06)
    for (t, side, ln, up) in ((0.52, 1, 4.4, 0.8), (0.66, -1, 4.0, 1.0), (0.82, 1, 3.4, 1.2), (0.38, -1, 3.0, 0.5), (0.92, -1, 2.6, 1.0)):
        y0 = h * t
        b0 = at(lean * 0.1, y0, 0)
        mid = at(side * ln * 0.55 + lean * 0.1, y0 + up * ln * 0.3, 0.6)
        end = at(side * ln + lean * 0.1, y0 + up * ln * 0.75, 0.2)
        chain_path(p, [b0, mid, end], 0.42, BLK, verts=4, tip=0.1, jit=0.07)
        tube(p, mid, at(side * ln * 0.8, y0 + up * ln * 0.75, 1.4), 0.2, 0.06, BLK, 4, 0.05)
    dk.ball(p, at(0, 0.2, 0), 2.6, RED, scale=(1, 0.12, 0.8), subdiv=1, jitter=0.04)
    dk.ball(p, at(0.8, 0.28, 0.6), 1.2, LAVA, scale=(1, 0.12, 0.8), subdiv=1, jitter=0.04)
    for yy in (h * 0.2, h * 0.45):
        dk.box(p, at(0.65, yy, 0.3), (0.28, 1.3, 0.25), LAVA, jitter=0.03)


def build_DeadTrees(p):
    dead_tree(p, -0.2, -0.9, 11, 0.6, 10)
    dead_tree(p, -8.2, 7.1, 9, -0.8, 80)
    dead_tree(p, 7.8, -6.9, 8, 0.8, 200)
    for (x, z, r) in ((-6, 0, 1.4), (4, 3, 1.2), (-2, -6, 1.0)):
        dk.ball(p, (x, 0.3, z), r, LAVA, scale=(1, 0.15, 0.9), subdiv=1, jitter=0.04)


# ---- 9. Cauldron ----------------------------------------------------------------------------------------------------------
def build_Cauldron(p):
    cx, cz = 0.5, 0.0
    dk.ball(p, (cx, 0.8, cz), 1.0, RED, scale=(3.6, 1.0, 3.6), subdiv=2, jitter=0.05)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        tube(p, (cx + 0.5 * math.cos(a), 0.9, cz + 0.5 * math.sin(a)), (cx + 4.0 * math.cos(a), 0.6, cz + 4.0 * math.sin(a)), 0.5, 0.42, WOOD, 5, 0.06)
    flame(p, cx, 1.2, cz, 2.5, 3.2, tongues=5)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        tube(p, (cx + 3.5 * math.cos(a), 3.6, cz + 3.5 * math.sin(a)), (cx + 4.9 * math.cos(a), 0.2, cz + 4.9 * math.sin(a)), 0.6, 0.5, BLK, 5)
        dk.ball(p, (cx + 5.0 * math.cos(a), 0.35, cz + 5.0 * math.sin(a)), 0.7, IRON, scale=(1, 0.6, 1), subdiv=1)
    dk.ball(p, (cx, 6.5, cz), 1.0, BLK, scale=(5.0, 3.7, 5.0), subdiv=2, jitter=0.04)
    for yy, rr in ((5.0, 4.85), (7.9, 4.8)):
        vcyl(p, cx, yy, yy + 0.4, cz, rr, IRON, verts=14, jit=0.03)
    vcyl(p, cx, 9.3, 10.2, cz, 4.7, IRON, verts=14, top_r=4.95)
    vcyl(p, cx, 9.9, 10.15, cz, 4.3, GREEN, verts=14, jit=0.04)
    for (dx, dz, r) in ((-1.4, 1.0, 0.9), (1.8, -0.6, 0.7), (0.2, -2.0, 0.6), (-2.2, -1.2, 0.5)):
        dk.ball(p, (cx + dx, 10.3 + r * 0.3, cz + dz), r, (160, 232, 110), scale=(1, 0.7, 1), subdiv=1, jitter=0.04)
    dk.ball(p, (cx + 0.6, 11.0, cz + 0.2), 0.9, (160, 232, 110), subdiv=1)
    for sx in (-1, 1):
        ring_xy(p, (cx + sx * 5.2, 8.6, cz), 1.3, 0.75, 0.5, IRON, segs=8)
    tube(p, (cx + 1.8, 10.0, cz + 1.4), (cx + 3.8, 10.9, cz + 2.4), 0.2, 0.2, WOOD, 4)
    dk.ball(p, (cx + 1.5, 9.9, cz + 1.3), 0.6, IRON, scale=(1, 0.6, 1), subdiv=1)
    bone(p, (cx - 6.9, 0.5, cz + 3.6), (cx - 3.4, 0.5, cz + 5.0), 0.28, DBONE)
    bone(p, (cx - 6.6, 0.5, cz - 1.0), (cx - 5.0, 0.5, cz - 4.0), 0.26, DBONE)
    skull(p, (cx + 6.0, 1.0, cz + 3.6), 1.1, yaw=-40, sub=1)
    rock(p, (cx - 5.4, 0.7, cz + 0.8), 0.9, ROCK, sub=0)


# ---- 10. SulfurVents ------------------------------------------------------------------------------------------------------
def vent(p, x, z, r, h, puffs):
    poly_cone(p, x, 0, h, z, r, ROCK, verts=8, rt=r * 0.62, jit=0.08)
    poly_cone(p, x, h - 0.3, h + 0.5, z, r * 0.7, SULF, verts=8, rt=r * 0.55, jit=0.06)
    vcyl(p, x, h + 0.45, h + 0.55, z, r * 0.36, BLK, verts=8, jit=0.02)
    for k in range(6):
        a = 2 * math.pi * k / 6 + x
        shard(p, x + r * 0.5 * math.cos(a), h + 0.2, z + r * 0.5 * math.sin(a), 0.55, 1.0 + (k % 2) * 0.5, SULF, tilt=(0.2 * math.cos(a), 0.2 * math.sin(a)), verts=4)
    for (dy, rr, col) in puffs:
        dk.ball(p, (x + 0.15 * dy % 0.6, h + dy, z), rr, col, scale=(1, 0.9, 1), subdiv=2, jitter=0.06)


def build_SulfurVents(p):
    vcyl(p, 0, 0, 0.35, 0, 9.0, SULF, verts=16, jit=0.08)
    vcyl(p, -1, 0.3, 0.4, 0.5, 5.5, (232, 214, 96), verts=12, jit=0.08)
    vent(p, 2, -5, 3.5, 2.4, ((2.2, 1.6, ASH), (4.6, 2.0, (140, 136, 142)), (7.2, 2.6, ASH)))
    vent(p, -6, 1, 2.8, 1.8, ((1.9, 1.3, ASH), (3.8, 1.7, (140, 136, 142)), (6.0, 2.1, ASH)))
    vent(p, 4, 5, 3.0, 2.0, ((2.0, 1.4, ASH), (4.2, 1.8, (140, 136, 142)), (6.6, 2.2, ASH)))


# ---- 11. ImpStatues -------------------------------------------------------------------------------------------------------
def imp_model(p, x, z, yaw):
    def A(dx, dy, dz):
        ox, oz = ryv(dx, dz, yaw)
        return (x + ox, dy, z + oz)
    R = (0, yaw, 0)
    dk.box(p, A(0, 0.6, 0), (5, 1.2, 5), ROCK, rot=R, jitter=0.05)
    dk.box(p, A(0, 1.6, 0), (4.0, 0.8, 4.0), LROCK, rot=R, jitter=0.05)
    for sx in (-1, 1):
        dk.box(p, A(sx * 0.95, 2.35, 0.5), (0.9, 0.5, 1.5), PURP, rot=R, jitter=0.04)             # feet
        tube(p, A(sx * 0.95, 2.4, 0.3), A(sx * 1.0, 3.9, -0.3), 0.5, 0.6, PURP, 5)                # shins
        tube(p, A(sx * 1.0, 3.9, -0.3), A(sx * 0.9, 5.0, 0.7), 0.62, 0.55, PURP, 5)               # thighs (crouched)
        tube(p, A(sx * 1.1, 6.5, 0.4), A(sx * 1.6, 5.2, 1.5), 0.36, 0.3, PURP, 4)                 # arms to the knees
        dk.ball(p, A(sx * 1.6, 5.1, 1.6), 0.38, LPURP, subdiv=1)
        for cz_ in (-0.2, 0.2):
            cone(p, *A(sx * 1.6 + cz_, 4.6, 1.9), 0.1, 0.6, BONE, verts=3)
    dk.box(p, A(0, 5.4, 0.2), (2.0, 1.4, 1.5), PURP, rot=R, jitter=0.04)                           # hips
    dk.box(p, A(0, 6.6, 0.3), (2.4, 1.7, 1.6), LPURP, rot=R, jitter=0.04)                          # chest
    dk.ball(p, A(0, 7.9, 0.6), 1.15, PURP, scale=(1.05, 0.95, 1.0), subdiv=2, rot=R, jitter=0.04)  # head
    dk.box(p, A(0, 7.4, 1.5), (1.5, 0.5, 0.5), BLK, rot=R, jitter=0.02)                            # grin
    for t in (-0.55, -0.2, 0.2, 0.55):
        dk.box(p, A(t, 7.62, 1.6), (0.2, 0.28, 0.14), BONE, rot=R, jitter=0.02)
    for sx in (-1, 1):
        dk.box(p, A(sx * 0.5, 8.2, 1.55), (0.36, 0.24, 0.18), LAVAY, rot=R, jitter=0.02)          # eyes
        horn(p, A(sx * 0.6, 8.7, 0.3), sx, 1.5, 0.9, 0.24, BONE, yaw=yaw, n=3)
        pyr = A(sx * 1.2, 8.2, 0.3)
        tube(p, pyr, A(sx * 2.3, 8.9, 0.1), 0.3, 0.05, PURP, 4)                                    # pointy ears
        # bat wing: bone arm + membrane
        a0, a1, a2 = A(sx * 0.9, 7.0, -0.7), A(sx * 2.6, 8.6, -1.0), A(sx * 3.5, 6.0, -1.0)
        tube(p, a0, a1, 0.14, 0.12, BONE, 4)
        tube(p, a1, a2, 0.12, 0.1, BONE, 4)
        wp = [(0, 0), (0, 0), (0, 0)]
        pts = [a0, a1, a2, A(sx * 1.6, 5.8, -0.9)]
        tri = [(0, 1, 2), (0, 2, 3)]
        verts_ = [(q[0], q[1], q[2]) for q in pts]
        dk.poly(p, (0, 0, 0), verts_, [(0, 1, 2), (0, 2, 3), (2, 1, 0), (3, 2, 0)], DRED, 0.04)
    chain_path(p, [A(0, 5.2, -0.6), A(0, 4.6, -1.8), A(0.8, 4.0, -2.2), A(1.2, 3.1, -1.6)], 0.2, PURP, verts=4, tip=0.1)
    pyramid(p, *[A(1.2, 2.7, -1.6)[0]], 2.7, A(1.2, 2.7, -1.6)[2], 0.7, 0.7, 0.5, BONE)


def build_ImpStatues(p):
    imp_model(p, -4.5, 2, 20)
    imp_model(p, 4.5, -2, -25)


# ---- 12. GatePillars ------------------------------------------------------------------------------------------------------
def gate_pillar(p, x):
    bx(p, (x - 3.2, x + 3.2), (0, 1.0), (-3.2, 3.2), ROCK)
    bx(p, (x - 2.8, x + 2.8), (1.0, 2.0), (-2.8, 2.8), LROCK)
    vcyl(p, x, 2.0, 20.6, 0, 2.35, OBS, verts=8, top_r=2.1, jit=0.07)
    for yy in (5.0, 9.0, 13.0, 17.0):
        vcyl(p, x, yy, yy + 0.7, 0, 2.7, RROCK, verts=8, jit=0.05)
    skull(p, (x, 14.8, 1.55), 1.5, sub=2, glow=LAVA)
    for yy in (7.0, 11.0):
        for sx in (-1, 1):
            dk.box(p, (x + sx * 1.9, yy, 1.4), (0.3, 1.6, 0.3), LAVA, jitter=0.03)
    bx(p, (x - 3.1, x + 3.1), (20.6, 21.6), (-3.1, 3.1), RROCK)
    bx(p, (x - 2.4, x + 2.4), (21.6, 22.0), (-2.4, 2.4), BLK)
    for sx in (-1, 1):
        horn(p, (x + sx * 1.5, 22.0, 0), sx, 3.8, 2.4, 0.75, BONE, n=4)
    cone(p, x, 22.0, 0, 0.7, 2.6, BONE, verts=5)


def build_GatePillars(p):
    gate_pillar(p, -12)
    gate_pillar(p, 12)
    link_chain(p, (-9.6, 15.2, 0), (9.6, 15.2, 0), 14, IRON, sag=2.6, size=0.6)
    link_chain(p, (-9.6, 11.6, 0), (9.6, 11.6, 0), 14, IRON, sag=1.4, size=0.6)
    for x in (-9.6, 9.6):
        for yy in (15.2, 11.6):
            dk.ball(p, (x, yy, 0), 0.55, IRON, subdiv=1)


# ---- 13. SkullTotems ------------------------------------------------------------------------------------------------------
def build_SkullTotems(p):
    bx(p, (-7, 7), (0, 0.7), (-3, 3), ROCK)
    bx(p, (-6, 6), (0.7, 1.0), (-2.6, 2.6), RROCK)
    # short pole left, tall horned pole in the middle, red-topped pole right
    for (x, h, ys, rr) in ((-4, 16.0, (4.0, 8.0, 12.0), 1.3), (0, 20.0, (5.4, 10.2, 14.8), 1.5), (4, 14.0, (4.0, 9.0), 1.3)):
        tube(p, (x, 1.0, 0), (x, h, 0), 0.5, 0.42, IRON, 6)
        for k, yy in enumerate(ys):
            skull(p, (x, yy, 0), rr, yaw=(-25, 15, 35)[k % 3], sub=1)
            bx(p, (x - 0.9, x + 0.9), (yy - rr - 0.28, yy - rr), (-0.9, 0.9), BLK)
        cone(p, x, h, 0, 0.55, 1.3 if x != 0 else 0.5, LIRON, verts=4)
    skull(p, (0, 18.9, 0), 1.7, sub=2, glow=RED)
    for sx in (-1, 1):
        horn(p, (sx * 1.2, 19.6, 0), sx, 2.7, 1.6, 0.5, BONE, n=3)
    skull(p, (4, 14.4, 0), 1.1, col=RED, sub=1)
    # crossbar with a tattered red pennant on each outer pole
    tube(p, (-4, 13.2, 0), (-1.6, 13.2, 0), 0.22, 0.22, IRON, 4)
    cloth(p, -2.9, 13.0, 0.25, 2.5, 3.6, RED, teeth=3, wave=0.3)
    tube(p, (4, 11.6, 0), (6.2, 11.6, 0), 0.22, 0.22, IRON, 4)
    cloth(p, 5.2, 11.4, 0.25, 2.3, 3.2, DRED, teeth=3, wave=0.3)


# ---- 14. HellKennel -------------------------------------------------------------------------------------------------------
def build_HellKennel(p):
    z0, z1 = -4.7, 2.3
    bx(p, (-4.6, 4.6), (0, 0.4), (z0 - 0.2, z1 + 0.5), LROCK)
    bx(p, (-4, 4), (0.4, 5.8), (z0, z0 + 0.8), OBS)
    bx(p, (-4, -1.9), (0.4, 5.8), (z0 + 0.8, z1), OBS)
    bx(p, (1.9, 4), (0.4, 5.8), (z0 + 0.8, z1), OBS)
    bx(p, (-1.9, 1.9), (4.0, 5.8), (z1 - 0.8, z1), OBS)
    bx(p, (-1.9, 1.9), (0.4, 4.0), (z0 + 0.8, z0 + 0.95), RED)
    bx(p, (-1.9, 1.9), (0.4, 0.5), (z0 + 0.95, z1), DRED)
    for sx in (-1, 1):
        bx(p, (sx * 2.15 - 0.25, sx * 2.15 + 0.25), (0.4, 4.4), (z1 - 0.1, z1 + 0.3), RROCK)
    bx(p, (-2.4, 2.4), (4.0, 4.5), (z1 - 0.1, z1 + 0.3), RROCK)
    for sx in (-1, 1):
        for yy in (1.5, 3.2):
            bx(p, (sx * 3.0 - 0.9, sx * 3.0 + 0.9), (yy, yy + 0.35), (z1 - 0.05, z1 + 0.1), RROCK)
    skull(p, (0, 5.0, z1 + 0.5), 0.8, sub=1, glow=RED)
    dk.prism(p, (0, 5.8, (z0 + z1) / 2), 9.2, 8.2, 3.6, BLK, ridge='z', jitter=0.05)
    bx(p, (-0.45, 0.45), (9.2, 9.7), (z0 - 0.6, z1 + 0.6), RROCK)
    for zz in (-4.0, -1.2, 1.6):
        cone(p, 0, 9.6, zz, 0.5, 2.3, BONE, verts=4)
    vcyl(p, 4.4, 0, 0.9, 3.8, 1.5, IRON, verts=10, top_r=1.7)
    for (dx, dz, r) in ((0, 0, 0.9), (0.6, 0.4, 0.5), (-0.5, -0.4, 0.5)):
        dk.ball(p, (4.4 + dx, 1.0, 3.8 + dz), r, BONE, scale=(1, 0.7, 1), subdiv=1)
    bone(p, (3.4, 1.4, 4.2), (5.2, 1.8, 3.2), 0.22)
    tube(p, (-4.4, 0, 3.8), (-4.4, 2.4, 3.8), 0.28, 0.2, IRON, 5)
    ring_xy(p, (-4.4, 2.5, 3.8), 0.55, 0.3, 0.3, IRON, segs=8)
    link_chain(p, (-4.3, 2.3, 3.8), (-2.2, 0.6, 2.6), 6, IRON, sag=0.5, size=0.45)


# ---- 15. IronCages --------------------------------------------------------------------------------------------------------
def hang_cage(p, x, ytop, h, w):
    y0 = ytop - h
    bx(p, (x - w / 2, x + w / 2), (y0, y0 + 0.3), (-w / 2, w / 2), IRON)
    bx(p, (x - w / 2, x + w / 2), (ytop - 0.3, ytop), (-w / 2, w / 2), IRON)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bx(p, (x + sx * (w / 2 - 0.1) - 0.12, x + sx * (w / 2 - 0.1) + 0.12), (y0, ytop), (sz * (w / 2 - 0.1) - 0.12, sz * (w / 2 - 0.1) + 0.12), BLK, 0.03)
    for sx in (-0.33, 0.33):
        bx(p, (x + sx * w - 0.1, x + sx * w + 0.1), (y0, ytop), (w / 2 - 0.2, w / 2), BLK, 0.03)
    ym = y0 + h * 0.5
    bx(p, (x - w / 2, x + w / 2), (ym, ym + 0.22), (w / 2 - 0.22, w / 2), IRON)
    bx(p, (x - w / 2, x + w / 2), (ym, ym + 0.22), (-w / 2, -w / 2 + 0.22), IRON)
    pyramid(p, x, ytop, 0, w * 0.9, w * 0.9, 0.7, IRON)
    skull(p, (x, y0 + 0.3 + 0.75, 0), 0.75, sub=1, yaw=(x * 37) % 90 - 45)
    dk.ball(p, (x, ytop + 0.8, 0), 0.3, IRON, subdiv=1)


def build_IronCages(p):
    bx(p, (-9, 9), (0, 1.0), (-3, 3), ROCK)
    bx(p, (-8.4, 8.4), (1.0, 1.4), (-2.5, 2.5), LROCK)
    for sx in (-1, 1):
        x = sx * 8
        bx(p, (x - 0.6, x + 0.6), (1.4, 14.2), (-0.6, 0.6), BLK)
        for yy in (3.0, 8.0, 12.4):
            bx(p, (x - 0.85, x + 0.85), (yy, yy + 0.5), (-0.85, 0.85), IRON)
        cone(p, x, 14.2, 0, 0.8, 1.3, IRON, verts=4)
    bx(p, (-8.8, 8.8), (14.0, 15.2), (-0.6, 0.6), BLK)
    for sx in (-1, 1):
        diag(p, sx * 8, 11.2, 0, sx * 4.6, 14.0, 0.5, 0.6, BLK)
    for (x, h, w) in ((-5, 4.4, 3.2), (0, 5.0, 3.6), (5, 4.4, 3.2)):
        top = 14.0 - 2.0 if x != 0 else 14.0 - 3.0
        top = 11.2 if x != 0 else 10.2
        link_chain(p, (x, 14.0, 0), (x, top + 0.9, 0), 4, IRON, size=0.45)
        hang_cage(p, x, top, h, w)
    skull(p, (-6.8, 1.9, 1.6), 0.8, sub=1, yaw=30)
    bone(p, (4.4, 1.6, 1.8), (7.4, 1.6, 0.8), 0.25)


# ---- 16. RitualCircle -----------------------------------------------------------------------------------------------------
def build_RitualCircle(p):
    vcyl(p, 0, 0, 0.4, 0, 11, DRED, verts=24, jit=0.06)
    vcyl(p, 0, 0.35, 0.55, 0, 8.8, RED, verts=24, jit=0.04)
    vcyl(p, 0, 0.5, 0.62, 0, 7.5, LAVA, verts=24, jit=0.03)
    vcyl(p, 0, 0.6, 0.74, 0, 7.0, BLK, verts=24, jit=0.03)
    star_poly(p, (0, 0.76, 0), 'xz', 6.5, 2.6, 0.08, LAVA, n=5, rot0=90)
    star_poly(p, (0, 0.8, 0), 'xz', 5.3, 2.1, 0.08, LAVAY, n=5, rot0=90)
    for k in range(14):
        a = 2 * math.pi * k / 14
        dk.box(p, (8.1 * math.cos(a), 0.58, 8.1 * math.sin(a)), (0.45, 0.1, 0.95), LAVAY, rot=(0, -math.degrees(a) + 90, 0), jitter=0.03)
    for k, (x, z, h) in enumerate(((0, 8.5, 6.4), (8.1, 2.5, 6.0), (5.1, -7.1, 6.8), (-5.1, -7.1, 6.0), (-8.1, 2.5, 6.4))):
        d = math.hypot(x, z)
        shard(p, x, 0.2, z, 2.4, h, OBS, tilt=(-x / d * 0.6, -z / d * 0.6), verts=5, tip=0.3, jit=0.1)
        ix, iz = x - x / d * 1.0, z - z / d * 1.0
        yaw = math.degrees(math.atan2(-x, -z))
        dk.box(p, (ix, h * 0.42, iz), (0.6, 1.8, 0.22), LAVA, rot=(0, yaw, 0), jitter=0.03)
        dk.box(p, (ix, h * 0.62, iz), (1.2, 0.3, 0.22), LAVA, rot=(0, yaw, 0), jitter=0.03)
    bx(p, (-2.5, 2.5), (0.8, 2.0), (-1.5, 1.5), BLK)
    bx(p, (-2.7, 2.7), (2.0, 2.3), (-1.7, 1.7), RROCK)
    skull(p, (0, 3.2, 0.1), 0.95, sub=1, yaw=0)
    for (x, z) in ((-3.4, -1.8), (3.4, 1.8), (-3.2, 2.6), (3.2, -2.6)):
        vcyl(p, x, 0.74, 1.8, z, 0.24, BONE, verts=5)
        cone(p, x, 1.8, z, 0.2, 0.5, LAVAY, verts=4)


# ---- 17. WarBanners -------------------------------------------------------------------------------------------------------
def standard(p, x, z, h, col, side):
    bx(p, (x - 1.5, x + 1.5), (0, 0.7), (z - 1.5, z + 1.5), ROCK)
    bx(p, (x - 1.1, x + 1.1), (0.7, 1.2), (z - 1.1, z + 1.1), RROCK)
    tube(p, (x, 1.2, z), (x, h, z), 0.4, 0.3, IRON, 6)
    for k in range(5):
        a = 2 * math.pi * k / 5
        cone(p, x + 0.9 * math.cos(a), 1.2, z + 0.9 * math.sin(a), 0.22, 1.6, BLK, verts=4)
    tube(p, (x, h - 1.4, z), (x + side * 4.8, h - 1.4, z), 0.18, 0.18, IRON, 4)
    cloth(p, x + side * 2.5, h - 1.5, z, 4.4, h * 0.38, col, teeth=3, wave=0.5, trim=BLK)
    dk.box(p, (x + side * 2.5, h - 1.5 - h * 0.17, z + 0.3), (1.2, 1.2, 0.12), BONE, jitter=0.03)
    dk.ball(p, (x, h + 0.6, z), 0.8, BONE, scale=(0.8, 1.2, 0.8), subdiv=1)
    cone(p, x, h + 1.0, z, 0.35, 1.8, LIRON, verts=4)
    for sx in (-1, 1):
        horn(p, (x + sx * 0.5, h - 0.3, z), sx, 1.4, 0.9, 0.2, BONE, n=3)


def build_WarBanners(p):
    standard(p, -6.6, 0, 16.0, RED, 1)
    standard(p, -0.6, 4, 18.0, DRED, 1)
    standard(p, 3.4, -4, 14.0, RED, 1)


# ---- 18. LavaFountain -----------------------------------------------------------------------------------------------------
def build_LavaFountain(p):
    vcyl(p, 0, 0, 2.0, 0, 8.6, ROCK, verts=14, jit=0.07)
    vcyl(p, 0, 2.0, 2.4, 0, 8.7, LROCK, verts=14, jit=0.05)
    vcyl(p, 0, 2.0, 2.2, 0, 7.2, LAVA, verts=14, jit=0.03)
    vcyl(p, 0, 2.15, 2.25, 0, 4.8, LAVAY, verts=12, jit=0.03)
    poly_cone(p, 0, 2.0, 7.0, 0, 3.4, BLK, verts=7, rt=1.6, jit=0.08)
    for k in range(3):
        a = 2 * math.pi * k / 3
        shard(p, 1.8 * math.cos(a), 2.0, 1.8 * math.sin(a), 1.1, 3.4, OBS, tilt=(0.9 * math.cos(a), 0.9 * math.sin(a)), verts=5)
    tube(p, (0, 6.8, 0), (0, 11.0, 0), 1.1, 0.6, LAVA, 6, 0.03)
    dk.ball(p, (0, 12.4, 0), 1.5, LAVAY, subdiv=2, jitter=0.04)
    for k in range(4):
        a = math.pi / 2 * k + 0.6
        pts = [(0, 10.0, 0), (2.0 * math.cos(a), 11.0, 2.0 * math.sin(a)), (4.2 * math.cos(a), 9.4, 4.2 * math.sin(a)), (5.6 * math.cos(a), 5.4, 5.6 * math.sin(a))]
        chain_path(p, pts, 0.5, LAVA, verts=5, tip=0.3, jit=0.03)
        dk.ball(p, (5.6 * math.cos(a), 4.0, 5.6 * math.sin(a)), 0.7, LAVAY, subdiv=1)
    for k in range(7):
        a = 2 * math.pi * k / 7
        rock(p, (9.0 * math.cos(a), 1.6, 9.0 * math.sin(a)), 1.5 + (k % 3) * 0.35, ROCK if k % 2 else OBS, squash=1.1, sub=1)
    skull(p, (6.2, 2.6, -3.0), 0.9, yaw=40, sub=1)


# ---- 19. BoneBridge -------------------------------------------------------------------------------------------------------
def bridge_y(x):
    return 1.2 + 1.4 * max(0.0, 1 - (x / 9.0) ** 2) ** 0.8


def build_BoneBridge(p):
    bx(p, (-4, 4), (0, 0.45), (-12, 12), LAVA, 0.03)
    for zz in (-9, -3, 3, 9):
        bx(p, (-1.2, 1.2), (0.45, 0.5), (zz - 1.2, zz + 1.2), LAVAY, 0.03)
    for sx in (-1, 1):
        bx(p, (sx * 4.2 if sx > 0 else -8.6, 8.6 if sx > 0 else -4.2), (0, 0.6), (-12, 12), BLK, 0.1)
        for k in range(5):
            rock(p, (sx * 4.6, 0.7, -9.5 + k * 4.8), 0.9, ROCK, squash=0.7, sub=0)
    for i in range(9):
        x = -9 + 2.0 * i + 1.0
        y = bridge_y(x)
        ang = -math.degrees(math.atan2(bridge_y(x + 0.5) - bridge_y(x - 0.5), 1.0))
        dk.box(p, (x, y, 0), (2.05, 0.55, 4.4), BONE if i % 2 else DBONE, rot=(0, 0, -ang), jitter=0.05)
    for sz in (-2.4, 2.4):
        for xx in (-9, -4.5, 0, 4.5, 9):
            y = bridge_y(xx) + 0.3
            bone(p, (xx, y, sz), (xx, y + 3.2, sz), 0.22, BONE, 1.6, 5)
        prev = None
        for xx in (-9, -6.75, -4.5, -2.25, 0, 2.25, 4.5, 6.75, 9):
            q = (xx, bridge_y(xx) + 3.3, sz)
            if prev:
                tube(p, prev, q, 0.2, 0.2, BONE, 4)
            prev = q
    for (xx, sz) in ((-9, -2.4), (9, -2.4), (-9, 2.4), (9, 2.4)):
        skull(p, (xx, bridge_y(xx) + 4.5, sz), 0.95, yaw=90 if xx > 0 else -90, sub=1)
    for sx in (-1, 1):
        bx(p, (sx * 9 - (0 if sx > 0 else 1.6), sx * 9 + (1.6 if sx > 0 else 0)), (0, 1.2), (-2.6, 2.6), ROCK)


# ---- 20. RuinedWall -------------------------------------------------------------------------------------------------------
def wall_block(p, x0, x1, h, z0=-1.3, z1=1.3, col=ROCK, crown=True):
    courses = max(2, int(h // 2.2))
    ch = h / courses
    for c in range(courses):
        off = 0.0 if c % 2 == 0 else (x1 - x0) * 0.22
        bx(p, (x0, x1), (c * ch, (c + 1) * ch - 0.05), (z0, z1), shade(col, 0.92 + 0.08 * (c % 2)), 0.07)
    if crown:
        n = max(1, int((x1 - x0) // 2.2))
        for k in range(n):
            if k % 2 == 0:
                xa = x0 + (x1 - x0) * k / n
                bx(p, (xa + 0.1, xa + (x1 - x0) / n - 0.1), (h, h + 1.0), (z0, z1), BLK, 0.06)


def build_RuinedWall(p):
    wall_block(p, -9.2, -2.2, 11.0)
    wall_block(p, -2.2, 3.2, 6.0, col=OBS)
    wall_block(p, 3.2, 9.8, 13.0)
    wall_block(p, 9.8, 13.4, 4.4, col=OBS, crown=False)
    bx(p, (-12.2, -9.2), (0, 8.0), (-1.7, 1.7), OBS)
    bx(p, (-9.2, -2.2), (5.0, 8.2), (1.3, 1.5), RROCK)
    bx(p, (-7.4, -4.4), (3.0, 6.4), (1.3, 1.6), BLK)
    bx(p, (-7.0, -4.8), (3.2, 6.0), (1.5, 1.6), RED)
    cloth(p, 6.4, 11.6, 1.5, 2.6, 4.4, DRED, teeth=3, wave=0.2)
    tube(p, (5.1, 11.8, 1.5), (7.7, 11.8, 1.5), 0.2, 0.2, IRON, 4)
    for (x, z, r, col) in ((-6, 2.6, 1.3, ROCK), (1, 2.4, 1.0, OBS), (7, 2.8, 1.3, ROCK), (11, 2.2, 1.1, OBS), (-10, 2.4, 1.0, ROCK), (4, -2.6, 1.0, OBS)):
        rock(p, (x, r * 0.5, z), r, col, squash=0.8, sub=1)
    skull(p, (-1.0, 0.9, 2.5), 0.8, yaw=20, sub=1)


# ---- 21. Watchtower -------------------------------------------------------------------------------------------------------
def build_Watchtower(p):
    bx(p, (-5.5, 5.5), (0, 0.8), (-5.5, 5.5), ROCK)
    bx(p, (-4.6, 4.6), (0.8, 1.6), (-4.6, 4.6), LROCK)
    frust(p, 0, 1.6, 18.4, 0, 7.6, 7.6, 6.6, 6.6, OBS)
    for yy in (4.5, 8.5, 12.5, 16.0):
        frust(p, 0, yy, yy + 0.6, 0, 8.0 - yy * 0.06, 8.0 - yy * 0.06, 8.0 - yy * 0.06, 8.0 - yy * 0.06, RROCK)
    for yy in (6.0, 10.5, 14.0):
        for (sx, sz, w, d) in ((0, 1, 1.3, 0.3), (0, -1, 1.3, 0.3), (1, 0, 0.3, 1.3), (-1, 0, 0.3, 1.3)):
            k = 3.35 - yy * 0.04
            dk.box(p, (sx * k, yy, sz * k), (w, 2.4, d), RED, jitter=0.03)
    bx(p, (-5.5, 5.5), (18.4, 19.6), (-5.5, 5.5), ROCK)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        bx(p, (sx * 4.4 - 0.7, sx * 4.4 + 0.7), (19.6, 21.0), (sz * 4.4 - 0.7, sz * 4.4 + 0.7), ROCK)
        cone(p, sx * 4.4, 21.0, sz * 4.4, 0.55, 1.5, BONE, verts=4)
    for t in (-2.2, 0, 2.2):
        bx(p, (t - 0.6, t + 0.6), (19.6, 20.8), (-5.2, -4.0), ROCK)
        bx(p, (t - 0.6, t + 0.6), (19.6, 20.8), (4.0, 5.2), ROCK)
    bx(p, (-3.7, 3.7), (19.6, 25.6), (-3.7, 3.7), BLK)
    for (sx, sz) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        dk.box(p, (sx * 3.75, 22.8, sz * 3.75), (1.9 if sx == 0 else 0.3, 2.6, 0.3 if sx == 0 else 1.9), RED, jitter=0.03)
    pyramid(p, 0, 25.6, 0, 9.6, 9.6, 3.0, DRED)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        horn(p, (sx * 4.2, 25.8, sz * 4.2), sx, 2.8, 1.0, 0.4, BONE, n=3)
    tube(p, (0, 28.0, 0), (0, 31.4, 0), 0.5, 0.15, BONE, 5)
    skull(p, (0, 28.4, 0.2), 0.0001 + 0.9, sub=1, yaw=0)


# ---- 22. DemonStatue ------------------------------------------------------------------------------------------------------
def build_DemonStatue(p):
    bx(p, (-8, 8), (0, 1.8), (-7, 7), ROCK)
    bx(p, (-7, 7), (1.8, 3.0), (-6, 6), LROCK)
    for sx in (-1, 1):
        skull(p, (sx * 5.2, 2.3, 6.2), 0.9, sub=1)
    for sx in (-1, 1):                                       # legs: thigh, shin, hoof
        x = sx * 2.7
        tube(p, (x, 10.4, 0), (x * 1.1, 7.2, 1.2), 1.7, 1.4, OBS, 6)
        tube(p, (x * 1.1, 7.2, 1.2), (x, 3.6, -0.4), 1.4, 1.1, OBS, 6)
        dk.box(p, (x, 3.4, 0.8), (2.4, 0.9, 3.6), BLK, jitter=0.05)
        cone(p, x - 0.7, 3.0, 2.6, 0.4, 0.9, BONE, verts=4)
        cone(p, x + 0.7, 3.0, 2.6, 0.4, 0.9, BONE, verts=4)
    frust(p, 0, 10.0, 14.4, 0, 7.0, 4.6, 9.0, 5.4, DRED)
    dk.box(p, (0, 13.8, 2.2), (2.4, 4.2, 0.4), RED, jitter=0.04)
    frust(p, 0, 14.4, 23.0, 0, 9.0, 5.4, 12.4, 6.6, OBS)
    for yy in (16.8, 19.2):
        dk.box(p, (0, yy, 3.2), (5.2, 0.35, 0.3), RROCK, jitter=0.03)
    dk.box(p, (0, 21.6, 3.3), (1.6, 1.6, 0.3), RED, jitter=0.03)
    for sx in (-1, 1):                                       # shoulders with spikes, arms to the sword hilt
        x = sx * 6.6
        dk.ball(p, (x, 22.4, 0), 2.3, BLK, scale=(1, 0.8, 1.0), subdiv=2, jitter=0.06)
        for k in range(3):
            horn(p, (x + sx * 0.4 * k, 24.0, -0.5 + k * 0.7), sx, 2.0 - 0.2 * k, 0.8, 0.45, BONE, n=2)
        tube(p, (x, 21.4, 0.4), (sx * 6.9, 17.6, 2.2), 1.4, 1.2, OBS, 6)
        tube(p, (sx * 6.9, 17.6, 2.2), (sx * 1.4, 15.8, 4.2), 1.2, 1.0, OBS, 6)
        dk.ball(p, (sx * 1.0, 15.6, 4.4), 1.1, BLK, subdiv=1)
    tube(p, (0, 15.0, 4.4), (0, 24.0, 4.4), 0.45, 0.45, BLK, 5)           # sword hilt above the hands
    dk.ball(p, (0, 24.4, 4.4), 0.8, BONE, subdiv=1)
    bx(p, (-2.6, 2.6), (14.4, 15.0), (4.0, 4.8), IRON)
    for sx in (-1, 1):
        horn(p, (sx * 2.4, 14.7, 4.4), sx, 1.4, 1.2, 0.3, BONE, n=2)
    bx(p, (-0.9, 0.9), (3.0, 14.4), (4.1, 4.7), LIRON)                   # blade, planted in the pedestal
    bx(p, (-0.2, 0.2), (4.0, 13.8), (4.7, 4.8), IRON)
    cone(p, 0, 2.2, 4.4, 0.0001 + 0.8, 0.8, LIRON, verts=4)
    dk.ball(p, (0, 28.4, 0.4), 2.7, OBS, scale=(1, 1.0, 1.0), subdiv=2, jitter=0.05)       # head
    dk.box(p, (0, 26.4, 2.0), (2.6, 1.2, 1.6), BLK, jitter=0.04)
    for t in (-0.9, -0.3, 0.3, 0.9):
        dk.box(p, (t, 26.8, 2.9), (0.3, 0.5, 0.2), BONE, jitter=0.02)
    for sx in (-1, 1):
        dk.box(p, (sx * 1.1, 28.9, 2.7), (0.9, 0.5, 0.3), RED, jitter=0.02)
        horn(p, (sx * 1.8, 30.3, 0.0), sx, 3.9, 2.8, 1.0, BONE, n=5)
        tube(p, (sx * 2.6, 28.4, 0.2), (sx * 4.6, 29.2, 0.0), 0.7, 0.1, OBS, 4)
        # folded wings behind: arm bone + 3 fingers + membrane
        s0, s1, s2 = (sx * 4.2, 24.0, -3.0), (sx * 9.2, 31.0, -4.2), (sx * 13.0, 26.0, -4.6)
        tube(p, s0, s1, 0.7, 0.55, OBS, 5)
        tube(p, s1, s2, 0.55, 0.4, OBS, 5)
        tips = [(sx * 13.6, 16.0, -4.6), (sx * 10.0, 9.4, -4.4), (sx * 5.0, 8.0, -3.6)]
        for t in tips:
            tube(p, s2, t, 0.34, 0.12, OBS, 4)
        for (a, b, c) in ((s0, s1, s2), (s0, s2, tips[0]), (s0, tips[0], tips[1]), (s0, tips[1], tips[2])):
            tri_slab(p, [(a[0], a[1]), (b[0], b[1]), (c[0], c[1])], -4.9, -4.4, DRED)
    dk.box(p, (0, 22.5, -3.4), (6.0, 7.0, 1.2), BLK, jitter=0.04)


# ---- 23. FireAltar --------------------------------------------------------------------------------------------------------
def build_FireAltar(p):
    bx(p, (-5.5, 5.5), (0, 1.2), (-5.5, 5.5), ROCK)
    bx(p, (-4.2, 4.2), (1.2, 2.4), (-4.2, 4.2), OBS)
    bx(p, (-3.0, 3.0), (2.4, 3.6), (-3.0, 3.0), RROCK)
    for sx in (-1, 1):
        for yy in (0.4, 1.8):
            bx(p, (sx * 4.9 - 0.4, sx * 4.9 + 0.4), (yy, yy + 0.5), (-1.6, 1.6), RED)
    vcyl(p, 0, 3.6, 5.0, 0, 1.7, IRON, verts=10, top_r=2.9)
    vcyl(p, 0, 4.9, 5.2, 0, 3.0, LIRON, verts=10)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cone(p, 2.9 * math.cos(a), 5.1, 2.9 * math.sin(a), 0.3, 1.5, BLK, verts=4)
    flame(p, 0, 5.1, 0, 2.7, 5.8, tongues=5)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, z = sx * 4.4, sz * 4.4
        vcyl(p, x, 3.0, 5.6, z, 0.5, BLK, verts=6)
        skull(p, (x, 6.4, z), 0.9, yaw=math.degrees(math.atan2(sx, sz)), sub=1)
        cone(p, x, 7.3, z, 0.3, 1.2, BONE, verts=4)


# ---- 24. LavaMoat ---------------------------------------------------------------------------------------------------------
def moat_blocks(p, x0, x1, z0, z1, along, rng, hmax):
    """Rough bank blocks along a straight edge (along = 'z' or 'x')."""
    L = (z1 - z0) if along == 'z' else (x1 - x0)
    n = max(1, int(L // 3.3))
    for k in range(n):
        a = k / n * L
        b = (k + 1) / n * L - 0.15
        h = 0.7 + rng.random() * (hmax - 0.7)
        if along == 'z':
            bx(p, (x0, x1), (0, h), (z0 + a, z0 + b), rng.choice([BLK, OBS, ROCK]), 0.1)
        else:
            bx(p, (x0 + a, x0 + b), (0, h), (z0, z1), rng.choice([BLK, OBS, ROCK]), 0.1)


def build_LavaMoat(p):
    rng = random.Random(8)
    zc = -48.0
    L = 29.5
    for (x, z, w, d) in ((-16, -47.75 - zc, 5, L), (16, -47.75 - zc, 5, L), (0, -60 - zc, 32, 5)):
        bx(p, (x - w / 2, x + w / 2), (0, 0.5), (z - d / 2, z + d / 2), LAVA, 0.03)
        if d > w:
            bx(p, (x - 0.6, x + 0.6), (0.5, 0.55), (z - d / 2 + 0.5, z + d / 2 - 0.5), LAVAY, 0.03)
        else:
            bx(p, (x - w / 2 + 0.5, x + w / 2 - 0.5), (0.5, 0.55), (z - 0.6, z + 0.6), LAVAY, 0.03)
    za, zb = -47.75 - zc - L / 2, -47.75 - zc + L / 2
    for (xa, xb) in ((-19.7, -18.5), (-13.5, -12.3), (12.3, 13.5), (18.5, 19.7)):
        moat_blocks(p, xa, xb, za, zb, 'z', rng, 1.4 if xa in (-19.7, 18.5) else 1.0)
    moat_blocks(p, -13.0, 13.0, -56.9 - zc - 0.6, -56.9 - zc + 0.6, 'x', rng, 1.0)
    moat_blocks(p, -19.7, 19.7, -63.1 - zc - 0.6, -63.1 - zc + 0.6, 'x', rng, 1.6)
    for (x, z) in ((-19, -15.0), (19, -15.0), (-18, 15.2), (18, 15.2), (0, 15.5), (-10, 15.0), (10, 15.0), (-19.2, 2.0), (19.2, 2.0)):
        shard(p, x, 0.9, z, 1.0, 2.3 + rng.random() * 0.9, BLK, tilt=(0.2, 0.2), verts=4, jit=0.1)
    for (x, z) in ((-17.0, 14.8), (17.0, 14.8)):
        rock(p, (x, 1.6, z - 0.0), 1.6, ROCK, squash=1.0, sub=1)


# ---- 25. SkullMountain ----------------------------------------------------------------------------------------------------
def build_SkullMountain(p):
    rng = random.Random(25)
    dk.ball(p, (0, 3.6, 0), 1.0, ROCK, scale=(13, 3.8, 11), subdiv=2, jitter=0.12)
    dk.ball(p, (0, 8.6, 0), 1.0, OBS, scale=(8.6, 4.2, 7.0), subdiv=2, jitter=0.12)
    dk.ball(p, (0, 13.0, 0), 1.0, ROCK, scale=(5.4, 3.4, 4.4), subdiv=2, jitter=0.12)
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.2
        r = 11.0 + (k % 3) * 0.5
        shard(p, r * 0.92 * math.cos(a), 0.8, r * 0.78 * math.sin(a), 2.0, 3.6 + (k % 4), OBS if k % 2 else BLK, tilt=(0.5 * math.cos(a), 0.5 * math.sin(a)), verts=5, jit=0.12)
    for k, (a, rad, y) in enumerate(((20, 11.4, 3.4), (80, 10.0, 3.0), (140, 11.0, 3.6), (200, 11.6, 3.0), (260, 10.4, 3.2), (320, 11.2, 3.6),
                                    (50, 7.4, 8.4), (130, 7.2, 8.0), (230, 7.6, 8.2), (310, 7.0, 8.6))):
        ar = math.radians(a)
        x, z = rad * math.cos(ar) * 0.95, rad * math.sin(ar) * 0.82
        skull(p, (x, y, z), 1.35 if k < 6 else 1.2, yaw=math.degrees(math.atan2(x, z)), sub=1)
    for (a, y0) in ((30, 4), (110, 5), (190, 4), (290, 5)):
        ar = math.radians(a)
        pts = [(8.5 * math.cos(ar) * 0.6, 12.5, 7.0 * math.sin(ar) * 0.6), (10.2 * math.cos(ar) * 0.8, 9.0, 8.6 * math.sin(ar) * 0.8), (11.6 * math.cos(ar), 4.6, 9.6 * math.sin(ar))]
        chain_path(p, pts, 0.38, LAVA, verts=4, tip=0.3, jit=0.03)
    skull(p, (0, 19.6, 0.4), 4.2, sub=2, glow=RED)
    for t in (-2.4, -0.8, 0.8, 2.4):
        dk.box(p, (t, 15.6, 3.9), (1.2, 1.0, 0.5), BONE, jitter=0.03)
    for sx in (-1, 1):
        horn(p, (sx * 3.2, 22.4, 0), sx, 5.8, 3.4, 0.95, BONE, n=5)
    dk.box(p, (0, 22.0, 0.3), (1.4, 0.6, 0.4), DBONE, jitter=0.03)


# ---- 26. GateArch ---------------------------------------------------------------------------------------------------------
def arch_pillar(p, x):
    bx(p, (x - 3.0, x + 3.0), (0, 1.0), (-2.8, 2.8), ROCK)
    bx(p, (x - 2.6, x + 2.6), (1.0, 2.0), (-2.6, 2.6), LROCK)
    vcyl(p, x, 2.0, 20.4, 0, 2.2, OBS, verts=8, top_r=2.0, jit=0.07)
    for yy in (5.0, 9.0, 13.0, 17.0):
        vcyl(p, x, yy, yy + 0.7, 0, 2.55, RROCK, verts=8, jit=0.05)
    skull(p, (x, 13.8, 1.5), 1.5, sub=2, glow=LAVA)
    for yy in (7.5, 10.5):
        for sx in (-1, 1):
            dk.box(p, (x + sx * 1.7, yy, 1.4), (0.3, 1.6, 0.3), LAVA, jitter=0.03)
    for sx in (-1, 1):
        horn(p, (x + sx * 1.4, 21.0, 0), sx, 5.0, 3.0, 0.75, BONE, n=5)


def build_GateArch(p):
    arch_pillar(p, -13.5)
    arch_pillar(p, 13.5)
    bx(p, (-15.5, 15.5), (20.4, 24.0), (-2.6, 2.6), RROCK)
    bx(p, (-15.0, 15.0), (19.9, 20.4), (-2.3, 2.3), BLK)
    dk.prism(p, (0, 24.0, 0), 30.0, 4.4, 4.6, OBS, ridge='z', jitter=0.05)
    skull(p, (0, 24.6, 2.2), 2.4, sub=2, glow=RED)
    cone(p, 0, 28.5, 0, 0.7, 3.1, BONE, verts=5)
    for k, x in enumerate((-12.4, -8.2, -4.2, 4.2, 8.2, 12.4)):
        poly_cone(p, x, 18.8, 19.9, 0, 0.06, BONE, verts=4, rt=0.55)
    for sx in (-1, 1):
        cloth(p, sx * 8.6, 19.8, 2.7, 3.0, 7.0, RED, teeth=3, wave=0.4, trim=BLK)
        dk.box(p, (sx * 8.6, 16.4, 3.05), (1.2, 1.2, 0.15), BONE, jitter=0.03)
        for sz in (-1, 1):
            horn(p, (sx * 14.6, 24.0, sz * 1.4), sx, 3.6, 1.6, 0.5, BONE, n=3)


# ---- 27. WingBackdrop -----------------------------------------------------------------------------------------------------
def build_WingBackdrop(p):
    frust(p, 0, 0, 28.0, 0, 3.2, 2.4, 2.2, 1.8, BLK)
    skull(p, (0, 30.4, 0.1), 1.5, sub=2, glow=RED)
    for sx in (-1, 1):
        horn(p, (sx * 0.9, 31.6, 0), sx, 2.4, 1.0, 0.4, BONE, n=3)
    for yy in (6, 12, 18, 24):
        bx(p, (-1.9, 1.9), (yy, yy + 0.7), (-1.1, 1.1), RROCK)
    for sx in (-1, 1):
        S0, E, W = (sx * 1.6, 23.0), (sx * 7.4, 32.4), (sx * 17.4, 30.0)
        tips = [(sx * 18.6, 19.0), (sx * 14.6, 10.4), (sx * 8.4, 4.4)]
        for (a, b) in ((S0, E), (E, W)):
            tube(p, (a[0], a[1], 0.5), (b[0], b[1], 0.5), 0.65, 0.5, BONE, 5)
        dk.ball(p, (E[0], E[1], 0.5), 0.9, BONE, subdiv=1)
        for t in tips:
            tube(p, (W[0], W[1], 0.5), (t[0], t[1], 0.5), 0.5, 0.15, BONE, 4)
        cone(p, W[0] + sx * 0.6, W[1] + 0.3, 0.5, 0.35, 1.3, BONE, verts=4)
        tris = [(S0, E, W), (S0, W, tips[0]), (S0, tips[0], tips[1]), (S0, tips[1], tips[2])]
        for (a, b, c) in tris:
            tri_slab(p, [a, b, c], -0.4, 0.3, DRED)
            cx, cy = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
            sh = [(cx + (q[0] - cx) * 0.62, cy + (q[1] - cy) * 0.62) for q in (a, b, c)]
            tri_slab(p, sh, 0.25, 0.42, RED)
        bx(p, (min(S0[0], sx * 4.0) - 0.0, max(S0[0], sx * 4.0)), (22, 23.5), (-0.5, 0.5), BONE)


# ---- 28. DemonThrone ------------------------------------------------------------------------------------------------------
def build_DemonThrone(p):
    bx(p, (-11, 11), (0, 1.2), (-8, 8), ROCK)
    bx(p, (-8.5, 8.5), (1.2, 2.4), (-7, 5), RROCK)
    bx(p, (-1.7, 1.7), (2.4, 2.48), (-3, 5), RED)
    bx(p, (-2.0, 2.0), (2.4, 2.45), (-3, 5), BLK)
    bx(p, (-1.7, 1.7), (2.46, 2.52), (-3, 5), RED)
    bx(p, (-4.5, 4.5), (2.4, 4.8), (-5.6, 1.6), BLK)
    bx(p, (-3.6, 3.6), (4.8, 5.3), (-4.6, 1.0), RED)
    bx(p, (-4.5, 4.5), (5.3, 18.0), (-5.8, -4.0), OBS)
    for yy in (8.0, 11.5, 15.0):
        bx(p, (-3.2, 3.2), (yy, yy + 0.35), (-4.0, -3.8), RED)
    frust(p, 0, 18.0, 19.4, -4.9, 9.4, 2.0, 11.0, 2.6, RROCK)
    skull(p, (0, 20.9, -4.5), 1.9, sub=2, glow=RED)
    for x, h in ((-4.6, 2.8), (-2.3, 3.4), (2.3, 3.4), (4.6, 2.8)):
        cone(p, x, 19.4, -4.9, 0.55, h, BONE, verts=4)
    cone(p, 0, 22.5, -4.9, 0.5, 0.9, BONE, verts=4)
    for sx in (-1, 1):
        horn(p, (sx * 5.2, 19.4, -4.9), sx, 3.9, 2.0, 0.65, BONE, n=4)
        bx(p, (sx * 4.6 - 0.7, sx * 4.6 + 0.7), (4.8, 6.4), (-5.0, 1.6), BLK)
        skull(p, (sx * 4.6, 7.2, 1.6), 0.9, sub=1, yaw=0)
        for sz in (-4.4, -0.8):
            bx(p, (sx * 4.6 - 0.45, sx * 4.6 + 0.45), (2.4, 4.8), (sz - 0.45, sz + 0.45), RROCK)
        bone(p, (sx * 8.6, 2.4, 5.6), (sx * 8.6, 8.4, 5.6), 0.35, BONE, 1.4, 5)
        skull(p, (sx * 8.6, 9.4, 5.6), 1.15, sub=1, yaw=sx * 20)
        cone(p, sx * 9.0, 2.4, 0.0, 0.5, 2.2, BONE, verts=4)
        cone(p, sx * 9.0, 2.4, -4.0, 0.5, 1.8, BONE, verts=4)
    for x in (-9.5, -5, 5, 9.5):
        rock(p, (x, 1.5, 7.0), 0.8, LROCK, squash=0.7, sub=0)


# ---- 29. HellfireSpire ----------------------------------------------------------------------------------------------------
def build_HellfireSpire(p):
    bx(p, (-7, 7), (0, 2.0), (-7, 7), ROCK)
    bx(p, (-6.2, 6.2), (2.0, 2.6), (-6.2, 6.2), RROCK)
    frust(p, 0, 2.6, 14.0, 0, 9.4, 9.4, 8.4, 8.4, OBS)
    bx(p, (-6.0, 6.0), (14.0, 15.2), (-6.0, 6.0), RROCK)
    frust(p, 0, 15.2, 27.0, 0, 7.4, 7.4, 6.4, 6.4, BLK)
    bx(p, (-5.0, 5.0), (27.0, 28.2), (-5.0, 5.0), RROCK)
    frust(p, 0, 28.2, 40.0, 0, 5.2, 5.2, 3.6, 3.6, OBS)
    for (lo, hi, w) in ((2.6, 14.0, 4.5), (15.2, 27.0, 3.7), (28.2, 40.0, 2.5)):
        for yy in (lo + (hi - lo) * 0.25, lo + (hi - lo) * 0.62):
            for (sx, sz) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                dk.box(p, (sx * (w + 0.1), yy, sz * (w + 0.1)), (1.2 if sx == 0 else 0.3, 2.6, 0.3 if sx == 0 else 1.2), RED, jitter=0.03)
    for (y, w) in ((14.0, 5.8), (27.0, 4.8)):
        for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            cone(p, sx * w, y + 1.2, sz * w, 0.5, 1.9, BONE, verts=4)
    for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        horn(p, (sx * 5.4, 2.6, sz * 5.4), sx, 9.0, 1.4, 0.9, OBS, n=4)
    vcyl(p, 0, 40.0, 43.2, 0, 1.4, IRON, verts=8)
    vcyl(p, 0, 43.2, 44.8, 0, 1.8, IRON, verts=8, top_r=3.6)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cone(p, 3.5 * math.cos(a), 44.7, 3.5 * math.sin(a), 0.32, 2.0, BLK, verts=4)
    flame(p, 0, 44.7, 0, 3.0, 6.6, tongues=6)
    for sx in (-1, 1):
        horn(p, (sx * 1.4, 41.0, 0), sx, 2.2, 1.2, 0.4, BONE, n=3)


# ---- 30. HellfirePortal ---------------------------------------------------------------------------------------------------
def build_HellfirePortal(p):
    bx(p, (-15, 15), (0, 1.0), (-6, 6), ROCK)
    bx(p, (-13.5, 13.5), (1.0, 2.0), (-5, 5), RROCK)
    for sx in (-1, 1):
        for k, x in enumerate((9.5, 12.5)):
            skull(p, (sx * x, 2.9, 4.4), 0.9, sub=1, yaw=sx * (10 + 20 * k))
        bx(p, (sx * 7.5 - 1.7, sx * 7.5 + 1.7), (2.0, 7.0), (-1.7, 1.7), BLK)
        bx(p, (sx * 7.5 - 2.0, sx * 7.5 + 2.0), (6.4, 7.2), (-2.0, 2.0), RROCK)
    cy = 16.0
    ring_xy(p, (0, cy, 0), 12.0, 8.7, 3.0, OBS, segs=16, jit=0.07)
    ring_xy(p, (0, cy, 0), 12.4, 11.4, 3.5, RROCK, segs=16, jit=0.05)
    ring_xy(p, (0, cy, 0), 8.8, 8.2, 2.2, LAVA, segs=16, jit=0.03)
    for k in range(12):
        a = 2 * math.pi * k / 12 + 0.26
        dk.box(p, (10.2 * math.cos(a), cy + 10.2 * math.sin(a), 1.55), (0.5, 1.5, 0.2), RED, rot=(0, 0, math.degrees(a) - 90), jitter=0.03)
    for k in range(8):
        a = math.radians(45 * k + 22.5) if k not in () else 0
        if abs(math.sin(a) - 1) < 0.01:
            continue
        r0, r1 = 12.0, 15.0 if abs(math.cos(a)) > 0.5 else 14.0
        tube(p, (r0 * math.cos(a), cy + r0 * math.sin(a), 0), (r1 * math.cos(a), cy + r1 * math.sin(a), 0), 0.85, 0.1, BONE, 5)
    dk.cyl(p, (0, cy, -0.4), 8.4, 0.8, DRED, axis='z', verts=20, jitter=0.03)
    dk.cyl(p, (0, cy, -0.1), 6.2, 0.5, RED, axis='z', verts=18, jitter=0.03)
    for k, (col, z0) in enumerate(((LRED, 0.1), (LAVA, 0.25), (LAVAY, 0.4))):
        spiral(p, (0, cy, 0), 1.0, 8.2, 2 * math.pi * k / 3, 1.1, 2.6, z0, z0 + 0.35, col, n=14)
    dk.cyl(p, (0, cy, 0.6), 1.9, 0.5, LAVAY, axis='z', verts=12, jitter=0.03)
    skull(p, (0, 29.6, 0), 1.6, sub=2, glow=RED)
    for sx in (-1, 1):
        horn(p, (sx * 1.0, 30.8, 0), sx, 1.2, 2.2, 0.45, BONE, n=3)
        horn(p, (sx * 12.0, 20.0, 0), sx, 4.0, 1.4, 0.7, BONE, n=3)


PART_IDS = ["Ground", "Braziers", "HellSign", "SpikeFence", "BoneHeap", "LavaPools", "ObsidianShards", "DeadTrees", "Cauldron",
            "SulfurVents", "ImpStatues", "GatePillars", "SkullTotems", "HellKennel", "IronCages", "RitualCircle", "WarBanners",
            "LavaFountain", "BoneBridge", "RuinedWall", "Watchtower", "DemonStatue", "FireAltar", "LavaMoat", "SkullMountain",
            "GateArch", "WingBackdrop", "DemonThrone", "HellfireSpire", "HellfirePortal"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

AZ = {"GatePillars": 100, "GateArch": 100, "Ground": 165}
ELEV = {}
MULT = {"Ground": 1.7, "HellfireSpire": 2.6, "DemonStatue": 2.3, "GateArch": 2.3, "HellfirePortal": 2.2, "WingBackdrop": 2.4}
SHIBA_AT = {"Ground": (20, -14, 270, 0)}
SHIBA_STUDS = 11.0
EOF_MARK = None


# ---- previews ----------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    # the meshes are mirrored in x before export (decorkit), so the reference Shiba is placed mirrored too
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}}, studs=SHIBA_STUDS)
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
            x = hi[0] + 6 if hi[0] + 6 < 84 else lo[0] - 6
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
    snap(allm, shm, "stage_3q.png", 165, 40, 2.6, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.0, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_HellGate.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
