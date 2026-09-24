# 0003 — The client reports hits, the server validates them

- Status: accepted (replaces "hits are detected only on the server" from the first design)
- Date: 2026-09-24

## Context

The first version detected hits only on the server: every frame, each projectile checked for overlap with the character.
In the first Studio playtest, hits that were clearly visible on screen did not count.

Cause: network delay. The client shows server-owned projectiles slightly in the past, and the server sees the
character slightly in the past. A player running into a 45-studs/s ball sees the hit; on the server the ball is
several studs further along. GET BONKED is about catching projectiles precisely, so this breaks the core loop.

## Decision

- The owning client detects the overlap between its character and the projectile it sees and sends `ReportHit(projectileId)`.
- The server validates every report and alone awards Bonk Points: owner matches, projectile not paid yet, player alive and not
  in hit immunity, rate ≤ 10/s, and the projectile's flight path (known exactly: launch position, velocity, per-projectile
  gravity) passed within `projectile radius + 6` studs of the character's root position on the server.
- Hit quality uses the projectile velocity on its flight path at the closest point and the (clamped) server-side character velocity.

## Consequences / revisit when

- Hits feel right: what you see is what counts.
- A cheater can claim near misses within the tolerance, but cannot create points from nothing, pay a projectile twice,
  or hit projectiles far away. The anti-farm rule (targets ≥ radius + 8 from the player) still keeps honest AFK players at 0.
- Revisit if exploiters abuse the tolerance (lower it, or keep a short history of server-side character positions).

## Amendment 2026-09-25 — pickup padding and collectable window

- Projectiles are collected with a **pickup sphere of radius + `Hits.PickupPadding` (2 studs)** on the client, so they are
  easier to catch without bigger models. The server adds the same padding: a report counts if the path passed within
  `radius + PickupPadding + HitTolerance` (= radius + 8) of the root, head claims within `radius + PickupPadding + HeadTolerance`.
- A report is only validated until `ReportGracePeriod` (2 s) after the projectile stopped being collectable
  (`ProjectilePath.GetCollectEndTime`: the end of its motion, or of its landing fade if `CollectableWhileFading`).
- Consequence: a cheater's near-miss margin grows by 2 studs; the anti-farm distance (radius + 6 from the standing player)
  still keeps honest AFK players at 0. Revisit together with the tolerance if exploiters abuse it.
