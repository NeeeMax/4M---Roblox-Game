"""Final low-poly decor models for the theme WesternSaloon (15 parts around the Cowboy Shiba of bay 7).

Usage: blender --background --factory-startup --python build_WesternSaloon.py -- <absolute outdir> [PartId,PartId,...]
Writes Decor_WesternSaloon_<PartId>.fbx, preview_<PartId>.png and stage_WesternSaloon.png into <outdir>.
Every model is fitted to the union box of its blueprint pieces (same footprint, same height). Everything is built in the
STAGE FRAME (x right, y up, z toward the road); text and signs are flat decals that face +z and read correctly from the road.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
KEY = "WesternSaloon"
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", KEY))
ONLY = ARGS[1].split(",") if len(ARGS) > 1 else None
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_WesternSaloon.json"))
RND = random.Random(5)

# ---- palette (one for the whole theme) --------------------------------------------------------------------------------
SAND = (214, 178, 120)
SAND_B = (206, 168, 110)
SAND_C = (222, 188, 132)
SAND2 = (198, 158, 102)
PLANK = (184, 138, 88)
PLANK2 = (170, 124, 78)
PLANK3 = (196, 150, 98)
WOOD = (140, 96, 60)
DWOOD = (92, 62, 40)
VDWOOD = (62, 42, 30)
CREAM = (238, 222, 186)
RED = (172, 54, 42)
DRED = (128, 38, 32)
BRICK = (150, 70, 52)
STONE = (176, 160, 140)
STONE2 = (156, 142, 124)
DSTONE = (120, 108, 96)
SSTONE = (204, 176, 134)
ROCK = (190, 98, 62)
ROCK2 = (214, 128, 80)
ROCKD = (150, 72, 48)
ROCKL = (230, 152, 102)
IRON = (66, 68, 76)
DIRON = (44, 44, 52)
STEEL = (150, 154, 164)
GOLD = (240, 190, 50)
DGOLD = (200, 150, 30)
GREEN = (86, 140, 72)
DGREEN = (62, 106, 56)
TEAL = (58, 128, 128)
DTEAL = (40, 96, 98)
BLACK = (34, 30, 32)
GLASS = (44, 62, 84)
GLASSL = (96, 132, 160)
WHITE = (240, 236, 226)
ORANGE = (236, 120, 40)
YELLOW = (250, 210, 70)
PINK = (226, 110, 140)
BLUE = (60, 120, 190)
LEATHER = (112, 70, 44)
HORSE1 = (130, 82, 48)
HORSE1D = (88, 54, 32)
HORSE2 = (236, 230, 220)


# ---- geometry helpers -------------------------------------------------------------------------------------------------
def rg(a, b):
    return (min(a, b), max(a, b))


def bx(p, x, y, z, col, jit=0.05, rot=(0, 0, 0), bot=False):
    """Box from ranges (min, max) in stage axes. The bottom face is dropped (never seen) unless bot=True or it is rotated."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(s[0], s[2], s[1]), verts=bm.verts)
    if not bot and tuple(rot) == (0, 0, 0):
        low = [f for f in bm.faces if f.calc_center_median().z < -1e-6]
        bmesh.ops.delete(bm, geom=low, context='FACES_ONLY')
    return dk._object(p, "Box", bm, S(*c), rot, col, jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.05):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=10, jit=0.05):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.05):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit)


def ball(p, c, r, col, sc=(1, 1, 1), subdiv=1, jit=0.06):
    return dk.ball(p, c, r, col, scale=sc, subdiv=subdiv, jitter=jit)


def slant(p, a, b, z, t, depth, col, jit=0.05):
    """Bar in the x-y plane from a=(x, y) to b=(x, y), thickness t, extent `depth` along z centred on z."""
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def beam(p, a, b, t, col, jit=0.04, t2=None):
    """Square bar between two 3D stage points, thickness t (tapering to t2 at b)."""
    A, B2 = S(*a), S(*b)
    d = B2 - A
    L = d.length
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    t2 = t if t2 is None else t2
    for v in bm.verts:
        k = v.co.z + 0.5
        w = t + (t2 - t) * k
        v.co = q @ Vector((v.co.x * w, v.co.y * w, v.co.z * L)) + (A + B2) / 2
    return dk._object(p, "Beam", bm, Vector((0, 0, 0)), (0, 0, 0), col, jit)


def quads(p, items, col, jit=0.0, name="Q"):
    """Flat faces: items = [(points in stage axes, wanted outward normal)]. One object per colour."""
    if not items:
        return None
    bm = bmesh.new()
    for pts, nrm in items:
        P = [S(*q) for q in pts]
        n = (P[1] - P[0]).cross(P[2] - P[0])
        want = Vector((nrm[0], nrm[2], nrm[1]))
        if n.dot(want) < 0:
            P = P[::-1]
        bm.faces.new([bm.verts.new(v) for v in P])
    return dk._object(p, name, bm, Vector((0, 0, 0)), (0, 0, 0), col, jit)


def fr(p, axis, pos, rects, col, sign=1, jit=0.0):
    """Flat rectangles on a plane. axis 'z': rects (x0, x1, y0, y1) at z=pos; 'x': (z0, z1, y0, y1) at x=pos;
    'y': (x0, x1, z0, z1) at y=pos. sign = which way they face."""
    items = []
    for a0, a1, b0, b1 in rects:
        if axis == 'z':
            pts, n = [(a0, b0, pos), (a1, b0, pos), (a1, b1, pos), (a0, b1, pos)], (0, 0, sign)
        elif axis == 'x':
            pts, n = [(pos, b0, a0), (pos, b0, a1), (pos, b1, a1), (pos, b1, a0)], (sign, 0, 0)
        else:
            pts, n = [(a0, pos, b0), (a1, pos, b0), (a1, pos, b1), (a0, pos, b1)], (0, sign, 0)
        items.append((pts, n))
    return quads(p, items, col, jit)


def tri(p, pts, nrm, col):
    """One flat triangle (or polygon) with a wanted normal."""
    return quads(p, [(pts, nrm)], col)


def band(p, cx, y0, y1, cz, r, col, verts=8, jit=0.04):
    """Open tube (sides only), e.g. a barrel hoop."""
    bm = bmesh.new()
    vs = []
    for k in range(verts):
        a = 2 * math.pi * k / verts
        vs.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    for k in range(verts):
        a, b = vs[k], vs[(k + 1) % verts]
        v = [bm.verts.new((a[0], a[1], y0)), bm.verts.new((b[0], b[1], y0)),
             bm.verts.new((b[0], b[1], y1)), bm.verts.new((a[0], a[1], y1))]
        bm.faces.new(v)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc on an open tube may point inwards: force outward
    for f in bm.faces:
        c = f.calc_center_median()
        if (Vector((c.x - cx, c.y - cz, 0))).dot(f.normal) < 0:
            f.normal_flip()
    return dk._object(p, "Band", bm, Vector((0, 0, 0)), (0, 0, 0), col, jit)


def ring(p, cx, cz, y0, y1, ro, ri, col, colin, coltop, colwater=None, wy=None, verts=10, jit=0.06):
    """Open-topped round wall (a well, a trough): outer wall, inner wall, top rim and an optional water disc."""
    pts = [(2 * math.pi * k / verts) for k in range(verts)]
    o = lambda a, r, y: (cx + r * math.cos(a), y, cz + r * math.sin(a))
    outer, inner, top = [], [], []
    for k in range(verts):
        a, b = pts[k], pts[(k + 1) % verts]
        m = (a + b) / 2
        outer.append(([o(a, ro, y0), o(b, ro, y0), o(b, ro, y1), o(a, ro, y1)], (math.cos(m), 0, math.sin(m))))
        inner.append(([o(a, ri, y0), o(b, ri, y0), o(b, ri, y1), o(a, ri, y1)], (-math.cos(m), 0, -math.sin(m))))
        top.append(([o(a, ro, y1), o(b, ro, y1), o(b, ri, y1), o(a, ri, y1)], (0, 1, 0)))
    quads(p, outer, col, jit)
    quads(p, inner, colin, jit)
    quads(p, top, coltop, jit)
    if colwater:
        quads(p, [([o(a, ri, wy) for a in pts], (0, 1, 0))], colwater, 0.0)


def deck(p, x0, x1, y0, y1, z0, z1, cols, step, sidecol, along='x', jit=0.04):
    """Flat slab with a plank-pattern top (alternating colours); no bottom face. along='x': boards run along x."""
    fr(p, 'z', z1, [(x0, x1, y0, y1)], sidecol, 1, jit)
    fr(p, 'z', z0, [(x0, x1, y0, y1)], sidecol, -1, jit)
    fr(p, 'x', x0, [(z0, z1, y0, y1)], sidecol, -1, jit)
    fr(p, 'x', x1, [(z0, z1, y0, y1)], sidecol, 1, jit)
    groups = {}
    if along == 'x':
        n = max(1, round((z1 - z0) / step))
        for i in range(n):
            groups.setdefault(cols[i % len(cols)], []).append((x0, x1, z0 + (z1 - z0) * i / n, z0 + (z1 - z0) * (i + 1) / n))
    else:
        n = max(1, round((x1 - x0) / step))
        for i in range(n):
            groups.setdefault(cols[i % len(cols)], []).append((x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n, z0, z1))
    for col, rects in groups.items():
        fr(p, 'y', y1, rects, col, 1, jit)


def hlines(p, axis, pos, a0, a1, ys, th, col, sign=1):
    fr(p, axis, pos, [(a0, a1, y, y + th) for y in ys], col, sign)


def frange(a, b, step):
    out, v = [], a
    while v < b - 1e-6:
        out.append(v)
        v += step
    return out


def rock(p, cx, y0, cz, sx, sy, sz, col, rot=0, subdiv=1):
    """Faceted boulder sitting on y0 (ico sphere stretched to the given full size)."""
    o = ball(p, (cx, y0 + sy * 0.4, cz), 0.5, col, sc=(sx, sy * 0.8 / 1.0 * 1.0, sz), subdiv=subdiv, jit=0.1)
    if rot:
        o.rotation_euler[2] = math.radians(rot)
    return o


# ---- block font (5 x 5), flat quads facing +z ---------------------------------------------------------------------------
FONT = {
    'S': ["XXXXX", "X....", "XXXXX", "....X", "XXXXX"],
    'A': [".XXX.", "X...X", "XXXXX", "X...X", "X...X"],
    'L': ["X....", "X....", "X....", "X....", "XXXXX"],
    'O': ["XXXXX", "X...X", "X...X", "X...X", "XXXXX"],
    'N': ["X...X", "XX..X", "X.X.X", "X..XX", "X...X"],
    'B': ["XXXX.", "X...X", "XXXX.", "X...X", "XXXX."],
    'K': ["X...X", "X..X.", "XXX..", "X..X.", "X...X"],
    'T': ["XXXXX", "..X..", "..X..", "..X..", "..X.."],
    'W': ["X...X", "X...X", "X.X.X", "XX.XX", "X...X"],
    'J': ["....X", "....X", "....X", "X...X", ".XXX."],
    'I': ["XXXXX", "..X..", "..X..", "..X..", "XXXXX"],
    'M': ["X...X", "XX.XX", "X.X.X", "X...X", "X...X"],
    'E': ["XXXXX", "X....", "XXXX.", "X....", "XXXXX"],
    'R': ["XXXX.", "X...X", "XXXX.", "X..X.", "X...X"],
}


def glyph_rects(ch, x0, ytop, cell):
    rows = FONT[ch]
    runs = []
    for r, row in enumerate(rows):
        c = 0
        while c < 5:
            if row[c] == 'X':
                c1 = c
                while c1 + 1 < 5 and row[c1 + 1] == 'X':
                    c1 += 1
                runs.append((r, c, c1))
                c = c1 + 1
            else:
                c += 1
    merged = []
    for r, c0, c1 in runs:
        for m in merged:
            if m[1] == c0 and m[2] == c1 and m[3] == r - 1:
                m[3] = r
                break
        else:
            merged.append([r, c0, c1, r])
    return [(x0 + c0 * cell, x0 + (c1 + 1) * cell, ytop - (r1 + 1) * cell, ytop - r0 * cell) for r0, c0, c1, r1 in merged]


def text_rects(txt, cx, ytop, cell, gap=1, space=3):
    cur, placed = 0, []
    for ch in txt:
        if ch == ' ':
            cur += space
            continue
        placed.append((ch, cur))
        cur += 5 + gap
    total = cur - gap
    x0 = cx - total * cell / 2
    rects = []
    for ch, c in placed:
        rects += glyph_rects(ch, x0 + c * cell, ytop, cell)
    return rects, total * cell


def put_text(p, txt, cx, ytop, cell, z, col, sign=1):
    rects, w = text_rects(txt, cx, ytop, cell)
    fr(p, 'z', z, rects, col, sign)
    return w


def star(p, cx, cy, z0, z1, ro, ri, col):
    pts, faces = [], []
    zc, d = (z0 + z1) / 2, (z1 - z0) / 2
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = ro if k % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), d))
    for k in range(10):
        pts.append((pts[k][0], pts[k][1], -d))
    pts += [(cx, cy, d), (cx, cy, -d)]
    for k in range(10):
        n = (k + 1) % 10
        faces += [(20, k, n), (21, 10 + n, 10 + k), (k, 10 + k, 10 + n, n)]
    return dk.poly(p, (0, 0, zc), pts, faces, col, 0.03)


