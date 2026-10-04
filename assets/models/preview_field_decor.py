import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Matrix, Euler

# Preview of the drop zone decor, mirrors src/shared/Config/FieldDecor.luau by hand (paint, rope border, signs, beach
# props from the FBX files in <fbx folder>, a landing ring, sticks, a character, basket, trophies and Shiba stand-ins).
# Blender Z up, bridge toward +Y. Usage: blender --background --factory-startup --python preview_field_decor.py -- <fbx folder> <out folder>
args = sys.argv[sys.argv.index("--") + 1:]
FBX_DIR = args[0]
OUT = args[1]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
scene = bpy.context.scene
COLL = scene.collection


def srgb(r, g, b):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))


def c3(t):
    return srgb(*t)


def over(base, paint, transparency):
    a = 1 - transparency
    return tuple(b * (1 - a) + p * a for b, p in zip(base, paint))


def paint_obj(o, col):
    me = o.data
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = col(poly) if callable(col) else col
            attr.data[li].color = (*c, 1.0)
    me.color_attributes.active_color = attr


def mesh_from_bm(bm, name, col):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    COLL.objects.link(o)
    paint_obj(o, col)
    return o


def disc(r, z, col, segs=96, cx=0, cy=0, sx=1, sy=1, rot=0, thick=0.02):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=thick)
    M = Matrix.Translation((cx, cy, z - thick / 2)) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Diagonal((sx, sy, 1, 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return mesh_from_bm(bm, "disc", col)


def annulus(r0, r1, z, col, segs=128):
    bm = bmesh.new()
    inner, outer = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        inner.append(bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), z)))
        outer.append(bm.verts.new((r1 * math.cos(a), r1 * math.sin(a), z)))
    for i in range(segs):
        k = (i + 1) % segs
        bm.faces.new((inner[i], outer[i], outer[k], inner[k]))
    return mesh_from_bm(bm, "ring", col)


def stadium(cx, cy, w, h, rot, z, col):
    # rounded rectangle with full rounding (UICorner 0.5)
    r = min(w, h) / 2
    pts = []
    straight_x = w / 2 - r
    straight_y = h / 2 - r
    for q, (ox, oy) in enumerate(((straight_x, straight_y), (-straight_x, straight_y), (-straight_x, -straight_y),
                                  (straight_x, -straight_y))):
        for k in range(9):
            a = q * math.pi / 2 + k * (math.pi / 2) / 8
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0)) for x, y in pts]
    bm.faces.new(vs)
    # canvas rotation is clockwise on screen; canvas Y is flipped vs Blender Y
    M = Matrix.Translation((cx, -cy, z)) @ Matrix.Rotation(-math.radians(rot), 4, 'Z')
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return mesh_from_bm(bm, "blob", col)


def cyl(a, b, r, col, segs=8):
    a, b = Vector(a), Vector(b)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=(b - a).length)
    q = Vector((0, 0, 1)).rotation_difference((b - a).normalized())
    M = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return mesh_from_bm(bm, "cyl", col)


def ball(p, r, col):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p), verts=bm.verts)
    return mesh_from_bm(bm, "ball", col)


def box(p, size, rot_z, col):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Diagonal((*size, 1)),
                        verts=bm.verts)
    return mesh_from_bm(bm, "box", col)


def tri(p0, p1, p2, col):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (p0, p1, p2)]
    bm.faces.new(vs)
    return mesh_from_bm(bm, "tri", col)


def text(body, cx, cy, height, rot, z, col, width=None):
    cu = bpy.data.curves.new("t", 'FONT')
    cu.body = body
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    try:
        cu.font = bpy.data.fonts.load("C:/Windows/Fonts/ariblk.ttf")
    except Exception:
        pass
    o = bpy.data.objects.new("t", cu)
    COLL.objects.link(o)
    o.scale = (height, height, height)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o)
    ob = bpy.data.objects.new("text", me)
    COLL.objects.link(ob)
    # fit width
    xs = [v.co.x for v in me.vertices]
    w = (max(xs) - min(xs)) * height
    s = height
    if width and w > width:
        s = height * width / w
    me.transform(Matrix.Diagonal((s, s, s, 1)))
    me.transform(Matrix.Translation((cx, -cy, z)) @ Matrix.Rotation(-math.radians(rot), 4, 'Z'))
    paint_obj(ob, col)
    return ob


