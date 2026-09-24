--!strict
-- Bonk Point balance. Server-only: clients can never add points, only BonkService does on a validated hit.

local DataService = require(script.Parent.DataService)

local EconomyService = {}

function EconomyService.GetPoints(player: Player): number
	local state = DataService.GetState(player)
	return if state then state.BonkPoints else 0
end

function EconomyService.AddPoints(player: Player, amount: number)
	local state = DataService.GetState(player)
	-- `amount == amount` rejects NaN.
	if not state or amount ~= amount or amount <= 0 then
		return
	end
	state.BonkPoints += math.floor(amount)
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

return EconomyService
