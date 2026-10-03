"""Final low-poly decor models for the theme DragonLair (30 parts around the 22nd Shiba, Dragon Shiba).

Usage: blender --background --factory-startup --python build_DragonLair.py -- <outdir> [PartId,PartId,...]
Writes Decor_DragonLair_<PartId>.fbx, preview_<PartId>.png and stage_DragonLair.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give a comma-separated part
list after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "DragonLair"))
ONLY = [a for s in ARGS[1:] for a in s.split(",") if a]
KEY = "DragonLair"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_DragonLair.json"))

# ---- palette (one for all 30 parts) ---------------------------------------------------------------------------------
FLOOR = (54, 48, 60)
PATHC = (104, 94, 104)
ROCK = (84, 76, 90)
DROCK = (56, 50, 64)
LROCK = (110, 102, 118)
OBS = (30, 26, 38)
LAVA = (238, 96, 28)
EMBER = (255, 168, 52)
GOLD = (240, 190, 52)
DGOLD = (186, 136, 36)
BONE = (232, 224, 198)
DBONE = (196, 186, 156)
SCALE = (58, 152, 82)
DSCALE = (30, 100, 62)
LSCALE = (96, 190, 110)
EMER = (84, 224, 170)
RUBY = (214, 52, 64)
WOOD = (112, 78, 50)
DWOOD = (80, 56, 38)
IRON = (118, 122, 136)
DIRON = (62, 64, 76)
CLOTH = (176, 42, 52)
STONE = (150, 144, 152)
HAY = (176, 146, 86)
PURPLE = (140, 100, 230)
CREAM = (228, 232, 214)

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
def ry(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


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


# ---- extra helpers ------------------------------------------------------------------------------------------------------
def rbox(p, c, s, col, yaw=0, jit=0.04):
    """Box by centre/size with a yaw about the vertical axis (degrees, Roblox sense)."""
    return dk.box(p, c, s, col, rot=(0, yaw, 0), jitter=jit)


def spike(p, cx, y0, cz, r, h, col, verts=5, top_r=0.0, jit=0.06):
    """Pointed rock spike / horn / crystal: a cone frustum standing on y0."""
    return dk.cyl(p, (cx, y0 + h / 2, cz), r, h, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def tilt(p, c, size, col, rot, jit=0.05):
    return dk.box(p, c, size, col, rot=rot, jitter=jit)


def rock(p, c, r, col, scale=(1, 1, 1), jit=0.08):
    """Chunky rock: a 1-subdivision ico ball."""
    return dk.ball(p, c, r, col, scale=scale, subdiv=1, jitter=jit)


def gemc(p, cx, y0, cz, w, h, col, rot=(0, 0, 0)):
    """Crystal: hexagonal prism with a pointed tip."""
    dk.cyl(p, (cx, y0 + h * 0.35, cz), w / 2, h * 0.7, col, axis='y', verts=6, rot=rot, jitter=0.1)
    c2 = Vector((cx, y0 + h * 0.7 + h * 0.15, cz))
    dk.cyl(p, tuple(c2), w / 2, h * 0.3, col, axis='y', verts=6, top_radius=0.02, rot=rot, jitter=0.1)


def flame(p, cx, y0, cz, w, h, col=LAVA, inner=EMBER):
    """Low-poly flame: two stacked pointed cones (no glow)."""
    spike(p, cx, y0, cz, w / 2, h, col, verts=5, jit=0.05)
    spike(p, cx, y0, cz, w / 3.4, h * 0.62, inner, verts=5, jit=0.04)


import random
RR = random.Random(11)


def frust(p, cx, y0, cz, w0, d0, w1, d1, h, col, yaw=0, ox=0, oz=0, jit=0.05):
    """Tapering block: bottom rect w0 x d0 on y0, top rect w1 x d1 shifted by (ox, oz) at y0 + h; yaw about the base centre."""
    loc = [(-w0 / 2, 0, -d0 / 2), (w0 / 2, 0, -d0 / 2), (w0 / 2, 0, d0 / 2), (-w0 / 2, 0, d0 / 2),
           (ox - w1 / 2, h, oz - d1 / 2), (ox + w1 / 2, h, oz - d1 / 2), (ox + w1 / 2, h, oz + d1 / 2), (ox - w1 / 2, h, oz + d1 / 2)]
    pts = []
    for (x, y, z) in loc:
        a, b = ry(x, z, yaw)
        pts.append((cx + a, y0 + y, cz + b))
    return hexa(p, pts, col, jit)


def disc(p, cx, y0, cz, rx, rz, h, col, verts=16, rtop=1.0, jit=0.04, yaw=0):
    """Elliptic slab / frustum (axis up): radii rx, rz at the bottom, scaled by rtop at the top."""
    pts, faces = [], []
    for k in range(verts):
        a = 2 * math.pi * k / verts
        pts.append((rx * math.cos(a), 0, rz * math.sin(a)))
    for k in range(verts):
        a = 2 * math.pi * k / verts
        pts.append((rx * rtop * math.cos(a), h, rz * rtop * math.sin(a)))
    faces.append(tuple(range(verts)))
    faces.append(tuple(range(2 * verts - 1, verts - 1, -1)))
    for k in range(verts):
        k2 = (k + 1) % verts
        faces.append((k, k2, verts + k2, verts + k))
    return dk.poly(p, (cx, y0, cz), pts, faces, col, jit, rot=(0, yaw, 0))


def rseed(n):
    global RR
    RR = random.Random(n)


def coin_heap(p, cx, cz, R, H, n, seed=1, cr=1.0, y0=0.0, xs=1.0, zs=0.92):
    """Heap of gold: a faceted cone core covered with tilted coins."""
    rr = random.Random(seed)
    disc(p, cx, y0, cz, R * xs, R * zs, H, DGOLD, verts=9, rtop=0.12, jit=0.1, yaw=rr.uniform(0, 40))
    for k in range(n):
        f = rr.uniform(0.1, 0.95)
        a = rr.uniform(0, 6.2832)
        r = R * f
        y = y0 + H * (1 - f) * 0.97 + 0.1
        tiltd = 28 * (1 - 0.4 * f)
        ca, sa = math.cos(a), math.sin(a)
        dk.cyl(p, (cx + r * ca * xs, y, cz + r * sa * zs), cr * rr.uniform(0.8, 1.15), 0.3, rr.choice([GOLD, GOLD, (252, 224, 108), DGOLD]),
               axis="y", verts=6, rot=(tiltd * sa, 0, -tiltd * ca), jitter=0.05)



BOXF = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def lbox(p, o, rot, xr, yr, zr, col, jit=0.04, taper=1.0):
    """Box from ranges relative to origin o, then rotated about o (stage rotation, degrees, Roblox order). taper scales the top ring."""
    pts = []
    for (y, k) in ((yr[0], 1.0), (yr[1], taper)):
        cx, cz = (xr[0] + xr[1]) / 2, (zr[0] + zr[1]) / 2
        hx, hz = (xr[1] - xr[0]) / 2 * k, (zr[1] - zr[0]) / 2 * k
        pts += [(cx - hx, y, cz - hz), (cx + hx, y, cz - hz), (cx + hx, y, cz + hz), (cx - hx, y, cz + hz)]
    return dk.poly(p, o, pts, BOXF, col, jit, rot=rot)


def crystal(p, x, y, z, w, h, col, tilt=(0, 0), yaw=0, sides=6, jit=0.1):
    """Pointed crystal standing on (x, y, z), tilted about its base by tilt = (about x, about z) degrees."""
    pts, faces = [], []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        pts.append((w / 2 * math.cos(a), 0, w / 2 * math.sin(a)))
    for k in range(sides):
        a = 2 * math.pi * k / sides
        pts.append((w / 2 * 0.92 * math.cos(a), h * 0.7, w / 2 * 0.92 * math.sin(a)))
    pts.append((w * 0.08, h, w * 0.05))
    faces.append(tuple(range(sides)))
    for k in range(sides):
        k2 = (k + 1) % sides
        faces.append((k, k2, sides + k2, sides + k))
        faces.append((sides + k, sides + k2, 2 * sides))
    return dk.poly(p, (x, y, z), pts, faces, col, jit, rot=(tilt[0], yaw, tilt[1]))


def skull(p, cx, y0, cz, w, col=BONE, horns=0.0, eyes=EMBER, jaw=True):
    """Dragon / beast skull of width w looking toward +z, standing on y0."""
    dcol = DBONE
    dk.ball(p, (cx, y0 + 0.56 * w, cz - 0.08 * w), 1, col, scale=(0.5 * w, 0.44 * w, 0.5 * w), subdiv=2, jitter=0.04)
    bx(p, (cx - 0.25 * w, cx + 0.25 * w), (y0 + 0.2 * w, y0 + 0.5 * w), (cz + 0.1 * w, cz + 0.62 * w), col, 0.04)
    if jaw:
        bx(p, (cx - 0.22 * w, cx + 0.22 * w), (y0 + 0.04 * w, y0 + 0.2 * w), (cz + 0.05 * w, cz + 0.6 * w), dcol, 0.04)
        for k in range(5):
            x = cx - 0.2 * w + k * 0.1 * w
            bx(p, (x - 0.025 * w, x + 0.025 * w), (y0 + 0.17 * w, y0 + 0.27 * w), (cz + 0.58 * w, cz + 0.63 * w), (250, 246, 230), 0.02)
    for s in (-1, 1):
        bx(p, (cx + s * 0.2 * w - 0.09 * w, cx + s * 0.2 * w + 0.09 * w), (y0 + 0.5 * w, y0 + 0.66 * w), (cz + 0.3 * w, cz + 0.45 * w), OBS, 0.02)
        dk.ball(p, (cx + s * 0.2 * w, y0 + 0.58 * w, cz + 0.45 * w), 0.05 * w, eyes, subdiv=1, jitter=0.02)
        bx(p, (cx + s * 0.09 * w - 0.03 * w, cx + s * 0.09 * w + 0.03 * w), (y0 + 0.4 * w, y0 + 0.46 * w), (cz + 0.6 * w, cz + 0.64 * w), OBS, 0.02)
        if horns:
            dk.cyl(p, (cx + s * 0.55 * w, y0 + 0.76 * w + horns * 0.3, cz - 0.1 * w), 0.07 * w, horns, col, axis='y', verts=5,
                   top_radius=0.0, rot=(0, 0, -s * 55), jitter=0.04)


def tube(p, a, b, r0, r1, col, verts=6, jit=0.04, capb=True):
    """Tapered tube between two stage points (any direction): radius r0 at a, r1 at b (0 = pointed)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    v = d.cross(u).normalized()
    pts, faces = [], []
    for q, r in ((a, r0), (b, r1)):
        for k in range(verts):
            t = 2 * math.pi * k / verts
            pts.append(tuple(q + (u * math.cos(t) + v * math.sin(t)) * r))
    for k in range(verts):
        k2 = (k + 1) % verts
        faces.append((k, k2, verts + k2, verts + k))
    faces.append(tuple(range(verts)))
    if r1 > 0.001:
        faces.append(tuple(range(2 * verts - 1, verts - 1, -1)))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def sheet(p, pts, col, jit=0.04):
    """Flat membrane polygon, visible from both sides (two faces)."""
    n = len(pts)
    dk.poly(p, (0, 0, 0), pts, [tuple(range(n))], col, jit)
    dk.poly(p, (0, 0, 0), pts, [tuple(range(n))[::-1]], col, jit)


def yawgroup(p, i0, cx, cz, deg):
    """Turns every object added to part p since index i0 about the vertical axis through stage (cx, cz); +deg turns +z toward -x."""
    c = S(cx, 0, cz)
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(deg), 4, 'Z') @ Matrix.Translation(-c)
    for o in p.objs[i0:]:
        o.matrix_world = m @ o.matrix_world


