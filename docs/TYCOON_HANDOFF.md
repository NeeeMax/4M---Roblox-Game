# Tycoon rework — hand-off for the next Claude session

Read this file first, then CLAUDE.md, docs/ARCHITECTURE.md, docs/NETWORK.md, docs/decisions/0006-tycoon-core-loop.md.

## Status (tycoon is implemented behind `Config/Features.Tycoon = false`, all of it unplayed in Studio)

Everything below type-checks (`luau-lsp analyze`) and passes `stylua --check`. `selene` could not run in the cloud session
(it cannot download the Roblox API dump): run it locally. Nothing was tested in Roblox Studio.

- **Contract (phase 0):** 13 new remotes in `shared/Net`, `OwnedShiba` / `HatchResult` / `TycoonState` in `shared/Types`
  (`PlayerState.Tycoon` optional), docs/NETWORK.md rows, ADR 0006. Merge this as its OWN PR first (CLAUDE.md), the rest after.
- **Shared:** `Config/Features.luau`, `Config/Tycoon.luau` (formulas' numbers, perks, zones, eggs, prices),
  `Config/TycoonWorld.luau` (layout), `Util/TycoonMath.luau` (pure formulas, also used by the sim and the client).
- **Server:** `DataService` save v4 (`Tycoon` default + `loadTycoon` validation), `Services/TycoonService.luau` (income tick,
  eggs/hatch, equip with zone gating, levels, arches, pads, zones, merge, ascension, crates, boops, vault stub; all remote
  handlers), `World/TycoonPlot.luau` (Mill, vault, lanes, belts, arches, egg stands, shrine, ProximityPrompts),
  `RewardService.GetIncomeMultiplier`, and `if Features.Tycoon then return end` at the top of `Start()` of NPCShooterService,
  ProjectileService, BonkService, AutoCatchService, RainService, AutomationService.
- **Client:** `Controllers/TycoonController.luau` + `UI/TycoonPanels.luau` (payout popups, belt items, hatch reveal,
  collection/equip/merge panel, crates), HUD rework (`Widgets.MoneyIcon`, money pill, tile grid, no "B$" text anywhere:
  `Format.Money` returns plain numbers), SHIBAS tile + income line wired to the tycoon.
- **Economy:** `docs/economy/tycoon_sim.luau`, calibrated: first run maxed at ~64 h simulated (lower bound; real players
  ~85-100 h), Ascension runs ~8 h each. See docs/economy/BALANCING.md.
- **Docs:** GAME_DESIGN.md (tycoon section), ARCHITECTURE.md, BALANCING.md, NETWORK.md notes.
- `Build.Label` #30 (the HUD change is visible even with the flag off).

### Known gaps / TODO (do these next)
1. Test in Studio with the flag ON (`Features.Tycoon = true` locally, never commit it): does the plot build, do prompts work,
   does income tick, does the hatch reveal show, do old systems (StationController, TutorialController, AdminController,
   HUD tiles) break when their services are off? Expect errors there: the old client controllers still run with the flag on.
2. The old tutorial, stations (StationService builds the old stalls; not guarded yet), QuestService/PartyService/IndexService/
   OfflineService still assume the old loop. IndexService: no discovery for the new Shibas yet (no simple API). Offline vault
   is a stub (`VaultStored` stays 0).
3. Prompts for other players' islands: the world builder forwards only the owner's trigger, but the prompts are visible to
   everyone; hide them client-side like StationController does.
4. `Tycoon_*` prompt behaviour, belt/dash visuals and lane billboards are placeholders (parts only, no Shiba particles).
5. Passes/products from the old game (+2 Shiba Slots, Magnet, FireRate, ...) still exist in Shop.luau; remove or repurpose
   them (no sold passes exist, so this is safe).
6. Phase 6 (flip the flag) and phase 7 (delete the old loop) are not done. CI does not run lune: run
   `lune run docs/economy/tycoon_sim` after price changes.
7. Missing tools locally? `rokit install`, then `stylua src`, `selene src` and the luau-lsp step from CONTRIBUTING.

## Decisions (Marco; Max agreed)

- All 30 Shiba models are used; target 70-100 hours to max everything.
- Shibas are a collection obtained from eggs; a limited number are equipped on the ring (3 slots at start, up to 10).
  Each equipped Shiba is its own worker with its OWN level, item, conveyor lane and perk. Duplicates can be merged.
- Optional active play: Golden Crates on belts (never required), boop mats.
- No live players, no sold passes: no migration, saves may be reset, old passes/products can go. Keep the
  `Features.Tycoon` flag anyway (CI merges every green push into main, Max plays on it).
- Keep Friend Boost (+10%/friend, max 4) and the invite reward; apply them to the new income.
- HUD: see below. Ownership questions are settled (Marco owns economy/HUD/saving/UI, Max agreed to the rest).

## Target design "Shiba Workers" (starting numbers: calibrate with a simulation first)

- Server computes income as per-second rates per lane; items on belts are client-side cosmetics only.
- Ring slots at radius 56 (existing ShibaPlatforms). Level plates (r 49) per slot with x1/x10/Max toggle. Belts r 50 -> 12
  into the Bonk Mill (r 0-10). Vault in the centre (auto-collect nearby, fills offline: 40% of online rate, 2 h cap -> 8 h).
- Level cost = 0.15 * price * 1.11^(L-1); value per level x(1+0.08(L-1)); milestones Lv 10 (rate x2), 25 (value x2),
  50 (rate x2 + aura); level cap +10 per Ascension. Arches per lane (2, x1.5 each), Mill rings (Sorter/Polisher/Refinery x1.25).
- Perks (extend to all 30, keep visible and simple): Shiba +5% all lanes per milestone; Shades 4 s x3 every 20 s; Buff +25% to
  ring neighbours; Chef processor multipliers squared; Police every 10th item x5; Ninja fast bursts; Gold vault bars ignore
  the offline cap; Galaxy 8% chance x10; Giant stomp +25% other lanes 3 s; Cheems God random bonus drop on other lanes.
- Items/rates for the first 10 (old sketch): Bone 1.0/s x1; Cool Coin 2.0 x3; Dumbbell 0.5 x90; Dish 0.7 x500; Fine Ticket
  3.0 x1K; Shuriken 8.0 x3.25K; Gold Bar 0.5 x460K; Star Shard 2.0 x1M; Boulder 0.25 x72M; Divine Cheems 0.1 x1.7B.
  That sketch reaches Shiba 10 after ~100 minutes: slow the whole game down ~50x (zones, more levels, Ascensions).
- Eggs: several egg tiers/zones, drop tables over Shiba tiers and rarities, skippable hatch animation, odds shown in the UI.
  Variants (Shiny 1/40 x1.5, Rainbow 1/400 x3, Huge 1/4000 x6) roll on hatch, pity kept. Index = collection goal
  (entry ids are saved: never rename them).
- Ascension: resets cash, levels, arches; keeps collection, Index, trophies, variants, quests, streaks. Multiplier 1+0.75n,
  +10 level cap, more equip slots. Define exactly what it resets in GAME_DESIGN.md.
- Cut: sticks, projectiles, landing rings, catch quality, head hits, combos, FIRST BONK, density cap, projectile tiers,
  Basket/Intern, "Shiba Tier evolves all", "More Shibas".

## Facts about the current code

- "Levels together": `state.UpgradeLevels.ShooterTier`, `RewardService.GetShooterTier`, `UpgradeService.TryPurchase`,
  `NPCShooterService.syncRing`.
- Shiba visuals (clone model, scale, platform, effects, variant look) sit in `NPCShooterService.buildShooter/buildPlatform/
  addEffects/addVariantLook`: extract into a module under `src/server/World/` and reuse (mixed tiers per slot already work).
  Shiba list: `EconomyConfig` SHIBA_LIST (~L84-131), alias `Gameplay.Shooters.Tiers`. Docs say 10 + editions; code has 30, no editions.
- Variants are keyed by ring slot (`state.Variants.Slots`): re-key to owned-Shiba ids.
- Throw hooks also live in EventService, PartyService, QuestService, IndexService, AdminService, UpgradeService,
  RewardService.GetStickValue (its rebirth x pass x boost x event x friend chain is reusable).
- DataService.stateFromSaved drops unknown fields; DataStore `PlayerData_v1` (do not rename), SAVE_VERSION 3.
- StateChanged replicates the whole state on every money change: batch tycoon payouts (4-10 Hz).
- New services/controllers in Services/ and Controllers/ are auto-loaded by Main; with the flag off they must return early
  in Init/Start. Remotes cannot be flag-gated (Net creates all of them).

## HUD rework (Marco's area)

Reference: a popular Roblox gym/pet game HUD (money pill top, icon-tile menu grid left). Match style, not content.
- Money pill at the top: wide rounded, dark translucent fill, thick outline, big money icon left, bold white number with dark
  stroke, short suffix (1.2K, 3.42P). Numbers only: NO "B$" or "$" text anywhere (HUD, billboards, popups, shop, admin);
  remove the text symbol from `Widgets.MoneySymbol/MoneyText` and `Format.Money`. The currency shows only as the icon.
- Icon: stack of Roblox-style cash bills (green, fanned, thick dark outline) with a BONK mark (yellow starburst badge or a
  Shiba paw), built from Frames/UICorner/UIStroke/UIGradient as one reusable widget (`Widgets.MoneyIcon(size)`), pop animation
  when money rises, used everywhere.
- Under the pill: income per second, small green ("+3.2K/s").
- Left: 2-column grid of big colourful icon buttons with bold white labels (thick stroke), no panel behind: Shibas, Eggs,
  Upgrades/Crew, Shop, Spin, Quests, Rewards, Friends (invite + boost), Ascension, Settings. Red dot for news. Hover/press scale
  tween 1.08/0.94 + click sound. "Limited!" tile style (red tag) for events/offers.
- Also: x1/x10/Max toggle, milestone hint text, existing yellow "cheapest affordable" arrow. Style tokens in
  `client/UI/Theme.luau`; mobile safe (UIScale, clear of top bar and thumbstick); placeholder icons until assets exist.
- Keep working: Settings > Hints, tutorial highlight, notifications, offline "Welcome back" panel.

## Hard rules (CLAUDE.md)

CI merges every green push into main: every push must be playable with the tycoon OFF. Contract changes (Net, Types,
CONVENTIONS) in their own PR first. One Script per side, `--strict`, server authoritative, validate every remote (type, range,
rate; use RateLimiter), no attributes on scripts, no side effects on require in shared/, `task.*` only. Bump `Build.Label`
for visible changes, run stylua/selene/luau-lsp + lune scripts, commit "area: imperative". Never push to main / force-push.
Update ARCHITECTURE/NETWORK/GAME_DESIGN in the same PR. Do not guess design: write it into GAME_DESIGN.md first.

## Phases (each: CI green, unchanged with the flag off, playable with the flag on, Label bump)

0. Contract PR — DONE (this branch).
1. `Config/Features.luau` (Tycoon = false), save v4 with `Tycoon` required + defaults, remove old passes/products,
   Studio-only DataStore suffix while developing. Also GAME_DESIGN.md tycoon section, `docs/economy/tycoon_sim.luau` calibrated
   to 70-100 h.
2. Plot skeleton: `TycoonService`, `World/TycoonPlot` (Mill, Vault, belts, level plates, egg stand placeholders); old
   ring/shooters/stalls off when the flag is on.
3. Income loop: server tick, batched payouts, client cosmetic items/popups, HUD basics (money pill + new icon + income/s).
4. Eggs, collection, equip, hatch animation, variants on hatch, Index re-scope; per-Shiba levels, arches, Mill rings,
   milestones; tutorial retarget.
5. Full HUD rework and port dependent systems: quests, party, offline bank, ascension, shop, events, friends/invites, admin.
6. Cutover: flip the flag in a one-line PR after playthroughs (fresh save, 5 players on 5 islands).
7. Cleanup: delete old services/controllers/remotes/config (contract PR for the remotes), docs.

## First message to send to the new session

"Read docs/TYCOON_HANDOFF.md. Phase 0 is written. Check it (rokit install; stylua, selene, luau-lsp), push it as its own PR,
then show me the plan for phase 1 and ask the open points before coding: number of zones/egg tiers and drop tables, what
Ascension resets, duplicate merge rules, equip slot growth, whether Friends gets a co-op egg bonus."
