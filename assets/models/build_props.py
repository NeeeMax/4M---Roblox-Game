import bpy, bmesh, math, sys, os, random, colorsys
from mathutils import Vector, Matrix, Euler
# World props for GET BONKED (every Prop_* / Trophy_* / Platform_* name the code asks for), low-poly and faceted
# like the tier Shibas: flat-shaded primitives, colours baked into the vertex colour attribute "Col" (Roblox ignores
# FBX material colours). The Shiba statue, the Rainbow trophy and the platform previews reuse the dog from
# shiba_bonk_default.blend, so the script runs with that file open.
#
# Units while building: studs (the size the game shows them at). Z is up, the model's front is -Y (Roblox -Z /
# LookVector after import). The FBX files are written at 1/4 scale (4 studs per unit, like the Shiba files); the game
# scales every prop to the height it asks for anyway.
#
# Named parts (separate meshes in the FBX, the code looks for them by name):
#   Body        everything else
#   Glow        Prop_Lamp: the bulb; PropService makes it Neon and puts the lamp's PointLight in it
#   StandPoint  Platform_*: tiny marker at the centre of the surface the Shiba stands on (NPCShooterService scales
#               and places the platform by it, then hides it)
#
# Usage:
#   blender --background --disable-autoexec shiba_bonk_default.blend --python build_props.py -- <output folder>
#       [<preview folder>] [<comma separated names to build, default all>]
# Writes <Name>.fbx per model and Props_preview.png (contact sheet of all models) into the output folder; the
# per-group sheets and single tiles go to the preview folder (default: the output folder's "_preview" subfolder).

args = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(args[0])
PREVIEW = os.path.abspath(args[1]) if len(args) > 1 and args[1] else os.path.join(OUT, "_preview")
ONLY = set(args[2].split(",")) if len(args) > 2 and args[2] else None
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)

scene = bpy.context.scene
for o in bpy.data.objects:
    o.hide_render = True
COLL = bpy.data.collections.new("Props")
scene.collection.children.link(COLL)
MATERIAL = bpy.data.materials.new("Prop")


# ---------------------------------------------------------------------------------------------------------------
# Colours (sRGB 0-255 in, linear out, like build_shiba_tiers.py)
# ---------------------------------------------------------------------------------------------------------------
def srgb(r, g, b):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def mul(c, k):
    return tuple(max(0.0, min(1.0, x * k)) for x in c)


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return srgb(r * 255, g * 255, b * 255)


def flat(c):
    return lambda p, n, i: c


def vary(c, amount=0.08, seed=0):
    """Flat colour with a small random brightness change per face: the faceted low-poly look."""
    return lambda p, n, i: mul(c, 1 + random.Random(seed * 7919 + i).uniform(-amount, amount))


def zgrad(c0, c1, z0, z1, amount=0.06, seed=0):
    return lambda p, n, i: mul(mix(c0, c1, (p.z - z0) / (z1 - z0 + 1e-9)),
                               1 + random.Random(seed * 7919 + i).uniform(-amount, amount))


LIGHT = Vector((-0.45, -0.6, 0.75)).normalized()


def metal(c, spread=0.32, seed=0):
    """Shiny faceted metal: faces toward the key light are brighter, a little random per face."""
    def fn(p, n, i):
        k = 0.82 + spread * max(-0.4, n.dot(LIGHT)) + random.Random(seed * 31 + i).uniform(-0.04, 0.04)
        return mix(mul(c, k), (1, 1, 1), max(0.0, n.dot(LIGHT) - 0.8) * 1.2)
    return fn


def bands(z_cols, amount=0.06, seed=0):
    """Colour by height: z_cols = [(z_top_of_band, colour), ...] ascending."""
    def fn(p, n, i):
        for z, c in z_cols:
            if p.z <= z:
                return mul(c, 1 + random.Random(seed * 7919 + i).uniform(-amount, amount))
        return mul(z_cols[-1][1], 1 + random.Random(seed * 7919 + i).uniform(-amount, amount))
    return fn


# Palette
WHITE = srgb(245, 245, 250)
CREAM_W = srgb(250, 244, 225)
BLACK = srgb(28, 28, 34)
GOLD = srgb(255, 200, 50)
GOLD_DARK = srgb(215, 150, 30)
GOLD_LIGHT = srgb(255, 232, 130)
SILVER = srgb(200, 205, 220)
BRONZE = srgb(205, 127, 50)
WOOD = srgb(150, 100, 60)
WOOD_DARK = srgb(105, 68, 40)
WOOD_LIGHT = srgb(215, 170, 110)
BARK = srgb(120, 80, 48)
LEAF_DARK = srgb(46, 130, 58)
LEAF_LIGHT = srgb(140, 210, 80)
GRASS = srgb(95, 185, 85)
STONE = srgb(150, 146, 160)
STONE_DARK = srgb(92, 88, 102)
IRON = srgb(48, 50, 62)
RED = srgb(230, 55, 60)
BLUE = srgb(45, 85, 205)
GLASS = srgb(40, 55, 85)


# ---------------------------------------------------------------------------------------------------------------
# Mesh helpers. Every helper returns a new object whose transform is already baked into the mesh (identity matrix),
# painted face by face: fn(face_centre, face_normal, face_index) -> linear rgb.
# ---------------------------------------------------------------------------------------------------------------
def paint(o, fn):
    me = o.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    mw = o.matrix_world
    rot = mw.to_3x3()
    for poly in me.polygons:
        c = mw @ poly.center
        n = (rot @ poly.normal).normalized()
        col = fn(c, n, poly.index)
        if n.z < -0.55:  # undersides a touch darker: reads better from below (islands, clouds)
            col = mul(col, 0.88)
        for li in poly.loop_indices:
            attr.data[li].color = (*col, 1.0)
    me.color_attributes.active_color = attr


def xform(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    return (Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()
            @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)))


def finish(bm, M, color=None, fn=None, jit=0.0, seed=0, name="piece", clamp_z=None):
    if jit:
        rnd = random.Random(seed)
        for v in bm.verts:
            v.co += Vector((rnd.uniform(-jit, jit), rnd.uniform(-jit, jit), rnd.uniform(-jit, jit)))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    if clamp_z is not None:
        for v in bm.verts:
            if v.co.z < clamp_z:
                v.co.z = clamp_z
    if M.determinant() < 0:
        for f in bm.faces:
            f.normal_flip()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    COLL.objects.link(o)
    paint(o, fn or flat(color if color is not None else WHITE))
    return o


def cube(loc, size, color=None, rot=(0, 0, 0), fn=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect='EDGES', profile=0.5)
    return finish(bm, xform(loc, rot), color, fn)


def ico(loc, r, color=None, fn=None, sub=1, scale=(1, 1, 1), rot=(0, 0, 0), jit=0.0, seed=0, clamp_z=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    s = scale if not isinstance(scale, (int, float)) else (scale,) * 3
    return finish(bm, xform(loc, rot, (r * s[0], r * s[1], r * s[2])), color, fn, jit, seed, clamp_z=clamp_z)


def ball(loc, r, color=None, fn=None, segs=8, rings=5, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    s = scale if not isinstance(scale, (int, float)) else (scale,) * 3
    return finish(bm, xform(loc, rot, (r * s[0], r * s[1], r * s[2])), color, fn)


def cyl(loc, r, depth, color=None, fn=None, segs=8, rot=(0, 0, 0), r2=None, scale=(1, 1, 1), jit=0.0, seed=0):
    """Cylinder (or cone with r2) along local Z, centred at loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    return finish(bm, xform(loc, rot, scale), color, fn, jit, seed)


def tilt(direction):
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_euler()


def rod(a, b, r, color=None, fn=None, segs=6, r2=None):
    a, b = Vector(a), Vector(b)
    return cyl((a + b) / 2, r, (b - a).length, color, fn, segs, tilt(b - a), r2)


def lathe(profile, segs=8, color=None, fn=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), jit=0.0, seed=0,
          phase=None):
    """Surface of revolution around Z. profile: [(radius, z) or (radius, z, jitter)], bottom to top; radius 0 makes
    a point. Closed at both ends. jitter moves each vertex randomly by that fraction of its radius."""
    rnd = random.Random(seed)
    phase = math.pi / segs if phase is None else phase
    bm = bmesh.new()
    rings = []
    for pt in profile:
        r, z = pt[0], pt[1]
        j = pt[2] if len(pt) > 2 else jit
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for i in range(segs):
            a = phase + 2 * math.pi * i / segs
            rr = r * (1 + rnd.uniform(-j, j))
            zz = z + (rnd.uniform(-j, j) * r * 0.3 if j else 0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(segs):
            k = (i + 1) % segs
            if len(A) == 1:
                bm.faces.new((A[0], B[i], B[k]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[k], B[0]))
            else:
                bm.faces.new((A[i], A[k], B[k], B[i]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return finish(bm, xform(loc, rot, scale), color, fn)


def prism(pts, depth, color=None, fn=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """2D polygon in local XY, extruded along local Z (centred). Use rot=(pi/2, 0, 0) to stand it up facing -Y
    (local X stays X, local Y becomes up)."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, -depth / 2)) for x, y in pts]
    top = [bm.verts.new((x, y, depth / 2)) for x, y in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        k = (i + 1) % n
        bm.faces.new((bot[i], bot[k], top[k], top[i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY',
                          ngon_method='EAR_CLIP')
    return finish(bm, xform(loc, rot, scale), color, fn)


def star_pts(n, R, r, phase=math.pi / 2):
    out = []
    for i in range(2 * n):
        a = phase + math.pi * i / n
        rr = R if i % 2 == 0 else r
        out.append((rr * math.cos(a), rr * math.sin(a)))
    return out


def torus(loc, R, r, color=None, fn=None, segs=16, minor=5, rot=(0, 0, 0), arc=2 * math.pi, scale=(1, 1, 1)):
    bm = bmesh.new()
    closed = arc >= 2 * math.pi - 1e-6
    count = segs if closed else segs + 1
    rings = []
    for i in range(count):
        a = arc * i / segs
        c, s = math.cos(a), math.sin(a)
        ring = []
        for j in range(minor):
            b = 2 * math.pi * j / minor
            d = R + r * math.cos(b)
            ring.append(bm.verts.new((d * c, d * s, r * math.sin(b))))
        rings.append(ring)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for A, B in pairs:
        for j in range(minor):
            k = (j + 1) % minor
            bm.faces.new((A[j], A[k], B[k], B[j]))
    if not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return finish(bm, xform(loc, rot, scale), color, fn)


FONT = {
    "B": ["110", "101", "110", "101", "110"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "K": ["1001", "1010", "1100", "1010", "1001"],
    "P": ["110", "101", "110", "100", "100"], "L": ["100", "100", "100", "100", "111"],
    "I": ["111", "010", "010", "010", "111"], "C": ["011", "100", "100", "100", "011"],
    "E": ["111", "100", "110", "100", "111"], "V": ["101", "101", "101", "101", "010"],
    "7": ["111", "001", "010", "010", "010"], "S": ["011", "100", "010", "001", "110"],
    "H": ["101", "101", "111", "101", "101"], "!": ["1", "1", "1", "0", "1"],
    "$": ["010", "111", "100", "111", "001", "111", "010"],
}


def text_width(text):
    return sum(len(FONT[ch][0]) + 1 for ch in text) - 1


def pixel_text(text, center, right, down, px, depth, color):
    """Blocky letters centred on `center` (on the surface); each horizontal run of pixels is one box."""
    right, down = Vector(right).normalized(), Vector(down).normalized()
    out_dir = right.cross(down)  # the side the text faces is -out_dir for (X, -Z) = faces -Y
    rows = max(len(FONT[ch]) for ch in text)
    origin = Vector(center) - right * text_width(text) * px / 2 - down * rows * px / 2
    boxes, col = [], 0
    M = Matrix((right, down, out_dir)).transposed().to_4x4()
    for ch in text:
        glyph = FONT[ch]
        for r, line in enumerate(glyph):
            k = 0
            while k < len(line):
                if line[k] == "1":
                    e = k
                    while e < len(line) and line[e] == "1":
                        e += 1
                    run = e - k
                    loc = origin + right * (col + k + run / 2) * px + down * (r + 0.5) * px
                    bm = bmesh.new()
                    bmesh.ops.create_cube(bm, size=1.0)
                    bmesh.ops.scale(bm, vec=Vector((run * px, px, depth)), verts=bm.verts)
                    boxes.append(finish(bm, Matrix.Translation(loc) @ M, color))
                    k = e
                else:
                    k += 1
        col += len(glyph[0]) + 1
    return boxes


def sparkle(loc, size, color, facing=(0, -1, 0)):
    """Four-pointed cartoon star facing `facing`."""
    rot = tilt(facing)
    return [prism(star_pts(4, size, size * 0.25), size * 0.18, color, loc=loc, rot=rot)]


def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


# ---------------------------------------------------------------------------------------------------------------
# The Shiba from shiba_bonk_default.blend (same stick placement as build_shiba_tiers.py)
# ---------------------------------------------------------------------------------------------------------------
DOG = [o for o in bpy.data.collections['Collection'].objects if o.type == 'MESH']
ORANGE, CREAM, DARK = (0.745, 0.254, 0.045), (0.922, 0.823, 0.672), (0.01, 0.01, 0.012)
STICK_WOOD = (0.12, 0.055, 0.022)
_src = bpy.data.objects['Stick_orig']
STICK = _src.copy()
STICK.data = _src.data.copy()
STICK.name = "BaseStick"
bpy.data.collections['Collection'].objects.link(STICK)
STICK.matrix_world = Matrix.Rotation(math.radians(-90), 4, 'X') @ _src.matrix_world
bpy.context.view_layer.update()
_pts = [STICK.matrix_world @ v.co for v in STICK.data.vertices]
_c = sum(_pts, Vector()) / len(_pts)
_axis = max((b - a for a in _pts[::7] for b in _pts[::7]), key=lambda v: v.length).normalized()
_proj = [(p - _c).dot(_axis) for p in _pts]
if _axis.z < 0:
    _axis = -_axis
    _proj = [-x for x in _proj]
_grip = _c + _axis * min(_proj)
_hmn, _hmx = bbox([bpy.data.objects['RightHand']])
_hand = (_hmn + _hmx) / 2
_rot = _axis.rotation_difference(Vector((0.40, -0.13, 0.90)).normalized()).to_matrix().to_4x4()
STICK.matrix_world = Matrix.Translation(_hand) @ _rot @ Matrix.Translation(-_grip) @ STICK.matrix_world
STICK.hide_render = True
bpy.context.view_layer.update()


def paint_by_material(o, cols, default=(0.8, 0.8, 0.8)):
    """cols: {material name: fn(position) -> colour}."""
    me = o.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        name = me.materials[poly.material_index].name if len(me.materials) else ""
        fn = cols.get(name)
        for li in poly.loop_indices:
            p = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            attr.data[li].color = (*(fn(p) if fn else default), 1.0)
    me.color_attributes.active_color = attr


def copy_obj(o):
    cp = o.copy()
    cp.data = o.data.copy()
    COLL.objects.link(cp)
    cp.hide_render = False
    return cp


def dog(height, base=(0, 0, 0), with_stick=True, cols=None):
    """A painted copy of the whole Shiba (and its stick), `height` studs tall, bottom centre at `base`."""
    parts = [copy_obj(o) for o in DOG]
    bpy.context.view_layer.update()
    cols = cols or {"fur_orange": lambda p: ORANGE, "fur_cream": lambda p: CREAM, "fur_dark": lambda p: DARK}
    for p in parts:
        paint_by_material(p, cols)
    if with_stick:
        s = copy_obj(STICK)
        paint(s, flat(STICK_WOOD))
        parts.append(s)
    fit(parts, height, base, by_dog=parts[:len(DOG)])
    return parts


def fit(objs, height, base, by_dog=None):
    mn, mx = bbox(by_dog or objs)
    k = height / (mx.z - mn.z)
    centre = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    M = Matrix.Translation(Vector(base)) @ Matrix.Scale(k, 4) @ Matrix.Translation(-centre)
    for o in objs:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------------------------------------------
# Reusable pieces
# ---------------------------------------------------------------------------------------------------------------
def tree_parts(base=(0, 0, 0), h=13.0, seed=1):
    """Round low-poly tree: tapered trunk, three roots, four leafy blobs (~400 triangles)."""
    s = h / 13.0
    b = Vector(base)
    rnd = random.Random(seed)
    out = [lathe([(0.8 * s, -0.2 * s, 0), (0.62 * s, 1.0 * s), (0.5 * s, 4.0 * s), (0.36 * s, 7.4 * s, 0)], segs=6,
                 fn=vary(BARK, 0.1, seed), loc=b, jit=0.05, seed=seed)]
    for k in range(3):
        a = k * 2.09 + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        out.append(rod(b + Vector((0, 0, 0.9 * s)), b + d * 1.5 * s + Vector((0, 0, -0.15 * s)), 0.32 * s,
                       fn=vary(mul(BARK, 0.85), 0.08, seed + k), segs=4, r2=0.08 * s))
    out.append(rod(b + Vector((0, 0, 4.6 * s)), b + Vector((1.6 * s, 0.4 * s, 6.4 * s)), 0.22 * s, BARK, segs=4,
                   r2=0.12 * s))
    blobs = [((0, 0, 8.3), 3.3), ((1.9, 0.6, 6.9), 2.3), ((-1.8, -0.8, 7.2), 2.4), ((0.4, -0.3, 10.6), 2.1)]
    leaf = zgrad(LEAF_DARK, LEAF_LIGHT, 5.5 * s + b.z, 12.5 * s + b.z, 0.08, seed)
    for k, (off, r) in enumerate(blobs):
        out.append(ico(b + Vector(off) * s, r * s, fn=leaf, sub=2, jit=0.12, seed=seed * 10 + k,
                       rot=(rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))))
    return out


def flower(loc, h, petal, seed=0):
    rnd = random.Random(seed)
    b = Vector(loc)
    top = b + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), h))
    out = [rod(b, top, 0.045, srgb(70, 150, 60), segs=4)]
    lean = Vector((top.x - b.x, top.y - b.y, 1.2)).normalized()
    rot = tilt(lean)
    out.append(prism(star_pts(5, 0.32, 0.16, rnd.uniform(0, 1)), 0.07, fn=vary(petal, 0.07, seed), loc=top, rot=rot))
    out.append(cyl(top + lean * 0.06, 0.11, 0.08, srgb(255, 215, 70), segs=5, rot=rot))
    mid = b + (top - b) * 0.45
    out.append(cyl(mid + Vector((0.12, 0, 0)), 0.14, 0.03, srgb(90, 175, 70), segs=3, rot=(0, math.radians(70), 0),
                   scale=(1, 0.5, 1)))
    return out


def rock_cone(h, r_top, segs=12, seed=0, loc=(0, 0, 0)):
    """Hanging rock under a floating island: top at loc.z, tip h below. Dirt band on top, grey rock below."""
    b = Vector(loc)
    prof = [(0, -h), (0.12 * r_top, -0.9 * h, 0.2), (0.3 * r_top, -0.72 * h, 0.14), (0.5 * r_top, -0.53 * h, 0.1),
            (0.7 * r_top, -0.35 * h, 0.07), (0.86 * r_top, -0.18 * h, 0.05), (0.97 * r_top, -0.07 * h, 0.02),
            (r_top, 0, 0)]
    dirt, rock, deep = srgb(140, 100, 64), srgb(160, 148, 134), srgb(122, 114, 112)

    def fn(p, n, i):
        t = (b.z - p.z) / h
        c = dirt if t < 0.2 else mix(rock, deep, (t - 0.2) / 0.8)
        return mul(c, 1 + random.Random(seed * 7919 + i).uniform(-0.09, 0.09))
    return lathe(prof, segs=segs, fn=fn, loc=b, seed=seed, rot=(0, 0, seed))


def plinth(w, h, color, trim, loc=(0, 0, 0), segs=8):
    """Low octagonal trophy / statue base with a trim band."""
    b = Vector(loc)
    return lathe([(w * 0.5, 0), (w * 0.5, h * 0.55), (w * 0.53, h * 0.55), (w * 0.53, h * 0.75), (w * 0.46, h * 0.75),
                  (w * 0.46, h), (0, h)], segs=segs, fn=bands([(h * 0.5 + b.z, color), (h * 0.8 + b.z, trim),
                                                              (h + 1 + b.z, color)], 0.05), loc=b)


# ---------------------------------------------------------------------------------------------------------------
# Models. Each builder returns {part name: [objects]}; "_preview" objects only show in the preview renders.
# ---------------------------------------------------------------------------------------------------------------
MODELS = []


def model(name, group):
    def reg(fn):
        MODELS.append((name, group, fn))
        return fn
    return reg


# --- World decoration ------------------------------------------------------------------------------------------
@model("Prop_Tree", "World")
def prop_tree():
    return {"Body": tree_parts(h=13.0, seed=3)}


@model("Prop_Flowers", "World")
def prop_flowers():
    out = [lathe([(1.45, -0.05, 0), (1.3, 0.1), (0.75, 0.2), (0, 0.24)], segs=7, fn=vary(GRASS, 0.08, 2), jit=0.07,
                 seed=2)]
    rnd = random.Random(5)
    for k in range(7):
        a = k * 0.9
        p = Vector((math.cos(a) * rnd.uniform(0.4, 1.1), math.sin(a) * rnd.uniform(0.4, 1.1), 0.1))
        out.append(cyl(p + Vector((0, 0, 0.3)), 0.09, 0.6, srgb(110, 195, 80), segs=3, r2=0,
                       rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0)))
    petals = [srgb(255, 90, 130), srgb(255, 220, 60), srgb(160, 120, 255), srgb(255, 255, 255), srgb(255, 140, 60)]
    spots = [(0.55, 0.25), (-0.5, 0.45), (0.05, -0.62), (-0.55, -0.35), (0.62, -0.45)]
    for k, (x, y) in enumerate(spots):
        out += flower((x, y, 0.15), 0.95 + 0.35 * ((k * 3) % 5) / 4, petals[k], seed=k + 1)
    return {"Body": out}


@model("Prop_Lamp", "World")
def prop_lamp():
    body = [lathe([(0.55, 0), (0.55, 0.3), (0.42, 0.42), (0.26, 0.62), (0, 0.62)], segs=8, fn=metal(IRON, 0.25)),
            cyl((0, 0, 3.1), 0.16, 5.2, fn=metal(IRON, 0.25), segs=6),
            cyl((0, 0, 1.25), 0.27, 0.18, GOLD, segs=8),
            cyl((0, 0, 5.55), 0.3, 0.22, GOLD, segs=8),
            lathe([(0.3, 5.66), (0.5, 5.8), (0.5, 5.9), (0, 5.9)], segs=6, fn=metal(IRON, 0.25))]
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        body.append(rod((math.cos(a) * 0.42, math.sin(a) * 0.42, 5.85), (math.cos(a) * 0.46, math.sin(a) * 0.46, 6.75),
                        0.045, IRON, segs=4))
    body.append(lathe([(0.52, 6.72), (0.62, 6.82), (0.3, 7.1), (0, 7.2)], segs=6, fn=metal(IRON, 0.3)))
    body.append(ball((0, 0, 7.28), 0.1, GOLD, segs=6, rings=4))
    glow = [ico((0, 0, 6.3), 0.34, srgb(255, 226, 150), sub=1)]
    return {"Body": body, "Glow": glow}


@model("Prop_IslandRock", "World")
def prop_island_rock():
    H, R = 10.0, 9.25
    out = [rock_cone(H, R, segs=14, seed=11)]
    rnd = random.Random(12)
    # Hanging stalactites and a few side boulders, all inside the cone's outline.
    for k in range(6):
        a = k * 1.05 + rnd.uniform(-0.2, 0.2)
        t = rnd.uniform(0.35, 0.6)
        r = R * (1 - t) * 0.8
        top = Vector((math.cos(a) * r, math.sin(a) * r, -t * H))
        out.append(cyl(top - Vector((0, 0, 1.2)), 0.7, 2.4, fn=vary(srgb(110, 102, 98), 0.08, k), segs=5, r2=0.05,
                       rot=(math.pi, 0, rnd.uniform(0, 3))))
    for k in range(5):
        a = k * 1.3 + 0.4
        t = rnd.uniform(0.25, 0.5)
        r = R * (1 - t) * 0.92
        out.append(ico((math.cos(a) * r, math.sin(a) * r, -t * H), 1.2, fn=vary(srgb(150, 140, 128), 0.1, k), sub=1,
                       jit=0.25, seed=k, scale=(1, 1, 0.8)))
    # Vines hanging from the top edge and glowing crystals.
    for k in range(9):
        a = k * 0.7 + rnd.uniform(0, 0.3)
        r = R * 0.9
        L = rnd.uniform(1.2, 2.6)
        out.append(cyl((math.cos(a) * r, math.sin(a) * r, -0.3 - L / 2), 0.18, L, srgb(80, 160, 70), segs=3, r2=0.04,
                       rot=(math.pi, 0, 0)))
    for k in range(4):
        a = k * 1.6 + 1.0
        t = 0.45 + 0.1 * (k % 2)
        r = R * (1 - t) * 0.95
        base = Vector((math.cos(a) * r, math.sin(a) * r, -t * H))
        out.append(rod(base, base + Vector((math.cos(a) * 1.0, math.sin(a) * 1.0, -0.4)), 0.35,
                       fn=metal(srgb(110, 220, 255), 0.3, k), segs=4, r2=0.0))
    return {"Body": out}


@model("Prop_Cloud", "World")
def prop_cloud():
    blobs = [((0, 0, 5.0), 5.0), ((-6.2, 0.6, 3.6), 3.8), ((6.3, -0.4, 3.8), 4.1), ((-2.8, 1.6, 6.8), 3.6),
             ((2.9, -1.2, 7.0), 3.9), ((9.8, 0.4, 2.6), 2.5), ((-9.6, -0.3, 2.4), 2.4)]
    white, shade = srgb(252, 252, 255), srgb(205, 215, 240)
    fn = lambda p, n, i: mix(shade, white, (p.z - 1.0) / 5.0 + max(0.0, n.z) * 0.5)
    return {"Body": [ico(c, r, fn=fn, sub=2, jit=0.08, seed=k, clamp_z=1.0) for k, (c, r) in enumerate(blobs)]}


@model("Prop_SmallIsland", "World")
def prop_small_island():
    out = [lathe([(6.2, -1.0, 0), (6.6, -0.3, 0.03), (6.4, 0.2, 0.02), (5.6, 0.45), (0, 0.5)], segs=12,
                 fn=lambda p, n, i: vary(GRASS, 0.08, 7)(p, n, i) if p.z > 0.1 else vary(srgb(128, 92, 60), 0.08)(p, n, i),
                 seed=7)]
    out.append(rock_cone(8.5, 6.2, segs=11, seed=8, loc=(0, 0, -0.95)))
    out += tree_parts(base=(0.8, 0.9, 0.3), h=7.5, seed=9)
    out += flower((-2.5, -1.8, 0.4), 0.9, srgb(255, 90, 130), seed=3)
    out += flower((-3.1, -0.9, 0.4), 0.7, srgb(255, 220, 60), seed=4)
    out.append(ico((-2.8, 2.6, 0.6), 0.8, fn=vary(STONE, 0.1), sub=1, jit=0.2, scale=(1.2, 1, 0.8)))
    for k in range(3):
        a = k * 2.2 + 0.5
        out.append(cyl((math.cos(a) * 6.0, math.sin(a) * 6.0, -1.6), 0.25, 1.6, srgb(80, 160, 70), segs=3, r2=0.05,
                       rot=(math.pi, 0, 0)))
    return {"Body": out}


@model("Prop_ShibaStatue", "Hub")
def prop_shiba_statue():
    stone, stone_l = srgb(120, 118, 136), srgb(165, 162, 180)
    ped = lathe([(6.0, 0), (6.0, 0.9), (5.3, 0.9), (5.3, 2.5), (5.6, 2.5), (5.6, 2.85), (5.25, 2.85), (5.25, 3.1),
                 (0, 3.1)], segs=8, phase=math.pi / 8,
                fn=bands([(0.95, stone), (2.45, stone_l), (2.9, GOLD), (4, stone)], 0.05))
    body = [ped]
    front = -5.3 * math.cos(math.pi / 8)
    body.append(cube((0, front - 0.05, 1.7), (4.4, 0.12, 1.3), GOLD_DARK))
    body += pixel_text("BONK", (0, front - 0.14, 1.7), (1, 0, 0), (0, 0, -1), 0.24, 0.12, srgb(40, 30, 20))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        body.append(ball((math.cos(a) * 5.85, math.sin(a) * 5.85, 0.95), 0.28, GOLD, segs=6, rings=4))
    body += dog(12.9, base=(0, 0, 3.1))
    return {"Body": body}


# --- Hub machines (12 studs, front -Y toward the hub centre) --------------------------------------------------------
@model("Prop_DailySpinMachine", "Hub")
def daily_spin():
    purple, purple_d = srgb(120, 70, 200), srgb(70, 45, 120)
    body = [cube((0, 0.4, 1.35), (6.4, 3.2, 2.7), fn=vary(purple_d, 0.05), bevel=0.25),
            cube((0, 0.4, 2.8), (6.8, 3.6, 0.3), GOLD, bevel=0.08),
            cube((0, 1.3, 5.2), (1.3, 1.0, 5.0), fn=metal(purple, 0.25)),
            cube((0, -1.25, 1.35), (5.2, 0.12, 1.4), GOLD_DARK)]
    body += pixel_text("SPIN", (0, -1.36, 1.35), (1, 0, 0), (0, 0, -1), 0.27, 0.1, WHITE)
    cols = [srgb(255, 70, 80), srgb(255, 200, 40), srgb(70, 170, 255), srgb(110, 220, 90), srgb(190, 100, 255),
            srgb(255, 140, 40), srgb(255, 110, 190), srgb(70, 225, 215)]
    cz, R, cy = 7.2, 4.1, 0.2

    def wedges(p, n, i):
        if abs(n.y) < 0.9:
            return mul(GOLD, 0.9)
        a = math.atan2(p.z - cz, p.x)
        return cols[int(((a + math.pi) / (2 * math.pi)) * 16) % 8]
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=16, radius1=R, radius2=R, depth=0.6)
    body.append(finish(bm, xform((0, cy, cz), (math.pi / 2, 0, 0)), fn=wedges))
    body.append(torus((0, cy, cz), R + 0.1, 0.32, fn=metal(GOLD), segs=16, minor=5, rot=(math.pi / 2, 0, 0)))
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        body.append(cube((math.cos(a) * R * 0.5, cy - 0.33, cz + math.sin(a) * R * 0.5), (R, 0.06, 0.1), WHITE,
                         rot=(0, -a, 0)))
    body.append(cyl((0, cy - 0.45, cz), 0.75, 0.5, fn=metal(GOLD), segs=8, rot=(math.pi / 2, 0, 0)))
    body.append(ball((0, cy - 0.75, cz), 0.35, RED, segs=6, rings=4))
    # Pointer at the top.
    body.append(prism([(-0.7, 0.9), (0.7, 0.9), (0, -0.5)], 0.5, fn=metal(RED, 0.3), loc=(0, cy - 0.2, cz + R + 0.35),
                       rot=(math.pi / 2, 0, 0)))
    for k in range(12):
        a = 2 * math.pi * k / 12
        body.append(ball((math.cos(a) * (R + 0.1), cy - 0.35, cz + math.sin(a) * (R + 0.1)), 0.2,
                         srgb(255, 250, 200), segs=5, rings=3))
    return {"Body": body}


