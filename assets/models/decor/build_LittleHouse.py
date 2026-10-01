"""Final low-poly decor models for the theme LittleHouse (10 parts), built on decorkit.py.

Run:  blender --background --factory-startup --python build_LittleHouse.py -- <outdir> [--only Id1,Id2] [--noview]
Writes Decor_LittleHouse_<PartId>.fbx, preview_<PartId>.png (3/4 view with a reference Shiba) and stage_LittleHouse.png.
Every model keeps the footprint and height of the union box of its blueprint pieces (the game fits models to that box).
All colours are flat vertex colours (Roblox ignores FBX material colours); max 4 meshes per part, ~1500 triangles.
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import decorkit as dk

KEY = "LittleHouse"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_LittleHouse.json"))
ARGS = dk.args()
OUT = ARGS[0] if ARGS and not ARGS[0].startswith("--") else os.path.join(HERE, "out", KEY)
ONLY = set(ARGS[ARGS.index("--only") + 1].split(",")) if "--only" in ARGS else set()
NOVIEW = "--noview" in ARGS
OUT = os.path.abspath(OUT)
dk.start(OUT)
R = random.Random(5)

# ---------------------------------------------------------------- palette (shared by all parts)
BRICK = (176, 88, 66)
BRICK_D = (146, 68, 52)
CREAM = (246, 232, 200)
TRIM = (250, 246, 236)
ROOF = (172, 74, 66)
ROOF_D = (128, 52, 50)
SLATE = (96, 98, 110)
STONE = (150, 150, 156)
STONE_D = (118, 118, 126)
STONE_L = (176, 176, 180)
WOOD = (150, 104, 62)
WOOD_D = (110, 76, 44)
WOOD_L = (176, 132, 86)
SHUT = (66, 122, 104)
GLASS = (150, 204, 232)
SOIL = (92, 64, 44)
LEAF = (70, 150, 70)
GOLD = (240, 190, 50)
WATER = (90, 170, 230)
DARK = (40, 28, 24)
FLOWERS = [(230, 60, 70), (250, 210, 60), (240, 120, 190), (250, 250, 250), (150, 110, 230)]

Y0 = 0.05


# ---------------------------------------------------------------- helpers
def bx(p, x0, x1, y0, y1, z0, z1, col, j=0.05, rot=(0, 0, 0), name="B"):
    """Box from extents (stage axes)."""
    return dk.box(p, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), col,
                  rot=rot, jitter=j, name=name)


def circ(cx, cz, r, y, n=12, rot=0.0):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n), y, cz + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def rr(cx, cz, hx, hz, y):
    return [(cx - hx, y, cz - hz), (cx + hx, y, cz - hz), (cx + hx, y, cz + hz), (cx - hx, y, cz + hz)]


def loft(p, rings, col, j=0.05, caps=True, closed=False, name="B"):
    """Closed solid through rings (lists of equal length of stage points)."""
    n = len(rings[0])
    m = len(rings)
    pts = [q for r in rings for q in r]
    faces = []
    for a in range(m if closed else m - 1):
        b = (a + 1) % m
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((a * n + k, a * n + k2, b * n + k2, b * n + k))
    if caps and not closed:
        faces.append(tuple(range(n)))
        faces.append(tuple(range((m - 1) * n, m * n)))
    return dk.poly(p, (0, 0, 0), pts, faces, col, j, name=name)


def octa(p, c, r, col, sy=0.8, j=0.08, name="B", rot=(0, 0, 0)):
    """Cheap gem-like blossom: octahedron (8 triangles)."""
    pts = [(r, 0, 0), (-r, 0, 0), (0, r * sy, 0), (0, -r * sy, 0), (0, 0, r), (0, 0, -r)]
    faces = [(0, 2, 4), (4, 2, 1), (1, 2, 5), (5, 2, 0), (0, 4, 3), (4, 1, 3), (1, 5, 3), (5, 0, 3)]
    return dk.poly(p, c, pts, faces, col, j, rot=rot, name=name)


def wobble(o, amt, seed=0):
    """Random radial vertex displacement (organic low-poly blobs); keeps the painted face colours."""
    rg = random.Random(seed)
    for v in o.data.vertices:
        f = 1.0 + rg.uniform(-amt, amt)
        v.co.x *= f
        v.co.y *= f
        v.co.z *= f
    o.data.update()


def mirror_part_x(p, cx):
    """Optional safety valve (--mirror-x): mirror the finished part in x around the union-box centre cx."""
    for o in p.objs:
        o.data.transform(o.matrix_world)
        o.matrix_world = o.matrix_world.Identity(4)
        for v in o.data.vertices:
            v.co.x = 2 * cx - v.co.x
        o.data.flip_normals()
        o.data.update()


def tube(p, cx, cz, rin, rout, y0, y1, col, n=16, j=0.05, name="B", rot=0.0):
    """Ring wall (hollow cylinder)."""
    return loft(p, [circ(cx, cz, rout, y0, n, rot), circ(cx, cz, rout, y1, n, rot), circ(cx, cz, rin, y1, n, rot),
                    circ(cx, cz, rin, y0, n, rot)], col, j, closed=True, name=name)


def grouped(p, **prefixes):
    """{group: [objects whose name starts with prefix]} for dk.finish (rest = Body)."""
    return {g: [o for o in p.objs if o.name.startswith(pre)] for g, pre in prefixes.items()}


class Wall:
    """Wall helper: u runs along the wall, y up, v outward from the wall's mid plane."""

    def __init__(s, p, axis, c, sgn):
        s.p, s.axis, s.c, s.sgn = p, axis, c, sgn

    def pt(s, u, y, v):
        return (u, y, s.c + s.sgn * v) if s.axis == 'x' else (s.c + s.sgn * v, y, u)

    def box(s, u0, u1, y0, y1, v0, v1, col, j=0.05, name="B", rot=(0, 0, 0)):
        a, b = s.pt(u0, y0, v0), s.pt(u1, y1, v1)
        return bx(s.p, a[0], b[0], a[1], b[1], a[2], b[2], col, j, rot, name)

    def frame(s, uc, yc, w, h, t, v0, v1, col, name="T_frame"):
        hw, hh, ow, oh = w / 2, h / 2, w / 2 + t, h / 2 + t
        pts = []
        for v in (v0, v1):
            for (u, y) in [(-ow, -oh), (ow, -oh), (ow, oh), (-ow, oh)]:
                pts.append(s.pt(uc + u, yc + y, v))
            for (u, y) in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                pts.append(s.pt(uc + u, yc + y, v))
        faces = []
        for k in range(4):
            k2 = (k + 1) % 4
            faces += [(k, k2, 8 + k2, 8 + k), (8 + k, 8 + k2, 12 + k2, 12 + k), (4 + k, 4 + k2, 12 + k2, 12 + k)]
        o = dk.poly(s.p, (0, 0, 0), pts, faces, col, 0.03, name=name)
        # open shell (no back ring): make sure the front ring faces outward
        a, b = s.pt(0, 0, 1), s.pt(0, 0, 0)
        out = Vector((a[0] - b[0], a[2] - b[2], a[1] - b[1]))
        best = max(o.data.polygons, key=lambda q: q.center.dot(out))
        if best.normal.dot(out) < 0:
            o.data.flip_normals()
        return o

    def ball(s, u, y, v, r, col, subdiv=1, name="T_ball", scale=(1, 1, 1), j=0.06):
        return dk.ball(s.p, s.pt(u, y, v), r, col, scale=scale, subdiv=subdiv, jitter=j, name=name)

    def wall_run(s, u0, u1, wins, y0, ytop, ysill, yhead, col, j=0.05):
        s.box(u0, u1, y0, ysill, -0.5, 0.5, col, j)
        s.box(u0, u1, yhead, ytop, -0.5, 0.5, col, j)
        prev = u0
        for uc, w in sorted(wins):
            s.box(prev, uc - w / 2, ysill, yhead, -0.5, 0.5, col, j)
            prev = uc + w / 2
        s.box(prev, u1, ysill, yhead, -0.5, 0.5, col, j)

    def window(s, uc, w, y0, y1, shutters=True, flowers=False, trim=0.45, scol=SHUT):
        yc = (y0 + y1) / 2
        s.box(uc - w / 2, uc + w / 2, y0, y1, -0.15, 0.15, GLASS, 0.03, "T_glass")
        s.box(uc - 0.15, uc + 0.15, y0, y1, -0.25, 0.25, TRIM, 0.02, "T_mull")
        s.box(uc - w / 2, uc + w / 2, yc - 0.15, yc + 0.15, -0.25, 0.25, TRIM, 0.02, "T_mull")
        s.frame(uc, yc, w, y1 - y0, trim, 0.2, 0.95, TRIM)
        if flowers:
            ya, yb = y0 - trim - 1.4, y0 - trim
            s.box(uc - w / 2 - 0.2, uc + w / 2 + 0.2, ya, yb, 0.5, 1.7, WOOD, 0.05, "T_fbox")
            s.box(uc - w / 2 - 0.05, uc + w / 2 + 0.05, yb - 0.05, yb + 0.12, 0.65, 1.55, SOIL, 0.03, "T_soil")
            n = max(2, int(w / 1.8))
            for i in range(n):
                u = uc - w / 2 + (i + 0.5) * w / n
                octa(s.p, s.pt(u, yb + 0.5, 1.1), 0.62, FLOWERS[(i + int(uc)) % 5], name="T_bloom")
        else:
            s.box(uc - w / 2 - trim - 0.25, uc + w / 2 + trim + 0.25, y0 - trim - 0.3, y0 - trim, 0.5, 1.25, STONE, 0.04, "T_sill")
        if shutters:
            sw = w * 0.27
            for sd in (-1, 1):
                u = uc + sd * (w / 2 + trim + sw / 2)
                s.box(u - sw / 2, u + sw / 2, y0 - trim, y1 + trim, 0.5, 0.85, scol, 0.05, "T_shut")


