# Roblox retention and pacing research for GET BONKED

Research done 2026-09-26 (web search, Roblox Creator Hub, DevForum, press, wikis). It compares GET BONKED at
`f8c623a` (`docs/GAME_DESIGN.md`, `docs/economy/BALANCING.md`, `src/shared/Config/EconomyConfig.luau`) with what the
biggest Roblox games and Roblox itself say keeps players coming back.
**None of this is a design decision.** It is input for Marco and Max. `GAME_DESIGN.md` stays the source of truth.

Contents: 1 Sources · 2 Key principles · 3 How GET BONKED compares · 4 Improvement ideas (prioritised) ·
5 TOP 3 mini-specs · 6 What we should not copy · 7 Kurzfassung für Max

---

## 1. Sources summary

Roblox official (creator docs, DevForum announcements, newsroom):

| # | Source | What we took from it |
|---|--------|----------------------|
| R1 | [Discovery (Creator Hub)](https://create.roblox.com/docs/discovery) | Recommendation signals: play-through rate, **first-play bounce** (sessions under 60 s and 61–180 s count against you), **play days per user** (D1, D2–7, D8–28), playtime per user **capped at 60 min per user per day**, **intentional co-play days**, qualified sessions, spend days. Regular updates help it test the game with wider audiences |
| R2 | [Optimizing Discovery (Roblox newsroom, 2026-06)](https://about.roblox.com/newsroom/2026/06/optimizing-discovery-great-games-reach-millions-players-roblox) | The algorithm window grew from 7 to **28 days**; games with good thumbnails but no long-term value lose reach |
| R3 | [Improved Recommended For You algorithm (DevForum)](https://devforum.roblox.com/t/boost-your-discovery-with-the-improved-recommended-for-you-algorithm-and-analytics-for-creators/3587441) | Signal list published; reserved/private server sessions count as intentional co-play |
| R4 | [Retention (Creator Hub)](https://create.roblox.com/docs/production/analytics/retention) | Low D1 = core loop / onboarding / performance ("get users to the fun … in 5 minutes or less"); low D7 = weak progression and unclear goals; low D30 = not enough endgame and updates. Suggested cadence: **small updates every 2–4 weeks, big features every 2–3 months**; social features (leaderboards, trading, guilds) |
| R5 | [Onboarding (Creator Hub)](https://create.roblox.com/docs/production/game-design/onboarding) + [onboarding techniques](https://github.com/Roblox/creator-docs/blob/main/content/en-us/production/game-design/onboarding-techniques.md) | Teach the essentials, get to the fun fast, leave players wanting more; contextual tutorials; low early thresholds; show short/mid/long-term goals; end onboarding with a deliberate "moment of joy"; measure the funnel |
| R6 | [Improving onboarding through funnel events (DevForum)](https://devforum.roblox.com/t/improving-onboarding-through-funnel-events/3064458) | `AnalyticsService` onboarding funnel events show where new players drop off |
| R7 | [Analytics essentials](https://github.com/Roblox/creator-docs/blob/main/content/en-us/production/game-design/analytics-essentials.md) | Experiments (A/B tests) and Configs (live tuning without a new publish) |
| R8 | [Season pass design (Creator Hub)](https://create.roblox.com/docs/production/game-design/season-pass-design) | Start with ~1-month seasons, a week off between seasons, ~10 tiers, free + premium track, daily and weekly missions, double XP in the last week as catch-up, grant premium rewards retroactively |
| R9 | [Feature Packages: Season Pass and Engagement Rewards (DevForum beta)](https://devforum.roblox.com/t/beta-new-feature-packages-season-pass-engagement-rewards/3579550), [Engagement rewards docs](https://create.roblox.com/docs/resources/feature-packages/engagement-rewards) | Ready-made packages from Roblox (daily login calendar, playtime rewards, season pass) with funnel analytics built in |
| R10 | [Friend Referral System (DevForum)](https://devforum.roblox.com/t/announcing-the-new-friend-referral-system-for-your-experiences/3623795) | Invites with `ReferredByPlayerId` in join data, reward inviter/invitee; **co-play sessions are ~1.9× longer than solo** |
| R11 | [Experience notifications (Creator Hub)](https://create.roblox.com/docs/production/promotion/experience-notifications) | Opt-in via `ExperienceNotificationService:PromptOptIn()`; 13+ only; **max 1 per user per day**; ≤ 99 characters; use for real, personal events ("your egg hatched") |
| R12 | [Paid random items policy](https://create.roblox.com/docs/production/monetization/paid-random-items) | Anything random bought with Robux (or Robux-bought currency) needs every outcome with **numeric odds before purchase**, and "luck" items must explain their effect numerically; use `PolicyService` `ArePaidRandomItemsRestricted`; no outcome may be worthless |
| R13 | [Price optimization](https://create.roblox.com/docs/production/monetization/price-optimization) | Roblox A/B tests prices, but only if prices are read with `MarketplaceService:GetProductInfo` (not hard-coded); eligibility from 60k transactions / 30 days |
| R14 | [Rewarded video ads (DevForum)](https://devforum.roblox.com/t/rewarded-video-ads-are-now-available-to-all-ads-eligible-creators/4063278), [docs](https://create.roblox.com/docs/production/promotion/rewarded-video-ads) | Opt-in "watch an ad for a reward", open to all ads-eligible creators since 2026-02 (ID-verified, public game, ≥ 2k unique visitors/month); used by Grow a Garden and others |
| R15 | [Creator Rewards (Roblox wiki)](https://roblox.fandom.com/wiki/Creator_Rewards) | Since 2025-07 creators are paid per **daily engaged spender** (their first 3 games of the day include yours, ≥ 10 min) and for bringing new/returning spenders: daily return visits of ≥ 10 min directly pay |
| R16 | [Badges (Creator Hub)](https://create.roblox.com/docs/production/publishing/badges) | `BadgeService:AwardBadgeAsync` from the server; badges show on the player's profile |

Data and analysis:

| # | Source | What we took from it |
|---|--------|----------------------|
| D1 | [GameAnalytics key Roblox metrics 2026 (via gamedevreports)](https://gamedevreports.substack.com/p/gameanalytics-key-roblox-and-roblox) | Games ≥ 1M MAU, 2025-08 → 2026-07: **D1 median 10.3 % / top 1 % 22.2 %; D7 1.6 % / 9.1 %; D30 0.5 % / 4.7 %**; median session 9.8 min; daily playtime median 22 min, top 10 % 124 min; payer conversion 3.8 %; median ARPPU $0.70 |
| D2 | [Kongregate / Pecorella, "The Math of Idle Games" part III](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii) (+ [part I](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i)) | Prestige formulas: prestige currency ∝ earnings^(1/2 … 1/7), so doubling the prestige reward needs 4× … 128× more earnings; "bumpy" progression with fast and slow stretches; big numbers alone no longer carry a game |
| D3 | [The algorithm behind Steal a Brainrot (Andy Hall)](https://freesystems.substack.com/p/the-algorithm-behind-steal-a-brainrot) | Timed free spins, FOMO events on fixed days and the social stealing loop line up with "unique play days" and "play with friends" signals |
| D4 | [Prestige vs Rebirth (DevForum)](https://devforum.roblox.com/t/prestige-vs-rebirth/594019) and [rebirth system notes (Picoo)](https://picoo.io/how-to-make/roblox-rebirth-system) | Small compounding % boosts, rising rebirth costs as a soft cap, a clear "what resets / what stays / what multiplies" screen, save before reset |

Game-specific (wikis and press; fan wikis are less reliable, used only for mechanics):

| # | Game | Source | Key facts |
|---|------|--------|-----------|
| G1 | Grow a Garden | [Wikipedia](https://en.wikipedia.org/wiki/Grow_a_Garden), [GameSpot update schedule](https://www.gamespot.com/articles/next-grow-a-garden-update-and-events/1100-6534922/), [Seed Shop wiki](https://growagarden.fandom.com/wiki/Seed_Shop), [mutations (Beebom)](https://beebom.com/roblox-grow-a-garden-mutation-guide/), [Admin Abuse (Followchain)](https://www.followchain.org/admin-abuse-grow-a-garden/) | Made in 3 days by a 16-year-old; plants **grow while offline**; seed/gear stock rotates **every 5 min**; **weekly Saturday updates**, each a CCU spike (5M → 11.7M → 16M → 21.3M, peak 22.3M); weather events create stackable **mutations** (value multipliers); "admin abuse" hour before each update; later two event teams; criticised for heavy monetisation |
| G2 | Steal a Brainrot | [Wikipedia](https://en.wikipedia.org/wiki/Steal_a_Brainrot), [Medium analysis](https://medium.com/@emtertoszef/steal-a-brainrot-phenomenon-6af7b49081e0) | Idle base income from bought characters (rarity = income), conveyor shop, **stealing** (social PvP), rebirth, mutations/traits; updates **every Saturday**; first game over 25M CCU; criticised as pay-to-win |
| G3 | Pet Simulator 99 / X | [Huge Pets wiki](https://pet-simulator.fandom.com/wiki/Huge_Pets_(Pet_Simulator_99)), [BIG Games Index](https://db.biggames.io/), [Ranks](https://pet-simulator.fandom.com/wiki/Ranks_(Pet_Simulator_99)), [Huge chances (Marix)](https://marix.app/library/games/pet-simulator-99-huge-pet-chances), [PSX Rainbow Machine](https://pet-simulator.fandom.com/wiki/Rainbow_Machine_(Pet_Simulator_X)) | Every pet has Golden / Rainbow / Shiny variants; **Huge** pets are ~1 in 500k–1M chase items; the **Index** of all variants is a never-finished checklist; ranks give equip/hatch slots; **"Huge Party" Fri–Sat before each update with 3× / 6× / 12× Huge odds** |
| G4 | Adopt Me! | [Mega Neons wiki](https://adoptme.fandom.com/wiki/Mega_Neons), [update schedule](https://bloxswaps.com/blog/adopt-me-update-schedule) | Combine 4 of a pet → Neon, 4 Neons → Mega Neon (rainbow glow): a long, deterministic upgrade path; something new almost every week; weekly free "Admin Abuse" Saturdays |
| G5 | Bee Swarm Simulator | [Quests wiki](https://bee-swarm-simulator.fandom.com/wiki/Quests) | NPC questlines (Black Bear, Mother Bear) teach mechanics and hand out eggs; quests unlock the next systems; hive slots grow slowly; rare bees are long-term chase |
| G6 | Anime Vanguards | [Summon wiki](https://animevanguards.fandom.com/wiki/Summon), [PCGamesN](https://www.pcgamesn.com/anime-vanguards/codes) | Revived several times by a reliable update cadence; banner rotates **every hour**; event banners with a **pity** (guaranteed after N summons); a new **7-day login track per update** starting with the update's headline unit |
| G7 | Blox Fruits | [Update 30 (Beebom)](https://beebom.com/blox-fruits-update-30-patch-notes/) | Hourly world event on a fixed clock (XX:00); secrets and hidden bosses give max-level players reasons to revisit old areas; level-cap raises |
| G8 | 99 Nights in the Forest | [PC Gamer](https://www.pcgamer.com/games/survival-crafting/with-a-peak-player-count-of-14-2-million-99-nights-in-the-forest-has-an-audience-other-multiplayer-games-would-kill-for-to-find-these-behemoth-playerbases-you-need-to-be-on-a-platform-like-roblox/), [PCGamesN interview](https://www.pcgamesn.com/roblox/99-nights-in-the-forest-interview), [GameDaily](https://gamedaily.com/games/99-nights-in-the-forest-robloxs-survival-horror-darling-dominating-october-2025-charts) | 14.2M peak CCU; **co-op** (up to 5), strongest on weekends when friends group up; ~40 % teens/adults; depth and tension instead of randomness |
| G9 | Friend boosts | [Grow a Garden 2 friend boost](https://mygagcalculator.com/grow-a-garden-2-friend-boost/), [War Tycoon](https://war-tycoon-roblox.fandom.com/wiki/Friend_Boosts), [DevForum friend boost](https://devforum.roblox.com/t/making-a-friend-boost-system/2392990) | Common pattern: **+10 % per Roblox friend in the server** (GaG2: up to +70 %), shown as a HUD pill |
| G10 | Tycoon visits / likes | [Tropical Resort Tycoon](https://roblox.fandom.com/wiki/Ready,_set,_more!/Tropical_Resort_Tycoon), [Island Tycoon](https://www.roblox.com/games/130072092537258/Island-Tycoon) | Visiting other players' islands, likes, "richest island" boards: social pride without PvP |

---

## 2. Key principles

1. **The first 60 seconds decide the recommendation, not only the player.** Roblox counts sessions under 60 s and
   61–180 s as a negative "first play bounce" signal [R1]. The fun must arrive in under a minute and the first
   5 minutes must show the loop [R4, R5].
2. **Play days beat long sessions.** Playtime counts only up to 60 min per user per day [R1], and the algorithm now
   looks at D1, D2–7 and D8–28 play days over 28 days [R1, R2]. Creator Rewards pay per engaged spender *per day*
   (≥ 10 min) [R15]. Design for "come back tomorrow for 15–30 minutes", not for 3-hour grinds.
3. **Daily hooks + weekly appointments.** Top games combine something daily (spins, streaks, quests, timed free
   spins [D3]) with a **fixed weekly moment**: Saturday updates with an "admin abuse" / party hour before them
   (Grow a Garden, Steal a Brainrot, PS99 Huge Party, Adopt Me [G1–G4]). Every weekly update in Grow a Garden was a
   new CCU record [G1].
4. **Collection with a long tail.** Every big simulator has chance-based variants on top of a deterministic path:
   Golden/Rainbow/Shiny/Huge (PS99), Neon/Mega Neon (Adopt Me), mutations (Grow a Garden, Steal a Brainrot) [G1–G4].
   The deterministic path gives steady progress; the rare roll gives stories, screenshots and "one more round". An
   index that is never quite finished is the D30 goal [G3].
5. **Short, mid and long goals always on screen** [R5, R4]: next purchase (seconds–minutes), next unlock / quest
   (minutes–hours), rare collection / rebirth / season (days–weeks).
6. **Social play is now a ranking signal.** "Intentional co-play days" (joins via invites, friends, private
   servers) is an official signal [R1, R3]; co-play sessions are ~1.9× longer [R10]. The cheap version is a friend
   boost and invite rewards [G9, R10]; the deep version is co-op (99 Nights [G8]).
7. **Idle and offline growth lower the cost of returning.** Grow a Garden plants grow offline [G1]; idle games use
   offline gains as the reason to open the game again [D2]. A notification when something is ready closes the loop
   [R11].
8. **Rebirth must feel like a new game, not a repeat.** Good prestige systems give something new per layer (new
   perks, new currency, rising requirements) and soften the reset with compounding boosts [D2, D4].
9. **Update cadence is part of the design.** Roblox suggests small updates every 2–4 weeks and big ones every
   2–3 months [R4]; the megahits ship weekly with dedicated event teams [G1, G2]. A 2-person team should plan for
   systems that make **new content cheap** (a new Shiba model, a new event, a new variant) rather than new systems.
10. **Monetise time and style, disclose chance, never sell the win.** Steal a Brainrot and Grow a Garden are
    publicly criticised for pay-to-win / excessive monetisation [G1, G2]. Robux-bought randomness needs numeric
    odds and a policy check [R12]. Keep prices dynamic so Roblox price tests can run [R13]. Rewarded ads are a
    non-Robux option players choose themselves [R14].
11. **Measure before tuning.** Onboarding funnel events [R6], Experiments and Configs [R7]; compare against the
    benchmark: median D1 10 %, top-1 % D1 22 %, D7 9 % [D1].

---

## 3. How GET BONKED compares

### Strengths (keep these)

| Area | What we have | Principle |
|------|--------------|-----------|
| First minute | Starting money = price of the 2nd Shiba (buy at 0 s), NEW SHIBA pad with "Step here!", **FIRST BONK ×10**, guided hints for 6 purchases, no text tutorial | 1, 5 (better than most simulators) |
| Core skill | Landing ring with BONK / AIR BONK / PERFECT BONK timing, head ×2, combo to ×3: active play earns ~2–3.7× idle | real skill layer that most tycoons lack |
| Pacing model | Prices derived from a target wait curve (4 s → 2.5 min), 67 purchases, first run 66.9 min, no payback over ~15 min, simulated with lune | 5; matches the "session 15–30 min" target over 2–4 sessions |
| Daily hooks | Daily spin, 7-day login streak, playtime gifts (5–60 min), 3 daily quests, obby reward every 30 min | 3 (daily part) |
| Idle / offline | Basket + intern, Offline Shiba Bank (up to 8 h), "Welcome back" popup | 7 |
| Live feel | Server events every ~15 min (Golden Minute, Mega Stick, Double Dollars, Stick Storm), Bonk Rain | 3 (session part) |
| Collection | Shiba-Index with 51 entries, discovery rewards and a completion bonus | 4 (start) |
| Prestige | Rebirth at Shiba 21, income ×(1 + rebirths), kept items listed | 8 (start) |
| Ethics | Bonk Dollars never sold for Robux, spins never sold, boosts/time savers/cosmetics only | 10 |

### Gaps (ordered by impact)

1. **No chance-based chase; the collection ends in run 1.** Everything is deterministic: every Shiba, projectile
   and golden stick is found on the first run (~67 min + trophies). After that the Index gives nothing to hunt, so
   there is no D8–28 goal [principle 4, R4 "D30"]. Also: the Index includes the **Robux-only trophies** (VIP,
   Diamond, Rainbow, Starter), so the completion bonus is only reachable by paying (`Config/Index` adds every trophy).
2. **No social or co-play reason.** Islands are solo; Roblox friends in the server give nothing; no invites, no
   visiting, no likes. Co-play is an official ranking signal [R1] and servers hold only 5 players.
3. **No weekly appointment.** Daily hooks exist, but nothing happens on a fixed day of the week, and updates have no
   visible cadence (no update log / countdown) [principle 3, 9].
4. **Rebirth repeats the same run.** Run 2 is the same 30 Shibas at ×2 speed, run 3 at ×3; `BALANCING.md` already
   warns later runs "get short quickly". Nothing new unlocks per rebirth [D2, D4].
5. **No Roblox-level long-term signals:** no badges [R16], no experience notifications [R11] ("Your Shiba Bank is
   full"), no onboarding funnel analytics [R6].
6. **Streak is harsh.** Missing one day resets the 7-day streak; after day 7 there is no longer track. Anime
   Vanguards restarts a 7-day track with each update [G6]; Roblox suggests milestones at 7/14/30 [R9].
7. **Shop prices are typed in `Config/Shop`**, so Roblox price optimisation can't run [R13].
8. **The goal display is short-term only.** Stands show the next purchase; there is no single "next goals" view
   (next Shiba ETA, quests, Index %, rebirth progress) [R5].

---

## 4. Improvement ideas (prioritised)

Effort for our 2-person team: **S** ≤ 1 day, **M** 2–5 days, **L** > 1 week (incl. docs, save migration, Studio test).
"Robux / Creator Hub" = needs new passes/products, badges, or settings on the Creator Hub.
Rank = impact on D1/D7/D30 and co-play ÷ effort, judged honestly.

| # | Name | What | Why (source) | Effort | Systems / files | Robux / Creator Hub |
|---|------|------|--------------|--------|-----------------|---------------------|
| **1** | **★ TOP 1: Shiba Variants (Shiny / Rainbow / Huge) + Index pages** | Every Shiba slot on your ring rolls a variant when you evolve or add a Shiba: Shiny, Rainbow, Huge (bigger, stronger). Variants never downgrade, survive evolution and rebirth, each one found fills an Index page. See §5.1 | The one missing pillar every top simulator has: a rare chase on top of the deterministic path; gives a D8–28 goal and makes rebirth runs different [G3, G4, G1, principle 4] | M | new `VariantService`, `UpgradeService`, `RewardService`, `NPCShooterService`, `BonkService`, `AutomationService`, `Config/Index`, `IndexController`, `ShibaController`/look, `EconomyConfig.Variants`, `Types`, `DataService` v3 | no (avoid Robux-bought rolls, see §5.1) |
| **2** | **★ TOP 2: Friend Boost + invite rewards** | +10 % income per Roblox friend on the server (max 4 = +40 %), INVITE button (Roblox invite prompt), one-time reward for inviter and invited friend via `ReferredByPlayerId`. See §5.2 | Co-play days are an official ranking signal [R1, R3]; co-play sessions ~1.9× longer [R10]; the standard simulator pattern [G9] | S–M | new `SocialService` (server), `RewardService`, `HudController`, `EconomyConfig.Social`, `Types`, `DataService` | optional: turn on the Friend Referral banner in Creator Hub |
| **3** | **★ TOP 3: Weekend Bonk Party** | Every Saturday 12:00 UTC for 24 h: server events every 7 min instead of 15, variant luck ×3, a party quest with a weekly party trophy. Countdown on the hub and HUD all week. See §5.3 | Weekly fixed appointment like Huge Party / admin abuse / Saturday updates [G1–G4, D3]; reuses `EventService`; gives the update cadence a stage | S–M | `EventService`, `Config/Events`, `EventController`, `VariantService` (luck), `QuestService`/new party quest, `TrophyService`, `Types` | no |
| 4 | Fix Index completion | Leave Robux-only trophies (VIP, Diamond, Rainbow, Starter) out of the completion requirement (still show them, marked "exclusive"). | A completion bonus only payers can reach feels like a paywall [principle 10] | S | `Config/Index` (`Completion` count), `IndexService`, `IndexController` | no |
| 5 | Achievements with Roblox badges | ~15 milestones: first PERFECT, 100 / 1,000 perfects, combo ×3, 10k catches, every 10 Shibas, first rebirth, rebirth 5, obby under 30 s, first Rainbow, first Huge, 7-day streak. Each gives a badge + bonks | Long-term goals [R4, R5]; badges show on the profile [R16]; cheap content | S–M | new `AchievementService`, `Config/Achievements`, small tab in `IndexController`, `Types` | yes: badges created on Creator Hub (ids into config) |
| 6 | Better daily login (28-day track + grace day) | Keep the 7-day track, add a 28-day calendar with milestones on day 7/14/21/28 (Bonk Rain, 2× boosts, a cosmetic trail); **one missed day per week is forgiven** instead of a full reset | Roblox Engagement Rewards pattern and 7/14/30 milestones [R9]; harsh resets drive players away | S | `StreakService`, `Config/Hub` Streak, `GiftsController`, `Types.StreakState` | no |
| 7 | Experience notifications | Ask to opt in after the first rebirth or a full Shiba Bank; send at most one per day: "Your Shiba Bank is full (8 h)!", "Bonk Party starts now!" | Brings players back on the day something is ready [R11, principle 7] | S | new `NotifyOptIn` in `OfflineService`/client, Open Cloud call (needs a key on a small backend or Roblox's in-experience API) | yes: notification strings in Creator Hub; 13+ only; ≥ 100 visits |
| 8 | Onboarding funnel + Configs | Log funnel steps (spawn, pad, first catch, first AIR/PERFECT, 6 guided buys, first Basket, first rebirth) with `AnalyticsService`; move 3–4 key numbers (StartingMoney, PerfectWindow, pace MaxSeconds) behind Roblox Configs for A/B tests | We can't tune D1 without data [R6, R7, D1] | S | `TutorialService`, `BonkService`, `UpgradeService`, `RebirthService` | Creator Hub analytics / Experiments |
| 9 | Rebirth perks ("Bonk Tokens") | Each rebirth also gives tokens for a small permanent perk tree: +start money, +1 intern speed, +5 % golden chance, +variant luck, keep Move Speed. Raise the requirement slowly after rebirth 5 (Shiba 21 → 23 → 25) | Makes each run feel different; soft cap on ever-shorter runs [D2, D4, BALANCING "Rebirth pacing"] | M | `RebirthService`, `EconomyConfig.Rebirth`, new `RebirthController` perk menu, `Types`, simulation | no |
| 10 | "Next goals" panel | One small HUD panel: next Shiba (price, ETA at current income), today's quests left, Index %, rebirth progress | Always show short/mid/long goals [R5, R4] | S | `HudController`, reads existing state | no |
| 11 | Follower Shiba (cosmetic) | Your best variant Shiba follows you around the island/hub as a mini version (0.4× scale). Pure cosmetic; others see it | The pet-that-follows-you is the #1 status symbol in simulators [G3]; shows off Huge/Rainbow finds in the hub | M | new `FollowerController` (client, other players' followers too), `Types` (chosen follower), reuses Shiba models | later: follower cosmetics as Robux items |
| 12 | Visit and Like islands | "LIKE" button on each island's name sign (once per player per island per day), hub board "Most liked islands" (weekly), liker and owner get a few bonks | Pride and social pull without PvP [G10]; uses the empty other islands | M | `IslandService` (sign prompt), new `LikeService`, `LeaderboardService` (weekly OrderedDataStore), `Types` | no |
| 13 | Field weather (mutations light) | Server-wide 2-min weather every ~20 min: Rain (sticks slide further, ×1.5), Wind (sticks drift, ×2), Night (glowing sticks, ×2), Rainbow sky (variant luck ×2). Adds 4 new Index entries ("caught in Rain") | Grow a Garden weather → mutations is one of its main loops [G1]; re-uses `EventService` | M | `EventService`, `Config/Events`, `ProjectilePath` (drift only if cheap), `EventController`, `Config/Index` | no |
| 14 | Weekly leaderboards | TOP BONKERS this week (earned this week) and fastest rebirth this week, reset Monday | All-time boards freeze out new players; weekly gives everyone a chance | S | `LeaderboardService` (weekly key suffix), hub board | no |
| 15 | Update log board + cadence | A board next to the hub spawn: last update's headline + "Next update Friday" countdown. Team rule: small update every 2 weeks (one new Shiba model or event), big one every ~2 months | Update cadence as a promise [R4, G1, G2, G6] | S (board) + process | `HubService`/`Signs`, `Config/Build` or new `Config/Updates` | no |
| 16 | Dynamic Robux prices | Read each product's price with `MarketplaceService:GetProductInfo` (cached) instead of `Config/Shop` numbers | Required for Roblox price tests; prices shown always match [R13] | S | `ShopService`/`ShopController`, `Config/Shop` | Price optimisation later (needs 60k tx / 30 days) |
| 17 | Rewarded video ad boosts | Optional "Watch an ad → 2× Dollars 10 min" or "double your offline earnings" (next to the R$ 39 button), max 3 per day | Monetises non-payers without selling power; used by Grow a Garden [R14] | S–M | `ShopService`, `WelcomeBackController`, `BoostService` | yes: ads eligibility (ID-verified, ≥ 2k visitors/month) |
| 18 | Server Bonk Goal | A community meter per server: all players together catch 2,000 sticks → a free Golden Minute for everyone | Cheap cooperative moment in a 5-player server [principle 6] | S | `EventService`, `BonkService` counter, `EventController` bar | no |
| 19 | Cosmetics: ring skins, bonk sounds, catch bursts | Unlock landing-ring skins and bonk sound packs from Index milestones, achievements and a few Robux items | "Style, not power" monetisation [principle 10]; keeps Robux ethical | M | `ProjectileController`, `BonkController`, `ShopController`, `Config/Shop`, `Types` | yes: products/passes |
| 20 | Bonk Buddy co-op | A friend standing on your island can catch your sticks; both get paid (owner full, buddy 50 %); combo shared | Real co-play [G8, R10]; bigger change to the anti-farm and hit rules | L | `ProjectileService`, `BonkService` (validate non-owner), `ProjectileController` (draw for guests), `NPCShooterService` | no |
| 21 | Island expansion / decor levels | Each 5 Shibas unlock an island "level": new decor ring, a bigger sand field lip, lamps, a flag; optional decor shop for Bonk Dollars (small permanent % bonus, e.g. +2 % each, 10 pieces) | Visible growth is the tycoon hook [G10]; the design doc lists "visual island progression" as not in MVP, so this needs a decision | L | `IslandService`, `DecorService`, `PropService`, models, `EconomyConfig`, simulation | no |
| 22 | Season pass ("Bonk Pass") | 4-week seasons, 10–20 tiers, XP from quests/achievements, free + premium track, last-week double XP | Proven retention + revenue [R8, R9]; only worth it once we have weekly players and cheap cosmetic rewards | L | Roblox Season Pass feature package or own `SeasonService`, UI, rewards | yes: premium pass product |

**Not in the list on purpose:** trading (scams, black markets, moderation load: Grow a Garden has an eBay black
market [G1]), stealing / PvP on islands (Steal a Brainrot's hook, but the opposite of our friendly tone and a big
security surface), paid random eggs or luck potions (policy work [R12], child-audience ethics).

**Suggested order:** 4 and 16 (quick fixes) → **1** → **2** → **3** → 5, 6, 10 → 8, 7 → 9 → 11, 12 → the rest after
real D1/D7 numbers.

---

## 5. TOP 3 mini-specs

All numbers are starting values. New save fields → `SAVE_VERSION` 3 in `DataService` with defaults for old saves.
Changes to `src/shared/Types` and `src/shared/Net` go in their own "contract" commit first (CLAUDE.md rule).

### 5.1 TOP 1: Shiba Variants (Shiny / Rainbow / Huge)

**Player view:** "I just evolved to Samurai Shiba and my 3rd Shiba came out **RAINBOW**!" Each of your up-to-10
Shibas has its own variant. Variants only ever go up (Normal → Shiny → Rainbow → Huge), stay through evolutions (a
Rainbow slot is a Rainbow Samurai, later a Rainbow Dragon) and through rebirth. The Index gets a **VARIANTS** tab:
30 Shibas × 3 variants = 90 new entries ("Rainbow Samurai Shiba").

**Rules**

| | Shiny | Rainbow | Huge |
|---|---|---|---|
| Chance per roll | 1 in 40 | 1 in 400 | 1 in 4,000 |
| Stick value of that Shiba's throws | ×1.5 | ×3 | ×6 |
| Look | sparkle particles + white-gold outline | outline cycles through the rainbow | 1.6× scale, rainbow outline, glowing platform ring |

- **A roll happens** for every slot when you buy a Shiba Tier with Bonk Dollars (evolution) and for the new slot when
  you buy More Shibas with Bonk Dollars. Roll from the best variant down (Huge first); a result only counts if it is
  better than what the slot has.
- **No roll on Robux purchases** (Shiba Tier Skip, Instant Shiba Tier, Instant Shiba): otherwise they become paid
  random items that need odds disclosure and `PolicyService` checks [R12]. The popup after a Robux skip says
  "Variant rolls come from Bonk Dollar evolutions".
- **Pity:** `RollsSinceRainbow` and `RollsSinceHuge` counters; at 800 / 8,000 rolls the next roll is guaranteed
  Rainbow / Huge (a run has ~150–230 rolls, so a Huge is guaranteed within ~40 runs, usually much earlier).
- **Luck multiplier** (`EconomyConfig.Variants.Luck`): 1 normally, 3 during the Bonk Party (§5.3), 2 during "Rainbow
  sky" weather (idea 13). Luck divides the "1 in N" numbers.
- **Balance:** expected value in run 1 is small (~+3 % income); a lucky Huge slot doubles that Shiba's output. Like
  golden sticks, variants stay out of the pacing baseline (`BALANCING.md` note: "variants and luck only speed things
  up"). Check with the simulation that 10 Huge slots (the extreme) keep every payback sensible.

**Data**

```lua
-- Types (new)
export type VariantId = "Normal" | "Shiny" | "Rainbow" | "Huge"
export type VariantState = {
	Slots: { [string]: VariantId }, -- slot index ("1".."10") → variant; string keys for DataStore/network
	RollsSinceRainbow: number,
	RollsSinceHuge: number,
	TotalRolls: number,
}
-- PlayerState gets: Variants: VariantState  (default: Slots = {}, counters 0)
-- Index ids (saved, never rename): "Variant_<Variant>_<AssetName>", e.g. "Variant_Rainbow_SamuraiShiba"
```

```lua
-- EconomyConfig (new section, no requires, lune-safe)
local VARIANTS = {
	Order = { "Huge", "Rainbow", "Shiny" },           -- roll order, best first
	OneIn = { Shiny = 40, Rainbow = 400, Huge = 4000 },
	Multiplier = { Normal = 1, Shiny = 1.5, Rainbow = 3, Huge = 6 },
	Pity = { Rainbow = 800, Huge = 8000 },
	Luck = 1,                                           -- EventService may raise it temporarily
	IndexReward = { Shiny = 30, Rainbow = 100, Huge = 400 }, -- bonks, one-time per entry
}
EconomyConfig.Variants = VARIANTS
```

**Server**

- `VariantService` (new): `RollSlots(player, slots: {number})`, `GetVariant(player, slot): VariantId`,
  `GetLuck(): number` (base × active event). Uses a server `Random`. Marks Index entries seen through `IndexService`.
- `UpgradeService.TryPurchase`: after a successful Bonk-Dollar purchase of `ShooterTier` → roll all owned slots; of
  `Shooters` → roll the new slot. Robux grants (`ShopService`) call the level-up path with `roll = false`.
- `NPCShooterService`: each shooter already has a slot position; store the slot index on the projectile record.
- `RewardService.GetStickValue(player, projectile)`: multiply by `Multiplier[variant of projectile.slot]`. Used by
  `BonkService`, `AutomationService`, `AutoCatchService`, so hand catches, basket, intern and magnet all get it.
- `RebirthService`: keep `Variants` (add it to the "kept" list in the rebirth billboard text).
- `DataService`: v3 migration adds `Variants` defaults.

**Net:** `VariantRolled` (S→C): `{ slot: number, variant: VariantId, shibaName: string }` for the reveal; the slot
variants replicate as attributes on the shooter models (`Variant`), so every client draws the looks. Document in
`docs/NETWORK.md`.

**Client / UI**

- Shooter look (`NPCShooterService` builds the model; effects in `Config/ShibaEffects` → new `Variants` block).
- Reveal: after an evolution, a short card per new variant ("RAINBOW! Samurai Shiba · ×3 sticks") with a sound;
  Huge gets a full-screen splash and a server-wide chat/notification line ("Marco found a HUGE Samurai Shiba!") –
  free marketing inside the server.
- `IndexController`: VARIANTS tab with 90 cards (silhouette until found), per-variant progress bars.
- Stand billboard for Shiba Tier: small line "Rolls: 8 Shibas · luck ×1".
- Admin: "Roll variants now", "Set slot variant", "Luck ×10".

**Hookup checklist:** `EconomyConfig.Variants` → `Types` + `Net` (contract commit) → `DataService` v3 →
`VariantService` → reward multiplier → looks → Index tab → simulation note in `BALANCING.md` → `GAME_DESIGN.md`
sections (Shiba-Index, Upgrades, Rebirth, Saving).

### 5.2 TOP 2: Friend Boost + invite rewards

**Player view:** A pill under the money bar: "FRIEND BOOST +20 %" when two Roblox friends are on the server. An
**INVITE** button in the menu opens Roblox's invite dialog. When a friend joins through your invite for the first
time, both of you get a Bonk Rain and the "Bonk Buddies" trophy.

**Rules**

- Boost = `1 + PerFriend × min(friendsInServer, MaxFriends)`, PerFriend 0.10, MaxFriends 4 (servers hold 5 players,
  so max +40 %). Friendship = Roblox friends (`Player:IsFriendsWith`), checked on join and when anyone joins/leaves;
  cached per pair (it yields and is rate limited).
- Applies to everything that goes through `RewardService.GetStickValue` (hands, automation, magnet), not to spin,
  quests or Index rewards (they are in bonks, which already scale).
- Invite reward: on join, `player:GetJoinData().ReferredByPlayerId` [R10]. If set, the inviter is a friend, and the
  new player has never been rewarded for a referral: give the new player the reward; give the inviter the reward if
  online (else store it as pending on the inviter's save via a small `ReferralsPending` DataStore key, claimed on
  their next join). Cap inviter rewards at 10 per week.
- The boost stays in the offline bank's income sample (it is money you earned; the bank only uses 5 % of it).

**Data**

```lua
-- Types
export type SocialState = {
	ReferralRewarded: boolean,      -- this player already got the "invited" reward
	InviteRewardsWeek: number,      -- week number (days since 1970 // 7)
	InviteRewardsThisWeek: number,
	PendingInviteRewards: number,   -- inviter rewards earned while offline
}
-- PlayerState gets: Social: SocialState
```

```lua
-- EconomyConfig
local SOCIAL = {
	PerFriend = 0.1,
	MaxFriends = 4,
	InviteReward = { BonkRains = 1, Trophy = "BonkBuddies" },
	MaxInviteRewardsPerWeek = 10,
}
EconomyConfig.Social = SOCIAL
```

**Server:** new `SocialService` (friend cache, `GetFriendMultiplier(player)`, referral handling, remote
`RequestInvite` → the client calls `SocialService:PromptGameInvite` with `ExperienceInviteOptions` — the prompt must
run on the client, the server only validates rate). `RewardService` multiplies. `TrophyService` gets the
"BonkBuddies" trophy (not counted for Index completion, see idea 4, since it needs a friend).

**Net:** `FriendBoostChanged` (S→C: count, multiplier). Invite needs no remote (client-only prompt) except
analytics.

**Client:** `HudController` boost pill (same style as boosts), INVITE entry in the menu list, "+Bonk Rain! Your
friend X joined through your invite" popup.

**Creator Hub:** optional: enable and style the Friend Referral banner (reward text must match).

**Effort:** S–M (2–3 days incl. testing with two accounts in a live test server; `IsFriendsWith` doesn't work
between Studio test players).

### 5.3 TOP 3: Weekend Bonk Party

**Player view:** All week the hub board and a small HUD line say "BONK PARTY in 2d 04h". Saturday 12:00 UTC the
party starts for 24 h: confetti banner, server events every 7 minutes instead of 15, **variant luck ×3**, and a party
quest ("Catch 500 sticks during the Bonk Party") that gives this week's party trophy / Index entry. Planned updates
ship on Friday so the party shows the new content (like Grow a Garden and PS99 [G1, G3]).

**Rules**

- Window: `Weekday` 7 (Saturday, UTC), `StartHourUtc` 12, `DurationHours` 24 (covers EU evening and US Saturday).
- During the party: `Config/Events.Interval` → `PartyInterval` (7 min), `Variants.Luck` × 3, event weights unchanged.
- Party quest: progress = sticks caught (hands only) during the party; reward: 150 bonks + trophy `Party` (one trophy,
  counts up: "Party trophy ×4"). Not a daily quest slot, its own row in the QUESTS menu.
- Admin: "Start party now (10 min)" / "End party".

**Data**

```lua
-- Types
export type PartyState = {
	Week: number,        -- week of the last party the player joined (days since 1970 // 7)
	Catches: number,     -- this party's catches
	Claimed: boolean,    -- this party's quest reward claimed
	Count: number,       -- parties completed (trophy counter)
}
-- PlayerState gets: Party: PartyState (reset Catches/Claimed when Week changes)
```

```lua
-- Config/Events (look + schedule) and EconomyConfig (rewards)
Party = {
	Weekday = 7, StartHourUtc = 12, DurationHours = 24,
	PartyInterval = 7 * 60,
	VariantLuck = 3,
	QuestCatches = 500,
}
EconomyConfig.Party = { RewardBonks = 150 }
```

**Server:** `EventService` computes `IsPartyActive(now)` from UTC (all servers agree, no MessagingService needed),
switches the interval, exposes `GetLuck()` to `VariantService`; `BonkService` counts party catches; `QuestService`
(or a tiny `PartyService`) handles the claim; `TrophyService` shows the trophy.

**Net:** reuse the existing event state remote with a new `party = { endsAt, startsAt }` field (contract change).

**Client:** `EventController` banner + countdown, hub board text, party row in `QuestController`.

**Effort:** S–M (1–2 days) on top of idea 1 (without variants the party still works, luck just does nothing yet).

---

## 6. What we should not copy

- **Stock that rotates every 5 minutes / "be online at X or miss it forever" items** (Grow a Garden) work, but they
  push children to stay online and are criticised [G1]. Our Bonk Party keeps the trophy obtainable every week.
- **Pay-to-win and paid randomness** (Steal a Brainrot, egg luck potions) [G2, R12]. Keep "Robux = time and style".
- **Very long first-run grinds.** Our 67-minute first run fits the 60-min/day playtime cap [R1]; don't stretch it.
- **Too many systems for two people.** Each idea above should reuse an existing service; skip L ideas until D1/D7
  data shows where players drop.

---

## 7. Kurzfassung für Max

- Recherche: Pet Sim 99, Grow a Garden, Adopt Me, Steal a Brainrot, Bee Swarm, Anime Vanguards, Blox Fruits,
  99 Nights + Roblox-Doku (Discovery, Retention, Onboarding, Season Pass, Friend Referral, Notifications, Policies).
- Roblox belohnt jetzt: kurze Bounce-Rate (< 60 s ist schlecht), **Spieltage** über 28 Tage, max. 60 min/Tag zählen,
  **Spielen mit Freunden** ist ein offizielles Ranking-Signal. Median D1 10 %, Top-1 % D1 22 %.
- Unsere Stärken: super erste Minute (FIRST BONK ×10, Pad), sauberes Pacing (67 min erster Run), Timing-Skill,
  Daily Spin/Streak/Quests, Offline-Bank, Events alle 15 min, faire Monetisierung.
- Größte Lücken: (1) keine Zufalls-Jagd – der Index ist nach Run 1 fertig, danach kein Langzeitziel;
  (2) nichts Soziales (Freunde bringen nichts); (3) kein fester Wochen-Termin; (4) Rebirth = gleicher Run nur schneller.
- Bug/Fairness: Index-Komplettbonus braucht aktuell die Robux-Trophäen (VIP, Diamond, Rainbow) → rausnehmen.
- **TOP 1 – Shiba-Varianten:** jeder Shiba-Platz würfelt beim Entwickeln Shiny (1/40, ×1,5), Rainbow (1/400, ×3),
  Huge (1/4000, ×6, größer). Bleibt bei Evolution und Rebirth, 90 neue Index-Einträge, Pity-Zähler.
  Kein Würfeln bei Robux-Käufen (sonst Loot-Box-Regeln).
- **TOP 2 – Friend Boost:** +10 % pro Roblox-Freund im Server (max. +40 %), INVITE-Knopf, beide bekommen
  beim ersten Beitritt über Einladung einen Bonk Rain + Trophäe.
- **TOP 3 – Bonk Party:** jeden Samstag 12:00 UTC für 24 h: Events alle 7 min, Varianten-Glück ×3,
  Party-Quest mit Trophäe. Updates freitags, damit die Party sie zeigt.
- Danach: Achievements mit Roblox-Badges, 28-Tage-Login mit einem verzeihbaren Fehltag, "Nächste Ziele"-Panel,
  Onboarding-Funnel-Analytics, Push-Benachrichtigung "Shiba Bank voll", Rebirth-Perks.
- Bewusst NICHT: Trading, Stehlen/PvP, bezahlte Zufalls-Eier.
- Für dich relevant: Varianten brauchen Looks auf den Shiba-Modellen (Glitzer, Regenbogen-Outline, Huge = 1,6×) –
  das berührt `NPCShooterService` (deins). Keine neuen Modelle nötig.
- Nichts davon ist schon entschieden – bitte mit Marco abstimmen, dann kommt es in `GAME_DESIGN.md`.
- Ganze Datei: `docs/research/ROBLOX_PACING.md` (Quellen mit Links, 22 Ideen mit Aufwand).