def arch_prism(p, x0, x1, zc, y0, a, h, col, n=8, jit=0.04):
    """Half-ellipse tunnel along x (canvas wagon cover): half width a (z), height h, from x0 to x1, base at y0."""
    ring0, ring1 = [], []
    for i in range(n + 1):
        t = math.pi * i / n
        ring0.append((x0, y0 + h * math.sin(t), zc + a * math.cos(t)))
        ring1.append((x1, y0 + h * math.sin(t), zc + a * math.cos(t)))
    pts = ring0 + ring1
    m = n + 1
    faces = []
    for i in range(n):
        faces.append((i, i + 1, m + i + 1, m + i))
    faces.append(tuple(range(m)))
    faces.append(tuple(range(m, 2 * m)))
    faces.append((0, m, m + n, n))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)



# ======================================================================================================================
# 1. Floor: Dusty Main Street (a thin dust slab under the whole town + boardwalks; everything stays below 0.3 studs and
#    the slab below the game's walkway at 0.1, so the walkway stays visible)
# ======================================================================================================================
def hexa(p, cx, cz, rx, rz, y, col, rot=0.0, n=6):
    pts = []
    for k in range(n):
        a = rot + 2 * math.pi * k / n
        pts.append((cx + rx * math.cos(a), y, cz + rz * math.sin(a)))
    return quads(p, [(pts, (0, 1, 0))], col)


def ribbon(p, pts, w, y, col):
    """A flat ribbon of width w along a polyline (x, z), mitred at the corners."""
    n = len(pts)

    def unit(a, b):
        dx, dz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dz)
        return dx / ln, dz / ln

    left, right = [], []
    for i in range(n):
        if i == 0:
            d = unit(pts[0], pts[1])
            nx, nz, m = -d[1], d[0], 1.0
        elif i == n - 1:
            d = unit(pts[-2], pts[-1])
            nx, nz, m = -d[1], d[0], 1.0
        else:
            d1, d2 = unit(pts[i - 1], pts[i]), unit(pts[i], pts[i + 1])
            n1, n2 = (-d1[1], d1[0]), (-d2[1], d2[0])
            sx, sz = n1[0] + n2[0], n1[1] + n2[1]
            sl = math.hypot(sx, sz)
            nx, nz = sx / sl, sz / sl
            m = 1.0 / max(0.45, nx * n1[0] + nz * n1[1])
        o = w / 2 * m
        left.append((pts[i][0] + nx * o, max(-63.9, min(63.9, pts[i][1] + nz * o))))
        right.append((pts[i][0] - nx * o, max(-63.9, min(63.9, pts[i][1] - nz * o))))
    items = []
    for i in range(n - 1):
        items.append(([(left[i][0], y, left[i][1]), (right[i][0], y, right[i][1]), (right[i + 1][0], y, right[i + 1][1]),
                       (left[i + 1][0], y, left[i + 1][1])], (0, 1, 0)))
    quads(p, items, col, 0.02)


def build_Floor(p):
    x0, x1, z0, z1, th = -94, 94, -64, 64, 0.06
    nx, nz = 16, 10
    cols = [SAND, (210, 174, 116), (218, 182, 124), SAND, (208, 172, 114)]
    groups = {}
    for i in range(nx):
        for j in range(nz):
            c = cols[(i * 7 + j * 13 + (i * j) % 5) % len(cols)]
            groups.setdefault(c, []).append((x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx,
                                             z0 + (z1 - z0) * j / nz, z0 + (z1 - z0) * (j + 1) / nz))
    for c, rs in groups.items():
        fr(p, 'y', th, rs, c, 1, 0.02)
    fr(p, 'z', z1, [(x0, x1, 0, th)], SAND2, 1)
    fr(p, 'z', z0, [(x0, x1, 0, th)], SAND2, -1)
    fr(p, 'x', x0, [(z0, z1, 0, th)], SAND2, -1)
    fr(p, 'x', x1, [(z0, z1, 0, th)], SAND2, 1)
    r = random.Random(3)
    # soft dirt patches, dry grass patches, cracks and pebbles (flat decals only)
    for k in range(26):
        cx, cz = r.uniform(-80, 80), r.uniform(-54, 54)
        c = r.choice([SAND_C, (226, 192, 138), (205, 168, 112), (196, 156, 102)])
        hexa(p, cx, cz, r.uniform(4, 11), r.uniform(3, 7), th + 0.006 + 0.002 * (k % 3), c, r.uniform(0, 1))
    for k in range(14):
        cx, cz = r.uniform(-84, 84), r.uniform(-56, 56)
        hexa(p, cx, cz, r.uniform(2, 4.5), r.uniform(1.4, 3), th + 0.012, r.choice([(168, 160, 92), (150, 150, 84)]), r.uniform(0, 1), 7)
    for k in range(40):
        cx, cz = r.uniform(-86, 80), r.uniform(-60, 56)
        ln = r.uniform(2.5, 7)
        if r.random() < 0.5:
            fr(p, 'y', th + 0.016, [(cx, cx + ln, cz, cz + 0.16)], (170, 130, 84))
        else:
            fr(p, 'y', th + 0.016, [(cx, cx + 0.16, cz, cz + ln)], (170, 130, 84))
    for k in range(46):
        cx, cz = r.uniform(-90, 90), r.uniform(-61, 61)
        hexa(p, cx, cz, r.uniform(0.25, 0.6), r.uniform(0.2, 0.45), th + 0.02, r.choice([STONE, STONE2, ROCKD, DSTONE]), r.uniform(0, 1), 5)
    # red-rock dust near the mesa and the mine
    for (x0, x1, z0, z1) in ((54, 86, 30, 56), (-86, -50, -56, -28)):
        for k in range(9):
            hexa(p, r.uniform(x0, x1), r.uniform(z0, z1), r.uniform(3, 8), r.uniform(2.5, 6), th + 0.008 + 0.002 * (k % 3),
                 r.choice([(206, 150, 106), (198, 140, 98), (214, 160, 116)]), r.uniform(0, 1), 7)
    # the packed-earth trail under the walkway (the game lays its own, narrower walkway on top)
    pts = [(q[0], max(-63.9, min(63.9, q[1]))) for q in BP["Path"]]
    ribbon(p, pts, 15.5, th + 0.012, (226, 194, 142))
    ribbon(p, pts, 12.6, th + 0.016, (214, 180, 128))
    # boardwalks (from the blueprint: the 0.3 high pieces)
    fl = dk.blueprint_part(BP, "Floor")
    for q in fl["Pieces"]:
        if abs(q["Size"][1] - 0.3) < 1e-6:
            cx, _, cz = q["Offset"]
            sx, _, sz = q["Size"]
            deck(p, cx - sx / 2, cx + sx / 2, 0, 0.3, cz - sz / 2, cz + sz / 2, [PLANK, PLANK2, PLANK3, PLANK2], 1.5, DWOOD, along='z')
            # nail heads / dark gaps between the boards
            gaps = [(cx - sx / 2 + 1.5 * k - 0.04, cx - sx / 2 + 1.5 * k + 0.04, cz - sz / 2, cz + sz / 2) for k in range(1, round(sx / 1.5))]
            fr(p, 'y', 0.305, gaps, VDWOOD)


# ======================================================================================================================
# 2. Saloon: Rusty Spur Saloon
# ======================================================================================================================
def barrel(p, x, y0, z, r=1.15, h=2.8):
    vcyl(p, x, y0, y0 + h, z, r, PLANK2, verts=8, jit=0.1)
    band(p, x, y0 + 0.35, y0 + 0.55, z, r + 0.04, DIRON, 8)
    band(p, x, y0 + h - 0.55, y0 + h - 0.35, z, r + 0.04, DIRON, 8)


def rg2(a, b, c, d):
    return (min(a, b), max(a, b), c, d)


def window(p, cx, y0, y1, hw, z, sign=1, shutters=True, sill=True, mull=True):
    """Front window: dark glass, cream frame and mullions as flat decals, optional shutters and sill (wall front at z)."""
    s = sign
    fr(p, 'z', z + 0.03 * s, [(cx - hw, cx + hw, y0, y1)], GLASS, s)
    fr(p, 'z', z + 0.03 * s, [(cx - hw + 0.4, cx - hw + 1.2, y0 + 0.5, y1 - 0.5)], GLASSL, s)
    ft = 0.32
    fr(p, 'z', z + 0.045 * s, [(cx - hw - ft, cx + hw + ft, y1, y1 + ft), (cx - hw - ft, cx + hw + ft, y0 - ft, y0),
                               (cx - hw - ft, cx - hw, y0, y1), (cx + hw, cx + hw + ft, y0, y1)], CREAM, s)
    if mull:
        fr(p, 'z', z + 0.045 * s, [(cx - 0.12, cx + 0.12, y0, y1), (cx - hw, cx + hw, (y0 + y1) / 2 - 0.12, (y0 + y1) / 2 + 0.12)], CREAM, s)
    if sill:
        bx(p, (cx - hw - 0.6, cx + hw + 0.6), (y0 - 0.55, y0 - 0.05), (z, z + 0.55 * s), CREAM)
    if shutters:
        for sx in (-1, 1):
            xa = cx + sx * (hw + ft)
            fr(p, 'z', z + 0.035 * s, [rg2(xa, xa + sx * 1.6, y0 - 0.3, y1 + 0.3)], TEAL, s)
            fr(p, 'z', z + 0.04 * s, [rg2(xa + sx * 0.7, xa + sx * 0.9, y0 - 0.1, y1 + 0.1)], DTEAL, s)