def d(angle_deg, r):
    a = math.radians(angle_deg)
    return Vector((math.sin(a) * r, math.cos(a) * r, 0))


SAND = c3((235, 215, 160))
GRASS = c3((95, 185, 85))
# ground + island edge far away
disc(80, 0.0, GRASS, segs=128, thick=0.5)
disc(30, 0.05, SAND, segs=128, thick=0.05)
# path ring hint
annulus(68, 72, 0.21, c3((222, 196, 140)))

z = 0.07
dz = 0.002
rnd = random.Random(3 * 7919 + 17)


def spot(rad):
    a = rnd.uniform(0, 2 * math.pi)
    dd = rad * math.sqrt(rnd.random())
    return math.cos(a) * dd, math.sin(a) * dd


patch_cols = [c3((205, 175, 115)), c3((250, 236, 196))]
for i in range(9):
    x, y = spot(26)
    w = rnd.uniform(3, 7)
    stadium(x, y, w, w * rnd.uniform(0.45, 0.8), rnd.uniform(0, 180), z, over(SAND, patch_cols[i % 2], 0.6))
    z += dz
peb = [c3((175, 150, 120)), c3((245, 240, 230)), c3((255, 175, 160))]
for i in range(22):
    x, y = spot(28.5)
    p = rnd.uniform(0.3, 0.7)
    stadium(x, y, p, p * rnd.uniform(0.7, 1), rnd.uniform(0, 180), z, over(SAND, peb[i % 3], 0.25))
    z += dz

W = c3((255, 252, 240))
TEAL = c3((60, 165, 200))
rings = [(12, 8, c3((150, 210, 215)), 0.62), (6.2, 0.5, TEAL, 0.35), (12, 0.5, TEAL, 0.45), (20, 0.5, TEAL, 0.45),
         (27.6, 0.55, TEAL, 0.4), (29.1, 0.9, c3((255, 176, 70)), 0.3)]
for r, w, col, t in rings:
    annulus(r, r + w, z, over(SAND, col, t))
    z += dz
disc(6.2, z, over(SAND, c3((95, 190, 215)), 0.5), thick=0.001)
z += dz
BULL = over(SAND, c3((95, 190, 215)), 0.5)
PAW = over(BULL, c3((255, 250, 235)), 0.1)
for (x, y, w, h, rot) in [(0, 1.25, 5.3, 4.5, 0), (-3.15, -2.2, 1.85, 2.4, -25), (-1.1, -3.7, 1.95, 2.6, -8),
                          (1.1, -3.7, 1.95, 2.6, 8), (3.15, -2.2, 1.85, 2.4, 25)]:
    # ellipse-ish: a stadium with equal-ish sides reads as ellipse
    stadium(x, y, w, h, rot, z, PAW)
z += dz
BAND = over(SAND, c3((150, 210, 215)), 0.62)
LET = over(BAND, c3((255, 132, 48)), 0.12)
STROKE = over(BAND, c3((255, 250, 235)), 0.12)
for body, x, y, w, h, rot in [("GET BONKED", 0, -16, 22, 5, 0), ("BONK ZONE", 0, 16, 20, 4.6, 180)]:
    for ox, oy in ((0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)):
        text(body, x + ox, y + oy, h * 0.62, rot, z, STROKE, width=w * 0.92)
    text(body, x, y, h * 0.62, rot, z + dz, LET, width=w * 0.92)
z += 2 * dz

