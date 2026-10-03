"""Knight Castle decor models (theme KnightCastle): builds the 20 decor parts around the eleventh Shiba (Knight Shiba).

Run:  blender --background --factory-startup --python build_KnightCastle.py -- <outdir>   (use an absolute outdir)
Writes into <outdir> (default: out/KnightCastle next to this script):
  Decor_KnightCastle_<PartId>.fbx, preview_<PartId>.png per part, stage_KnightCastle.png (3/4 view + top view stacked),
  stage_KnightCastle_34.png and stage_KnightCastle_top.png (the two views separately).
Every model is built in the stage frame (see decorkit.py) and, before export, fitted to the union box of its blueprint pieces so that
the game's fitToPieces scale stays about 1. Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures,
no neon. Previews are rendered the way the player sees the stage: from the road (+z) with +x to the right.
Env: KC_ONLY=Part1,Part2 builds only those parts; KC_DBG=<folder> adds extra debug views of each part.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "KnightCastle"
R = random.Random(11)
pi = math.pi
DBG = os.environ.get("KC_DBG")
ONLY = set(os.environ.get("KC_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
STONE = (150, 152, 158); STONE_D = (104, 108, 116); STONE_L = (196, 198, 200); STONE_W = (176, 168, 152)
ROOF = (46, 84, 150); ROOF_L = (86, 128, 196); ROOF_D = (34, 62, 116)
RED = (176, 42, 46); RED_D = (126, 30, 34); RED_L = (212, 84, 80)
GOLD = (232, 182, 52); GOLD_D = (186, 138, 36); GOLD_L = (250, 218, 110)
WOOD = (122, 86, 56); WOOD_D = (80, 56, 40); WOOD_L = (164, 122, 80)
IRON = (60, 62, 70); IRON_L = (92, 96, 108); STEEL = (176, 184, 196); STEEL_D = (130, 138, 152)
CREAM = (232, 224, 200); WHITE = (240, 240, 244)
HAY = (214, 180, 80); HAY_D = (176, 142, 56)
GRASS = (92, 150, 66); GRASS_D = (72, 124, 56); GRASS_L = (124, 176, 84); HEDGE = (52, 112, 56); HEDGE_D = (38, 88, 46); HEDGE_L = (74, 138, 66)
WATER = (60, 128, 176); WATER_D = (44, 100, 152); WATER_L = (126, 194, 230); FOAM = (226, 238, 242)
SAND = (214, 196, 150); SAND_D = (190, 168, 120); DIRT = (166, 140, 104)
HORSE = (150, 104, 66); HORSE_D = (104, 70, 44); MANE = (50, 36, 30)

TIM = WOOD; TIM_D = WOOD_D; TIM_L = WOOD_L; TIM_X = WOOD_L
TURF = GRASS; TURF_D = GRASS_D; TURF_L = GRASS_L
FIRE = (240, 132, 42); FIRE_Y = (252, 204, 70); FIRE_R = (206, 70, 36)
BONE = CREAM; BONE_D = (206, 196, 170)
# ---- geometry helpers --------------------------------------------------------------------------------------------
def _obj(part, name, pts, faces, color, jitter=0.0, closed=True, up=False):
    """Mesh from absolute stage-frame points. closed: outward normals are recomputed; up: open faces made to face +y."""
    bm = bmesh.new()
    vs = [bm.verts.new((p[0], p[2], p[1])) for p in pts]
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    if closed:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if up:
        for f in bm.faces:
            if f.normal.z < 0:
                f.normal_flip()
    return dk._object(part, name, bm, Vector((0, 0, 0)), (0, 0, 0), color, jitter)


def recolor(o, fn, jitter=0.0):
    """fn(center_stage, normal_stage, face_index) -> colour or None (keep). World space of the object, stage axes."""
    me = o.data
    attr = me.color_attributes.get("Col")
    mw = o.matrix_world
    m3 = mw.to_3x3()
    for poly in me.polygons:
        c = mw @ poly.center
        n = m3 @ poly.normal
        col = fn((c.x, c.z, c.y), (n.x, n.z, n.y), poly.index)
        if col is None:
            continue
        f = 1.0 + (R.random() - 0.5) * 2 * jitter if jitter else 1.0
        lc = dk.srgb(*dk.shade(col, f))
        for li in poly.loop_indices:
            attr.data[li].color = (*lc, 1.0)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _m(axis, u, v, h, bx_, by, bz, dx, dz):
    if axis == 'y':
        return (bx_ + u + dx, by + h, bz + v + dz)
    if axis == 'z':
        return (bx_ + u + dx, by + v, bz + h + dz)
    return (bx_ + h + dz, by + u, bz + v + dx)          # 'x'


def lathe(part, base, profile, sides, color, jitter=0.0, axis="y", rot0=0.0, name="Lathe", cap0=True):
    """Solid of revolution. profile = [(radius, height[, dx, dz])] bottom to top (radius 0 = apex point), base = stage point.
    axis 'y' = standing, 'z' / 'x' = lying along that stage axis (height runs along it)."""
    pts, rings = [], []
    bx_, by, bz = base
    for e in profile:
        r, h = e[0], e[1]
        dx = e[2] if len(e) > 2 else 0.0
        dz = e[3] if len(e) > 3 else 0.0
        if r <= 1e-6:
            pts.append(_m(axis, 0, 0, h, bx_, by, bz, dx, dz))
            rings.append([len(pts) - 1])
        else:
            idx = []
            for i in range(sides):
                a = 2 * pi * i / sides + rot0
                pts.append(_m(axis, r * math.cos(a), r * math.sin(a), h, bx_, by, bz, dx, dz))
                idx.append(len(pts) - 1)
            rings.append(idx)
    faces = []
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(a) == 1:
                faces.append((a[0], b[j], b[i]))
            elif len(b) == 1:
                faces.append((a[i], a[j], b[0]))
            else:
                faces.append((a[i], a[j], b[j], b[i]))
    if cap0 and len(rings[0]) > 1:
        faces.append(tuple(rings[0]))
    if len(rings[-1]) > 1:
        faces.append(tuple(rings[-1]))
    return _obj(part, name, pts, faces, color, jitter)


def blob(part, c, r, color, sy=1.0, sides=6, jitter=0.0, name="Blob"):
    """Cheap low-poly ball (2 rings)."""
    return lathe(part, (c[0], c[1] - r * sy, c[2]), [(0, 0), (r * 0.9, r * sy * 0.55), (r, r * sy * 1.1), (r * 0.9, r * sy * 1.65),
                                                  (0, r * sy * 2)], sides, color, jitter, name=name)


def slab(part, pts2, thick, plane, at, color, jitter=0.0, name="Slab"):
    """Extruded polygon. plane 'xy' (pts = x, y; thickness along z centred on `at`), 'yz' (pts = y, z; thickness along x
    centred on `at`) or 'xz' (pts = x, z; from y=`at` up by `thick`)."""
    n = len(pts2)
    if plane == 'xz':
        w0, w1 = at, at + thick
    else:
        w0, w1 = at - thick / 2, at + thick / 2

    def P(u, v, w):
        return (u, v, w) if plane == 'xy' else ((u, w, v) if plane == 'xz' else (w, u, v))
    pts = [P(u, v, w0) for u, v in pts2] + [P(u, v, w1) for u, v in pts2]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _obj(part, name, pts, faces, color, jitter)


def flat(part, pts_xz, y, color, jitter=0.0, name="Flat"):
    """Single open polygon lying flat, facing up (decals; 1 face)."""
    pts = [(x, y, z) for x, z in pts_xz]
    return _obj(part, name, pts, [tuple(range(len(pts)))], color, jitter, closed=False, up=True)


def frustum(part, cx, cz, y0, y1, bsx, bsz, tsx, tsz, color, jitter=0.0, tx=0.0, tz=0.0, name="Frustum"):
    b = [(cx - bsx / 2, y0, cz - bsz / 2), (cx + bsx / 2, y0, cz - bsz / 2), (cx + bsx / 2, y0, cz + bsz / 2), (cx - bsx / 2, y0, cz + bsz / 2)]
    t = [(cx + tx - tsx / 2, y1, cz + tz - tsz / 2), (cx + tx + tsx / 2, y1, cz + tz - tsz / 2),
         (cx + tx + tsx / 2, y1, cz + tz + tsz / 2), (cx + tx - tsx / 2, y1, cz + tz + tsz / 2)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _obj(part, name, b + t, faces, color, jitter)


def loft(part, rings, color, jitter=0.0, caps=True, name="Loft"):
    """Rings of stage points (equal length, last may be a single point) joined by quads."""
    pts, idx = [], []
    for ring in rings:
        idx.append(list(range(len(pts), len(pts) + len(ring))))
        pts.extend(ring)
    n = len(rings[0])
    faces = []
    for a, b in zip(idx, idx[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[0]) if len(b) == 1 else (a[i], a[j], b[j], b[i]))
    if caps:
        faces.append(tuple(idx[0]))
        if len(idx[-1]) > 2:
            faces.append(tuple(idx[-1]))
    return _obj(part, name, pts, faces, color, jitter)


def post(part, x, z, y0, y1, r, color, sides=6, top_r=None, jitter=0.0, name="Post"):
    return dk.cyl(part, (x, (y0 + y1) / 2, z), r, y1 - y0, color, verts=sides, top_radius=top_r, jitter=jitter, name=name)


def bx(p, x0, x1, y0, y1, z0, z1, color, jitter=0.0, rot=(0, 0, 0), name="Box"):
    """Box by extents."""
    return dk.box(p, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), color, rot=rot, jitter=jitter, name=name)


def drop_faces(o, pred):
    """Deletes faces of o whose stage normal satisfies pred(n)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    mw = o.matrix_world.to_3x3()
    bad = []
    for f in bm.faces:
        n = mw @ f.normal
        if pred((n.x, n.z, n.y)):
            bad.append(f)
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='FACES')
        bm.to_mesh(o.data)
    bm.free()


def rock(p, c, r, color, scale=(1, 0.7, 1), rot=(0, 0, 0), jitter=0.12, name="Rock"):
    return dk.ball(p, c, r, color, scale=scale, subdiv=1, rot=rot, jitter=jitter, name=name)


def gable(p, axis, c0, c1, uc, half, y_eave, y_ridge, t, col_a, col_b, n=5, jitter=0.06, name="Roof"):
    """Roof of n courses per slope from the eave line (uc +- half, y_eave) up to the ridge (uc, y_ridge), thickness t downward.
    axis 'x': ridge runs along x from c0 to c1, slopes fall toward +-z. axis 'z': ridge along z, slopes fall toward +-x."""
    out = []
    for side in (-1, 1):
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            ua, ya = uc + side * half * (1 - t0), y_eave + (y_ridge - y_eave) * t0
            ub, yb = uc + side * half * (1 - t1), y_eave + (y_ridge - y_eave) * t1
            du, dy = ub - ua, yb - ya
            L = math.hypot(du, dy)
            pu, py = -dy / L * side * t, du / L * side * t       # downward normal * thickness
            poly_uy = [(ua, ya), (ub, yb), (ub + pu, yb + py), (ua + pu, ya + py)]
            col = col_a if i % 2 == 0 else col_b
            if axis == 'x':
                out.append(slab(p, [(y, u) for u, y in poly_uy], c1 - c0, 'yz', (c0 + c1) / 2, col, jitter, name=name))
            else:
                out.append(slab(p, poly_uy, c1 - c0, 'xy', (c0 + c1) / 2, col, jitter, name=name))
    return out


def gable_end(p, axis, c, uc, half, y0, y1, thick, color, jitter=0.05, name="Gable"):
    """Triangular wall filling a gable at ridge coordinate c."""
    if axis == 'x':
        return slab(p, [(y0, uc - half), (y0, uc + half), (y1, uc)], thick, 'yz', c, color, jitter, name=name)
    return slab(p, [(uc - half, y0), (uc + half, y0), (uc, y1)], thick, 'xy', c, color, jitter, name=name)


def turf_roof(p, axis, c0, c1, uc, half, y_eave, y_ridge, t, n=5, N=8, col_a=TURF_D, col_b=TURF_L, soil=(92, 70, 46), lump=0.22, name="Turf"):
    """Turf roof: per slope a lumpy grid of n courses x N sods (alternating greens) over a soil layer of thickness t.
    axis 'x': ridge along x from c0 to c1, slopes fall toward +-z. axis 'z': ridge along z, slopes fall toward +-x."""
    out = []
    for side in (-1, 1):
        rows = [(uc + side * half * (1 - r / n), y_eave + (y_ridge - y_eave) * r / n) for r in range(n + 1)]
        du, dy = rows[-1][0] - rows[0][0], rows[-1][1] - rows[0][1]
        L = math.hypot(du, dy)
        pu, py = -dy / L * side, du / L * side                 # unit normal pointing down into the roof, in (u, y)

        def P(u, y, c):
            x = c0 + (c1 - c0) * c / N
            return (x, y, u) if axis == 'x' else (u, y, x)
        pts, T, B = [], [], []
        for r, (u, y) in enumerate(rows):
            tr, br = [], []
            for c in range(N + 1):
                d = R.uniform(0, lump) if 0 < r < n and 0 < c < N else 0.0
                tr.append(len(pts)); pts.append(P(u - pu * d, y - py * d, c))
            for c in range(N + 1):
                br.append(len(pts)); pts.append(P(u + pu * t, y + py * t, c))
            T.append(tr); B.append(br)
        faces = [(T[r][c], T[r][c + 1], T[r + 1][c + 1], T[r + 1][c]) for r in range(n) for c in range(N)]
        faces.append((B[0][0], B[0][N], B[n][N], B[n][0]))
        faces.append((T[0][0], T[0][N], B[0][N], B[0][0]))
        faces.append((T[n][0], T[n][N], B[n][N], B[n][0]))
        faces.append(tuple([T[r][0] for r in range(n + 1)] + [B[r][0] for r in range(n, -1, -1)]))
        faces.append(tuple([T[r][N] for r in range(n + 1)] + [B[r][N] for r in range(n, -1, -1)]))
        o = _obj(p, name, pts, faces, soil, 0.04)

        def col(c_, n_, i, n=n, N=N):
            if i < n * N:
                return mix(col_b, col_a, (((i * 37 + side * 11) % 17) / 16.0))
            return None
        recolor(o, col, 0.07)
        out.append(o)
    return out


def logwall(p, axis, c0, c1, u, y0, y1, thick, courses, col_a, col_b, bulge=0.2, jitter=0.07, name="Logs"):
    """Wall of stacked logs. axis 'x': runs along x at z=u (thickness along z); axis 'z': runs along z at x=u."""
    h = (y1 - y0) / courses
    out = []
    for i in range(courses):
        t = thick + (bulge if i % 2 else 0.0)
        col = col_a if i % 2 == 0 else col_b
        ya, yb = y0 + i * h + 0.03, y0 + (i + 1) * h - 0.03
        if axis == 'x':
            out.append(bx(p, c0, c1, ya, yb, u - t / 2, u + t / 2, col, jitter, name=name))
        else:
            out.append(bx(p, u - t / 2, u + t / 2, ya, yb, c0, c1, col, jitter, name=name))
    return out


def shield(p, x, y, z, r, c_face, c_rim, axis='z', sides=6, thick=0.4, boss=None):
    """Round shield facing +z (axis 'z') or +-x (axis 'x'): face colour on both caps, rim colour on the side."""
    o = dk.cyl(p, (x, y, z), r, thick, c_rim, axis=axis, verts=sides, jitter=0.05, name="Shield")
    ax = 2 if axis == 'z' else 0
    recolor(o, lambda c, n, i: c_face if abs(n[ax]) > 0.9 else None, 0.04)
    if boss:
        if axis == 'z':
            dk.cyl(p, (x, y, z + thick / 2 + 0.05), r * 0.3, 0.2, boss, axis='z', verts=5, name="Boss")
        else:
            sgn = 1 if x >= 0 else -1
            dk.cyl(p, (x, y, z), r * 0.3, thick + 0.25, boss, axis='x', verts=5, name="Boss")
    return o


def barrel(p, x, y0, z, r, h, color=TIM, hoop=IRON, sides=6, name="Barrel"):
    prof = [(0.8 * r, 0), (0.95 * r, 0.18 * h), (0.98 * r, 0.30 * h), (r, 0.5 * h), (0.98 * r, 0.70 * h), (0.95 * r, 0.82 * h), (0.8 * r, h)]
    o = lathe(p, (x, y0, z), prof, sides, color, 0.06, name=name)
    recolor(o, lambda c, n, i: hoop if (abs(n[1]) < 0.9 and (c[1] - y0 < 0.3 * h and c[1] - y0 > 0.18 * h or c[1] - y0 > 0.7 * h and c[1] - y0 < 0.82 * h)) else None, 0.03)
    return o


def fire(p, x, y0, z, r, h, name="Flame"):
    """Plain coloured fire: a cluster of flame tongues (no glow)."""
    tongues = [(0.0, 0.0, 1.0, 0.85, FIRE_R), (0.6, 0.15, 0.7, 0.55, FIRE), (-0.55, -0.3, 0.78, 0.6, FIRE), (0.1, -0.65, 0.62, 0.5, FIRE_R),
               (-0.25, 0.55, 0.55, 0.5, FIRE_R)]
    for dx, dz, hh, rr, col in tongues:
        dk.cone(p, (x + dx * r * 0.8, y0, z + dz * r * 0.8), r * rr, h * hh, col, verts=5, jitter=0.05, name=name)
    dk.cone(p, (x, y0, z), r * 0.5, h * 0.66, FIRE_Y, verts=5, jitter=0.04, name=name)
    dk.cone(p, (x + 0.1 * r, y0, z - 0.15 * r), r * 0.28, h * 0.42, (255, 238, 160), verts=4, name=name)


