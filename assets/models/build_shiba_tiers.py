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

# --- Shibas 21-30 (the third set, "top" Shibas: DJ, Knight, Superhero, Frost, Magma, Mecha, Angel, Demon, Eternal,
# Void). Same dog and model contract; helpers below are only used by these designs. ---
def mesh_obj(name, verts, faces, colors, double=False):
    """One mesh from raw faces, one colour per face (a list, or fn(face centre) -> colour). double=True adds a
    back side (own vertices, reversed faces) for thin sheets: Roblox draws one side only."""
    verts = [Vector(v) for v in verts]
    faces = [list(f) for f in faces]
    cols = [colors(sum((verts[i] for i in f), Vector()) / len(f)) if callable(colors) else colors[k]
            for k, f in enumerate(faces)]
    if double:
        n = len(verts)
        verts = verts + [v.copy() for v in verts]
        faces = faces + [[i + n for i in reversed(f)] for f in faces]
        cols = cols + [tuple(c * 0.8 for c in col) for col in cols]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            attr.data[li].color = (*cols[poly.index], 1.0)
    me.color_attributes.active_color = attr
    return o

def curve_tube(name, pts, radii, sides, col):
    """Faceted tube along the polyline pts, radius per point (0 closes that end in a point, otherwise flat caps).
    col(k, j, face centre) -> colour, k = segment (-1 start cap, len(pts) - 1 end cap). Faces wind outward."""
    pts = [Vector(p) for p in pts]
    verts, faces, cols, rows = [], [], [], []
    e1 = None
    for k, p in enumerate(pts):
        t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        e1 = t.orthogonal().normalized() if e1 is None else (e1 - t * e1.dot(t)).normalized()
        e2 = t.cross(e1)
        if radii[k] <= 0:
            rows.append([len(verts)]); verts.append(p)
            continue
        row = []
        for j in range(sides):
            a = j * math.tau / sides
            row.append(len(verts)); verts.append(p + (e1 * math.cos(a) + e2 * math.sin(a)) * radii[k])
        rows.append(row)

    def add(face, k, j):
        faces.append(face); cols.append(col(k, j, sum((verts[i] for i in face), Vector()) / len(face)))
    for k in range(len(rows) - 1):
        a, b = rows[k], rows[k + 1]
        for j in range(sides):
            jn = (j + 1) % sides
            if len(a) == 1: add([a[0], b[jn], b[j]], k, j)
            elif len(b) == 1: add([a[j], a[jn], b[0]], k, j)
            else: add([a[j], a[jn], b[jn], b[j]], k, j)
    if len(rows[0]) > 1: add(list(reversed(rows[0])), -1, 0)
    if len(rows[-1]) > 1: add(list(rows[-1]), len(rows) - 1, 0)
    return mesh_obj(name, verts, faces, cols)

def arc(center, e1, e2, radius, a0, a1, n):
    """Points on a circular arc from angle a0 to a1 (radians) in the plane spanned by e1, e2."""
    center, e1, e2 = Vector(center), Vector(e1), Vector(e2)
    return [center + (e1 * math.cos(a0 + (a1 - a0) * k / n) + e2 * math.sin(a0 + (a1 - a0) * k / n)) * radius
            for k in range(n + 1)]

def feather(base, direction, length, width, flat, color, tip=None):
    """One low-poly feather: a flattened spindle from base along direction, thin across `flat` (the wing's normal),
    blending from color to tip."""
    d = Vector(direction).normalized()
    n = Vector(flat); n = (n - d * n.dot(d)).normalized(); x = n.cross(d)
    m = Matrix((x, n, d)).transposed()
    base = Vector(base)
    fn = (lambda p, nm, i: mix(color, tip, max(0.0, min(1.0, (p - base).dot(d) / length)))) if tip else None
    return prim("uv", base + d * length / 2, m.to_euler(), scale=(width, width * 0.2, length / 2), color=color, fn=fn,
                segments=6, ring_count=4, radius=1)

def feather_wing(root, s, span, rise, back, n, length, colors, tip, flat_tilt=0.35, rows=3, fw=0.1):
    """A spread feathered wing on side s (1 = right): a curved arm from root out to the tip; `rows` rows of feathers
    hang from it, turning from pointing down (near the body) to pointing outward along the arm (at the tip), the
    longest (primaries) at the back, shorter coverts in front."""
    root = Vector(root)
    ctrl = [root, root + Vector((s * span * 0.45, back * 0.4, rise * 0.95)), root + Vector((s * span, back, rise))]
    arm = lambda t: ctrl[0] * (1 - t) ** 2 + ctrl[1] * 2 * t * (1 - t) + ctrl[2] * t * t
    out = [curve_tube("wingarm", [arm(k / 8) for k in range(9)], [0.055 - 0.03 * k / 8 for k in range(9)], 6,
                      lambda k, j, c: colors[0])]
    flat = Vector((s * flat_tilt, 1, 0)).normalized()
    down = Vector((s * 0.45, 0.1, -1)).normalized()
    for r in range(rows):
        m = n + (2 if r == 0 else 0)
        for k in range(m):
            t = (k + 0.5) / m
            p = arm(t) + Vector((0, -0.035 * r, -0.03 * r))
            along = (arm(min(1, t + 0.05)) - arm(max(0, t - 0.05))).normalized()
            d = down.lerp(along, 0.1 + 0.6 * t ** 1.5).normalized()
            L = length * (0.75 + 0.55 * t) * (1, 0.6, 0.34)[r]
            out.append(feather(p, d, L, fw * (1, 1.05, 1.15)[r], flat, colors[r % len(colors)],
                               tip if r == 0 else None))
    return out

def bat_wing(root, s, size, bone, skin, skin2):
    """A bat wing on side s: arm (root, elbow, wrist), four finger bones fanning out from the wrist, a scalloped
    membrane between them down to the body (both sides), a claw on the elbow."""
    R = Vector(root)
    v = lambda x, y, z: Vector((s * x, y, z)) * size
    E = R + v(0.3, 0.12, 0.38); W = E + v(0.28, 0.1, 0.12)
    tips = [W + v(0.42, 0.12, 0.38), W + v(0.58, 0.14, 0.02), W + v(0.48, 0.12, -0.34), W + v(0.22, 0.1, -0.6)]
    B = R + v(0.08, 0.05, -0.45)
    pts = [R, E, W] + tips + [B]
    faces, cols = [], []
    idx = lambda p: pts.index(p) if p in pts else (pts.append(p) or len(pts) - 1)
    edge = tips + [B]
    faces.append([idx(R), idx(E), idx(W)]); cols.append(skin)
    faces.append([idx(E), idx(tips[0]), idx(W)]); cols.append(skin2)
    for k in range(len(edge) - 1):
        a, b = edge[k], edge[k + 1]
        m = (a + b) / 2 + (W - (a + b) / 2) * 0.28
        faces.append([idx(W), idx(a), idx(m)]); cols.append(skin if k % 2 else skin2)
        faces.append([idx(W), idx(m), idx(b)]); cols.append(skin2 if k % 2 else skin)
    faces.append([idx(W), idx(B), idx(R)]); cols.append(skin)
    out = [mesh_obj("membrane", pts, faces, cols, double=True)]
    out.append(curve_tube("bone", [R, E, W], [0.04 * size, 0.035 * size, 0.03 * size], 5, lambda k, j, c: bone))
    for t in tips:
        out.append(curve_tube("finger", [W, t], [0.022 * size, 0], 4, lambda k, j, c: bone))
    out.append(spike(E, v(0.1, 0, 1), 0.12 * size, 0.03 * size, bone, verts=4))
    return out

def lit_eyes(l, color, glint=None, size=(0.06, 0.022, 0.036), angle=24, dz=-0.005):
    """Glowing almond eyes over the closed-eye lines (like the Galaxy Shiba's), with a white glint."""
    out = []
    for s in (-1, 1):
        x, z = s * l.eye_x, l.eye_z + dz
        out.append(ball((x, face_y(l, x, z) + 0.004, z), 1, color, scale=size, rot=(0, 0, s * math.radians(angle))))
        if glint:
            gx = x - s * 0.018
            out.append(ball((gx, face_y(l, gx, z + 0.012) - 0.014, z + 0.012), 0.014, glint))
    return out

def vein_paint(parts, rock, glow, hot, thresh, freq=1.0, keep_dark=True):
    """Per-face paint for every part: rock (fn(face centre)) with glowing veins where a smooth 3D wave pattern
    crosses zero (glow, the core `hot`). Decided per face, so each face is one solid colour."""
    cols = {}
    for name, o in parts.items():
        mw = o.matrix_world; table = {}
        for poly in o.data.polygons:
            c = mw @ poly.center
            mat = o.data.materials[poly.material_index].name if len(o.data.materials) else ""
            w = (math.sin(c.x * 9.1 * freq + c.z * 4.3 * freq) + math.sin(c.y * 8.3 * freq - c.z * 7.7 * freq + 1.3)
                 + math.sin(c.x * 5.3 * freq + c.y * 6.1 * freq + c.z * 10.7 * freq + 2.1))
            if keep_dark and mat == "fur_dark":
                table[poly.index] = DARK
            elif abs(w) < thresh * 0.35:
                table[poly.index] = hot
            elif abs(w) < thresh:
                table[poly.index] = glow
            else:
                table[poly.index] = rock(c)
        cols[f"{name}:*"] = lambda p, n, i, t=table: t[i]
    return cols