def build_Saloon(p):
    # porch deck with the Shiba's spot on it
    deck(p, 22, 82, 0, 0.5, -31, -8, [PLANK, PLANK2, PLANK3, PLANK2], 1.5, DWOOD, 'x')
    # ground floor: rear block + front wall with the open swing-door gap
    bx(p, (24, 80), (0.5, 10), (-62, -32), PLANK2)
    bx(p, (24, 46.5), (0.5, 10), (-32, -30), PLANK)
    bx(p, (57.5, 80), (0.5, 10), (-32, -30), PLANK)
    bx(p, (46.5, 57.5), (8.6, 10), (-32, -30), PLANK)
    hlines(p, 'z', -29.97, 24, 46.5, frange(1.5, 9.9, 1.2), 0.1, (146, 104, 64))
    hlines(p, 'z', -29.97, 57.5, 80, frange(1.5, 9.9, 1.2), 0.1, (146, 104, 64))
    hlines(p, 'z', -29.97, 46.5, 57.5, [9.0, 9.9], 0.1, (146, 104, 64))
    # the dark room behind the swing doors with a bar and bottle shelves
    fr(p, 'z', -31.95, [(46.5, 57.5, 0.5, 8.6)], (40, 28, 26), 1)
    fr(p, 'z', -31.93, [(47.4, 56.6, 6.6, 7.8)], GLASSL, 1)
    bx(p, (46.8, 57.2), (0.5, 2.6), (-31.9, -31.1), DWOOD)
    bx(p, (46.8, 57.2), (2.6, 2.8), (-31.9, -30.9), WOOD)
    shelf_cols = [GREEN, GOLD, RED, BLUE, GOLD, GREEN, RED, BLUE]
    for k, c in enumerate(shelf_cols):
        xb = 47.6 + k * 1.08
        fr(p, 'z', -31.9, [(xb, xb + 0.5, 3.4, 4.6)], c, 1)
        fr(p, 'z', -31.9, [(xb + 0.1, xb + 0.6, 5.4, 6.4)], shelf_cols[(k + 3) % 8], 1)
    bx(p, (46.9, 57.1), (3.2, 3.4), (-31.95, -31.5), WOOD)
    bx(p, (46.9, 57.1), (5.2, 5.4), (-31.95, -31.5), WOOD)
    # swing doors
    for xa, xb in ((46.6, 51.95), (52.05, 57.4)):
        bx(p, (xa, xb), (2.0, 6.2), (-30.95, -30.7), TEAL, 0.05)
        hlines(p, 'z', -30.69, xa, xb, frange(2.2, 6.0, 0.5), 0.14, DTEAL)
    # door frame
    bx(p, (45.9, 46.6), (0.5, 9.2), (-30.4, -29.8), CREAM)
    bx(p, (57.4, 58.1), (0.5, 9.2), (-30.4, -29.8), CREAM)
    bx(p, (45.9, 58.1), (8.6, 9.2), (-30.4, -29.8), CREAM)
    # posters
    fr(p, 'z', -29.96, [(43.6, 45.0, 3.0, 5.2), (59.0, 60.4, 3.4, 5.4)], CREAM, 1)
    fr(p, 'z', -29.95, [(43.9, 44.7, 3.4, 3.8), (43.9, 44.7, 4.1, 4.9), (59.3, 60.1, 3.8, 4.2), (59.3, 60.1, 4.5, 5.1)], DRED, 1)
    for c in (34, 70):
        window(p, c, 3.4, 7.4, 4.6, -30)
    # upper floor
    bx(p, (25, 79), (10, 18), (-62, -30), PLANK)
    hlines(p, 'z', -29.97, 25, 79, frange(10.9, 17.9, 1.0), 0.1, (146, 104, 64))
    for c in (31, 43, 61, 73):
        window(p, c, 12.0, 16.4, 2.8, -30)
    fr(p, 'z', -29.96, [(49, 55, 10.2, 15.6)], (40, 28, 26), 1)
    fr(p, 'z', -29.95, [(49, 50.3, 11.4, 15.6), (53.7, 55, 11.4, 15.6)], RED, 1)
    fr(p, 'z', -29.94, [(48.6, 55.4, 15.6, 16.0), (48.6, 49, 10.2, 15.6), (55, 55.4, 10.2, 15.6)], CREAM, 1)
    # balcony
    deck(p, 26, 78, 9.8, 10.2, -30, -24, [PLANK, PLANK2, PLANK3, PLANK2], 1.5, DWOOD, 'x')
    bx(p, (26, 78), (11.5, 11.8), (-24.4, -24.0), DWOOD)
    bx(p, (26, 78), (10.2, 10.5), (-24.4, -24.0), DWOOD)
    for sx in (26, 77.6):
        bx(p, (sx, sx + 0.4), (11.5, 11.8), (-30, -24.4), DWOOD)
        bx(p, (sx, sx + 0.4), (10.2, 10.5), (-30, -24.4), DWOOD)
        for zb in (-28.4, -26.2):
            bx(p, (sx + 0.06, sx + 0.34), (10.5, 11.5), (zb, zb + 0.28), DWOOD)
    for k in range(11):
        xb = 26.4 + k * 5.1
        bx(p, (xb, xb + 0.28), (10.5, 11.5), (-24.34, -24.06), DWOOD)
    for x in (28, 40, 64, 76):
        vcyl(p, x, 0.5, 9.8, -25.5, 0.4, DWOOD, verts=6, jit=0.07)
    # roof
    deck(p, 23, 81, 18, 18.7, -63.5, -30.5, [DWOOD, (104, 72, 46), (84, 56, 36)], 3.0, VDWOOD, 'z')
    bx(p, (66, 70), (18.7, 23.4), (-58, -54), BRICK)
    bx(p, (65.6, 70.4), (23.4, 24.0), (-58.4, -53.6), DSTONE)
    # false front with the big sign
    bx(p, (25, 79), (18.7, 23.0), (-30.6, -29.4), PLANK)
    bx(p, (31, 73), (23.0, 26.3), (-30.6, -29.4), PLANK)
    bx(p, (30.6, 73.4), (26.3, 26.7), (-30.9, -29.1), DWOOD)
    bx(p, (24.6, 79.4), (22.6, 23.0), (-30.9, -29.1), DWOOD)
    bx(p, (24.6, 25.8), (18.7, 22.6), (-30.9, -29.1), DWOOD)
    bx(p, (78.2, 79.4), (18.7, 22.6), (-30.9, -29.1), DWOOD)
    bx(p, (32, 72), (19.5, 25.0), (-29.4, -29.0), CREAM)
    fr(p, 'z', -28.98, [(32, 72, 24.65, 25.0), (32, 72, 19.5, 19.85), (32, 32.35, 19.85, 24.65), (71.65, 72, 19.85, 24.65)], DWOOD, 1)
    put_text(p, "SALOON", 52, 24.1, 0.74, -28.96, DRED)
    star(p, 35.4, 22.25, -29.0, -28.75, 1.45, 0.62, GOLD)
    star(p, 68.6, 22.25, -29.0, -28.75, 1.45, 0.62, GOLD)
    hlines(p, 'z', -29.37, 25.8, 31, frange(19.2, 22.5, 1.0), 0.09, (150, 108, 66))
    hlines(p, 'z', -29.37, 73, 78.2, frange(19.2, 22.5, 1.0), 0.09, (150, 108, 66))
    # side walls
    for xs, sg in ((24, -1), (80, 1)):
        hlines(p, 'x', xs + 0.0 * sg, -62, -32, frange(1.5, 9.9, 1.6), 0.1, (140, 98, 60), sg)
        for zc in (-39, -52):
            fr(p, 'x', xs + 0.03 * sg, [(zc - 2.4, zc + 2.4, 3.4, 7.4)], GLASS, sg)
            fr(p, 'x', xs + 0.04 * sg, [(zc - 0.12, zc + 0.12, 3.4, 7.4), (zc - 2.4, zc + 2.4, 5.3, 5.5)], CREAM, sg)
    for xs, sg in ((25, -1), (79, 1)):
        hlines(p, 'x', xs, -62, -30, frange(10.9, 17.9, 1.6), 0.1, (140, 98, 60), sg)
        for zc in (-39, -52):
            fr(p, 'x', xs + 0.03 * sg, [(zc - 2.4, zc + 2.4, 12.2, 16.2)], GLASS, sg)
            fr(p, 'x', xs + 0.04 * sg, [(zc - 0.12, zc + 0.12, 12.2, 16.2), (zc - 2.4, zc + 2.4, 14.1, 14.3)], CREAM, sg)
    # lanterns under the balcony
    for x in (38, 66):
        bx(p, (x - 0.06, x + 0.06), (8.4, 9.8), (-27.06, -26.94), DIRON)
        bx(p, (x - 0.45, x + 0.45), (7.6, 8.4), (-27.45, -26.55), CREAM)
        bx(p, (x - 0.6, x + 0.6), (8.4, 8.6), (-27.6, -26.4), DIRON)
        bx(p, (x - 0.6, x + 0.6), (7.4, 7.6), (-27.6, -26.4), DIRON)
    # porch furniture
    barrel(p, 25.6, 0.5, -11.5)
    barrel(p, 78.4, 0.5, -11.5)
    bx(p, (73.4, 76.2), (0.5, 2.5), (-12.9, -10.1), WOOD)
    hlines(p, 'z', -10.09, 73.4, 76.2, [1.2, 1.9], 0.1, DWOOD)
    for c in (34, 70):
        bx(p, (c - 4, c + 4), (1.3, 1.6), (-29.4, -28.2), WOOD)
        bx(p, (c - 3.7, c + 3.7), (0.5, 1.3), (-29.2, -28.4), DWOOD)


# ======================================================================================================================
# 3. Gate: Bonk Town Gate
# ======================================================================================================================
def build_Gate(p):
    for s in (-1, 1):
        x = 10.5 * s
        bx(p, (x - 1.8, x + 1.8), (0, 0.8), (56.5, 59.5), STONE, 0.08)
        bx(p, (x - 1.35, x + 1.35), (0.8, 1.3), (57, 59), STONE2, 0.08)
        vcyl(p, x, 1.3, 16, 58, 0.85, WOOD, verts=7, jit=0.08)
        bx(p, (x - 1.2, x + 1.2), (16.0, 17.3), (57, 59), DWOOD)
        # lantern on the post top
        bx(p, (x - 0.5, x + 0.5), (17.3, 18.3), (57.5, 58.5), CREAM)
        bx(p, (x - 0.7, x + 0.7), (18.3, 18.6), (57.3, 58.7), DIRON)
        bx(p, (x - 0.7, x + 0.7), (17.1, 17.3), (57.3, 58.7), DIRON)
    xcyl(p, -12.5, 12.5, 16.85, 58, 0.8, DWOOD, verts=8, jit=0.08)
    # sign board
    bx(p, (-9.5, 9.5), (10, 16), (57.7, 58.3), PLANK, 0.08)
    fr(p, 'z', 58.32, [(-9.5, 9.5, 15.6, 16.0), (-9.5, 9.5, 10.0, 10.4), (-9.5, -9.1, 10.4, 15.6), (9.1, 9.5, 10.4, 15.6)], DWOOD, 1)
    put_text(p, "BONK", 0, 15.0, 0.46, 58.34, DRED)
    put_text(p, "TOWN", 0, 12.45, 0.46, 58.34, DRED)
    for sx in (-8.4, 8.4):
        for yy in (10.8, 15.2):
            bx(p, (sx - 0.15, sx + 0.15), (yy - 0.15, yy + 0.15), (58.3, 58.45), DIRON)
    # longhorn skull on top
    ball(p, (0, 18.4, 58), 1.0, CREAM, sc=(1.25, 1.35, 1.2), subdiv=1, jit=0.05)
    bx(p, (-0.55, 0.55), (17.15, 18.0), (58.7, 59.45), CREAM)
    for s in (-1, 1):
        bx(p, (s * 0.35 - 0.2, s * 0.35 + 0.2), (18.4, 18.85), (59.1, 59.45), BLACK)
        beam(p, (s * 1.1, 18.15, 58), (s * 3.3, 18.0, 58), 0.5, CREAM, t2=0.35)
        beam(p, (s * 3.3, 18.0, 58), (s * 4.1, 19.4, 58), 0.35, CREAM, t2=0.15)
    # stars at the beam ends
    star(p, -11.5, 16.85, 58.8, 59.1, 1.0, 0.45, GOLD)
    star(p, 11.5, 16.85, 58.8, 59.1, 1.0, 0.45, GOLD)


# ======================================================================================================================
# 4. Jail: Sheriff's Office
# ======================================================================================================================
def build_Jail(p):
    # office
    bx(p, (-76, -60), (0, 8), (38, 52), PLANK)
    hlines(p, 'z', 52.03, -76, -60, frange(0.9, 8.0, 1.0), 0.1, (146, 104, 64))
    hlines(p, 'x', -76.03, 38, 52, frange(0.9, 8.0, 1.0), 0.1, (140, 98, 60), -1)
    # door
    bx(p, (-69.8, -69.2), (0, 5.9), (51.8, 52.25), CREAM)
    bx(p, (-66.8, -66.2), (0, 5.9), (51.8, 52.25), CREAM)
    bx(p, (-69.8, -66.2), (5.2, 5.9), (51.8, 52.25), CREAM)
    bx(p, (-69.2, -66.8), (0, 5.2), (51.85, 52.1), WOOD)
    fr(p, 'z', 52.12, [(-68.9, -67.1, 2.9, 4.9)], GLASS, 1)
    fr(p, 'z', 52.12, [(-68.9, -67.1, 0.4, 2.5)], (126, 84, 52), 1)
    bx(p, (-67.5, -67.2), (2.3, 2.6), (52.1, 52.3), GOLD)
    # windows with iron bars
    for c in (-73.4, -62.8):
        fr(p, 'z', 52.04, [(c - 1.5, c + 1.5, 2.8, 5.6)], GLASS, 1)
        fr(p, 'z', 52.05, [(c - 1.8, c + 1.8, 5.6, 5.9), (c - 1.8, c + 1.8, 2.5, 2.8), (c - 1.8, c - 1.5, 2.8, 5.6), (c + 1.5, c + 1.8, 2.8, 5.6)], CREAM, 1)
        fr(p, 'z', 52.07, [(c - 0.6, c - 0.4, 2.8, 5.6), (c + 0.4, c + 0.6, 2.8, 5.6)], DIRON, 1)
    fr(p, 'x', -76.04, [(44.5, 47.5, 2.8, 5.6)], GLASS, -1)
    fr(p, 'x', -76.05, [(45.9, 46.1, 2.8, 5.6)], CREAM, -1)
    fr(p, 'z', 52.05, [(-65.4, -64.2, 3.2, 5.0), (-61.8, -60.8, 3.0, 4.6)], CREAM, 1)
    fr(p, 'z', 52.06, [(-65.1, -64.5, 3.6, 3.9), (-65.1, -64.5, 4.2, 4.7), (-61.6, -61.0, 3.4, 3.7)], DRED, 1)
    star(p, -68, 6.7, 52.0, 52.3, 1.25, 0.55, GOLD)
    # roof + false front + sign
    deck(p, -76.75, -59.25, 8, 8.6, 37.25, 52.75, [DWOOD, (104, 72, 46), (84, 56, 36)], 1.6, VDWOOD, 'z')
    bx(p, (-76, -60), (8.6, 11.0), (51.2, 52.0), PLANK)
    bx(p, (-73.5, -62.5), (11.0, 11.8), (51.2, 52.0), PLANK)
    bx(p, (-73.9, -62.1), (11.8, 12.0), (51.0, 52.2), DWOOD)
    bx(p, (-76.2, -59.8), (10.7, 11.0), (51.0, 52.2), DWOOD)
    bx(p, (-73, -63), (9.2, 11.6), (52.0, 52.4), CREAM)
    fr(p, 'z', 52.42, [(-73, -63, 11.3, 11.6), (-73, -63, 9.2, 9.5)], DWOOD, 1)
    put_text(p, "JAIL", -68, 11.4, 0.4, 52.43, DRED)
    # chimney
    bx(p, (-73, -71), (8.6, 11.7), (40, 42), BRICK)
    bx(p, (-73.3, -70.7), (11.7, 12.0), (39.7, 42.3), DSTONE)
    hlines(p, 'z', 42.03, -73, -71, frange(9.2, 11.6, 0.8), 0.1, (118, 52, 40))
    # stone cell house
    bx(p, (-60, -50), (0, 7), (39, 51), STONE)
    joints = []
    rows = frange(0.0, 7.0, 0.9)
    for i, y in enumerate(rows):
        for k in range(3):
            xj = -60 + 1.7 + k * 3.3 + (1.6 if i % 2 else 0)
            if xj < -50.3:
                joints.append((xj, xj + 0.1, y, min(y + 0.9, 7.0)))
    fr(p, 'z', 51.03, joints, DSTONE, 1)
    hlines(p, 'z', 51.03, -60, -50, rows[1:], 0.08, DSTONE)
    fr(p, 'x', -49.97, [(z, z + 0.1, y, y + 0.9) for i, y in enumerate(rows) for z in (40.5 + (1.8 if i % 2 else 0), 44.1 + (1.8 if i % 2 else 0), 47.7 + (1.8 if i % 2 else 0)) if z < 50.8], DSTONE, 1)
    hlines(p, 'x', -49.97, 39, 51, rows[1:], 0.08, DSTONE)
    fr(p, 'z', 51.04, [(-58.2, -51.8, 2.4, 5.6)], (24, 22, 28), 1)
    for k in range(7):
        xb = -58.0 + k * 0.97
        bx(p, (xb, xb + 0.2), (2.4, 5.6), (51.0, 51.25), IRON, 0.03)
    bx(p, (-58.4, -51.6), (2.2, 2.45), (51.0, 51.3), STONE2)
    bx(p, (-58.4, -51.6), (5.6, 5.85), (51.0, 51.3), STONE2)
    bx(p, (-60.5, -49.5), (7.0, 7.6), (38.5, 51.5), DWOOD)
    # side door of the cell house
    fr(p, 'x', -49.95, [(43.5, 46.5, 0.0, 4.6)], DIRON, 1)
    fr(p, 'x', -49.94, [(44.0, 44.2, 0.2, 4.4), (45.8, 46.0, 0.2, 4.4), (43.5, 46.5, 2.2, 2.4)], STEEL, 1)


