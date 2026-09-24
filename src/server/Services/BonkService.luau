--!strict
-- Validates hits reported by clients and awards Bonk Points. The client says "this projectile touched me"
-- (what the player saw); the server checks the claim against the projectile's exact flight path and the
-- character's position on the server, and alone decides. See docs/decisions/0003.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)

local EconomyService = require(script.Parent.EconomyService)
local ProjectileService = require(script.Parent.ProjectileService)
local UpgradeService = require(script.Parent.UpgradeService)

local HITS = Gameplay.Hits
local COMBO = Gameplay.Combo
local TIERS = Gameplay.Shooters.Tiers

type Combo = {
	Count: number,
	-- os.clock() until which the next hit continues the combo.
	Until: number,
}

local bonkHit = Net.Get(Net.BonkHit)
local reportLimiter = RateLimiter.New(HITS.MaxReportsPerSecond, 1)
local immuneUntil: { [Player]: number } = {}
local combos: { [Player]: Combo } = {}

local BonkService = {}

local function getQuality(ratio: number): Economy.HitQualityDef
	local chosen = Economy.HitQualities[1]
	for _, quality in Economy.HitQualities do
		if ratio >= quality.MinRatio then
			chosen = quality
		end
	end
	return chosen
end

-- How long after a hit the next one still continues the combo: longer when shots come less often.
local function comboWindow(player: Player): number
	local timeBetweenShots = UpgradeService.GetValue(player, "FireRate") / UpgradeService.GetActiveShooters(player)
	return COMBO.BaseWindow + COMBO.ShotsWindow * timeBetweenShots
end

-- Counts this hit into the player's combo. Returns the combo length (1 = first hit), its multiplier and the window.
local function registerCombo(player: Player, now: number): (number, number, number)
	local existing = combos[player]
	local combo: Combo = if existing and now <= existing.Until then existing else { Count = 0, Until = 0 }
	combos[player] = combo
	local window = comboWindow(player)
	combo.Count += 1
	combo.Until = now + window
	local multiplier = math.min(1 + COMBO.Step * (combo.Count - 1), COMBO.MaxMultiplier)
	return combo.Count, multiplier, window
end

-- The character's velocity comes from the client, so cap it at what a legit character can do.
local function clampPlayerVelocity(velocity: Vector3, walkSpeed: number): Vector3
	local horizontal = Vector3.new(velocity.X, 0, velocity.Z)
	if horizontal.Magnitude > walkSpeed then
		horizontal = horizontal.Unit * walkSpeed
	end
	local vertical = math.clamp(velocity.Y, -HITS.MaxVerticalPlayerSpeed, HITS.MaxVerticalPlayerSpeed)
	return horizontal + Vector3.new(0, vertical, 0)
end

local function onReportHit(player: Player, projectileId: unknown, onHeadClaim: unknown)
	if not RateLimiter.Allow(reportLimiter, player) or typeof(projectileId) ~= "number" then
		return
	end
	local info = ProjectileService.GetById(projectileId)
	if not info or info.Owner ~= player or info.Paid then
		return
	end
	if (immuneUntil[player] or 0) > os.clock() then
		return
	end
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return
	end

	-- Only the part of the path the projectile has already travelled (flight and bounces) counts.
	local plan = info.Plan
	local travelled = os.clock() - info.LaunchedAt
	local distance, projectileVelocity = ProjectileService.ClosestApproach(plan, root.Position, travelled)
	if distance > plan.Radius + HITS.HitTolerance then
		return
	end
	-- Head bonus: the client saw the head touch it, and the path really passed close to the head.
	local head = (character :: Model):FindFirstChild("Head")
	local onHead = false
	if onHeadClaim == true and head and head:IsA("BasePart") then
		local headDistance = ProjectileService.ClosestApproach(plan, head.Position, travelled)
		onHead = headDistance <= plan.Radius + HITS.HeadTolerance
	end

	ProjectileService.MarkPaid(info)
	immuneUntil[player] = os.clock() + HITS.ImmunityTime

	-- Hit quality: how hard the impact was compared with the projectile's own launch speed.
	-- Running and jumping into a projectile raises it; standing under it gives about 1.0.
	local playerVelocity = clampPlayerVelocity(root.AssemblyLinearVelocity, humanoid.WalkSpeed)
	local ratio = (projectileVelocity - playerVelocity).Magnitude / plan.Speed
	local quality = getQuality(ratio)

	local combo, comboMultiplier, window = registerCombo(player, os.clock())
	local tier = TIERS[UpgradeService.GetLevel(player, "ShooterTier") + 1] or TIERS[1]
	local sizeMultiplier = plan.SizeScale
	local speedMultiplier = plan.NominalSpeed / plan.Def.BaseSpeed
	local headMultiplier = if onHead then HITS.HeadMultiplier else 1
	local reward = math.max(
		1,
		math.floor(
			plan.Def.BaseReward
				* sizeMultiplier
				* speedMultiplier
				* quality.Multiplier
				* headMultiplier
				* comboMultiplier
				* tier.RewardMultiplier
		)
	)
	EconomyService.AddPoints(player, reward)

	local flat = Vector3.new(projectileVelocity.X, 0, projectileVelocity.Z)
	local knockbackDirection = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zero
	bonkHit:FireClient(player, reward, quality.Name, knockbackDirection, onHead, combo, window)
end

function BonkService.Start()
	Net.Get(Net.ReportHit).OnServerEvent:Connect(onReportHit)
	Players.PlayerRemoving:Connect(function(player)
		immuneUntil[player] = nil
		combos[player] = nil
		RateLimiter.Remove(reportLimiter, player)
	end)
end

return BonkService