def slab(outline, center, right, up, thickness, front, back=None, side=None):
    """Flat plate from a 2D outline (convex, counter-clockwise seen from the front) in the plane right/up at center,
    `thickness` deep toward the back (normal = right x up points to the front)."""
    right, up = Vector(right).normalized(), Vector(up).normalized()
    nrm = right.cross(up).normalized()
    c = Vector(center)
    f = [c + right * x + up * y + nrm * thickness / 2 for x, y in outline]
    b = [p - nrm * thickness for p in f]
    n = len(outline)
    faces = [list(range(n)), [n + i for i in reversed(range(n))]]
    cols = [front, back or front]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, n + i, n + j, j]); cols.append(side or back or front)
    return mesh_obj("slab", f + b, faces, cols)

def glyph(center, right, up, size, color, rng):
    """A little rune: two or three thin bars in a random arrangement (clock halo, sigils)."""
    right, up = Vector(right).normalized(), Vector(up).normalized()
    nrm = right.cross(up)
    m = Matrix((right, up, nrm)).transposed().to_euler()
    out = []
    shapes = [[(0, 0, 0.1, 1), (0, 0.35, 0.7, 0.1)], [(-0.3, 0, 0.1, 1), (0.3, 0, 0.1, 1), (0, 0, 0.7, 0.1)],
              [(0, 0, 0.1, 1), (-0.2, 0.3, 0.5, 0.1), (0.2, -0.3, 0.5, 0.1)], [(0, 0.4, 0.8, 0.1), (0, -0.4, 0.8, 0.1),
              (0, 0, 0.1, 0.8)], [(-0.25, 0, 0.1, 1), (0.1, 0.1, 0.6, 0.1), (0.25, -0.3, 0.1, 0.5)]]
    for x, y, w, h in rng.choice(shapes):
        out.append(prim("cube", Vector(center) + right * x * size + up * y * size, m,
                        scale=(max(w, 0.18) * size, max(h, 0.18) * size, size * 0.2), color=color, size=1))
    return out

def crack_lines(samples, rng, colors, segs=4):
    """Glowing zigzag cracks lying on the fur: from each sample (object, point, normal) a few short bars, each end
    ray-cast back onto the surface so they follow it."""
    out = []
    for o, p, n in samples:
        mw, mwi = o.matrix_world, o.matrix_world.inverted()
        d = n.orthogonal().normalized()
        d.rotate(Matrix.Rotation(rng.uniform(0, math.tau), 3, n))
        a = p
        for k in range(segs):
            d.rotate(Matrix.Rotation(rng.uniform(-0.8, 0.8), 3, n))
            q = a + d * rng.uniform(0.05, 0.085)
            hit, loc, nrm, _ = o.ray_cast(mwi @ (q + n * 0.08), (mwi.to_3x3() @ -n).normalized(), distance=0.2)
            if not hit:
                break
            q = mw @ loc
            seg = q - a
            if seg.length < 0.02:
                break
            t = seg.normalized(); side = n.cross(t).normalized(); up = t.cross(side)
            m = Matrix((t, side, up)).transposed().to_euler()
            out.append(prim("cube", (a + q) / 2 + n * 0.004, m, scale=(seg.length + 0.018, 0.024, 0.022),
                            color=colors[k % len(colors)], size=1))
            a = q
    return out

def dj(parts, hs):
    l = landmarks(parts); ex = []
    black, grey, pink, cyan = srgb(28, 28, 34), srgb(120, 124, 136), srgb(255, 60, 190), srgb(40, 230, 255)
    cap, gold, white = srgb(120, 50, 230), srgb(255, 200, 45), srgb(245, 245, 250)
    top = l.skull_top - 0.03
    # Cap worn backwards: dome, the visor pointing back, a button on top.
    ex.append(ball((0, l.head_c.y + 0.02, top + 0.02), 1, cap, scale=(0.215, 0.235, 0.12)))
    ex.append(ball((0, l.head_c.y + 0.27, top - 0.01), 1, pink, scale=(0.17, 0.16, 0.022),
                   rot=(math.radians(14), 0, 0)))
    ex.append(ball((0, l.head_c.y + 0.02, top + 0.135), 0.025, pink))
    # Big headphones: cups on the sides of the head, band arching over the cap.
    cy, rx, ry = head_section(l, l.eye_z)
    for s in (-1, 1):
        x = s * (rx + 0.02)
        ex.append(prim("cyl", (x, cy + 0.02, l.eye_z), (0, math.radians(90), 0), color=black, vertices=12,
                       radius=0.12, depth=0.08))
        ex.append(prim("cyl", (x + s * 0.045, cy + 0.02, l.eye_z), (0, math.radians(90), 0), color=pink, vertices=12,
                       radius=0.085, depth=0.02))
        ex.append(ring((x + s * 0.042, cy + 0.02, l.eye_z), 0.1, 0.012, cyan, rot=(0, math.radians(90), 0),
                       segments=14))
    band_r = rx + 0.06
    pts = arc((0, cy + 0.02, l.eye_z), (1, 0, 0), (0, 0, 1), band_r, 0.12, math.pi - 0.12, 10)
    pts = [p + Vector((0, 0, max(0.0, top + 0.17 - l.eye_z - band_r) * (p.z - l.eye_z) / band_r)) for p in pts]
    ex.append(curve_tube("band", pts, [0.03] * len(pts), 6, lambda k, j, c: black))
    # Gold chain with a golden record pendant.
    chest_z = l.neck_z - 0.1
    chain_pts = []
    for i in range(11):
        t = -1 + i / 5
        z = chest_z + 0.09 * t * t
        chain_pts.append((0.2 * t, front_y(parts["Torso"], z, x=0.2 * t) - 0.015, z))
    ex += chain(chain_pts, gold)
    pz = chest_z - 0.1
    py = front_y(parts["Torso"], pz) - 0.025
    ex.append(prim("cyl", (0, py, pz), (math.radians(90), 0, 0), color=gold, vertices=14, radius=0.075, depth=0.02))
    ex.append(prim("cyl", (0, py - 0.012, pz), (math.radians(90), 0, 0), color=pink, vertices=10, radius=0.028,
                   depth=0.01))
    # DJ booth beside the free paw: a speaker box with two woofers, a turntable on top with a spinning record.
    sp = Vector((-0.68, -0.02, 0.0))
    ex.append(box(sp + Vector((0, 0, 0.26)), (0.36, 0.34, 0.52), black))
    ex.append(box(sp + Vector((0, 0, 0.52)), (0.38, 0.36, 0.025), pink))
    for z, r in ((0.15, 0.12), (0.37, 0.08)):
        fy = sp.y - 0.17
        ex.append(ring((sp.x, fy - 0.005, z), r, 0.018, grey, rot=(math.radians(90), 0, 0), segments=16))
        ex.append(prim("cone", (sp.x, fy + 0.01, z), (math.radians(90), 0, 0), color=srgb(55, 55, 65), vertices=12,
                       radius1=r, radius2=r * 0.3, depth=0.03))
        ex.append(ball((sp.x, fy - 0.02, z), r * 0.28, cyan))
    deck = sp + Vector((0, 0, 0.56))
    ex.append(box(deck, (0.42, 0.38, 0.06), grey))
    ex.append(prim("cyl", deck + Vector((-0.03, 0, 0.045)), color=black, vertices=16, radius=0.15, depth=0.025))
    ex.append(prim("cyl", deck + Vector((-0.03, 0, 0.062)), color=pink, vertices=10, radius=0.05, depth=0.012))
    ex.append(rod(deck + Vector((0.16, 0.13, 0.05)), deck + Vector((0.06, -0.06, 0.07)), 0.012, white, verts=4))
    for k, col in enumerate((cyan, pink, srgb(90, 255, 120))):
        ex.append(box(deck + Vector((0.15, -0.14 + 0.05 * k, 0.04)), (0.05, 0.03, 0.02), col))
    # Record in the free paw.
    rec = l.left_hand + Vector((-0.03, -0.08, 0.1))
    ex.append(prim("cyl", rec, (math.radians(80), 0, math.radians(-20)), color=black, vertices=16, radius=0.12,
                   depth=0.015))
    ex.append(prim("cyl", rec + Vector((0.003, -0.01, 0)), (math.radians(80), 0, math.radians(-20)), color=cyan,
                   vertices=10, radius=0.045, depth=0.012))
    return default_cols(), ex

