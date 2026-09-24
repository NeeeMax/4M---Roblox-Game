import bpy, math, sys, os, random
from mathutils import Vector, Matrix
# Shiba tiers 3-8 (LavaShiba ... GodShiba) and projectile tiers 2-4 (Bone, GoldenStick, DiamondStick), built from
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
wood = srgb(110, 62, 30)
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

# --- Landmarks (the dog faces -Y, Z is up) ---
head = bpy.data.objects['Head']; torso = bpy.data.objects['Torso']; tail = bpy.data.objects['Tail']
head_min, head_max = wb(head); torso_min, torso_max = wb(torso)
dog_min_z = min(wb(o)[0].z for o in dog); dog_max_z = max(wb(o)[1].z for o in dog)
hv = [head.matrix_world @ v.co for v in head.data.vertices]
skull_top = max(p.z for p in hv if abs(p.x) < 0.06)
head_c = Vector(((head_min.x + head_max.x) / 2, (head_min.y + head_max.y) / 2, (head_min.z + head_max.z) / 2))
dark = []
for poly in head.data.polygons:
    if head.data.materials[poly.material_index].name == 'fur_dark':
        cen = head.matrix_world @ poly.center
        if abs(cen.x) > 0.05: dark.append(cen)
# The eyes are the upper half of the dark faces off the centre line (the mouth line sits lower).
dark.sort(key=lambda p: p.z)
eyes = dark[len(dark) // 2:]
eye_z = sum(p.z for p in eyes) / len(eyes); eye_y = min(p.y for p in eyes)
tv = [tail.matrix_world @ v.co for v in tail.data.vertices]
tail_tip = max(tv, key=lambda p: p.z)
back_y = torso_max.y; shoulder_z = torso_max.z - 0.12

def height_t(p):
    return max(0.0, min(1.0, (p.z - dog_min_z) / (dog_max_z - dog_min_z)))

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

def spike(base, direction, length, radius, color, verts=4, tip=None):
    d = Vector(direction).normalized()
    loc = Vector(base) + d * length / 2
    fn = None
    if tip:
        fn = lambda p, n, i: mix(color, tip, max(0.0, min(1.0, (p - Vector(base)).dot(d) / length)))
    return prim("cone", loc, tilt(d), color=color, fn=fn, vertices=verts, radius1=radius, radius2=0, depth=length)

# --- The six Shiba designs ---
def lava():
    rock_top, rock_low = srgb(45, 16, 12), srgb(255, 80, 10)
    fur = lambda p: mix(rock_low, rock_top, min(1.0, height_t(p) * 1.35) ** 0.8)
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(255, 185, 40), "fur_dark": lambda p: srgb(255, 235, 90)}
    extras = []
    for i, (x, h) in enumerate([(-0.1, 0.16), (0, 0.24), (0.1, 0.16), (-0.05, 0.12), (0.05, 0.12)]):
        base = (x, head_c.y + (0.05 if i > 2 else -0.02), skull_top - 0.03)
        extras.append(spike(base, (x * 0.8, 0.1, 1), h, 0.06, srgb(255, 90, 0), verts=6, tip=srgb(255, 230, 60)))
    for _ in range(7):
        a = random.uniform(0, math.tau); r = random.uniform(0.42, 0.55)
        extras.append(prim("ico", (math.cos(a) * r, math.sin(a) * r * 0.8, random.uniform(0.2, 0.95)),
                           color=srgb(255, random.randint(90, 170), 20), subdivisions=1, radius=random.uniform(0.025, 0.045)))
    return cols, extras

def ice():
    fur = lambda p: mix(srgb(120, 195, 250), srgb(225, 245, 255), height_t(p))
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(245, 252, 255), "fur_dark": lambda p: srgb(20, 60, 150)}
    extras = []
    for x, z, h in [(-0.09, 0.0, 0.18), (0.0, 0.03, 0.26), (0.09, 0.0, 0.18)]:
        extras.append(spike((x, head_c.y + 0.08, skull_top - 0.04 + z), (x, 0.35, 1), h, 0.05,
                            srgb(170, 235, 255), tip=srgb(240, 252, 255)))
    for i in range(4):
        z = shoulder_z - i * 0.13
        extras.append(spike((0, back_y - 0.06, z), (0, 1, 0.5), 0.2 - i * 0.03, 0.06, srgb(110, 190, 245),
                            tip=srgb(220, 248, 255)))
    for s in (-1, 1):
        extras.append(spike((s * 0.3, torso_min.y + 0.2, 0.08), (s, 0.2, 0.6), 0.14, 0.04, srgb(150, 225, 255)))
    return cols, extras

