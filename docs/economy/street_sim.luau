-- Balancing simulation of the STREET tycoon (30 bays, one Shiba per expansion, automation pads; docs/GAME_DESIGN.md ->
-- "Street, plots and buttons" and "One Shiba per expansion"). Loads the real Config/Tycoon, Util/TycoonMath and
-- Util/TycoonSteps (Price), so it always matches the game's formulas. Run from the repo root:
--   lune run docs/economy/street_sim            -- current constants vs the recommended ones, both player types
--   SWEEP=1 lune run docs/economy/street_sim    -- grid over BaySeconds x AutomationSeconds x AutomationGrowth (slow)
--   BAY_SECONDS=40 AUTO_SECONDS=60 AUTO_GROWTH=1.5 LEVEL_COST_GROWTH=1.17 TIER_GROWTH=2.7 lune run docs/economy/street_sim
--     -- one run with overridden constants (environment variables, every one optional)
--
-- Model. Bay 1 is free. Expansion n (n >= 2) costs TycoonSteps.Price(Bay n) = floor(TierIncome(n - 1) * BaySeconds) and
-- spawns Shiba n (tier n - 1, level 1, not automated). Pad Auto n automates a Shiba: TycoonMath.AutomationPrice(tier,
-- Shibas already automated). Every spawned Shiba works at once; lane income = TycoonMath.LaneIncome * GlobalMultiplier
-- (real perks, neighbours and milestones included; arches, rings and ascension are not available / not modelled).
-- An automated Shiba pays its lane rate continuously. A click pays income per second * SwingTimer(tier), so clicking
-- non-stop also pays exactly the lane rate: the player earns ClickEff * (sum of the lane rates of the ClickTargets best
-- un-automated Shibas) on top of the automated lanes (ClickEff = share of time really spent clicking, walking and
-- stepping on pads included). Levels cost TycoonMath.LevelCost (one at a time).
--
-- Policy (greedy, both player types): whenever the player has a goal, pick the purchase with the smallest
-- "seconds until affordable + payback" = max(0, cost - money) / rate + cost / (income gain per second), buy it when the
-- money is there, repeat. Candidates: level up any spawned Shiba, automate any spawned un-automated Shiba, the next
-- expansion (its gain counted as if the new Shiba were automated, because the automation pad is next to it). The idle player
-- multiplies the score of automation purchases by AutoBias (< 1): it automates everything as soon as it can.
-- Done = all 30 bays spawned + automated + level 50 (the cap before any ascension). Real players are slower (breaks,
-- mistakes, no perfect greedy): read totals as a lower bound and apply a factor of about 1.3-1.6.
--
-- RECOMMENDED constants (for the owner to apply in src/shared/Config/Tycoon.luau in a separate PR; see
-- docs/economy/BALANCING.md -> "Street tycoon (30 bays)"):
--   Street.BaySeconds 40 -> 80, Swing.AutomationGrowth 1.5 -> 1.25, Lane.LevelCostSeconds 20 -> 225,
--   Lane.LevelCostGrowth 1.17 -> 1.21 (Swing.AutomationSeconds stays 60, Lane.TierGrowth stays 2.7).
-- Result with the recommendation (this file, default run): active clicker done after 63.3 h (idle 72.4 h); current
-- constants finish in 6.3 h (level costs far too low for 30 lanes earning at once).

local fs = require("@lune/fs")
local process = require("@lune/process")
local luau = require("@lune/luau")

