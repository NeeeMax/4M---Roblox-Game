# 0002 — NPC shooters aim at random points on the island, not at the player

- Status: accepted
- Date: 2026-09-24

## Context

In GET BONKED the player *wants* to be hit. If shooters aimed at the player, every shot would hit a player who stands still:
no skill, pure AFK farming, and movement speed would be useless. The concept asks for the opposite — the player must move,
reposition, react and read trajectories.

## Decision

- Each shot targets a **random point, uniformly distributed** on the player's island (radius 28), never the player.
- The target must be at least `projectile radius + 8` studs away from where the player stands at fire time, so standing still earns nothing.
- Projectiles fly a **visible 45° arc** with ±10 % launch-speed jitter; the shooter turns toward the target 0.5 s before firing.
- Movement speed upgrades exist so the player can **reach** impact points in time, not to dodge.
- Running and jumping into a projectile raises the hit quality (impact speed relative to launch speed), which rewards skill further.

Numbers are in `docs/GAME_DESIGN.md`.

## Consequences / revisit when

- Easier: no AFK farming by design; MoveSpeed, ProjectileSpeed and ProjectileSize all have a clear trade-off.
- Harder: early game can feel slow if too many shots land out of reach. Tune fire interval, launch speed and island radius first.
- Revisit if playtests show players can't tell where projectiles land (then consider a landing marker), or if hit rates of
  active players stay under ~30 % at base stats.