def plank_row(p, x0, x1, z0, z1, y0, y1, n, axis, color, gap=0.1, jitter=0.08, name="Plank"):
    out = []
    for i in range(n):
        if axis == 'x':
            w = (z1 - z0) / n
            out.append(bx(p, x0, x1, y0, y1, z0 + w * i + gap / 2, z0 + w * (i + 1) - gap / 2, color, jitter, name=name))
        else:
            w = (x1 - x0) / n
            out.append(bx(p, x0 + w * i + gap / 2, x0 + w * (i + 1) - gap / 2, y0, y1, z0, z1, color, jitter, name=name))
    return out


def stake(p, x, z, y0, y1, w, d, color, tip=0.9, jitter=0.07, name="Stake"):
    """Vertical plank with a pointed top (faces the road)."""
    return slab(p, [(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y1), (x, y1 + tip), (x - w / 2, y1)], d, 'xy', z, color, jitter, name=name)


def dragon_head(p, x, y, z, s, dirx, color, jaw=None):
    """A little carved dragon head on a gable: snout points toward dirx (+1 / -1 along x), s = overall size."""
    d = dirx
    bx(p, x - d * 0.1 * s, x + d * 1.0 * s, y - 0.25 * s, y + 0.3 * s, z - 0.3 * s, z + 0.3 * s, color, 0.05, name="Head")
    bx(p, x + d * 0.8 * s, x + d * 1.5 * s, y - 0.1 * s, y + 0.2 * s, z - 0.22 * s, z + 0.22 * s, color, 0.05, name="Snout")
    bx(p, x + d * 0.3 * s, x + d * 1.2 * s, y - 0.55 * s, y - 0.2 * s, z - 0.2 * s, z + 0.2 * s, GOLD_D, 0.05, name="Jaw")
    for sz in (-1, 1):
        dk.box(p, (x + d * 0.35 * s, y + 0.2 * s, z + sz * 0.38 * s), (0.2 * s, 0.34 * s, 0.14 * s), RED_D, name="Eye")
        dk.box(p, (x - d * 0.2 * s, y + 0.5 * s, z + sz * 0.2 * s), (0.2 * s, 0.7 * s, 0.16 * s), color, rot=(0, 0, -d * 25), name="Horn")


def rod(p, A, B, r, color, sides=5, r2=None, jitter=0.0, name="Rod"):
    """Cylinder (or cone frustum when r2 is given) between two stage points; round ends are capped."""
    a = Vector((A[0], A[2], A[1]))
    b = Vector((B[0], B[2], B[1]))
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides, radius1=r, radius2=r if r2 is None else r2, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    return dk._object(p, name, bm, (a + b) / 2, (0, 0, 0), color, jitter)


def tri_prism(p, pts_xy_or_yz, thick, plane, at, color, jitter=0.0, name="Tri"):
    return slab(p, pts_xy_or_yz, thick, plane, at, color, jitter, name=name)


# ---- fitting, bounds, validation ---------------------------------------------------------------------------------
def roblox_box(pieces):
    """Union of the pieces' size boxes (rotated, axis aligned) in the stage frame."""
    lo = [1e9] * 3
    hi = [-1e9] * 3

    def rotm(rx, ry, rz):
        rx, ry, rz = map(math.radians, (rx, ry, rz))
        X = Matrix.Rotation(rx, 3, 'X'); Y = Matrix.Rotation(ry, 3, 'Y'); Z = Matrix.Rotation(rz, 3, 'Z')
        return X @ Y @ Z
    for pc in pieces:
        M = rotm(*(pc.get("Rotation") or (0, 0, 0)))
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
    print("FIT %-11s scale x%.3f y%.3f z%.3f   built x[%.1f %.1f] y[%.1f %.1f] z[%.1f %.1f]" % (
        part.id, sc[0], sc[1], sc[2], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    return sc


def drop_ground_faces(part, y_max=0.02):
    """Removes down-facing faces lying on the ground plane (never visible)."""
    for o in part.objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bad = [f for f in bm.faces if f.normal.z < -0.99 and f.calc_center_median().z < y_max]
        if bad:
            bmesh.ops.delete(bm, geom=bad, context='FACES')
            bm.to_mesh(o.data)
        bm.free()


def noise(x, z):
    return (math.sin(x * 0.11 + 1.3) * math.cos(z * 0.13 + 0.7) + math.sin(x * 0.047 - z * 0.061 + 2.0)
            + 0.5 * math.sin(x * 0.27 + z * 0.31)) / 2.5




# ---- the parts ---------------------------------------------------------------------------------------------------
BUILDERS = []


def part_builder(pid):
    def deco(fn):
        BUILDERS.append((pid, fn))
        return fn
    return deco


FOOT = {}          # part id -> (lo, hi) footprint of the blueprint pieces (filled in main, used to scatter details in Ground)


def gouraud(o, fn):
    """Smooth colour field: every corner gets fn(x, z) (stage coordinates), the faces blend between their corners."""
    me = o.data
    attr = me.color_attributes.get("Col")
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            w = mw @ me.vertices[me.loops[li].vertex_index].co
            attr.data[li].color = (*dk.srgb(*fn(w.x, w.y)), 1.0)



# ---- castle helpers ----------------------------------------------------------------------------------------------
def stoneblock(p, x0, x1, y0, y1, z0, z1, courses=4, ca=STONE, cb=STONE_L, jitter=0.06, e=0.14, name="Stone"):
    """Wall block of stacked courses: alternate tones, every second course sticks out a little."""
    h = (y1 - y0) / courses
    out = []
    for i in range(courses):
        d = e if i % 2 else 0.0
        out.append(bx(p, x0 - d, x1 + d, y0 + i * h + 0.02, y0 + (i + 1) * h - 0.02, z0 - d, z1 + d, ca if i % 2 == 0 else cb, jitter, name=name))
    return out


def merlon_line(p, axis, c0, c1, u, y, step=2.4, w=1.2, h=1.3, d=1.0, color=STONE_L, jitter=0.05):
    """Row of battlement teeth along x (axis 'x', at z=u) or along z (axis 'z', at x=u), standing on height y."""
    n = max(1, int(round((c1 - c0) / step)))
    for k in range(n):
        c = c0 + (k + 0.5) * (c1 - c0) / n
        if axis == 'x':
            bx(p, c - w / 2, c + w / 2, y, y + h, u - d / 2, u + d / 2, color, jitter, name="Merlon")
        else:
            bx(p, u - d / 2, u + d / 2, y, y + h, c - w / 2, c + w / 2, color, jitter, name="Merlon")


def merlon_rect(p, x0, x1, z0, z1, y, sides="NSEW", **kw):
    """Battlement teeth on a rectangle's edges. N = back (z0), S = front (z1), W = x0, E = x1."""
    if "N" in sides:
        merlon_line(p, 'x', x0, x1, z0, y, **kw)
    if "S" in sides:
        merlon_line(p, 'x', x0, x1, z1, y, **kw)
    if "W" in sides:
        merlon_line(p, 'z', z0, z1, x0, y, **kw)
    if "E" in sides:
        merlon_line(p, 'z', z0, z1, x1, y, **kw)


def ring_merlons(p, cx, cz, y, r, n=8, color=STONE_L, w=1.3, h=1.3, d=0.9, jitter=0.05):
    for k in range(n):
        a = 2 * pi * k / n
        dk.box(p, (cx + r * math.cos(a), y + h / 2, cz + r * math.sin(a)), (w, h, d), color,
               rot=(0, -(math.degrees(a) + 90), 0), jitter=jitter, name="Merlon")


def cone_roof(p, cx, cz, y0, r, h, c1=ROOF, c2=ROOF_L, sides=8, name="Roof"):
    """Pointed roof with alternating colour sectors."""
    o = dk.cone(p, (cx, y0, cz), r, h, c1, verts=sides, jitter=0.04, name=name)
    if c2:
        def fn(c, n, i):
            if n[1] < -0.5:
                return None
            a = math.atan2(c[2] - cz, c[0] - cx)
            k = int((a % (2 * pi)) / (2 * pi / sides))
            return c2 if k % 2 else None
        recolor(o, fn, 0.04)
    return o


def round_tower(p, cx, cz, y0, y1, r, ca=STONE, cb=STONE_D, sides=10, flare=0.4, bands=(), name="Tower"):
    """Round stone tower with a little foot flare and dark bands at the heights in `bands` (centre heights, 0.5 thick)."""
    prof = [(r + flare, y0), (r + flare, y0 + 0.9), (r, y0 + 1.5), (r, y1)]
    o = lathe(p, (cx, 0, cz), prof, sides, ca, 0.06, name=name)
    for yb in bands:
        dk.cyl(p, (cx, yb, cz), r + 0.22, 0.5, cb, verts=sides, jitter=0.04, name="Band")
    return o


def slit(p, x, y, z, face, w=0.5, h=2.0, color=IRON, depth=0.3):
    """Dark arrow slit / window box sitting on a wall face ('+z', '-z', '+x', '-x') at the surface point (x, y, z)."""
    if face in ('+z', '-z'):
        dk.box(p, (x, y, z), (w, h, depth), color, name="Slit")
    else:
        dk.box(p, (x, y, z), (depth, h, w), color, name="Slit")


def arch_fill(p, cx, y0, spring, hw, z, thick, color, segs=6, jitter=0.03, name="Arch"):
    """Filled round-headed shape in the xy plane at depth z: rectangle up to `spring`, half circle above (door, window)."""
    pts = [(cx - hw, y0), (cx + hw, y0), (cx + hw, spring)]
    for k in range(1, segs):
        a = pi * k / segs
        pts.append((cx + hw * math.cos(a), spring + hw * math.sin(a)))
    pts.append((cx - hw, spring))
    return slab(p, pts, thick, 'xy', z, color, jitter, name=name)


def arch_wall(p, x0, x1, yb, ytop, cx, hw, spring, z, thick, color, segs=7, jitter=0.05, name="ArchWall"):
    """Wall slab (xy plane at depth z) with an arched opening cut out of its lower middle."""
    pts = [(x0, ytop), (x1, ytop), (x1, yb), (cx + hw, yb), (cx + hw, spring)]
    for k in range(1, segs):
        a = pi * k / segs
        pts.append((cx + hw * math.cos(a), spring + hw * math.sin(a)))
    pts += [(cx - hw, spring), (cx - hw, yb), (x0, yb)]
    return slab(p, pts, thick, 'xy', z, color, jitter, name=name)


def pennant(p, x, y, z, L, h, color, d=1, thick=0.16, name="Flag"):
    """Swallow-tail flag in the xy plane, hoist at x, flying toward +x (d=1) or -x (d=-1)."""
    pts = [(x, y + h / 2), (x + d * L, y + h / 2), (x + d * L * 0.78, y), (x + d * L, y - h / 2), (x, y - h / 2)]
    if d < 0:
        pts = pts[::-1]
    return slab(p, pts, thick, 'xy', z, color, 0.03, name=name)


def heater(p, x, y, z, w, h, color, emblem=GOLD, thick=0.3, name="Shield"):
    """Heater shield facing +z, centre (x, y), with a small emblem in the middle."""
    pts = [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2, y), (x + w * 0.28, y - h * 0.33), (x, y - h / 2),
           (x - w * 0.28, y - h * 0.33), (x - w / 2, y)]
    slab(p, pts, thick, 'xy', z, color, 0.03, name=name)
    if emblem:
        slab(p, [(x, y + h * 0.3), (x + w * 0.2, y), (x, y - h * 0.3), (x - w * 0.2, y)], thick + 0.1, 'xy', z, emblem, 0.02, name="Emblem")


def banner_cloth(p, x, ytop, z, w, h, color, emblem=GOLD, name="Banner", thick=0.2):
    """Hanging banner (xy plane at depth z) with a V cut at the bottom and a diamond emblem."""
    pts = [(x - w / 2, ytop), (x + w / 2, ytop), (x + w / 2, ytop - h), (x, ytop - h * 0.82), (x - w / 2, ytop - h)]
    slab(p, pts, thick, 'xy', z, color, 0.04, name=name)
    if emblem:
        cy = ytop - h * 0.42
        slab(p, [(x, cy + w * 0.34), (x + w * 0.26, cy), (x, cy - w * 0.34), (x - w * 0.26, cy)], thick + 0.12, 'xy', z, emblem, 0.02, name="Emblem")


def beam(p, A, B, w, color, w2=None, jitter=0.0, name="Beam"):
    """Square-section beam between two stage points."""
    a = Vector((A[0], A[2], A[1]))
    b = Vector((B[0], B[2], B[1]))
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, w2 or w, d.length), verts=bm.verts)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    return dk._object(p, name, bm, (a + b) / 2, (0, 0, 0), color, jitter)


def hay_bale(p, cx, cz, sx=2.4, sy=1.8, sz=1.8, rot=0.0, y0=0.0):
    """Hay bale with two darker straps."""
    dk.box(p, (cx, y0 + sy / 2, cz), (sx, sy, sz), HAY, rot=(0, rot, 0), jitter=0.08, name="Hay")
    for s in (-0.28, 0.28):
        a = math.radians(rot)
        dx, dz = s * sx * math.cos(a), -s * sx * math.sin(a)
        dk.box(p, (cx + dx, y0 + sy / 2, cz + dz), (0.2, sy + 0.1, sz + 0.1), HAY_D, rot=(0, rot, 0), name="Strap")


def crate(p, x, y0, z, s=1.6, color=WOOD, rot=0.0):
    dk.box(p, (x, y0 + s / 2, z), (s, s, s), color, rot=(0, rot, 0), jitter=0.08, name="Crate")
    dk.box(p, (x, y0 + s / 2, z), (s + 0.12, 0.25, s + 0.12), WOOD_D, rot=(0, rot, 0), name="Slat")


def horse(p, x, y0, z, s=1.0, yaw=0.0, color=HORSE, mane=MANE, cloth=None, cloth2=GOLD, head_down=False):
    """Low-poly horse, facing +x in its own frame, turned by yaw degrees about y (counter clockwise seen from above)."""
    a = math.radians(yaw)
    ca, sa = math.cos(a), math.sin(a)

    def L(lx, ly, lz):
        return (x + (lx * ca + lz * sa) * s, y0 + ly * s, z + (-lx * sa + lz * ca) * s)

    def hb(lx, ly, lz, sx, sy, sz, col, tilt=0.0, name="Horse"):
        dk.box(p, L(lx, ly, lz), (sx * s, sy * s, sz * s), col, rot=(0, yaw, tilt), jitter=0.05, name=name)
    hb(0, 2.9, 0, 4.4, 1.9, 1.7, color)
    hb(1.9, 2.95, 0, 0.9, 1.7, 1.55, color)
    for lx, lz in ((1.6, 0.55), (1.6, -0.55), (-1.6, 0.55), (-1.6, -0.55)):
        hb(lx, 1.0, lz, 0.55, 2.0, 0.55, color)
        hb(lx, 0.15, lz, 0.62, 0.35, 0.62, IRON_L, name="Hoof")
    hb(2.55, 4.3, 0, 1.0, 2.5, 0.95, color, tilt=-28)
    hb(2.2, 4.7, 0, 0.5, 2.5, 0.3, mane, tilt=-28, name="Mane")
    hb(3.35, 5.45, 0, 1.7, 0.95, 0.8, color, tilt=-10)
    hb(4.1, 5.2, 0, 0.5, 0.65, 0.7, HORSE_D, tilt=-10, name="Muzzle")
    hb(3.0, 6.1, 0.28, 0.3, 0.6, 0.22, color, name="Ear")
    hb(3.0, 6.1, -0.28, 0.3, 0.6, 0.22, color, name="Ear")
    hb(-2.5, 3.0, 0, 0.5, 2.3, 0.6, mane, tilt=12, name="Tail")
    if cloth:
        hb(0, 3.35, 0, 3.0, 1.45, 1.95, cloth, name="Cloth")
        hb(0, 3.0, 0, 3.05, 0.3, 1.98, cloth2, name="ClothTrim")


def bench(p, cx, cz, length, y0=0.0, axis='x', color=WOOD, h=1.4):
    if axis == 'x':
        bx(p, cx - length / 2, cx + length / 2, y0 + h - 0.3, y0 + h, cz - 0.55, cz + 0.55, color, 0.06, name="Seat")
        for sx in (-1, 1):
            bx(p, cx + sx * (length / 2 - 0.4) - 0.2, cx + sx * (length / 2 - 0.4) + 0.2, y0, y0 + h - 0.3, cz - 0.45, cz + 0.45, WOOD_D, 0.04, name="Leg")
    else:
        bx(p, cx - 0.55, cx + 0.55, y0 + h - 0.3, y0 + h, cz - length / 2, cz + length / 2, color, 0.06, name="Seat")
        for sz in (-1, 1):
            bx(p, cx - 0.45, cx + 0.45, y0, y0 + h - 0.3, cz + sz * (length / 2 - 0.4) - 0.2, cz + sz * (length / 2 - 0.4) + 0.2, WOOD_D, 0.04, name="Leg")


def bush(p, cx, y0, cz, r, color=HEDGE, sy=0.85, sides=6, jitter=0.1):
    return blob(p, (cx, y0 + r * sy, cz), r, color, sy=sy, sides=sides, jitter=jitter, name="Bush")


