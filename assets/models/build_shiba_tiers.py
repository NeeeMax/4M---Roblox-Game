import bpy, math, sys, os, random
from mathutils import Vector, Matrix, Euler
# Shiba tiers 1-10 and projectile tiers 1-10 (Stick included), built from
# shiba_bonk_default.blend like build_shiba.py: same posed dog, same stick in the right paw, same export settings.
# Each Shiba gets its own fur colours plus accessories made of low-poly primitives; everything is baked into vertex
# colours (Roblox ignores FBX material colours). Output: one <AssetName>.fbx per model, preview_tiers.png and
# preview_projectiles.png (the latter re-imported from the exported files).
# Usage:
#   blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba_tiers.py -- <output folder>
# Add `--only PirateShiba,CowboyShiba` to build just those Shibas (no projectiles) and render preview_only.png.
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
ONLY = set(ARGS[ARGS.index("--only") + 1].split(",")) if "--only" in ARGS else set()
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
WOOD = (0.12, 0.055, 0.022)  # wood_brown in shiba_bonk_default.blend (linear)
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
    # Dark faces on the head: two closed-eye lines (off-centre, high), the round nose (centre), the mouth (low).
    dark = [head.matrix_world @ poly.center for poly in head.data.polygons
            if head.data.materials[poly.material_index].name == 'fur_dark']
    head_top_dark = max(p.z for p in dark)
    eyes = [p for p in dark if abs(p.x) > 0.06 and p.z > head_top_dark - 0.05]
    nose = [p for p in dark if abs(p.x) <= 0.045 and p.z > 0.87]
    mouth = [p for p in dark if p not in eyes and p not in nose]
    l.eye_z = sum(p.z for p in eyes) / len(eyes)
    l.eye_x = sum(abs(p.x) for p in eyes) / len(eyes)
    l.eye_y = min(p.y for p in eyes)
    l.nose = sum(nose, Vector()) / len(nose)
    l.mouth = sum(mouth, Vector()) / len(mouth) if mouth else l.nose - Vector((0, -0.05, 0.09))
    l.neck_z = l.head_min.z + 0.04
    l.head_verts = hv
    l.head = head
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

def transform_about(o, pivot, m):
    o.matrix_world = Matrix.Translation(pivot) @ m @ Matrix.Translation(-Vector(pivot)) @ o.matrix_world

# --- Shiba designs. Each gets fresh copies of the dog parts (dict by name) and the paw stick, may reshape them,
# and returns (colours per fur material, extra meshes). ---
# The original Shiba colours (material base colours in shiba_bonk_default.blend, linear).
ORANGE, CREAM, DARK = (0.745, 0.254, 0.045), (0.922, 0.823, 0.672), (0.01, 0.01, 0.012)

def plain(parts, hs):
    """The standard orange Shiba (tier 1)."""
    return default_cols(), []

def default_cols():
    return {"fur_orange": lambda p: ORANGE, "fur_cream": lambda p: CREAM, "fur_dark": lambda p: DARK}

def surface_y(obj, x, z):
    """Front surface of obj at (x, z), found by casting a ray from the front (-Y) toward +Y."""
    mwi = obj.matrix_world.inverted()
    origin = mwi @ Vector((x, -5.0, z))
    direction = (mwi.to_3x3() @ Vector((0, 1, 0))).normalized()
    hit, loc, _, _ = obj.ray_cast(origin, direction)
    return (obj.matrix_world @ loc).y if hit else None

def face_y(l, x, z, r=0.045):
    """Front-most y of the head surface at (x, z): where something worn on the face must sit."""
    y = surface_y(l.head, x, z)
    if y is not None:
        return y
    near = [v.y for v in l.head_verts if abs(v.x - x) < r and abs(v.z - z) < r]
    return min(near) if near else l.eye_y

def front_y(obj, z, half_width=0.1, r=0.05, x=0.0):
    y = surface_y(obj, x, z)
    if y is not None:
        return y
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    near = [v.y for v in vs if abs(v.x - x) < half_width and abs(v.z - z) < r]
    return min(near) if near else min(v.y for v in vs)

def head_section(l, z):
    """Centre y and half-extents (x, y) of the head's cross-section at height z: to fit bands around it."""
    vs = [v for v in l.head_verts if abs(v.z - z) < 0.035]
    ys = [v.y for v in vs]
    return (min(ys) + max(ys)) / 2, max(abs(v.x) for v in vs), (max(ys) - min(ys)) / 2

def shell(src_obj, keep, offset, fn):
    """A thin layer copied from src_obj's faces where keep(world_centre, world_normal) is true, pushed out by
    `offset`: clothing that follows the body exactly (apron, mask)."""
    import bmesh
    o = src_obj.copy(); o.data = src_obj.data.copy(); coll.objects.link(o)
    mw = o.matrix_world; rot = mw.to_3x3()
    bm = bmesh.new(); bm.from_mesh(o.data)
    drop = [f for f in bm.faces if not keep(mw @ f.calc_center_median(), (rot @ f.normal).normalized())]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bm.normal_update()
    s = mw.to_scale(); local = offset / ((s.x + s.y + s.z) / 3)
    for v in bm.verts:
        v.co += v.normal * local
    bm.to_mesh(o.data); bm.free()
    paint(o, fn)
    return o

def chain(points, color, link=0.028):
    """Chain of alternating links along a polyline."""
    out, k = [], 0
    for a, b in zip(points, points[1:]):
        a, b = Vector(a), Vector(b)
        seg = b - a
        n = max(1, int(seg.length / (link * 1.25)))
        t = seg.normalized()
        side = t.cross(Vector((0, 1, 0)))
        if side.length < 1e-3: side = Vector((1, 0, 0))
        side.normalize()
        for i in range(n):
            c = a + seg * ((i + 0.5) / n)
            axis = t.cross(side) if k % 2 else side
            other = axis.cross(t).normalized()
            m = Matrix((t, other, axis.normalized())).transposed()
            out.append(prim("torus", c, m.to_euler(), scale=(1.5, 1, 1), color=color, major_radius=link * 0.45,
                            minor_radius=link * 0.14, major_segments=8, minor_segments=4))
            k += 1
    return out

def shades(parts, hs):
    l = landmarks(parts); ex = []
    black, white, gold = srgb(14, 14, 18), srgb(255, 255, 255), srgb(255, 196, 45)
    # "Deal with it" pixel shades: a flat pixel plate resting on the snout in front of the eyes (2 = white glint).
    rows = ["1111111111111111",
            "0111111001111110",
            "0121111001211110",
            "0011110000111100"]
    px = 0.032
    plate_y = min(face_y(l, l.eye_x, l.eye_z), face_y(l, -l.eye_x, l.eye_z)) - 0.05
    top = l.eye_z + 0.07
    for r, line in enumerate(rows):
        for k, bit in enumerate(line):
            if bit != "0":
                x = (k - (len(line) - 1) / 2) * px
                ex.append(box((x, plate_y, top - r * px), (px, 0.03, px), white if bit == "2" else black))
    edge = len(rows[0]) / 2 * px
    for s in (-1, 1):
        ex.append(box((s * edge, (plate_y + l.head_c.y + 0.05) / 2, top), (0.022, abs(l.head_c.y + 0.05 - plate_y), 0.024),
                      black))
    # Gold chain draped from the neck down to a big dollar-sign pendant.
    chest_z = l.neck_z - 0.12
    pts = []
    for i in range(13):
        t = -1 + i / 6
        pts.append((0.21 * t, front_y(parts["Torso"], chest_z + 0.1 * t * t, x=0.21 * t) - 0.015,
                    chest_z + 0.1 * t * t))
    ex += chain(pts, gold)
    pend_y = front_y(parts["Torso"], chest_z - 0.12) - 0.03
    ex += pixel_text("$", Vector((-0.0525, pend_y, chest_z - 0.02)), (1, 0, 0), (0, 0, -1), 0.035, (0, -1, 0), gold)
    # Cigar-shaped dog treat in the mouth corner.
    start = l.mouth + Vector((0.05, -0.03, 0.0))
    tip = start + Vector((0.1, -0.09, -0.03))
    ex.append(rod(start, tip, 0.022, srgb(125, 72, 35), verts=6))
    ex.append(prim("ico", tip, color=srgb(255, 100, 25), subdivisions=1, radius=0.026))
    return default_cols(), ex