def knight(parts, hs):
    l = landmarks(parts); ex = []
    steel, dark, shine = srgb(185, 192, 205), srgb(105, 112, 128), srgb(235, 240, 250)
    red, blue, gold, white = srgb(215, 30, 40), srgb(35, 70, 185), srgb(255, 200, 45), srgb(250, 248, 240)
    top = l.skull_top - 0.04
    polish = lambda p, n, i: mix(steel, shine, max(0.0, min(1.0, (p.z - top) / 0.18)))
    # Great helm: dome over the skull, a rim, cheek guards, the visor raised on the forehead, a red plume.
    ex.append(ball((0, l.head_c.y + 0.01, top + 0.01), 1, None, scale=(0.235, 0.255, 0.19), fn=polish))
    rim_z = l.eye_z + 0.075
    cy, rx, ry = head_section(l, rim_z)
    ex.append(ring((0, cy, rim_z), rx + 0.02, 0.028, dark, scale=(1, (ry + 0.02) / (rx + 0.02), 1), segments=20))
    for s in (-1, 1):
        ex.append(box((s * (rx + 0.005), cy + 0.04, l.eye_z - 0.03), (0.04, 0.2, 0.2), steel,
                      rot=(0, s * math.radians(-8), 0)))
    # Raised visor: a plate standing up on the forehead with a gold edge and breathing slits.
    vz = rim_z + 0.06
    vy = face_y(l, 0, min(vz, l.skull_top - 0.05)) - 0.035
    vrot = (math.radians(-68), 0, 0)
    ex.append(box((0, vy, vz), (0.3, 0.13, 0.035), dark, rot=vrot))
    ex.append(box((0, vy - 0.02, vz + 0.055), (0.31, 0.03, 0.04), gold, rot=vrot))
    for x in (-0.08, -0.04, 0.0, 0.04, 0.08):
        ex.append(box((x, vy - 0.02, vz - 0.005), (0.012, 0.06, 0.012), srgb(30, 30, 40), rot=vrot))
    # Plume: a fan of tall red feathers sweeping back from a gold socket.
    crest = Vector((0, l.head_c.y + 0.02, top + 0.17))
    ex.append(prim("cyl", crest, color=gold, vertices=8, radius=0.045, depth=0.07))
    for k, a in enumerate((-10, 10, 32, 55, 78)):
        ar = math.radians(a)
        d = Vector((0, math.sin(ar), math.cos(ar)))
        ex.append(feather(crest, d, 0.34 - 0.03 * k, 0.07, (1, 0, 0), red, srgb(255, 90, 80)))
    # Breastplate following the chest with a red cross, gorget, a pauldron on the shield side (the throwing side's
    # goes on the arm).
    lo, hi = l.torso_min.z + 0.2, l.neck_z - 0.02
    plate = srgb(150, 158, 176)
    ex.append(shell(parts['Torso'], lambda c, nrm: nrm.y < -0.25 and lo < c.z < hi and abs(c.x) < 0.3, 0.018,
                    lambda p, n, i: mix(plate, shine, max(0.0, min(1.0, (p.z - lo) / (hi - lo))) ** 1.5)))
    cz = (lo + hi) / 2 + 0.02
    cyf = front_y(parts['Torso'], cz) - 0.03
    ex.append(box((0, cyf, cz), (0.07, 0.03, 0.3), red))
    ex.append(box((0, cyf - 0.002, cz + 0.05), (0.24, 0.03, 0.07), red))
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.25, 0.045, steel, rot=(math.radians(-18), 0, 0), segments=16))
    ex.append(ring((0, (l.torso_min.y + l.torso_max.y) / 2, l.torso_min.z + 0.2), 0.36, 0.035, srgb(60, 40, 28),
                   scale=(1, 0.85, 1), segments=18))
    ex.append(box((0, front_y(parts['Torso'], l.torso_min.z + 0.2) - 0.03, l.torso_min.z + 0.2), (0.08, 0.03, 0.07),
                  gold))
    lu_min, lu_max = wb(parts['LeftUpperArm'])
    ex.append(ball(((lu_min.x + lu_max.x) / 2 - 0.02, (lu_min.y + lu_max.y) / 2, lu_max.z - 0.02), 1, steel,
                   scale=(0.16, 0.16, 0.1), rot=(0, math.radians(-25), 0)))
    ru_min, ru_max = wb(parts['RightUpperArm'])
    arm_plate = ball(((ru_min.x + ru_max.x) / 2 + 0.02, (ru_min.y + ru_max.y) / 2, ru_max.z - 0.02), 1, steel,
                     scale=(0.15, 0.15, 0.09), rot=(0, math.radians(25), 0))
    # Kite shield on the free arm: gold border, blue field, a white bone crest.
    c = l.left_hand + Vector((-0.1, -0.1, 0.28))
    right, up = Vector((1, -0.45, 0)).normalized(), Vector((0, 0, 1))
    kite = [(0, -0.3), (0.17, 0.02), (0.15, 0.17), (0, 0.22), (-0.15, 0.17), (-0.17, 0.02)]
    ex.append(slab([(x * 1.12, y * 1.1) for x, y in kite], c, right, up, 0.04, gold, dark))
    nrm = right.cross(up)
    ex.append(slab(kite, c + nrm * 0.012, right, up, 0.03, blue))
    fc = c + nrm * 0.03 + up * 0.0
    d = (right * 0.6 + up * 0.8).normalized()
    ex.append(rod(fc - d * 0.09, fc + d * 0.09, 0.022, white, verts=6))
    for e in (-1, 1):
        for q in (-1, 1):
            ex.append(ball(fc + d * 0.1 * e + (right * 0.8 - up * 0.6).normalized() * 0.025 * q, 0.028, white))
    return default_cols(), ex, {"ThrowArm": [arm_plate]}

def superhero(parts, hs):
    l = landmarks(parts); ex = []
    blue, blue2, red, dred, yellow = srgb(30, 85, 215), srgb(70, 130, 240), srgb(220, 30, 40), srgb(150, 15, 25), \
        srgb(255, 210, 40)
    fur = {"fur_orange": ORANGE, "fur_cream": CREAM, "fur_dark": DARK}
    cols = default_cols()
    # Blue suit on the body, red gloves and boots; the head and tail keep the Shiba fur.
    for name in parts:
        if name in ("Head", "Tail"):
            continue
        glove = name.endswith("Hand")
        boot = name.endswith("Leg")
        cols[f"{name}:*"] = (lambda p, n, i, g=glove, b=boot: red if g or (b and p.z < 0.16) else
                             (blue2 if n == "fur_cream" else blue))
    ex.append(ring((0, (l.torso_min.y + l.torso_max.y) / 2, l.torso_min.z + 0.22), 0.37, 0.035, yellow,
                   scale=(1, 0.85, 1), segments=18))
    # Chest emblem: yellow diamond with a red B.
    ez = l.neck_z - 0.2
    ey = front_y(parts['Torso'], ez) - 0.02
    ex.append(box((0, ey, ez), (0.24, 0.03, 0.24), yellow, rot=(0, math.radians(45), 0)))
    ex += pixel_text("B", Vector((-0.054, ey - 0.02, ez + 0.09)), (1, 0, 0), (0, 0, -1), 0.036, (0, -1, 0), red)
    # Domino mask: the band of the face around the eyes turns navy (decided per face, crisp edge), white lenses.
    mask = srgb(20, 30, 75)
    head = parts['Head']
    in_mask = set()
    for poly in head.data.polygons:
        c = head.matrix_world @ poly.center
        if l.eye_z - 0.045 < c.z < l.eye_z + 0.055 and c.y < l.eye_y + 0.09 and abs(c.x) < 0.27:
            in_mask.add(poly.index)
    cols["Head:*"] = lambda p, n, i: mask if i in in_mask else fur.get(n, ORANGE)
    mz = l.eye_z + 0.005
    for s in (-1, 1):
        x = s * l.eye_x
        ex.append(ball((x, face_y(l, x, mz) - 0.008, mz), 1, srgb(255, 255, 255), scale=(0.058, 0.016, 0.03),
                       rot=(0, 0, s * math.radians(20))))
        ex.append(ball((s * 0.255, l.eye_y + 0.1, mz + 0.01), 1, mask, scale=(0.05, 0.02, 0.03),
                       rot=(0, 0, s * math.radians(-60))))
    # Cape: from the shoulders down the back, flaring wide and billowing out to the free-paw side (away from the
    # throwing arm).
    rows, colsn = 7, 7
    verts = []
    for r in range(rows):
        t = r / (rows - 1)
        width = 0.3 + 0.75 * t
        for k in range(colsn):
            u = k / (colsn - 1) * 2 - 1
            wave = 0.08 * math.sin(u * 4.2 + t * 2) * t
            x = u * width - 0.3 * t * t
            y = l.back_y + 0.05 + 0.6 * t * t + 0.12 * (1 - u * u) * (1 - t) + wave
            z = l.neck_z + 0.02 - t * (l.neck_z - 0.12) + 0.28 * t * t * (0.6 + 0.4 * u * u)
            if r == 0:
                y = l.head_c.y + 0.12 + 0.08 * u * u
            verts.append((x, y, z))
    faces = []
    for r in range(rows - 1):
        for k in range(colsn - 1):
            a = r * colsn + k
            faces.append([a, a + colsn, a + colsn + 1, a + 1])
    ex.append(mesh_obj("cape", verts, faces, lambda c: red, double=True))
    for s in (-1, 1):
        ex.append(ball((s * 0.22, l.head_c.y + 0.08, l.neck_z + 0.01), 0.045, yellow))
        # High stand-up collar of the cape behind the head, and the cape draped over the shoulders.
        ex.append(box((s * 0.17, l.head_c.y + 0.17, l.neck_z + 0.13), (0.2, 0.025, 0.26), red,
                      rot=(math.radians(-18), 0, s * math.radians(-32))))
        ex.append(ball((s * 0.27, l.head_c.y + 0.12, l.shoulder_z + 0.03), 1, red, scale=(0.13, 0.15, 0.05),
                       rot=(0, s * math.radians(28), 0)))
    return cols, ex

