"""Final low-poly decor models for the theme IcePalace (25 parts around the twentieth Shiba, Frost Shiba).

Usage: blender --background --factory-startup --python build_IcePalace.py -- <outdir> [PartId ...]
Writes Decor_IcePalace_<PartId>.fbx, preview_<PartId>.png and stage_IcePalace.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then). No glow: lamps, crystals and aurora are plain flat colours.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "IcePalace"))
ONLY = [s for a in ARGS[1:] for s in a.split(",") if s]
KEY = "IcePalace"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_IcePalace.json"))

# ---- palette (shared by all 25 parts) -------------------------------------------------------------------------------
SNOW = (240, 246, 252)
SNOWS = (214, 226, 240)   # shaded snow
PALE = (205, 235, 252)
ICE = (170, 225, 255)
ICED = (110, 170, 230)
DEEP = (70, 120, 200)
STONE = (130, 150, 178)
STONEL = (160, 178, 202)
DARK = (50, 70, 100)
CYAN = (110, 230, 245)
WOOD = (130, 92, 62)
WOODD = (90, 62, 42)
WOODL = (160, 118, 80)
RED = (205, 60, 60)
GOLD = (245, 205, 90)
GREEN = (80, 200, 150)
PURPLE = (170, 110, 230)
BLACK = (30, 36, 48)
STEEL = (176, 186, 200)
TEAL = (90, 200, 210)
ORG = (240, 140, 50)


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



# ---- fit to the union box of the blueprint pieces --------------------------------------------------------------------
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



def B(p, cx, cy, cz, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Box from centre and size."""
    return dk.box(p, (cx, cy, cz), (sx, sy, sz), col, rot=rot, jitter=jit)


def lean(a, ux, uz):
    """Rotation that leans a standing piece by a degrees toward (ux, uz) (same convention as the theme's crystal())."""
    return (a * uz, 0, -a * ux)


def crystal(p, x, y0, z, r, h, col, rot=(0, 0, 0), sides=6, tip=0.3, jit=0.06):
    """Faceted crystal standing on (x, y0, z): prism of radius r, pointed top, rotated about its foot."""
    pts, faces = [], []
    for k in range(sides):
        a = 2 * math.pi * k / sides + math.pi / sides
        pts.append((r * 0.8 * math.cos(a), 0, r * 0.8 * math.sin(a)))
    for k in range(sides):
        a = 2 * math.pi * k / sides + math.pi / sides
        pts.append((r * math.cos(a), h * (1 - tip), r * math.sin(a)))
    pts.append((0, h, 0))
    faces.append(tuple(range(sides)))
    for k in range(sides):
        q = (k + 1) % sides
        faces.append((k, q, sides + q, sides + k))
        faces.append((sides + k, sides + q, 2 * sides))
    return dk.poly(p, (x, y0, z), pts, faces, col, jit, rot=rot)


def spike(p, x, y0, z, r, h, col, verts=5, rot=(0, 0, 0), jit=0.05):
    """Pointed cone standing on (x, y0, z), optionally leaned (rotated about its foot)."""
    if rot == (0, 0, 0):
        return dk.cone(p, (x, y0, z), r, h, col, verts=verts, jitter=jit)
    pts = [(r * math.cos(2 * math.pi * k / verts), 0, r * math.sin(2 * math.pi * k / verts)) for k in range(verts)]
    pts.append((0, h, 0))
    faces = [tuple(range(verts))] + [(k, (k + 1) % verts, verts) for k in range(verts)]
    return dk.poly(p, (x, y0, z), pts, faces, col, jit, rot=rot)


def icicle(p, x, ytop, z, r, ln, col=ICE, verts=5):
    """Icicle hanging down from ytop."""
    return dk.cyl(p, (x, ytop - ln / 2, z), 0.03, ln, col, axis='y', verts=verts, top_radius=r, jitter=0.04)


def mound(p, cx, y0, cz, rx, h, rz, col, col2=None, segs=12, rings=3, jit=0.04):
    """Half ellipsoid dome (foot on y0) built from stacked frusta; col2 gives every second ring another colour (brick rows)."""
    out = []
    for k in range(rings):
        a0 = (k / rings) * math.pi / 2
        a1 = ((k + 1) / rings) * math.pi / 2
        r0, r1 = math.cos(a0), math.cos(a1)
        if k == rings - 1:
            r1 = 0.0
        yb, yt = math.sin(a0) * h, math.sin(a1) * h
        c = col2 if (col2 and k % 2 == 1) else col
        o = dk.cyl(p, (cx, y0 + (yb + yt) / 2, cz), rx * r0, yt - yb, c, axis='y', verts=segs, top_radius=rx * r1 if r1 > 0 else 0.0,
                   jitter=jit)
        if abs(rz - rx) > 1e-6:
            o.data.transform(Matrix.Diagonal((1, rz / rx, 1, 1)))
        out.append(o)
    return out


def lamp(p, x, z, h, post=DARK):
    vcyl(p, x, 0, 0.5, z, 0.7, post, verts=8, jit=0.02)
    vcyl(p, x, 0.5, h - 0.8, z, 0.25, post, verts=6, jit=0.02)
    B(p, x, h - 0.4, z, 1.5, 0.8, 1.5, GOLD, jit=0.02)
    B(p, x, h + 0.15, z, 2.0, 0.35, 2.0, SNOW, jit=0.02)


def tree_tiers(p, x, y0, z, r, h, col, tiers=3, verts=8):
    """Fir tree: stacked cones."""
    for k in range(tiers):
        f = k / tiers
        dk.cyl(p, (x, y0 + h * (0.12 + f * 0.62) + h * 0.2, z), r * (1 - f * 0.55), h * 0.4, col, axis='y', verts=verts,
               top_radius=0.0, jitter=0.05)


