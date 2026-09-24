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
| Layout | a big **hub island** (radius 70) in the middle, **5 player islands** around it at 230 studs, each connected to the hub by a plank bridge with rails (tycoon style). Config: `Config/World` |
| Hub | stations between the bridges: Daily Spin, Coin Flip, Top Bonkers leaderboard, Daily Quests, How to play; "GET BONKED" title pillar in the middle. Menus open via ProximityPrompt |
| Islands | one per player, assigned on join (first free plot), freed on leave; owner name floats above it; more than 5 players = the extra ones stay on the hub. Set Max Players = 5 in Game Settings |
| Island | flat disc, radius 30 studs, surface at Y = 100 |
| Target area | disc radius 28 (2-stud margin to the edge) |
| Player spawn | own island centre, facing the hub (hub if no island) |
| Shooter ring | shooters stand on small platforms at radius 60 from the centre, at island surface height, evenly spaced (360°/n), with the bridge side exactly between two shooters |
| Shooter look | per Shiba Tier (see Upgrades): `ReplicatedStorage/Assets/Shiba`, `GalaxyShiba`, `LavaShiba`, `IceShiba`, `RoboShiba`, `AngelShiba`, `DemonShiba`, `GodShiba` (6 studs tall); a missing model falls back to the next lower tier's model with an outline in the tier colour, then `Shooter`, then a red block with barrel |
| Fall-off | below Y = 50 → back to own island (or hub), no penalty |

Players never affect each other: projectiles only exist for their owner's island, only the owner's character can be hit, and projectiles never physically collide with anything — the server moves them along their planned path, knockback comes from the hit code only.

## NPC shooters

- Shooters **never aim at the player**. Each shot picks a random target point, uniformly distributed in the target area.
- **Anti-farm rule:** the projectile's whole path (flight and both bounces) must stay at least `projectile radius + 6` studs away from the player's position at fire time; otherwise pick again (max 30 tries, then skip the turn). Standing still therefore earns 0 points.
- **Spread:** the random target point is the spread; additionally the launch speed varies ±10 % per shot.
- **Telegraph:** the shooter turns toward its target 0.5 s before firing.
- Fire interval: set by the Shiba tier (5.0 s → 1.3 s, see Upgrades), halved by the 2× fire-rate boost. Shooters only fire while their owner is within 45 studs of their island centre (not on the hub). **Shooters take turns:** with n shooters one of them fires every `interval / n` seconds, never two at once.
- A shooter model may contain a part named `Stick` (hidden for 0.4 s after each throw) and an Attachment `Muzzle` (where the throw starts).

## Projectiles

Projectile tiers (upgrade `ProjectileTier`): **Stick** (BaseReward 10) → **Bone** (20) → **Golden Stick** (40) → **Diamond Stick** (80). They fly the same; only look and reward differ. Models `ReplicatedStorage/Assets/Stick`, `Bone`, `GoldenStick`, `DiamondStick`; a missing model uses the next lower tier's model, tiers above Stick draw a trail in their colour, no model at all = coloured sphere. Hits use an invisible sphere of the projectile's diameter; the model is scaled so its longest side equals that diameter and spins in flight.

| Field | Bonk Stick |
|-------|------|
| Diameter | 3 studs |
| Base launch speed | 36 studs/s |
| BaseReward | 10 Bonk Points |

**Flight (visible arc):** launched at a fixed 45° angle toward the target point. Per projectile, gravity is set (with a `VectorForce`) to `g = v² / d` (v = launch speed, d = horizontal distance) so it lands exactly on the target. Every shot has the same readable arc shape (apex = d / 4); higher speed only shortens the flight time. At base speed a 60-stud shot flies 2.4 s.

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
Reward = floor(BaseReward × QualityMult × HeadMult × ComboMult × ShibaTierMult × BoostMult), at least 1

BaseReward    = projectile tier: 10 / 20 / 40 / 80
HeadMult      = 2 if the projectile touched the head, else 1
ComboMult     = 1 + 0.1 × (combo − 1), at most 3
ShibaTierMult = see Upgrades (1 → 60)
BoostMult     = 2 while the 2× points boost runs, else 1
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

Cost of the next level: `cost(n) = floor(BaseCost × Growth^n)`, n = current level. Four upgrades (projectile size and
fire rate were removed on 2026-09-24: projectiles always have the same size, the fire rate comes with the Shiba tier).

