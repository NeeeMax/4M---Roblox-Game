--!strict
-- Shiba themes for bays 11 to 20 (see Config/DecorTypes for the schema and the stage frame). Keyed by the bay number.
-- Pure data built from primitives. Small helpers at the top keep the part lists short:
--   box / cyl / ball / wedge / hcyl / blk build one Piece; cat joins pieces and lists of pieces; P is one decor part.
-- Bays 11 to 14 have 20 parts, bays 15 to 20 have 25 parts. Parts 1 and 2 are the foundation (flooring, walls or main body),
-- part 3 the "Get Bonked" sign, the last part is the showpiece. Layout rule used everywhere: the main landmark stands on the
-- right of the path (X > 7) deep in the plot (negative Z); the path |X| < 7 only carries flush flooring; the area X -25..-1,
-- |Z| < 9 around the Shiba and the Intern stays empty.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Part = DecorTypes.Part
type Theme = DecorTypes.Theme

local V3, RGB = Vector3.new, Color3.fromRGB
local MT = Enum.Material
local PT = Enum.PartType

-- One piece from its centre (x, y, z) and size.
local function mk(
	shape: Enum.PartType,
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?,
	rot: Vector3?
): Piece
	return {
		Size = V3(sx, sy, sz),
		Offset = V3(x, y, z),
		Color = color,
		Material = material,
		Shape = shape,
		Rotation = rot,
	}
end

-- Block with its centre y given (floating or rotated pieces).
local function blk(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	c: Color3,
	m: Enum.Material?,
	rot: Vector3?
): Piece
	return mk(PT.Block, x, y, z, sx, sy, sz, c, m, rot)
end

-- Block standing on y0 (default: the ground): footprint centre (x, z), width w (X), height h, depth d (Z).
local function box(
	x: number,
	z: number,
	w: number,
	h: number,
	d: number,
	c: Color3,
	m: Enum.Material?,
	y0: number?
): Piece
	return mk(PT.Block, x, (y0 or 0) + h / 2, z, w, h, d, c, m, nil)
end

-- Upright cylinder standing on y0.
local function cyl(x: number, z: number, dia: number, h: number, c: Color3, m: Enum.Material?, y0: number?): Piece
	return mk(PT.Cylinder, x, (y0 or 0) + h / 2, z, h, dia, dia, c, m, V3(0, 0, 90))
end

-- Lying cylinder with its centre (x, y, z); axis "X" or "Z".
local function hcyl(
	x: number,
	y: number,
	z: number,
	len: number,
	dia: number,
	axis: string,
	c: Color3,
	m: Enum.Material?
): Piece
	return mk(PT.Cylinder, x, y, z, len, dia, dia, c, m, if axis == "Z" then V3(0, 90, 0) else nil)
end

-- Ball standing (resting) on y0.
local function ball(x: number, z: number, d: number, c: Color3, m: Enum.Material?, y0: number?): Piece
	return mk(PT.Ball, x, (y0 or 0) + d / 2, z, d, d, d, c, m, nil)
end

-- Wedge standing on y0, turned by yaw degrees.
local function wedge(
	x: number,
	z: number,
	w: number,
	h: number,
	d: number,
	c: Color3,
	m: Enum.Material?,
	y0: number?,
	yaw: number?
): Piece
	return mk(PT.Wedge, x, (y0 or 0) + h / 2, z, w, h, d, c, m, if yaw then V3(0, yaw, 0) else nil)
end

-- Joins pieces and lists of pieces into one list.
local function cat(...: any): { Piece }
	local out: { Piece } = {}
	for _, item in { ... } do
		if item.Size then
			table.insert(out, item)
		else
			for _, piece in item do
				table.insert(out, piece)
			end
		end
	end
	return out
end

-- make(x, z, i) for n points on a line from (x0, z0) to (x1, z1).
local function line(
	n: number,
	x0: number,
	z0: number,
	x1: number,
	z1: number,
	make: (number, number, number) -> any
): { Piece }
	local out: { any } = {}
	for i = 0, n - 1 do
		local t = if n > 1 then i / (n - 1) else 0
		table.insert(out, make(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, i + 1))
	end
	return cat(table.unpack(out))
end

-- make(x, z, angle) for n points on a circle of radius r around (cx, cz); angle in degrees.
local function ring(n: number, cx: number, cz: number, r: number, make: (number, number, number) -> any): { Piece }
	local out: { any } = {}
	for i = 0, n - 1 do
		local a = i / n * 2 * math.pi
		table.insert(out, make(cx + r * math.cos(a), cz + r * math.sin(a), math.deg(a)))
	end
	return cat(table.unpack(out))
end

-- make(x, z, i) for every {x, z} of a list of points.
local function each(points: { { number } }, make: (number, number, number) -> any): { Piece }
	local out: { any } = {}
	for i, p in points do
		table.insert(out, make(p[1], p[2], i))
	end
	return cat(table.unpack(out))
end

-- The two thin ground slabs left and right of the path (the path |X| < 7 stays free), over the whole stage.
local function floorSlabs(half: number, cl: Color3, ml: Enum.Material?, cr: Color3, mr: Enum.Material?): { Piece }
	local w = half - 7
	local x = (half + 7) / 2
	return { blk(-x, 0.1, 0, w, 0.2, half * 2, cl, ml), blk(x, 0.1, 0, w, 0.2, half * 2, cr, mr) }
end

-- A very thin coloured patch lying on the floor slabs.
local function inlay(x: number, z: number, w: number, d: number, c: Color3, m: Enum.Material?): Piece
	return blk(x, 0.25, z, w, 0.1, d, c, m)
end

-- The "Get Bonked" sign: a board on two posts with neon trim and a lettering band, facing the road (+Z).
local function sign(x: number, z: number, w: number, board: Color3, trim: Color3, post: Color3): { Piece }
	return {
		box(x - w / 2 + 1, z, 0.9, 9, 0.9, post, MT.Wood),
		box(x + w / 2 - 1, z, 0.9, 9, 0.9, post, MT.Wood),
		box(x, z, w, 4.5, 0.6, board, MT.SmoothPlastic, 7),
		box(x, z + 0.4, w + 0.6, 0.5, 0.5, trim, MT.Neon, 11.5),
		box(x, z + 0.4, w + 0.6, 0.5, 0.5, trim, MT.Neon, 6.6),
		box(x, z + 0.35, w * 0.7, 2, 0.3, trim, MT.Neon, 8.2),
	}
end

-- A round tree: trunk and a ball of leaves.
local function tree(x: number, z: number, h: number, leaf: Color3, trunk: Color3): { Piece }
	return { cyl(x, z, 1.2, h * 0.5, trunk, MT.Wood), ball(x, z, h * 0.75, leaf, MT.Grass, h * 0.3) }
end

-- A pine tree: trunk and three shrinking discs of needles.
local function pine(x: number, z: number, h: number, leaf: Color3): { Piece }
	return {
		cyl(x, z, 1, h * 0.3, RGB(95, 65, 40), MT.Wood),
		cyl(x, z, h * 0.5, h * 0.3, leaf, MT.Grass, h * 0.2),
		cyl(x, z, h * 0.36, h * 0.3, leaf, MT.Grass, h * 0.42),
		cyl(x, z, h * 0.2, h * 0.3, leaf, MT.Grass, h * 0.64),
	}
end

-- A lamp post with a glowing ball on top.
local function lamp(x: number, z: number, h: number, glow: Color3, pole: Color3): { Piece }
	return { cyl(x, z, 0.5, h, pole, MT.Metal), ball(x, z, 1.6, glow, MT.Neon, h) }
end

-- A simple person made of blocks (s = scale, about 5.4 * s tall).
local function person(x: number, z: number, s: number, body: Color3, legs: Color3, skin: Color3): { Piece }
	return {
		box(x, z, 1.4 * s, 2 * s, 0.8 * s, legs, MT.Fabric),
		box(x, z, 1.8 * s, 2 * s, 1 * s, body, MT.Fabric, 2 * s),
		box(x, z, 0.7 * s, 0.6 * s, 3 * s, body, MT.Fabric, 3 * s),
		ball(x, z, 1.4 * s, skin, MT.SmoothPlastic, 4 * s),
	}
end

-- A fence along X from x0 to x1 at depth z: two rails and a post about every 4 studs.
local function fence(x0: number, x1: number, z: number, c: Color3, m: Enum.Material?): { Piece }
	local out: { Piece } = {
		box((x0 + x1) / 2, z, x1 - x0, 0.4, 0.4, c, m, 1.9),
		box((x0 + x1) / 2, z, x1 - x0, 0.4, 0.4, c, m, 0.9),
	}
	local n = math.max(2, math.floor((x1 - x0) / 4) + 1)
	for i = 0, n - 1 do
		table.insert(out, box(x0 + (x1 - x0) * i / (n - 1), z, 0.6, 2.6, 0.6, c, m))
	end
	return out
end

-- A small car (6 long along X, 3 wide), nose toward +X. 9 pieces.
local function car(x: number, z: number, body: Color3, roof: Color3, glass: Color3): { Piece }
	return {
		box(x, z, 6, 1.2, 3, body, MT.Metal, 0.6),
		box(x - 0.4, z, 3.2, 1.2, 2.8, glass, MT.Glass, 1.8),
		box(x - 0.4, z, 3.4, 0.3, 3, roof, MT.Metal, 3),
		hcyl(x - 2, 0.7, z - 1.6, 0.6, 1.4, "Z", RGB(30, 30, 35), MT.Metal),
		hcyl(x + 2, 0.7, z - 1.6, 0.6, 1.4, "Z", RGB(30, 30, 35), MT.Metal),
		hcyl(x - 2, 0.7, z + 1.6, 0.6, 1.4, "Z", RGB(30, 30, 35), MT.Metal),
		hcyl(x + 2, 0.7, z + 1.6, 0.6, 1.4, "Z", RGB(30, 30, 35), MT.Metal),
		box(x + 3, z - 1, 0.2, 0.5, 0.7, RGB(255, 245, 190), MT.Neon, 1),
		box(x + 3, z + 1, 0.2, 0.5, 0.7, RGB(255, 245, 190), MT.Neon, 1),
	}
end

-- A round fountain of radius r: basin, water, a pillar with a bowl and a water jet. 5 pieces.
local function fountain(x: number, z: number, r: number, water: Color3, stone: Color3): { Piece }
	return {
		cyl(x, z, r * 2, 1.2, stone, MT.Marble),
		cyl(x, z, r * 2 - 1.2, 0.2, water, MT.Glass, 1.1),
		cyl(x, z, 1.2, 4, stone, MT.Marble, 1.2),
		cyl(x, z, 3.4, 0.6, stone, MT.Marble, 4.2),
		ball(x, z, 1.4, water, MT.Neon, 4.8),
	}
end

local function P(id: string, name: string, description: string, pieces: { Piece }): Part
	return { Id = id, Name = name, Description = description, PriceSeconds = 0, Pieces = pieces }
end

-- Assembles a theme: the stage is 2 * half studs wide and deep; PriceSeconds rise from 10 (part 1) to lastPrice (last part).
local function build(key: string, name: string, half: number, lastPrice: number, parts: { Part }): Theme
	local count = #parts
	for index, part in parts do
		local price = 10 * (lastPrice / 10) ^ ((index - 1) / (count - 1))
		part.PriceSeconds = math.floor(price / 5 + 0.5) * 5
	end
	return { Key = key, Name = name, Area = Vector2.new(half * 2, half * 2), Parts = parts }
end

local themes: { [number]: Theme } = {}

-- 11 Knight Shiba: Castle. Courtyard x 12..48, z -48..-12 with the gate facing the path.
do
	local h = 54
	local stone, dark = RGB(172, 176, 185), RGB(105, 110, 124)
	local blue, silver, gold = RGB(45, 90, 200), RGB(222, 226, 236), RGB(250, 200, 60)
	local wood, red, water = RGB(120, 80, 45), RGB(185, 40, 50), RGB(70, 150, 225)
	local glow = RGB(255, 170, 50)
	local function merlon(x: number, z: number, y: number): Piece
		return box(x, z, 2.5, 2, 2.2, stone, MT.Cobblestone, y)
	end
	local function dummy(x: number, z: number): { Piece }
		return {
			cyl(x, z, 0.6, 4, wood, MT.Wood),
			box(x, z, 0.5, 0.5, 3, wood, MT.Wood, 3),
			ball(x, z, 1.4, RGB(220, 190, 110), MT.Fabric, 4),
		}
	end
	local function knight(x: number, z: number): { Piece }
		return {
			box(x, z, 2.4, 1.2, 2.4, dark, MT.Slate),
			box(x, z, 1.4, 2.2, 0.9, silver, MT.Metal, 1.2),
			box(x, z, 1.9, 2.2, 1.1, silver, MT.Metal, 3.4),
			ball(x, z, 1.3, silver, MT.Metal, 5.6),
			box(x + 1.3, z, 0.3, 3.5, 0.2, silver, MT.Metal, 3.6),
			box(x - 1.1, z, 0.3, 1.8, 1.4, blue, MT.Metal, 3.6),
		}
	end
	local towers = { { 12, -12 }, { 48, -12 }, { 12, -48 }, { 48, -48 } }
	themes[11] = build("KnightCastle", "Castle", h, 700, {
		P(
			"Flooring",
			"Castle Flooring",
			"Lawn outside, flagstone courtyard and a red carpet inside the walls.",
			cat(
				floorSlabs(h, RGB(90, 150, 70), MT.Grass, RGB(135, 140, 150), MT.Slate),
				inlay(30, -30, 36, 36, RGB(188, 191, 199), MT.Cobblestone),
				inlay(30, -30, 3, 36, red, MT.Fabric),
				inlay(-38, -30, 10, 8, RGB(235, 120, 165), MT.Grass),
				inlay(-38, 30, 10, 8, RGB(250, 215, 80), MT.Grass)
			)
		),
		P(
			"Walls",
			"Curtain Walls",
			"Thick grey stone walls around the courtyard, with a gate gap facing the path.",
			cat(
				box(30, -48, 38, 10, 2, stone, MT.Cobblestone),
				box(48, -30, 2, 10, 36, stone, MT.Cobblestone),
				box(30, -12, 38, 10, 2, stone, MT.Cobblestone),
				box(12, -42.5, 2, 10, 11, stone, MT.Cobblestone),
				box(12, -19.5, 2, 10, 15, stone, MT.Cobblestone)
			)
		),
		P("Sign", "Get Bonked Sign", "A blue and silver board on wooden posts.", sign(26, 43, 16, blue, silver, wood)),
		P(
			"Gatehouse",
			"Gatehouse",
			"Two stout towers and a raised portcullis around the gate.",
			cat(
				box(12, -38, 6, 14, 6, stone, MT.Cobblestone),
				box(12, -26, 6, 14, 6, stone, MT.Cobblestone),
				box(12, -32, 5, 3.5, 6, dark, MT.Slate, 7.5),
				line(3, 12, -33.2, 12, -30.8, function(x, z)
					return box(x, z, 0.4, 3.5, 0.4, dark, MT.Metal, 4)
				end),
				box(12, -38, 7.2, 1.2, 7.2, dark, MT.Slate, 14),
				box(12, -26, 7.2, 1.2, 7.2, dark, MT.Slate, 14)
			)
		),
		P(
			"CornerTowers",
			"Corner Towers",
			"Four round towers with blue roofs.",
			each(towers, function(x, z)
				return {
					cyl(x, z, 7, 16, stone, MT.Cobblestone),
					cyl(x, z, 8.4, 1, dark, MT.Slate, 16),
					cyl(x, z, 4.4, 3, blue, MT.Slate, 17),
				}
			end)
		),
		P(
			"Battlements",
			"Battlements",
			"Stone teeth along the back and side walls.",
			cat(
				line(7, 15, -48, 45, -48, function(x, z)
					return merlon(x, z, 10)
				end),
				line(6, 48, -44, 48, -16, function(x, z)
					return merlon(x, z, 10)
				end)
			)
		),
		P(
			"Banners",
			"Blue Banners",
			"Four blue banners with silver emblems on the front wall.",
			line(4, 18, -10.8, 42, -10.8, function(x, z)
				return {
					box(x, z, 3, 7, 0.3, blue, MT.Fabric, 2),
					blk(x, 5.2, z + 0.25, 1.2, 1.2, 0.2, silver, MT.Metal, V3(0, 0, 45)),
				}
			end)
		),
		P(
			"Moat",
			"Moat",
			"Water in front of and behind the castle, with lily pads.",
			cat(
				box(8.75, -30, 2.5, 0.4, 40, water, MT.Glass),
				box(30, -50, 40, 0.4, 2, water, MT.Glass),
				box(50, -30, 2, 0.4, 38, water, MT.Glass),
				cyl(8.2, -44, 1.4, 0.1, RGB(60, 150, 70), MT.Grass, 0.4),
				cyl(9.3, -40, 1.4, 0.1, RGB(60, 150, 70), MT.Grass, 0.4),
				cyl(8.4, -22, 1.4, 0.1, RGB(60, 150, 70), MT.Grass, 0.4),
				cyl(9.2, -16, 1.4, 0.1, RGB(60, 150, 70), MT.Grass, 0.4)
			)
		),
		P(
			"Drawbridge",
			"Drawbridge",
			"A wooden bridge over the moat, held by chains.",
			cat(
				box(9.75, -32, 4.5, 0.3, 5.6, wood, MT.WoodPlanks, 0.4),
				box(9.75, -34.9, 4.5, 0.8, 0.3, wood, MT.Wood, 0.7),
				box(9.75, -29.1, 4.5, 0.8, 0.3, wood, MT.Wood, 0.7),
				cyl(7.8, -35.5, 0.6, 5, dark, MT.Metal, 0.4),
				cyl(7.8, -28.5, 0.6, 5, dark, MT.Metal, 0.4),
				blk(9.9, 3.5, -35.2, 4.6, 0.25, 0.25, dark, MT.Metal, V3(0, 0, -50)),
				blk(9.9, 3.5, -28.8, 4.6, 0.25, 0.25, dark, MT.Metal, V3(0, 0, -50))
			)
		),
		P(
			"Torches",
			"Courtyard Torches",
			"Six glowing torches around the courtyard.",
			each({ { 24, -16 }, { 36, -16 }, { 24, -44 }, { 36, -44 }, { 16, -26 }, { 44, -26 } }, function(x, z)
				return lamp(x, z, 5, glow, dark)
			end)
		),
		P(
			"TrainingYard",
			"Training Yard",
			"Two straw dummies and an archery target.",
			cat(
				dummy(17, -42),
				dummy(17, -37),
				hcyl(22, 3, -44, 0.6, 4, "X", red, MT.Fabric),
				hcyl(22.2, 3, -44, 0.6, 2.6, "X", silver, MT.Fabric),
				hcyl(22.4, 3, -44, 0.6, 1.2, "X", gold, MT.Fabric),
				box(22, -45.6, 0.5, 2, 0.5, wood, MT.Wood),
				box(22, -42.4, 0.5, 2, 0.5, wood, MT.Wood)
			)
		),
		P(
			"Armory",
			"Armory Rack",
			"A weapon rack with swords and three shields.",
			cat(
				box(15.5, -18, 0.5, 4, 0.5, wood, MT.Wood),
				box(20.5, -18, 0.5, 4, 0.5, wood, MT.Wood),
				box(18, -18, 5.5, 0.5, 0.5, wood, MT.Wood, 3.5),
				box(18, -18, 5.5, 0.5, 0.5, wood, MT.Wood, 1.2),
				line(3, 16.5, -18, 19.5, -18, function(x, z)
					return box(x, z, 0.4, 3, 0.15, silver, MT.Metal, 0.3)
				end),
				hcyl(16.5, 2.2, -17.6, 0.3, 1.8, "Z", blue, MT.Metal),
				hcyl(18, 2.2, -17.6, 0.3, 1.8, "Z", red, MT.Metal),
				hcyl(19.5, 2.2, -17.6, 0.3, 1.8, "Z", gold, MT.Metal)
			)
		),
		P(
			"Stables",
			"Stables",
			"A little stable with hay and a brown horse.",
			cat(
				box(41, -23.5, 10, 5, 0.6, wood, MT.WoodPlanks),
				box(36.3, -19, 0.6, 5, 10, wood, MT.WoodPlanks),
				box(45.7, -19, 0.6, 5, 10, wood, MT.WoodPlanks),
				box(41, -19, 11, 0.5, 11, red, MT.Slate, 5),
				box(38, -21.5, 2, 1.5, 1.5, RGB(225, 195, 90), MT.Grass),
				box(44, -21.5, 2, 1.5, 1.5, RGB(225, 195, 90), MT.Grass),
				box(41, -19, 3.6, 1.6, 1.4, RGB(120, 70, 40), MT.Fabric, 1.8),
				box(39.8, -19, 0.5, 1.8, 1.2, RGB(120, 70, 40), MT.Fabric),
				box(42.2, -19, 0.5, 1.8, 1.2, RGB(120, 70, 40), MT.Fabric),
				box(43, -19, 0.8, 1.6, 0.8, RGB(120, 70, 40), MT.Fabric, 2.4),
				box(43.8, -19, 1.4, 0.7, 0.7, RGB(120, 70, 40), MT.Fabric, 3.2)
			)
		),
		P(
			"Well",
			"Courtyard Well",
			"A stone well with a small tiled roof.",
			cat(
				cyl(22, -27, 5, 1.6, stone, MT.Cobblestone),
				cyl(22, -27, 3.6, 1.7, water, MT.Glass),
				box(20.2, -27, 0.5, 5, 0.5, wood, MT.Wood),
				box(23.8, -27, 0.5, 5, 0.5, wood, MT.Wood),
				hcyl(22, 5, -27, 4.6, 0.5, "X", wood, MT.Wood),
				blk(22, 6.2, -28.1, 5.4, 0.3, 2.4, red, MT.Slate, V3(25, 0, 0)),
				blk(22, 6.2, -25.9, 5.4, 0.3, 2.4, red, MT.Slate, V3(-25, 0, 0)),
				cyl(22, -27, 1, 0.8, wood, MT.Wood, 2.6)
			)
		),
		P(
			"KeepBase",
			"Keep Base",
			"The big stone block of the keep in the middle of the courtyard.",
			cat(
				box(39, -36, 14, 12, 16, stone, MT.Cobblestone),
				box(31.6, -36, 0.4, 5, 3.6, wood, MT.Wood),
				box(31, -36, 2, 0.4, 6, dark, MT.Slate),
				box(31.6, -36, 1, 0.8, 6, dark, MT.Slate),
				box(31.8, -41, 0.3, 2.5, 1.4, glow, MT.Neon, 6),
				box(31.8, -31, 0.3, 2.5, 1.4, glow, MT.Neon, 6)
			)
		),
		P(
			"KeepUpper",
			"Keep Tower",
			"A narrower upper storey with a crown of battlements.",
			cat(
				box(39, -36, 10, 10, 12, RGB(160, 164, 174), MT.Cobblestone, 12),
				box(39, -36, 12, 1, 14, dark, MT.Slate, 22),
				each({ { 34, -43 }, { 39, -43 }, { 44, -43 }, { 34, -29 }, { 39, -29 }, { 44, -29 } }, function(x, z)
					return merlon(x, z, 23)
				end),
				box(33.8, -36, 0.3, 2.5, 1.5, glow, MT.Neon, 16)
			)
		),
		P(
			"Flagpoles",
			"Tower Flags",
			"A blue flag on every corner tower.",
			each(towers, function(x, z)
				return { cyl(x, z, 0.35, 6, dark, MT.Metal, 20), box(x + 1.4, z, 2.4, 1.5, 0.15, blue, MT.Fabric, 24.2) }
			end)
		),
		P(
			"Statues",
			"Knight Statues",
			"Two silver knights guarding the red carpet.",
			cat(knight(26.5, -22), knight(33.5, -22))
		),
		P(
			"Lists",
			"Garden and Jousting Lists",
			"Three trees on the lawn and a jousting fence.",
			cat(
				tree(-44, -40, 9, RGB(70, 140, 60), wood),
				tree(-36, -46, 8, RGB(80, 150, 65), wood),
				tree(-30, -30, 9, RGB(70, 140, 60), wood),
				fence(18, 34, 26, RGB(240, 240, 235), MT.Wood)
			)
		),
		P(
			"CrownSpire",
			"Golden Crown Spire",
			"A golden crown with a ruby on top of the keep and a giant blue flag.",
			cat(
				cyl(39, -36, 6, 1.2, gold, MT.Metal, 23),
				ball(39, -36, 2.4, RGB(255, 40, 70), MT.Neon, 24.2),
				ring(6, 39, -36, 2.6, function(x, z)
					return cyl(x, z, 0.7, 3.5, gold, MT.Metal, 24.2)
				end),
				cyl(42, -40, 0.5, 10, gold, MT.Metal, 23),
				box(44.6, -40, 5, 3, 0.15, blue, MT.Fabric, 29.5),
				blk(44.6, 31, -39.9, 1.6, 1.6, 0.2, silver, MT.Metal, V3(0, 0, 45))
			)
		),
	})
