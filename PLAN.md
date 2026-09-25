# PLAN — economy, bonk loop and island layout rework (GET BONKED)

Branch `feat/economy-v2` (integration). Prompt: "Shiba Bonk" rework (economy, gameplay loop, island layout), adapted to
this game with Marco's answers: adapt to our game, build the best bonk variant, hand off to Max via Discord if needed,
enough budget.

## Phase 0 — Recon

**Toolchain:** Rojo-compatible layout + Studio Script Sync, `stylua`, `selene`, `luau-lsp`, `rojo` (rokit), now also
`lune` (runs the economy simulation outside Roblox). No Wally. The world is built by code (islands, stands, props), so
the layout is changed in code, not in an .rbxl.

**Where things live**

| System | Files |
|--------|-------|
| Money | `EconomyService` (add/spend, server only), `DataService` (saved `BonkPoints`), `Util/Format` (numbers) |
| Shiba purchases | `UpgradeService.TryPurchase` (ShooterTier = Shiba evolution, Shooters = number of Shibas), `StationService` (stands + NEW SHIBA pad), `UpgradeController` (menu) |
| Bonk logic | `BonkService` (server validation + reward), `BonkController` (popup, sound, knockback), `ProjectileService`/`ProjectilePath`, `NPCShooterService` (throws) |
| Shop stalls | `Config/Stations` + `StationService` (server) + `StationController` (billboards, hints) |
| Save | `DataService` (DataStore `PlayerData_v1`, `Types.PlayerState`) |
| UI | `client/UI/Widgets`, `HudController`, `UpgradeController`, `ShopController` |

**Hardcoded economy values before the rework**

| Name | File | Value |
|------|------|-------|
| Upgrade cost formula | `Config/Upgrades` | `BaseCost × Growth^n × (1 + Curve n²)` |
| Shiba Tier (ShooterTier) | `Config/Upgrades` | Base 400, Growth 3.5, Curve 0.1, max 9 |
| Projectile Tier | `Config/Upgrades` | Base 150, Growth 3.6, Curve 0.15, max 9 |
| More Shibas | `Config/Upgrades` | Base 60, Growth 5.5, Curve 0.2, max 7 (+2 pass) |
| Move Speed | `Config/Upgrades` | Base 40, Growth 3.5, Curve 0.1, max 10 |
| Shiba tier RewardMultiplier | `Config/Gameplay` | 1, 1.6, 2.5, 3.9, 6.2, 9.7, 15, 24, 38, 60 |
| Shiba tier FireInterval | `Config/Gameplay` | 5, 4.3, 3.7, 3.2, 2.7, 2.4, 2, 1.8, 1.5, 1.3 s |
| Projectile BaseReward | `Config/Projectiles` | 10, 13, 16, 20, 25, 32, 40, 50, 63, 80 |
| Hit quality multipliers | `Config/Economy` | Normal 1, Good 2, Hard 5, Massive 10, Legendary 50 (by impact speed ratio) |
| Head / combo / golden | `Config/Gameplay` | ×2 / +0.1 per hit up to ×3 / ×5 |
| Starting money | `Config/Economy` | 0 |
| Trophies | `Config/Shop` | 5K, 50K, 500K, 5M, 100M total earned |
| Offline bank | `Config/Economy` | 10 % of recent income, max 8 h |
| Duel stakes / coin flip min | `Config/Hub` | 100 … 100,000 / 10 |
| Passes | `Config/Shop` | 2× Dollars ×2, VIP ×1.25, Lucky 15 % golden |

**Simulation of the old economy** (`lune run docs/economy/current_economy.luau`, player always buys the cheapest
upgrade): 35 purchases, 16 of them "Shiba" purchases (More Shibas + Shiba Tier).

| Shiba purchase | Play time |
|----------------|-----------|
| 1st | 63 s (first purchase of any kind: 26 s) |
| 5th | 13 min |
| 10th | 54 min |
| 16th (last) | 7.5 h |
| 20th | does not exist |

Why it feels slow / out of proportion: the first buy takes 26 s (target < 5 s); the wait never settles — it keeps
growing from ~40 s to 65 min per purchase (costs grow ×3.5–5.5 per level, income only ×1.6 per Shiba tier); Move Speed
is bought 10 times for +2 % catch rate each (payback of hours); the whole game ends at 6.7e7, so there is no long
number-go-up; nothing earns while you stand still.

## Why the bonk loop feels boring / unintuitive (Workstream C analysis)

1. **Invisible rule:** quality comes from the relative impact speed (run + jump into the stick). Players can't see
   it, so ×2 / ×5 / ×50 feel random.
2. **No telegraph:** long lobs land anywhere in the field and you must read the arc; arriving late is frustration, not
   skill.
3. **Standing still earns 0** (anti-farm): no idle layer at all except the Auto-Catch pass.
4. **Flat feedback:** every hit gets nearly the same popup; the combo is a small bar.
5. **Throwables** only change the model and the number.

**Variants**

- **V1 "Catch timing" (chosen).** A landing ring shows where each stick will land and shrinks until it lands.
  Quality depends on *when* you catch it: after it hit the ground = BONK ×1, in the air = AIR BONK ×2, in the last
  moment before it lands (ring almost closed) = PERFECT BONK ×4. Head ×2 and combo up to ×3 stay. Big juice on
  Perfect (sound, shake, coin burst), per-throwable impact effects. Idle layer: basket + intern catch the sticks you
  miss at a lower rate. Readable in one second, works on mobile, no new input.
