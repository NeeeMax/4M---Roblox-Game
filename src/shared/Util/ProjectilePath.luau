--!strict
-- A projectile's whole planned path (flight + bounces + settling hops + landing fade) and how it travels between
-- server and client. The server plans the path (ProjectileService → Build) and stores it as attributes on an
-- invisible, anchored marker part; every client reads them and draws the projectile along the same path each frame,
-- so it moves smoothly (no network corrections at the bounces). This module is the single source of truth for the
-- bounce physics and the timeline. Pure functions only: no side effects on require.
--
-- Timeline (seconds after launch):
--   0 .. SettleTime            flight and the `Bounces` restitution bounces
--   SettleTime .. EndTime      the small settling hops (`SettleHopHeights`); the model turns to lie flat
--   EndTime .. EndTime+FadeTime the projectile lies still on the ground and fades out (FadeTime = 0 after a fall)
-- It can be collected until GetCollectEndTime (EndTime, plus FadeTime if `CollectableWhileFading`).

local Gameplay = require(script.Parent.Parent.Config.Gameplay)

local CONFIG = Gameplay.Projectiles
local ISLAND = Gameplay.Island

-- One piece of the path: a free flight starting at StartTime (seconds after launch).
export type Segment = {
	StartTime: number,
	StartPosition: Vector3,
	StartVelocity: Vector3,
}

export type Path = {
	-- Downward acceleration of this projectile (studs/s²).
	Gravity: number,
	-- The flight, then one segment per bounce / settling hop.
	Segments: { Segment },
	-- Seconds after launch when the settling hops start (= EndTime if there are none, e.g. after a fall).
	SettleTime: number,
	-- Seconds after launch when the motion ends (last ground contact, or fallen below the island).
	EndTime: number,
	-- Seconds the projectile lies on the ground fading out after EndTime (0 if it fell off the island).
	FadeTime: number,
}

local ATTRIBUTE = {
	LaunchTime = "LaunchTime",
	Gravity = "Gravity",
	SettleTime = "SettleTime",
	EndTime = "EndTime",
	FadeTime = "FadeTime",
	SegmentCount = "SegmentCount",
	Diameter = "Diameter",
	Paid = "Paid",
}

local ProjectilePath = {
	Attribute = ATTRIBUTE,
}

-- Time until a body at height y0 with vertical speed vy falls to `height` under gravity g (the later root).
local function timeToHeight(y0: number, vy: number, g: number, height: number): number
	local discriminant = vy * vy + 2 * g * (y0 - height)
	return (vy + math.sqrt(math.max(discriminant, 0))) / g
end

local function isOverIsland(center: Vector3, position: Vector3): boolean
	return Vector3.new(position.X - center.X, 0, position.Z - center.Z).Magnitude <= ISLAND.Radius
end

-- Plans the whole path of a projectile with this `radius` launched from `from` with `velocity` under `gravity`
-- over the island centred at `islandCenter`: the flight, `Bounces` bounces (restitution / friction), then the
-- small settling hops, or the fall off the island edge if a bounce leaves it.
function ProjectilePath.Build(
	islandCenter: Vector3,
	radius: number,
	from: Vector3,
	velocity: Vector3,
	gravity: number
): Path
	local acceleration = Vector3.new(0, -gravity, 0)
	local groundHeight = ISLAND.SurfaceY + radius
	local hops = CONFIG.Bounces + #CONFIG.SettleHopHeights
	local segments: { Segment } = {}
	local startTime = 0
	local position = from
	local settleTime: number? = nil
	-- Apex height (above the ground) of the previous hop: a settling hop is never higher than the one before it.
	local lastApex = math.huge

	for contact = 1, hops + 1 do
		table.insert(segments, { StartTime = startTime, StartPosition = position, StartVelocity = velocity })
		local time = timeToHeight(position.Y, velocity.Y, gravity, groundHeight)
		local contactPosition = position + velocity * time + acceleration * (0.5 * time * time)
		if not isOverIsland(islandCenter, contactPosition) then
			-- Bounced off the edge: it keeps falling until it is well below the island, then vanishes (no fade).
			local fallHeight = ISLAND.SurfaceY - CONFIG.FallDespawnDepth
			local endTime = startTime + timeToHeight(position.Y, velocity.Y, gravity, fallHeight)
			return {
				Gravity = gravity,
				Segments = segments,
				SettleTime = settleTime or endTime,
				EndTime = endTime,
				FadeTime = 0,
			}
		end
		local endTime = startTime + time
		if contact > hops then
			return {
				Gravity = gravity,
				Segments = segments,
				SettleTime = settleTime or endTime,
				EndTime = endTime,
				FadeTime = CONFIG.LandingFadeTime,
			}
		end
		local contactVelocity = velocity + acceleration * time
		local upSpeed: number
		local keep: number
		if contact <= CONFIG.Bounces then
			upSpeed = -contactVelocity.Y * CONFIG.BounceRestitution
			keep = CONFIG.BounceFriction
		else
			-- Settling hop: a fixed small height, so it is visible whatever this projectile's gravity is.
			settleTime = settleTime or endTime
			local apex = math.min(CONFIG.SettleHopHeights[contact - CONFIG.Bounces], lastApex)
			upSpeed = math.sqrt(2 * gravity * apex)
			keep = CONFIG.SettleFriction
		end
		lastApex = upSpeed * upSpeed / (2 * gravity)
		startTime = endTime
		position = contactPosition
		velocity = Vector3.new(contactVelocity.X * keep, upSpeed, contactVelocity.Z * keep)
	end
	-- Not reached: the loop always returns on its last contact.
	error("ProjectilePath.Build: path did not end")
