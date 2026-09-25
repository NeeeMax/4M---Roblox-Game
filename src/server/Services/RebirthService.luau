--!strict
-- Rebirth (prestige, Config/EconomyConfig → Rebirth). Once a player owns the Shiba at ShooterTier level
-- Rebirth.MinShibaTier, they can rebirth: Bonk Dollars go back to the starting amount, every upgrade level (Shibas,
-- Shiba tier, projectile, speed, basket, intern) back to 0, and state.Rebirths goes up by one, which raises every
-- income for good (RewardService.GetRebirthMultiplier). Passes, trophies, Shiba-Index, quests, streaks, boosts,
-- Bonk Rains, pending Shiba Bank earnings and settings are kept. The server alone decides (TryRebirth is called from
-- the rebirth shrine's hold prompt, StationService). Admin tools: ForceRebirth, SetRebirths (AdminService).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local NotifyService = require(script.Parent.NotifyService)
local UpgradeService = require(script.Parent.UpgradeService)

local REBIRTH = EconomyConfig.Rebirth
-- Admin tools never set more rebirths than this (keeps test numbers sane).
local MAX_ADMIN_REBIRTHS = 1000

local RebirthService = {}

-- True if the player owns the Shiba needed to rebirth.
function RebirthService.CanRebirth(player: Player): boolean
	local state = DataService.GetState(player)
	return state ~= nil and (state.UpgradeLevels.ShooterTier or 0) >= REBIRTH.MinShibaTier
end

-- Resets the run and counts one more rebirth.
local function rebirth(player: Player, state: Types.PlayerState)
	for _, id in Upgrades.Order do
		state.UpgradeLevels[id] = 0
	end
	state.ActiveShooters = Upgrades.GetValue("Shooters", 0)
	state.BonkPoints = EconomyConfig.StartingMoney
	state.Rebirths += 1
	-- The measured income rates belong to the old run: without this, rebirthing and leaving would pay the old run's
	-- automation income as offline earnings into the fresh run. Pending earnings stay (they were earned).
	state.Bank.IncomePerMinute = 0
	state.Bank.AutomationPerMinute = 0
	-- SetLevel re-applies the WalkSpeed of Move Speed level 0 to the character (and replicates).
	UpgradeService.SetLevel(player, "MoveSpeed", 0)
	DataService.SaveNow(player)
	local multiplier = EconomyConfig.RebirthMultiplier(state.Rebirths)
	NotifyService.Send(player, `REBIRTH {state.Rebirths}! All income ×{multiplier} for good!`, "Good")
end

-- Rebirths the player if allowed. Returns whether it happened.
function RebirthService.TryRebirth(player: Player): boolean
	local state = DataService.GetState(player)
	if not state then
		return false
	end
	if not RebirthService.CanRebirth(player) then
		local needed = EconomyConfig.Shibas[REBIRTH.MinShibaTier + 1]
		NotifyService.Send(player, `Rebirth needs the {needed.Name}!`, "Bad")
		return false
	end
	rebirth(player, state)
	return true
end

-- Admin testing tool: rebirths right away, without the Shiba requirement.
function RebirthService.ForceRebirth(player: Player)
	local state = DataService.GetState(player)
	if state then
		rebirth(player, state)
	end
end

-- Admin testing tool: sets the rebirth count (0 … MAX_ADMIN_REBIRTHS) without touching anything else.
function RebirthService.SetRebirths(player: Player, count: number)
	local state = DataService.GetState(player)
	-- `count ~= count` = NaN.
	if not state or count ~= count then
		return
	end
	state.Rebirths = math.clamp(math.floor(count), 0, MAX_ADMIN_REBIRTHS)
	DataService.Replicate(player)
	local multiplier = EconomyConfig.RebirthMultiplier(state.Rebirths)
	NotifyService.Send(player, `Rebirths: {state.Rebirths} (income ×{multiplier})`, "Info")
end

return RebirthService