- **V2 "Headbutt button":** press a button to headbutt/dash with a timing window. More skill, but a new input
  (mobile), and it doesn't fix the arc-reading problem.
- **V3 "Rhythm bonks":** Shibas throw on a beat; catching on the beat multiplies. Fun but needs music sync and is
  hard to read with 8 Shibas.

## Shared contract (commit "contract", before the agents)

- **`src/shared/Config/EconomyConfig.luau`**: single source of truth. Prices are derived from the target pace
  `T(n) = 90 − 86 · e^(−n/22)` s over a Route of all 67 purchases of a run; the last Shiba costs
  `FINAL_SHIBA_COST = 1e33`; Shiba tier multipliers grow by a solved factor (~×8.3). Also bonk multipliers, rebirth,
  automation tables, trophy thresholds, `StartingMoney` (= price of the first purchase). No requires, so
  `lune` can load it.
- **30 Shibas:** the 10 models + "Shiny" and "Mythic" editions (same model, outline/aura colour). Models unchanged.
- **NumberFormat = `Util/Format`:** K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc, UDc, DDc … NoDc, Vg … up to 1e303;
  `Format.Money` writes ≥ 1e6 short, `Format.Number` ≥ 1e15 short.
- **Server-authoritative:** unchanged — clients only request; `UpgradeService`, `RebirthService`, automation pay-outs
  run on the server.
- **Save:** `SAVE_VERSION` 2. New fields `Rebirths`, `Tutorial {Step, FirstBonkDone}`, `Bank.AutomationPerMinute`,
  levels `Basket`, `Intern`. Version-1 saves keep everything (levels, money); old players skip the tutorial.
- **Types:** `UpgradeId` + `"Basket" | "Intern"`, `HitQuality = "Normal" | "Good" | "Perfect"`, `AutomationSource`.
- **Net:** new `AutomationCatch` (S→C, visual only).
- **Helpers:** `RewardService.GetStickValue` (stick value incl. tier, rebirth, golden, passes, boosts, events),
  `RewardService.GetRebirthMultiplier`, `RebirthService.TryRebirth / CanRebirth`.
- **Layout:** `Config/Stations` `Zones`, `Stalls` (polar: angle from the bridge direction, radius), `NewPlayerSpawn`,
  `MinStallDistance = 30`.

## Workstreams (agents, each in its own worktree + branch; nobody pushes, I merge)

| Workstream | Branch | Owns (files) |
|------------|--------|--------------|
| A economy | `feat/v2-economy` | `EconomyConfig` numbers, `docs/economy/*` (simulate.luau, BALANCING.md), `LeaderboardService` (1e33-safe), `OfflineService` + `Config/Economy` bank, `Config/Shop` trophies, `Config/Index` + `IndexService` (30 Shibas), `AdminService`/`AdminController` (rebirth tools), `UpgradeController` (menu for 6 upgrades, rebirth card), `RebirthController` (new, rebirth info UI) |
| C bonk | `feat/v2-bonk` | `BonkService` (timing quality, first-bonk bonus), `ProjectileService.ClosestApproach` time, `ProjectileController` (landing ring), `BonkController` (juice), `Config/Gameplay` Hits/Bonk juice values, `AutoCatchService`, `Config/Hub` quest text, `NPCShooterService` edition looks (outline + aura for Shiny/Mythic) |
| D automation | `feat/v2-automation` | `AutomationService` (new: basket + intern), `AutomationController` (new: visuals), `Config/Automation` visuals only |
| E layout | `feat/v2-layout` | `StationService` (stalls from `Stalls`, zone signs, paths, rebirth shrine, locked stalls), `Config/Stations`, `IslandService` decor (trees away from zones), `PropService` builders |
| B onboarding | `feat/v2-onboarding` | `IslandService` spawn for new players, `StationController` (beams, pulsing highlight, ≤ 4-word hints, next-Shiba silhouette with price + progress bar, rebirth/locked billboards), `TutorialController` (new) |

Merge order: economy → bonk → automation → layout → onboarding. Then: re-run the simulation with automation +
active multipliers, check the targets (first purchase < 5 s, minute rhythm around Shiba 8–12, last Shiba ≈ 1e33,
no absurd payback), docs (`GAME_DESIGN.md`, `NETWORK.md`, `ARCHITECTURE.md`), build label, push, report.

## Island layout (Workstream E)

```
                     bridge to hub (0°)
                          ║
            SPEED GYM  .──╨──.   name sign
              (30°) .-'        '-.
                  /   (Shibas r56)  \        SHIBA SHOP
                 /    .--------.    \  ◄── Shiba Tier (62°)
    REBIRTH     |    /  field   \    |    SPAWN (90°, r72) → NEW SHIBA pad (90°, r56)
    (270°) ◄──  |   |   r 30     |   |    More Shibas (118°)
                 \   \ trophies/    /
                  \   '--------'   /   ◄── THROWABLES (150°)
                   '-.          .-'
                      '-.____.-'   ◄── AUTOMATION: Basket (185°), Intern (220°)
```
Stalls on the outer ring (r 74, moved out from 70 by the layout agent so they sit behind the path) behind the Shibas,
≥ 30 studs apart, a path ring (r 70) links them to the bridge;
walking clockwise from the spawn = later in the game.