@model("Prop_CoinFlipMachine", "Hub")
def coin_flip():
    red, red_d = srgb(185, 45, 50), srgb(120, 30, 35)
    felt = srgb(40, 150, 90)
    body = [lathe([(2.9, 0), (2.9, 0.45), (2.3, 0.6), (2.1, 3.1), (2.9, 3.3), (2.9, 3.7), (0, 3.7)], segs=10,
                  fn=bands([(0.5, red_d), (3.15, red), (3.45, GOLD), (5, felt)], 0.05))]
    for z in (1.2, 2.3):
        body.append(cyl((0, 0, z), 2.22, 0.18, GOLD, segs=10))
    # The big coin, standing a little tilted in a gold holder.
    body.append(lathe([(0.9, 3.65), (0.9, 3.95), (0.55, 4.3), (0, 4.3)], segs=8, fn=metal(GOLD_DARK)))
    cz = 7.4
    rot = (math.pi / 2, math.radians(12), 0)
    body.append(cyl((0, 0, cz), 3.1, 0.55, fn=metal(GOLD), segs=18, rot=rot))
    body.append(torus((0, 0, cz), 3.0, 0.17, fn=metal(GOLD_LIGHT), segs=18, minor=4, rot=rot))
    face = Matrix.Rotation(math.radians(12), 3, 'Y')
    for side in (-1, 1):
        n = face @ Vector((0, side, 0))
        right = face @ Vector((-side, 0, 0))
        up = face @ Vector((0, 0, 1))
        body.append(prism(star_pts(5, 1.7, 0.75), 0.2, fn=metal(GOLD_DARK, 0.35), loc=Vector((0, 0, cz)) + n * 0.3,
                          rot=tilt(n)))
    # Coin stacks and sparkles.
    for k, (x, y, count) in enumerate([(-1.6, -1.1, 4), (1.5, -1.3, 3), (1.3, 1.4, 5)]):
        for j in range(count):
            body.append(cyl((x + 0.04 * (j % 2), y, 3.78 + j * 0.17), 0.42, 0.16, fn=metal(GOLD, 0.2, j), segs=8))
    for loc, s in [((-3.2, -0.6, 9.6), 0.6), ((3.3, -0.5, 6.0), 0.45), ((2.3, -0.4, 10.6), 0.35)]:
        body += sparkle(loc, s, srgb(255, 250, 200))
    return {"Body": body}


@model("Prop_ShopMachine", "Hub")
def shop():
    green, green_d = srgb(90, 210, 130), srgb(50, 150, 90)
    body = [cube((0, 0, 1.55), (9.6, 3.4, 3.1), fn=vary(WOOD, 0.06)),
            cube((0, -1.75, 1.8), (9.2, 0.12, 1.1), green),
            cube((0, 0, 3.3), (10.2, 3.9, 0.4), fn=vary(WOOD_LIGHT, 0.05), bevel=0.08)]
    body += pixel_text("SHOP", (0, -1.86, 1.8), (1, 0, 0), (0, 0, -1), 0.2, 0.08, WHITE)
    for x in (-4.7, 4.7):
        for y in (-1.6, 1.6):
            body.append(cube((x, y, 6.2), (0.45, 0.45, 5.6), fn=vary(WOOD_DARK, 0.05)))
    # Back shelf with boxes.
    body.append(cube((0, 1.55, 5.6), (9.0, 0.9, 0.2), WOOD_DARK))
    for k, x in enumerate((-3.4, -1.6, 0.4, 2.2, 3.6)):
        c = hsv(k / 5, 0.55, 1)
        body.append(cube((x, 1.5, 6.1), (1.2, 0.7, 0.8), fn=vary(c, 0.06, k), rot=(0, 0, 0.1 * (k % 3 - 1))))
    # Striped awning, a valance and a round "$" sign on top.
    for k in range(8):
        x = -4.55 + k * 1.3
        c = green if k % 2 == 0 else WHITE
        body.append(cube((x, 0, 9.2), (1.3, 4.6, 0.3), c, rot=(math.radians(-10), 0, 0)))
        body.append(prism([(-0.65, 0), (0.65, 0), (0, -0.6)], 0.12, c, loc=(x, -2.35, 8.95), rot=(math.pi / 2, 0, 0)))
    body.append(cyl((0, 0, 10.9), 1.15, 0.35, fn=metal(GOLD), segs=12, rot=(math.pi / 2, 0, 0)))
    body.append(cube((0, 0.1, 9.9), (0.3, 0.3, 0.9), WOOD_DARK))
    body += pixel_text("$", (0, -0.2, 10.9), (1, 0, 0), (0, 0, -1), 0.24, 0.08, srgb(40, 120, 60))
    # Goods on the counter: potions, a bone, a gift.
    for k, x in enumerate((-3.2, -2.2, 3.0)):
        c = [srgb(255, 80, 120), srgb(80, 170, 255), srgb(190, 110, 255)][k]
        body.append(ico((x, -0.4, 4.05), 0.55, fn=metal(c, 0.3, k), sub=1))
        body.append(cyl((x, -0.4, 4.75), 0.18, 0.5, srgb(220, 230, 240), segs=6))
        body.append(cyl((x, -0.4, 5.05), 0.22, 0.15, WOOD, segs=6))
    body.append(rod((-0.9, -0.3, 3.75), (0.9, -0.3, 3.75), 0.2, CREAM_W, segs=6))
    for x in (-0.95, 0.95):
        for y in (-0.55, -0.05):
            body.append(ball((x, y, 3.8), 0.3, CREAM_W, segs=6, rings=4))
    body.append(cube((1.8, 0.6, 4.05), (1.0, 1.0, 1.0), srgb(255, 90, 110), rot=(0, 0, 0.3)))
    body.append(cube((1.8, 0.6, 4.07), (1.06, 0.25, 1.06), GOLD, rot=(0, 0, 0.3)))
    body.append(cube((1.8, 0.6, 4.07), (0.25, 1.06, 1.06), GOLD, rot=(0, 0, 0.3)))
    return {"Body": body}


@model("Prop_QuestsMachine", "Hub")
def quests():
    body = []
    for x in (-4.1, 4.1):
        body.append(cube((x, 0.3, 4.9), (0.6, 0.6, 9.8), fn=vary(WOOD_DARK, 0.05)))
    # Plank board.
    for k in range(6):
        c = WOOD if k % 2 == 0 else mul(WOOD, 1.12)
        body.append(cube((0, 0.3, 2.8 + k * 1.0 + 0.5), (8.4, 0.4, 0.96), fn=vary(c, 0.04, k)))
    body.append(cube((0, 0.3, 8.9), (8.8, 0.55, 0.3), WOOD_DARK))
    body.append(cube((0, 0.3, 2.65), (8.8, 0.55, 0.3), WOOD_DARK))
    # Little roof.
    for s in (-1, 1):
        body.append(cube((0, 0.3 + s * 0.85, 9.75), (9.6, 1.9, 0.25), fn=vary(srgb(200, 60, 55), 0.05),
                         rot=(-s * math.radians(28), 0, 0)))
    # Notes with pins, one with a check mark.
    notes = [(-2.8, 7.3, 0.08), (-0.4, 7.6, -0.06), (2.2, 7.2, 0.1), (-2.2, 4.4, -0.08), (0.6, 4.6, 0.05),
             (3.0, 4.3, -0.1)]
    for k, (x, z, r) in enumerate(notes):
        body.append(cube((x, -0.02, z), (1.9, 0.06, 2.2), CREAM_W, rot=(0, r, 0)))
        for j in range(3):
            body.append(cube((x - 0.1, -0.06, z + 0.5 - j * 0.45), (1.3 - 0.3 * (j == 2), 0.03, 0.12),
                             srgb(120, 110, 100), rot=(0, r, 0)))
        body.append(ball((x, -0.15, z + 0.95), 0.14, [RED, BLUE, srgb(80, 190, 90)][k % 3], segs=5, rings=3))
    body.append(rod((0.3, -0.12, 4.3), (0.6, -0.12, 4.0), 0.09, srgb(60, 180, 70), segs=4))
    body.append(rod((0.6, -0.12, 4.0), (1.2, -0.12, 4.8), 0.09, srgb(60, 180, 70), segs=4))
    # Big yellow "!" above.
    body.append(prism([(-0.45, 0.0), (0.45, 0.0), (0.3, -1.3), (-0.3, -1.3)], 0.4, fn=metal(srgb(255, 210, 40)),
                      loc=(0, 0.3, 11.95), rot=(math.pi / 2, 0, 0)))
    body.append(ico((0, 0.3, 10.3), 0.3, fn=metal(srgb(255, 210, 40)), sub=1))
    # Barrel with scrolls at the foot.
    body.append(lathe([(0.7, 0), (0.85, 0.6), (0.7, 1.2), (0, 1.2)], segs=8, fn=vary(WOOD, 0.06), loc=(-3.2, -1.4, 0)))
    for k in range(3):
        body.append(rod((-3.2 + (k - 1) * 0.3, -1.4, 1.0), (-3.2 + (k - 1) * 0.45, -1.6, 2.1), 0.14, CREAM_W, segs=5))
    return {"Body": body}


