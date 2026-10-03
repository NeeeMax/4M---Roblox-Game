"""Wizard Tower decor models (theme WizardTower): builds the 25 decor parts around the seventeenth Shiba (Wizard Shiba).

Run:  blender --background --factory-startup --python build_WizardTower.py -- <outdir>   (use an absolute outdir)
Writes into <outdir>: Decor_WizardTower_<PartId>.fbx, preview_<PartId>.png per part, stage_WizardTower.png (3/4 view + top view
stacked), stage_WizardTower_34.png and stage_WizardTower_top.png. Every model is built in the stage frame (see decorkit.py) and,
before export, fitted to the union box of its blueprint pieces so that the game's fitToPieces scale stays about 1.
Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures, no neon. One palette: lilac stone, wizard
purple, brass/gold, crystal cyan/pink/green, warm wood. Previews are rendered the way the player sees the stage: from the road (+z).
Env: WT_ONLY=Part1,Part2 builds only those parts.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "WizardTower"
R = random.Random(17)
pi = math.pi
ONLY = set(os.environ.get("WT_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
ST = (176, 170, 186); ST_D = (120, 114, 138); ST_L = (214, 210, 226); ST_X = (238, 234, 246)
PUR = (96, 66, 160); PUR_D = (66, 46, 120); PUR_L = (150, 90, 214)
GOLD = (240, 192, 64); GOLD_D = (196, 150, 64); BRASS = (196, 150, 64); BRASS_D = (150, 108, 44)
WOOD = (126, 86, 58); WOOD_D = (84, 58, 42); WOOD_L = (168, 124, 84)
CY = (96, 206, 232); CY_D = (60, 150, 190); PINK = (226, 112, 190); GRN = (116, 214, 92); GRN_D = (78, 150, 70)
RED = (190, 56, 70); CREAM = (240, 228, 204); IRON = (58, 58, 70); IRON_L = (90, 90, 106)
WIN = (250, 226, 130); PLASTER = (238, 226, 206); ORANGE = (232, 132, 44); STRAW = (222, 190, 100)
GRASS = (98, 160, 100); GRASS_D = (78, 138, 92); GRASS_L = (128, 184, 112); WATER = (82, 170, 222); WATER_L = (150, 215, 240)
COPPER = (86, 164, 176); COPPER_D = (60, 126, 140); FUR = (150, 116, 86)
TIM = WOOD; FIRE = (240, 132, 42); FIRE_Y = (252, 204, 70); FIRE_R = (206, 70, 36)
SOIL = (92, 70, 46)

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






# ---- wizard helpers ----------------------------------------------------------------------------------------------
K8 = math.cos(pi / 8)          # apothem / radius of an 8-gon whose flats face the axes (lathe rot0 = pi/8)


def prof_at(prof, h):
    """(radius, dx, dz) of a lathe profile at relative height h."""
    g = lambda e, i: e[i] if len(e) > i else 0.0
    for a, b in zip(prof, prof[1:]):
        if a[1] <= h <= b[1]:
            t = (h - a[1]) / max(b[1] - a[1], 1e-6)
            return tuple(g(a, k) + (g(b, k) - g(a, k)) * t for k in (0, 2, 3))
    return (prof[-1][0], 0.0, 0.0)


def torus(p, c, Rr, r, color, major=16, minor=4, rx=0.0, rz=0.0, jitter=0.0, name="Ring"):
    """Ring lying in the xz plane around c, tilted by rx (about x) then rz (about z), degrees."""
    M = Matrix.Rotation(math.radians(rz), 3, 'Z') @ Matrix.Rotation(math.radians(rx), 3, 'X')
    pts = []
    for i in range(major):
        a = 2 * pi * i / major
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minor):
            b = 2 * pi * j / minor + pi / minor
            rr = Rr + r * math.cos(b)
            v = M @ Vector((rr * ca, r * math.sin(b), rr * sa))
            pts.append((c[0] + v.x, c[1] + v.y, c[2] + v.z))
    faces = []
    for i in range(major):
        i2 = (i + 1) % major
        for j in range(minor):
            j2 = (j + 1) % minor
            faces.append((i * minor + j, i2 * minor + j, i2 * minor + j2, i * minor + j2))
    return _obj(p, name, pts, faces, color, jitter)


def star_pts(cx, cy, Ro, Ri, n=5, rot=pi / 2):
    pts = []
    for i in range(2 * n):
        a = rot + pi * i / n
        r = Ro if i % 2 == 0 else Ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def star(p, x, y, z, R_, color, thick=0.5, name="Star"):
    """Flat 5-point star facing +z."""
    return slab(p, star_pts(x, y, R_, R_ * 0.45), thick, 'xy', z, color, 0.0, name=name)


def spark(p, x, y, z, R_, color, name="Spark"):
    """Little 3D sparkle: two crossed 4-point stars."""
    pts = star_pts(0, 0, R_, R_ * 0.28, n=4)
    slab(p, [(x + u, y + v) for u, v in pts], R_ * 0.3, 'xy', z, color, 0.0, name=name)
    return slab(p, [(y + v, z + u) for u, v in pts], R_ * 0.3, 'yz', x, color, 0.0, name=name)


def arch_pts(cx, y0, w, h, n=3, pointed=False):
    r = w / 2
    pts = [(cx - r, y0), (cx + r, y0)]
    if pointed:
        yc = y0 + h - 1.732 * r
        for k in range(0, n + 1):
            th = math.radians(60 * k / n)
            pts.append((cx - r + 2 * r * math.cos(th), yc + 2 * r * math.sin(th)))
        for k in range(n - 1, -1, -1):
            th = math.radians(60 * k / n)
            pts.append((cx + r - 2 * r * math.cos(th), yc + 2 * r * math.sin(th)))
    else:
        yc = y0 + h - r
        for k in range(0, 2 * n + 1):
            a = pi * k / (2 * n)
            pts.append((cx + r * math.cos(a), yc + r * math.sin(a)))
    return pts


def door(p, x, y0, z, w, h, col=WOOD, frame=ST_D, t=0.5):
    """Arched wooden door facing +z, z = the wall face."""
    slab(p, arch_pts(x, y0, w + 1.0, h + 0.5), t, 'xy', z, frame, 0.03, name="DoorFrame")
    slab(p, arch_pts(x, y0, w, h), t, 'xy', z + 0.12, col, 0.05, name="Door")
    zf = z + 0.12 + t / 2 + 0.03
    for dx in (-w * 0.25, w * 0.25):
        bx(p, x + dx - 0.07, x + dx + 0.07, y0, y0 + h * 0.8, zf - 0.02, zf + 0.06, WOOD_D, name="Plank")
    bx(p, x - w / 2, x + w / 2, y0 + h * 0.3, y0 + h * 0.3 + 0.35, zf - 0.02, zf + 0.1, IRON, name="Strap")
    bx(p, x - w / 2, x + w / 2, y0 + h * 0.62, y0 + h * 0.62 + 0.35, zf - 0.02, zf + 0.1, IRON, name="Strap")
    dk.box(p, (x + w * 0.3, y0 + h * 0.42, zf + 0.15), (0.35, 0.35, 0.3), GOLD, name="Knob")


def gwin(p, x, y0, z, w, h, glow=WIN, frame=ST_D, t=0.5, pointed=True, bar=True):
    """Arched window facing +z (frame, glowing pane, cross bars)."""
    slab(p, arch_pts(x, y0 - 0.3, w + 0.9, h + 0.6, pointed=pointed), t, 'xy', z, frame, 0.03, name="WinFrame")
    slab(p, arch_pts(x, y0, w, h, pointed=pointed), t, 'xy', z + 0.12, glow, 0.0, name="WinGlass")
    zf = z + 0.12 + t / 2 + 0.03
    if bar:
        bx(p, x - 0.08, x + 0.08, y0, y0 + h * 0.95, zf - 0.02, zf + 0.05, frame, name="Bar")
        bx(p, x - w / 2, x + w / 2, y0 + h * 0.4, y0 + h * 0.4 + 0.16, zf - 0.02, zf + 0.05, frame, name="Bar")


def courses(o, ca, cb, hgt=1.6, jitter=0.05):
    """Stone courses: alternate two colours by height on the vertical faces."""
    recolor(o, lambda c, n, i: (ca if int(c[1] / hgt) % 2 == 0 else cb) if abs(n[1]) < 0.6 else None, jitter)


def hat_prof(rb, rc, h, bend=(0.0, 0.0)):
    bx_, bz_ = bend
    return [(rb, 0), (rb * 0.96, 0.28), (rc, 0.45), (rc * 0.8, h * 0.35, bx_ * 0.15, bz_ * 0.15),
            (rc * 0.55, h * 0.62, bx_ * 0.45, bz_ * 0.45), (rc * 0.28, h * 0.86, bx_ * 0.8, bz_ * 0.8), (0, h, bx_, bz_)]


def hat(p, x, y0, z, rb, rc, h, col, band=None, bend=(0.0, 0.0), sides=8, name="Hat"):
    o = lathe(p, (x, y0, z), hat_prof(rb, rc, h, bend), sides, col, 0.05, rot0=pi / sides, name=name)
    if band:
        recolor(o, lambda c, n, i: band if 0.3 < c[1] - y0 < 0.42 else None, 0.03)
    return o


def dome(p, x, y0, z, r, h, col, sides=10, rings=4, jitter=0.05, name="Dome", rot0=0.0):
    prof = [(r, 0)]
    for k in range(1, rings + 1):
        a = pi / 2 * k / rings
        prof.append((r * math.cos(a), h * math.sin(a)))
    return lathe(p, (x, y0, z), prof, sides, col, jitter, rot0=rot0, name=name)


def crystal(p, x, y0, z, r, h, col, lean=(0.0, 0.0), sides=6, tip=0.3, name="Crystal"):
    lx, lz = lean
    prof = [(r * 0.8, 0), (r, h * 0.12, lx * 0.12, lz * 0.12), (r, h * (1 - tip), lx * (1 - tip), lz * (1 - tip)), (0, h, lx, lz)]
    o = lathe(p, (x, y0, z), prof, sides, col, 0.06, name=name)
    recolor(o, lambda c, n, i: dk.shade(col, 1.28) if n[1] > 0.35 else None, 0.05)
    return o


def boulder(p, x, y0, z, r, h, col, sides=6, jitter=0.1, name="Boulder", seed=None):
    rn = random.Random(seed if seed is not None else int(abs(x * 13 + z * 7 + r * 31)))
    rings = []
    for f, t in ((0.78, 0.0), (1.0, 0.35), (0.86, 0.75), (0.45, 1.0)):
        ring = []
        for i in range(sides):
            a = 2 * pi * i / sides + rn.uniform(-0.18, 0.18)
            rr = r * f * rn.uniform(0.86, 1.1)
            ring.append((x + rr * math.cos(a), y0 + h * t, z + rr * math.sin(a)))
        rings.append(ring)
    return loft(p, rings, col, jitter, name=name)


def ball2(p, c, r, color, sy=1.0, sides=8, jitter=0.0, name="Ball"):
    """Round ball from a lathe (rings every 40 degrees)."""
    prof = [(0, -r * sy)]
    for a in (-60, -20, 20, 60):
        prof.append((r * math.cos(math.radians(a)), r * sy * math.sin(math.radians(a))))
    prof.append((0, r * sy))
    return lathe(p, (c[0], c[1], c[2]), prof, sides, color, jitter, name=name)


def pole(p, x, z, y0, y1, w, color, jitter=0.04, name="Pole"):
    return bx(p, x - w / 2, x + w / 2, y0, y1, z - w / 2, z + w / 2, color, jitter, name=name)


def grid_top(p, x0, x1, z0, z1, y, nx, nz, color, jitter=0.0, name="Grid"):
    """Flat grid of quads facing up."""
    pts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            pts.append((x0 + (x1 - x0) * i / nx, y, z0 + (z1 - z0) * j / nz))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return _obj(p, name, pts, faces, color, jitter, closed=False, up=True)


# ---- the parts ---------------------------------------------------------------------------------------------------
BUILDERS = []


def part_builder(pid):
    def deco(fn):
        BUILDERS.append((pid, fn))
        return fn
    return deco


FOOT = {}          # part id -> (lo, hi) footprint of the blueprint pieces (used to scatter details in Ground)


@part_builder("Ground")
def build_Ground():
    p = dk.Part("Ground")
    bx(p, -95, 95, 0, 0.28, -65, 65, GRASS_D, name="Base")
    g = grid_top(p, -95, 95, -65, 65, 0.3, 19, 13, GRASS, name="Meadow")

    def tone(c, n, i):
        v = noise(c[0] * 1.3, c[2] * 1.3) + 0.35 * math.sin(c[0] * 0.37) * math.cos(c[2] * 0.29)
        return GRASS_D if v < -0.18 else (GRASS_L if v > 0.2 else GRASS)
    recolor(g, tone, 0.035)
    # darker lawns
    for cx, cz, w, d in ((-20, 14, 30, 14), (70, 4, 34, 18)):
        pts = [(cx + w / 2 * math.cos(a) * 0.98, cz + d / 2 * math.sin(a) * 0.98) for a in [2 * pi * k / 14 for k in range(14)]]
        dk_flat = flat(p, pts, 0.31, GRASS_D, 0.04, name="Lawn")
    # flagstone plaza for the Wizard Shiba
    bx(p, -79, -41, 0.28, 0.42, -23, 11, ST_D, 0.05, name="PlazaBase")
    nx, nz = 6, 5
    for i in range(nx):
        for j in range(nz):
            x0 = -79 + 38 / nx * i + 0.3
            x1 = -79 + 38 / nx * (i + 1) - 0.3
            z0 = -23 + 34 / nz * j + 0.3
            z1 = -23 + 34 / nz * (j + 1) - 0.3
            col = (ST_L, ST, ST_X, ST)[(i * 3 + j * 5 + (i * j)) % 4]
            flat(p, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 0.45, col, 0.05, name="Flag")
    # stepping-stone paths: to the road, and past the griffin to the tower door
    stones = []
    for k in range(12):
        stones.append((-60 + (1.2 if k % 2 else -1.2), 14 + k * 4.4))
    for k in range(20):
        stones.append((-37 + k * 4.2, -6 + (0.9 if k % 2 else -0.9)))
    for k in range(7):
        stones.append((46 + (0.9 if k % 2 else -0.9), -9 - k * 4.2))
    for (sx, sz) in stones:
        w, d = 3.4, 2.6
        flat(p, [(sx - w / 2, sz - d / 2 + 0.2), (sx + w / 2, sz - d / 2), (sx + w / 2 - 0.3, sz + d / 2), (sx - w / 2, sz + d / 2 - 0.2)],
             0.33, ST_L if R.random() > 0.4 else ST, 0.05, name="Step")
    # flowers and little crystals scattered in the meadow
    cols = (PINK, CY, CREAM, GOLD, PUR_L)
    n = 0
    tries = 0
    while n < 46 and tries < 2000:
        tries += 1
        x, z = R.uniform(-92, 92), R.uniform(-62, 62)
        bad = False
        for lo, hi in FOOT.values():
            if lo[0] - 3 < x < hi[0] + 3 and lo[2] - 3 < z < hi[2] + 3:
                bad = True
        if bad or (-81 < x < -39 and -25 < z < 13) or any(abs(x - sx) < 4 and abs(z - sz) < 3.5 for sx, sz in stones):
            continue
        dk.cyl(p, (x, 0.375, z), 0.5, 0.15, cols[n % 5], verts=4, top_radius=0.25, jitter=0.04, name="Flower")
        n += 1
    return p


@part_builder("Circle")
def build_Circle():
    p = dk.Part("Circle")
    cx, cz = -60.0, -6.0
    lathe(p, (cx, 0, cz), [(17, 0), (17, 0.4)], 16, ST_D, 0.07, rot0=pi / 16, name="Disc")
    lathe(p, (cx, 0.4, cz), [(12.8, 0), (12.8, 0.2)], 16, ST_L, 0.05, rot0=pi / 16, name="Inner")
    torus(p, (cx, 0.62, cz), 9.8, 0.24, PUR_L, major=24, minor=4, name="RuneRing")
    torus(p, (cx, 0.62, cz), 3.6, 0.2, CY, major=16, minor=4, name="RuneRing2")
    hv = [(cx + 9.8 * math.cos(pi / 2 + k * pi / 3), cz + 9.8 * math.sin(pi / 2 + k * pi / 3)) for k in range(6)]
    for k in range(6):
        a, b = hv[k], hv[(k + 2) % 6]
        rod(p, (a[0], 0.64, a[1]), (b[0], 0.64, b[1]), 0.2, PUR_L, sides=4, name="Star")
    for k in range(12):
        a = 2 * pi * k / 12 + pi / 12
        dk.box(p, (cx + 7.1 * math.cos(a), 0.55, cz + 7.1 * math.sin(a)), (0.9, 0.2, 0.9), CY if k % 2 else PINK, rot=(0, 45, 0), name="Rune")
    # six standing stones with glowing bands and floating crystals
    heights = [7.0, 8.5, 7.5, 8.0, 9.2, 7.0]
    cc = [CY, PINK, PUR_L, CY, PINK, PUR_L]
    for k in range(6):
        a = math.radians(80 + 60 * k)
        x, z = cx + 13.6 * math.cos(a), cz + 13.6 * math.sin(a)
        h = heights[k]
        yaw = -math.degrees(a) + 90
        dk.cyl(p, (x, 0.4 + h / 2, z), 1.6, h, ST_L, verts=5, top_radius=1.0, rot=(0, yaw, 0), jitter=0.08, name="Stone")
        dk.cone(p, (x, 0.4 + h, z), 1.0, 1.1, ST_X, verts=5, jitter=0.04, name="StoneTip")
        dk.cyl(p, (x, 0.4 + h * 0.55, z), 1.5, 0.5, PUR_L, verts=5, rot=(0, yaw, 0), name="Band")
        crystal(p, x, 0.4 + h + 1.5, z, 0.75, 2.3, cc[k], sides=5, tip=0.35)
    # central altar with a floating crystal
    lathe(p, (cx, 0.6, cz), [(2.6, 0), (2.2, 0.9), (1.4, 1.2), (1.0, 1.6)], 8, ST, 0.06, rot0=pi / 8, name="Altar")
    crystal(p, cx, 3.4, cz, 1.25, 4.4, CY, sides=6, tip=0.34)
    torus(p, (cx, 4.6, cz), 2.2, 0.16, GOLD, major=14, minor=4, rx=18, rz=-12, name="Halo")
    return p


@part_builder("Tower")
def build_Tower():
    p = dk.Part("Tower")
    cx, cz = 46.0, -46.0
    base = [(11.0, 0), (10.8, 2), (10.3, 6), (9.6, 9.5), (8.9, 10.0)]
    lathe(p, (cx, 0, cz), base, 8, ST_D, 0.12, rot0=pi / 8, name="Rock")
    t1 = [(8.4, 0), (8.1, 3), (7.8, 8), (7.5, 14, 0.3, 0)]
    o = lathe(p, (cx, 10, cz), t1, 8, ST, 0.05, rot0=pi / 8, name="Tier1")
    courses(o, ST, ST_L, 1.7)
    bx0 = cx + 0.3
    t2 = [(7.9, 0), (7.2, 0.5), (6.9, 1.2), (6.7, 6, 0.6, 0), (6.5, 12, 1.2, 0)]
    o = lathe(p, (bx0, 24, cz), t2, 8, ST_L, 0.05, rot0=pi / 8, name="Tier2")
    courses(o, ST_L, ST_X, 1.7)
    px = bx0 + 1.2
    lathe(p, (px, 35.8, cz), [(6.6, 0), (9.0, 0.6), (9.0, 1.2), (8.0, 1.25)], 8, ST_D, 0.05, rot0=pi / 8, name="Balcony")
    for k in range(8):
        a = pi / 8 + k * pi / 4
        pole(p, px + 7.6 * math.cos(a), cz + 7.6 * math.sin(a), 37.0, 38.6, 0.5, GOLD_D, name="RailPost")
    torus(p, (px, 38.5, cz), 7.6, 0.22, GOLD_D, major=16, minor=4, name="Rail")
    # the crooked purple hat
    hp = hat_prof(7.5, 6.3, 19.0, (-4.0, 1.0))
    hat(p, px, 37.0, cz, 7.5, 6.3, 19.0, PUR, band=PUR_D, bend=(-4.0, 1.0))
    for h, dx_, rr in ((6.5, -1.7, 1.2), (10.5, 1.4, 1.0), (13.8, -0.9, 0.8)):
        r_, ddx, ddz = prof_at(hp, h)
        star(p, px + ddx + dx_ * 0.4, 37.0 + h, cz + ddz + K8 * r_ + 0.05, rr, GOLD, 0.5)
    r_, ddx, ddz = prof_at(hp, 0.9)
    bx(p, px + ddx - 1.1, px + ddx + 1.1, 37.4, 38.6, cz + K8 * r_ - 0.1, cz + K8 * r_ + 0.35, GOLD, name="Buckle")
    ball2(p, (px - 4.0, 55.3, cz + 1.0), 0.75, GOLD, name="Tip")
    # door, steps, windows, lantern
    z0 = cz + K8 * prof_at(base, 2.5)[0]
    door(p, cx, 0.4, z0, 4.2, 6.6)
    bx(p, cx - 3.4, cx + 3.4, 0, 0.5, z0, z0 + 1.7, ST_L, 0.05, name="Step")
    bx(p, cx - 2.6, cx + 2.6, 0, 0.9, z0, z0 + 0.9, ST, 0.05, name="Step")
    for sgn in (-1, 1):
        dk.box(p, (cx + sgn * 3.6, 6.3, z0 + 0.3), (0.5, 0.9, 0.5), IRON, name="LampArm")
        dk.box(p, (cx + sgn * 3.6, 5.5, z0 + 0.35), (0.9, 1.1, 0.9), WIN, name="Lamp")
    r_, ddx, ddz = prof_at(t1, 7.5)
    gwin(p, cx + 0.15, 15.2, cz + K8 * r_ - 0.1, 2.4, 4.6)
    for sgn in (-1, 1):
        bx(p, cx + 0.15 + sgn * 1.9 - 0.4, cx + 0.15 + sgn * 1.9 + 0.4, 15.2, 19.4, cz + K8 * r_ - 0.1, cz + K8 * r_ + 0.4, PUR, name="Shutter")
    r_, ddx, ddz = prof_at(t2, 6.0)
    gwin(p, bx0 + ddx, 28.4, cz + K8 * r_ - 0.1, 2.8, 4.8)
    for sgn in (-1, 1):
        bx(p, bx0 + ddx + sgn * 2.1 - 0.4, bx0 + ddx + sgn * 2.1 + 0.4, 28.4, 32.8, cz + K8 * r_ - 0.1, cz + K8 * r_ + 0.4, PUR, name="Shutter")
    r_, ddx, ddz = prof_at(t1, 2.5)
    for sx in (-4.2, 4.2):
        slab(p, [(cx + sx - 0.35, 11.0), (cx + sx + 0.35, 11.0), (cx + sx + 0.35, 13.2), (cx + sx, 13.8), (cx + sx - 0.35, 13.2)], 0.4, 'xy',
             cz + K8 * prof_at(t1, 2.0)[0] - 0.15, WIN, 0.0, name="Slit")
    return p


@part_builder("Cauldron")
def build_Cauldron():
    p = dk.Part("Cauldron")
    cx, cz = -24.0, -26.0
    # crossed logs and flames under the pot
    dk.box(p, (cx, 0.9, cz), (11, 1.2, 1.6), WOOD_D, rot=(0, 35, 0), jitter=0.05, name="Log")
    dk.box(p, (cx, 0.9, cz), (11, 1.2, 1.6), WOOD, rot=(0, -35, 0), jitter=0.05, name="Log")
    dk.box(p, (cx, 1.7, cz), (9, 1.2, 1.5), WOOD_D, rot=(0, 90, 0), jitter=0.05, name="Log")
    fire(p, cx, 1.0, cz, 2.3, 3.4)
    for sx, sz in ((-2.8, 1.8), (3.0, -1.4), (0.5, 3.4)):
        dk.cone(p, (cx + sx, 0.9, cz + sz), 0.7, 1.6, FIRE_R, verts=4, jitter=0.05, name="Flame")
    for a in (90, 210, 330):
        ar = math.radians(a)
        rod(p, (cx + 4.9 * math.cos(ar), 0.0, cz + 4.9 * math.sin(ar)), (cx + 3.4 * math.cos(ar), 3.6, cz + 3.4 * math.sin(ar)), 0.6, IRON, sides=5, name="Leg")
    prof = [(2.6, 0), (4.4, 1.2), (5.6, 3.0), (6.0, 5.0), (5.8, 6.5), (5.2, 7.1)]
    o = lathe(p, (cx, 2.6, cz), prof, 10, IRON, 0.06, name="Pot")
    recolor(o, lambda c, n, i: IRON_L if (c[1] - 2.6) > 2.0 and n[1] > -0.2 and abs(n[1]) < 0.5 and i % 2 == 0 else None, 0.04)
    torus(p, (cx, 9.7, cz), 5.7, 0.48, IRON_L, major=10, minor=4, name="Rim")
    lathe(p, (cx, 9.35, cz), [(5.4, 0), (5.4, 0.35)], 10, GRN, 0.05, name="Brew")
    for a in (0, 180):
        ar = math.radians(a)
        dk.box(p, (cx + 6.4 * math.cos(ar), 7.6, cz), (1.2, 1.6, 1.2), IRON_L, name="Ear")
    for (bxx, bzz, r, h) in ((-1.6, 0.8, 1.2, 10.2), (1.8, -1.2, 1.0, 10.5), (0.4, 2.0, 0.8, 10.3), (-2.4, -1.8, 0.7, 10.2)):
        ball2(p, (cx + bxx, h, cz + bzz), r, GRN, sy=0.75, sides=6, jitter=0.05, name="Bubble")
    # green steam puffs
    for (bxx, bzz, r, h) in ((0.2, 0.2, 1.0, 11.7), (-1.0, -0.6, 0.7, 12.0), (1.3, 0.8, 0.6, 11.6)):
        ball2(p, (cx + bxx, h, cz + bzz), r, (176, 236, 150), sy=0.8, sides=6, jitter=0.04, name="Steam")
    # ladle
    rod(p, (cx + 3.6, 10.0, cz + 4.4), (cx + 1.2, 12.0, cz + 0.8), 0.28, WOOD_L, sides=4, name="Ladle")
    return p


@part_builder("Shop")
def build_Shop():
    p = dk.Part("Shop")
    bx(p, -70, -50, 0, 1, 37, 51, ST_D, 0.08, name="Plinth")
    bx(p, -68, -52, 1, 12, 38.5, 49.5, PLASTER, 0.04, name="Walls")
    gable(p, 'x', -70.5, -49.5, 44, 7.3, 11.6, 18.7, 0.8, PUR, PUR_D, n=5)
    gable_end(p, 'x', -68.0, 44, 5.5, 12, 17.6, 0.8, PLASTER)
    gable_end(p, 'x', -52.0, 44, 5.5, 12, 17.6, 0.8, PLASTER)
    # half timbering on the front
    zf = 49.5
    for x in (-68, -64.4, -58.8, -52.2):
        bx(p, x - 0.3, x + 0.3, 1, 12, zf, zf + 0.3, WOOD_D, name="Timber")
    for y in (5.9, 11.6):
        bx(p, -68, -52, y - 0.3, y + 0.3, zf, zf + 0.3, WOOD_D, name="Timber")
    rod(p, (-68, 1.2, zf + 0.15), (-64.4, 5.6, zf + 0.15), 0.22, WOOD_D, sides=4, name="Brace")
    rod(p, (-52.2, 1.2, zf + 0.15), (-58.8, 5.6, zf + 0.15), 0.22, WOOD_D, sides=4, name="Brace")
    # door, window, sign
    door(p, -62, 1.0, zf, 3.4, 6.8)
    bx(p, -64, -60, 1, 1.5, zf, zf + 1.4, ST_L, 0.05, name="Step")
    gwin(p, -55.8, 5.4, zf, 2.8, 3.6, pointed=False)
    bx(p, -57.6, -54.0, 4.9, 5.3, zf, zf + 0.9, WOOD, name="Sill")
    for i, c in enumerate((CY, PINK, GRN, PUR_L)):
        blob(p, (-57.0 + i * 0.95, 5.3, zf + 0.5), 0.36, c, sy=1.3, sides=5, name="SillBottle")
    bx(p, -64.6, -59.4, 9.0, 11.1, zf, zf + 0.3, WOOD, 0.04, name="SignBoard")
    slab(p, [(-62.4, 9.3), (-61.6, 9.3), (-61.4, 9.9), (-61.6, 10.4), (-61.7, 10.8), (-62.3, 10.8), (-62.4, 10.4), (-62.6, 9.9)], 0.3, 'xy', zf + 0.4, CY, 0.0, name="SignBottle")
    bx(p, -62.2, -61.8, 10.8, 11.05, zf + 0.25, zf + 0.6, GOLD, name="SignCork")
    # chimney with a puff of smoke
    bx(p, -55.8, -53.2, 13.0, 19.2, 40.2, 42.8, ST, 0.06, name="Chimney")
    bx(p, -56.1, -52.9, 19.2, 19.6, 39.9, 43.1, ST_D, name="ChimneyCap")
    # barrel and crates at the door
    barrel(p, -52.6, 1.0, 50.2, 1.0, 2.4, color=WOOD_L, hoop=IRON)
    bx(p, -68.6, -66.2, 1.0, 2.7, 48.8, 50.9, WOOD_L, 0.05, name="Crate")
    bx(p, -68.7, -66.1, 1.7, 2.0, 48.8, 51.0, WOOD_D, name="CrateBand")
    blob(p, (-67.4, 2.7, 49.9), 0.55, PINK, sy=1.3, sides=5, name="Bottle")
    return p


@part_builder("Well")
def build_Well():
    p = dk.Part("Well")
    cx, cz = -46.0, 22.0
    o = lathe(p, (cx, 0, cz), [(4.3, 0), (4.3, 2.4), (3.7, 2.8)], 8, ST, 0.06, rot0=pi / 8, name="Ring")
    courses(o, ST, ST_L, 0.9, 0.06)
    lathe(p, (cx, 0, cz), [(3.7, 2.55), (3.7, 2.7)], 8, WATER, 0.03, rot0=pi / 8, name="Water")
    for (mx, mz, r) in ((3.4, 2.4, 0.9), (-3.6, 1.2, 0.7), (1.0, -3.7, 0.8)):
        blob(p, (cx + mx, 1.9, cz + mz), r, GRASS_D, sy=0.7, sides=5, jitter=0.05, name="Moss")
    pole(p, cx - 3.4, cz, 2.6, 8.5, 0.9, WOOD_D)
    pole(p, cx + 3.4, cz, 2.6, 8.5, 0.9, WOOD_D)
    bx(p, cx - 3.5, cx + 3.5, 6.0, 6.5, cz - 0.2, cz + 0.2, WOOD, name="Beam")
    # purple gable roof, ridge along z
    gable(p, 'z', 17.7, 26.3, cx, 4.6, 8.0, 10.6, 0.7, PUR, PUR_D, n=4)
    gable_end(p, 'z', 17.9, cx, 4.0, 8.0, 10.0, 0.5, PUR_D)
    gable_end(p, 'z', 26.1, cx, 4.0, 8.0, 10.0, 0.5, PUR_D)
    star(p, cx, 8.9, 26.45, 0.9, GOLD, 0.3)
    # rope and bucket
    rod(p, (cx, 6.0, cz), (cx, 4.6, cz), 0.1, WOOD_L, sides=4, name="Rope")
    dk.cyl(p, (cx, 3.9, cz), 0.9, 1.3, WOOD_L, verts=6, top_radius=1.1, name="Bucket")
    torus(p, (cx, 4.55, cz), 1.05, 0.08, IRON, major=6, minor=4, name="BucketRim")
    # crank
    rod(p, (cx + 3.9, 6.25, cz), (cx + 4.9, 6.25, cz), 0.18, IRON, sides=4, name="Crank")
    rod(p, (cx + 4.9, 6.25, cz), (cx + 4.9, 5.2, cz + 0.3), 0.14, IRON, sides=4, name="Handle")
    # a coin and sparkle
    dk.cyl(p, (cx + 2.4, 3.1, cz + 4.0), 0.6, 0.12, GOLD, axis='z', verts=8, name="Coin")
    spark(p, cx + 0.6, 9.8, cz, 0.8, WATER_L)
    return p


@part_builder("Mushrooms")
def build_Mushrooms():
    p = dk.Part("Mushrooms")

    def shroom(x, z, r, h_stem, h_cap, cap, stem=CREAM, spots=CREAM, n_spots=5, yaw=0.0):
        s = lathe(p, (x, 0, z), [(r * 0.5, 0), (r * 0.36, h_stem * 0.4), (r * 0.34, h_stem), ], 6, stem, 0.05, name="Stem")
        prof = [(r, 0), (r * 0.98, h_cap * 0.22), (r * 0.84, h_cap * 0.55), (r * 0.52, h_cap * 0.82), (r * 0.2, h_cap * 0.96), (0, h_cap)]
        c = lathe(p, (x, h_stem - 0.1, z), prof, 8, cap, 0.05, rot0=pi / 8, name="Cap")
        recolor(c, lambda cc, n, i: dk.shade(stem, 0.9) if n[1] < -0.5 else None, 0.04)
        for k in range(n_spots):
            a = yaw + 2 * pi * k / n_spots + 0.4
            ph = 0.3 + 0.5 * ((k * 37) % 7) / 7
            rr = r * (0.84 - 0.55 * ph) * 0.97 if ph < 0.8 else 0
            hh = h_stem - 0.1 + h_cap * (0.5 + 0.45 * ph)
            rr = r * 0.6 * (1 - ph) + 0.1
            blob(p, (x + rr * math.cos(a), hh, z + rr * math.sin(a)), r * 0.17 + 0.2, spots, sy=0.55, sides=5, name="Spot")
        return c

    # the big red house mushroom with a little round door
    shroom(-85, 24, 6.0, 5.2, 7.0, RED, n_spots=7)
    slab(p, [(-85 + 1.0 * math.cos(a), 0.2 + 1.5 + 1.5 * math.sin(a)) for a in [2 * pi * k / 10 for k in range(10)]], 0.5, 'xy', 24 + 1.9, WOOD, 0.04, name="Door")
    torus(p, (-85, 1.7, 24 + 1.95), 1.15, 0.12, WOOD_D, major=10, minor=4, rx=90, name="DoorFrame")
    dk.box(p, (-84.5, 1.7, 24 + 2.25), (0.3, 0.3, 0.3), GOLD, name="Knob")
    gwin(p, -87.0, 3.2, 24 + 1.6, 0.9, 1.3, pointed=False, bar=False)
    shroom(-77, 26.5, 3.9, 3.0, 4.6, PUR_L, n_spots=5)
    shroom(-81.5, 29, 2.6, 1.8, 3.1, PINK, n_spots=4)
    shroom(-89, 19.4, 2.2, 1.6, 2.7, CY, n_spots=4)
    boulder(p, -75.4, 0, 20, 1.9, 1.7, ST_D, name="Rock")
    for (gx, gz) in ((-79.5, 22), (-91, 24.5), (-83, 18.5), (-88.5, 29), (-74, 24)):
        for k in range(3):
            dk.cone(p, (gx + 0.5 * k, 0, gz + 0.3 * (k % 2)), 0.35, 1.2 + 0.4 * k, GRASS_D, verts=4, name="Tuft")
    return p


@part_builder("Brooms")
def build_Brooms():
    p = dk.Part("Brooms")
    bx(p, -31, -21, 0, 0.8, 19.5, 24.5, WOOD_D, 0.06, name="Base")
    for x in (-30.4, -21.6):
        pole(p, x, 22, 0.8, 8.0, 0.8, WOOD)
        dk.cone(p, (x, 8.0, 22), 0.55, 0.9, GOLD_D, verts=4, name="Finial")
    bx(p, -31, -21, 7.2, 7.8, 21.6, 22.4, WOOD, name="TopBar")
    bx(p, -31, -21, 2.8, 3.3, 21.6, 22.4, WOOD, name="LowBar")

    def broom(x, tilt, top):
        a = (x, 0.9, 23.2)
        b = (x + tilt * 3.2, 4.2, 23.2)
        c = (x + tilt * (top - 0.9), top, 23.2)
        rod(p, a, b, 1.15, STRAW, sides=6, r2=0.38, jitter=0.07, name="Bristles")
        rod(p, b, c, 0.22, WOOD_L, sides=5, name="Handle")
        rod(p, (b[0] - tilt * 0.3, b[1] - 0.3, b[2]), (b[0] + tilt * 0.7, b[1] + 0.5, b[2]), 0.45, WOOD_D, sides=6, name="Binding")
    broom(-27.8, 0.045, 8.8)
    broom(-24.8, -0.04, 8.8)
    # horizontal broom on the hooks
    dk.box(p, (-26, 5.6, 22.9), (9.0, 0.3, 0.3), WOOD_L, name="HookRod")
    rod(p, (-30.0, 5.4, 22.95), (-22.4, 5.4, 22.95), 0.2, WOOD_L, sides=5, name="Handle")
    # pointy hat on top
    hat(p, -26, 7.8, 22, 1.9, 1.3, 2.2, PUR, band=GOLD_D, bend=(0.3, 0.0), sides=8)
    star(p, -26, 8.7, 22.0 + 1.3, 0.5, GOLD, 0.25)
    return p


@part_builder("Garden")
def build_Garden():
    p = dk.Part("Garden")

    def bed(cx, cz, w=7.0, d=4.6):
        bx(p, cx - w / 2, cx + w / 2, 0, 1.8, cz - d / 2, cz + d / 2, WOOD_D, 0.07, name="Bed")
        bx(p, cx - w / 2 + 0.35, cx + w / 2 - 0.35, 1.7, 2.0, cz - d / 2 + 0.35, cz + d / 2 - 0.35, SOIL, 0.06, name="Soil")
        for sx in (-1, 1):
            for sz in (-1, 1):
                pole(p, cx + sx * (w / 2 - 0.2), cz + sz * (d / 2 - 0.2), 0, 2.0, 0.55, WOOD)
    bed(-89.5, 52.5); bed(-80.5, 53.2); bed(-85, 46.2)
    # pumpkins
    for (x, z, r) in ((-91.2, 52.4, 1.35), (-88.2, 52.9, 1.1), (-89.6, 51.2, 0.8)):
        o = lathe(p, (x, 2.0, z), [(0, 0), (r * 0.8, r * 0.3), (r, r * 0.8), (r * 0.8, r * 1.4), (0.2 * r, r * 1.6), (0, r * 1.55)], 8, ORANGE, 0.06, name="Pumpkin")
        dk.box(p, (x, 2.0 + r * 1.7, z), (0.25, 0.5, 0.25), GRN_D, name="Stem")
    # purple cabbages
    for (x, z, r) in ((-82.2, 53.4, 1.3), (-79.2, 53.0, 1.2), (-80.6, 54.4, 0.8)):
        ball2(p, (x, 2.0 + r * 0.9, z), r, PUR_L, sy=0.85, sides=7, jitter=0.07, name="Cabbage")
        ball2(p, (x, 2.0 + r * 0.7, z), r * 1.1, PUR, sy=0.5, sides=6, jitter=0.06, name="CabbageLeaf")
    # star flowers
    for (x, z, c, hh) in ((-87.2, 46.0, PINK, 3.2), (-85.0, 46.4, GOLD, 3.9), (-82.8, 45.9, CY, 3.0)):
        rod(p, (x, 2.0, z), (x, 2.0 + hh, z), 0.12, GRN_D, sides=4, name="Stem")
        star(p, x, 2.0 + hh + 0.5, z + 0.1, 0.95, c, 0.25)
        dk.box(p, (x + 0.7, 2.6, z), (0.9, 0.12, 0.35), GRN_D, rot=(0, 0, 25), name="Leaf")
    # scarecrow wizard
    sx, sz = -76.4, 45.8
    pole(p, sx, sz, 0, 6.8, 0.7, WOOD, name="ScPost")
    bx(p, sx - 2.5, sx + 2.5, 4.7, 5.2, sz - 0.25, sz + 0.25, WOOD, name="Arms")
    bx(p, sx - 1.0, sx + 1.0, 3.2, 5.3, sz - 0.9, sz + 0.9, PUR_D, 0.05, name="Robe")
    for ax in (-3.2, 3.2):
        dk.box(p, (sx + ax * 0.9, 4.45, sz), (1.5, 1.2, 0.8), PUR_D, rot=(0, 0, 8 if ax < 0 else -8), name="Sleeve")
        dk.box(p, (sx + ax * 1.0, 4.0, sz), (0.8, 0.6, 0.6), STRAW, name="Straw")
    ball2(p, (sx, 6.3, sz), 1.0, STRAW, sy=1.0, sides=6, jitter=0.05, name="Head")
    for e in (-0.4, 0.4):
        dk.box(p, (sx + e, 6.4, sz + 0.9), (0.25, 0.25, 0.15), IRON, name="Eye")
    hat(p, sx, 7.1, sz, 1.6, 1.0, 2.0, PUR, band=GOLD_D, bend=(0.6, 0.0), sides=8)
    return p


@part_builder("Crystals")
def build_Crystals():
    p = dk.Part("Crystals")
    cx, cz = -84.0, -38.0
    boulder(p, cx, 0, cz, 6.2, 2.4, ST_D, sides=8, jitter=0.1, name="Heap")
    boulder(p, cx - 3.0, 0, cz - 2.0, 2.6, 3.6, ST, sides=6, jitter=0.1, name="Rock")
    boulder(p, cx + 3.4, 0, cz + 3.0, 2.0, 1.8, ST_D, sides=6, jitter=0.1, name="Rock")
    boulder(p, cx - 2.2, 0, cz + 3.6, 1.5, 1.3, ST, sides=5, jitter=0.1, name="Rock")
    crystal(p, cx, 2.0, cz, 1.9, 14.1, CY, lean=(0.4, 0.0), sides=6, tip=0.3)
    crystal(p, cx - 3.8, 2.2, cz + 1.0, 1.35, 9.0, PUR_L, lean=(-1.0, 0.3), sides=6, tip=0.32)
    crystal(p, cx + 3.6, 2.2, cz - 1.0, 1.4, 9.0, PINK, lean=(1.4, 0.0), sides=6, tip=0.32)
    crystal(p, cx + 1.5, 2.0, cz + 3.4, 1.0, 5.6, CY, lean=(0.2, 1.2), sides=5, tip=0.35)
    crystal(p, cx - 2.0, 2.0, cz - 3.6, 1.0, 5.4, PUR_L, lean=(0.4, -1.2), sides=5, tip=0.35)
    for (dx, dz, c, h) in ((2.4, 0.6, PINK, 3.2), (-1.4, 2.2, CY, 3.0), (-4.6, -1.0, PINK, 2.6), (4.8, 2.4, PUR_L, 2.4), (0.8, -3.4, CY, 2.8)):
        crystal(p, cx + dx, 1.6, cz + dz, 0.55, h, c, lean=(dx * 0.15, dz * 0.15), sides=5, tip=0.35)
    return p


@part_builder("Library")
def build_Library():
    p = dk.Part("Library")
    bx(p, 61, 87, 0, 1, 6, 22, ST_D, 0.06, name="Plinth")
    o = bx(p, 67, 85, 1, 13, 8.5, 19.5, ST_L, 0.04, name="Hall")
    courses(o, ST_L, ST_X, 1.5)
    gable(p, 'x', 66.5, 85.5, 14, 6.2, 13.0, 19.2, 0.8, PUR, PUR_D, n=5)
    gable_end(p, 'x', 85.0, 14, 5.5, 13, 18.6, 0.8, ST_L)
    dk.cyl(p, (85.55, 15.2, 14), 1.1, 0.3, WIN, axis='x', verts=10, name="RoseWin")
    dk.cyl(p, (85.5, 15.2, 14), 1.4, 0.2, ST_D, axis='x', verts=10, name="RoseFrame")
    # tall corner tower with a pointed cap
    ot = lathe(p, (65, 1, 14), [(4.5, 0), (4.3, 19)], 4, ST, 0.05, rot0=pi / 4, name="Tower")
    courses(ot, ST, ST_L, 1.5)
    lathe(p, (65, 19.5, 14), [(4.9, 0), (4.9, 0.6), (4.3, 0.7), (0.0, 6.5)], 4, PUR, 0.05, rot0=pi / 4, name="Spire")
    ball2(p, (65, 26.4, 14), 0.5, GOLD, name="Tip")
    gwin(p, 65, 13.0, 14 + 3.2, 1.6, 4.0)
    gwin(p, 65, 6.0, 14 + 3.2, 1.6, 3.6)
    # door and stained glass
    z = 19.5
    door(p, 76, 1.0, z, 4.0, 5.6)
    bx(p, 73.5, 78.5, 1.0, 1.5, z, z + 1.3, ST, name="Step")
    gwin(p, 76, 8.0, z, 4.0, 4.8, glow=WIN, bar=False)
    slab(p, [(75.0, 8.6), (76.0, 8.6), (76.0, 10.6), (75.0, 10.6)], 0.2, 'xy', z + 0.42, CY, 0.0, name="Glass")
    slab(p, [(76.0, 8.6), (77.0, 8.6), (77.0, 10.6), (76.0, 10.6)], 0.2, 'xy', z + 0.42, PINK, 0.0, name="Glass")
    slab(p, [(75.0, 10.6), (76.0, 10.6), (75.7, 12.0), (75.0, 11.6)], 0.2, 'xy', z + 0.42, PUR_L, 0.0, name="Glass")
    slab(p, [(77.0, 10.6), (76.0, 10.6), (76.3, 12.0), (77.0, 11.6)], 0.2, 'xy', z + 0.42, GRN, 0.0, name="Glass")
    for x in (70.0, 82.0):
        gwin(p, x, 6.0, z, 1.8, 4.4, bar=False)
    # buttresses
    for x in (71, 81):
        bx(p, x - 0.7, x + 0.7, 1, 8.4, 19.5, 21.0, ST, 0.04, name="Buttress")
        bx(p, x - 0.7, x + 0.7, 8.4, 9.2, 19.5, 20.6, ST_D, name="ButtressCap")
        dk.box(p, (x, 9.4, 20.0), (1.0, 1.4, 0.9), ST, rot=(35, 0, 0), name="Pinnacle")
    # book trolley
    bx(p, 84.2, 86.6, 1.0, 1.4, 15.0, 17.4, WOOD, 0.05, name="Cart")
    bx(p, 84.2, 86.6, 1.4, 4.2, 15.0, 15.2, WOOD_D, name="CartBack")
    for i, c in enumerate((RED, PUR_L, CY, GOLD, PINK, GRN)):
        bx(p, 84.4 + i * 0.35, 84.4 + i * 0.35 + 0.28, 1.4, 3.0 + 0.3 * (i % 3), 15.4, 17.0, c, name="Book")
    return p


def rm(rot):
    rx, ry, rz = (math.radians(a) for a in rot)
    return Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')


def rpos(c, off, rot):
    v = rm(rot) @ Vector(off)
    return (c[0] + v.x, c[1] + v.y, c[2] + v.z)


def egg(p, x, y0, z, r, h, col, lean=0.0, sides=10, spot=None, name="Egg"):
    unit = [(0, 0), (0.55, 0.05), (0.9, 0.2), (1.0, 0.42), (0.93, 0.64), (0.7, 0.82), (0.38, 0.94), (0, 1.0)]
    prof = [(r * u, h * v, lean * v, 0.0) for u, v in unit]
    o = lathe(p, (x, y0, z), prof, sides, col, 0.05, name=name)
    if spot:
        recolor(o, lambda c, n, i: spot if i % 5 == 2 else None, 0.04)
    return o


def bottle(p, x, y0, z, r, h, col, cork=CREAM, sides=6, name="Bottle"):
    prof = [(r * 0.8, 0), (r, h * 0.1), (r, h * 0.55), (r * 0.42, h * 0.72), (r * 0.42, h * 0.92)]
    o = lathe(p, (x, y0, z), prof, sides, col, 0.04, name=name)
    dk.cyl(p, (x, y0 + h * 0.96, z), r * 0.5, h * 0.12, cork, verts=5, name="Cork")
    return o


@part_builder("Fountain")
def build_Fountain():
    p = dk.Part("Fountain")
    cx, cz = 52.0, 54.0
    o = lathe(p, (cx, 0, cz), [(7.6, 0), (8.1, 0.5), (8.1, 2.5), (7.2, 2.7), (7.1, 2.3)], 12, ST, 0.05, rot0=pi / 12, name="Basin")
    recolor(o, lambda c, n, i: WATER if n[1] > 0.9 and c[1] < 2.5 else (ST_L if i % 2 == 0 and abs(n[1]) < 0.5 else None), 0.03)
    o = lathe(p, (cx, 2.2, cz), [(1.8, 0), (1.2, 0.8), (1.0, 3.2)], 8, ST_L, 0.05, rot0=pi / 8, name="Column")
    o = lathe(p, (cx, 5.3, cz), [(1.0, 0), (2.8, 0.6), (4.4, 1.3), (4.5, 1.9), (3.9, 2.0)], 12, ST, 0.05, rot0=pi / 12, name="Bowl")
    recolor(o, lambda c, n, i: WATER if n[1] > 0.9 and c[1] > 7.0 else (ST_L if i % 2 == 0 and abs(n[1]) < 0.6 else None), 0.03)
    lathe(p, (cx, 7.2, cz), [(1.0, 0), (0.8, 1.0), (1.5, 1.8), (1.9, 2.0), (1.3, 2.1)], 8, ST_L, 0.05, rot0=pi / 8, name="Top")
    for a in (0, 90, 180, 270):
        ar = math.radians(a)
        if a in (0, 180):
            dk.box(p, (cx + math.cos(ar) * 4.55, 4.9, cz), (0.18, 4.6, 0.7), WATER_L, name="Fall")
        else:
            dk.box(p, (cx, 4.9, cz + math.sin(ar) * 4.55), (0.7, 4.6, 0.18), WATER_L, name="Fall")
    # jets from the top and the golden star
    for a in range(0, 360, 90):
        ar = math.radians(a + 45)
        rod(p, (cx, 9.6, cz), (cx + 1.6 * math.cos(ar), 8.4, cz + 1.6 * math.sin(ar)), 0.16, WATER_L, sides=4, name="Jet")
    star(p, cx, 11.3, cz, 1.9, GOLD, 0.7)
    slab(p, [(11.3 + v, cz + u) for u, v in star_pts(0, 0, 1.9, 0.85)], 0.7, 'yz', cx, GOLD, 0.0, name="Star2")
    dk.cyl(p, (cx, 11.3, cz), 0.5, 0.9, GOLD_D, verts=6, name="Hub")
    for k in range(6):
        a = 2 * pi * k / 6
        dk.cone(p, (cx + 6.3 * math.cos(a), 2.7, cz + 6.3 * math.sin(a)), 0.45, 0.8, PINK if k % 2 else CY, verts=4, name="Gem")
    spark(p, cx + 3.0, 10.0, cz + 2.0, 0.7, WATER_L)
    return p


@part_builder("Owl")
def build_Owl():
    p = dk.Part("Owl")
    cx, cz = 18.0, -56.0
    prof = [(4.2, 0), (3.4, 1.8), (2.4, 4.5), (2.0, 8, -0.3, 0), (1.9, 12, -0.7, 0.2), (1.8, 16, -0.4, 0.2), (1.6, 20.2, -0.6, 0.0)]
    o = lathe(p, (cx, 0, cz), prof, 6, WOOD_D, 0.08, name="Trunk")
    recolor(o, lambda c, n, i: WOOD if i % 3 == 0 else None, 0.06)
    for k in range(5):
        a = 2 * pi * k / 5 + 0.5
        rod(p, (cx + 2.8 * math.cos(a), 2.4, cz + 2.4 * math.sin(a)), (cx + 5.2 * math.cos(a), 0.0, cz + 3.4 * math.sin(a)), 1.0, WOOD_D, sides=5, r2=0.3, name="Root")
    r_, dx_, dz_ = prof_at(prof, 5.0)
    slab(p, arch_pts(cx + dx_, 3.4, 1.8, 2.8, pointed=False), 0.4, 'xy', cz + dz_ + 0.866 * r_ - 0.05, IRON, 0.0, name="Knothole")
    # branches
    rod(p, (cx - 0.5, 12.3, cz), (cx + 7.0, 13.8, cz), 0.8, WOOD_D, sides=5, r2=0.4, name="Branch")
    rod(p, (cx - 0.9, 15.6, cz), (cx - 6.4, 18.0, cz), 0.7, WOOD_D, sides=5, r2=0.3, name="Branch")
    rod(p, (cx - 4.0, 17.0, cz), (cx - 4.2, 19.6, cz + 0.6), 0.3, WOOD_D, sides=4, name="Twig")
    for (dx, y, dz, r, c) in ((-5.4, 19.2, 0.0, 1.6, GRN_D), (-3.6, 20.4, 0.4, 1.4, GRN), (-1.8, 22.0, 0.2, 1.7, GRN_D), (-0.2, 21.0, -0.5, 1.3, GRN), (-5.8, 17.2, 0.8, 1.0, GRN)):
        ball2(p, (cx + dx, y, cz + dz), r, c, sy=0.85, sides=6, jitter=0.07, name="Leaves")
    # the owl
    ox = 22.0
    oy = 13.5
    lathe(p, (ox, oy, cz), [(1.5, 0), (2.3, 0.8), (2.6, 2.2), (2.1, 3.6), (1.5, 4.4)], 8, FUR, 0.06, rot0=pi / 8, name="Body")
    ball2(p, (ox, oy + 2.1, cz + 1.2), 1.7, CREAM, sy=1.35, sides=7, jitter=0.04, name="Belly")
    for sx in (-1, 1):
        dk.box(p, (ox + sx * 2.45, oy + 2.4, cz - 0.1), (0.7, 3.4, 2.6), dk.shade(FUR, 0.75), rot=(0, 0, -sx * 6), jitter=0.05, name="Wing")
        dk.box(p, (ox + sx * 1.0, oy + 0.3, cz + 1.9), (0.5, 0.5, 0.9), GOLD_D, name="Foot")
    dk.box(p, (ox, oy + 0.9, cz - 2.2), (1.8, 2.0, 0.7), dk.shade(FUR, 0.7), rot=(-20, 0, 0), jitter=0.05, name="Tail")
    ball2(p, (ox, oy + 5.7, cz), 2.0, FUR, sy=0.92, sides=8, jitter=0.05, name="Head")
    for sx in (-1, 1):
        dk.cyl(p, (ox + sx * 0.95, oy + 5.9, cz + 1.7), 0.85, 0.35, CREAM, axis='z', verts=8, name="EyeRing")
        dk.cyl(p, (ox + sx * 0.95, oy + 5.9, cz + 1.92), 0.62, 0.3, WIN, axis='z', verts=8, name="Eye")
        dk.cyl(p, (ox + sx * 0.95, oy + 5.9, cz + 2.1), 0.3, 0.3, IRON, axis='z', verts=6, name="Pupil")
    rod(p, (ox, oy + 5.4, cz + 1.8), (ox, oy + 4.9, cz + 2.9), 0.5, GOLD_D, sides=4, r2=0.0, name="Beak")
    hat(p, ox, oy + 7.4, cz, 2.5, 1.45, 3.1, PUR, band=GOLD_D, bend=(0.5, 0.0), sides=8)
    star(p, ox, oy + 8.6, cz + 1.15, 0.45, GOLD, 0.2)
    return p


@part_builder("Alchemy")
def build_Alchemy():
    p = dk.Part("Alchemy")
    # table
    bx(p, 70.2, 85.8, 2.9, 3.5, -61.0, -55.0, WOOD, 0.05, name="Top")
    for x in (71.2, 84.8):
        for z in (-60.4, -55.6):
            pole(p, x, z, 0, 2.9, 0.8, WOOD_D)
    bx(p, 71.0, 85.0, 1.0, 1.3, -60.6, -55.4, WOOD_D, name="Rail")
    # shelf unit behind
    for x in (71.0, 85.0):
        pole(p, x, -61.6, 0, 9.0, 0.8, WOOD_D)
    bx(p, 70.6, 85.4, 6.2, 6.7, -62.4, -60.8, WOOD, 0.05, name="Shelf")
    bx(p, 70.6, 85.4, 8.6, 9.0, -62.4, -60.8, PUR, 0.05, name="Cap")
    bx(p, 70.6, 85.4, 3.5, 6.2, -62.3, -62.1, WOOD_D, name="Back")
    for i, (c, h) in enumerate(((RED, 2.0), (CY, 1.6), (PINK, 2.2), (GRN, 1.7), (GOLD, 1.9), (PUR_L, 2.1))):
        bottle(p, 72.6 + i * 2.1, 6.7, -61.5, 0.62, h, c)
    for i, c in enumerate((RED, PUR_L, GRN, CY, GOLD)):
        bx(p, 71.4 + i * 0.5, 71.4 + i * 0.5 + 0.4, 3.6, 5.6 - 0.2 * (i % 2), -62.0, -61.0, c, name="Book")
    # flasks on the table
    o = lathe(p, (74.0, 3.5, -57.4), [(0.01, 0), (1.3, 0.3), (1.9, 1.4), (1.5, 2.6), (0.55, 3.2), (0.55, 4.0), (0.8, 4.2)], 8, GRN, 0.04, name="Flask")
    recolor(o, lambda c, n, i: dk.shade(GRN, 1.25) if n[1] > 0.4 else None, 0.04)
    dk.cyl(p, (74.0, 7.75, -57.4), 0.55, 0.4, CREAM, verts=6, name="Cork")
    o = lathe(p, (79.0, 3.5, -58.0), [(0.01, 0), (1.2, 0.3), (1.7, 1.2), (1.4, 2.3), (0.5, 2.9), (0.5, 3.5), (0.75, 3.7)], 8, PUR_L, 0.04, name="Flask")
    recolor(o, lambda c, n, i: dk.shade(PUR_L, 1.25) if n[1] > 0.4 else None, 0.04)
    o = lathe(p, (83.2, 3.5, -58.4), [(1.0, 0), (1.1, 0.2), (1.1, 2.4), (0.5, 3.0), (0.5, 3.3)], 8, CY, 0.04, name="Tube")
    recolor(o, lambda c, n, i: dk.shade(CY, 1.25) if n[1] > 0.4 else None, 0.04)
    # copper alembic and pipes
    lathe(p, (76.5, 3.5, -58.0), [(0.5, 0), (1.4, 0.4), (1.9, 1.3), (1.6, 2.2), (0.9, 2.8), (0.5, 3.0)], 8, BRASS, 0.05, name="Pot")
    rod(p, (76.5, 6.4, -58.0), (76.5, 6.9, -58.0), 0.28, BRASS_D, sides=5, name="Pipe")
    rod(p, (76.5, 6.9, -58.0), (74.4, 6.9, -58.0), 0.28, BRASS_D, sides=5, name="Pipe")
    rod(p, (74.4, 6.9, -58.0), (74.1, 6.9, -57.6), 0.28, BRASS_D, sides=5, name="Pipe")
    rod(p, (76.5, 6.9, -58.0), (82.4, 6.9, -58.4), 0.28, BRASS_D, sides=5, name="Pipe")
    rod(p, (82.4, 6.9, -58.4), (82.6, 6.5, -58.4), 0.28, BRASS_D, sides=5, name="Pipe")
    torus(p, (78.4, 7.0, -58.1), 0.7, 0.2, BRASS_D, major=8, minor=4, rx=90, name="Coil")
    # bubbles and a red flask on the shelf corner
    for (x, y, z, r) in ((74.0, 8.4, -57.4, 0.4), (74.5, 9.0, -57.0, 0.3), (83.4, 7.5, -58.4, 0.35), (79.0, 7.6, -58.0, 0.45)):
        ball2(p, (x, y, z), r, WATER_L, sides=5, name="Bubble")
    hat(p, 85.0, 3.5, -56.4, 1.4, 0.9, 1.6, PUR, band=GOLD_D, sides=6)
    return p


@part_builder("Range")
def build_Range():
    p = dk.Part("Range")
    bx(p, 12, 36, 0, 0.3, 48.5, 55.5, IRON, 0.05, name="Platform")
    bx(p, 13, 35, 0.3, 0.5, 54.7, 55.3, RED, name="Line")

    def target(x):
        pole(p, x, 52.0, 0.3, 5.6, 0.8, WOOD_D)
        rod(p, (x, 0.3, 54.0), (x, 3.2, 52.3), 0.28, WOOD_D, sides=4, name="Prop")
        rod(p, (x, 0.3, 50.0), (x, 3.2, 51.8), 0.28, WOOD_D, sides=4, name="Prop")
        zc = 52.6
        for (r, h, c) in ((2.6, 0.5, WOOD_L), (2.3, 0.62, CREAM), (1.8, 0.74, RED), (1.3, 0.86, CREAM), (0.8, 0.98, RED), (0.35, 1.1, GOLD)):
            dk.cyl(p, (x, 5.6, zc + h / 2 - 0.25), r, h, c, axis='z', verts=12, name="Target")
    target(16)
    target(32)
    star(p, 17.2, 6.5, 52.6 + 0.66, 0.7, PUR_L, 0.12)
    star(p, 30.8, 4.7, 52.6 + 0.7, 0.6, CY, 0.12)
    # the straw dummy
    x = 24.0
    pole(p, x, 52.0, 0.3, 7.0, 0.9, WOOD)
    bx(p, x - 1.6, x + 1.6, 0.3, 0.9, 51.2, 52.8, WOOD_D, name="Foot")
    bx(p, x - 2.9, x + 2.9, 4.6, 5.2, 51.75, 52.25, WOOD, name="Arms")
    for sx in (-1, 1):
        bx(p, x + sx * 2.9 - 0.5, x + sx * 2.9 + 0.5, 4.0, 4.9, 51.5, 52.5, STRAW, 0.07, name="Hand")
    o = bx(p, x - 1.5, x + 1.5, 3.2, 6.8, 50.9, 53.1, STRAW, 0.08, name="Body")
    bx(p, x - 1.55, x + 1.55, 3.9, 4.3, 50.85, 53.15, WOOD_D, name="Belt")
    ball2(p, (x, 7.6, 52.0), 1.25, STRAW, sy=1.0, sides=7, jitter=0.06, name="Head")
    for e in (-0.5, 0.5):
        dk.box(p, (x + e, 7.7, 53.2), (0.28, 0.28, 0.15), IRON, name="Eye")
    hat(p, x, 8.5, 52.0, 2.2, 1.35, 2.2, PUR, band=GOLD_D, bend=(0.5, 0.0), sides=8)
    star(p, x, 5.6, 53.15, 0.8, PUR_L, 0.12)
    # wand rack at the right end
    bx(p, 33.9, 35.4, 0.3, 1.2, 49.0, 49.8, WOOD, name="RackBox")
    for i, c in enumerate((PUR_L, CY, PINK)):
        rod(p, (34.2 + i * 0.5, 1.2, 49.4), (34.0 + i * 0.5 + 0.3, 3.4, 49.4), 0.15, c, sides=4, name="Wand")
    return p


@part_builder("Egg")
def build_Egg():
    p = dk.Part("Egg")
    cx, cz = 82.0, -10.0
    lathe(p, (cx, 0, cz), [(4.4, 0), (6.6, 0.6), (7.0, 1.5), (6.4, 1.9), (5.0, 1.5)], 12, WOOD_D, 0.08, name="NestBowl")
    for k in range(24):
        a = 2 * pi * k / 24 + R.uniform(-0.1, 0.1)
        rr = 6.2 + R.uniform(-0.2, 0.5)
        t = R.choice((-1, 1))
        A = (cx + rr * math.cos(a), 1.5 + R.uniform(0, 0.4), cz + rr * math.sin(a))
        B = (cx + (rr + 0.2) * math.cos(a + t * 0.55), 1.9 + R.uniform(0, 0.5), cz + (rr + 0.2) * math.sin(a + t * 0.55))
        rod(p, A, B, 0.3, WOOD if k % 2 else WOOD_L, sides=4, name="Twig")
    for k in range(9):
        a = 2 * pi * k / 9 + 0.3
        rod(p, (cx + 6.6 * math.cos(a), 1.7, cz + 6.6 * math.sin(a)), (cx + 6.95 * math.cos(a + 0.2), 2.8 + R.uniform(0, 0.7), cz + 6.95 * math.sin(a + 0.2)), 0.22, WOOD_L, sides=4, r2=0.1, name="Twig")
    # big wobbling green egg
    egg(p, cx, 1.3, cz, 4.3, 10.0, GRN, lean=0.5, sides=10, spot=GRN_D)
    for (dx, dy, dz, r) in ((1.8, 4.2, 3.4, 0.7), (-1.8, 6.2, 3.1, 0.6), (0.6, 8.0, 2.4, 0.5), (-2.6, 3.4, 2.5, 0.55)):
        blob(p, (cx + dx + 0.5 * dy / 10, 1.3 + dy, cz + dz), r, GRN_D, sy=0.6, sides=5, name="Spot")
    # crown of purple scales on top
    for (dx, dz, h, lx) in ((0.9, 0.0, 2.3, 0.3), (-0.8, 0.4, 2.0, -0.5), (0.0, -0.7, 1.8, 0.0)):
        crystal(p, cx + 0.5 + dx, 11.0, cz + dz, 0.55, h, PUR_L, lean=(lx, 0), sides=4, tip=0.5)
    egg(p, 77.0, 1.5, -6.6, 1.8, 4.0, PINK, sides=8, spot=(240, 160, 220))
    egg(p, 86.8, 1.5, -13.2, 1.7, 3.6, CY, sides=8, spot=(150, 230, 245))
    # coins
    for k in range(5):
        dk.cyl(p, (87.0, 0.35 + 0.28 * k, -6.0), 1.1, 0.26, GOLD if k % 2 else GOLD_D, verts=8, name="Coin")
    for (x, z) in ((84.4, -5.0), (88.0, -8.2), (76.0, -12.6), (79.5, -14.4)):
        dk.cyl(p, (x, 0.2, z), 0.8, 0.2, GOLD, verts=8, name="Coin")
        dk.cyl(p, (x + 0.7, 0.4, z + 0.3), 0.8, 0.2, GOLD_D, verts=8, rot=(0, 0, 10), name="Coin")
    return p


@part_builder("Bridge")
def build_Bridge():
    p = dk.Part("Bridge")

    def top(x):
        return 2.4 + 2.8 * math.sin(pi * (x - 72) / 20)
    # pond
    bx(p, 70.3, 93.7, 0, 0.5, 48.3, 59.7, WATER, 0.04, name="Water")
    pts = [(72, 0.4), (72, 2.4)]
    pts += [(72 + 2 * k, top(72 + 2 * k)) for k in range(1, 10)]
    pts += [(92, 2.4), (92, 0.4), (89, 0.4)]
    pts += [(82 + 7 * math.cos(t), 0.4 + 3.6 * math.sin(t)) for t in [pi * k / 8 for k in range(1, 8)]]
    pts += [(75, 0.4)]
    slab(p, pts, 4.6, 'xy', 54.0, ST_L, 0.04, name="Deck")
    # voussoirs round the arch
    for k in range(8):
        t0, t1 = pi * k / 8, pi * (k + 1) / 8
        inner = lambda t, s=0.0: (82 + (7 + s) * math.cos(t), 0.4 + (3.6 + s) * math.sin(t))
        poly_ = [inner(t0), inner(t1), inner(t1, 0.9), inner(t0, 0.9)]
        slab(p, poly_, 4.85, 'xy', 54.0, ST_X if k % 2 else ST_D, 0.03, name="Voussoir")
    for zz in (52.0, 56.0):
        xs = [72.4 + 19.2 * k / 12 for k in range(13)]
        poly_ = [(x, top(x) + 0.05) for x in xs] + [(x, top(x) + 1.0) for x in xs][::-1]
        slab(p, poly_, 0.55, 'xy', zz, ST, 0.04, name="Parapet")
    for x in (72.3, 91.7):
        for zz in (51.6, 56.4):
            dk.box(p, (x, 3.1, zz), (0.9, 1.0, 0.9), ST_D, name="PostCap")
    # abutments at both ends and rocks around the pond
    bx(p, 70, 74.2, 0, 2.4, 51.2, 56.8, ST, 0.05, name="Abut")
    bx(p, 89.8, 94, 0, 2.4, 51.2, 56.8, ST, 0.05, name="Abut")
    for k in range(7):
        x = 71.8 + k * 3.3
        boulder(p, x, 0, 48.7 + R.uniform(-0.3, 0.3), 1.2, 0.9 + R.random() * 0.4, ST_D if k % 2 else ST, name="Edge")
        boulder(p, x + 0.8, 0, 59.4 + R.uniform(-0.3, 0.3), 1.2, 0.9 + R.random() * 0.4, ST if k % 2 else ST_D, name="Edge")
    # lanterns on stone posts
    for x in (72.6, 91.4):
        for zz in (57.1, 50.9):
            o = lathe(p, (x, 2.4, zz), [(0.8, 0), (0.7, 3.2)], 6, ST, 0.04, name="LampPost")
            bx(p, x - 0.85, x + 0.85, 5.55, 5.9, zz - 0.85, zz + 0.85, GOLD_D, name="LampBase")
            bx(p, x - 0.6, x + 0.6, 5.9, 7.2, zz - 0.6, zz + 0.6, WIN, 0.0, name="LampGlow")
            for sx in (-1, 1):
                for sz in (-1, 1):
                    pole(p, x + sx * 0.62, zz + sz * 0.62, 5.9, 7.2, 0.22, GOLD_D, name="LampFrame")
            lathe(p, (x, 7.2, zz), [(1.1, 0), (0.9, 0.2), (0.0, 0.8)], 4, GOLD, 0.03, rot0=pi / 4, name="LampCap")
    # lily pads, lotus and a koi
    for (x, z) in ((76.0, 50.5), (79.5, 58.0), (86.5, 50.6), (89.5, 58.2), (84.0, 58.6), (74.8, 57.8)):
        pts = [(x + 0.95 * math.cos(a), z + 0.95 * math.sin(a)) for a in [2 * pi * k / 8 + 0.3 for k in range(8)]]
        flat(p, pts, 0.52, GRN, 0.06, name="Pad")
    for (x, z) in ((79.5, 58.0), (86.5, 50.6)):
        dk.cone(p, (x, 0.5, z), 0.5, 0.7, PINK, verts=6, jitter=0.05, name="Lotus")
    for (x, z, s) in ((77.0, 53.2, 1), (87.6, 55.4, -1)):
        flat(p, [(x - 1.0 * s, z), (x - 0.4 * s, z + 0.45), (x + 0.7 * s, z + 0.2), (x + 1.1 * s, z - 0.35), (x + 1.7 * s, z - 0.3), (x + 1.4 * s, z + 0.1), (x + 1.7 * s, z + 0.5), (x + 1.1 * s, z + 0.3), (x + 0.7 * s, z - 0.4), (x - 0.4 * s, z - 0.4)], 0.53, ORANGE, 0.0, name="Koi")
    return p


def lectern_lines(p, c, rot, x0, n, w):
    for k in range(n):
        q = rpos(c, (0, 0.27, -2.4 + k * 1.0), rot)
        dk.box(p, (q[0] + x0, q[1], q[2]), (w * (0.85 if k % 3 == 2 else 1.0), 0.06, 0.2), PUR, rot=rot, name="Line")


@part_builder("Spellbook")
def build_Spellbook():
    p = dk.Part("Spellbook")
    cx, cz = 36.0, 32.0
    o = lathe(p, (cx, 0, cz), [(3.3, 0), (3.3, 0.9), (2.5, 1.2), (1.4, 2.0), (1.1, 5.4), (2.0, 6.0), (2.0, 6.4)], 8, ST, 0.05, rot0=pi / 8, name="Pedestal")
    courses(o, ST, ST_L, 1.0)
    for sx in (-1, 1):
        dk.box(p, (cx + sx * 1.5, 5.4, cz), (0.5, 0.5, 1.2), GOLD_D, name="Bracket")
    dk.box(p, (cx, 6.9, cz), (9.0, 0.8, 6.0), WOOD, rot=(22, 0, 0), jitter=0.05, name="Desk")
    dk.box(p, (cx, 7.6, cz), (11.0, 0.5, 7.2), RED, rot=(22, 0, 0), jitter=0.04, name="Cover")
    for sx in (-1, 1):
        c = (cx + sx * 2.7, 8.25, cz)
        dk.box(p, c, (5.0, 0.4, 6.4), CREAM, rot=(22, 0, sx * -8), jitter=0.03, name="Page")
        for k in range(5):
            q = rpos(c, (0, 0.23, -2.3 + k * 1.15), (22, 0, sx * -8))
            dk.box(p, q, (3.5 - 0.5 * (k % 2), 0.06, 0.2), PUR, rot=(22, 0, sx * -8), name="Line")
    dk.box(p, (cx, 8.3, cz), (0.5, 0.5, 6.6), GOLD_D, rot=(22, 0, 0), name="Spine")
    for sx in (-1, 1):
        for sz in (-1, 1):
            q = rpos((cx, 7.6, cz), (sx * 5.45, 0.0, sz * 3.55), (22, 0, 0))
            dk.box(p, q, (0.9, 0.7, 0.9), GOLD_D, rot=(22, 0, 0), name="Corner")
    # the self-writing quill, ink trail and sparkles
    rod(p, (39.0, 8.6, 32.6), (40.6, 11.4, 30.6), 0.09, CREAM, sides=4, name="Quill")
    dk.box(p, (40.4, 10.8, 30.8), (0.9, 3.0, 0.12), (250, 244, 232), rot=(0, 0, -22), jitter=0.02, name="Feather")
    dk.box(p, (40.0, 10.2, 30.9), (0.2, 1.2, 0.14), PUR_L, rot=(0, 0, -22), name="Vein")
    spark(p, 32.4, 11.3, 31.0, 0.9, GOLD)
    spark(p, 35.3, 10.6, 31.5, 0.6, CY)
    spark(p, 38.0, 12.0, 31.0, 0.5, PINK)
    return p


@part_builder("Pavilion")
def build_Pavilion():
    p = dk.Part("Pavilion")
    cx, cz = 18.0, 4.0
    o = lathe(p, (cx, 0, cz), [(6.2, 0), (6.2, 0.5), (5.5, 0.6), (5.5, 1.1)], 12, ST_D, 0.05, rot0=pi / 12, name="Base")
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = cx + sx * 4.2, cz + sz * 4.2
            bx(p, x - 0.9, x + 0.9, 1.1, 1.6, z - 0.9, z + 0.9, ST, 0.04, name="ColBase")
            dk.cyl(p, (x, 4.0, z), 0.6, 4.8, ST_L, verts=8, jitter=0.04, name="Column")
            bx(p, x - 0.85, x + 0.85, 6.3, 6.7, z - 0.85, z + 0.85, ST, 0.04, name="Capital")
    # crystal ball on a pedestal
    lathe(p, (cx, 1.1, cz), [(1.9, 0), (1.2, 0.9), (1.1, 1.9), (1.7, 2.4)], 8, ST, 0.05, rot0=pi / 8, name="Pedestal")
    torus(p, (cx, 3.6, cz), 1.45, 0.17, GOLD, major=10, minor=4, name="Cradle")
    ball2(p, (cx, 5.1, cz), 1.9, CY, sy=1.0, sides=10, jitter=0.04, name="Ball")
    spark(p, cx, 5.2, cz, 0.8, (230, 250, 255))
    # pagoda roof
    prof = [(5.7, 0), (6.5, 0.15), (6.6, 0.55), (5.4, 1.2), (4.3, 1.9), (3.7, 2.1), (4.1, 2.45), (3.3, 3.1), (2.5, 3.9), (1.7, 4.7), (1.1, 5.3), (0, 5.8)]
    o = lathe(p, (cx, 6.7, cz), prof, 12, PUR, 0.04, rot0=pi / 12, name="Roof")
    recolor(o, lambda c, n, i: PUR_D if (i % 12) % 2 == 1 else None, 0.04)
    for k in range(12):
        a = 2 * pi * k / 12
        dk.cone(p, (cx + 6.55 * math.cos(a), 7.2, cz + 6.55 * math.sin(a)), 0.4, 0.8, GOLD, verts=4, name="EaveTip")
    torus(p, (cx, 6.95, cz), 5.6, 0.16, GOLD, major=12, minor=4, name="EaveTrim")
    ball2(p, (cx, 12.7, cz), 0.55, GOLD, sides=6, name="Finial")
    rod(p, (cx, 12.2, cz), (cx, 13.0, cz), 0.15, GOLD_D, sides=4, name="Spike")
    return p


@part_builder("Statue")
def build_Statue():
    p = dk.Part("Statue")
    cx, cz = 64.0, 38.0
    o = bx(p, 59, 69, 0, 3.2, 33, 43, ST_D, 0.05, name="Plinth")
    bx(p, 59.8, 68.2, 3.2, 4.4, 33.8, 42.2, ST, 0.05, name="Step")
    lathe(p, (cx, 4.4, cz), [(3.9, 0), (3.4, 1.8), (2.8, 5.0), (2.5, 8.0), (2.5, 10.0)], 8, ST_L, 0.05, rot0=pi / 8, name="Robe")
    robe = p.objs[-1]
    recolor(robe, lambda c, n, i: dk.shade(ST_L, 0.85) if i % 2 == 1 else None, 0.04)
    bx(p, 61.0, 67.0, 13.4, 16.2, 36.6, 39.4, ST_L, 0.05, name="Shoulders")
    bx(p, 61.4, 66.6, 13.0, 13.5, 36.3, 39.7, GOLD_D, name="Collar")
    ball2(p, (cx, 18.0, cz), 1.9, ST_X, sy=1.0, sides=8, jitter=0.04, name="Head")
    slab(p, [(63.0, 17.4), (65.0, 17.4), (64.6, 13.2), (64.0, 11.4), (63.4, 13.2)], 1.0, 'xy', 40.3, ST_X, 0.04, name="Beard")
    slab(p, [(62.8, 17.5), (65.2, 17.5), (64.7, 16.2), (63.3, 16.2)], 0.8, 'xy', 40.55, ST_L, 0.04, name="Mustache")
    for e in (-0.7, 0.7):
        dk.box(p, (cx + e, 18.4, cz + 1.75), (0.4, 0.3, 0.2), ST_D, name="Eye")
    hat(p, cx, 19.7, cz, 3.1, 2.0, 6.2, ST_D, band=GOLD_D, bend=(1.2, -0.6), sides=8)
    star(p, cx, 22.0, cz + 1.8, 0.7, GOLD, 0.2)
    # arms, staff, crystal
    rod(p, (66.6, 14.8, 38.4), (67.6, 13.4, 39.3), 0.85, ST_L, sides=6, name="Arm")
    ball2(p, (67.6, 13.3, 39.4), 0.8, ST_X, sides=6, name="Hand")
    rod(p, (60.9, 14.6, 38.0), (60.4, 11.6, 39.0), 0.85, ST_L, sides=6, name="Arm")
    ball2(p, (60.4, 11.4, 39.2), 0.75, ST_X, sides=6, name="Hand")
    rod(p, (67.6, 4.4, 39.4), (67.6, 19.4, 39.4), 0.34, WOOD, sides=5, name="Staff")
    torus(p, (67.6, 19.4, 39.4), 0.8, 0.14, GOLD, major=8, minor=4, name="StaffRing")
    crystal(p, 67.6, 19.4, 39.4, 0.95, 3.4, CY, sides=6, tip=0.38)
    return p


@part_builder("Observatory")
def build_Observatory():
    p = dk.Part("Observatory")
    cx, cz = -50.0, -48.0
    bx(p, -60, -40, 0, 1.2, -58, -38, ST_D, 0.06, name="Plinth")
    o = lathe(p, (cx, 1.2, cz), [(8.0, 0), (7.8, 10.0)], 12, ST, 0.05, rot0=pi / 12, name="Tower")
    courses(o, ST, ST_L, 1.6)
    lathe(p, (cx, 10.9, cz), [(7.9, 0), (8.9, 0.15), (8.9, 1.0), (8.2, 1.1)], 12, ST_D, 0.05, rot0=pi / 12, name="Ring")
    for k in range(12):
        a = 2 * pi * k / 12
        dk.box(p, (cx + 8.95 * math.cos(a), 11.5, cz + 8.95 * math.sin(a)), (0.5, 0.5, 0.5), GOLD, rot=(0, -math.degrees(a), 0), name="RingStud")
    d = dome(p, cx, 12.0, cz, 8.2, 11.4, COPPER, sides=12, rings=5, jitter=0.04, rot0=pi / 12, name="Dome")
    recolor(d, lambda c, n, i: IRON if (i % 12) == 2 else (COPPER_D if (i % 12) % 2 == 1 else None), 0.04)
    ball2(p, (cx, 23.5, cz), 0.6, GOLD, sides=6, name="DomeTip")
    # telescope sticking out of the slit
    rod(p, (cx - 0.3, 17.0, cz + 3.4), (cx + 2.6, 24.6, cz + 6.0), 1.05, BRASS, sides=8, name="Tube")
    rod(p, (cx + 2.2, 23.6, cz + 5.65), (cx + 3.4, 26.8, cz + 6.7), 1.45, BRASS_D, sides=8, r2=1.7, name="Bell")
    rod(p, (cx + 3.4, 26.8, cz + 6.7), (cx + 3.6, 27.3, cz + 6.85), 1.35, CY, sides=8, name="Lens")
    for t in (0.3, 0.6):
        q = (cx - 0.3 + 2.9 * t, 17.0 + 7.6 * t, cz + 3.4 + 2.6 * t)
        rod(p, (q[0] - 0.1, q[1] - 0.25, q[2] - 0.1), (q[0] + 0.1, q[1] + 0.25, q[2] + 0.1), 1.3, GOLD_D, sides=8, name="TubeRing")
    # door, steps, lamp
    z0 = cz + 8.0 * math.cos(pi / 12) - 0.08
    door(p, cx, 1.2, z0, 3.4, 5.2)
    bx(p, cx - 3.0, cx + 3.0, 0, 1.2, z0, z0 + 1.5, ST_L, 0.05, name="Step")
    bx(p, cx - 2.2, cx + 2.2, 0, 1.7, z0, z0 + 0.7, ST, 0.05, name="Step")
    for sx in (-1, 1):
        dk.box(p, (cx + sx * 3.2, 5.8, z0 + 0.3), (0.5, 0.9, 0.5), IRON, name="LampArm")
        dk.box(p, (cx + sx * 3.2, 5.0, z0 + 0.35), (0.9, 1.1, 0.9), WIN, name="Lamp")
    # gold star frieze and a signal flag
    for k in range(12):
        a = 2 * pi * (k + 0.5) / 12
        dk.box(p, (cx + 7.6 * math.cos(a), 9.2, cz + 7.6 * math.sin(a)), (0.9, 0.9, 0.15), GOLD, rot=(0, -math.degrees(a) + 90, 45), name="Frieze") if k % 3 == 0 else None
    gwin(p, cx - 3.3, 4.8, z0 - 0.35, 1.2, 2.6)
    gwin(p, cx + 3.3, 4.8, z0 - 0.35, 1.2, 2.6)
    return p


@part_builder("Griffin")
def build_Griffin():
    p = dk.Part("Griffin")
    z = 2.0
    bx(p, 30, 42, 0, 3.0, -1, 5, ST_D, 0.05, name="Plinth")
    bx(p, 30.4, 41.6, 3.0, 3.4, -0.6, 4.6, ST, 0.05, name="Trim")
    # body: lion rear and eagle chest
    lathe(p, (31.0, 5.6, z), [(0.6, 0), (1.5, 0.8), (1.9, 2.4), (1.8, 4.6), (1.4, 6.6)], 8, ST_L, 0.05, axis='x', name="Body")
    ball2(p, (38.8, 6.6, z), 2.1, ST_L, sy=1.15, sides=8, jitter=0.05, name="Chest")
    ball2(p, (33.8, 5.2, z - 1.3), 1.5, ST, sy=0.95, sides=7, jitter=0.05, name="Haunch")
    ball2(p, (33.8, 5.2, z + 1.3), 1.5, ST, sy=0.95, sides=7, jitter=0.05, name="Haunch")
    rod(p, (39.4, 7.6, z), (40.4, 9.6, z), 1.15, ST_L, sides=7, name="Neck")
    ball2(p, (40.7, 10.3, z), 1.35, ST_X, sy=0.95, sides=8, jitter=0.04, name="Head")
    rod(p, (41.6, 10.5, z), (42.7, 9.5, z), 0.7, GOLD, sides=4, r2=0.1, name="Beak")
    for sz in (-1, 1):
        dk.box(p, (41.4, 10.9, z + sz * 0.95), (0.45, 0.4, 0.2), IRON, name="Eye")
        dk.cone(p, (40.2, 11.2, z + sz * 0.6), 0.45, 1.7, ST, verts=4, name="Ear")
    # legs
    for sz in (-1, 1):
        rod(p, (39.2, 5.4, z + sz * 0.9), (40.0, 3.5, z + sz * 0.9), 0.55, ST_L, sides=5, name="ForeLeg")
        bx(p, 39.6, 41.2, 3.4, 4.0, z + sz * 0.9 - 0.5, z + sz * 0.9 + 0.5, GOLD_D, name="Talon")
        rod(p, (33.6, 4.2, z + sz * 1.5), (33.2, 3.4, z + sz * 1.5), 0.7, ST, sides=5, name="HindLeg")
        bx(p, 32.6, 34.2, 3.4, 3.9, z + sz * 1.5 - 0.6, z + sz * 1.5 + 0.6, ST_D, name="Paw")
    # tail
    rod(p, (31.4, 5.6, z), (30.4, 7.0, z), 0.55, ST, sides=5, name="Tail")
    rod(p, (30.4, 7.0, z), (30.6, 9.0, z), 0.5, ST, sides=5, name="Tail")
    ball2(p, (30.7, 9.6, z), 0.95, ST_L, sides=6, name="TailTuft")
    ball2(p, (39.0, 8.4, z), 1.5, ST_L, sy=1.1, sides=7, jitter=0.05, name="Mane")
    # spread wings
    outline = [(37.4, 7.0), (36.2, 10.2), (34.8, 12.8), (33.6, 14.5), (33.2, 12.9), (32.2, 13.8), (31.9, 11.9), (30.6, 12.4), (31.2, 10.3),
               (30.4, 9.6), (32.4, 8.4), (35.2, 6.2)]
    inner = [(37.0, 7.2), (35.8, 9.8), (34.4, 11.4), (33.6, 9.4), (35.0, 7.4)]
    for sz in (-1, 1):
        slab(p, outline, 0.55, 'xy', z + sz * 2.35, ST_L, 0.05, name="Wing")
        slab(p, inner, 0.3, 'xy', z + sz * 2.35 + sz * 0.42, ST, 0.05, name="WingInner")
    return p


@part_builder("Portal")
def build_Portal():
    p = dk.Part("Portal")
    zc = -12.0
    bx(p, 50, 66, 0, 1, -15, -9, ST_D, 0.05, name="Base")
    for x0 in (50.5, 62.5):
        o = bx(p, x0, x0 + 3.0, 1, 14.5, -13.8, -10.2, ST, 0.05, name="Pillar")
        courses(o, ST, ST_L, 1.5)
        bx(p, x0 - 0.3, x0 + 3.3, 1, 1.8, -14.1, -9.9, ST_D, name="PillarFoot")
    cy = 14.5
    for k in range(9):
        t0, t1 = pi * k / 9, pi * (k + 1) / 9
        pt = lambda t, r: (58 + r * math.cos(t), cy + r * math.sin(t))
        slab(p, [pt(t0, 4.5), pt(t1, 4.5), pt(t1, 7.5), pt(t0, 7.5)], 3.6, 'xy', zc, ST_X if k % 2 else ST_L, 0.04, name="Voussoir")
    # keystone gem
    slab(p, [(58, 19.0), (58.9, 20.6), (58, 22.0), (57.1, 20.6)], 0.4, 'xy', -10.15, PINK, 0.0, name="Gem")
    # gate: layered stadium shape with swirl arms
    def stadium(s):
        r = 4.5 - s
        pts = [(58 - r, 1.0 + s * 0.3), (58 + r, 1.0 + s * 0.3), (58 + r, cy)]
        pts += [(58 + r * math.cos(t), cy + r * math.sin(t)) for t in [pi * k / 8 for k in range(1, 8)]]
        pts += [(58 - r, cy)]
        return pts
    for k, (s, c) in enumerate(((0.0, PUR_D), (0.7, PUR), (1.5, PUR_L), (2.4, (190, 130, 230)), (3.2, (230, 190, 250)))):
        slab(p, stadium(s), 0.3, 'xy', zc + 0.1 * k, c, 0.02, name="Gate")
    for arm in range(2):
        pts = []
        for k in range(9):
            t = k / 8
            a = arm * pi + 1.9 * pi * t
            r = 0.5 + 3.6 * t
            pts.append((58 + r * math.cos(a), 10.2 + r * 1.05 * math.sin(a)))
        for A, B in zip(pts, pts[1:]):
            rod(p, (A[0], A[1], zc + 0.6), (B[0], B[1], zc + 0.6), 0.2, CY if arm else PINK, sides=4, name="Swirl")
    for x in (51.2, 63.8):
        bx(p, x - 0.7, x + 0.7, 14.6, 16.0, -10.3, -9.5, GOLD, name="Bracket")
    for y in (5.0, 8.0, 11.0):
        for x in (52.0, 64.0):
            dk.box(p, (x, y, -10.15), (0.7, 0.7, 0.15), CY, rot=(0, 0, 45), name="Rune")
    return p


@part_builder("SkyIsle")
def build_SkyIsle():
    p = dk.Part("SkyIsle")
    cx, cz = 10.0, -24.0
    rn = random.Random(5)
    levels = [(0.6, 9.0), (2.0, 10.3), (3.5, 12.0), (5.2, 14.0), (7.4, 16.4), (9.6, 18.2), (10.7, 19.0)]
    rings = []
    for r, y in levels:
        ring = []
        for i in range(9):
            a = 2 * pi * i / 9 + 0.2 * y
            ring.append((cx + r * rn.uniform(0.82, 1.1) * math.cos(a), y, cz + r * rn.uniform(0.82, 1.1) * math.sin(a)))
        rings.append(ring)
    o = loft(p, rings, ST_D, 0.1, name="Rock")
    recolor(o, lambda c, n, i: ST if (int(c[1] * 0.8) + i) % 3 == 0 else None, 0.07)
    lathe(p, (cx, 18.9, cz), [(10.7, 0), (11.0, 0.5), (10.5, 1.0)], 12, GRASS_D, 0.05, name="Turf")
    g = p.objs[-1]
    recolor(g, lambda c, n, i: GRASS if n[1] > 0.9 else None, 0.05)
    # rock chunks floating below and crystal tips
    boulder(p, 2.5, 11.0, -30.5, 1.3, 1.5, ST_D, sides=5, name="Chunk")
    boulder(p, 17.0, 12.2, -18.0, 1.1, 1.3, ST, sides=5, name="Chunk")
    boulder(p, 15.5, 9.6, -29.5, 0.8, 1.0, ST_D, sides=5, name="Chunk")
    for (dx, dz, c) in ((3.4, 2.8, CY), (-3.8, 1.4, PINK), (1.0, -4.0, PUR_L)):
        crystal(p, cx + dx, 9.8, cz + dz, 0.6, 2.4, c, lean=(dx * 0.1, dz * 0.1), sides=5, tip=0.4)
    # little castle: keep, wall, turret
    ktop = 26.6
    o = bx(p, 4.0, 10.0, 19.9, ktop, -29.0, -23.0, ST_L, 0.04, name="Keep")
    courses(o, ST_L, ST_X, 1.3)
    for i in range(4):
        x = 4.0 + i * 1.7
        bx(p, x, x + 0.9, ktop, ktop + 0.9, -29.0, -28.2, ST, name="Merlon")
        bx(p, x, x + 0.9, ktop, ktop + 0.9, -23.8, -23.0, ST, name="Merlon")
    hat(p, 7.0, ktop, -26.0, 4.4, 3.0, 7.4, PUR, band=PUR_D, bend=(0.6, 0.0), sides=8)
    rod(p, (7.6, ktop + 7.2, -26.0), (7.6, 35.0, -26.0), 0.12, GOLD_D, sides=4, name="FlagPole")
    slab(p, [(7.6, 34.9), (9.2, 34.4), (7.6, 33.9)], 0.15, 'xy', -26.0, GOLD, 0.0, name="Flag")
    bx(p, 10.0, 13.4, 19.9, 22.4, -27.4, -25.4, ST, 0.04, name="Wall")
    o = lathe(p, (13.4, 19.9, -26.4), [(1.6, 0), (1.5, 5.0)], 8, ST_L, 0.05, rot0=pi / 8, name="Turret")
    hat(p, 13.4, 24.9, -26.4, 2.0, 1.4, 3.6, PUR_L, band=PUR_D, sides=8)
    door(p, 7.0, 19.9, -23.0, 1.5, 2.6)
    gwin(p, 7.0, 23.2, -23.0, 1.1, 2.0)
    # tree
    rod(p, (15.5, 19.9, -20.0), (15.4, 23.2, -20.0), 0.55, WOOD, sides=5, r2=0.4, name="Trunk")
    for (dx, y, dz, r, c) in ((0.0, 24.6, 0.0, 2.4, GRN_D), (-0.9, 25.4, 0.6, 1.9, GRN), (1.0, 25.0, -0.5, 1.8, GRN_D)):
        ball2(p, (15.5 + dx, y, -20.0 + dz), r, c, sy=0.9, sides=7, jitter=0.07, name="Canopy")
    # waterfall and vines over the front rim
    bx(p, 8.4, 9.6, 14.3, 19.4, -13.5, -13.1, WATER_L, 0.03, name="Fall")
    ball2(p, (9.0, 14.0, -13.3), 0.9, (230, 245, 250), sy=0.7, sides=6, name="Mist")
    for dx in (-5.0, 3.0, 6.0):
        a = 0.0
        rod(p, (cx + dx, 19.0, cz + 9.4), (cx + dx + 0.2, 16.2, cz + 9.3), 0.16, GRN_D, sides=4, name="Vine")
    return p


def ring_pt(c, Rr, a, rx=0.0, rz=0.0):
    M = Matrix.Rotation(math.radians(rz), 3, 'Z') @ Matrix.Rotation(math.radians(rx), 3, 'X')
    v = M @ Vector((Rr * math.cos(a), 0, Rr * math.sin(a)))
    return (c[0] + v.x, c[1] + v.y, c[2] + v.z)


@part_builder("Orrery")
def build_Orrery():
    p = dk.Part("Orrery")
    cx, cz = 80.0, -34.0
    lathe(p, (cx, 0, cz), [(10, 0), (10, 0.5), (9.4, 1.4)], 14, ST_D, 0.05, rot0=pi / 14, name="Plinth")
    lathe(p, (cx, 1.4, cz), [(6.8, 0), (6.5, 1.0)], 14, ST, 0.05, rot0=pi / 14, name="Plinth2")
    for k in range(12):
        a = 2 * pi * k / 12
        dk.cone(p, (cx + 8.4 * math.cos(a), 1.4, cz + 8.4 * math.sin(a)), 0.5, 0.7, GOLD if k % 2 else CY, verts=4, name="Stud")
    lathe(p, (cx, 2.4, cz), [(2.2, 0), (1.5, 0.8), (1.1, 6.0), (1.7, 6.8)], 8, BRASS, 0.05, name="Column")
    c = (cx, 12.4, cz)
    ball2(p, c, 3.0, GOLD, sy=1.0, sides=10, jitter=0.03, name="Sun")
    for k in range(8):
        a = 2 * pi * k / 8
        rod(p, (cx + 2.8 * math.cos(a), 12.4, cz + 2.8 * math.sin(a)), (cx + 4.3 * math.cos(a), 12.4, cz + 4.3 * math.sin(a)), 0.5, GOLD_D, sides=4, r2=0.0, name="Ray")
    # orbit rings, planets, spokes
    torus(p, c, 7.2, 0.22, BRASS, major=20, minor=4, name="Orbit1")
    torus(p, c, 8.3, 0.2, BRASS_D, major=20, minor=4, rx=-12, name="Orbit2")
    pc = ring_pt(c, 7.2, math.atan2(2, 7))
    ball2(p, pc, 1.7, CY, sides=8, jitter=0.04, name="PlanetCyan")
    torus(p, pc, 2.7, 0.1, PINK, major=12, minor=4, rx=20, name="PlanetRing")
    pr = ring_pt(c, 7.2, math.atan2(5, -5))
    ball2(p, pr, 1.3, RED, sides=8, jitter=0.04, name="PlanetRed")
    ball2(p, (pr[0] + 1.9, pr[1] + 1.0, pr[2] + 0.6), 0.5, ST_X, sides=5, name="Moon")
    pp = ring_pt(c, 8.3, math.atan2(-7.4, -3) + 0.0, rx=-12)
    o = ball2(p, pp, 2.0, PINK, sides=9, jitter=0.03, name="PlanetPink")
    recolor(o, lambda cc, n, i: dk.shade(PINK, 1.2) if abs(cc[1] - pp[1]) < 0.7 else None, 0.03)
    for pt in (pc, pr, pp):
        rod(p, (cx, 12.4, cz), pt, 0.17, BRASS, sides=4, name="Spoke")
    # armillary on top
    rod(p, (cx, 15.2, cz), (cx, 22.4, cz), 0.32, BRASS, sides=5, name="Pole")
    torus(p, (cx, 19.6, cz), 3.4, 0.17, GOLD_D, major=12, minor=4, rx=90, name="Arm1")
    torus(p, (cx, 19.6, cz), 3.4, 0.17, GOLD_D, major=12, minor=4, rz=90, name="Arm2")
    torus(p, (cx, 19.6, cz), 3.4, 0.17, GOLD, major=12, minor=4, name="Arm3")
    ball2(p, (cx, 19.6, cz), 0.8, CY, sides=6, name="Core")
    spark(p, cx, 24.6, cz, 1.5, GOLD)
    return p
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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_WizardTower.json"))
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
        allm += meshes
        dk.hide(meshes)
    if not ONLY:
        dk.hide(allm, False)
        spot = mirror_spot(bp["Shiba"])
        view(allm, "stage_WizardTower_34.png", shiba=spot, az=205, el=40, size=(1800, 1000), zoom=1.55)
        view(allm, "stage_WizardTower_top.png", shiba=spot, top=True, size=(1800, 1000))
        stack_images(out, "stage_WizardTower_34.png", "stage_WizardTower_top.png", "stage_WizardTower.png")
    for s in stats:
        print("STAT %-12s meshes=%d tris=%d" % s)


main()
