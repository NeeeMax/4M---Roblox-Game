# assets

Only models that code depends on. Keep this folder small; the world lives in the Roblox place.

## models/

| File | Studio name (`ReplicatedStorage/Assets/…`) | Used by |
|------|---------------------------------------------|---------|
| `Shiba.fbx` | `Shiba` — orange standard Shiba holding a `Stick` | Shiba Tier 1 (`Config/Gameplay → Shooters.Tiers`) |
| `ShadesShiba.fbx` | `ShadesShiba` — pixel "deal with it" shades, gold `$` chain, cigar treat | Shiba Tier 2 |
| `BuffShiba.fbx` | `BuffShiba` — huge throwing arm, pecs and abs, tiny head, red sweatband | Shiba Tier 3 |
| `ChefShiba.fbx` | `ChefShiba` — tall chef hat, curly moustache, red neckerchief, apron, flour puffs | Shiba Tier 4 |
| `PoliceShiba.fbx` | `PoliceShiba` — police cap with red/blue siren, mirrored aviators, badge, donut | Shiba Tier 5 |
| `NinjaShiba.fbx` | `NinjaShiba` — black fur, red eyes, red headband with tails, katana, purple smoke | Shiba Tier 6 |
| `GoldShiba.fbx` | `GoldShiba` — all gold, diamond eyes, tilted crown, coins, glints | Shiba Tier 7 |
| `GalaxyShiba.fbx` | `GalaxyShiba` — indigo → violet → pink → cyan fur with star specks, glowing cyan eyes, a ringed planet and a moon flying around the head (`Orbit`, `OrbitCenter`) | Shiba Tier 8 |
| `GiantShiba.fbx` | `GiantShiba` — kaiju: tiny buildings and trees, cracked ground, scars, orange eyes | Shiba Tier 9 |
| `CheemsGod.fbx` | `CheemsGod` — golden throne on clouds, sun halo, six wings, laurel crown, orbiting golden sticks | Shiba Tier 10 |
| `Stick.fbx` | `Stick` — chunky brown branch, stubby twig, two green leaves | projectile tier 1 (`Config/Projectiles`) |
| `Newspaper.fbx` | `Newspaper` — rolled up, cream with grey print bands and a red headline band, hollow ends | projectile tier 2 |
| `Baguette.fbx` | `Baguette` — slightly bent pointed loaf, golden crust, darker underside, pale score marks | projectile tier 3 |
| `RollingPin.fbx` | `RollingPin` — pale wooden barrel, red handles | projectile tier 4 |
| `BaseballBat.fbx` | `BaseballBat` — wood, black grip tape, red knob and barrel band | projectile tier 5 |
| `GiantBone.fbx` | `GiantBone` — cartoon bone, cream shaft, double ivory knobs | projectile tier 6 |
| `SqueakyHammer.fbx` | `SqueakyHammer` — red head with yellow bumpers and a white stripe, yellow handle | projectile tier 7 |
| `BonkSign.fbx` | `BonkSign` — yellow diamond road sign, black border, BONK on both faces, grey pole | projectile tier 8 |
| `NeonStick.fbx` | `NeonStick` — cyan → pink neon tube with lighter facets, dark handle with cyan rings | projectile tier 9 |
| `LegendaryStick.fbx` | `LegendaryStick` — faceted golden staff, big cyan crystal in golden prongs | projectile tier 10 |

Tier Shibas are `Body` + `ThrowArm` (upper arm, forearm and paw that throw) + `Shoulder` (tiny marker at the joint,
made invisible in the game; the arm turns around it) + `Stick` (in the paw). In the game the `Stick` stays hidden: the
paw holds a copy of the player's current projectile model instead (`HandProjectile`, lined up with the stick: its
longest side along the stick's, same length, grip on the stick's lower end), hidden for a moment after each throw; only
if no projectile model exists the `Stick` shows (`Config/Gameplay → Shooters.HandProjectile`). The client turns the
whole Shiba and swings `ThrowArm` with what is in the paw for the throw animation (`Controllers/ShibaController`).
Optional: an `Orbit` part that spins around a tiny `OrbitCenter` marker (made invisible), speed and axis per model in
`Config/ShibaEffects` (Galaxy Shiba: planet and moon flying around its head). `Tiers_preview.png` shows them all.