def frost(parts, hs):
    l = landmarks(parts); ex = []
    ice, ice2, white, deep = srgb(135, 210, 255), srgb(60, 140, 230), srgb(245, 252, 255), srgb(25, 50, 110)
    span = l.max_z - l.min_z
    cols = {"fur_orange": lambda p: mix(ice2, ice, (p.z - l.min_z) / span),
            "fur_cream": lambda p: white, "fur_dark": lambda p: deep}
    ex += lit_eyes(l, srgb(120, 245, 255), srgb(255, 255, 255))
    # Ice crystal crown: a circlet with tall six-sided crystals, the middle one tallest.
    top = l.skull_top - 0.04
    cy, rx, ry = head_section(l, top - 0.02)
    ex.append(ring((0, cy, top - 0.02), rx + 0.01, 0.025, white, scale=(1, (ry + 0.01) / (rx + 0.01), 1), segments=18))
    for k, (a, h) in enumerate(((-90, 0.38), (-60, 0.26), (-120, 0.26), (-30, 0.18), (-150, 0.18), (10, 0.14),
                                (190, 0.14))):
        ar = math.radians(a)
        base = Vector((math.cos(ar) * (rx + 0.01), cy + math.sin(ar) * (ry + 0.01), top - 0.03))
        d = Vector((math.cos(ar) * 0.25, math.sin(ar) * 0.25, 1))
        ex.append(spike(base, d, h, 0.045 if k else 0.06, ice, verts=6, tip=white))
    # Icicles under the chin and along the frost mantle's hem.
    for k, x in enumerate((-0.09, -0.03, 0.03, 0.09)):
        ex.append(spike(l.mouth + Vector((x, 0.03, -0.03)), (0, 0, -1), 0.08 + 0.04 * (k % 2), 0.018, ice, verts=4,
                        tip=white))
    # Frost mantle: a pale blue cape from the shoulders, a snowy fur collar, icicles on its hem.
    top_z, bottom_z = l.neck_z, l.min_z + 0.2
    ex.append(prim("cone", (0, l.back_y + 0.04, (top_z + bottom_z) / 2), color=ice2, vertices=8, radius1=0.46,
                   radius2=0.26, depth=top_z - bottom_z, scale=(1, 0.32, 1)))
    for k in range(7):
        x = -0.36 + 0.12 * k
        ex.append(spike((x, l.back_y + 0.1, bottom_z + 0.01), (0, 0, -1), 0.12 + 0.06 * (k % 2), 0.03, ice, verts=4,
                        tip=white))
    for k in range(12):
        a = k * math.tau / 12
        ex.append(ball((math.cos(a) * 0.24, l.head_c.y + 0.07 + math.sin(a) * 0.22, l.neck_z - 0.02 +
                        0.04 * math.sin(a)), 0.055, white))
    # Ice shards on the free shoulder, a crystal cluster on the throwing arm, jagged ice on the ground.
    sh = Vector((-0.3, 0.0, l.shoulder_z + 0.05))
    for d, h in (((-0.5, 0.1, 1), 0.2), ((-1, 0.2, 0.5), 0.15), ((-0.2, 0.4, 1), 0.13)):
        ex.append(spike(sh, d, h, 0.04, ice, verts=5, tip=white))
    ru_min, ru_max = wb(parts['RightUpperArm'])
    arm = [spike(((ru_min.x + ru_max.x) / 2 + 0.06, (ru_min.y + ru_max.y) / 2, ru_max.z - 0.05), d, h, 0.035, ice,
                 verts=5, tip=white) for d, h in (((0.6, 0.1, 1), 0.16), ((1, 0.2, 0.3), 0.12))]
    rng = random.Random(21)
    for k in range(11):
        a = math.radians(-20 - k * 30 + rng.uniform(-8, 8))
        r = rng.uniform(0.5, 0.62)
        base = Vector((math.cos(a) * r, math.sin(a) * r * 0.9, -0.02))
        d = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 1))
        ex.append(spike(base, d, rng.uniform(0.2, 0.42), rng.uniform(0.05, 0.085), ice, verts=5, tip=white))
    ex.append(prim("cyl", (0, 0.05, -0.005), color=srgb(200, 235, 255), vertices=9, radius=0.64, depth=0.035,
                   scale=(1, 0.9, 1)))
    ex.append(prim("cyl", (0.1, -0.1, 0.0), color=white, vertices=7, radius=0.35, depth=0.037, scale=(1.2, 0.8, 1)))
    return cols, ex, {"ThrowArm": arm}

def magma(parts, hs):
    l = landmarks(parts); ex = []
    r1, r2 = srgb(34, 28, 28), srgb(58, 44, 40)
    lava, hot, crust = srgb(255, 100, 15), srgb(255, 215, 70), srgb(20, 16, 16)
    rock = lambda c: r2 if (int(c.x * 14 + 50) + int(c.y * 14 + 50) + int(c.z * 14)) % 3 == 0 else r1
    cols = vein_paint(parts, rock, lava, hot, 0.16)
    # Molten inside: the cream fur (belly, muzzle, paws) glows from orange to yellow-hot.
    for name, o in parts.items():
        base = cols[f"{name}:*"]
        cols[f"{name}:*"] = (lambda p, n, i, base=base: mix(lava, hot, max(0.0, min(1.0, (p.z - 0.05) / 0.9)))
                             if n == "fur_cream" else base(p, n, i))
    ex += lit_eyes(l, srgb(255, 170, 30), srgb(255, 250, 200))
    # Glowing zigzag cracks all over the rock fur (not on the face); the arm's cracks swing with the arm.
    rng = random.Random(22)
    head = parts['Head']
    face = lambda c: c.y < l.eye_y + 0.08 and l.mouth.z - 0.06 < c.z < l.eye_z + 0.07 and abs(c.x) < 0.24
    keep = lambda o, c, nrm, mat: mat == "fur_orange" and nrm.z > -0.4 and not (o is head and face(c))
    armp = [parts[n] for n in ARM_NAMES]
    samples = surface_samples(list(parts.values()), 34, rng, keep, 0.14)
    ex += crack_lines([s for s in samples if s[0] not in armp], rng, [lava, hot, lava], segs=5)
    arm_cracks = crack_lines([s for s in samples if s[0] in armp], rng, [lava, hot, lava], segs=5)
    # Volcanic crown: a ring of jagged obsidian spikes with molten tips round a smoking volcano with a glowing crater
    # and a lava blob bursting out.
    top = l.skull_top - 0.05
    cy, rx, ry = head_section(l, top)
    for k in range(9):
        ar = math.radians(-90 + (k - 4) * 40)
        base = Vector((math.cos(ar) * rx * 0.85, cy + math.sin(ar) * ry * 0.85, top))
        d = Vector((math.cos(ar) * 0.4, math.sin(ar) * 0.4, 1))
        ex.append(spike(base, d, 0.2 - 0.02 * abs(k - 4) + 0.05 * (k % 2), 0.05, r1, verts=4, tip=lava))
    vc = Vector((0, cy, top + 0.02))
    ex.append(prim("cone", vc + Vector((0, 0, 0.1)), color=r2, vertices=7, radius1=0.13, radius2=0.06, depth=0.2))
    ex.append(prim("cyl", vc + Vector((0, 0, 0.205)), color=hot, vertices=7, radius=0.05, depth=0.02))
    ex.append(ball(vc + Vector((0, 0, 0.26)), 0.05, lava))
    ex.append(ball(vc + Vector((0.03, -0.01, 0.33)), 0.03, hot))
    for x, y in ((-0.05, -0.1), (0.06, -0.07)):
        ex.append(box(vc + Vector((x, y * 0.55, 0.1)), (0.03, 0.02, 0.17), lava,
                      rot=(math.radians(-30), math.radians(x * 150), 0)))
    # Lava drips from the chin, the belly and the free arm.
    for p, L in ((l.mouth + Vector((-0.04, 0.03, -0.03)), 0.12), (l.mouth + Vector((0.05, 0.03, -0.02)), 0.08),
                 (Vector((-0.2, front_y(parts['Torso'], 0.4, x=-0.2) + 0.02, 0.4)), 0.12),
                 (Vector((0.18, front_y(parts['Torso'], 0.5, x=0.18) + 0.02, 0.5)), 0.1)):
        ex.append(ball(p + Vector((0, 0, -L / 2)), 1, None, scale=(0.028, 0.028, L / 2),
                       fn=lambda q, n, i, top_z=p.z, L=L: mix(lava, hot, max(0, min(1, (top_z - q.z) / L)))))
        ex.append(ball(p + Vector((0, 0, -L)), 0.035, hot))
    # Lava pool under the feet with crusted rocks, a few glowing embers around it.
    ex.append(prim("cyl", (0, 0.05, -0.01), color=lava, vertices=12, radius=0.66, depth=0.04, scale=(1, 0.9, 1)))
    ex.append(prim("cyl", (0, 0.05, 0.0), color=hot, vertices=12, radius=0.4, depth=0.045, scale=(1, 0.9, 1)))
    rng = random.Random(22)
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-0.2, 0.2)
        r = rng.uniform(0.55, 0.7)
        ex.append(prim("ico", (math.cos(a) * r, 0.05 + math.sin(a) * r * 0.9, 0.02), color=crust, subdivisions=1,
                       radius=rng.uniform(0.06, 0.1), scale=(1, 1, 0.6)))
    return cols, ex, {"ThrowArm": arm_cracks}

