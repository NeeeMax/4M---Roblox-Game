--!strict
-- Rebirth (prestige, Config/EconomyConfig → Rebirth). Once a player owns the Shiba at ShooterTier level
-- Rebirth.MinShibaTier, they can rebirth: Bonk Dollars go back to the starting amount, every upgrade level (Shibas,
-- Shiba tier, projectile, speed, basket, intern) back to 0, and state.Rebirths goes up by one, which raises every
-- income for good (RewardService.GetRebirthMultiplier). Passes, trophies, Shiba-Index, quests, streaks, boosts,
-- Bonk Rains, the Shiba Bank and settings are kept. The server alone decides (TryRebirth is called from the rebirth
-- stand's hold prompt, StationService).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local NotifyService = require(script.Parent.NotifyService)

local REBIRTH = EconomyConfig.Rebirth

local RebirthService = {}

-- True if the player owns the Shiba needed to rebirth.
function RebirthService.CanRebirth(player: Player): boolean
	local state = DataService.GetState(player)
	return state ~= nil and (state.UpgradeLevels.ShooterTier or 0) >= REBIRTH.MinShibaTier
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
	for _, id in Upgrades.Order do
		state.UpgradeLevels[id] = 0
	end
	state.ActiveShooters = Upgrades.GetValue("Shooters", 0)
	state.BonkPoints = EconomyConfig.StartingMoney
	state.Rebirths += 1
	DataService.Replicate(player)
	DataService.SaveNow(player)
	local multiplier = EconomyConfig.RebirthMultiplier(state.Rebirths)
	NotifyService.Send(player, `REBIRTH {state.Rebirths}! All income ×{multiplier} for good!`, "Good")
	return true
end

return RebirthService
