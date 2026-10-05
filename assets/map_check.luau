--!strict
-- Map checker: run in the Server DataModel during a playtest (Claude: execute_luau with this file's content).
-- Scans a square of REGION_RADIUS around the first player's character on a CELL grid (every floor level per column),
-- builds a walk/jump/drop graph with the character's real WalkSpeed and JumpPower and reports:
--   1 floating platforms        2 no-footing tops           3 unreachable high ground   4 places players shouldn't reach
--   5 no-way-out pockets        6 sight lines too open/closed 7 parts inside parts      8 uneven rings
--   9 short falls vs ragdoll-height falls
-- Move the character (or change REGION_RADIUS) to check another area; the street is ~10 000 studs long.

local REGION_RADIUS = 150 -- studs around the character
local CELL = 3 -- studs between scan columns
local MAX_LEVELS = 6 -- floors per column (ground, platform, roof, ...)
local HEADROOM = 5 -- studs a character needs above a floor
local MIN_FOOTING = 2 -- studs: tops narrower than this can't be stood on reliably
local MIN_PLATFORM_CELLS = 4 -- unreachable groups smaller than this are decor tops, not "high ground"
local RAGDOLL_FALL = 25 -- studs: falls this high should ragdoll / play a landing; shorter drops are one-way steps
local SIGHT_CLOSED = 12 -- studs: median view distance below this feels cramped
local SIGHT_OPEN = 250 -- studs: nothing within this in all 8 directions feels empty
local SIGHT_EVERY = 7 -- every Nth reachable floor cell gets sight rays
local RING_MIN = 5 -- parts in a group before it can count as a ring
local RING_TOLERANCE = 0.25 -- studs of radius / height difference allowed in a ring
local RING_ANGLE_TOLERANCE = 2 -- degrees of spacing difference allowed in a ring
local OFF_LIMITS = { "roof", "wall", "fence", "rail", "barrier", "tree", "leaf", "leaves", "lamp", "sign", "pole" }
local WALKABLE = { "floor", "ground", "road", "sidewalk", "path", "platform", "step", "stair", "bridge" }
local TOP = 8 -- lines per section

local Players = game:GetService("Players")
local Gameplay = require(game:GetService("ReplicatedStorage").Shared.Config.Gameplay) :: any

local player = Players:GetPlayers()[1]
assert(player and player.Character, "map_check needs a playtest with a spawned character")
local character = player.Character :: Model
local humanoid = character:FindFirstChildOfClass("Humanoid") :: Humanoid
local root = character:FindFirstChild("HumanoidRootPart") :: BasePart
local centre = root.Position

local g = workspace.Gravity
local jumpPower = if humanoid.JumpPower > 0 then humanoid.JumpPower else Gameplay.Character.JumpPower
local speed = math.max(humanoid.WalkSpeed, 16)
-- ponytail: +1 stud for tucked legs; sprint (Street) reaches farther than WalkSpeed, run it while sprinting if needed.
local JUMP_UP = jumpPower * jumpPower / (2 * g) + 1

-- Characters and NPCs (anything with a Humanoid) are not floors.
local ignore = {}
for _, h in workspace:GetDescendants() do
	if h:IsA("Humanoid") and h.Parent then
		table.insert(ignore, h.Parent)
	end
end
local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Exclude
rayParams.FilterDescendantsInstances = ignore
rayParams.RespectCanCollide = true
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Exclude
overlapParams.FilterDescendantsInstances = ignore

local function fmt(v: Vector3): string
	return ("(%d, %d, %d)"):format(math.round(v.X), math.round(v.Y), math.round(v.Z))
end

local function short(inst: Instance): string
	return (inst:GetFullName():gsub("^Workspace%.", ""))
end

-- 1. Scan floors -------------------------------------------------------------------------------------------------
type Node = { pos: Vector3, part: BasePart, ix: number, iz: number }
local nodes: { Node } = {}
local byColumn: { [string]: { number } } = {}
local n = math.floor(REGION_RADIUS / CELL)
local floorY = centre.Y - 400

for ix = -n, n do
	for iz = -n, n do
		local x, z = centre.X + ix * CELL, centre.Z + iz * CELL
		local origin = Vector3.new(x, centre.Y + 300, z)
		for _ = 1, MAX_LEVELS do
			local hit = workspace:Raycast(origin, Vector3.new(0, floorY - origin.Y, 0), rayParams)
			if not hit then
				break
			end
			local part = hit.Instance
			if part:IsA("BasePart") and hit.Normal.Y > 0.7 then
				local blocked =
					workspace:Raycast(hit.Position + Vector3.new(0, 0.1, 0), Vector3.new(0, HEADROOM, 0), rayParams)
				if not blocked then
					table.insert(nodes, { pos = hit.Position, part = part, ix = ix, iz = iz })
					local key = ix .. "," .. iz
					byColumn[key] = byColumn[key] or {}
					table.insert(byColumn[key], #nodes)
				end
			end
			-- A ray that starts inside a part does not hit it, so the next ray finds the floor below.
			origin = hit.Position - Vector3.new(0, 0.05, 0)
		end
	end
	task.wait() -- keep the server responsive during the scan
end

-- 2. Graph: walk / jump / drop edges -----------------------------------------------------------------------------
local out: { { number } } = {}
local inn: { { number } } = {}
for i = 1, #nodes do
	out[i], inn[i] = {}, {}
end

-- Time until the feet are back at height dy above take-off, nil if the jump never gets that high.
local function airTime(dy: number): number?
	local disc = jumpPower * jumpPower - 2 * g * (dy - 1)
	if disc < 0 then
		return nil
	end
	return (jumpPower + math.sqrt(disc)) / g
end

local function clear(a: Vector3, b: Vector3, lift: number): boolean
	local from = Vector3.new(a.X, math.max(a.Y, b.Y) + lift, a.Z)
	local to = Vector3.new(b.X, math.max(a.Y, b.Y) + lift, b.Z)
	return workspace:Raycast(from, to - from, rayParams) == nil
end

local function link(i: number, j: number)
	table.insert(out[i], j)
	table.insert(inn[j], i)
end

local maxReach = speed * (airTime(-RAGDOLL_FALL) or 0)
local jumpCells = math.ceil(maxReach / CELL)

for i, a in nodes do
	local isEdge = false
	for dx = -1, 1 do
		for dz = -1, 1 do
			if dx == 0 and dz == 0 then
				continue
			end
			local col = byColumn[(a.ix + dx) .. "," .. (a.iz + dz)]
			local level = false
			for _, j in col or {} do
				local dy = nodes[j].pos.Y - a.pos.Y
				if math.abs(dy) <= 1 then
					level = true
				end
				if dy <= JUMP_UP and clear(a.pos, nodes[j].pos, 2.5) then
					link(i, j)
				end
			end
			if not level then
				isEdge = true
			end
		end
	end
	-- Only floor cells at a ledge can jump across gaps; that keeps the search small.
	if isEdge then
		for dx = -jumpCells, jumpCells do
			for dz = -jumpCells, jumpCells do
				if math.abs(dx) <= 1 and math.abs(dz) <= 1 then
					continue
				end
				for _, j in byColumn[(a.ix + dx) .. "," .. (a.iz + dz)] or {} do
					local b = nodes[j]
					local t = airTime(b.pos.Y - a.pos.Y)
					local dist = math.sqrt((dx * CELL) ^ 2 + (dz * CELL) ^ 2)
					if t and dist <= speed * t and clear(a.pos, b.pos, 3) then
						link(i, j)
					end
				end
			end
		end
	end
	if i % 500 == 0 then
		task.wait()
	end
end

-- 3. Reachability from the character and back to it --------------------------------------------------------------
local feet = root.Position - Vector3.new(0, humanoid.HipHeight + root.Size.Y / 2, 0)
local start, best = nil :: number?, math.huge
for i, a in nodes do
	local d = (a.pos - feet).Magnitude
	if d < best then
		start, best = i, d
	end
end
assert(start, "no floor found under the character")

local function flood(edges: { { number } }): { [number]: boolean }
	local seen = { [start :: number] = true }
	local queue = { start :: number }
	local head = 1
	while queue[head] do
		for _, j in edges[queue[head]] do
			if not seen[j] then
				seen[j] = true
				table.insert(queue, j)
			end
		end
		head += 1
	end
	return seen
end
local reach = flood(out)
local back = flood(inn)

-- Helpers for grouped reports ------------------------------------------------------------------------------------
local report: { string } = {}
local function section(title: string, lines: { string }, total: number?)
	table.insert(report, ("\n## %s: %d"):format(title, total or #lines))
	for k = 1, math.min(#lines, TOP) do
		table.insert(report, "  " .. lines[k])
	end
end

local function groupByPart(filter: (number, Node) -> boolean): { { part: BasePart, cells: number, at: Vector3 } }
	local groups: { [BasePart]: { part: BasePart, cells: number, at: Vector3 } } = {}
	for i, a in nodes do
		if filter(i, a) then
			local grp = groups[a.part] or { part = a.part, cells = 0, at = a.pos }
			grp.cells += 1
			groups[a.part] = grp
		end
	end
	local list = {}
	for _, grp in groups do
		table.insert(list, grp)
	end
	table.sort(list, function(x, y)
		return x.cells > y.cells
	end)
	return list
end

local function partLines(list: { { part: BasePart, cells: number, at: Vector3 } }, minCells: number): { string }
	local lines = {}
	for _, grp in list do
		if grp.cells >= minCells then
			table.insert(lines, ("%s  %d cells at %s"):format(short(grp.part), grp.cells, fmt(grp.at)))
		end
	end
	return lines
end

local function offLimits(part: BasePart): boolean
	if part:GetAttribute("OffLimits") or part:HasTag("OffLimits") then
		return true
	end
	-- Whole words only ("Sidewalk" is not a wall); a part named like a floor is always fine, even inside "OuterWall".
	local function words(name: string): { [string]: boolean }
		local set = {}
		for w in name:gsub("(%l)(%u)", "%1 %2"):lower():gmatch("%a+") do
			set[w] = true
			set[(w:gsub("s$", ""))] = true
		end
		return set
	end
	local own = words(part.Name)
	for _, w in WALKABLE do
		if own[w] then
			return false
		end
	end
	local node: Instance? = part
	while node and node ~= workspace do
		local set = words(node.Name)
		for _, w in OFF_LIMITS do
			if set[w] then
				return true
			end
		end
		node = node.Parent
	end
	return false
end

-- 1 floating platforms: walkable parts that touch nothing and have nothing right below them
do
	local lines = {}
	local checked: { [BasePart]: boolean } = {}
	for _, a in nodes do
		local part = a.part
		if checked[part] or part.Name == "Baseplate" then
			continue
		end
		checked[part] = true
		local touching =
			workspace:GetPartBoundsInBox(part.CFrame, part.Size + Vector3.new(0.2, 0.2, 0.2), overlapParams)
		local others = 0
		for _, t in touching do
			if t ~= part then
				others += 1
			end
		end
		local bottom = part.Position - Vector3.new(0, part.Size.Y / 2, 0)
		if others == 0 and not workspace:Raycast(bottom, Vector3.new(0, -1, 0), rayParams) then
			table.insert(lines, ("%s at %s"):format(short(part), fmt(part.Position)))
		end
	end
	section("1 Floating platforms (touch nothing)", lines)
end

-- 2 no-footing tops: reachable tops narrower than MIN_FOOTING
section(
	"2 No-footing tops (reachable, narrower than " .. MIN_FOOTING .. " studs)",
	partLines(
		groupByPart(function(i, a)
			if not reach[i] then
				return false
			end
			local cf, s = a.part.CFrame, a.part.Size
			-- The two axes that are not pointing up span the top face.
			local ups = { math.abs(cf.RightVector.Y), math.abs(cf.UpVector.Y), math.abs(cf.LookVector.Y) }
			local sizes = { s.X, s.Y, s.Z }
			local upAxis = 1
			for k = 2, 3 do
				if ups[k] > ups[upAxis] then
					upAxis = k
				end
			end
			local width = math.huge
			for k = 1, 3 do
				if k ~= upAxis then
					width = math.min(width, sizes[k])
				end
			end
			return width < MIN_FOOTING
		end),
		1
	)
)

-- 3 unreachable high ground
section(
	"3 Unreachable high ground (" .. MIN_PLATFORM_CELLS .. "+ cells)",
	partLines(
		groupByPart(function(i, a)
			return not reach[i] and a.pos.Y > feet.Y + JUMP_UP and not offLimits(a.part)
		end),
		MIN_PLATFORM_CELLS
	)
)

-- 4 places players shouldn't reach (roofs, walls, fences, trees, ... or tagged/attributed OffLimits)
section(
	"4 Reachable but shouldn't be",
	partLines(
		groupByPart(function(i, a)
			return reach[i] == true and offLimits(a.part)
		end),
		1
	)
)

-- 5 no-way-out pockets: reachable, but no path back to the character's spot
section(
	"5 No-way-out pockets",
	partLines(
		groupByPart(function(i, _)
			return reach[i] == true and not back[i]
		end),
		1
	)
)

-- 6 sight lines
do
	local closed, open, sampled = {}, {}, 0
	local k = 0
	for i, a in nodes do
		if not reach[i] then
			continue
		end
		k += 1
		if k % SIGHT_EVERY ~= 0 then
			continue
		end
		sampled += 1
		local eye = a.pos + Vector3.new(0, 4.5, 0)
		local dists = {}
		for d = 0, 7 do
			local ang = d * math.pi / 4
			local dir = Vector3.new(math.cos(ang), 0, math.sin(ang)) * SIGHT_OPEN
			local hit = workspace:Raycast(eye, dir, rayParams)
			table.insert(dists, if hit then hit.Distance else SIGHT_OPEN)
		end
		table.sort(dists)
		if (dists[4] + dists[5]) / 2 < SIGHT_CLOSED then
			table.insert(closed, ("closed at %s (median %.0f studs)"):format(fmt(a.pos), (dists[4] + dists[5]) / 2))
		elseif dists[1] >= SIGHT_OPEN then
			table.insert(open, ("open at %s (nothing within %d studs)"):format(fmt(a.pos), SIGHT_OPEN))
		end
	end
	section(("6a Sight lines too closed (%d of %d samples)"):format(#closed, sampled), closed)
	section(("6b Sight lines too open (%d of %d samples)"):format(#open, sampled), open)
end

-- 7 visible parts fully inside a block, and exact duplicates
local regionParts = workspace:GetPartBoundsInBox(
	CFrame.new(centre),
	Vector3.new(2, 0, 2) * REGION_RADIUS + Vector3.new(0, 1000, 0),
	overlapParams
)
do
	local lines = {}
	local function inside(a: BasePart, b: BasePart): boolean
		local half = b.Size / 2 + Vector3.new(0.01, 0.01, 0.01)
		for _, sx in { -1, 1 } do
			for _, sy in { -1, 1 } do
				for _, sz in { -1, 1 } do
					local corner = a.CFrame:PointToWorldSpace(a.Size / 2 * Vector3.new(sx, sy, sz))
					local p = b.CFrame:PointToObjectSpace(corner)
					if math.abs(p.X) > half.X or math.abs(p.Y) > half.Y or math.abs(p.Z) > half.Z then
						return false
					end
				end
			end
		end
		return true
	end
	for idx, a in regionParts do
		if a.Transparency >= 1 or a:IsA("Terrain") then
			continue
		end
		for _, b in workspace:GetPartBoundsInBox(a.CFrame, a.Size, overlapParams) do
			if b == a or b.Transparency >= 1 then
				continue
			end
			if b.CFrame == a.CFrame and b.Size == a.Size then
				if a:GetFullName() < b:GetFullName() then
					table.insert(lines, ("duplicate %s = %s"):format(short(a), short(b)))
				end
			elseif b:IsA("Part") and b.Shape == Enum.PartType.Block and inside(a, b) then
				table.insert(lines, ("%s hidden inside %s"):format(short(a), short(b)))
			end
		end
		if idx % 300 == 0 then
			task.wait()
		end
	end
	section("7 Parts inside parts / duplicates", lines)
end

-- 8 uneven rings: groups of 5+ parts around a common centre with uneven radius, height or spacing
do
	local lines = {}
	local parents: { [Instance]: { BasePart } } = {}
	for _, p in regionParts do
		local parent = p.Parent
		if parent then
			parents[parent] = parents[parent] or {}
			table.insert(parents[parent], p)
		end
	end
	for parent, parts in parents do
		if #parts < RING_MIN then
			continue
		end
		local sum = Vector3.zero
		for _, p in parts do
			sum += p.Position
		end
		local c = sum / #parts
		local radii, angles, ys = {}, {}, {}
		for _, p in parts do
			local d = p.Position - c
			table.insert(radii, Vector2.new(d.X, d.Z).Magnitude)
			table.insert(angles, math.deg(math.atan2(d.Z, d.X)) % 360)
			table.insert(ys, p.Position.Y)
		end
		table.sort(radii)
		table.sort(angles)
		table.sort(ys)
		local mean = (radii[1] + radii[#radii]) / 2
		-- Not a ring unless every part sits roughly the same distance from the centre.
		if mean < 1 or (radii[#radii] - radii[1]) / mean > 0.3 then
			continue
		end
		local gaps = {}
		for k = 1, #angles do
			table.insert(gaps, ((angles[k % #angles + 1] - angles[k]) % 360))
		end
		table.sort(gaps)
		if gaps[#gaps] > 2 * gaps[math.ceil(#gaps / 2)] then
			table.remove(gaps) -- an arc, not a full ring: ignore the open side
		end
		local problems = {}
		if radii[#radii] - radii[1] > RING_TOLERANCE then
			table.insert(problems, ("radius %.2f–%.2f"):format(radii[1], radii[#radii]))
		end
		if ys[#ys] - ys[1] > RING_TOLERANCE then
			table.insert(problems, ("height spread %.2f"):format(ys[#ys] - ys[1]))
		end
		if gaps[#gaps] - gaps[1] > RING_ANGLE_TOLERANCE then
			table.insert(problems, ("spacing %.1f°–%.1f°"):format(gaps[1], gaps[#gaps]))
		end
		if #problems > 0 then
			table.insert(lines, ("%s (%d parts): %s"):format(short(parent), #parts, table.concat(problems, ", ")))
		end
	end
	section("8 Uneven rings", lines)
end

-- 9 falls: one-way drops (too high to jump back) vs ragdoll-height falls (the game has no ragdoll / landing yet)
do
	local shortFalls: { [string]: { count: number, drop: number, at: Vector3 } } = {}
	local bigFalls: { [string]: { count: number, drop: number, at: Vector3 } } = {}
	for i in reach do
		local a = nodes[i]
		for _, j in out[i] do
			local drop = a.pos.Y - nodes[j].pos.Y
			if drop > JUMP_UP then
				local bucket = if drop >= RAGDOLL_FALL then bigFalls else shortFalls
				local key = short(a.part) .. " → " .. short(nodes[j].part)
				local e = bucket[key] or { count = 0, drop = 0, at = a.pos }
				e.count += 1
				e.drop = math.max(e.drop, drop)
				bucket[key] = e
			end
		end
	end
	local function lines(bucket: { [string]: { count: number, drop: number, at: Vector3 } }): { string }
		local l = {}
		for key, e in bucket do
			table.insert(l, ("%s  %.0f studs, %d spots, at %s"):format(key, e.drop, e.count, fmt(e.at)))
		end
		table.sort(l)
		return l
	end
	section(
		("9a One-way short falls (%.1f–%d studs, can't jump back)"):format(JUMP_UP, RAGDOLL_FALL),
		lines(shortFalls)
	)
	section(("9b Ragdoll-height falls (%d+ studs, no landing reaction)"):format(RAGDOLL_FALL), lines(bigFalls))
end

local reached = 0
for _ in reach do
	reached += 1
end
table.insert(
	report,
	1,
	("Map check around %s, radius %d, cell %d: %d floor cells, %d reachable · jump up %.1f studs, speed %d"):format(
		fmt(centre),
		REGION_RADIUS,
		CELL,
		#nodes,
		reached,
		JUMP_UP,
		speed
	)
)
return table.concat(report, "\n")
