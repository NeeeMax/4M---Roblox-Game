# 0004 — Clients draw projectiles along the planned path

- Status: accepted (replaces "the server steers a physics part along the path")
- Date: 2026-09-24

## Context

The server moved an unanchored physics part along each planned path and teleported it onto the path at every bounce.
Clients see server physics through network interpolation, and a teleport is not interpolated: in playtests every stick
visibly hung for a moment each time it touched the ground.

## Decision

- The server still plans the whole path (flight + bounces) and validates hits against it (`docs/decisions/0003`).
- Instead of a moving part it creates an invisible, **anchored** marker that stores the path as attributes
  (`src/shared/Util/ProjectilePath.luau`), including the launch time on the synced server clock
  (`Workspace:GetServerTimeNow()`).
- Every client (`ProjectileController`) builds its own copy of the model and moves it along the path each frame.
  `BonkController` checks hits against these drawn positions.
- The server sets the attribute `Paid` after a payout; clients fade the model.

## Consequences / revisit when

- Flights and bounces are perfectly smooth and cost the server almost nothing (no physics, no per-frame steering).
- Client and server agree on the path by construction; the client shows the projectile where the server has it now
  (not ~100 ms in the past as with replicated physics), which makes hit reports more accurate.
- A new projectile type only needs a def in `Config/Projectiles` and an asset; the drawing is generic.
- Revisit if projectiles ever need to react to the world (collide with things): then they need real physics again.
