--!strict
-- EconomyConfig: the single source of truth for every price, income value and multiplier (docs/economy/BALANCING.md).
-- Other modules read their numbers from here; nothing else hardcodes economy numbers. If a system needs a new value,
-- add it here (with a `-- TODO(economy)` if it is a placeholder).
--
-- How the prices are made: they are DERIVED from a target pace, not typed in.
--   1. The Route lists every purchase of a full run in the intended order (Shibas, Shiba tiers, projectiles, speed,
--      basket, intern), spread evenly between each upgrade's From and To (fractions of the run).
--   2. The target wait for purchase n (0-based) is  T(n) = MaxSeconds − (MaxSeconds − MinSeconds) · e^(−n / Knee):
--      a few seconds at the start, settling into a minute rhythm.
--   3. price(n) = income of the Baseline player right before purchase n × T(n) × the upgrade's PriceShare.
--      Between two Shiba tiers the purchases are sorted cheapest first (what a player who buys the cheapest thing
--      does anyway), so every price is based on the income the player really has when buying it.
--   4. The Shiba tier multipliers grow by one constant factor, solved so that the last Shiba costs FinalShibaCost.
-- So changing FinalShibaCost, Pace or the Route re-prices the whole game consistently. After a change, run the
-- simulation and check its summary against the targets in docs/economy/BALANCING.md.
--
-- No requires, no side effects: the balancing simulation (lune run docs/economy/simulate.luau) loads this file directly.

-- The price of the very last Shiba (ShooterTier max level). 1e33 = one decillion.
local FINAL_SHIBA_COST = 1e33

-- Target seconds between two purchases (see the header).
local PACE = {
	MinSeconds = 4,
	-- MaxSeconds is never reached: with Knee 50 the curve is almost a straight line from 4 s to ~2.5 min at the last
	-- purchase. Waits pass 60 s around purchase 18 (while owning the 8th Shiba, ~6.5 min in) and a whole first run takes
	-- ~66 min.
	-- (A lower MaxSeconds keeps the end at ~1.5 min but the run then only lasts ~55 min.)
	MaxSeconds = 200,
	-- Purchases until the wait has closed ~63 % of the gap to MaxSeconds (larger = slower, straighter rise).
	Knee = 50,
}

-- The player the prices are derived for (an average, active player).
local BASELINE = {
	-- Share of thrown sticks a player catches at Move Speed level 0, + per Move Speed level, at most MaxCatchRate.
	CatchRate = 0.6,
	CatchPerSpeedLevel = 0.03,
	MaxCatchRate = 0.9,
	-- Nobody catches more than this many sticks per second, + per Move Speed level (the rest is left for the intern
	-- and the basket). Sticks land ~25 studs apart on average; at WalkSpeed 16 that is about one per second, at 46
	-- (Move Speed 10) about two. With the stick density cap (StickDensity, ~1.4 sticks/s) this rarely binds.
	MaxCatchesPerSecond = 1,
	CatchesPerSecondPerSpeedLevel = 0.1,
	-- Average multiplier of a caught stick from catch quality, head hits and combo (see Bonk below), + per Move Speed
	-- level: a faster player gets under more sticks before they land (AIR ×2 / PERFECT ×4 instead of a Normal
	-- pick-up). Since the density cap keeps the sticks few enough to reach, speed mostly pays through catch quality.
	ActiveBonus = 2,
	ActiveBonusPerSpeedLevel = 0.05,
}

-- Bonk payouts. A caught stick pays: stick value × quality × head × combo × golden × boosts/passes/events × rebirth.
-- Stick value = projectile BaseReward × Shiba tier RewardMultiplier.
local BONK = {
	-- Catch quality, by WHEN you catch it (docs/GAME_DESIGN.md → Hits):
	--   Normal  = after it touched the ground (bounces, settling hops)
	--   Good    = in the air ("AIR BONK")
	--   Perfect = in the air within PerfectWindow seconds before it lands ("PERFECT BONK")
	QualityMultipliers = {
		Normal = 1,
		Good = 2,
		Perfect = 4,
	},
	HeadMultiplier = 2,
	-- Combo: every hit within the combo window adds ComboStep, up to ComboMax.
	ComboStep = 0.1,
	ComboMax = 3,
	GoldenMultiplier = 5,
	-- A brand-new player's very first caught stick pays this many times more (onboarding "wow" moment).
	FirstBonkMultiplier = 10,
}