# --- Upgrade stands (7 studs, front -Y toward the path) -----------------------------------------------------------
def stand(color):
    body = [cube((0, 0, 1.5), (7.0, 3.2, 3.0), fn=vary(color, 0.05), bevel=0.12),
            cube((0, 0, 2.25), (7.1, 3.3, 0.5), WHITE),
            cube((0, 0, 3.2), (7.6, 3.8, 0.4), fn=vary(WOOD_LIGHT, 0.05), bevel=0.06)]
    for x in (-3.4, 3.4):
        body.append(cube((x, 1.3, 4.75), (0.4, 0.4, 3.1), fn=vary(WOOD, 0.05)))
    for k in range(6):
        x = -3.25 + k * 1.3
        c = color if k % 2 == 0 else WHITE
        body.append(cube((x, -0.2, 6.6), (1.3, 4.3, 0.28), c, rot=(math.radians(-12), 0, 0)))
        body.append(prism([(-0.65, 0), (0.65, 0), (0, -0.35)], 0.1, c, loc=(x, -2.36, 6.98), rot=(math.pi / 2, 0, 0)))
    return body


def bust(loc, height):
    """The Shiba's head (from the blend) on a little gold stand."""
    head = copy_obj(bpy.data.objects['Head'])
    bpy.context.view_layer.update()
    paint_by_material(head, {"fur_orange": lambda p: ORANGE, "fur_cream": lambda p: CREAM, "fur_dark": lambda p: DARK})
    b = Vector(loc)
    fit([head], height, b + Vector((0, 0, 0.35)))
    return [head, lathe([(0.55, 0), (0.55, 0.12), (0.3, 0.22), (0.3, 0.38), (0, 0.38)], segs=8, fn=metal(GOLD), loc=b)]


def up_arrow(loc, size, color):
    pts = [(-0.25, -0.6), (0.25, -0.6), (0.25, 0.0), (0.6, 0.0), (0, 0.65), (-0.6, 0.0), (-0.25, 0.0)]
    return prism([(x * size, y * size) for x, y in pts], 0.25 * size, fn=metal(color, 0.3), loc=loc,
                 rot=(math.pi / 2, 0, 0))


@model("Prop_UpgradeStand_ShooterTier", "Stands")
def stand_tier():
    c = srgb(190, 110, 255)
    body = stand(c)
    body += bust((-1.6, 0.5, 3.4), 2.1)
    body.append(up_arrow((1.6, 0.4, 4.75), 2.0, c))
    body += sparkle((2.8, 0.0, 5.6), 0.4, GOLD_LIGHT)
    return {"Body": body}


@model("Prop_UpgradeStand_ProjectileTier", "Stands")
def stand_projectile():
    c = srgb(255, 200, 40)
    body = stand(c)
    # A stick and a bone crossed in a little stand.
    body.append(cube((-1.6, 0.5, 3.55), (1.6, 0.9, 0.3), WOOD_DARK, bevel=0.05))
    body.append(rod((-2.5, 0.5, 3.5), (-0.6, 0.5, 5.9), 0.2, fn=vary(srgb(140, 90, 50), 0.08), segs=5))
    body.append(rod((-0.8, 0.4, 3.6), (-2.3, 0.4, 5.6), 0.22, CREAM_W, segs=6))
    for p in ((-0.8, 0.4, 3.6), (-2.3, 0.4, 5.6)):
        for dx in (-0.22, 0.22):
            body.append(ball((p[0] + dx, p[1], p[2] + dx * 0.6), 0.28, CREAM_W, segs=6, rings=4))
    body.append(up_arrow((1.6, 0.4, 4.75), 2.0, c))
    return {"Body": body}


@model("Prop_UpgradeStand_Shooters", "Stands")
def stand_shooters():
    c = srgb(255, 140, 60)
    body = stand(c)
    # Paw print and a big "+".
    pad = srgb(95, 60, 40)
    body.append(cube((-1.7, 0.5, 4.2), (0.3, 0.3, 1.6), WOOD_DARK))
    body.append(cyl((-1.7, 0.3, 4.9), 0.85, 0.25, pad, segs=8, rot=(math.pi / 2, 0, 0), scale=(1.1, 0.9, 1)))
    for k, (dx, dz) in enumerate([(-1.0, 0.85), (-0.36, 1.25), (0.36, 1.25), (1.0, 0.85)]):
        body.append(cyl((-1.7 + dx, 0.3, 4.9 + dz), 0.32, 0.25, pad, segs=6, rot=(math.pi / 2, 0, 0)))
    plus = [(-0.2, 0.6), (0.2, 0.6), (0.2, 0.2), (0.6, 0.2), (0.6, -0.2), (0.2, -0.2), (0.2, -0.6), (-0.2, -0.6),
            (-0.2, -0.2), (-0.6, -0.2), (-0.6, 0.2), (-0.2, 0.2)]
    body.append(prism([(x * 1.9, y * 1.9) for x, y in plus], 0.45, fn=metal(c, 0.3), loc=(1.6, 0.4, 4.75),
                      rot=(math.pi / 2, 0, 0)))
    return {"Body": body}


@model("Prop_UpgradeStand_MoveSpeed", "Stands")
def stand_speed():
    c = srgb(80, 200, 255)
    body = stand(c)
    bolt = [(0.1, 0.9), (-0.45, -0.05), (-0.05, -0.05), (-0.25, -0.9), (0.45, 0.15), (0.05, 0.15), (0.35, 0.9)]
    body.append(prism([(x * 1.4, y * 1.4) for x, y in bolt], 0.4, fn=metal(srgb(255, 215, 50), 0.3),
                      loc=(1.7, 0.4, 4.85), rot=(math.pi / 2, 0, 0)))
    # A big sneaker with a wing, toe to the right.
    body.append(cube((-1.5, 0.3, 3.6), (2.6, 1.2, 0.35), WHITE, bevel=0.08))
    body.append(cube((-1.8, 0.3, 4.15), (1.9, 1.1, 0.8), fn=vary(c, 0.05), bevel=0.15))
    body.append(cube((-2.4, 0.3, 4.8), (0.9, 1.05, 1.0), fn=vary(c, 0.05), bevel=0.15))
    body.append(cube((-1.2, 0.3, 4.6), (0.6, 0.9, 0.1), WHITE, rot=(0, 0.3, 0)))
    for s in (-1, 1):
        body.append(prism([(0, 0), (-1.1, 0.5), (-0.8, 0.1), (-1.2, -0.05), (-0.7, -0.25)], 0.1, WHITE,
                          loc=(-2.8, 0.3 + s * 0.6, 4.7), rot=(math.pi / 2, 0, 0)))
    return {"Body": body}


# --- Trophies (4 studs, front -Y toward the island centre) ---------------------------------------------------------
def cup(color, emblem=None, top=None, fnc=None):
    """Classic two-handled cup on an octagonal plinth."""
    fnc = fnc or metal(color)
    out = [plinth(2.0, 0.6, srgb(60, 48, 40), GOLD_DARK)]
    out.append(lathe([(0.72, 0.6), (0.72, 0.72), (0.42, 0.85), (0.16, 1.02), (0.14, 1.45), (0.3, 1.6), (0.82, 1.85),
                      (1.05, 2.35), (1.1, 2.95), (1.18, 3.2), (1.02, 3.22), (0.9, 2.9), (0, 2.75)], segs=10,
                     fn=fnc))
    for s in (-1, 1):
        pts = [Vector((s * (0.95 + 0.42 * math.cos(t)), 0, 2.55 + 0.52 * math.sin(t)))
               for t in [-math.pi / 2 + math.pi * k / 6 for k in range(7)]]
        for a, b in zip(pts, pts[1:]):
            out.append(rod(a, b, 0.1, fn=fnc, segs=4))
    out.append(cube((0, -1.02, 0.36), (1.0, 0.06, 0.28), GOLD_LIGHT))
    if emblem:
        out += emblem
    if top:
        out += top
    return out


def cup_star(color, size=0.42, z=2.45):
    return [prism(star_pts(5, size, size * 0.45), 0.12, fn=metal(color, 0.35), loc=(0, -1.12, z),
                  rot=(math.pi / 2 - 0.1, 0, 0))]


@model("Trophy_Wood", "Trophies")
def trophy_wood():
    wood = lambda p, n, i: vary(WOOD, 0.1, 3)(p, n, i)
    emblem = [rod((-0.45, -1.15, 2.1), (0.45, -1.15, 2.8), 0.08, WOOD_DARK, segs=4),
              rod((0.45, -1.15, 2.1), (-0.45, -1.15, 2.8), 0.08, WOOD_DARK, segs=4)]
    top = [rod((0, 0, 2.8), (0.35, 0.1, 4.0), 0.1, WOOD_DARK, segs=5),
           prism([(0, 0), (0.35, 0.15), (0.5, 0.45), (0.2, 0.35)], 0.05, srgb(90, 180, 70), loc=(0.2, 0.05, 3.55),
                 rot=(math.pi / 2, 0, 0.3))]
    return {"Body": cup(WOOD, emblem, top, fnc=wood)}


@model("Trophy_Bronze", "Trophies")
def trophy_bronze():
    return {"Body": cup(BRONZE, cup_star(mul(BRONZE, 0.8)),
                        [ico((0, 0, 3.55), 0.35, fn=metal(BRONZE), sub=1), cyl((0, 0, 3.2), 0.12, 0.2, BRONZE)])}


@model("Trophy_Silver", "Trophies")
def trophy_silver():
    top = [prism(star_pts(5, 0.55, 0.25), 0.18, fn=metal(SILVER, 0.35), loc=(0, 0, 3.55), rot=(math.pi / 2, 0, 0))]
    return {"Body": cup(SILVER, cup_star(srgb(120, 170, 255)), top)}


@model("Trophy_Gold", "Trophies")
def trophy_gold():
    top = [prism(star_pts(5, 0.6, 0.28), 0.2, fn=metal(GOLD, 0.35), loc=(0, 0, 3.55), rot=(math.pi / 2, 0, 0))]
    emblem = cup_star(RED, 0.4)
    for s in (-1, 1):
        emblem.append(ico((s * 0.62, -0.95, 2.15), 0.13, fn=metal(srgb(80, 170, 255)), sub=1))
    return {"Body": cup(GOLD, emblem, top)}


@model("Trophy_Galaxy", "Trophies")
def trophy_galaxy():
    def cosmic(p, n, i):
        t = (p.z - 0.6) / 2.7
        c = mix(srgb(60, 30, 140), srgb(190, 80, 255), t * 1.4) if t < 0.7 else mix(srgb(190, 80, 255),
                                                                                     srgb(90, 230, 255), (t - 0.7) * 3)
        c = mul(c, 0.85 + 0.3 * max(0.0, n.dot(LIGHT)))
        return (1, 1, 1) if random.Random(i * 13).random() < 0.05 else c
    top = [ico((0, 0, 3.6), 0.38, fn=metal(srgb(255, 150, 80)), sub=1),
           torus((0, 0, 3.6), 0.62, 0.06, srgb(255, 230, 160), segs=14, minor=3, rot=(0.4, 0.3, 0)),
           ball((0.55, -0.3, 3.95), 0.1, srgb(200, 230, 255), segs=5, rings=3)]
    emblem = sparkle((0, -1.15, 2.4), 0.45, srgb(120, 230, 255)) + sparkle((0.5, -1.05, 2.9), 0.2, WHITE)
    return {"Body": cup(srgb(150, 80, 255), emblem, top, fnc=cosmic)}


def base_only(color=srgb(60, 48, 40), trim=GOLD_DARK):
    return [plinth(2.0, 0.6, color, trim), cube((0, -1.02, 0.36), (1.0, 0.06, 0.28), GOLD_LIGHT)]


@model("Trophy_Starter", "Trophies")
def trophy_starter():
    g = srgb(80, 220, 160)
    out = base_only()
    out.append(lathe([(0.5, 0.6), (0.5, 0.75), (0.15, 0.9), (0.12, 1.5), (0, 1.5)], segs=8, fn=metal(GOLD)))
    out.append(prism(star_pts(5, 1.45, 0.62), 0.45, fn=metal(g, 0.35), loc=(0, 0, 2.62), rot=(math.pi / 2, 0, 0)))
    out.append(prism(star_pts(5, 0.8, 0.34), 0.5, fn=metal(srgb(210, 255, 230), 0.25), loc=(0, -0.03, 2.62),
                     rot=(math.pi / 2, 0, 0)))
    out += sparkle((0.95, -0.35, 3.85), 0.25, WHITE)
    return {"Body": out}


@model("Trophy_Streak", "Trophies")
def trophy_streak():
    out = base_only()
    out.append(lathe([(0.75, 0.6), (0.75, 0.72), (0.55, 0.9), (0.62, 1.05), (0, 1.05)], segs=8, fn=metal(srgb(80, 80, 95))))
    flame = lambda p, n, i: mul(mix(srgb(255, 90, 30), srgb(255, 230, 80), (p.z - 1.0) / 2.6),
                                0.9 + 0.2 * max(0.0, n.dot(LIGHT)))
    out.append(ico((0, 0, 1.9), 0.95, fn=flame, sub=2, scale=(1, 0.8, 1.05), jit=0.06))
    out.append(cyl((0, 0, 3.0), 0.75, 1.5, fn=flame, segs=7, r2=0.0, rot=(0.1, 0, 0), jit=0.05))
    out.append(cyl((0.55, 0.05, 2.6), 0.35, 1.2, fn=flame, segs=5, r2=0.0, rot=(0, 0.5, 0)))
    out.append(cyl((-0.55, 0.05, 2.5), 0.32, 1.1, fn=flame, segs=5, r2=0.0, rot=(0, -0.55, 0)))
    out += pixel_text("7", (0, -0.8, 1.95), (1, 0, 0), (0, 0, -1), 0.22, 0.14, WHITE)
    return {"Body": out}


@model("Trophy_VIP", "Trophies")
def trophy_vip():
    out = base_only(srgb(70, 30, 90), GOLD)
    out.append(cube((0, 0, 1.0), (1.8, 1.8, 0.8), fn=vary(srgb(200, 40, 70), 0.05), bevel=0.25))
    for x in (-0.85, 0.85):
        for y in (-0.85, 0.85):
            out.append(ball((x, y, 0.75), 0.13, GOLD, segs=5, rings=3))
    out.append(lathe([(0.95, 1.35), (1.0, 2.0), (0.9, 2.0), (0.85, 1.45), (0, 1.45)], segs=10, fn=metal(GOLD)))
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        p = Vector((math.cos(a) * 0.95, math.sin(a) * 0.95, 1.95))
        out.append(cyl(p + Vector((0, 0, 0.45)), 0.3, 0.9, fn=metal(GOLD), segs=4, r2=0.0))
        out.append(ball(p + Vector((0, 0, 0.95)), 0.12, srgb(255, 250, 220), segs=5, rings=3))
    for k, c in enumerate([RED, srgb(80, 170, 255), srgb(90, 220, 110)]):
        a = -math.pi / 2 + (k - 1) * 0.8
        out.append(ico((math.cos(a) * 1.0, math.sin(a) * 1.0, 1.7), 0.14, fn=metal(c), sub=1))
    out += pixel_text("VIP", (0, -0.93, 1.0), (1, 0, 0), (0, 0, -1), 0.11, 0.06, GOLD)
    return {"Body": out}


@model("Trophy_Diamond", "Trophies")
def trophy_diamond():
    out = base_only(srgb(40, 50, 80), SILVER)
    out.append(lathe([(0.55, 0.6), (0.55, 0.75), (0.2, 0.95), (0.15, 1.4), (0.45, 1.55), (0, 1.55)], segs=8,
                     fn=metal(SILVER)))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        out.append(rod((math.cos(a) * 0.35, math.sin(a) * 0.35, 1.5), (math.cos(a) * 0.7, math.sin(a) * 0.7, 2.1), 0.06,
                       SILVER, segs=4))
    gem = lambda p, n, i: mix(mul(srgb(90, 220, 255), 0.75 + 0.5 * max(0.0, n.dot(LIGHT))), (1, 1, 1),
                              0.35 if i % 3 == 0 else 0.0)
    out.append(lathe([(0, 1.45), (1.05, 2.55), (1.05, 2.7), (0.65, 3.15), (0, 3.15)], segs=8, fn=gem))
    out += sparkle((0.85, -0.6, 3.55), 0.3, WHITE) + sparkle((-0.9, -0.5, 2.9), 0.2, WHITE)
    return {"Body": out}


@model("Trophy_Rainbow", "Trophies")
def trophy_rainbow():
    out = base_only(srgb(50, 40, 70), GOLD)
    out.append(lathe([(0.55, 0.6), (0.55, 0.75), (0.2, 0.95), (0.2, 1.15), (0.55, 1.25), (0, 1.25)], segs=8,
                     fn=metal(GOLD)))
    head = copy_obj(bpy.data.objects['Head'])
    bpy.context.view_layer.update()
    mn, mx = bbox([head])
    span = mx.z - mn.z
    rainbow = lambda cr: (lambda p: hsv((p.z - mn.z) / span * 0.85, 0.75 * cr, 1.0))
    paint_by_material(head, {"fur_orange": rainbow(1.0), "fur_cream": rainbow(0.45), "fur_dark": lambda p: DARK})
    fit([head], 2.5, (0, 0, 1.2))
    out.append(head)
    # A little rainbow arc behind the head.
    for k in range(5):
        out.append(torus((0, 0.6, 1.9), 1.55 - k * 0.14, 0.075, hsv(k / 6, 0.7, 1), segs=12, minor=3,
                         rot=(math.pi / 2, 0, 0), arc=math.pi))
    return {"Body": out}


# --- Obby tower (exact 10 x 40.2 so it replaces the part tower 1:1: TowerRadius 5, FinishHeight 42 - 1.4 - 0.4) --
@model("Prop_ObbyTower", "Hub")
def obby_tower():
    H, R = 40.2, 5.0
    green, yellow = srgb(95, 215, 60), srgb(255, 210, 40)
    prof = [(R, 0)]
    z = 0.0
    edges = [1.6]
    while edges[-1] + 4.0 < H - 1.4:
        edges.append(edges[-1] + 4.0)
    for e in edges:
        prof += [(R, e - 0.12), (R * 0.95, e - 0.05), (R * 0.95, e + 0.05), (R, e + 0.12)]
    prof += [(R, H - 1.2), (R * 0.92, H - 1.1), (R * 0.92, H), (0, H)]
    zs = [0.0] + edges + [H - 1.15, H + 1]

    def fn(p, n, i):
        if p.z < 1.55:
            return vary(STONE_DARK, 0.06)(p, n, i)
        if p.z > H - 1.15:
            return metal(GOLD)(p, n, i)
        if abs(n.z) > 0.2 or any(abs(p.z - e) < 0.1 for e in edges):
            return WHITE
        band = sum(1 for e in edges if p.z > e)
        c = green if band % 2 else yellow
        a = math.atan2(p.y, p.x)
        return mul(c, 1.0 + 0.07 * math.cos(a * 16 / 2))
    return {"Body": [lathe(prof, segs=16, fn=fn, phase=0.0)]}


