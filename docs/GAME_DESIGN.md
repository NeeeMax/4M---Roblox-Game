# Game Design — GET BONKED

> Not decided yet = not in this file. Claude Code must not invent design decisions; if something is missing here, ask.
> All numbers below are **starting values**. They live in `src/shared/Config/` and are tuned in playtests.

## One-sentence pitch

NPCs lob silly objects at your personal floating island — run and jump **into** them to get bonked, earn Bonk Points, and buy upgrades that make it faster, bigger and more chaotic.

## Core loop

- **Every 5 seconds:** an NPC aims at a random spot on your island and fires. You read the arc, run there and try to take the hit (ideally running and jumping into it for a better hit quality).
- **Every 1–5 minutes:** spend Bonk Points on one of 5 upgrades.
- **Every session:** push upgrade levels higher; progress is saved.

## Target players and session length

Casual Roblox players, roughly 8–14. Understandable in under 10 seconds without a tutorial. Target session: 15–30 minutes.

## World

| Thing | Value |
|-------|-------|
| Islands | one per player, on a grid 500 studs apart, assigned on join, freed on leave |
| Island | flat disc, radius 30 studs, surface at Y = 100 |
| Target area | disc radius 28 (2-stud margin to the edge) |
| Player spawn | island centre |
| Shooter ring | shooters stand on small platforms at radius 60 from the centre, at island surface height, evenly spaced (360°/n), first one at north |
| Fall-off | below Y = 50 → respawn at island centre, no penalty |

Players never affect each other: projectiles only exist for their owner's island, only the owner's character can be hit, and projectiles do not physically collide with any character (collision group) — knockback comes from the hit code only.

## NPC shooters

- Shooters **never aim at the player**. Each shot picks a random target point, uniformly distributed in the target area.
- **Anti-farm rule:** the target point must be at least `projectile radius + 8` studs away from the player's position at fire time; otherwise pick again (max 10 tries, then skip the shot). Standing still therefore earns 0 points.
- **Spread:** the random target point is the spread; additionally the launch speed varies ±10 % per shot.
- **Telegraph:** the shooter turns toward its target 0.5 s before firing.
- Fire interval: 5.0 s at level 0 (see upgrades). Each shooter has its own timer, offset randomly by 0–1 s so shots don't sync.

## Projectiles

MVP has one projectile type: **Ball**.

| Field | Ball |
|-------|------|
| Diameter | 2 studs |
| Base launch speed | 45 studs/s |
| BaseReward | 10 Bonk Points |

**Flight (visible arc):** launched at a fixed 45° angle toward the target point. Per projectile, gravity is set (with a `VectorForce`) to `g = v² / d` (v = launch speed, d = horizontal distance) so it lands exactly on the target. Every shot has the same readable arc shape (apex = d / 4); higher speed only shortens the flight time. At base speed a 60-stud shot flies 1.9 s.

**Size vs speed:** projectile diameter = `2 × sizeScale`, launch speed = `45 × speedScale × sizeScale^-0.5`. Bigger projectiles are easier to hit but fly slower and therefore pay a lower speed multiplier.

**Lifetime / cleanup:** a projectile's flight ends at its first contact with anything (ground or other); only the flight counts for hits. Destroyed 1.5 s after first contact, or 8 s after launch at the latest. Max 60 live projectiles per island; the oldest is destroyed first. All projectiles of a player are destroyed when they leave.

## Hits (server decides)

- The owner's client detects the touch (what the player sees on screen) and reports the projectile id. See `docs/decisions/0003-client-reports-hits-server-validates.md`.
- The **server alone decides** and awards points. A report counts only if: the projectile belongs to the player, hasn't paid yet, the player is alive and not immune, and the projectile's flight path (launch until first contact) passed within `projectile radius + 6` studs of the character's root on the server. Max 10 reports/s.
- **Each projectile pays out at most once.**
- **Hit immunity:** 0.5 s after a hit (checked on client and server). Projectiles touching the player during immunity are ignored (they can still hit afterwards).
- **Knockback:** 0.4 s, 40 studs/s horizontally in the projectile's flight direction + 30 studs/s up. No ragdoll in MVP.

### Reward

```
Reward = floor(BaseReward × SizeMult × SpeedMult × QualityMult), at least 1

SizeMult  = sizeScale                   (1.2 ^ sizeLevel)
SpeedMult = launch speed / 45           (includes the size slowdown, excludes the ±10 % jitter)
```

### Hit quality — one rule

