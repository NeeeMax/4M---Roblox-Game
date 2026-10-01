# Tycoon / idle-tycoon retention and economy research for GET BONKED (Street / Tycoon mode)

Research done 2026-10-01 (web search). Companion to `docs/research/ROBLOX_PACING.md` (2026-09-26, simulator-focused);
this file only adds what is new and flags where it disagrees. It compares the live Tycoon mode ("Shiba Workers" on the
Street) as configured in `src/shared/Config/Tycoon.luau`, `Street.luau`, `Automation.luau`, `Upgrades.luau`, `Shop.luau`
(at `f83231d`) with tycoon and idle-game evidence.
**None of this is a design decision.** `docs/GAME_DESIGN.md` stays the source of truth; every recommendation below is
"decision needed".

Contents: 1 Method and reliability · 2 Sources · 3 Key numbers · 4 Where this disagrees with ROBLOX_PACING.md ·
5 How the current config compares · 6 Concrete recommendations for GET BONKED Street/Tycoon · 7 Open questions

---

## 1. Method and reliability (read first)

- Search-engine summaries only. **Page fetching was blocked in this environment** (gamedeveloper.com, kongregate.com,
  create.roblox.com, devforum.roblox.com all refused), so no primary page was read in full. Every number below comes
  from a search-result summary of the linked page. Treat each number as "needs a 2-minute check against the link"
  before it goes into `GAME_DESIGN.md`.
- Reliability tags: **[P]** primary (Roblox, Kongregate/Pecorella, GameAnalytics), **[C]** community DevForum thread
  (real developers, unverified), **[W]** fan wiki or guide-farm site (low reliability, mechanics only),
  **[B]** blog/vendor content (opinion, often SEO text).
- Nothing was found that gives hard retention numbers for tycoon games specifically; Roblox publishes no per-genre
  tycoon benchmark. The tycoon-specific claims are community knowledge, not data.

## 2. Sources

