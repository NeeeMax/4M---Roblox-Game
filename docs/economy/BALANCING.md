# Economy balancing (v2)

Everything here comes from `src/shared/Config/EconomyConfig.luau` and the simulation that loads it:

```
lune run docs/economy/simulate.luau          # from the repo root; prints markdown
```

`docs/economy/current_economy.luau` is the snapshot of the economy before the rework (for comparison).

## Targets and where we are

| Target | Result (run 1) |
|--------|----------------|
| first purchase < 5 s | **0 s**: a new player starts with B$ 10 = the price of the 2nd Shiba (NEW SHIBA pad) |
| minute rhythm (waits ≥ 60 s) from around Shiba 8–12 | waits pass 60 s **while owning the 8th Shiba** (6.4 min in; the 9th Shiba is a 63 s wait) |
| last Shiba costs 1e33 | **B$ 1Dc** exactly (`FINAL_SHIBA_COST`) |
| no payback > ~15 min (automation judged by idle payback) | longest: **15.0 min** (Intern 6, idle); everything else ≤ 14.4 min |
| cheapest-first order stays close to the Route | **0 of 67** purchases out of Route order |
| first run 60–90 min | **65.7 min** for all 67 purchases |
| active 1.5–3× idle once automation is unlocked | **3.8×** right after the intern, **3.5×** at Shiba 14, **2.9×** at Shiba 16, **2.6×** at Shiba 25, **2.4×** at the end |
| stick density: a player can follow every stick | at most **1.4 sticks/s** per island (2.1 in a Stick Storm), was up to 8.3/s (33/s boosted in a storm) |

Time to Shiba n (Shiba 1 is owned from the start; Shiba n = ShooterTier level n − 1):

| Shiba | 1 | 2 | 5 | 10 | 20 | 21 (rebirth) | 30 |
|-------|---|---|---|----|----|--------------|----|
| play time | 0 | 8 s | 1.7 min | 9.0 min | 35.9 min | 38.2 min | 65.7 min |

## Stick density cap

`EconomyConfig.StickDensity.MaxThrowsPerSecond = 1.4` (mirrored as `Gameplay.Shooters.MaxThrowsPerSecond`). A ring of
Shibas never throws more than 1.4 sticks per second; above that, every stick carries a **ValueMultiplier** = natural ÷
capped rate (`EconomyConfig.ThrowRate`). Income per second is exactly the same as without the cap, it just arrives in
fewer, more valuable sticks (shown on the stick as "×N"). Stick Storm raises the cap ×1.5 for its 90 s.

Why 1.4: sticks land ~25 studs apart and a player at WalkSpeed 16 reaches about one per second (two at max Move Speed).
A stick flies ~1.5 s plus bounces, so 1.4/s keeps ~4–5 sticks in the air: few enough to follow each one. Much lower and
the early mid game (3–4 Shibas) would already be capped and feel slow; above ~1.8 the late game gets chaotic again.

| situation | FireInterval | sticks/s without cap | sticks/s thrown | value per stick |
|-----------|--------------|----------------------|-----------------|-----------------|
| Shiba 5, 3 Shibas | 4.1 s | 0.73 | 0.73 | ×1.0 |
| Shiba 8, 5 Shibas | 3.5 s | 1.43 | 1.40 | ×1.0 |
| Shiba 10, 6 Shibas | 3.2 s | 1.88 | 1.40 | ×1.3 |
| Shiba 15, 8 Shibas | 2.5 s | 3.20 | 1.40 | ×2.3 |
| Shiba 30, 8 Shibas | 1.2 s | 6.67 | 1.40 | ×4.8 |
| Shiba 30, 10 Shibas (Shiba Slots pass) | 1.2 s | 8.33 | 1.40 | ×6.0 |
| … + 2× Fire Rate boost | 1.2 s | 16.67 | 1.40 | ×11.9 |
| … + Stick Storm (cap ×1.5) | 1.2 s | 33.33 | 2.10 | ×15.9 |

