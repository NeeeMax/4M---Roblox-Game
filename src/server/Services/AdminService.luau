--!strict
-- Admin testing tools (Config/Admin): one remote, AdminCommand(command, argument). The server checks admin rights
-- on every request; the client only decides whether the ADMIN button is shown. Commands act on the sender only.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local BoostService = require(script.Parent.BoostService)
local DailySpinService = require(script.Parent.DailySpinService)
local EventService = require(script.Parent.EventService)
local OfflineService = require(script.Parent.OfflineService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local IslandService = require(script.Parent.IslandService)
local NPCShooterService = require(script.Parent.NPCShooterService)
local NotifyService = require(script.Parent.NotifyService)
local QuestService = require(script.Parent.QuestService)
local RainService = require(script.Parent.RainService)
local ShopService = require(script.Parent.ShopService)
local StreakService = require(script.Parent.StreakService)
local UpgradeService = require(script.Parent.UpgradeService)

local limiter = RateLimiter.New(10, 1)

type Handler = (player: Player, argument: unknown) -> ()

local function upgradeId(argument: unknown): Types.UpgradeId?
	for _, id: Types.UpgradeId in Upgrades.Order do
		if id == argument then
			return id
		end
	end
	return nil
end

local function changeLevel(player: Player, argument: unknown, delta: number)
	local id = upgradeId(argument)
	if id then
		UpgradeService.SetLevel(player, id, UpgradeService.GetLevel(player, id) + delta)
	end
end

local function maxUpgrades(player: Player)
	for _, id: Types.UpgradeId in Upgrades.Order do
		-- SetLevel clamps to the player's own max (the +2 Shiba Slots pass raises it).
		UpgradeService.SetLevel(player, id, math.huge)
	end
end

local HANDLERS: { [string]: Handler } = {
	AddPoints = function(player, argument)
		-- Only the fixed button amounts, so even an admin client can't send absurd numbers.
		if typeof(argument) == "number" and table.find(Admin.PointAmounts, argument) then
			EconomyService.AddPoints(player, argument, false)
		end
	end,
	ClearPoints = function(player)
		EconomyService.SetPoints(player, 0)
	end,
	ResetAll = function(player)
		DataService.Reset(player)
		NotifyService.Send(player, "Everything reset to a new save", "Info")
	end,
	MaxUpgrades = maxUpgrades,
	UpgradeUp = function(player, argument)
		changeLevel(player, argument, 1)
	end,
	UpgradeDown = function(player, argument)
		changeLevel(player, argument, -1)
	end,
	ResetSpin = function(player)
		DailySpinService.ResetCooldown(player)
	end,
	ResetQuests = function(player)
		QuestService.Reset(player)
	end,
	CompleteQuests = function(player)
		QuestService.CompleteAll(player)
	end,
	BoostPoints = function(player)
		BoostService.Give(player, "Points", 600)
	end,
	BoostFireRate = function(player)
		BoostService.Give(player, "FireRate", 600)
	end,
	ClearBoosts = function(player)
		BoostService.Clear(player)
	end,
	TeleportHub = function(player)
		IslandService.TeleportToHub(player)
	end,
	TeleportIsland = function(player)
		IslandService.SpawnOnIsland(player)
	end,
	FireNow = function(player)
		NPCShooterService.FireNow(player)
	end,
	GiveRain = function(player)
		RainService.Give(player)
	end,
	StartRain = function(player)
		RainService.Give(player)
		RainService.TryStart(player)
	end,
	TogglePass = function(player, argument)
		if typeof(argument) == "string" then
			ShopService.TogglePass(player, argument)
		end
	end,
	ResetStarter = function(player)
		ShopService.ResetStarterPack(player)
	end,
	ResetGifts = function(player)
		StreakService.Reset(player)
	end,
	StartEvent = function(_player, argument)
		if typeof(argument) == "string" then
			EventService.StartNow(argument)
		end
	end,
	StopEvent = function()
		EventService.StopNow()
	end,
	SimulateOffline = function(player)
		OfflineService.SimulateAway(player, 3600)
	end,
	AllTrophies = function(player)
		local state = DataService.GetState(player)
		if state then
			for _, trophy in Shop.Trophies do
				state.Trophies[trophy.Id] = true
			end
			DataService.Replicate(player)
		end
	end,
}

local AdminService = {}

local function onAdminCommand(player: Player, command: unknown, argument: unknown)
	if not RateLimiter.Allow(limiter, player) or not Admin.IsAdmin(player.UserId) then
		return
	end
	if typeof(command) ~= "string" then
		return
	end
	local handler = HANDLERS[command]
	if handler then
		handler(player, argument)
	end
end

function AdminService.Start()
	Net.Get(Net.AdminCommand).OnServerEvent:Connect(onAdminCommand)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(limiter, player)
	end)
end

return AdminService
