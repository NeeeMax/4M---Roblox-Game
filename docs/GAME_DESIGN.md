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
| Shooter look | per Shiba Tier (see Upgrades): `ReplicatedStorage/Assets/Shiba`, `GalaxyShiba`, `GodShiba` (6 studs tall); a missing model falls back to the next lower tier's model with an outline in the tier colour, then `Shooter`, then a red block with barrel |
| Fall-off | below Y = 50 → respawn at island centre, no penalty |

Players never affect each other: projectiles only exist for their owner's island, only the owner's character can be hit, and projectiles never physically collide with anything — the server moves them along their planned path, knockback comes from the hit code only.

## NPC shooters

- Shooters **never aim at the player**. Each shot picks a random target point, uniformly distributed in the target area.
- **Anti-farm rule:** the projectile's whole path (flight and both bounces) must stay at least `projectile radius + 6` studs away from the player's position at fire time; otherwise pick again (max 30 tries, then skip the turn). Standing still therefore earns 0 points.
- **Spread:** the random target point is the spread; additionally the launch speed varies ±10 % per shot.
- **Telegraph:** the shooter turns toward its target 0.5 s before firing.
- Fire interval: 5.0 s per shooter at level 0 (see upgrades). **Shooters take turns:** with n shooters one of them fires every `interval / n` seconds, never two at once.
- A shooter model may contain a part named `Stick` (hidden for 0.4 s after each throw) and an Attachment `Muzzle` (where the throw starts).

## Projectiles

Projectile tiers (upgrade `ProjectileTier`): **Stick** (BaseReward 10) → **Bone** (20) → **Golden Stick** (40) → **Diamond Stick** (80). They fly the same; only look and reward differ. Models `ReplicatedStorage/Assets/Stick`, `Bone`, `GoldenStick`, `DiamondStick`; a missing model uses the next lower tier's model, tiers above Stick draw a trail in their colour, no model at all = coloured sphere. Hits use an invisible sphere of the projectile's diameter; the model is scaled so its longest side equals that diameter and spins in flight.

| Field | Bonk Stick |
|-------|------|
| Diameter | 3 studs |
| Base launch speed | 36 studs/s |
| BaseReward | 10 Bonk Points |

**Flight (visible arc):** launched at a fixed 45° angle toward the target point. Per projectile, gravity is set (with a `VectorForce`) to `g = v² / d` (v = launch speed, d = horizontal distance) so it lands exactly on the target. Every shot has the same readable arc shape (apex = d / 4); higher speed only shortens the flight time. At base speed a 60-stud shot flies 2.4 s.

**Size vs speed:** projectile diameter = `3 × sizeScale`, launch speed = `36 × sizeScale^-0.5`. Bigger projectiles are easier to hit but fly slower and therefore pay a lower speed multiplier.

**Bounces:** after landing it bounces **twice**: each bounce keeps 50 % of the vertical and 70 % of the horizontal speed (at base speed: first bounce ≈ 3.7 studs high, second ≈ 1 stud). The whole path is computed when the shot is planned; every client draws the projectile along it (`docs/decisions/0004`). A bounce that leaves the island makes it fall off the edge.

**Lifetime / cleanup:** it disappears the moment it touches the ground after the second bounce (or drops below the island): each client hides it when the path ends on the synced server clock. The server destroys its marker 0.5 s after the path ends, 15 s after launch at the latest, and keeps the path 2 s longer to validate late hit reports. Max 60 live projectiles per island; the oldest is destroyed first. All projectiles of a player are destroyed when they leave.

## Hits (server decides)

- The owner's client detects the touch (what the player sees on screen) and reports the projectile id. See `docs/decisions/0003-client-reports-hits-server-validates.md`.
- The **server alone decides** and awards points. A report counts only if: the projectile belongs to the player, hasn't paid yet, the player is alive and not immune, and the projectile's path so far (flight and bounces) passed within `projectile radius + 6` studs of the character's root on the server. Max 10 reports/s.
- **Each projectile pays out at most once.**
- **Hit immunity:** 0.5 s after a hit (checked on client and server). Projectiles touching the player during immunity are ignored (they can still hit afterwards).
- **Knockback:** 0.25 s, 16 studs/s horizontally in the projectile's flight direction + 12 studs/s up (≈ 4 studs, a small hop). No ragdoll in MVP.

### Reward

```
Reward = floor(BaseReward × SizeMult × SpeedMult × QualityMult × HeadMult × ComboMult × ShibaTierMult), at least 1

SizeMult  = sizeScale                   (1.2 ^ sizeLevel)
SpeedMult = launch speed / 36           (= the size slowdown sizeScale^-0.5; excludes the ±10 % jitter)
HeadMult  = 2 if the projectile touched the head, else 1
ComboMult = 1 + 0.1 × (combo − 1), at most 3
ShibaTierMult = Shiba 1, Galaxy Shiba 2, God Shiba 4
```