# --- Shiba platforms (Config/ShibaPlatforms). Built in studs around the island surface point: bottom at -0.5 (sunk
# into the island), StandPoint at the height the Shiba stands on, front (-Y) toward the island centre. ---------------
SINK = -0.5
TIER_HEIGHT = {"Shiba": 6, "ShadesShiba": 6, "BuffShiba": 7.5, "ChefShiba": 7.5, "PoliceShiba": 6.5,
               "NinjaShiba": 5.5, "GoldShiba": 6.5, "GalaxyShiba": 7, "GiantShiba": 16, "CheemsGod": 12}


TIER_HEIGHT.update({"PirateShiba": 7, "CowboyShiba": 7, "VikingShiba": 7.5, "WizardShiba": 8.5, "AstronautShiba": 7.5,
                    "RobotShiba": 7.5, "SamuraiShiba": 7.5, "VampireShiba": 7, "PharaohShiba": 7.5, "DragonShiba": 8})
MODEL_DIR = os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--python") + 1]))


def tier_dog(asset, top):
    """Preview only: the tier's own Shiba (assets/models/<asset>.fbx) standing on the platform, else the orange dog
    (tiers whose model is not built yet; 8 studs unless TIER_HEIGHT knows better)."""
    height = TIER_HEIGHT.get(asset, 8)
    path = os.path.join(MODEL_DIR, f"{asset}.fbx")
    if not os.path.exists(path):
        return dog(height, base=(0, 0, top))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, axis_forward='Z', axis_up='Y')
    bpy.context.view_layer.update()
    new = [o for o in bpy.data.objects if o not in before]
    keep = []
    for o in new:
        if o.type == 'MESH' and o.name.split(".")[0] not in ("Shoulder", "OrbitCenter"):
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            keep.append(o)
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    body = [o for o in keep if o.name.split(".")[0] != "Stick"]
    fit(keep, height, (0, 0, top), by_dog=body or keep)
    return keep


def platform(asset, top, body):
    # The game scales the platform by the distance from its bottom to the marker: nothing may reach below SINK.
    for o in body:
        for v in o.data.vertices:
            v.co.z = max(v.co.z, SINK)
    marker = cube((0, 0, top), (0.1, 0.1, 0.1), srgb(255, 0, 255))
    preview = tier_dog(asset, top)
    return {"Body": body, "StandPoint": [marker], "_preview": preview}


@model("Platform_Shiba", "Platforms")
def platform_shiba():
    top = 1.4
    rings = [(3.3, 0), (2.7, 1), (2.05, 0), (1.35, 1), (0.65, 0)]
    body = [lathe([(3.75, SINK, 0), (3.6, 0.3, 0.03), (3.4, 1.25, 0.02), (3.3, top, 0), (0, top)], segs=10,
                  fn=lambda p, n, i: vary(WOOD_LIGHT, 0.04)(p, n, i) if n.z > 0.9 else vary(BARK, 0.1, 1)(p, n, i),
                  seed=1)]
    # Tree rings as thin inlaid circles just above the top.
    for k, (r, dark) in enumerate(rings[1:]):
        if dark:
            body.append(torus((0, 0, top - 0.02), r, 0.07, mul(WOOD_LIGHT, 0.72), segs=10, minor=3))
    rnd = random.Random(2)
    for k in range(5):
        a = k * 1.25 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(rod(d * 2.9 + Vector((0, 0, 0.7)), d * 4.3 + Vector((0, 0, SINK + 0.1)), 0.55,
                        fn=vary(mul(BARK, 0.85), 0.08, k), segs=5, r2=0.2))
    for x, y, h, c in [(-3.4, -2.4, 0.9, RED), (-2.9, -3.2, 0.6, RED), (3.6, 1.8, 0.7, srgb(255, 200, 60))]:
        body.append(cyl((x, y, h / 2 - 0.1), 0.12, h, CREAM_W, segs=5))
        body.append(lathe([(0.4, h - 0.12), (0.34, h + 0.05), (0, h + 0.2)], segs=6, color=None,
                          fn=vary(c, 0.05), loc=(x, y, 0)))
    for k in range(6):
        a = k * 1.05 + 0.6
        body.append(cyl((math.cos(a) * 3.7, math.sin(a) * 3.7, 0.2), 0.14, 0.8, srgb(110, 195, 80), segs=3, r2=0,
                        rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)))
    return platform("Shiba", top, body)


@model("Platform_ShadesShiba", "Platforms")
def platform_shades():
    top = 2.0
    body = [lathe([(3.95, SINK), (3.95, 0.35), (4.02, 0.38), (4.02, 0.68), (3.72, 0.72), (3.72, 1.2), (3.55, 1.22),
                   (3.55, 1.85), (3.25, 1.88), (3.25, top), (0, top)], segs=8,
                  fn=lambda p, n, i: (metal(GOLD)(p, n, i) if (0.3 < p.z < 0.7 or 1.21 < p.z < 1.87)
                                      else mul(BLACK, 1.0 + 0.8 * max(0.0, n.dot(LIGHT)))))]
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        body.append(ball((math.cos(a) * 3.76, math.sin(a) * 3.76, 0.96), 0.13, fn=metal(GOLD), segs=5, rings=3))
    # A gold "$" coin leaning on the front and two little money stacks.
    body.append(cyl((0, -4.05, 0.3), 0.75, 0.2, fn=metal(GOLD), segs=12, rot=(math.radians(75), 0, 0)))
    body += pixel_text("$", (0, -4.18, 0.34), (1, 0, 0), (0, 0.26, -0.97), 0.12, 0.06, GOLD_DARK)
    for x in (-2.2, 2.2):
        for j in range(3):
            body.append(cube((x, -3.3, SINK + 0.72 + j * 0.2), (0.9, 0.5, 0.18), srgb(110, 200, 110), rot=(0, 0, 0.2 * j)))
    return platform("ShadesShiba", top, body)


@model("Platform_BuffShiba", "Platforms")
def platform_buff():
    top = 1.05
    plate = [(4.3, SINK), (4.3, 0.28), (4.42, 0.3), (4.42, 0.52), (4.3, 0.54), (4.3, 0.86), (4.05, 0.9),
             (3.3, 0.9), (3.3, 1.0), (1.05, 1.0), (1.05, top), (0, top)]

    def fn(p, n, i):
        r = math.hypot(p.x, p.y)
        if 0.29 < p.z < 0.53 and r > 4.25:
            return srgb(210, 40, 45)
        if r < 1.1 and p.z > 0.99:
            return metal(srgb(210, 212, 222))(p, n, i)
        return mul(srgb(40, 40, 48), 1.0 + 0.7 * max(0.0, n.dot(LIGHT)))
    body = [lathe(plate, segs=16, fn=fn)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        body.append(cyl((math.cos(a) * 2.2, math.sin(a) * 2.2, 0.91), 0.32, 0.04, srgb(20, 20, 24), segs=6))
    # Dumbbell lying in front.
    grey = srgb(70, 72, 82)
    body.append(rod((-1.5, -4.25, -0.05), (1.5, -4.25, -0.05), 0.14, srgb(200, 202, 212), segs=6))
    for x in (-1.25, 1.25):
        body.append(cyl((x, -4.25, -0.05), 0.55, 0.45, fn=metal(grey, 0.3), segs=6, rot=(0, math.pi / 2, 0)))
    return platform("BuffShiba", top, body)


@model("Platform_ChefShiba", "Platforms")
def platform_chef():
    top = 2.9
    body = [cube((0, 0, (SINK + 2.3) / 2), (7.0, 7.0, 2.3 - SINK), fn=vary(WHITE, 0.03)),
            cube((0, 0, 2.45), (7.6, 7.6, 0.3), fn=lambda p, n, i: mix(srgb(215, 215, 222), WHITE,
                                                                        random.Random(i).random() * 0.6)),
            cube((0, 0.2, 2.75), (4.6, 3.8, 0.3), fn=vary(srgb(195, 135, 75), 0.06), bevel=0.05)]
    for s in (-1, 1):
        body.append(cube((s * 1.72, -3.53, 1.0), (3.2, 0.08, 1.9), srgb(225, 225, 222)))
        body.append(cube((s * 0.5, -3.62, 1.35), (0.18, 0.14, 0.7), srgb(170, 170, 180)))
    for x in (-2.4, -0.8, 0.8, 2.4):
        body.append(cyl((x, -3.58, 2.1), 0.18, 0.14, BLACK, segs=6, rot=(math.pi / 2, 0, 0)))
    # A red pot, a tomato and a knife.
    body.append(lathe([(0.6, 2.6), (0.68, 2.7), (0.68, 3.5), (0.75, 3.55), (0.6, 3.55), (0, 3.4)], segs=8,
                      fn=metal(RED, 0.3), loc=(3.0, 3.0, 0)))
    body.append(ico((-3.0, -3.0, 2.95), 0.36, fn=metal(srgb(240, 50, 45), 0.3), sub=1))
    body.append(cyl((-3.0, -3.0, 3.33), 0.12, 0.1, srgb(60, 160, 60), segs=5))
    body.append(cube((2.9, -2.7, 2.64), (0.25, 1.3, 0.04), srgb(210, 212, 222), rot=(0, 0, 0.5)))
    body.append(cube((2.55, -2.05, 2.66), (0.2, 0.6, 0.12), BLACK, rot=(0, 0, 0.5)))
    return platform("ChefShiba", top, body)


@model("Platform_PoliceShiba", "Platforms")
def platform_police():
    top = 3.0
    blue, blue_d = srgb(40, 80, 200), srgb(28, 55, 150)
    asphalt = lathe([(3.95, SINK), (3.95, 0.02), (3.75, 0.08), (0, 0.08)], segs=12, fn=vary(srgb(70, 70, 78), 0.04))
    body = [asphalt]
    for x in (-2.95, 2.95):
        for y in (-1.6, 0.4):
            body.append(cube((x, y, 0.09), (0.25, 1.1, 0.03), WHITE))
    for x in (-1.9, 1.9):
        for y in (-2.25, 2.25):
            body.append(cyl((x, y, 0.75), 0.7, 0.55, BLACK, segs=10, rot=(0, math.pi / 2, 0)))
            body.append(cyl((x + (0.05 if x > 0 else -0.05), y, 0.75), 0.36, 0.5, srgb(190, 192, 200), segs=6,
                            rot=(0, math.pi / 2, 0)))
    body.append(cube((0, 0, 1.25), (3.8, 7.0, 1.1), fn=metal(blue, 0.2), bevel=0.25))
    for s in (-1, 1):
        body.append(cube((s * 1.91, 0.15, 1.25), (0.06, 2.9, 0.8), WHITE))
        body += pixel_text("POLICE", (s * 1.95, 0.15, 1.25), (0, s, 0), (0, 0, -1), 0.1, 0.03, blue_d)
    body.append(cube((0, 0.35, 2.3), (3.3, 3.7, 1.25), WHITE, bevel=0.2))
    # Windows: windscreen, rear window and side windows.
    body.append(cube((0, -1.52, 2.3), (2.8, 0.06, 0.8), GLASS, rot=(math.radians(-8), 0, 0)))
    body.append(cube((0, 2.22, 2.3), (2.8, 0.06, 0.8), GLASS))
    for s in (-1, 1):
        for y in (-0.55, 1.2):
            body.append(cube((s * 1.66, y, 2.35), (0.06, 1.4, 0.7), GLASS))
    body.append(cube((0, 0.35, top - 0.05), (3.0, 3.4, 0.1), WHITE))
    # Siren lights on the back of the roof, headlights, grille, bumpers, star on the hood.
    body.append(cube((0, 1.85, top + 0.05), (2.6, 0.45, 0.12), srgb(40, 40, 45)))
    body.append(cube((-0.65, 1.85, top + 0.24), (1.1, 0.4, 0.3), srgb(255, 50, 50), bevel=0.06))
    body.append(cube((0.65, 1.85, top + 0.24), (1.1, 0.4, 0.3), srgb(60, 120, 255), bevel=0.06))
    for x in (-1.25, 1.25):
        body.append(cube((x, -3.5, 1.4), (0.8, 0.1, 0.35), srgb(255, 245, 190)))
        body.append(cube((x, 3.5, 1.4), (0.7, 0.1, 0.3), srgb(230, 40, 40)))
    body.append(cube((0, -3.52, 1.05), (1.4, 0.08, 0.35), BLACK))
    body.append(cube((0, -3.6, 0.75), (3.9, 0.3, 0.3), srgb(160, 162, 172), bevel=0.08))
    body.append(cube((0, 3.6, 0.75), (3.9, 0.3, 0.3), srgb(160, 162, 172), bevel=0.08))
    body.append(prism(star_pts(5, 0.5, 0.22), 0.06, fn=metal(GOLD), loc=(0, -2.5, 1.82), rot=(0, 0, 0)))
    return platform("PoliceShiba", top, body)


@model("Platform_NinjaShiba", "Platforms")
def platform_ninja():
    top = 1.6
    stone, stone_l, red = srgb(52, 52, 60), srgb(75, 75, 86), srgb(190, 25, 35)

    def fn(p, n, i):
        if 0.9 < p.z < 1.16 and n.z < 0.9:
            return red
        if n.z > 0.9 and p.z > top - 0.01:
            r = math.hypot(p.x, p.y)
            return red if 1.25 < r < 1.6 else vary(stone_l, 0.05)(p, n, i)
        return vary(stone, 0.07)(p, n, i)
    body = [lathe([(4.0, SINK, 0.02), (4.0, 0.9, 0.01), (4.12, 0.92), (4.12, 1.14), (3.7, 1.16), (3.7, top),
                   (1.6, top), (1.25, top), (0, top)], segs=8, fn=fn, seed=4)]
    # Bamboo at the back, shuriken stuck in the stone.
    for k, (x, y, h) in enumerate([(3.0, 2.9, 5.0), (3.6, 2.1, 3.8), (2.3, 3.5, 3.2)]):
        for j in range(int(h / 1.0)):
            body.append(cyl((x, y, SINK + 0.5 + j * 1.0), 0.2, 0.95, srgb(110, 180, 70), segs=6))
            body.append(cyl((x, y, SINK + 1.0 + j * 1.0), 0.23, 0.08, srgb(80, 140, 50), segs=6))
        body.append(prism([(0, 0), (0.8, 0.2), (0.3, -0.15)], 0.03, srgb(110, 190, 70), loc=(x, y, SINK + h - 0.4),
                          rot=(math.pi / 2, 0, k * 1.3)))
    for a, z in [(-2.1, 0.5), (-0.9, 0.3), (2.4, 0.6)]:
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(prism(star_pts(4, 0.8, 0.2), 0.08, fn=metal(srgb(185, 188, 200), 0.35), loc=d * 4.1 + Vector((0, 0, z)),
                          rot=tilt(d)))
    return platform("NinjaShiba", top, body)


@model("Platform_GoldShiba", "Platforms")
def platform_gold():
    top = 2.0
    body = []
    coins = [(3.8, SINK, 0.35, 0, 0), (3.6, 0.35, 0.75, 0.3, 0), (3.7, 0.75, 1.15, -0.25, 0.2), (3.5, 1.15, 1.55, 0, -0.3),
             (3.6, 1.55, top, 0.15, 0)]
    for k, (r, z0, z1, x, y) in enumerate(coins):
        c = GOLD if k % 2 == 0 else GOLD_DARK
        rim = lambda p, n, i, c=c: mul(c, 0.8 if i % 2 else 1.0) if abs(n.z) < 0.5 else metal(c, 0.2)(p, n, i)
        body.append(cyl((x, y, (z0 + z1) / 2), r, z1 - z0, fn=rim, segs=20, rot=(0, 0, k)))
    rnd = random.Random(7)
    for k in range(9):
        a = k * 0.7 + rnd.uniform(0, 0.3)
        d = rnd.uniform(3.9, 4.4)
        body.append(cyl((math.cos(a) * d, math.sin(a) * d, 0.05 + 0.1 * (k % 2)), 0.45, 0.14, fn=metal(GOLD, 0.25, k),
                        segs=8, rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)))
    for k, (x, y, a) in enumerate([(-2.6, -3.4, 0.4), (2.8, 3.2, -0.3)]):
        body.append(prism([(-0.7, -0.3), (0.7, -0.3), (0.5, 0.3), (-0.5, 0.3)], 0.6, fn=metal(GOLD_LIGHT, 0.3),
                          loc=(x, y, 0.1), rot=(math.pi / 2, 0, a)))
    body.append(lathe([(0, -0.2), (0.55, 0.35), (0.45, 0.55), (0, 0.6)], segs=6, fn=metal(RED, 0.4),
                      loc=(3.4, -2.5, 0.0)))
    body += sparkle((-3.6, -1.8, 1.5), 0.35, srgb(255, 250, 210))
    return platform("GoldShiba", top, body)


@model("Platform_GalaxyShiba", "Platforms")
def platform_galaxy():
    top = 3.2
    body = [lathe([(3.1, SINK), (3.1, 0.1), (2.3, 0.1), (2.3, SINK)], segs=16,
                  fn=lambda p, n, i: hsv(0.72 + 0.12 * math.sin(math.atan2(p.y, p.x) * 2), 0.6, 1.0))]
    rock, rock_d = srgb(80, 45, 125), srgb(45, 25, 80)

    def fn(p, n, i):
        if n.z > 0.95 and p.z > top - 0.05:
            return vary(srgb(95, 60, 145), 0.08)(p, n, i)
        c = mix(rock_d, rock, (p.z - 0.8) / 2.4)
        return (1, 1, 1) if random.Random(i * 7).random() < 0.06 else vary(c, 0.1)(p, n, i)
    body.append(lathe([(0, 0.7), (1.2, 1.1, 0.12), (2.6, 1.8, 0.08), (3.4, 2.5, 0.05), (3.55, 2.95, 0.02),
                       (3.4, top, 0), (0, top)], segs=10, fn=fn, seed=9))
    for k, (a, t, c) in enumerate([(0.3, 1.7, srgb(110, 230, 255)), (2.2, 1.9, srgb(255, 130, 230)),
                                   (4.1, 1.6, srgb(110, 230, 255)), (5.2, 2.2, srgb(255, 130, 230))]):
        d = Vector((math.cos(a), math.sin(a), 0))
        base = d * 2.5 + Vector((0, 0, t))
        body.append(rod(base, base + d * 1.1 + Vector((0, 0, 0.7)), 0.3, fn=metal(c, 0.3), segs=4, r2=0))
        body.append(rod(base, base + d * 0.8 + Vector((0, 0, -0.5)), 0.22, fn=metal(c, 0.3), segs=4, r2=0))
    body.append(ico((-3.6, 2.6, 3.6), 0.5, fn=vary(srgb(200, 200, 215), 0.1), sub=1, jit=0.1))
    body += sparkle((3.3, -2.8, 4.3), 0.4, srgb(200, 240, 255)) + sparkle((-3.3, -2.5, 1.6), 0.3, WHITE)
    return platform("GalaxyShiba", top, body)


