import bpy, math, sys, os
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--")+1]
MODE = sys.argv[sys.argv.index("--")+2]  # preview | export
os.makedirs(OUT, exist_ok=True)

def wb(o):
    cs=[o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector((min(c.x for c in cs),min(c.y for c in cs),min(c.z for c in cs))),
            Vector((max(c.x for c in cs),max(c.y for c in cs),max(c.z for c in cs))))

def bake_vertex_colors(o, override=None):
    me=o.data
    attr=me.color_attributes.new("Col",'BYTE_COLOR','CORNER')
    for poly in me.polygons:
        if override is not None: col=override
        else:
            m=me.materials[poly.material_index] if len(me.materials) else None
            bsdf=[n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'] if m else []
            col=tuple(bsdf[0].inputs['Base Color'].default_value) if bsdf else (0.8,0.8,0.8,1)
        for li in poly.loop_indices: attr.data[li].color=col
    me.color_attributes.active_color=attr

wood=[n for n in bpy.data.materials['wood_brown'].node_tree.nodes if n.type=='BSDF_PRINCIPLED'][0].inputs['Base Color'].default_value
wood=tuple(wood)

# Dog: the posed parts in "Collection"
dog=[o for o in bpy.data.collections['Collection'].objects if o.type=='MESH']
for o in dog: bake_vertex_colors(o)

# Stick: copy of the backup stick, brought into the new (Z-up) frame and put into the right paw.
src=bpy.data.objects['Stick_orig']
stick=src.copy(); stick.data=src.data.copy(); stick.name="Stick"
bpy.data.collections['Collection'].objects.link(stick)
stick.matrix_world = Matrix.Rotation(math.radians(-90),4,'X') @ src.matrix_world  # orig frame was Y-up
bake_vertex_colors(stick, wood)
bpy.context.view_layer.update()
# Long axis of the stick (principal axis of its vertices), grip end = the lower end.
pts=[stick.matrix_world @ v.co for v in stick.data.vertices]
c=sum(pts,Vector())/len(pts)
axis=max((b-a for a in pts[::7] for b in pts[::7]), key=lambda v:v.length).normalized()
proj=[(p-c).dot(axis) for p in pts]
if axis.z<0: axis=-axis; proj=[-x for x in proj]
grip=c+axis*min(proj)
hmn,hmx=wb(bpy.data.objects['RightHand']); hand=(hmn+hmx)/2
want=Vector((0.40,-0.13,0.90)).normalized()
rot=axis.rotation_difference(want).to_matrix().to_4x4()
stick.matrix_world = Matrix.Translation(hand) @ rot @ Matrix.Translation(-grip) @ stick.matrix_world
bpy.context.view_layer.update()
print("stick bbox", [tuple(round(v,3) for v in b) for b in wb(stick)], "hand", tuple(round(v,3) for v in hand))

if MODE=="preview":
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='VERTEX'
    scene.render.resolution_x=480; scene.render.resolution_y=480
    scene.render.film_transparent=False
    for o in bpy.data.collections['Original_backup'].objects: o.hide_render=True
    cam=bpy.data.objects['Camera']
    target=Vector((0,0,0.65))
    for name,pos in [("front",(0,-4,0.9)),("side",(4,0,0.9)),("threequarter",(2.6,-2.8,1.6))]:
        cam.location=Vector(pos); d=target-cam.location
        cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
        cam.data.lens=50
        scene.render.filepath=os.path.join(OUT,f"preview_{name}.png")
        bpy.ops.render.render(write_still=True)
else:
    # Shooter = dog joined into one mesh + separate Stick mesh (the code hides "Stick" after each throw).
    one=bpy.data.materials.new("Shiba")
    for o in dog+[stick]:
        o.data.materials.clear(); o.data.materials.append(one)
    bpy.ops.object.select_all(action='DESELECT')
    for o in dog: o.select_set(True)
    bpy.context.view_layer.objects.active=dog[0]
    bpy.ops.object.join()
    body=bpy.context.view_layer.objects.active; body.name="Body"; body.data.name="Body"
    # Stick-only file: a clean copy standing upright at the origin.
    loose=stick.copy(); loose.data=stick.data.copy()
    common=dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH'},
                colors_type='SRGB', apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False)
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); stick.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,"Shiba.fbx"), **common)
    stick.name="HandStick"; loose.name="Stick"; loose.data.name="Stick"
    bpy.data.collections['Collection'].objects.link(loose)
    loose.matrix_world = Matrix.Rotation(math.radians(-90),4,'X') @ src.matrix_world
    bpy.context.view_layer.update()
    lmn,lmx=wb(loose); loose.location -= (lmn+lmx)/2
    bpy.ops.object.select_all(action='DESELECT'); loose.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,"Stick.fbx"), **common)
    print("exported", os.listdir(OUT))