def buff(parts, hs):
    l0 = landmarks(parts)
    tz = l0.torso_max.z - l0.torso_min.z
    torso_scale = (1.3, 1.15, 1.08)
    transform_about(parts['Torso'], (0, (l0.torso_min.y + l0.torso_max.y) / 2, l0.torso_min.z),
                    Matrix.Diagonal((*torso_scale, 1)))
    dz = tz * (torso_scale[2] - 1)
    transform_about(parts['Head'], (0, l0.head_c.y, l0.head_min.z),
                    Matrix.Translation((0, 0, dz)) @ Matrix.Diagonal((0.85, 0.85, 0.85, 1)))
    half = (l0.torso_max.x - l0.torso_min.x) / 2
    for side, thick in (("Right", 1.9), ("Left", 1.45)):
        names = [f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"]
        up_min, up_max = wb(parts[names[0]])
        shoulder = Vector(((up_min.x + up_max.x) / 2, (up_min.y + up_max.y) / 2, up_max.z))
        s = 1 if side == "Right" else -1
        hmin, hmax = wb(parts[f"{side}Hand"]); hand_before = (hmin + hmax) / 2
        # Thicker, not longer: scale across the arm only, then move it out by the torso's extra width.
        m = Matrix.Translation((s * half * (torso_scale[0] - 1) * 0.9, 0, dz)) @ Matrix.Diagonal((thick, thick, 1.05, 1))
        for n in names: transform_about(parts[n], shoulder, m)
        bpy.context.view_layer.update()
        if side == "Right":
            hmin, hmax = wb(parts["RightHand"])
            hs.location += (hmin + hmax) / 2 - hand_before
    for n in ("LeftLeg", "RightLeg"):
        lmin, lmax = wb(parts[n])
        transform_about(parts[n], ((lmin.x + lmax.x) / 2, (lmin.y + lmax.y) / 2, lmin.z), Matrix.Diagonal((1.2, 1.1, 1.0, 1)))
    bpy.context.view_layer.update()
    l = landmarks(parts); ex = []
    band_z = l.eye_z + 0.07
    hw = (l.head_max.x - l.head_min.x) / 2
    cy, rx, ry = head_section(l, band_z)
    ex.append(ring((0, cy, band_z), rx + 0.012, 0.03, srgb(225, 35, 45), scale=(1, (ry + 0.012) / (rx + 0.012), 1),
                   segments=20))
    for s in (-1, 1):
        ex.append(box((s * (l.eye_x - 0.005), face_y(l, s * l.eye_x, l.eye_z + 0.04) - 0.01, l.eye_z + 0.045),
                      (0.075, 0.02, 0.018), DARK, rot=(0, s * math.radians(-18), 0)))
    torso = parts['Torso']
    muscle, abs_col = srgb(236, 214, 178), srgb(228, 202, 160)
    pec_z = l.torso_min.z + (l.torso_max.z - l.torso_min.z) * 0.72
    for s in (-1, 1):
        ex.append(ball((s * 0.12, front_y(torso, pec_z, x=s * 0.12) + 0.006, pec_z), 1, muscle, scale=(0.15, 0.03, 0.08),
                       rot=(0, s * math.radians(-10), 0)))
    for row in range(3):
        z = pec_z - 0.17 - row * 0.075
        for s in (-1, 1):
            ex.append(box((s * 0.047, front_y(torso, z, x=s * 0.047) - 0.004, z), (0.075, 0.02, 0.058), abs_col))
    return default_cols(), ex

def chef(parts, hs):
    l = landmarks(parts); ex = []
    white, stain = srgb(255, 255, 255), srgb(222, 218, 210)
    base = l.skull_top - 0.03
    ex.append(prim("cyl", (0, l.head_c.y, base + 0.2), color=white, vertices=12, radius=0.19, depth=0.4))
    for k in range(7):
        a = k * math.tau / 7
        ex.append(ball((math.cos(a) * 0.14, l.head_c.y + math.sin(a) * 0.14, base + 0.44), 0.13, white))
    ex.append(ball((0, l.head_c.y, base + 0.5), 0.15, white))
    brown = srgb(60, 32, 18)
    stache = l.nose + Vector((0, 0.02, -0.055))
    for s in (-1, 1):
        ex.append(ball(stache + Vector((s * 0.06, 0, 0)), 1, brown, scale=(0.065, 0.028, 0.026),
                       rot=(0, s * math.radians(-12), 0)))
        ex.append(ball(stache + Vector((s * 0.125, 0.015, 0.03)), 0.028, brown))
    red = srgb(215, 30, 35)
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.035, red, rot=(math.radians(-18), 0, 0), segments=16))
    ex.append(prim("cone", Vector((0, front_y(parts['Torso'], l.neck_z - 0.1) - 0.02, l.neck_z - 0.1)),
                   (math.radians(-90), 0, 0), color=red, vertices=3, radius1=0.12, radius2=0, depth=0.03))
    # Apron: a layer copied from the belly, so it follows the body instead of floating in front of it.
    lo = l.torso_min.z + 0.06; hi = l.neck_z - 0.2
    stains = set(random.sample(range(4000), 300))
    ex.append(shell(parts['Torso'], lambda c, nrm: nrm.y < -0.3 and lo < c.z < hi and abs(c.x) < 0.24, 0.012,
                    lambda p, n, i: stain if i in stains else white))
    return default_cols(), ex

def police(parts, hs):
    l = landmarks(parts); ex = []
    navy, black, gold = srgb(28, 48, 115), srgb(15, 15, 20), srgb(255, 200, 45)
    # Cap: a band around the top of the skull, a flat crown on it, the visor over the eyes.
    band_z = l.skull_top - 0.03
    ex.append(prim("cyl", (0, l.head_c.y + 0.01, band_z), (math.radians(-6), 0, 0), color=navy, vertices=16,
                   radius=0.2, depth=0.08))
    ex.append(ball((0, l.head_c.y - 0.01, band_z + 0.06), 1, navy, scale=(0.24, 0.26, 0.07),
                   rot=(math.radians(-6), 0, 0)))
    ex.append(ball((0, l.head_c.y - 0.19, band_z - 0.035), 1, black, scale=(0.15, 0.09, 0.018),
                   rot=(math.radians(-14), 0, 0)))
    ex.append(prim("cone", (0, l.head_c.y - 0.205, band_z + 0.01), (math.radians(90), 0, 0), color=gold,
                   vertices=5, radius1=0.04, radius2=0, depth=0.015))
    top = band_z + 0.12
    ex.append(box((0, l.head_c.y, top), (0.14, 0.06, 0.025), srgb(230, 230, 235)))
    ex.append(ball((-0.035, l.head_c.y, top + 0.03), 0.035, srgb(255, 35, 35)))
    ex.append(ball((0.035, l.head_c.y, top + 0.03), 0.035, srgb(40, 100, 255)))
    # Mirrored aviators resting on the face.
    mirror = lambda p, n, i: mix(srgb(90, 140, 200), srgb(230, 242, 255), max(0.0, min(1.0, (p.z - l.eye_z + 0.05) / 0.09)))
    lens_y = {}
    for s in (-1, 1):
        x = s * (l.eye_x + 0.01)
        y = face_y(l, x, l.eye_z) - 0.03
        lens_y[s] = y
        ex.append(ball((x, y, l.eye_z - 0.01), 1, None, scale=(0.08, 0.016, 0.062), rot=(0, 0, s * math.radians(22)),
                       fn=mirror))
    bridge_y = face_y(l, 0, l.eye_z + 0.03) - 0.015
    ex.append(rod((-l.eye_x + 0.06, lens_y[-1], l.eye_z + 0.035), (0, bridge_y, l.eye_z + 0.04), 0.009, gold, verts=4))
    ex.append(rod((0, bridge_y, l.eye_z + 0.04), (l.eye_x - 0.06, lens_y[1], l.eye_z + 0.035), 0.009, gold, verts=4))
    badge_z = l.neck_z - 0.13
    ex.append(prim("cone", (0.12, front_y(parts['Torso'], badge_z, 0.2) - 0.015, badge_z), (math.radians(90), 0, 0),
                   color=gold, vertices=5, radius1=0.065, radius2=0.03, depth=0.022))
    donut = l.left_hand + Vector((-0.04, -0.1, 0.1))
    frosting = lambda p, n, i: srgb(255, 120, 190) if p.y < donut.y - 0.005 else srgb(215, 150, 80)
    ex.append(prim("torus", donut, (math.radians(80), 0, 0), fn=frosting, major_radius=0.08, minor_radius=0.04,
                   major_segments=14, minor_segments=6))
    return default_cols(), ex

def ninja(parts, hs):
    l = landmarks(parts); ex = []
    mask = srgb(28, 28, 36)
    lo, hi = l.eye_z - 0.055, l.eye_z + 0.06
    # Hood and face mask on the head only; the eye slit keeps the Shiba's own fur and eyes. Decided per face (by its
    # centre), so the mask edge is crisp instead of blending across faces.
    head = parts['Head']
    in_slit = {poly.index for poly in head.data.polygons if lo < (head.matrix_world @ poly.center).z < hi}
    fur = {"fur_orange": ORANGE, "fur_cream": CREAM, "fur_dark": DARK}
    cols = default_cols()
    cols["Head:*"] = lambda p, n, i: fur.get(n, ORANGE) if i in in_slit else mask
    red = srgb(210, 25, 35)
    band_z = hi + 0.01
    hw = (l.head_max.x - l.head_min.x) / 2
    cy, rx, ry = head_section(l, band_z)
    ex.append(ring((0, cy, band_z), rx + 0.012, 0.032, red, scale=(1, (ry + 0.012) / (rx + 0.012), 1), segments=20))
    knot = Vector((0, l.head_max.y - 0.03, band_z))
    for s, drop in ((-1, 0.1), (1, 0.18)):
        end = knot + Vector((s * 0.12, 0.45, -drop))
        ex.append(box((knot + end) / 2, (0.07, (end - knot).length, 0.015), red,
                      rot=(math.atan2(drop, 0.45), 0, -s * math.radians(14))))
    ex.append(prim("cone", (hw + 0.005, l.head_c.y + 0.03, band_z), (0, math.radians(90), 0), color=srgb(190, 195, 205),
                   vertices=4, radius1=0.07, radius2=0, depth=0.015))
    ex.append(ring((0, l.head_c.y + 0.07, l.neck_z), 0.24, 0.04, mask, rot=(math.radians(-18), 0, 0), segments=16))
    back = Vector((0, l.back_y + 0.04, l.torso_min.z + 0.45))
    d = Vector((-0.55, 0, 0.85)).normalized()
    ex.append(rod(back - d * 0.35, back + d * 0.35, 0.02, srgb(215, 220, 230), verts=4))
    ex.append(prim("cyl", back + d * 0.37, tilt(d), color=srgb(255, 200, 40), vertices=10, radius=0.055, depth=0.02))
    ex.append(rod(back + d * 0.38, back + d * 0.56, 0.025, srgb(30, 20, 20), verts=6))
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
    return cols, ex

