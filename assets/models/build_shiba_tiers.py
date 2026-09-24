import bpy, math, sys, os, random
from mathutils import Vector, Matrix
# Shiba tiers 2-10 (except GalaxyShiba, see build_galaxy_shiba.py) and projectile tiers 2-10, built from
# shiba_bonk_default.blend like build_shiba.py: same posed dog, same stick in the right paw, same export settings.
# Each Shiba gets its own fur colours plus accessories made of low-poly primitives; everything is baked into vertex
# colours (Roblox ignores FBX material colours). Output: one <AssetName>.fbx per model and preview_tiers.png.
# Usage:
#   blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba_tiers.py -- <output folder>
OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(OUT, exist_ok=True)
random.seed(4)

def srgb(r, g, b):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))

def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))

def wb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))),
            Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))))

def paint(o, fn):
    """fn(world_position, material_name, face_index) -> linear rgb, per face corner."""
    me = o.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        m = me.materials[poly.material_index] if len(me.materials) else None
        name = m.name if m else ""
        for li in poly.loop_indices:
            p = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            attr.data[li].color = (*fn(p, name, poly.index), 1.0)
    me.color_attributes.active_color = attr

coll = bpy.data.collections['Collection']
for o in bpy.data.collections['Original_backup'].objects:
    o.hide_render = True

# --- Base dog and hand stick (same as build_shiba.py) ---
dog = [o for o in coll.objects if o.type == 'MESH']
WOOD = srgb(110, 62, 30)
src = bpy.data.objects['Stick_orig']
stick = src.copy(); stick.data = src.data.copy(); stick.name = "BaseStick"
stick.hide_render = False  # copied from the hidden backup collection
coll.objects.link(stick)
stick.matrix_world = Matrix.Rotation(math.radians(-90), 4, 'X') @ src.matrix_world
bpy.context.view_layer.update()
pts = [stick.matrix_world @ v.co for v in stick.data.vertices]
c = sum(pts, Vector()) / len(pts)
axis = max((b - a for a in pts[::7] for b in pts[::7]), key=lambda v: v.length).normalized()
proj = [(p - c).dot(axis) for p in pts]
if axis.z < 0: axis = -axis; proj = [-x for x in proj]
grip = c + axis * min(proj)
hmn, hmx = wb(bpy.data.objects['RightHand']); hand = (hmn + hmx) / 2
want = Vector((0.40, -0.13, 0.90)).normalized()
rot = axis.rotation_difference(want).to_matrix().to_4x4()
stick.matrix_world = Matrix.Translation(hand) @ rot @ Matrix.Translation(-grip) @ stick.matrix_world
bpy.context.view_layer.update()

# --- Landmarks of the default pose (the dog faces -Y, Z is up) ---
class L:
    pass

