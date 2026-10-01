--!strict
-- Tycoon "Shiba Workers" tuning (docs/decisions/0006, docs/TYCOON_HANDOFF.md). Pure data, no requires: the same
-- file is loaded by the balancing simulation (docs/economy/tycoon_sim.luau). All prices are in Bonk Dollars.
-- Numbers are STARTING values, calibrated with the simulation to about 70-100 hours for everything; tune in playtests.

-- Price of unlocking zone 0 … 5 (calibrated with docs/economy/tycoon_sim.luau). Egg prices, Mill rings and equip slots
-- are derived from them so the whole economy scales together.
local ZONE_PRICES = { 0, 2.17e6, 3.67e9, 2.5e11, 2.6e15, 2e17 }
local ZONE_NAMES = { "Meadow", "Beach", "Forest", "Mountain", "Space", "Heaven" }
local EGG_SHARE = 200 -- an egg costs 1/EGG_SHARE of its zone's unlock price (zone 0: 50)

local function zoneEntry(index: number): { Name: string, Price: number, EggPrice: number }
	return {
		Name = ZONE_NAMES[index],
		Price = ZONE_PRICES[index],
		EggPrice = if index == 1 then 50 else ZONE_PRICES[index] / EGG_SHARE,
	}
end

local TIER_COUNT = 30 -- must equal #EconomyConfig.Shibas (TycoonService.Init asserts it)

-- Perks (one per Shiba tier). Kinds, all applied as EXPECTED average values on the server (the visible effects on the
-- client are flavour):
--   Global    Value = extra income for ALL lanes (added) per milestone the Shiba's own lane reached
--   Neighbors Value = extra income (fraction) for the two lanes next to it on the ring
--   Burst     Mult for Duration seconds every Period seconds (average = 1 + (Mult - 1) * Duration / Period)
--   Chance    each item has Chance to pay Mult times (average = 1 + Chance * (Mult - 1))
--   Rhythm    every Every-th item pays Mult times (average = 1 + (Mult - 1) / Every)
--   Synergy   the Mill rings' multiplier counts squared on its own lane
export type Perk = {
	Kind: string,
	Value: number?,
	Mult: number?,
	Duration: number?,
	Period: number?,
	Chance: number?,
	Every: number?,
}