# Galaxy fur gradient (linear RGB) from the feet to the ear tips, as in the old OBJ-based Galaxy Shiba.
GALAXY_STOPS = [(0.00, (0.020, 0.010, 0.090)),  # deep indigo
                (0.35, (0.160, 0.030, 0.420)),  # violet
                (0.65, (0.650, 0.080, 0.450)),  # pink
                (1.00, (0.120, 0.600, 0.900))]  # cyan

def galaxy_gradient(t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(GALAXY_STOPS, GALAXY_STOPS[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0))
    return GALAXY_STOPS[-1][1]

def surface_samples(objs, count, rng, keep, spacing):
    """Area-weighted random points on the faces of objs: (object, world point, world normal), at least `spacing`
    apart, on faces where keep(object, world_centre, world_normal, material) is true."""
    faces = []
    for o in objs:
        mw = o.matrix_world; nm = mw.to_3x3().inverted().transposed()
        for poly in o.data.polygons:
            c = mw @ poly.center; nrm = (nm @ poly.normal).normalized()
            mat = o.data.materials[poly.material_index].name if len(o.data.materials) else ""
            if keep(o, c, nrm, mat):
                vs = [mw @ o.data.vertices[v].co for v in poly.vertices]
                area = sum(((vs[k] - vs[0]).cross(vs[k + 1] - vs[0])).length / 2 for k in range(1, len(vs) - 1))
                faces.append((o, vs, nrm, area))
    weights = [f[3] for f in faces]
    out, tries = [], 0
    while len(out) < count and tries < count * 40:
        tries += 1
        o, vs, nrm, _ = rng.choices(faces, weights)[0]
        k = rng.randrange(1, len(vs) - 1)  # random point in one triangle of the face fan
        a, b = rng.random(), rng.random()
        if a + b > 1: a, b = 1 - a, 1 - b
        p = vs[0] + (vs[k] - vs[0]) * a + (vs[k + 1] - vs[0]) * b
        if all((p - q).length >= spacing for _, q, _ in out):
            out.append((o, p, nrm))
    return out

def star_specks(samples, rng, name):
    """One mesh of tiny four-pointed star specks lying on the fur: each rim point is ray-cast back onto the surface
    it was sampled from (so nothing floats), the centre is raised a little so the star catches the light."""
    white, cyan, pink = srgb(255, 255, 255), srgb(150, 245, 255), srgb(255, 170, 235)
    verts, tris, cols = [], [], []
    for o, p, n in samples:
        size = rng.uniform(0.022, 0.04)
        colr = rng.choices([white, cyan, pink], [5, 3, 2])[0]
        t1 = n.orthogonal().normalized(); t1.rotate(Matrix.Rotation(rng.uniform(0, math.pi), 3, n)); t2 = n.cross(t1)
        mwi = o.matrix_world.inverted(); mw = o.matrix_world
        rim = []
        for k in range(8):
            a = k * math.tau / 8
            r = size if k % 2 == 0 else size * 0.32
            q = p + (t1 * math.cos(a) + t2 * math.sin(a)) * r
            hit, loc, _, _ = o.ray_cast(mwi @ (q + n * 0.05), (mwi.to_3x3() @ -n).normalized(), distance=0.2)
            if not hit or abs((mw @ loc - q).dot(n)) > size * 0.5:
                break  # the surface falls away here (ear tip, edge): this star would stick out, skip it
            rim.append(mw @ loc - n * 0.003)
        if len(rim) < 8:
            continue
        base = len(verts)
        verts += [p + n * size * 0.28] + rim
        for k in range(8):
            tris.append((base, base + 1 + k, base + 1 + (k + 1) % 8))
            cols.append(colr)
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], tris)
    me.update()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            attr.data[li].color = (*cols[poly.index], 1.0)
    me.color_attributes.active_color = attr
    return ob

ARM_NAMES = ("RightUpperArm", "RightLowerArm", "RightHand")
# GalaxyShiba's Orbit: radius of the planet's path, its centre's height above the eyes, and its axis (the game spins Orbit
# about it).
ORBIT_RADIUS, ORBIT_LIFT, ORBIT_AXIS = 0.54, 0.15, (-0.28, 0.2, 1.0)

def galaxy(parts, hs):
    """Galaxy fur, glowing cyan eyes, star specks on the fur, and a planet with its moon flying
    around the head on a tilted path. Planet and moon are the separate part `Orbit`, which the game spins around the
    `OrbitCenter` marker (the path's centre) about the path's axis."""
    l = landmarks(parts); ex = []
    rng = random.Random(8)  # own generator: keeps the random layouts of the other designs unchanged
    span = l.max_z - l.min_z
    fur = lambda p: galaxy_gradient((p.z - l.min_z) / span)
    light = lambda p: tuple(min(1.0, c * 1.6 + 0.08) for c in fur(p))
    ink = (0.004, 0.003, 0.009)
    cols = {"fur_orange": fur, "fur_cream": light, "fur_dark": lambda p: ink}
    # Glowing eyes: a bright cyan almond with a white glint over each closed-eye line (nose and mouth stay dark ink).
    eye, glint = srgb(90, 235, 255), srgb(255, 255, 255)
    for s in (-1, 1):
        x, z = s * l.eye_x, l.eye_z - 0.005
        y = face_y(l, x, z)
        ex.append(ball((x, y + 0.004, z), 1, eye, scale=(0.06, 0.022, 0.036), rot=(0, 0, s * math.radians(24))))
        gx = x - s * 0.018
        ex.append(ball((gx, face_y(l, gx, z + 0.012) - 0.014, z + 0.012), 0.014, glint))
    # Star specks all over the fur (not on the face, nose or soles); the arm's specks swing with the arm.
    head = parts['Head']
    face = lambda c: c.y < l.eye_y + 0.08 and l.mouth.z - 0.06 < c.z < l.eye_z + 0.07 and abs(c.x) < 0.24
    keep = lambda o, c, nrm, mat: mat != "fur_dark" and nrm.z > -0.5 and not (o is head and face(c))
    arm = [parts[n] for n in ARM_NAMES]
    samples = surface_samples(list(parts.values()), 230, rng, keep, 0.06)
    ex.append(star_specks([s for s in samples if s[0] not in arm], rng, "GalaxyStars"))
    arm_stars = star_specks([s for s in samples if s[0] in arm], rng, "GalaxyArmStars")
    # --- Orbit: a tilted circular path around the head (up on the stick side), carrying a banded planet ("Jupiter")
    # wearing its own little ring, and a moon. The path's centre is the OrbitCenter marker. ---
    centre = Vector((0, (l.head_min.y + l.head_max.y) / 2, l.eye_z + ORBIT_LIFT))
    axis = Vector(ORBIT_AXIS).normalized()
    ring_rot = tilt(axis)
    e1 = ring_rot.to_matrix() @ Vector((1, 0, 0)); e2 = axis.cross(e1)
    on_ring = lambda a: centre + (e1 * math.cos(a) + e2 * math.sin(a)) * ORBIT_RADIUS
    # No visible ring: only the planet and the moon sit on the (invisible) orbit path, so the game's spin makes them
    # fly around the head.
    orbit = []
    planet = on_ring(math.radians(200))
    p_axis = (axis + e1 * 0.5).normalized()
    bands = [srgb(255, 90, 170), srgb(255, 205, 232), srgb(185, 70, 215), srgb(255, 150, 90), srgb(255, 90, 170)]
    band = lambda p, n, i: bands[min(4, max(0, int(((p - planet).dot(p_axis) / 0.11 + 1) * 2.5)))]
    orbit.append(prim("uv", planet, tilt(p_axis), fn=band, segments=12, ring_count=8, radius=0.11))
    orbit.append(prim("torus", planet, tilt(p_axis), color=srgb(190, 250, 255), major_radius=0.15, minor_radius=0.015,
                      major_segments=18, minor_segments=4, scale=(1, 1, 0.5)))
    orbit.append(prim("ico", on_ring(math.radians(20)), color=srgb(170, 245, 255), subdivisions=1, radius=0.05))
    # Clearance: spun, planet and moon sweep the whole circle, so check the full path against the dog.
    near = {}
    for o in list(parts.values()) + [hs]:
        mwi = o.matrix_world.inverted()
        near[o.name] = min((o.matrix_world @ o.closest_point_on_mesh(mwi @ on_ring(k * math.tau / 120))[1]
                            - on_ring(k * math.tau / 120)).length for k in range(120))
    close = sorted(near.items(), key=lambda kv: kv[1])[:3]
    print(f"GALAXY orbit centre {tuple(round(v, 3) for v in centre)} axis {tuple(round(v, 3) for v in axis)} "
          f"radius {ORBIT_RADIUS}; nearest to the orbit path: {[(n, round(d, 3)) for n, d in close]} "
          f"(planet with its ring reaches 0.165)")
    marker = box(centre, (0.02, 0.02, 0.02), srgb(255, 0, 255))
    return cols, ex, {"ThrowArm": [arm_stars], "Orbit": orbit, "OrbitCenter": [marker]}

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

# --- Shibas 11-20 (the second set, Config/EconomyConfig -> Shibas): same dog, own fur colours and accessories. ---
def recolor(orange, cream, dark=DARK):
    return {"fur_orange": lambda p: orange, "fur_cream": lambda p: cream, "fur_dark": lambda p: dark}

