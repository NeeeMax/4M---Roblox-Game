"""Pirate Ship decor models (theme PirateShip, bay 8): builds the 15 decor parts around the Pirate Shiba.

Run:  blender --background --factory-startup --python build_PirateShip.py -- <absolute outdir>
Writes into <outdir>: Decor_PirateShip_<PartId>.fbx, preview_<PartId>.png per part, stage_PirateShip.png (3/4 view and top view
stacked) plus stage_PirateShip_34.png / stage_PirateShip_top.png.
Every model is built in the stage frame (see decorkit.py) and fitted to the union box of its blueprint pieces before export.
Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures, no neon. One palette for all parts.
Previews are rendered from the road side (+z) AFTER the export mirror, so they show the models as they appear in the game.
Env: PS_ONLY=Hull,Sign builds only those parts (no stage render). PS_COUNT=1 prints triangles per object name.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "PirateShip"
R = random.Random(8)
pi = math.pi
ONLY = set(os.environ.get("PS_ONLY", "").split(",")) - {""}
DBG = os.environ.get("PS_DBG")          # optional folder for extra debug renders (not a deliverable)

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
HULL = (132, 86, 50); HULL_D = (98, 62, 36); HULL_L = (170, 114, 66)
DECK = (178, 126, 72); DECK_D = (146, 100, 56); DECK_L = (204, 150, 92)
BOARD = (74, 48, 34)
CREAM = (250, 242, 218); CREAM_D = (224, 212, 180)
RED = (176, 42, 42); RED_D = (132, 30, 34)
GOLD = (255, 200, 40); GOLD_D = (204, 150, 30)
IRON = (34, 34, 40); IRON_L = (84, 86, 98); STEEL_C = (58, 60, 72)
STONE = (122, 122, 132); STONE_L = (156, 156, 166); STONE_D = (88, 88, 98)
BONE = (236, 230, 214); BONE_D = (200, 192, 172)
SAND = (236, 214, 156); SAND_L = (248, 230, 176); SAND_D = (204, 180, 122); WET = (200, 180, 128)
DIRT = (190, 164, 114)
SEA = (40, 130, 200); SEA_L = (96, 190, 226); SEA_D = (26, 98, 168); FOAM = (240, 248, 250)
GRASS = (92, 152, 72); GRASS_D = (66, 118, 58)
LEAF = (60, 150, 70); LEAF_L = (96, 184, 90); LEAF_D = (40, 110, 58)
TRUNK = (154, 112, 70); TRUNK_D = (100, 70, 42)
ORANGE = (232, 120, 40); YELLOW = (255, 225, 90)
PURPLE = (120, 56, 140); PURPLE_L = (162, 92, 182); PURPLE_D = (84, 38, 104); PINK = (236, 150, 190)
AMBER = (232, 172, 72)


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


def recolor_v(o, fn):
    """Smooth per-corner colours from the vertex position (stage axes): fn(pos) -> colour (0-255)."""
    me = o.data
    attr = me.color_attributes.get("Col")
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            w = mw @ me.vertices[me.loops[li].vertex_index].co
            attr.data[li].color = (*dk.srgb(*fn((w.x, w.z, w.y))), 1.0)


def drop_faces(o, pred):
    """Deletes faces of o whose (stage-axes) normal satisfies pred(n)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bad = [f for f in bm.faces if pred((f.normal.x, f.normal.z, f.normal.y))]
    bmesh.ops.delete(bm, geom=bad, context='FACES')
    bm.to_mesh(o.data)
    bm.free()


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _m(axis, u, v, h, bx, by, bz, dx, dz):
    if axis == 'y':
        return (bx + u + dx, by + h, bz + v + dz)
    if axis == 'z':
        return (bx + u + dx, by + v, bz + h + dz)
    return (bx + h + dz, by + u, bz + v + dx)          # 'x'


def lathe(part, base, profile, sides, color, jitter=0.0, axis="y", rot0=0.0, name="Lathe", cap0=True):
    """Solid of revolution. profile = [(radius, height[, dx, dz])] bottom to top (radius 0 = apex), base = stage point."""
    pts, rings = [], []
    bx, by, bz = base
    for e in profile:
        r, h = e[0], e[1]
        dx = e[2] if len(e) > 2 else 0.0
        dz = e[3] if len(e) > 3 else 0.0
        if r <= 1e-6:
            pts.append(_m(axis, 0, 0, h, bx, by, bz, dx, dz))
            rings.append([len(pts) - 1])
        else:
            idx = []
            for i in range(sides):
                a = 2 * pi * i / sides + rot0
                pts.append(_m(axis, r * math.cos(a), r * math.sin(a), h, bx, by, bz, dx, dz))
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


def blob(part, c, r, color, sy=1.0, sx=1.0, sz=1.0, sides=6, jitter=0.0, name="Blob"):
    """Cheap low-poly ball (2 rings), centre c, radius r, stretched in y/x/z."""
    prof = [(0, 0), (r * 0.9, r * sy * 0.55), (r, r * sy * 1.1), (r * 0.9, r * sy * 1.65), (0, r * sy * 2)]
    o = lathe(part, (c[0], c[1] - r * sy, c[2]), prof, sides, color, jitter, name=name)
    if sx != 1.0 or sz != 1.0:
        me = o.data
        for v in me.vertices:
            v.co.x = (v.co.x - c[0]) * sx + c[0]
            v.co.y = (v.co.y - c[2]) * sz + c[2]
        me.update()
    return o


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