local PERKS: { Perk } = {
	{ Kind = "Global", Value = 0.05 }, -- 1 Shiba: Pack Leader
	{ Kind = "Burst", Mult = 3, Duration = 4, Period = 20 }, -- 2 Shades: Cool Mode
	{ Kind = "Neighbors", Value = 0.25 }, -- 3 Buff: Spotter
	{ Kind = "Synergy" }, -- 4 Chef: Recipe
	{ Kind = "Rhythm", Mult = 5, Every = 10 }, -- 5 DJ/Police style: every 10th item
	{ Kind = "Rhythm", Mult = 5, Every = 10 }, -- 6
	{ Kind = "Burst", Mult = 4, Duration = 2, Period = 12 }, -- 7 fast bursts
	{ Kind = "Chance", Chance = 0.08, Mult = 10 }, -- 8
	{ Kind = "Neighbors", Value = 0.3 }, -- 9
	{ Kind = "Synergy" }, -- 10
}
-- Tiers 11 … 30 cycle through the kinds with slowly growing strength.
do
	local kinds = { "Burst", "Neighbors", "Chance", "Synergy", "Global", "Rhythm" }
	for tier = #PERKS + 1, TIER_COUNT do
		local kind = kinds[(tier - 1) % #kinds + 1]
		local strength = 1 + (tier - 10) * 0.03
		local perk: Perk
		if kind == "Burst" then
			perk = { Kind = kind, Mult = 4 * strength, Duration = 3, Period = 12 }
		elseif kind == "Neighbors" then
			perk = { Kind = kind, Value = 0.3 * strength }
		elseif kind == "Chance" then
			perk = { Kind = kind, Chance = 0.1, Mult = 10 * strength }
		elseif kind == "Global" then
			perk = { Kind = kind, Value = 0.05 * strength }
		elseif kind == "Rhythm" then
			perk = { Kind = kind, Mult = 6 * strength, Every = 8 }
		else
			perk = { Kind = kind }
		end
		table.insert(PERKS, perk)
	end
end

return {
	TierCount = TIER_COUNT,
	Perks = PERKS,

	-- Equip slots (ring positions): the player starts with StartEquipSlots and can grow up to MaxEquipSlots.
	StartEquipSlots = 3,
	MaxEquipSlots = 10,
	-- Price of equip slot n (slot 4 … 10), bought with the pad "Slot<n>".
	SlotPrices = {
		[4] = ZONE_PRICES[2] / 10,
		[5] = ZONE_PRICES[2] / 2,
		[6] = ZONE_PRICES[3] / 10,
		[7] = ZONE_PRICES[3] / 2,
		[8] = ZONE_PRICES[4] / 10,
		[9] = ZONE_PRICES[5] / 10,
		[10] = ZONE_PRICES[6] / 10,
	} :: { [number]: number },

	Lane = {
		-- Income per second of a level-1 tier-0 Shiba, and the factor between neighbouring tiers.
		BaseIncome = 1,
		TierGrowth = 2.7,
		-- Each level adds this share of the level-1 income.
		LevelBonus = 0.08,
		-- Levels at which the lane's income doubles; after the last one every BeyondStep levels multiply it by BeyondMult.
		Milestones = { 10, 25, 50 },
		MilestoneMult = 2,
		BeyondStep = 25,
		BeyondMult = 1.5,
		-- Level cap: LevelCapBase + LevelCapPerAscension × ascensions (hard ceiling for saved data: LevelCapHard).
		LevelCapBase = 50,
		LevelCapPerAscension = 10,
		LevelCapHard = 500,
		-- Cost of level L → L + 1 = TierIncome(tier) × LevelCostSeconds × LevelCostGrowth^(L - 1).
		LevelCostSeconds = 20,
		LevelCostGrowth = 1.17,
	},

	-- Arches over a lane: each multiplies that lane's income. Price = the lane's level-1 income × seconds.
	Arch = { Max = 2, Mult = 1.5, PriceSeconds = { 900, 5400 } },

	-- Swing, click start, automation and the Bonk hit (docs/GAME_DESIGN.md → Swing, click and Bonk hit). Starting values.
	Swing = {
		-- Seconds between swings of one Shiba; a click pays this many seconds of the lane's income.
		Cooldown = 1,
		-- Seconds from the start of the swing until the stick lands (payout of a click and the hit check).
		HitDelay = 0.5,
		-- Hit zone in front of the Shiba: length in studs, half angle in degrees, height tolerance in studs.
		HitRange = 8,
		HitHalfAngle = 45,
		HitHeight = 8,
		-- The fling of a bonked owner: speed in studs/s and the upward share of the direction (applied by the client).
		LaunchSpeed = 18,
		LaunchLift = 0.2,
		-- A Bonk hit pays this many seconds of the lane's income; seconds between Bonk hits per player.
		BonusSeconds = 10,
		BonusCooldown = 5,
		-- Automation price = TierIncome * AutomationSeconds * AutomationGrowth ^ (Shibas already automated).
		AutomationSeconds = 60,
		AutomationGrowth = 1.5,
		-- One swing of a Shiba of tier t takes Cooldown * TimerGrowth ^ t seconds and pays income per second * that time: the
		-- first Shiba is the fastest, higher ones pay more per click but slower. The income per second does not change.
		TimerGrowth = 1.12,

		-- Street mode ("Gameplay flow"): one hit pays BonkPayout(tier) = TierIncome(tier) * BaseCooldown(tier) (before
		-- multipliers). BaseCooldown(tier) = Cooldown + CooldownPerTier * tier seconds (at most MaxBaseCooldown): the first Shiba
		-- 1 s, higher Shibas wait longer but pay more. Every upgrade level shrinks the cooldown geometrically from there to
		-- MinCooldown at StreetLevelCap (the first Shiba bonks every 20 ms when fully upgraded).
		CooldownPerTier = 8,
		MaxBaseCooldown = 240,
		-- The lowest cooldown a Shiba can reach: MinCooldown for the first Shiba, times MinCooldownGrowth for every tier above it
		-- (20 ms, 0.18 s at Shiba 10, 2 s at Shiba 20, 25 s at Shiba 30), so higher Shibas stay slower even fully upgraded.
		MinCooldown = 0.02,
		MinCooldownGrowth = 1.28,
		-- Every upgrade level also raises the payout per hit by this share of the level-1 payout (linear: $1, $2, $3 ... per hit
		-- for the first Shiba, so an upgrade is felt at once).
		PayoutPerLevel = 1,
		-- Street mode level costs (TycoonMath.LevelCost): an upgrade costs StreetLevelSeconds of the Shiba's OWN income at its current
		-- level (so the first upgrade of the first Shiba, earning 1 per second, is 8 clicks away), growing by StreetLevelGrowth per
		-- level: the better a Shiba already is, the longer its next upgrade takes.
		StreetLevelSeconds = 8,
		StreetLevelGrowth = 1.05,
		StreetLevelCap = 100,
		-- The stick lands this share of the cooldown after the swing starts, at most HitDelay seconds.
		HitDelayShare = 0.45,
		-- Street mode: popups, knockback and the swings of automated Shibas happen at most this often (seconds), however short
		-- the cooldown is. The money is not capped: every hit pays, automated Shibas pay through the income tick.
		EffectInterval = 0.25,
	},

	-- Street mode (docs/GAME_DESIGN.md → Street, plots and buttons, "One Shiba per expansion"). Prices are placeholders
	-- until the simulation is rebuilt for 30 bays.
	Street = {
		-- One bay and one Shiba per expansion (must equal #EconomyConfig.Shibas).
		Bays = 30,
		-- Floor pads shown at the same time.
		MaxPads = 3,
		-- Street mode has its own income scale (the island tycoon keeps Lane.BaseIncome / TierGrowth): the base income of Shiba n
		-- (level 1) is BaseIncome * TierGrowth ^ (n - 1) per second, TycoonMath.StreetTierIncome.
		BaseIncome = 1,
		TierGrowth = 4,
		-- Prices are counted in seconds of the income a Shiba earns at ReadyLevel (TycoonMath.StreetReadyIncome), because levels
		-- multiply a Shiba's income far more than its tier does: the Shiba of a bay at ReadyLevel is what the player typically has
		-- when the next purchase is due.
		ReadyLevel = 25,
		-- Stage n = the decor of bay n plus the expansion to bay n + 1. StageFactor[n] multiplies the prices of that stage (default 1);
		-- it is calibrated with docs/economy/street_sim so that every stage takes the intended time (it grows from stage to stage).
		-- Level costs also grow with the tier: LevelCost is multiplied by StageFactor[tier + 1] ^ LevelFactorPower, so the upgrades of a
		-- higher Shiba stay in proportion to its (much higher) price.
		LevelFactorPower = 0.9,
		StageFactor = {
			1, -- stage 1
			4.778, -- stage 2
			7.189, -- stage 3
			6.355, -- stage 4
			7.626, -- stage 5
			10.47, -- stage 6
			11.06, -- stage 7
			13.27, -- stage 8
			13.95, -- stage 9
			12.51, -- stage 10
			11.83, -- stage 11
			16.99, -- stage 12
			25.46, -- stage 13
			30.56, -- stage 14
			36.67, -- stage 15
			38.66, -- stage 16
			33.38, -- stage 17
			43.5, -- stage 18
			67.2, -- stage 19
			80.64, -- stage 20
			168.3, -- stage 21
			166.1, -- stage 22
			120.8, -- stage 23
			133.2, -- stage 24
			212.4, -- stage 25
			241.8, -- stage 26
			346, -- stage 27
			316.2, -- stage 28
			241.9, -- stage 29
		} :: { [number]: number },
		-- Expansion n (n >= 2) costs StreetReadyIncome(n - 2) * BaySeconds * StageFactor[n - 1] (the Shiba before it); the first one is free.
		BaySeconds = 300,
		-- A decor part costs StreetReadyIncome(bay - 1) * its PriceSeconds * DecorScale * StageFactor[bay].
		DecorScale = 0.1,
		-- The Bonk Intern of a Shiba costs StreetReadyIncome * AutomationSeconds * AutomationGrowth ^ (Shibas already automated).
		AutomationSeconds = 60,
		AutomationGrowth = 1.08,
		-- The Bonk Intern of the first Shiba, bought before any other Intern, costs only this much, so the first automation comes early.
		AutomationFirstPrice = 300,
		-- Decor is bought in this many parallel chains, so this many decor pads are visible at once (Util/TycoonSteps).
		DecorChains = 2,
	},

	-- Mill rings (pads "Sorter", "Polisher", "Refinery"): each multiplies ALL lanes.
	Rings = {
		{ Id = "Sorter", Mult = 1.25, Price = ZONE_PRICES[3] / 20 },
		{ Id = "Polisher", Mult = 1.25, Price = ZONE_PRICES[4] / 20 },
		{ Id = "Refinery", Mult = 1.25, Price = ZONE_PRICES[5] / 20 },
	},

	-- Zones: each has one egg with 5 Shiba tiers (zone z holds tiers 5z … 5z + 4). Zone 0 is free.
	Zones = {
		zoneEntry(1),
		zoneEntry(2),
		zoneEntry(3),
		zoneEntry(4),
		zoneEntry(5),
		zoneEntry(6),
	},
	TiersPerZone = 5,
	-- Chance in percent for the 5 tiers of an egg, common → rare (sums to 100).
	EggWeights = { 60, 25, 10, 4, 1 },
	HatchCounts = { 1, 3, 10 },

	-- Variant income multipliers (Normal … Huge), same as EconomyConfig.Variants.Multiplier.
	VariantMult = { Normal = 1, Shiny = 1.5, Rainbow = 3, Huge = 6 } :: { [string]: number },

	-- Merging two Shibas of the same tier: the target gains floor(source level × MergeShare) + 1 levels.
	MergeShare = 0.5,

	-- Ascension (pad "Ascend"): needs the last zone's egg unlocked. Resets money, Shiba levels, arches, rings, zones and
	-- equip slots above the start count; keeps the collection, variants, Index, trophies, quests, streaks.
	Ascension = { MinZone = 5, PerAscension = 0.75 },

	-- Sanity limits for saved data.
	MaxZone = 5,
	MaxOwnedShibas = 2000,
	MaxPads = 500,
	MaxEggIds = 100,
	MaxIdLength = 40,
}