# ---- 1. Ground ----------------------------------------------------------------------------------------------------------
def build_Ground(p):
    rseed(1)
    bx(p, (-80, 80), (0, 0.3), (-57.5, 57.5), FLOOR, 0.05)
    for _ in range(22):                                    # lighter and darker rock plates
        x, z = RR.uniform(-76, 76), RR.uniform(-54, 54)
        w, d = RR.uniform(4, 11), RR.uniform(4, 11)
        bx(p, (x - w / 2, x + w / 2), (0.3, 0.33), (z - d / 2, z + d / 2), RR.choice([ROCK, DROCK, (66, 60, 74)]), 0.05, rot=(0, RR.uniform(0, 90), 0))
    # golden plaza of the Dragon Shiba: stepped octagon with a dragon-scale star
    disc(p, -30, 0.3, -6, 13.6, 13.6, 0.12, DGOLD, verts=8, jit=0.03, yaw=22.5)
    disc(p, -30, 0.3, -6, 11.2, 11.2, 0.24, GOLD, verts=8, jit=0.03, yaw=22.5)
    disc(p, -30, 0.54, -6, 9.2, 9.2, 0.01, DGOLD, verts=8, jit=0.02, yaw=22.5)
    star_poly(p, (-30, 0.55, -6), 'xz', 8.4, 4.0, 0.02, DGOLD, n=8, rot0=90)
    star_poly(p, (-30, 0.56, -6), 'xz', 5.2, 2.6, 0.02, GOLD, n=8, rot0=67.5)
    disc(p, -30, 0.54, -6, 1.6, 1.6, 0.01, EMBER, verts=8, jit=0.02)

    # lava streams: dark banks and a bright river
    def river(pts, w):
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            ln = math.hypot(x1 - x0, z1 - z0) + 1.6
            ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
            c = ((x0 + x1) / 2, (z0 + z1) / 2)
            dk.box(p, (c[0], 0.33, c[1]), (ln, 0.1, w + 1.6), DROCK, rot=(0, ang, 0), jitter=0.04)
            dk.box(p, (c[0], 0.38, c[1]), (ln, 0.1, w), LAVA, rot=(0, ang, 0), jitter=0.07)
            dk.box(p, (c[0], 0.44, c[1]), (ln * 0.7, 0.08, w * 0.4), EMBER, rot=(0, ang, 0), jitter=0.05)
    river([(-76.5, -51), (-68, -53.5), (-60, -51), (-52, -53.5), (-43.5, -51.5)], 3.6)
    river([(66, -27), (68.5, -20), (64.5, -14), (68.5, -8), (66, -1)], 4.0)
    river([(-47, -33.5), (-49, -28), (-45.5, -22), (-47, -20.5)], 3.4)
    # path plates: four cobbles each, turned a little
    pts = [(0, 52), (-24, 40), (16, 26), (46, 6), (6, -10), (-8, -34), (30, -44), (0, -52)]
    for i, (x, z) in enumerate(pts):
        yaw = 12 * ((i % 3) - 1)
        for ix in (-1, 1):
            for iz in (-1, 1):
                dx, dz = ry(ix * 2.2, iz * 2.2, yaw)
                bx(p, (x + dx - 2, x + dx + 2), (0.3, 0.52 + 0.04 * ((ix + iz) % 3)), (z + dz - 2, z + dz + 2), PATHC if (ix * iz) > 0 else LROCK, 0.06, rot=(0, yaw, 0))
    # stepping stones along the walkway
    path = [(0, 57.5), (-24, 40), (16, 26), (46, 6), (6, -10), (-8, -34), (30, -44), (0, -57.5)]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        ln = math.hypot(x1 - x0, z1 - z0)
        n = int(ln // 12)
        for k in range(1, n):
            t = k / n
            x, z = x0 + (x1 - x0) * t + RR.uniform(-1.2, 1.2), z0 + (z1 - z0) * t + RR.uniform(-1.2, 1.2)
            if min(math.hypot(x - a, z - b) for a, b in pts) < 6.5:
                continue
            s = RR.uniform(1.8, 2.8)
            bx(p, (x - s / 2, x + s / 2), (0.3, 0.42), (z - s / 2, z + s / 2), PATHC, 0.07, rot=(0, RR.uniform(0, 90), 0))


# ---- 2. Cave ------------------------------------------------------------------------------------------------------------
def build_Cave(p):
    rseed(2)
    # mountain: stacked, rough tiers (octagonal), lighter strata bands, boulders around the foot
    MID = (122, 112, 132)
    disc(p, -68.5, 0, -8, 9.4, 16.2, 9, MID, verts=8, rtop=0.92, jit=0.07, yaw=10)
    disc(p, -68.5, 9, -8, 8.6, 14.8, 7, (146, 136, 156), verts=8, rtop=0.88, jit=0.07, yaw=-6)
    disc(p, -68.7, 16, -8.5, 7.8, 13.4, 6, MID, verts=8, rtop=0.8, jit=0.07, yaw=14)
    disc(p, -69, 22, -9.5, 6.6, 11.6, 4.2, (146, 136, 156), verts=8, rtop=0.74, jit=0.07, yaw=-10)
    rock(p, (-69, 25.4, -10), 1, MID, scale=(5.4, 3.6, 8.6), jit=0.07)
    frust(p, -71, 26.5, -10, 6, 10, 2.2, 3.4, 4.2, ROCK, ox=-1.0, yaw=-8)
    for (x, z, s) in ((-74, -19, 3.6), (-75, -4, 3.4), (-70, 6, 3.0), (-72, -24, 2.6), (-63.5, -21.5, 2.4)):
        rock(p, (x, 1.5, z), 1, DROCK, scale=(s, s * 0.65, s), jit=0.08)
    bx(p, (-62.4, -58.6), (0, 14.2), (-18, -1), (128, 118, 138), 0.06)          # front wall around the mouth
    # buttresses beside the mouth
    frust(p, -60.5, 0, -19.5, 9, 10, 5.5, 6, 16, (100, 92, 112), yaw=14, ox=-1, jit=0.07)
    frust(p, -61, 0, 5, 8, 11, 5, 6.5, 14, (100, 92, 112), yaw=-16, ox=-1, jit=0.07)
    # cave mouth: pillars, lintel with fangs, dark opening and a lava glow far inside
    bx(p, (-59.8, -58.6), (0, 13), (-15.6, -3.4), OBS, 0.03)
    bx(p, (-59.4, -58.2), (0.5, 9.0), (-14.0, -5.0), LAVA, 0.05)
    bx(p, (-59.0, -58.2), (0.5, 5.2), (-12.2, -6.8), EMBER, 0.04)
    for z in (-16.8, -2.2):
        bx(p, (-59.8, -56.6), (0, 16.2), (z - 1.7, z + 1.7), (150, 140, 160), 0.06)
        bx(p, (-60.2, -57.2), (13.4, 14.4), (z - 2.1, z + 2.1), DROCK, 0.05)
    bx(p, (-59.8, -56.2), (15.1, 18.5), (-18.8, -0.2), (96, 88, 108), 0.05)
    for z, h in ((-14.2, 3.0), (-11.8, 2.4), (-9.5, 3.2), (-7.2, 2.4), (-4.8, 3.0)):
        dk.cyl(p, (-57.7, 15.1 - h / 2, z), 0.12, h, BONE, axis="y", verts=5, top_radius=0.75, jitter=0.05)
    for z in (-12.8, -6.2):                                  # floor fangs
        spike(p, -57.9, 0, z, 0.5, 1.6, BONE, verts=5)
    # bone brow ridge over the mouth with spikes, big floor fangs, spiky crown
    bx(p, (-59.6, -56.4), (18.5, 19.7), (-19.6, 0.6), BONE, 0.05)
    for z in (-18.0, -13.5, -9.5, -5.5, -1.0):
        spike(p, -58.0, 19.7, z, 0.7, 2.2, BONE, verts=5, jit=0.05)
    for z, h in ((-14.6, 2.6), (-10.9, 3.0), (-8.1, 3.0), (-4.5, 2.6)):
        spike(p, -57.6, 0, z, 0.75, h, BONE, verts=5, jit=0.05)
    for k in range(7):
        a = k * 0.9 + 0.3
        spike(p, -69 + 5.2 * math.cos(a), 27.2 + 0.4 * (k % 2), -10 + 8.0 * math.sin(a), 0.9, 2.4 + (k % 3) * 0.6, (96, 88, 108), verts=4, jit=0.08)
    # rubble at the foot
    rock(p, (-57.5, 0.7, -21.5), 1, ROCK, scale=(2.6, 1.4, 2.2))
    rock(p, (-56.5, 0.6, 3.5), 1, DROCK, scale=(2.2, 1.2, 2.6))
    rock(p, (-56.0, 0.5, -9.5), 1, ROCK, scale=(1.4, 0.9, 1.8))
    # horns on the crown
    frust(p, -74, 22, -20, 5, 5, 0.5, 0.5, 10.5, DBONE, ox=1.5, oz=-1.5, jit=0.08)
    frust(p, -73, 23, 3, 4.4, 4.4, 0.4, 0.4, 10, DBONE, ox=-1.2, oz=1.2, jit=0.08)


# ---- 3. Hoard -----------------------------------------------------------------------------------------------------------
def build_Hoard(p):
    rseed(3)
    golds = [GOLD, DGOLD, (252, 222, 104), GOLD]

    def nuggets(cx, cz, R, rings, y0, rr_):
        k = 0
        for (rad, n, y, s) in rings:
            for i in range(n):
                a = i * 6.2832 / n + rr_.uniform(-0.3, 0.3) + rad
                dk.ball(p, (cx + rad * R * math.cos(a), y0 + y, cz + rad * R * 0.92 * math.sin(a)), 1, golds[k % 4],
                        scale=(s * 1.2, s * 0.8, s * 1.1), subdiv=1, jitter=0.1)
                k += 1
    r3 = random.Random(3)
    nuggets(-48, -8, 1.0, [(4.3, 8, 1.1, 2.1), (2.6, 5, 2.7, 1.9), (1.2, 3, 4.1, 1.6), (0.0, 1, 5.1, 1.6)], 0, r3)
    nuggets(-47, -1.6, 1.0, [(2.2, 4, 0.9, 1.6), (0.0, 1, 1.9, 1.5)], 0, r3)
    nuggets(-51, -14, 1.0, [(2.4, 4, 0.9, 1.7), (0.0, 1, 2.0, 1.5)], 0, r3)
    nuggets(-44, -13, 1.0, [(1.4, 3, 0.8, 1.2)], 0, r3)
    for _ in range(22):
        a = RR.uniform(0, 6.28)
        r = RR.uniform(0.6, 6.4)
        x, z = -48 + r * math.cos(a) * 1.0, -8 + r * math.sin(a) * 0.95
        y = max(0.8, 6.0 - r * 0.7)
        dk.cyl(p, (x, y, z), RR.uniform(0.85, 1.3), 0.25, RR.choice([GOLD, GOLD, (252, 224, 108), DGOLD]), axis='y', verts=6,
               rot=(RR.uniform(-40, 40), 0, RR.uniform(-40, 40)), jitter=0.05)
    # chests spilling gold
    for (x, z, yw) in ((-45.5, -17, 25), (-52.5, -3, -30)):
        rbox(p, (x, 1.2, z), (4, 2.4, 2.8), WOOD, yw)
        rbox(p, (x, 2.8, z), (4.1, 0.8, 2.9), DWOOD, yw)
        rbox(p, (x, 1.3, z), (0.8, 2.6, 2.9), GOLD, yw)
        rbox(p, (x, 3.4, z), (3.2, 0.5, 2.2), GOLD, yw)
    vcyl(p, -43, 0, 1.4, -5, 0.45, DGOLD, verts=8, top_r=0.2)
    vcyl(p, -43, 1.4, 2.8, -5, 0.2, DGOLD, verts=8, top_r=0.8)                 # goblet
    gemc(p, -49, 6.0, -9, 1.8, 2.6, RUBY)
    gemc(p, -46, 5.0, -6, 1.5, 2.0, EMER)
    gemc(p, -51.5, 4.0, -11.5, 1.3, 1.8, EMER)
    gemc(p, -42.8, 0.2, -10, 1.0, 1.6, RUBY)
    # crown on top
    vcyl(p, -48, 6.9, 7.9, -8, 1.3, GOLD, verts=8, top_r=1.45)
    for k in range(5):
        a = k * 1.2566
        spike(p, -48 + 1.2 * math.cos(a), 7.9, -8 + 1.2 * math.sin(a), 0.38, 0.9, GOLD, verts=4, jit=0.03)
    ball(p, (-48, 8.45, -8), 0.34, RUBY, subdiv=1)


# ---- 4. Braziers --------------------------------------------------------------------------------------------------------
def build_Braziers(p):
    rseed(4)
    for (x, z, h, a) in ((10, 52, 9, 0), (17, 46, 7, 25), (5, 44, 6, -20)):
        frust(p, x, 0, z, 3.6, 3.6, 2.6, 2.6, 0.9, ROCK, yaw=a + 20)
        vcyl(p, x, 0.9, h, z, 0.4, DIRON, verts=6, top_r=0.32)
        for k in range(3):                                   # tripod feet
            ang = k * 2.0944 + math.radians(a)
            dk.cyl(p, (x + 1.0 * math.cos(ang), 1.9, z + 1.0 * math.sin(ang)), 0.14, 2.2, DIRON, axis='y', verts=4, jitter=0.03)
        vcyl(p, x, h - 0.2, h + 0.5, z, 0.7, IRON, verts=8, top_r=0.9)
        vcyl(p, x, h + 0.5, h + 1.4, z, 1.6, IRON, verts=10, top_r=2.2)       # bowl
        vcyl(p, x, h + 1.3, h + 1.42, z, 2.0, DIRON, verts=10)                # coals
        flame(p, x, h + 1.4, z, 2.8, 2.9)
        spike(p, x + 0.9, h + 1.4, z - 0.5, 0.6, 2.0, LAVA, verts=4)
        spike(p, x - 0.8, h + 1.4, z + 0.6, 0.5, 1.5, EMBER, verts=4)
    rock(p, (13.5, 0.8, 49.5), 1, DROCK, scale=(1.7, 0.8, 1.5))
    rock(p, (8, 0.7, 47.5), 1, ROCK, scale=(1.2, 0.7, 1.2))
    rock(p, (14, 0.4, 53), 1, ROCK, scale=(1.2, 0.5, 1.1))


# ---- 5. Hatchery --------------------------------------------------------------------------------------------------------
def build_Hatchery(p):
    rseed(5)
    disc(p, -50, 0, 47, 6.6, 6.6, 1.3, HAY, verts=14, rtop=0.95, jit=0.08)
    for k in range(5):                                       # hay straws
        a = RR.uniform(0, 6.28)
        dk.box(p, (-50 + 3 * math.cos(a), 1.35, 47 + 3 * math.sin(a)), (2.4, 0.1, 0.3), (210, 180, 110), rot=(0, math.degrees(a) * 2, 0), jitter=0.04)
    for k in range(10):                                      # twig wall
        a = math.radians(k * 36 + 10)
        x, z = -50 + 7.4 * math.cos(a), 47 + 7.4 * math.sin(a)
        yw = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        rbox(p, (x, 1.4, z), (6.0, 1.4, 1.1), WOOD if k % 2 else DWOOD, yw, 0.08)
        rbox(p, (x * 0.995 - 0.25 * math.cos(a), 2.3, z), (5.2, 0.7, 0.9), DWOOD if k % 2 else WOOD, yw + 14, 0.08)
    for k in range(6):                                       # twigs sticking out
        a = math.radians(k * 60 + 25)
        x, z = -50 + 7.6 * math.cos(a), 47 + 7.6 * math.sin(a)
        dk.box(p, (x, 2.0, z), (3.2, 0.3, 0.3), DWOOD, rot=(0, -math.degrees(a) + 30, 12), jitter=0.05)
    for (x, z, y, rx, ry_, col) in ((-50.5, 47.5, 4.0, 2.7, 3.8, SCALE), (-47, 50, 3.3, 2.3, 3.1, DSCALE), (-53, 44.5, 3.1, 2.2, 3.0, GOLD)):
        dk.ball(p, (x, y, z), 1, col, scale=(rx, ry_, rx), subdiv=2, jitter=0.05)
        for k in range(5):                                   # speckles
            a = k * 1.3 + x
            dk.ball(p, (x + rx * 0.82 * math.cos(a), y + (k - 2) * ry_ * 0.27, z + rx * 0.82 * math.sin(a)), 0.38,
                    DSCALE if col == GOLD else CREAM, subdiv=1, jitter=0.03)
    dk.ball(p, (-49, 5.6, 45.2), 0.45, EMBER, subdiv=1)
    dk.ball(p, (-51.8, 6.4, 49), 0.45, EMBER, subdiv=1)
    spike(p, -50.5, 7.0, 47.5, 0.5, 0.8, EMBER, verts=4)


# ---- 6. Stalagmites -----------------------------------------------------------------------------------------------------
def build_Stalagmites(p):
    rseed(6)
    spikes = [(-22, -49, 4.6, 17, 10), (-27, -47, 3.8, 12, -20), (-18, -46, 3.4, 9, 35), (-30, -51, 3, 7, 0), (-15, -50, 2.6, 6, 25)]
    for (x, z, w, h, r) in spikes:
        dk.cyl(p, (x, h * 0.3, z), w * 0.62, h * 0.6, ROCK, axis='y', verts=7, top_radius=w * 0.38, jitter=0.07, rot=(0, r, 0))
        dk.cyl(p, (x, h * 0.6 + h * 0.2, z), w * 0.38, h * 0.4, (92, 84, 108), axis='y', verts=7, top_radius=0.0, jitter=0.07, rot=(0, r + 15, 0))
    for (x, z, w, h) in ((-24.5, -43.5, 1.5, 3.4), (-19.5, -42.5, 1.3, 2.6), (-29, -44.5, 1.2, 2.2), (-13.8, -45, 1.3, 2.6), (-26, -52.3, 1.4, 3.0)):
        spike(p, x, 0, z, w * 0.7, h, LROCK, verts=5, jit=0.08)
    rock(p, (-20, 1.6, -49), 1, DROCK, scale=(4.5, 1.6, 4), jit=0.08)
    rock(p, (-28, 1.2, -44), 1, ROCK, scale=(3, 1.2, 3), jit=0.08)
    rock(p, (-15.5, 0.8, -47), 1, ROCK, scale=(2, 0.9, 2.2), jit=0.08)
    for (x, z, ln, yw) in ((-24.0, -43.0, 6.0, 15), (-17.0, -43.8, 4.0, -25), (-29.0, -47.5, 3.5, 70)):
        rbox(p, (x, 0.1, z), (ln, 0.2, 0.6), LAVA, yw, 0.05)
        rbox(p, (x, 0.2, z), (ln * 0.6, 0.12, 0.3), EMBER, yw, 0.04)


# ---- 7. Ribs ------------------------------------------------------------------------------------------------------------
def build_Ribs(p):
    rseed(7)
    # spine with vertebrae and a short tail
    tube(p, (54.8, 1.6, 10), (73.5, 1.4, 10), 0.55, 0.3, DBONE, verts=5)
    for k in range(10):
        x = 56.5 + k * 1.75
        bx(p, (x - 0.65, x + 0.65), (1.4, 2.6), (9.4, 10.6), BONE, 0.05)
        spike(p, x, 2.6, 10, 0.25, 0.7, DBONE, verts=4)
    heights = [10.4, 10.0, 9.2, 8.0, 6.4]
    prof = [(0.9, 1.4), (3.6, 3.0), (5.6, 6.0), (5.0, 8.8), (2.6, 10.3)]
    for i in range(5):
        x = 57.5 + 3.4 * i
        h = heights[i]
        for s in (-1, 1):
            q = [(10 + s * zz, 0.6 + yy * (h - 0.6) / 10.3) for (zz, yy) in prof]
            for j in range(len(q) - 1):
                r0 = 0.62 - 0.1 * j
                r1 = 0.62 - 0.1 * (j + 1)
                tube(p, (x, q[j][1], q[j][0]), (x, q[j + 1][1], q[j + 1][0]), r0, max(r1, 0.12), BONE if j % 2 == 0 else DBONE, verts=5, jit=0.04)
    # skull of the beast at the head end, looking along the spine
    i0 = len(p.objs)
    skull(p, 0, 0.0, 0, 4.4, horns=2.6, eyes=LAVA)
    # move the skull from the origin to its place (x 52.6..56), turn it to face -x
    mv = Matrix.Translation(S(55.2, 0.4, 10.0)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    for o in p.objs[i0:]:
        o.matrix_world = mv @ o.matrix_world


# ---- 8. LavaPool --------------------------------------------------------------------------------------------------------
def build_LavaPool(p):
    rseed(8)
    disc(p, 24, 0, -24, 11.2, 8.4, 0.5, DROCK, verts=16, jit=0.04)
    disc(p, 24, 0.5, -24, 9.8, 7.0, 0.05, LAVA, verts=16, jit=0.06)
    disc(p, 24, 0.55, -24, 6.4, 4.4, 0.04, EMBER, verts=12, jit=0.06)
    for (x, z, r, c) in ((23, -24, 1.2, LAVA), (27, -22.5, 0.9, EMBER), (20, -25.5, 0.8, EMBER), (26.5, -26.5, 1.1, EMBER)):
        dk.ball(p, (x, 0.75, z), 1, c, scale=(r, 0.5, r), subdiv=1, jitter=0.05)       # bubbles
    for k in range(10):
        a = math.radians(k * 36)
        x, z = 24 + 9.5 * math.cos(a), -24 + 7.4 * math.sin(a)
        h = 2 + (k % 3) * 0.8
        frust(p, x, 0, z, 4.2, 3.6, 1.6, 1.4, h + 0.6, ROCK if k % 2 else LROCK, yaw=-math.degrees(a), ox=0.5 * (k % 3 - 1), jit=0.1)
    for k in range(5):
        a = math.radians(k * 72 + 20)
        rock(p, (24 + 12 * math.cos(a), 0.5, -24 + 9.6 * math.sin(a)), 1, DROCK, scale=(1.6, 0.8, 1.4))


# ---- 9. SkullGate -------------------------------------------------------------------------------------------------------
def build_SkullGate(p):
    rseed(9)
    for x, yw in ((-4, 10), (20, -12)):
        frust(p, x, 0, 28.8, 6.2, 6.2, 4.2, 4.2, 1.4, ROCK, yaw=yw, jit=0.07)
        for k, (r, h) in enumerate(((1.7, 2.2), (2.0, 0.6), (1.7, 2.0), (2.0, 0.6), (1.7, 1.8), (2.1, 0.8))):
            y0 = 1.4 + sum(hh for _, hh in ((1.7, 2.2), (2.0, 0.6), (1.7, 2.0), (2.0, 0.6), (1.7, 1.8), (2.1, 0.8))[:k])
            disc(p, x, y0, 28.8, r, r, h, BONE if k % 2 == 0 else DBONE, verts=8, jit=0.05, yaw=k * 17)
        rock(p, (x + (2.2 if x < 0 else -2.2), 0.8, 30.8), 1, DROCK, scale=(1.5, 0.9, 1.3))
    # lintel: a giant bone with knobbed ends, fangs hanging below
    xcyl(p, -5.4, 21.4, 9.9, 28.8, 1.3, BONE, verts=8)
    for x in (-5.8, 21.8):
        ball(p, (x, 9.9, 28.8), 1.9, BONE, scale=(1, 1.1, 1.3), subdiv=1)
    bx(p, (-4, 20), (8.4, 9.2), (27.6, 30.0), DBONE, 0.05)
    for x in (0, 3, 6, 10, 13, 16):
        spike(p, x, 7.0, 28.8, 0.5, 1.9, BONE, verts=5, jit=0.04)
        dk.cyl(p, (x, 7.95, 28.8), 0.04, 1.9, BONE, axis='y', verts=3, top_radius=0.5)
    # skulls on top
    skull(p, 8, 10.6, 28.0, 4.8, horns=3.0)
    skull(p, -1.6, 11.0, 28.6, 3.0, horns=1.6)
    skull(p, 17.6, 11.0, 28.6, 3.0, horns=1.6)
    # crossed tusks
    for s in (-1, 1):
        dk.cyl(p, (8 + s * 5.2, 12.9, 29.6), 0.5, 5.0, BONE, axis='y', verts=5, top_radius=0.05, rot=(0, 0, -s * 28), jitter=0.04)
    # hanging fire bowls
    for x in (3, 13):
        dk.cyl(p, (x, 8.6, 28.8), 0.05, 1.2, DIRON, axis='y', verts=3, top_radius=0.1)
        ball(p, (x, 7.6, 28.8), 0.9, DIRON, scale=(1, 0.8, 1), subdiv=1)
        spike(p, x, 7.9, 28.8, 0.55, 1.4, LAVA, verts=5)


# ---- 10. Crystals -------------------------------------------------------------------------------------------------------
def build_Crystals(p):
    rseed(10)
    rock(p, (-66, 1.6, 50), 1, DROCK, scale=(7, 1.7, 5), jit=0.08)
    rock(p, (-70.5, 1.0, 48), 1, ROCK, scale=(2.6, 1.0, 2.4), jit=0.08)
    rock(p, (-61, 0.9, 52.5), 1, ROCK, scale=(2.4, 0.9, 2.0), jit=0.08)
    specs = [(-66, 50, 3.6, 14, (4, -6), EMER), (-70, 51, 2.8, 9.4, (-6, 10), EMER), (-62, 48.5, 3.0, 8.6, (8, -8), EMER),
             (-68, 46.5, 2.2, 5.6, (-10, 14), EMER), (-63, 53, 2.0, 5.0, (6, -18), EMER), (-72, 47, 1.8, 4.0, (-8, 12), EMER),
             (-59, 51, 1.6, 3.4, (10, -20), EMER), (-65.5, 53.5, 1.7, 3.8, (-4, 16), RUBY), (-66.5, 50.5, 2.0, 7, (-3, 4), (60, 200, 150))]
    for (x, z, w, h, t, c) in specs:
        crystal(p, x, 1.0 if h > 4 else 0.7, z, w, h, c, tilt=t, yaw=RR.uniform(0, 60))
    for k in range(5):
        crystal(p, -66 + RR.uniform(-6, 6), 0.8, 50 + RR.uniform(-3.5, 3.5), 0.8, RR.uniform(1.2, 2.2), (150, 255, 220), tilt=(RR.uniform(-25, 25), RR.uniform(-25, 25)))


# ---- 11. Armory ---------------------------------------------------------------------------------------------------------
def armor(p, x, z, yaw, lean=0):
    o = (x, 0, z)
    lbox(p, o, (0, yaw, 0), (-1.5, 1.5), (0, 0.5), (-1.2, 1.2), DROCK, 0.05)                 # plinth
    for s in (-0.55, 0.55):
        lbox(p, o, (0, yaw, lean), (s - 0.4, s + 0.4), (0.5, 3.0), (-0.5, 0.5), IRON, 0.06)  # legs
    lbox(p, o, (0, yaw, lean), (-1.0, 1.0), (3.0, 3.6), (-0.7, 0.7), DIRON, 0.05)           # belt
    lbox(p, o, (0, yaw, lean), (-1.3, 1.3), (3.6, 6.0), (-0.8, 0.8), IRON, 0.06, taper=1.2)  # chest
    lbox(p, o, (0, yaw, lean), (-0.5, 0.5), (4.6, 5.0), (0.8, 1.0), CLOTH, 0.04)             # tabard stripe
    for s in (-1, 1):
        dk.ball(p, (x + s * 1.8 * math.cos(math.radians(yaw)), 5.6, z - s * 1.8 * math.sin(math.radians(yaw))), 0.95, (150, 154, 168), scale=(1, 0.8, 1), subdiv=1)
        lbox(p, o, (0, yaw, lean + s * 8), (s * 1.8 - 0.35, s * 1.8 + 0.35), (3.0, 5.3), (-0.4, 0.4), IRON, 0.06)
    dk.ball(p, (x, 7.1, z), 1.0, (150, 154, 168), scale=(1, 1.1, 1), subdiv=1)
    lbox(p, (x, 7.1, z), (0, yaw, 0), (-0.7, 0.7), (-0.15, 0.15), (0.75, 1.0), OBS, 0.02)    # visor slit
    spike(p, x, 8.0, z, 0.35, 0.8, CLOTH, verts=4)
    lbox(p, o, (0, yaw, lean), (-1.15, 1.15), (1.2, 5.8), (-1.25, -0.8), (130, 34, 44), 0.05, taper=0.8)          # tattered cape
    lbox(p, o, (0, yaw, lean), (0.2, 1.0), (3.0, 3.9), (0.8, 0.95), (148, 100, 72), 0.05)                         # rust
    lbox(p, o, (0, yaw, lean), (-1.1, -0.3), (1.0, 1.9), (0.5, 0.65), (148, 100, 72), 0.05)
    lbox(p, o, (0, yaw, lean), (2.0, 2.3), (0.4, 3.6), (0.7, 1.0), (206, 212, 226), 0.04)                          # sword in hand
    lbox(p, o, (0, yaw, lean), (1.7, 2.6), (3.6, 3.9), (0.6, 1.1), DGOLD, 0.04)


def build_Armory(p):
    rseed(11)
    armor(p, -75, 25, -15, 4)
    armor(p, -71, 30, 10, -6)
    # a fallen suit
    RUST = (148, 100, 72)
    lbox(p, (-68.0, 0.2, 25.5), (0, 25, 8), (-1.4, 1.4), (0, 2.3), (-1.2, 1.2), IRON, 0.06, taper=0.9)          # chest plate lying on its back
    lbox(p, (-68.0, 0.2, 25.5), (0, 25, 8), (-0.6, 0.6), (2.3, 2.5), (-0.5, 0.5), RUST, 0.05)
    lbox(p, (-65.9, 0.1, 24.4), (0, 40, 0), (0, 3.0), (0, 0.9), (-0.5, 0.5), DIRON, 0.06)                          # leg
    lbox(p, (-65.9, 0.1, 26.8), (0, 5, 0), (0, 3.0), (0, 0.9), (-0.5, 0.5), IRON, 0.06)
    dk.ball(p, (-63.9, 1.0, 28.0), 1.0, (150, 154, 168), scale=(1, 1.1, 1), subdiv=1)                             # helmet rolled away
    lbox(p, (-63.9, 1.0, 28.0), (0, 0, 0), (-0.7, 0.7), (-0.15, 0.15), (0.75, 1.0), OBS, 0.02)
    # dented shield and spear
    dk.cyl(p, (-72, 0.3, 26.4), 1.8, 0.35, DGOLD, axis='y', verts=10, jitter=0.05)
    dk.cyl(p, (-72, 0.55, 26.4), 0.5, 0.2, GOLD, axis='y', verts=8)
    lbox(p, (-71.2, 0, 31.2), (8, 0, 10), (-0.2, 0.2), (0, 8.0), (-0.2, 0.2), WOOD, 0.04)
    spike(p, -71.2 - 1.2, 7.6, 31.5, 0.35, 1.0, IRON, verts=4)
    dk.cyl(p, (-68.5, 1.5, 29.5), 1.7, 0.3, DGOLD, axis="z", verts=10, rot=(-18, 20, 0), jitter=0.05)
    dk.cyl(p, (-68.5, 1.5, 29.7), 0.5, 0.3, GOLD, axis="z", verts=8, rot=(-18, 20, 0), jitter=0.05)
    rock(p, (-66.5, 0.5, 31.8), 1, ROCK, scale=(1.6, 0.6, 1.2))
    rock(p, (-74.5, 0.5, 31), 1, DROCK, scale=(1.4, 0.5, 1.4))


# ---- 12. Chests ---------------------------------------------------------------------------------------------------------
def chest(p, x, z, w, h, yaw, open_deg=0, col=WOOD, lcol=DWOOD):
    o = (x, 0, z)
    d = w * 0.35
    lbox(p, o, (0, yaw, 0), (-w / 2, w / 2), (0, h), (-d, d), col, 0.05)
    for s in (-1, 1):
        lbox(p, o, (0, yaw, 0), (s * w * 0.36 - 0.28, s * w * 0.36 + 0.28), (-0.02, h + 0.02), (-d - 0.06, d + 0.06), GOLD, 0.03)
    lbox(p, o, (0, yaw, 0), (-0.45, 0.45), (h * 0.5, h * 0.82), (d, d + 0.14), GOLD, 0.03)    # lock
    if open_deg:
        hinge = (x - 0 * 1, h, z)
        # lid swung open about the back edge (z - d)
        a = math.radians(yaw)
        bxo, bzo = ry(0, -d, yaw)
        lbox(p, (x + bxo, h, z + bzo), (-open_deg, yaw, 0), (-w / 2, w / 2), (0, 0.7), (0, 2 * d), lcol, 0.05)
        coin_heap(p, x, z, w * 0.4, 1.2, 4, seed=int(w * 10), cr=0.6, y0=h - 0.2)
    else:
        lbox(p, o, (0, yaw, 0), (-w / 2 - 0.05, w / 2 + 0.05), (h, h + 0.6), (-d - 0.05, d + 0.05), lcol, 0.05, taper=0.9)
        lbox(p, o, (0, yaw, 0), (-w / 2 + 0.3, w / 2 - 0.3), (h + 0.6, h + 1.0), (-d + 0.3, d - 0.3), lcol, 0.05)


def build_Chests(p):
    rseed(12)
    chest(p, -46, 26.5, 5.0, 3.2, 20, open_deg=11)
    chest(p, -41.5, 30, 3.8, 2.6, -30)
    chest(p, -42.5, 24.8, 3.0, 2.2, 12, open_deg=16)
    for (x, z, r) in ((-44.5, 29.5, 1.5), (-48.5, 24.5, 1.3)):
        coin_heap(p, x, z, r * 1.2, 1.5, 4, seed=int(x), cr=0.7)
    for (x, z) in ((-39.5, 27), (-40, 33), (-47.5, 31.5), (-44, 22.8)):
        dk.cyl(p, (x, 0.2, z), 0.7, 0.25, GOLD, axis='y', verts=6, jitter=0.05)
    dk.cyl(p, (-39.3, 0.55, 29.5), 0.3, 1.0, DGOLD, axis='y', verts=6, top_radius=0.6)
    gemc(p, -46.5, 2.6, 27.5, 0.9, 1.2, RUBY)
    gemc(p, -45.2, 2.0, 25.2, 0.8, 1.0, EMER)


# ---- 13. Swords ---------------------------------------------------------------------------------------------------------
def sword(p, x, z, h, tx, tz, base=0.6):
    """Sword stuck in the rubble tip-down; h = total height above the rubble, tilted about its tip."""
    o = (x, base - 0.3, z)
    L = h - 2.9
    pts = [(0, 0, 0), (-0.22, L * 0.25, -0.08), (0.22, L * 0.25, -0.08), (0.22, L * 0.25, 0.08), (-0.22, L * 0.25, 0.08),
           (-0.38, L, -0.13), (0.38, L, -0.13), (0.38, L, 0.13), (-0.38, L, 0.13)]
    faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (1, 2, 6, 5), (2, 3, 7, 6), (3, 4, 8, 7), (4, 1, 5, 8), (5, 6, 7, 8)]
    dk.poly(p, o, pts, faces, (206, 212, 226), 0.05, rot=(tx, 0, tz))
    lbox(p, o, (tx, 0, tz), (-0.07, 0.07), (L * 0.3, L * 0.95), (-0.15, 0.15), (150, 156, 174), 0.03)
    lbox(p, o, (tx, 0, tz), (-1.5, 1.5), (L, L + 0.5), (-0.35, 0.35), DGOLD, 0.04)
    lbox(p, o, (tx, 0, tz), (-0.22, 0.22), (L + 0.5, L + 2.2), (-0.22, 0.22), WOOD, 0.04)
    lbox(p, o, (tx, 0, tz), (-0.4, 0.4), (L + 2.2, L + 2.9), (-0.4, 0.4), GOLD, 0.04)


def build_Swords(p):
    rseed(13)
    disc(p, 26, 0, 49, 6.4, 3.4, 1.0, ROCK, verts=10, rtop=0.92, jit=0.08)
    rock(p, (25, 1, 48), 1, DROCK, scale=(2.6, 1.2, 2.0), jit=0.08)
    rock(p, (29.5, 0.7, 50.5), 1, ROCK, scale=(1.6, 0.8, 1.4), jit=0.08)
    rock(p, (22, 0.6, 50), 1, LROCK, scale=(1.4, 0.7, 1.2), jit=0.08)
    for (x, z, h, tx, tz) in ((22, 47.5, 9, 5, -8), (25, 51, 7.4, -6, 6), (29, 47, 10, 4, 10), (27, 53, 6, -8, -5), (20, 51.5, 6.6, 7, 4), (31, 51, 8, -4, -12)):
        sword(p, x, z, h + 1.0, tx, tz)
    rock(p, (31.5, 0.5, 48.5), 1, DROCK, scale=(1.0, 0.5, 1.0))


# ---- 14. Forge ----------------------------------------------------------------------------------------------------------
def build_Forge(p):
    rseed(14)
    bx(p, (39, 53), (0, 9), (43, 53), (168, 160, 170), 0.06)
    for k in range(5):                                           # stone courses
        bx(p, (38.8, 53.2), (k * 1.8 + 0.7, k * 1.8 + 0.85), (42.8, 53.2), (130, 122, 134), 0.03)
    bx(p, (38.7, 39.7), (0, 9), (42.7, 53.3), (112, 104, 120), 0.05)
    bx(p, (52.3, 53.3), (0, 9), (42.7, 53.3), (112, 104, 120), 0.05)
    frust(p, 46, 9.0, 48, 17.0, 12.4, 12.0, 8.0, 1.8, (92, 96, 114), jit=0.05)                # slate roof
    frust(p, 46, 10.8, 48, 12.0, 8.0, 10.0, 1.2, 0.8, (110, 114, 134), jit=0.05)
    frust(p, 51.5, 9.8, 50.5, 3.4, 3.4, 2.6, 2.6, 10.2, (104, 96, 112), jit=0.07)               # chimney
    bx(p, (49.8, 53.2), (19.4, 20.0), (48.8, 52.2), DROCK, 0.05)
    dk.ball(p, (51.5, 20.4, 50.5), 1, (80, 74, 84), scale=(1.4, 0.5, 1.4), subdiv=1, jitter=0.04)
    # furnace mouth (arch frame + lava + ember)
    bx(p, (42.7, 43.6), (0, 5.0), (42.3, 43.2), DROCK, 0.05)
    bx(p, (48.4, 49.3), (0, 5.0), (42.3, 43.2), DROCK, 0.05)
    bx(p, (42.7, 49.3), (4.2, 5.2), (42.3, 43.2), DROCK, 0.05)
    bx(p, (43.6, 48.4), (0.3, 4.2), (42.7, 43.2), OBS, 0.03)
    bx(p, (43.8, 48.2), (0.4, 3.6), (42.45, 42.9), LAVA, 0.05)
    bx(p, (44.7, 47.3), (0.5, 2.2), (42.35, 42.8), EMBER, 0.05)
    for fx in (44.2, 46.0, 47.8):
        spike(p, fx, 0.4, 42.6, 0.5, 1.9, EMBER, verts=4)
    # door
    bx(p, (39.4, 42.6), (0, 6.2), (42.7, 43.3), DWOOD, 0.05)
    bx(p, (40.9, 41.1), (0, 6.2), (43.2, 43.4), DIRON, 0.03)
    # anvil on a stump
    bx(p, (35.2, 37.8), (0, 1.8), (42.3, 44.7), DWOOD, 0.05)
    frust(p, 36.5, 1.8, 43.5, 2.2, 1.4, 3.8, 1.8, 1.0, DIRON, jit=0.04)
    bx(p, (34.0, 35.4), (2.4, 2.9), (43.0, 44.0), DIRON, 0.04)
    rbox(p, (36.5, 3.0, 43.5), (2.4, 0.3, 0.5), (230, 120, 60), 0, 0.03)
    # coal barrel and tools
    vcyl(p, 54.8, 0, 3.2, 50.5, 1.2, WOOD, verts=9, top_r=1.1)
    vcyl(p, 54.8, 3.1, 3.4, 50.5, 1.0, DIRON, verts=9)
    for k in range(4):
        dk.ball(p, (54.8 + (k % 2 - 0.5) * 0.9, 3.4, 50.5 + (k // 2 - 0.5) * 0.9), 0.5, OBS, subdiv=1, jitter=0.03)
    rock(p, (55, 1, 45), 1, DROCK, scale=(1.8, 1.0, 1.8))
    rbox(p, (51, 0.8, 43.4), (3.4, 1.6, 2), DWOOD, 15)
    rbox(p, (39, 0.7, 53.5), (2.6, 1.4, 2.6), IRON, -20)


# ---- 15. Banners --------------------------------------------------------------------------------------------------------
def build_Banners(p):
    rseed(15)
    rock(p, (24, 0.8, 38.5), 1, ROCK, scale=(1.7, 0.8, 1.5))
    rock(p, (31.5, 0.7, 39), 1, DROCK, scale=(1.5, 0.7, 1.3))
    for (x, z, h, c) in ((22, 37, 12, 0), (26, 40, 14, 1), (30, 37, 10, 0), (33, 40.5, 13, 1)):
        col = SCALE if c else CLOTH
        dcol = DSCALE if c else (130, 28, 40)
        vcyl(p, x, 0, h, z, 0.35, WOOD, verts=6, top_r=0.3)
        dk.cyl(p, (x, 0.5, z), 0.8, 1.0, DWOOD, axis='y', verts=6, top_radius=0.5)
        ball(p, (x, h + 0.6, z), 0.6, GOLD, subdiv=1)
        spike(p, x, h + 1.0, z, 0.2, 0.7, GOLD, verts=4)
        bx(p, (x, x + 3.7), (h - 0.8, h - 0.5), (z - 0.12, z + 0.12), DWOOD, 0.03)           # cross bar
        # flag in three flapping panels with a swallow tail
        for k in range(3):
            x0 = x + 0.2 + k * 1.15
            top = h - 0.5
            bot = top - 5.0 + k * 0.6
            zz = z + (0.25 if k % 2 else -0.15)
            pts = [(x0, top, zz), (x0 + 1.15, top, zz + 0.15), (x0 + 1.15, bot, zz + 0.15), (x0, bot, zz)]
            if k == 2:
                pts = [(x0, top, zz), (x0 + 1.4, top - 0.2, zz + 0.3), (x0 + 0.4, bot + 1.2, zz + 0.2), (x0 + 1.4, bot + 0.3, zz + 0.2), (x0, bot, zz)]
            fcs = [tuple(range(len(pts)))]
            dk.poly(p, (0, 0, 0), pts, fcs, col if k != 1 else dcol, 0.04)
            dk.poly(p, (0, 0, 0), [(a, b, c_ - 0.06) for (a, b, c_) in pts], [tuple(range(len(pts)))[::-1]], col if k != 1 else dcol, 0.04)
        ball(p, (x + 1.9, h - 2.2, z + 0.3), 0.55, GOLD, scale=(1, 1, 0.3), subdiv=1)
        spike(p, x + 1.9, h - 3.4, z + 0.3, 0.5, 1.2, GOLD, verts=4)


# ---- 16. Tower ----------------------------------------------------------------------------------------------------------
def build_Tower(p):
    rseed(16)
    bx(p, (62.5, 73.5), (0, 8), (-19.5, -8.5), (118, 110, 126), 0.07)
    for k in range(4):
        bx(p, (62.3, 73.7), (k * 2 + 0.8, k * 2 + 1.0), (-19.7, -8.3), (84, 78, 94), 0.04)
    bx(p, (63.5, 72.5), (8, 20), (-18.5, -9.5), (98, 90, 108), 0.07)
    for k in range(5):
        bx(p, (63.3, 72.7), (8.8 + k * 2.3, 9.0 + k * 2.3), (-18.7, -9.3), (128, 120, 138), 0.04)
    bx(p, (62.3, 73.7), (20, 23.2), (-19.7, -8.3), (132, 124, 142), 0.06)                                  # corbel ring
    # broken battlement: teeth of different heights, one corner collapsed
    for (x, z, hh) in ((64, -18, 2.4), (72, -18, 1.4), (72, -10, 2.4), (68, -18.4, 1.1), (73, -14, 1.6), (64, -10.4, 0.9)):
        bx(p, (x - 1.3, x + 1.3), (23.2, 23.2 + hh), (z - 1.3, z + 1.3), (136, 128, 146) if hh > 1.3 else (100, 92, 110), 0.07)
    rbox(p, (65, 24.1, -12), (2.2, 0.8, 1.4), DROCK, 30)
    # cracks, moss and a breach in the wall
    bx(p, (69.6, 72.2), (14.4, 18.8), (-9.65, -9.45), OBS, 0.02)
    rbox(p, (70.2, 14.2, -9.0), (1.6, 0.8, 0.5), ROCK, 20)
    rbox(p, (72.0, 18.8, -9.0), (1.2, 0.9, 0.5), ROCK, -25)
    bx(p, (65.0, 66.6), (16.0, 19.4), (-9.65, -9.45), OBS, 0.02)
    for (x, y, ln, rz) in ((64.6, 14.0, 5.0, 70), (71.0, 6.4, 4.0, -60), (65.2, 7.0, 3.0, 40)):
        lbox(p, (x, y, -9.4), (0, 0, rz), (-ln / 2, ln / 2), (-0.12, 0.12), (-0.1, 0.1), OBS, 0.02)
    for (x, y, w, h) in ((63.4, 9.5, 2.4, 1.6), (71.5, 12.6, 2.0, 1.4), (66.5, 20.2, 3.2, 0.7), (71.5, 4.2, 2.0, 1.6)):
        bx(p, (x - w / 2, x + w / 2), (y, y + h), (-9.4, -9.2), (74, 120, 78), 0.07)
    # window with lava glow, door, torn banner
    bx(p, (67.1, 68.9), (11.3, 14.7), (-8.9, -8.3), LAVA, 0.04)
    bx(p, (66.7, 69.3), (14.7, 15.1), (-9.0, -8.2), DIRON, 0.03)
    bx(p, (66.7, 69.3), (11.0, 11.3), (-9.0, -8.2), DIRON, 0.03)
    bx(p, (66.7, 69.3), (0, 5.4), (-8.7, -8.1), DWOOD, 0.05)
    bx(p, (66.5, 69.5), (5.4, 5.8), (-8.8, -8.0), DIRON, 0.03)
    bx(p, (73.5, 73.9), (14.6, 18.4), (-12.7, -10.3), CLOTH, 0.05)
    spike(p, 73.7, 12.4, -11.5, 1.1, 2.3, CLOTH, verts=3)
    # rubble
    rbox(p, (72.2, 1.6, -8), (4, 3.2, 3.4), ROCK, 30, 0.07)
    rbox(p, (63.5, 1.2, -9), (3, 2.4, 3), DROCK, -20, 0.07)
    rock(p, (70, 0.5, -6.5), 1, DROCK, scale=(1.4, 0.6, 1.2))
    rock(p, (74.0, 0.6, -15.5), 1, ROCK, scale=(1.2, 0.8, 1.6))
    rock(p, (62.6, 0.6, -15.5), 1, LROCK, scale=(1.0, 0.6, 1.2))




# ---- 17. Baby -----------------------------------------------------------------------------------------------------------
def build_Baby(p):
    rseed(17)
    disc(p, -37.2, 0, 51, 6.6, 4.8, 1.6, ROCK, verts=9, rtop=0.9, jit=0.08)
    rock(p, (-41.5, 0.8, 47.0), 1, DROCK, scale=(1.6, 0.9, 1.4))
    rock(p, (-31, 0.7, 54.6), 1, LROCK, scale=(1.4, 0.8, 1.2))
    # round body, pale belly, big sleepy head resting on the front paws
    dk.ball(p, (-37, 3.9, 51), 1, SCALE, scale=(2.9, 2.3, 2.2), subdiv=2, jitter=0.05)
    dk.ball(p, (-36.4, 3.0, 51), 1, (170, 214, 150), scale=(2.2, 1.4, 1.7), subdiv=1, jitter=0.04)
    dk.ball(p, (-32.6, 4.8, 51), 1, SCALE, scale=(2.3, 2.1, 2.2), subdiv=2, jitter=0.05)
    frust(p, -30.8, 3.9, 51, 2.2, 2.2, 1.5, 1.7, 1.7, LSCALE, jit=0.04)                    # short snout
    for s in (-1, 1):
        bx(p, (-33.6, -31.6), (5.3, 5.6), (51 + s * 2.1 - 0.15, 51 + s * 2.1 + 0.15), OBS, 0.02)   # closed eyes
        bx(p, (-29.9, -29.6), (4.6, 5.1), (51 + s * 0.45 - 0.15, 51 + s * 0.45 + 0.15), OBS, 0.02)
        tube(p, (-33.4, 6.6, 51 + s * 1.3), (-35.0, 8.4, 51 + s * 1.7), 0.5, 0.04, BONE, verts=4)    # horns
        dk.ball(p, (-34.0, 5.4, 51 + s * 2.6), 0.55, DSCALE, scale=(1, 1.4, 0.4), subdiv=1)            # ear fins
    # small folded wings: bone arm and fingers with a membrane, half open over the back
    for s in (-1, 1):
        sh = (-37.6, 5.6, 51 + s * 1.9)
        wr = (-38.1, 8.9, 51 + s * 3.8)
        t1 = (-40.6, 8.0, 51 + s * 5.4)
        t2 = (-41.4, 6.2, 51 + s * 4.4)
        tube(p, sh, wr, 0.3, 0.22, BONE, verts=4)
        tube(p, wr, t1, 0.2, 0.08, BONE, verts=4)
        tube(p, wr, t2, 0.2, 0.08, BONE, verts=4)
        sheet(p, [sh, wr, t1, t2], (84, 180, 100))
        sheet(p, [sh, t2, (-39.6, 4.6, 51 + s * 2.6)], DSCALE)
    for k in range(5):                                                                        # back spines
        spike(p, -38.4 + k * 1.1, 5.9 - abs(k - 2) * 0.25, 51, 0.3, 0.9, GOLD if k % 2 else DSCALE, verts=4)
    # fat tail hugging the rock, ending in a spade
    pts_t = [(-39.3, 2.6, 51.8), (-41.6, 2.0, 52.6), (-43.6, 1.9, 54.0), (-44.0, 2.5, 55.6), (-42.4, 3.7, 56.0)]
    rads = [1.3, 1.1, 0.9, 0.7, 0.45]
    for i in range(4):
        tube(p, pts_t[i], pts_t[i + 1], rads[i], rads[i + 1], SCALE if i % 2 == 0 else (72, 164, 94), verts=6)
    lbox(p, (-42.2, 3.9, 56.0), (-30, 20, 0), (-0.8, 0.8), (-0.5, 0.5), (-0.1, 1.8), GOLD, 0.04, taper=0.4)
    # paws
    for z in (49.4, 52.6):
        bx(p, (-34.8, -32.2), (0, 1.6), (z - 0.7, z + 0.7), DSCALE, 0.05)
        for k in (-1, 0, 1):
            spike(p, -32.0, 0.2, z + k * 0.45, 0.14, 0.5, BONE, verts=3)
    dk.ball(p, (-39.6, 1.6, 49.2), 1, DSCALE, scale=(1.6, 1.0, 1.1), subdiv=1)


# ---- 18. Throne ---------------------------------------------------------------------------------------------------------
def build_Throne(p):
    rseed(18)
    frust(p, -6, 0, 8, 10, 9, 9.4, 8.4, 1.4, ROCK, jit=0.05)
    frust(p, -6, 0, 13, 7, 2.4, 6.6, 2.0, 0.7, DROCK, jit=0.05)
    # seat: bone block with a red cushion and a gold trim
    bx(p, (-8.5, -3.5), (1.4, 4.4), (5.7, 10.3), BONE, 0.04)
    bx(p, (-8.0, -4.0), (4.4, 5.2), (6.2, 9.8), CLOTH, 0.04)
    bx(p, (-8.2, -3.8), (4.2, 4.5), (9.6, 10.4), GOLD, 0.03)
    # back: solid bone slab with carved rib grooves, spine posts and a skull in the middle
    bx(p, (-8.8, -3.2), (4.4, 11.6), (5.1, 6.5), BONE, 0.04)
    for k in range(5):
        bx(p, (-8.0 + k * 1.0 - 0.1, -8.0 + k * 1.0 + 0.1), (5.4, 8.2), (6.5, 6.62), DBONE, 0.03)
    bx(p, (-9.2, -8.4), (4.4, 12.0), (4.9, 6.7), DBONE, 0.04)
    bx(p, (-3.6, -2.8), (4.4, 12.0), (4.9, 6.7), DBONE, 0.04)
    skull(p, -6, 7.6, 5.9, 2.8, horns=0.0)
    gemc(p, -6.0, 10.5, 6.55, 0.7, 0.9, RUBY)
    for s in (-1, 1):                                        # dragon horns rising behind
        tube(p, (-6 + s * 2.9, 11.6, 5.8), (-6 + s * 3.7, 14.1, 5.8), 0.55, 0.04, BONE, verts=5)
    bx(p, (-7.2, -4.8), (11.6, 12.0), (5.3, 6.3), GOLD, 0.03)                                       # crown on top
    for k in range(4):
        spike(p, -6.9 + k * 0.8, 12.0, 5.8, 0.3, 0.9, GOLD, verts=4, jit=0.03)
    # armrests with skulls
    for s in (-1, 1):
        x = -6 + s * 2.95
        bx(p, (x - 0.7, x + 0.7), (1.4, 4.4), (6.2, 10.2), DBONE, 0.04)
        skull(p, x, 4.4, 8.4, 1.9, horns=0.0)
        dk.ball(p, (x, 1.8, 11.6), 1, BONE, scale=(0.6, 0.7, 0.6), subdiv=1)
    skull(p, -9.6, 1.4, 11.4, 1.5)


# ---- 19. Coins ----------------------------------------------------------------------------------------------------------
def build_Coins(p):
    rseed(19)
    for (x, z, h, seed) in ((44, -26, 9.0, 1), (48, -23, 6.0, 2), (40, -23.5, 4.6, 3), (47, -30, 7.4, 4)):
        rr = random.Random(seed)
        n = max(4, int(h / 0.78))
        th = h / n
        lean = rr.uniform(-0.1, 0.1)
        for k in range(n):
            ox, oz = rr.uniform(-0.3, 0.3) + lean * k, rr.uniform(-0.3, 0.3)
            disc(p, x + ox, k * th, z + oz, 2.2, 2.2, th * 0.9, GOLD if k % 3 else (252, 222, 104) if k % 2 else DGOLD, verts=8, jit=0.05, yaw=rr.uniform(0, 45))
        gemc(p, x + lean * n, h, z, 1.5, 1.7, RUBY if seed == 1 else EMER if seed == 3 else (250, 250, 230))
    # loose coins: flat, leaning against a tower, tipped on the edge
    dk.cyl(p, (52, 0.3, -26), 1.8, 0.5, GOLD, axis='y', verts=8, jitter=0.05)
    dk.cyl(p, (51, 0.3, -21.5), 1.5, 0.5, DGOLD, axis='y', verts=8, jitter=0.05)
    dk.cyl(p, (50, 0.9, -25.8), 1.7, 0.4, GOLD, axis='y', verts=8, rot=(0, 0, 14), jitter=0.05)
    dk.cyl(p, (40.5, 2.0, -28), 1.7, 0.5, GOLD, axis='y', verts=8, rot=(0, 0, 60), jitter=0.05)
    dk.cyl(p, (44.5, 1.5, -22.0), 1.3, 0.4, DGOLD, axis='y', verts=8, rot=(60, 0, 0), jitter=0.05)


# ---- 20. Runes ----------------------------------------------------------------------------------------------------------
def build_Runes(p):
    rseed(20)
    disc(p, -22, 0, -24, 7.4, 7.4, 0.3, DROCK, verts=14, jit=0.04)
    disc(p, -22, 0.3, -24, 4.8, 4.8, 0.1, PURPLE, verts=12, jit=0.05)
    disc(p, -22, 0.4, -24, 3.2, 3.2, 0.05, (176, 140, 250), verts=10, jit=0.05)
    for k in range(7):                                                  # glyph marks on the plate
        a = math.radians(k * 51.4 + 30)
        rbox(p, (-22 + 4.0 * math.cos(a), 0.46, -24 + 4.0 * math.sin(a)), (0.4, 0.1, 1.3), (176, 140, 250), -math.degrees(a), 0.04)
    hs = [7, 5.4, 6.4, 8, 5, 6, 7.4]
    for k in range(7):
        a = math.radians(k * 51.4 + 8)
        x, z = -22 + 6.2 * math.cos(a), -24 + 6.2 * math.sin(a)
        t = (5 if k % 2 == 0 else -5, 6 if k % 3 == 0 else -4)
        yaw = -math.degrees(a)
        h = hs[k]
        lbox(p, (x, 0, z), (t[0], yaw, t[1]), (-0.9, 0.9), (0, h), (-0.5, 0.5), (120, 112, 130) if k % 2 else (150, 142, 160), 0.08, taper=0.8)
        lbox(p, (x, 0, z), (t[0], yaw, t[1]), (-0.8, 0.8), (h, h + 0.5), (-0.4, 0.4), DROCK, 0.06, taper=0.5)
        lbox(p, (x, 0, z), (t[0], yaw, t[1]), (-0.18, 0.18), (h * 0.3, h * 0.8), (0.48, 0.58), PURPLE, 0.05)   # glowing rune line
    crystal(p, -22, 0.4, -24, 2.4, 5.2, PURPLE, tilt=(0, 0), sides=6, jit=0.12)
    crystal(p, -22.8, 0.4, -23.2, 1.2, 2.4, (176, 140, 250), tilt=(10, -15), sides=5, jit=0.1)


# ---- 21. Wings ----------------------------------------------------------------------------------------------------------
def build_Wings(p):
    rseed(21)
    for s in (-1, 1):
        frust(p, 66 + s * 6, 0, 46, 8, 6, 5.0, 3.6, 1.8, ROCK, yaw=s * 12, jit=0.08)
        base = (66 + s * 3.6, 1.2, 46)
        elbow = (66 + s * 4.6, 11.0, 46)
        wrist = (66 + s * 11.0, 21.4, 46)
        tips = [(66 + s * 13.1, 12.5, 46), (66 + s * 11.4, 5.2, 46), (66 + s * 8.0, 1.6, 46)]
        tube(p, base, elbow, 0.8, 0.65, BONE, verts=5)
        tube(p, elbow, wrist, 0.65, 0.55, BONE, verts=5)
        dk.ball(p, wrist, 0.9, DBONE, subdiv=1)
        tube(p, (wrist[0], wrist[1] + 0.3, 46), (wrist[0] + s * 1.6, wrist[1] + 2.0, 46), 0.4, 0.05, DBONE, verts=4)   # claw
        for t in tips:
            tube(p, wrist, t, 0.5, 0.16, BONE, verts=5)

        def mid(a, b, k):
            return ((a[0] + b[0]) / 2 + (wrist[0] - (a[0] + b[0]) / 2) * k, (a[1] + b[1]) / 2 + (wrist[1] - (a[1] + b[1]) / 2) * k, 46)
        # membrane: inner panel from the arm to the first finger, then scalloped panels between the fingers
        sheet(p, [elbow, wrist, tips[2], base], SCALE)
        sheet(p, [wrist, tips[2], mid(tips[1], tips[2], 0.3), tips[1]], LSCALE)
        sheet(p, [wrist, tips[1], mid(tips[0], tips[1], 0.3), tips[0]], SCALE)
        sheet(p, [wrist, tips[0], (66 + s * 12.4, 17.0, 46)], LSCALE)
        for t in tips:
            spike(p, t[0] + s * 0.1, t[1] - 0.3, 46, 0.3, 0.8, BONE, verts=4)
        rock(p, (66 + s * 10.5, 0.6, 46.8), 1, DROCK, scale=(2.0, 0.8, 1.8))


# ---- 22. Skull ----------------------------------------------------------------------------------------------------------
def build_Skull(p):
    rseed(22)
    frust(p, -24, 0, 19.5, 16, 16, 14, 14, 1.6, ROCK, jit=0.07)
    rock(p, (-31, 0.7, 24), 1, DROCK, scale=(1.8, 0.9, 1.6))
    rock(p, (-17.2, 0.6, 14), 1, LROCK, scale=(1.4, 0.8, 1.4))
    w = 11.0
    cz = 17.4
    y0 = 1.6
    dk.ball(p, (-24, y0 + 0.5 * w, cz), 1, BONE, scale=(0.5 * w, 0.44 * w, 0.5 * w), subdiv=2, jitter=0.04)   # cranium
    bx(p, (-24 - 0.26 * w, -24 + 0.26 * w), (y0 + 0.2 * w, y0 + 0.5 * w), (cz + 0.1 * w, cz + 0.68 * w), BONE, 0.04)  # snout
    bx(p, (-24 - 0.22 * w, -24 + 0.22 * w), (y0 + 0.02 * w, y0 + 0.2 * w), (cz + 0.1 * w, cz + 0.66 * w), DBONE, 0.04)  # jaw
    frust(p, -24, y0 + 0.5 * w, cz + 0.1 * w, 6.2, 3.4, 4.8, 2.6, 0.9, DBONE, jit=0.04)                    # brow ridge
    for k in range(7):                                                                       # teeth
        x = -24 - 0.22 * w + k * 0.073 * w
        spike(p, x, y0 + 0.2 * w - 0.9, cz + 0.66 * w, 0.14 * w * 0.25, 1.0, (250, 246, 230), verts=4, top_r=0.04, jit=0.02)
    for s in (-1, 1):
        bx(p, (-24 + s * 0.22 * w - 0.12 * w, -24 + s * 0.22 * w + 0.12 * w), (y0 + 0.5 * w, y0 + 0.7 * w), (cz + 0.35 * w, cz + 0.5 * w), OBS, 0.02)
        dk.ball(p, (-24 + s * 0.22 * w, y0 + 0.6 * w, cz + 0.5 * w), 0.07 * w, LAVA, subdiv=1, jitter=0.02)  # glowing eyes
        bx(p, (-24 + s * 0.1 * w - 0.03 * w, -24 + s * 0.1 * w + 0.03 * w), (y0 + 0.4 * w, y0 + 0.5 * w), (cz + 0.66 * w, cz + 0.7 * w), OBS, 0.02)
        tube(p, (-24 + s * 3.8, y0 + 0.74 * w, cz - 0.1 * w), (-24 + s * 6.6, y0 + 0.74 * w + 1.6, cz - 0.1 * w), 0.9, 0.5, BONE, verts=6)
        tube(p, (-24 + s * 6.6, y0 + 0.74 * w + 1.6, cz - 0.1 * w), (-24 + s * 7.9, y0 + 0.74 * w + 3.6, cz - 0.1 * w), 0.5, 0.03, DBONE, verts=5)
        spike(p, -24 + s * 2.5, y0 + 0.2 * w - 0.4, cz + 0.68 * w, 0.28, 1.5, (250, 246, 230), verts=4, top_r=0.04)


# ---- 23. Spires ---------------------------------------------------------------------------------------------------------
def build_Spires(p):
    rseed(23)
    OB = (98, 88, 132)
    OB2 = (70, 62, 98)
    rock(p, (-70, 1.6, -47), 1, DROCK, scale=(8, 1.7, 6), jit=0.08)
    rock(p, (-66, 1.0, -41.2), 1, ROCK, scale=(2.4, 1.0, 2.0), jit=0.08)
    rock(p, (-75, 1.0, -43), 1, ROCK, scale=(2.2, 0.9, 2.0), jit=0.08)
    spec = [(-70, -46, 6.0, 28, (4, -3), OB), (-65.5, -51, 4.4, 20, (-8, 6), OB2), (-74, -52, 4.0, 16, (6, -14), OB),
            (-64, -43, 3.6, 13, (0, 8), OB2), (-73, -41, 3.4, 10, (8, -6), OB)]
    for (x, z, w, h, t, c) in spec:
        crystal(p, x, 1.4, z, w, h - 1.4, c, tilt=t, sides=5, jit=0.3)
    for k in range(5):
        crystal(p, -70 + RR.uniform(-7, 7), 1.0, -47 + RR.uniform(-5, 5), 0.9, RR.uniform(1.6, 3.4), PURPLE if k % 2 else OB, tilt=(RR.uniform(-25, 25), RR.uniform(-25, 25)), sides=4, jit=0.15)


# ---- 24. Keep -----------------------------------------------------------------------------------------------------------
def build_Keep(p):
    rseed(24)
    HALL = (74, 66, 86)
    # great hall with stone courses, merlons and slit windows
    bx(p, (-59, -37), (0, 18), (-53, -41), HALL, 0.06)
    for k in range(5):
        bx(p, (-59.2, -36.8), (k * 3.5 + 1.2, k * 3.5 + 1.4), (-53.2, -40.8), (100, 92, 112), 0.03)
    bx(p, (-59.6, -36.4), (17.6, 18.4), (-53.6, -40.4), (96, 88, 108), 0.04)
    for k in range(6):
        x = -57.8 + k * 3.7
        bx(p, (x - 0.7, x + 0.7), (18.4, 19.8), (-41.6, -40.4), (110, 102, 122), 0.05)
    for z in (-52.5, -47, -42.5):
        for x in (-58.6, -37.4):
            bx(p, (x - 0.4, x + 0.4), (18.4, 19.8), (z - 0.7, z + 0.7), (110, 102, 122), 0.05)
    bx(p, (-54, -42), (18.4, 32), (-51.5, -42.5), (104, 96, 116), 0.06)                            # upper keep
    for k in range(3):
        bx(p, (-54.2, -41.8), (21.6 + k * 3.6, 21.8 + k * 3.6), (-51.7, -42.3), (84, 76, 98), 0.03)
    # scaled dragon roof: stepped slabs
    for i, (w, d, h0, h1) in enumerate(((14.4, 11.4, 32, 33.2), (13.0, 10.2, 33.2, 34.4), (10.4, 8.2, 34.4, 35.4), (8.4, 6.6, 35.4, 36.4), (5.2, 4.4, 36.4, 37.4))):
        bx(p, (-48 - w / 2, -48 + w / 2), (h0, h1), (-47 - d / 2, -47 + d / 2), SCALE if i % 2 else DSCALE, 0.07)
    spike(p, -48, 37.4, -47, 1.1, 1.0, GOLD, verts=6, jit=0.04)
    # four round towers with scaled cone roofs
    for (x, z) in ((-58.5, -52.5), (-37.5, -52.5), (-58.5, -41.5), (-37.5, -41.5)):
        vcyl(p, x, 0, 22, z, 3.0, (104, 96, 114), verts=8, top_r=2.8)
        for yy in (10,):
            vcyl(p, x, yy, yy + 0.4, z, 3.2, (84, 76, 98), verts=8)
        vcyl(p, x, 22, 23.2, z, 3.8, DSCALE, verts=8)
        vcyl(p, x, 23.2, 28.0, z, 3.6, SCALE, verts=8, top_r=0.1)
        bx(p, (x - 0.35, x + 0.35), (13, 15.4), (z + 2.7, z + 3.1), LAVA, 0.04) if z > -45 else None
        ball(p, (x, 28.2, z), 0.45, GOLD, subdiv=1)
    # front gate: stone arch, wooden doors, dragon head gargoyle
    bx(p, (-51.4, -44.6), (0, 8.2), (-41.4, -40.2), (130, 122, 140), 0.05)
    bx(p, (-50.0, -46.0), (0, 7.2), (-40.9, -40.4), DWOOD, 0.05)
    bx(p, (-48.2, -47.8), (0, 7.2), (-40.9, -40.3), DIRON, 0.03)
    for k in range(3):
        for s in (-1, 1):
            dk.ball(p, (-48 + s * 1.0, 2.0 + k * 2.0, -40.2), 0.2, GOLD, subdiv=1)
    dk.ball(p, (-48, 11.8, -40.2), 1, SCALE, scale=(2.2, 1.8, 1.6), subdiv=2, jitter=0.05)
    frust(p, -48, 10.8, -39.4, 2.6, 1.8, 2.0, 1.4, 1.6, LSCALE, jit=0.04)
    for s in (-1, 1):
        dk.ball(p, (-48 + s * 1.2, 12.5, -39.6), 0.35, EMBER, subdiv=1)
        tube(p, (-48 + s * 1.2, 13.3, -40.4), (-48 + s * 2.2, 15.8, -41.0), 0.35, 0.03, BONE, verts=4)
        spike(p, -48 + s * 0.7, 10.6, -38.8, 0.2, 0.9, (250, 246, 230), verts=4, top_r=0.03)
    bx(p, (-49, -47), (20.3, 23.7), (-42.9, -42.4), LAVA, 0.04)                                    # lava window
    bx(p, (-49.4, -46.6), (23.7, 24.1), (-43.0, -42.3), DIRON, 0.03)
    for x in (-54, -42):                                                                          # slit windows
        bx(p, (x - 0.4, x + 0.4), (9, 12), (-41.1, -40.6), LAVA, 0.04)
    for x in (-55.5, -40.5):                                                                      # banners
        bx(p, (x - 0.9, x + 0.9), (7, 14), (-40.4, -40.2), CLOTH, 0.04)
        bx(p, (x - 0.1, x + 0.1), (12, 12.4), (-40.5, -40.1), GOLD, 0.03)
    for k in range(3):
        bx(p, (-51.4 + k * 0.5, -44.6 - k * 0.5), (-0.0, 0.5 - k * 0.12 + k * 0.3), (-40.2 + k * 0.4, -39.6 + k * 0.4), (130, 122, 140), 0.04)


# ---- 25. Catapult -------------------------------------------------------------------------------------------------------
def wheel(p, x, y, z, r, th):
    dk.cyl(p, (x, y, z), r, th, DWOOD, axis='z', verts=10, jitter=0.05)
    dk.cyl(p, (x, y, z + (th / 2 + 0.04) * (1 if z > 28 else -1)), r * 0.2, 0.2, IRON, axis='z', verts=6, jitter=0.03)
    for k in range(3):
        a = k * 60
        side = 1 if z > 28 else -1
        dk.box(p, (x, y, z + side * (th / 2 + 0.05)), (r * 1.8, 0.28, 0.12), WOOD, rot=(0, 0, a), jitter=0.04)


def build_Catapult(p):
    rseed(25)
    # base frame: two long beams, cross beams and planks
    for z in (25.6, 30.4):
        bx(p, (59.0, 69.0), (0.7, 1.7), (z - 0.5, z + 0.5), WOOD, 0.05)
    for x in (60, 64, 68):
        bx(p, (x - 0.5, x + 0.5), (0.9, 1.5), (25.2, 30.8), DWOOD, 0.05)
    bx(p, (59.2, 69.0), (1.7, 1.95), (26.4, 29.6), (150, 108, 70), 0.05)
    for (x, z) in ((60.2, 24.9), (60.2, 31.1), (67.8, 24.9), (67.8, 31.1)):
        wheel(p, x, 1.9, z, 1.8, 0.8)
    for z in (24.9, 31.1):
        dk.cyl(p, (64, 1.9, z), 0.2, 8.4, DIRON, axis='x', verts=5)
    # A-frame uprights on both sides, axle and winch
    for z in (25.6, 30.4):
        tube(p, (62.0, 1.7, z), (63.0, 7.0, z), 0.45, 0.4, DWOOD, verts=5)
        tube(p, (64.4, 1.7, z), (63.0, 7.0, z), 0.45, 0.4, DWOOD, verts=5)
        bx(p, (62.6, 63.5), (5.4, 5.7), (z - 0.3, z + 0.3), WOOD, 0.04)
    dk.cyl(p, (63, 6.9, 28), 0.4, 5.8, DIRON, axis='z', verts=6)
    dk.cyl(p, (60.6, 2.4, 28), 0.5, 3.0, WOOD, axis='z', verts=6)                       # winch drum
    # throwing arm rising to the bucket, counterweight at the low end
    lbox(p, (64.6, 7.6, 28), (0, 0, 28), (-5.5, 5.5), (-0.45, 0.45), (-0.5, 0.5), WOOD, 0.05)
    lbox(p, (64.6, 7.6, 28), (0, 0, 28), (-1.2, 1.2), (-0.55, 0.55), (-0.62, 0.62), IRON, 0.04)
    for z in (-1.1, 1.1):
        lbox(p, (59.4, 4.3, 28), (0, 0, 0), (-1.3, 1.3), (-1.4, 1.4), (z - 0.2, z + 0.2), DIRON, 0.04)
    bx(p, (57.7, 60.3), (3.1, 5.7), (26.8, 29.2), STONE, 0.06)                          # stone counterweight
    for yy in (3.7, 5.1):
        bx(p, (57.6, 60.4), (yy - 0.12, yy + 0.12), (26.7, 29.3), DIRON, 0.03)
    # bucket with a boulder
    bx(p, (67.9, 70.5), (9.4, 9.8), (26.8, 29.2), DWOOD, 0.05)
    for z in (26.8, 29.0):
        bx(p, (67.9, 70.5), (9.6, 11.3), (z, z + 0.2), WOOD, 0.05)
    bx(p, (70.3, 70.5), (9.6, 11.3), (26.8, 29.2), WOOD, 0.05)
    rock(p, (69.8, 11.4, 28), 1, ROCK, scale=(1.35, 1.35, 1.35), jit=0.08)
    # spare boulders and a coil of rope
    rock(p, (58.4, 0.8, 30.8), 1, DROCK, scale=(1.2, 0.8, 1.1))
    rock(p, (70.4, 0.7, 26.2), 1, ROCK, scale=(1.0, 0.7, 1.0))


# ---- 26. Statue ---------------------------------------------------------------------------------------------------------
def build_Statue(p):
    rseed(26)
    ST = (150, 144, 152)
    ST2 = (122, 116, 130)
    MOSS = (74, 120, 78)
    frust(p, -12, 0, -47, 7.4, 7.4, 6.4, 6.4, 2.4, ST2, jit=0.05)
    bx(p, (-14.2, -9.8), (2.4, 3.0), (-49.2, -44.8), ST, 0.05)
    bx(p, (-13.4, -10.6), (1.0, 1.8), (-43.55, -43.4), GOLD, 0.03)                               # plaque
    bx(p, (-9.6, -6.5), (0.1, 0.9), (-48.2, -45.6), MOSS, 0.07)                                  # moss
    bx(p, (-17.2, -14.4), (2.4, 2.9), (-47.0, -44.6), MOSS, 0.07)
    # slayer: boots, legs, tunic, belt, cape, helmet with a plume, sword raised, shield on the arm
    for s in (-1, 1):
        bx(p, (-12 + s * 1.0 - 0.8, -12 + s * 1.0 + 0.8), (3.0, 3.6), (-47.9, -46.1), ST2, 0.05)
        bx(p, (-12 + s * 1.0 - 0.65, -12 + s * 1.0 + 0.65), (3.6, 6.6), (-47.6, -46.4), ST, 0.05)
    bx(p, (-14.1, -9.9), (6.4, 7.0), (-47.8, -46.2), ST2, 0.05)
    frust(p, -12, 7.0, -47, 4.2, 2.4, 4.8, 2.6, 4.2, ST, jit=0.05)
    bx(p, (-14.4, -9.6), (11.0, 11.5), (-48.4, -45.6), ST2, 0.05)
    for s in (-1, 1):                                                                            # pauldrons
        dk.ball(p, (-12 + s * 2.5, 10.9, -47), 1.25, ST, scale=(1, 0.8, 1), subdiv=1, jitter=0.05)
        spike(p, -12 + s * 2.8, 11.5, -47, 0.3, 0.8, ST2, verts=4)
    bx(p, (-13.0, -11.0), (7.0, 7.5), (-45.9, -45.7), GOLD, 0.03)                                # belt buckle
    for k in range(3):                                                                           # breastplate ribs
        bx(p, (-13.4, -10.6), (8.3 + k * 0.9, 8.5 + k * 0.9), (-45.9, -45.75), ST2, 0.03)
    lbox(p, (-12, 6.8, -47.9), (0, 0, 0), (-2.0, 2.0), (-5.2, 4.2), (-0.5, 0.1), (118, 110, 126), 0.05, taper=0.8)    # cape
    dk.ball(p, (-12, 12.6, -47), 1, ST, scale=(1.35, 1.45, 1.35), subdiv=1, jitter=0.05)
    for s in (-1, 1):
        bx(p, (-12 + s * 0.55 - 0.3, -12 + s * 0.55 + 0.3), (12.8, 13.1), (-45.75, -45.55), OBS, 0.02)
    bx(p, (-12.2, -11.8), (11.9, 13.0), (-45.75, -45.45), ST2, 0.03)
    skull(p, -8.6, 0.0, -46.2, 2.6)
    tube(p, (-12, 13.7, -47), (-12, 15.6, -47.6), 0.45, 0.05, ST2, verts=4)                      # crest
    tube(p, (-10.2, 10.6, -47), (-8.8, 14.4, -47), 0.6, 0.5, ST, verts=5)                       # raised right arm
    dk.ball(p, (-8.6, 14.7, -47), 0.6, ST2, subdiv=1)
    lbox(p, (-8.6, 14.8, -47), (0, 0, -6), (-0.5, 0.5), (-0.4, 2.0), (-0.14, 0.14), (206, 212, 226), 0.04, taper=0.5)  # sword
    lbox(p, (-8.6, 14.8, -47), (0, 0, -6), (-1.2, 1.2), (-0.6, -0.3), (-0.3, 0.3), DGOLD, 0.04)
    tube(p, (-14.4, 10.6, -47), (-15.4, 8.0, -46.4), 0.6, 0.5, ST, verts=5)                      # left arm with shield
    dk.cyl(p, (-15.6, 8.6, -45.6), 1.9, 0.5, ST2, axis='z', verts=9, jitter=0.05)
    dk.cyl(p, (-15.6, 8.6, -45.3), 0.5, 0.3, GOLD, axis='z', verts=6)
    # moss on shoulders and rubble around
    bx(p, (-14.2, -12.6), (11.5, 11.7), (-48.2, -46.0), MOSS, 0.07)
    bx(p, (-12.6, -11.4), (7.0, 7.1), (-47.8, -46.4), MOSS, 0.07)
    rock(p, (-17, 0.9, -49), 1, DROCK, scale=(1.7, 0.9, 1.6))
    rock(p, (-7, 0.8, -49.5), 1, ROCK, scale=(1.3, 0.8, 1.2))
    rock(p, (-17.5, 0.5, -44.4), 1, LROCK, scale=(0.9, 0.5, 0.9))


# ---- 27. Volcano --------------------------------------------------------------------------------------------------------
def build_Volcano(p):
    rseed(27)
    disc(p, 60, 0, -42, 14.2, 14.2, 9, DROCK, verts=10, rtop=0.8, jit=0.07, yaw=8)
    disc(p, 60, 8.5, -42, 10.8, 10.8, 8, ROCK, verts=10, rtop=0.78, jit=0.07, yaw=-5)
    disc(p, 60, 16, -42, 7.8, 7.8, 6.6, (100, 92, 110), verts=10, rtop=0.78, jit=0.07, yaw=12)
    disc(p, 60, 22.2, -42, 5.6, 5.6, 2.6, DROCK, verts=10, rtop=0.9, jit=0.06, yaw=0)
    disc(p, 60, 24.8, -42, 4.9, 4.9, 0.2, OBS, verts=10, jit=0.04)
    disc(p, 60, 24.8, -42, 3.9, 3.9, 0.9, LAVA, verts=10, rtop=0.98, jit=0.05)
    disc(p, 60, 25.7, -42, 2.6, 2.6, 0.1, EMBER, verts=8, jit=0.05)
    # rim teeth
    for k in range(7):
        a = k * 0.8976 + 0.2
        spike(p, 60 + 4.5 * math.cos(a), 24.5, -42 + 4.5 * math.sin(a), 0.9, 1.4 + (k % 2) * 0.7, DROCK, verts=4, jit=0.08)
    # two lava streams running down the front
    def stream(pts, w):
        for (a, b) in zip(pts, pts[1:]):
            tube(p, a, b, w, w * 0.8, LAVA, verts=4, jit=0.06)
            tube(p, (a[0], a[1] + 0.2, a[2]), (b[0], b[1] + 0.2, b[2]), w * 0.45, w * 0.4, EMBER, verts=4, jit=0.04)
    stream([(57.6, 25.2, -38.6), (56.4, 18.5, -34.4), (56.0, 11.0, -31.7), (55.4, 4.0, -30.1)], 0.95)
    stream([(63.0, 25.0, -38.6), (64.6, 17.0, -34.0), (64.4, 9.5, -30.9), (65.6, 2.2, -29.2)], 0.8)
    for k in range(6):
        dk.ball(p, (60 + RR.uniform(-3, 3), 28 + k * 1.0, -42 + RR.uniform(-2, 2)), RR.uniform(0.7, 1.1), EMBER if k % 2 else LAVA, subdiv=1)
    dk.ball(p, (62.5, 31.8, -43), 1.0, EMBER, subdiv=1)
    rock(p, (49, 2, -33), 1, DROCK, scale=(4, 2, 3), jit=0.08)
    rock(p, (71, 2, -34), 1, ROCK, scale=(3.5, 1.8, 3), jit=0.08)
    rock(p, (52, 1, -52), 1, ROCK, scale=(2.4, 1.0, 2.0), jit=0.08)
    rock(p, (69, 1, -52), 1, DROCK, scale=(2.2, 1.0, 2.2), jit=0.08)


# ---- 28. Wagon ----------------------------------------------------------------------------------------------------------
def build_Wagon(p):
    rseed(28)
    bx(p, (35, 45), (2.1, 3.1), (-16.7, -11.3), WOOD, 0.05)
    for z in (-16.9, -11.1):
        bx(p, (34.6, 45.4), (3.1, 4.7), (z - 0.25, z + 0.25), DWOOD, 0.05)
    for x in (35.2, 44.8):
        bx(p, (x - 0.25, x + 0.25), (3.1, 4.7), (-16.9, -11.1), DWOOD, 0.05)
    for z in (-16.9, -11.1):
        for x in (35.4, 40, 44.6):
            bx(p, (x - 0.2, x + 0.2), (2.1, 4.9), (z - 0.32, z + 0.32), DIRON, 0.03)
    # wheels with spokes and iron hubs
    for (x, z) in ((36.5, -17.4), (36.5, -10.6), (43.5, -17.4), (43.5, -10.6)):
        side = -1 if z < -14 else 1
        dk.cyl(p, (x, 2.0, z), 2.0, 0.7, DWOOD, axis='z', verts=10, jitter=0.05)
        dk.cyl(p, (x, 2.0, z + side * 0.4), 1.7, 0.2, WOOD, axis='z', verts=10, jitter=0.04)
        dk.cyl(p, (x, 2.0, z + side * 0.5), 0.4, 0.25, IRON, axis='z', verts=6)
        for k in range(3):
            dk.box(p, (x, 2.0, z + side * 0.5), (3.4, 0.25, 0.1), DWOOD, rot=(0, 0, k * 60), jitter=0.03)
    for z in (-17.4, -10.6):
        dk.cyl(p, (36.5, 2.0, -14), 0.2, 7.6, DIRON, axis='z', verts=5)
        dk.cyl(p, (43.5, 2.0, -14), 0.2, 7.6, DIRON, axis='z', verts=5)
    bx(p, (45.0, 50.0), (1.7, 2.3), (-14.3, -13.7), WOOD, 0.05)                                  # draw bar
    bx(p, (49.4, 50.0), (1.4, 2.6), (-15.0, -13.0), DIRON, 0.04)
    # heaped gold with coins, ingots and a ruby
    coin_heap(p, 40, -14, 4.0, 3.4, 8, seed=28, cr=0.9, y0=3.1, xs=1.1, zs=0.55)
    dk.ball(p, (40, 5.4, -14), 1, GOLD, scale=(3.6, 1.5, 2.1), subdiv=1, jitter=0.07)
    for (x, z) in ((37.2, -16.0), (43.0, -12.2), (42.0, -16.0)):
        lbox(p, (x, 4.6, z), (0, 20, 0), (-0.9, 0.9), (0, 0.8), (-0.45, 0.45), (252, 222, 104), 0.04, taper=0.85)
    gemc(p, 40, 6.6, -14, 1.3, 1.5, RUBY)
    # sacks of coins and a crate at the tail
    dk.ball(p, (36.4, 4.3, -12.5), 1, HAY, scale=(1.0, 1.2, 0.9), subdiv=1)
    bx(p, (36.4, 38.4), (3.1, 4.9), (-16.6, -14.8), DWOOD, 0.05)


# ---- 29. Mushrooms ------------------------------------------------------------------------------------------------------
def build_Mushrooms(p):
    rseed(29)
    rock(p, (-37, 0.8, -21.5), 1, DROCK, scale=(2.6, 0.9, 2.2), jit=0.08)
    rock(p, (-42.2, 0.5, -19.2), 1, ROCK, scale=(1.3, 0.6, 1.2), jit=0.08)
    rock(p, (-32.0, 0.5, -24.5), 1, ROCK, scale=(1.3, 0.6, 1.3), jit=0.08)
    spots = [(-37, -23, 8.0, 5.2), (-41, -20, 5.4, 3.6), (-33, -19.5, 4.4, 3.0), (-40, -26, 3.2, 2.4), (-34, -26, 6.2, 4.0), (-43, -23.5, 2.4, 1.8)]
    for i, (x, z, h, r) in enumerate(spots):
        cap = PURPLE if i % 3 == 0 else EMER
        dcap = (104, 70, 190) if i % 3 == 0 else (52, 170, 130)
        tube(p, (x, 0, z), (x + 0.15 * (i % 2 - 0.5), h, z), 0.7, 0.5, CREAM, verts=7, jit=0.05)
        dk.ball(p, (x, h + 0.2, z), 1, cap, scale=(r * 0.5, r * 0.31, r * 0.5), subdiv=2, jitter=0.07)
        dk.cyl(p, (x, h + 0.1, z), r * 0.45, 0.2, dcap, axis='y', verts=9, jitter=0.05)               # gills
        for k in range(3):                                                                         # spots
            a = k * 2.1 + i
            dk.ball(p, (x + r * 0.22 * math.cos(a), h + 0.2 + r * 0.27, z + r * 0.22 * math.sin(a)), r * 0.08, CREAM, scale=(1, 0.5, 1), subdiv=1, jitter=0.03)
    for (x, z, hh) in ((-35.5, -22, 1.4), (-38.6, -22.5, 1.0), (-36, -26.2, 1.2)):                   # tiny glow-shrooms
        tube(p, (x, 0.5, z), (x, hh + 0.5, z), 0.2, 0.15, CREAM, verts=5)
        dk.ball(p, (x, hh + 0.7, z), 0.55, EMER, scale=(1, 0.65, 1), subdiv=1)


# ---- 30. GreatDragon ----------------------------------------------------------------------------------------------------
def build_GreatDragon(p):
    rseed(30)
    S1 = SCALE
    S2 = (72, 168, 96)
    # torso with a pale belly, haunch, chest
    dk.ball(p, (-66, 37.6, -10), 1, S1, scale=(9.0, 4.4, 4.4), subdiv=2, jitter=0.05)
    dk.ball(p, (-65, 36.4, -10), 1, (170, 214, 150), scale=(7.0, 2.4, 3.6), subdiv=1, jitter=0.04)
    dk.ball(p, (-70.5, 37.0, -10), 1, DSCALE, scale=(3.6, 3.8, 4.4), subdiv=1, jitter=0.06)
    dk.ball(p, (-59.5, 39.0, -10), 1, S1, scale=(4.0, 4.4, 3.6), subdiv=2, jitter=0.05)
    # neck rising to the head, tail curling off to the left
    nk = [(-58.5, 41.5, -10), (-56.5, 45.2, -10), (-53.8, 48.8, -10), (-51.0, 50.4, -10)]
    for i, (r0, r1) in enumerate(((2.2, 1.9), (1.9, 1.6), (1.6, 1.5))):
        tube(p, nk[i], nk[i + 1], r0, r1, S1 if i % 2 == 0 else S2, verts=6)
    tl = [(-73.5, 36.4, -10), (-76.0, 34.8, -9.0), (-78.0, 33.4, -10.4), (-77.4, 32.6, -12.6)]
    for i, (r0, r1) in enumerate(((2.4, 1.6), (1.6, 1.0), (1.0, 0.5))):
        tube(p, tl[i], tl[i + 1], r0, r1, S1 if i % 2 == 0 else S2, verts=6)
    sheet(p, [(-77.4, 32.8, -12.6), (-79.2, 34.0, -13.4), (-77.8, 32.4, -14.4)], GOLD)
    # back spikes
    for k in range(9):
        t = k / 8
        x = -73 + t * 20
        y = 40.8 + 0.4 * math.sin(t * 3.14) + (t * 8.5 if t > 0.65 else 0)
        spike(p, x, y - 0.4, -10, 0.55, 1.5 - 0.5 * abs(t - 0.4), GOLD if k % 2 else DSCALE, verts=4, jit=0.04)
    # head: cranium, snout, jaw, horns, eyes
    dk.ball(p, (-50, 50.8, -10), 1, S1, scale=(2.6, 2.0, 2.0), subdiv=2, jitter=0.05)
    frust(p, -47.6, 49.4, -10, 4.6, 2.8, 3.2, 2.0, 2.6, S2, jit=0.04, yaw=0)
    bx(p, (-48.6, -44.6), (47.6, 48.5), (-11.3, -8.7), DSCALE, 0.04)                                   # lower jaw
    for s in (-1, 1):
        dk.ball(p, (-49.2, 51.6, -10 + s * 1.7), 0.5, EMBER, subdiv=1)
        bx(p, (-49.9, -48.5), (51.3, 51.7), (-10 + s * 1.9 - 0.15, -10 + s * 1.9 + 0.15), OBS, 0.02)
        tube(p, (-51.5, 52.2, -10 + s * 1.1), (-54.2, 54.3, -10 + s * 1.9), 0.55, 0.06, BONE, verts=5)    # horns
        tube(p, (-54.2, 54.3, -10 + s * 1.9), (-56.2, 55.2, -10 + s * 2.2), 0.3, 0.04, DBONE, verts=4)
        for k in range(3):
            spike(p, -46.8 + k * 1.1, 48.4, -10 + s * 1.1, 0.14, 0.7, (250, 246, 230), verts=3, top_r=0.02)
    # fire breath: layered flame tongues rising from the mouth
    tube(p, (-45.0, 49.4, -10), (-38.6, 53.6, -10), 1.1, 0.06, LAVA, verts=5, jit=0.06)
    tube(p, (-45.0, 49.2, -10), (-40.0, 51.4, -10), 0.7, 0.05, EMBER, verts=5, jit=0.05)
    tube(p, (-45.0, 49.6, -10), (-41.4, 55.0, -10), 0.6, 0.05, LAVA, verts=4, jit=0.06)
    tube(p, (-45.0, 49.0, -10), (-40.6, 48.0, -10), 0.5, 0.05, EMBER, verts=4, jit=0.05)
    # legs braced on the cave roof (feet at y 32.1)
    for (x, z, big) in ((-62.5, -13.4, 0), (-62.5, -6.6, 0), (-70.0, -14.0, 1), (-70.0, -6.0, 1)):
        r = 1.5 if big else 1.2
        tube(p, (x, 36.8, z), (x - 0.6, 33.6, z + (-0.8 if z < -10 else 0.8)), r, r * 0.7, DSCALE, verts=5)
        bx(p, (x - 2.0, x + 1.4), (32.1, 33.1), (z + (-0.8 if z < -10 else 0.8) - 0.9, z + (-0.8 if z < -10 else 0.8) + 0.9), S1, 0.05)
        for k in (-1, 0, 1):
            spike(p, x + 1.4, 32.1, z + (-0.8 if z < -10 else 0.8) + k * 0.6, 0.18, 0.7, BONE, verts=3)
    # spread wings: bone arm, fingers and scalloped membranes (left and right of the body)
    for s in (-1, 1):
        sh = (-63.0, 42.4, -10 + s * 2.2)
        el = (-64.2, 47.4, -10 + s * 7.0)
        wr = (-66.0, 50.6, -10 + s * 11.2)
        tips = [(-60.0, 41.5, -10 + s * 13.4), (-65.5, 39.0, -10 + s * 13.0), (-71.5, 40.5, -10 + s * 10.0)]
        tube(p, sh, el, 0.8, 0.65, BONE, verts=5)
        tube(p, el, wr, 0.65, 0.5, BONE, verts=5)
        dk.ball(p, wr, 0.8, DBONE, subdiv=1)
        for t in tips:
            tube(p, wr, t, 0.45, 0.14, BONE, verts=4)
        base_in = (-69.5, 39.4, -10 + s * 3.0)
        sheet(p, [sh, wr, tips[0], (-60.5, 40.2, -10 + s * 3.0)], S1)
        for i in range(2):
            a, b = tips[i], tips[i + 1]
            m = ((a[0] + b[0]) / 2 + (wr[0] - (a[0] + b[0]) / 2) * 0.35, (a[1] + b[1]) / 2 + (wr[1] - (a[1] + b[1]) / 2) * 0.35, (a[2] + b[2]) / 2 + (wr[2] - (a[2] + b[2]) / 2) * 0.35)
            sheet(p, [wr, a, m, b], DSCALE if i % 2 == 0 else S2)
        sheet(p, [wr, tips[2], base_in], S1)
        spike(p, wr[0] - 0.3, wr[1] + 0.2, wr[2] + s * 0.3, 0.3, 1.0, DBONE, verts=4)


# ---- build registry: every function build_<PartId> above, in blueprint order ------------------------------------------
AZ = {"Cave": 215, "Hoard": 215, "GreatDragon": 215, "Forge": 335, "Baby": 215}
ELEV_OLD = {}
ELEV = {"Spires": 40}
MULT = {"Ground": 1.5, "Cave": 2.2, "GreatDragon": 2.2, "Volcano": 2.2, "Keep": 2.3}
SHIBA_AT = {"Ground": (-30, -6, 0, 0)}


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
    if ONLY == ["_boxes"]:
        for pj in BP["Parts"]:
            lo, hi = union(pj)
            print("UBOX %-12s x %7.2f %7.2f  y %6.2f %6.2f  z %7.2f %7.2f  size %5.1f %5.1f %5.1f" % (
                pj["Id"], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        return
    built = {}
    for pj in BP["Parts"]:
        pid = pj["Id"]
        fn = globals().get("build_" + pid)
        if fn is None or (ONLY and pid not in ONLY):
            continue
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_DragonLair.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
