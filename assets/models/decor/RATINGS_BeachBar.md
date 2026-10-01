# Ratings: Decor BeachBar

Scores 1-10 per round (mean of: silhouette at distance, theme clarity, proportion/attachment of details, consistency with the
low-poly style, wow factor). Anything below 8 was remade; the final column is the score of the shipped models.
Build: `blender --background --factory-startup --python build_BeachBar.py -- <outdir>` (default `out/BeachBar`).
Every model was fitted to the union box of its blueprint pieces and the exported FBX was re-imported and measured: deviation 0.000 studs on all 10.

| Part | R1 | R2 | R3 | Final | Tris | What changed |
|---|---|---|---|---|---|---|
| SandFloor | 6 | 7 | 8 | 8 | 1493 | R1: flat sand slab with tile-like facets, plain sea. R2: wavy wet-sand band, zig-zag surf line, wave crests, patches, footprints, starfish. R3: smooth Gouraud colour field instead of visible tiles (no more parquet look), wavy white lines on the sea, deep-water band, dune streaks, sand dollars, seaweed line, driftwood, three crabs; everything stays under the 0.5 stud top. |
| BarHut | 6 | 7.5 | 8 | 8 | 1493 | R1: dark brown lid for a roof, sign hid the counter. R2: thatch built from 4 layers with straw streak cuts, shaggy fringes on three levels, ridge roll, brighter straw colours; BAR sign moved onto the roof edge so the counter, bottles, cups and stools show; letters fixed to read correctly; window with shutters, flower box, lifebuoy, shelf with bottles; tris cut from 1780 to under 1500. |
| Kiosk | 7 | 8 | 8.5 | 8.5 | 1066 | R1: striped awning, candy counter, cones. R2: slanted walls following the awning, scalloped front, cone rack. R3: hanging ice cream cone sign, big cone icon on the road side wall, chalk menu, jar shelf, freezer chest. |
| PalmTrees | 6 | 7.5 | 8 | 8 | 1371 | R1: thin trunks, 7 stiff 4-segment fronds. R2: banded leaning trunks, 10 feathered fronds (zig-zag leaflet outline, arched), young upright fronds, sand mounds. R3: coconut clusters peeking out of the crown (lighter brown so they read), more lean per tree. |
| Parasols | 6.5 | 7.5 | 8 | 8 | 866 | R1: two panelled umbrellas, three loungers. R2: scalloped rim tabs on the canopies, darker undersides, wooden side tables with drinks. R3: sandcastle with red-roofed keep, bucket and beach ball in the free corner. |
| Surfboards | 6 | 7.5 | 8 | 8 | 752 | R1: transverse bands read as crosses. R2/R3: real board outlines (pointed nose, wide hips) tilted in a fan, two-tone tail and nose caps, star logo, fins on the back, rope ties; stringer removed because it made the nose look like an arrow; tall rack posts with caps and two bars. |
| Volleyball | 7.5 | 8 | 8 | 8 | 474 | Padded posts with caps, net made of real holes (tapes, strands, cords), court sand and white lines exactly at the footprint, corner flags, panelled beach ball. Only polish between rounds (lighter court sand). |
| Boat | 6.5 | 7.5 | 8 | 8 | 490 | R1: lofted hull with red gunwale, belly sails. R2: cream upper strakes, light floor, dark thwarts so the interior reads, forestay and backstay. R3: foam collar where the hull meets the sea, colourful bunting along the forestay, rope coil, oar, orange vest. |
| TikiCooler | 6 | 7.5 | 8 | 8 | 1054 | R1: torches read as plain pillars with orange acorns. R2: bamboo poles with dark node bands, wide cups, three flame tongues plus a yellow core, rope between the torches. R3: bunting on all four ropes, striped beach towel, coconut drinks, bottles, fish sticker and latches on the cooler. |
| Lifeguard | 7 | 8 | 8.5 | 8.5 | 962 | White legs with footings and X braces, platform with planks, red cabin with white stripes and cross, rail with ladder gap, real ladder, red/white roof trim, red-and-yellow waving flag (two-tone), rescue can in the sand, ring buoy, porthole, seagull on the roof. |

## Notes on the rating criteria
- Silhouette: all parts keep a distinct outline at the stage distance (thatch fringe, striped awning, crowned palms, sails, flag and roof of the tower, tall net posts).
- Theme clarity: BAR sign + thatch + stools + bottles, ice cream cones on sign and icon, palms with coconuts, umbrellas + loungers + sandcastle, surfboards in a rack, volleyball net, sailboat, tiki torches with a cooler, lifeguard tower with ring buoy.
- Palette is shared across all ten parts (sand, teal, red, white, yellow, palm greens, straw, wood browns, sea blues) and every part is flat vertex colours with a little per-face jitter; no neon, no textures.
- All parts are one mesh each (the project limit is 4); the largest are BarHut, SandFloor and PalmTrees at about 1.4-1.5k triangles.