def pirate(parts, hs):
    l = landmarks(parts); ex = []
    black, bone, red, gold = srgb(25, 22, 28), srgb(245, 240, 225), srgb(200, 30, 40), srgb(255, 200, 45)
    top = l.skull_top - 0.03
    # Tricorn: a domed crown on a three-cornered brim whose edges curl up (three tilted plates), gold trim, a skull
    # and crossbones on the front.
    ex.append(ball((0, l.head_c.y, top + 0.06), 1, black, scale=(0.2, 0.21, 0.13)))
    for k in range(3):
        a = math.radians(-90) + k * math.tau / 3
        out = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-out.y, out.x, 0))
        centre = Vector((0, l.head_c.y, top + 0.05)) + out * 0.2
        plate = box(centre, (0.46, 0.035, 0.11), black, rot=(0, 0, math.atan2(side.y, side.x)))
        # Tilt the plate outward around its long edge so the brim curls up and away from the head.
        transform_about(plate, centre, Matrix.Rotation(math.radians(-45), 4, side))
        ex.append(plate)
        ex.append(rod(centre + side * 0.23 + Vector((0, 0, 0.055)), centre - side * 0.23 + Vector((0, 0, 0.055)),
                      0.008, gold, verts=4))
    front = Vector((0, l.head_c.y - 0.2, top + 0.07))
    ex.append(ball(front + Vector((0, -0.03, 0.02)), 0.035, bone))
    for s in (-1, 1):
        ex.append(rod(front + Vector((s * 0.045, -0.03, -0.035)), front + Vector((-s * 0.045, -0.03, 0.035)), 0.009,
                      bone, verts=4))
    # Eye patch over the left eye with a strap around the head.
    x = -l.eye_x
    ex.append(ball((x, face_y(l, x, l.eye_z) - 0.01, l.eye_z), 1, black, scale=(0.065, 0.02, 0.055)))
    cy, rx, ry = head_section(l, l.eye_z + 0.04)
    ex.append(ring((0, cy, l.eye_z + 0.04), rx + 0.01, 0.012, black, scale=(1, (ry + 0.01) / (rx + 0.01), 1),
                   rot=(0, math.radians(-12), 0), segments=20))
    # Gold hoop earring on the right side, red neckerchief.
    ex.append(ring((l.head_max.x - 0.02, l.head_c.y, l.eye_z - 0.02), 0.045, 0.011, gold, rot=(0, math.radians(90), 0)))
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.035, red, rot=(math.radians(-18), 0, 0), segments=16))
    # Parrot on the left shoulder: green body, red head, yellow beak, blue tail.
    sh = Vector((-0.24, l.head_c.y + 0.02, l.shoulder_z + 0.14))
    ex.append(ball(sh, 1, srgb(40, 190, 70), scale=(0.07, 0.07, 0.1)))
    ex.append(ball(sh + Vector((0, -0.02, 0.12)), 0.06, srgb(225, 40, 40)))
    ex.append(spike(sh + Vector((0, -0.07, 0.11)), (0, -1, -0.4), 0.06, 0.025, srgb(255, 200, 40)))
    ex.append(spike(sh + Vector((0, 0.05, -0.05)), (0, 0.6, -1), 0.14, 0.04, srgb(40, 110, 230), verts=4))
    return recolor(srgb(150, 85, 40), srgb(235, 215, 185)), ex

def cowboy(parts, hs):
    l = landmarks(parts); ex = []
    hat, band, red, star = srgb(150, 95, 50), srgb(70, 40, 25), srgb(205, 40, 45), srgb(255, 205, 60)
    top = l.skull_top - 0.03
    # Wide oval brim, a tall crown with a dark band and a dent on top.
    ex.append(ball((0, l.head_c.y, top + 0.02), 1, hat, scale=(0.44, 0.38, 0.03)))
    ex.append(prim("cyl", (0, l.head_c.y, top + 0.13), color=hat, vertices=10, radius=0.17, depth=0.22,
                   scale=(1, 1.15, 1)))
    ex.append(prim("cyl", (0, l.head_c.y, top + 0.05), color=band, vertices=10, radius=0.175, depth=0.05,
                   scale=(1, 1.15, 1)))
    ex.append(box((0, l.head_c.y, top + 0.24), (0.05, 0.3, 0.03), band))
    # Red bandana: a band around the neck and a triangle over the chest.
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.035, red, rot=(math.radians(-18), 0, 0), segments=16))
    ex.append(prim("cone", Vector((0, front_y(parts['Torso'], l.neck_z - 0.1) - 0.02, l.neck_z - 0.12)),
                   (math.radians(-90), 0, 0), color=red, vertices=3, radius1=0.16, radius2=0, depth=0.03))
    # Sheriff star, and a lasso coiled in the free paw.
    badge_z = l.neck_z - 0.22
    ex.append(prim("cone", (0.13, front_y(parts['Torso'], badge_z, 0.2) - 0.015, badge_z), (math.radians(90), 0, 0),
                   color=star, vertices=5, radius1=0.07, radius2=0.03, depth=0.022))
    for k in range(3):
        ex.append(ring(l.left_hand + Vector((-0.02, -0.05, 0.02 * k)), 0.1 - 0.012 * k, 0.012, srgb(215, 180, 110),
                       rot=(math.radians(75), 0, 0), segments=16))
    return recolor(srgb(200, 120, 55), srgb(240, 222, 190)), ex

def viking(parts, hs):
    l = landmarks(parts); ex = []
    steel, horn, wood, iron = srgb(165, 170, 180), srgb(240, 230, 200), srgb(135, 85, 45), srgb(90, 90, 100)
    beard = srgb(190, 90, 30)
    top = l.skull_top - 0.06
    # Round helmet with a nose guard and two curved horns.
    ex.append(ball((0, l.head_c.y, top + 0.02), 1, steel, scale=(0.22, 0.24, 0.16)))
    ex.append(ring((0, l.head_c.y, top - 0.04), 0.22, 0.025, iron, scale=(1, 1.08, 1), segments=18))
    ex.append(box((0, face_y(l, 0, l.eye_z + 0.05) - 0.02, l.eye_z + 0.05), (0.04, 0.02, 0.13), iron))
    for s in (-1, 1):
        base = Vector((s * 0.2, l.head_c.y, top + 0.04))
        mid = base + Vector((s * 0.14, -0.02, 0.1))
        ex.append(rod(base, mid, 0.045, horn, verts=6))
        ex.append(spike(mid, (s * 0.3, 0, 1), 0.16, 0.042, horn, verts=6))
    # Braided beard hanging from the chin.
    for k in range(4):
        ex.append(ball(l.mouth + Vector((0, 0.01, -0.06 - k * 0.06)), 0.055 - k * 0.008, beard))
    for s in (-1, 1):
        ex.append(ball(l.mouth + Vector((s * 0.08, 0.03, -0.04)), 0.05, beard))
    # Round wooden shield with an iron rim and boss on the free arm.
    c = l.left_hand + Vector((-0.12, -0.02, 0.18))
    ex.append(prim("cyl", c, (0, math.radians(90), 0), color=wood, vertices=14, radius=0.24, depth=0.04))
    ex.append(ring(c, 0.235, 0.02, iron, rot=(0, math.radians(90), 0), segments=20))
    ex.append(ball(c + Vector((-0.03, 0, 0)), 0.06, iron))
    return recolor(srgb(215, 125, 45), srgb(240, 225, 195)), ex

def wizard(parts, hs):
    l = landmarks(parts); ex = []
    robe, star, beard, orb = srgb(55, 60, 175), srgb(255, 220, 70), srgb(245, 245, 250), srgb(120, 230, 255)
    top = l.skull_top - 0.04
    # Tall pointed hat, bent back a little, with a wide brim, a golden band and stars in front.
    ex.append(ball((0, l.head_c.y, top), 1, robe, scale=(0.36, 0.34, 0.03)))
    ex.append(spike((0, l.head_c.y, top), (0.25, 0.15, 1), 0.62, 0.2, robe, verts=10, tip=srgb(90, 80, 210)))
    ex.append(prim("cyl", (0, l.head_c.y, top + 0.04), color=star, vertices=10, radius=0.19, depth=0.04))
    for k, a in enumerate((-110, -70, -90)):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        ex.append(prim("cone", Vector((0, l.head_c.y, top + 0.13 + 0.07 * k)) + d * (0.17 - 0.03 * k),
                       tilt(d), color=star, vertices=5, radius1=0.04, radius2=0.015, depth=0.015))
    # Long white beard pointing down from the chin, bushy eyebrows.
    ex.append(spike(l.mouth + Vector((0, 0.02, 0.0)), (0, -0.25, -1), 0.4, 0.13, beard, verts=8))
    for s in (-1, 1):
        ex.append(ball(l.nose + Vector((s * 0.06, 0.02, -0.05)), 1, beard, scale=(0.06, 0.03, 0.025)))
    # Robe collar and a glowing crystal orb in the free paw.
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.25, 0.04, robe, rot=(math.radians(-18), 0, 0), segments=16))
    ex.append(prim("ico", l.left_hand + Vector((-0.03, -0.08, 0.12)), color=orb, subdivisions=1, radius=0.1))
    return recolor(srgb(225, 150, 70), srgb(245, 235, 215)), ex

