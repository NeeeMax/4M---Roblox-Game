"""Viking Longhouse decor models (theme VikingLonghouse): builds the 20 decor parts around the tenth Shiba (Viking Shiba).

Run:  blender --background --factory-startup --python build_VikingLonghouse.py -- <outdir>   (use an absolute outdir)
Writes into <outdir> (default: out/VikingLonghouse next to this script):
  Decor_VikingLonghouse_<PartId>.fbx, preview_<PartId>.png per part, stage_VikingLonghouse.png (3/4 view + top view stacked),
  stage_VikingLonghouse_34.png and stage_VikingLonghouse_top.png (the two views separately).
Every model is built in the stage frame (see decorkit.py) and, before export, fitted to the union box of its blueprint pieces so that
the game's fitToPieces scale stays about 1. Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures,
no neon. Previews are rendered the way the player sees the stage: from the road (+z) with +x to the right.
Env: VL_ONLY=Part1,Part2 builds only those parts; VL_DBG=<folder> adds extra debug views of each part.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "VikingLonghouse"
R = random.Random(10)
pi = math.pi
DBG = os.environ.get("VL_DBG")
ONLY = set(os.environ.get("VL_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
TIM = (112, 78, 52); TIM_D = (72, 50, 36); TIM_L = (150, 108, 72); TIM_X = (176, 138, 96)
TURF = (88, 134, 62); TURF_D = (62, 106, 48); TURF_L = (126, 168, 82)
STONE = (132, 134, 132); STONE_D = (88, 92, 98); STONE_L = (172, 172, 166)
STEEL = (178, 186, 196); IRON = (52, 54, 62); IRON_L = (84, 88, 98)
RED = (192, 50, 44); RED_D = (140, 34, 32); BONE = (238, 230, 210); BONE_D = (206, 196, 170)
GOLD = (238, 186, 58); GOLD_D = (192, 140, 36); BLUE = (48, 92, 150); BLUE_L = (84, 130, 188)
WATER = (56, 124, 172); WATER_D = (40, 98, 150); WATER_L = (120, 190, 226); FOAM = (226, 238, 242)
SAND = (214, 196, 150); GRAVEL = (170, 158, 132); DIRT = (170, 148, 110)
FIRE = (240, 132, 42); FIRE_Y = (252, 204, 70); FIRE_R = (206, 70, 36)
FUR = (150, 118, 88); FUR_D = (110, 80, 58); FUR_L = (196, 164, 126)
GRASS = (98, 150, 72); GRASS_D = (76, 128, 62); GRASS_L = (128, 176, 86)


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


@part_builder("Ground")
def build_Ground():
    p = dk.Part("Ground")
    dk.box(p, (0, 0.1, 0), (190, 0.2, 130), GRASS_D, name="Base")
    # grass: a 10x10 quad grid whose corners carry a slowly changing green (smooth, no visible tiles)
    nx, nz, cs = 19, 13, 10.0
    pts = [(-95 + i * cs, 0.3, -65 + j * cs) for j in range(nz + 1) for i in range(nx + 1)]
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, j * (nx + 1) + i + nx + 2, j * (nx + 1) + i + nx + 1)
             for j in range(nz) for i in range(nx)]
    g = _obj(p, "Grass", pts, faces, GRASS, closed=False, up=True)
    gouraud(g, lambda x, z: mix(GRASS_D, GRASS_L, max(0.0, min(1.0, 0.5 + 0.95 * noise(x, z) + 0.15 * math.sin(x * 0.9 + z * 0.7)))))

    def blotch(cx, cz, rx, rz, color, y, k=9, name="Patch"):
        a0 = R.uniform(0, 2 * pi)
        pts2 = [(cx + rx * (0.7 + 0.5 * R.random()) * math.cos(a0 + 2 * pi * i / k), cz + rz * (0.7 + 0.5 * R.random()) * math.sin(a0 + 2 * pi * i / k)) for i in range(k)]
        return flat(p, pts2, y, color, 0.05, name=name)
    n = 0
    while n < 10:                                         # organic patches of lighter and darker grass
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        if x > 52 and z < 16:
            continue
        blotch(x, z, R.uniform(4, 9), R.uniform(3, 7), (112, 160, 78) if n % 2 else (92, 144, 70), 0.315)
        n += 1

    # a ploughed crop field right of the feast table (furrows and rows of young barley)
    for k in range(10):
        x0 = 30.5 + k * 2.4
        flat(p, [(x0, -24), (x0 + 1.2, -24), (x0 + 1.2, -8), (x0, -8)], 0.34, (128, 98, 66), 0.05, name="Furrow")
        flat(p, [(x0 + 1.2, -24), (x0 + 2.4, -24), (x0 + 2.4, -8), (x0 + 1.2, -8)], 0.345, (150, 176, 84) if k % 2 else (132, 164, 72), 0.06, name="CropRow")
    # the fjord along the right edge
    shore = [(60, -65), (63, -57), (59, -48), (61.5, -39), (57, -30), (60.5, -21), (58, -12), (61, -4), (65, 3), (62.5, 9),
             (71, 12), (81, 10.5), (95, 13)]
    water = shore + [(95, -65)]
    cen = (80, -26)

    def grow(poly, d):
        out = []
        for (x, z) in poly:
            vx, vz = x - cen[0], z - cen[1]
            L = math.hypot(vx, vz) or 1.0
            out.append((min(95, max(-95, x + d * vx / L)), min(65, max(-65, z + d * vz / L))))
        return out
    flat(p, grow(shore, 4.5) + [(95, -65)], 0.33, SAND, 0.05, name="Beach")
    flat(p, grow(shore, 1.5) + [(95, -65)], 0.36, FOAM, 0.03, name="Foam")
    flat(p, water, 0.39, WATER, 0.04, name="Water")
    deep = [(cen[0] + (x - cen[0]) * 0.6, cen[1] + (z - cen[1]) * 0.85) for (x, z) in shore[1:-1]]
    flat(p, deep + [(95, 8), (95, -60)], 0.42, WATER_D, 0.05, name="Deep")
    for k in range(22):
        wx, wz = R.uniform(66, 91), R.uniform(-60, 8)
        flat(p, [(wx - 2.2, wz), (wx + 2.2, wz), (wx + 1.8, wz + 0.55), (wx - 1.8, wz + 0.55)], 0.45, WATER_L, 0.05, name="Wave")
    for (ix, iz, ir) in ((86.5, -58, 5.0), (86.5, 5, 4.2)):  # two little islets with a rock each
        k = 9
        flat(p, [(ix + (ir + 1.6) * math.cos(2 * pi * i / k + 0.3), iz + (ir + 1.6) * 0.9 * math.sin(2 * pi * i / k + 0.3)) for i in range(k)], 0.43, FOAM, 0.03, name="IsletFoam")
        flat(p, [(ix + ir * math.cos(2 * pi * i / k + 0.3), iz + ir * 0.9 * math.sin(2 * pi * i / k + 0.3)) for i in range(k)], 0.46, SAND, 0.04, name="IsletSand")
        flat(p, [(ix + ir * 0.62 * math.cos(2 * pi * i / k + 0.9), iz + ir * 0.55 * math.sin(2 * pi * i / k + 0.9)) for i in range(k)], 0.48, GRASS_L, 0.04, name="IsletGrass")
        rock(p, (ix + 0.8, 0.36, iz - 0.4), 0.7, STONE, scale=(1, 0.35, 1), name="IsletRock")
    for k in range(12):                                   # foam dashes along the shore
        z = -62 + k * 6.0 + R.uniform(-1, 1)
        x = 61.5 + 1.2 * math.sin(k * 1.7)
        flat(p, [(x, z - 1.4), (x + 0.5, z - 1.4), (x + 0.5, z + 1.4), (x, z + 1.4)], 0.47, (250, 252, 255), 0.02, name="FoamDash")

    # pebble yard before the longhouse, trampled earth around the busy spots
    flat(p, [(-84, -36.5), (-70, -37), (-50, -37), (-36, -36.5), (-34.5, -22), (-37, -4), (-48, 3), (-62, 5), (-76, 3), (-84, -6),
             (-85.5, -22)], 0.34, GRAVEL, 0.05, name="Yard")
    for (cx, cz, rx, rz) in ((28, 4, 10.5, 9.5), (14, -14, 13, 7.5), (-80, 34, 11, 9), (47, 22, 10, 8), (-78, 12, 9, 8), (10, 46, 6, 6),
                             (-19, -47, 10.5, 10.5), (-43, 24, 8, 8), (-58, 40, 11, 8)):
        blotch(cx, cz, rx, rz, DIRT, 0.36, k=9, name="Dirt")
    for k in range(8):
        qx, qz = R.uniform(-82, -38), R.uniform(-34, 2)
        s = R.uniform(0.3, 0.55)
        dk.box(p, (qx, 0.45, qz), (s * 1.4, s * 0.4, s), STONE_D if k % 2 else STONE, rot=(0, R.uniform(0, 90), 0), jitter=0.1, name="Pebble")
    # rune circle around the Shiba's platform (dark stone ring with gold marks)
    sx, sz = -60, -26
    for k in range(16):
        a0, a1 = 2 * pi * k / 16, 2 * pi * (k + 1) / 16
        flat(p, [(sx + 6.3 * math.cos(a0), sz + 6.3 * math.sin(a0)), (sx + 7.7 * math.cos(a0), sz + 7.7 * math.sin(a0)),
                 (sx + 7.7 * math.cos(a1), sz + 7.7 * math.sin(a1)), (sx + 6.3 * math.cos(a1), sz + 6.3 * math.sin(a1))], 0.37,
             STONE_D if k % 2 else STONE, 0.05, name="RuneRing")
    for k in range(8):
        a = 2 * pi * (k + 0.5) / 8
        c, s = math.cos(a), math.sin(a)
        flat(p, [(sx + 6.4 * c - 0.3 * s, sz + 6.4 * s + 0.3 * c), (sx + 7.6 * c - 0.3 * s, sz + 7.6 * s + 0.3 * c),
                 (sx + 7.6 * c + 0.3 * s, sz + 7.6 * s - 0.3 * c), (sx + 6.4 * c + 0.3 * s, sz + 6.4 * s - 0.3 * c)], 0.39, GOLD, 0.03, name="RuneMark")

    def free(x, z, m=2.5):
        if (x > 54 and z < 15) or (28 < x < 57 and -27 < z < -5):
            return False
        for (lo, hi) in FOOT.values():
            if lo[0] - m < x < hi[0] + m and lo[2] - m < z < hi[2] + m:
                return False
        return abs(x) < 93 and abs(z) < 63
    n = 0
    while n < 6:
        x, z = R.uniform(-93, 93), R.uniform(-63, 63)
        if free(x, z):
            dk.cone(p, (x, 0.3, z), R.uniform(0.45, 0.7), R.uniform(0.2, 0.3), mix(GRASS_D, GRASS_L, R.random()), verts=5, jitter=0.08, name="Tuft")
            n += 1
    n = 0
    while n < 18:                                         # flower clumps
        cx, cz = R.uniform(-90, 54), R.uniform(-60, 60)
        if not free(cx, cz, 4):
            continue
        col = [(250, 214, 70), (245, 245, 240), (236, 110, 150), (110, 150, 235)][R.randrange(4)]
        for k in range(4):
            fx, fz = cx + R.uniform(-2.2, 2.2), cz + R.uniform(-2.2, 2.2)
            if free(fx, fz, 1):
                flat(p, [(fx - 0.45, fz - 0.45), (fx + 0.45, fz - 0.45), (fx + 0.45, fz + 0.45), (fx - 0.45, fz + 0.45)], 0.38, col, 0.05, name="Flower")
        n += 1
    for k in range(6):
        x, z = R.uniform(-90, 52), R.uniform(-60, 60)
        if free(x, z, 3):
            rock(p, (x, 0.3, z), R.uniform(0.6, 0.95), STONE, scale=(1, 0.35, 1), rot=(0, R.uniform(0, 90), 0), name="Boulder")
    for k in range(5):                                   # boulders and reeds on the shore
        z = R.uniform(-62, 9)
        rock(p, (58 + R.uniform(-1, 2), 0.3, z), R.uniform(0.6, 0.9), STONE_D, scale=(1.1, 0.35, 1), name="ShoreRock")
        dk.cone(p, (56.5 + R.uniform(-1, 1), 0.3, z + R.uniform(-3, 3)), 0.35, 0.28, (150, 170, 90), verts=4, name="Reed")
    return p


@part_builder("Longhouse")
def build_Longhouse():
    p = dk.Part("Longhouse")
    X0, X1, ZB, ZF = -88.0, -32.0, -61.0, -37.0
    bx(p, -88.6, -31.4, 0, 0.7, -61.6, -36.4, STONE_D, 0.1, name="Plinth")
    bx(p, -87.2, -32.8, 0.65, 0.8, -60.8, -38.2, (62, 44, 32), 0.05, name="Floor")
    bx(p, X0, X1, 0.7, 8.0, ZB, ZB + 1.2, TIM_D, 0.05, name="BackWall")
    # log walls: front (two halves around the door), sides
    logwall(p, 'x', -88.6, -65, -37.6, 0.7, 8.0, 1.2, 7, TIM, TIM_L)
    logwall(p, 'x', -55, -31.4, -37.6, 0.7, 8.0, 1.2, 7, TIM, TIM_L)
    logwall(p, 'z', -61.6, -36.4, -87.4, 0.7, 8.0, 1.2, 7, TIM, TIM_L)
    logwall(p, 'z', -61.6, -36.4, -32.6, 0.7, 8.0, 1.2, 7, TIM, TIM_L)
    # door frame: carved posts with gold bands, lintel
    for sx in (-1, 1):
        cx = -60 + sx * 5.2
        bx(p, cx - 0.7, cx + 0.7, 0, 8.8, -38.4, -36.9, TIM_D, 0.04, name="DoorPost")
        for yb in (1.6, 4.4, 7.2):
            bx(p, cx - 0.85, cx + 0.85, yb, yb + 0.45, -38.55, -36.75, GOLD_D, 0.04, name="Band")
        dk.ball(p, (cx, 9.4, -37.6), 0.8, GOLD, subdiv=1, jitter=0.05, name="Knob")
    bx(p, -65, -55, 5.8, 8.0, -38.3, -36.9, TIM_D, 0.04, name="Lintel")
    for k in range(3):
        bx(p, -62.6 + k * 2.4, -61.6 + k * 2.4, 6.4, 7.4, -36.95, -36.7, GOLD, 0.04, name="LintelRune")
    # interior seen through the door: hearth with fire, bench, a red shield on the back wall
    bx(p, -62.4, -57.6, 0.75, 1.5, -52.5, -46.5, STONE_D, 0.08, name="Hearth")
    fire(p, -60, 1.5, -49.5, 2.0, 3.4)
    bx(p, -66, -54, 0.75, 2.2, -60.6, -58.6, TIM_L, 0.05, name="Bench")
    shield(p, -60, 5.2, -59.7, 2.3, RED, GOLD_D, boss=GOLD)
    # turf roof, gable walls with a gold sun disc, ridge, dragon heads
    turf_roof(p, 'x', -90, -30, -49, 12.6, 8.3, 15.4, 0.8, n=5, N=10, name="HallRoof")
    for xg in (-87.4, -32.6):
        gable_end(p, 'x', xg, -49, 12.0, 7.9, 14.8, 1.2, TIM_D)
    for xd in ():
        dk.cyl(p, (xd, 11.0, -49), 1.7, 0.3, GOLD, axis='x', verts=6, jitter=0.04, name="Sun")
    bx(p, -90, -30, 14.8, 15.7, -49.45, -48.55, TIM_D, 0.05, name="Ridge")
    # smoke louver on the ridge
    bx(p, -63, -57, 15.5, 15.9, -50.2, -47.8, TIM_D, 0.05, name="LouverBase")
    for lx in (-62.6, -57.4):
        for lz in (-49.8, -48.2):
            rod(p, (lx, 15.8, lz), (lx, 16.9, lz), 0.18, TIM_L, 4, name="LouverPost")
    bx(p, -63.5, -56.5, 16.9, 17.2, -50.6, -47.4, TIM_L, 0.05, name="LouverRoof")
    rock(p, (-60, 17.15, -49), 0.45, (240, 240, 245), scale=(1.3, 0.8, 1), jitter=0.04, name="LouverSmoke")
    for k in range(14):                                  # dragon-spine fins along the ridge
        slab(p, [(15.9, -49.45), (15.9, -48.55), (16.95 if k % 2 == 0 else 16.5, -49.0)], 0.4, 'yz', -86 + k * 4.0, GOLD_D if k % 2 else TIM_D, 0.04, name="Fin")
    dk.cyl(p, (-60, 15.7, -49), 0.75, 60, TURF_L, axis="x", verts=6, jitter=0.06, name="RidgeRoll")
    for xe in (-89.7, -30.3):
        for sg in (-1, 1):
            dk.box(p, (xe, 11.95, -49 + sg * 6.3), (0.6, 0.7, 14.5), TIM_D, rot=(sg * 29.4, 0, 0), jitter=0.04, name="Barge")
    bx(p, -90, -30, 7.5, 8.5, -61.8, -61.4, TIM_D, 0.05, name="Fascia")
    bx(p, -90, -30, 7.5, 8.5, -36.6, -36.2, TIM_D, 0.05, name="Fascia")
    for xn in (-88.8, -31.2):
        bx(p, xn - 0.5, xn + 0.5, 15.2, 16.4, -49.35, -48.65, TIM_D, 0.05, name="Neck")
    dragon_head(p, -88.9, 16.3, -49, 1.6, -1, GOLD)
    dragon_head(p, -31.1, 16.3, -49, 1.6, 1, GOLD)
    # wall shields on the front
    cols = [RED, BONE, BLUE, GOLD]
    for k in range(4):
        shield(p, -84 + k * 4.2, 4.4, -36.8, 1.4, cols[k % 4], IRON_L, sides=6)
        shield(p, -50 + k * 4.2, 4.4, -36.8, 1.4, cols[(k + 2) % 4], IRON_L, sides=6)
    return p


@part_builder("Smithy")
def build_Smithy():
    p = dk.Part("Smithy")
    bx(p, -88, -72, 0, 0.4, 28, 40, STONE_D, 0.08, name="Floor")
    for i in range(4):                                   # stone walls in courses
        y0 = 0.4 + i * 1.65
        col = STONE if i % 2 == 0 else STONE_L
        bx(p, -88, -72, y0, y0 + 1.6, 28.0, 29.2 + (0.12 if i % 2 else 0), col, 0.1, name="BackWall")
        bx(p, -88, -86.8 - (0.12 if i % 2 else 0), y0, y0 + 1.6, 29.2, 40, col, 0.1, name="SideWall")
    # forge: hearth block with a glowing mouth, tapering chimney with smoke
    bx(p, -86.5, -81.5, 0.4, 4.0, 29.2, 33.2, STONE_D, 0.08, name="Hearth")
    bx(p, -85.7, -82.3, 0.9, 2.5, 33.15, 33.35, IRON, 0.02, name="Mouth")
    bx(p, -85.3, -82.7, 0.9, 1.7, 33.3, 33.45, FIRE, 0.04, name="Embers")
    bx(p, -84.7, -83.3, 1.7, 2.2, 33.3, 33.45, FIRE_Y, 0.04, name="Embers")
    frustum(p, -84, 30.4, 4.0, 12.6, 4.8, 2.4, 3.0, 2.4, STONE, 0.08, name="Chimney")
    bx(p, -85.8, -82.2, 12.6, 13.0, 29.1, 31.7, STONE_D, 0.05, name="ChimneyCap")
    rock(p, (-84.0, 13.4, 30.4), 0.6, (200, 200, 205), scale=(1.2, 1, 1), jitter=0.05, name="Smoke")
    rock(p, (-83.2, 13.5, 30.0), 0.5, (170, 170, 178), scale=(1, 1, 1), jitter=0.05, name="Smoke")
    # anvil on a stump
    dk.cyl(p, (-77, 0.7, 34), 0.95, 1.4, TIM, verts=7, jitter=0.08, name="Stump")
    bx(p, -77.4, -76.6, 1.4, 2.3, 33.7, 34.3, IRON, 0.04, name="AnvilWaist")
    bx(p, -78.2, -75.8, 2.3, 3.2, 33.4, 34.6, IRON_L, 0.04, name="AnvilTop")
    bx(p, -79.3, -78.2, 2.7, 3.2, 33.7, 34.3, IRON_L, 0.04, name="AnvilHorn")
    bx(p, -76.9, -75.9, 3.2, 3.3, 33.6, 34.2, FIRE_R, 0.03, name="HotIron")
    # bellows and a coal box beside the hearth
    bx(p, -81.5, -78.5, 0.4, 1.0, 30, 32, TIM_D, 0.05, name="Bench")
    bx(p, -81.3, -78.7, 1.0, 1.9, 30.2, 31.8, RED_D, 0.05, name="Bellows")
    rod(p, (-81.4, 1.4, 31), (-82.6, 1.4, 31.6), 0.25, IRON, 5, name="Nozzle")
    # quench barrel with water, grindstone, coal heaps
    barrel(p, -74, 0.4, 30.6, 1.0, 2.0, TIM)
    dk.cyl(p, (-74, 2.38, 30.6), 0.85, 0.06, WATER, verts=6, name="Water")
    bx(p, -75.2, -74.4, 0.4, 1.7, 36, 37, TIM_D, 0.05, name="GrindFrame")
    bx(p, -73.2, -72.4, 0.4, 1.7, 36, 37, TIM_D, 0.05, name="GrindFrame")
    dk.cyl(p, (-73.8, 1.7, 36.5), 1.1, 0.7, STONE_L, axis='x', verts=8, jitter=0.06, name="Grindstone")
    rock(p, (-86.3, 0.9, 37), 1.3, IRON, scale=(1, 0.7, 1), name="Coal")
    rock(p, (-84.9, 0.7, 38.5), 0.9, IRON_L, scale=(1, 0.7, 1), name="Coal")
    # tools on a rack on the back wall
    bx(p, -80.8, -74.4, 4.5, 4.9, 29.2, 29.75, TIM_D, 0.05, name="Rack")
    for k, x in enumerate((-80.2, -78.6, -77.0, -75.4)):
        bx(p, x - 0.15, x + 0.15, 2.4, 4.5, 29.3, 29.6, TIM_L, 0.05, name="Handle")
        bx(p, x - 0.5, x + 0.5, 2.0 if k % 2 else 3.8, 2.7 if k % 2 else 4.4, 29.3, 29.65, STEEL if k < 3 else IRON_L, 0.05, name="Head")
    # roof: shingle boards over the back, open rafters over the front so the forge shows
    for i in range(3):
        t = -6.1 + 2.03 * (i + 0.5)
        dk.box(p, (-80, 7.0 - t * math.sin(math.radians(9.5)), 34 + t * math.cos(math.radians(9.5))), (17.5, 0.7, 1.95),
               TIM_L if i % 2 else TIM, rot=(9.5, 0, 0), jitter=0.07, name="Shingles")
    for x in (-87.6, -84.0, -80.0, -76.0, -72.4):
        dk.box(p, (x, 6.9 - 4.1 * math.sin(math.radians(9.5)), 34 + 4.1 * math.cos(math.radians(9.5)) + 0.0), (0.5, 0.6, 4.2), TIM_D, rot=(9.5, 0, 0), jitter=0.05, name="Rafter")
    for x in (-87.4, -72.6):
        post(p, x, 39.4, 0, 5.9, 0.45, TIM_D, 6, jitter=0.05, name="FrontPost")
    bx(p, -88, -72, 5.3, 6.1, 39.0, 39.8, TIM_D, 0.05, name="Header")
    # hanging sign: a gold anvil on an iron arm
    rod(p, (-80.2, 5.3, 39.95), (-80.2, 4.0, 39.95), 0.05, IRON, 3, name="SignChain")
    bx(p, -80.9, -79.5, 3.6, 4.0, 39.9, 40.0, GOLD, 0.03, name="SignAnvil")
    bx(p, -80.5, -79.9, 3.2, 3.6, 39.9, 40.0, GOLD_D, 0.03, name="SignAnvil")
    return p


@part_builder("FirePit")
def build_FirePit():
    p = dk.Part("FirePit")
    cx, cz = 28, 4
    dk.cyl(p, (cx, 0.2, cz), 6.6, 0.4, STONE_D, verts=12, jitter=0.07, name="Disc")
    for k in range(10):                                  # ring of stones
        a = 2 * pi * k / 10
        dk.box(p, (cx + 4.6 * math.cos(a), 0.7, cz + 4.6 * math.sin(a)), (1.7, 1.0 + 0.2 * (k % 2), 1.4),
               STONE if k % 2 else STONE_L, rot=(0, -math.degrees(a), 0), jitter=0.1, name="RingStone")
    for k in range(3):                                   # logs
        dk.cyl(p, (cx, 1.05, cz), 0.42, 4.2, TIM_D if k % 2 else TIM, axis='x', verts=6, rot=(0, k * 60, 0), jitter=0.08, name="Log")
    fire(p, cx, 1.3, cz, 1.8, 3.3)
    for k in range(3):                                   # tripod and hanging cauldron
        a = 2 * pi * (k + 0.25) / 3
        rod(p, (cx + 3.7 * math.cos(a), 0.4, cz + 3.7 * math.sin(a)), (cx, 6.2, cz), 0.24, TIM_D, 5, r2=0.18, name="Leg")
    rod(p, (cx, 6.2, cz), (cx, 5.2, cz), 0.07, IRON, 4, name="Chain")
    lathe(p, (cx, 3.2, cz), [(0.8, 0), (1.5, 0.5), (1.85, 1.3), (1.9, 2.0), (1.7, 2.4)], 7, IRON, 0.05, name="Cauldron")
    dk.cyl(p, (cx, 5.5, cz), 1.5, 0.08, (88, 52, 36), verts=7, name="Stew")
    for sx, sz in ((22, 4), (34, 4), (28, -2), (28, 10)):  # log stumps to sit on
        o = dk.cyl(p, (sx, 0.7, sz), 1.2, 1.4, TIM_D, verts=7, jitter=0.07, name="Seat")
        recolor(o, lambda c, n, i: TIM_X if n[1] > 0.9 else None, 0.05)
    for k in range(5):                                   # sparks / embers around the fire
        a = R.uniform(0, 2 * pi)
        dk.box(p, (cx + 2.5 * math.cos(a), 0.45, cz + 2.5 * math.sin(a)), (0.4, 0.12, 0.4), FIRE_R, rot=(0, 30 * k, 0), name="Ember")
    return p


def hull_ring(X, z, w, yt, t=0.5):
    te = min(t, w * 0.45)
    outer = [(-w, yt), (-0.95 * w, 0.55 * yt + 0.2), (-0.6 * w, 0.9), (-0.2 * w, 0.15), (0.2 * w, 0.15), (0.6 * w, 0.9),
             (0.95 * w, 0.55 * yt + 0.2), (w, yt)]
    inner = [(w - te, yt), (0.95 * w - te, 0.55 * yt + 0.5), (0.55 * w, 1.3), (-0.55 * w, 1.3), (-(0.95 * w - te), 0.55 * yt + 0.5),
             (-(w - te), yt)]
    return [(X + u, y, z) for u, y in outer + inner]


@part_builder("Longship")
def build_Longship():
    p = dk.Part("Longship")
    X = 78.0
    secs = [(-46.6, 0.6, 8.8), (-43.5, 2.4, 6.4), (-38.5, 4.0, 4.9), (-30, 4.8, 4.4), (-22, 4.5, 4.4), (-16.5, 3.4, 5.8), (-13.4, 1.2, 7.0)]
    hull = loft(p, [hull_ring(X, z, w, yt) for z, w, yt in secs], TIM, 0.05, name="Hull")

    def hcol(c, n, i):
        if abs(n[2]) > 0.8:
            return TIM_D
        if n[1] > 0.7:
            return GOLD_D if c[1] > 3.2 else TIM_X
        if n[1] < -0.3:
            return TIM_D
        if (c[0] - X) * n[0] > 0:
            return RED if c[1] > 3.7 else (TIM if int(c[1] / 1.2) % 2 == 0 else TIM_L)
        return TIM_L
    recolor(hull, hcol, 0.05)
    # foam collar around the hull
    left = [(X - (w + 1.0), z) for z, w, yt in secs]
    right = [(X + (w + 1.0), z) for z, w, yt in secs][::-1]
    flat(p, left + right, 0.6, FOAM, 0.04, name="Foam")
    # dragon prow: neck and head
    slab(p, [(7.0, -46.9), (9.7, -47.5), (9.7, -46.3), (7.0, -45.5)], 0.8, 'yz', X, RED, 0.05, name="Neck")
    hr = lambda z, w, y0, y1: [(X - w, y0, z), (X + w, y0, z), (X + 0.9 * w, y1, z), (X - 0.9 * w, y1, z)]
    loft(p, [hr(-46.6, 0.85, 9.5, 11.9), hr(-47.8, 0.75, 9.5, 11.5), hr(-49.1, 0.5, 9.9, 11.0)], RED, 0.05, name="Head")
    bx(p, X - 0.55, X + 0.55, 9.0, 9.55, -49.0, -47.4, GOLD_D, 0.05, name="Jaw")
    bx(p, X - 0.95, X + 0.95, 11.5, 11.9, -48.1, -46.6, RED_D, 0.05, name="Brow")
    for sx in (-1, 1):
        bx(p, X + sx * 0.7 - 0.12, X + sx * 0.7 + 0.12, 10.7, 11.4, -48.5, -47.9, BONE, 0.03, name="Eye")
        bx(p, X + sx * 0.7 - 0.14, X + sx * 0.7 + 0.14, 10.9, 11.2, -48.4, -48.1, IRON, 0.03, name="Pupil")
        bx(p, X + sx * 0.45 - 0.1, X + sx * 0.45 + 0.1, 9.55, 10.0, -49.0, -48.8, BONE, 0.03, name="Tooth")
        rod(p, (X + sx * 0.5, 11.6, -47.2), (X + sx * 0.9, 12.7, -46.0), 0.18, GOLD, 5, r2=0.06, name="Horn")
    for k in range(3):                                   # spiky fin down the neck
        slab(p, [(8.0 + k * 0.6, -46.4 + k * 0.1), (8.5 + k * 0.6, -45.6 + k * 0.1), (8.9 + k * 0.6, -46.4 + k * 0.1)], 0.3, 'yz', X, GOLD, 0.04, name="Fin")
    # curled stern post
    slab(p, [(5.8, -13.9), (8.4, -13.3), (8.4, -12.2), (7.5, -12.0), (7.5, -12.8), (5.8, -12.9)], 0.8, 'yz', X, RED, 0.05, name="Tail")
    dk.ball(p, (X, 8.0, -12.4), 0.5, GOLD, subdiv=1, name="TailKnob")
    # mast, yard, striped sail
    rod(p, (X, 1.5, -30), (X, 23.6, -30), 0.5, TIM_D, 6, r2=0.38, jitter=0.05, name="Mast")
    dk.ball(p, (X, 23.7, -30), 0.5, GOLD, subdiv=1, name="MastKnob")
    rod(p, (X - 5.8, 20.8, -30), (X + 5.8, 20.8, -30), 0.35, TIM_D, 5, name="Yard")
    for k in range(7):
        u = (k + 0.5) / 7
        belly = 0.9 * (1 - (2 * u - 1) ** 2)
        bx(p, 73.0 + 10 * k / 7 + 0.02, 73.0 + 10 * (k + 1) / 7 - 0.02, 11.6, 20.5, -30.2 + belly, -29.8 + belly, RED if k % 2 == 0 else BONE, 0.04, name="Sail")
    slab(p, [(23.1, -30.0), (23.1, -27.6), (22.4, -30.0)], 0.12, 'yz', X, RED, 0.03, name="Pennant")
    for sx in (-1, 1):                                   # shrouds
        for z in (-33, -27):
            rod(p, (X, 19.8, -30), (X + sx * 4.2, 4.6, z), 0.1, BONE_D, 3, name="Shroud")
    rod(p, (X, 23.0, -30), (X, 9.6, -46.7), 0.1, BONE_D, 3, name="Forestay")
    rod(p, (X, 23.0, -30), (X, 7.6, -13.6), 0.1, BONE_D, 3, name="Backstay")
    # shields along both rails
    cols = [(BLUE, BONE), (BONE, RED), (GOLD, BLUE)]
    for k, z in enumerate((-36, -30, -24)):
        shield(p, 73.2, 4.3, z, 0.95, cols[k][0], IRON_L, axis='x', sides=6, thick=0.4)
        shield(p, 82.8, 4.3, z, 0.95, cols[(k + 1) % 3][0], IRON_L, axis='x', sides=6, thick=0.4)
    # inside: thwarts, a chest, oars
    for z in (-40.5, -34, -28, -22, -18):
        w = 3.0 if abs(z + 30) < 12 else 1.6
        bx(p, X - w, X + w, 2.5, 3.0, z - 0.5, z + 0.5, TIM_L, 0.06, name="Thwart")
    bx(p, X - 1.4, X + 1.4, 1.3, 2.6, -21.2, -19.6, RED_D, 0.05, name="Chest")
    bx(p, X - 1.5, X + 1.5, 2.6, 2.9, -21.3, -19.5, GOLD_D, 0.05, name="ChestLid")
    for sx in (-1, 1):
        rod(p, (X + sx * 2.6, 2.1, -43), (X + sx * 2.6, 2.6, -17), 0.18, TIM_L, 4, name="Oar")
    return p


@part_builder("Feast")
def build_Feast():
    p = dk.Part("Feast")
    ROAST = (178, 108, 52)
    plank_row(p, 5, 23, -16, -12, 2.6, 3.2, 3, 'x', TIM_L, gap=0.12, jitter=0.07, name="Top")
    for x in (7.6, 20.4):                                # carved end boards instead of trestles
        slab(p, [(0, -15.6), (0, -12.4), (1.0, -12.4), (1.5, -12.9), (2.6, -12.7), (2.6, -15.3), (1.5, -15.1), (1.0, -15.6)], 0.7, 'yz', x, TIM_D, 0.05, name="EndBoard")
        bx(p, x - 0.4, x + 0.4, 1.0, 1.35, -15.1, -12.9, GOLD_D, 0.03, name="EndTrim")
    bx(p, 7.6, 20.4, 0.7, 1.0, -14.4, -13.6, TIM_D, 0.05, name="Stretcher")
    for z0, z1 in ((-18.6, -17.0), (-11.0, -9.4)):       # benches
        bx(p, 5, 23, 1.0, 1.5, z0, z1, TIM, 0.07, name="Bench")
        for x in (7.5, 20.5):
            bx(p, x - 0.35, x + 0.35, 0, 1.0, z0 + 0.2, z1 - 0.2, TIM_D, 0.05, name="BenchLeg")
    bx(p, 14.6, 18.6, 1.5, 1.75, -18.5, -17.1, FUR, 0.07, name="Pelt")     # wolf pelts thrown over the benches
    bx(p, 8.0, 11.0, 1.5, 1.72, -10.9, -9.5, FUR_L, 0.07, name="Pelt")
    bx(p, 5.6, 22.4, 3.2, 3.28, -14.9, -13.1, RED, 0.03, name="Runner")
    for k, x in enumerate((6.5, 9.5, 18.5, 21.5, 7.5, 20.0)):
        z = -15.0 if k < 4 else -12.8
        dk.cyl(p, (x, 3.3, z), 0.62, 0.12, STEEL, verts=6, jitter=0.04, name="Plate")
    for x, z in ((9, -12.6), (17.5, -15.2), (20, -13.0), (7.6, -14.8)):
        dk.cyl(p, (x, 3.6, z), 0.36, 0.8, TIM_L, verts=6, top_radius=0.42, jitter=0.05, name="Mug")
        bx(p, x + 0.35, x + 0.6, 3.4, 3.9, z - 0.1, z + 0.1, TIM_D, 0.03, name="Handle")
    # two drinking horns with gold rims lying on the table
    for (x, z, s) in ((11.0, -12.6, 1), (16.6, -15.4, -1)):
        rod(p, (x, 3.45, z), (x + s * 1.1, 3.55, z - 0.4 * s), 0.3, BONE, 5, r2=0.12, name="DrinkingHorn")
        dk.cyl(p, (x, 3.45, z), 0.34, 0.2, GOLD, axis='x', verts=5, name="HornRim")
    # roast boar on a platter
    bx(p, 11.2, 16.8, 3.2, 3.42, -15.1, -12.9, STEEL, 0.04, name="Platter")
    dk.ball(p, (14.2, 4.3, -14), 1.0, ROAST, scale=(1.9, 0.95, 1.0), subdiv=1, jitter=0.08, name="Boar")
    dk.ball(p, (12.1, 4.2, -14), 0.62, ROAST, scale=(1.1, 1, 1), subdiv=1, jitter=0.06, name="BoarHead")
    dk.ball(p, (11.6, 4.1, -14), 0.28, RED, subdiv=1, name="Apple")
    for sx in (-1, 1):
        for sz in (-1, 1):
            rod(p, (14.2 + sx * 1.0, 3.4, -14 + sz * 0.5), (14.2 + sx * 1.1, 4.0, -14 + sz * 0.7), 0.16, ROAST, 4, name="Trotter")
    # fruit bowl and bread
    lathe(p, (19.2, 3.2, -14), [(0.3, 0), (0.9, 0.25), (1.0, 0.6)], 6, TIM_D, 0.05, name="Bowl")
    for k, col in enumerate((RED, GOLD, (110, 170, 70))):
        dk.ball(p, (18.7 + 0.5 * k, 3.95, -14 + 0.25 * (k % 2)), 0.34, col, subdiv=1, name="Fruit")
    bx(p, 5.8, 7.0, 3.2, 3.7, -13.6, -12.6, TIM_X, 0.05, name="Bread")
    # torch stands at two corners
    for (x, z) in ((5.7, -9.9), (22.6, -18.0)):
        rod(p, (x, 0, z), (x, 4.2, z), 0.14, IRON, 5, name="TorchPole")
        lathe(p, (x, 4.1, z), [(0.15, 0), (0.45, 0.25), (0.6, 0.6)], 6, IRON, 0.04, name="TorchBowl")
        fire(p, x, 4.65, z, 0.5, 0.55)
    # the mead barrel
    barrel(p, 25.4, 0, -14, 1.2, 3.0, TIM)
    dk.cyl(p, (25.4, 3.02, -14), 1.0, 0.06, IRON_L, verts=6, name="Lid")
    rod(p, (25.4, 1.4, -12.8), (25.4, 1.2, -12.1), 0.18, GOLD_D, 4, name="Tap")
    return p


@part_builder("Jetty")
def build_Jetty():
    p = dk.Part("Jetty")
    for k in range(14):                                  # deck planks across the jetty
        bx(p, 58 + 2 * k + 0.07, 58 + 2 * k + 1.93, 1.15, 1.65, -4.5, 0.5, TIM if k % 2 else TIM_L, 0.08, name="Plank")
    bx(p, 58, 86, 0.75, 1.15, -3.9, -3.3, TIM_D, 0.05, name="Stringer")
    bx(p, 58, 86, 0.75, 1.15, -0.9, -0.3, TIM_D, 0.05, name="Stringer")
    for x in (62, 72, 82):
        for z in (-4.2, 0.2):
            rod(p, (x, -0.6, z), (x, 2.4, z), 0.45, TIM_D, 6, jitter=0.06, name="Post")
            bx(p, x - 0.5, x + 0.5, 1.9, 2.1, z - 0.47, z + 0.47, IRON_L, 0.04, name="RopeBand")
    for z in (-4.2, 0.2):                                # rope rails between the posts
        for (xa, xb) in ((62, 72), (72, 82)):
            rod(p, (xa, 2.25, z), (xb, 2.05, z), 0.09, BONE_D, 4, name="RopeRail")
    barrel(p, 66, 1.65, -3, 1.1, 2.2, TIM)
    barrel(p, 68.6, 1.65, -3.4, 1.1, 2.2, TIM_L)
    bx(p, 75.8, 78.2, 1.65, 3.15, -1.8, 0.6, TIM_D, 0.06, name="Crate")
    bx(p, 76.8, 78.4, 3.15, 4.6, -1.6, 0.0, TIM, 0.06, name="Crate")
    for x in (76.1, 77.9):                               # crate slats
        bx(p, x - 0.12, x + 0.12, 1.65, 3.15, -1.85, 0.65, TIM_L, 0.04, name="Slat")
    for k, x in enumerate((75.9, 76.5, 77.1, 77.7)):     # silver fish heaped in the open crate
        slab(p, [(x, 3.15), (x + 0.3, 3.5), (x, 3.95), (x - 0.3, 3.5)], 0.14, 'xy', -0.5 - 0.5 * (k % 2) - 0.0, STEEL if k % 2 else (150, 172, 196), 0.04, name="CrateFish")
    rock(p, (80.2, 2.35, -2.9), 0.8, (214, 196, 150), scale=(1.0, 1.0, 1.0), name="Sack")
    rock(p, (81.4, 2.2, -1.6), 0.7, (196, 176, 130), scale=(1.0, 0.9, 1.0), name="Sack")
    # lantern post at the end, a second small lantern near the shore
    rod(p, (85, 1.65, -2), (85, 5.4, -2), 0.3, TIM_D, 5, name="LampPost")
    bx(p, 84.5, 85.5, 5.5, 6.5, -2.5, -1.5, FIRE_Y, 0.03, name="Light")
    bx(p, 84.3, 85.7, 5.3, 5.5, -2.7, -1.3, IRON, 0.03, name="LampBase")
    bx(p, 84.3, 85.7, 6.5, 6.7, -2.7, -1.3, IRON, 0.03, name="LampTop")
    for sx in (-1, 1):
        for sz in (-1, 1):
            rod(p, (85 + sx * 0.6, 5.5, -2 + sz * 0.6), (85 + sx * 0.6, 6.5, -2 + sz * 0.6), 0.07, IRON, 4, name="LampBar")
    rod(p, (62, 2.4, 0.2), (62, 3.6, 0.2), 0.07, IRON, 4, name="HookPole")
    bx(p, 61.6, 62.4, 3.6, 4.2, -0.2, 0.6, FIRE_Y, 0.03, name="SmallLight")
    bx(p, 61.5, 62.5, 4.2, 4.3, -0.3, 0.7, IRON, 0.03, name="SmallLightTop")
    # a heap of fishing net, a coil of rope, a bollard
    rock(p, (60.5, 1.9, -0.8), 1.2, (96, 112, 96), scale=(1.5, 0.45, 1.0), name="Net")
    lathe(p, (63.5, 1.65, -1.8), [(1.0, 0), (1.0, 0.3), (0.5, 0.35), (0.5, 0.0)], 8, BONE_D, 0.06, name="RopeCoil")
    return p


@part_builder("ShieldWall")
def build_ShieldWall():
    p = dk.Part("ShieldWall")
    n = 20
    w = 29.0 / n
    for k in range(n):                                   # palisade of pointed stakes
        h = 4.0 + 0.35 * ((k * 7) % 3)
        stake(p, -89.5 + w * (k + 0.5), 55.0, 0, h, w * 0.94, 0.9, TIM if k % 2 else TIM_L, tip=0.9, name="Stake")
    for yb in (0.9, 3.3):
        bx(p, -89.8, -60.4, yb, yb + 0.5, 55.45, 55.75, TIM_D, 0.05, name="Rail")
    for x in (-89, -82, -68, -61):
        rod(p, (x, 0, 55), (x, 6.0, 55), 0.7, TIM_D, 6, r2=0.6, jitter=0.05, name="Post")
        dk.ball(p, (x, 6.2, 55), 0.55, GOLD, subdiv=1, name="Cap")
    cols = [(RED, GOLD_D), (BONE, IRON_L), (BLUE, GOLD_D), (GOLD, RED_D), (RED, IRON_L), (BONE, GOLD_D)]
    for k, x in enumerate((-86, -81, -76, -71, -66, -62.5)):
        shield(p, x, 2.3, 55.55, 1.55 if k < 5 else 1.25, cols[k][0], cols[k][1], sides=6, thick=0.4, boss=GOLD)
    for x in (-85.5, -78.5, -71.5, -64.5):               # spears above the wall
        rod(p, (x, 3.8, 55), (x, 6.1, 55), 0.12, TIM_L, 4, name="Shaft")
        dk.cone(p, (x, 6.0, 55), 0.3, 0.8, STEEL, verts=4, name="SpearHead")
    return p


@part_builder("Storehouse")
def build_Storehouse():
    p = dk.Part("Storehouse")
    for x in (-82.5, -73.5):                             # stilts with stone caps (the mice cannot climb these)
        for z in (7.5, 16.5):
            rod(p, (x, 0, z), (x, 2.2, z), 0.4, TIM_D, 6, r2=0.5, jitter=0.05, name="Stilt")
            dk.cyl(p, (x, 2.1, z), 0.95, 0.25, STONE, verts=7, jitter=0.05, name="StiltCap")
    bx(p, -83.5, -72.5, 2.25, 2.6, 6.5, 17.5, TIM_D, 0.05, name="Floor")
    bx(p, -83.4, -72.6, 2.6, 7.6, 6.7, 7.3, TIM_D, 0.05, name="BackWall")
    ZF = 16.9                                            # the front (door) wall faces the road, +z
    logwall(p, 'x', -83.9, -79.3, ZF, 2.6, 7.6, 1.2, 5, TIM, TIM_L)
    logwall(p, 'x', -76.7, -72.1, ZF, 2.6, 7.6, 1.2, 5, TIM, TIM_L)
    bx(p, -79.3, -76.7, 6.2, 7.6, 16.3, 17.5, TIM_D, 0.05, name="DoorTop")
    logwall(p, 'z', 6.1, 17.9, -82.9, 2.6, 7.6, 1.2, 5, TIM, TIM_L)
    logwall(p, 'z', 6.1, 17.9, -73.1, 2.6, 7.6, 1.2, 5, TIM, TIM_L)
    # carved door with iron straps and a ring
    bx(p, -79.6, -76.4, 2.6, 6.4, 17.15, 17.5, TIM_D, 0.05, name="Door")
    bx(p, -79.9, -79.6, 2.6, 6.6, 16.9, 17.6, TIM_L, 0.04, name="Frame")
    bx(p, -76.4, -76.1, 2.6, 6.6, 16.9, 17.6, TIM_L, 0.04, name="Frame")
    for y in (3.4, 5.4):
        bx(p, -79.5, -76.5, y, y + 0.35, 17.5, 17.65, IRON, 0.03, name="Strap")
    dk.ball(p, (-77.2, 4.3, 17.7), 0.2, GOLD, subdiv=1, name="Ring")
    for sx in (-1, 1):                                   # small shuttered window beside the door
        pass
    bx(p, -82.2, -80.6, 4.4, 5.8, 17.5, 17.65, IRON, 0.02, name="Window")
    bx(p, -82.45, -82.15, 4.3, 5.9, 17.5, 17.8, TIM_L, 0.03, name="Shutter")
    bx(p, -80.65, -80.35, 4.3, 5.9, 17.5, 17.8, TIM_L, 0.03, name="Shutter")
    # turf roof, gables, ridge, tufts
    turf_roof(p, 'x', -84.2, -71.8, 12, 6.5, 7.9, 12.2, 0.7, n=4, N=5, name="StoreRoof")
    for xg in (-83.0, -73.0):
        gable_end(p, 'x', xg, 12, 5.8, 7.5, 11.9, 0.8, TIM_D)
    bx(p, -84.2, -71.8, 11.9, 12.75, 11.65, 12.35, TIM_D, 0.05, name="Ridge")
    for k in range(5):
        dk.cone(p, (-83 + 2.5 * k, 12.0, 11.2 + 1.2 * (k % 2)), 0.45, 0.65, TURF_L, verts=5, jitter=0.1, name="RoofTuft")
    for xe in (-84.2, -71.8):                            # crossed gable boards
        rod(p, (xe, 11.3, 12 - 1.4), (xe, 12.65, 12 + 1.4), 0.12, TIM_D, 4, name="Cross")
        rod(p, (xe, 11.3, 12 + 1.4), (xe, 12.65, 12 - 1.4), 0.12, TIM_D, 4, name="Cross")
    # four steps up to the door
    for k in range(4):
        z1 = 21.5 - 0.85 * k
        bx(p, -79.7, -76.3, -0.4, 0.65 * (k + 1), z1 - 0.85 - (0.75 if k == 3 else 0), z1, TIM_L if k % 2 else TIM, 0.06, name="Step")
    # sacks of grain beside the door
    rock(p, (-74.6, 0.85, 19.0), 0.95, (214, 196, 150), scale=(1.0, 1.1, 1.0), name="Sack")
    rock(p, (-73.9, 0.7, 20.4), 0.8, (196, 176, 130), scale=(1.0, 1.0, 1.0), name="Sack")
    return p


@part_builder("Watchtower")
def build_Watchtower():
    p = dk.Part("Watchtower")
    lx = (74.4, 81.6)
    lz = (38.4, 45.6)
    for x in lx:
        for z in lz:
            rod(p, (x, 0, z), (x, 14.4, z), 0.6, TIM_D, 6, r2=0.5, jitter=0.05, name="Leg")
            bx(p, x - 0.9, x + 0.9, 0, 0.5, z - 0.9, z + 0.9, STONE, 0.06, name="Foot")
    for (y0, y1) in ((0.8, 7.6), (7.6, 14.2)):          # beams around and diagonal braces per level
        for z in lz:
            bx(p, 74.4, 81.6, y1 - 0.3, y1 + 0.1, z - 0.2, z + 0.2, TIM, 0.05, name="Beam")
            rod(p, (74.4, y0, z), (81.6, y1, z), 0.17, TIM_L, 4, name="Brace")
            rod(p, (81.6, y0, z), (74.4, y1, z), 0.17, TIM_L, 4, name="Brace")
        for x in lx:
            bx(p, x - 0.2, x + 0.2, y1 - 0.3, y1 + 0.1, 38.4, 45.6, TIM, 0.05, name="Beam")
            rod(p, (x, y0, 38.4), (x, y1, 45.6), 0.17, TIM_L, 4, name="Brace")
            rod(p, (x, y0, 45.6), (x, y1, 38.4), 0.17, TIM_L, 4, name="Brace")
    plank_row(p, 72.8, 83.2, 36.8, 47.2, 14.2, 15.0, 6, 'x', TIM, gap=0.1, jitter=0.07, name="Deck")
    # railing round the platform
    for x in (72.9, 78, 83.1):
        for z in (36.9, 47.1):
            rod(p, (x, 15.0, z), (x, 16.5, z), 0.17, TIM_D, 4, name="RailPost")
    for z in (41.97,):
        rod(p, (72.9, 15.0, z), (72.9, 16.5, z), 0.17, TIM_D, 4, name="RailPost")
        rod(p, (83.1, 15.0, z), (83.1, 16.5, z), 0.17, TIM_D, 4, name="RailPost")
    bx(p, 72.8, 83.2, 16.4, 16.7, 36.8, 37.1, TIM_L, 0.05, name="Rail")
    bx(p, 72.8, 83.2, 16.4, 16.7, 46.9, 47.2, TIM_L, 0.05, name="Rail")
    bx(p, 72.8, 73.1, 16.4, 16.7, 36.8, 47.2, TIM_L, 0.05, name="Rail")
    bx(p, 82.9, 83.2, 16.4, 16.7, 36.8, 47.2, TIM_L, 0.05, name="Rail")
    # lookout cabin with arrow slits
    bx(p, 74, 82, 15.0, 21.0, 38.0, 38.6, TIM_D, 0.05, name="CabinBack")
    logwall(p, 'x', 73.6, 82.4, 45.7, 15.0, 21.0, 0.6, 4, TIM, TIM_L, bulge=0.2)
    logwall(p, 'z', 37.6, 46.1, 74.3, 15.0, 21.0, 0.6, 4, TIM, TIM_L, bulge=0.2)
    logwall(p, 'z', 37.6, 46.1, 81.7, 15.0, 21.0, 0.6, 4, TIM, TIM_L, bulge=0.2)
    for x in (76.0, 80.0):
        bx(p, x - 0.35, x + 0.35, 17.6, 19.6, 46.0, 46.2, IRON, 0.02, name="Slit")
    shield(p, 78, 19.2, 46.2, 1.2, RED, GOLD_D, sides=6, thick=0.3)
    # roof
    gable(p, 'z', 37, 47, 78, 7.65, 18.4, 23.6, 0.8, TIM_D, TIM, n=4, jitter=0.06)
    for zg in (38.2, 45.8):
        gable_end(p, 'z', zg, 78, 4.4, 20.8, 23.0, 0.4, TIM_D)
    bx(p, 77.6, 78.4, 23.5, 24.4, 37, 47, TIM_D, 0.05, name="Ridge")
    # ladder
    for x in (77.3, 78.7):
        rod(p, (x, 0, 47.8), (x, 15.0, 47.8), 0.12, TIM_D, 4, name="LadderRail")
    for k in range(9):
        bx(p, 77.3, 78.7, 0.9 + k * 1.55, 1.1 + k * 1.55, 47.6, 48.0, TIM_L, 0.05, name="Rung")
    # fire basket on the platform corner
    lathe(p, (82.4, 15.0, 37.9), [(0.3, 0), (0.7, 0.5), (0.95, 1.1)], 6, IRON, 0.04, name="Brazier")
    rod(p, (82.4, 15.0, 37.9), (82.4, 15.3, 37.9), 0.2, IRON, 4, name="Stand")
    fire(p, 82.4, 16.0, 37.9, 0.7, 1.4)
    return p


@part_builder("FishRacks")
def build_FishRacks():
    p = dk.Part("FishRacks")
    fish_cols = [STEEL, (150, 172, 196), (206, 210, 220), (122, 150, 176)]
    for z, off in ((18, 0.0), (26, 0.55)):
        for x in (64, 80):
            rod(p, (x, 0, z), (x, 6.0, z), 0.35, TIM_D, 5, jitter=0.05, name="RackPost")
            rod(p, (x, 0.3, z - 0.3), (x, 4.0, z), 0.16, TIM_L, 4, name="Strut")
            rod(p, (x, 0.3, z + 0.3), (x, 4.0, z), 0.16, TIM_L, 4, name="Strut")
        bx(p, 63.5, 80.5, 5.55, 6.05, z - 0.25, z + 0.25, TIM, 0.05, name="Bar")
        if z == 18:
            bx(p, 63.5, 80.5, 3.4, 3.65, z - 0.2, z + 0.2, TIM_L, 0.05, name="LowBar")
        for k in range(9 if z == 18 else 7):             # hanging fish (the front rack stays high so the boat shows)
            x = 64.6 + k * (1.75 if z == 18 else 2.25) + off
            yt = 5.5 if (k % 2 == 0 or z != 18) else 3.9
            slab(p, [(x, yt), (x + 0.45, yt - 1.0), (x, yt - 2.0), (x - 0.45, yt - 1.0)], 0.16, 'xy', z, fish_cols[(k + int(z)) % 4], 0.05, name="Fish")
            slab(p, [(x, yt - 1.7), (x + 0.3, yt - 2.2), (x - 0.3, yt - 2.2)], 0.1, 'xy', z, fish_cols[(k + int(z)) % 4], 0.05, name="FishTail")
    # upturned rowing boat
    secs = [(67.0, 0.4, 0.6), (68.5, 1.5, 1.7), (72.0, 1.9, 2.2), (75.5, 1.5, 1.7), (77.0, 0.4, 0.6)]
    ring = lambda x, w, h: [(x, 0.0, 22 - w), (x, 0.9 * h, 22 - 0.85 * w), (x, h, 22), (x, 0.9 * h, 22 + 0.85 * w), (x, 0.0, 22 + w)]
    boat = loft(p, [ring(x, w, h) for x, w, h in secs], TIM_D, 0.06, name="Boat")
    recolor(boat, lambda c, n, i: (RED_D if 0.7 < c[1] < 1.4 and abs(n[1]) < 0.9 else TIM_L if n[1] > 0.8 else None), 0.05)
    bx(p, 67.2, 76.8, 2.0, 2.3, 21.75, 22.25, TIM_L, 0.05, name="Keel")
    for x in (69.0, 72.0, 75.0):
        bx(p, x - 0.15, x + 0.15, 0.0, 2.15, 20.5, 23.5, TIM, 0.04, name="Rib")
    barrel(p, 83, 0, 22, 1.0, 2.0, TIM)
    lathe(p, (65, 0, 24), [(0.7, 0), (0.95, 0.5), (1.0, 0.9)], 6, (196, 160, 90), 0.08, name="Basket")
    for k in range(3):
        slab(p, [(64.6 + 0.4 * k, 0.9), (64.9 + 0.4 * k, 1.5), (64.6 + 0.4 * k, 2.1), (64.3 + 0.4 * k, 1.5)], 0.14, 'xy', 24 + 0.1 * k, fish_cols[k], 0.05, name="BasketFish")
    # a cutting table with fish and a knife, two seagulls waiting for scraps
    bx(p, 78.2, 80.8, 1.9, 2.2, 20.9, 23.1, TIM_L, 0.06, name="Table")
    for tx in (78.5, 80.5):
        for tz in (21.2, 22.8):
            bx(p, tx - 0.15, tx + 0.15, 0.0, 1.9, tz - 0.15, tz + 0.15, TIM_D, 0.05, name="TableLeg")
    for k, (fx, fz, col) in enumerate(((79.0, 21.7, STEEL), (79.9, 22.4, (150, 172, 196)))):
        dk.ball(p, (fx, 2.45, fz), 0.45, col, scale=(1.5, 0.45, 0.6), subdiv=1, rot=(0, 25 * k, 0), name="TableFish")
    bx(p, 79.2, 80.1, 2.2, 2.28, 22.6, 22.8, IRON_L, 0.03, name="Knife")
    for (gx, gy, gz, gr) in ((70.0, 2.55, 22.0, 20), (83.0, 2.45, 22.0, -30)):
        dk.ball(p, (gx, gy + 0.4, gz), 0.55, BONE, scale=(1.3, 0.8, 0.8), subdiv=1, rot=(0, gr, 0), name="Gull")
        dk.ball(p, (gx - 0.55, gy + 0.85, gz), 0.28, BONE, subdiv=1, name="GullHead")
        dk.cone(p, (gx - 1.0, gy + 0.85, gz), 0.1, 0.35, GOLD, verts=4, name="GullBeak")
        dk.ball(p, (gx + 0.75, gy + 0.45, gz), 0.3, (150, 156, 164), scale=(1.4, 0.4, 0.9), subdiv=1, name="GullTail")
    return p


def axe_z(p, x, y, z0, length, head_col=STEEL):
    """An axe pointing along +z from z0: wooden handle, steel head at the far end."""
    rod(p, (x, y, z0), (x, y, z0 + length), 0.11, TIM_L, 4, name="AxeHandle")
    bx(p, x - 0.07, x + 0.07, y - 0.3, y + 0.5, z0 + length - 0.8, z0 + length, head_col, 0.03, name="AxeHead")
    bx(p, x - 0.07, x + 0.07, y - 0.1, y + 0.2, z0 + length - 1.1, z0 + length - 0.8, IRON_L, 0.03, name="AxeBack")


@part_builder("AxeRange")
def build_AxeRange():
    p = dk.Part("AxeRange")
    for k, x in enumerate((-48, -40, -32)):
        bx(p, x - 0.4, x + 0.4, 0, 4.9, 45.6, 46.4, TIM_D, 0.05, name="TargetPost")
        bx(p, x - 1.6, x + 1.6, 0, 0.4, 45.7, 46.5, TIM, 0.05, name="TargetFoot")
        dk.cyl(p, (x, 5.2, 46.6), 2.3, 0.6, BONE, axis='z', verts=8, jitter=0.03, name="TargetBoard")
        dk.cyl(p, (x, 5.2, 46.95), 1.75, 0.2, RED, axis='z', verts=8, jitter=0.03, name="TargetRing")
        dk.cyl(p, (x, 5.2, 47.05), 1.15, 0.2, BONE, axis='z', verts=8, jitter=0.03, name="TargetRing")
        dk.cyl(p, (x, 5.2, 47.15), 0.6, 0.2, RED, axis='z', verts=8, jitter=0.03, name="Bullseye")
        axe_z(p, x + (0.35 if k == 0 else -0.5 if k == 1 else 0.7), 5.4 + (0.1 if k == 1 else -0.9 if k == 2 else 0.0), 47.1, 1.8)
    # the lane: gravel with raked lines and a red throwing line
    bx(p, -51, -29, 0, 0.3, 48, 58, GRAVEL, 0.05, name="Lane")
    for k in range(7):
        bx(p, -49.5 + k * 3.1, -49.1 + k * 3.1, 0.3, 0.36, 48.3, 57.0, STONE_D, 0.06, name="Rake")
    bx(p, -50, -30, 0.3, 0.6, 57.2, 58.0, RED, 0.04, name="Line")
    for x in (-50, -30):
        bx(p, x - 0.3, x + 0.3, 0.3, 1.0, 57.2, 58.0, TIM_D, 0.05, name="Peg")
    # chopping stump with an axe, weapon rack with spare axes
    o = dk.cyl(p, (-27, 0.9, 54), 1.2, 1.8, TIM_D, verts=7, jitter=0.07, name="Stump")
    recolor(o, lambda c, n, i: TIM_X if n[1] > 0.9 else None, 0.05)
    rod(p, (-27.1, 1.8, 54), (-27.5, 3.0, 54), 0.1, TIM_L, 4, name="StuckHandle")
    bx(p, -27.9, -27.1, 2.6, 3.0, 53.93, 54.07, STEEL, 0.03, name="StuckHead")
    for x in (-28.6, -26.4):
        rod(p, (x, 0, 49.5), (x, 3.4, 49.5), 0.2, TIM_D, 5, name="RackPost")
    bx(p, -28.9, -26.1, 2.6, 3.0, 49.3, 49.7, TIM_D, 0.05, name="RackBar")
    bx(p, -28.9, -26.1, 1.2, 1.5, 49.3, 49.7, TIM_D, 0.05, name="RackBar")
    for k, x in enumerate((-28.1, -27.5, -26.9)):
        rod(p, (x, 3.0, 49.5), (x, 1.3, 49.5), 0.07, TIM_L, 4, name="SpareHandle")
        bx(p, x - 0.3, x + 0.3, 2.5, 3.0, 49.46, 49.54, STEEL, 0.03, name="SpareHead")
    return p


def menhir(p, cx, cz, h, w, d, yaw, lean=0.0, marks=3, col=STONE, rune=BLUE_L):
    """A rune stone: tapered block facing +z with carved marks, then turned by yaw degrees about its centre."""
    objs = [frustum(p, cx, cz, 0, h, w * 1.15, d * 1.15, w * 0.78, d * 0.8, col, 0.1, tx=lean, name="Menhir"),
            frustum(p, cx + lean, cz, h, h + 0.5, w * 0.78, d * 0.8, w * 0.3, d * 0.3, col, 0.1, tx=lean * 0.3, name="MenhirTip")]

    for k in range(marks):
        y = h * (0.3 + 0.2 * k)
        zf = cz + d * (0.575 - 0.175 * y / h) - 0.03
        x = cx + lean * (y / h)
        if k % 3 == 0:
            objs.append(bx(p, x - 0.1, x + 0.1, y - 0.5, y + 0.5, zf, zf + 0.12, rune, 0.03, name="Rune"))
            objs.append(bx(p, x + 0.1, x + 0.45, y + 0.1, y + 0.3, zf, zf + 0.12, rune, 0.03, name="Rune"))
        elif k % 3 == 1:
            objs.append(bx(p, x - 0.45, x + 0.45, y - 0.1, y + 0.1, zf, zf + 0.12, rune, 0.03, name="Rune"))
            objs.append(bx(p, x - 0.1, x + 0.1, y - 0.5, y, zf, zf + 0.12, rune, 0.03, name="Rune"))
        else:
            objs.append(bx(p, x - 0.4, x + 0.4, y - 0.45, y - 0.25, zf, zf + 0.12, rune, 0.03, name="Rune"))
            objs.append(bx(p, x - 0.1, x + 0.1, y - 0.45, y + 0.4, zf, zf + 0.12, rune, 0.03, name="Rune"))
    M = Matrix.Translation(Vector((cx, cz, 0))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(Vector((-cx, -cz, 0)))
    for o in objs:
        o.matrix_world = M @ o.matrix_world
        o.data.update()
    return objs


@part_builder("RuneStones")
def build_RuneStones():
    p = dk.Part("RuneStones")
    cx, cz = -19, -47
    dk.cyl(p, (cx, 0.2, cz), 8.5, 0.4, STONE_D, verts=16, jitter=0.07, name="Floor")
    for k in range(12):                                  # cobbles round the rim
        a = 2 * pi * k / 12 + 0.1
        dk.box(p, (cx + 7.3 * math.cos(a), 0.45, cz + 7.3 * math.sin(a)), (1.6, 0.5, 1.2), STONE if k % 2 else STONE_L,
               rot=(0, -math.degrees(a), 0), jitter=0.1, name="Cobble")
    for k in range(10):                                  # a carved ring on the floor with spokes
        a0, a1 = 2 * pi * k / 10, 2 * pi * (k + 1) / 10
        flat(p, [(cx + 3.0 * math.cos(a0), cz + 3.0 * math.sin(a0)), (cx + 3.8 * math.cos(a0), cz + 3.8 * math.sin(a0)),
                 (cx + 3.8 * math.cos(a1), cz + 3.8 * math.sin(a1)), (cx + 3.0 * math.cos(a1), cz + 3.0 * math.sin(a1))], 0.43,
             GOLD_D if k % 2 else GOLD, 0.03, name="FloorRune")
    # the tall centre stone with a red tip, and six smaller stones facing it
    menhir(p, cx, cz, 8.4, 3.0, 1.8, 0, lean=0.0, marks=5, col=STONE_L, rune=RED_D)
    frustum(p, cx, cz, 8.4, 9.8, 2.2, 1.4, 0.3, 0.3, RED_D, 0.05, name="RedTip")
    ring = [(-25.5, -47, 5.0, -90), (-22.2, -52.4, 6.4, -30), (-15.8, -52.4, 5.4, 30), (-12.5, -47, 6.0, 90), (-15.8, -41.6, 4.8, 150),
            (-22.2, -41.6, 5.8, -150)]
    for k, (x, z, h, ang) in enumerate(ring):
        # stone faces the centre: +z of the local frame must point to the centre
        dx, dz = cx - x, cz - z
        yaw = math.degrees(math.atan2(-dx, dz))          # rotation about stage y that turns +z toward (dx, dz)
        menhir(p, x, z, h, 2.2, 1.4, yaw, lean=(0.25 if k % 2 else -0.2), marks=2 + k % 2)
    bx(p, -20.5, -17.5, 0, 1.0, -44.8, -43.2, STONE_L, 0.06, name="Altar")
    lathe(p, (-19, 1.0, -44), [(0.3, 0), (0.7, 0.3), (0.8, 0.6)], 6, GOLD_D, 0.04, name="OfferingBowl")
    for k, (x, z) in enumerate(((-24.6, -49.0), (-14.0, -49.6), (-18.0, -43.0), (-21.0, -50.5))):
        dk.cone(p, (x, 0.4, z), 0.5, 0.8, TURF_D, verts=5, jitter=0.1, name="Moss")
    return p


@part_builder("Banners")
def build_Banners():
    p = dk.Part("Banners")
    raven = [(0, 1.1), (0.25, 0.7), (1.5, 1.4), (1.0, 0.5), (0.55, -0.1), (0.35, -1.1), (0.0, -0.7), (-0.35, -1.1), (-0.55, -0.1),
             (-1.0, 0.5), (-1.5, 1.4), (-0.25, 0.7)]
    z = -34.5
    for k, (x, cloth, bird, trim) in enumerate(((-84, RED, IRON, GOLD), (-68, BLUE, BONE, GOLD), (-52, BLUE, BONE, GOLD), (-36, RED, IRON, GOLD))):
        frustum(p, x, z, 0, 0.7, 1.6, 0.7, 0.9, 0.7, STONE, 0.06, name="Base")
        rod(p, (x, 0.5, z), (x, 13.0, z), 0.35, TIM_D, 5, r2=0.28, jitter=0.05, name="Pole")
        rod(p, (x - 2.2, 12.2, z), (x + 2.2, 12.2, z), 0.2, TIM_D, 5, name="Crossbar")
        slab(p, [(x - 1.7, 11.8), (x + 1.7, 11.8), (x + 1.7, 5.4), (x, 6.9), (x - 1.7, 5.4)], 0.2, 'xy', z, cloth, 0.04, name="Cloth")
        bx(p, x - 1.7, x + 1.7, 11.3, 11.8, z - 0.13, z + 0.13, trim, 0.03, name="Trim")
        for sg in (1, -1):
            slab(p, [(x + 1.0 * u, 8.6 + 1.0 * v) for u, v in raven], 0.1, 'xy', z + sg * 0.16, bird, 0.03, name="Raven")
        dk.ball(p, (x, 13.4, z), 0.7, GOLD, subdiv=1, jitter=0.04, name="Finial")
    return p


@part_builder("Sauna")
def build_Sauna():
    p = dk.Part("Sauna")
    bx(p, 40.5, 53.5, 0, 0.5, 16.5, 27.5, STONE_D, 0.08, name="Floor")
    bx(p, 42.0, 52.0, 0.5, 5.7, 18.0, 18.6, TIM_D, 0.05, name="BackWall")
    logwall(p, 'x', 41.4, 45.8, 25.7, 0.5, 5.7, 1.2, 5, TIM, TIM_L)
    logwall(p, 'x', 48.2, 52.6, 25.7, 0.5, 5.7, 1.2, 5, TIM, TIM_L)
    bx(p, 45.8, 48.2, 4.7, 5.7, 25.1, 26.3, TIM_D, 0.05, name="DoorTop")
    logwall(p, 'z', 17.4, 26.6, 42.6, 0.5, 5.7, 1.2, 5, TIM, TIM_L)
    logwall(p, 'z', 17.4, 26.6, 51.4, 0.5, 5.7, 1.2, 5, TIM, TIM_L)
    bx(p, 45.9, 48.1, 0.5, 4.7, 25.7, 26.1, TIM_D, 0.04, name="Door")
    dk.ball(p, (47.7, 2.6, 26.25), 0.2, GOLD, subdiv=1, name="Handle")
    bx(p, 44.0, 45.4, 2.6, 3.8, 26.2, 26.3, IRON, 0.02, name="Window")
    turf_roof(p, 'x', 41.3, 52.7, 22, 4.9, 6.1, 9.2, 0.7, n=3, N=5, name="SaunaRoof")
    for xg in (42.0, 52.0):
        gable_end(p, 'x', xg, 22, 4.3, 5.6, 8.9, 0.8, TIM_D)
    bx(p, 41.3, 52.7, 9.2, 10.05, 21.65, 22.35, TIM_D, 0.05, name="Ridge")
    for k in range(4):
        dk.cone(p, (42.5 + 2.7 * k, 9.9, 22), 0.4, 0.7, TURF_L, verts=5, jitter=0.1, name="RoofTuft")
    # stone chimney with steam
    for k in range(4):
        frustum(p, 51.5, 20, 1.0 + 2.75 * k, 3.75 + 2.75 * k, 2.2 - 0.12 * k, 2.2 - 0.12 * k, 2.1 - 0.12 * k, 2.1 - 0.12 * k,
                STONE if k % 2 == 0 else STONE_L, 0.08, name="Chimney")
    for (sx, sy, sz, sr) in ((51.5, 13.0, 20.0, 1.0), (52.5, 13.8, 19.7, 0.85), (50.9, 13.9, 20.3, 0.7), (52.7, 15.4, 19.7, 1.2),
                             (53.3, 15.9, 19.4, 0.8), (51.9, 15.9, 20.0, 0.75)):
        rock(p, (sx, sy, sz), sr, (255, 255, 255), scale=(1, 0.75, 1), jitter=0.02, name="Steam")
    # bench, bucket and ladle
    bx(p, 43.5, 50.5, 0.5, 1.3, 26.9, 28.3, TIM, 0.06, name="Bench")
    for x in (44.2, 49.8):
        bx(p, x - 0.3, x + 0.3, 0.5, 1.3, 27.1, 28.1, TIM_D, 0.05, name="BenchLeg")
    dk.cyl(p, (43.0, 1.1, 27.6), 0.8, 1.2, TIM_L, verts=6, top_radius=0.95, jitter=0.05, name="Bucket")
    dk.cyl(p, (43.0, 1.62, 27.6), 0.8, 0.05, WATER, verts=6, name="BucketWater")
    rod(p, (43.3, 1.7, 27.6), (44.6, 2.2, 27.6), 0.08, TIM_D, 4, name="Ladle")
    # firewood stack on the left
    for k, (z, y) in enumerate(((19.4, 0.9), (20.3, 0.9), (21.2, 0.9), (19.85, 1.7), (20.75, 1.7))):
        dk.cyl(p, (41.0, y, z + 1.0), 0.42, 3.2, TIM if k % 2 else TIM_L, axis='z', verts=6, jitter=0.08, name="Firewood")
    return p


@part_builder("Throne")
def build_Throne():
    p = dk.Part("Throne")
    bx(p, -49, -39, 0, 1.2, 19, 29, STONE, 0.07, name="DaisBase")
    bx(p, -48.2, -39.8, 1.2, 2.4, 19.4, 28.6, STONE_L, 0.07, name="DaisTop")
    bx(p, -48, -40, 0, 0.5, 29.8, 30.8, STONE, 0.06, name="StepLow")
    bx(p, -48, -40, 0.5, 1.0, 28.8, 29.8, STONE_L, 0.06, name="StepHigh")
    for sx in (-1, 1):                                   # gold studs on the dais edge
        for k in range(4):
            bx(p, -44 + sx * 4.6 - 0.2, -44 + sx * 4.6 + 0.2, 1.4, 1.8, 20 + k * 2.4, 20.5 + k * 2.4, GOLD_D, 0.03, name="Stud")
    # the carved throne
    bx(p, -45.9, -42.1, 2.4, 4.6, 21.1, 24.9, TIM, 0.06, name="Seat")
    bx(p, -45.9, -42.1, 2.4, 3.0, 24.9, 25.1, GOLD_D, 0.04, name="SeatTrim")
    slab(p, [(-45.9, 4.0), (-42.1, 4.0), (-42.1, 9.0), (-42.9, 9.8), (-44, 10.4), (-45.1, 9.8), (-45.9, 9.0)], 1.0, 'xy', 21.6, TIM_D, 0.05, name="Back")
    dk.cyl(p, (-44, 7.2, 22.2), 1.2, 0.2, GOLD, axis='z', verts=8, jitter=0.03, name="BackDisc")
    dk.cyl(p, (-44, 7.2, 22.35), 0.55, 0.15, RED, axis='z', verts=6, name="BackGem")
    for sx in (-1, 1):
        x = -44 + sx * 2.2
        bx(p, x - 0.35, x + 0.35, 3.9, 5.3, 21.4, 24.8, TIM_D, 0.05, name="Arm")
        bx(p, x - 0.35, x + 0.35, 2.4, 3.9, 24.2, 24.8, TIM_D, 0.05, name="FrontLeg")
        dk.ball(p, (x, 5.2, 25.0), 0.5, GOLD, subdiv=1, name="ArmKnob")
        dk.ball(p, (-44 + sx * 1.6, 9.9, 21.6), 0.45, GOLD, subdiv=1, name="BackKnob")
        rod(p, (-44 + sx * 1.0, 9.8, 21.6), (-44 + sx * 2.2, 12.7, 21.6), 0.4, BONE, 5, r2=0.12, name="Horn")
    bx(p, -46.5, -41.5, 2.4, 2.7, 24.9, 28.3, FUR_L, 0.07, name="Rug")
    bx(p, -45.7, -42.3, 4.6, 4.85, 21.9, 24.7, FUR, 0.07, name="Pelt")
    # fire bowls on tripods
    for x in (-48.2, -39.8):
        for k in range(3):
            a = 2 * pi * k / 3
            rod(p, (x + 0.9 * math.cos(a), 2.4, 20.2 + 0.9 * math.sin(a)), (x + 0.4 * math.cos(a), 3.5, 20.2 + 0.4 * math.sin(a)), 0.13, IRON, 4, name="Tripod")
        lathe(p, (x, 3.4, 20.2), [(0.4, 0), (1.0, 0.35), (1.3, 1.0)], 6, IRON, 0.04, name="Bowl")
        fire(p, x, 4.2, 20.2, 0.85, 1.1)
    return p


@part_builder("Totem")
def build_Totem():
    p = dk.Part("Totem")
    cx, cz = 10.0, 46.0
    bx(p, 7.5, 12.5, 0, 1.6, 43.5, 48.5, STONE, 0.08, name="Base")
    bx(p, 8.0, 12.0, 1.6, 1.9, 44.0, 48.0, STONE_L, 0.06, name="BaseTop")
    # four carved blocks: wolf, bear, eagle, bearded god
    cols = [TIM, RED, BLUE, TIM_L]
    spans = [(1.9, 5.6, 2.6), (5.6, 9.2, 2.8), (9.2, 12.8, 2.8), (12.8, 16.8, 2.6)]
    for k, (y0, y1, w) in enumerate(spans):
        bx(p, cx - w / 2, cx + w / 2, y0, y1, cz - 1.3, cz + 1.3, cols[k], 0.05, name="Block")
        if k < 3:
            bx(p, cx - w / 2 - 0.12, cx + w / 2 + 0.12, y1 - 0.12, y1 + 0.18, cz - 1.42, cz + 1.42, GOLD_D, 0.03, name="Band")
    zf = cz + 1.3
    # wolf: snout, nose, eyes, ears, fangs
    y = 3.9
    bx(p, cx - 0.55, cx + 0.55, y - 0.9, y - 0.1, zf, zf + 0.85, BONE, 0.04, name="Snout")
    bx(p, cx - 0.3, cx + 0.3, y - 0.2, y + 0.1, zf + 0.8, zf + 1.0, IRON, 0.02, name="Nose")
    for sx in (-1, 1):
        bx(p, cx + sx * 0.75 - 0.25, cx + sx * 0.75 + 0.25, y + 0.2, y + 0.55, zf, zf + 0.15, BONE, 0.02, name="Eye")
        bx(p, cx + sx * 0.75 - 0.1, cx + sx * 0.75 + 0.1, y + 0.25, y + 0.5, zf + 0.12, zf + 0.2, IRON, 0.02, name="Pupil")
        slab(p, [(cx + sx * 0.5, 5.6), (cx + sx * 1.4, 5.6), (cx + sx * 1.0, 6.3)], 0.5, 'xy', cz + 0.4, TIM_D, 0.04, name="Ear")
        bx(p, cx + sx * 0.3 - 0.07, cx + sx * 0.3 + 0.07, y - 1.15, y - 0.9, zf + 0.5, zf + 0.7, BONE, 0.02, name="Fang")
    # bear: round ears, big snout, tongue
    y = 7.4
    for sx in (-1, 1):
        dk.ball(p, (cx + sx * 1.1, 9.15, cz + 0.2), 0.45, RED_D, subdiv=1, name="BearEar")
        bx(p, cx + sx * 0.8 - 0.25, cx + sx * 0.8 + 0.25, y + 0.35, y + 0.75, zf, zf + 0.15, BONE, 0.02, name="Eye")
    bx(p, cx - 0.7, cx + 0.7, y - 1.0, y + 0.1, zf, zf + 0.7, BONE_D, 0.04, name="BearSnout")
    bx(p, cx - 0.35, cx + 0.35, y - 0.05, y + 0.25, zf + 0.65, zf + 0.82, IRON, 0.02, name="BearNose")
    bx(p, cx - 0.25, cx + 0.25, y - 1.3, y - 0.9, zf + 0.2, zf + 0.5, RED_D, 0.03, name="Tongue")
    # eagle: hooked beak, eyes, big wings out to both sides
    y = 11.0
    bx(p, cx - 0.4, cx + 0.4, y - 0.6, y + 0.3, zf, zf + 0.8, GOLD, 0.03, name="Beak")
    bx(p, cx - 0.25, cx + 0.25, y - 1.0, y - 0.6, zf + 0.5, zf + 0.9, GOLD_D, 0.03, name="Hook")
    for sx in (-1, 1):
        bx(p, cx + sx * 0.8 - 0.25, cx + sx * 0.8 + 0.25, y + 0.35, y + 0.75, zf, zf + 0.15, BONE, 0.02, name="Eye")
        pts = [(cx + sx * 1.4, 11.8), (cx + sx * 3.9, 12.6), (cx + sx * 4.4, 11.4), (cx + sx * 3.5, 11.2), (cx + sx * 4.0, 10.2),
               (cx + sx * 3.0, 10.2), (cx + sx * 3.3, 9.5), (cx + sx * 1.4, 10.0)]
        slab(p, pts, 0.5, 'xy', cz, BLUE_L if sx > 0 else BLUE_L, 0.06, name="Wing")
    # bearded god: nose, brows, eyes, moustache, horned hat
    y = 14.8
    bx(p, cx - 0.3, cx + 0.3, y - 0.6, y + 0.4, zf, zf + 0.7, BONE_D, 0.03, name="Nose")
    bx(p, cx - 1.1, cx + 1.1, y + 0.55, y + 0.85, zf, zf + 0.2, IRON, 0.03, name="Brows")
    for sx in (-1, 1):
        bx(p, cx + sx * 0.7 - 0.22, cx + sx * 0.7 + 0.22, y + 0.2, y + 0.5, zf, zf + 0.15, BONE, 0.02, name="Eye")
    slab(p, [(cx - 1.2, y - 0.7), (cx + 1.2, y - 0.7), (cx + 0.7, y - 1.9), (cx, y - 2.0), (cx - 0.7, y - 1.9)], 0.4, 'xy', zf + 0.15, BONE, 0.05, name="Beard")
    # raven on top: body, head, beak, spread wings, fan tail
    dk.ball(p, (cx, 18.2, cz), 1.0, IRON, scale=(1.6, 1.5, 2.2), subdiv=1, jitter=0.05, name="RavenBody")
    dk.ball(p, (cx, 19.8, cz + 1.6), 0.9, IRON, subdiv=1, jitter=0.05, name="RavenHead")
    rod(p, (cx, 19.5, cz + 2.2), (cx, 19.4, cz + 3.8), 0.38, GOLD, 5, r2=0.05, name="Beak")
    for sx in (-1, 1):
        dk.ball(p, (cx + sx * 0.5, 20.1, cz + 2.2), 0.2, BONE, subdiv=1, name="RavenEye")
        pts = [(cx + sx * 1.0, 44.8), (cx + sx * 2.8, 44.4), (cx + sx * 4.3, 45.0), (cx + sx * 3.4, 45.4), (cx + sx * 4.5, 46.0),
               (cx + sx * 3.4, 46.4), (cx + sx * 4.2, 47.0), (cx + sx * 1.0, 47.0)]
        slab(p, pts, 0.55, 'xz', 18.5, IRON, 0.08, name="RavenWing")
    slab(p, [(cx - 0.8, 44.8), (cx + 0.8, 44.8), (cx + 1.5, 42.6), (cx, 42.4), (cx - 1.5, 42.6)], 0.5, 'xz', 16.9, IRON_L, 0.05, name="RavenTail")
    return p


def fence_run(p, x0, z0, x1, z1, y_top=2.5, step=3.5, name="Fence"):
    """Fence of posts and two rails from (x0, z0) to (x1, z1); runs along x or z."""
    L = max(abs(x1 - x0), abs(z1 - z0))
    n = max(1, round(L / step))
    for i in range(n + 1):
        t = i / n
        x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
        bx(p, x - 0.3, x + 0.3, 0, y_top + (0.6 if i in (0, n) else 0), z - 0.3, z + 0.3, TIM_D, 0.06, name=name + "Post")
    for (ya, yb) in ((0.8, 1.2), (1.8, 2.2)):
        bx(p, min(x0, x1) - 0.15 if abs(x1 - x0) > 0 else x0 - 0.15, max(x0, x1) + 0.15 if abs(x1 - x0) > 0 else x0 + 0.15, ya, yb,
           min(z0, z1) - 0.15 if abs(z1 - z0) > 0 else z0 - 0.15, max(z0, z1) + 0.15 if abs(z1 - z0) > 0 else z0 + 0.15, TIM, 0.07, name=name + "Rail")


@part_builder("Stables")
def build_Stables():
    p = dk.Part("Stables")
    STRAW = (226, 196, 100)
    THATCH = (204, 170, 92)
    THATCH_D = (160, 124, 64)
    PAL = (204, 154, 92)            # palomino pony
    MANE = (240, 232, 208)
    fence_run(p, 62.3, 51.3, 89.7, 51.3)
    fence_run(p, 62.3, 51.3, 62.3, 61.7)
    fence_run(p, 89.7, 51.3, 89.7, 61.7)
    fence_run(p, 62.3, 61.7, 69.8, 61.7, step=3.5)
    fence_run(p, 76.2, 61.7, 89.7, 61.7, step=3.5)
    for x in (69.8, 76.2):                               # taller gate posts with gold caps
        bx(p, x - 0.4, x + 0.4, 0, 3.3, 61.3, 62.1, TIM_D, 0.05, name="GatePost")
        dk.ball(p, (x, 3.6, 61.7), 0.45, GOLD, subdiv=1, name="GateCap")
    # stable shed: log walls, a thatched roof sloping to the left, hay inside
    bx(p, 80.6, 88.6, 0, 6.0, 51.5, 52.3, TIM_D, 0.05, name="ShedBack")
    logwall(p, 'z', 51.5, 56.5, 81.0, 0, 6.0, 0.8, 5, TIM, TIM_L)
    logwall(p, 'z', 51.5, 56.5, 88.2, 0, 6.0, 0.8, 5, TIM, TIM_L)
    bx(p, 80.6, 88.6, 5.0, 5.9, 55.9, 56.5, TIM_D, 0.05, name="ShedBeam")
    for k in range(5):
        dk.box(p, (84.6, 7.1, 50.8 + 0.64 + 1.28 * k), (9.4, 0.8, 1.2), THATCH if k % 2 else (186, 150, 80), rot=(0, 0, 8), jitter=0.08, name="Thatch")
    for k in range(9):                                   # shaggy thatch fringe along the front edge
        x = 80.3 + 1.05 * k
        dk.box(p, (x, 6.55 + 0.14 * (x - 84.6) - 0.1, 57.05), (0.8, 0.9, 0.3), THATCH_D, rot=(0, 0, 8), jitter=0.1, name="Fringe")
    bx(p, 84.4, 84.9, 6.8, 8.2, 54.0, 54.5, TIM_D, 0.05, name="RoofPole")
    bx(p, 82.0, 84.4, 0.0, 1.6, 52.6, 54.2, STRAW, 0.08, name="Hay")
    bx(p, 84.8, 87.2, 0.0, 1.2, 52.6, 54.0, STRAW, 0.08, name="Hay")
    bx(p, 82.0, 84.4, 1.6, 2.3, 52.8, 54.0, STRAW, 0.1, name="Hay")
    bx(p, 77.7, 80.3, 0, 1.8, 57.8, 59.4, STRAW, 0.08, name="HayBale")
    for x in (78.3, 79.7):
        bx(p, x - 0.1, x + 0.1, 0, 1.82, 57.75, 59.45, TIM_D, 0.03, name="BaleBand")
    # water trough and a bucket
    bx(p, 69, 73, 0, 1.0, 52.2, 53.4, TIM_D, 0.06, name="Trough")
    bx(p, 69.3, 72.7, 0.85, 0.95, 52.4, 53.2, WATER, 0.04, name="TroughWater")
    dk.cyl(p, (75.6, 0.5, 52.9), 0.5, 1.0, TIM_L, verts=6, top_radius=0.6, jitter=0.05, name="Bucket")
    # the shaggy palomino pony (faces -x)
    dk.ball(p, (72, 3.0, 57), 1.0, PAL, scale=(2.3, 1.1, 0.8), subdiv=1, jitter=0.06, name="PonyBody")
    for (x, z) in ((70.4, 56.5), (70.4, 57.5), (73.6, 56.5), (73.6, 57.5)):
        rod(p, (x, 0.5, z), (x, 2.4, z), 0.28, PAL, 5, name="PonyLeg")
        rod(p, (x, 0.0, z), (x, 0.55, z), 0.3, MANE, 5, name="Sock")
    rod(p, (70.0, 3.5, 57), (68.9, 5.1, 57), 0.6, PAL, 5, r2=0.42, name="PonyNeck")
    dk.ball(p, (68.3, 5.2, 57), 0.8, PAL, scale=(1.05, 0.7, 0.65), subdiv=1, name="PonyHead")
    bx(p, 67.3, 67.9, 4.7, 5.3, 56.6, 57.4, MANE, 0.03, name="Muzzle")
    for sz in (-1, 1):
        dk.cone(p, (68.7, 5.6, 57 + sz * 0.3), 0.18, 0.5, PAL, verts=4, name="PonyEar")
        dk.ball(p, (68.0, 5.4, 57 + sz * 0.4), 0.1, IRON, subdiv=1, name="PonyEye")
    slab(p, [(69.9, 3.8), (68.9, 5.5), (69.3, 5.9), (70.7, 4.1)], 0.24, 'xy', 57, MANE, 0.05, name="Mane")
    rod(p, (74.2, 3.5, 57), (75.0, 1.9, 57), 0.26, MANE, 5, r2=0.14, name="PonyTail")
    bx(p, 71.0, 73.0, 3.95, 4.15, 56.3, 57.7, RED, 0.04, name="Blanket")
    bx(p, 71.0, 73.0, 4.15, 4.25, 56.7, 57.3, BLUE, 0.04, name="BlanketStripe")
    return p


@part_builder("Hoard")
def build_Hoard():
    p = dk.Part("Hoard")
    # the cave: back mass, two piers, a lintel rock, a few extra boulders for a rough outline
    bx(p, -62.5, -53.5, 0, 0.2, 38, 44, (58, 50, 42), 0.04, name="CaveFloor")
    dk.ball(p, (-58, 2.7, 37.5), 1.0, STONE_D, scale=(7.5, 3.0, 2.0), subdiv=2, jitter=0.16, name="CaveBack")
    slab(p, [(-62.2, 0.2), (-53.8, 0.2), (-53.8, 3.6), (-54.8, 4.4), (-58, 4.8), (-61.2, 4.4), (-62.2, 3.6)], 0.3, 'xy', 39.55, (34, 30, 30), 0.03, name="CaveDark")
    dk.ball(p, (-64.5, 2.4, 41), 1.0, STONE, scale=(2.0, 2.4, 3.0), subdiv=2, jitter=0.16, name="PierL")
    dk.ball(p, (-51.5, 2.4, 41), 1.0, STONE, scale=(2.0, 2.4, 3.0), subdiv=2, jitter=0.16, name="PierR")
    dk.ball(p, (-58, 5.55, 41), 1.0, STONE_L, scale=(4.8, 0.75, 2.5), subdiv=2, jitter=0.16, name="Lintel")
    for (x, y, z, r, sc) in ((-63.4, 4.2, 38.8, 1.5, (1, 0.7, 1)), (-52.6, 4.3, 38.6, 1.5, (1, 0.7, 1)), (-58, 5.2, 38.4, 1.8, (1.4, 0.6, 1)),
                              (-65.4, 1.2, 36.6, 1.2, (1, 0.8, 1)), (-50.6, 1.0, 37.0, 1.2, (1, 0.8, 1)), (-55.5, 5.5, 41.5, 1.1, (1.2, 0.5, 1))):
        rock(p, (x, y, z), r, STONE if x < -58 else STONE_D, scale=sc, jitter=0.16, name="Boulder")
    for (x, z) in ((-62.5, 38.4), (-53.5, 38.4), (-57, 36.2)):
        dk.cone(p, (x, 5.6, z), 0.45, 0.7, TURF_D, verts=5, jitter=0.1, name="Moss")
    # treasure: three gold heaps, an open chest full of coins
    dk.ball(p, (-61.8, 1.0, 42.6), 1.0, GOLD, scale=(1.8, 1.0, 1.8), subdiv=2, jitter=0.16, name="GoldHeap")
    dk.ball(p, (-54.4, 1.0, 42.8), 1.0, GOLD_D, scale=(2.0, 1.1, 1.8), subdiv=2, jitter=0.16, name="GoldHeap")
    dk.ball(p, (-58, 0.9, 43.4), 1.0, GOLD, scale=(1.5, 0.9, 1.2), subdiv=2, jitter=0.16, name="GoldHeap")
    bx(p, -59.8, -56.2, 0, 2.2, 39.2, 41.6, TIM, 0.06, name="Chest")
    for x in (-59.6, -56.4):
        bx(p, x - 0.15, x + 0.15, 0, 2.25, 39.15, 41.65, IRON, 0.03, name="ChestBand")
    dk.box(p, (-58, 3.48, 38.97), (3.8, 0.45, 2.6), TIM_D, rot=(-100, 0, 0), jitter=0.05, name="Lid")
    bx(p, -59.6, -56.4, 2.0, 2.4, 39.4, 41.4, GOLD, 0.06, name="ChestGold")
    dk.ball(p, (-58, 2.6, 40.4), 1.0, GOLD, scale=(1.4, 0.8, 0.9), subdiv=1, jitter=0.12, name="ChestHeap")
    for (cx, cz) in ((-63.0, 44.0), (-53.0, 44.3)):      # towers of coins
        for k in range(4):
            dk.cyl(p, (cx + 0.05 * (k % 2), 0.1 + 0.2 * k + 0.1, cz), 0.5, 0.18, GOLD if k % 2 else GOLD_D, verts=6, jitter=0.04, name="CoinStack")
    for k in range(6):                                   # loose coins
        x, z = R.uniform(-62.5, -53.5), R.uniform(41.6, 44.2)
        dk.cyl(p, (x, 0.12 + 0.05 * (k % 3), z), 0.32, 0.1, GOLD if k % 2 else GOLD_D, verts=6, rot=(R.uniform(-15, 15), 0, R.uniform(-15, 15)), name="Coin")
    # a crown, a goblet, gems, and a sword stuck in the rock
    dk.cyl(p, (-56.6, 3.2, 41), 0.7, 0.5, GOLD, verts=7, jitter=0.04, name="Crown")
    for k in range(5):
        a = 2 * pi * k / 5
        dk.cone(p, (-56.6 + 0.6 * math.cos(a), 3.45, 41 + 0.6 * math.sin(a)), 0.18, 0.5, GOLD, verts=4, name="CrownSpike")
    dk.ball(p, (-56.6, 3.1, 41.7), 0.2, RED, subdiv=1, name="CrownGem")
    lathe(p, (-52.4, 1.6, 41.4), [(0.2, 0), (0.25, 0.4), (0.55, 0.5), (0.5, 0.9)], 6, GOLD, 0.04, name="Goblet")
    for (x, y, z, col) in ((-60.0, 3.1, 41.0, RED), (-59.6, 2.5, 42.6, BLUE_L), (-55.0, 2.3, 43.0, (96, 190, 110)), (-62.4, 1.9, 43.4, RED),
                           (-53.2, 1.8, 44.0, BLUE_L), (-58.4, 1.6, 44.2, (96, 190, 110))):
        dk.ball(p, (x, y, z), 0.28, col, subdiv=1, jitter=0.03, name="Gem")
    rod(p, (-66.4, 3.3, 43.8), (-66.4, 5.6, 43.8), 0.2, STEEL, 4, name="Blade")
    bx(p, -66.55, -66.25, 5.4, 5.65, 43.2, 44.4, GOLD_D, 0.03, name="Guard")
    rod(p, (-66.4, 5.6, 43.8), (-66.4, 6.1, 43.8), 0.12, TIM_D, 4, name="Grip")
    dk.ball(p, (-66.4, 6.2, 43.8), 0.16, GOLD, subdiv=1, name="Pommel")
    return p


@part_builder("Helmet")
def build_Helmet():
    p = dk.Part("Helmet")
    cx, cz = -2.0, -45.0
    bx(p, -9, 5, 0, 2.0, -52, -38, STONE, 0.07, name="Plinth")
    bx(p, -7.2, 3.2, 2.0, 3.2, -50.2, -39.8, STONE_L, 0.07, name="Step")
    for sx in (-1, 1):                                   # gold knobs at the plinth corners
        for sz in (-1, 1):
            dk.ball(p, (cx + sx * 6.2, 2.5, cz + sz * 6.2), 0.7, GOLD, subdiv=1, jitter=0.04, name="Knob")
    # the bowl of the helmet: a lathe, a mail skirt, a gold brim band
    prof = [(6.2, 6.0), (6.05, 8.4), (5.4, 10.9), (4.2, 13.1), (2.3, 14.9), (0.0, 15.7)]
    lathe(p, (cx, 0, cz), [(r, h) for r, h in prof], 12, STEEL, 0.05, name="Bowl")
    lathe(p, (cx, 0, cz), [(5.2, 4.7), (6.0, 5.2), (6.3, 6.0)], 12, IRON_L, 0.08, name="Mail")
    dk.cyl(p, (cx, 6.6, cz), 6.4, 1.2, GOLD, verts=12, jitter=0.04, name="Brim")
    # gold ribs over the bowl (one along x, one along z) and the crest along z
    pts = [(r + 0.2, h) for r, h in prof]
    for k in range(len(pts) - 1):
        (ra, ha), (rb, hb) = pts[k], pts[k + 1]
        for sg in (-1, 1):
            rod(p, (cx + sg * ra, ha, cz), (cx + sg * rb, hb, cz), 0.3, GOLD_D, 4, name="RibX")
            rod(p, (cx, ha, cz + sg * ra), (cx, hb, cz + sg * rb), 0.4, GOLD, 4, name="RibZ")
    # face: nose guard, eye slots with gold rims, a red gem
    bx(p, cx - 0.7, cx + 0.7, 5.0, 10.6, -39.9, -39.1, GOLD_D, 0.04, name="NoseGuard")
    for sx in (-1, 1):
        bx(p, cx + sx * 2.3 - 0.8, cx + sx * 2.3 + 0.8, 7.4, 8.5, -39.2, -38.8, IRON, 0.02, name="EyeSlot")
        bx(p, cx + sx * 2.3 - 1.0, cx + sx * 2.3 + 1.0, 8.5, 8.8, -39.2, -38.8, GOLD, 0.02, name="EyeBrow")
    dk.ball(p, (cx, 11.0, -38.8), 0.6, RED, subdiv=1, jitter=0.03, name="Gem")
    # the curved bone horns with dark stripes and gold tips
    path = [(5.5, 9.8), (7.4, 11.8), (8.2, 14.6), (7.8, 17.4), (6.6, 19.6)]
    rr = [1.05, 0.9, 0.72, 0.52, 0.25]
    for sg in (-1, 1):
        for k in range(len(path) - 1):
            a = (cx + sg * path[k][0], path[k][1], cz)
            b = (cx + sg * path[k + 1][0], path[k + 1][1], cz)
            rod(p, a, b, rr[k], BONE if k % 2 == 0 else BONE_D, 6, r2=rr[k + 1], jitter=0.04, name="Horn")
        dk.ball(p, (cx + sg * path[-1][0], path[-1][1] + 0.4, cz), 0.62, GOLD, subdiv=1, jitter=0.04, name="HornTip")
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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_VikingLonghouse.json"))
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
        view(allm, "stage_VikingLonghouse_34.png", shiba=spot, az=205, el=40, size=(1800, 1000), zoom=1.55)
        view(allm, "stage_VikingLonghouse_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_VikingLonghouse_34.png", "stage_VikingLonghouse_top.png", "stage_VikingLonghouse.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