| # | Source | Tag | What we took from it |
|---|--------|-----|----------------------|
| T1 | [Boost Your Discovery by Building Games People Want to Play (DevForum, J. Ciancutti, updated 2026-08-20)](https://devforum.roblox.com/t/boost-your-discovery-by-building-games-people-want-to-play/4779042) | P | Roblox is testing a Home/Recommended update that rewards "games players choose to return to over time, and where players find value in making purchases"; expected late Aug / early Sep 2026. Message: build for retention first, then "thoughtful, sustainable monetization" for players who already love the game |
| T2 | [Optimizing Discovery (Roblox newsroom, 2026-06)](https://about.roblox.com/newsroom/2026/06/optimizing-discovery-great-games-reach-millions-players-roblox) (already R2) | P | Windows widened 7 to 28 days; new signal **7-day qualified play sessions per user** (sessions per user over the last 7 days, i.e. frequency of return, not length) |
| T3 | [Creator Roadmap 2026: Spring Update (DevForum)](https://devforum.roblox.com/t/creator-roadmap-2026-spring-update/4625473), [Roadmap page](https://create.roblox.com/updates/roadmap) | P | Creator Hub tools reported shipped/planned: A/B experimentation, game betas, Creator Rewards analytics with benchmarks against similar experiences (via [BloxBot summary](https://www.bloxbot.ai/guide/roblox-spring-2026-creator-roadmap), [B]) |
| T4 | [Engagement rewards feature package (Creator Hub)](https://create.roblox.com/docs/resources/feature-packages/engagement-rewards) (already R9) | P | Config details not in ROBLOX_PACING: two reward types **Time** and **Daily**; `EngagementRewardsConfig` module; `isHiddenOnJoin` (auto-popup of a claimable daily reward on join); `isAlignedToStreakResetTime` (day 2 claimable 24 h after day 1, or at the first midnight after) |
| T5 | [Creator Rewards is live (DevForum)](https://devforum.roblox.com/t/creator-rewards-is-live/3838257), [Tubefilter](https://www.tubefilter.com/2025/06/24/roblox-creator-rewards-program-robux-for-engagement-retention/) | P / B | Daily Engagement Reward: 5 Robux when an **Active Spender** (spent at least $9.99 on Roblox in the past 60 days) plays 10+ min, only for the user's first 3 experiences of the day; Audience Expansion Reward for new/returning (60+ days inactive) users |
| T6 | [The Math of Idle Games, Part I (Pecorella, Kongregate/Gamedeveloper)](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i) | P | `cost_next = cost_base * rate_growth ^ owned`; `rate_growth` is **1.07 to 1.15** in the big idle games (Clicker Heroes 1.07 for all 35 heroes, Cookie Clicker 1.15 for all buildings, AdVenture Capitalist 10 businesses each between 1.07 and 1.15, Lemonade Stand 1.07). Production is roughly linear in owned count, cost exponential, so time to next purchase grows steadily; **milestones** (AdCap: production time halves at 25/50/100/200/300/400 owned) create the buying "spikes" |
| T7 | [The Math of Idle Games, Part III](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii) / [Kongregate copy](https://www.kongregate.com/en/pages/the-math-of-idle-games-part-iii) (already D2) | P | New detail: AdCap prestige currency `p = 150 * sqrt(lifetime / 1e15)`; to double the prestige currency the player must earn 4x as much as the previous run (square root). Offline "double" is a common ad reward |
| T8 | [Quest for Progress (Pecorella, GDC Europe 2016 slides, PDF)](https://media.gdcvault.com/gdceurope2016/presentations/Pecorella_Anthony_Quest%20for%20Progress.pdf) | P | Same series as T6/T7 in slide form; the place to verify cost curves and prestige timing before we commit numbers |
| T9 | [How do "Steal a" games calculate offline cash? (DevForum)](https://devforum.roblox.com/t/how-do-steal-a-games-calculate-offline-cash/3854950) | C | Standard method: save `os.time()` on leave, on join multiply current income/s by elapsed time; devs clamp the elapsed time and often divide it, because items earning billions per hour would otherwise pay a day's worth after a day away. Steal a Brainrot: offline cash is about **3 % of normal income, only up to 5 h** after the last session |
| T10 | [Steal a Brainrot wiki: Offline Cash](https://stealabrainrot.fandom.com/wiki/Offline_Cash), [Gamepasses and Dev Products](https://stealabrainrot.fandom.com/wiki/Gamepasses_and_Dev_Products) | W | The 3 % / 5 h figure above (cross-checks T9); passes: 2x Money 299 R$, VIP 499 R$ (0.5x money bonus, chat tag, +10 s lock time), Server Luck 2x/15 min 249 R$ and 4x/30 min 999 R$ |
| T11 | Steal a Brainrot rebirth lists: [Sportskeeda](https://www.sportskeeda.com/roblox-news/steal-brainrot-rebirth-guide), [FandomWire](https://fandomwire.com/roblox-steal-a-brainrot-rebirth-list-all-requirements-rewards/) | W / B | Rebirth 1 costs about $500K plus two specific brainrots; each rebirth adds +1 to the money multiplier (R1 x0.5 up to R19 x19), +10 s base lock time and unlocks stronger shop items; top rebirth needs about $30Qa. Rebirth gating by **specific items**, not only money |
| T12 | [Rebirth cost formula threads (DevForum)](https://devforum.roblox.com/t/good-formula-to-calculate-amount-needed-to-rebirth/1047686), [Multiplier system per rebirth](https://devforum.roblox.com/t/multiplier-system-for-each-rebirth-in-a-game/1520426), [Rebirths math problem](https://devforum.roblox.com/t/rebirths-math-problem/768366) | C | Typical tycoon rebirth: cost `C(r) = S * R^r` (e.g. `100 * 1.5^r`, +50 % per rebirth) or linear sums; multiplier examples x1.2 after rebirth 1, x1.4 after rebirth 2 (+0.2 each); advice to put a soft limit on exponential costs so elite players are not walled |
| T13 | [Monetization Ideas for my Tycoon Game (DevForum)](https://devforum.roblox.com/t/monetization-ideas-for-my-tycoon-game/3048249) | C | Community advice: avoid a plain "2x cash" pass in a tycoon (reads as pay-to-win); prefer VIP area/items, chat/name styling, cosmetics and time savers; keep one pass under 100 R$ for impulse buyers; mid tier 50-199 R$ is where most revenue sits. Summarised in [Bloxg monetization guide](https://bloxg.com/guides/roblox-monetization) [B] |
| T14 | [Theme Park Tycoon 2 gamepasses](https://tpt2.fandom.com/wiki/Gamepass), [Retail Tycoon 2 gamepasses](https://roblox-retail-tycoon-2.fandom.com/wiki/Gamepasses) | W | The two big builder tycoons sell **capacity and creative tools** (height limit, 24 extra expansion plots, extra colours, land, vehicles, radio), not income multipliers |
| T15 | [Idle Clicker Games: Best Practices (Mind Studios)](https://games.themindstudios.com/post/idle-clicker-game-design-and-monetization/), [Idle game development (Game-Ace)](https://game-ace.com/blog/idle-game-development/), [GameAnalytics: keep players engaged in idle games](https://www.gameanalytics.com/blog/how-to-keep-players-engaged-and-coming-back-to-your-idle-game) | B / P | Offline caps are typically **2 to 24 h**, capped on purpose so the player feels the lost opportunity and returns; the cap is also the main ad/IAP hook (rewarded video multiplies the offline reward). GameAnalytics: idle/AFK titles often match or beat RPG D7/D30 retention (mobile) |
| T16 | [Idle first-session guidance (mobile idle blogs, summarised by search)](https://allbitsequal.medium.com/taking-games-apart-how-to-design-a-simple-idle-clicker-6ca196ef90d6), [How to make an idle game (GameAnalytics/Adjust)](https://www.gameanalytics.com/blog/how-to-make-an-idle-game-adjust) | B | Rules of thumb: first upgrade within about 60 s, numbers rising without input in the first minute, first automation within about 3 min, first prestige 10-15 min (mobile idle). Opinion, no measured source |
| T17 | [First Week Retention (RoLearn)](https://rolearn.dev/guidance/first-week-retention-optimization/) | B | "First 5 minutes decide D1"; tycoon: first machine/purchase within about 30 s; most leavers go within 2 min. Matches R4/R5, adds nothing official |
| T18 | [GameAnalytics 2026 Mobile & PC benchmarks](https://www.gameanalytics.com/reports/2026-mobile-pc-gaming-benchmarks) | P | Mobile medians for context only: D1 about 22 %, D7 just under 4 %. **Roblox is lower** (see D1 in ROBLOX_PACING: D1 median 10.3 %); do not compare our numbers with mobile idle benchmarks |
| T19 | [Forbes on Steal the Brainrot (Fortnite port) loot boxes and gambling wheel, 2026-01-13](https://www.forbes.com/sites/paultassi/2026/01/13/fortnite-players-angry-at-steal-the-brainrots-20-loot-boxes-gambling-wheel/) | B | Press backlash for $20 loot boxes and a paid wheel (2 % / 0.5 % outcomes) in the Fortnite version: reputation risk of paid randomness, in line with R12 |

## 3. Key numbers

| Topic | Number | Source |
|-------|--------|--------|
| Idle cost growth per owned unit | 1.07 (Clicker Heroes, AdCap Lemonade) to 1.15 (Cookie Clicker); AdCap businesses all within 1.07-1.15 | T6 |
| Production milestones | AdCap: production time halves at 25/50/100/200/300/400 owned | T6 |
| Prestige currency | AdCap `150 * sqrt(lifetime/1e15)`; doubling it needs 4x earnings | T7 |
| Tycoon rebirth cost | `S * R^r`, R about 1.5 in community examples; multiplier +0.2 per rebirth in examples | T12 |
| Steal a Brainrot rebirth | multiplier +1 per rebirth, up to R19 | T11 [W] |
| Offline | Steal a Brainrot: 3 % rate, 5 h cap. Idle genre: cap 2-24 h, rewarded ad multiplies it | T9, T10 [W], T15 [B] |
| Idle first session | first buy under 60 s, first automation under 3 min, first prestige 10-15 min (mobile idle) | T16 [B] |
| Roblox retention windows | 28 days; 7-day qualified sessions per user is now a signal | T2 |
| Creator payout trigger | Active Spender, 10+ min, first 3 experiences of the day | T5 |
| Tycoon pass pricing | under 100 R$ impulse pass; 50-199 R$ mid tier; Brainrot 2x Money 299, VIP 499 | T13 [C], T10 [W] |

## 4. Where this disagrees with, or refines, ROBLOX_PACING.md

1. **R15 (Creator Rewards) needs a qualifier.** ROBLOX_PACING says creators are paid per "daily engaged spender".
   The announcement defines the payer as an *Active Spender* (spent at least $9.99 on Roblox in the last 60 days) and
   the reward as 5 Robux, only for that user's first 3 experiences of the day [T5]. The design consequence is the same
   (be one of the first three games a day, hold the player 10+ min), but free players do not trigger it.
2. **"67-minute first run fits the 60-min/day cap" (section 6) no longer describes the live mode.** Tycoon.luau now says
   its numbers are "calibrated to about 70-100 hours for everything", and Ascension needs zone 5. With playtime
   counting only to 60 min/day [R1] and a 28-day ranking window [R2], a casual player who plays 30 min/day reaches
   about 14 h in the window: the first Ascension, the only prestige layer, is unreachable inside the window that
   decides recommendations. This does not contradict a source, it contradicts the old doc's reassurance. See rec 1.
3. **Principle 2 ("design for come back tomorrow for 15-30 min") is reinforced and sharpened:** the newest signal is
   7-day qualified sessions per user [T2], i.e. return *frequency*, and an August 2026 follow-up says Roblox is also
   weighting long-term return and purchase value [T1]. Practical meaning: reasons to start a session (a full bank,
   a ready floor pad, a daily reward) beat reasons to stay longer.
4. **"Strength: Offline Shiba Bank up to 8 h" is on the generous side.** Brainrot caps at 5 h and pays 3 % [T9, T10];
   the idle genre uses 2-24 h [T15]. Our `BaseOfflineShare = 0.05` and `OfflineHours` up to 8 are not wrong, but the
   Brainrot comparison shows 5 % is not low for Roblox; see rec 6 for what actually matters (automation share).
5. **Idea 17 (rewarded ads) and idea 6 (28-day login) are supported, not contradicted.** T4 adds that the Roblox
   package auto-pops the daily reward on join (`isHiddenOnJoin = false`), worth copying as behaviour.

## 5. How the current config compares

| Config value | Now | Evidence | Verdict |
|--------------|-----|----------|---------|
| `Tycoon.Swing.StreetLevelGrowth` | 1.12 per level, cap 100 (1.12^24 = 15x at the ReadyLevel 25, 1.12^99 = about 75,000x at the cap) | Inside the 1.07-1.15 band [T6] | Fine. The cap level costs 75k times the first: only deep players see it, which is intended |
| `Tycoon.Lane.LevelCostGrowth` | 1.17 (island tycoon lanes) | Above the 1.15 ceiling of the classics [T6]; 1.17^49 = about 2,200x by level 50 | Island mode only; if island mode returns, tune to 1.12-1.15 |
| `Tycoon.Swing.AutomationGrowth` / `Street.AutomationGrowth` | 1.5 (island) / 1.08 (Street) | Street 1.08 is in the Clicker Heroes range; 1.08^29 = 9.3x for the 30th Intern | Fine |
| `Street.TierGrowth` | 4x income per bay, 30 bays | Not comparable to a per-unit coefficient: it is a *tier* ratio, paired with `StageFactor` rising to 194.7 | Fine, but see rec 3 on milestones |
| `Street.BaySeconds` | 300 s of ReadyLevel income per expansion | Brainrot-style "next purchase every 1-5 min early" is the norm; ours scales up through StageFactor | Check the late stages in street_sim: the last stages (factor 100+) imply multi-hour waits |
| `Tycoon.Ascension` | `MinZone = 5`, `PerAscension = 0.75` | Brainrot +1 per rebirth with item gating [T11]; community +0.2 [T12]; AdCap sqrt currency [T7]; mobile idle first prestige 10-15 min [T16] | Reward size is in range; the *timing* is the outlier (70-100 h). See rec 1 |
| `Automation` / `EconomyConfig.OfflineHours` | 2-8 h by basket level; 5 % active share | Brainrot 5 h / 3 % [T9]; genre 2-24 h [T15] | In range |
| `Shop` | pass 199/299/199 R$, boosts 39-249 R$, "Bonk Points never sold" | T13, T14 | Ethics fine; the Shop still describes the old points economy (see rec 8) |

## 6. Concrete recommendations for GET BONKED Street/Tycoon

All **decision needed**. Starting values are suggestions to be checked in `docs/economy/street_sim` before they are
used. Ordered by expected impact on D1 / 7-day sessions / D8-28.

| # | Recommendation | File / field | Suggested starting value | Reasoning | Decision needed |
|---|----------------|--------------|--------------------------|-----------|-----------------|
| 1 | **Add an early, small prestige layer, or move the first Ascension much earlier.** Today the only reset is at zone 5 (about 70+ h). Let the first Ascension unlock after about 3-5 h of play (around zone 2 or a Street bay count of about 10), with a small multiplier, and keep the zone-5 gate for later tiers (Brainrot gates rebirth 1 at about $500K, an early number, and ramps after [T11]) | `Tycoon.luau` `Ascension.MinZone` (5 to 2) or a new `Ascension.Tiers` list; `Street.luau` needs a bay-count gate field | First gate 3-5 h of play; `PerAscension` 0.75 stays (inside the +0.2 to +1 range [T11, T12]); require *more* each time via `S * 1.5^r` style gate [T12], capped by a soft limit | A prestige that exists only after 70 h does nothing for the 28-day window [R2] and for D7; Roblox now rewards frequency of return [T1, T2]. A first reset inside week 1 is the cheapest "come back" reason | Yes: Max and Marco (ownership of the economy numbers, see ARCHITECTURE.md) |
| 2 | **Target "time to next purchase" per phase and test it**: first purchase at 0 s (already), 2nd within 10-15 s, first Intern within 3 min, each bay under 2-3 min in the first 30 min, then rising | `Tycoon.luau` `Street.BaySeconds` (300), `StageFactor[1..6]`, `AutomationFirstPrice` (300) | Keep `AutomationFirstPrice = 300` only if it is reachable in under 3 min of play; check bay 2-6 waits are each under 3 min; cap any single wait in the first 60 min at 5 min | Rules of thumb from mobile idle [T16] and tycoon community [T17] (low reliability) agree with R4/R5 (fun in 5 min). We already measure waits in street_sim; this is a tuning target, not new work | Yes: confirm the targets, then run street_sim |
| 3 | **Add milestone spikes to Street levels** (double income at levels 10/25/50/100 per Shiba, like AdCap's 25/50/100/200/300/400 [T6]). The island `Lane.Milestones = {10, 25, 50}` with `MilestoneMult = 2` already exists but Street mode uses cooldown shrink and `PayoutPerLevel` | `Tycoon.luau` `Swing` (Street mode), reuse `Lane.Milestones`, `Lane.MilestoneMult` | `{10, 25, 50, 75, 100}` x2 on that Shiba's payout; cost curve unchanged at 1.12 | Smooth 1.12 growth alone makes every wait feel the same; AdCap's "spikes" make players plan which Shiba to level next [T6]. Also gives a visible goal ("2 levels to DOUBLE") for the HUD | Yes |
| 4 | **Pick the Ascension gate by items as well as money** (e.g. "own a Shiba of each of the first N bays at level 25"), not by price alone | `Tycoon.luau` `Ascension` (new `RequireLevel` / `RequireBays`) | N = bays reached, level 25 (= `Street.ReadyLevel`) | Brainrot gates rebirths on specific brainrots plus money [T11]; a money-only gate is a pure wait, an item gate asks the player to play the loop | Yes |
| 5 | **Keep Ascension multiplier linear, make the *cost* the soft cap** | `Tycoon.luau` `Ascension.PerAscension` | `+0.75` stays; add `GateGrowth = 1.5` for the money gate per ascension | Community examples scale the cost exponentially (about +50 % per rebirth) and the reward linearly, with a limit so elite players are not walled [T12]; Brainrot's reward is also linear (+1) [T11]. Prestige currency by sqrt formula (AdCap [T7]) is the alternative if we want a currency, but needs Types/DataService changes | Yes |
| 6 | **Offline: keep the cap, lean on the *automation* share, and sell the cap, not the money.** Keep 2-8 h by Basket level; keep `OfflineShare = 1` for automation but leave `BaseOfflineShare` at 0.05 (Brainrot pays 3 % [T10]). Offer "watch an ad / Robux: collect x2" on the Welcome-back card | `EconomyConfig.luau` `OfflineHours`, `OfflineShare`, `BaseOfflineShare` (existing); `Shop.luau` `DoubleOffline` product (existing Kind) | No change to the numbers; add the x2 hook on the Welcome-back popup | A visible cap that the player fills in about 8 h makes "log in before it overflows" the daily appointment, the exact behaviour that raises 7-day qualified sessions [T2, T15]. Our design already has all pieces | Only for the ad (needs Creator Hub eligibility, see R14) |
| 7 | **Daily reward auto-popup on join and a forgiving streak** (copy `isHiddenOnJoin = false`; one missed day per week forgiven, 28-day track) | `Config/Hub` Streak (idea 6 in ROBLOX_PACING), no Street field | Pop up only if claimable; streak forgiveness 1 per 7 days | Roblox's own package does the auto-popup [T4]; sessions-per-week is the signal [T2] | Yes (already idea 6; this adds the popup rule) |
| 8 | **Shop: money-free monetisation for the tycoon.** Sell *capacity and style*, not income: extra plot decor slots, Shiba skins/outfits, plot sign/name effects, VIP (cosmetic tag + small extra daily gift), timed 30-60 min x2 boosts as a clearly labelled time saver, an "auto-collect" Intern for the *first* Shiba only if it is also earnable. Avoid a permanent 2x Dollars pass | `Shop.luau` `passes` (`DoublePoints`, `VIP`, `Manage`), `products` (boosts), `Pass.Robux`, `Boost` | Keep one product under 100 R$ (the 39 R$ boost is fine); one 199 R$ cosmetic/VIP pass; if a permanent boost is wanted, +25 % not x2, and also reachable in game | Builder tycoons (TPT2, Retail Tycoon 2) sell plots, colours and tools, not income [T14, W]; DevForum advice warns against a 2x cash pass [T13, C]; Brainrot's 2x Money pass and Server Luck are what the press calls pay-to-win [T10, T19]; Roblox is now weighting purchase value over time, which cosmetics fit [T1]. Note `Shop.luau` still speaks of "Bonk Points" while Tycoon uses Bonk Dollars: confirm which currency the pass names refer to | Yes: Marco (Shop is an economy file) |
| 9 | **Make "next purchase in M:SS" and "levels to double" the permanent goal display** on every floor pad and the HUD | client only (no config), reads `Street.StageFactor`-derived prices | n/a | Short/mid/long goals [R5] and the idle "number goes up with a clear next step" [T16] | Yes (client work, see ROBLOX_PACING idea 10) |
| 10 | **Verify the late Street stages.** `StageFactor` reaches 194.7 at stage 27; confirm the sim shows no single wait over about 30 min before the first Ascension, and that the whole path is consistent with the Ascension timing chosen in rec 1 | `Street.luau` `StageFactor[18..29]`, `Tycoon.luau` `Street.BaySeconds` | A cap of 30 min per wait in the pre-Ascension path | Idle waits grow by design [T6], but the 60-min/day playtime cap and 28-day window [R1, R2] mean a single 1 h wait is a lost day | Yes |
| 11 | **Fix the ranking-relevant cadence, not the length of the session.** Plan for one "reason to return" every 8-12 h (bank full, Intern payout, free pad, daily reward) rather than one very long session | `Automation.luau` / `EconomyConfig` `OfflineHours` ladder (2, 3, 4, 5, 6, 8) already does this; no change | n/a (design principle) | 7-day qualified sessions per user [T2] | No (note only) |

### Not recommended

- **Prestige currency with a square-root formula right now** [T7]. It fits a hard "Ascension Points" shop, but needs a
  new currency, Types, DataService and UI. Rec 5 gets 80 % of the effect with `Config` changes only.
- **Copying Steal a Brainrot's 3 % offline rate** [T10]. That works because its income is not automated; ours is
  automation-first (Interns), so the offline share should stay high for automation.
- **Paid randomness** (Brainrot-style loot boxes, luck passes) [T19, R12].

## 7. Open questions

- Are the tycoon "70-100 hours" in `Tycoon.luau` an intended endgame length, or a calibration artefact? Rec 1 and 10 depend on it.
- Which currency does the Shop price (Bonk Points vs Bonk Dollars)? `Shop.luau` still says Bonk Points.
- Verify T6, T7, T8, T9, T11 against the linked pages (could not be fetched here) before quoting them in `GAME_DESIGN.md`.