end

-- 12 Samurai Shiba: Shrine. Raised platform x 26..50, z -50..-18 reached by steps from the torii gate at x = 11.
do
	local h = 54
	local red, roof, stone = RGB(200, 35, 45), RGB(45, 45, 55), RGB(150, 152, 158)
	local pink, wood, white = RGB(255, 175, 205), RGB(115, 72, 45), RGB(240, 238, 230)
	local gold, water, green = RGB(250, 200, 60), RGB(80, 160, 215), RGB(90, 170, 80)
	local warm = RGB(255, 190, 90)
	local function lantern(x: number, z: number): { Piece }
		return {
			cyl(x, z, 1.6, 0.6, stone, MT.Granite),
			cyl(x, z, 0.8, 2, stone, MT.Granite, 0.6),
			box(x, z, 1.4, 1.4, 1.4, warm, MT.Neon, 2.6),
			box(x, z, 2.2, 0.4, 2.2, stone, MT.Granite, 4),
			ball(x, z, 0.8, stone, MT.Granite, 4.4),
		}
	end
	local function sakura(x: number, z: number, s: number): { Piece }
		return {
			cyl(x, z, 1.2, 4 * s, wood, MT.Wood),
			ball(x, z, 5 * s, pink, MT.Grass, 3 * s),
			ball(x - 1.6 * s, z + 0.8 * s, 3.4 * s, pink, MT.Grass, 2.6 * s),
			ball(x + 1.6 * s, z - 0.8 * s, 3.4 * s, RGB(255, 150, 190), MT.Grass, 3.2 * s),
		}
	end
	themes[12] = build("SamuraiShrine", "Shrine", h, 750, {
		P(
			"Flooring",
			"Shrine Gravel",
			"Raked grey gravel, green lawn and stone edging along the path.",
			cat(
				floorSlabs(h, RGB(80, 140, 70), MT.Grass, RGB(205, 200, 190), MT.Pebble),
				line(4, 30, 22, 30, 34, function(x, z)
					return inlay(x, z, 30, 0.8, RGB(175, 170, 162), MT.Pebble)
				end),
				inlay(8.5, 0, 1.2, 2 * h - 2, RGB(120, 120, 125), MT.Slate),
				inlay(-8.5, 0, 1.2, 2 * h - 2, RGB(120, 120, 125), MT.Slate)
			)
		),
		P(
			"Platform",
			"Shrine Platform",
			"A raised stone platform for the shrine hall.",
			cat(
				box(38, -34, 24, 3, 32, stone, MT.Granite),
				box(38, -34, 25, 0.8, 33, RGB(110, 112, 118), MT.Slate),
				box(38, -34, 24.6, 0.4, 32.6, RGB(175, 177, 183), MT.Granite, 3)
			)
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A red board with gold lettering on dark posts.",
			sign(20, 46, 16, red, gold, RGB(60, 40, 30))
		),
		P(
			"Steps",
			"Stone Steps",
			"Six wide stone steps up to the platform.",
			cat(
				line(6, 0, 0, 5, 0, function(_x, _z, i)
					local x0 = 14 + 2 * (i - 1)
					return box((x0 + 26) / 2, -34, 26 - x0, 0.5 * i, 8, stone, MT.Granite)
				end),
				box(20, -38.6, 12, 1.2, 1, stone, MT.Granite),
				box(20, -29.4, 12, 1.2, 1, stone, MT.Granite)
			)
		),
		P(
			"Torii",
			"Torii Gate",
			"A tall red torii gate at the foot of the steps.",
			cat(
				cyl(11, -40.5, 1.6, 11, red, MT.Wood),
				cyl(11, -27.5, 1.6, 11, red, MT.Wood),
				box(11, -40.5, 2.6, 0.8, 2.6, stone, MT.Granite),
				box(11, -27.5, 2.6, 0.8, 2.6, stone, MT.Granite),
				box(11, -34, 2.4, 0.7, 20, roof, MT.Wood, 11),
				box(11, -34, 1.8, 0.8, 19, red, MT.Wood, 10.2),
				box(11, -34, 1.2, 0.9, 17, red, MT.Wood, 8),
				box(10.6, -34, 0.4, 1.3, 1.4, gold, MT.Metal, 8.9)
			)
		),
		P(
			"HallWalls",
			"Shrine Hall",
			"White walls framed by red posts and beams.",
			cat(
				box(38, -34, 16, 5.5, 14, white, MT.SmoothPlastic, 3),
				box(30, -41, 1, 5.5, 1, red, MT.Wood, 3),
				box(46, -41, 1, 5.5, 1, red, MT.Wood, 3),
				box(30, -27, 1, 5.5, 1, red, MT.Wood, 3),
				box(46, -27, 1, 5.5, 1, red, MT.Wood, 3),
				box(38, -34, 16.4, 0.5, 14.4, red, MT.Wood, 3),
				box(38, -34, 16.4, 0.5, 14.4, red, MT.Wood, 8)
			)
		),
		P(
			"HallRoof",
			"Shrine Roof",
			"A dark layered roof with a golden finial.",
			cat(
				box(38, -34, 20, 0.8, 18, roof, MT.Slate, 8.5),
				box(38, -34, 16, 0.8, 14, roof, MT.Slate, 9.3),
				box(38, -34, 12, 0.8, 10, roof, MT.Slate, 10.1),
				box(38, -34, 8, 0.8, 6, roof, MT.Slate, 10.9),
				box(38, -34, 4, 0.8, 3, roof, MT.Slate, 11.7),
				cyl(38, -34, 0.5, 2, gold, MT.Metal, 12.5),
				ball(38, -34, 1.2, gold, MT.Metal, 14.2)
			)
		),
		P(
			"Doors",
			"Hall Doors and Offering Box",
			"Wooden doors, a red lintel and a donation box.",
			cat(
				box(29.8, -35, 0.4, 4, 2.2, wood, MT.Wood, 3),
				box(29.8, -33, 0.4, 4, 2.2, wood, MT.Wood, 3),
				box(29.7, -34, 0.5, 0.6, 5.2, red, MT.Wood, 7),
				box(27.5, -34, 1.4, 1.2, 3, wood, MT.WoodPlanks, 3),
				box(27.5, -34, 1, 0.1, 2, roof, MT.Slate, 4.2),
				box(28.6, -34, 0.3, 0.3, 0.3, gold, MT.Neon, 5)
			)
		),
		P(
			"Lanterns",
			"Stone Lanterns",
			"Two glowing stone lanterns beside the steps.",
			cat(lantern(17, -43), lantern(17, -25))
		),
		P("CherryTrees", "Cherry Trees", "Two pink cherry trees.", cat(sakura(16, -46, 1.2), sakura(16, -20, 1))),
		P(
			"Petals",
			"Fallen Petals",
			"Pink petals scattered around the stairs.",
			each({
				{ 14, -44 },
				{ 18, -48 },
				{ 22, -24 },
				{ 14, -22 },
				{ 20, -42 },
				{ 24, -44 },
				{ 16, -30 },
				{ 20, -18 },
				{ 12, -36 },
				{ 24, -22 },
			}, function(x, z, i)
				return blk(x, 0.27, z, 2 + (i % 3) * 0.4, 0.06, 1.4, pink, MT.Grass, V3(0, i * 37, 0))
			end)
		),
		P(
			"Pond",
			"Koi Pond",
			"A pond with rocks, lily pads and two orange koi.",
			cat(
				box(18, 10, 12, 0.3, 10, water, MT.Glass),
				ball(11.5, 10, 1.8, RGB(110, 112, 118), MT.Slate),
				ball(24.5, 7, 1.8, RGB(110, 112, 118), MT.Slate),
				ball(23.5, 14.5, 1.4, RGB(110, 112, 118), MT.Slate),
				ball(12, 4.5, 1.4, RGB(110, 112, 118), MT.Slate),
				cyl(21, 12, 1.4, 0.1, green, MT.Grass, 0.3),
				cyl(14.5, 7.5, 1.2, 0.1, green, MT.Grass, 0.3),
				box(20, 8, 1.4, 0.15, 0.5, RGB(255, 140, 40), MT.SmoothPlastic, 0.3),
				box(15, 12, 1.2, 0.15, 0.5, RGB(255, 255, 255), MT.SmoothPlastic, 0.3)
			)
		),
		P(
			"Bridge",
			"Arched Bridge",
			"A red wooden bridge over the pond.",
			cat(
				box(18, 10, 2.6, 0.4, 5, red, MT.Wood, 1.8),
				box(18, 6.2, 2.6, 0.4, 3, red, MT.Wood, 1.3),
				box(18, 13.8, 2.6, 0.4, 3, red, MT.Wood, 1.3),
				box(18, 3.7, 2.6, 0.4, 2, red, MT.Wood, 0.8),
				box(18, 16.3, 2.6, 0.4, 2, red, MT.Wood, 0.8),
				box(16.9, 10, 0.3, 0.4, 5, red, MT.Wood, 3),
				box(19.1, 10, 0.3, 0.4, 5, red, MT.Wood, 3),
				box(16.9, 7.7, 0.3, 1.4, 0.3, red, MT.Wood, 1.8),
				box(16.9, 12.3, 0.3, 1.4, 0.3, red, MT.Wood, 1.8),
				box(19.1, 7.7, 0.3, 1.4, 0.3, red, MT.Wood, 1.8),
				box(19.1, 12.3, 0.3, 1.4, 0.3, red, MT.Wood, 1.8)
			)
		),
		P(
			"Bamboo",
			"Bamboo Grove",
			"Ten tall bamboo stalks and two garden stones.",
			cat(
				each({
					{ 42, 28 },
					{ 44, 30 },
					{ 46, 28 },
					{ 43, 33 },
					{ 45, 35 },
					{ 48, 31 },
					{ 41, 36 },
					{ 47, 36 },
					{ 49, 28 },
					{ 44, 38 },
				}, function(x, z, i)
					return cyl(x, z, 0.5, 8 + (i % 4) * 1.2, green, MT.Grass)
				end),
				ball(40, 30, 1.8, RGB(110, 112, 118), MT.Slate),
				ball(47, 40, 1.4, RGB(110, 112, 118), MT.Slate)
			)
		),
		P(
			"Basin",
			"Water Basin",
			"A stone basin with a bamboo spout.",
			cat(
				box(24, 24, 3, 1.1, 2, stone, MT.Granite),
				box(24, 24, 2.4, 0.1, 1.4, water, MT.Glass, 1.1),
				cyl(22.2, 24, 0.5, 2.4, green, MT.Grass),
				hcyl(23.2, 2.4, 24, 2.4, 0.4, "X", green, MT.Grass),
				box(25.2, 24, 1.2, 0.2, 0.3, wood, MT.Wood, 1.2)
			)
		),
		P(
			"Bell",
			"Temple Bell",
			"A bronze bell hanging in a small wooden frame.",
			cat(
				cyl(46, 20, 0.8, 6, wood, MT.Wood),
				cyl(46, 26, 0.8, 6, wood, MT.Wood),
				hcyl(46, 6.3, 23, 6.8, 0.8, "Z", wood, MT.Wood),
				box(46, 23, 3, 0.4, 7.6, roof, MT.Slate, 6.7),
				cyl(46, 23, 2, 2.4, RGB(170, 120, 50), MT.Metal, 2.8),
				hcyl(44.6, 3.8, 23, 2.6, 0.4, "X", wood, MT.Wood)
			)
		),
		P(
			"Plaques",
			"Prayer Plaques",
			"A rack of small wooden wishing plaques.",
			cat(
				cyl(34, 44, 0.6, 4, wood, MT.Wood),
				cyl(46, 44, 0.6, 4, wood, MT.Wood),
				box(40, 44, 13, 0.4, 0.4, wood, MT.Wood, 3.8),
				line(8, 35, 44, 45, 44, function(x, z)
					return box(x, z, 0.9, 1.2, 0.2, RGB(210, 170, 110), MT.Wood, 2.4)
				end)
			)
		),
		P(
			"PaperLanterns",
			"Paper Lantern String",
			"A line of red paper lanterns beside the path.",
			cat(
				cyl(9.5, 12, 0.4, 6, wood, MT.Wood),
				cyl(9.5, 44, 0.4, 6, wood, MT.Wood),
				line(10, 9.5, 15, 9.5, 41, function(x, z)
					return ball(x, z, 1.5, RGB(255, 60, 60), MT.Neon, 4.4)
				end)
			)
		),
		P(
			"SamuraiStatue",
			"Samurai Statue",
			"A red-armoured warrior on a stone pedestal.",
			cat(
				box(28, -46, 3, 1.2, 3, stone, MT.Granite, 3),
				box(28, -46, 1.6, 2.4, 1, red, MT.Metal, 4.2),
				box(28, -46, 2.2, 2.4, 1.2, red, MT.Metal, 6.6),
				box(28, -46, 3.2, 0.7, 1.4, roof, MT.Metal, 8.4),
				ball(28, -46, 1.6, roof, MT.Metal, 9.1),
				blk(27.2, 11.3, -46, 0.2, 1.2, 0.2, gold, MT.Metal, V3(0, 0, 30)),
				blk(28.8, 11.3, -46, 0.2, 1.2, 0.2, gold, MT.Metal, V3(0, 0, -30)),
				box(29.4, -46, 0.2, 4, 0.2, RGB(220, 225, 235), MT.Metal, 4.6)
			)
		),
		P(
			"GreatSakura",
			"Great Sakura Tree",
			"A huge cherry tree in full bloom with floating petals.",
			cat(
				cyl(40, 10, 3, 14, wood, MT.Wood),
				blk(37.5, 12, 10, 0.9, 5, 0.9, wood, MT.Wood, V3(0, 0, 35)),
				blk(42.5, 12, 10, 0.9, 5, 0.9, wood, MT.Wood, V3(0, 0, -35)),
				ball(40, 10, 14, pink, MT.Grass, 11),
				ball(34, 8, 9, pink, MT.Grass, 10),
				ball(46, 12, 9, RGB(255, 150, 190), MT.Grass, 10),
				ball(40, 15, 8, pink, MT.Grass, 17),
				ball(36, 17, 1.2, pink, MT.Neon, 6),
				ball(44, 3, 1.2, pink, MT.Neon, 4),
				ball(33, 4, 1.2, pink, MT.Neon, 8)
			)
		),
	})
