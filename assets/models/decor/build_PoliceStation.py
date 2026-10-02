"""Final low-poly decor models for the theme PoliceStation (15 parts around the sixth Shiba, Police Shiba).

Usage: blender --background --factory-startup --python build_PoliceStation.py -- <outdir> [PartId ...]
Writes Decor_PoliceStation_<PartId>.fbx, preview_<PartId>.png and stage_PoliceStation.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "PoliceStation"))
ONLY = ARGS[1:]
KEY = "PoliceStation"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_PoliceStation.json"))

# ---- palette (shared by all 15 parts) -------------------------------------------------------------------------------
WHT = (232, 236, 244)    # painted white
OFF = (205, 210, 222)    # shaded white / light concrete
NAVY = (24, 40, 90)
BLU = (36, 90, 180)      # police blue
LBL = (86, 140, 214)
GLS = (118, 178, 228)    # glass
GLD_ = (58, 88, 138)     # dark glass
MET = (150, 156, 170)
DGR = (70, 74, 86)
BLK = (30, 30, 38)
ASP = (52, 54, 62)
CON = (168, 170, 180)
CONL = (196, 198, 208)
ROOF = (60, 64, 80)
ROOFL = (112, 116, 134)
YEL = (250, 205, 45)
RED = (205, 45, 55)
GLD = (255, 195, 40)
ORG = (245, 130, 35)
PNK = (245, 150, 190)
HPK = (240, 80, 150)
CRM = (250, 225, 190)
BRN = (120, 80, 50)
DBRN = (84, 56, 36)
ERT = (110, 90, 70)
RST = (150, 80, 50)
GRN = (62, 130, 72)


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


def window_z(p, x0, x1, y0, y1, z, d=0.16, mull=True, frame=NAVY, glass=GLS):
    """Window on a wall facing +z (wall plane at z, protrudes toward +z) or -z (negative d)."""
    zz = (z, z + d) if d > 0 else (z + d, z)
    bx(p, (x0 - 0.28, x1 + 0.28), (y0 - 0.28, y1 + 0.28), (zz[0], zz[0] + (zz[1] - zz[0]) * 0.7), frame, 0.02)
    bx(p, (x0, x1), (y0, y1), zz, glass, 0.05)
    if mull:
        xm = (x0 + x1) / 2
        bx(p, (xm - 0.1, xm + 0.1), (y0, y1), (zz[0], zz[1] + (0.04 if d > 0 else -0.04)), frame, 0.02)


def window_x(p, x, sgn, y0, y1, z0, z1, d=0.16, frame=NAVY, glass=GLS):
    """Window on a wall facing +x (sgn=1) or -x (sgn=-1), wall plane at x."""
    xx = (x, x + d * sgn)
    xx = (min(xx), max(xx))
    bx(p, xx, (y0 - 0.28, y1 + 0.28), (z0 - 0.28, z1 + 0.28), frame, 0.02)
    bx(p, (xx[0] + (0.05 if sgn > 0 else 0), xx[1] - (0 if sgn > 0 else 0.05)), (y0, y1), (z0, z1), glass, 0.05)


def fence_run(p, x0, x1, z0, z1, h, col=MET, post=0.32, step=3.0, rails=(0.12, 0.55, 0.95), t=0.18):
    """Chain-link style fence along x (z0==z1 wall) or z: posts every `step`, three rails."""
    along_x = abs(x1 - x0) >= abs(z1 - z0)
    length = (x1 - x0) if along_x else (z1 - z0)
    n = max(1, round(length / step))
    for i in range(n + 1):
        u = i / n
        cx = x0 + (x1 - x0) * u
        cz = z0 + (z1 - z0) * u
        bx(p, (cx - post / 2, cx + post / 2), (0, h), (cz - post / 2, cz + post / 2), col, 0.03)
    for f in rails:
        y = h * f
        if along_x:
            bx(p, (x0, x1), (y - t / 2, y + t / 2), (z0 - t / 2, z0 + t / 2), col, 0.03)
        else:
            bx(p, (x0 - t / 2, x0 + t / 2), (y - t / 2, y + t / 2), (z0, z1), col, 0.03)


def car(p, cx, cz, length=10.4, width=5.2, orient='z', body=WHT, stripe=BLU, lights=(RED, BLU), police=True,
        glass=GLD_, wheels=(1, 1, 1, 1), roof_drop=0.0, details=True, lift=0.0):
    """A small car, nose toward +v (v = z for orient 'z', x for orient 'x'). Wheels sit on y = 0.2 (the blueprint floats 0.2).
    wheels = (front-left, front-right, rear-left, rear-right) 1/0, roof_drop lowers the cabin (crushed wrecks)."""
    L, W = length / 2, width / 2

    def B(u0, u1, y0, y1, v0, v1, col, jit=0.03):
        """Box in car coordinates: u across the car, v along it."""
        y0, y1 = y0 + lift, y1 + lift
        if orient == 'z':
            return bx(p, (cx + u0, cx + u1), (y0, y1), (cz + v0, cz + v1), col, jit)
        return bx(p, (cx + v0, cx + v1), (y0, y1), (cz + u0, cz + u1), col, jit)

    def P(u, y, v):
        return (cx + u, y + lift, cz + v) if orient == 'z' else (cx + v, y + lift, cz + u)

    def wheel(su, sv):
        u0, u1 = (W - 0.75, W) if su > 0 else (-W, -W + 0.75)
        v = sv * (L - 2.1)
        hub = (u1, u1 + 0.03) if su > 0 else (u0 - 0.03, u0)
        if orient == 'z':
            xcyl(p, cx + u0, cx + u1, 1.15, cz + v, 0.95, BLK, verts=8, jit=0.02)
            if details:
                xcyl(p, cx + hub[0], cx + hub[1], 1.15, cz + v, 0.5, MET, verts=6, jit=0.02)
        else:
            zcyl(p, cx + v, 1.15, cz + u0, cz + u1, 0.95, BLK, verts=8, jit=0.02)
            if details:
                zcyl(p, cx + v, 1.15, cz + hub[0], cz + hub[1], 0.5, MET, verts=6, jit=0.02)
    k = 0
    for sv in (1, -1):
        for su in (-1, 1):
            if wheels[k]:
                wheel(su, sv)
            k += 1
    bw = W - 0.15
    B(-bw + 0.2, bw - 0.2, 0.5, 1.3, -L + 0.4, L - 0.4, BLK, 0.02)                      # underbody
    B(-bw, bw, 1.0, 2.8, -L, L, body, 0.03)                                             # body
    if stripe:
        B(-bw - 0.02, bw + 0.02, 1.55, 2.15, -L + 0.9, L - 0.9, stripe, 0.02)           # door stripe
    B(-bw + 0.05, bw - 0.05, 2.8, 3.0, L - 3.3, L - 0.2, BLK, 0.03)                     # hood
    B(-bw + 0.05, bw - 0.05, 2.8, 3.0, -L + 0.2, -L + 2.1, BLK, 0.03)                   # trunk
    top = 4.1 - roof_drop
    ub, ut = bw - 0.4, bw - 0.7
    v0, v1, t0, t1 = -2.9, 1.9, -2.2, 1.0
    pts = [P(-ub, 2.8, v0), P(ub, 2.8, v0), P(ub, 2.8, v1), P(-ub, 2.8, v1),
           P(-ut, top, t0), P(ut, top, t0), P(ut, top, t1), P(-ut, top, t1)]
    hexa(p, pts, glass, 0.03)                                                           # glass cabin, sloped screens
    B(-ut - 0.1, ut + 0.1, top, top + 0.25, t0 - 0.2, t1 + 0.2, body, 0.03)             # roof
    if police:
        B(-1.7, 0, top + 0.25, top + 0.55, -0.7 + (t0 + t1) / 2, 0.3 + (t0 + t1) / 2, lights[0], 0.02)
        B(0, 1.7, top + 0.25, top + 0.55, -0.7 + (t0 + t1) / 2, 0.3 + (t0 + t1) / 2, lights[1], 0.02)
    if details:
        for su in (-1, 1):
            B(su * (bw - 0.35) - 0.55, su * (bw - 0.35) + 0.55, 1.7, 2.3, L - 0.05, L + 0.02, YEL, 0.02)     # headlights
            B(su * (bw - 0.35) - 0.55, su * (bw - 0.35) + 0.55, 1.7, 2.3, -L - 0.02, -L + 0.05, RED, 0.02)   # tail lights
        B(-0.9, 0.9, 1.2, 1.8, L - 0.05, L + 0.02, BLK, 0.02)                                # grille


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


# ---- 1. Floor ------------------------------------------------------------------------------------------------------------
def build_Floor(p):
    # parking lot with bay lines
    bx(p, (-92, -56), (0, 0.3), (30, 58), ASP, 0.07)
    for x in (-91.8, -80, -68, -56.2):
        bx(p, (x - 0.2, x + 0.2), (0.3, 0.38), (36, 49), WHT, 0.02)
    bx(p, (-92, -56), (0.3, 0.38), (35.8, 36.2), WHT, 0.02)
    for x in (-86, -74, -62):          # painted arrows pointing out of the bays
        bx(p, (x - 0.25, x + 0.25), (0.3, 0.38), (40, 45), YEL, 0.02)
    # plaza in front of the headquarters: checker tiles, blue badge circle around the Shiba, yellow kerb
    bx(p, (33, 93), (0, 0.3), (-64, -16), CON, 0.05)
    for i in range(6):
        for j in range(4):
            if (i + j) % 2 == 0:
                bx(p, (33 + i * 10, 43 + i * 10), (0.3, 0.34), (-64 + j * 12, -52 + j * 12), CONL, 0.04)
    vcyl(p, 58, 0.3, 0.38, -37, 8.5, BLU, verts=18, jit=0.02)
    vcyl(p, 58, 0.3, 0.42, -37, 7.3, WHT, verts=18, jit=0.02)
    vcyl(p, 58, 0.3, 0.46, -37, 6.3, NAVY, verts=18, jit=0.02)
    star_poly(p, (58, 0.49, -37), 'xz', 5.2, 2.2, 0.06, YEL, n=5, rot0=90)
    bx(p, (33, 93), (0.3, 0.38), (-16.8, -16.0), YEL, 0.02)
    # gravel yard (impound) and cell-block apron
    bx(p, (-92, -58), (0, 0.3), (-24, 0), (120, 114, 102), 0.1)
    for (x0, x1, z0, z1) in ((-90, -84, -22, -17), (-72, -64, -10, -4), (-84, -78, -7, -3)):
        bx(p, (x0, x1), (0.3, 0.34), (z0, z1), (92, 88, 80), 0.08)
    bx(p, (-92, -62), (0, 0.3), (-63, -37), (130, 134, 146), 0.05)
    bx(p, (-92, -62), (0.3, 0.34), (-38.6, -38.0), YEL, 0.02)
    bx(p, (-79.5, -75.5), (0.3, 0.34), (-62, -45), (118, 122, 134), 0.03)
    # monument plaza: stone disc, blue ring, gold star
    vcyl(p, -24, 0, 0.3, 0, 13, CONL, verts=20, jit=0.03)
    vcyl(p, -24, 0.3, 0.38, 0, 9, BLU, verts=20, jit=0.02)
    vcyl(p, -24, 0.3, 0.42, 0, 8, CONL, verts=20, jit=0.02)
    star_poly(p, (-24, 0.45, 0), 'xz', 7.4, 3.4, 0.06, GLD, n=8, rot0=90)
    # donut-shop pad with candy stripes
    bx(p, (17, 39), (0, 0.3), (-9, 5), OFF, 0.04)
    for x in (19.5, 24.5, 29.5, 34.5):
        bx(p, (x - 1.2, x + 1.2), (0.3, 0.34), (-9, 5), PNK, 0.03)
    # sidewalk along the road with expansion joints
    bx(p, (-95, 95), (0, 0.3), (61, 65), CONL, 0.04)
    bx(p, (-95, 95), (0.3, 0.38), (60.8, 61.2), MET, 0.02)
    for x in range(-90, 91, 20):
        bx(p, (x - 0.12, x + 0.12), (0.3, 0.34), (61.2, 65), (150, 152, 162), 0.02)
    # helipad base with yellow edge
    bx(p, (-54, -26), (0, 0.3), (-62, -34), DGR, 0.05)
    for (x0, x1, z0, z1) in ((-53.2, -26.8, -61.4, -60.8), (-53.2, -26.8, -35.2, -34.6), (-53.2, -52.6, -61.4, -34.6),
                             (-27.4, -26.8, -61.4, -34.6)):
        bx(p, (x0, x1), (0.3, 0.34), (z0, z1), YEL, 0.02)
    # range lane
    bx(p, (51, 91), (0, 0.3), (21, 45), (140, 142, 154), 0.05)
    for x in (63, 71, 79):
        bx(p, (x - 0.2, x + 0.2), (0.3, 0.34), (26, 40), WHT, 0.02)
    bx(p, (53, 89), (0.3, 0.34), (41.8, 42.4), YEL, 0.02)
    # roadblock road with dashed centre line and edge lines
    bx(p, (15, 45), (0, 0.3), (49, 59), ASP, 0.07)
    for x in (17, 23, 29, 35):
        bx(p, (x, x + 4), (0.3, 0.34), (53.85, 54.15), WHT, 0.02)
    bx(p, (15, 45), (0.3, 0.34), (49.4, 49.7), WHT, 0.02)
    bx(p, (15, 45), (0.3, 0.34), (58.3, 58.6), WHT, 0.02)


# ---- 2. Station ----------------------------------------------------------------------------------------------------------
def build_Station(p):
    roof = []
    # walls: main block and two wings that wrap the courtyard
    bx(p, (36, 90), (0, 14), (-62, -48), WHT, 0.03)
    bx(p, (36, 47), (0, 12), (-62, -40), WHT, 0.03)
    bx(p, (79, 90), (0, 12), (-62, -40), WHT, 0.03)
    bx(p, (35.8, 90.2), (0, 0.9), (-62.2, -47.8), DGR, 0.04)
    bx(p, (35.8, 47.2), (0, 0.9), (-47.8, -39.8), DGR, 0.04)
    bx(p, (78.8, 90.2), (0, 0.9), (-47.8, -39.8), DGR, 0.04)
    # roofs
    roof.append(bx(p, (35.5, 90.5), (14, 14.8), (-62.5, -47.5), ROOF, 0.05))
    roof.append(bx(p, (35.5, 47.5), (12, 12.8), (-62.5, -39.5), ROOF, 0.05))
    roof.append(bx(p, (78.5, 90.5), (12, 12.8), (-62.5, -39.5), ROOF, 0.05))
    roof.append(bx(p, (35.5, 90.5), (14.8, 15.3), (-47.9, -47.5), BLU, 0.03))
    roof.append(bx(p, (35.5, 47.5), (12.8, 13.3), (-39.9, -39.5), BLU, 0.03))
    roof.append(bx(p, (78.5, 90.5), (12.8, 13.3), (-39.9, -39.5), BLU, 0.03))
    roof.append(bx(p, (74, 80), (14.8, 16.4), (-59, -54), MET, 0.05))
    roof.append(bx(p, (42, 47), (14.8, 15.8), (-60, -57), MET, 0.05))
    # clock tower with sign and clock
    bx(p, (56, 70), (14.5, 24.5), (-60, -50), WHT, 0.03)
    roof.append(bx(p, (55.25, 70.75), (24.4, 25.6), (-60.75, -49.25), NAVY, 0.03))
    for x in (55.8, 70.0):
        bx(p, (x, x + 0.2), (15.8, 18.6), (-57.5, -52.5), GLS, 0.04)
    bx(p, (57.4, 68.6), (18.5, 21.5), (-50.0, -49.6), BLU, 0.03)
    text(p, "POLICE", 63, 19.2, -49.6, -49.35, 1.2, 1.6, 0.3, 0.3, WHT)
    zcyl(p, 63, 23.0, -50.0, -49.8, 1.45, NAVY, verts=12, jit=0.02)
    zcyl(p, 63, 23.0, -49.8, -49.7, 1.2, WHT, verts=12, jit=0.02)
    bx(p, (62.9, 63.1), (23.0, 24.0), (-49.72, -49.62), NAVY, 0.02)
    bx(p, (63.0, 63.9), (22.9, 23.1), (-49.72, -49.62), NAVY, 0.02)
    # entrance: frame, glass doors, canopy, steps
    bx(p, (59.6, 66.4), (0, 6.4), (-48.0, -47.7), NAVY, 0.03)
    bx(p, (60.0, 62.9), (0.4, 6.0), (-47.75, -47.55), GLS, 0.04)
    bx(p, (63.1, 66.0), (0.4, 6.0), (-47.75, -47.55), GLS, 0.04)
    bx(p, (62.8, 63.2), (0.4, 6.0), (-47.8, -47.5), NAVY, 0.02)
    bx(p, (55, 71), (7.35, 7.85), (-47.8, -43.8), BLU, 0.03)
    bx(p, (55, 71), (7.0, 7.35), (-44.1, -43.8), NAVY, 0.03)
    bx(p, (57, 69), (0, 0.25), (-47.8, -45.6), OFF, 0.04)
    bx(p, (58, 68), (0.25, 0.5), (-47.8, -46.6), CONL, 0.04)
    # blue belt with stars
    bx(p, (36, 90), (9.4, 11.6), (-48.0, -47.7), BLU, 0.03)
    bx(p, (36, 47), (9.4, 11.6), (-40.15, -39.9), BLU, 0.03)
    bx(p, (79, 90), (9.4, 11.6), (-40.15, -39.9), BLU, 0.03)
    star_poly(p, (44, 10.5, -47.6), 'xy', 0.9, 0.4, 0.12, WHT, n=5)
    star_poly(p, (82, 10.5, -47.6), 'xy', 0.9, 0.4, 0.12, WHT, n=5)
    # windows
    for (a, b) in ((48.6, 51.8), (52.8, 56.0), (71.0, 74.2), (75.2, 78.4)):
        window_z(p, a, b, 2.6, 6.0, -48.0, mull=False)
    for (a, b) in ((38, 41.4), (42.6, 46.0)):
        window_z(p, a, b, 2.6, 6.0, -40.0, mull=False)
        window_z(p, a, b, 6.2, 8.8, -40.0, mull=False)
    for (a, b) in ((48.6, 51.8), (75.2, 78.4)):
        window_z(p, a, b, 6.7, 9.0, -48.0, mull=False)
    for x in (59.0, 67.0):
        bx(p, (x - 0.3, x + 0.3), (5.0, 6.4), (-47.7, -47.4), YEL, 0.02)
        bx(p, (x - 0.4, x + 0.4), (6.4, 6.6), (-47.7, -47.3), DGR, 0.02)
    star_poly(p, (63, 10.5, -47.55), 'xy', 1.0, 0.45, 0.1, GLD, n=5)
    window_x(p, 47.0, 1, 2.6, 6.0, -45.5, -42.5)
    window_x(p, 79.0, -1, 2.6, 6.0, -45.5, -42.5)
    # garage door on the right wing, yellow hazard strip
    bx(p, (80.8, 88.2), (0, 6.6), (-40.15, -39.9), MET, 0.04)
    for y in (1.6, 3.0, 4.4, 5.8):
        bx(p, (80.8, 88.2), (y, y + 0.14), (-39.95, -39.8), DGR, 0.02)
    bx(p, (80.6, 88.4), (6.6, 7.1), (-40.15, -39.85), YEL, 0.02)
    # roof flag
    vcyl(p, 87, 14.8, 25.0, -58, 0.22, MET, verts=6, jit=0.02)
    bx(p, (87.2, 90.2), (22.9, 24.7), (-58.1, -57.9), RED, 0.03)
    star_poly(p, (88.7, 23.8, -57.85), 'xy', 0.5, 0.22, 0.05, WHT, n=5)
    return {"Roof": roof}


# ---- 3. Cars -------------------------------------------------------------------------------------------------------------
def build_Cars(p):
    for x in (-86, -74, -62):
        car(p, x, 42.0)


# ---- 4. Cells --------------------------------------------------------------------------------------------------------------
def build_Cells(p):
    roof = []
    bx(p, (-90, -64), (0, 10), (-62, -44), (150, 154, 168), 0.05)
    for (a, b) in ((-90, -88.8), (-83.9, -83.1), (-70.9, -70.1), (-65.2, -64)):
        bx(p, (a, b), (0, 10), (-44.05, -43.7), OFF, 0.03)
    bx(p, (-90.3, -63.7), (0, 0.8), (-62.3, -43.7), DGR, 0.04)
    roof.append(bx(p, (-90.75, -63.25), (10, 10.8), (-62.75, -43.25), ROOFL, 0.05))
    roof.append(bx(p, (-90.75, -63.25), (10.8, 11.3), (-43.6, -43.25), BLU, 0.03))
    roof.append(bx(p, (-90.75, -63.25), (10.8, 11.3), (-62.75, -62.4), OFF, 0.03))
    roof.append(bx(p, (-90.75, -90.4), (10.8, 11.3), (-62.4, -43.6), OFF, 0.03))
    roof.append(bx(p, (-63.6, -63.25), (10.8, 11.3), (-62.4, -43.6), OFF, 0.03))
    roof.append(bx(p, (-72, -67), (10.8, 12.2), (-60, -56), MET, 0.04))
    roof.append(bx(p, (-86, -82), (10.8, 12.0), (-58, -54), MET, 0.04))
    # barred windows
    for x in (-86, -81, -73, -68):
        bx(p, (x - 2.0, x + 2.0), (3.3, 7.6), (-44.0, -43.85), GLD_, 0.03)
        bx(p, (x - 2.3, x + 2.3), (7.6, 8.0), (-44.0, -43.7), DGR, 0.02)
        bx(p, (x - 2.3, x + 2.3), (3.0, 3.3), (-44.0, -43.7), DGR, 0.02)
        for dx in (-1.0, 0.0, 1.0):
            bx(p, (x + dx - 0.12, x + dx + 0.12), (3.3, 7.6), (-43.9, -43.7), MET, 0.02)
    # door and sign
    bx(p, (-79.4, -74.6), (0, 6.0), (-44.0, -43.75), DGR, 0.03)
    bx(p, (-79.0, -75.0), (0, 5.6), (-43.8, -43.6), NAVY, 0.03)
    bx(p, (-78.0, -76.0), (3.6, 5.0), (-43.62, -43.5), GLD_, 0.02)
    bx(p, (-77.9, -77.7), (3.6, 5.0), (-43.55, -43.4), MET, 0.02)
    bx(p, (-76.3, -76.1), (3.6, 5.0), (-43.55, -43.4), MET, 0.02)
    bx(p, (-83, -71), (8.3, 9.8), (-43.7, -43.4), BLU, 0.03)
    text(p, "JAIL", -77, 8.55, -43.4, -43.25, 1.2, 1.0, 0.26, 0.5, WHT)
    star_poly(p, (-84.2, 9.05, -43.35), 'xy', 0.55, 0.25, 0.1, YEL, n=5)
    star_poly(p, (-69.8, 9.05, -43.35), 'xy', 0.55, 0.25, 0.1, YEL, n=5)
    bx(p, (-80, -74), (0, 0.4), (-43.8, -42.4), OFF, 0.03)
    # guard tower
    for (x, z) in ((-92.6, -43.6), (-89.4, -43.6), (-92.6, -40.4), (-89.4, -40.4)):
        bx(p, (x - 0.35, x + 0.35), (0, 15.5), (z - 0.35, z + 0.35), DGR, 0.03)
    for y in (4.5, 10.0):
        bx(p, (-93, -89), (y, y + 0.3), (-44, -40), DGR, 0.03)
    diag(p, -92.6, 0.5, -43.6, -89.4, 4.5, 0.3, 0.3, DGR, 0.02)
    diag(p, -89.4, 4.6, -43.6, -92.6, 10.0, 0.3, 0.3, DGR, 0.02)
    diag(p, -92.6, 10.1, -43.6, -89.4, 15.4, 0.3, 0.3, DGR, 0.02)
    bx(p, (-94, -88), (15.5, 16.6), (-45, -39), NAVY, 0.03)
    bx(p, (-93.7, -88.3), (16.6, 18.1), (-44.7, -39.3), GLS, 0.05)
    for (x, z) in ((-93.8, -44.8), (-88.2, -44.8), (-93.8, -39.2), (-88.2, -39.2)):
        bx(p, (x - 0.2, x + 0.2), (16.6, 18.1), (z - 0.2, z + 0.2), NAVY, 0.02)
    roof.append(bx(p, (-94.5, -87.5), (18.1, 18.7), (-45.5, -38.5), ROOFL, 0.04))
    roof.append(vcyl(p, -91, 18.7, 19.1, -42, 0.9, YEL, verts=8, jit=0.02))
    # fenced yard with open gate
    fence_run(p, -91, -81, -38, -38, 5, step=2.5)
    fence_run(p, -73, -63, -38, -38, 5, step=2.5)
    for x in (-80.6, -73.4):
        bx(p, (x - 0.35, x + 0.35), (0, 5.4), (-38.35, -37.65), DGR, 0.03)
    return {"Roof": roof}


# ---- 5. Donuts -------------------------------------------------------------------------------------------------------------
def build_Donuts(p):
    roof = []
    bx(p, (21, 35), (0, 6), (-6, 2), CRM, 0.03)
    bx(p, (20.8, 35.2), (0, 0.6), (-6.2, 2.2), BRN, 0.03)
    roof.append(bx(p, (20.5, 35.5), (6, 6.6), (-6.5, 2.5), PNK, 0.03))
    # striped awning over the front
    cols = (PNK, WHT)
    for i in range(7):
        x0 = 21.5 + i * 13 / 7
        x1 = x0 + 13 / 7
        hexa(p, [(x0, 5.65, 1.5), (x1, 5.65, 1.5), (x1, 4.65, 4.5), (x0, 4.65, 4.5),
                 (x0, 5.95, 1.5), (x1, 5.95, 1.5), (x1, 4.95, 4.5), (x0, 4.95, 4.5)], cols[i % 2], 0.02)
    # shop window, door, counter
    bx(p, (21.9, 29.6), (1.7, 4.5), (2.0, 2.1), BRN, 0.02)
    bx(p, (22.2, 29.3), (2.0, 4.2), (2.0, 2.15), GLS, 0.05)
    bx(p, (25.65, 25.85), (2.0, 4.2), (2.0, 2.2), BRN, 0.02)
    bx(p, (22.2, 29.3), (1.6, 2.0), (2.0, 3.4), BRN, 0.04)
    bx(p, (30.8, 33.6), (0, 4.9), (2.0, 2.12), BRN, 0.03)
    bx(p, (31.1, 33.3), (1.9, 4.5), (2.0, 2.2), GLS, 0.05)
    bx(p, (33.0, 33.15), (2.1, 2.9), (2.2, 2.4), GLD, 0.02)
    # roof sign and chimney
    bx(p, (21.5, 34.5), (6.6, 8.1), (1.5, 1.8), BRN, 0.03)
    text(p, "DONUTS", 28, 6.95, 1.8, 1.95, 1.4, 0.9, 0.24, 0.45, CRM)
    bx(p, (33, 35), (6.5, 9.5), (-5.5, -3.5), RST, 0.05)
    bx(p, (32.8, 35.2), (9.3, 9.5), (-5.7, -3.3), DGR, 0.03)
    # the giant donut: dough ring with pink icing and sprinkles
    torus(p, (28, 8.4, -2), 2.4, 1.1, (225, 170, 100), segs=16, sides=8, jit=0.05)
    torus(p, (28, 8.4, -2), 2.4, 1.16, HPK, segs=16, sides=4, arc=(0.0, math.pi), jit=0.03)
    for k, col in enumerate((WHT, YEL, BLU, WHT, YEL, RED, BLU, WHT)):
        a = k * math.pi / 4 + 0.3
        rr = 2.4 + 0.5 * math.cos(k * 2.1)
        bx(p, (28 + rr * math.cos(a) - 0.2, 28 + rr * math.cos(a) + 0.2), (9.52, 9.64),
           (-2 + rr * math.sin(a) - 0.1, -2 + rr * math.sin(a) + 0.1), col, 0.02, rot=(0, k * 40, 0))
    # stools
    for x in (24, 30):
        vcyl(p, x, 0, 0.2, 5.5, 0.7, DGR, verts=8, jit=0.02)
        vcyl(p, x, 0.2, 1.5, 5.5, 0.2, MET, verts=6, jit=0.02)
        vcyl(p, x, 1.5, 2.0, 5.5, 0.8, RED, verts=8, jit=0.03)
    return {"Roof": roof}


# ---- 6. Beacon -------------------------------------------------------------------------------------------------------------
def build_Beacon(p):
    bx(p, (1.5, 10.5), (0, 1.0), (5.5, 14.5), CON, 0.05)
    for (x, z) in ((2.6, 6.6), (9.4, 6.6), (2.6, 13.4), (9.4, 13.4)):
        bx(p, (x - 0.3, x + 0.3), (1.0, 1.25), (z - 0.3, z + 0.3), DGR, 0.02)
    legs = ((3.5, 7.5), (8.5, 7.5), (3.5, 12.5), (8.5, 12.5))
    for (x, z) in legs:
        vcyl(p, x, 1.0, 25.0, z, 0.4, MET, verts=6, jit=0.03)
    # braces on the four faces, three levels
    for (y0, y1) in ((1.0, 8.0), (8.0, 16.0), (16.0, 25.0)):
        flip = 1 if (y0 + y1) / 2 > 12 else 0
        pairs = (((3.5, 7.5), (8.5, 7.5)), ((8.5, 7.5), (8.5, 12.5)), ((8.5, 12.5), (3.5, 12.5)), ((3.5, 12.5), (3.5, 7.5)))
        for k, (a, b) in enumerate(pairs):
            if (k + flip) % 2:
                a, b = b, a
            bar(p, (a[0], y0, a[1]), (b[0], y1, b[1]), 0.22, DGR, 0.02)
    for y in (8.0, 16.0):
        bx(p, (3.0, 9.0), (y - 0.25, y + 0.25), (7.0, 13.0), DGR, 0.04)
    # top platform with rails
    bx(p, (2.5, 9.5), (24.9, 25.5), (6.5, 13.5), DGR, 0.04)
    for (x0, x1, z0, z1) in ((2.5, 9.5, 6.5, 6.7), (2.5, 9.5, 13.3, 13.5), (2.5, 2.7, 6.5, 13.5), (9.3, 9.5, 6.5, 13.5)):
        bx(p, (x0, x1), (25.5, 26.4), (z0, z1), MET, 0.03)
    # cab with window band, badge and light housing
    bx(p, (3.7, 8.3), (25.5, 29.1), (7.7, 12.3), WHT, 0.03)
    bx(p, (3.6, 8.4), (26.2, 27.6), (7.6, 12.4), GLD_, 0.05)
    bx(p, (3.6, 8.4), (25.5, 26.2), (7.6, 12.4), BLU, 0.03)
    for (x, z) in ((3.65, 7.65), (8.35, 7.65), (3.65, 12.35), (8.35, 12.35)):
        bx(p, (x - 0.25, x + 0.25), (26.2, 27.6), (z - 0.25, z + 0.25), WHT, 0.02)
    star_poly(p, (6, 28.4, 12.35), 'xy', 0.6, 0.28, 0.1, YEL, n=5)
    bx(p, (3.4, 8.6), (29.1, 29.6), (7.4, 12.6), NAVY, 0.03)
    bx(p, (2.4, 9.6), (29.6, 30.2), (8.7, 11.3), DGR, 0.03)
    ball(p, (4.3, 30.4, 10), 1.5, RED, subdiv=2)
    ball(p, (7.7, 30.4, 10), 1.5, BLU, subdiv=2)
    vcyl(p, 6, 30.2, 36.5, 10, 0.16, MET, verts=6, jit=0.02)
    bx(p, (5.2, 6.8), (35.0, 35.15), (9.92, 10.08), MET, 0.02)
    bx(p, (5.5, 6.5), (33.6, 33.75), (9.92, 10.08), MET, 0.02)
    # ladder on the road side
    for x in (5.4, 6.6):
        bx(p, (x - 0.07, x + 0.07), (1.0, 24.9), (5.5, 5.64), MET, 0.02)
    for y in [1.8 + 1.4 * k for k in range(16)]:
        bx(p, (5.4, 6.6), (y, y + 0.1), (5.5, 5.64), MET, 0.02)
    for y in (7.0, 15.0):
        bx(p, (5.2, 6.8), (y, y + 0.1), (5.5, 6.9), MET, 0.02)


# ---- 7. Range ---------------------------------------------------------------------------------------------------------------
def build_Range(p):
    # backstop wall of timber sleepers with posts
    for k in range(6):
        bx(p, (53, 89), (k * 1.0, k * 1.0 + 0.97), (22.6, 25.0), (130, 95, 60) if k % 2 == 0 else (104, 74, 48), 0.07)
    for x in (53.6, 62, 71, 80, 88.4):
        bx(p, (x - 0.5, x + 0.5), (0, 6.3), (22.6, 25.4), DBRN, 0.04)
    # targets on stakes
    for x in (59, 67, 75, 83):
        vcyl(p, x, 0, 4.4, 27.0, 0.25, BRN, verts=6, jit=0.03)
        zcyl(p, x, 4.5, 26.8, 27.0, 2.3, WHT, verts=10, jit=0.02)
        zcyl(p, x, 4.5, 26.8, 27.1, 1.6, RED, verts=10, jit=0.02)
        zcyl(p, x, 4.5, 26.8, 27.17, 1.0, WHT, verts=10, jit=0.02)
        zcyl(p, x, 4.5, 26.8, 27.22, 0.5, RED, verts=10, jit=0.02)
    # shooting bench with lane dividers
    bx(p, (54, 88), (1.5, 1.9), (38.7, 41.3), BRN, 0.06)
    for x in (55, 87):
        bx(p, (x - 0.5, x + 0.5), (0, 1.5), (39, 41), DGR, 0.03)
    for x in (63, 71, 79):
        bx(p, (x - 0.2, x + 0.2), (0, 4.0), (32.5, 40.5), BRN, 0.05)
        bx(p, (x - 0.3, x + 0.3), (4.0, 4.25), (32.5, 40.5), DBRN, 0.03)
    for x in (59, 67, 75, 83):
        bx(p, (x - 0.7, x + 0.7), (1.9, 2.4), (39.4, 40.4), BLU, 0.03)
        bx(p, (x + 1.3, x + 2.1), (1.9, 2.3), (39.7, 40.5), YEL, 0.03)


# ---- 8. Kennel -------------------------------------------------------------------------------------------------------------
def doghouse(p, xc, roof_col, wall_col, dog_col, dog_dark):
    """A hollow doghouse with its door toward -z (the run's open side) and a dog looking out."""
    bx(p, (xc - 2.5, xc + 2.5), (0, 0.2), (9.5, 14.5), DBRN, 0.03)
    bx(p, (xc - 2.5, xc + 2.5), (0.2, 4.0), (14.2, 14.5), wall_col, 0.04)
    bx(p, (xc - 2.5, xc - 2.2), (0.2, 4.0), (9.5, 14.2), wall_col, 0.04)
    bx(p, (xc + 2.2, xc + 2.5), (0.2, 4.0), (9.5, 14.2), wall_col, 0.04)
    bx(p, (xc - 2.2, xc - 1.1), (0.2, 4.0), (9.5, 9.8), wall_col, 0.04)
    bx(p, (xc + 1.1, xc + 2.2), (0.2, 4.0), (9.5, 9.8), wall_col, 0.04)
    bx(p, (xc - 1.1, xc + 1.1), (2.8, 4.0), (9.5, 9.8), wall_col, 0.04)
    bx(p, (xc - 1.2, xc + 1.2), (0.2, 0.3), (9.3, 10.2), DBRN, 0.02)
    dk.prism(p, (xc, 4.0, 12), 5.9, 6.2, 1.5, roof_col, ridge='z', jitter=0.04)
    # the dog in the doorway: head, ears, light muzzle, nose and eyes
    ball(p, (xc, 1.6, 10.2), 0.85, dog_col, scale=(1.0, 0.95, 0.95), subdiv=1, jit=0.03)
    for sx in (-1, 1):
        prism_z(p, [(xc + sx * 0.75, 2.05), (xc + sx * 0.2, 2.25), (xc + sx * 0.7, 2.85)], 9.95, 10.3, dog_dark, 0.03)
        bx(p, (xc + sx * 0.38 - 0.1, xc + sx * 0.38 + 0.1), (1.85, 2.1), (9.28, 9.4), BLK, 0.02)
    bx(p, (xc - 0.35, xc + 0.35), (1.15, 1.6), (9.1, 9.6), CRM, 0.03)
    bx(p, (xc - 0.15, xc + 0.15), (1.5, 1.68), (9.0, 9.2), BLK, 0.02)


def build_Kennel(p):
    doghouse(p, 76, RED, WHT, (225, 150, 80), (190, 110, 55))
    doghouse(p, 82, BLU, (200, 160, 110), (40, 40, 48), (28, 28, 34))
    doghouse(p, 88, RED, WHT, (238, 238, 244), (200, 204, 214))
    # picket fence: back and both sides, open at the front
    for k in range(9):
        x = 72.9 + k * 2.3
        bx(p, (x - 0.12, x + 0.12), (0, 3.0), (16.4, 16.8), WHT, 0.03)
    for z in [3.7 + k * 2.6 for k in range(6)]:
        bx(p, (72.0, 72.4), (0, 3.0), (z - 0.12, z + 0.12), WHT, 0.03)
        bx(p, (91.6, 92.0), (0, 3.0), (z - 0.12, z + 0.12), WHT, 0.03)
    bx(p, (72, 92), (0.6, 0.85), (16.4, 16.8), WHT, 0.03)
    bx(p, (72, 92), (2.2, 2.45), (16.4, 16.8), WHT, 0.03)
    for xx in (72.0, 91.6):
        bx(p, (xx, xx + 0.4), (0.6, 0.85), (3.2, 16.8), WHT, 0.03)
        bx(p, (xx, xx + 0.4), (2.2, 2.45), (3.2, 16.8), WHT, 0.03)
    for (x, z) in ((72.2, 16.6), (91.8, 16.6), (72.2, 3.5), (91.8, 3.5)):
        bx(p, (x - 0.3, x + 0.3), (0, 3.3), (z - 0.3, z + 0.3), WHT, 0.03)
    # bowls
    for (x, z, col) in ((79, 5.5, MET), (85, 4.9, RED)):
        vcyl(p, x, 0, 0.45, z, 0.9, col, verts=8, jit=0.03)
    # K-9 sign on two posts, readable from both sides
    for x in (77.5, 86.5):
        vcyl(p, x, 0, 7.0, 16.5, 0.25, MET, verts=6, jit=0.02)
    bx(p, (77, 87), (5.8, 8.2), (16.35, 16.65), BLU, 0.03)
    text(p, "K-9", 82, 6.4, 16.65, 16.8, 1.1, 1.3, 0.3, 0.4, WHT)
    text(p, "K-9", 82, 6.4, 16.2, 16.35, 1.1, 1.3, 0.3, 0.4, WHT, mirror=True)
    for xb in (78.7, 85.3):
        for (za, zb) in ((16.65, 16.8), (16.2, 16.35)):
            bx(p, (xb - 0.5, xb + 0.5), (6.95, 7.2), (za, zb), WHT, 0.02)
            for sx in (-1, 1):
                bx(p, (xb + sx * 0.5 - 0.15, xb + sx * 0.5 + 0.15), (6.8, 7.35), (za, zb), WHT, 0.02)


# ---- 9. Heli -------------------------------------------------------------------------------------------------------------
def build_Heli(p):
    vcyl(p, -40, 0, 0.5, -48, 12, DGR, verts=24, jit=0.04)
    vcyl(p, -40, 0.5, 0.55, -48, 11.6, YEL, verts=24, jit=0.02)
    vcyl(p, -40, 0.5, 0.6, -48, 11.0, (86, 90, 104), verts=24, jit=0.03)
    bx(p, (-44.7, -43.3), (0.6, 0.67), (-53.5, -42.5), YEL, 0.02)
    bx(p, (-36.7, -35.3), (0.6, 0.67), (-53.5, -42.5), YEL, 0.02)
    bx(p, (-43.3, -36.7), (0.6, 0.67), (-48.7, -47.3), YEL, 0.02)
    # fuselage, nose, cowling
    bx(p, (-42.8, -37.2), (1.7, 5.2), (-53, -45), BLU, 0.03)
    bx(p, (-42.4, -37.6), (1.3, 1.7), (-52.5, -44.5), NAVY, 0.03)
    ball(p, (-40, 3.3, -44.4), 2.2, GLD_, scale=(1.0, 0.9, 1.15), subdiv=2, jit=0.03)
    bx(p, (-41.4, -38.6), (5.2, 6.2), (-52, -47), NAVY, 0.03)
    bx(p, (-41.0, -40.05), (6.2, 6.5), (-51, -49), RED, 0.02)
    bx(p, (-39.95, -39.0), (6.2, 6.5), (-51, -49), BLU, 0.02)
    for sx, xs in ((-1, -42.8), (1, -37.2)):
        d = 0.1 * sx
        bx(p, tuple(sorted((xs, xs + d))), (2.6, 3.0), (-52.5, -45.2), WHT, 0.02)
        bx(p, tuple(sorted((xs, xs + d))), (3.2, 4.7), (-47.2, -45.4), GLS, 0.04)
        bx(p, tuple(sorted((xs, xs + d))), (3.2, 4.7), (-51.8, -48.2), BLU, 0.02)
        star_poly(p, (xs + d, 3.9, -49.9), 'yz', 0.85, 0.38, 0.06, YEL, n=5)
    # tail boom, fin, tail rotor
    hexa(p, [(-40.8, 3.5, -52), (-39.2, 3.5, -52), (-39.2, 5.0, -52), (-40.8, 5.0, -52),
             (-40.45, 4.25, -59.6), (-39.55, 4.25, -59.6), (-39.55, 5.0, -59.6), (-40.45, 5.0, -59.6)], BLU, 0.03)
    hexa(p, [(-40.2, 4.6, -58.6), (-40.2, 4.6, -60.2), (-40.2, 7.3, -60.6), (-40.2, 7.3, -59.6),
             (-39.8, 4.6, -58.6), (-39.8, 4.6, -60.2), (-39.8, 7.3, -60.6), (-39.8, 7.3, -59.6)], NAVY, 0.03)
    bx(p, (-39.8, -39.7), (5.3, 7.5), (-60.15, -59.85), DGR, 0.02)
    bx(p, (-39.8, -39.7), (6.3, 6.5), (-61.0, -59.0), DGR, 0.02)
    # skids and struts
    for xs in (-42.4, -37.6):
        bx(p, (xs - 0.25, xs + 0.25), (0.65, 1.15), (-53, -44), DGR, 0.03)
        for z in (-46.5, -51.0):
            bx(p, (xs - 0.15, xs + 0.15), (1.15, 1.9), (z - 0.15, z + 0.15), DGR, 0.03)
    for xs in (-42.0, -38.0):
        bx(p, (xs - 0.2, xs + 0.2), (1.7, 2.9), (-46.7, -46.3), DGR, 0.03)
    # rotor mast, hub and blades with white tips
    vcyl(p, -40, 5.9, 7.9, -49, 0.45, DGR, verts=8, jit=0.03)
    vcyl(p, -40, 7.7, 8.15, -49, 0.95, MET, verts=8, jit=0.03)
    bx(p, (-52, -28), (7.85, 8.15), (-49.6, -48.4), DGR, 0.03)
    bx(p, (-40.6, -39.4), (7.85, 8.15), (-61, -37), DGR, 0.03)
    for (x0, x1, z0, z1) in ((-52, -50.2, -49.62, -48.38), (-29.8, -28, -49.62, -48.38),
                             (-40.62, -39.38, -61, -59.2), (-40.62, -39.38, -38.8, -37)):
        bx(p, (x0, x1), (7.83, 8.17), (z0, z1), WHT, 0.02)


# ---- 10. Roadblock ------------------------------------------------------------------------------------------------------------
def build_Roadblock(p):
    for x in (20, 30, 40):
        bx(p, (x - 3.5, x + 3.5), (0, 0.8), (51.2, 52.8), DGR, 0.03)
        for sx in (-1, 1):
            bx(p, (x + sx * 3.0 - 0.2, x + sx * 3.0 + 0.2), (0.8, 3.2), (51.8, 52.2), WHT, 0.03)
        bx(p, (x - 3.5, x + 3.5), (2.25, 3.15), (51.75, 52.25), WHT, 0.02)
        bx(p, (x - 3.5, x + 3.5), (1.25, 2.15), (51.75, 52.25), RED, 0.02)
        for k in range(4):
            x0 = x - 3.5 + 0.5 + k * 1.75
            bx(p, (x0, x0 + 0.85), (2.25, 3.15), (51.7, 52.3), RED, 0.02)
            bx(p, (x0 + 0.9, x0 + 1.75), (1.25, 2.15), (51.7, 52.3), WHT, 0.02)
        bx(p, (x - 0.6, x + 0.6), (3.15, 3.7), (51.85, 52.15), YEL, 0.03)
    for x in (17, 25, 35, 43):
        bx(p, (x - 0.85, x + 0.85), (0, 0.2), (54.15, 55.85), BLK, 0.02)
        vcyl(p, x, 0.2, 1.0, 55, 0.75, ORG, verts=6, top_r=0.54, jit=0.03)
        vcyl(p, x, 1.0, 1.5, 55, 0.54, WHT, verts=6, top_r=0.4, jit=0.02)
        vcyl(p, x, 1.5, 2.4, 55, 0.4, ORG, verts=6, top_r=0.12, jit=0.03)
    bx(p, (23, 37), (0, 0.4), (55.8, 57.2), BLK, 0.03)
    for k in range(14):
        dk.cone(p, (23.5 + k * 1.0, 0.4, 56.5), 0.28, 0.4, MET, verts=4, jitter=0.02)
    # stop sign
    vcyl(p, 45, 0, 4.5, 50, 0.2, MET, verts=6, jit=0.02)
    zcyl(p, 45, 5.6, 49.85, 50.1, 1.2, WHT, verts=8, jit=0.02, rot=(0, 0, 22.5))
    zcyl(p, 45, 5.6, 49.9, 50.15, 1.04, RED, verts=8, jit=0.02, rot=(0, 0, 22.5))
    text(p, "STOP", 45, 5.3, 50.15, 50.22, 0.42, 0.62, 0.11, 0.08, WHT)


# ---- 11. Swat ----------------------------------------------------------------------------------------------------------------
def build_Swat(p):
    VAN = (40, 44, 58)
    bx(p, (14.5, 31.8), (0.8, 2.0), (-58.0, -52.0), BLK, 0.03)
    bx(p, (14, 26), (1.9, 7.2), (-58.5, -51.5), VAN, 0.04)
    bx(p, (26, 30.2), (1.9, 6.0), (-58.4, -51.6), VAN, 0.04)
    bx(p, (30.2, 32), (1.9, 4.2), (-58.4, -51.6), VAN, 0.04)
    prism_z(p, [(30.2, 4.2), (32.0, 4.2), (30.2, 6.0)], -57.4, -52.6, GLD_, 0.03)
    # wheels with arches
    for x in (16.5, 28.5):
        for z, s in ((-58.7, -1), (-51.3, 1)):
            zcyl(p, x, 1.7, z - 0.5, z + 0.5, 1.7, BLK, verts=10, jit=0.02)
            zcyl(p, x, 1.7, z + 0.5 * s, z + 0.55 * s, 0.9, MET, verts=8, jit=0.02)
            bx(p, (x - 2.0, x + 2.0), (3.35, 3.7), (z - 0.5, z + 0.5), BLK, 0.02)
    # armour details: stripes and SWAT letters on the road side
    bx(p, (14.1, 25.9), (6.1, 6.3), (-51.55, -51.4), YEL, 0.02)
    bx(p, (14.1, 25.9), (3.2, 3.4), (-51.55, -51.4), YEL, 0.02)
    text(p, "SWAT", 20, 4.0, -51.5, -51.3, 1.9, 1.7, 0.4, 0.5, WHT)
    bx(p, (14.1, 25.9), (6.1, 6.3), (-58.6, -58.45), YEL, 0.02)
    bx(p, (14.1, 25.9), (3.2, 3.4), (-58.6, -58.45), YEL, 0.02)
    # cab side windows, headlights, bull bar
    bx(p, (26.5, 29.8), (3.8, 5.7), (-51.6, -51.5), GLS, 0.04)
    bx(p, (26.5, 29.8), (3.8, 5.7), (-58.5, -58.4), GLS, 0.04)
    for z in (-56.8, -53.2):
        bx(p, (31.95, 32.15), (2.6, 3.3), (z - 0.5, z + 0.5), YEL, 0.02)
    bx(p, (32.0, 32.25), (1.9, 2.4), (-57.4, -52.6), DGR, 0.03)
    bx(p, (32.0, 32.25), (2.4, 3.9), (-55.2, -54.8), DGR, 0.03)
    # roof: light bar and breaching ram
    bx(p, (28, 30), (6.0, 6.3), (-57.5, -52.5), DGR, 0.02)
    bx(p, (28.05, 29.95), (6.3, 6.65), (-57.4, -55.1), RED, 0.02)
    bx(p, (28.05, 29.95), (6.3, 6.65), (-54.9, -52.6), BLU, 0.02)
    for x in (17.5, 22.5):
        bx(p, (x - 0.3, x + 0.3), (7.2, 7.9), (-57, -53), DGR, 0.03)
    xcyl(p, 16.5, 23.5, 7.9, -55, 0.4, MET, verts=8, jit=0.03)
    bx(p, (17, 23), (7.4, 8.2), (-56, -54), BLK, 0.03)
    bx(p, (13.95, 14.1), (4.5, 5.0), (-57.6, -57.0), RED, 0.02)
    bx(p, (13.95, 14.1), (4.5, 5.0), (-53.0, -52.4), RED, 0.02)
    bx(p, (13.9, 14.0), (2.2, 6.9), (-55.1, -54.9), DGR, 0.02)


# ---- 12. Wanted ---------------------------------------------------------------------------------------------------------------
def build_Wanted(p):
    PAPER = (235, 220, 170)
    INK = (60, 40, 30)
    for x in (-63, -47):
        bx(p, (x - 1.5, x + 1.5), (0, 1.0), (14.5, 17.5), CON, 0.04)
        for sx in (-1, 1):
            for sz in (-1, 1):
                bx(p, (x + sx * 1.0 - 0.15, x + sx * 1.0 + 0.15), (1.0, 1.15), (16 + sz * 1.0 - 0.15, 16 + sz * 1.0 + 0.15), DGR, 0.02)
        vcyl(p, x, 1.0, 11.0, 16, 0.6, DGR, verts=8, jit=0.03)
        bar(p, (x, 0.9, 14.7), (x, 8.0, 15.4), 0.3, DGR, 0.02)
    bx(p, (-65, -45), (6, 16), (15.6, 16.6), NAVY, 0.03)
    bx(p, (-64.2, -45.8), (6.8, 15.2), (16.55, 16.85), PAPER, 0.04)
    text(p, "WANTED", -55, 13.1, 16.85, 17.0, 1.3, 1.7, 0.34, 0.35, INK)
    bx(p, (-60.5, -49.5), (12.55, 12.8), (16.85, 16.95), INK, 0.02)
    # the bandit: striped shirt, tan face with black mask, beanie and ears
    bx(p, (-56.6, -53.4), (7.1, 9.2), (16.85, 17.05), WHT, 0.03)
    for y in (7.4, 8.1, 8.8):
        bx(p, (-56.6, -53.4), (y, y + 0.32), (17.0, 17.1), BLK, 0.02)
    ball(p, (-55, 10.5, 17.0), 1.75, (232, 178, 120), scale=(1.0, 1.0, 0.3), subdiv=2, jit=0.03)
    bx(p, (-56.9, -53.1), (10.5, 11.4), (17.35, 17.5), BLK, 0.02)
    for x in (-56.0, -54.0):
        bx(p, (x - 0.3, x + 0.3), (10.7, 11.2), (17.45, 17.55), WHT, 0.02)
        bx(p, (x - 0.1, x + 0.1), (10.8, 11.1), (17.55, 17.6), BLK, 0.02)
    bx(p, (-55.4, -54.6), (9.7, 10.1), (17.4, 17.55), BLK, 0.02)
    ball(p, (-55, 11.9, 17.0), 1.6, BLK, scale=(1.0, 0.62, 0.32), subdiv=2, jit=0.02)
    bx(p, (-56.6, -53.4), (11.5, 11.8), (17.3, 17.55), WHT, 0.02)
    prism_z(p, [(-56.9, 11.8), (-56.0, 11.8), (-56.6, 13.0)], 16.95, 17.25, (232, 178, 120), 0.03)
    prism_z(p, [(-54.0, 11.8), (-53.1, 11.8), (-53.4, 13.0)], 16.95, 17.25, (232, 178, 120), 0.03)
    # reward coins and money bag
    for (x, y) in ((-62.2, 7.3), (-61.2, 7.3), (-61.7, 7.8)):
        zcyl(p, x, y, 16.85, 17.1, 0.5, GLD, verts=8, jit=0.03)
    ball(p, (-48.2, 7.9, 17.0), 0.95, (200, 160, 70), scale=(1.0, 1.1, 0.4), subdiv=1, jit=0.03)
    bx(p, (-48.6, -47.8), (8.7, 9.0), (16.9, 17.2), BRN, 0.02)
    # lamp rail with three lamps
    bx(p, (-63, -47), (16.3, 16.9), (15.2, 16.8), DGR, 0.03)
    for x in (-60, -55, -50):
        bx(p, (x - 0.15, x + 0.15), (16.0, 16.3), (16.0, 16.3), DGR, 0.02)
        bx(p, (x - 0.7, x + 0.7), (16.35, 16.85), (16.8, 17.4), (255, 232, 150), 0.03)
    for (x, y) in ((-64.6, 6.3), (-45.4, 6.3), (-64.6, 15.7), (-45.4, 15.7)):
        bx(p, (x - 0.15, x + 0.15), (y - 0.15, y + 0.15), (16.6, 16.75), MET, 0.02)


# ---- 13. Impound ---------------------------------------------------------------------------------------------------------------
def build_Impound(p):
    # chain-link fence with an open gate and a POUND sign
    fence_run(p, -92, -58, -24, -24, 3.2, step=8.5, rails=(0.12, 0.97), t=0.16)
    fence_run(p, -92, -92, -24, 0, 3.2, step=8.0, rails=(0.12, 0.97), t=0.16)
    fence_run(p, -58, -58, -24, 0, 3.2, step=8.0, rails=(0.12, 0.97), t=0.16)
    fence_run(p, -92, -80, 0, 0, 3.2, step=6.0, rails=(0.12, 0.97), t=0.16)
    fence_run(p, -70, -58, 0, 0, 3.2, step=6.0, rails=(0.12, 0.97), t=0.16)
    for x in (-80.4, -69.6):
        bx(p, (x - 0.4, x + 0.4), (0, 5.6), (-0.2, 0.2), DGR, 0.03)
    bx(p, (-81, -69), (5.6, 6.8), (-0.25, 0.1), BLU, 0.03)
    text(p, "POUND", -75, 5.85, 0.1, 0.2, 1.2, 0.8, 0.25, 0.4, WHT)
    # tow truck
    bx(p, (-83.5, -70.5), (0.2, 1.4), (-21, -17), BLK, 0.03)
    bx(p, (-84.5, -75.5), (1.4, 3.3), (-21.3, -16.7), YEL, 0.04)
    bx(p, (-74.4, -69.6), (1.4, 5.0), (-21.3, -16.7), YEL, 0.04)
    bx(p, (-69.65, -69.5), (3.2, 4.6), (-20.5, -17.5), GLS, 0.04)
    bx(p, (-73.8, -70.6), (3.2, 4.6), (-16.7, -16.6), GLS, 0.04)
    bx(p, (-73.8, -70.6), (3.2, 4.6), (-21.4, -21.3), GLS, 0.04)
    bx(p, (-73.6, -70.4), (5.0, 5.4), (-19.8, -18.2), ORG, 0.03)
    for x in (-81, -72):
        for z, s in ((-21.1, -1), (-16.9, 1)):
            zcyl(p, x, 1.2, z - 0.4, z + 0.4, 1.2, BLK, verts=6, jit=0.02)
    bx(p, (-80.4, -79.6), (3.3, 6.3), (-19.4, -18.6), DGR, 0.03)
    bar(p, (-80, 6.5, -19), (-85.2, 6.5, -19), 0.55, DGR, 0.03)
    bx(p, (-85.5, -85.0), (3.6, 6.5), (-19.15, -18.85), MET, 0.02)
    bx(p, (-85.8, -84.7), (3.3, 3.7), (-19.3, -18.7), MET, 0.02)
    text(p, "TOW", -80, 1.95, -16.7, -16.55, 1.2, 1.1, 0.28, 0.3, BLK)
    # wrecks: rusty cars, some wheels missing, one crushed
    car(p, -86, -8, length=9.0, width=4.4, orient='x', body=RST, stripe=None, police=False, glass=(70, 50, 40),
        wheels=(1, 0, 0, 1), roof_drop=0.6, details=False)
    car(p, -68, -6, length=9.0, width=4.4, orient='z', body=(110, 118, 135), stripe=None, police=False, glass=(52, 58, 72),
        wheels=(0, 1, 1, 0), details=False)
    car(p, -86, -8, length=8.0, width=4.2, orient='z', body=(96, 128, 112), stripe=None, police=False, glass=(46, 62, 56),
        wheels=(0, 0, 0, 0), roof_drop=1.4, details=False, lift=3.0)
    car(p, -68, -6, length=8.0, width=4.2, orient='x', body=(200, 170, 80), stripe=None, police=False, glass=(80, 70, 40),
        wheels=(0, 0, 0, 0), roof_drop=1.4, details=False, lift=3.0)
    # tyre pile
    for k, y in enumerate((0.45, 1.35)):
        torus(p, (-64, y, -20), 0.85, 0.45, BLK, segs=8, sides=4, jit=0.02)


# ---- 14. Bikes ----------------------------------------------------------------------------------------------------------------
def bike(p, cx, cz):
    """Police motorbike parked along x with its nose toward +x (side view toward the stage)."""
    def B(u0, u1, y0, y1, v0, v1, col, jit=0.03):
        return bx(p, (cx + v0, cx + v1), (y0, y1), (cz + u0, cz + u1), col, jit)
    for v in (1.9, -1.9):
        zcyl(p, cx + v, 0.95, cz - 0.28, cz + 0.28, 0.95, BLK, verts=10, jit=0.02)
        zcyl(p, cx + v, 0.95, cz + 0.28, cz + 0.33, 0.4, MET, verts=6, jit=0.02)
        zcyl(p, cx + v, 0.95, cz - 0.33, cz - 0.28, 0.4, MET, verts=6, jit=0.02)
    # fork and front fender, engine block, tank and fairing, seat, top box with light bar, bags, exhaust
    bar(p, (cx + 1.9, 0.95, cz), (cx + 1.35, 3.0, cz), 0.26, MET, 0.02)
    B(-0.45, 0.45, 1.75, 2.0, 1.4, 2.6, DGR, 0.02)
    B(-0.6, 0.6, 1.1, 2.1, -1.4, 1.0, DGR, 0.03)
    B(-0.75, 0.75, 2.0, 3.0, -0.3, 1.3, WHT, 0.03)
    B(-0.7, 0.7, 2.6, 3.2, -1.7, -0.3, BLK, 0.03)
    B(-0.9, 0.9, 2.75, 3.85, -2.2, -0.9, BLU, 0.03)
    B(-0.5, 0, 3.85, 4.05, -1.9, -1.2, RED, 0.02)
    B(0, 0.5, 3.85, 4.05, -1.9, -1.2, BLU, 0.02)
    B(-0.9, 0.9, 3.0, 3.12, 1.0, 1.45, MET, 0.02)
    B(-0.38, 0.38, 3.1, 3.9, 1.1, 1.3, GLS, 0.03)
    B(-0.3, 0.3, 2.35, 2.85, 2.3, 2.45, YEL, 0.02)
    for su in (-1, 1):
        B(su * 1.0 - 0.15, su * 1.0 + 0.15, 1.5, 2.6, -1.6, -0.2, WHT, 0.03)
        B(su * 0.6 - 0.12, su * 0.6 + 0.12, 1.1, 1.4, -2.9, -0.8, MET, 0.02)


def build_Bikes(p):
    roof = []
    bx(p, (60, 84), (0, 6), (61.4, 62.0), WHT, 0.03)
    bx(p, (60, 84), (0, 0.5), (61.2, 62.2), DGR, 0.03)
    # lean-to roof over the back half (stripes), open front beam on two posts
    for k in range(6):
        x0 = 59.5 + k * 25 / 6
        roof.append(bx(p, (x0, x0 + 25 / 6), (6.1, 6.7), (58.6, 62.5), BLU if k % 2 == 0 else WHT, 0.03))
    roof.append(bx(p, (59.5, 84.5), (6.1, 6.7), (54.1, 54.7), NAVY, 0.03))
    for x in (60.5, 72, 83.5):
        roof.append(bx(p, (x - 0.3, x + 0.3), (5.7, 6.1), (54.1, 62.5), NAVY, 0.03))
    for (x, z) in ((60.5, 54.8), (83.5, 54.8)):
        vcyl(p, x, 0, 6.1, z, 0.4, MET, verts=6, jit=0.03)
    # POLICE on the inside face of the back wall (the side the stage sees)
    text(p, "POLICE", 72, 2.7, 61.25, 61.4, 1.3, 1.7, 0.36, 0.4, BLU, mirror=True)
    for x in (65.5, 72.5, 79.5):
        bike(p, x, 56.3)


# ---- 15. Monument ---------------------------------------------------------------------------------------------------------------
def build_Monument(p):
    bx(p, (-31.5, -16.5), (0, 1.2), (-7.5, 7.5), CONL, 0.04)
    bx(p, (-29.5, -18.5), (1.2, 2.2), (-5.5, 5.5), CON, 0.04)
    bx(p, (-27, -21), (2.2, 10.2), (-3, 3), NAVY, 0.03)
    for y in (2.2, 9.7):
        bx(p, (-27.25, -20.75), (y, y + 0.5), (-3.25, 3.25), GLD, 0.03)
    bx(p, (-25.8, -22.2), (6.3, 8.3), (3.0, 3.15), (36, 56, 110), 0.03)
    text(p, "BONK", -24, 6.6, 3.15, 3.3, 0.78, 1.4, 0.24, 0.2, GLD)
    bx(p, (-27.7, -20.3), (10.2, 11.0), (-3.7, 3.7), GLD, 0.03)
    # the golden badge: eight-pointed star with ball tips, blue disc and white star
    star_poly(p, (-24, 17.5, 0), 'xy', 5.7, 3.7, 1.2, GLD, n=8, rot0=90)
    for k in range(8):
        a = math.radians(90 + 45 * k)
        vcyl_x, vcyl_y = -24 + 5.8 * math.cos(a), 17.5 + 5.8 * math.sin(a)
        ball(p, (vcyl_x, vcyl_y, 0), 0.72, GLD, scale=(1, 1, 0.85), subdiv=1, jit=0.03)
    zcyl(p, -24, 17.5, -0.6, 0.9, 3.7, (205, 150, 30), verts=16, jit=0.02)
    zcyl(p, -24, 17.5, 0.5, 1.25, 3.0, BLU, verts=16, jit=0.02)
    star_poly(p, (-24, 17.5, 1.25), 'xy', 2.4, 1.0, 0.2, WHT, n=5)
    # four lamp posts
    for (x, z) in ((-32, -8), (-16, -8), (-32, 8), (-16, 8)):
        vcyl(p, x, 0, 0.5, z, 0.7, DGR, verts=8, jit=0.02)
        vcyl(p, x, 0.5, 4.8, z, 0.3, DGR, verts=6, jit=0.02)
        ball(p, (x, 5.6, z), 0.8, YEL, subdiv=2, jit=0.02)
        vcyl(p, x, 4.8, 5.0, z, 0.55, DGR, verts=8, jit=0.02)


PARTS = [("Floor", build_Floor), ("Station", build_Station), ("Cars", build_Cars), ("Cells", build_Cells),
         ("Donuts", build_Donuts), ("Beacon", build_Beacon), ("Range", build_Range), ("Kennel", build_Kennel),
         ("Heli", build_Heli), ("Roadblock", build_Roadblock), ("Swat", build_Swat), ("Wanted", build_Wanted),
         ("Impound", build_Impound), ("Bikes", build_Bikes), ("Monument", build_Monument)]

# reference Shiba in each preview: (x, z, facing, lift)
AZ = {"Kennel": 30, "Bikes": 30}
ELEV = {"Bikes": 36}
MULT = {"Floor": 1.5, "Station": 2.4, "Range": 2.6, "Impound": 2.6, "Heli": 2.2, "Monument": 2.4, "Beacon": 2.6}
SHIBA_AT = {"Floor": (-48, 52, 270, 0), "Station": (58, -34, 270, 0.5), "Cars": (-56, 50, 270, 0), "Cells": (-60, -40, 270, 0),
            "Donuts": (38, 6, 270, 0), "Beacon": (14, 6, 270, 0), "Range": (50, 42, 270, 0), "Kennel": (66, 1, 90, 0),
            "Heli": (-24, -44, 270, 0.5), "Roadblock": (12, 53, 270, 0), "Swat": (34, -48, 270, 0), "Wanted": (-42, 16, 270, 0),
            "Impound": (-54, -4, 270, 0), "Bikes": (90, 48, 90, 0), "Monument": (-10, 6, 270, 0)}


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


def flip_image(path):
    """Mirror a render left-right: the stage frame is a reflection of the Blender frame, so this is the in-game handedness."""
    import numpy as np
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[:, ::-1, :].copy()
    im.pixels.foreach_set(px.reshape(-1))
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


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
    # no flip: the mirrored scene seen from the road side is what the game shows (text reads correctly)
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
    roofs = [m for ms in built.values() for m in ms if m.name.endswith("_Roof")]
    dk.hide(roofs, True)
    snap([m for m in allm if m not in roofs], shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    dk.hide(roofs, False)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_PoliceStation.png"))


main()