def astronaut(parts, hs):
    l = landmarks(parts); ex = []
    suit, trim, glass, pack = srgb(240, 242, 248), srgb(255, 130, 30), srgb(70, 150, 235), srgb(200, 205, 215)
    # White space suit on the body; the head keeps its Shiba fur and looks out through the helmet window.
    fur = {"fur_orange": ORANGE, "fur_cream": CREAM, "fur_dark": DARK}
    cols = {"fur_orange": lambda p: suit, "fur_cream": lambda p: srgb(225, 228, 236), "fur_dark": lambda p: DARK,
            "Head:*": lambda p, n, i: fur.get(n, ORANGE)}
    # Helmet: a round frame standing around the face with a blue glass edge, a thick neck ring, and the back of the
    # helmet behind the head.
    frame_c = Vector((0, l.head_c.y - 0.02, l.eye_z - 0.03))
    ex.append(ring(frame_c, 0.3, 0.045, suit, rot=(math.radians(90), 0, 0), segments=24))
    ex.append(ring(frame_c + Vector((0, 0.012, 0)), 0.265, 0.014, glass, rot=(math.radians(90), 0, 0), segments=24))
    ex.append(ring((0, l.head_c.y + 0.04, l.neck_z - 0.01), 0.26, 0.055, suit, rot=(math.radians(-15), 0, 0),
                   segments=18))
    ex.append(ball((0, l.head_c.y + 0.1, l.eye_z + 0.02), 1, suit, scale=(0.29, 0.2, 0.31)))
    ex.append(rod((0.12, l.head_c.y + 0.12, l.eye_z + 0.3), (0.16, l.head_c.y + 0.14, l.eye_z + 0.46), 0.01, trim,
                  verts=4))
    ex.append(ball((0.16, l.head_c.y + 0.14, l.eye_z + 0.47), 0.03, srgb(255, 60, 60)))
    # Backpack with two lights, a chest control box with buttons, an orange patch.
    ex.append(box((0, l.back_y + 0.1, l.shoulder_z - 0.12), (0.34, 0.14, 0.36), pack))
    for s, col in ((-1, srgb(60, 255, 120)), (1, srgb(255, 70, 70))):
        ex.append(ball((s * 0.08, l.back_y + 0.18, l.shoulder_z), 0.03, col))
    cz = l.neck_z - 0.22
    ex.append(box((0, front_y(parts['Torso'], cz) - 0.03, cz), (0.18, 0.05, 0.12), pack))
    for k, col in enumerate((srgb(255, 60, 60), srgb(60, 200, 255), srgb(255, 220, 60))):
        ex.append(ball(((k - 1) * 0.05, front_y(parts['Torso'], cz) - 0.06, cz + 0.02), 0.018, col))
    ex.append(box((0.15, front_y(parts['Torso'], cz + 0.1, x=0.15) - 0.01, cz + 0.1), (0.08, 0.02, 0.05), trim))
    return cols, ex

def robot(parts, hs):
    l = landmarks(parts); ex = []
    dark, glow, bolt, red = srgb(60, 65, 75), srgb(70, 240, 255), srgb(200, 205, 215), srgb(255, 60, 60)
    metal = lambda p: mix(srgb(140, 150, 165), srgb(200, 208, 220), (math.sin(p.z * 25) + 1) / 2)
    cols = {"fur_orange": metal, "fur_cream": lambda p: srgb(215, 220, 228), "fur_dark": lambda p: dark}
    # Glowing visor over the eyes, antenna with a red bulb, bolts on the sides of the head.
    ex.append(box((0, face_y(l, 0, l.eye_z) - 0.025, l.eye_z), (0.34, 0.025, 0.06), glow))
    ex.append(rod((0, l.head_c.y, l.skull_top - 0.02), (0, l.head_c.y, l.skull_top + 0.2), 0.012, dark, verts=6))
    ex.append(ball((0, l.head_c.y, l.skull_top + 0.22), 0.04, red))
    for s in (-1, 1):
        ex.append(prim("cyl", (s * (l.head_max.x - 0.01), l.head_c.y, l.eye_z), (0, math.radians(90), 0),
                       color=bolt, vertices=6, radius=0.05, depth=0.05))
    # Chest panel with buttons and a glowing grille, neck bolts.
    cz = l.neck_z - 0.2
    ty = front_y(parts['Torso'], cz)
    ex.append(box((0, ty - 0.01, cz), (0.26, 0.03, 0.2), dark))
    for k, col in enumerate((red, srgb(255, 220, 60), srgb(60, 255, 120))):
        ex.append(ball(((k - 1) * 0.07, ty - 0.03, cz + 0.05), 0.022, col))
    for k in range(3):
        ex.append(box((0, ty - 0.03, cz - 0.03 - k * 0.03), (0.18, 0.01, 0.012), glow))
    for s in (-1, 1):
        ex.append(prim("cyl", (s * 0.15, l.head_c.y + 0.05, l.neck_z), (0, math.radians(90), 0), color=bolt,
                       vertices=6, radius=0.035, depth=0.08))
    return cols, ex

def samurai(parts, hs):
    l = landmarks(parts); ex = []
    lacquer, gold, cord, plate = srgb(160, 25, 30), srgb(255, 200, 45), srgb(30, 30, 40), srgb(120, 20, 25)
    top = l.skull_top - 0.05
    # Kabuto: dome, flared neck guard in layers, golden V crest.
    ex.append(ball((0, l.head_c.y, top + 0.02), 1, lacquer, scale=(0.22, 0.24, 0.14)))
    for k in range(3):
        ex.append(prim("cone", (0, l.head_c.y + 0.03, top - 0.03 - k * 0.04), color=plate if k % 2 else lacquer,
                       vertices=12, radius1=0.3 + k * 0.03, radius2=0.22 + k * 0.03, depth=0.04))
    for s in (-1, 1):
        ex.append(spike((0, l.head_c.y - 0.2, top + 0.02), (s * 0.55, -0.2, 1), 0.3, 0.035, gold, verts=4))
    ex.append(ball((0, l.head_c.y - 0.21, top + 0.02), 0.04, gold))
    # Shoulder plates in stacked strips, a cord belt, a topknot.
    for s in (-1, 1):
        for k in range(3):
            ex.append(box((s * 0.3, l.head_c.y + 0.08, l.shoulder_z + 0.05 - k * 0.06), (0.16, 0.2, 0.05),
                          lacquer if k % 2 == 0 else plate, rot=(0, s * math.radians(25), 0)))
    ex.append(ring((0, (l.torso_min.y + l.torso_max.y) / 2, l.torso_min.z + 0.2), 0.3, 0.03, cord,
                   scale=(1, 0.85, 1), segments=18))
    ex.append(ball((0, l.head_c.y + 0.12, l.skull_top + 0.12), 0.05, srgb(20, 20, 25)))
    return recolor(srgb(225, 110, 35), srgb(245, 230, 205)), ex

def vampire(parts, hs):
    l = landmarks(parts); ex = []
    cape, lining, fang, gem = srgb(20, 18, 28), srgb(170, 15, 35), srgb(255, 255, 255), srgb(230, 20, 40)
    # Pale fur, red eyes over the closed-eye lines, two fangs.
    cols = recolor(srgb(175, 170, 190), srgb(230, 228, 238), srgb(25, 20, 30))
    for s in (-1, 1):
        x = s * l.eye_x
        ex.append(ball((x, face_y(l, x, l.eye_z) + 0.004, l.eye_z), 1, srgb(255, 40, 50), scale=(0.05, 0.02, 0.03),
                       rot=(0, 0, s * math.radians(24))))
        ex.append(spike(l.mouth + Vector((s * 0.035, -0.02, 0.0)), (0, -0.2, -1), 0.06, 0.018, fang, verts=4))
    # Tall stand-up collar behind the head (red inside), a cape down the back, a gem clasp.
    for s in (-1, 1):
        ex.append(box((s * 0.18, l.head_c.y + 0.12, l.neck_z + 0.12), (0.2, 0.03, 0.3), cape,
                      rot=(math.radians(-15), 0, s * math.radians(-30))))
        ex.append(box((s * 0.18, l.head_c.y + 0.1, l.neck_z + 0.12), (0.19, 0.01, 0.28), lining,
                      rot=(math.radians(-15), 0, s * math.radians(-30))))
    top_z, bottom_z = l.neck_z, l.min_z + 0.08
    ex.append(prim("cone", (0, l.back_y + 0.06, (top_z + bottom_z) / 2), color=cape, vertices=8, radius1=0.42,
                   radius2=0.22, depth=top_z - bottom_z, scale=(1, 0.3, 1)))
    ex.append(ball((0, front_y(parts['Torso'], l.neck_z - 0.06) - 0.03, l.neck_z - 0.06), 0.045, gem))
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.025, cape, rot=(math.radians(-18), 0, 0), segments=16))
    return cols, ex