### Hit quality — one rule

`r = |projectile velocity − player velocity| / projectile launch speed`, measured at the moment of the hit (projectile velocity from its flight path at the closest point, player velocity from the server's view of the character).

The player velocity is clamped before use: horizontal ≤ current WalkSpeed, vertical ≤ 50 (jump velocity), so knockback or a spoofed client velocity can't inflate it.

| Quality | r | Multiplier | How you get it (base stats) |
|---------|---|-----------|-----------------------------|
| Normal | < 1.2 | 1× | walk under it (r ≈ 1.1) |
| Good | 1.2 – < 1.5 | 2× | run into it (r ≈ 1.35) |
| Hard | 1.5 – < 1.8 | 5× | run + jump into it (r ≈ 1.6) |
| Massive | 1.8 – < 2.2 | 10× | run + jump, well timed (r ≈ 1.9) |
| Legendary | ≥ 2.2 | 50× | run + jump right at take-off, perfect timing (max ≈ 2.4 at base stats) |

### Head hits and combo

- **Head hit (×2):** the client reports whether the projectile touched the head; the server accepts it if the path also
  passed within projectile radius + 4 studs of the server-side head.
- **Combo:** every hit within the combo window of the previous hit adds 0.1 to the multiplier (max ×3 at 21 hits).
  Window = 2 s + 1.5 × time between two shots (interval / active shooters), so it stays fair with more or faster shooters.
  The HUD shows `COMBO xN ×M` with a bar that runs out when the window ends.

## Feedback (client)

- Popup above the character: `+X BONK` for 1.0 s; for Good and above prefixed with the quality, e.g. `HARD BONK! +50`.
- One bonk sound; pitch 1.0 + 0.1 per quality tier above Normal.
- Head hits say `HEADBONK!` instead of `BONK`.
- Stars burst from the head in the quality colour (6 + 6 per tier above Normal); from Hard on the camera shakes briefly.

## Upgrades

Cost of the next level: `cost(n) = floor(BaseCost × Growth^n)`, n = current level. Defaults: BaseCost = 100, Growth = 2.85, configurable per upgrade.
Default series: 100 → 285 → 812 → 2,314 → 6,597 → 18,802 → …

| Id | Effect per level | Level 0 | Max level | At max | BaseCost | Growth |
|----|-----------------|---------|-----------|--------|----------|--------|
| `MoveSpeed` | WalkSpeed +3 | 16 | 10 | 46 | 100 | 2.85 |
| `ProjectileSize` | sizeScale ×1.2 | 1.0 | 10 | 6.19 (12.4-stud ball, 0.40× speed) | 100 | 2.85 |
| `FireRate` | fire interval ×0.85 | 5.0 s | 12 | 0.71 s | 100 | 2.85 |
| `Shooters` | +1 shooter | 1 | 7 | 8 | 500 | 4.0 |
| `ProjectileTier` | next projectile (see Projectiles) | Stick | 3 | Diamond Stick | 1,500 | 10 |
| `ShooterTier` ("Shiba Tier") | all Shibas evolve: new model, reward ×2 then ×4 | Shiba | 2 | God Shiba | 5,000 | 12 |

- MoveSpeed exists so the player can **reach impact points in time** (not to dodge). It also raises the achievable hit quality.
- ProjectileSize makes hits easier and pays more per hit (net ×1.2^0.5 ≈ 1.1 per level), but balls fly slower. There is no projectile speed upgrade (removed after the first playtest).
- **Shooters add/remove:** buying adds a shooter. In the upgrade menu the player can set the number of active shooters between 1 and the owned count for free.
- Purchases are validated on the server: known upgrade id, below max level, enough Bonk Points, max 5 requests/s.

## Admin (testing)

- Admins see an **ADMIN** row in the upgrade menu: **+1,000** and **+100,000** Bonk Points.
- Admins: everyone in Studio playtests, the experience owner, and the UserIds in `src/shared/Config/Admin.luau`.
- The server checks admin rights on every request (`AdminAddPoints`); the client check only hides the row.

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
- Projectile size upgrade
- Shooting frequency upgrade
- Add/remove NPC shooter upgrade
- Basic save structure if practical

Explicitly not in MVP:
- Projectile speed upgrade (was in the concept's list; removed after the first playtest, 2026-09-24)
- Projectile types that fly differently (tiers only change look and reward), "Unlock New Projectile" upgrade
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