# ---- more helpers -------------------------------------------------------------------------------------------------------
def disc_z(p, cx, cy, z, r, col, sign=1, n=10, sx=1.0):
    pts = [(cx + r * sx * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n), z) for k in range(n)]
    return quads(p, [(pts, (0, 0, sign))], col)


def zband(p, cx, cy, z0, z1, r, col, verts=10, jit=0.03):
    """Open tube around the z axis (a boiler band)."""
    items = []
    for k in range(verts):
        a, b = 2 * math.pi * k / verts, 2 * math.pi * (k + 1) / verts
        m = (a + b) / 2
        pa = (cx + r * math.cos(a), cy + r * math.sin(a))
        pb = (cx + r * math.cos(b), cy + r * math.sin(b))
        items.append(([(pa[0], pa[1], z0), (pb[0], pb[1], z0), (pb[0], pb[1], z1), (pa[0], pa[1], z1)], (math.cos(m), math.sin(m), 0)))
    return quads(p, items, col, jit)


def cone_band(p, cx, cz, y0, y1, r0, r1, col, verts=10, jit=0.03):
    """Open tapered tube around the vertical axis (a teepee stripe, a hat band)."""
    items = []
    for k in range(verts):
        a, b = 2 * math.pi * k / verts, 2 * math.pi * (k + 1) / verts
        m = (a + b) / 2
        pts = [(cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)), (cx + r0 * math.cos(b), y0, cz + r0 * math.sin(b)),
               (cx + r1 * math.cos(b), y1, cz + r1 * math.sin(b)), (cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a))]
        items.append((pts, (math.cos(m), 0.2, math.sin(m))))
    return quads(p, items, col, jit)


def wheel_z(p, cx, cy, z0, z1, ro, ri, col, hub=None, spokes=2, verts=10, jit=0.03):
    """Wooden wheel standing in the x-y plane (axle along z): rim ring + hub + spokes."""
    items = []
    for k in range(verts):
        a, b = 2 * math.pi * k / verts, 2 * math.pi * (k + 1) / verts
        m = (a + b) / 2
        o0, o1 = (cx + ro * math.cos(a), cy + ro * math.sin(a)), (cx + ro * math.cos(b), cy + ro * math.sin(b))
        i0, i1 = (cx + ri * math.cos(a), cy + ri * math.sin(a)), (cx + ri * math.cos(b), cy + ri * math.sin(b))
        items.append(([(o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1)], (math.cos(m), math.sin(m), 0)))
        items.append(([(i0[0], i0[1], z0), (i1[0], i1[1], z0), (i1[0], i1[1], z1), (i0[0], i0[1], z1)], (-math.cos(m), -math.sin(m), 0)))
        items.append(([(o0[0], o0[1], z1), (o1[0], o1[1], z1), (i1[0], i1[1], z1), (i0[0], i0[1], z1)], (0, 0, 1)))
        items.append(([(o0[0], o0[1], z0), (o1[0], o1[1], z0), (i1[0], i1[1], z0), (i0[0], i0[1], z0)], (0, 0, -1)))
    quads(p, items, col, jit)
    zc = (z0 + z1) / 2
    for k in range(spokes):
        dk.box(p, (cx, cy, zc), (2 * ri, 0.26, (z1 - z0) * 0.7), col, rot=(0, 0, 180.0 * k / spokes), jitter=jit)
    if hub is not False:
        zcyl(p, cx, cy, z0 - 0.05, z1 + 0.05, max(0.35, ri * 0.2), hub or col, verts=6, jit=jit)


def wheel_x(p, cx, cy, cz, r, th, col, hub=None, verts=8):
    """Train wheel: a disc standing across the x axis (axle along x)."""
    xcyl(p, cx - th / 2, cx + th / 2, cy, cz, r, col, verts=verts, jit=0.03)
    if hub:
        xcyl(p, cx - th / 2 - 0.05, cx + th / 2 + 0.05, cy, cz, r * 0.38, hub, verts=6, jit=0.02)


def strata(p, x0, x1, y0, y1, z0, z1, cols, n, wob=0.3, seed=1):
    """A cliff made of n stacked boxes whose edges step in and out by up to wob (the first layer keeps the full footprint)."""
    r = random.Random(seed)
    h = (y1 - y0) / n
    for i in range(n):
        a = [0, 0, 0, 0] if i == 0 else [r.choice([0, 0.5, 1]) * wob for _ in range(4)]
        bx(p, (x0 + a[0], x1 - a[1]), (y0 + i * h, y0 + (i + 1) * h), (z0 + a[2], z1 - a[3]), cols[i % len(cols)], 0.05)


def butte(p, cx, cz, rx, rz, profile, seed=1, n=12, wob=0.05, cap=None, jit=0.06, gullies=0, gcol=(104, 46, 34)):
    """Irregular rocky butte. profile = [(y, radius factor, colour of the band that ends here)]; the first entry is the
    bottom ring (factor 1 reaches the full rx / rz on the four axes). Two entries with the same y make a ledge."""
    r = random.Random(seed)
    base = [1.0 if (k % (n // 4) == 0) else r.uniform(0.84, 1.0) for k in range(n)]
    prev, prev_w, prev_y, prev_f = None, None, None, None
    ring = None
    all_rings = []
    for j, (y, f, col) in enumerate(profile):
        if j == 0:
            w = base[:]
        elif y == prev_y:
            w = prev_w
        else:
            w = [base[k] * (1 + r.uniform(-wob, wob)) for k in range(n)]
        ring = [(cx + rx * f * w[k] * math.cos(2 * math.pi * k / n), y, cz + rz * f * w[k] * math.sin(2 * math.pi * k / n)) for k in range(n)]
        if prev is not None:
            items = []
            for k in range(n):
                k2 = (k + 1) % n
                m = 2 * math.pi * (k + 0.5) / n
                if y == prev_y:
                    nrm = (0, 1, 0) if f < prev_f else (0, -1, 0)
                else:
                    nrm = (math.cos(m), 0.1, math.sin(m))
                items.append(([prev[k], prev[k2], ring[k2], ring[k]], nrm))
            quads(p, items, col, jit)
        prev, prev_w, prev_y, prev_f = ring, w, y, f
        all_rings.append(ring)
    if gullies:
        ks = r.sample(range(n), min(gullies, n))
        items = []
        for k in ks:
            k2 = (k + 1) % n
            m = 2 * math.pi * (k + 0.5) / n
            fa = r.uniform(0.3, 0.45)
            fb = fa + r.uniform(0.1, 0.16)
            for j in range(1, len(all_rings)):
                if profile[j][0] == profile[j - 1][0]:
                    continue
                pts = []
                for jj, (ta, tb) in ((j - 1, (fa, fb)), (j, (fa, fb))):
                    ra, rb = all_rings[jj][k], all_rings[jj][k2]
                    pa = (ra[0] + (rb[0] - ra[0]) * ta, ra[1], ra[2] + (rb[2] - ra[2]) * ta)
                    pb = (ra[0] + (rb[0] - ra[0]) * tb, ra[1], ra[2] + (rb[2] - ra[2]) * tb)
                    pts.append((pa, pb))
                off = (math.cos(m) * 0.06, 0, math.sin(m) * 0.06)
                q = [pts[0][0], pts[0][1], pts[1][1], pts[1][0]]
                items.append(([(a[0] + off[0], a[1], a[2] + off[2]) for a in q], (math.cos(m), 0.1, math.sin(m))))
        quads(p, items, gcol, 0.03)
    if cap is not None:
        quads(p, [(ring, (0, 1, 0))], cap, 0.03)


def cracks(p, axis, pos, a0, a1, y0, y1, n, seed, sign=1, col=(112, 52, 38)):
    """Dark vertical cracks painted on a cliff face."""
    r = random.Random(seed)
    rects = []
    for _ in range(n):
        a = r.uniform(a0 + 0.5, a1 - 0.7)
        ya = r.uniform(y0, y1 - 2.5)
        rects.append((a, a + r.choice([0.14, 0.2, 0.26]), ya, min(y1, ya + r.uniform(2.0, 5.0))))
    fr(p, axis, pos, rects, col, sign)


def spires(p, items, cols, seed=1):
    """Small rock spikes: items = [(x, y0, z, radius, height)]."""
    r = random.Random(seed)
    for x, y0, z, rad, h in items:
        dk.cone(p, (x, y0, z), rad, h, r.choice(cols), verts=6, jitter=0.08)


# ======================================================================================================================
# 5. Horses: Hitching Rail
# ======================================================================================================================
def ext_xy(p, pts, z0, z1, col, jit=0.05):
    """Side-profile polygon (x, y) extruded along z from z0 to z1."""
    n = len(pts)
    P = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n)), tuple(range(n, 2 * n))]
    return dk.poly(p, (0, 0, 0), P, faces, col, jit)


def horse(p, cx, z, d, col, dark, muzzle, patches=False, saddle=False, roll=False, sock=CREAM):
    X = lambda dx: cx + d * dx

    def prof(pts):
        return [(X(x), y) for x, y in pts]

    def bxr(dx0, dx1, y0, y1, dz, c, jit=0.05, zc=None):
        zc = z if zc is None else zc
        return bx(p, rg(X(dx0), X(dx1)), (y0, y1), (zc - dz, zc + dz), c, jit)

    # body, neck and head as extruded side profiles
    ext_xy(p, prof([(-3.0, 2.9), (-3.15, 4.4), (-2.2, 4.9), (0.2, 4.75), (2.0, 5.05), (3.0, 4.7), (3.2, 3.5), (2.6, 2.3),
                    (0.5, 2.2), (-2.2, 2.5)]), z - 1.0, z + 1.0, col)
    ext_xy(p, prof([(2.4, 4.2), (2.4, 5.0), (3.3, 7.0), (4.1, 7.1), (4.2, 6.2), (3.5, 4.4)]), z - 0.5, z + 0.5, col)
    ext_xy(p, prof([(3.9, 7.15), (4.4, 7.1), (5.8, 6.2), (5.9, 5.55), (5.3, 5.45), (4.3, 6.0), (3.9, 6.4)]), z - 0.45, z + 0.45, col)
    bxr(5.2, 5.9, 5.5, 6.2, 0.4, muzzle)
    ext_xy(p, prof([(2.2, 4.9), (3.1, 7.05), (3.45, 7.05), (2.7, 4.8)]), z - 0.22, z + 0.22, dark)           # mane
    ext_xy(p, prof([(-3.0, 4.5), (-3.5, 4.3), (-3.9, 2.5), (-3.5, 2.3), (-3.1, 3.7)]), z - 0.25, z + 0.25, dark)  # tail
    for dx in (2.3, -2.3):
        for dz in (-0.55, 0.55):
            bxr(dx - 0.32, dx + 0.32, 0.4, 2.6, 0.28, col, zc=z + dz)
            bxr(dx - 0.36, dx + 0.36, 0.0, 0.4, 0.31, BLACK, zc=z + dz)
            if sock:
                bxr(dx - 0.34, dx + 0.34, 0.4, 1.1, 0.3, sock, jit=0.02, zc=z + dz)
    for dz in (-0.28, 0.28):
        bxr(3.9, 4.2, 6.95, 7.2, 0.1, dark, zc=z + dz)                      # ears
    for sg in (1, -1):
        fr(p, 'z', z + sg * 0.46, [rg2(X(5.0), X(5.2), 6.4, 6.6)], BLACK, sg)  # eye
        fr(p, 'z', z + sg * 0.46, [rg2(X(5.8), X(5.9), 5.65, 5.8)], BLACK, sg)  # nostril
    if patches:
        for sg in (1, -1):
            fr(p, 'z', z + sg * 1.02, [rg2(X(-2.6), X(-0.6), 3.0, 4.5), rg2(X(0.8), X(1.9), 2.9, 4.0)], (150, 98, 62), sg)
            fr(p, 'z', z + sg * 0.52, [rg2(X(2.5), X(3.2), 5.2, 6.4)], (150, 98, 62), sg)
    if roll:
        bxr(-1.0, 1.0, 4.8, 5.6, 0.85, RED)
        bxr(-1.1, -0.9, 4.8, 5.6, 0.9, CREAM)
        bxr(0.9, 1.1, 4.8, 5.6, 0.9, CREAM)
    if saddle:
        bxr(-0.95, 0.95, 4.8, 5.05, 1.1, RED)
        bxr(-0.8, 0.8, 5.05, 5.45, 0.8, LEATHER)
        bxr(0.45, 0.85, 5.45, 5.95, 0.32, LEATHER)
        bxr(-0.85, -0.5, 5.45, 5.8, 0.55, LEATHER)
        for sg in (-1, 1):
            bxr(-0.07, 0.07, 3.3, 4.8, 0.07, LEATHER, zc=z + sg * 1.04)
            bxr(-0.2, 0.2, 3.1, 3.35, 0.15, STEEL, zc=z + sg * 1.04)


