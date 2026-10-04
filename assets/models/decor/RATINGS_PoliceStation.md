# PoliceStation decor ratings

Score 1-10 per round (silhouette at distance, theme clarity, proportion/attachment of details, low-poly consistency, wow).
Anything below 8 was remade (up to 4 rounds). Triangles are the final counts (limit 1500, max 4 meshes).
All models were rebuilt by `build_PoliceStation.py` from `blueprint_PoliceStation.json`; every model is fitted to the union box of its blueprint pieces (fit scales 0.97 to 1.03).

| Part | R1 | R2 | R3 | R4 | Final | Tris | Meshes | What changed |
|------|----|----|----|----|-------|------|--------|--------------|
| Floor | 7 | 8 | - | - | 8 | 1304 | 1 | R1: layers only 0.02 apart (z-fight at distance), tiny badge star. R2: all paint layers at least 0.04 apart (blueprint blue square made taller to give room), bigger yellow star on the Shiba badge circle, 8-pointed gold star in the monument plaza, checker plaza, kerb stripe, candy-striped donut pad, bay lines and arrows, helipad and roadblock markings. |
| Station | 7 | 8 | - | - | 8 | 1312 | 2 (Body, Roof) | R1: plain facade. R2: second window row on the outer bays, wall lamps by the door, gold star on the blue belt, stars on the wings, clock + POLICE sign on the tower, garage door with hazard strip, roof flag. U-shape wraps the Shiba courtyard. |
| Cars | 7 | 8 | - | - | 8 | 1080 | 1 | R1: wheels hidden inside the body, boxy cabin. R2: wheels stick out of the body with hub caps, sloped glass cabin, blue door stripe, red/blue light bar, head and tail lights, black hood and trunk. |
| Cells | 7 | 8 | - | - | 8 | 1188 | 2 (Body, Roof) | R1: dark roof swallowed the building, floating yellow cube on the tower. R2: lighter concrete roof with parapet and vent, pilasters between the barred windows, JAIL sign with stars, guard tower with braces and a lamp, open chain-link fence with gate posts. |
| Donuts | 9 | 9 | - | - | 9 | 1124 | 2 (Body, Roof) | Cream shop with striped awning, DONUTS sign, giant pink-iced donut (real ring with sprinkles) on the roof, chimney, two stools. |
| Beacon | 8 | 8 | - | - | 8 | 960 | 1 | Lattice tower with braces, three platforms, ladder, cab with star and window band, red and blue siren domes. R2 only joined the antenna to the light housing (it floated over the gap between the domes). |
| Range | 8 | 8 | - | - | 8 | 992 | 1 | Timber sleeper backstop with posts, four ringed targets on stakes, shooting bench with lane dividers, ear defenders and ammo boxes. |
| Kennel | 6 | 8 | - | - | 8 | 1404 | 1 | R1: the doghouse doors faced away from the player and were invisible. R2: hollow doghouses with the door toward the run and a dog (shiba, black lab, white) looking out of each, picket fence open at the front, bowls, K-9 sign with bones readable from both sides (mirrored copy). |
| Heli | 8 | 8 | - | - | 8 | 876 | 1 | Round helipad with yellow ring and H, blue police helicopter with glass nose, star badge, light bar, tail rotor and white-tipped blades. R2: spacing of the pad layers raised to avoid flicker. |
| Roadblock | 8 | 8 | - | - | 8 | 1144 | 1 | Three red/white striped barriers with amber lamps, four banded cones, spike strip with spikes, STOP sign with lettering. |
| Swat | 8 | 8 | - | - | 8 | 796 | 1 | Black armoured van with SWAT lettering and yellow stripes on the road side, sloped windscreen, bull bar, roof light bar and breaching ram, wheels with hubs. |
| Wanted | 8 | 8 | - | - | 8 | 1044 | 1 | Billboard on two posts with braces and bolted bases, big WANTED lettering, masked bandit in a striped shirt, coins and money bag, lamp rail with three lamps. |
| Impound | 6 | 7 | 8 | - | 8 | 1460 | 1 | R1: wrecks were plain boxes and the yard was empty. R2: wrecks rebuilt as rusty cars (missing wheels). R3: two more wrecks stacked on top (crushed roofs), POUND gate arch, TOW lettering, tyre pile; over-budget version (1924) trimmed to 1460 by thinning the fence posts and hub details. |
| Bikes | 6 | 6 | 7 | 8 | 8 | 1420 | 1 | R1: closed roof hid the bikes, bikes faced the road. R2: bikes turned around, slatted roof (still hid them). R3: slatted roof over the whole stand, bikes still under it. R4: lean-to roof only over the back half with stripes, bikes parked side on in the open half so the silhouette reads, POLICE lettering on the inside of the back wall (mirrored text for the stage side). |
| Monument | 9 | 9 | - | - | 9 | 1284 | 1 | Stepped base, navy pedestal with gold trim and BONK plaque, eight-pointed gold badge with ball tips, blue disc and white star, four lamp posts. |

Notes on the review images
- Previews are NOT flipped: decorkit mirrors the meshes in x before the export (checked in Studio by the previous themes), so a render of
  the exported meshes from the road side is the in-game view and the lettering reads correctly. The reference Shiba (6 studs tall) is
  placed mirrored for the same reason. Kennel and Bikes are shot from the deeper side (-z) because their open sides face the plot.
- `stage_PoliceStation.png`: 3/4 view from the road above, top view below (roofs hidden), reference Shiba on the blue badge circle.
- The fit scale of each model is printed by the build script (`FIT`); the largest is 0.968 in z for Wanted.
