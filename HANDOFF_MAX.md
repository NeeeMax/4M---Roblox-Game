# HANDOFF → Max

Status of the economy / bonk / layout rework (see `PLAN.md` for the full plan and the recon). Updated after every
phase, so you can continue from the latest state if Marco's Claude session gets cut off.

## Status

| Phase / workstream | State | Branch / commit |
|--------------------|-------|-----------------|
| Phase 0 recon + plan | done | `feat/economy-v2` (`PLAN.md`) |
| Shared contract (EconomyConfig, types, save v2, remotes, rebirth service, layout config, number format) | done | `feat/economy-v2` |
| A economy | done: tuned pace (first run ~67 min, minute rhythm from Shiba 9, last Shiba 1e33, paybacks ≤ 15 min), simulation + `docs/economy/BALANCING.md`, 1e33-safe leaderboard (`TotalEarned_v2`, log-encoded; text leaderstats), trophy prices, offline bank from automation (`EconomyService.AddAutomationPoints`), 30-Shiba index, rebirth admin tools + REBIRTH card + HUD pill, locked upgrades (menu + server) | `feat/v2-economy` |
| C bonk | done: catch-timing quality (BONK ×1 after landing, AIR BONK ×2, PERFECT BONK ×4 in the last 0.25 s), landing ring, juice (popups, coins, shake, combo tiers), first bonk ×10, impact effects per throwable, Shiny/Mythic looks, ADR 0005 | `feat/v2-bonk` |
| D automation | done: Bonk Basket (catches missed sticks) + Bonk Intern (NPC runs to sticks, gets bonked, 6 looks), `AutomationCatch` visuals | `feat/v2-automation` |
| E layout | done: stalls on the outer ring (r 74) in zones with signs, path, rebirth shrine, locked stalls, trees in a grove; `docs/economy/LAYOUT.md`, `lune run docs/economy/layout_check.luau` | `feat/v2-layout` |
| B onboarding | done: new players spawn in front of the NEW SHIBA pad with its exact price, guide beam + pulsing highlight + ≤ 4-word hints for 6 purchases, next-Shiba silhouette with price + progress bar, money bars, locked/rebirth billboards | `feat/v2-onboarding` |
| Integration | done: merged in order economy → bonk → automation → layout → onboarding, conflicts resolved, checks green, two code reviews (1 fix), simulation re-run, pushed | `feat/economy-v2` → `main` |

## Shared contract (read this first)

- `src/shared/Config/EconomyConfig.luau` is the single source of truth for prices, incomes and multipliers. Prices are
  derived from a target pace (header comment). Change `FINAL_SHIBA_COST`, `PACE` or `ROUTE_SPECS` and everything
  re-prices. `lune run docs/economy/simulate.luau` prints the resulting curve.
- 30 Shibas = the 10 models + Shiny + Mythic editions (`EconomyConfig.Shibas`, `Gameplay.Shooters.Tiers` points to it).
- Numbers: `Util/Format` (K … Dc … up to 1e303). `Format.Money` goes short from 1e6.
- Save version 2 (`DataService`): new `Rebirths`, `Tutorial`, `Bank.AutomationPerMinute`, levels `Basket`/`Intern`.
  Version-1 saves keep their money and levels; old players skip the tutorial.
- New remote `AutomationCatch` (S→C, visuals only). `HitQuality` is now `Normal | Good | Perfect` (catch timing).
- `RewardService.GetStickValue` = stick value incl. tier, rebirth, golden, passes, boosts, events.
- `RebirthService.TryRebirth` (server) — rebirth needs Shiba tier level 20. Admin: `ForceRebirth`, `SetRebirths`.
- Automation (basket, intern) must pay with `EconomyService.AddAutomationPoints(player, amount)`, not `AddPoints`:
  that sample drives the offline Shiba Bank (`Bank.AutomationPerMinute`).
- Upgrades with `EconomyConfig.UnlockAtShibaTier[id]` above the player's ShooterTier are refused by
  `UpgradeService.TryPurchase` ("… unlocks with the <Shiba>!"); stands/billboards should show them locked.

## Next steps

Nothing was handed over — everything is built. Still open (needs a playtest, not code):

- [ ] Test everything in Studio (checklists: `docs/economy/LAYOUT.md`, GAME_DESIGN sections Onboarding / Automation /
      Hits). Admin → RESET EVERYTHING gives a brand-new player.
- [ ] Tune `Gameplay.Hits.PerfectWindow` (0.25 s) and the real intern catch rate, then re-run
      `lune run docs/economy/simulate.luau` (the pricing assumes an average catch bonus of ×2).
- [ ] Decide: later rebirths get short fast (run 3 ≈ 22 min, run 6 ≈ 11 min) → maybe a rising rebirth requirement.
- [ ] Decide: duel stakes (100 … 100,000) are tiny against the new numbers.
- [ ] Old (version-1) saves keep their Bonk Dollars (up to ~6.7e7 ≈ Shiba 7 head start) and any levels.
- [ ] The TOP BONKERS board starts empty (new store `TotalEarned_v2`).
- [ ] Models not built yet (part-built placeholders): `Prop_Basket`, `Prop_RebirthShrine`, `Prop_UpgradeStand_Basket/Intern`.
