"""Scatter props: small reusable decoration models the game duplicates with random rotation/scale (see README.md).

Run:  blender --background --factory-startup --python build_scatter.py -- <outdir>
Writes into <outdir>: Scatter_<Name>.fbx (one mesh each, origin bottom centre on the ground, units = studs), manifest.json,
contact_sheet.png (all props, orange bar = Shiba height 6) and contact_<biome>.png per biome. Also rewrites README.md.
Built on ../decor/decorkit.py (stage frame: x right, y UP, z depth). The x mirror on export is kept on purpose.
"""
import os, sys, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "decor"))
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

R = random.Random(5)
pi = math.pi
ONLY = set(os.environ.get("SC_ONLY", "").split(",")) - {""}

# ---- palette ------------------------------------------------------------------------------------------------------
BARK = (110, 78, 50); BARK_D = (82, 58, 38); BARK_L = (140, 104, 70)
LEAF = (70, 156, 64); LEAF_L = (110, 188, 80); LEAF_D = (44, 116, 52); LEAF_Y = (150, 190, 70)
PINE = (36, 110, 70); PINE_D = (26, 86, 58); PINE_L = (54, 136, 78)
WHITE = (244, 244, 238); SNOW = (236, 244, 252); CREAM = (236, 222, 190)
GREY = (150, 154, 160); GREY_D = (104, 108, 116); GREY_L = (190, 194, 200)
STONE = (140, 140, 138); STONE_D = (104, 104, 104); STONE_L = (176, 174, 168)
RED = (208, 60, 52); RED_D = (160, 42, 40); ORANGE = (240, 130, 40); YEL = (246, 206, 70)
BLUE = (60, 110, 200); TEAL = (40, 170, 168); PINK = (240, 130, 170); PINK_L = (250, 180, 205); PINK_D = (214, 96, 140)
PURPLE = (150, 100, 200)
SAND = (238, 214, 150); SAND_D = (200, 176, 118); SAND_L = (248, 228, 168)
WOOD = (166, 122, 74); WOOD_D = (116, 80, 48); WOOD_L = (198, 154, 98); WOOD_W = (226, 214, 196); DRIFT = (176, 160, 138)
CACT = (84, 152, 84); CACT_D = (60, 120, 70)
MESA = (196, 100, 60); MESA_D = (160, 72, 46); MESA_L = (222, 140, 84)
STRAW = (232, 196, 90); STRAW_D = (196, 156, 62); TUMBLE = (190, 150, 96)
IRON = (62, 66, 74); IRON_D = (42, 46, 52); STEEL = (160, 166, 174)
ROPE = (206, 176, 118); ROPE_D = (170, 138, 84)
BAMBOO = (122, 176, 70); BAMBOO_D = (86, 138, 54)
GREEN_D = (36, 100, 66)

PROPS = []          # (name, biome, function)
CUR = None          # the Part being built


def prop(name, biome):
    def deco(fn):
        PROPS.append((name, biome, fn))
        return fn
    return deco


# ---- helpers (stage frame, current part) --------------------------------------------------------------------------
def bx(c, s, col, rot=(0, 0, 0), j=0.05):
    return dk.box(CUR, c, s, col, rot=rot, jitter=j)


def cy(c, r, h, col, axis='y', verts=8, top=None, rot=(0, 0, 0), j=0.05):
    return dk.cyl(CUR, c, r, h, col, axis=axis, verts=verts, top_radius=top, rot=rot, jitter=j)


def cn(base, r, h, col, verts=7, j=0.06):
    return dk.cone(CUR, base, r, h, col, verts=verts, jitter=j)


