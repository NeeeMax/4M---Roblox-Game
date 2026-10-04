# Ratings Clock Tower (theme 29, Eternal Shiba)

Self-review of the 30 models (`build_ClockTower.py`, previews in `out/ClockTower/`), score 1-10 on silhouette, theme clarity,
proportion/attachment, low-poly consistency and wow. Everything below 8 was remade. R1 = first build, Final = what ships.
All models: one mesh, flat vertex colours, no Neon, 240 to 1820 triangles (most 600 to 1600; StarLamps about 1350).

| Part | R1 | Final | What changed |
|---|---|---|---|
| Ground | 8 | 8 | none (zodiac dais, gold plaza rings, star-white stepping stones along the walkway) |
| StarLamps | 7 | 8 | gold rings round the lanterns, star plate on the pole |
| TimeSign | 9 | 9 | none |
| CogGarden | 6 | 8 | mounds were underground (model 45 % too tall, squashed by the fit): now flat stone bases, fewer teeth |
| SandBenches | 8 | 8 | none |
| HourStones | 8 | 8 | none |
| SandTimers | 8 | 8 | fewer segments (1944 to 1584 triangles) |
| Pendulum | 7 | 8 | braces pointed outside the footprint (fit squeezed x to 0.87): now inward |
| Astrolabe | 9 | 9 | none |
| GrandfatherClocks | 8 | 8 | none |
| StarObelisks | 8 | 8 | none |
| GearFountain | 8 | 8 | fewer teeth and segments (1944 to 1520 triangles) |
| TimeBanners | 7 | 8 | base disc made the model twice as wide as the blueprint (fit 0.5 in x): slimmer base, no ticks on the emblem |
| CuckooHouse | 8 | 8 | dead code removed |
| StarPond | 8 | 8 | none |
| ZodiacWheel | 9 | 9 | none |
| RuneCircle | 8 | 8 | none |
| CogGate | 8 | 8 | fewer teeth (1648 to 1552) |
| BellArch | 8 | 8 | none |
| Sentinel | 8 | 8 | no ticks on the chest clock, fewer teeth |
| GiantSundial | 8 | 8 | none |
| TimeThrone | 9 | 9 | fewer segments (2028 to 1820) |
| Orrery | 8 | 8 | none |
| Engine | 8 | 8 | fewer teeth (1920 to 1696) |
| ClockBase | 8 | 8 | none |
| TowerShaft | 8 | 8 | none |
| ClockFace | 9 | 9 | none (four bezelled dials, stepped roof, corner spires) |
| ClockHands | 8 | 8 | blueprint hands rebuilt to match the kite-shaped hands (hour 3.6, minute 5.0 long, ten past ten on all four faces) |
| GearRing | 8 | 8 | fewer teeth (1872 to 1488) |
| Hourglass | 8 | 9 | blueprint posts moved inside the plates, sparkles pulled in so the fit is 1.0 |

Notes
- Hands, the dials and the hourglass are static (the game cannot animate the models); the design table's "moving hands" is a
  possible later effect on the ClockHands part.
- CogGate is built without its Yaw (-18.4), the game turns it onto the CD walkway segment.
- Fit scales are between 0.93 and 1.0 except ClockHands (y 1.15, thin hands), CogGarden (y 0.68 before the fix, about 1.0 after)
  and TimeBanners (x 0.5 before the fix).
- The tower parts 25 to 30 stack at (-50, -34): base to y 15, shaft 15 to 35, face and roof to 64, gear ring floating at y 24, hourglass
  floating at y 68 to 93 (all pieces above y 7 are non-solid for the layout rules).