end

-- 13 Robot Shiba: Factory. Hall x 22..54, z -52..-24; the conveyor runs from its wall toward the path.
do
	local h = 57
	local steel, dark, concrete = RGB(140, 150, 165), RGB(55, 60, 72), RGB(110, 112, 118)
	local cyan, yellow, orange = RGB(70, 240, 255), RGB(255, 200, 30), RGB(255, 120, 30)
	local function arm(x: number, z: number, dir: number): { Piece }
		return {
			cyl(x, z, 3.2, 1, dark, MT.Metal),
			cyl(x, z, 2, 3, yellow, MT.Metal, 1),
			blk(x, 5.6, z + 2.2 * dir, 1.2, 1.2, 5, yellow, MT.Metal, V3(-35 * dir, 0, 0)),
			blk(x, 6.4, z + 5.4 * dir, 1, 1, 4, yellow, MT.Metal, V3(25 * dir, 0, 0)),
			ball(x, z + 7.2 * dir, 1.3, dark, MT.Metal, 3.6),
			box(x - 0.5, z + 7.2 * dir, 0.3, 1.6, 0.3, steel, MT.Metal, 2.2),
			box(x + 0.5, z + 7.2 * dir, 0.3, 1.6, 0.3, steel, MT.Metal, 2.2),
		}
	end
	themes[13] = build("RobotFactory", "Factory", h, 800, {
		P(
			"Flooring",
			"Factory Floor",
			"Dark concrete with yellow hazard lines and cyan guide strips.",
			cat(
				floorSlabs(h, RGB(90, 92, 100), MT.Concrete, RGB(105, 108, 116), MT.Concrete),
				inlay(19.5, -38, 1, 32, yellow, MT.SmoothPlastic),
				inlay(56.5, -38, 1, 32, yellow, MT.SmoothPlastic),
				inlay(38, -21.5, 37, 1, yellow, MT.SmoothPlastic),
				inlay(-30, 0, 0.8, 2 * h - 4, cyan, MT.Neon),
				inlay(-42, 0, 0.8, 2 * h - 4, cyan, MT.Neon)
			)
		),
		P(
			"Hall",
			"Factory Hall",
			"A big steel hall with a dark base, corner columns and a roller door.",
			cat(
				box(38, -38, 32, 14, 28, steel, MT.Metal),
				box(38, -38, 32.4, 2, 28.4, dark, MT.Concrete),
				box(22, -52, 1.4, 14.6, 1.4, dark, MT.DiamondPlate),
				box(54, -52, 1.4, 14.6, 1.4, dark, MT.DiamondPlate),
				box(22, -24, 1.4, 14.6, 1.4, dark, MT.DiamondPlate),
				box(54, -24, 1.4, 14.6, 1.4, dark, MT.DiamondPlate),
				box(21.8, -38, 0.4, 6, 8, dark, MT.CorrodedMetal)
			)
		),
		P("Sign", "Get Bonked Sign", "A dark board with cyan neon lettering.", sign(26, 49, 18, dark, cyan, steel)),
		P(
			"Roof",
			"Roof and Skylights",
			"A flat roof with glowing skylights and vents.",
			cat(
				box(38, -38, 33, 0.8, 29, dark, MT.Metal, 14),
				line(4, 28, -38, 48, -38, function(x, z)
					return box(x, z, 4, 1.2, 18, cyan, MT.Glass, 14.8)
				end),
				each({ { 52, -30 }, { 52, -38 }, { 52, -46 } }, function(x, z)
					return cyl(x, z, 2, 1.5, steel, MT.Metal, 14.8)
				end)
			)
		),
		P(
			"GlowStrips",
			"Cyan Glow Strips",
			"Neon strips along the front wall of the hall.",
			cat(
				box(21.7, -38, 0.3, 0.5, 26, cyan, MT.Neon, 4),
				box(21.7, -38, 0.3, 0.5, 26, cyan, MT.Neon, 8),
				box(21.7, -38, 0.3, 0.5, 26, cyan, MT.Neon, 12),
				each({ { 21.7, -50 }, { 21.7, -46 }, { 21.7, -30 }, { 21.7, -26 } }, function(x, z)
					return box(x, z, 0.3, 10, 0.5, cyan, MT.Neon, 2)
				end)
			)
		),
		P(
			"Conveyor",
			"Conveyor Line",
			"A long conveyor belt with chevrons running out of the hall.",
			cat(
				box(15.75, -30, 12.5, 0.8, 3, dark, MT.Metal, 1.4),
				box(15.75, -31.6, 12.5, 0.6, 0.4, yellow, MT.Metal, 2.2),
				box(15.75, -28.4, 12.5, 0.6, 0.4, yellow, MT.Metal, 2.2),
				each({ { 10.5, -30 }, { 14, -30 }, { 17.5, -30 }, { 21, -30 } }, function(x, z)
					return box(x, z, 0.6, 1.4, 2.4, steel, MT.Metal)
				end),
				line(3, 12, -30, 20, -30, function(x, z)
					return box(x, z, 1.2, 0.1, 1.6, cyan, MT.Neon, 2.2)
				end)
			)
		),
		P(
			"Crates",
			"Crates and Little Robots",
			"Boxes and tiny robots riding the belt.",
			cat(
				each({ { 11, -30 }, { 14.5, -30 }, { 18, -30 }, { 21, -30 } }, function(x, z, i)
					return box(
						x,
						z,
						1.6,
						1.6,
						1.6,
						if i % 2 == 0 then orange else RGB(200, 160, 90),
						MT.WoodPlanks,
						2.2
					)
				end),
				box(12.8, -30, 1, 1.2, 0.8, steel, MT.Metal, 2.2),
				ball(12.8, -30, 0.9, cyan, MT.Neon, 3.4),
				box(19.6, -30, 1, 1.2, 0.8, steel, MT.Metal, 2.2),
				ball(19.6, -30, 0.9, cyan, MT.Neon, 3.4)
			)
		),
		P("ArmOne", "Robot Arm One", "A yellow robot arm reaching over the belt.", arm(15, -24, -1)),
		P("ArmTwo", "Robot Arm Two", "A second yellow arm on the other side of the belt.", arm(15, -36, 1)),
		P(
			"Smokestack",
			"Smokestack",
			"A tall brick chimney with striped bands.",
			cat(
				box(50, -18, 7, 2, 7, concrete, MT.Concrete),
				cyl(50, -18, 5, 28, RGB(150, 80, 60), MT.Brick, 2),
				cyl(50, -18, 5.4, 1, RGB(240, 240, 240), MT.SmoothPlastic, 12),
				cyl(50, -18, 5.4, 1, RGB(220, 50, 50), MT.SmoothPlastic, 16),
				cyl(50, -18, 5.4, 1, RGB(240, 240, 240), MT.SmoothPlastic, 20),
				cyl(50, -18, 5.8, 0.8, dark, MT.Metal, 30)
			)
		),
		P(
			"Smoke",
			"Sparks and Smoke",
			"Grey smoke puffs and orange sparks above the chimney.",
			cat(
				ball(50, -18, 4, RGB(150, 150, 155), MT.SmoothPlastic, 31),
				ball(51.5, -17, 5.5, RGB(165, 165, 170), MT.SmoothPlastic, 34),
				ball(53, -16.5, 7, RGB(180, 180, 185), MT.SmoothPlastic, 38),
				each(
					{ { 48.5, -18 }, { 51.5, -19.5 }, { 50, -16.2 }, { 52.5, -17.5 }, { 49.5, -19.5 } },
					function(x, z, i)
						return ball(x, z, 0.7, orange, MT.Neon, 31 + i * 0.9)
					end
				)
			)
		),
		P(
			"Pipes",
			"Pipework",
			"Pipes and valves along the hall wall.",
			cat(
				hcyl(20.8, 9, -38, 26, 1, "Z", steel, MT.Metal),
				hcyl(20.8, 6.5, -38, 26, 0.8, "Z", orange, MT.Metal),
				cyl(20.8, -26, 1, 14, steel, MT.Metal),
				cyl(20.8, -50, 1, 14, steel, MT.Metal),
				ball(20.8, -26, 1.5, dark, MT.Metal, 8.2),
				ball(20.8, -50, 1.5, dark, MT.Metal, 8.2),
				ball(20.8, -32, 1.4, dark, MT.Metal, 8.3),
				ball(20.8, -44, 1.4, dark, MT.Metal, 8.3),
				cyl(20, -32, 1.4, 0.3, yellow, MT.Metal, 10),
				cyl(20, -44, 1.4, 0.3, yellow, MT.Metal, 10)
			)
		),
		P(
			"Tanks",
			"Storage Tanks",
			"Two tall tanks with hazard bands and a round gas sphere.",
			cat(
				each({ { 13, -46 }, { 13, -53 } }, function(x, z)
					return {
						cyl(x, z, 6, 9, steel, MT.Metal),
						cyl(x, z, 6.4, 0.4, dark, MT.Metal, 9),
						cyl(x, z, 6.2, 1.5, yellow, MT.SmoothPlastic, 3),
					}
				end),
				ball(28, -14, 7, RGB(200, 205, 215), MT.Metal, 2.5),
				each({ { 26.5, -15.5 }, { 29.5, -15.5 }, { 26.5, -12.5 }, { 29.5, -12.5 } }, function(x, z)
					return box(x, z, 0.6, 3, 0.6, dark, MT.Metal)
				end)
			)
		),
		P(
			"ControlBooth",
			"Control Booth",
			"A glass booth where the foreman watches the line.",
			cat(
				box(16, 28, 8, 1, 6, dark, MT.Concrete),
				box(16, 28, 8, 4, 6, cyan, MT.Glass, 1),
				box(16, 28, 9, 0.6, 7, dark, MT.Metal, 5),
				box(16, 29.8, 5, 1.2, 1, steel, MT.Metal, 1),
				box(14.5, 29.6, 1.6, 1, 0.2, cyan, MT.Neon, 2.2),
				box(17.5, 29.6, 1.6, 1, 0.2, cyan, MT.Neon, 2.2),
				cyl(19.5, 26, 0.3, 4, steel, MT.Metal, 5.6),
				ball(19.5, 26, 0.8, orange, MT.Neon, 9.6)
			)
		),
		P(
			"Gears",
			"Gear Display",
			"A big cogwheel on a plinth.",
			cat(
				box(40, 26, 3, 3, 3, concrete, MT.Concrete),
				cyl(40, 26, 6, 0.8, steel, MT.Metal, 3),
				ball(40, 26, 1.6, yellow, MT.Metal, 3.4),
				ring(8, 40, 26, 3.1, function(x, z, a)
					return blk(x, 3.4, z, 1, 0.8, 1.2, steel, MT.Metal, V3(0, -a, 0))
				end)
			)
		),
		P(
			"RobotStatue",
			"Robot Statue",
			"A friendly robot on show in front of the factory.",
			cat(
				box(30, 14, 1.6, 0.8, 2.4, dark, MT.Metal),
				box(33, 14, 1.6, 0.8, 2.4, dark, MT.Metal),
				box(30, 14, 1.2, 3, 1.2, steel, MT.Metal, 0.8),
				box(33, 14, 1.2, 3, 1.2, steel, MT.Metal, 0.8),
				box(31.5, 14, 5, 4, 3, steel, MT.Metal, 3.8),
				box(29.2, 14, 0.3, 2, 1.6, cyan, MT.Neon, 4.8),
				box(31.5, 14, 8, 1, 1, dark, MT.Metal, 6.4),
				box(31.5, 14, 2.6, 2.4, 2.4, steel, MT.Metal, 7.8),
				box(30.1, 14, 0.2, 0.6, 1.6, cyan, MT.Neon, 8.8),
				cyl(31.5, 14, 0.3, 2, dark, MT.Metal, 10.2),
				ball(31.5, 14, 0.8, orange, MT.Neon, 12.2)
			)
		),
		P(
			"Generator",
			"Power Generator",
			"Two humming generators wrapped in glowing coils.",
			cat(
				box(46, 10, 9, 1, 6, dark, MT.Concrete),
				cyl(43.5, 10, 4, 6, steel, MT.Metal, 1),
				cyl(48.5, 10, 4, 6, steel, MT.Metal, 1),
				cyl(43.5, 10, 4.4, 0.5, cyan, MT.Neon, 2.5),
				cyl(43.5, 10, 4.4, 0.5, cyan, MT.Neon, 4.5),
				cyl(48.5, 10, 4.4, 0.5, cyan, MT.Neon, 2.5),
				cyl(48.5, 10, 4.4, 0.5, cyan, MT.Neon, 4.5),
				ball(46, 10, 2, yellow, MT.Neon, 7.2)
			)
		),
		P(
			"Forklift",
			"Forklift",
			"A little yellow forklift carrying a crate.",
			cat(
				box(24, 18, 4.5, 1.4, 3, yellow, MT.Metal, 0.8),
				box(23.2, 18, 1.8, 0.2, 2.6, dark, MT.Metal, 2.2),
				box(22.4, 16.6, 0.3, 3, 0.3, dark, MT.Metal, 2.2),
				box(22.4, 19.4, 0.3, 3, 0.3, dark, MT.Metal, 2.2),
				box(26.6, 18, 0.5, 3.6, 2.6, dark, MT.Metal, 0.8),
				box(28.4, 18, 3, 0.3, 0.5, steel, MT.Metal, 0.9),
				box(29, 18, 1.6, 1.6, 1.6, RGB(200, 160, 90), MT.WoodPlanks, 1.2),
				hcyl(22.6, 0.8, 16.4, 0.6, 1.6, "Z", dark, MT.Metal),
				hcyl(25.6, 0.8, 16.4, 0.6, 1.6, "Z", dark, MT.Metal),
				hcyl(22.6, 0.8, 19.6, 0.6, 1.6, "Z", dark, MT.Metal),
				hcyl(25.6, 0.8, 19.6, 0.6, 1.6, "Z", dark, MT.Metal)
			)
		),
		P(
			"Warning",
			"Warning Lights and Fence",
			"A hazard fence and three orange warning beacons.",
			cat(
				fence(26, 38, -19.5, yellow, MT.Metal),
				each({ { 26, -17 }, { 38, -17 }, { 46, -21 } }, function(x, z)
					return lamp(x, z, 5, orange, dark)
				end)
			)
		),
		P(
			"GiantRobot",
			"Giant Robot",
			"A huge robot standing on the factory roof with glowing eyes.",
			cat(
				box(35, -38, 3.4, 1, 5, dark, MT.Metal, 14.8),
				box(41, -38, 3.4, 1, 5, dark, MT.Metal, 14.8),
				box(35, -38, 2.4, 7, 2.6, steel, MT.Metal, 15.8),
				box(41, -38, 2.4, 7, 2.6, steel, MT.Metal, 15.8),
				box(38, -38, 9, 2.4, 4, dark, MT.Metal, 22.8),
				box(38, -38, 9.6, 8, 5.6, steel, MT.Metal, 25.2),
				box(33.1, -38, 0.3, 4, 4, cyan, MT.Neon, 26.4),
				ball(31.8, -38, 3.6, yellow, MT.Metal, 30),
				ball(44.2, -38, 3.6, yellow, MT.Metal, 30),
				box(31.4, -38, 2.2, 8, 2.4, steel, MT.Metal, 22.4),
				box(44.6, -38, 2.2, 8, 2.4, steel, MT.Metal, 22.4),
				box(38, -38, 5, 4, 4, steel, MT.Metal, 33.2),
				box(35.4, -38, 0.3, 1, 3, cyan, MT.Neon, 35),
				cyl(38, -38, 0.4, 3.5, dark, MT.Metal, 37.2)
			)
		),
	})
end

