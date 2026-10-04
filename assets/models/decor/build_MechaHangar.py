"""Final low-poly decor models for the theme MechaHangar (30 parts around the 23rd Shiba, Mecha Shiba).

Usage: blender --background --factory-startup --python build_MechaHangar.py -- <outdir> [PartId,PartId,...]
Writes Decor_MechaHangar_<PartId>.fbx, preview_<PartId>.png and stage_MechaHangar.png into <outdir>.
Every model is written in LOCAL coordinates around the centre (cx, cz) of its part in the theme (ORG below) and is fitted to the
union box of its blueprint pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it).
Give part ids (comma separated) after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S, shade

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "MechaHangar"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "MechaHangar"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_MechaHangar.json"))

# centre (x, z) of every part in the theme (the argument of part(cx, cz, ...) in DecorTheme23.luau)
ORG = {"Floor": (0, 0), "Turntable": (22, 4), "Hangar": (60, -36), "BonkSign": (-30, 50), "Crates": (-70, 32), "Drums": (-51, 45),
       "Floodlights": (40, 52), "Console": (-14, -16), "Workshop": (66, 48), "FuelTanks": (-48, -4), "Radar": (-68, 48),
       "Barracks": (-64, -47), "MissileRack": (46, -14), "DronePad": (-28, 34), "RepairArm": (-68, 13), "Transport": (-48, 26),
       "PartsRack": (-70, -2), "Walkers": (-33, -26), "Range": (-52, -25), "Barriers": (4, 17), "Silos": (72, -12),
       "Tower": (-20, -44), "Dropship": (58, 25), "Scrap": (-72, -20), "StrategyTable": (4, -22), "Generator": (28, -50),
       "ChargeDock": (34, 24), "MechaHead": (-11, 44), "Colossus": (50, 0), "Reactor": (-40, -47)}
OX = OZ = 0.0

# ---- palette (one for all 30 parts) ---------------------------------------------------------------------------------
STEEL = (110, 130, 160)
LSTEEL = (168, 184, 208)
PANEL = (150, 168, 195)
DARK = (44, 54, 72)
DDARK = (30, 36, 50)
HAZ = (255, 200, 0)
BLK = (24, 26, 32)
HOLO = (80, 210, 255)
RED = (230, 50, 50)
WHITE = (232, 236, 244)
ORANGE = (240, 130, 40)
FLOOR = (84, 94, 110)
CONC = (124, 128, 138)
LCONC = (146, 150, 160)


# ---- helpers (all coordinates LOCAL to the part, ORG is added) --------------------------------------------------------
def org(name):
    global OX, OZ
    OX, OZ = ORG[name]


def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = (OX + (x[0] + x[1]) / 2, (y[0] + y[1]) / 2, OZ + (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def bc(p, c, s, col, yaw=0, jit=0.04):
    """Box from centre and size, turned about its own centre by yaw (degrees, Roblox sense)."""
    return dk.box(p, (OX + c[0], c[1], OZ + c[2]), s, col, rot=(0, yaw, 0), jitter=jit)


def ry(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


class Grp:
    """A turned group of boxes: offsets are given in the group's own frame and turned by yaw about the group centre c."""

    def __init__(self, p, c, yaw=0.0):
        self.p, self.c, self.yaw = p, c, yaw

    def pos(self, off):
        a, b = ry(off[0], off[2], self.yaw)
        return (self.c[0] + a, self.c[1] + off[1], self.c[2] + b)

    def box(self, off, size, col, jit=0.04, yaw=0.0):
        return bc(self.p, self.pos(off), size, col, self.yaw + yaw, jit)

    def cyl(self, off, r, h, col, verts=10, top_r=None, jit=0.04):
        """Standing cylinder, off = centre of its base."""
        q = self.pos(off)
        return vcyl(self.p, q[0], q[1], q[1] + h, q[2], r, col, verts, top_r, jit)

    def xcyl(self, off, length, r, col, verts=10, jit=0.04, yaw=0.0):
        """Cylinder lying along the group's x axis, off = centre."""
        q = self.pos(off)
        return dk.cyl(self.p, (OX + q[0], q[1], OZ + q[2]), r, length, col, axis='x', verts=verts, rot=(0, self.yaw + yaw, 0), jitter=jit)

    def zcyl(self, off, length, r, col, verts=10, jit=0.04, yaw=0.0):
        q = self.pos(off)
        return dk.cyl(self.p, (OX + q[0], q[1], OZ + q[2]), r, length, col, axis='z', verts=verts, rot=(0, self.yaw + yaw, 0), jitter=jit)

    def ball(self, off, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
        q = self.pos(off)
        return ball(self.p, q, r, col, scale, subdiv, jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (OX + cx, (y0 + y1) / 2, OZ + cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=10, jit=0.04, rot=(0, 0, 0)):
    return dk.cyl(p, (OX + (x0 + x1) / 2, cy, OZ + cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit, rot=rot)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, rot=(0, 0, 0)):
    return dk.cyl(p, (OX + cx, cy, OZ + (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit, rot=rot)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, (OX + c[0], c[1], OZ + c[2]), r, col, scale=scale, subdiv=subdiv, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (local stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (OX, 0, OZ), pts, faces, col, jit)


def prism_z(p, tri, z0, z1, col, jit=0.04):
    """Triangular prism: tri = three (x, y) points, extruded along z from z0 to z1."""
    pts = [(a, b, z0) for a, b in tri] + [(a, b, z1) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (OX, 0, OZ), pts, faces, col, jit)


def bar(p, a, b, t, col, jit=0.04):
    """Square bar of thickness t between two 3D points (local stage coordinates)."""
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
    return dk.poly(p, (OX, 0, OZ), pts, faces, col, jit)


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.04):
    """Bar in the x-y plane from (x1,y1) to (x2,y2), thickness t, depth along z centred on z."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (OX + cx, cy, OZ + z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def wedge_up(p, x0, x1, z0, z1, y0, y1, col, jit=0.04):
    """Ramp: full height y1 at z0 (back), sloping down to y0 at z1 (front, toward +z)."""
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0, y1, z0), (x1, y1, z0)]
    faces = [(0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)]
    return dk.poly(p, (OX, 0, OZ), pts, faces, col, jit)



# ---- lettering ----
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





# ---- extra helpers for this theme ---------------------------------------------------------------------------------------
_letter1 = letter


def letter(p, ch, x0, y0, z0, z1, w, h, t, col, mirror=False):
    if ch not in "MYZ":
        return _letter1(p, ch, x0, y0, z0, z1, w, h, t, col, mirror)
    zc, d = (z0 + z1) / 2, z1 - z0
    if ch == 'M':
        bx(p, (x0, x0 + t), (y0, y0 + h), (z0, z1), col, 0.03)
        bx(p, (x0 + w - t, x0 + w), (y0, y0 + h), (z0, z1), col, 0.03)
        diag(p, x0 + t * 0.5, y0 + h - t * 0.5, zc, x0 + w / 2, y0 + h * 0.35, t, d, col, 0.03)
        diag(p, x0 + w - t * 0.5, y0 + h - t * 0.5, zc, x0 + w / 2, y0 + h * 0.35, t, d, col, 0.03)


def stripes(p, x, y, z, n, c1=HAZ, c2=BLK, along='x', jit=0.03):
    """Hazard band: n alternating boxes along x or z inside the ranges."""
    for i in range(n):
        col = c1 if i % 2 == 0 else c2
        if along == 'x':
            a = x[0] + (x[1] - x[0]) * i / n
            b = x[0] + (x[1] - x[0]) * (i + 1) / n
            bx(p, (a, b), y, z, col, jit)
        else:
            a = z[0] + (z[1] - z[0]) * i / n
            b = z[0] + (z[1] - z[0]) * (i + 1) / n
            bx(p, x, y, (a, b), col, jit)


def drum(p, x, z, col, r=1.2, h=3.4, y0=0.0, band=DARK, verts=10):
    vcyl(p, x, y0 + 0.05, y0 + h - 0.05, z, r, col, verts)
    vcyl(p, x, y0 + h - 0.3, y0 + h - 0.02, z, r + 0.08, band, 8)
    vcyl(p, x, y0, y0 + 0.3, z, r + 0.08, band, 8)
    vcyl(p, x, y0 + h - 0.04, y0 + h, z, r * 0.8, shade(col, 1.18), verts, jit=0.02)


# ---- 1. Floor ---------------------------------------------------------------------------------------------------------------
def build_Floor(p):
    bx(p, (-79, 79), (-0.05, 0.25), (-56.5, 56.5), FLOOR, 0.05)
    for x in range(-60, 61, 20):                                   # plate seams
        bx(p, (x - 0.12, x + 0.12), (0.25, 0.3), (-55, 55), (66, 76, 92), 0.02)
    for z in (-40, -20, 0, 20, 40):
        bx(p, (-78, 78), (0.25, 0.3), (z - 0.12, z + 0.12), (66, 76, 92), 0.02)
    for (cx, cz, sx, sz) in ((-50, -28, 24, 18), (60, 22, 24, 20), (-8, 14, 18, 14)):      # concrete patches
        bx(p, (cx - sx / 2, cx + sx / 2), (0.2, 0.4), (cz - sz / 2, cz + sz / 2), CONC, 0.05)
        bx(p, (cx - 0.1, cx + 0.1), (0.4, 0.43), (cz - sz / 2 + 0.5, cz + sz / 2 - 0.5), LCONC, 0.02)
        bx(p, (cx - sx / 2 + 0.5, cx + sx / 2 - 0.5), (0.4, 0.43), (cz - 0.1, cz + 0.1), LCONC, 0.02)
    for (cx, cz, sx, sz) in ((-50, 12, 2, 30), (44, -34, 2, 26), (10, 48, 26, 2), (-22, -10, 2, 20)):   # hazard lanes
        bx(p, (cx - sx / 2, cx + sx / 2), (0.3, 0.46), (cz - sz / 2, cz + sz / 2), HAZ, 0.03)
        n = int(max(sx, sz) / 2)
        for i in range(1, n, 2):
            if sx > sz:
                bx(p, (cx - sx / 2 + i * 2, cx - sx / 2 + i * 2 + 2), (0.3, 0.5), (cz - sz / 2, cz + sz / 2), BLK, 0.02)
            else:
                bx(p, (cx - sx / 2, cx + sx / 2), (0.3, 0.5), (cz - sz / 2 + i * 2, cz - sz / 2 + i * 2 + 2), BLK, 0.02)
    for (a, b, c, d) in ((-79, 79, -56.5, -55.7), (-79, 79, 55.7, 56.5), (-79, -78.2, -55.7, 55.7), (78.2, 79, -55.7, 55.7)):    # hazard edging
        bx(p, (a, b), (0.25, 0.4), (c, d), HAZ, 0.03)
    # service details: manhole covers and drain grates
    for (cx, cz) in ((-30, 40), (20, -20), (-64, 48), (70, -4), (-8, -42)):
        vcyl(p, cx, 0.25, 0.33, cz, 1.6, DARK, 8, jit=0.03)
        vcyl(p, cx, 0.33, 0.36, cz, 0.9, STEEL, 8, jit=0.03)
    for (cx, cz) in ((-40, -8), (30, 36), (-4, 30)):
        bx(p, (cx - 2.5, cx + 2.5), (0.25, 0.32), (cz - 1.2, cz + 1.2), BLK, 0.02)
        for k in range(4):
            bx(p, (cx - 2.2 + k * 1.2, cx - 1.6 + k * 1.2), (0.32, 0.36), (cz - 1.0, cz + 1.0), STEEL, 0.02)
    # walkway tiles along the path
    pts = [(v[0], v[1]) for v in BP["Path"]]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        n = max(1, int(L // 8))
        ang = -math.degrees(math.atan2(z1 - z0, x1 - x0))
        for k in range(n):
            u = (k + 0.5) / n
            if abs(z0 + (z1 - z0) * u) < 53:
                bc(p, (x0 + (x1 - x0) * u, 0.25, z0 + (z1 - z0) * u), (5.0, 0.07, 3.6), (98, 110, 130), yaw=ang, jit=0.05)


# ---- 2. Turntable -----------------------------------------------------------------------------------------------------------
def build_Turntable(p):
    vcyl(p, 0, 0, 0.3, 0, 12.5, DARK, 32)
    vcyl(p, 0, 0.3, 0.36, 0, 10.5, HAZ, 32, jit=0.02)
    for k in range(16):                                           # black chevron blocks on the hazard ring
        a = math.radians(k * 22.5)
        bc(p, (9.9 * math.cos(a), 0.36, 9.9 * math.sin(a)), (1.8, 0.06, 1.3), BLK, yaw=-k * 22.5 - 90, jit=0.02)
    vcyl(p, 0, 0.36, 0.42, 0, 9.2, DARK, 32)
    vcyl(p, 0, 0.42, 0.5, 0, 6.2, STEEL, 24, jit=0.03)
    bx(p, (-6, 6), (0.5, 0.53), (-0.25, 0.25), LSTEEL, 0.02)
    bx(p, (-0.25, 0.25), (0.5, 0.53), (-6, 6), LSTEEL, 0.02)
    vcyl(p, 0, 0.5, 0.55, 0, 2.2, DARK, 16)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        bx(p, (5 * math.cos(a) - 0.3, 5 * math.cos(a) + 0.3), (0.5, 0.59), (5 * math.sin(a) - 0.3, 5 * math.sin(a) + 0.3), LSTEEL, 0.03)
    for (x, z, sx, sz) in ((11.7, 0, 1.2, 5), (-11.7, 0, 1.2, 5), (0, 11.7, 5, 1.2), (0, -11.7, 5, 1.2)):   # guide bars
        bx(p, (x - sx / 2, x + sx / 2), (0.3, 0.5), (z - sz / 2, z + sz / 2), HAZ, 0.03)
        if sx < sz:
            bx(p, (x - sx / 2, x + sx / 2), (0.3, 0.52), (z - 0.5, z + 0.5), BLK, 0.02)
        else:
            bx(p, (x - 0.5, x + 0.5), (0.3, 0.52), (z - sz / 2, z + sz / 2), BLK, 0.02)


# ---- 3. Hangar --------------------------------------------------------------------------------------------------------------
def build_Hangar(p):
    bx(p, (-15, 15), (0, 0.3), (-12.6, 12), DDARK, 0.03)                       # inside floor
    bx(p, (-16.6, 16.6), (0.3, 20), (-13, -10.2), STEEL, 0.03)                  # back wall
    for sx in (-1, 1):
        bx(p, (min(sx * 14.2, sx * 16.6), max(sx * 14.2, sx * 16.6)), (0.3, 20), (-11, 11), STEEL, 0.03)
        bx(p, (min(sx * 16.6, sx * 17), max(sx * 16.6, sx * 17)), (15, 16.2), (-11, 11), ORANGE, 0.03)
        for y in (6, 12):                                                         # dark plating bands, outside
            bx(p, (min(sx * 16.6, sx * 17), max(sx * 16.6, sx * 17)), (y, y + 0.7), (-11, 11), DARK, 0.03)
        for z in (-8, 0, 8):                                                       # ribs
            bx(p, (min(sx * 16.6, sx * 17), max(sx * 16.6, sx * 17)), (0.3, 20), (z - 0.4, z + 0.4), PANEL, 0.03)
    for y in (6, 12):
        bx(p, (-14.2, 14.2), (y, y + 0.5), (-10.4, -10.2), DARK, 0.03)
    for x in (-8, 0, 8):                                                          # back wall plates
        bx(p, (x - 0.3, x + 0.3), (0.3, 20), (-10.4, -10.2), DARK, 0.03)
    # roof: dark lower slab, light upper block with ribs, vents, beacons
    bx(p, (-18, 18), (20, 22), (-14, 13.6), DARK, 0.03)
    bx(p, (-15, 15), (22, 24.2), (-11, 11), PANEL, 0.03)
    for x in (-10, -5, 0, 5, 10):
        bx(p, (x - 0.35, x + 0.35), (24.0, 24.2), (-11, 11), STEEL, 0.03)
    for x in (-8, 8):
        vcyl(p, x, 22, 24.4, -4, 1.6, STEEL, 10)
        vcyl(p, x, 24.4, 25, -4, 1.9, DARK, 10)
    for sx in (-1, 1):
        bx(p, (sx * 16.5 - 0.5, sx * 16.5 + 0.5), (22, 23.2), (-12, -11), RED, 0.04)
    text(p, "MECHA", 0, 20.3, 13.6, 14.0, 2.4, 1.4, 0.45, 0.8, HAZ)
    # front beam, columns, blast doors
    stripes(p, (-17, 17), (17, 20), (12.2, 13.8), 9)
    for sx in (-1, 1):
        vcyl(p, sx * 16, 0, 17, 12.9, 1.1, PANEL, 10)
        vcyl(p, sx * 16, 0, 1.6, 12.9, 1.2, HAZ, 10)
        vcyl(p, sx * 16, 1.6, 2.4, 12.9, 1.2, BLK, 10)
        bx(p, (sx * 11.5 - 4, sx * 11.5 + 4), (0, 16), (11.9, 12.9), STEEL, 0.03)       # door leaves
        for y in (4, 8, 12):
            bx(p, (sx * 11.5 - 3.6, sx * 11.5 + 3.6), (y, y + 0.7), (12.9, 13.2), DARK, 0.03)
        xa = sx * 7.5 - (0.0 if sx > 0 else 1.0)
        for i in range(4):
            bx(p, (xa, xa + 1.0), (i * 4, i * 4 + 2), (12.9, 13.3), HAZ, 0.02)
    bx(p, (-16, 16), (16, 17), (11.9, 12.9), DARK, 0.03)                         # door rail
    bx(p, (-13, 13), (0, 1), (11.5, 12.5), HAZ, 0.03)                           # threshold strip
    for x in range(-11, 12, 2):
        if (x // 2) % 2:
            bx(p, (x - 1, x + 1), (0, 1.02), (11.5, 12.5), BLK, 0.02)
    # a parked mecha waits in the bay, seen through the open doors
    for sx in (-1, 1):
        bx(p, (sx * 1.0 - 0.8 if sx > 0 else sx * 2.6, sx * 2.6 if sx > 0 else sx * 1.0 + 0.8), (0.3, 6.2), (-9.2, -6.8), STEEL, 0.03)
        bx(p, (sx * 3.4 - 0.8 if sx > 0 else sx * 4.2, sx * 4.2 if sx > 0 else sx * 3.4 + 0.8), (7.0, 14.4), (-9.4, -6.4), PANEL, 0.03)
    bx(p, (-3.2, 3.2), (6.2, 8.2), (-9.4, -6.6), DARK, 0.03)
    bx(p, (-3.6, 3.6), (8.2, 14.0), (-9.6, -6.4), PANEL, 0.03)
    bx(p, (-2.2, 2.2), (10.0, 12.6), (-6.4, -6.2), HOLO, 0.03)
    bx(p, (-2.0, 2.0), (14.0, 17.4), (-9.2, -6.8), WHITE, 0.03)
    bx(p, (-1.6, 1.6), (15.4, 16.2), (-6.8, -6.6), HOLO, 0.03)
    for sx in (-1, 1):
        bx(p, (sx * 1.2 - 0.5, sx * 1.2 + 0.5), (17.4, 18.8), (-8.4, -7.6), ORANGE, 0.03)
    for z in (0,):                                                                # ceiling light
        bx(p, (-9, 9), (19.6, 20), (z - 0.5, z + 0.5), WHITE, 0.02)


# ---- 4. BonkSign ------------------------------------------------------------------------------------------------------------
def build_BonkSign(p):
    for sx in (-1, 1):
        bx(p, (sx * 8 - 2, sx * 8 + 2), (0, 0.8), (-1.5, 1.5), CONC, 0.04)
        vcyl(p, sx * 8, 0.8, 9.5, 0, 0.6, STEEL, 8)
        bx(p, (sx * 8 - 0.9, sx * 8 + 0.9), (0.8, 2.2), (-0.9, 0.9), DARK, 0.03)
    bx(p, (-11, 11), (5, 11), (-0.5, 0.5), DARK, 0.03)
    bx(p, (-11.3, 11.3), (10.4, 11.2), (-0.8, 0.8), HAZ, 0.03)
    bx(p, (-11.3, 11.3), (4.4, 5.2), (-0.8, 0.8), HAZ, 0.03)
    for sx in (-1, 1):
        bx(p, (sx * 10.2 - 0.3, sx * 10.2 + 0.3), (5.2, 10.4), (-0.7, 0.7), HAZ, 0.03)
    text(p, "GET BONKED", 0, 6.0, 0.5, 0.8, 1.65, 3.4, 0.55, 0.42, HAZ)
    for x in (-9, -4.5, 0, 4.5, 9):                                              # lamp housings on top
        bx(p, (x - 0.8, x + 0.8), (11.2, 11.6), (-0.6, 0.6), DARK, 0.03)
        bx(p, (x - 0.5, x + 0.5), (11.2, 11.6), (0.4, 0.8), WHITE, 0.03)


# ---- 5. Crates ----------------------------------------------------------------------------------------------------------------
def crate(p, c, size, col, yaw, band=None):
    band = band or shade(col, 0.6)
    g = Grp(p, c, yaw)
    sx, sy, sz = size
    g.box((0, 0, 0), (sx, sy, sz), col, 0.05)
    for ax in (-1, 1):
        for az in (-1, 1):                                                            # corner posts
            g.box((ax * (sx / 2 - 0.2), 0, az * (sz / 2 - 0.2)), (0.4, sy + 0.1, 0.4), band, 0.04)
    g.box((0, sy / 2 - 0.1, 0), (sx + 0.1, 0.3, sz + 0.1), band, 0.04)
    g.box((0, -sy / 2 + 0.1, 0), (sx + 0.1, 0.3, sz + 0.1), band, 0.04)
    lab = HAZ if col != HAZ else BLK
    g.box((0, 0, sz / 2 + 0.03), (sx * 0.55, sy * 0.45, 0.14), lab, 0.04)    # label plate
    g.box((0, sy * 0.08, sz / 2 + 0.1), (sx * 0.4, sy * 0.07, 0.08), BLK if lab == HAZ else HAZ, 0.02)
    g.box((0, -sy * 0.08, sz / 2 + 0.1), (sx * 0.25, sy * 0.07, 0.08), BLK if lab == HAZ else HAZ, 0.02)
    return g


def build_Crates(p):
    crate(p, (-2.5, 2.5, -1), (5, 5, 5), ORANGE, 18)
    crate(p, (-2, 7.2, -1), (4, 4.4, 4), STEEL, -25)
    crate(p, (3.5, 2, 2.5), (4, 4, 4), STEEL, -24)
    crate(p, (4, 1.5, -3.5), (3, 3, 3), ORANGE, 30)
    crate(p, (-4, 1.5, 4), (3, 3, 3), HAZ, 12)
    crate(p, (6.5, 0.8, 5), (2, 1.6, 2), RED, -10, band=WHITE)


# ---- 6. Drums -----------------------------------------------------------------------------------------------------------------
def build_Drums(p):
    bx(p, (-5.5, 2.5), (0, 0.6), (-4, 1), DARK, 0.03)                           # pallet
    for z in (-3.7, -1.5, 0.7):
        bx(p, (-5.5, 2.5), (0.45, 0.6), (z - 0.3, z + 0.3), (96, 106, 124), 0.03)
    for x in (-5.3, -1.5, 2.3):
        bx(p, (x - 0.2, x + 0.2), (0, 0.45), (-4, 1), (70, 80, 96), 0.03)
    drum(p, -3.2, -1.6, RED, y0=0.6)
    drum(p, -0.6, -2.2, STEEL, y0=0.6)
    drum(p, 2.0, -1.2, HAZ, y0=0.6)
    drum(p, -2.0, 1.0, ORANGE, y0=0.6)
    drum(p, 0.8, 0.4, RED, y0=0.6)
    drum(p, 4.4, 2.4, STEEL, y0=0)
    drum(p, -4.6, 2.6, DARK, band=STEEL, y0=0)
    g = Grp(p, (1, 1.2, 4.6), 35)                                                    # the rolled one
    g.xcyl((0, 0, 0), 3.4, 1.2, ORANGE, 10)
    for dx in (-1.5, 1.5):
        g.xcyl((dx, 0, 0), 0.3, 1.28, DARK, 8)


# ---- 7. Floodlights ---------------------------------------------------------------------------------------------------------
def mast(p, x, z, h, yaw):
    bx(p, (x - 1.2, x + 1.2), (0, 0.5), (z - 1.2, z + 1.2), DARK, 0.03)
    vcyl(p, x, 0.5, h, z, 0.5, STEEL, 8, top_r=0.35)
    vcyl(p, x, 0.5, 2.0, z, 0.65, HAZ, 8)
    bx(p, (x - 0.5, x + 0.5), (2.2, 3.4), (z + 0.35, z + 0.8), DARK, 0.03)       # junction box
    g = Grp(p, (x, h, z + 0.6), yaw)
    g.box((0, 0.3, 0), (3.4, 1.6, 1.4), DARK, 0.03)
    g.box((0, 1.25, 0.1), (3.6, 0.3, 1.8), STEEL, 0.03)                              # visor
    for ax in (-0.8, 0.8):
        for ay in (-0.1, 0.55):
            g.box((ax, 0.3 + ay, 0.72), (1.35, 0.55, 0.15), WHITE, 0.03)
    g.box((0, -0.8, -0.2), (0.8, 0.8, 0.8), STEEL, 0.03)                             # yoke


def build_Floodlights(p):
    mast(p, -4, 0, 13, 15)
    mast(p, 2, -3, 10, -20)
    mast(p, 5.5, 2.5, 12, 30)


# ---- 8. Console -------------------------------------------------------------------------------------------------------------
def build_Console(p):
    bx(p, (-6.5, 6.5), (0, 0.4), (-3.5, 5.5), DARK, 0.03)
    bx(p, (-5, 5), (0.4, 3.0), (-1.6, 1.6), STEEL, 0.03)
    bx(p, (-5.2, 5.2), (3.0, 3.3), (-1.8, 1.8), LSTEEL, 0.03)
    for sx in (-1, 1):
        g = Grp(p, (sx * 6.2, 0, 2), -35 * sx)
        g.box((0, 1.7, 0), (4, 3, 3), STEEL, 0.03)
        g.box((0, 3.45, 0), (4.2, 0.3, 3.2), LSTEEL, 0.03)
        for i, c in enumerate((RED, HAZ, HOLO)):
            g.box((-1.2 + i * 1.2, 3.7, 0.7), (0.7, 0.25, 0.6), c, 0.03)
    for i, c in enumerate((HOLO, HAZ, RED, WHITE, HOLO, HAZ)):                    # buttons on the main desk
        bx(p, (-4.2 + i * 1.6, -3.4 + i * 1.6), (3.3, 3.55), (0.4, 1.1), c, 0.03)
    bx(p, (-0.3, 0.3), (3.3, 3.9), (-0.9, -0.5), DARK, 0.03)
    bx(p, (-2.5, 2.5), (3.9, 6.2), (-1.05, -0.55), HOLO, 0.03)                    # screens
    bx(p, (-2.8, 2.8), (3.8, 6.4), (-1.25, -1.05), DARK, 0.03)
    for y in (4.6, 5.2, 5.8):
        bx(p, (-2, 1 + (y - 4.6)), (y, y + 0.2), (-0.55, -0.45), WHITE, 0.03)
    for sx in (-1, 1):
        g = Grp(p, (sx * 6.4, 0, 0.6), -35 * sx)
        g.box((0, 3.4, 0), (3.6, 2.4, 0.5), HOLO, 0.03)
        g.box((0, 3.4, -0.3), (3.9, 2.7, 0.2), DARK, 0.03)
        g.box((0, 3.3, 0.3), (2.4, 0.2, 0.1), WHITE, 0.02)
    vcyl(p, 0, 0.4, 1.0, 4.4, 1.2, DARK, 8)                                          # chair
    vcyl(p, 0, 1.0, 1.8, 4.4, 0.25, STEEL, 6)
    vcyl(p, 0, 1.8, 2.4, 4.4, 1.0, ORANGE, 10)
    bx(p, (-1, 1), (2.4, 4.2), (5.0, 5.5), ORANGE, 0.03)
    for a in (0, 90):
        bc(p, (0, 0.55, 4.4), (2.8, 0.2, 0.35), DARK, yaw=a + 45)


# ---- shared pieces for the next parts -----------------------------------------------------------------------------------
def ladder(p, x, y0, y1, z, rung=1.0, w=1.0, col=LSTEEL, depth=0.25, along='z'):
    """Ladder in the x-y plane (rails 0.15 thick) at depth z, rungs every `rung`."""
    for sx in (-1, 1):
        bx(p, (x + sx * w / 2 - 0.08, x + sx * w / 2 + 0.08), (y0, y1), (z - depth / 2, z + depth / 2), col, 0.02)
    y = y0 + rung / 2
    while y < y1:
        bx(p, (x - w / 2, x + w / 2), (y - 0.07, y + 0.07), (z - depth / 2, z + depth / 2), col, 0.02)
        y += rung


def wheel(p, x, cy, z, r, th, tyre=BLK, hub=LSTEEL, verts=8):
    """Wheel with its axis along z, centred at (x, cy, z); thickness th."""
    zcyl(p, x, cy, z - th / 2, z + th / 2, r, tyre, verts, 0.03)
    zcyl(p, x, cy, z - th / 2 - 0.04, z + th / 2 + 0.04, r * 0.5, hub, 6, 0.03)


# ---- 9. Workshop ------------------------------------------------------------------------------------------------------------
def build_Workshop(p):
    bx(p, (-9, 9), (0, 0.3), (-3.4, 4.6), DARK, 0.03)                           # slab
    bx(p, (-10, 10), (0.3, 10), (-5.2, -3.8), STEEL, 0.03)                       # back wall
    for sx in (-1, 1):
        bx(p, (min(sx * 8.6, sx * 10), max(sx * 8.6, sx * 10)), (0.3, 10), (-5.2, 5), STEEL, 0.03)
        bx(p, (min(sx * 8.6, sx * 8.2), max(sx * 8.6, sx * 8.2)), (7.4, 8.2), (-3.8, 4.8), DARK, 0.03)   # inner beams
    for y in (3, 6.5):                                                            # plating bands on the back wall
        bx(p, (-10, 10), (y, y + 0.5), (-3.8, -3.6), DARK, 0.03)
    bx(p, (-10, 10), (0.3, 0.8), (-3.8, -3.5), HAZ, 0.03)
    # pegboard with tools on the back wall
    bx(p, (-7, 3), (4, 8.4), (-3.8, -3.6), PANEL, 0.03)
    bx(p, (-6, -4.6), (5.4, 7.6), (-3.6, -3.35), LSTEEL, 0.03)                   # wrench
    bx(p, (-6.4, -4.2), (7.4, 8.0), (-3.6, -3.35), LSTEEL, 0.03)
    bx(p, (-3.4, -3.0), (4.6, 7.8), (-3.6, -3.35), RED, 0.03)                    # hammer
    bx(p, (-4.0, -2.4), (7.4, 8.1), (-3.6, -3.35), DARK, 0.03)
    bx(p, (-1.4, -0.9), (5.0, 7.6), (-3.6, -3.35), HAZ, 0.03)                    # screwdriver
    bx(p, (0.4, 2.4), (5.2, 6.0), (-3.6, -3.35), ORANGE, 0.03)                   # drill
    bx(p, (0.4, 1.0), (4.6, 5.2), (-3.6, -3.35), DARK, 0.03)
    # roof, fascia, front posts
    bx(p, (-11, 11), (10, 11.2), (-6, 6), HAZ, 0.03)
    for x in (-8, -3, 3, 8):
        bx(p, (x - 0.2, x + 0.2), (11.2, 11.4), (-6, 6), ORANGE, 0.03)
    bx(p, (-10, 10), (8.4, 10), (5.0, 5.6), DARK, 0.03)
    text(p, "REPAIR", 0, 8.75, 5.6, 5.95, 1.8, 0.95, 0.3, 0.35, HAZ)
    for sx in (-1, 1):
        vcyl(p, sx * 9.6, 0.3, 8.7, 5.6, 0.4, HAZ, 8)
    # workbench with a vise and a toolbox
    bx(p, (-5, 5), (0, 3), (1, 3.4), PANEL, 0.03)
    bx(p, (-5.3, 5.3), (3, 3.4), (0.8, 3.6), LSTEEL, 0.03)
    bx(p, (-4, 4), (0.5, 2.5), (3.4, 3.5), DARK, 0.03)
    bx(p, (-5.7, -4.3), (3.4, 4.2), (1.5, 2.9), DARK, 0.03)
    bx(p, (-5.3, -4.7), (4.2, 4.5), (1.9, 2.5), STEEL, 0.03)
    bx(p, (0.5, 3.5), (3.4, 4.6), (1.6, 2.8), RED, 0.03)
    bx(p, (1.5, 2.5), (4.6, 4.9), (2.0, 2.4), DARK, 0.03)
    bx(p, (-2.5, -0.5), (3.4, 3.8), (1.5, 2.9), ORANGE, 0.03)
    # barrel, chimney with smoke
    drum(p, 6.5, 2, RED, r=1.2, h=3.4, y0=0.3, band=DARK, verts=10)
    vcyl(p, -6.5, 10.5, 13.9, -2, 0.8, DARK, 8)
    vcyl(p, -6.5, 13.9, 14.2, -2, 1.05, STEEL, 8)
    ball(p, (-6.5, 14.7, -2), 0.8, (170, 176, 188), subdiv=1, jit=0.05)
    ball(p, (-6.1, 15.4, -2.1), 0.65, (190, 196, 206), subdiv=1, jit=0.05)
    # hanging lamp
    bx(p, (-0.2, 0.2), (8.4, 10), (0.9, 1.3), DARK, 0.03)
    bx(p, (-0.9, 0.9), (7.9, 8.4), (0.5, 1.7), STEEL, 0.03)
    bx(p, (-0.7, 0.7), (7.85, 7.95), (0.7, 1.5), WHITE, 0.02)


# ---- 10. FuelTanks ----------------------------------------------------------------------------------------------------------
def build_FuelTanks(p):
    bx(p, (-8.5, 8.5), (0, 0.55), (-5.5, 5.5), DARK, 0.03)
    for x in (-4.4, 2.6):                                                        # saddles
        bx(p, (x - 0.6, x + 0.6), (0.55, 3.0), (-1.5, 3.5), DARK, 0.03)
    # horizontal tank (rounded ends) with bands, hatch and ladder
    xcyl(p, -5.5, 3.5, 3.8, 1, 2.5, PANEL, 12)
    ball(p, (-5.5, 3.8, 1), 2.5, PANEL, scale=(0.4, 1, 1), subdiv=2)
    ball(p, (3.5, 3.8, 1), 2.5, PANEL, scale=(0.4, 1, 1), subdiv=2)
    for x in (-4.4, 2.6):
        xcyl(p, x - 0.45, x + 0.45, 3.8, 1, 2.62, DARK, 12)
    xcyl(p, -1.3, -0.7, 3.8, 1, 2.62, HAZ, 12)
    bx(p, (-1.7, -0.3), (6.3, 6.7), (0.3, 1.7), HAZ, 0.03)
    # vertical tank
    vcyl(p, 5.8, 0, 10.6, -3, 2.2, STEEL, 12)
    for y in (2.4, 5.8):
        vcyl(p, 5.8, y, y + 0.5, -3, 2.32, DARK, 12)
    vcyl(p, 5.8, 8.8, 9.6, -3, 2.3, HAZ, 12)
    vcyl(p, 5.8, 10.6, 11.4, -3, 1.5, STEEL, 12, top_r=0.8)
    ladder(p, 7.6, 0.3, 10.4, -1.6, rung=1.0, w=0.9, col=LSTEEL, depth=0.3)
    # pipe, valve, gauge
    xcyl(p, -1.1, 3.6, 2.4, -3, 0.4, DARK, 8)
    bx(p, (-1.6, -1.0), (1.6, 3.2), (-3.4, -2.6), DARK, 0.03)
    vcyl(p, 1.2, 2.4, 3.4, -3, 0.18, RED, 6)
    bx(p, (0.6, 1.8), (3.4, 3.7), (-3.4, -2.6), RED, 0.03)
    # vent pipe + hazard block on top
    bx(p, (-5.9, -5.1), (0, 6), (-3.9, -3.1), DARK, 0.03)
    bx(p, (-6.1, -4.9), (5.8, 6.2), (-4.1, -2.9), HAZ, 0.03)


# ---- 11. Radar --------------------------------------------------------------------------------------------------------------
def build_Radar(p):
    bx(p, (-4.5, 4.5), (0, 1.6), (-4.5, 4.5), CONC, 0.04)
    bx(p, (-3.8, 3.8), (1.6, 1.9), (-3.8, 3.8), DARK, 0.03)
    bx(p, (-1.2, 1.2), (1.9, 10.5), (-1.2, 1.2), STEEL, 0.03)
    for y in (3, 5.5, 8):
        bx(p, (-1.35, 1.35), (y, y + 0.5), (-1.35, 1.35), DARK, 0.03)
    bx(p, (-2, 2), (10.2, 12.6), (-2, 2), PANEL, 0.03)
    bx(p, (-2.1, 2.1), (12.4, 12.6), (-2.1, 2.1), HAZ, 0.03)
    # dish: rim ring, recessed face, hub, feed arms
    zcyl(p, 0, 14.4, 0.8, 1.3, 1.5, STEEL, 8)
    zcyl(p, 0, 14.4, 1.0, 1.7, 3.5, WHITE, 16)
    zcyl(p, 0, 14.4, 1.4, 2.0, 4.5, WHITE, 24)
    zcyl(p, 0, 14.4, 1.9, 2.0, 3.9, LSTEEL, 24, 0.03)
    zcyl(p, 0, 14.4, 1.9, 2.1, 0.7, DARK, 8)
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        bar(p, (3.3 * math.cos(a), 14.4 + 3.3 * math.sin(a), 2.0), (0, 14.4, 4.8), 0.25, LSTEEL, 0.02)
    bx(p, (-0.3, 0.3), (14.1, 14.7), (2.0, 4.8), STEEL, 0.03)
    bx(p, (-0.7, 0.7), (13.7, 15.1), (4.7, 6.1), RED, 0.03)
    # equipment shed + conduit
    bx(p, (4.1, 7.1), (0, 3.2), (-3.5, -0.5), PANEL, 0.03)
    bx(p, (3.9, 7.3), (3.2, 3.5), (-3.7, -0.3), DARK, 0.03)
    bx(p, (5.0, 6.2), (0.0, 2.1), (-0.52, -0.3), DARK, 0.03)
    bx(p, (5.4, 5.8), (1.6, 1.9), (-0.3, -0.2), HAZ, 0.03)
    vcyl(p, -3.4, 1.9, 6.0, 2.4, 0.25, DARK, 6)
    bx(p, (-3.8, -3.0), (5.6, 6.0), (2.0, 2.8), HAZ, 0.03)


# ---- 12. Barracks -----------------------------------------------------------------------------------------------------------
def build_Barracks(p):
    bx(p, (-10, 10), (0, 8), (-6.5, 6.5), PANEL, 0.03)
    for y in (2.4, 6.4):
        bx(p, (-10.1, 10.1), (y, y + 0.4), (-6.6, 6.6), STEEL, 0.03)
    bx(p, (-10.7, 10.7), (8, 9.6), (-7.2, 7.2), DARK, 0.03)
    bx(p, (-10.7, 10.7), (8, 8.4), (7.2, 7.4), HAZ, 0.03)
    bx(p, (-9, 9), (9.6, 10.8), (-2, 2), STEEL, 0.03)
    for x in (-6, -2, 2, 6):
        bx(p, (x - 0.2, x + 0.2), (10.8, 11.1), (-2, 2), DARK, 0.03)
    # door: hazard stripes + frame + number plate
    bx(p, (-4.8, -1.2), (0, 4.8), (6.5, 6.8), DARK, 0.03)
    bx(p, (-4.5, -1.5), (0, 4.4), (6.8, 6.9), HAZ, 0.03)
    for i in range(4):
        bx(p, (-4.5, -1.5), (i * 1.1 + 0.1, i * 1.1 + 0.6), (6.9, 6.95), BLK, 0.02)
    # glowing windows
    for x in (4, 8, -8):
        bx(p, (x - 1.5, x + 1.5), (4.3, 6.1), (6.5, 6.7), DARK, 0.03)
        bx(p, (x - 1.2, x + 1.2), (4.6, 5.8), (6.7, 6.9), HOLO, 0.03)
        bx(p, (x - 0.1, x + 0.1), (4.6, 5.8), (6.9, 6.95), DARK, 0.02)
    for sx in (-1, 1):
        for z in (-3, 1.5):
            bx(p, (sx * 10 - (0 if sx > 0 else 0.15), sx * 10 + (0.15 if sx > 0 else 0)), (4.3, 5.9), (z - 1, z + 1), HOLO, 0.03)
    # steps, vent stack, sign
    bx(p, (-5.5, -0.5), (0, 0.6), (7.0, 10.1), CONC, 0.03)
    vcyl(p, 6.5, 9.6, 12.4, -3, 0.8, DARK, 8)
    vcyl(p, 6.5, 12.4, 12.7, -3, 1.1, STEEL, 8)
    text(p, "PILOTS", 3, 8.15, 7.2, 7.5, 1.45, 1.3, 0.4, 0.3, HAZ)
    bx(p, (-5.2, -0.8), (4.8, 5.1), (6.5, 7.6), DARK, 0.03)
    for x in (-8.5, 8.5):                                                       # lamps at the corners
        bx(p, (x - 0.4, x + 0.4), (6.8, 7.4), (6.5, 7.1), WHITE, 0.03)


# ---- 13. MissileRack --------------------------------------------------------------------------------------------------------
def missile(p, y, z=0.0):
    xcyl(p, -4.8, 3.6, y, z, 0.8, WHITE, 10)
    dk.cyl(p, (OX + 4.8, y, OZ + z), 0.8, 2.4, RED, axis='x', verts=10, top_radius=0.12, jitter=0.04)
    xcyl(p, 0.8, 1.4, y, z, 0.88, HAZ, 10)
    for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):                            # tail fins
        bx(p, (-4.8, -3.6), (y + dy * 0.85 - (0.5 if dy else 0.05), y + dy * 0.85 + (0.5 if dy else 0.05)),
           (z + dz * 0.85 - (0.5 if dz else 0.05), z + dz * 0.85 + (0.5 if dz else 0.05)), DARK, 0.03)


def build_MissileRack(p):
    bx(p, (-6, 6), (0, 1), (-2.5, 2.5), DARK, 0.03)
    stripes(p, (-6, 6), (0, 0.5), (2.5, 2.7), 6)
    for sx in (-1, 1):
        bx(p, (sx * 4.5 - 0.4, sx * 4.5 + 0.4), (1, 7.5), (-1.5, 1.5), STEEL, 0.03)
        for y in (2.4, 4.4, 6.4):                                                # cradles
            bx(p, (sx * 4.5 - 0.5, sx * 4.5 + 0.5), (y - 1.1, y - 0.8), (-1.1, 1.1), DARK, 0.03)
    for y in (2.4, 4.4, 6.4):
        missile(p, y)
    bx(p, (-5, 5), (7.4, 8.0), (-1.7, 1.7), HAZ, 0.03)
    for x in (-3, -1, 1, 3):
        bx(p, (x - 0.4, x + 0.4), (7.4, 8.01), (-1.7, 1.7), BLK, 0.02)
    bx(p, (-0.3, 0.3), (1, 7.4), (-1.5, -1.2), DARK, 0.03)


# ---- 14. DronePad -----------------------------------------------------------------------------------------------------------
def quad(p, x, z, yaw, body):
    g = Grp(p, (x, 0, z), yaw)
    g.cyl((0, 0.3, 0), 0.5, 2.4, STEEL, 6)
    g.cyl((0, 0.3, 0), 1.1, 0.25, DARK, 8)
    g.box((0, 3.2, 0), (2.2, 1.0, 2.2), body, 0.04)
    g.box((0, 3.75, 0.9), (1.2, 0.3, 0.3), HOLO, 0.03)                              # front sensor strip
    for ang in (45, 135):
        g.box((0, 3.3, 0), (3.6, 0.3, 0.4), DARK, 0.03, yaw=ang)
    for sx in (-1, 1):
        for sz in (-1, 1):
            gx, gz = sx * 1.3, sz * 1.3
            g.box((gx, 3.5, gz), (0.5, 0.4, 0.5), STEEL, 0.03)
            g.cyl((gx, 3.7, gz), 0.8, 0.1, BLK, 6, jit=0.04)
            g.cyl((gx, 3.7, gz), 0.18, 0.2, LSTEEL, 5, jit=0.03)


def build_DronePad(p):
    bx(p, (-6.5, 6.5), (-0.05, 0.25), (-6.5, 6.5), DARK, 0.03)
    bx(p, (-5.5, 5.5), (0.25, 0.5), (-5.5, -5.0), HAZ, 0.03)
    bx(p, (-5.5, 5.5), (0.25, 0.5), (5.0, 5.5), HAZ, 0.03)
    bx(p, (-5.5, -5.0), (0.25, 0.5), (-5.0, 5.0), HAZ, 0.03)
    bx(p, (5.0, 5.5), (0.25, 0.5), (-5.0, 5.0), HAZ, 0.03)
    for (cx, cz) in ((-2.6, -1.6), (2.8, -2), (0, 3)):                             # landing circles
        vcyl(p, cx, 0.25, 0.3, cz, 2.1, HAZ, 12, jit=0.02)
        vcyl(p, cx, 0.3, 0.33, cz, 1.7, DARK, 12, jit=0.02)
    for k in range(4):
        a = math.radians(45 + 90 * k)
    quad(p, -2.6, -1.6, 20, STEEL)
    quad(p, 2.8, -2, -25, STEEL)
    quad(p, 0, 3, 10, HAZ)


# ---- 15. RepairArm ----------------------------------------------------------------------------------------------------------
def build_RepairArm(p):
    bx(p, (-8, 8), (0, 1), (-6, 6), DARK, 0.03)
    stripes(p, (-8, 8), (0, 0.5), (6, 6.2), 8)
    # gantry
    for sx in (-1, 1):
        bx(p, (sx * 7 - 0.8, sx * 7 + 0.8), (1, 14), (-4.8, -3.2), HAZ, 0.03)
    bx(p, (-8, 8), (13.7, 15.1), (-4.9, -3.1), HAZ, 0.03)
    stripes(p, (-8, 8), (13.7, 14.0), (-3.1, -2.95), 8)
    for sx in (-1, 1):
        prism_z(p, [(sx * 6.2, 13.7), (sx * 3.6, 13.7), (sx * 6.2, 11.1)], -4.6, -3.4, DARK, 0.03)
        for y in (2.5, 5.5, 8.5, 11.0):
            bx(p, (sx * 7 - 0.85, sx * 7 + 0.85), (y, y + 0.7), (-4.85, -3.15), BLK, 0.02)
    bx(p, (-6.2, 6.2), (6.6, 7.2), (-4.2, -3.8), STEEL, 0.03)                    # cross brace between the posts
    # trolley + arm
    bx(p, (1, 3), (11.4, 13.7), (-5, -3), STEEL, 0.03)
    bx(p, (1.6, 3.2), (7.1, 11.4), (-3.6, -2.4), PANEL, 0.03)
    ball(p, (2.4, 7.0, -3.0), 0.95, DARK, subdiv=1)
    bar(p, (2.4, 7.0, -3.0), (2.8, 6.8, -2.0), 0.9, PANEL, 0.03)
    ball(p, (2.8, 6.8, -2.0), 0.95, STEEL, subdiv=1)
    bx(p, (2.3, 3.3), (4.9, 5.9), (-2.1, 2.1), PANEL, 0.03)
    bx(p, (2.0, 3.6), (4.4, 4.8), (1.6, 2.1), DARK, 0.03)                         # claw
    bx(p, (2.0, 2.3), (4.4, 5.9), (1.4, 2.1), DARK, 0.03)
    bx(p, (3.3, 3.6), (4.4, 5.9), (1.4, 2.1), DARK, 0.03)
    # mecha leg in its cradle
    bx(p, (-3.5, 1.5), (1, 2.2), (0.5, 5.5), DARK, 0.03)
    bx(p, (-3.3, 1.3), (2.2, 3.0), (0.7, 5.3), ORANGE, 0.03)                       # foot
    hexa(p, [(-1.0, 3.0, 1.9), (0.0, 3.0, 1.9), (0.0, 3.0, 4.1), (-1.0, 3.0, 4.1),
             (-1.6, 5.2, 1.4), (0.6, 5.2, 1.4), (0.6, 5.2, 4.6), (-1.6, 5.2, 4.6)], STEEL, 0.03)   # shin, narrow at the ankle
    bx(p, (-0.9, -0.1), (3.6, 4.4), (4.1, 4.5), HAZ, 0.03)
    for sx in (-1, 1):                                                           # hydraulic pistons
        vcyl(p, -0.5 + sx * 1.5, 2.6, 5.4, 4.5, 0.28, LSTEEL, 6)
    xcyl(p, -3.0, 1.0, 5.4, 3, 0.95, DARK, 8)
    bx(p, (-3.2, 1.2), (5.2, 7.2), (0.8, 5.2), PANEL, 0.03)
    bx(p, (-3.3, 1.3), (6.0, 6.4), (0.7, 5.3), HAZ, 0.03)
    for sx in (-1, 1):                                                           # cradle frames
        bx(p, (-1 + sx * 2.9 - 0.3, -1 + sx * 2.9 + 0.3), (2.2, 6.8), (5.2, 5.8), HAZ, 0.03)
    bx(p, (-3.2, 1.2), (6.5, 6.9), (5.2, 5.8), HAZ, 0.03)
    # work light
    bx(p, (-7.4, -6.2), (7.6, 8.6), (-4.7, -3.3), WHITE, 0.03)
    bx(p, (-7.6, -6.0), (8.4, 8.8), (-4.8, -3.2), DARK, 0.03)


# ---- 16. Transport ----------------------------------------------------------------------------------------------------------
def build_Transport(p):
    bx(p, (-10, 3), (2.2, 3.0), (-2.2, 2.2), DARK, 0.03)                         # flatbed
    bx(p, (-10, 3), (3.0, 3.35), (-2.25, -1.85), HAZ, 0.03)
    bx(p, (-10, 3), (3.0, 3.35), (1.85, 2.25), HAZ, 0.03)
    for x in (-9.6, -5, -0.5, 2.6):
        bx(p, (x - 0.25, x + 0.25), (3.0, 3.9), (-2.25, -1.85), STEEL, 0.03)
        bx(p, (x - 0.25, x + 0.25), (3.0, 3.9), (1.85, 2.25), STEEL, 0.03)
    bx(p, (-10, 9), (1.6, 2.2), (-1.4, 1.4), DARK, 0.03)                        # chassis
    # cab
    bx(p, (3.9, 7.6), (1.3, 5.7), (-2.3, 2.3), ORANGE, 0.04)                     # cabin
    bx(p, (3.8, 7.7), (5.7, 6.0), (-2.4, 2.4), DARK, 0.04)
    bx(p, (7.6, 8.9), (1.3, 3.9), (-2.2, 2.2), ORANGE, 0.04)                     # hood
    bx(p, (7.6, 7.9), (3.7, 5.8), (-1.9, 1.9), HOLO, 0.03)                       # windscreen
    bx(p, (5.0, 7.0), (3.7, 5.6), (2.3, 2.4), HOLO, 0.03)                        # side windows
    bx(p, (5.0, 7.0), (3.7, 5.6), (-2.4, -2.3), HOLO, 0.03)
    bx(p, (8.9, 9.0), (1.6, 3.5), (-1.8, 1.8), DARK, 0.03)                       # grille
    for k in range(3):
        bx(p, (8.9, 9.05), (1.9 + k * 0.5, 2.1 + k * 0.5), (-1.4, 1.4), LSTEEL, 0.03)
    for z in (-1.6, 1.6):
        bx(p, (8.85, 9.05), (3.0, 3.6), (z - 0.35, z + 0.35), WHITE, 0.03)
    bx(p, (8.4, 9.1), (1.0, 1.4), (-2.0, 2.0), HAZ, 0.03)
    vcyl(p, 3.4, 3.0, 6.1, -1.9, 0.3, STEEL, 6)                                  # exhaust stack
    xcyl(p, 0.9, 3.5, 1.55, 2.5, 0.6, STEEL, 8)                                  # side fuel tank
    xcyl(p, 1.3, 1.5, 1.55, 2.5, 0.68, DARK, 8)
    xcyl(p, 2.9, 3.1, 1.55, 2.5, 0.68, DARK, 8)
    bx(p, (-10.0, -9.75), (1.7, 2.1), (-1.0, -0.4), RED, 0.03)
    bx(p, (-10.0, -9.75), (1.7, 2.1), (0.4, 1.0), RED, 0.03)
    bx(p, (5.0, 6.4), (6.0, 6.3), (-0.6, 0.6), HAZ, 0.03)                        # roof beacon
    for (x, z) in ((7, 2.4), (7, -2.4), (-1, 2.4), (-1, -2.4), (-6.4, 2.4), (-6.4, -2.4)):
        wheel(p, x, 1.3, z, 1.3, 0.8)
    # cargo: a spare mecha arm tied down with straps
    bx(p, (-9.3, -6.7), (3.35, 5.95), (-1.3, 1.3), PANEL, 0.03)                  # shoulder
    bx(p, (-9.3, -9.0), (3.8, 5.5), (-0.8, 0.8), HAZ, 0.03)
    xcyl(p, -6.7, -0.2, 4.4, 0, 1.1, STEEL, 10)
    ball(p, (-0.2, 4.4, 0), 1.25, DARK, subdiv=1)
    xcyl(p, -0.2, 1.5, 4.4, 0, 0.95, PANEL, 10)
    for dz in (-0.6, 0.6):
        bx(p, (1.1, 1.5), (3.8, 5.0), (dz - 0.2, dz + 0.2), DARK, 0.03)
    for x in (-5.4, -2.2):
        bx(p, (x - 0.25, x + 0.25), (3.35, 5.7), (-1.5, 1.5), HAZ, 0.03)


# ---- 17. PartsRack ----------------------------------------------------------------------------------------------------------
def build_PartsRack(p):
    for x in (-6, -2, 2, 6):                                                      # uprights
        bx(p, (x - 0.4, x + 0.4), (0, 8.2), (-1.5, 1.5), STEEL, 0.03)
    for i, y in enumerate((2.4, 5.2)):                                            # shelf planks
        bx(p, (-6.5, 6.5), (y - 0.3, y + 0.3), (-1.7, 1.7), PANEL, 0.03)
        bx(p, (-6.5, 6.5), (y - 0.3, y - 0.1), (1.7, 1.8), HAZ, 0.03)
    bx(p, (-6.5, 6.5), (7.9, 8.3), (-1.7, 1.7), PANEL, 0.03)
    for x in (-4, 0, 4):
        bx(p, (x - 1.4, x + 1.4), (8.3, 8.5), (-1.2, 1.2), [RED, HAZ, ORANGE][int(x / 4) + 1], 0.03)
    bx(p, (-6.5, 6.5), (7.9, 8.1), (1.7, 1.8), HAZ, 0.03)
    # floor level: crates and a cog
    bx(p, (-5.2, -2.6), (0, 2.1), (-1.2, 1.2), DARK, 0.03)
    bx(p, (-5.0, -2.8), (0.6, 1.6), (1.2, 1.3), HAZ, 0.03)
    bx(p, (-1.7, 1.7), (0, 1.4), (-1.3, 1.3), DARK, 0.03)
    bx(p, (2.6, 5.4), (0, 1.8), (-1.2, 1.2), ORANGE, 0.03)
    bx(p, (2.4, 5.6), (1.2, 1.5), (-1.3, 1.3), DARK, 0.03)
    # shelf 1: two spare orange arms
    for (cx, ln) in ((-2.8, 6.0), (3.2, 5.0)):
        xcyl(p, cx - ln / 2, cx + ln / 2, 3.6, 0, 0.9, ORANGE, 10)
        ball(p, (cx - ln / 2, 3.6, 0), 0.95, DARK, subdiv=1)
        bx(p, (cx + ln / 2, cx + ln / 2 + 0.5), (3.0, 4.2), (-0.7, 0.7), STEEL, 0.03)
        bx(p, (cx - 0.3, cx + 0.3), (2.7, 4.6), (-1.0, 1.0), HAZ, 0.03)
    # shelf 2: a boot and a helmet
    bx(p, (-5.6, -2.4), (5.5, 6.5), (-1.2, 1.2), DARK, 0.03)                       # sole
    bx(p, (-5.4, -3.6), (6.5, 7.7), (-1.1, 1.1), STEEL, 0.03)                      # shaft
    bx(p, (-3.8, -2.6), (6.5, 7.1), (-1.0, 1.0), STEEL, 0.03)                      # toe
    ball(p, (4, 6.8, 0), 1.35, WHITE, scale=(1, 0.95, 1), subdiv=2, jit=0.03)
    bx(p, (3.0, 5.0), (6.8, 7.5), (0.6, 1.4), HOLO, 0.03)                          # visor
    bx(p, (2.55, 2.85), (6.4, 7.2), (-0.6, 0.6), RED, 0.03)
    bx(p, (5.15, 5.45), (6.4, 7.2), (-0.6, 0.6), RED, 0.03)
    # top shelf: toolboxes


# ---- 18. Walkers ------------------------------------------------------------------------------------------------------------
def walker(p, c, yaw, lh, bw, bh, bd, body, accent=ORANGE):
    """Two-legged scout: c = body centre x, z; yaw turns it; lh = leg height; body box bw x bh x bd."""
    g = Grp(p, (c[0], 0, c[1]), yaw)
    hip = lh
    for sx in (-1, 1):
        lx = sx * bw * 0.28
        up = g.pos((lx, hip, 0))
        knee = g.pos((lx, hip * 0.55, -0.7))
        foot = g.pos((lx, 0.5, 0.35))
        bar(p, up, knee, bw * 0.2, DARK, 0.03)
        bar(p, knee, foot, bw * 0.17, DARK, 0.03)
        ball(p, knee, bw * 0.17, STEEL, subdiv=1, jit=0.03)
        g.box((lx, 0.2, 0.55), (bw * 0.32, 0.4, bw * 0.5), STEEL, 0.03)             # foot pad
    g.box((0, hip + bh / 2, 0), (bw, bh, bd), body, 0.03)
    g.box((0, hip + bh * 0.2, bd / 2 + 0.05), (bw * 0.9, 0.3, 0.12), accent, 0.03)    # belt stripe
    g.box((0, hip + bh + bh * 0.3, 0.25), (bw * 0.7, bh * 0.6, bd * 0.7), PANEL, 0.03)     # cockpit housing
    g.box((0, hip + bh + bh * 0.33, 0.25 + bd * 0.35 + 0.04), (bw * 0.55, bh * 0.35, 0.1), HOLO, 0.03)   # canopy glass
    for sx in (-1, 1):                                                           # headlamps
        g.box((sx * bw * 0.36, hip + bh * 0.7, bd / 2 + 0.06), (bw * 0.14, bh * 0.2, 0.12), WHITE, 0.03)
    g.box((bw / 2 + 0.55, hip + bh * 0.55, 0.4), (0.7, 0.7, bd * 0.9), accent, 0.03)    # arm gun
    g.box((bw / 2 + 0.55, hip + bh * 0.55, bd * 0.45 + 0.9), (0.3, 0.3, 1.2), DARK, 0.03)
    g.box((-bw * 0.3, hip + bh + bh * 0.5, -0.4), (0.2, bh * 0.6, 0.2), STEEL, 0.03)   # antenna
    for sx in (-1, 1):                                                           # Shiba ears on the cockpit
        g.box((sx * bw * 0.26, hip + bh + bh * 0.72, 0.5), (bw * 0.14, bh * 0.4, bw * 0.12), accent, 0.03)


def build_Walkers(p):
    walker(p, (-1.7, 0.6), 25, 3.0, 4.6, 2.6, 3.6, STEEL, ORANGE)
    walker(p, (6.0, 2.3), -35, 3.6, 5.6, 3.2, 4.4, ORANGE, STEEL)


# ---- 19. Range --------------------------------------------------------------------------------------------------------------
def target(p, x, z):
    bx(p, (x - 1.4, x + 1.4), (0, 0.5), (z - 1.0, z + 1.0), DARK, 0.03)
    vcyl(p, x, 0.5, 5.2, z, 0.3, STEEL, 6)
    zcyl(p, x, 5.8, z - 0.55, z - 0.2, 1.8, WHITE, 14, 0.03)
    zcyl(p, x, 5.8, z - 0.2, z + 0.0, 1.35, RED, 14, 0.03)
    zcyl(p, x, 5.8, z + 0.0, z + 0.15, 0.9, WHITE, 12, 0.03)
    zcyl(p, x, 5.8, z + 0.15, z + 0.3, 0.45, RED, 10, 0.03)


def build_Range(p):
    target(p, -6, -3.6)
    target(p, 0, -5.6)
    target(p, 6, -2.6)
    # sandbag wall: staggered rows of bags
    rows = (((-5.75, -3.25, -0.75, 1.75), 0.0), ((-4.5, -2.0, 0.5), 0.8), ((-5.2, -2.7), 1.6))
    for r, (xs, y) in enumerate(rows):
        for i, x in enumerate(xs):
            bc(p, (x, y + 0.4, 5), (2.4, 0.8, 2.3), shade(CONC, 0.9 + 0.12 * ((i + r) % 2)), yaw=(i * 6 - 5) * (1 if r % 2 == 0 else -1), jit=0.05)
    # ammo crate with hazard top
    bx(p, (4, 7), (0, 1.6), (3.2, 5.6), HAZ, 0.03)
    bx(p, (4, 7), (0.7, 0.95), (3.1, 5.7), DARK, 0.03)
    bx(p, (4.2, 4.5), (0, 1.7), (3.1, 5.7), DARK, 0.03)
    bx(p, (6.5, 6.8), (0, 1.7), (3.1, 5.7), DARK, 0.03)
    # scoreboard sign on a post


# ---- 20. Barriers -----------------------------------------------------------------------------------------------------------
def jersey(p, c, yaw, L=4.4):
    g = Grp(p, (c[0], 0, c[1]), yaw)
    h = L / 2
    pts_lo = [(-h, 0, -0.8), (h, 0, -0.8), (h, 0, 0.8), (-h, 0, 0.8), (-h, 1.0, -0.55), (h, 1.0, -0.55), (h, 1.0, 0.55), (-h, 1.0, 0.55)]
    pts_hi = [(-h, 1.0, -0.55), (h, 1.0, -0.55), (h, 1.0, 0.55), (-h, 1.0, 0.55), (-h, 2.7, -0.4), (h, 2.7, -0.4), (h, 2.7, 0.4), (-h, 2.7, 0.4)]
    for pts, col in ((pts_lo, CONC), (pts_hi, LCONC)):
        loc = []
        for (x, y, z) in pts:
            q = g.pos((x, y, z))
            loc.append(q)
        hexa(p, loc, col, 0.04)
    n = 6
    for i in range(n):                                                           # hazard top band
        x0 = -h + L * i / n
        g.box((x0 + L / (2 * n), 3.0, 0), (L / n, 0.7, 0.9), HAZ if i % 2 == 0 else BLK, 0.03)


def build_Barriers(p):
    jersey(p, (-5, 0), 5)
    jersey(p, (0, 1.5), -20)
    jersey(p, (5, 0), 25)
    jersey(p, (-2, -3.4), -8)
    jersey(p, (3, -3.8), 60)


# ---- 21. Silos --------------------------------------------------------------------------------------------------------------
def silo(p, x, z):
    vcyl(p, x, 0.8, 13.4, z, 3.0, PANEL, 14)
    for y in (3.0, 7.8, 11.2):
        vcyl(p, x, y, y + 0.4, z, 3.1, STEEL, 14)
    vcyl(p, x, 4.4, 5.6, z, 3.2, HAZ, 14)
    for k in range(7):                                                            # black hazard blocks on the band
        a = math.radians(k * 51.4)
    ball(p, (x, 13.4, z), 3.0, STEEL, scale=(1, 0.8, 1), subdiv=2, jit=0.04)
    vcyl(p, x, 15.2, 17.0, z, 0.5, DARK, 6)
    vcyl(p, x, 17.0, 17.7, z, 0.85, HAZ, 6)
    bx(p, (x - 0.9, x + 0.9), (0.8, 3.8), (z + 2.6, z + 3.2), DARK, 0.03)         # hatch door
    bx(p, (x - 0.6, x + 0.6), (1.0, 3.6), (z + 3.1, z + 3.25), STEEL, 0.03)


def build_Silos(p):
    bx(p, (-6.5, 6.5), (0, 0.8), (-4.5, 4.5), DARK, 0.03)
    stripes(p, (-6.5, 6.5), (0, 0.5), (4.5, 4.6), 8)
    silo(p, -3.2, -1)
    silo(p, 3.2, 1)
    xcyl(p, -3.2, 3.2, 2.0, 0.0, 0.4, DARK, 6)                                    # pipe between the silos near the foot
    ladder(p, -3.2, 0.8, 12.6, 2.4, rung=1.0, w=0.8, col=LSTEEL, depth=0.35)
    ladder(p, 3.2, 0.8, 12.6, 4.4, rung=1.0, w=0.8, col=LSTEEL, depth=0.35)
    bx(p, (-3.6, -2.8), (12.6, 12.8), (2.2, 2.6), DARK, 0.03)
    bx(p, (2.8, 3.6), (12.6, 12.8), (4.2, 4.6), DARK, 0.03)


# ---- 22. Tower --------------------------------------------------------------------------------------------------------------
def build_Tower(p):
    bx(p, (-4.5, 4.5), (0, 6), (-4.5, 4.5), PANEL, 0.03)
    bx(p, (-4.8, 4.8), (5.6, 6.2), (-4.8, 4.8), DARK, 0.03)
    bx(p, (-4.6, 4.6), (0, 0.8), (-4.6, 4.6), HAZ, 0.03)
    bx(p, (-1.4, 1.4), (0.8, 4.4), (4.5, 4.7), DARK, 0.03)                         # door
    bx(p, (-1.1, 1.1), (0.8, 4.0), (4.7, 4.8), HAZ, 0.03)
    for x in (-3.2, 3.2):
        bx(p, (x - 0.7, x + 0.7), (2.6, 4.2), (4.5, 4.7), HOLO, 0.03)
    bx(p, (-2.5, 2.5), (0, 0.8), (4.5, 8.4), CONC, 0.03)                           # steps
    # shaft with lift stripes
    bx(p, (-2, 2), (6.2, 19), (-2, 2), STEEL, 0.03)
    for y in (8.5, 12.5, 16.5):
        bx(p, (-2.15, 2.15), (y, y + 0.9), (-2.15, 2.15), HAZ, 0.03)
    ladder(p, 0, 6.2, 18.8, 2.2, rung=1.0, w=1.0, col=LSTEEL, depth=0.3)
    # cab
    bx(p, (-5, 5), (19, 24), (-5, 5), DARK, 0.03)
    bx(p, (-5.3, 5.3), (19, 19.6), (-5.3, 5.3), STEEL, 0.03)
    bx(p, (-5.3, 5.3), (20.3, 22.7), (-5.3, 5.3), HOLO, 0.03)
    for x in (-5, -2.5, 0, 2.5, 5):                                               # window mullions
        bx(p, (x - 0.2, x + 0.2), (20.2, 22.8), (5.2, 5.4), DARK, 0.03)
        bx(p, (x - 0.2, x + 0.2), (20.2, 22.8), (-5.4, -5.2), DARK, 0.03)
    for z in (-5, -2.5, 0, 2.5, 5):
        bx(p, (5.2, 5.4), (20.2, 22.8), (z - 0.2, z + 0.2), DARK, 0.03)
        bx(p, (-5.4, -5.2), (20.2, 22.8), (z - 0.2, z + 0.2), DARK, 0.03)
    bx(p, (-6, 6), (24.2, 25.4), (-6, 6), HAZ, 0.03)
    for x in (-5, -2.5, 0, 2.5, 5):
        bx(p, (x - 0.5, x + 0.5), (24.2, 25.45), (5.9, 6.0), BLK, 0.02)
    # roof gear: small radar, mast, beacon
    zcyl(p, -3, 26.4, -1.0, -0.6, 1.2, WHITE, 10)
    bx(p, (-3.2, -2.8), (25.4, 26.0), (-0.9, -0.7), STEEL, 0.03)
    vcyl(p, 0, 25.4, 32.1, 0, 0.25, STEEL, 6)
    bx(p, (-2.2, 2.2), (28.6, 28.9), (-0.15, 0.15), STEEL, 0.03)
    bx(p, (-1.4, 1.4), (30.4, 30.7), (-0.15, 0.15), STEEL, 0.03)
    bx(p, (-0.7, 0.7), (32.1, 33.5), (-0.7, 0.7), RED, 0.03)


# ---- 23. Dropship -----------------------------------------------------------------------------------------------------------
def build_Dropship(p):
    bx(p, (-11, 11), (0, 0.55), (-9, 9), DARK, 0.03)                               # pad
    bx(p, (-10.4, 10.4), (0.55, 0.62), (-8.4, -7.9), HAZ, 0.03)
    bx(p, (-10.4, 10.4), (0.55, 0.62), (7.9, 8.4), HAZ, 0.03)
    bx(p, (-10.4, -9.9), (0.55, 0.62), (-7.9, 7.9), HAZ, 0.03)
    bx(p, (9.9, 10.4), (0.55, 0.62), (-7.9, 7.9), HAZ, 0.03)
    bx(p, (-1, 0.2), (0.55, 0.62), (-3, 3), HAZ, 0.03)                             # H marking
    # landing gear
    for (x, z) in ((5, 1.6), (5, -1.6), (-5, 0)):
        vcyl(p, x, 0.55, 2.7, z, 0.4, STEEL, 6)
        bx(p, (x - 0.9, x + 0.9), (0.55, 0.9), (z - 0.9, z + 0.9), DARK, 0.03)
    # fuselage: body, tapering nose, cockpit glass
    bx(p, (-8, 4), (2.5, 5.9), (-2.2, 2.2), PANEL, 0.03)
    hexa(p, [(4, 2.5, -2.2), (8, 2.9, -1.2), (8, 2.9, 1.2), (4, 2.5, 2.2), (4, 5.9, -2.2), (8, 4.6, -1.0), (8, 4.6, 1.0), (4, 5.9, 2.2)], PANEL, 0.03)
    hexa(p, [(4.6, 5.0, -1.7), (7.6, 4.4, -0.9), (7.6, 4.4, 0.9), (4.6, 5.0, 1.7), (4.6, 5.9, -1.7), (7.4, 4.9, -0.9), (7.4, 4.9, 0.9), (4.6, 5.9, 1.7)], HOLO, 0.03)
    bx(p, (-8, 4), (2.5, 3.0), (-2.3, 2.3), DARK, 0.03)
    bx(p, (-2, 1), (3.4, 5.0), (2.2, 2.35), DARK, 0.03)                            # side hatch
    bx(p, (-1.7, 0.7), (3.6, 4.9), (2.35, 2.45), HAZ, 0.03)
    bx(p, (-8, -6), (3.4, 5.4), (-2.1, 2.1), STEEL, 0.03)                          # rear ramp block
    # wings and engine pods
    for sz in (-1, 1):
        # swept wing: wide at the root, narrow at the tip, hazard wing tip
        hexa(p, [(-4.2, 3.4, 0), (2.2, 3.4, 0), (0.6, 3.4, sz * 8.5), (-2.4, 3.4, sz * 8.5),
                 (-4.2, 4.2, 0), (2.2, 4.2, 0), (0.6, 4.2, sz * 8.5), (-2.4, 4.2, sz * 8.5)], STEEL, 0.03)
        hexa(p, [(-2.4, 3.4, sz * 7.7), (0.6, 3.4, sz * 7.7), (0.6, 3.4, sz * 8.5), (-2.4, 3.4, sz * 8.5),
                 (-2.4, 4.25, sz * 7.7), (0.6, 4.25, sz * 7.7), (0.6, 4.25, sz * 8.5), (-2.4, 4.25, sz * 8.5)], HAZ, 0.03)
        # engine pod: nacelle, hazard ring, intake with fan, exhaust skirt
        z = sz * 7.0
        vcyl(p, -1, 3.6, 7.2, z, 1.6, STEEL, 10)
        vcyl(p, -1, 5.0, 5.5, z, 1.7, HAZ, 10)
        vcyl(p, -1, 7.0, 7.25, z, 1.2, BLK, 10)
        bx(p, (-2.0, 0.0), (7.2, 7.4), (z - 0.18, z + 0.18), LSTEEL, 0.03)
        bx(p, (-1.18, -0.82), (7.2, 7.4), (z - 1.0, z + 1.0), LSTEEL, 0.03)
        vcyl(p, -1, 3.2, 3.6, z, 1.1, DARK, 8)
    # tail: swept vertical fin, hazard stripes, small tailplanes
    hexa(p, [(-9, 4.6, -0.4), (-5.8, 4.6, -0.4), (-5.8, 4.6, 0.4), (-9, 4.6, 0.4),
             (-9, 9.5, -0.4), (-7.4, 9.5, -0.4), (-7.4, 9.5, 0.4), (-9, 9.5, 0.4)], PANEL, 0.03)
    hexa(p, [(-9, 7.4, -0.5), (-6.9, 7.4, -0.5), (-6.9, 7.4, 0.5), (-9, 7.4, 0.5),
             (-9, 8.4, -0.5), (-7.6, 8.4, -0.5), (-7.6, 8.4, 0.5), (-9, 8.4, 0.5)], HAZ, 0.03)
    for sz in (-1, 1):
        bx(p, (-9, -6.6), (5.6, 6.0), (min(sz * 0.4, sz * 3.2), max(sz * 0.4, sz * 3.2)), STEEL, 0.03)
    for x in (-3.5, 0.5):                                                         # cabin windows
        bx(p, (x - 0.6, x + 0.6), (4.4, 5.2), (2.2, 2.36), HOLO, 0.03)
        bx(p, (x - 0.6, x + 0.6), (4.4, 5.2), (-2.36, -2.2), HOLO, 0.03)


# ---- 24. Scrap --------------------------------------------------------------------------------------------------------------
def plate(p, c, size, col, yaw, tilt=0.0, tilt2=0.0):
    """Armour plate / block, optionally tipped over: tilt about the plate's z axis, tilt2 about its x axis (degrees)."""
    g = Grp(p, c, yaw)
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    a, b = math.radians(tilt), math.radians(tilt2)
    pts = []
    for (x, y, z) in ((-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz),
                      (-sx, sy, -sz), (sx, sy, -sz), (sx, sy, sz), (-sx, sy, sz)):
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
        pts.append(g.pos((x, y, z)))
    hexa(p, pts, col, 0.06)
    return g


def build_Scrap(p):
    # the heap: tipped armour plates piled up
    plate(p, (0, 1, 0), (8, 2, 6), DARK, 12)
    plate(p, (-1, 2.8, 0.5), (6, 1.6, 4.4), STEEL, -28, tilt=8)
    plate(p, (1.4, 4.4, -0.4), (4, 1.6, 3), ORANGE, 40, tilt=-16, tilt2=9)
    plate(p, (-4.4, 1.2, 3.4), (3.4, 2.4, 3.4), STEEL, 20, tilt2=-12)
    plate(p, (4.6, 1.6, 3), (3, 3.2, 2.4), ORANGE, -50, tilt=14, tilt2=-10)
    plate(p, (-3, 5.0, 0), (2.4, 1.2, 2.4), PANEL, 30, tilt=-18)
    plate(p, (1.5, 2.2, 6), (3.6, 0.5, 2.4), STEEL, -15, tilt=-25)
    # a bent mecha leg sticking out of the back: thigh, knee joint, shin, orange foot
    bar(p, (-4.6, 1.6, -3.6), (-2.4, 4.6, -3.4), 1.5, PANEL, 0.03)
    ball(p, (-2.4, 4.6, -3.4), 1.05, DARK, subdiv=1)
    bar(p, (-2.4, 4.6, -3.4), (0.6, 2.0, -5.0), 1.2, STEEL, 0.03)
    plate(p, (1.4, 0.7, -5.5), (3.0, 1.0, 2.4), ORANGE, 20, tilt=-8)
    # a big gear leaning on the heap, with teeth
    zcyl(p, 5, 3.0, -3.5, -2.5, 2.0, STEEL, 12)
    zcyl(p, 5, 3.0, -3.6, -2.4, 0.7, DARK, 8)
    for k in range(10):
        a = math.radians(k * 36)
        bx(p, (5 + 2.25 * math.cos(a) - 0.4, 5 + 2.25 * math.cos(a) + 0.4), (3.0 + 2.25 * math.sin(a) - 0.4, 3.0 + 2.25 * math.sin(a) + 0.4),
           (-3.5, -2.5), STEEL, 0.03)
    # a cracked white helmet with a broken visor, half buried
    ball(p, (-3.6, 3.6, 3.4), 1.5, WHITE, scale=(1, 0.9, 1), subdiv=2, jit=0.03)
    bx(p, (-4.6, -2.4), (3.4, 4.2), (4.4, 4.9), HOLO, 0.03)
    bx(p, (-3.8, -3.5), (3.3, 5.0), (3.4, 5.0), DARK, 0.03)
    # a torn-off robot arm reaching out of the pile, with a claw hand
    bar(p, (4.4, 1.6, 4.4), (6.2, 2.6, 5.2), 1.0, PANEL, 0.03)
    bx(p, (5.6, 7.0), (2.0, 3.4), (4.8, 6.0), DARK, 0.03)
    for dz in (-0.35, 0.35):
        bx(p, (6.9, 7.2), (1.8, 3.6), (5.4 + dz - 0.15, 5.4 + dz + 0.15), STEEL, 0.03)
    # bent yellow rod, flattened red drum, loose bolts
    g = Grp(p, (-5, 3.8, -1), 15)
    g.box((0, 0, 0), (0.8, 5.0, 0.8), HAZ, 0.04)
    g.box((0.3, 2.6, 0), (1.4, 0.5, 0.8), HAZ, 0.04)
    g = Grp(p, (3, 0.9, 5), -20)
    g.xcyl((0, 0, 0), 3.4, 0.9, RED, 10)
    g.xcyl((-1.4, 0, 0), 0.3, 0.98, DARK, 8)
    g.xcyl((1.4, 0, 0), 0.3, 0.98, DARK, 8)
    for (x, z, c) in ((-0.5, 3.2, HAZ), (2.4, -1.5, LSTEEL), (-6.0, 1.0, STEEL)):
        bx(p, (x - 0.5, x + 0.5), (0.0, 0.5), (z - 0.5, z + 0.5), c, 0.04)


# ---- 25. StrategyTable ------------------------------------------------------------------------------------------------------
def build_StrategyTable(p):
    vcyl(p, 0, 0, 0.25, 0, 2.2, DARK, 12)
    vcyl(p, 0, 0.25, 1.8, 0, 1.2, STEEL, 10)
    vcyl(p, 0, 1.8, 3.0, 0, 3.5, PANEL, 16)
    vcyl(p, 0, 2.5, 2.9, 0, 3.6, HAZ, 16, jit=0.02)
    for k in range(8):                                                           # dark blocks on the hazard rim
        a = math.radians(k * 45 + 22.5)
        bc(p, (3.62 * math.cos(a), 2.7, 3.62 * math.sin(a)), (1.0, 0.3, 0.7), BLK, yaw=-(k * 45 + 22.5) - 90, jit=0.02)
    vcyl(p, 0, 3.0, 3.5, 0, 2.7, DARK, 16)
    vcyl(p, 0, 3.5, 3.8, 0, 2.5, HOLO, 16, jit=0.03)                               # the holo map plate
    # terrain on the map: little blocks, hills and a flag
    for (x, z, h, w, c) in ((-1.2, -0.8, 0.6, 0.9, WHITE), (0.9, -1.1, 0.9, 0.8, STEEL), (1.2, 0.9, 0.5, 1.0, WHITE), (-0.9, 1.1, 0.7, 0.7, LSTEEL)):
        bx(p, (x - w / 2, x + w / 2), (3.8, 3.8 + h), (z - w / 2, z + w / 2), c, 0.03)
    vcyl(p, 0, 3.8, 4.3, 0, 1.0, HOLO, 8, top_r=0.5, jit=0.03)
    vcyl(p, 0, 4.3, 5.2, 0, 0.12, WHITE, 5)
    ball(p, (-1.6, 4.5, 0.5), 0.55, HOLO, subdiv=1, jit=0.03)
    ball(p, (1.7, 4.3, -0.3), 0.45, WHITE, subdiv=1, jit=0.03)
    bx(p, (0.1, 1.1), (4.7, 5.2), (-0.1, 0.1), RED, 0.03)
    for (x, z) in ((-5, 0), (5, 0.8), (0.6, 5), (-0.4, -5)):                         # stools
        vcyl(p, x, 0, 1.0, z, 0.35, STEEL, 6)
        vcyl(p, x, 1.0, 1.4, z, 0.9, HAZ, 8)
        vcyl(p, x, 0, 0.12, z, 0.8, DARK, 8)


# ---- 26. Generator ----------------------------------------------------------------------------------------------------------
def build_Generator(p):
    bx(p, (-6, 6), (0, 0.8), (-4.5, 4.5), DARK, 0.03)
    stripes(p, (-6, 6), (0.7, 1.1), (4.1, 4.5), 6)
    bx(p, (-4.5, 4.5), (0.8, 6), (-3.2, 3.2), STEEL, 0.03)                          # casing
    bx(p, (-4.7, 4.7), (5.6, 6.0), (-3.4, 3.4), DARK, 0.03)
    for x in (-3.4, -1.7, 0, 1.7, 3.4):                                              # louvres
        bx(p, (x - 0.5, x + 0.5), (3.4, 5.0), (3.2, 3.35), DARK, 0.03)
        bx(p, (x - 0.4, x + 0.4), (3.8, 4.0), (3.35, 3.4), LSTEEL, 0.03)
        bx(p, (x - 0.4, x + 0.4), (4.4, 4.6), (3.35, 3.4), LSTEEL, 0.03)
    bx(p, (-4.5, -1.3), (1.2, 3.0), (3.2, 3.4), HAZ, 0.03)                           # service hatch
    for x in (-3.3, -2.0, -0.7):
        bx(p, (x - 0.15, x + 0.15), (1.4, 2.8), (3.4, 3.45), BLK, 0.02)
    bx(p, (1.0, 4.0), (1.2, 3.0), (3.2, 3.45), DARK, 0.03)                           # panel with gauges
    for i, c in enumerate((RED, HAZ, HOLO)):
        bx(p, (1.3 + i * 0.9, 1.9 + i * 0.9), (2.2, 2.8), (3.45, 3.55), c, 0.03)
    # coil towers with fins, glass cores
    for sx in (-1, 1):
        x = sx * 2.6
        vcyl(p, x, 6.0, 11.6, -1, 1.3, PANEL, 10)
        for y in (6.6, 8.0, 9.4, 10.8):
            vcyl(p, x, y, y + 0.4, -1, 1.7, STEEL, 10)
        vcyl(p, x, 8.4, 9.2, -1, 1.75, HAZ, 10)
        bx(p, (x - 1.5, x + 1.5), (10.7, 13.5), (-2.5, 0.5), HOLO, 0.03)
        bx(p, (x - 1.3, x + 1.3), (13.5, 13.7), (-2.3, 0.3), WHITE, 0.02)
        for dx in (-1.5, 1.5):
            bx(p, (x + dx - 0.12, x + dx + 0.12), (10.7, 13.7), (-2.5, -2.3), DARK, 0.03)
            bx(p, (x + dx - 0.12, x + dx + 0.12), (10.7, 13.7), (0.3, 0.5), DARK, 0.03)
    # exhaust stack + pipe
    vcyl(p, 5.2, 0.8, 12.0, -2.4, 0.6, DARK, 8)
    vcyl(p, 5.2, 11.4, 12.0, -2.4, 0.8, STEEL, 8)
    vcyl(p, 5.2, 0.8, 1.4, -2.4, 0.9, HAZ, 8)
    xcyl(p, -3.8, 3.8, 6.4, 2.2, 0.35, DARK, 8)
    bx(p, (-0.5, 0.5), (6.0, 6.8), (2.0, 2.4), DARK, 0.03)


# ---- 27. ChargeDock ---------------------------------------------------------------------------------------------------------
def build_ChargeDock(p):
    bx(p, (-4.5, 4.5), (0, 0.8), (-3.5, 3.5), DARK, 0.03)
    for sx in (-1, 1):
        x = sx * 3.6
        vcyl(p, x, 0.8, 11.2, 0, 0.8, HAZ, 8)
        for y in (2.0, 5.0, 8.0):
            vcyl(p, x, y, y + 0.6, 0, 0.9, BLK, 8)
        bx(p, (x - 0.9, x + 0.9), (0.8, 1.4), (-0.9, 0.9), DARK, 0.03)
        # battery level bars on the pylon front
        bx(p, (x - 0.9, x + 0.9), (6.2, 9.8), (0.8, 1.2), DARK, 0.03)
        for i, c in enumerate((HOLO, HOLO, HOLO, STEEL)):
            bx(p, (x - 0.7, x + 0.7), (6.4 + i * 0.85, 7.1 + i * 0.85), (1.2, 1.3), c, 0.03)
    bx(p, (-4.5, 4.5), (11.2, 12.4), (-0.7, 0.7), DARK, 0.03)
    for x in (-2.6, 0, 2.6):
        bx(p, (x - 0.6, x + 0.6), (11.4, 12.2), (0.7, 0.8), HAZ, 0.03)
    # central charger with screen and button
    bx(p, (-1.6, 1.6), (0.8, 6.0), (-1.2, 1.2), STEEL, 0.03)
    bx(p, (-1.8, 1.8), (5.6, 6.0), (-1.4, 1.4), DARK, 0.03)
    bx(p, (-1.1, 1.1), (3.2, 4.4), (1.2, 1.3), HOLO, 0.03)
    bx(p, (-0.8, 0.8), (4.4, 5.6), (1.2, 1.6), RED, 0.03)
    bx(p, (-1.3, 1.3), (1.2, 2.8), (1.2, 1.3), HAZ, 0.03)
    # heavy cable down to the plug
    zcyl(p, 0, 2.0, 1.2, 3.0, 0.4, BLK, 8)
    xcyl(p, -3.0, 2.0, 2.0, 3.0, 0.4, BLK, 8)
    ball(p, (-3.0, 2.0, 3.0), 0.5, BLK, subdiv=1)
    bx(p, (1.8, 3.4), (0.8, 2.4), (2.4, 4.0), STEEL, 0.03)                           # plug body
    for dx in (2.3, 2.9):
        bx(p, (dx - 0.1, dx + 0.1), (1.4, 1.8), (3.9, 4.0), LSTEEL, 0.03)
    bx(p, (1.8, 3.4), (2.4, 2.6), (2.4, 4.0), HAZ, 0.03)


# ---- 28. MechaHead ----------------------------------------------------------------------------------------------------------
def build_MechaHead(p):
    bx(p, (-5, 5), (0, 3), (-5, 5), CONC, 0.04)
    bx(p, (-4.2, 4.2), (3, 3.6), (-4.2, 4.2), HAZ, 0.03)
    bx(p, (-5.1, 5.1), (0.6, 2.6), (4.9, 5.0), DARK, 0.03)
    text(p, "SHIBA", 0, 0.9, 5.0, 5.2, 1.6, 1.3, 0.35, 0.35, HAZ)
    vcyl(p, 0, 3.6, 5.8, 0, 1.7, DARK, 10)
    for y in (4.1, 4.9):
        vcyl(p, 0, y, y + 0.35, 0, 1.9, STEEL, 10)
    # head: wide cheeks, narrower brow
    hexa(p, [(-4, 5.8, -3.5), (4, 5.8, -3.5), (4, 5.8, 3.5), (-4, 5.8, 3.5),
             (-3.2, 12.2, -3.2), (3.2, 12.2, -3.2), (3.2, 12.2, 3.2), (-3.2, 12.2, 3.2)], PANEL, 0.03)
    bx(p, (-4.1, 4.1), (6.6, 7.2), (-3.0, 3.0), STEEL, 0.03)                           # jaw line plate
    for sx in (-1, 1):
        # ears: triangular prisms with an orange inner
        prism_z(p, [(sx * 1.7 - 1.1, 11.8), (sx * 1.7 + 1.1, 11.8), (sx * 1.9 + (0.3 if sx > 0 else -0.3), 15.2)], -0.8, 0.8, STEEL, 0.03)
        prism_z(p, [(sx * 1.7 - 0.6, 11.9), (sx * 1.7 + 0.6, 11.9), (sx * 1.9 + (0.2 if sx > 0 else -0.2), 14.2)], 0.8, 0.95, ORANGE, 0.03)
        # white cheek plates
        hexa(p, [(sx * 4.0, 6.0, 0.6), (sx * 4.0, 6.0, 3.4), (sx * 1.6, 6.0, 3.4), (sx * 1.6, 6.0, 0.6),
                 (sx * 3.6, 9.0, 1.0), (sx * 3.6, 9.0, 3.2), (sx * 1.6, 8.0, 3.2), (sx * 1.6, 8.0, 1.0)], WHITE, 0.03)
    bx(p, (-3.2, 3.2), (9.2, 10.6), (3.4, 3.8), HOLO, 0.03)                           # visor
    bx(p, (-3.4, 3.4), (10.6, 10.9), (3.3, 3.9), DARK, 0.03)
    bx(p, (-3.4, 3.4), (8.9, 9.2), (3.3, 3.9), DARK, 0.03)
    bx(p, (-1.9, 1.9), (5.9, 8.9), (3.0, 5.4), WHITE, 0.03)                           # muzzle
    bx(p, (-0.7, 0.7), (7.7, 8.9), (5.0, 6.2), BLK, 0.03)                             # nose
    bx(p, (-1.5, 1.5), (6.3, 6.5), (5.4, 5.45), DARK, 0.02)                           # mouth line
    vcyl(p, 0, 12.2, 13.6, -1.8, 0.15, STEEL, 5)
    bx(p, (-0.4, 0.4), (13.4, 13.9), (-2.2, -1.4), RED, 0.03)


# ---- 29. Colossus -----------------------------------------------------------------------------------------------------------
def build_Colossus(p):
    bx(p, (-11, 11), (0, 1), (-8, 8), DARK, 0.03)
    stripes(p, (-11, 11), (0.6, 1.1), (7.6, 8.0), 11)
    for sx in (-1, 1):
        x = sx * 4.4
        # foot with three toes, ankle, shin with knee armour, thigh
        bx(p, (x - 2.5, x + 2.5), (1, 3.0), (-3.2, 4.4), STEEL, 0.03)
        bx(p, (x - 2.5, x + 2.5), (3.0, 3.8), (-3.2, 4.4), DARK, 0.03)
        bx(p, (x - 1.7, x + 1.7), (3.8, 8.4), (-1.7, 1.7), PANEL, 0.03)
        bx(p, (x - 1.9, x + 1.9), (6.6, 7.4), (-1.9, 1.9), HAZ, 0.03)
        bx(p, (x - 1.4, x + 1.4), (8.2, 9.0), (1.7, 2.2), DARK, 0.03)                  # knee cap
        xcyl(p, x - 1.8, x + 1.8, 9.0, 0, 1.2, DARK, 8)
        bx(p, (x - 1.8, x + 1.8), (9.0, 13.2), (-1.8, 1.8), STEEL, 0.03)
        bx(p, (x - 2.0, x + 2.0), (11.0, 11.4), (-2.0, 2.0), DARK, 0.03)
    # hips and skirt
    bx(p, (-6, 6), (13, 16.2), (-3.5, 3.5), DARK, 0.03)
    for i in range(6):
        bx(p, (-6 + i * 2, -5 + i * 2), (13.3, 14.3), (3.5, 3.7), HAZ if i % 2 == 0 else BLK, 0.02)
    # torso, chest vents, cockpit glass
    bx(p, (-6, 6), (16.1, 27.1), (-4, 4), PANEL, 0.03)
    bx(p, (-6.2, 6.2), (16.1, 17.0), (-4.2, 4.2), STEEL, 0.03)
    bx(p, (-6.2, 6.2), (26.4, 27.1), (-4.2, 4.2), STEEL, 0.03)
    for i in range(3):
        bx(p, (-4.4 + i * 1.0, -3.8 + i * 1.0), (18.0, 20.0), (4.0, 4.2), DARK, 0.03)
        bx(p, (3.8 - i * 1.0, 4.4 - i * 1.0), (18.0, 20.0), (4.0, 4.2), DARK, 0.03)
    bx(p, (-3.4, 3.4), (20.6, 25.0), (4.0, 4.5), DARK, 0.03)                           # cockpit frame
    bx(p, (-3.0, 3.0), (20.8, 24.4), (4.5, 4.8), HOLO, 0.03)
    bx(p, (-0.15, 0.15), (20.8, 24.4), (4.8, 4.85), DARK, 0.02)
    bx(p, (-3.0, 3.0), (22.5, 22.65), (4.8, 4.85), DARK, 0.02)
    bx(p, (-2.2, 2.2), (17.4, 17.8), (4.0, 4.3), ORANGE, 0.03)
    # shoulders with cannons, arms, fists
    for sx in (-1, 1):
        x = sx * 7.6
        bx(p, (x - 2.5, x + 2.5), (22.9, 27.9), (-2.5, 2.5), STEEL, 0.03)
        bx(p, (x - 2.7, x + 2.7), (26.8, 27.4), (-2.7, 2.7), DARK, 0.03)
        bx(p, (x - 2.6, x + 2.6), (23.8, 24.6), (-2.6, 2.6), ORANGE, 0.03)
        zcyl(p, x, 25.6, 2.5, 6.6, 0.85, DARK, 8)
        zcyl(p, x, 25.6, 6.0, 6.8, 1.1, HAZ, 8)
        zcyl(p, x, 25.6, 2.4, 3.0, 1.2, STEEL, 8)
        ax = sx * 8.8
        bx(p, (ax - 1.3, ax + 1.3), (14.0, 22.9), (-1.3, 1.3), PANEL, 0.03)
        bx(p, (ax - 1.5, ax + 1.5), (17.4, 18.2), (-1.5, 1.5), DARK, 0.03)
        ball(p, (ax, 18.8, 0), 1.45, DARK, subdiv=1)
        bx(p, (ax - 1.7, ax + 1.7), (13.9, 16.3), (-1.7, 1.7), STEEL, 0.03)            # fist
        bx(p, (ax - 1.5, ax + 1.5), (13.9, 14.6), (1.7, 2.1), DARK, 0.03)
    # head: Shiba face with ears, cheeks, visor eyes
    hexa(p, [(-4, 27.6, -3.3), (4, 27.6, -3.3), (4, 27.6, 3.7), (-4, 27.6, 3.7),
             (-3.2, 34, -3.0), (3.2, 34, -3.0), (3.2, 34, 3.5), (-3.2, 34, 3.5)], WHITE, 0.03)
    for sx in (-1, 1):
        prism_z(p, [(sx * 1.8 - 1.2, 33.6), (sx * 1.8 + 1.2, 33.6), (sx * 2.0 + (0.3 if sx > 0 else -0.3), 37.1)], -0.4, 1.2, ORANGE, 0.03)
        bx(p, (min(sx * 3.2, sx * 4.2), max(sx * 3.2, sx * 4.2)), (28.2, 31.6), (1.2, 3.8), STEEL, 0.03)
    bx(p, (-3.0, 3.0), (30.4, 32.0), (3.5, 4.1), HOLO, 0.03)                           # eye visor
    bx(p, (-3.2, 3.2), (32.0, 32.3), (3.4, 4.2), DARK, 0.03)
    bx(p, (-1.8, 1.8), (28.0, 30.2), (3.7, 5.2), PANEL, 0.03)                          # muzzle
    bx(p, (-0.7, 0.7), (29.2, 30.2), (5.0, 5.8), BLK, 0.03)
    bx(p, (-1.0, 1.0), (27.6, 28.2), (3.7, 4.4), DARK, 0.03)


# ---- 30. Reactor ------------------------------------------------------------------------------------------------------------
def build_Reactor(p):
    vcyl(p, 0, 0, 2, 0, 8.5, DARK, 20)
    vcyl(p, 0, 2, 12, 0, 4.5, STEEL, 16)
    vcyl(p, 0, 3.9, 4.9, 0, 5.2, HAZ, 16)
    vcyl(p, 0, 8.9, 9.9, 0, 5.2, HAZ, 16)
    for k in range(8):                                                           # black blocks on the rings
        a = math.radians(k * 45 + 22.5)
        for y in (4.4, 9.4):
            bc(p, (5.2 * math.cos(a), y, 5.2 * math.sin(a)), (1.4, 1.02, 1.0), BLK, yaw=-(k * 45 + 22.5) - 90, jit=0.02)
    vcyl(p, 0, 6.2, 7.4, 0, 4.6, DARK, 16)
    # glass dome with a bright core and ribs
    vcyl(p, 0, 12, 12.6, 0, 4.7, DARK, 16)
    vcyl(p, 0, 12.6, 15.5, 0, 4.4, HOLO, 16, top_r=2.3)
    vcyl(p, 0, 15.5, 15.9, 0, 2.5, WHITE, 16, top_r=1.9)
    for k in range(4):
        a = math.radians(k * 90 + 45)
        bar(p, (4.5 * math.cos(a), 12.6, 4.5 * math.sin(a)), (2.4 * math.cos(a), 15.6, 2.4 * math.sin(a)), 0.4, DARK, 0.03)
    # coil pylons with fins and red caps, linked to the body
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 6.4, sz * 6.4
            bx(p, (x - 0.8, x + 0.8), (2, 8), (z - 0.8, z + 0.8), PANEL, 0.03)
            for y in (3.0, 4.6, 6.2):
                bx(p, (x - 1.1, x + 1.1), (y, y + 0.4), (z - 1.1, z + 1.1), STEEL, 0.03)
            bx(p, (x - 1.1, x + 1.1), (7.5, 9.7), (z - 1.1, z + 1.1), RED, 0.03)
            bar(p, (x, 6.8, z), (x * 0.5, 6.8, z * 0.5), 0.4, DARK, 0.03)


# ---- previews ----------------------------------------------------------------------------------------------------------
ORDER = ["Floor", "Turntable", "Hangar", "BonkSign", "Crates", "Drums", "Floodlights", "Console", "Workshop", "FuelTanks", "Radar",
         "Barracks", "MissileRack", "DronePad", "RepairArm", "Transport", "PartsRack", "Walkers", "Range", "Barriers", "Silos",
         "Tower", "Dropship", "Scrap", "StrategyTable", "Generator", "ChargeDock", "MechaHead", "Colossus", "Reactor"]
AZ = {"Hangar": 165, "Silos": 160, "Reactor": 160}
ELEV = {"Hangar": 14}
MULT = {"Floor": 1.5, "Hangar": 2.2, "Colossus": 2.9, "Tower": 2.9, "Reactor": 2.5, "Silos": 2.5, "Radar": 2.6, "MechaHead": 2.5}
SHIBA_AT = {"Floor": (22, 4, 180, 0)}


def shiba_for(x, z, facing, lift):
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
    parts = [(pid, globals()["build_" + pid]) for pid in ORDER if "build_" + pid in globals()]
    print("MISSING:", [pid for pid in ORDER if "build_" + pid not in globals()])
    built = {}
    for pid, fn in parts:
        if ONLY and pid not in ONLY:
            continue
        org(pid)
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
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 150), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1000, 720))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 160, 40, 2.7, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.3, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_MechaHangar.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
