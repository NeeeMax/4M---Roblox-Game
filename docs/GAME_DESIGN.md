# Game Design — GET BONKED

> Not decided yet = not in this file. Claude Code must not invent design decisions; if something is missing here, ask.
> All numbers below are **starting values**. They live in `src/shared/Config/` and are tuned in playtests.

## One-sentence pitch

NPCs lob silly objects at your personal floating island — run and jump **into** them to get bonked, earn Bonk Dollars, and buy upgrades that make it faster, bigger and more chaotic.

## Core loop

- **Every 5 seconds:** an NPC aims at a random spot on your island and fires. You read the arc, run there and try to take the hit (ideally running and jumping into it for a better hit quality).
- **Every 1–5 minutes:** spend Bonk Dollars on one of 5 upgrades.
- **Every session:** push upgrade levels higher; progress is saved.

## Onboarding / first minute

No tutorial text, no popups: the game shows the one next thing to do (`Config/Tutorial`).

1. **Spawn (0 s):** a brand-new player (or one after RESET EVERYTHING) spawns on their island at the new-player spawn,
   facing the centre, with exactly `EconomyConfig.StartingMoney` = the price of the second Shiba. Right in front: the
   glowing green **NEW SHIBA** pad with a pulsing highlight, a line from the feet to it and **"Step here!"** above it.
2. **Pad (~3 s):** stepping on it buys the second Shiba, which starts throwing within a few seconds.
3. **First catch (< 30 s):** nothing is affordable now, so **"Catch the stick!"** floats over the field (with a line
   there only if the player is far away). The very first caught stick pays `EconomyConfig.Bonk.FirstBonkMultiplier`
   (×10, **FIRST BONK!**, BonkService / BonkController) — the "wow" moment, and usually enough for the next purchase.
