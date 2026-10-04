"""Final low-poly decor models for the theme NinjaDojo (20 parts around the ninth Shiba, bay 9).

Usage: blender --background --factory-startup --python build_NinjaDojo.py -- <outdir>
Writes Decor_NinjaDojo_<PartId>.fbx, preview_<PartId>.png and stage_NinjaDojo*.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height).
Env ND_ONLY=Hall,Gate builds only those parts (no stage render) for quick iteration.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "NinjaDojo"))
KEY = "NinjaDojo"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_NinjaDojo.json"))
ONLY = set(os.environ.get("ND_ONLY", "").split(",")) - {""}
R = random.Random(9)
pi = math.pi

# ---- palette (shared by all 20 parts) --------------------------------------------------------------------------------
WD = (70, 48, 40)        # dark timber
WM = (122, 84, 54)       # mid wood
WL = (166, 120, 76)      # light wood
RED = (192, 40, 46)
DRED = (140, 28, 34)
BLK = (32, 32, 40)
DGR = (54, 58, 74)
PAP = (240, 232, 205)    # paper / plaster
PAPD = (214, 204, 172)
ROOF = (58, 66, 94)      # slate roof
ROOFL = (74, 82, 110)
STN = (140, 140, 150)
STND = (98, 100, 112)
STNL = (178, 178, 186)
SAND = (224, 210, 172)
SANDD = (198, 182, 144)
GLD = (255, 205, 70)
DGLD = (206, 150, 40)
STL = (192, 197, 207)
STRAW = (214, 182, 110)
STRAWD = (176, 146, 84)
PINK = (255, 170, 200)
PINKL = (255, 188, 212)
PINKD = (236, 132, 172)
GRN = (66, 126, 68)
GRNL = (100, 162, 86)
GRND = (46, 96, 56)
BAM = (112, 172, 82)
BAMD = (78, 132, 60)
WAT = (66, 138, 190)
WATL = (118, 184, 222)
ORG = (240, 130, 50)
WHT = (245, 245, 245)
WARM = (255, 214, 140)
GRAV = (214, 204, 178)
GRAVD = (188, 177, 150)


# ---- helpers -------------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.05, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def bc(p, cx, y0, cz, sx, sy, sz, col, jit=0.05, rot=(0, 0, 0)):
    """Box standing on y0 centred on (cx, cz) like the blueprint pieces."""
    return dk.box(p, (cx, y0 + sy / 2, cz), (sx, sy, sz), col, rot=rot, jitter=jit)


def vc(p, cx, y0, y1, cz, r, col, verts=8, top_r=None, jit=0.05):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def zc(p, cx, cy, z0, z1, r, col, verts=12, jit=0.04):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit)


def xc(p, x0, x1, cy, cz, r, col, verts=8, jit=0.05):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def sph(p, c, r, col, scale=(1, 1, 1), sub=1, jit=0.06):
    return dk.ball(p, c, r, col, scale=scale, subdiv=sub, jitter=jit)


def cone(p, cx, y0, cz, r, h, col, verts=6, jit=0.05):
    return dk.cone(p, (cx, y0, cz), r, h, col, verts=verts, jitter=jit)


def beam(p, a, b, w, h, col, up=None, jit=0.04, caps=True):
    """Rectangular bar from point a to point b (stage axes), w x h cross-section; caps=False leaves the two ends open."""
    a, b = Vector(a), Vector(b)
    d = b - a
    dn = d.normalized()
    if up is None:
        up = Vector((0, 1, 0)) if abs(dn.y) < 0.9 else Vector((0, 0, 1))
    up = Vector(up)
    s = dn.cross(up).normalized()
    u = s.cross(dn).normalized()
    pts = []
    for t in (a, b):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = t + s * (w / 2 * sx) + u * (h / 2 * sy)
            pts.append((q.x, q.y, q.z))
    faces = [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    if caps:
        faces += [(0, 1, 2, 3), (7, 6, 5, 4)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def extrude(p, pts, z0, z1, col, jit=0.03):
    """Polygon in the x-y plane (stage) extruded along z (readable from +z)."""
    n = len(pts)
    P = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return dk.poly(p, (0, 0, 0), P, faces, col, jit)


def flat(p, pts, y, col, jit=0.05):
    """Flat polygon facing up at height y; pts = [(x, z)] (any winding)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    vs = [bm.verts.new((x, z, y)) for x, z in pts]
    bm.faces.new(vs)
    return dk._object(p, "Flat", bm, Vector((0, 0, 0)), (0, 0, 0), col, jit)


def rect(p, x0, x1, z0, z1, y, col, jit=0.05):
    return flat(p, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y, col, jit)


def ngon_pts(cx, cz, r, n, a0=0.0, sx=1.0, sz=1.0):
    return [(cx + r * sx * math.cos(a0 + 2 * pi * i / n), cz + r * sz * math.sin(a0 + 2 * pi * i / n)) for i in range(n)]


def stripline(p, pts, width, y, col, jit=0.04, joints=True):
    """Flat strip along a polyline (x, z) with round-ish joints."""
    for i in range(len(pts) - 1):
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        nx, nz = -dz / ln * width / 2, dx / ln * width / 2
        flat(p, [(x0 + nx, z0 + nz), (x1 + nx, z1 + nz), (x1 - nx, z1 - nz), (x0 - nx, z0 - nz)], y, col, jit)
    if joints:
        for (x, z) in pts[1:-1]:
            flat(p, ngon_pts(x, z, width / 2, 10), y, col, jit)


def frust(p, cx, cz, y0, y1, w0, d0, w1, d1, col, lift=0.0, jit=0.07, soffit=None):
    """Hip roof tier: base w0 x d0 at y0 (corners lifted by `lift`), top w1 x d1 at y1. Returns the objects."""
    a, b, c, d = w0 / 2, d0 / 2, w1 / 2, d1 / 2
    pts = [(-a, y0 + lift, -b), (a, y0 + lift, -b), (a, y0 + lift, b), (-a, y0 + lift, b),      # 0-3 corners
           (0, y0, -b), (a, y0, 0), (0, y0, b), (-a, y0, 0),                                       # 4-7 edge mids
           (-c, y1, -d), (c, y1, -d), (c, y1, d), (-c, y1, d),                                     # 8-11 top corners
           (0, y1, -d), (c, y1, 0), (0, y1, d), (-c, y1, 0),                                       # 12-15 top mids
           (0, y1, 0), (0, y0 + 0.001, 0)]                                                          # 16 top centre, 17 bottom centre
    faces = []
    cor = [0, 1, 2, 3]
    mid = [4, 5, 6, 7]
    top = [8, 9, 10, 11]
    tmid = [12, 13, 14, 15]
    for k in range(4):
        n = (k + 1) % 4
        faces.append((cor[k], mid[k], tmid[k], top[k]))
        faces.append((mid[k], cor[n], top[n], tmid[k]))
    faces += [(8, 12, 16, 15), (12, 9, 13, 16), (16, 13, 10, 14), (15, 16, 14, 11)]
    faces += [(0, 4, 17, 7), (4, 1, 5, 17), (17, 5, 2, 6), (7, 17, 6, 3)]
    return [dk.poly(p, (cx, 0, cz), pts, faces, col, jit)]


def eave_trim(p, cx, cz, y0, w0, d0, lift, col, t=0.34, h=0.34):
    """Bars along the lower edge of a roof tier (corner - mid - corner on every side). Returns objects."""
    a, b = (w0 - t) / 2, (d0 - t) / 2
    c = [(-a, y0 + lift, -b), (a, y0 + lift, -b), (a, y0 + lift, b), (-a, y0 + lift, b)]
    m = [(0, y0, -b), (a, y0, 0), (0, y0, b), (-a, y0, 0)]
    out = []
    for k in range(4):
        n = (k + 1) % 4
        for q0, q1 in ((c[k], m[k]), (m[k], c[n])):
            out.append(beam(p, (cx + q0[0], q0[1] + h / 2, cz + q0[2]), (cx + q1[0], q1[1] + h / 2, cz + q1[2]), t, h, col, jit=0.03,
                            up=(0, 1, 0), caps=False))
    return out


def shade3(c, f):
    return tuple(int(v * f) for v in c)


def grid(a, b, n):
    return [a + (b - a) * i / n for i in range(n + 1)]


