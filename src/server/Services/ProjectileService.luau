--!strict
-- Spawns projectiles and removes them again. Every shot flies a 45° arc; its gravity is set per projectile
-- (VectorForce) so it lands exactly on the target point. Because launch position, velocity and gravity are known,
-- the server can recompute the whole flight path, which BonkService uses to validate reported hits.
-- The flight ends at the first contact with anything. See docs/GAME_DESIGN.md → Projectiles.

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
	Id: number,
	Part: BasePart,
	Owner: Player,
	Def: Projectiles.ProjectileDef,
	-- Actual launch speed including jitter. Hit quality is measured against it.
	LaunchSpeed: number,
	-- Launch speed without jitter. Used for the reward's speed multiplier.
	NominalSpeed: number,
	SizeScale: number,
	LaunchPosition: Vector3,
	LaunchVelocity: Vector3,
	-- Downward acceleration of this projectile (studs/s²).
	Gravity: number,
	LaunchedAt: number,
	-- Time of the first contact with anything; the flight (and the chance to hit) ends here.
	LandedAt: number?,
	Paid: boolean,
}

local live: { [BasePart]: ProjectileInfo } = {}
local byId: { [number]: ProjectileInfo } = {}
local nextId = 1
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

local function destroy(info: ProjectileInfo)
	live[info.Part] = nil
	byId[info.Id] = nil
	info.Part:Destroy()
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
		destroy(oldest)
	end
end

local function markLanded(info: ProjectileInfo)
	if info.LandedAt then
		return
	end
	info.LandedAt = os.clock()
	info.Part.Transparency = CONFIG.LandedTransparency
	info.Part:SetAttribute(CONFIG.LandedAttribute, true)
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

-- Position and velocity on the flight path `time` seconds after launch.
function ProjectileService.GetFlightState(info: ProjectileInfo, time: number): (Vector3, Vector3)
	local acceleration = Vector3.new(0, -info.Gravity, 0)
	local position = info.LaunchPosition + info.LaunchVelocity * time + acceleration * (0.5 * time * time)
	local velocity = info.LaunchVelocity + acceleration * time
	return position, velocity
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
	local velocity = ProjectileService.GetLaunchDirection(from, target) * speed

	local id = nextId
	nextId += 1

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
	part:SetAttribute(CONFIG.IdAttribute, id)

	local attachment = Instance.new("Attachment")
	attachment.Parent = part
	local antiGravity = Instance.new("VectorForce")
	antiGravity.Attachment0 = attachment
	antiGravity.RelativeTo = Enum.ActuatorRelativeTo.World
	antiGravity.ApplyAtCenterOfMass = true
	antiGravity.Parent = part

	part.Parent = island.ProjectileFolder
	-- Server-owned so the flight matches the path the server uses to validate hits.
	part:SetNetworkOwner(nil)
	antiGravity.Force = Vector3.new(0, part.AssemblyMass * (Workspace.Gravity - gravity), 0)
	part.AssemblyLinearVelocity = velocity
	part.AssemblyAngularVelocity = Vector3.new(
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin)
	)

	local info: ProjectileInfo = {
		Id = id,
		Part = part,
		Owner = owner,
		Def = def,
		LaunchSpeed = speed,
		NominalSpeed = nominalSpeed,
		SizeScale = sizeScale,
		LaunchPosition = from,
		LaunchVelocity = velocity,
		Gravity = gravity,
		LaunchedAt = os.clock(),
		Paid = false,
	}
	live[part] = info
	byId[id] = info

	part.Touched:Connect(function(other)
		-- Characters don't collide with projectiles; hits on the owner come in through ReportHit.
		local character = owner.Character
		if character and other:IsDescendantOf(character) then
			return
		end
		markLanded(info)
	end)
end

function ProjectileService.GetById(id: number): ProjectileInfo?
	return byId[id]
end

-- After this the projectile can't pay out again.
function ProjectileService.MarkPaid(info: ProjectileInfo)
	info.Paid = true
	info.Part.Transparency = CONFIG.LandedTransparency
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
		for _, info in live do
			if info.Owner == player then
				destroy(info)
			end
		end
	end)

	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for part, info in live do
			local landedAt = info.LandedAt
			local landedLongEnough = landedAt ~= nil and now - landedAt >= CONFIG.LifetimeAfterContact
			if landedLongEnough or now - info.LaunchedAt >= CONFIG.MaxLifetime or part.Parent == nil then
				destroy(info)
			end
		end
	end)
end

return ProjectileService