def landmarks(parts):
    """Positions accessories attach to, measured on the (possibly reshaped) dog parts."""
    l = L()
    head, torso, tail = parts['Head'], parts['Torso'], parts['Tail']
    l.head_min, l.head_max = wb(head); l.torso_min, l.torso_max = wb(torso)
    l.min_z = min(wb(o)[0].z for o in parts.values()); l.max_z = max(wb(o)[1].z for o in parts.values())
    hv = [head.matrix_world @ v.co for v in head.data.vertices]
    l.skull_top = max(p.z for p in hv if abs(p.x) < 0.06)
    l.head_c = (l.head_min + l.head_max) / 2
    dark = []
    for poly in head.data.polygons:
        if head.data.materials[poly.material_index].name == 'fur_dark':
            cen = head.matrix_world @ poly.center
            if abs(cen.x) > 0.05: dark.append(cen)
    # The eyes are the upper half of the dark faces off the centre line (the mouth line sits lower).
    dark.sort(key=lambda p: p.z)
    eyes = dark[len(dark) // 2:]
    l.eye_z = sum(p.z for p in eyes) / len(eyes) + 0.055
    l.eye_y = min(p.y for p in eyes) - 0.01
    l.eye_x = max(0.08, sum(abs(p.x) for p in eyes) / len(eyes))
    l.mouth = Vector((0.0, l.head_min.y + 0.07, l.eye_z - 0.17))
    l.neck_z = l.head_min.z + 0.04
    tv = [tail.matrix_world @ v.co for v in tail.data.vertices]
    l.tail_tip = max(tv, key=lambda p: p.z)
    l.back_y = l.torso_max.y; l.shoulder_z = l.torso_max.z - 0.12
    l.chest = Vector((0, l.torso_min.y - 0.01, l.torso_min.z + (l.torso_max.z - l.torso_min.z) * 0.62))
    lh_min, lh_max = wb(parts['LeftHand']); l.left_hand = (lh_min + lh_max) / 2
    return l

# --- Primitive helpers: every accessory is one flat-coloured (or gradient) mesh ---
def prim(kind, loc, rot=(0, 0, 0), scale=(1, 1, 1), color=None, fn=None, **kw):
    ops = {"cone": bpy.ops.mesh.primitive_cone_add, "cyl": bpy.ops.mesh.primitive_cylinder_add,
           "cube": bpy.ops.mesh.primitive_cube_add, "ico": bpy.ops.mesh.primitive_ico_sphere_add,
           "uv": bpy.ops.mesh.primitive_uv_sphere_add, "torus": bpy.ops.mesh.primitive_torus_add}
    ops[kind](location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.scale = scale
    bpy.context.view_layer.update()
    paint(o, fn or (lambda p, n, i: color))
    return o

def tilt(direction):
    """Euler rotation that points a primitive's +Z along `direction`."""
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_euler()

def box(loc, size, color, rot=(0, 0, 0)):
    return prim("cube", loc, rot, scale=size, color=color, size=1)

def ball(loc, radius, color, scale=(1, 1, 1), rot=(0, 0, 0), fn=None):
    return prim("uv", loc, rot, scale=tuple(radius * s for s in scale), color=color, fn=fn, segments=10, ring_count=6,
                radius=1)

def rod(a, b, radius, color, verts=8, fn=None):
    """Cylinder from point a to point b."""
    a, b = Vector(a), Vector(b)
    return prim("cyl", (a + b) / 2, tilt(b - a), color=color, fn=fn, vertices=verts, radius=radius,
                depth=(b - a).length)

def spike(base, direction, length, radius, color, verts=4, tip=None):
    d = Vector(direction).normalized()
    loc = Vector(base) + d * length / 2
    fn = None
    if tip:
        fn = lambda p, n, i: mix(color, tip, max(0.0, min(1.0, (p - Vector(base)).dot(d) / length)))
    return prim("cone", loc, tilt(d), color=color, fn=fn, vertices=verts, radius1=radius, radius2=0, depth=length)

def ring(center, radius, thickness, color, rot=(0, 0, 0), scale=(1, 1, 1), segments=24):
    return prim("torus", center, rot, scale=scale, color=color, major_radius=radius, minor_radius=thickness,
                major_segments=segments, minor_segments=6)

def sparkle(loc, size, color):
    """Four-pointed cartoon star facing the camera (-Y)."""
    return [box(loc, (size, size * 0.12, size * 0.22), color, rot=(0, math.radians(45), 0)),
            box(loc, (size * 0.22, size * 0.12, size), color, rot=(0, math.radians(45), 0)),
            box(loc, (size * 1.3, size * 0.1, size * 0.16), color),
            box(loc, (size * 0.16, size * 0.1, size * 1.3), color)]

FONT = {
    "B": ["110", "101", "110", "101", "110"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "K": ["1001", "1010", "1100", "1010", "1001"],
    "$": ["010", "111", "100", "111", "001", "111", "010"],
}

def pixel_text(text, origin, right, down, px, depth_axis, color):
    """Blocky letters: `origin` is the top-left corner, `right`/`down` the text directions."""
    right, down, depth_axis = Vector(right).normalized(), Vector(down).normalized(), Vector(depth_axis).normalized()
    out, col = [], 0
    for ch in text:
        rows = FONT[ch]
        for r, line in enumerate(rows):
            for k, bit in enumerate(line):
                if bit == "1":
                    loc = Vector(origin) + right * (col + k + 0.5) * px + down * (r + 0.5) * px
                    m = Matrix((right, down, depth_axis)).transposed()
                    out.append(prim("cube", loc, m.to_euler(), scale=(px, px, px * 0.6), color=color, size=1))
        col += len(rows[0]) + 1
    return out

def zigzag(start, direction, side, segments, seg_len, amp, radius, color):
    """Lightning bolt: a chain of short rods alternating left and right of `direction`."""
    d, s = Vector(direction).normalized(), Vector(side).normalized()
    pts = [Vector(start)]
    for k in range(1, segments + 1):
        pts.append(Vector(start) + d * seg_len * k + s * (amp if k % 2 else -amp))
    return [rod(pts[k], pts[k + 1], radius, color, verts=4) for k in range(segments)]

def transform_about(o, pivot, m):
    o.matrix_world = Matrix.Translation(pivot) @ m @ Matrix.Translation(-Vector(pivot)) @ o.matrix_world

# --- Shiba designs. Each gets fresh copies of the dog parts (dict by name) and the paw stick, may reshape them,
# and returns (colours per fur material, extra meshes). ---
ORANGE, CREAM, DARK = srgb(190, 90, 25), srgb(247, 232, 205), srgb(25, 22, 25)

def default_cols():
    return {"fur_orange": lambda p: ORANGE, "fur_cream": lambda p: CREAM, "fur_dark": lambda p: DARK}

def shades(parts, hs):
    l = landmarks(parts); ex = []
    black, gold = srgb(12, 12, 16), srgb(255, 200, 40)
    for s in (-1, 1):
        x = s * (l.eye_x + 0.02)
        ex.append(box((x, l.eye_y - 0.03, l.eye_z), (0.17, 0.03, 0.075), black))
        ex.append(box((x + s * 0.03, l.eye_y - 0.03, l.eye_z - 0.06), (0.1, 0.03, 0.05), black))
        ex += sparkle((x - s * 0.04, l.eye_y - 0.05, l.eye_z + 0.01), 0.05, srgb(255, 255, 255))
    ex.append(box((0, l.eye_y - 0.03, l.eye_z + 0.03), (l.eye_x * 2 + 0.2, 0.03, 0.03), black))
    for s in (-1, 1):
        ex.append(box((s * (l.eye_x + 0.12), l.eye_y + 0.1, l.eye_z + 0.03), (0.02, 0.22, 0.025), black))
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.25, 0.028, gold, rot=(math.radians(-18), 0, 0), segments=20))
    medal = l.chest + Vector((0, -0.03, 0.02))
    ex.append(prim("cyl", medal, (math.radians(90), 0, 0), color=gold, vertices=12, radius=0.12, depth=0.03))
    ex += pixel_text("$", medal + Vector((-0.045, -0.02, 0.105)), (1, 0, 0), (0, 0, -1), 0.03, (0, -1, 0),
                     srgb(40, 140, 60))
    tip = l.mouth + Vector((0.12, -0.14, -0.02))
    ex.append(rod(l.mouth + Vector((0.04, -0.02, 0)), tip, 0.025, srgb(120, 70, 35), verts=6))
    ex.append(prim("ico", tip, color=srgb(255, 90, 20), subdivisions=1, radius=0.03))
    return default_cols(), ex

def buff(parts, hs):
    l0 = landmarks(parts)
    tz = l0.torso_max.z - l0.torso_min.z
    grow = 1.2
    transform_about(parts['Torso'], (0, (l0.torso_min.y + l0.torso_max.y) / 2, l0.torso_min.z),
                    Matrix.Diagonal((grow, grow, grow, 1)))
    dz = tz * (grow - 1)
    transform_about(parts['Head'], (0, l0.head_c.y, l0.head_min.z),
                    Matrix.Translation((0, 0, dz)) @ Matrix.Diagonal((0.72, 0.72, 0.72, 1)))
    for side, arm_scale, push in (("Right", 1.7, 0.14), ("Left", 1.25, 0.06)):
        names = [f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"]
        up_min, up_max = wb(parts[names[0]])
        shoulder = Vector(((up_min.x + up_max.x) / 2, (up_min.y + up_max.y) / 2, up_max.z))
        s = 1 if side == "Right" else -1
        m = Matrix.Translation((s * push, 0, dz * 0.8)) @ Matrix.Diagonal((arm_scale, arm_scale, arm_scale, 1))
        moved = [parts[n] for n in names] + ([hs] if side == "Right" else [])
        for o in moved: transform_about(o, shoulder, m)
        bpy.context.view_layer.update()
        # The bigger arm hangs lower; lift it so the paw (and the stick) stays above the ground.
        low = min(wb(o)[0].z for o in moved)
        if low < 0.03:
            for o in moved: o.location.z += 0.03 - low
    bpy.context.view_layer.update()
    l = landmarks(parts); ex = []
    ex.append(ring((0, l.head_c.y, l.eye_z + 0.08), 0.21, 0.035, srgb(230, 30, 40), scale=(1, 1.1, 1)))
    muscle = srgb(235, 215, 180)
    for s in (-1, 1):
        ex.append(box(l.chest + Vector((s * 0.12, -0.01, 0.04)), (0.22, 0.05, 0.14), muscle,
                      rot=(0, s * math.radians(-8), 0)))
    for row in range(3):
        for s in (-1, 1):
            ex.append(box(Vector((s * 0.055, l.chest.y + 0.01, l.chest.z - 0.14 - row * 0.085)), (0.09, 0.04, 0.07),
                          muscle))
    return default_cols(), ex

def chef(parts, hs):
    l = landmarks(parts); ex = []
    white, grey = srgb(255, 255, 255), srgb(225, 225, 230)
    base = l.skull_top - 0.03
    ex.append(prim("cyl", (0, l.head_c.y, base + 0.2), color=white, vertices=12, radius=0.19, depth=0.4))
    for k in range(7):
        a = k * math.tau / 7
        ex.append(ball((math.cos(a) * 0.14, l.head_c.y + math.sin(a) * 0.14, base + 0.44), 0.13, white))
    ex.append(ball((0, l.head_c.y, base + 0.5), 0.15, white))
    brown = srgb(60, 32, 18)
    for s in (-1, 1):
        ex.append(ball(l.mouth + Vector((s * 0.08, -0.03, 0.03)), 0.08, brown, scale=(1, 0.35, 0.35),
                       rot=(0, s * math.radians(-15), 0)))
        ex.append(ball(l.mouth + Vector((s * 0.16, -0.03, 0.07)), 0.035, brown))
    red = srgb(215, 30, 35)
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.035, red, rot=(math.radians(-18), 0, 0), segments=16))
    ex.append(prim("cone", l.chest + Vector((0, -0.04, 0.08)), (math.radians(-90), 0, 0), color=red,
                   vertices=3, radius1=0.14, radius2=0, depth=0.03))
    apron = Vector((0, l.torso_min.y - 0.015, l.torso_min.z + 0.3))
    ex.append(box(apron, (0.34, 0.02, 0.4), white))
    for _ in range(5):
        ex.append(ball(apron + Vector((random.uniform(-0.12, 0.12), -0.015, random.uniform(-0.15, 0.15))), 0.03,
                       grey, scale=(1, 0.3, 0.8)))
    for _ in range(9):
        a = random.uniform(0, math.tau); r = random.uniform(0.4, 0.55)
        ex.append(ball((math.cos(a) * r, math.sin(a) * r * 0.8, random.uniform(0.02, 0.2)), random.uniform(0.06, 0.1),
                       random.choice([white, grey])))
    return default_cols(), ex