-- Rebirth (prestige): resets Bonk Dollars and all upgrade levels (Shibas, tiers, projectiles, speed, basket, intern)
-- for a permanent income multiplier. Keeps passes, trophies, Shiba-Index, quests, streaks, boosts, Bonk Rains, settings.
local REBIRTH = {
	-- ShooterTier level needed to rebirth (level 20 = the 21st Shiba).
	MinShibaTier = 20,
	-- Income multiplier = 1 + PerRebirth × rebirths (×2, ×3, ×4 …).
	PerRebirth = 1,
}

-- The Shibas (ShooterTier level n = Shibas[n + 1]). Each one throws faster and pays more; the RewardMultiplier is
-- derived below. AssetName = the model in ReplicatedStorage.Assets (models are only referenced, never changed):
-- every Shiba has its own model.
-- Height = model height in studs. FireInterval = seconds between two throws of one Shiba.
export type ShibaDef = {
	Name: string,
	AssetName: string,
	-- Optional look variant of a shared model (ShibaEffects.Editions); nil = the model's own look (all Shibas now).
	Edition: string?,
	Height: number,
	Color: Color3,
	FireInterval: number,
	-- Derived (filled in below).
	RewardMultiplier: number,
}

-- In tier order. The Cheems God stays near the top; only the Eternal and the Void Shiba are above it.
-- Models: assets/models/build_shiba_tiers.py (DESIGNS, NEW_DESIGNS, THIRD_DESIGNS).
local SHIBA_LIST = {
	{ Name = "Shiba", AssetName = "Shiba", Height = 6, Color = Color3.fromRGB(255, 170, 60) }, -- 1
	{ Name = "Shades Shiba", AssetName = "ShadesShiba", Height = 6, Color = Color3.fromRGB(160, 160, 185) }, -- 2
	{ Name = "Buff Shiba", AssetName = "BuffShiba", Height = 7.5, Color = Color3.fromRGB(255, 110, 90) }, -- 3
	{ Name = "Chef Shiba", AssetName = "ChefShiba", Height = 7.5, Color = Color3.fromRGB(250, 250, 250) }, -- 4
	{ Name = "DJ Shiba", AssetName = "DJShiba", Height = 7, Color = Color3.fromRGB(255, 80, 200) }, -- 5
	{ Name = "Police Shiba", AssetName = "PoliceShiba", Height = 6.5, Color = Color3.fromRGB(70, 130, 255) }, -- 6
	{ Name = "Cowboy Shiba", AssetName = "CowboyShiba", Height = 7, Color = Color3.fromRGB(200, 120, 55) }, -- 7
	{ Name = "Pirate Shiba", AssetName = "PirateShiba", Height = 7, Color = Color3.fromRGB(150, 85, 40) }, -- 8
	{ Name = "Ninja Shiba", AssetName = "NinjaShiba", Height = 5.5, Color = Color3.fromRGB(220, 40, 60) }, -- 9
	{ Name = "Viking Shiba", AssetName = "VikingShiba", Height = 7.5, Color = Color3.fromRGB(165, 170, 180) }, -- 10
	{ Name = "Knight Shiba", AssetName = "KnightShiba", Height = 8, Color = Color3.fromRGB(190, 200, 215) }, -- 11
	{ Name = "Samurai Shiba", AssetName = "SamuraiShiba", Height = 7.5, Color = Color3.fromRGB(200, 30, 40) }, -- 12
	{ Name = "Robot Shiba", AssetName = "RobotShiba", Height = 7.5, Color = Color3.fromRGB(70, 240, 255) }, -- 13
	{ Name = "Astronaut Shiba", AssetName = "AstronautShiba", Height = 7.5, Color = Color3.fromRGB(240, 242, 248) }, -- 14
	{ Name = "Superhero Shiba", AssetName = "SuperheroShiba", Height = 8, Color = Color3.fromRGB(230, 40, 60) }, -- 15
	{ Name = "Gold Shiba", AssetName = "GoldShiba", Height = 6.5, Color = Color3.fromRGB(255, 200, 40) }, -- 16
	{ Name = "Wizard Shiba", AssetName = "WizardShiba", Height = 8.5, Color = Color3.fromRGB(70, 80, 220) }, -- 17
	{ Name = "Vampire Shiba", AssetName = "VampireShiba", Height = 7, Color = Color3.fromRGB(170, 15, 35) }, -- 18
	{ Name = "Pharaoh Shiba", AssetName = "PharaohShiba", Height = 7.5, Color = Color3.fromRGB(255, 195, 40) }, -- 19
	{ Name = "Frost Shiba", AssetName = "FrostShiba", Height = 8.5, Color = Color3.fromRGB(150, 220, 255) }, -- 20
	{ Name = "Magma Shiba", AssetName = "MagmaShiba", Height = 9, Color = Color3.fromRGB(255, 110, 20) }, -- 21
	{ Name = "Dragon Shiba", AssetName = "DragonShiba", Height = 8.5, Color = Color3.fromRGB(60, 180, 80) }, -- 22
	{ Name = "Mecha Shiba", AssetName = "MechaShiba", Height = 8.5, Color = Color3.fromRGB(120, 140, 170) }, -- 23
	{ Name = "Galaxy Shiba", AssetName = "GalaxyShiba", Height = 7, Color = Color3.fromRGB(170, 90, 255) }, -- 24
	{ Name = "Angel Shiba", AssetName = "AngelShiba", Height = 11, Color = Color3.fromRGB(255, 240, 190) }, -- 25
	{ Name = "Demon Shiba", AssetName = "DemonShiba", Height = 11, Color = Color3.fromRGB(200, 20, 30) }, -- 26
	{ Name = "Giant Shiba", AssetName = "GiantShiba", Height = 16, Color = Color3.fromRGB(255, 130, 40) }, -- 27
	{ Name = "Cheems God", AssetName = "CheemsGod", Height = 12, Color = Color3.fromRGB(255, 240, 170) }, -- 28
	{ Name = "Eternal Shiba", AssetName = "EternalShiba", Height = 16, Color = Color3.fromRGB(255, 225, 120) }, -- 29
	{ Name = "Void Shiba", AssetName = "VoidShiba", Height = 18, Color = Color3.fromRGB(140, 60, 255) }, -- 30
}