def build_Horses(p):
    horse(p, 68, 8.6, 1, HORSE1, BLACK, (84, 56, 40), saddle=True)
    horse(p, 81, 8.6, -1, HORSE2, (150, 98, 62), (214, 190, 178), patches=True, roll=True, sock=None)
    for x in (62, 75, 88):
        bx(p, (x - 0.35, x + 0.35), (0, 3.4), (4.65, 5.35), DWOOD)
    bx(p, (61.5, 88.5), (2.7, 3.2), (4.75, 5.25), WOOD)
    bx(p, (61.5, 88.5), (1.5, 1.9), (4.8, 5.2), WOOD)
    # reins from the bridles to the rail
    beam(p, (73.2, 6.0, 8.6), (73.6, 3.0, 5.0), 0.14, LEATHER)
    beam(p, (75.9, 6.0, 8.6), (75.5, 3.0, 5.0), 0.14, LEATHER)
    # water trough
    bx(p, (72, 78), (0, 1.4), (1.4, 1.6), PLANK2)
    bx(p, (72, 78), (0, 1.4), (2.8, 3.0), PLANK2)
    bx(p, (72, 72.2), (0, 1.4), (1.6, 2.8), PLANK2)
    bx(p, (77.8, 78), (0, 1.4), (1.6, 2.8), PLANK2)
    bx(p, (72.2, 77.8), (0, 0.9), (1.6, 2.8), DWOOD)
    fr(p, 'y', 1.1, [(72.2, 77.8, 1.6, 2.8)], BLUE, 1)
    fr(p, 'y', 1.12, [(73.0, 74.0, 1.9, 2.1), (75.5, 76.4, 2.3, 2.5)], GLASSL, 1)
    bx(p, (72.2, 72.6), (1.4, 1.6), (1.4, 3.0), DWOOD)
    bx(p, (77.4, 77.8), (1.4, 1.6), (1.4, 3.0), DWOOD)
    # hay bales
    for (x0, x1, z0, z1, y1) in ((62.4, 65.4, 2.4, 4.3, 1.7), (63.0, 65.0, 2.6, 4.1, 3.2)):
        yb = 0.0 if y1 < 2 else 1.7
        bx(p, (x0, x1), (yb, y1), (z0, z1), (214, 184, 92), 0.08)
        fr(p, 'z', z1 + 0.02, [(x0 + 0.7, x0 + 0.85, yb, y1), (x1 - 0.85, x1 - 0.7, yb, y1)], DWOOD, 1)


# ======================================================================================================================
# 6. Well: Town Well
# ======================================================================================================================
def build_Well(p):
    cx, cz = -8, 26
    ring(p, cx, cz, 0, 3.4, 3.6, 2.9, STONE, DSTONE, STONE2, colwater=(44, 94, 150), wy=2.1, verts=10, jit=0.1)
    bx(p, (-11.6, -10.8), (3.4, 10.2), (25.6, 26.4), DWOOD)
    bx(p, (-5.2, -4.4), (3.4, 10.2), (25.6, 26.4), DWOOD)
    xcyl(p, -11.4, -4.6, 8.65, 26, 0.28, WOOD, verts=6)
    xcyl(p, -9.8, -5.8, 8.65, 26, 0.7, WOOD, verts=8)
    bx(p, (-6.57, -6.43), (5.6, 8.2), (25.93, 26.07), LEATHER)
    vcyl(p, -6.5, 4.6, 5.8, 26, 0.6, WOOD, verts=8, top_r=0.7)
    band(p, -6.5, 5.0, 5.15, 26, 0.67, IRON, 8)
    beam(p, (-4.6, 8.65, 26), (-3.8, 8.65, 26), 0.24, IRON)
    beam(p, (-3.8, 8.65, 26), (-3.8, 7.2, 26), 0.22, IRON)
    beam(p, (-3.8, 7.2, 26), (-3.3, 7.2, 26), 0.28, WOOD)
    # roof
    bx(p, (-12.8, -3.2), (10.0, 10.2), (22.6, 29.4), DWOOD)
    dk.prism(p, (cx, 10.2, cz), 9.6, 6.8, 2.0, RED, ridge='z', jitter=0.06, name="Roof")
    bx(p, (-8.18, -7.82), (11.9, 12.2), (22.6, 29.4), DWOOD)
    tri(p, [(-12.8, 10.2, 29.41), (-3.2, 10.2, 29.41), (-8, 12.1, 29.41)], (0, 0, 1), DWOOD)
    tri(p, [(-11.6, 10.25, 29.43), (-4.4, 10.25, 29.43), (-8, 11.85, 29.43)], (0, 0, 1), PLANK2)
    tri(p, [(-12.8, 10.2, 22.59), (-3.2, 10.2, 22.59), (-8, 12.1, 22.59)], (0, 0, -1), DWOOD)
    bx(p, (-12.8, -12.0), (3.4, 4.0), (26.0, 26.4), DWOOD)
    bx(p, (-12.0, -11.6), (3.4, 10.0), (25.6, 26.4), DWOOD)


# ======================================================================================================================
# 7. Wagon: Covered Wagon
# ======================================================================================================================
def build_Wagon(p):
    z0, z1 = 15.3, 22.7
    bx(p, (-56, -40), (1.8, 2.6), (z0, z1), WOOD)
    bx(p, (-56, -40), (2.6, 3.4), (z0, z0 + 0.3), PLANK2)
    bx(p, (-56, -40), (2.6, 3.4), (z1 - 0.3, z1), PLANK2)
    hlines(p, 'z', z1 + 0.02, -56, -40, [2.9], 0.08, DWOOD)
    for xa in (-52, -44):
        bx(p, (xa - 0.3, xa + 0.3), (1.9, 2.4), (14.9, 23.1), DWOOD)
        for zc in (15.0, 23.0):
            wheel_z(p, xa, 2.3, zc - 0.35, zc + 0.35, 2.3, 1.75, DWOOD, hub=IRON, spokes=2, verts=10)
    arch_prism(p, -54, -42.2, 19, 2.6, 3.4, 6.3, CREAM)
    for xr in (-53.9, -51.0, -48.1, -45.2, -42.4):
        arch_prism(p, xr - 0.15, xr + 0.15, 19, 2.6, 3.47, 6.34, DWOOD, jit=0.03)
    # front gathers and rear opening
    tri(p, [(-54.02, 2.6, 17.4), (-54.02, 2.6, 20.6), (-54.02, 6.2, 19)], (-1, 0, 0), (60, 44, 36))
    # driver's bench, foot board, tongue and yoke
    bx(p, (-56, -54.2), (2.6, 3.2), (15.8, 22.2), WOOD)
    bx(p, (-56, -55.8), (3.2, 4.4), (15.8, 22.2), PLANK2)
    bx(p, (-56.2, -55.6), (1.3, 1.9), (15.5, 22.5), DWOOD)
    bx(p, (-62, -56), (1.2, 1.7), (18.7, 19.3), DWOOD)
    bx(p, (-62, -61.6), (1.2, 1.7), (17.6, 20.4), DWOOD)
    # barrels on the rear
    for zc in (17, 21):
        vcyl(p, -41, 2.6, 5.2, zc, 1.0, PLANK2, verts=8, jit=0.1)
        band(p, -41, 3.0, 3.2, zc, 1.04, DIRON, 8)
        band(p, -41, 4.6, 4.8, zc, 1.04, DIRON, 8)
    # lantern on the front hoop
    bx(p, (-54.5, -54.0), (7.0, 7.9), (18.8, 19.2), CREAM)
    bx(p, (-54.6, -53.9), (7.9, 8.1), (18.7, 19.3), DIRON)


# ======================================================================================================================
# 8. Bank: Gold Bank
# ======================================================================================================================
def build_Bank(p):
    bx(p, (-74, -52), (0, 12), (-12, 2), SSTONE)
    bx(p, (-74.4, -51.6), (0, 0.9), (-12.4, 2.4), STONE2)
    hlines(p, 'z', 2.03, -74, -52, frange(1.6, 11.8, 1.3), 0.09, (186, 156, 114))
    for xs, sg in ((-74, -1), (-52, 1)):
        hlines(p, 'x', xs, -12, 2, frange(1.6, 11.8, 1.3), 0.09, (186, 156, 114), sg)
    bx(p, (-74.2, -72.9), (0.9, 12), (1.5, 2.3), CREAM)
    bx(p, (-53.1, -51.8), (0.9, 12), (1.5, 2.3), CREAM)
    bx(p, (-75, -51), (12.0, 12.6), (-12.5, 2.5), (120, 86, 62))
    bx(p, (-74.6, -51.4), (11.4, 12.0), (-12.2, 2.4), CREAM)
    # portico
    bx(p, (-75, -51), (0, 0.5), (2, 5.2), STONE)
    bx(p, (-67, -59), (0, 0.25), (5.2, 5.4), STONE)
    for x in (-72, -66, -60, -54):
        bx(p, (x - 0.95, x + 0.95), (0.5, 1.0), (2.65, 4.55), CREAM)
        vcyl(p, x, 1.0, 9.5, 3.6, 0.7, CREAM, verts=8, jit=0.04)
        bx(p, (x - 0.95, x + 0.95), (9.5, 10.0), (2.65, 4.55), CREAM)
    bx(p, (-75.5, -50.5), (10.0, 10.5), (1.8, 5.4), CREAM)
    bx(p, (-75.5, -50.5), (10.5, 12.0), (1.8, 5.4), DTEAL)
    bx(p, (-75.5, -50.5), (12.0, 12.6), (1.8, 5.4), CREAM)
    put_text(p, "BANK", -63, 11.85, 0.26, 5.42, GOLD)
    disc_z(p, -72.3, 11.25, 5.42, 0.55, GOLD, 1, 8)
    disc_z(p, -53.7, 11.25, 5.42, 0.55, GOLD, 1, 8)
    bx(p, (-73, -53), (12.6, 13.8), (2.1, 5.1), CREAM)
    bx(p, (-69, -57), (13.8, 15.0), (2.4, 4.8), CREAM)
    disc_z(p, -63, 14.3, 4.82, 0.7, GOLD, 1, 10)
    fr(p, 'z', 4.83, [(-63.08, -62.92, 13.7, 14.9)], DGOLD, 1)
    # vault door
    bx(p, (-65.4, -60.6), (0.5, 6.9), (1.9, 2.3), CREAM)
    fr(p, 'z', 2.33, [(-65.0, -61.0, 0.5, 6.4)], DGOLD, 1)
    fr(p, 'z', 2.34, [(-64.6, -61.4, 0.9, 6.0)], GOLD, 1)
    disc_z(p, -63, 3.7, 2.36, 1.35, DGOLD, 1, 10)
    disc_z(p, -63, 3.7, 2.37, 1.0, STEEL, 1, 10)
    fr(p, 'z', 2.38, [(-63.1, -62.9, 2.6, 4.8), (-64.1, -61.9, 3.6, 3.8)], DIRON, 1)
    # barred windows between the columns
    for c in (-69, -57):
        fr(p, 'z', 2.04, [(c - 1.4, c + 1.4, 2.6, 7.4)], GLASS, 1)
        fr(p, 'z', 2.05, [(c - 1.7, c + 1.7, 7.4, 7.7), (c - 1.7, c + 1.7, 2.3, 2.6), (c - 1.7, c - 1.4, 2.6, 7.4), (c + 1.4, c + 1.7, 2.6, 7.4)], CREAM, 1)
        fr(p, 'z', 2.07, [(c - 0.5, c - 0.35, 2.6, 7.4), (c + 0.35, c + 0.5, 2.6, 7.4), (c - 1.4, c + 1.4, 4.9, 5.05)], IRON, 1)
    for xs, sg in ((-74.03, -1), (-51.97, 1)):
        for zc in (-4, -9):
            fr(p, 'x', xs, [(zc - 1.3, zc + 1.3, 3.0, 8.0)], GLASS, sg)
            fr(p, 'x', xs + 0.01 * sg, [(zc - 0.1, zc + 0.1, 3.0, 8.0), (zc - 1.3, zc + 1.3, 5.4, 5.6)], CREAM, sg)
    # gold bars stacked in the portico
    for xb in (-69, -57):
        for k in range(3):
            bx(p, (xb - 0.9 + 0.1 * (k % 2), xb + 0.9 - 0.1 * (k % 2)), (0.5 + 0.38 * k, 0.88 + 0.38 * k), (3.8, 4.5), GOLD, 0.08)