-- 14 Astronaut Shiba: Launch Pad. Round pad (centre (38, -38), diameter 26) with a rocket in the middle and a gantry beside it.
do
	local h = 60
	local concrete, white, red = RGB(150, 154, 160), RGB(240, 242, 248), RGB(230, 50, 50)
	local orange, dark, cyan = RGB(255, 130, 30), RGB(60, 65, 75), RGB(120, 220, 255)
	local yellow = RGB(255, 200, 30)
	themes[14] = build("LaunchPad", "Launch Pad", h, 850, {
		P(
			"Flooring",
			"Pad Floor",
			"Concrete ground with a yellow hazard ring around the launch pad.",
			cat(
				floorSlabs(h, RGB(120, 124, 130), MT.Concrete, RGB(150, 154, 160), MT.Concrete),
				cyl(38, -38, 32, 0.1, yellow, MT.SmoothPlastic, 0.2),
				cyl(38, -38, 30.4, 0.15, RGB(150, 154, 160), MT.Concrete, 0.2),
				inlay(30, 0, 0.8, 2 * h - 4, white, MT.SmoothPlastic),
				inlay(-30, 0, 0.8, 2 * h - 4, white, MT.SmoothPlastic)
			)
		),
		P(
			"Platform",
			"Launch Platform",
			"A raised round platform with a dark flame plate and hold-down clamps.",
			cat(
				cyl(38, -38, 26, 2, RGB(140, 144, 150), MT.Concrete),
				cyl(38, -38, 22, 0.3, dark, MT.Metal, 2),
				ring(4, 38, -38, 7, function(x, z, a)
					return blk(x, 2.8, z, 1.2, 1, 1.2, orange, MT.Metal, V3(0, -a, 0))
				end)
			)
		),
		P("Sign", "Get Bonked Sign", "A white board with red neon lettering.", sign(22, 52, 18, white, red, dark)),
		P(
			"LowerBody",
			"Rocket Lower Body",
			"The white first stage of the rocket with black bands.",
			cat(
				cyl(38, -38, 11.2, 1.2, dark, MT.Metal, 4.3),
				cyl(38, -38, 10, 14, white, MT.SmoothPlastic, 5.5),
				cyl(38, -38, 10.2, 1.5, dark, MT.SmoothPlastic, 9),
				cyl(38, -38, 10.2, 1.5, dark, MT.SmoothPlastic, 14)
			)
		),
		P(
			"UpperBody",
			"Rocket Upper Body",
			"The crew section with a red band and two round windows.",
			cat(
				cyl(38, -38, 10.3, 0.6, dark, MT.Metal, 19.5),
				cyl(38, -38, 10, 12, white, MT.SmoothPlastic, 20.1),
				cyl(38, -38, 10.2, 1.4, red, MT.SmoothPlastic, 26),
				ball(33.2, -40, 1.8, cyan, MT.Glass, 23),
				ball(33.2, -36, 1.8, cyan, MT.Glass, 23)
			)
		),
		P(
			"Nose",
			"Nose Cone",
			"A red stepped nose cone with a little antenna.",
			cat(
				cyl(38, -38, 9, 3, red, MT.SmoothPlastic, 32.1),
				cyl(38, -38, 7, 3, red, MT.SmoothPlastic, 35.1),
				cyl(38, -38, 5, 2.5, red, MT.SmoothPlastic, 38.1),
				cyl(38, -38, 3, 2, red, MT.SmoothPlastic, 40.6),
				ball(38, -38, 2, red, MT.SmoothPlastic, 42.4),
				cyl(38, -38, 0.3, 3, dark, MT.Metal, 44)
			)
		),
		P(
			"Fins",
			"Rocket Fins",
			"Four big red fins at the foot of the rocket.",
			cat(
				wedge(31.5, -38, 3, 8, 0.8, red, MT.Metal, 5, 0),
				wedge(44.5, -38, 3, 8, 0.8, red, MT.Metal, 5, 180),
				wedge(38, -31.5, 3, 8, 0.8, red, MT.Metal, 5, 90),
				wedge(38, -44.5, 3, 8, 0.8, red, MT.Metal, 5, 270)
			)
		),
		P(
			"Nozzles",
			"Engine Nozzles",
			"Three dark engine nozzles with glowing centres under the rocket.",
			cat(
				cyl(38, -38, 4, 2, dark, MT.Metal, 2.3),
				ring(3, 38, -38, 2.2, function(x, z)
					return cat(cyl(x, z, 2.2, 2, dark, MT.Metal, 2.3), cyl(x, z, 1.5, 0.2, orange, MT.Neon, 4.3))
				end)
			)
		),
		P(
			"GantryFrame",
			"Gantry Tower",
			"An orange service tower with grated floors.",
			cat(
				each({ { 26.4, -39.6 }, { 29.6, -39.6 }, { 26.4, -36.4 }, { 29.6, -36.4 } }, function(x, z)
					return box(x, z, 0.8, 38, 0.8, orange, MT.Metal, 2.3)
				end),
				box(28, -38, 4, 0.5, 4, orange, MT.DiamondPlate, 12),
				box(28, -38, 4, 0.5, 4, orange, MT.DiamondPlate, 22),
				box(28, -38, 4, 0.5, 4, orange, MT.DiamondPlate, 32),
				blk(28, 8, -40, 0.4, 12, 0.4, orange, MT.Metal, V3(25, 0, 0)),
				blk(28, 18, -36, 0.4, 12, 0.4, orange, MT.Metal, V3(-25, 0, 0)),
				blk(28, 28, -40, 0.4, 12, 0.4, orange, MT.Metal, V3(25, 0, 0))
			)
		),
		P(
			"GantryArms",
			"Gantry Arms",
			"Swing arms that reach to the rocket, and a red beacon on top.",
			cat(
				box(30.7, -38, 3.4, 0.6, 2, orange, MT.Metal, 15),
				box(30.7, -38, 3.4, 0.6, 2, orange, MT.Metal, 25),
				box(30.7, -38, 3.4, 0.6, 2, orange, MT.Metal, 35),
				box(32, -38, 0.8, 1, 2.4, dark, MT.Metal, 14.8),
				box(32, -38, 0.8, 1, 2.4, dark, MT.Metal, 24.8),
				box(32, -38, 0.8, 1, 2.4, dark, MT.Metal, 34.8),
				cyl(28, -38, 0.3, 4, dark, MT.Metal, 40.6),
				ball(28, -38, 1.2, RGB(255, 40, 40), MT.Neon, 44.4)
			)
		),
		P(
			"FuelTanks",
			"Fuel Tanks",
			"Two white fuel spheres joined by an orange pipe.",
			cat(
				ball(34, -18, 7, white, MT.Metal, 2),
				ball(44, -18, 7, white, MT.Metal, 2),
				cyl(34, -18, 3, 2, dark, MT.Metal),
				cyl(44, -18, 3, 2, dark, MT.Metal),
				hcyl(39, 4, -18, 6.5, 0.7, "X", orange, MT.Metal),
				hcyl(38, 1.2, -21.5, 18, 0.7, "X", orange, MT.Metal)
			)
		),
		P(
			"MissionControl",
			"Mission Control",
			"A concrete bunker with glowing glass strips.",
			cat(
				box(40, 10, 16, 4, 10, concrete, MT.Concrete),
				box(40, 10, 17, 0.8, 11, dark, MT.Metal, 4),
				box(40, 15.1, 12, 1.6, 0.3, cyan, MT.Glass, 1.4),
				box(31.9, 10, 0.3, 1.6, 6, cyan, MT.Glass, 1.4),
				box(47, 15.1, 2, 2.6, 0.3, dark, MT.Metal),
				cyl(46, 7, 0.4, 6, dark, MT.Metal, 4.8),
				ball(46, 7, 1, RGB(255, 40, 40), MT.Neon, 10.8)
			)
		),
		P(
			"Radar",
			"Radar Dish",
			"A white dish on a mast that follows the rocket.",
			cat(
				box(28, 14, 3, 1, 3, concrete, MT.Concrete),
				cyl(28, 14, 1, 8, white, MT.Metal, 1),
				mk(PT.Cylinder, 28, 9.4, 14, 0.6, 7, 7, white, MT.Metal, V3(0, 0, 60)),
				cyl(28.8, 14, 0.3, 3, dark, MT.Metal, 9.6),
				ball(28.8, 14, 0.9, RGB(255, 40, 40), MT.Neon, 12.4)
			)
		),
		P(
			"Floodlights",
			"Floodlights",
			"Four tall floodlight masts around the pad.",
			each({ { 22, -26 }, { 22, -50 }, { 54, -26 }, { 54, -50 } }, function(x, z)
				return { cyl(x, z, 0.6, 12, dark, MT.Metal), box(x, z, 3, 1.6, 0.6, white, MT.Neon, 12) }
			end)
		),
		P(
			"Rover",
			"Moon Rover",
			"A yellow rover with a dish and big wheels.",
			cat(
				box(16, 22, 4.5, 1, 3, yellow, MT.Metal, 1),
				box(15, 22, 1.4, 0.8, 1.6, dark, MT.Metal, 2),
				hcyl(14.4, 0.9, 20.3, 0.8, 1.8, "Z", dark, MT.Metal),
				hcyl(17.6, 0.9, 20.3, 0.8, 1.8, "Z", dark, MT.Metal),
				hcyl(14.4, 0.9, 23.7, 0.8, 1.8, "Z", dark, MT.Metal),
				hcyl(17.6, 0.9, 23.7, 0.8, 1.8, "Z", dark, MT.Metal),
				cyl(17.4, 22, 0.2, 2.5, dark, MT.Metal, 2),
				mk(PT.Cylinder, 17.4, 4.8, 22, 0.3, 1.8, 1.8, white, MT.Metal, V3(0, 0, 40))
			)
		),
		P(
			"Statue",
			"Astronaut Statue",
			"A statue of an astronaut with a golden visor.",
			cat(
				box(26, -14, 4, 1.5, 4, concrete, MT.Concrete),
				box(26, -14, 2, 3, 1.2, white, MT.SmoothPlastic, 1.5),
				box(26, -14, 2.6, 3, 1.6, white, MT.SmoothPlastic, 4.5),
				box(26, -14, 2.7, 0.5, 1.7, orange, MT.SmoothPlastic, 5.6),
				box(27.4, -14, 1, 2.2, 1.6, RGB(170, 175, 185), MT.Metal, 4.8),
				box(26, -14, 0.8, 0.8, 4.6, white, MT.SmoothPlastic, 6),
				ball(26, -14, 2.4, white, MT.SmoothPlastic, 7.6),
				ball(24.9, -14, 1.5, RGB(255, 200, 80), MT.Glass, 8)
			)
		),
		P(
			"Flag",
			"Flag Pole",
			"A tall pole with a striped flag and a star.",
			cat(
				cyl(30, -12, 0.4, 12, dark, MT.Metal),
				line(5, 0, 0, 0, 0, function(_x, _z, i)
					return box(32.4, -12, 4.8, 0.5, 0.15, if i % 2 == 1 then red else white, MT.Fabric, 6 + i * 0.5)
				end),
				box(30.9, -12, 2, 1.5, 0.2, RGB(40, 70, 190), MT.Fabric, 7.5),
				ball(30.9, -11.9, 0.6, white, MT.Neon, 7.95)
			)
		),
		P(
			"Countdown",
			"Countdown Board",
			"A big board counting down in cyan neon.",
			cat(
				cyl(12, -10, 0.5, 6, dark, MT.Metal),
				cyl(22, -10, 0.5, 6, dark, MT.Metal),
				box(17, -10, 12, 6, 0.6, dark, MT.Metal, 6),
				box(13.5, -9.6, 0.6, 3.4, 0.3, cyan, MT.Neon, 7.2),
				box(16, -9.6, 2.4, 0.5, 0.3, cyan, MT.Neon, 7.2),
				box(16, -9.6, 2.4, 0.5, 0.3, cyan, MT.Neon, 10.1),
				box(14.9, -9.6, 0.5, 3.4, 0.3, cyan, MT.Neon, 7.2),
				box(17.1, -9.6, 0.5, 3.4, 0.3, cyan, MT.Neon, 7.2),
				box(19.5, -9.6, 4, 0.8, 0.3, red, MT.Neon, 11)
			)
		),
		P(
			"Truck",
			"Support Truck",
			"A white service truck with an orange cab.",
			cat(
				box(44, 34, 8, 3, 3.4, white, MT.SmoothPlastic, 1.2),
				box(49, 34, 2.6, 2.4, 3, orange, MT.SmoothPlastic, 1.2),
				box(50.4, 34, 0.2, 1.2, 2.2, cyan, MT.Glass, 2),
				box(44, 34, 8.2, 0.5, 3.6, dark, MT.Metal, 0.8),
				hcyl(41, 1, 32, 0.8, 2, "Z", dark, MT.Metal),
				hcyl(47, 1, 32, 0.8, 2, "Z", dark, MT.Metal),
				hcyl(41, 1, 36, 0.8, 2, "Z", dark, MT.Metal),
				hcyl(47, 1, 36, 0.8, 2, "Z", dark, MT.Metal),
				box(43, 34, 4, 0.4, 3.5, red, MT.SmoothPlastic, 4.2)
			)
		),
		P(
			"Liftoff",
			"Ignition and Smoke",
			"Burning plumes around the pad and billowing white smoke.",
			cat(
				ring(5, 38, -38, 9.5, function(x, z)
					return cat(cyl(x, z, 3, 5, orange, MT.Neon, 2.3), cyl(x, z, 1.6, 6.5, yellow, MT.Neon, 2.3))
				end),
				ring(4, 38, -38, 13, function(x, z, a)
					return ball(x, z, 7 - (a % 3), RGB(240, 240, 245), MT.SmoothPlastic, 2.3)
				end)
			)
		),
	})
end

-- 15 Superhero Shiba: Hero HQ. Tower at (40, -40), statue plaza at (22, -22), signal beam on the roof.
do
	local h = 63
	local blue, red, yellow = RGB(40, 80, 200), RGB(220, 40, 50), RGB(255, 215, 60)
	local steel, dark, cyan = RGB(150, 160, 175), RGB(50, 55, 70), RGB(120, 225, 255)
	local white, wood = RGB(240, 242, 248), RGB(130, 90, 55)
	themes[15] = build("HeroHQ", "Hero HQ", h, 850, {
		P(
			"Flooring",
			"Plaza Floor",
			"Blue-grey paving with a red and yellow hero emblem in the plaza.",
			cat(
				floorSlabs(h, RGB(70, 80, 110), MT.Concrete, RGB(95, 105, 135), MT.Concrete),
				inlay(22, -22, 16, 16, red, MT.SmoothPlastic),
				blk(22, 0.3, -22, 11, 0.06, 11, yellow, MT.SmoothPlastic, V3(0, 45, 0)),
				inlay(22, -22, 5, 5, blue, MT.SmoothPlastic)
			)
		),
		P(
			"Base",
			"HQ Tower Base",
			"The wide blue ground floor of the tower.",
			cat(
				box(40, -40, 22, 1, 22, dark, MT.Concrete),
				box(40, -40, 20, 14, 20, blue, MT.Concrete),
				box(40, -40, 20.6, 1, 20.6, steel, MT.Metal, 13)
			)
		),
		P("Sign", "Get Bonked Sign", "A blue board with yellow neon lettering.", sign(24, 58, 18, blue, yellow, steel)),
		P(
			"Mid",
			"HQ Tower Middle",
			"A narrower middle section with a red stripe.",
			cat(
				box(40, -40, 14, 16, 14, RGB(55, 100, 215), MT.Concrete, 14),
				box(40, -40, 14.6, 1.2, 14.6, red, MT.SmoothPlastic, 22),
				box(40, -40, 14.6, 0.8, 14.6, steel, MT.Metal, 29.2)
			)
		),
		P(
			"Top",
			"HQ Tower Top",
			"The top floor with a red roof and four steel posts.",
			cat(
				box(40, -40, 10, 10, 10, blue, MT.Concrete, 30),
				box(40, -40, 11.6, 1, 11.6, red, MT.SmoothPlastic, 40),
				each({ { 34.7, -45.3 }, { 45.3, -45.3 }, { 34.7, -34.7 }, { 45.3, -34.7 } }, function(x, z)
					return box(x, z, 1, 10, 1, steel, MT.Metal, 30)
				end)
			)
		),
		P(
			"Emblem",
			"Hero Emblem",
			"A giant diamond emblem on the front of the tower.",
			cat(
				blk(29.6, 7.5, -43, 0.4, 9, 9, yellow, MT.SmoothPlastic, V3(45, 0, 0)),
				blk(29.4, 7.5, -43, 0.4, 6.4, 6.4, red, MT.SmoothPlastic, V3(45, 0, 0)),
				blk(29.2, 7.5, -43, 0.4, 3.6, 3.6, blue, MT.SmoothPlastic, V3(45, 0, 0)),
				box(29, -43, 0.3, 0.8, 8, cyan, MT.Neon, 7.1)
			)
		),
		P(
			"Entrance",
			"Hero Entrance",
			"Glass doors with a red canopy on two pillars.",
			cat(
				box(29.7, -33.5, 0.4, 5, 3.4, cyan, MT.Glass),
				box(28.2, -33.5, 3.4, 0.5, 7, red, MT.SmoothPlastic, 6),
				cyl(27, -36.7, 0.7, 6, steel, MT.Metal),
				cyl(27, -30.3, 0.7, 6, steel, MT.Metal),
				box(28.6, -33.5, 2, 0.4, 6, steel, MT.Granite)
			)
		),
		P(
			"Windows",
			"Tower Windows",
			"Two rows of glowing cyan windows.",
			each({ { -45, 17 }, { -40, 17 }, { -35, 17 }, { -45, 24 }, { -40, 24 }, { -35, 24 } }, function(z, y0)
				return box(32.8, z, 0.3, 2.6, 2, cyan, MT.Neon, y0)
			end)
		),
		P(
			"Helipad",
			"Roof Helipad",
			"A helipad with a yellow H and a radio mast.",
			cat(
				cyl(37.5, -37.5, 6.4, 0.3, dark, MT.Concrete, 41),
				box(36.6, -37.5, 0.5, 0.1, 3, yellow, MT.Neon, 41.3),
				box(38.4, -37.5, 0.5, 0.1, 3, yellow, MT.Neon, 41.3),
				box(37.5, -37.5, 1.8, 0.1, 0.5, yellow, MT.Neon, 41.3),
				cyl(35, -44, 0.3, 6, steel, MT.Metal, 41),
				ball(35, -44, 0.9, red, MT.Neon, 46.8)
			)
		),
		P(
			"Spotlight",
			"Signal Spotlight",
			"A big spotlight on the roof pointing at the sky.",
			cat(
				box(43.5, -43.5, 3, 1, 3, dark, MT.Metal, 41),
				cyl(43.5, -43.5, 2.4, 2.4, steel, MT.Metal, 42),
				cyl(43.5, -43.5, 2, 0.2, yellow, MT.Neon, 44.4)
			)
		),
		P(
			"Beam",
			"Signal Beam",
			"A bright beam of light shooting up from the spotlight.",
			cat(
				cyl(43.5, -43.5, 1.6, 14, yellow, MT.Neon, 44.6),
				cyl(43.5, -43.5, 3, 14, RGB(255, 240, 170), MT.Neon, 44.6),
				ball(43.5, -43.5, 4, yellow, MT.Neon, 58.6)
			)
		),
		P(
			"Pedestal",
			"Statue Pedestal",
			"A granite pedestal in the middle of the plaza.",
			cat(
				box(22, -22, 8, 0.8, 8, dark, MT.Granite),
				box(22, -22, 6, 3, 6, steel, MT.Granite, 0.8),
				box(18.9, -22, 0.2, 1, 3, yellow, MT.Neon, 1.8)
			)
		),
		P(
			"Statue",
			"Hero Statue",
			"A huge statue of the hero with a raised fist.",
			cat(
				box(22, -23.1, 2, 1, 1.2, dark, MT.Metal, 3.8),
				box(22, -20.9, 2, 1, 1.2, dark, MT.Metal, 3.8),
				box(22, -22, 1.8, 4, 3.4, blue, MT.Fabric, 4.8),
				box(22, -22, 2, 0.6, 3.6, yellow, MT.Metal, 8.8),
				box(22, -22, 2, 4.2, 4, blue, MT.Fabric, 9.4),
				box(20.9, -22, 0.2, 1.8, 1.8, yellow, MT.Neon, 10.6),
				box(22, -24.5, 1, 3.6, 1, blue, MT.Fabric, 9.6),
				blk(22, 14.5, -19.2, 1, 4.4, 1, blue, MT.Fabric, V3(-30, 0, 0)),
				ball(22, -22, 2.2, RGB(255, 205, 160), MT.SmoothPlastic, 13.6),
				box(20.9, -22, 0.2, 0.6, 1.8, red, MT.Neon, 14.3)
			)
		),
		P(
			"Cape",
			"Hero Cape",
			"A flowing red cape behind the statue.",
			cat(
				wedge(23.6, -22, 1.6, 7, 3.8, red, MT.Fabric, 6.8, 0),
				box(23.2, -22, 0.5, 2, 4.2, red, MT.Fabric, 12),
				wedge(24, -22, 1.2, 5, 3, RGB(180, 30, 40), MT.Fabric, 4, 0)
			)
		),
		P(
			"Fountain",
			"Plaza Fountain",
			"A fountain with two benches.",
			cat(
				fountain(34, -12, 6, RGB(90, 190, 255), steel),
				box(34, -3.5, 5, 0.5, 1.4, wood, MT.Wood, 1),
				box(34, -2.9, 5, 1.2, 0.3, wood, MT.Wood, 1.5),
				box(34, -20.5, 5, 0.5, 1.4, wood, MT.Wood, 1),
				box(34, -21.1, 5, 1.2, 0.3, wood, MT.Wood, 1.5)
			)
		),
		P(
			"Flags",
			"Hero Flags",
			"Three flags in red, blue and yellow.",
			each({ { 14, 30 }, { 22, 30 }, { 30, 30 } }, function(x, z, i)
				return {
					cyl(x, z, 0.4, 14, steel, MT.Metal),
					box(
						x + 1.8,
						z,
						3.4,
						2.2,
						0.15,
						if i == 1 then red elseif i == 2 then blue else yellow,
						MT.Fabric,
						10.8
					),
					ball(x, z, 0.8, yellow, MT.Metal, 14),
				}
			end)
		),
		P(
			"Car",
			"Hero Car",
			"A blue sports car with a yellow stripe.",
			cat(car(30, 40, blue, red, cyan), box(30, 40, 6.1, 0.1, 0.8, yellow, MT.Neon, 1.8))
		),
		P(
			"Jet",
			"Hero Jet",
			"A white jet with blue wings and a red nose.",
			cat(
				hcyl(44, 3.4, 26, 14, 3, "X", white, MT.Metal),
				ball(51, 26, 3, red, MT.Metal, 1.9),
				box(44, 26, 4, 0.4, 18, blue, MT.Metal, 3),
				box(38.5, 26, 2.4, 3.6, 0.4, red, MT.Metal, 4.5),
				box(38.5, 26, 2, 0.3, 6, blue, MT.Metal, 4.6),
				ball(48, 26, 2.2, cyan, MT.Glass, 4.4),
				hcyl(44, 2.4, 22, 3.4, 1.3, "X", dark, MT.Metal),
				hcyl(44, 2.4, 30, 3.4, 1.3, "X", dark, MT.Metal),
				box(47, 26, 0.5, 1.8, 0.5, dark, MT.Metal),
				box(41, 22, 0.5, 1.8, 0.5, dark, MT.Metal),
				box(41, 30, 0.5, 1.8, 0.5, dark, MT.Metal)
			)
		),
		P(
			"Course",
			"Training Course",
			"Hurdles, tyres and a balance beam on the lawn.",
			cat(
				each({ { -40, 14 }, { -40, 20 }, { -40, 26 }, { -40, 32 } }, function(x, z, i)
					return box(x, z, 0.8, 1.4, 4.4, if i % 2 == 0 then red else yellow, MT.Wood)
				end),
				each({ { -44, 38 }, { -41, 40.5 }, { -37, 38.5 } }, function(x, z)
					return cyl(x, z, 2.4, 0.8, dark, MT.Fabric)
				end),
				box(-40, 46, 1, 0.6, 8, wood, MT.Wood, 0.9),
				cyl(-40, 43, 0.8, 0.9, steel, MT.Metal),
				cyl(-40, 49, 0.8, 0.9, steel, MT.Metal)
			)
		),
		P(
			"Garage",
			"Gadget Garage",
			"A small steel workshop with a glowing sign.",
			cat(
				box(46, -12, 10, 6, 8, steel, MT.Metal),
				box(46, -7.9, 6, 4, 0.3, dark, MT.CorrodedMetal),
				box(46, -12, 11, 0.6, 9, red, MT.SmoothPlastic, 6),
				box(46, -7.8, 6.4, 0.5, 0.3, yellow, MT.Neon, 4.6),
				cyl(43, -14, 1.6, 0.8, dark, MT.Metal, 6.6),
				lamp(41, -6, 4, yellow, dark)
			)
		),
		P(
			"Trophies",
			"Trophy Pedestals",
			"Three golden cups on stone pedestals.",
			each({ { 14, -46 }, { 18, -46 }, { 22, -46 } }, function(x, z)
				return {
					box(x, z, 2.4, 1.6, 2.4, steel, MT.Granite),
					cyl(x, z, 1.8, 2, yellow, MT.Metal, 1.6),
					ball(x, z, 1.2, yellow, MT.Metal, 3.6),
				}
			end)
		),
		P(
			"Pennants",
			"Hero Pennants",
			"Five banners on poles along the path.",
			line(5, 9, 16, 9, 48, function(x, z, i)
				return {
					cyl(x, z, 0.3, 7, steel, MT.Metal),
					box(x, z + 1.1, 0.15, 3.2, 1.8, if i % 2 == 0 then red else blue, MT.Fabric, 3.5),
				}
			end)
		),
		P(
			"Lamps",
			"Plaza Lamps",
			"Four tall lamp posts around the plaza.",
			each({ { 26, -10 }, { 26, 6 }, { 42, 6 }, { 12, 6 } }, function(x, z)
				return lamp(x, z, 6, yellow, steel)
			end)
		),
		P(
			"Garden",
			"Hero Garden",
			"Three trees and two flower beds on the lawn.",
			cat(
				tree(-44, -30, 9, RGB(70, 150, 70), wood),
				tree(-36, -42, 8, RGB(80, 160, 70), wood),
				tree(-46, -12, 9, RGB(70, 150, 70), wood),
				inlay(-40, -20, 8, 6, red, MT.Grass),
				inlay(-30, -50, 8, 5, yellow, MT.Grass)
			)
		),
		P(
			"FloatingEmblem",
			"Floating Hero Emblem",
			"A giant glowing emblem floating above the tower with four orbiting lights.",
			cat(
				blk(40, 62, -40, 2, 18, 18, yellow, MT.Neon, V3(45, 0, 0)),
				blk(40, 62, -40, 2.4, 12, 12, red, MT.Neon, V3(45, 0, 0)),
				blk(40, 62, -40, 2.8, 6, 6, blue, MT.Neon, V3(45, 0, 0)),
				ball(40, -40, 4, white, MT.Neon, 60),
				ball(40, -53.5, 3, yellow, MT.Neon, 60.5),
				ball(40, -26.5, 3, yellow, MT.Neon, 60.5),
				ball(40, -40, 3, yellow, MT.Neon, 74),
				ball(40, -40, 3, yellow, MT.Neon, 47)
			)
		),
	})