def police(parts, hs):
    l = landmarks(parts); ex = []
    navy, black = srgb(25, 45, 110), srgb(15, 15, 20)
    cap = l.skull_top + 0.02
    ex.append(prim("cyl", (0, l.head_c.y, cap), color=navy, vertices=14, radius=0.23, depth=0.13))
    ex.append(prim("cyl", (0, l.head_c.y - 0.16, cap - 0.06), (math.radians(-8), 0, 0), color=black, vertices=14,
                   radius=0.16, depth=0.02))
    ex.append(prim("cone", (0, l.head_c.y - 0.22, cap + 0.01), (math.radians(90), 0, 0), color=srgb(255, 200, 40),
                   vertices=5, radius1=0.045, radius2=0, depth=0.02))
    ex.append(box((0, l.head_c.y, cap + 0.08), (0.2, 0.08, 0.03), srgb(230, 230, 235)))
    ex.append(box((-0.05, l.head_c.y, cap + 0.13), (0.09, 0.08, 0.09), srgb(255, 30, 30)))
    ex.append(box((0.05, l.head_c.y, cap + 0.13), (0.09, 0.08, 0.09), srgb(30, 90, 255)))
    mirror = lambda p, n, i: mix(srgb(120, 170, 220), srgb(235, 245, 255), max(0.0, min(1.0, (p.z - l.eye_z + 0.05) / 0.1)))
    for s in (-1, 1):
        ex.append(ball((s * (l.eye_x + 0.02), l.eye_y - 0.03, l.eye_z - 0.01), 0.1, None, scale=(0.95, 0.25, 0.7),
                       fn=mirror))
    ex.append(box((0, l.eye_y - 0.03, l.eye_z + 0.04), (l.eye_x * 2, 0.02, 0.02), srgb(200, 170, 60)))
    ex.append(prim("cone", l.chest + Vector((0.12, -0.02, 0.05)), (math.radians(90), 0, 0), color=srgb(255, 205, 50),
                   vertices=5, radius1=0.07, radius2=0.035, depth=0.025))
    donut = l.left_hand + Vector((-0.04, -0.1, 0.1))
    frosting = lambda p, n, i: srgb(255, 120, 190) if p.y < donut.y - 0.005 else srgb(215, 150, 80)
    ex.append(prim("torus", donut, (math.radians(80), 0, 0), fn=frosting, major_radius=0.08, minor_radius=0.04,
                   major_segments=14, minor_segments=6))
    return default_cols(), ex