4. **Guided purchases:** whenever something is affordable, the line, the pulsing highlight and a hint of at most four
   words point at the cheapest affordable, unlocked thing ("Upgrade your Shibas!", "Buy better sticks!", "Run faster
   here!", "More Shibas here!" or "Step here!" on the pad …); with nothing affordable: "Get more money!" over the
   field. Each hint disappears as soon as its goal is done (the target changes).
5. **End:** after `Tutorial.GuidedPurchases` (6) purchases the guidance stops for good; the normal hints (NEW arrows,
   "You can afford …" popup, yellow button) take over. Settings → Hints off hides the guidance too.

- **Progress** is saved in `state.Tutorial.Step`: `TutorialService` (server) adds every rise of the sum of all upgrade
  levels, up to GuidedPurchases. Players with saves from before the rework start with Step 1000 (no tutorial); after a
  rebirth Step stays, so no tutorial and the normal spawn.
- A brand-new player = every upgrade level 0 and `Tutorial.Step == 0`. The save loads after the first spawn, so the
  server moves such a player to the new-player spawn once it is loaded (and again after an admin reset).

## Target players and session length

Casual Roblox players, roughly 8–14. Understandable in under 10 seconds without a tutorial. Target session: 15–30 minutes.

## World

| Thing | Value |
|-------|-------|
| Layout | a big **hub island** (radius 70) in the middle, **5 player islands** (radius 80) around it at 280 studs, each joined to the hub by a plank bridge with rails and lamps (tycoon style). Config: `Config/World` |
| Hub | stations between the bridges: Daily Spin, Coin Flip, Shop, Daily Quests, Top Bonkers leaderboard; Shiba statue with "GET BONKED" in the middle; how-to-play board in front of the hub spawn. Menus open via ProximityPrompt |
| Player island | grass island; in the middle the **field** (sand, radius 30, rope border with gaps toward the bridge and the basket, see Field look) where sticks land; Shibas stand on the island around it; trophies on lit pedestals behind the field; the Bonk Basket and the Bonk Intern once bought (see Automation); shop stalls, zone signs and a path on the outer ring (see Island layout); trees and flowers in a grove between the rebirth shrine and the bridge; owner name on a sign where the bridge arrives |
| Field look | `Config/FieldDecor`, built once per plot (`World/FieldDecor`, called by IslandService); everything visual only (no collisions, queries or touches), about 80 parts per island with placeholder props. **Paint** on a SurfaceGui on an invisible plate 0.04 above the sand (no stacked parts, so nothing flickers; the landing ring floats 0.16 above the island surface, over it): soft mint band 12–20, teal target lines at 6.2 / 12 / 20 / 27.6, orange edge curb at 29.1, teal bullseye (r 6.2) with a cream paw print, "GET BONKED" (bridge side) and "BONK ZONE" (far side) in orange, both upright for someone in the centre looking outward; darker and lighter sand patches and pebbles, seeded per plot. Colours are chosen so brown sticks and every landing-ring colour (warm, white, pink, gold) stand out from the paint. **Border** at radius 31: wooden posts with coloured ball caps (a soft PointLight in every 3rd cap), a sagging rope (Beam) and two pennants per span, arcs 15°–138° and 162°–345° (gaps: bridge, basket); mini signs BONK! / BONK ZONE / CATCH! on three posts facing the field. **Beach props** just outside the rope (PropService, placeholders until imported): sandcastle 55°, beach ball 98°, beach umbrella with towel 114°, bucket and spade 243°, bone toys 28° and 300°, grass tufts 78°, 255°, 327° (nothing in the bridge gap, at the basket/intern 150° or the trophy row 180° ± 25°). A faint sand glitter (ParticleEmitter) rises from the field. Preview: `assets/models/props/FieldDecor_preview.jpg` |
| Island layout | themed zones on the outer ring (`Config/Stations`, checked by `lune run docs/economy/layout_check`, details in `docs/economy/LAYOUT.md`). Angles clockwise from the bridge, stalls at radius 74 facing the field, a wooden zone sign behind each zone (radius 78, board above the stall billboards, title in the zone colour): **Speed Gym** Move Speed 30°; **Shiba Shop** Shiba Tier 62°, More Shibas 118° (the new-player spawn at 90° is between them); **Throwables** Projectile Tier 150°; **Automation** Bonk Basket 185°, Bonk Intern 220°; **Rebirth** shrine 270°. Walking clockwise from the spawn = later in the game. A sandy cobblestone path (radius 70, 4 wide, visual only, no collisions) runs from the bridge clockwise to the rebirth shrine; stalls stand ≥ 30 studs apart, outside the Shibas' reach (radius 67), trees ≥ 10 studs from any stall, sign, spawn or path |
| Islands | one per player, assigned on join (first free plot), freed on leave; more than 5 players = the extra ones stay on the hub. **Max Players must be 5** (Creator Hub → Configure → Places) |
| Target area | disc radius 28 inside the field; bounces can continue anywhere on the island |
| Player spawn | own island centre, facing the hub (hub spawn in front of the how-to board if no island). Brand-new players (nothing bought, tutorial not started) spawn at `Config/Stations → NewPlayerSpawn` (90° right of the bridge, radius 72) facing the island centre, the NEW SHIBA pad right in front of them (see Onboarding) |
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

Projectile tiers (upgrade `ProjectileTier`): **Stick** (BaseReward 10) → **Newspaper** (13) → **Baguette** (16) → **Rolling Pin** (20) → **Baseball Bat** (25) → **Giant Bone** (32) → **Squeaky Hammer** (40) → **BONK Sign** (50) → **Neon Stick** (63) → **Legendary Stick** (80). They fly the same; look, reward and the impact burst on a catch differ (Feedback). Models `ReplicatedStorage/Assets/Stick`, `Bone`, `GoldenStick`, `DiamondStick`; a missing model uses the next lower tier's model, tiers above Stick draw a trail in their colour, no model at all = coloured sphere. Hits use an invisible sphere of the projectile's diameter; the model is scaled so its longest side equals that diameter and spins in flight.

| Field | Bonk Stick |
|-------|------|
| Diameter | 3 studs |
| Base launch speed | 36 studs/s |
| BaseReward | 10 Bonk Dollars |

**Flight (visible arc):** launched at a fixed 45° angle toward the target point. Per projectile, gravity is set (with a `VectorForce`) to `g = v² / d` (v = launch speed, d = horizontal distance) so it lands exactly on the target. Every shot has the same readable arc shape (apex = d / 4); higher speed only shortens the flight time. At base speed a 60-stud shot flies 2.4 s.

**Bounces:** after landing it bounces **twice**: each bounce keeps 50 % of the vertical and 70 % of the horizontal speed (at base speed and a 60-stud shot: first bounce ≈ 3.7 studs high, second ≈ 1 stud; shorter shots have higher gravity and lower bounces). Then it makes **two small settling hops** of fixed height (0.7 and 0.3 studs, never higher than the hop before) keeping 45 % of the horizontal speed each, so the landing is visible whatever the shot's gravity, and comes to rest. While hopping, the model turns to lie flat along its direction of travel, and near the ground it is drawn with its lowest point on the ground (the hit sphere centre stays one radius above the ground). The whole path is computed when the shot is planned (`src/shared/Util/ProjectilePath.luau`, `Build`); every client draws the projectile along it (`docs/decisions/0004`). A bounce that leaves the island makes it fall off the edge. Tuning: `Gameplay.Projectiles` `Bounces`, `BounceRestitution`, `BounceFriction`, `SettleHopHeights`, `SettleFriction`, `LandingFadeTime`, `CollectableWhileFading`.

**Landing ring:** the owner's client draws a ring on the ground at the first landing point (`ProjectilePath.GetFirstLandingPosition`), in the tier colour, shrinking until the landing and gold during the Perfect window; it disappears at the landing or when the projectile is caught (details under Hits → Catch quality). Other players' projectiles get no ring.

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
Reward = floor(StickValue × QualityMult × HeadMult × ComboMult × FirstBonkMult), at least 1

StickValue    = RewardService.GetStickValue: projectile BaseReward × Shiba tier RewardMultiplier × rebirth
                × golden (5) × 2× boost × passes (2× Bonk Dollars, VIP) × server events
QualityMult   = catch quality (below): 1 / 2 / 4   (EconomyConfig.Bonk.QualityMultipliers)
HeadMult      = 2 if the projectile touched the head, else 1
ComboMult     = 1 + 0.1 × (combo − 1), at most 3
FirstBonkMult = 10 for a new player's very first paid hit (EconomyConfig.Bonk.FirstBonkMultiplier), else 1
```

All multipliers live in `Config/EconomyConfig` (Bonk section).

### Catch quality — when you catch it

Decided by the server from **when** the stick was caught, compared with the moment it first touches the ground (the end of
its flight, `ProjectilePath.GetFirstLandingTime`). See `docs/decisions/0005-catch-timing-quality.md`.

| Quality | Popup | When | Multiplier |
|---------|-------|------|-----------|
| Normal | `BONK` | after it touched the ground (bounces, settling hops) | 1× |
| Good | `AIR BONK!` | in the air | 2× |
| Perfect | `PERFECT BONK!!` | in the air, at most `Gameplay.Hits.PerfectWindow` (0.25 s) before it lands | 4× |

- **Landing ring:** for each of your own projectiles a ring on the ground shows where it will first land. It shrinks from
  10 studs to the pickup size as the landing approaches and turns gold (and thicker) during the Perfect window. Standing
  inside the ring when it closes = PERFECT BONK; catching it earlier (a few studs in front, or jumping into it) = AIR BONK;
  arriving after it touched the ground = BONK.
- **Catch moment (server):** the first time the planned path came within projectile radius + pickup padding + 1 stud of
  the character's body line (3 studs below the root part up to the head), searched only in the last
  `ping + 0.12 s` (at most 0.6 s) before the report arrived (the client reports as soon as it sees the touch; without
  this bound a player reaching the landing spot late would get Perfect, because the descent passed through it). If the
  path never came that close (network delay), the time of its closest approach to the root in that window.
- Why 0.25 s: a stick comes down at ≈ 25 studs/s, so a standing player gets it ≈ 0.15 s (on the landing spot) to
  ≈ 0.3 s (a few studs in front) before it lands; earlier catches need a jump. Tune `PerfectWindow` in `Config/Gameplay`.
- **Magnet** (Auto-Catch) catches always pay Normal.
- **First bonk:** a new player's first paid hit (`Tutorial.FirstBonkDone` false in the save) pays ×10, sets the flag and
  shows a `FIRST BONK! ×10` splash (`BonkHit` argument `firstBonk`).

### Head hits and combo

- **Head hit (×2):** the client reports whether the projectile touched the head; the server accepts it if the path also
  passed within projectile radius + 2 (pickup padding) + 4 studs of the server-side head.
- **Combo:** every hit within the combo window of the previous hit adds 0.1 to the multiplier (max ×3 at 21 hits).
  Window = 2 s + 1.5 × time between two shots (interval / active shooters), so it stays fair with more or faster shooters.
  The HUD shows `COMBO xN ×M` with a bar that runs out when the window ends, plus a tier name in its colour from
  ×1.5 `ON FIRE`, ×2 `BONKTASTIC`, ×3 `MAX BONK` (`Gameplay.Bonk.ComboTiers`); the meter punches when a new tier is reached.

## Feedback (client)

All tunable in `Config/Gameplay` → `Bonk` (per quality: `Bonk.Qualities`).

| | BONK (Normal) | AIR BONK (Good) | PERFECT BONK (Perfect) |
|--|--|--|--|
| Popup (1.0 s, rises) | `BONK +X`, white | `AIR BONK! +X`, green, ×1.2 size | `PERFECT BONK!! +X`, gold, ×1.6 size, pops in big and bounces |
| Sound pitch | 1.0 | 1.08 | 1.18 |
| Coins from the character | 4 | 8 | 16 |
| Stars from the head | 6 | 10 | 18 |
| Camera shake | — | tiny | strong (× 1.3 on head hits and golden sticks) |

- Head hits say `HEADBONK` instead of `BONK` (`PERFECT HEADBONK!! +X`); golden sticks add `GOLDEN ` and are gold.
- One bonk sound (a custom cartoon "bonk", ≈ 0.9 s, `Gameplay.Bonk.SoundId`). Every hit plays its own copy, so quick hits overlap.
- **Impact burst** where the projectile hit (hand catches), in the projectile's tier colour (gold for golden ones),
  8 + 3 per tier particles and bigger per tier; some throwables burst differently (`Bonk.Impact.Textures`: smoke for
  the newspaper, baguette and bone, fire for the BONK sign and the Legendary Stick).
- **First bonk:** `FIRST BONK! ×10` big in the middle of the screen for 2.5 s.
- **Landing ring** for your own projectiles (see Catch quality; `Gameplay.LandingRing`).

## Upgrades

Prices are **derived** from a target pace in `Config/EconomyConfig` (single source of truth, see **Pacing** and
`docs/economy/BALANCING.md`); `Config/Upgrades` only has names, effects and colours. Six upgrades (projectile size and
fire rate were removed on 2026-09-24: projectiles always have the same size, the fire rate comes with the Shiba tier).

| Id | Menu name | Effect per level | Level 0 | Max level | Unlocks with |
|----|-----------|-----------------|---------|-----------|--------------|
| `Shooters` | More Shibas | +1 Shiba | 1 | 7 (8 Shibas; 9 with the pass) | start (the first purchase, B$ 10) |
| `ShooterTier` | Shiba Tier | all Shibas evolve: new model/edition, faster throws, ×8.08 dollars | Shiba | 29 (30 Shibas) | start |
| `ProjectileTier` | Projectile Tier | next projectile (×2.5 BaseReward) | Stick | 9 | Shades Shiba |
| `MoveSpeed` | Move Speed | WalkSpeed +3 | 16 | 10 (46) | Shades Shiba |
| `Basket` | Bonk Basket | catches missed sticks, sets the offline hours | none | 6 | Gold Shiba |
| `Intern` | Bonk Intern | a helper who catches missed sticks (Bonk Intern … Bonk CEO) | none | 6 | Giant Shiba |

- **Unlocks** come from `EconomyConfig.UnlockAtShibaTier` (derived from the Route): a locked upgrade shows "Unlocks with
  <Shiba>" (menu, stand) and the server refuses it (`UpgradeService.TryPurchase`).
- **Prices** (examples; the simulation prints all of them): Shibas 38 → 2K → 36K → 340K → … → 570B (Shiba 10) →
  78Sx (Shiba 20) → **1Dc = 1e33** (Shiba 30). More Shibas 10 … 190T, Move Speed 75 … 1.5Oc, Basket 450M … 3.4No,
  Intern 74B … 18No, Projectile Tier 647 … 79Oc.

Shiba tiers (`EconomyConfig.Shibas`, used by `Config/Gameplay → Shooters.Tiers`): 30 = the ten models (Shiba, Shades,
Buff, Chef, Police, Ninja, Gold, Galaxy, Giant, Cheems God), then the same ten as **Shiny** and **Mythic** editions
(same model, outline and aura in the edition colour). Throw interval 5.0 s → 1.2 s (geometric), dollars ×8.08 per
tier (×1 → ×2e26, solved so the last Shiba costs 1e33).

- MoveSpeed exists so the player can **reach impact points in time** (not to dodge). It also raises the achievable hit quality.
- **Active Shibas:** buying adds a Shiba; the "More Shibas" card sets how many are active (1 … owned) for free.
- Purchases are validated on the server: known upgrade id, below max level, enough Bonk Dollars, max 5 requests/s.
- **Upgrade stands** (main way to buy, tycoon style, `Config/Stations`): on every player island one market-stall stand
  per upgrade (`Prop_UpgradeStand_<UpgradeId>`, part-built until a model exists, colour from `Config/Upgrades`) on the
  outer ring in its themed zone, facing the field (World → Island layout): Move Speed, Shiba Tier, More Shibas,
  Projectile Tier, Bonk Basket, Bonk Intern.
  - **Locked stands:** a stand whose upgrade unlocks later (`EconomyConfig.UnlockAtShibaTier`, e.g. Basket and Intern)
    shows a grey shutter with a gold padlock and has no prompts until the player's Shiba Tier reaches that level.
  - **Rebirth shrine** (`Prop_RebirthShrine`, purple stone altar under a golden arch with a glowing orb) at 270°: hold
    **E "Rebirth"** for 3 s to rebirth (`RebirthService`). The prompt appears (and the orb lights up) only once the
    player can rebirth; only the island owner can use it.
  Above each stand floats a billboard: upgrade name, current value (tier name in its colour / number), level badge
  `xN`, level bar, a big UPGRADE button look (green when affordable, grey when not, gold MAXED at the top) with the
  cost (green / grey) and an **E** key hint. Only the island owner can use their stands and sees the billboards.
  - **E "Upgrade"** buys one level. With the **Stack Upgrade** pass one press buys as many levels as affordable, up to 10
    (the button then says `UPGRADE ×N` with the total cost).
  - **F "Buy with R$"** buys the next level with Robux (products `Instant<UpgradeId>` in `Config/Shop`).
  - **More Shibas** also has a glowing green **NEW SHIBA** pad with its cost on the Shiba ring, where the next Shiba will
    stand (of the new ring's spots, the one farthest from the Shibas standing now). Stepping on it buys the Shiba
    (2 s cooldown). The pad disappears at the max.
  - Every stand billboard (and the NEW SHIBA pad) also has a **money bar**: your Bonk Dollars / the next level's cost
    in %, gold while saving up, green **READY!** once affordable ("almost there" pull).
  - **Locked stands** (`EconomyConfig.UnlockAtShibaTier`: the Shiba tier at which the upgrade comes up in the Route;
    the server's `Locked` attribute on the anchor wins when set) look grey: button **LOCKED**, "unlocks with
    <Shiba name>" instead of the cost, no money bar, no hints.
  - **Next Shiba** next to the Shiba Tier stand: the next Shiba's model as a slowly turning black silhouette (outline in
    its colour), with "NEXT: ???" (its name, in its colour, once affordable), its price and a money bar.
  - **REBIRTH shrine** billboard: REBIRTH, rebirth count and current income multiplier, then either "Needs <Shiba>"
    (`EconomyConfig.Rebirth.MinShibaTier`) with a Shiba progress bar, or "Hold E: ×N income forever" (N = the
    multiplier after the next rebirth).
  - **Hints** (off with Settings → Hints): a bouncing **NEW** arrow over every stand whose next level you can afford, and
    once per upgrade level a popup "You can afford a new upgrade! [SHOW ME]" (only when you are not already at that
    stand; several newly affordable upgrades give one popup, for the cheapest; never during the guided tutorial, see
    Onboarding). SHOW ME draws a glowing line from your character to the stand for 8 s (or until you arrive).
  - The big round **yellow arrow button** at the bottom centre does the same as SHOW ME for the cheapest affordable
    upgrade ("Nothing affordable yet" otherwise). Locked stands never count as affordable.
- **Run Faster** pass: WalkSpeed ×1.5 on top of Move Speed.

### Pacing

Goal: the first purchase right away, a quick buy every few seconds at the start, a **minute rhythm from around the
9th Shiba**, never a wall, and a whole first run (30 Shibas, 67 purchases) in **60–90 min**; every purchase pays for
itself within ~15 min. Full model, tables and how to retune: `docs/economy/BALANCING.md`
(`lune run docs/economy/simulate.luau`).

```
target wait T(n) = 200 − 196 · e^(−n / 50) s   (4 s for the first purchase → 2.5 min for the last)
price(n)         = Baseline income before purchase n × T(n) × PriceShare(upgrade)
Baseline income  = stick value × (caught/s × 2 + intern catches × payout + basket catches × payout)
caught/s         = min(sticks/s × (60 % + 3 % per Move Speed), 1 + 0.1 per Move Speed)
```

A player who always buys the cheapest affordable upgrade (run 1, no rebirth, no passes):

| Shiba | 1 | 2 | 5 | 9 | 10 | 20 | 21 (rebirth) | 30 (1e33) |
|-------|---|---|---|---|----|----|--------------|-----------|
| play time | start | 8 s | 1.7 min | 7.5 min | 9.1 min | 36.6 min | 39.0 min | 66.9 min |
| wait for it | — | 8 s | 29 s | 64 s | 71 s | 2.1 min | 2.1 min | 2.5 min |

Between two Shibas come quick side buys (More Shibas, Move Speed, Basket, Intern: 2–35 s each) and every few Shibas a
projectile tier (as long as a Shiba). Active play earns ~3.7× the idle (AFK) income once the intern is hired and ~2×
at the end of the run.

Robux speeds this up without selling Bonk Dollars: 2× Dollars (pass or 30 min boost) halves every wait, 2× Fire Rate
nearly does, and the instant upgrades skip one level.
- Upgrade menu: one card per upgrade with level badge, current → next value (tier names in their colours), what the next
  level gives, one dot per level (Shiba Tier: 29 small dots), buy button (green when affordable, "LOCKED" with
  "Unlocks with <Shiba>" before its Shiba). At the bottom a **REBIRTH** card: rebirths and income multiplier, "Needs
  the Mythic Shiba (Shiba 21) · next: income ×N", READY when it can be done (at the shrine on the island). The UPGRADES
  button shows "!" when something unlocked is affordable.

### Rebirth

Once you own the **Mythic Shiba (Shiba 21)** you can rebirth at the rebirth shrine on your island
(`RebirthService.TryRebirth`, `EconomyConfig.Rebirth`): Bonk Dollars back to the start amount, all six upgrades back
to 0; your income is multiplied by **1 + rebirths** for good (×2, ×3 …, `RewardService.GetRebirthMultiplier`). Kept:
passes, trophies, Shiba-Index, quests, streaks, boosts, Bonk Rains, pending Shiba Bank earnings, settings; the
measured income rates are reset (so a rebirth can't cash the old run's income offline). Run 2 takes about half as
long (Shiba 21 after ~20 min), run 3 a third. The HUD shows a small "REBIRTH n · ×m INCOME" pill after the first one.

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
  xN combo, N PERFECT BONKS, win coin flips, spin the wheel, buy upgrades. Claim for 20–120 bonks. QUESTS button shows "!" when claimable.
- **Leaderboard:** "Bonk Dollars" in the Roblox player list (short text, "1.5Dc": a StringValue, since amounts pass
  the 9.2e18 limit of an IntValue; the list sorts it as text); the TOP BONKERS board ranks the top 10 by total Bonk
  Dollars ever earned (all servers, OrderedDataStore `TotalEarned_v2`, refreshed every minute; this server only when
  DataStores are unavailable). The store keeps `floor(log10(total + 1) × 1e14)` (an OrderedDataStore only holds whole
  numbers below 2^63; the log keeps the order and ~14 digits, up to 1e90) and the board decodes it for display. The old
  `TotalEarned_v1` board starts over. Admin gifts and coin-flip stakes coming back don't count, only real earnings.
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

A collection book (INDEX menu, `Config/Index`) with one entry per Shiba tier (30: the ten originals, then the Shiny
and Mythic editions), projectile tier (10), the golden stick and each trophy (10): 51 entries today, new tiers and
trophies are added automatically. Entry ids are saved: the ten original Shibas keep `Shiba_<Model>`, editions are
`Shiba_<Edition><Model>` (e.g. `Shiba_ShinyShiba`). An entry is **found** when you first reach it: Shiba / projectile
tier bought (or skipped past), first golden stick caught, trophy owned; a rebirth never un-finds anything. Unfound
entries show as a dark "???" silhouette. Each found entry pays a one-time discovery reward you claim on its card (in
bonks, see Hub features): Shibas 20 + 10 per tier (20 … 310), projectiles 15 + 5 per tier, golden stick 50, trophies
by rarity (Common 25, Rare 50, Epic 100, Legendary 200, Exclusive 300). Finding all entries unlocks a completion bonus
of 1,000 bonks. A bar on top shows the progress ("12/51 found").
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
| Product | Magnet 15 min (`Magnet15`) | 49 | timed boost `Magnet` (it used to be the Auto-Catch pass): every 0.25 s, sticks within 10 studs of the character are collected as a Normal bonk (no head bonus, combo counts); a small magnet circles the player while it runs, the HUD shows `MAGNET mm:ss`. Admin: Boosts → Magnet 5m / Clear. AutoCatchService, MagnetController |
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

Trophies stand on your island for everyone to see. Bought with Bonk Dollars (`EconomyConfig.TrophyThresholds`, each
about the price of the Shiba you buy around then): Wooden 1e4, Bronze 1e8, Silver 1e14, Golden 1e22, Galaxy 1e30,
plus exclusive ones (Starter, 7-Day Streak, VIP, Diamond, Rainbow).
Receipts are granted exactly once (handled purchase ids are saved); pass ownership is checked with Roblox on every join.

## Automation

Two upgrades catch the sticks the player misses, for a share of their value (idle income, also the base of the
offline earnings). Bought at their stands (`Basket`, `Intern` in `Config/Upgrades`, levels 0–6; level 0 = none).
**All numbers** (catch chance, payout, walk speed, names) live in `Config/EconomyConfig → Automation`, entry n = level
n; only look and tuning (position, colours, timings, effects) live in `Config/Automation`. The server decides and pays
everything (`AutomationService`); clients only draw (`AutomationController`, remote `AutomationCatch`).

Stick value = `RewardService.GetStickValue` (projectile BaseReward × Shiba tier × rebirth × golden × passes × 2× boost
× server events), i.e. a Normal bonk without head bonus or combo. Automation pays `floor(stick value × Payout[level])`,
at least 1, through `EconomyService.AddAutomationPoints` (counted as earned; sampled separately for the offline bank).
It gives no combo, quest progress or Shiba-Index discoveries. Both helpers only work while the owner is on their
island (like the Shibas). Order: the player first, then the intern, then the basket.

**Bonk Basket** (`Basket` ≥ 1)
- A big wicker basket (`Prop_Basket`, part-built until a model exists: woven brown body, dark bands and stakes, a rim
  in the level colour, a handle) just outside the field border, 150° clockwise from the bridge direction, facing the
  field. It grows a little per level (3.6 studs + 0.3 per level) and its rim changes colour.
- When a stick's collectable window ends and nobody caught it, the basket rolls `CatchChance[level]` once (0.2 s later,
  so a hand catch reported right at the end still wins). On success it pays `Payout[level]` × stick value.
- Look: the stick flies in an arc from where it lay into the basket, sparkles pop at the opening, "+B$ X" rises above
  the basket (only the owner sees it).

**Bonk Intern** (`Intern` ≥ 1)
- A blocky NPC (R6 proportions, built from parts) on the island with a name tag (`Names[level]`: Bonk Intern,
  Hard-Hat Intern, Junior Bonker, Senior Bonker, Bonk Manager, Bonk CEO). Shirt colour per level, yellow hard hat from
  level 2, long sleeves and a red tie from level 5, the CEO wears a dark suit, a gold tie and a crown.
- Every 0.2 s it picks a target: an unpaid stick whose first landing point (later: where it is now) it can reach at
  `WalkSpeed[level]` before the stick stops being collectable, inside radius 36 (it never leaves the Shiba ring),
  preferring sticks far from the player. **The player gets first dibs:** sticks within 12 studs of the character are
  left alone. Without a target it waits at the field's edge on the basket's side.
- A stick passing within its radius + 3 studs of the intern's body bonks it: `Payout[level]` × stick value, then it
  stands dazed for 0.9 s.
- It walks with physics movers owned by the server (no collisions: players walk through it and it can't be pushed);
  if it ever leaves the island it is put back. It is removed at level 0 (e.g. after a rebirth) or when the player
  leaves, and rebuilt when the level changes.
- Look: every client swings its arms and legs while it walks. On a bonk (owner only): it tips over and wobbles back
  up with flailing arms, stars burst from its head, the stick bounces off and fades, a speech bubble says a random
  line ("OW!", "Worth it!", "My pension!", "Is this in my contract?" …) and "+B$ X" rises.

## Offline Shiba Bank

While the player is away, their basket and intern keep earning (OfflineService; numbers in `EconomyConfig →
Automation`, sampling in `Config/Economy → OfflineBank`):

- **Income rates:** every 60 s of play two rates are smoothed (`rate += 0.3 × (sample − rate)`, the first sample sets
  it): `Bank.IncomePerMinute` = what the player earned themselves (hits, spin, quests, gifts, coin-flip wins; not
  admin gifts or the offline payout) and `Bank.AutomationPerMinute` = what the basket and intern earned
  (`EconomyService.AddAutomationPoints`). Each sample counts at most 8 normal bonks per Shiba throw, so a big coin-flip
  win can't inflate a rate. A rebirth resets both rates.
- **Last seen:** every save (leave, autosave, shutdown) stamps `Bank.LastSeenAt`.
- **On join:** time away = now − LastSeenAt, only if at least 60 s, capped at the basket's offline hours (Basket level
  1…6: 2 / 3 / 4 / 5 / 6 / 8 h; no basket: 1 h).
  `Pending += minutes away × (1 × AutomationPerMinute + 5 % × IncomePerMinute)`, then the "WELCOME BACK!" popup shows
  the time away and the amount.
- **OKAY** pays Pending (counts for the leaderboard). **x2 DOUBLE IT! (R$ 39)** opens the "Double Offline Earnings" product;
  when Roblox grants it, 2× Pending is paid. Unclaimed earnings stay pending (and add up) until claimed.
- Example: automation 1,000/min and own income 4,000/min, Basket level 2, away 5 h → capped at 3 h = 180 min ×
  (1,000 + 200) = 216,000 (432,000 doubled).

## Admin (testing)

- Admins get an **ADMIN** button (left) with: +1K / +1M / +1B / +1T … +1Dc points (every ×1000 up to 1e33,
  `Admin.PointAmounts`), set points to 0; each upgrade −/+ and MAX ALL (ignores the Shiba unlocks); rebirth now (no
  Shiba needed), +1 rebirth (only the multiplier), reset rebirths, with the current count and multiplier;
  reset daily spin, new quests, finish quests; 2× Dollars / 2× fire rate boost (10 min), clear boosts; teleport to hub / own
  island, all Shibas fire now; toggle each pass, +1 Bonk Rain, start a rain, all trophies, unlock gifts, show the
  starter offer again; RESET EVERYTHING (second click confirms; keeps the leaderboard total and Robux purchases).
- Admins: everyone in Studio playtests, the experience owner, and the UserIds in `src/shared/Config/Admin.luau`.
- The server checks admin rights on every request (`AdminCommand`, `AdminService`); the client check only hides the button.

## Economy

- Currency: **Bonk Dollars** (whole numbers, up to 1e33 and beyond: a double, written short from 1e6 with
  `Format.Money` / `Format.Short`: K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc …). Earned by hits, automation (basket,
  intern), daily spin, quests, coin flips and the Shiba Bank. A new player starts with **B$ 10** =
  `EconomyConfig.StartingMoney`, exactly the price of the first purchase (the second Shiba on the NEW SHIBA pad).
  Every price, income and multiplier lives in `Config/EconomyConfig` (see Upgrades → Pacing, `docs/economy/BALANCING.md`).
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
- Pacing target (for tuning): first purchase right away, minute rhythm from around the 9th Shiba, a whole first run
  (Shiba 30, 1e33) in ~67 min, no purchase with a payback over ~15 min (see Upgrades → Pacing). While away, the
  Offline Shiba Bank pays the automation's income (+5 % of your own) for up to the basket's offline hours.

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

Per player (DataStore `PlayerData_v1`, key = UserId): the whole `Types.PlayerState` (Bonk Dollars as `BonkPoints`, total earned, levels of all six upgrades, active Shibas, spins used today, boost end times, quests, login streak, playtime, trophies, Bonk Rains, first join, starter pack, passes, handled receipts, Shiba Bank, obby, Shiba-Index, settings, rebirths, tutorial). Loaded on join, saved on leave, every 60 s, and on server shutdown; a rebirth saves right away.

- **Save version 2** (economy rework): adds `Rebirths`, `Tutorial`, `Bank.AutomationPerMinute` and the `Basket` /
  `Intern` levels. Version-1 saves load unchanged (money, levels, everything); their players skip the tutorial.
  Old Bonk Dollar amounts stay as they are (tiny next to the new prices, which is fine: they start the new curve).
- Big numbers are plain doubles in the save (a DataStore holds them fine); only the leaderboard's OrderedDataStore
  needs the log encoding (see Hub features → Leaderboard).

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
