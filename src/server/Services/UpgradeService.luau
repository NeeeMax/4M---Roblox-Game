--!strict
-- Upgrade levels, server-validated purchases, the active-shooter count, and applying MoveSpeed to the character.
-- Other services read upgrade effects through GetValue / GetLevel / GetFireInterval / GetActiveShooters.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)

-- The Run Faster game pass (Config/Shop): WalkSpeed ×1.5.
local RUN_FASTER_MULTIPLIER = 1.5

local purchaseLimiter = RateLimiter.New(Economy.MaxRequestsPerSecond, 1)
local shooterLimiter = RateLimiter.New(Economy.MaxRequestsPerSecond, 1)

local UpgradeService = {}

-- True once the player's saved data is loaded. Before that, every upgrade reads as level 0.
function UpgradeService.IsReady(player: Player): boolean
	return DataService.GetState(player) ~= nil
end

-- `id` is an UpgradeId (a plain string is accepted because level tables are keyed by string).
function UpgradeService.GetLevel(player: Player, id: string): number
	local state = DataService.GetState(player)
	return if state then state.UpgradeLevels[id] or 0 else 0
end

-- The upgrade's effect at the player's current level (e.g. WalkSpeed, owned shooters, tier index).
function UpgradeService.GetValue(player: Player, id: Types.UpgradeId): number
	return Upgrades.GetValue(id, UpgradeService.GetLevel(player, id))
end

function UpgradeService.GetActiveShooters(player: Player): number
	local state = DataService.GetState(player)
	return if state then state.ActiveShooters else Upgrades.GetValue("Shooters", 0)
end

-- Seconds between two throws of one Shiba: set by the Shiba tier, halved by the fire-rate boost.
function UpgradeService.GetFireInterval(player: Player): number
	return RewardService.GetShooterTier(player).FireInterval / BoostService.GetMultiplier(player, "FireRate")
end

local function applyMovement(player: Player)
	local character = player.Character
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not humanoid then
		return
	end
	local state = DataService.GetState(player)
	local passMultiplier = if state and state.Passes.RunFaster then RUN_FASTER_MULTIPLIER else 1
	humanoid.WalkSpeed = UpgradeService.GetValue(player, "MoveSpeed") * passMultiplier
	-- Hit quality assumes this jump speed (Gameplay.Hits.MaxVerticalPlayerSpeed).
	humanoid.UseJumpPower = true
	humanoid.JumpPower = Gameplay.Character.JumpPower
end

-- Sets a level directly (admin testing tool), clamped to 0..MaxLevel.
function UpgradeService.SetLevel(player: Player, id: string, level: number)
	local state = DataService.GetState(player)
	local def = Upgrades.Defs[id]
	if not state or not def then
		return
	end
	state.UpgradeLevels[id] = math.clamp(math.floor(level), 0, Upgrades.GetMaxLevel(id, state.Passes))
	local owned = Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters or 0)
	if id == "Shooters" then
		state.ActiveShooters = owned
	end
	state.ActiveShooters = math.clamp(state.ActiveShooters, 1, owned)
	applyMovement(player)
	DataService.Replicate(player)
end

-- Buys up to `count` levels of upgrade `id`, one after another, while the player can afford them and the upgrade
-- is below its max level. Tells the player what happened. Returns how many levels were bought (0 = none).
-- Used by the RequestPurchase remote (1 level) and the upgrade stands (StationService).
function UpgradeService.TryPurchase(player: Player, id: string, count: number): number
	local def = Upgrades.Defs[id]
	local state = DataService.GetState(player)
	if not def or not state or count ~= count then
		return 0
	end
	-- Later upgrades (basket, intern) unlock with a Shiba tier (EconomyConfig.UnlockAtShibaTier).
	local unlockTier = EconomyConfig.UnlockAtShibaTier[def.Id] or 0
	if (state.UpgradeLevels.ShooterTier or 0) < unlockTier then
		local shiba = EconomyConfig.Shibas[unlockTier + 1]
		NotifyService.Send(player, `{def.DisplayName} unlocks with the {shiba.Name}!`, "Bad")
		return 0
	end
	local wanted = math.max(1, math.floor(count))
	local maxLevel = Upgrades.GetMaxLevel(def.Id, state.Passes)
	local startLevel = state.UpgradeLevels[def.Id] or 0
	local bought = 0
	local missing = 0
	while bought < wanted do
		local level = startLevel + bought
		if level >= maxLevel then
			break
		end
		local cost = Upgrades.GetCost(def.Id, level)
		if not EconomyService.TrySpend(player, cost) then
			missing = cost - state.BonkPoints
			break
		end
		bought += 1
		state.UpgradeLevels[def.Id] = level + 1
	end

	if bought == 0 then
		if startLevel >= maxLevel then
			NotifyService.Send(player, `{def.DisplayName} is maxed out!`, "Info")
		else
			NotifyService.Send(player, `You need {Format.Money(missing)} more`, "Bad")
		end
		return 0
	end

	local newLevel = startLevel + bought
	if def.Id == "Shooters" then
		-- A newly bought shooter starts active.
		state.ActiveShooters = Upgrades.GetValue("Shooters", newLevel)
	elseif def.Id == "MoveSpeed" then
		applyMovement(player)
	end
	DataService.Replicate(player)
	local times = if bought > 1 then ` (×{bought})` else ""
	NotifyService.Send(player, `{def.DisplayName}: {Upgrades.FormatValue(def.Id, newLevel)}!{times}`, "Good")
	QuestService.Record(player, "Upgrade", bought)
	return bought
end

local function onRequestPurchase(player: Player, upgradeId: unknown)
	if not RateLimiter.Allow(purchaseLimiter, player) then
		return
	end
	if typeof(upgradeId) ~= "string" or not Upgrades.Defs[upgradeId] then
		return
	end
	local state = DataService.GetState(player)
	-- The menu only asks for levels below the max; stay quiet like before if it does anyway.
	if not state or (state.UpgradeLevels[upgradeId] or 0) >= Upgrades.GetMaxLevel(upgradeId, state.Passes) then
		return
	end
	UpgradeService.TryPurchase(player, upgradeId, 1)
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

	-- Levels are 0 until the data is loaded; apply the real MoveSpeed once it is (and after an admin reset).
	DataService.OnLoaded(applyMovement)
	-- Re-apply when the Run Faster pass is bought or toggled (passes change through DataService.Replicate).
	local hadRunFaster: { [Player]: boolean } = {}
	DataService.OnReplicated(function(player)
		local state = DataService.GetState(player)
		local has = state ~= nil and state.Passes.RunFaster == true
		if (hadRunFaster[player] or false) ~= has then
			hadRunFaster[player] = has
			applyMovement(player)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		hadRunFaster[player] = nil
	end)
end

return UpgradeService