def prism_x(p, tri, x0, x1, col, jit=0.04):
    """Triangular prism: tri = three (z, y) points, extruded along x from x0 to x1."""
    pts = [(x0, b, a) for a, b in tri] + [(x1, b, a) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def arch_win_z(p, cx, y0, w, h, z, sgn, pane=CYAN, frame=PALE):
    """Pointed-arch window on a wall that faces +-z (sgn = +1 or -1)."""
    B(p, cx, y0 + h / 2, z + sgn * 0.15, w + 0.8, h, 0.3, frame, jit=0.02)
    B(p, cx, y0 + h / 2, z + sgn * 0.35, w, h - 0.4, 0.2, pane, jit=0.02)
    prism_z(p, [(cx - w / 2, y0 + h - 0.2), (cx + w / 2, y0 + h - 0.2), (cx, y0 + h - 0.2 + w * 0.7)], z + sgn * 0.3, z + sgn * 0.5, pane, 0.02)


def arch_win_x(p, x, y0, w, h, cz, sgn, pane=CYAN, frame=PALE):
    """Pointed-arch window on a wall that faces +-x."""
    B(p, x + sgn * 0.15, y0 + h / 2, cz, 0.3, h, w + 0.8, frame, jit=0.02)
    B(p, x + sgn * 0.35, y0 + h / 2, cz, 0.2, h - 0.4, w, pane, jit=0.02)
    prism_x(p, [(cz - w / 2, y0 + h - 0.2), (cz + w / 2, y0 + h - 0.2), (cz, y0 + h - 0.2 + w * 0.7)], x + sgn * 0.3, x + sgn * 0.5, pane, 0.02)


# ---- 1. Ground -------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    B(p, 0, 0.15, 0, 190, 0.3, 130, SNOW, jit=0.03)
    # winding walkway of trampled snow
    path = [(0, 60), (-44, 50), (6, 32), (-38, 12), (-40, -16), (-24, -44), (0, -60)]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        ang = math.degrees(math.atan2(-(z1 - z0), x1 - x0))
        B(p, (x0 + x1) / 2, 0.33, (z0 + z1) / 2, L, 0.06, 6.5, SNOWS, rot=(0, ang, 0), jit=0.03)
    for (x, z) in path[1:-1]:
        vcyl(p, x, 0.3, 0.36, z, 3.25, SNOWS, verts=10, jit=0.03)

    # frozen lake: ice plates, deep blue patch, cracks and white glints
    def plate(cx, cz, sx, sz, col, y0=0.3, y1=0.43):
        B(p, cx, (y0 + y1) / 2, cz, sx, y1 - y0, sz, col, jit=0.03)
    B(p, 64, 0.35, 28, 58, 0.1, 36, PALE, jit=0.02)
    B(p, 52, 0.35, 46, 34, 0.1, 12, PALE, jit=0.02)
    plate(64, 28, 56, 34, ICE)
    plate(52, 46, 32, 10, ICE)
    plate(86, 12, 14, 18, ICED, 0.25, 0.43)
    for (cx, cz, L, ang) in ((58, 24, 16, 20), (70, 33, 14, -30), (78, 24, 10, 55), (49, 46, 9, 10), (58, 46, 7, -35),
                              (86, 12, 8, 70), (66, 18, 8, -10)):
        B(p, cx, 0.43, cz, L, 0.04, 0.35, DEEP, rot=(0, ang, 0), jit=0.02)
    for (cx, cz, L, ang) in ((60, 30, 5, 15), (72, 24, 4, -20), (50, 44, 4, 5), (84, 8, 3, 40), (66, 38, 4, 25)):
        B(p, cx, 0.435, cz, L, 0.04, 0.5, SNOW, rot=(0, ang, 0), jit=0.02)
    # forecourt before the palace: pale ice tiles
    plate(60, -45, 50, 38, PALE, 0.2, 0.4)
    plate(30, -46, 14, 10, PALE, 0.2, 0.4)
    for i in range(5):
        for j in range(4):
            if (i + j) % 2 == 0:
                B(p, 40 + i * 10, 0.415, -62 + j * 9.5 + 1.0, 9.6, 0.05, 8.6, ICE, jit=0.03)
    B(p, 30, 0.415, -46, 12.6, 0.05, 8.6, ICE, jit=0.03)
    # gold-trimmed forecourt edge and snowflake emblem ring
    B(p, 60, 0.42, -26.2, 50, 0.04, 0.6, GOLD, jit=0.02)
    vcyl(p, 6, 0.3, 0.37, -22, 6.4, GOLD, verts=16, jit=0.02)
    vcyl(p, 6, 0.37, 0.4, -22, 5.6, ICE, verts=16, jit=0.02)
    for k in range(3):
        B(p, 6, 0.42, -22, 10, 0.04, 0.9, SNOW, rot=(0, k * 60, 0), jit=0.02)
    vcyl(p, 6, 0.4, 0.43, -22, 1.8, SNOW, verts=12, jit=0.02)
    # soft drifts
    for (x, z, rx, rz) in ((-60, 40, 7, 4), (-30, -58, 8, 4), (40, 58, 8, 4), (-88, 0, 4, 7), (88, -40, 4, 7), (20, 30, 5, 3)):
        dk.ball(p, (x, 0.3, z), 1.0, SNOW, scale=(rx, 0.13, rz), subdiv=1, jitter=0.03)
    # snow patches
    for (x, z, sx, sz) in ((-70, 50, 16, 10), (-45, 30, 12, 7), (30, 45, 14, 8), (-20, 55, 14, 8), (-80, -30, 12, 9), (20, 10, 10, 8), (-10, -50, 12, 8),
                           (76, -10, 12, 8), (-60, 20, 8, 6)):
        B(p, x, 0.33, z, sx, 0.06, sz, SNOWS, jit=0.05)


# ---- 2. Palace -------------------------------------------------------------------------------------------------------------
def build_Palace(p):
    # stepped stone plinth
    B(p, 67, 0.5, -47, 44, 1, 28, STONE, jit=0.05)
    B(p, 67, 1.5, -47, 42, 1, 26, STONEL, jit=0.05)
    # great hall
    B(p, 67, 8, -47, 34, 12, 20, ICE, jit=0.05)
    for z, sg in ((-57.2, 1), (-36.8, -1)):                       # pilasters on the long walls
        for x in (52, 82):
            B(p, x, 8, z + 0.3 * sg, 1.4, 12, 0.7, PALE, jit=0.03)
    for x in (55.5, 62.5, 71.5, 78.5):
        arch_win_z(p, x, 5.5, 1.8, 4.2, -36.95, 1)
    arch_win_x(p, 84.05, 6, 2, 4.5, -47, 1)
    for z in (-54.5, -39.5):
        arch_win_x(p, 49.95, 6, 1.6, 4.5, z, -1)
    B(p, 67, 14.3, -47, 35, 0.7, 21, STONEL, jit=0.03)          # roof deck / cornice
    for i in range(7):                                        # crenellations along the front and back
        x = 51.5 + i * 5.4
        for z in (-56.8, -37.2):
            B(p, x, 15.2, z, 2.4, 1.2, 1.2, PALE, jit=0.04)
    for i in range(3):
        z = -55 + i * 9
        for x in (50.8, 83.2):
            B(p, x, 15.2, z, 1.2, 1.2, 1.8, PALE, jit=0.04)
    # entrance porch on the front (-x) side with a pointed arch door
    B(p, 48, 4, -53.4, 6, 4, 3.4, DEEP, jit=0.04)
    B(p, 48, 4, -40.6, 6, 4, 3.4, DEEP, jit=0.04)
    B(p, 48, 7.2, -47, 6, 1.6, 10, DEEP, jit=0.04)
    dk.prism(p, (48, 8, -47), 6.6, 10.6, 2.6, ICE, ridge='x', jitter=0.04)
    B(p, 50.2, 4.2, -47, 0.5, 4.4, 3.4, DARK, jit=0.02)
    prism_x(p, [(-48.7, 6.4), (-45.3, 6.4), (-47, 8.2)], 49.9, 50.5, DARK, 0.02)
    B(p, 47.5, 2.1, -47, 5, 0.2, 3.6, RED, jit=0.02)             # red carpet
    for z in (-50.4, -43.6):
        crystal(p, 45.6, 8.2, z, 0.7, 2.6, CYAN, jit=0.04)
    # central keep with onion dome
    vcyl(p, 67, 14, 28, -49, 7, PALE, verts=12, jit=0.04)
    vcyl(p, 67, 22, 23, -49, 7.4, STONEL, verts=12, jit=0.03)
    for k in range(6):
        a = math.radians(150 + k * 36)
        x, z = 67 + 7.05 * math.cos(a), -49 + 7.05 * math.sin(a)
        B(p, x, 19.2, z, 1.0, 2.4, 1.0, CYAN, rot=(0, -math.degrees(a), 0), jit=0.02)
    vcyl(p, 67, 28, 29, -49, 7.8, GOLD, verts=12, jit=0.03)
    mound(p, 67, 29, -49, 6.2, 4.6, 6.2, DEEP, ICED, segs=12, rings=2)
    spike(p, 67, 33.2, -49, 0.9, 0.8, GOLD, verts=6)
    # corner towers with cone roofs
    for (x, z) in ((49, -37), (85, -37), (49, -57), (85, -57)):
        vcyl(p, x, 1, 22, z, 3.5, ICE, verts=8, jit=0.05)
        for y in ():
            vcyl(p, x, y, y + 0.9, z, 3.8, PALE, verts=8, jit=0.03)
        vcyl(p, x, 22, 23, z, 4.3, STONEL, verts=8, jit=0.03)
        dk.cyl(p, (x, 25.2, z), 4.4, 4.4, DEEP, axis='y', verts=8, top_radius=0.0, jitter=0.04)
        B(p, x, 26.6, z, 0.2, 3, 0.2, STEEL, jit=0.02)
        B(p, x + 0.9, 29, z, 1.6, 0.9, 0.12, GOLD, jit=0.02)
        for sx, sz in ((-1, 0), (0, 1)) if z > -50 else ((-1, 0), (0, -1)):
            B(p, x + sx * 3.45, 12.5, z + sz * 3.45, 0.7 if sx else 1.1, 3, 1.1 if sx else 0.7, CYAN, jit=0.02)
    # lantern pylons on the plinth corners
    for (x, z) in ((45.8, -33.6), (88.2, -33.6)):
        B(p, x, 3.4, z, 1.2, 2.8, 1.2, STONEL, jit=0.03)
        B(p, x, 5.4, z, 1.0, 1.2, 1.0, GOLD, jit=0.02)


# ---- 3. Halo ---------------------------------------------------------------------------------------------------------------
HALO = [(2.25, -36, 12, 12, 0.26, -0.97, ICE), (-3.32, -33.1, 16, 12, -0.64, -0.77, CYAN),
        (-7.14, -28.13, 11, 12, -0.91, -0.42, ICE), (-8.5, -22, 18, 12, -1, 0, PURPLE),
        (-7.14, -15.87, 11, 12, -0.91, 0.42, ICE), (-3.32, -10.9, 16, 12, -0.64, 0.77, CYAN),
        (2.25, -8, 12, 12, 0.26, 0.97, ICE)]
HALO2 = [(-8.28, -32.96, 6, 14, -0.79, -0.61), (-11.57, -25.9, 6, 14, -0.98, -0.22), (-11.57, -18.1, 6, 14, -0.98, 0.22),
         (-8.28, -11.04, 6, 14, -0.79, 0.61)]


def build_Halo(p):
    for (x, z, h, a, ux, uz, col) in HALO:
        mound(p, x, 0, z, 1.9, 0.9, 1.9, SNOW, segs=8, rings=2)
        crystal(p, x, 0.2, z, 1.35, h - 0.2, col, rot=lean(a, ux, uz), tip=0.28)
    for (x, z, h, a, ux, uz) in HALO2:
        crystal(p, x, 0, z, 0.85, h, GREEN, rot=lean(a, ux, uz), tip=0.35)
    # small shards between the big ones
    for (x, z, h, a, ux, uz, col) in ((-0.5, -34.6, 4.5, 10, -0.3, -0.95, PALE), (-6.2, -31, 4, 10, -0.8, -0.6, PALE),
                                       (-9.2, -25, 3.6, 10, -1, 0, ICED), (-9.2, -19, 3.6, 10, -1, 0, ICED),
                                       (-6.2, -13, 4, 10, -0.8, 0.6, PALE), (-0.5, -9.4, 4.5, 10, -0.3, 0.95, PALE)):
        crystal(p, x, 0, z, 0.65, h, col, rot=lean(a, ux, uz), tip=0.35)


# ---- 4. Gate ---------------------------------------------------------------------------------------------------------------
def build_Gate(p):
    B(p, 36.5, 0.25, -47, 7, 0.5, 11, PALE, jit=0.03)
    for k in (0, 2):
        B(p, 34.4 + k * 1.4, 0.55, -47, 1.2, 0.1, 10.4, ICE, jit=0.03)
    for z in (-53, -41):
        B(p, 38, 0.5, z, 4.2, 1.0, 4.2, STONE, jit=0.04)
        B(p, 38, 7.5, z, 3, 13, 3, ICE, jit=0.05)
        for dx, dz in ((1.45, 0), (-1.45, 0), (0, 1.45), (0, -1.45)):
            B(p, 38 + dx, 7.5, z + dz, 0.5 if dx else 2.2, 12, 2.2 if dx else 0.5, PALE, jit=0.03)
        B(p, 38, 13.4, z, 4, 1.2, 4, PALE, jit=0.03)
        B(p, 38, 14.3, z, 3, 0.7, 3, SNOW, jit=0.03)
    B(p, 38, 13.5, -47, 3.4, 3, 15.4, DEEP, jit=0.04)
    B(p, 38, 15.1, -47, 3.8, 0.5, 15.8, PALE, jit=0.03)
    prism_x(p, [(-51.5, 12), (-51.5, 9.4), (-48.8, 12)], 36.3, 39.7, ICED, 0.04)
    prism_x(p, [(-42.5, 12), (-42.5, 9.4), (-45.2, 12)], 36.3, 39.7, ICED, 0.04)
    for z in (-50, -48.5, -47, -45.5, -44):
        icicle(p, 38, 12, z, 0.3, 1.6 if z == -47 else 1.0, PALE)
    crystal(p, 38, 15.2, -47, 1.2, 5.9, CYAN, tip=0.4)
    crystal(p, 38, 15.2, -50.6, 0.8, 3.6, ICE, rot=lean(8, 0, -1), tip=0.4)
    crystal(p, 38, 15.2, -43.4, 0.8, 3.6, ICE, rot=lean(8, 0, 1), tip=0.4)
    for z in (-57.5, -36.5):
        mound(p, 38.2, 0, z, 2.5, 3.0, 2.5, SNOW, SNOWS, segs=10, rings=3)
        crystal(p, 39.3, 0.8, z + (-0.8 if z < -50 else 0.8), 0.5, 2.6, ICE, rot=lean(12, 1, 0), tip=0.4)


# ---- 5. Igloo --------------------------------------------------------------------------------------------------------------
def tunnel_x(p, x0, x1, z, r, col):
    B(p, (x0 + x1) / 2, r * 0.37, z, x1 - x0, r * 0.74, 2 * r, col, jit=0.03)
    dk.cyl(p, ((x0 + x1) / 2, r * 0.74, z), r, x1 - x0, col, axis='x', verts=10, jitter=0.03)


def build_Igloo(p):
    mound(p, -79, 0, 24, 7.5, 9, 7.5, SNOW, SNOWS, segs=14, rings=5)
    tunnel_x(p, -74.4, -67.6, 24, 2.3, SNOW)
    B(p, -67.5, 1.0, 24, 0.3, 2, 1.8, DARK, jit=0.02)
    dk.cyl(p, (-67.5, 2.0, 24), 0.9, 0.3, DARK, axis='x', verts=8, jitter=0.02)
    mound(p, -72, 0, 34, 5, 6.4, 5, SNOW, SNOWS, segs=12, rings=4)
    tunnel_x(p, -69.7, -64.7, 34, 1.8, SNOW)
    B(p, -64.8, 0.85, 34, 0.3, 1.7, 1.5, DARK, jit=0.02)
    dk.cyl(p, (-64.8, 1.7, 34), 0.75, 0.3, DARK, axis='x', verts=8, jitter=0.02)
    # ice block seams around both domes
    for (cx, cz, rx, h, hs) in ((-79, 24, 7.5, 9, (2.2, 4.3, 6.2, 7.7)), (-72, 34, 5, 6.4, (1.6, 3.1, 4.4, 5.4))):
        for y in hs:
            vcyl(p, cx, y - 0.14, y + 0.14, cz, rx * math.sqrt(max(0.05, 1 - (y / h) ** 2)) * 1.02, ICED, verts=14, jit=0.02)
    # stack of cut ice blocks
    B(p, -84.6, 1.2, 33.4, 1.9, 2.4, 2.6, ICE, rot=(0, 8, 0), jit=0.05)
    B(p, -83.0, 1.2, 34.6, 1.8, 2.4, 2.6, ICED, rot=(0, -6, 0), jit=0.05)
    B(p, -83.8, 3.1, 34.0, 2.4, 1.6, 2.4, PALE, rot=(0, 15, 0), jit=0.05)
    # flag pole with a red flag
    vcyl(p, -64, 0, 9, 28, 0.3, WOOD, verts=6, jit=0.03)
    B(p, -62.8, 8, 28, 2.4, 1.6, 0.2, RED, jit=0.03)
    # shovel stuck in the snow and a little pile of snowballs
    B(p, -85.2, 1.4, 20.6, 0.2, 3.2, 0.2, WOOD, rot=(0, 0, 8), jit=0.03)
    B(p, -85.5, 0.5, 20.6, 0.9, 1.0, 0.2, STEEL, rot=(0, 0, 8), jit=0.03)
    for (x, z) in ((-68, 28.5), (-66.5, 29.6), (-67.4, 30.6)):
        dk.ball(p, (x, 0.65, z), 0.65, SNOW, subdiv=1, jitter=0.03)


# ---- 6. Rink ---------------------------------------------------------------------------------------------------------------
def goal(p, x, z, d):
    """Small hockey goal at x; d = +1 means the net sits behind it toward -x."""
    for dz in (-1.5, 1.5):
        B(p, x, 1.0, z + dz, 0.25, 2.0, 0.25, RED, jit=0.02)
    B(p, x, 2.0, z, 0.25, 0.25, 3.25, RED, jit=0.02)
    B(p, x - d * 0.9, 1.0, z, 0.1, 1.9, 2.9, PALE, jit=0.02)
    for dz in (-1.5, 1.5):
        B(p, x - d * 0.45, 1.0, z + dz, 0.9, 1.9, 0.08, PALE, jit=0.02)
    B(p, x - d * 0.45, 2.0, z, 0.9, 0.08, 3.0, PALE, jit=0.02)


def build_Rink(p):
    B(p, 54, 0.35, 34, 28, 0.3, 16, PALE, jit=0.03)
    B(p, 54, 0.52, 34, 26, 0.05, 14, ICE, jit=0.03)
    vcyl(p, 54, 0.5, 0.56, 34, 3.4, ICED, verts=18, jit=0.02)
    vcyl(p, 54, 0.5, 0.6, 34, 2.9, PALE, verts=18, jit=0.02)
    B(p, 54, 0.57, 34, 0.35, 0.05, 14, ICED, jit=0.02)
    for x in (47, 61):
        B(p, x, 0.57, 34, 0.3, 0.05, 14, RED, jit=0.02)
    # skate marks
    for (cx, cz, L, a) in ((47, 30, 6, 10), (60, 38, 7, -15), (52, 38, 5, 30), (58, 29.5, 5, -25)):
        B(p, cx, 0.56, cz, L, 0.03, 0.18, SNOW, rot=(0, a, 0), jit=0.02)
    # wooden rim boards with an opening in front
    B(p, 54, 0.8, 25.6, 29.6, 1.4, 0.8, WOOD, jit=0.05)
    B(p, 39.6, 0.8, 34, 0.8, 1.4, 16.8, WOOD, jit=0.05)
    B(p, 68.4, 0.8, 34, 0.8, 1.4, 16.8, WOOD, jit=0.05)
    B(p, 45.6, 0.8, 42.4, 12.8, 1.4, 0.8, WOOD, jit=0.05)
    B(p, 62.4, 0.8, 42.4, 12.8, 1.4, 0.8, WOOD, jit=0.05)
    B(p, 54, 1.6, 25.6, 29.8, 0.25, 1.0, WOODL, jit=0.03)
    B(p, 39.6, 1.6, 34, 1.0, 0.25, 17, WOODL, jit=0.03)
    B(p, 68.4, 1.6, 34, 1.0, 0.25, 17, WOODL, jit=0.03)
    B(p, 45.6, 1.6, 42.4, 13, 0.25, 1.0, WOODL, jit=0.03)
    B(p, 62.4, 1.6, 42.4, 13, 0.25, 1.0, WOODL, jit=0.03)
    for x in (43, 48, 53, 58, 63, 67.6):
        B(p, x, 0.9, 25.6, 0.6, 1.6, 1.0, WOODD, jit=0.03)
    for z in (29, 34, 39):
        for x in (39.6, 68.4):
            B(p, x, 0.9, z, 1.0, 1.6, 0.6, WOODD, jit=0.03)
    for x in (40.4, 52, 56, 67.6):
        B(p, x, 0.9, 42.4, 0.6, 1.6, 1.0, WOODD, jit=0.03)
    goal(p, 43, 34, 1)
    goal(p, 65, 34, -1)
    lamp(p, 41, 27.5, 6.7)
    lamp(p, 67, 27.5, 6.7)
    # bench with backrest and a pair of skates
    B(p, 54, 1.2, 27.2, 6, 0.4, 1.4, WOOD, jit=0.04)
    B(p, 54, 2.0, 26.5, 6, 1.0, 0.3, WOOD, jit=0.04)
    for x in (51.3, 56.7):
        B(p, x, 0.7, 27.2, 0.4, 1.0, 1.2, WOODD, jit=0.03)
    for x in (53.2, 54.6):
        B(p, x, 1.65, 27.4, 0.6, 0.5, 1.0, RED, jit=0.03)
        B(p, x, 1.3, 27.4, 0.2, 0.2, 1.2, STEEL, jit=0.02)


# ---- 7. Snowmen --------------------------------------------------------------------------------------------------------------
def snowman(p, x, z, d, hat, scarf, arms=True):
    def ball_(cy, r, sy):
        return dk.ball(p, (x, cy, z), r, SNOW, scale=(1, sy, 1), subdiv=1, jitter=0.03)
    ball_(0.43 * d, 0.5 * d, 0.86)
    ball_(1.13 * d, 0.36 * d, 0.92)
    ball_(1.69 * d, 0.26 * d, 1.0)
    hy, hr = 1.69 * d, 0.26 * d
    for dx in (-0.1 * d, 0.1 * d):                                            # coal eyes
        B(p, x + dx, hy + 0.06 * d, z + hr * 0.92, 0.09 * d, 0.09 * d, 0.07 * d, BLACK, jit=0.01)
    dk.cyl(p, (x, hy - 0.01 * d, z + hr + 0.1 * d), 0.03, 0.26 * d, ORG, axis='z', verts=5, top_radius=0.045 * d, jitter=0.02)
    for k in range(3):                                                         # buttons
        B(p, x, (1.3 - k * 0.2) * d, z + 0.34 * d, 0.08 * d, 0.08 * d, 0.07 * d, BLACK, jit=0.01)
    vcyl(p, x, 1.4 * d, 1.4 * d + 0.12 * d, z, 0.3 * d, scarf, verts=10, jit=0.03)
    B(p, x + 0.12 * d, 1.22 * d, z + 0.33 * d, 0.14 * d, 0.38 * d, 0.07 * d, scarf, jit=0.03)
    if arms:
        for s in (-1, 1):
            B(p, x + s * (0.36 * d + 0.55 * d), 1.2 * d + 0.12 * d, z, 0.9 * d, 0.07 * d, 0.07 * d, WOOD, rot=(0, 0, s * 25), jit=0.03)
            B(p, x + s * (0.36 * d + 0.95 * d), 1.2 * d + 0.34 * d, z, 0.3 * d, 0.06 * d, 0.06 * d, WOOD, rot=(0, 0, -s * 30), jit=0.03)
    top = hy + hr * 0.75
    if hat == 'top':
        vcyl(p, x, top - 0.1 * d, top + 0.1 * d, z, 0.5 * d, BLACK, verts=10, jit=0.02)
        vcyl(p, x, top, top + 0.42 * d, z, 0.32 * d, BLACK, verts=10, jit=0.02)
        vcyl(p, x, top + 0.04 * d, top + 0.14 * d, z, 0.335 * d, RED, verts=10, jit=0.02)
    elif hat == 'bucket':
        dk.cyl(p, (x, top + 0.18 * d, z), 0.3 * d, 0.5 * d, STEEL, axis='y', verts=10, top_radius=0.36 * d, jitter=0.03)
        vcyl(p, x, top - 0.02 * d, top + 0.04 * d, z, 0.5 * d, STEEL, verts=10, jit=0.03)
    else:                                                                       # knit beanie with pompom
        dk.cyl(p, (x, top + 0.1 * d, z), 0.3 * d, 0.34 * d, RED, axis='y', verts=10, top_radius=0.2 * d, jitter=0.03)
        dk.ball(p, (x, top + 0.38 * d, z), 0.1 * d, SNOW, subdiv=1, jitter=0.02)


def build_Snowmen(p):
    snowman(p, -62, -6, 7, 'top', RED)
    snowman(p, -54, -2, 5.4, 'bucket', GREEN)
    snowman(p, -57, -12, 4, 'beanie', GOLD)
    for (x, z) in ((-58.5, -1.2), (-60, 0.2), (-64.6, -0.9)):
        dk.ball(p, (x, 0.5, z), 0.5, SNOW, subdiv=1, jitter=0.03)
    B(p, -66.5, 3.2, -9.5, 0.2, 6.4, 0.2, WOOD, rot=(0, 0, 10), jit=0.03)
    B(p, -66.9, 0.5, -9.5, 1.3, 1.0, 0.8, WOODL, rot=(0, 0, 10), jit=0.03)


# ---- 8. Sled ---------------------------------------------------------------------------------------------------------------
def present(p, x, y0, z, sx, sy, sz, col, rib, rot=(0, 0, 0)):
    B(p, x, y0 + sy / 2, z, sx, sy, sz, col, rot=rot, jit=0.04)
    B(p, x, y0 + sy / 2, z, sx + 0.08, sy + 0.08, 0.35, rib, rot=rot, jit=0.02)
    B(p, x, y0 + sy / 2, z, 0.35, sy + 0.08, sz + 0.08, rib, rot=rot, jit=0.02)
    B(p, x - 0.3, y0 + sy + 0.2, z, 0.6, 0.4, 0.4, rib, rot=(0, 0, 30), jit=0.02)
    B(p, x + 0.3, y0 + sy + 0.2, z, 0.6, 0.4, 0.4, rib, rot=(0, 0, -30), jit=0.02)


def build_Sled(p):
    B(p, 24, 1.6, 36, 10, 0.8, 4.6, RED, jit=0.04)
    for k in range(4):
        B(p, 20.5 + k * 2.3, 2.02, 36, 0.12, 0.06, 4.6, WOODD, jit=0.02)
    B(p, 19.2, 3.2, 36, 0.8, 3.2, 4.6, RED, jit=0.04)
    B(p, 19.2, 4.9, 36, 1.2, 0.4, 5.0, WOODD, jit=0.03)
    for z in (34, 38):
        B(p, 23.6, 0.7, z, 10.6, 0.5, 0.5, DARK, jit=0.03)
        B(p, 29.15, 1.05, z, 1.6, 0.5, 0.5, DARK, rot=(0, 0, 35), jit=0.03)
        for x in (20.6, 23.6, 26.6):
            B(p, x, 1.15, z, 0.4, 0.9, 0.4, WOODD, jit=0.03)
    present(p, 22, 2.0, 36, 3.2, 2.6, 3, GREEN, GOLD)
    present(p, 25.2, 2.0, 35.4, 3.6, 2.2, 3.4, PURPLE, ICE)
    present(p, 23.6, 4.6, 36.4, 2.4, 1.8, 2.4, GOLD, RED, rot=(0, 12, 0))
    present(p, 21.8, 4.6, 35.4, 1.4, 1.2, 1.4, DEEP, SNOW)
    # sack of toys
    dk.ball(p, (27.4, 3.4, 37.4), 1.6, WOOD, subdiv=1, jitter=0.05)
    dk.cyl(p, (27.4, 5.1, 37.4), 0.35, 0.7, WOODD, axis='y', verts=6, top_radius=0.6, jitter=0.03)
    B(p, 27.4, 4.75, 37.4, 1.1, 0.18, 1.1, RED, jit=0.02)
    # striped little tree
    vcyl(p, 30.2, 0, 0.8, 34.6, 0.5, WOODD, verts=6, jit=0.03)
    tree_tiers(p, 30.2, 0.4, 34.6, 1.55, 6.0, GREEN, tiers=3)
    for (y, r, c) in ((1.6, 1.45, RED), (3.2, 1.1, GOLD)):
        dk.ball(p, (30.2 + r * 0.7, y, 34.6 + r * 0.7), 0.2, c, subdiv=1, jitter=0.02)
        dk.ball(p, (30.2 - r * 0.7, y + 0.6, 34.6 + r * 0.7), 0.2, c, subdiv=1, jitter=0.02)
    crystal(p, 30.2, 5.7, 34.6, 0.4, 1.1, GOLD, tip=0.5)


# ---- 9. Fountain -----------------------------------------------------------------------------------------------------------
def build_Fountain(p):
    cx, cz = 30, 14
    vcyl(p, cx, 0, 2, cz, 7.5, STONE, verts=16, jit=0.05)
    torus(p, (cx, 2.0, cz), 7.0, 0.6, STONEL, segs=16, sides=4)
    vcyl(p, cx, 2.0, 2.4, cz, 6.5, ICED, verts=16, jit=0.04)
    for k in range(8):                                                       # frozen ripples on the basin
        a = math.radians(k * 45 + 10)
        B(p, cx + 4.6 * math.cos(a), 2.45, cz + 4.6 * math.sin(a), 2.0, 0.08, 0.4, PALE, rot=(0, -math.degrees(a) + 90, 0), jit=0.02)
    vcyl(p, cx, 2.4, 7.4, cz, 1.4, PALE, verts=8, top_r=1.1, jit=0.04)
    dk.cyl(p, (cx, 7.8, cz), 1.6, 1.3, ICE, axis='y', verts=14, top_radius=4.3, jitter=0.04)
    vcyl(p, cx, 8.4, 8.7, cz, 3.8, ICED, verts=14, jit=0.03)
    vcyl(p, cx, 8.4, 10.6, cz, 0.9, PALE, verts=8, jit=0.04)
    crystal(p, cx, 10.4, cz, 1.2, 3.3, CYAN, tip=0.4)
    for k in range(8):                                                       # ice spikes frozen mid-splash around the bowl
        a = k * math.pi / 4 + 0.2
        ux, uz = math.cos(a), math.sin(a)
        spike(p, cx + ux * 2.6, 8.6, cz + uz * 2.6, 0.4, 2.8 + (k % 2), ICE if k % 2 else PALE, rot=lean(28, ux, uz))
        icicle(p, cx + ux * 3.9, 8.0, cz + uz * 3.9, 0.28, 1.0 + 0.5 * (k % 2), PALE, verts=4)
    for k in range(6):                                                       # crown of tall spikes on the basin rim
        a = k * math.pi / 3 + math.pi / 6
        ux, uz = math.cos(a), math.sin(a)
        spike(p, cx + ux * 6.7, 2.2, cz + uz * 6.7, 0.5, 3.8, ICE, rot=lean(18, ux, uz))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.7
        dk.ball(p, (cx + 7.2 * math.cos(a), 1.9, cz + 7.2 * math.sin(a)), 0.7, SNOW, scale=(1.3, 0.6, 1), subdiv=1, jitter=0.03)


# ---- 10. Cabin -------------------------------------------------------------------------------------------------------------
def build_Cabin(p):
    cx, cz = -80, -14
    B(p, cx, 0.3, cz, 14.6, 0.6, 10.6, STONE, jit=0.05)
    B(p, cx, 4.0, cz, 13, 7.6, 9, WOODD, jit=0.03)
    rows = 6
    for k in range(rows):
        y = 1.0 + k * 1.2
        off = 0.6 if k % 2 else 0
        dk.cyl(p, (cx, y, cz + 5.0), 0.62, 14.4 + off, WOOD if k % 2 else WOODL, axis='x', verts=5, jitter=0.06)
        dk.cyl(p, (cx, y, cz - 5.0), 0.62, 14.4 + off, WOODL if k % 2 else WOOD, axis='x', verts=5, jitter=0.06)
        for s in (-1, 1):
            dk.cyl(p, (cx + s * 6.9, y, cz), 0.62, 10.4 - off, WOOD if k % 2 else WOODL, axis='z', verts=5, jitter=0.06)
    # roof: dark rafters, deep snow on top
    dk.prism(p, (cx, 7.6, cz), 15.4, 12.6, 4.4, WOODD, ridge='x', jitter=0.03)
    dk.prism(p, (cx, 8.2, cz), 16.4, 13.4, 4.4, SNOW, ridge='x', jitter=0.03)
    for s in (-1, 1):
        for i in range(5):
            dk.ball(p, (cx - 6.4 + i * 3.2, 8.3, cz + s * 6.6), 0.9, SNOW, scale=(1.3, 0.8, 1.0), subdiv=1, jitter=0.03)
        for i in range(3):
            icicle(p, cx - 5 + i * 5, 8.2, cz + s * 6.7, 0.18, 1.1, PALE, verts=4)
    # chimney with smoke
    B(p, -84.6, 10.0, -16.5, 2, 7, 2, STONE, jit=0.05)
    B(p, -84.6, 13.4, -16.5, 2.6, 0.5, 2.6, STONEL, jit=0.03)
    for (y, r, dx) in ((14.1, 0.75, 0), (14.5, 0.55, 0.5)):
        dk.ball(p, (-84.6 + dx, y, -16.5), r, SNOWS, subdiv=1, jitter=0.03)
    # door, windows, porch
    B(p, -80, 2.4, -8.3, 2.4, 4.4, 0.3, WOODD, jit=0.03)
    B(p, -80, 2.4, -8.1, 1.7, 3.8, 0.2, WOOD, jit=0.03)
    B(p, -79.2, 2.4, -7.95, 0.2, 0.2, 0.15, GOLD, jit=0.02)
    for x in (-83.8, -76.3):
        B(p, x, 4.6, -8.3, 2.6, 2.4, 0.3, WOODD, jit=0.03)
        B(p, x, 4.6, -8.3, 2.0, 1.8, 0.4, GOLD, jit=0.02)
        B(p, x, 4.6, -8.3, 0.2, 1.9, 0.45, WOODD, jit=0.02)
        B(p, x, 4.6, -8.3, 2.1, 0.2, 0.45, WOODD, jit=0.02)
    B(p, -73.0, 4.6, -14, 0.3, 2.4, 2.6, WOODD, jit=0.03)
    B(p, -72.85, 4.6, -14, 0.2, 1.8, 2.0, GOLD, jit=0.02)
    B(p, -80, 0.25, -7.6, 8, 0.5, 3, WOODD, jit=0.04)
    for x in (-83.5, -76.5):
        B(p, x, 2.5, -7, 0.6, 5, 0.6, WOODD, jit=0.03)
    B(p, -80, 5.3, -7.7, 8.8, 0.4, 3.4, WOODD, rot=(-12, 0, 0), jit=0.03)
    B(p, -80, 5.65, -7.8, 9.2, 0.5, 3.6, SNOW, rot=(-12, 0, 0), jit=0.03)
    B(p, -80, 1.3, -6.3, 7.4, 0.3, 0.3, WOODD, jit=0.03)
    B(p, -80, 3.9, -6.9, 0.5, 0.8, 0.5, GOLD, jit=0.02)
    # fairy lights along the front eave and a wreath on the door
    for i in range(8):
        B(p, -86.0 + i * 1.7, 7.6, -7.15, 0.4, 0.4, 0.4, (RED, GOLD, GREEN, CYAN)[i % 4], jit=0.02)
    dk.cyl(p, (-80, 3.6, -8.0), 0.8, 0.2, GREEN, axis='z', verts=8, jitter=0.03)
    B(p, -80, 2.9, -7.9, 0.5, 0.4, 0.2, RED, jit=0.02)
    # firewood pile
    for (z, y) in ((-13.3, 0.45), (-12.4, 0.45), (-11.5, 0.45), (-10.6, 0.45), (-12.9, 1.25), (-12.0, 1.25), (-11.1, 1.25), (-12.45, 2.0), (-11.55, 2.0)):
        dk.cyl(p, (-74, y, z), 0.45, 3.0, WOODL if (y > 1) else WOOD, axis='x', verts=5, jitter=0.07)
    B(p, -74, 2.55, -12, 3.2, 0.3, 4.0, SNOW, jit=0.03)


# ---- 11. Spires ------------------------------------------------------------------------------------------------------------
def build_Spires(p):
    mound(p, 51, 0, -15, 5, 2.8, 4.5, SNOW, SNOWS, segs=12, rings=3)
    crystal(p, 49, 0.4, -18, 1.8, 17.6, ICED, rot=(4, 0, -5), tip=0.2)
    crystal(p, 52.5, 0.4, -15, 2.0, 25.6, ICE, rot=(-4, 0, 3), tip=0.22)
    crystal(p, 47, 0.4, -13, 1.5, 11.6, PALE, rot=(5, 0, 6), tip=0.25)
    crystal(p, 54.6, 0.4, -18, 0.9, 5.6, CYAN, rot=(0, 0, -14), tip=0.3)
    for (x, z, h, c, a, ux, uz) in ((49.5, -12.2, 3.6, ICE, 20, 0, 1), (55.0, -14, 3.0, ICED, 20, 1, 0), (46.6, -17, 3.2, PALE, 20, -1, 0),
                                    (51.5, -19, 2.6, CYAN, 20, 0, -1), (54, -11.6, 2.2, PALE, 25, 0.5, 0.8)):
        crystal(p, x, 0.3, z, 0.55, h, c, rot=lean(a, ux, uz), tip=0.35)
    for (x, z, r) in ((46, -11, 1.1), (56, -17, 1.0), (45.8, -18.5, 0.9)):
        dk.ball(p, (x, 0.5, z), r, STONE, scale=(1.2, 0.8, 1), subdiv=1, jitter=0.06)


# ---- 12. Sculptures --------------------------------------------------------------------------------------------------------
def pedestal(p, x, z, s=5):
    B(p, x, 1.0, z, s, 2.0, s, STONE, jit=0.05)
    B(p, x, 2.2, z, s + 0.6, 0.4, s + 0.6, PALE, jit=0.03)
    mound(p, x + s * 0.5, 0, z + s * 0.45, 1.3, 0.8, 1.2, SNOW, segs=8, rings=2)


def build_Sculptures(p):
    # 1. tiny Shiba, sitting, facing +z
    x, z = -66, -46
    pedestal(p, x, z)
    dk.ball(p, (x, 3.9, z - 0.4), 1.5, ICE, scale=(1, 0.95, 1.05), subdiv=1, jitter=0.04)
    B(p, x, 5.0, z + 0.3, 1.8, 2.6, 1.4, ICE, rot=(-8, 0, 0), jit=0.04)
    B(p, x, 4.3, z + 1.0, 1.1, 2.0, 0.5, PALE, rot=(-8, 0, 0), jit=0.03)
    for dx in (-0.55, 0.55):
        B(p, x + dx, 3.2, z + 0.9, 0.55, 1.6, 0.6, ICE, jit=0.04)
    B(p, x, 6.7, z + 0.7, 2.2, 1.7, 1.8, ICE, jit=0.04)
    B(p, x, 6.3, z + 1.7, 1.0, 0.8, 0.8, PALE, jit=0.03)
    B(p, x, 6.5, z + 2.12, 0.4, 0.3, 0.2, DARK, jit=0.02)
    for dx in (-0.45, 0.45):
        B(p, x + dx, 6.95, z + 1.62, 0.22, 0.22, 0.2, DARK, jit=0.02)
    for dx in (-0.8, 0.8):
        prism_z(p, [(x + dx - 0.4, 7.4), (x + dx + 0.4, 7.4), (x + dx, 8.4)], z + 0.5, z + 0.9, ICE, 0.03)
    B(p, x + 1.5, 4.6, z - 1.2, 0.7, 2.4, 0.7, PALE, rot=(0, 0, -25), jit=0.03)
    dk.ball(p, (x + 2.15, 5.7, z - 1.2), 0.65, PALE, subdiv=1, jitter=0.03)
    # 2. swan
    x, z = -58, -48
    pedestal(p, x, z)
    dk.ball(p, (x, 4.0, z - 0.2), 1.5, PALE, scale=(1.0, 0.75, 1.55), subdiv=1, jitter=0.04)
    spike(p, x, 3.6, z - 2.3, 0.8, 2.6, PALE, rot=(-75, 0, 0), verts=4)
    for s in (-1, 1):
        B(p, x + s * 1.75, 5.1, z - 0.4, 0.5, 2.2, 2.6, ICE, rot=(0, 0, s * -28), jit=0.04)
        B(p, x + s * 2.35, 6.0, z - 0.7, 0.3, 1.4, 1.8, PALE, rot=(0, 0, s * -28), jit=0.04)
    bar(p, (x, 4.6, z + 0.9), (x, 6.6, z + 1.5), 0.75, PALE)
    bar(p, (x, 6.6, z + 1.5), (x, 8.6, z + 1.0), 0.7, PALE)
    bar(p, (x, 8.6, z + 1.0), (x, 9.7, z + 1.4), 0.7, PALE)
    B(p, x, 9.7, z + 1.8, 0.9, 0.7, 1.0, ICE, jit=0.03)
    B(p, x, 9.55, z + 2.55, 0.4, 0.3, 0.6, ORG, jit=0.02)
    # 3. snowflake on a post
    x, z = -50, -45
    pedestal(p, x, z)
    B(p, x, 3.4, z, 1.0, 2.4, 0.9, ICED, jit=0.03)
    cy = 6.6
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ux, uy = math.cos(a), math.sin(a)
        tip = (x + 3.5 * ux, cy + 3.5 * uy, z)
        bar(p, (x, cy, z), tip, 0.8, PALE)
        for f in (0.5, 0.78):
            bx_, by_ = x + 3.5 * f * ux, cy + 3.5 * f * uy
            for s in (-1, 1):
                b = a + s * math.radians(60)
                ln = 1.3 * (1.1 - f * 0.4)
                bar(p, (bx_, by_, z), (bx_ + ln * math.cos(b), by_ + ln * math.sin(b), z), 0.55, ICE)
    dk.cyl(p, (x, cy, z + 0.1), 0.95, 1.1, ICED, axis='z', verts=6, jitter=0.03)


# ---- shared helpers for parts 13-25 -----------------------------------------------------------------------------------------
def rotm(rot):
    rx, ry, rz = (math.radians(a) for a in rot)
    return Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')


def cr_center(p, c, size, rot, col, tip=0.3, sides=6, jit=0.06):
    """Crystal given like a blueprint block: centre, size (w, h, d) and Roblox rotation; the foot is derived from the centre."""
    w, h = max(size[0], size[2]), size[1]
    up = rotm(rot) @ Vector((0, 1, 0))
    foot = Vector(c) - up * (h / 2)
    return crystal(p, foot.x, foot.y, foot.z, w / 2, h, col, rot=rot, sides=sides, tip=tip, jit=jit)


def tri_slab(p, a, b, c, t, col, jit=0.03):
    """Thin triangular slab through three stage points (wing membranes, flags)."""
    a, b, c = Vector(a), Vector(b), Vector(c)
    n = (b - a).cross(c - a).normalized() * (t / 2)
    pts = [tuple(a + n), tuple(b + n), tuple(c + n), tuple(a - n), tuple(b - n), tuple(c - n)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def pyr(p, cx, y0, cz, half, h, col, jit=0.03):
    """Square pyramid (axis aligned base)."""
    pts = [(cx - half, y0, cz - half), (cx + half, y0, cz - half), (cx + half, y0, cz + half), (cx - half, y0, cz + half), (cx, y0 + h, cz)]
    faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


# ---- 13. Slide -------------------------------------------------------------------------------------------------------------
def build_Slide(p):
    TOP = 9.8                                              # platform underside
    for x in (85.5, 90.5):
        for z in (43.5, 48.5):
            B(p, x, TOP / 2, z, 1.2, TOP, 1.2, ICED, jit=0.05)
            B(p, x, 0.3, z, 1.8, 0.6, 1.8, STONE, jit=0.04)
    for (a, b) in (((90.9, 1.0, 43.5), (90.9, 8.0, 48.5)), ((90.9, 1.0, 48.5), (90.9, 8.0, 43.5)),
                   ((85.5, 1.0, 43.1), (90.5, 8.0, 43.1)), ((90.5, 1.0, 43.1), (85.5, 8.0, 43.1))):
        bar(p, a, b, 0.35, PALE)
    B(p, 88, TOP + 0.4, 46, 6.2, 0.8, 6.2, ICE, jit=0.04)               # platform
    B(p, 88, TOP + 0.85, 46, 6.2, 0.1, 6.2, SNOWS, jit=0.03)
    ytop = TOP + 0.8
    for (x, z) in ((85.1, 43.1), (90.9, 43.1), (85.1, 48.9), (90.9, 48.9)):   # corner posts and rails
        B(p, x, ytop + 0.6, z, 0.5, 1.2, 0.5, PALE, jit=0.03)
    B(p, 88, ytop + 1.0, 43.1, 5.8, 0.35, 0.3, PALE, jit=0.03)
    B(p, 90.9, ytop + 1.0, 46, 0.3, 0.35, 5.8, PALE, jit=0.03)
    B(p, 85.1, ytop + 1.0, 43.9, 0.3, 0.35, 1.6, PALE, jit=0.03)
    B(p, 85.1, ytop + 1.0, 48.1, 0.3, 0.35, 1.6, PALE, jit=0.03)
    B(p, 86.2, ytop + 1.0, 48.9, 2.0, 0.35, 0.3, PALE, jit=0.03)
    B(p, 89.8, ytop + 1.0, 48.9, 2.0, 0.35, 0.3, PALE, jit=0.03)
    B(p, 88, ytop + 1.1, 43.1, 0.15, 2.2, 0.15, WOOD, jit=0.02)    # flag
    tri_slab(p, (88.1, ytop + 2.2, 43.1), (88.1, ytop + 1.2, 43.1), (89.8, ytop + 1.7, 43.1), 0.08, RED)
    # stairs up the front with alternating stripes
    for i in range(10):
        zf = 57.5 - i * 0.85
        h = 1.0 * (i + 1)
        B(p, 88, h / 2, (zf + 49.0) / 2, 4.2, h, zf - 49.0, PALE if i % 2 else ICE, jit=0.03)
    for s in (-1, 1):
        x = 88 + s * 2.3
        bar(p, (x, 1.4, 57.4), (x, TOP + 1.3, 49.4), 0.35, GOLD)
        B(p, x, 0.8, 57.3, 0.4, 1.6, 0.4, PALE, jit=0.03)
    # the long slide: floor, side walls, cyan centre stripe, run-out and snow bank
    diag(p, 73.4, 0.9, 46, 85.2, TOP + 0.9, 0.6, 3.8, PALE)
    diag(p, 73.4, 1.35, 46, 85.2, TOP + 1.35, 0.3, 1.0, CYAN, jit=0.02)
    for z in (44.0, 48.0):
        diag(p, 73.6, 1.5, z, 85.2, TOP + 1.5, 0.9, 0.45, ICE)
    B(p, 72.4, 0.3, 46, 3.2, 0.5, 3.8, PALE, jit=0.03)
    for z in (44.0, 48.0):
        B(p, 72.4, 0.8, z, 3.2, 0.7, 0.45, ICE, jit=0.03)
    mound(p, 72, 0, 46, 2.5, 2.0, 2.5, SNOW, SNOWS, segs=8, rings=2)
    # ice cladding between the legs so the tower reads as a solid ice tower, gold trim and crystal finials
    B(p, 88, 5.0, 43.15, 4.4, 9.4, 0.35, ICE, jit=0.04)
    B(p, 90.95, 5.0, 46, 0.35, 9.4, 4.4, ICE, jit=0.04)
    B(p, 88, TOP - 0.2, 43.0, 5.2, 0.5, 0.2, GOLD, jit=0.02)
    B(p, 91.0, TOP - 0.2, 46, 0.2, 0.5, 5.2, GOLD, jit=0.02)
    for (x, z) in ((85.1, 43.1), (90.9, 43.1), (85.1, 48.9), (90.9, 48.9)):
        crystal(p, x, ytop + 1.2, z, 0.3, 0.8, CYAN, tip=0.5, sides=4)
    for (x, z) in ((84.0, 58.6), (92.0 - 0.7, 58.8)):
        dk.ball(p, (x, 0.55, z), 0.55, SNOW, subdiv=0, jitter=0.03)
    crystal(p, 90.5, 0.6, 51.5, 0.5, 2.0, CYAN, tip=0.4)
    crystal(p, 85.4, 0.6, 52.0, 0.4, 1.6, ICE, rot=lean(10, -1, 0), tip=0.4)


# ---- 14. Penguins ----------------------------------------------------------------------------------------------------------
def penguin(p, x, y0, z, sc, yaw):
    a = math.radians(yaw)

    def P(lx, ly, lz):
        return (x + lx * math.cos(a) + lz * math.sin(a), y0 + ly, z - lx * math.sin(a) + lz * math.cos(a))
    r = (0, yaw, 0)
    dk.ball(p, P(0, 1.45 * sc, 0), 1.0 * sc, BLACK, scale=(0.95, 1.55, 0.9), subdiv=1, rot=r, jitter=0.03)
    dk.ball(p, P(0, 1.3 * sc, 0.45 * sc), 0.8 * sc, SNOW, scale=(0.75, 1.5, 0.5), subdiv=0, rot=r, jitter=0.02)
    dk.ball(p, P(0, 3.0 * sc, 0.05 * sc), 0.66 * sc, BLACK, subdiv=0, rot=r, jitter=0.03)
    for s in (-1, 1):
        B(p, *P(s * 0.28 * sc, 3.15 * sc, 0.5 * sc), 0.2 * sc, 0.2 * sc, 0.12 * sc, SNOW, rot=r, jit=0.01)
        B(p, *P(s * 0.45 * sc, 0.1 * sc, 0.55 * sc), 0.6 * sc, 0.2 * sc, 1.0 * sc, ORG, rot=r, jit=0.02)
        B(p, *P(s * 1.05 * sc, 1.7 * sc, 0), 0.2 * sc, 1.5 * sc, 0.8 * sc, BLACK, rot=(0, yaw, s * 14), jit=0.02)
    dk.cyl(p, P(0, 2.95 * sc, 0.8 * sc), 0.2 * sc, 0.55 * sc, ORG, axis='z', verts=4, top_radius=0.03 * sc, rot=r, jitter=0.02)


def build_Penguins(p):
    hexa(p, [(-21.4, 0, -2.0), (-10.6, 0, -2.0), (-10.6, 0, 6.0), (-21.4, 0, 6.0),
             (-22.0, 2.4, -2.5), (-10.0, 2.4, -2.5), (-10.0, 2.4, 6.5), (-22.0, 2.4, 6.5)], ICE, 0.05)
    B(p, -18, 3.6, 1, 6, 2.4, 5, PALE, jit=0.05)
    hexa(p, [(-21, 4.8, -1.5), (-15, 4.8, -1.5), (-15, 4.8, 3.5), (-21, 4.8, 3.5),
             (-20.4, 5.0, -1.0), (-15.6, 5.0, -1.0), (-15.6, 5.0, 3.0), (-20.4, 5.0, 3.0)], SNOW, 0.03)
    B(p, -12.5, 2.9, -1, 2.4, 1.0, 1.4, ICED, jit=0.04)                    # little ramp block
    for (x, z, h, c, a, ux, uz) in ((-20.5, -1.0, 5.5, ICED, 12, -1, 0), (-18.0, -2.0, 3.8, PALE, 10, 0, -1), (-11.2, -1.8, 4.6, ICE, 12, 1, 0)):
        crystal(p, x, 2.0, z, 0.9, h, c, rot=lean(a, ux, uz), tip=0.3)
    B(p, -16, 2.43, 5.6, 3.4, 0.06, 1.8, DEEP, jit=0.02)                    # dark fishing hole
    for (x, z, a) in ((-15.0, 4.4, 20), (-13.4, 4.6, -30)):                  # fish on the ice
        B(p, x, 2.55, z, 1.2, 0.18, 0.5, TEAL, rot=(0, a, 0), jit=0.02)
    penguin(p, -12, 2.4, 4, 0.95, 20)
    penguin(p, -14.5, 2.4, 5.5, 0.9, -15)
    penguin(p, -10.5, 2.4, 1, 0.95, 50)
    penguin(p, -18, 4.9, 1, 0.9, 5)
    penguin(p, -20, 2.4, 4, 0.9, -25)
    for (x, z) in ((-21, 6), (-10.8, 6.2)):
        mound(p, x, 2.2, z, 1.0, 0.5, 0.9, SNOW, segs=6, rings=2)


# ---- 15. FishHut -----------------------------------------------------------------------------------------------------------
def build_FishHut(p):
    B(p, 74, 3.2, 14, 7, 6.4, 6, DEEP, jit=0.04)
    for i in range(5):                                                     # plank seams on the front wall
        B(p, 71.6 + i * 1.2, 3.2, 17.05, 0.1, 6.2, 0.1, ICED, jit=0.02)
    dk.prism(p, (74, 6.2, 14), 8.6, 7.2, 1.2, SNOW, ridge='x', jitter=0.03)
    B(p, 74, 6.35, 14, 8.6, 0.3, 7.2, WOODD, jit=0.03)
    B(p, 72.6, 2.0, 17.1, 1.8, 3.6, 0.3, WOODD, jit=0.03)                   # door
    B(p, 72.6, 2.0, 17.25, 1.3, 3.2, 0.15, WOOD, jit=0.02)
    B(p, 73.2, 2.0, 17.35, 0.2, 0.2, 0.1, GOLD, jit=0.02)
    B(p, 76, 3.9, 17.1, 2.0, 1.8, 0.3, WOODD, jit=0.03)                     # window
    B(p, 76, 3.9, 17.25, 1.5, 1.3, 0.15, CYAN, jit=0.02)
    B(p, 74, 5.6, 17.15, 2.4, 0.9, 0.2, RED, jit=0.02)                      # fish sign
    prism_z(p, [(75.2, 5.15), (75.2, 6.05), (76.0, 5.6)], 17.0, 17.3, RED, 0.02)
    B(p, 76.3, 6.9, 12.2, 0.9, 1.6, 0.9, STONE, jit=0.04)                    # chimney
    dk.ball(p, (76.3, 7.0, 12.2), 0.4, SNOWS, subdiv=0, jitter=0.03)
    B(p, 74, 0.42, 19.5, 4, 0.14, 4, PALE, jit=0.02)                         # hole in the ice
    B(p, 74, 0.5, 19.5, 2.8, 0.1, 2.8, DARK, jit=0.01)
    B(p, 74, 0.55, 19.5, 1.2, 0.05, 1.2, DEEP, jit=0.01)
    bar(p, (72.4, 0.3, 18.0), (73.9, 5.6, 20.3), 0.25, WOODD)                # rod and line
    bar(p, (73.9, 5.6, 20.3), (74.0, 0.6, 19.6), 0.06, SNOW)
    B(p, 78.6, 1.0, 17.5, 2, 2, 2, WOOD, jit=0.04)                            # crate
    B(p, 78.6, 1.0, 18.52, 2.0, 0.25, 0.05, WOODD, jit=0.02)
    B(p, 78.6, 2.05, 17.5, 2.2, 0.15, 2.2, WOODL, jit=0.03)
    vcyl(p, 70.2, 0.0, 1.8, 17.8, 0.8, RED, verts=8, top_r=0.9, jit=0.03)    # bucket with fish
    vcyl(p, 70.2, 1.8, 1.9, 17.8, 0.95, STEEL, verts=8, jit=0.02)
    for dx in (-0.3, 0.3):
        B(p, 70.2 + dx, 2.2, 17.8, 0.35, 0.9, 0.18, ORG if dx < 0 else TEAL, rot=(0, 0, dx * 40), jit=0.02)
    mound(p, 77.2, 0, 11, 1.8, 2.8, 1.3, SNOW, SNOWS, segs=8, rings=2)


# ---- 16. Cannon ------------------------------------------------------------------------------------------------------------
def build_Cannon(p):
    B(p, 40, 0.6, 58, 6, 1.2, 5, DARK, jit=0.04)
    for z in (56.0, 60.0):                                                  # wheels
        dk.cyl(p, (38.2, 0.95, z), 0.95, 0.5, BLACK, axis='z', verts=8, jitter=0.02)
        dk.cyl(p, (38.2, 0.95, z + (0.3 if z > 58 else -0.3)), 0.35, 0.2, STEEL, axis='z', verts=6, jitter=0.02)
    vcyl(p, 40, 1.2, 3.0, 58, 2.0, RED, verts=10, jit=0.03)                 # housing: red lower drum, steel top
    vcyl(p, 40, 3.0, 4.8, 58, 2.0, STEEL, verts=10, jit=0.03)
    vcyl(p, 40, 2.4, 2.8, 58, 2.15, DARK, verts=10, jit=0.02)
    B(p, 38.6, 2.8, 58, 0.5, 3.4, 3.4, DARK, jit=0.03)
    dk.cyl(p, (40, 5.6, 58), 1.0, 1.7, ICE, axis='y', verts=10, top_radius=2.0, jitter=0.03)     # snow hopper
    mound(p, 40, 6.4, 58, 1.8, 0.8, 1.8, SNOW, segs=8, rings=2)
    dk.cyl(p, (43.7, 3.9, 58), 1.15, 4.6, STEEL, axis='x', verts=8, rot=(0, 0, 12), jitter=0.03)  # barrel
    dk.cyl(p, (46.4, 4.5, 58), 1.1, 1.2, DARK, axis='x', verts=8, top_radius=1.7, rot=(0, 0, 12), jitter=0.03)
    for dz in (-1.25, 1.25):
        bar(p, (41.5, 1.2, 58 + dz * 1.6), (43.8, 3.0, 58 + dz * 0.8), 0.4, DARK)
    B(p, 40, 3.2, 60.1, 1.2, 1.2, 0.25, PALE, jit=0.02)                       # pressure gauge
    B(p, 40.15, 3.25, 60.25, 0.14, 0.55, 0.1, RED, rot=(0, 0, 30), jit=0.01)
    B(p, 41.3, 1.8, 60.05, 0.4, 0.4, 0.3, GOLD, jit=0.02)
    B(p, 38.7, 5.3, 56.6, 0.3, 0.3, 0.3, CYAN, jit=0.02)
    # fluffy cloud: many overlapping puffs growing away from the nozzle, with a few flakes
    for k, (x, y, z, r) in enumerate(((48.2, 5.0, 58, 1.2), (49.4, 5.9, 58.7, 1.3), (49.8, 5.3, 57.2, 1.4), (51.2, 6.3, 57.8, 1.8),
                                     (51.8, 5.2, 59.2, 1.5), (53.0, 7.0, 58.6, 1.9), (53.6, 6.0, 56.9, 1.7), (54.6, 7.4, 58.0, 1.5),
                                     (52.4, 8.0, 57.6, 1.0), (55.0, 5.6, 59.3, 1.1))):
        dk.ball(p, (x, y, z), r, SNOW if k % 3 else PALE, subdiv=1, jitter=0.03)
    for (x, y, z) in ((46.5, 6.4, 59.5), (47.2, 7.2, 57.0), (50.5, 8.4, 59.2), (55.4, 3.6, 57.6), (49.0, 2.8, 60.2), (52.2, 3.0, 60.0)):
        B(p, x, y, z, 0.35, 0.35, 0.35, SNOW, rot=(30, 20, 40), jit=0.02)
    for (x, z, rx, rz) in ((49, 58.2, 2.6, 1.8), (52.2, 59.4, 2.2, 1.6), (47.0, 59.8, 1.4, 1.1)):
        mound(p, x, 0, z, rx, 0.9, rz, SNOW, SNOWS, segs=8, rings=2)
    for (x, z) in ((44, 60.4), (46.5, 56)):
        dk.ball(p, (x, 0.3, z), 0.45, SNOW, subdiv=0, jitter=0.03)


# ---- 17. Crystals ----------------------------------------------------------------------------------------------------------
def build_Crystals(p):
    mound(p, -56, 0, 22, 6, 2.4, 5.5, STONE, STONEL, segs=12, rings=3)
    for (cx, cy, cz, w, h, rot, col, tip) in ((-56, 7, 22, 3.6, 14, (0, 0, 6), CYAN, 0.25), (-51, 4.5, 22, 2.6, 9, (0, 0, -20), ICE, 0.3),
                                              (-53.5, 3.5, 26.3, 2.6, 7, (17.3, 0, -10), PURPLE, 0.3), (-58.5, 4, 26.3, 2.6, 8, (17.3, 0, 10), ICE, 0.3),
                                              (-61, 3, 22, 2.6, 6, (0, 0, 20), GREEN, 0.3), (-58.5, 4.5, 17.7, 2.6, 9, (-17.3, 0, 10), ICE, 0.3),
                                              (-53.5, 3.5, 17.7, 2.6, 7, (-17.3, 0, -10), PURPLE, 0.3)):
        cr_center(p, (cx, cy, cz), (w, h, w), rot, col, tip=tip)
    for (x, z, h, c, a, ux, uz) in ((-56, 27.0, 3.0, PALE, 30, 0, 1), (-49.8, 24.6, 2.6, CYAN, 30, 1, 0.3), (-62.0, 25.5, 2.6, ICE, 30, -1, 0.5),
                                    (-50.5, 18.6, 2.8, GREEN, 30, 1, -0.5), (-62, 19, 2.6, PALE, 30, -1, -0.5), (-56.5, 16.7, 2.4, ICED, 30, 0, -1)):
        crystal(p, x, 0.8, z, 0.6, h, c, rot=lean(a, ux, uz), tip=0.35)
    for (x, z, r) in ((-62, 17, 1.0), (-50, 27, 0.9), (-61, 27.4, 0.8)):
        dk.ball(p, (x, 0.5, z), r, STONE, scale=(1.2, 0.8, 1), subdiv=1, jitter=0.06)


# ---- 19. HotSpring ---------------------------------------------------------------------------------------------------------
def build_HotSpring(p):
    vcyl(p, -80, 0, 1.4, 4, 6.0, STONE, verts=16, jit=0.05)
    vcyl(p, -80, 1.4, 1.6, 4, 5.0, TEAL, verts=16, jit=0.03)
    vcyl(p, -80, 1.6, 1.64, 4, 3.2, CYAN, verts=12, jit=0.02)
    for k in range(10):                                                      # rim rocks
        a = k * 2 * math.pi / 10 + 0.3
        r = 5.6 + (0.4 if k % 2 else 0)
        dk.ball(p, (-80 + r * math.cos(a), 1.2, 4 + r * math.sin(a)), 1.2 if k % 3 == 0 else 0.95, STONE if k % 2 else STONEL,
                scale=(1.2, 0.9, 1.1), subdiv=1 if k % 3 == 0 else 0, jitter=0.06)
    for (x, z) in ((-82.0, 7.8), (-76.4, 7.4)):                               # snow caps on rocks
        dk.ball(p, (x, 2.0, z), 0.9, SNOW, scale=(1.3, 0.55, 1.1), subdiv=0, jitter=0.03)
    # steam: two curling plumes of ever-smaller puffs, drifting up and sideways
    for plume in (((-82.0, 2.4, 3.0, 1.5), (-82.6, 3.7, 3.3, 1.3), (-83.4, 5.0, 3.0, 1.1), (-83.0, 6.2, 2.6, 0.9), (-82.2, 7.0, 2.6, 0.6)),
                  ((-77.6, 2.4, 5.0, 1.4), (-77.0, 3.7, 4.6, 1.3), (-77.6, 5.0, 4.4, 1.1), (-78.4, 6.1, 4.8, 0.8))):
        for k, (x, y, z, r) in enumerate(plume):
            dk.ball(p, (x, y, z), r, SNOW if k % 2 == 0 else PALE, scale=(1.0, 0.8, 1.0), subdiv=1 if r > 1.0 else 0, jitter=0.03)
    B(p, -72.5, 1.75, 10.4, 4, 0.5, 1.6, WOODL, jit=0.04)                    # bench
    for dx in (-1.6, 1.6):
        B(p, -72.5 + dx, 0.75, 10.4, 0.5, 1.5, 1.4, WOODD, jit=0.03)
    B(p, -72.5, 2.9, 11.0, 4, 0.4, 0.3, WOODL, jit=0.03)
    for dx in (-1.6, 1.6):
        B(p, -72.5 + dx, 2.4, 11.0, 0.4, 1.2, 0.3, WOODD, jit=0.03)
    for x in (-86.8, -84.0):                                                 # towel rack
        B(p, x, 2.6, 11, 0.4, 5.2, 0.4, WOODD, jit=0.03)
    B(p, -85.4, 4.9, 11, 3.2, 0.35, 0.4, WOOD, jit=0.03)
    B(p, -86.1, 3.7, 11.3, 0.9, 2.4, 0.12, RED, jit=0.02)
    B(p, -84.7, 3.7, 11.3, 0.9, 2.4, 0.12, PALE, jit=0.02)
    for (x, z) in ((-86.0, 7.0), (-75.0, 0.2)):
        dk.ball(p, (x, 0.25, z), 0.6, SNOW, scale=(2.5, 0.6, 1.6), subdiv=1, jitter=0.03)


# ---- 21. Observatory -------------------------------------------------------------------------------------------------------
def build_Observatory(p):
    cx, cz = -82, -42
    B(p, cx, 0.5, cz, 14, 1, 14, STONE, jit=0.05)
    vcyl(p, cx, 1.0, 9.5, cz, 5.5, PALE, verts=12, jit=0.04)
    for y in (3.2, 6.2):
        vcyl(p, cx, y, y + 0.5, cz, 5.75, STONEL, verts=12, jit=0.03)
    vcyl(p, cx, 8.9, 9.7, cz, 5.9, GOLD, verts=12, jit=0.02)
    mound(p, cx, 9.7, cz, 6.0, 5.3, 6.0, DEEP, ICED, segs=12, rings=3)
    for a in (20, 140, 200, 260, 320):                                         # tower slit windows
        ar = math.radians(a)
        B(p, cx + 5.55 * math.cos(ar), 6.0, cz + 5.55 * math.sin(ar), 0.5, 2.2, 0.5, CYAN, rot=(0, -a, 0), jit=0.02)
    B(p, cx, 3.0, -36.4, 2.6, 4.4, 0.4, DARK, jit=0.02)                         # door
    prism_z(p, [(cx - 1.3, 5.2), (cx + 1.3, 5.2), (cx, 6.6)], -36.6, -36.2, DARK, 0.02)
    B(p, cx, 1.0, -34.5, 4, 2, 4, SNOW, jit=0.03)
    B(p, cx, 2.05, -34.5, 4.2, 0.2, 4.2, SNOWS, jit=0.03)
    B(p, cx, 12.0, -38.0, 3.0, 5.0, 1.4, DARK, jit=0.02)                         # dome slit (open hatch)
    B(p, cx, 14.7, -38.2, 3.6, 0.4, 1.8, STONEL, jit=0.02)
    bar(p, (cx, 11.0, -40.0), (cx, 12.9, -36.7), 2.3, STEEL)                    # long brass telescope aimed at the sky
    bar(p, (cx, 12.7, -37.1), (cx, 14.4, -34.0), 1.6, GOLD)
    bar(p, (cx, 14.2, -34.4), (cx, 14.75, -33.5), 2.0, CYAN)
    for t in (0.5, 0.8):
        B(p, cx, 12.7 + 1.7 * (t - 0.0) * 0.8, -37.1 + 3.1 * t, 2.1, 0.35, 2.1, GOLD, rot=(-30, 0, 0), jit=0.02)
    B(p, cx, 8.6, -37.6, 0.4, 1.8, 0.4, STONEL, jit=0.02)
    dk.ball(p, (-88, 1.5, -36), 1.0, SNOW, scale=(3, 1.5, 3), subdiv=1, jitter=0.03)
    crystal(p, cx, 14.4, cz, 0.5, 0.6, CYAN, tip=0.5)


# ---- 22. Throne ------------------------------------------------------------------------------------------------------------
def build_Throne(p):
    B(p, 18, 0.8, -58, 12, 1.6, 10, PALE, jit=0.03)
    B(p, 18, 0.4, -52.2, 9, 0.8, 1.8, PALE, jit=0.03)
    B(p, 18, 1.65, -53.1, 12, 0.1, 0.3, GOLD, jit=0.02)
    B(p, 18, 0.85, -52.2, 3, 0.07, 1.8, RED, jit=0.02)
    B(p, 18, 1.65, -55.4, 3, 0.07, 4.6, RED, jit=0.02)
    B(p, 18, 3.0, -59, 3.4, 2.8, 3.4, ICE, jit=0.04)
    B(p, 18, 4.6, -58.8, 3.0, 0.5, 3.0, RED, jit=0.02)
    B(p, 18, 4.35, -57.2, 3.4, 0.2, 0.2, GOLD, jit=0.02)
    for x in (15.6, 20.4):
        B(p, x, 3.8, -59, 1.0, 1.6, 3.6, ICED, jit=0.04)
        dk.ball(p, (x, 4.8, -57.5), 0.5, GOLD, subdiv=0, jitter=0.02)
    B(p, 18, 8, -60.8, 4, 10, 1.2, ICE, jit=0.04)
    B(p, 18, 13.1, -60.8, 4.4, 0.35, 1.5, GOLD, jit=0.02)
    B(p, 18, 5.0, -60.1, 2.6, 0.2, 0.3, GOLD, jit=0.02)
    for (x, y, h, a, ux) in ((16.2, 11.9, 5.0, 8, -1), (18, 12.1, 6.6, 0, 0), (19.8, 11.9, 5.0, 8, 1)):
        cr_center(p, (x, y + h / 2, -60.8), (1.1, h, 1.1), lean(a, ux, 0), CYAN, tip=0.35, sides=4)
    for (x, ux) in ((15.5, -1), (20.5, 1)):
        crystal(p, x, 10.3, -60.8, 0.5, 3.0, ICED, rot=lean(18, ux, 0), tip=0.4, sides=4)
    for x in (12.8, 23.2):                                                      # crystal pillars
        B(p, x, 0.5, -55, 2.2, 1.0, 2.2, PALE, jit=0.03)
        B(p, x, 5, -55, 1.4, 10, 1.4, ICED, jit=0.04)
        B(p, x, 3.0, -55, 1.9, 0.35, 1.9, GOLD, jit=0.02)
        B(p, x, 8.4, -55, 1.9, 0.35, 1.9, GOLD, jit=0.02)
        crystal(p, x, 10, -55, 0.95, 3.2, CYAN, tip=0.4)
    for (x, z) in ((12.9, -61.8), (23.0, -62), (22.8, -52.4)):
        crystal(p, x, 1.4, z, 0.5, 2.2, ICE, rot=lean(15, 0, 1), tip=0.4)


# ---- 23. Obelisk -----------------------------------------------------------------------------------------------------------
def build_Obelisk(p):
    cx, cz = -38, -57
    B(p, cx, 0.8, cz, 10, 1.6, 10, STONE, jit=0.05)
    B(p, cx, 2.2, cz, 7, 1.2, 7, PALE, jit=0.03)
    hexa(p, [(cx - 2, 2.8, cz - 2), (cx + 2, 2.8, cz - 2), (cx + 2, 2.8, cz + 2), (cx - 2, 2.8, cz + 2),
             (cx - 1.2, 24, cz - 1.2), (cx + 1.2, 24, cz - 1.2), (cx + 1.2, 24, cz + 1.2), (cx - 1.2, 24, cz + 1.2)], PURPLE, 0.05)
    pyr(p, cx, 24, cz, 1.25, 4.0, CYAN)
    B(p, cx, 24.0, cz, 3.0, 0.5, 3.0, GOLD, jit=0.02)
    B(p, cx, 3.4, cz, 4.7, 0.6, 4.7, GOLD, jit=0.02)
    for y in (6.5, 10.5, 14.5, 18.5):                                           # rune marks on the front face
        half = 2 - 0.8 * (y - 2.8) / 21.2
        B(p, cx, y, cz + half + 0.12, 0.45, 2.2, 0.3, GOLD, jit=0.02)
        B(p, cx, y + 0.3, cz + half + 0.12, 1.4, 0.4, 0.3, GOLD, jit=0.02)
        B(p, cx, y - 0.7, cz + half + 0.12, 0.9, 0.35, 0.3, CYAN, jit=0.02)
    torus(p, (cx, 10, cz), 5.4, 0.35, GREEN, segs=20, sides=4)
    torus(p, (cx, 17, cz), 4.4, 0.3, CYAN, segs=20, sides=4)
    for (R, y, a, c) in ((5.4, 10, 20, PURPLE), (5.4, 10, 200, PURPLE), (4.4, 17, 110, GREEN), (4.4, 17, 290, GREEN)):
        ar = math.radians(a)
        crystal(p, cx + R * math.cos(ar), y + 0.2, cz + R * math.sin(ar), 0.45, 1.6, c, tip=0.4, sides=4)
    for x in (cx - 4.2, cx + 4.2):
        crystal(p, x, 1.6, cz, 1.1, 7.5, GREEN, rot=lean(6, -1 if x < cx else 1, 0), tip=0.3)
    for (x, z) in ((cx - 3.6, cz + 3.8), (cx + 3.6, cz + 3.8), (cx - 3.6, cz - 3.8), (cx + 3.6, cz - 3.8)):
        crystal(p, x, 1.6, z, 0.6, 3.0, ICE, rot=lean(12, x - cx, z - cz), tip=0.4, sides=5)


# ---- 25. Crown -------------------------------------------------------------------------------------------------------------
def build_Crown(p):
    cx, cz = 12, 50
    B(p, cx, 0.5, cz, 12, 1.0, 12, STONE, jit=0.05)
    B(p, cx, 1.5, cz, 10.4, 1.0, 10.4, STONEL, jit=0.04)
    vcyl(p, cx, 2.0, 2.6, cz, 4.95, GOLD, verts=16, jit=0.02)
    vcyl(p, cx, 2.6, 5.9, cz, 4.7, ICE, verts=16, jit=0.04)
    vcyl(p, cx, 5.9, 6.9, cz, 4.95, GOLD, verts=16, jit=0.02)
    for k in range(8):                                                                         # gems around the band
        a = k * math.pi / 4 + math.pi / 8
        c = (RED, CYAN, GREEN, PURPLE)[k % 4]
        B(p, cx + 4.75 * math.cos(a), 4.2, cz + 4.75 * math.sin(a), 1.0, 1.4, 1.0, c, rot=(0, -math.degrees(a), 0), jit=0.02)
    dk.ball(p, (cx, 4.3, cz + 4.9), 1.5, RED, scale=(1.0, 1.1, 0.6), subdiv=0, jitter=0.02)      # the huge red jewel
    for k in range(8):                                                                         # points
        a = k * math.pi / 4
        ux, uz = math.cos(a), math.sin(a)
        tall = (k % 2 == 0)
        h, r = (6.2, 0.95) if tall else (4.2, 0.75)
        fx, fz = cx + ux * 4.1, cz + uz * 4.1
        crystal(p, fx, 6.9, fz, r, h, ICE if tall else PALE, rot=lean(12, ux, uz), tip=0.35, sides=5)
        tp = rotm(lean(12, ux, uz)) @ Vector((0, h, 0))
        dk.ball(p, (fx + tp.x, 6.9 + tp.y + 0.1, fz + tp.z), 0.5 if tall else 0.4, GOLD, subdiv=0, jitter=0.02)
    crystal(p, cx, 6.9, cz, 1.3, 8.2, CYAN, tip=0.3, sides=6)
    dk.ball(p, (cx, 15.1, cz), 1.0, RED, subdiv=1, jitter=0.02)
    vcyl(p, cx, 6.9, 7.3, cz, 1.9, GOLD, verts=8, jit=0.02)


# ---- 18. SnowFort ----------------------------------------------------------------------------------------------------------
def build_SnowFort(p):
    B(p, 50, 2.2, -0.5, 14, 4.4, 2.4, SNOW, jit=0.03)
    B(p, 43.5, 2.2, 4, 2.4, 4.4, 11, SNOW, jit=0.03)
    B(p, 56.5, 2.2, 4, 2.4, 4.4, 11, SNOW, jit=0.03)
    for y in (1.1, 2.2, 3.3):                                               # ice-block courses: alternating blue-white bands
        for (cx, cz, sx, sz) in ((50, 0.78, 14, 0.14), (42.25, 4, 0.14, 11), (57.75, 4, 0.14, 11)):
            B(p, cx, y, cz, sx, 0.5, sz, ICE if int(y) % 2 else PALE, jit=0.03)
    for x in (45.5, 50, 54.5):                                               # merlons
        B(p, x, 5.1, -0.5, 2.2, 1.4, 2.4, SNOW, jit=0.03)
        B(p, x, 4.5, 0.78, 2.2, 0.25, 0.14, ICE, jit=0.02)
    for z in (2.0, 6.0):
        for x in (43.5, 56.5):
            B(p, x, 5.1, z, 2.4, 1.4, 2.2, SNOW, jit=0.03)
    for x in (43.5, 56.5):
        B(p, x, 5.1, -0.5, 2.4, 1.4, 2.4, SNOW, jit=0.03)
    B(p, 50, 1.2, 9, 6, 2.4, 1.2, SNOW, jit=0.03)                            # low front wall
    B(p, 50, 2.55, 9, 6.4, 0.3, 1.5, ICE, jit=0.03)
    B(p, 50, 1.2, 9.65, 6, 0.5, 0.14, ICE, jit=0.02)
    B(p, 50, 0.08, 4.5, 9.6, 0.16, 9, SNOWS, jit=0.03)                        # trampled floor
    B(p, 50, 5.6, -0.5, 0.2, 1.0, 0.2, WOOD, jit=0.02)                        # pennant on the middle merlon
    tri_slab(p, (50.1, 5.8, -0.5), (50.1, 4.9, -0.5), (51.8, 5.35, -0.5), 0.06, RED)
    for (x, z) in ((46.5, 3), (53.4, 3)):                                     # blueprint snowball heaps
        for k, (dx, dz, dy) in enumerate(((0, 0, 0.7), (1.3, 0.2, 0.7), (0.65, 1.1, 0.7), (0.65, 0.5, 1.7))):
            dk.ball(p, (x - 0.65 + dx, dy, z - 0.5 + dz), 0.72, PALE if k % 2 else SNOW, subdiv=1, jitter=0.03)
    for k, (dx, dz, dy) in enumerate(((0, 0, 0.6), (1.0, 0, 0.6), (0.5, 0.9, 0.6), (0.5, 0.4, 1.4))):
        dk.ball(p, (49.5 + dx, dy, 2.0 + dz), 0.6, PALE if k % 2 == 0 else SNOW, subdiv=0, jitter=0.03)
    for (x, z) in ((47.5, 6.6), (52.4, 6.8), (48.8, 7.4)):
        dk.ball(p, (x, 0.45, z), 0.45, SNOW, subdiv=0, jitter=0.03)
    # a snowman head grinning over the front wall, with top hat and scarf
    dk.ball(p, (50, 3.5, 8.4), 1.05, SNOW, subdiv=1, jitter=0.03)
    for dx in (-0.35, 0.35):
        B(p, 50 + dx, 3.8, 9.35, 0.22, 0.22, 0.14, BLACK, jit=0.01)
    dk.cyl(p, (50, 3.45, 9.75), 0.17, 0.8, ORG, axis='z', verts=5, top_radius=0.02, jitter=0.02)
    for k in range(4):
        B(p, 49.5 + k * 0.33, 3.0, 9.4, 0.14, 0.14, 0.14, BLACK, jit=0.01)
    vcyl(p, 50, 4.35, 4.5, 8.4, 1.05, BLACK, verts=10, jit=0.02)
    vcyl(p, 50, 4.5, 5.4, 8.4, 0.62, BLACK, verts=10, jit=0.02)
    vcyl(p, 50, 4.55, 4.85, 8.4, 0.66, RED, verts=10, jit=0.02)
    B(p, 50, 2.45, 8.4, 2.4, 0.3, 2.4, RED, jit=0.02)
    for x in (45.5, 50, 54.5):
        B(p, x, 5.78, -0.5, 2.3, 0.08, 2.5, ICE, jit=0.02)
    B(p, 44.6, 2.0, 9.4, 0.2, 3.0, 0.2, WOOD, rot=(0, 0, 12), jit=0.02)       # shovel in front
    B(p, 44.9, 0.7, 9.4, 0.8, 0.9, 0.15, STEEL, rot=(0, 0, 12), jit=0.02)
    mound(p, 54.4, 0, 9.0, 2.0, 1.6, 1.2, SNOW, SNOWS, segs=8, rings=2)


# ---- 20. Glacier -----------------------------------------------------------------------------------------------------------
def build_Glacier(p):
    # main cliff: front (+z) leans back, with blue strata bands
    hexa(p, [(79, 0, -16), (91, 0, -16), (91, 0, 8), (79, 0, 8), (80.2, 10, -14.8), (90.2, 10, -14.8), (90.2, 10, 5.6), (80.2, 10, 5.6)], ICE, 0.06)
    for (y, f) in ((2.4, 0.96), (5.0, 0.9), (7.6, 0.85)):
        zf = 8 - (8 - 5.6) * y / 10 + 0.1
        B(p, 85, y, zf, 11.6 * f + 0.4, 0.5, 0.25, ICED, jit=0.04)
        B(p, 79.9 + (y / 10) * 0.2, y, -4, 0.25, 0.5, 23.0 * f, ICED, jit=0.04)
    hexa(p, [(82, 9.8, -15), (90, 9.8, -15), (90, 9.8, -1), (82, 9.8, -1), (83.4, 16, -13.4), (88.6, 16, -13.4), (88.6, 16, -2.6), (83.4, 16, -2.6)], ICED, 0.06)
    hexa(p, [(83.2, 15.6, -13.6), (88.8, 15.6, -13.6), (88.8, 15.6, -2.4), (83.2, 15.6, -2.4), (84.0, 16.6, -12.8), (88.0, 16.6, -12.8), (88.0, 16.6, -3.2), (84.0, 16.6, -3.2)], SNOW, 0.03)
    B(p, 85.2, 10.4, -1.0, 10.4, 0.8, 13.5, SNOW, jit=0.03)
    cr_center(p, (84, 15, -2), (4, 14, 4), (4, 0, -8), PALE, tip=0.3, sides=5)
    crystal(p, 88.5, 10.4, -11.5, 1.6, 8.5, ICE, rot=lean(8, 1, 0), tip=0.3, sides=5)
    crystal(p, 81.0, 10.4, -11, 1.3, 6.5, PALE, rot=lean(12, -1, 0), tip=0.3, sides=5)
    crystal(p, 81.4, 10.6, 3.0, 1.2, 5.2, ICED, rot=lean(15, -1, 0.5), tip=0.3, sides=5)
    crystal(p, 88.0, 10.6, 3.5, 0.9, 3.8, CYAN, rot=lean(15, 1, 0.5), tip=0.3, sides=5)
    crystal(p, 89.8, 7.4, 5.0, 0.8, 3.0, PALE, rot=lean(14, 1, 0), tip=0.3, sides=5)
    B(p, 89, 3.5, 5, 4, 7, 5, ICED, jit=0.05)
    B(p, 89, 7.15, 5, 4.4, 0.7, 5.4, SNOW, jit=0.03)
    # ice cave on the front face with an icicle fringe
    B(p, 84.6, 2.3, 6.9, 3.8, 4.6, 0.5, DARK, jit=0.02)
    prism_z(p, [(82.7, 4.6), (86.5, 4.6), (84.6, 6.6)], 6.65, 7.15, DARK, 0.02)
    B(p, 84.6, 0.3, 7.4, 4.6, 0.6, 1.6, PALE, jit=0.03)
    for x in (83.1, 84.0, 84.9, 85.8):
        icicle(p, x, 5.0 if x in (84.0, 84.9) else 4.5, 7.2, 0.28, 1.3, PALE, verts=4)
    for x in (82.2, 87.0):
        B(p, x, 2.3, 7.0, 0.5, 4.6, 0.6, PALE, jit=0.03)
    for (x, z, h, c, ux, uz) in ((80.6, -13.5, 4.5, ICE, -1, -0.3), (80.8, -9.0, 5.5, PALE, -1, 0), (81.0, -4.5, 4.0, CYAN, -1, 0.2),
                                 (80.6, 0.0, 5.0, ICE, -1, 0.3), (89.4, -13.5, 4.5, PALE, 1, -0.3), (89.6, -7.0, 3.6, ICE, 1, 0)):
        crystal(p, x, 10.5, z, 0.9, h, c, rot=lean(14, ux, uz), tip=0.3, sides=5)
    # frozen waterfall down the east face with a fringe of icicles and a pale pool
    B(p, 91.1, 5.6, -5.5, 0.3, 8.8, 3.2, PALE, jit=0.03)
    B(p, 91.25, 5.6, -5.5, 0.2, 8.8, 1.2, CYAN, jit=0.02)
    for z in (-6.8, -5.5, -4.2):
        icicle(p, 91.2, 2.0, z, 0.26, 1.2, PALE, verts=4)
    B(p, 92.0, 0.15, -5.5, 2.4, 0.3, 4.2, PALE, jit=0.03)
    # crevasses on the west face
    for (z, y, ln) in ((-12, 7, 6), (2.5, 6, 5), (-9, 3, 4), (-5, 8.4, 5)):
        B(p, 78.9, y, z, 0.15, 0.3, ln, DEEP, jit=0.02)
    mound(p, 80.6, 0, 6, 2.5, 4.0, 3.0, SNOW, SNOWS, segs=10, rings=3)


# ---- 24. Drake -------------------------------------------------------------------------------------------------------------
def build_Drake(p):
    B(p, -76, 1.2, 54, 18, 2.4, 10, ICED, jit=0.05)
    B(p, -76, 2.5, 54, 17, 0.2, 9, SNOW, jit=0.03)
    dk.ball(p, (-76, 4.9, 54), 1.0, ICE, scale=(4.7, 2.3, 2.2), subdiv=1, jitter=0.04)       # torso
    dk.ball(p, (-73.2, 5.5, 54), 1.0, ICE, scale=(2.4, 2.6, 2.1), subdiv=1, jitter=0.04)     # chest
    B(p, -74.4, 3.3, 54, 5.2, 0.5, 1.5, PALE, jit=0.03)                                        # belly plates
    for k in range(4):
        B(p, -75.8 + k * 1.3, 3.1, 54, 0.15, 0.7, 2.6, PALE, jit=0.02)
    bar(p, (-72.6, 6.4, 54), (-70.9, 8.4, 54), 2.4, ICE)                                       # neck, thinning toward the head
    bar(p, (-70.9, 8.4, 54), (-69.8, 10.0, 54), 1.9, ICE)
    for (x, y) in ((-72.2, 7.4), (-71.2, 8.7), (-70.3, 9.8)):
        spike(p, x - 0.4, y + 0.7, 54, 0.3, 0.9, PALE, verts=4, rot=(0, 0, 25), jit=0.03)
    # head: tapering skull, lower jaw, brow, horns, eyes, teeth
    hexa(p, [(-70.6, 9.8, 52.7), (-70.6, 9.8, 55.3), (-66.4, 10.3, 54.6), (-66.4, 10.3, 53.4),
             (-70.6, 11.7, 52.7), (-70.6, 11.7, 55.3), (-66.4, 11.1, 54.6), (-66.4, 11.1, 53.4)], ICE, 0.04)
    hexa(p, [(-70.0, 9.3, 53.0), (-70.0, 9.3, 55.0), (-66.8, 9.6, 54.4), (-66.8, 9.6, 53.6),
             (-70.0, 9.9, 53.0), (-70.0, 9.9, 55.0), (-66.8, 10.2, 54.4), (-66.8, 10.2, 53.6)], ICED, 0.04)
    for z in (52.6, 55.4):
        B(p, -69.2, 11.45, z, 1.9, 0.35, 0.5, ICED, jit=0.03)                                  # brow ridge
        B(p, -69.1, 11.0, z + (0.1 if z > 54 else -0.1), 0.8, 0.5, 0.2, CYAN, jit=0.01)        # eye
    for z in (53.7, 54.3):
        B(p, -66.3, 10.8, z, 0.2, 0.2, 0.2, DARK, jit=0.01)                                    # nostrils
    for x in (-67.2, -68.3):
        for z in (53.6, 54.4):
            spike(p, x, 10.2, z, 0.17, 0.6, SNOW, verts=3, rot=(180, 0, 0), jit=0.02)
    for z in (53.2, 54.8):
        spike(p, -70.3, 11.5, z, 0.45, 1.5, GOLD, verts=4, rot=(0, 0, 62), jit=0.03)
    for k in range(6):                                                                         # dorsal spikes (gold and ice)
        x = -79.5 + k * 1.6
        spike(p, x, 6.5 - abs(k - 2.5) * 0.25, 54, 0.4, 1.2, GOLD if k % 2 else CYAN, verts=4, jit=0.03)
    bar(p, (-79.5, 4.6, 54), (-83.4, 3.6, 54.2), 1.7, ICE)                                     # tail
    bar(p, (-83.4, 3.6, 54.2), (-85.6, 3.6, 55.6), 0.9, ICE)
    spike(p, -85.2, 3.5, 55.4, 0.5, 1.4, PALE, verts=4, rot=(0, 0, 80), jit=0.03)
    for z in (52, 56):                                                                         # legs with claws
        B(p, -73, 2.8, z, 1.8, 3.0, 1.8, ICED, jit=0.04)
        for dz in (-0.5, 0, 0.5):
            spike(p, -71.9, 1.45, z + dz, 0.2, 0.9, GOLD, verts=3, rot=(0, 0, -80), jit=0.02)
        dk.ball(p, (-79, 4.0, z), 1.0, ICE, scale=(1.9, 1.7, 1.2), subdiv=0, jitter=0.04)
        B(p, -78.4, 1.8, z, 1.4, 1.0, 1.5, ICED, jit=0.04)
        B(p, -77.4, 1.5, z, 1.2, 0.5, 1.5, PALE, jit=0.03)
    for s in (-1, 1):                                                                          # wings: bat-wing with scalloped edge
        A = (-77.5, 6.8, 54 + s * 2.0)
        Wr = (-78.8, 11.4, 54 + s * 3.4)
        T1 = (-73.6, 10.4, 54 + s * 6.6)
        T2 = (-79.6, 10.2, 54 + s * 6.6)
        T3 = (-84.4, 8.4, 54 + s * 5.8)
        Bk = (-82.4, 5.6, 54 + s * 2.2)

        def mid(a, b):
            return tuple((a[i] + b[i]) / 2 * 0.72 + Wr[i] * 0.28 for i in range(3))
        M12, M23, M3B = mid(T1, T2), mid(T2, T3), mid(T3, Bk)
        for tri in ((Wr, T1, M12), (Wr, M12, T2), (Wr, T2, M23), (Wr, M23, T3), (Wr, T3, M3B), (Wr, M3B, Bk), (Wr, Bk, A), (Wr, A, T1)):
            tri_slab(p, *tri, 0.2, PALE, jit=0.04)
        for (a, b, t) in ((A, Wr, 0.8), (Wr, T1, 0.5), (Wr, T2, 0.5), (Wr, T3, 0.5)):
            bar(p, a, b, t, ICED)
    crystal(p, -84.5, 2.4, 50, 0.7, 2.6, ICE, rot=lean(12, -1, 0), tip=0.4)
    crystal(p, -68.5, 2.4, 49.8, 0.6, 2.2, PALE, rot=lean(12, 1, 0), tip=0.4)
    crystal(p, -84.0, 2.4, 58.5, 0.6, 2.2, PALE, rot=lean(12, -1, 0), tip=0.4)


PART_IDS = ["Ground", "Palace", "Halo", "Gate", "Igloo", "Rink", "Snowmen", "Sled", "Fountain", "Cabin", "Spires", "Sculptures",
            "Slide", "Penguins", "FishHut", "Cannon", "Crystals", "SnowFort", "HotSpring", "Glacier", "Observatory", "Throne",
            "Obelisk", "Drake", "Crown"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

# preview camera: azimuth / elevation / distance multiplier per part (defaults below)
AZ = {}
ELEV = {"Ground": 52}
MULT = {"Glacier": 2.9, "Slide": 2.6, "Ground": 1.7, "Palace": 2.5, "Halo": 2.7, "Spires": 2.5, "Obelisk": 2.6, "Gate": 2.7, "Snowmen": 2.5}
SHIBA_RIGHT = {"Ground": None}


# ---- previews --------------------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift=0):
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
    g = dk.ground(low, high, color=(120, 140, 170))
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
        if pid == "Ground":
            sx, sz, sf = BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"]
        else:
            sx, sz, sf = hi[0] + 4.5, (lo[2] + hi[2]) / 2, 180
        sb = shiba_for(sx, sz, sf)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 30),
             MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 40, 2.6, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_IcePalace.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
