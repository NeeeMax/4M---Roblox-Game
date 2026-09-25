# Model quality ratings

Self-review log of the model agents: every build round, each model's close-up (`preview_<Asset>.png`) and the row
preview (game-like distance) are rated 1–10 on silhouette at distance, theme clarity, attached/proportioned
accessories, consistency with the low-poly Shiba style, and wow factor for the tier position. Below 8 → rework.

## Shibas (new top set)

Built by `build_shiba_tiers.py` (`THIRD_DESIGNS`), preview `Tiers_top_preview.png`. Tier = position in the brief
(later = more impressive). Target: all ≥ 8, Eternal and Void ≥ 9.

| Tier | Asset | R1 | R2 | R3 | R4–6 | Final | What changed |
|------|-------|----|----|----|------|-------|--------------|
| 5 | `DJShiba` | 8 | 8 | 8 | 8 | **8** | R2: bigger backwards visor so the cap doesn't read as a beret. |
| 11 | `KnightShiba` | 6.5 | 8 | 8 | 8 | **8** | R1 breastplate read as cream, visor as a cap brim, plume tiny. R2: darker steel gradient, red cross, visor stands up on the forehead with slits and gold edge, fan of tall red plume feathers, dark leather belt. |
| 15 | `SuperheroShiba` | 6 | 7 | 7 | 8 | **8** | R1 mask was a ring floating like a hat brim, cape invisible from the front. R2: domino mask painted per face on the head + white lenses, bigger B emblem, wider cape. R3: stand-up collar, cape over the shoulders. R4: cape blown out sideways (away from the throwing arm) so it reads from the front. |
| 20 | `FrostShiba` | 7 | 8 | 8 | 8 | **8** | R2: more saturated ice fur, frozen floor in pale ice (was white), bigger ground shards, smaller snowy collar. |
| 21 | `MagmaShiba` | 6 | 6.5 | 8 | 8 | **8** | R1/R2 per-face veins looked like tortoiseshell patches, crown looked like castle towers. R2: glowing zigzag crack bars following the fur. R3: molten glowing belly/muzzle/paws, fewer vein faces, obsidian spike crown around a small volcano with a lava blob. |
| 23 | `MechaShiba` | 7 | 7.5 | 8 | 8 | **8** | R2: thrusters moved out so the exhaust shows, knee boxes replaced. R3: angular faceted helmet with crest, boots with yellow trim, floating thigh plates removed. |
| 25 | `AngelShiba` | 6 | 7 | 8 | 8 | **8** | R1 wings looked like fishbones (thin arm, sparse feathers). R2/R3: fuller wing helper (more, wider feathers hanging down and fanning out), upswept wings, gold tips, no blue row; cloud made lower-poly. |
| 26 | `DemonShiba` | 7.5 | 7.5 | 8 | 8 | **8** | R2: flames as teardrop bulbs with tongues and yellow cores. R3: bigger ring of fire, flame on the free shoulder. |
| 29 | `EternalShiba` | 7.5 | 8 | 8.5 | 9 | **9** | R1 dog washed out in gold-on-gold, cyan ring crossed the face. R2: ring moved down to the feet, wings fuller. R3: night-blue starry dial inside the clock halo (makes the white/gold dog pop), star-white fur. R4: bigger runes, thicker ring. |
| 30 | `VoidShiba` | 7 | 8 | 8 | 9 | **9** | R1 disk looked like a floor rug, tentacles hidden. R2: narrower tilted disk, bigger shards, bigger eyes on the halo. R3: glowing crack bars, curling spiral tentacles. R5: bigger black hole with longer spikes on top (tall "dark sun"), diagonal accretion disk crossing the silhouette, tentacles pushed back so the dog stays readable. |

Notes:
- The row preview is not scaled to the in-game Heights; in the game Eternal (16) and Void (18) tower over Cheems God
  (12), and the recommended Heights keep the dog itself growing from ~5 studs (DJ) to ~7.7 studs (Void).
- The close-up renders are Workbench (studio light); the black-hole sphere shows its facets there, in Roblox it is
  darker with the Void effects on.

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