def robo():
    steel = srgb(150, 158, 172)
    fur = lambda p: mix(srgb(95, 102, 115), steel, height_t(p))
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(60, 66, 78), "fur_dark": lambda p: srgb(0, 240, 255)}
    extras = [
        prim("cube", (0, eye_y - 0.01, eye_z + 0.055), scale=(0.24, 0.025, 0.07), color=srgb(0, 225, 255), size=1),
        prim("cyl", (0.08, head_c.y + 0.02, skull_top + 0.1), color=srgb(70, 72, 82), vertices=6, radius=0.015, depth=0.22),
        prim("ico", (0.08, head_c.y + 0.02, skull_top + 0.22), color=srgb(255, 40, 40), subdivisions=1, radius=0.04),
        prim("cube", (0, torso_min.y - 0.005, 0.35), scale=(0.2, 0.02, 0.16), color=srgb(40, 46, 58), size=1),
        prim("cube", (0, torso_min.y - 0.02, 0.37), scale=(0.1, 0.01, 0.05), color=srgb(0, 255, 190), size=1),
    ]
    for s in (-1, 1):
        extras.append(prim("cyl", (s * (head_max.x - 0.01), head_c.y, head_c.z), rot=(0, math.radians(90), 0),
                           color=srgb(205, 208, 218), vertices=8, radius=0.07, depth=0.06))
    return cols, extras

def angel():
    fur = lambda p: mix(srgb(255, 238, 205), srgb(255, 252, 245), height_t(p))
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(255, 222, 140), "fur_dark": lambda p: srgb(40, 110, 210)}
    extras = [prim("torus", (0, head_c.y + 0.03, skull_top + 0.17), rot=(math.radians(12), 0, 0),
                   color=srgb(255, 215, 70), major_radius=0.2, minor_radius=0.025, major_segments=24, minor_segments=6)]
    for s in (-1, 1):
        for k, (length, lift) in enumerate([(0.55, 0.12), (0.45, 0.0), (0.34, -0.1)]):
            d = Vector((s, 0.45, 0.55 + lift)).normalized()
            base = Vector((s * 0.12, back_y - 0.05, shoulder_z - k * 0.07))
            extras.append(prim("uv", base + d * length / 2, tilt(d), scale=(0.07, 0.025, length / 2),
                               fn=lambda p, n, i: srgb(255, 255, 255) if p.y > back_y + 0.02 else srgb(225, 235, 255),
                               segments=10, ring_count=6, radius=1))
    return cols, extras

def demon():
    fur = lambda p: mix(srgb(150, 12, 30), srgb(70, 5, 18), height_t(p))
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(30, 12, 18), "fur_dark": lambda p: srgb(255, 215, 0)}
    black, red = srgb(25, 18, 22), srgb(220, 30, 40)
    extras = []
    for s in (-1, 1):
        base = Vector((s * 0.14, head_c.y + 0.02, skull_top - 0.03))
        d1 = Vector((s * 0.6, 0.15, 1)).normalized()
        extras.append(spike(base, d1, 0.14, 0.06, black, verts=6))
        extras.append(spike(base + d1 * 0.12, (s * 0.15, 0.1, 1), 0.14, 0.04, black, verts=6, tip=red))
        for k, (length, rise) in enumerate([(0.42, 0.7), (0.34, 0.25), (0.26, -0.2)]):
            d = Vector((s, 0.5, rise)).normalized()
            extras.append(spike((s * 0.1, back_y - 0.05, shoulder_z), d, length, 0.07, srgb(90, 0, 18),
                                verts=3, tip=srgb(40, 0, 10)))
    extras.append(spike(tail_tip - Vector((0, 0, 0.02)), (0, 0.3, 1), 0.12, 0.07, red, verts=4))
    return cols, extras