def lump(c, r, col, sc=(1, 1, 1), amp=0.16, floor=False, j=0.07, rot=(0, 0, 0), up=0.0, subdiv=2):
    """Irregular low-poly blob: ico sphere with jittered vertices. floor: flattened at y=0. up: lighter on top faces."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.scale(bm, vec=(sc[0], sc[2], sc[1]), verts=bm.verts)
    for v in bm.verts:
        v.co += Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * r * amp
        if floor:
            v.co.z = max(v.co.z, -c[1])
    o = dk._object(CUR, "Lump", bm, dk.S(*c), rot, col, j)
    if up:
        attr = o.data.color_attributes.get("Col")
        for poly in o.data.polygons:
            k = 1.0 + up * max(0.0, poly.normal.z)
            for li in poly.loop_indices:
                cc = attr.data[li].color
                attr.data[li].color = (min(1, cc[0] * k), min(1, cc[1] * k), min(1, cc[2] * k), 1)
    return o


def limb(a, b, r0, r1, col, verts=6, j=0.05):
    """Tapered cylinder from stage point a (radius r0) to b (radius r1)."""
    A, B = Vector(dk.S(*a)), Vector(dk.S(*b))
    d = B - A
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r0, radius2=r1, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    return dk._object(CUR, "Limb", bm, (A + B) / 2, (0, 0, 0), col, j)


def frond(base, yaw, length, width, rise, droop, col, j=0.08):
    """Double sided leaf blade (palm frond, bamboo/grass leaf). yaw in degrees about up."""
    cs, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    loc = [(0, 0, 0), (.35, -.5, 1), (.35, .5, 1), (.72, -.36, .7), (.72, .36, .7), (1, 0, 0)]

    def pt(u, v, h):
        U, V = u * length, v * width
        hh = rise * math.sin(h * 1.3) - droop * (u ** 2)
        return (base[0] + U * cs - V * sn, base[1] + hh, base[2] + U * sn + V * cs)
    pts = [pt(*q) for q in loc]
    tris = [(0, 1, 2), (1, 3, 4), (1, 4, 2), (3, 5, 4)]
    bm = bmesh.new()
    for flip in (False, True):
        vs = [bm.verts.new((p[0], p[2], p[1])) for p in pts]
        for t in tris:
            bm.faces.new([vs[i] for i in (reversed(t) if flip else t)])
    return dk._object(CUR, "Frond", bm, Vector((0, 0, 0)), (0, 0, 0), col, j)


def torus(c, Rm, r, col, segs=9, sides=4, rot=(0, 0, 0), j=0.06):
    bm = bmesh.new()
    vs = []
    for i in range(segs):
        a = 2 * pi * i / segs
        row = []
        for k in range(sides):
            b = 2 * pi * k / sides + pi / sides
            rr = Rm + r * math.cos(b)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        vs.append(row)
    for i in range(segs):
        for k in range(sides):
            bm.faces.new([vs[i][k], vs[(i + 1) % segs][k], vs[(i + 1) % segs][(k + 1) % sides], vs[i][(k + 1) % sides]])
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return dk._object(CUR, "Torus", bm, dk.S(*c), rot, col, j)


def blade(base, h, r, col, lean=(0, 0), j=0.1):
    """Grass blade: thin 3 sided cone leaning by lean=(dx, dz)."""
    return limb(base, (base[0] + lean[0], base[1] + h, base[2] + lean[1]), r, 0.0, col, verts=3, j=j)


def tuft(n, rad, hmin, hmax, cols, base_r=0.28, cx=0.0, cz=0.0):
    for i in range(n):
        a = R.uniform(0, 2 * pi)
        d = R.uniform(0, rad)
        h = R.uniform(hmin, hmax)
        lean = R.uniform(0.2, 0.9)
        blade((cx + math.cos(a) * d, 0, cz + math.sin(a) * d), h, base_r, R.choice(cols),
              (math.cos(a) * lean * h * 0.35, math.sin(a) * lean * h * 0.35))


def fence_posts_rails(length, height, post_w, rails, col, post_col, post_h=None):
    h = post_h or height
    for x in (-length / 2 + post_w / 2, length / 2 - post_w / 2):
        bx((x, h / 2, 0), (post_w, h, post_w), post_col)
    for y in rails:
        bx((0, y, 0), (length - post_w, 0.45, 0.35), col)


# ===================================================================================================================
# SUBURBAN / PARK
# ===================================================================================================================
@prop("OakA", "suburban")
def oakA():
    limb((0, 0, 0), (0.2, 7.5, 0), 1.5, 0.9, BARK, 6)
    limb((0.1, 5.5, 0), (-3, 8.5, 1), 0.6, 0.35, BARK_D, 5)
    lump((0, 11.5, 0), 6.2, LEAF, (1, .85, 1), up=0.25)
    lump((-4, 9.5, 1.6), 4.4, LEAF_D, up=0.2)
    lump((4, 10, -1.2), 4.6, LEAF, up=0.2)
    lump((0.6, 15.2, 0.4), 4.2, LEAF_L, (1, .9, 1), up=0.3)
    lump((-1.2, 10.2, -4), 3.6, LEAF_D, up=0.2)


@prop("OakB", "suburban")
def oakB():
    limb((0, 0, 0), (-0.8, 5, 0.4), 1.3, 1.0, BARK, 6)
    limb((-0.8, 5, 0.4), (0.8, 10, -0.4), 1.0, 0.7, BARK, 6)
    limb((0, 8.4, 0), (3.2, 12, 1), 0.5, 0.3, BARK_D, 5)
    lump((0.6, 14, -0.4), 4.8, LEAF_D, (1, 1.1, 1), up=0.25)
    lump((3.6, 11.8, 1), 3.6, LEAF, up=0.25)
    lump((-3.2, 12.4, -.6), 3.8, LEAF, up=0.25)
    lump((0.4, 18, 0), 3.5, LEAF_L, (1, 1, 1), up=0.3)


@prop("Birch", "suburban")
def birch():
    limb((0, 0, 0), (0.3, 10, 0.1), 0.85, 0.5, WHITE, 6, j=0.04)
    limb((0.3, 8, 0.1), (2.2, 12, 0), 0.35, 0.2, WHITE, 5)
    for y in (1.8, 4.3, 6.8, 9.0):
        cy((0.05 + y * 0.03, y, 0.0), 0.9 - y * 0.035, 0.45, IRON_D, verts=6, j=0.1)
    lump((0.6, 13, 0), 4, LEAF_L, (0.9, 1.15, 0.9), up=0.25)
    lump((2.6, 12, 0.5), 2.6, LEAF_Y, up=0.25)
    lump((-1.6, 15, -0.5), 2.8, LEAF_L, up=0.3)
    lump((0.8, 17, 0.2), 2.2, LEAF_Y, up=0.3)


def pine_tiers(tiers, base_col, cap=None, tilt=0.0):
    for i, (y, r, h) in enumerate(tiers):
        o = cn((tilt * y, y, 0), r, h, base_col[i % len(base_col)], verts=7)
        if cap:
            cn((tilt * y, y + h * 0.42, 0), r * 0.6, h * 0.58, cap, verts=7, j=0.03)


@prop("Pine", "suburban")
def pine():
    limb((0, 0, 0), (0, 5, 0), 0.9, 0.6, BARK_D, 5)
    pine_tiers([(3, 5.6, 6.5), (7, 4.5, 6), (11, 3.3, 5.5), (15, 2.1, 5.5)], (PINE, PINE_D, PINE_L, PINE))


@prop("PineSmall", "suburban")
def pineSmall():
    limb((0, 0, 0), (0, 3, 0), 0.8, 0.5, BARK_D, 5)
    pine_tiers([(2, 4.2, 5), (5, 3.2, 4.6), (8, 2.0, 4.6)], (PINE_L, PINE, PINE_D), tilt=0.04)


@prop("Bush", "suburban")
def bush():
    lump((0, 1.7, 0), 2.4, LEAF, (1.15, .9, 1), floor=True, up=0.3)
    lump((-1.8, 1.3, 0.8), 1.8, LEAF_D, floor=True, up=0.3)
    lump((1.6, 1.4, -0.7), 2.0, LEAF_L, floor=True, up=0.3)


@prop("BushFlowers", "suburban")
def bushFlowers():
    lump((0, 1.6, 0), 2.3, LEAF_D, (1.2, .9, 1), floor=True, up=0.25)
    lump((1.8, 1.2, 0.6), 1.7, LEAF, floor=True, up=0.25)
    lump((-1.6, 1.2, -0.6), 1.7, LEAF, floor=True, up=0.25)
    for i, col in enumerate([PINK, PINK, PINK_L, YEL, PINK, PINK_L, PINK, YEL]):
        a = i * 2.4
        d = 1.0 + (i % 3) * 0.5
        bx((math.cos(a) * d, 2.6 + 0.4 * math.sin(i) + (0.4 if d < 1.5 else 0), math.sin(a) * d * 0.7),
           (0.6, 0.6, 0.6), col, rot=(R.uniform(0, 40), R.uniform(0, 90), R.uniform(0, 40)))


@prop("FlowerPatch", "suburban")
def flowerPatch():
    cy((0, 0.12, 0), 2.1, 0.24, LEAF_D, verts=9, j=0.1)
    cols = [PINK, YEL, WHITE, PURPLE, PINK_L, RED, YEL, WHITE, PINK, PURPLE]
    for i, col in enumerate(cols):
        a = i * 2.39
        d = 0.5 + (i * 0.37) % 1.4
        x, z = math.cos(a) * d, math.sin(a) * d
        blade((x, 0.1, z), 0.9, 0.12, LEAF, (0.1, 0.1), j=0.05)
        bx((x, 1.15, z), (0.65, 0.4, 0.65), col, rot=(0, R.uniform(0, 90), 0))


@prop("Hedge", "suburban")
def hedge():
    bx((0, 1.4, 0), (6.4, 2.8, 2.2), LEAF_D, j=0.1)
    bx((0, 1.4, 0), (6.6, 2.0, 1.8), LEAF_D, j=0.1)
    bx((0, 2.9, 0), (6.0, 0.5, 2.0), LEAF, j=0.1)
    lump((-1.8, 2.8, 0), 1.3, LEAF_L, (1.2, .7, 1), amp=0.1, up=0.2)
    lump((1.9, 2.8, 0), 1.3, LEAF, (1.2, .7, 1), amp=0.1, up=0.2)


@prop("PicketFenceSegment", "suburban")
def picketFence():
    for x in (-3.8, 3.8):
        bx((x, 2.0, 0), (0.7, 4.0, 0.7), WOOD_W)
        cn((x, 4.0, 0), 0.5, 0.6, WOOD_W, verts=4, j=0.03)
    for y in (1.0, 2.5):
        bx((0, y, -0.25), (8, 0.45, 0.3), WOOD_W, j=0.03)
    for i in range(8):
        x = -3.15 + i * 0.9
        bx((x, 1.65, 0.1), (0.62, 3.3, 0.25), WHITE, j=0.03)
        dk.prism(CUR, (x, 3.3, 0.1), 0.62, 0.25, 0.4, WHITE, ridge='z', jitter=0.03)


@prop("PicketFencePost", "suburban")
def picketPost():
    bx((0, 2.1, 0), (0.9, 4.2, 0.9), WOOD_W)
    cn((0, 4.2, 0), 0.75, 0.9, WHITE, verts=4, j=0.03)
    bx((0, 3.4, 0), (1.0, 0.25, 1.0), WOOD_L)


@prop("LampPost", "suburban")
def lampPost():
    cy((0, 0.6, 0), 1.0, 1.2, IRON, verts=8)
    cy((0, 6, 0), 0.38, 10.5, IRON_D, verts=6, top=0.3)
    bx((0, 10.9, 0), (1.9, 0.4, 1.9), IRON)
    bx((0, 12, 0), (1.4, 2.0, 1.4), (255, 232, 160), j=0.03)
    cn((0, 13, 0), 1.7, 1.1, IRON, verts=4, j=0.03)
    bx((0, 8.5, 0), (1.5, 0.3, 0.3), IRON)


@prop("StumpLog", "suburban")
def stumpLog():
    cy((-1.2, 1.1, 0), 2.1, 2.2, BARK, verts=9, top=1.9)
    cy((-1.2, 2.25, 0), 1.7, 0.12, WOOD_L, verts=9, j=0.04)
    cy((2.8, 0.9, 1.8), 0.95, 4.6, BARK, axis='x', verts=7, rot=(0, 35, 0))
    cy((2.8, 0.9, 1.8), 0.78, 4.7, WOOD_L, axis='x', verts=7, rot=(0, 35, 0), j=0.03)
    cy((2.8, 0.9, 1.8), 0.97, 4.0, BARK, axis='x', verts=7, rot=(0, 35, 0))


@prop("GardenGnome", "suburban")
def gnome():
    bx((0, 0.4, 0), (1.5, 0.8, 1.3), STONE)
    cy((0, 1.8, 0), 1.0, 2.0, BLUE, verts=7, top=0.7)
    bx((0, 1.5, 0.75), (0.5, 0.4, 0.25), WOOD_D, j=0.03)
    lump((0, 3.15, 0.1), 0.62, (240, 190, 160), floor=False, amp=0.04)
    cn((0.0, 2.7, 0.35), 0.75, 1.5, WHITE, verts=6, j=0.03)
    cn((0.0, 3.4, 0), 0.8, 1.7, RED, verts=6, j=0.03)


@prop("GrassTuftA", "suburban")
def grassA():
    tuft(9, 0.7, 1.4, 2.4, (LEAF, LEAF_L, LEAF_D))


@prop("GrassTuftB", "suburban")
def grassB():
    tuft(14, 1.3, 1.2, 3.0, (LEAF_Y, LEAF, LEAF_L), base_r=0.3)


# ===================================================================================================================
# BEACH
# ===================================================================================================================
def palm(lean, height, nfr, seed_yaw, trunk_col=(150, 112, 74)):
    pts = []
    for i in range(6):
        t = i / 5
        pts.append((lean * t * t, height * t, 0.3 * math.sin(t * 3) * lean * 0.2))
    for i in range(5):
        a, b = pts[i], pts[i + 1]
        limb(a, b, 1.1 - i * 0.12, 1.0 - (i + 1) * 0.12, trunk_col if i % 2 == 0 else (130, 96, 62), 6)
    top = pts[-1]
    for i in range(nfr):
        yaw = seed_yaw + i * 360 / nfr + R.uniform(-12, 12)
        frond((top[0], top[1] + 0.2, top[2]), yaw, R.uniform(7.0, 8.5), 1.7, R.uniform(3.0, 4.5), R.uniform(2.2, 3.4),
              R.choice([LEAF, LEAF_D, LEAF_L]))
    for k in range(3):
        a = k * 2.1
        lump((top[0] + math.cos(a) * 0.8, top[1] - 0.6, math.sin(a) * 0.8), 0.55, (110, 76, 44), amp=0.05)


@prop("PalmA", "beach")
def palmA():
    palm(4.5, 16, 9, 10)


@prop("PalmB", "beach")
def palmB():
    palm(-2.6, 12.5, 8, 40, (160, 122, 80))


@prop("Beachgrass", "beach")
def beachgrass():
    tuft(12, 1.1, 2.4, 4.4, ((178, 186, 92), (150, 170, 80), (200, 196, 110)), base_r=0.26)


@prop("Driftwood", "beach")
def driftwood():
    limb((-3.2, 0.5, 0), (0.5, 1.0, 0.8), 0.7, 0.55, DRIFT, 6)
    limb((0.5, 1.0, 0.8), (3.4, 0.55, -0.4), 0.55, 0.35, DRIFT, 6)
    limb((-1, 0.8, 0.3), (-0.2, 2.4, 1.6), 0.3, 0.12, (150, 134, 112), 5)
    limb((1.5, 0.9, 0.5), (2.4, 2.0, 1.8), 0.25, 0.1, (150, 134, 112), 5)
    lump((-3.3, 0.5, 0), 0.7, (196, 180, 156), amp=0.05)


@prop("ShellRock", "beach")
def shellRock():
    lump((0, 1.0, 0), 1.7, (190, 182, 170), (1.2, .75, 1), floor=True, up=0.25)
    lump((2.4, .6, 1.0), 0.9, (170, 164, 152), floor=True, up=0.2)
    cy((-1.8, 0.28, 1.6), 1.0, 0.5, PINK_L, verts=8, top=0.75, rot=(0, 0, 8))
    cy((-1.8, 0.58, 1.6), 0.5, 0.2, PINK_D, verts=6, top=0.3, rot=(0, 0, 8))
    cy((1.2, 0.2, -1.8), 0.6, 0.35, CREAM, verts=7, top=0.45)


@prop("Towel", "beach")
def towel():
    cols = (RED, WHITE, RED, WHITE, RED)
    for i, c in enumerate(cols):
        bx((-1.2 + i * 0.6, 0.12, 0), (0.6, 0.24, 6), c, rot=(0, 6, 0), j=0.03)
    bx((0, 0.34, 2.3), (3, 0.12, 0.35), YEL, rot=(0, 6, 0), j=0.03)


@prop("SandcastleSmall", "beach")
def sandcastle():
    bx((0, 0.7, 0), (5, 1.4, 4.4), SAND_D)
    bx((0, 1.7, 0), (3.2, 0.8, 2.4), SAND)
    for sx, sz in ((-2.0, -1.7), (2.0, -1.7), (-2.0, 1.7), (2.0, 1.7)):
        cy((sx, 1.7, sz), 0.7, 2.4, SAND_L, verts=7, top=0.6)
        cn((sx, 2.8, sz), 0.85, 1.0, RED, verts=7, j=0.03)
    cy((0, 3.3, 0), 0.75, 3.2, SAND_L, verts=7, top=0.6)
    cn((0, 4.9, 0), 0.95, 1.1, RED, verts=7, j=0.03)
    bx((0.0, 6.2, 0), (0.12, 1.6, 0.12), WOOD_D, j=0.02)
    bx((0.5, 6.7, 0), (1.0, 0.6, 0.1), YEL, j=0.02)


@prop("Crate", "beach")
def crate():
    bx((0, 1.5, 0), (3, 3, 3), WOOD_L, j=0.08)
    for sx in (-1.4, 1.4):
        for sz in (-1.4, 1.4):
            bx((sx, 1.5, sz), (0.35, 3.1, 0.35), WOOD_D)
    bx((0, 0.25, 0), (3.1, 0.35, 3.1), WOOD_D)
    bx((0, 2.85, 0), (3.1, 0.35, 3.1), WOOD_D)
    bx((0, 1.5, 1.52), (2.4, 0.3, 0.12), WOOD_L, rot=(0, 0, 38))


# ===================================================================================================================
# CITY / MODERN
# ===================================================================================================================
@prop("ChainFenceSegment", "city")
def chainFence():
    for x in (-3.9, 3.9):
        cy((x, 2.2, 0), 0.22, 4.4, STEEL, verts=6)
    cy((0, 4.35, 0), 0.18, 7.8, STEEL, axis='x', verts=6)
    cy((0, 0.35, 0), 0.14, 7.8, STEEL, axis='x', verts=5)
    for i in range(9):
        bx((-3.6 + i * 0.9, 2.35, 0), (0.1, 3.9, 0.1), GREY_L, j=0.03)
    for y in (1.1, 2.3, 3.5):
        bx((0, y, 0), (7.6, 0.1, 0.1), GREY_L, j=0.03)


@prop("TrafficCone", "city")
def trafficCone():
    bx((0, 0.15, 0), (2.0, 0.3, 2.0), IRON_D)
    cy((0, 1.35, 0), 0.8, 2.1, ORANGE, verts=8, top=0.18)
    cy((0, 1.6, 0), 0.6, 0.55, WHITE, verts=8, top=0.5, j=0.02)


@prop("Barrel", "city")
def barrel():
    cy((0, 1.6, 0), 1.3, 3.2, RED, verts=10, top=1.3)
    for y in (0.5, 2.7):
        cy((0, y, 0), 1.36, 0.28, RED_D, verts=10, j=0.03)
    cy((0, 3.22, 0), 1.0, 0.08, GREY_D, verts=10, j=0.03)


@prop("Dumpster", "city")
def dumpster():
    bx((0, 1.9, 0), (6, 3.0, 3.0), (60, 150, 100))
    bx((0, 0.4, 0), (6.2, 0.4, 3.2), IRON_D)
    bx((0, 3.55, 0.7), (6.2, 0.3, 1.9), (30, 86, 56), rot=(0, 0, 0))
    bx((0, 3.9, -0.85), (6.2, 0.3, 1.7), (30, 86, 56), rot=(22, 0, 0))
    for sx in (-2.4, 2.4):
        cy((sx, 0.35, 1.5), 0.45, 0.35, IRON, axis='z', verts=6)
    bx((0, 2.3, 1.52), (4.2, 0.18, 0.1), YEL, j=0.03)


@prop("StreetLamp", "city")
def streetLamp():
    cy((0, 0.5, 0), 0.9, 1.0, GREY_D, verts=8)
    limb((0, 0.8, 0), (0, 13, 0), 0.42, 0.28, GREY, 6)
    limb((0, 13, 0), (1.6, 14.1, 0), 0.28, 0.22, GREY, 5)
    limb((1.6, 14.1, 0), (3.5, 14.1, 0), 0.22, 0.22, GREY, 5)
    bx((3.7, 13.9, 0), (2.4, 0.6, 1.1), GREY_D)
    bx((3.7, 13.5, 0), (1.8, 0.2, 0.8), (255, 236, 170), j=0.03)


@prop("PlanterBox", "city")
def planter():
    bx((0, 0.9, 0), (4.2, 1.8, 2.2), (150, 150, 146))
    bx((0, 1.82, 0), (3.6, 0.2, 1.6), (84, 60, 40), j=0.08)
    lump((-0.9, 2.6, 0), 1.1, LEAF, floor=False, up=0.3)
    lump((0.9, 2.5, 0.1), 1.0, LEAF_L, floor=False, up=0.3)
    for x, c in ((-1.4, PINK), (0, YEL), (1.5, RED), (0.5, PINK_L)):
        bx((x, 3.0 + (x % 0.3), 0.3 - x * 0.1), (0.5, 0.5, 0.5), c, rot=(0, 30, 0))


@prop("Hydrant", "city")
def hydrant():
    cy((0, 1.4, 0), 0.75, 2.8, RED, verts=8, top=0.65)
    cy((0, 0.2, 0), 1.0, 0.4, RED_D, verts=8)
    lump((0, 3.0, 0), 0.8, RED_D, (1, .7, 1), amp=0.03)
    cy((0, 3.5, 0), 0.25, 0.4, STEEL, verts=6)
    cy((0, 1.9, 0), 0.4, 2.1, RED, axis='x', verts=6)
    cy((0.0, 1.9, 0.8), 0.32, 0.4, STEEL, axis='z', verts=6)


# ===================================================================================================================
# WESTERN
# ===================================================================================================================
@prop("CactusA", "western")
def cactusA():
    cy((0, 3.8, 0), 1.2, 7.6, CACT, verts=7, top=1.0)
    lump((0, 7.7, 0), 1.0, CACT, amp=0.04, subdiv=2)
    limb((1, 3.2, 0), (3.2, 3.4, 0), 0.62, 0.6, CACT_D, 6)
    limb((3.2, 3.4, 0), (3.4, 6.4, 0), 0.6, 0.5, CACT_D, 6)
    limb((-1, 4.6, 0), (-2.6, 4.8, 0.2), 0.55, 0.5, CACT, 6)
    limb((-2.6, 4.8, 0.2), (-2.7, 6.6, 0.2), 0.5, 0.42, CACT, 6)
    bx((0, 7.9, 0.9), (0.4, 0.4, 0.4), PINK)


@prop("CactusB", "western")
def cactusB():
    lump((0, 1.7, 0), 2.0, CACT, (1, .95, 1), floor=True, amp=0.05)
    lump((2.4, 1.0, 1.0), 1.1, CACT_D, floor=True, amp=0.05)
    lump((-1.8, 0.8, 1.6), 0.9, CACT, floor=True, amp=0.05)
    for a in range(6):
        bx((math.cos(a) * 0.6, 3.5 - 0.1 * (a % 2), math.sin(a) * 0.6), (0.45, 0.4, 0.45), (250, 190, 60 + a * 20),
           rot=(0, a * 30, 0))


@prop("Haystack", "western")
def haystack():
    cy((0, 1.3, 0), 3.2, 2.6, STRAW_D, verts=10, top=3.1)
    lump((0, 2.4, 0), 3.2, STRAW, (1, 0.85, 1), floor=False, amp=0.05, subdiv=2, up=0.3)
    cy((0, 4.5, 0), 0.25, 1.2, STRAW_D, verts=5, top=0.05)
    cy((0, 0.1, 0), 3.4, 0.2, (150, 110, 60), verts=10, j=0.1)
    bx((3.6, 0.3, 1.6), (1.6, 0.5, 0.5), STRAW, rot=(0, 25, 8))


@prop("WoodFenceSegment", "western")
def woodFence():
    for x, h in ((-3.7, 3.7), (3.7, 3.3), (0, 3.5)):
        bx((x, h / 2, 0), (0.7, h, 0.7), WOOD_D, rot=(0, R.uniform(-10, 10), R.uniform(-2, 2)), j=0.1)
    for y, tilt in ((1.1, 1.5), (2.0, -1.2), (2.9, 2.0)):
        bx((0, y, 0.45), (8.2, 0.5, 0.3), WOOD, rot=(0, 0, tilt), j=0.1)


@prop("Tumbleweed", "western")
def tumbleweed():
    lump((0, 1.9, 0), 1.9, TUMBLE, floor=False, amp=0.12, up=0.1)
    lump((0.2, 1.9, 0), 1.4, (150, 110, 70), amp=0.12)
    for i in range(9):
        a = i * 0.7
        limb((0, 1.9, 0), (math.cos(a) * 2.3, 1.9 + math.sin(i * 1.7) * 1.6, math.sin(a) * 2.3), 0.12, 0.05, (120, 88, 56), 3)
    cy((0, 0.05, 0), 0.01, 0.01, TUMBLE, verts=3)


@prop("DeadTree", "western")
def deadTree():
    limb((0, 0, 0), (0.4, 5, 0), 1.2, 0.8, (120, 108, 94), 6)
    limb((0.4, 5, 0), (-0.6, 10, 0.5), 0.8, 0.5, (130, 118, 100), 6)
    limb((-0.6, 10, 0.5), (0.2, 13.5, 0), 0.5, 0.15, (130, 118, 100), 5)
    limb((0.3, 6, 0), (3.8, 8.6, 0.5), 0.5, 0.18, (110, 98, 84), 5)
    limb((2.4, 7.6, 0.3), (3.6, 10.8, 0), 0.25, 0.1, (110, 98, 84), 4)
    limb((-0.2, 8, 0.2), (-3.4, 10.2, -0.4), 0.4, 0.14, (110, 98, 84), 5)
    limb((-2.0, 9.2, -0.2), (-3.4, 12.2, 0.4), 0.22, 0.08, (110, 98, 84), 4)


@prop("RockRed", "western")
def rockRed():
    cy((0, 1.2, 0), 3.3, 2.4, MESA_D, verts=7, top=2.9, rot=(0, 15, 0), j=0.1)
    cy((0.2, 3.1, 0), 2.7, 1.5, MESA, verts=6, top=2.3, rot=(0, 40, 0), j=0.1)
    cy((0.3, 4.5, 0), 2.2, 1.4, MESA_L, verts=6, top=1.7, rot=(0, 10, 0), j=0.1)
    cy((0.3, 5.3, 0), 1.6, 0.3, (200, 150, 100), verts=6, top=1.2, j=0.08)
    lump((3.8, .9, 1.6), 1.3, MESA_D, floor=True, up=0.2)


# ===================================================================================================================
# HARBOR / PIRATE
# ===================================================================================================================
@prop("RopeCoil", "harbor")
def ropeCoil():
    for i in range(3):
        torus((0, 0.45 + i * 0.7, 0), 1.7 - i * 0.12, 0.38, ROPE if i % 2 == 0 else ROPE_D, segs=9, sides=4, rot=(0, 0, i * 20))
    limb((1.6, 0.4, 0), (3.4, 0.35, 1.2), 0.3, 0.28, ROPE, 4)
    limb((3.4, 0.35, 1.2), (4.2, 0.35, 0.2), 0.28, 0.25, ROPE_D, 4)


@prop("CratesStack", "harbor")
def cratesStack():
    bx((-1.6, 1.4, 0), (2.8, 2.8, 2.8), WOOD, rot=(0, 4, 0), j=0.08)
    bx((1.8, 1.4, 0.3), (2.8, 2.8, 2.8), WOOD_D, rot=(0, -6, 0), j=0.08)
    bx((0.1, 4.2, 0.1), (2.7, 2.7, 2.7), WOOD_L, rot=(0, 24, 0), j=0.08)
    for (x, z, ry) in ((-1.6, 0, 4), (1.8, 0.3, -6)):
        bx((x, 1.4, z), (3.0, 0.3, 3.0), WOOD_D, rot=(0, ry, 0))
    bx((0.1, 4.2, 0.1), (2.9, 0.3, 2.9), WOOD_D, rot=(0, 24, 0))


@prop("BarrelStack", "harbor")
def barrelStack():
    for (x, z) in ((-1.3, 0), (1.3, 0.2)):
        cy((x, 1.6, z), 1.2, 3.2, WOOD, verts=9, top=1.2)
        for y in (0.5, 2.7):
            cy((x, y, z), 1.26, 0.25, IRON, verts=9, j=0.03)
    cy((0, 4.8, 0.1), 1.2, 3.2, WOOD_L, axis='x', verts=9, rot=(0, 8, 0))
    for sx in (-1.0, 1.0):
        cy((sx, 4.8, 0.1), 1.26, 0.25, IRON, axis='x', verts=9, rot=(0, 8, 0), j=0.03)


@prop("Anchor", "harbor")
def anchor():
    bx((0, 3.2, 0), (0.7, 6, 0.7), IRON)
    bx((0, 5.0, 0), (3.2, 0.6, 0.6), IRON_D)
    torus((0, 6.6, 0), 0.7, 0.2, IRON, segs=8, sides=4, rot=(90, 0, 0))
    limb((0, 0.4, 0), (-2.8, 1.9, 0), 0.4, 0.4, IRON, 5)
    limb((0, 0.4, 0), (2.8, 1.9, 0), 0.4, 0.4, IRON, 5)
    cn((-2.9, 1.7, 0), 0.8, 1.2, IRON_D, verts=4, j=0.03)
    cn((2.9, 1.7, 0), 0.8, 1.2, IRON_D, verts=4, j=0.03)
    bx((0, 0.3, 0), (1.4, 0.6, 0.7), IRON_D)


@prop("NetPile", "harbor")
def netPile():
    lump((0, 0.8, 0), 2.4, (188, 164, 112), (1.3, .38, 1.1), floor=True, up=0.1, amp=0.08)
    lump((-1.4, 0.7, 0.8), 1.5, ROPE_D, (1.1, .5, 1), floor=True, amp=0.08)
    torus((0.8, 0.9, -0.6), 1.3, 0.14, ROPE_D, segs=8, sides=3, rot=(0, 0, 0))
    torus((-0.6, 0.95, 0.2), 0.9, 0.14, ROPE, segs=8, sides=3, rot=(0, 0, 0))
    lump((2.5, 0.5, 1.4), 0.5, ORANGE, floor=True, amp=0.03)
    lump((-2.6, 0.5, -1.2), 0.5, RED, floor=True, amp=0.03)
    lump((1.4, 0.5, -2.0), 0.5, YEL, floor=True, amp=0.03)


# ===================================================================================================================
# ASIA / NINJA
# ===================================================================================================================
@prop("BambooClump", "asia")
def bamboo():
    stalks = [(0, 0, 0.3, 0.1, 17), (1.0, 0.6, 1.4, 0.5, 14), (-0.9, 0.5, -1.2, 0.7, 15.5), (0.3, -1.0, 0.2, -1.4, 12.5),
              (-0.2, 1.1, -0.4, 1.6, 13.5)]
    for (x, z, dx, dz, h) in stalks:
        a, b = (x, 0, z), (x + dx, h, z + dz)
        limb(a, b, 0.5, 0.36, BAMBOO if h > 14 else BAMBOO_D, 5, j=0.06)
        for t in (0.35, 0.7):
            cy((x + dx * t, h * t, z + dz * t), 0.55 - 0.1 * t, 0.3, (96, 148, 56), verts=5, j=0.05)
        for k in range(2):
            frond((b[0], b[1] - 1.5 - k, b[2]), R.uniform(0, 360), 3.4, 0.9, 0.8, 1.6, BAMBOO if k else (96, 168, 72))


@prop("SakuraTree", "asia")
def sakura():
    limb((0, 0, 0), (-0.8, 4.5, 0.2), 1.3, 0.9, BARK_D, 6)
    limb((-0.8, 4.5, 0.2), (0.8, 8, 0), 0.9, 0.6, BARK_D, 6)
    limb((-0.4, 6, 0.1), (-3.6, 9, 0.8), 0.5, 0.3, BARK_D, 5)
    limb((0.4, 7, 0), (3.6, 9.6, -0.6), 0.5, 0.3, BARK_D, 5)
    lump((0.6, 11.2, 0), 5.2, PINK, (1.1, .8, 1.1), up=0.25)
    lump((-3.8, 9.8, 0.8), 3.4, PINK_L, up=0.25)
    lump((3.8, 10.4, -0.6), 3.5, PINK_D, up=0.25)
    lump((0.2, 13.8, 0.2), 3.2, PINK_L, up=0.3)


@prop("StoneLantern", "asia")
def stoneLantern():
    bx((0, 0.4, 0), (2.4, 0.8, 2.4), STONE_D)
    cy((0, 2.0, 0), 0.5, 2.4, STONE, verts=6)
    cy((0, 3.5, 0), 1.1, 0.5, STONE_L, verts=6, top=1.5)
    bx((0, 4.6, 0), (2.2, 1.7, 2.2), STONE)
    bx((0, 4.6, 0.0), (2.22, 0.8, 1.0), (255, 224, 150), j=0.03)
    bx((0, 4.6, 0.0), (1.0, 0.8, 2.22), (255, 224, 150), j=0.03)
    dk.prism(CUR, (0, 5.5, 0), 4.2, 4.2, 1.6, STONE_D, ridge='x', jitter=0.05)
    lump((0, 7.0, 0), 0.5, STONE_L, amp=0.03)


@prop("LowFenceSegment", "asia")
def lowFence():
    for x in (-3.7, 0, 3.7):
        cy((x, 1.5, 0), 0.32, 3.0, BAMBOO_D, verts=5)
        cy((x, 3.05, 0), 0.34, 0.2, (92, 62, 40), verts=5, j=0.03)
    for y in (0.8, 2.0):
        cy((0, y, 0.38), 0.24, 8.0, BAMBOO, axis='x', verts=5)
    for i in range(7):
        x = -3.0 + i * 1.0
        if abs(x) < 0.4:
            continue
        cy((x, 1.4, -0.1), 0.15, 2.8, BAMBOO_D, verts=4)


@prop("ZenRock", "asia")
def zenRock():
    cy((0, 0.1, 0), 4.0, 0.2, SAND_L, verts=14, j=0.05)
    torus((0, 0.22, 0), 3.0, 0.16, SAND, segs=12, sides=3, rot=(0, 0, 0))
    torus((0, 0.22, 0), 2.0, 0.16, SAND, segs=12, sides=3, rot=(0, 0, 0))
    lump((-0.4, 1.8, 0), 1.8, STONE, (.9, 1.1, .8), floor=True, up=0.3, amp=0.12)
    lump((1.6, 0.9, 0.8), 1.0, STONE_D, floor=True, up=0.3, amp=0.12)
    lump((-1.8, 0.6, -1.0), 0.8, STONE_L, floor=True, up=0.2, amp=0.12)


# ===================================================================================================================
# VIKING / WINTER
# ===================================================================================================================
@prop("PineSnow", "viking")
def pineSnow():
    limb((0, 0, 0), (0, 4, 0), 0.9, 0.6, BARK_D, 5)
    pine_tiers([(2.6, 5.4, 6), (6.4, 4.2, 5.6), (10, 3.0, 5.2), (13.4, 1.9, 5)], (PINE_D, PINE, PINE_D, PINE), cap=SNOW)


@prop("RuneStoneSmall", "viking")
def runeStone():
    pts = [(-1.5, 0, -0.8), (1.5, 0, -0.8), (1.6, 0, 0.8), (-1.6, 0, 0.8), (-1.0, 4.6, -0.5), (0.7, 5.3, -0.5), (0.9, 4.8, 0.5),
           (-0.9, 4.2, 0.5)]
    dk.poly(CUR, (0, 0, 0), pts, [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0), (4, 7, 6, 5)],
            STONE, jitter=0.1)
    for (y, h, x, rz) in ((2.0, 1.4, -0.3, 0), (3.1, 0.9, 0.2, 0), (1.3, 0.7, 0.4, 0)):
        bx((x, y, 0.75), (0.3, h, 0.25), (150, 200, 240), j=0.03)
    bx((-0.1, 2.9, 0.75), (1.0, 0.28, 0.25), (150, 200, 240), rot=(0, 0, 32), j=0.03)
    bx((0.3, 2.3, 0.75), (1.0, 0.28, 0.25), (150, 200, 240), rot=(0, 0, -32), j=0.03)
    lump((2.2, 0.5, 0.8), 0.8, STONE_D, floor=True, up=0.3)


@prop("LogPile", "viking")
def logPile():
    spots = [(-1.6, 0.9, 0), (0, 0.9, 0), (1.6, 0.9, 0), (-0.8, 2.3, 0), (0.8, 2.3, 0), (0, 3.7, 0)]
    for i, (x, y, z) in enumerate(spots):
        ry = R.uniform(-6, 6)
        cy((x, y, z), 0.82, 5.0, BARK if i % 2 else BARK_L, axis='z', verts=6, rot=(0, ry, 0))
        cy((x, y, z + 2.5), 0.66, 0.1, WOOD_L, axis='z', verts=6, rot=(0, ry, 0), j=0.03)
        cy((x, y, z - 2.5), 0.66, 0.1, WOOD_L, axis='z', verts=6, rot=(0, ry, 0), j=0.03)


@prop("ShieldFence", "viking")
def shieldFence():
    for x in (-3.7, 3.7):
        bx((x, 2.0, 0), (0.6, 4.0, 0.6), WOOD_D)
        cn((x, 4.0, 0), 0.5, 0.5, WOOD_D, verts=4, j=0.03)
    bx((0, 1.0, -0.2), (8, 0.4, 0.35), WOOD)
    bx((0, 3.0, -0.2), (8, 0.4, 0.35), WOOD)
    for i, c in enumerate((RED, YEL, BLUE, WHITE)):
        x = -2.9 + i * 1.95
        cy((x, 2.0, 0.1), 1.0, 0.3, c, axis='z', verts=8)
        cy((x, 2.0, 0.33), 0.3, 0.2, STEEL, axis='z', verts=6, j=0.03)


# ===================================================================================================================
# ROCKS
# ===================================================================================================================
@prop("RockA", "rocks")
def rockA():
    lump((0, 1.5, 0), 2.1, STONE, (1, .8, .95), floor=True, up=0.35, amp=0.2)


@prop("RockB", "rocks")
def rockB():
    lump((0, 1.0, 0), 2.6, STONE, (1.2, .5, .85), floor=True, up=0.35, amp=0.2)
    lump((2.8, 0.6, 1.2), 1.2, STONE_D, floor=True, up=0.3, amp=0.2)


@prop("RockC", "rocks")
def rockC():
    lump((0, 2.2, 0), 1.9, STONE_D, (.75, 1.25, .8), floor=True, up=0.35, amp=0.22)
    lump((1.6, 0.9, 0.6), 1.2, STONE, floor=True, up=0.3, amp=0.2)
    lump((-1.4, 0.7, 0.8), 0.9, STONE_L, floor=True, up=0.3, amp=0.2)


@prop("BoulderA", "rocks")
def boulder():
    lump((0, 2.7, 0), 3.8, STONE, (1.1, .8, 1), floor=True, up=0.4, amp=0.18, subdiv=2)
    lump((3.6, 1.2, 1.4), 1.8, STONE_D, floor=True, up=0.3, amp=0.2)
    lump((-2.2, 0.8, 3.0), 1.2, STONE_L, floor=True, up=0.3, amp=0.2)


# ---- export + contact sheets ---------------------------------------------------------------------------------------
def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def label(text, pos, size=2.0):
    cu = bpy.data.curves.new("L", 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'CENTER'
    ob = bpy.data.objects.new("L", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    o = bpy.data.objects.new("Label", me)
    bpy.context.scene.collection.objects.link(o)
    o.location = pos
    dk._paint(o, (20, 20, 30))
    return o


def render_sheet(items, path, cols, width_px=2400, pitch=24.0, rowp=32.0):
    """items: [(name, preview_object, height)]; places them on a grid with Shiba-height bars and renders (ortho, 40 deg)."""
    rows = math.ceil(len(items) / cols)
    extras = []
    placed = []
    for i, (name, o, h) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = c * pitch, -r * rowp
        o.location = (x, y, 0)
        o.hide_render = False
        placed.append(o)
        extras.append(label(name, (x, y - 4.5, 0.05), 1.9))
    xmin, xmax = -pitch * 0.8, (cols - 1) * pitch + pitch * 0.6
    ymin, ymax = -(rows - 1) * rowp - 8, 14
    g = dk.ground(Vector((xmin, ymin, 0)), Vector((xmax, ymax, 0)), color=(214, 208, 192), margin=1.0)
    g.scale = (3, 3, 1)
    for r in range(rows):
        extras.append(dk.box(None, (-pitch * 0.55, 3, -r * rowp), (1.4, 6, 1.4), (250, 140, 30)))
    el = math.radians(40)
    W = xmax - xmin
    Hn = (ymax - ymin) * math.sin(el) + 24 * math.cos(el)
    aspect = W / Hn
    cam_data = bpy.data.cameras.new("C")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = W * 1.02
    cam = bpy.data.objects.new("C", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    tgt = Vector(((xmin + xmax) / 2, (ymin + ymax) / 2, 9))
    cam.location = tgt + Vector((0, -math.cos(el), math.sin(el))) * 500
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.clip_end = 3000
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = width_px, int(width_px / aspect * 1.02)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in extras + [g, cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in placed:
        o.hide_render = True

def main():
    out = (dk.args() or [os.path.join(HERE, "out")])[0]
    dk.start(out)
    bpy.context.scene.view_settings.view_transform = "Standard"
    global CUR
    manifest = []
    previews = []
    for name, biome, fn in PROPS:
        if ONLY and name not in ONLY:
            continue
        CUR = dk.Part(name)
        fn()
        mesh = dk.join(CUR.objs, name)
        mesh.data.transform(mesh.matrix_world)
        mesh.matrix_world = Matrix.Identity(4)
        bpy.context.view_layer.update()
        lo, hi = bounds(mesh)
        # origin at the bottom centre: shift so the footprint centre is x=z=0 and the lowest point y=0 (Blender z).
        cx, cyy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
        mesh.data.transform(Matrix.Translation((0, 0, -lo.z)))
        mesh.location = (0, 0, 0)
        bpy.context.view_layer.update()
        lo, hi = bounds(mesh)
        # preview copy (before the export mirror)
        prev = mesh.copy()
        prev.data = mesh.data.copy()
        bpy.context.scene.collection.objects.link(prev)
        prev.hide_render = True
        previews.append((name, prev, hi.z, biome))
        size = (round(hi.x - lo.x, 1), round(hi.z - lo.z, 1), round(hi.y - lo.y, 1))   # x, height, z (stage)
        tris = tri_count(mesh)
        manifest.append(dict(name=name, biome=biome, size=size, tris=tris))
        dk._mirror_x([mesh])
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)
        path = os.path.join(out, f"Scatter_{name}.fbx")
        bpy.ops.export_scene.fbx(filepath=path, **dk.EXPORT)
        bpy.data.objects.remove(mesh, do_unlink=True)
        print("PROP %-20s %-9s size(x,h,z)=%s tris=%d low=%.2f" % (name, biome, size, tris, lo.z))
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    write_readme(manifest)
    if os.environ.get("SC_NOSHEET"):
        return
    biomes = []
    for p in previews:
        if p[3] not in biomes:
            biomes.append(p[3])
    for b in biomes:
        items = [(n, o, h) for (n, o, h, bb) in previews if bb == b]
        render_sheet(items, os.path.join(out, f"contact_{b}.png"), cols=min(6, len(items)), width_px=2400)
    render_sheet([(n, o, h) for (n, o, h, bb) in previews], os.path.join(out, "contact_sheet.png"), cols=9, width_px=4200)


def write_readme(manifest):
    lines = ["# Scatter props", "",
             "Small single-mesh props the game duplicates with random rotation and scale to make stages feel organic",
             "(trees, fences, rocks, bushes, flowers, lamps...). Built by `build_scatter.py` on `../decor/decorkit.py`:", "",
             "    blender --background --factory-startup --python build_scatter.py -- C:/Dev/4M-tycoon/assets/models/scatter/out", "",
             "Output in `out/`: `Scatter_<Name>.fbx` (one mesh, flat vertex colours, no Neon, origin = bottom centre on the ground,",
             "units = studs, x mirrored on export like the decor), `manifest.json`, `contact_sheet.png` (all props, orange bar =",
             "Shiba height 6) and `contact_<biome>.png`. Self-review in `RATINGS.md`.", "",
             "Import: `assets/models/combine_for_import.py` includes `scatter/out` (one Import 3D for everything, see",
             "`assets/README.md`); each prop ends up as `Scatter_<Name>` in `ReplicatedStorage/Assets`. Or import single files",
             "and name them exactly like the file. Clone it, set a random `Yaw`, `Size`-scale 0.8-1.25 and tilt 0-6 degrees.", "",
             "| Name | Biome | Size x (width) | Height | Size z (depth) | Triangles |", "|---|---|---|---|---|---|"]
    for m in manifest:
        lines.append(f"| Scatter_{m['name']} | {m['biome']} | {m['size'][0]} | {m['size'][1]} | {m['size'][2]} | {m['tris']} |")
    lines += ["", "Biomes: suburban (parks, gardens), beach, city, western, harbor (pirate), asia (ninja), viking (winter), rocks (any)."]
    with open(os.path.join(HERE, "README.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


main()