def tiled_block(p, x0, x1, y0, y1, z0, z1, xs, zs, colfn, sidecol, jit=0.05):
    """Slab with a tiled top: open box for the sides plus quads for the tiles (xs/zs = grid breakpoints)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, z1 - z0, y1 - y0), verts=bm.verts)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    dk._object(p, "Side", bm, S((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (0, 0, 0), sidecol, jit)
    groups = {}
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            groups.setdefault(colfn(i, j), []).append((xs[i], xs[i + 1], zs[j], zs[j + 1]))
    for col, quads in groups.items():
        bm = bmesh.new()
        for (a, b, c, d) in quads:
            v = [bm.verts.new((a, c, y1)), bm.verts.new((b, c, y1)), bm.verts.new((b, d, y1)), bm.verts.new((a, d, y1))]
            bm.faces.new(v)
        bm.normal_update()
        dk._object(p, "Tiles", bm, Vector((0, 0, 0)), (0, 0, 0), col, 0.07)


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.05):
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def letter(p, ch, x0, y0, z0, z1, w, h, t, col):
    """Block letter in the x-y plane (readable from +z), box strokes."""
    zm, d = (z0 + z1) / 2, z1 - z0

    def r(a, b, c, e):
        bx(p, (x0 + a, x0 + c), (y0 + b, y0 + e), (z0, z1), col, 0.04)

    def dg(a, b, c, e):
        diag(p, x0 + a, y0 + b, zm, x0 + c, y0 + e, t, d, col, 0.04)
    if ch == 'B':
        r(0, 0, t, h); r(0, h - t, w - t * 0.6, h); r(0, h / 2 - t / 2, w - t * 0.3, h / 2 + t / 2); r(0, 0, w - t * 0.6, t)
        r(w - t, h / 2, w, h - t * 0.5); r(w - t, t * 0.5, w, h / 2)
    elif ch == 'O':
        r(0, 0, t, h); r(w - t, 0, w, h); r(t, h - t, w - t, h); r(t, 0, w - t, t)
    elif ch == 'N':
        r(0, 0, t, h); r(w - t, 0, w, h); dg(t * 0.5, h - t * 0.5, w - t * 0.5, t * 0.5)
    elif ch == 'K':
        r(0, 0, t, h); dg(t, h / 2, w - t * 0.3, h - t * 0.4); dg(t, h / 2, w - t * 0.3, t * 0.4)


def star4(p, cx, cy, z0, z1, R_, col, rot_deg=0, inner=0.3, jit=0.03):
    pts = []
    for k in range(8):
        a = math.radians(rot_deg) + k * pi / 4
        rr = R_ if k % 2 == 0 else R_ * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return extrude(p, pts, z0, z1, col, jit)


# ============================================================================================================================
# 1. Floor
# ============================================================================================================================
PATH = [(0, 65), (0, 48), (-52, 34), (40, 16), (-44, -6), (36, -18), (0, -48), (0, -65)]


def build_Floor(p):
    B1, B2 = (62, 72, 74), (54, 64, 68)
    tiled_block(p, -88, 88, 0, 0.3, -60, 60, grid(-88, 88, 11), grid(-60, 60, 8), lambda i, j: B1 if (i + j) % 2 == 0 else B2,
                shade3(B1, 0.8))
    # raked gravel fields
    bx(p, (-75, 75), (0.3, 0.4), (5, 55), GRAV, 0.04)
    bx(p, (-83, -7), (0.3, 0.4), (-56, -4), GRAV, 0.04)
    for z in range(8, 54, 3):
        rect(p, -74, 74, z, z + 0.45, 0.41, GRAVD, 0.03)
    for z in range(-54, -5, 3):
        rect(p, -82, -8, z, z + 0.45, 0.41, GRAVD, 0.03)
    # wooden deck under the dojo and under the tea house (planks along x)
    tiled_block(p, 43, 79, 0.3, 0.6, -54, -18, [43, 79], grid(-54, -18, 24), lambda i, j: WL if j % 2 else WM, shade3(WM, 0.7))
    tiled_block(p, -88, -68, 0.3, 0.6, 42, 58, [-88, -68], grid(42, 58, 10), lambda i, j: WL if j % 2 else WM, shade3(WM, 0.7))
    # entrance flagstones
    tiled_block(p, -10, 10, 0.3, 0.5, 48, 64, grid(-10, 10, 4), grid(48, 64, 4), lambda i, j: STNL if (i + j) % 2 == 0 else STN,
                shade3(STN, 0.8))
    # moss patches
    bx(p, (-88, -80), (0.3, 0.4), (-60, -40), GRN, 0.06)
    bx(p, (81, 91), (0.3, 0.4), (-64, -36), GRN, 0.06)
    for (x, z) in ((-84, -45), (-85, -55), (86, -45), (84, -58), (88, -40)):
        flat(p, ngon_pts(x, z, 1.6, 7), 0.43, GRNL, 0.1)
    # the winding walkway: dark border, light pavers, cross stripes
    PD = [(0, 60)] + PATH[1:-1] + [(0, -60)]
    stripline(p, PD, 7.4, 0.44, (70, 74, 88), 0.03)
    stripline(p, PD, 6.0, 0.46, (128, 132, 148), 0.05)
    for i in range(len(PD) - 1):
        (x0, z0), (x1, z1) = PD[i], PD[i + 1]
        ln = math.hypot(x1 - x0, z1 - z0)
        ux, uz = (x1 - x0) / ln, (z1 - z0) / ln
        nx, nz = -uz * 3.0, ux * 3.0
        t = 2.0
        while t < ln - 1.0:
            cx, cz = x0 + ux * t, z0 + uz * t
            flat(p, [(cx - ux * 0.1 + nx, cz - uz * 0.1 + nz), (cx + ux * 0.1 + nx, cz + uz * 0.1 + nz),
                     (cx + ux * 0.1 - nx, cz + uz * 0.1 - nz), (cx - ux * 0.1 - nx, cz - uz * 0.1 - nz)], 0.47, (104, 108, 124), 0.04)
            t += 3.4
    # round stepping stones scattered in the gravel
    for (x, z) in ((-60, 12), (-28, 24), (20, 40), (-56, -40), (-20, -50), (20, -34), (66, 22), (-30, -22)):
        flat(p, ngon_pts(x, z, 1.5, 7, 0.4), 0.43, STNL, 0.08)
        flat(p, ngon_pts(x, z, 0.9, 7, 0.4), 0.435, STN, 0.05)


# ============================================================================================================================
# 2. Hall (pagoda dojo)
# ============================================================================================================================
def build_Hall(p):
    cx, cz = 61, -36
    roofs = []
    # stone plinth strips under the walls
    bx(p, (45.8, 76.2), (0, 1.3), (-51.2, -49.6), STND, 0.05)
    bx(p, (45.8, 47.4), (0, 1.3), (-51.2, -20.8), STND, 0.05)
    bx(p, (74.6, 76.2), (0, 1.3), (-51.2, -20.8), STND, 0.05)
    # walls
    bx(p, (46, 76), (1.3, 10), (-51, -49.8), WD, 0.06)
    bx(p, (46, 47.2), (1.3, 10), (-51, -21), WD, 0.06)
    bx(p, (74.8, 76), (1.3, 10), (-51, -21), WD, 0.06)
    # back wall inside: battens and a big scroll with a red seal
    for x in (52, 61, 70):
        bx(p, (x - 0.2, x + 0.2), (1.3, 10), (-49.8, -49.62), WM, 0.05)
    bx(p, (54, 68), (3.6, 8.6), (-49.62, -49.48), PAP, 0.03)
    bx(p, (53.6, 54.2), (3.4, 8.8), (-49.62, -49.4), WD, 0.03)
    bx(p, (67.8, 68.4), (3.4, 8.8), (-49.62, -49.4), WD, 0.03)
    bx(p, (58.5, 63.5), (5.4, 6.8), (-49.48, -49.4), BLK, 0.03)
    bx(p, (60.4, 61.6), (4.0, 5.0), (-49.48, -49.38), RED, 0.03)
    # shoji windows on both side walls (paper with a dark frame)
    for out, xf in ((-1, 46.0), (1, 76.0)):
        for zc_ in (-43, -29):
            bx(p, sorted((xf, xf + out * 0.1)), (4.2, 8), (zc_ - 3, zc_ + 3), PAP, 0.03)
            for dz in (-3, 3):
                bx(p, sorted((xf, xf + out * 0.22)), (4.0, 8.2), (zc_ + dz - 0.18, zc_ + dz + 0.18), WD, 0.03)
            for yy in (4.0, 7.8):
                bx(p, sorted((xf, xf + out * 0.22)), (yy, yy + 0.2), (zc_ - 3, zc_ + 3), WD, 0.03)
    # pillars: red with stone bases and gold caps in front, plain at the back
    for (x, z) in ((47.2, -21.8), (74.8, -21.8), (54, -21.8), (68, -21.8)):
        bx(p, (x - 1.1, x + 1.1), (0, 0.6), (z - 1.1, z + 1.1), STN, 0.05)
        vc(p, x, 0.6, 9.6, z, 0.8, RED, 6, 0.74)
        bx(p, (x - 0.95, x + 0.95), (9.6, 10.0), (z - 0.95, z + 0.95), GLD, 0.03)
    for x in (47.2, 74.8):
        vc(p, x, 0, 10, -50.2, 0.8, RED, 6, 0.74)
    # lintel, hanging red lanterns
    bx(p, (46, 76), (7.9, 9.1), (-23.1, -21.7), RED, 0.04)
    for x in (58, 64):
        sph(p, (x, 6.9, -22.4), 0.7, RED, scale=(1, 1.3, 1), sub=1, jit=0.05)
    # stone steps
    bx(p, (54, 68), (0, 0.3), (-20.5, -17.9), STN, 0.05)
    bx(p, (54.8, 67.2), (0.3, 0.5), (-20.5, -19.2), STNL, 0.05)
    # ---- tier A: roof + plaster storey with the BONK sign
    roofs += frust(p, cx, cz, 9.2, 11.4, 38, 38, 25, 25, ROOF, lift=0.9)
    roofs += eave_trim(p, cx, cz, 9.2, 38, 38, 0.9, DGLD)
    bx(p, (48.5, 73.5), (11.4, 14.2), (-48.5, -23.5), PAP, 0.03)
    for x in (48.5, 73.5):
        bx(p, (x - 0.3, x + 0.3), (11.4, 14.2), (-23.6, -23.4), WD, 0.03)
    bx(p, (48.5, 73.5), (11.4, 11.7), (-23.65, -23.3), WD, 0.03)
    bx(p, (48.5, 73.5), (13.9, 14.2), (-23.65, -23.3), WD, 0.03)
    bx(p, (54.6, 67.4), (11.7, 13.9), (-23.5, -23.2), BLK, 0.03)       # sign board
    bx(p, (54.6, 67.4), (13.55, 13.9), (-23.5, -23.1), GLD, 0.03)
    bx(p, (54.6, 67.4), (11.7, 12.05), (-23.5, -23.1), GLD, 0.03)
    for i, ch in enumerate("BONK"):
        letter(p, ch, 55.4 + i * 3.0, 12.1, -23.2, -22.95, 2.4, 1.5, 0.5, GLD)
    for (x0, x1) in ((49.3, 54.0), (68.0, 72.7)):
        bx(p, (x0, x1), (12.0, 13.6), (-23.6, -23.45), PAPD, 0.03)
        bx(p, ((x0 + x1) / 2 - 0.12, (x0 + x1) / 2 + 0.12), (11.9, 13.7), (-23.65, -23.45), WD, 0.03)
    # ---- tier B
    roofs += frust(p, cx, cz, 14.2, 16.6, 30, 30, 17, 17, ROOF, lift=0.8)
    roofs += eave_trim(p, cx, cz, 14.2, 30, 30, 0.8, DGLD)
    bx(p, (52.5, 69.5), (16.6, 17.6), (-44.5, -27.5), PAP, 0.03)
    for x in (53.5, 68.5):
        bx(p, (x - 0.3, x + 0.3), (16.6, 17.6), (-27.6, -27.4), WD, 0.03)
    bx(p, (57, 65), (16.8, 17.4), (-27.55, -27.3), BLK, 0.03)
    # ---- tier C and the golden finial
    roofs += frust(p, cx, cz, 17.6, 19.6, 21, 21, 5, 5, ROOF, lift=0.7)
    for sx in (-1, 1):
        for sz in (-1, 1):
            roofs.append(cone(p, cx + sx * (19 - 0.6), 9.2 + 0.9, cz + sz * (19 - 0.6), 0.4, 1.3, GLD, 6))
    roofs.append(vc(p, cx, 19.6, 22.0, cz, 0.28, GLD, 6))
    for yy in (20.3, 21.0, 21.7):
        roofs.append(vc(p, cx, yy, yy + 0.22, cz, 0.62, DGLD, 6))
    roofs.append(sph(p, (cx, 22.0, cz), 0.9, GLD, sub=1, jit=0.03))
    return {"Roof": roofs}


# ============================================================================================================================
# 3. Gate (torii across the walkway)
# ============================================================================================================================
def build_Gate(p):
    Z = 56
    for sx in (-8, 8):
        vc(p, sx, 0, 0.9, Z, 1.5, STN, 8, 1.4)
        vc(p, sx, 0.9, 11.0, Z, 0.95, RED, 12, 0.8)
        vc(p, sx, 0.9, 2.1, Z, 1.05, BLK, 12)
        vc(p, sx, 8.0, 8.35, Z, 1.0, GLD, 12)
        vc(p, sx, 10.1, 10.4, Z, 0.9, GLD, 12)
    # lower tie beam (nuki) pokes through the pillars
    bx(p, (-9.5, 9.5), (8.2, 9.1), (Z - 0.6, Z + 0.6), RED, 0.04)
    # central strut, plaque and shimaki
    bx(p, (-0.5, 0.5), (9.1, 11.2), (Z - 0.5, Z + 0.5), RED, 0.04)
    bx(p, (-1.9, 1.9), (9.3, 11.1), (Z + 0.6, Z + 1.05), BLK, 0.03)
    bx(p, (-1.6, 1.6), (9.5, 10.9), (Z + 1.05, Z + 1.07), GLD, 0.03)
    zc(p, 0, 10.2, Z + 1.07, Z + 1.12, 0.55, RED, 12, 0.02)
    bx(p, (-10.5, 10.5), (10.5, 11.2), (Z - 1.1, Z + 1.1), RED, 0.04)
    # black kasagi: flat middle, upswept ends
    bx(p, (-10, 10), (11.2, 12.2), (Z - 1.4, Z + 1.4), BLK, 0.04)
    for s in (-1, 1):
        beam(p, (s * 10, 11.7, Z), (s * 13.5, 12.05, Z), 2.8, 0.9, BLK, up=(0, 1, 0))
        bx(p, sorted((s * 13.3, s * 13.5)), (11.7, 12.5), (Z - 1.4, Z + 1.4), BLK, 0.03)
        bx(p, sorted((s * 12.9, s * 13.5)), (12.35, 12.5), (Z - 1.4, Z + 1.4), GLD, 0.03)


# ============================================================================================================================
# 4. Dummies
# ============================================================================================================================
def straw_dummy(p, x, z):
    vc(p, x, 0.3, 5.6, z, 0.42, WD, 8)
    bx(p, (x - 1.3, x + 1.3), (0.3, 0.8), (z - 1.3, z + 1.3), WM, 0.05)
    vc(p, x, 1.2, 4.4, z, 1.1, STRAW, 10, 1.0, jit=0.1)
    for yy in (1.9, 3.7):
        vc(p, x, yy, yy + 0.3, z, 1.2, RED, 10, jit=0.04)
    zc(p, x, 3.0, z + 1.0, z + 1.12, 0.65, RED, 10, 0.03)
    zc(p, x, 3.0, z + 1.12, z + 1.16, 0.3, WHT, 10, 0.03)
    bx(p, (x - 2.6, x + 2.6), (3.4, 4.0), (z - 0.4, z + 0.4), WM, 0.05)
    for sx in (-2.3, 2.3):
        bx(p, (x + sx - 0.45, x + sx + 0.45), (3.1, 4.3), (z - 0.5, z + 0.5), STRAWD, 0.1)
    sph(p, (x, 6.6, z), 0.95, STRAW, sub=1, jit=0.08)
    vc(p, x, 6.1, 6.7, z, 1.0, RED, 10, jit=0.03)
    bx(p, (x - 0.5, x - 0.2), (6.9, 7.1), (z + 0.85, z + 0.97), BLK, 0.02)
    bx(p, (x + 0.2, x + 0.5), (6.9, 7.1), (z + 0.85, z + 0.97), BLK, 0.02)


def build_Dummies(p):
    bx(p, (-86, -62), (0, 0.3), (18, 26), SAND, 0.04)
    for z in (19, 20.5, 22, 23.5, 25):
        rect(p, -85.5, -62.5, z, z + 0.35, 0.31, SANDD, 0.03)
    for x in (-82, -74, -66):
        straw_dummy(p, x, 22)
    # two bokken stuck in the sand
    for (x, ang) in ((-78, 12), (-70, -14)):
        dk.box(p, (x, 1.4, 19.1), (0.4, 2.6, 0.5), WL, rot=(0, 0, ang), jitter=0.05)
    sph(p, (-63.8, 0.55, 19.0), 0.55, STRAWD, scale=(1.3, 1, 1), sub=1, jit=0.1)


# ============================================================================================================================
# 5. Lanterns
# ============================================================================================================================
def toro(p, x, z):
    vc(p, x, 0, 0.5, z, 1.0, STN, 8)
    vc(p, x, 0.5, 0.8, z, 0.72, STND, 8)
    vc(p, x, 0.8, 3.0, z, 0.42, STN, 6)
    vc(p, x, 1.7, 2.0, z, 0.62, STND, 6)
    bx(p, (x - 1.15, x + 1.15), (3.0, 3.4), (z - 1.15, z + 1.15), STND, 0.04)
    bx(p, (x - 0.8, x + 0.8), (3.4, 4.8), (z - 0.8, z + 0.8), WARM, 0.03)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (x + sx * 0.85 - 0.12, x + sx * 0.85 + 0.12), (3.4, 4.8), (z + sz * 0.85 - 0.12, z + sz * 0.85 + 0.12), STN, 0.04)
    for s in (-1, 1):
        bx(p, (x - 0.12 + s * 0.0, x + 0.12), (3.9, 4.5), (z + s * 0.78 - 0.04, z + s * 0.78 + 0.04), BLK, 0.02)
        bx(p, (x + s * 0.78 - 0.04, x + s * 0.78 + 0.04), (3.9, 4.5), (z - 0.12, z + 0.12), BLK, 0.02)
    frust(p, x, z, 4.8, 5.25, 3.0, 3.0, 0.7, 0.7, ROOF, lift=0.18, jit=0.05)
    vc(p, x, 5.25, 5.4, z, 0.3, GLD, 6, jit=0.02)


def build_Lanterns(p):
    for x in (46, 54, 68, 74):
        toro(p, x, -12)


# ============================================================================================================================
# 6. Zen garden
# ============================================================================================================================
ZROCKS = [(54, 41, 2.5, 1.5, 2.1), (66, 51, 1.8, 1.1, 1.7), (70, 39, 1.2, 0.8, 1.2), (48, 52, 1.0, 0.7, 1.0)]


def build_Zen(p):
    bx(p, (42, 78), (0, 0.4), (33, 57), SAND, 0.03)
    # raked lines (broken where rocks stand) + rings around the rocks
    circles = [(cx, cz, r + 3.3) for cx, cz, r, h, rz in ZROCKS]
    z = 35.0
    while z < 55.5:
        xa = 43.5
        cuts = []
        for (cx, cz, rr) in circles:
            dz = abs(z - cz)
            if dz < rr:
                dx = math.sqrt(rr * rr - dz * dz)
                cuts.append((cx - dx, cx + dx))
        cuts.sort()
        segs, cur = [], 43.5
        for a, b in cuts:
            if a > cur:
                segs.append((cur, a))
            cur = max(cur, b)
        if cur < 76.5:
            segs.append((cur, 76.5))
        for a, b in segs:
            if b - a > 0.5:
                rect(p, a, b, z, z + 0.35, 0.41, SANDD, 0.03)
        z += 1.8
    for (cx, cz, r, h, rz) in ZROCKS:
        for k in range(3):
            r0 = r + 0.9 + k * 1.0
            for s in range(16):
                a0, a1 = 2 * pi * s / 16, 2 * pi * (s + 1) / 16
                pts = [(cx + r0 * math.cos(a0), cz + r0 * math.sin(a0)), (cx + (r0 + 0.38) * math.cos(a0), cz + (r0 + 0.38) * math.sin(a0)),
                       (cx + (r0 + 0.38) * math.cos(a1), cz + (r0 + 0.38) * math.sin(a1)), (cx + r0 * math.cos(a1), cz + r0 * math.sin(a1))]
                flat(p, pts, 0.415, SANDD, 0.03)
    # stone frame: irregular blocks
    def run_x(zc_, x0, x1):
        x = x0
        while x < x1 - 0.1:
            ln = min(R.uniform(2.6, 4.2), x1 - x)
            bx(p, (x, x + ln - 0.08), (0, R.uniform(0.42, 0.5)), (zc_ - 0.6, zc_ + 0.6), STN, 0.1)
            x += ln

    def run_z(xc_, z0, z1):
        z = z0
        while z < z1 - 0.1:
            ln = min(R.uniform(2.6, 4.2), z1 - z)
            bx(p, (xc_ - 0.6, xc_ + 0.6), (0, R.uniform(0.42, 0.5)), (z, z + ln - 0.08), STN, 0.1)
            z += ln
    run_x(33.6, 41.4, 78.6)
    run_x(56.4, 41.4, 78.6)
    run_z(42.6, 34.2, 55.8)
    run_z(77.4, 34.2, 55.8)
    # rocks with moss
    for (cx, cz, r, h, rz) in ZROCKS:
        sph(p, (cx, 0.4 + h * 0.5, cz), r, STND, scale=(1, h / r * 0.95, rz / r), sub=1, jit=0.1)
        if r > 1.5:
            sph(p, (cx - r * 0.25, 0.4 + h * 0.95, cz), r * 0.5, GRN, scale=(1, 0.45, 0.9), sub=1, jit=0.08)
    sph(p, (54, 0.4 + 0.7, 38.7), 1.1, STN, scale=(1, 0.7, 0.8), sub=1, jit=0.1)
    # stepping stones from the south border to the big rock
    for (x, z) in ((59, 35.2), (58.2, 37.4), (57.2, 39.4)):
        flat(p, ngon_pts(x, z, 0.75, 6, 0.3), 0.42, STNL, 0.06)
    # little pine tree
    vc(p, 72, 0.4, 1.6, 52, 0.34, WD, 6, 0.28)
    beam(p, (72, 1.5, 52), (72.7, 2.7, 52.2), 0.5, 0.5, WD)
    sph(p, (72.0, 2.6, 52), 1.5, GRND, scale=(1, 0.5, 1), sub=1, jit=0.08)
    sph(p, (72.6, 3.3, 52.2), 1.2, GRN, scale=(1, 0.55, 1), sub=1, jit=0.08)
    sph(p, (72.2, 4.0, 52), 0.85, GRNL, scale=(1, 0.65, 1), sub=1, jit=0.08)


# ============================================================================================================================
# 7. Bamboo
# ============================================================================================================================
STALKS = [(83, 16, 15), (87, 15, 18), (90, 18, 13), (84, 21, 19), (88, 23, 16), (91, 26, 14), (82.5, 26, 12), (86, 28, 20), (90, 31, 17),
          (83.5, 32, 14), (88, 34, 19), (85, 36, 15), (91, 37, 12), (82.5, 38, 17)]


def build_Bamboo(p):
    bx(p, (80.5, 92.5), (0, 0.3), (13, 39), (60, 98, 60), 0.06)
    for (x, z) in ((82, 20), (86, 32), (89, 20), (84, 36), (91, 30)):
        flat(p, ngon_pts(x, z, 1.2, 6), 0.32, GRNL, 0.1)
    for i, (x, z, h) in enumerate(STALKS):
        col = BAM if i % 2 == 0 else (98, 160, 76)
        vc(p, x, 0.3, h, z, 0.42, col, 6, 0.34, jit=0.06)
        for yy in (h * 0.33, h * 0.66):
            bx(p, (x - 0.5, x + 0.5), (yy, yy + 0.2), (z - 0.5, z + 0.5), BAMD, 0.04, rot=(0, 30, 0))
        # a cross of four long leaves near the top, drooping outwards
        for k in range(4):
            a = math.radians(90 * k + 25 + i * 23)
            yy = h - 0.9 - (k % 2) * 1.6
            ex, ez = math.cos(a) * 0.95, math.sin(a) * 0.95
            beam(p, (x, yy + 0.15, z), (x + ex, yy - 0.35, z + ez), 0.5, 0.1, GRNL if k % 2 == 0 else GRN, up=(0, 1, 0), jit=0.06, caps=False)
        beam(p, (x, h - 0.05, z), (x + 0.3, h + 0.0, z + 0.3), 0.5, 0.1, GRNL, up=(0, 1, 0), caps=False)
    for (x, z, r) in ((82, 15, 0.6), (90, 36, 0.5), (86, 22, 0.45)):
        sph(p, (x, 0.45, z), r, STND, scale=(1.2, 0.7, 1), sub=1, jit=0.1)


# ============================================================================================================================
# ============================================================================================================================
# 8. Cherry trees
# ============================================================================================================================
def cherry_tree(p, x, z, k):
    vc(p, x, 0, 4.8, z, 0.9, WD, 8, 0.6, jit=0.07)
    vc(p, x, 0, 0.7, z, 1.3, WD, 8, 0.95, jit=0.05)
    beam(p, (x, 3.8, z), (x - 2.4, 6.2, z + 0.6), 0.6, 0.6, WD)
    beam(p, (x, 4.2, z), (x + 2.6, 6.6, z - 0.4), 0.55, 0.55, WD)
    sph(p, (x, 7.4, z), 5.0, PINK, scale=(1, 0.64, 1), sub=2, jit=0.07)
    sph(p, (x - 2.8, 8.2, z + 0.5), 3.0, PINKL, scale=(1, 0.7, 1), sub=2, jit=0.07)
    sph(p, (x + 3.0, 7.7, z - 0.5), 3.0, PINKD, scale=(1, 0.7, 1), sub=2, jit=0.07)
    sph(p, (x + 0.2, 9.7, z - 0.6), 2.6, PINK, scale=(1, 0.65, 1), sub=2, jit=0.07)


def build_Cherry(p):
    bx(p, (-62, -22), (0.3, 0.4), (52.5, 62.5), PINKL, 0.05)
    for (x, z, r) in ((-30, 55, 1.6), (-38, 61, 1.3), (-48, 54, 1.7), (-58, 60, 1.4), (-24, 60, 1.2), (-44, 56, 1.4), (-34, 57, 1.1)):
        flat(p, ngon_pts(x, z, r, 7), 0.42, PINK, 0.08)
    for k, x in enumerate((-28, -42, -56)):
        cherry_tree(p, x, (57, 59, 56)[k], k)


# ============================================================================================================================
# 9. Weapons (katana rack)
# ============================================================================================================================
def katana(p, x0, x1, y, z, scab, hilt, guard=GLD, tip_right=True):
    """Sword lying along x on the rack: scabbard/blade from x0 to x1, hilt beyond the right end."""
    bx(p, (x0, x1), (y - 0.17, y + 0.17), (z - 0.24, z + 0.24), scab, 0.04)
    bx(p, (x1, x1 + 0.2), (y - 0.3, y + 0.3), (z - 0.34, z + 0.34), guard, 0.03)
    bx(p, (x1 + 0.2, x1 + 1.7), (y - 0.21, y + 0.21), (z - 0.26, z + 0.26), hilt, 0.04)
    bx(p, (x1 + 0.7, x1 + 0.9), (y - 0.24, y + 0.24), (z - 0.29, z + 0.29), WHT, 0.02)
    bx(p, (x0 - 0.12, x0), (y - 0.2, y + 0.2), (z - 0.27, z + 0.27), guard, 0.03)


def build_Weapons(p):
    Z = 33
    for sx in (-82, -70):
        bx(p, (sx - 0.7, sx + 0.7), (0, 0.6), (Z - 2, Z + 2), WD, 0.05)
        beam(p, (sx, 0.6, Z - 1.7), (sx, 1.6, Z - 0.6), 0.4, 0.4, WD)
        beam(p, (sx, 0.6, Z + 1.7), (sx, 1.6, Z + 0.6), 0.4, 0.4, WD)
        bx(p, (sx - 0.45, sx + 0.45), (0.6, 6.8), (Z - 0.45, Z + 0.45), WD, 0.05)
        bx(p, (sx - 0.7, sx + 0.7), (6.8, 7.2), (Z - 0.7, Z + 0.7), GLD, 0.03)
    bx(p, (-83.2, -68.8), (6.4, 6.8), (Z - 0.55, Z + 0.55), WM, 0.05)
    bx(p, (-83.0, -69.0), (5.9, 6.1), (Z - 0.45, Z + 0.45), RED, 0.04)
    for yy in (2.0, 4.2):
        bx(p, (-82, -70), (yy, yy + 0.5), (Z - 0.5, Z + 0.5), WM, 0.05)
        for cx_ in (-80.2, -75.8, -71.8):
            bx(p, (cx_ - 0.3, cx_ + 0.3), (yy + 0.5, yy + 0.8), (Z - 0.5, Z + 0.5), WL, 0.04)
    katana(p, -80.5, -73.5, 2.85, Z + 0.15, BLK, RED)
    katana(p, -79.5, -73.0, 3.45, Z + 0.15, (30, 70, 130), WHT, guard=STL)
    katana(p, -80.5, -73.5, 5.05, Z + 0.15, STL, DRED)
    katana(p, -79.0, -72.5, 5.65, Z + 0.15, WD, GLD, guard=DGLD)
    # hanging red tassels and a little banner plate
    for x in (-78.6, -73.4):
        bx(p, (x - 0.12, x + 0.12), (3.6, 5.6), (Z + 0.55, Z + 0.7), RED, 0.03)
    bx(p, (-77.2, -74.8), (6.0, 6.0 + 0.0 + 0.25), (Z + 0.5, Z + 0.7), GLD, 0.03)


# ============================================================================================================================
# 10. Banners
# ============================================================================================================================
def war_banner(p, x):
    Z = -51
    vc(p, x, 0, 0.3, Z, 1.2, STND, 8)
    vc(p, x, 0.3, 1.0, Z, 0.95, STN, 8)
    vc(p, x, 1.0, 11.4, Z, 0.34, WD, 8, 0.28)
    sph(p, (x, 11.4, Z), 0.6, GLD, sub=1, jit=0.03)
    bx(p, (x - 2.5, x + 2.5), (11.0, 11.5), (Z - 0.25, Z + 0.25), WD, 0.04)
    for s in (-1, 1):
        sph(p, (x + s * 2.3, 11.25, Z), 0.25, GLD, sub=1, jit=0.03)
    pts = [(x - 1.9, 11.0), (x + 1.9, 11.0), (x + 1.9, 3.0), (x, 4.6), (x - 1.9, 3.0)]
    extrude(p, pts, Z + 0.35, Z + 0.55, RED, 0.04)
    extrude(p, [(x - 1.9, 11.0), (x + 1.9, 11.0), (x + 1.9, 10.2), (x - 1.9, 10.2)], Z + 0.55, Z + 0.62, BLK, 0.02)
    zc(p, x, 7.4, Z + 0.55, Z + 0.68, 1.2, WHT, 16, 0.02)
    zc(p, x + 0.5, 7.5, Z + 0.68, Z + 0.74, 1.0, RED, 16, 0.02)
    bx(p, (x - 0.12, x + 0.12), (2.0, 3.2), (Z + 0.38, Z + 0.5), GLD, 0.03)
    sph(p, (x, 1.9, Z + 0.45), 0.25, GLD, sub=1, jit=0.03)


def build_Banners(p):
    for x in (22, 31, 40):
        war_banner(p, x)


# ============================================================================================================================
# 11. Pond
# ============================================================================================================================
def build_Pond(p):
    bx(p, (-82, -58), (0, 0.4), (-30, -18), WAT, 0.04)
    for (cx, cz, r) in ((-64, -22, 1.9), (-76, -26, 1.7), (-70, -20.5, 1.2), (-68, -27.5, 1.5)):
        for k in range(2):
            flat(p, ngon_pts(cx, cz, r + 0.6 + k * 0.7, 14), 0.405 + 0.002 * k, WATL if k == 0 else WAT, 0.04)
    # rim stones
    def run_x(zc_, x0, x1):
        x = x0
        while x < x1 - 0.1:
            ln = min(R.uniform(2.2, 3.4), x1 - x)
            bx(p, (x, x + ln - 0.08), (0, R.uniform(0.45, 0.5)), (zc_ - 0.6, zc_ + 0.6), STN, 0.1)
            x += ln

    def run_z(xc_, z0, z1):
        z = z0
        while z < z1 - 0.1:
            ln = min(R.uniform(2.2, 3.0), z1 - z)
            bx(p, (xc_ - 0.6, xc_ + 0.6), (0, R.uniform(0.45, 0.5)), (z, z + ln - 0.08), STN, 0.1)
            z += ln
    run_x(-30.6, -83.2, -56.8)
    run_x(-17.4, -83.2, -56.8)
    run_z(-82.6, -30, -18)
    run_z(-57.4, -30, -18)
    # rocks and reeds
    sph(p, (-80, 1.1, -19.5), 1.8, STND, scale=(1, 0.67, 0.83), sub=1, jit=0.1)
    sph(p, (-80.4, 2.0, -19.4), 0.9, GRN, scale=(1.1, 0.5, 1), sub=1, jit=0.08)
    sph(p, (-60, 0.9, -28.5), 1.4, STND, scale=(1, 0.71, 0.93), sub=1, jit=0.1)
    sph(p, (-78, 0.8, -29), 1.1, STN, scale=(1, 0.73, 0.9), sub=1, jit=0.1)
    for (x, z, h) in ((-81.5, -28.6, 1.6), (-80.8, -29.2, 1.3), (-59.2, -19.4, 1.5)):
        vc(p, x, 0.4, 0.4 + h, z, 0.1, GRNL, 5)
        sph(p, (x, 0.4 + h, z), 0.15, WD, scale=(1, 2.0, 1), sub=1, jit=0.03)
    # lily pads with flowers
    for (cx, cz, r) in ((-64, -22, 1.2), (-76, -26, 1.0), (-70, -20.5, 0.7), (-68, -27.5, 0.8)):
        pts = ngon_pts(cx, cz, r, 9)
        pts.insert(0, (cx, cz))
        pts = ngon_pts(cx, cz, r, 9, 0.3)
        flat(p, pts, 0.43, GRN, 0.1)
    sph(p, (-64.3, 0.7, -22.4), 0.34, PINK, scale=(1, 0.8, 1), sub=1, jit=0.04)
    sph(p, (-70.2, 0.6, -20.6), 0.26, PINKL, scale=(1, 0.8, 1), sub=1, jit=0.04)
    # koi
    for (x, z, ang, col, col2) in ((-72, -21, 0, ORG, WHT), (-66, -26.5, 30, WHT, ORG)):
        sph(p, (x, 0.5, z), 0.8, col, scale=(1.0, 0.28, 0.4), sub=1, jit=0.04)
        sph(p, (x + 0.2, 0.62, z + 0.05), 0.4, col2, scale=(1, 0.2, 0.45), sub=1, jit=0.04)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        poly_pts = [(x - 0.7 * ca, 0.48, z + 0.7 * sa), (x - 1.3 * ca - 0.3 * sa, 0.48, z + 1.3 * sa - 0.3 * ca),
                    (x - 1.3 * ca + 0.3 * sa, 0.48, z + 1.3 * sa + 0.3 * ca)]
        flat(p, [(q[0], q[2]) for q in poly_pts], 0.5, col, 0.03)


# ============================================================================================================================
# 12. Tea house
# ============================================================================================================================
def build_Teahouse(p):
    roofs = []
    cx, cz = -78, 50
    # floor mat (tatami) and low table
    bx(p, (-84.6, -71.4), (0.6, 0.75), (44.4, 55.6), (196, 190, 120), 0.04)
    for x in (-81, -78, -75):
        bx(p, (x - 0.02, x + 0.02), (0.75, 0.77), (44.4, 55.6), (150, 144, 90), 0.03)
    # back wall (paper with grid), side walls (dark timber + paper windows)
    bx(p, (-85, -71), (0.6, 8.0), (43.2, 44.0), PAP, 0.03)
    for x in (-85, -81.5, -78, -74.5, -71):
        bx(p, (x - 0.2, x + 0.2), (0.6, 8.0), (43.0, 44.2), WD, 0.04)
    for yy in (2.6, 5.0, 7.5):
        bx(p, (-85, -71), (yy, yy + 0.3), (43.0, 44.2), WD, 0.04)
    for sx in (-85.8, -70.2):
        bx(p, (sx, sx + 0.8), (0.6, 8.0), (44, 56), WD, 0.06)
        zc_ = 50
        o = sx - 0.1 if sx < -78 else sx + 0.9
        bx(p, (o, o + 0.1), (3.0, 6.6), (zc_ - 3.5, zc_ + 3.5), PAP, 0.03)
        for dz in (-3.5, 0, 3.5):
            bx(p, (o - 0.05, o + 0.15), (2.9, 6.7), (zc_ + dz - 0.15, zc_ + dz + 0.15), WD, 0.03)
        for yy in (2.9, 4.7, 6.5):
            bx(p, (o - 0.05, o + 0.15), (yy, yy + 0.2), (zc_ - 3.5, zc_ + 3.5), WD, 0.03)
    # front: two posts, lintel beam, half-open sliding door
    for x in (-84.4, -71.6):
        vc(p, x, 0.6, 8.0, 55.4, 0.5, RED, 8)
        bx(p, (x - 0.7, x + 0.7), (0.6, 1.1), (54.7, 56.1), STN, 0.04)
    bx(p, (-85.2, -70.8), (7.0, 7.9), (55.0, 55.8), RED, 0.04)
    bx(p, (-84.0, -81.0), (0.9, 6.9), (55.0, 55.25), PAP, 0.03)
    for yy in (0.9, 2.9, 4.9, 6.7):
        bx(p, (-84.0, -81.0), (yy, yy + 0.2), (54.95, 55.3), WD, 0.03)
    # low table, cushions, tea set
    bx(p, (-80, -76), (0.75, 1.15), (47.5, 50.5), WM, 0.04)
    for sx in (-79.7, -76.3):
        for sz in (47.8, 50.2):
            bx(p, (sx - 0.15, sx + 0.15), (0.6, 0.75), (sz - 0.15, sz + 0.15), WD, 0.04)
    bx(p, (-81.8, -80.2), (0.75, 1.0), (47.8, 49.6), RED, 0.05)
    bx(p, (-75.8, -74.2), (0.75, 1.0), (47.8, 49.6), RED, 0.05)
    bx(p, (-80.3, -78.0), (1.15, 1.2), (48, 50), BLK, 0.03)
    sph(p, (-79.3, 1.6, 49), 0.5, DGR, scale=(1, 0.85, 1), sub=1, jit=0.04)
    vc(p, -79.3, 2.0, 2.2, 49, 0.18, STL, 6)
    for z in (48.4, 49.6):
        vc(p, -77, 1.2, 1.55, z, 0.22, WHT, 6)
    # hip roofs: lower and upper, golden finial ball, red paper lantern at the corner
    roofs += frust(p, cx, cz, 8.0, 9.2, 18, 16, 12, 10, ROOF, lift=0.6)
    roofs += eave_trim(p, cx, cz, 8.0, 18, 16, 0.6, DGLD, t=0.3, h=0.3)
    roofs += frust(p, cx, cz, 9.2, 10.4, 11, 9, 4, 3, ROOF, lift=0.4)
    roofs.append(sph(p, (cx, 11.2, cz), 0.8, GLD, sub=1, jit=0.03))
    roofs.append(cone(p, cx, 10.4, cz, 0.5, 0.35, DGLD, 6))
    sph(p, (-70.6, 6.2, 55.6), 0.55, RED, scale=(1, 1.2, 1), sub=1, jit=0.04)
    bx(p, (-70.85, -70.35), (6.9, 7.2), (55.35, 55.85), BLK, 0.02)
    return {"Roof": roofs}


# ============================================================================================================================
# 13. Tower
# ============================================================================================================================
def build_Tower(p):
    roofs = []
    cx, cz = -36, -46
    legs = [(-39.6, -49.6), (-32.4, -49.6), (-39.6, -42.4), (-32.4, -42.4)]
    for (x, z) in legs:
        vc(p, x, 0, 12, z, 0.75, WD, 8, 0.62, jit=0.06)
        bx(p, (x - 1.0, x + 1.0), (0, 0.5), (z - 1.0, z + 1.0), STN, 0.05)
    # cross braces on the four sides
    for (a, b, s) in (((-39.6, -49.6), (-32.4, -49.6), 'z'), ((-39.6, -42.4), (-32.4, -42.4), 'z'),
                      ((-39.6, -49.6), (-39.6, -42.4), 'x'), ((-32.4, -49.6), (-32.4, -42.4), 'x')):
        for (y0, y1) in ((1.2, 10.8), (10.8, 1.2)):
            beam(p, (a[0], y0, a[1]), (b[0], y1, b[1]), 0.45, 0.45, WM)
        bx(p, (min(a[0], b[0]) - 0.2, max(a[0], b[0]) + 0.2), (5.6, 6.1), (min(a[1], b[1]) - 0.2, max(a[1], b[1]) + 0.2), WD, 0.04)
    # platform with railing
    bx(p, (-41.5, -30.5), (12, 13), (-51.5, -40.5), WM, 0.06)
    bx(p, (-41.7, -30.3), (11.6, 12), (-51.7, -40.3), WD, 0.04)
    for (x, z) in ((-40.6, -50.6), (-31.4, -50.6), (-40.6, -41.4), (-31.4, -41.4)):
        vc(p, x, 13, 19, z, 0.4, RED, 8)
        bx(p, (x - 0.55, x + 0.55), (18.7, 19.0), (z - 0.55, z + 0.55), GLD, 0.03)
    bx(p, (-41.0, -31.0), (13.9, 14.2), (-51.0, -50.2), RED, 0.04)
    bx(p, (-41.0, -40.2), (13.9, 14.2), (-51.0, -41.0), RED, 0.04)
    bx(p, (-31.8, -31.0), (13.9, 14.2), (-51.0, -41.0), RED, 0.04)
    bx(p, (-41.0, -31.0), (13.9, 14.2), (-41.8, -41.0), RED, 0.04)
    for x in (-39.2, -37.6, -36.0, -34.4, -32.8):
        bx(p, (x - 0.1, x + 0.1), (13, 13.9), (-41.6, -41.4), WD, 0.04)
    # paper wall at the back with a dark window, side wall slits
    bx(p, (-40.5, -31.5), (13, 18.4), (-50.5, -50.3), PAP, 0.03)
    bx(p, (-38.5, -33.5), (14.8, 17.0), (-50.3, -50.2), BLK, 0.03)
    for x in (-40.5, -36, -31.5):
        bx(p, (x - 0.15, x + 0.15), (13, 18.4), (-50.6, -50.2), WD, 0.04)
    # ladder at the front
    for x in (-36.9, -35.1):
        bx(p, (x - 0.15, x + 0.15), (0, 12.2), (-41.8, -41.4), WM, 0.04)
    y = 0.9
    while y < 12:
        bx(p, (-36.9, -35.1), (y, y + 0.2), (-41.7, -41.5), WL, 0.04)
        y += 1.3
    # roofs
    roofs += frust(p, cx, cz, 19.0, 20.8, 15, 15, 8, 8, ROOF, lift=0.8)
    roofs += eave_trim(p, cx, cz, 19.0, 15, 15, 0.8, DGLD, t=0.3, h=0.3)
    roofs += frust(p, cx, cz, 20.4, 21.3, 9.4, 9.4, 1.6, 1.6, ROOF, lift=0.4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            roofs.append(cone(p, cx + sx * 7.2, 19.8, cz + sz * 7.2, 0.35, 1.2, GLD, 6))
    roofs.append(vc(p, cx, 21.3, 23.9, cz, 0.25, GLD, 6))
    for yy in (21.8, 22.5):
        roofs.append(vc(p, cx, yy, yy + 0.2, cz, 0.55, DGLD, 8))
    roofs.append(sph(p, (cx, 24.0, cz), 0.3, GLD, sub=1, jit=0.02))
    return {"Roof": roofs}


# ============================================================================================================================
# 14. Taiko drum
# ============================================================================================================================
def build_Taiko(p):
    X, Z = 22, 38
    bx(p, (16.5, 27.5), (0, 0.8), (Z - 2.5, Z + 2.5), WD, 0.05)
    for sx in (-1, 1):
        bx(p, (X + sx * 4.4 - 0.4, X + sx * 4.4 + 0.4), (0.8, 7.0), (Z - 1.3, Z + 1.3), WM, 0.05)
        bx(p, (X + sx * 4.4 - 0.55, X + sx * 4.4 + 0.55), (7.0, 7.3), (Z - 1.5, Z + 1.5), GLD, 0.03)
        for sz in (-1, 1):
            beam(p, (X + sx * 4.4, 0.8, Z + sz * 2.3), (X + sx * 4.4, 3.6, Z + sz * 0.9), 0.5, 0.5, WD)
        bx(p, (X + sx * 3.9 - 0.15, X + sx * 3.9 + 0.15), (4.6, 5.8), (Z - 0.5, Z + 0.5), STL, 0.03)
    # barrel (axis along z), bands, skins, tacks
    zc(p, X, 5.2, Z - 2.1, Z + 2.1, 3.3, (160, 60, 44), 16, 0.06)
    zc(p, X, 5.2, Z - 0.35, Z + 0.35, 3.45, GLD, 16, 0.03)
    for s in (-1, 1):
        zc(p, X, 5.2, Z + s * 1.7 - 0.15, Z + s * 1.7 + 0.15, 3.36, DGLD, 16, 0.03)
    zc(p, X, 5.2, Z + 2.1, Z + 2.35, 3.1, PAP, 16, 0.02)
    zc(p, X, 5.2, Z - 2.35, Z - 2.1, 3.1, PAP, 16, 0.02)
    zc(p, X, 5.2, Z + 2.35, Z + 2.4, 1.2, RED, 12, 0.02)
    zc(p, X, 5.2, Z + 2.4, Z + 2.43, 0.45, BLK, 8, 0.02)
    for k in range(14):
        a = 2 * pi * k / 14
        bx(p, (X + 3.12 * math.cos(a) - 0.12, X + 3.12 * math.cos(a) + 0.12), (5.2 + 3.12 * math.sin(a) - 0.12, 5.2 + 3.12 * math.sin(a) + 0.12),
           (Z + 2.35, Z + 2.5), GLD, 0.02)
    # mallets leaning on the stand
    for sx in (-1, 1):
        beam(p, (X + sx * 3.6, 0.8, Z + 3.0), (X + sx * 3.9, 3.8, Z + 1.4), 0.4, 0.4, WL)
        sph(p, (X + sx * 3.58, 1.0, Z + 3.05), 0.3, WD, sub=1, jit=0.03)


# ============================================================================================================================
# 15. Bridge
# ============================================================================================================================
def arch_y(z):
    t = max(-1.0, min(1.0, (z + 24) / 9.0))
    return 1.2 + 1.4 * (1 - t * t)


def build_Bridge(p):
    X = -70
    # stone abutments at both ends
    for z in (-32.2, -15.8):
        bx(p, (X - 2.2, X + 2.2), (0.6, 1.0), (z - 0.8, z + 0.8), STND, 0.05)
    # planks following the arch
    z = -33.0
    n = 0
    while z < -15.0 - 0.01:
        zm = z + 0.45
        y = arch_y(zm)
        ang = math.degrees(math.atan2(arch_y(z + 0.9) - arch_y(z), 0.9))
        dk.box(p, (X, y - 0.2, zm), (4.0, 0.4, 0.95), (196, 148, 96) if n % 2 else (170, 122, 76), rot=(-ang, 0, 0), jitter=0.05)
        z += 0.9
        n += 1
    for sx in (-2.0, 2.0):
        zz = [-33.0 + 1.5 * k for k in range(13)]
        for za, zb in zip(zz, zz[1:]):
            beam(p, (X + sx, max(0.9, arch_y(za) - 0.55), za), (X + sx, max(0.9, arch_y(zb) - 0.55), zb), 0.4, 0.55, DRED, up=(1, 0, 0))
    # railings: posts, curved top rail, lower rail
    zs = [-32.4, -28.8, -25.2, -22.8, -19.2, -15.6]
    for sx in (-2.0, 2.0):
        for zp in zs:
            y = arch_y(zp)
            vc(p, X + sx, y, y + 1.0, zp, 0.2, RED, 6)
            sph(p, (X + sx, y + 1.05, zp), 0.2, GLD, sub=1, jit=0.02)
        for (za, zb) in zip(zs, zs[1:]):
            beam(p, (X + sx, arch_y(za) + 0.85, za), (X + sx, arch_y(zb) + 0.85, zb), 0.22, 0.24, RED, up=(1, 0, 0))
            beam(p, (X + sx, arch_y(za) + 0.4, za), (X + sx, arch_y(zb) + 0.4, zb), 0.16, 0.2, DRED, up=(1, 0, 0))



# ============================================================================================================================
# 16. Obstacle course
# ============================================================================================================================
def build_Course(p):
    bx(p, (-89, -63), (0.3, 0.5), (-4, 8), SAND, 0.04)
    for z in (-2.5, -0.5, 1.5, 3.5, 5.5):
        rect(p, -88.5, -63.5, z, z + 0.4, 0.51, SANDD, 0.03)
    # climbing wall on the left, holds on its east face
    bx(p, (-89, -87.8), (0.5, 7.5), (-2.5, 6.5), (176, 128, 82), 0.05)
    for yy in (2.5, 4.5, 6.5):
        bx(p, (-89.1, -87.7), (yy, yy + 0.3), (-2.6, 6.6), WD, 0.04)
    bx(p, (-89.2, -87.6), (7.2, 7.5), (-2.7, 6.7), RED, 0.04)
    for (z0, z1, c) in ((-2.3, 0.5, WL), (0.7, 3.7, (196, 150, 100)), (3.9, 6.3, WL)):
        bx(p, (-87.8, -87.65), (0.8, 7.0), (z0, z1), c, 0.04)
    holds = [(0, 1.4, RED), (3, 1.9, GLD), (5, 1.3, (60, 120, 200)), (1.5, 3.4, GLD), (4.2, 3.8, RED), (-0.8, 4.8, (60, 120, 200)),
             (2.6, 5.2, RED), (5.4, 5.9, GLD), (0.8, 6.4, (60, 120, 200))]
    for (z, y, c) in holds:
        bx(p, (-87.8, -87.0), (y, y + 0.6), (z - 0.4, z + 0.4), c, 0.03)
    # balance beam on two trestles
    for x in (-83, -77):
        bx(p, (x - 0.45, x + 0.45), (0.5, 2.3), (1.2, 2.8), WD, 0.05)
        beam(p, (x, 0.5, 1.0), (x, 2.0, 1.8), 0.4, 0.4, WD)
        beam(p, (x, 0.5, 3.0), (x, 2.0, 2.2), 0.4, 0.4, WD)
    bx(p, (-84.5, -75.5), (2.3, 3.0), (1.3, 2.7), WM, 0.05)
    bx(p, (-84.5, -75.5), (3.0, 3.05), (1.5, 2.5), WL, 0.03)
    # jumping stumps with rope rings
    for (x, z, h, c) in ((-72, 0, 1.0, WL), (-69, 4, 1.6, WM), (-66, 0, 2.2, WL), (-63.5, 5, 2.8, WM)):
        vc(p, x, 0.5, 0.5 + h, z, 0.9, c, 10, jit=0.08)
        vc(p, x, 0.5 + h - 0.1, 0.5 + h, z, 0.95, WD, 10, jit=0.05)
        vc(p, x, 0.5 + h * 0.4, 0.5 + h * 0.4 + 0.18, z, 0.95, STRAW, 10, jit=0.05)
    # pull-up bar
    for x in (-81, -75):
        vc(p, x, 0.5, 5.0, 6.5, 0.35, WD, 8)
        beam(p, (x, 0.5, 6.5 + 1.3), (x, 3.0, 6.5 + 0.2), 0.3, 0.3, WD)
        bx(p, (x - 0.7, x + 0.7), (0.5, 0.8), (6.5 + 0.9, 6.5 + 1.5), WD, 0.04)
    bx(p, (-81.2, -74.8), (4.4, 4.8), (6.3, 6.7), STL, 0.03)
    # small start flag
    vc(p, -86, 0.5, 4.2, -3.3, 0.15, WD, 6)
    extrude(p, [(-86, 4.2), (-86, 3.2), (-84.6, 3.7)], -3.4, -3.2, RED, 0.03)


# ============================================================================================================================
# 17. Targets
# ============================================================================================================================
def build_Targets(p):
    bx(p, (63, 89), (0, 0.2), (-3, 3), (150, 140, 125), 0.05)
    for x in (68, 76, 84):
        # straw board on a tripod stand
        zc(p, x, 5.0, -0.35, 0.35, 2.6, STRAW, 14, 0.07)
        zc(p, x, 5.0, 0.35, 0.45, 2.35, WHT, 14, 0.02)
        zc(p, x, 5.0, 0.4, 0.5, 1.7, RED, 14, 0.02)
        zc(p, x, 5.0, 0.45, 0.55, 1.0, WHT, 12, 0.02)
        zc(p, x, 5.0, 0.5, 0.62, 0.55, GLD, 10, 0.02)
        zc(p, x, 5.0, -0.5, -0.35, 2.7, WD, 14, 0.04)
        beam(p, (x, 2.5, 0.0), (x, 0.2, 0.0), 0.5, 0.5, WD, up=(0, 0, 1))
        beam(p, (x, 2.6, -0.3), (x, 0.2, -2.6), 0.4, 0.4, WD)
        beam(p, (x, 2.6, 0.3), (x - 0.0, 0.2, 2.6), 0.4, 0.4, WD)
        bx(p, (x - 1.4, x + 1.4), (0.2, 0.5), (-0.3, 0.3), WD, 0.04)
    # shuriken stuck in the boards
    for (x, y, rot) in ((68.9, 5.9, 15), (76.2, 4.3, 35), (84.8, 5.4, 55), (83.6, 4.4, 10)):
        star4(p, x, y, 0.5, 0.75, 0.75, STL, rot, 0.3)
    # arrows laying in the gravel
    for (x, z, ang) in ((70.5, 2.0, 12), (79, 1.6, -9), (86.5, 2.2, 20)):
        dk.box(p, (x, 0.3, z), (3.0, 0.1, 0.1), WL, rot=(0, ang, 0), jitter=0.03)
        dk.box(p, (x + 1.5 * math.cos(math.radians(-ang)), 0.3, z + 1.5 * math.sin(math.radians(-ang))), (0.4, 0.1, 0.3), STL, rot=(0, ang, 0), jitter=0.03)


# ============================================================================================================================
# 18. Totem
# ============================================================================================================================
def build_Totem(p):
    X, Z = 88, -22
    vc(p, X, 0, 1.0, Z, 3.0, STN, 8)
    vc(p, X, 1.0, 2.0, Z, 2.3, STND, 8)
    vc(p, X, 2.0, 16.0, Z, 0.8, WD, 8, 0.7, jit=0.06)
    # coloured bands on the pole
    for (y0, y1, c) in ((2.0, 2.6, RED), (3.6, 4.0, GLD), (9.0, 9.4, GLD), (14.2, 14.7, RED), (15.4, 16.0, GLD)):
        vc(p, X, y0, y1, Z, 1.0, c, 8, jit=0.03)
    # carved ninja face between the shuriken
    bx(p, (X - 0.9, X + 0.9), (9.6, 11.4), (Z + 0.5, Z + 0.95), BLK, 0.03)
    bx(p, (X - 0.7, X + 0.7), (10.2, 10.7), (Z + 0.95, Z + 1.05), WHT, 0.02)
    bx(p, (X - 0.5, X - 0.2), (10.3, 10.6), (Z + 1.05, Z + 1.1), BLK, 0.02)
    bx(p, (X + 0.2, X + 0.5), (10.3, 10.6), (Z + 1.05, Z + 1.1), BLK, 0.02)
    bx(p, (X - 0.95, X + 0.95), (10.9, 11.2), (Z + 0.95, Z + 1.0), RED, 0.02)
    # two big steel shuriken, bolted on
    star4(p, X, 12.5, Z + 1.15, Z + 1.65, 3.6, STL, 0, 0.3)
    zc(p, X, 12.5, Z + 1.65, Z + 1.8, 0.9, RED, 12, 0.02)
    zc(p, X, 12.5, Z + 1.8, Z + 1.85, 0.35, BLK, 8, 0.02)
    star4(p, X, 6.5, Z + 1.15, Z + 1.65, 2.4, STL, 45, 0.3)
    zc(p, X, 6.5, Z + 1.65, Z + 1.8, 0.6, RED, 12, 0.02)
    # golden cap
    vc(p, X, 16.0, 17.0, Z, 1.1, GLD, 8, 0.85)
    cone(p, X, 17.0, Z, 0.7, 0.4, DGLD, 8)
    for sx in (-1, 1):
        bx(p, (X + sx * 1.0 - 0.1, X + sx * 1.0 + 0.1), (14.8, 15.4), (Z + 0.3, Z + 0.5), RED, 0.03)


# ============================================================================================================================
# 19. Statue
# ============================================================================================================================
def build_Statue(p):
    X, Z = -16, -30
    # stepped plinth with a carved front panel
    bx(p, (X - 4.3, X + 4.3), (0.4, 1.6), (Z - 4.3, Z + 4.3), STN, 0.06)
    bx(p, (X - 4.5, X + 4.5), (0, 0.4), (Z - 4.5, Z + 4.5), STND, 0.05)
    bx(p, (X - 3.5, X + 3.5), (1.6, 2.6), (Z - 3.5, Z + 3.5), STND, 0.06)
    bx(p, (X - 2.0, X + 2.0), (0.6, 1.3), (Z + 4.3, Z + 4.42), STND, 0.04)
    zc(p, X, 0.95, Z + 4.42, Z + 4.5, 0.3, GLD, 8, 0.03)
    # sitting body: haunches, chest, front legs, tail
    sph(p, (X - 1.4, 3.9, Z - 0.6), 1.6, STN, scale=(0.9, 1.1, 1.3), sub=1, jit=0.07)
    sph(p, (X + 1.4, 3.9, Z - 0.6), 1.6, STN, scale=(0.9, 1.1, 1.3), sub=1, jit=0.07)
    sph(p, (X, 6.0, Z - 0.5), 2.5, STN, scale=(1, 1.15, 0.9), sub=2, jit=0.06)
    sph(p, (X, 7.6, Z + 0.6), 1.5, STNL, scale=(0.95, 0.6, 0.6), sub=1, jit=0.05)
    for sx in (-1, 1):
        bx(p, (X + sx * 1.2 - 0.6, X + sx * 1.2 + 0.6), (2.6, 6.2), (Z + 1.0, Z + 2.1), STN, 0.06)
        bx(p, (X + sx * 1.2 - 0.7, X + sx * 1.2 + 0.7), (2.6, 3.2), (Z + 1.0, Z + 2.6), STNL, 0.05)
    sph(p, (X + 2.6, 4.3, Z - 3.4), 1.7, STNL, scale=(0.7, 1.2, 1.0), sub=1, jit=0.07)
    sph(p, (X + 2.3, 6.2, Z - 3.8), 1.0, STN, scale=(0.8, 1.0, 0.9), sub=1, jit=0.07)
    # head with snout, ears, eyes, nose
    sph(p, (X, 10.0, Z - 0.2), 2.4, STN, scale=(1.05, 0.92, 0.98), sub=2, jit=0.06)
    bx(p, (X - 1.0, X + 1.0), (8.7, 9.9), (Z + 1.7, Z + 3.4), STNL, 0.05)
    bx(p, (X - 0.45, X + 0.45), (9.5, 10.1), (Z + 3.4, Z + 3.9), BLK, 0.03)
    for sx in (-1, 1):
        cone(p, X + sx * 1.5, 11.5, Z - 0.3, 0.95, 2.2, STN, 4)
        bx(p, (X + sx * 1.5 - 0.12, X + sx * 1.5 + 0.12), (11.7, 13.0), (Z + 0.4, Z + 0.55), PINKD, 0.03)
        bx(p, (X + sx * 0.95 - 0.28, X + sx * 0.95 + 0.28), (10.35, 10.85), (Z + 2.0, Z + 2.18), BLK, 0.02)
        bx(p, (X + sx * 0.95 - 0.1, X + sx * 0.95), (10.6, 10.8), (Z + 2.18, Z + 2.25), WHT, 0.02)
    # red ninja headband with long tails, and a scarf
    vc(p, X, 10.4, 11.3, Z - 0.2, 2.5, RED, 12, jit=0.03)
    bx(p, (X - 1.0, X + 1.0), (10.45, 11.25), (Z + 2.3, Z + 2.55), DRED, 0.03)
    bx(p, (X - 0.45, X + 0.45), (10.65, 11.05), (Z + 2.55, Z + 2.62), GLD, 0.03)
    beam(p, (X + 0.3, 10.9, Z - 2.6), (X + 2.6, 10.3, Z - 4.8), 0.7, 0.2, RED, up=(0, 1, 0))
    beam(p, (X - 0.3, 10.9, Z - 2.6), (X - 2.0, 9.4, Z - 4.9), 0.7, 0.2, RED, up=(0, 1, 0))
    bx(p, (X - 1.6, X + 1.6), (8.0, 8.5), (Z + 0.2, Z + 1.6), RED, 0.04)


# ============================================================================================================================
# 20. Moon
# ============================================================================================================================
def build_Moon(p):
    X, Z = -68, -54
    # stone platform with steps
    tiled_block(p, -83, -53, 0, 1.2, -59, -49, grid(-83, -53, 10), grid(-59, -49, 4), lambda i, j: STN if (i + j) % 2 == 0 else STND,
                shade3(STND, 0.8))
    bx(p, (-73, -63), (0, 0.6), (-49.3, -47.1), STNL, 0.05)
    bx(p, (-72, -64), (0.6, 0.8), (-49.3, -48.2), STNL, 0.05)
    # the two red pillars with black bases and gold bands
    for x in (-81, -55):
        bx(p, (x - 1.5, x + 1.5), (1.2, 2.4), (Z - 1.5, Z + 1.5), BLK, 0.04)
        vc(p, x, 2.4, 23.2, Z, 0.9, RED, 12, 0.78, jit=0.05)
        for y0 in (3.0, 12.0, 20.6):
            vc(p, x, y0, y0 + 0.5, Z, 1.05, GLD, 12, jit=0.03)
    # top beams: black kasagi with upswept ends, red tie below
    bx(p, (-80, -56), (23.2, 24.2), (Z - 1.0, Z + 1.0), BLK, 0.04)
    for s in (-1, 1):
        beam(p, (X + s * 12, 23.7, Z), (X + s * 15, 24.0, Z), 2.0, 0.9, BLK, up=(0, 1, 0))
        bx(p, sorted((X + s * 14.8, X + s * 15)), (23.8, 24.4), (Z - 1.0, Z + 1.0), BLK, 0.03)
    bx(p, (-81, -55), (19.6, 20.5), (Z - 0.5, Z + 0.5), RED, 0.04)
    bx(p, (-81, -55), (21.4, 22.0), (Z - 0.4, Z + 0.4), DRED, 0.04)
    # the moon: pale halo behind, bright disc, craters
    zc(p, X, 13.2, Z - 0.95, Z - 0.6, 10.4, (252, 238, 168), 28, 0.02)
    zc(p, X, 13.2, Z - 0.6, Z + 0.6, 9.5, (250, 244, 214), 28, 0.03)
    for (dx, dy, r) in ((-4, 1.8, 2.0), (4, -2.2, 1.5), (-1, 5.6, 1.2), (2.4, 4.4, 0.8), (-5.2, -3.0, 0.9)):
        zc(p, X + dx, 13.2 + dy, Z + 0.6, Z + 0.85, r, (226, 218, 182), 12, 0.02)
    zc(p, X + 2.6, 13.2 + 0.6, Z + 0.6, Z + 0.7, 5.2, (240, 233, 200), 20, 0.02)
    # ninja silhouette in front of the moon (flat figure)
    nz0, nz1 = Z + 0.85, Z + 1.35
    ox, oy = X - 1.5, 5.4
    def L(a, b, w, c=BLK):
        beam(p, (ox + a[0], oy + a[1], nz0), (ox + b[0], oy + b[1], nz0), w, nz1 - nz0, c, up=(0, 0, 1), jit=0.02)
    L((0, 3.0), (0, 5.2), 1.3)                  # torso
    L((0, 3.0), (-1.9, 1.3), 0.95); L((-1.9, 1.3), (-2.9, 0.0), 0.8)       # back leg
    L((0.2, 3.0), (1.9, 1.9), 0.95); L((1.9, 1.9), (2.1, 0.0), 0.8)        # front leg
    L((0.1, 5.0), (1.6, 5.9), 0.7); L((1.6, 5.9), (2.5, 7.0), 0.6)         # sword arm
    L((-0.1, 5.0), (-1.4, 5.5), 0.6); L((-1.4, 5.5), (-1.0, 6.6), 0.55)    # other arm
    L((2.5, 7.0), (5.0, 9.4), 0.28, STL)                                   # blade
    L((-0.3, 6.15), (-2.8, 6.7), 0.35, RED); L((-2.8, 6.7), (-4.2, 6.0), 0.3, RED)   # scarf
    zl = nz0
    sph(p, (ox + 0.1, oy + 5.95, (nz0 + nz1) / 2), 0.75, BLK, scale=(1, 1, 0.5 / 1.5), sub=1, jit=0.02)
    bx(p, (ox - 0.55, ox + 0.75), (oy + 5.9, oy + 6.2), (nz1 - 0.02, nz1 + 0.05), RED, 0.02)


# ============================================================================================================================
PARTS = [("Floor", build_Floor), ("Hall", build_Hall), ("Gate", build_Gate), ("Dummies", build_Dummies), ("Lanterns", build_Lanterns),
         ("Zen", build_Zen), ("Bamboo", build_Bamboo), ("Cherry", build_Cherry), ("Weapons", build_Weapons), ("Banners", build_Banners),
         ("Pond", build_Pond), ("Teahouse", build_Teahouse), ("Tower", build_Tower), ("Taiko", build_Taiko), ("Bridge", build_Bridge),
         ("Course", build_Course), ("Targets", build_Targets), ("Totem", build_Totem), ("Statue", build_Statue), ("Moon", build_Moon)]

EL = {"Hall": 36, "Floor": 40}
MULT = {"Floor": 2.0, "Hall": 3.3, "Gate": 2.2, "Dummies": 2.6, "Lanterns": 2.8, "Zen": 2.4, "Bamboo": 2.6, "Cherry": 2.3,
        "Weapons": 3.0, "Banners": 2.6, "Pond": 2.6, "Teahouse": 2.7, "Tower": 2.3, "Taiko": 3.2, "Bridge": 3.0, "Course": 2.6,
        "Targets": 2.6, "Totem": 2.8, "Statue": 3.0, "Moon": 2.0}
# where the reference Shiba stands in each preview: (x, z, facing, lift); defaults to the part's pad
SHIBA_AT = {"Hall": (61, -34, 270, 0.6), "Floor": (24, 58, 270, 0.0), "Gate": (14, 50, 270, 0.0), "Dummies": (-74, 14, 270, 0.0),
            "Lanterns": (61, -6, 270, 0.0), "Zen": (60, 31, 270, 0.0), "Bamboo": (87, 10, 270, 0.0), "Cherry": (-42, 50, 270, 0.0),
            "Weapons": (-76, 38, 270, 0.0), "Banners": (31, -44, 270, 0.0), "Pond": (-55, -24, 180, 0.0),
            "Teahouse": (-78, 61, 270, 0.0), "Tower": (-36, -36, 270, 0.0), "Taiko": (22, 30, 270, 0.0), "Bridge": (-70, -11, 270, 0.0),
            "Course": (-83, -6, 270, 0.0), "Targets": (76, 8, 270, 0.0), "Totem": (88, -14, 270, 0.0), "Statue": (-16, -20, 270, 0.0),
            "Moon": (-68, -44, 270, 0.0)}


# ---- fit to the union box of the blueprint pieces ---------------------------------------------------------------------------------
def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = list(q["Size"]); o = q["Offset"]; r = q.get("Rotation")
        if r:
            assert r[0] == 0 and (r[1], r[2]) in ((0, 0), (90, 0), (0, 90))
            if r[2] == 90:
                s = [s[1], s[0], s[2]]
            if r[1] == 90:
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
    for o in objs:   # report objects that stick out of the target box by more than 0.05 studs
        ws = [v.co for v in o.data.vertices]
        for i, nm in enumerate("xzy"):
            if min(v[i] for v in ws) < tl[i] - 0.05 or max(v[i] for v in ws) > th[i] + 0.05:
                print(f"  WARN {part.id}: {o.name} sticks out on {nm}: {min(v[i] for v in ws):.2f}..{max(v[i] for v in ws):.2f} vs {tl[i]:.2f}..{th[i]:.2f}")
    sc = [(th[i] - tl[i]) / (bh[i] - bl[i]) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    sx, sy, sz = sc[0], sc[2], sc[1]    # back to stage order
    print(f"FIT {part.id}: raw size {[round(bh[0]-bl[0],2), round(bh[2]-bl[2],2), round(bh[1]-bl[1],2)]} "
          f"scale stage xyz = {sx:.3f} {sy:.3f} {sz:.3f}")


# ---- previews -----------------------------------------------------------------------------------------------------------------------
def shiba_for(x, z, facing, lift):
    # the part meshes are mirrored in x by dk.finish, so mirror the reference dog too (position and facing)
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
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    path = os.path.join(OUT, filename)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    pass   # no flip: dk.finish already mirrors x, so the render is the in-game handedness
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
    tri_report = {}
    for pid, fn in PARTS:
        if ONLY and pid not in ONLY:
            continue
        pj = dk.blueprint_part(BP, pid)
        part = dk.Part(pid)
        groups = fn(part)
        if os.environ.get("ND_DBG"):
            tally = {}
            for o in part.objs:
                k = o.name.rstrip("0123456789.")
                tally[k] = tally.get(k, 0) + sum(len(q.vertices) - 2 for q in o.data.polygons)
            print("TALLY", pid, sorted(tally.items(), key=lambda kv: -kv[1])[:8])
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        built[pid] = meshes
        tri_report[pid] = (len(meshes), sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons))
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        x, z, f, lift = SHIBA_AT[pid]
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", 150, EL.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000))
        roofm = [m for m in meshes if m.name.endswith("_Roof")]
        if roofm:   # cutaway view without the roofs, to check the interior and the Shiba spot
            dk.hide(roofm, True)
            snap([m for m in meshes if m not in roofm], [o for o in sb if o.type == "MESH"], f"preview_{pid}_open.png", 150, 34, MULT.get(pid, 2.4), (1400, 1000))
            dk.hide(roofm, False)
        drop(sb)
    print("TRIS", json.dumps(tri_report))
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0.6)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 160, 40, 2.3, (1800, 1100))
    roof = [m for ms in built.values() for m in ms if m.name.endswith(("Hall_Roof",))]
    dk.hide(roof, True)
    snap([m for m in allm if m not in roof], shm, "stage_top.png", 180, 89, 2.1, (1800, 1100), top=True)
    dk.hide(roof, False)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_NinjaDojo.png"))


main()
