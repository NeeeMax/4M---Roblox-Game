--!strict
-- Bonk Point balance. Server-only: clients can never add points themselves. Points come from validated hits
-- (BonkService), automation (basket + intern, AddAutomationPoints), the daily spin, quests, coin flips and the admin
-- testing tools (AdminService).
-- Also sums each player's earned points per sample for the Shiba Bank's income rates (OfflineService): what they
-- earned themselves and what the automation earned, kept apart (offline pays mostly the automation's rate).

local Players = game:GetService("Players")

local DataService = require(script.Parent.DataService)

type Sample = {
	-- Bonk Points earned by the player themselves since StartedAt (not by automation).
	Points: number,
	-- Bonk Points earned by the basket and the intern since StartedAt.
	Automation: number,
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

-- Adds points earned by the player's automation (basket, intern; AutomationService). They count as earned (leaderboard)
-- and go into the automation sample, which drives the offline Shiba Bank (Bank.AutomationPerMinute).
function EconomyService.AddAutomationPoints(player: Player, amount: number)
	local state = DataService.GetState(player)
	if not state or not isValidAmount(amount) then
		return
	end
	local whole = math.floor(amount)
	state.BonkPoints += whole
	state.TotalEarned += whole
	local sample = samples[player]
	if sample then
		sample.Automation += whole
	end
	DataService.Replicate(player)
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

-- Bonk Points earned since the last sample (by the player, by the automation) and the seconds that covers, then
-- starts a new sample. Returns (0, 0, 0) and keeps counting while the sample is shorter than `minSeconds` or the
-- player's data is not loaded. OfflineService turns these samples into Bank.IncomePerMinute / AutomationPerMinute.
function EconomyService.TakeIncomeSample(player: Player, minSeconds: number): (number, number, number)
	local sample = samples[player]
	local now = os.clock()
	if not sample or now - sample.StartedAt < minSeconds then
		return 0, 0, 0
	end
	local points, automation, elapsed = sample.Points, sample.Automation, now - sample.StartedAt
	sample.Points = 0
	sample.Automation = 0
	sample.StartedAt = now
	return points, automation, elapsed
end

function EconomyService.Start()
	DataService.OnLoaded(function(player)
		samples[player] = { Points = 0, Automation = 0, StartedAt = os.clock() }
	end)
	Players.PlayerRemoving:Connect(function(player)
		samples[player] = nil
	end)
end

return EconomyService