-- Throw interval of the first and the last Shiba; the ones between are spread geometrically.
local FIRST_FIRE_INTERVAL = 5
local LAST_FIRE_INTERVAL = 1.2

-- Stick density cap (docs/GAME_DESIGN.md → Shooters). The ring of Shibas throws at most MaxThrowsPerSecond sticks per
-- second, however many Shibas, however fast their tier, fire-rate boost or StickStorm. When the natural rate
-- (Shibas / FireInterval, with boosts and events) is higher, the ring throws at the cap and every stick is worth
-- natural ÷ capped times as much (its ValueMultiplier, shown on the stick as "×N"), so Bonk Dollars per second stay
-- exactly the same, only in fewer, bigger sticks. Mirrored as Gameplay.Shooters.MaxThrowsPerSecond.
-- Why 1.4: sticks land ~25 studs apart and a player at WalkSpeed 16 reaches about one per second (two at max Move
-- Speed); with a flight of ~1.5 s plus bounces that keeps ~4–5 sticks in the air, few enough to follow every one.
-- Below 1.2 the early mid game (3–4 Shibas) already hits the cap and feels slow; above ~1.8 the late game gets
-- chaotic again. The cap first bites at about 5 Shibas on Shiba 8 (natural 1.4/s) and at the end (8 Shibas at
-- 1.2 s = 6.7/s natural) each stick carries ×4.8.
local STICK_DENSITY = {
	MaxThrowsPerSecond = 1.4,
}