end

-- 16 Gold Shiba: Vault. Steel room x 16..58, z -62..-26 with a doorway in the west wall; the round door hangs open outside.
do
	local h = 66
	local steel, dark = RGB(130, 138, 150), RGB(70, 76, 88)
	local gold, goldB, red = RGB(255, 200, 40), RGB(240, 180, 30), RGB(255, 40, 40)
	local cyan, green, silver = RGB(120, 235, 255), RGB(60, 160, 80), RGB(190, 196, 208)
	local function goldStack(cx: number, z: number): { Piece }
		local out: { Piece } = {}
		for row = 0, 3 do
			local count = 4 - row
			for i = 0, count - 1 do
				local x = cx + (i - (count - 1) / 2) * 2.4
				table.insert(
					out,
					box(x, z, 2.3, 0.8, 1.3, if (i + row) % 2 == 0 then gold else goldB, MT.Metal, row * 0.8)
				)
			end
		end
		return out
	end
	local function pile(x: number, z: number): { Piece }
		return {
			mk(PT.Ball, x, 0.9, z, 5, 1.8, 5, gold, MT.Metal, nil),
			mk(PT.Ball, x + 2.4, 0.6, z + 0.8, 2.8, 1.2, 2.8, goldB, MT.Metal, nil),
			cyl(x - 1, z + 2.4, 1.4, 0.2, gold, MT.Metal),
			cyl(x + 1.4, z - 2.6, 1.4, 0.2, goldB, MT.Metal),
		}
	end
	themes[16] = build("GoldVault", "Vault", h, 900, {
		P(
			"Flooring",
			"Vault Floor",
			"Dark diamond-plate steel with a polished vault floor and gold edging.",
			cat(
				floorSlabs(h, RGB(60, 64, 74), MT.DiamondPlate, RGB(85, 90, 100), MT.DiamondPlate),
				inlay(37.5, -44, 40, 34, RGB(30, 32, 40), MT.Metal),
				inlay(37.5, -27.8, 40, 0.8, gold, MT.Metal),
				inlay(37.5, -60.2, 40, 0.8, gold, MT.Metal)
			)
		),
		P(
			"Walls",
			"Vault Walls",
			"Thick steel walls with a doorway facing the path.",
			cat(
				box(37, -62, 42, 12, 2, steel, MT.Metal),
				box(37, -26, 42, 12, 2, steel, MT.Metal),
				box(58, -44, 2, 12, 36, steel, MT.Metal),
				box(16, -55, 2, 12, 14, steel, MT.Metal),
				box(16, -33, 2, 12, 14, steel, MT.Metal)
			)
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A dark steel board with gold neon lettering.",
			sign(24, 58, 18, dark, gold, steel)
		),
		P(
			"Ceiling",
			"Vault Ceiling",
			"A heavy steel roof with a gold edge and three vents.",
			cat(
				box(37, -44, 44, 1.5, 38, dark, MT.Metal, 12),
				box(37, -44, 44.4, 0.4, 38.4, gold, MT.Metal, 11.7),
				each({ { 28, -44 }, { 37, -44 }, { 46, -44 } }, function(x, z)
					return cyl(x, z, 2, 1.2, steel, MT.Metal, 13.5)
				end)
			)
		),
		P(
			"DoorFrame",
			"Door Frame",
			"A thick steel frame around the doorway with gold trim.",
			cat(
				box(16, -48.8, 3, 12, 1.6, dark, MT.Metal),
				box(16, -39.2, 3, 12, 1.6, dark, MT.Metal),
				box(16, -44, 3, 2, 10, dark, MT.Metal, 10),
				box(14.4, -44, 0.3, 0.4, 10, gold, MT.Metal, 10.3),
				box(14.4, -48.8, 0.3, 10, 0.4, gold, MT.Metal),
				box(14.4, -39.2, 0.3, 10, 0.4, gold, MT.Metal)
			)
		),
		P(
			"Door",
			"Round Vault Door",
			"A huge round steel door swung open against the wall.",
			cat(
				hcyl(13.9, 5, -54, 1.8, 9, "X", silver, MT.Metal),
				hcyl(13.8, 5, -54, 2, 6.2, "X", RGB(120, 128, 140), MT.Metal),
				hcyl(13.7, 5, -54, 2.2, 2.2, "X", gold, MT.Metal),
				box(14.4, -49.2, 1.6, 1.2, 0.8, dark, MT.Metal, 1.4),
				box(14.4, -49.2, 1.6, 1.2, 0.8, dark, MT.Metal, 7.4)
			)
		),
		P(
			"Wheel",
			"Door Wheel and Bolts",
			"A gold turning wheel in the middle of the door, ringed by bolts.",
			cat(
				hcyl(12.7, 5, -54, 0.6, 4.4, "X", gold, MT.Metal),
				blk(12.45, 5, -54, 0.3, 4.2, 0.5, gold, MT.Metal),
				blk(12.45, 5, -54, 0.3, 0.5, 4.2, gold, MT.Metal),
				ball(12.3, -54, 1.2, gold, MT.Metal, 4.4),
				ball(13, -54, 0.8, dark, MT.Metal, 8),
				ball(13, -54, 0.8, dark, MT.Metal, 1.6),
				ball(13, -57.2, 0.8, dark, MT.Metal, 4.6),
				ball(13, -50.8, 0.8, dark, MT.Metal, 4.6)
			)
		),
		P("StackOne", "Gold Bar Stack One", "A pyramid of ten gold bars.", goldStack(26, -58)),
		P("StackTwo", "Gold Bar Stack Two", "A second pyramid of gold bars.", goldStack(37, -58)),
		P("StackThree", "Gold Bar Stack Three", "A third pyramid of gold bars.", goldStack(48, -58)),
		P(
			"Coins",
			"Gold Coin Piles",
			"Three heaps of glittering coins.",
			cat(pile(30, -34), pile(46, -34), pile(52, -52))
		),
		P(
			"LaserGrid",
			"Laser Grid",
			"Red lasers crossing the vault floor.",
			cat(
				each({ { 22.5, 1.2 }, { 28, 2.6 }, { 46, 1.2 }, { 52, 2.6 } }, function(x, y)
					return hcyl(x, y, -47, 26, 0.2, "Z", red, MT.Neon)
				end),
				hcyl(37, 1.8, -34, 34, 0.2, "X", red, MT.Neon),
				hcyl(37, 1.8, -54, 34, 0.2, "X", red, MT.Neon)
			)
		),
		P(
			"Emitters",
			"Laser Emitters",
			"Little boxes on the back wall that shoot the lasers.",
			each({ { 22.5, 0.6 }, { 28, 2 }, { 46, 0.6 }, { 52, 2 } }, function(x, y0)
				return { box(x, -60.2, 1.2, 1.2, 1, dark, MT.Metal, y0), ball(x, -59.5, 0.6, red, MT.Neon, y0 + 0.3) }
			end)
		),
		P(
			"Cameras",
			"Security Cameras",
			"Four cameras with red lights in the corners of the room.",
			each({ { 18, -28 }, { 56, -28 }, { 18, -60 }, { 56, -60 } }, function(x, z)
				return {
					box(x, z, 0.4, 1, 0.4, dark, MT.Metal, 11),
					box(x, z, 0.8, 0.8, 1.6, dark, MT.Metal, 10.4),
					ball(x, z, 0.5, red, MT.Neon, 10.5),
				}
			end)
		),
		P(
			"SafeBoxes",
			"Safe Deposit Boxes",
			"A wall of nine small safe doors.",
			cat(
				box(56.6, -44, 0.8, 6.4, 17, dark, MT.Metal, 0.4),
				each({
					{ -49, 0.8 },
					{ -44, 0.8 },
					{ -39, 0.8 },
					{ -49, 2.8 },
					{ -44, 2.8 },
					{ -39, 2.8 },
					{ -49, 4.8 },
					{ -44, 4.8 },
					{ -39, 4.8 },
				}, function(z, y0)
					return box(56.1, z, 0.3, 1.6, 4.8, silver, MT.Metal, y0)
				end)
			)
		),
		P(
			"Desk",
			"Guard Desk",
			"A desk with three glowing monitors and a chair.",
			cat(
				box(22, -30, 8, 1.4, 2.4, dark, MT.Metal),
				box(22, -30, 8.4, 0.2, 2.8, steel, MT.Metal, 1.4),
				each({ { 19.5, -30.8 }, { 22, -30.8 }, { 24.5, -30.8 } }, function(x, z)
					return box(x, z, 1.8, 1.2, 0.2, cyan, MT.Neon, 1.8)
				end),
				box(22, -32.8, 1.8, 0.5, 1.8, dark, MT.Fabric, 1.2),
				box(22, -33.6, 1.8, 1.8, 0.3, dark, MT.Fabric, 1.6)
			)
		),
		P(
			"Truck",
			"Armoured Truck",
			"A heavy truck with a gold stripe and a gold back door.",
			cat(
				box(39, -14, 9, 4.4, 4.4, dark, MT.Metal, 0.8),
				box(45, -14, 3, 3.4, 4.2, steel, MT.Metal, 0.8),
				box(46.6, -14, 0.2, 1.4, 3.4, cyan, MT.Glass, 2.4),
				box(39, -14, 9.2, 0.5, 4.6, gold, MT.Metal, 3),
				box(34.4, -14, 0.2, 3.6, 3.2, gold, MT.Metal, 1.2),
				each(
					{ { 35.5, -16.4 }, { 39.5, -16.4 }, { 45, -16.4 }, { 35.5, -11.6 }, { 39.5, -11.6 }, { 45, -11.6 } },
					function(x, z)
						return hcyl(x, 0.9, z, 0.8, 1.8, "Z", RGB(30, 30, 35), MT.Metal)
					end
				)
			)
		),
		P(
			"Trolley",
			"Money Trolley",
			"A trolley stacked with cash and a gold bar.",
			cat(
				box(28, -18, 4, 0.4, 2, dark, MT.Metal, 1),
				box(25.8, -18, 0.3, 2.4, 2, dark, MT.Metal, 1),
				each({ { 27.2, -18.6 }, { 28.6, -18.6 }, { 27.2, -17.4 }, { 28.6, -17.4 } }, function(x, z)
					return box(x, z, 1.2, 0.8, 1, green, MT.Fabric, 1.4)
				end),
				box(27.9, -18, 2.3, 0.8, 1.2, gold, MT.Metal, 2.2),
				hcyl(26.8, 0.5, -18.9, 0.4, 1, "Z", dark, MT.Metal),
				hcyl(29.2, 0.5, -18.9, 0.4, 1, "Z", dark, MT.Metal)
			)
		),
		P(
			"BoneStatue",
			"Golden Bone Statue",
			"A giant golden bone on a steel pedestal.",
			cat(
				box(24, 12, 5, 2, 5, steel, MT.Granite),
				hcyl(24, 3.6, 12, 7, 1.4, "X", gold, MT.Metal),
				ball(20.5, 11.2, 2.2, gold, MT.Metal, 2.5),
				ball(20.5, 12.8, 2.2, gold, MT.Metal, 2.5),
				ball(27.5, 11.2, 2.2, gold, MT.Metal, 2.5),
				ball(27.5, 12.8, 2.2, gold, MT.Metal, 2.5),
				box(21.4, 12, 0.2, 1, 3, gold, MT.Neon, 0.8)
			)
		),
		P(
			"Pillars",
			"Golden Pillars",
			"Four gold pillars flanking the entrance.",
			each({ { 11, -60 }, { 11, -49 }, { 11, -39 }, { 11, -30 } }, function(x, z)
				return {
					box(x, z, 2.4, 0.8, 2.4, dark, MT.Granite),
					cyl(x, z, 2, 11, gold, MT.Metal, 0.8),
					ball(x, z, 2.8, gold, MT.Metal, 11.8),
				}
			end)
		),
		P(
			"DiamondStand",
			"Diamond Pedestal",
			"A velvet pedestal under a glass case with four rope posts.",
			cat(
				cyl(37, -44, 5, 2.5, steel, MT.Marble),
				cyl(37, -44, 4, 0.3, red, MT.Fabric, 2.5),
				box(37, -44, 3, 3, 3, cyan, MT.Glass, 2.8),
				blk(37, 4.3, -44, 1.4, 1.4, 1.4, cyan, MT.Neon, V3(45, 0, 45)),
				each({ { 33.4, -47.6 }, { 40.6, -47.6 }, { 33.4, -40.4 }, { 40.6, -40.4 } }, function(x, z)
					return cyl(x, z, 0.4, 1.4, gold, MT.Metal)
				end)
			)
		),
		P(
			"Carpet",
			"Red Carpet and Lamps",
			"A red carpet from the path to the pedestal, lit by four lamps.",
			cat(
				inlay(12, -44, 9, 6, red, MT.Fabric),
				inlay(37.5, -44, 40, 6, red, MT.Fabric),
				lamp(8.5, -47, 4, RGB(255, 245, 200), gold),
				lamp(8.5, -41, 4, RGB(255, 245, 200), gold),
				lamp(24, -47, 3.5, RGB(255, 245, 200), gold),
				lamp(24, -41, 3.5, RGB(255, 245, 200), gold)
			)
		),
		P(
			"CoinSign",
			"Giant Coin Sign",
			"A giant gold coin with a glowing dollar sign.",
			cat(
				hcyl(24, 8, 38, 1.2, 12, "Z", gold, MT.Metal),
				hcyl(24, 8, 38.1, 1.4, 9.6, "Z", goldB, MT.Metal),
				blk(24, 10.4, 38.8, 3.6, 0.7, 0.3, RGB(255, 245, 170), MT.Neon),
				blk(24, 8, 38.8, 3.6, 0.7, 0.3, RGB(255, 245, 170), MT.Neon),
				blk(24, 5.6, 38.8, 3.6, 0.7, 0.3, RGB(255, 245, 170), MT.Neon),
				blk(22.4, 9.2, 38.8, 0.7, 1.7, 0.3, RGB(255, 245, 170), MT.Neon),
				blk(25.6, 6.8, 38.8, 0.7, 1.7, 0.3, RGB(255, 245, 170), MT.Neon),
				blk(24, 8, 38.8, 0.4, 8, 0.3, RGB(255, 245, 170), MT.Neon),
				box(21, 38, 1, 2, 1, dark, MT.Metal),
				box(27, 38, 1, 2, 1, dark, MT.Metal)
			)
		),
		P(
			"Fountain",
			"Gold Fountain",
			"A golden fountain with two lamps.",
			cat(
				fountain(46, 20, 6, RGB(255, 215, 80), gold),
				lamp(38, 26, 4, RGB(255, 245, 200), gold),
				lamp(54, 26, 4, RGB(255, 245, 200), gold)
			)
		),
		P(
			"GiantDiamond",
			"Giant Diamond",
			"A huge floating diamond above the vault, ringed by six small gems.",
			cat(
				blk(37, 23, -44, 8, 8, 8, cyan, MT.Neon, V3(45, 0, 45)),
				blk(37, 23, -44, 5, 5, 5, RGB(240, 255, 255), MT.Neon, V3(45, 45, 0)),
				ring(6, 37, -44, 8, function(x, z, a)
					return blk(x, 23 + math.sin(math.rad(a * 2)) * 2, z, 1.6, 1.6, 1.6, cyan, MT.Neon, V3(45, 0, 45))
				end),
				cyl(37, -44, 1, 8, RGB(240, 255, 255), MT.Neon, 14.2)
			)
		),
	})
end