end

-- Position and velocity on the path `time` seconds after launch (clamped to the path's start and EndTime, so during
-- the landing fade it returns the resting position).
function ProjectilePath.GetState(path: Path, time: number): (Vector3, Vector3)
	local clamped = math.clamp(time, 0, path.EndTime)
	local segment = path.Segments[1]
	for _, candidate in path.Segments do
		if candidate.StartTime <= clamped then
			segment = candidate
		end
	end
	local dt = clamped - segment.StartTime
	local acceleration = Vector3.new(0, -path.Gravity, 0)
	local position = segment.StartPosition + segment.StartVelocity * dt + acceleration * (0.5 * dt * dt)
	return position, segment.StartVelocity + acceleration * dt
end

-- Seconds after launch until which the projectile can be collected (client check and server validation).
function ProjectilePath.GetCollectEndTime(path: Path): number
	return path.EndTime + (if CONFIG.CollectableWhileFading then path.FadeTime else 0)
end

-- Seconds after launch when the projectile is fully faded out (clients stop drawing it).
function ProjectilePath.GetVisibleEndTime(path: Path): number
	return path.EndTime + path.FadeTime
end

-- Server: stores the path, its launch time (Workspace:GetServerTimeNow()) and the hit diameter on the marker.
function ProjectilePath.Write(marker: Instance, path: Path, launchTime: number, diameter: number)
	marker:SetAttribute(ATTRIBUTE.LaunchTime, launchTime)
	marker:SetAttribute(ATTRIBUTE.Gravity, path.Gravity)
	marker:SetAttribute(ATTRIBUTE.SettleTime, path.SettleTime)
	marker:SetAttribute(ATTRIBUTE.EndTime, path.EndTime)
	marker:SetAttribute(ATTRIBUTE.FadeTime, path.FadeTime)
	marker:SetAttribute(ATTRIBUTE.Diameter, diameter)
	marker:SetAttribute(ATTRIBUTE.SegmentCount, #path.Segments)
	for index, segment in path.Segments do
		marker:SetAttribute(`S{index}Time`, segment.StartTime)
		marker:SetAttribute(`S{index}Position`, segment.StartPosition)
		marker:SetAttribute(`S{index}Velocity`, segment.StartVelocity)
	end
end

-- Client: reads what Write stored. Returns nil if anything is missing or malformed.
function ProjectilePath.Read(marker: Instance): (Path?, number, number)
	local launchTime = marker:GetAttribute(ATTRIBUTE.LaunchTime)
	local gravity = marker:GetAttribute(ATTRIBUTE.Gravity)
	local settleTime = marker:GetAttribute(ATTRIBUTE.SettleTime)
	local endTime = marker:GetAttribute(ATTRIBUTE.EndTime)
	local fadeTime = marker:GetAttribute(ATTRIBUTE.FadeTime)
	local diameter = marker:GetAttribute(ATTRIBUTE.Diameter)
	local count = marker:GetAttribute(ATTRIBUTE.SegmentCount)
	if
		typeof(launchTime) ~= "number"
		or typeof(gravity) ~= "number"
		or typeof(settleTime) ~= "number"
		or typeof(endTime) ~= "number"
		or typeof(fadeTime) ~= "number"
		or typeof(diameter) ~= "number"
		or typeof(count) ~= "number"
	then
		return nil, 0, 0
	end
	local segments: { Segment } = {}
	for index = 1, count do
		local startTime = marker:GetAttribute(`S{index}Time`)
		local position = marker:GetAttribute(`S{index}Position`)
		local velocity = marker:GetAttribute(`S{index}Velocity`)
		if typeof(startTime) ~= "number" or typeof(position) ~= "Vector3" or typeof(velocity) ~= "Vector3" then
			return nil, 0, 0
		end
		table.insert(segments, { StartTime = startTime, StartPosition = position, StartVelocity = velocity })
	end
	if #segments == 0 then
		return nil, 0, 0
	end
	return {
		Gravity = gravity,
		Segments = segments,
		SettleTime = settleTime,
		EndTime = endTime,
		FadeTime = fadeTime,
	},
		launchTime,
		diameter
end

return ProjectilePath