@model("Platform_GiantShiba", "Platforms")
def platform_giant():
    top = 1.8
    rock, rock_l, crack = srgb(122, 110, 100), srgb(148, 136, 120), srgb(55, 45, 40)

    def fn(p, n, i):
        if n.z > 0.9 and p.z > 1.7:
            return vary(rock_l, 0.08, 3)(p, n, i)
        return vary(rock, 0.1, 4)(p, n, i)
    body = [lathe([(10.2, SINK, 0.03), (10.0, 0.8, 0.04), (9.6, 1.4, 0.03), (9.0, top, 0), (0, top)], segs=14, fn=fn,
                  seed=5)]
    for (x, y, a, L) in [(3.0, 2.0, 0.5, 8.0), (-3.5, -2.5, -0.9, 6.0), (-1.0, 4.5, 2.0, 5.0), (5.5, -3.5, 1.2, 4.0)]:
        body.append(cube((x, y, top + 0.02), (0.35, L, 0.08), crack, rot=(0, 0, a)))
    rnd = random.Random(6)
    for k, (x, y, r) in enumerate([(7.3, 5.7, 1.5), (-7.8, 5.2, 1.2), (8.6, -2.5, 1.0), (-6.5, -6.5, 1.3)]):
        body.append(ico((x, y, 1.2), r, fn=vary(rock if k % 2 else rock_l, 0.1, k), sub=1, jit=0.2, seed=k))
    # Tiny town and pine trees at the edge: the kaiju's playground.
    for k, (x, y, rot) in enumerate([(-8.0, -3.0, 0.3), (-7.2, 1.2, -0.2), (6.4, -6.9, 0.6)]):
        c = [srgb(235, 225, 200), srgb(200, 220, 240), srgb(240, 200, 190)][k]
        body.append(cube((x, y, top + 0.6), (1.4, 1.2, 1.2), fn=vary(c, 0.04), rot=(0, 0, rot)))
        body.append(prism([(-0.85, 0), (0.85, 0), (0, 0.75)], 1.3, fn=vary(srgb(200, 70, 60), 0.05),
                          loc=(x, y, top + 1.2), rot=(math.pi / 2, 0, rot)))
    for k, (x, y) in enumerate([(-5.0, 7.5), (-3.6, 8.4), (4.2, 8.2), (8.7, 1.8), (-9.0, -1.0), (1.5, -8.8)]):
        body.append(cyl((x, y, top + 0.25), 0.12, 0.5, BARK, segs=4))
        body.append(cyl((x, y, top + 1.1), 0.6, 1.4, fn=vary(LEAF_DARK, 0.1, k), segs=6, r2=0))
    return platform("GiantShiba", top, body)


@model("Platform_CheemsGod", "Platforms")
def platform_cheems():
    top = 10.0
    white, shade = srgb(252, 252, 255), srgb(210, 218, 240)
    cloud = lambda p, n, i: mix(shade, white, (p.z + 0.5) / 2.0 + max(0.0, n.z) * 0.4)
    body = [lathe([(5.2, SINK), (5.4, 0.4), (4.6, 1.2), (0, 1.3)], segs=10, fn=cloud)]
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        d = 5.0 + 0.6 * (k % 2)
        body.append(ico((math.cos(a) * d, math.sin(a) * d, 0.5), 1.6 - 0.3 * (k % 2), fn=cloud, sub=2, jit=0.08,
                        seed=k, clamp_z=SINK))
    body.append(lathe([(2.8, 1.2), (2.8, 1.6), (2.5, 1.7), (2.5, 2.25), (2.2, 2.4), (0, 2.4)], segs=12,
                      fn=metal(GOLD)))
    marble = srgb(245, 228, 170)

    def fluted(p, n, i):
        if abs(n.z) > 0.5:
            return marble
        return mul(marble, 1.0 if i % 2 == 0 else 0.86)
    body.append(lathe([(2.05, 2.4), (1.9, 5.8), (1.95, 9.2), (0, 9.2)], segs=16, fn=fluted))
    body.append(lathe([(2.0, 9.2), (2.6, 9.45), (2.7, 9.6), (0, 9.6)], segs=12, fn=metal(GOLD)))
    body.append(cube((0, 0, 9.8), (5.6, 5.6, 0.4), fn=metal(GOLD_DARK, 0.3), bevel=0.08))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        body.append(ico((math.cos(a) * 3.3, math.sin(a) * 3.3, 9.8), 0.3, fn=metal(srgb(120, 220, 255)), sub=1))
    for loc, s in [((-3.6, -2.4, 6.5), 0.5), ((3.4, -2.0, 7.6), 0.4), ((2.6, 2.8, 4.4), 0.35)]:
        body += sparkle(loc, s, GOLD_LIGHT)
    return platform("CheemsGod", top, body)


# --- Platforms for Shibas 11-20 and the ten after them (same rules; each one carries its Shiba's theme) -------------
P2 = "Platforms11to30"


def plank_deck(R, z0, z1, w, cols, seed=0, gap=0.07):
    """Round deck of parallel planks (along Y), clipped to radius R."""
    out = []
    for k in range(int(2 * R / w)):
        x = -R + w * (k + 0.5)
        L = 2 * math.sqrt(max(R * R - x * x, 0.0))
        if L > 0.6:
            out.append(cube((x, 0, (z0 + z1) / 2), (w - gap, L, z1 - z0), fn=vary(cols[k % len(cols)], 0.05, seed + k)))
    return out


def wheel(c, R, rot, rim, spokes=8, r=0.12, hub=None):
    """Spoked wheel (ship's wheel with handles if spokes stick out past the rim)."""
    M = Euler(rot).to_matrix()
    out = [torus(c, R, r, fn=vary(rim, 0.06), segs=16, minor=4, rot=rot)]
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = M @ Vector((math.cos(a), math.sin(a), 0))
        out.append(rod(Vector(c), Vector(c) + d * R, r * 0.6, rim, segs=4))
    out.append(cyl(c, R * 0.18, r * 3, hub or mul(rim, 0.7), segs=8, rot=rot))
    return out


def flame(loc, h, seed=0):
    """Low-poly flame: red, orange and yellow cones stacked inside each other."""
    rnd = random.Random(seed)
    b = Vector(loc)
    lean = Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 1)).normalized()
    out = []
    for k, (c, s) in enumerate([(srgb(230, 50, 30), 1.0), (srgb(255, 140, 30), 0.72), (srgb(255, 230, 90), 0.45)]):
        out.append(cyl(b + lean * h * s / 2 + Vector((0, 0, 0.02 * k)), 0.32 * h * s, h * s, c, segs=5, r2=0,
                       rot=tilt(lean)))
    return out


def surf_z(profile, d):
    """Height of a lathe profile [(radius, z), ...] (top part, radius shrinking upward) at distance d."""
    for (r0, z0, *_), (r1, z1, *_) in zip(profile, profile[1:]):
        if r1 <= d <= r0 or r0 <= d <= r1:
            t = (d - r0) / (r1 - r0 + 1e-9)
            return z0 + (z1 - z0) * t
    return profile[-1][1]


@model("Platform_PirateShiba", P2)
def platform_pirate():
    top = 1.6
    wood, wood_d, rope = srgb(170, 112, 62), srgb(105, 66, 38), srgb(222, 192, 130)
    # Round ship's deck: a planked hull (horizontal boards), deck planks on top, a thick rope along the rim.
    hull = [(4.0, SINK), (4.35, 0.25), (4.4, 0.7), (4.3, 1.15), (4.05, top - 0.2), (0, top - 0.2)]
    body = [lathe(hull, segs=14, fn=lambda p, n, i: mul(wood_d if int((p.z + 1) / 0.42) % 2 else mix(wood_d, wood, 0.35),
                                                          1 + random.Random(i).uniform(-0.05, 0.05)))]
    body += plank_deck(3.95, top - 0.25, top, 0.78, [wood, mix(wood, WOOD_LIGHT, 0.35)], 1)
    body.append(torus((0, 0, top - 0.08), 4.1, 0.17, fn=lambda p, n, i: rope if i % 3 else mul(rope, 0.8), segs=28,
                      minor=5))
    # Ship's wheel on a post at the back left, facing the field.
    c = Vector((-2.4, 3.2, top + 1.45))
    body.append(rod((-2.4, 3.45, top - 0.2), c + Vector((0, 0.25, -0.2)), 0.22, wood_d, segs=6))
    body += wheel(c, 1.05, (math.pi / 2, 0, 0.35), srgb(120, 72, 38), spokes=8, r=0.11, hub=GOLD)
    M = Euler((math.pi / 2, 0, 0.35)).to_matrix()
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = M @ Vector((math.cos(a), math.sin(a), 0))
        body.append(rod(c + d * 1.05, c + d * 1.5, 0.1, srgb(120, 72, 38), segs=5, r2=0.06))
    # Treasure barrel front right, overflowing with gold coins; open chest front left.
    bx, by = 3.0, -2.6
    body.append(lathe([(0.78, SINK), (0.92, 0.55), (0.78, 1.35), (0, 1.35)], segs=10, loc=(bx, by, 0),
                      fn=lambda p, n, i: IRON if abs(n.z) < 0.5 and (0.05 < p.z < 0.25 or 0.95 < p.z < 1.15)
                      else vary(wood, 0.06, 3)(p, n, i)))
    body.append(lathe([(0.72, 1.3), (0.45, 1.65), (0, 1.8)], segs=8, loc=(bx, by, 0), fn=metal(GOLD)))
    rnd = random.Random(11)
    for k in range(5):
        a = rnd.uniform(0, 6.3)
        body.append(cyl((bx + math.cos(a) * 0.6, by + math.sin(a) * 0.6, 1.45), 0.2, 0.06, fn=metal(GOLD, 0.25, k),
                        segs=8, rot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 0)))
    cx, cy = -3.1, -2.4
    body.append(cube((cx, cy, 0.25), (1.6, 1.0, 0.95), fn=vary(wood_d, 0.05), rot=(0, 0, 0.5)))
    for s in (-1, 1):
        body.append(cube((cx + s * 0.45 * math.cos(0.5), cy + s * 0.45 * math.sin(0.5), 0.3), (0.16, 1.06, 1.0), GOLD,
                         rot=(0, 0, 0.5)))
    body.append(cube((cx - 0.3 * math.sin(0.5), cy + 0.62 * math.cos(0.5), 1.05), (1.6, 0.12, 0.8), wood_d,
                     rot=(math.radians(-25), 0, 0.5)))
    body.append(ico((cx, cy, 0.78), 0.62, fn=metal(GOLD), sub=1, scale=(1.1, 0.7, 0.4), rot=(0, 0, 0.5)))
    body.append(ico((cx + 0.2, cy - 0.1, 0.98), 0.16, fn=metal(srgb(230, 30, 60)), sub=1))
    # Jolly Roger at the back right: black flag with a bone-white skull and crossbones.
    body.append(rod((2.6, 3.3, top - 0.2), (2.6, 3.3, top + 5.2), 0.1, wood_d, segs=6))
    body.append(cube((3.55, 3.3, top + 4.55), (1.9, 0.05, 1.2), BLACK))
    body.append(ico((3.55, 3.26, top + 4.7), 0.26, CREAM_W, sub=1, scale=(1, 0.3, 0.95)))
    for s in (-1, 1):
        body.append(rod((3.55 - 0.45, 3.26, top + 4.4 + s * 0.22), (3.55 + 0.45, 3.26, top + 4.4 - s * 0.22), 0.06,
                        CREAM_W, segs=4))
    return platform("PirateShiba", top, body)


@model("Platform_CowboyShiba", P2)
def platform_cowboy():
    top = 2.0
    hay, hay_d, twine = srgb(235, 195, 90), srgb(200, 155, 60), srgb(120, 75, 40)
    # Round hay bale standing on end: straw faces, twine bands, a spiral on top, straws sticking out.
    body = [lathe([(3.5, SINK, 0.02), (3.65, 0.3, 0.03), (3.7, 1.0, 0.03), (3.6, 1.7, 0.02), (3.4, top), (0, top)],
                  segs=14, fn=lambda p, n, i: vary(hay if n.z < 0.9 else mix(hay, hay_d, 0.2), 0.1, i % 7)(p, n, i),
                  seed=3)]
    for z in (0.55, 1.4):
        body.append(torus((0, 0, z), 3.72, 0.07, twine, segs=18, minor=3))
    for r in (2.6, 1.6, 0.7):
        body.append(torus((0, 0, top + 0.01), r, 0.08, hay_d, segs=14, minor=3))
    rnd = random.Random(5)
    for k in range(14):
        a = rnd.uniform(0, 6.3)
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(-0.3, 0.4))).normalized()
        base = Vector((math.cos(a) * 3.55, math.sin(a) * 3.55, rnd.uniform(0.2, 1.8)))
        body.append(rod(base, base + d * rnd.uniform(0.5, 0.9), 0.05, hay_d if k % 2 else hay, segs=3, r2=0.01))
    # Wagon wheel leaning on the bale (right), a cactus (back left), a crate (front right), a horseshoe.
    body += wheel((4.05, 1.0, 1.65), 1.65, (0, math.pi / 2 - 0.22, 0), srgb(125, 80, 45), spokes=10, r=0.13,
                  hub=IRON)
    body.append(torus((4.05, 1.0, 1.65), 1.72, 0.06, IRON, segs=16, minor=3, rot=(0, math.pi / 2 - 0.22, 0)))
    green, green_d = srgb(80, 170, 80), srgb(50, 130, 60)
    body.append(lathe([(0.45, SINK), (0.45, 3.2), (0.3, 3.55), (0, 3.65)], segs=8, loc=(-3.4, 3.1, 0),
                      fn=lambda p, n, i: green if i % 2 else green_d))
    for s, h in ((-1, 1.7), (1, 2.3)):
        base = Vector((-3.4 + s * 0.4, 3.1, h))
        elbow = base + Vector((s * 0.6, 0, 0))
        body.append(rod(base, elbow, 0.26, green, segs=6))
        body.append(rod(elbow, elbow + Vector((0, 0, 0.9)), 0.26, green, segs=6))
        body.append(ball(elbow + Vector((0, 0, 0.9)), 0.26, green, segs=6, rings=3))
    body.append(ball((-3.4, 3.1, 3.7), 0.18, srgb(255, 110, 150), segs=6, rings=3))
    body.append(cube((3.0, -2.9, 0.35), (1.3, 1.3, 1.3), fn=vary(srgb(190, 140, 85), 0.05), rot=(0, 0, 0.3)))
    for s in (-1, 1):
        body.append(cube((3.0, -2.9, 0.35), (1.36, 1.36, 0.14), srgb(110, 70, 40), rot=(0, 0, 0.3)))
        body.append(cube((3.0, -2.9, 0.35), (0.14, 1.36, 1.36), srgb(110, 70, 40), rot=(0, 0, 0.3 + s * 0.0)))
    body.append(torus((-1.4, -4.0, 0.06), 0.45, 0.1, srgb(170, 172, 182), segs=10, minor=3, arc=4.6,
                      rot=(0, 0, math.pi / 2 + 0.9)))
    return platform("CowboyShiba", top, body)


@model("Platform_VikingShiba", P2)
def platform_viking():
    top = 1.5
    wood, wood_d = srgb(160, 105, 60), srgb(95, 60, 35)
    body = [lathe([(4.0, SINK), (4.3, 0.4), (4.25, 1.0), (4.0, top - 0.2), (0, top - 0.2)], segs=16,
                  fn=lambda p, n, i: mul(wood_d if int((p.z + 1) / 0.4) % 2 else mix(wood_d, wood, 0.3),
                                         1 + random.Random(i).uniform(-0.05, 0.05)))]
    body += plank_deck(4.0, top - 0.25, top, 0.8, [wood, mix(wood, WOOD_LIGHT, 0.3)], 2)
    # Ring of round shields hung on the rail, painted in two colours each, iron boss.
    pairs = [(srgb(200, 35, 40), srgb(240, 232, 215)), (srgb(40, 80, 180), srgb(250, 200, 60)),
             (srgb(240, 232, 215), srgb(40, 120, 70)), (srgb(250, 200, 60), srgb(200, 35, 40))]
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        d = Vector((math.cos(a), math.sin(a), 0))
        c = d * 4.42 + Vector((0, 0, 0.85))
        ca, cb = pairs[k % 4]
        rot = tilt(d)
        body.append(cyl(c, 0.78, 0.12, ca, segs=12, rot=rot))
        body.append(cube(c + d * 0.07, (0.3, 0.3, 1.5), cb, rot=(0, 0, a)))
        body.append(ico(c + d * 0.12, 0.2, IRON, sub=1))
    # Carved dragon-head prow rising behind the Shiba (back left), looking over the deck toward the field.
    pts = [Vector((-1.9, 4.0, top - 0.2)), Vector((-2.1, 4.5, 2.6)), Vector((-2.2, 4.6, 4.2)), Vector((-2.2, 4.3, 5.6)),
           Vector((-2.15, 3.8, 6.6))]
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        body.append(rod(a, b, 0.55 - 0.08 * k, fn=vary(wood_d, 0.06, k), segs=6, r2=0.5 - 0.08 * k))
        body.append(torus(b, 0.5 - 0.08 * k, 0.07, GOLD, segs=8, minor=3, rot=tilt(b - a)))
    head = pts[-1] + Vector((0, -0.45, 0.1))
    body.append(cube(head, (0.75, 1.3, 0.7), fn=vary(wood_d, 0.05), bevel=0.12, rot=(0.15, 0, 0)))
    body.append(cube(head + Vector((0, -0.75, -0.2)), (0.6, 0.6, 0.35), srgb(200, 40, 40), rot=(0.15, 0, 0)))
    for s in (-1, 1):
        body.append(ico(head + Vector((s * 0.36, -0.25, 0.15)), 0.12, GOLD, sub=1))
        body.append(cyl(head + Vector((s * 0.25, 0.35, 0.55)), 0.13, 0.7, CREAM_W, segs=5, r2=0,
                        rot=tilt((s * 0.3, 0.8, 1))))
    return platform("VikingShiba", top, body)


@model("Platform_WizardShiba", P2)
def platform_wizard():
    top = 2.4
    body = []
    pages = srgb(245, 235, 205)
    books = [(7.0, 5.4, SINK, 0.8, 0.0, srgb(55, 60, 175)), (6.4, 5.0, 0.8, 1.6, 0.28, srgb(120, 50, 160)),
             (5.8, 4.6, 1.6, top, -0.16, srgb(170, 40, 50))]
    for k, (w, d, z0, z1, yaw, col) in enumerate(books):
        h = z1 - z0
        R = Matrix.Rotation(yaw, 3, 'Z')
        at = lambda x, y, z, R=R: tuple(R @ Vector((x, y, 0)) + Vector((0, 0, z)))
        body.append(cube(at(0, 0, z0 + 0.07), (w, d, 0.14), fn=vary(col, 0.04, k), rot=(0, 0, yaw)))
        body.append(cube(at(0, 0, z1 - 0.07), (w, d, 0.14), fn=vary(col, 0.04, k + 5), rot=(0, 0, yaw)))
        body.append(cube(at(-w / 2 + 0.08, 0, (z0 + z1) / 2), (0.16, d, h), mul(col, 0.8), rot=(0, 0, yaw)))
        body.append(cube(at(0.1, 0, (z0 + z1) / 2), (w - 0.35, d - 0.25, h - 0.26), pages, rot=(0, 0, yaw)))
        for sx in (-1, 1):
            body.append(cube(at(w / 2 - 0.25, sx * (d / 2 - 0.25), z1 - 0.06), (0.52, 0.52, 0.16), fn=metal(GOLD),
                             rot=(0, 0, yaw)))
        # Gold bands across the spine.
        for sy in (-1, 1):
            body.append(cube(at(-w / 2 + 0.06, sy * d * 0.28, (z0 + z1) / 2), (0.2, 0.22, h + 0.02), GOLD,
                             rot=(0, 0, yaw)))
    body.append(cube((0.6, -2.55, 1.0), (0.4, 0.06, 1.2), srgb(220, 40, 50), rot=(0.1, 0, 0.28)))
    body.append(prism(star_pts(5, 0.55, 0.24), 0.08, fn=metal(GOLD), loc=(1.5, -1.6, top + 0.04)))
    # Four standing rune stones with glowing runes on their outer faces, a candle, a floating crystal.
    glow = srgb(90, 230, 255)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        c = d * 4.55
        h = 2.4 if k < 2 else 3.0
        body.append(cube(c + Vector((0, 0, SINK + h / 2)), (1.0, 0.7, h), fn=vary(STONE, 0.08, k), rot=(0, 0, a + math.pi / 2)))
        f = c + d * 0.36
        side = Vector((-d.y, d.x, 0))
        body.append(cube(f + Vector((0, 0, SINK + h * 0.62)), (0.12, 0.1, 0.9), glow, rot=(0, 0, a + math.pi / 2)))
        body.append(rod(f + side * 0.25 + Vector((0, 0, SINK + h * 0.45)), f - side * 0.25 + Vector((0, 0, SINK + h * 0.8)),
                        0.06, glow, segs=4))
    body.append(cyl((-2.4, -1.4, 1.6 + 0.5), 0.2, 1.0, CREAM_W, segs=6))
    body += flame((-2.4, -1.4, 2.6), 0.5, 1)
    body.append(ico((2.9, 3.0, 5.2), 0.55, fn=metal(srgb(150, 110, 255)), sub=1, scale=(0.8, 0.8, 1.4)))
    body += sparkle((-3.3, 2.6, 4.3), 0.45, GOLD_LIGHT) + sparkle((3.6, -1.0, 3.6), 0.35, srgb(200, 240, 255))
    return platform("WizardShiba", top, body)