def ninja(parts, hs):
    l = landmarks(parts); ex = []
    cols = {"fur_orange": lambda p: srgb(24, 24, 30), "fur_cream": lambda p: srgb(58, 58, 70),
            "fur_dark": lambda p: srgb(255, 30, 40)}
    red = srgb(210, 25, 35)
    band_z = l.eye_z + 0.09
    ex.append(ring((0, l.head_c.y, band_z), 0.285, 0.035, red, scale=(1, 1.12, 1), segments=20))
    knot = Vector((0, l.head_max.y - 0.02, band_z))
    for s, drop in ((-1, 0.1), (1, 0.18)):
        end = knot + Vector((s * 0.12, 0.45, -drop))
        ex.append(box((knot + end) / 2, (0.07, (end - knot).length, 0.015), red,
                      rot=(math.atan2(drop, 0.45), 0, -s * math.radians(14))))
    ex.append(prim("cone", (l.head_max.x - 0.01, l.head_c.y, band_z), (0, math.radians(90), 0), color=srgb(190, 195, 205),
                   vertices=4, radius1=0.07, radius2=0, depth=0.015))
    back = Vector((0, l.back_y + 0.04, l.torso_min.z + 0.45))
    d = Vector((-0.55, 0, 0.85)).normalized()
    ex.append(rod(back - d * 0.35, back + d * 0.35, 0.02, srgb(215, 220, 230), verts=4))
    ex.append(prim("cyl", back + d * 0.37, tilt(d), color=srgb(255, 200, 40), vertices=10, radius=0.055, depth=0.02))
    ex.append(rod(back + d * 0.38, back + d * 0.56, 0.025, srgb(30, 20, 20), verts=6))
    for _ in range(10):
        a = random.uniform(0, math.tau); r = random.uniform(0.3, 0.5)
        ex.append(prim("ico", (math.cos(a) * r, math.sin(a) * r * 0.8 - 0.05, random.uniform(0.0, 0.18)),
                       color=random.choice([srgb(90, 30, 140), srgb(60, 20, 100), srgb(130, 50, 180)]),
                       subdivisions=1, radius=random.uniform(0.06, 0.11)))
    return cols, ex

