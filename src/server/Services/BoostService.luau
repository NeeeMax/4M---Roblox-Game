--!strict
-- Timed boosts (2× points, 2× fire rate) from the daily spin or the admin menu. Stored as Unix end times in the
-- player's saved state, so they keep running across rejoins. Multipliers: Config/Hub → Boosts.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)

local BoostService = {}

function BoostService.IsActive(player: Player, id: Types.BoostId): boolean
	local state = DataService.GetState(player)
	return state ~= nil and (state.Boosts[id] or 0) > os.time()
end

-- The boost's multiplier while it runs, else 1.
function BoostService.GetMultiplier(player: Player, id: Types.BoostId): number
	if not BoostService.IsActive(player, id) then
		return 1
	end
	if id == "Points" then
		return Hub.Boosts.Points
	elseif id == "FireRate" then
		return Hub.Boosts.FireRate
	end
	-- The Magnet boost has no multiplier (AutoCatchService checks IsActive).
	return 1
end

-- Starts the boost, or extends it if it already runs.
function BoostService.Give(player: Player, id: Types.BoostId, seconds: number)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Boosts[id] = math.max(state.Boosts[id] or 0, os.time()) + seconds
	DataService.Replicate(player)
end

function BoostService.Clear(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Boosts = {}
	DataService.Replicate(player)
end

return BoostService
