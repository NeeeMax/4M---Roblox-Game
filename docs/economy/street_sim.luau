--!nocheck
-- Balancing simulation of the STREET tycoon (30 bays; docs/GAME_DESIGN.md → "Gameplay flow"). It loads the REAL Config/Tycoon,
-- Util/TycoonMath, Util/TycoonSteps and all decor themes, so prices and incomes are exactly the game's. Run from the repo root:
--   lune run docs/economy/street_sim                       -- the constants in src/ now
--   TIER_GROWTH=4 BAY_SECONDS=2000 lune run docs/economy/street_sim   -- override constants (see KEYS, all optional)
--   QUIET=1 ...                                            -- only the summary line
--   PLAYER=active|idle ...                                 -- one player type only (default both)
--
-- Model
--  * Player policy: head for the next progress item (decor part / next Shiba); while it is not affordable, buy only what pays
--    for itself before that moment (level ups, Interns). IDLE buys every Intern at once.
--  * Bay 1 is free. Bay n (n >= 2) is bought with TycoonSteps.Price after ALL decor of bay n - 1 is bought (decor is bought in
--    two parallel chains; Bonk Intern pads are optional). A new Shiba starts at level 1, not automated.
--  * Income per second = sum over automated Shibas of TycoonMath.LaneIncome * GlobalMultiplier (perks, neighbours and the
--    decor reward bonuses included) + what the player earns by clicking: the best manual Shiba's rate, capped by the click
--    rate (CLICKS_PER_SECOND) and the time really spent clicking (CLICK_EFF: walking, stepping on pads).
--  * Decor of bays 6 to 30 has no RewardMult in the themes yet: the sim gives each of those themes a total of x6 spread evenly
--    (the written themes 1 to 5 use their real values).
--  * ACTIVE clicks all the time, IDLE stops clicking after its first Intern.
-- Read the totals as a lower bound: real players need about 1.3 to 1.6 times as long.

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local process = require("@lune/process")
local roblox = require("@lune/roblox")

