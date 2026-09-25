-- Phase 0 snapshot: simulates the economy as it was before the rework (main @ d121430).
-- Run: lune run docs/economy/current_economy.luau
-- Player model (docs/GAME_DESIGN.md → Pacing): always buys the cheapest upgrade next.
-- income/s = Shibas / FireInterval × catch rate × BaseReward × Shiba tier mult × 1.3 (average bonus)

local upgrades = {
	{ id = "MoveSpeed", base = 40, growth = 3.5, curve = 0.1, max = 10 },
	{ id = "Shooters", base = 60, growth = 5.5, curve = 0.2, max = 7 },
	{ id = "ShooterTier", base = 400, growth = 3.5, curve = 0.1, max = 9 },
	{ id = "ProjectileTier", base = 150, growth = 3.6, curve = 0.15, max = 9 },
}
local fire = { 5, 4.3, 3.7, 3.2, 2.7, 2.4, 2, 1.8, 1.5, 1.3 }
local mult = { 1, 1.6, 2.5, 3.9, 6.2, 9.7, 15, 24, 38, 60 }
local reward = { 10, 13, 16, 20, 25, 32, 40, 50, 63, 80 }

local function cost(u, level)
	return math.floor(u.base * u.growth ^ level * (1 + u.curve * level * level) + 1e-6)
end

local levels = { MoveSpeed = 0, Shooters = 0, ShooterTier = 0, ProjectileTier = 0 }
local function income()
	local catch = 0.6 + 0.02 * levels.MoveSpeed
	local t = levels.ShooterTier + 1
	return (levels.Shooters + 1) / fire[t] * catch * reward[levels.ProjectileTier + 1] * mult[t] * 1.3
end

local function fmt(s)
	if s < 120 then
		return string.format("%.0f s", s)
	elseif s < 7200 then
		return string.format("%.1f min", s / 60)
	end
	return string.format("%.1f h", s / 3600)
end

local time, money, buys, shibas = 0, 0, 0, 0
print("| # | bought | cost | income/s before | wait | play time |")
print("|---|--------|------|-----------------|------|-----------|")
while true do
	local best, bestCost = nil, math.huge
	for _, u in upgrades do
		if levels[u.id] < u.max then
			local c = cost(u, levels[u.id])
			if c < bestCost then
				best, bestCost = u, c
			end
		end
	end
	if not best then
		break
	end
	local rate = income()
	local wait = math.max(0, (bestCost - money) / rate)
	time += wait
	money += wait * rate - bestCost
	levels[best.id] += 1
	buys += 1
	local tag = ""
	if best.id == "Shooters" or best.id == "ShooterTier" then
		shibas += 1
		tag = string.format(" (Shiba purchase %d)", shibas)
	end
	print(string.format("| %d | %s %d%s | %d | %.1f | %s | %s |", buys, best.id, levels[best.id], tag, bestCost, rate, fmt(wait), fmt(time)))
end
print(string.format("\nAll %d purchases: %s. Final income %.0f/s.", buys, fmt(time), income()))
