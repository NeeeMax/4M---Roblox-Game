-- Balancing simulation of the v2 economy (docs/economy/BALANCING.md). Loads the real src/shared/Config/EconomyConfig.
-- Run from the repo root:  lune run docs/economy/simulate.luau
--
-- Player model: always buys the CHEAPEST affordable upgrade next (respecting EconomyConfig.UnlockAtShibaTier and the
-- normal max levels), earning EconomyConfig.BaselineIncome(levels) per second (an average active player incl.
-- intern and basket), money carried over between purchases. Run 2 is the same after one rebirth
-- (income × RebirthMultiplier(1), same prices).

local E = require("./load_config")

local IDS = {}
for _, spec in E.RouteSpecs do
	table.insert(IDS, spec.Upgrade)
end

local function fmtTime(s: number): string
	if s < 90 then
		return string.format("%.1f s", s)
	elseif s < 5400 then
		return string.format("%.1f min", s / 60)
	end
	return string.format("%.2f h", s / 3600)
end

local SUFFIX = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc", "UDc", "DDc" }
local function fmtNum(v: number): string
	if v < 1000 then
		return string.format("%.3g", v)
	end
	local group = math.floor(math.log10(v) / 3)
	if group >= #SUFFIX then
		return string.format("%.2e", v)
	end
	return string.format("%.3g%s", v / 10 ^ (group * 3), SUFFIX[group + 1])
end

local function copy(levels)
	local out = {}
	for k, v in levels do
		out[k] = v
	end
	return out
end

type Purchase = {
	N: number,
	Upgrade: string,
	Level: number,
	Price: number,
	Income: number,
	IncomeAfter: number,
	Idle: number,
	IdleAfter: number,
	Wait: number,
	Time: number,
	Levels: { [string]: number },
}

-- One run. Returns the purchases in order.
local function run(multiplier: number): { Purchase }
	local levels: { [string]: number } = {}
	for _, id in IDS do
		levels[id] = 0
	end
	local money = E.StartingMoney
	local time = 0
	local purchases: { Purchase } = {}
	while true do
		local best, bestPrice = nil, math.huge
		for _, id in IDS do
			local unlocked = (E.UnlockAtShibaTier[id] or 0) <= levels.ShooterTier
			if unlocked and levels[id] < E.RouteCount(id) then
				local price = E.GetCost(id, levels[id])
				if price < bestPrice then
					best, bestPrice = id, price
				end
			end
		end
		if not best then
			break
		end
		local income = E.BaselineIncome(levels) * multiplier
		local idle = E.BaselineIncome(levels, true) * multiplier
		local wait = math.max(0, (bestPrice - money) / income)
		time += wait
		money += wait * income - bestPrice
		levels[best] += 1
		table.insert(purchases, {
			N = #purchases + 1,
			Upgrade = best,
			Level = levels[best],
			Price = bestPrice,
			Income = income,
			IncomeAfter = E.BaselineIncome(levels) * multiplier,
			Idle = idle,
			IdleAfter = E.BaselineIncome(levels, true) * multiplier,
			Wait = wait,
			Time = time,
			Levels = copy(levels),
		})
	end
	return purchases
end

local function label(p: Purchase): string
	if p.Upgrade == "ShooterTier" then
		return string.format("**Shiba %d** (%s)", p.Level + 1, E.Shibas[p.Level + 1].Name)
	end
	return string.format("%s %d", p.Upgrade, p.Level)
end

local function payback(p: Purchase): number
	local gain = p.IncomeAfter - p.Income
	return if gain > 0 then p.Price / gain else math.huge
end

local function idlePayback(p: Purchase): number
	local gain = p.IdleAfter - p.Idle
	return if gain > 0 then p.Price / gain else math.huge
end

local function shibaTimes(purchases: { Purchase }): { [number]: number }
	local times = { [1] = 0 }
	for _, p in purchases do
		if p.Upgrade == "ShooterTier" then
			times[p.Level + 1] = p.Time
		end
	end
	return times
end

local purchases = run(1)

print("# GET BONKED economy simulation\n")
print(
	string.format(
		"FinalShibaCost %s · ShibaGrowth ×%.2f per Shiba · StartingMoney %s · %d purchases in the route\n",
		fmtNum(E.FinalShibaCost),
		E.ShibaGrowth,
		fmtNum(E.StartingMoney),
		#E.Route
	)
)
print("## Run 1 (greedy: cheapest affordable upgrade)\n")
print("| # | upgrade → level | price | income/s | wait | target T(n) | play time | payback | idle payback |")
print("|---|-----------------|-------|----------|------|-------------|-----------|---------|--------------|")
local maxPayback, maxPaybackAt = 0, ""
local routeMismatch = 0
for index, p in purchases do
	local route = E.Route[index]
	local sameAsRoute = route and route.Upgrade == p.Upgrade and route.Level == p.Level
	if not sameAsRoute then
		routeMismatch += 1
	end
	local isAutomation = p.Upgrade == "Basket" or p.Upgrade == "Intern"
	local pb = payback(p)
	-- Automation is judged by what it earns while idle (its point); the rest by active income.
	local judged = if isAutomation then idlePayback(p) else pb
	if judged > maxPayback then
		maxPayback, maxPaybackAt = judged, label(p)
	end
	print(
		string.format(
			"| %d | %s%s | %s | %s | %s | %s | %s | %s | %s |",
			p.N,
			label(p),
			if sameAsRoute then "" else " ≠route",
			fmtNum(p.Price),
			fmtNum(p.Income),
			fmtTime(p.Wait),
			fmtTime(E.TargetSeconds(index - 1)),
			fmtTime(p.Time),
			if pb == math.huge then "—" else fmtTime(pb),
			if isAutomation then fmtTime(idlePayback(p)) else ""
		)
	)
