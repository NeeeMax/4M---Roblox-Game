"""Samurai Shrine decor models (theme SamuraiShrine): builds the 20 decor parts around the twelfth Shiba (Samurai Shiba).

Run:  blender --background --factory-startup --python build_SamuraiShrine.py -- <outdir>   (use an absolute outdir)
Writes into <outdir> (default: out/SamuraiShrine next to this script):
  Decor_SamuraiShrine_<PartId>.fbx, preview_<PartId>.png per part, stage_SamuraiShrine.png (3/4 view + top view stacked).
Every model is built in the stage frame (see decorkit.py) WITHOUT the part's Yaw and, before export, fitted to the union box of its
blueprint pieces so that the game's fitToPieces scale stays about 1. Style: chunky low poly, flat vertex colours with a little
per-face jitter, no textures, no neon. Previews are rendered the way the player sees the stage: from the road (+z), +x to the right.
Env: SS_ONLY=Part1,Part2 builds only those parts.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "SamuraiShrine"
R = random.Random(12)
pi = math.pi
DBG = os.environ.get("SS_DBG")
ONLY = set(os.environ.get("SS_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
GRASS = (104, 154, 78); GRASS_D = (84, 134, 66); GRASS_L = (132, 180, 90); MOSS = (78, 124, 66)
GRAVEL = (222, 214, 192); GRAVEL_D = (196, 188, 166)
STONE = (152, 152, 150); STONE_L = (186, 186, 180); STONE_D = (96, 98, 104)
VERM = (206, 54, 38); VERM_D = (150, 38, 34); VERM_L = (226, 88, 60)
ROOF = (60, 64, 76); ROOF_L = (86, 92, 108)
WOOD = (124, 86, 54); WOOD_D = (74, 50, 38); WOOD_L = (170, 124, 82)
PLASTER = (238, 232, 214); PLASTER_D = (214, 206, 184)
INDIGO = (44, 62, 112); INDIGO_L = (70, 94, 150)
GOLD = (238, 190, 62); GOLD_D = (196, 148, 40); BRONZE = (150, 112, 62); BRONZE_D = (112, 80, 44)
PINK = (248, 178, 202); PINK_D = (236, 140, 176); PINK_L = (255, 214, 226)
WATER = (72, 150, 184); WATER_L = (130, 196, 222); WATER_D = (52, 118, 156)
KOI = (238, 120, 44); LEAF = (112, 166, 76); LEAF_D = (80, 132, 62)
STRAW = (216, 190, 122); STRAW_D = (176, 148, 86); EARTH = (128, 98, 70); EARTH_D = (98, 74, 52)
WARM = (250, 214, 130); BLACK = (36, 36, 44); STEEL = (184, 190, 200); STEEL_D = (130, 138, 152); SKIN = (226, 184, 146)
WHITE = (250, 250, 246)

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



# ---- samurai shrine helpers ---------------------------------------------------------------------------------------
def hip_roof(p, cx, cz, y0, hw, hd, tw, td, h, col=ROOF, curl=0.8, fascia=0.5, trim=None, jitter=0.05, name="Roof"):
    """Japanese tiled hip roof: eave rectangle hw x hd (half sizes) with corners curled up by `curl`, ridge rectangle tw x td at y0+h."""
    def ring(a, b, y, cy):
        return [(cx - a, y + cy, cz - b), (cx, y, cz - b), (cx + a, y + cy, cz - b), (cx + a, y, cz), (cx + a, y + cy, cz + b),
                (cx, y, cz + b), (cx - a, y + cy, cz + b), (cx - a, y, cz)]
    rings = [ring(hw * 0.9, hd * 0.9, y0 - fascia, 0.0), ring(hw, hd, y0, curl), ring(tw, td, y0 + h, 0.0)]
    pts, idx = [], []
    for r in rings:
        idx.append(list(range(len(pts), len(pts) + 8)))
        pts += r
    faces = []
    for a, b in zip(idx, idx[1:]):
        for i in range(8):
            j = (i + 1) % 8
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(idx[0]))
    faces.append(tuple(idx[-1]))
    o = _obj(p, name, pts, faces, col, jitter)
    if trim:
        recolor(o, lambda c, n, i: trim if n[1] < 0.35 else None, 0.04)
    return o


def patch(p, cx, cz, rx, rz, y0, y1, col, n=10, irr=0.18, jitter=0.05, name="Patch"):
    """Irregular flat blob (slab) in the xz plane."""
    pts = []
    for i in range(n):
        a = 2 * pi * i / n
        k = 1 + R.uniform(-irr, irr)
        pts.append((cx + rx * k * math.cos(a), cz + rz * k * math.sin(a)))
    return slab(p, pts, y1 - y0, 'xz', y0, col, jitter, name=name)


def stone(p, cx, cz, rx, ry, rz, col, y0=0.0, sides=6, jitter=0.1, top=None, rot=0.0, name="Rock"):
    """Low-poly boulder: rings with random radii. top = colour of the up-facing faces (moss)."""
    prof = [(0.8, 0.0), (1.0, 0.3), (0.85, 0.75), (0.45, 1.0)]
    rings = []
    ph = R.uniform(0, 6.28)
    for k, (rr, hh) in enumerate(prof):
        ring = []
        for i in range(sides):
            a = 2 * pi * i / sides + rot
            kk = rr * (1 + R.uniform(-0.18, 0.18))
            ring.append((cx + rx * kk * math.cos(a), y0 + ry * hh * (1 + R.uniform(-0.06, 0.06)), cz + rz * kk * math.sin(a)))
        rings.append(ring)
    rings.append([(cx + R.uniform(-0.1, 0.1) * rx, y0 + ry * 1.02, cz + R.uniform(-0.1, 0.1) * rz)])
    o = loft(p, rings, col, jitter, name=name)
    if top:
        recolor(o, lambda c, n, i: top if n[1] > 0.55 else None, 0.06)
    return o


def ring_flat(p, cx, cz, r0, r1, y, col, sx=1.0, sz=1.0, n=12, name="Ring"):
    """Flat annulus on the ground (one face per segment), facing up."""
    pts, faces = [], []
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + r0 * sx * math.cos(a), y, cz + r0 * sz * math.sin(a)))
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + r1 * sx * math.cos(a), y, cz + r1 * sz * math.sin(a)))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return _obj(p, name, pts, faces, col, 0.03, closed=False, up=True)


def disc(p, x, y, z, r, col, axis='z', sides=8, thick=0.15, name="Disc"):
    return dk.cyl(p, (x, y, z), r, thick, col, axis=axis, verts=sides, name=name)


def pillar(p, x, z, y0, y1, r, col, sides=6, top_r=None, name="Pillar"):
    return post(p, x, z, y0, y1, r, col, sides, top_r, 0.04, name)


def curve_roof_slab(p, x0, x1, y_eave, y_top, z0, z1, col, n=6, t=0.6, jitter=0.05, name="Arch"):
    """Not used."""
    return None


def quad_strip(p, x0, x1, z, y0, y1, n, cols, thick=0.2, name="Strip"):
    """n vertical strips between x0 and x1 at depth z, alternating colours."""
    w = (x1 - x0) / n
    for i in range(n):
        bx(p, x0 + i * w, x0 + (i + 1) * w, y0, y1, z - thick / 2, z + thick / 2, cols[i % len(cols)], 0.04, name=name)


def toro_model(p, x, z, s, moss=True):
    """Stone lantern (ishi-doro) of scale s: base, post, bulb, fire box with four openings, curled roof, jewel."""
    lathe(p, (x, 0, z), [(1.9 * s, 0), (1.9 * s, 0.5 * s), (1.2 * s, 0.9 * s)], 6, STONE_D, 0.06, name="ToroBase")
    lathe(p, (x, 0.9 * s, z), [(0.6 * s, 0), (0.6 * s, 1.9 * s)], 6, STONE, 0.06, name="ToroPost")
    lathe(p, (x, 2.5 * s, z), [(0.7 * s, 0), (1.3 * s, 0.45 * s), (1.5 * s, 0.9 * s), (0.9 * s, 1.1 * s)], 6, STONE_L, 0.05, name="ToroBulb")
    y0 = 3.6 * s
    bx(p, x - 0.95 * s, x + 0.95 * s, y0, y0 + 1.5 * s, z - 0.95 * s, z + 0.95 * s, WARM, 0.03, name="ToroLight")
    for sx in (-1, 1):
        for sz in (-1, 1):
            bx(p, x + sx * 0.95 * s - 0.2 * s, x + sx * 0.95 * s + 0.2 * s, y0 - 0.1 * s, y0 + 1.6 * s,
               z + sz * 0.95 * s - 0.2 * s, z + sz * 0.95 * s + 0.2 * s, STONE, 0.04, name="ToroCorner")
    bx(p, x - 0.3 * s, x + 0.3 * s, y0 + 0.2 * s, y0 + 1.3 * s, z - 1.0 * s, z + 1.0 * s, STONE_D, 0.03, name="ToroCross")
    bx(p, x - 1.1 * s, x + 1.1 * s, y0 + 1.5 * s, y0 + 1.75 * s, z - 1.1 * s, z + 1.1 * s, STONE_D, 0.04, name="ToroLid")
    o = lathe(p, (x, y0 + 1.7 * s, z), [(2.2 * s, 0), (2.0 * s, 0.25 * s), (0.9 * s, 0.9 * s), (0.25 * s, 1.35 * s)], 6, STONE, 0.06, name="ToroRoof")
    dk.ball(p, (x, y0 + 3.4 * s, z), 0.4 * s, STONE_L, subdiv=1, name="ToroJewel")
    if moss:
        patch(p, x, z, 1.9 * s, 1.9 * s, 0, 0.14, MOSS, 8, name="ToroMoss")


def sign_marks(p, x, y, z, w, h, col, seed=0, name="Glyph"):
    """A few bars like a brush-written glyph, facing +z, inside w x h centred at (x, y)."""
    bx(p, x - w / 2, x + w / 2, y + h * 0.28, y + h * 0.28 + h * 0.12, z, z + 0.12, col, 0.02, name=name)
    bx(p, x - w * 0.5, x + w * 0.5, y - h * 0.18, y - h * 0.06, z, z + 0.12, col, 0.02, name=name)
    bx(p, x - w * 0.07, x + w * 0.07, y - h * 0.5, y + h * 0.5, z, z + 0.12, col, 0.02, name=name)
    bx(p, x - w * 0.5, x - w * 0.34, y - h * 0.5, y - h * 0.2, z, z + 0.12, col, 0.02, name=name)




# ---- the parts ----------------------------------------------------------------------------------------------------
PATH = [(0, 65), (38, 48), (-28, 34), (-34, 6), (10, -10), (46, -24), (30, -46), (0, -65)]
COURTS = [(-77, -47, 19, 41), (-92, -64, 38, 65), (-21, 5, -53, -27), (54, 82, -36, -23)]


def _near_path(x, z, d):
    for (ax, az), (bx_, bz) in zip(PATH, PATH[1:]):
        vx, vz = bx_ - ax, bz - az
        t = max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / (vx * vx + vz * vz)))
        if math.hypot(x - (ax + t * vx), z - (az + t * vz)) < d:
            return True
    return False


@part_builder("Ground")
def build_Ground():
    p = dk.Part("Ground")
    bx(p, -95, 95, 0, 0.3, -65, 65, GRASS, 0.04, name="Base")
    for k in range(7):                                    # lighter and darker lawn patches
        patch(p, R.uniform(-80, 80), R.uniform(-52, 52), R.uniform(8, 14), R.uniform(6, 10), 0.3, 0.34, GRASS_L if k % 2 else GRASS_D, 9, 0.2, 0.04, name="Lawn")
    # the winding stone path
    w = 2.6
    for (ax, az), (bx_, bz) in zip(PATH, PATH[1:]):
        L = math.hypot(bx_ - ax, bz - az)
        nx, nz = -(bz - az) / L * w, (bx_ - ax) / L * w
        cl = lambda zz: max(-64.6, min(64.6, zz))
        slab(p, [(ax + nx, cl(az + nz)), (bx_ + nx, cl(bz + nz)), (bx_ - nx, cl(bz - nz)), (ax - nx, cl(az - nz))], 0.14, 'xz', 0.3, (206, 196, 168), 0.05, name="Path")
    for (ax, az), (bx_, bz) in zip(PATH, PATH[1:]):       # joints between the flagstones
        L = math.hypot(bx_ - ax, bz - az)
        ux, uz = (bx_ - ax) / L, (bz - az) / L
        nx, nz = -uz * (w - 0.3), ux * (w - 0.3)
        for k in range(1, int(L // 4.2) + 1):
            cx, cz = ax + ux * k * 4.2, az + uz * k * 4.2
            if abs(cz) > 63:
                continue
            flat(p, [(cx + nx - ux * 0.09, cz + nz - uz * 0.09), (cx + nx + ux * 0.09, cz + nz + uz * 0.09),
                     (cx - nx + ux * 0.09, cz - nz + uz * 0.09), (cx - nx - ux * 0.09, cz - nz - uz * 0.09)], 0.455, (172, 162, 134), 0.02, name="Joint")
    for (ax, az) in PATH[1:-1]:
        dk.cyl(p, (ax, 0.37, az), w * 1.02, 0.14, (206, 196, 168), verts=8, jitter=0.05, name="PathNode")
    # raked gravel courts
    for (x0, x1, z0, z1) in COURTS:
        bx(p, x0, x1, 0.3, 0.42, z0, z1, GRAVEL, 0.03, name="Court")
        bx(p, x0 - 0.5, x1 + 0.5, 0.3, 0.46, z0 - 0.5, z0, STONE, 0.06, name="Edge")
        bx(p, x0 - 0.5, x1 + 0.5, 0.3, 0.46, z1, min(z1 + 0.5, 65), STONE, 0.06, name="Edge")
        bx(p, x0 - 0.5, x0, 0.3, 0.46, z0, z1, STONE, 0.06, name="Edge")
        bx(p, x1, x1 + 0.5, 0.3, 0.46, z0, z1, STONE, 0.06, name="Edge")
    for (x0, x1, z0, z1) in COURTS[:3]:
        n = 5
        for k in range(n):
            z = z0 + (k + 0.5) * (z1 - z0) / n
            bx(p, x0 + 1, x1 - 1, 0.42, 0.5, z - 0.2, z + 0.2, GRAVEL_D, 0.03, name="Rake")
    patch(p, -12, -20, 12, 8, 0.3, 0.46, MOSS, 10, 0.12, 0.05, name="Moss")
    patch(p, 41, 27, 11, 7, 0.3, 0.46, MOSS, 10, 0.12, 0.05, name="Moss")
    # flowers and tufts
    cols = [PINK, WHITE, (255, 224, 110), PINK_D, (190, 170, 240)]
    n = 0
    while n < 34:
        x, z = R.uniform(-90, 90), R.uniform(-60, 60)
        if _near_path(x, z, 4.5) or any(a - 3 < x < b + 3 and c - 3 < z < d + 3 for a, b, c, d in COURTS):
            continue
        dk.cone(p, (x, 0.3, z), 0.5, 0.2, cols[n % 5], verts=4, jitter=0.05, name="Flower")
        n += 1
    return p


@part_builder("Pagoda")
def build_Pagoda():
    p = dk.Part("Pagoda")
    cx, cz = -78, 52
    bx(p, -88, -68, 0, 1.4, 42, 62, STONE, 0.07, name="BaseLow")
    bx(p, -86.5, -69.5, 1.4, 2.2, 43.5, 60.5, STONE_D, 0.06, name="BaseHigh")
    bx(p, -81, -75, 1.4, 1.8, 60.5, 62, STONE_L, 0.05, name="Step")
    HW = [4.8, 4.4, 4.0, 3.6, 3.2]
    WY = [2.2, 5.7, 9.2, 12.7, 16.2]
    RY = [5.2, 8.7, 12.2, 15.7, 19.2]
    RH = [8.0, 7.0, 6.0, 5.0, 4.0]
    for i in range(5):
        hw, y0 = HW[i], WY[i]
        wall = VERM if i % 2 == 0 else PLASTER
        bx(p, cx - hw, cx + hw, y0, y0 + 3.0, cz - hw, cz + hw, wall, 0.04, name="Wall")
        for sx in (-1, 1):
            for sz in (-1, 1):
                bx(p, cx + sx * hw - 0.3, cx + sx * hw + 0.3, y0, y0 + 3.0, cz + sz * hw - 0.3, cz + sz * hw + 0.3,
                   VERM_D if wall == VERM else VERM, 0.03, name="Pillar")
        # window with a lattice on the road side
        bx(p, cx - hw * 0.45, cx + hw * 0.45, y0 + 0.7, y0 + 2.4, cz + hw, cz + hw + 0.12, WOOD_D, 0.02, name="Window")
        bx(p, cx - 0.12, cx + 0.12, y0 + 0.7, y0 + 2.4, cz + hw + 0.12, cz + hw + 0.2, PLASTER_D, 0.02, name="Lattice")
        bx(p, cx - hw * 0.45, cx + hw * 0.45, y0 + 1.45, y0 + 1.65, cz + hw + 0.12, cz + hw + 0.2, PLASTER_D, 0.02, name="Lattice")
        if 0 < i < 4:                                      # balcony rail
            r = hw + 1.0
            bx(p, cx - r, cx + r, y0 + 0.4, y0 + 0.8, cz + r - 0.2, cz + r, WOOD_D, 0.04, name="Rail")
            bx(p, cx - r, cx + r, y0 + 0.4, y0 + 0.8, cz - r, cz - r + 0.2, WOOD_D, 0.04, name="Rail")
            bx(p, cx - r, cx - r + 0.2, y0 + 0.4, y0 + 0.8, cz - r, cz + r, WOOD_D, 0.04, name="Rail")
            bx(p, cx + r - 0.2, cx + r, y0 + 0.4, y0 + 0.8, cz - r, cz + r, WOOD_D, 0.04, name="Rail")
        last = i == 4
        hip_roof(p, cx, cz, RY[i], RH[i], RH[i], 0.5 if last else HW[i + 1] - 0.4, 0.5 if last else HW[i + 1] - 0.4,
                 2.4 if last else 1.3, ROOF, 0.9, 0.5, trim=ROOF_L, name="Roof")
        for sx in (-1, 1):                                 # little gold bells under the eave corners
            for sz in (-1, 1):
                dk.cyl(p, (cx + sx * (RH[i] - 0.1), RY[i] + 0.3, cz + sz * (RH[i] - 0.1)), 0.06, 0.6, GOLD, verts=4, top_radius=0.28, name="Bell")
    # golden spire (sorin): pole, rings, jewel
    top = 21.6
    dk.cyl(p, (cx, (top + 29.1) / 2, cz), 0.35, 29.1 - top, GOLD_D, verts=6, name="Pole")
    dk.cyl(p, (cx, top + 0.3, cz), 1.3, 0.6, GOLD, verts=6, name="SpireBase")
    for k in range(7):
        r = 1.15 - k * 0.1
        dk.cyl(p, (cx, top + 1.6 + k * 0.95, cz), r, 0.28, GOLD, verts=6, jitter=0.03, name="Ring")
    lathe(p, (cx, 28.4, cz), [(0.75, 0), (0.55, 0.45), (0.0, 1.0)], 6, GOLD, 0.03, name="Jewel")
    return p


@part_builder("Torii")
def build_Torii():
    p = dk.Part("Torii")
    z = 20
    for x in (-40.5, -21.5):
        post(p, x, z, 1, 13.4, 1.25, VERM, 8, 0.98, 0.03, name="Pillar")
        dk.cyl(p, (x, 0.5, z), 1.6, 1.0, BLACK, verts=8, jitter=0.04, name="Foot")
        dk.cyl(p, (x, 2.2, z), 1.3, 1.6, BLACK, verts=8, top_radius=1.28, jitter=0.03, name="Sleeve")
    bx(p, -43.5, -18.5, 9.2, 10.4, z - 0.6, z + 0.6, VERM, 0.04, name="Nuki")
    for x in (-40.5, -21.5):
        for s in (-1, 1):
            bx(p, x + s * 1.1 - 0.25, x + s * 1.1 + 0.25, 8.9, 10.7, z - 0.7, z + 0.7, BLACK, 0.02, name="Wedge")
    bx(p, -44, -18, 12.2, 13.3, z - 1.0, z + 1.0, VERM, 0.04, name="Shimagi")
    pts_b, pts_t = [], []
    for k in range(7):
        u = -15 + 5 * k
        pts_b.append((-31 + u, 13.3 + 1.6 * max(0.0, (abs(u) - 8) / 7) ** 1.5))
        pts_t.append((-31 + u, 14.5 + 1.25 * (u / 15) ** 2))
    slab(p, pts_b + pts_t[::-1], 3.2, 'xy', z, BLACK, 0.03, name="Kasagi")
    bx(p, -32.4, -29.6, 10.4, 12.2, z - 0.5, z + 0.5, GOLD, 0.03, name="Plaque")
    bx(p, -32.2, -29.8, 10.6, 12.0, z + 0.5, z + 0.58, VERM_D, 0.02, name="PlaqueIn")
    sign_marks(p, -31, 11.3, z + 0.58, 1.3, 1.1, GOLD)
    return p


@part_builder("Lanterns")
def build_Lanterns():
    p = dk.Part("Lanterns")
    patch(p, -20, 54, 8.0, 4.0, 0.0, 0.1, GRAVEL, 10, 0.1, 0.03, name="Bed")
    for (x, z, s) in ((-28, 52, 1.1), (-20, 58, 0.8), (-12, 51.5, 1.3)):
        toro_model(p, x, z, s)
    stone(p, -24, 54.5, 1.3, 0.9, 1.1, STONE, top=MOSS, name="Rock")
    stone(p, -16, 55.5, 1.0, 0.7, 0.9, STONE_D, top=MOSS, name="Rock")
    return p


@part_builder("Teahouse")
def build_Teahouse():
    p = dk.Part("Teahouse")
    plank_row(p, 57, 79, 28, 44, 0, 1, 8, 'x', WOOD, 0.06, 0.07, name="Deck")
    bx(p, 59, 77, 1, 6.5, 30.2, 30.8, PLASTER, 0.03, name="BackWall")
    for k in range(5):
        bx(p, 59 + k * 4.5 - 0.1, 59 + k * 4.5 + 0.1, 1, 6.5, 30.8, 31.0, WOOD_D, 0.02, name="Bar")
    bx(p, 59, 77, 3.6, 3.8, 30.8, 31.0, WOOD_D, 0.02, name="Bar")
    for x0, xo in ((59, 59.6), (76.4, 77)):
        bx(p, x0, xo, 1, 6.5, 30.8, 41.4, PLASTER, 0.03, name="SideWall")
        side = (x0 + 0.6, x0 + 0.8) if x0 < 70 else (x0 - 0.2, x0)
        bx(p, side[0], side[1], 3.6, 3.8, 30.8, 41.4, WOOD_D, 0.02, name="Bar")
        for zz in (34.5, 38.0):
            bx(p, side[0], side[1], 1, 6.5, zz - 0.1, zz + 0.1, WOOD_D, 0.02, name="Bar")
    for x, z in ((59.4, 41.6), (76.6, 41.6), (59.4, 30.6), (76.6, 30.6)):
        pillar(p, x, z, 1, 6.5, 0.45, WOOD_D, 6)
    bx(p, 59, 77, 5.7, 6.5, 41.2, 42.0, WOOD_D, 0.04, name="Lintel")
    # blue curtain (noren) with slits and a white crest
    for k in range(3):
        x0 = 62 + k * 4.2
        bx(p, x0, x0 + 3.7, 4.0, 5.7, 42.0, 42.25, INDIGO, 0.04, name="Noren")
    sign_marks(p, 68, 4.85, 42.25, 1.3, 1.1, WHITE)
    hip_roof(p, 68, 36, 6.5, 11.0, 8.0, 8.3, 5.4, 0.9, ROOF, 0.6, 0.45, trim=ROOF_L, name="RoofLow")
    hip_roof(p, 68, 36, 7.3, 8.3, 5.4, 3.6, 1.6, 1.5, ROOF, 0.4, 0.4, trim=ROOF_L, name="RoofHigh")
    for sx in (-1, 1):
        dk.cone(p, (68 + sx * 3.4, 8.7, 36), 0.35, 0.5, GOLD, verts=4, name="Shachi")
    # bench with cushion, teapot and cups
    bx(p, 64, 72, 1, 2, 37.4, 39.8, WOOD_L, 0.05, name="Bench")
    bx(p, 64.5, 67.5, 2, 2.3, 37.6, 39.6, VERM, 0.03, name="Cushion")
    lathe(p, (70.2, 2.0, 38.6), [(0.55, 0), (0.75, 0.35), (0.55, 0.8), (0.2, 0.95)], 6, INDIGO, 0.04, name="Teapot")
    rod(p, (70.7, 2.4, 38.6), (71.5, 2.9, 38.6), 0.12, INDIGO, 4, name="Spout")
    for dx in (-1.2, 0.0):
        dk.cyl(p, (68.6 + dx, 2.2, 38.6), 0.3, 0.4, PLASTER, verts=5, name="Cup")
    # red paper lantern and the parasol
    lathe(p, (75.0, 3.2, 42.6), [(0.35, 0), (0.95, 0.5), (0.95, 1.0), (0.35, 1.5)], 6, VERM, 0.04, name="Chochin")
    rod(p, (75.0, 4.7, 42.6), (75.0, 5.7, 41.6), 0.06, BLACK, 4, name="Cord")
    bx(p, 58.4, 63.6, 1, 2, 41.5, 43, VERM, 0.04, name="RedBench")
    post(p, 61, 43, 1, 6.4, 0.2, WOOD_D, 5, name="ParasolPole")
    o = lathe(p, (61, 5.2, 43), [(3.0, 0), (2.8, 0.25), (1.2, 1.0), (0, 1.5)], 8, VERM, 0.03, name="Parasol")
    recolor(o, lambda c, n, i: PLASTER if (i % 2 == 1 and n[1] > 0.2) else None, 0.02)
    return p


def nobori_model(p, x, z, h, cloth, mark, trim):
    post(p, x, z, 0, h - 0.3, 0.32, WOOD_D, 6, 0.26, 0.04, name="Pole")
    bx(p, x - 0.65, x + 0.65, 0, 0.6, z - 0.65, z + 0.65, STONE_D, 0.05, name="Foot")
    dk.ball(p, (x, h - 0.05, z), 0.4, GOLD, subdiv=1, name="Finial")
    bx(p, x - 0.2, x + 3.9, h - 0.7, h - 0.2, z - 0.2, z + 0.2, WOOD_D, 0.04, name="Arm")
    dk.ball(p, (x + 3.9, h - 0.45, z), 0.3, GOLD, subdiv=1, name="ArmEnd")
    x0, x1 = x + 0.45, x + 3.4
    yb = h - 0.7
    ylow = h - 11.0
    pts = [(x0, yb), (x1, yb), (x1, yb - 3), (x1 + 0.5, yb - 5.5), (x1, yb - 8), (x1 + 0.4, ylow), (x0 + 1.5, ylow - 0.6), (x0, ylow + 0.2)]
    slab(p, pts, 0.18, 'xy', z, cloth, 0.04, name="Cloth")
    bx(p, x0, x0 + 0.35, ylow + 0.2, yb, z - 0.12, z + 0.12, trim, 0.03, name="Hem")
    bx(p, x0, x1, yb - 0.45, yb, z - 0.12, z + 0.12, trim, 0.03, name="Top")
    cxm = (x0 + x1) / 2
    for sg in (1, -1):
        dk.cyl(p, (cxm, h - 4.4, z + sg * 0.12), 1.0, 0.08, mark, axis='z', verts=8, name="Mon")
        dk.cyl(p, (cxm, h - 4.4, z + sg * 0.19), 0.45, 0.06, cloth, axis='z', verts=6, name="MonIn")
    for k in range(3):
        bx(p, x0 + 0.5 + k * 0.9, x0 + 0.8 + k * 0.9, h - 8.6, h - 6.2, z + 0.09, z + 0.2, trim, 0.03, name="Stripe")


@part_builder("Nobori")
def build_Nobori():
    p = dk.Part("Nobori")
    nobori_model(p, -44, -20, 15, VERM, PLASTER, VERM_D)
    nobori_model(p, -39, -25, 13.5, PLASTER, VERM, INDIGO)
    nobori_model(p, -33.5, -21, 15.5, INDIGO, GOLD, PLASTER)
    nobori_model(p, -28, -26.5, 14, VERM, PLASTER, VERM_D)
    return p


@part_builder("KoiPond")
def build_KoiPond():
    p = dk.Part("KoiPond")
    patch(p, 68, 10, 14.5, 11.5, 0.0, 0.3, MOSS, 14, 0.06, 0.05, name="Bank")
    patch(p, 68, 10, 12.4, 9.4, 0.1, 0.6, WATER, 16, 0.07, 0.03, name="Water")
    for (cx, cz, r) in ((63, 7, 2.6), (74, 13, 3.0)):
        ring_flat(p, cx, cz, 1.6, r, 0.62, WATER_L, n=10, name="Ripple")
    # boulders around the shore
    for (x, z, sx, sy, sz, c) in ((56, 1.5, 4.2, 2.0, 4, STONE), (62, 0, 3.6, 1.6, 3, STONE_D), (73, -0.2, 4.4, 1.8, 3.2, STONE),
                                  (80, 2, 4, 2.0, 4, STONE_D), (81, 12.5, 3.2, 1.4, 4.4, STONE), (79, 19, 4.4, 1.8, 3.6, STONE_D),
                                  (70, 20, 3.6, 1.6, 3, STONE), (60, 19, 4.2, 2.0, 4, STONE_D), (55, 10.5, 3.4, 1.6, 4.4, STONE)):
        stone(p, x, z, sx / 2, sy, sz / 2, c, y0=0.0, sides=6, top=MOSS, name="Boulder")
    # lily pads with lotus flowers
    for (x, z, r, fl) in ((63, 6, 1.6, True), (74, 14, 1.9, True), (68, 14.5, 1.3, False), (72, 5, 1.2, False)):
        dk.cyl(p, (x, 0.66, z), r, 0.12, LEAF, verts=8, jitter=0.05, name="Pad")
        if fl:
            dk.cone(p, (x + 0.2, 0.7, z), 0.55, 0.7, PINK, verts=6, jitter=0.04, name="Lotus")
            dk.cone(p, (x + 0.2, 0.7, z), 0.28, 0.55, PINK_L, verts=5, name="LotusIn")

    def koi(x, z, ang, ln, body, spot):
        ca, sa = math.cos(ang), math.sin(ang)

        def T(u, v):
            return (x + u * ca - v * sa, z + u * sa + v * ca)
        shape = [(1.0, 0), (0.55, 0.38), (-0.1, 0.42), (-0.6, 0.2), (-0.85, 0.12), (-1.25, 0.55), (-1.1, 0.0), (-1.25, -0.55),
                 (-0.85, -0.12), (-0.6, -0.2), (-0.1, -0.42), (0.55, -0.38)]
        slab(p, [T(u * ln, v * ln) for u, v in shape], 0.06, 'xz', 0.63, body, 0.03, name="Koi")
        slab(p, [T(0.3 * ln, 0.0), T(0.0, 0.27 * ln), T(-0.35 * ln, 0.1 * ln), T(-0.3 * ln, -0.25 * ln), T(0.05 * ln, -0.25 * ln)],
             0.06, 'xz', 0.7, spot, 0.02, name="KoiSpot")
    koi(66, 11.5, 0.5, 2.6, KOI, WHITE)
    koi(71, 7.5, 3.6, 2.4, WHITE, VERM)
    koi(64.5, 14.5, 2.3, 2.2, (232, 190, 70), KOI)
    # reeds
    for (x, z) in ((78.5, 6.0), (79.3, 7.4), (78.0, 8.2), (57.5, 14.5), (56.8, 15.8)):
        rod(p, (x, 0.2, z), (x + 0.3, 1.9, z + 0.2), 0.07, LEAF_D, 4, r2=0.03, name="Reed")
        rod(p, (x + 0.27, 1.45, z + 0.18), (x + 0.3, 1.95, z + 0.2), 0.16, BRONZE_D, 5, name="Cattail")
    return p


def straw_dummy(p, x, z, h=5.6):
    post(p, x, z, 0, h + 0.4, 0.25, WOOD_D, 5, name="DummyPost")
    o = lathe(p, (x, 0.9, z), [(0.9, 0), (1.05, 0.6), (1.0, 2.6), (0.85, 3.8)], 6, STRAW, 0.08, name="DummyBody")
    for yy in (1.5, 2.9, 4.1):
        dk.cyl(p, (x, yy, z), 1.1, 0.22, BRONZE_D, verts=6, name="DummyRope")
    bx(p, x - 2.2, x + 2.2, 3.7, 4.4, z - 0.4, z + 0.4, STRAW_D, 0.08, name="DummyArms")
    dk.ball(p, (x, h + 0.6, z), 0.85, STRAW, scale=(1, 1, 1), subdiv=1, jitter=0.08, name="DummyHead")
    bx(p, x - 0.4, x + 0.4, h + 0.5, h + 0.8, z + 0.78, z + 0.9, BLACK, 0.02, name="DummyBand")


@part_builder("Dojo")
def build_Dojo():
    p = dk.Part("Dojo")
    bx(p, -81, -51, 0, 0.8, -54, -34, STONE_D, 0.06, name="Foundation")
    plank_row(p, -80, -52, -53, -35, 0.8, 1.4, 6, 'x', WOOD, 0.08, 0.07, name="Floor")
    bx(p, -79, -53, 1.4, 8.4, -53, -52.2, PLASTER, 0.03, name="BackWall")
    for x in (-79, -73, -66, -59, -53.6):
        bx(p, x - 0.2, x + 0.2, 1.4, 8.4, -52.2, -51.9, WOOD_D, 0.03, name="BackBeam")
    bx(p, -79, -53, 4.2, 4.6, -52.2, -51.9, WOOD_D, 0.03, name="BackBeam")
    for xo, xi in ((-79.0, -78.2), (-53.8, -53.0)):
        bx(p, xo, xi, 1.4, 8.4, -52.2, -37, PLASTER, 0.03, name="SideWall")
        out = xo - 0.12 if xo < -70 else xi + 0.0
        o2 = (xo - 0.15, xo) if xo < -70 else (xi, xi + 0.15)
        for z in (-50, -44, -38.5):
            bx(p, o2[0], o2[1], 1.4, 8.4, z - 0.2, z + 0.2, WOOD_D, 0.03, name="SideBeam")
        bx(p, o2[0], o2[1], 4.2, 4.6, -52.2, -37, WOOD_D, 0.03, name="SideBeam")
        bx(p, o2[0], o2[1], 5.0, 7.2, -48, -41, WOOD_D, 0.02, name="Window")
    for x in (-78.6, -71, -61, -53.4):
        pillar(p, x, -37, 1.4, 8.4, 0.5, VERM, 6, name="FrontPost")
    bx(p, -79.6, -52.4, 7.2, 8.4, -37.5, -36.5, WOOD_D, 0.04, name="Lintel")
    bx(p, -69, -63, 4.8, 7.2, -36.8, -36.5, PLASTER, 0.03, name="SignBoard")
    bx(p, -69.2, -62.8, 4.7, 4.9, -36.9, -36.5, WOOD_D, 0.02, name="SignFrame")
    bx(p, -69.2, -62.8, 7.1, 7.3, -36.9, -36.5, WOOD_D, 0.02, name="SignFrame")
    sign_marks(p, -66, 6.0, -36.5, 2.4, 1.8, BLACK)
    # paper screens in the hall
    for x0 in (-77.0, -63.0):
        bx(p, x0, x0 + 8, 1.4, 7.4, -45.2, -44.8, PLASTER, 0.02, name="Shoji")
        for k in range(5):
            bx(p, x0 + k * 2.0 - 0.1 + (0.1 if k == 4 else 0) * -1, x0 + k * 2.0 + 0.1 + (0.0 if k < 4 else -0.0), 1.4, 7.4, -44.8, -44.6, WOOD_D, 0.02, name="ShojiBar")
        for y in (3.4, 5.4):
            bx(p, x0, x0 + 8, y, y + 0.2, -44.8, -44.6, WOOD_D, 0.02, name="ShojiBar")
    bx(p, -67.4, -64.6, 2.8, 7.0, -52.2, -52.0, PLASTER_D, 0.02, name="Scroll")
    sign_marks(p, -66, 5.0, -52.0, 1.5, 1.6, BLACK)
    # weapon rack with staffs
    bx(p, -76, -75.5, 1.4, 6.6, -51.9, -51.3, WOOD_D, 0.03, name="RackPost")
    bx(p, -71.5, -71, 1.4, 6.6, -51.9, -51.3, WOOD_D, 0.03, name="RackPost")
    bx(p, -76, -71, 3.2, 3.6, -51.9, -51.3, WOOD_D, 0.03, name="RackRail")
    for k in range(4):
        x = -75.0 + k * 1.2
        rod(p, (x, 1.5, -50.8), (x + 0.2, 6.4, -51.5), 0.13, STEEL if k % 2 else WOOD_L, 4, name="Staff")
    # roof, two tiers, golden fish ornaments
    hip_roof(p, -66, -44, 8.4, 15, 10, 12.6, 7.4, 1.1, ROOF, 0.9, 0.5, trim=ROOF_L, name="RoofLow")
    gable(p, 'x', -78.4, -53.6, -44, 7.2, 9.4, 11.3, 0.5, ROOF, ROOF_L, n=3, name="RoofHigh")
    for xg in (-78.4, -53.6):
        gable_end(p, 'x', xg, -44, 6.5, 9.4, 11.0, 0.6, PLASTER)
        dk.cyl(p, (xg + (-0.35 if xg < -70 else 0.35), 9.9, -44), 0.6, 0.12, VERM, axis='x', verts=6, name="Crest")
    for sx in (-1, 1):
        dk.cone(p, (-66 + sx * 12.0, 11.0, -44), 0.5, 0.5, GOLD, verts=5, jitter=0.03, name="Shachi")
    straw_dummy(p, -75, -36)
    straw_dummy(p, -57, -36)
    return p


@part_builder("Temizuya")
def build_Temizuya():
    p = dk.Part("Temizuya")
    patch(p, -10, 19, 4.8, 4.0, 0.0, 0.12, GRAVEL, 8, 0.05, 0.03, name="Gravel")
    bx(p, -12.8, -7.2, 0, 1.8, 16.8, 21.2, STONE, 0.07, name="Basin")
    bx(p, -13.1, -6.9, 1.6, 2.0, 16.5, 21.5, STONE_L, 0.06, name="BasinRim")
    bx(p, -12.1, -7.9, 1.9, 2.1, 17.4, 20.6, WATER, 0.02, name="BasinWater")
    for x, z in ((-14, 15.8), (-6, 15.8), (-14, 22.2), (-6, 22.2)):
        pillar(p, x, z, 0, 5.5, 0.4, WOOD_D, 6)
    bx(p, -14.5, -5.5, 4.9, 5.5, 15.4, 22.8, WOOD_D, 0.04, name="Beam")
    hip_roof(p, -10, 19, 5.5, 4.8, 4.0, 2.0, 1.1, 1.5, ROOF, 0.5, 0.4, trim=ROOF_L, name="Roof")
    dk.ball(p, (-10, 7.1, 19), 0.3, GOLD, subdiv=1, name="Finial")
    # bamboo spout with a thin stream, bamboo ladle
    rod(p, (-10, 4.5, 16.2), (-10, 3.7, 18.2), 0.28, LEAF_D, 6, name="Spout")
    bx(p, -10.1, -9.9, 2.1, 3.65, 18.0, 18.2, WATER_L, 0.02, name="Stream")
    dk.cyl(p, (-11.3, 2.4, 20.0), 0.45, 0.5, LEAF, verts=6, name="LadleCup")
    rod(p, (-11.3, 2.55, 20.0), (-9.0, 2.45, 17.2), 0.12, LEAF, 4, name="LadleHandle")
    for (x, z, r) in ((-10, 22.8, 0.8), (-12.3, 23.0, 0.55)):
        pass
    for (sx, sz, sr) in ((-13.2, 22.7, 1.0), (-7.2, 22.8, 0.9), (-14.0, 16.6, 0.8)):
        blob(p, (sx, 0.9 * sr, sz), sr, LEAF_D, sy=0.9, sides=6, jitter=0.1, name="Shrub")
        for k in range(3):
            dk.cone(p, (sx + (k - 1) * 0.5, 1.6 * sr, sz + 0.5), 0.22, 0.2, PINK, verts=4, name="Blossom")
    stone(p, -8.5, 15.8, 0.9, 0.6, 0.8, STONE_D, top=MOSS, name="Rock")
    stone(p, -11.8, 22.4, 0.8, 0.5, 0.7, STONE, top=MOSS, name="Rock")
    return p


def arrow(p, x, y, z, dz=1.9, col=WOOD_L):
    rod(p, (x, y, z), (x + 0.15, y + 0.15, z + dz), 0.07, col, 4, name="Arrow")
    bx(p, x + 0.1, x + 0.3, y + 0.1, y + 0.32, z + dz - 0.5, z + dz, VERM, 0.02, name="Fletch")


@part_builder("Archery")
def build_Archery():
    p = dk.Part("Archery")
    o = frustum(p, -62, -15, 0, 3.4, 22, 2.0, 20.0, 1.2, EARTH_D, 0.07, name="Bank")
    recolor(o, lambda c, n, i: GRASS_D if n[1] > 0.5 else None, 0.05)
    for x in (-67, -62, -57):
        for sg in (-1, 1):
            rod(p, (x + sg * 1.6, 0.15, -12.6), (x + sg * 0.5, 3.3, -13.5), 0.22, WOOD_D, 4, name="Leg")
        post(p, x, -13.5, 2.4, 4.6, 0.3, WOOD_D, 5, name="TargetPost")
        disc(p, x, 4.7, -13.65, 2.4, STRAW, 'z', 8, 0.5, name="TargetRim")
        disc(p, x, 4.7, -13.35, 2.1, WHITE, 'z', 8, 0.2, name="TargetFace")
        disc(p, x, 4.7, -13.22, 1.45, BLACK, 'z', 8, 0.2, name="TargetRing")
        disc(p, x, 4.7, -13.1, 0.95, WHITE, 'z', 8, 0.2, name="TargetRing2")
        disc(p, x, 4.7, -13.0, 0.5, VERM, 'z', 8, 0.2, name="TargetEye")
    arrow(p, -66.5, 5.2, -13.0)
    arrow(p, -67.3, 4.0, -13.0)
    arrow(p, -56.6, 4.9, -13.0)
    # roof over the bank
    for x in (-72, -62, -52):
        pillar(p, x, -12, 0, 7.6, 0.4, WOOD_D, 6, name="RoofPost")
    bx(p, -72.5, -51.5, 6.6, 7.6, -12.4, -11.6, WOOD_D, 0.04, name="Beam")
    hip_roof(p, -62, -13.5, 7.6, 11.0, 2.5, 9.6, 0.9, 0.7, ROOF, 0.4, 0.3, trim=ROOF_L, name="Roof")
    # shooting line: boards, red line, bow rack with two bows
    plank_row(p, -72, -52, -5.5, -2, 0, 0.5, 4, 'x', WOOD, 0.06, 0.07, name="Boards")
    bx(p, -72, -52, 0.5, 0.56, -5.5, -5.0, VERM, 0.03, name="Line")
    for x in (-70, -64):
        pillar(p, x, -3, 0.5, 4.4, 0.3, WOOD_D, 5, name="RackPost")
    bx(p, -71, -63, 3.6, 4.1, -3.3, -2.7, WOOD, 0.04, name="Rack")
    for bxp in (-68.5, -66.0):
        pts = [(0, 4.1), (0.55, 5.1), (0.7, 6.2), (0.55, 7.3), (0, 8.1)]
        for a, b in zip(pts, pts[1:]):
            rod(p, (bxp + a[0], a[1], -3.0), (bxp + b[0], b[1], -3.0), 0.13, WOOD_D, 4, name="Bow")
        rod(p, (bxp, 4.1, -3.0), (bxp, 8.1, -3.0), 0.04, WHITE, 3, name="String")
    return p


@part_builder("Bridge")
def build_Bridge():
    p = dk.Part("Bridge")
    z0, z1 = 7.5, 12.5
    xs = [57 + 22 * k / 12 for k in range(13)]

    def top(x):
        u = (x - 68.0) / 11.0
        return 1.2 + 3.0 * (1 - u * u)
    deck_t = [(x, top(x)) for x in xs]
    deck_b = [(x, top(x) - 0.55) for x in xs]
    o = slab(p, deck_b + deck_t[::-1], z1 - z0, 'xy', (z0 + z1) / 2, VERM, 0.03, name="Deck")
    recolor(o, lambda c, n, i: None, 0.0)
    # plank lines on top face
    for k in range(1, 12):
        x = xs[k]
        sl = (top(xs[k + 1]) - top(xs[k - 1])) / (xs[k + 1] - xs[k - 1]) if k < 12 else 0
        bx(p, x - 0.07, x + 0.07, top(x) - 0.02, top(x) + 0.07, z0 + 0.2, z1 - 0.2, DARK_RED if False else VERM_D, 0.02, rot=(0, 0, math.degrees(math.atan(sl))), name="Plank")
    # under-beams
    for zz in (z0 + 0.5, z1 - 0.5):
        slab(p, [(x, top(x) - 0.55) for x in xs[1:-1]] + [(x, top(x) - 1.1) for x in xs[-2:0:-1]], 0.5, 'xy', zz, WOOD_D, 0.04, name="Beam")
    # rails with posts, gold giboshi on the ends
    for zz in (z0 + 0.3, z1 - 0.3):
        for k in range(0, 13, 2):
            x = xs[k]
            post(p, x, zz, top(x), top(x) + 1.7, 0.22, VERM_D, 5, name="RailPost")
            dk.ball(p, (x, top(x) + 1.9, zz), 0.28, GOLD, subdiv=1, name="Gibo") if k in (0, 12) else None
        slab(p, [(x, top(x) + 1.35) for x in xs] + [(x, top(x) + 1.6) for x in xs[::-1]], 0.35, 'xy', zz, VERM, 0.03, name="Rail")
        slab(p, [(x, top(x) + 0.7) for x in xs] + [(x, top(x) + 0.85) for x in xs[::-1]], 0.25, 'xy', zz, VERM_D, 0.03, name="LowRail")
    # stone abutments at both ends
    for (xa, xb) in ((56.9, 59.3), (76.7, 79.1)):
        bx(p, xa, xb, 0, 1.3, 7.6, 12.4, STONE, 0.06, name="Abutment")
        bx(p, xa - 0.0, xb, 1.3, 1.45, 7.5, 12.5, STONE_L, 0.05, name="AbutmentCap")
    return p


@part_builder("RockGarden")
def build_RockGarden():
    p = dk.Part("RockGarden")
    bx(p, 11, 33, 0, 0.3, -2, 14, GRAVEL, 0.03, name="Bed")
    for (x0, x1, z0, z1) in ((11, 33, -2, -1.6), (11, 33, 13.6, 14), (11, 11.4, -2, 14), (32.6, 33, -2, 14)):
        bx(p, x0, x1, 0, 0.7, z0, z1, WOOD_D, 0.05, name="Frame")
    for z in (-0.5, 12.4):
        pass
    # rake lines: straight on the sides, rings around the big rocks
    for k in range(4):
        bx(p, 12.0, 32, 0.3, 0.38, 0.4 + k * 3.4 - (0 if k < 3 else 0), 0.7 + k * 3.4, GRAVEL_D, 0.03, name="Rake") if k in (0, 3) else None
    for (cx, cz, sx) in ((18, 3, 1.0), (27, 2, 0.9), (22.5, 7.5, 0.8)):
        ring_flat(p, cx, cz, 3.2 * sx + 0.5, 3.8 * sx + 0.5, 0.38, GRAVEL_D, n=12, name="Ring")
        if cx == 22.5:
            ring_flat(p, cx, cz, 5.0 * sx + 0.5, 5.6 * sx + 0.5, 0.38, GRAVEL_D, n=12, name="Ring")
    for (x, z, sx, sy, sz, c) in ((18, 3, 4, 3.2, 3.4, STONE), (22.5, 7.5, 2.6, 2, 2.4, STONE_D), (27, 2, 3.2, 2.4, 3, STONE),
                                  (28.5, 10, 2, 1.4, 2, STONE_D), (16, 10.5, 1.8, 1.2, 1.8, STONE)):
        stone(p, x, z, sx / 2, sy, sz / 2, c, y0=0.2, sides=6, top=MOSS, name="Rock")
    # bonsai pine in a pot
    bx(p, 12.8, 15.2, 0.3, 0.9, 10.3, 12.7, (170, 96, 70), 0.05, name="Pot")
    pts = [(14, 0.9, 11.5), (13.6, 1.8, 11.5), (14.5, 2.7, 11.6), (14, 3.5, 11.5)]
    for a, b in zip(pts, pts[1:]):
        rod(p, a, b, 0.4, WOOD_D, 5, name="Trunk")
    for (cx, y, cz, rr) in ((13.2, 3.4, 11.1, 2.0), (15.2, 4.2, 12.0, 1.7), (13.9, 5.0, 11.6, 1.3)):
        lathe(p, (cx, y - 0.45, cz), [(0, 0), (rr, 0.2), (rr * 0.8, 0.7), (0, 0.9)], 7, LEAF_D, 0.08, name="Pine")
        lathe(p, (cx, y - 0.45, cz), [(rr * 0.8, 0.6), (rr * 0.45, 0.9), (0, 1.0)], 7, LEAF, 0.08, name="PineTop")
    # tiny lantern
    lathe(p, (31, 0.3, 12), [(1.0, 0), (1.0, 0.8), (0.4, 1.0)], 6, STONE_D, 0.05, name="Toro")
    post(p, 31, 12, 1.0, 2.3, 0.35, STONE, 6, name="Toro")
    bx(p, 30.4, 31.6, 2.3, 3.0, 11.4, 12.6, WARM, 0.03, name="Toro")
    lathe(p, (31, 3.0, 12), [(1.4, 0), (1.2, 0.2), (0.2, 0.8)], 6, STONE, 0.05, name="Toro")
    return p


@part_builder("Sakura")
def build_Sakura():
    p = dk.Part("Sakura")
    patch(p, 8, 22, 9.0, 8.8, 0.3, 0.5, PINK, 12, 0.1, 0.05, name="Petals")
    patch(p, 11, 26, 4.5, 3.5, 0.5, 0.56, PINK_L, 8, 0.2, 0.04, name="Petals")
    patch(p, 4, 18, 3.5, 3.0, 0.5, 0.56, PINK_D, 8, 0.2, 0.04, name="Petals")
    # twisted trunk
    rings = []
    C = [(8.0, 0.3, 22.0, 2.4), (8.3, 1.8, 22.1, 1.6), (7.5, 4.0, 22.3, 1.4), (8.4, 6.5, 21.8, 1.25), (8.0, 9.2, 22.0, 1.1)]
    for (cx, y, cz, r) in C:
        rings.append([(cx + r * math.cos(2 * pi * i / 7), y, cz + r * math.sin(2 * pi * i / 7)) for i in range(7)])
    loft(p, rings, WOOD_D, 0.07, name="Trunk")
    for (A, B, r) in (((8, 8.0, 22), (4.2, 13, 21.8), 0.65), ((8, 8.2, 22), (12, 13.5, 22.3), 0.65), ((8, 9.0, 22), (8.5, 15, 24.5), 0.55),
                      ((7.8, 7.5, 22), (3.5, 11, 25), 0.5)):
        rod(p, A, B, r, WOOD_D, 5, r2=r * 0.5, jitter=0.05, name="Branch")
    BL = [(255, 176, 206), (246, 132, 182), (255, 212, 228)]
    for k, (x, y, z, r, sy) in enumerate(((8, 15.2, 22, 5.5, 0.8), (1.5, 14.0, 25, 4.8, 0.78), (14.8, 16.0, 18.3, 5.2, 0.8), (9, 19.0, 23, 4.4, 0.72),
                                          (4.5, 17.2, 19, 3.8, 0.8), (13.5, 14.0, 24.5, 3.8, 0.8), (16.8, 18.0, 15.8, 3.2, 0.8), (2, 17.5, 28, 3.2, 0.8),
                                          (7, 13, 27.5, 3.2, 0.7), (12, 19.2, 20, 3.0, 0.8), (4, 20, 24, 2.6, 0.8))):
        o = dk.ball(p, (x, y, z), r, BL[k % 3], scale=(1, sy, 1), subdiv=2, rot=(R.uniform(-20, 20), R.uniform(0, 90), 0), jitter=0.08, name="Canopy")
        for v in o.data.vertices:
            v.co *= R.uniform(0.9, 1.1)
    for k in range(16):                                   # falling petals
        a = R.uniform(0, 2 * pi)
        d = R.uniform(2, 9)
        dk.cone(p, (8 + d * math.cos(a), R.uniform(6, 12), 22 + d * math.sin(a)), 0.32, 0.14, BL[k % 3], verts=4, name="Petal")
    # hanami bench
    bx(p, 5.2, 10.8, 1.0, 1.4, 27.4, 29.2, WOOD_L, 0.05, name="Bench")
    for x in (5.7, 10.3):
        bx(p, x - 0.25, x + 0.25, 0.3, 1.0, 27.6, 29.0, WOOD_D, 0.04, name="BenchLeg")
    bx(p, 5.8, 8.2, 1.4, 1.5, 27.7, 28.9, VERM, 0.03, name="Cloth")
    return p


@part_builder("Taiko")
def build_Taiko():
    p = dk.Part("Taiko")
    plank_row(p, -59, -45, 7, 13, 0, 0.6, 5, 'z', WOOD, 0.06, 0.07, name="Stage")
    # big drum: barrel body with skins on both faces
    o = lathe(p, (-54, 4.0, 7.6), [(3.0, 0), (3.2, 0.3), (3.5, 1.4), (3.55, 2.4), (3.5, 3.4), (3.2, 4.5), (3.0, 4.8)], 10, (176, 44, 36), 0.05, axis='z', name="Drum")
    recolor(o, lambda c, n, i: (250, 240, 214) if abs(n[2]) > 0.85 else None, 0.02)
    for k in range(10):                                  # gold tacks around the skin on the road side
        a = 2 * pi * k / 10
        dk.cyl(p, (-54 + 3.15 * math.cos(a), 4.0 + 3.15 * math.sin(a), 12.45), 0.2, 0.25, GOLD, axis='z', verts=4, name="Tack")
    dk.cyl(p, (-54, 4.0, 12.42), 0.8, 0.1, VERM, axis='z', verts=6, name="DrumEye")
    for k in range(3):
        a = 2 * pi * k / 3 + 0.5
        dk.cyl(p, (-54 + 1.75 * math.cos(a), 4.0 + 1.75 * math.sin(a), 12.42), 0.6, 0.1, VERM, axis='z', verts=5, name="Tomoe")
    for k in range(3):
        dk.cyl(p, (-54, 2.0 + k * 2.0, 10.0), 3.58, 0.25, BRONZE_D, axis='z', verts=10, name="DrumBand") if False else None
    for sx in (-1, 1):
        bx(p, -54 + sx * 3.9 - 0.8, -54 + sx * 3.9 + 0.8, 0.6, 3.4, 8.0, 12.0, WOOD_D, 0.04, name="Cradle")
        bx(p, -54 + sx * 3.9 - 0.4, -54 + sx * 3.9 + 0.4, 3.4, 4.0, 8.3, 11.7, WOOD_D, 0.04, name="CradleTop")
    bx(p, -57.6, -50.4, 0.6, 1.2, 9.4, 10.6, WOOD_D, 0.04, name="Crossbar")
    # small drum on a stand, drumsticks
    o = lathe(p, (-47, 3.2, 8.5), [(1.7, 0), (2.0, 0.8), (2.0, 2.2), (1.7, 3.0)], 8, VERM, 0.05, axis='z', name="SmallDrum")
    recolor(o, lambda c, n, i: PLASTER if abs(n[2]) > 0.85 else None, 0.03)
    for k in range(8):
        a = 2 * pi * k / 8
        dk.cyl(p, (-47 + 1.75 * math.cos(a), 3.2 + 1.75 * math.sin(a), 11.45), 0.16, 0.2, GOLD, axis='z', verts=4, name="SmallTack")
    dk.cyl(p, (-47, 3.2, 11.45), 0.5, 0.08, VERM, axis='z', verts=6, name="SmallEye")
    for sz in (-1, 1):
        bx(p, -48.0, -46.0, 0.6, 1.4, 10 + sz * 1.5 - 0.3, 10 + sz * 1.5 + 0.3, WOOD_D, 0.04, name="SmallLeg")
        rod(p, (-47.8, 1.4, 10 + sz * 1.5), (-47.0, 2.0, 10 + sz * 1.0), 0.2, WOOD_D, 4, name="SmallBrace")
    for k, (a, b) in enumerate((((-57.5, 0.75, 12.3), (-55.6, 0.75, 8.6)), ((-56.8, 0.75, 12.5), (-57.2, 0.75, 8.2)))):
        rod(p, a, b, 0.2, WOOD_L, 5, name="Bachi")
        dk.ball(p, b, 0.26, WOOD_L, subdiv=1, name="BachiEnd") if False else None
    return p


@part_builder("BellTower")
def build_BellTower():
    p = dk.Part("BellTower")
    cx, cz = -34, -42
    bx(p, -40, -28, 0, 1, -48, -36, STONE_D, 0.06, name="Base")
    bx(p, -39.4, -28.6, 1, 1.35, -47.4, -36.6, STONE, 0.05, name="BaseTop")
    posts = [(-38.6, -46.6), (-29.4, -46.6), (-38.6, -37.4), (-29.4, -37.4)]
    for (x, z) in posts:
        dk.cyl(p, (x, 1.5, z), 1.0, 0.7, STONE, verts=6, name="Footing")
        pillar(p, x, z, 1.35, 8, 0.6, VERM, 6, 0.55, name="Post")
    for z in (-46.6, -37.4):
        bx(p, -39.4, -28.6, 6.9, 7.8, z - 0.4, z + 0.4, WOOD_D, 0.04, name="Beam")
        bx(p, -39.4, -28.6, 3.4, 3.8, z - 0.25, z + 0.25, WOOD_D, 0.04, name="LowBeam")
    for x in (-38.6, -29.4):
        bx(p, x - 0.4, x + 0.4, 6.9, 7.8, -47, -37, WOOD_D, 0.04, name="Beam")
    bx(p, -39.2, -28.8, 7.0, 7.9, cz - 0.7, cz + 0.7, WOOD_D, 0.04, name="BellBeam")
    hip_roof(p, cx, cz, 8.0, 6.0, 6.0, 3.6, 3.6, 1.4, ROOF, 0.8, 0.45, trim=ROOF_L, name="RoofLow")
    hip_roof(p, cx, cz, 9.3, 4.0, 4.0, 0.5, 0.5, 1.3, ROOF, 0.5, 0.35, trim=ROOF_L, name="RoofHigh")
    dk.ball(p, (cx, 10.7, cz), 0.3, GOLD, subdiv=1, name="Finial")
    for sx in (-1, 1):
        for sz in (-1, 1):
            dk.cyl(p, (cx + sx * 5.9, 8.2, cz + sz * 5.9), 0.06, 0.6, GOLD, verts=4, top_radius=0.26, name="EaveBell")
    # the great bronze bell
    o = lathe(p, (cx, 2.6, cz), [(2.1, 0), (2.15, 0.3), (1.9, 1.0), (1.6, 2.4), (1.35, 3.7), (1.05, 4.3), (0.5, 4.6)], 8, (196, 146, 76), 0.05, name="Bell")
    recolor(o, lambda c, n, i: BRONZE_D if (2.6 < c[1] < 3.1 or 4.9 < c[1] < 5.3) and abs(n[1]) < 0.9 else None, 0.04)
    for k in range(4):
        a = 2 * pi * k / 4 + pi / 4
        dk.cyl(p, (cx + 1.55 * math.cos(a), 5.8, cz + 1.55 * math.sin(a)), 0.22, 0.3, GOLD, verts=5, name="BellBoss")
    bx(p, -36.4, -31.6, 5.1, 6.9, -37.05, -36.85, PLASTER, 0.03, name="NameBoard")
    bx(p, -36.5, -31.5, 5.0, 5.15, -37.1, -36.8, WOOD_D, 0.02, name="NameFrame")
    sign_marks(p, cx, 6.0, -36.85, 1.4, 1.2, BLACK)
    bx(p, cx - 0.35, cx + 0.35, 7.7, 8.0, cz - 0.35, cz + 0.35, BRONZE_D, 0.04, name="BellRing")
    # striker log on two ropes
    for z in (-43.4, -38.8):
        rod(p, (cx, 7.0, z), (cx, 4.9, z), 0.12, BRONZE_D, 4, name="Rope")
    dk.cyl(p, (cx, 4.8, -41), 0.5, 6.4, WOOD, axis='z', verts=6, jitter=0.05, name="Striker")
    dk.cyl(p, (cx, 4.8, -37.9), 0.55, 0.5, BLACK, axis='z', verts=6, name="StrikerCap")
    # hanging lanterns at the front posts and stone step
    for x in (-38.6, -29.4):
        lathe(p, (x, 4.4, -36.4), [(0.3, 0), (0.75, 0.4), (0.75, 0.8), (0.3, 1.2)], 6, VERM, 0.04, name="Lantern")
        rod(p, (x, 5.6, -36.4), (x, 6.9, -36.7), 0.05, BLACK, 4, name="Cord")
    bx(p, -36.6, -31.4, 1.0, 1.6, -36.9, -36.1, STONE_L, 0.05, name="Step")
    return p


@part_builder("Armor")
def build_Armor():
    p = dk.Part("Armor")
    cx, cz = -82, 6
    bx(p, -87, -77, 0, 0.8, 2, 10, WOOD_D, 0.05, name="Dais")
    bx(p, -85.8, -78.2, 0.8, 1.3, 3.2, 8.8, WOOD, 0.05, name="DaisTop")
    bx(p, -82.4, -81.6, 1.3, 3.2, 5.6, 6.4, WOOD_D, 0.04, name="Stand")
    bx(p, -86.4, -77.6, 6.0, 6.5, 5.3, 5.8, WOOD_D, 0.04, name="Arms")
    bx(p, -86.4, -85.8, 1.3, 6.0, 5.3, 5.8, WOOD_D, 0.04, name="ArmsPost")
    bx(p, -78.2, -77.6, 1.3, 6.0, 5.3, 5.8, WOOD_D, 0.04, name="ArmsPost")
    # skirt plates: alternating lacing colours
    rows = [(1.8, 2.5, 6.4, 4.4, INDIGO), (2.5, 3.1, 6.0, 4.1, VERM_D), (3.1, 3.8, 5.6, 3.8, INDIGO)]
    for (y0, y1, w, d, col) in rows:
        bx(p, cx - w / 2, cx + w / 2, y0, y1, cz - d / 2, cz + d / 2, col, 0.04, name="Skirt")
    for k in range(5):
        bx(p, cx - 3.0 + k * 1.5 - 0.06, cx - 3.0 + k * 1.5 + 0.06, 1.8, 3.8, cz + 2.2 - 0.1, cz + 2.3, GOLD_D, 0.02, name="SkirtLace")
    # cuirass with lacing rows and a golden plate
    bx(p, -84.2, -79.8, 3.8, 7.8, 4.6, 7.4, VERM, 0.04, name="Cuirass")
    for y in (4.5, 5.4, 6.3, 7.1):
        bx(p, -84.2, -79.8, y, y + 0.35, 7.4, 7.55, INDIGO, 0.03, name="Lacing")
    bx(p, -82.7, -81.3, 5.0, 6.5, 7.4, 7.65, GOLD, 0.03, name="Plate")
    # shoulder plates (sode), three layers each
    for sg in (-1, 1):
        for k in range(3):
            w = 2.2 - 0.0 * k
            xa = cx + sg * (2.6 + 0.0) - w / 2 + sg * 0.0
            bx(p, xa - 0.0, xa + w, 7.8 - 0.75 * (k + 1), 7.8 - 0.75 * k, 4.4, 7.6, VERM_D if k % 2 == 0 else INDIGO, 0.04, name="Sode") if False else None
        for k in range(3):
            y1, y0 = 7.8 - 0.75 * k, 7.8 - 0.75 * (k + 1)
            xin, xout = cx + sg * 2.2, cx + sg * (4.4 + 0.15 * k)
            bx(p, min(xin, xout), max(xin, xout), y0, y1, 4.4, 7.6, VERM_D if k % 2 == 0 else INDIGO, 0.04, name="Sode")
        bx(p, cx + sg * 3.3 - 0.05, cx + sg * 3.3 + 0.05, 5.55, 7.8, 7.6, 7.7, GOLD_D, 0.02, name="SodeLace")
    # neck guard, face mask, helmet bowl and gold crescent
    frustum(p, cx, cz, 7.8, 8.7, 3.0, 2.8, 2.6, 2.4, INDIGO, 0.04, name="Neck")
    bx(p, -83.0, -81.0, 8.3, 9.7, 6.5, 7.2, VERM_D, 0.03, name="Mask")
    for sx in (-1, 1):
        bx(p, cx + sx * 0.55 - 0.25, cx + sx * 0.55 + 0.25, 9.0, 9.3, 7.2, 7.3, BLACK, 0.02, name="Eye")
    bx(p, -82.6, -81.4, 8.45, 8.7, 7.2, 7.3, WHITE, 0.02, name="Teeth")
    bx(p, -82.8, -81.2, 8.8, 9.0, 7.2, 7.28, BLACK, 0.02, name="Moustache")
    sh = lathe(p, (cx, 8.9, cz), [(3.4, 0), (3.1, 0.5), (2.2, 1.3)], 8, INDIGO_L, 0.04, name="Shikoro")
    drop_faces(sh, lambda n: n[2] > 0.5)
    lathe(p, (cx, 9.6, cz), [(2.0, 0), (2.0, 0.7), (1.6, 1.5), (0.8, 2.0), (0, 2.2)], 8, STEEL_D, 0.05, name="Bowl")
    dk.cyl(p, (cx, 9.8, cz), 2.1, 0.3, GOLD, verts=8, name="Brim")
    slab(p, [(-82, 11.0), (-84.4, 11.8), (-85.6, 13.4), (-84.1, 12.9), (-82, 12.0), (-79.9, 12.9), (-78.4, 13.4), (-79.6, 11.8)], 0.45, 'xy', 7.5, GOLD, 0.03, name="Crescent")
    dk.cyl(p, (cx, 11.0, 7.5), 0.45, 0.3, VERM, axis='z', verts=6, name="Gem")
    # katana on a two-forked rest in front of the dais
    for x in (-84.6, -80.4):
        bx(p, x - 0.2, x + 0.2, 0.8, 2.0, 8.9, 9.5, WOOD_D, 0.04, name="SwordRest")
        bx(p, x - 0.5, x + 0.5, 1.9, 2.2, 8.9, 9.5, WOOD_D, 0.04, name="SwordRestTop")
    bx(p, -85.8, -81.4, 2.2, 2.45, 9.05, 9.35, STEEL, 0.03, name="Blade")
    dk.cyl(p, (-81.3, 2.33, 9.2), 0.5, 0.15, GOLD, axis='x', verts=6, name="Tsuba")
    bx(p, -81.2, -78.8, 2.2, 2.5, 9.0, 9.4, BLACK, 0.02, name="Hilt")
    return p


@part_builder("ShrineHall")
def build_ShrineHall():
    p = dk.Part("ShrineHall")
    cx, cz = 66, -49
    bx(p, 51, 81, 0, 1.6, -59, -39, STONE, 0.06, name="Terrace")
    bx(p, 50.6, 81.4, 0, 0.5, -59.4, -38.6, STONE_D, 0.06, name="TerraceFoot") if False else None
    bx(p, 60.5, 71.5, 0, 1.1, -39, -37, STONE_L, 0.05, name="Step2")
    bx(p, 60, 72, 0, 0.6, -37, -35, STONE_L, 0.05, name="Step1")
    plank_row(p, 54.8, 77.2, -57.2, -42, 1.6, 2.0, 5, 'x', WOOD, 0.06, 0.06, name="Floor")
    bx(p, 54, 78, 1.6, 9, -58, -57.2, PLASTER, 0.03, name="BackWall")
    bx(p, 54, 54.8, 1.6, 9, -57.2, -42, PLASTER, 0.03, name="SideWall")
    bx(p, 77.2, 78, 1.6, 9, -57.2, -42, PLASTER, 0.03, name="SideWall")
    for y in (4.6, 8.0):
        bx(p, 54, 78, y, y + 0.4, -58.2, -57.2, WOOD_D, 0.03, name="WallBand")
        bx(p, 53.8, 54.8, y, y + 0.4, -57.2, -42, WOOD_D, 0.03, name="WallBand")
        bx(p, 77.2, 78.2, y, y + 0.4, -57.2, -42, WOOD_D, 0.03, name="WallBand")
    for x in (55, 62, 70, 77):
        pillar(p, x, -41.5, 1.6, 9, 0.75, VERM, 6, name="Pillar")
        dk.cyl(p, (x, 1.9, -41.5), 1.0, 0.6, STONE_D, verts=6, name="PillarBase")
    bx(p, 54.2, 77.8, 7.7, 8.9, -42.2, -40.8, VERM_D, 0.03, name="Lintel")
    for k in range(7):
        bx(p, 55 + k * 3.6, 55.5 + k * 3.6, 8.9, 9.0, -42.2, -40.8, GOLD_D, 0.02, name="Stud") if False else None
    bx(p, 62, 70, 1.6, 7.4, -56, -55.4, VERM_D, 0.03, name="Doors")
    bx(p, 65.9, 66.1, 1.6, 7.4, -55.4, -55.3, BLACK, 0.02, name="DoorSeam")
    for sx in (-1, 1):
        for y in (3.2, 4.6, 6.0):
            bx(p, 66 + sx * 1.8 - 0.3, 66 + sx * 1.8 + 0.3, y, y + 0.6, -55.3, -55.1, GOLD, 0.02, name="DoorStud")
    # offering box, gong rope and bell, sacred rope with paper strips
    bx(p, 63.4, 68.6, 2.0, 3.6, -46, -44, WOOD, 0.05, name="OfferBox")
    for k in range(6):
        bx(p, 63.6 + k * 0.82, 63.8 + k * 0.82, 2.2, 3.4, -44.0, -43.9, WOOD_D, 0.02, name="OfferSlat")
    bx(p, 63.2, 68.8, 3.6, 3.9, -46.2, -43.8, WOOD_D, 0.04, name="OfferLid")
    for k in range(3):
        rod(p, (66, 7.6 - k * 1.1, -42.6), (66, 6.5 - k * 1.1, -42.6), 0.2, VERM if k % 2 == 0 else WHITE, 4, name="GongRope")
    dk.ball(p, (66, 4.0, -42.6), 0.85, GOLD, subdiv=1, name="Gong")
    bx(p, 65.9, 66.1, 3.3, 4.0, -41.8, -41.72, BLACK, 0.02, name="GongSlit")
    for k in range(5):
        x0, x1 = 55.3 + k * 4.4, 55.3 + (k + 1) * 4.4
        rod(p, (x0, 7.3 - (0.2 if k % 4 == 0 else 0.35), -40.7), (x1, 7.3 - (0.2 if k % 3 == 1 else 0.35), -40.7), 0.3, STRAW, 5, name="Shimenawa")
    for k in range(6):
        x = 57.8 + k * 3.4
        bx(p, x - 0.3, x + 0.3, 6.0, 7.0, -40.75, -40.65, WHITE, 0.02, name="Shide")
    bx(p, 63.4, 68.6, 5.4, 6.9, -41.2, -40.9, BLACK, 0.02, name="Plaque") if False else None
    for x in (61, 71):
        pillar(p, x, -36.2, 0.6, 7.4, 0.5, VERM, 6, name="PorchPost")
    bx(p, 60.2, 71.8, 6.9, 7.4, -36.7, -35.7, WOOD_D, 0.04, name="PorchBeam")
    gable(p, 'z', -41.5, -35.3, 66, 6.2, 7.4, 9.3, 0.5, ROOF, ROOF_L, n=3, name="Porch")
    gable_end(p, 'z', -35.45, 66, 5.8, 7.4, 9.0, 0.4, PLASTER)
    dk.cyl(p, (66, 8.1, -35.2), 0.6, 0.14, GOLD, axis='z', verts=6, name="Crest")
    # roofs: three tiers and golden crossed finials
    hip_roof(p, cx, cz, 9.0, 15.0, 10.0, 12.4, 8.0, 1.4, ROOF, 1.0, 0.55, trim=ROOF_L, name="RoofA")
    hip_roof(p, cx, cz, 10.2, 12.2, 8.0, 8.0, 3.6, 1.8, ROOF, 0.7, 0.45, trim=ROOF_L, name="RoofB")
    hip_roof(p, cx, cz, 11.7, 8.0, 3.8, 6.2, 1.8, 1.3, ROOF, 0.4, 0.4, trim=ROOF_L, name="RoofC")
    for sx in (-1, 1):
        for sg in (-1, 1):
            bx(p, cx + sx * 6.5 - 0.2, cx + sx * 6.5 + 0.2, 12.6, 14.4, -49.3, -48.7, GOLD, 0.03, rot=(0, 0, sg * 28), name="Chigi")
    return p


def komainu_model(p, x, z, open_mouth, ball_paw):
    bx(p, x - 2.2, x + 2.2, 0, 2.0, z - 2.2, z + 2.2, STONE_D, 0.06, name="Pedestal")
    bx(p, x - 2.0, x + 2.0, 2.0, 2.3, z - 2.0, z + 2.0, STONE_L, 0.05, name="PedestalTop")
    # haunches, back and chest
    for sx in (-1, 1):
        blob(p, (x + sx * 1.15, 3.3, z - 1.0), 1.15, STONE, sy=0.95, sides=6, jitter=0.07, name="Haunch")
    bx(p, x - 1.5, x + 1.5, 2.3, 4.6, z - 2.0, z + 0.4, STONE, 0.05, name="Body")
    for sx in (-1, 1):
        bx(p, x + sx * 0.75 - 0.4, x + sx * 0.75 + 0.4, 2.3, 4.8, z + 0.3, z + 1.3, STONE, 0.05, name="Leg")
        bx(p, x + sx * 0.75 - 0.5, x + sx * 0.75 + 0.5, 2.3, 2.7, z + 0.9, z + 1.9, STONE_L, 0.05, name="Paw")
    bx(p, x - 0.9, x + 0.9, 4.3, 6.4, z - 0.3, z + 1.0, STONE, 0.05, name="Neck")
    bx(p, x - 1.15, x + 1.15, 4.3, 4.8, z - 0.1, z + 1.3, VERM, 0.03, name="Bib")
    # head
    bx(p, x - 1.3, x + 1.3, 5.9, 8.0, z + 0.2, z + 1.8, STONE_L, 0.05, name="Head")
    if open_mouth:
        bx(p, x - 0.95, x + 0.95, 6.7, 7.6, z + 1.8, z + 2.2, STONE_L, 0.05, name="UpperJaw")
        bx(p, x - 0.85, x + 0.85, 5.7, 6.1, z + 1.1, z + 2.1, STONE_L, 0.05, name="LowerJaw")
        bx(p, x - 0.6, x + 0.6, 6.1, 6.25, z + 1.2, z + 2.0, VERM, 0.03, name="Tongue")
        for sx in (-1, 1):
            bx(p, x + sx * 0.6 - 0.1, x + sx * 0.6 + 0.1, 6.2, 6.7, z + 2.05, z + 2.15, WHITE, 0.02, name="Fang")
    else:
        bx(p, x - 0.95, x + 0.95, 5.9, 7.6, z + 1.8, z + 2.2, STONE_L, 0.05, name="Muzzle")
        bx(p, x - 0.8, x + 0.8, 6.55, 6.68, z + 2.2, z + 2.26, BLACK, 0.02, name="Mouth")
    for sx in (-1, 1):
        bx(p, x + sx * 0.7 - 0.28, x + sx * 0.7 + 0.28, 7.2, 7.7, z + 1.8, z + 1.95, WHITE, 0.02, name="Eye")
        bx(p, x + sx * 0.7 - 0.12, x + sx * 0.7 + 0.12, 7.3, 7.6, z + 1.95, z + 2.02, BLACK, 0.02, name="Pupil")
        bx(p, x + sx * 0.7 - 0.45, x + sx * 0.7 + 0.45, 7.8, 8.0, z + 1.8, z + 2.0, STONE_D, 0.03, name="Brow")
        dk.cone(p, (x + sx * 1.0, 7.9, z + 0.8), 0.4, 0.4, STONE, verts=4, jitter=0.05, name="Ear")
    bx(p, x - 0.35, x + 0.35, 6.9, 7.3, z + 2.2, z + 2.3, BLACK, 0.02, name="Nose")
    # mane: a ruff behind the face with curls on the rim
    lathe(p, (x, 6.5, z - 0.5), [(2.0, 0), (1.9, 0.6), (1.2, 0.9)], 8, STONE, 0.12, axis='z', name="Mane")
    for k in range(6):
        a = 2 * pi * k / 6 + 0.3
        dk.cone(p, (x + 1.8 * math.cos(a), 6.5 + 1.8 * math.sin(a), z + 0.1), 0.5, 0.35, STONE_L, verts=4, jitter=0.08, name="Curl")
    # tail curling up behind
    pts = [(x, 2.6, z - 2.0), (x + 0.3, 4.2, z - 2.1), (x + 0.9, 5.6, z - 2.0), (x + 0.5, 6.6, z - 1.8)]
    for a, b, r in zip(pts, pts[1:], (0.55, 0.5, 0.42)):
        rod(p, a, b, r, STONE_L, 5, name="Tail")
    if ball_paw:
        blob(p, (x + 0.75, 2.3 + 0.55, z + 1.9), 0.55, STONE_L, sy=1.0, sides=6, name="Ball") if False else None
        dk.ball(p, (x + 0.75, 2.85, z + 1.7), 0.45, GOLD_D, subdiv=1, name="Ball")
    patch(p, x, z, 2.0, 2.0, 2.3, 2.38, MOSS, 7, 0.2, 0.05, name="Moss") if False else None


@part_builder("Komainu")
def build_Komainu():
    p = dk.Part("Komainu")
    komainu_model(p, 58, -28, True, False)
    komainu_model(p, 74, -28, False, True)
    return p


@part_builder("EmaWall")
def build_EmaWall():
    p = dk.Part("EmaWall")
    z = -36
    for x in (8, 14, 20):
        pillar(p, x, z, 0, 6.6, 0.5, WOOD_D, 6, name="Post")
    bx(p, 7.2, 20.8, 5.8, 6.6, z - 0.4, z + 0.4, WOOD_D, 0.04, name="TopBeam")
    bx(p, 8.0, 20.0, 1.4, 1.9, z - 0.3, z + 0.3, WOOD_D, 0.04, name="LowRail")
    bx(p, 8.4, 19.6, 1.9, 5.8, z - 0.2, z - 0.05, WOOD_D, 0.03, name="Back")
    hip_roof(p, 14, z, 6.6, 7.0, 2.0, 4.8, 0.7, 1.6, ROOF, 0.5, 0.4, trim=ROOF_L, name="Roof")
    marks = [VERM, INDIGO, GOLD, LEAF, PINK_D, VERM_D, INDIGO_L]
    spots = [(9.4, 4.1), (11.2, 4.4), (12.9, 4.0), (15.2, 4.2), (17.0, 4.5), (18.7, 4.0),
             (9.9, 2.1), (12.0, 2.4), (14.6, 2.0), (16.4, 2.3), (18.4, 2.1)]
    for k, (x, y) in enumerate(spots):
        w, h = 1.5, 1.7
        slab(p, [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y + h * 0.7), (x, y + h), (x - w / 2, y + h * 0.7)], 0.25, 'xy', z + 0.3, WOOD_L if k % 3 else PLASTER, 0.05, name="Ema")
        bx(p, x - 0.45, x + 0.45, y + 0.25, y + 0.95, z + 0.42, z + 0.5, marks[k % len(marks)], 0.03, name="EmaArt")
        bx(p, x - 0.3, x + 0.3, y + 1.0, y + 1.2, z + 0.42, z + 0.5, BLACK, 0.02, name="EmaMark")
        rod(p, (x, y + h, z + 0.3), (x, 5.8 if y > 3 else y + h + 0.5, z + 0.3), 0.05, STRAW_D, 3, name="Cord") if y > 3 else None
    for x in (11.0, 17.0):
        bx(p, x - 0.1, x + 0.1, 4.0, 5.8, z + 0.28, z + 0.33, STRAW_D, 0.02, name="Cord") if False else None
    return p


@part_builder("Statue")
def build_Statue():
    p = dk.Part("Statue")
    bx(p, -17, 1, 0, 2.4, -49, -33, STONE, 0.06, name="Base")
    bx(p, -13, -3, 0, 0.8, -33, -31, STONE_L, 0.05, name="Step")
    bx(p, -12, -4, 0, 1.6, -33, -32, STONE_L, 0.05, name="Step")
    bx(p, -17.2, 1.2, 1.9, 2.4, -49.2, -32.8, STONE_D, 0.05, name="BaseTop") if False else None
    bx(p, -14, -2, 2.4, 4.2, -46, -34, STONE_D, 0.06, name="Plinth")
    bx(p, -14.2, -1.8, 3.8, 4.2, -46.2, -33.8, STONE_L, 0.05, name="PlinthTop") if False else None
    # legs in wide trousers, sandals
    for x in (-11, -5):
        frustum(p, x, -42, 4.5, 11.0, 3.9, 3.9, 3.0, 3.0, INDIGO, 0.05, name="Leg")
        bx(p, x - 1.5, x + 1.5, 4.2, 5.0, -44.2, -39.6, WOOD_D, 0.04, name="Sandal")
    bx(p, -13.5, -2.5, 10.5, 14.2, -44, -39, INDIGO, 0.05, name="Hips")
    bx(p, -13.6, -2.4, 13.2, 14.2, -44.1, -38.9, VERM_D, 0.04, name="Belt")
    bx(p, -9.2, -6.8, 13.0, 14.4, -39.0, -38.8, GOLD, 0.03, name="Buckle")
    # armoured torso with lacing
    bx(p, -12.5, -3.5, 14.2, 20.8, -43.2, -39.8, VERM, 0.04, name="Torso")
    for y in (15.2, 16.6, 18.0, 19.4):
        bx(p, -12.5, -3.5, y, y + 0.5, -39.8, -39.6, INDIGO, 0.03, name="Lacing")
    bx(p, -9.4, -6.6, 16.8, 18.8, -39.8, -39.55, GOLD, 0.03, name="Plate")
    # shoulder plates (sode)
    for sg in (-1, 1):
        for k in range(3):
            y1, y0 = 21.4 - 1.5 * k, 21.4 - 1.5 * (k + 1)
            xin = -8 + sg * 4.6
            xout = -8 + sg * (7.9 + 0.1 * k)
            bx(p, min(xin, xout), max(xin, xout), y0, y1, -44.2, -38.8, DARK_RED if False else (VERM_D if k % 2 == 0 else INDIGO_L), 0.04, name="Sode")
        xm = -8 + sg * 6.3
        bx(p, xm - 0.1, xm + 0.1, 16.9, 21.4, -38.8, -38.65, GOLD, 0.02, name="SodeLace")
    # arms reaching to the sword hilt
    for sg in (-1, 1):
        s0 = (-8 + sg * 4.9, 19.6, -41.4)
        s1 = (-8 + sg * 3.6, 16.8, -38.8)
        s2 = (-8 + sg * 0.5, 20.0 + (0.8 if sg > 0 else 0), -37.0)
        rod(p, s0, s1, 1.05, INDIGO_L, 6, name="UpperArm")
        rod(p, s1, s2, 0.9, STEEL_D, 6, name="Forearm")
        dk.ball(p, s2, 0.8, STEEL, subdiv=1, name="Hand")
    # head: face, mask details, helmet
    dk.ball(p, (-8, 23.2, -41.5), 2.3, SKIN, scale=(1, 1.02, 1), subdiv=1, jitter=0.03, name="Head")
    for sx in (-1, 1):
        bx(p, -8 + sx * 0.95 - 0.5, -8 + sx * 0.95 + 0.5, 23.3, 23.7, -39.3, -39.1, BLACK, 0.02, name="Eye")
        bx(p, -8 + sx * 0.95 - 0.7, -8 + sx * 0.95 + 0.7, 23.9, 24.2, -39.35, -39.15, BLACK, 0.02, name="Brow")
    bx(p, -9.2, -6.8, 22.0, 22.5, -39.4, -39.15, BLACK, 0.02, name="Moustache")
    bx(p, -8.5, -7.5, 22.5, 23.1, -39.3, -39.1, SKIN, 0.02, name="Nose")
    sk = lathe(p, (-8, 21.0, -41.5), [(3.5, 0), (3.2, 0.7), (2.6, 2.7)], 8, VERM_D, 0.05, name="Shikoro")
    drop_faces(sk, lambda n: n[2] > 0.45)
    lathe(p, (-8, 24.1, -41.5), [(2.7, 0), (2.7, 0.5), (2.2, 1.4), (1.2, 2.1), (0, 2.4)], 8, STEEL_D, 0.05, name="Kabuto")
    dk.cyl(p, (-8, 24.4, -41.5), 2.8, 0.35, GOLD, verts=8, name="Brim")
    slab(p, [(-8, 26.0), (-10.4, 27.0), (-12.0, 28.9), (-12.9, 31.0), (-11.2, 29.9), (-9.8, 28.7), (-8, 28.1), (-6.2, 28.7), (-4.8, 29.9),
             (-3.1, 31.0), (-4.0, 28.9), (-5.6, 27.0)], 0.6, 'xy', -39.3, GOLD, 0.03, name="Crescent")
    dk.cyl(p, (-8, 26.0, -39.1), 0.55, 0.3, VERM, axis='z', verts=6, name="Gem")
    # the great sword, point on the plinth
    bx(p, -8.45, -7.55, 4.2, 18.2, -37.3, -36.7, STEEL, 0.03, name="Blade")
    bx(p, -8.15, -7.85, 4.2, 18.2, -37.32, -36.68, WHITE, 0.0, name="BladeEdge")
    dk.cyl(p, (-8, 18.4, -37), 1.5, 0.35, GOLD, verts=8, name="Tsuba")
    bx(p, -8.5, -7.5, 18.6, 21.0, -37.3, -36.7, BLACK, 0.02, name="Hilt")
    for k in range(3):
        bx(p, -8.5, -7.5, 19.0 + k * 0.7, 19.15 + k * 0.7, -37.32, -36.68, GOLD_D, 0.02, name="HiltWrap")
    dk.ball(p, (-8, 21.2, -37), 0.45, GOLD, subdiv=1, name="Pommel")
    # back banner (sashimono)
    rod(p, (-8, 14.0, -44.6), (-8, 30.0, -44.6), 0.28, WOOD_D, 5, name="BannerPole")
    slab(p, [(-7.7, 29.6), (-3.2, 29.6), (-3.8, 27.6), (-3.2, 25.6), (-7.7, 25.6)], 0.2, 'xy', -44.6, VERM, 0.03, name="Banner")
    dk.cyl(p, (-5.5, 27.6, -44.45), 1.1, 0.1, WHITE, axis='z', verts=8, name="BannerMon")
    dk.cyl(p, (-5.5, 27.6, -44.38), 0.5, 0.08, VERM, axis='z', verts=6, name="BannerMonIn")
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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_SamuraiShrine.json"))
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
        view(allm, "stage_SamuraiShrine_34.png", shiba=spot, az=205, el=42, size=(1800, 1000), zoom=2.15)
        view(allm, "stage_SamuraiShrine_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_SamuraiShrine_34.png", "stage_SamuraiShrine_top.png", "stage_SamuraiShrine.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_SamuraiShrine.json"))
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
        view(allm, "stage_SamuraiShrine_34.png", shiba=spot, az=205, el=42, size=(1800, 1000), zoom=2.15)
        view(allm, "stage_SamuraiShrine_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_SamuraiShrine_34.png", "stage_SamuraiShrine_top.png", "stage_SamuraiShrine.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
