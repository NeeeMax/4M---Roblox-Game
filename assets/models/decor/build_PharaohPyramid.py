"""Final low-poly decor models for the theme PharaohPyramid (25 parts around the Pharaoh Shiba, bay 19).

Usage: blender --background --factory-startup --python build_PharaohPyramid.py -- <outdir> [PartId ...]
Writes Decor_PharaohPyramid_<PartId>.fbx, preview_<PartId>.png and stage_PharaohPyramid.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Give part ids after the out
folder to rebuild only those parts (no stage render then). Parts are written in local coordinates around the same origin as
the theme's P(cx, cz) block; the global OX/OZ below moves them to the world spot.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "PharaohPyramid"))
ONLY = ARGS[1:]
KEY = "PharaohPyramid"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_PharaohPyramid.json"))

# ---- palette (one for all 25 parts) ----------------------------------------------------------------------------------------
SAND = (224, 196, 138)
SAND_D = (200, 166, 108)
STONE = (226, 202, 152)
STONE_L = (240, 226, 190)
STONE_D = (176, 148, 104)
GOLD = (240, 190, 56)
GOLD_D = (205, 148, 38)
LAPIS = (38, 74, 156)
TURQ = (50, 160, 160)
RED = (190, 58, 48)
BLACK = (38, 36, 42)
WATER = (60, 152, 192)
WATER_L = (120, 196, 224)
PALM = (70, 140, 60)
PALM_D = (50, 112, 48)
TRUNK = (130, 96, 62)
TRUNK_D = (104, 74, 48)
MUD = (184, 138, 96)
MUD_D = (160, 116, 78)
LINEN = (238, 230, 210)
WOOD = (118, 80, 50)
GRASS = (104, 156, 74)
GRASS_D = (80, 132, 60)
GRANITE = (214, 120, 96)
GRANITE_D = (176, 90, 72)
CLAY = (196, 110, 76)
SKIN = (176, 104, 70)
FALCON = (86, 60, 44)
FALCON_L = (150, 112, 78)

OX = OZ = 0   # world origin of the part being built (set in main)


# ---- helpers ---------------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in local stage axes."""
    c = ((x[0] + x[1]) / 2 + OX, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2 + OZ)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=8, top_r=None, jit=0.04):
    return dk.cyl(p, (cx + OX, (y0 + y1) / 2, cz + OZ), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def tcyl(p, cx, y0, y1, cz, r, col, tilt, verts=8, top_r=None, jit=0.04):
    """Standing cylinder tilted about z (positive leans toward -x), centred between y0 and y1."""
    return dk.cyl(p, (cx + OX, (y0 + y1) / 2, cz + OZ), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r,
                  rot=(0, 0, tilt), jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=8, jit=0.04):
    return dk.cyl(p, ((x0 + x1) / 2 + OX, cy, cz + OZ), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, top_r=None):
    return dk.cyl(p, (cx + OX, cy, (z0 + z1) / 2 + OZ), r, z1 - z0, col, axis='z', verts=verts, top_radius=top_r, jitter=jit)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04, rot=(0, 0, 0)):
    return dk.ball(p, (c[0] + OX, c[1], c[2] + OZ), r, col, scale=scale, subdiv=subdiv, jitter=jit, rot=rot)


def poly(p, pts, faces, col, jit=0.04):
    pp = [(a + OX, b, c + OZ) for a, b, c in pts]
    return dk.poly(p, (0, 0, 0), pp, faces, col, jit)


BOXF = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def tbox(p, cx, cz, y0, y1, w0, d0, w1, d1, col, jit=0.04, cx1=None, cz1=None):
    """Frustum with a rectangular footprint: w0 x d0 at y0, w1 x d1 at y1 (top centre may be shifted)."""
    cx1 = cx if cx1 is None else cx1
    cz1 = cz if cz1 is None else cz1
    pts = [(cx - w0 / 2, y0, cz - d0 / 2), (cx + w0 / 2, y0, cz - d0 / 2), (cx + w0 / 2, y0, cz + d0 / 2), (cx - w0 / 2, y0, cz + d0 / 2),
           (cx1 - w1 / 2, y1, cz1 - d1 / 2), (cx1 + w1 / 2, y1, cz1 - d1 / 2), (cx1 + w1 / 2, y1, cz1 + d1 / 2), (cx1 - w1 / 2, y1, cz1 + d1 / 2)]
    return poly(p, pts, BOXF, col, jit)


def pyr(p, cx, cz, y0, y1, w, d, col, jit=0.04):
    pts = [(cx - w / 2, y0, cz - d / 2), (cx + w / 2, y0, cz - d / 2), (cx + w / 2, y0, cz + d / 2), (cx - w / 2, y0, cz + d / 2), (cx, y1, cz)]
    faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return poly(p, pts, faces, col, jit)


