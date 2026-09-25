# 0005 — Catch quality comes from catch timing, shown by a landing ring

- Status: accepted (replaces "Hit quality uses the relative impact speed" from 0003)
- Date: 2026-09-25

## Context

Hit quality came from the relative impact speed `|projectile velocity − player velocity| / launch speed` (Normal ×1 …
Legendary ×50). Players could not see that rule, so the multipliers felt random; long lobs landed anywhere and arriving
late felt like failure, not skill; and every hit got nearly the same feedback (PLAN.md, "Why the bonk loop feels
boring"). Variant V1 "Catch timing" was chosen: readable in one second, works on mobile, no new input.

## Decision

- **Three qualities** (`Types.HitQuality`, multipliers in `EconomyConfig.Bonk.QualityMultipliers`, shown via
  `Economy.HitQualities`): Normal `BONK` ×1 = caught after the stick first touched the ground; Good `AIR BONK` ×2 = caught
  in the air; Perfect `PERFECT BONK` ×4 = caught in the air at most `Gameplay.Hits.PerfectWindow` (0.25 s) before it
  lands. Head ×2 and combo up to ×3 stay.
- **First landing** = end of the flight segment of the planned path (`ProjectilePath.GetFirstLandingTime/Position`).
- **The server decides** (`BonkService`), with all 0003 checks unchanged (owner, not paid, alive, immunity, rate,
  path within radius + padding + 6 studs of the root, head check). The catch moment is the **first contact** of the path
  with the character's body line (3 studs below the root part up to the head, reach = radius + pickup padding + 1),
  searched only in the last `ping + 0.12 s` (max 0.6 s) before the report arrived; fallback: the closest approach to the
  root in that window (`ProjectileService.FirstContactTime`, `ClosestApproach` now also returns the time).
  - Why first contact and not the plain closest approach: the client reports on the first overlap, and a stick coming
    down at 45° is closest to the root only after it passed the body, often after it bounced (a player standing on the
    landing spot would get Normal).
  - Why the lookback window: without it, a player who reaches the landing spot *after* the landing would get Perfect,
    because the descent passed through that spot earlier.
- **PerfectWindow 0.25 s instead of the planned ~0.45 s.** A stick lands at ≈ 25 studs/s vertically, so a standing
  player touches it only in the last ≈ 0.15 s (on the spot) to ≈ 0.3 s (a few studs in front); with 0.45 s nearly every
  air catch would be Perfect and AIR BONK would almost never show. 0.25 s = "be inside the ring when it closes".
- **Landing ring** (client, `ProjectileController`, `Gameplay.LandingRing`): own projectiles only; a pooled flat ring
  (two `CylinderHandleAdornment`s) at the first landing point in the tier colour, shrinking from 10 studs to the pickup
  size at the landing, gold and thicker during the Perfect window, released at the landing or when paid.
- **First bonk:** the first paid hit of a player with `Tutorial.FirstBonkDone == false` pays × `FirstBonkMultiplier`
  (10), sets the flag (saved, replicated) and the client shows a splash (`BonkHit` gets a trailing `firstBonk: boolean`).
- Auto-Catch pass catches pay Normal. The "Hard (or better)" quest counts Perfect catches (event name `HardHit` kept).
- Removed: the velocity-ratio rule and `Gameplay.Hits.MaxVerticalPlayerSpeed`.

## Consequences / revisit when

- The rule is visible (the ring) and learnable; Perfect rewards reading the arc and being on the spot in time.
- The anti-farm rule still keeps standing players at 0 (the path never comes near where you stood at fire time).
- A cheater can still claim near misses within the tolerance and can time a fake report to get Perfect; they cannot
  create hits from nothing or pay a projectile twice (same limits as 0003).
- Qualities depend on the ping estimate (`Player:GetNetworkPing`) and on the server's view of the root; very laggy
  players may see a Perfect downgraded to AIR BONK (or an AIR BONK searched in the wrong window). Revisit
  `PerfectWindow`, `ReportLookbackSlack` or a short server-side history of character positions if playtests show
  wrong qualities.
- Revisit the window if the economy simulation (`EconomyConfig.Baseline.ActiveBonus`) assumes a different share of
  Perfect catches than playtests show.