def pharaoh(parts, hs):
    l = landmarks(parts); ex = []
    gold, blue, ink = srgb(255, 195, 40), srgb(35, 70, 190), srgb(20, 20, 30)
    top = l.skull_top - 0.05
    # Nemes headdress from solid stripes (vertex colours blend across a face, so each stripe is its own piece):
    # stacked slices over the skull, and striped lappets falling beside the face to the shoulders.
    for k in range(5):
        z = top + 0.1 - k * 0.045
        r = 0.2 + k * 0.022
        ex.append(prim("cyl", (0, l.head_c.y + 0.03, z), color=gold if k % 2 == 0 else blue, vertices=14, radius=r,
                       depth=0.046, scale=(1, 1.08, 1)))
    ex.append(ball((0, l.head_c.y + 0.03, top + 0.13), 1, gold, scale=(0.2, 0.216, 0.06)))
    for s in (-1, 1):
        for k in range(6):
            z = top - 0.2 - k * 0.055
            ex.append(box((s * (0.25 + k * 0.006), l.head_c.y - 0.02, z), (0.07, 0.15, 0.056),
                          gold if k % 2 == 0 else blue))
    # Cobra on the front of the headdress.
    ex.append(rod((0, l.head_c.y - 0.22, top - 0.02), (0, l.head_c.y - 0.24, top + 0.1), 0.025, gold, verts=6))
    ex.append(ball((0, l.head_c.y - 0.25, top + 0.12), 1, gold, scale=(0.045, 0.025, 0.035)))
    # Kohl lines, a false beard, a wide collar of gold and blue rings, an ankh in the free paw.
    for s in (-1, 1):
        x = s * (l.eye_x + 0.03)
        ex.append(box((x, face_y(l, x, l.eye_z - 0.01) - 0.008, l.eye_z - 0.01), (0.07, 0.01, 0.012), ink,
                      rot=(0, s * math.radians(-15), 0)))
    ex.append(prim("cyl", l.mouth + Vector((0, 0.02, -0.1)), color=blue, vertices=6, radius=0.03, depth=0.14))
    ex.append(ring(l.mouth + Vector((0, 0.02, -0.14)), 0.032, 0.01, gold, segments=8))
    for k, col in enumerate((gold, blue, gold)):
        ex.append(ring((0, l.head_c.y + 0.05, l.neck_z - 0.03 - k * 0.035), 0.24 + k * 0.035, 0.022, col,
                       rot=(math.radians(-18), 0, 0), segments=18))
    a = l.left_hand + Vector((-0.02, -0.06, 0.05))
    ex.append(rod(a, a + Vector((0, 0, 0.26)), 0.018, gold, verts=6))
    ex.append(rod(a + Vector((-0.08, 0, 0.18)), a + Vector((0.08, 0, 0.18)), 0.018, gold, verts=6))
    ex.append(ring(a + Vector((0, 0, 0.3)), 0.05, 0.018, gold, rot=(math.radians(90), 0, 0), scale=(1, 1.3, 1),
                   segments=12))
    return recolor(srgb(210, 150, 70), srgb(245, 230, 200)), ex

def dragon(parts, hs):
    l = landmarks(parts); ex = []
    scale_a, scale_b, belly = srgb(40, 150, 70), srgb(70, 200, 90), srgb(245, 215, 120)
    horn, bone, skin = srgb(250, 235, 200), srgb(25, 95, 50), srgb(55, 165, 85)
    fur = lambda p: scale_a if (int(p.x * 30) + int(p.z * 30)) % 2 else scale_b
    cols = {"fur_orange": fur, "fur_cream": lambda p: belly, "fur_dark": lambda p: srgb(255, 200, 30)}
    # Two swept-back horns and spikes along the spine.
    for s in (-1, 1):
        ex.append(spike((s * 0.12, l.head_c.y + 0.04, l.skull_top - 0.04), (s * 0.3, 0.8, 0.6), 0.25, 0.045, horn,
                        verts=6))
    for k in range(6):
        z = l.skull_top - 0.08 - k * 0.12
        y = l.back_y + 0.02 if k else l.head_max.y
        ex.append(spike((0, y - 0.02, z), (0, 1, 0.4), 0.12 - k * 0.008, 0.04, srgb(250, 180, 40), verts=4))
    # Wings on the back: an arm bone going up and out, three thin membrane panels hanging down from it.
    for s in (-1, 1):
        root = Vector((s * 0.12, l.back_y + 0.06, l.shoulder_z - 0.02))
        tip = root + Vector((s * 0.5, 0.18, 0.38))
        ex.append(rod(root, tip, 0.028, bone, verts=6))
        ex.append(ball(tip, 0.035, horn))
        heading = math.atan2(tip.y - root.y, tip.x - root.x)
        for k in range(3):
            top_pt = root + (tip - root) * (0.35 + 0.3 * k)
            length = 0.34 + 0.08 * k
            centre = top_pt + Vector((0, 0, -length / 2))
            ex.append(box(centre, (0.2, 0.012, length), skin, rot=(0, 0, heading)))
            ex.append(rod(top_pt, top_pt + Vector((0, 0, -length)), 0.012, bone, verts=4))
    return cols, ex

NEW_DESIGNS = [("PirateShiba", pirate), ("CowboyShiba", cowboy), ("VikingShiba", viking), ("WizardShiba", wizard),
               ("AstronautShiba", astronaut), ("RobotShiba", robot), ("SamuraiShiba", samurai),
               ("VampireShiba", vampire), ("PharaohShiba", pharaoh), ("DragonShiba", dragon)]

DESIGNS = [("Shiba", plain), ("ShadesShiba", shades), ("BuffShiba", buff), ("ChefShiba", chef), ("PoliceShiba", police),
           ("NinjaShiba", ninja), ("GoldShiba", gold), ("GalaxyShiba", galaxy), ("GiantShiba", giant), ("CheemsGod", cheems)]

EXPORT = dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH'}, colors_type='SRGB',
              apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False)
one = bpy.data.materials.new("Tier")