-- Projectile tiers (Config/Projectiles has names and models, same order): BaseReward of the first one, and the
-- factor from one tier to the next. PROJECTILE_TIERS must match Config/Projectiles → Tiers.
local PROJECTILE_TIERS = 10
local FIRST_PROJECTILE_REWARD = 10
local PROJECTILE_GROWTH = 2.5

-- Automation (docs/GAME_DESIGN.md → Automation). Per level (level 1 = unlocked). Only sticks the player does not
-- catch are left for them: the intern goes for them first, the basket gets what the intern misses.
-- Tuned so that an AFK player earns a real share: with basket and intern, active play earns ~3.8× the idle income at
-- first, ~3× from Shiba 16 and ~2.4× at the end of a run (the simulation prints it), so playing always pays more but
-- idling is not zero. The stick density cap (StickDensity) means there is no flood of missed sticks: the intern takes
-- a share of what the player leaves and the basket rolls on the rest, so both keep mattering; their levels step up in
-- big increments so every level still pays for itself (idle) within ~15 min.
local AUTOMATION = {
	Basket = {
		-- Chance that a stick nobody caught ends up in the basket.
		CatchChance = { 0.35, 0.48, 0.61, 0.74, 0.87, 1 },
		-- Pays this share of a Normal bonk.
		Payout = { 0.45, 0.56, 0.67, 0.78, 0.89, 1 },
		-- Offline earnings (Shiba Bank) are capped at this many hours.
		OfflineHours = { 2, 3, 4, 5, 6, 8 },
	},
	Intern = {
		Names = { "Bonk Intern", "Hard-Hat Intern", "Junior Bonker", "Senior Bonker", "Bonk Manager", "Bonk CEO" },
		WalkSpeed = { 18, 22, 26, 30, 34, 38 },
		Payout = { 0.7, 0.76, 0.82, 0.88, 0.94, 1 },
		-- The model of what the intern reaches (pricing and the simulation only; in the game it depends on where the
		-- sticks land and its WalkSpeed): CatchShare of the sticks the player leaves, at most ExpectedCatchesPerSecond.
		-- CatchShare follows the Baseline player's rule (60 % at WalkSpeed 16, +1 % per stud/s): with the density cap
		-- there are at most ~1.4 sticks/s, so a walker can't take all of them however fast it is, and the basket
		-- keeps getting the rest.
		CatchShare = { 0.5, 0.56, 0.62, 0.68, 0.74, 0.8 },
		ExpectedCatchesPerSecond = { 0.8, 1, 1.2, 1.4, 1.6, 1.8 },
	},
	-- Offline (Shiba Bank): per minute away the player gets OfflineShare × their automation income per minute
	-- (+ BaseOfflineShare × their active income per minute), for at most the basket's OfflineHours (NoBasketHours
	-- without a basket).
	OfflineShare = 1,
	BaseOfflineShare = 0.05,
	NoBasketHours = 1,
}

