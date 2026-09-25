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
--   4. The Shiba tier multipliers grow by one constant factor, solved so that the last Shiba costs FinalShibaCost.
-- So changing FinalShibaCost, Pace or the Route re-prices the whole game consistently.
--
-- No requires, no side effects: the balancing simulation (lune run docs/economy/simulate.luau) loads this file directly.

-- The price of the very last Shiba (ShooterTier max level). 1e33 = one decillion.
local FINAL_SHIBA_COST = 1e33

-- Target seconds between two purchases (see the header).
local PACE = {
	MinSeconds = 4,
	MaxSeconds = 90,
	-- Purchases until the wait has closed ~63 % of the gap to MaxSeconds; ~22 puts the minute rhythm around Shiba 10.
	Knee = 22,
}

-- The player the prices are derived for (an average, active player).
local BASELINE = {
	-- Share of thrown sticks a player catches at Move Speed level 0, + per Move Speed level, at most MaxCatchRate.
	CatchRate = 0.6,
	CatchPerSpeedLevel = 0.03,
	MaxCatchRate = 0.9,
	-- Nobody catches more than this many sticks per second, + per Move Speed level (with many fast Shibas the rest is
	-- left for the intern and the basket).
	MaxCatchesPerSecond = 1,
	CatchesPerSecondPerSpeedLevel = 0.05,
	-- Average multiplier of a caught stick from catch quality, head hits and combo (see Bonk below).
	ActiveBonus = 2,
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
-- the Shiny and Mythic editions reuse the ten models with an outline and aura in their Color.
-- Height = model height in studs. FireInterval = seconds between two throws of one Shiba.
export type ShibaDef = {
	Name: string,
	AssetName: string,
	-- nil for the ten originals, else "Shiny" or "Mythic".
	Edition: string?,
	Height: number,
	Color: Color3,
	FireInterval: number,
	-- Derived (filled in below).
	RewardMultiplier: number,
}

local BASE_SHIBAS = {
	{ Name = "Shiba", AssetName = "Shiba", Height = 6, Color = Color3.fromRGB(255, 170, 60) },
	{ Name = "Shades Shiba", AssetName = "ShadesShiba", Height = 6, Color = Color3.fromRGB(160, 160, 185) },
	{ Name = "Buff Shiba", AssetName = "BuffShiba", Height = 7.5, Color = Color3.fromRGB(255, 110, 90) },
	{ Name = "Chef Shiba", AssetName = "ChefShiba", Height = 7.5, Color = Color3.fromRGB(250, 250, 250) },
	{ Name = "Police Shiba", AssetName = "PoliceShiba", Height = 6.5, Color = Color3.fromRGB(70, 130, 255) },
	{ Name = "Ninja Shiba", AssetName = "NinjaShiba", Height = 5.5, Color = Color3.fromRGB(220, 40, 60) },
	{ Name = "Gold Shiba", AssetName = "GoldShiba", Height = 6.5, Color = Color3.fromRGB(255, 200, 40) },
	{ Name = "Galaxy Shiba", AssetName = "GalaxyShiba", Height = 7, Color = Color3.fromRGB(170, 90, 255) },
	{ Name = "Giant Shiba", AssetName = "GiantShiba", Height = 16, Color = Color3.fromRGB(255, 130, 40) },
	{ Name = "Cheems God", AssetName = "CheemsGod", Height = 12, Color = Color3.fromRGB(255, 240, 170) },
}

-- Editions after the ten originals, in order. Their Colors (one per base Shiba) are the outline/aura colours.
local EDITIONS = {
	{
		Edition = "Shiny",
		Colors = {
			Color3.fromRGB(255, 235, 120),
			Color3.fromRGB(200, 255, 255),
			Color3.fromRGB(255, 160, 200),
			Color3.fromRGB(255, 255, 200),
			Color3.fromRGB(150, 220, 255),
			Color3.fromRGB(255, 120, 150),
			Color3.fromRGB(255, 250, 180),
			Color3.fromRGB(220, 170, 255),
			Color3.fromRGB(255, 200, 120),
			Color3.fromRGB(255, 255, 255),
		},
	},
	{
		Edition = "Mythic",
		Colors = {
			Color3.fromRGB(255, 60, 200),
			Color3.fromRGB(60, 255, 220),
			Color3.fromRGB(255, 80, 40),
			Color3.fromRGB(120, 255, 90),
			Color3.fromRGB(80, 120, 255),
			Color3.fromRGB(200, 0, 255),
			Color3.fromRGB(255, 170, 0),
			Color3.fromRGB(0, 200, 255),
			Color3.fromRGB(255, 40, 90),
			Color3.fromRGB(255, 225, 90),
		},
	},
}

-- Throw interval of the first and the last Shiba; the ones between are spread geometrically.
local FIRST_FIRE_INTERVAL = 5
local LAST_FIRE_INTERVAL = 1.2

-- Projectile tiers (Config/Projectiles has names and models, same order): BaseReward of the first one, and the
-- factor from one tier to the next. PROJECTILE_TIERS must match Config/Projectiles → Tiers.
local PROJECTILE_TIERS = 10
local FIRST_PROJECTILE_REWARD = 10
local PROJECTILE_GROWTH = 2.5

-- Automation (docs/GAME_DESIGN.md → Automation). Per level (level 1 = unlocked). Only sticks the player does not
-- catch are left for them: the intern goes for them first, the basket gets what the intern misses.
local AUTOMATION = {
	Basket = {
		-- Chance that a stick nobody caught ends up in the basket.
		CatchChance = { 0.2, 0.28, 0.36, 0.44, 0.52, 0.6 },
		-- Pays this share of a Normal bonk.
		Payout = { 0.3, 0.34, 0.38, 0.42, 0.46, 0.5 },
		-- Offline earnings (Shiba Bank) are capped at this many hours.
		OfflineHours = { 2, 3, 4, 5, 6, 8 },
	},
	Intern = {
		Names = { "Bonk Intern", "Hard-Hat Intern", "Junior Bonker", "Senior Bonker", "Bonk Manager", "Bonk CEO" },
		WalkSpeed = { 12, 14, 16, 18, 20, 22 },
		Payout = { 0.6, 0.65, 0.7, 0.75, 0.8, 0.85 },
		-- Sticks per second the intern is expected to reach (used for pricing and the simulation only; in the game it
		-- depends on where the sticks land and its WalkSpeed).
		ExpectedCatchesPerSecond = { 0.3, 0.4, 0.5, 0.6, 0.7, 0.8 },
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
-- little income are cheaper so they still pay for themselves). Shooters starts at 0: the first purchase of the game
-- is the second Shiba (the NEW SHIBA pad in front of the spawn).
export type RouteSpec = {
	Upgrade: string,
	Count: number,
	From: number,
	To: number,
	PriceShare: number,
}

local ROUTE_SPECS: { RouteSpec } = {
	{ Upgrade = "Shooters", Count = 7, From = 0, To = 0.5, PriceShare = 1 },
	{ Upgrade = "ShooterTier", Count = #BASE_SHIBAS * (1 + #EDITIONS) - 1, From = 0.02, To = 1, PriceShare = 1 },
	{ Upgrade = "ProjectileTier", Count = PROJECTILE_TIERS - 1, From = 0.04, To = 0.85, PriceShare = 1 },
	{ Upgrade = "MoveSpeed", Count = 10, From = 0.05, To = 0.8, PriceShare = 0.25 },
	{ Upgrade = "Basket", Count = #AUTOMATION.Basket.CatchChance, From = 0.3, To = 0.9, PriceShare = 0.5 },
	{ Upgrade = "Intern", Count = #AUTOMATION.Intern.Payout, From = 0.36, To = 0.94, PriceShare = 0.5 },
}

-- Levels past the Route (e.g. More Shibas with the +2 Shiba Slots pass) are priced by continuing the last two
-- prices' ratio for this many levels.
local EXTRA_LEVELS = 2

-- Trophies for total Bonk Dollars ever earned (Config/Shop → Trophies).
local TROPHY_THRESHOLDS = {
	Wood = 1e4,
	Bronze = 1e8,
	Silver = 1e14,
	Gold = 1e22,
	Galaxy = 1e30,
}

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
-- Round 1 = the ten originals, round n = EDITIONS[n - 1].
for round = 1, 1 + #EDITIONS do
	local edition = if round > 1 then EDITIONS[round - 1] else nil
	for baseIndex, base in BASE_SHIBAS do
		table.insert(shibas, {
			Name = if edition then `{edition.Edition} {base.Name}` else base.Name,
			AssetName = base.AssetName,
			Edition = if edition then edition.Edition else nil,
			Height = base.Height,
			Color = if edition then edition.Colors[baseIndex] else base.Color,
			FireInterval = 0,
			RewardMultiplier = 1,
		})
	end
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

-- Bonk Dollars per second of the Baseline player at these upgrade levels (active play + automation), without
-- rebirth, boosts or passes. `idleOnly` = the player catches nothing (AFK): only the intern and basket earn.
-- Used to derive prices and by the simulation.
function EconomyConfig.BaselineIncome(levels: Levels, idleOnly: boolean?): number
	local shibaCount = 1 + (levels.Shooters or 0)
	local shiba = shibas[math.clamp((levels.ShooterTier or 0) + 1, 1, #shibas)]
	local reward = projectileRewards[math.clamp((levels.ProjectileTier or 0) + 1, 1, #projectileRewards)]
	local sticksPerSecond = shibaCount / shiba.FireInterval
	local value = reward * shiba.RewardMultiplier
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
		then math.min(missed, AUTOMATION.Intern.ExpectedCatchesPerSecond[internLevel])
		else 0
	local internPay = if internLevel > 0 then AUTOMATION.Intern.Payout[internLevel] else 0
	local byBasket = if basketLevel > 0 then (missed - byIntern) * AUTOMATION.Basket.CatchChance[basketLevel] else 0
	local basketPay = if basketLevel > 0 then AUTOMATION.Basket.Payout[basketLevel] else 0
	return value * (caught * BASELINE.ActiveBonus + byIntern * internPay + byBasket * basketPay)
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
		step.Price = tidy(incomes[index] * step.TargetSeconds * shareOf[step.Upgrade])
	end
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
EconomyConfig.RouteSpecs = ROUTE_SPECS
EconomyConfig.TrophyThresholds = TROPHY_THRESHOLDS

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
