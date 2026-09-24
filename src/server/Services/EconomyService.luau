--!strict
-- Bonk Point balance. Server-only: clients can never add points themselves. Points come from validated hits
-- (BonkService), the daily spin, quests, coin flips and the admin testing tools (AdminService).

local DataService = require(script.Parent.DataService)

local EconomyService = {}

function EconomyService.GetPoints(player: Player): number
	local state = DataService.GetState(player)
	return if state then state.BonkPoints else 0
end

-- Adds points. `earned` (default true) also counts them for the leaderboard; admin gifts pass false.
function EconomyService.AddPoints(player: Player, amount: number, earned: boolean?)
	local state = DataService.GetState(player)
	-- `amount == amount` rejects NaN.
	if not state or amount ~= amount or amount <= 0 or amount == math.huge then
		return
	end
	local whole = math.floor(amount)
	state.BonkPoints += whole
	if earned ~= false then
		state.TotalEarned += whole
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

return EconomyService
