--!strict
-- Server-side hit detection and rewards. Every frame, each live projectile checks whether it overlaps its
-- owner's character. A hit pays once, starts hit immunity, and tells the client to play the bonk effects.
-- See docs/GAME_DESIGN.md → Hits.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)

local EconomyService = require(script.Parent.EconomyService)
local ProjectileService = require(script.Parent.ProjectileService)

local HITS = Gameplay.Hits

local bonkHit = Net.Get(Net.BonkHit)
local immuneUntil: { [Player]: number } = {}
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include

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

local function onHit(player: Player, info: ProjectileService.ProjectileInfo, root: BasePart, humanoid: Humanoid)
	ProjectileService.MarkSpent(info.Part)
	immuneUntil[player] = os.clock() + HITS.ImmunityTime

	-- Hit quality: how hard the impact was compared with the projectile's own launch speed.
	-- Running and jumping into a projectile raises it; standing under it gives about 1.0.
	local projectileVelocity = info.Part.AssemblyLinearVelocity
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

local function checkHits()
	local now = os.clock()
	for part, info in ProjectileService.GetLive() do
		if info.SpentAt then
			continue
		end
		local player = info.Owner
		if (immuneUntil[player] or 0) > now then
			-- Ignored, not spent: it can still hit once immunity ends.
			continue
		end
		local character = player.Character
		if not character then
			continue
		end
		local root = character:FindFirstChild("HumanoidRootPart")
		local humanoid = character:FindFirstChildOfClass("Humanoid")
		if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
			continue
		end

		local radius = part.Size.X / 2
		-- Cheap distance test first; the exact overlap query only runs for projectiles near the character.
		if (part.Position - root.Position).Magnitude > radius + HITS.BroadPhaseDistance then
			continue
		end
		overlapParams.FilterDescendantsInstances = { character }
		if #Workspace:GetPartBoundsInRadius(part.Position, radius, overlapParams) > 0 then
			onHit(player, info, root, humanoid)
		end
	end
end

function BonkService.Start()
	Players.PlayerRemoving:Connect(function(player)
		immuneUntil[player] = nil
	end)
	RunService.Heartbeat:Connect(checkHits)
end

return BonkService
