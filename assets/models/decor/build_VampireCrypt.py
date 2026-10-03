"""Vampire Crypt decor models (theme VampireCrypt): builds the 25 decor parts around the eighteenth Shiba (Vampire Shiba).

Run:  blender --background --factory-startup --python build_VampireCrypt.py -- <outdir>   (use an absolute outdir)
Writes into <outdir> (default: out/VampireCrypt next to this script):
  Decor_VampireCrypt_<PartId>.fbx, preview_<PartId>.png per part, stage_VampireCrypt.png (3/4 view + top view stacked),
  stage_VampireCrypt_34.png and stage_VampireCrypt_top.png (the two views separately).
Every model is built in the stage frame (see decorkit.py) and, before export, fitted to the union box of its blueprint pieces so that
the game's fitToPieces scale stays about 1. Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures,
no neon (candles, lanterns, blood and the moon are plain coloured blocks). Previews are rendered the way the player sees the stage:
from the road (+z) with +x to the right.
Env: VC_ONLY=Part1,Part2 builds only those parts; VC_DBG=<folder> adds extra debug views of each part.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "VampireCrypt"
R = random.Random(18)
pi = math.pi
DBG = os.environ.get("VC_DBG")
ONLY = set(os.environ.get("VC_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
NIGHT = (44, 64, 58); NIGHT_L = (62, 90, 72); NIGHT_D = (34, 50, 46)
COB = (96, 94, 110); COB_L = (126, 124, 142); COB_D = (70, 68, 84)
STONE = (116, 114, 130); STONE_L = (152, 150, 168); STONE_D = (78, 76, 94)
BLACK = (36, 34, 46); BLACK_L = (58, 54, 72)
PURP = (86, 58, 122); PURP_L = (124, 90, 162); PURP_D = (58, 38, 84)
CRIM = (160, 26, 46); BLOOD = (200, 34, 54); BLOOD_D = (118, 18, 36)
BONE = (232, 224, 206); BONE_D = (194, 184, 160)
IRON = (40, 40, 50); IRON_L = (78, 78, 94)
WOOD = (88, 58, 44); WOOD_D = (60, 40, 32); WOOD_L = (124, 88, 62)
GOLD = (214, 172, 66); GOLD_D = (166, 124, 40)
MOON = (240, 236, 208); MOON_D = (204, 198, 168)
DIRT = (78, 60, 50); DIRT_L = (106, 84, 66)
HEDGE = (36, 74, 54); HEDGE_L = (54, 102, 72); HEDGE_D = (26, 56, 42)
GREEN = (126, 206, 126); GREEN_D = (72, 152, 88)
FLAME = (255, 198, 92); FLAME_R = (238, 124, 62)
GLASS = (112, 84, 168); GLASS_L = (170, 150, 214); GLASS_D = (66, 46, 108)
FOG = (176, 184, 204)


# colours used as defaults by the shared helpers below
TURF_D = HEDGE_D; TURF_L = HEDGE_L; TIM = WOOD; TIM_D = WOOD_D; TIM_L = WOOD_L; STEEL = IRON_L

DARK = (62, 60, 76)
WALL = (56, 52, 74); ROOF = (84, 60, 120); ROOF_L = (110, 82, 150)
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
        part.id, sc[0], sc[1], sc[2], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]) + "   TARGET x[%.1f %.1f] y[%.1f %.1f] z[%.1f %.1f]" % (tlo[0], thi[0], tlo[1], thi[1], tlo[2], thi[2]))
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




# ---- more helpers for this theme -----------------------------------------------------------------------------------
def turn(objs, cx, cz, deg):
    """Turns objects about the vertical axis through stage (cx, cz). deg 0 = unchanged; a model built facing +z faces +x with -90,
    -x with +90 and -z with 180."""
    a = math.radians(deg)
    M = Matrix.Translation(Vector((cx, cz, 0))) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation(Vector((-cx, -cz, 0)))
    for o in objs:
        o.matrix_world = M @ o.matrix_world


def arch_curve(u0, h, y0, H, n=5):
    """Pointed arch outline from the left springing (u0 - h, y0) over the apex (u0, y0 + H) to the right springing: (u, y) list."""
    k = (H * H - h * h) / (2 * h)
    cu, rr = u0 + k, h + k
    tha = math.atan2(H, -k)
    left = []
    for i in range(n + 1):
        t = pi + (tha - pi) * i / n
        left.append((cu + rr * math.cos(t), y0 + rr * math.sin(t)))
    right = [(2 * u0 - u, y) for (u, y) in reversed(left[:-1])]
    return left + right


def lancet(p, plane, u, y0, y1, w, at, thick, color, jitter=0.0, ah=None, n=4, name="Lancet"):
    """Window / door shape with a pointed top: width w, from y0 up to y1. plane 'xy': centred on x = u, thickness along z around
    `at`; plane 'yz': centred on z = u, thickness along x."""
    H = ah if ah is not None else w * 0.85
    pts = [(u - w / 2, y0)] + arch_curve(u, w / 2, y1 - H, H, n) + [(u + w / 2, y0)]
    if plane == 'xy':
        return slab(p, pts, thick, 'xy', at, color, jitter, name=name)
    return slab(p, [(y, uu) for uu, y in pts], thick, 'yz', at, color, jitter, name=name)


def arch_band(p, plane, u0, h, y0, H, t, at, thick, color, jitter=0.0, n=6, name="ArchBand"):
    """Pointed arch ring: inner outline half-span h / height H, band thickness t."""
    inner = arch_curve(u0, h, y0, H, n)
    outer = arch_curve(u0, h + t, y0, H + t * 0.9, n)
    pts = outer + list(reversed(inner))
    if plane == 'xy':
        return slab(p, pts, thick, 'xy', at, color, jitter, name=name)
    return slab(p, [(y, uu) for uu, y in pts], thick, 'yz', at, color, jitter, name=name)


def spire4(p, x, y0, z, half, h, color, jitter=0.05, name="Spire"):
    """Square pyramid (axis aligned) with half-width `half` at the base."""
    return lathe(p, (x, y0, z), [(half * 1.4142, 0), (0, h)], 4, color, jitter, rot0=pi / 4, name=name)


def flame(p, x, y0, z, r, h, col=FLAME, name="Flame"):
    return dk.cone(p, (x, y0, z), r, h, col, verts=4, jitter=0.04, name=name)


def candle(p, x, y0, z, h=1.0, r=0.22, col=BONE):
    dk.cyl(p, (x, y0 + h / 2, z), r, h, col, verts=5, jitter=0.04, name="Candle")
    flame(p, x, y0 + h, z, r * 0.9, r * 2.6)


def skull(p, x, y, z, s=1.0, ang=0, detail=1):
    """A skull facing +z (turned by ang), centre (x, y, z), about 1 s wide."""
    n0 = len(p.objs)
    if detail:
        blob(p, (x, y, z), 0.5 * s, BONE, sy=0.9, sides=6, jitter=0.04, name="Skull")
        bx(p, x - 0.28 * s, x + 0.28 * s, y - 0.55 * s, y - 0.28 * s, z + 0.02 * s, z + 0.42 * s, BONE_D, 0.03, name="Jaw")
        for sg in (-1, 1):
            bx(p, x + sg * 0.2 * s - 0.11 * s, x + sg * 0.2 * s + 0.11 * s, y - 0.08 * s, y + 0.14 * s, z + 0.36 * s, z + 0.5 * s, IRON, 0, name="Eye")
    else:
        bx(p, x - 0.46 * s, x + 0.46 * s, y - 0.4 * s, y + 0.4 * s, z - 0.4 * s, z + 0.4 * s, BONE, 0.07, name="Skull")
        bx(p, x - 0.34 * s, x + 0.34 * s, y - 0.12 * s, y + 0.14 * s, z + 0.39 * s, z + 0.43 * s, IRON, 0, name="Eyes")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def gargoyle(p, x, y0, z, s=1.0, ang=0, col=STONE, wing=BLACK_L):
    """A crouching winged gargoyle (about 3.6 s tall incl. wings, 5 s wide) standing at (x, y0, z), facing +z turned by ang."""
    n0 = len(p.objs)

    def X(a): return x + a * s
    def Y(a): return y0 + a * s
    def Z(a): return z + a * s
    blob(p, (X(0), Y(1.0), Z(-0.1)), 0.85 * s, col, sy=0.9, sides=6, jitter=0.06, name="GBody")
    bx(p, X(-0.55), X(0.55), Y(0.5), Y(1.7), Z(0.1), Z(0.95), col, 0.05, name="GChest")
    bx(p, X(-0.5), X(0.5), Y(1.55), Y(2.35), Z(0.55), Z(1.4), STONE_L if col == STONE else col, 0.05, name="GHead")
    bx(p, X(-0.28), X(0.28), Y(1.55), Y(1.95), Z(1.4), Z(1.95), col, 0.05, name="GSnout")
    for sg in (-1, 1):
        dk.cone(p, (X(sg * 0.38), Y(2.3), Z(0.8)), 0.14 * s, 0.7 * s, BONE_D, verts=4, name="GHorn")
        bx(p, X(sg * 0.3 - 0.1), X(sg * 0.3 + 0.1), Y(1.95), Y(2.15), Z(1.38), Z(1.5), BLOOD, 0, name="GEye")
        bx(p, X(sg * 0.5 - 0.17), X(sg * 0.5 + 0.17), Y(0), Y(1.05), Z(0.7), Z(1.1), col, 0.05, name="GArm")
        bx(p, X(sg * 0.7 - 0.2), X(sg * 0.7 + 0.2), Y(0), Y(0.7), Z(-0.55), Z(0.4), col, 0.05, name="GLeg")
        pts = [(0.3, 1.3), (0.5, 2.8), (1.4, 3.7), (2.6, 3.3), (2.0, 2.6), (2.5, 1.9), (1.7, 1.6), (1.4, 0.9)]
        slab(p, [(X(sg * a), Y(b)) for a, b in pts][::sg], 0.14 * s, 'xy', Z(-0.5), wing, 0.05, name="GWing")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def bat(p, x, y, z, s=1.0, ang=0, col=IRON, flat=False):
    """A little bat with spread wings, facing +z turned by ang (centre of the body at (x, y, z), wingspan 4 s)."""
    n0 = len(p.objs)
    bx(p, x - 0.3 * s, x + 0.3 * s, y - 0.4 * s, y + 0.3 * s, z - 0.3 * s, z + 0.3 * s, col, 0.05, name="BatBody")
    bx(p, x - 0.25 * s, x + 0.25 * s, y + 0.15 * s, y + 0.55 * s, z + 0.1 * s, z + 0.5 * s, col, 0.05, name="BatHead")
    for sg in (-1, 1):
        dk.cone(p, (x + sg * 0.17 * s, y + 0.5 * s, z + 0.3 * s), 0.1 * s, 0.4 * s, col, verts=4, name="BatEar")
        pts = [(0.25, 0.25), (1.0, 0.7), (2.0, 0.55), (1.6, 0.05), (1.7, -0.6), (1.0, -0.1), (0.25, -0.35)]
        slab(p, [(x + sg * a * s, y + b * s) for a, b in pts][::sg], 0.1 * s, 'xy', z, col, 0.05, name="BatWing")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def crescent(p, plane, zc, yc, R_, at, thick, color, jitter=0.0, name="Crescent"):
    """Crescent moon polygon, opening toward +z (plane 'yz', thickness along x) or +x (plane 'xy')."""
    r_in, d = R_ * 0.8, R_ * 0.45
    ix = (R_ * R_ - r_in * r_in + d * d) / (2 * d)
    iy = math.sqrt(max(R_ * R_ - ix * ix, 0))
    t0 = math.atan2(iy, ix)
    phi = math.atan2(iy, ix - d)
    outer = [(R_ * math.cos(t0 + (2 * pi - 2 * t0) * i / 8), R_ * math.sin(t0 + (2 * pi - 2 * t0) * i / 8)) for i in range(9)]
    inner = [(d + r_in * math.cos(2 * pi - phi - (2 * pi - 2 * phi) * i / 6), r_in * math.sin(2 * pi - phi - (2 * pi - 2 * phi) * i / 6)) for i in range(7)]
    pts = [(zc + a, yc + b) for a, b in outer + inner]
    if plane == 'yz':
        return slab(p, [(b, a) for a, b in pts], thick, 'yz', at, color, jitter, name=name)
    return slab(p, pts, thick, 'xy', at, color, jitter, name=name)


def annulus(p, center, r_out, r_in, thick, color, sides=8, jitter=0.0, rot0=0.0, name="Ring"):
    """Flat ring in the x-y plane (a wheel rim), thickness along z."""
    cx, cy, cz = center
    pts, faces = [], []
    for zz in (-thick / 2, thick / 2):
        for r_ in (r_out, r_in):
            for i in range(sides):
                a = 2 * pi * i / sides + rot0
                pts.append((cx + r_ * math.cos(a), cy + r_ * math.sin(a), cz + zz))
    o, i_, o2, i2 = 0, sides, 2 * sides, 3 * sides
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((o + i, o + j, o2 + j, o2 + i))        # outer
        faces.append((i_ + i, i2 + i, i2 + j, i_ + j))       # inner
        faces.append((o + i, i_ + i, i_ + j, o + j))         # back annulus
        faces.append((o2 + i, o2 + j, i2 + j, i2 + i))       # front annulus
    return _obj(p, name, pts, faces, color, jitter)


def wheel(p, x, y, z, r, thick, rim, spoke, sides=8, spokes=3, rot0=0.0):
    """Spoked cart wheel in the x-y plane (axle along z)."""
    annulus(p, (x, y, z), r, r * 0.8, thick, rim, sides, 0.05, rot0, name="Rim")
    for k in range(spokes):
        a = pi * k / spokes + rot0
        dk.box(p, (x, y, z), (2 * r * 0.84, 0.16 * r, thick * 0.6), spoke, rot=(0, 0, math.degrees(a)), jitter=0.04, name="Spoke")
    dk.cyl(p, (x, y, z), r * 0.22, thick * 1.4, IRON_L, axis='z', verts=6, name="Hub")


def bottle(p, x, y0, z, h, col, sides=5):
    return lathe(p, (x, y0, z), [(0.34 * h * 0.5, 0), (0.34 * h * 0.5, h * 0.62), (0.13 * h * 0.5, h * 0.78), (0.13 * h * 0.5, h)], sides,
                 col, 0.04, name="Bottle")


def cross(p, x, y0, z, h, col, w=0.5, d=0.5, jitter=0.06):
    bx(p, x - w / 2, x + w / 2, y0, y0 + h, z - d / 2, z + d / 2, col, jitter, name="CrossV")
    bx(p, x - h * 0.3, x + h * 0.3, y0 + h * 0.62, y0 + h * 0.62 + w, z - d / 2, z + d / 2, col, jitter, name="CrossH")


def gravestone(p, x, z, w, h, col, kind=0, d=1.2, ang=0, y0=0.0):
    """Tombstone facing +z: kind 0 round top, 1 pointed top, 2 cross."""
    n0 = len(p.objs)
    if kind == 2:
        bx(p, x - w * 0.7, x + w * 0.7, y0, y0 + 0.5, z - d * 0.6, z + d * 0.6, COB_D, 0.05, name="CrossBase")
        cross(p, x, y0 + 0.5, z, h - 0.5, col, w=0.55, d=0.6)
    else:
        top = []
        if kind == 0:
            top = [(x - w / 2 + w * i / 5, y0 + h - 0.0 + w * 0.5 * math.sin(pi * i / 5)) for i in range(6)]
            top = [(x + (w / 2) * math.cos(pi * i / 5 + 0), y0 + h - w * 0.5 + (w / 2) * math.sin(pi * i / 5)) for i in range(6)]
        else:
            top = [(x + w / 2, y0 + h - w * 0.45), (x, y0 + h), (x - w / 2, y0 + h - w * 0.45)]
        pts = [(x - w / 2, y0), (x + w / 2, y0)] + top
        if kind == 0:
            pts = [(x - w / 2, y0), (x + w / 2, y0)] + top
        slab(p, pts, d, 'xy', z, col, 0.07, name="Tomb")
        # engraved cross on the face
        bx(p, x - 0.07, x + 0.07, y0 + h * 0.35, y0 + h * 0.8, z + d / 2, z + d / 2 + 0.05, IRON, 0, name="Engr")
        bx(p, x - 0.3, x + 0.3, y0 + h * 0.6, y0 + h * 0.66, z + d / 2, z + d / 2 + 0.05, IRON, 0, name="Engr")
    if ang:
        turn(p.objs[n0:], x, z, ang)



@part_builder("Ground")
def build_Ground():
    p = dk.Part("Ground")
    dk.box(p, (0, 0.15, 0), (190, 0.3, 130), NIGHT_D, name="Base")
    # grass: a grid of flat quads with a smooth dark-green colour field
    nx, nz = 15, 10
    pts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            pts.append((-95 + 190 * i / nx, 0.31, -65 + 130 * j / nz))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    g = _obj(p, "Grass", pts, faces, NIGHT, 0.0, closed=False, up=True)
    gouraud(g, lambda x, z: mix(NIGHT_D, NIGHT_L, max(0.0, min(1.0, 0.5 + 0.9 * noise(x, z)))))

    # cobbled court under the crypt (x 38..82, z -57..-27)
    bx(p, 38, 82, 0.3, 0.46, -57, -27, COB_D, 0.04, name="CourtBase")
    pts, faces = [], []
    tx, tz = 11, 7
    for j in range(tz):
        for i in range(tx):
            x0, x1 = 38 + 44 * i / tx + 0.15, 38 + 44 * (i + 1) / tx - 0.15
            z0, z1 = -57 + 30 * j / tz + 0.15, -57 + 30 * (j + 1) / tz - 0.15
            k = len(pts)
            pts += [(x0, 0.5, z0), (x1, 0.5, z0), (x1, 0.5, z1), (x0, 0.5, z1)]
            faces.append((k, k + 1, k + 2, k + 3))
    _obj(p, "Court", pts, faces, COB, 0.16, closed=False, up=True)

    # red carpet runner from the crypt door toward the path, gold edges
    bx(p, 57.5, 62.5, 0.3, 0.44, -31, -1, CRIM, 0.05, name="Carpet")
    for xe in (57.5, 61.9):
        bx(p, xe, xe + 0.6, 0.44, 0.47, -31, -1, GOLD_D, 0.04, name="CarpetEdge")
    for z in range(-29, 0, 4):
        bx(p, 58.6, 61.4, 0.44, 0.47, z, z + 0.6, GOLD_D, 0.04, name="CarpetBar")

    # round plaza around the Shiba's platform
    cx, cz = -60, 4
    dk.cyl(p, (cx, 0.4, cz), 13.6, 0.2, COB_D, verts=20, jitter=0.03, name="PlazaBase")
    pts, faces = [], []
    for ring, (r0, r1, n) in enumerate(((6.0, 9.6, 18), (9.6, 13.3, 22))):
        for i in range(n):
            a0, a1 = 2 * pi * i / n + 0.02, 2 * pi * (i + 1) / n - 0.02
            k = len(pts)
            pts += [(cx + r0 * math.cos(a0), 0.5, cz + r0 * math.sin(a0)), (cx + r1 * math.cos(a0), 0.5, cz + r1 * math.sin(a0)),
                    (cx + r1 * math.cos(a1), 0.5, cz + r1 * math.sin(a1)), (cx + r0 * math.cos(a1), 0.5, cz + r0 * math.sin(a1))]
            faces.append((k, k + 1, k + 2, k + 3))
    _obj(p, "Plaza", pts, faces, COB, 0.16, closed=False, up=True)
    # blood-red rune ring and moon marks on the plaza
    pts, faces = [], []
    for i in range(24):
        a0, a1 = 2 * pi * i / 24, 2 * pi * (i + 0.7) / 24
        k = len(pts)
        for rr, aa in ((9.2, a0), (9.7, a0), (9.7, a1), (9.2, a1)):
            pts.append((cx + rr * math.cos(aa), 0.505, cz + rr * math.sin(aa)))
        faces.append((k, k + 1, k + 2, k + 3))
    _obj(p, "Rune", pts, faces, BLOOD_D, 0.05, closed=False, up=True)

    # muddy graveyard plot with fresh mounds in front of the tombstones
    bx(p, -83, -49, 0.3, 0.44, 29, 51, DIRT, 0.05, name="Plot")
    for _ in range(14):
        x, z = R.uniform(-80, -52), R.uniform(30.5, 49.5)
        w, d = R.uniform(1.2, 2.6), R.uniform(1.2, 2.2)
        flat(p, [(x - w, z - d * 0.4), (x - w * 0.3, z - d), (x + w, z - d * 0.5), (x + w * 0.8, z + d * 0.6), (x - w * 0.4, z + d)], 0.46, DIRT_L, 0.1, name="Mud")
    for (x, z) in ((-78.6, 36.4), (-72, 40.6), (-65, 37.4), (-58, 36.9), (-53.1, 40.4), (-76, 46.4), (-60, 46.0), (-54.4, 48.4), (-68, 47.4)):
        lathe(p, (x, 0.3, z), [(1.7, 0), (1.3, 0.12), (0.6, 0.19), (0, 0.2)], 6, DIRT_L, 0.08, name="Mound")

    # night-grass patches, dead flowers and fog wisps over the field
    for _ in range(36):
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        w = R.uniform(1.5, 4.0)
        flat(p, [(x + w * math.cos(a) * R.uniform(0.7, 1.2), z + w * 0.7 * math.sin(a) * R.uniform(0.7, 1.2)) for a in [k * 2 * pi / 6 for k in range(6)]],
             0.33, R.choice((NIGHT_L, NIGHT_D, (52, 78, 64))), 0.06, name="Patch")
    for _ in range(30):
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        flat(p, [(x - 0.3, z), (x, z - 0.3), (x + 0.3, z), (x, z + 0.3)], 0.36, R.choice((BLOOD_D, PURP, BONE_D)), 0.05, name="Flower")
    for _ in range(8):
        x, z = R.uniform(-85, 85), R.uniform(-55, 55)
        w = R.uniform(4, 8)
        flat(p, [(x + w * math.cos(a), z + w * 0.5 * math.sin(a)) for a in [k * 2 * pi / 8 for k in range(8)]], 0.38, FOG, 0.03, name="Fog")
    return p


@part_builder("Gate")
def build_Gate():
    p = dk.Part("Gate")
    X0, X1 = -84.0, -80.0
    XC = -82.0
    for zc in (-8.2, 16.2):
        a, b = zc - 2, zc + 2
        bx(p, X0, X1, 0, 2.4, a, b, STONE_D, 0.06, name="PBase")
        bx(p, X0 + 0.3, X1 - 0.3, 2.4, 15, a + 0.3, b - 0.3, STONE, 0.08, name="PShaft")
        for xr in (X0, X1 - 0.3):
            bx(p, xr, xr + 0.3, 2.4, 15, zc - 0.55, zc + 0.55, STONE_L, 0.05, name="PRib")
        bx(p, X0, X1, 15, 16.4, a, b, STONE_L, 0.05, name="PCap")
        bx(p, X0 + 0.3, X1 - 0.3, 6.0, 6.5, a, b, STONE_L, 0.04, name="PBand")
        gargoyle(p, XC + 0.2, 16.4, zc, 0.85, ang=-90, col=STONE_D)
    # pointed arch ring, stained-glass tympanum, rose window and golden crescent
    arch_band(p, 'yz', 4.0, 10.2, 16.4, 7.6, 2.0, XC, 2.6, STONE, 0.07, n=6, name="Arch")
    inner = arch_curve(4.0, 10.2, 16.4, 7.6, 6)
    slab(p, [(y, u) for u, y in inner], 0.6, 'yz', XC, GLASS, 0.05, name="Glass")
    for zz, top in ((-2.2, 21.6), (4.0, 24.2), (10.2, 21.6)):
        bx(p, XC - 0.3, XC + 0.3, 16.4, top, zz - 0.12, zz + 0.12, IRON, 0, name="Mullion")
    bx(p, XC - 0.3, XC + 0.3, 18.2, 18.5, -6.2, 14.2, IRON, 0, name="Transom")
    dk.cyl(p, (XC + 0.2, 21.0, 4.0), 2.6, 0.5, STONE_L, axis='x', verts=12, name="RoseRim")
    dk.cyl(p, (XC + 0.4, 21.0, 4.0), 2.2, 0.5, GLASS_D, axis='x', verts=12, name="RoseGlass")
    crescent(p, 'yz', 3.7, 21.0, 1.7, XC + 0.7, 0.5, GOLD, 0.03)
    # keystone skull and crown spire
    bx(p, XC - 1.0, XC + 1.0, 24.6, 25.4, 3.0, 5.0, STONE_L, 0.05, name="Keystone")
    skull(p, X1 - 0.7, 24.0, 4.0, 1.1, ang=-90, detail=1)
    spire4(p, XC, 25.4, 4.0, 1.1, 1.6, STONE_D)
    # the open iron gates: two leaves swung half back against the pillars
    for (za, zb) in ((-6.2, -2.6), (10.6, 14.2)):
        bx(p, XC - 0.15, XC + 0.15, 0.4, 0.9, za, zb, IRON, 0, name="LeafRail")
        bx(p, XC - 0.15, XC + 0.15, 12.6, 13.1, za, zb, IRON, 0, name="LeafRail")
        for k in range(5):
            zz = za + 0.3 + (zb - za - 0.6) * k / 4
            bx(p, XC - 0.12, XC + 0.12, 0.9, 12.6, zz - 0.14, zz + 0.14, IRON_L, 0, name="Bar")
            dk.cone(p, (XC, 13.1, zz), 0.26, 1.2, IRON, verts=4, name="Spear")
    return p


@part_builder("Crypt")
def build_Crypt():
    p = dk.Part("Crypt")
    # body: plinth, walls with a pointed door gap, buttresses, windows
    bx(p, 41.6, 78.4, 0, 0.7, -56, -34, STONE_D, 0.05, name="Plinth")
    bx(p, 42, 78, 0.7, 10, -56, -54, WALL, 0.06, name="BackWall")
    bx(p, 42, 44, 0.7, 10, -54, -34, WALL, 0.06, name="LWall")
    bx(p, 76, 78, 0.7, 10, -54, -34, WALL, 0.06, name="RWall")
    bx(p, 42, 57, 0.7, 10, -36, -34, WALL, 0.06, name="FrontL")
    bx(p, 63, 78, 0.7, 10, -36, -34, WALL, 0.06, name="FrontR")
    door = arch_curve(60, 3, 5.4, 3.2, 5)
    slab(p, door + [(63, 10), (57, 10)], 2.0, 'xy', -35, WALL, 0.06, name="DoorFill")
    # string course
    bx(p, 42, 78, 6.2, 6.6, -56, -33.8, STONE_D, 0.05, name="Course")
    # pointed crimson door, stone surround, gold studs
    lancet(p, 'xy', 60, 0.7, 8.6, 6.0, -35.4, 0.3, CRIM, 0.05, ah=3.2, n=5, name="Door")
    arch_band(p, 'xy', 60, 3.0, 5.4, 3.2, 0.8, -33.9, 0.5, STONE_L, 0.05, n=5, name="DoorArch")
    bx(p, 56.2, 57.0, 0.7, 5.4, -34.15, -33.65, STONE_L, 0.05, name="DoorJambL")
    bx(p, 63.0, 63.8, 0.7, 5.4, -34.15, -33.65, STONE_L, 0.05, name="DoorJambR")
    bx(p, 59.9, 60.1, 0.9, 5.6, -35.2, -35.0, IRON, 0, name="DoorSeam")
    for sg in (-1, 1):
        for yy in (2.0, 4.0):
            bx(p, 60 + sg * 1.6 - 0.2, 60 + sg * 1.6 + 0.2, yy, yy + 0.4, -35.2, -35.0, GOLD, 0.03, name="Stud")
    # front lancet windows on both front walls, side windows, buttresses
    for xc in (49.5, 70.5):
        lancet(p, 'xy', xc, 3.0, 8.4, 2.4, -33.9, 0.3, GLASS_L, 0.05, n=4, name="Win")
        lancet(p, 'xy', xc, 2.8, 8.6, 3.0, -34.0, 0.2, STONE_L, 0.04, n=4, name="WinFrame")
    for zz in (-48.8, -41.2):
        lancet(p, 'yz', zz, 3.0, 8.4, 2.4, 41.9, 0.3, GLASS_L, 0.05, n=4, name="SWin")
        lancet(p, 'yz', zz, 3.0, 8.4, 2.4, 78.1, 0.3, GLASS_L, 0.05, n=4, name="SWin")
    for zz in (-52, -45, -38):
        for x0, x1 in ((40, 42), (78, 80)):
            bx(p, x0, x1, 0, 5.2, zz - 1.2, zz + 1.2, BLACK_L, 0.06, name="Buttress")
            bx(p, x0 + (0.4 if x0 == 40 else 0), x1 - (0.4 if x0 == 78 else 0), 5.2, 8.0, zz - 1.0, zz + 1.0, BLACK_L, 0.06, name="ButtressTop")
            pass
    # roof: courses of slate, gable ends, ridge cap
    gable(p, 'x', 41.0, 79.0, -45.0, 10.7, 10.1, 15.9, 0.8, ROOF, ROOF_L, n=4, jitter=0.06, name="Roof")
    gable_end(p, 'x', 43, -45, 10.0, 10.0, 15.6, 2.0, WALL, 0.05, name="GableL")
    gable_end(p, 'x', 77, -45, 10.0, 10.0, 15.6, 2.0, WALL, 0.05, name="GableR")
    bx(p, 40.6, 79.4, 15.6, 16.2, -45.5, -44.5, STONE_L, 0.05, name="Ridge")
    # belfry tower on the ridge with a spire
    bx(p, 57.2, 62.8, 15.6, 21.0, -47.8, -42.2, BLACK_L, 0.05, name="Tower")
    for sg in (-1, 1):
        lancet(p, 'xy', 60, 17.0, 20.2, 1.6, -42.1 if sg > 0 else -47.9, 0.2, IRON, 0, n=3, name="Louver")
        lancet(p, 'yz', -45, 17.0, 20.2, 1.6, 57.1 if sg < 0 else 62.9, 0.2, IRON, 0, n=3, name="Louver")
    bx(p, 56.9, 63.1, 21.0, 21.7, -48.1, -41.9, STONE_L, 0.05, name="TowerCornice")
    spire4(p, 60, 21.7, -45, 2.6, 4.3, ROOF)
    for sx in (-1, 1):
        for sz in (-1, 1):
            spire4(p, 60 + sx * 2.9, 21.7, -45 + sz * 2.9, 0.4, 1.4, STONE_D)
    # porch: stone columns, a little gable roof, steps, braziers
    for x in (54, 66):
        bx(p, x - 1.0, x + 1.0, 0.7, 1.4, -32.0, -30.0, STONE_D, 0.04, name="ColBase")
        dk.cyl(p, (x, 5.2, -31), 0.8, 7.6, STONE, verts=8, jitter=0.06, name="Column")
        bx(p, x - 1.1, x + 1.1, 9.0, 9.8, -32.1, -29.9, STONE_L, 0.04, name="ColCap")
    dk.prism(p, (60, 9.8, -32.6), 16.6, 5.4, 2.0, STONE_D, ridge='z', jitter=0.05, name="PorchRoof")
    bx(p, 51.9, 68.1, 9.4, 9.8, -35.3, -29.9, STONE_L, 0.04, name="PorchBeam")
    bx(p, 54.6, 65.4, 0.7, 1.05, -31.9, -29.9, STONE_L, 0.05, name="Step1")
    bx(p, 55.4, 64.6, 0.0, 0.7, -31.4, -29.9, STONE_L, 0.05, name="Step2")
    for x in (50.8, 69.2):
        bx(p, x - 0.45, x + 0.45, 0.7, 2.4, -31.8, -30.8, STONE_D, 0.05, name="BrazierPost")
        dk.cyl(p, (x, 2.7, -31.3), 0.9, 0.5, IRON, verts=6, top_radius=1.1, name="BrazierBowl")
        flame(p, x, 2.95, -31.3, 0.7, 1.7, BLOOD)
        flame(p, x + 0.2, 2.95, -31.2, 0.45, 1.2, FLAME)
    return p


# ---- extra helpers (graveyard set) -------------------------------------------------------------------------------------
def slab3(p, pts2, origin, U, V, thick, color, jitter=0.0, name="Slab3", off=0.0):
    """Extruded polygon in an arbitrary plane: pts2 = (u, v) along unit vectors U, V (stage axes) from origin; thick along U x V."""
    U = Vector(U).normalized()
    V = Vector(V).normalized()
    N = U.cross(V)
    o = Vector(origin)
    n = len(pts2)
    pts = []
    for s in (-0.5, 0.5):
        for (u, v) in pts2:
            q = o + U * u + V * v + N * (thick * s + off)
            pts.append((q.x, q.y, q.z))
    faces = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _obj(p, name, pts, faces, color, jitter)


def scaled(pts, k):
    cx = sum(a for a, b in pts) / len(pts)
    cz = sum(b for a, b in pts) / len(pts)
    return [(cx + (a - cx) * k, cz + (b - cz) * k) for a, b in pts]


BARK = (84, 66, 72); BARK_L = (112, 90, 92); GREEN_L = (186, 246, 170)


def angel(p, x, y0, z, s=1.0, col=STONE_L, ang=0):
    """A weeping angel statue (robed, head bowed into its hands, wings raised), 4.4 s tall, facing +z."""
    n0 = len(p.objs)

    def X(a): return x + a * s
    def Y(a): return y0 + a * s
    def Z(a): return z + a * s
    lathe(p, (x, y0, z), [(0.95 * s, 0), (0.8 * s, 1.2 * s), (0.58 * s, 2.4 * s), (0.5 * s, 2.8 * s)], 6, col, 0.05, name="Robe")
    bx(p, X(-0.75), X(0.75), Y(2.3), Y(2.95), Z(-0.38), Z(0.38), col, 0.05, name="Shoulders")
    blob(p, (X(0), Y(3.45), Z(0.12)), 0.42 * s, col, sy=1.0, sides=6, jitter=0.04, name="Head")
    for sg in (-1, 1):
        bx(p, X(sg * 0.32 - 0.14), X(sg * 0.32 + 0.14), Y(2.55), Y(3.5), Z(0.3), Z(0.62), BONE, 0.03, name="Hand")
        pts = [(0.3, 2.4), (0.55, 4.4), (1.4, 3.95), (1.9, 3.3), (2.2, 2.2), (1.55, 1.7), (1.2, 2.0), (0.75, 1.2)]
        slab(p, [(X(sg * a), Y(b)) for a, b in pts][::sg], 0.2 * s, 'xy', Z(-0.5), col, 0.05, name="Wing")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def hang_bat(p, x, ytop, z, s=1.0, col=IRON, ang=0):
    """A bat hanging upside down from y = ytop, wings wrapped around the body."""
    n0 = len(p.objs)
    blob(p, (x, ytop - 0.75 * s, z), 0.38 * s, col, sy=1.7, sides=5, jitter=0.05, name="HBody")
    for sg in (-1, 1):
        dk.cone(p, (x + sg * 0.22 * s, ytop - 0.1 * s, z + 0.05 * s), 0.1 * s, 0.4 * s, col, verts=4, name="HEar")
        bx(p, x + sg * 0.38 * s - 0.08 * s, x + sg * 0.38 * s + 0.08 * s, ytop - 1.8 * s, ytop - 0.4 * s, z - 0.3 * s, z + 0.3 * s,
           PURP_D, 0.04, name="HWing")
    bx(p, x - 0.14 * s, x + 0.14 * s, ytop - 0.2 * s, ytop, z - 0.1 * s, z + 0.1 * s, BONE_D, 0, name="Grip")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def crow(p, x, y0, z, s=1.0, ang=0):
    """A crow perched on a branch (facing +z turned by ang), feet at y0."""
    n0 = len(p.objs)
    blob(p, (x, y0 + 0.75 * s, z), 0.55 * s, IRON, sy=0.95, sides=6, jitter=0.04, name="CBody")
    blob(p, (x, y0 + 1.5 * s, z + 0.45 * s), 0.34 * s, IRON, sy=1.0, sides=5, jitter=0.04, name="CHead")
    bx(p, x - 0.12 * s, x + 0.12 * s, y0 + 1.36 * s, y0 + 1.56 * s, z + 0.7 * s, z + 1.2 * s, GOLD_D, 0.03, name="CBeak")
    bx(p, x - 0.14 * s, x + 0.14 * s, y0 + 1.5 * s, y0 + 1.68 * s, z + 0.66 * s, z + 0.78 * s, BONE, 0, name="CEye")
    bx(p, x - 0.3 * s, x + 0.3 * s, y0 + 0.5 * s, y0 + 0.8 * s, z - 1.2 * s, z - 0.3 * s, IRON_L, 0.04, name="CTail", rot=(20, 0, 0))
    for sg in (-1, 1):
        bx(p, x + sg * 0.5 * s - 0.1 * s, x + sg * 0.5 * s + 0.1 * s, y0 + 0.45 * s, y0 + 1.3 * s, z - 0.8 * s, z + 0.4 * s, BLACK_L, 0.04, name="CWing")
        bx(p, x + sg * 0.22 * s - 0.05 * s, x + sg * 0.22 * s + 0.05 * s, y0, y0 + 0.4 * s, z, z + 0.1 * s, GOLD_D, 0, name="CLeg")
    if ang:
        turn(p.objs[n0:], x, z, ang)


def torch_stand(p, x, z, h, flame_h=1.8, col=BLOOD):
    """Iron torch stand with a bowl and a flame."""
    dk.cyl(p, (x, 0.25, z), 0.9, 0.5, STONE_D, verts=6, top_radius=0.7, name="TBase")
    dk.cyl(p, (x, h / 2, z), 0.22, h, IRON, verts=5, name="TPole")
    dk.cyl(p, (x, h + 0.2, z), 0.75, 0.5, IRON_L, verts=6, top_radius=1.0, name="TBowl")
    flame(p, x, h + 0.45, z, 0.7, flame_h, col)
    flame(p, x + 0.12, h + 0.45, z + 0.1, 0.42, flame_h * 0.65, FLAME)


# ---- parts 4..8 ----------------------------------------------------------------------------------------------------------
@part_builder("Graves")
def build_Graves():
    p = dk.Part("Graves")
    for (x, z, w, h, col, kind, lean) in ((-78.6, 34, 2.2, 4.0, STONE, 0, 7), (-72, 38, 2.4, 6.0, STONE_D, 1, -5), (-65, 35, 2.2, 3.8, STONE, 2, 6),
                                          (-58, 34.5, 2.4, 5.2, STONE_D, 0, -8), (-53.1, 38, 2.2, 4.0, STONE, 1, 5), (-76, 44, 2.2, 3.2, STONE, 0, -6),
                                          (-60, 43.5, 2.4, 4.0, STONE_D, 1, 8), (-54.4, 45.9, 2.2, 3.6, STONE, 2, -4)):
        gravestone(p, x, z, w, h, col, kind=kind, d=1.2, ang=lean)
    # the weeping angel on a plinth
    bx(p, -69.6, -66.4, 0, 0.6, 44.2, 45.8, STONE_D, 0.05, name="AngelBase")
    bx(p, -69.2, -66.8, 0.6, 2.0, 44.4, 45.6, STONE, 0.05, name="AngelPlinth")
    bx(p, -69.4, -66.6, 2.0, 2.3, 44.3, 45.7, STONE_L, 0.04, name="AngelCap")
    angel(p, -68, 2.3, 45, 1.1, col=STONE_L)
    # fresh mounds, an old skull and wilted flowers
    for (x, z) in ((-78.6, 36.8), (-72, 40.8), (-58, 37.2), (-60, 41.2), (-76, 41.8)):
        lathe(p, (x, 0, z), [(1.6, 0), (1.2, 0.35), (0.5, 0.55), (0, 0.6)], 5, DIRT_L, 0.08, name="Mound")
    skull(p, -64.6, 0.45, 38.3, 0.8, ang=25, detail=0)
    for (x, z, c) in ((-78.4, 37.4, BLOOD_D), (-71.6, 41.4, PURP), (-57.6, 37.8, BLOOD_D)):
        bx(p, x - 0.08, x + 0.08, 0.5, 1.5, z - 0.08, z + 0.08, HEDGE_D, 0, name="Stem")
        bx(p, x - 0.25, x + 0.25, 1.4, 1.8, z - 0.25, z + 0.25, c, 0.05, name="Bloom")
    # little iron fence posts along the plot
    bx(p, -79.1, -52.7, 0.85, 1.0, 46.45, 46.55, IRON, 0, name="FenceRail")
    for k in range(7):
        x = -79 + k * 4.3
        bx(p, x - 0.1, x + 0.1, 0, 1.5, 46.4, 46.6, IRON, 0, name="Fence")
        dk.cone(p, (x, 1.5, 46.5), 0.2, 0.55, IRON, verts=4, name="FenceTip")
    return p


def lamp(p, x, z):
    frustum(p, x, z, 0, 1.2, 2.4, 2.4, 1.5, 1.5, IRON_L, 0.04, name="LBase")
    lathe(p, (x, 0, z), [(0.55, 1.2), (0.36, 1.9), (0.3, 2.5), (0.3, 9.6), (0.5, 10.0)], 6, IRON, 0.03, name="LPole")
    dk.cyl(p, (x, 5.6, z), 0.5, 0.45, IRON_L, verts=6, name="LCollar")
    for sg in (-1, 1):
        rod(p, (x + sg * 0.3, 4.0, z), (x + sg * 1.1, 5.0, z), 0.12, IRON, sides=4, name="LScroll")
        dk.box(p, (x + sg * 1.1, 5.15, z), (0.35, 0.35, 0.35), GOLD_D, name="LCurl")
    frustum(p, x, z, 10.0, 10.5, 1.5, 1.5, 1.8, 1.8, IRON, 0.03, name="LCradle")
    frustum(p, x, z, 10.5, 12.1, 1.5, 1.5, 1.9, 1.9, GREEN_L, 0.03, name="LGlass")
    frustum(p, x, z, 10.9, 11.7, 0.9, 0.9, 1.1, 1.1, (226, 255, 206), 0, name="LCore")
    hang_bat(p, x + 1.1, 5.0, z, 0.6, col=BLACK_L)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, x + sx * 0.92 - 0.08, x + sx * 0.92 + 0.08, 10.5, 12.1, z + sz * 0.92 - 0.08, z + sz * 0.92 + 0.08, IRON, 0, name="LFrame")
    spire4(p, x, 12.1, z, 1.25, 0.95, IRON, 0.03, name="LCap")
    dk.cone(p, (x, 13.0, z), 0.22, 0.5, GOLD_D, verts=4, name="LTip")


@part_builder("Lamps")
def build_Lamps():
    p = dk.Part("Lamps")
    for (x, z) in ((34, 57), (50, 53), (66, 57)):
        lamp(p, x, z)
    hang_bat(p, 50 + 1.1, 5.4, 53, 0.55)
    hang_bat(p, 34 - 1.1, 5.4, 57, 0.55, ang=30)
    hang_bat(p, 66 + 1.1, 5.4, 57, 0.55, ang=-30)
    return p


@part_builder("Tree")
def build_Tree():
    p = dk.Part("Tree")
    cx, cz = 30.0, -52.0
    lathe(p, (cx, 0, cz), [(3.2, 0), (2.8, 0.7), (2.0, 1.4), (1.7, 1.9)], 8, STONE_D, 0.08, name="Mound")

    def ring(x, y, z, r, k=1.0):
        return [(x + r * k * math.cos(2 * pi * i / 6 + 0.3), y, z + r * math.sin(2 * pi * i / 6 + 0.3)) for i in range(6)]
    loft(p, [ring(cx, 1.6, cz, 2.0), ring(cx - 0.3, 4.5, cz, 1.35, 1.1), ring(cx + 0.4, 7.5, cz + 0.1, 1.05), ring(cx + 0.1, 10.5, cz, 0.78),
             [(cx - 0.3, 13.2, cz)]], BARK, 0.08, name="Trunk")
    # roots
    for a, L in ((20, 3.4), (110, 3.0), (200, 3.6), (290, 3.0), (60, 2.4)):
        ar = math.radians(a)
        rod(p, (cx + 0.9 * math.cos(ar), 2.0, cz + 0.9 * math.sin(ar)), (cx + L * math.cos(ar), 0.2, cz + L * math.sin(ar)), 0.5, BARK_L, sides=4, r2=0.12, name="Root")

    def limb(pts, r0, r1=0.12):
        n = len(pts) - 1
        for i in range(n):
            ra = r0 + (r1 - r0) * i / n
            rb = r0 + (r1 - r0) * (i + 1) / n
            rod(p, pts[i], pts[i + 1], ra, BARK if i % 2 == 0 else BARK_L, sides=5, r2=rb, jitter=0.05, name="Limb")
        for q in pts[1:-1]:
            blob(p, q, r0 * 0.5, BARK, sy=1.0, sides=5, jitter=0.05, name="Knot")
    limb([(cx - 0.3, 9.0, cz), (26.6, 10.8, cz - 0.1), (23.4, 12.3, cz - 0.3), (22.3, 13.9, cz - 0.1)], 0.75, 0.16)
    limb([(26.6, 10.8, cz - 0.1), (25.2, 13.4, cz - 0.7), (24.6, 15.2, cz - 0.5)], 0.38, 0.1)
    limb([(24.8, 11.6, cz - 0.2), (23.6, 10.6, cz + 0.4), (22.6, 9.6, cz + 0.2)], 0.28, 0.08)
    limb([(cx + 0.4, 9.5, cz), (34.5, 10.7, cz + 0.1), (38.5, 12.3, cz - 0.2), (39.0, 14.0, cz - 0.1)], 0.78, 0.16)
    limb([(34.5, 10.7, cz + 0.1), (36.0, 13.4, cz + 0.4), (36.6, 15.5, cz + 0.2)], 0.38, 0.1)
    limb([(37.0, 11.6, cz - 0.1), (38.4, 10.4, cz + 0.3), (38.9, 9.0, cz + 0.2)], 0.26, 0.08)
    limb([(cx + 0.1, 10.0, cz - 0.3), (cx + 0.5, 11.3, -55.2), (cx + 0.9, 12.2, -59.0), (cx + 0.7, 13.6, -59.4)], 0.62, 0.14)
    limb([(cx + 0.5, 11.3, -55.2), (cx - 1.2, 13.4, -56.5), (cx - 2.0, 15.0, -56.1)], 0.3, 0.09)
    limb([(cx + 0.2, 10.6, cz + 0.3), (cx + 0.6, 11.8, -48.4), (cx + 0.4, 12.8, -45.0), (cx + 0.1, 14.1, -45.2)], 0.6, 0.14)
    limb([(cx + 0.6, 11.8, -48.4), (cx + 2.4, 14.0, -47.4), (cx + 2.8, 15.3, -47.6)], 0.28, 0.08)
    limb([(cx - 0.3, 12.0, cz), (cx - 1.4, 14.2, cz - 0.3), (cx - 1.9, 15.7, cz - 0.1)], 0.45, 0.1)
    # a hollow with watching eyes
    bx(p, cx - 0.6, cx + 0.5, 4.6, 6.3, cz + 1.05, cz + 1.3, BLACK, 0, name="Hollow")
    for sg in (-1, 1):
        bx(p, cx - 0.05 + sg * 0.26 - 0.1, cx - 0.05 + sg * 0.26 + 0.1, 5.5, 5.75, cz + 1.3, cz + 1.4, BLOOD, 0, name="Eye")
    # the crow and the hanging bats
    crow(p, 36.1, 11.45, cz + 0.1, 0.95, ang=20)
    hang_bat(p, 25.0, 11.3, cz - 0.3, 0.8)
    hang_bat(p, 27.8, 10.0, cz - 0.1, 0.7, ang=40)
    hang_bat(p, 32.6, 10.0, cz + 0.1, 0.7, ang=-30)
    return p


@part_builder("Coffin")
def build_Coffin():
    p = dk.Part("Coffin")
    # stone dais with two steps
    bx(p, 27.0, 41.0, 0, 0.75, 7.5, 16.5, STONE_D, 0.05, name="DaisLow")
    bx(p, 27.6, 40.4, 0.75, 1.2, 8.0, 16.0, STONE, 0.06, name="DaisTop")
    outline = [(29.2, 10.9), (31.1, 10.0), (38.8, 10.8), (38.8, 13.2), (31.1, 14.0), (29.2, 13.1)]
    slab(p, outline, 2.2, 'xz', 1.2, BLACK, 0.06, name="CoffinBody")
    slab(p, scaled(outline, 1.0), 0.12, 'xz', 3.4, GOLD, 0.03, name="CoffinTrim")
    slab(p, scaled(outline, 0.84), 0.28, 'xz', 3.4, CRIM, 0.05, name="Velvet")
    bx(p, 29.8, 31.5, 3.68, 4.2, 11.1, 12.9, BONE, 0.03, name="Pillow")
    bx(p, 33.4, 37.3, 3.68, 3.8, 11.9, 12.1, GOLD, 0.03, name="CrossL")
    bx(p, 34.4, 34.6, 3.68, 3.8, 11.3, 12.7, GOLD, 0.03, name="CrossT")
    for k in range(3):
        bx(p, 32.2 + k * 3.2, 33.0 + k * 3.2, 1.9, 2.6, 9.85, 10.05, GOLD_D, 0.04, name="Handle")
        bx(p, 32.2 + k * 3.2, 33.0 + k * 3.2, 1.9, 2.6, 13.95, 14.15, GOLD_D, 0.04, name="Handle")
    # lid leaning back against the dais
    a = math.radians(62)
    U, V = (1, 0, 0), (0, math.sin(a), -math.cos(a))
    lid = [(x - 34.0, z - 10.0) for x, z in outline]
    slab3(p, lid, (34.0, 1.3, 9.7), U, V, 0.5, BLACK, 0.06, name="Lid")
    slab3(p, scaled(lid, 0.84), (34.0, 1.3, 9.7), U, V, 0.1, CRIM, 0.05, name="LidLining", off=0.3)
    slab3(p, [(-1.0, 2.3), (-0.1, 2.3), (-0.1, 0.8), (0.1, 0.8), (0.1, 2.3), (1.0, 2.3), (1.0, 2.5), (0.1, 2.5), (0.1, 3.2), (-0.1, 3.2), (-0.1, 2.5), (-1.0, 2.5)], (34.0, 1.3, 9.7), U, V, 0.06, GOLD, 0.03, name="LidCross", off=0.38)
    # pillar candles and a skull at the head
    candle(p, 28.2, 1.2, 15.6, h=2.4, r=0.45)
    candle(p, 39.8, 1.2, 15.6, h=2.4, r=0.45)
    skull(p, 30.4, 2.2, 8.4, 0.9, ang=-10, detail=1)
    # a pale hand gripping the rim of the coffin
    bx(p, 35.2, 36.4, 3.3, 3.85, 14.0, 14.9, BONE, 0.03, name="Palm")
    for k in range(4):
        bx(p, 35.2 + k * 0.32, 35.45 + k * 0.32, 3.3, 3.75, 13.3, 14.05, BONE_D, 0.03, name="Finger")
    bx(p, 36.5, 36.8, 3.3, 3.7, 14.1, 14.8, BONE_D, 0.03, name="Thumb")
    for xs in (28.4, 39.6):
        skull(p, xs, 1.7, 8.3, 0.8, ang=0, detail=0)
    return p


@part_builder("Fountain")
def build_Fountain():
    p = dk.Part("Fountain")
    cx, cz = 66.0, -4.0
    lathe(p, (cx, 0, cz), [(7.4, 0), (8.0, 0.5), (8.0, 1.7), (7.2, 1.7), (7.1, 1.4)], 14, STONE, 0.06, name="Basin")
    dk.cyl(p, (cx, 1.4, cz), 7.1, 0.1, BLOOD, verts=14, jitter=0.03, name="BasinBlood")
    lathe(p, (cx, 1.4, cz), [(2.6, 0), (1.9, 0.9), (1.25, 1.8), (1.25, 6.3)], 8, STONE_D, 0.06, name="Stem")
    lathe(p, (cx, 3.3, cz), [(1.2, 0), (4.6, 1.0), (4.8, 1.8), (4.0, 1.8), (3.9, 1.5)], 12, STONE, 0.06, name="Bowl2")
    dk.cyl(p, (cx, 4.78, cz), 3.9, 0.1, BLOOD, verts=12, jitter=0.03, name="Bowl2Blood")
    lathe(p, (cx, 7.0, cz), [(1.0, 0), (2.5, 0.7), (2.7, 1.3), (2.1, 1.3), (2.0, 1.1)], 10, STONE, 0.06, name="Bowl3")
    dk.cyl(p, (cx, 8.0, cz), 2.0, 0.1, BLOOD, verts=10, jitter=0.03, name="Bowl3Blood")
    dk.cyl(p, (cx, 9.4, cz), 0.25, 3.0, IRON, verts=5, name="Spike")
    bat(p, cx, 11.1, cz, 0.95, ang=0, col=IRON)
    # streams of blood between the bowls
    for k in range(4):
        a = pi / 4 + k * pi / 2
        bx(p, cx + 2.15 * math.cos(a) - 0.18, cx + 2.15 * math.cos(a) + 0.18, 4.7, 7.9, cz + 2.15 * math.sin(a) - 0.18, cz + 2.15 * math.sin(a) + 0.18, BLOOD, 0.03, name="Stream")
        bx(p, cx + 4.5 * math.cos(a) - 0.2, cx + 4.5 * math.cos(a) + 0.2, 1.5, 4.5, cz + 4.5 * math.sin(a) - 0.2, cz + 4.5 * math.sin(a) + 0.2, BLOOD_D, 0.03, name="Stream")
    for k in range(4):
        a = k * pi / 2 + pi / 4
        skull(p, cx + 7.5 * math.cos(a), 2.3, cz + 7.5 * math.sin(a), 0.85, ang=math.degrees(a) * -1 + 90, detail=0)
    return p


# ---- parts 9..13 -------------------------------------------------------------------------------------------------------
def pedestal(p, x, z, h, col=STONE_D):
    frustum(p, x, z, 0, 0.7, 3.4, 3.4, 2.8, 2.8, COB_D, 0.05, name="PedBase")
    bx(p, x - 1.3, x + 1.3, 0.7, h - 0.45, z - 1.3, z + 1.3, col, 0.06, name="PedShaft")
    bx(p, x - 1.7, x + 1.7, h - 0.45, h, z - 1.7, z + 1.7, STONE, 0.05, name="PedCap")
    bx(p, x - 0.8, x + 0.8, h * 0.28, h * 0.28 + 0.9 if h > 3.5 else h * 0.28 + 0.6, z + 1.3, z + 1.42, BLACK, 0, name="PedPlaque")
    skull(p, x, h * 0.28 + 0.45 if h > 3.5 else h * 0.28 + 0.3, z + 1.45, 0.55, detail=0)


@part_builder("Gargoyles")
def build_Gargoyles():
    p = dk.Part("Gargoyles")
    for (x, z, h, ang) in ((10, 58, 3.2, 14), (20, 52, 4.8, 0), (28, 59, 2.4, -14)):
        pedestal(p, x, z, h)
        gargoyle(p, x, h, z, 1.4, ang=ang, col=STONE if h != 4.8 else STONE_L, wing=BLACK_L)
    return p


def hearse_wheel(p, x, y, z, r, thick):
    wheel(p, x, y, z, r, thick, BLACK_L, WOOD_L, sides=8, spokes=3, rot0=pi / 8)


@part_builder("Hearse")
def build_Hearse():
    p = dk.Part("Hearse")
    zl, zr = 31.2, 40.8
    for z in (zl, zr):
        hearse_wheel(p, 59, 2.8, z, 2.8, 0.8)
        hearse_wheel(p, 70, 2.2, z, 2.2, 0.8)
    rod(p, (59, 2.8, zl), (59, 2.8, zr), 0.3, IRON, sides=5, name="AxleB")
    rod(p, (70, 2.2, zl), (70, 2.2, zr), 0.3, IRON, sides=5, name="AxleF")
    # chassis and deck
    bx(p, 57.0, 73.0, 2.0, 3.1, 33.3, 38.7, BLACK, 0.05, name="Deck")
    bx(p, 57.0, 73.0, 2.9, 3.1, 33.2, 38.8, GOLD_D, 0.03, name="DeckTrim")
    bx(p, 56.7, 57.1, 2.0, 3.6, 33.6, 38.4, BLACK_L, 0.05, name="Tail")
    # coffin on the deck
    outline = [(58.6, 35.4), (60.0, 34.7), (68.8, 35.0), (68.8, 37.0), (60.0, 37.3), (58.6, 36.6)]
    slab(p, outline, 1.5, 'xz', 3.1, BLACK_L, 0.05, name="Coffin")
    bx(p, 61.0, 66.0, 4.6, 4.72, 35.9, 36.1, GOLD, 0.03, name="CrossL")
    bx(p, 62.6, 62.8, 4.6, 4.72, 35.5, 36.5, GOLD, 0.03, name="CrossT")
    # posts, canopy
    for x in (58.2, 69.8):
        for z in (33.6, 38.4):
            dk.cyl(p, (x, 5.4, z), 0.35, 6.0, IRON, verts=5, name="Post")
            dk.cyl(p, (x, 3.4, z), 0.5, 0.5, GOLD_D, verts=5, name="PostFoot")
    bx(p, 57.0, 71.0, 8.3, 8.9, 32.8, 39.2, BLACK, 0.04, name="CanopyPlate")
    bx(p, 57.0, 71.0, 8.9, 9.05, 32.8, 39.2, GOLD_D, 0.03, name="CanopyTrim")
    frustum(p, 64.0, 36.0, 9.05, 9.6, 14.0, 6.4, 9.0, 2.6, BLACK_L, 0.04, name="CanopyTop")
    for x in (57.5, 70.5):
        for z in (33.3, 38.7):
            dk.cone(p, (x, 9.05, z), 0.35, 0.55, BLOOD, verts=4, name="Plume")
    # purple drapes hanging from the canopy corners
    for z in (33.6, 38.4):
        for x in (58.7, 69.3):
            bx(p, x - 0.5, x + 0.5, 5.8, 8.3, z - 0.25, z + 0.25, PURP, 0.07, name="Drape")
            bx(p, x - 0.2, x + 0.2, 5.3, 5.8, z - 0.1, z + 0.1, GOLD, 0, name="Tassel")
    # lantern post and driver's seat
    dk.cyl(p, (71.4, 4.7, 36.0), 0.22, 3.2, IRON, verts=5, name="LanternPole")
    bx(p, 71.0, 71.8, 6.2, 7.8, 35.6, 36.4, IRON, 0, name="LanternCage")
    bx(p, 71.1, 71.7, 6.5, 7.5, 35.7, 36.3, GREEN, 0.03, name="LanternGlass")
    dk.cone(p, (71.4, 7.8, 36.0), 0.55, 0.45, IRON, verts=4, name="LanternCap")
    bx(p, 72.0, 73.0, 3.1, 3.9, 34.6, 37.4, WOOD, 0.05, name="Seat")
    bx(p, 72.8, 73.0, 3.9, 6.0, 34.6, 37.4, WOOD_D, 0.05, name="SeatBack")
    # skeleton coachman in a top hat
    bx(p, 72.1, 72.8, 3.9, 4.3, 35.2, 36.8, BONE_D, 0.03, name="Pelvis")
    bx(p, 72.2, 72.7, 4.3, 5.8, 35.5, 36.5, BONE, 0.03, name="Ribs")
    for yy in (4.7, 5.2):
        bx(p, 72.1, 72.9, yy, yy + 0.18, 35.3, 36.7, BONE_D, 0.02, name="Rib")
    skull(p, 72.45, 6.3, 36.0, 0.9, ang=-90, detail=1)
    bx(p, 72.0, 72.9, 6.75, 6.85, 35.5, 36.5, BLACK, 0, name="HatBrim")
    bx(p, 72.15, 72.75, 6.85, 7.5, 35.7, 36.3, BLACK, 0, name="Hat")
    for z in (35.2, 36.8):
        rod(p, (72.4, 5.5, z), (74.8, 4.1, z), 0.14, BONE, sides=4, name="Arm")
    # tongue and yoke
    rod(p, (73, 2.6, 36), (78, 2.4, 36), 0.26, WOOD, sides=5, name="Tongue")
    bx(p, 77.4, 77.8, 2.2, 2.6, 34.8, 37.2, WOOD_L, 0.04, name="Yoke")
    return p


def candelabra(p, x, z, h=7.0):
    lathe(p, (x, 0, z), [(1.2, 0), (0.9, 0.5), (0.4, 1.1), (0.3, 1.8), (0.3, h), (0.55, h + 0.3)], 6, IRON, 0.04, name="CandPole")
    bx(p, x - 1.7, x + 1.7, h + 0.3, h + 0.6, z - 0.22, z + 0.22, GOLD, 0.03, name="CandArm")
    for k, hh in ((-1, 0.9), (0, 1.25), (1, 0.9)):
        bx(p, x + k * 1.45 - 0.3, x + k * 1.45 + 0.3, h + 0.6, h + 0.85, z - 0.3, z + 0.3, GOLD_D, 0.03, name="CandCup")
        candle(p, x + k * 1.45, h + 0.85, z, h=hh, r=0.22)
    rod(p, (x, h - 1.4, z), (x + 1.45, h + 0.3, z), 0.12, GOLD_D, sides=4, name="CandCurl")
    rod(p, (x, h - 1.4, z), (x - 1.45, h + 0.3, z), 0.12, GOLD_D, sides=4, name="CandCurl")


@part_builder("Candles")
def build_Candles():
    p = dk.Part("Candles")
    # stone floor and a blood rune ring
    ell = lambda rx, rz, n=14: [(9.0 + rx * math.cos(2 * pi * i / n), 9.0 + rz * math.sin(2 * pi * i / n)) for i in range(n)]
    slab(p, ell(7.5, 4.5), 0.2, 'xz', 0.0, COB_D, 0.04, name="Floor")
    slab(p, ell(6.4, 3.7), 0.25, 'xz', 0.0, COB, 0.06, name="FloorIn")
    for k in range(10):
        a = 2 * pi * k / 10
        bx(p, 9.0 + 5.4 * math.cos(a) - 0.3, 9.0 + 5.4 * math.cos(a) + 0.3, 0.25, 0.3, 9.0 + 3.1 * math.sin(a) - 0.3, 9.0 + 3.1 * math.sin(a) + 0.3, BLOOD_D, 0.04, name="Rune")
    for (x, z) in ((3, 6), (14.6, 5.4), (3.4, 11.6), (15, 12)):
        candelabra(p, x, z)
    # the altar
    bx(p, 6.1, 11.9, 0, 0.6, 8.0, 12.0, STONE_D, 0.05, name="AltarBase")
    bx(p, 6.5, 11.5, 0.6, 1.8, 8.3, 11.7, STONE, 0.06, name="Altar")
    bx(p, 6.3, 11.7, 1.8, 2.0, 8.1, 11.9, STONE_L, 0.04, name="AltarTop")
    bx(p, 7.0, 11.0, 2.0, 2.08, 8.4, 11.8, CRIM, 0.04, name="Cloth")
    bx(p, 7.0, 11.0, 1.0, 2.0, 11.7, 11.82, CRIM, 0.04, name="ClothHang")
    skull(p, 9.4, 2.7, 10.0, 1.3, ang=-10, detail=1)
    bx(p, 7.2, 8.9, 2.08, 2.28, 8.9, 10.5, WOOD_D, 0.04, name="BookCover")
    bx(p, 7.3, 8.8, 2.28, 2.48, 9.0, 10.4, BONE, 0.03, name="BookPages")
    candle(p, 10.7, 2.08, 9.0, h=0.8, r=0.25)
    candle(p, 10.9, 2.08, 11.0, h=0.6, r=0.25)
    return p


@part_builder("Chapel")
def build_Chapel():
    p = dk.Part("Chapel")
    Z = -40.0
    slab(p, [(-73, 0), (-63, 0), (-63, 12), (-65.5, 12), (-66.6, 10.2), (-68.6, 11.3), (-70, 8.6), (-71.5, 9.8), (-73, 7.2)], 2.0, 'xy', Z, STONE, 0.07, name="WallL")
    slab(p, [(-57, 0), (-47, 0), (-47, 4.6), (-48.6, 5.9), (-50, 4.9), (-51.8, 8.2), (-53.2, 7.0), (-54.6, 10.0), (-57, 10.0)], 2.0, 'xy', Z, STONE, 0.07, name="WallR")
    door = arch_curve(-60, 3, 6.4, 2.6, 5)
    slab(p, door + [(-57, 12), (-63, 12)], 2.0, 'xy', Z, STONE, 0.07, name="Lintel")
    slab(p, [(-65, 12), (-55, 12), (-55, 13.3), (-57, 14.6), (-58.3, 16.4), (-60.6, 15.5), (-62, 14.2), (-64, 14.9), (-65, 13.2)], 2.0, 'xy', Z, DARK, 0.07, name="Gable")
    arch_band(p, 'xy', -60, 3.0, 6.4, 2.6, 0.7, Z + 1.05, 0.4, STONE_L, 0.05, n=5, name="DoorArch")
    bx(p, -63.7, -63.0, 0, 6.4, Z + 0.9, Z + 1.3, STONE_L, 0.05, name="JambL")
    bx(p, -57.0, -56.3, 0, 6.4, Z + 0.9, Z + 1.3, STONE_L, 0.05, name="JambR")
    # window openings are dark glass behind a stone frame, one pane already smashed
    for xc, top, w in ((-68, 9.0, 2.6), (-52, 8.0, 2.4)):
        lancet(p, 'xy', xc, 3.4, top, w, Z + 1.02, 0.12, GLASS_D, 0.05, n=4, name="Glass")
        arch_band(p, 'xy', xc, w / 2, top - w * 0.85, w * 0.85, 0.45, Z + 1.1, 0.3, STONE_L, 0.04, n=4, name="WinFrame")
        bx(p, xc - w / 2 - 0.45, xc - w / 2, 3.4, top - w * 0.85, Z + 0.95, Z + 1.25, STONE_L, 0.04, name="WinJamb")
        bx(p, xc + w / 2, xc + w / 2 + 0.45, 3.4, top - w * 0.85, Z + 0.95, Z + 1.25, STONE_L, 0.04, name="WinJamb")
    annulus(p, (-60, 14.0, Z + 1.1), 1.9, 1.25, 0.4, STONE_L, sides=10, jitter=0.04, name="Rose")
    dk.cyl(p, (-60, 14.0, Z + 1.05), 1.3, 0.2, GLASS_D, axis='z', verts=10, name="RoseGlass")
    bx(p, -60.15, -59.85, 12.8, 15.2, Z + 1.1, Z + 1.3, STONE_L, 0, name="RoseBarV")
    # stubs, broken side walls
    slab(p, [(0, -39), (0, -35), (9.4, -35), (10.2, -37.4), (8.4, -39)], 2.2, 'yz', -72.5, DARK, 0.07, name="StubL")
    slab(p, [(0, -39), (0, -35), (7.0, -35), (8.0, -37.2), (6.2, -39)], 2.2, 'yz', -47.5, DARK, 0.07, name="StubR")
    slab(p, [(0, -47), (0, -39), (7.0, -39), (5.8, -41.2), (6.8, -43), (4.4, -44.6), (5.2, -47)], 1.8, 'yz', -74.0, STONE, 0.07, name="SideL")
    slab(p, [(0, -47), (0, -39), (4.0, -39), (3.0, -41.5), (3.8, -44), (2.2, -47)], 1.8, 'yz', -46.4, STONE, 0.07, name="SideR")
    # inside: stone steps and a torn red carpet through the doorway
    bx(p, -62.6, -57.4, 0, 0.5, -38.9, -37.2, STONE_L, 0.05, name="Step")
    bx(p, -61.6, -58.4, 0.5, 0.58, -38.9, -37.4, CRIM, 0.05, name="Carpet")
    # rubble, fallen blocks, ivy and a perched bat
    for (x, z, r, c, sy) in ((-56, -36.4, 1.35, DARK, 0.55), (-65, -36.4, 1.1, STONE, 0.6), (-52.6, -36.2, 0.9, STONE, 0.6), (-68.4, -36.8, 0.8, DARK, 0.6)):
        blob(p, (x, r * sy, z), r, c, sy=sy, sides=5, jitter=0.1, name="Rubble")
    bx(p, -61.2, -59.4, 0, 0.7, -37.1, -36.0, STONE, 0.06, name="Block", rot=(0, 18, 0))
    bx(p, -55.0, -53.5, 0.6, 1.1, -37.2, -36.2, STONE_D, 0.06, name="Block", rot=(0, -25, 0))
    for (x, y0, h) in ((-72.6, 3.0, 5.0), (-71.0, 5.0, 3.6), (-48.2, 2.0, 3.4), (-64.0, 5.4, 5.0)):
        bx(p, x - 0.3, x + 0.3, y0, y0 + h, Z + 0.98, Z + 1.18, HEDGE, 0.08, name="Ivy")
        bx(p, x - 0.9, x + 0.1, y0 + h * 0.4, y0 + h * 0.4 + 0.45, Z + 0.98, Z + 1.18, HEDGE_L, 0.08, name="Ivy")
    bat(p, -58.3, 16.8, -39.4, 0.45, col=IRON)
    return p


def barrel_z(p, x, y, z0, r, L, color=WOOD, hoop=IRON, sides=6):
    prof = [(0.82 * r, 0), (0.98 * r, 0.2 * L), (r, 0.5 * L), (0.98 * r, 0.8 * L), (0.82 * r, L)]
    o = lathe(p, (x, y, z0), prof, sides, color, 0.06, axis='z', name="BarrelZ")
    recolor(o, lambda c, n, i: hoop if (abs(n[2]) < 0.9 and (abs(c[2] - z0 - 0.18 * L) < 0.12 * L or abs(c[2] - z0 - 0.82 * L) < 0.12 * L)) else (WOOD_L if abs(n[2]) > 0.9 else None), 0.04)
    return o


@part_builder("Cellar")
def build_Cellar():
    p = dk.Part("Cellar")
    barrel(p, -27.0, 0, 24.6, 1.7, 4.0, color=WOOD, hoop=IRON, sides=6)
    barrel(p, -23.4, 0, 25.4, 1.7, 4.0, color=WOOD_D, hoop=IRON, sides=6)
    barrel(p, -25.4, 0, 29.0, 1.7, 4.0, color=WOOD, hoop=GOLD_D, sides=6)
    barrel(p, -25.4, 4.0, 29.0, 1.4, 1.8, color=WOOD_L, hoop=IRON, sides=6)
    # big cask lying on a cradle, with a tap
    barrel_z(p, -20.0, 2.6, 27.4, 2.5, 6.0)
    for z in (28.2, 32.4):
        bx(p, -22.6, -17.4, 0, 1.3, z - 0.3, z + 0.3, WOOD_D, 0.05, name="Cradle")
    dk.cyl(p, (-20.0, 1.8, 33.5), 0.28, 0.9, GOLD, axis='z', verts=5, name="Tap")
    bx(p, -20.2, -19.8, 1.4, 1.9, 33.4, 33.9, GOLD_D, 0, name="TapHandle")
    bx(p, -20.15, -19.85, 0.1, 1.5, 33.1, 33.4, BLOOD, 0.03, name="Drip")
    # bottle rack with six bottles
    bx(p, -16.6, -14.6, 0, 0.5, 22.2, 28.6, WOOD_D, 0.05, name="RackBase")
    for z in (22.4, 28.4):
        bx(p, -16.6, -14.6, 0.5, 5.0, z - 0.2, z + 0.2, WOOD, 0.06, name="RackSide")
    for y in (1.6, 3.0, 4.4):
        bx(p, -16.6, -14.6, y - 0.12, y + 0.12, 22.4, 28.4, WOOD_L, 0.05, name="Shelf")
    for yi, y in enumerate((1.7, 3.1, 4.5)):
        for k in range(3):
            z = 23.4 + k * 2.2 + (0.5 if yi % 2 else 0)
            lathe(p, (-16.5, y + 0.3, z), [(0.46, 0), (0.46, 1.1), (0.18, 1.5), (0.18, 1.9)], 4, BLOOD_D if (yi + k) % 2 == 0 else GLASS_D, 0.05, axis='x', name="Bottle")
    # table with goblets, a bottle and a candle
    for (x, z) in ((-20.6, 22.9), (-17.4, 22.9), (-20.6, 25.1), (-17.4, 25.1)):
        bx(p, x - 0.15, x + 0.15, 0, 2.1, z - 0.15, z + 0.15, WOOD_D, 0.04, name="Leg")
    bx(p, -21.0, -17.0, 2.1, 2.45, 22.7, 25.3, WOOD, 0.05, name="TableTop")
    bx(p, -20.2, -17.8, 2.45, 2.5, 22.6, 25.4, CRIM, 0.04, name="Runner")
    for (x, z) in ((-19.8, 23.3), (-18.4, 24.4)):
        dk.cyl(p, (x, 2.5 + 0.35, z), 0.3, 0.7, GOLD, verts=5, top_radius=0.4, name="Goblet")
        dk.cyl(p, (x, 3.2, z), 0.36, 0.08, BLOOD, verts=5, name="GobletBlood")
    bottle(p, -20.4, 2.5, 24.7, 1.7, BLOOD_D)
    candle(p, -18.0, 2.5, 22.95, h=0.7, r=0.2)
    return p
# ---- parts 14..25 ------------------------------------------------------------------------------------------------------
FOG_L = (206, 214, 232); FOG_M = (150, 160, 184)


def skull_lite(p, x, y, z, s=1.0):
    """Cheap wall skull (24 tris) facing +z."""
    bx(p, x - 0.42 * s, x + 0.42 * s, y - 0.4 * s, y + 0.4 * s, z - 0.4 * s, z + 0.4 * s, BONE, 0.07, name="SkullL")
    bx(p, x - 0.32 * s, x + 0.32 * s, y - 0.12 * s, y + 0.14 * s, z + 0.39 * s, z + 0.43 * s, IRON, 0, name="EyesL")


def bone(p, A, B, r=0.2, col=BONE_D):
    rod(p, A, B, r, col, sides=4, jitter=0.04, name="Bone")


@part_builder("Mirror")
def build_Mirror():
    p = dk.Part("Mirror")
    cx, z = 4.0, -16.0
    frustum(p, cx, z, 0, 1.4, 6.0, 3.6, 5.2, 3.0, BLACK_L, 0.05, name="Plinth")
    lancet(p, 'xy', cx, 1.4, 14.6, 8.0, z, 1.4, BLACK, 0.05, ah=6.0, n=5, name="Frame")
    lancet(p, 'xy', cx, 1.9, 14.0, 7.0, z + 0.62, 0.16, BLACK_L, 0.04, ah=5.6, n=5, name="FrameIn")
    lancet(p, 'xy', cx, 2.7, 13.0, 5.6, z + 0.7, 0.3, FOG_M, 0.02, ah=4.6, n=5, name="Glass")
    arch_band(p, 'xy', cx, 2.8, 8.4, 4.6, 0.36, z + 0.72, 0.34, GOLD, 0.03, n=5, name="GoldArch")
    bx(p, 0.82, 1.2, 2.4, 8.4, z + 0.55, z + 0.9, GOLD, 0.03, name="GoldSide")
    bx(p, 6.8, 7.18, 2.4, 8.4, z + 0.55, z + 0.9, GOLD, 0.03, name="GoldSide")
    bx(p, 0.82, 7.18, 2.3, 2.7, z + 0.55, z + 0.9, GOLD, 0.03, name="GoldSill")
    slab(p, [(2.2, 3.4), (3.0, 3.4), (5.4, 9.6), (4.6, 9.6)], 0.06, 'xy', z + 0.87, FOG_L, 0.02, name="Shine")
    slab(p, [(3.4, 3.4), (3.8, 3.4), (5.5, 7.6), (5.1, 7.6)], 0.06, 'xy', z + 0.87, FOG_L, 0.02, name="Shine")
    lathe(p, (cx, 14.4, z), [(0.7, 0), (0.45, 0.5), (0.8, 1.0), (0.45, 1.5), (0, 2.0)], 6, GOLD, 0.04, name="Crest")
    bat(p, cx, 13.75, z + 0.75, 0.5, col=GOLD_D)
    for sg in (-1, 1):
        rod(p, (cx + sg * 1.3, 13.6, z + 0.2), (cx + sg * 2.0, 15.4, z + 0.2), 0.3, BLACK_L, sides=4, r2=0.04, name="Horn")
    for xs in (0.45, 7.55):
        spire4(p, xs, 8.5, z, 0.5, 1.7, BLACK_L, 0.05, name="Finial")
    for xs in (1.1, 6.9):
        candle(p, xs, 1.4, z + 1.0, h=0.9, r=0.26)
    skull(p, cx, 0.75, z + 1.7, 0.75, detail=1)
    return p


@part_builder("Cauldron")
def build_Cauldron():
    p = dk.Part("Cauldron")
    cx, cz = -44.0, 28.0
    # fire bed
    for k in range(4):
        a = pi / 4 + k * pi / 2
        rod(p, (cx + 3.0 * math.cos(a), 0.5, cz + 3.0 * math.sin(a)), (cx + 0.3 * math.cos(a), 0.9, cz + 0.3 * math.sin(a)), 0.42, WOOD_D, sides=5, jitter=0.05, name="FireLog")
    for dx, dz, r, h in ((0, 0, 1.2, 4.0), (2.6, 1.4, 1.1, 3.6), (-2.6, 1.6, 1.1, 3.8), (0.4, 3.2, 1.3, 4.2), (3.6, -0.8, 0.9, 3.0), (-3.4, -0.8, 0.9, 2.8), (-1.5, 3.0, 0.9, 3.0), (2.0, 3.0, 0.9, 2.8)):
        flame(p, cx + dx, 0.6, cz + dz, r, h, FLAME_R if (abs(dx) + abs(dz)) > 2.0 else FLAME)
    flame(p, cx + 0.3, 0.7, cz + 2.9, 0.55, 2.0, (255, 232, 150))
    flame(p, cx, 0.7, cz, 0.6, 2.4, (255, 232, 150))
    # front log pile
    for (x, y, zz) in ((cx - 0.0, 0.55, 23.9), (cx + 0.2, 0.55, 24.95), (cx - 0.2, 1.35, 24.4)):
        rod(p, (x - 2.7, y, zz), (x + 2.7, y + 0.1, zz), 0.55, WOOD if y < 1 else WOOD_L, sides=5, jitter=0.06, name="Log")
    # legs
    for a in (pi / 6, 5 * pi / 6, 3 * pi / 2):
        rod(p, (cx + 3.4 * math.cos(a), 3.2, cz + 3.4 * math.sin(a)), (cx + 4.2 * math.cos(a), 0.0, cz + 4.2 * math.sin(a)), 0.42, IRON, sides=5, r2=0.34, name="Leg")
    o = lathe(p, (cx, 1.0, cz), [(1.7, 0), (3.1, 0.9), (3.95, 2.3), (4.0, 3.7), (3.6, 5.0), (3.9, 5.5)], 8, IRON, 0.05, name="Pot")
    recolor(o, lambda c, n, i: IRON_L if (n[1] > 0.3) else None, 0.04)
    lathe(p, (cx, 6.1, cz), [(4.0, 0), (4.3, 0.35), (4.3, 1.2), (3.6, 1.2)], 8, IRON_L, 0.05, name="Rim")
    dk.cyl(p, (cx, 7.33, cz), 3.7, 0.12, GREEN, verts=8, jitter=0.03, name="Brew")
    for (dx, dz, r) in ((-1.4, -0.8, 0.55), (1.0, 1.2, 0.7), (0.6, -1.5, 0.45), (-1.0, 1.3, 0.4), (1.9, -0.2, 0.35)):
        blob(p, (cx + dx, 7.45 + r * 0.6, cz + dz), r, GREEN_L, sy=0.9, sides=5, jitter=0.04, name="Bubble")
    for sg in (-1, 1):
        bx(p, cx + sg * 4.25 - 0.3, cx + sg * 4.25 + 0.3, 5.9, 6.7, cz - 0.5, cz + 0.5, IRON_L, 0.04, name="Ear")
    # ladle resting on the rim
    rod(p, (cx + 1.9, 7.35, cz + 0.8), (-38.9, 7.65, 32.4), 0.22, WOOD_L, sides=4, name="LadleStick")
    skull(p, cx, 3.5, cz + 4.05, 1.0, detail=0)
    skull(p, cx - 0.9, 7.55, cz + 1.3, 1.1, ang=-20, detail=1)
    bone(p, (cx + 1.6, 7.3, cz - 1.0), (cx + 2.8, 8.0, cz - 0.2), 0.22, BONE)
    bone(p, (cx - 2.2, 7.3, cz - 1.6), (cx - 3.0, 7.9, cz - 0.6), 0.2, BONE)
    skull(p, -39.4, 0.9, 27.3, 1.25, ang=-40, detail=1)
    # bones
    skull(p, -40.2, 0.5, 25.9, 0.95, ang=35, detail=1)
    bone(p, (-41.4, 0.3, 24.7), (-39.0, 0.3, 27.4), 0.2)
    bone(p, (-39.2, 0.3, 24.6), (-38.9, 0.3, 27.0), 0.2)
    bone(p, (-41.0, 0.3, 27.2), (-38.9, 0.3, 28.0), 0.18)
    return p


def cage(p, x, z, y0, y1, w, skeleton):
    h = w / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, x + sx * h - 0.09, x + sx * h + 0.09, y0, y1, z + sz * h - 0.09, z + sz * h + 0.09, IRON_L, 0.03, name="CageBar")
    for yy in (y0 + 0.05, y0 + (y1 - y0) * 0.5, y1 - 0.5):
        bx(p, x - h, x + h, yy, yy + 0.14, z + h - 0.07, z + h + 0.07, IRON, 0, name="CageBand")
        bx(p, x - h, x + h, yy, yy + 0.14, z - h - 0.07, z - h + 0.07, IRON, 0, name="CageBand")
        bx(p, x - h - 0.07, x - h + 0.07, yy, yy + 0.14, z - h, z + h, IRON, 0, name="CageBand")
        bx(p, x + h - 0.07, x + h + 0.07, yy, yy + 0.14, z - h, z + h, IRON, 0, name="CageBand")
    for k in (-0.4, 0.4):
        bx(p, x + k * w * 0.5 - 0.05, x + k * w * 0.5 + 0.05, y0, y1 - 0.5, z + h - 0.05, z + h + 0.05, IRON_L, 0, name="CageBar")
    bx(p, x - h, x + h, y0 - 0.1, y0 + 0.1, z - h, z + h, IRON, 0, name="CageFloor")
    spire4(p, x, y1 - 0.5, z, h * 0.95, 1.1, IRON, 0.04, name="CageTop")
    dk.cyl(p, (x, y1 + 0.75, z), 0.28, 0.28, IRON_L, axis='z', verts=6, name="CageRing")
    if skeleton:
        skull(p, x, y1 - 1.3, z, 0.8, detail=1)
        bx(p, x - 0.08, x + 0.08, y0 + 0.9, y1 - 1.7, z - 0.08, z + 0.08, BONE_D, 0, name="Spine")
        for k in range(3):
            bx(p, x - 0.55 + k * 0.03, x + 0.55 - k * 0.03, y1 - 1.9 - k * 0.38, y1 - 1.76 - k * 0.38, z - 0.12, z + 0.3, BONE, 0.03, name="Rib")
        bone(p, (x - 0.5, y1 - 1.9, z), (x - 0.7, y0 + 0.9, z + 0.2), 0.12)
        bone(p, (x + 0.5, y1 - 1.9, z), (x + 0.7, y0 + 0.9, z + 0.2), 0.12)
        bone(p, (x - 0.2, y0 + 0.9, z), (x - 0.35, y0 + 0.15, z + 0.2), 0.14)
        bone(p, (x + 0.2, y0 + 0.9, z), (x + 0.35, y0 + 0.15, z + 0.2), 0.14)
    else:
        hang_bat(p, x, y1 - 0.4, z, 0.75, col=BLACK_L)


@part_builder("Gibbet")
def build_Gibbet():
    p = dk.Part("Gibbet")
    z = -48.0
    ell = lambda cx0, cz0, rx, rz, n=10: [(cx0 + rx * math.cos(2 * pi * i / n), cz0 + rz * math.sin(2 * pi * i / n)) for i in range(n)]
    slab(p, ell(87.5, -46.0, 4.75, 4.5), 0.5, 'xz', 0.0, DIRT, 0.06, name="Mound")
    for (x, zz, r) in ((92.0, -44.0, 0.7), (83.4, -47.0, 0.6), (86.0, -42.0, 0.5)):
        rock(p, (x, r * 0.4 + 0.4, zz), r, STONE_D, name="Stone")
    bx(p, 90.2, 91.8, 0.4, 14.0, z - 0.8, z + 0.8, WOOD, 0.06, name="Post")
    bx(p, 89.9, 92.1, 0.4, 1.2, z - 1.1, z + 1.1, WOOD_D, 0.05, name="PostFoot")
    bx(p, 83.2, 91.8, 13.0, 13.8, z - 0.4, z + 0.4, WOOD_L, 0.06, name="Beam")
    rod(p, (91.0, 9.6, z + 0.5), (88.0, 13.0, z + 0.5), 0.3, WOOD_D, sides=4, name="Brace")
    rod(p, (91.0, 9.6, z - 0.5), (88.0, 13.0, z - 0.5), 0.3, WOOD_D, sides=4, name="Brace")
    for (x, yb, yt, sk) in ((84.8, 6.3, 11.3, True), (89.0, 5.9, 10.9, False)):
        bx(p, x - 0.07, x + 0.07, yt + 0.9, 13.0, z - 0.07, z + 0.07, IRON_L, 0, name="Chain")
        cage(p, x, z, yb, yt, 2.6, sk)
    crow(p, 86.9, 13.8, z, 0.7, ang=-15)
    skull(p, 85.6, 0.95, -43.6, 0.75, ang=25, detail=1)
    bone(p, (87.2, 0.6, -44.0), (89.4, 0.6, -42.6), 0.17)
    bone(p, (84.0, 0.6, -44.6), (82.9, 0.6, -46.6), 0.17)
    return p


@part_builder("Hunter")
def build_Hunter():
    p = dk.Part("Hunter")
    bx(p, -77.5, -68.5, 3.2, 4.0, 54.5, 59.5, WOOD, 0.06, name="Bed")
    for (z0, z1) in ((54.5, 55.0), (59.0, 59.5)):
        bx(p, -77.5, -68.5, 4.0, 4.9, z0, z1, WOOD_L, 0.06, name="SidePlank")
        bx(p, -77.5, -68.5, 5.0, 5.8, z0, z1, WOOD, 0.06, name="SidePlank")
    bx(p, -77.6, -77.1, 4.0, 5.8, 54.5, 59.5, WOOD_L, 0.06, name="EndBoard")
    for zc in (53.6, 60.4):
        wheel(p, -75.0, 2.2, zc, 2.2, 0.6, IRON, WOOD_L, sides=8, spokes=4, rot0=pi / 8)
    dk.cyl(p, (-75.0, 2.2, 57.0), 0.22, 7.0, IRON, axis='z', verts=5, name="Axle")
    for zh in (55.2, 58.8):
        rod(p, (-68.6, 3.6, zh), (-62.9, 2.6, zh), 0.22, WOOD_L, sides=4, name="Shaft")
        rod(p, (-63.6, 2.7, zh), (-63.6, 0.0, zh), 0.16, WOOD_D, sides=4, name="Prop")
    bx(p, -63.2, -62.6, 2.2, 2.9, 54.9, 59.1, WOOD_L, 0.05, name="Grip")
    # stakes
    for (xb, zb, xt, zt, yt) in ((-76.4, 55.6, -72.0, 55.4, 8.8), (-75.6, 56.4, -71.4, 56.9, 9.2), (-76.8, 57.4, -73.0, 58.2, 8.4),
                                 (-75.2, 58.6, -76.8, 58.0, 8.9), (-74.4, 55.6, -77.0, 56.0, 8.6), (-76.0, 58.2, -72.2, 58.8, 7.8)):
        rod(p, (xb, 4.1, zb), (xt, yt, zt), 0.2, WOOD_L, sides=4, r2=0.03, jitter=0.04, name="Stake")
    bx(p, -76.6, -76.0, 4.9, 5.4, 54.6, 59.4, BONE_D, 0.03, name="Rope")
    # garlic sack and bulbs
    blob(p, (-70.8, 5.0, 57.4), 1.45, BONE_D, sy=0.9, sides=6, jitter=0.05, name="Sack")
    dk.cone(p, (-70.8, 6.1, 57.4), 0.4, 0.9, GREEN_D, verts=4, name="SackTop")
    bx(p, -71.5, -70.1, 5.9, 6.2, 57.0, 57.8, BONE, 0.03, name="SackTie")
    for (dx, dz) in ((-1.9, -1.2), (-1.0, 1.9), (1.7, -1.4), (1.8, 1.0), (0.2, -2.2)):
        x, zz = -70.8 + dx * 0.9, 57.2 + dz * 0.8
        blob(p, (x, 4.65, zz), 0.6, BONE, sy=0.85, sides=5, jitter=0.04, name="Garlic")
        dk.cone(p, (x, 5.1, zz), 0.14, 0.6, GREEN_D, verts=4, name="GarlicTop")
    for (gx, nb) in ((-72.5, 3), (-69.0, 3)):
        bx(p, gx - 0.06, gx + 0.06, 5.6, 5.85, 59.5, 59.9, BONE_D, 0, name="BraidHook")
        for k in range(nb):
            blob(p, (gx, 5.3 - k * 0.8, 59.95), 0.42, BONE, sy=0.9, sides=5, jitter=0.04, name="BraidGarlic")
    # crossbow
    bx(p, -74.2, -69.6, 4.0, 4.3, 55.4, 55.9, WOOD_D, 0.04, name="CrossbowStock")
    rod(p, (-69.9, 4.35, 55.65), (-70.9, 4.35, 54.6), 0.2, WOOD_L, sides=4, name="Limb")
    rod(p, (-69.9, 4.35, 55.65), (-70.9, 4.35, 56.9), 0.2, WOOD_L, sides=4, name="Limb")
    rod(p, (-70.9, 4.35, 54.6), (-70.9, 4.35, 56.9), 0.05, BONE, sides=3, name="String")
    bx(p, -72.6, -72.4, 4.3, 4.7, 55.55, 55.75, IRON, 0, name="Trigger")
    # a cross
    cross(p, -68.9, 4.0, 58.6, 4.6, WOOD_L, w=0.4, d=0.4)
    return p


@part_builder("Ossuary")
def build_Ossuary():
    p = dk.Part("Ossuary")
    cx, Z = -24.0, -56.5
    door = arch_curve(cx, 3.0, 2.2, 3.4, 5)
    slab(p, [(-34, 0), (cx - 3.0, 0)] + door + [(cx + 3.0, 0), (-14, 0), (-14, 8), (-34, 8)], 2.0, 'xy', Z, STONE, 0.07, name="Wall")
    slab(p, [(cx - 3.0, 0)] + door + [(cx + 3.0, 0)], 0.3, 'xy', Z - 0.3, BLACK, 0.03, name="Alcove")
    arch_band(p, 'xy', cx, 3.0, 2.2, 3.4, 0.6, Z + 1.3, 0.8, STONE_L, 0.05, n=5, name="AlcoveArch")
    bx(p, cx - 3.6, cx - 3.0, 0, 2.2, Z + 0.9, Z + 1.7, STONE_L, 0.05, name="Jamb")
    bx(p, cx + 3.0, cx + 3.6, 0, 2.2, Z + 0.9, Z + 1.7, STONE_L, 0.05, name="Jamb")
    bx(p, cx - 2.4, cx + 2.4, 0, 0.6, Z + 0.4, Z + 1.7, STONE_D, 0.05, name="Shelf")
    skull(p, cx, 1.65, Z + 1.0, 1.5, detail=1)
    candle(p, cx - 1.9, 0.6, Z + 1.2, h=1.1, r=0.28)
    candle(p, cx + 1.9, 0.6, Z + 1.2, h=0.8, r=0.28)
    bx(p, -34, -14, 7.3, 8.1, Z + 0.3, Z + 1.3, STONE_L, 0.05, name="Cap")
    bone(p, (cx - 1.5, 6.5, Z + 1.45), (cx + 1.5, 7.1, Z + 1.45), 0.22, BONE)
    bone(p, (cx - 1.5, 7.1, Z + 1.35), (cx + 1.5, 6.5, Z + 1.35), 0.22, BONE_D)
    skull(p, cx, 6.8, Z + 1.7, 0.75, detail=1)
    # bone columns
    for x in (-33.0, -15.0):
        bx(p, x - 1.0, x + 1.0, 0, 0.6, -55.3, -53.3, STONE_D, 0.05, name="ColBase")
        bx(p, x - 0.7, x + 0.7, 0.6, 6.5, -54.9, -53.7, BONE_D, 0.05, name="ColCore")
        for k in range(5):
            bx(p, x - 1.15, x + 1.15, 0.9 + k * 1.1, 1.5 + k * 1.1, -54.1, -53.4, BONE if k % 2 == 0 else BONE_D, 0.05, name="ColBone")
        bx(p, x - 1.0, x + 1.0, 6.5, 7.0, -55.2, -53.4, STONE_L, 0.05, name="ColCap")
        skull(p, x, 7.5, -54.2, 0.9, detail=0)
    # wall of skulls
    for xs in (-30.0, -18.0):
        for ci in range(3):
            for ri in range(4):
                if ri == 3 and ci == 1:
                    continue
                skull_lite(p, xs + (ci - 1) * 1.3 + (0.3 if ri % 2 else 0), 1.2 + ri * 1.6, Z + 1.3, 1.1)
    bx(p, -32.0, -27.6, 0, 0.5, Z + 0.9, Z + 1.7, STONE_D, 0.05, name="Ledge")
    bx(p, -20.4, -16.0, 0, 0.5, Z + 0.9, Z + 1.7, STONE_D, 0.05, name="Ledge")
    # skull piles at the foot
    for (x, y, zz, s) in ((-29.6, 0.7, -53.4, 1.3), (-31.0, 0.7, -52.6, 1.1), (-28.2, 0.65, -52.4, 1.0), (-29.7, 1.65, -53.2, 1.1),
                          (-18.6, 0.7, -53.2, 1.3), (-17.2, 0.7, -52.4, 1.0), (-19.9, 0.65, -52.3, 1.05), (-18.5, 1.6, -53.0, 1.05), (-24.0, 0.7, -52.6, 1.0),
                          (-22.5, 0.5, -52.2, 0.8)):
        skull_lite(p, x, y, zz, s)
    bone(p, (-26.0, 0.25, -52.4), (-23.4, 0.25, -51.9), 0.2)
    bone(p, (-25.3, 0.25, -51.8), (-23.0, 0.3, -52.6), 0.16)
    return p


@part_builder("Belfry")
def build_Belfry():
    p = dk.Part("Belfry")
    cx, cz = -86.0, -52.0
    frustum(p, cx, cz, 0, 14.0, 9.0, 9.0, 8.0, 8.0, COB_D, 0.06, name="Shaft")
    for y in (4.6, 9.2):
        bx(p, cx - 4.4 + y * 0.03, cx + 4.4 - y * 0.03, y, y + 0.35, cz - 4.4, cz + 4.4, STONE, 0.05, name="Band")
    # windows and door
    zf = cz + 4.5
    lancet(p, 'xy', cx, 0.0, 4.2, 2.2, zf - 0.05, 0.3, BLACK, 0.03, n=4, name="Door")
    arch_band(p, 'xy', cx, 1.1, 4.2 - 1.85, 1.85, 0.4, zf + 0.0, 0.45, STONE_L, 0.04, n=4, name="DoorArch")
    for (yy, w) in ((7.2, 1.3), (11.4, 1.3)):
        lancet(p, 'xy', cx, yy, yy + 2.7, w, zf - 0.15, 0.3, BLACK, 0.03, n=3, name="Slit")
    for sx in (-1, 1):
        lancet(p, 'yz', cz, 6.4, 9.6, 1.3, cx + sx * 4.3, 0.3, BLACK, 0.03, n=3, name="SlitSide")
    # belfry stage
    bx(p, cx - 3.9, cx + 3.9, 14.0, 14.5, cz - 3.9, cz + 3.9, STONE, 0.05, name="Floor")
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, cx + sx * 3.0 - 0.5, cx + sx * 3.0 + 0.5, 14.5, 20.0, cz + sz * 3.0 - 0.5, cz + sz * 3.0 + 0.5, BLACK_L, 0.05, name="Pier")
    for sz in (-1, 1):
        arch_band(p, 'xy', cx, 2.5, 15.8, 3.3, 0.7, cz + sz * 3.55, 0.7, STONE_L, 0.05, n=4, name="Louver")
    for sx in (-1, 1):
        arch_band(p, 'yz', cz, 2.5, 15.8, 3.3, 0.7, cx + sx * 3.55, 0.7, STONE_L, 0.05, n=4, name="Louver")
    # bell
    lathe(p, (cx, 15.0, cz), [(1.9, 0), (1.65, 0.6), (1.1, 2.6), (0.9, 3.3), (0.4, 3.9)], 8, GOLD, 0.04, name="Bell")
    bx(p, cx - 2.4, cx + 2.4, 18.9, 19.3, cz - 0.2, cz + 0.2, WOOD_D, 0.04, name="BellBeam")
    for sg in (-1, 1):
        bx(p, cx + sg * 2.3 - 0.2, cx + sg * 2.3 + 0.2, 14.5, 19.3, cz - 0.2, cz + 0.2, WOOD_D, 0.04, name="BellPost")
    dk.ball(p, (cx, 15.0, cz), 0.35, IRON, subdiv=1, name="Clapper")
    bx(p, cx - 4.5, cx + 4.5, 20.0, 20.8, cz - 4.5, cz + 4.5, STONE, 0.05, name="Cornice")
    # spire
    spire4(p, cx, 20.8, cz, 2.6, 9.6, PURP, 0.07, name="Spire")
    for sg in (-1, 1):
        bx(p, cx + sg * 2.5 - 0.15, cx + sg * 2.5 + 0.15, 21.0, 21.5, cz - 2.5, cz + 2.5, GOLD, 0.03, name="SpireBand")
        bx(p, cx - 2.5, cx + 2.5, 21.0, 21.5, cz + sg * 2.5 - 0.15, cz + sg * 2.5 + 0.15, GOLD, 0.03, name="SpireBand")
    for sg in (-1, 1):
        bx(p, cx + sg * 1.5 - 0.2, cx + sg * 1.5 + 0.2, 20.8, 23.2, cz + 2.4, cz + 2.5, PURP_L, 0.05, name="SpireRib")
    rod(p, (cx, 30.0, cz), (cx, 34.0, cz), 0.2, IRON, sides=4, name="Spike")
    bat(p, cx, 32.6, cz, 0.55, col=IRON)
    for sx in (-1, 1):
        for sz in (-1, 1):
            spire4(p, cx + sx * 4.1, 20.8, cz + sz * 4.1, 0.55, 2.2, PURP_D, 0.05, name="Pinnacle")
    for (dx, dz, sc) in ((-3.6, 4.2, 1.5), (0.0, 4.3, 1.7), (3.6, 4.2, 1.5)):
        hang_bat(p, cx + dx, 20.0, cz + dz, sc, ang=0)
    bat(p, cx + 1.2, 27.5, cz + 2.2, 0.55, col=IRON)
    return p


@part_builder("Hedge")
def build_Hedge():
    p = dk.Part("Hedge")
    HB = (92, 158, 100); HB2 = (62, 124, 78); HT = (110, 176, 116)
    for xs in (82.5, 90.5):
        bx(p, xs - 1.2, xs + 1.2, 0, 4.4, -26.0, -2.0, HB, 0.1, name="Wall")
        for z in (-24.0, -21.0, -18.0, -15.0, -12.0, -9.0, -6.0, -3.6):
            blob(p, (xs, 4.5, z), 1.35, HB2 if int(z) % 2 else HB, sy=0.95, sides=6, jitter=0.1, name="Clump")
        for z in (-22.5, -16.5, -10.5, -5.0):
            dk.cone(p, (xs, 5.2, z), 0.9, 2.6, HT, verts=4, jitter=0.07, name="Pike")
        inner = 1 if xs < 86 else -1
        for y in (1.0, 2.4):
            xa, xb = sorted((xs + inner * 1.2 - inner * 0.05, xs + inner * 1.2 + inner * 0.22)); bx(p, xa, xb, y, y + 0.55, -26.0, -2.0, HT, 0.08, name="Band")
        lathe(p, (xs, 0, -1.6), [(1.5, 0), (1.5, 3.6), (1.9, 3.8), (1.9, 4.6), (1.3, 4.8), (1.3, 5.7), (0.7, 5.9), (0.7, 6.5), (0, 7.4)], 6, HT, 0.08, name="GateTopiary")
    bx(p, 81.3, 91.7, 0, 4.4, -26.8, -24.4, HB, 0.1, name="BackWall")
    for z in (-25.6,):
        for x in (84.8, 88.2):
            blob(p, (x, 4.5, z), 1.3, HB2, sy=0.95, sides=6, jitter=0.1, name="Clump")
    for xs in (82.5, 90.5):
        lathe(p, (xs, 0, -25.6), [(1.5, 0), (1.5, 4.7), (1.9, 4.8), (1.9, 5.7), (1.3, 5.9), (1.3, 6.8), (0.75, 7.0), (0.75, 7.7), (0, 8.6)], 6, HT, 0.08, name="Tower")
    half = [(0, 8.0), (0.3, 8.9), (0.65, 8.0), (1.8, 8.5), (1.8, 6.9), (1.3, 6.3), (1.1, 7.0), (0.8, 6.0), (0.45, 6.5)]
    pts = [(86.5 + u, y) for u, y in half] + [(86.5, 4.5)] + [(86.5 - u, y) for u, y in reversed(half)]
    slab(p, pts, 1.4, 'xy', -25.6, HB2, 0.06, name="BatCut")
    for sg in (-1, 1):
        bx(p, 86.5 + sg * 0.4 - 0.18, 86.5 + sg * 0.4 + 0.18, 7.1, 7.5, -24.93, -24.82, BLOOD, 0, name="BatEye")
    bx(p, 86.0, 87.0, 6.5, 6.8, -24.93, -24.84, BONE, 0, name="BatFang")
    lathe(p, (86.5, 0, -9.0), [(1.35, 0), (1.35, 0.5), (1.0, 0.7), (1.0, 2.0), (1.3, 2.1), (1.3, 2.4)], 8, STONE, 0.05, name="Pedestal")
    bat(p, 86.5, 3.7, -9.0, 0.55, col=STONE_D)
    return p


@part_builder("Tomb")
def build_Tomb():
    p = dk.Part("Tomb")
    bx(p, 7.0, 13.0, 0, 0.6, -47.7, -45.1, STONE_L, 0.05, name="StepLow")
    bx(p, 7.5, 12.5, 0.6, 1.2, -47.7, -46.2, STONE, 0.05, name="StepHigh")
    bx(p, 5.7, 14.3, 0, 1.0, -54.3, -47.7, STONE_D, 0.05, name="Plinth")
    bx(p, 6.0, 14.0, 1.0, 8.0, -54.0, -48.0, STONE, 0.06, name="Body")
    bx(p, 5.3, 14.7, 8.0, 8.6, -54.7, -47.3, DARK, 0.05, name="Cornice")
    bx(p, 5.6, 14.4, 8.6, 9.1, -54.4, -47.6, STONE_D, 0.05, name="Roof")
    lancet(p, 'xy', 10.0, 1.2, 6.4, 3.0, -47.92, 0.2, BLACK, 0.03, n=4, name="Door")
    arch_band(p, 'xy', 10.0, 1.5, 4.2, 2.2, 0.5, -47.85, 0.36, STONE_L, 0.04, n=4, name="DoorArch")
    for x in (9.2, 10.0, 10.8):
        bx(p, x - 0.07, x + 0.07, 1.2, 5.6, -47.9, -47.8, IRON_L, 0, name="DoorBar")
    for sx in (6.8, 13.2):
        bx(p, sx - 0.45, sx + 0.45, 1.0, 8.0, -48.5, -47.9, STONE_L, 0.05, name="Pilaster")
        bx(p, sx - 0.6, sx + 0.6, 7.6, 8.0, -48.6, -47.8, STONE_D, 0.05, name="PilCap")
    for (xx, at) in ((6.0, 5.9), (14.0, 14.1)):
        lancet(p, 'yz', -51.0, 3.0, 6.2, 1.3, at, 0.2, BLACK, 0.03, n=3, name="Slit")
    skull(p, 10.0, 7.2, -47.7, 0.9, detail=1)
    for (x, zz) in ((5.9, -54.1), (14.1, -54.1), (5.9, -47.9), (14.1, -47.9)):
        spire4(p, x, 9.1, zz, 0.55, 1.5, STONE_L, 0.05, name="Finial")
    bx(p, 8.8, 11.2, 9.1, 9.7, -51.9, -50.1, STONE_L, 0.05, name="AngelBase")
    angel(p, 10.0, 9.7, -51.0, 1.0, col=STONE_L)
    bx(p, 8.8, 11.2, 6.9, 7.6, -47.85, -47.7, GOLD, 0.03, name="Plaque")
    bx(p, 9.0, 11.0, 1.2, 1.28, -47.2, -45.2, CRIM, 0.04, name="Carpet")
    bat(p, 7.2, 9.6, -47.7, 0.5, col=BLACK_L)
    bat(p, 12.8, 9.6, -47.7, 0.5, col=BLACK_L)
    for x in (5.0, 15.0):
        lathe(p, (x, 0, -47.0), [(0.95, 0), (0.95, 0.5), (0.6, 0.75), (1.1, 1.6), (1.2, 2.0), (0.9, 2.7), (0.6, 2.9), (0.75, 3.2)], 8, DARK, 0.05, name="Urn")
        flame(p, x, 3.2, -47.0, 0.4, 1.0)
    for (x, y0, h) in ((6.2, 2.0, 4.4), (13.7, 3.0, 3.6)):
        bx(p, x - 0.3, x + 0.3, y0, y0 + h, -48.05, -47.9, HEDGE, 0.08, name="Ivy")
    return p


@part_builder("Moon")
def build_Moon():
    p = dk.Part("Moon")
    cx, cy, z = -46.0, 15.5, -57.0
    bx(p, -52.0, -40.0, 0, 0.8, -58.4, -55.6, DARK, 0.05, name="Base")
    bx(p, -51.7, -40.3, 0.8, 1.3, -58.0, -56.0, STONE, 0.05, name="BaseTop")
    for xs in (-50.6, -41.4):
        bx(p, xs - 0.6, xs + 0.6, 1.3, 12.0, z - 0.6, z + 0.6, IRON, 0.04, name="Post")
        bx(p, xs - 0.9, xs + 0.9, 1.3, 2.3, z - 0.9, z + 0.9, IRON_L, 0.04, name="PostFoot")
        spire4(p, xs, 11.9, z, 0.7, 1.3, IRON_L, 0.04, name="PostTip")
    dk.cyl(p, (cx, cy, z), 5.0, 1.2, MOON, axis='z', verts=12, jitter=0.03, name="Moon")
    annulus(p, (cx, cy, z), 5.9, 4.9, 0.9, IRON, sides=12, jitter=0.04, name="Ring")
    annulus(p, (cx, cy, z), 4.9, 4.45, 1.3, BLOOD_D, sides=12, jitter=0.03, name="BloodRing")
    for (dx, dy, r) in ((-2.4, 2.2, 1.0), (2.6, -1.6, 0.85), (-0.6, -3.0, 0.6), (3.0, 2.4, 0.5)):
        dk.cyl(p, (cx + dx, cy + dy, z + 0.63), r, 0.14, MOON_D, axis='z', verts=6, jitter=0.03, name="Crater")
    bat(p, cx - 0.4, cy + 0.3, z + 0.7, 1.2, col=BLACK)
    for a in (35, 62, 118, 145):
        ar = math.radians(a)
        rod(p, (cx + 5.7 * math.cos(ar), cy + 5.7 * math.sin(ar), z), (cx + 7.3 * math.cos(ar), cy + 7.3 * math.sin(ar), z), 0.4, IRON, sides=4, r2=0.04, name="Spike")
    rod(p, (cx, cy + 5.7, z), (cx, 23.0, z), 0.45, IRON, sides=4, r2=0.04, name="Spike")
    hang_bat(p, cx, cy - 5.8, z, 1.0, col=BLACK_L)
    return p


@part_builder("Organ")
def build_Organ():
    p = dk.Part("Organ")
    bx(p, 79.0, 94.0, 0, 2.0, 50.7, 52.3, BLACK, 0.04, name="PipeBase")
    pts = [(79.1, 2.0), (93.9, 2.0), (93.9, 13.0), (91.0, 15.0), (88.8, 17.0), (86.6, 18.4), (84.4, 17.0), (82.2, 15.0), (79.1, 13.0)]
    slab(p, pts, 0.5, 'xy', 51.0, BLACK_L, 0.04, name="PipeBack")
    for x, top in zip((80.0, 82.2, 84.4, 86.6, 88.8, 91.0, 93.2), (14, 16, 18, 19, 18, 16, 14)):
        lathe(p, (x, 2.0, 51.5), [(0.8, 0), (0.8, top - 2.0), (0.62, top - 1.75)], 8, GOLD, 0.05, name="Pipe")
        bx(p, x - 0.42, x + 0.42, 3.6, 4.5, 52.25, 52.38, IRON, 0, name="Mouth")
        bx(p, x - 0.82, x + 0.82, 8.0, 8.3, 51.4, 52.35, GOLD_D, 0.03, name="PipeBand")
    bx(p, 79.0, 93.0, 0, 5.0, 52.0, 56.0, BLACK, 0.05, name="Case")
    bx(p, 78.5, 93.5, 5.0, 5.8, 51.8, 56.2, DARK, 0.05, name="CaseTop")
    for xc in (81.5, 86.0, 90.5):
        lancet(p, 'xy', xc, 0.5, 2.9, 2.6, 56.05, 0.12, BLACK_L, 0.04, ah=1.2, n=3, name="Panel")
    bx(p, 80.0, 92.0, 2.95, 3.4, 56.0, 57.3, BLACK_L, 0.04, name="Desk")
    bx(p, 82.2, 89.8, 3.4, 3.62, 56.3, 57.1, BONE, 0.03, name="Keys")
    for k in (0, 1, 3, 4, 5):
        bx(p, 82.6 + k * 1.0, 82.95 + k * 1.0, 3.62, 3.78, 56.7, 57.05, IRON, 0, name="Sharp")
    for xk in (80.6, 81.4, 90.6, 91.4):
        bx(p, xk - 0.2, xk + 0.2, 3.7, 4.3, 56.0, 56.35, GOLD, 0.03, name="Stop")
    bx(p, 84.4, 87.6, 5.8, 7.6, 55.2, 55.45, BLACK_L, 0.03, name="MusicStand")
    bx(p, 84.7, 87.3, 6.1, 7.3, 55.45, 55.52, BONE, 0.03, name="Sheet")
    candle(p, 79.5, 5.8, 54.0, h=1.3, r=0.32)
    candle(p, 92.5, 5.8, 54.0, h=1.0, r=0.32)
    skull(p, 89.5, 6.3, 54.6, 0.85, ang=-20, detail=1)
    for xl in (84.0, 88.0):
        for zl in (56.5, 57.6):
            bx(p, xl - 0.12, xl + 0.12, 0.0, 1.0, zl - 0.12, zl + 0.12, WOOD_D, 0.04, name="BenchLeg")
    bx(p, 83.5, 88.5, 1.0, 1.4, 56.2, 57.8, WOOD, 0.05, name="BenchSeat")
    bx(p, 83.7, 88.3, 1.4, 1.8, 56.4, 57.6, CRIM, 0.05, name="Cushion")
    bx(p, 84.0, 88.0, 0, 0.25, 55.9, 56.6, GOLD_D, 0.03, name="Pedals")
    return p


@part_builder("Throne")
def build_Throne():
    p = dk.Part("Throne")
    cx = -38.0
    bx(p, -45.0, -31.0, 0, 1.2, -30.0, -18.0, DARK, 0.05, name="Dais")
    bx(p, -42.0, -34.0, 1.2, 2.4, -29.0, -21.0, STONE, 0.05, name="DaisTop")
    bx(p, -39.6, -36.4, 1.2, 1.3, -21.0, -18.0, CRIM, 0.04, name="Carpet")
    bx(p, -39.6, -36.4, 1.3, 2.4, -21.1, -21.0, CRIM, 0.04, name="CarpetStep")
    for (x, zz) in ((-44.2, -18.8), (-31.8, -18.8)):
        skull(p, x, 1.65, zz, 0.8, detail=0)
    # wings behind the back
    wing = [(1.9, 6.5), (1.9, 13.5), (3.6, 15.0), (5.6, 13.6), (5.0, 12.2), (5.4, 10.8), (4.2, 10.4), (4.4, 8.8), (3.0, 9.0), (2.6, 7.4)]
    for sg in (-1, 1):
        slab(p, [(cx + sg * u, y) for u, y in wing][::sg], 0.3, 'xy', -27.9, PURP, 0.06, name="Wing")
        rod(p, (cx + sg * 2.0, 13.0, -27.6), (cx + sg * 5.5, 13.6, -27.6), 0.18, PURP_D, sides=4, name="WingBone")
        rod(p, (cx + sg * 2.0, 12.6, -27.6), (cx + sg * 4.3, 8.9, -27.6), 0.15, PURP_D, sides=4, name="WingBone")
    lancet(p, 'xy', cx, 3.5, 14.2, 4.4, -27.2, 1.0, BLACK, 0.04, ah=3.6, n=5, name="Back")
    lancet(p, 'xy', cx, 4.8, 13.4, 3.2, -26.62, 0.24, BLACK_L, 0.04, ah=2.6, n=5, name="BackPanel")
    arch_band(p, 'xy', cx, 1.7, 10.8, 2.6, 0.28, -26.55, 0.28, GOLD, 0.03, n=4, name="BackTrim")
    bx(p, cx - 1.98, cx - 1.7, 4.8, 10.8, -26.7, -26.4, GOLD, 0.03, name="BackTrim")
    bx(p, cx + 1.7, cx + 1.98, 4.8, 10.8, -26.7, -26.4, GOLD, 0.03, name="BackTrim")
    bat(p, cx, 9.6, -26.45, 0.8, col=GOLD_D)
    dk.cone(p, (cx, 14.0, -27.2), 0.5, 1.3, GOLD, verts=4, name="Finial")
    for sg in (-1, 1):
        bx(p, cx + sg * 2.0 - 0.15, cx + sg * 2.0 + 0.15, 11.0, 14.0, -27.5, -26.9, BLACK_L, 0.04, name="BackRib")
    # seat
    bx(p, -39.8, -36.2, 2.4, 3.5, -26.7, -23.3, BLACK, 0.04, name="SeatBase")
    bx(p, -39.7, -36.3, 3.5, 4.8, -26.6, -23.4, CRIM, 0.05, name="Cushion")
    bx(p, -39.8, -36.2, 3.5, 3.65, -23.45, -23.3, GOLD, 0.03, name="Piping")
    for sg in (-1, 1):
        xa = cx + sg * 2.35
        bx(p, xa - 0.4, xa + 0.4, 2.4, 5.4, -26.7, -23.3, BLACK, 0.04, name="Arm")
        skull(p, xa, 5.7, -23.4, 0.55, detail=0)
    torch_stand(p, -44.0, -20.0, 5.8, flame_h=1.7)
    torch_stand(p, -32.0, -20.0, 5.8, flame_h=1.7)
    return p


@part_builder("Statue")
def build_Statue():
    p = dk.Part("Statue")
    cx, cz = -70.0, -18.0
    frustum(p, cx, cz, 0, 2.8, 12.0, 12.0, 10.6, 10.6, DARK, 0.05, name="Plinth")
    bx(p, cx - 4.5, cx + 4.5, 2.8, 4.0, cz - 4.5, cz + 4.5, STONE, 0.05, name="PlinthTop")
    bx(p, cx - 1.8, cx + 1.8, 3.0, 3.8, cz + 4.5, cz + 4.58, BLACK, 0, name="Plaque")
    for sx in (-1, 1):
        for sz in (-1, 1):
            skull(p, cx + sx * 5.3, 3.3, cz + sz * 5.3, 0.9, ang=sx * 20, detail=0)
    # legs and feet
    for sg in (-1, 1):
        x = cx + sg * 2.2
        blob(p, (x, 6.0, cz - 0.8), 1.7, STONE, sy=1.0, sides=6, jitter=0.06, name="Haunch")
        rod(p, (x, 5.6, cz - 0.4), (x, 4.5, cz + 1.9), 0.7, STONE, sides=5, name="Shin")
        bx(p, x - 0.75, x + 0.75, 4.0, 4.6, cz + 1.2, cz + 3.4, STONE_D, 0.05, name="Foot")
        for k in (-1, 0, 1):
            rod(p, (x + k * 0.4, 4.3, cz + 3.3), (x + k * 0.45, 4.05, cz + 4.3), 0.22, BONE_D, sides=4, r2=0.03, name="Claw")
    dk.ball(p, (cx, 8.8, cz - 0.2), 2.6, STONE, scale=(1.0, 1.25, 0.85), subdiv=1, jitter=0.07, name="Torso")
    for k, y in enumerate((9.0, 10.1, 11.2)):
        bx(p, cx - 1.9 + k * 0.1, cx + 1.9 - k * 0.1, y, y + 0.5, cz + 1.6, cz + 1.95, STONE_L if k % 2 == 0 else STONE_D, 0.05, name="ChestPlate")
    bx(p, cx - 1.0, cx + 1.0, 12.2, 13.5, cz - 0.6, cz + 0.8, STONE_D, 0.05, name="Neck")
    for sg in (-1, 1):
        sh = (cx + sg * 3.0, 11.6, cz - 0.2)
        blob(p, sh, 1.4, STONE_L, sy=0.9, sides=6, jitter=0.05, name="Shoulder")
        rod(p, (sh[0], sh[1] - 0.3, sh[2]), (cx + sg * 3.6, 8.6, cz + 1.3), 0.75, STONE, sides=5, name="UpperArm")
        rod(p, (cx + sg * 3.6, 8.6, cz + 1.3), (cx + sg * 2.8, 6.3, cz + 2.9), 0.65, STONE, sides=5, name="ForeArm")
        bx(p, cx + sg * 2.8 - 0.55, cx + sg * 2.8 + 0.55, 5.6, 6.5, cz + 2.5, cz + 3.5, STONE_D, 0.05, name="Hand")
        for k in (-1, 0, 1):
            rod(p, (cx + sg * 2.8 + k * 0.33, 5.9, cz + 3.4), (cx + sg * 2.8 + k * 0.38, 4.9, cz + 4.1), 0.17, BONE_D, sides=4, r2=0.03, name="Finger")
    # head
    dk.ball(p, (cx, 14.3, cz + 0.5), 1.9, STONE_L, scale=(1.0, 0.9, 1.0), subdiv=1, jitter=0.06, name="Head")
    bx(p, cx - 0.9, cx + 0.9, 13.3, 14.2, cz + 1.8, cz + 3.1, STONE, 0.05, name="Snout")
    bx(p, cx - 0.85, cx + 0.85, 13.3, 13.45, cz + 2.0, cz + 3.12, BLACK, 0, name="Mouth")
    bx(p, cx - 1.6, cx + 1.6, 14.9, 15.35, cz + 1.8, cz + 2.5, STONE_D, 0.05, name="Brow")
    for sg in (-1, 1):
        bx(p, cx + sg * 0.75 - 0.32, cx + sg * 0.75 + 0.32, 14.4, 14.85, cz + 2.3, cz + 2.5, BLOOD, 0, name="Eye")
        rod(p, (cx + sg * 0.55, 13.5, cz + 2.9), (cx + sg * 0.55, 12.65, cz + 2.95), 0.22, BONE, sides=4, r2=0.03, name="Fang")
        rod(p, (cx + sg * 1.4, 15.0, cz + 0.3), (cx + sg * 3.1, 17.4, cz - 0.2), 0.6, STONE, sides=4, r2=0.04, name="Ear")
        rod(p, (cx + sg * 0.9, 15.7, cz + 0.4), (cx + sg * 1.4, 17.3, cz - 0.1), 0.4, BONE_D, sides=4, name="Horn")
        rod(p, (cx + sg * 1.4, 17.3, cz - 0.1), (cx + sg * 1.1, 18.6, cz - 0.7), 0.28, BONE_D, sides=4, r2=0.04, name="Horn")
    # wings
    zw = cz - 2.4
    wing = [(1.6, 13.0), (4.8, 17.0), (8.4, 19.9), (9.9, 17.4), (8.0, 15.0), (8.6, 12.9), (6.4, 11.4), (6.2, 9.6), (3.8, 8.8), (1.8, 7.0)]
    for sg in (-1, 1):
        slab(p, [(cx + sg * u, y) for u, y in wing][::sg], 0.5, 'xy', zw, BLACK_L, 0.06, name="Membrane")
        rod(p, (cx + sg * 1.8, 12.8, zw + 0.3), (cx + sg * 8.4, 19.6, zw + 0.3), 0.45, STONE_D, sides=4, r2=0.28, name="WingArm")
        for (fu, fy) in ((9.8, 17.5), (8.5, 13.0), (6.2, 9.7)):
            rod(p, (cx + sg * 8.2, 19.4, zw + 0.3), (cx + sg * fu, fy, zw + 0.3), 0.2, STONE_D, sides=4, r2=0.1, name="WingFinger")
    # tail
    for (A, Bp, r0, r1) in (((cx + 0.3, 5.2, cz - 2.2), (cx + 2.8, 4.6, cz - 3.8), 0.6, 0.5), ((cx + 2.8, 4.6, cz - 3.8), (cx + 4.5, 4.5, cz - 2.2), 0.5, 0.4),
                            ((cx + 4.5, 4.5, cz - 2.2), (cx + 4.4, 4.5, cz + 0.2), 0.4, 0.05)):
        rod(p, A, Bp, r0, STONE_D, sides=5, r2=r1, name="Tail")
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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_VampireCrypt.json"))
    for part in bp["Parts"]:
        if part["Id"] != "Ground":
            FOOT[part["Id"]] = roblox_box(part["Pieces"])
    ids = [pp["Id"] for pp in bp["Parts"]]
    BUILDERS.sort(key=lambda b: ids.index(b[0]) if b[0] in ids else 99)
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
        view(allm, "stage_VampireCrypt_34.png", shiba=spot, az=205, el=40, size=(1800, 1000), zoom=1.55)
        view(allm, "stage_VampireCrypt_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_VampireCrypt_34.png", "stage_VampireCrypt_top.png", "stage_VampireCrypt.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