# ======================================================================================================================
# 9. Cacti: Cactus Garden
# ======================================================================================================================
def saguaro(p, x, z, h):
    r = 1.1
    vcyl(p, x, 0, h - 1.0, z, r, GREEN, verts=10, top_r=r * 0.92, jit=0.2)
    ball(p, (x, h - 1.0, z), r * 0.92, GREEN, sc=(1, 1.08, 1), subdiv=1, jit=0.12)
    for side, yv, vh in ((-1, h * 0.42, 4.6), (1, h * 0.6, 3.8)):
        ya = yv + 0.6
        xa, xb = x + side * 1.0, x + side * 3.4
        xcyl(p, min(xa, xb), max(xa, xb), ya, z, 0.6, GREEN, verts=6, jit=0.2)
        ball(p, (xb, ya, z), 0.62, GREEN, subdiv=1, jit=0.08)
        vcyl(p, xb, ya, yv + vh - 0.6, z, 0.6, GREEN, verts=6, jit=0.2)
        ball(p, (xb, yv + vh - 0.6, z), 0.6, GREEN, sc=(1, 1.1, 1), subdiv=1, jit=0.08)
    for dx, dy in ((0.55, h - 1.2), (-0.5, h - 1.8), (0.7, h - 2.6)):
        bx(p, (x + dx - 0.28, x + dx + 0.28), (dy, dy + 0.56), (z + 0.5, z + 1.1), PINK)


def build_Cacti(p):
    saguaro(p, 65, 22, 15)
    saguaro(p, 86, 27, 12)
    for (x, z, fc) in ((76, 20, YELLOW), (91, 31, PINK)):
        ball(p, (x, 1.45, z), 1.6, GREEN, sc=(1, 0.92, 1), subdiv=1, jit=0.1)
        bx(p, (x - 0.35, x + 0.35), (2.65, 2.95), (z - 0.35, z + 0.35), fc)
    rock(p, 72, 0, 28, 4, 2, 3, ROCK, rot=20, subdiv=1)
    rock(p, 70, 0, 26.8, 2.4, 1.2, 2.2, ROCKD, rot=-30, subdiv=1)
    rock(p, 88, 0, 21, 2.6, 1.4, 2.0, ROCK2, rot=40, subdiv=0)
    # prickly pear: upright pads with red fruit
    for (x, z, ry, s) in ((77.5, 31.0, 20, 1.0), (79.4, 31.8, -35, 0.85), (75.9, 31.9, 70, 0.8)):
        o = ball(p, (x, 0.9 * s + 0.15, z), 0.85 * s, GREEN, sc=(1.0, 1.1, 0.28), subdiv=1, jit=0.1)
        o.rotation_euler[2] = math.radians(ry)
        bx(p, (x - 0.2, x + 0.2), (1.7 * s + 0.1, 2.0 * s + 0.1), (z - 0.2, z + 0.2), RED)
    # agaves and small round cacti fill the sand between the big ones
    for (x, z, hh) in ((68.5, 29.5, 2.4), (84.5, 21.0, 2.0)):
        for k in range(8):
            a = 2 * math.pi * k / 8
            beam(p, (x, 0.2, z), (x + 1.6 * math.cos(a), hh * (0.9 if k % 2 else 0.6) + 0.2, z + 1.6 * math.sin(a)), 0.55, (110, 150, 120) if k % 2 else (92, 132, 104), t2=0.1)
    for (x, z) in ((62.5, 28.0), (81.0, 29.0), (66.5, 19.5), (89.0, 25.5)):
        ball(p, (x, 0.75, z), 0.85, GREEN, sc=(1, 0.9, 1), subdiv=1, jit=0.1)
        bx(p, (x - 0.2, x + 0.2), (1.55, 1.8), (z - 0.2, z + 0.2), YELLOW)
    ball(p, (73.5, 1.3, 23.3), 1.3, (178, 150, 96), subdiv=1, jit=0.25)
    # a steer skull in the sand
    ball(p, (80, 0.65, 25), 0.6, CREAM, sc=(1.3, 0.9, 1.1), subdiv=1, jit=0.05)
    bx(p, (80.9, 81.9), (0.25, 0.8), (24.65, 25.35), CREAM)
    for s in (-1, 1):
        beam(p, (79.3, 0.9, 25 + s * 0.5), (78.3, 1.2, 25 + s * 1.3), 0.3, CREAM, t2=0.15)
        bx(p, (80.2, 80.6), (0.8, 1.1), (25 + s * 0.35 - 0.12, 25 + s * 0.35 + 0.12), BLACK)
    # dry grass tufts
    r = random.Random(9)
    for (x, z) in ((67, 26), (74, 24), (82, 30), (73, 31), (69, 30), (86, 22), (62, 24), (90, 26)):
        dk.cone(p, (x, 0, z), 0.5, r.uniform(0.9, 1.4), r.choice([(176, 160, 80), (196, 176, 90)]), verts=4)


# ======================================================================================================================
# 10. WaterTower
# ======================================================================================================================
def build_WaterTower(p):
    cx, cz = 12, -42
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, (cx + sx * 3.6 - 0.5, cx + sx * 3.6 + 0.5), (0, 13.6), (cz + sz * 3.6 - 0.5, cz + sz * 3.6 + 0.5), DWOOD)
    d = 3.6
    for sz in (-1, 1):
        beam(p, (cx - d, 0.8, cz + sz * d), (cx + d, 13.0, cz + sz * d), 0.34, WOOD)
        beam(p, (cx + d, 0.8, cz + sz * d), (cx - d, 13.0, cz + sz * d), 0.34, WOOD)
    for sx in (-1, 1):
        beam(p, (cx + sx * d, 0.8, cz - d), (cx + sx * d, 13.0, cz + d), 0.34, WOOD)
        beam(p, (cx + sx * d, 0.8, cz + d), (cx + sx * d, 13.0, cz - d), 0.34, WOOD)
    for sz in (-1, 1):
        bx(p, (cx - d, cx + d), (6.4, 6.8), (cz + sz * d - 0.2, cz + sz * d + 0.2), DWOOD)
    for sx in (-1, 1):
        bx(p, (cx + sx * d - 0.2, cx + sx * d + 0.2), (6.4, 6.8), (cz - d, cz + d), DWOOD)
    deck(p, 7, 17, 13.6, 14.0, -47, -37, [WOOD, PLANK2], 1.4, DWOOD, 'x')
    vcyl(p, cx, 14.0, 21.0, cz, 4.5, PLANK2, verts=12, jit=0.12)
    for yb in (15.3, 17.4, 19.5):
        band(p, cx, yb, yb + 0.28, cz, 4.58, DIRON, 12)
    vcyl(p, cx, 21.0, 23.0, cz, 5.2, DWOOD, verts=12, top_r=0.0, jit=0.1)
    # ladder
    for xr in (cx - 0.7, cx + 0.55):
        bx(p, (xr, xr + 0.15), (0, 13.6), (-36.75, -36.45), WOOD)
    for k in range(10):
        bx(p, (cx - 0.7, cx + 0.7), (0.8 + k * 1.3, 0.92 + k * 1.3), (-36.7, -36.5), WOOD)
    # spout
    beam(p, (cx + 3.6, 14.6, cz + 1.2), (cx + 4.8, 12.4, cz + 2.0), 0.5, IRON)
    bx(p, (cx + 4.1, cx + 5.1), (11.9, 12.5), (cz + 1.6, cz + 2.4), DIRON)


# ======================================================================================================================
# 11. Windmill: Wind Pump
# ======================================================================================================================
def build_Windmill(p):
    cx, cz = -22, 40

    def w(y):
        return 2.4 - (2.4 - 1.35) * y / 16.0

    for sx in (-1, 1):
        for sz in (-1, 1):
            beam(p, (cx + sx * 2.4, 0, cz + sz * 2.4), (cx + sx * 1.35, 16, cz + sz * 1.35), 0.75, STEEL, t2=0.5)
    for ya, yb in ((0.4, 7.0), (7.0, 15.8)):
        for sz in (-1, 1):
            beam(p, (cx - w(ya), ya, cz + sz * w(ya)), (cx + w(yb), yb, cz + sz * w(yb)), 0.2, STEEL)
            beam(p, (cx + w(ya), ya, cz + sz * w(ya)), (cx - w(yb), yb, cz + sz * w(yb)), 0.2, STEEL)
        for sx in (-1, 1):
            beam(p, (cx + sx * w(ya), ya, cz - w(ya)), (cx + sx * w(yb), yb, cz + w(yb)), 0.2, STEEL)
            beam(p, (cx + sx * w(ya), ya, cz + w(ya)), (cx + sx * w(yb), yb, cz - w(yb)), 0.2, STEEL)
    ww = w(7.0)
    for sz in (-1, 1):
        bx(p, (cx - ww, cx + ww), (6.9, 7.2), (cz + sz * ww - 0.15, cz + sz * ww + 0.15), STEEL)
    for sx in (-1, 1):
        bx(p, (cx + sx * ww - 0.15, cx + sx * ww + 0.15), (6.9, 7.2), (cz - ww, cz + ww), STEEL)
    bx(p, (cx - 2.5, cx + 2.5), (16, 16.5), (cz - 2.5, cz + 2.5), DWOOD)
    bx(p, (cx - 1.2, cx + 1.2), (16.5, 18.9), (37.5, 42.5), IRON)
    bx(p, (cx - 0.9, cx + 0.9), (18.9, 19.1), (38.0, 42.0), DIRON)
    zcyl(p, cx, 19.5, 42.5, 43.85, 0.75, DIRON, verts=8)
    wc = 43.6
    for k in range(12):
        a = math.radians(k * 30)
        rr = 3.05
        dk.box(p, (cx + rr * math.cos(a), 19.5 + rr * math.sin(a), wc), (3.7, 1.0, 0.16),
               (176, 180, 190) if k % 2 else (150, 154, 166), rot=(0, 0, k * 30.0), jitter=0.03)
    wheel_z(p, cx, 19.5, wc - 0.1, wc + 0.1, 4.9, 4.6, STEEL, hub=False, spokes=0, verts=12)
    # tail
    bx(p, (cx - 0.25, cx + 0.25), (19.05, 19.55), (34.9, 40), STEEL)
    bx(p, (cx - 0.2, cx + 0.2), (18.4, 21.4), (32.75, 36.25), RED)
    fr(p, 'x', cx + 0.22, [(33.4, 35.6, 19.2, 20.2)], CREAM, 1)
    fr(p, 'x', cx - 0.22, [(33.4, 35.6, 19.2, 20.2)], CREAM, -1)
    beam(p, (cx, 16.0, cz), (cx, 2.0, cz), 0.22, IRON)
    # trough and spout
    bx(p, (-18, -13), (0, 1.6), (38.7, 38.95), PLANK2)
    bx(p, (-18, -13), (0, 1.6), (41.05, 41.3), PLANK2)
    bx(p, (-18, -17.75), (0, 1.6), (38.95, 41.05), PLANK2)
    bx(p, (-13.25, -13), (0, 1.6), (38.95, 41.05), PLANK2)
    bx(p, (-17.75, -13.25), (0, 1.0), (38.95, 41.05), DWOOD)
    fr(p, 'y', 1.25, [(-17.75, -13.25, 38.95, 41.05)], BLUE, 1)
    fr(p, 'y', 1.27, [(-17.0, -16.0, 39.5, 39.7), (-15.2, -14.2, 40.2, 40.4)], GLASSL, 1)
    beam(p, (cx + 1.0, 4.4, cz), (-16.2, 2.2, cz), 0.4, IRON)
    bx(p, (-16.6, -15.8), (1.6, 2.3), (cz - 0.4, cz + 0.4), DIRON)


