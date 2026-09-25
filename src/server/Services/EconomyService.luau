--!strict
-- Bonk Point balance. Server-only: clients can never add points themselves. Points come from validated hits
-- (BonkService), the daily spin, quests, coin flips and the admin testing tools (AdminService).
-- Also sums each player's earned points per sample for the Shiba Bank's income rate (OfflineService).

local Players = game:GetService("Players")

local DataService = require(script.Parent.DataService)

type Sample = {
	-- Earned Bonk Points since StartedAt.
	Points: number,
	-- os.clock() when this sample started.
	StartedAt: number,
}

local samples: { [Player]: Sample } = {}

local EconomyService = {}

function EconomyService.GetPoints(player: Player): number
	local state = DataService.GetState(player)
	return if state then state.BonkPoints else 0
end

local function isValidAmount(amount: number): boolean
	-- `amount == amount` rejects NaN.
	return amount == amount and amount > 0 and amount ~= math.huge
end

-- Adds points. `earned` (default true) also counts them for the leaderboard and the income rate; admin gifts pass
-- false.
function EconomyService.AddPoints(player: Player, amount: number, earned: boolean?)
	local state = DataService.GetState(player)
	if not state or not isValidAmount(amount) then
		return
	end
	local whole = math.floor(amount)
	state.BonkPoints += whole
	if earned ~= false then
		state.TotalEarned += whole
		local sample = samples[player]
		if sample then
			sample.Points += whole
		end
	end
	DataService.Replicate(player)
end

-- Automation income (the basket and the intern, AutomationService): paid and counted like AddPoints. It is sampled
-- separately for the offline bank (Bank.AutomationPerMinute) — the economy agent owns that sampling; this minimal
-- version only pays.
function EconomyService.AddAutomationPoints(player: Player, amount: number)
	EconomyService.AddPoints(player, amount)
end

-- Removes `amount` points if the player has enough. Returns whether it did.
function EconomyService.TrySpend(player: Player, amount: number): boolean
	local state = DataService.GetState(player)
	if not state or amount ~= amount or amount < 0 or state.BonkPoints < amount then
		return false
	end
	state.BonkPoints -= amount
	DataService.Replicate(player)
	return true
end

-- Admin testing tool.
function EconomyService.SetPoints(player: Player, amount: number)
	local state = DataService.GetState(player)
	if not state or amount ~= amount or amount < 0 then
		return
	end
	state.BonkPoints = math.floor(amount)
	DataService.Replicate(player)
end

-- Pays the pending Shiba Bank earnings × `multiplier` (1, or 2 after the "DoubleOffline" purchase) and clears them.
-- They count for the leaderboard but not for the income rate (offline income must not raise itself).
-- Returns the amount paid (0 if nothing was pending).
function EconomyService.PayOffline(player: Player, multiplier: number): number
	local state = DataService.GetState(player)
	if not state then
		return 0
	end
	local amount = math.floor(state.Bank.Pending * multiplier)
	state.Bank.Pending = 0
	state.Bank.PendingSeconds = 0
	if isValidAmount(amount) then
		state.BonkPoints += amount
		state.TotalEarned += amount
	else
		amount = 0
	end
	DataService.Replicate(player)
	return amount
end

-- Earned Bonk Points since the last sample and the seconds that covers, then starts a new sample. Returns (0, 0) and
-- keeps counting while the sample is shorter than `minSeconds` or the player's data is not loaded.
-- OfflineService turns these samples into Bank.IncomePerMinute.
function EconomyService.TakeIncomeSample(player: Player, minSeconds: number): (number, number)
	local sample = samples[player]
	local now = os.clock()
	if not sample or now - sample.StartedAt < minSeconds then
		return 0, 0
	end
	local points, elapsed = sample.Points, now - sample.StartedAt
	sample.Points = 0
	sample.StartedAt = now
	return points, elapsed
end

function EconomyService.Start()
	DataService.OnLoaded(function(player)
		samples[player] = { Points = 0, StartedAt = os.clock() }
	end)
	Players.PlayerRemoving:Connect(function(player)
		samples[player] = nil
	end)
end

return EconomyService