def ellipse_pts(cx, cz, rx, rz, k=10, a0=0.0, wob=0.0):
    return [(cx + rx * (1 + wob * (R.random() - 0.5)) * math.cos(a0 + 2 * pi * i / k), cz + rz * (1 + wob * (R.random() - 0.5)) * math.sin(a0 + 2 * pi * i / k)) for i in range(k)]


def box_pole(p, x, z, y0, y1, w, color, jitter=0.05, name="Pole"):
    return bx(p, x - w / 2, x + w / 2, y0, y1, z - w / 2, z + w / 2, color, jitter, name=name)


PATH = [(0, 65), (50, 50), (-4, 36), (-40, 30), (-14, 8), (40, -12), (60, -40), (24, -50), (0, -65)]


def path_dist(x, z):
    best = 1e9
    for (ax, az), (bx_, bz) in zip(PATH, PATH[1:]):
        dx, dz = bx_ - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - (ax + t * dx), z - (az + t * dz)))
    return best


@part_builder("Ground")
def build_Ground():
    p = dk.Part("Ground")
    dk.box(p, (0, 0.1, 0), (190, 0.2, 130), GRASS_D, name="Base")
    nx, nz, cs = 19, 13, 10.0
    pts = [(-95 + i * cs, 0.3, -65 + j * cs) for j in range(nz + 1) for i in range(nx + 1)]
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, j * (nx + 1) + i + nx + 2, j * (nx + 1) + i + nx + 1)
             for j in range(nz) for i in range(nx)]
    g = _obj(p, "Grass", pts, faces, GRASS, closed=False, up=True)
    gouraud(g, lambda x, z: mix(GRASS_D, GRASS_L, max(0.0, min(1.0, 0.5 + 0.95 * noise(x, z) + 0.15 * math.sin(x * 0.9 + z * 0.7)))))

    def blotch(cx, cz, rx, rz, color, y, k=9, name="Patch"):
        return flat(p, ellipse_pts(cx, cz, rx, rz, k, R.uniform(0, 2 * pi), 0.5), y, color, 0.05, name=name)

    def rect(x0, x1, z0, z1, y, color, name="Flat", jit=0.04):
        return flat(p, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y, color, jit, name=name)

    # earth patches under the busy places
    for (cx, cz, rx, rz) in ((-6, -33, 13, 8), (-20, 54, 11, 8), (-48, 54, 12, 8), (-80, 56, 13, 8), (78, 48, 11, 9), (78, -6, 15, 8),
                             (80, -28, 14, 9), (80, -54, 12, 9), (44, 24, 11, 11), (-12, -48, 10, 9), (24, -30, 11, 8), (76, 24, 17, 9)):
        blotch(cx, cz, rx * 0.72, rz * 0.7, mix(GRASS_D, DIRT, 0.7), 0.325)
    n = 0
    while n < 8:                                          # lighter and darker grass patches
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        if -92 < x < -28 and -66 < z < -16:
            continue
        blotch(x, z, R.uniform(4, 9), R.uniform(3, 7), (112, 160, 78) if n % 2 else (84, 138, 64), 0.315)
        n += 1

    # the moat: sandy bank, foam, water, little waves and lily pads
    rect(-90, -30, -65, -17, 0.33, SAND_D, "Bank")
    for (x0, x1, z0, z1) in ((-87, -33, -64, -58), (-87, -33, -26, -20), (-87, -81, -58, -26), (-39, -33, -58, -26)):
        rect(x0, x1, z0, z1, 0.37, WATER, "Water", 0.03)
    rect(-87, -33, -64, -63, 0.4, FOAM, "Foam", 0.02)
    rect(-87, -33, -21, -20, 0.4, FOAM, "Foam", 0.02)
    rect(-87, -86, -64, -20, 0.4, FOAM, "Foam", 0.02)
    rect(-34, -33, -64, -20, 0.4, FOAM, "Foam", 0.02)
    for k in range(10):
        wx, wz = R.uniform(-84, -36), R.choice((-61, -23))
        rect(wx - 1.6, wx + 1.6, wz - 0.2, wz + 0.2, 0.41, WATER_L, "Wave", 0.03)
    for wx, wz in ((-84, -34), (-36, -50), (-84, -48), (-36, -30)):
        rect(wx - 0.5, wx + 0.5, wz - 1.4, wz + 1.4, 0.41, WATER_L, "Wave", 0.03)
    for (lx, lz) in ((-46, -61), (-70, -23.5), (-84, -52), (-36, -36)):
        flat(p, ellipse_pts(lx, lz, 0.9, 0.9, 7, 0.4), 0.42, (70, 140, 64), 0.05, name="Lily")
    # the flagstone island: dark foot, light flags, a red carpet from the gate to the keep
    bx(p, -81, -39, 0, 0.58, -58, -26, STONE_D, 0.06, name="Island")
    for i in range(7):
        for j in range(5):
            x0, z0 = -81 + i * 6, -58 + j * 6.4
            rect(x0 + 0.1, x0 + 5.9, z0 + 0.1, z0 + 6.3, 0.6, STONE_L if (i + j) % 2 else (176, 178, 182), "Flag", 0.04)
    rect(-62.2, -57.8, -34, -26, 0.62, RED, "Carpet", 0.03)
    rect(-62.8, -62.2, -34, -26, 0.63, GOLD, "CarpetTrim", 0.02)
    rect(-57.8, -57.2, -34, -26, 0.63, GOLD, "CarpetTrim", 0.02)

    # the sand yard before the gate with the knight's checker ring around the Shiba
    flat(p, ellipse_pts(-60, 24, 21, 11.5, 12, 0.3, 0.1), 0.335, SAND_D, 0.04, name="YardEdge")
    flat(p, ellipse_pts(-60, 24, 19.6, 10.4, 12, 0.3, 0.1), 0.345, SAND, 0.04, name="Yard")
    sx, sz = -60, 22
    for k in range(16):
        a0, a1 = 2 * pi * k / 16, 2 * pi * (k + 1) / 16
        flat(p, [(sx + 6.3 * math.cos(a0), sz + 6.3 * math.sin(a0)), (sx + 7.8 * math.cos(a0), sz + 7.8 * math.sin(a0)),
                 (sx + 7.8 * math.cos(a1), sz + 7.8 * math.sin(a1)), (sx + 6.3 * math.cos(a1), sz + 6.3 * math.sin(a1))], 0.37,
             ROOF if k % 2 else WHITE, 0.04, name="CheckRing")
    # a causeway of paving stones from the gate to the drawbridge
    for j in range(7):
        for i in range(4):
            x0, z0 = -64 + i * 2.0, -16.4 + j * 2.0
            rect(x0 + 0.07, x0 + 1.93, z0 + 0.07, z0 + 1.93, 0.35, STONE_L if (i + j) % 2 else (172, 174, 178), "Paver", 0.05)

    def free(x, z, m=2.5):
        if path_dist(x, z) < 6 or (-92 < x < -28 and -66 < z < -16):
            return False
        if -84 < x < -36 and 10 < z < 38:
            return False
        for (lo, hi) in FOOT.values():
            if lo[0] - m < x < hi[0] + m and lo[2] - m < z < hi[2] + m:
                return False
        return abs(x) < 93 and abs(z) < 63
    n = 0
    while n < 5:
        x, z = R.uniform(-93, 93), R.uniform(-63, 63)
        if free(x, z):
            dk.cone(p, (x, 0.3, z), R.uniform(0.45, 0.7), R.uniform(0.2, 0.3), mix(GRASS_D, GRASS_L, R.random()), verts=5, jitter=0.08, name="Tuft")
            n += 1
    n = 0
    while n < 14:                                         # flower clumps
        cx, cz = R.uniform(-90, 90), R.uniform(-60, 60)
        if not free(cx, cz, 4):
            continue
        col = [(250, 214, 70), (245, 245, 240), (236, 110, 150), (110, 150, 235)][R.randrange(4)]
        for k in range(4):
            fx, fz = cx + R.uniform(-2.2, 2.2), cz + R.uniform(-2.2, 2.2)
            if free(fx, fz, 1):
                rect(fx - 0.45, fx + 0.45, fz - 0.45, fz + 0.45, 0.35, col, "Flower", 0.05)
        n += 1
    for k in range(6):
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        if free(x, z, 3):
            rock(p, (x, 0.3, z), R.uniform(0.6, 0.95), STONE, scale=(1, 0.35, 1), rot=(0, R.uniform(0, 90), 0), name="Boulder")
    return p


@part_builder("Gatehouse")
def build_Gatehouse():
    p = dk.Part("Gatehouse")
    TOP = 8.8
    for (x0, x1) in ((-86, -74), (-46, -34)):
        stoneblock(p, x0, x1, 0, TOP, 1, 9, courses=5, ca=STONE, cb=STONE_W)
        merlon_rect(p, x0, x1, 1.5, 8.5, TOP, "NSW" if x0 < -60 else "NSE", step=2.7, w=1.4, h=1.2, d=1.0)
        bx(p, x0 + 1, x1 - 1, TOP - 0.2, TOP, 1.2, 8.8, STONE_D, 0.04, name="WallWalk")
        for sxp in (0.25, 0.75):
            slit(p, x0 + (x1 - x0) * sxp, 5, 9.2, '+z', 0.55, 2.4)
    for cx in (-69, -51):
        round_tower(p, cx, 5, 0, 20, 5.0, bands=(7.2, 14.4))
        dk.cyl(p, (cx, 21, 5), 5.7, 2.0, STONE_D, verts=10, jitter=0.05, name="Corbel")
        cone_roof(p, cx, 5, 22, 6.0, 7.0, ROOF, ROOF_L, sides=10)
        dk.cyl(p, (cx, 32.5, 5), 0.3, 7.0, WOOD_D, verts=5, name="FlagPole")
        dk.ball(p, (cx, 36.1, 5), 0.5, GOLD, subdiv=1, name="Knob")
        pennant(p, cx + 0.15, 34.4, 5, 3.6, 2.2, RED if cx < -60 else ROOF_L, 1)
        for yy in (11.0, 16.0):
            slit(p, cx, yy, 10.1, '+z', 0.7, 1.9)
    # front wall between the towers with the pointed gate arch, portcullis, coat of arms and banners
    arch_wall(p, -69, -51, 0, 19.2, -60, 3.6, 8.5, 9.7, 1.4, STONE)
    arch_wall(p, -69, -51, 0, 19.2, -60, 3.6, 8.5, -1.6, 1.4, STONE)
    for k in range(7):
        xx = -62.4 + k * 1.2
        yt = 8.5 + math.sqrt(max(0.0, 3.6 ** 2 - (xx + 60) ** 2)) - 0.15
        bx(p, xx - 0.14, xx + 0.14, 6.6, yt, 9.0, 9.35, IRON, 0.03, name="Bar")
    bx(p, -63.5, -56.5, 8.4, 8.8, 8.95, 9.4, IRON, 0.03, name="Rail")
    bx(p, -63.2, -56.8, 11.2, 11.6, 8.95, 9.4, IRON, 0.03, name="Rail")
    bx(p, -64, -56, 12.2, 13.0, -2, 10, STONE_D, 0.04, name="Vault")
    bx(p, -66, -54, 19.2, 20.4, -3.5, 13.5, STONE_D, 0.05, name="Platform")
    merlon_rect(p, -66, -54, -3.1, 13.1, 20.4, step=2.4, w=1.3, h=1.3, d=1.0)
    for k in range(5):
        xx = -65 + k * 2.5
        bx(p, xx - 0.6, xx + 0.6, 17.4, 19.2, 10.4, 13.5, STONE_L, 0.05, name="Corbel")
    heater(p, -60, 15.2, 10.55, 4.2, 5.0, RED, GOLD)
    for xx in (-66.2, -53.8):
        banner_cloth(p, xx, 17.6, 10.6, 2.6, 6.6, ROOF, GOLD)
    return p


@part_builder("Banners")
def build_Banners():
    p = dk.Part("Banners")
    for (x, z, col, emb) in ((-78, 35, RED, GOLD), (-72, 42, ROOF, GOLD_L), (-52, 46, ROOF, GOLD_L), (-47, 42, RED, GOLD)):
        bx(p, x - 0.9, x + 0.9, 0, 0.7, z - 0.9, z + 0.9, STONE_D, 0.05, name="Foot")
        dk.cyl(p, (x, 7.1, z), 0.34, 14.2, WOOD_D, verts=6, jitter=0.04, name="Pole")
        bx(p, x - 2.4, x + 2.4, 13.4, 14.0, z - 0.2, z + 0.2, WOOD, 0.04, name="Cross")
        for sg in (-1, 1):
            dk.ball(p, (x + sg * 2.5, 13.7, z), 0.3, GOLD, subdiv=1, name="Knob")
        banner_cloth(p, x, 13.4, z + 0.35, 3.8, 6.4, col, emb)
        dk.cone(p, (x, 14.2, z), 0.5, 0.8, GOLD, verts=5, name="Tip")
        for sg in (-1, 1):
            dk.cone(p, (x + sg * 1.5, 7.2, z + 0.4), 0.18, 0.7, GOLD, verts=4, name="Tassel")
    return p


@part_builder("Drawbridge")
def build_Drawbridge():
    p = dk.Part("Drawbridge")
    plank_row(p, -65, -55, -28, -16, 0.05, 0.55, 8, 'z', WOOD, gap=0.08, jitter=0.1)
    for zz in (-27, -22, -17):
        bx(p, -65.3, -54.7, 0.5, 0.75, zz - 0.45, zz + 0.45, WOOD_D, 0.05, name="Beam")
    for sx in (-1, 1):
        xr = -60 + sx * 5.0
        bx(p, xr - 0.2, xr + 0.2, 0.55, 1.5, -28, -16, WOOD_D, 0.05, name="Rail")
        for zz in (-27.6, -24, -20, -16.4):
            bx(p, xr - 0.3, xr + 0.3, 0.55, 1.9, zz - 0.3, zz + 0.3, WOOD_D, 0.05, name="RailPost")
    for xp in (-66.4, -53.6):
        bx(p, xp - 1.4, xp + 1.4, 0, 0.9, -15.9, -13.1, STONE_D, 0.05, name="PostFoot")
        dk.cyl(p, (xp, 5.4, -14.5), 0.8, 9.0, WOOD_D, verts=8, jitter=0.05, name="Post")
        dk.ball(p, (xp, 10.6, -14.5), 1.0, GOLD, subdiv=1, name="Cap")
        dk.cyl(p, (xp, 8.0, -14.5), 1.0, 0.5, IRON, verts=8, name="Strap")
        dk.cyl(p, (xp, 3.0, -14.5), 1.0, 0.5, IRON, verts=8, name="Strap")
        sgn = -1 if xp < -60 else 1
        rod(p, (xp + sgn * 0.0, 9.6, -15.2), (xp + 1.3 * (-sgn), 0.9, -27.8), 0.22, IRON_L, 4, name="Chain")
        for t in (0.25, 0.5, 0.75):
            cxp = xp + (1.3 * (-sgn)) * t
            dk.box(p, (cxp, 9.6 + (0.9 - 9.6) * t, -15.2 + (-27.8 + 15.2) * t), (0.55, 0.55, 0.55), IRON, jitter=0.03, name="Link")
    bx(p, -66.4, -53.6, 9.1, 9.8, -14.9, -14.1, WOOD, 0.05, name="Lintel")
    heater(p, -60, 10.8, -13.6, 2.6, 3.2, RED, GOLD)
    pennant(p, -60, 11.8, -14.5, 3.0, 1.6, ROOF_L, 1)
    bx(p, -60.12, -59.88, 9.8, 11.7, -14.6, -14.4, WOOD_D, 0.0, name="FlagPole")
    return p


def stripe_canopy(p, cx, cz, w, d, y_back, y_front, c1=RED, c2=CREAM, stripes=6, val=1.0, thick=0.35):
    """Striped awning sloping toward +z with a scalloped valance; stripes run front to back."""
    sw = w / stripes
    zb, zf = cz - d / 2, cz + d / 2
    for i in range(stripes):
        xc = cx - w / 2 + (i + 0.5) * sw
        low = val if i % 2 == 0 else val * 0.55
        prof = [(y_back, zb), (y_front, zf), (y_front - low, zf), (y_front - thick, zf - 0.3), (y_back - thick, zb)]
        slab(p, prof, sw - 0.02, 'yz', xc, c1 if i % 2 == 0 else c2, 0.05, name="Awning")


def stall(p, cx, cz, w, d, c1, c2, goods, y_roof=5.8):
    """Market stall: four posts, counter with a front board, striped awning, goods on the counter."""
    for sx in (-1, 1):
        for sz in (-1, 1):
            box_pole(p, cx + sx * (w / 2 - 0.25), cz + sz * (d / 2 - 0.25), 0, y_roof + 0.3, 0.4, WOOD_D)
    bx(p, cx - w / 2 + 0.2, cx + w / 2 - 0.2, 0.0, 2.7, cz + d / 2 - 0.9, cz + d / 2 - 0.1, WOOD, 0.06, name="Counter")
    bx(p, cx - w / 2 + 0.2, cx + w / 2 - 0.2, 2.7, 3.0, cz - d / 2 + 0.3, cz + d / 2 - 0.05, WOOD_L, 0.05, name="Top")
    bx(p, cx - w / 2 + 0.3, cx + w / 2 - 0.3, 0.0, y_roof, cz - d / 2 + 0.05, cz - d / 2 + 0.25, WOOD_D, 0.04, name="Back")
    stripe_canopy(p, cx, cz, w + 1.2, d + 2.8, y_roof + 0.6, y_roof - 0.5, c1, c2)
    goods(p, cx, cz + d / 2 - 0.8, 3.0)


