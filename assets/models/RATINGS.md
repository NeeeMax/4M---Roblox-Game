# Model ratings

Self-review log for the low-poly models: each item is rated 1-10 per round from Blender renders (close-up 3/4 view
and the game-distance row). Criteria: readable silhouette at game distance, theme clear at a glance, accessories
attached and in proportion, style consistent with the other Shibas / platforms, model and platform read as one design.
Anything under 8 was reworked and rendered again.

## Existing new Shibas (11-20 set)

Close-ups: `build_shiba_tiers.py -- <out> --only <names>` (`preview_<Asset>.png`), game-distance row:
`Tiers11-20_preview.png`.

| Shiba | Round 1 | Round 2 | Round 3 | What changed |
|-------|---------|---------|---------|--------------|
| PirateShiba | 6 | 7 | 8 | R1: tricorn was a flat black box, parrot hidden behind the head. R2: parrot moved out onto the shoulder, bigger, red/blue/yellow with eyes and a hanging tail; neckerchief knot on the chest. R3: tricorn rebuilt as a triangular bowl widening upward (turned-up brim, one corner to the front) with gold trim on the top edges, domed crown, skull and crossbones on the front corner. |
| CowboyShiba | 8 | — | — | Kept: hat, bandana, star and lasso all read. |
| VikingShiba | 7 | 7 | 8 | R1: shield edge-on (a dark blob from the front), beard looked like beads. R2: big ginger beard wedge, moustache, two braids with gold rings; shield turned to face front-left (but its quarters smeared). R3: shield with a fan-filled face in red/white wedges, iron rim and boss. |
| WizardShiba | 8 | — | — | Kept: hat, beard, orb read well. |
| AstronautShiba | 8 | — | — | Kept: helmet frame, suit, backpack, chest box. |
| RobotShiba | 8 | — | — | Kept: visor, antenna, chest panel. |
| SamuraiShiba | 7 | 8 | — | R1: kabuto read as a bucket hat, shoulder strips floated, topknot sat on the helmet. R2: neck guard layers tilted (rise at the front, flare over the neck), gold band, side flaps, bigger V crest on a sun disc; red lacquer do (chest armour) following the body; shoulder plates hang on the upper arms with gold tops; topknot removed. |
| VampireShiba | 6 | 8 | — | R1: read as a plain grey dog, collar and cape hidden behind the body. R2: slicked black hair with a widow's peak, tall collar flaring out beside the head (red inside), a much wider cape with red lining that shows on both sides, bigger ruby clasp in a gold ring. |
| PharaohShiba | 8 | — | — | Kept: striped nemes, cobra, collar, ankh. |
| DragonShiba | 6 | 8 | — | R1: wings were flat green boards on one side, horns lost in the ears. R2: bat wings spread wide (arm bone, three finger bones, five triangular membranes in two greens) visible on both sides from the front; big curved horns between the ears; orange spine spikes and a tail spike; belly plates. |

## Platforms

Renders: one 3/4 tile per platform from `build_props.py` with the tier's Shiba standing on it (its own FBX from
`assets/models/` for Pirate … Dragon; the orange default dog, 8 studs, for the ten tiers whose models are made
separately — those are rated on the platform alone). Sheet: `Platforms_preview.png`. Targets: every platform ≥ 8,
Eternal and Void ≥ 9.

| Platform | Round 1 | Round 2 | Round 3 | What changed |
|----------|---------|---------|---------|--------------|
| Platform_PirateShiba | 8 | — | — | Kept: ship's deck, rope, wheel, treasure barrel, chest and Jolly Roger read as one pirate scene with the tricorn Shiba. |
| Platform_CowboyShiba | 8 | — | — | Kept: hay bale, wagon wheel, cactus, crate. |
| Platform_VikingShiba | 7 | 8 | — | R1: the dragon prow sat low right behind the Shiba and could not be seen. R2: prow moved to the back-left corner and raised to 8.6 studs, so the carved head shows beside the helmet. |
| Platform_WizardShiba | 8 | — | — | Kept: book stack, rune stones, candle, crystal. |
| Platform_AstronautShiba | 8 | — | — | Kept: moon rock, craters, flag, rocket. |
| Platform_RobotShiba | 8 | — | — | Kept: hazard-striped pad, glowing ring and lights, brass gears. |
| Platform_SamuraiShiba | 9 | — | — | Kept: tatami, torii framing the Shiba, lantern, pink bonsai. |
| Platform_VampireShiba | 8 | — | — | Kept: coffin, tombstones, spiked fence, candles, bats. |
| Platform_PharaohShiba | 8 | — | — | Kept: stepped pyramid, hieroglyph bands, gold top, obelisks. |
| Platform_DragonShiba | 9 | — | — | Kept: gold hoard with gems, sword, crown and goblet under the winged Shiba. |
| Platform_DJShiba | 8 | — | — | Kept: light-up floor, speakers, deck, disco ball. |
| Platform_KnightShiba | 7 | 8 | — | R1: plain tower top, the only pennant hidden behind the Shiba. R2: two tall poles with long red/blue pennants and gold emblems at the back corners, corbels under the parapet, arrow slits. |
| Platform_SuperheroShiba | 8 | — | — | Kept: rooftop, lit windows, hero emblem, water tower, searchlight. |
| Platform_FrostShiba | 8 | — | — | Kept: ice chunk, snow cap, icicles, crystal clusters. |
| Platform_MagmaShiba | 7 | 8 | — | R1: vents too small to notice. R2: two big vents (4.6 and 3.4 studs) with lava streams down their sides and lava blobs flying out. |
| Platform_MechaShiba | 7 | 8 | — | R1: flat hex pad, little sci-fi silhouette. R2: hangar gantry over the back (armoured columns with glowing strips and yellow bands, hazard-striped beam, warning lights, docking clamp), glowing vents on the side panels. |
| Platform_AngelShiba | 6 | 8 | — | R1: wings were flat blades lying almost horizontal, cloud greyish. R2: two wings of six feather blades fanning up from gold shoulders, gold top feather; brighter white cloud. |
| Platform_DemonShiba | 6 | 8 | — | R1: the flames were hidden inside the rock, one small horn. R2: nine flames burning around the foot, two huge ribbed horns curling up and over from both sides, glowing cracks down the rock. |
| Platform_EternalShiba | 8 | 9 | — | R1: dais, clock-face top and standing clock were good, but the front steps looked like a grey box and it was not yet over the top. R2: sunburst of golden rays around the standing clock, twin golden columns with a sun and a crescent moon, a floating hourglass, gold-edged marble steps. |
| Platform_VoidShiba | 8 | 8 | 9 | R1: flat from the front: the vortex was dark on dark, shards tiny. R2: glowing ribbons spiralling up the vortex, a pink ring at its foot, bigger shards (still flat). R3: a void portal standing behind the Shiba (black disc with glowing spiral arms, thick purple/pink/cyan rim, outer cyan ring, crystal struts) — now the most striking silhouette of all. |