**Projectile contract** (all ten projectile FBX files): the long axis is Blender Z (→ Roblox model-local Y) and is the
longest side; the bounding box is centred at the origin; the end held in the paw is at -Z; plus a tiny marker mesh
`Grip` (0.02 cube, on the axis) exactly where the paw holds it. The game hides `Grip` and uses it to put the projectile
into the Shiba's paw. The visible mesh is one mesh named after the asset (e.g. `Baguette`), ≤ ~900 triangles.
Designed 1.0 long in Blender units (the game scales the longest side to the projectile diameter); the wide side is
along X (faces front in the paw). Chunky faceted shapes in 2–3 flat colours, no loose sparkles: effects (trail,
glow) come from the game. `Grip` in Blender units (x, y, z):

| Projectile | Grip | Triangles |
|------------|------|-----------|
| `Stick` | (-0.017, 0, -0.398) | 104 |
| `Newspaper` | (-0.006, 0, -0.36) | 264 |
| `Baguette` | (-0.046, 0, -0.34) | 544 |
| `RollingPin` | (0, 0, -0.41) | 356 |
| `BaseballBat` | (0, 0, -0.35) | 236 |
| `GiantBone` | (0, 0, -0.25) | 364 |
| `SqueakyHammer` | (0, 0, -0.397) | 360 |
| `BonkSign` | (0, 0, -0.40) | 884 |
| `NeonStick` | (0, 0, -0.36) | 288 |
| `LegendaryStick` | (0, 0.011, -0.38) | 164 |

`Projectiles_preview.png` shows them (re-imported from the exported files) and, below, each tier's Shiba holding its
tier's projectile by `Grip` on the paw stick's lower end, 0.75 × the stick's length.

`GalaxyShiba` has two more parts: `Orbit` (the banded planet with its little ring, and the moon, on a tilted circular
path around the head; the path itself is not drawn) and `OrbitCenter` (tiny marker at the path's centre, made
invisible in the game). The game spins `Orbit` around `OrbitCenter` about the path's axis, so the planet and moon
circle the head. In Blender units (model faces -Y, Z up, ~1.33 tall): centre (0, -0.097, 1.135), about 0.15 above
the eyes; path radius 0.54; axis (-0.265, 0.189, 0.946), i.e. tilted ~19° up on the stick side and slightly up at the
front; planet radius 0.11 (its ring 0.15), moon radius 0.05, both on the path. The whole path stays ≥0.18 away from
the dog and the stick (`ORBIT_*` in `build_shiba_tiers.py`).

A tier without its own model uses the next lower tier's model (shooters get an outline in the tier colour,
projectiles a trail). The old name `Shooter` still works as the last fallback for shooters. Output lists found and
missing models when a playtest starts.

Colours are baked into vertex colours because Roblox ignores FBX material colours (Blender 5.2).

Tier Shibas 1–10 and all projectiles 1–10 (`Stick` included) are Marco's designs, built from the same
`shiba_bonk_default.blend` (same pose and paw stick, own colours plus accessories from low-poly primitives) with
`build_shiba_tiers.py` (also writes `preview_tiers.png` and `preview_projectiles.png`):

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba_tiers.py -- <output folder>
```

The old one-piece orange Shiba comes from `shiba_bonk_default.blend` with `build_shiba.py` (it no longer writes
`Stick.fbx`); the committed `Shiba.fbx` is built by `build_shiba_tiers.py` (same model, throwing arm split out):

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba.py -- <output folder> export
```

Import in Studio: **Import** (Home tab) → pick the `.fbx` → Import, then move the model into
`ReplicatedStorage/Assets` and name it exactly as in the table. The code scales and orients it; without these models it
falls back to plain parts.

## Props (world models) — `models/props/`