def goods_fruit(p, cx, cz, y):
    for k, col in enumerate(((200, 50, 44), (232, 190, 60), (110, 170, 70), (200, 50, 44), (232, 190, 60))):
        dk.ball(p, (cx - 2.0 + k * 1.0, y + 0.45, cz + (0.2 if k % 2 else -0.3)), 0.45, col, subdiv=1, name="Fruit")
    bx(p, cx - 2.3, cx - 0.2, y, y + 0.5, cz - 0.9, cz + 0.3, WOOD_D, 0.05, name="Tray")
    for k in range(3):
        dk.ball(p, (cx + 0.8 + k * 0.7, y + 0.7, cz - 0.2), 0.38, (214, 90, 40), subdiv=1, name="Fruit")
    bx(p, cx + 0.5, cx + 2.5, y, y + 0.4, cz - 0.8, cz + 0.4, WOOD_D, 0.05, name="Tray")


def goods_swords(p, cx, cz, y):
    for k in range(4):
        x = cx - 2.0 + k * 1.35
        bx(p, x - 0.12, x + 0.12, y, y + 2.3, cz - 0.45, cz - 0.3, STEEL, 0.03, name="Blade")
        bx(p, x - 0.5, x + 0.5, y + 0.55, y + 0.8, cz - 0.5, cz - 0.25, GOLD_D, 0.03, name="Guard")
    heater(p, cx + 0.2, y + 1.2, cz + 0.45, 1.5, 1.8, ROOF, GOLD)
    heater(p, cx + 2.0, y + 1.0, cz + 0.45, 1.3, 1.6, RED, GOLD_L)


def goods_cloth(p, cx, cz, y):
    for k, col in enumerate((RED, ROOF, GOLD, (90, 150, 80), CREAM)):
        bx(p, cx - 2.3 + k * 1.0, cx - 1.5 + k * 1.0, y, y + 0.7 + (k % 2) * 0.3, cz - 0.5, cz + 0.4, col, 0.05, name="Bolt")
    for k in range(2):
        dk.cyl(p, (cx + 2.2, y + 0.55, cz + 0.1 - k * 0.2), 0.5, 1.1, (200, 120, 70), verts=6, jitter=0.08, name="Pot")


@part_builder("Market")
def build_Market():
    p = dk.Part("Market")
    stall(p, -14, -35, 6, 2.6, RED, CREAM, goods_fruit)
    stall(p, -6, -35, 6, 2.6, ROOF, CREAM, goods_swords)
    stall(p, 2, -35, 6, 2.6, GOLD, CREAM, goods_cloth)
    # handcart with hay
    bx(p, -11.4, -6.6, 1.0, 1.6, -31.3, -28.7, WOOD_D, 0.06, name="CartBed")
    for sz in (-1, 1):
        bx(p, -11.4, -6.6, 1.6, 2.4, -30 + sz * 1.3 - 0.1, -30 + sz * 1.3 + 0.1, WOOD, 0.06, name="CartSide")
    bx(p, -11.4, -11.2, 1.6, 2.4, -31.3, -28.7, WOOD, 0.06, name="CartEnd")
    dk.ball(p, (-8.8, 2.4, -30), 1.4, HAY, scale=(1.5, 0.6, 0.8), subdiv=1, jitter=0.08, name="Hay")
    for xx in (-11.4, -6.6):
        for sz in (-1, 1):
            dk.cyl(p, (xx, 1.1, -30 + sz * 1.4), 1.1, 0.35, WOOD_D, axis='z', verts=8, name="Wheel")
    rod(p, (-6.6, 1.3, -30), (-4.4, 0.4, -30), 0.2, WOOD, 4, name="Shaft")
    barrel(p, 0.0, 0, -30.5, 1.0, 2.4)
    barrel(p, 2.4, 0, -29.5, 1.0, 2.4)
    dk.ball(p, (0.0, 2.55, -30.5), 0.6, (200, 50, 44), subdiv=1, name="Apple")
    crate(p, -15, 0, -30, 1.8, WOOD, 8)
    crate(p, -13, 0, -29.2, 1.8, WOOD_L, -12)
    crate(p, -14.2, 1.8, -29.8, 1.4, WOOD_L, 20)
    # a hanging price sign and a tiny pennant on the middle stall
    bx(p, -6.1, -5.9, 5.8, 7.0, -37.5, -37.3, WOOD_D, 0.0, name="SignPole")
    pennant(p, -6, 6.6, -37.4, 2.2, 1.2, RED, 1)
    return p


def wall_tower(p, cx, cz, y1, r, roof_h, sides=8, roof_extra=0.8, bands=(5.0,)):
    round_tower(p, cx, cz, 0, y1, r, bands=bands, sides=sides, flare=0.3)
    dk.cyl(p, (cx, y1 + 0.5, cz), r + 0.6, 1.0, STONE_D, verts=sides, jitter=0.05, name="Corbel")
    cone_roof(p, cx, cz, y1 + 1.0, r + roof_extra, roof_h, ROOF, ROOF_L, sides=sides)


@part_builder("Walls")
def build_Walls():
    p = dk.Part("Walls")
    TOP = 8.0
    # wall runs
    stoneblock(p, -79, -41, 0, TOP, -58, -55, courses=4)
    stoneblock(p, -81, -78, 0, TOP, -58, -28, courses=4)
    stoneblock(p, -42, -39, 0, TOP, -58, -28, courses=4)
    stoneblock(p, -79, -66, 0, TOP, -29, -26, courses=4)
    stoneblock(p, -54, -41, 0, TOP, -29, -26, courses=4)
    for (x0, x1, z0, z1) in ((-79, -41, -58, -55), (-81, -78, -58, -28), (-42, -39, -58, -28), (-79, -66, -29, -26), (-54, -41, -29, -26)):
        bx(p, x0, x1, TOP - 0.1, TOP + 0.1, z0, z1, STONE_D, 0.03, name="WalkTop")
    merlon_line(p, 'x', -78, -42, -57.4, TOP, step=3.6, w=1.7, h=1.3, d=1.0)
    merlon_line(p, 'z', -56, -30, -80.4, TOP, step=3.6, w=1.7, h=1.3, d=1.0)
    merlon_line(p, 'z', -56, -30, -39.6, TOP, step=3.6, w=1.7, h=1.3, d=1.0)
    merlon_line(p, 'x', -77, -67, -26.4, TOP, step=3.6, w=1.7, h=1.3, d=1.0)
    merlon_line(p, 'x', -53, -43, -26.4, TOP, step=3.6, w=1.7, h=1.3, d=1.0)
    for xx in (-73, -48):
        slit(p, xx, 4.2, -25.8, '+z', 0.5, 2.2)
    # corner towers and gate towers
    for (cx, cz) in ((-78, -56), (-42, -56), (-78, -28), (-42, -28)):
        wall_tower(p, cx, cz, 14.0, 4.0, 5.2)
        for k in (1,):
            a = pi / 2 + k * 0.7 - 0.7
            slit(p, cx + 3.9 * math.cos(a), 9.5, cz + 3.9 * math.sin(a), '+z', 0.5, 1.8)
    for cx in (-66, -54):
        round_tower(p, cx, -27.5, 0, 11.0, 3.0, bands=(5.5,), sides=8, flare=0.3)
        dk.cyl(p, (cx, 11.5, -27.5), 3.6, 1.0, STONE_D, verts=8, jitter=0.05, name="Corbel")
        cone_roof(p, cx, -27.5, 12.0, 3.9, 3.0, ROOF, ROOF_L, sides=8)
        pennant(p, cx, 14.2, -27.5, 2.6, 1.5, RED if cx < -60 else ROOF_L, 1)
        dk.cyl(p, (cx, 14.0, -27.5), 0.12, 2.4, WOOD_D, verts=4, name="FlagPole")
        slit(p, cx, 6.0, -24.5, '+z', 0.45, 1.8)
    # gate arch between the gate towers, with raised portcullis
    arch_wall(p, -63.6, -56.4, 0, 9.4, -60, 2.7, 5.0, -26.2, 1.0, STONE)
    for k in range(5):
        xx = -62.0 + k * 1.0
        yt = 5.0 + math.sqrt(max(0.0, 2.7 ** 2 - (xx + 60) ** 2)) - 0.15
        bx(p, xx - 0.1, xx + 0.1, 3.6, yt, -25.9, -25.65, IRON, 0.03, name="Bar")
    bx(p, -62.6, -57.4, 4.5, 4.8, -25.95, -25.6, IRON, 0.03, name="Rail")
    bx(p, -64, -56, 8.0, 9.2, -28.6, -26, STONE_D, 0.04, name="Lintel")
    merlon_line(p, 'x', -63.4, -56.6, -26.3, 9.2, step=2.4, w=1.2, h=1.1, d=0.9)
    heater(p, -60, 7.4, -25.65, 1.9, 2.3, RED, GOLD)
    return p


@part_builder("Armory")
def build_Armory():
    p = dk.Part("Armory")
    bx(p, -28, -12, 0, 0.4, 48, 60, STONE_D, 0.06, name="Floor")
    stoneblock(p, -28, -12, 0.4, 6.6, 48.2, 49.6, courses=4)
    for xs in (-27.3, -12.7):
        slab(p, [(0.4, 49.6), (0.4, 55.6), (7.6, 55.6), (6.8, 49.6)], 1.4, 'yz', xs, STONE, 0.06, name="SideWall")
        slab(p, [(2.4, 49.6), (2.4, 55.6), (2.8, 55.6), (2.8, 49.6)], 1.6, 'yz', xs, STONE_D, 0.04, name="SideBand")
    mono_roof(p, -28.9, -11.1, 47.8, 7.2, 56.0, 8.4, 0.7, 3, ROOF, ROOF_L)
    for xp in (-28.2, -11.8):
        box_pole(p, xp, 55.5, 0.4, 7.9, 0.7, WOOD_D)
    # chimney
    bx(p, -26, -22.4, 7.5, 12.0, 49.0, 52.6, STONE_D, 0.06, name="Chimney")
    bx(p, -26.3, -22.1, 11.6, 12.0, 48.7, 52.9, STONE, 0.04, name="ChimneyCap")
    # forge: hearth with coals and fire colours, bellows
    bx(p, -26.4, -22.2, 0.4, 3.2, 49.7, 53.2, STONE_D, 0.07, name="Hearth")
    bx(p, -25.6, -23.0, 2.6, 3.3, 50.2, 52.7, (206, 70, 36), 0.04, name="Coals")
    dk.cone(p, (-24.3, 3.2, 51.4), 0.9, 1.6, FIRE, verts=5, name="Flame")
    dk.cone(p, (-24.3, 3.2, 51.4), 0.5, 1.1, FIRE_Y, verts=5, name="Flame")
    bx(p, -27.2, -26.4, 1.4, 2.2, 51.0, 52.6, WOOD_D, 0.05, name="BellowsA")
    dk.cone(p, (-26.3, 1.8, 51.8), 0.7, 1.4, WOOD, verts=4, rot=(0, 0, -90), name="BellowsB") if False else None
    # anvil on a log stump, hammer, water barrel, grindstone
    dk.cyl(p, (-19, 0.9, 55), 1.1, 1.5, WOOD, verts=7, jitter=0.08, name="Stump")
    bx(p, -20.3, -17.7, 1.5, 2.2, 54.4, 55.6, IRON, 0.03, name="AnvilBase")
    bx(p, -20.9, -17.1, 2.2, 2.8, 54.2, 55.8, IRON_L, 0.03, name="AnvilTop")
    dk.cyl(p, (-16.3, 2.5, 55), 0.5, 1.2, IRON_L, axis="x", verts=4, top_radius=0.05, name="AnvilHorn")
    bx(p, -19.6, -17.8, 2.8, 3.0, 54.8, 55.2, (240, 120, 50), 0.0, name="HotIron")
    barrel(p, -14.4, 0.4, 58.0, 1.1, 2.8)
    dk.cyl(p, (-14.4, 3.15, 58.0), 0.95, 0.15, WATER, verts=8, name="Water")
    dk.cyl(p, (-16.2, 1.2, 50.8), 1.0, 0.5, STONE, axis='z', verts=8, name="Grindstone")
    bx(p, -17.2, -15.2, 0.4, 1.2, 50.3, 51.3, WOOD_D, 0.05, name="GrindFrame")
    # racks on the back wall: swords and shields
    bx(p, -21.5, -12.5, 2.3, 2.7, 49.6, 49.9, WOOD_D, 0.03, name="RackBar")
    bx(p, -21.5, -12.5, 4.9, 5.3, 49.6, 49.9, WOOD_D, 0.03, name="RackBar")
    for k in range(6):
        x = -20.8 + k * 1.6
        bx(p, x - 0.12, x + 0.12, 2.5, 5.0 + (k % 2) * 0.5, 49.9, 50.1, STEEL, 0.03, name="Sword")
        bx(p, x - 0.4, x + 0.4, 4.2, 4.4, 49.9, 50.2, GOLD_D, 0.03, name="Guard")
    heater(p, -17.5, 6.6, 49.7, 1.6, 1.9, RED, GOLD)
    heater(p, -14.5, 6.6, 49.7, 1.6, 1.9, ROOF, GOLD)
    # swinging shop sign at the front with crossed swords
    bx(p, -11.2, -11.0, 5.0, 8.6, 59.4, 59.6, WOOD_D, 0.0, name="SignPost")
    bx(p, -11.2, -9.6, 8.4, 8.6, 59.4, 59.6, WOOD_D, 0.0, name="SignArm")
    slab(p, [(-10.9, 6.2), (-9.5, 6.2), (-9.5, 8.0), (-10.9, 8.0)], 0.3, 'xy', 59.5, CREAM, 0.03, name="SignBoard")
    rod(p, (-10.8, 6.3, 59.8), (-9.6, 7.9, 59.8), 0.1, STEEL_D, 4, name="SignSword")
    rod(p, (-9.6, 6.3, 59.8), (-10.8, 7.9, 59.8), 0.1, STEEL_D, 4, name="SignSword")
    return p


@part_builder("Stables")
def build_Stables():
    p = dk.Part("Stables")
    bx(p, -90.4, -69.6, 0, 0.35, 50, 62, DIRT, 0.06, name="Floor")
    stoneblock(p, -90, -70, 0.35, 0.9, 50.1, 51.5, courses=1, ca=STONE_D)
    bx(p, -90, -70, 0.35, 5.6, 50.2, 51.4, WOOD, 0.07, name="BackWall")
    for k in range(10):
        bx(p, -89.7 + k * 2.0, -89.5 + k * 2.0, 0.35, 5.6, 51.35, 51.55, WOOD_D, 0.05, name="Batten")
    bx(p, -90, -88.8, 0.35, 5.6, 50.2, 62, WOOD, 0.07, name="SideWall")
    bx(p, -71.2, -70, 0.35, 5.6, 50.2, 58, WOOD, 0.07, name="SideWall")
    mono_roof(p, -90.6, -69.4, 49.6, 5.5, 58.6, 7.7, 0.6, 3, RED, RED_L)
    for xp in (-89.4, -80.0, -70.6):
        box_pole(p, xp, 58.1, 0.35, 7.4, 0.7, WOOD_D)
    # stall partitions, hay stack, trough, saddle rack
    for xx in (-85.5, -80.5):
        bx(p, xx - 0.15, xx + 0.15, 0.35, 3.2, 51.4, 56, WOOD_D, 0.05, name="Divider")
    for (hx, hz) in ((-88, 53.2), (-87.6, 54.8), (-88.3, 56.4)):
        hay_bale(p, hx, hz, 1.8, 1.3, 1.5, R.uniform(-10, 10), 0.35)
    hay_bale(p, -88, 54, 1.8, 1.3, 1.5, 5, 1.65)
    bx(p, -79, -73, 0.35, 1.5, 57.8, 59.2, WOOD_D, 0.05, name="Trough")
    bx(p, -78.6, -73.4, 1.2, 1.55, 58.0, 59.0, WATER, 0.02, name="TroughWater")
    bx(p, -74.2, -72.8, 0.35, 2.0, 52, 53.6, WOOD, 0.05, name="SaddleRack")
    bx(p, -74.6, -72.4, 2.0, 2.5, 51.8, 53.8, RED_D, 0.04, name="Saddle")
    # fence along the front, pointed posts
    for k in range(7):
        xx = -90 + k * 20 / 6
        stake(p, xx, 61.7, 0.35, 3.2, 0.7, 0.7, WOOD_D, tip=0.4)
    bx(p, -90, -70, 1.3, 1.75, 61.35, 61.85, WOOD, 0.05, name="Rail")
    bx(p, -90, -70, 2.3, 2.75, 61.35, 61.85, WOOD, 0.05, name="Rail")
    # the war horse in a red and gold caparison and a second smaller one in the stall
    horse(p, -79, 0.35, 59.6, 0.95, yaw=0, cloth=RED, cloth2=GOLD)
    horse(p, -84.2, 0.35, 54.8, 0.8, yaw=-90, color=(210, 200, 186), mane=(150, 140, 126))
    # horseshoe sign and a lantern
    bx(p, -70.4, -70.2, 3.0, 6.2, 61.2, 61.4, WOOD_D, 0.0, name="LampPost")
    dk.box(p, (-70.3, 6.4, 61.3), (0.9, 0.9, 0.9), GOLD, jitter=0.03, name="Lantern")
    return p