def mecha(parts, hs):
    l = landmarks(parts); ex = []
    white, grey, blue, red, yellow = srgb(236, 240, 246), srgb(70, 76, 90), srgb(40, 85, 210), srgb(215, 40, 45), \
        srgb(255, 200, 40)
    glow = srgb(80, 250, 255)
    cols = recolor(srgb(92, 98, 112), srgb(170, 176, 188), srgb(30, 32, 40))
    arm = []
    # Helmet: blue dome, white face guard sides, armoured ears, a gold V-fin, a dark visor with glowing eyes.
    top = l.skull_top - 0.05
    ex.append(prim("ico", (0, l.head_c.y + 0.02, top), color=blue, subdivisions=1, radius=1,
                   scale=(0.26, 0.28, 0.19)))
    ex.append(box((0, l.head_c.y + 0.02, top + 0.12), (0.06, 0.4, 0.1), white))
    rim_z = l.eye_z + 0.07
    cy, rx, ry = head_section(l, rim_z)
    ex.append(ring((0, cy, rim_z), rx + 0.02, 0.03, white, scale=(1, (ry + 0.02) / (rx + 0.02), 1), segments=16))
    for s in (-1, 1):
        ex.append(box((s * (rx + 0.01), cy + 0.03, l.eye_z - 0.04), (0.06, 0.24, 0.2), white))
        ex.append(box((s * (rx + 0.045), cy + 0.03, l.eye_z - 0.04), (0.02, 0.12, 0.08), red))
        # Ear armour: a pointed blue plate over each ear.
        ear = [v for v in l.head_verts if s * v.x > 0.08]
        tip = max(ear, key=lambda v: v.z)
        ex.append(spike(tip + Vector((-s * 0.02, 0.01, -0.17)), (s * 0.05, 0, 1), 0.22, 0.085, blue, verts=4))
        ex.append(spike((s * 0.03, face_y(l, s * 0.03, rim_z + 0.03) - 0.02, rim_z + 0.03), (s * 0.9, -0.1, 0.8), 0.24,
                        0.025, yellow, verts=4))
    ex.append(box((0, face_y(l, 0, rim_z + 0.03) - 0.025, rim_z + 0.03), (0.07, 0.03, 0.06), red))
    vz = l.eye_z - 0.005
    vy = min(face_y(l, l.eye_x, vz), face_y(l, -l.eye_x, vz)) - 0.03
    ex.append(box((0, vy, vz), (0.4, 0.035, 0.075), grey))
    for s in (-1, 1):
        ex.append(box((s * l.eye_x, vy - 0.02, vz), (0.085, 0.012, 0.03), glow, rot=(0, s * math.radians(-12), 0)))
    # Chest: blue plate with yellow vents and a glowing core, white ab plates, a red belt.
    cz = l.neck_z - 0.17
    ty = front_y(parts['Torso'], cz)
    ex.append(box((0, ty - 0.01, cz), (0.5, 0.08, 0.26), blue))
    for s in (-1, 1):
        for k in range(3):
            ex.append(box((s * 0.16, ty - 0.055, cz + 0.06 - k * 0.04), (0.1, 0.01, 0.02), yellow))
    ex.append(prim("cyl", (0, ty - 0.06, cz - 0.01), (math.radians(90), 0, 0), color=white, vertices=8, radius=0.075,
                   depth=0.03))
    ex.append(prim("cyl", (0, ty - 0.075, cz - 0.01), (math.radians(90), 0, 0), color=glow, vertices=8, radius=0.05,
                   depth=0.02))
    for row in range(2):
        z = cz - 0.2 - row * 0.09
        for s in (-1, 1):
            ex.append(box((s * 0.07, front_y(parts['Torso'], z, x=s * 0.07) - 0.01, z), (0.12, 0.04, 0.075), white))
    ex.append(ring((0, (l.torso_min.y + l.torso_max.y) / 2, l.torso_min.z + 0.17), 0.37, 0.04, red,
                   scale=(1, 0.85, 1), segments=16))
    # Boots.
    for n in ("LeftLeg", "RightLeg"):
        mn, mx = wb(parts[n])
        ex.append(box(((mn.x + mx.x) / 2, mn.y + 0.06, 0.07), (0.2, 0.12, 0.1), red))
        ex.append(box(((mn.x + mx.x) / 2, mn.y + 0.035, 0.14), (0.14, 0.05, 0.04), yellow))
    # Huge shoulder pauldrons (the throwing side's rides on the arm).
    for s, target in ((-1, ex), (1, arm)):
        up_min, up_max = wb(parts["LeftUpperArm" if s < 0 else "RightUpperArm"])
        c = Vector(((up_min.x + up_max.x) / 2 + s * 0.06, (up_min.y + up_max.y) / 2, up_max.z + 0.01))
        rot = (0, s * math.radians(22), 0)
        target.append(box(c, (0.26, 0.34, 0.12), blue, rot=rot))
        target.append(box(c + Vector((s * 0.02, 0, 0.07)), (0.2, 0.28, 0.05), white, rot=rot))
        target.append(box(c + Vector((s * 0.13, 0, -0.07)), (0.04, 0.3, 0.18), blue, rot=rot))
        target.append(box(c + Vector((s * 0.155, 0, -0.07)), (0.01, 0.2, 0.05), yellow, rot=rot))
        mn, mx = wb(parts["LeftLowerArm" if s < 0 else "RightLowerArm"])
        target.append(box(((mn.x + mx.x) / 2 + s * 0.02, mn.y + 0.07, (mn.z + mx.z) / 2), (0.17, 0.1, 0.2), white,
                          rot=(math.radians(-15), 0, 0)))
    # Jet pack: a white back unit, two thrusters with glowing exhaust, two blue fins.
    bz = l.shoulder_z - 0.12
    by = l.back_y + 0.06
    ex.append(box((0, by + 0.04, bz), (0.42, 0.18, 0.42), white))
    ex.append(box((0, by + 0.135, bz + 0.02), (0.2, 0.02, 0.3), blue))
    for s in (-1, 1):
        tc = Vector((s * 0.29, by + 0.1, bz - 0.05))
        ex.append(prim("cyl", tc, color=grey, vertices=10, radius=0.085, depth=0.4))
        ex.append(ring(tc + Vector((0, 0, 0.12)), 0.088, 0.018, red, segments=12))
        ex.append(prim("cone", tc + Vector((0, 0, -0.25)), color=grey, vertices=10, radius1=0.11, radius2=0.075,
                       depth=0.1))
        ex.append(spike(tc + Vector((0, 0, -0.3)), (0, 0.15, -1), 0.3, 0.085, glow, verts=8, tip=srgb(255, 255, 255)))
        ex.append(box(tc + Vector((s * 0.2, 0.06, 0.22)), (0.32, 0.03, 0.14), blue,
                      rot=(0, s * math.radians(-35), s * math.radians(-15))))
    return cols, ex, {"ThrowArm": arm}