Low-poly models in the Shiba style (flat-shaded, colours in the vertex colour attribute `Col`), one `<Name>.fbx` per
model, built by `build_props.py` (the statue, the Rainbow trophy and the ShooterTier stand reuse the dog from
`shiba_bonk_default.blend`). `props/Props_preview.png` shows all of them.

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_props.py -- props [<preview folder>] [<names>]
```

`PropService` uses `ReplicatedStorage/Assets/<Name>` when it exists: scaled so its **height** is what the code asks for,
**bottom centre on the ground** (hanging props, `Config/Props → Hanging`: top centre at the given point), **front = -Z /
LookVector** (Blender -Y). Imported props keep collisions (except `Config/Props → NoCollide`: flowers, clouds); a part
named `Glow` becomes Neon and gets the prop's light (`Config/Props → Lights`). Without a model it builds a part
placeholder and Output lists the missing names (`[PropService] No model …`); the pink "MODEL: <name>" labels are off
unless `Config/Props → ShowPlaceholderMarkers` is true.

| File (`models/props/`) | Studio name (`ReplicatedStorage/Assets/…`) | Used by | Height (studs) | Tris |
|------|------|------|------|------|
| `Prop_Tree.fbx` | `Prop_Tree` | trees on islands and hub | 11–16 | 412 |
| `Prop_Flowers.fbx` | `Prop_Flowers` | flower patches (no collisions) | 1.5 | 428 |
| `Prop_Lamp.fbx` | `Prop_Lamp` (parts `Body`, `Glow`) | lamps on bridges, `Glow` holds the PointLight | 7 | 334 |
| `Prop_IslandRock.fbx` | `Prop_IslandRock` | rock cone under each island (hangs from the island's bottom) | 70–72 | 486 |
| `Prop_Cloud.fbx` | `Prop_Cloud` | clouds (no collisions) | 12–22 | 560 |
| `Prop_SmallIsland.fbx` | `Prop_SmallIsland` | small floating islands in the distance | 10–18 | 846 |
| `Prop_ShibaStatue.fbx` | `Prop_ShibaStatue` | statue on the obby finish pad (ObbyService) | 16 | 3050 |
| `Prop_ObbyTower.fbx` | `Prop_ObbyTower` | column in the middle of the obby (the platforms are separate parts) | 40.2 | 1406 |
| `Prop_DailySpinMachine.fbx`, `Prop_CoinFlipMachine.fbx`, `Prop_ShopMachine.fbx`, `Prop_QuestsMachine.fbx` | same names | hub station machines, front toward the hub centre | 12 | 1152 / 940 / 1204 / 702 |
| `Prop_UpgradeStand_ShooterTier.fbx`, `…_ProjectileTier`, `…_Shooters`, `…_MoveSpeed` | `Prop_UpgradeStand_<UpgradeId>` | upgrade stands (StationService), front toward the path | 7 | 786 / 492 / 408 / 444 |
| `Trophy_Wood/Bronze/Silver/Gold/Galaxy/Starter/Streak/VIP/Diamond/Rainbow.fbx` | `Trophy_<Id>` | trophies on the island pedestals (TrophyService) | 4 | 268–982 |
| `Platform_<AssetName>.fbx` (Shiba, ShadesShiba, BuffShiba, ChefShiba, PoliceShiba, NinjaShiba, GoldShiba, GalaxyShiba, GiantShiba, CheemsGod) | `Platform_<AssetName>` (parts `Body`, `StandPoint`) | the platform each tier's Shibas stand on (NPCShooterService) | see below | 346–1650 |

`Prop_ObbyTower` is exactly 10 × 40.2 (TowerRadius 5, FinishHeight − Thickness − plaza): scaled to the tower height it
has the same footprint as the part tower. If `Config/Obby` changes those numbers, rebuild it with the new ratio.

Platforms (`Config/ShibaPlatforms`): NPCShooterService scales the model so its tiny `StandPoint` part (hidden in the game)
is `ModelTop` (else `Top`) studs above the island surface and its bottom `ModelSink` (0.5) below it, `StandPoint` right
above the Shiba's spot, front (-Z) toward the island centre. Visual only (the invisible barrier keeps players out).
`Platform_PoliceShiba` is a small police car; the Shiba stands on its roof (`ModelTop = 3`). Without the model the
part platform is built as before.

**Import in Studio**: Home → **Import 3D** (or Avatar → Import 3D) → pick the `.fbx` files from `assets/models/props/`
(several at once works) → keep the import options' defaults, make sure the vertex colours are imported → Import. Move
every imported **Model** (a one-mesh file may arrive as a single MeshPart, that works too) into `ReplicatedStorage/Assets` and keep its name exactly as the file name (e.g. `Prop_Tree`,
`Trophy_Gold`, `Platform_PoliceShiba`). Keep the part names inside (`Body`, `Glow`, `StandPoint`). No scaling or
rotating needed: the code does it. Start a playtest; Output lists props and platforms that are still missing.