@part_builder("Training")
def build_Training():
    p = dk.Part("Training")
    bx(p, -58, -38, 0, 0.3, 47, 61, DIRT, 0.07, name="Ground")
    dummies = ((-53, 52, 15), (-47, 57, -20), (-42, 51, 25))
    for (x, z, ry) in dummies:
        a = math.radians(ry)
        dk.cyl(p, (x, 2.5, z), 0.45, 5.0, WOOD, verts=6, jitter=0.06, name="DummyPost")
        dk.box(p, (x, 3.8, z), (3.0, 0.5, 0.6), WOOD, rot=(0, ry, 0), jitter=0.05, name="Arms")
        dk.cyl(p, (x, 2.3, z), 0.9, 2.2, HAY, verts=7, jitter=0.1, name="DummyBody")
        dk.ball(p, (x, 5.0, z), 0.8, HAY, subdiv=1, jitter=0.06, name="DummyHead")
        dk.cyl(p, (x, 5.55, z), 0.85, 0.4, RED, verts=7, name="Cap")
        # target ring on the chest and a wooden shield on one arm
        dk.cyl(p, (x + 0.0, 2.6, z + 0.9), 0.55, 0.2, RED, axis='z', verts=8, rot=(0, ry, 0), name="Target")
        dk.cyl(p, (x + 1.5 * math.cos(a), 3.2, z - 1.5 * math.sin(a) + 0.35), 0.6, 0.25, ROOF, axis='z', verts=8, rot=(0, ry, 0), name="ArmShield")
        dk.box(p, (x, 0.2, z), (1.4, 0.4, 1.4), STONE_D, jitter=0.05, name="Foot")
    # hay bale targets and a bull's-eye on a stand
    hay_bale(p, -55, 57, 2.4, 1.8, 1.8, 10)
    hay_bale(p, -52.4, 58.4, 2.4, 1.8, 1.8, -8)
    hay_bale(p, -55, 57, 2.4, 1.8, 1.8, 10, y0=1.8) if False else None
    hay_bale(p, -40.5, 56, 1.8, 1.8, 2.4, 0)
    dk.cyl(p, (-41, 3.2, 59), 1.8, 0.5, CREAM, axis='z', verts=10, name="Target")
    dk.cyl(p, (-41, 3.2, 59.3), 1.2, 0.3, RED, axis='z', verts=10, name="Target")
    dk.cyl(p, (-41, 3.2, 59.5), 0.55, 0.3, GOLD, axis='z', verts=8, name="Target")
    dk.cyl(p, (-41, 1.6, 58.6), 0.3, 3.2, WOOD_D, verts=5, name="TargetPole")
    # sword rack with wooden swords and shields
    bx(p, -51.5, -44.5, 0.3, 2.8, 48.7, 49.3, WOOD_D, 0.05, name="Rack")
    for k in range(6):
        x = -51.0 + k * 1.15
        bx(p, x - 0.12, x + 0.12, 1.8, 4.1, 49.3, 49.5, WOOD_L, 0.05, name="WoodSword")
        bx(p, x - 0.45, x + 0.45, 2.4, 2.65, 49.3, 49.6, WOOD_D, 0.03, name="Guard")
    heater(p, -48, 4.6, 49.0, 1.5, 1.8, ROOF, GOLD)
    # rope fence on the road side
    for xx in (-57, -52, -47, -42, -39):
        box_pole(p, xx, 60.6, 0.3, 2.3, 0.4, WOOD_D)
    bx(p, -57, -39, 1.9, 2.1, 60.45, 60.75, (196, 170, 120), 0.05, name="Rope")
    return p


@part_builder("Fountain")
def build_Fountain():
    p = dk.Part("Fountain")
    cx, cz = 18, 20
    # basin: stone ring with a rim, water, stepped base
    lathe(p, (cx, 0, cz), [(7.0, 0), (7.0, 1.7), (6.6, 1.7), (6.6, 0.4)], 12, STONE_L, 0.06, name="BasinWall")
    dk.cyl(p, (cx, 1.75, cz), 7.0, 0.5, STONE, verts=12, jitter=0.05, name="Rim")
    dk.cyl(p, (cx, 2.05, cz), 6.2, 0.2, WATER, verts=12, name="Water")
    dk.cyl(p, (cx, 2.2, cz), 3.0, 0.1, WATER_L, verts=10, name="Ripple")
    # central column with two bowls
    lathe(p, (cx, 2.0, cz), [(1.2, 0), (0.9, 1.0), (0.9, 5.5), (1.1, 6.0)], 8, STONE, 0.06, name="Column")
    lathe(p, (cx, 8.0, cz), [(0.5, 0), (3.3, 0.5), (3.7, 1.2), (3.3, 1.3), (0.0, 1.0)], 10, STONE_L, 0.05, name="Bowl")
    dk.cyl(p, (cx, 8.9, cz), 3.1, 0.15, WATER, verts=10, name="BowlWater")
    lathe(p, (cx, 9.0, cz), [(0.8, 0), (0.6, 1.0), (0.6, 3.2), (0.9, 3.8)], 8, STONE, 0.06, name="Stem")
    # the knight statue
    bx(p, cx - 1.3, cx + 1.3, 11.9, 12.6, cz - 1.3, cz + 1.3, STONE_D, 0.05, name="Plinth")
    bx(p, cx - 0.9, cx - 0.1, 12.6, 14.6, cz - 0.4, cz + 0.4, STEEL_D, 0.04, name="Leg")
    bx(p, cx + 0.1, cx + 0.9, 12.6, 14.6, cz - 0.4, cz + 0.4, STEEL_D, 0.04, name="Leg")
    bx(p, cx - 1.2, cx + 1.2, 14.6, 17.0, cz - 0.7, cz + 0.7, STEEL, 0.05, name="Torso")
    dk.ball(p, (cx, 17.9, cz), 0.95, STEEL, subdiv=1, name="Helmet")
    bx(p, cx - 0.12, cx + 0.12, 18.4, 18.9, cz + 0.6, cz + 1.0, RED, 0.0, name="Visor")
    dk.cone(p, (cx, 18.7, cz), 0.3, 0.9, RED, verts=4, name="Plume")
    bx(p, cx + 1.2, cx + 1.6, 14.8, 17.3, cz - 0.2, cz + 0.2, STEEL, 0.03, name="Arm")
    rod(p, (cx + 1.5, 15.4, cz + 0.2), (cx + 1.5, 19.2, cz + 0.2), 0.14, STEEL_D, 4, name="Sword")
    bx(p, cx + 0.9, cx + 2.1, 16.6, 16.9, cz, cz + 0.4, GOLD_D, 0.03, name="Guard")
    heater(p, cx - 1.7, 15.8, cz + 0.55, 1.5, 1.9, ROOF, GOLD)
    # water jets from the upper bowl and basin edge
    for k in range(6):
        a = 2 * pi * k / 6
        dk.cone(p, (cx + 2.2 * math.cos(a), 9.1, cz + 2.2 * math.sin(a)), 0.28, 1.1, WATER_L, verts=4, name="Jet")
    # four corner pillars with gold lanterns
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        px, pz = cx + sx * 6.4, cz + sz * 6.4
        bx(p, px - 0.7, px + 0.7, 0, 0.7, pz - 0.7, pz + 0.7, STONE_D, 0.05, name="Foot")
        dk.cyl(p, (px, 2.3, pz), 0.4, 3.2, STONE, verts=6, name="Pillar")
        bx(p, px - 0.55, px + 0.55, 3.9, 4.4, pz - 0.55, pz + 0.55, GOLD, 0.03, name="Lantern")
        dk.cone(p, (px, 4.4, pz), 0.55, 0.5, GOLD_D, verts=4, name="LampTop") if False else None
    return p


# ---- part 2: pavilion .. excalibur --------------------------------------------------------------------------------
def mono_roof(p, x0, x1, z_back, y_back, z_front, y_front, t, n, ca, cb, name="Roof"):
    """Single-pitch roof, n courses from the back eave to the front eave, rising toward +z, thickness t downward."""
    for i in range(n):
        a, b = i / n, (i + 1) / n
        za, zb = z_back + (z_front - z_back) * a, z_back + (z_front - z_back) * b
        ya, yb = y_back + (y_front - y_back) * a, y_back + (y_front - y_back) * b
        slab(p, [(ya, za), (yb, zb), (yb - t, zb), (ya - t, za)], x1 - x0, 'yz', (x0 + x1) / 2, ca if i % 2 == 0 else cb, 0.05, name=name)


def arch_side(p, x, y0, spring, hw, zc, thick, color, segs=5, jitter=0.03, name="SideArch"):
    """Round-headed shape on a wall facing +-x (yz plane), centred at z=zc."""
    pts = [(y0, zc - hw), (y0, zc + hw), (spring, zc + hw)]
    for k in range(1, segs):
        a = pi * k / segs
        pts.append((spring + hw * math.sin(a), zc + hw * math.cos(a)))
    pts.append((spring, zc - hw))
    return slab(p, pts, thick, 'yz', x, color, jitter, name=name)


def diamond(p, x, y, z, w, h, color, thick=0.3, name="Gem"):
    return slab(p, [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)], thick, 'xy', z, color, 0.02, name=name)


def boulder(p, cx, y0, cz, rx, h, rz, color, sides=8, wob=0.16, top=0.6, moss=True, name="Boulder", yaw=0.0):
    """Lumpy low-poly rock: 4 rings, up-facing faces mossy, low faces darker."""
    lv = [(0.0, 0.88), (0.42, 1.0), (0.82, 0.78), (1.0, top)]
    rings = []
    a0 = R.uniform(0, 1) + math.radians(yaw)
    for (hy, rf) in lv:
        ring = []
        for i in range(sides):
            a = a0 + 2 * pi * i / sides
            k = rf * (1 + wob * (R.random() - 0.5) * 2) if hy > 0 else rf
            ring.append((cx + rx * k * math.cos(a), y0 + h * hy * (1 + 0.06 * (R.random() - 0.5)), cz + rz * k * math.sin(a)))
        rings.append(ring)
    o = loft(p, rings, color, 0.07, caps=True, name=name)
    if moss:
        def fn(c, n, i):
            if n[1] > (0.55 if h < 5 else 0.82):
                return mix(GRASS_D, GRASS_L, R.random())
            if n[1] < 0.3 and c[1] - y0 < h * 0.35:
                return STONE_D
            return None
        recolor(o, fn, 0.05)
    return o


def torch_stand(p, x, z, h=3.6, full=True):
    dk.cyl(p, (x, h / 2, z), 0.22, h, WOOD_D, verts=5, name="TorchPole")
    dk.cyl(p, (x, h + 0.25, z), 0.55, 0.5, IRON, verts=6, top_radius=0.75, name="Brazier")
    if full:
        fire(p, x, h + 0.45, z, 0.55, 1.5)
    else:
        dk.cone(p, (x, h + 0.45, z), 0.5, 1.5, FIRE, verts=5, name="Flame")
        dk.cone(p, (x, h + 0.45, z), 0.28, 1.0, FIRE_Y, verts=4, name="Flame")


@part_builder("Pavilion")
def build_Pavilion():
    p = dk.Part("Pavilion")
    cx = 78.0
    # wooden floor and the blue-trimmed tent walls
    bx(p, 70.6, 85.4, 0, 0.5, 42, 54, WOOD_D, 0.06, name="Floor")
    bx(p, 70.8, 85.2, 0.5, 5.0, 42.0, 42.6, CREAM, 0.04, name="BackWall")
    slab(p, [(70.8, 5.0), (85.2, 5.0), (cx, 11.2)], 0.5, 'xy', 42.3, CREAM, 0.04, name="BackGable")
    for sx in (70.8, 85.0):
        bx(p, sx, sx + 0.2, 0.5, 5.0, 42.0, 54.0, CREAM, 0.04, name="SideWall")
        for zz in (45.0, 49.0, 53.0):
            bx(p, sx - 0.05, sx + 0.25, 0.5, 5.0, zz - 0.18, zz + 0.18, ROOF, 0.03, name="WallStripe")
    # roof: red and cream stripes, two slopes, scalloped valance in blue and gold
    n = 8
    zs = [41.5 + 13.0 * k / n for k in range(n + 1)]
    for k in range(n):
        col = RED if k % 2 == 0 else CREAM
        z0, z1 = zs[k] + 0.02, zs[k + 1] - 0.02
        zc, dz = (z0 + z1) / 2, z1 - z0
        slab(p, [(69.8, 4.8), (cx, 12.0), (cx, 11.3), (69.8, 4.1)], dz, 'xy', zc, col, 0.05, name="RoofL")
        slab(p, [(86.2, 4.8), (cx, 12.0), (cx, 11.3), (86.2, 4.1)], dz, 'xy', zc, col, 0.05, name="RoofR")
        for xe in (69.9, 86.1):
            slab(p, [(4.3, z0), (4.3, z1), (3.2, zc)], 0.3, 'yz', xe, ROOF if k % 2 == 0 else GOLD, 0.03, name="Valance")
    for sg in (-1, 1):
        rod(p, (cx + sg * 8.25, 4.4, 54.4), (cx, 11.9, 54.4), 0.22, GOLD, 5, name="FrontTrim")
        rod(p, (cx + sg * 8.25, 4.4, 41.6), (cx, 11.9, 41.6), 0.22, GOLD_D, 5, name="BackTrim")
    rod(p, (cx, 12.0, 41.6), (cx, 12.0, 54.4), 0.25, GOLD, 5, name="Ridge")
    for xx in (71.2, 84.8):
        dk.cyl(p, (xx, 2.7, 53.6), 0.35, 4.4, GOLD, verts=6, name="Post")
        dk.ball(p, (xx, 5.1, 53.6), 0.5, GOLD_L, subdiv=1, name="PostKnob")
    slab(p, [(70.8, 5.0), (85.2, 5.0), (cx, 11.0)], 0.4, 'xy', 53.8, CREAM, 0.04, name="FrontGable")
    bx(p, 70.8, 85.2, 4.2, 5.0, 53.7, 54.1, RED, 0.04, name="Pelmet")
    heater(p, cx, 7.7, 54.1, 3.0, 3.6, RED, GOLD)
    # the golden centre pole with a red pennant
    dk.cyl(p, (cx, 16.0, 48.0), 0.32, 8.4, GOLD, verts=6, name="Pole")
    dk.ball(p, (cx, 20.4, 48.0), 0.65, GOLD_L, subdiv=1, name="Finial")
    pennant(p, cx + 0.2, 18.9, 48.0, 3.4, 1.9, RED, 1)
    # throne on a stepped dais with a red rug leading to it
    bx(p, 75.0, 81.0, 0.5, 1.0, 42.6, 47.0, STONE_D, 0.05, name="Step")
    bx(p, 75.6, 80.4, 1.0, 1.6, 42.8, 46.2, STONE, 0.05, name="Step")
    bx(p, 76.6, 79.4, 1.6, 2.7, 43.2, 45.4, GOLD, 0.04, name="Seat")
    bx(p, 76.9, 79.1, 2.7, 3.0, 43.6, 45.2, RED, 0.03, name="Cushion")
    bx(p, 76.4, 79.6, 2.7, 7.0, 42.8, 43.6, GOLD, 0.04, name="Back")
    bx(p, 76.8, 79.2, 3.1, 6.4, 43.55, 43.8, RED_D, 0.03, name="BackPad")
    for xx in (76.4, 79.6):
        bx(p, xx - 0.4, xx + 0.4, 2.7, 4.2, 43.2, 45.4, GOLD_D, 0.04, name="Arm")
    for k, xx in enumerate((76.7, 78.0, 79.3)):
        dk.cone(p, (xx, 7.0, 43.2), 0.5, 1.2 if k == 1 else 0.9, GOLD_L, verts=4, name="Crown")
    heater(p, cx, 8.9, 42.7, 4.4, 5.2, RED, GOLD)
    bx(p, 74.8, 81.2, 0.5, 0.62, 46.2, 54.0, RED, 0.03, name="Rug")
    bx(p, 74.6, 74.8, 0.5, 0.66, 46.2, 54.0, GOLD, 0.02, name="RugTrim")
    bx(p, 81.2, 81.4, 0.5, 0.66, 46.2, 54.0, GOLD, 0.02, name="RugTrim")
    # side table with goblet and fruit, a stool, torches
    bx(p, 72.0, 74.4, 0.5, 2.3, 49.4, 51.6, WOOD, 0.06, name="Table")
    bx(p, 71.8, 74.6, 2.3, 2.6, 49.2, 51.8, WOOD_L, 0.05, name="TableTop")
    dk.cyl(p, (72.7, 3.0, 50.2), 0.28, 0.9, GOLD, verts=6, top_radius=0.4, name="Goblet")
    dk.ball(p, (73.6, 2.9, 50.9), 0.32, RED_L, subdiv=1, name="Apple")
    dk.ball(p, (73.2, 2.9, 50.0), 0.32, GOLD_L, subdiv=1, name="Apple")
    bx(p, 82.0, 84.0, 0.5, 1.8, 50.0, 51.8, ROOF, 0.05, name="Stool")
    bx(p, 81.9, 84.1, 1.8, 2.1, 49.9, 51.9, GOLD, 0.04, name="StoolTop")
    torch_stand(p, 74.0, 52.8, 3.4)
    torch_stand(p, 82.0, 52.8, 3.4)
    return p


