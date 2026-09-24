--!strict
-- A projectile's whole planned path (flight + bounces) and how it travels between server and client.
-- The server plans the path (ProjectileService) and stores it as attributes on an invisible, anchored marker part;
-- every client reads them and draws the projectile along the same path each frame, so it moves smoothly
-- (no network corrections at the bounces). Pure functions only: no side effects on require.

-- One piece of the path: a free flight starting at StartTime (seconds after launch).
export type Segment = {
	StartTime: number,
	StartPosition: Vector3,
	StartVelocity: Vector3,
}

export type Path = {
	-- Downward acceleration of this projectile (studs/s²).
	Gravity: number,
	-- The flight, then one segment per bounce.
	Segments: { Segment },
	-- Seconds after launch when the path ends (last ground contact, or fallen below the island).
	EndTime: number,
}

local ATTRIBUTE = {
	LaunchTime = "LaunchTime",
	Gravity = "Gravity",
	EndTime = "EndTime",
	SegmentCount = "SegmentCount",
	Diameter = "Diameter",
	Paid = "Paid",
}

local ProjectilePath = {
	Attribute = ATTRIBUTE,
}

-- Position and velocity on the path `time` seconds after launch (clamped to the path's start and end).
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

-- Server: stores the path, its launch time (Workspace:GetServerTimeNow()) and the hit diameter on the marker.
function ProjectilePath.Write(marker: Instance, path: Path, launchTime: number, diameter: number)
	marker:SetAttribute(ATTRIBUTE.LaunchTime, launchTime)
	marker:SetAttribute(ATTRIBUTE.Gravity, path.Gravity)
	marker:SetAttribute(ATTRIBUTE.EndTime, path.EndTime)
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
	local endTime = marker:GetAttribute(ATTRIBUTE.EndTime)
	local diameter = marker:GetAttribute(ATTRIBUTE.Diameter)
	local count = marker:GetAttribute(ATTRIBUTE.SegmentCount)
	if
		typeof(launchTime) ~= "number"
		or typeof(gravity) ~= "number"
		or typeof(endTime) ~= "number"
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
	return { Gravity = gravity, Segments = segments, EndTime = endTime }, launchTime, diameter
end

return ProjectilePath