What it changed in the model: before, the player's catches were capped per second (~1–2/s) while up to 6.7 sticks/s
flew, so most sticks at the top fed the automation and extra Shibas / Move Speed paid mostly through it. With the cap
the player can reach most sticks, so:

- **Move Speed** now pays through catch quality: `ActiveBonusPerSpeedLevel = 0.05` (a faster player gets under more
  sticks before they land: AIR ×2 / PERFECT ×4 instead of Normal), on top of +3 % catch rate per level.
- **Intern** takes a share of what the player leaves (`CatchShare` 50 % → 80 %, like the player's own catch rate:
  60 % at WalkSpeed 16, +1 % per stud/s), at most `ExpectedCatchesPerSecond`. Without that it would take all ≤ 1.4
  sticks/s and the basket would get nothing.
- **Basket** rolls on the rest. Its levels step up in bigger increments (`CatchChance` 35 % → 100 %, `Payout` 45 % →
  100 %) and cost less (PriceShare 0.25 → 0.15); intern `Payout` 70 % → 100 %, PriceShare 0.15 → 0.12.

## The model

**Baseline player** (`EconomyConfig.BaselineIncome(levels)`), an average active player:

```
sticks/s   = min(Shibas / FireInterval(Shiba tier), 1.4)             (5.0 s → 1.2 s over the 30 Shibas; density cap)
stick value = projectile BaseReward × Shiba RewardMultiplier × (natural ÷ capped rate)
caught/s   = min(sticks/s × catch rate, max catches/s)
             catch rate     = 60 % + 3 % per Move Speed level, max 90 %
             max catches/s  = 1 + 0.1 per Move Speed level            (sticks land ~25 studs apart; rarely binds now)
missed/s   = sticks/s − caught/s  → intern first (CatchShare of it, up to ExpectedCatchesPerSecond),
             basket gets CatchChance of the rest
income/s   = stick value × (caught × ActiveBonus + intern × intern Payout + basket × basket Payout)
             ActiveBonus = 2 + 0.05 per Move Speed level
```

`ActiveBonus = 2` is the average of catch quality (AIR ×2, PERFECT ×4), head ×2 and combo. Idle (AFK) income is the
same with caught = 0. Rebirth, passes, boosts, golden sticks and events are left out (they only make it faster).

**Prices are derived, not typed.** Every purchase of a run is in the **Route** (`ROUTE_SPECS`: each upgrade's levels
spread between From and To). Purchase n has a target wait

```
T(n) = MaxSeconds − (MaxSeconds − MinSeconds) · e^(−n / Knee)      MinSeconds 4, MaxSeconds 200, Knee 50
price(n) = income right before purchase n × T(n) × PriceShare(upgrade)
```

With Knee 50 the curve is almost a straight line from 4 s to 2.5 min. The 30 Shiba reward multipliers grow by one
factor (**×7.87 per Shiba**), solved so the last Shiba costs exactly 1e33. Between two Shibas the purchases are
sorted cheapest-first (what a player who buys the cheapest thing does anyway), so each price is based on the income
the player really has when buying it.

**Unlocks** (`UnlockAtShibaTier`, derived from the Route): Projectile Tier and Move Speed with the Shades Shiba
(tier 1, 8 s in), Bonk Basket with the Cowboy Shiba (tier 6, ~4 min), Bonk Intern with the Ninja Shiba (tier 8,
~7.5 min). Locked stands/cards say "Unlocks with …" and the server refuses them.

## Target curve vs the actual waits

The greedy player waits almost exactly T(n) for Shibas and projectiles (price share 1); the cheap items in between
(More Shibas, Move Speed, Basket, Intern) are quick buys of 2–25 s. Selected purchases:

