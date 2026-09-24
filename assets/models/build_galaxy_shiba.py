import bpy, sys, os
from mathutils import Vector
# Galaxy Shiba shooter (Marco). Source: galaxy_shiba.obj + .mtl exported from three-d-stage (kept outside git).
# The OBJ has ~1,000 separate objects and plain white fur, so this script
#   - bakes colours into vertex colours (Roblox ignores FBX material colours),
#   - paints the fur with a galaxy gradient (deep indigo at the feet -> violet -> pink -> cyan at the ears),
#   - joins everything into three meshes: Body, Stars, Stick (the code hides "Stick" after each throw).
# Usage:
#   blender --background --factory-startup --python build_galaxy_shiba.py -- <galaxy_shiba.obj> <output folder> preview|export
args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, MODE = args[0], args[1], args[2]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=SRC)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']

pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)

# Galaxy gradient stops (linear RGB), bottom to top.
STOPS = [
    (0.00, (0.020, 0.010, 0.090)),  # deep indigo
    (0.35, (0.160, 0.030, 0.420)),  # violet
    (0.65, (0.650, 0.080, 0.450)),  # pink
    (1.00, (0.120, 0.600, 0.900)),  # cyan
]
GALAXY = {"galaxy_fur", "galaxy_light"}

def gradient(t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return tuple(a + (b - a) * f for a, b in zip(c0, c1))
    return STOPS[-1][1]

def base_color(mat):
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                return tuple(n.inputs['Base Color'].default_value)[:3]
    return (0.8, 0.8, 0.8)

def bake(o):
    me = o.data
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        mat = me.materials[poly.material_index] if len(me.materials) else None
        name = mat.name.split(".")[0] if mat else ""
        for li in poly.loop_indices:
            if name in GALAXY:
                z = (o.matrix_world @ me.vertices[me.loops[li].vertex_index].co).z
                col = gradient((z - zmin) / (zmax - zmin))
                if name == "galaxy_light":  # lighter patches (belly, cheeks)
                    col = tuple(min(1.0, c * 1.6 + 0.08) for c in col)
            else:
                col = base_color(mat)
            attr.data[li].color = (*col, 1.0)
    me.color_attributes.active_color = attr

for o in objs:
    bake(o)

def group(o):
    n = o.name
    if n.startswith(("star", "burst_star", "sparkle")):
        return "Stars"
    if n.startswith("stick"):
        return "Stick"
    return "Body"

one = bpy.data.materials.new("GalaxyShiba")
# Group before joining: join() deletes the merged objects.
groups = {name: [o for o in objs if group(o) == name] for name in ("Body", "Stars", "Stick")}
joined = {}
for name, members in groups.items():
    for o in members:
        o.data.materials.clear(); o.data.materials.append(one)
    bpy.ops.object.select_all(action='DESELECT')
    for o in members:
        o.select_set(True)
    bpy.context.view_layer.objects.active = members[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name; j.data.name = name
    joined[name] = j
    tris = sum(len(p.vertices) - 2 for p in j.data.polygons)
    print(f"MESH {name}: {tris} triangles")

if MODE == "preview":
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'VERTEX'
    sc.render.resolution_x = sc.render.resolution_y = 480
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.25, 0.25, 0.25)
    ctr = Vector((0.1, 0, (zmin + zmax) / 2))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    for name, pos in [("front", (0.1, -3.2, 1.1)), ("threequarter", (2.2, -2.3, 1.5))]:
        cam.location = Vector(pos)
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f"preview_{name}.png")
        bpy.ops.render.render(write_still=True)
else:
    # Same export settings as build_shiba.py, so the model faces the same way in Roblox.
    bpy.ops.object.select_all(action='DESELECT')
    for j in joined.values():
        j.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "Shooter.fbx"), axis_forward='Z', axis_up='Y',
                             use_selection=True, object_types={'MESH'}, colors_type='SRGB',
                             apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False)
    print("exported", os.listdir(OUT))