def arrow(p, x, y, z, ln, col=WOOD_L, ang=0.0):
    """Arrow stuck in a target face (+z side), shaft pointing toward +z."""
    rod(p, (x, y, z), (x + ln * math.sin(ang), y, z + ln), 0.1, col, 4, name="Arrow")
    zt = z + ln
    bx(p, x - 0.35, x + 0.35, y - 0.04, y + 0.04, zt - 0.8, zt, RED, 0.02, name="Fletch")
    bx(p, x - 0.04, x + 0.04, y - 0.35, y + 0.35, zt - 0.8, zt, WHITE, 0.02, name="Fletch")


@part_builder("Archery")
def build_Archery():
    p = dk.Part("Archery")
    # hay backstop: two courses of big bales with straps
    for row, (n, x0) in enumerate(((6, 67.0), (5, 68.8))):
        y0 = 0.0 + row * 1.8
        for k in range(n):
            xa = x0 + k * 3.6
            bx(p, xa + 0.04, xa + 3.56, y0, y0 + 1.76, -12.8, -11.2, HAY if (k + row) % 2 else HAY_D, 0.1, name="Bale")
            bx(p, xa + 1.7, xa + 1.9, y0 - 0.0, y0 + 1.8, -11.25, -11.1, WOOD_D, 0.03, name="Strap")
    for xx in (66.6, 89.4):
        dk.cyl(p, (xx, 3.6, -11.6), 0.3, 7.2, WOOD_D, verts=5, name="BackPole")
        dk.ball(p, (xx, 7.4, -11.6), 0.4, GOLD, subdiv=1, name="Knob")
    pennant(p, 66.9, 6.3, -11.6, 3.2, 1.8, RED, 1)
    pennant(p, 89.1, 6.3, -11.6, 3.2, 1.8, ROOF_L, -1)
    # three target stands
    for k, x in enumerate((70.0, 78.0, 86.0)):
        for sg in (-1, 1):
            rod(p, (x + sg * 1.9, 0.0, -7.3), (x + sg * 0.3, 4.6, -9.0), 0.2, WOOD_D, 4, name="Leg")
        rod(p, (x, 0.0, -11.2), (x, 5.0, -9.2), 0.2, WOOD_D, 4, name="Brace")
        bx(p, x - 1.0, x + 1.0, 2.4, 2.7, -9.1, -8.5, WOOD_D, 0.04, name="Rail")
        dk.cyl(p, (x, 5.4, -8.65), 2.7, 0.3, WOOD, axis='z', verts=10, name="Frame")
        dk.cyl(p, (x, 5.4, -8.4), 2.45, 0.3, CREAM, axis='z', verts=10, name="Ring")
        dk.cyl(p, (x, 5.4, -8.25), 1.95, 0.3, ROOF, axis='z', verts=10, name="Ring")
        dk.cyl(p, (x, 5.4, -8.1), 1.4, 0.3, RED, axis='z', verts=10, name="Ring")
        dk.cyl(p, (x, 5.4, -7.95), 0.75, 0.3, GOLD, axis='z', verts=8, name="Bullseye")
    arrow(p, 70.4, 6.0, -7.85, 1.8, ang=0.1)
    arrow(p, 69.2, 4.6, -7.85, 1.5, ang=-0.1)
    arrow(p, 78.1, 5.5, -7.8, 2.0)
    arrow(p, 79.2, 6.6, -7.85, 1.6, ang=0.08)
    arrow(p, 85.6, 4.7, -7.85, 1.7, ang=-0.08)
    arrow(p, 87.0, 5.9, -7.85, 1.4, ang=0.1)
    # shooting line: rope between posts with little flags and a log barrier
    for xx in (68.0, 88.0, 78.0):
        dk.cyl(p, (xx, 1.3, 1.0), 0.32, 2.6, WOOD_D, verts=5, name="LinePost")
    bx(p, 68.0, 88.0, 1.9, 2.1, 0.85, 1.15, (196, 170, 120), 0.04, name="Rope")
    dk.cyl(p, (78.0, 0.45, 1.8), 0.45, 20.0, WOOD, axis='x', verts=6, jitter=0.06, name="Log")
    for k, xx in enumerate((71.0, 74.5, 81.5, 85.0)):
        slab(p, [(xx - 0.5, 1.9), (xx + 0.5, 1.9), (xx + 0.5, 0.9), (xx, 1.3), (xx - 0.5, 0.9)], 0.1, 'xy', 1.0, RED if k % 2 else ROOF_L, 0.03, name="LineFlag")
    # quiver rack with a bow
    for zz in (-4.3, -1.7):
        bx(p, 66.0, 66.5, 0.0, 3.2, zz - 0.2, zz + 0.2, WOOD_D, 0.05, name="RackLeg")
    bx(p, 65.9, 67.1, 2.7, 3.0, -4.5, -1.5, WOOD, 0.05, name="RackTop")
    bx(p, 65.9, 67.1, 1.0, 1.2, -4.5, -1.5, WOOD, 0.05, name="RackBar")
    for k, zz in enumerate((-3.6, -3.0, -2.4)):
        dk.cyl(p, (66.5, 1.9, zz), 0.28, 1.8, WOOD_D if k == 1 else (122, 70, 48), verts=5, name="Quiver")
        for dz in (-0.1, 0.1):
            bx(p, 66.4, 66.6, 2.8, 3.8, zz + dz - 0.04, zz + dz + 0.04, WOOD_L, 0.02, name="ArrowEnd")
        bx(p, 66.3, 66.7, 3.4, 4.0, zz - 0.2, zz + 0.2, RED if k != 1 else WHITE, 0.02, name="Fletch")
    rod(p, (67.6, 0.0, -1.8), (67.2, 2.6, -2.6), 0.1, WOOD, 4, name="BowA")
    rod(p, (67.2, 2.6, -2.6), (67.6, 5.2, -3.4), 0.1, WOOD, 4, name="BowB")
    return p


@part_builder("Garden")
def build_Garden():
    p = dk.Part("Garden")
    # hedge walls with a lighter top and little flowers
    def hedge(x0, x1, z0, z1, h=3.6):
        bx(p, x0, x1, 0, h - 0.5, z0, z1, HEDGE_L, 0.08, name="Hedge")
        bx(p, x0 - 0.12, x1 + 0.12, h - 0.9, h + 0.3, z0 - 0.12, z1 + 0.12, (118, 178, 90), 0.1, name="HedgeTop")
    bx(p, 17.5, 30.5, 0, 0.15, -34.3, -24.0, SAND, 0.05, name="Gravel")
    hedge(16.0, 32.0, -35.8, -34.2)
    hedge(16.0, 17.6, -34.2, -25.8)
    hedge(30.4, 32.0, -34.2, -25.8)
    hedge(16.0, 20.6, -25.6, -24.0)
    hedge(27.4, 32.0, -25.6, -24.0)
    for k, (x, z, col) in enumerate(((18.0, -35.0, RED_L), (22.0, -35.0, GOLD_L), (26.0, -35.0, WHITE), (30.0, -35.0, RED_L),
                                      (16.8, -30.0, GOLD_L), (31.2, -29.0, WHITE), (16.8, -33.0, RED_L), (31.2, -33.0, GOLD_L), (18.5, -24.8, WHITE), (29.5, -24.8, RED_L))):
        dk.box(p, (x, 4.2, z), (0.8, 0.8, 0.8), col, rot=(0, 20 * k, 0), name="HedgeFlower")
    # topiary cones at the front corners
    for x in (16.8, 31.2):
        bx(p, x - 0.6, x + 0.6, 0, 0.6, -25.4, -24.2, STONE_D, 0.04, name="Pot")
        dk.cone(p, (x, 0.6, -24.8), 1.0, 3.6, HEDGE_D, verts=6, jitter=0.08, name="Topiary")
        dk.ball(p, (x, 4.5, -24.8), 0.5, GOLD, subdiv=1, name="TopiaryTop")
    # white rose arch
    for xx in (21.2, 26.8):
        bx(p, xx - 0.3, xx + 0.3, 0, 3.8, -25.1, -24.5, CREAM, 0.03, name="ArchPost")
    prev = (21.2, 3.8)
    for k in range(1, 7):
        a = pi * k / 6
        cur = (24 - 2.8 * math.cos(a), 3.8 + 1.8 * math.sin(a))
        rod(p, (prev[0], prev[1], -24.8), (cur[0], cur[1], -24.8), 0.28, CREAM, 5, name="ArchRing")
        prev = cur
    for k, (x, y) in enumerate(((21.3, 2.4), (21.5, 4.5), (22.4, 5.2), (24.0, 5.6), (25.6, 5.2), (26.5, 4.5), (26.7, 2.4), (21.1, 3.4), (26.9, 3.4))):
        dk.ball(p, (x, y, -24.4), 0.38, RED_L if k % 3 else WHITE, subdiv=1, name="ArchRose")
        dk.box(p, (x + 0.35, y - 0.2, -24.5), (0.5, 0.2, 0.3), HEDGE_L, rot=(0, 0, 30), name="Leaf")
    # rose beds, a stone bird bath on a pedestal, paving
    bx(p, 18.0, 21.6, 0, 0.7, -33.6, -27.0, DIRT, 0.05, name="Bed")
    bx(p, 26.4, 30.0, 0, 0.7, -33.6, -27.0, DIRT, 0.05, name="Bed")
    for k, (x, z) in enumerate(((18.9, -32.4), (20.6, -30.2), (19.4, -28.0), (27.3, -32.4), (28.9, -30.2), (27.6, -28.0))):
        bush(p, x, 0.6, z, 1.05, HEDGE_L if k % 2 else (96, 160, 74), sy=0.8)
        for j in range(2):
            dk.ball(p, (x + (j - 0.5) * 0.7, 1.9 + j * 0.15, z + 0.3), 0.5, (RED_L, GOLD_L, (236, 130, 170), WHITE)[(k + j) % 4], subdiv=1, name="Rose")
    bx(p, 22.6, 25.4, 0, 0.5, -31.9, -29.1, STONE_D, 0.05, name="BathBase")
    lathe(p, (24.0, 0.5, -30.5), [(0.8, 0), (0.55, 0.6), (0.55, 2.2), (1.9, 2.8), (1.8, 3.3), (1.4, 3.2)], 8, STONE_L, 0.05, name="Bath")
    dk.cyl(p, (24.0, 3.6, -30.5), 1.4, 0.1, WATER, verts=8, name="BathWater")
    dk.ball(p, (24.0, 4.1, -30.5), 0.38, GOLD, subdiv=1, name="Bird")
    for k in range(3):
        bx(p, 23.3, 24.7, 0.0, 0.2, -26.6 + k * 1.1, -25.9 + k * 1.1, STONE_L, 0.04, name="Paver")
    # stone bench with a cushion
    bx(p, 18.0, 21.0, 0.0, 0.9, -35.0, -34.0, STONE_D, 0.04, name="BenchBase")
    bx(p, 17.8, 21.2, 0.9, 1.3, -35.1, -33.7, STONE_L, 0.05, name="BenchTop")
    bx(p, 18.4, 20.6, 1.3, 1.6, -34.9, -34.0, RED, 0.04, name="Cushion")
    return p


@part_builder("Chapel")
def build_Chapel():
    p = dk.Part("Chapel")
    cx = -12.0
    stoneblock(p, -17, -7, 0, 9, -54, -44, courses=5, ca=CREAM, cb=STONE_W)
    bx(p, -17.3, -6.7, 0, 0.7, -54.3, -43.7, STONE_D, 0.05, name="Plinth")
    gable(p, 'z', -54.7, -43.3, cx, 6.2, 8.8, 14.2, 0.6, ROOF, ROOF_L, n=3)
    bx(p, cx - 0.3, cx + 0.3, 14.0, 14.4, -54.7, -43.3, ROOF_D, 0.03, name="Ridge")
    gable_end(p, 'z', -44.1, cx, 5.8, 9.0, 13.6, 0.8, STONE_W)
    gable_end(p, 'z', -53.9, cx, 5.8, 9.0, 13.6, 0.8, STONE_W)
    # round apse behind the altar
    lathe(p, (cx, 0, -54), [(3.7, 0), (3.5, 0.8), (3.5, 7.2)], 10, CREAM, 0.06, name="Apse")
    cone_roof(p, cx, -54, 7.0, 4.1, 3.6, ROOF, ROOF_L, sides=10)
    arch_fill(p, cx, 2.6, 4.2, 0.7, -57.45, 0.3, ROOF_L)
    # buttresses and stained glass windows on both long sides
    for xs, sg in ((-17.4, -1), (-6.6, 1)):
        for zz in (-53.4, -49.0, -44.8):
            bx(p, xs - 0.5, xs + 0.5, 0, 5.4, zz - 0.6, zz + 0.6, STONE, 0.05, name="Buttress")
            bx(p, xs - 0.4, xs + 0.4, 5.4, 5.9, zz - 0.5, zz + 0.5, STONE_L, 0.04, name="ButtressCap")
        xw = -17.0 if sg < 0 else -7.0
        for zz in (-51.2, -46.8):
            arch_side(p, xw + sg * 0.05, 2.6, 5.0, 1.1, zz, 0.3, STONE_L)
            arch_side(p, xw + sg * 0.15, 2.9, 5.0, 0.8, zz, 0.3, ROOF_L)
    # bell tower with belfry, blue spire and golden cross
    stoneblock(p, -14.3, -9.7, 0, 14, -45.8, -41.2, courses=7, ca=STONE, cb=STONE_W)
    bx(p, -14.6, -9.4, 13.6, 14.2, -46.1, -40.9, STONE_D, 0.04, name="Band")
    bx(p, -14.3, -9.7, 14.2, 19.4, -45.8, -41.2, STONE_W, 0.05, name="Belfry")
    for (xx, zz) in ((-14.45, -46.0), (-9.55, -46.0), (-14.45, -41.0), (-9.55, -41.0)):
        bx(p, xx - 0.35, xx + 0.35, 14.2, 19.6, zz - 0.35, zz + 0.35, STONE, 0.04, name="BelfryPost")
    bx(p, -14.8, -9.2, 19.4, 20.1, -46.3, -40.7, STONE_D, 0.04, name="Cornice")
    for zz in (-41.15, -45.85):
        arch_fill(p, cx, 15.2, 17.4, 1.0, zz, 0.3, IRON, name="BelfryOpen")
    for xx in (-9.65, -14.35):
        arch_side(p, xx, 15.2, 17.4, 1.0, -43.5, 0.3, IRON, name="BelfryOpen")
    dk.cyl(p, (cx, 16.4, -43.5), 0.7, 1.7, GOLD, verts=6, top_radius=0.3, name="Bell")
    cone_roof(p, cx, -43.5, 19.8, 3.3, 7.4, ROOF, ROOF_L, sides=8)
    bx(p, cx - 0.2, cx + 0.2, 27.0, 29.8, -43.7, -43.3, GOLD, 0.02, name="CrossV")
    bx(p, cx - 0.8, cx + 0.8, 28.4, 28.9, -43.7, -43.3, GOLD, 0.02, name="CrossH")
    # front door with rose window and steps
    arch_fill(p, cx, 0.0, 3.4, 1.7, -41.05, 0.4, STONE_L, name="DoorFrame")
    arch_fill(p, cx, 0.0, 3.2, 1.35, -40.85, 0.4, WOOD_D, name="Door")
    for xx in (-12.6, -11.4):
        bx(p, xx - 0.05, xx + 0.05, 0.1, 4.0, -40.6, -40.55, IRON_L, 0.02, name="DoorPlank")
    for yy in (1.2, 3.0):
        bx(p, -13.3, -10.7, yy, yy + 0.25, -40.65, -40.55, IRON, 0.02, name="Hinge")
    dk.cyl(p, (cx, 8.6, -41.1), 1.5, 0.4, STONE_L, axis='z', verts=10, name="RoseFrame")
    dk.cyl(p, (cx, 8.6, -40.9), 1.15, 0.3, ROOF_L, axis='z', verts=10, name="Rose")
    for ang in (0, 60, 120):
        dk.box(p, (cx, 8.6, -40.72), (0.16, 2.3, 0.1), GOLD, rot=(0, 0, ang), name="RoseSpoke")
    bx(p, -14.2, -9.8, 0.0, 0.4, -41.4, -40.4, STONE_D, 0.04, name="Step")
    for xx in (-14.7, -9.3):
        slit(p, xx, 8.0, -43.5, '+x' if xx > -12 else '-x', 0.5, 2.6)
    return p


