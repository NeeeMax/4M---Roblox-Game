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
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local BoostService = require(script.Parent.BoostService)
local EconomyService = require(script.Parent.EconomyService)
local EventService = require(script.Parent.EventService)
local IndexService = require(script.Parent.IndexService)
local ProjectileService = require(script.Parent.ProjectileService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)
local UpgradeService = require(script.Parent.UpgradeService)

local HITS = Gameplay.Hits
local COMBO = Gameplay.Combo
-- Quality names from Hard up count for "Hard (or better)" quests.
local HARD_QUALITIES = { Hard = true, Massive = true, Legendary = true }

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
	local timeBetweenShots = UpgradeService.GetFireInterval(player) / UpgradeService.GetActiveShooters(player)
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
	if not info or info.Owner ~= player or info.Paid or not ProjectileService.AcceptsReports(info) then
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

	-- Only the part of the path the projectile has already travelled (flight, bounces, settling hops) counts; the
	-- resting position at its end is the last point. The pickup sphere is radius + PickupPadding, as on the client.
	local plan = info.Plan
	local travelled = os.clock() - info.LaunchedAt
	local pickupRadius = plan.Radius + HITS.PickupPadding
	local distance, projectileVelocity = ProjectileService.ClosestApproach(plan, root.Position, travelled)
	if distance > pickupRadius + HITS.HitTolerance then
		return
	end
	-- Head bonus: the client saw the head touch it, and the path really passed close to the head.
	local head = (character :: Model):FindFirstChild("Head")
	local onHead = false
	if onHeadClaim == true and head and head:IsA("BasePart") then
		local headDistance = ProjectileService.ClosestApproach(plan, head.Position, travelled)
		onHead = headDistance <= pickupRadius + HITS.HeadTolerance
	end

	ProjectileService.MarkPaid(info)
	immuneUntil[player] = os.clock() + HITS.ImmunityTime

	-- Hit quality: how hard the impact was compared with the projectile's own launch speed.
	-- Running and jumping into a projectile raises it; standing under it gives about 1.0.
	local playerVelocity = clampPlayerVelocity(root.AssemblyLinearVelocity, humanoid.WalkSpeed)
	local ratio = (projectileVelocity - playerVelocity).Magnitude / plan.Speed
	local quality = getQuality(ratio)

	local combo, comboMultiplier, window = registerCombo(player, os.clock())
	local tier = RewardService.GetShooterTier(player)
	local goldenMultiplier = if plan.Golden then Gameplay.Projectiles.GoldenMultiplier else 1
	local passMultiplier = (
		if RewardService.HasPass(player, "DoublePoints") then Shop.Pass.DoublePointsMultiplier else 1
	) * (if RewardService.HasPass(player, "VIP") then Shop.Pass.VIPMultiplier else 1)
	local headMultiplier = if onHead then HITS.HeadMultiplier else 1
	local reward = math.max(
		1,
		math.floor(
			plan.Def.BaseReward
				* quality.Multiplier
				* headMultiplier
				* comboMultiplier
				* tier.RewardMultiplier
				* BoostService.GetMultiplier(player, "Points")
				* goldenMultiplier
				* passMultiplier
				* EventService.RewardMultiplier(plan.Mega) -- server events: DoublePoints, MegaStick
		)
	)
	EconomyService.AddPoints(player, reward)
	if plan.Golden then
		IndexService.DiscoverGolden(player) -- Shiba-Index: first golden catch
	end
	QuestService.Record(player, "Hit", 1)
	QuestService.Record(player, "Combo", combo)
	if onHead then
		QuestService.Record(player, "HeadHit", 1)
	end
	if HARD_QUALITIES[quality.Name] then
		QuestService.Record(player, "HardHit", 1)
	end

	local flat = Vector3.new(projectileVelocity.X, 0, projectileVelocity.Z)
	local knockbackDirection = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zero
	bonkHit:FireClient(player, reward, quality.Name, knockbackDirection, onHead, combo, window, plan.Golden)
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