def join(objs, name):
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(one)
    j = objs[0]
    if len(objs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = j
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
for asset, design in DESIGNS + NEW_DESIGNS:
    if ONLY and asset not in ONLY:
        continue
    parts = {}
    for o in dog:
        cp = o.copy(); cp.data = o.data.copy(); coll.objects.link(cp)
        parts[o.name] = cp
    hs = stick.copy(); hs.data = stick.data.copy(); coll.objects.link(hs); hs.name = f"{asset}_Stick"
    bpy.context.view_layer.update()
    # A design may return a third value, {mesh name: [objects]}: extra objects for "Body" or "ThrowArm", or extra
    # named parts exported as their own meshes (GalaxyShiba's "Orbit" and "OrbitCenter").
    cols, extras, *rest = design(parts, hs)
    named = dict(rest[0]) if rest else {}
    bpy.context.view_layer.update()
    for base_name, cp in parts.items():
        whole = cols.get(f"{base_name}:*")  # full paint override for this part: fn(position, material, face)
        paint(cp, whole or (lambda p, n, i: (cols.get(n) or (lambda q: srgb(200, 200, 200)))(p)))
    # The throwing arm is its own part with a Shoulder marker at the joint, so the game can swing it.
    up_min, up_max = wb(parts["RightUpperArm"])
    shoulder = Vector(((up_min.x + up_max.x) / 2, (up_min.y + up_max.y) / 2, up_max.z - 0.04))
    arm = join([parts[n] for n in ARM_NAMES] + named.pop("ThrowArm", []), f"{asset}_Arm")
    body = join([p for n, p in parts.items() if n not in ARM_NAMES] + extras + named.pop("Body", []), f"{asset}_Body")
    marker = box(shoulder, (0.02, 0.02, 0.02), srgb(255, 0, 255))
    marker.data.materials.append(one)
    paint(hs, lambda p, n, i: WOOD)
    hs.data.materials.clear(); hs.data.materials.append(one)
    meshes = {"Body": body, "ThrowArm": arm, "Shoulder": marker, "Stick": hs}
    for part_name, objs in named.items():
        meshes[part_name] = join(objs, f"{asset}_{part_name}")
    export(meshes, f"{asset}.fbx")
    tris = ", ".join(f"{n} {sum(len(p.vertices) - 2 for p in o.data.polygons)}" for n, o in meshes.items())
    print(f"BUILT {asset}: triangles {tris}")
    built.append(list(meshes.values()))


# --- Projectiles 1-10 (Config/Projectiles). Contract with the game: the long axis is Blender Z (Roblox model Y), the
# bounding box is centred at the origin, the end held in the paw is at -Z, and a tiny `Grip` marker mesh sits on the
# axis exactly where the paw holds it (the game hides it and puts it into the Shiba's paw). Each one is a chunky,
# faceted shape in 2-3 bold flat colours that still reads at ~3 studs while spinning; no loose sparkles or zigzags
# (effects come from the game). Designed 1.0 long (the game scales them), the wide side along X (it faces front in
# the paw).
def solid(name, verts, faces, colors):
    """One mesh from raw faces, one flat colour per face."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            attr.data[li].color = (*colors[poly.index], 1.0)
    me.color_attributes.active_color = attr
    return o

def lathe(name, rings, sides, col, axis=None, up=(1, 0, 0), phase=0.5):
    """Faceted tube through rings [(centre, radius)]: a centre is a point or just z, a radius a number or (rx, ry)
    (rx along `up`). Each ring is perpendicular to `axis`, or to the path when no axis is given. A radius of 0 closes
    that end in a point, otherwise the ends get flat caps; consecutive rings at the same place make a flat step.
    col(k, j, face_centre) -> colour, k = segment index (-1 bottom cap, len(rings) - 1 top cap), j = side.
    Faces wind outward (Roblox draws one side only)."""
    pts = [Vector((0, 0, c)) if isinstance(c, (int, float)) else Vector(c) for c, _ in rings]
    verts, faces, cols, idx = [], [], [], []
    for k, (p, (_, r)) in enumerate(zip(pts, rings)):
        t = Vector(axis).normalized() if axis else (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        e1 = Vector(up) - t * Vector(up).dot(t); e1.normalize(); e2 = t.cross(e1)
        rx, ry = (r, r) if isinstance(r, (int, float)) else r
        if rx == 0 and ry == 0:
            idx.append([len(verts)]); verts.append(p)
            continue
        row = []
        for j in range(sides):
            a = (j + phase) * math.tau / sides
            row.append(len(verts)); verts.append(p + e1 * (math.cos(a) * rx) + e2 * (math.sin(a) * ry))
        idx.append(row)

    def add(face, k, j):
        faces.append(face)
        cols.append(col(k, j, sum((verts[i] for i in face), Vector()) / len(face)))
    for k in range(len(rings) - 1):
        a, b = idx[k], idx[k + 1]
        for j in range(sides):
            jn = (j + 1) % sides
            if len(a) == 1: add([a[0], b[jn], b[j]], k, j)
            elif len(b) == 1: add([a[j], a[jn], b[0]], k, j)
            else: add([a[j], a[jn], b[jn], b[j]], k, j)
    if len(idx[0]) > 1: add(list(reversed(idx[0])), -1, 0)
    if len(idx[-1]) > 1: add(list(idx[-1]), len(rings) - 1, 0)
    return solid(name, verts, faces, cols)

def by_z(bands, default):
    """Colour by the face centre's z: bands = [(z_from, z_to, colour)]."""
    def col(k, j, c):
        for z0, z1, colr in bands:
            if z0 <= c.z <= z1:
                return colr
        return default
    return col

def block_text(text, centre, right, down, px, depth, color):
    """Blocky letters centred on `centre`, each pixel row merged into long bricks (clean and cheap); `depth` is the
    brick thickness along right x down."""
    right, down = Vector(right).normalized(), Vector(down).normalized()
    normal = right.cross(down)
    width = sum(len(FONT[ch][0]) + 1 for ch in text) - 1
    height = len(FONT[text[0]])
    origin = Vector(centre) - right * width * px / 2 - down * height * px / 2
    m = Matrix((right, down, normal)).transposed().to_euler()
    out, col0 = [], 0
    for ch in text:
        rows = FONT[ch]
        for r, line in enumerate(rows):
            k = 0
            while k < len(line):
                if line[k] == "1":
                    n = 1
                    while k + n < len(line) and line[k + n] == "1": n += 1
                    loc = origin + right * (col0 + k + n / 2) * px + down * (r + 0.5) * px
                    out.append(prim("cube", loc, m, scale=(n * px, px, depth), color=color, size=1))
                    k += n
                else:
                    k += 1
        col0 += len(rows[0]) + 1
    return out

def stick_proj():
    """Tier 1: a chunky wooden branch with a stubby twig and two leaves."""
    bark, cut, leaf, leaf2 = srgb(150, 92, 48), srgb(238, 196, 128), srgb(95, 190, 60), srgb(60, 150, 45)
    ends = lambda k, j, c, n=5: cut if k in (-1, n - 1) else bark
    path = [((0.0, 0, -0.5), 0.08), ((0.03, 0, -0.25), 0.085), ((0.0, 0, 0.0), 0.08), ((-0.03, 0, 0.25), 0.072),
            ((-0.015, 0, 0.5), 0.065)]
    ex = [lathe("stk", path, 6, ends)]
    ex.append(lathe("twig", [((0.0, 0, 0.02), 0.055), ((0.12, 0, 0.2), 0.046), ((0.17, 0, 0.3), 0.04)], 6,
                    lambda k, j, c: cut if k == 2 else bark))
    for base, tip in (((0.17, 0, 0.3), (0.22, 0, 0.5)), ((-0.04, 0, 0.28), (-0.24, 0, 0.4))):
        base, tip = Vector(base), Vector(tip)
        ex.append(lathe("leaf", [(base, 0), (base.lerp(tip, 0.45), (0.085, 0.025)), (tip, 0)], 4,
                        lambda k, j, c: leaf if j in (0, 3) else leaf2, phase=0))
    return ex, -0.4

def newspaper():
    """Tier 2: a rolled-up newspaper: cream paper, grey print bands, a red headline band, hollow ends."""
    paper, ink, red, inside = srgb(242, 238, 222), srgb(105, 108, 118), srgb(225, 40, 40), srgb(170, 165, 150)
    r, hole = 0.15, 0.085
    rings = [(-0.46, hole), (-0.5, hole), (-0.5, r), (0.5, r), (0.5, hole), (0.46, hole)]
    bands = [(-0.37, -0.31, ink), (-0.25, -0.2, ink), (-0.08, 0.12, red), (0.24, 0.29, ink), (0.35, 0.41, ink)]
    # Split the long outer segment at the band edges so each band gets its own faces.
    zs = sorted({z for z0, z1, _ in bands for z in (z0, z1)})
    rings = rings[:3] + [(z, r) for z in zs] + rings[3:]
    col = by_z(bands, paper)
    ex = [lathe("paper", rings, 8, lambda k, j, c: inside if (c.to_2d().length < hole + 0.005) else col(k, j, c),
                axis=(0, 0, 1))]
    # The loose outer page edge along the roll.
    ex.append(box((r * math.cos(math.radians(22.5)) + 0.004, 0.035, 0), (0.016, 0.11, 0.99), paper))
    return ex, -0.36

def baguette():
    """Tier 3: a slightly bent, pointed loaf: golden crust, darker underside, pale score slashes."""
    crust, under, score = srgb(222, 146, 58), srgb(160, 86, 32), srgb(250, 222, 160)
    prof = [(-0.5, 0), (-0.47, 0.05), (-0.42, 0.085), (-0.33, 0.106), (-0.18, 0.117), (0.0, 0.12), (0.18, 0.117),
            (0.33, 0.106), (0.42, 0.085), (0.47, 0.05), (0.5, 0)]
    bow = lambda z: 0.035 * (1 - (2 * z) ** 2)
    rings = [((bow(z), 0, z), (r, r * 0.85)) for z, r in prof]
    col = lambda k, j, c: under if math.cos((j + 0.5 + 0.5) * math.tau / 8) < -0.3 else crust
    ex = [lathe("loaf", rings, 8, col, phase=0.5)]
    for z in (-0.27, -0.09, 0.09, 0.27):
        rz = dict(prof)
        r = min(rz.items(), key=lambda kv: abs(kv[0] - z))[1]
        ex.append(ball((bow(z) + r * 0.9, 0, z), 1, score, scale=(0.03, 0.04, 0.085), rot=(math.radians(40), 0, 0)))
    return ex, -0.34

def rolling_pin():
    """Tier 4: pale wooden barrel with bevelled edges, red handles on dark wooden necks."""
    wood, neck, red = srgb(232, 190, 128), srgb(150, 95, 50), srgb(215, 45, 40)
    half = [(0.5, 0.05), (0.49, 0.068), (0.44, 0.074), (0.37, 0.07), (0.335, 0.05), (0.335, 0.042), (0.3, 0.042),
            (0.3, 0.13), (0.28, 0.15)]
    rings = [(-z, r) for z, r in half] + [(z, r) for z, r in reversed(half)]
    def col(k, j, c):
        a = abs(c.z)
        if k in (-1, len(rings) - 1) or a > 0.334: return red
        if a > 0.299 and c.to_2d().length < 0.06: return neck
        return wood
    return [lathe("pin", rings, 10, col, axis=(0, 0, 1))], -0.41

def baseball_bat():
    """Tier 5: wooden bat, black grip tape, red knob and a red band on the barrel."""
    wood, tape, red, end = srgb(222, 165, 98), srgb(38, 38, 44), srgb(220, 40, 35), srgb(190, 130, 70)
    rings = [(-0.5, 0.05), (-0.49, 0.078), (-0.46, 0.078), (-0.44, 0.046), (-0.2, 0.05), (-0.05, 0.062),
             (0.1, 0.088), (0.2, 0.105), (0.26, 0.114), (0.4, 0.128), (0.46, 0.124), (0.5, 0.09)]
    def col(k, j, c):
        if k == -1 or c.z < -0.44: return red
        if c.z < -0.2: return tape
        if 0.2 < c.z < 0.26: return red
        if k == len(rings) - 1: return end
        return wood
    return [lathe("bat", rings, 10, col, axis=(0, 0, 1))], -0.35

def giant_bone():
    """Tier 6: cartoon bone: cream shaft, two faceted ivory knobs at each end."""
    ivory, cream = srgb(250, 244, 226), srgb(232, 214, 176)
    ex = [lathe("shaft", [(-0.37, 0.1), (0.0, 0.085), (0.37, 0.1)], 8, lambda k, j, c: cream, axis=(0, 0, 1))]
    for z in (-0.365, 0.365):
        for x in (-0.097, 0.097):
            ex.append(prim("ico", (x, 0, z), color=ivory, subdivisions=2, radius=0.135))
    return ex, -0.25

def squeaky_hammer():
    """Tier 7: toy hammer: red head with yellow bumpers and a white stripe on a yellow handle."""
    red, yellow, white = srgb(230, 38, 38), srgb(255, 212, 30), srgb(255, 255, 255)
    ex = [lathe("handle", [(-0.5, 0.06), (-0.49, 0.075), (-0.44, 0.075), (-0.41, 0.052), (0.3, 0.052)], 8,
                lambda k, j, c: red if c.z < -0.405 else yellow, axis=(0, 0, 1))]
    head = [(-0.275, 0.14), (-0.255, 0.178), (-0.2, 0.178), (-0.2, 0.162), (-0.035, 0.162), (-0.035, 0.168),
            (0.035, 0.168), (0.035, 0.162), (0.2, 0.162), (0.2, 0.178), (0.255, 0.178), (0.275, 0.14)]
    zc = 0.5 - 0.178
    def col(k, j, c):
        if abs(c.x) > 0.199: return yellow
        if abs(c.x) < 0.036: return white
        return red
    ex.append(lathe("head", [((x, 0, zc), r) for x, r in head], 12, lambda k, j, c: col(k, j, c - Vector((0, 0, zc))),
                    axis=(1, 0, 0), up=(0, 0, 1)))
    return ex, -0.4

def bonk_sign():
    """Tier 8: yellow diamond road sign with a black border and BONK on both faces, on a grey pole."""
    yellow, black, grey = srgb(255, 208, 0), srgb(18, 18, 20), srgb(150, 155, 165)
    ex = [lathe("pole", [(-0.5, 0.048), (-0.44, 0.048), (-0.44, 0.034), (0.1, 0.034)], 6,
                lambda k, j, c: black if c.z < -0.439 else grey, axis=(0, 0, 1))]
    side = 0.44
    zc = 0.5 - side * math.sqrt(2) / 2
    diamond = (0, math.radians(45), 0)
    ex.append(box((0, 0, zc), (side, 0.08, side), black, rot=diamond))
    ex.append(box((0, 0, zc), (side - 0.07, 0.088, side - 0.07), yellow, rot=diamond))
    for s in (-1, 1):  # front (-Y) reads left to right along +X, the back along -X
        ex += block_text("BONK", (0, s * 0.046, zc), (-s, 0, 0), (0, 0, -1), 0.021, 0.012, black)
    return ex, -0.4

def neon_stick():
    """Tier 9: neon tube glowing cyan to pink (lighter facets alternate), dark handle with cyan rings."""
    dark, cyan, pink = srgb(46, 40, 72), srgb(40, 215, 255), srgb(255, 60, 215)
    handle = [(-0.5, 0.07), (-0.49, 0.082), (-0.44, 0.082), (-0.44, 0.09), (-0.41, 0.09), (-0.41, 0.082),
              (-0.3, 0.082), (-0.3, 0.09), (-0.27, 0.09), (-0.27, 0.082), (-0.21, 0.082), (-0.21, 0.115),
              (-0.17, 0.115), (-0.17, 0.07)]
    ex = [lathe("handle", handle, 8, lambda k, j, c: cyan if c.to_2d().length > 0.079 and c.z < -0.25 else dark,
                axis=(0, 0, 1))]
    blade = [(-0.17, 0.075), (0.0, 0.078), (0.2, 0.078), (0.42, 0.075), (0.47, 0.058), (0.5, 0.03)]
    def glow(k, j, c):
        colr = mix(cyan, pink, max(0.0, min(1.0, (c.z + 0.1) / 0.5)))
        return mix(colr, (1, 1, 1), 0.45) if j % 2 == 0 else colr
    ex.append(lathe("blade", blade, 6, glow, axis=(0, 0, 1)))
    return ex, -0.36

def legendary_stick():
    """Tier 10: faceted golden staff with a big cyan crystal held by three golden prongs."""
    gold, deep, gem, gem_hi = srgb(255, 200, 45), srgb(210, 130, 20), srgb(60, 205, 255), srgb(185, 245, 255)
    facet = lambda k, j, c: gold if j % 2 == 0 else deep
    ex = [lathe("pommel", [(-0.5, 0), (-0.46, 0.075), (-0.41, 0.062), (-0.39, 0.05)], 6, facet, axis=(0, 0, 1), phase=0)]
    ex.append(lathe("shaft", [((0, 0, -0.4), 0.052), ((0.02, 0, -0.1), 0.056), ((-0.015, 0, 0.1), 0.054),
                              ((0, 0, 0.2), 0.058)], 6, facet))
    ex.append(lathe("cup", [(0.12, 0.06), (0.16, 0.1), (0.22, 0.115), (0.22, 0.07)], 6, facet, axis=(0, 0, 1)))
    ex.append(lathe("gem", [(0.19, 0), (0.3, 0.1), (0.4, 0.09), (0.5, 0)], 6,
                    lambda k, j, c: gem_hi if (j + k) % 2 == 0 else gem, axis=(0, 0, 1), phase=0))
    for k in range(3):
        a = k * math.tau / 3 + math.pi / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        ex.append(spike(d * 0.1 + Vector((0, 0, 0.2)), d * 0.25 + Vector((0, 0, 1)), 0.15, 0.03, gold, verts=4))
    return ex, -0.38

PROJECTILES = [("Stick", stick_proj), ("Newspaper", newspaper), ("Baguette", baguette), ("RollingPin", rolling_pin),
               ("BaseballBat", baseball_bat), ("GiantBone", giant_bone), ("SqueakyHammer", squeaky_hammer),
               ("BonkSign", bonk_sign), ("NeonStick", neon_stick), ("LegendaryStick", legendary_stick)]

thrown = []
for name, design in ([] if ONLY else PROJECTILES):
    objs, grip_z = design()
    o = join(objs, f"{name}_obj")
    mn, mx = wb(o)
    shift = -(mn + mx) / 2
    o.location += shift
    grip = box(Vector((0, 0, grip_z)) + shift, (0.02, 0.02, 0.02), srgb(255, 0, 255))
    grip.data.materials.append(one); grip.name = f"{name}_Grip"
    bpy.context.view_layer.update()
    export({name: o, "Grip": grip}, f"{name}.fbx")
    mn, mx = wb(o)
    print(f"BUILT {name}: {sum(len(p.vertices) - 2 for p in o.data.polygons)} triangles, size "
          f"{tuple(round(v, 3) for v in mx - mn)}, grip {tuple(round(v, 3) for v in grip.location)}")
    thrown.append((o, grip))

# --- Preview: the Shibas in a row, the projectiles in a row in front ---
for o in dog + [stick]: o.hide_render = True
for k, objs in enumerate(built):
    for o in objs: o.location.x += (k - (len(built) - 1) / 2) * 1.45
for k, (o, grip) in enumerate(thrown):
    o.location += Vector(((k - (len(thrown) - 1) / 2) * 1.2, -2.2, 0.45))
    grip.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 2000, 900
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.2, 0.22, 0.26)
cam = bpy.data.objects['Camera']
cam.location = Vector((0, -15.5, 3.2)); target = Vector((0, -0.8, 0.6))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 36  # wide enough for all ten Shibas
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "preview_only.png" if ONLY else "preview_tiers.png")
bpy.ops.render.render(write_still=True)
if ONLY:
    # Close-ups: each Shiba alone, turned three-quarters toward the camera (preview_<asset>.png).
    for k, objs in enumerate(built):
        for other in built:
            for o in other: o.hide_render = other is not objs
        shift = (k - (len(built) - 1) / 2) * 1.45
        cam.data.lens = 50
        target = Vector((shift, 0, 0.62))
        cam.location = target + Vector((1.2, -2.6, 0.55))
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = 700, 800
        sc.render.filepath = os.path.join(OUT, f"preview_{objs[0].name.split('_')[0]}.png")
        bpy.ops.render.render(write_still=True)
    print("DONE", sorted(os.listdir(OUT)))
    sys.exit(0)