def angel(parts, hs):
    l = landmarks(parts); ex = []
    white, pearl, gold, gold2 = srgb(255, 255, 255), srgb(238, 240, 250), srgb(255, 200, 50), srgb(255, 235, 150)
    sky = srgb(190, 225, 255)
    cols = recolor(srgb(252, 246, 236), white, srgb(70, 55, 40))
    # Floating golden halo, a laurel wreath round the head.
    ex.append(ring((0, l.head_c.y + 0.06, l.skull_top + 0.2), 0.2, 0.035, gold2, rot=(math.radians(-12), 0, 0),
                   segments=20))
    lz = l.skull_top - 0.06
    cy, rx, ry = head_section(l, lz)
    ex.append(ring((0, cy, lz), rx + 0.01, 0.015, gold, scale=(1, (ry + 0.01) / (rx + 0.01), 1), segments=18))
    for k in range(14):
        a = k * math.tau / 14
        if -2.1 < math.atan2(math.sin(a), math.cos(a)) < -1.05:
            continue  # leaves open over the forehead
        p = Vector((math.cos(a) * (rx + 0.02), cy + math.sin(a) * (ry + 0.02), lz + 0.015))
        ex.append(ball(p, 0.045, gold, scale=(1, 0.45, 0.45), rot=(0, math.radians(-30), a + math.radians(90))))
    # White robe with a gold sash and hem.
    lo, hi = l.torso_min.z + 0.05, l.neck_z - 0.02
    ex.append(shell(parts['Torso'], lambda c, nrm: lo < c.z < hi and nrm.y < 0.3, 0.012, lambda p, n, i: pearl))
    ez = l.neck_z - 0.28
    for k in range(9):
        t = -1 + k / 4
        z = ez + 0.18 * t
        x = 0.2 * t
        ex.append(box((x, front_y(parts['Torso'], z, x=x) - 0.012, z), (0.07, 0.02, 0.075), gold,
                      rot=(0, math.radians(-42), 0)))
    ex.append(ring((0, (l.torso_min.y + l.torso_max.y) / 2, l.torso_min.z + 0.08), 0.395, 0.03, gold,
                   scale=(1, 0.9, 1), segments=18))
    ex.append(ring((0, l.head_c.y + 0.06, l.neck_z), 0.24, 0.03, gold, rot=(math.radians(-18), 0, 0), segments=16))
    # Big spread feathered wings: white with golden tips.
    for s in (-1, 1):
        root = Vector((s * 0.14, l.back_y + 0.05, l.shoulder_z + 0.02))
        ex += feather_wing(root, s, 1.05, 0.85, 0.25, 9, 0.62, [white, pearl, srgb(255, 244, 214)], gold2, fw=0.13)
    # Golden trumpet in the free paw, a little cloud under the feet.
    a = l.left_hand + Vector((-0.02, -0.06, 0.08))
    b = a + Vector((-0.12, -0.12, 0.3))
    ex.append(rod(a, b, 0.02, gold, verts=6))
    ex.append(prim("cone", b + (b - a).normalized() * 0.05, tilt(b - a), color=gold2, vertices=10, radius1=0.02,
                   radius2=0.08, depth=0.1))
    rng = random.Random(25)
    for k in range(9):
        a2 = k * math.tau / 9 + rng.uniform(-0.2, 0.2); r = rng.uniform(0.25, 0.55)
        ex.append(prim("ico", (math.cos(a2) * r, 0.05 + math.sin(a2) * r * 0.8, -0.1), color=white, subdivisions=1,
                       radius=rng.uniform(0.12, 0.17), scale=(1.3, 1, 0.75)))
    return cols, ex

def demon(parts, hs):
    l = landmarks(parts); ex = []
    red, belly, black = srgb(135, 18, 25), srgb(70, 14, 20), srgb(15, 10, 12)
    bone, horn_tip = srgb(235, 215, 180), srgb(40, 25, 25)
    fire = [srgb(200, 20, 10), srgb(255, 110, 20), srgb(255, 220, 80)]
    cols = recolor(red, belly, black)
    ex += lit_eyes(l, srgb(255, 200, 40), None, size=(0.065, 0.022, 0.03), angle=-18)
    # Angry brows.
    for s in (-1, 1):
        x = s * (l.eye_x - 0.005)
        ex.append(box((x, face_y(l, x, l.eye_z + 0.045) - 0.01, l.eye_z + 0.045), (0.08, 0.02, 0.02), black,
                      rot=(0, s * math.radians(20), 0)))
    # Big curved horns: out from the forehead, up, back and hooking forward at the tip.
    top = l.skull_top - 0.08
    for s in (-1, 1):
        base = Vector((s * 0.13, l.head_c.y - 0.03, top))
        pts = [base, base + Vector((s * 0.12, 0.0, 0.1)), base + Vector((s * 0.22, 0.05, 0.25)),
               base + Vector((s * 0.26, 0.1, 0.42)), base + Vector((s * 0.22, 0.08, 0.56)),
               base + Vector((s * 0.14, 0.0, 0.64))]
        radii = [0.07, 0.065, 0.055, 0.042, 0.026, 0]
        n = len(pts)
        ex.append(curve_tube("horn", pts, radii, 7, lambda k, j, c, n=n: mix(bone, horn_tip, max(0, k) / (n - 2))))
        ex.append(ring(base + Vector((s * 0.03, 0, 0.03)), 0.07, 0.018, srgb(255, 170, 40), rot=(0, s * 0.6, 0),
                       segments=10))
    # Bat wings on the back.
    for s in (-1, 1):
        root = Vector((s * 0.12, l.back_y + 0.04, l.shoulder_z + 0.02))
        ex += bat_wing(root, s, 1.25, srgb(40, 20, 22), srgb(110, 15, 30), srgb(85, 10, 25))
    # Spiked tail with a spade tip, spikes down the spine.
    tip = l.tail_tip
    ex.append(prim("cone", tip + Vector((0, 0.02, 0.07)), (math.radians(-15), 0, 0), color=black, vertices=3,
                   radius1=0.11, radius2=0, depth=0.18, scale=(1, 0.35, 1)))
    for k in range(5):
        z = l.skull_top - 0.2 - k * 0.12
        y = l.back_y + 0.02 if k else l.head_max.y
        ex.append(spike((0, y - 0.03, z), (0, 1, 0.3), 0.1, 0.035, black, verts=4))
    # Flames: a ring of fire round the feet, small flames on the shoulders.
    rng = random.Random(26)

    def flame(base, h, r, lean=(0, 0, 1)):
        """A teardrop flame: a red-orange bulb with a tongue rising to a yellow tip, a smaller yellow core in front."""
        base = Vector(base); d = Vector(lean).normalized()
        grad = lambda p, n, i: mix(fire[0], fire[1], max(0.0, min(1.0, (p.z - base.z) / (h * 0.5))))
        out = [ball(base + Vector((0, 0, r * 0.7)), 1, None, scale=(r, r, r * 0.9), fn=grad)]
        out.append(spike(base + Vector((0, 0, r * 0.9)), d, h - r * 0.9, r * 0.85, fire[1], verts=5, tip=fire[2]))
        out.append(spike(base + Vector((0, -r * 0.55, r * 0.4)), d, h * 0.55, r * 0.5, fire[2], verts=4,
                         tip=srgb(255, 250, 200)))
        return out
    for k in range(11):
        a = k * math.tau / 11 + rng.uniform(-0.15, 0.15)
        r = rng.uniform(0.5, 0.6)
        base = Vector((math.cos(a) * r, 0.05 + math.sin(a) * r * 0.85, -0.02))
        ex += flame(base, rng.uniform(0.36, 0.56), rng.uniform(0.09, 0.125),
                    (0.25 * math.cos(a) + rng.uniform(-0.2, 0.2), 0.25 * math.sin(a), 1))
    ex += flame((-0.3, 0.02, l.shoulder_z + 0.04), 0.22, 0.055, (-0.3, 0.2, 1))  # on the free shoulder
    ex.append(prim("cyl", (0, 0.05, -0.01), color=srgb(60, 10, 10), vertices=12, radius=0.6, depth=0.025,
                   scale=(1, 0.88, 1)))
    # Trident in the free paw.
    a = l.left_hand + Vector((-0.05, -0.05, -0.05))
    t = a + Vector((-0.08, 0, 1.0))
    ex.append(rod(a, t, 0.018, srgb(40, 35, 40), verts=6))
    ex.append(rod(t + Vector((-0.1, 0, 0)), t + Vector((0.1, 0, 0)), 0.02, srgb(40, 35, 40), verts=6))
    for x in (-0.1, 0, 0.1):
        ex.append(spike(t + Vector((x, 0, 0)), (x * 0.5, 0, 1), 0.16 if x == 0 else 0.12, 0.025, fire[0], verts=4,
                        tip=fire[2]))
    return cols, ex

# EternalShiba's Orbit: a tilted golden ring with gems around the body; the game spins it about the vertical axis, so
# the tilted ring wobbles like an armillary sphere. VoidShiba's: void shards on a tilted circle.
ETERNAL_ORBIT = dict(radius=0.86, tilt=25, lift=0.62)
VOID_ORBIT = dict(radius=1.4, axis=(0.0, -0.2, 1.0), lift=0.8)

