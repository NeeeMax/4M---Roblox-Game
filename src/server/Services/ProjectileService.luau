--!strict
-- Plans, spawns and removes projectiles. Every shot is planned in full before it is fired: a 45° arc with its own
-- gravity so it lands exactly on the target, then `Bounces` bounces on the island, then it disappears on the next
-- ground contact. Because the whole path is known, the shooter can check it against the anti-farm rule and
-- BonkService can validate reported hits against it. The server steers the physics part along that path
-- (it never collides with anything). See docs/GAME_DESIGN.md → Projectiles.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local IslandService = require(script.Parent.IslandService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Projectiles
local HITS = Gameplay.Hits
local ISLAND = Gameplay.Island

-- One piece of the path: a free flight starting at StartTime (seconds after launch).
export type Segment = {
	StartTime: number,
	StartPosition: Vector3,
	StartVelocity: Vector3,
}

export type ShotPlan = {
	Def: Projectiles.ProjectileDef,
	From: Vector3,
	SizeScale: number,
	Radius: number,
	-- Launch speed without jitter. Used for the reward's speed multiplier.
	NominalSpeed: number,
	-- Actual launch speed including jitter. Hit quality is measured against it.
	Speed: number,
	-- Downward acceleration of this projectile (studs/s²).
	Gravity: number,
	-- The flight, then one segment per bounce.
	Segments: { Segment },
	-- Seconds after launch when the path ends (last ground contact, or fallen below the island).
	EndTime: number,
}

export type ProjectileInfo = {
	Id: number,
	Part: BasePart,
	-- Parts to fade when the projectile has paid out (the model, or the sphere itself).
	VisualParts: { BasePart },
	Owner: Player,
	Plan: ShotPlan,
	LaunchedAt: number,
	-- Index of the next segment (bounce) the server still has to apply.
	NextSegment: number,
	EndedAt: number?,
	Paid: boolean,
}

local live: { [BasePart]: ProjectileInfo } = {}
local byId: { [number]: ProjectileInfo } = {}
local nextId = 1
local random = Random.new()

local ProjectileService = {}

-- Time until a body at height y0 with vertical speed vy falls to `height` under gravity g (the later root).
local function timeToHeight(y0: number, vy: number, g: number, height: number): number
	local discriminant = vy * vy + 2 * g * (y0 - height)
	return (vy + math.sqrt(math.max(discriminant, 0))) / g
end

local function isOverIsland(center: Vector3, position: Vector3): boolean
	return Vector3.new(position.X - center.X, 0, position.Z - center.Z).Magnitude <= ISLAND.Radius
end

local function destroy(info: ProjectileInfo)
	live[info.Part] = nil
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

-- The visible part of a projectile: the Assets model welded to the invisible hit sphere, or the sphere itself.
local function attachVisual(sphere: Part, def: Projectiles.ProjectileDef, diameter: number): { BasePart }
	local model = if def.AssetName then Assets.CloneModel(def.AssetName) else nil
	if not model then
		sphere.Color = def.Color
		sphere.Material = def.Material
		return { sphere }
	end
	sphere.Transparency = 1
	Assets.ScaleTo(model, diameter)
	Assets.MakeVisualOnly(model, false)
	-- Centre the model's bounding box on the sphere.
	local box = model:GetBoundingBox()
	model:PivotTo(sphere.CFrame * box:ToObjectSpace(model:GetPivot()))
	local parts: { BasePart } = {}
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = sphere
			weld.Part1 = descendant
			weld.Parent = descendant
			table.insert(parts, descendant)
		end
	end
	model.Parent = sphere
	return parts
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

-- Plans a shot for `owner` from `from` that first lands on `target` (a point at projectile-centre height).
-- Returns nil if the owner has no island.
function ProjectileService.Plan(owner: Player, from: Vector3, target: Vector3): ShotPlan?
	local island = IslandService.GetIsland(owner)
	if not island then
		return nil
	end
	local def = ProjectileService.GetDef()
	local sizeScale = UpgradeService.GetValue(owner, "ProjectileSize")
	local radius = def.Diameter * sizeScale / 2
	-- Bigger projectiles fly slower: that is the price of the easier, bigger-paying hit.
	local nominalSpeed = def.BaseSpeed * sizeScale ^ -0.5
	local speed = nominalSpeed * (1 + random:NextNumber(-CONFIG.SpeedJitter, CONFIG.SpeedJitter))

	-- Solve for the gravity that makes a launch at this speed and angle land on the target:
	-- horizontal: distance = vH·t  →  t = distance / vH;  vertical: dy = vY·t − ½·g·t²  →  g = 2(vY·t − dy) / t².
	local angle = math.rad(CONFIG.LaunchAngleDegrees)
	local distance = math.max(Vector3.new(target.X - from.X, 0, target.Z - from.Z).Magnitude, 1)
	local flightTime = distance / (speed * math.cos(angle))
	local gravity = 2 * (speed * math.sin(angle) * flightTime - (target.Y - from.Y)) / (flightTime * flightTime)

	local acceleration = Vector3.new(0, -gravity, 0)
	local groundHeight = ISLAND.SurfaceY + radius
	local segments: { Segment } = {}
	local startTime = 0
	local position = from
	local velocity = ProjectileService.GetLaunchDirection(from, target) * speed
	local endTime = 0

	for contact = 1, CONFIG.Bounces + 1 do
		table.insert(segments, { StartTime = startTime, StartPosition = position, StartVelocity = velocity })
		local time = timeToHeight(position.Y, velocity.Y, gravity, groundHeight)
		local contactPosition = position + velocity * time + acceleration * (0.5 * time * time)
		if not isOverIsland(island.Center, contactPosition) then
			-- Bounced off the edge: it keeps falling until it is well below the island.
			local fallHeight = ISLAND.SurfaceY - CONFIG.FallDespawnDepth
			endTime = startTime + timeToHeight(position.Y, velocity.Y, gravity, fallHeight)
			break
		end
		endTime = startTime + time
		if contact == CONFIG.Bounces + 1 then
			break
		end
		local contactVelocity = velocity + acceleration * time
		startTime = endTime
		position = contactPosition
		velocity = Vector3.new(
			contactVelocity.X * CONFIG.BounceFriction,
			-contactVelocity.Y * CONFIG.BounceRestitution,
			contactVelocity.Z * CONFIG.BounceFriction
		)
	end

	return {
		Def = def,
		From = from,
		SizeScale = sizeScale,
		Radius = radius,
		NominalSpeed = nominalSpeed,
		Speed = speed,
		Gravity = gravity,
		Segments = segments,
		EndTime = endTime,
	}
end

-- Position and velocity on the planned path `time` seconds after launch.
function ProjectileService.GetState(plan: ShotPlan, time: number): (Vector3, Vector3)
	local clamped = math.clamp(time, 0, plan.EndTime)
	local segment = plan.Segments[1]
	for _, candidate in plan.Segments do
		if candidate.StartTime <= clamped then
			segment = candidate
		end
	end
	local dt = clamped - segment.StartTime
	local acceleration = Vector3.new(0, -plan.Gravity, 0)
	local position = segment.StartPosition + segment.StartVelocity * dt + acceleration * (0.5 * dt * dt)
	return position, segment.StartVelocity + acceleration * dt
end

-- The point of the path (up to `untilTime`, default: the whole path) closest to `position`:
-- returns the distance and the projectile velocity there.
function ProjectileService.ClosestApproach(plan: ShotPlan, position: Vector3, untilTime: number?): (number, Vector3)
	local lastTime = math.min(untilTime or plan.EndTime, plan.EndTime)
	local bestDistance = math.huge
	local bestVelocity = plan.Segments[1].StartVelocity
	local time = 0
	while time <= lastTime do
		local point, velocity = ProjectileService.GetState(plan, time)
		local distance = (point - position).Magnitude
		if distance < bestDistance then
			bestDistance = distance
			bestVelocity = velocity
		end
		time += HITS.FlightSampleStep
	end
	return bestDistance, bestVelocity
end

-- Fires a planned shot for `owner`.
function ProjectileService.Fire(owner: Player, plan: ShotPlan)
	local island = IslandService.GetIsland(owner)
	if not island then
		return
	end
	makeRoom(owner)

	local id = nextId
	nextId += 1

	-- Invisible hit sphere that carries the model. It never collides: the server moves it along the plan.
	local sphere = Instance.new("Part")
	sphere.Name = plan.Def.Id
	sphere.Shape = Enum.PartType.Ball
	sphere.Size = Vector3.one * plan.Radius * 2
	sphere.TopSurface = Enum.SurfaceType.Smooth
	sphere.BottomSurface = Enum.SurfaceType.Smooth
	sphere.CanCollide = false
	sphere.CanTouch = false
	sphere.CanQuery = false
	sphere.CFrame = CFrame.new(plan.From)
	sphere:SetAttribute(CONFIG.IdAttribute, id)
	local visualParts = attachVisual(sphere, plan.Def, plan.Radius * 2)

	local attachment = Instance.new("Attachment")
	attachment.Parent = sphere
	local antiGravity = Instance.new("VectorForce")
	antiGravity.Attachment0 = attachment
	antiGravity.RelativeTo = Enum.ActuatorRelativeTo.World
	antiGravity.ApplyAtCenterOfMass = true
	antiGravity.Parent = sphere

	sphere.Parent = island.ProjectileFolder
	-- Server-owned so it moves exactly along the plan the server validates hits against.
	sphere:SetNetworkOwner(nil)
	antiGravity.Force = Vector3.new(0, sphere.AssemblyMass * (Workspace.Gravity - plan.Gravity), 0)
	sphere.AssemblyLinearVelocity = plan.Segments[1].StartVelocity
	sphere.AssemblyAngularVelocity = Vector3.new(
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin),
		random:NextNumber(-CONFIG.MaxSpin, CONFIG.MaxSpin)
	)

	local info: ProjectileInfo = {
		Id = id,
		Part = sphere,
		VisualParts = visualParts,
		Owner = owner,
		Plan = plan,
		LaunchedAt = os.clock(),
		NextSegment = 2,
		Paid = false,
	}
	live[sphere] = info
	byId[id] = info