# --- Projectiles preview, from the exported files as the game gets them: the ten projectiles (top), and each tier's
# Shiba holding its tier's projectile the way the game does it (bottom): Grip on the paw stick's lower end, long axis
# along the stick, 0.75 x the stick's length (Config/Gameplay -> Shooters.HandProjectile.LengthScale). Back faces are
# culled like in Roblox, so wrongly wound faces would show as holes. ---
for o in sc.objects: o.hide_render = True
view = bpy.data.collections.new("ProjectilesPreview"); sc.collection.children.link(view)
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[view.name]

def import_fbx(filename):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, filename), axis_forward='Z', axis_up='Y')
    bpy.context.view_layer.update()
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def base_name(o):
    return o.name.split(".")[0]

def move(objs, m):
    for o in objs: o.matrix_world = m @ o.matrix_world

SPACING = 1.65
for k, ((name, _), (shiba, _)) in enumerate(zip(PROJECTILES, DESIGNS)):
    x = (k - (len(PROJECTILES) - 1) / 2) * SPACING
    proj = import_fbx(f"{name}.fbx")
    grip = next(o for o in proj if base_name(o) == "Grip")
    grip_pos = grip.matrix_world.translation.copy()
    grip.hide_render = True
    # Top row: standing, turned a little so the faces show.
    move(proj, Matrix.Translation((x, 0, 2.55)) @ Matrix.Rotation(math.radians(-25), 4, 'Z')
         @ Matrix.Rotation(math.radians(12), 4, 'Y'))
    # Bottom row: the same projectile once more, in the Shiba's paw.
    held = import_fbx(f"{name}.fbx")
    dog_objs = import_fbx(f"{shiba}.fbx")
    hstick = next(o for o in dog_objs if base_name(o) == "Stick")
    hstick.hide_render = True
    pts = [hstick.matrix_world @ v.co for v in hstick.data.vertices]
    c = sum(pts, Vector()) / len(pts)
    up = max((b - a for a in pts for b in pts), key=lambda v: v.length).normalized()
    if up.z < 0: up = -up
    along = [(p - c).dot(up) for p in pts]
    stick_len = max(along) - min(along)
    stick_grip = c + up * min(along)
    right = Vector((1, 0, 0)) - up * up.x; right.normalize()
    rot = Matrix((right, up.cross(right), up)).transposed().to_4x4()
    hmn = Vector((min(min((o.matrix_world @ Vector(b)).z for b in o.bound_box) for o in held),) * 3)
    hmx = Vector((max(max((o.matrix_world @ Vector(b)).z for b in o.bound_box) for o in held),) * 3)
    s = stick_len * 0.75 / (hmx.z - hmn.z)
    move(held, Matrix.Translation(stick_grip) @ rot @ Matrix.Scale(s, 4) @ Matrix.Translation(-grip_pos))
    for o in held:
        if base_name(o) == "Grip": o.hide_render = True
    move(held + dog_objs, Matrix.Translation((x, 0, 0)))
    for o in dog_objs:
        if base_name(o) in ("Shoulder", "OrbitCenter"): o.hide_render = True

sc.display.shading.show_backface_culling = True
sc.render.resolution_x, sc.render.resolution_y = 2800, 700
cam2 = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam")); view.objects.link(cam2)
cam2.data.type = 'ORTHO'; cam2.data.ortho_scale = 17.6
cam2.location = Vector((0, -12, 2.75)); cam2.rotation_euler = (math.radians(84), 0, 0)
sc.camera = cam2
sc.render.filepath = os.path.join(OUT, "preview_projectiles.png")
bpy.ops.render.render(write_still=True)
print("DONE", sorted(os.listdir(OUT)))
