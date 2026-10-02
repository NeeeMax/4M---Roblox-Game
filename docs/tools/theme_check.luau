--!nocheck
-- Checks one decor theme file (src/shared/Config/DecorThemeNN.luau, schema: Config/DecorTypes) against the layout rules:
--   lune run docs/tools/theme_check src/shared/Config/DecorTheme01.luau 1
-- (the second argument is the bay number). Exit code 1 = errors. The theme file may only use Vector3.new, Vector2.new,
-- Color3.fromRGB, Enum.<x>.<y>, math/string/table and `require(script.Parent.DecorTypes)` (it is stubbed).
--
-- Rules (all positions in the stage frame: +X right, -Z deeper, +Z toward the road):
--  * schema: Key, Name, Area (X, Y <= 190), part count (10 for bays 1-3, 15 for 4-8, 20 for 9-14, 25 for 15-21, 30 for 22-30), unique alphanumeric ids, prices not
--    dropping, 1-16 pieces per part, every Part has Pad, the theme has Shiba, Path, BayPad, AutoPad
--  * Path: starts at (0, Area.Y/2), ends at (0, -Area.Y/2), every waypoint inside the Area, segments >= 8 long
--  * every piece inside the Area (rotated bounding boxes; a part's optional Yaw turns all its pieces about the centre of their union box)
--  * a piece is SOLID (the player cannot walk through it) if it is over 0.6 studs high and starts lower than 7 studs above the
--    ground (same rule as World/StreetPlot); solid pieces keep clear of: the walkway (5.5 studs from its centre line), the Shiba
--    (8 studs: its platform and barrier), the zone in front of the Shiba (8-17 studs along its facing, 5 studs to each side), every pad (3 studs, pieces of
--    OTHER parts; the own prop stands where the pad is) and the Intern's spot
--  * walkability: a player (radius 1.5) entering at the stage's front centre can reach every pad (with all props of the other
--    parts built), the area in front of the Shiba and the stage's back exit

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local process = require("@lune/process")

local file = process.args[1]
local bay = tonumber(process.args[2])
if not file or not bay then
	print("usage: lune run docs/tools/theme_check <theme file> <bay>")
	process.exit(2)
end

local function V3(x, y, z)
	return { X = x, Y = y, Z = z }
end
local function V2(x, y)
	return { X = x, Y = y }
end
local enum = setmetatable({}, {
	__index = function(_, k)
		return setmetatable({}, {
			__index = function(_, j)
				return k .. "." .. j
			end,
		})
	end,
})
local chunk = luau.load(fs.readFile(file), {
	debugName = file,
	environment = {
		Vector3 = { new = V3, zero = V3(0, 0, 0) },
		Vector2 = { new = V2 },
		Color3 = {
			fromRGB = function(r, g, b)
				return { r, g, b }
			end,
		},
		Enum = enum,
		require = function()
			return {}
		end,
		script = setmetatable({}, {
			__index = function(self)
				return self
			end,
		}),
	},
	injectGlobals = true,
})
local theme = chunk()

local errors = 0
local function err(message)
	errors += 1
	print("ERROR " .. message)
end

if type(theme) ~= "table" then
	err("the file returns " .. tostring(theme) .. " instead of a theme")
	process.exit(1)
end

-- ---- schema
local expectParts = if bay <= 3 then 10 elseif bay <= 8 then 15 elseif bay <= 14 then 20 elseif bay <= 21 then 25 else 30
if not (theme.Key and string.match(theme.Key, "^%w+$")) then
	err("Key must be letters and digits")
end
if not theme.Name or theme.Name == "" then
	err("Name missing")
end
local area = theme.Area
if not area or area.X > 190 or area.Y > 190 or area.X < 40 or area.Y < 40 then
	err("Area must be between 40 and 190 per side")
	process.exit(1)
end
local hx, hz = area.X / 2, area.Y / 2
if #theme.Parts ~= expectParts then
	err(`{#theme.Parts} parts, expected {expectParts}`)
