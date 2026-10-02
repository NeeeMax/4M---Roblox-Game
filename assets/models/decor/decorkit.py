"""Toolkit for the Blender decor models of the street themes (see README.md in this folder).

Coordinates: everything is given in the STAGE FRAME of the theme (docs: src/shared/Config/DecorTypes.luau), in studs:
  x = right, y = UP, z = depth (-z = deeper into the plot, +z = toward the road).
Blender is Z-up with -Y as the "front", so stage (x, y, z) becomes Blender (x, z, y) = `S(x, y, z)`. The FBX export uses
axis_forward='Z', axis_up='Y' like the rest of the pipeline, which brings -Y (front) to Roblox -Z and Z (up) to Y.
In the game the model is scaled and moved to the box of the part's blueprint pieces (World/StreetPlot -> fitToPieces), so
build each model to the same footprint as its blueprint pieces; the pieces stay as invisible colliders.

Usage from a build script (run with: blender --background --factory-startup --python build_<Key>.py -- <out folder>):
    import decorkit as dk
    dk.start(OUT)                       # empty scene, Workbench renderer
    part = dk.Part("Flooring")          # objects created while a part is open belong to it
    dk.box(part, (18, 0.2, 47), (28, 0.4, 14), (150, 150, 156))
    dk.finish(part, key="LittleHouse")  # joins into a few meshes, writes Decor_<Key>_<PartId>.fbx
    dk.preview(part, "Flooring.png")    # 3/4 render of the part with a Shiba for scale
"""
import bpy, bmesh, math, os, json, random, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.dirname(HERE)
EXPORT = dict(axis_forward='Z', axis_up='Y', use_selection=True, object_types={'MESH'}, colors_type='SRGB',
              apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', add_leaf_bones=False)
# Basis change stage -> Blender: stage (x, y, z) = Blender (x, z, y), so it swaps y and z.
SWAP = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
OUT = "."
# The FBX export (forward Z, up Y) is a rotation that sends Blender x to -x, and S() above is a reflection of the stage, so the
# two cancel only if x is mirrored once more before export (checked in Studio: without it every model came in mirrored in x).
MIRROR_X_ON_EXPORT = True
_rng = random.Random(7)


def S(x, y, z):
    """Stage frame point -> Blender point."""
    return Vector((x, z, y))


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def srgb(r, g, b):
    return (lin(r), lin(g), lin(b))


def shade(color, factor):
    """sRGB 0-255 colour times a brightness factor."""
    return tuple(max(0, min(255, c * factor)) for c in color)


def start(out="."):
    """Empty scene, Workbench renderer with studio light and vertex colours."""
    global OUT
    OUT = out
    os.makedirs(out, exist_ok=True)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'VERTEX'
    sc.display.shading.show_backface_culling = True
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
    sc.render.film_transparent = False
    if not sc.world:
        sc.world = bpy.data.worlds.new("W")
    sc.world.color = (0.62, 0.68, 0.76)


class Part:
    """A decor part: collects the objects built for it (one FBX = one part)."""

    def __init__(self, part_id):
        self.id = part_id
        self.objs = []
        self.meshes = []

    def add(self, o):
        self.objs.append(o)
        return o


def _paint(o, color, jitter=0.0):
    """One flat colour (sRGB 0-255) per face, optionally varied a little per face (low-poly texture)."""
    me = o.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        f = 1.0 + (_rng.random() - 0.5) * 2 * jitter if jitter else 1.0
        c = srgb(*shade(color, f))
        for li in poly.loop_indices:
            attr.data[li].color = (*c, 1.0)
    me.color_attributes.active_color = attr
    for poly in me.polygons:
        poly.use_smooth = False


def _object(part, name, bm, location, rot_deg, color, jitter):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    # Rotation is given about the STAGE axes in Roblox order (Rx * Ry * Rz, Rz applied first), then expressed in Blender.
    rx, ry, rz = (math.radians(a) for a in rot_deg)
    r_stage = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
    r_blender = SWAP @ r_stage @ SWAP.transposed()
    o.matrix_world = Matrix.Translation(location) @ r_blender.to_4x4()
    _paint(o, color, jitter)
    if part is not None:
        part.add(o)
    return o


def box(part, center, size, color, rot=(0, 0, 0), jitter=0.0, name="Box"):
    """Block. center and size in stage axes (size = x, y, z)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size[0], size[2], size[1]), verts=bm.verts)
    return _object(part, name, bm, S(*center), rot, color, jitter)


def cyl(part, center, radius, height, color, axis='y', verts=14, top_radius=None, rot=(0, 0, 0), jitter=0.0, name="Cyl"):
    """Cylinder (or cone frustum with top_radius). axis: 'y' = standing (default), 'x' or 'z' = lying along that stage axis."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=radius,
                          radius2=radius if top_radius is None else top_radius, depth=height)
    # create_cone is built along Blender Z (= stage y): standing. Lie it down by rotating the mesh itself.
    if axis == 'x':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'))
    elif axis == 'z':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    return _object(part, name, bm, S(*center), rot, color, jitter)