# Border posts, caps, rope, pennants
POST = c3((150, 105, 65))
caps = [c3(c) for c in ((255, 140, 60), (255, 210, 60), (80, 200, 220), (255, 110, 150))]
flags = [c3(c) for c in ((255, 90, 80), (255, 205, 60), (70, 185, 255), (120, 220, 110), (255, 140, 200))]
posts = []
for arc_i, (a0, a1) in enumerate(((15, 138), (162, 345))):
    spans = math.ceil((a1 - a0) / 27)
    for s in range(spans + 1):
        posts.append((a0 + (a1 - a0) * s / spans, arc_i))
fn = 0
sag = 0.55 / 0.75
for i, (a, arc) in enumerate(posts):
    g = d(a, 31)
    cyl(g + Vector((0, 0, -0.3)), g + Vector((0, 0, 2.3)), 0.225, POST)
    ball(g + Vector((0, 0, 2.3 + 0.75 * 0.25)), 0.375, caps[i % 4])
    if i + 1 < len(posts) and posts[i + 1][1] == arc:
        g2 = d(posts[i + 1][0], 31)
        p0 = g + Vector((0, 0, 1.85))
        p3 = g2 + Vector((0, 0, 1.85))
        p1 = p0 - Vector((0, 0, sag))
        p2 = p3 - Vector((0, 0, sag))
        pts = []
        for k in range(13):
            t = k / 12
            pts.append(p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t * t + p3 * t ** 3)
        for q0, q1 in zip(pts, pts[1:]):
            cyl(q0, q1, 0.1, c3((235, 215, 175)), segs=5)
        along = (p3 - p0)
        along.z = 0
        along.normalize()
        for j, share in enumerate((1 / 3, 2 / 3)):
            lo, hi = 0.0, 1.0
            for _ in range(20):
                t = (lo + hi) / 2
                if t * t * (3 - 2 * t) < share:
                    lo = t
                else:
                    hi = t
            pos = p0.lerp(p3, share) - Vector((0, 0, 3 * t * (1 - t) * sag))
            side = along if j % 2 == 0 else -along
            top0 = pos - along * 0.55
            top1 = pos + along * 0.55
            tip = (top1 if j % 2 == 0 else top0) - Vector((0, 0, 1.25))
            tri(top0, top1, tip, flags[fn % 5])
            fn += 1

