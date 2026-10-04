"""Final low-poly decor models for the theme ClockTower (30 parts around the 29th Shiba, Eternal Shiba).

Usage: blender --background --factory-startup --python build_ClockTower.py -- <outdir> [PartId,PartId,...]
Writes Decor_ClockTower_<PartId>.fbx, preview_<PartId>.png and stage_ClockTower.png into <outdir>.
Every model is written in STAGE coordinates (the numbers of DecorTheme29.luau) and fitted to the union box of its blueprint
pieces (same footprint, same height). Models are built WITHOUT the part's Yaw (the game applies it). Give part ids (comma
separated) after the out folder to rebuild only those parts (no stage render then).
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decorkit as dk
from decorkit import S

ARGS = dk.args()
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(HERE, "out", "ClockTower"))
ONLY = [a for a in (ARGS[1].split(",") if len(ARGS) > 1 else []) if a]
KEY = "ClockTower"
BP = dk.load_blueprint(os.path.join(HERE, "blueprint_ClockTower.json"))

# ---- palette (one for all 30 parts: midnight blue stone, star-white, gold and brass, a little violet and cyan) --------------
NAVY = (26, 30, 74)
MIDNIGHT = (42, 48, 110)
INDIGO = (66, 72, 148)
VIOLET = (120, 92, 196)
STARW = (248, 248, 255)
PEARL = (228, 230, 246)
GOLD = (246, 200, 72)
LGOLD = (255, 226, 130)
BRASS = (204, 152, 62)
DBRASS = (150, 106, 44)
COPPER = (198, 112, 72)
STONE = (186, 188, 204)
DSTONE = (120, 124, 150)
GLASS = (176, 212, 250)
SAND = (255, 228, 150)
CYAN = (110, 206, 238)
WOOD = (130, 84, 56)
DWOOD = (96, 60, 40)
DARK = (36, 38, 62)
PATH = [(0, 57.5), (34, 44), (-12, 32), (-48, 20), (-16, -2), (22, -10), (52, -28), (20, -44), (0, -57.5)]

# ---- helpers ---------------------------------------------------------------------------------------------------------
def bx(p, x, y, z, col, jit=0.04, rot=(0, 0, 0)):
    """Box from ranges (min, max) in stage axes."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    s = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    return dk.box(p, c, s, col, rot=rot, jitter=jit)


def vcyl(p, cx, y0, y1, cz, r, col, verts=10, top_r=None, jit=0.04):
    return dk.cyl(p, (cx, (y0 + y1) / 2, cz), r, y1 - y0, col, axis='y', verts=verts, top_radius=top_r, jitter=jit)


def xcyl(p, x0, x1, cy, cz, r, col, verts=10, jit=0.04):
    return dk.cyl(p, ((x0 + x1) / 2, cy, cz), r, x1 - x0, col, axis='x', verts=verts, jitter=jit)


def zcyl(p, cx, cy, z0, z1, r, col, verts=10, jit=0.04, rot=(0, 0, 0)):
    return dk.cyl(p, (cx, cy, (z0 + z1) / 2), r, z1 - z0, col, axis='z', verts=verts, jitter=jit, rot=rot)


def ball(p, c, r, col, scale=(1, 1, 1), subdiv=1, jit=0.04):
    return dk.ball(p, c, r, col, scale=scale, subdiv=subdiv + 1, jitter=jit)


def hexa(p, pts, col, jit=0.04):
    """Any 8-point hexahedron: points 0-3 bottom ring, 4-7 the top ring above them (absolute stage coordinates)."""
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def prism_z(p, tri, z0, z1, col, jit=0.04):
    """Triangular prism: tri = three (x, y) points, extruded along z from z0 to z1."""
    pts = [(a, b, z0) for a, b in tri] + [(a, b, z1) for a, b in tri]
    faces = [(0, 1, 2), (3, 5, 4), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def bar(p, a, b, t, col, jit=0.04):
    """Square bar of thickness t between two 3D points (stage coordinates)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized() * (t / 2)
    v = d.cross(u).normalized() * (t / 2)
    pts = []
    for q in (a, b):
        for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            pts.append(tuple(q + u * su + v * sv))
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def diag(p, x1, y1, z, x2, y2, t, depth, col, jit=0.04):
    """Bar in the x-y plane from (x1,y1) to (x2,y2), thickness t, depth along z centred on z."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    ln = math.hypot(x2 - x1, y2 - y1)
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return dk.box(p, (cx, cy, z), (ln, t, depth), col, rot=(0, 0, ang), jitter=jit)


def star_poly(p, c, plane, ro, ri, thick, col, n=5, rot0=90, jit=0.03):
    """Flat n-pointed star around centre c. plane: 'xy' (faces +z), 'xz' (lies flat), 'yz' (faces +x)."""
    cx, cy, cz = c
    ring = []
    for k in range(2 * n):
        a = math.radians(rot0) + k * math.pi / n
        r = ro if k % 2 == 0 else ri
        ring.append((r * math.cos(a), r * math.sin(a)))

    def at(a, b, d):
        if plane == 'xy':
            return (cx + a, cy + b, cz + d)
        if plane == 'xz':
            return (cx + a, cy + d, cz + b)
        return (cx + d, cy + a, cz + b)
    h = thick / 2
    pts = [at(a, b, h) for a, b in ring] + [at(a, b, -h) for a, b in ring] + [at(0, 0, h), at(0, 0, -h)]
    m = 2 * n
    faces = []
    for k in range(m):
        q = (k + 1) % m
        faces += [(2 * m, k, q), (2 * m + 1, m + q, m + k), (k, m + k, m + q, q)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def torus(p, c, R, r, col, segs=16, sides=8, arc=None, scale_y=1.0, jit=0.04):
    """Ring lying flat (axis up) around centre c; arc=(b0, b1) in radians gives an open part of the tube (e.g. the top half)."""
    pts, faces = [], []
    full = arc is None
    b0, b1 = (0.0, 2 * math.pi) if full else arc
    ns = sides if full else sides + 1
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for j in range(ns):
            b = b0 + (b1 - b0) * j / sides
            rr = R + r * math.cos(b)
            pts.append((rr * math.cos(a), r * scale_y * math.sin(b), rr * math.sin(a)))
    for i in range(segs):
        for j in range(ns if full else ns - 1):
            i2 = (i + 1) % segs
            j2 = (j + 1) % ns if full else j + 1
            faces.append((i * ns + j, i2 * ns + j, i2 * ns + j2, i * ns + j2))
    return dk.poly(p, c, pts, faces, col, jit)




def fit(part, lo, hi):
    objs = part.objs
    for o in objs:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    pts = [v.co.copy() for o in objs for v in o.data.vertices]
    bl = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
    bh = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
    tl, th = S(*lo), S(*hi)
    print(f"BOX {part.id}: target stage x {lo[0]:.2f}..{hi[0]:.2f} y {lo[1]:.2f}..{hi[1]:.2f} z {lo[2]:.2f}..{hi[2]:.2f}")
    print(f"BOX {part.id}: built  stage x {bl.x:.2f}..{bh.x:.2f} y {bl.z:.2f}..{bh.z:.2f} z {bl.y:.2f}..{bh.y:.2f}")
    sc = [(th[i] - tl[i]) / (bh[i] - bl[i]) for i in range(3)]
    m = Matrix.Translation(tl) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-bl)
    for o in objs:
        o.data.transform(m)
    print(f"FIT {part.id}: scale stage xyz = {sc[0]:.3f} {sc[2]:.3f} {sc[1]:.3f}")




def ry(x, z, deg):
    """Roblox rotation about y of the horizontal vector (x, z)."""
    a = math.radians(deg)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)



def union(part_json):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for q in part_json["Pieces"]:
        s, o, r = q["Size"], q["Offset"], q.get("Rotation") or (0, 0, 0)
        shape = q.get("Shape") or ""
        cyl = "Cylinder" in shape
        if cyl:
            # Roblox cylinder: axis along the piece's x
            pass
        rx, ry_, rz = (math.radians(a) for a in r)
        R = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry_, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append(R @ Vector((sx * s[0] / 2, sy * s[1] / 2, sz * s[2] / 2)))
        if "Ball" in shape or cyl:
            # ellipsoid / cylinder: use the exact extents of the rotated shape
            ext = [0, 0, 0]
            for i in range(3):
                if "Ball" in shape:
                    ext[i] = math.sqrt(sum((R[i][j] * s[j] / 2) ** 2 for j in range(3)))
                else:
                    # axis (x) half length, round (y, z) radius s[1]/2
                    ext[i] = abs(R[i][0]) * s[0] / 2 + math.sqrt(R[i][1] ** 2 + R[i][2] ** 2) * s[1] / 2
        else:
            ext = [max(abs(v[i]) for v in pts) for i in range(3)]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - ext[i])
            hi[i] = max(hi[i], o[i] + ext[i])
    return lo, hi




# ---- more helpers ---------------------------------------------------------------------------------------------------------
def frustum(p, cx, y0, y1, cz, wb, db, wt, dt, col, jit=0.04):
    """Box that narrows from wb x db at y0 to wt x dt at y1 (roof tier)."""
    pts = [(cx - wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz - db / 2), (cx + wb / 2, y0, cz + db / 2), (cx - wb / 2, y0, cz + db / 2),
           (cx - wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz - dt / 2), (cx + wt / 2, y1, cz + dt / 2), (cx - wt / 2, y1, cz + dt / 2)]
    return hexa(p, pts, col, jit)


def edisc(p, cx, y0, y1, cz, rx, rz, col, n=16, jit=0.03):
    """Flat elliptical slab."""
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), y0, cz + rz * math.sin(2 * math.pi * i / n)) for i in range(n)]
    pts += [(x, y1, z) for (x, _, z) in pts]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


WING_OUTLINE = [(0, 0), (0.5, -0.14), (1.0, 0.04), (0.82, 0.38), (0.98, 0.70), (0.62, 0.86), (0.42, 1.0), (0.16, 0.66)]



def lbox(p, cx, cz, deg, lx, y, lz, sx, sy, sz, col, jit=0.04):
    """Box placed by an offset (lx, lz) in the local frame of a group turned by deg about its centre (cx, cz)."""
    a, b = ry(lx, lz, deg)
    return dk.box(p, (cx + a, y, cz + b), (sx, sy, sz), col, rot=(0, deg, 0), jitter=jit)



