-- Balancing simulation of the tycoon ("Shiba Workers", docs/decisions/0006). Loads the real Config/Tycoon and
-- Util/TycoonMath, so it always matches the game's numbers. Run from the repo root:  lune run docs/economy/tycoon_sim.luau
--
-- Player model (a solo, efficient, always-online player; no passes, boosts, events, friends, crates or lucky variants):
-- always takes the action with the shortest "wait until affordable + payback" time: level up an equipped Shiba, hatch an
-- egg (expected gain over 20 evenly spread rolls, worth EGG_PULL times its immediate gain: collection value), buy an equip
-- slot, arch or Mill ring. Zones are unlocked once their price is within ZONE_HORIZON seconds of income. Shibas are
-- always re-equipped best-first. Duplicates are merged. Real players are slower (breaks, mistakes): read the totals as a
-- lower bound and check them against the 70-100 hour target with a factor of about 1.3-1.6.

local fs = require("@lune/fs")
local process = require("@lune/process")
local luau = require("@lune/luau")

local EGG_PULL = 3
-- Test knob: PRICE_SCALE=10 lune run docs/economy/tycoon_sim multiplies every zone / egg / ring / slot price.
local PRICE_SCALE = tonumber(process.env.PRICE_SCALE) or 1
local ZONE_HORIZON = 1800
local RUNS = 4 -- the first run plus 3 ascensions

local function loadModule(path: string, requires: { [string]: any })
	local chunk = luau.load(fs.readFile(path), {
		debugName = path,
		environment = {
			-- TycoonMath requires its Config and Types by relative path: hand them over by call order.
			require = function(_value: any)
				return table.remove(requires, 1)
			end,
			script = setmetatable({}, {
				__index = function(self)
					return self
				end,
			}),
		},
		injectGlobals = true,
	})
	return chunk()
end

local Config = loadModule("src/shared/Config/Tycoon.luau", {})
if PRICE_SCALE ~= 1 then
	for _, zone in Config.Zones do
		zone.Price *= PRICE_SCALE
		zone.EggPrice *= PRICE_SCALE
	end
	for _, ring in Config.Rings do
		ring.Price *= PRICE_SCALE
	end
	for slot, price in Config.SlotPrices do
		Config.SlotPrices[slot] = price * PRICE_SCALE
	end
end
local Math = loadModule("src/shared/Util/TycoonMath.luau", { Config, {} })

local function fmtTime(s: number): string
	if s < 90 then
		return string.format("%.1f s", s)
	elseif s < 5400 then
		return string.format("%.1f min", s / 60)
	end
	return string.format("%.2f h", s / 3600)
end

