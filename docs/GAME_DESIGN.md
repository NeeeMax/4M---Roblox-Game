# Game Design — GET BONKED

> Not decided yet = not in this file. Claude Code must not invent design decisions; if something is missing here, ask.
> All numbers below are **starting values**. They live in `src/shared/Config/` and are tuned in playtests.

## One-sentence pitch

NPCs lob silly objects at your personal floating island — run and jump **into** them to get bonked, earn Bonk Dollars, and buy upgrades that make it faster, bigger and more chaotic.

## Core loop

- **Every 5 seconds:** an NPC aims at a random spot on your island and fires. You read the arc, run there and try to take the hit (ideally running and jumping into it for a better hit quality).
- **Every 1–5 minutes:** spend Bonk Dollars on one of 5 upgrades.
- **Every session:** push upgrade levels higher; progress is saved.

## Target players and session length

Casual Roblox players, roughly 8–14. Understandable in under 10 seconds without a tutorial. Target session: 15–30 minutes.

## World

| Thing | Value |
|-------|-------|
| Layout | a big **hub island** (radius 70) in the middle, **5 player islands** (radius 80) around it at 280 studs, each joined to the hub by a plank bridge with rails and lamps (tycoon style). Config: `Config/World` |
| Hub | stations between the bridges: Daily Spin, Coin Flip, Shop, Daily Quests, Top Bonkers leaderboard; Shiba statue with "GET BONKED" in the middle; how-to-play board in front of the hub spawn. Menus open via ProximityPrompt |
| Player island | grass island; in the middle the **field** (sand, radius 30, low white border with a gap toward the bridge) where sticks land; Shibas stand on the island around it; trophies on lit pedestals behind the field; trees and flowers on the outer ring; owner name on a sign where the bridge arrives |
| Islands | one per player, assigned on join (first free plot), freed on leave; more than 5 players = the extra ones stay on the hub. **Max Players must be 5** (Creator Hub → Configure → Places) |
| Target area | disc radius 28 inside the field; bounces can continue anywhere on the island |
| Player spawn | own island centre, facing the hub (hub spawn in front of the how-to board if no island) |
| Shooter ring | Shibas on platforms at radius 56, evenly spaced, with the bridge side exactly between two of them. Each Shiba sits inside an invisible wall (cylinder around platform and Shiba) so players can't walk through it; it doesn't affect projectiles or hits |
| Shiba platforms | per tier, built from parts (`Config/ShibaPlatforms`), the Shiba stands and throws from its top: Shiba wooden stump (1.4 studs), Shades black-and-gold podium (2), Buff gym weight plate (1.05), Chef kitchen counter with cutting board (2.9), Police blue-white striped pedestal with siren lights (1.8), Ninja dark stone with red trim (1.6), Gold coin stack (2), Galaxy purple space rock floating over a glowing ring (3.2), Giant cracked rock plateau (1.8, 21 studs wide), Cheems God golden temple column on a cloud (10). Tops are at least 0.2 studs above the island surface (equal heights flicker) |
| Shooter look | per Shiba Tier (see Upgrades): `ReplicatedStorage/Assets/Shiba`, `ShadesShiba`, `BuffShiba`, `ChefShiba`, `PoliceShiba`, `NinjaShiba`, `GoldShiba`, `GalaxyShiba`, `GiantShiba`, `CheemsGod`, each scaled to its tier's height (Ninja 5.5 … Shiba 6 … Buff/Chef 7.5 … Cheems God 12, Giant 16 studs). From the Gold Shiba on, every tier gets a glow and particles, more special with each tier but kept moderate so they don't blow out the screen (`Config/ShibaEffects`: Gold glints; Galaxy stars and nebula haze, floats gently up and down, a small planet and moon orbit its head; Giant dust and embers; Cheems God holy glow, sparkles and light motes). Every Shiba holds the player's current projectile (Projectile Tier) in its paw (its `Grip` marker on the paw, long side along the paw's stick; it swings with the throwing arm and is gone from the paw for 0.4 s after each release). A missing model falls back to the next lower tier's model with an outline in the tier colour, then `Shooter`, then a red block with barrel |
| Looks | warm lighting with atmosphere, soft bloom and sun rays (kept low so the hub does not glare: bloom 0.3 / threshold 1.8; on the hub only thin accents such as the station rings and shop orbs are Neon, sign and board frames are coloured plastic); real terrain water far below (surface Y = 40); clouds and small floating islands in the distance; rocky cones under every island |
| Props | everything that should become a 3D model is a `PropService` prop: `ReplicatedStorage/Assets/<name>` if it exists, else a part-built placeholder. In Studio placeholders get a pink box and a "MODEL: <name>" label (list in `assets/README.md`) |
| Fall-off | below Y = 50 → back to own island (or hub), no penalty |