-- Every purchase of a full run. Count = levels in the Route (the upgrade's MaxLevel); From/To = where in the run
-- (0 = first purchase, 1 = last) its first and last level sit; PriceShare scales its price (utility upgrades that add
-- little income are cheaper so they still pay for themselves within ~15 min). Shooters starts at 0: the first purchase
-- of the game is the second Shiba (the NEW SHIBA pad in front of the spawn).
-- Keep every PriceShare above ~1.2 / ShibaGrowth (≈ 0.15): a cheaper item placed right after a Shiba would still be
-- cheaper than that Shiba, get bought before it and then pay for itself ShibaGrowth (×8) times slower than planned.
-- Shares: Shibas and projectiles 1 (they multiply income); More Shibas 0.15 (cheap, quick buys: with the density cap
-- each extra Shiba adds its full share of value); Move Speed 0.16 (+3 % catch rate, +0.05 catch bonus ≈ +4 % income
-- per level); Basket 0.15 and Intern 0.12 (judged by what they add while idle). The Intern is below the ~0.15 rule:
-- its levels sit mid-segment, and the simulation shows none of them is bought out of Route order (re-check after
-- moving its From / To).
export type RouteSpec = {
	Upgrade: string,
	Count: number,
	From: number,
	To: number,
	PriceShare: number,
}

local ROUTE_SPECS: { RouteSpec } = {
	{ Upgrade = "Shooters", Count = 7, From = 0, To = 0.4, PriceShare = 0.15 },
	{
		Upgrade = "ShooterTier",
		Count = #SHIBA_LIST - 1,
		From = 0.02,
		To = 1,
		PriceShare = 1,
	},
	{ Upgrade = "ProjectileTier", Count = PROJECTILE_TIERS - 1, From = 0.04, To = 0.85, PriceShare = 1 },
	{ Upgrade = "MoveSpeed", Count = 10, From = 0.05, To = 0.8, PriceShare = 0.16 },
	{ Upgrade = "Basket", Count = #AUTOMATION.Basket.CatchChance, From = 0.2, To = 0.9, PriceShare = 0.15 },
	{ Upgrade = "Intern", Count = #AUTOMATION.Intern.Payout, From = 0.28, To = 0.94, PriceShare = 0.12 },
}

-- Levels past the Route (e.g. More Shibas with the +2 Shiba Slots pass) are priced by continuing the last two
-- prices' ratio for this many levels.
local EXTRA_LEVELS = 2

-- Trophy prices in Bonk Dollars (Config/Shop → Trophies `Points`, bought in the shop): each costs about as much as
-- the Shiba you buy around then (Wood ≈ Shiba 4, Bronze ≈ 7, Silver ≈ 12, Gold ≈ 20, Galaxy ≈ 27), so it is a
-- choice between the next Shiba and a trophy for your island.
local TROPHY_THRESHOLDS = {
	Wood = 1e4,
	Bronze = 1e8,
	Silver = 1e14,
	Gold = 1e22,
	Galaxy = 1e30,
}

-- ==== Social + Bonk Party (feat/social-party) ====
-- Friend Boost + invite rewards (docs/GAME_DESIGN.md → Friends and invites). A bonus on top of the paced income: the
-- route and the simulation never count it (SocialService, RewardService.GetStickValue).
local SOCIAL = {
	-- Income multiplier = 1 + PerFriend × min(Roblox friends in the server, MaxFriends).
	PerFriend = 0.1,
	-- Servers hold 5 players, so at most 4 friends: +40 %.
	MaxFriends = 4,
	-- What both the inviter and the invited friend get the first time a friend joins through an invite.
	InviteReward = { BonkRains = 1, Trophy = "BonkBuddies" },
	-- Inviter rewards per week (days since 1970 // 7); more wait as pending for next week.
	MaxInviteRewardsPerWeek = 10,
	-- DataStore for inviter rewards earned while the inviter was offline (key = inviter UserId, value = count).
	PendingStoreName = "ReferralsPending",
}

-- Weekend Bonk Party quest reward (schedule and look: Config/Events → Party).
local PARTY = {
	-- Normal bonks' worth (RewardService.Hits) for finishing the party quest.
	RewardHits = 150,
	Trophy = "Party",
}
-- ==== end Social + Bonk Party ====

------------------------------------------------------------------------------------------------------------------------
-- Derivation (pure maths, runs once on require).

export type Levels = { [string]: number }

export type RouteStep = {
	Upgrade: string,
	-- Level the upgrade reaches with this purchase (1 = first level bought).
	Level: number,
	-- 0-based position in the run.
	Index: number,
	-- Target seconds of play to afford it.
	TargetSeconds: number,
	Price: number,
}

-- Rounds to 2 significant digits (3 below 1,000), at least 1: prices look tidy.
local function tidy(value: number): number
	if value < 100 then
		return math.max(1, math.floor(value + 0.5))
	end
	local digits = if value < 1000 then 3 else 2
	local unit = 10 ^ (math.floor(math.log10(value)) - digits + 1)
	return math.floor(value / unit + 0.5) * unit
end

local function targetSeconds(index: number): number
	return PACE.MaxSeconds - (PACE.MaxSeconds - PACE.MinSeconds) * math.exp(-index / PACE.Knee)
end

-- Shibas with editions, fire intervals (multipliers come later).
local shibas: { ShibaDef } = {}
for _, entry in SHIBA_LIST do
	table.insert(shibas, {
		Name = entry.Name,
		AssetName = entry.AssetName,
		Height = entry.Height,
		Color = entry.Color,
		FireInterval = 0,
		RewardMultiplier = 1,
	})
end
for index, shiba in shibas do
	local k = (index - 1) / (#shibas - 1)
	-- One decimal is enough (and reads well in the menu).
	shiba.FireInterval = math.floor(FIRST_FIRE_INTERVAL * (LAST_FIRE_INTERVAL / FIRST_FIRE_INTERVAL) ^ k * 10 + 0.5)
		/ 10
end

local projectileRewards: { number } = {}
for tier = 1, PROJECTILE_TIERS do
	projectileRewards[tier] = tidy(FIRST_PROJECTILE_REWARD * PROJECTILE_GROWTH ^ (tier - 1))
end

-- The purchases of a full run, in order.
local route: { RouteStep } = {}
do
	type Entry = { Upgrade: string, Level: number, Position: number, Order: number }
	local entries: { Entry } = {}
	for order, spec in ROUTE_SPECS do
		for level = 1, spec.Count do
			local share = if spec.Count > 1 then (level - 1) / (spec.Count - 1) else 0
			table.insert(entries, {
				Upgrade = spec.Upgrade,
				Level = level,
				Position = spec.From + (spec.To - spec.From) * share,
				Order = order,
			})
		end
	end
	table.sort(entries, function(a: Entry, b: Entry): boolean
		if a.Position ~= b.Position then
			return a.Position < b.Position
		end
		return a.Order < b.Order
	end)
	for index, entry in entries do
		table.insert(route, {
			Upgrade = entry.Upgrade,
			Level = entry.Level,
			Index = index - 1,
			TargetSeconds = targetSeconds(index - 1),
			Price = 0,
		})
	end
end

local EconomyConfig = {}

-- The stick density cap (STICK_DENSITY above) for a ring of `shibaCount` Shibas that each throw every `fireInterval`
-- seconds (fire-rate boost and StickStorm already applied). `capScale` multiplies the cap (StickStorm lets a few
-- more sticks fly; default 1). Returns the sticks per second the ring really throws and the ValueMultiplier every
-- stick carries (≥ 1): throws/s × multiplier = shibaCount / fireInterval, so income never changes with the cap.
function EconomyConfig.ThrowRate(shibaCount: number, fireInterval: number, capScale: number?): (number, number)
	local natural = shibaCount / math.max(fireInterval, 1e-3)
	local cap = STICK_DENSITY.MaxThrowsPerSecond * (capScale or 1)
	if natural <= cap then
		return natural, 1
	end
	return cap, natural / cap
end

-- Bonk Dollars per second of the Baseline player at these upgrade levels (active play + automation), without
-- rebirth, boosts or passes. `idleOnly` = the player catches nothing (AFK): only the intern and basket earn.
-- Used to derive prices and by the simulation. Sticks are counted after the density cap (ThrowRate): fewer sticks,
-- each worth ValueMultiplier times as much, so the per-second catch limits below apply to the capped sticks.
function EconomyConfig.BaselineIncome(levels: Levels, idleOnly: boolean?): number
	local shibaCount = 1 + (levels.Shooters or 0)
	local shiba = shibas[math.clamp((levels.ShooterTier or 0) + 1, 1, #shibas)]
	local reward = projectileRewards[math.clamp((levels.ProjectileTier or 0) + 1, 1, #projectileRewards)]
	local sticksPerSecond, valueMultiplier = EconomyConfig.ThrowRate(shibaCount, shiba.FireInterval)
	local value = reward * shiba.RewardMultiplier * valueMultiplier
	local speed = levels.MoveSpeed or 0
	local caught = if idleOnly
		then 0
		else math.min(
			sticksPerSecond * math.min(BASELINE.MaxCatchRate, BASELINE.CatchRate + BASELINE.CatchPerSpeedLevel * speed),
			BASELINE.MaxCatchesPerSecond + BASELINE.CatchesPerSecondPerSpeedLevel * speed
		)
	local missed = sticksPerSecond - caught
	local internLevel = levels.Intern or 0
	local basketLevel = levels.Basket or 0
	local byIntern = if internLevel > 0
		then math.min(
			missed * AUTOMATION.Intern.CatchShare[internLevel],
			AUTOMATION.Intern.ExpectedCatchesPerSecond[internLevel]
		)
		else 0
	local internPay = if internLevel > 0 then AUTOMATION.Intern.Payout[internLevel] else 0
	local byBasket = if basketLevel > 0 then (missed - byIntern) * AUTOMATION.Basket.CatchChance[basketLevel] else 0
	local basketPay = if basketLevel > 0 then AUTOMATION.Basket.Payout[basketLevel] else 0
	local activeBonus = BASELINE.ActiveBonus + BASELINE.ActiveBonusPerSpeedLevel * speed
	return value * (caught * activeBonus + byIntern * internPay + byBasket * basketPay)
end

-- Price the route with Shiba tier multiplier growth 1, then solve the growth that makes the last Shiba cost
-- FINAL_SHIBA_COST: every income before the last purchase is proportional to growth^(tier level).
do
	local shareOf: { [string]: number } = {}
	for _, spec in ROUTE_SPECS do
		shareOf[spec.Upgrade] = spec.PriceShare
	end
	local function incomesBefore(): { number }
		local levels: Levels = {}
		local incomes: { number } = {}
		for index, step in route do
			incomes[index] = EconomyConfig.BaselineIncome(levels)
			levels[step.Upgrade] = step.Level
		end
		return incomes
	end
	-- Between two Shibas, a player who buys the cheapest thing first buys the cheap items first. Reorder every
	-- segment (the purchases between two Shiba tiers) by price, cheapest first, and re-price until nothing moves.
	-- Otherwise an item placed after a projectile tier (×PROJECTILE_GROWTH income) would be priced on that income,
	-- bought before it anyway, and take much longer to pay for itself than planned. Within a segment the tier (and
	-- so the growth) is the same, so ordering at growth 1 gives the same order as the final prices.
	for _ = 1, 10 do
		local incomes = incomesBefore()
		local changed = false
		-- The very first purchase (the second Shiba on the NEW SHIBA pad) stays first.
		local first = 2
		while first <= #route do
			if route[first].Upgrade == "ShooterTier" then
				first += 1
				continue
			end
			local last = first
			while last < #route and route[last + 1].Upgrade ~= "ShooterTier" do
				last += 1
			end
			type Item = { Upgrade: string, Price: number, At: number }
			local items: { Item } = {}
			for index = first, last do
				local step = route[index]
				table.insert(items, {
					Upgrade = step.Upgrade,
					Price = incomes[index] * step.TargetSeconds * shareOf[step.Upgrade],
					At = index,
				})
			end
			table.sort(items, function(a: Item, b: Item): boolean
				if a.Price ~= b.Price then
					return a.Price < b.Price
				end
				return a.At < b.At
			end)
			-- Levels of one upgrade stay in order: each upgrade takes its lowest level of the segment first.
			local lowest: { [string]: number } = {}
			for index = first, last do
				local step = route[index]
				lowest[step.Upgrade] = math.min(lowest[step.Upgrade] or math.huge, step.Level)
			end
			for offset, item in items do
				local step = route[first + offset - 1]
				local level = lowest[item.Upgrade]
				lowest[item.Upgrade] = level + 1
				if step.Upgrade ~= item.Upgrade or step.Level ~= level then
					changed = true
				end
				step.Upgrade = item.Upgrade
				step.Level = level
			end
			first = last + 1
		end
		if not changed then
			break
		end
	end
	local last = route[#route]
	assert(last.Upgrade == "ShooterTier" and last.Level == #shibas - 1, "the last purchase must be the last Shiba")
	local flat = incomesBefore()
	local lastPriceAtGrowthOne = flat[#route] * last.TargetSeconds * shareOf[last.Upgrade]
	-- Right before the last purchase the player has ShooterTier level #shibas − 2.
	local growth = (FINAL_SHIBA_COST / lastPriceAtGrowthOne) ^ (1 / (#shibas - 2))
	for index, shiba in shibas do
		shiba.RewardMultiplier = tidy(growth ^ (index - 1))
	end
	local incomes = incomesBefore()
	for index, step in route do
		-- The first purchase ignores its PriceShare: it costs exactly the start money, and a full share gives a
		-- round, not-silly amount (B$ 10 rather than B$ 1).
		local share = if index == 1 then 1 else shareOf[step.Upgrade]
		step.Price = tidy(incomes[index] * step.TargetSeconds * share)
	end
	-- The rounded multipliers leave the last price ~1 % off; the last Shiba costs exactly FINAL_SHIBA_COST.
	last.Price = FINAL_SHIBA_COST
	EconomyConfig.ShibaGrowth = growth
end

-- Prices per upgrade: Costs[upgradeId][level + 1] = price of level → level + 1.
local costs: { [string]: { number } } = {}
for _, step in route do
	costs[step.Upgrade] = costs[step.Upgrade] or {}
	costs[step.Upgrade][step.Level] = step.Price
end
for _, list in costs do
	for _ = 1, EXTRA_LEVELS do
		local ratio = if #list >= 2 then list[#list] / list[#list - 1] else 10
		table.insert(list, tidy(list[#list] * ratio))
	end
end

-- The ShooterTier level the player owns when each upgrade's first level comes up in the route: stands for later
-- upgrades (basket, intern) stay locked until then.
local unlockAtShibaTier: { [string]: number } = {}
do
	local tier = 0
	for _, step in route do
		if step.Upgrade == "ShooterTier" then
			tier = step.Level
		elseif step.Level == 1 and unlockAtShibaTier[step.Upgrade] == nil then
			unlockAtShibaTier[step.Upgrade] = tier
		end
	end
end

EconomyConfig.FinalShibaCost = FINAL_SHIBA_COST
EconomyConfig.Pace = PACE
EconomyConfig.Baseline = BASELINE
EconomyConfig.Bonk = BONK
EconomyConfig.Rebirth = REBIRTH
EconomyConfig.Automation = AUTOMATION
EconomyConfig.StickDensity = STICK_DENSITY
EconomyConfig.RouteSpecs = ROUTE_SPECS
EconomyConfig.TrophyThresholds = TROPHY_THRESHOLDS
-- Social + Bonk Party (feat/social-party).
EconomyConfig.Social = SOCIAL
EconomyConfig.Party = PARTY

-- Derived tables.
EconomyConfig.Shibas = shibas
EconomyConfig.ProjectileRewards = projectileRewards
EconomyConfig.Route = route
EconomyConfig.Costs = costs
EconomyConfig.UnlockAtShibaTier = unlockAtShibaTier
-- A brand-new player starts with exactly the price of the first purchase (the second Shiba).
EconomyConfig.StartingMoney = route[1].Price

-- Price of upgrade `id` from `level` to `level + 1` (math.huge past the priced levels).
function EconomyConfig.GetCost(id: string, level: number): number
	local list = costs[id]
	return if list then list[level + 1] or math.huge else math.huge
end

-- How many levels of `id` the route prices (its normal MaxLevel).
function EconomyConfig.RouteCount(id: string): number
	for _, spec in ROUTE_SPECS do
		if spec.Upgrade == id then
			return spec.Count
		end
	end
	return 0
end

function EconomyConfig.TargetSeconds(index: number): number
	return targetSeconds(index)
end

-- Income multiplier after `rebirths` rebirths.
function EconomyConfig.RebirthMultiplier(rebirths: number): number
	return 1 + REBIRTH.PerRebirth * rebirths
end

return EconomyConfig
