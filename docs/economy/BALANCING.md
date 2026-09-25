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
| minute rhythm (waits ≥ 60 s) from around Shiba 8–12 | waits pass 60 s at the **9th Shiba** (7.5 min in) |
| last Shiba costs 1e33 | **B$ 1Dc** exactly (`FINAL_SHIBA_COST`) |
| no payback > ~15 min (automation judged by idle payback) | longest: **15.0 min** (Basket 2, idle); everything else ≤ 14.6 min |
| cheapest-first order stays close to the Route | **0 of 67** purchases out of Route order |
| first run 60–90 min | **66.9 min** for all 67 purchases |
| active 1.5–3× idle once automation is unlocked | **3.7×** right after the intern, **3.1×** at Shiba 14, **2.6×** at Shiba 16, **1.7×** at the end |

Time to Shiba n (Shiba 1 is owned from the start; Shiba n = ShooterTier level n − 1):

| Shiba | 1 | 2 | 5 | 10 | 20 | 21 (rebirth) | 30 |
|-------|---|---|---|----|----|--------------|----|
| play time | 0 | 8 s | 1.7 min | 9.1 min | 36.6 min | 39.0 min | 66.9 min |

## The model

**Baseline player** (`EconomyConfig.BaselineIncome(levels)`), an average active player:

