"""Final low-poly decor models for the theme RobotFactory (20 parts around the thirteenth Shiba, Robot Shiba).

Usage: blender --background --factory-startup --python build_RobotFactory.py -- <outdir> [PartId ...]
Writes Decor_RobotFactory_<PartId>.fbx, preview_<PartId>.png and stage_RobotFactory.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then). Models are built unrotated: the game applies the part's Yaw.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "RobotFactory"))
ONLY = ARGS[1:]
KEY = "RobotFactory"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_RobotFactory.json"))
RND = random.Random(13)

# ---- palette (shared by all 20 parts) ---------------------------------------------------------------------------------
STL = (150, 160, 176)    # steel
STLD = (110, 120, 136)   # shaded steel
STLL = (196, 204, 216)   # bright steel
DRK = (52, 58, 70)       # dark metal
DRK2 = (34, 38, 48)      # near black
CON = (122, 124, 130)    # concrete
CONL = (156, 158, 164)
FLR = (86, 90, 98)       # factory floor
FLRD = (66, 70, 78)
PLT = (108, 112, 120)    # steel plate
YEL = (255, 200, 30)     # hazard yellow
ORG = (255, 120, 30)     # robot orange
CYN = (110, 215, 240)    # screens, lamps
CYND = (60, 150, 190)
GLS = (150, 210, 232)    # glass
BRK = (150, 82, 62)      # brick
BRKD = (122, 64, 50)
WHT = (226, 230, 238)
RED = (214, 60, 52)
REDD = (160, 40, 40)
RST = (150, 92, 56)      # rust
RSTD = (110, 66, 40)
DIRT = (104, 88, 70)
CRT = (196, 154, 92)     # crate wood
CRTD = (150, 112, 62)
GRN = (96, 200, 120)
BLU = (70, 120, 200)
NAVY = DRK
MET = STL
COP = (200, 120, 70)     # copper
PNK = (240, 150, 190)    # brain


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



# ---- extra helpers for this theme ---------------------------------------------------------------------------------------
def bc(p, cx, cy, cz, sx, sy, sz, col, jit=0.04, rot=(0, 0, 0)):
    """Box from centre and size (stage axes)."""
    return dk.box(p, (cx, cy, cz), (sx, sy, sz), col, rot=rot, jitter=jit)


def annulus(p, c, axis, r0, r1, a, b, col, n=24, t0=0.0, t1=360.0, jit=0.03):
    """Ring (r0 inner, r1 outer) between a and b along `axis`. axis 'z': ring in the x-y plane around c=(x, y), z from a to b.
    axis 'y': ring in the x-z plane around c=(x, z), y from a to b (stage angle t: x = cos t, z = -sin t). t0..t1 degrees = partial ring."""
    full = abs((t1 - t0) - 360.0) < 1e-6
    steps = n if full else n + 1
    pts, faces = [], []
    for i in range(steps):
        th = math.radians(t0 + (t1 - t0) * i / n)
        co, si = math.cos(th), math.sin(th)
        for (r, h) in ((r0, a), (r1, a), (r1, b), (r0, b)):
            if axis == 'z':
                pts.append((r * co, r * si, h))
            else:
                pts.append((r * co, h, -r * si))
    last = steps if full else steps - 1
    for i in range(last):
        j = (i + 1) % steps
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((4 * i + k, 4 * i + k2, 4 * j + k2, 4 * j + k))
    if not full:
        faces.append((0, 1, 2, 3))
        e = 4 * (steps - 1)
        faces.append((e, e + 1, e + 2, e + 3))
    origin = (c[0], 0, c[1]) if axis == 'z' and False else None
    if axis == 'z':
        return dk.poly(p, (c[0], c[1], 0), pts, faces, col, jit)
    return dk.poly(p, (c[0], 0, c[1]), pts, faces, col, jit)


def radial(p, cx, cz, r, theta, y0, y1, length, width, col, jit=0.03):
    """Box lying on the ground plane, its long side pointing along the stage angle theta (degrees, x = cos, z = -sin), centre at radius r."""
    th = math.radians(theta)
    return dk.box(p, (cx + r * math.cos(th), (y0 + y1) / 2, cz - r * math.sin(th)), (length, y1 - y0, width), col,
                  rot=(0, theta, 0), jitter=jit)


def cog(p, cx, cy, z0, z1, rb, tooth, n, col, hole=0.0, tcol=None, spokes=0, spoke_col=None, hub=0.0, hub_col=None, seg=28):
    """Cog wheel standing in the x-y plane (axis z) around (cx, cy). rb = body radius, teeth stick out `tooth`."""
    annulus(p, (cx, cy), 'z', hole, rb, z0, z1, col, n=seg)
    tw = 2 * math.pi * rb / n * 0.5
    for k in range(n):
        a = 360.0 * k / n
        th = math.radians(a)
        dk.box(p, (cx + (rb + tooth / 2 - 0.05) * math.cos(th), cy + (rb + tooth / 2 - 0.05) * math.sin(th), (z0 + z1) / 2),
               (tooth + 0.1, tw, z1 - z0), tcol or col, rot=(0, 0, a), jitter=0.03)
    if spokes:
        h0 = hub or hole
        ln = rb - h0 + 0.1
        rm = (h0 + rb) / 2
        for k in range(spokes):
            a = 360.0 * k / spokes + 15
            th = math.radians(a)
            dk.box(p, (cx + rm * math.cos(th), cy + rm * math.sin(th), (z0 + z1) / 2), (ln, tw * 0.9, z1 - z0), spoke_col or col,
                   rot=(0, 0, a), jitter=0.03)
    if hub:
        dk.cyl(p, (cx, cy, (z0 + z1) / 2), hub, z1 - z0 + 0.25, hub_col or col, axis='z', verts=12, jitter=0.03)


def hazard_x(p, x0, x1, y0, y1, z0, z1, n, c1=YEL, c2=DRK2):
    """Alternating yellow/dark blocks along x."""
    w = (x1 - x0) / n
    for i in range(n):
        bx(p, (x0 + i * w, x0 + (i + 1) * w), (y0, y1), (z0, z1), c1 if i % 2 == 0 else c2, 0.02)


def hazard_y(p, x0, x1, y0, y1, z0, z1, n, c1=YEL, c2=DRK2):
    """Alternating yellow/dark blocks along y (vertical post bands)."""
    h = (y1 - y0) / n
    for i in range(n):
        bx(p, (x0, x1), (y0 + i * h, y0 + (i + 1) * h), (z0, z1), c1 if i % 2 == 0 else c2, 0.02)


def bolts_z(p, xs, y, z, r=0.2, col=STLL, depth=0.15):
    for x in xs:
        dk.cyl(p, (x, y, z + depth / 2), r, depth, col, axis='z', verts=6, jitter=0.02)


def rung_ladder(p, x, z, y0, y1, w=1.2, col=STLD, step=0.9, axis='z', t=0.16):
    """Ladder on a face. axis 'z' = ladder in the x-y plane at depth z, 'x' = in the y-z plane at x."""
    if axis == 'z':
        bx(p, (x - w / 2 - t / 2, x - w / 2 + t / 2), (y0, y1), (z - t / 2, z + t / 2), col, 0.02)
        bx(p, (x + w / 2 - t / 2, x + w / 2 + t / 2), (y0, y1), (z - t / 2, z + t / 2), col, 0.02)
        y = y0 + step / 2
        while y < y1:
            bx(p, (x - w / 2, x + w / 2), (y - t / 2, y + t / 2), (z - t / 2, z + t / 2), col, 0.02)
            y += step
    else:
        bx(p, (x - t / 2, x + t / 2), (y0, y1), (z - w / 2 - t / 2, z - w / 2 + t / 2), col, 0.02)
        bx(p, (x - t / 2, x + t / 2), (y0, y1), (z + w / 2 - t / 2, z + w / 2 + t / 2), col, 0.02)
        y = y0 + step / 2
        while y < y1:
            bx(p, (x - t / 2, x + t / 2), (y - t / 2, y + t / 2), (z - w / 2, z + w / 2), col, 0.02)
            y += step


def sphere_pts(p, c, r, col, sc=(1, 1, 1), sub=2, jit=0.03):
    return dk.ball(p, c, r, col, scale=sc, subdiv=sub, jitter=jit)


def bolt_zig(p, a, b, t, col, n=4, amp=0.5, jit=0.02):
    """Zig-zag spark between two stage points."""
    a, b = Vector(a), Vector(b)
    prev = a
    for i in range(1, n + 1):
        q = a + (b - a) * (i / n)
        if i < n:
            q = q + Vector((amp * (1 if i % 2 else -1), 0, amp * 0.5 * (-1 if i % 2 else 1)))
        bar(p, tuple(prev), tuple(q), t, col, jit)
        prev = q


def union(part_json):
    """Union box of the blueprint pieces (rotated pieces by the bounds of their rotated box, like the validator)."""
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = q["Size"]; o = q["Offset"]; r = q.get("Rotation") or (0, 0, 0)
        ax, ay, az = (math.radians(a) for a in r)
        cx_, sx_, cy_, sy_, cz_, sz_ = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
        Rx = Matrix(((1, 0, 0), (0, cx_, -sx_), (0, sx_, cx_)))
        Ry = Matrix(((cy_, 0, sy_), (0, 1, 0), (-sy_, 0, cy_)))
        Rz = Matrix(((cz_, -sz_, 0), (sz_, cz_, 0), (0, 0, 1)))
        m = Ry @ Rx @ Rz
        half = [abs(m[i][0]) * s[0] / 2 + abs(m[i][1]) * s[1] / 2 + abs(m[i][2]) * s[2] / 2 for i in range(3)]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - half[i]); hi[i] = max(hi[i], o[i] + half[i])
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



ORDER = ["Floor", "Hall", "Sign", "Conveyor", "Welder", "Smokestack", "Silos", "Booth", "Gears", "Statue", "Generator",
         "Forklift", "Pipes", "Crane", "Charging", "Press", "Drones", "Scrap", "Lab", "GiantRobot"]

# ---- 1. Floor ------------------------------------------------------------------------------------------------------------
PATH = [(0, 65), (52, 46), (6, 14), (-44, -14), (-34, -48), (0, -65)]
SHX, SHZ = -4, -14


def build_Floor(p):
    bx(p, (-95, 95), (0, 0.30), (-65, 65), FLR, 0.05)
    for x in range(-76, 90, 19):
        bx(p, (x - 0.15, x + 0.15), (0.30, 0.33), (-65, 65), FLRD, 0.02)
    for z in (-44, -22, 0, 22, 44):
        bx(p, (-95, 95), (0.30, 0.33), (z - 0.15, z + 0.15), FLRD, 0.02)
    # steel apron plates
    bx(p, (32, 88), (0.30, 0.42), (-60, -20), PLT, 0.05)
    bx(p, (7, 33), (0.30, 0.42), (-45, -23), PLT, 0.05)
    bx(p, (-91, -61), (0.30, 0.42), (-27, 3), PLT, 0.05)
    bx(p, (64, 88), (0.30, 0.42), (8, 32), PLT, 0.05)
    bx(p, (-72, -44), (0.30, 0.42), (-1, 21), DIRT, 0.08)
    # hazard edge of the hall apron and the door ramp
    hazard_x(p, 32, 88, 0.42, 0.45, -20.7, -20.0, 10)
    bx(p, (50, 66), (0.42, 0.45), (-27, -22), DRK2, 0.02)
    for i in range(6):
        bc(p, 52 + 2.4 * i, 0.465, -24.5, 4.2, 0.03, 0.8, YEL, 0.02, rot=(0, 45, 0))
    # welder apron outline, dirt tracks
    bx(p, (65, 87), (0.42, 0.45), (9, 9.5), YEL, 0.02)
    bx(p, (65, 87), (0.42, 0.45), (30.5, 31), YEL, 0.02)
    bx(p, (65, 65.5), (0.42, 0.45), (9, 31), YEL, 0.02)
    bx(p, (86.5, 87), (0.42, 0.45), (9, 31), YEL, 0.02)
    bx(p, (-71, -45), (0.42, 0.45), (4, 5.4), RSTD, 0.03)
    bx(p, (-71, -45), (0.42, 0.45), (11, 12.4), RSTD, 0.03)
    # guide lines along both sides of the walkway
    for i, ((x1, z1), (x2, z2)) in enumerate(zip(PATH[:-1], PATH[1:])):
        dx, dz = x2 - x1, z2 - z1
        ln = math.hypot(dx, dz)
        ux, uz = dx / ln, dz / ln
        ang = math.degrees(math.atan2(-dz, dx))
        f0 = 0.5 if i == 0 else 0.03
        f1 = 0.5 if i == len(PATH) - 2 else 0.97
        fm = (f0 + f1) / 2
        for s in (-1, 1):
            nx, nz = -uz * 6.4 * s, ux * 6.4 * s
            bc(p, x1 + dx * fm + nx, 0.315, z1 + dz * fm + nz, ln * (f1 - f0), 0.03, 0.5, YEL, 0.02, rot=(0, ang, 0))
    # oil stains and a cable trench
    for (x, z, a, b) in ((46, 2, 5, 3), (-28, -30, 4, 2.5), (-60, 26, 4, 3)):
        bc(p, x, 0.31, z, a, 0.02, b, FLRD, 0.02, rot=(0, 20, 0))
    bx(p, (-18, -14), (0.30, 0.36), (-60, -30), DRK2, 0.02)
    for i in range(4):
        bx(p, (-18, -14), (0.36, 0.40), (-58 + i * 7, -57.4 + i * 7), STLD, 0.02)
    # manholes
    for (x, z) in ((-30, 38), (40, 52)):
        vcyl(p, x, 0.30, 0.36, z, 1.4, STLD, verts=10, jit=0.03)
    # the turntable of the Robot Shiba
    vcyl(p, SHX, 0.30, 0.42, SHZ, 12.2, STL, verts=32, jit=0.03)
    for k in range(16):
        radial(p, SHX, SHZ, 12.6, 22.5 * k, 0.30, 0.42, 0.8, 1.5, STLD)
    for k in range(8):
        radial(p, SHX, SHZ, 10.4, 45 * k + 22.5, 0.42, 0.44, 3.6, 0.4, DRK2, 0.02)
    for k in range(12):
        annulus(p, (SHX, SHZ), 'y', 5.6, 8.5, 0.42, 0.54, YEL if k % 2 == 0 else DRK2, n=1, t0=30 * k, t1=30 * k + 30, jit=0.02)
    vcyl(p, SHX, 0.42, 0.50, SHZ, 5.4, DRK, verts=20, jit=0.03)


# ---- 2. Hall -----------------------------------------------------------------------------------------------------------
def build_Hall(p):
    bx(p, (37, 83), (0, 14), (-56, -54.8), STL)
    bx(p, (37, 38.2), (0, 14), (-56, -28), STL)
    bx(p, (81.8, 83), (0, 14), (-56, -28), STL)
    bx(p, (37, 50), (0, 14), (-29.2, -28), STL)
    bx(p, (66, 83), (0, 14), (-29.2, -28), STL)
    bx(p, (50, 66), (10, 14), (-29.2, -28), DRK)
    # plinth, corner columns, door frame
    bx(p, (36.8, 50), (0, 1.4), (-29.4, -27.8), DRK)
    bx(p, (66, 83.2), (0, 1.4), (-29.4, -27.8), DRK)
    bx(p, (36.8, 38.4), (0, 1.4), (-56, -29.4), DRK)
    bx(p, (81.6, 83.2), (0, 1.4), (-56, -29.4), DRK)
    for (x0, x1, z0, z1) in ((36.8, 38.6, -56.2, -54.4), (81.4, 83.2, -56.2, -54.4), (36.8, 38.6, -29.4, -27.8), (81.4, 83.2, -29.4, -27.8)):
        bx(p, (x0, x1), (1.4, 14.8), (z0, z1), STLD)
    hazard_y(p, 49.2, 50.0, 0, 10, -28.0, -27.8, 10)
    hazard_y(p, 66.0, 66.8, 0, 10, -28.0, -27.8, 10)
    # corrugation ribs on the front and the side faces
    for x in (41.9, 47.9, 70.9, 76.9):
        bx(p, (x - 0.15, x + 0.15), (1.4, 13.6), (-28.15, -28.0), STLD, 0.03)
    for z in ():
        bx(p, (36.85, 37.0), (1.4, 13.6), (z - 0.15, z + 0.15), STLD, 0.03)
        bx(p, (83.0, 83.15), (1.4, 13.6), (z - 0.15, z + 0.15), STLD, 0.03)
    # windows
    for (a, b) in ((39, 43), (44.5, 48.5), (68, 72), (73.5, 77.5)):
        window_z(p, a, b, 7.2, 11.0, -28.0, d=0.2, mull=False, frame=DRK, glass=GLS)
    for (a, b) in ((-53, -48), (-45, -40), (-37, -32)):
        window_x(p, 37.0, -1, 7.2, 11.0, a, b, d=0.2, frame=DRK, glass=GLS)
        window_x(p, 83.0, 1, 7.2, 11.0, a, b, d=0.2, frame=DRK, glass=GLS)
    # the rolled-up roller door
    for i in range(5):
        bx(p, (50.2, 65.8), (6.9 + 0.62 * i, 7.4 + 0.62 * i), (-28.9, -28.4), STLL if i % 2 == 0 else STL, 0.03)
    bx(p, (50.2, 65.8), (6.4, 6.8), (-28.95, -28.35), YEL, 0.02)
    bx(p, (50.0, 50.5), (0, 10), (-28.9, -28.4), DRK, 0.02)
    bx(p, (65.5, 66.0), (0, 10), (-28.9, -28.4), DRK, 0.02)
    # lintel lettering
    text(p, "ROBOTS", 58, 10.6, -28.0, -27.7, 1.7, 2.6, 0.5, 0.55, CYN)
    # inside: dark back wall, a robot arm and a car body on the line
    bx(p, (38.2, 81.8), (0.4, 13.6), (-54.8, -54.6), DRK2, 0.02)
    vcyl(p, 58, 0.0, 1.2, -48, 1.8, DRK, verts=10)
    bar(p, (58, 1.2, -48), (58, 5.2, -46), 0.9, YEL)
    bar(p, (58, 5.2, -46), (58, 7.2, -42), 0.8, YEL)
    bx(p, (52, 64), (0.4, 1.6), (-42, -35), RED)
    bx(p, (54, 62), (1.6, 3.0), (-40.5, -36.5), DRK)
    # pipe along the left wall
    zcyl(p, 37.0, 5.5, -55, -30, 0.35, ORG, verts=8)
    vcyl(p, 37.0, 0, 5.5, -30, 0.35, ORG, verts=8)
    for z in (-46,):
        bx(p, (36.8, 37.5), (5.1, 5.9), (z - 0.2, z + 0.2), DRK, 0.02)
    mark = len(p.objs)
    # roof with saw-tooth skylights, parapet, vent and air units
    bx(p, (36.6, 83.4), (14, 14.8), (-56.4, -27.6), DRK)
    bx(p, (36.6, 83.4), (14.8, 15.3), (-27.9, -27.6), YEL, 0.02)
    bx(p, (36.6, 36.9), (14.8, 15.3), (-56.4, -27.9), STLD, 0.02)
    bx(p, (83.1, 83.4), (14.8, 15.3), (-56.4, -27.9), STLD, 0.02)
    bx(p, (36.9, 83.1), (14.8, 15.3), (-56.4, -56.1), STLD, 0.02)
    for x0 in (41, 55, 69):
        prism_z(p, [(x0, 14.8), (x0 + 10, 14.8), (x0, 18.0)], -54.6, -29.4, STLL)
        bx(p, (x0 - 0.2, x0), (14.8, 18.0), (-54.4, -29.6), GLS, 0.03)
    bx(p, (78.2, 81.8), (14.8, 18.0), (-53.8, -50.2), STLD)
    bx(p, (78.0, 82.0), (18.0, 18.4), (-54.0, -50.0), STL)
    for y in (16.6,):
        bx(p, (78.5, 81.5), (y, y + 0.25), (-50.2, -50.05), DRK2, 0.02)
    bx(p, (62, 67), (14.8, 16.6), (-34, -31), STL)
    vcyl(p, 64.5, 16.6, 16.8, -32.5, 1.1, DRK2, verts=10)
    bx(p, (44, 48), (14.8, 16.2), (-50, -47), STL)
    return {"Body": p.objs[:mark], "Roof": p.objs[mark:]}


# ---- 3. Sign --------------------------------------------------------------------------------------------------------------
def build_Sign(p):
    for x in (-72.5, -47.5):
        bx(p, (x - 1.5, x + 1.5), (0, 1), (48.5, 51.5), CON)
        for dx in (-1.0, 1.0):
            for dz in (-1.0, 1.0):
                bx(p, (x + dx - 0.2, x + dx + 0.2), (1, 1.25), (50 + dz - 0.2, 50 + dz + 0.2), STLL, 0.02)
        vcyl(p, x, 1, 9.8, 50, 0.7, STL, verts=10)
        bar(p, (x + (1.2 if x < -60 else -1.2), 1.0, 49.0), (x, 8.8, 49.0), 0.45, STLD)
    # catwalk with railing along the front
    bx(p, (-74, -46), (8.4, 8.8), (48.8, 51.2), DRK)
    bx(p, (-74, -46), (9.6, 9.8), (51.0, 51.2), STL, 0.02)
    for x in range(-74, -45, 4):
        bx(p, (x - 0.1, x + 0.1), (8.8, 9.7), (51.0, 51.2), STL, 0.02)
    # the board
    bx(p, (-75, -45), (9, 18), (49.4, 50.6), DRK)
    bx(p, (-75.5, -44.5), (18, 18.8), (49.2, 50.8), YEL)
    bx(p, (-74.6, -45.4), (9.3, 9.6), (50.6, 50.85), CYND, 0.02)
    hazard_x(p, -74.6, -45.4, 9.6, 10.4, 50.6, 50.85, 30)
    bx(p, (-74.6, -74.2), (10.4, 17.6), (50.6, 50.85), CYND, 0.02)
    bx(p, (-45.8, -45.4), (10.4, 17.6), (50.6, 50.85), CYND, 0.02)
    bx(p, (-74.6, -45.4), (17.2, 17.6), (50.6, 50.85), CYND, 0.02)
    text(p, "BONK", -59.6, 10.9, 50.6, 51.05, 5.3, 6.0, 1.3, 1.3, CYND)
    text(p, "BONK", -60, 11.1, 50.85, 51.4, 5.3, 6.0, 1.3, 1.3, YEL)
    for x in (-70, -63.3, -56.7, -50):
        bx(p, (x - 1.1, x + 1.1), (17.0, 17.9), (50.6, 51.5), DRK2, 0.02)
        bx(p, (x - 0.8, x + 0.8), (16.85, 17.0), (50.7, 51.4), YEL, 0.02)
    for x in (-70, -60, -50):
        bx(p, (x - 0.3, x + 0.3), (9, 18), (48.8, 49.4), STLD, 0.03)
    bolts_z(p, (-74, -45.9), 17.2, 50.6)
    bolts_z(p, (-74, -45.9), 9.9, 50.6)


# ---- 4. Conveyor ------------------------------------------------------------------------------------------------------------
def crate(p, cx, cz, y0, s, col, tape=YEL):
    bc(p, cx, y0 + s / 2, cz, s, s, s, col, 0.05)
    bx(p, (cx - 0.25, cx + 0.25), (y0 + 0.02, y0 + s + 0.05), (cz - s / 2 - 0.05, cz + s / 2 + 0.05), tape, 0.02)
    bx(p, (cx - s / 2 - 0.05, cx + s / 2 + 0.05), (y0 + 0.02, y0 + s + 0.05), (cz - 0.25, cz + 0.25), tape, 0.02)
    bx(p, (cx - s / 2 + 0.3, cx - s / 2 + 1.0), (y0 + 0.4, y0 + 1.0), (cz + s / 2, cz + s / 2 + 0.06), WHT, 0.02)


def mini_bot(p, cx, cz, y0, col=STL, eye=CYN):
    bx(p, (cx - 0.8, cx + 0.8), (y0 + 0.3, y0 + 1.7), (cz - 0.8, cz + 0.8), col)
    bx(p, (cx - 0.65, cx + 0.65), (y0 + 1.7, y0 + 2.7), (cz - 0.65, cz + 0.65), col)
    bx(p, (cx - 0.5, cx + 0.5), (y0 + 2.0, y0 + 2.4), (cz + 0.65, cz + 0.72), eye, 0.02)
    bx(p, (cx - 1.1, cx - 0.8), (y0 + 0.8, y0 + 1.6), (cz - 0.3, cz + 0.3), DRK)
    bx(p, (cx + 0.8, cx + 1.1), (y0 + 0.8, y0 + 1.6), (cz - 0.3, cz + 0.3), DRK)
    bx(p, (cx - 0.05, cx + 0.05), (y0 + 2.7, y0 + 2.95), (cz - 0.05, cz + 0.05), ORG, 0.02)
    bx(p, (cx - 0.6, cx + 0.6), (y0, y0 + 0.3), (cz - 0.6, cz + 0.6), DRK)


def build_Conveyor(p):
    bx(p, (26, 62), (0.9, 1.7), (-10, -6), DRK)
    for x in (26.9, 61.1):
        zcyl(p, x, 1.45, -9.8, -6.2, 0.9, STLD, verts=10)
    bx(p, (27.4, 60.6), (1.7, 1.95), (-9.6, -6.4), DRK2, 0.02)
    for i in range(8):
        x = 30 + 3.8 * i
        bar(p, (x - 0.7, 1.99, -9.0), (x + 0.5, 1.99, -8.0), 0.22, STLL, 0.02)
        bar(p, (x - 0.7, 1.99, -7.0), (x + 0.5, 1.99, -8.0), 0.22, STLL, 0.02)
    bx(p, (26, 62), (1.7, 2.75), (-10.25, -9.75), YEL, 0.03)
    bx(p, (26, 62), (1.7, 2.75), (-6.25, -5.75), YEL, 0.03)
    for x in range(28, 62, 6):
        bx(p, (x - 0.25, x + 0.25), (0.9, 1.7), (-10.25, -9.7), DRK, 0.02)
        bx(p, (x - 0.25, x + 0.25), (0.9, 1.7), (-6.3, -5.75), DRK, 0.02)
    for x in (28.5, 44, 59.5):
        for z in (-9.6, -6.4):
            bx(p, (x - 0.6, x + 0.6), (0, 0.9), (z - 0.2, z + 0.2), DRK, 0.03)
        bx(p, (x - 0.6, x + 0.6), (0.45, 0.8), (-9.6, -6.4), DRK, 0.03)
    crate(p, 33, -8, 2.1, 2.6, CRT)
    crate(p, 39, -8, 2.1, 2.6, ORG, STLL)
    mini_bot(p, 50, -8, 2.0, STL)
    mini_bot(p, 56, -8, 2.0, WHT, YEL)


# ---- 5. Welder -----------------------------------------------------------------------------------------------------------------
def build_Welder(p):
    bx(p, (69, 83), (0, 0.4), (13, 27), DRK)
    bx(p, (69.4, 82.6), (0.4, 0.46), (13.4, 13.9), YEL, 0.02)
    bx(p, (69.4, 69.9), (0.4, 0.46), (13.4, 26.6), YEL, 0.02)
    bx(p, (82.1, 82.6), (0.4, 0.46), (13.4, 26.6), YEL, 0.02)
    # safety cage: posts, top frame, mesh on three sides
    for (x, z) in ((69.3, 13.3), (82.7, 13.3), (69.3, 26.7), (82.7, 26.7)):
        vcyl(p, x, 0.4, 9.0, z, 0.35, STL, verts=8)
        vcyl(p, x, 0.4, 1.2, z, 0.5, DRK, verts=8)
    bx(p, (69.0, 83.0), (9.0, 9.6), (13.0, 13.6), YEL)
    bx(p, (69.0, 83.0), (9.0, 9.6), (26.4, 27.0), YEL)
    bx(p, (69.0, 69.6), (9.0, 9.6), (13.6, 26.4), YEL)
    bx(p, (82.4, 83.0), (9.0, 9.6), (13.6, 26.4), YEL)
    for i in range(7):
        x = 70.4 + i * 1.95
        bx(p, (x - 0.06, x + 0.06), (0.4, 9.0), (13.25, 13.37), STLD, 0.02)
    for i in range(7):
        z = 14.9 + i * 1.8
        bx(p, (69.24, 69.36), (0.4, 9.0), (z - 0.06, z + 0.06), STLD, 0.02)
        bx(p, (82.64, 82.76), (0.4, 9.0), (z - 0.06, z + 0.06), STLD, 0.02)
    for y in (3.2, 6.2):
        bx(p, (69.6, 82.4), (y, y + 0.12), (13.25, 13.37), STLD, 0.02)
        bx(p, (69.24, 69.36), (y, y + 0.12), (13.6, 26.4), STLD, 0.02)
        bx(p, (82.64, 82.76), (y, y + 0.12), (13.6, 26.4), STLD, 0.02)
    bx(p, (69.6, 74.5), (3.2, 3.32), (26.63, 26.75), STLD, 0.02)
    bx(p, (69.6, 74.5), (6.2, 6.32), (26.63, 26.75), STLD, 0.02)
    # robot arm
    vcyl(p, 76, 0.4, 2.6, 17, 2.0, DRK, verts=12)
    vcyl(p, 76, 2.6, 2.9, 17, 1.6, YEL, verts=12)
    vcyl(p, 76, 2.9, 5.6, 17, 0.9, YEL, verts=10)
    xcyl(p, 75.0, 77.0, 5.8, 17, 1.0, DRK, verts=10)
    bar(p, (76, 5.8, 17), (76, 8.4, 19.8), 1.1, YEL)
    xcyl(p, 75.2, 76.8, 8.4, 19.8, 0.8, DRK, verts=10)
    bar(p, (76, 8.4, 19.8), (76, 6.0, 23.0), 0.9, YEL)
    bx(p, (75.5, 76.5), (5.4, 6.2), (22.8, 23.5), DRK)
    bar(p, (76, 5.6, 23.2), (76, 4.5, 23.6), 0.45, STLL)
    for (dx, dy, dz) in ((0.5, 0.1, 0.1), (-0.6, 0.3, -0.2), (0.3, 0.6, 0.5), (-0.3, 0.1, 0.6), (0.8, 0.5, -0.3)):
        bc(p, 76 + dx, 4.1 + dy, 23.6 + dz, 0.3, 0.3, 0.3, ORG, 0.02, rot=(30, 40, 20))
    bolt_zig(p, (76, 4.3, 23.6), (77.4, 5.6, 24.3), 0.16, YEL, 3, 0.3)
    # work table with a half-built robot torso
    bx(p, (73.5, 78.5), (0.4, 3.6), (22.1, 25.1), STL)
    bx(p, (73.3, 78.7), (3.6, 4.0), (21.9, 25.3), DRK)
    bx(p, (74.8, 77.2), (4.0, 5.2), (22.7, 24.3), ORG)
    bx(p, (75.3, 76.7), (5.2, 5.6), (23.0, 24.0), STL)
    hazard_x(p, 73.5, 78.5, 0.4, 1.0, 25.1, 25.15, 8)
    # control cabinet with screen and beacon
    bx(p, (70, 72.2), (0.4, 3.6), (13.6, 15.4), DRK)
    bx(p, (70.3, 71.9), (2.0, 3.2), (15.4, 15.5), CYN, 0.02)
    bx(p, (70.3, 71.9), (1.2, 1.7), (15.4, 15.5), RED, 0.02)
    vcyl(p, 71.1, 3.6, 4.2, 14.5, 0.35, RED, verts=8)

PNKL = (250, 184, 212)
SMK1, SMK2, SMK3 = (170, 172, 178), (192, 194, 200), (150, 152, 160)


# ---- 6. Smokestack -------------------------------------------------------------------------------------------------------------
def build_Smokestack(p):
    cx, cz = 18, -54
    bx(p, (13, 23), (0, 3), (-59, -49), CON)
    bx(p, (12.8, 23.2), (2.6, 3.0), (-59.2, -48.8), CONL, 0.03)
    for (x, z) in ((13.4, -58.6), (22.6, -58.6), (13.4, -49.4), (22.6, -49.4)):
        vcyl(p, x, 3.0, 3.3, z, 0.35, STLL, verts=6, jit=0.02)
    # chimney: brick foot, then red / white bands, slightly tapering
    def rad(y):
        return 2.9 - 0.55 * (y - 3) / 27

    bounds = [3, 12, 15, 18, 21, 24, 27, 29.6]
    cols = [BRK, WHT, RED, WHT, RED, WHT, RED]
    for i, c in enumerate(cols):
        vcyl(p, cx, bounds[i], bounds[i + 1], cz, rad(bounds[i]), c, verts=12, top_r=rad(bounds[i + 1]))
    for y in (5.2, 7.4, 9.6):
        vcyl(p, cx, y, y + 0.35, cz, rad(y) + 0.12, BRKD, verts=12, jit=0.03)
    vcyl(p, cx, 29.6, 30.9, cz, 3.3, DRK, verts=12, top_r=3.0)
    vcyl(p, cx, 30.9, 31.0, cz, 2.5, DRK2, verts=10, jit=0.02)
    bx(p, (cx + 2.4, cx + 3.2), (30.9, 31.5), (cz - 0.4, cz + 0.4), RED, 0.02)
    # door, foot pipe, ladder
    bx(p, (16.8, 19.2), (3.0, 5.4), (-51.75, -51.3), DRK2, 0.02)
    bx(p, (16.6, 19.4), (5.4, 5.7), (-51.8, -51.2), STLD, 0.02)
    xcyl(p, 13.0, 15.6, 4.3, cz, 0.8, STLD, verts=8)
    bx(p, (15.4, 15.9), (3.5, 5.1), (cz - 1.0, cz + 1.0), DRK, 0.02)
    rung_ladder(p, 20.75, cz, 3.2, 28.0, w=1.0, col=STLD, step=1.8, axis='x', t=0.15)
    # smoke
    ball(p, (18, 34, -54), 3.0, SMK1, scale=(1, 0.83, 1), subdiv=1, jit=0.05)
    ball(p, (20, 39, -54), 3.5, SMK2, scale=(1, 0.8, 1), subdiv=1, jit=0.05)
    ball(p, (15.8, 37.6, -53.4), 2.3, SMK3, scale=(1, 0.8, 1), subdiv=1, jit=0.05)


# ---- 7. Silos -------------------------------------------------------------------------------------------------------------------
def tank(p, cx, cz, r, h, col):
    vcyl(p, cx, 0, 0.8, cz, r + 0.3, DRK, verts=10)
    vcyl(p, cx, 0.8, h - 1.0, cz, r, col, verts=10)
    vcyl(p, cx, h - 1.0, h, cz, r, col, verts=10, top_r=r * 0.6)
    vcyl(p, cx, 3.2, 4.0, cz, r + 0.1, YEL, verts=10, jit=0.02)
    vcyl(p, cx, 4.0, 4.8, cz, r + 0.1, DRK2, verts=10, jit=0.02)
    vcyl(p, cx, 9.5, 9.9, cz, r + 0.15, STLD, verts=10, jit=0.02)


def build_Silos(p):
    tank(p, -82, -5, 3.5, 15, STL)
    tank(p, -82, -19, 3.5, 15, STLL)
    # catwalk between the tank tops with rails
    bx(p, (-82.6, -81.4), (15.15, 15.65), (-19, -5), DRK)
    for x in (-82.6, -81.4):
        bx(p, (x - 0.06, x + 0.06), (15.65, 16.5), (-19, -5), STL, 0.02)
        for z in (-18, -12, -6):
            bx(p, (x - 0.08, x + 0.08), (15.65, 16.5), (z - 0.08, z + 0.08), STL, 0.02)
    rung_ladder(p, -78.4, -8, 0.8, 15.0, w=1.0, col=STLD, step=1.8, axis='x', t=0.15)
    # gas sphere on four legs
    ball(p, (-69, 9, -12), 5.0, WHT, subdiv=2, jit=0.03)
    vcyl(p, -69, 8.7, 9.3, -12, 5.1, YEL, verts=12, jit=0.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bar(p, (-69 + 3.3 * sx, 4.0, -12 + 3.3 * sz), (-69 + 3.3 * sx, 0.1, -12 + 3.3 * sz), 0.7, DRK)
    for sx in (-1, 1):
        bar(p, (-69 + 3.3 * sx, 3.0, -15.3), (-69 + 3.3 * sx, 3.0, -8.7), 0.25, STLD)
    bar(p, (-72.3, 1.2, -15.3), (-65.7, 3.2, -8.7), 0.25, STLD)
    bar(p, (-65.7, 1.2, -15.3), (-72.3, 3.2, -8.7), 0.25, STLD)
    bx(p, (-70.0, -68.0), (13.9, 14.3), (-12.6, -11.4), STLD, 0.02)
    # orange pipe up between sphere and tanks with connectors
    vcyl(p, -75, 0, 15, -12, 0.4, ORG, verts=8)
    for y in (3, 7.5, 12):
        xcyl(p, -78.4, -75, y, -12, 0.3, ORG, verts=6)
        xcyl(p, -75, -72.6, y, -12, 0.3, ORG, verts=6)
        bx(p, (-75.4, -74.6), (y - 0.2, y + 0.2), (-12.5, -11.5), YEL, 0.02)
    vcyl(p, -75, 15, 15.4, -12, 0.55, DRK, verts=8)


# ---- 8. Booth ------------------------------------------------------------------------------------------------------------------------
def build_Booth(p):
    for (x, z) in ((-83, 20), (-73, 20), (-83, 28), (-73, 28)):
        vcyl(p, x, 0, 4.2, z, 0.5, DRK, verts=8)
        vcyl(p, x, 0, 0.4, z, 0.8, STLD, verts=8)
    for z in (20, 28):
        bar(p, (-83, 0.7, z), (-73, 3.7, z), 0.25, STLD)
        bar(p, (-73, 0.7, z), (-83, 3.7, z), 0.25, STLD)
    bx(p, (-84, -72), (4.2, 4.6), (19, 29), DRK)
    bx(p, (-84.1, -71.9), (4.4, 4.6), (28.7, 29.1), YEL, 0.02)
    # walls: solid lower band, glass above; the road side (+z) has an open window frame
    bx(p, (-83.2, -72.8), (4.6, 5.6), (20.2, 27.8), STL)
    for x in (-83.0, -73.0):
        for z in (20.2, 27.8):
            bx(p, (x - 0.25, x + 0.25), (4.6, 9.1), (z - 0.25, z + 0.25), DRK)
    bx(p, (-83.2, -82.8), (5.6, 8.7), (20.4, 27.6), GLS, 0.04)
    bx(p, (-73.2, -72.8), (5.6, 8.7), (20.4, 27.6), GLS, 0.04)
    bx(p, (-82.8, -73.2), (5.6, 8.7), (20.2, 20.6), GLS, 0.04)
    bx(p, (-83.1, -72.9), (8.5, 8.9), (27.5, 28.0), DRK, 0.02)
    bx(p, (-83.2, -72.8), (4.6, 5.8), (27.6, 28.1), STL)
    # inside: desk with screens, chair, foreman robot
    bx(p, (-82, -75), (4.6, 5.9), (25, 26.4), DRK)
    for x in (-81, -78.5, -76):
        bx(p, (x - 0.8, x + 0.8), (5.9, 7.0), (25.4, 25.6), DRK2, 0.02)
        bx(p, (x - 0.65, x + 0.65), (6.05, 6.85), (25.6, 25.7), CYN, 0.02)
    bx(p, (-79.4, -77.6), (4.6, 5.4), (22.2, 23.8), DRK)
    bx(p, (-79.3, -77.7), (5.4, 6.8), (21.9, 22.2), DRK)
    bx(p, (-79.1, -77.9), (5.4, 6.3), (22.6, 23.4), STL)
    bx(p, (-79.0, -78.0), (6.3, 7.3), (22.5, 23.5), STL)
    bx(p, (-78.8, -78.2), (6.7, 6.95), (23.5, 23.6), CYN, 0.02)
    # roof
    bx(p, (-83.7, -72.3), (9.1, 9.7), (19.3, 28.7), YEL)
    bx(p, (-83.7, -72.3), (9.1, 9.3), (19.3, 28.7), DRK, 0.02)
    bx(p, (-82.6, -80.6), (9.7, 10.5), (21, 23.4), STLD)
    vcyl(p, -80, 9.7, 13.2, 24.0, 0.2, STL, verts=6)
    bx(p, (-80.6, -79.4), (12.4, 12.55), (23.4, 24.6), STLL, 0.02)
    vcyl(p, -73.6, 9.7, 10.5, 20.4, 0.4, RED, verts=8)
    # stairs on the right, with handrail
    bx(p, (-72, -69.7), (0, 4.6), (22, 26), STL)
    bx(p, (-69.7, -68.7), (0, 3.0), (22, 26), STL)
    bx(p, (-68.7, -67.7), (0, 1.4), (22, 26), STL)
    for (x0, x1, top) in ((-72, -69.7, 4.6), (-69.7, -68.7, 3.0), (-68.7, -67.7, 1.4)):
        bx(p, (x0, x1), (top, top + 0.1), (21.9, 26.1), YEL, 0.02)
    for z in (22.0, 26.0):
        bar(p, (-71.6, 5.7, z), (-67.9, 2.5, z), 0.18, STLL, 0.02)
        vcyl(p, -71.6, 4.7, 5.7, z, 0.1, STLL, verts=4, jit=0.02)
        vcyl(p, -67.9, 1.5, 2.5, z, 0.1, STLL, verts=4, jit=0.02)


# ---- 9. Gears ---------------------------------------------------------------------------------------------------------------------------
def build_Gears(p):
    bx(p, (-48, -24), (0, 2), (29, 35), CON)
    bx(p, (-48.2, -23.8), (1.7, 2.1), (28.8, 35.2), CONL, 0.03)
    bx(p, (-47, -25), (0.4, 1.6), (35.0, 35.2), YEL, 0.02)
    for x in (-40, -28.5):
        bx(p, (x - 1.2, x + 1.2), (2, 8), (31.2, 33.2), DRK)
    bx(p, (-41.4, -38.6), (2, 3.0), (29.6, 34.4), DRK)
    bx(p, (-29.9, -27.1), (2, 3.0), (29.6, 34.4), DRK)
    cog(p, -40, 9.8, 31.2, 33.0, 6.4, 0.8, 16, STL, hole=2.6, tcol=STLL, spokes=6, spoke_col=STLD, hub=1.7, hub_col=DRK, seg=20)
    cog(p, -28.5, 7.4, 31.4, 33.0, 3.5, 0.7, 10, YEL, hole=0.9, tcol=YEL, spokes=0, hub=1.0, hub_col=DRK, seg=16)
    bx(p, (-41.6, -38.4), (2.3, 3.0), (33.0, 33.6), DRK2, 0.02)
    # warning stripes on the plinth front
    hazard_x(p, -47.5, -24.5, 0.1, 1.0, 35.0, 35.1, 14)


# ---- 10. Statue -----------------------------------------------------------------------------------------------------------------------------
def build_Statue(p):
    bx(p, (7, 17), (0, 3), (39, 49), CON)
    bx(p, (6.7, 17.3), (2.6, 3.0), (38.7, 49.3), CONL, 0.03)
    bx(p, (8.6, 15.4), (3.0, 3.5), (40.6, 47.4), STLD)
    bx(p, (10.0, 11.5), (3.5, 8.4), (41.8, 44.2), STLD)
    bx(p, (12.5, 14.0), (3.5, 8.4), (41.8, 44.2), STLD)
    bx(p, (9.4, 11.8), (3.0, 4.0), (41.2, 45.6), DRK)
    bx(p, (12.2, 14.6), (3.0, 4.0), (41.2, 45.6), DRK)
    bx(p, (8.4, 15.6), (8.0, 9.0), (41.3, 46.7), DRK)
    bx(p, (8.0, 16.0), (8.8, 14.2), (41.5, 46.5), STL)
    bx(p, (9.2, 14.8), (10.0, 13.0), (46.5, 46.7), DRK2, 0.02)
    bx(p, (10.0, 11.0), (11.2, 12.2), (46.7, 46.8), CYN, 0.02)
    bx(p, (11.4, 12.4), (11.2, 12.2), (46.7, 46.8), RED, 0.02)
    bx(p, (12.8, 13.8), (11.2, 12.2), (46.7, 46.8), GRN, 0.02)
    bx(p, (9.2, 14.8), (9.2, 9.7), (46.5, 46.7), YEL, 0.02)
    bx(p, (10.5, 13.5), (14.2, 14.9), (42.5, 45.5), DRK)
    bx(p, (9.4, 14.6), (14.9, 19.6), (41.8, 46.2), STL)
    bx(p, (10.2, 13.8), (16.4, 17.8), (46.2, 46.4), DRK2, 0.02)
    bx(p, (10.5, 11.5), (16.8, 17.5), (46.4, 46.5), CYN, 0.02)
    bx(p, (12.5, 13.5), (16.8, 17.5), (46.4, 46.5), CYN, 0.02)
    bx(p, (10.8, 13.2), (15.2, 15.7), (46.2, 46.4), DRK2, 0.02)
    bx(p, (8.8, 9.4), (16.0, 18.4), (42.6, 45.4), YEL, 0.02)
    bx(p, (14.6, 15.2), (16.0, 18.4), (42.6, 45.4), YEL, 0.02)
    vcyl(p, 12, 19.6, 22.0, 44, 0.2, DRK, verts=6)
    ball(p, (12, 22.3, 44), 0.55, RED, subdiv=1, jit=0.02)
    # left arm hangs down, right arm waves
    bx(p, (5.8, 7.8), (8.6, 13.6), (42.6, 45.4), STL)
    bx(p, (6.0, 7.6), (8.0, 8.8), (42.8, 45.2), DRK)
    bx(p, (7.8, 8.2), (11.6, 13.8), (43.0, 45.0), STLD, 0.02)
    bar(p, (16.8, 13.0, 44), (17.6, 16.6, 44), 1.9, STL)
    bx(p, (16.2, 18.2), (15.8, 17.8), (42.8, 45.2), STL)
    bx(p, (16.4, 18.0), (17.8, 18.4), (43.0, 45.0), DRK, 0.02)
    bx(p, (16.1, 16.4), (13.0, 13.6), (43.0, 45.0), DRK, 0.02)
    bx(p, (8.0, 8.6), (13.0, 14.3), (43.0, 45.0), DRK, 0.02)


# ---- 11. Generator ------------------------------------------------------------------------------------------------------------------------
def coil(p, cx, cz, h_tower, r, ball_r, ball_y, col=STL):
    vcyl(p, cx, 1.2, 1.9, cz, r + 0.7, DRK, verts=10)
    vcyl(p, cx, 1.9, h_tower, cz, r, col, verts=10, top_r=r * 0.7)
    for y in (3.4, 5.2, 7.0):
        if y < h_tower - 0.8:
            vcyl(p, cx, y, y + 0.35, cz, r + 0.22 - 0.03 * (y - 3), COP, verts=10, jit=0.03)
    vcyl(p, cx, h_tower, h_tower + 0.5, cz, r * 0.85, DRK, verts=10)
    vcyl(p, cx, h_tower + 0.5, ball_y - ball_r + 0.5, cz, r * 0.3, STLL, verts=6)
    ball(p, (cx, ball_y, cz), ball_r, CYN, subdiv=1, jit=0.03)


def build_Generator(p):
    bx(p, (43, 57), (0, 1.2), (19, 29), DRK)
    bx(p, (43.2, 56.8), (1.2, 1.35), (19.2, 28.8), PLT, 0.03)
    hazard_x(p, 43, 57, 0.2, 1.0, 29.0, 29.1, 14)
    coil(p, 45, 24, 8.4, 1.2, 2.2, 10.4)
    coil(p, 50, 24, 12.2, 1.4, 2.7, 14.4)
    coil(p, 55, 24, 8.4, 1.2, 2.2, 10.4)
    bolt_zig(p, (46.9, 11.2, 24), (47.8, 14.0, 24), 0.2, YEL, 2, 0.35)
    bolt_zig(p, (53.1, 11.2, 24), (52.2, 14.0, 24), 0.2, YEL, 2, 0.35)
    # control box with lamps, cables
    bx(p, (54.3, 57.3), (1.2, 4.2), (25.8, 28.2), YEL)
    bx(p, (54.5, 57.1), (2.4, 3.6), (28.2, 28.3), DRK2, 0.02)
    bx(p, (54.7, 55.4), (2.6, 3.4), (28.3, 28.35), GRN, 0.02)
    bx(p, (55.9, 56.9), (2.6, 3.4), (28.3, 28.35), RED, 0.02)
    bx(p, (54.5, 57.1), (4.2, 4.5), (25.6, 28.4), DRK, 0.02)
    for (x0, x1, z) in ((45, 49, 27), (51, 54.3, 27.4)):
        bx(p, (x0, x1), (1.35, 1.7), (z - 0.2, z + 0.2), DRK2, 0.02)
    bx(p, (44.2, 45.8), (1.35, 2.6), (26.6, 27.4), STLD)


# ---- 12. Forklift ------------------------------------------------------------------------------------------------------------------------------
def pallet_crate(p, cx, cz, y0, s, col, tape=YEL):
    crate(p, cx, cz, y0, s, col, tape)


def build_Forklift(p):
    # forklift faces +x
    bx(p, (-17, -11), (1.1, 3.7), (36.2, 39.8), YEL)
    bx(p, (-17.2, -14.4), (1.3, 3.9), (36.0, 40.0), DRK)
    bx(p, (-14.2, -11.2), (3.7, 4.7), (36.5, 39.5), YEL)
    bx(p, (-14.0, -11.4), (3.8, 4.5), (36.7, 39.3), DRK2, 0.02)
    bx(p, (-16.6, -14.6), (3.9, 4.6), (37.0, 39.0), DRK)
    bx(p, (-16.2, -14.8), (4.6, 6.0), (37.1, 38.9), DRK)
    bx(p, (-13.0, -12.4), (3.7, 5.2), (37.0, 39.0), DRK, 0.02)
    for (x, z) in ((-16.4, 36.4), (-16.4, 39.6), (-13.6, 36.4), (-13.6, 39.6)):
        vcyl(p, x, 3.9, 6.2, z, 0.2, DRK, verts=6)
    bx(p, (-17.0, -13.0), (6.2, 6.6), (36.2, 39.8), YEL)
    for z in (36.6, 39.4):
        for x in (-15.3, -12.6):
            zcyl(p, x, 1.1, z - 0.3, z + 0.3, 1.1, DRK2, verts=10)
            zcyl(p, x, 1.1, z + (0.3 if z > 38 else -0.3), z + (0.45 if z > 38 else -0.45), 0.55, STLD, verts=8, jit=0.02)
    vcyl(p, -15.3, 6.6, 7.0, 38, 0.3, RED, verts=6)
    # mast and carriage
    for z in (36.8, 39.2):
        bx(p, (-11.0, -10.2), (0, 9.2), (z - 0.3, z + 0.3), DRK)
    bx(p, (-11.0, -10.2), (8.6, 9.2), (36.5, 39.5), STLD)
    bx(p, (-10.4, -10.0), (1.6, 4.4), (36.6, 39.4), STLD)
    bx(p, (-10.6, -7.4), (0.45, 0.95), (36.9, 37.7), STLL)
    bx(p, (-10.6, -7.4), (0.45, 0.95), (38.3, 39.1), STLL)
    # loaded pallet
    bx(p, (-9.7, -7.1), (0.95, 1.2), (36.7, 39.3), CRTD)
    crate(p, -8.4, 38, 1.2, 2.2, CRT)
    # crate stack, more crates, drums
    crate(p, -3, 33.4, 0, 3.0, CRT)
    crate(p, -3, 33.4, 3.0, 1.8, ORG, STLL)
    crate(p, -3.5, 42.6, 0, 2.4, CRT)
    for (cx, cz, h) in ((-17.5, 33, 3.2), (-15, 32.4, 3.2)):
        vcyl(p, cx, 0, h, cz, 1.1, RED, verts=10)
        vcyl(p, cx, h * 0.3, h * 0.3 + 0.2, cz, 1.15, REDD, verts=10, jit=0.02)
        vcyl(p, cx, h * 0.7, h * 0.7 + 0.2, cz, 1.15, REDD, verts=10, jit=0.02)
        vcyl(p, cx, h, h + 0.05, cz, 0.8, DRK2, verts=8, jit=0.02)


# ---- 13. Pipes ----------------------------------------------------------------------------------------------------------------------------------
def build_Pipes(p):
    for x in (-49, -29):
        bx(p, (x - 1.7, x + 1.7), (0, 1), (-32.7, -29.3), CON)
        bx(p, (x - 1.0, x + 1.0), (1, 13.7), (-32.2, -29.8), STL)
        bx(p, (x - 1.2, x + 1.2), (1, 1.8), (-32.4, -29.6), DRK)
        for y in (3.5, 7, 10.5):
            bx(p, (x - 1.15, x + 1.15), (y, y + 0.3), (-32.35, -29.65), STLD, 0.02)
        for sx in (-1.6, 1.6):
            for sz in (-31.8, -30.2):
                vcyl(p, x + sx, 1.0, 1.25, sz, 0.15, STLL, verts=6, jit=0.02)
    # corner braces
    for (x, s) in ((-49, 1), (-29, -1)):
        diag(p, x + s * 1.0, 11.5, -31, x + s * 3.8, 13.7, 0.5, 1.6, DRK)
    # cross beam, pipes, flanges
    bx(p, (-50.2, -27.8), (13.7, 14.7), (-32.4, -29.6), DRK)
    bx(p, (-50.2, -27.8), (14.5, 14.7), (-32.4, -29.6), YEL, 0.02)
    xcyl(p, -50, -28, 11.4, -32.4, 0.9, ORG, verts=10)
    xcyl(p, -50, -28, 11.4, -29.6, 0.9, STL, verts=10)
    xcyl(p, -50, -28, 9.0, -31, 0.6, YEL, verts=8)
    for x in (-47, -43, -35, -31):
        for (y, z, r) in ((11.4, -32.4, 1.1), (11.4, -29.6, 1.1), (9.0, -31, 0.8)):
            xcyl(p, x - 0.25, x + 0.25, y, z, r, STLD, verts=10, jit=0.02)
    for x in (-39.4, -38.6):
        pass
    # valve wheels on the pipes (facing the road)
    for (x, y, z, col) in ((-41, 11.4, -28.7, RED), (-37, 11.4, -28.7, RED)):
        bx(p, (x - 0.25, x + 0.25), (y - 0.25, y + 0.25), (-28.75, -28.35), STLD, 0.02)
        zcyl(p, x, y, -28.4, -28.2, 0.9, col, verts=8, jit=0.02)
        bx(p, (x - 0.1, x + 0.1), (y - 0.9, y + 0.9), (-28.45, -28.25), col, 0.02)
        bx(p, (x - 0.9, x + 0.9), (y - 0.1, y + 0.1), (-28.45, -28.25), col, 0.02)
    # vertical drop pipe + gauge
    vcyl(p, -39, 8.4, 10.5, -31, 0.35, STLD, verts=6)
    bx(p, (-40, -38), (8.3, 8.6), (-31.6, -30.4), DRK, 0.02)
    zcyl(p, -34, 9.0, -29.55, -29.3, 0.55, WHT, verts=8, jit=0.02)
    bx(p, (-34.1, -33.9), (9.0, 9.5), (-29.3, -29.2), RED, 0.02)


# ---- 14. Crane ------------------------------------------------------------------------------------------------------------------------------------
def build_Crane(p):
    legs = ((72.8, -20), (87.2, -20), (72.8, 0), (87.2, 0))
    for (x, z) in legs:
        bx(p, (x - 0.8, x + 0.8), (0, 18), (z - 0.8, z + 0.8), YEL)
        bx(p, (x - 1.2, x + 1.2), (0, 0.8), (z - 1.2, z + 1.2), DRK)
        hazard_y(p, x - 0.85, x + 0.85, 0.8, 4.0, z - 0.85, z + 0.85, 4)
    # leg braces
    for x in (72.8, 87.2):
        bx(p, (x - 0.5, x + 0.5), (8.8, 9.2), (-20.6, 0.6), DRK, 0.02)
        for z in (-20, 0):
            sg = 1 if z == -20 else -1
            bar(p, (x, 14.8, z), (x, 17.8, z + sg * 3.2), 0.35, STLD)
    for z in (-20, 0):
        bx(p, (72.2, 87.8), (8.8, 9.2), (z - 0.3, z + 0.3), DRK, 0.02)
    # top rails and girder
    for x in (72.8, 87.2):
        bx(p, (x - 0.8, x + 0.8), (17.8, 19.4), (-21, 1), YEL)
        bx(p, (x - 0.9, x + 0.9), (19.4, 19.6), (-21, 1), DRK, 0.02)
    bx(p, (72, 88), (18.5, 19.9), (-7, -5), YEL)
    bx(p, (72, 88), (19.9, 20.1), (-7, -5), DRK, 0.02)
    for i in range(7):
        x = 73.5 + i * 2.2
        bar(p, (x, 18.5, -6), (x + 1.1, 19.9, -6), 0.18, DRK, 0.02)
    # cab on one end of the rail
    bx(p, (71.0, 73.4), (16.2, 18.4), (-4.4, -1.6), STL)
    bx(p, (71.3, 73.1), (16.9, 17.9), (-1.7, -1.55), GLS, 0.04)
    bx(p, (71.0, 73.4), (18.4, 18.8), (-4.6, -1.4), YEL, 0.02)
    # trolley, cable, hook block, red container
    bx(p, (78.4, 81.6), (17.4, 18.5), (-7.5, -4.5), DRK)
    for x in (78.8, 81.2):
        for z in (-7.2, -4.8):
            zcyl(p, x, 17.5, z - 0.15, z + 0.15, 0.5, STLD, verts=6)
    vcyl(p, 80, 8.5, 17.4, -6, 0.15, DRK2, verts=4)
    bx(p, (79.2, 80.8), (6.7, 8.1), (-6.8, -5.2), DRK)
    bx(p, (79.6, 80.4), (6.4, 6.7), (-6.4, -5.6), YEL, 0.02)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bar(p, (80 + 0.6 * sx, 6.7, -6 + 0.6 * sz), (80 + 2.6 * sx, 5.5, -6 + 1.8 * sz), 0.12, STLD, 0.02)
    bx(p, (77, 83), (2.5, 5.5), (-8, -4), RED)
    for x in (77.5, 78.6, 79.7, 80.8, 81.9):
        bx(p, (x - 0.15, x + 0.15), (2.7, 5.3), (-4.1, -3.9), REDD, 0.02)
    bx(p, (77, 83), (5.5, 5.6), (-8, -4), REDD, 0.02)
    bx(p, (78.0, 80.2), (3.5, 4.4), (-3.95, -3.9), WHT, 0.02)
    # rail posts and stop blocks
    bx(p, (72.2, 73.4), (19.6, 20.3), (-21.4, -20.4), RED, 0.02)
    bx(p, (86.6, 87.8), (19.6, 20.3), (-21.4, -20.4), RED, 0.02)


# ---- 15. Charging --------------------------------------------------------------------------------------------------------------------------------------
def charge_bot(p, cx, col, accent):
    # robot faces +z, stands in its stall
    bx(p, (cx - 1.5, cx + 1.5), (0, 0.8), (38.8, 41.4), DRK)
    bx(p, (cx - 1.3, cx + 1.3), (0.8, 3.1), (39.0, 41.2), col)
    bx(p, (cx - 0.7, cx + 0.7), (2.0, 2.7), (41.2, 41.4), accent, 0.02)
    bx(p, (cx - 0.4, cx + 0.4), (1.2, 1.6), (41.2, 41.3), CYN, 0.02)
    bx(p, (cx - 1.7, cx - 1.3), (1.1, 2.9), (39.6, 40.6), DRK)
    bx(p, (cx + 1.3, cx + 1.7), (1.1, 2.9), (39.6, 40.6), DRK)
    bx(p, (cx - 1.1, cx + 1.1), (3.1, 4.9), (39.2, 41.0), col)
    bx(p, (cx - 0.85, cx - 0.3), (3.7, 4.3), (41.0, 41.15), CYN, 0.02)
    bx(p, (cx + 0.3, cx + 0.85), (3.7, 4.3), (41.0, 41.15), CYN, 0.02)
    vcyl(p, cx, 4.9, 5.7, 40.1, 0.1, DRK, verts=4)
    bx(p, (cx - 0.25, cx + 0.25), (5.7, 6.2), (39.85, 40.35), accent, 0.02)
    # charge cable to the socket on the back panel
    bar(p, (cx, 2.5, 39.0), (cx, 3.2, 38.0), 0.18, YEL, 0.02)


def build_Charging(p):
    for x in (61.5, 78.5):
        vcyl(p, x, 0, 8.0, 37.5, 0.45, DRK, verts=8)
        vcyl(p, x, 0, 0.5, 37.5, 0.8, STLD, verts=8)
    bx(p, (60.5, 79.5), (8.0, 8.6), (36.1, 41.1), YEL)
    bx(p, (60.5, 79.5), (7.8, 8.0), (36.1, 41.1), DRK, 0.02)
    bx(p, (60.5, 79.5), (8.6, 8.9), (36.1, 36.4), DRK, 0.02)
    bx(p, (60.5, 79.5), (8.6, 8.9), (40.8, 41.1), DRK, 0.02)
    for x in (63.5, 70, 76.5):
        bx(p, (x - 2.2, x + 2.2), (0, 6.4), (37.2, 38.0), DRK)
        bx(p, (x - 1.6, x + 1.6), (4.4, 5.8), (38.0, 38.1), DRK2, 0.02)
        bx(p, (x - 1.3, x + 1.3), (4.7, 5.0), (38.1, 38.15), GRN, 0.02)
        bx(p, (x - 0.6, x + 0.6), (2.8, 3.8), (38.0, 38.3), YEL, 0.02)
        bx(p, (x - 2.2, x - 1.9), (0, 6.4), (37.9, 39.0), STLD, 0.02)
        bx(p, (x + 1.9, x + 2.2), (0, 6.4), (37.9, 39.0), STLD, 0.02)
    charge_bot(p, 63.5, STL, ORG)
    charge_bot(p, 70, WHT, CYN)
    charge_bot(p, 76.5, STL, YEL)
    for x in (66.75, 73.25):
        bx(p, (x - 0.25, x + 0.25), (0, 6.4), (37.2, 39.0), STLD, 0.02)
    bx(p, (60.5, 79.5), (0, 0.15), (36.1, 41.4), PLT, 0.02)


# ---- 16. Press -------------------------------------------------------------------------------------------------------------------------------------------
def build_Press(p):
    bx(p, (13, 27), (0, 3), (-39, -29), DRK)
    hazard_x(p, 13, 27, 0.2, 2.6, -29.1, -28.9, 14)
    for x in (13.3, 24.3):
        bx(p, (x, x + 2.4), (3, 16.5), (-37, -31), ORG)
        bx(p, (x + (2.4 if x < 20 else -0.3), x + (2.7 if x < 20 else 0)), (3.2, 15.5), (-36.5, -31.5), STLD, 0.02)
    bx(p, (13, 27), (15.5, 18.5), (-38, -30), ORG)
    bx(p, (12.8, 27.2), (18.2, 18.5), (-38.2, -29.8), DRK, 0.02)
    bx(p, (13, 27), (15.4, 15.7), (-38.1, -29.9), DRK, 0.02)
    vcyl(p, 20, 11.5, 15.5, -34, 2.0, STL, verts=10)
    for y in (12.2, 14.4):
        vcyl(p, 20, y, y + 0.35, -34, 2.2, STLL, verts=10, jit=0.02)
    vcyl(p, 20, 7.3, 11.7, -34, 1.0, STLL, verts=8)
    bx(p, (16, 24), (5.9, 7.3), (-36.5, -31.5), DRK)
    bx(p, (16.2, 23.8), (5.9, 6.1), (-31.6, -31.5), YEL, 0.02)
    bx(p, (16, 24), (3, 4.8), (-36.5, -31.5), STL)
    bx(p, (16.5, 23.5), (4.8, 5.2), (-36, -32), STLL, 0.03)
    # hoses, gauge, beacon
    bar(p, (22, 15.5, -34), (25.4, 12.0, -34), 0.5, DRK2)
    bar(p, (25.4, 12.0, -34), (25.4, 9.0, -34), 0.5, DRK2)
    zcyl(p, 14.9, 16.6, -29.95, -29.6, 0.8, WHT, verts=10, jit=0.02)
    bx(p, (14.85, 14.95), (16.6, 17.2), (-29.6, -29.5), RED, 0.02)
    bx(p, (17.2, 18.8), (16.2, 17.2), (-29.95, -29.7), YEL, 0.02)
    vcyl(p, 25.8, 18.0, 18.8, -36.5, 0.5, RED, verts=8)
    # control stand and sheet stack
    bx(p, (27.4, 29.2), (0, 2.2), (-37.2, -36.0), DRK)
    bx(p, (27.3, 29.3), (2.2, 3.2), (-37.3, -35.9), STL)
    bx(p, (27.6, 29.0), (2.4, 3.0), (-35.9, -35.8), CYN, 0.02)
    bx(p, (27.1, 30.1), (0, 0.3), (-30.6, -28.2), DRK)
    for i in range(6):
        bx(p, (27.1 + 0.04 * (i % 2), 30.1 - 0.05 * (i % 3)), (0.3 + 0.35 * i, 0.3 + 0.35 * (i + 1)),
           (-30.6 + 0.05 * (i % 2), -28.2), PLT if i % 2 else STLL, 0.03)


# ---- 17. Drones ------------------------------------------------------------------------------------------------------------------------------------------
def drone(p, cx, y0, cz, col=WHT, accent=ORG):
    bx(p, (cx - 0.7, cx + 0.7), (y0 + 0.3, y0 + 1.1), (cz - 0.7, cz + 0.7), col)
    bx(p, (cx - 0.4, cx + 0.4), (y0 + 0.5, y0 + 0.9), (cz + 0.7, cz + 0.78), CYN, 0.02)
    bx(p, (cx - 0.25, cx + 0.25), (y0 + 1.1, y0 + 1.3), (cz - 0.25, cz + 0.25), DRK, 0.02)
    bar(p, (cx - 1.0, y0 + 0.8, cz - 1.0), (cx + 1.0, y0 + 0.8, cz + 1.0), 0.16, DRK, 0.02)
    bar(p, (cx - 1.0, y0 + 0.8, cz + 1.0), (cx + 1.0, y0 + 0.8, cz - 1.0), 0.16, DRK, 0.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            vcyl(p, cx + sx, y0 + 0.8, y0 + 0.95, cz + sz, 0.3, accent, verts=6, jit=0.02)
    for sx in (-0.45, 0.45):
        bx(p, (cx + sx - 0.07, cx + sx + 0.07), (y0 + 0.0, y0 + 0.3), (cz - 0.8, cz + 0.8), DRK, 0.02)


def build_Drones(p):
    vcyl(p, 84, 0, 2, 56, 4, CON, verts=12, top_r=3.4)
    vcyl(p, 84, 2, 4.5, 56, 1.9, STL, verts=10, top_r=1.0)
    vcyl(p, 84, 4.5, 13.0, 56, 0.9, STL, verts=10)
    for y in (6.0, 8.5, 11.0):
        vcyl(p, 84, y, y + 0.4, 56, 1.15, YEL if y == 8.5 else DRK, verts=10, jit=0.02)
    vcyl(p, 84, 12.95, 13.65, 56, 5, DRK, verts=16)
    vcyl(p, 84, 12.5, 12.95, 56, 2.2, STLD, verts=10, jit=0.02)
    for k in range(10):
        a = math.radians(36 * k)
        bc(p, 84 + 4.6 * math.cos(a), 13.7, 56 + 4.6 * math.sin(a), 0.6, 0.12, 0.6, YEL if k % 2 == 0 else DRK2, 0.02, rot=(0, 0, 0))
    for (x, z) in ((81.5, 54.5), (86.5, 54.5), (81.5, 57.5), (86.5, 57.5)):
        bx(p, (x - 1.2, x + 1.2), (13.65, 14.2), (z - 1.2, z + 1.2), PLT)
        bx(p, (x - 0.9, x + 0.9), (14.2, 14.3), (z - 0.9, z + 0.9), STLL, 0.02)
    drone(p, 81.5, 14.3, 54.5, WHT, ORG)
    drone(p, 86.5, 14.3, 54.5, STL, CYN)
    drone(p, 81.5, 14.3, 57.5, STL, YEL)
    drone(p, 86.5, 14.3, 57.5, WHT, RED)
    vcyl(p, 84, 13.65, 17.0, 56, 0.2, STLL, verts=6)
    ball(p, (84, 17.2, 56), 0.4, RED, subdiv=1, jit=0.02)
    bx(p, (83.6, 84.4), (15.0, 15.15), (55.2, 56.8), STLL, 0.02)
    bx(p, (83.6, 84.4), (16.2, 16.35), (55.4, 56.6), STLL, 0.02)


# ---- 18. Scrap ----------------------------------------------------------------------------------------------------------------------------------------------
def build_Scrap(p):
    rnd = random.Random(7)
    ball(p, (-58, 1.6, 10), 1.0, RSTD, scale=(8, 2.0, 5.0), subdiv=1, jit=0.1)
    cols = [RST, RSTD, STLD, STL, DIRT, COP, REDD, RST, STLD]
    n = 0
    tries = 0
    while n < 46 and tries < 500:
        tries += 1
        x = -58 + rnd.uniform(-8.5, 8.5)
        z = 10 + rnd.uniform(-4.8, 4.8)
        h = 8.0 * (1 - ((x + 58) / 9.0) ** 2 - ((z - 10) / 5.6) ** 2)
        if h < 1.0:
            continue
        sx, sy, sz = rnd.uniform(1.6, 3.6), rnd.uniform(0.5, 1.3), rnd.uniform(1.6, 3.2)
        bc(p, x, max(sy, h * rnd.uniform(0.55, 1.0)), z, sx, sy, sz, cols[n % len(cols)], 0.08,
           rot=(rnd.uniform(-22, 22), rnd.uniform(0, 180), rnd.uniform(-22, 22)))
        n += 1
    # junk poking out of the heap
    bx(p, (-60.4, -57.2), (5.0, 6.6), (6.0, 8.6), STL)      # robot head
    bx(p, (-60.0, -58.8), (5.6, 6.1), (8.6, 8.7), CYND, 0.02)
    bx(p, (-58.8, -57.6), (5.6, 6.1), (8.6, 8.7), DRK2, 0.02)
    bar(p, (-58.8, 6.6, 7.2), (-58.2, 7.8, 7.0), 0.15, DRK)
    bar(p, (-64, 6.5, 8), (-60, 8.6, 12), 0.7, STLD)         # broken arm
    bx(p, (-60.8, -59.4), (8.3, 9.4), (11.4, 12.6), YEL)
    bar(p, (-55, 5.0, 9), (-50.5, 7.2, 13.5), 0.5, DRK)
    zcyl(p, -54.8, 5.0, 12.0, 13.0, 1.6, DRK2, verts=10)       # tyre
    zcyl(p, -54.8, 5.0, 13.0, 13.1, 0.8, STLD, verts=8, jit=0.02)
    xcyl(p, -66.5, -62, 3.6, 5.6, 0.6, COP, verts=6)         # pipe
    cog(p, -57.0, 6.0, 12.2, 13.0, 1.3, 0.35, 8, STL, hole=0.4, tcol=STLL, seg=12)
    bar(p, (-52.2, 4.8, 8), (-49.4, 6.2, 8.5), 0.4, RSTD)
    bx(p, (-51.5, -50.0), (4.5, 5.6), (10.5, 12.0), STL)
    # crushed cube
    bx(p, (-68.2, -63.8), (0, 4.4), (11.8, 16.2), STL)
    for y in (1.0, 2.0, 3.0):
        bx(p, (-68.25, -63.75), (y, y + 0.25), (11.75, 16.25), STLD, 0.03)
    bx(p, (-67.0, -65.0), (4.4, 4.6), (13.0, 14.6), RST, 0.05)
    bx(p, (-67.0, -64.4), (1.4, 2.4), (16.2, 16.3), YEL, 0.03)
    # magnet crane
    bx(p, (-70.7, -69.3), (0, 0.8), (3.3, 4.7), DRK)
    vcyl(p, -70, 0.8, 13.0, 4, 0.6, YEL, verts=8)
    bx(p, (-70.6, -60.2), (12.75, 13.65), (3.4, 4.6), YEL)
    bar(p, (-70, 7.0, 4), (-66.6, 12.75, 4), 0.3, STLD)
    vcyl(p, -61, 7.3, 12.3, 4, 0.1, DRK2, verts=4)
    vcyl(p, -61, 6.6, 7.4, 4, 1.5, DRK, verts=10)
    vcyl(p, -61, 6.45, 6.6, 4, 1.2, STLD, verts=8, jit=0.02)
    bx(p, (-61.4, -60.6), (5.9, 6.5), (3.8, 4.2), RST, 0.05)
    bx(p, (-62.0, -61.0), (12.0, 12.7), (4.6, 5.3), DRK, 0.02)


# ---- 19. Lab -----------------------------------------------------------------------------------------------------------------------------------------------------
def build_Lab(p):
    cy = -40
    vcyl(p, 0, 0, 1.6, cy, 9.5, CON, verts=20)
    vcyl(p, 0, 1.6, 1.9, cy, 8.9, STLD, verts=20, jit=0.02)
    for k in range(12):
        annulus(p, (0, cy), 'y', 7.3, 8.6, 1.9, 2.05, YEL if k % 2 == 0 else DRK2, n=1, t0=30 * k, t1=30 * k + 30, jit=0.02)
    # pedestal and brain
    vcyl(p, 0, 1.9, 4.8, cy, 2.5, DRK, verts=10, top_r=1.7)
    vcyl(p, 0, 3.0, 3.3, cy, 2.3, CYND, verts=10, jit=0.02)
    vcyl(p, 0, 4.8, 5.4, cy, 0.8, STLL, verts=8)
    ball(p, (-1.3, 7.0, cy), 1.0, PNK, scale=(2.5, 2.2, 3.0), subdiv=1, jit=0.06)
    ball(p, (1.3, 7.0, cy), 1.0, PNK, scale=(2.5, 2.2, 3.0), subdiv=1, jit=0.06)
    for (x, y, z) in ((-1.6, 8.3, cy - 0.8), (1.6, 8.3, cy + 0.6), (0.0, 8.5, cy - 0.2), (-1.9, 7.2, cy + 1.6), (1.9, 7.2, cy - 1.6),
                      (-0.6, 6.6, cy + 2.0), (0.6, 6.6, cy - 2.0), (0.0, 7.4, cy + 1.0)):
        ball(p, (x * 1.25, y + 0.6, z * 1.2 + cy * (1 - 1.2)), 0.9, PNKL, subdiv=0, jit=0.05)
    ball(p, (0, 5.6, cy + 0.6), 0.6, PNK, scale=(1, 1, 1.2), subdiv=0, jit=0.05)
    annulus(p, (0, cy), 'y', 4.6, 4.95, 6.9, 7.1, CYN, n=16, jit=0.02)
    # glass dome as a rib cage
    rx, ry, y0 = 8.7, 11.4, 1.6
    steps = [0, 22.5, 45, 67.5, 90]

    def dp(phi, theta):
        ph, th = math.radians(phi), math.radians(theta)
        return (rx * math.sin(ph) * math.cos(th), y0 + ry * math.cos(ph), cy - rx * math.sin(ph) * math.sin(th))
    for k in range(6):
        th = 60 * k
        for a, b in zip(steps[:-1], steps[1:]):
            bar(p, dp(b, th), dp(a, th), 0.4, STL if k % 2 == 0 else STLL, 0.02)
    for k in range(12):
        bar(p, dp(45, 30 * k), dp(45, 30 * k + 30), 0.35, YEL, 0.02)
    vcyl(p, 0, 12.4, 13.0, cy, 0.7, DRK, verts=8)
    for k in range(6):
        t = math.radians(60 * k)
        bx(p, (8.2 * math.cos(t) - 0.5, 8.2 * math.cos(t) + 0.5), (1.9, 2.5), (cy - 8.2 * math.sin(t) - 0.5, cy - 8.2 * math.sin(t) + 0.5), DRK, 0.02)


# ---- 20. GiantRobot ----------------------------------------------------------------------------------------------------------------------------------------------------
def build_GiantRobot(p):
    for x in (-76.5, -67.5):
        bx(p, (x - 3.2, x + 3.2), (0, 3), (-48.7, -39.3), DRK)
        bx(p, (x - 3.0, x + 3.0), (0, 1.0), (-39.3, -37.9) if False else (-40.6, -39.3), DRK2, 0.02)
        bx(p, (x - 2.4, x + 2.4), (3.0, 3.6), (-47.6, -40.8), STLD)
        bx(p, (x - 1.8, x + 1.8), (3.6, 13.6), (-46.2, -41.8), STL)
        bx(p, (x - 1.5, x + 1.5), (7.2, 9.6), (-41.8, -41.1), YEL)
        bx(p, (x - 1.2, x + 1.2), (4.2, 6.6), (-41.8, -41.3), STLD)
        vcyl(p, x, 3.6, 13.4, -46.8, 0.3, STLL, verts=6)
        bx(p, (x - 0.5, x + 0.5), (4.0, 6.0), (-39.9, -39.3), YEL, 0.02)
    # hips
    bx(p, (-79.5, -64.5), (13.4, 16.8), (-47.5, -40.5), DRK)
    hazard_x(p, -79.2, -64.8, 14.0, 15.4, -40.55, -40.3, 12)
    for x in (-79.8, -64.2):
        bx(p, (x - 0.3, x + 0.3), (14.2, 15.6), (-45.5, -42.5), YEL, 0.02)
    # torso, chest plate, light, vents
    bx(p, (-80.5, -63.5), (16.8, 29.3), (-48.4, -39.9), STL)
    bx(p, (-80.5, -63.5), (16.8, 17.8), (-48.4, -39.9), STLD)
    bx(p, (-78.0, -66.0), (19.0, 28.0), (-39.95, -39.7), STLD)
    bx(p, (-72.9, -71.1), (19.0, 28.0), (-39.7, -39.5), DRK2, 0.02)
    zcyl(p, -72, 24.5, -39.7, -39.35, 3.0, DRK, verts=14, jit=0.02)
    zcyl(p, -72, 24.5, -39.35, -39.3, 2.2, CYN, verts=12, jit=0.02)
    zcyl(p, -72, 24.5, -39.3, -39.2, 1.1, WHT, verts=10, jit=0.02)
    for i in range(4):
        bx(p, (-77.3, -66.7), (19.4 + i * 0.5, 19.6 + i * 0.5), (-39.75, -39.6), DRK2, 0.02)
    for x in (-78.8, -65.2):
        bx(p, (x - 0.3, x + 0.3), (24.5, 28.5), (-39.95, -39.75), YEL, 0.02)
    for (x, y) in ((-79.2, 17.6), (-64.8, 17.6), (-79.2, 28.4), (-64.8, 28.4)):
        vcyl(p, x, y, y + 0.1, -39.9, 0.35, STLL, verts=6, jit=0.02)
    # backpack with exhausts
    bx(p, (-77, -67), (18.5, 28), (-50.3, -48.4), DRK)
    for x in (-75, -69):
        vcyl(p, x, 28.0, 31.0, -49.4, 0.7, ORG, verts=8)
        vcyl(p, x, 31.0, 31.3, -49.4, 0.9, DRK2, verts=8, jit=0.02)
    # neck and head
    bx(p, (-73.5, -70.5), (29.3, 29.9), (-46.4, -43.2), DRK)
    bx(p, (-76, -68), (29.6, 34.2), (-47.2, -41.0), STL)
    bx(p, (-75.4, -68.6), (31.0, 33.4), (-41.2, -40.7), DRK2)
    bx(p, (-74.8, -73.2), (31.7, 32.7), (-40.7, -40.5), CYN, 0.02)
    bx(p, (-70.8, -69.2), (31.7, 32.7), (-40.7, -40.5), CYN, 0.02)
    bx(p, (-74.0, -70.0), (29.9, 30.5), (-41.2, -40.9), DRK2, 0.02)
    for x in (-72.8, -72.0, -71.2):
        bx(p, (x - 0.08, x + 0.08), (29.95, 30.45), (-40.95, -40.85), STLL, 0.02)
    xcyl(p, -77.2, -76.0, 31.8, -44, 1.3, YEL, verts=8)
    xcyl(p, -68.0, -66.8, 31.8, -44, 1.3, YEL, verts=8)
    bx(p, (-74.5, -69.5), (34.2, 34.7), (-46.0, -42.0), YEL)
    vcyl(p, -72, 34.7, 37.2, -44, 0.35, DRK, verts=6)
    ball(p, (-72, 37.4, -44), 0.5, RED, subdiv=1, jit=0.02)
    # arms
    for (sg, x) in ((-1, -83.4), (1, -60.6)):
        bx(p, (x - 2.8, x + 2.8), (27.4, 29.8), (-47.0, -41.0), YEL)       # shoulder pad
        bx(p, (x - 2.3, x + 2.3), (16.4, 27.4), (-46.5, -41.5), STL)       # arm
        bx(p, (x - 2.3, x + 2.3), (25.5, 26.0), (-46.5, -41.5), DRK, 0.02)
        bx(p, (x - 2.45, x + 2.45), (20.6, 21.2), (-46.7, -41.3), DRK2, 0.02)
        bx(p, (x - 2.7, x + 2.7), (12.2, 16.6), (-46.7, -41.3), YEL)       # fist
        bx(p, (x - 2.7, x + 2.7), (12.2, 13.0), (-46.7, -41.3), DRK, 0.02)
        for i in range(3):
            bx(p, (x - 2.0 + i * 1.5, x - 1.9 + i * 1.5), (13.0, 16.0), (-41.35, -41.2), DRK2, 0.02)
        bx(p, (x + sg * 2.3, x + sg * 2.6), (22.0, 27.0), (-45.0, -43.0), STLD, 0.02)


# ---- all parts, preview settings ---------------------------------------------------------------------------------------------
PARTS = [(n[6:], f) for n, f in sorted(((k, v) for k, v in globals().items() if k.startswith("build_") and callable(v)),
                                       key=lambda kv: ORDER.index(kv[0][6:]))]

AZ = {}
ELEV = {"Drones": 40}
MULT = {"Floor": 1.5, "Hall": 2.3, "Sign": 2.4, "Smokestack": 3.5, "Statue": 3.0, "GiantRobot": 3.1, "Drones": 2.5, "Silos": 2.7, "Crane": 2.6}
# reference Shiba in each preview: (x, z, facing, lift)
SHIBA_AT = {"Floor": (-48, 52, 270, 0), "Hall": (30, -20, 270, 0), "Sign": (-40, 56, 270, 0), "Conveyor": (40, 0, 270, 0),
            "Welder": (66, 28, 270, 0), "Smokestack": (27, -44, 270, 0), "Silos": (-76, 3, 270, 0), "Booth": (-80, 35, 270, 0),
            "Gears": (-36, 40, 270, 0), "Statue": (24, 46, 270, 0), "Generator": (62, 33, 270, 0), "Forklift": (-12, 48, 270, 0),
            "Pipes": (-30, -23, 270, 0), "Crane": (80, 6, 270, 0), "Charging": (70, 48, 270, 0), "Press": (26, -23, 270, 0),
            "Drones": (74, 62, 270, 0), "Scrap": (-56, 24, 270, 0), "Lab": (0, -26, 270, 0), "GiantRobot": (-72, -33, 270, 0)}
SHIBA_DEFAULT = None
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
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_RobotFactory.png"))


main()
