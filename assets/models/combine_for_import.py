# Packs many model FBX files into ONE FBX, so Studio needs a single Import 3D instead of one per file.
# Every file becomes a group (FBX node) named like the file; its parts keep their names plus ".<group>" (Blender needs
# unique names), which the Studio snippet in README.md ("Import all models at once") cuts off again.
# Checks the result: re-imports it and compares every group's size with its single file.
#
#   blender --background --factory-startup --python combine_for_import.py -- <out.fbx> [<name> ...]
#
# Without names: every .fbx in models/ and models/props/. With names: only those (file names without .fbx).
import bpy, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
ONLY = set(ARGS[1:])
files = []
for folder in (ROOT, os.path.join(ROOT, "props")):
    files += [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".fbx")]
if ONLY:
    files = [f for f in files if os.path.splitext(os.path.basename(f))[0] in ONLY]

IMPORT = dict(axis_forward='Z', axis_up='Y')
# Same settings as build_props.py, but scale 1: the parts come in already scaled from the single files.
EXPORT = dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH', 'EMPTY'}, colors_type='SRGB',
              apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False, global_scale=1.0)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def dims(objs):
    import mathutils
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    if not pts:
        return None
    return tuple(round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3))


clear()
expected = {}
for path in files:
    name = os.path.splitext(os.path.basename(path))[0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, **IMPORT)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    expected[name] = dims(new)
    for o in new:
        o.name = o.name.split(".")[0] + "." + name
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw
    print("LOADED", name, [o.name for o in new], expected[name])

bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, **EXPORT)

# Verify: re-import the combined file and compare each group's size with the single file.
clear()
bpy.ops.import_scene.fbx(filepath=OUT, **IMPORT)
bpy.context.view_layer.update()
bad = 0
for name, want in expected.items():
    root = bpy.data.objects.get(name)
    got = dims(root.children_recursive) if root else None
    ok = got is not None and want is not None and all(abs(a - b) < 0.01 for a, b in zip(got, want))
    if not ok:
        bad += 1
        print("MISMATCH", name, want, got)
print("GROUPS", len(expected), "MISMATCHES", bad, "SIZE", os.path.getsize(OUT))
