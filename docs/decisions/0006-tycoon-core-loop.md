# 0006 — The core loop becomes a tycoon ("Shiba Workers")

- Status: proposed (contract phase 0 merged first; the gameplay follows behind `Config/Features.Tycoon`)
- Date: 2026-09-29
- Supersedes (once the tycoon is the default): 0002, 0003, 0004, 0005

## Context

The throw-and-catch loop (Shibas throw sticks, the player catches them) has no tycoon feel and no long-term hook, and all
Shibas level together through one global `ShooterTier`, so the different Shiba types never matter. Goal: 70-100 hours of
play, every Shiba type useful, a collection to chase.

## Decision

- Shibas are a **collection** of 30 types (`EconomyConfig.Shibas`), obtained by **hatching eggs**. Duplicates can be merged.
- A limited number of Shibas are **equipped** on the ring (start 3 slots, up to 10). Each equipped Shiba is its own
  worker: **own level**, own output item, own conveyor lane into a central Bonk Mill, own perk.
- Income is computed on the **server as per-second rates**. Items on belts, popups and hatch animations are client-side
  and visual only. Clients never report anything that awards money (`ReportHit` and friends go away).
- Progression: purchase pads (egg stands per zone, Mill rings, vault upgrades, equip slots), lane arches, level milestones
  (10/25/50), Ascension (rebirth). Optional active play: Golden Crates, boop mats.
- Friend Boost and invite rewards stay and apply to the new income.
- Rollout: `Config/Features.Tycoon = false` by default. Every push must be playable with the tycoon off. Old code is deleted
  only after the cutover (phase 7 in `docs/TYCOON_HANDOFF.md`).
- No live players and no sold passes, so no save migration: the save version is bumped and saves may be reset.

## Addendum 2026-09-30: swing, click start, automation, Bonk hit

Marco asked for an active layer: every equipped Shiba swings a stick like the "Bonk" meme; at the start a Shiba only swings
when clicked, and each Shiba can be bought free of clicking ("automation"). Standing in the hit zone gets the owner flung and
paid a bonus. Belts, arches and Mill rings stay; Ascension resets the automation. Contract: `ShibaSwung` and `PlayerBonked`
(both S→C, visual only) and `OwnedShiba.Automated` (optional). Click and buy are world interactions, so no new C→S remote.
Details and open numbers: `docs/GAME_DESIGN.md → Swing, click and Bonk hit`.

## Consequences

- New remotes and types are a contract change and were merged on their own (this ADR's PR): see `docs/NETWORK.md`.
- `ReportHit`, `BonkHit`, `AutomationCatch`, `BonkRainStarted`, `UseBonkRain`, `SetActiveShooters` become dead and are
  removed in the cleanup contract PR.
- Design numbers and pacing (70-100 h) must be calibrated with `docs/economy/` simulations before content is built.
