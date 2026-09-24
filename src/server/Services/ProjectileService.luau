--!strict
-- Plans, spawns and removes projectiles. Every shot is planned in full before it is fired: a 45° arc with its own
-- gravity so it lands exactly on the target, then `Bounces` bounces and a few small settling hops on the island, then
-- it lies still and fades out (ProjectilePath.Build plans it all). Because the whole path is known, the shooter can
-- check it against the anti-farm rule and BonkService can validate reported hits against it. The server only creates
-- an invisible, anchored marker that carries the path (Util/ProjectilePath); every client draws the projectile along
-- it (ProjectileController), so the flight is smooth. See docs/GAME_DESIGN.md → Projectiles and docs/decisions/0004.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Events = require(ReplicatedStorage.Shared.Config.Events)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local EventService = require(script.Parent.EventService)
local IslandService = require(script.Parent.IslandService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Projectiles
local HITS = Gameplay.Hits

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
	-- Golden projectiles glow and pay Gameplay.Projectiles.GoldenMultiplier times as much.
	Golden: boolean,
	-- MegaStick server event: the giant stick (Events.MegaStick.DiameterScale × diameter, pays RewardMultiplier ×).
	Mega: boolean,
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

-- Rolls whether the next projectile of `owner` is golden (Lucky Sticks pass: more often).
local function rollGolden(owner: Player): boolean
	if EventService.IsActive("GoldenMinute") then
		return true
	end
	local chance = if RewardService.HasPass(owner, "LuckySticks")
		then Shop.Pass.LuckyGoldenChance
		else CONFIG.GoldenChance
	return random:NextNumber() < chance
end

-- Plans a shot for `owner` from `from` that first lands on `target` (a point at projectile-centre height).
-- Returns nil if the owner has no island.
function ProjectileService.Plan(owner: Player, from: Vector3, target: Vector3): ShotPlan?
	local island = IslandService.GetIsland(owner)
	if not island then
		return nil
	end
	local def = ProjectileService.GetDef(owner)
	-- MegaStick event: the player's next shot is the giant stick (taken for good when it is fired).
	local mega = EventService.HasMegaPending(owner)
	local radius = def.Diameter / 2 * (if mega then Events.MegaStick.DiameterScale else 1)
	local nominalSpeed = def.BaseSpeed
	local speed = nominalSpeed * (1 + random:NextNumber(-CONFIG.SpeedJitter, CONFIG.SpeedJitter))

	-- Solve for the gravity that makes a launch at this speed and angle land on the target:
	-- horizontal: distance = vH·t  →  t = distance / vH;  vertical: dy = vY·t − ½·g·t²  →  g = 2(vY·t − dy) / t².
	local angle = math.rad(CONFIG.LaunchAngleDegrees)
	local distance = math.max(Vector3.new(target.X - from.X, 0, target.Z - from.Z).Magnitude, 1)
	local flightTime = distance / (speed * math.cos(angle))
	local gravity = 2 * (speed * math.sin(angle) * flightTime - (target.Y - from.Y)) / (flightTime * flightTime)
	local velocity = ProjectileService.GetLaunchDirection(from, target) * speed

	return {
		Def = def,
		From = from,
		Radius = radius,
		NominalSpeed = nominalSpeed,
		Speed = speed,
		Path = ProjectilePath.Build(island.Center, radius, from, velocity, gravity),
		Golden = rollGolden(owner),
		Mega = mega,
	}
end

-- Bonk Rain: a projectile dropping from `height` above `target` (slightly sideways), then bouncing as usual.
function ProjectileService.PlanDrop(owner: Player, target: Vector3, height: number): ShotPlan?
	local island = IslandService.GetIsland(owner)
	if not island then
		return nil
	end
	local def = ProjectileService.GetDef(owner)
	local radius = def.Diameter / 2
	local gravity = 60
	local fallTime = math.sqrt(2 * height / gravity)
	local drift = Vector3.new(random:NextNumber(-1, 1), 0, random:NextNumber(-1, 1)) * 6
	local from = target + Vector3.new(0, height, 0) - drift
	local velocity = drift / fallTime
	return {
		Def = def,
		From = from,
		Radius = radius,
		NominalSpeed = def.BaseSpeed,
		-- Hit quality compares against launch speed; a drop lands at about this speed.
		Speed = gravity * fallTime,
		Path = ProjectilePath.Build(island.Center, radius, from, velocity, gravity),
		Golden = rollGolden(owner),
		Mega = false,
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
	local function sample(time: number)
		local point, velocity = ProjectileService.GetState(plan, time)
		local distance = (point - position).Magnitude
		if distance < bestDistance then
			bestDistance = distance
			bestVelocity = velocity
		end
	end
	local time = 0
	while time < lastTime do
		sample(time)
		time += HITS.FlightSampleStep
	end
	-- The last point exactly (e.g. where it comes to rest).
	sample(math.max(lastTime, 0))
	return bestDistance, bestVelocity
end

-- Whether a hit report for this projectile may still be validated now: until the end of its collectable window
-- (ProjectilePath.GetCollectEndTime) plus ReportGracePeriod for network delay.
function ProjectileService.AcceptsReports(info: ProjectileInfo): boolean
	local age = os.clock() - info.LaunchedAt
	return age <= ProjectilePath.GetCollectEndTime(info.Plan.Path) + CONFIG.ReportGracePeriod
end

-- Fires a planned shot for `owner`.
function ProjectileService.Fire(owner: Player, plan: ShotPlan)
	local island = IslandService.GetIsland(owner)
	if not island then
		return
	end
	-- Only one giant stick per player and event: a second mega plan (two Shibas aimed at once) is dropped.
	if plan.Mega and not EventService.TakeMega(owner) then
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
	marker:SetAttribute(CONFIG.GoldenAttribute, plan.Golden)
	if plan.Mega then
		marker:SetAttribute(Events.MegaStick.Attribute, true)
		NotifyService.Send(owner, `MEGA STICK incoming! Catch it for x{Events.MegaStick.RewardMultiplier}!`, "Good")
	end
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
			-- The marker stays until every client has finished the landing fade (it drives their model).
			if
				age >= ProjectilePath.GetVisibleEndTime(info.Plan.Path) + CONFIG.DespawnDelay
				or age >= CONFIG.MaxLifetime
				or part.Parent == nil
			then
				destroy(info)
			end
		end
		for id, info in byId do
			if not live[info.Part] and not ProjectileService.AcceptsReports(info) then
				byId[id] = nil
			end
		end
	end)
end

return ProjectileService