@model("Platform_AstronautShiba", P2)
def platform_astronaut():
    top = 2.0
    moon, moon_d = srgb(185, 185, 195), srgb(120, 120, 132)
    prof = [(4.1, SINK, 0.03), (4.3, 0.5, 0.05), (4.05, 1.3, 0.04), (3.5, top, 0), (0, top)]
    body = [lathe(prof, segs=12, fn=lambda p, n, i: vary(moon if n.z > 0.8 else mix(moon, moon_d, 0.4), 0.08, i)(p, n, i),
                  seed=21)]
    # Craters on top and on the sides.
    for (x, y, r) in [(2.3, -1.6, 0.6), (-2.4, 1.2, 0.5), (0.4, 2.6, 0.4)]:
        body.append(cyl((x, y, top + 0.01), r, 0.04, moon_d, segs=8))
        body.append(torus((x, y, top + 0.03), r + 0.08, 0.1, moon, segs=10, minor=3))
    for k, a in enumerate((0.5, 2.4, 4.2)):
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(torus(d * 4.2 + Vector((0, 0, 0.7)), 0.4, 0.1, mul(moon, 0.9), segs=8, minor=3, rot=tilt(d)))
    for k, (x, y, r) in enumerate([(4.4, -1.6, 0.5), (-4.1, -2.2, 0.4), (-3.9, 2.9, 0.35)]):
        body.append(ico((x, y, 0.0), r, fn=vary(moon_d, 0.1, k), sub=1, jit=0.1, seed=k))
    # Flag on the moon (back left): white with a blue band and a gold star.
    body.append(rod((-2.5, 2.3, top - 0.3), (-2.5, 2.3, top + 4.6), 0.07, srgb(210, 212, 222), segs=6))
    body.append(cube((-1.6, 2.3, top + 4.05), (1.8, 0.05, 1.1), WHITE))
    body.append(cube((-1.6, 2.27, top + 3.7), (1.8, 0.05, 0.25), srgb(40, 90, 200)))
    body.append(prism(star_pts(5, 0.3, 0.13), 0.06, fn=metal(GOLD), loc=(-1.6, 2.24, top + 4.2), rot=(math.pi / 2, 0, 0)))
    # Little rocket standing next to the rock (back right): white body, red nose and fins, blue window.
    rx, ry = 3.7, 3.1
    red = srgb(225, 50, 50)
    body.append(lathe([(0.5, 0.0), (0.62, 0.4), (0.62, 2.6), (0.45, 3.3), (0.22, 3.75), (0, 3.95)], segs=10,
                      loc=(rx, ry, 0), fn=lambda p, n, i: red if p.z > 3.05 else vary(WHITE, 0.03)(p, n, i)))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(prism([(0, 0), (0.75, -0.25), (0.75, 0.35), (0, 1.3)], 0.12, red, loc=(rx + d.x * 0.5, ry + d.y * 0.5, SINK),
                          rot=(math.pi / 2, 0, a)))
    body.append(cyl((rx - 0.35, ry - 0.5, 2.2), 0.28, 0.12, srgb(90, 180, 255), segs=10, rot=tilt((-0.55, -0.8, 0))))
    body += sparkle((2.2, -3.4, 4.6), 0.4, WHITE) + sparkle((-3.6, -1.2, 3.0), 0.3, srgb(255, 240, 180))
    return platform("AstronautShiba", top, body)


@model("Platform_RobotShiba", P2)
def platform_robot():
    top = 1.6
    steel, dark, yellow, cyan = srgb(150, 158, 172), srgb(62, 66, 78), srgb(250, 200, 40), srgb(70, 240, 255)

    def fn(p, n, i):
        if 0.52 < p.z < 0.98 and abs(n.z) < 0.5:
            return yellow if i % 2 else BLACK
        if n.z > 0.9 and p.z > top - 0.01:
            return vary(dark, 0.04)(p, n, i)
        return metal(steel, 0.3, i)(p, n, i)
    body = [lathe([(4.2, SINK), (4.2, 0.5), (4.35, 0.52), (4.35, 0.98), (4.1, 1.0), (3.8, 1.3), (3.8, top), (0, top)],
                  segs=16, fn=fn, phase=0.0)]
    body.append(torus((0, 0, top + 0.02), 3.1, 0.09, cyan, segs=16, minor=3))
    for k in range(4):
        body.append(cube((0, 0, top + 0.015), (0.12, 5.6, 0.04), cyan, rot=(0, 0, k * math.pi / 4)))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(cube(d * 3.97 + Vector((0, 0, 1.16)), (0.35, 0.35, 0.2), srgb(255, 60, 60) if k % 2 else cyan,
                         rot=(0, math.radians(35), a)))
        body.append(cyl(d * 3.45 + Vector((0, 0, top + 0.03)), 0.14, 0.08, srgb(200, 205, 215), segs=6))
    # Brass gears standing at the back: a big one half sunk into the island and a small one meshing with it.
    brass = srgb(215, 165, 60)

    def gear(c, R, teeth, depth, rot):
        M = Euler(rot).to_matrix()
        out = [cyl(c, R, depth, fn=metal(brass, 0.3), segs=teeth, rot=rot)]
        for k in range(teeth):
            a = 2 * math.pi * k / teeth
            d = M @ Vector((math.cos(a), math.sin(a), 0))
            out.append(cube(Vector(c) + d * (R + 0.18), (0.4, 0.4, depth), fn=metal(brass, 0.3),
                            rot=(M.to_4x4() @ Matrix.Rotation(a, 4, 'Z')).to_euler()))
        out.append(cyl(c, R * 0.35, depth + 0.1, dark, segs=8, rot=rot))
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.4
            d = M @ Vector((math.cos(a), math.sin(a), 0))
            out.append(cyl(Vector(c) + d * R * 0.65, R * 0.14, depth + 0.02, mul(brass, 0.55), segs=6, rot=rot))
        return out
    body += gear((-0.9, 3.8, 1.6), 2.2, 14, 0.5, (math.pi / 2, 0, 0.15))
    body += gear((2.3, 3.4, 2.4), 1.15, 9, 0.45, (math.pi / 2, 0, -0.2))
    # A little antenna with a red bulb.
    body.append(rod((3.3, 1.9, top - 0.1), (3.3, 1.9, top + 3.0), 0.06, dark, segs=4))
    body.append(ico((3.3, 1.9, top + 3.1), 0.2, srgb(255, 60, 60), sub=1))
    return platform("RobotShiba", top, body)


@model("Platform_SamuraiShiba", P2)
def platform_samurai():
    top = 1.4
    wood_d, tatami, border = srgb(85, 50, 30), srgb(205, 200, 125), srgb(40, 70, 45)
    body = [cube((0, 0, (SINK + 1.1) / 2), (7.4, 7.4, 1.1 - SINK), fn=vary(wood_d, 0.05), bevel=0.08)]
    for x in (-1.75, 1.75):
        body.append(cube((x, 0, 1.25), (3.4, 6.8, 0.3), fn=lambda p, n, i: vary(tatami, 0.03)(p, n, i)))
        for s in (-1, 1):
            body.append(cube((x + s * 1.62, 0, 1.26), (0.18, 6.82, 0.32), border))
    # Torii gate behind the Shiba: vermilion posts with black feet, two beams, the top beam with upturned ends.
    verm = srgb(220, 60, 35)
    for s in (-1, 1):
        body.append(cyl((s * 2.6, 3.2, (SINK + 6.8) / 2), 0.3, 6.8 - SINK, verm, segs=8))
        body.append(cyl((s * 2.6, 3.2, (SINK + 0.5) / 2), 0.38, 0.5 - SINK, BLACK, segs=8))
    body.append(cube((0, 3.2, 5.4), (6.6, 0.35, 0.42), verm))
    body.append(cube((0, 3.2, 6.55), (7.0, 0.5, 0.35), verm))
    body.append(cube((0, 3.2, 6.93), (7.4, 0.62, 0.4), BLACK))
    for s in (-1, 1):
        body.append(cube((s * 3.95, 3.2, 7.08), (1.0, 0.62, 0.36), BLACK, rot=(0, s * -0.3, 0)))
    body.append(cube((0, 3.2, 5.98), (0.35, 0.3, 0.8), verm))
    body.append(cube((0, 3.02, 5.98), (0.6, 0.06, 0.55), GOLD))
    # Stone lantern front left, a pink cherry bonsai front right.
    lx, ly = -3.1, -3.0
    body.append(cyl((lx, ly, SINK + 0.35), 0.55, 0.7, STONE, segs=6))
    body.append(cyl((lx, ly, 0.75), 0.22, 1.0, STONE, segs=6))
    body.append(cube((lx, ly, 1.55), (0.8, 0.8, 0.6), STONE))
    body.append(cube((lx, ly, 1.55), (0.84, 0.4, 0.34), srgb(255, 220, 110)))
    body.append(cube((lx, ly, 1.55), (0.4, 0.84, 0.34), srgb(255, 220, 110)))
    body.append(cyl((lx, ly, 2.1), 0.8, 0.5, STONE_DARK, segs=4, r2=0.1, rot=(0, 0, math.pi / 4)))
    body.append(ico((lx, ly, 2.45), 0.17, STONE_DARK, sub=1))
    bx, by = 3.0, -2.9
    body.append(cyl((bx, by, 1.3), 0.55, 0.35, srgb(60, 60, 70), segs=8))
    body.append(rod((bx, by, 1.4), (bx + 0.3, by, 2.4), 0.12, BARK, segs=5))
    body.append(rod((bx + 0.3, by, 2.4), (bx - 0.2, by + 0.1, 3.0), 0.1, BARK, segs=5))
    for k, (x, y, z, r) in enumerate([(0.4, 0, 2.6, 0.55), (-0.3, 0.1, 3.1, 0.5), (0.1, -0.2, 3.3, 0.4)]):
        body.append(ico((bx + x, by + y, z), r, fn=vary(srgb(255, 170, 200), 0.08, k), sub=1, jit=0.1, seed=k))
    return platform("SamuraiShiba", top, body)


@model("Platform_VampireShiba", P2)
def platform_vampire():
    top = 2.0
    soil, coffin, lid, silver = srgb(62, 46, 52), srgb(75, 38, 42), srgb(48, 24, 30), srgb(200, 200, 215)
    body = [lathe([(4.6, SINK, 0.02), (4.7, 0.05), (4.3, 0.18), (0, 0.18)], segs=12, fn=vary(soil, 0.08), seed=7)]
    # Coffin lying on the grave, head end at the back; lid a bit wider, silver trim and handles, a red bat emblem.
    pts = [(-1.1, -3.4), (1.1, -3.4), (2.0, 1.6), (1.3, 3.4), (-1.3, 3.4), (-2.0, 1.6)]
    body.append(prism(pts, 1.7 - SINK, fn=vary(coffin, 0.05), loc=(0, 0, (SINK + 1.7) / 2)))
    body.append(prism(pts, 0.1, silver, loc=(0, 0, 1.62), scale=(1.07, 1.05, 1)))
    body.append(prism(pts, 0.3, fn=vary(lid, 0.04), loc=(0, 0, top - 0.15), scale=(1.04, 1.03, 1)))
    for s in (-1, 1):
        for y in (-1.6, 0.6):
            body.append(cube((s * (1.5 + 0.25 * (y + 3.4) / 5.0), y, 1.0), (0.12, 0.7, 0.15), silver,
                             rot=(0, 0, s * -0.18)))
    body.append(prism([(0, 0.35), (0.3, 0.05), (0.9, 0.3), (0.55, -0.2), (0, -0.05), (-0.55, -0.2), (-0.9, 0.3),
                       (-0.3, 0.05)], 0.06, srgb(200, 20, 40), loc=(0, -2.6, top + 0.02)))
    # Tombstones and a spiked iron fence behind, candles in front, two bats.
    for (x, y, w, h, a) in [(-3.0, 3.2, 1.3, 2.2, 0.35), (3.2, 2.6, 1.1, 1.8, -0.4)]:
        body.append(cube((x, y, SINK + h / 2), (w, 0.4, h), fn=vary(STONE, 0.06), rot=(0.08, 0, a)))
        body.append(cyl((x, y, SINK + h), w / 2, 0.4, fn=vary(STONE, 0.06), segs=10, rot=(math.pi / 2, 0, a)))
        body.append(cube((x - 0.21 * math.sin(a), y - 0.21 * math.cos(a) + 0.01, SINK + h * 0.72), (0.12, 0.05, 0.7),
                         STONE_DARK, rot=(0, 0, a)))
        body.append(cube((x - 0.21 * math.sin(a), y - 0.21 * math.cos(a) + 0.01, SINK + h * 0.8), (0.42, 0.05, 0.12),
                         STONE_DARK, rot=(0, 0, a)))
    for k in range(9):
        a = math.radians(55 + k * 8.75)
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(rod(d * 4.5 + Vector((0, 0, SINK)), d * 4.5 + Vector((0, 0, 2.6)), 0.06, BLACK, segs=4))
        body.append(cyl(d * 4.5 + Vector((0, 0, 2.75)), 0.13, 0.3, BLACK, segs=4, r2=0))
    for z in (0.9, 2.2):
        body.append(torus((0, 0, z), 4.5, 0.05, BLACK, segs=24, minor=3, arc=math.radians(70),
                          rot=(0, 0, math.radians(55))))
    for k, (x, y, h) in enumerate([(-2.6, -2.9, 0.9), (2.7, -2.7, 0.7), (-3.6, -0.9, 0.6)]):
        body.append(cyl((x, y, h / 2), 0.16, h, CREAM_W, segs=6))
        body += flame((x, y, h), 0.4, k)
    for (x, y, z, a) in [(-2.2, 3.8, 4.4, 0.3), (1.8, 4.2, 5.0, -0.4)]:
        body.append(ico((x, y, z), 0.2, BLACK, sub=1))
        body.append(prism([(0, 0), (0.5, 0.3), (0.9, 0.1), (0.75, -0.15), (0.5, -0.05), (0.3, -0.2)], 0.04, BLACK,
                          loc=(x, y, z), rot=(math.pi / 2, 0, a)))
        body.append(prism([(0, 0), (-0.5, 0.3), (-0.9, 0.1), (-0.75, -0.15), (-0.5, -0.05), (-0.3, -0.2)], 0.04,
                          BLACK, loc=(x, y, z), rot=(math.pi / 2, 0, a)))
    return platform("VampireShiba", top, body)


@model("Platform_PharaohShiba", P2)
def platform_pharaoh():
    top = 2.5
    sand, sand_d, blue, red = srgb(225, 190, 120), srgb(190, 150, 90), srgb(35, 70, 190), srgb(200, 60, 40)
    body = []
    steps = [(8.2, SINK, 0.8), (6.8, 0.8, 1.6), (5.4, 1.6, 2.4)]
    for k, (w, z0, z1) in enumerate(steps):
        body.append(cube((0, 0, (z0 + z1) / 2), (w, w, z1 - z0), fn=vary(sand if k % 2 == 0 else mix(sand, sand_d, 0.3),
                                                                           0.05, k)))
        # Hieroglyph band on all four faces: small blue, gold and red tiles.
        rnd = random.Random(k)
        for side in range(4):
            a = side * math.pi / 2
            out = Vector((math.cos(a - math.pi / 2), math.sin(a - math.pi / 2), 0))
            along = Vector((-out.y, out.x, 0))
            n = int(w / 0.7)
            for j in range(n):
                t = (j - (n - 1) / 2) * 0.62
                c = [blue, GOLD, red, blue][rnd.randrange(4)]
                sz = (0.32, 0.05, 0.4) if j % 3 else (0.18, 0.05, 0.5)
                body.append(cube(out * (w / 2 + 0.01) + along * t + Vector((0, 0, (z0 + z1) / 2 + (0.05 if j % 2 else -0.05))),
                                 sz, c, rot=(0, 0, a)))
    body.append(cube((0, 0, 2.45), (4.8, 4.8, 0.1), fn=metal(GOLD)))
    # Gold scarab on the front of the top step.
    body.append(ico((0, -2.75, 2.0), 0.35, fn=metal(GOLD), sub=1, scale=(1, 0.5, 0.8)))
    body.append(ico((0, -2.8, 2.0), 0.18, blue, sub=1, scale=(1, 0.5, 0.8)))
    for s in (-1, 1):
        body.append(prism([(0, 0), (0.7, 0.25), (0.6, -0.1)], 0.05, fn=metal(GOLD), loc=(s * 0.2, -2.78, 2.0),
                          rot=(math.pi / 2, 0, 0), scale=(s, 1, 1)))
    # Obelisks with gold tips at the back corners.
    for s in (-1, 1):
        o = (s * 3.55, 3.55, 0)
        body.append(lathe([(0.55, SINK), (0.42, 4.8), (0.43, 4.8), (0, 4.8)], segs=4, loc=o, fn=vary(sand, 0.04),
                          phase=math.pi / 4))
        body.append(lathe([(0.44, 4.78), (0, 5.5)], segs=4, loc=o, fn=metal(GOLD), phase=math.pi / 4))
        for j in range(4):
            body.append(cube((o[0], o[1] - 0.5 + 0.02 * j, 1.2 + j * 0.8), (0.28, 0.05, 0.35), blue if j % 2 else red))
    return platform("PharaohShiba", top, body)


@model("Platform_DragonShiba", P2)
def platform_dragon():
    top = 2.6
    rock, rock_d = srgb(88, 76, 72), srgb(58, 50, 50)
    body = [lathe([(4.5, SINK, 0.04), (4.65, 0.4, 0.06), (4.2, 1.0, 0.05), (3.8, 1.35, 0.03), (0, 1.35)], segs=11,
                  fn=lambda p, n, i: vary(rock if i % 3 else rock_d, 0.1, i)(p, n, i), seed=31)]
    mound = [(4.0, 1.2), (3.6, 1.8), (2.7, 2.35), (2.0, top), (0, top)]
    body.append(lathe(mound, segs=12, fn=metal(GOLD, 0.35), phase=0.2))
    rnd = random.Random(8)
    for k in range(22):
        a, d = rnd.uniform(0, 6.3), rnd.uniform(2.1, 3.9)
        z = surf_z(mound, d) + 0.03
        body.append(cyl((math.cos(a) * d, math.sin(a) * d, z), 0.32, 0.07, fn=metal(GOLD_LIGHT if k % 3 else GOLD, 0.3, k),
                        segs=8, rot=(rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 0)))
    for k in range(10):
        a, d = rnd.uniform(0, 6.3), rnd.uniform(4.3, 5.0)
        body.append(cyl((math.cos(a) * d, math.sin(a) * d, 0.02), 0.3, 0.07, fn=metal(GOLD, 0.3, k), segs=8,
                        rot=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)))
    for k, (a, d, c) in enumerate([(0.3, 3.1, srgb(230, 30, 60)), (1.9, 2.8, srgb(40, 200, 90)),
                                   (3.4, 3.3, srgb(60, 130, 255)), (4.9, 3.0, srgb(230, 30, 60)),
                                   (5.8, 3.6, srgb(180, 60, 230))]):
        body.append(ico((math.cos(a) * d, math.sin(a) * d, surf_z(mound, d) + 0.12), 0.26, fn=metal(c, 0.4), sub=1,
                        scale=(1, 1, 1.3)))
    # Goblet (front left), a sword stuck in the hoard (back right), a crown (front right), dark crags at the back.
    body.append(lathe([(0.35, 0.02), (0.1, 0.1), (0.08, 0.6), (0.4, 0.95), (0.35, 1.2), (0, 0.95)], segs=8,
                      loc=(-3.2, -2.9, 0), fn=metal(GOLD)))
    sw = Vector((2.4, 2.1, surf_z(mound, 3.2)))
    tip_dir = Vector((0.15, 0.2, 1)).normalized()
    body.append(cube(sw + tip_dir * 1.0, (0.35, 0.08, 2.4), fn=metal(SILVER), rot=tilt(tip_dir)))
    body.append(cube(sw + tip_dir * 2.25, (1.2, 0.2, 0.2), fn=metal(GOLD), rot=tilt(tip_dir)))
    body.append(cyl(sw + tip_dir * 2.75, 0.1, 0.8, srgb(110, 40, 30), segs=6, rot=tilt(tip_dir)))
    body.append(ico(sw + tip_dir * 3.2, 0.17, srgb(230, 30, 60), sub=1))
    cr = Vector((2.9, -2.2, surf_z(mound, 3.65) + 0.2))
    body.append(cyl(cr, 0.45, 0.35, fn=metal(GOLD), segs=10, rot=(0.3, -0.2, 0)))
    for k in range(5):
        a = 2 * math.pi * k / 5
        body.append(cyl(cr + Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 0.3)), 0.12, 0.35, fn=metal(GOLD), segs=4,
                        r2=0))
    for k, (x, y, r, h) in enumerate([(-2.6, 3.9, 0.9, 3.4), (-1.0, 4.4, 0.7, 2.4), (3.9, 2.7, 0.7, 2.2)]):
        body.append(cyl((x, y, SINK + h / 2), r, h, fn=vary(rock_d, 0.1, k), segs=5, r2=0.15, jit=0.08, seed=k))
    return platform("DragonShiba", top, body)


