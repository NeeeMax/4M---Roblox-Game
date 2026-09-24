--!strict
-- Spawns projectiles and removes them again. Every shot flies a 45° arc; its gravity is set per projectile
-- (VectorForce) so it lands exactly on the target point. A projectile is "spent" on its first contact with
-- anything and never pays after that. See docs/GAME_DESIGN.md → Projectiles.

local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local IslandService = require(script.Parent.IslandService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Projectiles
local PROJECTILE_GROUP = "Projectiles"
local CHARACTER_GROUP = "Characters"

export type ProjectileInfo = {
	Part: BasePart,
	Owner: Player,
	Def: Projectiles.ProjectileDef,
	-- Actual launch speed including jitter. Hit quality is measured against it.
	LaunchSpeed: number,
	-- Launch speed without jitter. Used for the reward's speed multiplier.
	NominalSpeed: number,
	SizeScale: number,
	LaunchedAt: number,
	SpentAt: number?,
}

local live: { [BasePart]: ProjectileInfo } = {}
local random = Random.new()

local ProjectileService = {}

local function registerGroup(name: string)
	if not PhysicsService:IsCollisionGroupRegistered(name) then
		PhysicsService:RegisterCollisionGroup(name)
	end
end

local function setCharacterGroup(character: Model)
	for _, descendant in character:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.CollisionGroup = CHARACTER_GROUP
		end
	end
	character.DescendantAdded:Connect(function(descendant)
		if descendant:IsA("BasePart") then
			descendant.CollisionGroup = CHARACTER_GROUP
		end
	end)
end

local function destroy(part: BasePart)
	live[part] = nil
	part:Destroy()
end

-- Enforces MaxPerIsland by destroying the owner's oldest projectile.
local function makeRoom(owner: Player)
	local count = 0
	local oldest: ProjectileInfo? = nil
	for _, info in live do
		if info.Owner == owner then
			count += 1
			if not oldest or info.LaunchedAt < oldest.LaunchedAt then
				oldest = info
			end
		end
	end
	if count >= CONFIG.MaxPerIsland and oldest then
		destroy(oldest.Part)
	end
end

function ProjectileService.GetDef(): Projectiles.ProjectileDef
	return Projectiles.Defs[Projectiles.DefaultId]
end

-- Projectile diameter for this player's current ProjectileSize level.
function ProjectileService.GetDiameter(player: Player): number
	return ProjectileService.GetDef().Diameter * UpgradeService.GetValue(player, "ProjectileSize")
end

-- Unit vector from `from` toward `to` (horizontally), tilted up by the launch angle.
function ProjectileService.GetLaunchDirection(from: Vector3, to: Vector3): Vector3
	local flat = Vector3.new(to.X - from.X, 0, to.Z - from.Z)
	local horizontal = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local angle = math.rad(CONFIG.LaunchAngleDegrees)
	return horizontal * math.cos(angle) + Vector3.yAxis * math.sin(angle)
end

-- Fires one projectile for `owner` from `from` so that it lands on `target`.
function ProjectileService.Fire(owner: Player, from: Vector3, target: Vector3)
	local island = IslandService.GetIsland(owner)
	if not island then
		return
	end
	makeRoom(owner)

	local def = ProjectileService.GetDef()
	local sizeScale = UpgradeService.GetValue(owner, "ProjectileSize")
	-- Bigger projectiles fly slower: that is the price of the easier, bigger-paying hit.
	local nominalSpeed = def.BaseSpeed * UpgradeService.GetValue(owner, "ProjectileSpeed") * sizeScale ^ -0.5
	local speed = nominalSpeed * (1 + random:NextNumber(-CONFIG.SpeedJitter, CONFIG.SpeedJitter))

	-- Solve for the gravity that makes a launch at this speed and angle land on the target:
	-- horizontal: distance = vH·t  →  t = distance / vH;  vertical: dy = vY·t − ½·g·t²  →  g = 2(vY·t − dy) / t².
	local angle = math.rad(CONFIG.LaunchAngleDegrees)
	local horizontalSpeed = speed * math.cos(angle)
	local verticalSpeed = speed * math.sin(angle)
	local distance = math.max(Vector3.new(target.X - from.X, 0, target.Z - from.Z).Magnitude, 1)
	local flightTime = distance / horizontalSpeed
	local gravity = 2 * (verticalSpeed * flightTime - (target.Y - from.Y)) / (flightTime * flightTime)

	local part = Instance.new("Part")
	part.Name = def.Id
	part.Shape = Enum.PartType.Ball
	part.Size = Vector3.one * def.Diameter * sizeScale
	part.Color = def.Color
	part.Material = def.Material
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.CollisionGroup = PROJECTILE_GROUP
	part.CFrame = CFrame.new(from)

	local attachment = Instance.new("Attachment")
	attachment.Parent = part
	local antiGravity = Instance.new("VectorForce")
	antiGravity.Attachment0 = attachment
	antiGravity.RelativeTo = Enum.ActuatorRelativeTo.World
	antiGravity.ApplyAtCenterOfMass = true
	antiGravity.Parent = part

	part.Parent = island.ProjectileFolder
	-- Server-owned so the server simulates it and hit checks see the true position.
	part:SetNetworkOwner(nil)
	antiGravity.Force = Vector3.new(0, part.AssemblyMass * (Workspace.Gravity - gravity), 0)
	part.AssemblyLinearVelocity = ProjectileService.GetLaunchDirection(from, target) * speed
	part.AssemblyAngularVelocity = Vector3.new(
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin)
	)

	live[part] = {
		Part = part,
		Owner = owner,
		Def = def,
		LaunchSpeed = speed,
		NominalSpeed = nominalSpeed,
		SizeScale = sizeScale,
		LaunchedAt = os.clock(),
	}

	part.Touched:Connect(function(other)
		local info = live[part]
		if not info or info.SpentAt then
			return
		end
		-- Characters don't collide with projectiles; BonkService decides about hits on the owner.
		local character = info.Owner.Character
		if character and other:IsDescendantOf(character) then
			return
		end
		ProjectileService.MarkSpent(part)
	end)