@part_builder("Lists")
def build_Lists():
    p = dk.Part("Lists")
    bx(p, 62.0, 90.0, 0, 0.4, 18.0, 30.0, SAND, 0.05, name="Arena")
    bx(p, 62.0, 90.0, 0, 0.45, 29.6, 30.0, SAND_D, 0.05, name="ArenaEdge")
    # striped jousting barrier
    bx(p, 63.0, 89.0, 0.3, 0.7, 23.5, 24.5, WOOD_D, 0.04, name="BarrierFoot")
    for k in range(13):
        xa = 63.0 + k * 2.0
        bx(p, xa + 0.03, xa + 1.97, 0.7, 3.0, 23.65, 24.35, RED if k % 2 == 0 else CREAM, 0.04, name="Panel")
    bx(p, 62.8, 89.2, 3.0, 3.6, 23.5, 24.5, WOOD, 0.05, name="BarrierRail")
    for xp in (63.0, 76.0, 89.0):
        bx(p, xp - 0.45, xp + 0.45, 0, 3.9, 23.45, 24.55, WOOD_D, 0.05, name="BarrierPost")
    heater(p, 69.0, 1.9, 24.5, 1.6, 1.9, ROOF, GOLD)
    heater(p, 83.0, 1.9, 24.5, 1.6, 1.9, ROOF, GOLD)
    # tall flag poles at both ends
    for xp, d, col in ((63.5, 1, RED), (88.5, -1, ROOF_L)):
        dk.cyl(p, (xp, 6.0, 24.0), 0.3, 12.0, WOOD_D, verts=5, name="Pole")
        dk.ball(p, (xp, 12.2, 24.0), 0.45, GOLD, subdiv=1, name="Knob")
        pennant(p, xp + d * 0.2, 10.6, 24.0, 4.0, 2.2, col, d)
    # grandstand: three tiers, back fence, striped canopy on posts, royal box with throne
    for k, zt in enumerate((20.0, 19.0, 18.0)):
        bx(p, 64.0, 88.0, 0, 1.0 + k, zt, zt + 1.0, WOOD if k % 2 == 0 else WOOD_L, 0.06, name="Tier")
    bx(p, 63.8, 88.2, 3.0, 5.0, 17.8, 18.1, WOOD_D, 0.05, name="BackFence")
    for xp in (64.4, 70.2, 76.0, 81.8, 87.6):
        box_pole(p, xp, 21.3, 0, 6.5, 0.5, WOOD_D)
        box_pole(p, xp, 17.9, 0, 7.4, 0.5, WOOD_D)
    stripe_canopy(p, 76.0, 19.7, 24.8, 4.8, 7.6, 6.4, ROOF, CREAM, stripes=8, val=0.9)
    bx(p, 74.0, 78.0, 3.0, 3.4, 18.1, 20.4, GOLD_D, 0.04, name="RoyalDais")
    bx(p, 75.0, 77.0, 3.4, 4.3, 18.3, 19.7, GOLD, 0.04, name="Throne")
    bx(p, 75.0, 77.0, 4.3, 6.2, 18.15, 18.55, GOLD, 0.04, name="ThroneBack")
    bx(p, 75.3, 76.7, 3.7, 4.6, 18.55, 19.6, RED, 0.03, name="Cushion")
    for k, xx in enumerate((75.2, 76.0, 76.8)):
        dk.cone(p, (xx, 6.2, 18.35), 0.35, 0.9 if k == 1 else 0.6, GOLD_L, verts=4, name="Crown")
    for xx, col in ((73.2, ROOF), (78.8, ROOF)):
        banner_cloth(p, xx, 6.2, 20.5, 1.8, 3.4, col, GOLD)
    for k, (x, tier, col) in enumerate(((66.5, 1, RED), (69.6, 2, ROOF), (72.5, 3, GOLD_D), (80.0, 3, RED), (83.3, 2, ROOF_L), (85.8, 1, GOLD_D))):
        z = 20.5 - (tier - 1) * 1.0
        bx(p, x - 0.5, x + 0.5, tier, tier + 1.5, z - 0.3, z + 0.3, col, 0.05, name="Spectator")
        dk.ball(p, (x, tier + 2.0, z), 0.5, (236, 190, 150) if k % 2 else (200, 150, 110), subdiv=1, name="Head")
    # lance rack with striped lances
    for xx in (68.4, 73.6):
        bx(p, xx - 0.2, xx + 0.2, 0, 3.2, 28.2, 28.8, WOOD_D, 0.05, name="RackLeg")
    bx(p, 68.2, 73.8, 1.0, 1.3, 28.2, 28.8, WOOD, 0.05, name="RackBar")
    bx(p, 68.2, 73.8, 3.0, 3.3, 28.2, 28.8, WOOD, 0.05, name="RackBar")
    for k in range(4):
        xl = 69.4 + k * 1.4
        mid = (xl + 0.2 * (k - 1.5) * 0.4, 3.6, 28.5)
        top = (xl + 0.4 * (k - 1.5) * 0.3, 7.0, 28.5)
        rod(p, (xl, 0.4, 28.5), mid, 0.16, RED if k % 2 else CREAM, 5, name="Lance")
        rod(p, mid, top, 0.15, CREAM if k % 2 else RED, 5, name="Lance")
        dk.cone(p, (top[0], 7.0, 28.5), 0.2, 0.9, STEEL, verts=4, name="LanceTip")
    return p


@part_builder("Keep")
def build_Keep():
    p = dk.Part("Keep")
    cx, TOP = -60.0, 24.0
    bx(p, -72.6, -47.4, 0, 1.4, -54.6, -33.4, STONE_D, 0.05, name="Plinth")
    stoneblock(p, -72, -48, 1.4, TOP, -54, -34, courses=5, e=0.12)
    bx(p, -72.4, -47.6, 11.6, 12.1, -54.4, -33.6, STONE_D, 0.04, name="StringCourse")
    bx(p, -73, -47, TOP, TOP + 1.4, -55, -33, STONE_D, 0.05, name="Parapet")
    merlon_line(p, 'x', -68.0, -52.0, -33.5, TOP + 1.4, step=3.3, w=1.7, h=1.5, d=1.0)
    merlon_line(p, 'z', -50.0, -38.0, -72.5, TOP + 1.4, step=3.3, w=1.7, h=1.5, d=1.0)
    merlon_line(p, 'z', -50.0, -38.0, -47.5, TOP + 1.4, step=3.3, w=1.7, h=1.5, d=1.0)
    # four round corner turrets with blue roofs and pennants
    for k, (tx, tz) in enumerate(((-72, -54), (-48, -54), (-72, -34), (-48, -34))):
        round_tower(p, tx, tz, 0, 31, 3.2, sides=8, flare=0.4, bands=(16.0,))
        dk.cyl(p, (tx, 31.5, tz), 3.9, 1.0, STONE_D, verts=8, jitter=0.05, name="Corbel")
        cone_roof(p, tx, tz, 32.0, 4.0, 7.0, ROOF, ROOF_L, sides=8)
        dk.cyl(p, (tx, 41.0, tz), 0.14, 4.0, WOOD_D, verts=4, name="FlagPole")
        pennant(p, tx + 0.1, 42.2, tz, 2.6, 1.5, RED if k % 2 == 0 else ROOF_L, 1 if tx < -60 else -1)
        for yy in (9.0, 22.0):
            slit(p, tx, yy, tz + 3.05 if tz > -40 else tz - 3.05, '+z', 0.5, 2.2)
    # central tower with a square pyramid roof, royal flag
    stoneblock(p, -65, -55, TOP + 1.4, 36.4, -51, -41, courses=4, ca=STONE_W, cb=STONE)
    bx(p, -65.7, -54.3, 36.4, 37.2, -51.7, -40.3, STONE_D, 0.04, name="TowerCornice")
    rf = lathe(p, (cx, 0, -46), [(8.3, 37.2), (8.0, 37.6), (0, 45.2)], 4, ROOF, 0.04, rot0=pi / 4, name="Pyramid")
    recolor(rf, lambda c, n, i: ROOF_L if (n[1] > 0.2 and int(round(math.atan2(c[2] + 46, c[0] - cx) / (pi / 2))) % 2 == 0) else None, 0.04)
    dk.cyl(p, (cx, 46.9, -46), 0.2, 3.6, WOOD_D, verts=4, name="RoyalPole")
    dk.ball(p, (cx, 48.8, -46), 0.4, GOLD, subdiv=1, name="Knob")
    slab(p, [(cx + 0.1, 48.2), (cx + 5.0, 48.2), (cx + 4.0, 47.0), (cx + 5.0, 45.8), (cx + 0.1, 45.8)], 0.16, 'xy', -46, RED, 0.03, name="RoyalFlag")
    diamond(p, cx + 2.0, 47.0, -46, 1.4, 1.6, GOLD, 0.26)
    for zz in (-41.05,):
        for xx in (-62.4, -57.6):
            arch_fill(p, xx, 29.0, 31.4, 0.8, zz, 0.3, IRON, segs=3, name="TowerWin")
    # facade: heavy door with portcullis, coat of arms, windows, banners, steps
    arch_fill(p, cx, 0.0, 5.4, 3.0, -33.95, 0.4, STONE_L, name="DoorFrame")
    arch_fill(p, cx, 0.0, 5.0, 2.55, -33.7, 0.4, WOOD_D, name="Door")
    for k in range(4):
        xx = -62.0 + k * 1.33
        bx(p, xx - 0.12, xx + 0.12, 0.2, 7.2, -33.55, -33.4, IRON_L, 0.02, name="DoorPlank")
    for yy in (1.8, 4.4):
        bx(p, -62.5, -57.5, yy, yy + 0.35, -33.58, -33.42, IRON, 0.02, name="Hinge")
    dk.ball(p, (cx - 0.7, 3.2, -33.4), 0.28, GOLD, subdiv=1, name="Ring")
    dk.ball(p, (cx + 0.7, 3.2, -33.4), 0.28, GOLD, subdiv=1, name="Ring")
    heater(p, cx, 14.2, -33.8, 5.0, 6.0, RED, GOLD, thick=0.4)
    for xx in (-65.5, -54.5):
        for yy in (9.5, 17.5):
            arch_fill(p, xx, yy, yy + 2.0, 1.0, -33.9, 0.3, STONE_L, segs=3, name="WinFrame")
            arch_fill(p, xx, yy + 0.2, yy + 2.0, 0.7, -33.7, 0.3, ROOF_L if yy > 12 else IRON, segs=3, name="Win")
    for xx in (-69.0, -51.0):
        banner_cloth(p, xx, 21.5, -33.75, 3.0, 8.0, ROOF if xx < -60 else RED, GOLD)
    bx(p, -64.5, -55.5, 0, 0.6, -33.0, -30.8, STONE_D, 0.05, name="Step")
    bx(p, -63.5, -56.5, 0.6, 1.2, -33.0, -31.8, STONE, 0.05, name="Step")
    for xx in (-66.0, -54.0):
        torch_stand(p, xx, -31.6, 3.4, full=False)
    return p


@part_builder("Windmill")
def build_Windmill():
    p = dk.Part("Windmill")
    cx, cz = 80.0, -54.0
    # stone mill house with a flat deck, round plastered tower above
    stoneblock(p, 74, 86, 0, 5.4, -59, -49, courses=4, ca=STONE, cb=STONE_W)
    bx(p, 73.7, 86.3, 5.4, 6.0, -59.3, -48.7, STONE_D, 0.05, name="Deck")
    bx(p, 73.7, 86.3, 6.0, 6.7, -48.9, -48.5, STONE_L, 0.04, name="Parapet")
    bx(p, 73.7, 74.1, 6.0, 6.7, -59.3, -48.7, STONE_L, 0.04, name="Parapet")
    bx(p, 85.9, 86.3, 6.0, 6.7, -59.3, -48.7, STONE_L, 0.04, name="Parapet")
    lathe(p, (cx, 0, cz), [(4.7, 6.0), (3.6, 20.0)], 8, CREAM, 0.05, rot0=pi / 8, name="Tower")
    for yb in (10.0, 15.0):
        rr = 4.7 - (yb - 6.0) * 1.1 / 14.0 + 0.2
        dk.cyl(p, (cx, yb, cz), rr, 0.5, STONE_D, verts=8, jitter=0.04, name="Band", rot=(0, 22.5, 0))
    dk.cyl(p, (cx, 20.3, cz), 4.2, 0.7, WOOD_D, verts=8, rot=(0, 22.5, 0), name="CapBase")
    cone_roof(p, cx, cz, 20.6, 4.6, 3.8, ROOF, ROOF_L, sides=8)
    dk.ball(p, (cx, 24.6, cz), 0.45, GOLD, subdiv=1, name="Knob")
    for yy in (12.0, 17.0):
        bx(p, cx - 0.7, cx + 0.7, yy, yy + 1.7, cz + 3.55 - 0.4 * (yy - 12) / 5, cz + 3.95 - 0.4 * (yy - 12) / 5, IRON, 0.03, name="TowerWin")
    # door, steps, sacks, barrel
    arch_fill(p, cx, 0.0, 3.0, 1.7, -48.8, 0.3, STONE_L, name="DoorFrame")
    arch_fill(p, cx, 0.0, 2.9, 1.3, -48.6, 0.3, WOOD_D, name="Door")
    for xx in (79.6, 80.4):
        bx(p, xx - 0.05, xx + 0.05, 0.1, 3.6, -48.45, -48.4, IRON_L, 0.02, name="DoorPlank")
    bx(p, 77.8, 82.2, 0, 0.35, -49.0, -47.8, STONE_D, 0.05, name="Step")
    for k, (xx, col) in enumerate(((75.6, CREAM), (77.2, CREAM), (84.4, HAY))):
        bx(p, xx - 0.65, xx + 0.65, 0, 1.7, -48.9 + 0.1 * k - 0.5, -48.9 + 0.1 * k + 0.5, col, 0.07, name="Sack")
        dk.cone(p, (xx, 1.7, -48.4 + 0.1 * k), 0.45, 0.6, col, verts=5, name="SackTop")
        bx(p, xx - 0.7, xx + 0.7, 1.2, 1.35, -48.95 + 0.1 * k - 0.5, -48.95 + 0.1 * k + 0.5, RED, 0.03, name="SackTie")
    barrel(p, 85.0, 0.0, -48.2, 0.9, 2.0)
    # sail shaft, hub and the four big sails
    hub = (cx, 19.5)
    dk.cyl(p, (cx, 19.5, -49.0), 0.75, 3.2, WOOD_D, axis='z', verts=6, name="Shaft")
    dk.cyl(p, (cx, 19.5, -48.0), 1.3, 0.8, IRON, axis='z', verts=8, name="Hub")
    dk.ball(p, (cx, 19.5, -47.5), 0.6, GOLD, subdiv=1, name="Spinner")

    def R2(th, u, v):
        a = math.radians(th)
        return (hub[0] + u * math.cos(a) - v * math.sin(a), hub[1] + u * math.sin(a) + v * math.cos(a))

    def rect(th, u0, u1, v0, v1, thick, zc, col, name):
        slab(p, [R2(th, u0, v0), R2(th, u1, v0), R2(th, u1, v1), R2(th, u0, v1)], thick, 'xy', zc, col, 0.04, name=name)
    for th in (35, 125, 215, 305):
        rect(th, 0.9, 9.6, -0.28, 0.28, 0.5, -47.65, WOOD_D, "Spar")
        rect(th, 2.0, 9.6, 2.35, 2.75, 0.4, -47.9, WOOD, "SailBar")
        rect(th, 9.2, 9.6, 0.2, 2.75, 0.4, -47.9, WOOD, "SailTip")
        for k, col in enumerate((RED, CREAM, RED)):
            ua = 2.0 + k * 2.4
            rect(th, ua, ua + 2.3, 0.28, 2.4, 0.16, -47.95, col, "Cloth")
    return p