```
sticks/s   = Shibas / FireInterval(Shiba tier)                       (5.0 s → 1.2 s over the 30 Shibas)
caught/s   = min(sticks/s × catch rate, max catches/s)
             catch rate     = 60 % + 3 % per Move Speed level, max 90 %
             max catches/s  = 1 + 0.1 per Move Speed level            (sticks land ~25 studs apart)
missed/s   = sticks/s − caught/s  → intern first (up to its ExpectedCatchesPerSecond), basket gets CatchChance of the rest
income/s   = stick value × (caught × ActiveBonus 2 + intern × intern Payout + basket × basket Payout)
stick value = projectile BaseReward × Shiba RewardMultiplier
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
factor (**×8.08 per Shiba**), solved so the last Shiba costs exactly 1e33. Between two Shibas the purchases are
sorted cheapest-first (what a player who buys the cheapest thing does anyway), so each price is based on the income
the player really has when buying it.

**Unlocks** (`UnlockAtShibaTier`, derived from the Route): Projectile Tier and Move Speed with the Shades Shiba
(tier 1, 8 s in), Bonk Basket with the Gold Shiba (tier 6, ~4 min), Bonk Intern with the Giant Shiba (tier 8,
~7.5 min). Locked stands/cards say "Unlocks with …" and the server refuses them.

## Target curve vs the actual waits

The greedy player waits almost exactly T(n) for Shibas and projectiles (price share 1); the cheap items in between
(More Shibas, Move Speed, Basket, Intern) are quick buys of 2–35 s. Selected purchases:

| # | purchase | T(n) | actual wait | play time |
|---|----------|------|-------------|-----------|
| 2 | Shiba 2 | 7.9 s | 7.9 s | 8 s |
| 8 | Shiba 5 | 29.6 s | 29.4 s | 1.7 min |
| 17 | Shiba 8 | 57.7 s | 58.2 s | 5.5 min |
| 19 | Shiba 9 | 63.3 s | 63.6 s | 7.5 min |
| 22 | Shiba 10 | 71.2 s | 70.7 s | 9.1 min |
| 21 | Intern 1 (share 0.15) | 68.6 s | 10.4 s | 7.9 min |
| 36 | Shiba 15 | 1.7 min | 1.7 min | 21.3 min |
| 48 | Shiba 20 | 2.1 min | 2.1 min | 36.6 min |
| 67 | Shiba 30 | 2.5 min | 2.5 min | 66.9 min |

```
cumulative play time per Shiba (run 1, 50 chars = 66.9 min)
Shiba  1     0.0 s |
Shiba  2     7.9 s |
Shiba  3    44.2 s |#
Shiba  4    74.0 s |#
Shiba  5   1.7 min |#
Shiba  6   3.3 min |##
Shiba  7   4.0 min |###
Shiba  8   5.5 min |####
Shiba  9   7.5 min |######
Shiba 10   9.1 min |#######
Shiba 11  10.7 min |########
Shiba 12  13.9 min |##########
Shiba 13  15.9 min |############
Shiba 14  17.7 min |#############
Shiba 15  21.3 min |################
Shiba 16  23.6 min |##################
Shiba 17  25.6 min |###################
Shiba 18  29.8 min |######################
Shiba 19  31.7 min |########################
Shiba 20  36.6 min |###########################
Shiba 21  39.0 min |#############################
Shiba 22  41.5 min |###############################
Shiba 23  45.9 min |##################################
Shiba 24  48.6 min |####################################
Shiba 25  51.6 min |#######################################
Shiba 26  56.3 min |##########################################
Shiba 27  58.6 min |############################################
Shiba 28  61.6 min |##############################################
Shiba 29  64.4 min |################################################
Shiba 30  66.9 min |##################################################
```

## Payback per item

Payback = price ÷ income gained (active). Automation is judged by what it adds while idle (its whole point).

| Upgrade | PriceShare | Payback in run 1 | Why that share |
|---------|------------|------------------|----------------|
| Shiba tier | 1 | 1–21 s | ×8 income each: the main progression, always the "big" buy |
| Projectile tier | 1 | 10 s – 1.5 min | ×2.5 stick value |
| More Shibas | 0.15 | 4 s – 9.7 min | early it doubles the sticks; with many Shibas you can't catch more, the extra sticks mostly feed the automation |
| Move Speed | 0.16 | 38 s – 14.5 min | +3 % catch rate / +0.1 catches/s ≈ +5 % income |
| Bonk Basket | 0.25 | idle 1.6–15 min (active up to 6 h: it only gets the few sticks you miss while playing) | |
| Bonk Intern | 0.15 | 55 s – 14.6 min (active = idle) | |

**Rule:** keep every PriceShare above ~1.2 / ShibaGrowth (≈ 0.15). A cheaper item placed right after a Shiba would
still be cheaper than that Shiba, get bought before it, and then pay for itself ×8 slower than planned. (The first
version of this tuning had Move Speed at 0.08 and got 30–40 min paybacks for exactly this reason.)

## Idle vs active

| at purchase | Basket / Intern | active ÷ idle |
|-------------|-----------------|---------------|
| #20 (Shiba 9) | 1 / 0 | 7.2× |
| #25 (Shiba 11) | 1 / 1 | 3.7× |
| #35 (Shiba 14) | 2 / 2 | 3.1× |
| #40 (Shiba 16) | 3 / 3 | 2.6× |
| #50 (Shiba 21) | 4 / 4 | 2.3× |
| #60 (Shiba 25) | 5 / 5 | 2.0× |
| #65 (Shiba 28) | 6 / 6 | 1.7× |

Only the basket (before the intern) is weak on its own; with the intern the ratio sits in the 1.5–3× band from about
Shiba 14 on. Two things pull idle up over the run: Shibas throw faster, and the player's catches are capped per
second, so more and more sticks go to the automation.

**Offline (Shiba Bank)**: per minute away = 1 × automation income/min + 5 % × own income/min, for at most the basket's
OfflineHours (2 → 8 h; 1 h without a basket). See `docs/GAME_DESIGN.md → Offline Shiba Bank`.

## Rebirth pacing

Rebirth needs Shiba 21 (the Mythic Shiba, ShooterTier level 20) and gives income × (1 + rebirths).

| run | multiplier | reaches Shiba 21 | whole run |
|-----|------------|------------------|-----------|
| 1 | ×1 | 39.0 min | 66.9 min |
| 2 | ×2 | 19.5 min | 33.4 min |
| 3 | ×3 | 13.0 min | 22.3 min |
| 4 | ×4 | 9.8 min | 16.7 min |
| 6 | ×6 | 6.5 min | 11.1 min |

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
   - how strong idle is: `AUTOMATION` tables (`ExpectedCatchesPerSecond` is only the model — keep it honest with what
     AutomationService really catches, `WalkSpeed` drives the real intern);
   - end number: `FINAL_SHIBA_COST` (everything re-prices).
2. `lune run docs/economy/simulate.luau` and compare the summary with the targets table above.
3. Update this file (the tables are copied from the simulation output) and `docs/GAME_DESIGN.md → Pacing`.
4. After real playtests, correct the model first (`BASELINE`: catch rate, catches/s, ActiveBonus) so the simulation
   matches what players actually earn, then retune the pace.