| # | purchase | T(n) | actual wait | play time |
|---|----------|------|-------------|-----------|
| 2 | Shiba 2 | 7.9 s | 7.9 s | 8 s |
| 8 | Shiba 5 | 29.6 s | 30.0 s | 1.7 min |
| 17 | Shiba 8 | 57.7 s | 57.5 s | 5.4 min |
| 18 | Projectile Tier 3 | 60.5 s | 61.1 s | 6.4 min |
| 19 | Shiba 9 | 63.3 s | 63.2 s | 7.5 min |
| 20 | Intern 1 (share 0.12) | 66.0 s | 8.0 s | 7.6 min |
| 22 | Shiba 10 | 71.2 s | 71.9 s | 9.0 min |
| 36 | Shiba 15 | 1.7 min | 1.7 min | 21.1 min |
| 48 | Shiba 20 | 2.1 min | 2.1 min | 35.9 min |
| 67 | Shiba 30 | 2.5 min | 2.5 min | 65.7 min |

```
cumulative play time per Shiba (run 1, 50 chars = 65.7 min)
Shiba  1     0.0 s |
Shiba  2     7.9 s |
Shiba  3    44.7 s |#
Shiba  4    74.3 s |#
Shiba  5   1.7 min |#
Shiba  6   3.3 min |###
Shiba  7   4.0 min |###
Shiba  8   5.4 min |####
Shiba  9   7.5 min |######
Shiba 10   9.0 min |#######
Shiba 11  10.7 min |########
Shiba 12  13.7 min |##########
Shiba 13  15.7 min |############
Shiba 14  17.5 min |#############
Shiba 15  21.1 min |################
Shiba 16  23.1 min |##################
Shiba 17  25.1 min |###################
Shiba 18  29.2 min |######################
Shiba 19  31.1 min |########################
Shiba 20  35.9 min |###########################
Shiba 21  38.2 min |#############################
Shiba 22  40.7 min |###############################
Shiba 23  45.1 min |##################################
Shiba 24  47.6 min |####################################
Shiba 25  50.6 min |######################################
Shiba 26  55.2 min |##########################################
Shiba 27  57.6 min |############################################
Shiba 28  60.4 min |##############################################
Shiba 29  63.2 min |################################################
Shiba 30  65.7 min |##################################################
```

## Payback per item

Payback = price ÷ income gained (active). Automation is judged by what it adds while idle (its whole point).

| Upgrade | PriceShare | Payback in run 1 | Why that share |
|---------|------------|------------------|----------------|
| Shiba tier | 1 | 1–23 s | ×7.9 income each: the main progression, always the "big" buy |
| Projectile tier | 1 | 10 s – 1.5 min | ×2.5 stick value |
| More Shibas | 0.15 | 4 s – 1.6 min | cheap quick buys; with the density cap each extra Shiba adds its full share of value (bigger sticks) |
| Move Speed | 0.16 | 25 s – 8.9 min | +3 % catch rate and +0.05 catch bonus per level ≈ +4 % income |
| Bonk Basket | 0.15 | idle 54 s – 14.4 min (active up to 2.4 h: it only gets the few sticks you and the intern leave) | |
| Bonk Intern | 0.12 | idle 45 s – 15.0 min (active up to 2.5 h) | |

**Rule:** keep every PriceShare above ~1.2 / ShibaGrowth (≈ 0.15). A cheaper item placed right after a Shiba would
still be cheaper than that Shiba, get bought before it, and then pay for itself ×8 slower than planned. (The first
version of this tuning had Move Speed at 0.08 and got 30–40 min paybacks for exactly this reason; with the density cap
Move Speed at 0.11 did the same: 12 purchases out of order, 1.9 h paybacks.) The Intern at 0.12 is the exception: its
levels sit mid-segment and the simulation shows none of them out of order — re-check after moving its From / To.

## Idle vs active

