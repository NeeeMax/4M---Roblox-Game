# assets

Only models that code depends on. Keep this folder small; the world lives in the Roblox place.

## models/

| File | Studio name (`ReplicatedStorage/Assets/…`) | Used by |
|------|---------------------------------------------|---------|
| `Shiba.fbx` | `Shiba` — orange standard Shiba holding a `Stick` | Shiba Tier 1 (`Config/Gameplay → Shooters.Tiers`) |
| `GalaxyShiba.fbx` | `GalaxyShiba` — Galaxy Shiba (`Body`, `Stars`) holding a `Stick` in its raised paw | Shiba Tier 2 |
| — | `GodShiba` (not built yet) | Shiba Tier 3 |
| `Stick.fbx` | `Stick` | projectile tier 1 (`Config/Projectiles`) |
| — | `Bone`, `GoldenStick`, `DiamondStick` (not built yet) | projectile tiers 2–4 |

A tier without its own model uses the next lower tier's model (shooters get an outline in the tier colour,
projectiles a trail). The old name `Shooter` still works as the last fallback for shooters. Output lists found and
missing models when a playtest starts.

Colours are baked into vertex colours because Roblox ignores FBX material colours (Blender 5.2).

`GalaxyShiba.fbx` is Marco's Galaxy Shiba, made from `galaxy_shiba.obj` + `.mtl` (three-d-stage export, kept outside git)
with `build_galaxy_shiba.py`. It paints the fur with a galaxy gradient and joins the ~1,000 source objects into
three meshes. Re-export:

```
blender --background --factory-startup --python build_galaxy_shiba.py -- galaxy_shiba.obj <output folder> export
```

`Shiba.fbx` and `Stick.fbx` come from `shiba_bonk_default.blend` with `build_shiba.py`:

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba.py -- <output folder> export
```

Import in Studio: **Import** (Home tab) → pick the `.fbx` → Import, then move the model into
`ReplicatedStorage/Assets` and name it exactly as in the table. The code scales and orients it; without these models it
falls back to plain parts.

## Props (world models, not in git)

Built in Studio by Marco and put into `ReplicatedStorage/Assets` with exactly these names. Until then `PropService` builds
a placeholder (pink box + "MODEL: <name>" label in Studio). Models are scaled to the height the code asks for; their
bottom sits on the ground, their front (-Z / LookVector) faces the way the placeholder faces.

| Name | What | Height (studs) |
|------|------|----------------|
| `Prop_Tree` | tree on islands and hub | 11–16 |
| `Prop_Flowers` | small flower patch | 1.5 |
| `Prop_Lamp` | lamp post on bridges (should contain a light) | 7 |
| `Prop_IslandRock` | rocky cone under a floating island (hangs down from its top) | 70–72 |
| `Prop_Cloud` | cloud | 12–22 |
| `Prop_SmallIsland` | small floating deco island with a tree | 10–18 |
| `Prop_ShibaStatue` | big Shiba statue in the hub centre | 16 |
| `Prop_DailySpinMachine`, `Prop_CoinFlipMachine`, `Prop_ShopMachine`, `Prop_QuestsMachine` | hub station machines, front toward the hub centre | 12 |
| `Trophy_Wood`, `Trophy_Bronze`, `Trophy_Silver`, `Trophy_Gold`, `Trophy_Galaxy`, `Trophy_Starter`, `Trophy_Streak`, `Trophy_VIP`, `Trophy_Diamond`, `Trophy_Rainbow` | trophies on the island pedestals | 4 |
