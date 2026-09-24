# assets

Only models that code depends on. Keep this folder small; the world lives in the Roblox place.

## models/

| File | Studio name (`ReplicatedStorage/Assets/…`) | Used by |
|------|---------------------------------------------|---------|
| `Shooter.fbx` | `Shooter` — Galaxy Shiba (`Body`, `Stars`) holding a `Stick` in its raised paw | NPC shooters (`Config/Gameplay → Shooters`) |
| `Stick.fbx` | `Stick` | the thrown projectile (`Config/Projectiles`) |

Colours are baked into vertex colours because Roblox ignores FBX material colours (Blender 5.2).

`Shooter.fbx` is Marco's Galaxy Shiba, made from `galaxy_shiba.obj` + `.mtl` (three-d-stage export, kept outside git)
with `build_galaxy_shiba.py`. It paints the fur with a galaxy gradient and joins the ~1,000 source objects into
three meshes. Re-export:

```
blender --background --factory-startup --python build_galaxy_shiba.py -- galaxy_shiba.obj <output folder> export
```

`Stick.fbx` (and the earlier orange Shiba) come from `shiba_bonk_default.blend` with `build_shiba.py`:

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba.py -- <output folder> export
```

Import in Studio: **Import** (Home tab) → pick the `.fbx` → Import, then move the model into
`ReplicatedStorage/Assets` and name it exactly as in the table. The code scales and orients it; without these models it
falls back to plain parts.
