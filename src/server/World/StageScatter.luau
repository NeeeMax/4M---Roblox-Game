--!strict
-- The organic dressing of a Shiba stage (docs/GAME_DESIGN.md -> "Stage scatter"; data in Config/StageScatter):
--   - the winding path: the theme's waypoints become a smooth curve (centripetal Catmull-Rom, kept within MAX_DEVIATION studs of
--     the original polyline, which is what the validator and the pad reachability use) with a slightly varying width;
--   - the scatter: fence rows along both sides of the curve (rotated to its tangent, with gaps), clusters of trees, bushes, rocks
--     and flowers in the empty areas (random yaw, random scale, rocks and logs lean), tufts and small rocks along the border of
--     the theme's Area and along the path's edges.
-- Everything is deterministic (seeded by plot slot and bay), anchored, not queryable and not collidable, except the invisible
-- trunk colliders of big trees and boulders. A prop is the model Assets.Scatter_<Name> if it exists, else a primitive-built
-- fallback. Nothing is announced (no pop-in): the scatter appears silently with its stage. The stage frame is the one of
-- Config/DecorTypes (origin in the middle of the stage on the path's centre line, +X right, -Z deeper, +Y up).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config.StageScatter)
local TycoonDecor = require(ReplicatedStorage.Shared.Config.TycoonDecor)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local StreetLayout = require(ReplicatedStorage.Shared.Util.StreetLayout)

local LAYOUT = TycoonWorld.Street
local STAGE_SCALE = LAYOUT.StageScale
local TAU = math.pi * 2

type Prop = Config.Prop
type Entries = Config.Entries

export type PathData = {
	-- Points of the curve in the stage frame (X, Z), about SAMPLE studs apart, from the front of the stage to its back.
	Points: { Vector2 },
	-- Width factor at every point (1 +- WIDTH_VARIATION, exactly 1 at both ends so neighbouring stages join).
	Widths: { number },
	-- Distance along the curve at every point, and its total length.
	Arc: { number },
	Length: number,
}

export type Params = {
	Bay: number,
	Slot: number,
	-- The stage frame in the world (StreetPlot.stageFrame).
	Frame: CFrame,
	-- Every pad of the stage in the stage frame (X, Z).
	Pads: { Vector2 },
	Parent: Instance,
}

type Rect = { X: number, Z: number, HX: number, HZ: number, Cos: number, Sin: number }

local StageScatter = {}

-- ==== the path =========================================================================================================

-- Spacing of the curve's points, the most the curve may stray from the theme's polyline, and the width variation.
local SAMPLE = 3
local MAX_DEVIATION = 2.8
local WIDTH_VARIATION = 0.08
-- How far the end tangents are extended straight along the stage axis, so neighbouring stages join without a kink.
local GHOST = 12

local function nearestOnPolyline(poly: { Vector2 }, point: Vector2): Vector2
	local best = poly[1]
	local bestDistance = math.huge
	for index = 1, #poly - 1 do
		local a, b = poly[index], poly[index + 1]
		local along = b - a
		local length2 = along:Dot(along)
		local t = if length2 > 0 then math.clamp((point - a):Dot(along) / length2, 0, 1) else 0
		local candidate = a + along * t
		local distance = (point - candidate).Magnitude
		if distance < bestDistance then
			best, bestDistance = candidate, distance
		end
	end
	return best
end

-- Centripetal Catmull-Rom (Barry-Goldman) between p1 and p2 at u = 0 .. 1.
local function catmull(p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2, u: number): Vector2
	local t0 = 0
	local t1 = t0 + math.max(0.001, (p1 - p0).Magnitude) ^ 0.5
	local t2 = t1 + math.max(0.001, (p2 - p1).Magnitude) ^ 0.5
	local t3 = t2 + math.max(0.001, (p3 - p2).Magnitude) ^ 0.5
	local t = t1 + (t2 - t1) * u
	local a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
	local a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
	local a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
	local b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
	local b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
	return b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1))
end

local function clampToPolyline(points: { Vector2 }, poly: { Vector2 })
	for index = 2, #points - 1 do
		local point = points[index]
		local nearest = nearestOnPolyline(poly, point)
		local offset = point - nearest
		if offset.Magnitude > MAX_DEVIATION then
			points[index] = nearest + offset.Unit * MAX_DEVIATION
		end
	end
end