end

function ProjectileService.GetById(id: number): ProjectileInfo?
	return byId[id]
end

-- After this the projectile can't pay out again.
function ProjectileService.MarkPaid(info: ProjectileInfo)
	info.Paid = true
	if live[info.Part] then
		for _, part in info.VisualParts do
			part.Transparency = math.max(part.Transparency, CONFIG.PaidTransparency)
		end
	end
end

-- Keeps the part on its planned path: applies each bounce exactly, and stops it where the path ends.
local function steer(info: ProjectileInfo, now: number)
	local part = info.Part
	local plan = info.Plan
	local elapsed = now - info.LaunchedAt
	local segment = plan.Segments[info.NextSegment]
	if segment and elapsed >= segment.StartTime then
		local position, velocity = ProjectileService.GetState(plan, elapsed)
		part.CFrame = CFrame.new(position) * part.CFrame.Rotation
		part.AssemblyLinearVelocity = velocity
		info.NextSegment += 1
	end
	if elapsed >= plan.EndTime then
		info.EndedAt = now
		part.Anchored = true
		part.CFrame = CFrame.new((ProjectileService.GetState(plan, plan.EndTime))) * part.CFrame.Rotation
	end
end

function ProjectileService.Start()
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
			local endedAt = info.EndedAt
			if not endedAt then
				steer(info, now)
			elseif now - endedAt >= CONFIG.DespawnDelay then
				destroy(info)
				continue
			end
			if now - info.LaunchedAt >= CONFIG.MaxLifetime or part.Parent == nil then
				destroy(info)
			end
		end
		for id, info in byId do
			local endedAt = info.EndedAt or info.LaunchedAt
			if not live[info.Part] and now - endedAt >= CONFIG.ReportGracePeriod then
				byId[id] = nil
			end
		end
	end)
end

return ProjectileService
