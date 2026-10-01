--!strict
-- Shiba themes for bays 1 to 10 (see Config/DecorTypes for the schema and the stage frame). Keyed by the bay number.
-- Pure data: every theme is built from primitives by the small pure helpers below (nothing here creates Instances).
-- Part counts: bays 1 to 3 have 10 parts, bays 4 to 8 have 15, bays 9 and 10 have 20. Parts 1 and 2 are the foundation
-- (flooring and walls or shell), then comes the Get Bonked sign, then the props and the showpiece last.
-- Layout rule used everywhere: the path |X| < 7 stays free, the circles of radius 8 around the Shiba (-16, 0) and the Intern
-- (-10, 0) stay free (only flat flooring inside), so props stand on the right side (X > 8), on the far left (X < -25) or in
-- the left bands with |Z| > 9.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local V = Vector3.new
local C = Color3.fromRGB
local Mat = Enum.Material

---------------------------------------------------------------------------------------------------------------------
-- Piece helpers. (x, z) is the centre on the ground plane and y the BOTTOM of the piece, so stacking is easy.
---------------------------------------------------------------------------------------------------------------------

-- A block.
local function B(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?,
	rotY: number?
): Piece
	return {
		Size = V(sx, sy, sz),
		Offset = V(x, y + sy / 2, z),
		Color = color,
		Material = material,
		Rotation = if rotY then V(0, rotY, 0) else nil,
	}
end