`r = |projectile velocity − player velocity| / projectile launch speed`, measured at the moment of the hit (projectile velocity from its flight path at the closest point, player velocity from the server's view of the character).

The player velocity is clamped before use: horizontal ≤ current WalkSpeed, vertical ≤ 50 (jump velocity), so knockback or a spoofed client velocity can't inflate it.

| Quality | r | Multiplier | How you get it (base stats) |
|---------|---|-----------|-----------------------------|
| Normal | < 1.2 | 1× | walk under it (r ≈ 1.0) |
| Good | 1.2 – < 1.5 | 2× | run into it (r ≈ 1.28) |
| Hard | 1.5 – < 1.8 | 5× | run + jump into it (r ≈ 1.65) |
| Massive | 1.8 – < 2.2 | 10× | run + jump, well timed (max ≈ 2.1) |
| Legendary | ≥ 2.2 | 50× | needs MoveSpeed upgrades + perfect timing |

## Feedback (client)

- Popup above the character: `+X BONK` for 1.0 s; for Good and above prefixed with the quality, e.g. `HARD BONK! +50`.
- One bonk sound; pitch 1.0 + 0.1 per quality tier above Normal.

## Upgrades

Cost of the next level: `cost(n) = floor(BaseCost × Growth^n)`, n = current level. Defaults: BaseCost = 100, Growth = 2.85, configurable per upgrade.
Default series: 100 → 285 → 812 → 2,314 → 6,597 → 18,802 → …

| Id | Effect per level | Level 0 | Max level | At max | BaseCost | Growth |
|----|-----------------|---------|-----------|--------|----------|--------|
| `MoveSpeed` | WalkSpeed +3 | 16 | 10 | 46 | 100 | 2.85 |
| `ProjectileSpeed` | speedScale ×1.15 | 1.0 | 10 | 4.05 | 100 | 2.85 |
| `ProjectileSize` | sizeScale ×1.2 | 1.0 | 10 | 6.19 (12.4-stud ball, 0.40× speed) | 100 | 2.85 |
| `FireRate` | fire interval ×0.85 | 5.0 s | 12 | 0.71 s | 100 | 2.85 |
| `Shooters` | +1 shooter | 1 | 7 | 8 | 500 | 4.0 |

- MoveSpeed exists so the player can **reach impact points in time** (not to dodge). It also raises the achievable hit quality.
- ProjectileSpeed and ProjectileSize change difficulty, but both raise the reward per hit, so they are worth buying.
- **Shooters add/remove:** buying adds a shooter. In the upgrade menu the player can set the number of active shooters between 1 and the owned count for free.
- Purchases are validated on the server: known upgrade id, below max level, enough Bonk Points, max 5 requests/s.

## Economy

- Currency: **Bonk Points** (integer). Only earned by hits. Start with 0.
- Pacing target (for tuning): first upgrade after ~90 s of active play, 5 purchases within the first 10 minutes.

## UI (MVP)

- HUD: current Bonk Points, button to open the upgrade menu.
- Upgrade menu: per upgrade — name, current level, current value, next cost (or "MAX"), buy button (disabled if not affordable); active-shooter selector.

## Saving

Per player (DataStore, key = UserId): Bonk Points, level per upgrade, active shooter count. Loaded on join, saved on leave, every 60 s, and on server shutdown.

## Scope of the first playable version (MVP)

Must have (= "Prototype Scope – Required" from the concept):
- One player island
- One NPC shooter
- One projectile type
- Projectile physically travels toward island
- Player can move
- Collision with player awards Bonk Points
- Basic knockback/ragdoll effect (MVP: knockback only)
- Basic currency UI
- Basic upgrade shop
- Movement speed upgrade
- Projectile speed upgrade
- Projectile size upgrade
- Shooting frequency upgrade
- Add/remove NPC shooter upgrade
- Basic save structure if practical

Explicitly not in MVP:
- More projectile types, projectile tiers 1–5, "Unlock New Projectile" upgrade
- More than 8 shooters, multiple shots per second per shooter
- Ragdoll, complex animations, polished art, visual island progression
- Physical shop area on the island (shop is a UI menu in MVP)
- HUD stats beyond Bonk Points (Bonks/second, speed, projectile tier, shooter count)
- Visiting other players' islands
- Leaderboards, cosmetics, additional upgrade trees
- Pets, trading, PvP, rebirths, quests, large maps
- Monetisation

## Systems (high level)

| System | What it does | Owner |
|--------|--------------|-------|
| Islands | assign/free island slots, spawn, fall-off respawn | Max |
| NPC shooters | place shooters, pick target points, telegraph, fire timers | Max |
| Projectiles | spawn, arc physics, lifetime, cleanup | Max |
| Hit detection | overlap check, immunity, hit quality, reward calculation | Max |
| Bonk effects | knockback, `+X BONK` popup, sound | Max |
| Economy | Bonk Point balance, add/spend (server only) | Marco |
| Upgrades | levels, cost formula, server-validated purchases | Marco |
| Shop / upgrade menu | UI to buy upgrades, active-shooter selector | Marco |
| HUD | Bonk Points display | Marco |
| Saving | DataStore load/save | Marco |
| 3D models & visuals | models for islands, shooters, projectiles; UI art; effects | Marco |

## Monetisation

_TBD (decide late, but decide before building shops beyond the MVP upgrade menu)_

## Open questions

- Should a landing marker show where a projectile will land, or must players read the arc themselves? (MVP: no marker.)
- Should players be able to lower other upgrades (like active shooters) to control difficulty?