local function loadModule(path: string, requires: { any })
	local chunk = luau.load(fs.readFile(path), {
		debugName = path,
		environment = {
			-- The modules require their Config and Types by relative path: hand them over by call order.
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
local Math = loadModule("src/shared/Util/TycoonMath.luau", { Config, {} })
-- TycoonSteps requires EconomyConfig (names only), Config, TycoonDecor (decor prices are not simulated yet), Types, TycoonMath.
-- (stubbed empty: the real file needs Roblox's Color3, and decor is out of scope here).
local Decor = { Themes = {} }
local Steps = loadModule("src/shared/Util/TycoonSteps.luau", { { Shibas = {} }, Config, Decor, {}, Math })

-- The constants the experiments change (overridable). CURRENT = what src has now; RECOMMENDED = this file's proposal.
local KEYS =
	{ "BaySeconds", "AutomationSeconds", "AutomationGrowth", "LevelCostGrowth", "LevelCostSeconds", "TierGrowth" }
local function readCurrent()
	return {
		BaySeconds = Config.Street.BaySeconds,
		AutomationSeconds = Config.Swing.AutomationSeconds,
		AutomationGrowth = Config.Swing.AutomationGrowth,
		LevelCostGrowth = Config.Lane.LevelCostGrowth,
		LevelCostSeconds = Config.Lane.LevelCostSeconds,
		TierGrowth = Config.Lane.TierGrowth,
	}
end
local CURRENT = readCurrent()

-- RECOMMENDED: filled by the experiments (see BALANCING.md). Keys left out keep the current value.
local RECOMMENDED = {
	BaySeconds = 80,
	AutomationSeconds = 60,
	AutomationGrowth = 1.25,
	LevelCostSeconds = 225,
	LevelCostGrowth = 1.21,
}

local function apply(constants: { [string]: number })
	Config.Street.BaySeconds = constants.BaySeconds
	Config.Swing.AutomationSeconds = constants.AutomationSeconds
	Config.Swing.AutomationGrowth = constants.AutomationGrowth
	Config.Lane.LevelCostGrowth = constants.LevelCostGrowth
	Config.Lane.LevelCostSeconds = constants.LevelCostSeconds
	Config.Lane.TierGrowth = constants.TierGrowth
end

local function merged(base: { [string]: number }, over: { [string]: number }): { [string]: number }
	local result = {}
	for _, key in KEYS do
		result[key] = over[key] or base[key]
	end
	return result
end

local function envOverrides(): { [string]: number }
	local over = {}
	local names = {
		BaySeconds = "BAY_SECONDS",
		AutomationSeconds = "AUTO_SECONDS",
		AutomationGrowth = "AUTO_GROWTH",
		LevelCostGrowth = "LEVEL_COST_GROWTH",
		LevelCostSeconds = "LEVEL_COST_SECONDS",
		TierGrowth = "TIER_GROWTH",
	}
	for key, name in names do
		local value = tonumber(process.env[name])
		if value then
			over[key] = value
		end
	end
	return over
end

-- Player types.
local PLAYERS = {
	{ Name = "active clicker", ClickEff = 0.6, ClickTargets = 2, AutoBias = 1 },
	{ Name = "idle (automates asap)", ClickEff = 0.2, ClickTargets = 1, AutoBias = 0.25 },
}

local LEVEL_CAP = Math.LevelCap(0)
local BAYS = Config.Street.Bays
local EARLY_WINDOW = 10 * 3600

local function fmtTime(s: number): string
	if s < 90 then
		return string.format("%.1f s", s)
	elseif s < 5400 then
		return string.format("%.1f min", s / 60)
	end
	return string.format("%.2f h", s / 3600)
end

local function newState()
	local equipped = {}
	for slot = 1, BAYS do
		equipped[tostring(slot)] = "s" .. slot
	end
	return {
		Street = true,
		Shibas = {},
		NextShibaId = 1,
		Equipped = equipped,
		EquipSlots = BAYS,
		Arches = {},
		Pads = {},
		Steps = {},
		Zone = 5,
		Ascensions = 0,
	}
end

local function simulate(player)
	local state = newState()
	local shibas = state.Shibas
	local spawned = 0
	local automated = 0

	local function spawn()
		spawned += 1
		shibas["s" .. spawned] = { Tier = spawned - 1, Level = 1, Variant = "Normal", Automated = false }
		state.Steps["Bay" .. spawned] = true
	end

	-- Income per second under the player model.
	local function income(): number
		local global = Math.GlobalMultiplier(state)
		local auto = 0
		local manual = {}
		for slot = 1, spawned do
			local rate = Math.LaneIncome(state, slot)
			if shibas["s" .. slot].Automated then
				auto += rate
			else
				table.insert(manual, rate)
			end
		end
		table.sort(manual, function(a, b)
			return a > b
		end)
		local clicked = 0
		for index = 1, math.min(player.ClickTargets, #manual) do
			clicked += manual[index]
		end
		return global * (auto + player.ClickEff * clicked)
	end

	spawn() -- bay 1 is free
	local time, money = 0, 0
	local milestones = {}
	local function mark(name: string)
		if not milestones[name] then
			milestones[name] = time
		end
	end
	mark("Shiba 1")
	local maxGapEarly, maxGapEarlyAt = 0, 0
	local lastBuy = 0
	local purchases = 0

	local function done(): boolean
		if spawned < BAYS or automated < BAYS then
			return false
		end
		for slot = 1, BAYS do
			if shibas["s" .. slot].Level < LEVEL_CAP then
				return false
			end
		end
		return true
	end

	local function record()
		purchases += 1
		local gap = time - lastBuy
		if time <= EARLY_WINDOW and gap > maxGapEarly then
			maxGapEarly, maxGapEarlyAt = gap, time
		end
		lastBuy = time
		for _, n in { 2, 5, 10, 20, 30 } do
			if spawned >= n then
				mark("Shiba " .. n .. " spawned")
			end
		end
		if automated >= 1 then
			mark("first automation")
		end
		if automated >= BAYS then
			mark("all automated")
		end
		local all50 = true
		for slot = 1, spawned do
			if shibas["s" .. slot].Level < LEVEL_CAP then
				all50 = false
				break
			end
		end
		if all50 and spawned == BAYS then
			mark("all level 50")
		end
	end

	local guard = 0
	while not done() and guard < 20000 do
		guard += 1
		local rate = income()
		local best, bestScore
		local function consider(cost: number, delta: number, bias: number, action: () -> (), undo: () -> ())
			-- The mutation for the delta was already applied by the caller; `action`/`undo` commit or revert it.
			undo()
			if delta > 0 then
				local wait = math.max(0, cost - money) / rate
				local score = (wait + cost / delta) * bias
				if not bestScore or score < bestScore then
					best, bestScore = { Cost = cost, Apply = action }, score
				end
			end
		end

		for slot = 1, spawned do
			local shiba = shibas["s" .. slot]
			if shiba.Level < LEVEL_CAP then
				local cost = Math.LevelCost(shiba.Tier, shiba.Level)
				shiba.Level += 1
				local delta = income() - rate
				consider(cost, delta, 1, function()
					shiba.Level += 1
				end, function()
					shiba.Level -= 1
				end)
			end
			if not shiba.Automated then
				local cost = Math.AutomationPrice(shiba.Tier, automated)
				shiba.Automated = true
				local delta = income() - rate
				consider(cost, delta, player.AutoBias, function()
					shiba.Automated = true
					automated += 1
				end, function()
					shiba.Automated = false
				end)
			end
		end
		if spawned < BAYS then
			local cost = Steps.Price(Steps.ById["Bay" .. spawned + 1], state)
			spawn()
			shibas["s" .. spawned].Automated = true -- counted as if automated: the pad is right next to it
			local delta = income() - rate
			consider(cost, delta, 1, function()
				spawn()
			end, function()
				shibas["s" .. spawned] = nil
				state.Steps["Bay" .. spawned] = nil
				spawned -= 1
			end)
		end
		if not best then
			break
		end
		local wait = math.max(0, best.Cost - money) / rate
		time += wait
		money += wait * rate - best.Cost
		best.Apply()
		record()
	end
	milestones["done"] = if done() then time else nil
	return milestones, maxGapEarly, maxGapEarlyAt, purchases
end

local ORDER = {
	"Shiba 2 spawned",
	"first automation",
	"Shiba 5 spawned",
	"Shiba 10 spawned",
	"Shiba 20 spawned",
	"Shiba 30 spawned",
	"all automated",
	"all level 50",
	"done",
}

local function runOne(label: string, constants: { [string]: number })
	apply(constants)
	local parts = {}
	for _, key in KEYS do
		table.insert(parts, key .. "=" .. tostring(constants[key]))
	end
	print("== " .. label .. ": " .. table.concat(parts, " "))
	for _, player in PLAYERS do
		local milestones, gap, gapAt, purchases = simulate(player)
		local cells = {}
		for _, name in ORDER do
			local t = milestones[name]
			table.insert(cells, string.format("%s %s", name, if t then fmtTime(t) else "never"))
		end
		print(string.format("  %-22s %s", player.Name, table.concat(cells, " | ")))
		print(
			string.format(
				"  %-22s longest wait in the first 10 h: %s (at %s), purchases: %d",
				"",
				fmtTime(gap),
				fmtTime(gapAt),
				purchases
			)
		)
	end
end

if process.env.SWEEP then
	for _, baySeconds in { 20, 40, 80 } do
		for _, autoSeconds in { 30, 60, 120 } do
			for _, autoGrowth in { 1.1, 1.15, 1.2, 1.25 } do
				local constants = merged(CURRENT, {
					BaySeconds = baySeconds,
					AutomationSeconds = autoSeconds,
					AutomationGrowth = autoGrowth,
				})
				apply(constants)
				local active = simulate(PLAYERS[1])
				local idle = simulate(PLAYERS[2])
				print(
					string.format(
						"bay %3d auto %3d growth %.2f : active done %s (first auto %s, shiba2 %s) | idle done %s",
						baySeconds,
						autoSeconds,
						autoGrowth,
						if active.done then fmtTime(active.done) else "never",
						fmtTime(active["first automation"] or 0),
						fmtTime(active["Shiba 2 spawned"] or 0),
						if idle.done then fmtTime(idle.done) else "never"
					)
				)
			end
		end
	end
elseif process.env.CASES then
	-- CASES="bay:autoSec:autoGrowth:levelCostSec:levelCostGrowth;..." runs several constant sets (both player types each).
	for _, case in string.split(process.env.CASES, ";") do
		local v = string.split(case, ":")
		runOne(
			case,
			merged(CURRENT, {
				BaySeconds = tonumber(v[1]),
				AutomationSeconds = tonumber(v[2]),
				AutomationGrowth = tonumber(v[3]),
				LevelCostSeconds = tonumber(v[4]),
				LevelCostGrowth = tonumber(v[5]),
			})
		)
	end
else
	local over = envOverrides()
	if next(over) then
		runOne("overridden", merged(CURRENT, over))
	else
		runOne("CURRENT constants (src/shared/Config/Tycoon.luau)", CURRENT)
		runOne("RECOMMENDED constants", merged(CURRENT, RECOMMENDED))
	end
end
apply(CURRENT)