def cone(part, base_center, radius, height, color, verts=10, jitter=0.0, name="Cone"):
    """Pointed cone standing on base_center (tip up)."""
    c = (base_center[0], base_center[1] + height / 2, base_center[2])
    return cyl(part, c, radius, height, color, verts=verts, top_radius=0.0, jitter=jitter, name=name)


def ball(part, center, radius, color, scale=(1, 1, 1), subdiv=2, rot=(0, 0, 0), jitter=0.0, name="Ball"):
    """Low-poly sphere (ico). scale = (x, y, z) stretch in stage axes."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    bmesh.ops.scale(bm, vec=(scale[0], scale[2], scale[1]), verts=bm.verts)
    return _object(part, name, bm, S(*center), rot, color, jitter)


def poly(part, origin, points, faces, color, jitter=0.0, rot=(0, 0, 0), name="Poly"):
    """Raw mesh: points in stage axes relative to origin, faces as index tuples (winding is fixed automatically)."""
    bm = bmesh.new()
    verts = [bm.verts.new((p[0], p[2], p[1])) for p in points]
    for f in faces:
        try:
            bm.faces.new([verts[i] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _object(part, name, bm, S(*origin), rot, color, jitter)


def prism(part, base_center, width, depth, height, color, ridge='x', jitter=0.0, name="Roof"):
    """Gable roof / triangular prism: base width x depth centred on base_center, ridge along stage x ('x') or z ('z')."""
    w, d, h = width / 2, depth / 2, height
    if ridge == 'x':   # ridge runs along x, triangle in the y-z plane
        pts = [(-w, 0, -d), (w, 0, -d), (w, 0, d), (-w, 0, d), (-w, h, 0), (w, h, 0)]
        faces = [(0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)]
    else:              # ridge runs along z, triangle in the x-y plane
        pts = [(-w, 0, -d), (w, 0, -d), (w, 0, d), (-w, 0, d), (0, h, -d), (0, h, d)]
        faces = [(0, 1, 2, 3), (0, 4, 1), (3, 2, 5), (0, 3, 5, 4), (1, 4, 5, 2)]
    return poly(part, base_center, pts, faces, color, jitter, name=name)


def wedge(part, center, size, color, rot=(0, 0, 0), jitter=0.0, name="Wedge"):
    """Ramp like a Roblox WedgePart: vertical back (+z), sloping from the top at the back down to the front (-z)."""
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    pts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz), (-sx, sy, sz), (sx, sy, sz)]
    faces = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2), (0, 4, 5, 1)]
    return poly(part, center, pts, faces, color, jitter, rot=rot, name=name)


def from_pieces(part, pieces, jitter=0.0):
    """The blueprint as it is now: one primitive per piece (JSON 'Pieces' of the exported theme)."""
    for i, p in enumerate(pieces):
        size, off, col = p["Size"], p["Offset"], p["Color"]
        rot = p.get("Rotation") or (0, 0, 0)
        shape = p.get("Shape") or "PartType.Block"
        if "Cylinder" in shape:
            # Roblox cylinder: axis along the piece's x, diameter in y/z.
            cyl(part, off, max(size[1], size[2]) / 2, size[0], col, axis='x', rot=rot, jitter=jitter, name=f"Piece{i}")
        elif "Ball" in shape:
            ball(part, off, size[0] / 2, col, scale=(1, size[1] / size[0], size[2] / size[0]), rot=rot, jitter=jitter,
                 name=f"Piece{i}")
        elif "Wedge" in shape:
            wedge(part, off, size, col, rot=rot, jitter=jitter, name=f"Piece{i}")
        else:
            box(part, off, size, col, rot=rot, jitter=jitter, name=f"Piece{i}")


def load_blueprint(path):
    with open(path) as f:
        return json.load(f)


def blueprint_part(bp, part_id):
    return next(p for p in bp["Parts"] if p["Id"] == part_id)


# ---- finishing: join, export ---------------------------------------------------------------------------------------
_material = None


def _single_material():
    global _material
    if _material is None or _material.name not in bpy.data.materials:
        _material = bpy.data.materials.new("Decor")
    return _material


def join(objs, name):
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(_single_material())
    j = objs[0]
    if len(objs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = j
        bpy.ops.object.join()
        j = bpy.context.view_layer.objects.active
    j.name = name
    j.data.name = name
    return j


def _mirror_x(meshes):
    """Bakes each mesh into world space and mirrors it in x (windings flipped back), so the exported FBX lands correctly in Roblox."""
    for m in meshes:
        me = m.data
        me.transform(m.matrix_world)
        m.matrix_world = Matrix.Identity(4)
        me.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
        me.flip_normals()
        me.update()


def finish(part, key, groups=None):
    """Joins the part's objects and exports Decor_<key>_<id>.fbx to the output folder.

    groups: optional {mesh name: [objects]} to keep a few separate meshes (e.g. 'Roof'); the rest becomes 'Body'.
    Keep it to a handful of meshes: every mesh is one MeshPart in Roblox. Returns the exported mesh objects."""
    groups = dict(groups or {})
    used = {id(o) for objs in groups.values() for o in objs}
    rest = [o for o in part.objs if id(o) not in used]
    if rest:
        groups["Body"] = groups.get("Body", []) + rest
    meshes = [join(objs, f"{part.id}_{name}") for name, objs in groups.items() if objs]
    part.meshes = meshes
    if MIRROR_X_ON_EXPORT:
        _mirror_x(meshes)
    bpy.ops.object.select_all(action='DESELECT')
    for m in meshes:
        m.select_set(True)
    path = os.path.join(OUT, f"Decor_{key}_{part.id}.fbx")
    bpy.ops.export_scene.fbx(filepath=path, **EXPORT)
    tris = sum(len(p.vertices) - 2 for m in meshes for p in m.data.polygons)
    print(f"EXPORTED Decor_{key}_{part.id}: {len(meshes)} meshes, {tris} triangles -> {path}")
    return meshes


# ---- reference Shiba and preview rendering ------------------------------------------------------------------------
def add_reference_shiba(bp, studs=6.0):
    """Imports Shiba.fbx scaled to `studs` tall at the theme's Shiba spot (stage frame), facing as in the blueprint."""
    spot = bp.get("Shiba")
    if not spot:
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(MODELS, "Shiba.fbx"), axis_forward='Z', axis_up='Y')
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low = min(p.z for p in pts)
    high = max(p.z for p in pts)
    k = studs / (high - low)
    x, z = spot["Position"]
    facing = math.radians(spot["Facing"])
    # Stage facing: 0 = +x, 90 = -z (deeper), i.e. direction (cos f, -sin f) in stage (x, z) = Blender (x, y).
    # The imported dog faces Blender -Y.
    want = Vector((math.cos(facing), -math.sin(facing), 0))
    yaw = math.atan2(want.y, want.x) - math.atan2(-1, 0)
    m = Matrix.Translation(S(x, 0, z)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(k, 4) @ Matrix.Translation((0, 0, -low))
    for o in new:
        o.matrix_world = m @ o.matrix_world
    return new


def _bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    low = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    high = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return low, high


def ground(low, high, color=(96, 160, 80), margin=1.3):
    """A flat grass slab under the scene for context (not exported)."""
    cx, cy = (low.x + high.x) / 2, (low.y + high.y) / 2
    sx, sy = (high.x - low.x) * margin / 2 + 4, (high.y - low.y) * margin / 2 + 4
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx * 2, sy * 2, 0.3), verts=bm.verts)
    me = bpy.data.meshes.new("Ground")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("Ground", me)
    bpy.context.scene.collection.objects.link(o)
    o.location = (cx, cy, -0.17)
    _paint(o, color)
    return o


def _camera(target, distance, azimuth_deg, elevation_deg):
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    # azimuth 0 = looking from the front (-Y) toward +Y
    pos = target + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * distance
    cam.location = pos
    cam.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 40
    cam_data.clip_end = 5000
    bpy.context.scene.camera = cam
    return cam


def preview(what, filename, with_shiba=None, azimuth=35, elevation=28, size=(1400, 1000), extra=None, top=False):
    """Renders a Part (or list of objects) on a grass slab; with_shiba = blueprint dict adds the Shiba for scale.
    extra = further objects to frame (e.g. the other parts of the stage)."""
    if isinstance(what, Part):
        objs = list(what.meshes or what.objs)
    else:
        objs = list(what)
    shiba = add_reference_shiba(with_shiba) if with_shiba else []
    low, high = _bounds(objs + shiba + list(extra or []))
    g = ground(low, high)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 6)
    cam = _camera(centre, radius * (3.0 if top else 2.6), azimuth, 89 if top else elevation)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in shiba:
        bpy.data.objects.remove(o, do_unlink=True)
    print("RENDERED", sc.render.filepath)


def hide(objs, hidden=True):
    for o in objs:
        o.hide_render = hidden
        o.hide_viewport = hidden


def args():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