def eternal(parts, hs):
    l = landmarks(parts); ex = []
    rng = random.Random(29)
    white, pearl, gold, gold2, deep = srgb(255, 255, 255), srgb(255, 248, 228), srgb(255, 196, 40), \
        srgb(255, 232, 140), srgb(205, 140, 20)
    cyan, glass = srgb(120, 240, 255), srgb(200, 245, 255)
    span = l.max_z - l.min_z
    # Star-white fur with a golden shimmer (gold toward the paws), pure white cream fur.
    shimmer = lambda p: mix(srgb(255, 252, 244), srgb(255, 226, 150), 0.5 + 0.5 * math.sin(p.x * 9 + p.z * 7 + p.y * 5))
    cols = {"fur_orange": lambda p: mix(gold, shimmer(p), min(1.0, (p.z - l.min_z) / span * 3.0)),
            "fur_cream": lambda p: white, "fur_dark": lambda p: deep}
    ex += lit_eyes(l, srgb(255, 230, 120), white)
    head = parts['Head']
    face = lambda c: c.y < l.eye_y + 0.08 and l.mouth.z - 0.06 < c.z < l.eye_z + 0.07 and abs(c.x) < 0.24
    keep = lambda o, c, nrm, mat: mat != "fur_dark" and nrm.z > -0.5 and not (o is head and face(c))
    armp = [parts[n] for n in ARM_NAMES]
    samples = surface_samples(list(parts.values()), 140, rng, keep, 0.07)
    ex.append(star_specks([s for s in samples if s[0] not in armp], rng, "EternalStars"))
    arm_stars = star_specks([s for s in samples if s[0] in armp], rng, "EternalArmStars")
    # Crown: gold circlet with rays of light and a cyan gem.
    top = l.skull_top - 0.05
    cy, rx, ry = head_section(l, top)
    ex.append(ring((0, cy, top), rx + 0.01, 0.03, gold, scale=(1, (ry + 0.01) / (rx + 0.01), 1), segments=18))
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 22)
        base = Vector((math.cos(a) * (rx + 0.01), cy + math.sin(a) * (ry + 0.01), top + 0.01))
        ex.append(spike(base, (math.cos(a) * 0.3, math.sin(a) * 0.3, 1), 0.24 - abs(k - 4) * 0.03, 0.03, gold,
                        verts=4, tip=white))
    ex.append(prim("ico", (0, cy - ry - 0.02, top + 0.03), color=cyan, subdivisions=1, radius=0.045,
                   scale=(0.8, 0.6, 1.2)))
    # Giant clock halo behind: thick gold ring, white dial band, twelve hour marks, runes, two hands, a ray corona.
    hc = Vector((0, l.back_y + 0.32, l.eye_z + 0.12))
    R = 1.02
    face_rot = (math.radians(90), 0, 0)
    ex.append(ring(hc, R, 0.06, gold, rot=face_rot, segments=48))
    # The dial behind everything: deep night blue with golden and white stars, so the white dog stands out.
    night = srgb(22, 34, 95)
    ex.append(prim("cyl", hc + Vector((0, 0.05, 0)), face_rot, color=night, vertices=32, radius=R - 0.02, depth=0.03))
    for k in range(26):
        a = rng.uniform(0, math.tau); r = math.sqrt(rng.uniform(0.08, 1)) * (R - 0.1)
        ex.append(prim("ico", hc + Vector((math.cos(a) * r, 0.03, math.sin(a) * r)), color=rng.choice([white, gold2]),
                       subdivisions=1, radius=rng.uniform(0.015, 0.03)))
    ex.append(ring(hc, R - 0.24, 0.035, gold2, rot=face_rot, segments=40))
    ex.append(ring(hc, R * 0.5, 0.03, gold, rot=face_rot, segments=32))
    right, up = Vector((1, 0, 0)), Vector((0, 0, 1))
    for k in range(12):
        a = k * math.tau / 12
        d = Vector((math.sin(a), 0, math.cos(a)))
        major = k % 3 == 0
        ex.append(box(hc + d * (R - 0.12), (0.05 if major else 0.035, 0.05, 0.2 if major else 0.13), gold,
                      rot=(0, a, 0)))
        if major:
            ex.append(prim("ico", hc + d * (R + 0.02) + Vector((0, -0.07, 0)), color=cyan, subdivisions=1, radius=0.06))
        ga = a + math.tau / 24
        gd = Vector((math.sin(ga), 0, math.cos(ga)))
        ex += glyph(hc + gd * (R - 0.12) + Vector((0, -0.03, 0)), (math.cos(ga), 0, -math.sin(ga)), gd, 0.07, cyan, rng)
    for k in range(24):
        a = (k + 0.5) * math.tau / 24
        d = Vector((math.sin(a), 0, math.cos(a)))
        ex.append(spike(hc + d * (R + 0.05), d, 0.2 if k % 2 else 0.34, 0.035, gold, verts=4, tip=white))
    for a, L, w in ((math.radians(-60), 0.95, 0.05), (math.radians(35), 0.7, 0.07)):
        d = Vector((math.sin(a), 0, math.cos(a)))
        c = hc + Vector((0, -0.04, 0))
        ex.append(box(c + d * L / 2, (w, 0.03, L), deep, rot=(0, a, 0)))
        ex.append(spike(c + d * L, d, 0.12, w * 1.4, deep, verts=4))
    # Three pairs of golden-white feathered wings between the dog and the clock.
    for s in (-1, 1):
        for k, (rise, span_, n, L) in enumerate(((0.75, 1.0, 7, 0.55), (0.2, 1.15, 7, 0.55), (-0.3, 0.9, 6, 0.45))):
            root = Vector((s * 0.12, l.back_y + 0.08 + 0.02 * k, l.shoulder_z + 0.05 - 0.12 * k))
            ex += feather_wing(root, s, span_, rise, 0.18, n, L, [white, pearl], gold2, rows=2)
    # Standing on a floating clock face: white dial, gold rim, hour marks, hands pointing forward.
    dz = -0.05
    ex.append(prim("cyl", (0, 0.05, dz), color=pearl, vertices=24, radius=0.78, depth=0.06))
    ex.append(ring((0, 0.05, dz + 0.02), 0.78, 0.04, gold, segments=32))
    ex.append(prim("cone", (0, 0.05, dz - 0.12), (math.pi, 0, 0), color=gold, vertices=24, radius1=0.76,
                   radius2=0.25, depth=0.18))
    for k in range(12):
        a = k * math.tau / 12
        ex.append(box((math.sin(a) * 0.66, 0.05 - math.cos(a) * 0.66, dz + 0.035), (0.04, 0.12 if k % 3 == 0 else 0.07,
                      0.02), gold, rot=(0, 0, -a)))
    ex.append(box((0.18, -0.28, dz + 0.04), (0.035, 0.34, 0.015), deep, rot=(0, 0, math.radians(-20))))
    # A golden hourglass in the free paw.
    hg = l.left_hand + Vector((-0.02, -0.08, 0.14))
    ex.append(prim("cyl", hg + Vector((0, 0, 0.13)), color=gold, vertices=8, radius=0.07, depth=0.025))
    ex.append(prim("cyl", hg + Vector((0, 0, -0.13)), color=gold, vertices=8, radius=0.07, depth=0.025))
    ex.append(prim("cone", hg + Vector((0, 0, 0.06)), (math.pi, 0, 0), color=glass, vertices=8, radius1=0.055,
                   radius2=0.008, depth=0.12))
    ex.append(prim("cone", hg + Vector((0, 0, -0.06)), color=gold2, vertices=8, radius1=0.055, radius2=0.008,
                   depth=0.12))
    for s in (-1, 1):
        ex.append(rod(hg + Vector((s * 0.06, 0, -0.13)), hg + Vector((s * 0.06, 0, 0.13)), 0.008, gold, verts=4))
    # Static glowing ring crossing the orbit, and floating diamond sparkles.
    cen = Vector((0, 0.05, ETERNAL_ORBIT["lift"]))
    ex.append(ring((0, 0.05, 0.2), 1.0, 0.018, cyan, rot=(math.radians(-6), math.radians(8), 0), segments=40))
    for k in range(14):
        a = rng.uniform(0, math.tau); r = rng.uniform(0.9, 1.25)
        p = Vector((math.cos(a) * r, 0.1 + math.sin(a) * r * 0.6, rng.uniform(0.1, 1.9)))
        ex.append(prim("ico", p, color=rng.choice([white, gold2, cyan]), subdivisions=1, radius=rng.uniform(0.025, 0.045),
                       scale=(0.6, 0.6, 1.5)))
    # Orbit: a tilted golden ring carrying four gems and two small clock dials.
    tilt_r = math.radians(ETERNAL_ORBIT["tilt"])
    Rr = ETERNAL_ORBIT["radius"]
    e1 = Vector((1, 0, 0)); e2 = Vector((0, math.cos(tilt_r), math.sin(tilt_r)))
    on = lambda a: cen + (e1 * math.cos(a) + e2 * math.sin(a)) * Rr
    orbit = [ring(cen, Rr, 0.022, gold, rot=(tilt_r, 0, 0), segments=48)]
    for k in range(4):
        a = k * math.tau / 4 + 0.4
        orbit.append(prim("ico", on(a), color=cyan if k % 2 else white, subdivisions=1, radius=0.065,
                          scale=(0.8, 0.8, 1.3)))
        b = a + math.tau / 8
        orbit.append(prim("cyl", on(b), (math.radians(90), 0, b), color=pearl, vertices=12, radius=0.07, depth=0.02))
        orbit.append(ring(on(b), 0.07, 0.012, gold, rot=(math.radians(90), 0, b), segments=12))
    marker = box(cen, (0.02, 0.02, 0.02), srgb(255, 0, 255))
    return cols, ex, {"ThrowArm": [arm_stars], "Orbit": orbit, "OrbitCenter": [marker]}