def shade(c, f):
    return dk.shade(c, f)


def done(p, groups, shiba, az, el=30, extra_views=None):
    """Join + export + preview, then hide the part so the next previews stay clean."""
    if "--tri" in ARGS:
        cnt = {}
        for o in p.objs:
            stem = o.name.split(".")[0]
            cnt[stem] = cnt.get(stem, 0) + sum(len(q.vertices) - 2 for q in o.data.polygons)
        print("TRIS", p.id, sorted(cnt.items(), key=lambda kv: -kv[1]))
    if "--mirror-x" in ARGS:
        pcs = dk.blueprint_part(BP, p.id)["Pieces"]
        def hx(q):
            rot = q.get("Rotation") or (0, 0, 0)
            return q["Size"][1 if rot[2] == 90 else (2 if rot[1] == 90 else 0)] / 2
        lo_x = min(q["Offset"][0] - hx(q) for q in pcs)
        hi_x = max(q["Offset"][0] + hx(q) for q in pcs)
        mirror_part_x(p, (lo_x + hi_x) / 2)
    meshes = dk.finish(p, KEY, groups={k: v for k, v in groups.items() if v})
    # footprint check against the union box of the blueprint pieces (stage frame)
    from mathutils import Matrix
    lo_u, hi_u = [1e9] * 3, [-1e9] * 3
    for q in dk.blueprint_part(BP, p.id)["Pieces"]:
        rx, ry, rz = (math.radians(a) for a in (q.get("Rotation") or (0, 0, 0)))
        Rm = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    c = Rm @ Vector((sx * q["Size"][0] / 2, sy * q["Size"][1] / 2, sz * q["Size"][2] / 2))
                    for i in range(3):
                        lo_u[i] = min(lo_u[i], q["Offset"][i] + c[i])
                        hi_u[i] = max(hi_u[i], q["Offset"][i] + c[i])
    wp = [m.matrix_world @ v.co for m in meshes for v in m.data.vertices]
    lb = Vector((min(v.x for v in wp), min(v.y for v in wp), min(v.z for v in wp)))
    hb = Vector((max(v.x for v in wp), max(v.y for v in wp), max(v.z for v in wp)))
    lo_m, hi_m = (lb.x, lb.z, lb.y), (hb.x, hb.z, hb.y)
    dev = [round(lo_m[i] - lo_u[i], 2) for i in range(3)] + [round(hi_m[i] - hi_u[i], 2) for i in range(3)]
    print("FOOTPRINT", p.id, "union", [round(v, 2) for v in lo_u], [round(v, 2) for v in hi_u], "dev(lo xyz, hi xyz)", dev)
    tris = sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)
    STATS[p.id] = (len(meshes), tris)
    if not NOVIEW:
        sb = {"Shiba": {"Position": list(shiba), "Facing": 180}} if shiba else BP
        dk.preview(p, f"preview_{p.id}.png", with_shiba=sb, azimuth=az, elevation=el)
    ALL.extend(meshes)
    dk.hide(meshes)
    return meshes


STATS = {}
ALL = []


# ================================================================= 1 Flooring
def flags(p, x0, x1, z0, z1, rows, cols, y0, y1, col, gap=0.3, stagger=True, name="B", j=0.07):
    dz = (z1 - z0) / rows
    for r in range(rows):
        shift = (0.5 if (r % 2 and stagger) else 0.0)
        cuts = [x0]
        wcol = (x1 - x0) / cols
        c = x0 + (wcol * (1 - shift) if shift else wcol * (0.8 + R.random() * 0.4))
        while c < x1 - wcol * 0.4:
            cuts.append(c)
            c += wcol * (0.85 + R.random() * 0.3)
        cuts.append(x1)
        for a, b in zip(cuts[:-1], cuts[1:]):
            bx(p, a + gap / 2, b - gap / 2, y0, y1 - R.random() * 0.03, z0 + r * dz + gap / 2, z0 + (r + 1) * dz - gap / 2,
               shade(col if R.random() > 0.22 else (178, 162, 142), 0.94 + R.random() * 0.1), j, name=name)


