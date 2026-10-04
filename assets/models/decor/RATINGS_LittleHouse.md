# LittleHouse decor ratings

Scores 1-10 per part (average of: silhouette at distance, theme clarity, proportion/attachment of details, low-poly style
consistency, wow factor). Every score comes from looking at `out/LittleHouse/preview_<PartId>.png` (and the stage renders)
after each build round. Anything below 8 was remade; Final is the last round.

| Part | R1 | R2 | R3 | Final | What changed |
|---|---|---|---|---|---|
| Flooring | 6 | 7 | 8 | 8 | R1 plain grey slabs. R2 paw-print inlay in the patio, sandstone accent flags, moss patches, rug with 3 borders. R3 preview reframed on the real Shiba spot. Height stays 0.4 so the box matches the pieces. |
| LittleHouse | 6 | 7 | 8 | 8 | R1 2008 tris, roof like a ziggurat, Shiba hidden. R2 real window openings, hip roof in 5 shingle courses, cutaway render (roof is its own mesh), 1560 tris. R3 lit fireplace with logs and flames, chimney smoke, single wide north window, window frames as open shells, 1516 tris. Doorway stays open (lintel at y 11+). |
| BonkedSign | 7 | 7 | 8 | 8 | Block letters "GET / BONKED" with bone icons, red frame, planked board, post finials and footings. R3: bbox trimmed to the pieces. Note: the Blender preview shows the lettering mirrored, see the x-mirror note below. |
| Garage | 6 | 7 | 8 | 8 | R1 roof hid the car (preview angle). R2 lower preview angle, car with glass cabin, hubs, lamps; shingle-course slate roof, gable triangles, header, shelf with cans. R3 fascia boards, gable vents, side windows with shutters. Front stays open (header at y 8.5). |
| Mailbox | 6 | 7 | 8 | 8 | R1 stick-like flag, blank plate. R2 flag with arm and plate, loaf shape (box + half barrel), door with knob, flowers at the stone base. R3 letter with red seal on top, white paw print instead of the blank plate. |
| Fence | 7 | 7 | 8 | 8 | Pointed pickets, capped posts, two rails (R1). Post height trimmed to 6.6 (R2). R3 pickets moved behind the garland, climbing-rose garland with blooms along the whole fence. |
| Garden | 7 | 7 | 8 | 8 | R1 1670 tris. R2 blooms reduced (ico, 7 per row), foliage tufts, stepping stones, wooden edges with corner posts, gnome at the path end, 1334 tris. R3 posts moved inside the footprint. (Octahedron blooms were tried and dropped: they read as umbrellas.) |
| Tree | 6 | 8 | 8 | 8 | R1 canopy was a pile of identical balls. R2 three flat canopy pads plus crown and side clumps with vertex wobble, flared trunk with roots, two branches, rope swing, apples, rocks and flowers. R3 left clump widened to the full footprint. |
| DoghouseBench | 6 | 8 | 8 | 8 | R1 trims were placed inside the walls (invisible), dark red. R2 trims moved to the outer face, brighter red, hollow house with dark liner and dog bed, wood door frame, battens, bone sign, bowl and ball; bench with iron ends, 3 plank seat, 3 slat back. |
| Fountain | 7 | 7 | 8 | 8 | R1 floating stick jets. R2/R3 hollow stone basin with crenellated rim, two-tier pedestal and bowl, eight water spouts falling into the basin with foam, gold bone on a gold cap. |

## Numbers (final build)

| Part | Meshes | Triangles |
|---|---|---|
| Flooring | 2 | 1080 |
| LittleHouse | 3 (Body, Roof, Trim) | 1516 |
| BonkedSign | 3 | 768 |
| Garage | 4 | 1184 |
| Mailbox | 2 | 364 |
| Fence | 2 | 660 |
| Garden | 1 | 1334 |
| Tree | 3 | 1228 |
| DoghouseBench | 4 | 692 |
| Fountain | 3 | 1188 |

Each model's bounding box was checked against the union box of its blueprint pieces (build script prints `FOOTPRINT`):
all deviations are 0.5 studs or less (Tree canopy, other parts 0.3 or less). The game scales by the longest side and centres
on the box, so this keeps them in place.

## Open point for the integrator: x mirroring

decorkit maps stage (x, y, z) to Blender (x, z, y). That is a reflection, and the FBX export (axis_forward Z, axis_up Y) is a
proper rotation with x_fbx = -x_blender, so if Roblox imports the FBX faithfully, every model comes out mirrored in x inside
its own box (lettering, the patio vs the house floor in Flooring, car nose direction, gnome side ...). The Blender previews
show this as mirrored lettering on the sign. I built to the kit as specified. If an in-Studio check of `Flooring` shows the
patio on the wrong side, rebuild with `--mirror-x` (mirrors each part about the centre of its piece box, normals flipped) or
fix the mapping once in decorkit for all themes.
