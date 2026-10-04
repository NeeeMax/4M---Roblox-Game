"""Beach Bar decor models (theme BeachBar): builds the 10 decor parts around the second Shiba.

Run:  blender --background --factory-startup --python build_BeachBar.py -- <outdir>
Writes into <outdir> (default: out/BeachBar next to this script):
  Decor_BeachBar_<PartId>.fbx, preview_<PartId>.png per part, stage_BeachBar.png (3/4 view + top view stacked),
  stage_BeachBar_34.png and stage_BeachBar_top.png (the two views separately).
Every model is built in the stage frame (see decorkit.py) and, before export, fitted to the union box of its blueprint
pieces (Roblox-style box: size boxes rotated, axis aligned) so that the game's fitToPieces scale stays ~1.
Style: chunky low poly, flat vertex colours with a little per-face jitter, no textures, no neon.
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import decorkit as dk

KEY = "BeachBar"
R = random.Random(21)
pi = math.pi
DBG = os.environ.get("BB_DBG")          # optional folder for extra debug renders (not a deliverable)
ONLY = set(os.environ.get("BB_ONLY", "").split(",")) - {""}

# ---- palette (shared by all parts) -------------------------------------------------------------------------------
SAND = (238, 214, 150); SAND_D = (200, 176, 118); SAND_M = (218, 194, 132); SAND_L = (248, 228, 168)
WOOD = (160, 116, 70); WOOD_D = (110, 76, 46); WOOD_L = (192, 148, 94)
TEAL = (32, 178, 170); TEAL_D = (22, 138, 134)
RED = (214, 62, 54); RED_D = (168, 44, 40)
WHITE = (245, 245, 240); CREAM = (235, 220, 190); YEL = (250, 205, 70); ORANGE = (232, 120, 40)
GREEN = (46, 139, 70); GREEN_L = (92, 178, 86); GREEN_D = (30, 104, 58)
THATCH = (224, 188, 108); THATCH_D = (186, 142, 72); THATCH_L = (246, 216, 140)
SEA = (46, 150, 214); SEA_D = (30, 122, 192); SEA_L = (110, 200, 236)
GLASS_G = (60, 150, 80); GLASS_A = (196, 112, 30); GLASS_B = (60, 130, 210); GLASS_C = (214, 236, 240)
STEEL = (150, 156, 164)


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


def lathe(part, base, profile, sides, color, jitter=0.0, axis="y", rot0=0.0, name="Lathe", cap0=True):
    """Solid of revolution. profile = [(radius, height[, dx, dz])] bottom to top (radius 0 = apex point), base = stage point.
    axis 'y' = standing, 'z' / 'x' = lying along that stage axis (height runs along it)."""
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


def _m(axis, u, v, h, bx, by, bz, dx, dz):
    if axis == 'y':
        return (bx + u + dx, by + h, bz + v + dz)
    if axis == 'z':
        return (bx + u + dx, by + v, bz + h + dz)
    return (bx + h + dz, by + u, bz + v + dx)          # 'x'


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


def blade(part, base, yaw, length, width, rise, droop, color, segs=4, thick=0.28, jitter=0.07, name="Frond", notch=False):
    """A palm frond / leaf: arched spine, widest in the first half, ridge on top, tip point."""
    a = math.radians(yaw)
    dx, dz = math.cos(a), -math.sin(a)
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
            w *= 0.66                                   # zig-zag outline = feathered leaflets
        s = 0.24 * w
        rings.append([(cx - px * w / 2, cy - s, cz - pz * w / 2), (cx, cy + thick / 2, cz),
                      (cx + px * w / 2, cy - s, cz + pz * w / 2)])
    return loft(part, rings, color, jitter, name=name)


def torus(part, c, Rr, r, axis, segs, sides, color, color_b=None, jitter=0.0, name="Torus"):
    """Ring whose hole axis is `axis`; colour_b alternates with colour per segment."""
    pts, faces = [], []
    for i in range(segs):
        a = 2 * pi * i / segs
        for j in range(sides):
            b = 2 * pi * j / sides
            rr = Rr + r * math.cos(b)
            u = (rr * math.cos(a), rr * math.sin(a), r * math.sin(b))
            m = (u[0], u[2], u[1]) if axis == 'y' else ((u[0], u[1], u[2]) if axis == 'z' else (u[2], u[0], u[1]))
            pts.append((c[0] + m[0], c[1] + m[1], c[2] + m[2]))
    for i in range(segs):
        for j in range(sides):
            i2, j2 = (i + 1) % segs, (j + 1) % sides
            faces.append((i * sides + j, i * sides + j2, i2 * sides + j2, i2 * sides + j))
    o = _obj(part, name, pts, faces, color, jitter)
    if color_b:
        recolor(o, lambda c_, n_, k: color_b if (k // sides) % 2 else color, jitter)
    return o


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


def tetra(part, p0, p1, p2, p3, color, jitter=0.0, name="Tooth"):
    return _obj(part, name, [p0, p1, p2, p3], [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], color, jitter)


def post(part, x, z, y0, y1, r, color, sides=6, top_r=None, jitter=0.0, name="Post"):
    return dk.cyl(part, (x, (y0 + y1) / 2, z), r, y1 - y0, color, verts=sides, top_radius=top_r, jitter=jitter, name=name)


def planks(part, x0, x1, z0, z1, y0, y1, n, axis, color, gap=0.12, jitter=0.08, name="Plank"):
    """n planks filling the rectangle, running along `axis` ('x' or 'z')."""
    out = []
    for i in range(n):
        if axis == 'x':
            w = (z1 - z0) / n
            c = (x0 + (x1 - x0) / 2, (y0 + y1) / 2, z0 + w * (i + 0.5))
            s = (x1 - x0, y1 - y0, w - gap)
        else:
            w = (x1 - x0) / n
            c = (x0 + w * (i + 0.5), (y0 + y1) / 2, z0 + (z1 - z0) / 2)
            s = (w - gap, y1 - y0, z1 - z0)
        out.append(dk.box(part, c, s, color, jitter=jitter, name=name))
    return out


def pennant(part, x, y, z, w, h, color, plane='xy', thick=0.1):
    return slab(part, [(x - w / 2, y), (x + w / 2, y), (x, y - h)], thick, plane, z, color, name="Pennant")


def bottle(p, x, y, z, color, h=2.6, r=0.5):
    return lathe(p, (x, y, z), [(r, 0), (r, h * 0.55), (r * 0.5, h * 0.78), (r * 0.5, h)], 4, color, jitter=0.03, name="Bottle")


def cup(p, x, y, z, color, h=1.1, r=0.5, sides=6):
    return dk.cyl(p, (x, y + h / 2, z), r, h, color, verts=sides, top_radius=r * 1.3, name="Cup")


def star(cx, cz, ro, ri, n=5, rot=0.0):
    pts = []
    for i in range(2 * n):
        a = rot + pi * i / n
        rr = ro if i % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


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
    # stage (x, y, z) -> Blender (x, z, y)
    B = lambda v: Vector((v[0], v[2], v[1]))
    F = Matrix.Translation(B(tc)) @ Matrix.Diagonal(Vector((sc[0], sc[2], sc[1], 1.0))) @ Matrix.Translation(-B(cc))
    for o in part.objs:
        o.data.transform(F @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.update()
    print("FIT %-11s scale x%.3f y%.3f z%.3f" % (part.id, sc[0], sc[1], sc[2]))
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




def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def sail(part, A, B, C, belly, color, jitter=0.0, name="Sail"):
    """Thin triangular sail with a belly (bulge along stage x) so its two sides catch light differently."""
    cx = [(A[i] + B[i] + C[i]) / 3 for i in range(3)]
    bt = (cx[0] + belly, cx[1], cx[2])
    bb = (cx[0] + belly * 0.55, cx[1], cx[2])
    pts = [A, B, C, bt, bb]
    faces = [(0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 1, 4), (1, 2, 4), (2, 0, 4)]
    return _obj(part, name, pts, faces, color, jitter)


# ---- PART: SandFloor ---------------------------------------------------------------------------------------------
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


CRAB = (226, 84, 60)


def crab(p, x, z, ang):
    """Tiny crab: flat body blob, two claws and six leg triangles (kept under 0.5 studs high)."""
    a = math.radians(ang)
    ex, ez = math.cos(a), math.sin(a)
    px, pz = -ez, ex
    blob(p, (x, 0.38, z), 0.62, CRAB, sy=0.2, sides=6, jitter=0.04, name="CrabBody")
    for s in (-1, 1):
        dk.box(p, (x + ex * 0.8 + px * 0.55 * s, 0.38, z + ez * 0.8 + pz * 0.55 * s), (0.34, 0.2, 0.34), CRAB, rot=(0, -ang, 0), jitter=0.04, name="Claw")
        for k in (-1, 0, 1):
            bx, bz = x + px * 0.5 * s + ex * 0.25 * k, z + pz * 0.5 * s + ez * 0.25 * k
            tip = (bx + px * 0.6 * s + ex * 0.2 * k, bz + pz * 0.6 * s + ez * 0.2 * k)
            flat(p, [(bx + ex * 0.06, bz + ez * 0.06), (bx - ex * 0.06, bz - ez * 0.06), tip], 0.33, dk.shade(CRAB, 0.8), 0.0, name="CrabLeg")


def build_SandFloor():
    p = dk.Part("SandFloor")
    dk.box(p, (-11, 0.12, 0), (154, 0.24, 96), SAND, name="SandBase")
    top = grid(p, -88, 66, -48, 48, 14, 8, 0.27, 0.035, SAND, 0.0, name="SandTop")
    recolor_v(top, lambda c: mix(mix((226, 198, 132), SAND_L, 0.5 + 0.5 * math.sin(c[0] * 0.05 + c[2] * 0.08)), (212, 184, 118), 0.4 + 0.4 * math.sin(c[0] * 0.11 - c[2] * 0.04 + 1.0)))
    dk.box(p, (68, 0.17, 0), (8, 0.34, 96), SAND_D, jitter=0.03, name="WetSand")
    dk.box(p, (80, 0.2, 0), (16, 0.4, 96), SEA_D, jitter=0.03, name="Sea")
    sea = grid(p, 72, 88, -48, 48, 4, 12, 0.42, 0.04, SEA, 0.0, name="SeaTop")
    recolor_v(sea, lambda c: mix(mix(SEA_L, SEA, min(1.0, max(0.0, (c[0] - 72) / 8))), SEA_D, min(1.0, max(0.0, (c[0] - 78) / 10))))
    # wet sand with a wavy edge, foam: a lace-like surf line with a zig-zag edge on the sea side
    west = [(62.2 + 1.8 * math.sin(z * 0.33), z) for z in range(-48, 49, 4)]
    flat(p, west + [(69.9, 48), (69.9, -48)], 0.345, dk.shade(SAND_D, 0.9), 0.02, name="WetPatch")
    east = [(72.4 + (1.8 if k % 2 else 0.0), -48 + 4 * k) for k in range(25)]
    slab(p, east + [(69.8, 48), (69.8, -48)], 0.14, 'xz', 0.36, WHITE, 0.03, name="Foam")
    zig = [(66.3 + (0.9 if k % 2 else 0.0), -46 + 3.0 * k) for k in range(32)]
    flat(p, zig + [(zx + 0.0, zz) for zx, zz in reversed([(66.0 + (0.9 if k % 2 else 0.0) - 0.55, -46 + 3.0 * k) for k in range(32)])],
         0.37, dk.shade(WHITE, 0.95), 0.02, name="FoamLine")
    # wavy white lines on the sea
    for x0, ph in ((77.0, 0.0), (80.5, 1.3), (84.0, 2.1)):
        cen = [(x0 + 0.8 * math.sin(z * 0.45 + ph), z) for z in range(-46, 47, 4)]
        flat(p, [(x - 0.2, z) for x, z in cen] + [(x + 0.2, z) for x, z in reversed(cen)], 0.495, (196, 234, 250), 0.03, name="WaveLine")
    # long soft dune streaks
    for _ in range(9):
        x = R.uniform(-80, 52)
        z = R.uniform(-42, 42)
        flat(p, lens(x, z, R.uniform(8, 14), R.uniform(0.9, 1.5), bend=R.uniform(-1.0, 1.0)), 0.335, mix(SAND, SAND_L, 0.8), 0.02, name="DuneStreak")
    # wave crests and a darker deep-water band
    flat(p, [(85.6, -48), (88, -48), (88, 48), (85.6, 48)], 0.47, dk.shade(SEA_D, 0.85), 0.03, name="Deep")
    for _ in range(18):
        x = R.uniform(75.5, 85)
        z = R.uniform(-44, 44)
        flat(p, lens(x, z, R.uniform(2.5, 6), R.uniform(0.35, 0.6)), 0.49, (176, 228, 248), 0.05, name="Crest")
    # sand patches: the two blueprint patches plus a few more
    for (cx, cz, sx, sz, col) in [(-30, 34, 6, 4, SAND_M), (24, -14, 7, 5, SAND_M), (-62, -10, 8, 5, SAND_M), (-8, 20, 5, 3.5, SAND_D),
                                  (40, 40, 6, 4, SAND_M), (-52, 40, 7, 4, SAND_D), (10, -40, 7, 4, SAND_M), (-75, 8, 4, 6, SAND_D)]:
        pts = [(cx + sx / 2 * math.cos(a) * R.uniform(0.85, 1.05), cz + sz / 2 * math.sin(a) * R.uniform(0.85, 1.05))
               for a in [2 * pi * k / 9 for k in range(9)]]
        flat(p, pts, 0.335, col, 0.04, name="Patch")
    # ripples parallel to the shore
    for _ in range(20):
        x = R.uniform(-84, 58)
        z = R.uniform(-44, 44)
        flat(p, lens(x, z, R.uniform(3, 8), R.uniform(0.3, 0.45), bend=R.uniform(-0.3, 0.3)), 0.34, dk.shade(SAND, 0.9), 0.03, name="Ripple")
    # footprints
    for k in range(16):
        x = -66 + k * 6.2
        z = 30 + math.sin(k * 0.45) * 5 + (1.1 if k % 2 else -1.1)
        flat(p, lens(x, z, 0.8, 0.38, along='x'), 0.345, dk.shade(SAND, 0.82), 0.0, name="Print")
    # starfish, shells, pebbles (flat enough to stay under the 0.5 stud top of the model)
    for (x, z, rot) in [(60, 22, 0.3), (54, -30, 1.1), (-58, -32, 0.7), (-20, 42, 0.0)]:
        flat(p, star(x, z, 2.1, 0.85, 5, rot), 0.36, (236, 108, 70), 0.04, name="Starfish")
    for (x, z, rot) in [(58, -8, 0.4), (50, 30, 2.0), (-44, 20, 1.2), (-12, -26, 3.0), (20, 30, 0.2)]:
        fan = [(x, z)] + [(x + 1.1 * math.cos(rot + pi * k / 4), z + 1.1 * math.sin(rot + pi * k / 4)) for k in range(5)]
        flat(p, fan, 0.36, (250, 224, 224), 0.03, name="Shell")
    for (x, z) in [(-80, -30), (-35, 6), (30, -22), (5, 38), (-70, 44)]:
        lathe(p, (x, 0.3, z), [(0, 0.0), (0.55, 0.06), (0.4, 0.15), (0, 0.19)], 5, (150, 150, 150), 0.06, rot0=R.random(), name="Pebble", cap0=False)
    for _ in range(10):
        x = R.uniform(-80, 56)
        z = R.uniform(-44, 44)
        flat(p, [(x + 0.55 * math.cos(2 * pi * k / 7), z + 0.55 * math.sin(2 * pi * k / 7)) for k in range(7)], 0.355, (250, 240, 224), 0.03, name="SandDollar")
    for _ in range(14):
        x = R.uniform(62.5, 69)
        z = R.uniform(-45, 45)
        flat(p, lens(x, z, R.uniform(0.7, 1.5), R.uniform(0.25, 0.4), bend=R.uniform(-0.2, 0.2)), 0.36, (84, 110, 60), 0.05, name="Seaweed")
    # driftwood and little crabs
    for (x, z, ang, ln) in [(-48, -38, 20, 5.0), (30, 14, -35, 4.0), (-12, 33, 70, 4.5)]:
        a = math.radians(ang)
        ex, ez = math.cos(a), math.sin(a)
        px, pz = -ez, ex
        pts = [(x - ex * ln / 2 + px * 0.2, z - ez * ln / 2 + pz * 0.2), (x - ex * ln * 0.15 + px * 0.4, z - ez * ln * 0.15 + pz * 0.4),
               (x + ex * ln / 2 + px * 0.15, z + ez * ln / 2 + pz * 0.15), (x + ex * ln / 2 - px * 0.2, z + ez * ln / 2 - pz * 0.2),
               (x + ex * ln * 0.1 - px * 0.45, z + ez * ln * 0.1 - pz * 0.45), (x - ex * ln / 2 - px * 0.25, z - ez * ln / 2 - pz * 0.25)]
        slab(p, pts, 0.17, 'xz', 0.28, (150, 120, 88), 0.08, name="Driftwood")
    for (x, z, ang) in [(56, -22, 30), (-28, 40, 160), (46, 36, 100)]:
        crab(p, x, z, ang)
    return p


# ---- PART: BarHut ------------------------------------------------------------------------------------------------
def fringe(p, x0, x1, z0, z1, y, step, ln, color, jit=0.08):
    """Hanging thatch strands (little tetrahedra) along the four edges of a rectangle at height y."""
    edges = [((x0, z0), (x1, z0), (0, -1)), ((x1, z0), (x1, z1), (1, 0)), ((x1, z1), (x0, z1), (0, 1)), ((x0, z1), (x0, z0), (-1, 0))]
    for (a, b, n) in edges:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(2, int(round(L / step)))
        ex, ez = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        for i in range(k):
            t0, t1 = L * i / k, L * (i + 1) / k
            tm = (t0 + t1) / 2
            A = (a[0] + ex * t0, y, a[1] + ez * t0)
            B = (a[0] + ex * t1, y, a[1] + ez * t1)
            T = (a[0] + ex * tm, y - ln * R.uniform(0.75, 1.15), a[1] + ez * tm)
            D = (A[0] / 2 + B[0] / 2 - n[0] * 0.55, y + 0.05, A[2] / 2 + B[2] / 2 - n[1] * 0.55)
            tetra(p, A, B, T, D, color, jit)


def recolor_v(o, fn):
    """Smooth per-corner colours from the vertex position (stage axes): fn(pos) -> colour (0-255). Gouraud-interpolated."""
    me = o.data
    attr = me.color_attributes.get("Col")
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            w = mw @ me.vertices[me.loops[li].vertex_index].co
            attr.data[li].color = (*dk.srgb(*fn((w.x, w.z, w.y))), 1.0)


def drop_faces(o, pred):
    """Deletes faces of o whose (stage-axes) normal satisfies pred(n) - hidden sides of parts glued to something."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bad = [f for f in bm.faces if pred((f.normal.x, f.normal.z, f.normal.y))]
    bmesh.ops.delete(bm, geom=bad, context='FACES')
    bm.to_mesh(o.data)
    bm.free()


