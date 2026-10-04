# WesternSaloon decor ratings

Score 1-10 per round (silhouette at distance, theme clarity, proportion/attachment, low-poly consistency, wow). Anything below 8
was remade (max 3 rounds needed). Triangles are final counts (limit about 1500, all parts are 1 mesh). Build:
`blender --background --factory-startup --python build_WesternSaloon.py -- <absolute outdir> [PartId,...]`.

| Part | R1 | R2 | R3 | Final | Tris | What changed |
|------|----|----|----|-------|------|--------------|
| Floor | 6 | 7 | 8 | 8 | 1184 | R1 strong checker grid, muddy. R2 calmer sand, packed-earth trail under the walkway. R3 red-rock dust near mesa/mine, kept below the game walkway (0.1) and boardwalks at 0.3. |
| Saloon | 8 | 9 | - | 9 | 1468 | R1 was 1888 tris: shutters became decals, fewer balusters/barrels/roof boards/bench legs. Cowboy Shiba stands on its porch deck. |
| Gate | 8 | 8 | - | 8 | 522 | BONK / TOWN sign on two lines, longhorn skull, post lanterns, stars. |
| Jail | 8 | 8 | - | 8 | 552 | JAIL letters enlarged in R2; barred stone cell, tin star. |
| Horses | 6 | 7 | 8 | 8 | 792 | R1 boxy slabs. R2 side-profile extruded body/neck/head, socks, saddle, pinto patches, mane/tail. R3 preview framing and saddle/bedroll fit. |
| Well | 8 | 8 | - | 8 | 277 | Open stone ring with water, roof, windlass, bucket, crank. |
| Wagon | 8 | 8 | - | 8 | 931 | Spoked wheels, canvas arch with hoops, barrels, tongue. |
| Bank | 8 | 8 | - | 8 | 596 | Letters on a teal frieze (enlarged), vault door, columns, gold bars; medallion kept inside the height box. |
| Cacti | 6 | 7 | 8 | 8 | 1156 | R1 two bare saguaros. R2 ribs, flowers, prickly pears. R3 agaves, small round cacti, tumbleweed, steer skull. |
| WaterTower | 8 | 8 | - | 8 | 478 | Removed two odd red decal triangles; X-braced legs, ladder, hoops, spout. |
| Windmill | 9 | 9 | - | 9 | 692 | Lattice tower, 12-blade wheel with ring, tail vane, trough. |
| Mine | 7 | 8 | - | 8 | 1124 | R1 stepped boxes. R2 rocky buttes on top, cracks, spires; sign, cart, TNT, gold. |
| Train | 9 | 9 | - | 9 | 948 | Preview moved to the town side; engine, tender, red freight car on a track. |
| Camp | 8 | 8 | - | 8 | 720 | Teepee with bands, campfire with tripod pot, log seats, hat, crate, bedroll. |
| Mesa | 5 | 7 | 8 | 8 | 1040 | R1 stacked slabs (wedding cake). R2 irregular banded butte. R3 gullies, spires, brim wings, small butte. |

Notes: text and signs are flat decals facing +z (road side); previews are rendered from the road side without an image flip
(decorkit mirrors x on export, the reference Cowboy Shiba is mirrored the same way) and the lettering reads correctly in them.
