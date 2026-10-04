# Ratings VoidPortal (theme 30, Void Shiba)

Self-review of the 30 models (`build_VoidPortal.py`, previews and `stage_VoidPortal.png` in `out/VoidPortal/`), score 1-10 on
silhouette, theme clarity, proportion/attachment, low-poly consistency and wow. Everything below 8 was remade. R1 = first build,
R2 = after the first round of changes, Final = what ships. All models: one mesh, flat vertex colours, no Neon, 536 to 2722 triangles
(the seven landmark parts at the end are 1.5k to 2.7k).

| Part | R1 | R2 | Final | What changed |
|---|---|---|---|---|
| Ground | 7 | 8 | 8 | Tiles with glowing seams, flagstones along the whole path, rune star plaza |
| Gate | 8 | 8 | 8 | none (preview camera moved to the road side) |
| Sign | 7 | 8 | 8 | Posts moved behind the board so they no longer cover the D of THE VOID |
| RuneStones | 8 | 8 | 8 | none |
| Braziers | 7 | 8 | 8 | Base stone lightened so it reads against the black floor |
| Crystals | 9 | 9 | 9 | none |
| Spikes | 6 | 8 | 8 | Spikes were black on black: lighter stone, lighter bed, cyan tips |
| Rift | 7 | 8 | 8 | Thin light needles removed, small glowing shoots along the crack |
| Lanterns | 8 | 8 | 8 | none |
| VoidTrees | 8 | 8 | 8 | Fourth leaf blob removed (1722 to 1482 triangles) |
| Altar | 8 | 8 | 8 | none |
| Shrooms | 8 | 8 | 8 | Fewer cap facets and pups (2030 to 1185 triangles) |
| Statues | 7 | 8 | 8 | Sword moved beside the body, it covered the hooded face |
| Pool | 6 | 7 | 8 | Rim lightened with cyan studs, odd straight swirl lines replaced by a star |
| Ruins | 6 | 8 | 8 | Columns lightened, violet crack stronger, floating capitals tilted |
| Tentacles | 7 | 8 | 8 | Body lightened so the violet bands read |
| Obelisks | 8 | 8 | 8 | none |
| Throne | 8 | 8 | 8 | none |
| Watchtower | 8 | 8 | 8 | none |
| Shards | 8 | 8 | 8 | none |
| Orrery | 8 | 8 | 8 | none |
| Sentinel | 7 | 8 | 8 | Armour lightened from near black to grey-violet |
| PortalFrame | 7 | 8 | 9 | Lighter stone, cyan inner rim, runes on the ring |
| PortalSwirl | 9 | 9 | 9 | none (five spiral arms in a funnel, cyan core) |
| Citadel | 7 | 8 | 9 | Walls and towers lightened, banners on the towers, glowing door and hall |
| Comets | 8 | 8 | 8 | none |
| Island | 6 | 7 | 9 | Lighter rock and top, violet moss rim, crystals, glowing temple door, waterfall foam |
| Spire | 8 | 8 | 9 | Tiers lightened, preview framed wider |
| BlackHole | 8 | 8 | 9 | Two lensing rings around the core, jets, spiral arms in the disc |
| VoidEye | 9 | 9 | 9 | Facet counts reduced (2722 to 2466 triangles) |

Notes
- Previews are rendered in the exported (x-mirrored) frame, so they match what Studio shows; text reads correctly from +z.
- Fit scales are between 0.80 and 1.09 (the models were designed to the union boxes of the blueprint pieces); the Pool is the flattest (y 0.80, it is a low pool).
- Largest models: VoidEye 2466, BlackHole 2048, Island 1908 triangles (landmarks).
- The flagstones of the Ground follow the walkway only in the model (a turned flat piece counts as solid in `theme_check`), so the Ground blueprint keeps a plain slab.
