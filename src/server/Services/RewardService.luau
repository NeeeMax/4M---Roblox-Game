--!strict
-- What one normal bonk is worth to a player right now (projectile tier × Shiba tier). The daily spin and quests
-- pay in multiples of it ("hits"), so their rewards stay worth it at every stage of the game.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local DataService = require(script.Parent.DataService)

local TIERS = Gameplay.Shooters.Tiers

local RewardService = {}

function RewardService.GetShooterTier(player: Player): typeof(TIERS[1])
	local state = DataService.GetState(player)
	local level = if state then state.UpgradeLevels.ShooterTier or 0 else 0
	return TIERS[math.clamp(level + 1, 1, #TIERS)]
end

function RewardService.GetHitValue(player: Player): number
	local state = DataService.GetState(player)
	local projectileLevel = if state then state.UpgradeLevels.ProjectileTier or 0 else 0
	return Projectiles.ForTier(projectileLevel).BaseReward * RewardService.GetShooterTier(player).RewardMultiplier
end

-- `hits` normal bonks' worth, at least 1.
function RewardService.Hits(player: Player, hits: number): number
	return math.max(1, math.floor(RewardService.GetHitValue(player) * hits))
end

return RewardService