def god():
    fur = lambda p: mix(srgb(240, 170, 30), srgb(255, 232, 130), height_t(p))
    cols = {"fur_orange": fur, "fur_cream": lambda p: srgb(255, 250, 235), "fur_dark": lambda p: srgb(110, 235, 255)}
    gold = srgb(255, 195, 40)
    crown_z = skull_top + 0.02
    extras = [prim("cyl", (0, head_c.y, crown_z), color=gold, vertices=10, radius=0.17, depth=0.07)]
    gems = [srgb(255, 40, 60), srgb(40, 120, 255), srgb(40, 220, 90), srgb(40, 120, 255), srgb(255, 40, 60)]
    for k in range(5):
        a = math.radians(-90 + (k - 2) * 38)
        x, y = math.cos(a) * 0.16, head_c.y + math.sin(a) * 0.16
        extras.append(spike((x, y, crown_z + 0.03), (0, 0, 1), 0.13, 0.045, gold, verts=4, tip=srgb(255, 240, 150)))
        extras.append(prim("ico", (x * 1.08, y - 0.01, crown_z), color=gems[k], subdivisions=1, radius=0.03))
    sun = Vector((0, back_y + 0.05, head_c.z + 0.05))
    extras.append(prim("torus", sun, rot=(math.radians(90), 0, 0), color=srgb(255, 225, 110),
                       major_radius=0.42, minor_radius=0.025, major_segments=32, minor_segments=6))
    for k in range(12):
        a = k * math.tau / 12
        d = Vector((math.cos(a), 0, math.sin(a)))
        extras.append(spike(sun + d * 0.44, d, 0.14 if k % 2 else 0.22, 0.035, srgb(255, 215, 80), verts=4,
                            tip=srgb(255, 250, 200)))
    return cols, extras

DESIGNS = [("LavaShiba", lava), ("IceShiba", ice), ("RoboShiba", robo), ("AngelShiba", angel),
           ("DemonShiba", demon), ("GodShiba", god)]

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
    cols, extras = design()
    parts = []
    for o in dog:
        cp = o.copy(); cp.data = o.data.copy(); coll.objects.link(cp)
        paint(cp, lambda p, n, i: cols.get(n, lambda q: srgb(200, 200, 200))(p))
        parts.append(cp)
    body = join(parts + extras, f"{asset}_Body")
    hs = stick.copy(); hs.data = stick.data.copy(); coll.objects.link(hs); hs.name = f"{asset}_Stick"
    paint(hs, lambda p, n, i: wood)
    hs.data.materials.clear(); hs.data.materials.append(one)
    export({"Body": body, "Stick": hs}, f"{asset}.fbx")
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    print(f"BUILT {asset}: Body {tris} triangles")
    built.append([body, hs])

# --- Projectiles: upright and centred at the origin, like Stick.fbx ---
def loose_stick(name):
    s = src.copy(); s.data = src.data.copy(); coll.objects.link(s); s.name = name; s.hide_render = False
    s.matrix_world = Matrix.Rotation(math.radians(-90), 4, 'X') @ src.matrix_world
    bpy.context.view_layer.update()
    mn, mx = wb(s); s.location -= (mn + mx) / 2
    bpy.context.view_layer.update()
    return s

gold_shades = [srgb(255, 205, 70), srgb(235, 160, 25), srgb(255, 230, 130)]
golden = loose_stick("GoldenStick_obj")
paint(golden, lambda p, n, i: gold_shades[i % 3])
diamond_shades = [srgb(160, 235, 255), srgb(90, 195, 255), srgb(230, 250, 255), srgb(120, 215, 250)]
diamond = loose_stick("DiamondStick_obj")
paint(diamond, lambda p, n, i: diamond_shades[(i * 7) % 4])

ivory, shade = srgb(242, 234, 212), srgb(215, 202, 170)
bone_parts = [prim("cyl", (0, 0, 0), color=ivory, vertices=8, radius=0.07, depth=0.72)]
for x in (-0.075, 0.075):
    for z in (-0.37, 0.37):
        bone_parts.append(prim("uv", (x, 0, z), fn=lambda p, n, i: shade if abs(p.z) > 0.42 else ivory,
                               segments=10, ring_count=6, radius=0.1))
bone = join(bone_parts, "Bone_obj")

for name, o in (("GoldenStick", golden), ("DiamondStick", diamond), ("Bone", bone)):
    o.data.materials.clear(); o.data.materials.append(one)
    export({name: o}, f"{name}.fbx")
    print(f"BUILT {name}")

# --- Preview: all six Shibas in a row, projectiles in front ---
for o in dog + [stick]: o.hide_render = True
for k, objs in enumerate(built):
    for o in objs: o.location.x += (k - 2.5) * 1.35
for k, o in enumerate((bone, golden, diamond)):
    o.location += Vector(((k - 1) * 0.9, -1.6, 0.35))
    o.rotation_euler = (0, math.radians(60), 0)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 1600, 720
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.2, 0.22, 0.26)
cam = bpy.data.objects['Camera']
cam.location = Vector((0, -11.5, 2.4)); target = Vector((0, -0.5, 0.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "preview_tiers.png")
bpy.ops.render.render(write_still=True)
print("DONE", sorted(os.listdir(OUT)))
