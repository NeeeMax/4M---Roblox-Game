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

local HITS = Gameplay.Hits

local bonkHit = Net.Get(Net.BonkHit)
local reportLimiter = RateLimiter.New(HITS.MaxReportsPerSecond, 1)
local immuneUntil: { [Player]: number } = {}

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

-- The character's velocity comes from the client, so cap it at what a legit character can do.
local function clampPlayerVelocity(velocity: Vector3, walkSpeed: number): Vector3
	local horizontal = Vector3.new(velocity.X, 0, velocity.Z)
	if horizontal.Magnitude > walkSpeed then
		horizontal = horizontal.Unit * walkSpeed
	end
	local vertical = math.clamp(velocity.Y, -HITS.MaxVerticalPlayerSpeed, HITS.MaxVerticalPlayerSpeed)
	return horizontal + Vector3.new(0, vertical, 0)
end

-- The point of the flight (launch until first contact) closest to `position`: distance and projectile velocity there.
local function closestApproach(info: ProjectileService.ProjectileInfo, position: Vector3): (number, Vector3)
	local flightEnd = (info.LandedAt or os.clock()) - info.LaunchedAt
	local bestDistance = math.huge
	local bestVelocity = info.LaunchVelocity
	local time = 0
	while time <= flightEnd do
		local point, velocity = ProjectileService.GetFlightState(info, time)
		local distance = (point - position).Magnitude
		if distance < bestDistance then
			bestDistance = distance
			bestVelocity = velocity
		end
		time += HITS.FlightSampleStep
	end
	return bestDistance, bestVelocity
end

local function onReportHit(player: Player, projectileId: unknown)
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

	local radius = info.Part.Size.X / 2
	local distance, projectileVelocity = closestApproach(info, root.Position)
	if distance > radius + HITS.HitTolerance then
		return
	end

	ProjectileService.MarkPaid(info)
	immuneUntil[player] = os.clock() + HITS.ImmunityTime

	-- Hit quality: how hard the impact was compared with the projectile's own launch speed.
	-- Running and jumping into a projectile raises it; standing under it gives about 1.0.
	local playerVelocity = clampPlayerVelocity(root.AssemblyLinearVelocity, humanoid.WalkSpeed)
	local ratio = (projectileVelocity - playerVelocity).Magnitude / info.LaunchSpeed
	local quality = getQuality(ratio)

	local sizeMultiplier = info.SizeScale
	local speedMultiplier = info.NominalSpeed / info.Def.BaseSpeed
	local reward = math.max(1, math.floor(info.Def.BaseReward * sizeMultiplier * speedMultiplier * quality.Multiplier))
	EconomyService.AddPoints(player, reward)

	local flat = Vector3.new(projectileVelocity.X, 0, projectileVelocity.Z)
	local knockbackDirection = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zero
	bonkHit:FireClient(player, reward, quality.Name, knockbackDirection)
end

function BonkService.Start()
	Net.Get(Net.ReportHit).OnServerEvent:Connect(onReportHit)
	Players.PlayerRemoving:Connect(function(player)
		immuneUntil[player] = nil
		RateLimiter.Remove(reportLimiter, player)
	end)
end

return BonkService