def build_flooring():
    p = dk.Part("Flooring")
    # flagstone patio at the gate
    bx(p, 4, 32, Y0, 0.25, 40, 54, STONE_D, 0.04)
    flags(p, 4.2, 31.8, 40.2, 53.8, 3, 6, 0.25, 0.41, STONE)
    # Shiba paw print inlay in the patio
    paw = (228, 216, 192)
    dk.cyl(p, (18, 0.35, 48.4), 2.4, 0.2, paw, verts=8, jitter=0.03, name="I_paw")
    for tx, tz in ((-3.4, -3.2), (-1.2, -5.0), (1.2, -5.0), (3.4, -3.2)):
        dk.cyl(p, (18 + tx, 0.35, 48.4 + tz), 1.1, 0.2, paw, verts=6, jitter=0.03, name="I_paw")
    # stepping stones towards the house
    bx(p, 32, 40, Y0, 0.25, 32, 40, STONE_D, 0.04)
    flags(p, 32.2, 39.8, 32.2, 39.8, 2, 2, 0.25, 0.45, STONE, stagger=False)
    # cobble path
    bx(p, 40, 48, Y0, 0.25, -36, -16, (92, 92, 98), 0.04)
    for r in range(7):
        for c in range(3):
            z = -36 + (r + 0.5) * 20 / 7 + R.uniform(-0.15, 0.15)
            x = 40 + (c + 0.5) * 8 / 3 + R.uniform(-0.15, 0.15)
            bx(p, x - 1.15, x + 1.15, 0.25, 0.45 - R.random() * 0.04, z - 1.1, z + 1.1,
               shade((126, 126, 134), 0.92 + R.random() * 0.14), 0.05, rot=(0, R.uniform(-14, 14), 0), name="B")
    # moss between the stones
    for mx, mz in ((6.5, 41.2), (13.0, 52.5), (26.5, 44.0), (30.5, 52.0), (33.5, 38.5), (38.0, 33.3), (42.0, -34.5), (46.0, -17.5), (41.5, -26.0)):
        bx(p, mx - 0.7, mx + 0.7, 0.25, 0.44, mz - 0.5, mz + 0.5, (86, 140, 70), 0.08, rot=(0, R.uniform(0, 60), 0), name="B")
    # wooden floor of the cottage: planks along x, staggered joints
    bx(p, 49.5, 84.5, Y0, 0.25, -41.5, -10.5, (96, 62, 38), 0.03)
    rows = 10
    dz = 31.0 / rows
    for r in range(rows):
        cut = 55 + R.random() * 20 + (r % 3) * 2
        z0 = -41.5 + r * dz
        for a, b in ((49.5, cut), (cut, 84.5)):
            bx(p, a + 0.07, b - 0.07, 0.25, 0.40, z0 + 0.07, z0 + dz - 0.07,
               shade(WOOD, 0.9 + R.random() * 0.2), 0.05, name="B")
    # rug under the Shiba
    bx(p, 59.5, 74.5, 0.25, 0.43, -32, -20, (214, 188, 140), 0.03, name="R_rug")
    bx(p, 60.5, 73.5, 0.25, 0.45, -31, -21, (176, 62, 58), 0.04, name="R_rug")
    bx(p, 62.0, 72.0, 0.25, 0.45, -29.6, -22.4, (200, 96, 78), 0.03, name="R_rug")
    bx(p, 63.4, 70.6, 0.25, 0.45, -28.2, -23.8, (176, 62, 58), 0.03, name="R_rug")
    return done(p, grouped(p, Rug="R_"), None, -60, 40)


# ================================================================= 2 LittleHouse
def build_house():
    p = dk.Part("LittleHouse")
    CX, CZ = 67.0, -26.0
    YT = 14.0
    # ---- walls (real window openings)
    N = Wall(p, 'x', -41.5, -1)
    S_ = Wall(p, 'x', -10.5, +1)
    E = Wall(p, 'z', 85.0, +1)
    W = Wall(p, 'z', 50.0, -1)
    wn = [(62, 8.0)]
    ws = [(58, 6.4), (77, 6.4)]
    N.wall_run(49.5, 85.5, wn, Y0, YT, 5.0, 10.6, CREAM)
    S_.wall_run(49.5, 85.5, ws, Y0, YT, 5.0, 10.6, CREAM)
    E.wall_run(-41, -11, [(-26, 8.4)], Y0, YT, 5.0, 10.6, BRICK)
    W.wall_run(-41, -35, [(-38, 2.8)], Y0, YT, 5.0, 10.6, BRICK)
    W.wall_run(-17, -11, [(-14, 2.8)], Y0, YT, 5.0, 10.6, BRICK)
    # door header over the wide opening
    W.box(-35, -17, 11.7, YT, -0.5, 0.5, BRICK, 0.05)
    # brick courses on the brick walls
    for yb in (2.6, 12.3):
        E.box(-41, -11, yb, yb + 0.32, 0.5, 0.62, BRICK_D, 0.04, "B")
        if yb < 5:         W.box(-41, -35, yb, yb + 0.32, 0.5, 0.62, BRICK_D, 0.04, "B")
        if yb < 5:         W.box(-17, -11, yb, yb + 0.32, 0.5, 0.62, BRICK_D, 0.04, "B")
    # stone plinth
    N.box(49.3, 85.7, Y0, 1.5, 0.5, 0.9, STONE, 0.05)
    S_.box(49.3, 85.7, Y0, 1.5, 0.5, 0.9, STONE, 0.05)
    E.box(-41, -11, Y0, 1.5, 0.5, 0.9, STONE, 0.05)
    W.box(-41, -35, Y0, 1.5, 0.5, 0.9, STONE, 0.05)
    W.box(-17, -11, Y0, 1.5, 0.5, 0.9, STONE, 0.05)
    # corner pilasters
    for x in (49.3, 85.7):
        for z in (-42.2, -9.8):
            bx(p, x - 0.45, x + 0.45, Y0, YT, z - 0.45, z + 0.45, TRIM, 0.03, name="T_corner")
    # ---- windows
    for uc, w in wn:
        N.window(uc, w, 5.0, 10.6, shutters=True, flowers=False)
    for uc, w in ws:
        S_.window(uc, w, 5.0, 10.6, shutters=True, flowers=True)
    E.window(-26, 8.4, 5.0, 10.6, shutters=False, flowers=False)
    W.window(-38, 2.8, 5.0, 10.6, shutters=False, flowers=True, trim=0.4)
    W.window(-14, 2.8, 5.0, 10.6, shutters=False, flowers=True, trim=0.4)
    # ---- open doorway: timber lintel, knee braces, porch columns, steps
    W.box(-35.4, -16.6, 11.0, 12.5, 0.5, 1.5, WOOD_D, 0.05, "T_beam")
    for sd, zc in ((1, -35.0), (-1, -17.0)):
        W.box(zc - 0.55, zc + 0.55, 11.0, 12.5, 0.5, 1.5, WOOD_D, 0.05, "T_beam")
        W.box(zc - 0.2, zc + 0.2, 8.6, 11.0, 0.5, 1.2, WOOD_D, 0.04, "T_beam")
    for z in (-35.7, -16.3):
        # column + base + capital
        bx(p, 47.2, 48.3, 0.5, YT, z - 0.55, z + 0.55, TRIM, 0.02, name="T_col")
        bx(p, 46.9, 48.6, 0.5, 1.5, z - 0.85, z + 0.85, STONE, 0.04, name="T_col")
        bx(p, 46.9, 48.6, YT - 0.8, YT, z - 0.85, z + 0.85, TRIM, 0.03, name="T_col")
    bx(p, 45.5, 49.5, Y0, 0.3, -35, -17, STONE_D, 0.04)
    bx(p, 46.7, 49.5, 0.3, 0.55, -34.2, -17.8, STONE, 0.04)
    # ---- fireplace chimney (inside the house, rises through the roof)
    bx(p, 77.4, 82.6, 0.0, 4.4, -40.6, -35.4, BRICK, 0.06)
    bx(p, 78.9, 81.1, 0.45, 2.9, -35.45, -35.3, DARK, 0.02, name="T_fire")
    bx(p, 77.2, 82.8, 4.4, 4.9, -40.7, -35.2, WOOD_D, 0.04, name="T_beam")
    bx(p, 78, 82, 4.9, 19.4, -40, -36, BRICK, 0.06)
    for yb in (9.0, 14.5):
        bx(p, 77.8, 82.2, yb, yb + 0.35, -40.2, -35.8, BRICK_D, 0.04)
    bx(p, 77.5, 82.5, 19.4, 20.0, -40.5, -35.5, STONE, 0.04)
    for dx in (-1.0, 1.0):
        dk.cyl(p, (80 + dx, 20.55, -38), 0.72, 1.1, (130, 70, 56), verts=7, top_radius=0.6, jitter=0.05, name="B")
    octa(p, (79.4, 21.7, -38), 0.8, (236, 236, 242), sy=0.9, j=0.03, name="T_smoke")
    octa(p, (80.9, 22.06, -37.6), 0.6, (222, 224, 232), sy=0.9, j=0.03, name="T_smoke")
    # the fire: two logs and flames on the hearth
    for dx in (-0.45, 0.45):
        dk.cyl(p, (80, 0.85, -35.1 + dx), 0.32, 2.4, WOOD_D, axis="x", verts=5, jitter=0.05, rot=(0, 0, 0), name="T_fire")
    octa(p, (79.7, 1.8, -35.1), 0.75, (232, 120, 50), sy=1.3, j=0.05, name="T_fire")
    octa(p, (80.5, 1.7, -35.1), 0.65, (240, 170, 60), sy=1.3, j=0.05, name="T_fire")
    # ---- roof: hip roof in five red shingle courses (separate mesh so it can be hidden for the cutaway)
    n, rise, run = 5, 7.0, 17.6
    for i in range(n):
        d0, d1 = i * run / n, (i + 1) * run / n
        y0, y1 = YT + i * rise / n, YT + (i + 1) * rise / n
        rings = [rr(CX, CZ, 20 - d0, 18 - d0, y0), rr(CX, CZ, 20 - d0, 18 - d0, y0 + 0.32), rr(CX, CZ, 20 - d1, 18 - d1, y1)]
        col = shade(ROOF, 1.0 if i % 2 == 0 else 0.9)
        loft(p, rings, col, 0.04, name="R_course")
    bx(p, CX - 3.2, CX + 3.2, YT + rise - 0.25, YT + rise + 0.3, CZ - 0.8, CZ + 0.8, ROOF_D, 0.04, name="R_ridge")
    g = grouped(p, Roof="R_", Trim="T_")
    return done(p, g, None, -105, 20)