def gold(parts, hs):
    l = landmarks(parts); ex = []
    g1, g2 = srgb(215, 140, 20), srgb(255, 225, 110)
    shine = lambda p: mix(g1, g2, (math.sin(p.x * 9 + p.z * 7) + 1) / 2)
    cols = {"fur_orange": shine, "fur_cream": lambda p: mix(srgb(255, 215, 90), srgb(255, 240, 170), (p.z % 0.2) / 0.2),
            "fur_dark": lambda p: srgb(210, 250, 255)}
    crown = Vector((0.08, l.head_c.y, l.skull_top + 0.02))
    tilt_c = (0, math.radians(18), 0)
    ex.append(prim("cyl", crown, tilt_c, color=srgb(255, 200, 30), vertices=8, radius=0.1, depth=0.05))
    for k in range(5):
        a = k * math.tau / 5
        base = crown + Vector((math.cos(a) * 0.09, math.sin(a) * 0.09, 0.02))
        ex.append(spike(base, (0.3, 0, 1), 0.08, 0.03, srgb(255, 200, 30), tip=srgb(255, 245, 170)))
    for _ in range(12):
        a = random.uniform(0, math.tau); r = random.uniform(0.35, 0.55)
        ex.append(prim("cyl", (math.cos(a) * r, math.sin(a) * r * 0.8, random.uniform(0.0, 0.06)),
                       (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0), color=srgb(255, 195, 40),
                       vertices=10, radius=0.065, depth=0.018))
    for loc in ((0.3, -0.35, 1.2), (-0.35, -0.3, 0.8), (0.4, -0.3, 0.45), (-0.2, -0.4, 1.35)):
        ex += sparkle(loc, 0.09, srgb(255, 255, 230))
    return cols, ex

def giant(parts, hs):
    l = landmarks(parts); ex = []
    cols = {"fur_orange": lambda p: srgb(150, 60, 20), "fur_cream": lambda p: srgb(215, 185, 140),
            "fur_dark": lambda p: srgb(255, 140, 0)}
    scar = srgb(235, 190, 170)
    ex.append(box((-0.12, l.eye_y + 0.03, l.eye_z + 0.02), (0.02, 0.02, 0.2), scar, rot=(0, math.radians(25), 0)))
    ex.append(box((0.15, l.torso_min.y + 0.03, l.chest.z), (0.02, 0.02, 0.22), scar, rot=(0, math.radians(-30), 0)))
    ex.append(box((0.21, l.torso_min.y + 0.04, l.chest.z - 0.02), (0.02, 0.02, 0.18), scar, rot=(0, math.radians(-30), 0)))
    for _ in range(9):
        a = random.uniform(math.radians(200), math.radians(340)); r = random.uniform(0.42, 0.62)
        w, h = random.uniform(0.06, 0.11), random.uniform(0.1, 0.28)
        x, y = math.cos(a) * r, math.sin(a) * r * 0.9
        ex.append(box((x, y, h / 2), (w, w, h), random.choice([srgb(140, 145, 160), srgb(110, 115, 130), srgb(170, 170, 180)])))
        ex.append(box((x, y, h + 0.01), (w * 1.05, w * 1.05, 0.02), srgb(70, 60, 60)))
    for _ in range(6):
        a = random.uniform(0, math.tau); r = random.uniform(0.45, 0.65)
        x, y = math.cos(a) * r, math.sin(a) * r * 0.9
        ex.append(rod((x, y, 0), (x, y, 0.05), 0.012, srgb(90, 60, 30), verts=4))
        ex.append(spike((x, y, 0.04), (0, 0, 1), 0.12, 0.045, srgb(40, 140, 50), verts=5))
    for _ in range(8):
        a = random.uniform(0, math.tau); r = random.uniform(0.15, 0.5)
        ex.append(box((math.cos(a) * r, math.sin(a) * r, -0.01), (random.uniform(0.12, 0.22), random.uniform(0.12, 0.2), 0.03),
                      srgb(80, 60, 45), rot=(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(0, 3))))
    for _ in range(6):
        a = random.uniform(0, math.tau); r = random.uniform(0.35, 0.6)
        ex.append(ball((math.cos(a) * r, math.sin(a) * r * 0.8, 0.05), random.uniform(0.06, 0.1), srgb(200, 180, 150)))
    return cols, ex

