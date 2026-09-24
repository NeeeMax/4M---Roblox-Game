# Architecture — 4M

## Principles

1. **Server is authoritative.** All game state, currency, damage, inventory and saving live on the server. The client requests, the server decides.
2. **One entry point per side.** `Main.server.luau` and `Main.client.luau` load every module in a fixed order. No other Scripts or LocalScripts.
3. **Shared code is pure.** Types, config, remote definitions and helpers. No side effects at require time.
4. **Strict types everywhere** (`--!strict`).

## Folder layout

```
src/
├─ server/                         → ServerScriptService/Server
│  ├─ Main.server.luau             # bootstrap: requires services, calls Init then Start
│  └─ Services/                    # one ModuleScript per server system (e.g. DataService)
├─ client/                         → StarterPlayer/StarterPlayerScripts/Client
│  ├─ Main.client.luau             # bootstrap: requires controllers, calls Init then Start
│  ├─ Controllers/                 # one ModuleScript per client system (input, camera, effects)
│  └─ UI/                          # UI logic (layout itself is built in Studio)
└─ shared/                         → ReplicatedStorage/Shared
   ├─ Net/                         # remote definitions — the only place remotes are created
   ├─ Types/                       # shared type definitions
   ├─ Config/                      # tuning values (replaces attributes)
   └─ Util/                        # pure helper functions
```

Subfolders are created when the first module goes into them.

## Module lifecycle

Every Service (server) and Controller (client) is a ModuleScript returning a table with:

- `Init()` — set up internal state, no calls to other services yet.
- `Start()` — connect events, talk to other services. Called after **all** `Init()` calls finished.

The bootstrap calls all `Init()`s first, then all `Start()`s. This gives a deterministic load order and removes most race conditions.

## Where does code go?

| Question | Place |
|----------|-------|
| Does it change game state, money, inventory, saving? | `server/Services` |
| Is it input, camera, UI, sound, visual effects? | `client/Controllers` or `client/UI` |
| Do both sides need the same value or type? | `shared/Config` or `shared/Types` |
| Does client and server need to talk? | define in `shared/Net`, document in `docs/NETWORK.md` |

## Ownership

Work is split by feature area. The owner reviews changes in their area and decides its internals.

| Area | Owner | Notes |
|------|-------|-------|
| `shared/Net`, `shared/Types`, `CLAUDE.md`, `docs/CONVENTIONS.md` | both | contract files — changes in separate PRs, both approve |
| All game code: islands, NPC shooters, projectiles, hit detection, bonk effects, economy, upgrades, shop, HUD, saving | Max | only EconomyService / UpgradeService change Bonk Points or upgrade levels |
| 3D models and other visual assets (islands, shooters, projectiles, UI art, effects) | Marco | built in Studio, not in git (see *World vs code*); code finds them by stable names |

## World vs code

- **In git:** all Luau code.
- **In the Roblox place (not git):** maps, models, parts, UI layouts, lighting, sounds.
- **MVP exception:** islands, shooters, projectiles and the HUD/upgrade menu are created by code, so the prototype runs in an empty Baseplate place. Moving them to Studio-built assets later is fine.
- Code references world objects by stable names/paths. When you rename something in the world that code uses, update the code in the same session and mention it in the PR.