# ================================================================= 3 BonkedSign
GLYPHS = {
    'B': [(0, 0, 1, 5), (1, 4, 2.6, 5), (1, 2, 2.6, 3), (1, 0, 2.6, 1), (2, 3, 3, 4), (2, 1, 3, 2)],
    'O': [(0, 0, 1, 5), (2, 0, 3, 5), (1, 4, 2, 5), (1, 0, 2, 1)],
    'N': [(0, 0, 1, 5), (2, 0, 3, 5)],
    'K': [(0, 0, 1, 5)],
    'E': [(0, 0, 1, 5), (1, 4, 3, 5), (1, 2, 2.6, 3), (1, 0, 3, 1)],
    'D': [(0, 0, 1, 5), (1, 4, 2.4, 5), (1, 0, 2.4, 1), (2, 1, 3, 4)],
    'G': [(0, 4, 3, 5), (0, 1, 1, 4), (0, 0, 3, 1), (2, 1, 3, 2.6), (1.4, 1.8, 3, 2.6)],
    'T': [(0, 4, 3, 5), (1, 0, 2, 4)],
}
DIAGS = {'N': [((0.5, 5), (2.5, 0))], 'K': [((1, 2.5), (3, 5)), ((1, 2.5), (3, 0))]}


def letter(p, ch, x0, y0, w, h, z0, z1, col):
    cw, chh = w / 3, h / 5
    for a, b, c, d in GLYPHS[ch]:
        bx(p, x0 + a * cw, x0 + c * cw, y0 + b * chh, y0 + d * chh, z0, z1, col, 0.04, name="L_text")
    for (a, b) in DIAGS.get(ch, []):
        ax, ay = x0 + a[0] * cw, y0 + a[1] * chh
        bx2, by2 = x0 + b[0] * cw, y0 + b[1] * chh
        dx, dy = bx2 - ax, by2 - ay
        L = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(-dx, dy))
        dk.box(p, ((ax + bx2) / 2, (ay + by2) / 2, (z0 + z1) / 2), (cw * 0.95, L + 0.05, z1 - z0), col, rot=(0, 0, ang),
               jitter=0.04, name="L_text")


def word(p, text, xc, y0, lw, h, gap, z0, z1, col):
    total = len(text) * lw + (len(text) - 1) * gap
    x = xc - total / 2
    for ch in text:
        letter(p, ch, x, y0, lw, h, z0, z1, col)
        x += lw + gap


def bone_icon(p, xc, yc, z0, z1, col=(250, 250, 244)):
    bx(p, xc - 1.1, xc + 1.1, yc - 0.22, yc + 0.22, z0, z1, col, 0.02, name="L_icon")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx(p, xc + sx * 1.1 - 0.35, xc + sx * 1.1 + 0.35, yc + sy * 0.3 - 0.3, yc + sy * 0.3 + 0.3, z0, z1, col, 0.02,
               name="L_icon")


def build_sign():
    p = dk.Part("BonkedSign")
    for x in (26, 46):
        dk.cyl(p, (x, 6.75, 28), 0.8, 13.5, WOOD, verts=8, jitter=0.06, name="B")
        dk.ball(p, (x, 13.5, 28), 0.55, WOOD_L, subdiv=1, jitter=0.05, name="B")
        bx(p, x - 0.85, x + 0.85, 0, 0.45, 27.15, 28.85, STONE, 0.05)
    # backing frame + yellow board
    bx(p, 24, 48, 5.0, 13.3, 27.4, 28.6, (250, 200, 60), 0.025, name="Y_board")
    # plank seams
    for y in (7.0, 9.0, 11.0):
        bx(p, 24.05, 47.95, y - 0.05, y + 0.05, 28.55, 28.63, (222, 172, 40), 0.02, name="Y_board")
    # red rails and side stiles
    bx(p, 24, 48, 12.4, 13.3, 28.3, 29.0, ROOF, 0.04, name="B")
    bx(p, 24, 48, 5.0, 5.9, 28.3, 29.0, ROOF, 0.04, name="B")
    bx(p, 24, 24.9, 5.0, 13.3, 28.3, 29.0, ROOF, 0.04, name="B")
    bx(p, 47.1, 48, 5.0, 13.3, 28.3, 29.0, ROOF, 0.04, name="B")
    # braces behind
    bx(p, 24.5, 47.5, 6.0, 6.5, 27.2, 27.45, WOOD_D, 0.04)
    # lettering
    brown = (92, 52, 34)
    word(p, "GET", 36, 10.1, 1.9, 2.0, 0.55, 28.6, 29.0, brown)
    word(p, "BONKED", 36, 6.25, 3.0, 3.4, 0.55, 28.6, 29.0, brown)
    bone_icon(p, 29.0, 11.1, 28.6, 28.95)
    bone_icon(p, 43.0, 11.1, 28.6, 28.95)
    return done(p, grouped(p, Board="Y_", Text="L_"), (36, 36), 150, 26)