def arc_strip(p, cx, cy, ao, bo, ai, bi, z0, z1, col, n=10, t0=0.0, t1=math.pi, jit=0.03):
    """Solid band between two ellipse arcs (outer half-axes ao, bo, inner ai, bi) around (cx, cy), extruded from z0 to z1."""
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((cx + ao * math.cos(t), cy + bo * math.sin(t), z0))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pts.append((cx + ai * math.cos(t), cy + bi * math.sin(t), z0))
    m = n + 1
    pts += [(x, y, z1) for (x, y, _) in pts]
    off = 2 * m
    faces = []
    for i in range(n):
        faces += [(i, i + 1, m + i + 1, m + i), (off + i, off + i + 1, off + m + i + 1, off + m + i),
                  (i, i + 1, off + i + 1, off + i), (m + i, m + i + 1, off + m + i + 1, off + m + i)]
    faces += [(0, m, off + m, off), (n, m + n, off + m + n, off + n)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)






# ---- helpers of this theme ---------------------------------------------------------------------------------------------
def B(p, x, y, z, sx, sy, sz, col, rot=(0, 0, 0), jit=0.04):
    """Block by centre and size (like the theme's B())."""
    return dk.box(p, (x, y, z), (sx, sy, sz), col, rot=rot, jitter=jit)


def lathe(p, cx, cz, prof, cols, verts=12, jit=0.04):
    """Turned body: prof = [(radius, y), ...] bottom to top, cols = one colour (or a list, one per segment)."""
    if not isinstance(cols[0], (tuple, list)):
        cols = [cols] * (len(prof) - 1)
    for i in range(len(prof) - 1):
        (r0, y0), (r1, y1) = prof[i], prof[i + 1]
        if y1 - y0 < 1e-4:
            continue
        vcyl(p, cx, y0, y1, cz, max(r0, 0.02), cols[i], verts=verts, top_r=max(r1, 0.02), jit=jit)


def ring3(p, c, R, r, normal, col, segs=18, sides=4, jit=0.03, rot0=0.0):
    """Torus of radius R, tube radius r, around centre c, the ring lying in the plane perpendicular to `normal`."""
    n = Vector(normal).normalized()
    ref = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    u = n.cross(ref).normalized()
    v = n.cross(u).normalized()
    pts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        d = u * math.cos(a) + v * math.sin(a)
        for j in range(sides):
            b = 2 * math.pi * j / sides + rot0
            q = d * (R + r * math.cos(b)) + n * (r * math.sin(b))
            pts.append((q.x, q.y, q.z))
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2))
    return dk.poly(p, c, pts, faces, col, jit)


def uvw(axis, c, u, v, w):
    """Local gear frame -> stage point. axis: 'y' = lying flat (faces up), 'z' = faces the road, 'x' = faces sideways."""
    cx, cy, cz = c
    if axis == 'y':
        return (cx + u, cy + w, cz + v)
    if axis == 'z':
        return (cx + u, cy + v, cz + w)
    return (cx + w, cy + u, cz + v)


def gear(p, c, axis, R, depth, n, thick, col, hole=0.0, jit=0.04, phase=0.0):
    """Toothed wheel: outer radius R (tooth tips), tooth depth, n teeth, thick along its axis, optional centre hole radius."""
    out = []
    for i in range(n):
        a0 = 2 * math.pi * i / n + phase
        da = 2 * math.pi / n
        for (f, rr) in ((0.04, R - depth), (0.22, R), (0.50, R), (0.68, R - depth)):
            out.append((a0 + f * da * 1.5, rr))
    m = len(out)
    h = thick / 2
    pts = []
    for w in (h, -h):
        for (a, rr) in out:
            pts.append(uvw(axis, c, rr * math.cos(a), rr * math.sin(a), w))
    faces = []
    if hole > 0:
        for w in (h, -h):
            for (a, _) in out:
                pts.append(uvw(axis, c, hole * math.cos(a), hole * math.sin(a), w))
        base_o = (0, m)
        base_h = (2 * m, 3 * m)
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((k, k2, 2 * m + k2, 2 * m + k))
            faces.append((m + k, m + 2 * m + k, m + 2 * m + k2, m + k2) if False else (m + k2, m + k, 3 * m + k, 3 * m + k2))
            faces.append((k, m + k, m + k2, k2))
            faces.append((2 * m + k, 2 * m + k2, 3 * m + k2, 3 * m + k))
        _ = (base_o, base_h)
    else:
        pts.append(uvw(axis, c, 0, 0, h))
        pts.append(uvw(axis, c, 0, 0, -h))
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((2 * m, k, k2))
            faces.append((2 * m + 1, m + k2, m + k))
            faces.append((k, m + k, m + k2, k2))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def face_pt(face, c, u, v, w):
    """Viewer frame on a wall: u = to the viewer's right, v = up, w = out of the wall. face in +z -z +x -x."""
    cx, cy, cz = c
    if face == '+z':
        return (cx + u, cy + v, cz + w)
    if face == '-z':
        return (cx - u, cy + v, cz - w)
    if face == '+x':
        return (cx + w, cy + v, cz - u)
    return (cx - w, cy + v, cz + u)


def fbox(p, face, c, u0, u1, v0, v1, w0, w1, col, jit=0.03):
    pts = [face_pt(face, c, u, v, w) for w in (w0, w1) for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def fpoly(p, face, c, uv, w0, w1, col, jit=0.03):
    """Prism over the convex polygon uv = [(u, v), ...] between two depths on a wall."""
    n = len(uv)
    pts = [face_pt(face, c, u, v, w) for w in (w0, w1) for (u, v) in uv]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def fdisc(p, face, c, r, w0, w1, col, verts=16, jit=0.03):
    """Cylinder standing on a wall (axis = wall normal) from depth w0 to w1."""
    cx, cy, cz = c
    if face == '+z':
        return zcyl(p, cx, cy, cz + w0, cz + w1, r, col, verts, jit)
    if face == '-z':
        return zcyl(p, cx, cy, cz - w1, cz - w0, r, col, verts, jit)
    if face == '+x':
        return xcyl(p, cx + w0, cx + w1, cy, cz, r, col, verts, jit)
    return xcyl(p, cx - w1, cx - w0, cy, cz, r, col, verts, jit)


def rrect(u0, v0, u1, v1, t):
    """Rectangle of width t along the segment (u0, v0) -> (u1, v1), as uv points."""
    dx, dy = u1 - u0, v1 - v0
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln * t / 2, dx / ln * t / 2
    return [(u0 + nx, v0 + ny), (u1 + nx, v1 + ny), (u1 - nx, v1 - ny), (u0 - nx, v0 - ny)]


def clock(p, face, c, R, s=0.8, bez=GOLD, dial=STARW, tick=DARK, verts=18, ticks=True, big=0.2):
    """Round clock on a wall: bezel, raised dial and 12 hour marks. c = point on the wall surface."""
    fdisc(p, face, c, R, 0, s * 0.75, bez, verts)
    fdisc(p, face, c, R * 0.88, 0, s, dial, verts)
    if ticks:
        for k in range(12):
            a = math.radians(30 * k)
            major = k % 3 == 0
            r0, r1 = R * (0.66 if major else 0.72), R * 0.82
            uv = rrect(r0 * math.cos(a), r0 * math.sin(a), r1 * math.cos(a), r1 * math.sin(a), R * (0.11 if major else 0.06))
            fpoly(p, face, c, uv, s, s + 0.1 * (1 + R * 0.05), tick, 0.02)


def hands(p, face, c, w0, w1, lh=3.6, lm=5.0, tail=1.0, wh=0.45, wm=0.35, hour_deg=150, min_deg=30, col=GOLD, hub=BRASS, hub_r=0.7):
    """Hour and minute hand (kite shaped) standing on a wall from depth w0 to w1, plus a hub."""
    for ang, ln, wd in ((hour_deg, lh, wh), (min_deg, lm, wm)):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(-tail * ca, -tail * sa), (0.3 * ln * ca - wd * sa, 0.3 * ln * sa + wd * ca), (ln * ca, ln * sa),
               (0.3 * ln * ca + wd * sa, 0.3 * ln * sa - wd * ca)]
        fpoly(p, face, c, pts, w0, w1, col, 0.02)
    fdisc(p, face, c, hub_r, w0 - 0.05, w1 + 0.05, hub, 10, 0.02)


def pyramid(p, cx, y0, y1, cz, wb, db, col, jit=0.04):
    return frustum(p, cx, y0, y1, cz, wb, db, 0.02, 0.02, col, jit)


def prism_x(p, tri, x0, x1, col, jit=0.04):
    """Prism along x over the polygon tri = [(y, z), ...] (convex)."""
    n = len(tri)
    pts = [(x, y, z) for x in (x0, x1) for (y, z) in tri]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return dk.poly(p, (0, 0, 0), pts, faces, col, jit)


def spark(p, c, r, col=STARW, plane='xy'):
    star_poly(p, c, plane, r, r * 0.3, 0.14, col, n=4, rot0=90)


def hourglass(p, cx, y0, cz, r, h, glass=GLASS, sand=SAND, sand2=STARW, frame=GOLD, posts=True, verts=12, plate_r=None, post_r=None):
    """Hourglass standing on y0: gold plates, two glass bulbs with sand in the lower parts, a neck, a falling stream."""
    t = h * 0.06
    pr = plate_r or r * 1.18
    vcyl(p, cx, y0, y0 + t, cz, pr, frame, verts=verts)
    vcyl(p, cx, y0 + h - t, y0 + h, cz, pr, frame, verts=verts)
    yb, yt = y0 + t, y0 + h - t
    mid = (yb + yt) / 2
    nk = h * 0.05
    low = [(r * 0.5, yb), (r * 0.92, yb + (mid - yb) * 0.16), (r, yb + (mid - yb) * 0.4), (r * 0.8, yb + (mid - yb) * 0.7),
           (r * 0.4, yb + (mid - yb) * 0.9), (r * 0.12, mid - nk)]
    lc = [sand, sand, glass, glass, glass]
    lathe(p, cx, cz, low, lc, verts=verts, jit=0.03)
    up = [(r * 0.12, mid + nk), (r * 0.4, mid + (yt - mid) * 0.1), (r * 0.8, mid + (yt - mid) * 0.3), (r, mid + (yt - mid) * 0.6),
          (r * 0.92, mid + (yt - mid) * 0.84), (r * 0.5, yt)]
    uc = [sand2, sand2, glass, glass, glass]
    lathe(p, cx, cz, up, uc, verts=verts, jit=0.03)
    vcyl(p, cx, mid - nk, mid + nk, cz, r * 0.12, sand, verts=8)
    if posts:
        pq = post_r or r * 1.05
        for k in range(4):
            a = math.radians(45 + 90 * k)
            vcyl(p, cx + pq * math.cos(a), yb, yt, cz + pq * math.sin(a), max(0.07, r * 0.07), frame, verts=6, jit=0.02)