# --- The next ten Shibas (models built by another pass; AssetNames per the tier contract) ---
@model("Platform_DJShiba", P2)
def platform_dj():
    top = 1.4
    stage = srgb(30, 30, 38)
    body = [lathe([(4.6, SINK), (4.6, 0.9), (4.4, 1.2), (0, 1.2)], segs=16,
                  fn=lambda p, n, i: vary(stage, 0.05)(p, n, i))]
    body.append(torus((0, 0, 0.95), 4.62, 0.09, srgb(255, 60, 200), segs=24, minor=3))
    body.append(torus((0, 0, 0.45), 4.62, 0.07, srgb(60, 230, 255), segs=24, minor=3))
    # Light-up dance floor: glowing tiles in five neon colours.
    neon = [srgb(255, 60, 200), srgb(60, 230, 255), srgb(255, 230, 60), srgb(120, 255, 90), srgb(170, 90, 255)]
    rnd = random.Random(3)
    for ix in range(-4, 4):
        for iy in range(-4, 4):
            x, y = ix + 0.5, iy + 0.5
            if math.hypot(x, y) < 3.9:
                body.append(cube((x * 0.98, y * 0.98, 1.3), (0.9, 0.9, 0.2), neon[rnd.randrange(5)]))
    # Speaker stacks left and right at the back, turned toward the field.
    for s in (-1, 1):
        a = s * -0.35
        c = Vector((s * 3.6, 2.5, 0))
        for k, (w, z0, z1) in enumerate([(1.8, SINK, 1.7), (1.5, 1.7, 3.1)]):
            zc = (z0 + z1) / 2
            body.append(cube(c + Vector((0, 0, zc)), (w, 1.3, z1 - z0), fn=vary(srgb(25, 25, 30), 0.05), rot=(0, 0, a)))
            f = c + Vector((math.sin(a) * -0.66, -math.cos(a) * 0.66, zc))
            body.append(cyl(f, w * 0.3, 0.1, srgb(90, 90, 100), segs=10, rot=(math.pi / 2, 0, a)))
            body.append(cyl(f - Vector((math.sin(a) * 0.04, math.cos(a) * 0.04, 0)), w * 0.12, 0.12, neon[k + (s > 0)],
                            segs=8, rot=(math.pi / 2, 0, a)))
    # DJ deck at the back with two turntables and a mixer; a disco ball on a truss above.
    body.append(cube((0, 3.55, 1.85), (3.2, 1.2, 1.3), fn=vary(srgb(40, 40, 50), 0.04)))
    body.append(cube((0, 2.94, 1.85), (3.0, 0.05, 0.3), srgb(60, 230, 255)))
    for x in (-0.9, 0.9):
        body.append(cyl((x, 3.55, 2.55), 0.5, 0.1, BLACK, segs=12))
        body.append(torus((x, 3.55, 2.62), 0.35, 0.04, srgb(255, 60, 200), segs=12, minor=3))
    body.append(cube((0, 3.55, 2.56), (0.5, 0.8, 0.12), srgb(90, 90, 100)))
    body.append(rod((0, 4.25, 1.1), (0, 4.25, 8.0), 0.12, srgb(160, 160, 175), segs=4))
    body.append(rod((0, 4.25, 8.0), (0, 3.2, 8.0), 0.1, srgb(160, 160, 175), segs=4))
    body.append(ico((0, 3.2, 7.4), 0.65, fn=lambda p, n, i: mix(srgb(150, 155, 170), WHITE, random.Random(i).random()),
                    sub=2))
    body += sparkle((-2.5, -3.2, 3.2), 0.4, srgb(255, 60, 200)) + sparkle((2.8, -2.6, 4.0), 0.35, srgb(60, 230, 255))
    return platform("DJShiba", top, body)


@model("Platform_KnightShiba", P2)
def platform_knight():
    top = 2.8
    stone, stone_d = srgb(165, 162, 172), srgb(115, 112, 125)
    prof = [(3.9, SINK)] + [(3.9, z) for z in (0.0, 0.45, 0.9, 1.35, 1.8, 2.25)] + [(4.35, 2.4), (4.35, top), (0, top)]

    def brick(p, n, i):
        if n.z > 0.9:
            return vary(mix(stone, WHITE, 0.15), 0.05)(p, n, i)
        row = int((p.z + 1) / 0.45)
        return mul(stone if (i + row) % 3 else stone_d, 1 + random.Random(i).uniform(-0.07, 0.07))
    body = [lathe(prof, segs=14, fn=brick)]
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(cube(d * 4.0 + Vector((0, 0, top + 0.45)), (1.3, 0.7, 0.95), fn=vary(stone, 0.06, k),
                         rot=(0, 0, a + math.pi / 2)))
    # Heraldic banners on the tower (front and sides) and a pennant flying from a pole at the back.
    red, blue = srgb(200, 35, 45), srgb(40, 70, 180)
    for k, a in enumerate((-math.pi / 2, -math.pi / 2 + 1.3, -math.pi / 2 - 1.3)):
        d = Vector((math.cos(a), math.sin(a), 0))
        c = d * 3.97 + Vector((0, 0, 1.2))
        body.append(cube(c, (1.4, 0.08, 1.9), red if k == 0 else blue, rot=(0, 0, a + math.pi / 2)))
        body.append(prism([(0, 0.5), (0.4, 0), (0, -0.5), (-0.4, 0)], 0.06, fn=metal(GOLD), loc=c + d * 0.06,
                          rot=tilt(d)))
        body.append(prism([(-0.7, 0), (0.7, 0), (0, -0.45)], 0.08, red if k == 0 else blue, loc=c + Vector((0, 0, -1.05)),
                          rot=(math.pi / 2, 0, a + math.pi / 2)))
    body.append(rod((-2.4, 2.4, top - 0.1), (-2.4, 2.4, top + 6.0), 0.08, srgb(120, 80, 45), segs=6))
    body.append(ico((-2.4, 2.4, top + 6.1), 0.16, GOLD, sub=1))
    body.append(prism([(0, 0.55), (2.4, 0.1), (0, -0.55)], 0.05, red, loc=(-2.4, 2.4, top + 5.35), rot=(math.pi / 2, 0, 0.2)))
    return platform("KnightShiba", top, body)


@model("Platform_SuperheroShiba", P2)
def platform_superhero():
    top = 2.6
    wall, roof, lit, dark = srgb(90, 110, 160), srgb(150, 150, 158), srgb(255, 225, 120), srgb(35, 45, 80)
    body = [cube((0, 0, (SINK + 2.5) / 2), (8.0, 8.0, 2.5 - SINK), fn=vary(wall, 0.03)),
            cube((0, 0, 2.55), (7.6, 7.6, 0.1), fn=vary(roof, 0.04))]
    for s in (-1, 1):
        body.append(cube((s * 3.9, 0, 2.75), (0.3, 8.2, 0.5), srgb(200, 200, 210)))
        body.append(cube((0, s * 3.9, 2.75), (7.5, 0.3, 0.5), srgb(200, 200, 210)))
    rnd = random.Random(4)
    for side in range(4):
        a = side * math.pi / 2
        out = Vector((math.cos(a - math.pi / 2), math.sin(a - math.pi / 2), 0))
        along = Vector((-out.y, out.x, 0))
        for j in range(5):
            for zz in (0.35, 1.5):
                if side == 0 and abs(j - 2) <= 1:
                    continue  # the hero emblem goes there
                body.append(cube(out * 4.01 + along * (j - 2) * 1.45 + Vector((0, 0, zz)), (0.9, 0.06, 0.7),
                                 lit if rnd.random() < 0.55 else dark, rot=(0, 0, a)))
    # Hero emblem on the front facade: a gold star in a red circle with a gold rim.
    body.append(cyl((0, -4.05, 1.05), 1.35, 0.12, srgb(210, 30, 40), segs=16, rot=(math.pi / 2, 0, 0)))
    body.append(torus((0, -4.08, 1.05), 1.35, 0.1, GOLD, segs=16, minor=3, rot=(math.pi / 2, 0, 0)))
    body.append(prism(star_pts(5, 1.0, 0.42), 0.12, fn=metal(GOLD), loc=(0, -4.15, 1.05), rot=(math.pi / 2, 0, 0)))
    # Rooftop: water tower (back right), AC unit (back left), antenna, a searchlight.
    wx, wy = 2.6, 2.6
    for dx in (-0.6, 0.6):
        for dy in (-0.6, 0.6):
            body.append(rod((wx + dx, wy + dy, 2.6), (wx + dx * 0.8, wy + dy * 0.8, 4.2), 0.08, srgb(70, 60, 55), segs=4))
    body.append(lathe([(0.95, 4.2), (0.95, 5.8), (1.05, 5.85), (0.6, 6.5), (0, 6.7)], segs=10, loc=(wx, wy, 0),
                      fn=lambda p, n, i: WOOD if p.z < 5.84 else srgb(80, 70, 65)))
    body.append(torus((wx, wy, 4.7), 0.97, 0.05, IRON, segs=10, minor=3))
    body.append(torus((wx, wy, 5.4), 0.97, 0.05, IRON, segs=10, minor=3))
    body.append(cube((-2.6, 2.8, 3.1), (1.5, 1.1, 1.0), srgb(185, 188, 195)))
    body.append(cyl((-2.6, 2.8, 3.62), 0.4, 0.06, srgb(60, 60, 70), segs=8))
    body.append(rod((-3.1, -2.9, 2.6), (-3.1, -2.9, 6.5), 0.06, srgb(70, 70, 80), segs=4))
    body.append(ico((-3.1, -2.9, 6.55), 0.14, srgb(255, 50, 50), sub=1))
    body.append(cyl((3.0, -2.9, 3.0), 0.45, 0.8, srgb(70, 70, 80), segs=8))
    body.append(cyl((3.0, -2.9, 3.6), 0.5, 0.5, srgb(200, 200, 210), segs=8, rot=(-0.6, 0.4, 0)))
    body.append(cyl((3.2, -3.2, 3.8), 0.4, 0.06, srgb(255, 250, 200), segs=8, rot=(-0.6, 0.4, 0)))
    return platform("SuperheroShiba", top, body)


@model("Platform_FrostShiba", P2)
def platform_frost():
    top = 2.3
    ice, ice_d, ice_l, snow = srgb(160, 220, 245), srgb(90, 165, 220), srgb(215, 245, 255), srgb(250, 252, 255)
    body = [lathe([(4.0, SINK, 0.04), (4.35, 0.7, 0.07), (4.1, 1.5, 0.05), (3.75, 2.0, 0.02), (0, 2.0)], segs=8,
                  fn=lambda p, n, i: mix(ice_d, ice_l, random.Random(i).random() * 0.8 + max(0.0, n.dot(LIGHT)) * 0.3),
                  seed=41, phase=0.1)]
    body.append(lathe([(3.75, 1.85, 0.02), (3.9, 2.05, 0.02), (3.5, top, 0), (0, top)], segs=12,
                      fn=vary(snow, 0.03), seed=42))
    # Icicles hanging under the snow lip, crystal clusters around the foot (tallest at the back).
    for k in range(14):
        a = 2 * math.pi * k / 14 + 0.1
        d = Vector((math.cos(a), math.sin(a), 0))
        L = 0.6 + 0.5 * ((k * 7) % 3) / 2
        body.append(cyl(d * 3.85 + Vector((0, 0, 1.9 - L / 2)), 0.16, L, ice_l, segs=4, r2=0, rot=(math.pi, 0, 0)))
    for k, (a, h) in enumerate([(1.2, 4.2), (1.7, 3.2), (2.4, 2.4), (-0.4, 2.0), (3.6, 1.8), (-1.9, 1.5), (0.6, 2.8)]):
        d = Vector((math.cos(a), math.sin(a), 0))
        for j in range(3):
            lean = (d * (0.35 + 0.15 * j) + Vector((0.2 * (j - 1), 0, 1))).normalized()
            base = d * (4.2 + 0.2 * j) + Vector((0, 0, SINK))
            hh = h * (1 - 0.25 * j)
            body.append(cyl(base + lean * hh * 0.4, 0.3 - 0.05 * j, hh * 0.8, fn=metal(ice, 0.35, k * 3 + j), segs=6,
                            rot=tilt(lean)))
            body.append(cyl(base + lean * hh * 0.9, 0.3 - 0.05 * j, hh * 0.2, fn=metal(ice_l, 0.3), segs=6, r2=0,
                            rot=tilt(lean)))
    for k, (x, y, r) in enumerate([(-3.5, -2.8, 0.45), (3.2, -3.2, 0.35)]):
        body.append(ico((x, y, 0.1), r, snow, sub=1, jit=0.05, seed=k))
    body += sparkle((-2.8, -3.0, 3.8), 0.45, WHITE) + sparkle((3.0, -1.8, 4.6), 0.35, ice_l)
    return platform("FrostShiba", top, body)


@model("Platform_MagmaShiba", P2)
def platform_magma():
    top = 2.4
    basalt, basalt_d, lava, lava_l = srgb(52, 44, 46), srgb(32, 28, 30), srgb(255, 110, 20), srgb(255, 210, 60)

    def rockfn(p, n, i):
        if random.Random(i * 13).random() < 0.1:
            return lava
        return vary(basalt if n.z > 0.5 else basalt_d, 0.12, i)(p, n, i)
    body = [lathe([(4.2, SINK, 0.05), (4.4, 0.6, 0.07), (4.0, 1.5, 0.05), (3.5, top, 0), (0, top)], segs=10, fn=rockfn,
                  seed=51)]
    # Glowing lava moat around the foot and lava running down the sides, cracks glowing on top.
    body.append(lathe([(5.2, SINK), (5.2, 0.05), (4.0, 0.05), (4.0, SINK)], segs=18,
                      fn=lambda p, n, i: lava if i % 3 else lava_l))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [d * 3.5 + Vector((0, 0, top - 0.02)), d * 4.12 + Vector((0, 0, 1.4)), d * 4.45 + Vector((0, 0, 0.55)),
               d * 4.5 + Vector((0, 0, 0.0))]
        for j, (p0, p1) in enumerate(zip(pts, pts[1:])):
            body.append(rod(p0 + d * 0.05, p1 + d * 0.05, 0.2 - 0.03 * j, lava if j % 2 else lava_l, segs=4))
    for (x, y, a, L) in [(1.2, 1.0, 0.6, 3.2), (-1.4, -0.6, -0.8, 2.6), (0.4, -2.0, 1.6, 2.0), (-1.0, 2.0, 2.4, 1.8)]:
        body.append(cube((x, y, top + 0.01), (0.2, L, 0.04), lava, rot=(0, 0, a)))
    # Two little vents at the back spitting lava blobs.
    for k, (x, y, h) in enumerate([(-2.8, 3.2, 2.8), (2.9, 3.0, 2.0)]):
        body.append(lathe([(1.1, SINK), (0.5, h), (0.32, h), (0, h - 0.1)], segs=7, loc=(x, y, 0), fn=vary(basalt_d, 0.1, k)))
        body.append(cyl((x, y, h - 0.02), 0.34, 0.06, lava_l, segs=7))
        for j in range(3):
            body.append(ico((x + 0.3 * (j - 1), y - 0.2 * j, h + 0.6 + 0.7 * j), 0.18 - 0.03 * j, lava if j else lava_l, sub=1))
    return platform("MagmaShiba", top, body)


@model("Platform_MechaShiba", P2)
def platform_mecha():
    top = 1.8
    steel, dark, cyan, yellow = srgb(140, 150, 165), srgb(55, 60, 72), srgb(60, 230, 255), srgb(250, 200, 40)

    def fn(p, n, i):
        if n.z > 0.9 and p.z > top - 0.01:
            return vary(dark, 0.03)(p, n, i)
        if 0.72 < p.z < 1.48 and abs(n.z) < 0.5:
            return yellow if i % 2 else BLACK
        return metal(steel, 0.3, i)(p, n, i)
    body = [lathe([(4.6, SINK), (4.6, 0.6), (4.35, 0.7), (4.35, 1.5), (4.0, top), (0, top)], segs=6, fn=fn, phase=0.0)]
    # Glowing hex outline and landing ring on top, chevrons pointing to the centre.
    for k in range(6):
        a0, a1 = 2 * math.pi * k / 6, 2 * math.pi * (k + 1) / 6
        p0 = Vector((math.cos(a0), math.sin(a0), 0)) * 3.5
        p1 = Vector((math.cos(a1), math.sin(a1), 0)) * 3.5
        body.append(cube((p0 + p1) / 2 + Vector((0, 0, top + 0.02)), ((p1 - p0).length, 0.14, 0.05), cyan,
                         rot=(0, 0, math.atan2(p1.y - p0.y, p1.x - p0.x))))
        am = (a0 + a1) / 2
        d = Vector((math.cos(am), math.sin(am), 0))
        body.append(prism([(-0.4, 0.25), (0, -0.2), (0.4, 0.25), (0.4, 0.05), (0, -0.4), (-0.4, 0.05)], 0.05, yellow,
                          loc=d * 2.6 + Vector((0, 0, top + 0.02)), rot=(0, 0, am + math.pi / 2)))
        # Hydraulic legs at each corner.
        c = Vector((math.cos(a0), math.sin(a0), 0))
        body.append(rod(c * 4.75 + Vector((0, 0, SINK)), c * 4.5 + Vector((0, 0, 1.2)), 0.32, dark, segs=6))
        body.append(rod(c * 4.62 + Vector((0, 0, 0.5)), c * 4.45 + Vector((0, 0, 1.55)), 0.2, SILVER, segs=6))
        body.append(ico(c * 4.4 + Vector((0, 0, 1.62)), 0.14, srgb(255, 60, 60) if k % 2 else srgb(60, 255, 120), sub=1))
    body.append(torus((0, 0, top + 0.02), 2.0, 0.07, yellow, segs=18, minor=3))
    # Two pylons with antennas and lights at the back.
    for s in (-1, 1):
        x, y = s * 2.3, 3.4
        body.append(cube((x, y, top + 1.0), (0.7, 0.7, 2.0), fn=metal(steel, 0.3)))
        body.append(cube((x, y - 0.36, top + 1.3), (0.4, 0.04, 1.0), cyan))
        body.append(rod((x, y, top + 2.0), (x, y, top + 3.4), 0.05, dark, segs=4))
        body.append(ico((x, y, top + 3.45), 0.16, cyan, sub=1))
    return platform("MechaShiba", top, body)


