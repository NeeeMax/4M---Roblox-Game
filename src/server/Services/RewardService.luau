--!strict
-- Shared reward helpers:
-- * what one normal bonk is worth to a player right now (projectile tier × Shiba tier). The daily spin, quests and
--   gifts pay in multiples of it ("hits"), so their rewards stay worth it at every stage of the game;
-- * handing out a reward (points, boost, Bonk Rain, trophy) from the spin, login streak or playtime gifts;
-- * which game passes a player owns (ShopService keeps state.Passes up to date).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)
local Types = require(ReplicatedStorage.Shared.Types)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)

local TIERS = Gameplay.Shooters.Tiers

local RewardService = {}

function RewardService.HasPass(player: Player, id: string): boolean
	local state = DataService.GetState(player)
	return state ~= nil and state.Passes[id] == true
end

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

-- Hands out a reward and returns what the player got, in words ("+B$ 1,200", "Bonk Rain").
function RewardService.Give(player: Player, reward: Hub.Reward): string
	local state = DataService.GetState(player)
	if not state then
		return ""
	end
	local parts: { string } = {}
	if reward.Kind == "Boost" and reward.Boost and reward.Seconds then
		BoostService.Give(player, reward.Boost :: Types.BoostId, reward.Seconds)
		table.insert(parts, reward.Text)
	elseif reward.Kind == "BonkRain" then
		state.BonkRains += 1
		DataService.Replicate(player)
		table.insert(parts, "+1 Bonk Rain")
	elseif reward.Kind == "Trophy" and reward.Trophy then
		state.Trophies[reward.Trophy] = true
		DataService.Replicate(player)
		table.insert(parts, "new trophy")
	end
	if reward.Hits then
		local amount = RewardService.Hits(player, reward.Hits)
		EconomyService.AddPoints(player, amount)
		table.insert(parts, `+{Format.Money(amount)}`)
	end
	return table.concat(parts, " · ")
end

return RewardService