local enum = setmetatable({}, {
	__index = function(_, k)
		return setmetatable({}, {
			__index = function(_, j)
				return k .. "." .. j
			end,
		})
	end,
})
local function loadFile(path, requires)
	local chunk = luau.load(fs.readFile(path), {
		debugName = path,
		environment = {
			Vector3 = roblox.Vector3,
			Vector2 = roblox.Vector2,
			Color3 = roblox.Color3,
			CFrame = roblox.CFrame,
			Enum = enum,
			require = function()
				return table.remove(requires or {}, 1) or {}
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

local Config = loadFile("src/shared/Config/Tycoon.luau")

-- Decor themes: the older ones of DecorThemesA/B/C, replaced by DecorTheme01 … 05 where those exist.
local themes = {}
for _, name in { "A", "B", "C" } do
	for bay, theme in loadFile(`src/shared/Config/DecorThemes{name}.luau`) do
		themes[bay] = theme
	end
end
for bay = 1, 5 do
	local theme = loadFile(`src/shared/Config/DecorTheme0{bay}.luau`)
	if type(theme) == "table" then
		themes[bay] = theme
	end
end
for bay = 6, 30 do
	local theme = themes[bay]
	if theme then
		for _, part in theme.Parts do
			if part.RewardMult == nil then
				part.RewardMult = 6 ^ (1 / #theme.Parts)
			end
		end
	end
end
local Decor = { Themes = themes }

local Math = loadFile("src/shared/Util/TycoonMath.luau", { Config, Decor, {} })
local Steps = loadFile("src/shared/Util/TycoonSteps.luau", { { Shibas = {} }, Config, Decor, {}, Math })

-- ==== constants the experiments may override ===========================================================================
local KEYS = {
	TIER_GROWTH = { Config.Street, "TierGrowth" },
	BAY_SECONDS = { Config.Street, "BaySeconds" },
	DECOR_SCALE = { Config.Street, "DecorScale" },
	AUTO_SECONDS = { Config.Street, "AutomationSeconds" },
	AUTO_GROWTH = { Config.Street, "AutomationGrowth" },
	AUTO_FIRST_SHARE = { Config.Street, "AutomationFirstShare" },
	LEVEL_SECONDS = { Config.Swing, "StreetLevelSeconds" },
	LEVEL_GROWTH = { Config.Swing, "StreetLevelGrowth" },
	PAYOUT_PER_LEVEL = { Config.Swing, "PayoutPerLevel" },
	MIN_COOLDOWN_GROWTH = { Config.Swing, "MinCooldownGrowth" },
}
for key, target in KEYS do
	local value = process.env[key]
	if value and tonumber(value) then
		target[1][target[2]] = tonumber(value)
	end
end
-- FACTORS=1.5,2,3.2: StageFactor of stage 1, 2, 3 ... (the rest stays 1)
if process.env.FACTORS then
	local n = 0
	for value in string.gmatch(process.env.FACTORS, "[^,]+") do
		n += 1
		Config.Street.StageFactor[n] = tonumber(value)
	end
end
local CLICKS_PER_SECOND = tonumber(process.env.CLICKS_PER_SECOND or "") or 3
local CLICK_EFF = tonumber(process.env.CLICK_EFF or "") or 0.5
local QUIET = process.env.QUIET ~= nil
local MAX_HOURS = tonumber(process.env.MAX_HOURS or "") or 400
local BAYS = Config.Street.Bays
-- STOP_BAY=8: end the run when that Shiba is bought (fast calibration of the early game)
local DEBUG = process.env.DEBUG ~= nil
local STOP_BAY = tonumber(process.env.STOP_BAY or "") or BAYS
local CAP = Config.Swing.StreetLevelCap

-- ==== state and incomes ================================================================================================
local function newState()
	return {
		Enabled = true,
		Street = true,
		Ascensions = 0,
		Zone = 0,
		EquipSlots = 0,
		Shibas = {},
		Equipped = {},
		Arches = {},
		Pads = {},
		Steps = {},
		NextShibaId = 1,
	}
end

local function spawn(tycoon, bay)
	local id = `s{tycoon.NextShibaId}`
	tycoon.NextShibaId += 1
	tycoon.Shibas[id] = { Tier = bay - 1, Level = 1, Variant = "Normal" }
	tycoon.Equipped[tostring(bay)] = id
	tycoon.EquipSlots = math.max(tycoon.EquipSlots, bay)
	tycoon.Steps[`Bay{bay}`] = true
end

local function shibaOf(tycoon, bay)
	local id = tycoon.Equipped[tostring(bay)]
	return if id then tycoon.Shibas[id] else nil
end

-- (automated income, best manual rate) per second.
local function incomes(tycoon)
	local global = Math.GlobalMultiplier(tycoon)
	local auto, bestManual = 0, 0
	for bay = 1, tycoon.EquipSlots do
		local shiba = shibaOf(tycoon, bay)
		if shiba then
			local rate = Math.LaneIncome(tycoon, bay) * global
			if shiba.Automated then
				auto += rate
			else
				local cooldown = Math.SwingCooldown(shiba.Tier, shiba.Level)
				-- a click pays one hit; you cannot click faster than CLICKS_PER_SECOND
				local manual = rate * math.min(1, cooldown * CLICKS_PER_SECOND)
				if manual > bestManual then
					bestManual = manual
				end
			end
		end
	end
	return auto, bestManual
end

local function totalIncome(tycoon, clicking)
	local auto, manual = incomes(tycoon)
	return auto + (if clicking then manual * CLICK_EFF else 0)
end

local function decorParts(bay)
	local theme = themes[bay]
	return if theme then theme.Parts else {}
end

local function partStep(bay, index)
	return Steps.ById[`Decor{bay}_{decorParts(bay)[index].Id}`]
end

-- the decor parts of `bay` not bought yet, in order
local function remainingDecor(tycoon, bay)
	local out = {}
	for index, part in decorParts(bay) do
		if not tycoon.Steps[`Decor{bay}_{part.Id}`] then
			table.insert(out, index)
		end
	end
	return out
end

local function hours(seconds)
	return seconds / 3600
end

local function levelList(tycoon)
	local parts = {}
	for slot = 1, tycoon.EquipSlots do
		local shiba = shibaOf(tycoon, slot)
		table.insert(parts, `{shiba and shiba.Level or 0}{if shiba and shiba.Automated then "a" else ""}`)
	end
	return table.concat(parts, " ")
end

-- ==== the run ==========================================================================================================
local function run(idle)
	local tycoon = newState()
	spawn(tycoon, 1)
	local money, now = 0, 0
	local clicking = true
	local bayTime, decorDoneTime = {}, {}
	bayTime[1] = 0
	local automatedCount = 0
	local purchases = 0

	while now < MAX_HOURS * 3600 do
		local income = totalIncome(tycoon, clicking)
		if income <= 0 then
			break
		end
		local bay = tycoon.EquipSlots
		local candidates = {}

		-- the package of progress items: remaining decor of the current bay + the next bay
		local rest = remainingDecor(tycoon, bay)
		local nextBayStep = if bay < BAYS then Steps.ById[`Bay{bay + 1}`] else nil
		local packageCost = 0
		for _, index in rest do
			packageCost += Steps.Price(partStep(bay, index), tycoon)
		end
		local bayPrice = if nextBayStep then Steps.Price(nextBayStep, tycoon) else 0
		packageCost += bayPrice
		local bayGain = 0
		if nextBayStep then
			-- the new Shiba at level 1, automated
			spawn(tycoon, bay + 1)
			local fresh = shibaOf(tycoon, bay + 1)
			fresh.Automated = true
			local after = incomes(tycoon)
			tycoon.Shibas[tycoon.Equipped[tostring(bay + 1)]] = nil
			tycoon.Equipped[tostring(bay + 1)] = nil
			tycoon.Steps[`Bay{bay + 1}`] = nil
			tycoon.EquipSlots = bay
			tycoon.NextShibaId -= 1
			local before = incomes(tycoon)
			bayGain = math.max(after - before, 1e-9)
		end

		local function consider(cost, gain, apply, kind, bonus)
			table.insert(
				candidates,
				{ Cost = cost, Gain = gain, Apply = apply, Kind = kind, Progress = kind == "decor" or kind == "bay" }
			)
		end

		-- level ups
		for slot = 1, tycoon.EquipSlots do
			local shiba = shibaOf(tycoon, slot)
			if shiba and shiba.Level < CAP then
				local cost = Math.LevelCost(shiba.Tier, shiba.Level, true)
				shiba.Level += 1
				local gain = totalIncome(tycoon, clicking) - income
				shiba.Level -= 1
				consider(cost, gain, function()
					shiba.Level += 1
				end, "level")
			end
		end
		-- Bonk Interns
		for slot = 1, tycoon.EquipSlots do
			local shiba = shibaOf(tycoon, slot)
			if shiba and not shiba.Automated then
				local cost = Math.StreetAutomationPrice(shiba.Tier, automatedCount)
				shiba.Automated = true
				local gain = totalIncome(tycoon, clicking) - income
				shiba.Automated = nil
				-- the idle player wants every Shiba automated as soon as possible
				consider(cost, if idle then gain * 50 else gain, function()
					shiba.Automated = true
					automatedCount += 1
					if idle then
						clicking = false
					end
				end, "intern")
			end
		end
		-- decor (the visible heads of the two chains) and the next bay when all decor is done
		if #rest > 0 then
			for position = 1, math.min(2, #rest) do
				local index = rest[position]
				local part = decorParts(bay)[index]
				-- chain order: part i needs part i - 2 (parts 1 and 2 need the bay)
				local open = index <= 2 or tycoon.Steps[`Decor{bay}_{decorParts(bay)[index - 2].Id}`]
				if open then
					local cost = Steps.Price(partStep(bay, index), tycoon)
					tycoon.Steps[`Decor{bay}_{part.Id}`] = true
					local gain = totalIncome(tycoon, clicking) - income
					tycoon.Steps[`Decor{bay}_{part.Id}`] = nil
					local share = if packageCost > 0 then cost / packageCost else 0
					consider(cost, gain, function()
						tycoon.Steps[`Decor{bay}_{part.Id}`] = true
					end, "decor", bayGain * share)
				end
			end
		elseif nextBayStep then
			consider(bayPrice, 0, function()
				if DEBUG then
					local decor = 0
					for _, part in decorParts(bay) do
						decor += Steps.Price(Steps.ById[`Decor{bay}_{part.Id}`], tycoon)
					end
					print(
						string.format(
							"   [debug] buying Shiba %d at %.1f min: income %.3g/s, price %.3g, decor of bay %d totalled %.3g, levels %s",
							bay + 1,
							now / 60,
							income,
							bayPrice,
							bay,
							decor,
							levelList(tycoon)
						)
					)
				end
				spawn(tycoon, bay + 1)
				bayTime[bay + 1] = now
			end, "bay", bayGain)
		end

		if #candidates == 0 then
			break
		end
		-- Policy: the player wants the next progress item (a decor part, or the next Shiba when the decor is done). Until it is
		-- affordable they only buy what pays for itself before that moment (upgrades, Interns). The idle player buys an Intern
		-- as soon as it is affordable.
		local goal
		for _, candidate in candidates do
			if candidate.Progress and (not goal or candidate.Cost < goal.Cost) then
				goal = candidate
			end
		end
		local pick = goal
		local goalWait = if goal then math.max(0, goal.Cost - money) / income else math.huge
		if not goal or goalWait > 0 then
			local best, bestTime
			for _, candidate in candidates do
				if not candidate.Progress then
					local wait = math.max(0, candidate.Cost - money) / income
					local payback = candidate.Cost / math.max(candidate.Gain, 1e-12)
					local useful = if candidate.Kind == "intern" and idle then true else wait + payback < goalWait * 0.9
					if useful and wait < goalWait and (not best or wait < bestTime) then
						best, bestTime = candidate, wait
					end
				end
			end
			if best then
				pick = best
			end
		end
		if not pick then
			break
		end
		local wait = math.max(0, pick.Cost - money) / income
		now += wait
		money += income * wait - pick.Cost
		if process.env.TRACE and now / 60 < tonumber(process.env.TRACE) then
			print(
				string.format(
					"   [trace] %.2f min: money %.3g income %.3g/s -> %s cost %.3g",
					now / 60,
					money,
					income,
					pick.Kind,
					pick.Cost
				)
			)
		end
		pick.Apply()
		purchases += 1
		if tycoon.EquipSlots >= STOP_BAY then
			break
		end
		if #remainingDecor(tycoon, bay) == 0 and not decorDoneTime[bay] and shibaOf(tycoon, bay) then
			decorDoneTime[bay] = now
		end
		-- done: every bay, all decor, all Interns, every Shiba at the cap
		if tycoon.EquipSlots == BAYS and #remainingDecor(tycoon, BAYS) == 0 then
			local all = true
			for slot = 1, BAYS do
				local shiba = shibaOf(tycoon, slot)
				if not shiba or not shiba.Automated or shiba.Level < CAP then
					all = false
					break
				end
			end
			if all then
				break
			end
		end
	end
	return { Now = now, BayTime = bayTime, DecorDone = decorDoneTime, Purchases = purchases, Tycoon = tycoon }
end

local function report(name, result)
	print(`== {name}`)
	local tycoon = result.Tycoon
	if QUIET then
		print(`   total {string.format("%.1f", hours(result.Now))} h, bays {tycoon.EquipSlots}`)
		return
	end
	local line = {}
	for _, bay in { 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30 } do
		local t = result.BayTime[bay]
		table.insert(line, `Shiba {bay}: {if t then string.format("%.2fh", hours(t)) else "-"}`)
	end
	print("   " .. table.concat(line, " | "))
	local stage = {}
	for bay = 2, BAYS do
		local a, b = result.BayTime[bay - 1], result.BayTime[bay]
		if a and b then
			table.insert(stage, string.format("%d:%.0fm", bay, (b - a) / 60))
		end
	end
	print("   minutes per stage (Shiba n after n-1): " .. table.concat(stage, " "))
	local levelList = {}
	for bay = 1, tycoon.EquipSlots do
		local shiba = shibaOf(tycoon, bay)
		table.insert(levelList, `{bay}:{shiba and shiba.Level or 0}{if shiba and shiba.Automated then "a" else ""}`)
	end
	print("   final levels (a = Intern): " .. table.concat(levelList, " "))
	print(
		`   total {string.format("%.1f", hours(result.Now))} h, purchases {result.Purchases}, bays {tycoon.EquipSlots}`
	)
	if process.env.RESULT then
		-- machine-readable bay times for the calibration driver
		for bay = 1, BAYS do
			if result.BayTime[bay] then
				print(`BAYTIME {bay} {result.BayTime[bay]}`)
			end
		end
	end
end

print(
	`street_sim: TierGrowth {Config.Street.TierGrowth}, BaySeconds {Config.Street.BaySeconds}, DecorScale {Config.Street.DecorScale}, {#Config.Street.StageFactor} stage factors, Intern {Config.Street.AutomationSeconds}*{Config.Street.AutomationGrowth}^n, level {Config.Swing.StreetLevelSeconds}s*{Config.Swing.StreetLevelGrowth}^L, payout +{Config.Swing.PayoutPerLevel}/level, min cooldown x{Config.Swing.MinCooldownGrowth}/tier`
)
local which = process.env.PLAYER or "both"
if which ~= "idle" then
	report("active clicker", run(false))
end
if which ~= "active" then
	report("idle (automates asap)", run(true))
end
