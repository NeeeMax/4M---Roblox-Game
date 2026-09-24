--!strict
-- Plans, spawns and removes projectiles. Every shot is planned in full before it is fired: a 45° arc with its own
-- gravity so it lands exactly on the target, then `Bounces` bounces on the island, then it disappears on the next
-- ground contact. Because the whole path is known, the shooter can check it against the anti-farm rule and
-- BonkService can validate reported hits against it. The server only creates an invisible, anchored marker that
-- carries the path (Util/ProjectilePath); every client draws the projectile along it (ProjectileController), so the
-- flight is smooth. See docs/GAME_DESIGN.md → Projectiles and docs/decisions/0004.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local IslandService = require(script.Parent.IslandService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Projectiles
local HITS = Gameplay.Hits
local ISLAND = Gameplay.Island

export type ShotPlan = {
	Def: Projectiles.ProjectileDef,
	From: Vector3,
	Radius: number,
	-- Launch speed without jitter.
	NominalSpeed: number,
	-- Actual launch speed including jitter. Hit quality is measured against it.
	Speed: number,
	-- Flight and bounces, as the clients draw it.
	Path: ProjectilePath.Path,
}

export type ProjectileInfo = {
	Id: number,
	-- Invisible, anchored marker carrying the path for the clients.
	Part: BasePart,
	Owner: Player,
	Plan: ShotPlan,
	-- os.clock() at launch.
	LaunchedAt: number,
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

-- The projectile this player's shooters fire (their ProjectileTier level).
function ProjectileService.GetDef(player: Player): Projectiles.ProjectileDef
	return Projectiles.ForTier(UpgradeService.GetLevel(player, "ProjectileTier"))
end

-- Projectile diameter (the same at every level).
function ProjectileService.GetDiameter(player: Player): number
	return ProjectileService.GetDef(player).Diameter
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
	local def = ProjectileService.GetDef(owner)
	local radius = def.Diameter / 2
	local nominalSpeed = def.BaseSpeed
	local speed = nominalSpeed * (1 + random:NextNumber(-CONFIG.SpeedJitter, CONFIG.SpeedJitter))

	-- Solve for the gravity that makes a launch at this speed and angle land on the target:
	-- horizontal: distance = vH·t  →  t = distance / vH;  vertical: dy = vY·t − ½·g·t²  →  g = 2(vY·t − dy) / t².
	local angle = math.rad(CONFIG.LaunchAngleDegrees)
	local distance = math.max(Vector3.new(target.X - from.X, 0, target.Z - from.Z).Magnitude, 1)
	local flightTime = distance / (speed * math.cos(angle))
	local gravity = 2 * (speed * math.sin(angle) * flightTime - (target.Y - from.Y)) / (flightTime * flightTime)

	local acceleration = Vector3.new(0, -gravity, 0)
	local groundHeight = ISLAND.SurfaceY + radius
	local segments: { ProjectilePath.Segment } = {}
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
		Radius = radius,
		NominalSpeed = nominalSpeed,
		Speed = speed,
		Path = { Gravity = gravity, Segments = segments, EndTime = endTime },
	}
end

-- Position and velocity on the planned path `time` seconds after launch.
function ProjectileService.GetState(plan: ShotPlan, time: number): (Vector3, Vector3)
	return ProjectilePath.GetState(plan.Path, time)
end

-- The point of the path (up to `untilTime`, default: the whole path) closest to `position`:
-- returns the distance and the projectile velocity there.
function ProjectileService.ClosestApproach(plan: ShotPlan, position: Vector3, untilTime: number?): (number, Vector3)
	local path = plan.Path
	local lastTime = math.min(untilTime or path.EndTime, path.EndTime)
	local bestDistance = math.huge
	local bestVelocity = path.Segments[1].StartVelocity
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

	-- Invisible marker: it never moves or collides. Clients draw the projectile along the path it carries.
	local marker = Instance.new("Part")
	marker.Name = plan.Def.Id
	marker.Size = Vector3.one
	marker.Transparency = 1
	marker.Anchored = true
	marker.CanCollide = false
	marker.CanTouch = false
	marker.CanQuery = false
	marker.CFrame = CFrame.new(plan.From)
	marker:SetAttribute(CONFIG.IdAttribute, id)
	ProjectilePath.Write(marker, plan.Path, Workspace:GetServerTimeNow(), plan.Radius * 2)
	marker.Parent = island.ProjectileFolder

	local info: ProjectileInfo = {
		Id = id,
		Part = marker,
		Owner = owner,
		Plan = plan,
		LaunchedAt = os.clock(),
		Paid = false,
	}
	live[marker] = info
	byId[id] = info
end

function ProjectileService.GetById(id: number): ProjectileInfo?
	return byId[id]
end

-- After this the projectile can't pay out again.
function ProjectileService.MarkPaid(info: ProjectileInfo)
	info.Paid = true
	if live[info.Part] then
		-- Clients fade the projectile when they see this.
		info.Part:SetAttribute(ProjectilePath.Attribute.Paid, true)
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
			local age = now - info.LaunchedAt
			if
				age >= info.Plan.Path.EndTime + CONFIG.DespawnDelay
				or age >= CONFIG.MaxLifetime
				or part.Parent == nil
			then
				destroy(info)
			end
		end
		for id, info in byId do
			local endedAt = info.LaunchedAt + info.Plan.Path.EndTime
			if not live[info.Part] and now - endedAt >= CONFIG.ReportGracePeriod then
				byId[id] = nil
			end
		end
	end)
end

return ProjectileService