# ======================================================================================================================
# 12. Mine: Gold Mine
# ======================================================================================================================
def build_Mine(p):
    cols = [ROCK, ROCK2, ROCKD, ROCK, ROCKL]
    # the hill, split around the shaft
    strata(p, -90, -76.9, 0, 8, -62, -42, cols, 6, 0.5, seed=1)
    strata(p, -69.1, -56, 0, 8, -62, -42, cols, 6, 0.5, seed=2)
    cracks(p, 'z', -41.7, -90, -77, 0.2, 8, 4, 21)
    cracks(p, 'z', -41.7, -69, -56, 0.2, 8, 4, 22)
    bx(p, (-76.9, -69.1), (7.4, 8.0), (-47, -42), ROCKD, bot=True)
    bx(p, (-76.9, -69.1), (0, 7.4), (-48, -47), (36, 28, 30))
    fr(p, 'x', -76.88, [(-47, -42, 0, 7.4)], (44, 34, 34), 1)
    fr(p, 'x', -69.12, [(-47, -42, 0, 7.4)], (44, 34, 34), -1)
    fr(p, 'y', 7.38, [(-76.9, -69.1, -47, -42)], (28, 22, 24), -1)
    fr(p, 'y', 0.03, [(-76.9, -69.1, -47, -42)], (56, 44, 40), 1)
    bx(p, (-76.9, -76.4), (0, 7.4), (-45.0, -44.5), DWOOD)
    bx(p, (-69.6, -69.1), (0, 7.4), (-45.0, -44.5), DWOOD)
    bx(p, (-76.9, -69.1), (6.9, 7.4), (-45.0, -44.5), DWOOD)
    butte(p, -76, -54, 12, 7.5, [(8, 1.0, None), (9.5, 0.97, ROCK2), (11, 0.94, ROCK), (12.5, 0.92, ROCKD), (14, 0.9, ROCK2)], seed=3, cap=ROCKL, n=12)
    butte(p, -82, -55, 6, 5.5, [(14, 1.0, None), (15.3, 0.95, ROCKD), (16.6, 0.9, ROCK), (18, 0.86, ROCK2)], seed=4, cap=ROCKL, n=12)
    butte(p, -60.5, -50, 3.5, 4, [(8, 1.0, None), (9.5, 0.94, ROCKD), (11, 0.88, ROCK), (12, 0.84, ROCK2)], seed=5, cap=ROCKL, n=12)
    spires(p, [(-72, 14.0, -52, 1.6, 3.6), (-66, 14.0, -50, 1.1, 2.6), (-84, 8.0, -46, 1.3, 3.2),
               (-60, 12.0, -49, 1.5, 3.4), (-62, 8.0, -57, 1.4, 2.8)], [ROCK, ROCKD, ROCK2], 3)
    rock(p, -84, 8.0, -44.4, 2.6, 1.8, 2.2, ROCKD, rot=15)
    rock(p, -62, 8.0, -44.2, 2.2, 1.4, 1.8, ROCK, rot=-20, subdiv=0)
    rock(p, -86, 0, -39.5, 3.0, 1.6, 2.4, ROCK2, rot=30, subdiv=0)
    # timber frame, sign and lantern
    bx(p, (-78.1, -76.9), (0, 8.4), (-42.2, -41.0), DWOOD)
    bx(p, (-69.1, -67.9), (0, 8.4), (-42.2, -41.0), DWOOD)
    bx(p, (-78.5, -67.5), (8.4, 9.6), (-42.2, -41.0), WOOD)
    slant(p, (-76.9, 6.4), (-75.3, 8.4), -41.6, 0.45, 0.9, DWOOD)
    slant(p, (-69.1, 6.4), (-70.7, 8.4), -41.6, 0.45, 0.9, DWOOD)
    bx(p, (-77, -69), (10, 12), (-41.65, -41.15), CREAM)
    bx(p, (-76.6, -76.0), (9.6, 10.0), (-41.6, -41.2), DWOOD)
    bx(p, (-70.0, -69.4), (9.6, 10.0), (-41.6, -41.2), DWOOD)
    fr(p, 'z', -41.14, [(-77, -69, 11.75, 12), (-77, -69, 10, 10.25), (-77, -76.75, 10.25, 11.75), (-69.25, -69, 10.25, 11.75)], DWOOD, 1)
    put_text(p, "MINE", -73, 11.55, 0.27, -41.13, BLACK)
    bx(p, (-68.0, -67.7), (7.0, 8.4), (-40.9, -40.7), DIRON)
    bx(p, (-68.4, -67.3), (6.0, 7.0), (-41.0, -40.6), CREAM)
    bx(p, (-68.5, -67.2), (7.0, 7.2), (-41.1, -40.5), DIRON)
    # rails, ore cart, gold pile, TNT and a pickaxe
    for z in frange(-41.3, -34.8, 1.15):
        bx(p, (-74.6, -71.4), (0, 0.12), (z, z + 0.5), DWOOD)
    bx(p, (-74.2, -74.0), (0.12, 0.32), (-47, -34.3), STEEL)
    bx(p, (-72.0, -71.8), (0.12, 0.32), (-47, -34.3), STEEL)
    bx(p, (-74.6, -71.4), (1.0, 2.4), (-37.6, -35.2), IRON)
    bx(p, (-74.6, -71.4), (2.4, 2.6), (-37.6, -35.2), STEEL)
    for xw in (-74.45, -71.55):
        for zw in (-36.9, -35.9):
            xcyl(p, xw - 0.15, xw + 0.15, 0.6, zw, 0.6, DIRON, verts=8)
    ball(p, (-73, 2.6, -36.4), 1.2, GOLD, sc=(1.15, 0.7, 0.95), subdiv=1, jit=0.1)
    rock(p, -66.5, 0, -39, 3.6, 1.6, 3, ROCKD)
    for (x, y, z) in ((-67.2, 1.25, -39.3), (-66.2, 1.35, -38.4), (-65.6, 1.1, -39.8)):
        ball(p, (x, y, z), 0.42, GOLD, subdiv=0, jit=0.08)
    bx(p, (-82.5, -79.5), (0, 1.8), (-40.5, -38), RED)
    bx(p, (-82.0, -80.0), (1.8, 3.1), (-40.1, -38.4), RED)
    fr(p, 'z', -37.98, [(-82.5, -79.5, 0.8, 0.95)], DRED, 1)
    put_text(p, "TNT", -81, 1.45, 0.15, -37.97, WHITE)
    fr(p, 'z', -38.38, [(-82.0, -80.0, 2.3, 2.4)], DRED, 1)
    beam(p, (-67.6, 0.1, -40.0), (-68.2, 4.2, -40.7), 0.18, WOOD)
    beam(p, (-69.1, 4.3, -40.8), (-67.1, 4.0, -40.8), 0.26, STEEL)


# ======================================================================================================================
# 13. Train: Steam Locomotive
# ======================================================================================================================
def build_Train(p):
    cx = -89
    # track bed, sleepers and rails
    bx(p, (-94, -84), (0, 0.5), (-30, 22), (122, 112, 100), 0.08)
    fr(p, 'y', 0.51, [(-93, -85, z, z + 0.5) for z in frange(-29.5, 21.5, 1.8)], DWOOD)
    bx(p, (-91.5, -91.0), (0.5, 0.85), (-30, 22), STEEL, 0.03)
    bx(p, (-87.0, -86.5), (0.5, 0.85), (-30, 22), STEEL, 0.03)
    xl, xr = -91.25, -86.75
    # ---- locomotive (front = +z)
    bx(p, (-90.4, -87.6), (0.9, 2.4), (-2, 22), DIRON)
    bx(p, (-92.7, -85.3), (3.9, 4.2), (5.5, 22), IRON)
    zcyl(p, cx, 5.6, 5.5, 19.2, 2.7, IRON, verts=10, jit=0.05)
    zcyl(p, cx, 5.6, 19.2, 20.5, 2.75, DIRON, verts=10, jit=0.03)
    zband(p, cx, 5.6, 9.0, 9.5, 2.78, GOLD, 10)
    zband(p, cx, 5.6, 14.0, 14.5, 2.78, GOLD, 10)
    disc_z(p, cx, 5.6, 20.52, 2.2, IRON, 1, 10)
    disc_z(p, cx, 5.6, 20.54, 0.5, GOLD, 1, 8)
    bx(p, (-89.6, -88.4), (8.3, 9.5), (19.4, 20.6), GOLD)
    disc_z(p, cx, 8.9, 20.62, 0.4, CREAM, 1, 8)
    vcyl(p, cx, 8.2, 13.2, 18.5, 0.8, DIRON, verts=8, top_r=1.5, jit=0.03)
    vcyl(p, cx, 8.2, 9.8, 13.0, 1.0, GOLD, verts=8, top_r=0.7, jit=0.03)
    vcyl(p, cx, 8.2, 9.2, 9.8, 0.7, GOLD, verts=8, top_r=0.5, jit=0.03)
    dk.wedge(p, (cx, 1.3, 22.7), (6.4, 1.6, 1.4), STEEL, rot=(0, 180, 0), jitter=0.04)
    # cab
    bx(p, (-92.7, -85.3), (2.3, 10.9), (-0.4, 6.8), RED)
    bx(p, (-93.1, -84.9), (10.9, 11.4), (-0.9, 7.3), IRON)
    for xs, sg in ((-92.7, -1), (-85.3, 1)):
        fr(p, 'x', xs + 0.02 * sg, [(0.8, 4.8, 6.2, 9.4)], GLASS, sg)
        fr(p, 'x', xs + 0.03 * sg, [(0.6, 5.0, 9.4, 9.6), (0.6, 5.0, 6.0, 6.2), (0.6, 0.8, 6.2, 9.4), (4.8, 5.0, 6.2, 9.4)], CREAM, sg)
        fr(p, 'x', xs + 0.02 * sg, [(-0.4, 6.8, 3.6, 3.9)], GOLD, sg)
    fr(p, 'z', 6.82, [(-91.6, -90.0, 6.4, 9.2), (-88.0, -86.4, 6.4, 9.2)], GLASS, 1)
    # wheels and rods
    for zc in (8.5, 13.5):
        for xw in (xl, xr):
            wheel_x(p, xw, 1.9, zc, 1.9, 0.5, DIRON, hub=GOLD, verts=8)
    for xw, sg in ((xl - 0.45, -1), (xr + 0.45, 1)):
        bx(p, (xw - 0.1, xw + 0.1), (1.6, 2.2), (8.5, 13.5), STEEL)
    for xw in (xl, xr):
        wheel_x(p, xw, 1.2, 19.5, 1.2, 0.4, DIRON, verts=6)
    # ---- tender
    bx(p, (-91.0, -87.0), (0.9, 2.2), (-14, -2), DIRON)
    bx(p, (-92.2, -85.8), (2.2, 4.8), (-14, -2), IRON)
    bx(p, (-91.9, -86.1), (4.8, 5.4), (-12.9, -3.1), BLACK, 0.18)
    bx(p, (-91.2, -86.8), (5.4, 5.9), (-12.0, -4.0), BLACK, 0.18)
    bx(p, (-90.4, -87.6), (5.9, 6.2), (-11.0, -5.0), BLACK, 0.18)
    for xs, sg in ((-92.2, -1), (-85.8, 1)):
        fr(p, 'x', xs + 0.02 * sg, [(-13.4, -2.6, 3.5, 3.8)], GOLD, sg)
    for zc in (-11, -5):
        for xw in (xl, xr):
            wheel_x(p, xw, 1.1, zc, 1.1, 0.4, DIRON, verts=6)
    bx(p, (-89.4, -88.6), (1.2, 1.6), (-2, 0), IRON)
    # ---- freight car
    bx(p, (-91.0, -87.0), (0.9, 1.6), (-28, -16), DIRON)
    bx(p, (-92.5, -85.5), (1.6, 7.4), (-28, -16), RED)
    bx(p, (-92.8, -85.2), (7.4, 7.9), (-28.3, -15.7), DWOOD)
    bx(p, (-89.4, -88.6), (1.2, 1.6), (-16, -14), IRON)
    for xs, sg in ((-92.5, -1), (-85.5, 1)):
        hlines(p, 'x', xs + 0.02 * sg, -28, -16, frange(2.6, 7.2, 1.0), 0.09, DRED, sg)
        fr(p, 'x', xs + 0.03 * sg, [(-24.8, -19.2, 1.8, 6.6)], (140, 44, 34), sg)
        fr(p, 'x', xs + 0.04 * sg, [(-24.8, -24.6, 1.8, 6.6), (-19.4, -19.2, 1.8, 6.6), (-24.8, -19.2, 6.4, 6.6), (-22.1, -21.9, 1.8, 6.6)], CREAM, sg)
    for zc in (-25, -19):
        for xw in (xl, xr):
            wheel_x(p, xw, 1.1, zc, 1.1, 0.4, DIRON, verts=6)
    fr(p, 'z', -15.68, [(-92.5, -85.5, 6.2, 7.2)], DRED, 1)


