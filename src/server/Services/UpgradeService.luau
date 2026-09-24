--!strict
-- Upgrade levels, server-validated purchases, the active-shooter count, and applying MoveSpeed to the character.
-- Other services read upgrade effects through GetValue / GetActiveShooters.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)

local purchaseLimiter = RateLimiter.New(Economy.MaxRequestsPerSecond, 1)
local shooterLimiter = RateLimiter.New(Economy.MaxRequestsPerSecond, 1)

local UpgradeService = {}

-- True once the player's saved data is loaded. Before that, every upgrade reads as level 0.
function UpgradeService.IsReady(player: Player): boolean
	return DataService.GetState(player) ~= nil
end

function UpgradeService.GetLevel(player: Player, id: Types.UpgradeId): number
	local state = DataService.GetState(player)
	return if state then state.UpgradeLevels[id] or 0 else 0
end

-- The upgrade's effect at the player's current level (e.g. WalkSpeed, speed scale, fire interval).
function UpgradeService.GetValue(player: Player, id: Types.UpgradeId): number
	return Upgrades.GetValue(id, UpgradeService.GetLevel(player, id))
end

function UpgradeService.GetActiveShooters(player: Player): number
	local state = DataService.GetState(player)
	return if state then state.ActiveShooters else Upgrades.GetValue("Shooters", 0)
end

local function applyMovement(player: Player)
	local character = player.Character
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not humanoid then
		return
	end
	humanoid.WalkSpeed = UpgradeService.GetValue(player, "MoveSpeed")
	-- Hit quality assumes this jump speed (Gameplay.Hits.MaxVerticalPlayerSpeed).
	humanoid.UseJumpPower = true
	humanoid.JumpPower = Gameplay.Character.JumpPower
end

local function onRequestPurchase(player: Player, upgradeId: unknown)
	if not RateLimiter.Allow(purchaseLimiter, player) then
		return
	end
	if typeof(upgradeId) ~= "string" then
		return
	end
	local def = Upgrades.Defs[upgradeId]
	local state = DataService.GetState(player)
	if not def or not state then
		return
	end
	local level = state.UpgradeLevels[def.Id] or 0
	if level >= def.MaxLevel then
		return
	end
	if not EconomyService.TrySpend(player, Upgrades.GetCost(def.Id, level)) then
		return
	end

	state.UpgradeLevels[def.Id] = level + 1
	if def.Id == "Shooters" then
		-- A newly bought shooter starts active.
		state.ActiveShooters = Upgrades.GetValue("Shooters", level + 1)
	elseif def.Id == "MoveSpeed" then
		applyMovement(player)
	end
	DataService.Replicate(player)
end

local function onSetActiveShooters(player: Player, count: unknown)
	if not RateLimiter.Allow(shooterLimiter, player) then
		return
	end
	-- `count == math.floor(count)` rejects fractions, NaN and infinity.
	if typeof(count) ~= "number" or count ~= math.floor(count) then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local owned = Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters or 0)
	if count < 1 or count > owned then
		return
	end
	state.ActiveShooters = count
	DataService.Replicate(player)
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		character:WaitForChild("Humanoid", 10)
		applyMovement(player)
	end)
	applyMovement(player)
end

function UpgradeService.Start()
	Net.Get(Net.RequestPurchase).OnServerEvent:Connect(onRequestPurchase)
	Net.Get(Net.SetActiveShooters).OnServerEvent:Connect(onSetActiveShooters)

	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(purchaseLimiter, player)
		RateLimiter.Remove(shooterLimiter, player)
	end)

	-- Levels are 0 until the data is loaded; apply the real MoveSpeed once it is.
	DataService.OnLoaded(applyMovement)
end

return UpgradeService