# Signs on posts 3, 11, 13
for num, label in ((3, "BONK!"), (11, "BONK ZONE"), (13, "CATCH!")):
    a = posts[num - 1][0]
    g = d(a, 31)
    inward = -g.normalized()
    p = g + inward * (0.225 + 0.09) + Vector((0, 0, 1.05))
    rz = math.atan2(inward.y, inward.x) + math.pi / 2
    box(p, (2.6, 0.18, 1.15), rz, c3((255, 245, 225)))
    # text on the inward face
    cu = bpy.data.curves.new("s", 'FONT')
    cu.body = label
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    try:
        cu.font = bpy.data.fonts.load("C:/Windows/Fonts/ariblk.ttf")
    except Exception:
        pass
    o = bpy.data.objects.new("s", cu)
    COLL.objects.link(o)
    o.scale = (0.45, 0.45, 0.45)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    xs = [v.co.x for v in me.vertices]
    w = (max(xs) - min(xs)) * 0.45
    s = 0.45 * min(1, 2.2 / w)
    me.transform(Matrix.Diagonal((s, s, s, 1)))
    me.transform(Matrix.Translation(p + inward * 0.1) @ Matrix.Rotation(rz + math.pi, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    ob = bpy.data.objects.new("signtext", me)
    COLL.objects.link(ob)
    paint_obj(ob, c3((255, 110, 50)))


# Props from the FBX files
def place(name, angle, radius, height, yaw):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(FBX_DIR, name + ".fbx"))
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    bpy.context.view_layer.update()
    zs = []
    for o in objs:
        for v in o.data.vertices:
            zs.append((o.matrix_world @ v.co).z)
    h = max(zs) - min(zs)
    k = height / h
    g = d(angle, radius)
    face = math.atan2(-g.y, -g.x)  # toward centre
    for o in objs:
        mw = o.matrix_world.copy()
        o.matrix_world = (Matrix.Translation(g) @ Matrix.Rotation(face + math.pi / 2 + math.radians(-yaw), 4, 'Z')
                          @ Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((0, 0, -min(zs))) @ mw)


for name, a, r, h, yaw in [("Prop_Sandcastle", 55, 35, 4, 0), ("Prop_BeachBall", 98, 33.6, 2.3, 30), ("Prop_BeachUmbrella", 114, 36.5, 6.5, 25),
                           ("Prop_BucketSpade", 243, 34, 2.5, -20), ("Prop_BoneToy", 28, 33.2, 0.85, 60),
                           ("Prop_BoneToy", 300, 33.8, 0.85, -35), ("Prop_GrassTuft", 78, 32.6, 1.5, 0),
                           ("Prop_GrassTuft", 255, 33, 1.4, 40), ("Prop_GrassTuft", 327, 32.8, 1.6, 80)]:
    place(name, a, r, h, yaw)

# Gameplay stand-ins: a landing ring (Stick tier, brightened brown), a stick lying, a golden stick in flight,
# a character, the basket and trophies, a few Shibas (orange blocks) on the ring.
RING = over(c3((150, 100, 60)), (1, 1, 1), 0.35)
ringc = (0.85, 0.72, 0.55)
ra = annulus(4.3, 4.8, 0.21, c3((195, 153, 126)))
rc = annulus(3.6, 4.1, 0.21, c3((242, 240, 233)))
rc.location = d(215, 16)
rb = annulus(0.01, 4.3, 0.2, over(SAND, c3((195, 153, 126)), 0.72))
lp = d(300, 9)
for o in (ra, rb):
    o.location = lp
stick = cyl(Vector((8, -6, 0.2)), Vector((10.6, -4.8, 0.25)), 0.22, c3((150, 100, 60)))
gold = cyl(Vector((-5, 3, 6)), Vector((-3, 4.5, 6.8)), 0.22, c3((255, 205, 40)))
# character (R15-ish capsule) near centre
cyl(Vector((2, -2, 0)), Vector((2, -2, 3.8)), 0.9, c3((70, 120, 220)))
ball(Vector((2, -2, 4.6)), 0.7, c3((255, 205, 160)))
# basket at 150
bp = d(150, 34.4)
cyl(bp, bp + Vector((0, 0, 2.2)), 2.2, c3((176, 124, 66)), segs=16)
# trophies at 180
for k in range(3):
    tp = d(180 + (k - 1) * 10, 42)
    box(tp + Vector((0, 0, 1)), (3.4, 3.4, 2), 0, c3((45, 42, 60)))
    ball(tp + Vector((0, 0, 3.3)), 1.1, c3((255, 200, 60)))
for k in range(8):
    a = 22.5 + k * 45
    sp = d(a, 56)
    cyl(sp, sp + Vector((0, 0, 1.4)), 3.5, c3((120, 90, 60)), segs=10)
    box(sp + Vector((0, 0, 4.4)), (2.4, 2.4, 6), 0, c3((230, 150, 70)))

# Render settings
sc = scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.view_settings.view_transform = 'Standard'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX'
sc.display.shading.show_shadows = False
sc.display.shading.shadow_intensity = 0.35
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'WORLD'
sc.display.shading.show_object_outline = False
sc.world = bpy.data.worlds.new("w")
sc.world.color = srgb(150, 200, 240)
sc.render.resolution_x = 1600
sc.render.resolution_y = 1000
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 28
cam_data.clip_end = 1000
cam = bpy.data.objects.new("cam", cam_data)
COLL.objects.link(cam)
sc.camera = cam


def shot(loc, target, path):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


shot((0, 62, 38), (0, -2, 0), os.path.join(OUT, "field_overview.png"))
shot((6, 18, 7.5), (-2, -10, 0), os.path.join(OUT, "field_player.png"))
shot((-40, -30, 14), (0, 0, 0), os.path.join(OUT, "field_edge.png"))
print("PREVIEW DONE")