end

-- After this the projectile can't pay out any more; it fades and is removed after LifetimeAfterContact.
function ProjectileService.MarkSpent(part: BasePart)
	local info = live[part]
	if info and not info.SpentAt then
		info.SpentAt = os.clock()
		part.Transparency = CONFIG.SpentTransparency
	end
end

-- All live projectiles. Read-only for callers.
function ProjectileService.GetLive(): { [BasePart]: ProjectileInfo }
	return live
end

function ProjectileService.Init()
	registerGroup(PROJECTILE_GROUP)
	registerGroup(CHARACTER_GROUP)
	-- Projectiles pass through characters (knockback comes from the hit code) and through each other,
	-- so a ball lying on the ground can't block the next one.
	PhysicsService:CollisionGroupSetCollidable(PROJECTILE_GROUP, CHARACTER_GROUP, false)
	PhysicsService:CollisionGroupSetCollidable(PROJECTILE_GROUP, PROJECTILE_GROUP, false)
end

function ProjectileService.Start()
	local function onPlayerAdded(player: Player)
		player.CharacterAdded:Connect(setCharacterGroup)
		if player.Character then
			setCharacterGroup(player.Character)
		end
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	Players.PlayerRemoving:Connect(function(player: Player)
		for part, info in live do
			if info.Owner == player then
				destroy(part)
			end
		end
	end)

	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for part, info in live do
			local spentLongEnough = info.SpentAt ~= nil and now - info.SpentAt >= CONFIG.LifetimeAfterContact
			if spentLongEnough or now - info.LaunchedAt >= CONFIG.MaxLifetime or part.Parent == nil then
				destroy(part)
			end
		end
	end)
end

return ProjectileService