def tube(part, path, radii, sides, color, jitter=0.0, name="Tube"):
    """Tube along a polyline of stage points; ring radii per point (0 = apex); rings are perpendicular to the path."""
    rings = []
    n = len(path)
    for i, pt in enumerate(path):
        p = Vector(pt)
        if radii[i] <= 1e-6:
            rings.append([tuple(p)])
            continue
        t = (Vector(path[min(i + 1, n - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        v = t.cross(u).normalized()
        ring = [tuple(p + (u * math.cos(2 * pi * k / sides) + v * math.sin(2 * pi * k / sides)) * radii[i]) for k in range(sides)]
        rings.append(ring)
    return loft(part, rings, color, jitter, name=name)


def bar(part, A, B, w, color, h=None, jitter=0.0, name="Bar", up=(0, 1, 0)):
    """Square bar from stage point A to B; w = width (perpendicular to the bar and `up`), h = thickness in the other direction."""
    A = Vector(A)
    B = Vector(B)
    d = (B - A).normalized()
    ref = Vector(up) if abs(d.dot(Vector(up))) < 0.95 else Vector((1, 0, 0))
    u = d.cross(ref).normalized() * w / 2
    v = d.cross(u).normalized() * (h if h else w) / 2
    pts = [A - u - v, A + u - v, A + u + v, A - u + v, B - u - v, B + u - v, B + u + v, B - u + v]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _obj(part, name, [tuple(p) for p in pts], faces, color, jitter)


def tetra(part, p0, p1, p2, p3, color, jitter=0.0, name="Tooth"):
    return _obj(part, name, [p0, p1, p2, p3], [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], color, jitter)


def post(part, x, z, y0, y1, r, color, sides=6, top_r=None, jitter=0.0, name="Post"):
    return dk.cyl(part, (x, (y0 + y1) / 2, z), r, y1 - y0, color, verts=sides, top_radius=top_r, jitter=jitter, name=name)


def strips(part, center, size, color, n, axis, jitter=0.06, name="Strips"):
    """Box cut into n slices perpendicular to `axis` ('x','y','z') so the faces read as boards."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size[0], size[2], size[1]), verts=bm.verts)
    ax = {'x': 0, 'y': 2, 'z': 1}[axis]
    L = size['xyz'.index(axis)]
    for k in range(1, n):
        co = [0, 0, 0]
        no = [0, 0, 0]
        co[ax] = -L / 2 + L * k / n
        no[ax] = 1
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)
    return dk._object(part, name, bm, dk.S(*center), (0, 0, 0), color, jitter)


def barrel(p, x, y0, z, r, h, color=HULL, band=IRON_L, sides=8, name="Barrel"):
    """Staved barrel with two metal hoops."""
    o = lathe(p, (x, y0, z), [(r * 0.78, 0), (r, h * 0.3), (r, h * 0.7), (r * 0.78, h)], sides, color, 0.06, name=name)
    for t in (0.2, 0.8):
        rr = r * (0.9 + 0.1 * math.sin(pi * t)) + 0.04
        lathe(p, (x, y0 + h * t - h * 0.04, z), [(rr, 0), (rr, h * 0.08)], sides, band, 0.0, name=name + "Hoop", cap0=False)
    return o


def crate(p, x, y0, z, s, color=DECK, name="Crate", rot=0.0):
    """Wooden crate with darker corner battens."""
    dk.box(p, (x, y0 + s / 2, z), (s, s, s), color, rot=(0, rot, 0), jitter=0.06, name=name)
    t = s * 0.12
    for sx in (-1, 1):
        for sz in (-1, 1):
            a = math.radians(rot)
            ox, oz = sx * s * 0.47, sz * s * 0.47
            cx = x + ox * math.cos(a) + oz * math.sin(a)
            cz = z - ox * math.sin(a) + oz * math.cos(a)
            dk.box(p, (cx, y0 + s / 2, cz), (t, s * 1.02, t), HULL_D, rot=(0, rot, 0), name=name + "Batten")


def pennant_loft(p, x0, y, z, length, h, wave, color, name="Pennant"):
    """Swallow-less pennant that tapers to a point along +x with a little wave in z."""
    rings = []
    n = 5
    for i in range(n):
        t = i / (n - 1)
        x = x0 + length * t
        hh = h * (1 - t * 0.9) / 2
        zz = z + wave * math.sin(t * pi * 1.4) * t
        rings.append([(x, y + hh, zz - 0.05), (x, y - hh, zz - 0.05), (x, y - hh, zz + 0.05), (x, y + hh, zz + 0.05)])
    return loft(p, rings, color, 0.02, name=name)


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
    print("FIT %-10s scale x%.3f y%.3f z%.3f  model x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]  box x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"
          % (part.id, sc[0], sc[1], sc[2], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], tlo[0], thi[0], tlo[1], thi[1], tlo[2], thi[2]))
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


def add_blade(p, base, yaw, length, width, rise, droop, color, segs=4, thick=0.28, jitter=0.07, name="Frond", notch=False):
    """A palm frond / leaf: arched spine, widest in the first half, ridge on top, tip point."""
    a = math.radians(yaw)
    dx, dz = math.cos(a), -math.sin(a) * 0.9
    px, pz = -dz, dx
    rings = []
    for i in range(segs + 1):
        t = i / segs
        r = length * t
        cx, cz = base[0] + dx * r, base[2] + dz * r
        cy = base[1] + rise * t - droop * t * t
        if i == segs:
            rings.append([(cx, cy - 0.05, cz)])
            break
        w = width * (0.25 + 0.75 * math.sin(pi * min(1.0, 0.12 + 0.88 * t ** 0.8)))
        if i % 2 == 1 and notch:
            w *= 0.66
        s = 0.24 * w
        rings.append([(cx - px * w / 2, cy - s, cz - pz * w / 2), (cx, cy + thick / 2, cz), (cx + px * w / 2, cy - s, cz + pz * w / 2)])
    return loft(p, rings, color, jitter, name=name)


# ---- PART 1: Floor -----------------------------------------------------------------------------------------------
LAG_C = (-68.5, -33.0)
LAG_R = (21.5, 31.0)


def lagoon_pt(a, grow=0.0):
    c, s = math.cos(a), math.sin(a)
    e = 0.5
    wob = 1.0 + 0.035 * math.sin(7 * a + 0.6) + 0.02 * math.sin(13 * a)
    x = LAG_C[0] + (LAG_R[0] + grow) * wob * math.copysign(abs(c) ** e, c)
    z = LAG_C[1] + (LAG_R[1] + grow) * wob * math.copysign(abs(s) ** e, s)
    return max(-94.6, x), max(-64.6, min(64.6, z))


def lagoon_surface(p, y, grow, fracs, color_fn, n=32, name="Lagoon"):
    """Concentric rings + centre fan (open, facing up), vertex-coloured by color_fn(x, z)."""
    pts, faces, rings = [], [], []
    for f in fracs:
        ring = []
        for k in range(n):
            x, z = lagoon_pt(2 * pi * k / n, grow)
            pts.append((LAG_C[0] + (x - LAG_C[0]) * f, y, LAG_C[1] + (z - LAG_C[1]) * f))
            ring.append(len(pts) - 1)
        rings.append(ring)
    pts.append((LAG_C[0], y, LAG_C[1]))
    c = len(pts) - 1
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((a[i], a[j], b[j], b[i]))
    for i in range(n):
        faces.append((rings[-1][i], rings[-1][(i + 1) % n], c))
    o = _obj(p, name, pts, faces, SEA, 0.0, closed=False, up=True)
    recolor_v(o, lambda q: color_fn(q[0], q[2]))
    return o


def grid(p, x0, x1, z0, z1, nx, nz, y, amp, color, jitter, name="Grid"):
    pts, faces = [], []
    for j in range(nz + 1):
        for i in range(nx + 1):
            edge = i in (0, nx) or j in (0, nz)
            h = 0.0 if edge else (R.random() - 0.5) * amp
            pts.append((x0 + (x1 - x0) * i / nx, y + h, z0 + (z1 - z0) * j / nz))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return _obj(p, name, pts, faces, color, jitter, closed=False, up=True)


def lens(cx, cz, hl, hw, along='z', bend=0.0):
    if along == 'z':
        return [(cx + bend, cz - hl), (cx + hw, cz - hl / 3), (cx + hw - bend, cz + hl / 3), (cx - bend, cz + hl),
                (cx - hw - bend, cz + hl / 3), (cx - hw + bend, cz - hl / 3)]
    return [(cx - hl, cz), (cx - hl / 3, cz + hw), (cx + hl / 3, cz + hw), (cx + hl, cz), (cx + hl / 3, cz - hw), (cx - hl / 3, cz - hw)]


def star(cx, cz, ro, ri, n=5, rot=0.0):
    pts = []
    for i in range(2 * n):
        a = rot + pi * i / n
        rr = ro if i % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


def in_lagoon(x, z, grow=0.0):
    nx = (x - LAG_C[0]) / (LAG_R[0] + grow)
    nz = (z - LAG_C[1]) / (LAG_R[1] + grow)
    return abs(nx) ** 4 + abs(nz) ** 4 < 1.0


def blob_poly(cx, cz, rx, rz, n=9, jit=0.12, rot=0.0):
    return [(cx + rx * math.cos(rot + 2 * pi * k / n) * (1 + R.uniform(-jit, jit)),
             cz + rz * math.sin(rot + 2 * pi * k / n) * (1 + R.uniform(-jit, jit))) for k in range(n)]


def build_Floor():
    p = dk.Part("Floor")
    dk.box(p, (0, 0.14, 0), (190, 0.28, 130), SAND_D, name="SandBase")
    top = grid(p, -95, 95, -65, 65, 19, 13, 0.3, 0.0, SAND, 0.0, name="SandTop")

    def sand_col(c):
        n1 = math.sin(c[0] * 0.05 + c[2] * 0.08) * math.sin(c[2] * 0.07 - c[0] * 0.045 + 1.3)
        n2 = math.sin(c[0] * 0.11 - c[2] * 0.04 + 1.0)
        col = mix(mix(SAND, SAND_L, 0.4 + 0.4 * n1), SAND_D, 0.04 + 0.04 * n2)
        # wetter sand towards the lagoon, dryer dunes far away
        d = ((c[0] - LAG_C[0]) / (LAG_R[0] + 14)) ** 4 + ((c[2] - LAG_C[1]) / (LAG_R[1] + 14)) ** 4
        return mix(col, WET, 1.0 - d) if d < 1.0 else col
    recolor_v(top, sand_col)
    # wet shore rim, the lagoon with a deep centre, a foam line along the shore
    lagoon_surface(p, 0.36, 2.6, (1.0, 0.7), lambda x, z: mix(WET, SAND_D, 0.35 + 0.2 * math.sin(x * 0.3 + z * 0.2)), name="WetRim")
    lagoon_surface(p, 0.46, 0.0, (1.0, 0.7, 0.4),
                   lambda x, z: mix(SEA_L, SEA_D, 1.0 - min(1.0, (1.0 - (((x - LAG_C[0]) / LAG_R[0]) ** 4 + ((z - LAG_C[1]) / LAG_R[1]) ** 4)) * 2.2)),
                   name="Lagoon")
    n = 32
    pts, faces = [], []
    for k in range(n):
        a = 2 * pi * k / n
        xo, zo = lagoon_pt(a, 0.0 if k % 2 else 0.9)
        xi, zi = lagoon_pt(a, -1.3)
        pts += [(xo, 0.49, zo), (xi, 0.49, zi)]
    for k in range(n):
        j = (k + 1) % n
        faces.append((2 * k, 2 * j, 2 * j + 1, 2 * k + 1))
    _obj(p, "Foam", pts, faces, FOAM, 0.02, closed=False, up=True)
    for x0, ph in ((-86.0, 0.0), (-78.0, 1.3), (-58.0, 2.1), (-50.0, 0.7)):
        for z0 in (-56.0, -30.0, -8.0):
            cen = [(x0 + 0.9 * math.sin(z * 0.5 + ph), z) for z in range(int(z0) - 4, int(z0) + 5, 4)]
            if all(in_lagoon(x, z, -3) for x, z in cen):
                flat(p, [(x - 0.2, z) for x, z in cen] + [(x + 0.2, z) for x, z in reversed(cen)], 0.495, SEA_L, 0.02, name="WaveLine")
    # patches: tavern yard, treasure beach, grass with tufts
    def soft_patch(cx, cz, rx, rz, y, color, n=12, name="Patch"):
        """Disc that fades into the sand towards its rim (centre fan + one ring + rim ring)."""
        pts, faces, rings = [], [], []
        for f in (1.0, 0.6):
            ring = []
            for k in range(n):
                a = 2 * pi * k / n + 0.3
                j = 1.0 + (R.uniform(-0.08, 0.08) if f == 1.0 else 0.0)
                pts.append((cx + rx * f * j * math.cos(a), y, cz + rz * f * j * math.sin(a)))
                ring.append(len(pts) - 1)
            rings.append(ring)
        pts.append((cx, y, cz))
        for i in range(n):
            j = (i + 1) % n
            faces.append((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
            faces.append((rings[1][i], rings[1][j], len(pts) - 1))
        o = _obj(p, name, pts, faces, color, 0.0, closed=False, up=True)

        def fade(q):
            d = math.sqrt(((q[0] - cx) / rx) ** 2 + ((q[2] - cz) / rz) ** 2)
            return mix(sand_col(q), color, (1.15 - d) / 0.45)
        recolor_v(o, fade)
    soft_patch(38, -43, 18, 16, 0.325, DIRT, 14, "TavernYard")
    soft_patch(76, -8, 14, 12, 0.325, mix(WET, GOLD, 0.15), 12, "TreasureBeach")
    for (cx, cz, rx, rz) in [(30, 56, 8.5, 5.5), (-70, 30, 9.5, 6.5), (60, 58, 7.5, 4.5), (6, -6, 5, 3.5), (-8, 36, 6, 4)]:
        soft_patch(cx, cz, rx, rz, 0.34, GRASS, 9, "GrassPatch")
        for _ in range(3):
            tx, tz = cx + R.uniform(-rx * 0.6, rx * 0.6), cz + R.uniform(-rz * 0.6, rz * 0.6)
            flat(p, star(tx, tz, R.uniform(0.7, 1.1), 0.25, 4, R.uniform(0, 1.5)), 0.355, GRASS_D, 0.05, name="Tuft")
    # treasure trail: dashes from the pier to the red X at the treasure beach
    ctrl = [(-31, -41), (-14, -46), (6, -38), (26, -22), (46, -12), (62, -4), (70.4, -1.4)]
    samples = []
    for (a, b) in zip(ctrl, ctrl[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(ln // 3.4)):
            t = k * 3.4 / ln
            samples.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (b[0] - a[0]) / ln, (b[1] - a[1]) / ln))
    for ((x, z), dx, dz) in samples:
        px, pz = -dz * 0.3, dx * 0.3
        flat(p, [(x - dx * 0.8 - px, z - dz * 0.8 - pz), (x + dx * 0.8 - px, z + dz * 0.8 - pz), (x + dx * 0.8 + px, z + dz * 0.8 + pz),
                 (x - dx * 0.8 + px, z - dz * 0.8 + pz)], 0.345, (176, 120, 72), 0.03, name="TrailDash")
    # seaweed and sparkles in the lagoon
    for _ in range(6):
        x, z = R.uniform(-88, -49), R.uniform(-62, -4)
        if in_lagoon(x, z, -5):
            flat(p, lens(x, z, R.uniform(1.2, 2.2), R.uniform(0.3, 0.45), bend=R.uniform(-0.3, 0.3)), 0.47, (46, 120, 84), 0.04, name="Seaweed")
    for _ in range(9):
        x, z = R.uniform(-88, -49), R.uniform(-62, -4)
        if in_lagoon(x, z, -4):
            flat(p, star(x, z, 0.7, 0.18, 4, R.uniform(0, 1)), 0.495, FOAM, 0.0, name="Sparkle")
    # dune streaks, ripples, footprints, shells, starfish, pebbles
    for _ in range(9):
        x, z = R.uniform(-80, 80), R.uniform(-50, 50)
        if not in_lagoon(x, z, 4):
            flat(p, lens(x, z, R.uniform(7, 12), R.uniform(0.9, 1.5), bend=R.uniform(-1, 1)), 0.335, mix(SAND, SAND_L, 0.8), 0.02, name="DuneStreak")
    for _ in range(8):
        x, z = R.uniform(-80, 80), R.uniform(-50, 50)
        if not in_lagoon(x, z, 4):
            flat(p, lens(x, z, R.uniform(3, 6), R.uniform(0.3, 0.45), bend=R.uniform(-0.3, 0.3)), 0.34, dk.shade(SAND, 0.9), 0.03, name="Ripple")
    for k in range(14):
        x = 8 + k * 5.0
        z = 54 + math.sin(k * 0.5) * 3 + (0.9 if k % 2 else -0.9)
        flat(p, lens(x, z, 0.8, 0.38, along='x'), 0.345, dk.shade(SAND, 0.8), 0.0, name="Print")
    for (x, z, rot) in [(-30, 40, 0.3), (60, -26, 1.1), (-24, -62, 0.7), (40, 24, 0.0)]:
        flat(p, star(x, z, 2.0, 0.8, 5, rot), 0.36, (236, 108, 70), 0.04, name="Starfish")
    for (x, z, rot) in [(-40, 14, 0.4), (20, -18, 2.0), (70, 44, 1.2), (-14, 56, 3.0), (52, -6, 0.2)]:
        fan = [(x, z)] + [(x + 1.1 * math.cos(rot + pi * k / 4), z + 1.1 * math.sin(rot + pi * k / 4)) for k in range(5)]
        flat(p, fan, 0.36, (250, 224, 224), 0.03, name="Shell")
    for (x, z) in [(-20, -48), (20, 10), (84, -40)]:
        lathe(p, (x, 0.3, z), [(0, 0.0), (0.7, 0.08), (0.5, 0.2), (0, 0.24)], 5, STONE_L, 0.06, rot0=R.random(), name="Pebble", cap0=False)
    return p


# ---- PART 2: Hull ------------------------------------------------------------------------------------------------
CX = -62.0
# stations along the ship: z, half width, keel y, deck y
STA = [(-6.0, 8.6, 1.4, 7.6), (-10.0, 9.5, 0.7, 7.3), (-18.0, 9.8, 0.15, 7.0), (-28.0, 9.8, 0.0, 7.0), (-38.0, 9.8, 0.0, 7.0),
       (-45.0, 9.5, 0.25, 7.0), (-50.5, 8.2, 0.7, 7.3), (-55.0, 5.8, 1.6, 7.7), (-58.6, 3.4, 2.8, 8.1), (-61.0, 1.6, 4.2, 8.5),
       (-62.0, 0.6, 5.4, 8.8)]
PROF = [(1.0, 0.97), (0.86, 1.02), (0.72, 1.02), (0.5, 0.97), (0.25, 0.82), (0.0, 0.4)]


def hw_at(z):
    for a, b in zip(STA, STA[1:]):
        if b[0] <= z <= a[0]:
            t = (a[0] - z) / (a[0] - b[0])
            return a[1] + (b[1] - a[1]) * t
    return STA[0][1] if z > STA[0][0] else STA[-1][1]


def hull_ring(z, hw, keel, top):
    left = [(CX - hw * xf, keel + (top - keel) * t, z) for t, xf in PROF]
    right = [(CX + hw * xf, keel + (top - keel) * t, z) for t, xf in reversed(PROF)]
    return left + right


def hull_col(c, n, k):
    i = k % 12
    return {0: HULL_L, 1: GOLD_D, 2: HULL, 3: RED_D, 4: HULL_D, 5: HULL_D, 6: HULL_D, 7: RED_D, 8: HULL, 9: GOLD_D, 10: HULL_L, 11: DECK}[i]


def side_poly(zs, out_f, thick, sign):
    """Outline polygon (x, z) of a bulwark along the hull side: outer edge follows the hull, `thick` wide."""
    outer = [(CX + sign * hw_at(z) * out_f, z) for z in zs]
    inner = [(CX + sign * (hw_at(z) * out_f - thick), z) for z in zs]
    return outer + inner[::-1]


def build_Hull():
    p = dk.Part("Hull")
    rings = [hull_ring(z, hw, k, t) for (z, hw, k, t) in STA]
    h = loft(p, rings, HULL, 0.07, name="HullLoft")
    nfaces = 12 * (len(STA) - 1)
    recolor(h, lambda c, n, k: hull_col(c, n, k) if k < nfaces else HULL, 0.07)
    # deck
    zs = [-6.5, -12, -18, -28, -38, -45, -50.5, -55, -58.4]
    outline = [(CX - hw_at(z) * 0.93, z) for z in zs] + [(CX + hw_at(z) * 0.93, z) for z in zs[::-1]]
    deck = slab(p, outline, 0.4, 'xz', 7.0, DECK, 0.06, name="Deck")
    drop_faces(deck, lambda n: n[1] < -0.99)
    for i in range(-5, 6):
        x = CX + i * 1.6
        flat(p, [(x - 0.05, -16.4), (x + 0.05, -16.4), (x + 0.05, -50.0), (x - 0.05, -50.0)], 7.405, DECK_D, 0.04, name="PlankLine")
    # bulwarks along both sides, gold rail on top
    zb = [-16.4, -22, -28, -34, -40, -46, -50.0]
    for sign in (-1, 1):
        bw = slab(p, side_poly(zb, 0.97, 0.6, sign), 1.8, 'xz', 7.0, HULL_D, 0.05, name="Bulwark")
        drop_faces(bw, lambda n: n[1] < -0.99)
        recolor(bw, lambda c, n, k: GOLD_D if n[1] > 0.9 else None, 0.04)
    # stern castle with the windows
    cas = frustum(p, CX, -11.2, 7.4, 12.0, 19.0, 9.8, 17.4, 9.8, HULL, 0.07, name="Castle")
    recolor(cas, lambda c, n, k: HULL_L if n[1] > 0.9 else None, 0.05)
    slab(p, [(CX - 10, -16.4), (CX + 10, -16.4), (CX + 10, -6.0), (CX - 10, -6.0)], 0.4, 'xz', 12.0, DECK, 0.05, name="AftDeck")
    for x0, x1, z0, z1 in [(-10, 10, -16.4, -16.0), (-10, -9.6, -16.4, -6.0), (9.6, 10, -16.4, -6.0), (-10, 10, -6.4, -6.0)]:
        dk.box(p, (CX + (x0 + x1) / 2, 12.75, (z0 + z1) / 2), (x1 - x0, 0.7, z1 - z0), HULL_D, jitter=0.04, name="AftRail")
    for k in range(5):
        x = CX + (k - 2) * 3.4
        dk.box(p, (x, 9.6, -6.18), (2.5, 2.7, 0.24), GOLD_D, name="WindowFrame")
        dk.box(p, (x, 9.6, -6.06), (1.8, 2.0, 0.2), AMBER, name="WindowGlass")
    dk.box(p, (CX, 7.85, -6.15), (17, 0.5, 0.3), GOLD_D, name="Balcony")
    dk.box(p, (CX, 11.6, -6.15), (17.4, 0.5, 0.3), GOLD_D, name="CastleTrim")
    # stairs up to the aft deck from the main deck
    for side in (-1, 1):
        for s in range(5):
            top = 12.0 - 0.95 * s
            dk.box(p, (CX + side * 6.8, 7.4 + (top - 7.4) / 2, -16.6 - 0.5 - s * 1.0), (3.0, top - 7.4, 1.0), DECK_L, jitter=0.05, name="Stair")
    # forecastle
    fc = [(-7.0, -49.8), (7.0, -49.8), (6.2, -54.0), (4.2, -57.6), (-4.2, -57.6), (-6.2, -54.0)]
    f1 = slab(p, [(CX + x, z) for x, z in fc], 3.6, 'xz', 7.4, HULL, 0.06, name="Forecastle")
    drop_faces(f1, lambda n: n[1] < -0.99)
    topf = [(-7.5, -49.5), (7.5, -49.5), (6.6, -54.0), (4.6, -58.2), (-4.6, -58.2), (-6.6, -54.0)]
    f2 = slab(p, [(CX + x, z) for x, z in topf], 0.4, 'xz', 11.0, DECK, 0.05, name="ForeDeck")
    drop_faces(f2, lambda n: n[1] < -0.99)
    # gunports on both sides
    for sign in (-1, 1):
        for z in (-22.0, -28.0, -34.0, -40.0):
            x = CX + sign * (hw_at(z) * 0.975 + 0.04)
            dk.box(p, (x, 3.9, z), (0.22, 1.3, 1.5), IRON, name="Gunport")
    # deck furniture: hatch, capstan, mast collars
    dk.box(p, (CX, 7.55, -24), (3.6, 0.3, 3.6), HULL_D, name="Hatch")
    dk.box(p, (CX, 7.75, -24), (3.4, 0.15, 0.25), DECK_L, name="Grate")
    dk.box(p, (CX, 7.75, -24), (0.25, 0.15, 3.4), DECK_L, name="Grate")
    dk.cyl(p, (CX, 7.9, -43.5), 0.9, 1.0, HULL_L, verts=8, name="Capstan")
    for a in (0, 90):
        dk.box(p, (CX, 8.2, -43.5), (2.6, 0.2, 0.2), DECK_D, rot=(0, a, 0), name="Spoke")
    for z, y in ((-32, 7.4), (-50, 7.4)):
        dk.cyl(p, (CX, y + 0.25, z), 1.3, 0.5, HULL_D, verts=6, name="MastStep")
    # two barrels beside the stairs
    barrel(p, CX + 3.6, 7.4, -19.4, 0.85, 1.7, sides=6, name="DeckBarrel")
    barrel(p, CX - 3.9, 7.4, -19.0, 0.8, 1.5, sides=6, name="DeckBarrel")
    # stern lanterns on the aft deck corners
    for s in (-1, 1):
        lx = CX + s * 8.5
        dk.cyl(p, (lx, 13.75, -7.5), 0.25, 1.3, GOLD_D, verts=5, name="LanternPost")
        dk.box(p, (lx, 14.55, -7.5), (0.95, 1.0, 0.95), AMBER, name="Lantern")
        dk.cone(p, (lx, 15.05, -7.5), 0.8, 0.45, GOLD_D, verts=4, name="LanternRoof")
    # foam collar where the hull meets the water
    fz = [-6.0, -10.0, -18.0, -28.0, -38.0, -45.0, -50.5, -55.0, -58.6, -61.0]
    inner = lambda z, s: CX + s * (hw_at(z) * 0.52)
    for s in (-1, 1):
        for a, b in zip(fz, fz[1:]):
            ya = 0.5
            flat(p, [(inner(a, s), a), (inner(b, s), b), (inner(b, s) + s * 1.5, b + 0.4), (inner(a, s) + s * 1.7, a)], ya, FOAM, 0.02, name="HullFoam")
    flat(p, [(CX - hw_at(-6.0) * 0.52, -6.0), (CX + hw_at(-6.0) * 0.52, -6.0), (CX + hw_at(-6.0) * 0.52 + 1.2, -7.4), (CX - hw_at(-6.0) * 0.52 - 1.2, -7.4)], 0.5, FOAM, 0.02, name="HullFoam")
    # ship's wheel on the aft deck (rim of 8 bars, spokes, pedestal)
    wx, wy, wz, wr = CX, 14.0, -11.6, 1.25
    dk.box(p, (wx, 13.1, wz), (0.7, 1.4, 0.7), HULL_D, name="WheelStand")
    for k in range(8):
        a0, a1 = k * pi / 4, (k + 1) * pi / 4
        bar(p, (wx + wr * math.cos(a0), wy + wr * math.sin(a0), wz), (wx + wr * math.cos(a1), wy + wr * math.sin(a1), wz), 0.36, DECK_L, h=0.26, name="WheelRim")
    bar(p, (wx - wr * 1.18, wy, wz), (wx + wr * 1.18, wy, wz), 0.26, HULL_L, h=0.2, name="WheelSpoke")
    bar(p, (wx, wy - wr * 1.18, wz), (wx, wy + wr * 1.18, wz), 0.26, HULL_L, h=0.2, name="WheelSpoke")
    dk.cyl(p, (wx, wy, wz), 0.36, 0.5, GOLD, axis='z', verts=6, name="WheelHub")
    # rail around the forecastle deck
    topf2 = [(-7.5, -49.5), (7.5, -49.5), (6.6, -54.0), (4.6, -58.2), (-4.6, -58.2), (-6.6, -54.0)]
    for (ax_, az_), (bx_, bz_) in zip(topf2[1:], topf2[2:] + topf2[:1]):
        bar(p, (CX + ax_, 11.7, az_), (CX + bx_, 11.7, bz_), 0.3, HULL_D, h=0.6, name="ForeRail")
    # figurehead: a golden dog bust at the stem
    dk.box(p, (CX, 6.3, -60.3), (2.0, 1.9, 2.0), GOLD, jitter=0.03, name="FigHead")
    dk.box(p, (CX, 5.9, -61.3), (1.1, 0.9, 1.2), GOLD_D, name="FigSnout")
    dk.box(p, (CX, 6.25, -61.95), (0.35, 0.3, 0.2), IRON, name="FigNose")
    for s in (-1, 1):
        dk.box(p, (s * 0.55 + CX, 6.7, -61.3), (0.3, 0.3, 0.2), IRON, name="FigEye")
        tetra(p, (CX + s * 1.0, 7.1, -60.9), (CX + s * 0.35, 7.1, -61.0), (CX + s * 0.75, 8.3, -60.6), (CX + s * 0.7, 7.1, -59.8), GOLD_D, name="FigEar")
    # skull and crossbones on the transom, under the windows
    dk.ball(p, (CX, 4.7, -5.95), 1.3, BONE, scale=(1.0, 0.95, 0.12), subdiv=1, name="SternSkull")
    dk.box(p, (CX, 3.55, -5.95), (1.3, 0.8, 0.2), BONE, name="SternJaw")
    for s in (-0.5, 0.5):
        dk.box(p, (CX + s, 4.85, -5.84), (0.5, 0.5, 0.12), IRON, name="SternEye")
    for a in (-1, 1):
        bar(p, (CX - a * 3.0, 2.7, -5.95), (CX + a * 3.0, 6.0, -5.95), 0.2, BONE_D, h=0.5, name="SternBone")
    return p


# ---- PART 3: Sign ------------------------------------------------------------------------------------------------
# 4 x 5 pixel font, rows from the top; horizontal runs are merged into boxes (and equal runs of neighbouring rows into one)
FONT = {"G": [".XXX", "X...", "X.XX", "X..X", ".XXX"],
        "E": ["XXXX", "X...", "XXX.", "X...", "XXXX"],
        "T": ["XXXX", ".XX.", ".XX.", ".XX.", ".XX."],
        "B": ["XXX.", "X..X", "XXX.", "X..X", "XXX."],
        "O": [".XX.", "X..X", "X..X", "X..X", ".XX."],
        "N": ["X..X", "XX.X", "X.XX", "X..X", "X..X"],
        "K": ["X..X", "X.X.", "XX..", "X.X.", "X..X"],
        "D": ["XXX.", "X..X", "X..X", "X..X", "XXX."]}


def glyph_rects(rows):
    """[(x0, width, y0_from_bottom, height)] in cells."""
    runs = []
    n = len(rows)
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == "X":
                c0 = c
                while c < len(row) and row[c] == "X":
                    c += 1
                runs.append([c0, c - c0, n - 1 - r, 1])
            else:
                c += 1
    merged = []
    for run in runs:
        for m in merged:
            if m[0] == run[0] and m[1] == run[1] and m[2] + m[3] == run[2]:
                m[3] += 1
                break
        else:
            merged.append(run)
    return merged


def letter(p, ch, x_left, y0, z, cw, chh, color, depth=0.3):
    for (cx, w, cy, h) in glyph_rects(FONT[ch]):
        o = dk.box(p, (x_left + (cx + w / 2) * cw, y0 + (cy + h / 2) * chh, z), (w * cw, h * chh, depth), color, name="Letter")
        drop_faces(o, lambda n: n[2] < -0.99)


def word(p, text, cx, y0, z, cw, chh, color):
    width = len(text) * 4 + (len(text) - 1)
    x = cx - (width - 1) * cw / 2
    for ch in text:
        letter(p, ch, x, y0, z, cw, chh, color)
        x += 5 * cw


def build_Sign():
    p = dk.Part("Sign")
    X = -52.0
    Z = 54.0
    for sx in (-8.5, 8.5):
        post(p, X + sx, Z, 0, 15, 0.6, HULL_D, 6, top_r=0.5, jitter=0.06, name="SignPost")
        dk.cyl(p, (X + sx, 1.0, Z), 0.78, 0.5, IRON_L, verts=6, name="PostBand")
        dk.cyl(p, (X + sx, 3.2, Z), 0.78, 0.5, IRON_L, verts=6, name="PostBand")
        dk.ball(p, (X + sx, 15.6, Z), 0.8, GOLD, subdiv=1, name="Finial")
        dk.box(p, (X + sx, 0.4, Z), (2.0, 0.8, 2.0), STONE, jitter=0.05, name="Footing")
    board = strips(p, (X, 9.7, Z), (18.4, 9.0, 0.8), BOARD, 6, 'y', 0.09, "Board")
    dk.box(p, (X, 14.6, Z), (21, 0.8, 1.4), HULL, jitter=0.05, name="TopBeam")
    dk.box(p, (X, 4.8, Z), (20, 0.8, 1.2), HULL, jitter=0.05, name="BottomBeam")
    for sx in (-8.8, 8.8):
        for y in (5.5, 13.9):
            dk.box(p, (X + sx, y, Z + 0.45), (1.2, 1.2, 0.2), GOLD_D, name="Corner")
    word(p, "GET", X, 10.2, 54.55, 0.5, 0.62, CREAM)
    word(p, "BONKED", X, 6.3, 54.55, 0.5, 0.62, CREAM)
    # skull and crossbones on top
    for a in (-1, 1):
        bar(p, (X - a * 2.5, 15.3, 53.6), (X + a * 2.5, 17.4, 53.6), 0.5, BONE_D, h=0.55, name="Crossbone")
        dk.ball(p, (X + a * 2.5, 17.4, 53.6), 0.42, BONE_D, subdiv=0, name="BoneEnd")
        dk.ball(p, (X - a * 2.5, 15.3, 53.6), 0.42, BONE_D, subdiv=0, name="BoneEnd")
    dk.ball(p, (X, 16.4, Z), 1.5, BONE, scale=(1.0, 0.93, 0.5), subdiv=1, name="Skull")
    dk.box(p, (X, 15.2, Z + 0.1), (1.8, 0.8, 1.0), BONE, name="Jaw")
    for s in (-0.6, 0.6):
        dk.box(p, (X + s, 16.5, Z + 0.78), (0.65, 0.65, 0.2), IRON, name="Eye")
    dk.box(p, (X, 15.8, Z + 0.78), (0.3, 0.45, 0.2), IRON, name="Nose")
    for x in (-0.55, 0.0, 0.55):
        dk.box(p, (X + x, 14.95, Z + 0.62), (0.08, 0.5, 0.08), IRON, name="Teeth")
    return p


# ---- PART 4: Masts -----------------------------------------------------------------------------------------------
ROPE = (190, 164, 112)


def yard(p, y, z, L, r=0.42, color=HULL_D):
    return tube(p, [(CX - L / 2, y, z), (CX, y, z), (CX + L / 2, y, z)], [r * 0.5, r, r * 0.5], 6, color, 0.05, name="Yard")


def rope_ladder(p, z, y_top, side, y_bot=7.6):
    xo = CX + side * 8.9
    xt = CX + side * 0.7
    za, zb = z - 1.3, z + 1.3
    A = ((xt, y_top, z - 0.3), (xo, y_bot, za))
    B = ((xt, y_top, z + 0.3), (xo, y_bot, zb))
    for a, b in (A, B):
        bar(p, a, b, 0.2, ROPE, h=0.2, name="Shroud")
    for f in (0.33, 0.66):
        pa = [A[0][i] + (A[1][i] - A[0][i]) * f for i in range(3)]
        pb = [B[0][i] + (B[1][i] - B[0][i]) * f for i in range(3)]
        bar(p, pa, pb, 0.14, ROPE, h=0.14, name="Ratline")


def build_Masts():
    p = dk.Part("Masts")
    # main mast with iron bands, topmast and crow's nest
    dk.cyl(p, (CX, 22.4, -32), 0.75, 30, HULL, verts=8, top_radius=0.5, jitter=0.05, name="MainMast")
    for y in (10.0, 16.4, 25.4):
        dk.cyl(p, (CX, y, -32), 0.88, 0.4, IRON_L, verts=8, name="MastBand")
    tube(p, [(CX, 37.4, -32), (CX, 42.4, -32)], [0.45, 0.2], 6, HULL, 0.05, name="TopMast")
    for y, L in ((16.4, 18.0), (25.4, 14.0), (32.0, 10.0)):
        yard(p, y, -32, L)
    dk.cyl(p, (CX, 26.6, -32), 0.45, 0.9, HULL_D, verts=6, top_radius=1.5, name="NestBase")
    dk.cyl(p, (CX, 27.2, -32), 1.7, 0.4, DECK_D, verts=6, name="NestFloor")
    for k in range(6):
        a = pi / 6 + k * pi / 3
        dk.box(p, (CX + 1.55 * math.cos(a), 27.9, -32 + 1.55 * math.sin(a)), (1.75, 1.3, 0.2), DECK, rot=(0, -math.degrees(a) + 90, 0), jitter=0.05, name="NestWall")
    # fore mast
    dk.cyl(p, (CX, 19.4, -50), 0.65, 24, HULL, verts=8, top_radius=0.45, jitter=0.05, name="ForeMast")
    dk.cyl(p, (CX, 24.2, -50), 1.4, 0.35, DECK_D, verts=8, name="ForeTop")
    for y in (10.0, 15.5):
        dk.cyl(p, (CX, y, -50), 0.78, 0.35, IRON_L, verts=8, name="MastBand")
    for y, L in ((15.5, 14.0), (22.5, 11.0)):
        yard(p, y, -50, L, 0.38)
    # mizzen mast with a gaff
    dk.cyl(p, (CX, 21.6, -14), 0.55, 18, HULL, verts=6, top_radius=0.38, jitter=0.05, name="MizzenMast")
    tube(p, [(CX, 23.6, -17.0), (CX, 23.6, -14.0), (CX, 23.6, -9.0)], [0.16, 0.3, 0.14], 6, HULL_D, 0.05, name="Gaff")
    # bowsprit
    tube(p, [(CX, 9.85, -58.5), (CX, 10.25, -64.0)], [0.55, 0.4], 6, HULL, 0.05, name="Bowsprit")
    # rigging
    for side in (-1, 1):
        rope_ladder(p, -32, 25.0, side)
        rope_ladder(p, -50, 22.0, side)
        rope_ladder(p, -14, 21.0, side, y_bot=12.8)
    # hanging lantern under the crow's nest and yard lifts from the mast to the yard arms
    # fore top bell, topmast cap and gold yard-arm caps
    dk.cone(p, (CX + 1.5, 23.25, -50), 0.45, 0.6, GOLD, verts=6, name="Bell")
    dk.ball(p, (CX, 42.1, -32), 0.3, GOLD, subdiv=0, name="TopCap")
    for (yy, zz, LL) in ((16.4, -32, 18.0), (25.4, -32, 14.0), (32.0, -32, 10.0), (15.5, -50, 14.0), (22.5, -50, 11.0)):
        for sd in (-1, 1):
            dk.box(p, (CX + sd * (LL / 2 - 0.2), yy, zz), (0.4, 0.4, 0.4), GOLD_D, name="YardCap")
    dk.box(p, (CX + 2.0, 25.6, -32), (0.7, 0.9, 0.7), AMBER, name="NestLantern")
    dk.cone(p, (CX + 2.0, 26.05, -32), 0.55, 0.4, IRON, verts=4, name="NestLanternCap")
    bar(p, (CX + 1.7, 27.2, -32), (CX + 2.0, 26.1, -32), 0.1, IRON, h=0.1, name="LanternChain")
    for side in (-1, 1):
        bar(p, (CX + side * 0.5, 22.0, -32.3), (CX + side * 8.0, 16.6, -32.3), 0.12, ROPE, h=0.12, name="Lift")
        bar(p, (CX + side * 0.5, 29.5, -32.3), (CX + side * 6.4, 25.6, -32.3), 0.12, ROPE, h=0.12, name="Lift")
        bar(p, (CX + side * 0.5, 20.5, -50.3), (CX + side * 6.4, 15.7, -50.3), 0.12, ROPE, h=0.12, name="Lift")
    bar(p, (CX, 36.5, -32), (CX, 29.0, -50), 0.14, ROPE, h=0.14, name="Stay")
    bar(p, (CX, 30.0, -50), (CX, 10.4, -63.6), 0.14, ROPE, h=0.14, name="Stay")
    bar(p, (CX, 30.0, -32), (CX, 29.6, -14), 0.14, ROPE, h=0.14, name="Stay")
    return p


# ---- PART 5: Pier ------------------------------------------------------------------------------------------------
def rope_sag(p, A, B, sag, color=ROPE, w=0.16):
    M = [(A[0] + B[0]) / 2, min(A[1], B[1]) - sag, (A[2] + B[2]) / 2]
    bar(p, A, M, w, color, h=w, name="Rope")
    bar(p, M, B, w, color, h=w, name="Rope")


def buoy(p, x, y0, z, r=0.55):
    lathe(p, (x, y0, z), [(0, 0), (r * 0.9, r * 0.45), (r, r * 0.9), (r * 0.9, r * 1.4), (0, r * 1.8)], 6, RED, 0.02, name="Buoy")
    lathe(p, (x, y0 + r * 0.8, z), [(r * 1.02, 0), (r * 1.02, r * 0.3)], 6, CREAM, 0.0, name="BuoyBand", cap0=False)


def build_Pier():
    p = dk.Part("Pier")
    for i in range(9):
        x = -51.3 + i * 1.45
        wd = 5.0 if i < 6 else 6.5
        dk.box(p, (x, 0.44, -30), (1.32, 0.28, wd), DECK, jitter=0.07, name="PierPlank")
    for z in (-28.4, -31.6):
        dk.box(p, (-45.5, 0.4, z), (13.0, 0.12, 0.4), HULL_D, name="Stringer")
    posts = [(-50.5, -32.9), (-50.5, -27.1), (-44.5, -32.9), (-44.5, -27.1)]
    for (x, z) in posts:
        dk.cyl(p, (x, 1.5, z), 0.45, 2.4, HULL_D, verts=6, top_radius=0.38, jitter=0.05, name="Bollard")
        if (x, z) == (-44.5, -32.9):
            dk.ball(p, (x, 2.95, z), 0.5, BONE, subdiv=0, name="BollardSkull")
            for s in (-0.2, 0.2):
                dk.box(p, (x + s, 3.0, z + 0.42), (0.18, 0.18, 0.1), IRON, name="BollardEye")
        else:
            dk.ball(p, (x, 2.8, z), 0.42, HULL, subdiv=0, name="BollardCap")
        dk.cyl(p, (x, 0.55, z), 0.5, 0.4, IRON_L, verts=6, name="BollardFoot")
    for z in (-32.9, -27.1):
        rope_sag(p, (-50.5, 2.5, z), (-44.5, 2.5, z), 0.8)
    barrel(p, -47.4, 0.3, -31.2, 1.0, 2.0, name="Barrel")
    crate(p, -49.0, 0.3, -28.6, 1.6, name="Crate", rot=15)
    crate(p, -41.8, 0.3, -32.0, 1.1, name="Crate", rot=-10)
    # lantern on a hook at the shore side post
    bar(p, (-44.5, 2.7, -27.1), (-44.5, 3.1, -27.1), 0.12, IRON, name="Hook")
    dk.box(p, (-44.5, 3.05, -27.1), (0.7, 0.9, 0.7), AMBER, name="Lantern")
    dk.cone(p, (-44.5, 3.5, -27.1), 0.6, 0.05, IRON, verts=4, name="LanternCap")
    buoy(p, -51.3, 0.45, -32.5)
    buoy(p, -39.8, 0.45, -27.5)
    # a tricorn hat on a bollard, a rolled treasure map and a crab on the planks
    frustum(p, -50.5, -27.1, 2.65, 2.95, 1.6, 1.6, 1.2, 1.2, IRON, 0.02, name="BollardHat")
    frustum(p, -50.5, -27.1, 2.95, 3.45, 0.9, 0.9, 0.8, 0.8, IRON, 0.02, name="BollardHat")
    lathe(p, (-48.2, 0.7, -29.4), [(0.22, 0), (0.22, 1.4)], 5, CREAM_D, 0.03, axis='x', name="MapScroll")
    blob(p, (-46.6, 0.7, -28.6), 0.3, (226, 84, 60), sx=1.4, sy=0.5, sides=5, name="Crab")
    # wanted board on a post at the shore end
    dk.cyl(p, (-40.3, 1.8, -32.4), 0.2, 3.0, HULL_D, verts=5, name="BoardPost")
    dk.box(p, (-40.3, 2.6, -32.2), (1.9, 1.5, 0.15), DECK_L, name="Wanted")
    dk.ball(p, (-40.3, 2.7, -32.08), 0.4, BONE_D, scale=(1, 1, 0.3), subdiv=0, name="WantedSkull")
    # coil of rope
    lathe(p, (-42.2, 0.58, -28.2), [(0.8, 0), (0.8, 0.3), (0.35, 0.3), (0.35, 0)], 8, ROPE, 0.05, name="RopeCoil")
    return p


# ---- PART 6: Sails -----------------------------------------------------------------------------------------------
def square_sail(p, z0, ybot, ytop, wbot, wtop, belly, color, stripe=None, thick=0.36, nx=6, ny=4, lift=0.5, name="Sail"):
    rings = []
    for j in range(ny + 1):
        t = j / ny
        hw = (wbot + (wtop - wbot) * t) / 2
        front, back = [], []
        for i in range(nx + 1):
            u = -1 + 2 * i / nx
            yb = ybot + lift * (1 - u * u) + (0.35 if i % 2 else 0.0)
            y = yb + (ytop - yb) * t
            zb = -belly * (1 - u * u) * math.sin(pi * (0.1 + 0.8 * t))
            front.append((CX + u * hw, y, z0 + zb + thick / 2))
            back.append((CX + u * hw, y, z0 + zb - thick / 2))
        rings.append(front + back[::-1])
    o = loft(p, rings, color, 0.03, name=name)
    m = 2 * (nx + 1)

    def col(c, n, k):
        if k >= ny * m:
            return CREAM_D
        band, i = divmod(k, m)
        if i in (nx, m - 1):
            return CREAM_D
        return RED if stripe is not None and band == stripe else color
    recolor(o, col, 0.04)
    return o


def build_Sails():
    p = dk.Part("Sails")
    zc = -32.6
    square_sail(p, zc, 9.4, 16.0, 16.4, 14.8, 1.1, CREAM, name="MainCourse")
    square_sail(p, zc, 16.9, 24.9, 12.6, 11.4, 1.0, CREAM, name="MainTopsail")
    square_sail(p, zc, 25.8, 31.6, 8.6, 7.6, 0.8, CREAM, stripe=2, nx=4, name="MainGallant")
    square_sail(p, -50.6, 8.6, 15.0, 12.6, 11.4, 1.0, CREAM, stripe=2, name="ForeCourse")
    square_sail(p, -50.6, 15.9, 21.9, 9.6, 8.6, 0.9, CREAM, nx=4, name="ForeTopsail")
    # jolly roger on the main course (road side): pixel skull plus two crossed bones that follow the belly of the sail
    def sail_z(x, y):
        hw = (16.4 + (14.8 - 16.4) * (y - 9.4) / 6.6) / 2
        u = (x - CX) / hw
        t = (y - 9.4) / 6.6
        return zc - 1.1 * (1 - u * u) * math.sin(pi * (0.1 + 0.8 * t)) + 0.18 + 0.07
    for a in (-1, 1):
        A = (CX - a * 3.7, 10.9, sail_z(CX - a * 3.7, 10.9))
        B = (CX + a * 3.7, 13.6, sail_z(CX + a * 3.7, 13.6))
        bar(p, A, B, 0.12, IRON, h=0.62, name="EmblemBone")
        for q in (A, B):
            dk.box(p, (q[0], q[1], q[2]), (0.85, 0.85, 0.12), IRON, name="EmblemBoneEnd")
    skull = [".XXXX.", "XXXXXX", "X.XX.X", "XX..XX", ".XXXX."]
    cw, chh = 0.75, 0.68
    for (cx_, w_, cy_, h_) in glyph_rects(skull):
        px = CX - 3 * cw + (cx_ + w_ / 2) * cw
        py = 12.4 + (cy_ + h_ / 2) * chh
        dk.box(p, (px, py, sail_z(px, py) + 0.02), (w_ * cw, h_ * chh, 0.14), IRON, name="Emblem")
    # gaff sail and jib
    slab(p, [(14.2, -17.8), (14.6, -9.6), (23.2, -10.4), (23.5, -17.4)], 0.5, 'yz', CX, CREAM, 0.03, name="GaffSail")
    slab(p, [(10.4, -61.4), (10.8, -54.8), (20.8, -55.6)], 0.45, 'yz', CX, CREAM, 0.03, name="Jib")
    dk.box(p, (CX, 18.8, -13.8), (0.62, 0.6, 7.4), RED, name="GaffStripe")
    return p


# ---- PART 7: Tavern ----------------------------------------------------------------------------------------------
TX = 38.0


def window(p, x, y0, z, w, h, shutters=True):
    dk.box(p, (x, y0 + h / 2, z + 0.05), (w + 0.6, h + 0.6, 0.2), HULL_D, name="WinFrame")
    dk.box(p, (x, y0 + h / 2, z + 0.16), (w, h, 0.12), AMBER, name="WinGlass")
    dk.box(p, (x, y0 + h / 2, z + 0.24), (0.16, h, 0.1), HULL_D, name="WinBar")
    dk.box(p, (x, y0 + h / 2, z + 0.24), (w, 0.16, 0.1), HULL_D, name="WinBar")
    if shutters:
        for s in (-1, 1):
            dk.box(p, (x + s * (w / 2 + 0.55), y0 + h / 2, z + 0.28), (0.9, h + 0.4, 0.14), RED_D, name="Shutter")


def build_Tavern():
    p = dk.Part("Tavern")
    dk.box(p, (TX, 0.25, -43), (28, 0.5, 26), STONE_D, name="Slab")
    g = grid(p, TX - 14, TX + 14, -56, -30, 9, 8, 0.53, 0.0, STONE, 0.1, name="Cobbles")
    recolor(g, lambda c, n, k: STONE if (k % 2) else STONE_L, 0.07)
    # ground floor walls, upper floor overhang plate and walls
    strips(p, (TX, 4.5, -48.5), (22, 8.0, 15), HULL, 11, 'x', 0.08, "WallsLow")
    dk.box(p, (TX, 8.75, -48), (24, 0.5, 16), DECK_D, jitter=0.04, name="Overhang")
    strips(p, (TX, 11.75, -48.5), (19, 5.5, 13), HULL_D, 9, 'x', 0.08, "WallsHigh")
    for x in (TX - 11.0, TX + 11.0):
        dk.box(p, (x, 4.5, -41.0), (0.9, 8.0, 0.5), HULL_D, name="Corner")
    for x in (TX - 9.5, TX + 9.5):
        dk.box(p, (x, 11.75, -41.9), (0.8, 5.5, 0.5), HULL, name="Corner")
    # door with a lintel and a step
    dk.box(p, (TX, 2.8, -40.75), (3.4, 4.6, 0.3), HULL_D, name="DoorFrame")
    dk.box(p, (TX, 2.8, -40.6), (2.6, 4.2, 0.2), IRON, name="Door")
    dk.box(p, (TX, 5.4, -40.75), (3.8, 0.6, 0.3), GOLD_D, name="DoorLintel")
    dk.box(p, (TX + 0.8, 2.6, -40.45), (0.3, 0.3, 0.2), GOLD, name="DoorKnob")
    dk.box(p, (TX, 0.7, -39.8), (4.4, 0.4, 1.4), STONE_L, name="DoorStep")
    for x in (TX - 6.8, TX + 6.8):
        window(p, x, 3.4, -41.0, 2.8, 2.8)
    for x in (TX - 6.0, TX, TX + 6.0):
        window(p, x, 10.0, -41.95, 2.6, 2.4, shutters=(x != TX))
    # gabled roof with red tiles
    dk.prism(p, (TX, 14.5, -48.5), 25.4, 16.6, 3.4, RED_D, ridge="x", name="RoofCore")
    for s in (-1, 1):
        pts, faces = [], []
        nr, nc = 4, 8
        for r in range(nr + 1):
            for c in range(nc + 1):
                pts.append((TX - 12.7 + 25.4 * c / nc, 14.5 + 3.4 * (r / nr) + 0.12, -48.5 + s * 8.3 * (1 - r / nr)))
        for r in range(nr):
            for c in range(nc):
                a = r * (nc + 1) + c
                faces.append((a, a + 1, a + nc + 2, a + nc + 1))
        o = _obj(p, "Tiles", pts, faces, RED, 0.05, closed=False, up=True)
        recolor(o, lambda c, n, k: RED if (k // 8 + k % 8) % 2 else mix(RED, RED_D, 0.45), 0.05)
    dk.box(p, (TX, 17.95, -48.5), (25.6, 0.35, 0.5), GOLD_D, name="Ridge")
    for sx, ln in ((-12.4, 3.6), (12.4, -3.6)):
        tube(p, [(TX + sx, 17.9, -48.5), (TX + sx, 20.0, -48.5)], [0.16, 0.1], 5, HULL_D, 0.0, name="RoofPole")
        pennant_loft(p, TX + sx, 19.3, -48.5, ln, 1.1, 0.3, RED)
    # chimney with smoke
    dk.box(p, (46, 16.0, -52), (3, 4.0, 3), STONE, jitter=0.06, name="Chimney")
    dk.box(p, (46, 18.2, -52), (3.6, 0.4, 3.6), STONE_D, name="ChimneyCap")
    blob(p, (46.2, 18.9, -52), 0.62, (228, 228, 232), sides=5, name="Smoke")
    blob(p, (46.7, 19.5, -51.6), 0.45, (240, 240, 244), sides=5, name="Smoke")
    # porch: posts, roof, balcony rail
    dk.box(p, (TX, 8.25, -37), (24.5, 0.5, 8.6), DECK, jitter=0.04, name="PorchRoof")
    for x in (TX - 9.5, TX + 9.5):
        dk.cyl(p, (x, 4.25, -33.4), 0.4, 7.5, HULL_D, verts=6, jitter=0.05, name="PorchPost")
        dk.box(p, (x, 0.9, -33.4), (1.1, 0.8, 1.1), STONE_L, name="PostBase")
        bar(p, (x, 7.4, -33.4), (x + (2.0 if x < TX else -2.0), 8.0, -33.4), 0.3, HULL_D, name="Brace")
    dk.box(p, (TX, 9.2, -33.0), (24.4, 0.3, 0.3), HULL_D, name="Rail")
    for x in range(-12, 13, 3):
        dk.box(p, (TX + x, 8.85, -33.0), (0.3, 0.7, 0.3), HULL_D, name="Baluster")
    # barrels, sign, lantern
    barrel(p, 50.4, 0.5, -31.2, 1.2, 2.8, sides=6, name="Barrel")
    barrel(p, 26.5, 0.5, -31.6, 1.2, 2.8, sides=6, name="Barrel")
    bar(p, (47.5, 6.7, -33.4), (49.5, 6.7, -33.4), 0.3, IRON, name="SignArm")
    dk.box(p, (48.5, 5.2, -33.4), (2.8, 2.2, 0.3), GOLD, jitter=0.03, name="SignBoard")
    dk.box(p, (48.5, 5.1, -33.2), (1.0, 1.3, 0.12), RED, name="SignMug")
    dk.box(p, (49.2, 5.1, -33.2), (0.35, 0.7, 0.12), RED, name="SignMug")
    dk.box(p, (28.9, 5.6, -33.4), (0.7, 0.9, 0.7), AMBER, name="PorchLamp")
    return p


# ---- PART 8: Cannons ---------------------------------------------------------------------------------------------
def cannon_model(p, c, z, d):
    """c = carriage centre x, d = +1 muzzle towards +x, -1 towards -x. Deck at y = 7.4."""
    y0 = 7.4
    X = lambda u: c + d * u
    for s in (-0.95, 0.95):
        dk.box(p, (X(0.0), y0 + 0.55, z + s), (2.2, 0.9, 0.45), HULL_D, jitter=0.05, name="Cheek")
    dk.box(p, (X(-0.7), y0 + 0.3, z), (0.3, 0.3, 2.4), DECK_D, name="Axle")
    dk.box(p, (X(0.7), y0 + 0.3, z), (0.3, 0.3, 2.4), DECK_D, name="Axle")
    for u in (-0.7, 0.7):
        for s in (-1.12, 1.12):
            dk.cyl(p, (X(u), y0 + 0.48, z + s), 0.48, 0.3, RED_D, axis="z", verts=5, name="Wheel")
    path = [(X(-1.2), y0 + 1.3, z), (X(-0.9), y0 + 1.3, z), (X(1.2), y0 + 1.3, z), (X(2.45), y0 + 1.3, z), (X(2.8), y0 + 1.3, z)]
    tube(p, path, [0.3, 0.7, 0.62, 0.5, 0.6], 6, STEEL_C, 0.04, name="Barrel")
    dk.cyl(p, (X(2.0), y0 + 1.3, z), 0.58, 0.3, GOLD_D, axis="x", verts=6, name="BarrelRing")
    dk.cyl(p, (X(-0.45), y0 + 1.3, z), 0.74, 0.28, GOLD_D, axis="x", verts=6, name="BarrelRing")


def build_Cannons():
    p = dk.Part("Cannons")
    for z in (-24.0, -33.0, -42.0):
        cannon_model(p, CX + 7.8, z, 1)
        cannon_model(p, CX - 7.8, z, -1)
    dk.box(p, (-61.6, 7.55, -28.2), (2.2, 0.3, 2.2), DECK_D, jitter=0.05, name="BallRack")
    for (x, y, z) in ((-62.4, 8.2, -27.6), (-61.2, 8.2, -27.6), (-61.8, 8.2, -28.8), (-62.4, 8.2, -28.8), (-61.2, 8.2, -28.8),
                      (-61.8, 8.95, -28.2)):
        dk.ball(p, (x, y, z), 0.5, IRON_L, subdiv=0, name="Cannonball")
    # powder kegs with a red band, and a ramrod leaning on the cannon carriage
    for (x, z) in ((CX - 2.2, -38.4), (CX + 2.0, -37.6)):
        barrel(p, x, 7.4, z, 0.8, 1.3, color=RED_D, band=GOLD_D, sides=6, name="Keg")
    bar(p, (CX + 6.6, 7.4, -22.9), (CX + 3.6, 8.6, -22.9), 0.14, DECK_L, h=0.14, name="Ramrod")
    return p


# ---- PART 9: Camp ------------------------------------------------------------------------------------------------
def build_Camp():
    p = dk.Part("Camp")
    # tent with a dark opening
    tent = dk.prism(p, (70, 0, 37.5), 8.2, 8.0, 3.7, CREAM, ridge='z', jitter=0.04, name="Tent")
    recolor(tent, lambda c, n, k: CREAM_D if abs(n[0]) > 0.5 else None, 0.04)
    slab(p, [(68.2, 0.0), (71.8, 0.0), (70.0, 2.9)], 0.12, 'xy', 41.55, IRON, 0.02, name="TentDoor")
    bar(p, (70, 3.75, 33.2), (70, 3.75, 42.2), 0.22, HULL_D, name="RidgePole")
    for z in (33.2, 42.2):
        dk.ball(p, (70, 3.75, z), 0.3, GOLD_D, subdiv=0, name="PoleKnob")
    for (sx, sz, rz) in ((66.2, 43.6, 42.2), (73.8, 43.6, 42.2), (66.2, 31.4, 33.2), (73.8, 31.4, 33.2)):
        bar(p, (70, 3.7, rz), (sx, 0.1, sz), 0.1, ROPE, h=0.1, name="Guy")
        dk.box(p, (sx, 0.35, sz), (0.2, 0.7, 0.2), HULL_D, name="Stake")
    # campfire: ring of stones, crossed logs, flames, tripod with cauldron
    fx, fz = 78.0, 42.0
    for k in range(7):
        a = 2 * pi * k / 7
        dk.ball(p, (fx + 1.55 * math.cos(a), 0.3, fz + 1.55 * math.sin(a)), 0.4, STONE if k % 2 else STONE_L, scale=(1, 0.7, 1), subdiv=0, name="FireStone")
    for a in (0, 60, 120):
        ra = math.radians(a)
        bar(p, (fx - math.cos(ra) * 1.0, 0.55, fz + math.sin(ra) * 1.0), (fx + math.cos(ra) * 1.0, 0.55, fz - math.sin(ra) * 1.0), 0.4, HULL_D, name="Log")
    dk.cone(p, (fx, 0.5, fz), 0.8, 1.7, ORANGE, verts=6, name="Flame")
    dk.cone(p, (fx, 0.5, fz), 0.45, 1.1, YELLOW, verts=5, name="Flame")
    for k in range(3):
        a = 2 * pi * k / 3 + 0.4
        bar(p, (fx + 2.1 * math.cos(a), 0.1, fz + 2.1 * math.sin(a)), (fx, 4.15, fz), 0.22, HULL_D, name="TripodLeg")
    bar(p, (fx, 4.15, fz), (fx, 3.3, fz), 0.1, IRON, name="Chain")
    lathe(p, (fx, 2.0, fz), [(0.6, 0), (1.0, 0.35), (1.1, 0.95), (0.95, 1.2)], 7, IRON, 0.03, name="Cauldron")
    dk.cyl(p, (fx, 3.18, fz), 0.9, 0.08, GRASS_D, verts=7, name="Stew")
    # log seats
    dk.cyl(p, (78, 0.5, 46.5), 0.5, 4.2, HULL, axis='x', verts=6, jitter=0.05, name="LogSeat")
    dk.cyl(p, (73.5, 0.5, 42), 0.5, 3.6, HULL, axis='z', verts=6, jitter=0.05, name="LogSeat")
    # a little jolly roger on a pole beside the tent
    tube(p, [(73.0, 0.0, 45.6), (73.0, 4.3, 45.6)], [0.22, 0.12], 5, HULL_D, 0.04, name="CampPole")
    pennant_loft(p, 73.1, 3.4, 45.6, 1.9, 1.5, 0.2, IRON)
    dk.box(p, (74.0, 3.45, 45.8), (0.55, 0.5, 0.1), BONE, name="CampSkull")
    # barrels, crates, sacks
    barrel(p, 85.0, 0.0, 36.0, 1.1, 2.6, sides=6, name="Barrel")
    barrel(p, 87.3, 0.0, 37.4, 1.0, 2.4, sides=6, name="Barrel")
    crate(p, 82.5, 0.0, 31.5, 2.6, name="Crate", rot=8)
    crate(p, 85.6, 0.0, 31.2, 2.2, name="Crate", rot=-12)
    crate(p, 84.0, 2.6, 31.5, 1.8, name="Crate", rot=25)
    for (sx, sz) in ((80.6, 34.8), (79.2, 33.4)):
        blob(p, (sx, 0.75, sz), 0.85, CREAM_D, sy=0.9, sides=6, jitter=0.04, name="Sack")
    return p


# ---- PART 10: Flag -----------------------------------------------------------------------------------------------
def make_flag_art(cols=14, rows=10):
    g = [["."] * cols for _ in range(rows)]
    for r in range(4, rows):                       # crossed bones
        for cA in (1.2 + (r - 4) * 2.1, 12.8 - (r - 4) * 2.1):
            for c in range(cols):
                if abs(c - cA) <= 1.1:
                    g[r][c] = "X"
    skull = [".....XXXX.....", "....XXXXXX....", "....X.XX.X....", "....XXXXXX....", ".....XXXX....."]
    for r, row in enumerate(skull):                # skull on top (dark eyes are the gaps inside)
        for c in range(4, 10):
            g[r][c] = "X" if row[c] == "X" else "."
    g[3][6] = "."; g[3][7] = "."                   # nose
    return ["".join(r) for r in g]


def pixel_flag(p, x0, ybot, z, w, h, art, amp, thick=0.22):
    rows, cols = len(art), len(art[0])
    rings = []
    for i in range(cols + 1):
        u = i / cols
        x = x0 + w * u
        zz = z + amp * u * math.sin(u * pi * 2.4)
        ring = [(x, ybot + h * j / rows, zz + thick / 2) for j in range(rows + 1)]
        ring += [(x, ybot + h * j / rows, zz - thick / 2) for j in range(rows, -1, -1)]
        rings.append(ring)
    o = loft(p, rings, IRON, 0.02, name="Flag")
    m = 2 * (rows + 1)

    def col(c, n, k):
        interval, i = divmod(k, m)
        if interval >= cols:
            return IRON
        if i < rows:                       # front face, row i from the bottom
            r = rows - 1 - i
            return BONE if art[r][interval] == "X" else IRON
        if rows + 1 <= i <= 2 * rows:      # back face, mirrored so it reads correctly from behind
            j = rows - 1 - (i - (rows + 1))
            r = rows - 1 - j
            return BONE if art[r][cols - 1 - interval] == "X" else IRON
        return IRON
    recolor(o, col, 0.02)
    return o


def build_Flag():
    p = dk.Part("Flag")
    tube(p, [(CX, 42.4, -32), (CX, 46.4, -32)], [0.3, 0.2], 6, HULL_D, 0.04, name="FlagPole")
    dk.ball(p, (CX, 46.6, -32), 0.45, GOLD, subdiv=1, name="Finial")
    pixel_flag(p, CX + 0.2, 41.6, -32, 6.8, 4.4, make_flag_art(), 0.4)
    for z, y0 in ((-50, 31.4), (-14, 30.6)):
        tube(p, [(CX, y0, z), (CX, y0 + 3.0, z)], [0.25, 0.15], 6, HULL_D, 0.04, name="PennantPole")
        dk.ball(p, (CX, y0 + 3.15, z), 0.3, GOLD, subdiv=0, name="Finial")
        pennant_loft(p, CX + 0.2, y0 + 1.6, z, 5.0, 1.5, 0.35, RED)
    return p


# ---- PART 11: Palms ----------------------------------------------------------------------------------------------
def palm(p, cx, cz, H, yaw0, lean, n_big=9, L=6.9):
    lx, lz = lean
    fr = [(0, 1.3), (0.05, 1.05), (0.2, 0.92), (0.4, 0.84), (0.6, 0.8), (0.8, 0.8), (0.93, 0.88), (1.0, 0.7)]
    Hc = H - 0.9
    prof = [(r, Hc * f, lx * f * f, lz * f * f) for f, r in fr]
    tr = lathe(p, (cx, 0.0, cz), prof, 6, TRUNK, 0.04, name="Trunk")
    recolor(tr, lambda c, n, k: TRUNK_D if (k // 6) % 2 else TRUNK, 0.04)
    top = (cx + lx, Hc, cz + lz)
    lathe(p, (cx, 0.0, cz), [(2.4, 0), (1.6, 0.3), (0, 0.5)], 7, SAND_D, 0.04, name="Mound")
    for k in range(3):
        a = math.radians(yaw0 + 18 + 120 * k)
        lathe(p, (top[0] + 1.0 * math.cos(a), Hc - 1.0, top[2] + 1.0 * math.sin(a)), [(0, 0), (0.7, 0.7), (0, 1.5)], 5, DECK_D, 0.05, name="Coconut")
    cols = [LEAF, LEAF_L, LEAF_D]
    for k in range(n_big):
        yaw = yaw0 + 360 / n_big * k
        add_blade(p, (top[0], Hc + 0.1, top[2]), yaw, L if k % 2 == 0 else L * 0.94, 3.2, 1.6 + 0.4 * (k % 3), 3.6 + 0.5 * (k % 2), cols[k % 3], segs=4, notch=True, name="Frond")


def build_Palms():
    p = dk.Part("Palms")
    palm(p, 64, 10, 14.5, 0, (0.8, 0.6))
    palm(p, 78, 18, 16.5, 20, (-0.9, 0.5))
    palm(p, 88, 8, 13.5, 10, (-1.0, 0.4))
    return p


# ---- PART 12: Rowboat --------------------------------------------------------------------------------------------
def boat_ring(x, b, ytop, ykeel, t=0.3):
    H = ytop - ykeel
    Y = lambda f: ykeel + f * H
    zs = [(-b, ytop), (-0.85 * b, Y(0.3)), (-0.35 * b, ykeel), (0.35 * b, ykeel), (0.85 * b, Y(0.3)), (b, ytop),
          (b - t, ytop), (0.8 * b - t, Y(0.3) + t), (0.3 * b, ykeel + t), (-0.3 * b, ykeel + t), (-(0.8 * b - t), Y(0.3) + t), (-(b - t), ytop)]
    return [(x, y, -56 + z) for z, y in zs]


def build_Rowboat():
    p = dk.Part("Rowboat")
    stations = [(-39.3, 0.15, 2.4, 1.9), (-38.0, 1.3, 2.3, 1.1), (-36.0, 1.95, 2.2, 0.55), (-33.0, 2.3, 2.2, 0.32), (-30.0, 2.15, 2.2, 0.32),
                (-28.0, 1.85, 2.2, 0.4)]
    rings = [boat_ring(x, b, yt, yk) for (x, b, yt, yk) in stations]
    h = loft(p, rings, HULL, 0.07, name="Hull")
    m = 12

    def hc(c, n, k):
        i = k % m
        if k >= m * (len(stations) - 1):
            return HULL_D
        return {0: RED_D, 1: HULL, 2: HULL_D, 3: HULL, 4: RED_D, 5: GOLD_D, 6: DECK_L, 7: DECK, 8: DECK_D, 9: DECK, 10: DECK_L, 11: GOLD_D}[i]
    recolor(h, hc, 0.07)
    dk.box(p, (-27.7, 1.25, -56), (0.6, 1.9, 4.4), HULL_D, name="Transom")
    for x in (-35.0, -31.0):
        dk.box(p, (x, 1.5, -56), (0.8, 0.35, 4.2), DECK, jitter=0.05, name="Thwart")
    for s in (-1, 1):
        dk.box(p, (-33.0, 1.9, -56 + s * 2.1), (0.5, 0.35, 0.5), IRON, name="Oarlock")
    # oars on the sand
    for z in (-61.2, -60.2):
        dk.box(p, (-29.2, 0.45, z), (4.4, 0.18, 0.28), DECK_L, name="OarShaft")
        dk.box(p, (-25.9, 0.45, z), (1.5, 0.16, 0.7), DECK, name="OarBlade")
    lathe(p, (-31.0, 0.7, -56.0), [(0.7, 0), (0.7, 0.28), (0.3, 0.28), (0.3, 0)], 7, ROPE, 0.05, name="RopeCoil")
    lathe(p, (-34.6, 0.7, -55.0), [(0.5, 0), (0.62, 0.9)], 6, GOLD_D, 0.04, name="Bucket", cap0=True)
    dk.box(p, (-33.2, 1.45, -56.8), (0.7, 0.9, 0.7), AMBER, name="Lantern")
    dk.cone(p, (-33.2, 1.9, -56.8), 0.55, 0.4, IRON, verts=4, name="LanternCap")
    # a seagull on the transom and an oar leaning on the boat
    gx, gy, gz = -27.9, 2.35, -56.0
    blob(p, (gx, gy + 0.55, gz), 0.55, CREAM, sx=1.0, sy=0.8, sz=1.5, sides=5, name="Gull")
    blob(p, (gx - 0.35, gy + 1.15, gz), 0.28, CREAM, sides=5, name="GullHead")
    tetra(p, (gx - 0.55, gy + 1.15, gz - 0.08), (gx - 0.55, gy + 1.15, gz + 0.08), (gx - 1.0, gy + 1.05, gz), (gx - 0.55, gy + 1.0, gz), ORANGE, name="GullBeak")
    for s in (-1, 1):
        dk.box(p, (gx + 0.15, gy + 0.65, gz + s * 0.6), (0.9, 0.12, 0.5), (206, 212, 218), name="GullWing")
    bar(p, (-30.6, 0.4, -53.6), (-33.8, 3.6, -53.9), 0.2, DECK_L, h=0.2, name="LeaningOar")
    for k, (fx, fz) in enumerate(((-37.0, -57.4), (-36.2, -55.0))):
        blob(p, (fx, 0.95, fz), 0.35, (210, 90, 70), sx=1.8, sy=0.5, sides=5, name="Fish")
    # anchor planted in the sand
    dk.cyl(p, (-24.5, 2.3, -58), 0.22, 4.0, IRON, verts=5, name="AnchorShaft")
    dk.box(p, (-24.5, 3.25, -58), (3.2, 0.45, 0.45), IRON, name="AnchorStock")
    dk.ball(p, (-24.5, 4.0, -58), 0.5, IRON_L, scale=(1, 1, 0.5), subdiv=0, name="AnchorRing")
    for s in (-1, 1):
        bar(p, (-24.5, 0.4, -58), (-24.5 + s * 1.5, 1.8, -58), 0.4, IRON, h=0.45, name="AnchorArm")
    return p


# ---- PART 13: Chest ----------------------------------------------------------------------------------------------
def gem(p, x, y, z, color, r=0.4):
    lathe(p, (x, y, z), [(0, 0), (r, r * 0.9), (0, r * 1.8)], 4, color, 0.03, name="Gem")


def coin(p, x, y, z, r=0.38):
    dk.cyl(p, (x, y, z), r, 0.1, GOLD, verts=6, rot=(R.uniform(-25, 25), R.uniform(0, 90), R.uniform(-25, 25)), jitter=0.06, name="Coin")


def build_Chest():
    p = dk.Part("Chest")
    slab(p, blob_poly(74, -8, 10, 8, 12, 0.05), 0.5, 'xz', 0.0, mix(WET, GOLD, 0.2), 0.04, name="Bed")
    strips(p, (74, 2.2, -8), (8, 3.4, 5), HULL, 4, 'y', 0.06, "ChestBody")
    dk.cyl(p, (74, 3.9, -8), 2.5, 8.0, HULL_L, axis="x", verts=10, jitter=0.06, name="Lid")
    for sx in (-3.5, 3.5):
        dk.box(p, (74 + sx, 2.25, -8), (0.8, 3.5, 5.2), GOLD, jitter=0.02, name="Band")
        dk.cyl(p, (74 + sx, 3.9, -8), 2.58, 0.8, GOLD_D, axis='x', verts=10, name="LidBand")
    for sx in (-3.9, 3.9):
        for sz in (-2.5, 2.5):
            dk.box(p, (74 + sx, 0.9, -8 + sz), (0.4, 0.5, 0.4), GOLD_D, name="Corner")
    dk.box(p, (74, 2.9, -5.45), (1.3, 1.7, 0.3), GOLD, name="LockPlate")
    dk.box(p, (74, 2.8, -5.28), (0.35, 0.55, 0.12), IRON, name="Keyhole")
    heaps = ((68.5, 1.35, -5.0, 5.6, 2.6, 4.6), (80.5, 1.25, -5.0, 5.0, 2.4, 4.2), (78.0, 1.15, -3.4, 4.0, 1.8, 3.2))
    for (x, y, z, sx, sy, sz) in heaps:
        dk.ball(p, (x, y, z), sx / 2, GOLD, scale=(1, sy / sx, sz / sx), subdiv=1, jitter=0.06, name="Heap")
    for k in range(12):
        a = R.uniform(0, 2 * pi)
        hx, hy, hz, sx, sy, sz = R.choice(heaps)
        coin(p, hx + 0.9 * (sx / 2) * math.cos(a), hy + sy * 0.4, hz + 0.9 * (sz / 2) * math.sin(a))
    for (x, z, col) in ((66.6, -3.5, RED), (70.4, -2.4, (60, 130, 220)), (82.0, -2.8, (60, 180, 100)), (79.4, -1.6, RED)):
        gem(p, x, 0.5, z, col)
    # a golden crown on the left heap
    lathe(p, (68.2, 2.45, -4.6), [(0.95, 0), (1.0, 0.65)], 7, GOLD, 0.03, name="CrownRim", cap0=False)
    for k in range(5):
        a = 2 * pi * k / 5
        cx_, cz_ = 68.2 + 0.9 * math.cos(a), -4.6 + 0.9 * math.sin(a)
        tetra(p, (cx_ - 0.25, 3.1, cz_ - 0.25), (cx_ + 0.25, 3.1, cz_ - 0.25), (cx_, 3.1, cz_ + 0.3), (cx_, 4.0, cz_), GOLD, name="CrownSpike")
    gem(p, 68.2, 2.65, -3.6, RED, 0.3)
    # goblet, skull, cutlasses, X mark
    lathe(p, (80.0, 0.5, -11.0), [(0.55, 0), (0.55, 0.15), (0.15, 0.3), (0.15, 0.9), (0.7, 1.0), (0.65, 1.9)], 6, GOLD, 0.03, name="Goblet", cap0=True)
    dk.ball(p, (70.5, 1.05, -11.0), 1.0, BONE, subdiv=1, name="BoneSkull")
    for s in (-0.35, 0.35):
        dk.box(p, (70.5 + s, 1.25, -10.1), (0.35, 0.35, 0.15), IRON, name="Eye")
    for a in (-1, 1):
        bar(p, (82.6 + a * 0.3, 0.3, -12.5 + a * 0.2), (82.6 - a * 0.9, 5.8, -12.5 + a * 0.2), 0.25, IRON_L, h=0.12, name="Cutlass")
        dk.box(p, (82.6 - a * 0.9, 5.8, -12.5 + a * 0.2), (0.7, 0.3, 0.3), GOLD_D, name="Hilt")
    for a in (-1, 1):
        bar(p, (70.4 - a * 1.4, 0.52, -1.4 - a * 1.4), (70.4 + a * 1.4, 0.52, -1.4 + a * 1.4), 0.5, RED, h=0.06, name="XMark")
    return p


# ---- PART 14: Skull Rock -----------------------------------------------------------------------------------------
def rock(p, cx, y0, cz, rx, rz, h, sides=8, top=0.55, color=STONE, name="Rock", rot=0.0):
    """Faceted boulder: three rings with jittered radii."""
    pts, rings = [], []
    for (f, rr) in ((0.0, 1.0), (0.45, 1.05), (1.0, top)):
        ring = []
        for i in range(sides):
            a = 2 * pi * i / sides + rot
            j = 1.0 + R.uniform(-0.14, 0.14)
            pts.append((cx + rx * rr * j * math.cos(a), y0 + h * f, cz + rz * rr * j * math.sin(a)))
            ring.append(len(pts) - 1)
        rings.append(ring)
    faces = []
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a[i], a[j], b[j], b[i]))
    faces.append(tuple(rings[-1]))
    faces.append(tuple(rings[0]))
    o = _obj(p, name, pts, faces, color, 0.08)
    recolor(o, lambda c, n, k: STONE_L if n[1] > 0.7 else (STONE_D if n[1] < -0.2 else None), 0.07)
    return o


def build_SkullRock():
    p = dk.Part("SkullRock")
    X, Z = -82.0, -52.0
    rock(p, X, 0.0, Z, 6.0, 5.5, 4.6, 9, 0.8, name="Base")
    rock(p, -86.5, 0.0, -55.0, 1.7, 1.7, 9.0, 6, 0.45, name="Spire", rot=0.3)
    rock(p, -76.8, 0.0, -56.0, 1.6, 1.6, 7.0, 6, 0.4, name="Spire", rot=0.5)
    # skull: cranium, jaw with teeth, dark eyes and nose
    dk.ball(p, (X, 10.6, Z), 5.0, BONE, scale=(1.0, 0.84, 0.9), subdiv=2, jitter=0.03, name="Cranium")
    frustum(p, X, -50.4, 4.5, 7.8, 6.2, 6.2, 8.2, 6.4, BONE_D, 0.04, name="Jaw")
    dk.box(p, (X, 6.3, -47.15), (6.2, 1.3, 0.5), IRON, name="Mouth")
    for k in range(7):
        x = X - 3.0 + k * 1.0
        dk.box(p, (x, 5.5, -47.0), (0.78, 1.0, 0.5), BONE, jitter=0.02, name="TeethLow")
        dk.box(p, (x, 7.1, -47.0), (0.78, 0.9, 0.5), BONE, jitter=0.02, name="TeethUp")
    for s in (-2.4, 2.4):
        dk.box(p, (X + s, 9.8, -47.7), (2.6, 2.8, 0.8), IRON, name="EyeSocket")
        dk.box(p, (X + s, 11.5, -47.55), (3.0, 0.5, 0.7), BONE_D, name="Brow")
    slab(p, [(X - 0.65, 8.4), (X + 0.65, 8.4), (X, 7.0)], 0.5, 'xy', -47.55, IRON, name="Nose")
    for s in (-1, 1):
        bar(p, (X + s * 1.0, 14.6, Z + 1.0), (X + s * 2.4, 11.8, Z + 2.8), 0.22, STONE_D, h=0.15, name="Crack")
    # pirate hat
    frustum(p, X, Z, 14.3, 14.9, 8.0, 7.0, 7.4, 6.4, IRON, 0.02, name="HatBrim")
    frustum(p, X, Z, 14.9, 17.1, 4.6, 4.2, 4.0, 3.8, IRON, 0.02, name="HatCrown")
    dk.box(p, (X, 15.2, -49.85), (4.0, 0.35, 0.2), GOLD, name="HatBand")
    dk.ball(p, (X, 15.8, -49.8), 0.7, BONE, scale=(1, 0.9, 0.25), subdiv=0, name="HatSkull")
    # foam around the rock, a few loose stones
    flat(p, blob_poly(X, Z, 6.5, 6.0, 16, 0.03), 0.49, FOAM, 0.02, name="RockFoam")
    for (x, z) in ((-79.4, -47.2), (-85.2, -47.4), (-77.0, -50.4)):
        rock(p, x, 0.0, z, 1.0, 1.0, 1.2, 5, 0.6, name="Stone")
    return p


# ---- PART 15: Kraken ---------------------------------------------------------------------------------------------
def smooth(t, a, b):
    t = max(0.0, min(1.0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def tentacle_model(p, x, z, H, curl, sway, phase):
    """curl = (dx, dz) the tip hooks over towards; the body does an S-curve of amplitude `sway`."""
    path, radii = [], []
    n = 13
    for i in range(n):
        t = i / (n - 1)
        c = smooth(t, 0.5, 1.0)
        px = x + sway * math.sin(t * pi * 1.7 + phase) * (0.3 + 0.7 * t) + curl[0] * c
        pz = z + 0.7 * sway * math.sin(t * pi * 1.3 + phase + 1.2) * t + curl[1] * c
        py = H * t - 0.16 * H * c * c
        path.append((px, py, pz))
        radii.append(1.9 * (1 - t) ** 0.9 + 0.2 if i < n - 1 else 0.0)
    path[0] = (path[0][0], 0.2, path[0][2])
    o = tube(p, path, radii, 6, PURPLE, 0.05, name="Tentacle")
    recolor(o, lambda c_, n_, k: (PURPLE_L if (k // 6) % 2 else PURPLE) if k < 6 * (n - 1) else PURPLE_D, 0.05)
    for i in range(1, n - 2, 1):                   # suckers along the road side
        px, py, pz = path[i]
        r = radii[i]
        tetra(p, (px - 0.3, py - 0.25, pz + r * 0.8), (px + 0.3, py - 0.25, pz + r * 0.8), (px, py + 0.3, pz + r * 0.8),
              (px, py, pz + r * 1.35), PINK, 0.02, name="Sucker")
    flat(p, blob_poly(path[0][0], path[0][2], 2.3, 2.3, 10, 0.06), 0.49, FOAM, 0.02, name="BaseFoam")
    return path


def build_Kraken():
    p = dk.Part("Kraken")
    X, Z = -82.0, -8.0
    head = dk.ball(p, (X, 6.0, Z), 5.0, PURPLE_L, scale=(1.0, 0.9, 0.9), subdiv=2, jitter=0.03, name="Head")
    recolor(head, lambda c, n, k: PURPLE_D if R.random() < 0.18 else None, 0.04)
    for s in (-2.5, 2.5):
        dk.ball(p, (X + s, 7.8, -3.9), 1.3, YELLOW, scale=(1.0, 1.15, 0.65), subdiv=1, name="Eye")
        dk.box(p, (X + s, 7.7, -3.3), (0.5, 1.4, 0.2), IRON, name="Pupil")
        dk.box(p, (X + s, 9.2, -3.6), (2.8, 0.45, 0.5), PURPLE_D, rot=(0, 0, 8 * (1 if s > 0 else -1)), name="Brow")
    dk.box(p, (X, 4.6, -3.4), (4.2, 0.6, 0.3), IRON, name="Mouth")
    for x in (-1.5, -0.5, 0.5, 1.5):
        tetra(p, (X + x - 0.3, 4.9, -3.3), (X + x + 0.3, 4.9, -3.3), (X + x, 4.25, -3.3), (X + x, 4.6, -3.0), BONE, name="Fang")
    for (hx, hz, hh) in ((-2.5, -9.0, 10.3), (0.0, -9.5, 10.8), (2.5, -9.0, 10.3)):
        tetra(p, (X + hx - 0.7, 10.0, hz - 0.7), (X + hx + 0.7, 10.0, hz - 0.7), (X + hx, 10.0, hz + 0.9), (X + hx, hh + 0.9, hz), PURPLE_D, name="Spike")
    tentacle_model(p, -87.4, -10.0, 21.0, (2.8, 0.6), 0.7, 0.0)
    tentacle_model(p, -76.6, -9.0, 19.0, (-2.7, 0.4), 0.6, 1.7)
    tentacle_model(p, -86.0, -16.0, 20.0, (2.0, 2.4), 0.7, 3.1)
    tentacle_model(p, -78.0, -16.0, 18.8, (-2.2, 2.4), 0.6, 4.4)
    flat(p, blob_poly(X, Z, 6.6, 5.4, 14, 0.08), 0.49, FOAM, 0.02, name="HeadFoam")
    return p


BUILDERS = [("Floor", build_Floor), ("Hull", build_Hull), ("Sign", build_Sign), ("Masts", build_Masts), ("Pier", build_Pier), ("Sails", build_Sails),
            ("Tavern", build_Tavern), ("Cannons", build_Cannons), ("Camp", build_Camp), ("Flag", build_Flag), ("Palms", build_Palms),
            ("Rowboat", build_Rowboat), ("Chest", build_Chest), ("SkullRock", build_SkullRock), ("Kraken", build_Kraken)]


# ---- pipeline ----------------------------------------------------------------------------------------------------
def mirrored_spot(x, z, facing=180):
    """The reference Shiba is placed mirrored in x because the finished (exported) meshes are mirrored in the scene."""
    return {"Shiba": {"Position": [-x, z], "Facing": 180 - facing}}


def shiba_spot(part_id, bp, lo, hi):
    if part_id == "Floor":
        sp = bp["Shiba"]
        return mirrored_spot(sp["Position"][0], sp["Position"][1], sp["Facing"])
    return mirrored_spot(hi[0] + 9.0, (lo[2] + hi[2]) / 2, 180)


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
    a = dk.args()
    out = os.path.abspath(a[0]) if a else os.path.join(HERE, "out", KEY)
    dk.start(out)
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_PirateShip.json"))
    stats = []
    allm = []
    for pid, fn in BUILDERS:
        if ONLY and pid not in ONLY:
            continue
        part = fn()
        pcs = dk.blueprint_part(bp, pid)["Pieces"]
        box = roblox_box(pcs)
        if os.environ.get("PS_COUNT"):
            cnt = {}
            for o in part.objs:
                k = o.name.rstrip("0123456789.")
                cnt[k] = cnt.get(k, 0) + sum(len(q.vertices) - 2 for q in o.data.polygons)
            print("COUNT", pid, sorted(cnt.items(), key=lambda kv: -kv[1])[:16])
        drop_ground_faces(part)
        fit(part, box)
        lo, hi = true_bounds(part.objs)
        meshes = dk.finish(part, KEY)
        tris = sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)
        stats.append((pid, len(meshes), tris))
        dk.preview(part, f"preview_{pid}.png", with_shiba=shiba_spot(pid, bp, lo, hi), azimuth=150, elevation=28)
        if DBG:
            for k, (az, el) in enumerate(((35, 24), (215, 24), (90, 12))):
                o2 = dk.OUT
                dk.OUT = DBG
                dk.preview(part, f"dbg_{pid}_{k}.png", with_shiba=None, azimuth=az, elevation=el)
                dk.OUT = o2
        allm += meshes
        dk.hide(meshes)
    if not ONLY:
        sp = bp["Shiba"]
        mb = mirrored_spot(sp["Position"][0], sp["Position"][1], sp["Facing"])
        dk.hide(allm, False)
        dk.preview(allm, "stage_PirateShip_34.png", with_shiba=mb, azimuth=155, elevation=32, size=(1600, 1000))
        dk.preview(allm, "stage_PirateShip_top.png", with_shiba=mb, azimuth=180, top=True, size=(1600, 1000))
        stack_images(out, "stage_PirateShip_34.png", "stage_PirateShip_top.png", "stage_PirateShip.png")
    for s in stats:
        print("STAT %-10s meshes=%d tris=%d" % s)


main()