end
local ids, lastPrice = {}, 0
for i, part in theme.Parts do
	if not string.match(part.Id or "", "^%w+$") then
		err(`part {i}: Id must be letters and digits`)
	end
	if ids[part.Id] then
		err(`part {i}: duplicate Id {part.Id}`)
	end
	ids[part.Id] = true
	if not part.Name or part.Name == "" or not part.Description or part.Description == "" then
		err(`part {i} ({part.Id}): Name or Description empty`)
	end
	if (part.PriceSeconds or 0) < lastPrice then
		err(`part {i} ({part.Id}): PriceSeconds drops`)
	end
	lastPrice = part.PriceSeconds or 0
	if #part.Pieces < 1 or #part.Pieces > 16 then
		err(`part {i} ({part.Id}): {#part.Pieces} pieces (1 to 16)`)
	end
	if part.Yaw ~= nil and type(part.Yaw) ~= "number" then
		err(`part {i} ({part.Id}): Yaw must be a number (degrees)`)
	end
	if not part.Pad then
		err(`part {i} ({part.Id}): Pad missing`)
	elseif math.abs(part.Pad.X) > hx - 3 or math.abs(part.Pad.Y) > hz - 3 then
		err(`part {i} ({part.Id}): Pad outside the Area`)
	end
end
if not theme.Shiba or not theme.Shiba.Position or not theme.Shiba.Facing then
	err("Shiba spot (Position, Facing) missing")
	process.exit(1)
end
if not theme.Path or #theme.Path < 2 then
	err("Path needs at least 2 waypoints")
	process.exit(1)
end
if not theme.BayPad or not theme.AutoPad then
	err("BayPad and AutoPad needed")
	process.exit(1)
end

-- RewardMult: 1 to 2 per part, the whole theme at most 8, at least 3 parts have one
local bonusProduct, bonusParts = 1, 0
for i, part in theme.Parts do
	if part.RewardMult ~= nil then
		if type(part.RewardMult) ~= "number" or part.RewardMult < 1 or part.RewardMult > 2 then
			err(`part {i} ({part.Id}): RewardMult must be between 1 and 2`)
		else
			bonusProduct *= part.RewardMult
			bonusParts += 1
		end
	end
end
if bonusProduct > 8 then
	err(`the RewardMult of the whole theme is {bonusProduct}, at most 8`)
end
if bonusParts < 3 then
	err(`only {bonusParts} parts have a RewardMult (at least 3)`)
end

-- ---- path
local path = theme.Path
if path[1].X ~= 0 or path[1].Y ~= hz then
	err(`Path must start at (0, {hz})`)
