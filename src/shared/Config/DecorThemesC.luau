--!strict
-- Shiba themes for bays 21 to 30 (see Config/DecorTypes for the schema and the STAGE FRAME). Keyed by the bay number.
-- Pure data built with small pure helpers (no Instances, no side effects). Bay 21 has 25 parts, bays 22 to 30 have 30.
-- Layout rules every theme follows: the path |X| < 7 stays free on the ground (only 0.2 thick flooring may cover the
-- sides, things above 12 studs may hover over the path), a free circle of radius 8 around the Shiba (-16, 0) and the
-- intern (-10, 0), so props on the left stand behind the Shiba (X < -26) or at |Z| > 9.
-- Visuals are placeholders ("models are adjusted later"): simple blocks, cylinders, wedges and balls.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Part = DecorTypes.Part
type Theme = DecorTypes.Theme

local M = Enum.Material
local rgb = Color3.fromRGB
local BLOCK = Enum.PartType.Block
local CYLINDER = Enum.PartType.Cylinder
local BALL = Enum.PartType.Ball
local WEDGE = Enum.PartType.Wedge

-- ---------------------------------------------------------------------------------------------------------------------
-- Piece helpers. Position arguments are (x, base y, z): the piece stands ON y, so heights are easy to stack.

local function raw(
	cx: number,
	cy: number,
	cz: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?,
	shape: Enum.PartType?,
	rotation: Vector3?
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(cx, cy, cz),
		Color = color,
		Material = material,
		Shape = shape,
		Rotation = rotation,
	}
end

local function yaw(deg: number?): Vector3?
	if deg and deg ~= 0 then
		return Vector3.new(0, deg, 0)
	end
	return nil
end

-- Block: width (X), height (Y), depth (Z), optional rotation around Y.
local function blk(
	x: number,
	y: number,
	z: number,
	w: number,
	h: number,
	d: number,
	c: Color3,
	m: Enum.Material?,
	ry: number?
): Piece
	return raw(x, y + h / 2, z, w, h, d, c, m, BLOCK, yaw(ry))
end

-- Standing cylinder (axis up).
local function cyl(x: number, y: number, z: number, dia: number, h: number, c: Color3, m: Enum.Material?): Piece
	return raw(x, y + h / 2, z, h, dia, dia, c, m, CYLINDER, Vector3.new(0, 0, 90))
end

-- Lying cylinder along the X axis (axis = "x") or the Z axis (axis = "z").
local function lcyl(
	x: number,
	y: number,
	z: number,
	len: number,
	dia: number,
	axis: string,
	c: Color3,
	m: Enum.Material?
): Piece
	return raw(x, y + dia / 2, z, len, dia, dia, c, m, CYLINDER, if axis == "z" then Vector3.new(0, 90, 0) else nil)
end

local function ball(x: number, y: number, z: number, dia: number, c: Color3, m: Enum.Material?): Piece
	return raw(x, y + dia / 2, z, dia, dia, dia, c, m, BALL, nil)
end

local function wedge(
	x: number,
	y: number,
	z: number,
	w: number,
	h: number,
	d: number,
	c: Color3,
	m: Enum.Material?,
	ry: number?
): Piece
	return raw(x, y + h / 2, z, w, h, d, c, m, WEDGE, yaw(ry))
end

-- Flatten pieces and lists of pieces into one list.
local function pcs(...: any): { Piece }
	local out: { Piece } = {}
	for _, item in { ... } do
		if item.Size then
			table.insert(out, item)
		else
			for _, p in item do
				table.insert(out, p)
			end
		end
	end
	return out
end

local function append(out: { Piece }, list: { Piece })
	for _, p in list do
		table.insert(out, p)
	end
end

-- n points on a straight line from (x0, z0) to (x1, z1) (both ends included); fn(x, z, i) returns a piece or a list.
local function line(
	n: number,
	x0: number,
	z0: number,
	x1: number,
	z1: number,
	fn: (number, number, number) -> any
): { Piece }
	local out: { Piece } = {}
	for i = 1, n do
		local t = if n == 1 then 0 else (i - 1) / (n - 1)
		append(out, pcs(fn(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, i)))
	end
	return out
end

-- n points on a horizontal circle; fn(x, z, degrees, i) returns a piece or a list. Degrees = the heading of the point.
local function around(
	cx: number,
	cz: number,
	r: number,
	n: number,
	fn: (number, number, number, number) -> any
): { Piece }
	local out: { Piece } = {}
	for i = 1, n do
		local deg = (i - 1) * 360 / n
		local rad = math.rad(deg)
		append(out, pcs(fn(cx + r * math.cos(rad), cz + r * math.sin(rad), deg, i)))
	end
	return out
end

-- n points on a vertical circle in the plane XY (axis "z": a portal facing along Z, over the path) or YZ (axis "x").
-- fn(x, y, z, degrees, i) returns a piece or a list.
local function aroundV(
	cx: number,
	cy: number,
	cz: number,
	r: number,
	n: number,
	axis: string,
	fn: (number, number, number, number, number) -> any
): { Piece }
	local out: { Piece } = {}
	for i = 1, n do
		local deg = (i - 1) * 360 / n
		local rad = math.rad(deg)
		local u, v = r * math.cos(rad), r * math.sin(rad)
		local px, pz = cx, cz
		if axis == "z" then
			px += u
		else
			pz += u
		end
		append(out, pcs(fn(px, cy + v, pz, deg, i)))
	end
	return out
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Prop helpers.

-- Ground flooring: a left and a right slab (0.2 thick) leaving the path |X| < 7.2 free.
local function floorSlabs(w: number, d: number, c: Color3, m: Enum.Material?): { Piece }
	local lo, hi = 7.2, w - 0.5
	local width, mid = hi - lo, (hi + lo) / 2
	return { blk(-mid, 0, 0, width, 0.2, 2 * d - 1, c, m), blk(mid, 0, 0, width, 0.2, 2 * d - 1, c, m) }
end

-- Thin flat marking on top of the flooring (top at 0.3).
local function mark(x: number, z: number, w: number, d: number, c: Color3, m: Enum.Material?, ry: number?): Piece
	return blk(x, 0.2, z, w, 0.1, d, c, m, ry)
end

local function round(x: number, z: number, dia: number, c: Color3, m: Enum.Material?): Piece
	return cyl(x, 0.2, z, dia, 0.1, c, m)
end

-- Pushes a Z coordinate out of the band |Z| < 14, which is reserved around the Shiba and the intern (also in the air).
local function awayZ(z: number): number
	if z >= 0 and z < 14 then
		return 14
	elseif z < 0 and z > -14 then
		return -14
	end
	return z
end

-- Round tree: trunk and two leaf balls.
local function tree(x: number, z: number, s: number, trunk: Color3, leaf: Color3, m: Enum.Material?): { Piece }
	return {
		cyl(x, 0, z, 1.2 * s, 5 * s, trunk, M.Wood),
		ball(x, 3.5 * s, z, 6 * s, leaf, m or M.Grass),
		ball(x, 7 * s, z, 3.8 * s, leaf, m or M.Grass),
	}
end

local function lamp(x: number, z: number, pole: Color3, glow: Color3, h: number?): { Piece }
	local height = h or 7
	return {
		cyl(x, 0, z, 1.6, 0.6, pole, M.Metal),
		cyl(x, 0.6, z, 0.6, height, pole, M.Metal),
		ball(x, height + 0.4, z, 2, glow, M.Neon),
	}
end

-- A simple blocky character, facing +X by default (rotate with ry).
local function person(x: number, z: number, body: Color3, skin: Color3, s: number, ry: number?): { Piece }
	return {
		blk(x, 0, z, 1.6 * s, 2.6 * s, 1.2 * s, body, M.Fabric, ry),
		blk(x, 2.6 * s, z, 2.2 * s, 3 * s, 1.4 * s, body, M.Fabric, ry),
		ball(x, 5.6 * s, z, 1.9 * s, skin, M.SmoothPlastic),
		blk(x, 3 * s, z + 1.5 * s, 0.7 * s, 2.6 * s, 0.7 * s, skin, M.SmoothPlastic, ry),
		blk(x, 3 * s, z - 1.5 * s, 0.7 * s, 2.6 * s, 0.7 * s, skin, M.SmoothPlastic, ry),
	}
end

-- A "GET BONKED" sign facing the path: a board on two posts with accent trim and six letter blocks.
-- dir = -1: the face looks toward -X (sign on the right of the path), dir = 1: toward +X (sign on the left).
local function bonkSign(
	x: number,
	z: number,
	dir: number,
	board: Color3,
	accent: Color3,
	post: Color3,
	m: Enum.Material?
): { Piece }
	local pieces = {
		cyl(x, 0, z - 10, 1.4, 9, post, M.Metal),
		cyl(x, 0, z + 10, 1.4, 9, post, M.Metal),
		blk(x, 4, z, 1.2, 9, 25, board, m),
		blk(x + dir * 0.4, 12.4, z, 1.6, 0.8, 26, accent, M.Neon),
		blk(x + dir * 0.4, 3.8, z, 1.6, 0.8, 26, accent, M.Neon),
	}
	for i = 1, 6 do
		table.insert(pieces, blk(x + dir * 0.9, 6.5, z - 9 + (i - 1) * 3.6, 0.6, 4, 2.4, accent, M.Neon))
	end
	return pieces
end

-- Round-ish rock pile for filler (three balls of grey).
local function rocks(x: number, z: number, s: number, c: Color3): { Piece }
	return {
		ball(x, 0, z, 5 * s, c, M.Slate),
		ball(x + 2.5 * s, 0, z + 1 * s, 3.4 * s, c, M.Slate),
		ball(x - 1.5 * s, 0, z + 2.2 * s, 2.8 * s, c, M.Slate),
	}
end

-- Floating island: a thick disc, tapering discs below, and an optional top layer colour.
local function island(
	x: number,
	y: number,
	z: number,
	r: number,
	top: Color3,
	rock: Color3,
	topM: Enum.Material?
): { Piece }
	return {
		cyl(x, y, z, 2 * r, 1.2, top, topM or M.Grass),
		cyl(x, y - 3, z, 1.7 * r, 3, rock, M.Slate),
		cyl(x, y - 6, z, 1.1 * r, 3, rock, M.Slate),
		ball(x, y - 11, z, 0.7 * r, rock, M.Slate),
	}
end

-- Stage area of a bay: about (36 + 6 * bay) square, at most 190 wide (the plot is 200 wide).
local function areaOf(bay: number): Vector2
	return Vector2.new(math.min(190, 36 + 6 * bay), if bay == 30 then 240 else 36 + 6 * bay)
end

type Def = { Id: string, Name: string, Description: string, Pieces: { Piece } }

local function def(id: string, name: string, description: string, pieces: { Piece }): Def
	return { Id = id, Name = name, Description = description, Pieces = pieces }
end

-- Assembles a theme: the price grows geometrically from 10 to lastPrice seconds of income (placeholders).
local function build(key: string, name: string, bay: number, lastPrice: number, defs: { Def }): Theme
	local parts: { Part } = {}
	local count = #defs
	for i, d in defs do
		table.insert(parts, {
			Id = d.Id,
			Name = d.Name,
			Description = d.Description,
			PriceSeconds = math.round(10 * (lastPrice / 10) ^ ((i - 1) / (count - 1))),
			Pieces = d.Pieces,
		})
	end
	return { Key = key, Name = name, Area = areaOf(bay), Parts = parts }
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 21: Magma Shiba, Volcano. A big dark cone on the right with a glowing crater, lava rivers and an eruption.