-- 17 Wizard Shiba: Wizard Tower. Round tower at (40, -42) on a rune circle.
do
	local h = 69
	local stone, dark, blue = RGB(95, 85, 150), RGB(50, 40, 90), RGB(60, 70, 180)
	local glow, gold, cyan = RGB(200, 90, 255), RGB(255, 210, 70), RGB(100, 230, 255)
	local wood, green = RGB(90, 60, 40), RGB(100, 255, 140)
	local function mushroom(x: number, z: number, s: number): { Piece }
		return {
			cyl(x, z, 0.8 * s, 1.4 * s, RGB(240, 230, 210), MT.SmoothPlastic),
			mk(PT.Ball, x, 1.4 * s + 0.5 * s, z, 3 * s, 1.8 * s, 3 * s, glow, MT.SmoothPlastic, nil),
		}
	end
	themes[17] = build("WizardTower", "Wizard Tower", h, 900, {
		P(
			"Flooring",
			"Rune Floor",
			"Purple slate with a glowing rune circle around the tower.",
			cat(
				floorSlabs(h, RGB(60, 55, 110), MT.Slate, RGB(75, 70, 125), MT.Slate),
				cyl(40, -42, 26, 0.1, glow, MT.Neon, 0.2),
				cyl(40, -42, 24.6, 0.15, dark, MT.Slate, 0.2),
				cyl(40, -42, 18.6, 0.1, cyan, MT.Neon, 0.2)
			)
		),
		P(
			"Base",
			"Tower Base",
			"A wide round base with four stone buttresses.",
			cat(
				cyl(40, -42, 18, 8, stone, MT.Slate),
				cyl(40, -42, 18.6, 1, dark, MT.Slate, 7.5),
				ring(4, 40, -42, 9.5, function(x, z, a)
					return blk(x, 3, z, 2, 6, 2, dark, MT.Slate, V3(0, -a, 0))
				end)
			)
		),
		P("Sign", "Get Bonked Sign", "A purple board with magical neon lettering.", sign(22, 60, 18, dark, glow, wood)),
		P(
			"Shaft",
			"Tower Shaft",
			"A tall slim shaft with three dark bands.",
			cat(
				cyl(40, -42, 12, 18, stone, MT.Slate, 8),
				cyl(40, -42, 12.6, 0.8, dark, MT.Slate, 12),
				cyl(40, -42, 12.6, 0.8, dark, MT.Slate, 18),
				cyl(40, -42, 12.6, 0.8, dark, MT.Slate, 24)
			)
		),
		P(
			"Chamber",
			"Upper Chamber",
			"A wider room at the top with a balcony and a railing.",
			cat(
				cyl(40, -42, 16, 6, blue, MT.Slate, 26),
				cyl(40, -42, 19, 0.8, dark, MT.Slate, 26),
				ring(8, 40, -42, 9.2, function(x, z)
					return cyl(x, z, 0.4, 1.4, gold, MT.Metal, 26.8)
				end)
			)
		),
		P(
			"Roof",
			"Pointed Roof",
			"A tall stepped pointed roof with a glowing tip.",
			cat(
				cyl(40, -42, 15, 3, dark, MT.Slate, 32),
				cyl(40, -42, 12, 3, blue, MT.Slate, 35),
				cyl(40, -42, 9, 3, dark, MT.Slate, 38),
				cyl(40, -42, 6, 3, blue, MT.Slate, 41),
				cyl(40, -42, 3.5, 3, dark, MT.Slate, 44),
				ball(40, -42, 1.8, glow, MT.Neon, 47)
			)
		),
		P(
			"Stars",
			"Roof Stars",
			"Golden stars dotted across the roof.",
			cat(
				ring(5, 40, -42, 7.3, function(x, z)
					return ball(x, z, 0.9, gold, MT.Neon, 33.2)
				end),
				ring(4, 40, -42, 5, function(x, z)
					return ball(x, z, 0.9, gold, MT.Neon, 39)
				end),
				blk(40, 49.4, -42, 1.8, 1.8, 1.8, gold, MT.Neon, V3(45, 45, 0))
			)
		),
		P(
			"Windows",
			"Windows and Door",
			"A wooden door at the foot of the tower and glowing windows above.",
			cat(
				box(31, -42, 0.4, 5, 3.2, wood, MT.Wood),
				box(30.8, -42, 0.3, 0.5, 4, gold, MT.Metal, 5),
				box(34, -42, 0.3, 3, 1.6, cyan, MT.Neon, 14),
				box(34, -42, 0.3, 3, 1.6, cyan, MT.Neon, 20),
				box(32.1, -42, 0.3, 3, 2, cyan, MT.Neon, 28),
				box(31.9, -42, 0.3, 0.5, 2, gold, MT.Metal, 31.5)
			)
		),
		P(
			"Stair",
			"Spiral Stair",
			"Stone steps winding up around the tower.",
			ring(12, 40, -42, 7.5, function(x, z, a)
				return blk(x, 8.3 + a / 30 * 1.2, z, 3, 0.6, 1.6, stone, MT.Slate, V3(0, -a, 0))
			end)
		),
		P(
			"CrystalBall",
			"Crystal Ball",
			"A glowing ball on a golden stand.",
			cat(
				cyl(22, -18, 4, 0.6, dark, MT.Slate),
				cyl(22, -18, 1.4, 1.6, gold, MT.Metal, 0.6),
				cyl(22, -18, 2.6, 0.4, gold, MT.Metal, 2.2),
				ball(22, -18, 3.2, glow, MT.Neon, 2.6)
			)
		),
		P(
			"Circle",
			"Magic Circle",
			"A glowing circle with a three-line star on the lawn.",
			cat(
				cyl(24, 22, 12, 0.1, glow, MT.Neon, 0.2),
				cyl(24, 22, 11, 0.15, dark, MT.Slate, 0.2),
				blk(24, 0.36, 22, 11, 0.1, 0.5, cyan, MT.Neon, V3(0, 0, 0)),
				blk(24, 0.36, 22, 11, 0.1, 0.5, cyan, MT.Neon, V3(0, 60, 0)),
				blk(24, 0.36, 22, 11, 0.1, 0.5, cyan, MT.Neon, V3(0, 120, 0)),
				ball(24, 22, 1, glow, MT.Neon, 0.3)
			)
		),
		P(
			"Books",
			"Floating Books",
			"Five spell books hovering in the air.",
			each({ { 18, 14 }, { 22, 18 }, { 27, 12 }, { 31, 17 }, { 25, 22 } }, function(x, z, i)
				return blk(
					x,
					5 + i * 0.9,
					z,
					1.6,
					0.4,
					2.2,
					if i % 2 == 0 then RGB(150, 40, 60) else RGB(40, 90, 170),
					MT.Fabric,
					V3(20 * i, 30 * i, 15)
				)
			end)
		),
		P(
			"Cauldron",
			"Bubbling Cauldron",
			"A black cauldron on three legs with green potion and bubbles.",
			cat(
				cyl(44, 22, 5, 2.8, RGB(35, 35, 40), MT.Metal, 1),
				cyl(44, 22, 4.2, 0.2, green, MT.Neon, 3.7),
				each({ { 42.4, 20.8 }, { 45.6, 20.8 }, { 44, 23.6 } }, function(x, z)
					return box(x, z, 0.6, 1, 0.6, RGB(35, 35, 40), MT.Metal)
				end),
				ball(43, 21.5, 0.9, green, MT.Neon, 4.6),
				ball(45, 22.5, 0.7, green, MT.Neon, 5.4),
				ball(44, 22, 0.6, green, MT.Neon, 6.4)
			)
		),
		P(
			"Shelf",
			"Potion Shelf",
			"A shelf of colourful glowing potions.",
			cat(
				box(46, 38, 0.4, 5, 1.2, wood, MT.Wood),
				box(54, 38, 0.4, 5, 1.2, wood, MT.Wood),
				box(50, 38, 8.4, 0.3, 1.2, wood, MT.Wood, 1),
				box(50, 38, 8.4, 0.3, 1.2, wood, MT.Wood, 2.8),
				box(50, 38, 8.4, 0.3, 1.2, wood, MT.Wood, 4.6),
				each(
					{ { 48, 1.3 }, { 50, 1.3 }, { 52, 1.3 }, { 48.5, 3.1 }, { 51.5, 3.1 }, { 50, 4.9 } },
					function(x, y0)
						return ball(x, 38, 1, if x > 50 then cyan else glow, MT.Neon, y0)
					end
				)
			)
		),
		P(
			"Mushrooms",
			"Glowing Mushrooms",
			"Four giant purple mushrooms.",
			cat(mushroom(16, 44, 1.2), mushroom(19, 47, 1.6), mushroom(14, 48, 1), mushroom(21, 43, 0.9))
		),
		P(
			"Trees",
			"Enchanted Trees",
			"Three twisted purple trees with glowing fruit.",
			cat(
				tree(-40, -40, 10, RGB(130, 70, 190), wood),
				tree(-46, -28, 9, RGB(110, 60, 180), wood),
				tree(-36, -48, 9, RGB(130, 70, 190), wood),
				ball(-38, -40, 0.9, cyan, MT.Neon, 7),
				ball(-44.5, -28, 0.9, cyan, MT.Neon, 6.5),
				ball(-34.5, -48, 0.9, cyan, MT.Neon, 6.5)
			)
		),
		P(
			"Candles",
			"Floating Candles",
			"Five candles hovering around the tower.",
			ring(5, 40, -42, 12.5, function(x, z, a)
				local y = 5 + a / 36
				return {
					cyl(x, z, 0.5, 1.2, RGB(245, 240, 225), MT.SmoothPlastic, y),
					ball(x, z, 0.7, gold, MT.Neon, y + 1.2),
				}
			end)
		),
		P(
			"Owl",
			"Owl Perch",
			"A wise owl sitting on a wooden perch.",
			cat(
				cyl(30, -10, 0.6, 5, wood, MT.Wood),
				box(30, -10, 0.4, 0.4, 3, wood, MT.Wood, 4.6),
				ball(30, -10, 2, RGB(140, 100, 70), MT.Fabric, 5),
				ball(30, -10, 1.4, RGB(150, 110, 80), MT.Fabric, 6.8),
				ball(29.4, -10.4, 0.5, gold, MT.Neon, 7.2),
				ball(29.4, -9.6, 0.5, gold, MT.Neon, 7.2),
				box(30, -11.2, 1.4, 0.2, 0.8, RGB(110, 80, 55), MT.Fabric, 5.6),
				box(30, -8.8, 1.4, 0.2, 0.8, RGB(110, 80, 55), MT.Fabric, 5.6)
			)
		),
		P(
			"WizardStatue",
			"Wizard Statue",
			"A statue of an old wizard with a pointed hat, a beard and a glowing staff.",
			cat(
				box(12, -22, 3.4, 1, 3.4, dark, MT.Slate),
				person(12, -22, 1.2, blue, dark, RGB(240, 210, 180)),
				cyl(12, -22, 3.4, 0.3, blue, MT.Fabric, 6.2),
				cyl(12, -22, 2.2, 1.6, blue, MT.Fabric, 6.5),
				cyl(12, -22, 1, 1.6, blue, MT.Fabric, 8.1),
				box(10.9, -22, 0.4, 1.8, 0.8, RGB(235, 235, 240), MT.Fabric, 5.4),
				cyl(14.2, -22, 0.3, 7, wood, MT.Wood, 1),
				ball(14.2, -22, 1.2, glow, MT.Neon, 8)
			)
		),
		P(
			"Broom",
			"Flying Broomstick",
			"A broomstick floating above the ground with sparkles behind it.",
			cat(
				blk(30, 3, 28, 7, 0.3, 0.3, wood, MT.Wood, V3(0, 20, 12)),
				blk(33.5, 3.9, 27.2, 2.2, 1, 1, RGB(200, 170, 80), MT.Fabric, V3(0, 20, 12)),
				ball(26, 29, 0.6, gold, MT.Neon, 2.5),
				ball(25, 28, 0.5, cyan, MT.Neon, 3.2),
				ball(24.2, 29.5, 0.4, glow, MT.Neon, 2.8),
				ball(27, 30, 0.4, gold, MT.Neon, 3.6)
			)
		),
		P(
			"Lectern",
			"Spell Book Lectern",
			"A big glowing spell book on a wooden lectern.",
			cat(
				cyl(46, 10, 1, 3, wood, MT.Wood),
				box(46, 10, 3, 0.4, 2.4, wood, MT.Wood, 3),
				blk(46, 3.9, 10, 2.6, 0.3, 2, RGB(150, 40, 60), MT.Fabric, V3(0, 0, 0)),
				box(46, 10, 2.2, 0.15, 1.6, cyan, MT.Neon, 4.1),
				ball(46, 10, 0.6, gold, MT.Neon, 5.2)
			)
		),
		P(
			"Obelisks",
			"Arcane Obelisks",
			"Three dark stone obelisks with glowing runes.",
			each({ { 20, -54 }, { 60, -54 }, { 40, -64 } }, function(x, z)
				return {
					box(x, z, 2, 10, 2, dark, MT.Slate),
					box(x - 1.05, z, 0.1, 5, 0.8, glow, MT.Neon, 2.5),
					ball(x, z, 1.4, cyan, MT.Neon, 10),
				}
			end)
		),
		P(
			"Rocks",
			"Floating Rocks",
			"Five rocks drifting in the air with three crystals.",
			cat(
				each({
					{ -20, -30, 16, 5 },
					{ -26, -26, 21, 4 },
					{ -14, -36, 19, 3.4 },
					{ -30, -38, 14, 3 },
					{ -22, -42, 24, 2.6 },
				}, function(x, z, i)
					return ball(x, z, 2 + i * 0.5, RGB(120, 110, 160), MT.Slate, 9 + i * 2.5)
				end),
				ball(-20, -30, 1.2, cyan, MT.Neon, 21),
				ball(-26, -26, 1.2, cyan, MT.Neon, 25.5),
				ball(-14, -36, 1.2, glow, MT.Neon, 23)
			)
		),
		P(
			"Banners",
			"Star Banners",
			"Four poles along the path with star banners.",
			line(4, 9, 14, 9, 46, function(x, z)
				return {
					cyl(x, z, 0.3, 7, gold, MT.Metal),
					box(x, z + 1.1, 0.15, 3.2, 1.8, blue, MT.Fabric, 3.5),
					ball(x + 0.2, z + 1.1, 0.8, gold, MT.Neon, 4.8),
				}
			end)
		),
		P(
			"ArcaneBeam",
			"Arcane Beam",
			"A violet beam of magic shooting from the roof tip, ringed by six cyan orbs and topped with a star.",
			cat(
				cyl(40, -42, 2, 22, glow, MT.Neon, 48.8),
				cyl(40, -42, 4, 22, RGB(230, 170, 255), MT.Neon, 48.8),
				ring(6, 40, -42, 6, function(x, z, a)
					return ball(x, z, 1.6, cyan, MT.Neon, 52 + a / 30)
				end),
				blk(40, 73, -42, 4, 4, 4, gold, MT.Neon, V3(45, 45, 0))
			)
		),
	})
end