| at purchase | Basket / Intern | active ÷ idle |
|-------------|-----------------|---------------|
| #15 (Shiba 7) | 1 / 0 | 9.1× |
| #20 (Shiba 9) | 1 / 1 | 3.8× |
| #25 (Shiba 11) | 1 / 1 | 4.0× |
| #35 (Shiba 14) | 2 / 2 | 3.5× |
| #40 (Shiba 16) | 3 / 3 | 2.9× |
| #50 (Shiba 21) | 4 / 4 | 2.7× |
| #60 (Shiba 25) | 5 / 5 | 2.6× |
| #65 (Shiba 28) | 6 / 6 | 2.4× |

Only the basket (before the intern) is weak on its own; with the intern the ratio sits in the 1.5–3× band from about
Shiba 16 on (3.5–4× before that, while intern and basket are at levels 1–2). The cap keeps the late game more active
than before (2.4× at the end instead of 1.7×): the player can now reach most sticks, so there is less overflow for
the helpers.

**Offline (Shiba Bank)**: per minute away = 1 × automation income/min + 5 % × own income/min, for at most the basket's
OfflineHours (2 → 8 h; 1 h without a basket). The samples it is built from already include the ValueMultiplier (the
basket and intern pay it). See `docs/GAME_DESIGN.md → Offline Shiba Bank`.

## Rebirth pacing

Rebirth needs Shiba 21 (ShooterTier level 20) and gives income × (1 + rebirths).

| run | multiplier | reaches Shiba 21 | whole run |
|-----|------------|------------------|-----------|
| 1 | ×1 | 38.2 min | 65.7 min |
| 2 | ×2 | 19.1 min | 32.9 min |
| 3 | ×3 | 12.7 min | 21.9 min |
| 4 | ×4 | 9.6 min | 16.4 min |
| 6 | ×6 | 6.4 min | 11.0 min |

Because every price is income × time, a ×m multiplier divides every wait by m: later runs get short quickly. That is
the usual prestige power trip for the first few rebirths; if later runs feel too short in playtests, lower
`Rebirth.PerRebirth` (0.5 = ×1.5, ×2, ×2.5 …) or make the requirement rise with rebirths (needs a small
RebirthService + billboard change).

## Trophies

Bought with Bonk Dollars (`TrophyThresholds` → `Config/Shop` Points), each about the price of the Shiba bought around
then: Wood 1e4 (≈ Shiba 4), Bronze 1e8 (≈ Shiba 7), Silver 1e14 (≈ Shiba 12), Gold 1e22 (≈ Shiba 20), Galaxy 1e30
(≈ Shiba 27).

## How to retune

1. Change numbers in `EconomyConfig.luau` only:
   - whole run longer/shorter: `PACE.MaxSeconds` (and `Knee` to move where the minute rhythm starts: larger Knee =
     later);
   - how cheap a side upgrade is: its `PriceShare` (mind the ≥ 0.15 rule);
   - when an upgrade appears: its `From` / `To` in `ROUTE_SPECS` (this also moves `UnlockAtShibaTier`);
   - how strong idle is: `AUTOMATION` tables (`CatchShare` / `ExpectedCatchesPerSecond` are only the model — keep them
     honest with what AutomationService really catches, `WalkSpeed` drives the real intern);
   - how many sticks fly: `StickDensity.MaxThrowsPerSecond` (income stays the same; it moves value between the player
     and the helpers, so re-run the simulation);
   - end number: `FINAL_SHIBA_COST` (everything re-prices).
2. `lune run docs/economy/simulate.luau` and compare the summary with the targets table above.
3. Update this file (the tables are copied from the simulation output) and `docs/GAME_DESIGN.md → Pacing`.
4. After real playtests, correct the model first (`BASELINE`: catch rate, catches/s, ActiveBonus) so the simulation
   matches what players actually earn, then retune the pace.

## Tycoon