local function volcano(): Theme
	local area = areaOf(21)
	local w = area.X / 2
	local rock, dark = rgb(52, 40, 40), rgb(26, 24, 30)
	local ash, bone = rgb(74, 68, 70), rgb(225, 215, 190)
	local lava, glow = rgb(255, 96, 18), rgb(255, 190, 60)
	local cx = 44

	local cone = {}
	local levels = { { 66, 6 }, { 58, 6 }, { 50, 6 }, { 42, 6 }, { 34, 6 }, { 26, 4 } }
	local y = 0
	for i, lv in levels do
		table.insert(cone, cyl(cx, y, 0, lv[1], lv[2], if i > 4 then dark else rock, M.Slate))
		y += lv[2]
	end
	table.insert(cone, ball(cx + 30, 0, 18, 12, rock, M.Slate))
	table.insert(cone, ball(cx - 20, 0, -28, 10, rock, M.Slate))

	local spikes = {}
	for i, p in { { 72, -42 }, { 66, -48 }, { 78, -36 }, { 74, 44 }, { 68, 50 }, { 60, -58 }, { 56, -54 }, { 78, 10 } } do
		local h = 10 + (i % 3) * 3
		table.insert(spikes, blk(p[1], 0, p[2], 3, h, 3, dark, M.Basalt, i * 17))
		table.insert(spikes, blk(p[1], h, p[2], 1.6, 6, 1.6, dark, M.Basalt, i * 17))
	end

	local defs = {
		def(
			"AshGround",
			"Ash Ground",
			"Dark ash flooring split by glowing cracks.",
			pcs(
				floorSlabs(w, 81, ash, M.Slate),
				mark(30, -20, 1.2, 40, lava, M.Neon, 10),
				mark(60, 30, 1.2, 50, lava, M.Neon, -15),
				mark(-40, 40, 1.2, 36, lava, M.Neon, 25),
				mark(-60, -30, 1.2, 44, lava, M.Neon, -8),
				mark(-30, -60, 30, 1.2, lava, M.Neon, 12),
				mark(70, -10, 1.2, 30, lava, M.Neon, 5)
			)
		),
		def("VolcanoCone", "Volcano Cone", "The huge dark cone of the volcano.", cone),
		def(
			"BonkSign",
			"Get Bonked Sign",
			"A scorched board that reads GET BONKED.",
			bonkSign(11, -62, -1, rock, glow, dark, M.Slate)
		),
		def(
			"CraterRim",
			"Crater Rim",
			"Jagged rocks around a glowing lava lake at the top.",
			pcs(
				cyl(cx, 34, 0, 20, 0.6, lava, M.Neon),
				around(cx, 0, 11.5, 12, function(px, pz, deg, i)
					return blk(px, 34, pz, 5, 4 + (i % 3) * 1.5, 5, dark, M.Slate, deg)
				end)
			)
		),
		def("LavaFlow", "Lava Flow", "Two rivers of lava run down to glowing pools.", {
			blk(30, 0.2, 40, 3, 0.3, 16, lava, M.Neon),
			blk(27, 0.2, 50, 12, 0.3, 3, lava, M.Neon),
			blk(21, 0.2, 58, 3, 0.3, 16, lava, M.Neon),
			cyl(21, 0.2, 70, 12, 0.4, lava, M.Neon),
			blk(56, 0.2, 36, 3, 0.3, 16, lava, M.Neon),
			blk(60, 0.2, 46, 10, 0.3, 3, lava, M.Neon),
			blk(64, 0.2, 56, 3, 0.3, 16, lava, M.Neon),
			cyl(64, 0.2, 66, 10, 0.4, glow, M.Neon),
			ball(21, 0.5, 70, 2.5, glow, M.Neon),
			ball(64, 0.5, 66, 2, lava, M.Neon),
		}),
		def("ObsidianSpikes", "Obsidian Spikes", "Black glassy spikes rising from the ash.", spikes),
		def(
			"StoneTorches",
			"Stone Torches",
			"Six burning torches line the right side of the path.",
			line(6, 9.5, -56, 9.5, 56, function(px, pz)
				return { cyl(px, 0, pz, 1.2, 5, rock, M.Slate), ball(px, 5, pz, 2.6, glow, M.Neon) }
			end)
		),
		def(
			"LavaPool",
			"Lava Pool",
			"A bubbling pool behind the Shiba.",
			pcs(
				cyl(-50, 0.1, 40, 26, 0.4, lava, M.Neon),
				around(-50, 40, 14, 8, function(px, pz, deg)
					return blk(px, 0, pz, 4, 2, 4, dark, M.Slate, deg)
				end),
				ball(-46, 0.5, 38, 3, glow, M.Neon),
				ball(-54, 0.5, 43, 2, glow, M.Neon)
			)
		),
		def(
			"BasaltColumns",
			"Basalt Columns",
			"Tall black columns of cooled lava.",
			line(8, -58, -26, -38, -44, function(px, pz, i)
				return cyl(px, 0, pz, 4, 6 + (i * 5) % 11, dark, M.Basalt)
			end)
		),
		def(
			"DeadTrees",
			"Charred Trees",
			"Burnt trees without leaves.",
			line(5, -34, -20, -70, 32, function(px, pz, i)
				return {
					cyl(px, 0, pz, 1.4, 9, dark, M.Wood),
					blk(px, 6, pz, 0.9, 0.9, 6, dark, M.Wood, 20 * i),
					blk(px, 8, pz, 0.9, 0.9, 5, dark, M.Wood, 20 * i + 90),
				}
			end)
		),
		def("LavaFalls", "Lava Falls", "A rocky cliff with a lava waterfall.", {
			blk(62, 0, -66, 26, 16, 12, rock, M.Slate),
			blk(62, 16, -66, 18, 4, 9, dark, M.Slate),
			blk(62, 2, -59.5, 6, 14, 0.8, lava, M.Neon),
			blk(62, 0, -55, 10, 0.4, 6, lava, M.Neon),
			ball(60, 0.4, -53, 2, glow, M.Neon),
			ball(64, 0.4, -54, 1.6, glow, M.Neon),
			blk(50, 0, -60, 6, 5, 6, rock, M.Slate, 15),
		}),
		def("StoneBridges", "Stone Bridges", "A lava channel crossed by two stone bridges.", {
			blk(45, 0.1, -45, 66, 0.3, 6, lava, M.Neon),
			blk(26, 0, -45, 5, 1, 9, rock, M.Slate),
			blk(26, 1, -49.2, 5, 1.2, 0.6, dark, M.Slate),
			blk(26, 1, -40.8, 5, 1.2, 0.6, dark, M.Slate),
			blk(60, 0, -45, 5, 1, 9, rock, M.Slate),
			blk(60, 1, -49.2, 5, 1.2, 0.6, dark, M.Slate),
			blk(60, 1, -40.8, 5, 1.2, 0.6, dark, M.Slate),
		}),
		def("MagmaGate", "Magma Gate", "A stone gate behind the Shiba with a glowing core.", {
			cyl(-40, 0, -11, 4, 20, rock, M.Slate),
			cyl(-40, 0, 11, 4, 20, rock, M.Slate),
			blk(-40, 20, 0, 5, 3, 28, dark, M.Slate),
			blk(-40, 23, 0, 3, 2, 20, rock, M.Slate),
			blk(-38, 17, 0, 0.8, 2, 18, lava, M.Neon),
			wedge(-40, 25, -9, 3, 4, 3, dark, M.Basalt),
			wedge(-40, 25, 9, 3, 4, 3, dark, M.Basalt),
			blk(-40, 0, -11, 7, 1, 7, dark, M.Slate),
			blk(-40, 0, 11, 7, 1, 7, dark, M.Slate),
		}),
		def(
			"FireBowls",
			"Fire Bowls",
			"Four fire bowls guard the volcano.",
			pcs(
				line(2, 14, -24, 14, -36, function(px, pz)
					return {
						cyl(px, 0, pz, 3, 4, rock, M.Slate),
						cyl(px, 4, pz, 5.5, 1.5, dark, M.Metal),
						ball(px, 5.5, pz, 4, glow, M.Neon),
					}
				end),
				line(2, 14, 24, 14, 36, function(px, pz)
					return {
						cyl(px, 0, pz, 3, 4, rock, M.Slate),
						cyl(px, 4, pz, 5.5, 1.5, dark, M.Metal),
						ball(px, 5.5, pz, 4, glow, M.Neon),
					}
				end)
			)
		),
		def(
			"SmokeVents",
			"Smoke Vents",
			"Hot vents puffing grey smoke.",
			line(4, -30, -40, -76, -10, function(px, pz, i)
				return {
					cyl(px, 0, pz, 5, 2, rock, M.Slate),
					cyl(px, 2, pz, 2, 4, dark, M.Metal),
					ball(px, 7, pz, 4 + i % 2, ash, M.SmoothPlastic),
					ball(px + 1, 10.5, pz, 5, ash, M.SmoothPlastic),
				}
			end)
		),
		def("StoneShiba", "Stone Shiba", "A statue of a Shiba on a rock pedestal.", {
			blk(-50, 0, -62, 12, 3, 12, dark, M.Slate),
			blk(-50, 3, -62, 7, 5, 4, rock, M.Slate),
			blk(-47, 6, -62, 4, 5, 4, rock, M.Slate),
			ball(-45, 7, -62, 5, rock, M.Slate),
			wedge(-44, 11, -63.4, 1.2, 2, 1.2, rock, M.Slate),
			wedge(-44, 11, -60.6, 1.2, 2, 1.2, rock, M.Slate),
			blk(-54, 6, -62, 1.2, 1.2, 4, rock, M.Slate, 30),
			ball(-42.6, 8.6, -61, 0.8, glow, M.Neon),
			ball(-42.6, 8.6, -63, 0.8, glow, M.Neon),
		}),
		def(
			"LavaFountain",
			"Lava Fountain",
			"A fountain that sprays glowing lava.",
			pcs(
				cyl(-62, 0, 0, 16, 1.5, dark, M.Slate),
				cyl(-62, 1.5, 0, 13, 0.4, lava, M.Neon),
				cyl(-62, 1.5, 0, 3, 12, glow, M.Neon),
				ball(-62, 13, 0, 5, lava, M.Neon),
				around(-62, 0, 4.5, 6, function(px, pz)
					return ball(px, 9, pz, 1.6, lava, M.Neon)
				end)
			)
		),
		def("AshClouds", "Ash Clouds", "A dark ash cloud hanging over the stage.", {
			ball(44, 58, 0, 30, rgb(60, 56, 58), M.SmoothPlastic),
			ball(20, 62, 20, 24, rgb(70, 64, 66), M.SmoothPlastic),
			ball(-10, 60, -28, 28, rgb(56, 52, 54), M.SmoothPlastic),
			ball(60, 64, 40, 22, rgb(66, 60, 62), M.SmoothPlastic),
			ball(0, 66, 40, 22, rgb(62, 58, 60), M.SmoothPlastic),
			ball(-40, 62, 0, 26, rgb(70, 64, 66), M.SmoothPlastic),
			ball(36, 70, -40, 20, rgb(58, 54, 56), M.SmoothPlastic),
			ball(-60, 66, -50, 22, rgb(64, 60, 62), M.SmoothPlastic),
		}),
		def(
			"EmberLights",
			"Floating Embers",
			"Glowing sparks drifting in the air.",
			line(14, -70, -60, 70, 60, function(px, pz, i)
				return ball(
					px,
					16 + (i * 7) % 15,
					awayZ(pz + ((i * 13) % 20) - 10),
					2 + (i % 3) * 0.6,
					if i % 2 == 0 then lava else glow,
					M.Neon
				)
			end)
		),
		def(
			"MagmaGeysers",
			"Magma Geysers",
			"Three geysers shoot lava into the air.",
			line(3, 24, 60, 70, 20, function(px, pz, i)
				return {
					cyl(px, 0, pz, 7, 1.5, dark, M.Slate),
					cyl(px, 1.5, pz, 2.4, 14 + i * 3, lava, M.Neon),
					ball(px, 15.5 + i * 3, pz, 4.5, glow, M.Neon),
				}
			end)
		),
		def(
			"LavaRiver",
			"Lava River",
			"A winding river of lava behind the Shiba.",
			pcs(
				line(6, -72, -66, -72, 66, function(px, pz, i)
					return blk(px + ((i % 2) * 6 - 3), 0.2, pz, 4, 0.3, 28, lava, M.Neon)
				end),
				line(6, -72, -66, -72, 66, function(px, pz, i)
					return blk(px + ((i % 2) * 6 - 3) + 3.5, 0, pz, 3, 1.4, 6, dark, M.Slate)
				end)
			)
		),
		def(
			"SkullTotems",
			"Skull Totems",
			"Bone totems with glowing eyes.",
			line(3, -34, -26, -42, 26, function(px, pz)
				return {
					cyl(px, 0, pz, 1.6, 12, dark, M.Wood),
					ball(px, 8, pz, 4.4, bone, M.SmoothPlastic),
					ball(px, 12, pz, 3.4, bone, M.SmoothPlastic),
					ball(px + 1.8, 9.6, pz - 0.8, 0.8, lava, M.Neon),
					ball(px + 1.8, 9.6, pz + 0.8, 0.8, lava, M.Neon),
				}
			end)
		),
		def(
			"MeteorRocks",
			"Meteor Rocks",
			"Burning rocks hover high above the ground.",
			line(8, -60, 55, 70, -50, function(px, pz, i)
				return {
					ball(px, 24 + (i * 5) % 18, awayZ(pz), 6 + i % 3 * 2, dark, M.Slate),
					ball(px + 2, 26 + (i * 5) % 18, awayZ(pz), 3, lava, M.Neon),
				}
			end)
		),
		def(
			"MagmaCrystals",
			"Magma Crystals",
			"A cluster of huge glowing crystals.",
			pcs(
				cyl(-62, 0, -60, 20, 1, dark, M.Slate),
				line(5, -68, -60, -56, -60, function(px, pz, i)
					return blk(px, 1, pz + (i % 2) * 4 - 2, 3 + (i % 3), 10 + i * 3, 3 + (i % 3), lava, M.Neon, 45)
				end),
				ball(-62, 1, -54, 3, glow, M.Neon),
				ball(-58, 1, -66, 2.4, glow, M.Neon)
			)
		),
		def("Eruption", "Eruption", "The volcano erupts: a glowing plume of fire and ash.", {
			ball(cx, 36, 0, 14, lava, M.Neon),
			ball(cx, 46, 0, 18, glow, M.Neon),
			ball(cx, 58, 0, 22, lava, M.Neon),
			ball(cx, 72, 0, 28, rgb(70, 60, 60), M.SmoothPlastic),
			ball(cx, 88, 0, 34, rgb(58, 52, 54), M.SmoothPlastic),
			ball(cx + 12, 100, 6, 30, rgb(66, 58, 60), M.SmoothPlastic),
			ball(cx - 12, 98, -6, 28, rgb(54, 48, 50), M.SmoothPlastic),
			ball(cx + 22, 60, 14, 5, lava, M.Neon),
			ball(cx - 24, 62, -12, 4, lava, M.Neon),
			ball(cx + 26, 78, -16, 4, glow, M.Neon),
			ball(cx - 20, 80, 18, 5, glow, M.Neon),
			ball(cx + 8, 52, -20, 3, lava, M.Neon),
		}),
	}
	return build("Volcano", "Volcano", 21, 400, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 22: Dragon Shiba, Dragon Lair. A rocky cave on the right full of gold, eggs and bones; a huge dragon on the roof.

local function dragonLair(): Theme
	local area = areaOf(22)
	local w, d = area.X / 2, area.Y / 2
	local rock, deep = rgb(36, 52, 42), rgb(20, 30, 26)
	local moss = rgb(48, 100, 56)
	local gold, bone = rgb(255, 200, 40), rgb(228, 218, 190)
	local flame, ember = rgb(255, 140, 30), rgb(255, 70, 20)
	local scale = rgb(40, 150, 70)

	local coin = function(px: number, pz: number, py: number)
		return cyl(px, py, pz, 4, 0.6, gold, M.Metal)
	end

	local defs = {
		def(
			"LairFloor",
			"Lair Floor",
			"Mossy dark stone flooring with scorch marks.",
			pcs(
				floorSlabs(w, d, deep, M.Slate),
				round(-50, 40, 22, moss, M.Grass),
				round(-60, -40, 18, moss, M.Grass),
				round(60, 60, 20, moss, M.Grass),
				round(60, -62, 24, moss, M.Grass),
				mark(30, 0, 18, 24, rgb(60, 40, 30), M.Slate),
				mark(-40, 0, 30, 3, flame, M.Neon, 8),
				mark(-70, 20, 3, 40, flame, M.Neon, -6)
			)
		),
		def(
			"CaveMouth",
			"Cave Mouth",
			"A big rocky cave with a wide opening toward the path.",
			{
				blk(70, 0, 0, 22, 34, 76, rock, M.Slate),
				blk(40, 0, -25, 40, 28, 26, rock, M.Slate),
				blk(40, 0, 25, 40, 28, 26, rock, M.Slate),
				blk(40, 22, 0, 40, 10, 26, rock, M.Slate),
				ball(30, 24, -25, 22, moss, M.Grass),
				ball(50, 24, 25, 24, moss, M.Grass),
				ball(60, 30, 0, 26, rock, M.Slate),
				ball(36, 28, 0, 14, rock, M.Slate),
				ball(20, 0, -40, 10, rock, M.Slate),
				ball(20, 0, 40, 10, rock, M.Slate),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A rusty board that reads GET BONKED.", bonkSign(11, 64, -1, deep, flame, rock, M.Slate)),
		def(
			"GoldHoard",
			"Gold Hoard",
			"A mountain of gold coins and a golden goblet inside the cave.",
			{
				ball(48, 0, 0, 18, gold, M.Metal),
				ball(40, 0, 6, 11, gold, M.Metal),
				ball(41, 0, -7, 12, gold, M.Metal),
				ball(54, 0, -8, 9, gold, M.Metal),
				ball(55, 0, 9, 10, gold, M.Metal),
				coin(34, 2, 0.1),
				coin(35, -3, 0.1),
				coin(33, -6, 0.1),
				coin(36, 8, 0.1),
				cyl(34, 0, 0, 1.2, 2.4, gold, M.Metal),
				cyl(34, 2.4, 0, 3, 1.6, gold, M.Metal),
				ball(46, 8, 0, 3, rgb(230, 60, 80), M.Glass),
				ball(51, 8.6, 3, 2.4, rgb(70, 140, 255), M.Glass),
				ball(42, 4.8, -4, 2, rgb(80, 220, 120), M.Glass),
			}
		),
		def(
			"EggNest",
			"Dragon Egg Nest",
			"A twig nest with three speckled dragon eggs.",
			pcs(
				around(20, -54, 7, 10, function(px, pz, deg)
					return blk(px, 0, pz, 4, 1.4, 1.2, rgb(110, 80, 50), M.Wood, 90 - deg)
				end),
				ball(20, 0.4, -54, 5.5, scale, M.SmoothPlastic),
				ball(23, 0.4, -51, 4.6, rgb(200, 120, 60), M.SmoothPlastic),
				ball(17, 0.4, -51, 4.8, rgb(90, 100, 220), M.SmoothPlastic),
				ball(20.6, 4, -54, 1, bone, M.SmoothPlastic)
			)
		),
		def(
			"SkullGate",
			"Skull Gate",
			"An arch of huge bones with skulls guards the cave entrance.",
			{
				cyl(17, 0, -15, 3, 16, bone, M.SmoothPlastic),
				cyl(17, 0, 15, 3, 16, bone, M.SmoothPlastic),
				lcyl(17, 16, 0, 34, 3, "z", bone, M.SmoothPlastic),
				ball(17, 18, -15, 6, bone, M.SmoothPlastic),
				ball(17, 18, 15, 6, bone, M.SmoothPlastic),
				ball(17, 19, 0, 7, bone, M.SmoothPlastic),
				ball(14.6, 20.4, -1.4, 1.4, flame, M.Neon),
				ball(14.6, 20.4, 1.4, 1.4, flame, M.Neon),
				wedge(17, 24, -3.6, 1.4, 4, 1.4, bone, M.SmoothPlastic),
				wedge(17, 24, 3.6, 1.4, 4, 1.4, bone, M.SmoothPlastic),
			}
		),
		def(
			"FireBraziers",
			"Fire Braziers",
			"Two burning braziers beside the entrance.",
			pcs(
				line(2, 12, -20, 12, 20, function(px, pz)
					return {
						cyl(px, 0, pz, 2, 4, rock, M.Slate),
						cyl(px, 4, pz, 5, 1.6, deep, M.Metal),
						ball(px, 5.6, pz, 4, flame, M.Neon),
						ball(px, 8.6, pz, 2.4, ember, M.Neon),
					}
				end)
			)
		),
		def(
			"Stalagmites",
			"Stalagmites",
			"Spiky rocks growing out of the floor behind the Shiba.",
			line(8, -40, -30, -75, -68, function(px, pz, i)
				return wedge(px, 0, pz, 4 + i % 3, 7 + (i * 3) % 9, 4 + i % 3, rock, M.Slate, i * 40)
			end)
		),
		def(
			"GreenCrystals",
			"Green Crystals",
			"A cluster of glowing green crystals.",
			pcs(
				line(6, -62, 42, -50, 54, function(px, pz, i)
					return blk(px, 0, pz, 2.6, 6 + (i * 5) % 9, 2.6, rgb(80, 255, 140), M.Neon, i * 30)
				end),
				ball(-56, 0, 48, 4, rgb(120, 255, 170), M.Neon)
			)
		),
		def(
			"BonePile",
			"Bone Pile",
			"A heap of old bones left by hungry dragons.",
			pcs(
				line(7, 26, 44, 40, 56, function(px, pz, i)
					return lcyl(px, (i % 3) * 0.8, pz, 5 + i % 3, 1, if i % 2 == 0 then "x" else "z", bone, M.SmoothPlastic)
				end),
				ball(33, 0, 50, 5, bone, M.SmoothPlastic),
				ball(30, 0.4, 52, 1.2, deep, M.SmoothPlastic),
				ball(32, 0.4, 53, 1.2, deep, M.SmoothPlastic)
			)
		),
		def(
			"TreasureChests",
			"Treasure Chests",
			"Three chests full of loot.",
			line(3, 24, -30, 30, -42, function(px, pz, i)
				return {
					blk(px, 0, pz, 5, 3, 3.4, rgb(110, 70, 40), M.Wood, i * 20),
					blk(px, 3, pz, 5, 1.2, 3.2, rgb(130, 85, 45), M.Wood, i * 20),
					ball(px, 3.6, pz, 3, gold, M.Metal),
				}
			end)
		),
		def(
			"EmberPool",
			"Ember Pool",
			"A pool of glowing embers behind the Shiba.",
			pcs(
				cyl(-56, 0.1, 40, 22, 0.4, flame, M.Neon),
				around(-56, 40, 12, 7, function(px, pz, deg)
					return blk(px, 0, pz, 4, 2.4, 4, deep, M.Slate, deg)
				end),
				ball(-58, 0.5, 38, 3, ember, M.Neon),
				ball(-52, 0.5, 42, 2, ember, M.Neon)
			)
		),
		def(
			"WallTorches",
			"Wall Torches",
			"Six torches burning along the cave front.",
			pcs(
				line(3, 19, -34, 19, -18, function(px, pz)
					return { cyl(px, 6, pz, 0.8, 4, rgb(90, 60, 40), M.Wood), ball(px, 10, pz, 2.4, flame, M.Neon) }
				end),
				line(3, 19, 18, 19, 34, function(px, pz)
					return { cyl(px, 6, pz, 0.8, 4, rgb(90, 60, 40), M.Wood), ball(px, 10, pz, 2.4, flame, M.Neon) }
				end)
			)
		),
		def(
			"DragonRibs",
			"Dragon Skeleton",
			"The ribcage of an ancient dragon behind the Shiba.",
			pcs(
				lcyl(-46, 2, 0, 48, 1.6, "z", bone, M.SmoothPlastic),
				line(6, -46, -20, -46, 20, function(px, pz)
					return {
						blk(px - 2.2, 2, pz, 0.8, 8, 0.8, bone, M.SmoothPlastic),
						blk(px + 2.2, 2, pz, 0.8, 8, 0.8, bone, M.SmoothPlastic),
					}
				end)
			)
		),
		def(
			"DragonSkull",
			"Dragon Skull",
			"A giant dragon skull with glowing eyes.",
			{
				blk(-46, 0, -58, 12, 4, 8, bone, M.SmoothPlastic),
				blk(-46, 4, -58, 12, 6, 8, bone, M.SmoothPlastic),
				blk(-38, 4, -58, 6, 3, 6, bone, M.SmoothPlastic),
				ball(-40, 6, -61.6, 2.2, flame, M.Neon),
				ball(-40, 6, -54.4, 2.2, flame, M.Neon),
				wedge(-50, 10, -61, 2, 7, 2, bone, M.SmoothPlastic),
				wedge(-50, 10, -55, 2, 7, 2, bone, M.SmoothPlastic),
				blk(-38, 1, -58, 6, 1, 5, deep, M.Slate),
			}
		),
		def(
			"CoinTowers",
			"Coin Towers",
			"Four towers of stacked gold coins.",
			line(4, 24, 30, 24, 60, function(px, pz, i)
				local h = 3 + (i * 4) % 8
				return { cyl(px, 0, pz, 5, h, gold, M.Metal), cyl(px, h, pz, 6, 0.8, gold, M.Metal) }
			end)
		),
		def(
			"ArmorStands",
			"Armor Stands",
			"Dented knight armor left by brave visitors.",
			line(3, -30, 30, -52, 22, function(px, pz)
				return {
					blk(px, 0, pz, 3, 4, 2, rgb(150, 155, 165), M.Metal),
					blk(px, 4, pz, 4, 4, 2.4, rgb(150, 155, 165), M.Metal),
					ball(px, 8, pz, 2.8, rgb(170, 175, 185), M.Metal),
					blk(px, 5, pz + 3, 1.2, 4, 1.2, rgb(150, 155, 165), M.Metal),
					blk(px, 5, pz - 3, 1.2, 4, 1.2, rgb(150, 155, 165), M.Metal),
				}
			end)
		),
		def(
			"SwordsInStone",
			"Swords in the Ground",
			"Six swords stuck in the ground.",
			line(6, 14, -62, 70, -70, function(px, pz, i)
				return {
					blk(px, 0, pz, 0.8, 6, 0.3, rgb(190, 200, 215), M.Metal, i * 30),
					blk(px, 5, pz, 3, 0.6, 0.6, gold, M.Metal, i * 30),
				}
			end)
		),
		def(
			"BabyDragon",
			"Baby Dragon",
			"A little green dragon guarding the loot.",
			{
				blk(40, 1, 52, 8, 4, 5, scale, M.SmoothPlastic),
				blk(44, 4, 52, 3, 4, 3, scale, M.SmoothPlastic),
				ball(46, 6.5, 52, 4, scale, M.SmoothPlastic),
				blk(33, 1.4, 52, 8, 1.6, 1.6, scale, M.SmoothPlastic),
				wedge(40, 5, 47, 5, 4, 1, rgb(30, 110, 55), M.SmoothPlastic, 90),
				wedge(40, 5, 57, 5, 4, 1, rgb(30, 110, 55), M.SmoothPlastic, 270),
				ball(47.6, 8, 51, 0.8, flame, M.Neon),
				ball(47.6, 8, 53, 0.8, flame, M.Neon),
				blk(38, 0, 49.6, 1.4, 1.4, 1.4, scale, M.SmoothPlastic),
				blk(42, 0, 49.6, 1.4, 1.4, 1.4, scale, M.SmoothPlastic),
			}
		),
		def(
			"RuneCircle",
			"Rune Circle",
			"A glowing ring of runes on the ground.",
			pcs(
				around(-60, 0, 10, 12, function(px, pz, deg)
					return mark(px, pz, 2, 2, flame, M.Neon, deg)
				end),
				round(-60, 0, 8, rgb(90, 40, 20), M.Slate),
				round(-60, 0, 3, flame, M.Neon)
			)
		),
		def(
			"FloatingFireballs",
			"Floating Fireballs",
			"Fireballs hover in the air above the lair.",
			line(10, -70, 70, 70, -60, function(px, pz, i)
				return ball(px, 12 + (i * 6) % 20, awayZ(pz), 3 + i % 3, if i % 2 == 0 then flame else ember, M.Neon)
			end)
		),
		def(
			"WingArches",
			"Wing Arches",
			"Two giant wing-shaped arches rise beside the cave.",
			{
				wedge(36, 28, -40, 24, 12, 3, deep, M.Slate, 0),
				wedge(36, 28, 40, 24, 12, 3, deep, M.Slate, 180),
				blk(48, 26, -40, 20, 2, 3, rock, M.Slate),
				blk(48, 26, 40, 20, 2, 3, rock, M.Slate),
				cyl(30, 0, -40, 3, 30, bone, M.SmoothPlastic),
				cyl(30, 0, 40, 3, 30, bone, M.SmoothPlastic),
			}
		),
		def(
			"RockSpires",
			"Rock Spires",
			"Tall rock spires frame the back of the lair.",
			line(7, 74, -66, 74, 66, function(px, pz, i)
				return {
					cyl(px, 0, pz, 9, 14 + (i * 5) % 12, rock, M.Slate),
					cyl(px, 14 + (i * 5) % 12, pz, 5, 8, deep, M.Slate),
				}
			end)
		),
		def(
			"FireMoat",
			"Fire Moat",
			"A stream of fire in front of the cave.",
			{
				blk(16, 0.1, -40, 3, 0.3, 24, flame, M.Neon),
				blk(16, 0.1, 40, 3, 0.3, 24, flame, M.Neon),
				blk(16, 0.1, -58, 3, 0.3, 12, flame, M.Neon),
				blk(16, 0.1, 58, 3, 0.3, 12, flame, M.Neon),
				ball(16, 0.3, -28, 2, ember, M.Neon),
				ball(16, 0.3, 28, 2, ember, M.Neon),
			}
		),
		def(
			"DragonThrone",
			"Dragon Throne",
			"A golden throne of bones inside the cave.",
			{
				blk(58, 0, 0, 10, 2, 10, rock, M.Slate),
				blk(58, 2, 0, 5, 3, 6, gold, M.Metal),
				blk(61, 2, 0, 1.6, 10, 6, gold, M.Metal),
				blk(58, 5, -3.2, 5, 1.6, 1, gold, M.Metal),
				blk(58, 5, 3.2, 5, 1.6, 1, gold, M.Metal),
				wedge(61, 12, -2.6, 1.6, 3, 1.4, bone, M.SmoothPlastic),
				wedge(61, 12, 2.6, 1.6, 3, 1.4, bone, M.SmoothPlastic),
				ball(61, 12.4, 0, 2, rgb(230, 60, 80), M.Glass),
			}
		),
		def(
			"GlowingMushrooms",
			"Glowing Mushrooms",
			"Cave mushrooms glowing teal.",
			line(8, -30, -62, -75, -20, function(px, pz, i)
				return {
					cyl(px, 0, pz, 1.2, 2 + i % 3, bone, M.SmoothPlastic),
					ball(px, 1.6 + i % 3, pz, 3.6 + i % 2, rgb(60, 240, 200), M.Neon),
				}
			end)
		),
		def(
			"DragonEggsLarge",
			"Giant Eggs",
			"Huge speckled eggs on the left side of the lair.",
			pcs(
				ball(-66, 0, 50, 12, scale, M.SmoothPlastic),
				ball(-52, 0, 62, 10, rgb(200, 120, 60), M.SmoothPlastic),
				ball(-74, 0, 36, 9, rgb(90, 100, 220), M.SmoothPlastic),
				line(6, -70, 46, -62, 56, function(px, pz, i)
					return ball(px, 3 + i % 4 * 1.6, pz - 6, 1.6, bone, M.SmoothPlastic)
				end)
			)
		),
		def(
			"GemPiles",
			"Gem Piles",
			"Piles of gold with sparkling gems.",
			line(5, -62, -34, -62, -8, function(px, pz, i)
				return {
					ball(px, 0, pz, 6, gold, M.Metal),
					ball(px + 1, 4, pz, 2.4, if i % 2 == 0 then rgb(230, 60, 80) else rgb(70, 140, 255), M.Glass),
					ball(px - 1.4, 3, pz + 1, 1.8, rgb(80, 220, 120), M.Glass),
				}
			end)
		),
		def(
			"CaveWings",
			"Cave Banners",
			"Green dragon banners hang on tall poles.",
			line(4, 12, -34, 12, 34, function(px, pz, i)
				return {
					cyl(px, 0, pz, 0.8, 14, bone, M.Metal),
					blk(px, 5, pz + 2, 0.4, 8, 3.6, if i % 2 == 0 then scale else flame, M.Fabric),
					ball(px, 14, pz, 1.4, gold, M.Metal),
				}
			end)
		),
		def(
			"GreatDragon",
			"The Great Dragon",
			"A giant green dragon perched on top of the cave, breathing fire.",
			{
				blk(40, 32, 0, 22, 8, 10, scale, M.SmoothPlastic),
				blk(32, 36, 0, 8, 7, 6, scale, M.SmoothPlastic),
				blk(26, 40, 0, 6, 6, 6, scale, M.SmoothPlastic),
				blk(21, 40, 0, 6, 4, 5, scale, M.SmoothPlastic),
				ball(25, 46, -2.4, 1.6, flame, M.Neon),
				ball(25, 46, 2.4, 1.6, flame, M.Neon),
				wedge(24, 46, -2, 1.6, 5, 1.6, bone, M.SmoothPlastic),
				wedge(24, 46, 2, 1.6, 5, 1.6, bone, M.SmoothPlastic),
				wedge(40, 40, -12, 14, 10, 2, rgb(30, 110, 55), M.SmoothPlastic, 0),
				wedge(40, 40, 12, 14, 10, 2, rgb(30, 110, 55), M.SmoothPlastic, 180),
				blk(56, 33, 0, 16, 3, 3, scale, M.SmoothPlastic),
				blk(70, 33, 0, 10, 2, 2, scale, M.SmoothPlastic),
				blk(14, 40, 0, 6, 3, 3, flame, M.Neon),
				ball(9, 40, 0, 5, ember, M.Neon),
			}
		),
	}
	return build("DragonLair", "Dragon Lair", 22, 500, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 23: Mecha Shiba, Mecha Hangar. A steel hangar on the right with a huge empty mecha suit on a stand.

local function mechaHangar(): Theme
	local area = areaOf(23)
	local w, d = area.X / 2, area.Y / 2
	local steel, dark, panel = rgb(110, 130, 160), rgb(44, 54, 72), rgb(150, 168, 195)
	local hazard, black = rgb(255, 200, 0), rgb(24, 26, 32)
	local holo, red = rgb(80, 210, 255), rgb(230, 50, 50)
	local mx = 56

	local function leg(pz: number): { Piece }
		return {
			blk(mx, 1.5, pz, 8, 2, 5.4, dark, M.DiamondPlate),
			blk(mx, 3.5, pz, 4.4, 6, 4, steel, M.Metal),
			ball(mx, 8.6, pz, 4.6, panel, M.Metal),
			blk(mx, 10, pz, 4.8, 5, 4.4, steel, M.Metal),
			blk(mx, 3.5, pz + (if pz > 0 then 2.3 else -2.3), 0.8, 5, 1.6, hazard, M.SmoothPlastic),
		}
	end

	local function crate(px: number, pz: number, c: Color3, ry: number): { Piece }
		return { blk(px, 0, pz, 5, 4, 5, c, M.DiamondPlate, ry), blk(px, 4, pz, 5.4, 0.6, 5.4, hazard, M.SmoothPlastic, ry) }
	end

	local defs = {
		def(
			"HangarFloor",
			"Hangar Floor",
			"Steel diamond-plate flooring with hazard lanes.",
			pcs(
				floorSlabs(w, d, rgb(84, 94, 110), M.DiamondPlate),
				mark(30, -44, 24, 1.2, hazard, M.SmoothPlastic),
				mark(30, 44, 24, 1.2, hazard, M.SmoothPlastic),
				mark(-40, -30, 1.2, 40, hazard, M.SmoothPlastic),
				mark(-40, 30, 1.2, 40, hazard, M.SmoothPlastic),
				mark(60, 0, 26, 26, rgb(60, 70, 88), M.Metal),
				mark(-60, 0, 20, 1.2, holo, M.Neon)
			)
		),
		def(
			"HangarHall",
			"Hangar Hall",
			"A giant hangar with a wide open front.",
			{
				blk(80, 0, 0, 3, 30, 80, steel, M.Metal),
				blk(50, 0, -39, 62, 30, 3, steel, M.Metal),
				blk(50, 0, 39, 62, 30, 3, steel, M.Metal),
				blk(50, 30, 0, 64, 2, 82, dark, M.Metal),
				cyl(20, 0, -37, 3, 30, panel, M.Metal),
				cyl(20, 0, 37, 3, 30, panel, M.Metal),
				blk(50, 0, -37.4, 60, 2, 0.6, hazard, M.SmoothPlastic),
				blk(50, 0, 37.4, 60, 2, 0.6, hazard, M.SmoothPlastic),
				blk(21, 27, 0, 3, 3, 76, hazard, M.SmoothPlastic),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A steel board that reads GET BONKED.", bonkSign(11, -62, -1, dark, hazard, panel, M.Metal)),
		def(
			"GantryCrane",
			"Gantry Crane",
			"A yellow overhead crane runs along the hangar roof.",
			{
				lcyl(36, 27, 0, 76, 2, "z", hazard, M.Metal),
				blk(36, 25, -37, 4, 4, 4, hazard, M.Metal),
				blk(36, 25, 37, 4, 4, 4, hazard, M.Metal),
				blk(36, 25, 10, 5, 2, 5, dark, M.Metal),
				cyl(36, 15, 10, 0.6, 10, black, M.Metal),
				blk(36, 13.5, 10, 3, 1.5, 3, hazard, M.Metal),
				blk(36, 12, 10, 1, 1.5, 2.4, red, M.Metal),
				cyl(36, 0, -37, 1.4, 25, hazard, M.Metal),
				cyl(36, 0, 37, 1.4, 25, hazard, M.Metal),
			}
		),
		def(
			"LaunchRails",
			"Launch Rails",
			"Two long rails lead out of the hangar toward the stage.",
			pcs(
				lcyl(46, 0, -9, 52, 1.2, "x", panel, M.Metal),
				lcyl(46, 0, 9, 52, 1.2, "x", panel, M.Metal),
				line(8, 24, 0, 70, 0, function(px, pz)
					return blk(px, 0, pz, 1.6, 0.5, 21, dark, M.Metal)
				end)
			)
		),
		def(
			"SuitStand",
			"Mecha Suit Stand",
			"A yellow frame and platform that hold the mecha suit.",
			pcs(
				blk(mx, 0, 0, 20, 1.5, 20, dark, M.DiamondPlate),
				blk(mx, 0, 0, 22, 0.5, 22, hazard, M.SmoothPlastic),
				line(2, mx - 9, -9, mx - 9, 9, function(px, pz)
					return cyl(px, 1.5, pz, 1.4, 26, hazard, M.Metal)
				end),
				line(2, mx + 9, -9, mx + 9, 9, function(px, pz)
					return cyl(px, 1.5, pz, 1.4, 26, hazard, M.Metal)
				end),
				blk(mx - 9, 27, 0, 1.4, 1.4, 20, hazard, M.Metal),
				blk(mx + 9, 27, 0, 1.4, 1.4, 20, hazard, M.Metal)
			)
		),
		def("MechaLegs", "Mecha Legs", "Two heavy armoured legs.", pcs(leg(-4.4), leg(4.4), blk(mx, 14.6, 0, 5, 1.6, 4, dark, M.Metal))),
		def(
			"MechaTorso",
			"Mecha Torso",
			"A broad chest with a glowing cockpit and a backpack.",
			{
				blk(mx, 15.4, 0, 6, 2, 12, dark, M.Metal),
				blk(mx, 17.4, 0, 9, 8, 14, steel, M.Metal),
				blk(mx - 4.6, 20, 0, 0.8, 3.6, 7, holo, M.Neon),
				blk(mx - 4.6, 17.8, 0, 0.8, 1, 10, hazard, M.SmoothPlastic),
				ball(mx, 22.4, -8.4, 5, panel, M.Metal),
				ball(mx, 22.4, 8.4, 5, panel, M.Metal),
				blk(mx + 5.4, 17.4, 0, 3, 8, 10, dark, M.Metal),
				cyl(mx + 6, 25.4, -3, 1.6, 2, black, M.Metal),
				cyl(mx + 6, 25.4, 3, 1.6, 2, black, M.Metal),
				blk(mx - 4.6, 21.8, -4, 0.8, 0.8, 2, red, M.Neon),
				blk(mx - 4.6, 21.8, 4, 0.8, 0.8, 2, red, M.Neon),
			}
		),
		def(
			"MechaArms",
			"Mecha Arms",
			"Two strong arms, one with a cannon.",
			{
				blk(mx, 14, -9.2, 3.2, 8, 3.2, steel, M.Metal),
				blk(mx, 14, 9.2, 3.2, 8, 3.2, steel, M.Metal),
				blk(mx, 9, -9.4, 3.6, 5, 3.6, dark, M.Metal),
				blk(mx, 9, 9.4, 3.6, 5, 3.6, dark, M.Metal),
				ball(mx, 6.8, -9.4, 3.6, panel, M.Metal),
				lcyl(mx - 4, 7.2, 9.4, 8, 2.4, "x", black, M.Metal),
				ball(mx - 8.4, 7.4, 9.4, 1.8, red, M.Neon),
			}
		),
		def(
			"MechaHead",
			"Mecha Head",
			"A helmet with a glowing visor and antennas.",
			{
				cyl(mx, 25.4, 0, 2.4, 1.6, dark, M.Metal),
				blk(mx, 26.6, 0, 5.4, 4, 5.4, steel, M.Metal),
				blk(mx - 2.8, 27.8, 0, 0.6, 1.2, 4.4, holo, M.Neon),
				blk(mx, 30.6, 0, 3, 0.8, 5.6, hazard, M.SmoothPlastic),
				cyl(mx + 1, 30.6, -2.2, 0.3, 4, panel, M.Metal),
				cyl(mx + 1, 30.6, 2.2, 0.3, 4, panel, M.Metal),
				ball(mx + 1, 34.6, -2.2, 0.8, red, M.Neon),
				ball(mx + 1, 34.6, 2.2, 0.8, red, M.Neon),
			}
		),
		def(
			"HoloDisplay",
			"Holo Display",
			"Blue hologram screens next to the stand.",
			{
				blk(30, 0, -18, 6, 1, 6, dark, M.Metal),
				blk(30, 1, -18, 1.4, 10, 12, holo, M.Neon),
				blk(30, 0, 18, 6, 1, 6, dark, M.Metal),
				blk(30, 1, 18, 1.4, 10, 12, holo, M.Neon),
				cyl(36, 0, 0, 5, 2, dark, M.Metal),
				ball(36, 2.4, 0, 5, holo, M.Neon),
				blk(31, 6, -18, 0.6, 1, 8, dark, M.Metal),
				blk(31, 6, 18, 0.6, 1, 8, dark, M.Metal),
			}
		),
		def(
			"HazardBarriers",
			"Hazard Barriers",
			"Striped barriers keep visitors away from the rails.",
			line(8, 14, -50, 14, 50, function(px, pz, i)
				return { blk(px, 0, pz, 1.6, 2.4, 6, if i % 2 == 0 then hazard else black, M.SmoothPlastic) }
			end)
		),
		def(
			"AmmoCrates",
			"Supply Crates",
			"Stacks of metal supply crates.",
			pcs(
				crate(30, -34, steel, 0),
				crate(36, -34, panel, 10),
				crate(33, -34, dark, 0),
				blk(33, 4.6, -34, 5, 4, 5, steel, M.DiamondPlate, 20),
				crate(30, 34, panel, -5),
				crate(36, 34, steel, 0)
			)
		),
		def(
			"FuelTanks",
			"Fuel Tanks",
			"Round fuel tanks with pipes.",
			pcs(
				line(3, 70, -30, 70, 30, function(px, pz)
					return {
						cyl(px, 0, pz, 10, 12, panel, M.Metal),
						ball(px, 10, pz, 10, panel, M.Metal),
						cyl(px - 5.2, 0, pz, 1, 8, hazard, M.Metal),
					}
				end)
			)
		),
		def(
			"ControlTower",
			"Control Tower",
			"A tower with a glass cabin to run the hangar.",
			{
				blk(24, 0, -56, 12, 24, 12, steel, M.Metal),
				blk(24, 24, -56, 16, 7, 16, dark, M.Metal),
				blk(15.8, 24.6, -56, 0.6, 5, 14, holo, M.Glass),
				blk(24, 31, -56, 18, 1.2, 18, hazard, M.SmoothPlastic),
				blk(17.8, 8, -56, 0.6, 6, 5, holo, M.Neon),
				blk(17.8, 0, -56, 0.6, 7, 3, black, M.Metal),
			}
		),
		def(
			"RadarDish",
			"Radar Dish",
			"A radar dish on top of the control tower.",
			{
				cyl(24, 32.2, -56, 1.2, 5, panel, M.Metal),
				cyl(24, 37, -56, 9, 0.8, panel, M.Metal),
				ball(24, 36, -56, 2, red, M.Neon),
				cyl(22, 37, -56, 0.6, 5, panel, M.Metal),
				ball(22, 42, -56, 1.2, hazard, M.Neon),
			}
		),
		def(
			"WeldingArms",
			"Welding Robots",
			"Two robot arms that weld the mecha suit.",
			pcs(
				line(2, 40, -22, 40, 22, function(px, pz)
					return {
						cyl(px, 0, pz, 3, 2, dark, M.Metal),
						blk(px, 2, pz, 1.6, 8, 1.6, hazard, M.Metal),
						blk(px + 2, 8.6, pz, 5, 1.4, 1.4, hazard, M.Metal, 0),
						ball(px + 4.6, 8, pz, 1.4, holo, M.Neon),
					}
				end)
			)
		),
		def(
			"ToolWall",
			"Tool Wall",
			"A wall rack full of big tools.",
			{
				blk(79, 0, -20, 1.2, 12, 24, dark, M.Metal),
				blk(77.8, 8, -26, 0.6, 3, 1, hazard, M.Metal),
				blk(77.8, 3, -20, 0.6, 5, 1, red, M.Metal),
				blk(77.8, 6, -14, 3, 1, 0.8, panel, M.Metal),
				blk(77.8, 2, -24, 3, 1, 0.8, panel, M.Metal),
				cyl(77.8, 7, -17, 2, 0.6, hazard, M.Metal),
				ball(77.6, 4, -16, 2, panel, M.Metal),
			}
		),
		def(
			"Spotlights",
			"Spotlights",
			"Bright spotlights on tall poles.",
			pcs(
				line(5, 12, -66, 12, 66, function(px, pz)
					return lamp(px, pz, dark, holo, 12)
				end)
			)
		),
		def(
			"PartsConveyor",
			"Parts Conveyor",
			"A conveyor belt carrying robot parts.",
			pcs(
				blk(-40, 0, -56, 40, 1.4, 5, dark, M.Metal),
				blk(-40, 1.4, -56, 38, 0.2, 3.4, black, M.Slate),
				line(5, -54, -56, -26, -56, function(px, pz, i)
					return blk(px, 1.6, pz, 2.4, 2 + i % 2, 2.4, if i % 2 == 0 then hazard else panel, M.Metal)
				end),
				cyl(-62, 0, -56, 3, 3, dark, M.Metal),
				cyl(-18, 0, -56, 3, 3, dark, M.Metal)
			)
		),
		def(
			"MiniDrones",
			"Mini Drones",
			"Small drones hover around the hangar.",
			line(5, 20, -50, 70, 50, function(px, pz, i)
				return {
					blk(px, 14 + i * 2, pz, 3, 1, 3, steel, M.Metal),
					ball(px, 15 + i * 2, pz, 1.4, holo, M.Neon),
					blk(px, 15 + i * 2, pz, 6, 0.2, 0.6, panel, M.Metal, 45),
				}
			end)
		),
		def(
			"CargoStack",
			"Cargo Containers",
			"Colourful stacked cargo containers.",
			{
				blk(-40, 0, 56, 16, 6, 6, rgb(200, 70, 60), M.CorrodedMetal),
				blk(-40, 6, 56, 16, 6, 6, rgb(60, 110, 190), M.CorrodedMetal),
				blk(-58, 0, 56, 16, 6, 6, rgb(230, 190, 50), M.CorrodedMetal),
				blk(-58, 6, 56, 16, 6, 6, rgb(70, 160, 90), M.CorrodedMetal),
				blk(-40, 0, 66, 16, 6, 6, rgb(70, 160, 90), M.CorrodedMetal),
				blk(-58, 0, 66, 16, 6, 6, rgb(200, 70, 60), M.CorrodedMetal),
			}
		),
		def(
			"Forklift",
			"Forklift",
			"A yellow forklift that carries a crate.",
			{
				blk(30, 1, 50, 6, 3, 4, hazard, M.Metal),
				blk(32, 4, 50, 2, 5, 4, hazard, M.Metal),
				cyl(28.4, 0, 48, 2, 1, black, M.Slate),
				cyl(31.6, 0, 52, 2, 1, black, M.Slate),
				blk(26, 0.4, 50, 4, 0.4, 3, panel, M.Metal),
				blk(25, 0.8, 50, 3, 3, 3, steel, M.DiamondPlate),
				blk(32.6, 4, 48, 0.5, 6, 0.5, dark, M.Metal),
				blk(32.6, 4, 52, 0.5, 6, 0.5, dark, M.Metal),
			}
		),
		def(
			"ScoutWalker",
			"Scout Walker",
			"A small two-legged scout mecha.",
			{
				blk(26, 0, -40, 2, 4, 2, steel, M.Metal),
				blk(26, 0, -44, 2, 4, 2, steel, M.Metal),
				blk(26, 4, -42, 5, 3, 6, panel, M.Metal),
				blk(24, 7, -42, 3, 2, 4, holo, M.Neon),
				lcyl(23, 5, -42, 4, 1, "x", black, M.Metal),
				blk(28.4, 7, -42, 1.2, 2, 3, dark, M.Metal),
			}
		),
		def(
			"PowerGenerators",
			"Power Generators",
			"Humming generators with glowing coils.",
			line(4, 66, 22, 66, 62, function(px, pz, i)
				return {
					blk(px, 0, pz, 6, 3, 6, dark, M.Metal),
					cyl(px, 3, pz, 4, 5 + i % 2 * 2, steel, M.Metal),
					cyl(px, 6 + i % 2 * 2, pz, 4.6, 0.6, holo, M.Neon),
					ball(px, 8 + i % 2 * 2, pz, 3, holo, M.Neon),
				}
			end)
		),
		def(
			"LandingPad",
			"Landing Pad",
			"A round landing pad with glowing rings.",
			pcs(
				round(-66, 40, 26, dark, M.Metal),
				round(-66, 40, 20, hazard, M.SmoothPlastic),
				round(-66, 40, 17, dark, M.Metal),
				around(-66, 40, 11, 8, function(px, pz)
					return ball(px, 0.1, pz, 1.4, holo, M.Neon)
				end),
				blk(-66, 0.2, 40, 2, 0.2, 8, hazard, M.SmoothPlastic)
			)
		),
		def(
			"MissileRack",
			"Missile Rack",
			"A rack of big white missiles.",
			pcs(
				blk(70, 0, -56, 12, 1, 10, dark, M.Metal),
				line(4, 66, -58.5, 74, -58.5, function(px, pz)
					return {
						cyl(px, 1, pz, 2, 12, rgb(235, 238, 245), M.SmoothPlastic),
						cyl(px, 13, pz, 1.2, 2, red, M.SmoothPlastic),
					}
				end),
				line(4, 66, -53.5, 74, -53.5, function(px, pz)
					return cyl(px, 1, pz, 2, 11, rgb(235, 238, 245), M.SmoothPlastic)
				end)
			)
		),
		def(
			"HoloRings",
			"Holo Rings",
			"Glowing rings float high above the hangar.",
			pcs(
				aroundV(50, 46, 0, 14, 8, "x", function(px, py, pz)
					return ball(px, py, pz, 4.4, holo, M.Neon)
				end),
				aroundV(50, 46, 0, 22, 8, "x", function(px, py, pz)
					return ball(px, py, pz, 3.2, hazard, M.Neon)
				end)
			)
		),
		def(
			"WarningBeacons",
			"Warning Beacons",
			"Red beacons flash along the hangar front.",
			line(6, 18, -40, 18, 40, function(px, pz)
				return { cyl(px, 0, pz, 1, 14, dark, M.Metal), ball(px, 14, pz, 2.6, red, M.Neon) }
			end)
		),
		def(
			"GiantHologram",
			"Giant Mecha Hologram",
			"A huge blue hologram of the mecha floating above the hangar.",
			pcs(
				blk(48, 40, -5, 6, 14, 5, holo, M.Neon),
				blk(48, 40, 5, 6, 14, 5, holo, M.Neon),
				blk(48, 54, 0, 8, 6, 18, holo, M.Neon),
				blk(48, 60, 0, 10, 14, 24, holo, M.Neon),
				ball(48, 72, -15, 9, holo, M.Neon),
				ball(48, 72, 15, 9, holo, M.Neon),
				blk(48, 60, -17, 6, 16, 6, holo, M.Neon),
				blk(48, 60, 17, 6, 16, 6, holo, M.Neon),
				blk(48, 74, 0, 8, 8, 8, holo, M.Neon),
				blk(44, 76, 0, 0.8, 2, 7, hazard, M.Neon),
				aroundV(48, 62, 0, 34, 6, "x", function(px, py, pz)
					return ball(px, py, pz, 3, hazard, M.Neon)
				end)
			)
		),
	}
	return build("MechaHangar", "Mecha Hangar", 23, 600, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 24: Galaxy Shiba, Observatory. A night-blue observatory with a slit dome, a long telescope and planets in the sky.

local function observatory(): Theme
	local area = areaOf(24)
	local w, d = area.X / 2, area.Y / 2
	local night, deep, violet = rgb(38, 32, 86), rgb(20, 16, 52), rgb(120, 78, 210)
	local pink, star, gold = rgb(255, 110, 220), rgb(245, 245, 255), rgb(255, 210, 90)
	local cyan = rgb(90, 220, 255)
	local ox = 52

	local function telescope(px: number, pz: number, s: number, ry: number): { Piece }
		return {
			cyl(px, 0, pz, 0.8 * s, 4 * s, deep, M.Metal),
			raw(px, 5 * s, pz, 5 * s, 1.4 * s, 1.4 * s, violet, M.Metal, CYLINDER, Vector3.new(0, ry, 35)),
			ball(px - 2.6 * s, 6.6 * s, pz, 1.1 * s, cyan, M.Neon),
		}
	end

	local defs = {
		def(
			"NightFloor",
			"Night Floor",
			"Dark blue flooring dotted with stars.",
			pcs(
				floorSlabs(w, d, night, M.Slate),
				line(12, -80, -70, 80, 70, function(px, pz, i)
					return mark(px, pz + (i * 17) % 30 - 15, 1.4, 1.4, star, M.Neon, 45)
				end),
				round(-60, 0, 20, violet, M.Slate)
			)
		),
		def(
			"DomeBase",
			"Observatory Base",
			"A round stone building under the dome.",
			{
				cyl(ox, 0, 0, 38, 2, deep, M.Slate),
				cyl(ox, 2, 0, 36, 12, night, M.Slate),
				cyl(ox, 14, 0, 37, 1, violet, M.Metal),
				blk(ox - 18.2, 2, -6, 0.8, 7, 2.6, cyan, M.Neon),
				blk(ox - 18.2, 2, 6, 0.8, 7, 2.6, cyan, M.Neon),
				blk(ox - 18.2, 8, -14, 0.8, 4, 2.6, cyan, M.Neon),
				blk(ox - 18.2, 8, 14, 0.8, 4, 2.6, cyan, M.Neon),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A starry board that reads GET BONKED.", bonkSign(11, 66, -1, deep, pink, violet, M.Slate)),
		def(
			"ObservatoryDome",
			"Observatory Dome",
			"A big dome with a glowing slit for the telescope.",
			{
				ball(ox, 12, 0, 34, violet, M.Metal),
				blk(ox - 16.4, 22, 0, 1.4, 22, 4, cyan, M.Neon),
				cyl(ox, 11.6, 0, 35, 0.8, gold, M.Metal),
				cyl(ox, 44, 0, 1, 4, gold, M.Metal),
				ball(ox, 48, 0, 2.4, pink, M.Neon),
			}
		),
		def(
			"EntranceSteps",
			"Entrance Steps",
			"Wide steps up to the observatory door.",
			{
				blk(31.4, 0, 0, 3, 0.8, 14, deep, M.Slate),
				blk(33, 0, 0, 3, 1.6, 12, night, M.Slate),
				blk(34.6, 0, 0, 3, 2.4, 10, deep, M.Slate),
				blk(32, 0.8, -7.6, 0.8, 1.6, 0.8, gold, M.Metal),
				blk(32, 0.8, 7.6, 0.8, 1.6, 0.8, gold, M.Metal),
				ball(32, 2.4, -7.6, 1.2, pink, M.Neon),
				ball(32, 2.4, 7.6, 1.2, pink, M.Neon),
			}
		),
		def(
			"MainTelescope",
			"Giant Telescope",
			"A long telescope poking out of the dome.",
			{
				raw(31, 36, 0, 26, 4, 4, violet, M.Metal, CYLINDER, Vector3.new(0, 0, 130)),
				raw(24.4, 43.6, 0, 3, 5, 5, gold, M.Metal, CYLINDER, Vector3.new(0, 0, 130)),
				raw(37.6, 28.4, 0, 3, 2.4, 2.4, deep, M.Metal, CYLINDER, Vector3.new(0, 0, 130)),
				cyl(ox - 14, 20, 0, 2, 8, deep, M.Metal),
				ball(23.2, 44.8, 0, 3, cyan, M.Neon),
			}
		),
		def(
			"StarLamps",
			"Star Lamps",
			"Purple lamps along the path.",
			pcs(
				line(5, 10, -60, 10, 60, function(px, pz)
					return lamp(px, pz, deep, pink, 8)
				end)
			)
		),
		def(
			"ObservationDeck",
			"Observation Deck",
			"A railing around the base for stargazing.",
			pcs(
				around(ox, 0, 22, 14, function(px, pz)
					return cyl(px, 0, pz, 0.8, 3, gold, M.Metal)
				end),
				cyl(ox, 0, 0, 46, 0.4, violet, M.Metal)
			)
		),
		def(
			"StarPillars",
			"Star Pillars",
			"Six pillars crowned with glowing stars.",
			line(6, 20, -50, 20, 50, function(px, pz)
				return { cyl(px, 0, pz, 2.4, 9, night, M.Marble), ball(px, 9, pz, 3.4, gold, M.Neon) }
			end)
		),
		def(
			"StarChartTable",
			"Star Chart Table",
			"A table with a glowing map of the night sky.",
			{
				cyl(30, 0, 40, 3, 4, deep, M.Metal),
				cyl(30, 4, 40, 10, 1, violet, M.Metal),
				cyl(30, 5, 40, 9, 0.3, cyan, M.Neon),
				ball(30, 6, 40, 2.4, gold, M.Neon),
				blk(26, 0, 46, 3, 2, 3, night, M.Slate),
				blk(34, 0, 46, 3, 2, 3, night, M.Slate),
			}
		),
		def(
			"StoneBenches",
			"Stone Benches",
			"Benches to watch the stars.",
			line(4, 14, -30, 14, 30, function(px, pz)
				return { blk(px, 0, pz, 2.4, 1.4, 6, night, M.Slate), blk(px + 1, 1.4, pz, 0.6, 2, 6, violet, M.Slate) }
			end)
		),
		def(
			"Orrery",
			"Orrery",
			"A model of the planets on golden rods.",
			{
				cyl(-60, 0, -40, 6, 1.4, deep, M.Metal),
				cyl(-60, 1.4, -40, 1, 14, gold, M.Metal),
				ball(-60, 14, -40, 6, gold, M.Neon),
				blk(-60, 8, -35, 10, 0.4, 0.4, gold, M.Metal),
				ball(-55, 8.6, -35, 2, rgb(80, 150, 255), M.SmoothPlastic),
				blk(-60, 10, -45, 12, 0.4, 0.4, gold, M.Metal, 40),
				ball(-65, 10.6, -45, 2.6, rgb(255, 120, 70), M.SmoothPlastic),
				ball(-52, 13, -40, 1.6, star, M.SmoothPlastic),
			}
		),
		def(
			"CrystalPrisms",
			"Crystal Prisms",
			"Glowing prisms that split starlight.",
			line(6, 66, -60, 66, 60, function(px, pz, i)
				return blk(px, 0, pz, 3, 6 + i % 3 * 3, 3, if i % 2 == 0 then cyan else pink, M.Neon, 45)
			end)
		),
		def(
			"SatelliteDish",
			"Satellite Dish",
			"A big dish listening to the stars.",
			{
				cyl(30, 0, -50, 1.6, 8, deep, M.Metal),
				raw(30, 9, -50, 10, 1, 10, star, M.Metal, CYLINDER, Vector3.new(0, 0, 35)),
				cyl(32, 8, -50, 0.5, 5, gold, M.Metal),
				ball(32.6, 13, -50, 1.4, pink, M.Neon),
				blk(30, 0, -50, 6, 1, 6, night, M.Slate),
			}
		),
		def(
			"RocketModel",
			"Model Rocket",
			"A white model rocket on a launch stand.",
			{
				blk(-62, 0, 40, 9, 1, 9, deep, M.Metal),
				cyl(-62, 1, 40, 4, 12, star, M.SmoothPlastic),
				cyl(-62, 13, 40, 2.4, 2, pink, M.SmoothPlastic),
				ball(-62, 15, 40, 2, pink, M.SmoothPlastic),
				wedge(-62, 1, 36.6, 0.8, 4, 3, violet, M.SmoothPlastic, 90),
				wedge(-62, 1, 43.4, 0.8, 4, 3, violet, M.SmoothPlastic, 270),
				ball(-62, 7, 40, 1.4, cyan, M.Neon),
			}
		),
		def(
			"TelescopeRow",
			"Telescope Row",
			"Small telescopes for visitors.",
			line(4, 16, -42, 16, 42, function(px, pz, i)
				return telescope(px, pz, 1.2, 0 + i * 2)
			end)
		),
		def(
			"SpaceGarden",
			"Space Garden",
			"Alien plants glowing in the night.",
			line(8, -34, -32, -76, -74, function(px, pz, i)
				return {
					cyl(px, 0, pz, 0.8, 4 + i % 3 * 2, rgb(60, 200, 160), M.Neon),
					ball(px, 4 + i % 3 * 2, pz, 3, if i % 2 == 0 then pink else cyan, M.Neon),
				}
			end)
		),
		def(
			"MoonRocks",
			"Moon Rocks",
			"Purple rocks from far away.",
			pcs(rocks(-40, 40, 1.4, violet), rocks(-70, 56, 1.8, night), rocks(-52, -64, 1.2, violet), rocks(76, -70, 1.4, night))
		),
		def(
			"StarGate",
			"Star Gate",
			"A glowing arch behind the Shiba.",
			{
				cyl(-40, 0, -12, 3, 18, night, M.Marble),
				cyl(-40, 0, 12, 3, 18, night, M.Marble),
				blk(-40, 18, 0, 3, 3, 30, violet, M.Metal),
				blk(-40, 21, 0, 2, 2, 12, gold, M.Metal),
				blk(-40.6, 2, 0, 0.6, 16, 22, deep, M.Neon),
				ball(-40, 24, 0, 3, pink, M.Neon),
				ball(-40, 19, -12, 2.4, cyan, M.Neon),
				ball(-40, 19, 12, 2.4, cyan, M.Neon),
			}
		),
		def(
			"Comet",
			"Comet",
			"A comet with a long glowing tail.",
			pcs(
				ball(-30, 40, -50, 8, star, M.Neon),
				line(7, -34, -46, -62, -20, function(px, pz, i)
					return ball(px, 38 - i * 1.4, pz, 8 - i, cyan, M.Neon)
				end)
			)
		),
		def(
			"Saturn",
			"Ringed Planet",
			"A floating planet with a ring.",
			pcs(
				ball(20, 50, -66, 16, rgb(240, 190, 120), M.SmoothPlastic),
				around(20, -66, 14, 12, function(px, pz)
					return ball(px - 0.6, 57, pz, 2, gold, M.Neon)
				end)
			)
		),
		def("MoonOrb", "Moon", "A pale moon hanging over the stage.", {
			ball(-60, 70, 62, 26, rgb(225, 225, 235), M.SmoothPlastic),
			ball(-54, 82, 52, 6, rgb(190, 190, 205), M.SmoothPlastic),
			ball(-68, 76, 56, 5, rgb(190, 190, 205), M.SmoothPlastic),
		}),
		def(
			"Constellation",
			"Constellation",
			"Stars shining in the pattern of a great dog.",
			line(14, -76, 20, 76, 70, function(px, pz, i)
				return ball(px, 58 + (i * 11) % 22, awayZ(pz + (i * 7) % 25 - 12), 2.4 + i % 3, star, M.Neon)
			end)
		),
		def(
			"NebulaClouds",
			"Nebula Clouds",
			"Pink and violet glowing clouds high in the sky.",
			{
				ball(40, 84, -30, 40, rgb(150, 70, 200), M.Neon),
				ball(0, 90, 40, 34, rgb(230, 90, 200), M.Neon),
				ball(-40, 86, -34, 38, rgb(110, 70, 220), M.Neon),
				ball(60, 90, 40, 30, rgb(240, 110, 210), M.Neon),
				ball(-60, 92, 40, 30, rgb(140, 80, 230), M.Neon),
				ball(10, 96, -60, 30, rgb(220, 90, 190), M.Neon),
			}
		),
		def(
			"OrbitingPlanets",
			"Orbiting Planets",
			"Small planets circle around the dome.",
			around(ox, 0, 30, 6, function(px, pz, _deg, i)
				return {
					ball(px, 34 + i * 2, pz, 4 + i % 3 * 1.4, ({ rgb(255, 130, 80), cyan, pink, gold, rgb(120, 220, 130), violet })[i], M.SmoothPlastic),
					ball(px + 3, 36 + i * 2, pz, 1.4, star, M.SmoothPlastic),
				}
			end)
		),
		def(
			"SatelliteRing",
			"Satellite Ring",
			"A ring of tiny lights orbiting high above.",
			around(ox, 0, 34, 16, function(px, pz, deg)
				return blk(px, 60, pz, 3, 1, 3, gold, M.Neon, deg)
			end)
		),
		def(
			"AstronautStatue",
			"Astronaut Statue",
			"A white astronaut waving at the stars.",
			pcs(
				cyl(-30, 0, 50, 8, 1.4, deep, M.Metal),
				person(-30, 50, star, rgb(255, 215, 120), 1.4),
				ball(-30, 8.2, 50, 3.6, cyan, M.Glass)
			)
		),
		def(
			"GalaxySwirl",
			"Galaxy Swirl",
			"A glowing spiral galaxy turning above the stage.",
			around(45, 0, 0, 16, function(_px, _pz, deg, i)
				local r = 4 + i * 1.6
				local rad = math.rad(deg)
				return ball(45 + r * math.cos(rad), 50 + i * 0.4, r * math.sin(rad), 4, if i % 2 == 0 then pink else cyan, M.Neon)
			end)
		),
		def(
			"AuroraBanners",
			"Aurora Banners",
			"Tall ribbons of light waving in the sky.",
			line(4, -70, -50, 70, 50, function(px, pz, i)
				return blk(px, 30, pz, 1, 30, 14, if i % 2 == 0 then rgb(120, 255, 200) else rgb(190, 120, 255), M.Neon)
			end)
		),
		def(
			"NebulaBeam",
			"Nebula Beam",
			"The telescope fires a huge beam of pink and violet light into space.",
			pcs(
				cyl(23, 46, 0, 5, 20, pink, M.Neon),
				cyl(23, 66, 0, 8, 20, violet, M.Neon),
				cyl(23, 86, 0, 12, 20, pink, M.Neon),
				cyl(23, 106, 0, 18, 20, violet, M.Neon),
				ball(23, 126, 0, 30, pink, M.Neon),
				ball(23, 56, 0, 9, star, M.Neon),
				ball(23, 76, 0, 12, star, M.Neon),
				ball(23, 96, 0, 16, star, M.Neon),
				aroundV(23, 100, 0, 28, 8, "x", function(px, py, pz)
					return ball(px, py, pz, 4, cyan, M.Neon)
				end)
			)
		),
	}
	return build("Observatory", "Observatory", 24, 700, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 25: Angel Shiba, Cloud Temple. A white marble temple on soft clouds with golden trim, a halo and a beam of light.

local function cloudTemple(): Theme
	local area = areaOf(25)
	local w, d = area.X / 2, area.Y / 2
	local cloud, marble, gold = rgb(232, 238, 255), rgb(244, 242, 234), rgb(255, 214, 110)
	local sky, pink, white = rgb(170, 210, 255), rgb(255, 190, 220), rgb(255, 255, 255)
	local glow = rgb(255, 245, 200)
	local tx = 52

	local function angel(px: number, pz: number, s: number): { Piece }
		return pcs(
			person(px, pz, white, rgb(255, 225, 190), s),
			wedge(px - 1.4 * s, 3 * s, pz - 3 * s, 0.6 * s, 5 * s, 3.4 * s, white, M.SmoothPlastic),
			wedge(px - 1.4 * s, 3 * s, pz + 3 * s, 0.6 * s, 5 * s, 3.4 * s, white, M.SmoothPlastic, 180),
			cyl(px, 7.8 * s, pz, 2.4 * s, 0.3 * s, gold, M.Neon)
		)
	end

	local defs = {
		def(
			"CloudFloor",
			"Cloud Floor",
			"Soft glowing cloud flooring with sky-blue swirls.",
			pcs(
				floorSlabs(w, d, cloud, M.Neon),
				round(-60, 40, 26, sky, M.Neon),
				round(-70, -40, 20, pink, M.Neon),
				round(60, 66, 24, sky, M.Neon),
				round(60, -66, 22, pink, M.Neon),
				round(-40, -70, 16, sky, M.Neon),
				mark(30, 0, 40, 1.2, gold, M.Neon),
				mark(-40, 40, 1.2, 40, gold, M.Neon)
			)
		),
		def(
			"TemplePlatform",
			"Temple Platform",
			"Three wide marble tiers carry the temple.",
			{
				blk(tx, 0, 0, 58, 1.5, 58, marble, M.Marble),
				blk(tx, 1.5, 0, 52, 1.5, 52, cloud, M.Marble),
				blk(tx, 3, 0, 46, 1.5, 46, marble, M.Marble),
				blk(tx - 23.4, 4.5, 0, 0.6, 0.4, 46, gold, M.Neon),
				blk(tx, 4.5, 0, 20, 0.2, 20, gold, M.Neon),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A golden board on white marble posts that reads GET BONKED.", bonkSign(11, 66, -1, marble, gold, white, M.Marble)),
		def(
			"FrontColumns",
			"Front Columns",
			"Eight tall marble columns in front of the temple.",
			line(8, 31, -19, 31, 19, function(px, pz)
				return { cyl(px, 4.5, pz, 3, 16, marble, M.Marble) }
			end)
		),
		def(
			"BackColumns",
			"Back Columns",
			"Eight marble columns behind the altar.",
			line(8, 72, -19, 72, 19, function(px, pz)
				return { cyl(px, 4.5, pz, 3, 16, marble, M.Marble) }
			end)
		),
		def(
			"TempleRoof",
			"Temple Roof",
			"A golden-trimmed marble roof.",
			{
				blk(tx, 20.5, 0, 50, 2, 48, marble, M.Marble),
				blk(tx, 22.5, 0, 40, 2, 38, gold, M.Neon),
				blk(tx, 24.5, 0, 28, 2, 28, marble, M.Marble),
				blk(tx - 24.6, 20.5, 0, 0.6, 2.4, 49, gold, M.Neon),
				ball(tx, 26.5, 0, 4, gold, M.Neon),
				ball(tx - 24, 22, -23, 2.4, gold, M.Neon),
				ball(tx - 24, 22, 23, 2.4, gold, M.Neon),
			}
		),
		def(
			"CloudSteps",
			"Cloud Steps",
			"Soft steps up to the temple.",
			{
				blk(19.8, 0, 0, 2.4, 0.8, 18, cloud, M.Neon),
				blk(21.2, 0, 0, 2.4, 1.6, 16, white, M.Neon),
				blk(22.6, 0, 0, 2.4, 2.4, 14, cloud, M.Neon),
				blk(19.8, 0.8, -9.4, 0.8, 2, 0.8, gold, M.Neon),
				blk(19.8, 0.8, 9.4, 0.8, 2, 0.8, gold, M.Neon),
			}
		),
		def(
			"GoldenAltar",
			"Golden Altar",
			"A glowing golden altar in the middle of the temple.",
			{
				blk(tx + 6, 4.5, 0, 8, 1, 8, gold, M.Metal),
				blk(tx + 6, 5.5, 0, 6, 4, 6, marble, M.Marble),
				blk(tx + 6, 9.5, 0, 8, 1, 8, gold, M.Metal),
				cyl(tx + 6, 10.5, 0, 4, 1, gold, M.Metal),
				ball(tx + 6, 11.5, 0, 3, glow, M.Neon),
			}
		),
		def(
			"GoldenHarp",
			"Golden Harp",
			"A big golden harp with glowing strings.",
			pcs(
				blk(tx - 4, 4.5, -10, 4, 1, 3, gold, M.Metal),
				cyl(tx - 4, 5.5, -10, 1, 9, gold, M.Metal),
				blk(tx - 4, 14, -10, 1.2, 1.2, 9, gold, M.Metal),
				line(7, tx - 4, -13.6, tx - 4, -6.4, function(px, pz)
					return blk(px - 0.2, 6, pz, 0.2, 8, 0.2, glow, M.Neon)
				end)
			)
		),
		def(
			"AngelStatues",
			"Angel Statues",
			"Two white angel statues with halos guard the steps.",
			pcs(angel(16, -18, 1.6), angel(16, 18, 1.6))
		),
		def(
			"FeatherGates",
			"Feather Gates",
			"Two big feather wings frame the temple entrance.",
			{
				wedge(18, 0, -30, 2, 22, 12, white, M.SmoothPlastic),
				wedge(18, 0, 30, 2, 22, 12, white, M.SmoothPlastic, 180),
				wedge(18, 0, -40, 2, 16, 10, cloud, M.SmoothPlastic),
				wedge(18, 0, 40, 2, 16, 10, cloud, M.SmoothPlastic, 180),
				ball(18, 22, -30, 2.4, gold, M.Neon),
				ball(18, 22, 30, 2.4, gold, M.Neon),
			}
		),
		def(
			"HaloLamps",
			"Halo Lamps",
			"Golden lamps with glowing halos line the path.",
			pcs(
				line(5, 9.5, -62, 9.5, 62, function(px, pz)
					return {
						cyl(px, 0, pz, 0.8, 8, gold, M.Metal),
						cyl(px, 8, pz, 3.4, 0.4, glow, M.Neon),
						ball(px, 8.6, pz, 1.4, white, M.Neon),
					}
				end)
			)
		),
		def(
			"CloudBanks",
			"Cloud Banks",
			"Fluffy cloud heaps along the edges.",
			pcs(
				line(4, -84, -80, -30, 80, function(px, pz, i)
					return ball(px, 0, pz, 8 + i % 3 * 3, if i % 2 == 0 then white else cloud, M.Neon)
				end),
				line(4, 30, -80, 84, 80, function(px, pz, i)
					return ball(px, 0, pz, 8 + i % 3 * 3, if i % 2 == 0 then white else cloud, M.Neon)
				end)
			)
		),
		def(
			"LightFountain",
			"Fountain of Light",
			"A fountain that sprays glowing droplets of light.",
			pcs(
				cyl(-60, 0, 0, 16, 1.5, marble, M.Marble),
				cyl(-60, 1.5, 0, 12, 0.5, sky, M.Neon),
				cyl(-60, 1.5, 0, 3, 9, marble, M.Marble),
				cyl(-60, 10, 0, 8, 1, gold, M.Metal),
				ball(-60, 11, 0, 4, glow, M.Neon),
				around(-60, 0, 5, 8, function(px, pz)
					return ball(px, 9, pz, 1.4, glow, M.Neon)
				end)
			)
		),
		def(
			"FlowerBeds",
			"Flower Beds",
			"Pink and white heavenly flowers.",
			line(5, -34, -26, -76, -74, function(px, pz, i)
				return {
					cyl(px, 0, pz, 0.5, 2.6, rgb(130, 200, 140), M.Grass),
					ball(px, 2.4, pz, 2.6, if i % 2 == 0 then pink else white, M.SmoothPlastic),
					ball(px + 1.6, 0.6, pz, 1.6, if i % 2 == 0 then white else pink, M.SmoothPlastic),
				}
			end)
		),
		def(
			"BellPosts",
			"Golden Bells",
			"Posts with golden bells that ring softly.",
			line(4, 14, -48, 14, 48, function(px, pz)
				return {
					cyl(px, 0, pz, 0.8, 9, white, M.Marble),
					blk(px, 8.6, pz, 0.8, 0.8, 4, white, M.Marble),
					cyl(px, 6, pz + 1.8, 2, 2.4, gold, M.Metal),
					ball(px, 5.6, pz + 1.8, 0.8, glow, M.Neon),
				}
			end)
		),
		def(
			"CloudTrees",
			"Cloud Trees",
			"Trees with soft pink and white blossoms.",
			line(5, -34, 24, -76, 72, function(px, pz, i)
				return tree(px, pz, 1.4, rgb(220, 205, 190), if i % 2 == 0 then pink else white, M.Neon)
			end)
		),
		def(
			"MarbleBenches",
			"Marble Benches",
			"White benches to rest on the clouds.",
			line(4, 16, -34, 16, 34, function(px, pz, i)
				return { blk(px, 0, pz, 3, 1.4, 7, marble, M.Marble), blk(px + 1.2, 1.4, pz, 0.6, 2, 7, gold, M.Neon) }
			end)
		),
		def(
			"Candelabras",
			"Golden Candelabras",
			"Three tall golden candelabras with glowing flames.",
			line(3, 36, -26, 36, 26, function(px, pz)
				return {
					cyl(px, 4.5, pz, 0.8, 6, gold, M.Metal),
					blk(px, 10.5, pz, 0.6, 0.6, 5, gold, M.Metal),
					ball(px, 11.1, pz - 2.4, 1.2, glow, M.Neon),
					ball(px, 11.1, pz, 1.2, glow, M.Neon),
					ball(px, 11.1, pz + 2.4, 1.2, glow, M.Neon),
				}
			end)
		),
		def(
			"PearlGate",
			"Pearl Gate",
			"A gate of white pearls behind the Shiba.",
			pcs(
				cyl(-40, 0, -12, 3, 20, marble, M.Marble),
				cyl(-40, 0, 12, 3, 20, marble, M.Marble),
				blk(-40, 20, 0, 3, 2.4, 28, gold, M.Metal),
				line(7, -40, -9, -40, 9, function(px, pz)
					return ball(px, 22.4, pz, 3, white, M.SmoothPlastic)
				end),
				ball(-40, 25, 0, 4, glow, M.Neon)
			)
		),
		def(
			"FloatingIslets",
			"Floating Islets",
			"Small cloud islands hover on the left side.",
			pcs(
				island(-56, 24, -50, 8, cloud, white, M.Neon),
				island(-70, 36, 30, 7, cloud, white, M.Neon),
				island(-40, 30, 64, 6, cloud, white, M.Neon)
			)
		),
		def(
			"Rainbow",
			"Rainbow",
			"A big rainbow arching behind the Shiba.",
			pcs(
				aroundV(-72, 0, 0, 34, 8, "x", function(px, py, pz, deg)
					return if deg <= 180 then ball(px, py, pz, 4, rgb(255, 90, 90), M.Neon) else {}
				end),
				aroundV(-72, 0, 0, 38, 8, "x", function(px, py, pz, deg)
					return if deg <= 180 then ball(px, py, pz, 4, rgb(255, 220, 90), M.Neon) else {}
				end),
				aroundV(-72, 0, 0, 42, 8, "x", function(px, py, pz, deg)
					return if deg <= 180 then ball(px, py, pz, 4, rgb(110, 170, 255), M.Neon) else {}
				end)
			)
		),
		def(
			"SunOrb",
			"Sun Orb",
			"A gold sun orb with rays above the temple.",
			pcs(
				ball(tx + 10, 70, -60, 20, gold, M.Neon),
				aroundV(tx + 10, 80, -60, 18, 8, "x", function(px, py, pz, deg)
					return blk(px, py - 2, pz, 1.4, 2, 6, glow, M.Neon, deg)
				end)
			)
		),
		def(
			"AngelTrumpets",
			"Angel Trumpets",
			"Golden trumpets resting on cloud stands.",
			line(4, 28, -50, 28, 50, function(px, pz)
				return {
					cyl(px, 0, pz, 1, 4, white, M.Marble),
					raw(px, 6, pz, 7, 1, 1, gold, M.Metal, CYLINDER, Vector3.new(0, 0, 40)),
					ball(px - 2.8, 8.4, pz, 2.6, gold, M.Metal),
				}
			end)
		),
		def(
			"GoldenStairs",
			"Stairway to Heaven",
			"Floating golden steps climbing into the sky.",
			line(14, -60, -30, -60, 50, function(px, pz, i)
				return blk(px, 2 + i * 3, pz, 6, 1, 6, if i % 2 == 0 then gold else white, M.Neon)
			end)
		),
		def(
			"FeatherRain",
			"Feather Rain",
			"White feathers drifting down from above.",
			line(16, -80, -70, 80, 70, function(px, pz, i)
				return blk(px, 14 + (i * 9) % 26, awayZ(pz + (i * 5) % 14), 0.6, 4, 1.4, white, M.Neon, i * 25)
			end)
		),
		def(
			"LightPillars",
			"Light Pillars",
			"Slender pillars of light around the temple.",
			line(6, 14, -64, 14, 64, function(px, pz, i)
				return { cyl(px + 4, 0, pz, 1.4, 20 + i * 3, glow, M.Neon), ball(px + 4, 20 + i * 3, pz, 3, white, M.Neon) }
			end)
		),
		def(
			"GiantWings",
			"Giant Wings",
			"Huge white wings spread behind the temple.",
			{
				wedge(84, 0, -20, 4, 44, 26, white, M.SmoothPlastic),
				wedge(84, 0, 20, 4, 44, 26, white, M.SmoothPlastic, 180),
				wedge(86, 0, -36, 4, 30, 14, cloud, M.SmoothPlastic),
				wedge(86, 0, 36, 4, 30, 14, cloud, M.SmoothPlastic, 180),
				blk(84, 44, -20, 3, 2, 22, gold, M.Neon),
				blk(84, 44, 20, 3, 2, 22, gold, M.Neon),
			}
		),
		def(
			"AngelSinger",
			"Singing Angel",
			"A little angel singing on a cloud.",
			pcs(
				ball(-40, 0, -56, 12, white, M.Neon),
				ball(-48, 0, -60, 8, cloud, M.Neon),
				angel(-40, -56, 1.2),
				ball(-34, 9, -56, 1.4, gold, M.Neon),
				ball(-36, 12, -52, 1.4, gold, M.Neon)
			)
		),
		def(
			"LightBeam",
			"Beam of Heaven",
			"A glowing beam of light shines from the sky onto the altar.",
			pcs(
				cyl(tx + 6, 12, 0, 14, 60, glow, M.Neon),
				cyl(tx + 6, 72, 0, 20, 40, white, M.Neon),
				cyl(tx + 6, 112, 0, 28, 30, glow, M.Neon),
				ball(tx + 6, 140, 0, 36, white, M.Neon),
				aroundV(tx + 6, 60, 0, 18, 8, "x", function(px, py, pz)
					return ball(px, py, pz, 4, gold, M.Neon)
				end),
				ball(tx + 6, 12, 0, 8, white, M.Neon)
			)
		),
	}
	return build("CloudTemple", "Cloud Temple", 25, 800, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 26: Demon Shiba, Hell Gate. Black and red rock, a huge horned gate with a swirling portal, lava and a throne.

local function hellGate(): Theme
	local area = areaOf(26)
	local w, d = area.X / 2, area.Y / 2
	local obsidian, redRock, horn = rgb(24, 18, 26), rgb(112, 26, 30), rgb(70, 44, 40)
	local lava, ember, bone = rgb(255, 64, 20), rgb(255, 150, 40), rgb(225, 214, 190)
	local portal, soul = rgb(215, 30, 70), rgb(120, 140, 255)
	local gx = 50

	local function skull(px: number, py: number, pz: number, s: number): { Piece }
		return {
			ball(px, py + 0.8 * s, pz, 3 * s, bone, M.SmoothPlastic),
			blk(px, py, pz, 1.8 * s, 1 * s, 2 * s, bone, M.SmoothPlastic),
			ball(px - 1.3 * s, py + 2 * s, pz - 0.6 * s, 0.7 * s, lava, M.Neon),
			ball(px - 1.3 * s, py + 2 * s, pz + 0.6 * s, 0.7 * s, lava, M.Neon),
		}
	end

	local function flame(px: number, py: number, pz: number, s: number): { Piece }
		return { ball(px, py, pz, 3 * s, lava, M.Neon), ball(px, py + 2 * s, pz, 2 * s, ember, M.Neon) }
	end

	local defs = {
		def(
			"ObsidianGround",
			"Obsidian Ground",
			"Black rock flooring split by glowing red cracks.",
			pcs(
				floorSlabs(w, d, obsidian, M.Slate),
				mark(36, -30, 1.2, 50, lava, M.Neon, 8),
				mark(70, 20, 1.2, 60, lava, M.Neon, -12),
				mark(-40, 50, 1.2, 40, lava, M.Neon, 20),
				mark(-60, -20, 1.2, 50, lava, M.Neon, -6),
				mark(-30, -70, 40, 1.2, lava, M.Neon, 10),
				round(66, 0, 22, redRock, M.Slate)
			)
		),
		def(
			"GatePillars",
			"Gate Pillars",
			"Two giant black pillars with red bases.",
			{
				blk(gx, 0, -23, 14, 3, 14, redRock, M.Slate),
				blk(gx, 0, 23, 14, 3, 14, redRock, M.Slate),
				blk(gx, 3, -23, 9, 34, 9, obsidian, M.Basalt),
				blk(gx, 3, 23, 9, 34, 9, obsidian, M.Basalt),
				blk(gx - 4.6, 6, -23, 0.6, 24, 2, lava, M.Neon),
				blk(gx - 4.6, 6, 23, 0.6, 24, 2, lava, M.Neon),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A charred board that reads GET BONKED.", bonkSign(11, 70, -1, obsidian, lava, redRock, M.Slate)),
		def(
			"GateArch",
			"Gate Arch",
			"A massive arch with spikes joins the pillars.",
			{
				blk(gx, 37, 0, 10, 6, 56, obsidian, M.Basalt),
				blk(gx - 4.6, 38, 0, 0.6, 1.2, 50, lava, M.Neon),
				blk(gx, 43, 0, 6, 4, 40, redRock, M.Slate),
				wedge(gx, 47, -12, 4, 8, 4, obsidian, M.Basalt),
				wedge(gx, 47, 0, 4, 12, 4, obsidian, M.Basalt),
				wedge(gx, 47, 12, 4, 8, 4, obsidian, M.Basalt),
				ball(gx - 3, 44, 0, 4, lava, M.Neon),
			}
		),
		def(
			"LavaMoat",
			"Lava Moat",
			"A river of lava runs in front of the gate.",
			{
				blk(28, 0.1, 0, 6, 0.3, 120, lava, M.Neon),
				blk(28, 0, -62, 9, 1, 10, obsidian, M.Slate),
				blk(28, 0, 62, 9, 1, 10, obsidian, M.Slate),
				ball(28, 0.4, -30, 2.4, ember, M.Neon),
				ball(28, 0.4, 36, 2.4, ember, M.Neon),
				ball(28, 0.4, 10, 2, ember, M.Neon),
			}
		),
		def(
			"DemonThrone",
			"Demon Throne",
			"A spiked throne of black stone behind the gate.",
			{
				blk(70, 0, 0, 16, 1.5, 16, redRock, M.Slate),
				blk(70, 1.5, 0, 12, 1.5, 12, obsidian, M.Basalt),
				blk(70, 3, 0, 7, 3, 7, obsidian, M.Basalt),
				blk(74, 6, 0, 2, 16, 7, obsidian, M.Basalt),
				blk(70, 6, -3.6, 7, 3, 1, obsidian, M.Basalt),
				blk(70, 6, 3.6, 7, 3, 1, obsidian, M.Basalt),
				wedge(74, 22, -2.6, 2, 7, 2, horn, M.Basalt),
				wedge(74, 22, 2.6, 2, 7, 2, horn, M.Basalt),
				ball(72.6, 17, 0, 3, lava, M.Neon),
				blk(67.6, 3, 0, 0.6, 3, 5, lava, M.Neon),
			}
		),
		def(
			"HellfirePortal",
			"Hellfire Portal",
			"A swirling red portal fills the gate.",
			pcs(
				ball(gx, 14, 0, 8, portal, M.Neon),
				aroundV(gx, 20, 0, 8, 6, "x", function(px, py, pz)
					return ball(px, py, pz, 5, lava, M.Neon)
				end),
				aroundV(gx, 20, 0, 15, 9, "x", function(px, py, pz)
					return ball(px, py, pz, 5, portal, M.Neon)
				end)
			)
		),
		def(
			"HornOrnaments",
			"Horn Ornaments",
			"Giant curved horns crown the pillars.",
			{
				wedge(gx - 2, 37, -27, 3, 14, 3, horn, M.Basalt),
				wedge(gx - 2, 37, -19, 3, 14, 3, horn, M.Basalt),
				wedge(gx - 2, 37, 19, 3, 14, 3, horn, M.Basalt),
				wedge(gx - 2, 37, 27, 3, 14, 3, horn, M.Basalt),
				ball(gx - 3, 38, -23, 3, lava, M.Neon),
				ball(gx - 3, 38, 23, 3, lava, M.Neon),
			}
		),
		def(
			"SpikeFence",
			"Spike Fence",
			"A row of black spikes beside the path.",
			line(12, 12, -66, 12, 66, function(px, pz, i)
				return wedge(px, 0, pz, 1.6, 6 + i % 3 * 2, 1.6, obsidian, M.Basalt, 45)
			end)
		),
		def(
			"SkullTorches",
			"Skull Torches",
			"Torches topped with burning skulls.",
			line(2, 16, -48, 16, 48, function(px, pz)
				return pcs(cyl(px, 0, pz, 1, 6, horn, M.Wood), skull(px, 6, pz, 1.6), flame(px, 9, pz, 1))
			end)
		),
		def(
			"LavaFalls",
			"Lava Falls",
			"A cliff pouring lava into a pool.",
			{
				blk(88, 0, 50, 10, 26, 30, redRock, M.Slate),
				blk(88, 26, 50, 8, 6, 24, obsidian, M.Basalt),
				blk(82.6, 3, 50, 0.8, 24, 8, lava, M.Neon),
				cyl(78, 0.1, 50, 14, 0.4, lava, M.Neon),
				ball(78, 0.5, 48, 2.6, ember, M.Neon),
				ball(76, 0.5, 53, 2, ember, M.Neon),
			}
		),
		def(
			"BonePiles",
			"Bone Piles",
			"Heaps of bones and skulls.",
			pcs(
				line(5, 30, -70, 70, -76, function(px, pz, i)
					return lcyl(px, (i % 2) * 0.8, pz, 5, 1, if i % 2 == 0 then "x" else "z", bone, M.SmoothPlastic)
				end),
				skull(40, 0, -72, 2),
				skull(58, 0, -74, 1.6)
			)
		),
		def(
			"HangingCages",
			"Iron Cages",
			"Tall iron cages with glowing red prisoners.",
			line(3, 34, -50, 34, 50, function(px, pz)
				return {
					cyl(px, 0, pz, 0.8, 14, obsidian, M.Metal),
					blk(px + 2, 12, pz, 0.6, 0.6, 5, obsidian, M.Metal),
					blk(px + 4, 7, pz, 4, 5, 4, obsidian, M.DiamondPlate),
					ball(px + 4, 8, pz, 1.8, lava, M.Neon),
				}
			end)
		),
		def(
			"DemonStatues",
			"Demon Statues",
			"Two horned demon statues on stone pedestals.",
			pcs(
				blk(18, 0, -26, 6, 2, 6, redRock, M.Slate),
				blk(18, 0, 26, 6, 2, 6, redRock, M.Slate),
				line(2, 18, -26, 18, 26, function(px, pz)
					return {
						blk(px, 2, pz, 3, 6, 2.4, obsidian, M.Basalt),
						ball(px, 8, pz, 2.8, obsidian, M.Basalt),
						wedge(px, 10, pz - 1.2, 0.8, 3, 0.8, horn, M.Basalt),
						wedge(px, 10, pz + 1.2, 0.8, 3, 0.8, horn, M.Basalt),
						ball(px - 1.2, 8.6, pz - 0.6, 0.6, lava, M.Neon),
						ball(px - 1.2, 8.6, pz + 0.6, 0.6, lava, M.Neon),
					}
				end)
			)
		),
		def(
			"LavaPits",
			"Lava Pits",
			"Pits of molten rock behind the Shiba.",
			pcs(
				cyl(-50, 0.1, 40, 22, 0.4, lava, M.Neon),
				cyl(-72, 0.1, 22, 14, 0.4, lava, M.Neon),
				cyl(-40, 0.1, -50, 18, 0.4, lava, M.Neon),
				around(-50, 40, 12.5, 8, function(px, pz, deg)
					return blk(px, 0, pz, 4, 2, 4, obsidian, M.Slate, deg)
				end),
				ball(-52, 0.5, 38, 3, ember, M.Neon)
			)
		),
		def(
			"ObsidianSpires",
			"Obsidian Spires",
			"Tall black spires with red veins.",
			line(5, -34, -30, -76, -80, function(px, pz, i)
				return {
					cyl(px, 0, pz, 6, 12 + i % 3 * 5, obsidian, M.Basalt),
					cyl(px, 12 + i % 3 * 5, pz, 3, 6, obsidian, M.Basalt),
					blk(px + 2.8, 0, pz, 0.4, 12 + i % 3 * 5, 1, lava, M.Neon),
				}
			end)
		),
		def(
			"FirePits",
			"Fire Pits",
			"Square fire pits with roaring flames.",
			line(4, 36, 24, 36, 70, function(px, pz)
				return pcs(blk(px, 0, pz, 6, 1.6, 6, obsidian, M.Basalt), flame(px, 1.6, pz, 1.4))
			end)
		),
		def(
			"SoulFlames",
			"Soul Flames",
			"Cold blue flames floating in the dark.",
			line(14, -80, 40, 80, -40, function(px, pz, i)
				return ball(px, 6 + (i * 5) % 22, awayZ(pz + (i * 9) % 30 - 15), 2 + i % 3, soul, M.Neon)
			end)
		),
		def(
			"CrackedBridge",
			"Cracked Bridge",
			"A bridge of black stone across the lava moat.",
			{
				blk(28, 1, 0, 8, 1, 14, obsidian, M.Basalt),
				blk(28, 2, -6.6, 8, 1.4, 0.8, redRock, M.Slate),
				blk(28, 2, 6.6, 8, 1.4, 0.8, redRock, M.Slate),
				blk(28, 0, -6, 2, 1, 2, obsidian, M.Basalt),
				blk(28, 0, 6, 2, 1, 2, obsidian, M.Basalt),
				blk(24, 0, 0, 3, 0.6, 12, redRock, M.Slate),
				blk(32, 0, 0, 3, 0.6, 12, redRock, M.Slate),
			}
		),
		def(
			"BloodFountain",
			"Blood Fountain",
			"A fountain spraying glowing crimson liquid.",
			pcs(
				cyl(-60, 0, 0, 16, 1.5, obsidian, M.Slate),
				cyl(-60, 1.5, 0, 13, 0.4, portal, M.Neon),
				cyl(-60, 1.5, 0, 3, 8, obsidian, M.Basalt),
				cyl(-60, 9.5, 0, 8, 1, redRock, M.Slate),
				ball(-60, 10.5, 0, 4, portal, M.Neon),
				around(-60, 0, 5, 6, function(px, pz)
					return ball(px, 8, pz, 1.6, portal, M.Neon)
				end)
			)
		),
		def(
			"BrimstoneVents",
			"Brimstone Vents",
			"Yellow smoking vents.",
			line(4, 60, 40, 76, 76, function(px, pz, i)
				return {
					cyl(px, 0, pz, 5, 1.6, obsidian, M.Slate),
					cyl(px, 1.6, pz, 2, 3, horn, M.Metal),
					ball(px, 5, pz, 4, rgb(220, 200, 80), M.SmoothPlastic),
					ball(px + 1, 8.6, pz, 3 + i % 2, rgb(150, 140, 70), M.SmoothPlastic),
				}
			end)
		),
		def(
			"DemonBanners",
			"Demon Banners",
			"Black and red banners on tall poles.",
			line(4, 9.5, -56, 9.5, 56, function(px, pz, i)
				return {
					cyl(px, 0, pz, 0.8, 16, horn, M.Metal),
					blk(px, 6, pz + 2, 0.4, 9, 4, if i % 2 == 0 then redRock else obsidian, M.Fabric),
					wedge(px, 16, pz, 1, 3, 1, bone, M.SmoothPlastic),
				}
			end)
		),
		def(
			"CrimsonTrees",
			"Crimson Trees",
			"Dead trees with glowing red sap.",
			line(4, -34, -22, -80, 70, function(px, pz, i)
				return {
					cyl(px, 0, pz, 1.6, 12, obsidian, M.Wood),
					blk(px, 8, pz, 1, 1, 7, redRock, M.Wood, 20 * i),
					blk(px, 11, pz, 1, 1, 6, redRock, M.Wood, 20 * i + 80),
					ball(px, 12, pz, 1.4, lava, M.Neon),
				}
			end)
		),
		def(
			"RedMoon",
			"Red Moon",
			"A huge blood-red moon low in the sky.",
			{
				ball(-30, 70, -68, 44, rgb(190, 30, 40), M.Neon),
				ball(-22, 84, -72, 8, rgb(130, 20, 30), M.SmoothPlastic),
				ball(-44, 78, -64, 6, rgb(130, 20, 30), M.SmoothPlastic),
				ball(-34, 64, -60, 10, rgb(130, 20, 30), M.SmoothPlastic),
			}
		),
		def(
			"EmberClouds",
			"Ember Clouds",
			"Dark clouds lit red from below.",
			{
				ball(40, 70, 40, 34, rgb(50, 30, 34), M.SmoothPlastic),
				ball(-20, 76, 40, 30, rgb(60, 34, 38), M.SmoothPlastic),
				ball(70, 74, -30, 32, rgb(54, 30, 34), M.SmoothPlastic),
				ball(0, 80, -34, 30, rgb(46, 26, 30), M.SmoothPlastic),
				ball(-50, 72, 70, 28, rgb(60, 34, 38), M.SmoothPlastic),
				ball(30, 66, 74, 24, lava, M.Neon),
			}
		),
		def(
			"FlyingImps",
			"Flying Imps",
			"Little red imps buzzing around.",
			line(4, 20, -60, 80, 60, function(px, pz, i)
				return {
					blk(px, 14 + i * 3, pz, 1.8, 2, 1.8, portal, M.SmoothPlastic),
					ball(px, 16 + i * 3, pz, 1.6, portal, M.SmoothPlastic),
					wedge(px, 14.6 + i * 3, pz - 2.2, 3, 1.6, 0.4, obsidian, M.SmoothPlastic),
					wedge(px, 14.6 + i * 3, pz + 2.2, 3, 1.6, 0.4, obsidian, M.SmoothPlastic, 180),
				}
			end)
		),
		def(
			"SkullMountain",
			"Skull Mountain",
			"A mountain of skulls at the back of the stage.",
			pcs(
				cyl(80, 0, -62, 20, 6, redRock, M.Slate),
				skull(80, 6, -62, 5),
				skull(74, 6, -56, 3.4),
				skull(86, 6, -68, 3.4)
			)
		),
		def(
			"GateFlames",
			"Gate Flames",
			"Tall flames burning on top of both pillars.",
			pcs(
				flame(gx, 37, -23, 3.4),
				flame(gx, 37, 23, 3.4),
				flame(gx, 45, -23, 2),
				flame(gx, 45, 23, 2),
				ball(gx, 52, -23, 4, ember, M.Neon),
				ball(gx, 52, 23, 4, ember, M.Neon)
			)
		),
		def(
			"LavaTornado",
			"Lava Tornado",
			"A swirling tower of fire behind the Shiba.",
			line(8, -60, -60, -60, -60, function(px, pz, i)
				return {
					cyl(px, (i - 1) * 6, pz, 4 + i * 2.2, 5.6, if i % 2 == 0 then lava else ember, M.Neon),
					ball(px + 6 + i, (i - 1) * 6 + 2, pz + 4, 2, lava, M.Neon),
				}
			end)
		),
		def(
			"DemonSkullCrown",
			"Demon Skull",
			"A giant horned skull with burning eyes floats above the gate.",
			{
				ball(gx, 60, 0, 30, bone, M.SmoothPlastic),
				blk(gx, 54, 0, 16, 6, 22, bone, M.SmoothPlastic),
				ball(gx - 12, 70, -7, 7, lava, M.Neon),
				ball(gx - 12, 70, 7, 7, lava, M.Neon),
				wedge(gx, 80, -14, 5, 26, 5, horn, M.Basalt),
				wedge(gx, 80, 14, 5, 26, 5, horn, M.Basalt),
				blk(gx - 14, 62, 0, 2, 4, 3, obsidian, M.Basalt),
				blk(gx - 14, 55, -6, 2, 4, 2, bone, M.SmoothPlastic),
				blk(gx - 14, 55, -2, 2, 4, 2, bone, M.SmoothPlastic),
				blk(gx - 14, 55, 2, 2, 4, 2, bone, M.SmoothPlastic),
				blk(gx - 14, 55, 6, 2, 4, 2, bone, M.SmoothPlastic),
				ball(gx, 90, 0, 12, lava, M.Neon),
				ball(gx, 98, 0, 8, ember, M.Neon),
			}
		),
	}
	return build("HellGate", "Hell Gate", 26, 900, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 27: Giant Shiba, Beanstalk and Stone Circle. Everything is giant: standing stones, a stool, a club, a beanstalk
-- that reaches a cloud castle (scaled for a 16-stud Shiba).

local function beanstalk(): Theme
	local area = areaOf(27)
	local w, d = area.X / 2, area.Y / 2
	local grass, dirt = rgb(96, 170, 70), rgb(120, 90, 60)
	local stone, moss = rgb(145, 146, 154), rgb(80, 130, 70)
	local stalk, leaf = rgb(64, 170, 72), rgb(100, 205, 84)
	local gold, wood, white = rgb(255, 210, 60), rgb(140, 98, 58), rgb(250, 250, 250)
	local sx, sz = 62, 44
	local cx, cz = 56, -36

	local function leaves(y0: number, step: number, rad: number): { Piece }
		return around(sx, sz, rad, 4, function(px, pz, _deg, i)
			local y = y0 + (i - 1) * step
			return { cyl(px, y, pz, 16, 1, leaf, M.Grass), cyl((px + sx) / 2, y - 0.4, (pz + sz) / 2, 1.4, 1, stalk, M.Grass) }
		end)
	end

	local function bigFlower(px: number, pz: number, c: Color3): { Piece }
		return pcs(
			cyl(px, 0, pz, 1.4, 12, stalk, M.Grass),
			ball(px, 11.4, pz, 4, gold, M.SmoothPlastic),
			around(px, pz, 4.2, 6, function(ax, az)
				return ball(ax, 11.2, az, 4.2, c, M.SmoothPlastic)
			end)
		)
	end

	local defs = {
		def(
			"MeadowFloor",
			"Meadow Floor",
			"Green meadow flooring with dirt patches and wildflowers.",
			pcs(
				floorSlabs(w, d, grass, M.Grass),
				round(-60, 0, 26, dirt, M.Ground),
				round(30, 60, 20, dirt, M.Ground),
				round(70, 80, 16, dirt, M.Ground),
				round(-50, -70, 22, dirt, M.Ground),
				line(8, -80, -90, 80, 90, function(px, pz, i)
					return round(px, pz + (i * 7) % 20 - 10, 1.6, if i % 2 == 0 then rgb(255, 230, 90) else rgb(255, 150, 200), M.SmoothPlastic)
				end)
			)
		),
		def(
			"StandingStones",
			"Standing Stones",
			"A circle of eight tall grey standing stones.",
			around(cx, cz, 26, 8, function(px, pz, deg, i)
				return blk(px, 0, pz, 7, 16 + (i % 3) * 2, 3.6, stone, M.Slate, -deg)
			end)
		),
		def("BonkSign", "Get Bonked Sign", "A huge wooden board on log posts that reads GET BONKED.", bonkSign(11, 74, -1, wood, gold, rgb(110, 76, 44), M.Wood)),
		def(
			"StoneCaps",
			"Stone Caps",
			"Flat capstones rest on top of four stones.",
			around(cx, cz, 26, 4, function(px, pz, deg)
				return blk(px, 18, pz, 10, 2, 5, stone, M.Slate, -deg)
			end)
		),
		def(
			"CenterAltar",
			"Altar Stone",
			"A mossy flat stone in the middle of the circle.",
			{
				blk(cx, 0, cz, 14, 3, 10, stone, M.Slate, 10),
				blk(cx, 3, cz, 10, 1.4, 7, moss, M.Grass, 10),
				ball(cx, 4.4, cz, 4, gold, M.Neon),
				ball(cx + 5, 0, cz + 4, 4, stone, M.Slate),
				ball(cx - 5, 0, cz - 4, 3, stone, M.Slate),
			}
		),
		def(
			"GiantStool",
			"Giant Stool",
			"A wooden stool as big as a house.",
			{
				cyl(-52, 16, 42, 24, 4, wood, M.Wood),
				cyl(-59, 0, 35, 5, 16, wood, M.Wood),
				cyl(-45, 0, 35, 5, 16, wood, M.Wood),
				cyl(-59, 0, 49, 5, 16, wood, M.Wood),
				cyl(-45, 0, 49, 5, 16, wood, M.Wood),
				blk(-52, 6, 35, 14, 1.4, 1.4, wood, M.Wood),
				blk(-52, 6, 49, 14, 1.4, 1.4, wood, M.Wood),
				cyl(-52, 20, 42, 20, 0.6, rgb(160, 115, 70), M.Wood),
			}
		),
		def(
			"GiantClub",
			"Giant Club",
			"A huge spiked wooden club lying on the grass.",
			pcs(
				lcyl(-72, 0, -60, 40, 5, "z", wood, M.Wood),
				ball(-72, 0, -84, 14, wood, M.Wood),
				line(6, -76, -86, -68, -82, function(px, pz, i)
					return ball(px, 4 + i % 2 * 5, pz + (i % 3) * 2 - 2, 2.4, rgb(110, 110, 120), M.Metal)
				end)
			)
		),
		def(
			"StalkBase",
			"Beanstalk Base",
			"The thick base of a giant beanstalk with roots.",
			pcs(
				cyl(sx, 0, sz, 9, 30, stalk, M.Grass),
				around(sx, sz, 6, 5, function(px, pz)
					return ball(px, 0, pz, 7, stalk, M.Grass)
				end),
				ball(sx, 0, sz, 12, dirt, M.Ground)
			)
		),
		def("StalkMiddle", "Beanstalk Middle", "The beanstalk climbs higher.", { cyl(sx, 30, sz, 7, 30, stalk, M.Grass), ball(sx, 29, sz, 8, leaf, M.Grass) }),
		def(
			"StalkTop",
			"Beanstalk Top",
			"The thin top of the beanstalk, ending in a bud.",
			{ cyl(sx, 60, sz, 5, 35, stalk, M.Grass), ball(sx, 59, sz, 6, leaf, M.Grass), ball(sx, 93, sz, 7, leaf, M.Grass) }
		),
		def("LowLeaves", "Low Leaves", "Four big leaves like steps around the lower stalk.", leaves(8, 6, 10)),
		def("MidLeaves", "Middle Leaves", "Four more leaves around the middle.", leaves(36, 6, 9)),
		def("HighLeaves", "High Leaves", "Four leaves near the top.", leaves(62, 7, 8)),
		def(
			"GooseNest",
			"Golden Nest",
			"A twig nest with golden eggs at the very top.",
			pcs(
				around(sx, sz, 5, 8, function(px, pz, deg)
					return blk(px, 95, pz, 4, 1.6, 1.2, wood, M.Wood, -deg + 90)
				end),
				ball(sx - 1.4, 96, sz - 1, 3, gold, M.Neon),
				ball(sx + 1.8, 96, sz, 3, gold, M.Neon),
				ball(sx, 96, sz + 1.8, 3, gold, M.Neon)
			)
		),
		def(
			"GoldenGoose",
			"Golden Goose",
			"The goose that lays the golden eggs sits in the nest.",
			{
				ball(sx, 98, sz, 5, gold, M.Metal),
				blk(sx - 2, 100, sz, 1.4, 3.4, 1.4, gold, M.Metal),
				ball(sx - 2, 103, sz, 2.2, gold, M.Metal),
				blk(sx - 3.6, 103, sz, 1.6, 0.6, 1, rgb(255, 130, 40), M.SmoothPlastic),
				wedge(sx + 2.4, 99, sz, 3, 2.4, 2, gold, M.Metal),
				ball(sx - 2.8, 104, sz - 0.8, 0.5, rgb(20, 20, 24), M.SmoothPlastic),
				ball(sx - 2.8, 104, sz + 0.8, 0.5, rgb(20, 20, 24), M.SmoothPlastic),
			}
		),
		def(
			"GiantMushrooms",
			"Giant Mushrooms",
			"Red mushrooms with white spots, tall as trees.",
			line(3, -34, -34, -76, -76, function(px, pz, i)
				return {
					cyl(px, 0, pz, 5, 8 + i * 2, rgb(240, 230, 210), M.SmoothPlastic),
					ball(px, 5 + i * 2, pz, 14, rgb(220, 50, 50), M.SmoothPlastic),
					ball(px + 3, 15 + i * 2, pz - 2, 3, white, M.SmoothPlastic),
					ball(px - 4, 14 + i * 2, pz + 3, 3, white, M.SmoothPlastic),
				}
			end)
		),
		def(
			"GiantFlowers",
			"Giant Flowers",
			"Two huge flowers swaying in the breeze.",
			pcs(bigFlower(-40, 76, rgb(255, 120, 170)), bigFlower(-70, 62, rgb(255, 230, 90)))
		),
		def(
			"GiantBoulders",
			"Giant Boulders",
			"Mossy boulders scattered around.",
			pcs(rocks(24, 76, 3.4, stone), rocks(80, 6, 3, stone), rocks(-84, 10, 3.2, stone), rocks(30, -84, 3, stone))
		),
		def(
			"GiantStump",
			"Tree Stump and Axe",
			"A giant tree stump with an axe stuck in it.",
			{
				cyl(30, 0, 70, 22, 10, wood, M.Wood),
				cyl(30, 10, 70, 18, 0.4, rgb(190, 150, 100), M.Wood),
				blk(30, 10, 70, 1.6, 16, 1.6, wood, M.Wood, 30),
				blk(26, 20, 66, 8, 5, 1.2, rgb(150, 155, 165), M.Metal, 30),
				blk(26, 24, 66, 4, 0.6, 1.4, rgb(190, 195, 205), M.Metal, 30),
			}
		),
		def(
			"GiantBone",
			"Giant Bone",
			"A giant dog bone left on the meadow.",
			{
				lcyl(-60, 1.6, -50, 24, 3.2, "x", white, M.SmoothPlastic),
				ball(-72, 0, -48.4, 6, white, M.SmoothPlastic),
				ball(-72, 0, -51.6, 6, white, M.SmoothPlastic),
				ball(-48, 0, -48.4, 6, white, M.SmoothPlastic),
				ball(-48, 0, -51.6, 6, white, M.SmoothPlastic),
			}
		),
		def(
			"GiantBowl",
			"Giant Food Bowl",
			"A red bowl full of kibble.",
			pcs(
				cyl(34, 0, -76, 24, 3, rgb(210, 50, 60), M.SmoothPlastic),
				cyl(34, 3, -76, 20, 1, rgb(210, 50, 60), M.SmoothPlastic),
				line(7, 30, -78, 38, -74, function(px, pz, i)
					return ball(px, 4 + i % 2, pz, 3.2, rgb(150, 100, 60), M.Slate)
				end)
			)
		),
		def(
			"GiantStick",
			"Giant Stick",
			"A very large stick, perfect for fetching.",
			{
				lcyl(70, 0, 80, 30, 3, "x", wood, M.Wood),
				blk(66, 2, 80, 1.2, 1.2, 8, wood, M.Wood, 20),
				blk(76, 2, 80, 1, 1, 6, wood, M.Wood, -30),
				ball(55, 0, 80, 3, wood, M.Wood),
			}
		),
		def(
			"LogFence",
			"Log Fence",
			"A fence of giant logs beside the path.",
			line(14, 9.5, -80, 9.5, 52, function(px, pz, i)
				return cyl(px, 0, pz, 3, 8 + i % 3, wood, M.Wood)
			end)
		),
		def(
			"CloudPuffs",
			"Cloud Puffs",
			"White clouds drift around the top of the beanstalk.",
			{
				ball(sx - 20, 90, sz - 14, 18, white, M.Neon),
				ball(sx + 18, 96, sz + 10, 22, rgb(240, 245, 255), M.Neon),
				ball(sx - 6, 88, sz + 20, 16, white, M.Neon),
				ball(sx + 6, 102, sz - 18, 20, rgb(240, 245, 255), M.Neon),
				ball(sx - 30, 100, sz + 4, 14, white, M.Neon),
				ball(sx + 20, 90, sz - 14, 14, white, M.Neon),
			}
		),
		def(
			"HangingVines",
			"Hanging Vines",
			"Green vines hang from the leaves.",
			around(sx, sz, 12, 8, function(px, pz, _deg, i)
				return cyl(px, 20 + (i % 3) * 8, pz, 1, 10 + (i % 2) * 6, stalk, M.Grass)
			end)
		),
		def(
			"MagicBeans",
			"Magic Beans",
			"Glowing beans scattered at the foot of the stalk.",
			line(8, 40, 30, 80, 70, function(px, pz, i)
				return raw(px, 1.2, pz, 3, 2.4, 2, if i % 2 == 0 then rgb(120, 255, 140) else gold, M.Neon, BALL, Vector3.new(0, i * 40, 0))
			end)
		),
		def(
			"FairyLights",
			"Fairy Lights",
			"Little yellow lights float among the leaves and clouds.",
			line(14, 30, 20, 90, 80, function(px, pz, i)
				return ball(px, 6 + (i * 9) % 70, pz, 1.6, rgb(255, 240, 140), M.Neon)
			end)
		),
		def(
			"GiantFootprints",
			"Giant Footprints",
			"Huge dirt footprints lead to the stalk.",
			line(8, 16, -16, 54, 34, function(px, pz, i)
				return mark(px, pz + (i % 2) * 5 - 2.5, 7, 12, dirt, M.Ground, 15)
			end)
		),
		def(
			"GiantBirdhouse",
			"Giant Birdhouse",
			"A big birdhouse on a tall pole.",
			{
				cyl(-84, 0, -20, 3, 22, wood, M.Wood),
				blk(-84, 22, -20, 12, 10, 12, rgb(220, 90, 70), M.Wood),
				wedge(-84, 32, -20, 14, 6, 14, rgb(140, 60, 50), M.Wood),
				cyl(-77.6, 24, -20, 4, 0.6, rgb(30, 24, 20), M.SmoothPlastic),
				blk(-77.6, 21, -20, 0.6, 1, 6, wood, M.Wood),
			}
		),
		def(
			"CloudCastle",
			"Cloud Castle",
			"A golden castle floats on a cloud island above the beanstalk.",
			pcs(
				island(sx, 114, sz, 22, white, white, M.Neon),
				blk(sx, 115, sz, 20, 12, 14, rgb(250, 240, 200), M.Marble),
				cyl(sx - 11, 115, sz - 8, 5, 18, gold, M.Metal),
				cyl(sx + 11, 115, sz - 8, 5, 18, gold, M.Metal),
				cyl(sx - 11, 115, sz + 8, 5, 18, gold, M.Metal),
				cyl(sx + 11, 115, sz + 8, 5, 18, gold, M.Metal),
				blk(sx - 10.4, 127, sz, 0.8, 6, 6, rgb(120, 210, 255), M.Neon),
				ball(sx, 127, sz, 8, gold, M.Neon),
				ball(sx, 122, sz, 4, white, M.Neon)
			)
		),
	}
	return build("Beanstalk", "Beanstalk and Stone Circle", 27, 1000, defs)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Bay 28: Cheems God, Doge Altar. White and gold marble altar with a throne, bone pillars, a halo arch and holy light.

local function dogeAltar(): Theme
	local area = areaOf(28)
	local w, d = area.X / 2, area.Y / 2
	local marble, cream, gold = rgb(246, 242, 230), rgb(255, 246, 214), rgb(255, 210, 80)
	local light, red, bone = rgb(255, 236, 170), rgb(205, 45, 65), rgb(255, 250, 235)
	local ax = 58
	local top = 4.2

	local function bonePillar(pz: number): { Piece }
		return {
			cyl(ax, top, pz, 3, 20, bone, M.Marble),
			ball(ax, top + 19, pz - 1.4, 4.4, bone, M.Marble),
			ball(ax, top + 19, pz + 1.4, 4.4, bone, M.Marble),
			ball(ax, top - 1, pz - 1.4, 4.4, bone, M.Marble),
			ball(ax, top - 1, pz + 1.4, 4.4, bone, M.Marble),
		}
	end

	local function dogeStatue(px: number, pz: number): { Piece }
		return {
			blk(px, 0, pz, 4, 1.4, 5, marble, M.Marble),
			blk(px, 1.4, pz + 0.6, 3.6, 4.4, 3, gold, M.Metal),
			ball(px - 0.6, 5.6, pz, 3.4, gold, M.Metal),
			wedge(px - 0.6, 8, pz - 1.2, 0.8, 2.4, 1, gold, M.Metal),
			wedge(px - 0.6, 8, pz + 1.2, 0.8, 2.4, 1, gold, M.Metal),
			blk(px + 0.6, 1.4, pz - 2.4, 1, 3, 1, gold, M.Metal),
			ball(px - 2, 5.8, pz - 0.7, 0.5, red, M.Neon),
			ball(px - 2, 5.8, pz + 0.7, 0.5, red, M.Neon),
		}
	end

	local defs = {
		def(
			"MarbleFloor",
			"Marble Floor",
			"White marble flooring with golden lines.",
			pcs(
				floorSlabs(w, d, marble, M.Marble),
				mark(58, 0, 70, 1.2, gold, M.Neon),
				mark(58, -40, 70, 1.2, gold, M.Neon),
				mark(58, 40, 70, 1.2, gold, M.Neon),
				mark(-50, 0, 1.2, 160, gold, M.Neon),
				mark(-70, 0, 1.2, 160, gold, M.Neon),
				round(-60, 40, 24, cream, M.Marble),
				round(-60, -40, 24, cream, M.Marble)
			)
		),
		def(
			"AltarSteps",
			"Altar Steps",
			"Three wide marble steps with golden edges.",
			{
				blk(ax, 0, 0, 44, 1.4, 62, marble, M.Marble),
				blk(ax + 2, 1.4, 0, 36, 1.4, 52, cream, M.Marble),
				blk(ax + 4, 2.8, 0, 28, 1.4, 42, marble, M.Marble),
				blk(ax - 22.4, 1.4, 0, 0.6, 0.4, 62, gold, M.Neon),
				blk(ax - 16.4, 2.8, 0, 0.6, 0.4, 52, gold, M.Neon),
				blk(ax - 10.4, 4.2, 0, 0.6, 0.4, 42, gold, M.Neon),
			}
		),
		def("BonkSign", "Get Bonked Sign", "A golden board on marble posts that reads GET BONKED.", bonkSign(11, 76, -1, marble, gold, cream, M.Marble)),
		def(
			"AltarTable",
			"Altar Table",
			"A marble table with a golden cloth and candles.",
			{
				blk(ax - 8, top, 0, 6, 3, 16, marble, M.Marble),
				blk(ax - 8, top + 3, 0, 7, 0.4, 17, gold, M.Metal),
				cyl(ax - 8, top + 3.4, -6, 0.8, 3, cream, M.SmoothPlastic),
				cyl(ax - 8, top + 3.4, 6, 0.8, 3, cream, M.SmoothPlastic),
				ball(ax - 8, top + 6.4, -6, 1.2, light, M.Neon),
				ball(ax - 8, top + 6.4, 6, 1.2, light, M.Neon),
				lcyl(ax - 8, top + 3.8, 0, 6, 1, "z", bone, M.Marble),
				ball(ax - 8, top + 3.4, -3.4, 1.8, bone, M.Marble),
				ball(ax - 8, top + 3.4, 3.4, 1.8, bone, M.Marble),
			}
		),
		def(
			"DogeThrone",
			"Doge Throne",
			"A golden throne with ears on top.",
			{
				blk(ax + 8, top, 0, 10, 2, 10, gold, M.Metal),
				blk(ax + 8, top + 2, 0, 6, 3, 6, red, M.Fabric),
				blk(ax + 13, top + 2, 0, 2, 20, 10, gold, M.Metal),
				blk(ax + 8, top + 4, -4.4, 6, 3, 1.2, gold, M.Metal),
				blk(ax + 8, top + 4, 4.4, 6, 3, 1.2, gold, M.Metal),
				wedge(ax + 13, top + 22, -3, 2, 6, 3, gold, M.Metal),
				wedge(ax + 13, top + 22, 3, 2, 6, 3, gold, M.Metal),
				ball(ax + 11.6, top + 15, 0, 3, light, M.Neon),
			}
		),
		def("BonePillarsA", "Golden Bone Pillars", "Three pillars shaped like giant bones.", pcs(bonePillar(-36), bonePillar(-28), bonePillar(-20))),
		def("BonePillarsB", "More Bone Pillars", "Three more bone pillars on the other side.", pcs(bonePillar(20), bonePillar(28), bonePillar(36))),
		def(
			"HaloArch",
			"Halo Arch",
			"A glowing golden ring behind the throne.",
			aroundV(ax + 17, 30, 0, 18, 16, "x", function(px, py, pz)
				return ball(px, py, pz, 3.6, gold, M.Neon)
			end)
		),
		def(
			"RedCarpet",
			"Red Carpet",
			"A red carpet runs from the path to the altar.",
			{
				mark(23, 0, 30, 9, red, M.Fabric),
				mark(23, -4.8, 30, 0.8, gold, M.Neon),
				mark(23, 4.8, 30, 0.8, gold, M.Neon),
				mark(8.6, 0, 1.2, 9, gold, M.Neon),
			}
		),
		def(
			"GoldBraziers",
			"Gold Braziers",
			"Four golden braziers with holy fire.",
			line(4, 14, -44, 14, 44, function(px, pz)
				return {
					cyl(px, 0, pz, 2, 4, gold, M.Metal),
					cyl(px, 4, pz, 4.4, 1.4, gold, M.Metal),
					ball(px, 5.4, pz, 3.4, light, M.Neon),
				}
			end)
		),
		def("DogeStatues", "Doge Statues", "Two golden Shiba statues sit in front of the steps.", pcs(dogeStatue(20, -28), dogeStatue(20, 28))),
		def(
			"OfferingBowls",
			"Offering Bowls",
			"Bowls full of treats for the god.",
			line(4, 28, -16, 28, 16, function(px, pz)
				return {
					cyl(px, 0, pz, 4, 1.2, gold, M.Metal),
					ball(px, 1.2, pz, 2.6, rgb(190, 130, 70), M.Slate),
					ball(px + 0.8, 2.6, pz + 0.6, 1.6, rgb(230, 160, 90), M.Slate),
				}
			end)
		),
		def(
			"MarbleBenches",
			"Marble Benches",
			"White marble benches with golden backs.",
			line(4, 16, -38, 16, 38, function(px, pz)
				return { blk(px, 0, pz, 3, 1.4, 7, marble, M.Marble), blk(px + 1.2, 1.4, pz, 0.6, 2, 7, gold, M.Metal) }
			end)
		),
		def(
			"GoldFountain",
			"Golden Fountain",
			"A fountain flowing with golden light.",
			pcs(
				cyl(-60, 0, 0, 16, 1.5, marble, M.Marble),
				cyl(-60, 1.5, 0, 13, 0.4, light, M.Neon),
				cyl(-60, 1.5, 0, 3, 8, gold, M.Metal),
				cyl(-60, 9.5, 0, 8, 1, gold, M.Metal),
				ball(-60, 10.5, 0, 4, light, M.Neon),
				around(-60, 0, 5, 6, function(px, pz)
					return ball(px, 8, pz, 1.6, light, M.Neon)
				end)
			)
		),
		def(
			"PrayerCandles",
			"Prayer Candles",
			"A field of tiny candles on the steps.",
			line(16, 40, -30, 40, 30, function(px, pz, i)
				return ball(px, 0.4, pz + (i % 2) * 3, 1, light, M.Neon)
			end)
		),
		def(
			"HeavenClouds",
			"Heaven Clouds",
			"Low white clouds float around the altar.",
			{
				ball(30, 0, -80, 14, bone, M.Neon),
				ball(30, 0, 84, 16, bone, M.Neon),
				ball(84, 0, -70, 16, cream, M.Neon),
				ball(84, 0, 76, 14, cream, M.Neon),
				ball(-70, 0, -90, 16, bone, M.Neon),
				ball(-80, 0, 80, 16, bone, M.Neon),
			}
		),
		def(
			"CreamBanners",
			"Cream Banners",
			"Cream and gold banners on tall poles.",
			line(4, 9.5, -62, 9.5, 62, function(px, pz, i)
				return {
					cyl(px, 0, pz, 0.8, 16, gold, M.Metal),
					blk(px, 6, pz + 2, 0.4, 9, 4, if i % 2 == 0 then cream else red, M.Fabric),
					ball(px, 16, pz, 1.6, gold, M.Neon),
				}
			end)
		),
		def(
			"GoldenTrees",
			"Golden Trees",
			"Trees with golden trunks and cream leaves.",
			line(5, -34, -30, -80, 80, function(px, pz)
				return tree(px, pz, 1.5, gold, cream, M.SmoothPlastic)
			end)
		),
		def(
			"BoneGate",
			"Bone Gate",
			"A gate made of bones behind the Shiba.",
			pcs(
				cyl(-40, 0, -12, 3, 20, bone, M.Marble),
				cyl(-40, 0, 12, 3, 20, bone, M.Marble),
				lcyl(-40, 20, 0, 28, 3, "z", bone, M.Marble),
				ball(-40, 19, -13.4, 4.4, bone, M.Marble),
				ball(-40, 19, -10.6, 4.4, bone, M.Marble),
				ball(-40, 19, 10.6, 4.4, bone, M.Marble),
				ball(-40, 19, 13.4, 4.4, bone, M.Marble),
				ball(-40, 24, 0, 4, light, M.Neon)
			)
		),
		def(
			"FloatingBone",
			"Floating Golden Bone",
			"A giant golden bone hovers above the stage.",
			{
				lcyl(0, 40, -50, 30, 4, "z", gold, M.Metal),
				ball(0, 38, -66, 6, gold, M.Metal),
				ball(0, 42, -66, 6, gold, M.Metal),
				ball(0, 38, -34, 6, gold, M.Metal),
				ball(0, 42, -34, 6, gold, M.Metal),
				ball(0, 46, -50, 2, light, M.Neon),
			}
		),
		def(
			"TreatPiles",
			"Treat Piles",
			"Heaps of golden dog treats.",
			pcs(
				line(3, -34, -40, -74, -66, function(px, pz, i)
					return {
						ball(px, 0, pz, 8, gold, M.Metal),
						ball(px + 3, 0, pz + 2, 5, gold, M.Metal),
						ball(px - 2, 6 + i % 2, pz, 3, rgb(190, 130, 70), M.Slate),
					}
				end)
			)
		),
		def(
			"DogeCoin",
			"Giant Doge Coin",
			"A giant golden coin standing behind the Shiba.",
			{
				blk(-70, 0, 20, 6, 3, 14, marble, M.Marble),
				lcyl(-70, 3, 20, 2, 22, "x", gold, M.Metal),
				lcyl(-68.9, 6, 20, 0.4, 16, "x", light, M.Neon),
				ball(-69, 11, 20, 4, gold, M.Neon),
			}
		),
		def(
			"Sparkles",
			"Golden Sparkles",
			"Golden sparks float up from the altar.",
			line(16, 30, -50, 84, 50, function(px, pz, i)
				return ball(px, 8 + (i * 7) % 40, pz + (i * 3) % 18 - 9, 1 + i % 3 * 0.6, light, M.Neon)
			end)
		),
		def(
			"SunRays",
			"Sun Rays",
			"Golden rays spread out behind the halo.",
			aroundV(ax + 20, 30, 0, 26, 16, "x", function(px, py, pz)
				return blk(px, py - 4, pz, 1.2, 8, 1.2, gold, M.Neon)
			end)
		),
		def(
			"DogePodium",
			"Statue Podium",
			"A golden Shiba statue on a marble podium with glowing gems.",
			pcs(
				blk(34, 0, -66, 10, 1.4, 22, marble, M.Marble),
				dogeStatue(34, -66),
				ball(34, 1.4, -74, 1.8, red, M.Neon),
				ball(34, 1.4, -58, 1.8, light, M.Neon)
			)
		),
		def(
			"SunDisc",
			"Sun Disc",
			"A glowing sun disc stands behind the altar.",
			{
				lcyl(90, 6, 0, 2, 40, "x", gold, M.Metal),
				lcyl(88.8, 10, 0, 0.6, 32, "x", light, M.Neon),
				blk(90, 0, 0, 6, 6, 10, marble, M.Marble),
				ball(88, 24, 0, 8, cream, M.Neon),
			}
		),
		def(
			"GoldenCrown",
			"Golden Crown",
			"A floating golden crown above the throne.",
			pcs(
				around(ax + 8, 0, 6, 8, function(px, pz)
					return wedge(px, 46, pz, 2, 6, 2, gold, M.Metal)
				end),
				cyl(ax + 8, 44, 0, 13, 2, gold, M.Metal),
				ball(ax + 8, 50, 0, 3, red, M.Neon),
				ball(ax + 8, 53, 0, 2, light, M.Neon)
			)
		),
		def(
			"GoldenAura",
			"Golden Aura",
			"Rings of light circle around the throne.",
			pcs(
				around(ax + 8, 0, 8, 5, function(px, pz)
					return ball(px, 12, pz, 2.4, light, M.Neon)
				end),
				around(ax + 8, 0, 11, 5, function(px, pz)
					return ball(px, 22, pz, 2.4, gold, M.Neon)
				end),
				around(ax + 8, 0, 14, 5, function(px, pz)
					return ball(px, 32, pz, 2.4, light, M.Neon)
				end)
			)
		),
		def(
			"LightColumns",
			"Great Light Columns",
			"Two tall columns of light left and right of the altar.",
			{
				cyl(ax, top, -46, 6, 70, light, M.Neon),
				cyl(ax, top, 46, 6, 70, light, M.Neon),
				ball(ax, top + 70, -46, 9, gold, M.Neon),
				ball(ax, top + 70, 46, 9, gold, M.Neon),
				cyl(ax, top, -46, 10, 1, gold, M.Metal),
				cyl(ax, top, 46, 10, 1, gold, M.Metal),
			}
		),
		def(
			"HolyLight",
			"Holy Light",
			"A huge column of warm light falls from the sky onto the throne.",
			pcs(
				cyl(ax + 8, top, 0, 16, 60, light, M.Neon),
				cyl(ax + 8, top + 60, 0, 26, 40, cream, M.Neon),
				cyl(ax + 8, top + 100, 0, 38, 30, light, M.Neon),
				ball(ax + 8, top + 130, 0, 44, cream, M.Neon),
				around(ax + 8, 0, 14, 8, function(px, pz)
					return ball(px, top + 10, pz, 3, gold, M.Neon)
				end)
			)
		),
	}
	return build("DogeAltar", "Doge Altar", 28, 1100, defs)
end

-- @@THEMES@@

return {
	[21] = volcano(),
	[22] = dragonLair(),
	[23] = mechaHangar(),
	[24] = observatory(),
	[25] = cloudTemple(),
	[26] = hellGate(),
	[27] = beanstalk(),
	[28] = dogeAltar(),
} :: { [number]: DecorTypes.Theme }