# ================================================================= 4 Garage
def build_garage():
    p = dk.Part("Garage")
    GX0, GX1, ZB, ZF = -86.0, -50.0, 14.0, 38.5
    WH = 10.0
    # floor + walls
    bx(p, -85, -51, 0, 0.22, 14.5, 39.0, STONE, 0.04, name="B")
    bx(p, GX0, GX1, 0, WH, 13.5, 14.5, BRICK, 0.06)
    for yb in (2.2, 3.8, 8.3):
        bx(p, GX0, GX1, yb, yb + 0.3, 14.5, 14.62, BRICK_D, 0.04)       # inside courses
        bx(p, GX0, GX1, yb, yb + 0.3, 13.38, 13.5, BRICK_D, 0.04)       # outside courses
    L = Wall(p, 'z', -85.5, -1)
    Rw = Wall(p, 'z', -50.5, +1)
    for Wl in (L, Rw):
        Wl.wall_run(13.5, 38.5, [(27, 6.0)], 0, WH, 4.2, 8.0, CREAM)
        Wl.box(13.5, 38.5, 0, 1.4, 0.5, 0.9, STONE, 0.05)
        Wl.window(27, 6.0, 4.2, 8.0, shutters=True, flowers=False, trim=0.4)
    # front frame: corner posts + header
    for x in (-86.0, -50.0):
        bx(p, x - 0.85, x + 0.85, 0, WH, 37.7, 39.4, TRIM, 0.02, name="T_post")
    bx(p, GX0 - 0.5, GX1 + 0.5, 8.5, WH, 38.3, 39.3, CREAM, 0.03, name="T_post")
    bx(p, GX0 - 0.5, GX1 + 0.5, 8.3, 8.7, 39.0, 39.55, WOOD_D, 0.04, name="T_post")
    bx(p, -72, -64, 8.9, 9.8, 39.3, 39.55, WOOD, 0.03, name="T_post")        # plaque
    bone_icon(p, -68, 9.35, 39.55, 39.7, (250, 250, 244))
    # gable triangles (cream) under the roof ends
    dk.prism(p, (-68, WH, 26), 36, 20.7, 2.3, CREAM, ridge='x', jitter=0.03, name="B")
    # roof: slate shingle courses, ridge along x
    k = 3.0 / 13.5
    al = math.atan(k)
    sa, ca = math.sin(al), math.cos(al)
    ypk, zc = 12.85, 26.0
    Ls = math.hypot(13.5, 3.0)
    ncs = 3
    t = 0.45
    for sgn in (1, -1):
        for i in range(ncs):
            seg = Ls / ncs
            s_mid = (i + 0.5) * seg
            sz = zc + sgn * s_mid * ca
            sy = ypk - s_mid * sa
            nz, ny = sgn * sa, ca
            raise_ = (ncs - 1 - i) * 0.06
            cz = sz - nz * (t / 2) + nz * raise_
            cy = sy - ny * (t / 2) + ny * raise_
            dk.box(p, (-68, cy, cz), (38, t, seg + 0.3), shade(SLATE, 1.0 if i % 2 == 0 else 0.88),
                   rot=(sgn * math.degrees(al), 0, 0), jitter=0.04, name="R_slab")
    bx(p, -87, -49, 12.75, 13.0, 25.2, 26.8, (66, 68, 78), 0.03, name="R_ridge")
    bx(p, -87, -49, 9.1, 9.8, 39.3, 39.6, CREAM, 0.03, name="T_post")                  # fascia boards
    bx(p, -87, -49, 9.1, 9.8, 12.4, 12.7, CREAM, 0.03, name="T_post")
    for x in (-86.25, -49.75):
        bx(p, x - 0.15, x + 0.15, 10.2, 11.3, 25.2, 26.8, (84, 90, 104), 0.03, name="T_post")   # gable vents
    # ---- the little blue car (nose to +x)
    car = (60, 120, 200)
    cz0, cz1 = 22.75, 29.25
    bx(p, -75, -61, 1.4, 4.4, cz0, cz1, car, 0.04, name="C_body")
    bx(p, -75.3, -74.7, 1.9, 3.3, cz0 + 0.3, cz1 - 0.3, (190, 190, 196), 0.03, name="C_body")    # rear bumper
    bx(p, -61.3, -60.7, 1.9, 3.3, cz0 + 0.3, cz1 - 0.3, (190, 190, 196), 0.03, name="C_body")    # front bumper
    for z in (cz0 + 0.8, cz1 - 0.8):
        bx(p, -61.1, -60.8, 2.5, 3.5, z - 0.5, z + 0.5, (255, 244, 190), 0.02, name="C_body")
        bx(p, -75.1, -74.8, 2.5, 3.5, z - 0.5, z + 0.5, (200, 40, 40), 0.02, name="C_body")
    # cabin (glass trapezoid) + roof plate + pillars
    pts = [(-72.5, 4.4), (-64.0, 4.4), (-66.0, 7.0), (-71.0, 7.0)]
    zs = (cz0 + 0.15, cz1 - 0.15)
    gp = [(x, y, zs[0]) for x, y in pts] + [(x, y, zs[1]) for x, y in pts]
    gf = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    dk.poly(p, (0, 0, 0), gp, gf, (140, 196, 232), 0.03, name="C_glass")
    cp = [(-71.4, 7.0, cz0 + 0.0), (-65.6, 7.0, cz0 + 0.0), (-65.6, 7.35, cz0), (-71.4, 7.35, cz0)]
    bx(p, -71.6, -65.4, 7.0, 7.4, cz0, cz1, car, 0.04, name="C_body")
    bx(p, -69.3, -68.7, 4.4, 7.0, cz0 - 0.1, cz1 + 0.1, car, 0.03, name="C_body")
    for x0, x1, ya, yb in ((-72.9, -72.0, 4.4, 4.7), ):
        pass
    # wheels (lying along z) with hubs
    for x in (-72.6, -63.4):
        for z in (22.2, 29.8):
            dk.cyl(p, (x, 1.7, z), 1.7, 1.2, (30, 30, 34), axis='z', verts=10, jitter=0.03, name="C_wheel")
            dk.cyl(p, (x, 1.7, z + (-0.05 if z < 26 else 0.05)), 0.8, 1.3, (176, 176, 184), axis='z', verts=8, jitter=0.03,
                   name="C_wheel")
    # shelf in the back corner with paint cans
    for x in (-84.6, -79.2):
        bx(p, x - 0.2, x + 0.2, 0.22, 7.2, 14.6, 16.4, WOOD_D, 0.04)
    for y in (2.2, 4.6, 7.0):
        bx(p, -84.8, -79.0, y, y + 0.3, 14.6, 16.4, WOOD, 0.04)
    dk.cyl(p, (-83.4, 3.0, 15.5), 0.65, 0.9, (200, 50, 50), verts=8, jitter=0.04, name="B")
    dk.cyl(p, (-82.0, 3.0, 15.5), 0.65, 0.9, (60, 120, 200), verts=8, jitter=0.04, name="B")
    bx(p, -83.0, -80.5, 2.5, 4.3, 14.7, 16.2, (180, 140, 90), 0.05)
    bx(p, -83.6, -81.0, 4.9, 6.1, 14.7, 16.2, (180, 140, 90), 0.05)
    g = grouped(p, Roof="R_", Car="C_", Trim="T_")
    return done(p, g, (-68, 47), 150, 14)