local SUFFIX = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc", "UDc", "DDc", "TDc", "QaDc", "QiDc" }
local function fmtNum(v: number): string
	if v < 1000 then
		return string.format("%.3g", v)
	end
	local group = math.min(math.floor(math.log10(v) / 3), #SUFFIX - 1)
	return string.format("%.3g%s", v / 10 ^ (group * 3), SUFFIX[group + 1])
end

local function newState()
	return {
		Shibas = {},
		NextShibaId = 1,
		Equipped = {},
		EquipSlots = Config.StartEquipSlots,
		Arches = {},
		Pads = {},
		Zone = -1, -- no zone yet; zone 0 is free and unlocked at the start
		Ascensions = 0,
	}
end

local function copyState(state)
	local copy = {
		Shibas = {},
		NextShibaId = state.NextShibaId,
		Equipped = {},
		EquipSlots = state.EquipSlots,
		Arches = {},
		Pads = state.Pads,
		Zone = state.Zone,
		Ascensions = state.Ascensions,
	}
	for id, shiba in state.Shibas do
		copy.Shibas[id] = { Tier = shiba.Tier, Level = shiba.Level, Variant = shiba.Variant }
	end
	for slot, id in state.Equipped do
		copy.Equipped[slot] = id
	end
	for slot, count in state.Arches do
		copy.Arches[slot] = count
	end
	return copy
end

-- Re-equips the best Shibas (by potential) into the slots.
local function equipBest(state)
	local list = {}
	for id, shiba in state.Shibas do
		-- A Shiba can only be equipped once its zone is unlocked.
		if shiba.Tier // Config.TiersPerZone > math.max(state.Zone, 0) then
			continue
		end
		table.insert(list, {
			Id = id,
			Potential = Math.TierIncome(shiba.Tier)
				* Math.LevelMultiplier(shiba.Level)
				* Config.VariantMult[shiba.Variant],
		})
	end
	table.sort(list, function(a, b)
		return a.Potential > b.Potential
	end)
	state.Equipped = {}
	for slot = 1, math.min(state.EquipSlots, #list) do
		state.Equipped[tostring(slot)] = list[slot].Id
	end
end

local function income(state): number
	return Math.TotalIncome(state)
end

-- Adds the Shiba an egg roll gives (merging duplicates) and re-equips.
local function applyHatch(state, tier: number)
	local best
	for _, shiba in state.Shibas do
		if shiba.Tier == tier and (not best or shiba.Level > best.Level) then
			best = shiba
		end
	end
	local cap = Math.LevelCap(state.Ascensions)
	if best then
		best.Level = math.min(cap, best.Level + math.floor(1 * Config.MergeShare) + 1)
	else
		state.Shibas["s" .. state.NextShibaId] = { Tier = tier, Level = 1, Variant = "Normal" }
		state.NextShibaId += 1
	end
	equipBest(state)
end

local function highestZone(state, money: number, rate: number): number
	local best = 0
	for zone = 0, math.max(state.Zone, 0) do
		if Config.Zones[zone + 1].EggPrice <= rate * 1800 or zone == 0 then
			best = zone
		end
	end
	return best
end

-- Candidate actions: { Cost, Delta, Apply }. Delta = income gain per second.
local function candidates(state, rate: number)
	local list = {}
	local cap = Math.LevelCap(state.Ascensions)

	for slot = 1, state.EquipSlots do
		local id = state.Equipped[tostring(slot)]
		local shiba = id and state.Shibas[id]
		if shiba then
			if shiba.Level < cap then
				local cost = Math.LevelCost(shiba.Tier, shiba.Level)
				shiba.Level += 1
				local after = income(state)
				shiba.Level -= 1
				table.insert(list, {
					Cost = cost,
					Delta = after - rate,
					Apply = function()
						shiba.Level += 1
					end,
				})
			end
			local arches = state.Arches[tostring(slot)] or 0
			if arches < Config.Arch.Max then
				local cost = Math.ArchPrice(shiba.Tier, arches + 1)
				state.Arches[tostring(slot)] = arches + 1
				local after = income(state)
				state.Arches[tostring(slot)] = arches
				table.insert(list, {
					Cost = cost,
					Delta = after - rate,
					Apply = function()
						state.Arches[tostring(slot)] = arches + 1
					end,
				})
			end
		end
	end

	-- Mill rings.
	for _, ring in Config.Rings do
		if not state.Pads[ring.Id] then
			state.Pads[ring.Id] = true
			local after = income(state)
			state.Pads[ring.Id] = nil
			table.insert(list, {
				Cost = ring.Price,
				Delta = after - rate,
				Apply = function()
					state.Pads[ring.Id] = true
				end,
			})
		end
	end

	-- Equip slot.
	if state.EquipSlots < Config.MaxEquipSlots then
		local price = Config.SlotPrices[state.EquipSlots + 1]
		local trial = copyState(state)
		trial.EquipSlots += 1
		equipBest(trial)
		table.insert(list, {
			Cost = price,
			Delta = income(trial) - rate,
			Apply = function()
				state.EquipSlots += 1
				equipBest(state)
			end,
		})
	end

	-- Egg of the best sensible zone.
	if state.Zone >= 0 then
		local zone = highestZone(state, 0, rate)
		local price = Math.EggPrice(zone)
		local gain = 0
		for step = 1, 20 do
			local trial = copyState(state)
			applyHatch(trial, Math.TierFromRoll(zone, (step - 0.5) * 5))
			gain += (income(trial) - rate) / 20
		end
		table.insert(list, {
			Cost = price,
			Delta = gain * EGG_PULL,
			Apply = function()
				-- The real roll: a fixed pseudo-random sequence so runs are reproducible.
				state.Seed = (state.Seed * 1103515245 + 12345) % 2147483648
				applyHatch(state, Math.TierFromRoll(zone, state.Seed / 2147483648 * 100))
			end,
		})
	end
	return list
end

local function allOwned(state): boolean
	local seen = 0
	local tiers = {}
	for _, shiba in state.Shibas do
		if not tiers[shiba.Tier] then
			tiers[shiba.Tier] = true
			seen += 1
		end
	end
	return seen >= Config.TierCount
end

local function isMaxed(state): boolean
	local cap = Math.LevelCap(state.Ascensions)
	if not allOwned(state) or state.EquipSlots < Config.MaxEquipSlots or state.Zone < Config.MaxZone then
		return false
	end
	for slot = 1, state.EquipSlots do
		local id = state.Equipped[tostring(slot)]
		local shiba = id and state.Shibas[id]
		if not shiba or shiba.Level < cap or (state.Arches[tostring(slot)] or 0) < Config.Arch.Max then
			return false
		end
	end
	for _, ring in Config.Rings do
		if not state.Pads[ring.Id] then
			return false
		end
	end
	return true
end

local function report(label: string, t: number, rate: number, extra: string?)
	print(string.format("  %-34s %-10s income %-9s/s %s", label, fmtTime(t), fmtNum(rate), extra or ""))
end

local time = 0
local money = Math.EggPrice(0) -- the first egg
local state = newState()
state.Seed = 12345
state.Zone = 0
local zoneReported = {}
local allOwnedReported = false
local ascensionTimes = {}

for run = 1, RUNS do
	print(
		string.format(
			"== Run %d (ascensions done: %d, level cap %d)",
			run,
			state.Ascensions,
			Math.LevelCap(state.Ascensions)
		)
	)
	local runStart = time
	local steps = 0
	while not isMaxed(state) and steps < 3000000 do
		steps += 1
		local rate = income(state)
		-- Zone unlock policy.
		local nextZone = state.Zone + 1
		if nextZone <= Config.MaxZone then
			local price = Config.Zones[nextZone + 1].Price
			if price <= math.max(rate, 1) * ZONE_HORIZON and money >= price then
				money -= price
				state.Zone = nextZone
				report(
					string.format("zone %d (%s) unlocked", nextZone, Config.Zones[nextZone + 1].Name),
					time - runStart,
					rate
				)
				continue
			end
		end
		if rate <= 0 then
			-- Nothing equipped yet: buy the first egg.
			local price = Math.EggPrice(0)
			if money < price then
				time += 1
				continue
			end
			money -= price
			applyHatch(state, Math.TierFromRoll(0, 10))
			continue
		end
		local best, bestScore
		for _, action in candidates(state, rate) do
			if action.Delta > 0 then
				local wait = math.max(0, action.Cost - money) / rate
				local score = wait + action.Cost / action.Delta
				if not bestScore or score < bestScore then
					best, bestScore = action, score
				end
			end
		end
		-- A pending zone unlock can be the better goal: wait for it when the best score is worse than the zone's.
		if nextZone <= Config.MaxZone then
			local price = Config.Zones[nextZone + 1].Price
			local wait = math.max(0, price - money) / rate
			if price <= rate * ZONE_HORIZON and (not bestScore or wait < bestScore) then
				time += wait
				money += wait * rate
				continue
			end
		end
		if not best then
			-- Nothing left that pays: wait for the next zone, whatever it costs.
			if nextZone <= Config.MaxZone then
				local price = Config.Zones[nextZone + 1].Price
				local wait = math.max(0, price - money) / rate
				time += wait
				money += wait * rate - price
				state.Zone = nextZone
				report(
					string.format("zone %d (%s) unlocked", nextZone, Config.Zones[nextZone + 1].Name),
					time - runStart,
					income(state)
				)
				continue
			end
			-- Everything that pays is bought: hatch eggs for the collection (Index) until every type is owned.
			if not allOwned(state) then
				local zone = highestZone(state, 0, rate)
				-- The zone with an unowned tier, cheapest first.
				local found = false
				for candidate = 0, state.Zone do
					if found then
						break
					end
					for index = 0, Config.TiersPerZone - 1 do
						local tier = candidate * Config.TiersPerZone + index
						local owned = false
						for _, shiba in state.Shibas do
							owned = owned or shiba.Tier == tier
						end
						if not owned then
							zone = candidate
							found = true
							break
						end
					end
				end
				local price = Math.EggPrice(zone)
				local wait = math.max(0, price - money) / rate
				time += wait
				money += wait * rate - price
				state.Seed = (state.Seed * 1103515245 + 12345) % 2147483648
				applyHatch(state, Math.TierFromRoll(zone, state.Seed / 2147483648 * 100))
				continue
			end
			break
		end
		local wait = math.max(0, best.Cost - money) / rate
		time += wait
		money += wait * rate - best.Cost
		best.Apply()
		if not allOwnedReported and allOwned(state) then
			allOwnedReported = true
			report("all 30 Shiba types owned", time - runStart, income(state))
		end
	end
	report(if isMaxed(state) then "MAXED (this run's cap)" else "stopped (step limit)", time - runStart, income(state))
	table.insert(ascensionTimes, time)
	if run < RUNS then
		-- Ascend: reset money, levels, arches, rings, zones, equip slots; keep the collection.
		state.Ascensions += 1
		for _, shiba in state.Shibas do
			shiba.Level = 1
		end
		state.Arches = {}
		state.Pads = {}
		state.Zone = 0
		state.EquipSlots = Config.StartEquipSlots
		equipBest(state)
		money = Math.EggPrice(0)
		allOwnedReported = true
	end
end
print(string.format("Total simulated time for %d runs: %s", RUNS, fmtTime(time)))