-- 18 Vampire Shiba: Vampire Crypt. Crypt hall at (42, -44) with the gothic gate on its west face (x = 30).
do
	local h = 72
	local black, stone, crim = RGB(35, 32, 42), RGB(70, 66, 82), RGB(150, 15, 35)
	local blood, bone, iron = RGB(255, 30, 50), RGB(225, 215, 200), RGB(30, 30, 36)
	local wood, moon, purple = RGB(70, 45, 35), RGB(240, 235, 205), RGB(80, 50, 110)
	local function gargoyle(x: number, z: number): { Piece }
		return {
			box(x, z, 1.8, 1.6, 1.8, stone, MT.Slate, 10.8),
			ball(x, z, 1.2, stone, MT.Slate, 12.4),
			blk(x - 1.2, 12, z, 1.6, 0.2, 1.2, iron, MT.Slate, V3(0, 0, 30)),
			blk(x + 1.2, 12, z, 1.6, 0.2, 1.2, iron, MT.Slate, V3(0, 0, -30)),
		}
	end
	local function bat(x: number, y: number, z: number): { Piece }
		return {
			blk(x, y, z, 0.8, 0.6, 0.8, iron, MT.Fabric),
			blk(x - 0.9, y, z, 1.4, 0.1, 0.9, iron, MT.Fabric, V3(0, 0, 25)),
			blk(x + 0.9, y, z, 1.4, 0.1, 0.9, iron, MT.Fabric, V3(0, 0, -25)),
		}
	end
	local function fog(x: number, z: number, sx: number, sz: number): Piece
		return mk(PT.Ball, x, 0.6, z, sx, 1.2, sz, RGB(200, 200, 215), MT.SmoothPlastic, nil)
	end
	local function pillar(x: number, z: number): { Piece }
		return {
			box(x, z, 2.6, 1, 2.6, stone, MT.Slate),
			box(x, z, 2, 7, 2, black, MT.Cobblestone, 1),
			ball(x, z, 2.4, stone, MT.Slate, 8),
			cyl(x, z, 0.3, 2.4, iron, MT.Metal, 10.4),
		}
	end
	local function deadTree(x: number, z: number): { Piece }
		return {
			cyl(x, z, 1, 7, iron, MT.Wood),
			blk(x + 1.2, 6.5, z, 0.4, 3.4, 0.4, iron, MT.Wood, V3(0, 0, -40)),
			blk(x - 1.2, 5.5, z, 0.4, 3, 0.4, iron, MT.Wood, V3(0, 0, 40)),
		}
	end
	themes[18] = build("VampireCrypt", "Vampire Crypt", h, 950, {
		P(
			"Flooring",
			"Crypt Floor",
			"Dark grass, cobbled ground, a crimson carpet to the gate and muddy graves.",
			cat(
				floorSlabs(h, RGB(40, 60, 45), MT.Grass, RGB(55, 50, 65), MT.Cobblestone),
				inlay(19, -44, 23, 4, crim, MT.Fabric),
				inlay(-35, -20, 16, 12, RGB(50, 40, 35), MT.Pebble),
				inlay(-35, 20, 16, 12, RGB(50, 40, 35), MT.Pebble),
				inlay(42, -44, 26, 20, RGB(30, 28, 38), MT.Slate)
			)
		),
		P(
			"Hall",
			"Crypt Hall",
			"A black stone hall on a plinth with four buttresses.",
			cat(
				box(42, -44, 25, 1, 19, stone, MT.Slate),
				box(42, -44, 24, 10, 18, black, MT.Cobblestone, 1),
				each({ { 30, -53 }, { 54, -53 }, { 30, -35 }, { 54, -35 } }, function(x, z)
					return box(x, z, 2, 11, 2, stone, MT.Slate)
				end)
			)
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A black board with blood-red neon lettering.",
			sign(26, 62, 18, black, blood, iron)
		),
		P(
			"Roof",
			"Crypt Roof",
			"A stepped dark roof with a crimson edge.",
			cat(
				box(42, -44, 26.4, 0.4, 20.4, crim, MT.Slate, 9.7),
				box(42, -44, 26, 0.8, 20, black, MT.Slate, 10),
				box(42, -44, 22, 0.8, 16, black, MT.Slate, 10.8),
				box(42, -44, 18, 0.8, 12, black, MT.Slate, 11.6),
				box(42, -44, 14, 0.8, 8, black, MT.Slate, 12.4),
				box(42, -44, 10, 0.8, 5, crim, MT.Slate, 13.2)
			)
		),
		P(
			"Gate",
			"Gothic Gate",
			"A pointed arch gate with a dark red door.",
			cat(
				box(29.4, -47.8, 1.6, 8, 1.6, black, MT.Cobblestone),
				box(29.4, -40.2, 1.6, 8, 1.6, black, MT.Cobblestone),
				blk(29.2, 8.6, -45.2, 0.8, 4.4, 0.9, black, MT.Cobblestone, V3(40, 0, 0)),
				blk(29.2, 8.6, -42.8, 0.8, 4.4, 0.9, black, MT.Cobblestone, V3(-40, 0, 0)),
				box(29.7, -44, 0.3, 6.6, 4.2, RGB(90, 15, 25), MT.Wood),
				ball(29.5, -43.2, 0.5, bone, MT.Metal, 3),
				ball(29.5, -44.8, 0.5, bone, MT.Metal, 3)
			)
		),
		P(
			"Fence",
			"Iron Fences",
			"Black iron fences around the graveyard and the front garden.",
			cat(fence(-50, -30, -20, iron, MT.Metal), fence(14, 26, 22, iron, MT.Metal))
		),
		P(
			"Graves",
			"Gravestones",
			"Eight crooked gravestones and two crosses.",
			cat(
				each({
					{ -44, -30 },
					{ -40, -26 },
					{ -36, -32 },
					{ -32, -26 },
					{ -42, -16 },
					{ -34, -14 },
					{ -44, 14 },
					{ -38, 18 },
				}, function(x, z, i)
					return blk(
						x,
						1.3,
						z,
						1.8,
						2.4,
						0.6,
						RGB(110, 108, 118),
						MT.Slate,
						V3(0, i * 20, if i % 2 == 0 then 4 else -4)
					)
				end),
				box(-30, -34, 0.6, 3.2, 0.6, RGB(110, 108, 118), MT.Slate),
				box(-30, -34, 2, 0.6, 0.6, RGB(110, 108, 118), MT.Slate, 2),
				box(-46, 20, 0.6, 3.2, 0.6, RGB(110, 108, 118), MT.Slate),
				box(-46, 20, 2, 0.6, 0.6, RGB(110, 108, 118), MT.Slate, 2)
			)
		),
		P(
			"DeadTrees",
			"Dead Trees",
			"Three bare black trees.",
			cat(deadTree(-44, -40), deadTree(-34, -48), deadTree(-46, -10))
		),
		P(
			"Altar",
			"Coffin Altar",
			"A stone slab with four candles.",
			cat(
				box(22, -30, 8, 0.8, 4, stone, MT.Slate),
				each({ { 18.4, -28.2 }, { 25.6, -28.2 }, { 18.4, -31.8 }, { 25.6, -31.8 } }, function(x, z)
					return {
						cyl(x, z, 0.5, 1.2, bone, MT.SmoothPlastic, 0.8),
						ball(x, z, 0.6, RGB(255, 150, 50), MT.Neon, 2),
					}
				end)
			)
		),
		P(
			"Coffin",
			"Coffin",
			"A dark wooden coffin with a slightly open lid and a crimson cross.",
			cat(
				box(22, -30, 6, 1.2, 2.4, wood, MT.Wood, 0.8),
				blk(22.6, 2.15, -30, 6.2, 0.3, 2.6, wood, MT.Wood, V3(0, 10, 0)),
				box(22.6, -30, 2.4, 0.1, 0.5, crim, MT.Neon, 2.3),
				box(22.2, -30, 0.5, 0.1, 1.6, crim, MT.Neon, 2.3)
			)
		),
		P(
			"Belfry",
			"Bat Belfry",
			"A tall belfry tower with a red roof and a bronze bell.",
			cat(
				box(22, -56, 7, 16, 7, black, MT.Cobblestone),
				box(22, -56, 9, 1, 9, stone, MT.Slate, 16),
				each({ { 19.2, -58.8 }, { 24.8, -58.8 }, { 19.2, -53.2 }, { 24.8, -53.2 } }, function(x, z)
					return box(x, z, 1, 5, 1, stone, MT.Slate, 17)
				end),
				box(22, -56, 9, 0.8, 9, crim, MT.Slate, 22),
				box(22, -56, 7.2, 0.8, 7.2, crim, MT.Slate, 22.8),
				box(22, -56, 5.4, 0.8, 5.4, crim, MT.Slate, 23.6),
				cyl(22, -56, 0.5, 4, iron, MT.Metal, 24.4),
				cyl(22, -56, 2, 2, RGB(170, 120, 50), MT.Metal, 17)
			)
		),
		P(
			"Bats",
			"Flying Bats",
			"Four bats circling the belfry.",
			each({ { 16, -50 }, { 28, -52 }, { 18, -62 }, { 30, -60 } }, function(x, z, i)
				return bat(x, 18 + i * 1.4, z)
			end)
		),
		P(
			"Fountain",
			"Blood Fountain",
			"A fountain running with red blood, ringed by four skulls.",
			cat(
				fountain(38, -10, 5, blood, stone),
				ring(4, 38, -10, 5.4, function(x, z)
					return ball(x, z, 1, bone, MT.SmoothPlastic, 1.2)
				end)
			)
		),
		P(
			"Moon",
			"Pale Moon",
			"A huge pale moon with craters low in the sky.",
			cat(
				ball(-30, -60, 16, moon, MT.Neon, 34),
				ball(-33, -57, 3, RGB(210, 205, 170), MT.Neon, 42),
				ball(-27, -57, 2, RGB(210, 205, 170), MT.Neon, 38),
				ball(-31, -56.4, 2.4, RGB(210, 205, 170), MT.Neon, 36)
			)
		),
		P(
			"Gargoyles",
			"Gargoyles",
			"Three stone gargoyles guarding the roof corners.",
			cat(gargoyle(32, -52), gargoyle(32, -36), gargoyle(52, -52))
		),
		P(
			"Candelabras",
			"Candelabras",
			"Two tall iron candelabras beside the gate.",
			each({ { 26, -48 }, { 26, -40 } }, function(x, z)
				return {
					cyl(x, z, 0.5, 4, iron, MT.Metal),
					box(x, z, 0.3, 0.3, 2.6, iron, MT.Metal, 3.8),
					ball(x, z - 1.2, 0.7, RGB(255, 150, 50), MT.Neon, 4.1),
					ball(x, z, 0.7, RGB(255, 150, 50), MT.Neon, 4.1),
					ball(x, z + 1.2, 0.7, RGB(255, 150, 50), MT.Neon, 4.1),
				}
			end)
		),
		P(
			"Fog",
			"Creeping Fog",
			"Six low patches of grey fog.",
			cat(
				fog(-38, -12, 8, 6),
				fog(-30, -20, 7, 5),
				fog(14, -24, 8, 6),
				fog(30, -20, 8, 5),
				fog(-42, -36, 9, 6),
				fog(50, -28, 8, 6)
			)
		),
		P(
			"Hearse",
			"Haunted Hearse",
			"A black hearse with a coffin on its roof.",
			cat(car(46, 24, black, crim, RGB(70, 50, 80)), box(44.4, 24, 3.4, 0.8, 1.6, wood, MT.Wood, 3.3))
		),
		P(
			"Torches",
			"Blood Torches",
			"Six torches with red flames along the carpet.",
			each(
				{ { 12, -47.5 }, { 12, -40.5 }, { 18, -47.5 }, { 18, -40.5 }, { 24, -52 }, { 24, -36 } },
				function(x, z)
					return lamp(x, z, 5, blood, iron)
				end
			)
		),
		P(
			"Banners",
			"Crimson Banners",
			"Four crimson banners with black bat marks along the path.",
			line(4, 9, 14, 9, 50, function(x, z)
				return {
					cyl(x, z, 0.3, 7, iron, MT.Metal),
					box(x, z + 1.1, 0.15, 3.2, 1.8, crim, MT.Fabric, 3.5),
					ball(x + 0.2, z + 1.1, 0.9, iron, MT.Fabric, 4.6),
				}
			end)
		),
		P(
			"GatePillars",
			"Spiked Gate Pillars",
			"Two tall pillars with spikes at the entrance of the grounds.",
			cat(pillar(9, 66), pillar(-9, 66))
		),
		P(
			"Roses",
			"Rose Garden",
			"Three dark bushes covered in red roses.",
			each({ { 14, 10 }, { 20, 13 }, { 16, 17 } }, function(x, z)
				return {
					ball(x, z, 3, RGB(35, 70, 40), MT.Grass),
					ball(x + 0.8, z + 0.5, 0.8, blood, MT.Grass, 2.6),
					ball(x - 0.7, z - 0.3, 0.8, blood, MT.Grass, 2.4),
					ball(x + 0.2, z - 0.9, 0.8, blood, MT.Grass, 2.2),
				}
			end)
		),
		P(
			"Windows",
			"Stained Windows",
			"Glowing stained-glass windows beside the gate.",
			cat(
				box(29.7, -50.5, 0.3, 4.4, 2, purple, MT.Neon, 3),
				box(29.7, -37.5, 0.3, 4.4, 2, purple, MT.Neon, 3),
				box(29.6, -50.5, 0.2, 5, 0.4, iron, MT.Metal, 2.7),
				box(29.6, -37.5, 0.2, 5, 0.4, iron, MT.Metal, 2.7),
				box(29.6, -50.5, 0.2, 0.4, 2.6, blood, MT.Neon, 3.2),
				box(29.6, -37.5, 0.2, 0.4, 2.6, blood, MT.Neon, 3.2)
			)
		),
		P(
			"Spires",
			"Crypt Spires",
			"Four slim black spires on the roof.",
			each({ { 38, -47 }, { 46, -47 }, { 38, -41 }, { 46, -41 } }, function(x, z)
				return {
					cyl(x, z, 1.6, 7, black, MT.Cobblestone, 13.2),
					cyl(x, z, 1, 2.4, crim, MT.Slate, 20.2),
					ball(x, z, 0.8, iron, MT.Metal, 22.6),
				}
			end)
		),
		P(
			"BloodMoon",
			"Blood Moon and Bat Swarm",
			"A giant blood-red moon above the crypt with a swarm of bats and a dark halo.",
			cat(
				ball(42, -44, 22, RGB(200, 20, 40), MT.Neon, 38),
				cyl(42, -44, 28, 0.3, RGB(120, 10, 30), MT.Neon, 48),
				ring(8, 42, -44, 15, function(x, z, a)
					return ball(x, z, 1.2, iron, MT.Fabric, 44 + math.sin(math.rad(a * 3)) * 5)
				end)
			)
		),
	})
end

-- 19 Pharaoh Shiba: Pyramid. Six-tier pyramid at (44, -44), sphinx in front of it facing the path.
do
	local h = 75
	local sand, sandD, gold = RGB(225, 195, 130), RGB(190, 160, 100), RGB(255, 205, 60)
	local dark, water, green = RGB(60, 45, 35), RGB(70, 170, 200), RGB(60, 150, 60)
	local blue, wood = RGB(40, 90, 190), RGB(130, 90, 55)
	local glyph = RGB(255, 225, 120)
	local function tier(size: number, y0: number): { Piece }
		return {
			box(44, -44, size, 5, size, sand, MT.Sandstone, y0),
			box(44, -44, size + 0.4, 0.5, size + 0.4, sandD, MT.Sandstone, y0 + 4.5),
		}
	end
	local function obelisk(x: number, z: number): { Piece }
		return {
			box(x, z, 3, 1, 3, sandD, MT.Sandstone),
			box(x, z, 2.2, 8, 2.2, sand, MT.Sandstone, 1),
			box(x, z, 1.7, 5, 1.7, sand, MT.Sandstone, 9),
			box(x, z, 1.2, 1, 1.2, gold, MT.Metal, 14),
			box(x, z, 0.7, 1, 0.7, gold, MT.Metal, 15),
			box(x - 1.15, z, 0.1, 5, 0.7, glyph, MT.Neon, 3),
			box(x - 0.9, z, 0.1, 2.5, 0.5, glyph, MT.Neon, 9.5),
		}
	end
	local function palm(x: number, z: number): { Piece }
		return {
			cyl(x, z, 0.9, 8, RGB(130, 95, 60), MT.Wood),
			blk(x + 2.3, 8.2, z, 5, 0.2, 1.4, green, MT.Grass, V3(0, 0, -18)),
			blk(x - 2.3, 8.2, z, 5, 0.2, 1.4, green, MT.Grass, V3(0, 0, 18)),
			blk(x, 8.2, z + 2.3, 1.4, 0.2, 5, green, MT.Grass, V3(18, 0, 0)),
			blk(x, 8.2, z - 2.3, 1.4, 0.2, 5, green, MT.Grass, V3(-18, 0, 0)),
		}
	end
	local function stall(x: number, z: number, c: Color3): { Piece }
		return {
			box(x, z, 4, 1.2, 2, wood, MT.Wood),
			box(x - 1.8, z - 1.2, 0.3, 4, 0.3, wood, MT.Wood),
			box(x + 1.8, z - 1.2, 0.3, 4, 0.3, wood, MT.Wood),
			box(x, z - 0.8, 4.6, 0.3, 2.8, c, MT.Fabric, 3.8),
		}
	end
	local function pharaoh(x: number, z: number): { Piece }
		return {
			box(x, z, 4, 1, 4, sandD, MT.Sandstone),
			box(x, z, 3, 3, 3, sand, MT.Sandstone, 1),
			box(x, z, 2.4, 3, 1.8, sand, MT.Sandstone, 4),
			ball(x, z, 1.8, RGB(220, 170, 110), MT.Sandstone, 7),
			box(x, z, 1.4, 1.4, 1.4, blue, MT.Fabric, 8.6),
			box(x, z, 1.8, 0.4, 1.8, gold, MT.Metal, 8.4),
		}
	end
	themes[19] = build("PharaohPyramid", "Pyramid", h, 950, {
		P(
			"Flooring",
			"Desert Sand",
			"Warm desert sand with a darker sandstone road to the pyramid.",
			cat(
				floorSlabs(h, RGB(215, 185, 120), MT.Sand, RGB(225, 195, 130), MT.Sand),
				inlay(16, -44, 18, 6, sandD, MT.Sandstone),
				inlay(44, -44, 44, 44, RGB(200, 170, 110), MT.Sandstone),
				inlay(36, -12, 18, 11, sandD, MT.Sandstone)
			)
		),
		P("Tier1", "Pyramid Base", "The wide first tier of the great pyramid.", cat(tier(40, 0))),
		P("Sign", "Get Bonked Sign", "A sandstone board with golden lettering.", sign(26, 66, 18, sandD, gold, wood)),
		P("Tier2", "Second Tier", "The second sandstone tier.", cat(tier(34, 5))),
		P("Tier3", "Third Tier", "The third sandstone tier.", cat(tier(28, 10))),
		P("Tier4", "Fourth Tier", "The fourth sandstone tier.", cat(tier(22, 15))),
		P("Tier5", "Fifth Tier", "The fifth tier and a smaller sixth tier on top.", cat(tier(16, 20), tier(10, 25))),
		P(
			"Capstone",
			"Golden Capstone",
			"A glowing golden tip on top of the pyramid.",
			cat(
				box(44, -44, 6, 2, 6, gold, MT.Metal, 30),
				box(44, -44, 4, 2, 4, gold, MT.Metal, 32),
				box(44, -44, 2, 2, 2, gold, MT.Neon, 34),
				ball(44, -44, 1.4, RGB(255, 240, 160), MT.Neon, 36)
			)
		),
		P(
			"Entrance",
			"Pyramid Entrance",
			"A dark doorway framed by sandstone and gold.",
			cat(
				box(23.7, -44, 0.5, 5, 4, dark, MT.Slate),
				box(23.4, -46.4, 1, 5.4, 0.8, sandD, MT.Sandstone),
				box(23.4, -41.6, 1, 5.4, 0.8, sandD, MT.Sandstone),
				box(23.4, -44, 1, 0.8, 5.6, sandD, MT.Sandstone, 5),
				box(23.1, -44, 0.3, 0.3, 5.6, gold, MT.Metal, 5.4),
				ball(23.2, -44, 1.2, gold, MT.Neon, 5.7)
			)
		),
		P(
			"SphinxBody",
			"Sphinx Body",
			"The long lion body of the sphinx on a sandstone platform.",
			cat(
				box(36, -12, 16, 0.6, 9, sandD, MT.Sandstone),
				box(38, -12, 10, 4, 6, sand, MT.Sandstone, 0.6),
				box(41.5, -12, 5, 5.6, 6.4, sand, MT.Sandstone, 0.6)
			)
		),
		P(
			"SphinxHead",
			"Sphinx Head",
			"A human head with a striped headdress and a golden snake.",
			cat(
				box(32.4, -12, 3.6, 4, 3.6, RGB(215, 170, 115), MT.Sandstone, 4.6),
				box(32.4, -14, 4.4, 5, 1, blue, MT.Fabric, 4),
				box(32.4, -10, 4.4, 5, 1, blue, MT.Fabric, 4),
				box(32.6, -12, 4.2, 0.8, 3.4, blue, MT.Fabric, 8.6),
				box(30.5, -12, 0.3, 0.6, 2, dark, MT.Slate, 7),
				box(30.4, -12, 0.5, 1.2, 0.6, RGB(200, 155, 100), MT.Sandstone, 5.6),
				ball(30.5, -12, 0.9, gold, MT.Neon, 8.4)
			)
		),
		P(
			"SphinxPaws",
			"Paws and Necklace",
			"Two big front paws and a golden collar.",
			cat(
				box(31.2, -14, 5, 1.4, 1.8, sand, MT.Sandstone, 0.6),
				box(31.2, -10, 5, 1.4, 1.8, sand, MT.Sandstone, 0.6),
				box(33.4, -12, 0.6, 0.6, 4.6, gold, MT.Metal, 4.4),
				box(30, -14, 0.5, 0.5, 0.5, gold, MT.Neon, 1.2),
				box(30, -10, 0.5, 0.5, 0.5, gold, MT.Neon, 1.2)
			)
		),
		P("ObeliskL", "Obelisk Left", "A tall sandstone obelisk with a golden tip.", cat(obelisk(14, -26))),
		P("ObeliskR", "Obelisk Right", "A matching obelisk on the other side.", cat(obelisk(14, -62))),
		P("Palms", "Palm Trees", "Two date palms by the oasis.", cat(palm(12.5, 19), palm(27.5, 28))),
		P(
			"Oasis",
			"Oasis Pool",
			"A small pool of clear water with sandstone edging and lily pads.",
			cat(
				box(20, 24, 12, 0.3, 9, water, MT.Glass),
				box(20, 19.5, 13, 0.5, 1, sandD, MT.Sandstone),
				box(20, 28.5, 13, 0.5, 1, sandD, MT.Sandstone),
				box(13.5, 24, 1, 0.5, 8, sandD, MT.Sandstone),
				box(26.5, 24, 1, 0.5, 8, sandD, MT.Sandstone),
				cyl(18, 25, 1.4, 0.1, green, MT.Grass, 0.3),
				cyl(22, 23, 1.2, 0.1, green, MT.Grass, 0.3)
			)
		),
		P(
			"Camel",
			"Camel",
			"A sandy camel with one hump.",
			cat(
				box(44, 30, 4, 2, 1.6, RGB(200, 160, 100), MT.Fabric, 2.4),
				ball(44, 30, 1.8, RGB(200, 160, 100), MT.Fabric, 4.2),
				box(46.4, 30, 0.8, 2.6, 0.8, RGB(200, 160, 100), MT.Fabric, 3.6),
				box(47.2, 30, 1.6, 0.8, 0.8, RGB(200, 160, 100), MT.Fabric, 6),
				each({ { 42.6, 29.4 }, { 42.6, 30.6 }, { 45.4, 29.4 }, { 45.4, 30.6 } }, function(x, z)
					return box(x, z, 0.4, 2.4, 0.4, RGB(185, 145, 90), MT.Fabric)
				end),
				box(41.8, 30, 0.2, 1.4, 0.3, dark, MT.Fabric, 2.4)
			)
		),
		P(
			"Stalls",
			"Market Stalls",
			"Three market stalls with coloured awnings.",
			cat(stall(56, 10, RGB(200, 60, 50)), stall(56, 16, blue), stall(56, 22, RGB(230, 190, 60)))
		),
		P(
			"GlyphWalls",
			"Hieroglyph Walls",
			"Two low sandstone walls covered in glowing golden glyphs.",
			cat(
				box(11, 50, 1.2, 3, 16, sand, MT.Sandstone),
				box(11, 30, 1.2, 3, 12, sand, MT.Sandstone),
				each(
					{ { 10.3, 45 }, { 10.3, 48 }, { 10.3, 51 }, { 10.3, 54 }, { 10.3, 28 }, { 10.3, 32 } },
					function(x, z)
						return box(x, z, 0.1, 1.4, 0.8, glyph, MT.Neon, 0.8)
					end
				)
			)
		),
		P(
			"Avenue",
			"Pillar Avenue",
			"Six sandstone pillars lining the road to the pyramid.",
			each({ { 10, -48 }, { 10, -40 }, { 16, -48 }, { 16, -40 }, { 22, -48 }, { 22, -40 } }, function(x, z)
				return { cyl(x, z, 2, 8, sand, MT.Sandstone), box(x, z, 2.6, 0.8, 2.6, gold, MT.Metal, 8) }
			end)
		),
		P(
			"SunDisc",
			"Sun Disc",
			"A glowing golden sun disc between two posts.",
			cat(
				hcyl(54, 9, -8, 1, 10, "X", gold, MT.Neon),
				hcyl(53.6, 9, -8, 1, 7, "X", RGB(255, 235, 150), MT.Neon),
				box(54, -2.4, 1, 10, 1, sandD, MT.Sandstone),
				box(54, -13.6, 1, 10, 1, sandD, MT.Sandstone),
				box(54, -8, 1.2, 0.6, 16, gold, MT.Metal, 9.2),
				box(54, -8, 1.8, 1, 18, sandD, MT.Sandstone, 10)
			)
		),
		P(
			"Sarcophagus",
			"Golden Sarcophagus",
			"A golden coffin with a pharaoh face on a stone stand.",
			cat(
				box(28, -20, 4, 0.8, 8, sandD, MT.Sandstone),
				box(28, -20, 2.4, 1.6, 6.4, gold, MT.Metal, 0.8),
				ball(28, -22.6, 2, gold, MT.Metal, 2.2),
				box(28, -19, 1.8, 0.2, 2.4, blue, MT.Neon, 2.4),
				box(28, -17.6, 1.2, 0.2, 1.4, RGB(220, 40, 40), MT.Neon, 2.4)
			)
		),
		P(
			"Colossi",
			"Pharaoh Statues",
			"Two seated pharaoh statues guarding the entrance.",
			cat(pharaoh(18, -58), pharaoh(18, -30))
		),
		P(
			"Braziers",
			"Torch Braziers",
			"Four braziers with orange flames beside the path.",
			each({ { 8.5, -54 }, { 8.5, -34 }, { 8.5, -20 }, { 8.5, -66 } }, function(x, z)
				return {
					cyl(x, z, 0.8, 2.5, dark, MT.Metal),
					cyl(x, z, 2.2, 0.8, gold, MT.Metal, 2.5),
					ball(x, z, 1.4, RGB(255, 140, 40), MT.Neon, 3.3),
				}
			end)
		),
		P(
			"SolarBeam",
			"Solar Beam",
			"A golden beam of light shooting from the capstone to a blazing sun.",
			cat(
				cyl(44, -44, 2, 30, gold, MT.Neon, 37),
				cyl(44, -44, 4, 30, RGB(255, 235, 150), MT.Neon, 37),
				ball(44, -44, 10, RGB(255, 190, 60), MT.Neon, 66),
				ring(6, 44, -44, 9, function(x, z, a)
					return ball(x, z, 1.4, gold, MT.Neon, 66 + math.sin(math.rad(a * 2)) * 3)
				end)
			)
		),
	})