def cheems(parts, hs):
    l = landmarks(parts); ex = []
    cols = {"fur_orange": lambda p: srgb(240, 200, 120), "fur_cream": lambda p: srgb(255, 250, 235),
            "fur_dark": lambda p: srgb(50, 40, 60)}
    gold, white = srgb(255, 195, 40), srgb(255, 255, 255)
    ex.append(box((0, (l.torso_min.y + l.back_y) / 2 + 0.05, -0.06), (0.9, 0.75, 0.12), gold))
    ex.append(box((0, l.back_y + 0.1, 0.45), (0.8, 0.1, 1.0), gold))
    ex.append(ball((0, l.back_y + 0.1, 0.98), 0.1, srgb(255, 60, 80)))
    for s in (-1, 1):
        ex.append(box((s * 0.45, l.torso_min.y + 0.25, 0.18), (0.1, 0.5, 0.08), gold))
        ex.append(ball((s * 0.45, l.back_y + 0.1, 0.95), 0.07, gold))
    for _ in range(10):
        a = random.uniform(0, math.tau); r = random.uniform(0.2, 0.6)
        ex.append(ball((math.cos(a) * r, math.sin(a) * r * 0.8, -0.16), random.uniform(0.1, 0.16), white,
                       scale=(1.3, 1, 0.8)))
    sun = Vector((0, l.back_y + 0.2, l.head_c.z + 0.1))
    ex.append(ring(sun, 0.4, 0.03, srgb(255, 230, 120), rot=(math.radians(90), 0, 0), segments=32))
    for k in range(10):
        a = k * math.tau / 10 + 0.3
        d = Vector((math.cos(a), 0, math.sin(a)))
        ex.append(spike(sun + d * 0.42, d, 0.18 if k % 2 else 0.26, 0.035, srgb(255, 220, 90), tip=srgb(255, 255, 220)))
    for s in (-1, 1):
        for k, (length, rise) in enumerate([(0.75, 0.9), (0.65, 0.35), (0.55, -0.15)]):
            d = Vector((s, 0.35, rise)).normalized()
            base = Vector((s * 0.35, l.back_y + 0.12, 0.75 - k * 0.1))
            ex.append(ball(base + d * length / 2, 1, None, scale=(0.09, 0.03, length / 2), rot=tilt(d),
                           fn=lambda p, n, i: white if p.z > 0.6 else srgb(230, 238, 255)))
    ex.append(ring((0, l.head_c.y, l.skull_top - 0.02), 0.2, 0.02, gold, scale=(1, 1.1, 1), segments=18))
    for k in range(10):
        a = k * math.tau / 10
        ex.append(ball((math.cos(a) * 0.2, l.head_c.y + math.sin(a) * 0.22, l.skull_top + 0.01), 0.045, gold,
                       scale=(1, 0.5, 0.5), rot=(0, 0, a + math.radians(90))))
    for k in range(4):
        a = k * math.tau / 4 + 0.4
        cen = Vector((math.cos(a) * 0.62, math.sin(a) * 0.5, 0.55 + 0.25 * math.sin(a * 2)))
        d = Vector((math.cos(a + 1.2), 0.3, 1))
        ex.append(rod(cen - d.normalized() * 0.12, cen + d.normalized() * 0.12, 0.022, gold, verts=6))
    return cols, ex

DESIGNS = [("ShadesShiba", shades), ("BuffShiba", buff), ("ChefShiba", chef), ("PoliceShiba", police),
           ("NinjaShiba", ninja), ("GoldShiba", gold), ("GiantShiba", giant), ("CheemsGod", cheems)]

EXPORT = dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH'}, colors_type='SRGB',
              apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False)
one = bpy.data.materials.new("Tier")

def join(objs, name):
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(one)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name; j.data.name = name
    return j

def export(objs_by_name, filename):
    """Temporarily gives the objects their Roblox names (Body, Stick) and exports only them."""
    old = {}
    for want_name, o in objs_by_name.items():
        old[o] = o.name; o.name = want_name
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs_by_name.values(): o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, filename), **EXPORT)
    for o, n in old.items(): o.name = n

built = []
for asset, design in DESIGNS:
    parts = {}
    for o in dog:
        cp = o.copy(); cp.data = o.data.copy(); coll.objects.link(cp)
        parts[o.name] = cp
    hs = stick.copy(); hs.data = stick.data.copy(); coll.objects.link(hs); hs.name = f"{asset}_Stick"
    bpy.context.view_layer.update()
    cols, extras = design(parts, hs)
    bpy.context.view_layer.update()
    for cp in parts.values():
        paint(cp, lambda p, n, i: cols.get(n, lambda q: srgb(200, 200, 200))(p))
    body = join(list(parts.values()) + extras, f"{asset}_Body")
    paint(hs, lambda p, n, i: WOOD)
    hs.data.materials.clear(); hs.data.materials.append(one)
    export({"Body": body, "Stick": hs}, f"{asset}.fbx")
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    print(f"BUILT {asset}: Body {tris} triangles")
    built.append([body, hs])

# --- Projectiles: long axis along Z, centred at the origin, like Stick.fbx ---
def loose_stick(name):
    s = src.copy(); s.data = src.data.copy(); coll.objects.link(s); s.name = name; s.hide_render = False
    s.matrix_world = Matrix.Rotation(math.radians(-90), 4, 'X') @ src.matrix_world
    bpy.context.view_layer.update()
    mn, mx = wb(s); s.location -= (mn + mx) / 2
    bpy.context.view_layer.update()
    return s

def newspaper():
    paper, ink, red = srgb(238, 235, 222), srgb(90, 90, 95), srgb(220, 25, 30)
    ex = [prim("cyl", (0, 0, 0), color=paper, vertices=12, radius=0.14, depth=0.9)]
    for z in (-0.3, -0.22, -0.14, 0.3, 0.38):
        ex.append(prim("cyl", (0, 0, z), color=ink, vertices=12, radius=0.142, depth=0.015))
    ex.append(prim("cyl", (0, 0, 0.06), color=paper, vertices=12, radius=0.143, depth=0.3))
    # Reads bottom to top along the roll.
    ex += pixel_text("BONK", (-0.065, -0.15, -0.2), (0, 0, 1), (1, 0, 0), 0.026, (0, -1, 0), red)
    for k in range(3):
        ex.append(box((0.08 + k * 0.03, 0.05 * (k - 1), 0.5), (0.2, 0.01, 0.16), paper,
                      rot=(math.radians(20 * (k - 1)), math.radians(35 + k * 12), 0)))
    return ex