@part_builder("RoundTable")
def build_RoundTable():
    p = dk.Part("RoundTable")
    cx, cz = 44.0, 24.0
    # stepped round dais
    lathe(p, (cx, 0, cz), [(8.2, 0), (8.2, 0.5), (7.6, 0.5), (7.6, 1.0)], 12, STONE_D, 0.05, name="Dais")
    dk.cyl(p, (cx, 1.05, cz), 6.9, 0.2, STONE_L, verts=12, jitter=0.05, name="Floor")
    # six pillars carrying a ring beam
    for k in range(6):
        a = 2 * pi * k / 6 + pi / 6
        px, pz = cx + 7.0 * math.cos(a), cz + 7.0 * math.sin(a)
        bx(p, px - 0.8, px + 0.8, 1.0, 1.6, pz - 0.8, pz + 0.8, STONE_D, 0.05, name="Base")
        dk.cyl(p, (px, 5.6, pz), 0.6, 8.0, STONE, verts=6, jitter=0.05, name="Pillar")
        bx(p, px - 0.8, px + 0.8, 9.6, 10.3, pz - 0.8, pz + 0.8, STONE_L, 0.04, name="Capital")
    dk.cyl(p, (cx, 10.0, cz), 8.0, 0.8, STONE_D, verts=12, jitter=0.04, name="RingBeam")
    # the roof: blue cone with a golden eave band and finial
    rf = lathe(p, (cx, 0, cz), [(8.5, 10.4), (8.5, 11.2), (5.2, 13.6), (2.4, 15.2), (0, 16.0)], 12, ROOF, 0.04, name="Roof")
    recolor(rf, lambda c, n, i: GOLD if (c[1] < 11.3 and abs(n[1]) < 0.5) else (ROOF_L if (n[1] > 0.1 and int(((math.atan2(c[2] - cz, c[0] - cx) % (2 * pi)) / (2 * pi / 12))) % 2) else None), 0.04)
    lathe(p, (cx, 15.4, cz), [(1.0, 0), (1.1, 0.8), (0.5, 1.6), (0.0, 2.0)], 8, GOLD, 0.03, name="Finial")
    dk.cyl(p, (cx, 17.9, cz), 0.16, 2.4, GOLD_D, verts=4, name="Spire")
    pennant(p, cx + 0.1, 18.2, cz, 3.0, 1.6, RED, 1)
    # the round table: pedestal, wooden top with golden rim, red centre
    dk.cyl(p, (cx, 1.9, cz), 1.5, 2.0, WOOD_D, verts=8, top_radius=1.0, name="Pedestal")
    dk.cyl(p, (cx, 1.1, cz), 2.6, 0.3, WOOD_D, verts=8, name="PedestalFoot")
    tp = lathe(p, (cx, 2.5, cz), [(4.6, 0), (4.7, 0.5), (4.5, 1.0), (0, 1.0)], 12, WOOD, 0.04, name="TableTop")
    recolor(tp, lambda c, n, i: (WOOD_L if int(((math.atan2(c[2] - cz, c[0] - cx) % (2 * pi)) / (2 * pi / 12))) % 2 else WOOD) if n[1] > 0.5 else None, 0.04)
    dk.cyl(p, (cx, 3.55, cz), 1.7, 0.1, RED, verts=10, name="Cloth")
    dk.cyl(p, (cx, 3.62, cz), 1.1, 0.1, GOLD, verts=10, name="Medallion")
    for k in range(4):
        a = pi / 4 + k * pi / 2
        gx, gz = cx + 3.4 * math.cos(a), cz + 3.4 * math.sin(a)
        dk.cyl(p, (gx, 4.1, gz), 0.28, 1.1, GOLD, verts=6, top_radius=0.42, name="Goblet")
    rod(p, (cx - 1.4, 3.7, cz + 0.9), (cx + 1.6, 3.7, cz - 0.2), 0.12, STEEL, 4, name="Sword")
    # four high-backed chairs facing the table
    for (dx, dz, fx, fz) in ((6.4, 0, -1, 0), (-6.4, 0, 1, 0), (0, 6.4, 0, -1), (0, -6.4, 0, 1)):
        gx, gz = cx + dx * 0.78, cz + dz * 0.78
        bk = (-fx * 0.8, -fz * 0.8)
        bx(p, gx - 0.9, gx + 0.9, 1.0, 2.4, gz - 0.9, gz + 0.9, WOOD_D, 0.05, name="ChairSeat")
        bx(p, gx - 0.75, gx + 0.75, 2.4, 2.8, gz - 0.75, gz + 0.75, RED, 0.04, name="Cushion")
        if fx:
            bx(p, gx + bk[0] - 0.2, gx + bk[0] + 0.2, 2.4, 5.6, gz - 0.9, gz + 0.9, WOOD_D, 0.05, name="ChairBack")
            dk.ball(p, (gx + bk[0], 5.9, gz - 0.7), 0.3, GOLD, subdiv=1, name="Finial")
            dk.ball(p, (gx + bk[0], 5.9, gz + 0.7), 0.3, GOLD, subdiv=1, name="Finial")
        else:
            bx(p, gx - 0.9, gx + 0.9, 2.4, 5.6, gz + bk[1] - 0.2, gz + bk[1] + 0.2, WOOD_D, 0.05, name="ChairBack")
            dk.ball(p, (gx - 0.7, 5.9, gz + bk[1]), 0.3, GOLD, subdiv=1, name="Finial")
            dk.ball(p, (gx + 0.7, 5.9, gz + bk[1]), 0.3, GOLD, subdiv=1, name="Finial")
    return p


@part_builder("Trebuchet")
def build_Trebuchet():
    p = dk.Part("Trebuchet")
    # base frame
    for zz in (-33.0, -23.0):
        bx(p, 68.0, 88.0, 0, 1.4, zz - 0.6, zz + 0.6, WOOD_D, 0.06, name="Skid")
    for xx in (72.0, 84.0):
        bx(p, xx - 0.6, xx + 0.6, 0, 1.4, -33.6, -22.4, WOOD_D, 0.06, name="Cross")
    # two A-frames and the axle
    for zz in (-32.4, -23.6):
        rod(p, (72.5, 1.0, zz), (78.0, 15.0, zz), 0.55, WOOD, 4, name="Leg")
        rod(p, (83.5, 1.0, zz), (78.0, 15.0, zz), 0.55, WOOD, 4, name="Leg")
        bx(p, 74.4, 81.6, 4.6, 5.2, zz - 0.35, zz + 0.35, WOOD_D, 0.05, name="Brace")
        bx(p, 77.0, 79.0, 14.4, 15.8, zz - 0.5, zz + 0.5, IRON, 0.03, name="Bearing")
    dk.cyl(p, (78.0, 15.0, -28.0), 0.65, 11.2, IRON_L, axis='z', verts=6, name="Axle")
    # throwing arm: heavy short end, slim long end, with iron bands
    A, M, B = (71.7, 12.0, -28.0), (78.0, 15.0, -28.0), (89.6, 20.4, -28.0)
    beam(p, A, M, 1.5, WOOD, 1.5, 0.06, name="ArmShort")
    beam(p, M, (84.4, 17.7, -28.0), 1.4, WOOD_L, 1.4, 0.06, name="ArmLong")
    beam(p, (84.4, 17.7, -28.0), B, 0.9, WOOD_L, 0.9, 0.06, name="ArmTip")
    for t in (0.35, 0.7):
        dk.box(p, (M[0] + (B[0] - M[0]) * t * 0.7, M[1] + (B[1] - M[1]) * t * 0.7, -28.0), (0.5, 1.9, 1.9), IRON, rot=(0, 0, 25), name="ArmBand")
    # counterweight box swinging from the short end, with a heraldic shield
    for zz in (-30.4, -25.6):
        rod(p, (71.7, 12.0, zz), (71.7, 10.2, zz), 0.2, IRON, 4, name="Hanger")
    bx(p, 69.1, 74.3, 5.8, 10.2, -30.6, -25.4, STONE_L, 0.07, name="Weight")
    bx(p, 68.9, 74.5, 5.6, 6.3, -30.8, -25.2, IRON, 0.03, name="WeightBand")
    bx(p, 68.9, 74.5, 9.7, 10.4, -30.8, -25.2, IRON, 0.03, name="WeightBand")
    heater(p, 71.7, 8.1, -25.0, 2.6, 3.0, RED, GOLD)
    # sling with a loaded boulder at the tip
    rod(p, (89.6, 20.4, -28.0), (90.5, 17.4, -28.6), 0.1, WOOD_L, 4, name="SlingRope")
    rod(p, (89.6, 20.4, -28.0), (90.5, 17.4, -27.4), 0.1, WOOD_L, 4, name="SlingRope")
    rock(p, (90.5, 16.6, -28.0), 1.3, STONE, scale=(1, 0.9, 1), jitter=0.1, name="Shot")
    # winch with a crank wheel, boulder pile, red pennant on a mast
    dk.cyl(p, (84.0, 3.2, -32.1), 2.4, 0.5, WOOD_D, axis='z', verts=10, name="WheelRim")
    dk.cyl(p, (84.0, 3.2, -32.1), 1.9, 0.6, WOOD, axis='z', verts=10, name="WheelFace")
    dk.cyl(p, (84.0, 3.2, -32.1), 0.5, 1.0, IRON, axis='z', verts=6, name="WheelHub")
    for ang in (0, 60, 120):
        dk.box(p, (84.0, 3.2, -31.75), (4.2, 0.4, 0.3), WOOD_D, rot=(0, 0, ang), name="Spoke")
    dk.cyl(p, (84.0, 3.2, -28.0), 0.45, 8.8, WOOD_D, axis='z', verts=6, name="Windlass")
    for (x, z, r) in ((86.0, -29.4, 1.3), (88.2, -26.8, 1.1), (86.6, -26.4, 1.0), (87.8, -30.0, 0.9)):
        rock(p, (x, r * 0.55 + 0.1, z), r, STONE, scale=(1, 0.8, 1), rot=(0, R.uniform(0, 90), 0), jitter=0.12, name="Boulder")
    dk.cyl(p, (78.0, 18.0, -22.6), 0.2, 6.0, WOOD_D, verts=4, name="Mast")
    pennant(p, 78.2, 19.9, -22.6, 3.6, 2.0, RED, 1)
    return p


@part_builder("Excalibur")
def build_Excalibur():
    p = dk.Part("Excalibur")
    cx, cz = -12.0, -17.0
    boulder(p, cx, 0, cz, 6.4, 6.0, 6.4, STONE, sides=9, wob=0.2, top=0.5, name="Rock")
    boulder(p, -14.4, 0, -13.4, 3.2, 3.8, 3.0, STONE, sides=7, name="Rock")
    boulder(p, -8.2, 0, -13.2, 2.6, 3.0, 2.6, STONE_W, sides=7, name="Rock")
    boulder(p, -18.0, 0, -20.0, 1.3, 1.6, 1.3, STONE, sides=6, name="Rock")
    boulder(p, -6.0, 0, -21.0, 1.3, 1.5, 1.3, STONE_W, sides=6, name="Rock")
    boulder(p, -16.0, 0, -22.0, 1.6, 1.8, 1.6, STONE, sides=6, name="Rock")
    # stone steps in front
    bx(p, -16.0, -8.0, 0, 0.9, -11.6, -10.2, STONE_L, 0.05, name="Step")
    bx(p, -17.4, -6.6, 0, 0.5, -10.2, -8.9, STONE, 0.05, name="Step")
    # the sword: blade with fuller and golden runes, crossguard, wrapped grip, pommel with a gem
    slab(p, [(cx - 0.9, 5.4), (cx + 0.9, 5.4), (cx + 0.9, 24.0), (cx - 0.9, 24.0)], 0.5, 'xy', cz, STEEL, 0.03, name="Blade")
    bx(p, cx - 0.2, cx + 0.2, 6.6, 23.6, cz + 0.24, cz + 0.3, STEEL_D, 0.0, name="Fuller")
    bx(p, cx - 0.2, cx + 0.2, 6.6, 23.6, cz - 0.3, cz - 0.24, STEEL_D, 0.0, name="Fuller")
    bx(p, cx - 0.95, cx - 0.7, 6.0, 24.0, cz - 0.26, cz + 0.26, WHITE, 0.02, name="Edge")
    bx(p, cx + 0.7, cx + 0.95, 6.0, 24.0, cz - 0.26, cz + 0.26, WHITE, 0.02, name="Edge")
    for yy in (10.5, 14.0, 17.5, 21.0):
        diamond(p, cx, yy, cz, 0.5, 1.0, GOLD, 0.62, name="Rune")
    slab(p, [(cx - 3.6, 25.9), (cx - 3.3, 24.9), (cx - 1.0, 24.1), (cx + 1.0, 24.1), (cx + 3.3, 24.9), (cx + 3.6, 25.9),
             (cx + 1.2, 25.3), (cx - 1.2, 25.3)], 1.0, 'xy', cz, GOLD, 0.03, name="Crossguard")
    dk.ball(p, (cx, 24.9, cz + 0.62), 0.4, RED_L, subdiv=1, name="Gem")
    dk.cyl(p, (cx, 27.0, cz), 0.42, 3.4, WOOD_D, verts=6, name="Grip")
    for yy in (25.8, 26.6, 27.4, 28.2):
        dk.cyl(p, (cx, yy, cz), 0.5, 0.22, GOLD_D, verts=6, name="Wrap")
    dk.ball(p, (cx, 29.4, cz), 0.95, GOLD, subdiv=1, name="Pommel")
    dk.ball(p, (cx, 29.4, cz + 0.8), 0.32, RED_L, subdiv=1, name="PommelGem")
    # drifting golden sparkles around the hilt
    for (dx, yy, dz, s) in ((-3.4, 21.0, 1.2, 1.0), (3.2, 23.0, -0.8, 0.8), (-2.2, 27.4, -1.2, 0.7), (2.6, 28.4, 1.4, 0.9), (-4.0, 25.4, -0.6, 0.6)):
        diamond(p, cx + dx, yy, cz + dz, s * 0.7, s * 1.3, GOLD_L, 0.3, name="Sparkle")
    # vines, tufts and flowers at the foot
    for k, (x, z) in enumerate(((-18.4, -17.0), (-5.8, -16.5), (-13.0, -23.2))):
        rod(p, (x, 0.4, z), (x * 0.9 + cx * 0.1, 4.4, z * 0.95 + cz * 0.05), 0.14, HEDGE_D, 4, name="Vine")
        for j in range(3):
            dk.ball(p, (x * 0.96 + cx * 0.04, 1.4 + j * 1.2, z * 0.98 + cz * 0.02), 0.32, HEDGE if j % 2 else HEDGE_L, subdiv=1, name="VineLeaf")
    for k, (x, z) in enumerate(((-18.8, -14.5), (-6.0, -10.8), (-18.4, -10.4), (-10.0, -22.8), (-19.0, -18.4), (-5.0, -18.0))):
        dk.cone(p, (x, 0.0, z), 0.5, 1.0, mix(GRASS_D, GRASS_L, (k % 3) / 2), verts=5, jitter=0.08, name="Tuft")
        dk.ball(p, (x + 0.5, 1.0, z + 0.2), 0.28, (WHITE, GOLD_L, (236, 130, 170))[k % 3], subdiv=1, name="Flower")
    return p


# ---- pipeline ----------------------------------------------------------------------------------------------------
def camera(target, distance, az, el, top=False, ortho=None):
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    a, e = math.radians(az), math.radians(el)
    pos = target + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * distance
    cam.location = pos
    cam.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler()
    if top:
        cam.rotation_euler = (0.0, 0.0, math.pi)          # straight down, road at the bottom, +x to the right
    cam_data.lens = 40
    cam_data.clip_start = distance * 0.2
    cam_data.clip_end = distance * 5
    if ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = ortho
    bpy.context.scene.camera = cam
    return cam


def mirror_spot(spot):
    """Stage-frame Shiba spot -> the frame of the exported (x mirrored) meshes."""
    if not spot:
        return None
    x, z = spot["Position"]
    return {"Shiba": {"Position": [-x, z], "Facing": 180 - spot["Facing"]}}


def view(objs, filename, shiba=None, az=215, el=34, size=(1400, 1000), top=False, zoom=2.6, extra=()):
    """Renders the (exported, x mirrored) meshes the way the player sees them: from the road (+z) with +x to the right."""
    sh = dk.add_reference_shiba(shiba, 7.5) if shiba else []
    low, high = dk._bounds(list(objs) + sh + list(extra))
    g = dk.ground(low, high)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 6)
    if top:
        cam = camera(centre + Vector((0, 0, 50)), 900, 180, 90, top=True, ortho=max(high.x - low.x, (high.y - low.y) * size[0] / size[1]) * 1.06)
    else:
        cam = camera(centre, radius * zoom, az, el)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.filepath = os.path.join(dk.OUT, filename)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in sh:
        bpy.data.objects.remove(o, do_unlink=True)
    print("RENDERED", sc.render.filepath)


def stack_images(out, a, b, dst):
    ia = bpy.data.images.load(os.path.join(out, a))
    ib = bpy.data.images.load(os.path.join(out, b))
    w = max(ia.size[0], ib.size[0])
    h = ia.size[1] + ib.size[1]
    import numpy as np
    pa = np.array(ia.pixels[:], dtype=np.float32).reshape(ia.size[1], ia.size[0], 4)
    pb = np.array(ib.pixels[:], dtype=np.float32).reshape(ib.size[1], ib.size[0], 4)
    canvas = np.ones((h, w, 4), dtype=np.float32)
    canvas[:ib.size[1], :ib.size[0]] = pb            # image rows are bottom-up: top view goes at the bottom
    canvas[ib.size[1]:, :ia.size[0]] = pa
    im = bpy.data.images.new("stack", w, h)
    im.pixels.foreach_set(canvas.ravel())
    im.filepath_raw = os.path.join(out, dst)
    im.file_format = 'PNG'
    im.save()


def main():
    a = dk.args()
    out = os.path.abspath(a[0]) if a else os.path.join(HERE, "out", KEY)
    dk.start(out)
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_KnightCastle.json"))
    for part in bp["Parts"]:
        if part["Id"] != "Ground":
            FOOT[part["Id"]] = roblox_box(part["Pieces"])
    ids = [pp["Id"] for pp in bp["Parts"]]
    assert ONLY or ids == [pid for pid, _ in BUILDERS], "builders and blueprint parts differ: %s vs %s" % (ids, [pid for pid, _ in BUILDERS])
    stats = []
    allm = []
    for pid, fn in BUILDERS:
        if ONLY and pid not in ONLY:
            continue
        part = fn()
        box = roblox_box(dk.blueprint_part(bp, pid)["Pieces"])
        drop_ground_faces(part)
        fit(part, box)
        meshes = dk.finish(part, KEY)
        tris = sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)
        stats.append((pid, len(meshes), tris))
        lo, hi = true_bounds(meshes)             # x of the mirrored meshes
        if pid == "Ground":
            view(meshes, f"preview_{pid}.png", shiba=mirror_spot(bp["Shiba"]), az=190, el=38, zoom=2.0)
        else:
            spot = {"Shiba": {"Position": [lo[0] - 6.5, (lo[2] + hi[2]) / 2], "Facing": 0}}
            view(meshes, f"preview_{pid}.png", shiba=spot)
        if DBG:
            for k, az in enumerate((150, 215, 330)):
                o2 = dk.OUT
                dk.OUT = DBG
                view(meshes, f"dbg_{pid}_{k}.png", shiba=None, az=az, el=24)
                dk.OUT = o2
        allm += meshes
        dk.hide(meshes)
    if not ONLY:
        dk.hide(allm, False)
        spot = mirror_spot(bp["Shiba"])
        view(allm, "stage_KnightCastle_34.png", shiba=spot, az=205, el=40, size=(1800, 1000), zoom=1.55)
        view(allm, "stage_KnightCastle_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_KnightCastle_34.png", "stage_KnightCastle_top.png", "stage_KnightCastle.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