end

-- 20 Frost Shiba: Ice Palace. Palace hall at (46, -46) with the gate on its west face (x = 26).
do
	local h = 78
	local ice, deep, white = RGB(170, 225, 255), RGB(90, 150, 230), RGB(238, 244, 252)
	local glass, cyan, dark = RGB(210, 240, 255), RGB(110, 240, 255), RGB(50, 70, 100)
	local green, purple, pale = RGB(80, 255, 170), RGB(170, 100, 255), RGB(215, 240, 255)
	local pineLeaf = RGB(60, 130, 110)
	local function spire(x: number, z: number, y0: number): { Piece }
		return {
			cyl(x, z, 3, 14, ice, MT.Ice, y0),
			cyl(x, z, 2, 4, ice, MT.Ice, y0 + 14),
			cyl(x, z, 1, 3, deep, MT.Ice, y0 + 18),
			ball(x, z, 1, cyan, MT.Neon, y0 + 21),
		}
	end
	local function snowman(x: number, z: number): { Piece }
		return {
			ball(x, z, 3.2, white, MT.Snow),
			ball(x, z, 2.4, white, MT.Snow, 2.6),
			ball(x, z, 1.6, white, MT.Snow, 4.6),
			box(x - 0.9, z, 1, 0.25, 0.25, RGB(255, 140, 40), MT.SmoothPlastic, 5.2),
			ball(x - 0.7, z - 0.35, 0.3, dark, MT.SmoothPlastic, 5.6),
			ball(x - 0.7, z + 0.35, 0.3, dark, MT.SmoothPlastic, 5.6),
		}
	end
	local function snowDrift(x: number, z: number, sx: number, sz: number): Piece
		return mk(PT.Ball, x, 1.2, z, sx, 2.4, sz, white, MT.Snow, nil)
	end
	themes[20] = build("IcePalace", "Ice Palace", h, 1000, {
		P(
			"Flooring",
			"Ice Floor",
			"Fresh snow outside, a frozen courtyard and an icy road to the gate.",
			cat(
				floorSlabs(h, white, MT.Snow, RGB(160, 215, 245), MT.Ice),
				inlay(46, -46, 46, 36, RGB(200, 235, 255), MT.Ice),
				inlay(16, -46, 18, 5, RGB(215, 240, 255), MT.Ice),
				inlay(-38, 30, 14, 10, RGB(200, 235, 255), MT.Ice)
			)
		),
		P(
			"Walls",
			"Ice Walls",
			"The big ice hall of the palace with four corner buttresses.",
			cat(
				box(46, -46, 42, 1.5, 32, white, MT.Snow),
				box(46, -46, 40, 14, 30, ice, MT.Ice),
				each({ { 26, -61 }, { 66, -61 }, { 26, -31 }, { 66, -31 } }, function(x, z)
					return box(x, z, 3, 16, 3, deep, MT.Ice)
				end)
			)
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"An icy blue board with white and cyan neon lettering.",
			sign(26, 70, 18, deep, cyan, white)
		),
		P(
			"Roof",
			"Palace Roof",
			"Layered blue and icy roofs with a snow cap.",
			cat(
				box(46, -46, 42, 1, 32, deep, MT.Ice, 14),
				box(46, -46, 36, 1, 26, ice, MT.Ice, 15),
				box(46, -46, 30, 1, 20, deep, MT.Ice, 16),
				box(46, -46, 26, 0.6, 16, white, MT.Snow, 17)
			)
		),
		P(
			"Gate",
			"Main Gate",
			"A tall ice gate with a glass door and glowing edges.",
			cat(
				box(25.4, -49, 2, 10, 2, ice, MT.Ice),
				box(25.4, -43, 2, 10, 2, ice, MT.Ice),
				box(25.4, -46, 2, 2, 8, deep, MT.Ice, 10),
				box(25.7, -46, 0.4, 8, 4.4, glass, MT.Glass),
				box(24.2, -49, 0.2, 9, 0.4, cyan, MT.Neon),
				box(24.2, -43, 0.2, 9, 0.4, cyan, MT.Neon)
			)
		),
		P(
			"SpiresWest",
			"Front Spires",
			"Two tall ice spires on the front corners.",
			cat(spire(26, -61, 16), spire(26, -31, 16))
		),
		P(
			"SpiresEast",
			"Back Spires",
			"Two tall ice spires on the back corners.",
			cat(spire(66, -61, 16), spire(66, -31, 16))
		),
		P(
			"Tower",
			"Central Tower",
			"A round tower rising from the middle of the roof.",
			cat(
				cyl(46, -46, 10, 14, ice, MT.Ice, 17),
				cyl(46, -46, 10.6, 1, deep, MT.Ice, 22),
				cyl(46, -46, 12, 1, deep, MT.Ice, 31),
				box(40.9, -46, 0.3, 3, 1.6, cyan, MT.Neon, 24),
				box(40.9, -46, 0.3, 3, 1.6, cyan, MT.Neon, 27)
			)
		),
		P(
			"Dome",
			"Crystal Dome",
			"A glass dome on the tower with a glowing spike.",
			cat(
				ball(46, -46, 12, glass, MT.Glass, 32),
				cyl(46, -46, 12.4, 0.5, white, MT.Snow, 31.8),
				cyl(46, -46, 0.6, 5, ice, MT.Ice, 44),
				ball(46, -46, 1, cyan, MT.Neon, 49)
			)
		),
		P(
			"Drifts",
			"Snow Drifts",
			"Six soft snow drifts.",
			cat(
				snowDrift(14, -12, 8, 5),
				snowDrift(20, -20, 7, 5),
				snowDrift(30, -26, 9, 5),
				snowDrift(-40, -14, 8, 5),
				snowDrift(-30, -24, 8, 5),
				snowDrift(14, 12, 7, 5)
			)
		),
		P(
			"Pines",
			"Snowy Pines",
			"Three tall pine trees.",
			cat(pine(-44, -40, 14, pineLeaf), pine(-36, -48, 12, pineLeaf), pine(-46, -24, 13, pineLeaf))
		),
		P(
			"Snowmen",
			"Snowman Guards",
			"Two snowmen with carrot noses guarding the gate.",
			cat(snowman(22, -52), snowman(22, -40))
		),
		P(
			"Pond",
			"Frozen Pond",
			"A round frozen pond with cracks and four rocks.",
			cat(
				cyl(20, 16, 14, 0.3, RGB(150, 205, 240), MT.Ice),
				blk(20, 0.33, 16, 12, 0.06, 0.3, white, MT.Ice, V3(0, 20, 0)),
				blk(20, 0.33, 16, 12, 0.06, 0.3, white, MT.Ice, V3(0, 80, 0)),
				blk(20, 0.33, 16, 10, 0.06, 0.3, white, MT.Ice, V3(0, 140, 0)),
				ball(12.8, 12, 1.8, RGB(120, 128, 140), MT.Slate),
				ball(27.4, 18, 1.6, RGB(120, 128, 140), MT.Slate),
				ball(24, 22.4, 1.4, RGB(120, 128, 140), MT.Slate),
				ball(15, 22, 1.2, RGB(120, 128, 140), MT.Slate)
			)
		),
		P(
			"Bridge",
			"Ice Bridge",
			"A little arched bridge made of ice over the pond.",
			cat(
				box(20, 16, 5, 0.5, 2.6, ice, MT.Ice, 1.8),
				box(15.8, 16, 3, 0.5, 2.6, ice, MT.Ice, 1.3),
				box(24.2, 16, 3, 0.5, 2.6, ice, MT.Ice, 1.3),
				box(12.5, 16, 2, 0.5, 2.6, ice, MT.Ice, 0.8),
				box(27.5, 16, 2, 0.5, 2.6, ice, MT.Ice, 0.8),
				box(20, 14.8, 5, 0.3, 0.3, cyan, MT.Neon, 2.8),
				box(20, 17.2, 5, 0.3, 0.3, cyan, MT.Neon, 2.8)
			)
		),
		P(
			"Sculpture",
			"Ice Sculpture",
			"A little Shiba carved from clear ice on a snowy pedestal.",
			cat(
				box(30, 24, 5, 1.2, 3, white, MT.Snow),
				box(30, 24, 3, 1.8, 1.4, ice, MT.Ice, 1.2),
				box(28.4, 24, 1.6, 1.6, 1.6, ice, MT.Ice, 2.4),
				wedge(28.2, 23.4, 0.6, 1, 0.6, ice, MT.Ice, 4),
				wedge(28.2, 24.6, 0.6, 1, 0.6, ice, MT.Ice, 4),
				ball(31.8, 24, 1.2, ice, MT.Ice, 2.6),
				box(29, 23.5, 0.5, 1.2, 0.5, ice, MT.Ice, 0.2 + 1),
				box(29, 24.5, 0.5, 1.2, 0.5, ice, MT.Ice, 0.2 + 1),
				blk(30, 6.4, 24, 1.2, 1.2, 1.2, cyan, MT.Neon, V3(45, 0, 45))
			)
		),
		P(
			"Igloo",
			"Igloo",
			"A snow igloo with a tunnel entrance.",
			cat(
				mk(PT.Ball, 52, 3, 26, 10, 6, 10, white, MT.Snow, nil),
				box(47.4, 26, 3.4, 2.6, 3, white, MT.Snow),
				box(45.6, 26, 0.2, 2, 1.8, dark, MT.Slate),
				box(52, 26, 1.6, 0.8, 1.6, ice, MT.Ice, 4),
				box(49, 24, 1.2, 0.8, 1.2, ice, MT.Ice, 3),
				box(55, 28, 1.2, 0.8, 1.2, ice, MT.Ice, 2.6)
			)
		),
		P(
			"Sled",
			"Sled and Presents",
			"A red sled loaded with two wrapped presents.",
			cat(
				box(36, 39.2, 4, 0.3, 0.4, dark, MT.Metal),
				box(36, 40.8, 4, 0.3, 0.4, dark, MT.Metal),
				box(36, 40, 4, 0.3, 2, RGB(200, 50, 50), MT.Wood, 0.3),
				wedge(38.4, 40, 1, 1, 2, RGB(200, 50, 50), MT.Wood, 0.3),
				box(35, 40, 1.2, 1.2, 1.2, RGB(60, 150, 90), MT.Fabric, 0.6),
				box(35, 40, 1.3, 1.3, 0.3, RGB(255, 220, 90), MT.Fabric, 0.55),
				box(36.8, 40, 1, 1, 1, purple, MT.Fabric, 0.6),
				box(36.8, 40, 1.1, 1.1, 0.25, RGB(255, 220, 90), MT.Fabric, 0.55)
			)
		),
		P(
			"Lamps",
			"Ice Lamps",
			"Four lamps with cyan glow along the road to the gate.",
			each({ { 11, -50 }, { 11, -42 }, { 17, -50 }, { 17, -42 } }, function(x, z)
				return lamp(x, z, 5, cyan, pale)
			end)
		),
		P(
			"Cannon",
			"Snow Cannon",
			"A snow-making machine puffing white clouds.",
			cat(
				box(56, 12, 3, 0.8, 3, dark, MT.Metal),
				cyl(56, 12, 2.2, 2.4, RGB(180, 190, 205), MT.Metal, 0.8),
				hcyl(57.8, 3.6, 12, 3.6, 1, "X", dark, MT.Metal),
				ball(59.8, 12, 1, white, MT.Neon, 3.1),
				box(54.6, 10.6, 0.4, 1.6, 0.4, dark, MT.Metal),
				box(54.6, 13.4, 0.4, 1.6, 0.4, dark, MT.Metal),
				ball(61.4, 11.4, 2, white, MT.Snow, 3),
				ball(63, 12.4, 2.6, white, MT.Snow, 3),
				ball(65, 11.6, 3.2, white, MT.Snow, 3.2)
			)
		),
		P(
			"Icicles",
			"Icicles",
			"Ten sharp icicles hanging from the front roof edge.",
			line(10, 25.2, -59, 25.2, -33, function(x, z)
				return cyl(x, z, 0.5, 2.4, pale, MT.Ice, 11.6)
			end)
		),
		P(
			"Fountain",
			"Frozen Fountain",
			"A fountain frozen solid, ringed by four ice crystals.",
			cat(
				fountain(38, 4, 6, ice, white),
				ring(4, 38, 4, 7.6, function(x, z, a)
					return blk(x, 2.2, z, 1, 3, 1, cyan, MT.Ice, V3(0, -a, 12))
				end)
			)
		),
		P(
			"Throne",
			"Ice Throne",
			"A spiky ice throne on a snowy step.",
			cat(
				box(60, -18, 7, 0.6, 7, white, MT.Snow),
				box(60, -18, 4, 1.8, 3.4, ice, MT.Ice, 0.6),
				box(62.2, -18, 0.8, 7.4, 4, ice, MT.Ice, 0.6),
				box(60, -19.8, 3.6, 1.4, 0.6, ice, MT.Ice, 2.4),
				box(60, -16.2, 3.6, 1.4, 0.6, ice, MT.Ice, 2.4),
				box(62.2, -19.4, 0.6, 2.2, 0.6, deep, MT.Ice, 8),
				box(62.2, -18, 0.6, 2.6, 0.6, deep, MT.Ice, 8),
				box(62.2, -16.6, 0.6, 2.2, 0.6, deep, MT.Ice, 8),
				ball(61.6, -18, 1.2, cyan, MT.Neon, 5.4)
			)
		),
		P(
			"Crystals",
			"Crystal Cluster",
			"A cluster of eight tilted crystals.",
			each({
				{ -40, -34 },
				{ -38, -32 },
				{ -42, -32 },
				{ -39, -36 },
				{ -43, -35 },
				{ -36, -35 },
				{ -41, -30 },
				{ -37, -38 },
			}, function(x, z, i)
				return blk(
					x,
					2.4 + (i % 4) * 0.8 + 0.8,
					z,
					1.4,
					4 + (i % 4) * 1.6,
					1.4,
					if i % 3 == 0 then purple elseif i % 3 == 1 then cyan else white,
					MT.Ice,
					V3(0, i * 35, if i % 2 == 0 then 8 else -8)
				)
			end)
		),
		P(
			"Prisms",
			"Aurora Prisms",
			"Four glowing prisms on little ice discs at the back of the grounds.",
			each({ { 30, -70 }, { 44, -70 }, { 58, -70 }, { 70, -70 } }, function(x, z, i)
				return {
					cyl(x, z, 3, 0.4, deep, MT.Ice),
					blk(x, 6.4, z, 1.6, 12, 1.6, if i % 2 == 0 then purple else green, MT.Neon, V3(0, 45, 0)),
				}
			end)
		),
		P(
			"AuroraLight",
			"Aurora Light",
			"Huge green, purple and cyan ribbons of light waving above the palace.",
			cat(
				blk(46, 58, -48, 50, 5, 0.5, green, MT.Neon, V3(0, 10, 6)),
				blk(46, 63, -44, 50, 5, 0.5, purple, MT.Neon, V3(0, -12, -6)),
				blk(46, 53, -52, 50, 5, 0.5, cyan, MT.Neon, V3(0, 18, 4)),
				blk(46, 68, -40, 46, 4, 0.5, green, MT.Neon, V3(0, -8, 5)),
				blk(46, 48, -46, 44, 4, 0.5, purple, MT.Neon, V3(0, 5, -4)),
				blk(46, 73, -48, 40, 3, 0.5, cyan, MT.Neon, V3(0, 14, -3)),
				ball(30, -30, 1.5, white, MT.Neon, 62),
				ball(62, -64, 1.5, white, MT.Neon, 68),
				ball(70, -34, 1.5, white, MT.Neon, 58),
				ball(22, -60, 1.5, white, MT.Neon, 72)
			)
		),
	})
end

return themes