def baguette():
    crust = lambda p, n, i: mix(srgb(150, 85, 30), srgb(225, 165, 80), max(0.0, min(1.0, (p.x + 0.12) / 0.24)))
    ex = [ball((0, 0, 0), 1, None, scale=(0.11, 0.11, 0.62), fn=crust)]
    for k in range(5):
        ex.append(ball((0.09, 0, -0.4 + k * 0.2), 1, srgb(245, 215, 150), scale=(0.02, 0.05, 0.08),
                       rot=(0, 0, 0)))
    top = Vector((0.05, 0, 0.55))
    ex.append(rod(top, top + Vector((0.12, 0, 0.12)), 0.006, srgb(150, 120, 80), verts=4))
    for k, colr in enumerate((srgb(0, 60, 180), srgb(255, 255, 255), srgb(220, 30, 40))):
        ex.append(box(top + Vector((0.14 + k * 0.035, 0, 0.1)), (0.035, 0.005, 0.06), colr))
    return ex

def rolling_pin():
    wood = srgb(205, 150, 90)
    ex = [prim("cyl", (0, 0, 0), color=wood, vertices=12, radius=0.14, depth=0.6)]
    for s in (-1, 1):
        ex.append(prim("cyl", (0, 0, s * 0.4), color=srgb(170, 110, 60), vertices=8, radius=0.05, depth=0.2))
        ex.append(ball((0, 0, s * 0.51), 0.065, srgb(150, 95, 50)))
    for _ in range(4):
        ex.append(ball((random.choice([-1, 1]) * 0.1, random.uniform(-0.1, 0.1), random.uniform(-0.2, 0.2)), 0.06,
                       srgb(250, 238, 205)))
    for _ in range(10):
        a = random.uniform(0, math.tau)
        ex.append(prim("ico", (math.cos(a) * random.uniform(0.18, 0.3), math.sin(a) * 0.2, random.uniform(-0.3, 0.3)),
                       color=srgb(255, 255, 255), subdivisions=1, radius=random.uniform(0.02, 0.04)))
    return ex

def baseball_bat():
    ex = [prim("cone", (0, 0, 0), color=srgb(190, 130, 70), vertices=10, radius1=0.055, radius2=0.13, depth=0.9)]
    ex.append(ball((0, 0, -0.46), 0.07, srgb(150, 95, 50), scale=(1, 1, 0.5)))
    for k in range(4):
        ex.append(prim("cyl", (0, 0, -0.35 + k * 0.05), color=srgb(40, 40, 45) if k % 2 else srgb(235, 235, 235),
                       vertices=10, radius=0.068, depth=0.04))
    for k in range(6):
        a = k * math.tau / 6
        ex.append(spike((math.cos(a) * 0.06, math.sin(a) * 0.06, -0.3), (math.cos(a), math.sin(a), 0.3), 0.05, 0.015,
                        srgb(170, 170, 175)))
    for colr, z, a in ((srgb(60, 200, 90), 0.05, 0.3), (srgb(255, 80, 180), 0.2, 2.4), (srgb(60, 140, 255), 0.12, 4.2)):
        r = 0.055 + (0.13 - 0.055) * (z + 0.45) / 0.9
        ex.append(box((math.cos(a) * r, math.sin(a) * r, z), (0.06, 0.06, 0.06), colr, rot=(0, 0, a)))
    ex.append(ball((0, 0, 0.46), 0.13, srgb(255, 40, 30), scale=(1, 1, 0.4)))
    return ex

def giant_bone():
    ivory, shade = srgb(245, 238, 215), srgb(215, 202, 170)
    ex = [prim("cyl", (0, 0, 0), color=ivory, vertices=10, radius=0.09, depth=0.7)]
    for x in (-0.1, 0.1):
        for z in (-0.37, 0.37):
            ex.append(ball((x, 0, z), 0.13, None, fn=lambda p, n, i: shade if abs(p.z) > 0.44 else ivory))
    for z in (-0.1, 0.0, 0.12):
        ex.append(ball((0.07, -0.05, z), 0.03, srgb(160, 145, 115), scale=(1, 0.6, 1.3)))
    for loc in ((0.22, -0.05, 0.2), (-0.22, 0.05, -0.1), (0.15, 0.05, -0.4)):
        ex += sparkle(loc, 0.08, srgb(255, 210, 60))
    return ex

def squeaky_hammer():
    ex = [prim("cyl", (0, 0, -0.12), color=srgb(255, 215, 30), vertices=10, radius=0.05, depth=0.7)]
    head = Vector((0, 0, 0.32))
    ex.append(prim("cyl", head, (0, math.radians(90), 0), color=srgb(230, 35, 35), vertices=14, radius=0.17, depth=0.5))
    for s in (-1, 1):
        ex.append(prim("cyl", head + Vector((s * 0.26, 0, 0)), (0, math.radians(90), 0), color=srgb(255, 215, 30),
                       vertices=14, radius=0.18, depth=0.04))
    for loc in ((0.3, -0.1, 0.55), (-0.32, -0.1, 0.5), (0.0, -0.15, 0.58)):
        ex += sparkle(loc, 0.09, srgb(255, 245, 120))
    return ex

