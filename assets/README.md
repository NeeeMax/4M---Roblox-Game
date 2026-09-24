# assets

Only models that code depends on. Keep this folder small; the world lives in the Roblox place.

## models/

| File | Studio name (`ReplicatedStorage/Assets/…`) | Used by |
|------|---------------------------------------------|---------|
| `Shooter.fbx` | `Shooter` — Shiba (`Body`) holding a `Stick` in its right paw | NPC shooters (`Config/Gameplay → Shooters`) |
| `Stick.fbx` | `Stick` | the thrown projectile (`Config/Projectiles`) |

Made from `shiba_bonk_default.blend` with `build_shiba.py` (Blender 5.2, colours baked into vertex colours because
Roblox ignores FBX material colours). Re-export:

```
blender --background --disable-autoexec shiba_bonk_default.blend --python build_shiba.py -- <output folder> export
```

Import in Studio: **Import** (Home tab) → pick the `.fbx` → Import, then move the model into
`ReplicatedStorage/Assets` and name it exactly as in the table. The code scales and orients it; without these models it
falls back to plain parts.
