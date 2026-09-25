# HANDOFF → Max

Status of the economy / bonk / layout rework (see `PLAN.md` for the full plan and the recon). Updated after every
phase, so you can continue from the latest state if Marco's Claude session gets cut off.

## Status

| Phase / workstream | State | Branch / commit |
|--------------------|-------|-----------------|
| Phase 0 recon + plan | done | `feat/economy-v2` (`PLAN.md`) |
| Shared contract (EconomyConfig, types, save v2, remotes, rebirth service, layout config, number format) | done | `feat/economy-v2` |
| A economy | done: tuned pace (first run ~67 min, minute rhythm from Shiba 9, last Shiba 1e33, paybacks ≤ 15 min), simulation + `docs/economy/BALANCING.md`, 1e33-safe leaderboard (`TotalEarned_v2`, log-encoded; text leaderstats), trophy prices, offline bank from automation (`EconomyService.AddAutomationPoints`), 30-Shiba index, rebirth admin tools + REBIRTH card + HUD pill, locked upgrades (menu + server) | `feat/v2-economy` |
| C bonk | in progress (agent) | `feat/v2-bonk` |
| D automation | in progress (agent) | `feat/v2-automation` |
| E layout | in progress (agent) | `feat/v2-layout` |
| B onboarding | in progress (agent) | `feat/v2-onboarding` |
| Integration | not started | `feat/economy-v2` |

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

Filled in if work is left over.