def void(parts, hs):
    l = landmarks(parts); ex = []
    rng = random.Random(30)
    black, ink, purple, cyan, magenta = srgb(10, 8, 18), srgb(22, 16, 36), srgb(170, 70, 255), srgb(70, 235, 255), \
        srgb(255, 70, 220)
    white = srgb(255, 255, 255)
    rock = lambda c: ink if (int(c.x * 12 + 50) + int(c.z * 12)) % 4 == 0 else black
    cols = vein_paint(parts, rock, purple, cyan, 0.17, freq=1.15)
    ex += lit_eyes(l, cyan, white, size=(0.07, 0.024, 0.04))
    # Glowing purple/cyan zigzag cracks over the black fur (not on the face); the arm's swing with the arm.
    head = parts['Head']
    face = lambda c: c.y < l.eye_y + 0.08 and l.mouth.z - 0.06 < c.z < l.eye_z + 0.07 and abs(c.x) < 0.24
    keep = lambda o, c, nrm, mat: mat != "fur_dark" and nrm.z > -0.4 and not (o is head and face(c))
    armp = [parts[n] for n in ARM_NAMES]
    samples = surface_samples(list(parts.values()), 30, rng, keep, 0.15)
    ex += crack_lines([s for s in samples if s[0] not in armp], rng, [purple, cyan, magenta], segs=5)
    arm_cracks = crack_lines([s for s in samples if s[0] in armp], rng, [purple, cyan, magenta], segs=5)
    # Third eye on the forehead.
    fz = l.eye_z + 0.1
    fy = face_y(l, 0, fz)
    ex.append(ball((0, fy - 0.005, fz), 1, magenta, scale=(0.035, 0.02, 0.06)))
    ex.append(ball((0, fy - 0.02, fz), 1, white, scale=(0.012, 0.01, 0.03)))
    # Crown of dark crystal: faceted black/purple spikes with glowing tips.
    top = l.skull_top - 0.05
    cy, rx, ry = head_section(l, top)
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 24)
        base = Vector((math.cos(a) * rx * 0.9, cy + math.sin(a) * ry * 0.9, top))
        h = 0.42 - abs(k - 4) * 0.07
        ex.append(spike(base, (math.cos(a) * 0.35, math.sin(a) * 0.35, 1), h, 0.05, black, verts=4,
                        tip=magenta if k % 2 else purple))
    # Black hole behind the head: a black sphere, a white-hot photon ring, a purple lensing ring, sigils and eyes.
    bh = Vector((0, l.back_y + 0.38, l.eye_z + 0.28))
    face_rot = (math.radians(90), 0, 0)
    ex.append(prim("uv", bh, color=srgb(2, 1, 5), segments=20, ring_count=12, radius=0.44))
    ex.append(ring(bh + Vector((0, -0.02, 0)), 0.47, 0.045, white, rot=face_rot, segments=40))
    ex.append(ring(bh + Vector((0, -0.01, 0)), 0.56, 0.03, cyan, rot=face_rot, segments=40))
    ex.append(ring(bh, 0.74, 0.04, purple, rot=face_rot, segments=48))
    for k in range(10):
        a = k * math.tau / 10
        d = Vector((math.cos(a), 0, math.sin(a)))
        p = bh + d * 0.65 + Vector((0, -0.05, 0))
        if k % 2:
            ex += glyph(p, (-math.sin(a), 0, math.cos(a)), d, 0.07, magenta, rng)
        else:
            ex.append(ball(p, 1, white, scale=(0.085, 0.025, 0.05), rot=(0, -a, 0)))
            ex.append(ball(p + Vector((0, -0.02, 0)), 1, magenta, scale=(0.035, 0.015, 0.035)))
            ex.append(ball(p + Vector((0, -0.03, 0)), 1, black, scale=(0.012, 0.01, 0.03), rot=(0, -a, 0)))
        ex.append(spike(bh + d * 0.77, d, 0.3 if k % 2 else 0.18, 0.04, purple, verts=4, tip=cyan))
    # Accretion disk (event horizon ring) around the body: white-hot inside, cyan, purple, fading dark outside.
    ring_c = Vector((0, 0.05, 0.6))
    stops = [(0.0, white), (0.2, cyan), (0.55, purple), (1.0, srgb(55, 15, 110))]
    grad = lambda t: next(mix(c0, c1, (t - t0) / (t1 - t0)) for (t0, c0), (t1, c1) in zip(stops, stops[1:]) if t <= t1)
    r_in, r_out, n_seg, n_ring = 0.8, 1.3, 40, 3
    dtilt = Matrix.Rotation(math.radians(22), 3, 'X')
    verts, faces, fc = [], [], []
    for r in range(n_ring + 1):
        rad = r_in + (r_out - r_in) * r / n_ring
        for k in range(n_seg):
            a = k * math.tau / n_seg
            verts.append(ring_c + dtilt @ Vector((math.cos(a) * rad, math.sin(a) * rad, 0.03 * math.sin(3 * a) * r)))
    for r in range(n_ring):
        for k in range(n_seg):
            kn = (k + 1) % n_seg
            faces.append([r * n_seg + k, r * n_seg + kn, (r + 1) * n_seg + kn, (r + 1) * n_seg + k])
            t = (r + 0.5) / n_ring
            fc.append(mix(grad(t), white, 0.25) if (k + r) % 5 == 0 else grad(t))
    ex.append(mesh_obj("disk", verts, faces, fc, double=True))
    ex.append(ring(ring_c, r_in, 0.035, white, rot=(math.radians(22), 0, 0), segments=40))
    # Void tentacles: tapering ribbons curling out of the back, black to purple with glowing cyan tips.
    for k, (s, rise, reach, curl) in enumerate(((-1, 0.9, 0.9, 1), (1, 0.9, 0.85, -1), (-1, 0.3, 1.1, -1),
                                                (1, 0.35, 1.05, 1), (-1, -0.25, 0.95, 1), (1, -0.2, 0.9, -1))):
        root = Vector((s * 0.2, l.back_y - 0.02, l.shoulder_z - 0.05 - 0.14 * (k // 2)))
        pts = []
        for i in range(10):
            t = i / 9
            pts.append(root + Vector((s * reach * 1.1 * t, 0.15 * math.sin(t * 3) - 0.1 * t, rise * t
                                      + curl * 0.2 * math.sin(t * math.pi * 1.6))))
        radii = [0.095 * (1 - t / 11) for t in range(9)] + [0]
        ex.append(curve_tube("tentacle", pts, radii, 6,
                             lambda kk, j, c: cyan if kk >= 7 else (purple if (kk + j) % 3 == 0 or kk >= 5 else black)))
        ex.append(ball(pts[-2], 0.045, magenta))
    # Orbit: floating void shards (faceted black/purple crystals) on a tilted circle around the body.
    axis = Vector(VOID_ORBIT["axis"]).normalized()
    cen = Vector((0, 0.05, VOID_ORBIT["lift"]))
    rot = tilt(axis).to_matrix()
    e1 = rot @ Vector((1, 0, 0)); e2 = axis.cross(e1)
    on = lambda a: cen + (e1 * math.cos(a) + e2 * math.sin(a)) * VOID_ORBIT["radius"]
    orbit = []
    for k in range(7):
        a = k * math.tau / 7
        p = on(a); h = 0.2 + 0.08 * (k % 3)
        d = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 1)).normalized()
        cs = [black, purple if k % 2 else cyan]
        orbit.append(prim("cone", p + d * h / 2, tilt(d), fn=lambda q, n, i, cs=cs: cs[i % 2], vertices=4,
                          radius1=0.085, radius2=0, depth=h))
        orbit.append(prim("cone", p - d * h / 3, tilt(-d), fn=lambda q, n, i, cs=cs: cs[(i + 1) % 2], vertices=4,
                          radius1=0.085, radius2=0, depth=h * 0.66))
    marker = box(cen, (0.02, 0.02, 0.02), srgb(255, 0, 255))
    return cols, ex, {"ThrowArm": arm_cracks, "Orbit": orbit, "OrbitCenter": [marker]}

THIRD_DESIGNS = [("DJShiba", dj), ("KnightShiba", knight), ("SuperheroShiba", superhero), ("FrostShiba", frost),
                 ("MagmaShiba", magma), ("MechaShiba", mecha), ("AngelShiba", angel), ("DemonShiba", demon),
                 ("EternalShiba", eternal), ("VoidShiba", void)]

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
for asset, design in DESIGNS + NEW_DESIGNS + THIRD_DESIGNS:
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
xs = [(k - (len(built) - 1) / 2) * 1.45 for k in range(len(built))]
if ONLY:
    # Side by side by their real widths (wings, halos), so the big ones don't overlap their neighbours.
    spans = [(min(wb(o)[0].x for o in objs), max(wb(o)[1].x for o in objs)) for objs in built]
    widths = [max(1.2, b - a) + 0.2 for a, b in spans]
    total, x0 = sum(widths), -sum(widths) / 2
    xs = [x0 + sum(widths[:k]) + widths[k] / 2 - (spans[k][0] + spans[k][1]) / 2 for k in range(len(built))]
for k, objs in enumerate(built):
    for o in objs: o.location.x += xs[k]
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
if ONLY and total > 14:
    cam.location = Vector((0, -15.5 * total / 14, 3.2 + 0.6 * (total / 14 - 1)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "preview_only.png" if ONLY else "preview_tiers.png")
bpy.ops.render.render(write_still=True)
if ONLY:
    # Close-ups: each Shiba alone, turned three-quarters toward the camera (preview_<asset>.png).
    for k, objs in enumerate(built):
        for other in built:
            for o in other: o.hide_render = other is not objs
        bpy.context.view_layer.update()
        mn = Vector([min(wb(o)[0][i] for o in objs) for i in range(3)])
        mx = Vector([max(wb(o)[1][i] for o in objs) for i in range(3)])
        size = max(1.0, (mx.z - mn.z) / 1.4, (mx.x - mn.x) / 1.6)
        cam.data.lens = 50
        target = Vector((xs[k] if size == 1.0 else (mn.x + mx.x) / 2, 0, 0.62 if size == 1.0 else (mn.z + mx.z) / 2))
        cam.location = target + Vector((1.2, -2.6, 0.55)) * size
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