# ================================================================= 5 Mailbox
def build_mailbox():
    p = dk.Part("Mailbox")
    red = (200, 50, 50)
    dk.cyl(p, (62, 0.15, 44), 1.3, 0.3, STONE_D, verts=8, jitter=0.05, name="B")
    bx(p, 61.55, 62.45, 0.0, 5.7, 43.55, 44.45, WOOD, 0.05, name="B")
    bx(p, 60.6, 63.4, 5.1, 5.7, 43.6, 44.4, WOOD_D, 0.04, name="B")                      # bracket
    # loaf: box + half barrel on top
    bx(p, 60.2, 64.0, 5.7, 7.0, 42.7, 45.3, red, 0.04, name="M_box")
    dk.cyl(p, (62.1, 7.0, 44), 1.3, 3.8, red, axis='x', verts=10, jitter=0.04, name="M_box")
    bx(p, 60.0, 60.25, 5.7, 8.3, 42.7, 45.3, shade(red, 0.82), 0.03, name="M_box")        # door
    dk.ball(p, (60.32, 7.0, 44), 0.28, (240, 220, 120), subdiv=1, jitter=0.03, name="M_box")
    # a letter for the Shiba on top, with a red seal
    bx(p, 61.3, 63.1, 8.3, 8.42, 43.6, 44.5, (250, 248, 240), 0.02, rot=(0, 12, 0), name="M_box")
    bx(p, 62.0, 62.4, 8.42, 8.5, 43.95, 44.2, (220, 60, 70), 0.02, rot=(0, 12, 0), name="M_box")
    # flag
    bx(p, 64.0, 64.4, 6.2, 8.3, 43.4, 43.8, (120, 120, 126), 0.03, name="M_flag")
    bx(p, 64.15, 64.65, 8.1, 9.2, 43.4, 45.2, (250, 220, 60), 0.03, name="M_flag")
    bx(p, 64.0, 64.4, 5.9, 6.4, 43.3, 43.9, (120, 120, 126), 0.03, name="M_flag")
    # house number plate + little flowers at the foot
    # white Shiba paw print on the side
    bx(p, 61.55, 62.45, 5.85, 6.4, 45.3, 45.34, (245, 245, 240), 0.02, name="M_box")
    for tx in (-0.55, -0.18, 0.18, 0.55):
        bx(p, 62 + tx - 0.12, 62 + tx + 0.12, 6.5 + (0.1 if abs(tx) < 0.3 else 0.0), 6.88 + (0.1 if abs(tx) < 0.3 else 0.0), 45.3, 45.34, (245, 245, 240), 0.02, name="M_box")
    for i, (x, z) in enumerate(((60.9, 43.2), (63.2, 44.9), (60.8, 44.8), (63.3, 43.1))):
        dk.cone(p, (x, 0.0, z), 0.3, 0.5, (70, 150, 70), verts=5, jitter=0.05, name="B")
        dk.ball(p, (x, 0.65, z), 0.3, FLOWERS[i], subdiv=1, jitter=0.05, name="B")
    return done(p, grouped(p, Box="M_"), (70, 44), 150, 24)