## NPC shooters

- **Golden sticks:** 5 % of all projectiles are golden (15 % with the Lucky Sticks pass): gold outline and trail, pay ×5.
- Shooters **never aim at the player**. Each shot picks a random target point, uniformly distributed in the target area.
- **Anti-farm rule:** the projectile's whole path (flight, bounces, settling hops and resting point) must stay at least `projectile radius + 6` studs away from the player's position at fire time; otherwise pick again (max 30 tries, then skip the turn). Standing still therefore earns 0 points.
- **Spread:** the random target point is the spread; additionally the launch speed varies ±10 % per shot.
- **Telegraph:** the shooter turns (smoothly) toward its target 0.5 s before firing and winds up its throwing arm.
- Fire interval: set by the Shiba tier (5.0 s → 1.3 s, see Upgrades), halved by the 2× fire-rate boost. Shooters only fire while their owner is within 45 studs of their island centre (not on the hub). **Shooters take turns:** with n shooters one of them fires every `interval / n` seconds, never two at once.
- A shooter model may contain a part named `Stick` (replaced by the current projectile's model, which is hidden for 0.4 s after each throw; without a projectile model the stick itself is) and an Attachment `Muzzle` (where the throw starts). Throws start from the Shiba's standing height on its platform.

## Projectiles

Projectile tiers (upgrade `ProjectileTier`): **Stick** (BaseReward 10) → **Newspaper** (13) → **Baguette** (16) → **Rolling Pin** (20) → **Baseball Bat** (25) → **Giant Bone** (32) → **Squeaky Hammer** (40) → **BONK Sign** (50) → **Neon Stick** (63) → **Legendary Stick** (80). They fly the same; only look and reward differ. Models `ReplicatedStorage/Assets/Stick`, `Bone`, `GoldenStick`, `DiamondStick`; a missing model uses the next lower tier's model, tiers above Stick draw a trail in their colour, no model at all = coloured sphere. Hits use an invisible sphere of the projectile's diameter; the model is scaled so its longest side equals that diameter and spins in flight.

| Field | Bonk Stick |
|-------|------|
| Diameter | 3 studs |
| Base launch speed | 36 studs/s |
| BaseReward | 10 Bonk Dollars |

**Flight (visible arc):** launched at a fixed 45° angle toward the target point. Per projectile, gravity is set (with a `VectorForce`) to `g = v² / d` (v = launch speed, d = horizontal distance) so it lands exactly on the target. Every shot has the same readable arc shape (apex = d / 4); higher speed only shortens the flight time. At base speed a 60-stud shot flies 2.4 s.

**Bounces:** after landing it bounces **twice**: each bounce keeps 50 % of the vertical and 70 % of the horizontal speed (at base speed and a 60-stud shot: first bounce ≈ 3.7 studs high, second ≈ 1 stud; shorter shots have higher gravity and lower bounces). Then it makes **two small settling hops** of fixed height (0.7 and 0.3 studs, never higher than the hop before) keeping 45 % of the horizontal speed each, so the landing is visible whatever the shot's gravity, and comes to rest. While hopping, the model turns to lie flat along its direction of travel, and near the ground it is drawn with its lowest point on the ground (the hit sphere centre stays one radius above the ground). The whole path is computed when the shot is planned (`src/shared/Util/ProjectilePath.luau`, `Build`); every client draws the projectile along it (`docs/decisions/0004`). A bounce that leaves the island makes it fall off the edge. Tuning: `Gameplay.Projectiles` `Bounces`, `BounceRestitution`, `BounceFriction`, `SettleHopHeights`, `SettleFriction`, `LandingFadeTime`, `CollectableWhileFading`.

**Lifetime / cleanup:** after its last settling hop it lies still and **fades out over 0.6 s** (`LandingFadeTime`), then each client stops drawing it (all on the synced server clock). It **can be collected during flight, bounces and settling hops, not while it fades** (`CollectableWhileFading = false`; the client check and the server validation both follow this setting). A projectile that falls off the island edge has no fade: it vanishes 20 studs below the island. The server destroys its marker 0.5 s after the fade ends (`DespawnDelay`), 15 s after launch at the latest, and validates hit reports until 2 s (`ReportGracePeriod`) after the collectable window ended (network delay). Max 60 live projectiles per island; the oldest is destroyed first. All projectiles of a player are destroyed when they leave.

## Hits (server decides)

- The owner's client detects the touch (what the player sees on screen) and reports the projectile id. See `docs/decisions/0003-client-reports-hits-server-validates.md`.
- The **server alone decides** and awards points. A report counts only if: the projectile belongs to the player, hasn't paid yet, the player is alive and not immune, and the projectile's path so far (flight, bounces, settling hops) passed within `projectile radius + 2 + 6` studs of the character's root on the server, and the report arrives at most 2 s after the projectile stopped being collectable. Max 10 reports/s.
- **Pickup padding (+2 studs):** projectiles are easier to collect than their model size suggests. The client counts a touch when the character overlaps a sphere of `projectile radius + 2` studs (`Gameplay.Hits.PickupPadding`) around the projectile (a Bonk Stick: 3.5 studs instead of 1.5); the server adds the same padding before its tolerances, so both sides agree. The models are not bigger. Anti-farm stays safe: the padded reach of a standing character (≈ radius + 2 + ~2 studs of body) is below the anti-farm distance of radius + 6.
- **Each projectile pays out at most once.**
- **Hit immunity:** 0.5 s after a hit (checked on client and server). Projectiles touching the player during immunity are ignored (they can still hit afterwards).
- **Knockback:** only a small nudge: 0.12 s at 6 studs/s horizontally in the projectile's flight direction + 4 studs/s up (under a stud, a tiny hop; `Gameplay.Knockback`). It only pushes along that direction, so the player keeps walking. Auto-catches have no direction, only the tiny hop. No ragdoll in MVP.

### Reward

```
Reward = floor(BaseReward × QualityMult × HeadMult × ComboMult × ShibaTierMult × BoostMult), at least 1

BaseReward    = projectile tier: 10 / 13 / 16 / 20 / 25 / 32 / 40 / 50 / 63 / 80
HeadMult      = 2 if the projectile touched the head, else 1
ComboMult     = 1 + 0.1 × (combo − 1), at most 3
ShibaTierMult = see Upgrades (1 → 60)
BoostMult     = 2 while the 2× Bonk Dollars boost runs, else 1
GoldenMult    = 5 for golden projectiles, else 1
PassMult      = 2 with the 2× Bonk Dollars pass, × 1.25 with VIP
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
  passed within projectile radius + 2 (pickup padding) + 4 studs of the server-side head.
- **Combo:** every hit within the combo window of the previous hit adds 0.1 to the multiplier (max ×3 at 21 hits).
  Window = 2 s + 1.5 × time between two shots (interval / active shooters), so it stays fair with more or faster shooters.
  The HUD shows `COMBO xN ×M` with a bar that runs out when the window ends.

## Feedback (client)

- Popup above the character: `+X BONK` for 1.0 s; for Good and above prefixed with the quality, e.g. `HARD BONK! +50`.
- One bonk sound (a custom cartoon "bonk", ≈ 0.9 s, `Gameplay.Bonk.SoundId`); pitch 1.0 + 0.05 per quality tier above Normal. Every hit plays its own copy, so quick hits overlap.
- Head hits say `HEADBONK!` instead of `BONK`.
- Stars burst from the head in the quality colour (6 + 6 per tier above Normal); from Hard on the camera shakes briefly.

## Upgrades

Cost of the next level: `cost(n) = floor(BaseCost × Growth^n × (1 + Curve × n²))`, n = current level. The `Curve`
term keeps the first levels cheap and bends the late ones up (see **Pacing** below). Four upgrades (projectile size and
fire rate were removed on 2026-09-24: projectiles always have the same size, the fire rate comes with the Shiba tier).

| Id | Menu name | Effect per level | Level 0 | Max level | BaseCost | Growth | Curve |
|----|-----------|-----------------|---------|-----------|----------|--------|-------|
| `ShooterTier` | Shiba Tier | all Shibas evolve: new model, faster throws, more points | Shiba | 9 | 400 | 3.5 | 0.1 |
| `ProjectileTier` | Projectile Tier | next projectile (see Projectiles) | Stick | 9 | 150 | 3.6 | 0.15 |
| `Shooters` | More Shibas | +1 Shiba | 1 | 7 (8 Shibas) | 60 | 5.5 | 0.2 |
| `MoveSpeed` | Move Speed | WalkSpeed +3 | 16 | 10 (46) | 40 | 3.5 | 0.1 |

Costs per level:

| Upgrade | 0→1 | 1→2 | 2→3 | 3→4 | 4→5 | 5→6 | 6→7 | 7→8 | 8→9 | 9→10 |
|---------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| Shiba Tier | 400 | 1.5K | 6.9K | 33K | 156K | 735K | 3.4M | 15M | 67M | — |
| Projectile Tier | 150 | 621 | 3.1K | 16K | 86K | 431K | 2.1M | 9.8M | 45M | — |
| More Shibas | 60 | 396 | 3.3K | 28K | 231K | 1.8M | 14M | — | — | — |
| Move Speed | 40 | 154 | 686 | 3.3K | 16K | 74K | 338K | 1.5M | 6.7M | 29M |

Shiba tiers (`Config/Gameplay → Shooters.Tiers`):

| Tier | Throws every | Points × |
|------|-------------|----------|
| Shiba | 5.0 s | 1 |
| Shades Shiba | 4.3 s | 1.6 |
| Buff Shiba | 3.7 s | 2.5 |
| Chef Shiba | 3.2 s | 3.9 |
| Police Shiba | 2.7 s | 6.2 |
| Ninja Shiba | 2.4 s | 9.7 |
| Gold Shiba | 2.0 s | 15 |
| Galaxy Shiba | 1.8 s | 24 |
| Giant Shiba | 1.5 s | 38 |
| Cheems God | 1.3 s | 60 |

- MoveSpeed exists so the player can **reach impact points in time** (not to dodge). It also raises the achievable hit quality.
- **Active Shibas:** buying adds a Shiba; the "More Shibas" card sets how many are active (1 … owned) for free.
- Purchases are validated on the server: known upgrade id, below max level, enough Bonk Dollars, max 5 requests/s.
- **Upgrade stands** (main way to buy, tycoon style, `Config/Stations`): on every player island one market-stall stand
  per upgrade (`Prop_UpgradeStand_<UpgradeId>`, part-built until a model exists) on both sides of the path from the
  bridge to the field (Shiba Tier / Projectile Tier nearer the field, More Shibas / Move Speed nearer the bridge).
  Above each stand floats a billboard: upgrade name, current value (tier name in its colour / number), level badge
  `xN`, level bar, a big UPGRADE button look (green when affordable, grey when not, gold MAXED at the top) with the
  cost (green / grey) and an **E** key hint. Only the island owner can use their stands and sees the billboards.
  - **E "Upgrade"** buys one level. With the **Stack Upgrade** pass one press buys as many levels as affordable, up to 10
    (the button then says `UPGRADE ×N` with the total cost).
  - **F "Buy with R$"** buys the next level with Robux (products `Instant<UpgradeId>` in `Config/Shop`).
  - **More Shibas** also has a glowing green **NEW SHIBA** pad with its cost on the Shiba ring, where the next Shiba will
    stand (of the new ring's spots, the one farthest from the Shibas standing now). Stepping on it buys the Shiba
    (2 s cooldown). The pad disappears at the max.
  - **Hints** (off with Settings → Hints): a bouncing **NEW** arrow over every stand whose next level you can afford, and
    once per upgrade level a popup "You can afford a new upgrade! [SHOW ME]" (only when you are not already at that
    stand; several newly affordable upgrades give one popup, for the cheapest). SHOW ME draws a glowing line from your
    character to the stand for 8 s (or until you arrive).
  - The big round **yellow arrow button** at the bottom centre does the same as SHOW ME for the cheapest affordable
    upgrade ("Nothing affordable yet" otherwise).
- **Run Faster** pass: WalkSpeed ×1.5 on top of Move Speed.

### Pacing

Goal: the first upgrades come fast (first buy within ~30 s, five within ~4 min), later ones slower but never a wall
(at most ~75 min of play for the very last levels), so boosts and instant upgrades are worth buying in the mid and late
game. Estimated with a player who always buys the cheapest upgrade next:

```
income / min = 60 / FireInterval(Shiba tier) × Shibas × catch rate × BaseReward(projectile) × Shiba tier mult × 1.3
catch rate   = 60 % (+2 % per Move Speed level); 1.3 = average bonus from quality, head hits, combo and golden sticks
```

| Buy # | Upgrade bought | Cost | Income at that stage (/min) | Wait for it (min) | Play time so far |
|-------|----------------|------|-----------------------------|-------------------|------------------|
| 1 | Move Speed 1 | 40 | 94 | 0.4 | 26 s |
| 2 | More Shibas 1 | 60 | 95 | 0.6 | 1.1 min |
| 3 | Projectile Tier 1 | 150 | 191 | 0.8 | 1.8 min |
| 5 | More Shibas 2 | 396 | 253 | 1.6 | 4 min |
| 6 | Shiba Tier 1 | 400 | 380 | 1.1 | 5 min |
| 10 | Projectile Tier 3 | 3.1K | 1.6K | 1.9 | 10 min |
| 15 | Projectile Tier 4 | 16K | 5.0K | 3.3 | 23 min |
| 20 | Shiba Tier 5 | 156K | 19K | 8 | 50 min |
| 25 | Move Speed 8 | 1.5M | 96K | 16 | 1.8 h |
| 30 | Projectile Tier 8 | 9.8M | 258K | 38 | 3.8 h |
| 35 | Shiba Tier 9 (all maxed) | 67M | 911K | 73 | 8.2 h |

Robux speeds this up without selling Bonk Dollars: 2× Dollars (pass or 30 min boost) halves every wait, 2× Fire Rate
nearly does, and the instant upgrades skip one level.
- Upgrade menu: one card per upgrade with level badge, current → next value (tier names in their colours), what the next
  level gives, one dot per level, buy button (green when affordable). The UPGRADES button shows "!" when something is affordable.

## Hub features

All rewards in "bonks" = what one normal bonk pays right now (projectile BaseReward × Shiba tier multiplier), so they stay
worth it at every stage. Config: `Config/Hub`.

- **Daily Spin:** 1 free spin per UTC day (VIP: 2), also from the SPIN button. A pie-chart wheel (segment size = chance,
  every chance listed next to it): 5 bonks 26 %, Nothing 16 %, 10 bonks 20 %, 2× Dollars 5 min 12 %, 20 bonks 12 %,
  2× fire 5 min 8 %, Bonk Rain 4 %, JACKPOT 50 bonks 2 %. Small on purpose: a daily treat, not the main income.
  Spins are never sold for Robux. The server picks the prize; boosts are saved and keep running across rejoins.
- **Login streak (GIFTS):** consecutive login days climb a 7-day reward track (10 / 20 bonks, 2× Dollars 10 min, 40 bonks,
  Bonk Rain, 80 bonks, Streak trophy + 150 bonks); missing a day starts over; one claim per day.
- **Playtime gifts (GIFTS):** after 5 / 10 / 20 / 30 / 60 minutes played per UTC day: 5 bonks, 10 bonks, 2× fire 5 min,
  25 bonks, Bonk Rain.
- **Bonk Rain:** 30 s of sticks dropping all over your field (5 per second, normal rules, golden chance). Collected from the
  shop, wheel and gifts; started with the BONK RAIN button while on your island.
- **Coin Flip vs house:** pick heads/tails, bet 10 % / 25 % / 50 % / all of your Bonk Dollars (min 10), 50:50, win = bet doubled.
- **Duels:** challenge another player in the server for 100 / 1,000 / 10,000 / 100,000; they get a popup (20 s) to accept;
  both pay the stake, a fair coin decides, the winner gets both. One open duel per player.
- **Daily Quests:** 3 per UTC day (same for everyone, never two of the same kind), e.g. catch N sticks, N headbonks, reach a
  xN combo, N Hard+ bonks, win coin flips, spin the wheel, buy upgrades. Claim for 20–120 bonks. QUESTS button shows "!" when claimable.
- **Leaderboard:** "Bonk Dollars" in the Roblox player list; the TOP BONKERS board ranks the top 10 by total Bonk Dollars
  ever earned (all servers, OrderedDataStore, refreshed every minute; this server only when DataStores are unavailable).
  Admin gifts and coin-flip stakes coming back don't count, only real earnings.
- Only earned points can be bet. Bonk Dollars must never be sold for Robux while coin flips exist (Roblox rules on paid random items).

## Server events

Every ~15 minutes (`Config/Events`: `Interval` 15 min from one start to the next, ± 1 min jitter, first one 5 min after
the server starts) one random event (equal weights) runs for everyone in the server:

| Event | Duration | Effect |
|-------|----------|--------|
| **Golden Minute** | 60 s | every projectile is golden (pays the golden ×5) |
| **Mega Stick** | 90 s | each player's Shibas throw ONE giant stick (3× diameter) onto their field; catching it pays ×50. Only thrown while you are on your island; a player who joins during the event gets one too |
| **Double Dollars** | 120 s | every bonk pays ×2 (stacks with passes, boosts, golden) |
| **Stick Storm** | 90 s | every Shiba's fire interval is halved |

A banner at the top of the screen shows the running event and its countdown (a big splash when it starts); between
events a small line shows "Next event in mm:ss". Players who join mid-event see it right away. Admins can start one
right away (`EventService.StartNow(eventId)`, hooked into the admin menu later).

## Shiba-Index

A collection book (INDEX menu, `Config/Index`) with one entry per Shiba tier (10), projectile tier (10), the golden stick
and each trophy (10): 31 entries today, new tiers and trophies are added automatically. An entry is **found** when you
first reach it: Shiba / projectile tier bought (or skipped past), first golden stick caught, trophy owned. Unfound entries
show as a dark "???" silhouette. Each found entry pays a one-time discovery reward you claim on its card (in bonks, see
Hub features): Shibas 20 + 10 per tier, projectiles 15 + 5 per tier, golden stick 50, trophies by rarity (Common 25,
Rare 50, Epic 100, Legendary 200, Exclusive 300). Finding all entries unlocks a completion bonus of 1,000 bonks.
A bar on top shows the progress ("12/31 found").
## Obby (jump and run)

A spiral tower of chunky green / yellow / orange platforms in the hub centre (`ObbyService`, layout in `Config/Obby`),
with the Shiba statue and the "GET BONKED" title on top. Footprint within ~20 studs of the centre, so the paths to the
bridges and stations stay free; falling off lands you on the plaza.

- **Course:** start pad on the plaza (south side, facing the spawn point, START sign on the tower), 16 platforms
  spiralling up ~1.8 turns to the finish pad on top of the tower (42 studs up). Easy blocks first, then smaller blocks,
  narrow beams and three moving platforms (in/out, up/down, sideways), with three bigger round pads to rest on.
  **No checkpoints:** one run from the START pad to the top.
- **Timing (server):** stepping off the start pad starts the run (`ObbyStarted`); reaching the finish pad ends it.
  A finish only counts after at least 8 s (`MinTime`) and with at least half of the platforms passed since the start
  (`MinStageShare`; invisible progress zones above every platform, following the moving ones; blocks teleporting and
  flying straight up). **Falling means starting over:** after standing on anything higher than the plaza
  (`FallHeight` 1.5 studs, floor found by a short ray down from the character), landing back on the plaza drops the
  run ("You fell! Start again from the START pad." message; the client timer stops by the same rule). A run is also
  dropped after 10 min, on respawn, or when you walk more than 30 studs from the hub centre.
- **Reward:** at most once per 30 min per player: 40 bonks' worth of Bonk Dollars + a 5-minute 2× Bonk Dollars boost.
  Finishing during the cooldown still counts for the best time. Best time and last reward time are saved
  (`state.Obby`). Daily quest "Climb the obby tower" (30 bonks).
- **FASTEST CLIMBERS board** left of the obby entrance: top 10 best times of all servers (OrderedDataStore
  `ObbyTimes_v1`, tenths of a second, refreshed every minute; this server's players when DataStores are unavailable).
- **Client:** timer at the top while running; popup "FINISHED! 23.4 s · +฿ 1,234 · 2× dollars 5 min · next reward in 29:59"
  (or "Best: …" / "NEW BEST TIME!" during the cooldown).
- **Testing:** set `RewardCooldown` in `Config/Obby` to e.g. 20 to get the reward again quickly.

## Shop (monetisation)

Goal: earn well without being a scam. Robux buys time savers, boosts and cosmetics; Bonk Dollars are **never** sold for
Robux (coin flips exist) and wheel spins are never sold. Prices shown in the shop must match the Creator Hub.
Roblox ids live in `Config/Shop` (0 = not created yet: free test purchase in Studio, "Coming soon" live).

| Kind | Item | Robux | Effect |
|------|------|-------|--------|
| Pass | 2× Bonk Dollars | 199 | every bonk ×2 |
| Pass | VIP | 299 | +25 % points, golden VIP tag, VIP trophy, 2 daily spins |
| Pass | Lucky Sticks | 149 | golden chance 5 % → 15 % |
| Pass | +2 Shiba Slots | 249 | More Shibas max 7 → 9 (10 Shibas) |
| Product | Bonk Rain | 49 | +1 Bonk Rain (starts right away when on your island) |
| Product | 2× Dollars 30 min / 2× Fire Rate 30 min | 39 each | boost |
| Product | Shiba Tier Skip | 99 | next Shiba tier now (blocked at the top tier) |
| Product | Starter Pack | 49 | once: 2× Dollars 1 h + 3 Bonk Rains + Starter trophy; offered in a popup for 48 h after the first join |
| Product | Diamond / Rainbow trophy | 99 / 249 | exclusive trophies |
| Product | Instant Shiba Tier / Projectile Tier / Shiba / Speed | 99 / 79 / 49 / 25 | +1 level of that upgrade now (blocked when it is maxed) |
| Product | Double Offline Earnings | 39 | only in the "Welcome back" popup: pays 2× the pending Shiba Bank earnings |

**POWERS** (first shop tab, big cards with yellow Robux price pills, "OWNED" once bought; other code opens it with
`ShopController.OpenTab("POWERS")`):

| Pass | Robux | Effect | Implemented in |
|------|-------|--------|----------------|
| Manage | 199 | manage all income sources from one place: the upgrade menu opens anywhere | HudController |
| Run Faster | 99 | walk speed x1 → x1.5 | UpgradeService |
| Stack Upgrade | 149 | buy several upgrade levels at once (x1 → x10) | UpgradeService |
| Auto-Catch | 249 | every 0.25 s, sticks whose current position is within 10 studs of the character are collected as a Normal bonk (no head bonus, combo counts); only while they could be caught by hand. Look (client only): a small red/silver magnet circles the owner; each auto-caught stick is pulled into the player with a beam and a trail, sparkles pop and the magnet wiggles | AutoCatchService, MagnetController |

Trophies stand on your island for everyone to see: Wooden 5K, Bronze 50K, Silver 500K, Golden 5M, Galaxy 100M Bonk
Points (long-term goals), plus exclusive ones (Starter, 7-Day Streak, VIP, Diamond, Rainbow).
Receipts are granted exactly once (handled purchase ids are saved); pass ownership is checked with Roblox on every join.

## Offline Shiba Bank

While the player is away, their Shibas keep earning (Config/Economy → `OfflineBank`, OfflineService):

- **Income rate:** every 60 s of play the Bonk Dollars earned in that minute (hits, spin, quests, gifts, coin-flip wins;
  not admin gifts or the offline payout itself) are smoothed into `Bank.IncomePerMinute`
  (`rate += 0.3 × (sample − rate)`, the first sample sets it). A sample counts at most 8 normal bonks per Shiba throw,
  so a big coin-flip win can't inflate the rate.
- **Last seen:** every save (leave, autosave, shutdown) stamps `Bank.LastSeenAt`.
- **On join:** time away = now − LastSeenAt, only if at least 60 s, capped at 8 h.
  `Pending += IncomePerMinute × minutes away × 10 %`, then the "WELCOME BACK!" popup shows the time away and the amount.
- **OKAY** pays Pending (counts for the leaderboard). **x2 DOUBLE IT! (R$ 39)** opens the "Double Offline Earnings" product;
  when Roblox grants it, 2× Pending is paid. Unclaimed earnings stay pending (and add up) until claimed.
- Example: 1,000 points/min while playing, away 2 h → 1,000 × 120 × 0.1 = 12,000 (24,000 doubled).

## Admin (testing)

- Admins get an **ADMIN** button (left) with: +1K / +100K / +10M / +1B points, set points to 0; each upgrade −/+ and MAX ALL;
  reset daily spin, new quests, finish quests; 2× Dollars / 2× fire rate boost (10 min), clear boosts; teleport to hub / own
  island, all Shibas fire now; toggle each pass, +1 Bonk Rain, start a rain, all trophies, unlock gifts, show the
  starter offer again; RESET EVERYTHING (second click confirms; keeps the leaderboard total and Robux purchases).
- Admins: everyone in Studio playtests, the experience owner, and the UserIds in `src/shared/Config/Admin.luau`.
- The server checks admin rights on every request (`AdminCommand`, `AdminService`); the client check only hides the button.

## Economy

- Currency: **Bonk Dollars** (integer). Earned by hits, daily spin, quests and coin flips. Start with 0.
  (It used to be called Bonk Points: the saved field and the code keep the name `BonkPoints` / `AddPoints`, so saves
  are unchanged; only what players see changed. Name and plain-text symbol live in `Config/Economy → Currency`.)
- **Symbol:** a bold capital **B with a vertical bar through it** (like "฿"), drawn in front of every amount:
  "฿ 1,234". The game fonts have no such glyph, so menus build it from UI parts (`Widgets.MoneySymbol`: a "B"
  TextLabel plus a thin bar Frame, same colour, scaling with the text size). `Format.Money(n)` writes amounts as
  **"B$ 1,234"**; `Widgets.MoneyText` / `Widgets.SetMoneyText` draw every "B$" in a string as the symbol, so server
  messages (notifications, spin results) just use `Format.Money` and the HUD shows the symbol.
- **Plain-text form: "B$"** (never "฿", which the Roblox fonts may not have) wherever a UI element can't be used:
  the TOP BONKERS board on the hub (SurfaceGui text), and any future chat messages. The player-list column
  (leaderstats) is named "Bonk Dollars". Rewards counted in hits ("20 Bonks", quest/index "30 bonks") stay in bonks.
- Where the symbol shows: HUD counter, upgrade card prices and "per bonk" line, upgrade stand billboards and the
  Shiba pad, shop trophy prices, coin flip bets/stakes/results/duel invites, bonk popups, spin result, obby reward,
  "Welcome back" popup, notifications.
- Pacing target (for tuning): first upgrade after ~30 s of active play, 5 purchases within the first 5 minutes, all
  upgrades maxed after ~8 h (see Upgrades → Pacing). While away, the Offline Shiba Bank pays 10 % of the recent income.

## UI (MVP)

Look and usability follow successful Roblox tycoons: few buttons on screen, big and chunky.

- HUD (uncluttered), top centre: square **menu** button (list icon) + green **clipboard** button (MANAGE) + dark bar
  with the Bonk Dollars symbol and counter in big green text, abbreviated (`Format.Abbreviate`: "324.316 quadrillion", counts up).
  - Menu button opens a small list: SHOP, GIFTS, QUESTS, SPIN, INDEX, SETTINGS (ADMIN for admins). A menu that does
    not exist yet says "coming soon".
  - MANAGE: with the Manage pass the upgrade menu opens anywhere; without it the shop opens on the POWERS tab to
    buy it (upgrades are normally bought at the stands on the island).
  - Red "!" badges on the menu button and its entries (and on MANAGE) when something can be claimed or bought;
    hidden when Settings → "Show "New" Hints" is off.
  - Also: running boosts (pill under the bar), Bonk Rain button (right), short messages (bottom centre). Bottom
    centre is kept free for the big round yellow upgrade button. The Roblox player list shows cash (leaderstats).
- Menus: one open at a time, built in code (`client/UI/Widgets`), shared look (`client/UI/Theme`): black inside a
  thick studded border (green; grey for Settings), big white outlined title, red square X over the top-right corner,
  chunky buttons and tabs, yellow price pills with a coin (Robux) or the Bonk Dollars symbol.
- Settings: Volume sliders Master / Music / Effects (Master only on this device), Gameplay "Show "New" Hints".
  Music, Effects and Hints are saved (`state.Settings`, `SaveSettings`).
- Icons: `assets/ui/*.png` (see its README), ids in `shared/Config/Icons`; until uploaded, glyphs are shown.

## Saving

Per player (DataStore, key = UserId): the whole `Types.PlayerState` (Bonk Dollars as `BonkPoints`, total earned, levels, active Shibas, spins used today, boost end times, quests, login streak, playtime, trophies, Bonk Rains, first join, starter pack, passes, handled receipts). Loaded on join, saved on leave, every 60 s, and on server shutdown.

## Scope of the first playable version (MVP)

Must have (= "Prototype Scope – Required" from the concept):
- One player island
- One NPC shooter
- One projectile type
- Projectile physically travels toward island
- Player can move
- Collision with player awards Bonk Dollars
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
- Physical shop area on the island for the Robux shop (upgrades have stands on the island, the shop is a UI menu)
- HUD stats beyond Bonk Dollars (Bonks/second, speed, projectile tier, shooter count)
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
| HUD | Bonk Dollars display | Marco |
| Saving | DataStore load/save | Marco |
| 3D models & visuals | models for islands, shooters, projectiles; UI art; effects | Marco |

## Monetisation

See **Shop (monetisation)** above. Before going live: create the passes and products on the Creator Hub, paste their ids
into `Config/Shop`, and answer the experience questionnaire honestly (the coin flip counts as chance-based content).

## Open questions

- Should a landing marker show where a projectile will land, or must players read the arc themselves? (MVP: no marker.)
- Should players be able to lower other upgrades (like active shooters) to control difficulty?