local function computePath(bay: number): PathData
	local theme = TycoonDecor.Themes[bay]
	local area = StreetLayout.AreaOf(bay)
	local depth = StreetLayout.Compute().Depths[bay]

	-- The original polyline in the stage frame: from the stage's front to its back, along the theme's waypoints.
	local poly: { Vector2 } = { Vector2.new(0, depth / 2) }
	if theme and theme.Path then
		for _, waypoint in theme.Path do
			table.insert(poly, waypoint * STAGE_SCALE)
		end
	else
		table.insert(poly, Vector2.new(0, area.Y / 2))
		table.insert(poly, Vector2.new(0, -area.Y / 2))
	end
	table.insert(poly, Vector2.new(0, -depth / 2))

	-- A dense curve through the polyline's points.
	local control: { Vector2 } = table.clone(poly)
	table.insert(control, 1, poly[1] + Vector2.new(0, GHOST))
	table.insert(control, poly[#poly] + Vector2.new(0, -GHOST))
	local dense: { Vector2 } = {}
	for index = 2, #control - 2 do
		local p0, p1, p2, p3 = control[index - 1], control[index], control[index + 1], control[index + 2]
		local steps = math.max(4, math.ceil((p2 - p1).Magnitude / 1.5))
		for step = 0, steps - 1 do
			table.insert(dense, catmull(p0, p1, p2, p3, step / steps))
		end
	end
	table.insert(dense, poly[#poly])

	-- Round off whatever is still sharp, but never leave the walkway the pads were placed on.
	clampToPolyline(dense, poly)
	for _ = 1, 2 do
		for _ = 1, 3 do
			local smooth = table.clone(dense)
			for index = 2, #dense - 1 do
				smooth[index] = dense[index - 1] * 0.25 + dense[index] * 0.5 + dense[index + 1] * 0.25
			end
			dense = smooth
		end
		clampToPolyline(dense, poly)
	end

	-- Even spacing along the curve.
	local cumulative: { number } = { 0 }
	for index = 2, #dense do
		cumulative[index] = cumulative[index - 1] + (dense[index] - dense[index - 1]).Magnitude
	end
	local total = cumulative[#cumulative]
	local count = math.max(2, math.round(total / SAMPLE))
	local points: { Vector2 } = {}
	local arc: { number } = {}
	local cursor = 1
	for step = 0, count do
		local s = total * step / count
		while cursor < #dense - 1 and cumulative[cursor + 1] < s do
			cursor += 1
		end
		local span = cumulative[cursor + 1] - cumulative[cursor]
		local t = if span > 0 then (s - cumulative[cursor]) / span else 0
		table.insert(points, dense[cursor]:Lerp(dense[cursor + 1], math.clamp(t, 0, 1)))
		table.insert(arc, s)
	end
	points[1] = poly[1]
	points[#points] = poly[#poly]

	-- A slowly changing width, plain at both ends.
	local random = Random.new(bay * 131 + 7)
	local phaseA, phaseB = random:NextNumber(0, TAU), random:NextNumber(0, TAU)
	local widths: { number } = {}
	for index, s in arc do
		local fade = math.min(1, s / 8, (total - s) / 8)
		local wave = 0.6 * math.sin(s * 0.085 + phaseA) + 0.4 * math.sin(s * 0.21 + phaseB)
		widths[index] = 1 + WIDTH_VARIATION * math.max(0, fade) * wave
	end
	return { Points = points, Widths = widths, Arc = arc, Length = total }
end

local pathCache: { [number]: PathData } = {}

-- The smooth path of a bay (memoised, the same for every plot): see PathData. Stage frame, StageScale applied.
function StageScatter.PathFor(bay: number): PathData
	local cached = pathCache[bay]
	if cached then
		return cached
	end
	local data = computePath(bay)
	pathCache[bay] = data
	return data
end

-- Position on the curve `s` studs from its start and the unit tangent there (toward the back of the stage).
local function pathFrame(data: PathData, s: number): (Vector2, Vector2)
	local function position(at: number): Vector2
		local clamped = math.clamp(at, 0, data.Length)
		local low, high = 1, #data.Arc
		while high - low > 1 do
			local middle = (low + high) // 2
			if data.Arc[middle] <= clamped then
				low = middle
			else
				high = middle
			end
		end
		local span = data.Arc[high] - data.Arc[low]
		local t = if span > 0 then (clamped - data.Arc[low]) / span else 0
		return data.Points[low]:Lerp(data.Points[high], t)
	end
	local ahead, behind = position(s + 1.5), position(s - 1.5)
	local along = ahead - behind
	local tangent = if along.Magnitude > 0.001 then along.Unit else Vector2.new(0, -1)
	return position(s), tangent
end

local function distanceToPath(data: PathData, x: number, z: number): number
	local best = math.huge
	local points = data.Points
	for index = 1, #points - 1 do
		local a, b = points[index], points[index + 1]
		local abX, abZ = b.X - a.X, b.Y - a.Y
		local length2 = abX * abX + abZ * abZ
		local t = if length2 > 0 then math.clamp(((x - a.X) * abX + (z - a.Y) * abZ) / length2, 0, 1) else 0
		local dx, dz = x - (a.X + abX * t), z - (a.Y + abZ * t)
		local d2 = dx * dx + dz * dz
		if d2 < best then
			best = d2
		end
	end
	return math.sqrt(best)
end

local function distanceToSegment(a: Vector2, b: Vector2, x: number, z: number): number
	local abX, abZ = b.X - a.X, b.Y - a.Y
	local length2 = abX * abX + abZ * abZ
	local t = if length2 > 0 then math.clamp(((x - a.X) * abX + (z - a.Y) * abZ) / length2, 0, 1) else 0
	local dx, dz = x - (a.X + abX * t), z - (a.Y + abZ * t)
	return math.sqrt(dx * dx + dz * dz)
end

-- ==== the theme's solid footprints =====================================================================================

-- Props the player could walk into (same rule as World/StreetPlot and docs/tools/theme_check).
local function isSolid(piece: TycoonDecor.Piece): boolean
	local reach = if piece.Rotation then math.max(piece.Size.X, piece.Size.Y, piece.Size.Z) / 2 else piece.Size.Y / 2
	return piece.Offset.Y + reach > 0.6 and piece.Offset.Y - reach < 7
end

-- Centre (X, Z, scaled) of the union box of a part's pieces: the point its Yaw turns around (same as StreetPlot.piecesBox).
local function partCenter(pieces: { TycoonDecor.Piece }): Vector2
	local low = Vector3.new(math.huge, math.huge, math.huge)
	local high = Vector3.new(-math.huge, -math.huge, -math.huge)
	for _, piece in pieces do
		local rotation = piece.Rotation or Vector3.zero
		local cframe = CFrame.new(piece.Offset)
			* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
		local half = piece.Size / 2
		for _, x in { -1, 1 } do
			for _, y in { -1, 1 } do
				for _, z in { -1, 1 } do
					local corner = cframe:PointToWorldSpace(Vector3.new(x * half.X, y * half.Y, z * half.Z))
					low = low:Min(corner)
					high = high:Max(corner)
				end
			end
		end
	end
	return Vector2.new((low.X + high.X) / 2, (low.Z + high.Z) / 2) * STAGE_SCALE
end

local function footprints(theme: TycoonDecor.Theme?): { Rect }
	local rects: { Rect } = {}
	if not theme then
		return rects
	end
	for _, part in theme.Parts do
		local yaw = math.rad(part.Yaw or 0)
		local cosYaw, sinYaw = math.cos(yaw), math.sin(yaw)
		local center = partCenter(part.Pieces)
		for _, piece in part.Pieces do
			if isSolid(piece) then
				local rotation = piece.Rotation or Vector3.zero
				local halfX: number, halfZ: number, angle: number
				if rotation.X == 0 and rotation.Z == 0 then
					halfX, halfZ = piece.Size.X / 2 * STAGE_SCALE, piece.Size.Z / 2 * STAGE_SCALE
					angle = math.rad(rotation.Y) + yaw
				else
					-- A tilted piece: its axis-aligned box, turned with the part.
					local cframe = CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
					halfX, halfZ = 0, 0
					for _, x in { -1, 1 } do
						for _, y in { -1, 1 } do
							for _, z in { -1, 1 } do
								local corner = cframe:PointToWorldSpace(
									Vector3.new(x * piece.Size.X / 2, y * piece.Size.Y / 2, z * piece.Size.Z / 2)
								)
								halfX = math.max(halfX, math.abs(corner.X))
								halfZ = math.max(halfZ, math.abs(corner.Z))
							end
						end
					end
					halfX, halfZ = halfX * STAGE_SCALE, halfZ * STAGE_SCALE
					angle = yaw
				end
				local offset = piece.Offset * STAGE_SCALE
				local relX, relZ = offset.X - center.X, offset.Z - center.Y
				table.insert(rects, {
					X = center.X + relX * cosYaw + relZ * sinYaw,
					Z = center.Y - relX * sinYaw + relZ * cosYaw,
					HX = halfX,
					HZ = halfZ,
					Cos = math.cos(angle),
					Sin = math.sin(angle),
				})
			end
		end
	end
	return rects
end

-- ==== primitive fallbacks ==============================================================================================

local function shade(color: Color3, random: Random, amount: number): Color3
	local t = random:NextNumber(-amount, amount)
	return if t >= 0 then color:Lerp(Color3.new(1, 1, 1), t) else color:Lerp(Color3.new(0, 0, 0), -t)
end

local function flat(material: Enum.Material): Enum.Material
	if material == Enum.Material.Neon or material == Enum.Material.ForceField then
		return Enum.Material.SmoothPlastic
	end
	return material
end

-- Builds the fallback of `spec` at scale `s` in the frame `base` (origin = bottom centre, +Y up, fences run along X).
local function buildFallback(spec: Prop, base: CFrame, s: number, random: Random): Model
	local model = Instance.new("Model")
	local H, W = spec.Height * s, spec.Width * s
	local color = shade(spec.Color, random, 0.07)
	local color2 = shade(spec.Color2 or spec.Color, random, 0.05)
	local kind = spec.Kind

	local function make(size: Vector3, cframe: CFrame, col: Color3, shape: Enum.PartType?, transparency: number?): Part
		local part = Instance.new("Part")
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = H >= 6
		part.Material = Enum.Material.SmoothPlastic
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.Color = col
		part.Size = size
		part.CFrame = cframe
		if shape then
			part.Shape = shape
		end
		part.Transparency = transparency or 0
		part.Parent = model
		return part
	end
	local function box(size: Vector3, offset: CFrame, col: Color3, transparency: number?): Part
		return make(size, base * offset, col, nil, transparency)
	end
	local function ball(diameter: number, x: number, y: number, z: number, col: Color3): Part
		return make(Vector3.new(diameter, diameter, diameter), base * CFrame.new(x, y, z), col, Enum.PartType.Ball, nil)
	end
	-- A cylinder along the local Y axis of `at` (the engine's own axis is X: turned up here).
	local function cyl(height: number, diameter: number, axis: CFrame, col: Color3): Part
		return make(
			Vector3.new(height, diameter, diameter),
			base * axis * CFrame.Angles(0, 0, math.pi / 2),
			col,
			Enum.PartType.Cylinder,
			nil
		)
	end
	local function at(x: number, y: number, z: number): CFrame
		return CFrame.new(x, y, z)
	end
	-- Horizontal along X.
	local function along(x: number, y: number, z: number): CFrame
		return CFrame.new(x, y, z) * CFrame.Angles(0, 0, math.pi / 2)
	end

	if kind == "Oak" then
		local canopy = W
		local trunk = H - canopy * 0.55
		cyl(trunk, math.max(0.5, canopy * 0.15), at(0, trunk / 2, 0), color2)
		ball(canopy, 0, H - canopy / 2, 0, color)
		ball(canopy * 0.7, canopy * 0.32, H - canopy * 0.62, canopy * 0.15, shade(color, random, 0.12))
		ball(canopy * 0.6, -canopy * 0.3, H - canopy * 0.68, -canopy * 0.2, shade(color, random, 0.12))
	elseif kind == "Pine" then
		local snowy = spec.Color2 ~= nil and (spec.Color2.R + spec.Color2.G + spec.Color2.B) / 3 > 0.85
		local bark = if snowy then Color3.fromRGB(90, 64, 44) else (spec.Color2 or Color3.fromRGB(90, 64, 44))
		cyl(H * 0.3, W * 0.14, at(0, H * 0.15, 0), bark)
		for tier = 0, 2 do
			local height = H * 0.22
			local tierColor = if snowy and tier == 2 then spec.Color2 or color else shade(color, random, 0.06)
			cyl(height, W * (1 - tier * 0.27), at(0, H * 0.25 + tier * H * 0.22 + height / 2, 0), tierColor)
		end
		ball(W * 0.3, 0, H * 0.94, 0, if snowy then spec.Color2 or color else color)
	elseif kind == "Palm" then
		local trunkHeight = H * 0.9
		local lean = CFrame.Angles(0, 0, -0.1)
		cyl(trunkHeight, W * 0.1, lean * at(0, trunkHeight / 2, 0), color2)
		local top = lean * Vector3.new(0, trunkHeight, 0)
		for index = 0, 5 do
			local leaf = CFrame.new(top) * CFrame.Angles(0, index / 6 * TAU, 0) * CFrame.Angles(0, 0, -0.45)
			box(Vector3.new(W * 0.58, 0.3, W * 0.2), leaf * at(W * 0.29, 0, 0), shade(color, random, 0.1))
		end
		ball(W * 0.14, top.X + 0.2 * s, top.Y - 0.5 * s, 0, color2)
	elseif kind == "DeadTree" then
		local trunk = H * 0.85
		cyl(trunk, W * 0.2, at(0, trunk / 2, 0), color)
		for index = 0, 2 do
			local branchLength = H * 0.36
			local branch = at(0, H * (0.45 + index * 0.14), 0)
				* CFrame.Angles(0, index * 2.1 + random:NextNumber(0, 0.6), 0)
				* CFrame.Angles(0, 0, -0.9)
			cyl(branchLength, W * 0.08, branch * at(0, branchLength / 2, 0), color)
		end
	elseif kind == "Bush" or (kind == "Flowers" and H > 2) then
		local d = math.min(W, H * 1.5)
		ball(d, 0, H - d / 2, 0, color)
		ball(d * 0.65, d * 0.38, H - d * 0.65, d * 0.12, shade(color, random, 0.1))
		ball(d * 0.6, -d * 0.36, H - d * 0.62, -d * 0.18, shade(color, random, 0.1))
		if kind == "Flowers" then
			for _ = 1, 6 do
				local angle, lift = random:NextNumber(0, TAU), random:NextNumber(0.25, 1)
				local reach = d * 0.5 * math.sqrt(1 - lift * lift * 0.6)
				ball(0.5 * s, math.cos(angle) * reach, H - d / 2 + lift * d * 0.42, math.sin(angle) * reach, color2)
			end
		end
	elseif kind == "Flowers" then
		cyl(0.25, W, at(0, 0.12, 0), color)
		local palette = { color2, Color3.fromRGB(255, 255, 255), shade(color2, random, 0.2) }
		for _ = 1, 8 do
			local angle, radius = random:NextNumber(0, TAU), random:NextNumber(0.1, 0.42) * W
			ball(0.6 * s, math.cos(angle) * radius, 0.45, math.sin(angle) * radius, palette[random:NextInteger(1, 3)])
		end
	elseif kind == "Hedge" then
		box(Vector3.new(W, H, W * 0.38), at(0, H / 2, 0), color)
		box(Vector3.new(W * 0.9, H * 0.18, W * 0.3), at(0, H * 1.02, 0), shade(color, random, 0.1))
	elseif kind == "Rock" then
		if random:NextNumber() < 0.5 then
			local d = math.min(W, H * 1.5)
			ball(d, 0, d * 0.35, 0, color)
			ball(d * 0.6, d * 0.36, d * 0.22, d * 0.1, shade(color, random, 0.08))
		else
			box(Vector3.new(W * 0.8, H * 0.9, W * 0.7), at(0, H * 0.4, 0) * CFrame.Angles(0.1, 0.35, 0.12), color)
			box(
				Vector3.new(W * 0.5, H * 0.6, W * 0.5),
				at(W * 0.28, H * 0.25, W * 0.12) * CFrame.Angles(-0.1, 1.1, 0.2),
				shade(color, random, 0.1)
			)
		end
	elseif kind == "Standing" then
		box(Vector3.new(W, H, W * 0.45), at(0, H / 2, 0), color)
		box(Vector3.new(W * 0.5, H * 0.35, 0.12), at(0, H * 0.55, W * 0.23), color2)
	elseif kind == "Stump" then
		cyl(H, W, at(0, H / 2, 0), color)
		cyl(0.12, W * 0.9, at(0, H + 0.02, 0), color2)
	elseif kind == "LogPile" then
		local d = H * 0.36
		for _, side in { -1, 1 } do
			cyl(W, d, along(0, d / 2, side * d * 0.5), color)
		end
		cyl(W, d, along(0, d * 1.35, 0), shade(color, random, 0.1))
	elseif kind == "Log" then
		local d = H * 0.7
		cyl(W, d, along(0, d / 2, 0), color)
		cyl(W * 0.35, d * 0.5, CFrame.new(W * 0.1, d * 0.9, 0) * CFrame.Angles(0, 0, math.pi / 2 - 0.8), color)
	elseif kind == "Lamp" then
		cyl(H * 0.06, W * 0.9, at(0, H * 0.03, 0), color)
		cyl(H, W * 0.28, at(0, H / 2, 0), color)
		ball(W * 0.9, 0, H + W * 0.2, 0, color2)
		box(Vector3.new(W * 0.8, 0.2, W * 0.8), at(0, H + W * 0.72, 0), color)
	elseif kind == "Crate" then
		box(Vector3.new(W, H, W), at(0, H / 2, 0), color)
		box(Vector3.new(W * 1.02, H * 0.12, W * 1.02), at(0, H * 0.2, 0), color2)
		box(Vector3.new(W * 1.02, H * 0.12, W * 1.02), at(0, H * 0.8, 0), color2)
		if random:NextNumber() < 0.35 then
			box(Vector3.new(W * 0.6, H * 0.6, W * 0.6), at(W * 0.1, H * 1.3, 0) * CFrame.Angles(0, 0.4, 0), color)
		end
	elseif kind == "Barrel" then
		cyl(H, W, at(0, H / 2, 0), color)
		cyl(0.2 * s, W * 1.07, at(0, H * 0.25, 0), color2)
		cyl(0.2 * s, W * 1.07, at(0, H * 0.75, 0), color2)
	elseif kind == "Cone" then
		cyl(0.25 * s, W, at(0, 0.12 * s, 0), color)
		cyl(H * 0.34, W * 0.66, at(0, H * 0.17 + 0.2 * s, 0), color)
		cyl(H * 0.2, W * 0.5, at(0, H * 0.5 + 0.1 * s, 0), color2)
		cyl(H * 0.32, W * 0.34, at(0, H * 0.82, 0), color)
	elseif kind == "Dumpster" then
		box(Vector3.new(W, H * 0.8, W * 0.55), at(0, H * 0.4, 0), color)
		box(Vector3.new(W * 1.04, H * 0.12, W * 0.6), at(0, H * 0.86, 0) * CFrame.Angles(0.06, 0, 0), color2)
	elseif kind == "Planter" then
		box(Vector3.new(W, H * 0.5, W * 0.55), at(0, H * 0.25, 0), color)
		ball(W * 0.5, -W * 0.22, H * 0.5 + W * 0.12, 0, color2)
		ball(W * 0.42, W * 0.22, H * 0.5 + W * 0.08, 0, shade(color2, random, 0.1))
	elseif kind == "Hydrant" then
		cyl(H * 0.1, W * 1.2, at(0, H * 0.05, 0), color2)
		cyl(H * 0.7, W, at(0, H * 0.4, 0), color)
		ball(W * 0.95, 0, H * 0.78, 0, color)
		for _, side in { -1, 1 } do
			cyl(W * 0.5, W * 0.35, along(side * W * 0.55, H * 0.5, 0), color)
		end
	elseif kind == "Cactus" then
		cyl(H, W, at(0, H / 2, 0), color)
		cyl(W * 1.6, W * 0.7, along(W * 0.9, H * 0.5, 0), color)
		cyl(H * 0.35, W * 0.7, at(W * 1.7, H * 0.5 + H * 0.15, 0), color)
		cyl(W * 1.2, W * 0.6, along(-W * 0.8, H * 0.35, 0), color)
		cyl(H * 0.25, W * 0.6, at(-W * 1.4, H * 0.35 + H * 0.1, 0), color)
	elseif kind == "Haystack" then
		cyl(H * 0.55, W, at(0, H * 0.275, 0), color)
		ball(W, 0, H * 0.55, 0, shade(color, random, 0.06))
	elseif kind == "Ball" then
		ball(W, 0, W / 2, 0, color)
		ball(W * 0.7, W * 0.12, W * 0.55, W * 0.05, shade(color, random, 0.15))
	elseif kind == "Rope" then
		cyl(H * 0.6, W, at(0, H * 0.3, 0), color)
		cyl(H * 0.5, W * 0.5, at(0, H * 0.7, 0), shade(color, random, 0.15))
	elseif kind == "Anchor" then
		cyl(H, W * 0.14, at(0, H / 2, 0), color)
		box(Vector3.new(W, W * 0.12, W * 0.12), at(0, H * 0.78, 0), color)
		for _, side in { -1, 1 } do
			box(
				Vector3.new(W * 0.5, W * 0.12, W * 0.12),
				at(side * W * 0.28, W * 0.14, 0) * CFrame.Angles(0, 0, -side * 0.6),
				color
			)
		end
	elseif kind == "Net" then
		box(Vector3.new(W, H, W * 0.65), at(0, H / 2, 0), color, 0.25)
		for _, side in { -1, 1 } do
			cyl(H * 4, 0.3 * s, at(side * W * 0.5, H * 2, W * 0.3), shade(color, random, 0.2))
		end
	elseif kind == "Bamboo" then
		for index = 1, 5 do
			local height = H * random:NextNumber(0.65, 1)
			local x, z = random:NextNumber(-0.4, 0.4) * W, random:NextNumber(-0.4, 0.4) * W
			local stalk = shade(color, random, 0.1)
			cyl(
				height,
				W * 0.12,
				CFrame.new(x, height / 2, z)
					* CFrame.Angles(random:NextNumber(-0.06, 0.06), 0, random:NextNumber(-0.06, 0.06)),
				stalk
			)
			if index <= 2 then
				ball(W * 0.38, x, height, z, shade(color, random, 0.15))
			end
		end
	elseif kind == "Lantern" then
		box(Vector3.new(W * 0.9, H * 0.1, W * 0.9), at(0, H * 0.05, 0), color)
		cyl(H * 0.4, W * 0.35, at(0, H * 0.3, 0), color)
		box(Vector3.new(W * 0.7, H * 0.2, W * 0.7), at(0, H * 0.6, 0), color2)
		box(Vector3.new(W * 1.2, H * 0.08, W * 1.2), at(0, H * 0.74, 0), color)
		ball(W * 0.3, 0, H * 0.82, 0, color)
	elseif kind == "Towel" then
		box(Vector3.new(W, 0.12, W * 0.6), at(0, 0.07, 0), color)
		for _, side in { -1, 1 } do
			box(Vector3.new(W, 0.14, W * 0.1), at(0, 0.08, side * W * 0.18), color2)
		end
	elseif kind == "Sandcastle" then
		box(Vector3.new(W, H * 0.45, W), at(0, H * 0.225, 0), color)
		for _, x in { -1, 1 } do
			for _, z in { -1, 1 } do
				cyl(H * 0.65, W * 0.28, at(x * W * 0.4, H * 0.325, z * W * 0.4), shade(color, random, 0.06))
			end
		end
		cyl(H * 0.5, W * 0.4, at(0, H * 0.45 + H * 0.25, 0), shade(color, random, 0.08))
	elseif kind == "Gnome" then
		cyl(H * 0.35, W * 0.7, at(0, H * 0.175, 0), color2)
		ball(W * 0.55, 0, H * 0.42, W * 0.1, Color3.fromRGB(245, 245, 245))
		cyl(H * 0.28, W * 0.5, at(0, H * 0.62, 0), color)
		cyl(H * 0.18, W * 0.25, at(0, H * 0.85, 0), color)
	elseif kind == "Tuft" or kind == "Blades" then
		local blades = if kind == "Tuft" then 3 else 5
		for index = 1, blades do
			local height = H * random:NextNumber(0.75, 1.1)
			local angle = index / blades * TAU
			local x, z = math.cos(angle) * W * 0.22, math.sin(angle) * W * 0.22
			local tiltX, tiltZ = random:NextNumber(-0.4, 0.4), random:NextNumber(-0.4, 0.4)
			box(
				Vector3.new(W * 0.16, height, W * 0.16),
				CFrame.new(x, height / 2 * 0.95, z) * CFrame.Angles(tiltX, 0, tiltZ),
				shade(color, random, 0.1)
			)
		end
	elseif kind == "FencePicket" then
		local length = spec.Length or W
		length = length * s
		local pickets = 6
		for index = 1, pickets do
			local x = -length / 2 + (index - 0.5) * length / pickets
			local height = H * (0.92 + 0.08 * random:NextNumber())
			box(Vector3.new(length / pickets * 0.55, height, 0.18), at(x, height / 2, 0), color)
		end
		for _, y in { 0.28, 0.68 } do
			box(Vector3.new(length, H * 0.09, 0.2), at(0, H * y, 0.17), shade(color, random, 0.04))
		end
		for _, side in { -1, 1 } do
			box(Vector3.new(0.3, H * 1.05, 0.3), at(side * length / 2, H * 0.525, 0.05), color)
		end
	elseif kind == "FenceChain" then
		local length = (spec.Length or W) * s
		for _, x in { -1, 0, 1 } do
			box(Vector3.new(0.25, H, 0.25), at(x * length / 2, H / 2, 0), color2)
		end
		box(Vector3.new(length, H * 0.82, 0.05), at(0, H * 0.46, 0), color, 0.55)
		box(Vector3.new(length, 0.2, 0.2), at(0, H, 0), color2)
	elseif kind == "FenceWood" then
		local length = (spec.Length or W) * s
		for _, x in { -1, 0, 1 } do
			box(
				Vector3.new(0.45, H * (1 - 0.05 * (x * x)), 0.45),
				at(x * length / 2, H / 2, 0),
				shade(color, random, 0.08)
			)
		end
		for _, y in { 0.4, 0.78 } do
			box(Vector3.new(length, H * 0.12, 0.25), at(0, H * y, 0.2), color)
		end
	elseif kind == "FenceLow" then
		local length = (spec.Length or W) * s
		for _, side in { -1, 1 } do
			box(Vector3.new(0.35, H, 0.35), at(side * length / 2, H / 2, 0), color)
		end
		for _, y in { 0.45, 0.82 } do
			box(Vector3.new(length, H * 0.16, 0.25), at(0, H * y, 0.1), shade(color, random, 0.05))
		end
	elseif kind == "FenceShield" then
		local length = (spec.Length or W) * s
		for _, x in { -1, 0, 1 } do
			box(Vector3.new(0.45, H, 0.45), at(x * length / 2, H / 2, 0), color)
		end
		box(Vector3.new(length, H * 0.25, 0.2), at(0, H * 0.35, 0.1), shade(color, random, 0.05))
		for index = 1, 3 do
			local x = -length / 2 + (index - 0.5) * length / 3
			local shield = if index % 2 == 1 then color2 else Color3.fromRGB(235, 225, 195)
			cyl(0.2, H * 0.52, at(x, H * 0.72, 0.25) * CFrame.Angles(math.pi / 2, 0, 0), shield)
		end
	else
		ball(W, 0, W / 2, 0, color)
	end
	return model
end

-- ==== models ===========================================================================================================

-- Per prop name: the scale that fits the model to its nominal size and the offset that puts its bottom centre at the origin.
type Fit = { Scale: number, Offset: Vector3 }
local fits: { [string]: Fit } = {}

local function modelProp(name: string, spec: Prop, base: CFrame, scale: number): Model?
	local assetName = `Scatter_{name}`
	if not Assets.Has(assetName) then
		return nil
	end
	local fit = fits[name]
	if not fit then
		local probe = Assets.CloneModel(assetName)
		if not probe then
			return nil
		end
		probe:PivotTo(CFrame.new())
		local _, extents = probe:GetBoundingBox()
		local mode = spec.Fit or "Height"
		local current = if mode == "Length"
			then extents.X
			elseif mode == "Width" then math.max(extents.X, extents.Z)
			else extents.Y
		local target = if mode == "Length"
			then spec.Length or spec.Width
			elseif mode == "Width" then spec.Width
			else spec.Height
		if current > 0 then
			probe:ScaleTo(probe:GetScale() * target / current)
		end
		probe:PivotTo(CFrame.new())
		local box, size = probe:GetBoundingBox()
		fit = {
			Scale = probe:GetScale(),
			Offset = Vector3.new(-box.Position.X, -(box.Position.Y - size.Y / 2), -box.Position.Z),
		}
		probe:Destroy()
		fits[name] = fit
	end
	local model = Assets.CloneModel(assetName)
	if not model or not fit then
		return nil
	end
	Assets.MakeVisualOnly(model, true)
	local shadows = spec.Height * scale >= 6
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.Material = flat(descendant.Material)
			descendant.CastShadow = shadows
		end
	end
	model:ScaleTo(fit.Scale * scale)
	model:PivotTo(base * CFrame.new(fit.Offset * scale))
	return model
end

-- ==== the build ========================================================================================================

local function weightedPick(random: Random, entries: Entries?): string?
	if not entries then
		return nil
	end
	local names: { string } = {}
	local total = 0
	for name, weight in entries do
		if weight > 0 and Config.Props[name] then
			table.insert(names, name)
			total += weight
		end
	end
	if #names == 0 then
		return nil
	end
	table.sort(names)
	local roll = random:NextNumber() * total
	for _, name in names do
		roll -= entries[name]
		if roll <= 0 then
			return name
		end
	end
	return names[#names]
end

local CLUSTER_KINDS = { "Trees", "Bushes", "Rocks", "Flowers", "Misc" }
local CLUSTER_WEIGHT: { [string]: number } = { Trees = 4, Bushes = 2.5, Rocks = 2, Flowers = 1.5, Misc = 2 }

function StageScatter.Build(params: Params): Folder
	local bay = params.Bay
	local frame = params.Frame
	local theme = TycoonDecor.Themes[bay]
	local area = StreetLayout.AreaOf(bay)
	local depth = StreetLayout.Compute().Depths[bay]
	local path = StageScatter.PathFor(bay)
	local biome = Config.Biomes[bay] or Config.Default
	local random = Random.new(params.Slot * 100003 + bay * 7919 + 13)
	local halfX = Config.MaxHalfWidth
	local halfZ = depth / 2 - 2
	local halfPath = LAYOUT.PathWidth / 2 * (1 + WIDTH_VARIATION)

	local folder = Instance.new("Folder")
	folder.Name = `Scatter{bay}`

	-- Where the Shiba stands and the zone in front of it (the Intern's spot is inside it), in the stage frame.
	local spot = if theme and theme.Shiba then theme.Shiba else nil
	local shibaPosition = (if spot then spot.Position else Vector2.new(-LAYOUT.ShibaX, 0)) * STAGE_SCALE
	local facing = math.rad(if spot then spot.Facing else 0)
	local shibaZoneEnd = shibaPosition + Vector2.new(math.cos(facing), -math.sin(facing)) * Config.ShibaZoneLength
	local rects = footprints(theme)
	local pads = params.Pads

	local placed: { { X: number, Z: number, R: number } } = {}
	local count = 0

	-- Room for a prop of radius r at (x, z): inside the stage, off the path (`pathMin`), the pads, the Shiba zone and the
	-- theme's solid pieces.
	local function openGround(x: number, z: number, r: number, pathMin: number): boolean
		if math.abs(x) > halfX - r or math.abs(z) > halfZ - r then
			return false
		end
		if distanceToPath(path, x, z) < pathMin then
			return false
		end
		local padReach = Config.PadClear + r * 0.5
		for _, pad in pads do
			local dx, dz = x - pad.X, z - pad.Y
			if dx * dx + dz * dz < padReach * padReach then
				return false
			end
		end
		if distanceToSegment(shibaPosition, shibaZoneEnd, x, z) < Config.ShibaClear + r * 0.5 then
			return false
		end
		local margin = Config.SolidMargin + r * 0.5
		for _, rect in rects do
			local dx, dz = x - rect.X, z - rect.Z
			local localX = dx * rect.Cos - dz * rect.Sin
			local localZ = dx * rect.Sin + dz * rect.Cos
			if math.abs(localX) <= rect.HX + margin and math.abs(localZ) <= rect.HZ + margin then
				return false
			end
		end
		return true
	end

	-- Not on top of another prop (`overlap` < 1 lets the edges of a cluster touch).
	local function roomFor(x: number, z: number, r: number, overlap: number): boolean
		for _, other in placed do
			local least = (r + other.R) * overlap
			local dx, dz = x - other.X, z - other.Z
			if dx * dx + dz * dz < least * least then
				return false
			end
		end
		return true
	end

	local function addColliders(model: Model, spec: Prop, base: CFrame, scale: number)
		local height = spec.Height * scale
		local function collider(name: string, size: Vector3, at: CFrame, shape: Enum.PartType)
			local part = Instance.new("Part")
			part.Name = name
			part.Anchored = true
			part.CanCollide = true
			part.CanQuery = false
			part.CanTouch = false
			part.CastShadow = false
			part.Transparency = 1
			part.Size = size
			part.CFrame = at
			part.Shape = shape
			part.Parent = model
		end
		if spec.Collide == "Trunk" and height >= 8 then
			local d = (spec.Trunk or 1.5) * scale
			collider("Trunk", Vector3.new(d, 6, d), base * CFrame.new(0, 3, 0), Enum.PartType.Block)
		elseif spec.Collide == "Boulder" and height > 4 then
			local d = math.min(spec.Width * scale, height * 1.4) * 0.8
			collider("Boulder", Vector3.new(d, d, d), base * CFrame.new(0, d * 0.45, 0), Enum.PartType.Ball)
		end
	end

	-- Puts one prop on the ground at (x, z), turned `yaw` radians (about the vertical axis, stage frame), at `scale`.
	local function place(
		name: string,
		x: number,
		z: number,
		yaw: number,
		scale: number,
		registerRadius: number?
	): boolean
		local spec = Config.Props[name]
		if not spec or count >= Config.MaxProps then
			return false
		end
		local tilt = spec.Tilt or 0
		local tiltX = if tilt > 0 then math.rad(random:NextNumber(-tilt, tilt)) else 0
		local tiltZ = if tilt > 0 then math.rad(random:NextNumber(-tilt, tilt)) else 0
		local sink = if tilt > 0 and spec.Length == nil then 0.12 * spec.Height * scale else 0
		local base = frame * CFrame.new(x, -sink, z) * CFrame.Angles(0, yaw, 0) * CFrame.Angles(tiltX, 0, tiltZ)
		local model = modelProp(name, spec, base, scale) or buildFallback(spec, base, scale, random)
		model.Name = name
		addColliders(model, spec, base, scale)
		model.Parent = folder
		count += 1
		table.insert(placed, { X = x, Z = z, R = registerRadius or spec.Width * scale / 2 })
		return true
	end

	-- A prop at a random yaw, if there is room.
	local function tryProp(
		name: string?,
		x: number,
		z: number,
		scaleMin: number,
		scaleMax: number,
		pathMin: number?,
		overlap: number?
	): boolean
		local spec = if name then Config.Props[name] else nil
		if not name or not spec then
			return false
		end
		local scale = random:NextNumber(scaleMin, scaleMax)
		local r = spec.Width * scale / 2
		local keepOff = pathMin or (Config.PathClear + r * 0.6)
		if not openGround(x, z, r, keepOff) or not roomFor(x, z, r, overlap or 0.8) then
			return false
		end
		return place(name, x, z, random:NextNumber(0, TAU), scale)
	end

	local density = biome.Density

	-- ---- fence rows along both sides of the path ----
	local style = biome.Fence
	local fenceSpec = if style then Config.Props[style.Name] else nil
	if style and fenceSpec then
		local length = fenceSpec.Length or 6
		for _, side in { -1, 1 } do
			if random:NextNumber() > 0.15 * (2 - density) then
				local s = random:NextNumber(6, 14)
				local function offsetPoint(at: number): Vector2
					local position, tangent = pathFrame(path, at)
					local normal = Vector2.new(-tangent.Y, tangent.X) * side
					local off = halfPath + style.Offset + 0.7 * math.sin(at * 0.11 + side * 2)
					return position + normal * off
				end
				while s + length < path.Length - 6 do
					local run = random:NextInteger(3, 7)
					for _ = 1, run do
						if s + length >= path.Length - 6 then
							break
						end
						local a, b = offsetPoint(s), offsetPoint(s + length)
						local middle = (a + b) / 2
						local chord = b - a
						if chord.Magnitude > 1 then
							local yaw = math.atan2(-chord.Y, chord.X) + math.rad(random:NextNumber(-4, 4))
							local roomy = openGround(middle.X, middle.Y, 0.5, Config.PathClear)
								and openGround(a.X, a.Y, 0.5, Config.PathClear)
								and openGround(b.X, b.Y, 0.5, Config.PathClear)
							if roomy then
								place(style.Name, middle.X, middle.Y, yaw, chord.Magnitude / length, 1.5)
							end
						end
						s += length
					end
					if style.Coverage < 0.98 then
						local gap = run
							* (1 - style.Coverage)
							/ math.max(style.Coverage, 0.05)
							* random:NextNumber(0.6, 1.4)
						s += length * math.max(1, math.floor(gap + 0.5)) * random:NextNumber(0.85, 1.15)
					end
				end
			end
		end
	end

	-- ---- clusters in the empty areas ----
	local weights: { number } = {}
	local totalWeight = 0
	for index, kind in CLUSTER_KINDS do
		local entries = (biome :: any)[kind] :: Entries?
		local weight = 0
		if entries and next(entries) ~= nil then
			local mix = if biome.Mix then (biome.Mix :: any)[kind] else nil
			weight = if type(mix) == "number" then mix else CLUSTER_WEIGHT[kind]
		end
		weights[index] = weight
		totalWeight += weight
	end
	local function pickKind(): string?
		if totalWeight <= 0 then
			return nil
		end
		local roll = random:NextNumber() * totalWeight
		for index, kind in CLUSTER_KINDS do
			roll -= weights[index]
			if roll <= 0 and weights[index] > 0 then
				return kind
			end
		end
		return nil
	end
	local function entriesOf(kind: string): Entries?
		return (biome :: any)[kind] :: Entries?
	end
	local function member(kind: string, cx: number, cz: number, spread: number, scaleMin: number?, scaleMax: number?)
		local angle = random:NextNumber(0, TAU)
		local dist = random:NextNumber(0.15, 1) * spread
		tryProp(
			weightedPick(random, entriesOf(kind)),
			cx + math.cos(angle) * dist,
			cz + math.sin(angle) * dist,
			scaleMin or Config.ScaleMin,
			scaleMax or Config.ScaleMax,
			nil,
			0.55
		)
	end
	local function tufts(cx: number, cz: number, spread: number, amount: number)
		for _ = 1, amount do
			local angle = random:NextNumber(0, TAU)
			local dist = random:NextNumber(0.3, 1) * spread
			tryProp(biome.Cover, cx + math.cos(angle) * dist, cz + math.sin(angle) * dist, 0.9, 1.5, nil, 0.5)
		end
	end
	local function cluster(kind: string, cx: number, cz: number)
		if kind == "Trees" then
			for _ = 1, random:NextInteger(1, 2) do
				member("Trees", cx, cz, 5)
			end
			for _ = 1, random:NextInteger(1, 3) do
				member("Bushes", cx, cz, 9)
			end
			if random:NextNumber() < 0.4 then
				member("Rocks", cx, cz, 9, 0.6, 1.1)
			end
			if random:NextNumber() < 0.4 then
				member("Flowers", cx, cz, 9)
			end
			tufts(cx, cz, 10, random:NextInteger(1, 3))
		elseif kind == "Rocks" then
			member("Rocks", cx, cz, 2)
			for _ = 1, random:NextInteger(1, 3) do
				member("Rocks", cx, cz, 7, 0.5, 1)
			end
			tufts(cx, cz, 8, random:NextInteger(1, 3))
		elseif kind == "Bushes" then
			for _ = 1, random:NextInteger(2, 4) do
				member("Bushes", cx, cz, 6)
			end
			if random:NextNumber() < 0.6 then
				member("Flowers", cx, cz, 7)
			end
			tufts(cx, cz, 8, random:NextInteger(0, 2))
		elseif kind == "Flowers" then
			for _ = 1, random:NextInteger(2, 4) do
				member("Flowers", cx, cz, 6)
			end
			tufts(cx, cz, 8, random:NextInteger(1, 3))
		else
			for _ = 1, random:NextInteger(1, 2) do
				member("Misc", cx, cz, 4)
			end
			if random:NextNumber() < 0.5 then
				member("Bushes", cx, cz, 8)
			end
			if random:NextNumber() < 0.5 then
				member("Rocks", cx, cz, 8, 0.6, 1.1)
			end
			tufts(cx, cz, 8, random:NextInteger(1, 2))
		end
	end

	local centres: { Vector2 } = {}
	local wanted = math.max(1, math.round(Config.Clusters * density * random:NextNumber(0.85, 1.15)))
	for _ = 1, wanted do
		for _ = 1, 60 do
			local x: number, z: number
			if random:NextNumber() < 0.45 then
				-- Composed with the path: a group a little off its edge.
				local position, tangent = pathFrame(path, random:NextNumber(4, path.Length - 4))
				local side = if random:NextNumber() < 0.5 then -1 else 1
				local off = halfPath + random:NextNumber(4, 16)
				x = position.X - tangent.Y * side * off
				z = position.Y + tangent.X * side * off
			else
				x = random:NextNumber(-halfX + 6, halfX - 6)
				z = random:NextNumber(-halfZ + 6, halfZ - 6)
			end
			local apart = true
			for _, other in centres do
				local dx, dz = x - other.X, z - other.Y
				if dx * dx + dz * dz < Config.ClusterSpacing * Config.ClusterSpacing then
					apart = false
					break
				end
			end
			if apart and openGround(x, z, 3, Config.PathClear + 2) then
				table.insert(centres, Vector2.new(x, z))
				local kind = pickKind()
				if kind then
					cluster(kind, x, z)
				end
				break
			end
		end
	end

	-- ---- the border of the theme's Area: tufts, small rocks and shrubs so the floor's straight edge is broken up ----
	local areaX, areaZ = area.X / 2, area.Y / 2
	for _ = 1, math.round(Config.EdgeProps * density) do
		local w, h = areaX * 2, areaZ * 2
		local t = random:NextNumber() * 2 * (w + h)
		local x: number, z: number
		if t < w then
			x, z = -areaX + t, -areaZ
		elseif t < w + h then
			x, z = areaX, -areaZ + (t - w)
		elseif t < 2 * w + h then
			x, z = areaX - (t - w - h), areaZ
		else
			x, z = -areaX, areaZ - (t - 2 * w - h)
		end
		x += random:NextNumber(-3, 3)
		z += random:NextNumber(-3, 3)
		local roll = random:NextNumber()
		if roll < 0.6 then
			tryProp(biome.Cover, x, z, 0.9, 1.5, Config.PathClear - 0.5, 0.5)
			tryProp(
				biome.Cover,
				x + random:NextNumber(-2, 2),
				z + random:NextNumber(-2, 2),
				0.8,
				1.3,
				Config.PathClear - 0.5,
				0.5
			)
		elseif roll < 0.8 then
			tryProp(weightedPick(random, biome.Rocks), x, z, 0.5, 0.95, nil, 0.6)
		else
			tryProp(weightedPick(random, biome.Bushes or biome.Flowers), x, z, 0.7, 1.1, nil, 0.6)
		end
	end

	-- ---- along the path's edges: tufts, pebbles, a flower now and then ----
	for _ = 1, math.round(Config.PathEdgeProps * density) do
		local position, tangent = pathFrame(path, random:NextNumber(4, path.Length - 4))
		local side = if random:NextNumber() < 0.5 then -1 else 1
		local off = halfPath + random:NextNumber(0.6, 3.2)
		local x = position.X - tangent.Y * side * off
		local z = position.Y + tangent.X * side * off
		local roll = random:NextNumber()
		if roll < 0.65 then
			tryProp(biome.Cover, x, z, 0.8, 1.4, halfPath + 0.3, 0.5)
		elseif roll < 0.88 then
			tryProp(weightedPick(random, biome.Rocks), x, z, 0.35, 0.6, halfPath + 0.3, 0.6)
		else
			tryProp(weightedPick(random, biome.Flowers or biome.Bushes), x, z, 0.5, 0.8, halfPath + 0.6, 0.6)
		end
	end

	folder.Parent = params.Parent
	return folder
end

return StageScatter