def clockwise_poly(pts):
    return pts




# ---- 1. Ground --------------------------------------------------------------------------------------------------------------
def build_Ground(p):
    bx(p, (-80, 80), (0, 0.3), (-57.5, 57.5), NAVY, 0.05)
    plazas = [(14, 16, 36, 22, INDIGO), (48, 12, 30, 24, INDIGO), (-48, 40, 36, 26, INDIGO), (-18, -36, 28, 40, INDIGO),
              (66, -38, 26, 30, MIDNIGHT), (62, 38, 28, 28, INDIGO)]
    for (x, z, w, d, col) in plazas:
        bx(p, (x - w / 2, x + w / 2), (0.3, 0.5), (z - d / 2, z + d / 2), col, 0.06)
        s = min(w, d) * 0.32
        B(p, x, 0.52, z, s, 0.06, s, PEARL, rot=(0, 45, 0), jit=0.03)
        B(p, x, 0.55, z, s * 0.5, 0.06, s * 0.5, GOLD, rot=(0, 45, 0), jit=0.03)
    # tower plaza with a gold ring
    bx(p, (-67, -33), (0.3, 0.5), (-51, -17), MIDNIGHT, 0.05)
    vcyl(p, -50, 0.5, 0.54, -34, 16.2, GOLD, verts=24)
    vcyl(p, -50, 0.5, 0.56, -34, 15.4, MIDNIGHT, verts=24)
    # the Shiba's dais: midnight disc, gold ring, pearl centre with a star, twelve zodiac ticks
    vcyl(p, -30, 0.3, 0.45, -6, 15, MIDNIGHT, verts=20)
    vcyl(p, -30, 0.45, 0.54, -6, 11.4, GOLD, verts=20)
    vcyl(p, -30, 0.45, 0.55, -6, 10.5, INDIGO, verts=20)
    vcyl(p, -30, 0.45, 0.55, -6, 6.2, PEARL, verts=14)
    star_poly(p, (-30, 0.57, -6), 'xz', 5.4, 3.0, 0.04, GOLD, n=8)
    for k in range(12):
        a = math.radians(30 * k)
        B(p, -30 + 13.2 * math.cos(a), 0.5, -6 + 13.2 * math.sin(a), 1.6, 0.1, 0.5, GOLD, rot=(0, -30 * k, 0), jit=0.02)
    # star-white stepping stones along the walkway
    for (ax, az), (bx_, bz) in zip(PATH, PATH[1:]):
        ln = math.hypot(bx_ - ax, bz - az)
        deg = -math.degrees(math.atan2(bz - az, bx_ - ax))
        n = int(ln // 8)
        for i in range(n):
            t = (i + 0.5) / n
            B(p, ax + (bx_ - ax) * t, 0.34, az + (bz - az) * t, 2.4, 0.08, 1.0, PEARL, rot=(0, deg, 0), jit=0.04)


# ---- 2. StarLamps ---------------------------------------------------------------------------------------------------------
def lamp(p, x, z):
    vcyl(p, x, 0, 0.6, z, 1.3, DBRASS, verts=10)
    vcyl(p, x, 0.6, 1.4, z, 0.9, BRASS, verts=10)
    vcyl(p, x, 1.4, 9.4, z, 0.32, GOLD, verts=8)
    vcyl(p, x, 4.8, 5.3, z, 0.55, GOLD, verts=8)
    lathe(p, x, z, [(0.45, 9.4), (1.3, 9.9), (1.55, 10.8), (1.15, 11.7)], [GOLD, STARW, STARW], verts=8)
    vcyl(p, x, 11.7, 12.7, z, 1.45, GOLD, verts=8, top_r=0.15)
    ball(p, (x, 12.95, z), 0.4, GOLD)
    for k in range(4):
        a = math.radians(90 * k + 45)
        vcyl(p, x + 1.0 * math.cos(a), 10.1, 11.5, z + 1.0 * math.sin(a), 0.1, GOLD, verts=4, jit=0.02)


def build_StarLamps(p):
    for (x, z) in ((-6, 46), (46, 52), (4, 24)):
        lamp(p, x, z)


# ---- 3. TimeSign ----------------------------------------------------------------------------------------------------------
def build_TimeSign(p):
    bx(p, (-26, -12), (0, 1), (48, 52), STONE, 0.04)
    bx(p, (-25, -13), (1, 1.4), (48.6, 51.4), PEARL, 0.03)
    for x in (-24, -14):
        vcyl(p, x, 1.4, 10.0, 50, 0.45, BRASS, verts=8)
        vcyl(p, x, 1.4, 2.0, 50, 0.8, GOLD, verts=8)
        ball(p, (x, 10.4, 50), 0.8, GOLD, subdiv=1)
    bx(p, (-26, -12), (5.4, 11.4), (49.3, 49.8), GOLD, 0.03)
    bx(p, (-25.4, -12.6), (5.9, 10.9), (49.6, 50.4), MIDNIGHT, 0.04)
    bx(p, (-25.4, -12.6), (10.6, 10.9), (50.4, 50.6), GOLD, 0.02)
    bx(p, (-25.4, -12.6), (5.9, 6.2), (50.4, 50.6), GOLD, 0.02)
    bx(p, (-25.4, -25.1), (5.9, 10.9), (50.4, 50.6), GOLD, 0.02)
    bx(p, (-12.9, -12.6), (5.9, 10.9), (50.4, 50.6), GOLD, 0.02)
    clock(p, '+z', (-19, 8.4, 50.4), 2.3, s=0.4)
    hands(p, '+z', (-19, 8.4, 50.4), 0.45, 0.8, lh=1.3, lm=1.9, tail=0.4, wh=0.2, wm=0.15, hub_r=0.28)
    for sx in (-22.6, -15.4):
        star_poly(p, (sx, 8.4, 50.5), 'xy', 1.0, 0.45, 0.2, GOLD, n=5)
    gear(p, (-24.2, 6.6, 50.6), 'z', 0.7, 0.2, 8, 0.25, GOLD)
    gear(p, (-13.8, 6.6, 50.6), 'z', 0.7, 0.2, 8, 0.25, GOLD)


# ---- 4. CogGarden ---------------------------------------------------------------------------------------------------------
def build_CogGarden(p):
    gears = [(-66, 50, 5.0, BRASS, 1.8, 14, 2.4), (-58, 47, 3.5, DBRASS, 1.6, 12, 2.2), (-60, 54, 3.0, GOLD, 1.4, 10, 1.8),
             (-71, 44, 3.5, COPPER, 1.6, 12, 2.2)]
    for (x, z, R, col, th, n, hub) in gears:
        ball(p, (x, 0.1, z), R + 0.5, DSTONE, scale=(1, 0.22, 1), subdiv=1, jit=0.06)
        gear(p, (x, th / 2, z), 'y', R, max(0.5, R * 0.14), n, th, col, hole=R * 0.28)
        vcyl(p, x, 0.2, hub, z, R * 0.3, GOLD, verts=10)
        vcyl(p, x, hub - 0.15, hub, z, R * 0.12, STARW, verts=8)
    vcyl(p, -61.5, 0, 1.2, 49.2, 1.7, STONE, verts=10)
    vcyl(p, -61.5, 1.2, 1.4, 49.2, 1.2, GOLD, verts=10)
    for (x, z, r) in ((-64, 44.6, 0.7), (-54.6, 51, 0.6), (-69.5, 51.2, 0.8), (-63.4, 55.5, 0.6)):
        ball(p, (x, 0.4, z), r, STONE, scale=(1, 0.6, 1), subdiv=1, jit=0.08)


# ---- 5. SandBenches -------------------------------------------------------------------------------------------------------
def bench(p, x, z):
    bx(p, (x - 3.5, x + 3.5), (1.3, 1.9), (z - 1.2, z + 1.2), STONE, 0.04)
    bx(p, (x - 3.0, x + 3.0), (1.9, 2.0), (z - 0.9, z + 0.6), MIDNIGHT, 0.03)
    for sx in (-1, 1):
        bx(p, (x + sx * 3.0 - 0.35, x + sx * 3.0 + 0.35), (0.25, 1.3), (z - 1.0, z + 1.0), GOLD, 0.03)
        bx(p, (x + sx * 3.0 - 0.6, x + sx * 3.0 + 0.6), (0, 0.25), (z - 1.2, z + 1.2), DBRASS, 0.03)
        bx(p, (x + sx * 3.4 - 0.2, x + sx * 3.4 + 0.2), (1.9, 4.3), (z + 0.75, z + 1.45), GOLD, 0.03)
        ball(p, (x + sx * 3.4, 4.3, z + 1.1), 0.4, GOLD)
    bx(p, (x - 3.3, x + 3.3), (2.0, 4.1), (z + 0.85, z + 1.35), MIDNIGHT, 0.04)
    bx(p, (x - 3.5, x + 3.5), (4.1, 4.3), (z + 0.8, z + 1.4), GOLD, 0.03)
    clock(p, '+z', (x, 3.05, z + 1.35), 0.95, s=0.25, verts=12)


def build_SandBenches(p):
    bench(p, -42, 41)
    bench(p, -34, 45)


# ---- 6. HourStones --------------------------------------------------------------------------------------------------------
def build_HourStones(p):
    cx, cz, R = -64, 30, 6.5
    heights = [4.2, 3.6, 4.6, 3.6, 4.2, 5.2, 4.2, 3.6, 4.6, 3.6, 4.2, 5.6]
    vcyl(p, cx, 0, 0.5, cz, 3.0, GOLD, verts=12)
    star_poly(p, (cx, 0.53, cz), 'xz', 2.6, 1.3, 0.04, PEARL, n=6)
    bx(p, (cx - 0.45, cx + 0.45), (0.5, 2.1), (cz - 0.45, cz + 0.45), STARW, 0.03)
    pyramid(p, cx, 2.1, 2.4, cz, 0.9, 0.9, GOLD)
    for hr in range(1, 13):
        h = heights[hr - 1]
        a = math.radians(90 - 30 * hr)
        x, z = cx + R * math.cos(a), cz - R * math.sin(a)
        deg = -(math.degrees(a) + 90)
        dk.box(p, (x, (h - 0.5) / 2, z), (2.2, h - 0.5, 1.2), STONE, rot=(0, deg, 0), jitter=0.05)
        dk.box(p, (x, h - 0.25, z), (2.2, 0.5, 1.2), PEARL if hr % 3 else GOLD, rot=(0, deg, 0), jitter=0.03)
        dx, dz = ry(0, 1, deg)
        sgn = 1 if (dx * (cx - x) + dz * (cz - z)) > 0 else -1
        nb = (hr - 1) % 3 + 1
        for i in range(nb):
            lbox(p, x, z, deg, (i - (nb - 1) / 2) * 0.5, h * 0.5, sgn * 0.65, 0.2, min(1.5, h * 0.4), 0.14, GOLD, 0.02)


# ---- 7. SandTimers --------------------------------------------------------------------------------------------------------
def build_SandTimers(p):
    for (x, z) in ((42, 38), (50, 34), (58, 40)):
        lathe(p, x, z, [(1.9, 0), (1.9, 0.5), (1.45, 0.9), (1.45, 1.9), (1.8, 2.2), (1.8, 2.4)], [STONE, STONE, STONE, GOLD, GOLD], verts=10)
        hourglass(p, x, 2.4, z, 1.0, 5.8, plate_r=1.5, post_r=1.2, verts=10)


# ---- 8. Pendulum ----------------------------------------------------------------------------------------------------------
def build_Pendulum(p):
    bx(p, (8, 20), (0, 1), (17.5, 22.5), DSTONE, 0.04)
    bx(p, (8.4, 19.6), (1, 1.3), (17.9, 22.1), GOLD, 0.03)
    for x in (9.5, 18.5):
        bx(p, (x - 0.5, x + 0.5), (1.3, 12), (19.4, 20.6), BRASS, 0.04)
        bx(p, (x - 0.7, x + 0.7), (1.3, 2.0), (19.2, 20.8), GOLD, 0.03)
        ball(p, (x, 13.2, 20), 0.8, GOLD, subdiv=1)
        sgn = -1 if x < 14 else 1
        bar(p, (x + sgn * -0.1, 7, 20), (x + sgn * 2.2, 1.3, 20), 0.45, DBRASS)
    bx(p, (8.5, 19.5), (11.9, 12.9), (19.2, 20.8), GOLD, 0.03)
    bx(p, (13.3, 14.7), (10.9, 11.9), (19.5, 20.5), BRASS, 0.03)
    ball(p, (14, 11.5, 20), 0.6, GOLD, subdiv=1)
    bx(p, (13.85, 14.15), (2.6, 11.5), (19.85, 20.15), GOLD, 0.03)
    zcyl(p, 14, 2.4, 19.55, 20.45, 2.2, GOLD, verts=16)
    zcyl(p, 14, 2.4, 20.45, 20.75, 1.3, PEARL, verts=14)
    star_poly(p, (14, 2.4, 20.8), 'xy', 0.9, 0.4, 0.1, GOLD, n=5)
    gear(p, (9.5, 9.0, 21.0), 'z', 1.4, 0.35, 10, 0.3, GOLD, hole=0.35)
    gear(p, (18.5, 9.0, 21.0), 'z', 1.4, 0.35, 10, 0.3, GOLD, hole=0.35)
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        bx(p, (14 + 4.2 * math.sin(a) - 0.1, 14 + 4.2 * math.sin(a) + 0.1), (0.5 + 0.4 * (1 - math.cos(a)) * 0.0, 0.9), (22.0, 22.4), GOLD, 0.02)


# ---- 9. Astrolabe ---------------------------------------------------------------------------------------------------------
def build_Astrolabe(p):
    lathe(p, 36, 22, [(2.8, 0), (2.8, 1.2), (2.2, 1.4), (2.2, 2.4)], [STONE, GOLD, STONE], verts=14)
    lathe(p, 36, 22, [(1.0, 2.4), (0.55, 3.2), (0.55, 5.2), (1.1, 6.0)], BRASS, verts=10)
    vcyl(p, 36, 6.0, 7.4, 22, 1.1, GOLD, verts=10, top_r=2.0)
    c = (36, 9.6, 22)
    ring3(p, c, 4.7, 0.26, (0, 0, 1), GOLD, segs=22, sides=4)
    ring3(p, c, 4.2, 0.24, (1, 0, 0), BRASS, segs=22, sides=4)
    ring3(p, c, 3.4, 0.2, (0.5, 0.8, 0.33), PEARL, segs=18, sides=4)
    ring3(p, c, 2.6, 0.2, (0.8, 0.0, 0.6), GOLD, segs=16, sides=4)
    ball(p, c, 1.5, VIOLET, subdiv=1)
    star_poly(p, (36, 9.6, 23.3), 'xy', 0.9, 0.4, 0.1, GOLD, n=5)
    vcyl(p, 36, 14.4, 14.9, 22, 0.3, GOLD, verts=6)
    ball(p, (36, 15.0, 22), 0.6, GOLD, subdiv=1)
    for k in range(6):
        a = math.radians(60 * k)
        bx(p, (36 + 4.7 * math.cos(a) - 0.18, 36 + 4.7 * math.cos(a) + 0.18), (9.6 + 4.7 * math.sin(a) - 0.18, 9.6 + 4.7 * math.sin(a) + 0.18), (22.1, 22.5), STARW, 0.02)


# ---- 10. GrandfatherClocks ------------------------------------------------------------------------------------------------
def gclock(p, x, z, h):
    bx(p, (x - 2.2, x + 2.2), (0, 1.0), (z - 1.5, z + 1.5), DSTONE, 0.04)
    bx(p, (x - 2.3, x + 2.3), (1.0, 1.25), (z - 1.6, z + 1.6), GOLD, 0.03)
    bx(p, (x - 1.7, x + 1.7), (1.25, h - 2.4), (z - 1.2, z + 1.2), WOOD, 0.05)
    for sx in (-1, 1):
        bx(p, (x + sx * 1.7 - 0.1, x + sx * 1.7 + 0.1), (1.25, h - 2.4), (z + 1.0, z + 1.3), GOLD, 0.02)
    bx(p, (x - 0.95, x + 0.95), (2.4, h - 4.2), (z + 1.2, z + 1.35), DARK, 0.03)
    bx(p, (x - 0.07, x + 0.07), (2.5, h - 4.3), (z + 1.3, z + 1.4), GOLD, 0.02)
    zcyl(p, x, 3.2, z + 1.3, z + 1.55, 0.6, GOLD, verts=10)
    bx(p, (x - 2.3, x + 2.3), (h - 2.4, h - 0.1), (z - 1.6, z + 1.6), GOLD, 0.03)
    clock(p, '+z', (x, h - 1.25, z + 1.6), 1.0, s=0.3, bez=BRASS, verts=14)
    hands(p, '+z', (x, h - 1.25, z + 1.6), 0.3, 0.45, lh=0.55, lm=0.8, tail=0.2, wh=0.12, wm=0.1, hub_r=0.12)
    dk.prism(p, (x, h - 0.1, z), 3.8, 3.0, 1.3, BRASS, ridge='x')
    ball(p, (x, h + 1.3, z), 0.3, GOLD, subdiv=1)


def build_GrandfatherClocks(p):
    gclock(p, 58, 30, 12)
    gclock(p, 64, 30, 14)
    gclock(p, 70, 30, 12)


# ---- 11. StarObelisks -----------------------------------------------------------------------------------------------------
def obelisk(p, x, z, h):
    bx(p, (x - 2.1, x + 2.1), (0, 0.6), (z - 2.1, z + 2.1), STONE, 0.04)
    bx(p, (x - 1.7, x + 1.7), (0.6, 1.2), (z - 1.7, z + 1.7), PEARL, 0.04)
    frustum(p, x, 1.2, h + 0.8, z, 2.4, 2.4, 1.5, 1.5, DARK, 0.05)
    bx(p, (x - 1.3, x + 1.3), (1.2, 1.6), (z - 1.3, z + 1.3), GOLD, 0.03)
    bx(p, (x - 0.85, x + 0.85), (h + 0.4, h + 0.8), (z - 0.85, z + 0.85), GOLD, 0.03)
    pyramid(p, x, h + 0.8, h + 2.4, z, 1.5, 1.5, GOLD)
    ys = 1.2 + (h - 1) * 0.55
    wz = 1.2 - 0.45 * ((ys - 1.2) / (h - 0.4))
    star_poly(p, (x, ys, z + wz + 0.02), 'xy', 0.62, 0.28, 0.08, GOLD, n=5)
    for k in range(3):
        bx(p, (x - 0.25, x + 0.25), (ys - 2.0 - 0.9 * k - 0.1, ys - 2.0 - 0.9 * k + 0.1), (z + wz - 0.05, z + wz + 0.04), STARW, 0.02)


def build_StarObelisks(p):
    obelisk(p, 68, 46, 15)
    obelisk(p, 60, 52, 11)
    obelisk(p, 74, 38, 11)


# ---- 12. GearFountain -----------------------------------------------------------------------------------------------------
def build_GearFountain(p):
    cx, cz = 40, 2
    lathe(p, cx, cz, [(7.0, 0), (7.0, 1.7), (6.5, 2.0)], [STONE, PEARL], verts=20)
    torus(p, (cx, 1.8, cz), 6.7, 0.3, GOLD, segs=24, sides=4)
    vcyl(p, cx, 1.7, 2.05, cz, 6.1, CYAN, verts=20)
    lathe(p, cx, cz, [(1.5, 2.05), (0.95, 2.6), (0.95, 6.6), (1.5, 7.0)], BRASS, verts=10)
    gear(p, (cx, 7.4, cz), 'y', 4.5, 0.65, 12, 0.8, GOLD, hole=0.9)
    vcyl(p, cx, 7.8, 8.2, cz, 3.0, CYAN, verts=14)
    lathe(p, cx, cz, [(1.0, 8.2), (0.7, 8.7), (0.7, 10.6), (1.0, 11.0)], BRASS, verts=8)
    ball(p, (cx, 11.9, cz), 1.1, GOLD, subdiv=1)
    for sx in (-6, 6):
        gear(p, (cx + sx, 4.0, cz), 'z', 2.5, 0.5, 10, 0.8, BRASS, hole=0.5)
        zcyl(p, cx + sx, 4.0, cz - 0.7, cz + 0.7, 0.6, GOLD, verts=8)
    for k in range(6):
        a = math.radians(60 * k + 20)
        ball(p, (cx + 2.2 * math.cos(a), 9.0, cz + 2.2 * math.sin(a)), 0.28, CYAN, subdiv=0)




# ---- 13. TimeBanners ------------------------------------------------------------------------------------------------------
def banner(p, x, z):
    vcyl(p, x, 0, 0.5, z, 1.0, DBRASS, verts=8)
    vcyl(p, x, 0.5, 14.2, z, 0.35, GOLD, verts=8)
    ball(p, (x, 14.6, z), 0.4, GOLD, subdiv=1)
    bx(p, (x - 0.3, x + 0.3), (14.3, 14.9), (z - 2.6, z + 2.6), GOLD, 0.03)
    for sz in (-2.6, 2.6):
        ball(p, (x, 14.6, z + sz), 0.4, GOLD, subdiv=1)
    bx(p, (x + 0.05, x + 0.35), (8.0, 14.0), (z - 2.0, z + 2.0), MIDNIGHT, 0.04)
    prism_x(p, [(8.0, z - 2.0), (8.0, z + 2.0), (6.0, z)], x + 0.05, x + 0.35, MIDNIGHT, 0.04)
    bx(p, (x + 0.05, x + 0.4), (13.6, 14.0), (z - 2.0, z + 2.0), GOLD, 0.02)
    bx(p, (x + 0.05, x + 0.4), (8.0, 13.6), (z - 2.0, z - 1.8), GOLD, 0.02)
    bx(p, (x + 0.05, x + 0.4), (8.0, 13.6), (z + 1.8, z + 2.0), GOLD, 0.02)
    prism_x(p, [(8.0, z - 2.0), (8.0, z - 1.8), (6.4, z - 0.1)], x + 0.05, x + 0.4, GOLD, 0.02)
    prism_x(p, [(8.0, z + 2.0), (8.0, z + 1.8), (6.4, z + 0.1)], x + 0.05, x + 0.4, GOLD, 0.02)
    clock(p, '+x', (x + 0.35, 10.6, z), 1.35, s=0.2, verts=14)
    hands(p, '+x', (x + 0.35, 10.6, z), 0.2, 0.3, lh=0.7, lm=1.0, tail=0.25, wh=0.14, wm=0.1, hub_r=0.16)


def build_TimeBanners(p):
    for z in (20, 28, 36):
        banner(p, -74, z)


# ---- 14. CuckooHouse ------------------------------------------------------------------------------------------------------
def build_CuckooHouse(p):
    bx(p, (-48, -40), (0, 7), (46.5, 53.5), WOOD, 0.07)
    bx(p, (-48.1, -39.9), (0, 0.5), (46.4, 53.6), DWOOD, 0.04)
    prism_z(p, [(-48, 7), (-40, 7), (-44, 10.2)], 46.6, 53.4, WOOD, 0.05)
    for sx in (-1, 1):
        B(p, -44 + sx * 2.3, 8.5, 50, 5.6, 0.8, 8.6, GOLD, rot=(0, 0, -sx * 36), jit=0.04)
        for k in range(3):
            t = -1.6 + 1.6 * k
            B(p, -44 + sx * (2.3 + t * 0.809 * 0.0 + 0.0) + sx * t * 0.809 * 0 + 0, 8.5, 50, 0.01, 0.01, 0.01, GOLD, jit=0.0) if False else None
        for k in range(3):
            off = -1.5 + 1.5 * k
            dx = off * math.cos(math.radians(36)) * sx
            dy = -off * math.sin(math.radians(36)) * sx * sx * (-1 if sx < 0 else 1) * -1
            B(p, -44 + sx * 2.3 + dx + sx * 0.0, 8.5 + 0.0 + (0.588 * off) + 0.44 * 0.0, 50, 0.3, 0.9, 8.7, DBRASS, rot=(0, 0, -sx * 36), jit=0.03) if False else None
    bx(p, (-44.25, -43.75), (10.1, 10.5), (45.7, 54.3), DBRASS, 0.03)
    clock(p, '+z', (-44, 8.0, 53.5), 1.45, s=0.4, verts=14)
    hands(p, '+z', (-44, 8.0, 53.5), 0.4, 0.55, lh=0.75, lm=1.1, tail=0.3, wh=0.16, wm=0.12, hub_r=0.18)
    bx(p, (-45.2, -42.8), (0.1, 4.6), (53.5, 53.9), DWOOD, 0.04)
    zcyl(p, -44, 4.6, 53.5, 53.9, 1.2, DWOOD, verts=12)
    bx(p, (-45.5, -42.5), (0, 0.3), (53.4, 54.2), GOLD, 0.03)
    for sx in (-1.45, 1.45):
        bx(p, (-44 + sx - 0.12, -44 + sx + 0.12), (0.3, 4.4), (53.9, 54.05), GOLD, 0.02)
    ball(p, (-43.3, 2.2, 54.0), 0.18, GOLD, subdiv=0)
    bx(p, (-45.2, -42.8), (4.6, 5.0), (53.5, 54.7), GOLD, 0.03)
    ball(p, (-44, 5.7, 54.0), 0.5, CYAN, subdiv=1)
    bx(p, (-44.15, -43.85), (5.55, 5.75), (54.3, 54.6), GOLD, 0.02)
    ball(p, (-44, 6.3, 54.05), 0.3, CYAN, subdiv=1)
    for x in (-41.4, -46.6):
        vcyl(p, x, 1.3, 4.6, 53.8, 0.13, GOLD, verts=4, jit=0.02)
        ball(p, (x, 0.5, 53.8), 0.6, BRASS, scale=(1, 1.15, 1), subdiv=1)
    for sx in (-1, 1):
        fbox(p, '+x' if sx > 0 else '-x', (-44 + sx * 4.0, 3.8, 50), -0.9, 0.9, -1.0, 1.0, 0, 0.12, GOLD, 0.02)
        fbox(p, '+x' if sx > 0 else '-x', (-44 + sx * 4.0, 3.8, 50), -0.7, 0.7, -0.8, 0.8, 0.12, 0.2, STARW, 0.02)
    bx(p, (-40.9, -39.2), (3.5, 4.0), (45.7, 46.0), GOLD, 0.03)


# ---- 15. StarPond ---------------------------------------------------------------------------------------------------------
def build_StarPond(p):
    bx(p, (58, 78), (0.05, 0.5), (-2.5, 10.5), MIDNIGHT, 0.04)
    bx(p, (59, 77), (0.4, 0.5), (-1.5, 9.5), INDIGO, 0.08)
    bx(p, (57.4, 78.6), (0, 1.5), (-3.1, -1.9), GOLD, 0.03)
    bx(p, (57.4, 78.6), (0, 1.5), (9.9, 11.1), GOLD, 0.03)
    bx(p, (57.2, 58.4), (0, 1.5), (-1.9, 9.9), GOLD, 0.03)
    bx(p, (77.6, 78.8), (0, 1.5), (-1.9, 9.9), GOLD, 0.03)
    for (x, z) in ((57.8, -2.5), (78.2, -2.5), (57.8, 10.5), (78.2, 10.5)):
        bx(p, (x - 0.8, x + 0.8), (0, 1.5), (z - 0.8, z + 0.8), STONE, 0.04)
    for (x, z, r, col) in ((64, 2, 1.5, GOLD), (71, 6, 1.8, GOLD), (68, 3, 1.1, STARW), (63, 7, 1.1, STARW)):
        vcyl(p, x, 0.45, 0.6, z, r, col, verts=12)
        vcyl(p, x, 0.45, 0.62, z, r * 0.72, PEARL if col == GOLD else GOLD, verts=12)
        bx(p, (x - 0.07, x + 0.07), (0.62, 0.66), (z - 0.1, z + r * 0.6), DARK, 0.0)
    for k, (x, z) in enumerate(((60.5, 0), (62, 8.5), (66, 7.5), (70, 0.5), (74, 3), (75.5, 8), (72.5, 8.5), (67, 5.5))):
        B(p, x, 0.55, z, 0.8, 0.06, 0.8, STARW if k % 2 else CYAN, rot=(0, 45, 0), jit=0.02)


# ---- 16. ZodiacWheel ------------------------------------------------------------------------------------------------------
def build_ZodiacWheel(p):
    bx(p, (42.5, 53.5), (0, 1.2), (11.5, 16.5), DSTONE, 0.04)
    bx(p, (42.8, 53.2), (1.2, 1.5), (12, 16), GOLD, 0.03)
    for x in (42.6, 53.4):
        bx(p, (x - 0.45, x + 0.45), (1.2, 11), (13.4, 14.6), BRASS, 0.04)
        ball(p, (x, 12, 14), 0.8, GOLD, subdiv=1)
        bar(p, (x, 3.5, 14), (x - 0.0 + (-1.6 if x < 48 else 1.6), 1.2, 14), 0.5, DBRASS)
    c = (48, 10.5, 14)
    ring3(p, c, 7.4, 0.6, (0, 0, 1), GOLD, segs=24, sides=6)
    zcyl(p, 48, 10.5, 14.1, 14.9, 6.7, MIDNIGHT, verts=24)
    ring3(p, (48, 10.5, 14.9), 6.4, 0.18, (0, 0, 1), GOLD, segs=24, sides=4)
    for k in range(3):
        B(p, 48, 10.5, 15.2, 12, 0.5, 0.4, GOLD, rot=(0, 0, 60 * k), jit=0.02)
    for k in range(12):
        a = math.radians(30 * k)
        B(p, 48 + 5.2 * math.cos(a), 10.5 + 5.2 * math.sin(a), 15.05, 0.9, 0.9, 0.3, PEARL if k % 2 else GOLD, rot=(0, 0, 45), jit=0.02)
    zcyl(p, 48, 10.5, 14.6, 15.4, 1.6, GOLD, verts=12)
    zcyl(p, 48, 10.5, 15.3, 15.5, 0.8, STARW, verts=10)
    star_poly(p, (48, 10.5, 15.0), 'xy', 3.4, 1.7, 0.2, VIOLET, n=6, rot0=90)
    zcyl(p, 48, 10.5, 14.6, 15.4, 1.6, GOLD, verts=12)
    zcyl(p, 48, 10.5, 15.3, 15.5, 0.8, STARW, verts=10)


# ---- 17. RuneCircle -------------------------------------------------------------------------------------------------------
def build_RuneCircle(p):
    cx, cz = -58, -4
    vcyl(p, cx, 0, 0.5, cz, 9.5, MIDNIGHT, verts=22)
    vcyl(p, cx, 0.5, 0.56, cz, 8.6, GOLD, verts=22)
    vcyl(p, cx, 0.5, 0.58, cz, 8.0, INDIGO, verts=22)
    vcyl(p, cx, 0.5, 0.58, cz, 4.0, GOLD, verts=14)
    star_poly(p, (cx, 0.61, cz), 'xz', 3.6, 1.8, 0.04, PEARL, n=6)
    for k in range(6):
        d = 60 * k
        a = math.radians(d)
        x, z = cx + 7 * math.cos(a), cz + 7 * math.sin(a)
        frustum(p, x, 0, 6, z, 1.8, 1.8, 1.3, 1.3, DSTONE, 0.06)
        frustum(p, x, 6, 7, z, 2.4, 2.4, 1.4, 1.4, GOLD, 0.03)
        ry_ = -(d + 90)
        lbox(p, x, z, ry_, 0, 3.6, 0.78, 0.18, 2.2, 0.14, PEARL, 0.02)
        lbox(p, x, z, ry_, 0.3, 4.2, 0.78, 0.5, 0.15, 0.14, PEARL, 0.02)
        lbox(p, x, z, ry_, -0.3, 3.0, 0.78, 0.5, 0.15, 0.14, PEARL, 0.02)
        lbox(p, x, z, ry_, 0.0, 5.2, 0.7, 0.3, 0.3, 0.14, GOLD, 0.02)
    lathe(p, cx, cz, [(0.02, 8.0), (1.5, 9.5), (0.02, 11.0)], [STARW, VIOLET], verts=6, jit=0.05)
    for k in range(3):
        a = math.radians(120 * k + 30)
        ball(p, (cx + 3.2 * math.cos(a), 9.5 + 0.9 * math.sin(a * 2), cz + 3.2 * math.sin(a)), 0.35, GOLD, subdiv=0)


# ---- 18. CogGate ----------------------------------------------------------------------------------------------------------
def build_CogGate(p):
    cx, cz = -22, 28.7
    for z in (17.7, 39.7):
        s = 1 if z < cz else -1
        bx(p, (cx - 2.2, cx + 2.2), (0, 2), (z - 2.2, z + 2.2), STONE, 0.04)
        bx(p, (cx - 1.3, cx + 1.3), (2, 15), (z - 1.3, z + 1.3), DARK, 0.05)
        for (a, b) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            bx(p, (cx + a * 1.3 - 0.15, cx + a * 1.3 + 0.15), (2.4, 14.6), (z + b * 1.3 - 0.15, z + b * 1.3 + 0.15), PEARL, 0.03)
        for y in (4.5, 9.0):
            bx(p, (cx - 1.55, cx + 1.55), (y, y + 0.4), (z - 1.55, z + 1.55), GOLD, 0.03)
        frustum(p, cx, 14.8, 16.0, z, 3.4, 3.4, 2.8, 2.8, GOLD, 0.03)
        ball(p, (cx, 11.3, z + s * 1.9), 0.75, STARW, subdiv=1)
        bx(p, (cx - 0.12, cx + 0.12), (10.6, 11.3), (z + s * 1.3, z + s * 1.9), GOLD, 0.02)
    bx(p, (cx - 1.2, cx + 1.2), (16.1, 18.3), (16.2, 41.2), GOLD, 0.03)
    bx(p, (cx - 1.0, cx + 1.0), (18.3, 18.7), (18.2, 39.2), DBRASS, 0.02)
    gear(p, (cx, 22, cz), 'x', 6.0, 1.1, 14, 1.5, BRASS, hole=2.0)
    ring3(p, (cx, 22, cz), 3.6, 0.3, (1, 0, 0), GOLD, segs=16, sides=4)
    xcyl(p, cx - 1.1, cx + 1.1, 22, cz, 1.7, GOLD, verts=10)
    xcyl(p, cx - 1.15, cx + 1.15, 22, cz, 0.7, STARW, verts=8)
    for k in range(6):
        a = math.radians(60 * k + 30)
        bar(p, (cx, 22 + 1.6 * math.sin(a), cz + 1.6 * math.cos(a)), (cx, 22 + 3.6 * math.sin(a), cz + 3.6 * math.cos(a)), 0.55, DBRASS)
    for s in (-1, 1):
        gear(p, (cx, 22.0, cz + s * 8.4), 'x', 2.2, 0.5, 8, 1.2, GOLD, hole=0.5)


# ---- 19. BellArch ---------------------------------------------------------------------------------------------------------
def build_BellArch(p):
    bx(p, (-78, -66), (0, 0.8), (10, 14), STONE, 0.04)
    bx(p, (-77.2, -66.8), (0.8, 1.1), (10.4, 13.6), GOLD, 0.03)
    for x in (-76, -68):
        bx(p, (x - 0.7, x + 0.7), (1.1, 11.4), (11.3, 12.7), BRASS, 0.04)
        bx(p, (x - 1.0, x + 1.0), (1.1, 1.8), (11.0, 13.0), GOLD, 0.03)
        ball(p, (x, 12.2, 12), 0.8, GOLD, subdiv=1)
    arc_strip(p, -72, 10.9, 5.2, 2.2, 4.5, 1.5, 11.2, 12.8, GOLD, n=14)
    for (x, top, bot, r, col) in ((-74.6, 9.5, 6.1, 1.3, GOLD), (-72, 9.3, 5.1, 1.7, BRASS), (-69.4, 9.5, 6.1, 1.3, GOLD)):
        hgt = top - bot
        lathe(p, x, 12, [(r, bot), (r * 0.9, bot + hgt * 0.16), (r * 0.62, bot + hgt * 0.5), (r * 0.4, bot + hgt * 0.82), (r * 0.25, top)],
              [DBRASS, col, col, col], verts=10)
        ball(p, (x, bot - 0.05, 12), 0.38, DBRASS, subdiv=1)
        inner = 10.9 + 1.5 * math.sqrt(max(0.0, 1 - ((x + 72) / 4.5) ** 2)) - 0.1
        bx(p, (x - 0.08, x + 0.08), (top, inner), (11.9, 12.1), GOLD, 0.02)


# ---- 20. Sentinel ---------------------------------------------------------------------------------------------------------
def build_Sentinel(p):
    x0, z0 = 68, -18
    bx(p, (63.5, 72.5), (0, 0.8), (-22.5, -13.5), STONE, 0.04)
    bx(p, (64.3, 71.7), (0.8, 1.4), (-21.7, -14.3), PEARL, 0.03)
    for sx in (66.4, 69.6):
        bx(p, (sx - 1.1, sx + 1.1), (1.4, 2.0), (-19.4, -16.4), DBRASS, 0.03)
        bx(p, (sx - 0.7, sx + 0.7), (2.0, 5.2), (-18.7, -17.3), BRASS, 0.04)
        bx(p, (sx - 0.9, sx + 0.9), (3.2, 3.6), (-18.9, -17.1), GOLD, 0.03)
    bx(p, (65.4, 70.6), (5.0, 5.8), (-19.0, -17.0), DBRASS, 0.03)
    frustum(p, x0, 5.8, 10.6, z0, 5.0, 3.4, 5.4, 3.6, BRASS, 0.04)
    bx(p, (66.3, 69.7), (6.4, 10.2), (-16.35, -16.2), DBRASS, 0.03)
    clock(p, '+z', (x0, 8.4, -16.2), 1.6, s=0.3, verts=14)
    hands(p, '+z', (x0, 8.4, -16.2), 0.3, 0.45, lh=0.8, lm=1.15, tail=0.25, wh=0.14, wm=0.1, hub_r=0.15)
    for sx in (-1, 1):
        gear(p, (x0 + sx * 3.0, 9.8, z0), 'x', 1.3, 0.3, 8, 0.7, GOLD, hole=0.3)
        bx(p, (x0 + sx * 3.0 - 0.7, x0 + sx * 3.0 + 0.7), (6.2, 9.0), (-18.8, -17.2), BRASS, 0.04)
        bx(p, (x0 + sx * 3.0 - 0.75, x0 + sx * 3.0 + 0.75), (8.2, 8.5), (-18.85, -17.15), GOLD, 0.03)
        ball(p, (x0 + sx * 3.0, 6.4, z0), 0.7, DBRASS, subdiv=1)
    bx(p, (67.2, 68.8), (10.6, 11.1), (-18.6, -17.4), DBRASS, 0.03)
    ball(p, (x0, 12.6, z0), 1.7, BRASS, scale=(1.12, 1.0, 1.0), subdiv=2)
    bx(p, (66.7, 69.3), (12.45, 13.15), (-16.5, -16.1), CYAN, 0.02)
    for sx in (-1, 1):
        xcyl(p, x0 + sx * 1.8, x0 + sx * 2.1, 12.4, z0, 0.7, GOLD, verts=8)
    vcyl(p, x0, 14.2, 15.0, z0, 0.2, GOLD, verts=6)
    star_poly(p, (x0, 15.3, z0), 'xy', 0.6, 0.25, 0.1, STARW, n=4)
    gear(p, (x0, 8.6, -20.0), 'z', 2.5, 0.5, 10, 0.8, GOLD, hole=0.5)
    zcyl(p, x0, 8.6, -20.4, -19.6, 0.7, DBRASS, verts=8)


# ---- 21. GiantSundial -----------------------------------------------------------------------------------------------------
def build_GiantSundial(p):
    cx, cz = -18, -51
    vcyl(p, cx, 0, 1.0, cz, 6.0, STONE, verts=24)
    vcyl(p, cx, 0.95, 1.34, cz, 5.0, GOLD, verts=24)
    vcyl(p, cx, 0.95, 1.36, cz, 4.6, PEARL, verts=24)
    for k in range(12):
        a = math.radians(30 * k)
        c1, s1 = math.cos(a), math.sin(a)
        r0 = 3.5 if k % 3 == 0 else 3.9
        B(p, cx + (r0 + 4.6) / 2 * c1, 1.42, cz + (r0 + 4.6) / 2 * s1, 4.6 - r0, 0.12, 0.3 if k % 3 else 0.5, GOLD, rot=(0, -30 * k, 0), jit=0.02)
        B(p, cx + 2.8 * c1, 1.4, cz + 2.8 * s1, 0.4, 0.08, 0.4, DARK, rot=(0, -30 * k, 0), jit=0.02)
    star_poly(p, (cx, 1.4, cz), 'xz', 1.6, 0.7, 0.06, GOLD, n=8)
    bx(p, (cx - 1.0, cx + 1.0), (1.3, 1.8), (cz - 2.7, cz + 1.8), DBRASS, 0.03)
    prism_x(p, [(1.1, cz - 2.2), (1.1, cz + 2.2), (5.1, cz + 2.2)], cx - 0.4, cx + 0.4, GOLD, 0.03)
    bx(p, (cx - 0.45, cx + 0.45), (4.4, 5.1), (cz + 1.85, cz + 2.2), BRASS, 0.03)


# ---- 22. TimeThrone -------------------------------------------------------------------------------------------------------
def build_TimeThrone(p):
    cx, cz = 68, -42
    vcyl(p, cx, 0, 1.6, cz, 9.0, PEARL, verts=20)
    vcyl(p, cx, 1.6, 3.2, cz, 6.5, STARW, verts=20)
    vcyl(p, cx, 3.2, 4.8, cz, 4.0, PEARL, verts=16)
    torus(p, (cx, 1.6, cz), 8.7, 0.22, GOLD, segs=24, sides=4)
    torus(p, (cx, 3.2, cz), 6.3, 0.2, GOLD, segs=20, sides=4)
    star_poly(p, (cx, 1.63, cz), 'xz', 7.6, 5.6, 0.04, GOLD, n=12)
    bx(p, (65.7, 70.3), (4.8, 6.2), (-45.2, -40.8), GOLD, 0.03)
    bx(p, (66.2, 69.8), (6.2, 6.8), (-44.8, -41.2), VIOLET, 0.05)
    for sx in (65.3, 70.7):
        bx(p, (sx - 0.4, sx + 0.4), (5.0, 8.4), (-44.8, -41.4), GOLD, 0.03)
        ball(p, (sx, 8.2, -41.4), 0.55, GOLD, subdiv=1)
    bx(p, (65.5, 70.5), (5.8, 13.2), (-45.8, -44.6), GOLD, 0.03)
    bx(p, (66.2, 69.8), (6.6, 12.6), (-44.65, -44.55), INDIGO, 0.04)
    frustum(p, cx, 13.2, 14.2, -45.2, 5.0, 1.2, 1.2, 1.2, GOLD, 0.03)
    clock(p, '+z', (cx, 12.6, -46.4), 3.7, s=0.5, verts=18)
    ring3(p, (cx, 12.6, -46.2), 4.2, 0.4, (0, 0, 1), GOLD, segs=24, sides=6)
    hands(p, '+z', (cx, 12.6, -46.4), 0.5, 0.65, lh=1.9, lm=2.7, tail=0.6, wh=0.3, wm=0.22, hub_r=0.35)
    for sx in (59.4, 76.6):
        lathe(p, sx, cz, [(1.1, 0), (1.1, 0.7), (0.55, 0.9), (0.55, 11.4)], [STONE, STONE, GOLD], verts=8)
        for y in (3.0, 6.0, 9.0):
            vcyl(p, sx, y, y + 0.3, cz, 0.95, DBRASS, verts=8)
        ball(p, (sx, 12.8, cz), 1.1, STARW, subdiv=1)


# ---- 23. Orrery -----------------------------------------------------------------------------------------------------------
def build_Orrery(p):
    cx, cz = -18, -37.5
    lathe(p, cx, cz, [(4.0, 0), (4.0, 1.2), (3.2, 1.6), (1.4, 2.0)], [STONE, GOLD, STONE], verts=14)
    lathe(p, cx, cz, [(1.2, 2.0), (0.7, 3.0), (0.7, 5.6), (1.2, 6.4)], BRASS, verts=10)
    torus(p, (cx, 8.6, cz), 6.0, 0.28, GOLD, segs=26, sides=4)
    torus(p, (cx, 9.4, cz), 3.9, 0.22, BRASS, segs=20, sides=4)
    ring3(p, (cx, 8.8, cz), 5.0, 0.2, (0.3, 1, 0.2), PEARL, segs=22, sides=4)
    ball(p, (cx, 8.6, cz), 2.2, GOLD, subdiv=2)
    for k in range(8):
        a = math.radians(45 * k)
        vcyl(p, cx + 2.2 * math.cos(a), 8.5, 8.6 + 1.0, cz + 2.2 * math.sin(a), 0.3, LGOLD, verts=4, jit=0.02) if False else None
    planets = [((-12.6, 9, -37.5), 0.9, VIOLET), ((-22.6, 9, -34), 0.75, CYAN), ((-15, 9.8, -42), 0.65, STARW),
               ((-24, 9.8, -39), 0.8, COPPER), ((-18, 10.2, -33), 0.6, PEARL)]
    for (pos, r, col) in planets:
        bar(p, (cx, 8.6, cz), pos, 0.14, DBRASS)
        ball(p, pos, r, col, subdiv=1)
    ball(p, (-12.6 - 0.1, 9.2, -37.5), 0.3, GOLD, subdiv=0) if False else None


# ---- 24. Engine -----------------------------------------------------------------------------------------------------------
def build_Engine(p):
    bx(p, (-23, -9), (0, 2), (-27.5, -16.5), DSTONE, 0.04)
    bx(p, (-22.5, -9.5), (2, 2.4), (-27, -17), GOLD, 0.03)
    bx(p, (-22, -10), (2.4, 10), (-26.5, -17.5), DARK, 0.05)
    for (x, z) in ((-22, -26.5), (-10, -26.5), (-22, -17.5), (-10, -17.5)):
        bx(p, (x - 0.6, x + 0.6), (2.4, 10), (z - 0.6, z + 0.6), GOLD, 0.03)
    bx(p, (-22.5, -9.5), (10, 10.8), (-27, -17), GOLD, 0.03)
    for sx, c in ((1, '+x'), (-1, '-x')):
        for z in (-24.2, -19.8):
            fbox(p, c, (-16 + sx * 6, 6.5, z), -1.0, 1.0, -1.6, 1.6, 0, 0.1, GOLD, 0.02)
            fbox(p, c, (-16 + sx * 6, 6.5, z), -0.8, 0.8, -1.4, 1.4, 0.1, 0.18, STARW, 0.02)
    pyramid(p, -16, 10.8, 12.2, -22, 4.0, 4.0, GOLD)
    for (cx_, y, col, R, n, hub) in ((-18.4, 6.4, BRASS, 4.0, 12, 1.2), (-12.2, 8.4, GOLD, 2.5, 9, 0.8), (-12.2, 4.0, COPPER, 2.0, 8, 0.6)):
        gear(p, (cx_, y, -17.2), 'z', R, R * 0.2, n, 1.0, col, hole=R * 0.3)
        zcyl(p, cx_, y, -17.4, -16.6 if hub < 1 else -15.8, hub, GOLD if col != GOLD else DBRASS, verts=10)
    lathe(p, -20.4, -24, [(1.2, 10.4), (1.2, 15.2), (1.5, 15.4), (1.5, 16.2)], [COPPER, COPPER, GOLD], verts=10)
    vcyl(p, -20.4, 12.4, 12.8, -24, 1.5, GOLD, verts=10)
    lathe(p, -11, -25, [(0.8, 10.6), (0.8, 14.2), (1.2, 14.6), (1.2, 15.4)], [BRASS, BRASS, GOLD], verts=8)
    zcyl(p, -22.6, 3.0, -24, -20, 1.2, COPPER, verts=10)
    for z in (-23.5, -20.5):
        zcyl(p, -22.6, 3.0, z - 0.15, z + 0.15, 1.3, GOLD, verts=10)
    xcyl(p, -10.3, -8.5, 3.6, -22, 0.7, BRASS, verts=8)
    for x in (-10.0, -9.6, -9.2, -8.8):
        ring3(p, (x, 3.6, -22), 0.9, 0.12, (1, 0, 0), GOLD, segs=8, sides=4)
    for k in range(3):
        ball(p, (-14 + 2.0 * k, 11.4, -23.5), 0.3, STARW, subdiv=0)




# ---- 25. ClockBase --------------------------------------------------------------------------------------------------------
def build_ClockBase(p):
    bx(p, (-63, -37), (0, 2), (-47, -21), STONE, 0.04)
    bx(p, (-61, -39), (2, 4), (-45, -23), PEARL, 0.04)
    bx(p, (-58, -42), (4, 14), (-42, -26), MIDNIGHT, 0.05)
    bx(p, (-58.5, -41.5), (13.2, 14), (-42.5, -25.5), PEARL, 0.03)
    bx(p, (-59, -41), (14, 15), (-43, -25), GOLD, 0.03)
    for (x, z) in ((-57.6, -41.6), (-42.4, -41.6), (-57.6, -26.4), (-42.4, -26.4)):
        bx(p, (x - 1.2, x + 1.2), (5, 13.5), (z - 1.2, z + 1.2), STARW, 0.03)
        bx(p, (x - 1.4, x + 1.4), (4.6, 5.3), (z - 1.4, z + 1.4), GOLD, 0.03)
        bx(p, (x - 1.4, x + 1.4), (13.4, 14.0), (z - 1.4, z + 1.4), GOLD, 0.03)
    bx(p, (-53.3, -46.7), (4, 10.5), (-26, -25.4), GOLD, 0.03)
    zcyl(p, -50, 8.7, -26, -25.4, 3.3, GOLD, verts=14)
    bx(p, (-52.2, -47.8), (4, 8.7), (-25.7, -25.1), DWOOD, 0.04)
    zcyl(p, -50, 8.7, -25.7, -25.1, 2.2, DWOOD, verts=12)
    bx(p, (-50.08, -49.92), (4, 10.9), (-25.1, -25.0), GOLD, 0.02)
    gear(p, (-50, 8.4, -25.15), 'z', 1.3, 0.3, 10, 0.2, GOLD, hole=0.3)
    for sx in (-4.2, 4.2):
        bx(p, (-50 + sx - 0.12, -50 + sx + 0.12), (6.0, 6.5), (-25.4, -24.8), GOLD, 0.02)
        ball(p, (-50 + sx, 6.5, -24.6), 0.8, STARW, subdiv=1)
    for sx in (-5.6, 5.6):
        fbox(p, '+z', (-50, 9.0, -26), sx - 0.9, sx + 0.9, -1.7, 1.7, 0, 0.1, GOLD, 0.02)
        fbox(p, '+z', (-50, 9.0, -26), sx - 0.7, sx + 0.7, -1.5, 1.5, 0.1, 0.18, STARW, 0.02)
    for f, c in (('+x', (-42, 9, -34)), ('-x', (-58, 9, -34))):
        for u in (-3.5, 3.5):
            fbox(p, f, c, u - 1.0, u + 1.0, -2.0, 2.0, 0, 0.12, GOLD, 0.02)
            fbox(p, f, c, u - 0.75, u + 0.75, -1.75, 1.75, 0.12, 0.2, STARW, 0.02)
    gear(p, (-58.05, 10.0, -34), 'x', 1.6, 0.35, 10, 0.2, GOLD, hole=0.3)
    gear(p, (-41.95, 10.0, -34), 'x', 1.6, 0.35, 10, 0.2, GOLD, hole=0.3)


# ---- 26. TowerShaft -------------------------------------------------------------------------------------------------------
def build_TowerShaft(p):
    cx, cz = -50, -34
    bx(p, (-55, -45), (15, 35), (-39, -29), MIDNIGHT, 0.05)
    for y0, y1 in ((17.0, 17.8), (24.6, 25.4), (33.8, 35.0)):
        bx(p, (-55.7, -44.3), (y0, y1), (-39.7, -28.3), GOLD, 0.03)
    for (x, z) in ((-55.2, -39.2), (-44.8, -39.2), (-55.2, -28.8), (-44.8, -28.8)):
        bx(p, (x - 0.6, x + 0.6), (15.4, 33.8), (z - 0.6, z + 0.6), PEARL, 0.03)
        bx(p, (x - 0.7, x + 0.7), (15.0, 15.6), (z - 0.7, z + 0.7), GOLD, 0.03)
    pent = [(-1.5, -2.2), (1.5, -2.2), (1.5, 0.9), (0, 2.2), (-1.5, 0.9)]
    pane = [(-1.1, -1.9), (1.1, -1.9), (1.1, 0.8), (0, 1.8), (-1.1, 0.8)]
    for f, c in (('+z', (cx, 0, -29)), ('-z', (cx, 0, -39)), ('+x', (-45, 0, cz)), ('-x', (-55, 0, cz))):
        for y in (21.0, 29.6):
            cc = (c[0], y, c[2])
            fpoly(p, f, cc, pent, 0, 0.3, GOLD, 0.02)
            fpoly(p, f, cc, pane, 0.3, 0.5, STARW, 0.02)
            fbox(p, f, cc, -0.07, 0.07, -1.9, 1.7, 0.5, 0.55, GOLD, 0.02)
        for u in (-3.2, 3.2):
            fbox(p, f, (c[0], 25, c[2]), u - 0.08, u + 0.08, -8.6, 8.6, 0, 0.06, NAVY, 0.02)
        star_poly(p, face_pt(f, (c[0], 25, c[2]), 0, 0, 0.0), 'xy' if f[1] == 'z' else 'yz', 0.01, 0.005, 0.01, GOLD, n=4) if False else None


# ---- 27. ClockFace --------------------------------------------------------------------------------------------------------
def build_ClockFace(p):
    cx, cz = -50, -34
    frustum(p, cx, 35.0, 36.6, cz, 10, 10, 12, 12, GOLD, 0.03)
    frustum(p, cx, 36.6, 38.2, cz, 12, 12, 14, 14, PEARL, 0.03)
    bx(p, (-58, -42), (38.2, 52), (-42, -26), INDIGO, 0.05)
    for (x, z) in ((-57.7, -41.7), (-42.3, -41.7), (-57.7, -26.3), (-42.3, -26.3)):
        bx(p, (x - 0.7, x + 0.7), (38.2, 51.8), (z - 0.7, z + 0.7), PEARL, 0.03)
    for f, c in (('+z', (cx, 44, -26)), ('-z', (cx, 44, -42)), ('+x', (-42, 44, cz)), ('-x', (-58, 44, cz))):
        clock(p, f, c, 6.4, s=0.8, verts=14)
    bx(p, (-59, -41), (51.3, 52.7), (-43, -25), GOLD, 0.03)
    frustum(p, cx, 52.7, 55.7, cz, 13, 13, 9, 9, DARK, 0.04)
    frustum(p, cx, 55.7, 58.3, cz, 8, 8, 2.5, 2.5, NAVY, 0.04)
    vcyl(p, cx, 58.3, 62.9, cz, 0.6, GOLD, verts=8, top_r=0.25)
    ball(p, (cx, 63.4, cz), 1.0, STARW, subdiv=1)
    for (x, z) in ((-57.8, -41.8), (-42.2, -41.8), (-57.8, -26.2), (-42.2, -26.2)):
        vcyl(p, x, 52.7, 55.0, z, 0.8, GOLD, verts=6, top_r=0.05)


# ---- 28. ClockHands -------------------------------------------------------------------------------------------------------
def build_ClockHands(p):
    for f, c in (('+z', (-50, 44, -26)), ('-z', (-50, 44, -42)), ('+x', (-42, 44, -34)), ('-x', (-58, 44, -34))):
        hands(p, f, c, 0.85, 1.35, lh=3.6, lm=5.0, tail=1.0, wh=0.45, wm=0.35, hub_r=0.7)


# ---- 29. GearRing ---------------------------------------------------------------------------------------------------------
def build_GearRing(p):
    cx, cz = -50, -34
    gear(p, (cx, 24, cz), 'y', 17.5, 1.5, 20, 1.4, BRASS, hole=11.0, jit=0.05)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        B(p, cx + 14.0 * math.cos(a), 24.7, cz + 14.0 * math.sin(a), 1.6, 0.1, 1.6, STARW, rot=(0, 45 - 45 * k, 0), jit=0.02)
    for (dx, dz) in ((-10.4, 0), (10.4, 0), (0, -10.4), (0, 10.4)):
        gear(p, (cx + dx, 27.6, cz + dz), 'y', 4.0, 0.7, 8, 1.2, GOLD, hole=0.8)
        vcyl(p, cx + dx, 27.0, 29.0, cz + dz, 1.0, DBRASS, verts=8)


# ---- 30. Hourglass --------------------------------------------------------------------------------------------------------
def build_Hourglass(p):
    cx, cz = -50, -34
    hourglass(p, cx, 68.0, cz, 4.5, 22.0, plate_r=6.0, post_r=5.5, verts=14)
    vcyl(p, cx, 90.0, 91.3, cz, 0.3, GOLD, verts=6)
    ball(p, (cx, 92.4, cz), 1.1, GOLD, subdiv=1)
    spark(p, (-58.4, 82, cz), 1.5, STARW)
    spark(p, (-58.4, 82, cz), 1.5, STARW, plane='yz')
    spark(p, (-41.6, 76, cz), 1.5, STARW)
    spark(p, (-41.6, 76, cz), 1.5, STARW, plane='yz')


PART_IDS = ["Ground", "StarLamps", "TimeSign", "CogGarden", "SandBenches", "HourStones", "SandTimers", "Pendulum", "Astrolabe",
            "GrandfatherClocks", "StarObelisks", "GearFountain", "TimeBanners", "CuckooHouse", "StarPond", "ZodiacWheel",
            "RuneCircle", "CogGate", "BellArch", "Sentinel", "GiantSundial", "TimeThrone", "Orrery", "Engine", "ClockBase",
            "TowerShaft", "ClockFace", "ClockHands", "GearRing", "Hourglass"]
PARTS = [(pid, globals()["build_" + pid]) for pid in PART_IDS if ("build_" + pid) in globals()]

AZ = {"CogGate": 100, "ClockHands": 165}
ELEV = {}
MULT = {"Ground": 1.7, "ClockBase": 2.2, "TowerShaft": 2.4, "ClockFace": 2.4, "ClockHands": 2.4, "GearRing": 2.6, "Hourglass": 2.6,
        "StarPond": 2.0, "CogGarden": 2.0}
SHIBA_AT = {"Ground": (-30, -6, 0, 0)}



def shiba_for(x, z, facing, lift):
    # the meshes are mirrored in x before export (decorkit), so the reference Shiba is placed mirrored too
    sb = dk.add_reference_shiba({"Shiba": {"Position": [-x, z], "Facing": 180 - facing}})
    bpy.context.view_layer.update()
    for o in sb:
        if o.parent is None:
            o.location.z += lift
    bpy.context.view_layer.update()
    return sb


def drop(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def snap(objs, extra, filename, az, el, mult, size, top=False):
    low, high = dk._bounds(list(objs) + list(extra))
    g = dk.ground(low, high)
    centre = (low + high) / 2
    radius = max((high - low).length / 2, 6)
    cam = dk._camera(centre, radius * mult, az, 89 if top else el)
    cam.data.clip_start = max(0.5, radius * mult * 0.08)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    path = os.path.join(OUT, filename)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(g, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print("RENDERED", path)


def combine(a, b, out):
    import numpy as np
    ia, ib = bpy.data.images.load(a), bpy.data.images.load(b)
    w, h = ia.size
    pa = np.empty(w * h * 4, dtype=np.float32); ia.pixels.foreach_get(pa)
    pb = np.empty(w * h * 4, dtype=np.float32); ib.pixels.foreach_get(pb)
    both = np.concatenate([pb, pa])      # image rows start at the bottom: top view below, 3/4 view above
    img = bpy.data.images.new("stage", w, h * 2, alpha=False)
    img.pixels.foreach_set(both)
    img.filepath_raw = out
    img.file_format = 'PNG'
    img.save()
    print("RENDERED", out)


def main():
    dk.start(OUT)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    built = {}
    for pid, fn in PARTS:
        if ONLY and pid not in ONLY:
            continue
        pj = dk.blueprint_part(BP, pid)
        part = dk.Part(pid)
        groups = fn(part)
        lo, hi = union(pj)
        fit(part, lo, hi)
        meshes = dk.finish(part, KEY, groups)
        built[pid] = meshes
        for other, ms in built.items():
            dk.hide(ms, other != pid)
        if pid in SHIBA_AT:
            x, z, f, lift = SHIBA_AT[pid]
        else:
            x = hi[0] + 5 if hi[0] + 5 < 76 else lo[0] - 5
            z = hi[2] - 3
            x, z, f, lift = x, z, 270, 0
        sb = shiba_for(x, z, f, lift)
        snap(meshes, [o for o in sb if o.type == 'MESH'], f"preview_{pid}.png", AZ.get(pid, 165), ELEV.get(pid, 28), MULT.get(pid, 2.4), (1400, 1000))
        drop(sb)
    if ONLY:
        return
    allm = [m for ms in built.values() for m in ms]
    for ms in built.values():
        dk.hide(ms, False)
    sbs = shiba_for(BP["Shiba"]["Position"][0], BP["Shiba"]["Position"][1], BP["Shiba"]["Facing"], 0)
    shm = [o for o in sbs if o.type == 'MESH']
    snap(allm, shm, "stage_3q.png", 165, 40, 2.8, (1800, 1000))
    snap(allm, shm, "stage_top.png", 180, 89, 2.1, (1800, 1000), top=True)
    combine(os.path.join(OUT, "stage_3q.png"), os.path.join(OUT, "stage_top.png"), os.path.join(OUT, "stage_CloudTemple.png"))
    for f in ("stage_3q.png", "stage_top.png"):
        try:
            os.remove(os.path.join(OUT, f))
        except OSError:
            pass


main()
