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
| World (hub + islands), NPC shooters, projectiles, hit detection, bonk effects, hub features (daily spin, coin flip + duels, quests, leaderboard, boosts), admin tools | Max | calls EconomyService to award Bonk Points, reads upgrade values from UpgradeService |
| Economy, upgrades, upgrade menu, HUD, saving, shared UI kit (`client/UI`) | Marco | DataService owns the saved state; Bonk Points change only through EconomyService, levels only through UpgradeService; other services (quests, spin, boosts) change their own fields via DataService.GetState + Replicate |
| Tycoon "Shiba Workers" (`TycoonService`, `World/TycoonPlot`, `TycoonController`, `Config/Tycoon`, `Config/TycoonWorld`, `Util/TycoonMath`, `Config/Features`) | Marco | economy, HUD, saving and UI are Marco's; Max agreed to the rest (hand-off decisions). Behind `Config/Features.Tycoon` (default false), see `docs/decisions/0006` and `docs/TYCOON_HANDOFF.md` |
| 3D models and other visual assets (`ReplicatedStorage/Assets` in the place) | Marco | built in Studio, not in git (see *World vs code*); code finds them by stable names |

## World vs code

- **In git:** all Luau code.
- **In the Roblox place (not git):** maps, models, parts, UI layouts, lighting, sounds.
- **MVP exception:** islands, shooters, projectiles and the HUD/upgrade menu are created by code, so the prototype runs in an empty Baseplate place. Moving them to Studio-built assets later is fine.
- Upgrade stands: `StationService` builds `Island_<UserId>/Stations` (stand props, `Station_<UpgradeId>` prompt parts,
  `ShibaPad`); `StationController` finds them by these names (`Config/Stations`) and draws the billboards client-side.
- Automation: `AutomationService` builds `Island_<UserId>/Prop_Basket` (a `PropService` prop, so a model named
  `Prop_Basket` in `ReplicatedStorage/Assets` replaces the placeholder) and `Island_<UserId>/BonkIntern` (part-built
  rig: `Root` with the movers, `Torso`, `Head`, arms and legs joined by the Motor6Ds in `Config/Automation → Intern.Joints`);
  `AutomationController` finds them by these names (`Config/Automation`).
- Street interns: `World/StreetPlot` builds `Lane_<n>/Intern` as an R15 character (`Players:CreateHumanoidModelFromDescription`, built asynchronously, part-built fallback; attribute `StreetIntern`; only the HumanoidRootPart is anchored). `InternChatController` (client only, `Features.Street`) animates it (idle bob, look-around, flinch via Motor6D Transform) and shows speech bubbles with the lines of `Config/InternLines` (tuning in `Config/Automation -> Chat`); `TycoonController` ducks it and sets the local attribute `BonkedAt`.
- Street (`Config/Street`, `Config/Features.Street`, `Services/StreetService`): with the flag (and the tycoon) on, the street with 10 plots replaces the islands: `StreetService` builds `Workspace/Street` (road, `Plot1` … `Plot10`, 5 per side, slot 1 = left), claims a free plot per joining player, spawns them on the road in front of it and frees the plot on leave. `IslandService` then returns early and its `GetIsland` / `SpawnOnIsland` / `TeleportToHub` forward to it, so `TycoonService` and the others still get the same `Island` record (`Center` = plot centre, `HubAngle` = toward the road, `Model` = `Islands/Island_<UserId>`). Phase 2: with the flags on, `TycoonService` builds `World/StreetPlot` instead of the island's ring (`TycoonPlot`): two bays per row left and right of a path (`Lane_<n>` with the `Shiba`, an invisible `SwingPart` with a ClickDetector and the prompts `Tycoon_Swing` Q, `Tycoon_LevelUp` E, `Tycoon_LevelUp10` F, plus an invisible `Belt_<n>` the client's swing animation takes its direction from) and at most 3 floor pads `Pad_<id>` from `Util/TycoonSteps` (expansion `Bay<n>`, automation `Auto<n>`). Stepping on a pad calls `actions.BuyStep`; `state.Tycoon.Steps` holds the bought pads and `EquipSlots` the number of bays. No eggs, equip or collection panel in this mode; the client skips belt items and the SHIBAS and MANAGE tiles. `TycoonGuideController` (client only, does nothing with `Features.Street` off) draws the walkthrough guide: a bobbing arrow over the current floor pad and a one-line objective under the money pill. Decor: `Config/TycoonDecor` holds per-Shiba themes (parts bought as `Decor<bay>_<part>` floor pads, drawn by `StreetPlot` from primitives or `Decor_<Key>_<Part>` assets); `TycoonSteps.VisibleDecor` picks the decor pads outside the 3-pad limit and `TycoonService` re-checks owner proximity once a second. Ascension (street): `TycoonSteps.AscendStep` is a repeatable pad that is not in `List`/`ById` (never saved in `Steps`); `Visible` appends it once `CanAscend` (best Shiba >= `AscendRequirement`), `StreetPlot` draws it beside the entrance with a hold prompt, `actions.BuyStep("Ascend")` re-checks and runs `TycoonService.ascend` (shared with the island; the street branch wipes steps, Shibas and money, saves at once and rebuilds the plot). Offline (street): `OfflineService.onLoaded` pays the time away on join through `EconomyService.PayOffline` and a `Notify` toast; no new remote. `ShibaPanelController` (client only, does nothing with `Features.Street` off) draws the Shiba menu: a BillboardGui on `Lane_<n>/Anchor` with the cooldown bar and the UPGRADE button (key E, `UpgradeShiba`), while `TycoonController` animates the stick swing and the Bonk Intern's ducking.
- Onboarding (`Config/Tutorial`): `IslandService` spawns brand-new players in front of the NEW SHIBA pad and stamps
  `Island_<UserId>` with the attribute `IslandCenter`; `TutorialService` counts guided purchases in
  `state.Tutorial.Step` (the only field it changes); `TutorialController` draws the guidance client-side, using
  `StationController.CheapestAffordable / GetAnchor / GetPad / GetStand`.
