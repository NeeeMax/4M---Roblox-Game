# Ratings: Decor VikingLonghouse (bay 10, Viking Shiba)

Scores 1-10 per round (mean of: silhouette at distance, theme clarity, proportion/attachment of details, consistency with the
low-poly style, wow factor). Anything below 8 was remade; the final column is the score of the shipped models. Every preview was
looked at (`out/VikingLonghouse/preview_<Part>.png`, `stage_VikingLonghouse.png`). The previews are rendered the way the player sees the
stage: from the road (+z) with +x to the right, with a 7.5 stud reference Shiba.
Build: `blender --background --factory-startup --python build_VikingLonghouse.py -- <absolute outdir>` (default `out/VikingLonghouse`).
Every model is fitted to the union box of its blueprint pieces (`blueprint_VikingLonghouse.json`); the fit scale printed by the build is
within 0.96-1.03 on every axis of every part except Ground in y (0.89, only 0.5 studs tall, flat decals) and Hoard in y (0.96).
All parts: 1 mesh, flat vertex colours with a little per-face jitter, no Neon, no textures, 491-1432 triangles.

| Part | R1 | R2 | Final | Tris | What changed |
|---|---|---|---|---|---|
| Ground | 7 | 7.5 | 8 | 1345 | R1: tiled grass grid with visible squares, plain sand, flat fjord. R2: smooth Gouraud green field, fjord with beach, foam and deep water, rune ring around the Shiba's platform, gravel yard, flower clumps. R3: two islets with rocks, foam dashes and reeds on the shore, a ploughed crop field with barley rows, softer dirt patches and fewer hard-edged patches (all decals stay under 0.55 studs). |
| Longhouse | 7.5 | 7 | 8 | 1432 | R1: log walls with ribbed courses, gold-banded door posts, red shield inside, plain striped roof. R2: ribs on the roof read as a greenhouse (worse). R3: roof replaced by a lumpy sod roof (soil edge, irregular greens), dragon-spine fins along the ridge, smoke louver, barge boards and fascia, bigger gold dragon heads on both gables, bigger hearth fire seen through the open door, 8 wall shields. |
| Smithy | 6 | 7.5 | 8 | 710 | R1: the roof covered the whole forge, it read as a table with a chimney. R2: open rafters over the front half, hanging anvil sign. R3: only 3 board strips over the back so the anvil, bellows and glowing hearth show, chimney lowered with smoke puffs, hot iron on the anvil. |
| FirePit | 7.5 | 8.5 | 8.5 | 491 | R1: one red cone as flame. R2: cluster of flame tongues with a yellow core, tripod with hanging cauldron, ring of stones, log seats with light tops, embers. |
| Longship | 8.5 | 8.5 | 8.5 | 792 | Lofted hollow hull with red gunwale strakes, striped bellied sail, shrouds and stays, rail shields (face colour per side), thwarts, chest, oars, foam collar. R3: dragon head rebuilt as a tapering loft with brow, jaw, teeth, eyes and horns instead of a cube. |
| Feast | 7 | 7.5 | 8 | 948 | R1: read as a picnic table. R2: carved end boards instead of trestles, wolf pelts on the benches, drinking horns, torch stands at two corners, roast boar with apple, fruit bowl, mead barrel with tap. |
| Jetty | 7 | 7.5 | 8 | 845 | R1: deck, posts, barrels, crates, one lantern. R2: rope rails between the posts, sacks, fish crate with silver fish, second small lantern near the shore, net and rope coil. |
| ShieldWall | 8 | 8 | 8 | 704 | Palisade of pointed stakes with two rails, four gold-capped posts, six round painted shields with gold bosses (kept inside the blueprint depth), four spears above. |
| Storehouse | 6.5 | 8 | 8 | 773 | R1: the door and steps were on the back (deep) side so the road side showed a blank wall; blueprint and model flipped to face +z. R2: sod roof with soil edge, gable cross boards, stone-capped stilts, four steps, shuttered window, sacks. |
| Watchtower | 8.5 | 8.5 | 8.5 | 1034 | Four tapering legs with two levels of cross braces, ladder with rungs, railed platform, log cabin with arrow slits and a shield, timber roof with ridge board, fire basket on the corner. |
| FishRacks | 7 | 7 | 8 | 928 | R1: two racks of diamond fish hid the upturned boat. R2: front rack hangs its fish high so the boat shows, bigger fish, cutting table with fish and knife, two seagulls, basket of fish, barrel. |
| AxeRange | 8 | 8 | 8 | 749 | Three octagonal targets with red/white rings on foot-beam posts, axes stuck in them, raked gravel lane with a red throwing line, weapon rack with spare axes, chopping stump with axe. |
| RuneStones | 8 | 8 | 8 | 814 | Tall centre obelisk with red tip and red runes, six tapered stones turned to face the centre with blue runes, carved gold ring on the floor, cobble rim, altar with offering bowl, moss. |
| Banners | 7.5 | 7.5 | 8 | 692 | Four tall poles on stone bases with crossbars, swallow-tail cloth, gold trim, a raven on both sides in contrasting colour (dark on red, white on blue), gold finials. Finial size matches the blueprint depth. |
| Sauna | 7.5 | 7.5 | 8 | 754 | Log hut with sod roof, stone chimney in four courses, door, bench with bucket and ladle, firewood stack. R1 steam read as grey rocks; now two clouds of three white puffs each. |
| Throne | 8.5 | 8.5 | 8.5 | 588 | Two-tier stone dais with steps and gold studs, carved wooden throne with gold disc and red gem, bone horns, gold knobs, fur rug and pelt, two fire bowls on tripods. |
| Totem | 8.5 | 8.5 | 8.5 | 596 | Four carved blocks (wolf, bear, eagle with spread wings, bearded god) separated by gold bands, black raven with spread wings and gold beak on top, stone base. |
| Stables | 7 | 8 | 8 | 1042 | R1: dark plank roof and a dark pony were hard to read. R2: thatch roof with shaggy fringe, palomino pony with white mane, tail and socks, blanket, hay, bucket, trough, fence with gold-capped gate posts. |
| Hoard | 7.5 | 7.5 | 8 | 1289 | R1: rock heap with gold. R2: dark cave mouth behind the chest, open chest with lid and coins, three gold heaps, towers of coins, crown, goblet, gems, sword stuck in the rock. |
| Helmet | 9 | 9 | 9 | 822 | Steel bowl on a stone plinth with a gold brim band, mail skirt, gold ribs over the bowl, nose guard with gem, eye slots, two curved striped bone horns with gold tips, gold corner knobs. |

## Notes on the rating criteria
- Silhouette: hall with dragon-spine ridge and gable heads, tall helmet horns, mast and striped sail of the ship, tower on legs, totem with raven, banners and rune obelisk all read at stage distance.
- Theme clarity: Viking props only (longhouse, longship, rune stones, helmet, shield wall, forge, feast with boar, axe throwing, sauna, raven totem, hoard, fjord).
- Openings stay open: the hall door shows the hearth, the forge is open to the road, the cave mouth is dark and open, the stable shed is open to the paddock.
- Palette is shared across the theme (timber browns, turf greens, stone greys, red/blue/bone shields, gold, steel, fjord blues); no Neon, no textures.
- Orientation: everything with a front (hall door, forge, storehouse door, shields, stable, tower ladder, cave, helmet face) looks toward +z, the road side.
