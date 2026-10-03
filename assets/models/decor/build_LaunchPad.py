"""Launch Pad decor models (theme LaunchPad): builds the 20 decor parts around the fourteenth Shiba (Astronaut Shiba).

Run:  blender --background --factory-startup --python build_LaunchPad.py -- <outdir> [PartId ...]   (use an absolute outdir)
Writes into <outdir>: Decor_LaunchPad_<PartId>.fbx, preview_<PartId>.png per part and stage_LaunchPad.png (3/4 + top view).
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Part ids after the out folder
rebuild only those parts (no stage render then). Models are built WITHOUT the part's Yaw (the game applies it).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "LaunchPad"))
ONLY = ARGS[1:]
KEY = "LaunchPad"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_LaunchPad.json"))

# ---- palette (one for all 20 parts) ----------------------------------------------------------------------------------
WHT = (238, 240, 246)
OFW = (208, 213, 224)
NAVY = (30, 48, 100)
ORG = (240, 128, 36)
RED = (214, 52, 48)
YEL = (250, 205, 50)
GLD = (226, 178, 66)
DGR = (72, 78, 92)
BLK = (34, 36, 44)
MET = (150, 156, 170)
CON = (152, 156, 162)
CONL = (178, 182, 190)
COND = (120, 124, 134)
GRAV = (172, 162, 140)
GRAVD = (146, 136, 118)
ASP = (60, 62, 72)
GRS = (118, 156, 92)
GRSD = (100, 140, 80)
GRSL = (136, 172, 104)
SOL = (38, 64, 136)
SOLL = (74, 108, 180)
RST = (176, 98, 62)
RSTD = (138, 74, 48)
RSTL = (196, 120, 80)
MOON = (176, 178, 184)
MOOND = (130, 132, 142)
GLS = (120, 182, 232)
GLSD = (44, 78, 130)


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vc(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xc(p, x0, x1, cy, cz, r, col, verts=10, jit=0.04, top_r=None):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit, top_radius=top_r)


def zc(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, top_r=None):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit, top_radius=top_r)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (absolute stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
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


def slab(p, poly_xz, y0, y1, col, jit=0.04):
    """Prism over a convex polygon in the x-z plane, from y0 to y1."""
    n = len(poly_xz)
    pts = [(x, y0, z) for x, z in poly_xz] + [(x, y1, z) for x, z in poly_xz]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def side(p, poly_xy, z0, z1, col, jit=0.04):
    """Prism over a polygon in the x-y plane (profile seen from the side), from z0 to z1."""
    n = len(poly_xy)
    pts = [(x, y, z0) for x, y in poly_xy] + [(x, y, z1) for x, y in poly_xy]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def front(p, poly_zy, x0, x1, col, jit=0.04):
    """Prism over a polygon in the z-y plane, from x0 to x1."""
    n = len(poly_zy)
    pts = [(x0, y, z) for z, y in poly_zy] + [(x1, y, z) for z, y in poly_zy]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def lathe(p, c, prof, segs, col, axis='y', jit=0.04, rot0=0.0, cap_start=True, cap_end=True):
    """Solid of revolution. prof = [(t, r), ...] along the axis ('y' or 'x'), r == 0 closes to a point; c = centre."""
    pts, rows = [], []

    def pt(t, a, b):
        if axis == 'y':
            return (c[0] + a, c[1] + t, c[2] + b)
        return (c[0] + t, c[1] + a, c[2] + b)
    for t, r in prof:
        if r < 1e-6:
            pts.append(pt(t, 0, 0))
            rows.append([len(pts) - 1] * segs)
        else:
            row = []
            for k in range(segs):
                a = rot0 + 2 * math.pi * k / segs
                pts.append(pt(t, r * math.cos(a), r * math.sin(a)))
                row.append(len(pts) - 1)
            rows.append(row)
    faces = []
    for i in range(len(prof) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            quad = []
            for v in (rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]):
                if v not in quad:
                    quad.append(v)
            if len(quad) >= 3:
                faces.append(tuple(quad))
    if cap_start and len(set(rows[0])) > 1:
        faces.append(tuple(rows[0]))
    if cap_end and len(set(rows[-1])) > 1:
        faces.append(tuple(rows[-1]))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def dome(p, cx, y0, cz, rx, h, col, rz=None, segs=12, rings=4, jit=0.04, base=True):
    """Half sphere (flattened to height h) standing on y0."""
    rz = rx if rz is None else rz
    prof = []
    for i in range(rings + 1):
        a = (math.pi / 2) * i / rings
        prof.append((y0 + h * math.sin(a), math.cos(a)))
    pts, rows = [], []
    for t, f in prof:
        if f < 1e-6:
            pts.append((cx, t, cz))
            rows.append([len(pts) - 1] * segs)
        else:
            row = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                pts.append((cx + rx * f * math.cos(a), t, cz + rz * f * math.sin(a)))
                row.append(len(pts) - 1)
            rows.append(row)
    faces = []
    for i in range(rings):
        for k in range(segs):
            k2 = (k + 1) % segs
            quad = []
            for v in (rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]):
                if v not in quad:
                    quad.append(v)
            faces.append(tuple(quad))
    if base:
        faces.append(tuple(rows[0]))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def annulus(p, cx, cz, r0, r1, y0, y1, col, segs=24, jit=0.02):
    """Flat ring on the floor (closed tube of rectangular section)."""
    pts, faces = [], []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        c, s = math.cos(a), math.sin(a)
        for rr, y in ((r0, y0), (r1, y0), (r1, y1), (r0, y1)):
            pts.append((cx + rr * c, y, cz + rr * s))
    for k in range(segs):
        k2 = (k + 1) % segs
        for j in range(4):
            j2 = (j + 1) % 4
            faces.append((k * 4 + j, k2 * 4 + j, k2 * 4 + j2, k * 4 + j2))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def fin(p, cx, cz, dx, dz, pts2d, th, col, jit=0.04):
    """Flat fin: pts2d = (u, y) outline, u runs outward along (dx, dz) from (cx, cz); thickness th across it."""
    n = len(pts2d)
    pts = []
    for w in (-th / 2, th / 2):
        for u, y in pts2d:
            pts.append((cx + dx * u - dz * w, y, cz + dz * u + dx * w))
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def star(p, c, plane, ro, ri, thick, col, n=5, rot0=90, jit=0.03):
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
    """Block letter in the x-y plane (readable from +z), box strokes."""
    zc_, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.03)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zc_, x0 + c, y0 + e, t, d, col, 0.03)
    if ch in 'O0':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'L':
        r(0, 0, t, h); r(0, 0, w, t)
    elif ch == 'I':
        r(0, 0, w, t); r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h)
    elif ch == '1':
        r(w / 2 - t / 2, 0, w / 2 + t / 2, h); r(w * 0.15, 0, w * 0.85, t); dg(w / 2 - t / 2, h - t * 0.4, w * 0.1, h * 0.72)
    elif ch == 'C':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, 0, w, t)
    elif ch == 'E':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2); r(t, 0, w, t)
    elif ch == 'F':
        r(0, 0, t, h); r(t, h - t, w, h); r(t, h / 2 - t / 2, w * 0.85, h / 2 + t / 2)
    elif ch == 'A':
        r(0, 0, t, h - t); r(w - t, 0, w, h - t); r(0, h - t, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'N':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w - t * 0.5, t * 0.5)
    elif ch == 'U':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, 0, w - t, t)
    elif ch == 'T':
        r(0, h - t, w, h); r(w / 2 - t / 2, 0, w / 2 + t / 2, h - t)
    elif ch == 'S':
        r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(0, 0, w, t); r(0, h / 2, t, h - t); r(w - t, t, w, h / 2)
    elif ch == 'H':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h / 2 - t / 2, w - t, h / 2 + t / 2)
    elif ch == 'R':
        r(0, 0, t, h); r(0, h - t, w, h); r(0, h / 2 - t / 2, w, h / 2 + t / 2); r(w - t, h / 2, w, h - t)
        dg(t * 0.6, h / 2, w - t * 0.4, t * 0.3)
    elif ch == 'B':
        r(0, 0, t, h); r(0, h - t, w - t * 0.6, h); r(0, h / 2 - t / 2, w - t * 0.3, h / 2 + t / 2); r(0, 0, w - t * 0.6, t)
        r(w - t, h / 2, w, h - t * 0.5); r(w - t, t * 0.5, w, h / 2)
    elif ch == '-':
        r(w * 0.1, h / 2 - t / 2, w * 0.9, h / 2 + t / 2)


def text(p, s, cx, y0, z0, z1, w, h, t, gap, col):
    total = len(s) * w + (len(s) - 1) * gap
    x = cx - total / 2
    for ch in s:
        if ch != ' ':
            letter(p, ch, x, y0, z0, z1, w, h, t, col)
        x += w + gap


def dish(p, c, R, depth, col, tilt=0.0, face=1, rim=None, feed=True, verts=12):
    """Radar dish: a hollow bowl opening toward its facing direction (+x if face=1, -x if face=-1), tilted up by `tilt` degrees."""
    a = math.radians(tilt)
    d = (face * math.cos(a), math.sin(a), 0.0)
    v = (-d[1], d[0], 0.0)
    depth = max(depth, R * 0.38)
    th = max(0.22, R * 0.07)
    rs = (0.0, 0.3, 0.55, 0.8, 1.0)
    prof = [(-depth / 2 + depth * r * r, R * r) for r in rs] + [(-depth / 2 + depth * r * r - th, R * r) for r in reversed(rs)]
    pts, rows = [], []
    for t, r in prof:
        if r < 1e-6:
            pts.append((c[0] + d[0] * t, c[1] + d[1] * t, c[2]))
            rows.append([len(pts) - 1] * verts)
        else:
            row = []
            for k in range(verts):
                ph = 2 * math.pi * k / verts
                cs, sn = math.cos(ph), math.sin(ph)
                pts.append((c[0] + d[0] * t + v[0] * r * cs, c[1] + d[1] * t + v[1] * r * cs, c[2] + r * sn))
                row.append(len(pts) - 1)
            rows.append(row)
    faces = []
    for i in range(len(prof) - 1):
        for k in range(verts):
            k2 = (k + 1) % verts
            quad = []
            for q in (rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]):
                if q not in quad:
                    quad.append(q)
            if len(quad) >= 3:
                faces.append(tuple(quad))
    dk.poly(p, (0, 0, 0), pts, faces, col, 0.03)
    fc = (c[0] + d[0] * (depth / 2 + R * 0.5), c[1] + d[1] * (depth / 2 + R * 0.5), c[2])
    if feed:
        dk.cyl(p, fc, R * 0.07, R * 0.3, DGR, axis='x', verts=6, rot=(0, 0, math.degrees(math.atan2(d[1], d[0]))), jitter=0.02)
        e = (c[0] + d[0] * depth / 2, c[1] + d[1] * depth / 2, c[2])
        for u, w in ((1, 0), (-0.5, 0.87), (-0.5, -0.87)):
            tip = (e[0] + v[0] * R * 0.97 * u, e[1] + v[1] * R * 0.97 * u, e[2] + R * 0.97 * w)
            bar(p, tip, fc, R * 0.05, DGR, 0.02)
    # hub on the back
    hb = (c[0] - d[0] * (depth / 2 + th), c[1] - d[1] * (depth / 2 + th), c[2])
    dk.cyl(p, hb, R * 0.16, R * 0.25, DGR, axis='x', verts=6, rot=(0, 0, math.degrees(math.atan2(d[1], d[0]))), jitter=0.02)


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


# ---- 1. Ground -----------------------------------------------------------------------------------------------------------
def build_Ground(p):
    bx(p, (-95, 95), (0, 0.3), (-65, 65), GRS, 0.02)
    for x, z, w, d, c in [(-20, 10, 30, 16, GRSL), (30, 20, 26, 14, GRSD), (-70, -40, 34, 20, GRSD), (10, 60, 40, 8, GRSL),
                          (-40, -58, 30, 10, GRSL), (88, 10, 10, 40, GRSD), (-90, 50, 10, 26, GRSL), (40, -10, 18, 12, GRSL),
                          (-30, -30, 12, 10, GRSD), (60, 8, 16, 10, GRSD)]:
        bx(p, (x - w / 2, x + w / 2), (0.3, 0.34), (z - d / 2, z + d / 2), c, 0.02)
    # launch apron with expansion joints and a yellow edge
    bx(p, (38, 86), (0.3, 0.4), (-64, -24), CON)
    for xx in range(46, 86, 8):
        bx(p, (xx - 0.15, xx + 0.15), (0.4, 0.45), (-64, -24), COND, 0.02)
    for zz in range(-56, -24, 8):
        bx(p, (38, 86), (0.4, 0.45), (zz - 0.15, zz + 0.15), COND, 0.02)
    bx(p, (38, 86), (0.4, 0.46), (-25.6, -24.4), YEL, 0.02)
    # crawler road
    bx(p, (-4, 48), (0.3, 0.4), (-54.5, -45.5), GRAV)
    for zz in (-52.2, -47.8):
        bx(p, (-4, 48), (0.4, 0.44), (zz - 0.5, zz + 0.5), GRAVD, 0.03)
    for xx in range(0, 48, 6):
        bx(p, (xx, xx + 1.4), (0.4, 0.46), (-50.6, -49.4), CONL, 0.03)
    # landing target
    bx(p, (-11, 11), (0.3, 0.4), (-35, -13), ASP)
    annulus(p, 0, -24, 8.6, 10.0, 0.4, 0.47, WHT, 24)
    annulus(p, 0, -24, 5.0, 6.2, 0.4, 0.47, WHT, 20)
    vc(p, 0, 0.4, 0.47, -24, 3.2, RED, 14, jit=0.02)
    for s in (1, -1):
        bx(p, (s * 7.4 - 0.9, s * 7.4 + 0.9), (0.4, 0.47), (-24.5, -23.5), WHT, 0.02)
        bx(p, (-0.5, 0.5), (0.4, 0.47), (-24 + s * 7.4 - 0.9, -24 + s * 7.4 + 0.9), WHT, 0.02)
    bx(p, (-1.7, -1.0), (0.47, 0.5), (-25.8, -22.2), WHT, 0.02)
    bx(p, (1.0, 1.7), (0.47, 0.5), (-25.8, -22.2), WHT, 0.02)
    bx(p, (-1.0, 1.0), (0.47, 0.5), (-24.35, -23.65), WHT, 0.02)
    # forecourt in front of the Shiba
    bx(p, (-79, -53), (0.3, 0.4), (1, 43), CONL)
    for zz in range(7, 43, 6):
        bx(p, (-79, -53), (0.4, 0.45), (zz - 0.15, zz + 0.15), COND, 0.02)
    bx(p, (-66.15, -65.85), (0.4, 0.45), (1, 43), COND, 0.02)
    bx(p, (-79, -78.2), (0.4, 0.46), (1, 43), YEL, 0.02)
    bx(p, (-53.8, -53), (0.4, 0.46), (1, 43), YEL, 0.02)
    annulus(p, -60, 22, 5.6, 6.6, 0.4, 0.47, NAVY, 20)
    # paw print
    vc(p, -70, 0.4, 0.47, 33, 2.4, NAVY, 12, jit=0.02)
    for ox, oz in ((-3.4, 3.6), (-1.2, 4.9), (1.2, 4.9), (3.4, 3.6)):
        vc(p, -70 + ox, 0.4, 0.47, 33 + oz, 1.05, NAVY, 8, jit=0.02)
    # parking apron
    bx(p, (63, 89), (0.3, 0.4), (43, 61), ASP)
    for xx in (65, 69.5, 74, 78.5, 83, 87):
        bx(p, (xx - 0.2, xx + 0.2), (0.4, 0.46), (46, 61), WHT, 0.02)
    bx(p, (63, 89), (0.4, 0.46), (43.5, 44.1), YEL, 0.02)


# ---- 2. Control ----------------------------------------------------------------------------------------------------------
def build_Control(p):
    bx(p, (-88, -74), (0.3, 10.3), (7, 37), WHT)
    bx(p, (-88.2, -73.8), (0.3, 1.5), (6.8, 37.2), OFW, 0.03)                       # plinth band
    bx(p, (-88.5, -73.5), (10.3, 10.9), (6.5, 37.5), NAVY, 0.03)                    # roof
    for a, b, c, d in ((-88.5, -73.5, 6.5, 7.1), (-88.5, -73.5, 36.9, 37.5), (-88.5, -87.9, 6.5, 37.5), (-74.1, -73.5, 6.5, 37.5)):
        bx(p, (a, b), (10.9, 11.5), (c, d), WHT, 0.03)                              # parapet
    for x, z in ((-82, 28), (-79, 33.5), (-85, 20)):
        bx(p, (x - 1.3, x + 1.3), (10.9, 12.3), (z - 1.2, z + 1.2), MET, 0.04)
        bx(p, (x - 0.9, x + 0.9), (12.3, 12.5), (z - 0.8, z + 0.8), DGR, 0.03)
    # glazed lobby with canopy
    bx(p, (-74, -71.9), (0.3, 5.5), (13, 31), GLS, 0.05)
    for z in (13, 16, 19, 25, 28, 31):
        bx(p, (-72.3, -71.7), (0.3, 5.5), (z - 0.25, z + 0.25), WHT, 0.02)
    bx(p, (-72.2, -71.6), (0.3, 4.2), (20.6, 23.4), NAVY, 0.03)                     # door
    bx(p, (-74, -69.8), (5.5, 6.05), (16, 28), ORG, 0.03)                           # canopy
    bx(p, (-74, -69.8), (6.05, 6.35), (13, 31), WHT, 0.03)
    for z in (16.4, 27.6):
        bx(p, (-70.4, -69.9), (0.3, 5.5), (z - 0.25, z + 0.25), WHT, 0.02)
    # window rows
    for z in (10.2, 14.8, 29.2, 33.8):
        bx(p, (-74.0, -73.8), (7.0, 9.6), (z - 2, z + 2), WHT, 0.02)
        bx(p, (-73.8, -73.65), (7.3, 9.3), (z - 1.7, z + 1.7), GLSD, 0.04)
    xc(p, -74.0, -73.6, 8.4, 22, 2.5, NAVY, 14, 0.02)                                # logo disc
    xc(p, -73.6, -73.4, 8.4, 22, 1.7, ORG, 14, 0.02)
    xc(p, -73.4, -73.2, 8.4, 22, 0.8, WHT, 10, 0.02)
    for x in (-84, -78):
        bx(p, (x - 1.7, x + 1.7), (7.3, 9.3), (36.9, 37.2), GLSD, 0.04)
        bx(p, (x - 1.7, x + 1.7), (7.3, 9.3), (6.8, 7.1), GLSD, 0.04)
    # flight tower
    vc(p, -84, 10.9, 20.9, 12, 2.8, WHT, 12)
    vc(p, -84, 14.2, 14.9, 12, 3.05, NAVY, 12, jit=0.02)
    vc(p, -84, 18.0, 18.6, 12, 3.05, NAVY, 12, jit=0.02)
    vc(p, -84, 20.9, 22.6, 12, 3.5, GLSD, 12, jit=0.03)
    for k in range(6):
        a = k * math.pi / 3
        bx(p, (-84 + 3.5 * math.cos(a) - 0.2, -84 + 3.5 * math.cos(a) + 0.2), (20.9, 22.6), (12 + 3.5 * math.sin(a) - 0.2, 12 + 3.5 * math.sin(a) + 0.2), WHT, 0.02)
    vc(p, -84, 22.6, 23.2, 12, 4.0, WHT, 12, top_r=3.4)
    vc(p, -84, 23.2, 25.0, 12, 0.18, DGR, 6)
    ball(p, (-84, 25.2, 12), 0.35, RED, subdiv=1)
    # dish on a pedestal
    vc(p, -79, 10.9, 14.1, 30, 0.8, DGR, 8)
    dish(p, (-78, 16, 30), 4.5, 1.2, WHT, tilt=28, face=1)
    # antenna mast
    for k in range(5):
        vc(p, -86, 10.9 + k * 4.04, 10.9 + (k + 1) * 4.04, 32, 0.45, RED if k % 2 == 0 else WHT, 6, jit=0.02)
    ball(p, (-86, 30.6, 32), 0.6, RED, subdiv=1, jit=0.02)
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bar(p, (-86, 17, 32), (-86 + sx * 3.2, 11, 32 + sz * 3.2), 0.12, DGR, 0.02)  # guy wires


# ---- 3. Platform ---------------------------------------------------------------------------------------------------------
def build_Platform(p):
    vc(p, 62, 0.3, 0.58, -44, 14, CON, 16)
    annulus(p, 62, -44, 12.0, 13.2, 0.58, 0.64, YEL, 16)
    annulus(p, 62, -44, 7.6, 8.2, 0.58, 0.64, DGR, 12)
    bx(p, (56, 68), (0.58, 0.64), (-50, -38), DGR, 0.02)                              # trench plate
    bx(p, (60.6, 63.4), (0.58, 0.66), (-60, -50), BLK, 0.02)                          # flame trench channel
    for z in (-58, -55, -52):
        bx(p, (60.2, 63.8), (0.58, 0.7), (z - 0.2, z + 0.2), DGR, 0.02)
    # blast wall with hazard stripes
    bx(p, (51, 73), (0.3, 3.7), (-61.8, -60.2), CONL)
    bx(p, (51, 73), (3.7, 4.0), (-62.0, -60.0), CON, 0.03)
    for i in range(11):
        bx(p, (51.1 + i * 2, 52.1 + i * 2), (0.3, 1.5), (-60.2, -59.95), YEL if i % 2 == 0 else BLK, 0.02)
    # floodlight masts
    for x in (49, 75):
        vc(p, x, 0.3, 1.5, -58, 1.15, CON, 8)
        vc(p, x, 1.5, 26.3, -58, 0.65, DGR, 8, top_r=0.5)
        for y in (8, 14, 20):
            bx(p, (x - 0.9, x + 0.9), (y, y + 0.25), (-58.9, -57.1), DGR, 0.02)
        bx(p, (x - 2.2, x + 2.2), (26.3, 27.7), (-58.8, -57.2), DGR, 0.03)
        for i in range(4):
            bx(p, (x - 1.9 + i * 1.0, x - 1.1 + i * 1.0), (26.55, 27.45), (-57.2, -56.9), YEL, 0.02)
    # cable cabinets
    for x in (54, 70):
        bx(p, (x - 1.5, x + 1.5), (0.3, 2.7), (-58, -56), ORG, 0.03)
        bx(p, (x - 1.4, x + 1.4), (2.7, 2.9), (-58.1, -55.9), DGR, 0.03)
        bx(p, (x - 0.9, x + 0.9), (0.6, 2.2), (-56.0, -55.85), DGR, 0.02)
        bx(p, (x + 0.2, x + 0.5), (1.1, 1.6), (-55.85, -55.7), YEL, 0.02)
        bx(p, (x - 0.5 - 0.15, x - 0.5 + 0.15), (0.3, 0.9), (-56.0, -55.0), BLK, 0.02)
    # cable runs and bollards
    bx(p, (54, 60), (0.58, 0.72), (-56.3, -55.7), BLK, 0.02)
    bx(p, (64, 70), (0.58, 0.72), (-56.3, -55.7), BLK, 0.02)
    for x, z in ((50, -34), (74, -34), (50, -52), (74, -52)):
        vc(p, x, 0.58, 1.6, z, 0.4, YEL, 6, jit=0.02)
    # hold-down posts, water deluge ring with nozzles
    for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        bx(p, (62 + sx * 5.2 - 0.7, 62 + sx * 5.2 + 0.7), (0.58, 1.9), (-44 + sz * 5.2 - 0.7, -44 + sz * 5.2 + 0.7), ORG, 0.03)
        bx(p, (62 + sx * 5.2 - 0.8, 62 + sx * 5.2 + 0.8), (1.9, 2.2), (-44 + sz * 5.2 - 0.8, -44 + sz * 5.2 + 0.8), YEL, 0.02)
    annulus(p, 62, -44, 10.0, 10.6, 0.64, 0.95, COND, 12, 0.03)
    for k in range(8):
        a = k * math.pi / 4 + 0.39
        vc(p, 62 + 10.3 * math.cos(a), 0.95, 1.6, -44 + 10.3 * math.sin(a), 0.25, GLS, 6, jit=0.02)
    # umbilical tower base plinths
    for x in (47.5, 76.5):
        bx(p, (x - 0.8, x + 0.8), (0.3, 0.9), (-45, -43), CON, 0.03)


# ---- 4. Rocket -----------------------------------------------------------------------------------------------------------
def build_Rocket(p):
    X, Z = 62, -44
    # engine bells
    for dx, dz in ((0, 0), (2.2, 0), (-2.2, 0), (0, 2.2), (0, -2.2)):
        vc(p, X + dx, 0.6, 2.2, Z + dz, 1.3 if dx or dz else 1.5, BLK, 8, top_r=0.6)
    vc(p, X, 2.2, 3.8, Z, 3.8, DGR, 12, jit=0.03)
    # fins (swept)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        fin(p, X, Z, dx, dz, [(3.9, 11.5), (3.9, 3.6), (7, 2.0), (7, 5.8)], 0.8, RED)
        fin(p, X, Z, dx, dz, [(7, 2.0), (7, 5.8), (6.4, 5.8), (6.4, 2.0)], 0.9, DGR, 0.02)
    # body
    vc(p, X, 3.8, 26, Z, 4.5, WHT, 14, jit=0.03)
    vc(p, X, 8.0, 10.0, Z, 4.55, BLK, 14, jit=0.02)
    vc(p, X, 12.0, 13.0, Z, 4.55, RED, 14, jit=0.02)
    vc(p, X, 26, 27, Z, 4.7, NAVY, 14, jit=0.02)
    vc(p, X, 27, 39, Z, 4.0, WHT, 14, top_r=3.9, jit=0.03)
    vc(p, X, 33.5, 34.5, Z, 4.05, RED, 14, jit=0.02)
    vc(p, X, 39, 43, Z, 3.4, RED, 14, top_r=2.0)
    vc(p, X, 43, 46, Z, 1.9, RED, 12, top_r=0.5)
    vc(p, X, 46, 48, Z, 0.35, DGR, 6)
    # portholes and stripes facing +z and +x
    for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        for y in (20.5, 29.5):
            cx, cz = X + dx * 4.0, Z + dz * 4.0
            if dx == 0:
                bx(p, (cx - 1.0, cx + 1.0), (y - 1.0, y + 1.0), (cz - 0.2 + dz * 0.3, cz + 0.2 + dz * 0.3), NAVY, 0.02)
                bx(p, (cx - 0.6, cx + 0.6), (y - 0.6, y + 0.6), (cz - 0.1 + dz * 0.5, cz + 0.1 + dz * 0.5), GLS, 0.02)
            else:
                bx(p, (cx - 0.2 + dx * 0.3, cx + 0.2 + dx * 0.3), (y - 1.0, y + 1.0), (cz - 1.0, cz + 1.0), NAVY, 0.02)
                bx(p, (cx - 0.1 + dx * 0.5, cx + 0.1 + dx * 0.5), (y - 0.6, y + 0.6), (cz - 0.6, cz + 0.6), GLS, 0.02)
        bx(p, (X + dx * 4.4 - (0.5 if dz else 0.15) + 0.0, X + dx * 4.4 + (0.5 if dz else 0.15)), (14.5, 24.5),
           (Z + dz * 4.4 - (0.5 if dx else 0.15), Z + dz * 4.4 + (0.5 if dx else 0.15)), OFW, 0.02)   # seam panels
    # emblem stripe on the +z face
    zc(p, X, 17.5, Z + 4.1, Z + 4.7, 2.3, NAVY, 14, 0.02)
    zc(p, X, 16.8, Z + 4.7, Z + 4.95, 0.9, WHT, 8, 0.02)
    for tx, ty, tr in ((-1.2, 18.2, 0.42), (-0.45, 18.9, 0.42), (0.45, 18.9, 0.42), (1.2, 18.2, 0.42)):
        zc(p, X + tx, ty, Z + 4.7, Z + 4.95, tr, WHT, 6, 0.02)


# ---- 5. Sign -------------------------------------------------------------------------------------------------------------
def build_Sign(p):
    for x in (-33, -15):
        bx(p, (x - 0.7, x + 0.7), (0.3, 7.3), (51.3, 52.7), DGR)
        bx(p, (x - 1.4, x + 1.4), (0.3, 1.1), (51.0, 53.0), CON, 0.03)
    bar(p, (-33, 1.1, 52), (-30, 7.3, 52), 0.5, DGR, 0.03)
    bar(p, (-15, 1.1, 52), (-18, 7.3, 52), 0.5, DGR, 0.03)
    bx(p, (-37, -11), (7.3, 17.3), (51.3, 52.7), NAVY, 0.03)                         # board
    bx(p, (-36.4, -11.6), (7.9, 16.7), (52.7, 52.95), BLK, 0.02)                       # display
    bx(p, (-38, -10), (17.3, 18.4), (50.8, 53.2), ORG, 0.03)                           # top beam
    for x in (-34.4, -13.6):
        bx(p, (x - 0.8, x + 0.8), (18.4, 19.6), (51.2, 52.8), YEL, 0.02)
        bx(p, (x - 0.4, x + 0.4), (19.6, 20.0), (51.6, 52.4), RED, 0.02)
    text(p, "T-10", -24, 11.0, 52.95, 53.2, 4.0, 5.2, 0.9, 1.1, ORG)
    text(p, "LIFT OFF", -24, 8.4, 52.95, 53.2, 2.1, 2.1, 0.5, 0.5, WHT)
    for x in (-35.6, -12.4):                                                         # corner lights
        bx(p, (x - 0.35, x + 0.35), (15.6, 16.3), (52.95, 53.2), RED, 0.02)
        bx(p, (x - 0.35, x + 0.35), (8.4, 9.1), (52.95, 53.2), YEL, 0.02)


# ---- 6. Gantry -----------------------------------------------------------------------------------------------------------
def build_Gantry(p):
    bx(p, (45.5, 54.5), (0.5, 1.3), (-48.5, -39.5), CON)
    legs = [(47, -47), (53, -47), (47, -41), (53, -41)]
    for x, z in legs:
        bx(p, (x - 0.45, x + 0.45), (1.3, 40.3), (z - 0.45, z + 0.45), ORG, 0.03)
    levels = (1.3, 13, 25, 37, 40.3)
    for a, b in zip(levels[:-1], levels[1:]):
        for (x1, z1), (x2, z2) in ((legs[0], legs[1]), (legs[2], legs[3]), (legs[0], legs[2]), (legs[1], legs[3])):
            bar(p, (x1, a, z1), (x2, b, z2), 0.28, ORG, 0.03)
            bar(p, (x2, a, z2), (x1, b, z1), 0.28, ORG, 0.03)
    for y in (13, 25, 37):
        bx(p, (46.3, 53.7), (y - 0.25, y + 0.25), (-47.7, -40.3), DGR, 0.03)
        for x in (46.3, 53.7):
            bx(p, (x - 0.1, x + 0.1), (y + 0.25, y + 1.4), (-47.7, -40.3), YEL, 0.02)
        for z in (-47.7, -40.3):
            bx(p, (46.3, 53.7), (y + 1.2, y + 1.4), (z - 0.1, z + 0.1), YEL, 0.02)
    # swing arms toward the rocket
    for y in (14.2, 26.2, 36.2):
        bx(p, (53.7, 58), (y - 0.6, y + 0.6), (-44.9, -43.1), ORG, 0.03)
        bx(p, (57.2, 58), (y - 0.9, y + 0.9), (-45.4, -42.6), WHT, 0.02)
        bar(p, (53.7, y - 0.55, -44), (57.0, y - 0.55, -44), 0.2, DGR, 0.02)
    # elevator box and ladder on the back
    bx(p, (50.5, 52.5), (1.3, 5), (-46.2, -45.2), WHT, 0.03)
    bx(p, (50.8, 52.2), (1.8, 3.4), (-45.2, -45.0), GLSD, 0.03)
    for y in range(3, 40, 3):
        bx(p, (49.4, 50.2), (y, y + 0.2), (-48.6, -48.4), DGR, 0.02)
    # top: lightning mast and beacon
    vc(p, 50, 40.3, 45.3, -44, 0.3, DGR, 6)
    ball(p, (50, 45.2, -44), 0.5, RED, subdiv=1, jit=0.02)
    bx(p, (49.2, 50.8), (40.3, 41.3), (-44.8, -43.2), YEL, 0.03)


# ---- 7. Rover ------------------------------------------------------------------------------------------------------------
def build_Rover(p):
    for z in (40.9, 47.1):
        for x in (-51.5, -48, -44.5):
            zc(p, x, 1.9, z - 0.6, z + 0.6, 1.6, DGR, 12, jit=0.03)
            zc(p, x, 1.9, z - 0.7 if z < 44 else z + 0.5, z - 0.5 if z < 44 else z + 0.7, 0.8, MET, 8, jit=0.02)
        bar(p, (-51.5, 1.9, z), (-44.5, 1.9, z), 0.5, MET, 0.03)
    bx(p, (-52.5, -43.5), (2.3, 3.5), (41.3, 46.7), OFW)                             # chassis
    bx(p, (-52.9, -43.1), (3.1, 3.5), (41.1, 46.9), WHT, 0.03)
    bx(p, (-51.2, -48.8), (3.5, 5.3), (42.4, 45.6), ORG, 0.03)                       # cab
    bx(p, (-48.9, -48.5), (3.9, 5.0), (42.7, 45.3), GLSD, 0.03)
    bx(p, (-50, -46.5), (3.5, 4.4), (41.4, 42.3), NAVY, 0.03)
    # solar panel on the back and cargo
    bx(p, (-52.4, -50.8), (3.5, 3.8), (41.4, 46.6), SOL, 0.03)
    bx(p, (-52.4, -50.8), (3.8, 4.4), (41.4, 41.7), YEL, 0.02)
    # mast with camera and dish
    vc(p, -45, 3.5, 7.5, 44, 0.25, DGR, 6)
    bx(p, (-45.6, -44.4), (6.8, 7.4), (43.5, 44.5), DGR, 0.03)
    dish(p, (-45.2, 8.0, 44), 1.5, 0.45, WHT, tilt=40, face=-1, feed=False, verts=10)
    bar(p, (-43.6, 3.4, 45.8), (-43.0, 6.5, 45.8), 0.12, DGR, 0.02)                  # whip antenna
    # front scoop and bumper
    bx(p, (-43.8, -43.2), (2.1, 3.0), (41.8, 46.2), YEL, 0.03)
    # flag
    vc(p, -52, 3.5, 6.5, 41.7, 0.1, DGR, 6, jit=0.02)
    bx(p, (-52.9, -52.0), (5.8, 6.5), (41.6, 41.8), RED, 0.02)


# ---- 8. Tanks ------------------------------------------------------------------------------------------------------------
def build_Tanks(p):
    bx(p, (-48.5, -24), (0.3, 0.5), (-33.5, -15.5), CON, 0.03)
    for x in (-43, -29):
        vc(p, x, 0.5, 1.0, -21, 4.4, COND, 12, jit=0.03)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            bar(p, (x + 3.6 * math.cos(a), 0.9, -21 + 3.6 * math.sin(a)), (x + 4.9 * math.cos(a), 7.2, -21 + 4.9 * math.sin(a)), 0.7, DGR, 0.03)
        vc(p, x, 3.1, 3.6, -21, 4.4, DGR, 12, jit=0.02)
        ball(p, (x, 9.2, -21), 5.5, WHT, subdiv=2, jit=0.03)
        vc(p, x, 8.9, 9.6, -21, 5.56, ORG, 14, jit=0.02)                              # equator band
        vc(p, x, 14.3, 14.9, -21, 0.9, DGR, 8)                                         # top hatch
        vc(p, x + 1.5, 14.0, 15.4, -21.8, 0.25, MET, 6)                                # vent
        # ladder up the side
        for y in (2.0, 4.0, 6.0, 8.0, 10.0):
            bx(p, (x - 0.5, x + 0.5), (y, y + 0.18), (-26.1 + (0.0 if y < 8 else -0.3), -25.9 + (0.0 if y < 8 else -0.3)), YEL, 0.02)
        bx(p, (x - 0.55, x - 0.4), (1.0, 10.6), (-26.15, -25.95), YEL, 0.02)
        bx(p, (x + 0.4, x + 0.55), (1.0, 10.6), (-26.15, -25.95), YEL, 0.02)
    # catwalk between the spheres
    bx(p, (-38.6, -33.4), (11.8, 12.2), (-22.2, -19.8), DGR, 0.03)
    for z in (-22.2, -19.8):
        bx(p, (-38.6, -33.4), (12.2, 13.1), (z - 0.06, z + 0.06), YEL, 0.02)
    # connecting pipe with elbow and valve wheels
    xc(p, -41, -31, 3.0, -21, 0.45, ORG, 8)
    bar(p, (-36, 3.0, -21), (-36, 2.6, -28.7), 0.9, ORG, 0.03)
    vc(p, -36, 3.5, 4.4, -21, 0.9, RED, 8, jit=0.03)
    bx(p, (-37, -35), (4.4, 4.6), (-21.2, -20.8), RED, 0.02)
    vc(p, -33.2, 3.0, 4.0, -21, 0.6, YEL, 8, jit=0.03)
    # bullet tank
    xc(p, -44.2, -27.8, 2.6, -31, 2.3, WHT, 14, jit=0.03)
    for x in (-45.2, -26.8):
        ball(p, (x + (1.0 if x < -36 else -1.0), 2.6, -31), 2.3, WHT, scale=(0.8, 1, 1), subdiv=2, jit=0.03)
    for x in (-40.5, -31.5):
        xc(p, x - 0.4, x + 0.4, 2.6, -31, 2.36, RED, 14, jit=0.02)
    vc(p, -36, 4.8, 5.1, -31, 0.7, DGR, 8)
    bx(p, (-41.8, -40.2), (0.3, 2.5), (-33.5, -28.5), DGR, 0.03)
    bx(p, (-31.8, -30.2), (0.3, 2.5), (-33.5, -28.5), DGR, 0.03)
    bx(p, (-42.0, -40.0), (2.3, 2.6), (-33.0, -29.0), COND, 0.03)
    bx(p, (-32.0, -30.0), (2.3, 2.6), (-33.0, -29.0), COND, 0.03)
    # hazard diamond sign and gauge
    bx(p, (-37.3, -34.7), (1.9, 4.5), (-28.65, -28.5), YEL, 0.02, rot=(0, 0, 0))
    bx(p, (-36.6, -35.4), (2.7, 3.7), (-28.5, -28.4), RED, 0.02)


# ---- 9. Radar ------------------------------------------------------------------------------------------------------------
def build_Radar(p):
    for cx, cz, pw in ((-82, -8, 11), (-70, -22, 9)):
        bx(p, (cx - pw / 2, cx + pw / 2), (0.3, 0.58), (cz - pw / 2, cz + pw / 2), CON)
        for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            bx(p, (cx + sx * (pw / 2 - 0.9) - 0.5, cx + sx * (pw / 2 - 0.9) + 0.5), (0.58, 0.64), (cz + sz * (pw / 2 - 0.9) - 0.5, cz + sz * (pw / 2 - 0.9) + 0.5), YEL, 0.02)
    # big dish
    vc(p, -82, 0.58, 8.2, -8, 1.5, WHT, 10, top_r=1.1)
    bx(p, (-84.5, -79.5), (8.2, 9.8), (-9.2, -6.8), DGR)
    for z in (-9.5, -6.5):
        bx(p, (-82.4, -81.6), (9.8, 13.3), (z - 0.25, z + 0.25), DGR, 0.03)
    dish(p, (-82, 13.9, -8), 5.5, 1.3, WHT, tilt=38, face=1)
    # second dish
    vc(p, -70, 0.58, 7.0, -22, 1.3, WHT, 10, top_r=0.9)
    bx(p, (-72.2, -67.8), (7.0, 8.4), (-23.1, -20.9), DGR)
    for z in (-23.2, -20.8):
        bx(p, (-70.4, -69.6), (8.4, 11.0), (z - 0.2, z + 0.2), DGR, 0.03)
    dish(p, (-70, 11.4, -22), 4.5, 1.2, WHT, tilt=52, face=-1)
    # control cabin
    bx(p, (-87, -81), (0.3, 4.9), (-24.5, -19.5), OFW)
    bx(p, (-87.3, -80.7), (4.9, 5.4), (-24.8, -19.2), NAVY, 0.03)
    bx(p, (-85.4, -83.2), (0.3, 3.6), (-19.5, -19.3), DGR, 0.03)
    bx(p, (-82.6, -81.2), (2.2, 3.8), (-19.5, -19.3), GLSD, 0.03)
    bx(p, (-86.6, -85.2), (2.2, 3.8), (-19.5, -19.3), GLSD, 0.03)
    bx(p, (-81.0, -80.6), (1.0, 3.6), (-23.5, -20.5), GLSD, 0.03)
    dish(p, (-84, 6.4, -22), 1.5, 0.5, WHT, tilt=50, face=1, feed=False, verts=8)
    vc(p, -84, 5.4, 6.3, -22, 0.2, DGR, 6)
    # antenna mast with beacon
    for k in range(4):
        vc(p, -76, 0.3 + k * 2.85, 0.3 + (k + 1) * 2.85, -14, 0.5, RED if k % 2 == 0 else WHT, 6, jit=0.02)
    ball(p, (-76, 11.5, -14), 0.5, RED, subdiv=1, jit=0.02)
    bx(p, (-76.6, -75.4), (6.6, 6.8), (-14.6, -13.4), DGR, 0.02)
    # cable trays
    bx(p, (-81, -78), (0.3, 0.46), (-19.4, -18.8), BLK, 0.02)
    bx(p, (-78.4, -77.8), (0.3, 0.46), (-18.8, -13.5), BLK, 0.02)


# ---- 10. Cafe ------------------------------------------------------------------------------------------------------------
def build_Cafe(p):
    bx(p, (69, 83), (0.3, 6.1), (46, 54), WHT)
    bx(p, (68.8, 83.2), (0.3, 1.2), (45.8, 54.2), NAVY, 0.03)
    bx(p, (68.5, 83.5), (6.1, 6.9), (45.5, 54.5), RED, 0.03)
    bx(p, (68.5, 83.5), (6.0, 6.2), (54.5, 54.7), WHT, 0.03)
    # windows and door on the road side (+z)
    for x0, x1 in ((70, 73.8), (79.2, 82.4)):
        bx(p, (x0 - 0.3, x1 + 0.3), (1.9, 4.9), (54, 54.15), NAVY, 0.02)
        bx(p, (x0, x1), (2.2, 4.6), (54.15, 54.3), GLS, 0.04)
        bx(p, ((x0 + x1) / 2 - 0.1, (x0 + x1) / 2 + 0.1), (2.2, 4.6), (54.3, 54.4), NAVY, 0.02)
    bx(p, (75, 78), (0.3, 4.6), (54, 54.15), NAVY, 0.02)
    bx(p, (75.3, 77.7), (0.3, 4.4), (54.15, 54.3), ORG, 0.03)
    bx(p, (76.8, 77.1), (1.8, 2.5), (54.3, 54.45), YEL, 0.02)
    # striped awning
    for i in range(12):
        bx(p, (70 + i * 1.0, 71 + i * 1.0), (5.2, 5.6), (53.9, 56.9), RED if i % 2 == 0 else WHT, 0.02)
        bx(p, (70 + i * 1.0, 71 + i * 1.0), (4.7, 5.2), (56.5, 56.9), RED if i % 2 == 0 else WHT, 0.02)
    # roof sign board with CAFE
    bx(p, (70, 82.5), (6.9, 10.0), (50.2, 50.8), NAVY, 0.03)
    bx(p, (70.2, 82.3), (7.1, 9.8), (50.8, 51.0), BLK, 0.02)
    text(p, "CAFE", 76.25, 7.5, 51.0, 51.4, 2.3, 2.0, 0.55, 0.7, YEL)
    bx(p, (73, 74), (6.9, 7.1), (49, 50.2), DGR, 0.02)
    bx(p, (78.5, 79.5), (6.9, 7.1), (49, 50.2), DGR, 0.02)
    for x in (70.6, 81.9):                                                              # roof vents
        bx(p, (x - 0.6, x + 0.6), (6.9, 7.8), (47.2, 48.4), MET, 0.03)
    # three umbrella tables
    for x, col in ((70, RED), (76, ORG), (82, RED)):
        vc(p, x, 0.3, 4.9, 58.5, 0.25, DGR, 6)
        vc(p, x, 4.2, 5.2, 58.5, 2.5, col, 10, top_r=0.5)
        vc(p, x, 5.2, 5.5, 58.5, 0.2, DGR, 6)
        vc(p, x, 2.2, 2.5, 58.5, 1.5, WHT, 10, jit=0.03)
        for sx in (-1, 1):
            bx(p, (x + sx * 1.9 - 0.5, x + sx * 1.9 + 0.5), (1.0, 1.3), (58.0, 59.0), NAVY, 0.03)
            bx(p, (x + sx * 1.9 - 0.5, x + sx * 1.9 + 0.5), (1.3, 2.4), (58.0 + (0.8 if sx else 0), 58.2 + (0.8 if sx else 0)), NAVY, 0.03)
            bx(p, (x + sx * 1.9 - 0.15, x + sx * 1.9 + 0.15), (0.3, 1.0), (58.4, 58.6), DGR, 0.02)
    # planters
    for x in (69.8, 82.2):
        bx(p, (x - 0.9, x + 0.9), (0.3, 1.3), (54.2, 55.0), (150, 90, 60), 0.03)
        ball(p, (x, 1.6, 54.6), 0.8, (70, 150, 80), subdiv=1)
    # rocket sign on a pole
    vc(p, 84.5, 0.3, 8.8, 46, 0.3, DGR, 6)
    vc(p, 84.5, 8.8, 13.9, 46, 1.2, WHT, 10, jit=0.03)
    vc(p, 84.5, 13.9, 16.0, 46, 1.2, RED, 10, top_r=0.1)
    bx(p, (83.9, 85.1), (11.0, 12.2), (47.0, 47.25), NAVY, 0.02)
    for dx in (-1, 1):
        fin(p, 84.5, 46, dx, 0, [(1.1, 8.8), (1.1, 10.6), (2.3, 8.8)], 0.3, RED)
    vc(p, 84.5, 8.4, 8.8, 46, 0.8, ORG, 8, top_r=1.0)


# ---- 11. Lander ----------------------------------------------------------------------------------------------------------
def build_Lander(p):
    Z = -24
    # legs with foot pads
    for sx in (-1, 1):
        for sz in (-1, 1):
            px, pz = sx * 6.0, Z + sz * 6.0
            vc(p, px, 0.3, 0.8, pz, 1.4, DGR, 10, top_r=1.0)
            bar(p, (sx * 3.2, 6.6, Z + sz * 3.2), (px, 0.9, pz), 0.55, OFW, 0.03)
            bar(p, (sx * 4.2, 5.9, Z + sz * 1.0), (sx * 5.4, 2.8, Z + sz * 4.6), 0.3, MET, 0.03)
    # descent stage (gold foil)
    vc(p, 0, 5.7, 8.7, Z, 4.7, GLD, 8, jit=0.07)
    vc(p, 0, 6.5, 7.0, Z, 4.85, OFW, 8, jit=0.03)
    vc(p, 0, 4.7, 5.7, Z, 1.3, DGR, 8, top_r=0.5)
    # ascent stage
    vc(p, 0, 8.7, 13.3, Z, 3.0, WHT, 6, top_r=2.4, jit=0.04)
    for sx in (-1, 1):
        bx(p, (sx * 1.5 - 0.65, sx * 1.5 + 0.65), (10.4, 12.0), (Z + 2.2, Z + 2.55), GLSD, 0.03)
        ball(p, (sx * 3.9, 10.6, Z), 1.5, GLD, subdiv=1, jit=0.07)
        bx(p, (sx * 3.9 - 0.3, sx * 3.9 + 0.3), (9.0, 9.4), (Z - 0.3, Z + 0.3), DGR, 0.02)
        bx(p, (sx * 2.6 - 0.25, sx * 2.6 + 0.25), (9.4, 9.9), (Z + 1.6 - 0.25, Z + 1.6 + 0.25), DGR, 0.02)
    vc(p, 0, 13.3, 13.7, Z, 1.2, DGR, 8)
    dish(p, (0, 14.6, Z), 1.4, 0.5, WHT, tilt=55, face=1, feed=False, verts=8)
    vc(p, 0, 13.7, 14.6, Z, 0.15, DGR, 6)
    vc(p, 0, 14.6, 15.9, Z, 0.12, DGR, 6)
    ball(p, (0, 15.9, Z), 0.3, RED, subdiv=1, jit=0.02)
    # thrusters
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (sx * 2.2 - 0.3, sx * 2.2 + 0.3), (8.7, 9.2), (Z + sz * 2.2 - 0.3, Z + sz * 2.2 + 0.3), DGR, 0.02)


# ---- 12. Dome ------------------------------------------------------------------------------------------------------------
def build_Dome(p):
    CX = -40
    vc(p, CX, 0.3, 7.5, 0, 7.0, WHT, 16, jit=0.03)
    vc(p, CX, 0.3, 1.0, 0, 7.2, OFW, 16, jit=0.03)
    vc(p, CX, 6.8, 7.5, 0, 7.15, NAVY, 16, jit=0.02)
    dome(p, CX, 7.5, 0, 7.0, 7.0, OFW, segs=16, rings=5, jit=0.05)
    # slit toward the walkway with the telescope sticking out
    az = math.radians(55)
    ux, uz = math.cos(az), math.sin(az)
    prev = None
    for i in range(6):
        ph = math.radians(8 + i * 14)
        pt = (CX + ux * 7.08 * math.cos(ph), 7.5 + 7.08 * math.sin(ph), uz * 7.08 * math.cos(ph))
        if prev:
            bar(p, prev, pt, 1.7, NAVY, 0.02)
        prev = pt
    ph = math.radians(38)
    d = (ux * math.cos(ph), math.sin(ph), uz * math.cos(ph))
    c0 = (CX + d[0] * 2.0, 7.5 + d[1] * 2.0 + 0.5, d[2] * 2.0)
    c1 = (CX + d[0] * 9.6, 7.5 + d[1] * 9.6 + 0.5, d[2] * 9.6)
    bar(p, c0, c1, 1.6, WHT, 0.03)
    bar(p, c1, (c1[0] + d[0] * 0.5, c1[1] + d[1] * 0.5, c1[2] + d[2] * 0.5), 1.0, DGR, 0.02)
    bar(p, (c1[0] - d[0] * 3, c1[1] - d[1] * 3, c1[2] - d[2] * 3), (c1[0] - d[0] * 2.4, c1[1] - d[1] * 2.4, c1[2] - d[2] * 2.4), 2.0, GLD, 0.03)
    vc(p, CX + ux * 0.0, 13.5, 14.5, 0, 0.5, DGR, 6)
    # drum windows
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        if abs(math.degrees(a) - 90) < 30:
            continue
        bx(p, (CX + 6.95 * math.cos(a) - 0.7, CX + 6.95 * math.cos(a) + 0.7), (3.8, 5.6), (6.95 * math.sin(a) - 0.2, 6.95 * math.sin(a) + 0.2), GLSD, 0.03,
           rot=(0, 90 - math.degrees(a), 0))
    # porch and door
    bx(p, (CX - 1.3, CX + 1.3), (0.3, 4.2), (6.75, 7.05), NAVY, 0.03)
    bx(p, (CX - 2.0, CX + 2.0), (0.3, 0.9), (6.0, 8.6), CONL, 0.03)
    bx(p, (CX - 2.0, CX + 2.0), (0.9, 1.5), (6.0, 7.3), CON, 0.03)
    bx(p, (CX - 1.7, CX + 1.7), (4.2, 4.6), (6.7, 7.5), RED, 0.03)
    # annex
    bx(p, (-34, -30), (0.3, 4.7), (-3, 3), WHT)
    bx(p, (-34.3, -29.7), (4.7, 5.2), (-3.3, 3.3), NAVY, 0.03)
    bx(p, (-30.2, -30.0), (1.8, 3.8), (-1.3, 1.3), GLSD, 0.03)
    bx(p, (-33.2, -30.8), (0.3, 3.4), (2.9, 3.1), DGR, 0.03)
    for k in range(3):
        vc(p, -32, 5.2 + k * 1.1, 5.2 + (k + 1) * 1.1, 0, 0.25, RED if k % 2 == 0 else WHT, 6, jit=0.02)
    ball(p, (-32, 8.5, 0), 0.3, RED, subdiv=1, jit=0.02)


# ---- 13. Solar -----------------------------------------------------------------------------------------------------------
def build_Solar(p):
    bx(p, (68.8, 87.2), (0.2, 0.36), (22, 38.2), GRAV, 0.03)
    n = math.cos(math.radians(30)), math.sin(math.radians(30))
    for z0 in (24.2, 30.0, 35.8):
        for x in (70, 74, 78, 82, 86):
            bx(p, (x - 0.2, x + 0.2), (0.3, 4.0), (z0 - 1.8, z0 - 1.4), MET, 0.03)
            bx(p, (x - 0.2, x + 0.2), (0.3, 1.8), (z0 + 1.6, z0 + 2.0), MET, 0.03)
        dk.box(p, (78, 3.2, z0), (18, 0.3, 4.8), SOL, rot=(30, 0, 0), jitter=0.05)
        dk.box(p, (78, 3.2, z0), (18.3, 0.2, 5.0), OFW, rot=(30, 0, 0), jitter=0.02)
        dk.box(p, (78, 3.2 + 0.2 * n[0], z0 + 0.2 * n[1]), (17.6, 0.12, 4.5), SOL, rot=(30, 0, 0), jitter=0.05)
        for i in range(1, 6):
            dk.box(p, (69 + i * 3.0, 3.2 + 0.3 * n[0], z0 + 0.3 * n[1]), (0.12, 0.08, 4.5), SOLL, rot=(30, 0, 0), jitter=0.02)
        dk.box(p, (78, 3.2 + 0.3 * n[0], z0 + 0.3 * n[1]), (17.6, 0.08, 0.12), SOLL, rot=(30, 0, 0), jitter=0.02)
    # battery box
    bx(p, (84, 87), (0.3, 3.3), (18, 21), OFW)
    bx(p, (83.8, 87.2), (3.3, 3.6), (17.8, 21.2), DGR, 0.03)
    for k in range(4):
        bx(p, (84.4 + k * 0.7, 84.7 + k * 0.7), (0.8, 2.6), (21.0, 21.15), DGR, 0.02)
    bx(p, (84, 87), (3.0, 3.3), (21.0, 21.1), YEL, 0.02)
    bx(p, (84.2, 84.6), (0.3, 0.7), (21.0, 23.0), BLK, 0.02)
    # power hut
    bx(p, (69, 72), (0.2, 2.2), (18.3, 20.7), YEL)
    bx(p, (68.8, 72.2), (2.2, 2.6), (18.1, 20.9), NAVY, 0.03)
    bx(p, (69.6, 71.4), (0.2, 1.8), (20.7, 20.85), DGR, 0.03)
    bx(p, (72.0, 72.15), (0.9, 1.7), (19.2, 19.8), GLSD, 0.03)
    bx(p, (72.2, 84), (0.2, 0.34), (19.0, 19.5), BLK, 0.02)                             # cable run hut to battery


# ---- 14. Hangar ----------------------------------------------------------------------------------------------------------
def build_Hangar(p):
    bx(p, (-36, -8), (0.3, 22.3), (-58.5, -41.5), WHT)
    bx(p, (-36.2, -7.8), (20.1, 21.3), (-41.7, -41.5), NAVY, 0.03)
    bx(p, (-36.5, -7.5), (22.3, 23.3), (-59, -41), NAVY, 0.03)
    for x in range(-34, -9, 4):
        bx(p, (x - 0.35, x + 0.35), (23.3, 23.7), (-59, -41), DGR, 0.03)
    for x in (-34, -30, -26, -18, -14, -10):
        bx(p, (x - 0.3, x + 0.3), (0.3, 20.1), (-41.5, -41.2), OFW, 0.03)
    bx(p, (-36.5, -7.5), (0.3, 0.45), (-41.2, -39.2), CONL, 0.03)
    # big door with hazard frame
    bx(p, (-28, -16), (0.3, 18.3), (-41.4, -40.6), DGR)
    for y in range(2, 18, 2):
        bx(p, (-28, -16), (y, y + 0.25), (-40.6, -40.45), MET, 0.03)
    for i in range(12):
        bx(p, (-28.6 + i * 1.04, -27.56 + i * 1.04), (18.3, 19.3), (-41.5, -40.4), YEL if i % 2 == 0 else BLK, 0.02)
    for x in (-28.6, -16.0):
        bx(p, (x, x + 0.6), (0.3, 18.3), (-41.5, -40.4), YEL, 0.03)
    # rocket mural left of the door
    bx(p, (-34.8, -29.6), (3.0, 19.6), (-41.2, -41.0), NAVY, 0.03)
    bx(p, (-33.0, -31.4), (5.8, 15.0), (-41.0, -40.8), WHT, 0.02)
    side(p, [(-33.0, 15.0), (-31.4, 15.0), (-32.2, 18.4)], -40.95, -40.8, RED, 0.02)
    side(p, [(-33.0, 5.8), (-33.0, 9.5), (-34.2, 5.8)], -40.95, -40.8, RED, 0.02)
    side(p, [(-31.4, 5.8), (-31.4, 9.5), (-30.2, 5.8)], -40.95, -40.8, RED, 0.02)
    bx(p, (-32.9, -31.5), (10.5, 11.6), (-40.8, -40.7), GLS, 0.02)
    # emblem right of the door
    zc(p, -11.8, 14.0, -41.5, -41.1, 2.5, NAVY, 14, 0.02)
    star(p, (-11.8, 14.0, -41.0), 'xy', 1.9, 0.8, 0.2, YEL, 5)
    # office with flat roof
    bx(p, (-16.5, -8.5), (0.3, 6.3), (-42.8, -39.2), OFW)
    bx(p, (-16.8, -8.2), (6.3, 6.8), (-43.1, -38.9), NAVY, 0.03)
    bx(p, (-15.6, -12.4), (2.2, 4.8), (-42.8, -42.65), GLSD, 0.03)
    bx(p, (-11.6, -9.4), (0.3, 4.3), (-42.8, -42.65), NAVY, 0.03)
    # high windows on the sides, roof vents, flag
    for z in (-56, -52.5, -49, -45.5):
        bx(p, (-36.15, -36.0), (16, 19), (z - 1.2, z + 1.2), GLSD, 0.03)
        bx(p, (-8.0, -7.85), (16, 19), (z - 1.2, z + 1.2), GLSD, 0.03)
    for x in (-30, -14):
        bx(p, (x - 2, x + 2), (23.7, 24.6), (-52, -48), MET, 0.03)
        bx(p, (x - 2.2, x + 2.2), (24.6, 25.0), (-52.2, -47.8), DGR, 0.03)
    vc(p, -10, 23.3, 30.7, -54, 0.25, OFW, 6)
    bx(p, (-10, -7.6), (28.8, 30.4), (-54.1, -53.9), RED, 0.02)
    ball(p, (-10, 30.7, -54), 0.35, YEL, subdiv=1, jit=0.02)
    # corner floodlights
    for x in (-35.5, -8.5):
        bx(p, (x - 0.4, x + 0.4), (18.5, 19.3), (-41.9, -41.5), YEL, 0.02)


# ---- 15. Capsule ---------------------------------------------------------------------------------------------------------
def build_Capsule(p):
    X, Z = 25, -18
    # parachute lying on the grass: 12 gores, alternating white and orange, closed wedges
    cx, cz, rx, rz = 16, -21, 7.0, 5.5
    for par, col in ((0, WHT), (1, ORG)):
        pts, faces = [], []
        for k in range(par, 12, 2):
            a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
            b = len(pts)
            T, B = (cx, 0.58, cz), (cx, 0.3, cz)
            r0t, r1t = (cx + rx * math.cos(a0), 0.4, cz + rz * math.sin(a0)), (cx + rx * math.cos(a1), 0.4, cz + rz * math.sin(a1))
            r0b, r1b = (r0t[0], 0.3, r0t[2]), (r1t[0], 0.3, r1t[2])
            pts += [T, B, r0t, r1t, r0b, r1b]
            faces += [(b, b + 2, b + 3), (b + 1, b + 5, b + 4), (b + 2, b + 4, b + 5, b + 3), (b, b + 1, b + 4, b + 2), (b, b + 3, b + 5, b + 1)]
        dk.poly(p, (0, 0, 0), pts, faces, col, 0.03)
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6 + 0.2
        bar(p, (cx + rx * 0.95 * math.cos(a), 0.34, cz + rz * 0.95 * math.sin(a)), (X - 1.2, 1.4, Z + 0.2 * (k - 3)), 0.14, DGR, 0.02)
    # capsule
    vc(p, X, 0.3, 1.0, Z, 3.2, (70, 62, 62), 14, top_r=2.9, jit=0.06)
    lathe(p, (X, 0, Z), [(1.0, 2.9), (2.0, 2.8), (5.0, 1.5), (5.6, 1.3)], 14, WHT)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.5
        bar(p, (X + 2.86 * math.cos(a), 1.5, Z + 2.86 * math.sin(a)), (X + 1.84 * math.cos(a), 4.5, Z + 1.84 * math.sin(a)), 0.5, (84, 70, 64), 0.05)
    for a_deg in (60, 150):
        a = math.radians(a_deg)
        r = 2.35
        bx(p, (X + r * math.cos(a) - 0.5, X + r * math.cos(a) + 0.5), (3.0, 4.3), (Z + r * math.sin(a) - 0.2, Z + r * math.sin(a) + 0.2), NAVY, 0.03,
           rot=(0, 90 - a_deg, 0))
    vc(p, X, 5.6, 6.4, Z, 1.3, DGR, 10, top_r=1.0)
    vc(p, X, 4.9, 5.3, Z, 1.6, GLD, 14, jit=0.04)
    vc(p, X, 1.0, 1.45, Z, 2.95, (60, 52, 52), 14, jit=0.03)
    ah = math.radians(105)
    bx(p, (X + 2.2 * math.cos(ah) - 0.6, X + 2.2 * math.cos(ah) + 0.6), (2.4, 3.8), (Z + 2.2 * math.sin(ah) - 0.15, Z + 2.2 * math.sin(ah) + 0.15), OFW, 0.03,
       rot=(0, 90 - 105, 0))
    vc(p, 28.2, 0.3, 3.8, -15.6, 0.1, DGR, 6, jit=0.02)
    bx(p, (28.2, 29.4), (2.8, 3.8), (-15.7, -15.5), RED, 0.02)
    vc(p, X, 6.4, 8.0, Z, 0.15, DGR, 6)
    ball(p, (X, 8.0, Z), 0.3, RED, subdiv=1, jit=0.02)
    for k in range(4):
        a = k * math.pi / 2 + 0.78
        bx(p, (X + 1.9 * math.cos(a) - 0.3, X + 1.9 * math.cos(a) + 0.3), (4.7, 5.2), (Z + 1.9 * math.sin(a) - 0.3, Z + 1.9 * math.sin(a) + 0.3), DGR, 0.02)


# ---- 16. Centrifuge ------------------------------------------------------------------------------------------------------
def build_Centrifuge(p):
    X, Z = 45, 25
    vc(p, X, 0.3, 0.58, Z, 13.4, CON, 20)
    bx(p, (32, 58), (0.3, 0.58), (12, 38), CON, 0.03)
    annulus(p, X, Z, 11.0, 12.0, 0.58, 0.64, YEL, 20)
    annulus(p, X, Z, 5.2, 5.7, 0.58, 0.64, DGR, 16)
    for k in range(12):
        a = k * math.pi / 6
        bx(p, (X + 12.3 * math.cos(a) - 0.2, X + 12.3 * math.cos(a) + 0.2), (0.58, 1.7), (Z + 12.3 * math.sin(a) - 0.2, Z + 12.3 * math.sin(a) + 0.2), YEL, 0.02)
    vc(p, X, 0.58, 3.2, Z, 4.5, DGR, 12)
    vc(p, X, 3.2, 17.2, Z, 2.3, WHT, 12, jit=0.03)
    for y in (6.0, 9.5, 13.0):
        vc(p, X, y, y + 0.7, Z, 2.4, NAVY, 12, jit=0.02)
    vc(p, X, 17.2, 19.6, Z, 3.2, NAVY, 12)
    vc(p, X, 19.6, 21.0, Z, 1.6, DGR, 10)
    # the arm: orange beams with truss diagonals
    bx(p, (33, 57), (19.6, 20.1), (24.1, 25.9), ORG, 0.03)
    bx(p, (33, 57), (20.5, 21.0), (24.1, 25.9), ORG, 0.03)
    for i in range(8):
        for z in (24.2, 25.8):
            x0 = 33.2 + i * 3.0
            bar(p, (x0, 19.9 if i % 2 == 0 else 20.7, z), (x0 + 3.0, 20.7 if i % 2 == 0 else 19.9, z), 0.25, ORG, 0.03)
    for x in (33.4, 56.6):
        bx(p, (x - 0.4, x + 0.4), (19.6, 21.0), (24.0, 26.0), YEL, 0.02)
    # gondola pod
    for z in (23.9, 26.1):
        bar(p, (36.0, 19.6, z), (36.0, 18.9, z), 0.3, DGR, 0.03)
    xc(p, 33.6, 37.8, 17.5, Z, 1.7, WHT, 12, jit=0.03)
    ball(p, (33.7, 17.5, Z), 1.7, WHT, scale=(0.6, 1, 1), subdiv=1)
    ball(p, (37.7, 17.5, Z), 1.7, WHT, scale=(0.6, 1, 1), subdiv=1)
    xc(p, 34.6, 36.4, 17.5, Z, 1.76, ORG, 12, jit=0.02)
    bx(p, (33.4, 34.4), (17.7, 18.8), (26.5, 26.75), GLSD, 0.03)
    bx(p, (33.4, 34.4), (17.7, 18.8), (23.25, 23.5), GLSD, 0.03)
    # counterweight
    for z in (23.9, 26.1):
        bar(p, (55.4, 19.6, z), (55.4, 19.0, z), 0.3, DGR, 0.03)
    bx(p, (53.7, 57.1), (16.3, 19.7), (23.3, 26.7), RED, 0.03)
    for y in (17.0, 18.2):
        bx(p, (53.5, 57.3), (y, y + 0.35), (23.1, 26.9), DGR, 0.03)
    bx(p, (54.4, 56.4), (16.6, 17.0), (26.7, 26.85), YEL, 0.02)
    # control booth
    bx(p, (34, 38), (0.58, 3.6), (14, 18), WHT)
    bx(p, (33.7, 38.3), (3.6, 4.0), (13.7, 18.3), NAVY, 0.03)
    bx(p, (34.5, 37.5), (1.6, 3.0), (18.0, 18.15), GLSD, 0.03)
    bx(p, (36.8, 37.8), (0.58, 2.4), (18.0, 18.15), DGR, 0.03)


# ---- 17. Habitat ---------------------------------------------------------------------------------------------------------
def build_Habitat(p):
    bx(p, (66, 90), (0.3, 0.58), (-10, 14), RST, 0.05)
    for x, z, w, d, c in ((70, 10, 8, 6, RSTD), (86, 8, 6, 8, RSTL), (68, -6, 5, 8, RSTL), (84, -8, 8, 3, RSTD)):
        bx(p, (x - w / 2, x + w / 2), (0.58, 0.62), (z - d / 2, z + d / 2), c, 0.03)
    # two domes with base rings, panel rings and windows
    for cx, rr, hh in ((72, 5.5, 7.3), (85, 4.5, 6.5)):
        vc(p, cx, 0.58, 1.2, 2, rr + 0.25, OFW, 12, jit=0.03)
        dome(p, cx, 0.58, 2, rr, hh, WHT, segs=12, rings=4, jit=0.04)
        for fr in (0.55,):
            h = hh * fr
            r = rr * math.cos(math.asin(fr)) + 0.06
            vc(p, cx, 0.58 + h - 0.15, 0.58 + h + 0.15, 2, r, OFW, 12, jit=0.03)
        vc(p, cx, 1.0, 1.4, 2, rr + 0.1, ORG, 12, jit=0.03)
        for k in range(4):
            a = math.radians(40 + k * 33)
            r = rr * 0.9
            yy = 0.58 + hh * 0.2 + 0.3
            bx(p, (cx + r * math.cos(a) - 0.5, cx + r * math.cos(a) + 0.5), (yy, yy + 1.1), (2 + r * math.sin(a) - 0.2, 2 + r * math.sin(a) + 0.2), GLSD, 0.03,
               rot=(0, 90 - math.degrees(a), 0))
    # comm mast with a small dish on the big dome
    vc(p, 72, 7.88, 11.6, 2, 0.2, DGR, 6)
    dish(p, (72, 11.3, 2), 1.0, 0.4, WHT, tilt=50, face=1, feed=False, verts=8)
    ball(p, (72, 12.1, 2), 0.2, RED, subdiv=1, jit=0.02)
    # tunnel with ribs, corridor and airlock
    xc(p, 75.8, 81.8, 2.4, 2, 1.8, OFW, 10)
    for x in (76.6, 78.8, 81.0):
        xc(p, x - 0.2, x + 0.2, 2.4, 2, 1.95, DGR, 10, jit=0.02)
    zc(p, 78.8, 2.4, -3.0, 0.4, 1.3, OFW, 8)
    bx(p, (76.5, 80.5), (0.58, 4.7), (-7, -3), WHT)
    bx(p, (76.2, 80.8), (4.7, 5.1), (-7.3, -2.7), NAVY, 0.03)
    xc(p, 80.5, 80.75, 2.4, -5, 1.2, NAVY, 10, 0.02)
    xc(p, 80.75, 80.95, 2.4, -5, 0.8, OFW, 10, 0.02)
    bx(p, (80.9, 81.1), (2.2, 2.6), (-5.5, -4.5), DGR, 0.02)
    bx(p, (79.6, 80.4), (5.1, 5.5), (-5.4, -4.6), RED, 0.03)
    # fuel tanks with domed tops and straps, pipes to the airlock
    for x, z, col in ((71.5, -4, WHT), (74, -4.4, ORG)):
        vc(p, x, 0.58, 3.4, z, 1.0, col, 8, jit=0.03)
        ball(p, (x, 3.4, z), 1.0, col, scale=(1, 0.7, 1), subdiv=1, jit=0.03)
        for y in (1.2, 2.5):
            vc(p, x, y, y + 0.25, z, 1.06, NAVY, 8, jit=0.02)
    bar(p, (74.8, 2.0, -4.4), (76.5, 2.0, -4.8), 0.3, DGR, 0.03)
    bar(p, (72.4, 3.4, -4.1), (73.2, 3.4, -4.3), 0.25, DGR, 0.03)
    # boulders
    for c, r, sc, col in (((68, 1, 9), 1.3, (1.0, 0.7, 0.85), RSTD), ((88, 1.1, -6), 1.5, (1, 0.67, 0.87), RSTD),
                          ((82, 0.9, 10), 1.0, (1, 0.7, 1), RSTL), ((86.5, 0.9, -8.5), 0.9, (1, 0.8, 1), RSTL), ((67.8, 0.8, 0), 0.8, (1, 0.8, 1), RSTL)):
        ball(p, c, r, col, scale=sc, subdiv=1, jit=0.08)
    # solar panel on a stand and a flag
    dk.box(p, (87, 1.6, 11), (4, 0.2, 3), SOL, rot=(30, 0, 0), jitter=0.04)
    bx(p, (86.8, 87.2), (0.58, 1.2), (11.9, 12.3), DGR, 0.02)
    bx(p, (86.8, 87.2), (0.58, 2.4), (9.7, 10.1), DGR, 0.02)
    vc(p, 76, 0.58, 4.0, 10, 0.1, DGR, 6, jit=0.02)
    bx(p, (76, 77.5), (3.0, 4.0), (9.95, 10.05), RED, 0.02)


# ---- 18. Crater ----------------------------------------------------------------------------------------------------------
def build_Crater(p):
    X, Z = 85, -48
    bx(p, (78, 92), (0.3, 0.5), (-55, -41), MOON, 0.04)
    for x, z, w, d, c in ((81, -52, 6, 4, MOOND), (90, -44, 4, 4, MOOND), (88, -53.5, 5, 3, (190, 192, 198))):
        bx(p, (x - w / 2, x + w / 2), (0.5, 0.54), (z - d / 2, z + d / 2), c, 0.03)
    vc(p, X, 0.5, 0.6, Z, 4.2, MOOND, 16, jit=0.04)
    annulus(p, X, Z, 3.4, 4.6, 0.5, 1.1, MOON, 16, 0.05)
    annulus(p, X, Z, 4.4, 6.2, 0.5, 0.78, (190, 192, 198), 16, 0.05)
    for cx, cz, rr in ((80.5, -52.5, 1.2), (90.5, -44.5, 1.0), (82.5, -43.8, 0.8)):
        vc(p, cx, 0.5, 0.6, cz, rr, MOOND, 8, jit=0.03)
        annulus(p, cx, cz, rr, rr + 0.45, 0.5, 0.75, (190, 192, 198), 8, 0.04)
    for c, r, sc, col in (((80, 1.4, -44), 1.5, (1.13, 0.87, 1.0), MOON), ((90, 1.6, -52), 1.9, (1.0, 0.79, 0.89), MOOND),
                          ((81.5, 1.2, -53), 1.2, (1.0, 0.75, 1.0), MOOND), ((88.5, 1.0, -43.5), 1.0, (1.0, 0.8, 1.0), MOON)):
        ball(p, c, r, col, scale=sc, subdiv=1, jit=0.09)
    ball(p, (91, 2.9, -52.5), 0.8, MOON, scale=(1, 0.8, 1), subdiv=1, jit=0.09)
    # footprints leading to the flag
    for i in range(6):
        for s in (-0.4, 0.4):
            bx(p, (82.5 + i * 0.5 - 0.3, 82.5 + i * 0.5 + 0.3), (0.6, 0.64), (-45.5 - i * 0.6 + s - 0.15, -45.5 - i * 0.6 + s + 0.15), (96, 98, 108), 0.02)
    # flag
    vc(p, X, 0.5, 15.7, Z, 0.2, WHT, 8)
    bx(p, (85.1, 88.2), (12.9, 15.1), (-48.1, -47.9), ORG, 0.03)
    star(p, (86.65, 14.0, -47.85), 'xy', 0.8, 0.35, 0.12, WHT, 5)
    ball(p, (X, 16.0, Z), 0.45, GLD, subdiv=1, jit=0.03)


# ---- 19. Shuttle ---------------------------------------------------------------------------------------------------------
def build_Shuttle(p):
    Z = -47
    bx(p, (-74, -50), (0.3, 1.9), (-52, -42), CON)
    bx(p, (-73.6, -50.4), (1.7, 1.95), (-51.6, -42.4), COND, 0.03)
    for x in (-67, -56):
        vc(p, x, 1.9, 3.6, Z, 1.2, DGR, 8)
        bx(p, (x - 1.5, x + 1.5), (3.3, 3.8), (Z - 1.4, Z + 1.4), DGR, 0.03)
    bx(p, (-74, -50), (0.3, 0.5), (-52, -51.6), YEL, 0.02)
    bx(p, (-74, -50), (0.3, 0.5), (-42.4, -42), YEL, 0.02)
    # fuselage and nose
    lathe(p, (0, 6.6, Z), [(-76, 2.5), (-74.5, 3.0), (-55, 3.0)], 12, WHT, axis='x', jit=0.03)
    lathe(p, (0, 6.6, Z), [(-55, 3.0), (-53, 2.8), (-51, 2.2), (-49, 1.4), (-47.5, 0.7), (-46.5, 0.0)], 12, DGR, axis='x', jit=0.03)
    bx(p, (-56.5, -52.3), (8.9, 9.5), (Z - 1.5, Z + 1.5), NAVY, 0.03)                    # cockpit windows
    bx(p, (-69, -57.5), (9.5, 9.65), (Z - 0.2, Z + 0.2), DGR, 0.02)                      # payload bay seam
    bx(p, (-69, -57.5), (9.45, 9.6), (Z - 2.0, Z - 1.8), DGR, 0.02)
    bx(p, (-69, -57.5), (9.45, 9.6), (Z + 1.8, Z + 2.0), DGR, 0.02)
    bx(p, (-68, -64), (5.4, 6.0), (Z - 3.05, Z - 2.95), NAVY, 0.02)
    # delta wings
    for s in (1, -1):
        slab(p, [(-58, Z + s * 2.6), (-71, Z + s * 13), (-73, Z + s * 13), (-73, Z + s * 2.6)], 5.5, 6.0, WHT, 0.03)
        slab(p, [(-58, Z + s * 2.6), (-71, Z + s * 13), (-72, Z + s * 13), (-60.5, Z + s * 2.6)], 5.2, 5.5, DGR, 0.03)
        slab(p, [(-71.2, Z + s * 13), (-73, Z + s * 13), (-73, Z + s * 2.6), (-71.6, Z + s * 2.6)], 5.45, 6.1, DGR, 0.03)
    for s in (1, -1):
        slab(p, [(-58, Z + s * 2.6), (-71, Z + s * 13), (-71.9, Z + s * 12.2), (-59.6, Z + s * 2.6)], 5.5, 6.05, BLK, 0.03)
        bx(p, (-70, -57), (6.3, 6.8), (Z + s * 3.05 - 0.06, Z + s * 3.05 + 0.06), NAVY, 0.02)
        bx(p, (-63, -60), (6.8, 7.2), (Z + s * 3.05 - 0.06, Z + s * 3.05 + 0.06), RED, 0.02)
    # tail fin and OMS pods
    side(p, [(-76, 9.0), (-69, 9.0), (-73.4, 16.0), (-76.0, 16.0)], Z - 0.45, Z + 0.45, WHT, 0.03)
    side(p, [(-76.05, 11.0), (-74.4, 11.0), (-75.4, 14.0), (-76.05, 14.0)], Z - 0.5, Z + 0.5, NAVY, 0.02)
    for s in (-1, 1):
        bx(p, (-76, -71.5), (8.8, 10.0), (Z + s * 1.6 - 0.7, Z + s * 1.6 + 0.7), OFW, 0.03)
    # main engines
    for y, z in ((7.4, Z), (5.4, Z - 1.8), (5.4, Z + 1.8)):
        xc(p, -78.8, -76, y, z, 1.2, DGR, 8, top_r=0.55)
        xc(p, -78.9, -78.6, y, z, 1.0, BLK, 8, 0.02)


# ---- 20. Station ---------------------------------------------------------------------------------------------------------
def build_Station(p):
    X, Z = 14, 24
    vc(p, X, 0.3, 1.7, Z, 5.0, CON, 14)
    annulus(p, X, Z, 3.2, 3.8, 1.7, 1.78, YEL, 14)
    vc(p, X, 1.7, 19.7, Z, 1.5, WHT, 10, top_r=1.2, jit=0.03)
    for y in (5.0, 9.5, 14.0):
        vc(p, X, y, y + 0.7, Z, 1.65, NAVY, 10, jit=0.02)
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.4
        bar(p, (X + 1.2 * math.cos(a), 12.5, Z + 1.2 * math.sin(a)), (X + 3.8 * math.cos(a), 1.7, Z + 3.8 * math.sin(a)), 0.35, MET, 0.03)
    # node, main module, cross module
    ball(p, (X, 21, Z), 2.5, OFW, subdiv=1, jit=0.03)
    xc(p, 2.5, 25.5, 21, Z, 2.0, WHT, 12, jit=0.03)
    for x in (6.0, 9.5, 18.5, 22.0):
        xc(p, x - 0.3, x + 0.3, 21, Z, 2.1, NAVY, 12, jit=0.02)
    xc(p, 1.0, 2.5, 21, Z, 2.0, OFW, 12, top_r=1.2)
    xc(p, 25.5, 27.0, 21, Z, 1.2, OFW, 12, top_r=2.0)
    xc(p, 27.0, 29.6, 21, Z, 1.2, WHT, 12, top_r=0.6)
    zc(p, X, 21, 17, 31, 1.8, GLD, 12, jit=0.07)
    for z in (17.3, 30.7):
        zc(p, X, 21, z - 0.4, z + 0.4, 1.9, DGR, 12, jit=0.02)
    # truss and four solar wings
    bx(p, (-2, 30), (23.75, 24.65), (23.55, 24.45), DGR, 0.03)
    bx(p, (X - 0.5, X + 0.5), (23.3, 23.75), (Z - 0.5, Z + 0.5), MET, 0.03)
    for x0, x1 in ((1, 6), (7, 12), (16, 21), (22, 27)):
        bx(p, (x0, x1), (24.05, 24.35), (18, 30), SOL, 0.04)
        for i in range(1, 5):
            bx(p, (x0 + i * (x1 - x0) / 5 - 0.05, x0 + i * (x1 - x0) / 5 + 0.05), (24.35, 24.42), (18, 30), SOLL, 0.02)
        bx(p, (x0, x1), (24.05, 24.4), (23.85, 24.15), WHT, 0.03)
    # dish, arm, radiator
    vc(p, 7.5, 22.8, 23.4, Z, 0.2, DGR, 6)
    dish(p, (7.5, 23.7, Z), 1.1, 0.4, WHT, tilt=55, face=1, feed=False, verts=8)
    bar(p, (19, 19.2, Z - 1), (22.5, 19.0, Z - 3), 0.4, ORG, 0.03)
    bar(p, (22.5, 19.0, Z - 3), (25.5, 20.0, Z - 4), 0.4, ORG, 0.03)
    for z in (18.6, 29.4):
        bx(p, (12.8, 15.2), (17.2, 20.0), (z - 0.1, z + 0.1), OFW, 0.03)


PARTS = [("Ground", build_Ground), ("Control", build_Control), ("Platform", build_Platform), ("Rocket", build_Rocket),
         ("Sign", build_Sign), ("Gantry", build_Gantry), ("Rover", build_Rover), ("Tanks", build_Tanks),
         ("Radar", build_Radar), ("Cafe", build_Cafe), ("Lander", build_Lander), ("Dome", build_Dome),
         ("Solar", build_Solar), ("Hangar", build_Hangar), ("Capsule", build_Capsule), ("Centrifuge", build_Centrifuge),
         ("Habitat", build_Habitat), ("Crater", build_Crater), ("Shuttle", build_Shuttle), ("Station", build_Station)]

# camera: azimuth, elevation, distance multiplier; reference Shiba: (x, z, facing, lift)
AZ = {"Control": 235}
ELEV = {"Tanks": 48, "Control": 24}
MULT = {"Ground": 1.6, "Rocket": 3.0, "Gantry": 3.0, "Control": 2.6, "Station": 2.8, "Hangar": 2.8, "Shuttle": 2.6, "Sign": 2.2}
SHIBA_AT = {"Ground": (-60, 22, 270, 0), "Control": (-62, 30, 0, 0), "Platform": (42, -36, 0, 0), "Rocket": (46, -30, 0, 0),
            "Sign": (-24, 60, 270, 0), "Gantry": (40, -38, 0, 0), "Rover": (-46, 52, 270, 0), "Tanks": (-36, -10, 270, 0),
            "Radar": (-74, 6, 270, 0), "Cafe": (76, 66, 270, 0), "Lander": (0, -10, 270, 0), "Dome": (-40, 14, 270, 0),
            "Solar": (78, 44, 270, 0), "Hangar": (-22, -34, 270, 0), "Capsule": (18, -8, 270, 0), "Centrifuge": (45, 44, 270, 0),
            "Habitat": (78, 22, 270, 0), "Crater": (85, -34, 270, 0), "Shuttle": (-62, -30, 270, 0), "Station": (14, 36, 270, 0)}


# ---- previews --------------------------------------------------------------------------------------------------------------------
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
        x, z, f, lift = SHIBA_AT[pid]
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 28), MULT.get(pid, 2.5), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 150, 38, 2.2, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.0, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_LaunchPad.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        os.remove(os.path.join(OUT, f))


main()
