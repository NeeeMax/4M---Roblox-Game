# FoodTruck decor ratings

Score 1-10 per round (silhouette at distance, theme clarity, proportion/attachment of details, low-poly consistency, wow).
Anything below 8 was remade (up to 4 rounds). Triangles are the final counts (about 1500 max, 1 mesh per part, flat vertex colours, no Neon).
All models are built by `build_FoodTruck.py` from `blueprint_FoodTruck.json` (exported from `DecorTheme04.luau`, validator 0 errors); every model is fitted to the union box of its blueprint pieces (fit scales 1.000 to 1.020, trucks 1.006 in x).

| Part | R1 | R2 | Final | Tris | What changed |
|------|----|----|-------|------|--------------|
| Paving | 7 | 8 | 8 | 552 | R1: plain two-tone checker with diamonds. R2: raised tiles on dark grout, cream/red diamond inlays and a small yellow stud in every tile. |
| TruckBurger | 8 | 8 | 8 | 1504 | White van with red stripe, serving window under a red-white sloped awning with valance and two poles, cab with sloped glass, grille, bumper, wheels with hub caps, roof sign BURGER with border, roof unit, exhaust, burger badge on the rear wall. R2 only trimmed 1592 to 1504 triangles (wheel flares, door handle, bell ball, pipe cap removed). |
| TicketBooth | 7 | 8 | 8 | 664 | R1: TICKET lettering was hidden under the striped roof fascia. R2: sign band lowered and enlarged, window shortened, fascia shortened. Red booth, hip roof with ridge cap and yellow finial, wooden counter with ticket roll, bell and tickets, side door, posters. |
| TruckTaco | 8 | 8 | 8 | 1280 | Same truck kit in teal with yellow stripe, orange-white awning, TACO sign, taco badge (yellow shell with lettuce and tomato). |
| Tables | 8 | 8 | 8 | 784 | Two picnic tables with plank tops, checkered runners (red and green), A-frame legs, planked benches, ketchup, mustard, napkin holder. R2: leg bars no longer dip below the ground. |
| Lights | 7 | 8 | 8 | 980 | R1: bulbs read as brown rocks. R2: teardrop bulbs in two warm tones with dark sockets, sagging wire, tapered wooden poles with steel caps and dark collars. |
| Fountain | 7 | 8 | 8 | 1136 | R1: outer water arcs looked like spider legs, then like pillars. R2: only the spray from the top ball falls into the upper bowl. Round stone basin with rim blocks, pedestal, upper bowl with lip and water, column. |
| Umbrellas | 8 | 8 | 8 | 920 | Two round tables with eight-panel striped umbrellas (orange, teal), white table tops with coloured edge, four stools each, ketchup, mustard, napkins. |
| TruckPizza | 8 | 8 | 8 | 1352 | Red van with white stripe, green-white awning, PIZZA sign (red on white), pizza slice badge with pepperoni. |
| Planters | 7 | 8 | 8 | 1296 | R1: flowers were bare hexagon discs. R2: yellow/brown flower centres, rim ring, brick courses in two shades, leafy cones; three different flower mixes. |
| Bins | 8 | 8 | 8 | 724 | Two steel bins with bands, domed lids with flap and handle, foot pedals and labels, blue recycling bin with sloped lid, slot and white triangle sign. Preview Shiba moved aside so the labels are visible. |
| Menus | 8 | 8 | 8 | 800 | Two chalkboards on wooden legs and frames: MENU with three coloured rows and prices, TODAY with a pizza slice and a drink. Chalk text reads from +z. |
| TruckDessert | 8 | 8 | 8 | 1440 | Pink van with raspberry stripe, orange-white awning, SWEETS sign, ice cream cone badge. |
| Stage | 7 | 8 | 8 | 1492 | R1: the FOOD banner sat behind the truss and spotlights, 1836 triangles. R2: banner lowered below the lights, curtain folds 11 to 7, lamps simplified, planks 7 to 5, one speaker cap and the cutlery icons removed. Planked deck with yellow/red trim, red curtain backdrop with header, truss on two poles with four spotlights, two speaker stacks with woofers, teal drum kit with cymbals, two amps, mic stand. |
| GiantBurger | 9 | 9 | 9 | 1264 | Steel plinth with yellow bulbs, bottom bun, rough patty, cheese with drooping corner tips and a rotated second slab, ruffled lettuce, tomato, domed top bun with sesame seeds. |

Notes on the review images
- Previews are NOT flipped: decorkit mirrors the meshes in x before the export, so a render of the exported meshes from the road side is the in-game view and lettering reads correctly. The reference Shiba (6 studs tall) is placed mirrored for the same reason.
- `stage_FoodTruck.png`: 3/4 view from the road above, top view below, reference Shiba at the plaza spot beside the fountain.
- Text and signs (BURGER, TACO, PIZZA, SWEETS, TICKET, MENU, TODAY, FOOD) face +z (road side).
- Openings stay open: no model closes the plaza paths; the awning poles of the trucks stand at the truck's own footprint edge (z up to +6.1, inside the blueprint box).