- Social + Bonk Party: `SocialService` owns the Friend Boost (friend cache) and invite rewards (`state.Social`, the
  `ReferralsPending` DataStore); `RewardService.GetStickValue` multiplies by `SocialService.GetFriendMultiplier`.
  `EventService` owns the Bonk Party schedule (`IsPartyActive`, `GetPartyWindow`, `VariantLuckMultiplier`);
  `PartyService` owns the party quest (`state.Party`) and builds `Workspace/BonkPartySign`.
- Retention extras (no remotes, no saved fields): `MilestoneService` reads the saved state every few seconds and awards
  Roblox badges (`Config/Milestones → Badges`, `BadgeId` 0 = inert) and logs the onboarding funnel with `AnalyticsService`
  (`Config/Milestones → Funnel`, only for saves younger than 72 h). `UpdateBoardService` builds the update log board
  (`Workspace/UpdateBoard`, west end of the street, or next to the hub plaza with `Features.Street` off) from `Config/Updates`,
  with a countdown to the weekly update (`Updates.NextUpdateAt`, UTC).
- Tycoon ("Shiba Workers", behind `Config/Features.Tycoon`, `docs/GAME_DESIGN.md → Tycoon`): `TycoonService` (server, in
  `Services/`) owns `state.Tycoon` logic (income tick, hatching, equip, levels, merge, pads, Ascension); with the flag off it
  returns early in `Init`/`Start`. `World/TycoonPlot` (server, in `src/server/World/`) builds `Island_<UserId>/Tycoon` with
  `Lane_<n>` (n = equip slot 1 to 10; holds the visual-only `Shiba` model, an invisible `SwingPart` with a ClickDetector and the
  prompts `Tycoon_Swing` (Q) and `Tycoon_Automate` (R); the swing/automation/Bonk-hit logic is in `TycoonService`), `Belt_<n>`, `Mill`, `Vault` and `Egg_<zone>` (zone 0 to 5); sizes and positions are in
  `Config/TycoonWorld`. `TycoonController` (client, in `Controllers/`) finds them by these names and draws belt items, popups
  and the hatch animation (visual only). Shared: `Config/Tycoon` (all tuning, pure data), `Config/TycoonWorld` (names and
  layout), `Config/Features` (flags), `Util/TycoonMath` (pure formulas, also loaded by `docs/economy/tycoon_sim.luau`).
  `DataService` saves `state.Tycoon` (save version 4). Status: `Config/Tycoon`, `Config/Features`, `Util/TycoonMath` and the save
  exist; `TycoonService`, `World/TycoonPlot`, `TycoonController` and `Config/TycoonWorld` come in phases 2 and 3.
- Code references world objects by stable names/paths. When you rename something in the world that code uses, update the code in the same session and mention it in the PR.