-- A standing cylinder (axis up).
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, material: Enum.Material?): Piece
	return {
		Size = V(h, d, d),
		Offset = V(x, y + h / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = V(0, 0, 90),
	}
end

-- A lying cylinder or flat disc: its axis runs along X (or along Z when alongZ is true).
local function Pipe(
	x: number,
	y: number,
	z: number,
	d: number,
	len: number,
	color: Color3,
	material: Enum.Material?,
	alongZ: boolean?
): Piece
	return {
		Size = V(len, d, d),
		Offset = V(x, y + d / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = if alongZ then V(0, 90, 0) else nil,
	}
end

-- An ellipsoid (a sphere when the three sizes are equal).
local function El(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?
): Piece
	return {
		Size = V(sx, sy, sz),
		Offset = V(x, y + sy / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Ball,
	}
end

local function Ba(x: number, y: number, z: number, d: number, color: Color3, material: Enum.Material?): Piece
	return El(x, y, z, d, d, d, color, material)
end

-- A wedge ramp (the slope direction depends on rotY; used for roofs and bows).
local function Wg(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?,
	rotY: number?
): Piece
	return {
		Size = V(sx, sy, sz),
		Offset = V(x, y + sy / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Wedge,
		Rotation = if rotY then V(0, rotY, 0) else nil,
	}
end

-- A block tilted around any axis: here (x, y, z) is the CENTRE of the piece and the rotation is in degrees.
local function Bt(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material?,
	rx: number,
	ry: number,
	rz: number
): Piece
	return {
		Size = V(sx, sy, sz),
		Offset = V(x, y, z),
		Color = color,
		Material = material,
		Rotation = V(rx, ry, rz),
	}
end

-- Copies the pieces moved by (dx, dy, dz).
local function move(pieces: Pieces, dx: number, dy: number, dz: number): Pieces
	local out: Pieces = {}
	for _, piece in pieces do
		local copy = table.clone(piece)
		copy.Offset = piece.Offset + V(dx, dy, dz)
		table.insert(out, copy)
	end
	return out
end

local function merge(...: Pieces): Pieces
	local out: Pieces = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

-- Repeats make(x, z, i) n times, stepping (dx, dz) from (x0, z0).
local function line(
	n: number,
	x0: number,
	z0: number,
	dx: number,
	dz: number,
	make: (number, number, number) -> Pieces
): Pieces
	local out: Pieces = {}
	for i = 1, n do
		for _, piece in make(x0 + (i - 1) * dx, z0 + (i - 1) * dz, i) do
			table.insert(out, piece)
		end
	end
	return out
end

---------------------------------------------------------------------------------------------------------------------
-- Structure helpers.
---------------------------------------------------------------------------------------------------------------------

local WOOD = C(130, 90, 55)
local DARK_WOOD = C(90, 60, 38)
local WHITE = C(240, 240, 240)
local BLACK = C(30, 30, 34)
local GREEN = C(70, 150, 60)

-- Walls of a rectangular building centred on (cx, cz): back (-Z), left (-X), right (+X) and, when front is true, +Z.
local function walls(
	cx: number,
	cz: number,
	w: number,
	d: number,
	h: number,
	t: number,
	color: Color3,
	material: Enum.Material?,
	front: boolean?
): Pieces
	local out: Pieces = {
		B(cx, 0, cz - d / 2 + t / 2, w, h, t, color, material),
		B(cx - w / 2 + t / 2, 0, cz, t, h, d - 2 * t, color, material),
		B(cx + w / 2 - t / 2, 0, cz, t, h, d - 2 * t, color, material),
	}
	if front then
		table.insert(out, B(cx, 0, cz + d / 2 - t / 2, w, h, t, color, material))
	end
	return out
end

-- Four corner posts of a building.
local function corners(
	cx: number,
	cz: number,
	w: number,
	d: number,
	h: number,
	dia: number,
	color: Color3,
	material: Enum.Material?
): Pieces
	return {
		Cy(cx - w / 2, 0, cz - d / 2, dia, h, color, material),
		Cy(cx + w / 2, 0, cz - d / 2, dia, h, color, material),
		Cy(cx - w / 2, 0, cz + d / 2, dia, h, color, material),
		Cy(cx + w / 2, 0, cz + d / 2, dia, h, color, material),
	}
end

-- A sign board for the "Get Bonked" sign that faces the path (-X): board, two posts, three white letter bars and two accents.
local function bonkSign(x: number, z: number, board: Color3, accent: Color3, postColor: Color3, width: number?): Pieces
	local w = width or 9
	return {
		B(x, 3.6, z, 0.6, 3.4, w, board, Mat.Wood),
		Cy(x, 0, z - w / 2 + 0.8, 0.6, 3.6, postColor, Mat.Wood),
		Cy(x, 0, z + w / 2 - 0.8, 0.6, 3.6, postColor, Mat.Wood),
		B(x - 0.35, 5.6, z, 0.2, 0.7, w * 0.78, WHITE, Mat.SmoothPlastic),
		B(x - 0.35, 4.7, z, 0.2, 0.6, w * 0.55, WHITE, Mat.SmoothPlastic),
		B(x - 0.35, 3.9, z, 0.2, 0.4, w * 0.35, accent, Mat.Neon),
	}
end

local function lamp(x: number, z: number, h: number, glow: Color3?): Pieces
	return { Cy(x, 0, z, 0.4, h, C(50, 50, 55), Mat.Metal), Ba(x, h, z, 1.2, glow or C(255, 230, 150), Mat.Neon) }
end

local function tree(x: number, z: number, h: number): Pieces
	return {
		Cy(x, 0, z, 0.9, h * 0.5, C(110, 75, 45), Mat.Wood),
		El(x, h * 0.35, z, h * 0.8, h * 0.55, h * 0.8, GREEN, Mat.Grass),
		Ba(x + 0.3, h * 0.65, z, h * 0.45, C(90, 170, 70), Mat.Grass),
	}
end

local function pine(x: number, z: number, h: number): Pieces
	local dark = C(40, 110, 60)
	return {
		Cy(x, 0, z, 0.8, h * 0.4, C(100, 70, 45), Mat.Wood),
		El(x, h * 0.2, z, h * 0.55, h * 0.35, h * 0.55, dark, Mat.Grass),
		El(x, h * 0.45, z, h * 0.42, h * 0.3, h * 0.42, dark, Mat.Grass),
		El(x, h * 0.68, z, h * 0.28, h * 0.32, h * 0.28, dark, Mat.Grass),
	}
end

local function palm(x: number, z: number, h: number): Pieces
	local leaf = C(60, 160, 70)
	return {
		Cy(x, 0, z, 0.8, h, C(150, 110, 70), Mat.Wood),
		B(x, h, z, 7, 0.3, 1.4, leaf, Mat.Grass, 0),
		B(x, h, z, 7, 0.3, 1.4, leaf, Mat.Grass, 90),
		B(x, h + 0.2, z, 7, 0.3, 1.4, leaf, Mat.Grass, 45),
		B(x, h + 0.2, z, 7, 0.3, 1.4, leaf, Mat.Grass, 135),
		Ba(x, h - 0.8, z, 1, C(110, 75, 40), Mat.Wood),
	}
end

local function bush(x: number, z: number, s: number): Pieces
	return { El(x, 0, z, s * 1.4, s, s * 1.2, C(60, 140, 55), Mat.Grass) }
end

-- A fence along X from x0 to x1 at depth z: n posts and two rails.
local function fenceX(
	x0: number,
	x1: number,
	z: number,
	n: number,
	h: number,
	color: Color3,
	material: Enum.Material?
): Pieces
	local step = (x1 - x0) / (n - 1)
	local out = line(n, x0, z, step, 0, function(px, pz)
		return { B(px, 0, pz, 0.4, h, 0.4, color, material) }
	end)
	table.insert(out, B((x0 + x1) / 2, h * 0.3, z, x1 - x0, 0.25, 0.2, color, material))
	table.insert(out, B((x0 + x1) / 2, h * 0.7, z, x1 - x0, 0.25, 0.2, color, material))
	return out
end

-- A person made of blocks: legs, torso, arms and head (4 pieces) plus an optional hat (5th).
local function person(x: number, z: number, shirt: Color3, pants: Color3, hat: Color3?): Pieces
	local out: Pieces = {
		B(x, 0, z, 1.1, 1.8, 0.7, pants, Mat.Fabric),
		B(x, 1.8, z, 1.4, 1.6, 0.8, shirt, Mat.Fabric),
		B(x, 2.4, z, 2.4, 0.5, 0.5, shirt, Mat.Fabric),
		Ba(x, 3.4, z, 1.1, C(240, 195, 150), Mat.SmoothPlastic),
	}
	if hat then
		table.insert(out, B(x, 4.4, z, 1.3, 0.4, 1.3, hat, Mat.Fabric))
	end
	return out
end

local function flag(x: number, z: number, h: number, color: Color3, w: number?): Pieces
	local fw = w or 3
	return {
		Cy(x, 0, z, 0.3, h, C(200, 200, 205), Mat.Metal),
		B(x + fw / 2, h - fw * 0.65, z, fw, fw * 0.65, 0.15, color, Mat.Fabric),
	}
end

local function barrel(x: number, y: number, z: number, d: number, h: number, color: Color3?): Pieces
	return { Cy(x, y, z, d, h, color or C(120, 80, 45), Mat.Wood) }
end

local function crate(x: number, y: number, z: number, s: number, color: Color3?): Pieces
	return { B(x, y, z, s, s, s, color or C(160, 115, 65), Mat.Wood) }
end

local function chair(x: number, z: number, color: Color3): Pieces
	return {
		B(x, 1, z, 1.4, 0.3, 1.4, color, Mat.Wood),
		B(x, 1.3, z - 0.6, 1.4, 1.4, 0.25, color, Mat.Wood),
		Cy(x, 0, z, 0.4, 1, DARK_WOOD, Mat.Wood),
	}
end

local function table_(x: number, z: number, d: number, color: Color3): Pieces
	return { Cy(x, 1.5, z, d, 0.3, color, Mat.Wood), Cy(x, 0, z, 0.5, 1.5, DARK_WOOD, Mat.Wood) }
end

-- A dumbbell lying along X: bar and two plates.
local function dumbbell(x: number, y: number, z: number, plate: Color3): Pieces
	return {
		Pipe(x, y, z, 0.3, 2.4, C(180, 180, 190), Mat.Metal),
		Pipe(x - 1.1, y - 0.3, z, 0.9, 0.5, plate, Mat.Metal),
		Pipe(x + 1.1, y - 0.3, z, 0.9, 0.5, plate, Mat.Metal),
	}
end

---------------------------------------------------------------------------------------------------------------------
-- Theme builder: ids unique, prices rise from 10 seconds to lastPrice over the parts.
---------------------------------------------------------------------------------------------------------------------

type PartDef = { Id: string, Name: string, Description: string, Pieces: Pieces }

local function P(id: string, name: string, description: string, pieces: Pieces): PartDef
	return { Id = id, Name = name, Description = description, Pieces = pieces }
end

local function theme(
	key: string,
	name: string,
	w: number,
	d: number,
	lastPrice: number,
	defs: { PartDef }
): DecorTypes.Theme
	local parts: { DecorTypes.Part } = {}
	local n = #defs
	for i, def in defs do
		local price = math.floor(10 * (lastPrice / 10) ^ ((i - 1) / (n - 1)) + 0.5)
		table.insert(parts, {
			Id = def.Id,
			Name = def.Name,
			Description = def.Description,
			PriceSeconds = price,
			Pieces = def.Pieces,
		})
	end
	return { Key = key, Name = name, Area = Vector2.new(w, d), Parts = parts }
end

local themes: { [number]: DecorTypes.Theme } = {}

---------------------------------------------------------------------------------------------------------------------
-- 1. Little Garage (Shiba): a small orange and white garage with a bit of garden. 42 x 42.
---------------------------------------------------------------------------------------------------------------------
do
	local cream = C(245, 235, 215)
	local orange = C(255, 150, 40)
	local roofRed = C(190, 60, 40)
	themes[1] = theme("LittleGarage", "Little Garage", 42, 42, 150, {
		P(
			"Floor",
			"Wooden Floor and Lawn",
			"Warm plank floor on the right, a lawn on the left and a concrete driveway.",
			{
				B(14, 0, 0, 14, 0.3, 42, C(200, 150, 90), Mat.Wood),
				B(-14, 0, 0, 14, 0.3, 42, C(110, 170, 80), Mat.Grass),
				B(14, 0.3, -14, 12, 0.1, 12, C(225, 215, 195), Mat.Concrete),
			}
		),
		P("Walls", "Garage Walls", "Cream walls with a door opening toward the path.", {
			B(15, 0.3, -19.5, 10, 6, 1, cream, Mat.Brick),
			B(19.5, 0.3, -14, 1, 6, 12, cream, Mat.Brick),
			B(15, 0.3, -8.5, 10, 6, 1, cream, Mat.Brick),
			B(10.5, 0.3, -18, 1, 6, 4, cream, Mat.Brick),
			B(10.5, 0.3, -10, 1, 6, 4, cream, Mat.Brick),
			B(10.5, 4.8, -14, 1, 1.5, 4, cream, Mat.Brick),
		}),
		P(
			"Sign",
			"Get Bonked Sign",
			"An orange wooden board that reads GET BONKED.",
			bonkSign(11, 4, orange, C(255, 90, 60), WOOD)
		),
		P("Roof", "Garage Roof", "A red roof with a darker ridge.", {
			B(15, 6.3, -14, 11.5, 0.6, 13.5, roofRed, Mat.Slate),
			B(15, 6.9, -14, 11.5, 0.8, 3, C(140, 40, 30), Mat.Slate),
		}),
		P("Door", "Garage Door", "An orange roll-up door with ribs.", {
			B(10.3, 0.3, -14, 0.3, 4.2, 4, orange, Mat.Metal),
			B(10.1, 1.2, -14, 0.15, 0.2, 4, C(200, 110, 30), Mat.Metal),
			B(10.1, 2.4, -14, 0.15, 0.2, 4, C(200, 110, 30), Mat.Metal),
			B(10.1, 3.6, -14, 0.15, 0.2, 4, C(200, 110, 30), Mat.Metal),
		}),
		P(
			"Workbench",
			"Workbench",
			"A workbench with a toolbox and a stack of tyres inside the garage.",
			merge({
				B(17, 1.8, -18.5, 4, 0.4, 1.8, WOOD, Mat.Wood),
				B(15.3, 0.3, -18.5, 0.4, 1.5, 1.6, DARK_WOOD, Mat.Wood),
				B(18.7, 0.3, -18.5, 0.4, 1.5, 1.6, DARK_WOOD, Mat.Wood),
				B(18.2, 2.2, -18.5, 1.2, 0.8, 0.8, C(200, 40, 40), Mat.Metal),
				Cy(12.5, 0.3, -18.5, 2, 0.6, BLACK, Mat.Rubber),
				Cy(12.5, 0.9, -18.5, 2, 0.6, BLACK, Mat.Rubber),
			})
		),
		P(
			"Lamps",
			"Street Lamps",
			"Four warm lamps along the path.",
			merge(lamp(8.5, -18, 5), lamp(8.5, -5, 5), lamp(8.5, 11, 5), lamp(8.5, 18, 5))
		),
		P(
			"Trees",
			"Garden Trees",
			"Two shady trees and two bushes.",
			merge(tree(17.5, 3, 7), tree(17, 15, 6), bush(13, 17, 1.6), bush(10.5, 8, 1.2))
		),
		P(
			"Fence",
			"Picket Fence",
			"A white picket fence along the front.",
			fenceX(8.5, 19.5, 19.5, 9, 1.6, WHITE, Mat.Wood)
		),
		P("Doghouse", "Big Doghouse", "The showpiece: a doghouse with a bone on the roof.", {
			B(13.5, 0.3, 12, 6, 4, 5, C(215, 130, 70), Mat.Wood),
			Wg(13.5, 4.3, 12, 6, 2.5, 5, roofRed, Mat.Wood),
			B(10.45, 0.3, 12, 0.2, 2.6, 2.2, C(40, 25, 20), Mat.SmoothPlastic),
			Pipe(13.5, 6.8, 12, 0.7, 3.5, C(250, 245, 230), Mat.SmoothPlastic),
			Ba(11.7, 6.7, 11.6, 1, C(250, 245, 230), Mat.SmoothPlastic),
			Ba(11.7, 6.7, 12.4, 1, C(250, 245, 230), Mat.SmoothPlastic),
			Ba(15.3, 6.7, 11.6, 1, C(250, 245, 230), Mat.SmoothPlastic),
			Ba(15.3, 6.7, 12.4, 1, C(250, 245, 230), Mat.SmoothPlastic),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 2. Beach Bar (Shades Shiba): bamboo bar on sand with a grey-blue parasol and neon shades. 48 x 48.
---------------------------------------------------------------------------------------------------------------------
do
	local sand = C(235, 215, 160)
	local bamboo = C(200, 175, 100)
	local steel = C(110, 130, 165)
	themes[2] = theme("BeachBar", "Beach Bar", 48, 48, 180, {
		P("Floor", "Sand and Boardwalk", "Sand on both sides and a wooden boardwalk beside the path.", {
			B(15.5, 0, 0, 17, 0.3, 48, sand, Mat.Sand),
			B(-15.5, 0, 0, 17, 0.3, 48, C(240, 222, 172), Mat.Sand),
			B(11, 0.3, 0, 3, 0.15, 40, WOOD, Mat.Wood),
		}),
		P(
			"Hut",
			"Bamboo Hut Walls",
			"Three bamboo walls and four corner posts.",
			merge(walls(18, -16, 8, 12, 5, 1, bamboo, Mat.Wood), corners(18, -16, 8, 12, 6, 0.8, DARK_WOOD, Mat.Wood))
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A dark board with neon cyan letters and a pair of shades.",
			merge(bonkSign(11, 6, C(40, 50, 70), C(0, 230, 255), DARK_WOOD, 10), {
				El(10.55, 6.3, 3.6, 0.2, 1, 1.6, BLACK, Mat.Glass),
				El(10.55, 6.3, 5, 0.2, 1, 1.6, BLACK, Mat.Glass),
			})
		),
		P(
			"Counter",
			"Bar Counter",
			"A counter with a dark top and three stools.",
			merge(
				{
					B(18, 0.3, -11.5, 8, 2.4, 1.5, bamboo, Mat.Wood),
					B(18, 2.7, -11.5, 8.6, 0.3, 2, DARK_WOOD, Mat.Wood),
				},
				line(3, 15.5, -8.5, 2.5, 0, function(x, z)
					return {
						Cy(x, 0.3, z, 0.4, 1, C(80, 80, 90), Mat.Metal),
						Cy(x, 1.3, z, 1.4, 0.4, C(40, 150, 200), Mat.SmoothPlastic),
					}
				end)
			)
		),
		P("Roof", "Thatch Roof", "A thatched roof over the bar.", {
			B(18, 5.5, -16, 11, 0.6, 14, C(190, 160, 90), Mat.Wood),
			B(18, 6.1, -16, 11, 0.6, 3, C(170, 140, 75), Mat.Wood),
			B(18, 5.2, -16, 11.4, 0.3, 14.4, C(150, 120, 60), Mat.Wood),
		}),
		P(
			"Parasol",
			"Parasol and Table",
			"A grey-blue parasol over a round table with two chairs.",
			merge({
				Cy(16, 0.3, 2, 0.4, 5.5, WHITE, Mat.Metal),
				El(16, 5, 2, 8, 2.2, 8, steel, Mat.Fabric),
				Ba(16, 7, 2, 0.8, WHITE, Mat.Metal),
			}, table_(16, 2, 3, WHITE), chair(13.5, 2, steel), chair(18.5, 2, steel))
		),
		P("Palms", "Palm Trees", "Two tall palm trees.", merge(palm(19.5, 6, 7), palm(19.5, 19, 8))),
		P(
			"Tiki",
			"Tiki Torches",
			"Five torches with a glowing flame.",
			line(5, 9, -4, 0, 5, function(x, z)
				return { Cy(x, 0, z, 0.3, 3.5, DARK_WOOD, Mat.Wood), Ba(x, 3.5, z, 0.9, C(255, 140, 40), Mat.Neon) }
			end)
		),
		P(
			"Rack",
			"Sunglasses Rack",
			"A rack full of colourful sunglasses.",
			merge(
				{ B(21.5, 0.3, 6, 0.6, 5, 7, DARK_WOOD, Mat.Wood) },
				line(4, 21, 3.5, 0, 1.7, function(x, z, i)
					local c = if i % 2 == 0 then C(255, 60, 160) else C(0, 220, 255)
					return { El(x - 0.4, 3, z, 0.2, 0.9, 1.4, c, Mat.Neon) }
				end)
			)
		),
		P("Neon", "Neon Shades Arch", "The showpiece: a giant glowing pair of shades above the bar.", {
			Cy(10.5, 0.3, -23.3, 0.8, 9, C(60, 60, 70), Mat.Metal),
			Cy(23.5, 0.3, -23.3, 0.8, 9, C(60, 60, 70), Mat.Metal),
			El(14, 9.3, -23.3, 5, 2.6, 0.6, C(0, 230, 255), Mat.Neon),
			El(20, 9.3, -23.3, 5, 2.6, 0.6, C(0, 230, 255), Mat.Neon),
			B(17, 10.2, -23.3, 1.2, 0.5, 0.5, C(0, 230, 255), Mat.Neon),
			B(11.5, 10.3, -23.3, 2.4, 0.4, 0.5, C(255, 60, 160), Mat.Neon),
			B(22.5, 10.3, -23.3, 2.4, 0.4, 0.5, C(255, 60, 160), Mat.Neon),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 3. Gym (Buff Shiba): red and black rubber gym with chunky weights and gold trophies. 54 x 54.
---------------------------------------------------------------------------------------------------------------------
do
	local red = C(200, 40, 40)
	local rubber = C(40, 40, 46)
	local gold = C(255, 200, 40)
	themes[3] = theme("GymHall", "Gym", 54, 54, 220, {
		P("Floor", "Rubber Floor Mat", "Black rubber flooring with red tiles.", {
			B(16.5, 0, 0, 19, 0.3, 54, rubber, Mat.Slate),
			B(-16.5, 0, 0, 19, 0.3, 54, rubber, Mat.Slate),
			B(18, 0.3, -17, 14, 0.1, 16, red, Mat.Slate),
			B(-16.5, 0.3, -17, 14, 0.1, 10, red, Mat.Slate),
		}),
		P(
			"Walls",
			"Gym Walls",
			"Tall concrete walls, open to the front.",
			walls(19, -17, 14, 18, 8, 1, C(70, 70, 80), Mat.Concrete)
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A black board with red letters and a gold trim.",
			bonkSign(11, 4, rubber, red, DARK_WOOD, 10)
		),
		P(
			"Roof",
			"Gym Roof and Lights",
			"A flat steel roof with a red stripe and two bright lamps along the path.",
			merge({
				B(19, 8, -17, 15, 0.6, 19, C(90, 90, 100), Mat.Metal),
				B(19, 8.6, -17, 15, 0.4, 3, red, Mat.Metal),
			}, lamp(8.5, -6, 6, WHITE), lamp(8.5, 14, 6, WHITE))
		),
		P("Bench", "Bench Press", "A padded bench with a loaded barbell.", {
			B(16, 0.3, -12, 1.8, 1.2, 5, rubber, Mat.Fabric),
			B(15, 0.3, -12, 0.3, 3, 0.3, C(150, 150, 160), Mat.Metal),
			B(17, 0.3, -12, 0.3, 3, 0.3, C(150, 150, 160), Mat.Metal),
			Pipe(16, 3.2, -12, 0.3, 6, C(190, 190, 200), Mat.Metal),
			Pipe(13.2, 2.65, -12, 1.4, 0.5, rubber, Mat.Metal),
			Pipe(18.8, 2.65, -12, 1.4, 0.5, rubber, Mat.Metal),
		}),
		P(
			"Rack",
			"Dumbbell Rack",
			"A rack with three chunky dumbbells.",
			merge(
				{
					B(23, 0.3, -12, 2, 0.4, 6, C(60, 60, 70), Mat.Metal),
					B(23, 2.4, -12, 2, 0.4, 6, C(60, 60, 70), Mat.Metal),
				},
				line(3, 23, -14, 0, 2, function(x, z)
					return dumbbell(x, 0.9, z, red)
				end)
			)
		),
		P(
			"Treadmills",
			"Treadmills",
			"Two treadmills with glowing screens.",
			line(2, 14, -22, 0, 4.5, function(x, z)
				return {
					B(x, 0.3, z, 1.8, 0.6, 4, C(60, 60, 70), Mat.Metal),
					B(x, 0.9, z - 1.8, 1.8, 2.2, 0.3, rubber, Mat.Metal),
					B(x, 2.4, z - 1.6, 1.4, 0.6, 0.15, C(0, 230, 255), Mat.Neon),
				}
			end)
		),
		P(
			"Bags",
			"Punching Bags",
			"Two heavy bags hanging from a beam.",
			merge(
				{ B(22, 7, -22, 0.6, 0.6, 8, C(120, 120, 130), Mat.Metal) },
				line(2, 22, -24, 0, 4, function(x, z)
					return { Cy(x, 5, z, 0.2, 2, C(150, 150, 160), Mat.Metal), Cy(x, 1.5, z, 1.8, 3.5, red, Mat.Fabric) }
				end)
			)
		),
		P("Mats", "Training Corner", "A boxing ring on the left side with ropes.", {
			B(-17, 0.3, 17, 12, 0.6, 12, red, Mat.Fabric),
			Cy(-22.5, 0.9, 11.5, 0.5, 4, C(60, 60, 70), Mat.Metal),
			Cy(-11.5, 0.9, 11.5, 0.5, 4, C(60, 60, 70), Mat.Metal),
			Cy(-22.5, 0.9, 22.5, 0.5, 4, C(60, 60, 70), Mat.Metal),
			Cy(-11.5, 0.9, 22.5, 0.5, 4, C(60, 60, 70), Mat.Metal),
			B(-17, 3.2, 11.5, 11, 0.2, 0.2, WHITE, Mat.Fabric),
			B(-17, 3.2, 22.5, 11, 0.2, 0.2, WHITE, Mat.Fabric),
		}),
		P(
			"Trophies",
			"Trophy Shelf",
			"The showpiece: a wall of shining gold trophies.",
			merge(
				{
					B(19, 0.3, -24.8, 11, 6, 0.6, C(40, 30, 25), Mat.Wood),
					B(19, 3, -24.2, 11, 0.3, 1.4, DARK_WOOD, Mat.Wood),
				},
				line(4, 15.5, -24.2, 2.7, 0, function(x, z)
					return { Cy(x, 3.3, z, 0.9, 1.4, gold, Mat.Metal), Ba(x, 4.7, z, 1.1, gold, Mat.Metal) }
				end)
			)
		),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 4. Food Truck Plaza (Chef Shiba): white truck with a red-white awning, grill, picnic tables and a giant burger. 60 x 60.
---------------------------------------------------------------------------------------------------------------------
do
	local white = C(245, 245, 245)
	local red = C(210, 50, 45)
	local steel = C(170, 175, 185)
	local function picnic(x: number, z: number): Pieces
		return {
			B(x, 1.8, z, 3, 0.3, 5, WOOD, Mat.Wood),
			B(x - 2.2, 1, z, 0.8, 0.3, 5, WOOD, Mat.Wood),
			B(x + 2.2, 1, z, 0.8, 0.3, 5, WOOD, Mat.Wood),
			B(x - 1.2, 0.3, z, 0.4, 1.5, 4.6, DARK_WOOD, Mat.Wood),
			B(x + 1.2, 0.3, z, 0.4, 1.5, 4.6, DARK_WOOD, Mat.Wood),
		}
	end
	themes[4] = theme("FoodTruck", "Food Truck Plaza", 60, 60, 280, {
		P("Floor", "Plaza Floor", "Asphalt on the right, cobblestones on the left and a red-white tile strip.", {
			B(18.5, 0, 0, 23, 0.3, 60, C(95, 95, 100), Mat.Concrete),
			B(-18.5, 0, 0, 23, 0.3, 60, C(190, 170, 140), Mat.Cobblestone),
			B(18.5, 0.3, 12, 12, 0.1, 6, red, Mat.Concrete),
			B(18.5, 0.3, 18, 12, 0.1, 6, white, Mat.Concrete),
		}),
		P("Truck", "Truck Body", "A white food truck with a cab, bumper and four wheels.", {
			B(20, 1, -20, 7, 5, 14, white, Mat.Metal),
			B(20, 1, -11, 6.4, 3.4, 4, white, Mat.Metal),
			B(20, 2.6, -8.95, 5.4, 1.4, 0.1, C(120, 170, 220), Mat.Glass),
			B(20, 0.4, -8.6, 7, 0.6, 0.6, steel, Mat.Metal),
			Pipe(16.4, 0, -24, 2.2, 0.8, BLACK, Mat.Rubber),
			Pipe(23.6, 0, -24, 2.2, 0.8, BLACK, Mat.Rubber),
			Pipe(16.4, 0, -12, 2.2, 0.8, BLACK, Mat.Rubber),
			Pipe(23.6, 0, -12, 2.2, 0.8, BLACK, Mat.Rubber),
		}),
		P(
			"Sign",
			"Get Bonked Sign",
			"A red board with white letters and a yellow stripe.",
			bonkSign(11, 6, red, C(255, 220, 60), DARK_WOOD)
		),
		P(
			"Awning",
			"Serving Awning",
			"A red-white striped awning over the serving window.",
			merge(
				line(6, 15.4, -26.2, 0, 2.4, function(x, z, i)
					return { B(x, 4.6, z, 2.2, 0.3, 2.4, if i % 2 == 1 then red else white, Mat.Fabric) }
				end),
				{ Cy(14.4, 0, -26.5, 0.3, 4.6, steel, Mat.Metal), Cy(14.4, 0, -14, 0.3, 4.6, steel, Mat.Metal) }
			)
		),
		P("Window", "Serving Window", "A glass window with a shelf and a warm light strip.", {
			B(16.45, 2.4, -20, 0.2, 1.8, 5, C(30, 40, 60), Mat.Glass),
			B(15.7, 2.3, -20, 1.2, 0.2, 5.4, steel, Mat.Metal),
			B(16.4, 4.2, -20, 0.2, 0.3, 5, C(255, 220, 120), Mat.Neon),
		}),
		P("Grill", "Grill", "A steel grill with glowing coals and a chimney.", {
			B(12, 0.3, -25, 3, 1.6, 2, steel, Mat.Metal),
			B(12, 1.9, -25, 3.2, 0.2, 2.2, BLACK, Mat.Metal),
			B(12, 2.1, -25, 2.6, 0.1, 1.6, C(255, 90, 30), Mat.Neon),
			Cy(13.2, 2.1, -25.6, 0.5, 3, steel, Mat.Metal),
		}),
		P("Tables", "Picnic Tables", "Two wooden picnic tables.", merge(picnic(17, -4), picnic(17, 3))),
		P(
			"StringLights",
			"String Lights",
			"Two poles with a wire of warm bulbs.",
			merge(
				{
					Cy(9, 0, -7.5, 0.3, 6, DARK_WOOD, Mat.Wood),
					Cy(28, 0, -7.5, 0.3, 6, DARK_WOOD, Mat.Wood),
					B(18.5, 6, -7.5, 19, 0.1, 0.1, BLACK, Mat.Metal),
				},
				line(6, 11, -7.5, 3.2, 0, function(x, z)
					return { Ba(x, 5.2, z, 0.7, C(255, 220, 120), Mat.Neon) }
				end)
			)
		),
		P("Menu", "Menu Board", "A chalkboard menu on two legs.", {
			B(26, 1.2, 4, 0.5, 3.6, 6, C(30, 50, 40), Mat.Slate),
			B(26, 0, 1.5, 0.4, 1.2, 0.4, WOOD, Mat.Wood),
			B(26, 0, 6.5, 0.4, 1.2, 0.4, WOOD, Mat.Wood),
			B(25.65, 3.9, 4, 0.15, 0.3, 4.5, WHITE, Mat.SmoothPlastic),
			B(25.65, 3.2, 4, 0.15, 0.3, 3.5, WHITE, Mat.SmoothPlastic),
			B(25.65, 2.5, 4, 0.15, 0.3, 4, WHITE, Mat.SmoothPlastic),
		}),
		P(
			"Planters",
			"Planters",
			"Three brick planters with small trees on the left side.",
			line(3, -24, 16, 6, 0, function(x, z)
				return merge({ B(x, 0.3, z, 2.4, 0.8, 2.4, C(170, 80, 60), Mat.Brick) }, move(tree(x, z, 5), 0, 1.1, 0))
			end)
		),
		P(
			"Lamps",
			"Street Lamps",
			"Four lamps along the path.",
			merge(lamp(8.5, -24, 5), lamp(8.5, -2, 5), lamp(8.5, 14, 5), lamp(8.5, 26, 5))
		),
		P(
			"Supplies",
			"Supply Crates",
			"Stacked crates and two barrels behind the truck.",
			merge(
				crate(24.5, 0.3, -28.2, 2),
				crate(27, 0.3, -28.2, 2),
				crate(25.7, 2.3, -28.2, 2),
				barrel(28.8, 0.3, -25, 1.8, 2.5),
				barrel(28.8, 0.3, -22, 1.8, 2.5)
			)
		),
		P(
			"Queue",
			"Hungry Customers",
			"Three customers waiting at the window.",
			merge(
				person(12.5, -21.5, C(255, 120, 120), C(60, 80, 140)),
				person(12.5, -18.5, C(120, 200, 255), C(70, 70, 80)),
				person(12.5, -15.5, C(255, 220, 90), C(90, 60, 40))
			)
		),
		P("ChefHat", "Chef Hat and Open Sign", "A giant chef hat and a neon sign on the truck roof.", {
			Cy(20, 6, -20, 3.2, 2, white, Mat.Fabric),
			El(18.8, 7.6, -20, 2.4, 2, 2.4, white, Mat.Fabric),
			El(21.2, 7.6, -20, 2.4, 2, 2.4, white, Mat.Fabric),
			El(20, 8.1, -20, 3, 2.2, 3, white, Mat.Fabric),
			B(20, 6, -14, 5, 0.8, 0.4, red, Mat.Neon),
		}),
		P("Burger", "Giant Burger", "The showpiece: a giant burger statue with sesame seeds.", {
			El(24, 0.3, 14, 8, 2.4, 8, C(220, 160, 80), Mat.SmoothPlastic),
			Cy(24, 2.7, 14, 8.4, 1, C(100, 55, 35), Mat.SmoothPlastic),
			B(24, 3.7, 14, 8, 0.3, 8, C(255, 205, 50), Mat.SmoothPlastic, 45),
			Cy(24, 4, 14, 8.8, 0.4, GREEN, Mat.Grass),
			Cy(24, 4.4, 14, 8, 0.5, red, Mat.SmoothPlastic),
			El(24, 4.9, 14, 8.4, 3.6, 8.4, C(225, 165, 85), Mat.SmoothPlastic),
			El(22.5, 8.3, 13, 0.9, 0.4, 0.5, C(250, 240, 200), Mat.SmoothPlastic),
			El(24, 8.5, 15, 0.9, 0.4, 0.5, C(250, 240, 200), Mat.SmoothPlastic),
			El(25.6, 8.2, 13.5, 0.9, 0.4, 0.5, C(250, 240, 200), Mat.SmoothPlastic),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 5. DJ Stage (DJ Shiba): black stage with pink and cyan neon, speakers, truss, lasers and giant headphones. 66 x 66.
---------------------------------------------------------------------------------------------------------------------
do
	local black = C(20, 20, 26)
	local metal = C(70, 70, 80)
	local pink = C(255, 60, 200)
	local cyan = C(0, 230, 255)
	local function stack(x: number): Pieces
		return {
			B(x, 2.3, -24, 3, 2, 3, black, Mat.Metal),
			B(x, 4.3, -24, 2.6, 2, 2.6, black, Mat.Metal),
			B(x, 6.3, -24, 2.2, 1.6, 2.2, black, Mat.Metal),
			Pipe(x, 2.9, -22.45, 1.4, 0.3, cyan, Mat.Neon, true),
			Pipe(x, 4.9, -22.45, 1.4, 0.3, cyan, Mat.Neon, true),
		}
	end
	themes[5] = theme("DJStage", "DJ Stage", 66, 66, 320, {
		P(
			"Floor",
			"Dance Floor",
			"Black floor with a glowing pink and cyan dance grid.",
			merge(
				{ B(19.5, 0, 0, 25, 0.3, 66, black, Mat.Slate), B(-19.5, 0, 0, 25, 0.3, 66, C(30, 30, 40), Mat.Slate) },
				line(3, 16, 4, 4, 0, function(x, z, i)
					return line(3, x, z, 0, 4, function(tx, tz, j)
						return { B(tx, 0.3, tz, 4, 0.1, 4, if (i + j) % 2 == 0 then pink else cyan, Mat.Neon) }
					end)
				end)
			)
		),
		P("Stage", "Stage Platform", "A raised black stage with steps and a glowing pink edge.", {
			B(20, 0.3, -22, 22, 2, 14, black, Mat.Metal),
			B(20, 0.3, -13.5, 8, 1, 2, metal, Mat.Metal),
			B(20, 2.3, -14.95, 22, 0.15, 0.2, pink, Mat.Neon),
			B(20, 1.3, -12.45, 8, 0.15, 0.2, cyan, Mat.Neon),
		}),
		P("Sign", "Get Bonked Sign", "A black board with neon pink letters.", bonkSign(11, 8, black, pink, metal, 10)),
		P("Truss", "Light Truss", "Two steel poles and a beam across the stage.", {
			Cy(10.5, 2.3, -16, 0.8, 9, metal, Mat.Metal),
			Cy(29.5, 2.3, -16, 0.8, 9, metal, Mat.Metal),
			B(20, 11.3, -16, 20, 0.8, 0.8, metal, Mat.Metal),
			B(10.5, 2.3, -16, 1.6, 0.2, 1.6, black, Mat.Metal),
			B(29.5, 2.3, -16, 1.6, 0.2, 1.6, black, Mat.Metal),
		}),
		P("Speakers", "Speaker Stacks", "Two towers of speakers with glowing woofers.", merge(stack(12), stack(28))),
		P(
			"Booth",
			"DJ Booth",
			"A DJ desk with two turntables, a laptop and the DJ.",
			merge({
				B(20, 2.3, -23, 6, 1.6, 2, black, Mat.Metal),
				B(20, 2.8, -21.95, 5.6, 0.3, 0.1, pink, Mat.Neon),
				Cy(18.5, 3.9, -23, 1.4, 0.2, metal, Mat.Metal),
				Cy(21.5, 3.9, -23, 1.4, 0.2, metal, Mat.Metal),
				B(20, 3.9, -23.2, 1.2, 0.1, 0.9, C(200, 200, 210), Mat.Metal),
			}, move(person(20, -25, pink, black, cyan), 0, 2.3, 0))
		),
		P(
			"Lasers",
			"Laser Beams",
			"Five neon beams sweeping over the dance floor.",
			line(5, 14, -13.4, 3, 0, function(x, z, i)
				return { Bt(x, 6, z, 0.15, 11, 0.15, if i % 2 == 1 then pink else cyan, Mat.Neon, 28, 0, 0) }
			end)
		),
		P(
			"Spots",
			"Spot Lights",
			"Four stage spotlights hanging from the truss.",
			merge(
				line(2, 11.5, -16, 3, 0, function(x, z)
					return { B(x, 10.3, z, 1, 1, 1, black, Mat.Metal), Ba(x, 9.5, z, 0.9, pink, Mat.Neon) }
				end),
				line(2, 25.5, -16, 3, 0, function(x, z)
					return { B(x, 10.3, z, 1, 1, 1, black, Mat.Metal), Ba(x, 9.5, z, 0.9, cyan, Mat.Neon) }
				end)
			)
		),
		P(
			"Lamps",
			"Neon Lamps",
			"Four neon lamps along the path.",
			merge(lamp(8.5, -26, 5, pink), lamp(8.5, -8, 5, cyan), lamp(8.5, 16, 5, pink), lamp(8.5, 28, 5, cyan))
		),
		P(
			"Crowd",
			"Dancing Crowd",
			"Three ravers on the dance floor.",
			merge(
				person(17, 6, C(255, 90, 160), C(40, 40, 90)),
				person(22, 10, C(90, 220, 255), C(30, 30, 40)),
				person(25, 4, C(255, 230, 90), C(90, 40, 120))
			)
		),
		P("Merch", "Merch Stand", "A merch stand with a pink canopy and three shirts.", {
			B(28.5, 0.3, 8, 3, 2.2, 7, black, Mat.Metal),
			B(28.5, 6, 8, 4, 0.4, 8, pink, Mat.Fabric),
			Cy(26.7, 0, 4.5, 0.3, 6, metal, Mat.Metal),
			Cy(30.3, 0, 4.5, 0.3, 6, metal, Mat.Metal),
			Cy(26.7, 0, 11.5, 0.3, 6, metal, Mat.Metal),
			Cy(30.3, 0, 11.5, 0.3, 6, metal, Mat.Metal),
			B(28.5, 2.5, 5.8, 1.6, 0.2, 1.4, cyan, Mat.Fabric),
			B(28.5, 2.5, 8, 1.6, 0.2, 1.4, C(255, 230, 90), Mat.Fabric),
			B(28.5, 2.5, 10.2, 1.6, 0.2, 1.4, pink, Mat.Fabric),
		}),
		P(
			"VideoWall",
			"Video Wall",
			"A black wall with six colourful neon screens behind the DJ.",
			merge(
				{ B(20, 2.3, -28.4, 18, 9, 0.5, black, Mat.Metal) },
				line(3, 14, -28.1, 6, 0, function(x, z, i)
					return {
						B(x, 3, z, 5.4, 3.6, 0.2, if i % 2 == 1 then pink else cyan, Mat.Neon),
						B(x, 7, z, 5.4, 3.6, 0.2, if i % 2 == 1 then cyan else pink, Mat.Neon),
					}
				end)
			)
		),
		P(
			"Pillars",
			"Light Pillars",
			"Four tall neon pillars with glowing tops.",
			line(4, 32, -28, 0, 18, function(x, z, i)
				return {
					Cy(x, 0, z, 1.2, 12, if i % 2 == 1 then pink else cyan, Mat.Neon),
					Ba(x, 12, z, 1.6, WHITE, Mat.Neon),
				}
			end)
		),
		P("DiscoBall", "Disco Ball", "A mirrored ball hanging from the truss.", {
			Cy(20, 10.5, -16, 0.3, 0.8, metal, Mat.Metal),
			Ba(20, 5.5, -16, 5, C(210, 215, 225), Mat.Metal),
			Ba(17.6, 7.5, -16, 0.7, cyan, Mat.Neon),
			Ba(22.4, 7.5, -16, 0.7, pink, Mat.Neon),
			Ba(20, 7.5, -13.5, 0.7, pink, Mat.Neon),
			Ba(20, 7.5, -18.5, 0.7, cyan, Mat.Neon),
		}),
		P("Headphones", "Giant Neon Headphones", "The showpiece: giant glowing headphones behind the stage.", {
			Pipe(12, 4, -31.5, 8, 2.4, pink, Mat.Neon, true),
			Pipe(28, 4, -31.5, 8, 2.4, pink, Mat.Neon, true),
			Pipe(12, 5.5, -31.2, 5, 2.8, cyan, Mat.Neon, true),
			Pipe(28, 5.5, -31.2, 5, 2.8, cyan, Mat.Neon, true),
			B(12, 12, -31.5, 1.2, 4, 1.2, pink, Mat.Neon),
			B(28, 12, -31.5, 1.2, 4, 1.2, pink, Mat.Neon),
			B(20, 16, -31.5, 17, 1.2, 1.2, pink, Mat.Neon),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 6. Police Station (Police Shiba): blue and white building, patrol car, cell, helipad and a police helicopter. 72 x 72.
---------------------------------------------------------------------------------------------------------------------
do
	local blue = C(60, 100, 190)
	local roofDark = C(50, 55, 70)
	local steel = C(150, 155, 165)
	local glass = C(120, 170, 230)
	local gold = C(255, 205, 60)
	local red = C(230, 40, 40)
	themes[6] = theme("PoliceStation", "Police Station", 72, 72, 380, {
		P(
			"Floor",
			"Asphalt Yard",
			"Asphalt with yellow parking lines on the right, light concrete on the left.",
			merge(
				{
					B(21.5, 0, 0, 29, 0.3, 72, C(80, 80, 85), Mat.Concrete),
					B(-21.5, 0, 0, 29, 0.3, 72, C(150, 155, 160), Mat.Concrete),
				},
				line(4, 13, 16, 4.5, 0, function(x, z)
					return { B(x, 0.3, z, 0.3, 0.1, 8, gold, Mat.Concrete) }
				end)
			)
		),
		P(
			"Building",
			"Station Building",
			"Blue walls with a wide door opening toward the road.",
			merge(walls(23, -26, 20, 16, 9, 1.2, blue, Mat.Concrete), {
				B(15.5, 0, -18.6, 5, 9, 1.2, blue, Mat.Concrete),
				B(30.5, 0, -18.6, 5, 9, 1.2, blue, Mat.Concrete),
				B(23, 6.5, -18.6, 10, 2.5, 1.2, blue, Mat.Concrete),
			})
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A blue board with white letters and a red light strip.",
			bonkSign(11, 4, blue, red, steel)
		),
		P(
			"StationSign",
			"Station Sign",
			"A white POLICE board with blue letters and a gold star.",
			merge(
				{ B(23, 9.8, -17.9, 14, 2.6, 0.6, WHITE, Mat.SmoothPlastic) },
				line(6, 17.5, -17.5, 2.2, 0, function(x, z)
					return { B(x, 10.4, z, 1.2, 1.6, 0.2, blue, Mat.SmoothPlastic) }
				end),
				{ Ba(23, 12.6, -17.9, 1.6, gold, Mat.Metal) }
			)
		),
		P("Roof", "Flat Roof", "A dark flat roof with a parapet around it.", {
			B(23, 9, -26, 21.4, 0.6, 17.4, roofDark, Mat.Slate),
			B(23, 9.6, -34.4, 21.4, 1, 0.6, WHITE, Mat.Concrete),
			B(23, 9.6, -17.6, 21.4, 1, 0.6, WHITE, Mat.Concrete),
			B(12.5, 9.6, -26, 0.6, 1, 17.4, WHITE, Mat.Concrete),
			B(33.5, 9.6, -26, 0.6, 1, 17.4, WHITE, Mat.Concrete),
		}),
		P("Doors", "Doors and Windows", "Glass doors and four windows.", {
			B(21.5, 0.3, -18.6, 3.4, 5.8, 0.2, glass, Mat.Glass),
			B(24.5, 0.3, -18.6, 3.4, 5.8, 0.2, glass, Mat.Glass),
			B(15.5, 3, -17.95, 3, 2.5, 0.2, glass, Mat.Glass),
			B(30.5, 3, -17.95, 3, 2.5, 0.2, glass, Mat.Glass),
			B(12.9, 3, -26, 0.2, 2.5, 4, glass, Mat.Glass),
			B(33.1, 3, -26, 0.2, 2.5, 4, glass, Mat.Glass),
		}),
		P("Car", "Patrol Car", "A white patrol car with a red and blue light bar.", {
			B(15, 0.5, 8, 3.4, 1.2, 7, WHITE, Mat.Metal),
			B(15, 1.7, 7.5, 3, 1.2, 3.6, C(40, 50, 70), Mat.Glass),
			B(14.2, 2.9, 7.5, 0.8, 0.4, 0.6, red, Mat.Neon),
			B(15.8, 2.9, 7.5, 0.8, 0.4, 0.6, C(40, 90, 255), Mat.Neon),
			Pipe(13.3, 0, 5.5, 1.2, 0.5, BLACK, Mat.Rubber),
			Pipe(16.7, 0, 5.5, 1.2, 0.5, BLACK, Mat.Rubber),
			Pipe(13.3, 0, 10.5, 1.2, 0.5, BLACK, Mat.Rubber),
			Pipe(16.7, 0, 10.5, 1.2, 0.5, BLACK, Mat.Rubber),
		}),
		P(
			"Lamps",
			"Street Lamps",
			"Four blue-white lamps along the path.",
			merge(
				lamp(8.5, -30, 6, C(190, 220, 255)),
				lamp(8.5, -14, 6, C(190, 220, 255)),
				lamp(8.5, 16, 6, C(190, 220, 255)),
				lamp(8.5, 30, 6, C(190, 220, 255))
			)
		),
		P(
			"Fence",
			"Security Fence",
			"A steel fence along the front of the yard.",
			fenceX(9, 34, 33, 10, 2.2, C(60, 60, 70), Mat.Metal)
		),
		P(
			"Flags",
			"Flag Poles",
			"A blue and a white flag beside the station.",
			merge(flag(10, -22, 8, blue, 2.5), flag(10, -28, 8, WHITE, 2.5))
		),
		P(
			"Cell",
			"Holding Cell",
			"A small cell with bars on the left side.",
			merge(
				{
					B(-20, 0, 20, 9, 0.3, 9, C(110, 110, 115), Mat.Concrete),
					B(-20, 0.3, 15.65, 9, 4.9, 0.3, C(120, 120, 125), Mat.Concrete),
					B(-20, 5.2, 20, 9.4, 0.4, 9.4, roofDark, Mat.Slate),
				},
				line(6, -24, 24.35, 1.6, 0, function(x, z)
					return { Cy(x, 0.3, z, 0.3, 4.9, C(50, 50, 58), Mat.Metal) }
				end)
			)
		),
		P(
			"Cones",
			"Cones and Barricade",
			"Four traffic cones and a red barricade.",
			merge(
				line(4, 12, 26, 2.5, 0, function(x, z)
					return {
						Cy(x, 0, z, 1.2, 0.2, BLACK, Mat.Rubber),
						El(x, 0.2, z, 0.9, 1.6, 0.9, C(255, 130, 30), Mat.SmoothPlastic),
					}
				end),
				{
					B(33, 0, 26, 0.3, 1.8, 0.3, steel, Mat.Metal),
					B(33, 0, 28.4, 0.3, 1.8, 0.3, steel, Mat.Metal),
					B(33, 1, 27.2, 0.2, 0.6, 3.4, red, Mat.SmoothPlastic),
				}
			)
		),
		P("Pad", "Helipad", "A concrete helipad with a yellow H and four red lights.", {
			Cy(26, 0.3, 22, 10, 0.2, C(60, 60, 65), Mat.Concrete),
			B(24.5, 0.5, 22, 0.8, 0.1, 4, gold, Mat.SmoothPlastic),
			B(27.5, 0.5, 22, 0.8, 0.1, 4, gold, Mat.SmoothPlastic),
			B(26, 0.5, 22, 3, 0.1, 0.8, gold, Mat.SmoothPlastic),
			Ba(21.6, 0.4, 22, 0.6, red, Mat.Neon),
			Ba(30.4, 0.4, 22, 0.6, red, Mat.Neon),
			Ba(26, 0.4, 17.6, 0.6, red, Mat.Neon),
			Ba(26, 0.4, 26.4, 0.6, red, Mat.Neon),
		}),
		P("Beacon", "Siren Beacon", "A tall mast with a flashing red and blue beacon.", {
			B(9.5, 0.3, -31, 2, 1, 2, steel, Mat.Concrete),
			Cy(9.5, 1.3, -31, 0.6, 9, steel, Mat.Metal),
			Ba(8.9, 10.3, -31, 1.6, red, Mat.Neon),
			Ba(10.1, 10.3, -31, 1.6, C(40, 90, 255), Mat.Neon),
			Cy(9.5, 11.9, -31, 0.4, 0.6, steel, Mat.Metal),
		}),
		P("Heli", "Police Helicopter", "The showpiece: a blue police helicopter on the pad.", {
			Pipe(24.8, 0.5, 22, 0.3, 5, steel, Mat.Metal, true),
			Pipe(27.2, 0.5, 22, 0.3, 5, steel, Mat.Metal, true),
			B(24.8, 0.8, 22, 0.2, 0.9, 0.2, steel, Mat.Metal),
			B(27.2, 0.8, 22, 0.2, 0.9, 0.2, steel, Mat.Metal),
			El(26, 1.6, 22, 3.2, 2.6, 5, blue, Mat.Metal),
			El(26, 2.2, 20, 2.4, 1.8, 2.4, glass, Mat.Glass),
			B(26, 3, 26, 0.8, 0.8, 5.5, blue, Mat.Metal),
			B(26, 3, 28.4, 0.2, 2.2, 0.8, WHITE, Mat.Metal),
			Cy(26, 4.2, 22, 0.4, 0.8, steel, Mat.Metal),
			B(26, 5, 22, 13, 0.15, 0.8, roofDark, Mat.Metal),
			B(26, 5, 22, 13, 0.15, 0.8, roofDark, Mat.Metal, 90),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 7. Wild West Saloon (Cowboy Shiba): weathered boardwalk, saloon with false front, water tower and a sheriff star. 78 x 78.
---------------------------------------------------------------------------------------------------------------------
do
	local plank = C(150, 100, 60)
	local darkPlank = C(110, 70, 45)
	local cream = C(235, 215, 170)
	local gold = C(255, 205, 60)
	local red = C(190, 50, 40)
	local brown = C(120, 75, 40)
	local function cactus(x: number, z: number): Pieces
		local c = C(60, 140, 70)
		return {
			Cy(x, 0, z, 1.2, 4, c, Mat.Grass),
			Pipe(x + 0.9, 2, z, 0.7, 1.4, c, Mat.Grass),
			Cy(x + 1.4, 2.35, z, 0.7, 1.6, c, Mat.Grass),
			Pipe(x - 0.9, 1.4, z, 0.7, 1.4, c, Mat.Grass),
			Cy(x - 1.4, 1.75, z, 0.7, 1.4, c, Mat.Grass),
		}
	end
	themes[7] = theme("WesternSaloon", "Wild West Saloon", 78, 78, 440, {
		P("Floor", "Boardwalk and Dust", "Dusty ground on both sides and a wooden boardwalk.", {
			B(22.5, 0, 0, 31, 0.3, 78, C(205, 165, 115), Mat.Sand),
			B(12, 0.3, -14, 6, 0.2, 40, C(150, 105, 65), Mat.Wood),
			B(-22.5, 0, 0, 31, 0.3, 78, C(195, 155, 105), Mat.Sand),
		}),
		P(
			"Saloon",
			"Saloon Building",
			"Weathered plank walls with a swinging-door opening.",
			merge(walls(24, -28, 24, 18, 10, 1.2, plank, Mat.Wood), {
				B(16.5, 0, -19.6, 9, 10, 1.2, plank, Mat.Wood),
				B(31.5, 0, -19.6, 9, 10, 1.2, plank, Mat.Wood),
				B(24, 6.5, -19.6, 6, 3.5, 1.2, plank, Mat.Wood),
			})
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A rough wooden board that reads GET BONKED.",
			bonkSign(11, 4, plank, red, DARK_WOOD)
		),
		P(
			"FalseFront",
			"False Front",
			"A tall false front with a SALOON board.",
			merge(
				{
					B(24, 10, -19.6, 25, 4, 1.2, plank, Mat.Wood),
					B(24, 14, -19.6, 15, 2.4, 1.2, plank, Mat.Wood),
					B(24, 10.5, -20.3, 13, 2.2, 0.3, cream, Mat.Wood),
				},
				line(5, 20.4, -20.55, 1.8, 0, function(x, z)
					return { B(x, 11, z, 0.9, 1.2, 0.15, red, Mat.SmoothPlastic) }
				end)
			)
		),
		P("Doors", "Swinging Doors", "Two half-height swinging doors.", {
			B(22.5, 0.3, -19.6, 2.8, 3.4, 0.2, brown, Mat.Wood),
			B(25.5, 0.3, -19.6, 2.8, 3.4, 0.2, brown, Mat.Wood),
			Cy(21.1, 0.3, -19.6, 0.4, 3.4, darkPlank, Mat.Wood),
			Cy(26.9, 0.3, -19.6, 0.4, 3.4, darkPlank, Mat.Wood),
		}),
		P("Roof", "Roof and Chimney", "A plank roof with a brick chimney.", {
			B(24, 10, -28, 25.4, 0.6, 19.4, darkPlank, Mat.Wood),
			B(32, 10.6, -33, 1.6, 3, 1.6, C(130, 60, 50), Mat.Brick),
			Cy(32, 13.6, -33, 1, 0.5, C(60, 50, 50), Mat.Brick),
		}),
		P(
			"Bar",
			"Saloon Bar",
			"A long bar with bottles and a mirror.",
			merge(
				{
					B(31, 0.3, -28, 2, 2.4, 12, darkPlank, Mat.Wood),
					B(34.4, 3.5, -28, 0.8, 0.3, 12, WOOD, Mat.Wood),
					B(34.9, 4, -28, 0.2, 3, 10, C(200, 225, 235), Mat.Glass),
				},
				line(5, 31, -32, 0, 2, function(x, z, i)
					local colors =
						{ C(80, 200, 100), C(220, 150, 50), C(200, 60, 60), C(80, 150, 230), C(230, 210, 80) }
					return { Cy(x, 2.7, z, 0.4, 1, colors[i], Mat.Glass) }
				end)
			)
		),
		P(
			"Table",
			"Poker Table",
			"A round table with two chairs and a deck of cards.",
			merge(
				table_(18, -27, 3.2, WOOD),
				chair(18, -24.5, darkPlank),
				chair(18, -29.5, darkPlank),
				{ B(18, 1.8, -27, 1, 0.05, 1.4, WHITE, Mat.SmoothPlastic) }
			)
		),
		P("Horse", "Horse and Hitching Post", "A brown horse tied to a hitching post.", {
			El(12.5, 1.8, -9, 2, 2, 4.6, brown, Mat.SmoothPlastic),
			B(11.9, 0, -10.6, 0.5, 1.9, 0.5, brown, Mat.SmoothPlastic),
			B(13.1, 0, -10.6, 0.5, 1.9, 0.5, brown, Mat.SmoothPlastic),
			B(11.9, 0, -7.4, 0.5, 1.9, 0.5, brown, Mat.SmoothPlastic),
			B(13.1, 0, -7.4, 0.5, 1.9, 0.5, brown, Mat.SmoothPlastic),
			B(12.5, 3, -6.9, 0.9, 1.4, 0.9, brown, Mat.SmoothPlastic),
			B(12.5, 3.8, -6.2, 0.8, 0.8, 1.6, brown, Mat.SmoothPlastic),
			B(12.5, 2.2, -11.5, 0.3, 1.4, 0.3, darkPlank, Mat.SmoothPlastic),
			Cy(10, 0, -12, 0.4, 2.6, darkPlank, Mat.Wood),
			Cy(10, 0, -5, 0.4, 2.6, darkPlank, Mat.Wood),
			B(10, 2, -8.5, 0.3, 0.3, 7.2, darkPlank, Mat.Wood),
		}),
		P("WaterTower", "Water Tower", "A wooden barrel tank on four legs with a cone roof.", {
			Cy(29, 0, 4, 0.6, 9, darkPlank, Mat.Wood),
			Cy(33, 0, 4, 0.6, 9, darkPlank, Mat.Wood),
			Cy(29, 0, 8, 0.6, 9, darkPlank, Mat.Wood),
			Cy(33, 0, 8, 0.6, 9, darkPlank, Mat.Wood),
			B(31, 4, 4, 4, 0.3, 0.3, darkPlank, Mat.Wood),
			B(31, 4, 8, 4, 0.3, 0.3, darkPlank, Mat.Wood),
			Cy(31, 9, 6, 6, 6, brown, Mat.Wood),
			El(31, 15, 6, 6.4, 2, 6.4, darkPlank, Mat.Wood),
		}),
		P("Cacti", "Cacti", "Two prickly cacti.", merge(cactus(37, 10), cactus(36, 24))),
		P(
			"Lanterns",
			"Oil Lanterns",
			"Four oil lanterns along the boardwalk.",
			merge(
				lamp(8.5, -30, 6, C(255, 170, 70)),
				lamp(8.5, -18, 6, C(255, 170, 70)),
				lamp(8.5, 12, 6, C(255, 170, 70)),
				lamp(8.5, 26, 6, C(255, 170, 70))
			)
		),
		P(
			"Wagon",
			"Covered Wagon",
			"A covered wagon with two barrels.",
			merge({
				B(28, 1.2, 18, 4, 1.2, 7, plank, Mat.Wood),
				Pipe(25.85, 0, 16.2, 2.4, 0.3, darkPlank, Mat.Wood),
				Pipe(30.15, 0, 16.2, 2.4, 0.3, darkPlank, Mat.Wood),
				Pipe(25.85, 0, 19.8, 2.4, 0.3, darkPlank, Mat.Wood),
				Pipe(30.15, 0, 19.8, 2.4, 0.3, darkPlank, Mat.Wood),
				El(28, 2.4, 18, 3.8, 2.4, 6.6, cream, Mat.Fabric),
				B(28, 0.8, 22.5, 0.3, 0.3, 3, darkPlank, Mat.Wood),
			}, barrel(32.6, 0, 20, 1.4, 1.8), barrel(32.6, 0, 22, 1.4, 1.8))
		),
		P(
			"Sheriff",
			"Sheriff and Wanted Board",
			"A sheriff with a star and a wanted board.",
			merge(person(10.5, -15, C(200, 170, 110), brown, darkPlank), {
				Ba(10.5, 2.9, -14.55, 0.5, gold, Mat.Metal),
				B(14, 0, -15, 0.4, 1.8, 0.4, darkPlank, Mat.Wood),
				B(14, 1.6, -15, 2.4, 2.4, 0.2, WOOD, Mat.Wood),
				B(14, 2.2, -14.85, 1.4, 1.6, 0.05, cream, Mat.SmoothPlastic),
			})
		),
		P(
			"Star",
			"Golden Sheriff Star",
			"The showpiece: a giant golden sheriff star on a column.",
			merge(
				{
					Cy(30, 0.3, 30, 5, 0.7, C(150, 150, 155), Mat.Concrete),
					Cy(30, 1, 30, 2.4, 6, C(190, 150, 70), Mat.Metal),
					Ba(30, 10, 30, 2, gold, Mat.Neon),
				},
				line(5, 0, 0, 0, 0, function(_x, _z, i)
					local angle = math.rad(72 * (i - 1))
					return {
						Bt(
							30,
							11 + 2.5 * math.cos(angle),
							30 + 2.5 * math.sin(angle),
							0.9,
							5,
							1.4,
							gold,
							Mat.Metal,
							72 * (i - 1),
							0,
							0
						),
					}
				end)
			)
		),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 8. Pirate Ship (Pirate Shiba): a lake with a full pirate ship (the stern at the road, the bow pointing deep into the
-- plot), a jetty, crew mates, a treasure chest, a bonk flag, a beach camp and a skull rock. 92 x 100.
---------------------------------------------------------------------------------------------------------------------
do
	local hull = C(110, 70, 40)
	local deck = C(160, 110, 60)
	local wood = C(95, 60, 35)
	local darkWood = C(80, 50, 30)
	local cream = C(240, 230, 200)
	local red = C(170, 40, 40)
	local gold = C(255, 200, 40)
	local iron = C(30, 30, 35)
	local sand = C(235, 215, 160)
	local bone = C(235, 230, 215)
	local function cannon(side: number, z: number): Pieces
		-- side = 1 (right, +X) or -1 (left); the ship's centre line is X = 27 and the deck is at Y = 6.9.
		return {
			B(27 + side * 4.6, 6.9, z, 2, 0.8, 2, darkWood, Mat.Wood),
			Pipe(27 + side * 5.65, 7, z, 1.3, 3.5, iron, Mat.Metal),
		}
	end
	themes[8] = theme("PirateShip", "Pirate Ship", 92, 100, 520, {
		P("Floor", "Beach and Lake", "Sand on both sides, a lake in front of the beach with a sandy shore.", {
			B(26.5, 0, 0, 39, 0.3, 100, sand, Mat.Sand),
			B(-26.5, 0, 0, 39, 0.3, 100, C(230, 210, 155), Mat.Sand),
			B(27, 0.3, -29, 37.5, 0.15, 40.4, C(245, 232, 190), Mat.Sand),
			B(27, 0.3, -29, 34, 0.3, 38, C(40, 130, 200), Mat.Glass),
		}),
		P("Hull", "Ship Hull", "A dark wood hull with a stepped bow, a pointed tip, planked decks and rails.", {
			B(27, 0.5, -24, 12, 6, 20, hull, Mat.Wood),
			B(27, 0.5, -36.5, 10, 6, 5, hull, Mat.Wood),
			B(27, 0.5, -41, 7, 6, 4, hull, Mat.Wood),
			B(27, 0.5, -44.5, 4.2, 6, 4.2, hull, Mat.Wood, 45),
			B(27, 6.5, -24, 11.4, 0.4, 19.6, deck, Mat.WoodPlanks),
			B(27, 6.5, -36.5, 9.4, 0.4, 4.6, deck, Mat.WoodPlanks),
			B(27, 6.5, -41, 6.4, 0.4, 3.6, deck, Mat.WoodPlanks),
			B(21.3, 6.9, -24, 0.5, 1.2, 19.6, hull, Mat.Wood),
			B(32.7, 6.9, -24, 0.5, 1.2, 19.6, hull, Mat.Wood),
			Wg(27, 6.9, -15.5, 8, 2.4, 3, darkWood, Mat.Wood),
		}),
		P(
			"Sign",
			"Get Bonked Sign",
			"A dark wooden board with golden letters.",
			bonkSign(11, 7.5, C(70, 45, 30), gold, wood)
		),
		P("Mast", "Masts", "A main mast with two yards and a crow's nest, and a shorter foremast.", {
			Cy(27, 6.9, -27, 1.5, 15.6, wood, Mat.Wood),
			Pipe(27, 18, -27, 0.8, 10.4, wood, Mat.Wood),
			Pipe(27, 11, -27, 0.8, 12, wood, Mat.Wood),
			Cy(27, 16.4, -27, 3, 0.5, darkWood, Mat.Wood),
			Cy(27, 6.9, -39, 1.1, 12, wood, Mat.Wood),
			Pipe(27, 13, -39, 0.6, 8, wood, Mat.Wood),
		}),
		P("Sail", "Sails", "Cream sails with red stripes.", {
			B(27, 11.8, -27.3, 10, 6.2, 0.4, cream, Mat.Fabric),
			B(27, 14.3, -27, 10, 1, 0.1, red, Mat.Fabric),
			B(27, 7.5, -39.3, 7.4, 5.4, 0.4, cream, Mat.Fabric),
			B(27, 9.6, -39, 7.4, 0.8, 0.1, red, Mat.Fabric),
			B(27, 18.8, -27.3, 7, 3.6, 0.4, cream, Mat.Fabric),
		}),
		P("Flag", "Bonk Flag", "A black flag with a white skull and crossbones at the mast top.", {
			Cy(27, 22.5, -27, 0.3, 2.5, wood, Mat.Wood),
			B(28.5, 23.2, -27, 3, 1.8, 0.15, iron, Mat.Fabric),
			Ba(28.2, 24, -26.9, 0.8, WHITE, Mat.SmoothPlastic),
			B(28.2, 23.5, -26.9, 0.5, 0.4, 0.1, WHITE, Mat.SmoothPlastic),
			Bt(29.3, 24, -26.9, 1.6, 0.2, 0.1, WHITE, Mat.SmoothPlastic, 0, 0, 30),
			Bt(29.3, 24, -26.9, 1.6, 0.2, 0.1, WHITE, Mat.SmoothPlastic, 0, 0, -30),
		}),
		P(
			"Cannons",
			"Cannons",
			"Four black cannons, two on each side of the deck.",
			merge(cannon(1, -20), cannon(1, -29), cannon(-1, -20), cannon(-1, -29))
		),
		P("Wheel", "Ship's Wheel", "A wooden wheel with spokes and a brass hub at the stern.", {
			Cy(27, 6.9, -17.5, 0.5, 2.2, darkWood, Mat.Wood),
			Pipe(27, 8.1, -17.5, 3, 0.4, darkWood, Mat.Wood, true),
			Ba(27, 9.3, -17.5, 0.6, C(200, 160, 60), Mat.Metal),
			Bt(27, 9.6, -17.5, 3.4, 0.2, 0.2, darkWood, Mat.Wood, 0, 0, 0),
			Bt(27, 9.6, -17.5, 3.4, 0.2, 0.2, darkWood, Mat.Wood, 0, 0, 45),
			Bt(27, 9.6, -17.5, 3.4, 0.2, 0.2, darkWood, Mat.Wood, 0, 0, 90),
			Bt(27, 9.6, -17.5, 3.4, 0.2, 0.2, darkWood, Mat.Wood, 0, 0, 135),
		}),
		P("Chest", "Treasure Chest", "A chest with a round lid, gold bands and a glowing gold rim.", {
			B(27, 6.9, -21, 3, 1.6, 2, C(120, 75, 40), Mat.Wood),
			Pipe(27, 8.5, -21, 2, 3, C(120, 75, 40), Mat.Wood),
			B(25.8, 6.9, -21, 0.3, 1.7, 2.1, gold, Mat.Metal),
			B(28.2, 6.9, -21, 0.3, 1.7, 2.1, gold, Mat.Metal),
			B(27, 8.45, -21, 3.1, 0.1, 2.1, gold, Mat.Neon),
			Ba(27, 10.2, -21, 0.6, gold, Mat.Neon),
		}),
		P(
			"Crew",
			"Crew Mates",
			"Two pirate crew mates on the deck.",
			merge(
				move(person(29.5, -25, C(200, 50, 50), C(40, 40, 60), iron), 0, 6.9, 0),
				move(person(24.5, -31, C(240, 240, 240), C(60, 50, 40), iron), 0, 6.9, 0)
			)
		),
		P(
			"Dock",
			"Wooden Jetty",
			"A jetty from the shore to the ship.",
			merge(
				{ B(15, 0.6, -22, 12, 0.3, 3, deck, Mat.WoodPlanks) },
				line(2, 11, -23.3, 8, 0, function(x, z)
					return { Cy(x, 0.3, z, 0.5, 1.4, wood, Mat.Wood), Cy(x, 0.3, z + 2.6, 0.5, 1.4, wood, Mat.Wood) }
				end)
			)
		),
		P("Palms", "Beach Palms", "Two palm trees on the left beach.", merge(palm(-34, -14, 8), palm(-40, 18, 7))),
		P(
			"Lanterns",
			"Ship Lanterns",
			"Four warm lanterns along the shore.",
			merge(
				lamp(8.5, -40, 6, C(255, 170, 70)),
				lamp(8.5, -4, 6, C(255, 170, 70)),
				lamp(8.5, 14, 6, C(255, 170, 70)),
				lamp(8.5, 30, 6, C(255, 170, 70))
			)
		),
		P(
			"Camp",
			"Beach Camp",
			"A tent, a campfire, barrels and crates.",
			merge(
				{
					Bt(-36.9, 2.3, 8, 4.8, 0.3, 7, cream, Mat.Fabric, 0, 0, 40),
					Bt(-33.1, 2.3, 8, 4.8, 0.3, 7, cream, Mat.Fabric, 0, 0, -40),
					Cy(-35, 0.3, 14, 2.4, 0.3, C(110, 110, 115), Mat.Slate),
					Ba(-35, 0.5, 14, 1.2, C(255, 140, 40), Mat.Neon),
				},
				barrel(-42, 0.3, 3, 1.4, 1.8),
				barrel(-42, 0.3, 5.5, 1.4, 1.8),
				crate(-29.5, 0.3, 4, 1.8),
				crate(-29.5, 0.3, 6.2, 1.8)
			)
		),
		P(
			"SkullRock",
			"Skull Rock",
			"The showpiece: a giant skull-shaped rock with a mouth full of gold and crossed bones.",
			{
				El(-36, 0.3, -34, 14, 10, 12, bone, Mat.Slate),
				B(-36, 0.3, -30.2, 9, 3.2, 4, bone, Mat.Slate),
				El(-38.6, 4.5, -28.4, 3, 3.2, 1.6, iron, Mat.SmoothPlastic),
				El(-33.4, 4.5, -28.4, 3, 3.2, 1.6, iron, Mat.SmoothPlastic),
				B(-36, 3.5, -28.4, 1, 1.6, 0.8, iron, Mat.SmoothPlastic),
				B(-38, 0.3, -28.1, 0.4, 2.6, 0.3, iron, Mat.SmoothPlastic),
				B(-36, 0.3, -28.1, 0.4, 2.6, 0.3, iron, Mat.SmoothPlastic),
				B(-34, 0.3, -28.1, 0.4, 2.6, 0.3, iron, Mat.SmoothPlastic),
				Ba(-37, 0.3, -26.8, 2, gold, Mat.Metal),
				Ba(-35, 0.3, -26.8, 2, gold, Mat.Metal),
				B(-36, 0.3, -25.5, 8, 0.8, 0.8, bone, Mat.Slate, 30),
				B(-36, 0.3, -25.5, 8, 0.8, 0.8, bone, Mat.Slate, -30),
			}
		),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 9. Dojo (Ninja Shiba): a dark-wood dojo with a pagoda roof, paper screens, torii, training ground and a giant moon. 98 x 104.
---------------------------------------------------------------------------------------------------------------------
do
	local dark = C(60, 45, 40)
	local roofDark = C(45, 45, 60)
	local red = C(190, 40, 45)
	local paper = C(240, 232, 205)
	local stone = C(130, 130, 140)
	local straw = C(210, 180, 110)
	local gold = C(255, 205, 70)
	local function stoneLantern(x: number, z: number): Pieces
		return {
			Cy(x, 0, z, 1.6, 0.6, stone, Mat.Slate),
			Cy(x, 0.6, z, 0.6, 1.8, stone, Mat.Slate),
			B(x, 2.4, z, 1.2, 1, 1.2, C(255, 200, 110), Mat.Neon),
			B(x, 3.4, z, 2, 0.4, 2, roofDark, Mat.Slate),
		}
	end
	local function dummy(x: number, z: number): Pieces
		return {
			Cy(x, 0.3, z, 0.5, 4, DARK_WOOD, Mat.Wood),
			B(x, 3, z, 3, 0.4, 0.4, straw, Mat.Fabric),
			Cy(x, 1.2, z, 1.8, 2.6, straw, Mat.Fabric),
			Ba(x, 3.6, z, 1.2, straw, Mat.Fabric),
		}
	end
	local function brazier(x: number, z: number): Pieces
		return {
			Cy(x, 0, z, 0.6, 1.8, BLACK, Mat.Metal),
			Cy(x, 1.8, z, 1.6, 0.5, BLACK, Mat.Metal),
			El(x, 2.3, z, 1.2, 1.6, 1.2, C(255, 120, 30), Mat.Neon),
		}
	end
	local function banner(x: number, z: number): Pieces
		return {
			Cy(x, 0, z - 0.3, 0.4, 7, dark, Mat.Wood),
			B(x, 6.7, z, 3, 0.3, 0.3, dark, Mat.Wood),
			B(x, 2.2, z, 2.6, 4.5, 0.15, red, Mat.Fabric),
			Ba(x, 4, z + 0.1, 1.2, WHITE, Mat.Neon),
		}
	end
	local function cherry(x: number, z: number): Pieces
		return {
			Cy(x, 0, z, 1.2, 4.5, C(70, 45, 40), Mat.Wood),
			El(x, 3.5, z, 8, 4.5, 8, C(255, 150, 190), Mat.Grass),
			El(x - 2.2, 4.8, z - 1, 5, 3.2, 5, C(255, 175, 205), Mat.Grass),
			El(x + 2.2, 4.6, z + 1, 5, 3.2, 5, C(250, 140, 180), Mat.Grass),
			El(x, 6.5, z, 4.5, 2.6, 4.5, C(255, 190, 215), Mat.Grass),
		}
	end
	themes[9] = theme("NinjaDojo", "Dojo", 98, 104, 560, {
		P("Floor", "Dojo Grounds", "Dark stone grounds, a wooden dojo floor and a gravel courtyard.", {
			B(27.5, 0, 0, 41, 0.3, 104, C(60, 55, 65), Mat.Slate),
			B(-27.5, 0, 0, 41, 0.3, 104, C(70, 70, 78), Mat.Slate),
			B(29, 0.3, -30, 30, 0.2, 30, C(110, 80, 55), Mat.WoodPlanks),
			B(28, 0.3, 5, 40, 0.1, 22, C(150, 150, 150), Mat.Concrete),
		}),
		P(
			"Walls",
			"Dojo Walls",
			"Dark timber walls with red corner posts, open to the front.",
			merge(walls(29, -30, 30, 30, 8, 1.2, dark, Mat.Wood), corners(29, -30, 30, 30, 8, 1, red, Mat.Wood))
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A dark board with red letters and a gold trim.",
			bonkSign(11, 10, dark, red, DARK_WOOD, 10)
		),
		P("Roof", "Pagoda Roof", "A two-tier pagoda roof with a red band and a golden finial.", {
			B(29, 8, -30, 36, 0.8, 36, roofDark, Mat.Slate),
			B(29, 8.8, -30, 32, 0.6, 32, red, Mat.Wood),
			B(29, 9.4, -30, 26, 0.8, 26, roofDark, Mat.Slate),
			Cy(29, 10.2, -30, 0.5, 3, gold, Mat.Metal),
			Ba(29, 13.2, -30, 1, gold, Mat.Metal),
		}),
		P(
			"Shoji",
			"Paper Screens",
			"Five paper screens along the back wall.",
			merge(
				line(5, 17.5, -43.7, 5.6, 0, function(x, z)
					return { B(x, 0.5, z, 4.8, 5, 0.15, paper, Mat.Fabric) }
				end),
				{ B(29, 5.5, -43.7, 26, 0.3, 0.3, red, Mat.Wood), B(29, 0.5, -43.7, 26, 0.2, 0.3, dark, Mat.Wood) }
			)
		),
		P("Torii", "Red Gate", "A red torii gate in front of the dojo.", {
			Cy(14, 0, -8, 1.4, 9, red, Mat.Wood),
			Cy(26, 0, -8, 1.4, 9, red, Mat.Wood),
			B(20, 9.3, -8, 16, 1, 1.6, red, Mat.Wood),
			B(20, 10.8, -8, 19, 0.8, 1.8, dark, Mat.Wood),
			B(20, 7.6, -8, 14, 0.6, 0.8, red, Mat.Wood),
		}),
		P(
			"Lanterns",
			"Stone Lanterns",
			"Three glowing stone lanterns along the path.",
			merge(stoneLantern(9.5, -30), stoneLantern(9.5, -14), stoneLantern(9.5, 18))
		),
		P(
			"Dummies",
			"Training Dummies",
			"Three straw dummies on the training ground.",
			merge(dummy(-36, -18), dummy(-36, -10), dummy(-36, -2))
		),
		P("Zen", "Zen Garden", "Raked sand with three rocks.", {
			B(-36, 0.3, 16, 16, 0.1, 12, C(235, 228, 205), Mat.Sand),
			El(-38, 0.4, 15, 3, 2, 2.4, stone, Mat.Slate),
			El(-33, 0.4, 18, 2, 1.4, 1.6, stone, Mat.Slate),
			El(-35, 0.4, 13.5, 1.6, 1.1, 1.4, stone, Mat.Slate),
			B(-36, 0.4, 11.5, 14, 0.05, 0.2, C(190, 180, 160), Mat.Sand),
			B(-36, 0.4, 13, 14, 0.05, 0.2, C(190, 180, 160), Mat.Sand),
			B(-36, 0.4, 19.5, 14, 0.05, 0.2, C(190, 180, 160), Mat.Sand),
			B(-36, 0.4, 20.5, 14, 0.05, 0.2, C(190, 180, 160), Mat.Sand),
		}),
		P(
			"Bamboo",
			"Bamboo Grove",
			"Twelve tall green bamboo stalks.",
			merge(
				line(6, -44, 32, 2.4, 0, function(x, z, i)
					return { Cy(x, 0.3, z, 0.5, 8 + (i % 3), C(90, 160, 70), Mat.Grass) }
				end),
				line(6, -42.8, 35, 2.4, 0, function(x, z, i)
					return { Cy(x, 0.3, z, 0.5, 9 + (i % 3), C(70, 140, 60), Mat.Grass) }
				end)
			)
		),
		P("Cherry", "Cherry Trees", "Two cherry trees in blossom.", merge(cherry(41, 14), cherry(41, 28))),
		P(
			"Weapons",
			"Weapon Rack",
			"A rack with four katanas.",
			merge(
				{
					B(36, 0.5, -42.6, 8, 0.4, 0.6, DARK_WOOD, Mat.Wood),
					B(36, 2.4, -42.6, 8, 0.3, 0.4, DARK_WOOD, Mat.Wood),
				},
				line(4, 33, -42.6, 2, 0, function(x, z)
					return {
						B(x, 1.2, z, 0.2, 3.6, 0.15, C(200, 205, 215), Mat.Metal),
						B(x, 0.7, z, 0.3, 0.8, 0.25, BLACK, Mat.Fabric),
					}
				end)
			)
		),
		P(
			"Banners",
			"Dojo Banners",
			"Three red banners with a white moon.",
			merge(banner(20, -10.5), banner(29, -10.5), banner(38, -10.5))
		),
		P("Pond", "Koi Pond", "A stone-rimmed pond with two orange koi.", {
			B(40, 0.3, 2, 10, 0.2, 8, C(40, 90, 130), Mat.Glass),
			B(40, 0.3, -2.3, 10.8, 0.5, 0.6, stone, Mat.Slate),
			B(40, 0.3, 6.3, 10.8, 0.5, 0.6, stone, Mat.Slate),
			B(34.7, 0.3, 2, 0.6, 0.5, 8.4, stone, Mat.Slate),
			B(45.3, 0.3, 2, 0.6, 0.5, 8.4, stone, Mat.Slate),
			El(38, 0.5, 1, 1.6, 0.3, 0.8, C(255, 130, 40), Mat.SmoothPlastic),
			El(42, 0.5, 3.5, 1.6, 0.3, 0.8, C(255, 240, 230), Mat.SmoothPlastic),
		}),
		P(
			"Stones",
			"Stepping Stones",
			"Six round stones leading from the path to the gate.",
			line(6, 10, -2, 2.4, 0, function(x, z)
				return { Cy(x, 0.3, z, 1.8, 0.2, stone, Mat.Slate) }
			end)
		),
		P(
			"Ninjas",
			"Rooftop Ninjas",
			"Two black ninjas with red scarves on the roof.",
			merge(
				move(person(21, -30, BLACK, BLACK, red), 0, 10.2, 0),
				move(person(37, -30, BLACK, BLACK, red), 0, 10.2, 0)
			)
		),
		P(
			"Totem",
			"Shuriken Totem",
			"A pole with three stacked giant shuriken.",
			merge(
				{ Cy(22, 0.3, 18, 0.8, 9, DARK_WOOD, Mat.Wood) },
				line(3, 0, 0, 0, 0, function(_x, _z, i)
					local size = 7 - i * 1.4
					local y = 2.5 + i * 2.4
					return {
						B(22, y, 18, size, 0.4, size, C(180, 185, 195), Mat.Metal),
						B(22, y, 18, size, 0.4, size, C(180, 185, 195), Mat.Metal, 45),
						Ba(22, y - 0.1, 18, 0.9, red, Mat.Neon),
					}
				end)
			)
		),
		P(
			"Braziers",
			"Fire Braziers",
			"Four iron braziers with flames.",
			merge(brazier(18, -5), brazier(34, -5), brazier(18, 24), brazier(34, 24))
		),
		P(
			"PaperLanterns",
			"Paper Lanterns",
			"A string of red paper lanterns under the roof edge.",
			merge(
				{ B(29, 7, -13, 26, 0.1, 0.1, BLACK, Mat.Metal) },
				line(6, 17, -13, 4.8, 0, function(x, z)
					return { Ba(x, 5.6, z, 1.4, C(255, 70, 60), Mat.Neon) }
				end)
			)
		),
		P("Moon", "Giant Moon", "The showpiece: a huge glowing moon over the dojo with dark clouds and stars.", {
			Ba(29, 15, -44, 14, C(255, 250, 210), Mat.Neon),
			Ba(26, 24, -37.6, 2, C(235, 225, 170), Mat.Neon),
			Ba(32, 20, -37.8, 2.6, C(235, 225, 170), Mat.Neon),
			Ba(30, 27, -37.5, 1.6, C(235, 225, 170), Mat.Neon),
			El(20, 18, -36, 10, 2, 3, C(60, 70, 100), Mat.Fabric),
			El(38, 24, -36, 9, 2, 3, C(60, 70, 100), Mat.Fabric),
			Ba(14, 28, -30, 0.7, WHITE, Mat.Neon),
			Ba(44, 30, -26, 0.7, WHITE, Mat.Neon),
			Ba(10, 22, -44, 0.7, WHITE, Mat.Neon),
			Ba(47, 20, -44, 0.7, WHITE, Mat.Neon),
		}),
	})
end

---------------------------------------------------------------------------------------------------------------------
-- 10. Longhouse (Viking Shiba): a timber longhouse with a turf roof and shield wall, a longship with a dragon prow on a fjord,
-- rune stones, a forge and a giant horned helmet. 100 x 110.
---------------------------------------------------------------------------------------------------------------------
do
	local timber = C(80, 55, 40)
	local turf = C(80, 130, 60)
	local stone = C(120, 122, 118)
	local steel = C(175, 180, 190)
	local bone = C(235, 228, 205)
	local cream = C(240, 230, 200)
	local gold = C(255, 205, 70)
	local shieldColors = { C(200, 50, 45), C(240, 240, 235), C(240, 200, 60) }
	local function torch(x: number, z: number): Pieces
		return lamp(x, z, 5, C(255, 140, 50))
	end
	local function runeStone(x: number, z: number): Pieces
		return {
			B(x, 0.3, z, 1.6, 4.2, 0.8, stone, Mat.Slate),
			B(x - 0.85, 2.6, z, 0.1, 1.6, 0.3, C(0, 230, 255), Mat.Neon),
			B(x - 0.85, 1.6, z, 0.1, 0.3, 0.6, C(0, 230, 255), Mat.Neon),
		}
	end
	local function shipShield(x: number, z: number, i: number): Pieces
		return { Pipe(x, 2.4, z, 1.6, 0.2, shieldColors[(i - 1) % 3 + 1], Mat.Wood) }
	end
	themes[10] = theme("VikingLonghouse", "Longhouse", 100, 110, 600, {
		P("Floor", "Meadow and Rock", "Grass on the right, grey rock on the left and a gravel yard.", {
			B(28.5, 0, 0, 43, 0.3, 110, C(95, 125, 70), Mat.Grass),
			B(-28.5, 0, 0, 43, 0.3, 110, C(120, 125, 120), Mat.Slate),
			B(27, 0.3, -10, 24, 0.1, 16, C(150, 145, 130), Mat.Concrete),
		}),
		P(
			"Frame",
			"Longhouse Frame",
			"Dark timber walls with corner posts and a door opening to the front.",
			merge(walls(27, -34, 24, 32, 7, 1.4, timber, Mat.Wood), {
				B(19.5, 0, -18.7, 9, 7, 1.4, timber, Mat.Wood),
				B(34.5, 0, -18.7, 9, 7, 1.4, timber, Mat.Wood),
				B(27, 5.4, -18.7, 6, 1.6, 1.4, timber, Mat.Wood),
				Cy(15, 0, -18, 1.2, 8, DARK_WOOD, Mat.Wood),
				Cy(39, 0, -18, 1.2, 8, DARK_WOOD, Mat.Wood),
				Cy(15, 0, -50, 1.2, 8, DARK_WOOD, Mat.Wood),
				Cy(39, 0, -50, 1.2, 8, DARK_WOOD, Mat.Wood),
			})
		),
		P(
			"Sign",
			"Get Bonked Sign",
			"A dark timber board with red letters and a yellow stripe.",
			bonkSign(11, 8, C(70, 48, 35), shieldColors[3], timber, 10)
		),
		P("Roof", "Turf Roof", "A grass-covered roof with two slopes and a ridge beam.", {
			Bt(20.6, 9.1, -34, 13.2, 0.8, 34, turf, Mat.Grass, 0, 0, 18),
			Bt(33.4, 9.1, -34, 13.2, 0.8, 34, turf, Mat.Grass, 0, 0, -18),
			B(27, 11.3, -34, 0.8, 0.5, 34, DARK_WOOD, Mat.Wood),
		}),
		P("Door", "Carved Door", "Two heavy doors under a carved golden lintel.", {
			B(25.5, 0.3, -18.7, 2.8, 5.1, 0.3, DARK_WOOD, Mat.Wood),
			B(28.5, 0.3, -18.7, 2.8, 5.1, 0.3, DARK_WOOD, Mat.Wood),
			B(27, 5.4, -19.5, 6.4, 0.5, 0.4, gold, Mat.Metal),
			Ba(24.4, 2, -18.4, 0.5, gold, Mat.Metal),
			Ba(29.6, 2, -18.4, 0.5, gold, Mat.Metal),
		}),
		P(
			"Shields",
			"Shield Wall",
			"Six round shields in red, white and yellow on the front wall.",
			merge(
				line(3, 17, -17.8, 3, 0, function(x, z, i)
					return { Pipe(x, 2.2, z, 2.2, 0.3, shieldColors[i], Mat.Wood, true) }
				end),
				line(3, 31, -17.8, 3, 0, function(x, z, i)
					return { Pipe(x, 2.2, z, 2.2, 0.3, shieldColors[i], Mat.Wood, true) }
				end)
			)
		),
		P("FirePit", "Fire Pit", "A stone ring with logs and flames inside the hall.", {
			Cy(27, 0.3, -32, 4, 0.4, stone, Mat.Slate),
			Bt(27, 1, -32, 3, 0.4, 0.4, DARK_WOOD, Mat.Wood, 0, 30, 0),
			Bt(27, 1, -32, 3, 0.4, 0.4, DARK_WOOD, Mat.Wood, 0, -30, 0),
			El(27, 1, -32, 1.4, 2.4, 1.4, C(255, 130, 30), Mat.Neon),
			El(27.4, 1, -32.3, 0.9, 1.6, 0.9, C(255, 210, 60), Mat.Neon),
		}),
		P(
			"Table",
			"Long Table",
			"A long feast table with two benches and three golden goblets.",
			merge(
				{
					B(27, 1.8, -40, 3, 0.3, 12, WOOD, Mat.Wood),
					B(24.5, 1, -40, 1, 0.3, 12, DARK_WOOD, Mat.Wood),
					B(29.5, 1, -40, 1, 0.3, 12, DARK_WOOD, Mat.Wood),
					B(26, 0.3, -40, 0.4, 1.5, 11, DARK_WOOD, Mat.Wood),
					B(28, 0.3, -40, 0.4, 1.5, 11, DARK_WOOD, Mat.Wood),
				},
				line(3, 27, -43, 0, 3, function(x, z)
					return { Cy(x, 2.1, z, 0.5, 0.6, gold, Mat.Metal) }
				end)
			)
		),
		P(
			"Hay",
			"Barrels and Hay",
			"Three barrels and three hay bales at the back of the hall.",
			merge(barrel(35, 0.3, -47, 1.6, 2), barrel(37, 0.3, -47, 1.6, 2), barrel(36, 0.3, -45, 1.6, 2), {
				B(18, 0.3, -47, 2.4, 1.4, 1.6, C(215, 185, 90), Mat.Fabric),
				B(20.6, 0.3, -47, 2.4, 1.4, 1.6, C(215, 185, 90), Mat.Fabric),
				B(19.3, 1.7, -47, 2.4, 1.4, 1.6, C(215, 185, 90), Mat.Fabric),
			})
		),
		P("Fjord", "Fjord Water", "A fjord with grey rocks along its shore.", {
			B(-37, 0.3, -20, 20, 0.3, 66, C(35, 100, 165), Mat.Glass),
			El(-26, 0.3, -48, 3, 1.8, 3, stone, Mat.Slate),
			El(-26.2, 0.3, -36, 2.4, 1.4, 2.8, stone, Mat.Slate),
			El(-26, 0.3, -12, 3.2, 2, 2.6, stone, Mat.Slate),
			El(-26.4, 0.3, 0, 2.6, 1.6, 3, stone, Mat.Slate),
		}),
		P("ShipHull", "Longship Hull", "A long dark hull with pointed bow and stern, a deck and side rails.", {
			B(-37, 0.6, -32, 8, 3, 16, C(100, 65, 40), Mat.Wood),
			B(-37, 0.6, -21, 6, 3, 6, C(100, 65, 40), Mat.Wood),
			B(-37, 0.6, -43, 6, 3, 6, C(100, 65, 40), Mat.Wood),
			B(-37, 0.6, -47.5, 4.2, 3, 4.2, C(100, 65, 40), Mat.Wood, 45),
			B(-37, 0.6, -17, 4.2, 3, 4.2, C(100, 65, 40), Mat.Wood, 45),
			B(-37, 3.6, -32, 6, 0.3, 30, C(165, 120, 70), Mat.WoodPlanks),
			B(-40.6, 3.6, -32, 0.4, 1, 28, C(80, 52, 35), Mat.Wood),
			B(-33.4, 3.6, -32, 0.4, 1, 28, C(80, 52, 35), Mat.Wood),
			B(-37, 0.3, -32, 1, 0.4, 32, C(60, 40, 28), Mat.Wood),
		}),
		P("Prow", "Dragon Prow", "A carved dragon head on the bow and a curled tail on the stern.", {
			B(-37, 3.9, -47, 1.2, 3.5, 1.2, C(80, 52, 35), Mat.Wood),
			B(-37, 7.2, -48, 1.2, 1, 2.4, C(80, 52, 35), Mat.Wood),
			B(-37, 7.4, -50, 1.6, 1.6, 2.4, C(100, 65, 40), Mat.Wood),
			Bt(-37.7, 9.4, -49.4, 0.4, 1.8, 0.4, bone, Mat.SmoothPlastic, 0, 0, 20),
			Bt(-36.3, 9.4, -49.4, 0.4, 1.8, 0.4, bone, Mat.SmoothPlastic, 0, 0, -20),
			Ba(-37.9, 8.5, -50.6, 0.5, C(255, 60, 40), Mat.Neon),
			Ba(-36.1, 8.5, -50.6, 0.5, C(255, 60, 40), Mat.Neon),
			B(-37, 3.9, -15.5, 1, 3, 1, C(80, 52, 35), Mat.Wood),
		}),
		P("Sail", "Mast and Sail", "A tall mast with a yard and a red and white striped sail.", {
			Cy(-37, 3.9, -32, 1, 13, DARK_WOOD, Mat.Wood),
			Pipe(-37, 15, -32, 0.6, 9, DARK_WOOD, Mat.Wood),
			B(-37, 7.5, -32, 8.4, 7.4, 0.3, cream, Mat.Fabric),
			B(-40, 7.5, -31.8, 1.2, 7.4, 0.1, shieldColors[1], Mat.Fabric),
			B(-37, 7.5, -31.8, 1.2, 7.4, 0.1, shieldColors[1], Mat.Fabric),
			B(-34, 7.5, -31.8, 1.2, 7.4, 0.1, shieldColors[1], Mat.Fabric),
			B(-37, 16.9, -32, 1, 1.4, 0.1, shieldColors[1], Mat.Fabric),
		}),
		P(
			"ShipShields",
			"Ship Shields",
			"Eight round shields along both sides of the longship.",
			merge(
				line(4, -40.9, -38, 0, 4, shipShield),
				line(4, -33.1, -38, 0, 4, function(x, z, i)
					return shipShield(x, z, i + 1)
				end)
			)
		),
		P(
			"Oars",
			"Oars",
			"Six long oars sticking out of the ship.",
			merge(
				line(3, -42.5, -38, 0, 6, function(x, z)
					return { Bt(x, 2.6, z, 5, 0.25, 0.4, C(150, 105, 60), Mat.Wood, 0, 0, 20) }
				end),
				line(3, -31.5, -38, 0, 6, function(x, z)
					return { Bt(x, 2.6, z, 5, 0.25, 0.4, C(150, 105, 60), Mat.Wood, 0, 0, -20) }
				end)
			)
		),
		P(
			"Runes",
			"Rune Stones",
			"Three standing stones with glowing runes.",
			merge(runeStone(12, -14), runeStone(12, -10), runeStone(12, -6))
		),
		P(
			"Forge",
			"Forge and Anvil",
			"A stone forge with a glowing mouth, an anvil and a water barrel.",
			merge({
				B(43, 0.3, -8, 4, 3.5, 4, stone, Mat.Slate),
				B(40.9, 0.8, -8, 0.2, 1.4, 2.4, C(255, 140, 40), Mat.Neon),
				Cy(43.5, 3.8, -8.5, 1.2, 3, stone, Mat.Slate),
				Cy(38, 0.3, -8, 1.2, 1, BLACK, Mat.Metal),
				B(38, 1.3, -8, 2.2, 0.6, 0.9, BLACK, Mat.Metal),
				B(40, 0.3, -3.5, 0.5, 0.3, 0.5, C(120, 80, 45), Mat.Wood),
			}, barrel(40, 0.3, -4, 1.4, 1.8, C(90, 90, 100)))
		),
		P("Pines", "Pine Forest", "Three tall pine trees.", merge(pine(44, 24, 10), pine(38, 38, 9), pine(44, 46, 10))),
		P(
			"Torches",
			"Torch Posts",
			"Four flaming torches along the path.",
			merge(torch(8.5, -42), torch(8.5, -26), torch(8.5, 22), torch(8.5, 36))
		),
		P("Helmet", "Giant Viking Helmet", "The showpiece: a giant horned helmet on a stone plinth.", {
			Cy(30, 0.3, 28, 10, 1, stone, Mat.Slate),
			El(30, 1.3, 28, 9, 6, 9, steel, Mat.Metal),
			Cy(30, 1.3, 28, 9.8, 0.8, gold, Mat.Metal),
			B(25.8, 2.6, 28, 0.5, 3.6, 1, steel, Mat.Metal),
			Bt(30, 5.9, 33.5, 1, 4.5, 1, bone, Mat.SmoothPlastic, 35, 0, 0),
			Bt(30, 5.9, 22.5, 1, 4.5, 1, bone, Mat.SmoothPlastic, -35, 0, 0),
			Ba(30, 7.3, 28, 1.4, gold, Mat.Metal),
			B(25.55, 4.5, 26.5, 0.1, 0.5, 1.4, C(255, 120, 40), Mat.Neon),
			B(25.55, 4.5, 29.5, 0.1, 0.5, 1.4, C(255, 120, 40), Mat.Neon),
		}),
	})
end

return themes