end

local times = shibaTimes(purchases)
local total = purchases[#purchases].Time
print("\n## Summary run 1\n")
print(string.format("- first purchase after %s (%s)", fmtTime(purchases[1].Time), label(purchases[1])))
for _, n in { 1, 2, 5, 10, 20, 21, 30 } do
	print(string.format("- Shiba %d (ShooterTier level %d): %s", n, n - 1, fmtTime(times[n] or 0)))
end
print(string.format("- all %d purchases: %s", #purchases, fmtTime(total)))
local minuteStart = nil
for _, p in purchases do
	if p.Wait >= 60 and not minuteStart then
		minuteStart = p
	end
end
if minuteStart then
	print(
		string.format(
			"- first wait ≥ 60 s: purchase #%d (%s) while owning Shiba %d, at %s",
			minuteStart.N,
			label(minuteStart),
			minuteStart.Levels.ShooterTier + (if minuteStart.Upgrade == "ShooterTier" then 0 else 1),
			fmtTime(minuteStart.Time)
		)
	)
end
print(string.format("- longest payback (automation judged by idle payback): %s for %s", fmtTime(maxPayback), maxPaybackAt))
print(string.format("- purchases in a different order than the Route: %d of %d", routeMismatch, #purchases))
print(string.format("- last price: %s", fmtNum(purchases[#purchases].Price)))

print("\n## Idle vs active income (run 1)\n")
print("| at purchase | levels (Shooters/Tier/Proj/Speed/Basket/Intern) | active /s | idle /s | active ÷ idle |")
print("|-------------|--------------------------------------------------|-----------|---------|---------------|")
local step = math.max(1, math.floor(#purchases / 12))
for index = step, #purchases, step do
	local p = purchases[index]
	local l = p.Levels
	local ratio = if p.IdleAfter > 0 then string.format("%.2f×", p.IncomeAfter / p.IdleAfter) else "no idle income"
	print(
		string.format(
			"| #%d | %d/%d/%d/%d/%d/%d | %s | %s | %s |",
			p.N,
			l.Shooters,
			l.ShooterTier,
			l.ProjectileTier,
			l.MoveSpeed,
			l.Basket,
			l.Intern,
			fmtNum(p.IncomeAfter),
			fmtNum(p.IdleAfter),
			ratio
		)
	)
end

print("\n## Automation payback (run 1)\n")
print("| purchase | price | active payback | idle payback |")
print("|----------|-------|----------------|--------------|")
for _, p in purchases do
	if p.Upgrade == "Basket" or p.Upgrade == "Intern" then
		print(string.format("| %s | %s | %s | %s |", label(p), fmtNum(p.Price), fmtTime(payback(p)), fmtTime(idlePayback(p))))
	end
end

-- ASCII curve: cumulative play time per Shiba.
print("\n## Time to Shiba n (run 1)\n")
print("```")
local width = 50
for n = 1, #E.Shibas do
	local t = times[n]
	if t then
		local bar = string.rep("#", math.floor(t / total * width + 0.5))
		print(string.format("Shiba %2d %9s |%s", n, fmtTime(t), bar))
	end
end
print("```")

-- Rebirth.
local gate = E.Rebirth.MinShibaTier + 1
local run2 = run(E.RebirthMultiplier(1))
local times2 = shibaTimes(run2)
print("\n## Rebirth\n")
print(
	string.format(
		"- rebirth needs Shiba %d (ShooterTier level %d): run 1 reaches it after %s; gives ×%g income",
		gate,
		E.Rebirth.MinShibaTier,
		fmtTime(times[gate] or 0),
		E.RebirthMultiplier(1)
	)
)
print(
	string.format(
		"- run 2 (×%g): first purchase %s, Shiba 10 %s, Shiba %d (rebirth 2) %s, Shiba 30 %s, all purchases %s",
		E.RebirthMultiplier(1),
		fmtTime(run2[1].Time),
		fmtTime(times2[10] or 0),
		gate,
		fmtTime(times2[gate] or 0),
		fmtTime(times2[#E.Shibas] or 0),
		fmtTime(run2[#run2].Time)
	)
)
for r = 2, 5 do
	local rr = run(E.RebirthMultiplier(r))
	local tt = shibaTimes(rr)
	print(
		string.format(
			"- run %d (×%g): Shiba %d after %s, whole run %s",
			r + 1,
			E.RebirthMultiplier(r),
			gate,
			fmtTime(tt[gate] or 0),
			fmtTime(rr[#rr].Time)
		)
	)
end