def wedge_x(p, x0, x1, y0, y1, z0, z1, col, jit=0.04, high_at='x1'):
    """Ramp along x: full height y1 at one end sloping to y0 at the other (triangular prism extruded along z)."""
    if high_at == 'x1':
        tri = [(x0, y0), (x1, y0), (x1, y1)]
    else:
        tri = [(x0, y0), (x1, y0), (x0, y1)]
    pts = [(a, b, z0) for a, b in tri] + [(a, b, z1) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return poly(p, pts, faces, col, jit)


def wedge_z(p, x0, x1, y0, y1, z0, z1, col, jit=0.04, high_at='z0'):
    """Ramp along z (e.g. steps / slopes): full height at z0 (or z1), sloping down to the other end."""
    if high_at == 'z0':
        tri = [(z0, y0), (z1, y0), (z0, y1)]
    else:
        tri = [(z0, y0), (z1, y0), (z1, y1)]
    pts = [(x0, b, a) for a, b in tri] + [(x1, b, a) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return poly(p, pts, faces, col, jit)


def bar(p, a, b, t, col, jit=0.04):
    """Square bar of thickness t between two local 3D points."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized() * (t / 2)
    v = d.cross(u).normalized() * (t / 2)
    pts = []
    for q in (a, b):
        for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            pts.append(tuple(q + u * su + v * sv))
    return poly(p, pts, BOXF, col, jit)


def pot(p, x, y0, z, r, h, col, band=None, verts=8):
    """Clay jar: belly, shoulder, neck and rim."""
    vcyl(p, x, y0, y0 + h * 0.5, z, r * 0.62, col, verts, top_r=r)
    vcyl(p, x, y0 + h * 0.5, y0 + h * 0.85, z, r, col, verts, top_r=r * 0.5)
    vcyl(p, x, y0 + h * 0.85, y0 + h, z, r * 0.5, band or col, verts, top_r=r * 0.62)


def lotus_cap(p, x, y0, z, r, h, col=STONE_L, accent=LAPIS):
    """Papyrus bud capital: flared bowl with a lapis band."""
    vcyl(p, x, y0, y0 + h * 0.75, z, r * 0.6, col, 8, top_r=r)
    vcyl(p, x, y0 + h * 0.75, y0 + h, z, r, accent, 8, top_r=r * 0.8)


def frond(p, ox, oy, oz, yaw, L, W, col, droop=0.8):
    t = 0.07
    st = [(0.0, 0.1, 0.16), (0.45 * L, 0.5 * L / 4.4, W), (L, -droop, 0.08)]
    pts = [(x, y + t, -w) if k == 0 else (x, y + t, w) for x, y, w in st for k in (0, 1)]
    pts += [(x, y - t, -w) if k == 0 else (x, y - t, w) for x, y, w in st for k in (0, 1)]
    faces = [(0, 1, 3, 2), (2, 3, 5, 4), (6, 8, 9, 7), (8, 10, 11, 9), (0, 2, 8, 6), (2, 4, 10, 8), (1, 7, 9, 3), (3, 9, 11, 5),
             (4, 5, 11, 10), (0, 6, 7, 1)]
    return dk.poly(p, (ox + OX, oy, oz + OZ), pts, faces, col, 0.05, rot=(0, yaw, 0))


def palm(p, x, z, h, tilt, r=0.6, fr=4.4, dates=False, y0=0.4, yaw0=0, nf=6):
    """Date palm: three-piece bent trunk and a crown of drooping fronds. Positive tilt leans toward -x."""
    px, py = x, y0
    L = h / 3
    for i in range(3):
        t = tilt * (0.3 + 0.45 * i)
        dx, dy = -math.sin(math.radians(t)) * L, math.cos(math.radians(t)) * L
        r0, r1 = r * (1 - 0.2 * i), r * (1 - 0.2 * (i + 1))
        dk.cyl(p, (px + dx / 2 + OX, py + dy / 2, z + OZ), r0, L * 1.05, TRUNK if i % 2 == 0 else TRUNK_D, axis='y', verts=7,
               top_radius=r1, rot=(0, 0, t), jitter=0.05)
        px, py = px + dx, py + dy
    ball(p, (px, py + 0.2, z), 0.9, PALM_D, scale=(1, 0.8, 1))
    for k in range(nf):
        frond(p, px, py + 0.3, z, yaw0 + k * 360 / nf, fr, fr * 0.2, PALM if k % 2 == 0 else PALM_D)
    if dates:
        for dx_, dz_ in ((0.9, 0.2), (-0.8, 0.5), (0.1, -0.9)):
            ball(p, (px + dx_, py - 0.7, z + dz_), 0.5, GOLD_D, scale=(1, 1.3, 1))
    return px, py


def glyph(p, kind, x, y, z, s, col, t=0.2):
    """Tiny relief glyph on a +z facing wall (x, y = centre, z = wall surface, s = height)."""
    z0, z1 = z, z + t
    if kind == 'ankh':
        bx(p, (x - 0.09 * s, x + 0.09 * s), (y - 0.5 * s, y + 0.08 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.3 * s, x + 0.3 * s), (y - 0.1 * s, y + 0.06 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.2 * s, x - 0.1 * s), (y + 0.08 * s, y + 0.5 * s), (z0, z1), col, 0.02)
        bx(p, (x + 0.1 * s, x + 0.2 * s), (y + 0.08 * s, y + 0.5 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.2 * s, x + 0.2 * s), (y + 0.4 * s, y + 0.5 * s), (z0, z1), col, 0.02)
    elif kind == 'eye':
        bx(p, (x - 0.4 * s, x + 0.4 * s), (y - 0.06 * s, y + 0.1 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.08 * s, x + 0.08 * s), (y - 0.04 * s, y + 0.18 * s), (z0, z1 + 0.05), BLACK, 0.02)
        bx(p, (x - 0.3 * s, x + 0.1 * s), (y + 0.18 * s, y + 0.26 * s), (z0, z1), col, 0.02)
        bx(p, (x + 0.05 * s, x + 0.15 * s), (y - 0.4 * s, y - 0.06 * s), (z0, z1), col, 0.02)
    elif kind == 'wave':
        for k in range(3):
            bx(p, (x - 0.4 * s, x + 0.4 * s), (y - 0.3 * s + k * 0.3 * s, y - 0.2 * s + k * 0.3 * s), (z0, z1), col, 0.02)
    elif kind == 'bird':
        bx(p, (x - 0.3 * s, x + 0.2 * s), (y - 0.15 * s, y + 0.1 * s), (z0, z1), col, 0.02)
        bx(p, (x + 0.1 * s, x + 0.25 * s), (y + 0.05 * s, y + 0.35 * s), (z0, z1), col, 0.02)
        bx(p, (x + 0.25 * s, x + 0.4 * s), (y + 0.22 * s, y + 0.3 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.4 * s, x - 0.28 * s), (y - 0.2 * s, y + 0.0 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.1 * s, x - 0.02 * s), (y - 0.5 * s, y - 0.15 * s), (z0, z1), col, 0.02)
    elif kind == 'sun':
        zcyl(p, x, y, z0, z1, 0.3 * s, col, 8)
    elif kind == 'was':
        bx(p, (x - 0.06 * s, x + 0.06 * s), (y - 0.5 * s, y + 0.4 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.2 * s, x + 0.2 * s), (y + 0.3 * s, y + 0.4 * s), (z0, z1), col, 0.02)
    elif kind == 'reed':
        bx(p, (x - 0.06 * s, x + 0.06 * s), (y - 0.5 * s, y + 0.3 * s), (z0, z1), col, 0.02)
        bx(p, (x - 0.2 * s, x + 0.0 * s), (y + 0.1 * s, y + 0.3 * s), (z0, z1), col, 0.02)
        bx(p, (x + 0.0 * s, x + 0.2 * s), (y + 0.1 * s, y + 0.3 * s), (z0, z1), col, 0.02)


def glyph_col(p, kinds, x, y_top, z, s, col, gap=1.25):
    for i, k in enumerate(kinds):
        glyph(p, k, x, y_top - i * gap * s, z, s, col)


# ---- 1. Ground ---------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    bx(p, (-95, 95), (0, 0.3), (-65, 65), SAND, 0.05)
    # dunes: flat ellipsoid humps (stay below the 0.44 top of the plaza)
    for (x, z, sx, sz, c) in ((-62, 40, 19, 8, SAND_D), (-8, -2, 14, 7, SAND_D), (74, 40, 16, 8, SAND_D), (-34, -58, 19, 5, SAND_D),
                              (-70, -8, 14, 6, SAND), (20, 58, 12, 4, SAND_D), (88, -4, 4, 14, SAND_D)):
        ball(p, (x, 0.28, z), 1.0, c, scale=(sx, 0.15, sz), subdiv=2, jit=0.03)
    # pyramid plaza: checker of sandstone tiles
    for i in range(6):
        for j in range(6):
            bx(p, (39 + i * 7 + 0.05, 46 + i * 7 - 0.05 + 0), (0.3, 0.42), (-64 + j * 7 + 0.05, -57 + j * 7 - 0.05),
               STONE if (i + j) % 2 == 0 else STONE_L, 0.03)
    # sun-stone circle around the Pharaoh Shiba
    vcyl(p, 36, 0.3, 0.4, 4, 12, STONE_L, 20, jit=0.02)
    vcyl(p, 36, 0.4, 0.43, 4, 9.2, GOLD, 20, jit=0.02)
    vcyl(p, 36, 0.43, 0.46, 4, 7.6, STONE_L, 20, jit=0.02)
    vcyl(p, 36, 0.46, 0.49, 4, 3.0, GOLD, 12, jit=0.02)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        dk.box(p, (36 + 5.2 * math.cos(a), 0.47, 4 + 5.2 * math.sin(a)), (3.2, 0.03, 0.9), GOLD_D, rot=(0, -math.degrees(a), 0), jitter=0.02)
    # paving slabs
    bx(p, (21, 39), (0.3, 0.42), (30, 38), STONE_D, 0.05)
    for k in range(4):
        bx(p, (22.5 + k * 4.2, 24.5 + k * 4.2), (0.42, 0.44), (31, 37), STONE, 0.04)
    bx(p, (-88, -68), (0.3, 0.42), (-41, -23), STONE_D, 0.05)
    for i in range(3):
        for j in range(3):
            bx(p, (-87 + i * 6.4, -81.4 + i * 6.4), (0.42, 0.44), (-40 + j * 5.8, -34.8 + j * 5.8), STONE if (i + j) % 2 == 0 else STONE_L, 0.03)
    # scattered rocks and scrub
    for (x, z, s) in ((-40, 20, 1.2), (90, -50, 1.6), (-5, 60, 1.0), (50, 55, 1.3), (-90, 55, 1.5), (5, -30, 1.0)):
        bx(p, (x - s, x + s), (0.3, 0.42), (z - s * 0.8, z + s * 0.8), STONE_D, 0.06, rot=(0, 25, 0))


# ---- 2. Pyramid ------------------------------------------------------------------------------------------------------------
def build_Pyramid(p):
    for i in range(8):
        w0 = 34 - 4 * i
        tbox(p, 0, 0, 3.5 * i, 3.5 * (i + 1), w0, w0, w0 - 3.4, w0 - 3.4, STONE if i % 2 == 0 else STONE_L, 0.05)
    pyr(p, 0, 0, 28, 30.4, 3.0, 3.0, GOLD, 0.02)
    # entrance porch on the road side
    bx(p, (-4.4, 4.4), (0, 0.5), (11.5, 17), STONE_D, 0.04)
    bx(p, (-3.8, -2.6), (0.5, 6.4), (13.5, 17), STONE_L, 0.04)
    bx(p, (2.6, 3.8), (0.5, 6.4), (13.5, 17), STONE_L, 0.04)
    bx(p, (-4.2, 4.2), (6.4, 7.6), (13.5, 17), STONE_L, 0.04)
    bx(p, (-2.6, 2.6), (0.5, 6.4), (13.5, 16.4), BLACK, 0.02)
    bx(p, (-1.0, 1.0), (7.6, 8.4), (14.5, 16.2), GOLD, 0.03)
    # causeway ramp in front
    wedge_z(p, -2.2, 2.2, 0, 0.5, 11.5, 17, STONE_D, 0.04, high_at='z0')


# ---- 3. Sphinx -------------------------------------------------------------------------------------------------------------
def build_Sphinx(p):
    bx(p, (-14, 14), (0, 1), (-5.5, 5.5), STONE_D, 0.05)
    bx(p, (-12, 12.5), (1, 1.4), (-4.5, 4.5), SAND_D, 0.04)
    # lion body, haunch and tail
    bx(p, (-3, 10.5), (1, 4.6), (-3.2, 3.2), SAND, 0.04)
    tbox(p, 3.6, 0, 4.6, 6.0, 14, 6.4, 11, 4.4, SAND, 0.04)                      # rounded back
    ball(p, (-4.6, 4.0, 0), 1.0, SAND, scale=(2.6, 2.6, 3.0), subdiv=2)          # chest
    ball(p, (8, 3.8, 0), 3.4, SAND, scale=(1.1, 0.95, 1.0), subdiv=2)
    bx(p, (-6, -2), (1, 6.6), (-2.8, 2.8), SAND, 0.04)
    bx(p, (-9.4, -4.6), (4, 9.2), (-2.0, 2.0), SAND, 0.04)  # neck
    for s in (-1, 1):
        bx(p, (-14, -3), (1, 3.2), (s * 1.0 + (0.4 if s > 0 else -2.4), s * 1.0 + (2.4 if s > 0 else -0.4)), SAND, 0.04)  # paws
        for k in range(3):
            bx(p, (-14.05, -13.5), (1.0, 2.0), (s * 1.7 - 0.12 + (k - 1) * 0.6, s * 1.7 + 0.12 + (k - 1) * 0.6), SAND_D, 0.02)
    # tail curling up the flank
    bx(p, (10.5, 13.2), (1.0, 1.8), (2.4, 3.6), SAND, 0.04)
    bx(p, (12.4, 13.4), (1.0, 5.2), (2.4, 3.4), SAND, 0.04)
    bx(p, (12.2, 13.6), (4.8, 6.0), (2.2, 3.6), SAND_D, 0.04)
    # head, face, headdress
    bx(p, (-11.0, -5.0), (6.4, 13.0), (-2.9, 2.9), SAND, 0.03)
    bx(p, (-12.0, -10.9), (8.4, 10.4), (-0.8, 0.8), SAND_D, 0.03)   # broken nose
    for s in (-1, 1):
        bx(p, (-11.2, -10.9), (10.6, 11.5), (s * 1.45 - 0.65, s * 1.45 + 0.65), LINEN, 0.02)   # eyes
        bx(p, (-11.35, -11.0), (10.7, 11.4), (s * 1.45 - 0.3, s * 1.45 + 0.3), BLACK, 0.02)
        bx(p, (-11.3, -10.9), (11.7, 12.2), (s * 1.45 - 1.0, s * 1.45 + 1.0), LAPIS, 0.02)    # brows
        for k in range(4):   # nemes lappets, one striped block each side
            bx(p, (-10.4, -5.4), (5.2 + k * 1.85, 5.2 + (k + 1) * 1.85), (s * 3.75 - 0.85, s * 3.75 + 0.85), LAPIS if k % 2 == 0 else GOLD, 0.02)
    bx(p, (-11.6, -10.8), (7.4, 8.0), (-1.1, 1.1), RED, 0.02)     # lips
    bx(p, (-11.3, -10.5), (4.6, 7.4), (-0.6, 0.6), GOLD_D, 0.03)   # beard
    bx(p, (-11.2, -4.4), (13.0, 14.0), (-4.6, 4.6), LAPIS, 0.03)
    bx(p, (-11.4, -11.0), (13.0, 13.7), (-4.6, 4.6), GOLD, 0.03)
    bx(p, (-11.7, -10.9), (13.6, 14.4), (-0.4, 0.4), RED, 0.02)    # uraeus
    # rubble at the base
    bx(p, (-13, -11), (1.4, 2.4), (-5, -3.4), SAND_D, 0.05, rot=(0, 20, 0))
    bx(p, (8, 10.4), (1.4, 2.2), (3.8, 5.2), SAND_D, 0.05, rot=(0, -25, 0))


# ---- 4. Pylon --------------------------------------------------------------------------------------------------------------
def build_Pylon(p):
    bx(p, (-15, 15), (0, 1), (-4, 4), STONE_D, 0.05)
    bx(p, (-14, 14), (1, 1.4), (-3.4, 3.4), STONE, 0.04)
    for s in (-1, 1):
        cx = s * 9
        tbox(p, cx, 0, 1.4, 16.2, 8.8, 5, 7.4, 5, STONE, 0.05)
        bx(p, (cx - 5.2, cx + 5.2), (16.2, 17.3), (-3, 3), STONE_L, 0.04)
        bx(p, (cx - 4.8, cx + 4.8), (17.3, 17.7), (-2.6, 2.6), STONE_D, 0.04)
        # framed relief panel
        bx(p, (cx - 2.9, cx + 2.9), (4, 13.4), (2.5, 2.7), LAPIS, 0.03)
        glyph_col(p, ["bird", "ankh", "eye", "was"], cx, 12.2, 2.7, 2.1, GOLD, 1.15)
        # flagpole with brackets
        vcyl(p, cx, 0.5, 27.6, 3.3, 0.3, WOOD, 6)
        for y in (6, 13, 20):
            bx(p, (cx - 0.25, cx + 0.25), (y, y + 0.5), (2.5, 3.3), WOOD, 0.02)
        ball(p, (cx, 27.7, 3.3), 0.5, GOLD, subdiv=1)
        fx0, fx1 = (cx + 0.3, cx + 3.3) if s < 0 else (cx - 3.3, cx - 0.3)
        bx(p, (fx0, fx1), (22.6, 26.2), (3.2, 3.4), RED if s < 0 else LAPIS, 0.03)
        bx(p, (fx0, fx1), (23.9, 24.9), (3.35, 3.5), GOLD, 0.02)
    # gate lintel with winged sun
    bx(p, (-4.7, 4.7), (11.3, 15.1), (-2.1, 2.1), STONE_L, 0.04)
    bx(p, (-5.8, 5.8), (15.1, 16.1), (-2.4, 2.4), STONE_L, 0.04)
    zcyl(p, 0, 13.4, 2.1, 2.7, 2.1, GOLD, 12)
    zcyl(p, 0, 13.4, 2.7, 3.0, 1.2, RED, 10)
    for s in (-1, 1):
        bx(p, (min(s * 2.3, s * 4.5), max(s * 2.3, s * 4.5)), (13.9, 14.5), (2.1, 2.5), LAPIS, 0.02)
        bx(p, (min(s * 2.3, s * 4.2), max(s * 2.3, s * 4.2)), (13.2, 13.8), (2.1, 2.5), GOLD, 0.02)
        bx(p, (min(s * 2.3, s * 3.8), max(s * 2.3, s * 3.8)), (12.5, 13.1), (2.1, 2.5), LAPIS, 0.02)
        bx(p, (s * 1.9 - 0.3, s * 1.9 + 0.3), (11.4, 12.6), (2.1, 2.5), RED, 0.02)  # cobras


# ---- 5. Obelisks -----------------------------------------------------------------------------------------------------------
def obelisk(p, cx, cz, w0, w1, y0, y1, ytop, pw, col):
    """Tapering shaft with a golden pyramidion and hieroglyph strips on the road side."""
    tbox(p, cx, cz, y0, y1, w0, w0, w1, w1, col, 0.05)
    pyr(p, cx, cz, y1, ytop, w1, w1, GOLD, 0.02)
    bx(p, (cx - w1 / 2 - 0.1, cx + w1 / 2 + 0.1), (y1 - 0.5, y1), (cz - w1 / 2 - 0.1, cz + w1 / 2 + 0.1), GOLD_D, 0.02)
    kinds = ['ankh', 'eye', 'bird', 'was', 'wave', 'sun', 'reed', 'eye', 'ankh', 'bird']
    n = int((y1 - y0 - 3) / 1.7)
    for i in range(n):
        y = y1 - 2.2 - i * 1.7
        wy = w0 + (w1 - w0) * (y - y0) / (y1 - y0)
        glyph(p, kinds[i % len(kinds)], cx, y, cz + wy / 2 - 0.02, 1.1, GRANITE_D)


def build_Obelisks(p):
    bx(p, (-8.8, -3.2), (0, 1), (-5.8, -0.2), STONE_D, 0.05)
    bx(p, (-8, -4), (1, 1.8), (-5, -1), STONE, 0.04)
    obelisk(p, -6, -3, 3.2, 2.2, 1.8, 20.4, 23.2, 2.2, GRANITE)
    bx(p, (4.6, 9.4), (0, 1), (0.6, 5.4), STONE_D, 0.05)
    bx(p, (5.2, 8.8), (1, 1.8), (1.2, 4.8), STONE, 0.04)
    obelisk(p, 7, 3, 2.8, 1.9, 1.8, 17.4, 19.3, 1.9, GRANITE)


# ---- 6. Oasis --------------------------------------------------------------------------------------------------------------
def build_Oasis(p):
    bx(p, (-13.5, 13.5), (0, 0.55), (-10.5, 10.5), GRASS, 0.06)
    # pond with stone rim
    bx(p, (-11, 10), (0.4, 0.75), (-7.25, 7.25), WATER, 0.03)
    for (x0, x1, z0, z1) in ((-11.6, 10.6, -8, -7.1), (-11.6, 10.6, 7.1, 8), (-11.6, -10.8, -7.1, 7.1), (10.2, 11.0, -7.1, 7.1)):
        bx(p, (x0, x1), (0.4, 1.0), (z0, z1), STONE_D, 0.06)
    for k in range(5):
        bx(p, (-8 + k * 4.2, -6.4 + k * 4.2), (0.75, 0.79), (-1.2 + (k % 2) * 3, 0.0 + (k % 2) * 3), WATER_L, 0.02)
    for (x, z, c) in ((-3, 1, PALM), (2, -3, PALM_D), (5, 3, PALM)):   # lily pads and lotus
        vcyl(p, x, 0.75, 0.82, z, 0.9, c, 8, jit=0.03)
    ball(p, (2, 1.1, -3), 0.4, (240, 150, 190), subdiv=1)
    # palms
    palm(p, -7, -5, 10, -8, r=0.6, fr=4.6, y0=0.55, dates=True, yaw0=10)
    palm(p, 8, 4, 11.2, 10, r=0.62, fr=4.8, y0=0.55, dates=True, yaw0=30)
    palm(p, -9, 5.5, 8, -14, r=0.55, fr=4.0, y0=0.55, yaw0=0)
    # reeds, grass tufts and a rock
    bx(p, (9.3, 11.7), (0.55, 2.0), (-7, -5), STONE_D, 0.06, rot=(0, 20, 0))
    for (x, z, h) in ((1, -9, 2.2), (2, -9.4, 2.6), (3.5, -9.4, 2.4), (4.6, -9, 2.0), (-12, 0, 1.8), (-12, 2, 2.2)):
        bx(p, (x - 0.2, x + 0.2), (0.55, 0.55 + h), (z - 0.2, z + 0.2), PALM, 0.05, rot=(0, 0, 6))
        bx(p, (x - 0.25, x + 0.25), (0.55 + h, 0.9 + h), (z - 0.25, z + 0.25), TRUNK, 0.05)
    for (x, z) in ((-12, -8), (12, 8), (-4, 9.5), (6, -9)):
        ball(p, (x, 0.7, z), 1.1, GRASS_D, scale=(1, 0.5, 1), subdiv=1)


# ---- 7. Palms --------------------------------------------------------------------------------------------------------------
def build_Palms(p):
    bx(p, (-13, 13), (0, 0.4), (-8, 8), SAND_D, 0.06)
    palm(p, -8, -3, 13, 10, r=0.7, fr=5.0, dates=True, y0=0.4, yaw0=0)
    palm(p, -1, 4, 10, -8, r=0.65, fr=4.6, dates=True, y0=0.4, yaw0=25)
    palm(p, 6, -2, 14.4, 6, r=0.7, fr=5.2, dates=True, y0=0.4, yaw0=10)
    palm(p, 10, 4, 8.8, -12, r=0.6, fr=4.2, dates=False, y0=0.4, yaw0=40)
    for (x, z, s) in ((-11, 5, 1.2), (3, -6, 0.9), (12, -5, 1.1)):
        bx(p, (x - s, x + s), (0.4, 0.4 + s), (z - s, z + s), STONE_D, 0.06, rot=(0, 30, 0))
    for (x, z) in ((-4, -6), (-12, 0), (9, 0), (1, 7)):
        ball(p, (x, 0.7, z), 1.0, GRASS_D, scale=(1, 0.55, 1), subdiv=1)
    pot(p, 3, 0.4, 5.6, 1.0, 1.8, CLAY)


# ---- 8. Bazaar -------------------------------------------------------------------------------------------------------------
def stall(p, cx, cz, along, awn, rotv, sx=5.4, sz=2.4):
    """Market stall: counter, posts, striped awning. along='x' (stall faces +z) or 'z' (faces +x)."""
    stripes = 6
    if along == 'x':
        bx(p, (cx - sx / 2, cx + sx / 2), (0, 2.6), (cz - sz / 2, cz + sz / 2), WOOD, 0.05)
        bx(p, (cx - sx / 2 - 0.15, cx + sx / 2 + 0.15), (2.6, 2.9), (cz - sz / 2 - 0.15, cz + sz / 2 + 0.3), STONE_D, 0.04)
        for sx_ in (-1, 1):
            vcyl(p, cx + sx_ * 2.4, 0, 5.2, cz + 1.4, 0.22, WOOD, 6)
            vcyl(p, cx + sx_ * 2.4, 0, 5.4, cz - 1.0, 0.22, WOOD, 6)
        w = 6.4 / stripes
        for k in range(stripes):
            c = ((cx - 3.2 + (k + 0.5) * w) + OX, 5.4, cz - 0.1 + OZ)
            dk.box(p, c, (w, 0.4, 4.6), awn if k % 2 == 0 else LINEN, rot=(rotv, 0, 0), jitter=0.03)
    else:
        bx(p, (cx - sz / 2, cx + sz / 2), (0, 2.6), (cz - sx / 2, cz + sx / 2), WOOD, 0.05)
        bx(p, (cx - sz / 2 - 0.3, cx + sz / 2 + 0.15), (2.6, 2.9), (cz - sx / 2 - 0.15, cz + sx / 2 + 0.15), STONE_D, 0.04)
        for sz_ in (-1, 1):
            vcyl(p, cx - 1.6, 0, 5.2, cz + sz_ * 2.4, 0.22, WOOD, 6)
            vcyl(p, cx + 1.0, 0, 5.4, cz + sz_ * 2.4, 0.22, WOOD, 6)
        w = 6.4 / stripes
        for k in range(stripes):
            c = (cx - 0.6 + OX, 5.4, (cz - 3.2 + (k + 0.5) * w) + OZ)
            dk.box(p, c, (4.6, 0.4, w), awn if k % 2 == 0 else LINEN, rot=(0, 0, rotv), jitter=0.03)


def build_Bazaar(p):
    # ground rug
    bx(p, (-10.2, 10.7), (0, 0.15), (-6.7, 7.2), SAND_D, 0.05)
    stall(p, -7, -3, 'x', RED, 14)
    stall(p, 3, -5, 'x', LAPIS, 14)
    stall(p, 9, 4, 'z', GOLD, -14)
    # goods on the counters
    for k in range(4):
        ball(p, (-8.8 + k * 1.15, 3.2, -2.6), 0.5, (225, 70 + k * 30, 40), subdiv=1)          # fruit
    bx(p, (-9.5, -4.5), (2.9, 3.3), (-3.9, -3.2), TURQ, 0.03)                                    # cloth roll
    for k in range(3):
        vcyl(p, 1.2 + k * 1.6, 2.9, 3.6, -4.6, 0.6, (230, 200, 60) if k != 1 else (200, 60, 50), 8, top_r=0.5)   # spice bowls
    bx(p, (8.4, 9.6), (2.9, 3.6), (1.4, 3.0), GOLD_D, 0.04)
    bx(p, (8.4, 9.6), (2.9, 3.4), (4.4, 6.0), TURQ, 0.04)
    # jars, baskets and a stack of crates
    pot(p, -1.4, 0, 3.6, 1.3, 2.8, MUD)
    pot(p, 1.2, 0, 5.2, 1.0, 2.2, CLAY, band=GOLD_D)
    pot(p, -3.2, 0, 5.8, 0.8, 1.6, TURQ)
    vcyl(p, -5, 0, 1.3, 3, 1.2, (204, 160, 70), 8, top_r=1.4)
    vcyl(p, -5, 1.3, 1.5, 3, 1.15, (200, 60, 50), 8)
    bx(p, (5.8, 7.6), (0, 1.5), (1.4, 3.2), WOOD, 0.05)
    bx(p, (6.1, 7.7), (1.5, 2.8), (1.7, 3.1), WOOD, 0.05, rot=(0, 20, 0))


# ---- 9. Anubis -------------------------------------------------------------------------------------------------------------
def anubis(p, cx, cz, plinth=True):
    """Standing jackal-headed god facing +z: kilt, gold collar, black head with tall ears, was sceptre in one hand."""
    if plinth:
        bx(p, (cx - 2.8, cx + 2.8), (0, 1.0), (cz - 2.5, cz + 2.5), STONE_D, 0.05)
        bx(p, (cx - 2.3, cx + 2.3), (1.0, 2.0), (cz - 2.0, cz + 2.0), STONE, 0.04)
    tbox(p, cx, cz, 2.0, 5.4, 2.8, 1.8, 2.5, 1.7, LINEN, 0.03)                  # kilt
    for k in (-1, 0, 1):
        bx(p, (cx + k * 0.8 - 0.1, cx + k * 0.8 + 0.1), (2.2, 5.2), (cz + 0.85, cz + 1.0), GOLD_D, 0.02)
    bx(p, (cx - 1.4, cx + 1.4), (5.4, 6.0), (cz - 0.95, cz + 0.95), GOLD, 0.03)    # belt
    bx(p, (cx - 1.3, cx + 1.3), (6.0, 9.0), (cz - 0.85, cz + 0.85), BLACK, 0.03)   # torso
    for s in (-1, 1):
        bx(p, (cx + s * 1.3 + (0 if s > 0 else -0.5), cx + s * 1.3 + (0.5 if s > 0 else 0)), (5.0, 8.8), (cz - 0.45, cz + 0.55), BLACK, 0.03)  # arms
        bx(p, (cx + s * 1.25 - 0.3, cx + s * 1.25 + 0.3), (5.8, 6.2), (cz - 0.5, cz + 0.6), GOLD, 0.02)
    # usekh collar
    tbox(p, cx, cz + 0.1, 8.4, 9.4, 4.2, 2.2, 3.4, 2.0, GOLD, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * 0.9 - 0.3, cx + s * 0.9 + 0.3), (8.5, 9.3), (cz + 1.0, cz + 1.2), TURQ, 0.02)
    bx(p, (cx - 0.5, cx + 0.5), (9.4, 10.4), (cz - 0.5, cz + 0.5), BLACK, 0.03)       # neck
    # jackal head: skull, long snout, nose, ears, eyes
    bx(p, (cx - 0.95, cx + 0.95), (10.2, 12.4), (cz - 1.0, cz + 1.0), BLACK, 0.03)
    tbox(p, cx, cz + 1.6, 10.4, 11.5, 1.3, 1.8, 0.9, 1.8, BLACK, 0.03)
    bx(p, (cx - 0.5, cx + 0.5), (11.2, 11.8), (cz + 2.2, cz + 2.5), GOLD_D, 0.02)
    for s in (-1, 1):
        wedge_z(p, cx + s * 0.5 - 0.3, cx + s * 0.5 + 0.3, 12.2, 14.6, cz - 0.4, cz + 0.3, BLACK, 0.02, high_at='z0')
        bx(p, (cx + s * 0.5 - 0.3, cx + s * 0.5 + 0.3), (14.0, 14.6), (cz - 0.4, cz), GOLD, 0.02)
        bx(p, (cx + s * 0.95 - 0.08, cx + s * 0.95 + 0.08), (11.6, 12.0), (cz + 0.7, cz + 1.3), GOLD, 0.02)
    bx(p, (cx - 1.0, cx + 1.0), (12.0, 12.4), (cz - 1.05, cz + 1.05), GOLD, 0.03)   # headband
    # was sceptre
    sxp = cx + (-2.7 if cx < 0 else 2.7)
    vcyl(p, sxp, 2.0, 11.6, cz + 0.8, 0.2, GOLD, 6)
    bx(p, (sxp - 0.35, sxp + 0.35), (11.2, 12.0), (cz + 0.45, cz + 1.15), GOLD, 0.02)
    bx(p, (sxp - 0.15, sxp + 0.55), (11.6, 12.2), (cz + 0.6, cz + 1.0), GOLD, 0.02)


def build_Anubis(p):
    anubis(p, -5.5, 0)
    anubis(p, 5.5, 0)
    # shared base sand drift
    bx(p, (-1.2, 1.2), (0, 0.5), (-1.5, 1.5), STONE_D, 0.05)


# ---- 10. Camel -------------------------------------------------------------------------------------------------------------
CAM = (196, 150, 96)
CAM_D = (176, 130, 84)
CAM_L = (212, 172, 118)


def build_Camel(p):
    # body, hump, saddle blanket
    bx(p, (-3.6, 3.6), (3.6, 6.8), (-1.4, 1.4), CAM, 0.04)
    ball(p, (0.4, 7.2, 0), 1.7, CAM, scale=(1.0, 1.0, 0.9), subdiv=2)
    ball(p, (3.4, 5.3, 0), 1.6, CAM, scale=(0.8, 1.0, 0.95), subdiv=1)
    bx(p, (-1.4, 2.2), (6.7, 7.0), (-1.7, 1.7), RED, 0.03)
    bx(p, (-1.4, 2.2), (4.6, 7.0), (1.4, 1.75), RED, 0.03)
    bx(p, (-1.4, 2.2), (4.6, 7.0), (-1.75, -1.4), RED, 0.03)
    bx(p, (-1.4, 2.2), (5.0, 5.3), (1.7, 1.8), GOLD, 0.02)
    bx(p, (-1.4, 2.2), (5.0, 5.3), (-1.8, -1.7), GOLD, 0.02)
    # neck and head (facing -x)
    bx(p, (-4.7, -3.2), (5.0, 8.0), (-0.8, 0.8), CAM, 0.04)
    bx(p, (-5.9, -4.3), (8.0, 9.7), (-0.8, 0.8), CAM, 0.04, rot=(0, 0, 18))
    bx(p, (-7.3, -4.9), (9.1, 10.4), (-0.7, 0.7), CAM_L, 0.04)
    bx(p, (-7.4, -6.6), (8.3, 9.3), (-0.55, 0.55), CAM_L, 0.04)
    bx(p, (-7.5, -7.3), (9.3, 9.7), (-0.4, 0.4), BLACK, 0.02)
    for s in (-1, 1):
        bx(p, (-6.0, -5.7), (10.0, 10.5), (s * 0.55 - 0.15, s * 0.55 + 0.15), CAM_D, 0.02)   # ears
        bx(p, (-6.45, -6.2), (9.8, 10.2), (s * 0.7 - 0.05, s * 0.7 + 0.05), BLACK, 0.02)    # eyes
    bx(p, (-5.0, -4.5), (6.2, 9.0), (-0.9, 0.9), CAM_D, 0.05)                              # mane
    # legs with knees and feet
    for (x, zz) in ((-2.6, -1.0), (-2.6, 1.0), (2.6, -1.0), (2.6, 1.0)):
        bx(p, (x - 0.5, x + 0.5), (1.8, 3.8), (zz - 0.45, zz + 0.45), CAM_D, 0.04)
        bx(p, (x - 0.38, x + 0.38), (0.5, 1.9), (zz - 0.35, zz + 0.35), CAM, 0.04)
        bx(p, (x - 0.7, x + 0.7), (0, 0.5), (zz - 0.55, zz + 0.55), STONE_D, 0.04)
    bx(p, (3.4, 4.0), (3.2, 5.6), (-0.15, 0.15), CAM_D, 0.04)    # tail
    # cargo
    bx(p, (5.2, 7.6), (0, 2), (-3.2, -0.8), WOOD, 0.05)
    bx(p, (5.9, 8.0), (2, 3.2), (-3.2, -1.2), WOOD, 0.05, rot=(0, 24, 0))
    bx(p, (5.2, 7.6), (0.6, 0.9), (-3.25, -0.75), GOLD_D, 0.02)
    pot(p, 6.6, 0, 2.4, 1.0, 2.2, MUD)
    bx(p, (-2.1, 0.9), (0, 0.3), (2.6, 4.6), LAPIS, 0.03)                                       # rug
    bx(p, (-1.7, 0.5), (0.3, 0.34), (3.1, 4.1), GOLD, 0.02)
    bx(p, (-4.6, -3.0), (0.0, 0.3), (2.6, 3.8), RED, 0.03)
    # leading rope to the head


# ---- 11. Colonnade ---------------------------------------------------------------------------------------------------------
def build_Colonnade(p):
    bx(p, (-14, 14), (0, 0.6), (-6, 6), STONE_D, 0.05)
    bx(p, (-4, 4), (0.6, 0.7), (-5.8, 5.8), LAPIS, 0.03)
    bx(p, (-0.6, 0.6), (0.7, 0.75), (-5.8, 5.8), GOLD, 0.02)
    for x in (-10, -3.5, 3.5, 10):
        for z in (-4, 4):
            bx(p, (x - 1.4, x + 1.4), (0.6, 1.1), (z - 1.4, z + 1.4), STONE_L, 0.04)
            vcyl(p, x, 1.1, 11.0, z, 1.0, STONE, 8, top_r=0.85)
            vcyl(p, x, 3.0, 3.4, z, 1.05, GOLD, 8)
            vcyl(p, x, 9.4, 9.8, z, 0.95, TURQ, 8)
            lotus_cap(p, x, 11.0, z, 1.0, 1.7)
    for z in (-4, 4):
        bx(p, (-12.6, 12.6), (12.7, 14.2), (z - 1.4, z + 1.4), STONE_L, 0.04)
        bx(p, (-12.6, 12.6), (13.2, 13.7), (z - 1.45, z + 1.45), GOLD, 0.02)
        for k in range(13):
            bx(p, (-12.2 + k * 2.04, -11.6 + k * 2.04), (13.5 + 0.0, 14.5), (z + (1.4 if z > 0 else -1.5), z + (1.5 if z > 0 else -1.4)), TURQ if k % 2 else LAPIS, 0.02)
    bx(p, (-12.6, 12.6), (14.2, 14.7), (-6, 6), STONE_D, 0.04)
    bx(p, (-12.6, 12.6), (14.7, 15.3), (-6, 6), LAPIS, 0.03)
    for k in range(5):
        bx(p, (-10 + k * 5 - 0.35, -10 + k * 5 + 0.35), (15.3, 15.34), (-5.4, 5.4), GOLD, 0.02)
    for s in (-1, 1):
        bx(p, (s * 12.6 - 0.4, s * 12.6 + 0.4), (14.2, 15.3), (-6, 6), STONE_L, 0.03)
    # steps in front
    bx(p, (-5, 5), (0, 0.4), (5.9, 6.0), STONE, 0.02)


# ---- 12. Tomb --------------------------------------------------------------------------------------------------------------
def jackal_lying(p, cx, cz):
    """Black jackal lying on a plinth facing +z, gold collar."""
    bx(p, (cx - 1.6, cx + 1.6), (0, 0.8), (cz - 2.2, cz + 2.2), STONE_D, 0.05)
    bx(p, (cx - 0.9, cx + 0.9), (0.8, 2.4), (cz - 1.8, cz + 0.9), BLACK, 0.03)
    ball(p, (cx, 1.8, cz - 1.4), 1.1, BLACK, scale=(0.9, 1, 1), subdiv=1)
    bx(p, (cx - 0.7, cx + 0.7), (0.8, 3.4), (cz + 0.3, cz + 1.2), BLACK, 0.03)
    bx(p, (cx - 0.6, cx + 0.6), (3.0, 4.3), (cz + 0.3, cz + 1.6), BLACK, 0.03)
    bx(p, (cx - 0.35, cx + 0.35), (3.2, 3.8), (cz + 1.6, cz + 2.6), BLACK, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * 0.35 - 0.15, cx + s * 0.35 + 0.15), (4.3, 5.8), (cz + 0.3, cz + 0.8), BLACK, 0.02)
        bx(p, (cx + s * 0.35 - 0.15, cx + s * 0.35 + 0.15), (5.4, 5.8), (cz + 0.3, cz + 0.6), GOLD, 0.02)
        bx(p, (cx + s * 0.55 - 0.1, cx + s * 0.55 + 0.1), (0.8, 1.5), (cz + 0.8, cz + 2.0), BLACK, 0.03)
    bx(p, (cx - 0.8, cx + 0.8), (2.8, 3.2), (cz + 0.2, cz + 1.4), GOLD, 0.02)


def build_Tomb(p):
    # cliff: stacked tiers and boulders
    bx(p, (-12, 12), (0, 10), (-7, 2), STONE_D, 0.06)
    tbox(p, 0.5, -3, 10, 12.4, 22, 8, 17, 7, STONE, 0.06)
    tbox(p, -3, -3.5, 12.4, 15.2, 9, 5.5, 5.5, 4, STONE_D, 0.06)
    for (x0, x1, y1) in ((-12, -9, 6.5), (9, 12, 7.5)):
        bx(p, (x0, x1), (0, y1), (1.6, 3.2), STONE_D, 0.07)
    # carved facade
    bx(p, (-4, 4), (0, 7.2), (2, 3.4), STONE_L, 0.04)
    bx(p, (-4.4, 4.4), (7.2, 8.4), (2, 3.8), STONE_L, 0.04)
    bx(p, (-4.0, 4.0), (8.4, 8.8), (2.2, 3.9), GOLD, 0.02)
    bx(p, (-2.2, 2.2), (0.4, 6.4), (3.4, 3.6), BLACK, 0.02)
    for s in (-1, 1):
        vcyl(p, s * 3.2, 0.4, 7.2, 4.3, 0.65, STONE_L, 8, top_r=0.55)
        lotus_cap(p, s * 3.2, 7.0, 4.3, 0.75, 0.9, STONE_L, GOLD)
        bx(p, (s * 3.2 - 1.0, s * 3.2 + 1.0), (0, 0.4), (3.4, 5.2), STONE_D, 0.04)
    zcyl(p, 0, 9.8, 3.3, 3.8, 0.9, GOLD, 10)
    bx(p, (-1.9, 1.9), (9.4, 9.9), (3.3, 3.7), GOLD, 0.02)
    glyph(p, 'wave', -2.1, 9.8, 3.8, 1.0, LAPIS)
    glyph(p, 'wave', 2.1, 9.8, 3.8, 1.0, LAPIS)
    jackal_lying(p, -8, 4.4)
    jackal_lying(p, 8, 4.4)
    # steps
    bx(p, (-4, 4), (0, 0.4), (4.9, 7.2), STONE_D, 0.04)
    bx(p, (-3.2, 3.2), (0.4, 0.8), (3.5, 5.0), STONE_D, 0.04)


# ---- 13. HieroWall ---------------------------------------------------------------------------------------------------------
def god(p, x, y0, kind, face=1):
    """Flat relief figure on the wall front: walking god with a staff, painted in gold, white and brown."""
    z0, z1 = 1.2, 1.45
    bx(p, (x - 0.6, x + 0.0), (y0, y0 + 1.4), (z0, z1), SKIN, 0.02)
    bx(p, (x - 0.1, x + 0.5), (y0, y0 + 1.4), (z0, z1), SKIN, 0.02)
    bx(p, (x - 0.7, x + 0.6), (y0 + 1.3, y0 + 2.2), (z0, z1 + 0.05), LINEN, 0.02)
    bx(p, (x - 0.5, x + 0.5), (y0 + 2.2, y0 + 3.5), (z0, z1), SKIN, 0.02)
    bx(p, (x - 0.6, x + 0.6), (y0 + 3.2, y0 + 3.6), (z0, z1 + 0.1), GOLD, 0.02)
    bx(p, (min(x + 0.4 * face, x + 1.4 * face), max(x + 0.4 * face, x + 1.4 * face)), (y0 + 3.0, y0 + 3.3), (z0, z1), SKIN, 0.02)
    bx(p, (x + 1.3 * face - 0.1, x + 1.3 * face + 0.1), (y0, y0 + 3.9), (z0, z1 + 0.05), GOLD, 0.02)
    if kind == 'jackal':
        bx(p, (x - 0.4, x + 0.4), (y0 + 3.6, y0 + 4.6), (z0, z1 + 0.05), BLACK, 0.02)
        bx(p, (min(x, x + 1.2 * face), max(x, x + 1.2 * face)), (y0 + 3.9, y0 + 4.25), (z0, z1 + 0.05), BLACK, 0.02)
        bx(p, (x - 0.35, x), (y0 + 4.6, y0 + 5.7), (z0, z1), BLACK, 0.02)
    elif kind == 'falcon':
        bx(p, (x - 0.4, x + 0.4), (y0 + 3.6, y0 + 4.6), (z0, z1 + 0.05), FALCON, 0.02)
        bx(p, (min(x + 0.4 * face, x + 0.9 * face), max(x + 0.4 * face, x + 0.9 * face)), (y0 + 3.9, y0 + 4.3), (z0, z1 + 0.05), GOLD, 0.02)
        bx(p, (x - 0.4, x + 0.4), (y0 + 4.6, y0 + 5.0), (z0, z1 + 0.05), RED, 0.02)


def build_HieroWall(p):
    bx(p, (-12, 12), (0, 6.8), (-1.2, 1.2), STONE, 0.05)
    bx(p, (-12.5, 12.5), (6.8, 7.6), (-1.5, 1.5), STONE_L, 0.04)
    bx(p, (-12.5, 12.5), (7.6, 7.8), (-1.2, 1.2), GOLD, 0.02)
    for s in (-1, 1):
        tbox(p, s * 12.6, 0, 0, 8.4, 3.2, 3.0, 2.8, 2.6, STONE_L, 0.05)
        bx(p, (s * 12.6 - 1.7, s * 12.6 + 1.7), (8.4, 9.2), (-1.5, 1.5), GOLD, 0.03)
        bx(p, (s * 12.6 - 0.9, s * 12.6 + 0.9), (2.8, 7.4), (1.5, 1.7), LAPIS, 0.02)
        glyph(p, 'ankh', s * 12.6, 5.0, 1.7, 1.6, GOLD)
        glyph(p, 'was', s * 12.6, 3.2, 1.7, 1.2, GOLD)
    bx(p, (-11.5, 11.5), (5.1, 6.1), (1.2, 1.5), LAPIS, 0.02)
    for k in range(11):
        bx(p, (-10.8 + k * 2.16, -10.2 + k * 2.16), (5.4, 5.8), (1.5, 1.65), GOLD, 0.02)
    god(p, -9.2, 0.6, 'jackal', 1)
    god(p, 9.2, 0.6, 'falcon', -1)
    for s in (-1, 1):
        bx(p, (s * 4 - 1.2, s * 4 + 1.2), (1.3, 4.7), (1.2, 1.5), GOLD, 0.02)
        bx(p, (s * 4 - 0.9, s * 4 + 0.9), (1.6, 4.4), (1.5, 1.6), STONE_L, 0.02)
        bx(p, (s * 4 - 0.15, s * 4 + 0.15), (2.0, 4.0), (1.6, 1.7), BLACK, 0.02)
        bx(p, (s * 4 - 0.5, s * 4 + 0.5), (1.0, 1.4), (1.2, 1.5), GOLD, 0.02)
    zcyl(p, 0, 4.1, 1.2, 1.7, 1.0, GOLD, 10)
    zcyl(p, 0, 4.1, 1.7, 1.85, 0.55, RED, 8)
    for s in (-1, 1):
        bx(p, (min(s * 1.0, s * 2.4), max(s * 1.0, s * 2.4)), (4.2, 4.5), (1.2, 1.6), GOLD, 0.02)
        bx(p, (min(s * 1.0, s * 2.0), max(s * 1.0, s * 2.0)), (3.8, 4.1), (1.2, 1.6), LAPIS, 0.02)
    glyph(p, 'ankh', 0, 2.0, 1.2, 2.4, GOLD, 0.3)
    glyph_col(p, ['bird', 'eye', 'wave'], -6.6, 4.4, 1.2, 1.2, LAPIS, 1.1)
    glyph_col(p, ['was', 'sun', 'reed'], 6.6, 4.4, 1.2, 1.2, LAPIS, 1.1)
    bx(p, (-11, -7), (0, 1.2), (1.5, 3.8), STONE_D, 0.05)


# ---- 14. SunDisc -----------------------------------------------------------------------------------------------------------
def build_SunDisc(p):
    bx(p, (-9, 9), (0, 1.2), (-4, 4), STONE_D, 0.05)
    bx(p, (-6, 6), (1.2, 2.0), (-2.5, 2.5), STONE, 0.04)
    for s in (-1, 1):
        bx(p, (s * 6 - 1.3, s * 6 + 1.3), (2.0, 13.0), (-1.3, 1.3), STONE, 0.04)
        for y in (4.0, 9.0):
            bx(p, (s * 6 - 1.4, s * 6 + 1.4), (y, y + 0.45), (-1.4, 1.4), GOLD, 0.02)
        bx(p, (s * 6 - 1.0, s * 6 + 1.0), (5, 8), (1.3, 1.45), LAPIS, 0.02)
        glyph(p, 'ankh', s * 6, 6.5, 1.45, 1.8, GOLD)
        bx(p, (s * 6 - 1.8, s * 6 + 1.8), (13.0, 14.2), (-1.8, 1.8), STONE_L, 0.03)
    # disc: gold rim, red heart, gold boss
    zcyl(p, 0, 10.6, -0.5, 0.5, 5.0, GOLD, 16)
    zcyl(p, 0, 10.6, 0.5, 0.8, 3.7, RED, 14)
    zcyl(p, 0, 10.6, 0.8, 1.0, 1.8, GOLD, 10)
    for s in (-1, 1):   # cobras flanking the disc
        bx(p, (s * 5.2 - 0.3, s * 5.2 + 0.3), (11.2, 13.0), (-0.3, 0.3), RED, 0.02)
        bx(p, (s * 5.0 - 0.6, s * 5.0 + 0.6), (13.0, 13.7), (-0.3, 0.3), RED, 0.02)
    # altar with offering bowl
    bx(p, (-1.9, 1.9), (2.0, 3.6), (0.4, 2.6), LAPIS, 0.03)
    bx(p, (-2.1, 2.1), (3.6, 3.9), (0.3, 2.7), GOLD, 0.02)
    vcyl(p, 0, 3.9, 4.6, 1.5, 0.9, GOLD, 8, top_r=1.1)
    bx(p, (-0.4, 0.4), (4.6, 5.6), (1.1, 1.9), RED, 0.03)
    bx(p, (-0.25, 0.25), (5.6, 6.2), (1.25, 1.75), GOLD, 0.02)
    bx(p, (-3.4, 3.4), (0, 0.6), (3.0, 4.0), STONE, 0.04)


# ---- 15. Horus -------------------------------------------------------------------------------------------------------------
def build_Horus(p):
    bx(p, (-4.5, 4.5), (0, 2), (-4.5, 4.5), STONE_D, 0.05)
    bx(p, (-3.2, 3.2), (2, 3.2), (-3.2, 3.2), STONE, 0.04)
    bx(p, (-2.6, 2.6), (0.6, 1.5), (4.5, 4.7), LAPIS, 0.02)
    glyph(p, 'eye', -1.6, 1.05, 4.7, 1.3, GOLD)
    glyph(p, 'was', 0, 1.05, 4.7, 1.3, GOLD)
    glyph(p, 'ankh', 1.6, 1.05, 4.7, 1.3, GOLD)
    # falcon body, chest, wings, tail
    ball(p, (0, 6.8, 0), 1.0, FALCON, scale=(2.2, 3.5, 2.0), subdiv=2)
    ball(p, (0, 6.2, 1.1), 1.0, FALCON_L, scale=(1.4, 2.6, 1.0), subdiv=1)
    for s in (-1, 1):
        bx(p, (s * 2.0 - 0.45, s * 2.0 + 0.45), (3.6, 9.6), (-1.8, 1.4), FALCON, 0.04, rot=(0, 0, -s * 6))
        for k in range(3):   # layered flight feathers
            bx(p, (s * (2.0 + 0.1 * k) - 0.4, s * (2.0 + 0.1 * k) + 0.4), (3.4 - k * 0.0, 5.4 + k * 1.0), (-2.9 + k * 0.5, -1.7 + k * 0.5), FALCON_L if k % 2 == 0 else FALCON, 0.03)
    bx(p, (-1.2, 1.2), (2.4, 6.0), (-3.0, -1.8), FALCON, 0.04, rot=(24, 0, 0))
    bx(p, (-0.7, 0.7), (2.4, 4.0), (-3.4, -2.6), FALCON_L, 0.03, rot=(24, 0, 0))
    # legs and talons
    for s in (-1, 1):
        bx(p, (s * 1.0 - 0.3, s * 1.0 + 0.3), (3.2, 4.4), (0.3, 0.9), GOLD, 0.02)
        for k in (-1, 0, 1):
            bx(p, (s * 1.0 + k * 0.4 - 0.12, s * 1.0 + k * 0.4 + 0.12), (3.2, 3.6), (0.6, 1.9), GOLD_D, 0.02)
    # head
    ball(p, (0, 11.6, 0.4), 1.0, FALCON, scale=(1.5, 1.5, 1.5), subdiv=2)
    bx(p, (-0.45, 0.45), (10.5, 11.9), (1.4, 2.7), GOLD, 0.02)         # beak
    bx(p, (-0.35, 0.35), (10.2, 10.9), (2.0, 3.1), GOLD, 0.02)
    for s in (-1, 1):
        bx(p, (s * 0.85 - 0.25, s * 0.85 + 0.25), (11.7, 12.4), (1.1, 1.7), BLACK, 0.02)   # eyes
        bx(p, (s * 0.85 - 0.1, s * 0.85 + 0.1), (10.3, 11.7), (1.1, 1.5), BLACK, 0.02)      # tear mark
        bx(p, (s * 1.35 - 0.2, s * 1.35 + 0.2), (11.2, 12.0), (-0.3, 0.9), FALCON_L, 0.03)
    # white crown rising from a red band, gold brow, uraeus
    bx(p, (-1.0, 1.0), (12.9, 13.5), (-0.6, 1.4), GOLD, 0.02)
    tbox(p, 0, 0.4, 13.5, 14.4, 2.6, 2.6, 2.4, 2.4, RED, 0.03)
    tbox(p, 0, 0.4, 14.4, 16.2, 2.2, 2.2, 1.0, 1.0, LINEN, 0.02)
    ball(p, (0, 16.2, 0.4), 0.45, LINEN, subdiv=1)
    bx(p, (-0.15, 0.15), (13.9, 15.0), (1.2, 1.5), RED, 0.02)           # uraeus
    bx(p, (-0.2, 0.2), (13.5, 14.1), (1.1, 1.6), GOLD, 0.02)


# ---- 16. Scarab ------------------------------------------------------------------------------------------------------------
def build_Scarab(p):
    bx(p, (-6.2, 6.2), (0, 1.2), (-4.5, 4.5), STONE_D, 0.05)
    bx(p, (-5.2, 5.2), (1.2, 2.0), (-3.6, 3.6), STONE, 0.04)
    bx(p, (-5.2, 5.2), (1.3, 1.9), (3.6, 3.8), LAPIS, 0.02)
    for k in range(5):
        bx(p, (-4.0 + k * 2.0 - 0.3, -4.0 + k * 2.0 + 0.3), (1.35, 1.85), (3.8, 3.95), GOLD, 0.02)
    # six gold legs (angled), below the shell
    for s in (-1, 1):
        for (z, ang) in ((2.2, -30), (-0.2, 0), (-2.6, 30)):
            x0, x1 = (3.0, 6.0) if s > 0 else (-6.0, -3.0)
            bx(p, (x0, x1), (3.4, 4.0), (z - 0.35, z + 0.35), GOLD, 0.02, rot=(0, -s * ang, 0))
            bx(p, (s * 5.7 - 0.35, s * 5.7 + 0.35), (2.0, 3.9), (z - 0.35, z + 0.35), GOLD_D, 0.02)
    # shell (elytra), thorax shield, head
    ball(p, (0, 4.8, -1.2), 1.0, LAPIS, scale=(4.4, 2.8, 3.4), subdiv=2)
    for k in range(7):    # split down the back, following the shell
        z = -3.6 + k * 0.7
        yt = 4.8 + 2.8 * math.sqrt(max(1 - ((z + 1.2) / 3.4) ** 2, 0))
        bx(p, (-0.15, 0.15), (yt - 0.25, yt + 0.05), (z - 0.4, z + 0.4), BLACK, 0.01)
    ball(p, (0, 4.8, 1.7), 1.0, TURQ, scale=(3.0, 2.3, 1.6), subdiv=2)
    ball(p, (0, 4.5, 3.1), 1.0, GOLD, scale=(1.6, 1.3, 1.1), subdiv=1)
    for k in (-1, 0, 1):
        bx(p, (k * 0.8 - 0.2, k * 0.8 + 0.2), (4.2, 5.2), (3.9, 4.6), GOLD_D, 0.02)   # head horns
    for s in (-1, 1):
        bx(p, (s * 0.8 - 0.2, s * 0.8 + 0.2), (5.0, 5.5), (3.7, 4.2), BLACK, 0.02)
        bx(p, (s * 1.35 - 0.3, s * 1.35 + 0.3), (5.2, 8.0), (3.0, 3.6), GOLD, 0.02, rot=(0, 0, -s * 6))   # front legs reach up
    # sun disc held high above the head
    zcyl(p, 0, 8.7, 3.1, 3.9, 1.5, GOLD, 12, 0.03)
    zcyl(p, 0, 8.7, 3.9, 4.2, 0.8, RED, 10, 0.02)


# ---- 17. Village -----------------------------------------------------------------------------------------------------------
def house(p, x0, x1, z0, z1, h, col, roof_col=STONE_D, door='front'):
    tbox(p, (x0 + x1) / 2, (z0 + z1) / 2, 0, h, x1 - x0, z1 - z0, x1 - x0 - 0.6, z1 - z0 - 0.6, col, 0.06)
    bx(p, (x0 - 0.3, x1 + 0.3), (h, h + 0.6), (z0 - 0.3, z1 + 0.3), roof_col, 0.05)
    bx(p, (x0 - 0.3, x1 + 0.3), (h + 0.6, h + 1.1), (z0 - 0.3, z0 + 0.2), roof_col, 0.05)
    bx(p, (x0 - 0.3, x1 + 0.3), (h + 0.6, h + 1.1), (z1 - 0.2, z1 + 0.3), roof_col, 0.05)
    bx(p, (x0 - 0.3, x0 + 0.2), (h + 0.6, h + 1.1), (z0 - 0.3, z1 + 0.3), roof_col, 0.05)
    bx(p, (x1 - 0.2, x1 + 0.3), (h + 0.6, h + 1.1), (z0 - 0.3, z1 + 0.3), roof_col, 0.05)
    cx = (x0 + x1) / 2
    bx(p, (cx - 1.0, cx + 1.0), (0, 3.4), (z1 - 0.1, z1 + 0.15), BLACK, 0.02)
    bx(p, (cx - 1.2, cx + 1.2), (3.4, 3.8), (z1 - 0.1, z1 + 0.3), WOOD, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * 2.2 - 0.4, cx + s * 2.2 + 0.4), (h - 1.8, h - 0.9), (z1 - 0.1, z1 + 0.15), BLACK, 0.02)


def build_Village(p):
    bx(p, (-10.8, 10.8), (0, 0.2), (-7.8, 7.8), SAND_D, 0.05)
    house(p, -10.5, -1.5, -7, 1, 6, MUD)                              # house 1 with canopy
    bx(p, (-9, -3), (7.2, 7.5), (-6, 0), LINEN, 0.03)
    for (x, z) in ((-9, -6), (-3, -6), (-9, 0), (-3, 0)):
        vcyl(p, x, 6.6, 7.2, z, 0.18, WOOD, 6)
    house(p, 1.5, 8.5, 0.5, 7.5, 5, (196, 150, 104))                  # house 2 with a wind catcher
    tbox(p, 5, 4, 5.6, 8.4, 1.8, 1.8, 1.8, 1.8, (196, 150, 104), 0.05)
    bx(p, (4.2, 5.8), (7.4, 8.2), (4.0, 4.1), BLACK, 0.02)
    house(p, 4.5, 10.5, -7.5, -1.5, 8.4, MUD)                           # tall house 3
    # roof ladder
    for s in (-0.3, 0.3):
        bx(p, (1.5 + s - 0.12, 1.5 + s + 0.12), (0, 6.6), (3.6, 3.84), WOOD, 0.03, rot=(0, 0, 8))
    for k in range(6):
        bx(p, (1.2, 2.2), (0.7 + k * 1.0, 0.9 + k * 1.0), (3.6, 3.9), WOOD, 0.03, rot=(0, 0, 8))
    # pots, mat, basket, drying racks
    pot(p, -0.3, 0.2, 4.2, 1.0, 1.9, CLAY)
    pot(p, -1.8, 0.2, 5.0, 0.7, 1.3, MUD, band=GOLD_D)
    bx(p, (-9.5, -4.5), (0.2, 0.32), (3.0, 6.2), RED, 0.03)
    bx(p, (-9.0, -5.0), (0.32, 0.36), (3.4, 3.8), GOLD, 0.02)
    bx(p, (-9.0, -5.0), (0.32, 0.36), (5.4, 5.8), LAPIS, 0.02)
    vcyl(p, -3.0, 0.2, 1.3, 7.0, 0.9, (204, 160, 70), 8, top_r=1.1)
    bx(p, (5.0, 8.0), (0.2, 1.2), (-0.9, 0.3), MUD_D, 0.05)
    bx(p, (5.0, 8.0), (1.2, 1.9), (-0.7, 0.3), LINEN, 0.04)


# ---- 18. Shaduf ------------------------------------------------------------------------------------------------------------
def build_Shaduf(p):
    bx(p, (-6.6, 7.1), (0, 0.6), (-3.5, 3.5), GRASS, 0.06)
    # irrigation channel and a bed with crops
    bx(p, (-6.0, -0.5), (0.5, 0.75), (1.4, 3.1), WATER, 0.03)
    for (x0, x1, z0, z1) in ((-6.4, 0.1, 0.9, 1.4), (-6.4, 0.1, 3.1, 3.5), (-6.4, -5.9, 1.4, 3.1), (-0.6, 0.1, 1.4, 3.1)):
        bx(p, (x0, x1), (0.45, 0.95), (z0, z1), STONE_D, 0.05)
    for k in range(5):
        bx(p, (2.2 + k * 0.95 - 0.35, 2.2 + k * 0.95 + 0.35), (0.6, 1.5), (1.4, 2.1), PALM, 0.05)
        bx(p, (2.2 + k * 0.95 - 0.35, 2.2 + k * 0.95 + 0.35), (0.6, 1.2), (-1.6, -0.9), PALM_D, 0.05)
    # two mud pillars and the pivot beam
    for z in (-1.5, 1.5):
        tbox(p, 0.6, z, 0.6, 6.4, 2.0, 1.2, 1.3, 1.0, MUD, 0.06)
    bx(p, (-0.2, 1.4), (5.9, 6.5), (-2.2, 2.2), WOOD, 0.04)
    # lever pole (high end carries a clay counterweight), rope and bucket on the low end
    bx(p, (-5.4, 6.6), (6.6, 7.2), (-0.4, 0.4), WOOD, 0.04, rot=(0, 0, 14))
    ball(p, (5.9, 7.0, 0), 1.0, MUD, subdiv=2)
    bx(p, (5.8, 6.0), (7.9, 8.2), (-0.1, 0.1), WOOD, 0.02)
    bx(p, (-5.0, -4.9), (3.9, 5.5), (-0.07, 0.07), WOOD, 0.02)
    vcyl(p, -4.95, 2.4, 3.9, 0, 0.8, WOOD, 8, top_r=0.95)
    vcyl(p, -4.95, 3.7, 3.9, 0, 0.78, WATER, 8)
    bx(p, (-4.4, 0.0), (0.5, 0.9), (-3.0, -2.2), WATER, 0.03)   # trough
    bx(p, (-4.8, 0.4), (0.5, 1.1), (-3.4, -3.0), STONE_D, 0.05)
# ---- 19. Barge -------------------------------------------------------------------------------------------------------------
def build_Barge(p):
    bx(p, (-13, 13), (0, 0.6), (-6, 6), WATER, 0.03)
    for k in range(6):
        bx(p, (-12 + k * 4.2, -9.6 + k * 4.2), (0.6, 0.66), (-5 + (k % 3) * 3.4, -4.5 + (k % 3) * 3.4), WATER_L, 0.02)
    # hull: tapered lower hull, gold gunwale, raised papyrus prow and stern
    tbox(p, 0, 0, 0.6, 3.0, 17, 3.6, 21, 5.0, GOLD_D, 0.03)
    bx(p, (-10.3, 10.3), (2.8, 3.2), (-2.8, 2.8), GOLD, 0.03)
    bx(p, (-9, 9), (3.0, 3.1), (-2.3, 2.3), WOOD, 0.05)
    for s in (-1, 1):
        for k in range(4):
            bx(p, (s * (10.2 + 0.45 * k) - 0.8 + 0.0, s * (10.2 + 0.45 * k) + 0.8), (3.0 + 0.95 * k, 4.0 + 0.95 * k), (-0.8, 0.8), GOLD, 0.02)
        ball(p, (s * 12.4, 6.3, 0), 0.95, RED, scale=(1, 1.1, 1), subdiv=1)
        bx(p, (s * 12.0 - 0.25, s * 12.0 + 0.25), (5.5, 6.1), (-0.35, 0.35), TURQ, 0.02)
        bx(p, (s * 9.6 - 0.2, s * 9.6 + 0.2), (3.0, 4.0), (-2.45, 2.45 + 0.1), LAPIS, 0.02)
    # rowing benches and oars
    for x in (-8, -5.6, 4.4, 6.8):
        bx(p, (x - 0.5, x + 0.5), (3.0, 3.6), (-2.2, 2.2), WOOD, 0.04)
        for s in (-1, 1):
            bar(p, (x, 3.4, s * 2.7), (x - 0.6, 0.9, s * 5.0), 0.28, WOOD, 0.02)
            bar(p, (x - 0.6, 0.9, s * 5.0), (x - 0.9, -0.8, s * 5.6), 0.55, LAPIS, 0.02)
    # cabin shrine
    bx(p, (-4.2, 2.2), (3.1, 6.1), (-1.8, 1.8), STONE_L, 0.04)
    bx(p, (-4.3, 2.3), (3.6, 4.0), (-1.9, 1.9), LAPIS, 0.02)
    bx(p, (-1.6, 0.8), (3.1, 5.3), (1.8, 1.95), BLACK, 0.02)
    for (x, z) in ((-4.2, 2.1), (2.2, 2.1), (-4.2, -2.1), (2.2, -2.1)):
        vcyl(p, x, 3.1, 6.4, z, 0.22, WOOD, 6)
    bx(p, (-5, 3), (6.2, 6.7), (-2.6, 2.6), RED, 0.03)
    bx(p, (-5, 3), (6.7, 6.9), (-2.6, -2.0), GOLD, 0.02)
    bx(p, (-5, 3), (6.7, 6.9), (2.0, 2.6), GOLD, 0.02)
    zcyl(p, -1, 7.2, -0.2, 0.2, 0.6, GOLD, 10)
    # steering oars at the stern (tilted)
    for s in (-1, 1):
        tcyl(p, 11.6, 0.4, 7.4, s * 3.6, 0.22, WOOD, -20, 6)
        bx(p, (12.6, 13.0), (0.6, 2.8), (s * 3.6 - 0.5, s * 3.6 + 0.5), LAPIS, 0.02, rot=(0, 0, -20))


# ---- 20. Sarcophagus -------------------------------------------------------------------------------------------------------
def brazier(p, x, z, y0=0.0):
    vcyl(p, x, y0, y0 + 1.6, z, 0.6, STONE_D, 8, top_r=0.8)
    vcyl(p, x, y0 + 1.6, y0 + 2.2, z, 0.9, GOLD, 8, top_r=1.1)
    bx(p, (x - 0.5, x + 0.5), (y0 + 2.2, y0 + 3.2), (z - 0.5, z + 0.5), RED, 0.03)
    bx(p, (x - 0.3, x + 0.3), (y0 + 3.2, y0 + 3.9), (z - 0.3, z + 0.3), GOLD, 0.02)


def build_Sarcophagus(p):
    bx(p, (-6, 6), (0, 1.2), (-4, 4), STONE_D, 0.05)
    bx(p, (-5.2, 5.2), (1.2, 1.6), (-3.2, 3.2), STONE, 0.04)
    # coffin: anthropoid lid, lying with the head toward -x
    bx(p, (-4.0, 4.4), (1.6, 3.4), (-1.5, 1.5), GOLD, 0.03)
    tbox(p, 4.6, 0, 1.6, 3.2, 1.2, 2.2, 1.0, 1.6, GOLD, 0.03)
    bx(p, (-4.0, 4.4), (3.4, 3.7), (-1.1, 1.1), GOLD_D, 0.03)
    ball(p, (-3.9, 3.6, 0), 1.0, GOLD, scale=(1.3, 1.3, 1.3), subdiv=2)
    bx(p, (-5.2, -2.6), (2.2, 4.6), (-1.3, 1.3), LAPIS, 0.03)      # headdress
    bx(p, (-5.4, -5.0), (2.6, 4.6), (-1.05, 1.05), GOLD, 0.02)       # face plate
    for s in (-1, 1):
        bx(p, (-5.5, -5.1), (3.6, 4.0), (s * 0.5 - 0.25, s * 0.5 + 0.25), BLACK, 0.02)
        bx(p, (-3.0, -1.2), (2.2, 3.9), (s * 1.3 - 0.1, s * 1.3 + 0.1), LAPIS, 0.02)
    for k in range(4):   # lapis bands across the lid
        bx(p, (-1.4 + k * 1.8, -0.8 + k * 1.8), (3.4, 3.8), (-1.2, 1.2), LAPIS if k % 2 == 0 else TURQ, 0.02)
    bx(p, (-1.6, 0.4), (3.8, 4.1), (-0.9, -0.1), LAPIS, 0.02, rot=(0, 25, 0))     # crook and flail crossed on the chest
    bx(p, (-1.6, 0.4), (3.8, 4.1), (0.1, 0.9), RED, 0.02, rot=(0, -25, 0))
    # pillars and canopy
    for (x, z) in ((-5, -3), (5, -3), (-5, 3), (5, 3)):
        bx(p, (x - 0.55, x + 0.55), (1.6, 2.1), (z - 0.55, z + 0.55), STONE_L, 0.03)
        vcyl(p, x, 2.1, 7.2, z, 0.45, STONE_L, 8)
        vcyl(p, x, 3.4, 3.7, z, 0.5, GOLD, 8)
        lotus_cap(p, x, 6.8, z, 0.5, 1.2, STONE_L, GOLD)
    bx(p, (-6, 6), (8.0, 8.8), (-4.2, 4.2), STONE, 0.04)
    bx(p, (-5.5, 5.5), (8.8, 8.9), (-3.7, 3.7), LAPIS, 0.02)
    for k in range(5):
        bx(p, (-4.2 + k * 2.1 - 0.2, -4.2 + k * 2.1 + 0.2), (8.8, 8.95), (-3.7, 3.7), GOLD, 0.02)
    brazier(p, -7.4, 4.0)
    brazier(p, 5.0, 4.1)


# ---- 21. Queens ------------------------------------------------------------------------------------------------------------
def little_pyramid(p, cx, cz, w, h_total, door=True):
    n = 3
    hh = (h_total - 0.9) / n
    for i in range(n):
        w0 = w - i * (w * 0.3)
        tbox(p, cx, cz, i * hh, (i + 1) * hh, w0, w0, w0 - w * 0.26, w0 - w * 0.26, STONE if i % 2 == 0 else STONE_L, 0.05)
    wtop = w - 2 * (w * 0.3) - w * 0.26
    pyr(p, cx, cz, h_total - 0.9, h_total, max(wtop, 1.0), max(wtop, 1.0), GOLD, 0.02)
    if door:
        bx(p, (cx - 0.9, cx + 0.9), (0, 1.7), (cz + w / 2 - 0.3, cz + w / 2), BLACK, 0.02)
        bx(p, (cx - 1.4, cx + 1.4), (0, 0.3), (cz + w / 2 - 0.6, cz + w / 2), STONE_D, 0.04)


def build_Queens(p):
    bx(p, (-13.5, 11.8), (0, 0.3), (-8, 8.2), SAND_D, 0.05)
    little_pyramid(p, -7, -2, 12, 9.9)
    little_pyramid(p, 7, -3, 9.6, 8.0)
    little_pyramid(p, 2, 4, 8.4, 7.2)
    # causeway linking the three, with a cornice
    bx(p, (-1.5, 1.5), (0.0, 0.6), (-6, 6), STONE_D, 0.04, rot=(0, 40, 0))
    bx(p, (-0.3, 0.3), (0.6, 0.7), (-5.4, 5.4), GOLD, 0.02, rot=(0, 40, 0))
    # offering chapels
    bx(p, (-12.5, -10.5), (0, 1.5), (-1, 1.5), STONE_L, 0.04)
    bx(p, (10, 11.6), (0, 1.3), (-1, 0.8), STONE_L, 0.04)
    glyph(p, 'ankh', -11.5, 0.8, 1.5, 1.0, LAPIS)
    # little obelisk
    tbox(p, -3.2, 7.4, 0, 3.4, 0.9, 0.9, 0.6, 0.6, GRANITE, 0.04)
    pyr(p, -3.2, 7.4, 3.4, 4.2, 0.6, 0.6, GOLD, 0.02)


# ---- 22. Pavilion ----------------------------------------------------------------------------------------------------------
def build_Pavilion(p):
    bx(p, (-7, 7), (0, 1.2), (-5.5, 5.5), STONE_D, 0.05)
    bx(p, (-6.3, 6.3), (1.2, 1.5), (-4.8, 4.8), STONE_L, 0.04)
    for k in range(5):
        bx(p, (-5 + k * 2.5 - 0.6, -5 + k * 2.5 + 0.6), (1.5, 1.52), (-4.5, 4.5), LAPIS if k % 2 == 0 else RED, 0.02)
    for (x, z) in ((-6, -4.4), (6, -4.4), (-6, 4.4), (6, 4.4)):
        vcyl(p, x, 1.5, 9.6, z, 0.45, GOLD, 8)
        lotus_cap(p, x, 9.0, z, 0.55, 1.2, GOLD_D, TURQ)
        bx(p, (x - 0.5, x + 0.5), (1.2, 1.7), (z - 0.5, z + 0.5), GOLD_D, 0.03)
    # roof: lapis slab, gold crown, striped valance
    bx(p, (-7, 7), (10.2, 11.0), (-5.6, 5.6), LAPIS, 0.03)
    bx(p, (-5.5, 5.5), (11.0, 11.8), (-4.3, 4.3), GOLD, 0.03)
    for k in range(7):
        bx(p, (-6.7 + k * 2.0 - 0.0, -5.7 + k * 2.0), (9.4, 10.2), (5.4, 5.7), RED if k % 2 == 0 else LINEN, 0.02)
    # back curtain and tied side curtains
    bx(p, (-6, 6), (1.5, 10.0), (-5.1, -4.9), RED, 0.03)
    for k in range(6):
        bx(p, (-5.4 + k * 2.0, -4.6 + k * 2.0), (1.5, 10.0), (-4.9, -4.8), GOLD if k % 2 == 0 else RED, 0.02)
    for s in (-1, 1):
        bx(p, (s * 6.3 - 0.15, s * 6.3 + 0.15), (3.0, 9.4), (-3.8, -1.6), LINEN, 0.03)
        bx(p, (s * 6.3 - 0.2, s * 6.3 + 0.2), (5.8, 6.2), (-4.0, -1.4), GOLD, 0.02)
    # throne
    bx(p, (-1.6, 1.6), (1.5, 4.0), (-3.9, -1.0), GOLD, 0.03)
    bx(p, (-1.4, 1.4), (4.0, 4.5), (-3.7, -1.2), LAPIS, 0.03)
    bx(p, (-1.6, 1.6), (4.0, 8.2), (-4.2, -3.6), GOLD, 0.03)
    bx(p, (-1.1, 1.1), (5.0, 7.4), (-3.7, -3.55), LAPIS, 0.02)
    bx(p, (-1.0, 1.0), (8.2, 8.9), (-4.1, -3.7), GOLD_D, 0.02)
    for s in (-1, 1):
        bx(p, (s * 1.6 - 0.2, s * 1.6 + 0.2), (4.0, 5.4), (-3.9, -1.0), GOLD_D, 0.03)
    bx(p, (-1.2, 1.2), (1.5, 2.1), (-0.4, 0.6), GOLD, 0.03)           # footstool
    # feather fans
    for s in (-1, 1):
        vcyl(p, s * 4.4, 1.5, 6.6, -2.0, 0.15, WOOD, 6)
        ball(p, (s * 4.4, 7.9, -2.0), 1.0, LINEN, scale=(1.1, 1.6, 0.35), subdiv=1)
        bx(p, (s * 4.4 - 0.12, s * 4.4 + 0.12), (6.6, 7.4), (-2.1, -1.9), GOLD, 0.02)
        ball(p, (s * 4.4, 7.9, -1.85), 0.5, TURQ, scale=(1, 1.4, 0.3), subdiv=1)
    # lamps beside the steps
    for s in (-1, 1):
        vcyl(p, s * 3.6, 1.5, 3.0, 4.2, 0.35, GOLD, 6, top_r=0.5)
        bx(p, (s * 3.6 - 0.45, s * 3.6 + 0.45), (3.0, 3.7), (3.75, 4.65), RED, 0.03)


# ---- 23. Treasure ----------------------------------------------------------------------------------------------------------
def chest(p, cx, cz, w, d, lid_back=True):
    bx(p, (cx - w / 2, cx + w / 2), (0.4, 2.0), (cz - d / 2, cz + d / 2), WOOD, 0.05)
    bx(p, (cx - w / 2 - 0.05, cx + w / 2 + 0.05), (0.4, 0.8), (cz - d / 2 - 0.05, cz + d / 2 + 0.05), GOLD_D, 0.03)
    for s in (-1, 1):
        bx(p, (cx + s * w * 0.32 - 0.2, cx + s * w * 0.32 + 0.2), (0.4, 2.05), (cz - d / 2 - 0.05, cz + d / 2 + 0.05), GOLD_D, 0.03)
    # open lid standing at the back
    bx(p, (cx - w / 2, cx + w / 2), (2.0, 4.2), (cz - d / 2 - 0.5, cz - d / 2 - 0.1), WOOD, 0.05, rot=(-12, 0, 0))
    bx(p, (cx - 0.3, cx + 0.3), (2.0, 4.2), (cz - d / 2 - 0.55, cz - d / 2 - 0.05), GOLD_D, 0.03, rot=(-12, 0, 0))
    # heap of gold
    ball(p, (cx, 2.0, cz), 1.0, GOLD, scale=(w * 0.5, 1.0, d * 0.5), subdiv=2)
    for (dx, dz, c) in ((-0.8, 0.2, RED), (0.9, -0.2, TURQ), (0.1, 0.5, LAPIS)):
        ball(p, (cx + dx, 2.9, cz + dz), 0.32, c, subdiv=1)


def build_Treasure(p):
    bx(p, (-7, 7), (0, 0.4), (-5, 5), STONE_D, 0.05)
    bx(p, (-6.4, 6.4), (0.4, 0.45), (-4.4, 4.4), SAND_D, 0.04)
    chest(p, -3.5, -1.5, 4.4, 3.0)
    chest(p, 3.4, 0.8, 4.0, 2.8)
    # big pile of coins with a stacked column of coins
    ball(p, (0, 1.0, 3), 1.0, GOLD, scale=(2.8, 1.0, 1.8), subdiv=2)
    for k in range(5):
        vcyl(p, -1.6 + 0.4 * (k % 2), 0.4 + 0.3 * k, 0.7 + 0.3 * k, 3.4, 0.7, GOLD if k % 2 == 0 else GOLD_D, 8, jit=0.02)
    bx(p, (-0.5, 0.5), (2.3, 3.2), (2.5, 3.5), RED, 0.03, rot=(0, 30, 0))
    bx(p, (-2.2, -1.4), (1.5, 2.2), (2.2, 3.0), TURQ, 0.03, rot=(0, 20, 20))
    # golden jars and an amphora
    pot(p, -6, 0.4, 2.6, 1.0, 3.4, GOLD, band=GOLD_D)
    pot(p, 6, 0.4, -2.8, 0.9, 2.6, GOLD, band=GOLD_D)
    # standing golden plate and crown on a stand
    vcyl(p, 0, 0.4, 3.2, -3.6, 0.2, GOLD_D, 6)
    zcyl(p, 0, 3.9, -3.9, -3.5, 0.9, GOLD, 12)
    zcyl(p, 0, 3.9, -3.5, -3.4, 0.55, RED, 8)
    # necklace on a jar
    for k in range(5):
        a = math.radians(-70 + k * 35)
        ball(p, (6 + 1.1 * math.sin(a), 2.0 + 0.5 * math.cos(a), -2.8 + 0.95), 0.2, TURQ if k % 2 else GOLD, subdiv=1)
    for k in range(4):
        ball(p, (-6.5 + k * 0.6, 0.6, 4.2 - k * 0.2), 0.3, (GOLD, RED, TURQ, LAPIS)[k], subdiv=1)


# ---- 24. Scales ------------------------------------------------------------------------------------------------------------
def build_Scales(p):
    bx(p, (-4.4, 4.4), (0, 1.4), (-3, 3), STONE_D, 0.05)
    bx(p, (-3.4, 3.4), (1.4, 1.8), (-2.2, 2.2), STONE, 0.04)
    # djed-like gold column and beam
    bx(p, (-0.7, 0.7), (1.8, 14.0), (-0.7, 0.7), GOLD, 0.03)
    for y in (4.0, 5.2, 6.4):
        bx(p, (-1.1, 1.1), (y, y + 0.5), (-1.1, 1.1), GOLD_D, 0.03)
    bx(p, (-7.2, 7.2), (14.0, 14.8), (-0.45, 0.45), GOLD, 0.03)
    ball(p, (0, 15.4, 0), 1.1, RED, subdiv=1)
    for s in (-1, 1):
        bx(p, (s * 6.9 - 0.3, s * 6.9 + 0.3), (13.9, 15.0), (-0.4, 0.4), GOLD_D, 0.03)
        # strings (three per pan) and the pan
        for dz in (-1.3, 1.3):
            bar(p, (s * 6.6, 13.9, 0), (s * 6.6 + (1.5 if dz else 0) * 0 + 0.0, 8.3, dz * 0.8), 0.14, GOLD, 0.02)
        bar(p, (s * 6.6, 13.9, 0), (s * 6.6 - s * 1.7, 8.4, 0), 0.14, GOLD, 0.02)
        bar(p, (s * 6.6, 13.9, 0), (s * 6.6 + s * 1.7, 8.4, 0), 0.14, GOLD, 0.02)
        vcyl(p, s * 6.6, 7.5, 8.0, 0, 2.2, GOLD, 12, top_r=2.2)
        vcyl(p, s * 6.6, 7.9, 8.1, 0, 2.3, GOLD_D, 12)
    ball(p, (-6.6, 9.1, 0), 1.0, RED, subdiv=2)                            # the heart
    bx(p, (-7.0, -6.2), (9.7, 10.3), (-0.2, 0.2), RED, 0.02)
    bx(p, (6.5, 6.7), (8.1, 10.4), (-0.12, 0.12), LINEN, 0.02)           # the feather of truth
    ball(p, (6.6, 9.6, 0), 0.7, LINEN, scale=(0.7, 1.9, 0.3), subdiv=1)
    # Anubis seated beside the base, reading the scale
    bx(p, (2.8, 4.4), (1.4, 3.4), (1.6, 3.4), BLACK, 0.03)
    bx(p, (2.9, 4.3), (3.4, 5.6), (1.8, 2.8), BLACK, 0.03)
    bx(p, (3.1, 4.1), (5.4, 6.4), (2.2, 4.1), BLACK, 0.03)
    for s in (-1, 1):
        bx(p, (3.6 + s * 0.35 - 0.12, 3.6 + s * 0.35 + 0.12), (6.4, 7.6), (2.3, 2.7), BLACK, 0.02)
    bx(p, (2.8, 4.4), (4.8, 5.2), (1.7, 2.9), GOLD, 0.02)
    bx(p, (3.1, 4.1), (1.4, 1.9), (3.4, 4.2), BLACK, 0.03)


# ---- 25. Mask --------------------------------------------------------------------------------------------------------------
def build_Mask(p):
    bx(p, (-8, 8), (0, 1.4), (-6, 6), STONE_D, 0.05)
    bx(p, (-6.2, 6.2), (1.4, 2.6), (-4.7, 4.7), STONE, 0.04)
    bx(p, (-5.5, 5.5), (2.6, 4.6), (-3.5, 3.5), STONE_L, 0.04)
    bx(p, (-5.6, 5.6), (4.0, 4.1), (3.5, 3.6), GOLD, 0.02)
    for k in range(5):
        bx(p, (-4.5 + k * 2.25 - 0.3, -4.5 + k * 2.25 + 0.3), (2.9, 3.7), (4.7, 4.8), LAPIS, 0.02)
    # golden face
    ball(p, (0, 10.4, 0), 1.0, GOLD, scale=(3.8, 5.6, 2.8), subdiv=2, jit=0.025)
    # striped nemes: lappets either side, top block
    for s in (-1, 1):
        for k in range(7):
            bx(p, (s * 4.6 - 1.6, s * 4.6 + 1.6), (4.4 + k * 1.75, 6.15 + k * 1.75), (-1.9, 1.6), LAPIS if k % 2 == 0 else GOLD, 0.02)
    for k in range(4):
        bx(p, (-4.8, 4.8), (15.0 + k * 0.7, 15.7 + k * 0.7), (-1.9 + 0.2 * k, 2.0 - 0.3 * k), LAPIS if k % 2 == 0 else GOLD, 0.02)
    # features sit on the ellipsoid surface (z = 2.8 * sqrt(1 - ...))
    def ez(x, y):
        v = 1 - (x / 3.8) ** 2 - ((y - 10.4) / 5.6) ** 2
        return 2.8 * math.sqrt(max(v, 0.0))
    for s in (-1, 1):
        zc = ez(s * 1.5, 11.6)
        bx(p, (s * 1.5 - 1.0, s * 1.5 + 1.0), (11.2, 12.0), (zc - 0.1, zc + 0.35), LINEN, 0.02)           # eye white
        bx(p, (s * 1.5 - 0.35, s * 1.5 + 0.35), (11.3, 11.9), (zc + 0.3, zc + 0.5), BLACK, 0.02)          # pupil
        bx(p, (s * 1.5 - 1.3, s * 1.5 + 1.3), (11.9, 12.3), (zc - 0.1, zc + 0.45), BLACK, 0.02)           # kohl line
        zb = ez(s * 1.6, 12.9)
        bx(p, (s * 1.6 - 1.3, s * 1.6 + 1.3), (12.5, 13.0), (zb - 0.1, zb + 0.4), LAPIS, 0.02)            # brows
    zn = ez(0, 9.6)
    bx(p, (-0.45, 0.45), (8.4, 11.6), (zn - 0.2, zn + 0.9), GOLD_D, 0.03)                                  # nose
    bx(p, (-0.9, 0.9), (8.2, 8.9), (zn - 0.2, zn + 0.5), GOLD_D, 0.03)
    zl = ez(0, 7.6)
    bx(p, (-1.3, 1.3), (7.3, 7.9), (zl - 0.1, zl + 0.45), RED, 0.02)                                       # lips
    bx(p, (-0.85, 0.85), (6.4, 7.2), (ez(0, 6.5) - 0.1, ez(0, 6.5) + 0.35), GOLD, 0.02)
    # braided beard curving forward
    for k in range(4):
        bx(p, (-0.55, 0.55), (3.6 + k * 0.7, 4.3 + k * 0.7), (ez(0, 6.0) - 0.1 + k * 0.1, ez(0, 6.0) + 0.45 + k * 0.1), LAPIS if k % 2 == 0 else GOLD, 0.02)
    # cobra and vulture on the brow
    bx(p, (-0.4, 0.4), (14.0, 17.4), (ez(0, 14.0) - 0.1, ez(0, 14.0) + 0.7), GOLD, 0.02)
    bx(p, (-0.65, 0.65), (17.0, 18.2), (ez(0, 14.0), ez(0, 14.0) + 0.9), RED, 0.02)
    bx(p, (-0.3, 0.3), (18.2, 19.1), (ez(0, 14.0) + 0.1, ez(0, 14.0) + 0.7), GOLD, 0.02)
    bx(p, (-1.6, -0.4), (14.9, 15.7), (ez(-1, 14.6) + 0.0, ez(-1, 14.6) + 0.7), TURQ, 0.02)
    bx(p, (0.4, 1.6), (14.9, 15.7), (ez(1, 14.6) + 0.0, ez(1, 14.6) + 0.7), TURQ, 0.02)


# ---- fit, export, previews -------------------------------------------------------------------------------------------------
BUILDERS = [(n[6:], f) for n, f in list(globals().items()) if n.startswith("build_") and callable(f)]


def roblox_box(pieces):
    """Union of the pieces' size boxes (rotated, axis aligned) in the stage frame."""
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for pc in pieces:
        rx, ry, rz = map(math.radians, pc.get("Rotation") or (0, 0, 0))
        M = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        for sx in (-.5, .5):
            for sy in (-.5, .5):
                for sz in (-.5, .5):
                    v = M @ Vector((sx * pc["Size"][0], sy * pc["Size"][1], sz * pc["Size"][2]))
                    for i in range(3):
                        w = v[i] + pc["Offset"][i]
                        lo[i] = min(lo[i], w)
                        hi[i] = max(hi[i], w)
    return lo, hi


def true_bounds(objs):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            s = (w.x, w.z, w.y)
            for i in range(3):
                lo[i] = min(lo[i], s[i])
                hi[i] = max(hi[i], s[i])
    return lo, hi


def fit(part, box):
    """Bakes every object into world space and stretches the whole part (stage axes) to the target box."""
    tlo, thi = box
    lo, hi = true_bounds(part.objs)
    sc = [(thi[i] - tlo[i]) / max(hi[i] - lo[i], 1e-6) for i in range(3)]
    cc = [(lo[i] + hi[i]) / 2 for i in range(3)]
    tc = [(tlo[i] + thi[i]) / 2 for i in range(3)]
    B = lambda v: Vector((v[0], v[2], v[1]))
    F = Matrix.Translation(B(tc)) @ Matrix.Diagonal(Vector((sc[0], sc[2], sc[1], 1.0))) @ Matrix.Translation(-B(cc))
    for o in part.objs:
        o.data.transform(F @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.update()
    print("FIT %-11s scale x%.3f y%.3f z%.3f" % (part.id, sc[0], sc[1], sc[2]))


def drop_ground_faces(part, y_max=0.02):
    for o in part.objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bad = [f for f in bm.faces if f.normal.z < -0.99 and f.calc_center_median().z < y_max]
        if bad:
            bmesh.ops.delete(bm, geom=bad, context='FACES')
            bm.to_mesh(o.data)
        bm.free()


def shiba_spot(part_id, bp, lo, hi):
    if part_id == "Ground":
        return bp
    return {"Shiba": {"Position": [hi[0] + 5.5, (lo[2] + hi[2]) / 2], "Facing": 180}}


def stack_images(out, a, b, dst):
    ia = bpy.data.images.load(os.path.join(out, a))
    ib = bpy.data.images.load(os.path.join(out, b))
    w = max(ia.size[0], ib.size[0])
    h = ia.size[1] + ib.size[1]
    import numpy as np
    pa = np.array(ia.pixels[:], dtype=np.float32).reshape(ia.size[1], ia.size[0], 4)
    pb = np.array(ib.pixels[:], dtype=np.float32).reshape(ib.size[1], ib.size[0], 4)
    canvas = np.ones((h, w, 4), dtype=np.float32)
    canvas[:ib.size[1], :ib.size[0]] = pb
    canvas[ib.size[1]:, :ia.size[0]] = pa
    im = bpy.data.images.new("stack", w, h)
    im.pixels.foreach_set(canvas.ravel())
    im.filepath_raw = os.path.join(out, dst)
    im.file_format = 'PNG'
    im.save()


def main():
    dk.start(OUT)
    ids = [pp["Id"] for pp in BP["Parts"]]
    assert ONLY or ids == [pid for pid, _ in BUILDERS], "builders and blueprint parts differ: %s vs %s" % (ids, [b[0] for b in BUILDERS])
    stats = []
    allm = []
    for pid, fn in BUILDERS:
        if ONLY and pid not in ONLY:
            continue
        part = dk.Part(pid)
        fn(part)
        box = roblox_box(dk.blueprint_part(BP, pid)["Pieces"])
        drop_ground_faces(part)
        fit(part, box)
        meshes = dk.finish(part, KEY)
        tris = sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)
        stats.append((pid, len(meshes), tris))
        lo, hi = true_bounds(meshes)
        dk.preview(part, f"preview_{pid}.png", with_shiba=shiba_spot(pid, BP, lo, hi), azimuth=150, elevation=26)
        allm += meshes
        dk.hide(meshes)
    if not ONLY:
        dk.hide(allm, False)
        dk.preview(allm, "stage_34.png", with_shiba=BP, azimuth=150, elevation=32, size=(1600, 1000))
        dk.preview(allm, "stage_top.png", with_shiba=BP, azimuth=0, top=True, size=(1600, 1000))
        stack_images(OUT, "stage_34.png", "stage_top.png", "stage_PharaohPyramid.png")
        for f in ("stage_34.png", "stage_top.png"):
            os.remove(os.path.join(OUT, f))
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