| Id | Menu name | Effect per level | Level 0 | Max level | BaseCost | Growth |
|----|-----------|-----------------|---------|-----------|----------|--------|
| `ShooterTier` | Shiba Tier | all Shibas evolve: new model, faster throws, more points | Shiba | 7 | 2,000 | 7 |
| `ProjectileTier` | Projectile Tier | next projectile (see Projectiles) | Stick | 3 | 1,500 | 10 |
| `Shooters` | More Shibas | +1 Shiba | 1 | 7 (8 Shibas) | 500 | 4 |
| `MoveSpeed` | Move Speed | WalkSpeed +3 | 16 | 10 (46) | 100 | 2.6 |

Shiba tiers (`Config/Gameplay → Shooters.Tiers`):

| Tier | Throws every | Points × |
|------|-------------|----------|
| Shiba | 5.0 s | 1 |
| Galaxy Shiba | 4.2 s | 1.8 |
| Lava Shiba | 3.5 s | 3.2 |
| Ice Shiba | 2.9 s | 5.8 |
| Robo Shiba | 2.4 s | 10.5 |
| Angel Shiba | 2.0 s | 19 |
| Demon Shiba | 1.6 s | 34 |
| God Shiba | 1.3 s | 60 |

- MoveSpeed exists so the player can **reach impact points in time** (not to dodge). It also raises the achievable hit quality.
- **Active Shibas:** buying adds a Shiba; the "More Shibas" card sets how many are active (1 … owned) for free.
- Purchases are validated on the server: known upgrade id, below max level, enough Bonk Points, max 5 requests/s.
- Upgrade menu: one card per upgrade with level badge, current → next value (tier names in their colours), what the next
  level gives, one dot per level, buy button (green when affordable). The UPGRADES button shows "!" when something is affordable.

## Hub features

All rewards in "bonks" = what one normal bonk pays right now (projectile BaseReward × Shiba tier multiplier), so they stay
worth it at every stage. Config: `Config/Hub`.

- **Daily Spin:** one free spin every 24 h (also from the SPIN button). Wheel: 25 / 50 / 100 bonks, JACKPOT 500 bonks,
  2× points 10 min, 2× fire rate 10 min, 2× points 30 min (weighted). The server picks the prize; boosts are saved and keep
  running across rejoins; running boosts show under the points.
- **Coin Flip vs house:** pick heads/tails, bet 10 % / 25 % / 50 % / all of your Bonk Points (min 10), 50:50, win = bet doubled.
- **Duels:** challenge another player in the server for 100 / 1,000 / 10,000 / 100,000; they get a popup (20 s) to accept;
  both pay the stake, a fair coin decides, the winner gets both. One open duel per player.
- **Daily Quests:** 3 per UTC day (same for everyone, never two of the same kind), e.g. catch N sticks, N headbonks, reach a
  xN combo, N Hard+ bonks, win coin flips, spin the wheel, buy upgrades. Claim for 20–120 bonks. QUESTS button shows "!" when claimable.
- **Leaderboard:** "Bonk Points" in the Roblox player list; the TOP BONKERS board ranks the top 10 by total Bonk Points
  ever earned (all servers, OrderedDataStore, refreshed every minute; this server only when DataStores are unavailable).
  Admin gifts and coin-flip stakes coming back don't count, only real earnings.
- Only earned points can be bet. Bonk Points must never be sold for Robux while coin flips exist (Roblox rules on paid random items).

## Admin (testing)

- Admins get an **ADMIN** button (left) with: +1K / +100K / +10M / +1B points, set points to 0; each upgrade −/+ and MAX ALL;
  reset daily spin, new quests, finish quests; 2× points / 2× fire rate boost (10 min), clear boosts; teleport to hub / own
  island, all Shibas fire now; RESET EVERYTHING (second click confirms; keeps the leaderboard total).
- Admins: everyone in Studio playtests, the experience owner, and the UserIds in `src/shared/Config/Admin.luau`.
- The server checks admin rights on every request (`AdminCommand`, `AdminService`); the client check only hides the button.

## Economy

- Currency: **Bonk Points** (integer). Earned by hits, daily spin, quests and coin flips. Start with 0.
- Pacing target (for tuning): first upgrade after ~90 s of active play, 5 purchases within the first 10 minutes.

## UI (MVP)

- HUD: Bonk Points (counts up), running boosts, left buttons UPGRADES / QUESTS / SPIN (/ ADMIN) with "!" badges, short messages at the bottom.
- Menus: one open at a time, built in code (`client/UI/Widgets`), shared look (`client/UI/Theme`).

## Saving

Per player (DataStore, key = UserId): Bonk Points, total earned, level per upgrade, active shooter count, last daily spin, boost end times, today's quests. Loaded on join, saved on leave, every 60 s, and on server shutdown.

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
- Anything to do on other players' islands (you can walk there, but projectiles only exist for the owner)
- Cosmetics, additional upgrade trees
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
