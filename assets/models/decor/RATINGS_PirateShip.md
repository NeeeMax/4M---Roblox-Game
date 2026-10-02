# Ratings: Decor PirateShip

Scores 1-10 per round (mean of: silhouette at distance, theme clarity, proportion/attachment of details, consistency with the
low-poly style, wow factor). Every preview PNG and the stage render were looked at in each round; anything below 8 was remade.
The final column is the score of the shipped models. Build: `blender --background --factory-startup --python build_PirateShip.py -- <absolute outdir>`
(env `PS_ONLY=Hull,Sign` builds single parts, `PS_COUNT=1` prints the triangles per object name, `PS_DBG=<folder>` renders extra angles).
Previews are rendered from the road side (+z) after the export mirror, so text and emblems read as they do in the game; the
reference Shiba is placed mirrored for the same reason. Every FBX was re-imported and measured: deviation 0.000 studs from the union box
of the blueprint pieces on all 15, one mesh each (limit 4), flat vertex colours only, no Neon, no textures.

Rounds: R1 = first complete build, R2 = after palette/emblem/colour fixes, Final = after the last polish round (3 rounds in total).

| Part | R1 | R2 | Final | Tris | What changed |
|---|---|---|---|---|---|
| Floor | 6.5 | 7 | 8 | 1499 | R1: muddy sand with spiky white foam blocks and tuft cones sticking out of the 0.5 stud box. R2: continuous zig-zag foam ring, sand colour lightened. Final: sand base no longer z-fights the top grid (stripes in the top view), soft-edged dirt yard / treasure beach / grass patches that fade into the sand, seaweed and sparkles in the lagoon, a dashed treasure trail from the pier to the red X, everything kept under 0.5 studs. |
| Hull | 7 | 7.5 | 8 | 1498 | R1: dark, flat barge with a bare transom. R2: lighter palette, gold and red wales that bulge out of the hull, gold stern lanterns, ship's wheel, forecastle rail, stairs to the aft deck. Final: golden dog figurehead at the stem, skull and crossbones on the transom under the gallery windows, foam collar at the waterline, barrels by the stairs; triangles trimmed from 1534 to under 1500. |
| Sign | 6.5 | 8.5 | 9 | 972 | R1: 3x5 block font read as "6ET / BONKED" (D looked like O). R2: 4x5 pixel font with merged boxes, GET / BONKED reads clearly from the road side, plank cuts in the board, iron-banded posts, gold corners, skull with crossbones on top. Final: only tidy-up of extents. |
| Masts | 7.5 | 7.5 | 8 | 1064 | R1: three masts, yards, nest, shroud ladders. R2: unchanged structure. Final: lantern under the crow's nest, yard lifts, fore top bell, gold yard-arm caps and topmast cap, stays between the masts. |
| Pier | 7 | 7.5 | 8 | 893 | R1: planks, four bollards, ropes, barrel, crates. R2: stringer and buoy extents fixed. Final: skull on one bollard, tricorn hat on another, rolled treasure map, crab, wanted board on a post, lantern on a hook. |
| Sails | 6.5 | 7 | 8 | 774 | R1: flat grey panels with a tiny black blob as emblem. R2: brighter cream, zig-zag hems, red stripes. Final: pixel skull plus two crossed bones that follow the belly of the main course (moved up off the hem, no more dashes), gaff sail with stripe, jib. |
| Tavern | 7.5 | 8 | 8 | 1380 | R1: two storey tavern with checker roof, cobble floor z-fought with its base (moire). R2: cobbles lifted above the slab, roof depth matched to the blueprint, softer roof checker, red pennants on both gables, chimney with smoke, hanging mug sign, balcony rail. |
| Cannons | 7 | 7.5 | 8 | 1422 | R1: black cannons on brown carriages. R2: steel barrels with gold rings, red wheels. Final: cannonball pyramid on a rack, two red powder kegs, ramrod. |
| Camp | 7.5 | 8 | 8 | 921 | A-frame tent with a dark door and guy ropes, campfire with stone ring, tripod and cauldron, log seats, barrels, crates, sacks, small jolly roger on a pole (added in R2). |
| Flag | 8 | 8 | 9 | 848 | Pixel-art skull and crossbones woven into a waving cloth (mirrored on the back so it reads from both sides), gold finials, two red pennants. Final: the skull got two eyes and a nose gap instead of one slit. |
| Palms | 8 | 8 | 8 | 1011 | Three banded leaning palms with feathered fronds and coconuts; crown size tuned so the model fits the blueprint box without squashing (z scale 0.96). |
| Rowboat | 7 | 7.5 | 8 | 539 | R1: lofted open hull, thwarts, oars, black anchor, beige box as "net". R2: red hull with a gold rim, rope coil, bucket, lantern, fish. Final: seagull on the transom, oar leaning on the boat. |
| Chest | 7.5 | 7.5 | 8 | 757 | Big round-lid chest with gold bands and lock, three gold heaps with coins, gems, a golden crown, goblet, skull, crossed cutlasses and the red X. Final: lid lighter than the body so the shape reads. |
| SkullRock | 8.5 | 8.5 | 9 | 550 | A rock in the lagoon with a bone-coloured skull on top, toothy grin, dark eye sockets and a pirate hat; foam ring and loose stones brought inside the blueprint box. |
| Kraken | 6 | 8 | 8 | 970 | R1: four straight spikes that read as horns. R2: S-curved tentacles with hooked tips, suckers, striped colouring, yellow eyes with brows, fangs and head spikes; heights tuned to the blueprint box. |

## Notes on the rating criteria
- Silhouette: ship with three masts and a tall flag, skull rock with hat, kraken with raised tentacles, red gabled tavern, palms and a round-lid chest all read at the 3/4 stage distance (`stage_PirateShip.png`).
- Theme clarity: every part is pirate-specific (jolly roger on the flag, the main sail, the transom, the sign, a bollard and the camp pole).
- Palette is shared by all 15 parts (dark wood, deck planks, cream, red, gold, iron, stone, sand, lagoon blue, kraken purple) and every part uses flat vertex colours with a little per-face jitter.
- All parts are one mesh (limit 4) and between 539 and 1499 triangles.
- Openings (stairs, the pier, the open tavern porch, the crow's nest, the boat) stay open; ship parts that stand on the deck (Masts, Sails, Cannons, Flag) only occupy their own blueprint boxes above y = 7.4 so they sit on the Hull model.