# ======================================================================================================================
# 14. Camp: Cowboy Camp
# ======================================================================================================================
def build_Camp(p):
    tx, tz = -61, -30
    R0, R1, H = 3.2, 0.35, 8.2
    rad = lambda y: R0 - (R0 - R1) * y / H
    vcyl(p, tx, 0, H, tz, R0, CREAM, verts=10, top_r=R1, jit=0.05)
    cone_band(p, tx, tz, 1.0, 1.8, rad(1.0) + 0.04, rad(1.8) + 0.04, RED, 10)
    cone_band(p, tx, tz, 1.8, 2.4, rad(1.8) + 0.04, rad(2.4) + 0.04, TEAL, 10)
    cone_band(p, tx, tz, 5.6, 6.3, rad(5.6) + 0.04, rad(6.3) + 0.04, RED, 10)
    tri(p, [(tx - 1.45, 0.0, tz + rad(0.0) - 0.1), (tx + 1.45, 0.0, tz + rad(0.0) - 0.1), (tx, 5.3, tz + rad(5.3) + 0.03)], (0, 0.45, 1), DRED)
    tri(p, [(tx - 1.0, 0.0, tz + rad(0.0) - 0.04), (tx + 1.0, 0.0, tz + rad(0.0) - 0.04), (tx, 4.6, tz + rad(4.6) + 0.05)], (0, 0.45, 1), (50, 34, 30))
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.3
        beam(p, (tx + 3.0 * math.cos(a), 0, tz + 3.0 * math.sin(a)), (tx - 0.3 * math.cos(a), 9.6, tz - 0.3 * math.sin(a)), 0.3, DWOOD, t2=0.18)
    # fire
    fx, fz = -53, -27
    for k in range(8):
        a = 2 * math.pi * k / 8
        dk.box(p, (fx + 1.65 * math.cos(a), 0.4, fz + 1.65 * math.sin(a)), (0.9, 0.8, 0.9), STONE if k % 2 else STONE2, rot=(0, -math.degrees(a), 0), jitter=0.1)
    xcyl(p, fx - 1.0, fx + 1.0, 0.55, fz, 0.22, DWOOD, verts=6)
    zcyl(p, fx, 0.7, fz - 1.0, fz + 1.0, 0.22, WOOD, verts=6)
    dk.cyl(p, (fx, 0.9, fz), 0.2, 2.0, DWOOD, axis='x', verts=6, rot=(0, 45, 0))
    dk.cone(p, (fx, 0.5, fz), 0.85, 2.0, ORANGE, verts=5, jitter=0.05)
    dk.cone(p, (fx + 0.15, 0.7, fz - 0.1), 0.55, 2.8, YELLOW, verts=5, jitter=0.05)
    dk.cone(p, (fx - 0.5, 0.5, fz + 0.4), 0.4, 1.4, RED, verts=5, jitter=0.05)
    for a_deg in (20, 140, 260):
        a = math.radians(a_deg)
        beam(p, (fx + 2.3 * math.cos(a), 0, fz + 2.3 * math.sin(a)), (fx, 5.2, fz), 0.2, DWOOD)
    beam(p, (fx, 5.2, fz), (fx, 4.5, fz), 0.08, IRON)
    vcyl(p, fx, 3.7, 4.5, fz, 0.7, DIRON, verts=8, top_r=0.62, jit=0.03)
    # log seats, hat and saddle
    xcyl(p, -55.2, -50.8, 0.8, -23.2, 0.7, DWOOD, verts=8)
    zcyl(p, -56.8, 0.8, -29.2, -24.8, 0.7, DWOOD, verts=8)
    xcyl(p, -55.2, -50.8, 0.8, -30.8, 0.7, DWOOD, verts=8)
    vcyl(p, -53.8, 1.5, 1.6, -30.8, 1.0, LEATHER, verts=8, jit=0.05)
    vcyl(p, -53.8, 1.6, 2.2, -30.8, 0.55, LEATHER, verts=8, top_r=0.5, jit=0.05)
    bx(p, (-52.4, -50.9), (1.5, 1.75), (-23.6, -22.8), RED)
    bx(p, (-52.2, -51.1), (1.75, 2.1), (-23.5, -22.9), LEATHER)
    # crate, sack and bedroll
    bx(p, (-49.2, -46.8), (0, 2.0), (-31.2, -28.8), WOOD)
    bx(p, (-49.2, -46.8), (2.0, 2.2), (-31.3, -28.7), PLANK2)
    hlines(p, 'z', -28.78, -49.2, -46.8, [0.6, 1.3], 0.1, DWOOD)
    vcyl(p, -48.0, 2.2, 2.9, -30.0, 0.35, DIRON, verts=6, top_r=0.3, jit=0.03)
    zcyl(p, -58, 0.7, -25.2, -21.8, 0.7, RED, verts=8)
    zband(p, -58, 0.7, -24.6, -24.4, 0.76, DWOOD, 8)
    zband(p, -58, 0.7, -22.6, -22.4, 0.76, DWOOD, 8)
    disc_z(p, -58, 0.7, -21.79, 0.55, CREAM, 1, 8)


# ======================================================================================================================
# 15. Mesa: Red Rock Mesa with the giant hat
# ======================================================================================================================
def build_Mesa(p):
    cx, cz = 79, 50
    SANDR = (226, 186, 140)
    # the big mesa: sloping talus foot, banded cliff, flat cap that overhangs a little
    butte(p, cx, cz, 13, 12, [(0, 1.0, None), (2.5, 0.93, ROCKD), (5, 0.88, ROCK), (7, 0.84, ROCK2), (9, 0.81, ROCK),
                              (10.6, 0.8, ROCKL), (12.2, 0.79, ROCKD), (13.6, 0.79, ROCK), (15.4, 0.78, SANDR),
                              (16.8, 0.78, ROCK2), (18.4, 0.77, ROCKD), (19.8, 0.77, ROCK), (21, 0.76, ROCKL),
                              (21, 0.84, DRED), (22.2, 0.84, ROCK2)], seed=12, cap=ROCKL, wob=0.04, gullies=7)
    butte(p, 62.5, 44, 3.5, 4, [(0, 1.0, None), (3, 0.92, ROCKD), (6, 0.86, ROCK), (8.5, 0.82, ROCK2), (11, 0.78, ROCKL), (13, 0.75, ROCK)],
          seed=15, cap=ROCKL, gullies=3)
    spires(p, [(70, 22.2, 44, 1.3, 2.4), (87, 22.2, 56, 1.5, 3.0), (86, 22.2, 44, 1.0, 2.0), (71, 22.2, 56, 1.1, 2.2)],
           [ROCK, ROCKD, ROCKL], 5)
    rock(p, 72, 0, 36, 4, 3, 3.6, ROCKD, rot=15)
    rock(p, 86, 0, 35.4, 5, 2.4, 3.4, ROCK, rot=-25)
    rock(p, 62.5, 0, 38.5, 3, 1.8, 2.4, ROCK2, rot=40, subdiv=0)
    rock(p, 90.5, 0, 36.5, 2.6, 1.5, 2.2, ROCKD, rot=10, subdiv=0)
    rock(p, 79, 0, 36.2, 2.2, 1.2, 1.8, ROCK2, rot=-5, subdiv=0)
    rock(p, 66.5, 0, 60.4, 2.4, 1.4, 1.8, ROCKD, rot=25, subdiv=0)
    rock(p, 90, 0, 60.4, 2.2, 1.3, 1.6, ROCK2, rot=-15, subdiv=0)
    # the giant cowboy hat on top
    hx, hz = 78, 50
    vcyl(p, hx, 22.2, 23.8, hz, 4.9, DWOOD, verts=12, top_r=4.7, jit=0.05)
    vcyl(p, hx, 23.8, 26.8, hz, 2.8, WOOD, verts=12, top_r=2.25, jit=0.05)
    cone_band(p, hx, hz, 24.2, 25.1, 2.74, 2.58, DRED, 12)
    for sg in (-1, 1):
        dk.box(p, (hx + sg * 4.6, 23.55, hz), (2.8, 0.45, 5.4), DWOOD, rot=(0, 0, sg * 26.0), jitter=0.05)
    bx(p, (77.5, 78.5), (24.3, 25.0), (52.55, 52.85), GOLD)
    fr(p, 'y', 26.805, [(77.6, 78.4, 47.8, 52.2)], DWOOD, 1)
    # a desert shrub or two on the mesa foot
    r = random.Random(4)
    for (x, z) in ((76, 37), (83, 36.5), (68, 37.5), (89, 38)):
        dk.cone(p, (x, 0, z), 0.5, r.uniform(0.9, 1.5), (176, 160, 80), verts=4)


# ======================================================================================================================
# fit to the union box of the blueprint pieces, previews, main
# ======================================================================================================================
ORDER = ["Floor", "Saloon", "Gate", "Jail", "Horses", "Well", "Wagon", "Bank", "Cacti", "WaterTower", "Windmill", "Mine",
         "Train", "Camp", "Mesa"]
# where the reference Cowboy Shiba stands in each preview: (x, z, facing, lift); the Saloon one is the real Shiba spot
SHIBA_AT = {"Floor": (60, 40, 270, 0), "Saloon": (52, -14, 270, 0), "Gate": (0, 50, 270, 0), "Jail": (-64, 60, 270, 0),
            "Horses": (62, 14, 270, 0), "Well": (-16, 30, 270, 0), "Wagon": (-48, 30, 270, 0), "Bank": (-63, 12, 270, 0),
            "Cacti": (74, 14, 270, 0), "WaterTower": (24, -38, 270, 0), "Windmill": (-12, 46, 270, 0),
            "Mine": (-73, -30, 270, 0), "Train": (-76, 14, 270, 0), "Camp": (-53, -17, 270, 0), "Mesa": (79, 68, 270, 0)}
MULT = {"Floor": 2.0, "Saloon": 2.1, "Gate": 2.2, "Jail": 2.3, "Horses": 1.9, "Well": 3.4, "Wagon": 2.8, "Bank": 2.7,
        "Cacti": 2.7, "WaterTower": 2.8, "Windmill": 2.8, "Mine": 2.5, "Train": 2.4, "Camp": 3.0, "Mesa": 3.0}
AZ = {"Train": 225, "Windmill": 205}


def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s = list(q["Size"])
        o = q["Offset"]
        r = q.get("Rotation")
        if r:
            assert r[0] == 0 and (r[1] == 0 or r[2] == 0)
            if r[2] == 90:
                s = [s[1], s[0], s[2]]
            elif r[1] == 90:
                s = [s[2], s[1], s[0]]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - s[i] / 2)
            hi[i] = max(hi[i], o[i] + s[i] / 2)
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
    seen = set()
    for o in objs:
        ws = [v.co for v in o.data.vertices]
        for i, nm in enumerate("xzy"):
            if min(v[i] for v in ws) < tl[i] - 0.05 or max(v[i] for v in ws) > th[i] + 0.05:
                key = (nm, round(min(v[i] for v in ws), 1), round(max(v[i] for v in ws), 1))
                if key not in seen:
                    seen.add(key)
                    print(f"  WARN {part.id}: {o.name} sticks out on {nm}: {min(v[i] for v in ws):.2f}..{max(v[i] for v in ws):.2f} vs {tl[i]:.2f}..{th[i]:.2f}")
    sc = [(th[i] - tl[i]) / max(1e-6, (bh[i] - bl[i])) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    print(f"FIT {part.id}: raw size stage xyz {[round(bh[0]-bl[0],2), round(bh[2]-bl[2],2), round(bh[1]-bl[1],2)]} "
          f"scale stage xyz = {sc[0]:.3f} {sc[2]:.3f} {sc[1]:.3f}")


def add_shiba(x, z, facing, lift=0.0, studs=6.4):
    """Reference Cowboy Shiba. The scene is the MIRRORED stage (decorkit mirrors x when finishing), so mirror the spot too."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(dk.MODELS, "CowboyShiba.fbx"), axis_forward='Z', axis_up='Y')
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low, high = min(q.z for q in pts), max(q.z for q in pts)
    k = studs / (high - low)
    f = math.radians(180 - facing)
    want = Vector((math.cos(f), -math.sin(f), 0))
    yaw = math.atan2(want.y, want.x) - math.atan2(-1, 0)
    m = Matrix.Translation(Vector((-x, z, 0))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(k, 4) @ Matrix.Translation((0, 0, -low))
    for o in new:
        o.matrix_world = m @ o.matrix_world
    bpy.context.view_layer.update()
    for o in new:
        if o.parent is None:
            o.location.z += lift
    bpy.context.view_layer.update()
    return new


def drop(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def snap(objs, extra, filename, az, el, mult, size, top=False):
    low, high = dk._bounds(list(objs) + list(extra))
    g = dk.ground(low, high, color=(120, 150, 92))
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
    print("RENDERED", path)


def combine(a, b, out):
    import numpy as np
    ia, ib = bpy.data.images.load(a), bpy.data.images.load(b)
    w, h = ia.size
    pa = np.empty(w * h * 4, dtype=np.float32)
    ia.pixels.foreach_get(pa)
    pb = np.empty(w * h * 4, dtype=np.float32)
    ib.pixels.foreach_get(pb)
    both = np.concatenate([pb, pa])      # image rows start at the bottom: top view below, 3/4 view above
    img = bpy.data.images.new("stage", w, h * 2, alpha=False)
    img.pixels.foreach_set(both)
    img.filepath_raw = out
    img.file_format = 'PNG'
    img.save()
    print("RENDERED", out)


def tri_count(meshes):
    return sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)


def main():
    dk.start(OUT)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    ids = ONLY or ORDER
    built, stats = {}, {}
    for pid in ids:
        fn = globals().get("build_" + pid)
        if fn is None:
            print("SKIP (not written yet)", pid)
            continue
        pj = dk.blueprint_part(BP, pid)
        part = dk.Part(pid)
        groups = fn(part)
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        built[pid] = meshes
        stats[pid] = {"tris": tri_count(meshes), "meshes": len(meshes)}
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        x, z, f, lift = SHIBA_AT[pid]
        sb = add_shiba(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 205), 28, MULT.get(pid, 2.6), (1400, 1000))
        drop(sb)
    with open(os.path.join(OUT, "summary.json"), "w") as fh:
        json.dump(stats, fh, indent=1)
    print("STATS", json.dumps(stats))
    if ONLY is None or len(ids) == len(ORDER):
        allm = [m for ms in built.values() for m in ms]
        for ms in built.values():
            dk.hide(ms, False)
        sx, sz, sf = BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"]
        sbs = add_shiba(sx, sz, sf, 0, 6.4)
        shm = [o for o in sbs if o.type == 'MESH']
        snap(allm, shm, "stage_3q.png", 205, 38, 1.9, (1800, 1100))
        snap(allm, shm, "stage_top.png", 180, 89, 1.9, (1800, 1100), top=True)
        combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_WesternSaloon.png"))


main()
