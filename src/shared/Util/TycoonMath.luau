--!strict
-- Pure tycoon formulas (docs/decisions/0006): income of a lane, level costs, egg rolls, merge results. No side effects
-- on require; used by TycoonService (server), the client for display, and docs/economy/tycoon_sim.luau.
-- Everything is computed from the saved Types.TycoonState, so server and client always agree on the numbers.

local Config = require(script.Parent.Parent.Config.Tycoon)
local Types = require(script.Parent.Parent.Types)

type TycoonState = Types.TycoonState

local LANE = Config.Lane

local TycoonMath = {}

function TycoonMath.TierIncome(tier: number): number
	return LANE.BaseIncome * LANE.TierGrowth ^ tier
end

function TycoonMath.LevelCap(ascensions: number): number
	return math.min(LANE.LevelCapHard, LANE.LevelCapBase + LANE.LevelCapPerAscension * ascensions)
end

-- How many of the lane milestones (10 / 25 / 50) this level has reached.
function TycoonMath.MilestonesReached(level: number): number
	local count = 0
	for _, milestone in LANE.Milestones do
		if level >= milestone then
			count += 1
		end
	end
	return count
end

-- Income factor of an own level: +LevelBonus per level, doubled at every milestone, ×BeyondMult every BeyondStep levels
-- past the last milestone.
function TycoonMath.LevelMultiplier(level: number): number
	local base = 1 + LANE.LevelBonus * (level - 1)
	local milestones = LANE.MilestoneMult ^ TycoonMath.MilestonesReached(level)
	local last = LANE.Milestones[#LANE.Milestones]
	local beyond = LANE.BeyondMult ^ math.max(0, math.floor((level - last) / LANE.BeyondStep))
	return base * milestones * beyond
end

-- Cost of raising a Shiba of `tier` from `level` to `level + 1`.
function TycoonMath.LevelCost(tier: number, level: number): number
	return math.floor(TycoonMath.TierIncome(tier) * LANE.LevelCostSeconds * LANE.LevelCostGrowth ^ (level - 1))
end

-- Total cost of raising a Shiba by `count` levels, and the number of levels that really fit into `budget`
-- (count = 0 means "as many as affordable"), never above `cap`.
function TycoonMath.LevelUpPlan(
	tier: number,
	level: number,
	count: number,
	budget: number,
	cap: number
): (number, number)
	local levels, spent = 0, 0
	local limit = if count > 0 then count else math.huge
	while levels < limit and level + levels < cap do
		local cost = TycoonMath.LevelCost(tier, level + levels)
		if spent + cost > budget then
			break
		end
		spent += cost
		levels += 1
	end
	return levels, spent
end

function TycoonMath.ArchMultiplier(arches: number): number
	return Config.Arch.Mult ^ arches
end

-- Price of arch number `index` (1 or 2) over a lane holding a Shiba of `tier`.
function TycoonMath.ArchPrice(tier: number, index: number): number
	return math.floor(TycoonMath.TierIncome(tier) * Config.Arch.PriceSeconds[index])
end

-- Seconds one swing of a Shiba of `tier` takes: short for the first Shiba, longer (and paying more per swing) for higher tiers.
function TycoonMath.SwingTimer(tier: number): number
	local swing = Config.Swing
	return swing.Cooldown * swing.TimerGrowth ^ tier
end

-- Street mode: seconds a swing of a Shiba of `tier` takes at level 1 (the first Shiba is the fastest).
function TycoonMath.BaseCooldown(tier: number): number
	local swing = Config.Swing
	return math.min(swing.MaxBaseCooldown, swing.Cooldown + swing.CooldownPerTier * tier)
end

-- Street mode: the cooldown of a Shiba at `level`: BaseCooldown at level 1, shrinking geometrically to MinCooldown at the
-- street level cap (a few milliseconds when fully upgraded).
function TycoonMath.SwingCooldown(tier: number, level: number): number
	local swing = Config.Swing
	local base = TycoonMath.BaseCooldown(tier)
	local progress = math.clamp((level - 1) / (swing.StreetLevelCap - 1), 0, 1)
	return base * (swing.MinCooldown / base) ^ progress
end

-- Street mode: the money one hit pays before multipliers (bigger and rarer for higher Shibas).
function TycoonMath.BonkPayout(tier: number): number
	return TycoonMath.TierIncome(tier) * TycoonMath.BaseCooldown(tier)
end

-- The level cap that applies to this player's Shibas.
function TycoonMath.CapFor(tycoon: TycoonState): number
	if tycoon.Street == true then
		return Config.Swing.StreetLevelCap
	end
	return TycoonMath.LevelCap(tycoon.Ascensions)
end

-- Number of Shibas the player has bought the automation for.
function TycoonMath.AutomatedCount(tycoon: TycoonState): number
	local count = 0
	for _, shiba in tycoon.Shibas do
		if shiba.Automated == true then
			count += 1
		end
	end
	return count
end

-- Price of automating a Shiba of `tier` when `automated` Shibas already are.
function TycoonMath.AutomationPrice(tier: number, automated: number): number
	local swing = Config.Swing
	return math.floor(TycoonMath.TierIncome(tier) * swing.AutomationSeconds * swing.AutomationGrowth ^ automated)
end

-- Multiplier of all owned Mill rings.
function TycoonMath.RingsMultiplier(pads: { [string]: boolean }): number
	local mult = 1
	for _, ring in Config.Rings do
		if pads[ring.Id] then
			mult *= ring.Mult
		end
	end
	return mult
end

function TycoonMath.AscensionMultiplier(ascensions: number): number
	return 1 + Config.Ascension.PerAscension * ascensions
end

-- A Shiba can only be equipped once the zone of its egg is unlocked (zone z holds tiers 5z … 5z + 4). After an Ascension
-- the zones start over, so the collection is kept but only the first zone's Shibas can work at first.
function TycoonMath.IsEquippable(tycoon: TycoonState, tier: number): boolean
	return tier // Config.TiersPerZone <= tycoon.Zone
end

function TycoonMath.EggPrice(zone: number): number
	return Config.Zones[zone + 1].EggPrice
end

-- The tier an egg of `zone` gives for a roll in [0, 100) (Config.EggWeights, common → rare).
function TycoonMath.TierFromRoll(zone: number, roll: number): number
	local sum = 0
	for index, weight in Config.EggWeights do
		sum += weight
		if roll < sum then
			return zone * Config.TiersPerZone + index - 1
		end
	end
	return zone * Config.TiersPerZone + #Config.EggWeights - 1
end

local function shibaAt(tycoon: TycoonState, slot: number): Types.OwnedShiba?
	local id = tycoon.Equipped[tostring(slot)]
	return if id then tycoon.Shibas[id] else nil
end

-- Expected average income factor of a Shiba's own perk on its own lane (Burst / Chance / Rhythm / Synergy).
local function selfPerk(perk: Config.Perk, rings: number): number
	local kind = perk.Kind
	if kind == "Burst" then
		return 1 + ((perk.Mult or 1) - 1) * (perk.Duration or 0) / math.max(perk.Period or 1, 1)
	elseif kind == "Chance" then
		return 1 + (perk.Chance or 0) * ((perk.Mult or 1) - 1)
	elseif kind == "Rhythm" then
		return 1 + ((perk.Mult or 1) - 1) / math.max(perk.Every or 1, 1)
	elseif kind == "Synergy" then
		return rings
	end
	return 1
end

-- Income per second of the lane on equip `slot` (0 if empty), without pass / boost / event / friend multipliers.
function TycoonMath.LaneIncome(tycoon: TycoonState, slot: number): number
	local shiba = shibaAt(tycoon, slot)
	if not shiba then
		return 0
	end
	local perks = Config.Perks
	local rings = TycoonMath.RingsMultiplier(tycoon.Pads)
	-- Street mode: payout per hit divided by the level's cooldown; the island tycoon: tier income times the level multiplier.
	local base = if tycoon.Street == true
		then TycoonMath.BonkPayout(shiba.Tier) / TycoonMath.SwingCooldown(shiba.Tier, shiba.Level)
		else TycoonMath.TierIncome(shiba.Tier) * TycoonMath.LevelMultiplier(shiba.Level)
	local income = base
		* Config.VariantMult[shiba.Variant]
		* TycoonMath.ArchMultiplier(tycoon.Arches[tostring(slot)] or 0)
		* rings
		* TycoonMath.AscensionMultiplier(tycoon.Ascensions)
	income *= selfPerk(perks[shiba.Tier + 1], rings)

	-- Neighbours: on the ring (equip slots are spaced evenly over it) or, in street mode, the bays next to it (no wrap).
	local slots = tycoon.EquipSlots
	if slots > 1 then
		local street = tycoon.Street == true
		local previous = if street then slot - 1 else (slot - 2) % slots + 1
		local following = if street then slot + 1 else slot % slots + 1
		local bonus = 0
		for _, other in { previous, following } do
			local neighbour = if other >= 1 and other <= slots then shibaAt(tycoon, other) else nil
			if neighbour then
				local perk = perks[neighbour.Tier + 1]
				if perk.Kind == "Neighbors" then
					bonus += perk.Value or 0
				end
			end
		end
		-- With 2 slots previous and following are the same lane: count it once.
		if slots == 2 and not street then
			bonus /= 2
		end
		income *= 1 + bonus
	end
	return income
end

-- Extra factor for ALL lanes from "Global" perks: + Value per milestone the perk's own lane reached.
function TycoonMath.GlobalMultiplier(tycoon: TycoonState): number
	local extra = 0
	for slot = 1, tycoon.EquipSlots do
		local shiba = shibaAt(tycoon, slot)
		if shiba then
			local perk = Config.Perks[shiba.Tier + 1]
			if perk.Kind == "Global" then
				extra += (perk.Value or 0) * TycoonMath.MilestonesReached(shiba.Level)
			end
		end
	end
	return 1 + extra
end

-- Income per second of the whole ring.
function TycoonMath.TotalIncome(tycoon: TycoonState): number
	local sum = 0
	for slot = 1, tycoon.EquipSlots do
		sum += TycoonMath.LaneIncome(tycoon, slot)
	end
	return sum * TycoonMath.GlobalMultiplier(tycoon)
end

local VARIANT_RANK: { [string]: number } = { Normal = 0, Shiny = 1, Rainbow = 2, Huge = 3 }

-- Result of merging `source` into `target` (same tier): the target gains levels (up to `cap`) and keeps the better variant.
function TycoonMath.MergeResult(
	target: Types.OwnedShiba,
	source: Types.OwnedShiba,
	cap: number
): (number, Types.VariantId)
	local level = math.min(cap, target.Level + math.floor(source.Level * Config.MergeShare) + 1)
	local variant: Types.VariantId = target.Variant
	if VARIANT_RANK[source.Variant] > VARIANT_RANK[variant] then
		variant = source.Variant
	end
	return level, variant
end

return TycoonMath