The tycoon ("Shiba Workers", `docs/GAME_DESIGN.md → Tycoon`) has its own simulation, `docs/economy/tycoon_sim.luau`. It loads
the real `Config/Tycoon` and `Util/TycoonMath`, so it always matches the game's numbers, and plays a solo, efficient,
always-online player (no passes, boosts, events, friends, crates or lucky variants): it always takes the action with the
shortest wait plus payback (level up, hatch, equip slot, arch, Mill ring, zone). Real players are slower, so read the totals
as a lower bound (factor about 1.3 to 1.6) against the 70-100 hour target.

```
lune run docs/economy/tycoon_sim                  # from the repo root
PRICE_SCALE=10 lune run docs/economy/tycoon_sim   # test knob
```

`PRICE_SCALE` (environment variable, default 1) multiplies every zone price, egg price, Mill ring price and equip slot price;
use it to see how much longer or shorter the run gets without editing the config. Real retuning goes into
`src/shared/Config/Tycoon.luau` (prices, `Lane.LevelCostGrowth`, `Lane.TierGrowth`, `EggWeights` ...); then re-run and copy
the result here.

CALIBRATION RESULT (`lune run docs/economy/tycoon_sim`, 4 runs = first run + 3 Ascensions; zone prices are in
`ZONE_PRICES` at the top of `Config/Tycoon.luau`, egg, Mill ring and equip slot prices derive from them):

| Milestone (run 1, solo efficient player) | Time |
|---|---|
| Zone 1 Beach | 30 min |
| Zone 2 Forest | 3.1 h |
| Zone 3 Mountain | 4.3 h |
| Zone 4 Space | 59.8 h |
| Zone 5 Heaven | 63.6 h |
| Everything maxed (all 30 types, level 50, arches, rings, 10 slots) | 64.1 h |
| Runs 2-4 after Ascension 1-3 (level cap 60 / 70 / 80) | about 8.5 h / 7.7 h / 8.9 h each |

The simulation is a lower bound (no breaks or mistakes): with the factor 1.3-1.6 a real player needs about 85-100 hours for the
first run, the target being 70-100 hours. Zones 1-3 open early on purpose (early game is fast); the long wall is zone 4 (price
divided by the income the player can reach with the zone 0-3 Shibas). To lengthen or shorten the game change the prices of
zone 4 and 5 only, then re-run. Known simplifications: variants, crates, boops, passes and friends are ignored; a Shiba can
only be equipped once its zone is unlocked (also in the sim). The greedy policy takes the best egg it can afford within 30
minutes of income.

## Street tycoon (30 bays)

`docs/economy/street_sim.luau` (`lune run docs/economy/street_sim`) simulates the street mode (docs/GAME_DESIGN.md, "Gameplay flow"). It
loads the REAL `Config/Tycoon`, `Util/TycoonMath`, `Util/TycoonSteps` and every decor theme, so prices, cooldowns, perks, neighbour
bonuses and the decor reward bonuses are exactly the game's. Environment variables override single constants (`TIER_GROWTH`,
`BAY_SECONDS`, `DECOR_SCALE`, `AUTO_SECONDS`, `AUTO_GROWTH`, `LEVEL_SECONDS`, `LEVEL_GROWTH`, `PAYOUT_PER_LEVEL`,
`MIN_COOLDOWN_GROWTH`, `FACTORS=f1,f2,...` for the stage factors), `PLAYER=active|idle`, `STOP_BAY=n`, `DEBUG=1`, `TRACE=minutes`,
`RESULT=1` (machine-readable bay times). A full run takes about 8 s.

