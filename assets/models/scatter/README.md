# Scatter props

Small single-mesh props the game duplicates with random rotation and scale to make stages feel organic
(trees, fences, rocks, bushes, flowers, lamps...). Built by `build_scatter.py` on `../decor/decorkit.py`:

    blender --background --factory-startup --python build_scatter.py -- C:/Dev/4M-tycoon/assets/models/scatter/out

Output in `out/`: `Scatter_<Name>.fbx` (one mesh, flat vertex colours, no Neon, origin = bottom centre on the ground,
units = studs, x mirrored on export like the decor), `manifest.json`, `contact_sheet.png` (all props, orange bar =
Shiba height 6) and `contact_<biome>.png`. Self-review in `RATINGS.md`.

Import: `assets/models/combine_for_import.py` includes `scatter/out` (one Import 3D for everything, see
`assets/README.md`); each prop ends up as `Scatter_<Name>` in `ReplicatedStorage/Assets`. Or import single files
and name them exactly like the file. Clone it, set a random `Yaw`, `Size`-scale 0.8-1.25 and tilt 0-6 degrees.

| Name | Biome | Size x (width) | Height | Size z (depth) | Triangles |
|---|---|---|---|---|---|
| Scatter_OakA | suburban | 17.2 | 19.1 | 13.3 | 436 |
| Scatter_OakB | suburban | 13.8 | 21.7 | 9.5 | 376 |
| Scatter_Birch | suburban | 10.0 | 19.1 | 7.5 | 436 |
| Scatter_Pine | suburban | 10.9 | 20.5 | 10.6 | 64 |
| Scatter_PineSmall | suburban | 8.2 | 12.6 | 8.0 | 52 |
| Scatter_Bush | suburban | 7.2 | 4.2 | 5.7 | 240 |
| Scatter_BushFlowers | suburban | 6.6 | 3.6 | 4.9 | 336 |
| Scatter_FlowerPatch | suburban | 4.1 | 1.4 | 4.1 | 192 |
| Scatter_Hedge | suburban | 6.8 | 3.8 | 2.8 | 196 |
| Scatter_PicketFenceSegment | suburban | 8.6 | 4.6 | 1.0 | 220 |
| Scatter_PicketFencePost | suburban | 1.5 | 5.1 | 1.5 | 30 |
| Scatter_LampPost | suburban | 3.4 | 14.1 | 3.4 | 90 |
| Scatter_StumpLog | suburban | 8.5 | 2.4 | 5.9 | 136 |
| Scatter_GardenGnome | suburban | 1.9 | 5.1 | 2.0 | 148 |
| Scatter_GrassTuftA | suburban | 1.6 | 2.4 | 1.6 | 36 |
| Scatter_GrassTuftB | suburban | 2.6 | 3.0 | 2.5 | 56 |
| Scatter_PalmA | beach | 15.4 | 20.0 | 14.8 | 412 |
| Scatter_PalmB | beach | 16.3 | 16.7 | 16.0 | 404 |
| Scatter_Beachgrass | beach | 2.6 | 4.3 | 2.9 | 48 |
| Scatter_Driftwood | beach | 7.5 | 2.7 | 2.6 | 152 |
| Scatter_ShellRock | beach | 6.1 | 2.4 | 4.9 | 232 |
| Scatter_Towel | beach | 3.6 | 0.4 | 6.0 | 72 |
| Scatter_SandcastleSmall | beach | 5.7 | 7.0 | 5.0 | 228 |
| Scatter_Crate | beach | 3.1 | 3.1 | 3.2 | 96 |
| Scatter_ChainFenceSegment | city | 8.2 | 4.5 | 0.4 | 220 |
| Scatter_TrafficCone | city | 2.0 | 2.4 | 2.0 | 68 |
| Scatter_Barrel | city | 2.6 | 3.3 | 2.7 | 144 |
| Scatter_Dumpster | city | 6.2 | 4.5 | 3.4 | 100 |
| Scatter_StreetLamp | city | 5.8 | 14.3 | 1.8 | 104 |
| Scatter_PlanterBox | city | 4.2 | 3.8 | 2.3 | 232 |
| Scatter_Hydrant | city | 2.1 | 3.7 | 2.0 | 196 |
| Scatter_CactusA | western | 6.9 | 8.7 | 2.3 | 196 |
| Scatter_CactusB | western | 6.1 | 3.7 | 4.6 | 312 |
| Scatter_Haystack | western | 7.7 | 5.5 | 6.8 | 180 |
| Scatter_WoodFenceSegment | western | 8.2 | 3.7 | 1.0 | 72 |
| Scatter_Tumbleweed | western | 4.5 | 3.9 | 4.6 | 240 |
| Scatter_DeadTree | western | 7.4 | 13.6 | 2.4 | 112 |
| Scatter_RockRed | western | 8.4 | 5.5 | 6.4 | 164 |
| Scatter_RopeCoil | harbor | 6.2 | 3.0 | 3.9 | 240 |
| Scatter_CratesStack | harbor | 6.6 | 5.5 | 3.8 | 72 |
| Scatter_BarrelStack | harbor | 5.1 | 6.0 | 2.8 | 288 |
| Scatter_Anchor | harbor | 7.4 | 7.4 | 1.6 | 144 |
| Scatter_NetPile | harbor | 6.1 | 1.7 | 5.2 | 496 |
| Scatter_BambooClump | asia | 9.9 | 17.1 | 7.5 | 320 |
| Scatter_SakuraTree | asia | 14.9 | 16.9 | 11.7 | 392 |
| Scatter_StoneLantern | asia | 4.2 | 7.5 | 4.2 | 176 |
| Scatter_LowFenceSegment | asia | 8.0 | 3.2 | 0.9 | 200 |
| Scatter_ZenRock | asia | 7.8 | 3.8 | 8.0 | 436 |
| Scatter_PineSnow | viking | 10.5 | 18.4 | 10.3 | 112 |
| Scatter_RuneStoneSmall | viking | 4.7 | 5.3 | 2.5 | 152 |
| Scatter_LogPile | viking | 4.7 | 4.4 | 5.2 | 360 |
| Scatter_ShieldFence | viking | 8.4 | 4.5 | 1.0 | 252 |
| Scatter_RockA | rocks | 4.3 | 3.2 | 4.2 | 80 |
| Scatter_RockB | rocks | 7.4 | 2.7 | 4.9 | 160 |
| Scatter_RockC | rocks | 5.2 | 4.9 | 3.4 | 240 |
| Scatter_BoulderA | rocks | 9.8 | 6.0 | 8.6 | 240 |

Biomes: suburban (parks, gardens), beach, city, western, harbor (pirate), asia (ninja), viking (winter), rocks (any).