@model("Platform_AngelShiba", P2)
def platform_angel():
    top = 2.2
    white, shade = srgb(252, 252, 255), srgb(205, 215, 240)
    cloud = lambda p, n, i: mix(shade, white, (p.z + 0.5) / 2.2 + max(0.0, n.z) * 0.4)
    body = [lathe([(4.4, SINK), (4.6, 0.5), (4.0, 1.4), (0, 1.5)], segs=10, fn=cloud)]
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        d = 4.3 + 0.4 * (k % 2)
        body.append(ico((math.cos(a) * d, math.sin(a) * d, 0.55 + 0.25 * (k % 3)), 1.35 - 0.25 * (k % 2), fn=cloud, sub=2,
                        jit=0.08, seed=k, clamp_z=SINK))
    # Golden disc with a marble top and a thick gold rim, gold beads around.
    body.append(lathe([(3.4, 1.3), (3.7, 1.8), (3.6, 2.05), (0, 2.05)], segs=16, fn=metal(GOLD)))
    body.append(cyl((0, 0, 2.12), 3.25, 0.16, fn=vary(srgb(250, 246, 235), 0.02), segs=16))
    body.append(torus((0, 0, 2.12), 3.45, 0.14, fn=metal(GOLD), segs=24, minor=4))
    for k in range(12):
        a = 2 * math.pi * k / 12
        body.append(ico((math.cos(a) * 3.72, math.sin(a) * 3.72, 1.62), 0.16, fn=metal(GOLD_LIGHT), sub=1))
    # A pair of white wings with gold edges rising at the sides, a floating halo above the back.
    for s in (-1, 1):
        root = Vector((s * 3.9, 0.9, 1.5))
        for k in range(5):
            L = 3.2 - 0.45 * k
            ang = math.radians(20 + 14 * k)
            d = Vector((s * math.cos(ang), 0.15, math.sin(ang)))
            c = root + d * L / 2 + Vector((0, 0.05 * k, -0.1 * k))
            col = GOLD_LIGHT if k == 0 else white
            body.append(prism([(-L / 2, -0.28), (L / 2 - 0.3, -0.25), (L / 2, 0), (L / 2 - 0.3, 0.25), (-L / 2, 0.3)],
                              0.12, col, loc=c, rot=(math.pi / 2, -s * ang, 0), scale=(s, 1, 1)))
    body.append(torus((0, 3.2, 8.2), 1.1, 0.16, fn=metal(GOLD_LIGHT), segs=18, minor=4, rot=(math.radians(70), 0, 0)))
    for loc, sz in [((-3.4, -3.2, 3.4), 0.45), ((3.2, -3.0, 4.4), 0.4), ((0.5, -4.4, 2.9), 0.3)]:
        body += sparkle(loc, sz, GOLD_LIGHT)
    return platform("AngelShiba", top, body)


@model("Platform_DemonShiba", P2)
def platform_demon():
    top = 2.0
    obs, obs_l, crack = srgb(34, 20, 40), srgb(70, 45, 80), srgb(255, 50, 20)

    def fn(p, n, i):
        if random.Random(i * 17).random() < 0.1:
            return crack
        return mix(obs, obs_l, max(0.0, n.dot(LIGHT)) * 0.9 + random.Random(i).uniform(0, 0.15))
    body = [lathe([(4.1, SINK, 0.05), (4.5, 0.6, 0.08), (4.1, 1.4, 0.05), (3.6, top, 0), (0, top)], segs=9, fn=fn,
                  seed=61)]
    for (x, y, a, L) in [(1.5, 0.6, 0.4, 3.4), (-1.5, -0.8, -0.9, 3.0), (0.2, -2.4, 1.5, 2.2), (-0.8, 2.3, 2.6, 2.0)]:
        body.append(cube((x, y, top + 0.01), (0.18, L, 0.04), crack, rot=(0, 0, a)))
    # Obsidian spikes around the edge leaning outward (tallest at the back), two big horns curling up behind.
    rnd = random.Random(62)
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.2
        d = Vector((math.cos(a), math.sin(a), 0))
        h = 1.6 + 1.8 * max(0.0, math.sin(a)) + rnd.uniform(0, 0.5)
        lean = (d * 0.4 + Vector((0, 0, 1))).normalized()
        body.append(cyl(d * 4.2 + lean * h / 2 + Vector((0, 0, SINK)), 0.5, h, fn=lambda p, n, i: mix(obs, obs_l, max(0.0, n.dot(LIGHT))),
                        segs=5, r2=0, rot=tilt(lean)))
    for s in (-1, 1):
        pts = [Vector((s * 2.2, 3.4, 0.5)), Vector((s * 3.0, 3.6, 2.6)), Vector((s * 3.1, 3.4, 4.4)),
               Vector((s * 2.6, 2.9, 5.6)), Vector((s * 1.9, 2.5, 6.0))]
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            body.append(rod(a, b, 0.55 - 0.12 * k, srgb(120, 25, 30) if k % 2 else srgb(80, 15, 25), segs=6,
                            r2=0.45 - 0.12 * k if k < 3 else 0.02))
    # Hellfire: flames at the foot, front and sides.
    for k, (x, y, h) in enumerate([(-3.4, -2.6, 1.6), (3.3, -2.8, 1.3), (-4.3, 0.8, 1.2), (4.2, 1.0, 1.5),
                                   (0.0, -4.3, 0.9)]):
        body += flame((x, y, 0.0), h, k)
    return platform("DemonShiba", top, body)


@model("Platform_EternalShiba", P2)
def platform_eternal():
    top = 5.0
    marble, night = srgb(248, 244, 232), srgb(40, 40, 110)
    # Celestial dais: a night-blue base studded with gold stars, a white marble tier, a gold tier, and on top a
    # giant golden clock face the Shiba stands on (hour marks, two hands).
    body = [lathe([(6.6, SINK), (6.6, 0.6), (6.8, 0.65), (6.8, 0.9), (6.2, 1.0), (0, 1.0)], segs=24,
                  fn=lambda p, n, i: metal(GOLD)(p, n, i) if 0.62 < p.z < 0.92 else vary(night, 0.08)(p, n, i))]
    rnd = random.Random(71)
    for k in range(14):
        a = 2 * math.pi * k / 14 + rnd.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        body.append(prism(star_pts(4, 0.28, 0.08), 0.05, GOLD_LIGHT, loc=d * 6.62 + Vector((0, 0, 0.25)), rot=tilt(d)))
    body.append(lathe([(5.3, 0.9), (5.3, 2.4), (5.5, 2.45), (5.5, 2.7), (5.0, 2.8), (0, 2.8)], segs=20,
                      fn=lambda p, n, i: metal(GOLD)(p, n, i) if p.z > 2.42 else mul(marble, 1.0 if i % 2 else 0.9)))
    body.append(lathe([(4.2, 2.7), (4.2, 4.3), (4.45, 4.35), (4.45, 4.75), (4.3, 4.8), (4.3, top - 0.1), (0, top - 0.1)],
                      segs=24, fn=metal(GOLD, 0.3)))
    body.append(cyl((0, 0, top - 0.05), 4.0, 0.1, srgb(252, 244, 215), segs=24))
    body.append(torus((0, 0, top - 0.02), 4.1, 0.14, fn=metal(GOLD), segs=24, minor=4))
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = Vector((math.cos(a), math.sin(a), 0))
        big = k % 3 == 0
        body.append(cube(d * 3.45 + Vector((0, 0, top + 0.02)), (0.7 if big else 0.4, 0.2 if big else 0.14, 0.05),
                         srgb(40, 40, 110), rot=(0, 0, a)))
    body.append(cube((0.8, 1.3, top + 0.04), (0.28, 3.0, 0.05), srgb(40, 40, 110), rot=(0, 0, -0.55)))
    body.append(cube((-1.1, 0.6, top + 0.05), (0.32, 2.4, 0.05), srgb(40, 40, 110), rot=(0, 0, 1.05)))
    # Steps up the front.
    for k in range(3):
        body.append(cube((0, -5.6 + 0.55 * k, 1.2 + 0.55 * k), (3.0 - 0.3 * k, 1.2, 0.5), fn=metal(GOLD, 0.25) if k == 2
                         else vary(marble, 0.03)))
    # Giant standing clock behind the Shiba: gold ring with twelve marks, deep blue face with gold hands at 10:10.
    cc = Vector((0, 4.4, top + 5.8))
    face = (math.pi / 2, 0, 0)
    body.append(cyl(cc, 4.6, 0.3, night, segs=24, rot=face))
    body.append(torus(cc, 4.7, 0.35, fn=metal(GOLD), segs=24, minor=5, rot=face))
    for k in range(12):
        a = 2 * math.pi * k / 12
        p = cc + Vector((math.cos(a) * 3.9, -0.2, math.sin(a) * 3.9))
        big = k % 3 == 0
        body.append(cube(p, (0.8 if big else 0.45, 0.12, 0.28 if big else 0.18), GOLD_LIGHT, rot=(0, -a, 0)))
    for ang, L, w in [(math.radians(150), 2.6, 0.3), (math.radians(30), 3.5, 0.22)]:
        d = Vector((math.cos(ang), 0, math.sin(ang)))
        body.append(cube(cc + d * L / 2 + Vector((0, -0.25, 0)), (L, 0.08, w), fn=metal(GOLD), rot=(0, -ang, 0)))
    body.append(cyl(cc + Vector((0, -0.28, 0)), 0.35, 0.12, fn=metal(GOLD), segs=10, rot=face))
    for s in (-1, 1):
        body.append(lathe([(0.45, 2.7), (0.35, top + 1.3), (0, top + 1.3)], segs=8, loc=(s * 3.6, 4.4, 0),
                          fn=metal(GOLD)))
        body.append(ico((s * 3.6, 4.4, top + 1.5), 0.4, fn=metal(srgb(120, 220, 255)), sub=1))
    # Two armillary rings crossing around the dais, little planets on them, sparkles.
    for k, rot in enumerate([(math.radians(14), 0, 0), (math.radians(-10), math.radians(12), 0.6)]):
        body.append(torus((0, 0, 3.0 + k * 0.6), 7.0 - 0.4 * k, 0.12, fn=metal(GOLD_LIGHT), segs=32, minor=4, rot=rot))
    for (a, r, z, c, rr) in [(2.3, 7.0, 3.8, srgb(120, 220, 255), 0.4), (5.2, 6.6, 3.0, srgb(255, 130, 180), 0.32)]:
        body.append(ico((math.cos(a) * r, math.sin(a) * r, z), rr, fn=metal(c), sub=1))
    for loc, sz in [((-5.0, -3.4, 7.2), 0.6), ((5.4, -2.2, 8.6), 0.5), ((-3.4, 2.8, 12.6), 0.45), ((4.2, 3.4, 12.0), 0.4)]:
        body += sparkle(loc, sz, GOLD_LIGHT)
    return platform("EternalShiba", top, body)


@model("Platform_VoidShiba", P2)
def platform_void():
    top = 6.0
    black, purple, pink, cyan = srgb(12, 8, 22), srgb(150, 60, 255), srgb(255, 90, 210), srgb(80, 230, 255)

    def rim_col(p):
        a = math.atan2(p.y, p.x)
        t = (math.sin(a * 2) + 1) / 2
        return mix(purple, pink, t) if math.cos(a) > -0.3 else mix(purple, cyan, t)
    # Black hole on the ground: a black disc with glowing spiral arms, a glowing accretion rim in purple, pink and
    # cyan, and a thin tilted outer ring.
    body = [lathe([(9.3, SINK), (9.3, 0.05), (8.9, 0.1), (0, 0.1)], segs=32, fn=flat(black))]
    body.append(torus((0, 0, 0.3), 9.3, 0.4, fn=lambda p, n, i: rim_col(p), segs=40, minor=5))
    for arm in range(4):
        prev = None
        for k in range(11):
            t = k / 10
            r = 8.6 - 6.6 * t
            a = arm * math.pi / 2 + t * 3.0
            pt = Vector((math.cos(a) * r, math.sin(a) * r, 0.14))
            if prev is not None:
                body.append(rod(prev, pt, 0.26 * (1 - 0.6 * t), mix(purple, pink, t), segs=4))
            prev = pt
    body.append(torus((0, 0, 1.4), 10.0, 0.1, cyan, segs=40, minor=3, rot=(math.radians(6), math.radians(4), 0)))
    # A swirling vortex rising out of it to the stand: dark bands striped with purple, a glowing rim on top.
    prof = [(1.3, 0.05), (1.5, 1.5), (1.9, 2.8), (2.5, 4.0), (3.2, 5.2), (3.6, top - 0.15), (0, top - 0.15)]
    body.append(lathe(prof, segs=16, fn=lambda p, n, i: (mix(black, purple, 0.55) if (i + int(p.z * 1.2)) % 4 == 0 else black)
                      if n.z < 0.9 else flat(srgb(20, 12, 38))(p, n, i), phase=0.0))
    body.append(cyl((0, 0, top - 0.07), 3.45, 0.14, srgb(28, 16, 52), segs=16))
    body.append(torus((0, 0, top - 0.1), 3.7, 0.22, fn=lambda p, n, i: rim_col(p), segs=24, minor=4))
    # Tilted glowing rings around the vortex and floating dark crystal shards with glowing tips.
    body.append(torus((0, 0, 3.4), 5.0, 0.13, pink, segs=28, minor=3, rot=(math.radians(18), 0, 0.4)))
    body.append(torus((0, 0, 4.2), 6.2, 0.11, cyan, segs=32, minor=3, rot=(math.radians(-14), math.radians(10), 1.2)))
    rnd = random.Random(81)
    for k in range(10):
        a = 2 * math.pi * k / 10 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(6.3, 8.2)
        z = rnd.uniform(2.5, 9.0)
        axis = Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 1)).normalized()
        c = Vector((math.cos(a) * r, math.sin(a) * r, z))
        L = rnd.uniform(1.0, 1.8)
        body.append(cyl(c + axis * L * 0.25, 0.4, L * 0.5, srgb(35, 20, 60), segs=4, r2=0, rot=tilt(axis)))
        body.append(cyl(c - axis * L * 0.25, 0.4, L * 0.5, black, segs=4, r2=0, rot=tilt(-axis)))
        body.append(ico(c + axis * L * 0.52, 0.12, [purple, pink, cyan][k % 3], sub=1))
    for k in range(12):
        a, r = rnd.uniform(0, 6.3), rnd.uniform(3.5, 9.5)
        body.append(ico((math.cos(a) * r, math.sin(a) * r, rnd.uniform(1.5, 11.0)), rnd.uniform(0.08, 0.16), WHITE, sub=1))
    return platform("VoidShiba", top, body)


# ---------------------------------------------------------------------------------------------------------------
# Build, export, preview
# ---------------------------------------------------------------------------------------------------------------
EXPORT = dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH'}, colors_type='SRGB',
              apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False, global_scale=0.25)


def join(objs, name):
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(MATERIAL)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name
    j.data.name = name
    # Bake the transform, triangulate (what Roblox gets anyway; keeps jittered quads from flipping).
    j.data.transform(j.matrix_world)
    j.matrix_world = Matrix.Identity(4)
    bm = bmesh.new()
    bm.from_mesh(j.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bm.to_mesh(j.data)
    bm.free()
    for p in j.data.polygons:
        p.use_smooth = False
    return j


def export(parts, filename):
    old = {}
    for part_name, o in parts.items():
        old[o] = o.name
        o.name = part_name
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts.values():
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, filename), **EXPORT)
    for o, n in old.items():
        o.name = n


built = []  # (name, group, [objects incl. preview], tris)
for name, group, builder in MODELS:
    if ONLY and name not in ONLY:
        continue
    parts = builder()
    preview = parts.pop("_preview", [])
    meshes = {part: join(objs, f"{name}_{part}") for part, objs in parts.items()}
    export(meshes, f"{name}.fbx")
    tris = {part: len(o.data.polygons) for part, o in meshes.items()}
    mn, mx = bbox(list(meshes.values()))
    size = mx - mn
    print(f"BUILT {name}: triangles {sum(tris.values())} {tris} size {size.x:.2f} x {size.y:.2f} x {size.z:.2f} studs")
    if preview:
        preview = [join(preview, f"{name}_preview")]
    built.append((name, group, list(meshes.values()) + preview, sum(tris.values())))

# --- Preview: one 3/4-view tile per model (front-right, from above), then contact sheets ---
sc = scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = 'Standard'  # show the vertex colours as they are
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX'
sc.display.shading.show_object_outline = True
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'WORLD'
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("preview")
sc.world.color = srgb(120, 150, 190)
TILE = 600  # rendered size; the sheets shrink it
sc.render.resolution_x = sc.render.resolution_y = TILE
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("PreviewCam", cam_data)
COLL.objects.link(cam)
sc.camera = cam
label_curve = bpy.data.curves.new("Label", 'FONT')
label_curve.align_x = 'CENTER'
label = bpy.data.objects.new("Label", label_curve)
COLL.objects.link(label)
label.parent = cam
label.hide_render = True
# Views: from the front-right and above; hanging things from a little below.
VIEWS = {"Prop_IslandRock": (0.62, -1.0, -0.45)}

tiles = []
everything = [o for (_, _, objs, _) in built for o in objs]
for name, group, objs, tris in built:
    for o in everything:
        o.hide_render = True
    for o in objs:
        o.hide_render = False
    mn, mx = bbox(objs)
    centre = (mn + mx) / 2
    radius = (mx - mn).length / 2
    view = Vector(VIEWS.get(name, (0.62, -1.0, 0.55))).normalized()
    cam.location = centre + view * radius * 4
    cam.rotation_euler = (-view).to_track_quat('-Z', 'Y').to_euler()
    cam_data.ortho_scale = radius * 2.3
    cam_data.clip_end = radius * 10
    # The label is a white mesh in front of the camera (Workbench shows vertex colours only).
    label_curve.body = f"{name}   {tris} tris"
    label.scale = (radius * 0.1,) * 3
    label.location = (0, -radius * 1.05, -radius * 1.5)
    bpy.context.view_layer.update()
    text_mesh = bpy.data.meshes.new_from_object(label.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    text = bpy.data.objects.new("LabelMesh", text_mesh)
    COLL.objects.link(text)
    text.matrix_world = label.matrix_world
    bpy.context.view_layer.update()
    paint(text, flat((1, 1, 1)))
    path = os.path.join(PREVIEW, f"{name}.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(text)
    tiles.append((name, group, path))


def sheet(entries, path, cols, factor=1):
    """Tiles in a grid, each shrunk by `factor` (area average), saved as an RGB PNG."""
    import numpy as np
    t = TILE // factor
    rows = (len(entries) + cols - 1) // cols
    canvas = None
    for k, (_, _, tile_path) in enumerate(entries):
        img = bpy.data.images.load(tile_path)
        img.colorspace_settings.name = 'Non-Color'
        px = np.array(img.pixels[:], dtype=np.float32).reshape(TILE, TILE, 4)
        px = px.reshape(t, factor, t, factor, 4).mean(axis=(1, 3))
        if canvas is None:
            canvas = np.empty((rows * t, cols * t, 4), dtype=np.float32)
            canvas[:] = px[2, 2]
        r, c = k // cols, k % cols
        y0 = (rows - 1 - r) * t  # image rows go bottom-up
        canvas[y0:y0 + t, c * t:(c + 1) * t] = px
        bpy.data.images.remove(img)
    out = bpy.data.images.new("sheet", cols * t, rows * t, alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    out.pixels.foreach_set(canvas.ravel())
    settings = sc.render.image_settings
    settings.file_format = 'PNG'
    settings.color_mode = 'RGB'
    settings.compression = 100
    out.save_render(path, scene=sc)
    bpy.data.images.remove(out)


groups = []
for _, g, _ in tiles:
    if g not in groups:
        groups.append(g)
for g in groups:
    entries = [t for t in tiles if t[1] == g]
    sheet(entries, os.path.join(PREVIEW, f"sheet_{g}.png"), min(5 if g == P2 else 4, len(entries)), 2)
if not ONLY:
    sheet(tiles, os.path.join(OUT, "Props_preview.png"), 8, 2)
print("DONE", len(built), "models")