end
if path[#path].X ~= 0 or path[#path].Y ~= -hz then
	err(`Path must end at (0, {-hz})`)
end
for i, point in path do
	if math.abs(point.X) > hx - 8 or math.abs(point.Y) > hz then
		err(`Path waypoint {i} outside the Area`)
	end
	if i > 1 then
		local dx, dy = point.X - path[i - 1].X, point.Y - path[i - 1].Y
		if math.sqrt(dx * dx + dy * dy) < 8 then
			err(`Path segment {i - 1} is shorter than 8`)
		end
	end
end

-- ---- pieces and obstacles
-- The footprint (x0, x1, z0, z1) of a piece. `yaw` (radians) and `center` (x, z of the union box of the part's pieces) apply the
-- part's Yaw: the offset is turned about the centre, and the piece's own rotation gets the yaw added.
local function bounds(piece, yaw, center)
	yaw = yaw or 0
	local r = piece.Rotation
	local sx, sy, sz = piece.Size.X / 2, piece.Size.Y / 2, piece.Size.Z / 2
	local rotated = r and (r.X ~= 0 or r.Y ~= 0 or r.Z ~= 0)
	if rotated or yaw ~= 0 then
		local ax, ay, az = math.rad(r and r.X or 0), math.rad(r and r.Y or 0), math.rad(r and r.Z or 0)
		local cx, sx_, cy, sy_, cz, sz_ =
			math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
		local Rx = { { 1, 0, 0 }, { 0, cx, -sx_ }, { 0, sx_, cx } }
		local Ry = { { cy, 0, sy_ }, { 0, 1, 0 }, { -sy_, 0, cy } }
		local Rz = { { cz, -sz_, 0 }, { sz_, cz, 0 }, { 0, 0, 1 } }
		local function mul(a, b)
			local o = {}
			for i = 1, 3 do
				o[i] = {}
				for j = 1, 3 do
					local s = 0
					for k = 1, 3 do
						s += a[i][k] * b[k][j]
					end
					o[i][j] = s
				end
			end
			return o
		end
		local m = mul(mul(Ry, Rx), Rz)
		if yaw ~= 0 then
			local cw, sw = math.cos(yaw), math.sin(yaw)
			m = mul({ { cw, 0, sw }, { 0, 1, 0 }, { -sw, 0, cw } }, m)
		end
		sx, sy, sz =
			math.abs(m[1][1]) * sx + math.abs(m[1][2]) * sy + math.abs(m[1][3]) * sz,
			math.abs(m[2][1]) * sx + math.abs(m[2][2]) * sy + math.abs(m[2][3]) * sz,
			math.abs(m[3][1]) * sx + math.abs(m[3][2]) * sy + math.abs(m[3][3]) * sz
	end
	local o = piece.Offset
	local ox, oz = o.X, o.Z
	if yaw ~= 0 then
		local dx, dz = ox - center[1], oz - center[2]
		ox = center[1] + dx * math.cos(yaw) + dz * math.sin(yaw)
		oz = center[2] - dx * math.sin(yaw) + dz * math.cos(yaw)
	end
	return ox - sx, ox + sx, oz - sz, oz + sz
end

-- Centre (x, z) of the union box of a part's pieces (before its Yaw): the point the Yaw turns around.
local function partCenter(part)
	local x0, x1, z0, z1 = math.huge, -math.huge, math.huge, -math.huge
	for _, piece in part.Pieces do
		local a, b, c, d = bounds(piece)
		x0, x1, z0, z1 = math.min(x0, a), math.max(x1, b), math.min(z0, c), math.max(z1, d)
	end
	return { (x0 + x1) / 2, (z0 + z1) / 2 }
end

local obstacles = {} -- { x0, x1, z0, z1, part = index }
local pieceCount = 0
for i, part in theme.Parts do
	local yaw = math.rad(part.Yaw or 0)
	local center = partCenter(part)
	for n, piece in part.Pieces do
		pieceCount += 1
		local x0, x1, z0, z1 = bounds(piece, yaw, center)
		if x0 < -hx - 0.01 or x1 > hx + 0.01 or z0 < -hz - 0.01 or z1 > hz + 0.01 then
			err(`part {i} ({part.Id}) piece {n} sticks out of the Area`)
		end
		local rotated = piece.Rotation and (piece.Rotation.X ~= 0 or piece.Rotation.Y ~= 0 or piece.Rotation.Z ~= 0)
		local reach = if rotated then math.max(piece.Size.X, piece.Size.Y, piece.Size.Z) / 2 else piece.Size.Y / 2
		if piece.Offset.Y + reach > 0.6 and piece.Offset.Y - reach < 7 then
			table.insert(obstacles, { x0, x1, z0, z1, part = i })
		end
	end
end

local function inside(rect, x, z, grow)
	return x >= rect[1] - grow and x <= rect[2] + grow and z >= rect[3] - grow and z <= rect[4] + grow
end
local function blockedAt(x, z, grow, exceptPart)
	for _, rect in obstacles do
		if rect.part ~= exceptPart and inside(rect, x, z, grow) then
			return true
		end
	end
	return false
end

-- walkway
for index = 1, #path - 1 do
	local a, b = path[index], path[index + 1]
	local length = math.sqrt((b.X - a.X) ^ 2 + (b.Y - a.Y) ^ 2)
	for step = 0, math.floor(length) do
		local t = step / math.max(1, math.floor(length))
		local x, z = a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t
		if blockedAt(x, z, 5.5, nil) then
			err(`a solid piece is on the walkway near ({math.floor(x)}, {math.floor(z)})`)
			break
		end
	end
end

-- Shiba and the zone in front of it
local sp = theme.Shiba.Position
local face = math.rad(theme.Shiba.Facing)
local fx, fz = math.cos(face), -math.sin(face)
local rx, rz = -fz, fx -- to the side
if blockedAt(sp.X, sp.Y, 8, nil) then
	err("a solid piece is within 8 studs of the Shiba")
end
for along = 8, 17, 1 do
	for side = -5, 5, 2.5 do
		local x, z = sp.X + fx * along + rx * side, sp.Y + fz * along + rz * side
		if blockedAt(x, z, 0, nil) then
			err(`the zone in front of the Shiba is blocked at ({math.floor(x)}, {math.floor(z)})`)
			break
		end
	end
end
if math.abs(sp.X) > hx - 8 or math.abs(sp.Y) > hz - 8 then
	err("the Shiba stands too close to the edge of the Area")
end
local intern = { sp.X + fx * 7.5, sp.Y + fz * 7.5 }
if blockedAt(intern[1], intern[2], 1.5, nil) then
	err("a solid piece stands on the Intern's spot")
end

-- pads
local function padClear(pad, label, exceptPart)
	for _, radius in { 0, 1.5, 3 } do
		for k = 0, 7 do
			local a = k * math.pi / 4
			local x, z = pad.X + math.cos(a) * radius, pad.Y + math.sin(a) * radius
			if blockedAt(x, z, 0, exceptPart) then
				err(`{label}: a solid piece blocks the pad near ({math.floor(x)}, {math.floor(z)})`)
				return
			end
		end
	end
end
padClear(theme.BayPad, "BayPad", nil)
padClear(theme.AutoPad, "AutoPad", nil)
for i, part in theme.Parts do
	if part.Pad then
		padClear(part.Pad, `part {i} ({part.Id})`, i)
	end
end

-- ---- walkability (grid, 2 studs, player radius 1.5)
local cell = 2
local cols, rows = math.ceil(area.X / cell), math.ceil(area.Y / cell)
local function toCell(x, z)
	return math.clamp(math.floor((x + hx) / cell) + 1, 1, cols), math.clamp(math.floor((z + hz) / cell) + 1, 1, rows)
end
local function flood(exceptPart)
	local blocked = {}
	for c = 1, cols do
		blocked[c] = {}
	end
	for _, rect in obstacles do
		if rect.part ~= exceptPart then
			local c0, r0 = toCell(rect[1] - 1.5, rect[3] - 1.5)
			local c1, r1 = toCell(rect[2] + 1.5, rect[4] + 1.5)
			for c = c0, c1 do
				for r = r0, r1 do
					blocked[c][r] = true
				end
			end
		end
	end
	-- the Shiba's body
	local c0, r0 = toCell(sp.X - 4, sp.Y - 4)
	local c1, r1 = toCell(sp.X + 4, sp.Y + 4)
	for c = c0, c1 do
		for r = r0, r1 do
			blocked[c][r] = true
		end
	end
	local reached = {}
	for c = 1, cols do
		reached[c] = {}
	end
	local sc, sr = toCell(0, hz - 2)
	local queue, head = { { sc, sr } }, 1
	reached[sc][sr] = true
	blocked[sc][sr] = nil
	while head <= #queue do
		local c, r = queue[head][1], queue[head][2]
		head += 1
		for _, d in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
			local nc, nr = c + d[1], r + d[2]
			if nc >= 1 and nc <= cols and nr >= 1 and nr <= rows and not blocked[nc][nr] and not reached[nc][nr] then
				reached[nc][nr] = true
				table.insert(queue, { nc, nr })
			end
		end
	end
	return reached
end
local function canReach(reached, x, z)
	local c, r = toCell(x, z)
	return reached[c][r] == true
end

local all = flood(nil)
if not canReach(all, sp.X + fx * 9, sp.Y + fz * 9) then
	err("the player cannot reach the zone in front of the Shiba")
end
if not canReach(all, 0, -hz + 2) then
	err("the stage's back exit cannot be reached from the front")
end
if not canReach(all, theme.BayPad.X, theme.BayPad.Y) then
	err("BayPad cannot be reached")
end
if not canReach(all, theme.AutoPad.X, theme.AutoPad.Y) then
	err("AutoPad cannot be reached")
end
for i, part in theme.Parts do
	if part.Pad and not canReach(flood(i), part.Pad.X, part.Pad.Y) then
		err(`part {i} ({part.Id}): the pad cannot be reached`)
	end
end

print(
	`{theme.Key}: {#theme.Parts} parts, {pieceCount} pieces, {#obstacles} solid, Area {area.X}x{area.Y}, {errors} error(s)`
)
if errors > 0 then
	process.exit(1)
end