def streak_cut(o, color, xs, zs, jitter=0.1):
    """Cuts a roof layer with planes (stage x / z) so the faces read as straw streaks, drops the caps, re-jitters colours."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for x in xs:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    for z in zs:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, z, 0), plane_no=(0, 1, 0))
    caps = [f for f in bm.faces if abs(f.normal.z) > 0.99]
    bmesh.ops.delete(bm, geom=caps, context='FACES')
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    recolor(o, lambda c, n, k: color, jitter)


def pixel_letter(p, ch, x, y0, zl, cell, color):
    """Block letters B, A, R on a sign facing +x; read left to right as seen from +x in the Blender preview (= +z)."""
    rects = {"B": [(0, 0, 1, 5), (1, 4, 1, 1), (1, 2, 1, 1), (1, 0, 1, 1), (2, 3, 1, 1), (2, 1, 1, 1)],
             "A": [(0, 0, 1, 4), (2, 0, 1, 4), (0, 4, 3, 1), (1, 2, 1, 1)],
             "R": [(0, 0, 1, 5), (1, 4, 1, 1), (1, 2, 1, 1), (2, 3, 1, 1), (2, 0, 1, 2)]}[ch]
    for (cx_, cy_, w, h) in rects:
        o = dk.box(p, (x, y0 + (cy_ + h / 2) * cell, zl + (cx_ + w / 2) * cell), (0.3, h * cell, w * cell), color, name="Letter")
        drop_faces(o, lambda n: n[0] < -0.99)           # the back of a letter sits on the sign


def build_BarHut():
    p = dk.Part("BarHut")
    # deck
    dk.box(p, (-62, 0.28, 10), (26, 0.56, 18), WOOD_D, name="DeckBase")
    planks(p, -75, -49, 1, 19, 0.5, 0.8, 6, 'x', WOOD, gap=0.18, jitter=0.07, name="DeckPlank")
    # walls (teal boards)
    strips(p, (-62, 5.1, 2.5), (24, 9.2, 1), TEAL, 6, 'x', 0.07, "WallBack")
    strips(p, (-62, 5.1, 17.5), (24, 9.2, 1), TEAL, 6, 'x', 0.07, "WallFront")
    strips(p, (-73.5, 5.1, 10), (1, 9.2, 16), TEAL, 5, 'z', 0.07, "WallLeft")
    # trim beams under the roof and posts
    for (c, s) in [((-62, 9.5, 1.95), (27, 0.7, 0.7)), ((-62, 9.5, 18.05), (27, 0.7, 0.7)), ((-50.2, 9.5, 10), (0.7, 0.7, 17))]:
        dk.box(p, c, s, WOOD_D, name="Beam")
    for (x, z) in [(-50.4, 2.5), (-50.4, 17.5)]:
        dk.box(p, (x, 4.9, z), (1.1, 9.0, 1.1), WOOD_D, jitter=0.05, name="Post")
    # window with shutters and flower box on the back wall
    dk.box(p, (-62, 5.8, 1.93), (5, 3.6, 0.2), (46, 96, 118), name="Glass")
    dk.box(p, (-62, 5.8, 1.78), (0.25, 3.6, 0.25), WOOD_D, name="Mullion")
    dk.box(p, (-62, 7.8, 1.8), (6.0, 0.45, 0.45), WOOD_D, name="Frame")
    dk.box(p, (-62, 3.8, 1.7), (6.4, 0.45, 0.65), WOOD_D, name="Sill")
    dk.box(p, (-64.7, 5.8, 1.8), (0.45, 3.9, 0.45), WOOD_D, name="Frame")
    dk.box(p, (-59.3, 5.8, 1.8), (0.45, 3.9, 0.45), WOOD_D, name="Frame")
    dk.box(p, (-58.38, 5.8, 0.93), (2.4, 3.9, 0.25), RED, rot=(0, 40, 0), jitter=0.05, name="Shutter")
    dk.box(p, (-65.62, 5.8, 0.93), (2.4, 3.9, 0.25), RED, rot=(0, -40, 0), jitter=0.05, name="Shutter")
    dk.box(p, (-62, 3.15, 1.3), (5.0, 0.6, 0.7), RED_D, name="FlowerBox")
    for i, col in enumerate([RED, YEL, WHITE, RED]):
        lathe(p, (-63.6 + 1.1 * i, 3.45, 1.3), [(0, 0), (0.38, 0.28), (0, 0.56)], 4, col, 0.03, name="Flower")
    torus(p, (-70.2, 6.3, 1.5), 1.3, 0.38, 'z', 6, 4, RED, WHITE, name="Lifebuoy")
    # counter on the open (east) side
    c1 = strips(p, (-51, 2.4, 10), (1.6, 4, 14), WOOD_D, 5, 'z', 0.07, "Counter")
    recolor(c1, lambda c, n, k: WOOD if (int((c[2] - 3) / 2) % 2) else WOOD_D, 0.05)
    dk.box(p, (-51, 4.6, 10), (2.6, 0.5, 15), CREAM, jitter=0.03, name="CounterTop")
    dk.box(p, (-49.95, 1.2, 10), (0.5, 0.35, 13.4), WOOD_D, name="Footrest")
    # bottles, cups, pineapple on the counter
    for z, col in [(4.4, GLASS_G), (5.5, GLASS_A)]:
        bottle(p, -51.6, 4.85, z, col)
    for z, col in [(8.6, RED), (10.2, YEL)]:
        cup(p, -50.9, 4.85, z, col)
    dk.box(p, (-50.9, 6.2, 8.6), (0.14, 1.3, 0.14), WHITE, rot=(20, 0, 10), name="Straw")
    lathe(p, (-51.1, 4.85, 13.6), [(0, 0), (0.7, 0.25), (0.85, 0.95), (0.6, 1.5), (0, 1.7)], 6, (232, 172, 44), 0.06, name="Pineapple", cap0=False)
    lathe(p, (-51.1, 6.5, 13.6), [(0.45, 0), (0.15, 1.0), (0, 1.1)], 5, GREEN, 0.05, name="PineappleTop", cap0=False)
    # back shelf with bottles
    dk.box(p, (-72.3, 5.9, 10), (1.5, 0.35, 12.4), WOOD, name="Shelf")
    for z in (4.6, 9.9, 15.4):
        dk.box(p, (-72.9, 5.35, z), (0.4, 0.9, 0.4), WOOD_D, name="Bracket")
    for z, col in [(6.0, GLASS_G), (8.0, GLASS_A), (13.4, GLASS_B)]:
        bottle(p, -72.5, 6.08, z, col, h=2.3, r=0.45)
    cup(p, -72.4, 6.08, 10.2, RED)
    # stools
    for z in (5.5, 10, 14.5):
        lathe(p, (-47.5, 0.0, z), [(0.75, 0), (0.3, 0.2), (0.3, 2.6)], 4, WHITE, 0.0, name="StoolLeg", cap0=False)
        lathe(p, (-47.5, 2.55, z), [(0.95, 0), (1.15, 0.3), (1.1, 0.75), (0, 0.8)], 6, RED, 0.04, name="StoolSeat", cap0=False)
    # thatched roof: stacked layers with shaggy fringes
    layers = [(9.8, 10.6, 30.0, 22.0, 27.0, 19.2, THATCH_D), (10.5, 11.2, 27.4, 19.6, 24.2, 16.4, THATCH),
              (11.1, 11.7, 24.4, 16.6, 19.0, 11.5, THATCH_L), (11.55, 11.75, 19.2, 11.7, 15.0, 7.5, THATCH)]
    for i, (y0, y1, bx, bz, tx, tz, col) in enumerate(layers):
        o = frustum(p, -62, 10, y0, y1, bx, bz, tx, tz, col, 0.07, name="Thatch%d" % i)
        if i < 2:
            streak_cut(o, col, [-62 + 3.6 * k for k in range(-3, 4)], [10 + 3.6 * k for k in range(-2, 3)], 0.1)
    dk.box(p, (-62, 9.78, 10), (29.8, 0.1, 21.8), THATCH_D, name="Ceiling")
    dk.cyl(p, (-62, 11.8, 10), 0.4, 15.0, THATCH_D, axis='x', verts=6, jitter=0.06, name="RidgeRoll")
    fringe(p, -77, -47, -1, 21, 9.85, 2.8, 1.5, THATCH_D)
    fringe(p, -75.7, -48.3, 0.2, 19.8, 10.55, 4.5, 1.0, THATCH)
    fringe(p, -74.2, -49.8, 1.7, 18.3, 11.15, 5.5, 0.8, THATCH_L)
    # hanging BAR sign on the open side
    dk.box(p, (-47.8, 11.1, 10), (0.4, 2.2, 7.0), RED, jitter=0.04, name="Sign")
    for z in (6.8, 13.2):
        dk.box(p, (-47.8, 10.0, z), (0.4, 1.0, 0.4), WOOD_D, name="SignPost")
    for ch, zl in (("B", 7.4), ("A", 9.2), ("R", 11.0)):
        pixel_letter(p, ch, -47.45, 10.2, zl, 0.38, CREAM)
    return p


# ---- PART: Kiosk -------------------------------------------------------------------------------------------------
ICE_PINK = (255, 160, 190); ICE_MINT = (150, 225, 190); ICE_CREAM = (255, 235, 180); WAFFLE = (212, 160, 92)


def build_Kiosk():
    p = dk.Part("Kiosk")
    dk.box(p, (30, 0.25, 40), (14, 0.5, 10), WOOD_D, name="DeckBase")
    planks(p, 23, 37, 35, 45, 0.45, 0.62, 6, 'x', WOOD, 0.12, 0.07, "DeckPlank")
    # yellow walls: back wall flat, side walls follow the slope of the awning
    back = strips(p, (30, 4.8, 44.6), (14, 8.6, 0.8), YEL, 7, 'x', 0.05, "WallBack")
    recolor(back, lambda c, n, k: YEL if int((c[0] - 23) / 2) % 2 == 0 else dk.shade(YEL, 0.9), 0.02)
    for x in (23.4, 36.6):
        slab(p, [(0.5, 35.5), (0.5, 44.5), (9.1, 44.5), (8.55, 35.5)], 0.8, 'yz', x, YEL, 0.05, name="WallSide")
    for x in (22.7, 37.3):
        dk.box(p, (x, 4.25, 33.5), (0.6, 8.0, 0.6), WOOD_D, jitter=0.05, name="Post")
    # candy-striped counter with white top
    cs = strips(p, (30, 1.7, 35.4), (14, 2.2, 1.6), RED, 14, 'x', 0.02, "Counter")
    recolor(cs, lambda c, n, k: RED if int(c[0] - 23) % 2 == 0 else WHITE, 0.02)
    dk.box(p, (30, 3.0, 35.4), (14.8, 0.4, 2.4), WHITE, jitter=0.03, name="CounterTop")
    # ice cream cones in a wooden rack, cups
    dk.box(p, (29.2, 3.45, 35.4), (5.2, 0.5, 1.3), WOOD, name="Rack")
    for x, cols in [(27.6, [ICE_PINK]), (29.2, [ICE_MINT, ICE_CREAM]), (30.8, [(255, 190, 90)])]:
        lathe(p, (x, 3.6, 35.4), [(0, 0), (0.55, 1.6)], 6, WAFFLE, 0.05, name="Cone")
        for i, col in enumerate(cols):
            blob(p, (x, 5.45 + i * 1.0, 35.4), 0.68, col, sides=6, jitter=0.03, name="Scoop")
    cup(p, 33.4, 3.2, 35.2, RED, h=1.0, r=0.5)
    cup(p, 34.4, 3.2, 35.7, WHITE, h=1.0, r=0.5)
    lathe(p, (36.0, 3.2, 35.4), [(0.5, 0), (0.5, 0.9), (0, 0.9)], 6, GLASS_C, 0.0, name="TipJar", cap0=False)
    # wall decorations: chalk menu, jar shelf
    dk.box(p, (26.5, 5.5, 44.1), (5.2, 3.4, 0.2), (52, 74, 66), name="Menu")
    for (c, s) in [((26.5, 7.3, 44.0), (5.6, 0.3, 0.3)), ((26.5, 3.7, 44.0), (5.6, 0.3, 0.3)), ((23.8, 5.5, 44.0), (0.3, 3.7, 0.3)), ((29.2, 5.5, 44.0), (0.3, 3.7, 0.3))]:
        dk.box(p, c, s, WOOD_D, name="MenuFrame")
    for i, w in enumerate((3.6, 3.0, 3.3)):
        dk.box(p, (26.5 - (3.6 - w) / 2, 6.4 - i * 0.9, 43.95), (w, 0.16, 0.1), WHITE, name="Chalk")
    dk.box(p, (34.0, 4.6, 43.9), (4.6, 0.3, 0.8), WOOD, name="Shelf")
    for x, col in [(32.4, TEAL), (33.6, YEL), (34.8, RED), (36.0, TEAL)]:
        cup(p, x, 4.75, 43.9, col, h=1.0, r=0.32)
    # freezer chest with lid on the left
    dk.box(p, (26, 1.8, 37), (3, 2.4, 3), TEAL, jitter=0.03, name="Freezer")
    frustum(p, 26, 37, 3.0, 3.4, 3.3, 3.3, 3.0, 3.0, WHITE, 0.02, name="FreezerLid")
    dk.box(p, (26, 3.65, 37), (1.2, 0.2, 0.4), RED, name="FreezerHandle")
    dk.box(p, (26, 1.9, 35.48), (1.8, 1.0, 0.06), WHITE, name="Sticker")
    # hanging ice cream cone sign under the awning
    slab(p, [(33.3, 6.1), (35.1, 6.1), (34.2, 3.7)], 0.3, 'xy', 33.4, WAFFLE, 0.04, name="SignCone")
    blob(p, (34.2, 6.75, 33.4), 0.95, ICE_PINK, sides=6, jitter=0.03, name="SignScoop")
    blob(p, (34.2, 7.75, 33.4), 0.28, RED, sides=5, name="Cherry")
    # big ice cream icon on the back wall (the side facing the road)
    slab(p, [(28.7, 5.3), (31.3, 5.3), (30.0, 1.5)], 0.2, 'xy', 45.1, WAFFLE, 0.04, name="IconCone")
    blob(p, (30.0, 6.4, 45.2), 1.3, ICE_PINK, sides=6, jitter=0.03, name="IconScoop")
    blob(p, (30.0, 8.0, 45.2), 1.0, ICE_MINT, sides=6, jitter=0.03, name="IconScoop")
    # striped awning sloping down to a scalloped front edge
    for i in range(8):
        col = RED if i % 2 == 0 else WHITE
        xc = 23 + 2 * i
        slab(p, [(9.8, 46), (9.0, 34.0), (8.35, 32.7), (7.95, 32.9), (8.55, 34.1), (9.3, 46)], 2.0, 'yz', xc, col, 0.03, name="Awning")
        slab(p, [(xc - 1, 7.97), (xc + 1, 7.97), (xc, 7.3)], 0.25, 'xy', 32.85, col, 0.03, name="Scallop")
    return p


# ---- PART: PalmTrees ---------------------------------------------------------------------------------------------
BARK = (156, 114, 68); BARK_D = (96, 66, 40); NUT = (176, 122, 62)


def palm(p, cx, cz, H, cy, yaw0, lean, n_big=10):
    lx, lz = lean
    fr = [(0, 1.3), (0.05, 1.05), (0.2, 0.92), (0.4, 0.84), (0.6, 0.8), (0.8, 0.8), (0.93, 0.88), (1.0, 0.7)]
    prof = [(r, H * f, lx * f * f, lz * f * f) for f, r in fr]
    tr = lathe(p, (cx, 0.0, cz), prof, 6, BARK, 0.04, name="Trunk")
    recolor(tr, lambda c, n, k: BARK_D if (k // 6) % 2 else BARK, 0.04)
    top = (cx + lx, cy, cz + lz)
    lathe(p, (cx, 0.0, cz), [(2.4, 0), (1.6, 0.3), (0, 0.5)], 7, SAND_D, 0.04, name="Mound")
    for k in range(3):
        a = math.radians(yaw0 + 18 + 120 * k)
        lathe(p, (top[0] + 1.2 * math.cos(a), cy - 0.8, top[2] + 1.2 * math.sin(a)), [(0, 0), (1.1, 1.1), (0, 2.2)], 6, NUT, 0.05, name="Coconut")
    cols = [GREEN, GREEN_L, GREEN_D]
    for k in range(n_big):
        yaw = yaw0 + 360 / n_big * k
        L = 7.0 if k % 2 == 0 else 6.6
        blade(p, (top[0], cy + 0.1, top[2]), yaw, L, 3.6, 2.4 + 0.5 * (k % 3), 5.0 + 0.5 * (k % 2), cols[k % 3], segs=5, notch=True, name="Frond")
    for k in range(2):
        blade(p, (top[0], cy + 0.1, top[2]), yaw0 + 25 + 160 * k, 4.2, 1.8, 3.6, 1.2, GREEN_L, segs=3, name="Frond")


def build_PalmTrees():
    p = dk.Part("PalmTrees")
    palm(p, -42, -8, 18.0, 18.5, 0, (1.0, 1.2))
    palm(p, -56, -15, 21.0, 21.2, 20, (-1.2, 0.8))
    palm(p, -34, -23, 17.0, 17.4, 10, (1.3, -0.9))
    return p


# ---- PART: Parasols ----------------------------------------------------------------------------------------------
def umbrella(p, cx, cz, y_top, y_rim, Rr, c1, c2, n=8):
    ym = y_rim + (y_top - y_rim) * 0.6
    pts = [(cx, y_top, cz)]
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + 0.55 * Rr * math.cos(a), ym, cz + 0.55 * Rr * math.sin(a)))
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + Rr * math.cos(a), y_rim, cz + Rr * math.sin(a)))
    pts.append((cx, y_top - 0.4, cz))
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + 0.55 * Rr * math.cos(a), ym - 0.35, cz + 0.55 * Rr * math.sin(a)))
    for i in range(n):
        a = 2 * pi * i / n
        pts.append((cx + Rr * math.cos(a), y_rim - 0.3, cz + Rr * math.sin(a)))
    M = lambda i: 1 + i % n
    Rm = lambda i: 1 + n + i % n
    A2 = 1 + 2 * n
    M2 = lambda i: A2 + 1 + i % n
    R2 = lambda i: A2 + 1 + n + i % n
    faces = []
    for i in range(n):
        faces += [(0, M(i), M(i + 1)), (M(i), M(i + 1), Rm(i + 1), Rm(i)),
                  (A2, M2(i), M2(i + 1)), (M2(i), M2(i + 1), R2(i + 1), R2(i)),
                  (Rm(i), Rm(i + 1), R2(i + 1), R2(i))]
    o = _obj(p, "Canopy", pts, faces, c1, 0.03)

    def col(c, nn, k):
        base = c1 if (k // 5) % 2 == 0 else c2
        return dk.shade(base, 0.78) if (k % 5) in (2, 3) else base
    recolor(o, col, 0.02)
    for i in range(n):
        a0, a1 = 2 * pi * i / n, 2 * pi * (i + 1) / n
        am = (a0 + a1) / 2
        A = (cx + Rr * math.cos(a0), y_rim - 0.15, cz + Rr * math.sin(a0))
        B = (cx + Rr * math.cos(a1), y_rim - 0.15, cz + Rr * math.sin(a1))
        T = (cx + (Rr + 0.1) * math.cos(am) * 0.97, y_rim - 1.0, cz + (Rr + 0.1) * math.sin(am) * 0.97)
        D = (cx + (Rr - 0.5) * math.cos(am), y_rim - 0.25, cz + (Rr - 0.5) * math.sin(am))
        tetra(p, A, B, T, D, c1 if i % 2 == 0 else c2, 0.03, name="RimTab")
    return o


def lounger(p, x, z0, color, stripe):
    for dx in (-1.2, 1.2):
        dk.box(p, (x + dx, 0.5, z0 + 3.9), (0.3, 0.5, 5.6), WOOD_D, name="Rail")
    for dx in (-1.2, 1.2):
        for dz in (1.7, 6.0):
            dk.box(p, (x + dx, 0.22, z0 + dz), (0.3, 0.45, 0.3), WOOD_D, name="Leg")
    dk.box(p, (x, 1.1, z0 + 4.0), (3.0, 0.5, 5.0), color, jitter=0.04, name="Mattress")
    dk.box(p, (x, 1.37, z0 + 3.0), (3.02, 0.08, 0.5), stripe, name="Stripe")
    dk.box(p, (x, 1.37, z0 + 5.0), (3.02, 0.08, 0.5), stripe, name="Stripe")
    ang = 32
    dk.box(p, (x, 1.35 + 1.3 * math.sin(math.radians(ang)) + 0.1, z0 + 1.5 - 1.3 * math.cos(math.radians(ang))), (3.0, 0.5, 2.9), color, rot=(ang, 0, 0), jitter=0.04, name="Backrest")
    dk.box(p, (x, 2.7, z0 - 0.1), (2.2, 0.4, 0.9), WHITE, rot=(ang, 0, 0), jitter=0.02, name="Pillow")


def build_Parasols():
    p = dk.Part("Parasols")
    for (x, z, c1, c2) in [(54, 26, RED, WHITE), (62, 16, YEL, WHITE)]:
        post(p, x, z, 0.0, 14.2, 0.28, WHITE, 6, name="Pole")
        post(p, x, z, 0.0, 0.5, 1.3, c1, 8, top_r=1.0, name="PoleBase")
        umbrella(p, x, z, 14.55, 12.9, 6.0, c1, c2)
        dk.cyl(p, (x, 14.6, z), 0.3, 0.4, WHITE, verts=5, top_radius=0.0, name="Finial")
    lounger(p, 47, 19.0, TEAL, WHITE)
    lounger(p, 53, 17.0, WHITE, RED)
    lounger(p, 59, 19.0, RED, WHITE)
    # sandcastle with a bucket and a beach ball in front of the loungers
    cx, cz = 49.5, 13.2
    dk.box(p, (cx, 0.75, cz), (2.8, 0.9, 2.8), SAND_D, jitter=0.05, name="CastleBase")
    for (dx, dz) in [(-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)]:
        dk.cyl(p, (cx + dx, 1.15, cz + dz), 0.5, 1.7, SAND_M, verts=5, jitter=0.05, name="CastleTower")
        dk.cyl(p, (cx + dx, 2.25, cz + dz), 0.62, 0.5, SAND_D, verts=5, top_radius=0.0, jitter=0.05, name="CastleCap")
    dk.cyl(p, (cx, 1.9, cz), 0.65, 2.6, SAND_M, verts=5, jitter=0.05, name="Keep")
    dk.cyl(p, (cx, 3.55, cz), 0.8, 0.8, RED, verts=5, top_radius=0.0, name="KeepRoof")
    dk.box(p, (cx, 4.35, cz), (0.08, 0.8, 0.08), WOOD_D, name="FlagStick")
    dk.cyl(p, (cx + 2.9, 0.65, cz - 0.8), 0.4, 0.7, YEL, verts=6, top_radius=0.55, name="Bucket")
    ball = blob(p, (cx + 5.6, 1.05, cz + 0.2), 0.75, RED, sides=6, name="BeachBall")
    recolor(ball, lambda c, n, k: [RED, WHITE, YEL][(k % 6) % 3], 0.02)
    # little tables with a drink between the loungers
    for (x, z, col) in [(50, 21.5, YEL), (56, 20.5, RED)]:
        post(p, x, z, 0.0, 1.2, 0.16, WOOD_D, 5, name="TableLeg")
        post(p, x, z, 1.1, 1.3, 0.95, WOOD, 8, name="TableTop")
        cup(p, x, 1.3, z, col, h=0.9, r=0.28, sides=5)
    return p


# ---- PART: Surfboards --------------------------------------------------------------------------------------------
def rot2(u, v, deg):
    a = math.radians(deg)
    return (u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a))


BOARD_PROF = [(-5.5, 0.62), (-5.2, 0.8), (-4.0, 0.95), (-1.5, 1.0), (1.2, 0.95), (3.2, 0.78), (4.5, 0.5), (5.2, 0.22), (5.5, 0.0)]


def board_w(v):
    for (v0, w0), (v1, w1) in zip(BOARD_PROF, BOARD_PROF[1:]):
        if v0 <= v <= v1:
            return w0 + (w1 - w0) * (v - v0) / max(v1 - v0, 1e-6)
    return 0.0


def board_poly(v0, v1, inset=0.0):
    vs = [v0] + [v for v, _ in BOARD_PROF if v0 < v < v1] + [v1]
    left = [(-max(board_w(v) - inset, 0.0), v) for v in vs]
    right = [(max(board_w(v) - inset, 0.0), v) for v in reversed(vs)]
    pts = left + right
    out = []
    for q in pts:                                     # drop duplicate points (tip)
        if not out or abs(q[0] - out[-1][0]) > 1e-6 or abs(q[1] - out[-1][1]) > 1e-6:
            out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def surfboard(p, x, tilt, color, stripe, z=-26.6, cy=5.5):
    loc = board_poly(-5.5, 5.5)
    slab(p, [(x + rot2(u, v, tilt)[0], cy + rot2(u, v, tilt)[1]) for u, v in loc], 0.6, 'xy', z, color, 0.03, name="Board")
    fz = z - 0.32
    # two-tone: coloured tail and nose caps drawn on the face, centre stringer, star logo
    for (v0, v1) in ((-5.5, -2.6), (3.6, 5.5)):
        slab(p, [(x + rot2(u, v, tilt)[0], cy + rot2(u, v, tilt)[1]) for u, v in board_poly(v0, v1, 0.12)], 0.07, 'xy', fz + 0.02, stripe, 0.02, name="Cap")
    cu, cv = rot2(0, 0.6, tilt)
    slab(p, [(x + cu + rot2(a, b, tilt)[0], cy + cv + rot2(a, b, tilt)[1]) for a, b in star(0, 0, 0.62, 0.27, 5, pi / 2)], 0.08, 'xy', fz, dk.shade(stripe, 1.0), 0.0, name="Logo")
    # fin on the back of the tail
    slab(p, [(cy + rot2(0, -5.3, tilt)[1], z + 0.3), (cy + rot2(0, -3.3, tilt)[1], z + 0.3), (cy + rot2(0, -5.3, tilt)[1], z + 1.05)],
         0.18, 'yz', x + rot2(0, -4.5, tilt)[0], dk.shade(stripe, 0.85), name="Fin")


def build_Surfboards():
    p = dk.Part("Surfboards")
    for x, t, c, s in [(60, -6, RED, WHITE), (62.8, -2, YEL, RED), (65.6, 2, TEAL, WHITE), (68.4, 6, WHITE, TEAL)]:
        surfboard(p, x, t, c, s)
    for x in (58.5, 69.5):
        dk.box(p, (x, 3.8, -26), (1.2, 7.6, 1.2), WOOD_D, jitter=0.05, name="RackPost")
        dk.box(p, (x, 7.75, -26), (1.5, 0.35, 1.5), WOOD, name="RackCap")
        dk.box(p, (x, 0.2, -26), (2.0, 0.4, 1.6), WOOD_D, name="RackFoot")
    dk.box(p, (64, 3.4, -26), (11, 0.8, 0.8), WOOD, name="RackBar")
    dk.box(p, (64, 6.6, -26), (11, 0.7, 0.7), WOOD, name="RackBar")
    # rope ties where the boards meet the bars
    for x in (60, 62.8, 65.6, 68.4):
        dk.box(p, (x, 3.4, -26.45), (0.5, 0.5, 0.2), (226, 208, 160), name="Tie")
    return p


# ---- PART: Volleyball --------------------------------------------------------------------------------------------
def build_Volleyball():
    p = dk.Part("Volleyball")
    flat(p, [(-24.8, -41.8), (0.8, -41.8), (0.8, -30.2), (-24.8, -30.2)], 0.31, (246, 228, 168), 0.02, name="CourtSand")
    for (x0, x1, z0, z1) in [(-25.2, 1.2, -30.2, -29.8), (-25.2, 1.2, -42.2, -41.8), (-25.2, -24.8, -42.2, -29.8), (0.8, 1.2, -42.2, -29.8),
                             (-25.2, 1.2, -36.15, -35.85)]:
        slab(p, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 0.07, 'xz', 0.31, WHITE, name="Line")
    for x in (-22, -2):
        dk.box(p, (x, 0.15, -36), (1.8, 0.3, 1.8), WOOD_D, name="PostBase")
        post(p, x, -36, 0.0, 9.55, 0.5, WOOD_L, 8, name="NetPost")
        post(p, x, -36, 2.0, 6.2, 0.78, RED, 8, name="PostPad")
        dk.cyl(p, (x, 9.78, -36), 0.6, 0.45, RED_D, verts=8, top_radius=0.1, name="PostCap")
    # net: tapes, strands and verticals leave real holes
    dk.box(p, (-12, 9.3, -36), (20, 0.5, 0.5), RED, name="NetTop")
    dk.box(p, (-12, 6.25, -36), (20, 0.3, 0.25), WHITE, name="NetBottom")
    for y in (7.15, 8.2):
        dk.box(p, (-12, y, -36), (20, 0.14, 0.14), WHITE, name="NetStrand")
    for i in range(10):
        dk.box(p, (-21 + 2 * i, 7.8, -36), (0.16, 3.0, 0.14), WHITE, name="NetCord")
    # beach ball
    ball = blob(p, (-7, 1.45, -32), 1.1, YEL, sides=8, name="Ball")
    recolor(ball, lambda c, n, k: [YEL, WHITE, TEAL, WHITE][(k % 8) % 4], 0.02)
    # corner flags
    for (x, z) in [(-24.8, -30.4), (0.8, -30.4), (-24.8, -41.6), (0.8, -41.6)]:
        dk.box(p, (x, 1.2, z), (0.2, 2.4, 0.2), WHITE, name="FlagPole")
        slab(p, [(x, 2.35), (x + 1.1, 1.95), (x, 1.55)], 0.1, 'xy', z, RED, name="Flag")
    return p


# ---- PART: Boat --------------------------------------------------------------------------------------------------
HULL = (150, 98, 56)


def build_Boat():
    p = dk.Part("Boat")
    X = 79.0
    # stations: z, half width at the sheer, half width at the keel, keel y, sheer y
    st = [(23.0, 3.6, 2.3, 0.4, 3.3), (25.0, 4.1, 2.5, 0.0, 3.1), (30.0, 4.3, 2.6, 0.0, 2.9), (35.0, 4.3, 2.6, 0.0, 2.9),
          (39.0, 3.8, 2.0, 0.0, 3.2), (42.5, 2.4, 1.0, 0.4, 3.7), (46.43, 0.12, 0.1, 2.0, 4.0)]
    rings = []
    for (z, wt, wb, yb, ys) in st:
        yf = ys - 0.9
        wm = (wt + wb) / 2 + 0.2
        ym = (yf + yb) / 2 + 0.1
        rings.append([(X - wt, yf, z), (X - wm, ym, z), (X - wb, yb, z), (X + wb, yb, z), (X + wm, ym, z), (X + wt, yf, z)])
    hull = loft(p, rings, HULL, 0.07, name="Hull")
    # planking: cream upper strakes, brown lower hull, light wooden floor
    recolor(hull, lambda c, n, k: (238, 232, 214) if k % 6 in (0, 4) else ((214, 172, 112) if k % 6 == 5 else None), 0.04)
    # red gunwale ribbons, port and starboard, merging at the bow
    for side in (-1, 1):
        rr = []
        for (z, wt, wb, yb, ys) in st:
            yf = ys - 0.9
            wi = min(0.55, wt * 0.9)
            rr.append([(X + side * wt, yf, z), (X + side * wt, ys, z), (X + side * (wt - wi), ys, z), (X + side * (wt - wi), yf, z)])
        loft(p, rr, RED, 0.04, name="Gunwale")
    dk.box(p, (X, 2.55, 23.25), (7.4, 1.5, 0.6), RED, jitter=0.04, name="Transom")
    # seats
    dk.box(p, (X, 2.45, 30.0), (7.5, 0.4, 1.3), WOOD_D, jitter=0.04, name="Thwart")
    dk.box(p, (X, 2.45, 38.0), (6.3, 0.4, 1.3), WOOD_D, jitter=0.04, name="Thwart")
    # mast, boom, sails (with a belly so they catch the light)
    post(p, X, 33.0, 1.9, 17.0, 0.38, WOOD_D, 6, name="Mast")
    dk.cyl(p, (X, 4.35, 29.3), 0.2, 7.6, WOOD_D, axis='z', verts=5, name="Boom")
    sail(p, (X, 4.5, 32.7), (X, 16.6, 32.7), (X, 4.5, 25.4), 0.9, WHITE, name="Mainsail")
    slab(p, star(7.6, 31.0, 1.8, 0.75, 5, pi / 2), 0.5, 'yz', X, YEL, 0.02, name="Emblem")
    sail(p, (X, 15.4, 33.5), (X, 3.9, 43.4), (X, 4.9, 34.3), -0.8, RED, name="Jib")
    slab(p, [(16.05, 33.0), (16.95, 33.0), (16.5, 30.8)], 0.14, 'yz', X, RED, name="Pennant")
    # bunting along the forestay
    bcols = [YEL, WHITE, TEAL, RED]
    for i in range(8):
        t0, t1 = 0.12 + 0.105 * i, 0.12 + 0.105 * (i + 1)
        ya, za = 16.8 + (3.7 - 16.8) * t0, 33.0 + (43.3 - 33.0) * t0
        yb, zb = 16.8 + (3.7 - 16.8) * t1, 33.0 + (43.3 - 33.0) * t1
        slab(p, [(ya, za), (yb, zb), ((ya + yb) / 2 - 1.1, (za + zb) / 2)], 0.1, 'yz', X, bcols[i % 4], name="BoatFlag")
    # foam collar where the hull meets the sea
    for side in (-1, 1):
        inner, outer = [], []
        for z in [24.5 + 2.4 * k for k in range(9)]:
            wt = 2.6 if z < 41 else max(0.3, 2.6 - (z - 41) * 0.5)
            inner.append((X + side * (wt - 0.05), z))
            outer.append((X + side * (wt + 0.75 + (0.35 if int((z - 24.5) / 2.4) % 2 else 0.0)), z))
        flat(p, inner + list(reversed(outer)), 0.52, WHITE, 0.03, name="FoamCollar")
    # forestay and backstay
    for (ya, za, yb, zb) in [(16.8, 33.0, 3.7, 43.3), (16.8, 33.0, 3.4, 23.4)]:
        L = math.hypot(yb - ya, zb - za)
        dk.box(p, (X, (ya + yb) / 2, (za + zb) / 2), (0.14, L, 0.14), WOOD_D, rot=(math.degrees(math.atan2(zb - za, yb - ya)), 0, 0), name="Stay")
    # small props: rope coil, oar, life vest
    torus(p, (X - 1.8, 2.2, 40.4), 0.62, 0.17, 'y', 6, 4, (226, 208, 160), name="RopeCoil")
    dk.cyl(p, (X + 2.0, 2.2, 27.4), 0.1, 5.4, WOOD_L, axis='z', verts=4, name="Oar")
    dk.box(p, (X + 2.0, 2.2, 24.2), (0.5, 0.1, 1.5), WOOD_L, name="OarBlade")
    dk.box(p, (X - 2.2, 2.85, 30.0), (1.4, 0.5, 0.9), ORANGE, jitter=0.04, name="Vest")
    return p


# ---- PART: TikiCooler --------------------------------------------------------------------------------------------
BAMBOO = (178, 132, 76)


def torch(p, x, z):
    post(p, x, z, 0.0, 6.4, 0.4, BAMBOO, 6, jitter=0.05, name="TorchPole")
    for y in (1.5, 3.4, 5.2):
        post(p, x, z, y - 0.14, y + 0.14, 0.53, WOOD_D, 6, name="TorchBand")
    dk.cyl(p, (x, 6.65, z), 0.45, 0.9, WOOD_D, verts=6, top_radius=0.7, jitter=0.04, name="TorchCup")
    # three flame tongues
    for (dx, dz, h, r) in [(0, 0, 1.4, 0.5), (0.3, -0.12, 0.95, 0.3), (-0.28, 0.14, 0.85, 0.28)]:
        lathe(p, (x + dx, 7.0, z + dz), [(0, 0), (r, h * 0.3), (r * 0.7, h * 0.65), (0, h)], 4, (255, 150, 40), 0.04, name="Flame", cap0=False)
    lathe(p, (x, 7.05, z), [(0, 0), (0.3, 0.25), (0.22, 0.6), (0, 1.0)], 4, (255, 226, 96), 0.03, name="FlameCore", cap0=False)


def build_TikiCooler():
    p = dk.Part("TikiCooler")
    for (x, z) in [(-70, -26), (-58, -26), (-70, -40), (-58, -40)]:
        torch(p, x, z)
    ROPE = (208, 178, 112)
    for z in (-26, -40):
        dk.box(p, (-64, 4.9, z), (12, 0.14, 0.14), ROPE, name="Rope")
    for x in (-70, -58):
        dk.box(p, (x, 4.9, -33), (0.14, 0.14, 14), ROPE, name="Rope")
    # bunting on all four ropes
    cols = [RED, YEL, TEAL, WHITE]
    for i in range(5):
        t = -4.8 + 2.4 * i
        for z in (-26, -40):
            pennant(p, -64 + t, 4.85, z, 1.0, 1.0, cols[i % 4])
        for x in (-70, -58):
            slab(p, [(4.85, -33 + t - 0.5), (4.85, -33 + t + 0.5), (3.85, -33 + t)], 0.1, 'yz', x, cols[(i + 1) % 4], name="Pennant")
    # cooler box
    frustum(p, -64, -33, 0.0, 3.6, 5.8, 3.4, 6.0, 3.6, TEAL, 0.03, name="Cooler")
    frustum(p, -64, -33, 3.6, 4.2, 6.4, 4.0, 6.0, 3.6, WHITE, 0.02, name="CoolerLid")
    dk.box(p, (-64, 4.78, -33), (0.5, 0.3, 2.6), RED, name="Handle")
    for dz in (-1.1, 1.1):
        dk.box(p, (-64, 4.45, -33 + dz), (0.5, 0.5, 0.4), RED, name="HandleLeg")
    for x in (-67.35, -60.65):
        dk.box(p, (x, 2.7, -33), (0.35, 0.4, 1.6), RED, name="SideGrip")
    for x in (-65.4, -62.6):
        dk.box(p, (x, 3.75, -35.0), (0.7, 0.7, 0.3), STEEL, name="Latch")
    fish = [(-1.15, 0), (-0.55, 0.5), (0.4, 0.5), (0.75, 0.15), (1.2, 0.5), (1.2, -0.5), (0.75, -0.15), (0.4, -0.5), (-0.55, -0.5)]
    slab(p, [(-64 + 1.2 * u, 1.7 + 1.2 * v) for u, v in fish], 0.1, 'xy', -34.82, WHITE, name="Fish")
    # beach towel, coconut drinks and bottles in the sand
    ta = math.radians(12)
    for i in range(5):
        x0 = -2.25 + i * 0.9
        q = [(x0, -1.6), (x0 + 0.9, -1.6), (x0 + 0.9, 1.6), (x0, 1.6)]
        flat(p, [(-64 + u * math.cos(ta) - v * math.sin(ta), -28.6 + u * math.sin(ta) + v * math.cos(ta)) for u, v in q],
             0.32, RED if i % 2 == 0 else WHITE, 0.02, name="Towel")
    for (x, z) in [(-59.8, -34.5), (-60.6, -30.8)]:
        blob(p, (x, 0.6, z), 0.62, (120, 84, 50), sides=6, name="CoconutCup")
        dk.box(p, (x + 0.1, 1.55, z), (0.14, 1.2, 0.14), RED, rot=(0, 0, 14), name="Straw")
    bottle(p, -67.9, 0.0, -36.5, GLASS_G, h=2.4)
    bottle(p, -67.0, 0.0, -37.4, GLASS_A, h=2.4)
    return p


# ---- PART: Lifeguard ---------------------------------------------------------------------------------------------
def build_Lifeguard():
    p = dk.Part("Lifeguard")
    for (x, z) in [(56, -44), (64, -44), (56, -36), (64, -36)]:
        dk.box(p, (x, 3.85, z), (1.2, 8.3, 1.2), WHITE, jitter=0.03, name="Leg")
        dk.box(p, (x, 0.05, z), (2.0, 0.4, 2.0), WOOD_D, name="Footing")
    for x in (55.2, 64.8):
        dk.box(p, (x, 11.4, -35.0), (0.6, 5.2, 0.6), WHITE, name="FrontPost")
    BL = 10.7
    for sgn in (1, -1):
        for x in (56, 64):
            dk.box(p, (x, 4.2, -40), (0.35, BL, 0.35), WHITE, rot=(sgn * 48, 0, 0), name="Brace")
        dk.box(p, (60, 4.2, -44), (0.35, BL, 0.35), WHITE, rot=(0, 0, sgn * 48), name="Brace")
    # platform
    dk.box(p, (60, 8.25, -40), (11, 0.5, 11), WOOD_D, name="DeckBase")
    planks(p, 54.5, 65.5, -45.5, -34.5, 8.5, 8.8, 5, 'x', WOOD, 0.14, 0.07, "DeckPlank")
    # red cabin walls with white stripes
    strips(p, (60, 11.2, -45), (11, 5, 0.6), RED, 6, 'x', 0.05, "WallBack")
    strips(p, (55, 11.2, -40), (0.6, 5, 11), RED, 5, 'z', 0.05, "WallLeft")
    strips(p, (65, 11.2, -40), (0.6, 5, 11), RED, 5, 'z', 0.05, "WallRight")
    dk.box(p, (60, 12.6, -45.35), (10.8, 0.5, 0.15), WHITE, name="Stripe")
    dk.box(p, (54.65, 12.6, -40), (0.15, 0.5, 10.8), WHITE, name="Stripe")
    dk.box(p, (65.35, 12.6, -40), (0.15, 0.5, 10.8), WHITE, name="Stripe")
    dk.box(p, (60, 10.4, -45.45), (0.9, 3.0, 0.15), WHITE, name="Cross")
    dk.box(p, (60, 10.4, -45.45), (3.0, 0.9, 0.15), WHITE, name="Cross")
    # porthole on the left wall
    lathe(p, (54.72, 11.0, -40), [(1.0, 0), (1.0, -0.2)], 8, WHITE, 0.0, axis='x', name="Porthole")
    lathe(p, (54.72, 11.0, -40), [(0.66, 0), (0.66, -0.27)], 8, (46, 96, 118), 0.0, axis='x', name="PortholeGlass")
    # front rail with gap for the ladder
    for (x0, x1) in [(55.2, 58.6), (61.4, 64.8)]:
        xc = (x0 + x1) / 2
        dk.box(p, (xc, 10.0, -34.8), (x1 - x0, 0.3, 0.3), WHITE, name="Rail")
        dk.box(p, (xc, 9.2, -34.8), (x1 - x0, 0.25, 0.25), WHITE, name="Rail")
    for x in (58.6, 61.4):
        dk.box(p, (x, 9.5, -34.8), (0.3, 1.5, 0.3), WHITE, name="RailPost")
    # ladder
    for x in (58.9, 61.1):
        dk.box(p, (x, 4.25, -34.0), (0.35, 8.6, 0.4), WOOD_D, rot=(-20, 0, 0), name="LadderRail")
    for i in range(7):
        t = -3.6 + 1.2 * i
        dk.box(p, (60, 4.25 + 0.94 * t, -34.0 - 0.342 * t), (2.0, 0.3, 0.4), WOOD_L, rot=(-20, 0, 0), name="Rung")
    # roof
    frustum(p, 60, -40, 14.0, 14.45, 14.0, 14.0, 13.4, 13.4, RED, 0.04, name="RoofTrim")
    frustum(p, 60, -40, 14.4, 14.8, 13.5, 13.5, 8.0, 8.0, WHITE, 0.03, name="Roof")
    # flag pole and waving flag
    post(p, 66.5, -45, 14.2, 19.6, 0.25, WHITE, 6, name="FlagPole")
    xs = [66.75, 68.4, 70.0, 71.5]
    dz = [0.0, 0.4, -0.3, 0.25]
    fr = []
    for x, d in zip(xs, dz):
        fr.append([(x, 17.1, -45 + d - 0.07), (x, 18.5, -45 + d - 0.07), (x, 19.9, -45 + d - 0.07), (x, 19.9, -45 + d + 0.07), (x, 18.5, -45 + d + 0.07), (x, 17.1, -45 + d + 0.07)])
    flag = loft(p, fr, YEL, 0.02, name="Flag")
    recolor(flag, lambda c, n, k: RED if c[1] < 18.5 else YEL, 0.02)
    # rescue can lying in the sand, ring buoy on the right wall
    can = lathe(p, (52.5, 0.85, -39.1), [(0, 0), (0.55, 0.25), (0.85, 0.7), (0.85, 3.5), (0.55, 3.95), (0, 4.2)], 8, RED, 0.03, axis='z', name="RescueCan")
    recolor(can, lambda c, n, k: WHITE if abs(c[2] + 37.0) < 0.5 else None, 0.02)
    torus(p, (65.65, 11.0, -40), 1.25, 0.4, 'x', 8, 4, RED, WHITE, name="RingBuoy")
    # a seagull on the roof
    sx, sy, sz = 58.0, 14.8, -37.2
    gy = sy + 0.55
    lathe(p, (sx, gy, sz + 1.1), [(0, 0), (0.38, -0.5), (0.66, -1.2), (0.58, -1.9), (0, -2.3)], 6, WHITE, 0.02, axis='z', name="GullBody", cap0=False)
    blob(p, (sx, gy + 0.55, sz - 1.25), 0.42, WHITE, sides=6, name="GullHead")
    lathe(p, (sx, gy + 0.5, sz - 1.62), [(0.14, 0), (0, -0.6)], 4, ORANGE, 0.0, axis='z', name="GullBeak", cap0=False)
    dk.box(p, (sx, gy + 0.05, sz + 1.25), (0.9, 0.12, 0.9), STEEL, rot=(-8, 0, 0), name="GullTail")
    for d in (-1, 1):
        dk.box(p, (sx + d * 0.64, gy + 0.2, sz + 0.1), (0.14, 0.5, 1.9), (206, 212, 218), rot=(0, 0, -d * 8), name="GullWing")
        dk.box(p, (sx + d * 0.66, gy + 0.2, sz + 1.05), (0.15, 0.4, 0.5), STEEL, name="GullWingTip")
        dk.box(p, (sx + d * 0.3, gy + 0.82, sz - 1.4), (0.1, 0.1, 0.1), (30, 30, 30), name="GullEye")
        post(p, sx + d * 0.25, sz - 0.2, sy, sy + 0.5, 0.06, ORANGE, 4, name="GullLeg")
    return p


BUILDERS = [("SandFloor", build_SandFloor), ("BarHut", build_BarHut), ("Kiosk", build_Kiosk), ("PalmTrees", build_PalmTrees),
            ("Parasols", build_Parasols), ("Surfboards", build_Surfboards), ("Volleyball", build_Volleyball), ("Boat", build_Boat),
            ("TikiCooler", build_TikiCooler), ("Lifeguard", build_Lifeguard)]


# ---- pipeline ----------------------------------------------------------------------------------------------------
def shiba_spot(part_id, bp, lo, hi):
    if part_id == "SandFloor":
        return bp
    return {"Shiba": {"Position": [hi[0] + 5.5, (lo[2] + hi[2]) / 2], "Facing": 180}}


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
    bp = dk.load_blueprint(os.path.join(HERE, "blueprint_BeachBar.json"))
    stats = []
    allm = []
    for pid, fn in BUILDERS:
        if ONLY and pid not in ONLY:
            continue
        part = fn()
        pcs = dk.blueprint_part(bp, pid)["Pieces"]
        box = roblox_box(pcs)
        if os.environ.get("BB_COUNT"):
            cnt = {}
            for o in part.objs:
                k = o.name.rstrip("0123456789.")
                cnt[k] = cnt.get(k, 0) + sum(len(q.vertices) - 2 for q in o.data.polygons)
            print("COUNT", pid, sorted(cnt.items(), key=lambda kv: -kv[1])[:14])
        drop_ground_faces(part)
        fit(part, box)
        meshes = dk.finish(part, KEY)
        tris = sum(len(q.vertices) - 2 for m in meshes for q in m.data.polygons)
        stats.append((pid, len(meshes), tris))
        lo, hi = true_bounds(meshes)
        dk.preview(part, f"preview_{pid}.png", with_shiba=shiba_spot(pid, bp, lo, hi))
        if DBG:
            for k, az in enumerate((35, 215, 125)):
                o2 = dk.OUT
                dk.OUT = DBG
                dk.preview(part, f"dbg_{pid}_{k}.png", with_shiba=None, azimuth=az, elevation=24)
                dk.OUT = o2
        allm += meshes
        dk.hide(meshes)
    if not ONLY:
        dk.hide(allm, False)
        dk.preview(allm, "stage_BeachBar_34.png", with_shiba=bp, azimuth=35, elevation=32, size=(1600, 1000))
        dk.preview(allm, "stage_BeachBar_top.png", with_shiba=bp, azimuth=0, top=True, size=(1600, 1000))
        stack_images(out, "stage_BeachBar_34.png", "stage_BeachBar_top.png", "stage_BeachBar.png")
    for s in stats:
        print("STAT %-11s meshes=%d tris=%d" % s)


main()