# ================================================================= 6 Fence
def build_fence():
    p = dk.Part("Fence")
    W_ = (245, 245, 240)
    xs = [66, 71.5, 77, 82.5, 88]
    for x in xs:
        bx(p, x - 0.6, x + 0.6, 0, 5.9, 37.4, 38.6, W_, 0.03, name="B")
        dk.prism(p, (x, 5.9, 38.0), 1.4, 1.4, 0.7, shade(W_, 0.96), ridge='z', jitter=0.02, name="B")
    # rails behind pickets
    bx(p, 65.5, 88.5, 1.8, 2.6, 37.5, 37.95, (225, 224, 218), 0.03, name="B")
    bx(p, 65.5, 88.5, 4.6, 5.4, 37.5, 37.95, (225, 224, 218), 0.03, name="B")
    # pickets: 3 per bay, pointed tops
    for a, b in zip(xs[:-1], xs[1:]):
        for i in range(3):
            x = a + 0.6 + (b - a - 1.2) * (i + 0.5) / 3
            h = 4.8 + (0.0 if i != 1 else 0.0)
            bx(p, x - 0.5, x + 0.5, 0.0, h, 37.85, 38.35, W_, 0.03, name="P_picket")
            dk.prism(p, (x, h, 38.1), 1.0, 0.5, 0.75, W_, ridge='z', jitter=0.03, name="P_picket")
    # climbing roses along the middle bays
    for i in range(28):
        x = 66.6 + i * 0.78
        y = 4.5 + 0.4 * math.sin(i * 0.9)
        octa(p, (x, y, 38.4), 0.6, (60 + R.randint(0, 30), 140 + R.randint(0, 25), 62), sy=0.7, j=0.07, name="V_rose")
        if i % 3 == 1:
            octa(p, (x + 0.3, y + 0.5, 38.5), 0.5, FLOWERS[(i // 3) % 4], sy=0.9, j=0.05, name="V_rose")
    # tiny grass tufts at the foot
    return done(p, grouped(p, Roses="V_"), (77, 46), 150, 22)


# ================================================================= 7 Garden
def build_garden():
    p = dk.Part("Garden")
    xa, xb = -55.0, -33.0
    for zc in (2.0, -10.0):
        z0, z1 = zc - 3.5, zc + 3.5
        bx(p, xa, xb, 0.0, 1.5, z0, z1, SOIL, 0.07, name="B")
        bx(p, xa, xb, 0.0, 1.8, z0, z0 + 0.5, WOOD, 0.05, name="W_edge")
        bx(p, xa, xb, 0.0, 1.8, z1 - 0.5, z1, WOOD, 0.05, name="W_edge")
        bx(p, xa, xa + 0.5, 0.0, 1.8, z0, z1, WOOD, 0.05, name="W_edge")
        bx(p, xb - 0.5, xb, 0.0, 1.8, z0, z1, WOOD, 0.05, name="W_edge")
        for x in (xa, xb):
            for z in (z0, z1):
                sx = 0.8 if x == xa else -0.8
                sz = 0.8 if z == z0 else -0.8
                bx(p, x, x + sx, 0.0, 2.2, z, z + sz, WOOD_L, 0.04, name="W_edge")
        k = 0
        for row, dz in enumerate((-1.5, 1.5)):
            for i in range(7):
                x = xa + 2.2 + i * 2.75 + (0.7 if row else 0.0)
                if x > xb - 1.8:
                    continue
                z = zc + dz + R.uniform(-0.3, 0.3)
                hc = R.uniform(2.45, 3.2)
                dk.cyl(p, (x, 0.9 + (hc - 0.9) / 2 + 0.2, z), 0.17, hc - 0.9, (60, 130, 60), verts=3, jitter=0.05, name="B")
                dk.ball(p, (x, hc, z), 0.8, FLOWERS[(k + row) % 5], subdiv=1, jitter=0.08, name="F_bloom")
                k += 1
        for i in range(7):
            x = xa + 1.3 + i * 3.1 + R.uniform(-0.3, 0.3)
            for dz in (-2.6, 2.6):
                dk.cone(p, (x, 1.4, zc + dz * 0.9 + R.uniform(-.2, .2)), 0.7, 0.9, (60 + R.randint(0, 20), 140, 60), verts=5,
                        jitter=0.06, name="B")
    # stepping stones between the beds
    for i in range(5):
        x = -52.5 + i * 4.0
        bx(p, x - 1.4, x + 1.4, 0.0, 0.2, -4.0 - 1.4 + R.uniform(-0.3, 0.3), -4.0 + 1.4, STONE, 0.06,
           rot=(0, R.uniform(-15, 15), 0), name="B")
    # garden gnome at the end of the path
    gx, gz = -34.8, -4.0
    bx(p, gx - 0.6, gx + 0.6, 0.0, 1.2, gz - 0.55, gz + 0.55, (60, 100, 190), 0.03, name="B")
    dk.ball(p, (gx, 1.55, gz), 0.5, (240, 200, 170), subdiv=1, jitter=0.03, name="B")
    dk.cone(p, (gx, 0.9, gz + 0.35), 0.55, 0.9, (245, 245, 240), verts=5, jitter=0.03, name="B")
    dk.cone(p, (gx, 1.75, gz), 0.62, 1.5, (210, 40, 50), verts=6, jitter=0.04, name="B")
    return done(p, grouped(p), (-30, -4), 200, 36)


# ================================================================= 8 Tree
def build_tree():
    p = dk.Part("Tree")
    cx, cz = -62.0, -30.0
    # trunk (flared), roots, branches
    dk.cyl(p, (cx, 7.0, cz), 3.2, 14.0, (110, 76, 44), verts=8, top_radius=2.15, jitter=0.07, name="T_trunk")
    dk.cyl(p, (cx, 15.5, cz), 2.1, 4.0, (104, 70, 40), verts=8, top_radius=1.6, jitter=0.07, name="T_trunk")
    for a in range(5):
        ang = a * 72 + 20
        rx, rz = cx + 3.0 * math.cos(math.radians(ang)), cz + 3.0 * math.sin(math.radians(ang))
        dk.box(p, (rx, 0.45, rz), (2.4, 0.9, 1.0), (100, 68, 40), rot=(0, -ang, 0), jitter=0.07, name="T_trunk")
    th = 70
    dk.cyl(p, (cx - 4.7, 11.7, cz), 0.9, 10.0, (110, 76, 44), verts=6, top_radius=0.7, rot=(0, 0, th), jitter=0.06, name="T_trunk")
    dk.cyl(p, (cx + 4.0, 13.2, cz + 1.0), 0.8, 8.0, (110, 76, 44), verts=6, top_radius=0.6, rot=(0, 0, -62), jitter=0.06,
           name="T_trunk")
    # swing from the left branch
    for dz in (-0.9, 0.9):
        dk.cyl(p, (cx - 5.6, 8.0, cz + dz), 0.1, 7.2, (200, 170, 120), verts=3, jitter=0.03, name="S_swing")
    bx(p, cx - 7.1, cx - 4.1, 4.2, 4.6, cz - 1.3, cz + 1.3, WOOD_L, 0.05, name="S_swing")
    # layered canopy
    def blob(x, y, z, r, col, sc=(1, 1, 1), sub=2):
        o = dk.ball(p, (x, y, z), r, col, scale=sc, subdiv=sub, jitter=0.07, name="C_leaf")
        wobble(o, 0.07, seed=int(x * 7 + y * 3 + z))
    # three flat pads (layers) topped by a crown, plus side clumps so the outline stays lumpy
    blob(cx, 17.5, cz, 13.0, (62, 140, 66), (1, 0.46, 1))
    blob(cx + 0.5, 23.8, cz - 0.5, 11.2, (74, 156, 74), (1, 0.52, 1))
    blob(cx - 0.5, 29.0, cz + 0.5, 9.0, (88, 172, 82), (1, 0.55, 1))
    blob(cx, 33.2, cz, 6.6, (104, 188, 92), (1, 0.88, 1))
    blob(cx - 10, 20.5, cz - 4, 8.5, (80, 165, 80), (1, 0.7, 1))
    blob(cx + 10, 20.5, cz + 4, 7.6, (66, 146, 70), (1, 0.7, 1))
    blob(cx + 1, 21.0, cz - 7.2, 5.8, (72, 152, 72), (1, 0.7, 1))
    blob(cx - 2, 21.0, cz + 7.2, 5.8, (90, 172, 84), (1, 0.7, 1))
    blob(cx + 6, 28.0, cz - 4, 5.0, (96, 180, 88), (1, 0.7, 1))
    blob(cx - 6, 27.0, cz + 3.5, 5.0, (82, 164, 80), (1, 0.7, 1))
    # apples
    for ang, y, rr_ in ((10, 16.2, 11.4), (110, 15.8, 10.8), (200, 16.0, 11.2), (290, 15.4, 10.5), (60, 21.0, 12.0)):
        x = cx + rr_ * math.cos(math.radians(ang))
        z = cz + rr_ * math.sin(math.radians(ang))
        dk.ball(p, (x, y, z), 0.7, (220, 50, 50), subdiv=1, jitter=0.06, name="C_leaf")
    # rocks and flowers at the base
    for (x, z, r) in ((cx + 4.2, cz - 2.0, 0.9), (cx - 3.0, cz + 3.8, 0.7), (cx + 2.5, cz + 4.0, 0.6)):
        dk.ball(p, (x, r * 0.5, z), r, STONE, scale=(1, 0.7, 1), subdiv=1, jitter=0.08, name="T_trunk")
    for i, (x, z) in enumerate(((cx - 4.3, cz - 2.4), (cx - 5.0, cz - 1.0), (cx + 1.0, cz + 4.6))):
        dk.cone(p, (x, 0.0, z), 0.3, 0.5, (70, 150, 70), verts=5, name="T_trunk")
        dk.ball(p, (x, 0.7, z), 0.35, FLOWERS[i], subdiv=1, name="T_trunk")
    return done(p, grouped(p, Trunk="T_", Swing="S_", Canopy="C_"), (-62, -12), 200, 22)


# ================================================================= 9 DoghouseBench
def build_doghouse():
    p = dk.Part("DoghouseBench")
    red, redd = (208, 84, 70), (166, 62, 54)
    # ---- doghouse (hollow, open door)
    zf = -20.0
    bx(p, -4, 4, 0, 0.3, -28, zf, WOOD_D, 0.04)                                  # floor
    bx(p, -4, -3.6, 0.3, 5.0, -28, zf, red, 0.05)                                # side walls
    bx(p, 3.6, 4, 0.3, 5.0, -28, zf, red, 0.05)
    bx(p, -4, 4, 0.3, 5.0, -28, -27.6, red, 0.05)                                # back wall
    bx(p, -3.6, -1.7, 0.3, 5.0, zf - 0.4, zf, red, 0.05)                         # front piers + lintel
    bx(p, 1.7, 3.6, 0.3, 5.0, zf - 0.4, zf, red, 0.05)
    bx(p, -1.7, 1.7, 4.0, 5.0, zf - 0.4, zf, red, 0.05)
    # dark liner inside + dog bed
    bx(p, -3.6, 3.6, 0.3, 4.0, -27.6, -27.4, (60, 36, 30), 0.03)
    bx(p, -3.6, -3.4, 0.3, 4.0, -27.6, zf - 0.4, (60, 36, 30), 0.03)
    bx(p, 3.4, 3.6, 0.3, 4.0, -27.6, zf - 0.4, (60, 36, 30), 0.03)
    bx(p, -3.0, 3.0, 0.3, 0.8, -27.0, -22.0, (200, 150, 70), 0.04)
    # wood trim around the door and corners, battens on the sides
    bx(p, -2.15, -1.7, 0.0, 4.5, zf, zf + 0.3, WOOD_L, 0.03, name="T_trim")
    bx(p, 1.7, 2.15, 0.0, 4.5, zf, zf + 0.3, WOOD_L, 0.03, name="T_trim")
    bx(p, -2.15, 2.15, 4.0, 4.5, zf, zf + 0.3, WOOD_L, 0.03, name="T_trim")
    for x in (-4.1, 4.1):
        bx(p, x - 0.2, x + 0.2, 0.0, 5.1, zf - 0.1, zf + 0.2, WOOD_L, 0.03, name="T_trim")
        bx(p, x - 0.2, x + 0.2, 0.0, 5.1, -28.1, -27.7, WOOD_L, 0.03, name="T_trim")
    for x in (-3.0, 3.0):
        bx(p, x - 0.15, x + 0.15, 0.3, 4.9, zf, zf + 0.15, redd, 0.03, name="T_trim")
    for sd in (-1, 1):
        for z in (-26.0, -24.0, -22.0):
            bx(p, sd * 4.0 - (0.0 if sd < 0 else 0.1), sd * 4.0 + (0.1 if sd > 0 else 0.0) + (-0.1 if sd < 0 else 0.0),
               0.3, 4.9, z - 0.15, z + 0.15, redd, 0.03, name="T_trim")
    # gable triangle + roof
    dk.prism(p, (0, 5.0, -24), 8.0, 8.0, 2.0, red, ridge='z', jitter=0.04, name="B")
    al = math.atan2(2.0, 5.0)
    sa, ca = math.sin(al), math.cos(al)
    Lsl, t = 5.6, 0.5
    for sd in (1, -1):
        mx, my = sd * 2.5, 6.1
        nx, ny = sd * sa, ca
        dk.box(p, (mx - nx * t / 2, my - ny * t / 2 - 0.1, -24), (Lsl, t, 10.0), ROOF, rot=(0, 0, -sd * math.degrees(al)),
               jitter=0.05, name="R_roof")
    bx(p, -0.45, 0.45, 6.9, 7.3, -29.0, -19.0, ROOF_D, 0.04, name="R_roof")
    # bone sign above the door
    bx(p, -1.0, 1.0, 5.15, 5.55, zf, zf + 0.4, (250, 250, 244), 0.02, name="T_trim")
    for sx in (-1, 1):
        for sy in (-1, 1):
            octa(p, (sx * 1.05, 5.35 + sy * 0.25, zf + 0.25), 0.33, (250, 250, 244), sy=1.0, j=0.02, name="T_trim")
    # food bowl and ball
    dk.cyl(p, (7.0, 0.35, -21.8), 1.2, 0.7, (220, 90, 70), verts=8, top_radius=1.4, jitter=0.04, name="B")
    dk.cyl(p, (7.0, 0.72, -21.8), 0.95, 0.1, (150, 110, 70), verts=8, jitter=0.04, name="B")
    dk.ball(p, (9.2, 0.55, -22.5), 0.55, (200, 230, 70), subdiv=1, jitter=0.03, name="B")
    # ---- bench: iron ends, 3 plank seat, 3 slat back
    iron = (60, 60, 66)
    for x0, x1 in ((12.0, 13.0), (23.0, 24.0)):
        bx(p, x0, x1, 0.0, 2.7, -27.5, -26.6, iron, 0.03, name="I_iron")     # back leg
        bx(p, x0, x1, 0.0, 2.7, -25.2, -24.5, iron, 0.03, name="I_iron")     # front leg
        bx(p, x0, x1, 2.4, 2.7, -27.5, -24.5, iron, 0.03, name="I_iron")     # seat rail
        bx(p, x0, x1, 2.7, 7.3, -27.9, -27.3, iron, 0.03, name="I_iron")     # back post
        bx(p, x0, x1, 4.6, 5.0, -27.6, -24.5, iron, 0.03, name="I_iron")     # arm
        bx(p, x0, x1, 2.7, 4.8, -25.0, -24.6, iron, 0.03, name="I_iron")     # arm support
    for i in range(3):
        z0 = -27.6 + i * 1.15
        bx(p, 12.0, 24.0, 2.7, 3.7, z0, z0 + 1.0, WOOD, 0.05, name="B")
    for i in range(3):
        y0 = 3.95 + i * 1.12
        bx(p, 13.0, 23.0, y0, y0 + 0.95, -27.85, -27.35, WOOD_L, 0.05, name="B")
    return done(p, grouped(p, Trim="T_", Roof="R_", Iron="I_"), (10, -14), 150, 26)


# ================================================================= 10 Fountain
def build_fountain():
    p = dk.Part("Fountain")
    cx, cz = -24.0, -38.0
    stone, stoned = STONE, STONE_D
    # basin wall, rim cap, floor
    tube(p, cx, cz, 9.0, 11.0, 0.0, 2.7, stone, n=16, name="B")
    tube(p, cx, cz, 8.8, 11.0, 2.7, 3.0, STONE_L, n=16, name="B")
    for k in range(8):
        a = k * 45 + 22.5
        x, z = cx + 10.0 * math.cos(math.radians(a)), cz + 10.0 * math.sin(math.radians(a))
        dk.box(p, (x, 3.3, z), (1.5, 0.6, 1.5), STONE_L, rot=(0, -a, 0), jitter=0.05, name="B")
    # pedestal, bowl, column
    dk.cyl(p, (cx, 1.6, cz), 3.4, 3.2, stoned, verts=10, top_radius=2.6, jitter=0.06, name="B")
    dk.cyl(p, (cx, 4.0, cz), 2.0, 5.6, stone, verts=10, jitter=0.05, name="B")
    dk.cyl(p, (cx, 6.05, cz), 3.0, 1.5, stone, verts=12, top_radius=5.4, jitter=0.05, name="B")
    dk.cyl(p, (cx, 7.0, cz), 5.4, 0.4, STONE_L, verts=12, jitter=0.05, name="B")
    dk.cyl(p, (cx, 8.3, cz), 1.5, 2.6, stone, verts=10, jitter=0.05, name="B")
    # water
    dk.cyl(p, (cx, 1.8, cz), 8.95, 1.5, WATER, verts=16, jitter=0.05, name="W_water")
    dk.cyl(p, (cx, 7.3, cz), 4.6, 0.5, WATER, verts=12, jitter=0.05, name="W_water")
    # eight water spouts falling from the bowl rim into the basin
    for k in range(8):
        a0, a1 = math.radians(k * 45 - 8), math.radians(k * 45 + 8)
        def quad(r0, r1, y):
            return [(cx + r0 * math.cos(a0), y, cz + r0 * math.sin(a0)), (cx + r0 * math.cos(a1), y, cz + r0 * math.sin(a1)),
                    (cx + r1 * math.cos(a1), y, cz + r1 * math.sin(a1)), (cx + r1 * math.cos(a0), y, cz + r1 * math.sin(a0))]
        loft(p, [quad(5.0, 5.6, 6.9), quad(6.7, 7.2, 2.65)], (132, 204, 242), 0.05, name="W_water")
    for k in range(8):
        a = k * 45
        octa(p, (cx + 6.95 * math.cos(math.radians(a)), 2.7, cz + 6.95 * math.sin(math.radians(a))), 0.8,
             (224, 242, 252), sy=0.5, j=0.04, name="W_water")
    # golden bone
    gold = GOLD
    dk.cyl(p, (cx, 9.8, cz), 1.2, 0.8, gold, verts=8, jitter=0.07, name="G_gold")
    dk.cyl(p, (cx, 11.0, cz), 0.95, 9.0, gold, axis='x', verts=8, jitter=0.07, name="G_gold")
    for sx in (-5, 5):
        for sz in (-1, 1):
            dk.ball(p, (cx + sx, 11.0, cz + sz), 1.5, gold, subdiv=2, jitter=0.09, name="G_gold")
    return done(p, grouped(p, Water="W_", Gold="G_"), (-24, -22), 180, 30)


BUILDERS = [("Flooring", build_flooring), ("LittleHouse", build_house), ("BonkedSign", build_sign), ("Garage", build_garage),
            ("Mailbox", build_mailbox), ("Fence", build_fence), ("Garden", build_garden), ("Tree", build_tree),
            ("DoghouseBench", build_doghouse), ("Fountain", build_fountain)]

for pid, fn in BUILDERS:
    if ONLY and pid not in ONLY:
        continue
    fn()

# ---------------------------------------------------------------- whole stage + cutaway
if not NOVIEW and not ONLY:
    dk.hide(ALL, False)
    dk.preview(ALL, "stage_LittleHouse.png", with_shiba=BP, azimuth=-150, elevation=33, size=(2000, 1200))
    dk.preview(ALL, "stage_LittleHouse_top.png", with_shiba=BP, azimuth=0, elevation=89, size=(2000, 1200), top=True)
    roofs = [o for o in ALL if o.name.endswith("_Roof") and o.name.startswith("LittleHouse")]
    house = [o for o in ALL if o.name.startswith("LittleHouse_") or o.name.startswith("Flooring_")]
    dk.hide([o for o in ALL if o not in house])
    dk.hide(roofs)
    dk.preview(house, "preview_LittleHouse_cutaway.png", with_shiba=BP, azimuth=-125, elevation=40)

print("STATS", STATS)