**Why the first street economy was broken (Marco, 2026-10-01: "the first Shiba went to level 100 without effort, then I could unlock
everything without waiting").** A Shiba's income at level L is payout(L) / cooldown(L): the payout grows with every level and the
cooldown shrinks from seconds to milliseconds, so a Shiba earns up to about 20 000 times its level-1 income. The old prices were
counted in seconds of the LEVEL-1 income (`TierIncome`), so after a few minutes of levelling everything cost almost nothing: with the
old constants the sim finished the whole game (30 bays, all decor, all Interns, all levels 100) in 1.4 h.

**The model now.**
- Level cost: `LevelCost(tier, level, street)` = `StreetLevelSeconds` (8) x `StreetLevelGrowth` (1.12)^(level-1) seconds of the Shiba's OWN income at that
  level, times `StageFactor[tier+1]^LevelFactorPower` (0.9): the first upgrade of Shiba 1 is $8 = 8 clicks, and levelling a Shiba from 1 to 30
  costs about 15 to 25 times its purchase price (Shiba 1 is around level 35 after two hours, Shiba 2 about 30) (`LEVELRATIO=1 lune run docs/economy/street_sim` prints the ratio per Shiba).
- All other prices are counted in seconds of `StreetReadyIncome(tier)` = the income a Shiba earns at `ReadyLevel` 25 (what the player
  typically has when the purchase is due): expansion n = `StreetReadyIncome(n-2) x BaySeconds x StageFactor[n-1]`, a decor part =
  `StreetReadyIncome(bay-1) x PriceSeconds x DecorScale x StageFactor[bay]`, the Bonk Intern = `StreetReadyIncome(tier) x
  AutomationSeconds x AutomationGrowth^(Interns bought)`. The Intern of Shiba 1, bought before any other Intern, costs a fixed `AutomationFirstPrice` of 300. `TierGrowth` (street only) is 4.
- Stage n = the decor of bay n + the expansion to bay n+1. `StageFactor[n]` (29 numbers in `Config/Tycoon`) was calibrated per stage
  (secant search on the sim, `node docs/tools/calibrate_street.js`) so that every stage takes: 8 min for stages 1 to 3, then 17%
  longer than the stage before. The factors are rough where the themes differ (10 to 30 parts, different PriceSeconds).
- Base cooldown 1 s + 8 s per tier (max 240 s), lowest cooldown per tier 20 ms x 1.28^tier (`MinCooldownGrowth`) and +100% of the level-1 payout per level (`PayoutPerLevel` 1) as in
  docs/GAME_DESIGN.md. Decor of bays 6 to 30 has no `RewardMult` yet: the sim assumes x6 per theme.

**Player.** Heads for the next progress item (a decor part, then the next Shiba); while it is not affordable it buys only what pays for
itself before that moment (level ups, Interns). ACTIVE clicks (3 clicks/s cap, 50% of the time), IDLE stops clicking after its first Intern.

**Result** (hours until the Shiba is bought; active, a lower bound: real players need 1.3 to 1.6 times as long):
Shiba 2: 0.13 h, 3: 0.26, 5: 0.55, 10: 1.8, 15: 4.6, 20: 10.7, 25: 24, 30: 53.4 h. Stage times: 8 min (stages 1 to 4), 15 min (stage 8),
28 min (stage 12), 51 min (stage 16), 96 min (stage 20), 3.6 h (stage 25), 7.7 h (stage 29). Shiba 1 is level 21 when Shiba 2 is bought
(8 min), 46 at 16 min, 70 at 33 min and about 80 after 1.8 h; the idle player is within 1% of the active one because the Intern is cheap.
After the last Shiba every level is bought within minutes (no ascension yet), so the game ends with the last expansion.

**Re-calibrating.** After changing any constant or a theme (prices, `RewardMult`), run `node docs/tools/calibrate_street.js BAY_SECONDS=300
DECOR_SCALE=0.1 AUTO_SECONDS=60 AUTO_GROWTH=1.08` (about 3 minutes): for stage n = 1 to 29 it finds `StageFactor[n]` until stage n takes its target
(8 min, then x1.17 per stage) and prints the new factors for `Config/Tycoon`. The sim prints the stage times (`minutes per stage`); the numbers
above are what the committed constants give.
