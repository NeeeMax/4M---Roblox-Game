# Ratings: DragonLair (bay 22, 30 parts)

Self-review of the Blender models (1 to 10; criteria: silhouette, theme clarity, proportion and attachment, low-poly consistency, wow).
R1 = first build, R2 = after the first remake round, Final = after the last round. Everything below 8 was remade (at most 3 rounds).
All 30 parts: 1 mesh each, flat vertex colours, no Neon, max 1484 triangles (SkullGate), one shared palette (dark volcanic rock, bone, dragon-scale green, gold, lava orange).
Models are built without the part's Yaw, in the stage frame, fitted to the union box of the blueprint pieces (see `fit()` in `build_DragonLair.py`).
Build: `blender --background --factory-startup --python build_DragonLair.py -- out/DragonLair [Part,Part,...]`.

| Part | R1 | R2 | Final | What changed |
|------|----|----|-------|--------------|
| Ground | 7 | 8 | 8 | 1884 tris over budget: fewer rock plates and stepping stones (1428); gold octagon plaza with a star, lava rivers with banks, cobbled path plates. |
| Cave | 4 | 7 | 8 | R1 was one dark box: now stacked tiers with lighter strata, bone horns, bone brow ridge with spikes, fanged mouth with a lava glow, spiky crown. |
| Hoard | 6 | 7 | 8 | Smooth blobs became cake-like tiers, then pyramids; final is a lumpy mound of gold nuggets with loose coins, chests, gems and a crown. |
| Braziers | 7 | 8 | 8 | Added tripod feet, coals, extra flame tongues and rock rubble. |
| Hatchery | 8 | 8 | 8 | Twig nest with hay, three speckled eggs with ember cracks. No change needed. |
| Stalagmites | 7 | 8 | 8 | Lighter tips for contrast, small spikes around, lava cracks at the base. |
| Ribs | 7 | 8 | 8 | Hook-like ribs became tapering arched bones on a vertebrae spine; added a horned beast skull at the head end. |
| LavaPool | 7 | 8 | 8 | Brick-like ring stones became jagged tapering rocks; bubbles and embers on the lava. |
| SkullGate | 8 | 8 | 8 | Vertebra pillars, giant bone lintel with fangs, three horned skulls, hanging fire bowls; z fitted to the box. |
| Crystals | 8 | 8 | 8 | Tilted hexagonal emerald crystals with a ruby and glints on a rock mound. |
| Armory | 7 | 8 | 8 | Robot-like suits got capes, rust, a sword in hand; the fallen suit and helmet were rebuilt, the dark slab became a dented shield. |
| Chests | 7 | 8 | 8 | Lids opened only a few degrees (R1 lid exceeded the box height), spilled gold heaps, gems. |
| Swords | 5 | 8 | 8 | R1 swords stood hilt-down in the rubble; rebuilt blade-down with guard, grip and pommel, tilted about the tip. |
| Forge | 6 | 8 | 8 | Furnace was hidden inside its frame: now a visible lava mouth with flames, lighter walls, slate roof, chimney, anvil, coal barrel; previewed from the -z front. |
| Banners | 8 | 8 | 8 | Four poles with flapping red and green banners and gold emblems. |
| Tower | 7 | 8 | 8 | Lighter stone, breach in the wall, cracks, moss, collapsed battlement, torn banner. |
| Baby | 5 | 7 | 8 | R1 was a green blob with a flat tail and floating panels; now round sleepy head, belly, bat wings with bone fingers, fat curled tail with a spade. |
| Throne | 7 | 8 | 8 | The rib-bar back looked like a cage: now a solid bone slab with grooves, a central skull, horns, crown and ruby. |
| Coins | 6 | 8 | 8 | Thick pancake discs became thin coin stacks with slight offsets, gems on top, loose coins. |
| Runes | 7 | 8 | 8 | Lighter standing stones with glowing rune lines, purple plate with glyphs and a central crystal. |
| Wings | 4 | 5 | 8 | R1 read as tents, R2 as furled umbrellas; final is two bat-wing arches (bent arm, wrist claw, fingers) with scalloped green membranes. |
| Skull | 7 | 8 | 8 | Depth and height refitted to the box (horns sweep sideways), removed the crack marks, glowing eyes and fangs. |
| Spires | 6 | 7 | 8 | Near-black blobs: lighter violet facets, stronger facet jitter, purple glints, higher preview angle. |
| Keep | 8 | 8 | 8 | Four round towers with scale-green cones, stepped scale roof, gate with dragon head, lava window; triangles cut from 1662 to 1366. |
| Catapult | 8 | 8 | 8 | Spoked wheels, A-frame, throwing arm rising to the bucket, stone counterweight. |
| Statue | 7 | 8 | 8 | Visor bar became eye slits, added pauldrons, belt, a bigger sword and a dragon skull trophy at the pedestal. |
| Volcano | 8 | 8 | 8 | Strata tiers, crater with rim teeth, two lava streams, flying embers. |
| Wagon | 7 | 8 | 8 | Gold heap fitted inside the box (z overflow), spoked wheels, ingots, ruby. |
| Mushrooms | 6 | 8 | 8 | R1 caps were radius instead of diameter (huge); now correctly sized caps with gills and spots, tiny glow-shrooms. |
| GreatDragon | 8 | 8 | 8 | Landmark: green dragon with spread wings, spiked back, long neck and tail, horned head breathing fire; feet rest on y 32.1 (cave roof). |
