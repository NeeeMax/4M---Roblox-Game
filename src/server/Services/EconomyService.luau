--!strict
-- Bonk Point balance. Server-only: clients can never add points themselves. Points come from validated hits
-- (BonkService) and from the admin testing tool (AdminAddPoints, admins only).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)

local DataService = require(script.Parent.DataService)

local adminLimiter = RateLimiter.New(Economy.MaxRequestsPerSecond, 1)

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

local function onAdminAddPoints(player: Player, amount: unknown)
	if not RateLimiter.Allow(adminLimiter, player) or not Admin.IsAdmin(player.UserId) then
		return
	end
	-- Only the fixed button amounts, so even an admin client can't send absurd numbers.
	if typeof(amount) ~= "number" or not table.find(Admin.PointAmounts, amount) then
		return
	end
	EconomyService.AddPoints(player, amount)
end

function EconomyService.Start()
	Net.Get(Net.AdminAddPoints).OnServerEvent:Connect(onAdminAddPoints)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(adminLimiter, player)
	end)
end

return EconomyService