def bonk_sign():
    yellow, black = srgb(255, 210, 0), srgb(15, 15, 15)
    sign = Vector((0, 0, 0.25))
    ex = [box(sign + Vector((0, 0.012, 0)), (0.52, 0.02, 0.52), black, rot=(0, math.radians(45), 0)),
          box(sign, (0.47, 0.03, 0.47), yellow, rot=(0, math.radians(45), 0))]
    ex += pixel_text("BONK", sign + Vector((-0.29, -0.02, 0.055)), (1, 0, 0), (0, 0, -1), 0.034, (0, -1, 0), black)
    ex.append(rod((0, 0.03, -0.1), (0, 0.03, 0.02), 0.025, srgb(150, 155, 165), verts=6))
    ex.append(rod((0, 0.03, -0.1), (0.1, 0.03, -0.5), 0.025, srgb(150, 155, 165), verts=6))
    for s in (-1, 1):
        ex.append(ball(sign + Vector((s * 0.07, 0, 0.4)), 0.045, srgb(255, 120, 0)))
    ex.append(box(sign + Vector((0, 0, 0.36)), (0.2, 0.03, 0.03), srgb(60, 60, 65)))
    return ex

def neon_stick():
    grad = lambda p, n, i: mix(srgb(40, 170, 255), srgb(255, 60, 220), max(0.0, min(1.0, (p.z + 0.45) / 0.9)))
    ex = [prim("cyl", (0, 0, 0), color=None, fn=grad, vertices=8, radius=0.07, depth=0.9)]
    ex.append(prim("cyl", (0, 0, 0), color=srgb(255, 255, 255), vertices=8, radius=0.03, depth=0.94))
    for z in (-0.3, 0.0, 0.3):
        ex.append(ring((0, 0, z), 0.1, 0.012, srgb(255, 255, 255), segments=12))
    ex += zigzag((0.12, 0, -0.4), (0, 0, 1), (1, 0, 0), 6, 0.13, 0.05, 0.012, srgb(120, 240, 255))
    ex += zigzag((-0.12, 0, 0.4), (0, 0, -1), (-1, 0, 0), 5, 0.14, 0.05, 0.012, srgb(255, 150, 250))
    return ex

def legendary_stick():
    s = loose_stick("Legendary_core")
    gold_shades = [srgb(255, 205, 70), srgb(235, 160, 25), srgb(255, 235, 150)]
    paint(s, lambda p, n, i: gold_shades[i % 3])
    ex = [s]
    ex.append(prim("cyl", (0, 0, 0), color=srgb(255, 255, 240), vertices=6, radius=0.025, depth=0.5))
    for k in range(3):
        a = k * math.tau / 3
        side = Vector((math.cos(a), math.sin(a), 0))
        ex += zigzag(side * 0.2 + Vector((0, 0, -0.35)), (0, 0, 1), side, 5, 0.14, 0.05, 0.014, srgb(255, 240, 80))
    for k in range(5):
        a = k * math.tau / 5
        ex.append(box((math.cos(a) * 0.28, math.sin(a) * 0.28, 0.25 * math.sin(a * 2)), (0.07, 0.015, 0.07),
                      srgb(90, 230, 255), rot=(0, 0, a)))
    for _ in range(8):
        ex.append(prim("ico", (random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), random.uniform(-0.45, 0.45)),
                       color=srgb(255, random.randint(200, 255), 90), subdivisions=1, radius=0.02))
    return ex

PROJECTILES = [("Newspaper", newspaper), ("Baguette", baguette), ("RollingPin", rolling_pin),
               ("BaseballBat", baseball_bat), ("GiantBone", giant_bone), ("SqueakyHammer", squeaky_hammer),
               ("BonkSign", bonk_sign), ("NeonStick", neon_stick), ("LegendaryStick", legendary_stick)]

thrown = []
for name, design in PROJECTILES:
    o = join(design(), f"{name}_obj")
    mn, mx = wb(o)
    o.location -= (mn + mx) / 2
    bpy.context.view_layer.update()
    export({name: o}, f"{name}.fbx")
    print(f"BUILT {name}: {sum(len(p.vertices) - 2 for p in o.data.polygons)} triangles")
    thrown.append(o)

# --- Preview: the Shibas in a row, the projectiles in a row in front ---
for o in dog + [stick]: o.hide_render = True
for k, objs in enumerate(built):
    for o in objs: o.location.x += (k - (len(built) - 1) / 2) * 1.45
for k, o in enumerate(thrown):
    o.location += Vector(((k - (len(thrown) - 1) / 2) * 1.2, -2.2, 0.45))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 2000, 900
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.2, 0.22, 0.26)
cam = bpy.data.objects['Camera']
cam.location = Vector((0, -15.5, 3.2)); target = Vector((0, -0.8, 0.6))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "preview_tiers.png")
bpy.ops.render.render(write_still=True)
print("DONE", sorted(os.listdir(OUT)))
