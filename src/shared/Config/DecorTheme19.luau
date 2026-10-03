--!strict
-- Theme of the Shiba of bay 19: Pharaoh Pyramid (Config/DecorTypes -> Theme). 190 x 130: the Pharaoh Shiba stands on a sun-gold dais in
-- the middle of the right half, a temple pylon gate behind it and the Great Sphinx and the Great Pyramid to its back right; a winding
-- sandy walkway zigzags past an oasis, a bazaar, a camel caravan and the old tomb on the left.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: braziers, gold and lamps are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local SAND = C(224, 196, 138)
local SAND_D = C(200, 166, 108)
local STONE = C(226, 202, 152)
local STONE_L = C(240, 226, 190)
local STONE_D = C(176, 148, 104)
local GOLD = C(240, 190, 56)
local LAPIS = C(38, 74, 156)
local TURQ = C(50, 160, 160)
local RED = C(190, 58, 48)
local BLACK = C(38, 36, 42)
local WATER = C(60, 152, 192)
local PALM = C(70, 140, 60)
local TRUNK = C(130, 96, 62)
local MUD = C(184, 138, 96)
local LINEN = C(238, 230, 210)
local WOOD = C(118, 80, 50)
local GRASS = C(104, 156, 74)

local OX, OZ = 0, 0 -- origin of the part being written (see P)

local Sand = Enum.Material.Sand
local Sandstone = Enum.Material.Sandstone
local Rock = Enum.Material.Rock
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Grass = Enum.Material.Grass
local Brick = Enum.Material.Brick

-- Block centred at (x, y, z), size (sx, sy, sz), optional rotation in degrees.
local function B(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material,
	rot: Vector3?
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
		Rotation = rot,
	}
end

-- Standing cylinder (axis up): diameter d, height h, centre y.
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder tilted away from vertical by `tilt` degrees (positive leans toward -X).
local function CyT(
	x: number,
	y: number,
	z: number,
	d: number,
	h: number,
	tilt: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90 + tilt),
	}
end

-- Cylinder lying along Z (a disc facing the road): diameter d, thickness len.
local function Cz(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

local function Ball(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
end

local function rot(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
end

-- Builds a list of pieces written around their own origin and moves it to the world spot (cx, cz).
local function P(cx: number, cz: number, build: () -> Pieces): Pieces
	OX, OZ = cx, cz
	local out = build()
	OX, OZ = 0, 0
	return out
end

local theme: DecorTypes.Theme = {
	Key = "PharaohPyramid",
	Name = "Pharaoh Pyramid",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(36, 4), Facing = 180 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-48, 44),
		Vector2.new(-6, 20),
		Vector2.new(-52, -8),
		Vector2.new(12, -28),
		Vector2.new(-30, -48),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(47, 4),
	AutoPad = Vector2.new(25, 4),
	Parts = {
		{
			Id = "Ground",
			Name = "Desert Sands",
			Description = "Warm golden sand with dunes, a sandstone plaza for the pyramid and a sun-stone circle for the Pharaoh.",
			Pad = Vector2.new(16, 58),
			PriceSeconds = 58,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, SAND, Sand),
				B(-62, 0.3, 40, 40, 0.2, 18, SAND_D, Sand),
				B(-8, 0.3, -2, 30, 0.2, 16, SAND_D, Sand),
				B(74, 0.3, 40, 34, 0.2, 18, SAND_D, Sand),
				B(-34, 0.3, -58, 40, 0.2, 12, SAND_D, Sand),
				B(60, 0.34, -43, 42, 0.2, 42, STONE, Sandstone),
				B(36, 0.34, 4, 24, 0.2, 24, STONE_L, Sandstone),
				B(30, 0.3, 34, 18, 0.2, 8, STONE_D, Sandstone),
				B(-78, 0.3, -32, 20, 0.2, 18, STONE_D, Sandstone),
			},
		},
		{
			Id = "Pyramid",
			Name = "Great Pyramid",
			Description = "The mighty pyramid of the pharaoh: a huge sandstone mountain with a golden tip and a dark entrance.",
			Pad = Vector2.new(44, -24),
			Yaw = 8,
			PriceSeconds = 67,
			RewardMult = 1.25,
			Pieces = P(60, -44, function()
				return {
					B(0, 1.75, 0, 34, 3.5, 34, STONE, Sandstone),
					B(0, 5.25, 0, 30, 3.5, 30, STONE, Sandstone),
					B(0, 8.75, 0, 26, 3.5, 26, STONE_L, Sandstone),
					B(0, 12.25, 0, 22, 3.5, 22, STONE, Sandstone),
					B(0, 15.75, 0, 18, 3.5, 18, STONE_L, Sandstone),
					B(0, 19.25, 0, 14, 3.5, 14, STONE, Sandstone),
					B(0, 22.75, 0, 10, 3.5, 10, STONE_L, Sandstone),
					B(0, 26.25, 0, 6, 3.5, 6, STONE, Sandstone),
					B(0, 29.2, 0, 3, 2.4, 3, GOLD, Metal),
					B(0, 2.6, 16.4, 5, 5.2, 1.2, BLACK, Rock),
				}
			end),
		},
		{
			Id = "Sphinx",
			Name = "Great Sphinx",
			Description = "A giant lion with the head of a king, guarding the pyramid with a calm stare.",
			Pad = Vector2.new(46, -14),
			Yaw = -10,
			PriceSeconds = 77,
			RewardMult = 1.3,
			Pieces = P(64, -16, function()
				return {
					B(0, 0.5, 0, 28, 1, 11, STONE_D, Sandstone),
					B(3.5, 3.5, 0, 15, 5, 6.4, SAND, Sandstone),
					B(-1, 6.2, 0, 8, 6, 5.4, SAND, Sandstone),
					B(-9.5, 2.2, -2.3, 9, 2.4, 2, SAND, Sandstone),
					B(-9.5, 2.2, 2.3, 9, 2.4, 2, SAND, Sandstone),
					B(-7.2, 9.4, 0, 5.2, 7.2, 5.2, SAND, Sandstone),
					B(-7.2, 9.4, -3.6, 4.6, 8, 2, LAPIS, Plastic),
					B(-7.2, 9.4, 3.6, 4.6, 8, 2, LAPIS, Plastic),
					B(-7.2, 13.6, 0, 6.4, 1.4, 6.6, GOLD, Metal),
					B(10.5, 4.6, 0, 5, 2.4, 3.2, SAND, Sandstone, rot(0, 0, 20)),
				}
			end),
		},
		{
			Id = "Pylon",
			Name = "Temple Pylon",
			Description = "The sun gate of the temple: two sloping towers with flagpoles, a golden sun disc and a doorway.",
			Pad = Vector2.new(74, 22),
			Yaw = 6,
			PriceSeconds = 88,
			Pieces = P(74, 14, function()
				return {
					B(0, 0.5, 0, 30, 1, 8, STONE_D, Sandstone),
					B(-9, 8.6, 0, 8.6, 15.2, 5, STONE, Sandstone),
					B(9, 8.6, 0, 8.6, 15.2, 5, STONE, Sandstone),
					B(-9, 16.6, 0, 10, 1.4, 6, STONE_L, Sandstone),
					B(9, 16.6, 0, 10, 1.4, 6, STONE_L, Sandstone),
					B(0, 13.2, 0, 9.4, 3.8, 4.2, STONE_L, Sandstone),
					Cz(0, 13.4, 2.4, 4.4, 0.5, GOLD, Metal),
					Cy(-9, 14, 3.2, 0.6, 28, WOOD, Wood),
					Cy(9, 14, 3.2, 0.6, 28, WOOD, Wood),
					B(-7.4, 24.4, 3.2, 3, 2.6, 0.2, RED, Fabric),
					B(7.4, 24.4, 3.2, 3, 2.6, 0.2, LAPIS, Fabric),
				}
			end),
		},
		{
			Id = "Obelisks",
			Name = "Twin Obelisks",
			Description = "Two tall granite needles carved with hieroglyphs and tipped with gold.",
			Pad = Vector2.new(40, 44),
			Yaw = -14,
			PriceSeconds = 102,
			Pieces = P(40, 54, function()
				return {
					B(-6, 0.9, -3, 5.6, 1.8, 5.6, STONE_D, Sandstone),
					B(-6, 10.8, -3, 3.2, 18, 3.2, C(214, 120, 96), Rock),
					B(-6, 20.4, -3, 2.2, 3, 2.2, C(214, 120, 96), Rock),
					B(-6, 22.4, -3, 1.4, 1.6, 1.4, GOLD, Metal),
					B(7, 0.9, 3, 4.8, 1.8, 4.8, STONE_D, Sandstone),
					B(7, 8.8, 3, 2.8, 14, 2.8, C(214, 120, 96), Rock),
					B(7, 16.8, 3, 1.9, 2.4, 1.9, C(214, 120, 96), Rock),
					B(7, 18.6, 3, 1.2, 1.4, 1.2, GOLD, Metal),
				}
			end),
		},
		{
			Id = "Oasis",
			Name = "Palm Oasis",
			Description = "A cool blue pond ringed with green grass, reeds and three leaning date palms.",
			Pad = Vector2.new(-62, 38),
			Yaw = 12,
			PriceSeconds = 117,
			Pieces = P(-74, 26, function()
				return {
					B(0, 0.3, 0, 27, 0.5, 21, GRASS, Grass),
					B(-0.5, 0.58, 0, 21, 0.3, 14.5, WATER, Plastic),
					CyT(-7, 5, -5, 1, 10, -8, TRUNK, Wood),
					Ball(-7.8, 10.6, -5, 8, 3, 8, PALM, Grass),
					CyT(8, 5.6, 4, 1, 11.2, 10, TRUNK, Wood),
					Ball(9.2, 11.6, 4, 8, 3, 8, PALM, Grass),
					CyT(-9, 4, 5.5, 1, 8, -14, TRUNK, Wood),
					Ball(-10.2, 8.4, 5.5, 6.4, 2.6, 6.4, PALM, Grass),
					B(10.5, 0.8, -6, 2.2, 1.2, 2, STONE_D, Rock),
					B(1, 1.1, -9, 0.4, 2.2, 0.4, PALM, Grass),
					B(3.5, 1.1, -9.4, 0.4, 2.4, 0.4, PALM, Grass),
				}
			end),
		},
		{
			Id = "Palms",
			Name = "Date Palm Grove",
			Description = "Four tall date palms bent by the desert wind, heavy with bunches of dates.",
			Pad = Vector2.new(-58, 52),
			Yaw = -18,
			PriceSeconds = 134,
			Pieces = P(-72, 52, function()
				return {
					B(0, 0.2, 0, 26, 0.4, 16, SAND_D, Sand),
					CyT(-8, 6.5, -3, 1.2, 13, -10, TRUNK, Wood),
					Ball(-9.4, 13.4, -3, 9.4, 3.2, 9.4, PALM, Grass),
					CyT(-1, 5, 4, 1.2, 10, 8, TRUNK, Wood),
					Ball(0.2, 10.4, 4, 8.4, 3, 8.4, PALM, Grass),
					CyT(6, 7, -2, 1.2, 14, -6, TRUNK, Wood),
					Ball(5, 14.6, -2, 9.6, 3.4, 9.6, PALM, Grass),
					CyT(10, 4.4, 4, 1.2, 8.8, 12, TRUNK, Wood),
					Ball(11.1, 9.2, 4, 7.2, 2.6, 7.2, PALM, Grass),
					B(-1, 9.4, 4.4, 1.2, 1.4, 1.2, GOLD, Plastic),
				}
			end),
		},
		{
			Id = "Bazaar",
			Name = "Desert Bazaar",
			Description = "Three market stalls with striped awnings, baskets of spices and big clay jars.",
			Pad = Vector2.new(-40, 26),
			Yaw = 22,
			PriceSeconds = 154,
			Pieces = P(-48, 22, function()
				return {
					-- stall 1 (red)
					B(-7, 1.3, -3, 5.4, 2.6, 2.4, WOOD, Planks),
					Cy(-9.4, 2.6, -1.4, 0.4, 5.2, WOOD, Wood),
					Cy(-4.6, 2.6, -1.4, 0.4, 5.2, WOOD, Wood),
					B(-7, 5.4, -2.4, 6.4, 0.4, 4.6, RED, Fabric, rot(14, 0, 0)),
					-- stall 2 (blue)
					B(3, 1.3, -5, 5.4, 2.6, 2.4, WOOD, Planks),
					Cy(0.6, 2.6, -3.4, 0.4, 5.2, WOOD, Wood),
					Cy(5.4, 2.6, -3.4, 0.4, 5.2, WOOD, Wood),
					B(3, 5.4, -4.4, 6.4, 0.4, 4.6, LAPIS, Fabric, rot(14, 0, 0)),
					-- stall 3 (gold)
					B(9, 1.3, 4, 2.4, 2.6, 5.4, WOOD, Planks),
					Cy(7.4, 2.6, 1.6, 0.4, 5.2, WOOD, Wood),
					Cy(7.4, 2.6, 6.4, 0.4, 5.2, WOOD, Wood),
					B(8.4, 5.4, 4, 4.6, 0.4, 6.4, GOLD, Fabric, rot(0, 0, -14)),
					-- jars and a basket
					Cy(-1.4, 1.2, 3.6, 2.4, 2.4, MUD, Brick),
					Cy(1, 0.9, 5, 1.8, 1.8, C(196, 110, 76), Brick),
					B(-5, 0.6, 3, 2.2, 1.2, 2.2, C(204, 160, 70), Wood),
				}
			end),
		},
		{
			Id = "Anubis",
			Name = "Anubis Guardians",
			Description = "Two black jackal-headed statues with golden collars watch over the road.",
			Pad = Vector2.new(16, 36),
			Yaw = -20,
			PriceSeconds = 178,
			Pieces = P(16, 26, function()
				return {
					B(-5.5, 1, 0, 5, 2, 5, STONE_D, Sandstone),
					B(-5.5, 5.6, 0, 2.8, 7.2, 1.8, BLACK, Plastic),
					B(-5.5, 8.6, 0.2, 3.4, 1, 2, GOLD, Metal),
					B(-5.5, 10.6, 0.4, 1.8, 2.4, 3.2, BLACK, Plastic),
					B(-5.5, 13, 0, 1.6, 3, 0.8, BLACK, Plastic),
					Cy(-8.2, 6.6, 1.4, 0.4, 9.6, GOLD, Metal),
					B(5.5, 1, 0, 5, 2, 5, STONE_D, Sandstone),
					B(5.5, 5.6, 0, 2.8, 7.2, 1.8, BLACK, Plastic),
					B(5.5, 8.6, 0.2, 3.4, 1, 2, GOLD, Metal),
					B(5.5, 10.6, 0.4, 1.8, 2.4, 3.2, BLACK, Plastic),
					B(5.5, 13, 0, 1.6, 3, 0.8, BLACK, Plastic),
					Cy(8.2, 6.6, 1.4, 0.4, 9.6, GOLD, Metal),
				}
			end),
		},
		{
			Id = "Camel",
			Name = "Camel Caravan",
			Description = "A sleepy camel in a red saddle blanket, with trade crates and a water jar.",
			Pad = Vector2.new(-2, -4),
			Yaw = 28,
			PriceSeconds = 204,
			Pieces = P(-12, 0, function()
				return {
					B(0, 5.2, 0, 7, 3, 2.8, C(196, 150, 96), Fabric),
					Ball(-0.6, 7.4, 0, 2.6, 2.8, 2.4, C(196, 150, 96), Fabric),
					B(-4.4, 7.4, 0, 1.4, 4.2, 1.4, C(196, 150, 96), Fabric, rot(0, 0, -22)),
					B(-5.6, 9.6, 0, 3, 1.6, 1.6, C(206, 164, 110), Fabric),
					B(-2.6, 2.1, -1, 0.9, 4.2, 0.9, C(176, 130, 84), Fabric),
					B(-2.6, 2.1, 1, 0.9, 4.2, 0.9, C(176, 130, 84), Fabric),
					B(2.6, 2.1, -1, 0.9, 4.2, 0.9, C(176, 130, 84), Fabric),
					B(2.6, 2.1, 1, 0.9, 4.2, 0.9, C(176, 130, 84), Fabric),
					B(0.4, 6.8, 0, 3.4, 0.4, 3.2, RED, Fabric),
					B(6.4, 1, -2, 2.4, 2, 2.4, WOOD, Planks),
					B(7, 2.6, -2.2, 2, 1.2, 2, WOOD, Planks, rot(0, 24, 0)),
					Cy(6.6, 1.1, 2.4, 1.8, 2.2, MUD, Brick),
					B(-0.6, 1, 3.6, 3, 0.3, 2, LAPIS, Fabric),
				}
			end),
		},
		{
			Id = "Colonnade",
			Name = "Lotus Colonnade",
			Description = "Two rows of tall columns topped with lotus flowers along a sandstone terrace.",
			Pad = Vector2.new(8, 56),
			Yaw = -9,
			PriceSeconds = 235,
			Pieces = P(8, 46, function()
				return {
					B(0, 0.3, 0, 28, 0.6, 12, STONE_D, Sandstone),
					Cy(-10, 6.6, -4, 2.2, 12, STONE, Sandstone),
					Cy(-3.5, 6.6, -4, 2.2, 12, STONE, Sandstone),
					Cy(3.5, 6.6, -4, 2.2, 12, STONE, Sandstone),
					Cy(10, 6.6, -4, 2.2, 12, STONE, Sandstone),
					Cy(-10, 6.6, 4, 2.2, 12, STONE, Sandstone),
					Cy(-3.5, 6.6, 4, 2.2, 12, STONE, Sandstone),
					Cy(3.5, 6.6, 4, 2.2, 12, STONE, Sandstone),
					Cy(10, 6.6, 4, 2.2, 12, STONE, Sandstone),
					B(0, 13.4, -4, 25, 1.4, 2.4, STONE_L, Sandstone),
					B(0, 13.4, 4, 25, 1.4, 2.4, STONE_L, Sandstone),
					B(0, 15, 0, 25, 0.6, 12, LAPIS, Plastic),
				}
			end),
		},
		{
			Id = "Tomb",
			Name = "Rock Tomb",
			Description = "A tomb cut into a sandstone cliff, with a pillared doorway and two jackal watchers.",
			Pad = Vector2.new(-82, -26),
			Yaw = -12,
			PriceSeconds = 270,
			Pieces = P(-78, -38, function()
				return {
					B(0, 5, -2.5, 24, 10, 9, STONE_D, Sandstone),
					B(2, 11.5, -3, 17, 3, 7, STONE, Sandstone),
					B(-3, 14, -3.5, 9, 2.4, 5, STONE_D, Sandstone),
					B(0, 3.6, 2.6, 8, 7.2, 1.6, STONE_L, Sandstone),
					B(0, 3, 3.5, 4.4, 6, 0.4, BLACK, Rock),
					Cy(-3.4, 3.8, 4, 1.2, 7.6, STONE_L, Sandstone),
					Cy(3.4, 3.8, 4, 1.2, 7.6, STONE_L, Sandstone),
					B(0, 7.6, 3.8, 9.6, 1, 2, GOLD, Metal),
					B(-8, 1, 4.4, 2.4, 2, 3.6, BLACK, Plastic),
					B(8, 1, 4.4, 2.4, 2, 3.6, BLACK, Plastic),
					B(0, 0.4, 6, 8, 0.8, 2.4, STONE_D, Sandstone),
				}
			end),
		},
		{
			Id = "HieroWall",
			Name = "Hieroglyph Wall",
			Description = "A long carved wall painted with gods, birds and golden cartouches.",
			Pad = Vector2.new(-48, -50),
			Yaw = 14,
			PriceSeconds = 310,
			Pieces = P(-60, -56, function()
				return {
					B(0, 3.4, 0, 24, 6.8, 2.4, STONE, Sandstone),
					B(0, 7.2, 0, 25, 0.8, 3, STONE_L, Sandstone),
					B(0, 5.6, 1.3, 22, 1, 0.3, LAPIS, Plastic),
					B(-4, 3, 1.4, 3.2, 3.4, 0.3, GOLD, Metal),
					B(4, 3, 1.4, 3.2, 3.4, 0.3, GOLD, Metal),
					B(-12.6, 4.6, 0, 3, 9.2, 3, STONE_L, Sandstone),
					B(12.6, 4.6, 0, 3, 9.2, 3, STONE_L, Sandstone),
					B(-10, 0.6, 3, 4, 1.2, 1.6, STONE_D, Sandstone),
				}
			end),
		},
		{
			Id = "SunDisc",
			Name = "Sun Disc Shrine",
			Description = "The sun god's golden disc held between two sandstone pillars on a stepped platform.",
			Pad = Vector2.new(-68, -14),
			Yaw = -16,
			PriceSeconds = 357,
			RewardMult = 1.4,
			Pieces = P(-80, -14, function()
				return {
					B(0, 0.6, 0, 18, 1.2, 8, STONE_D, Sandstone),
					B(0, 1.6, 0, 12, 0.8, 5, STONE, Sandstone),
					B(-6, 7.4, 0, 2.6, 12, 2.6, STONE, Sandstone),
					B(6, 7.4, 0, 2.6, 12, 2.6, STONE, Sandstone),
					B(-6, 13.6, 0, 3.6, 1.2, 3.6, STONE_L, Sandstone),
					B(6, 13.6, 0, 3.6, 1.2, 3.6, STONE_L, Sandstone),
					Cz(0, 11.4, 0, 10, 1, GOLD, Metal),
					Cz(0, 11.4, 0.6, 6.4, 0.5, RED, Plastic),
					B(0, 2.6, 1.2, 3, 1.8, 2, LAPIS, Plastic),
				}
			end),
		},
		{
			Id = "Horus",
			Name = "Falcon of Horus",
			Description = "A giant falcon god with the double crown, standing on a stone plinth.",
			Pad = Vector2.new(-54, -22),
			Yaw = 24,
			PriceSeconds = 410,
			Pieces = P(-58, -30, function()
				return {
					B(0, 1, 0, 9, 2, 9, STONE_D, Sandstone),
					B(0, 2.6, 0, 6.4, 1.2, 6.4, STONE, Sandstone),
					Ball(0, 7, 0, 4.4, 7.4, 4, C(86, 60, 44), Fabric),
					Ball(0, 11.6, 0.6, 3, 3, 3, C(86, 60, 44), Fabric),
					B(0, 11, 2.4, 0.8, 1.2, 1.2, GOLD, Metal),
					B(-2.3, 7.4, -0.2, 1, 5.6, 3.6, C(70, 48, 36), Fabric, rot(0, 0, 8)),
					B(2.3, 7.4, -0.2, 1, 5.6, 3.6, C(70, 48, 36), Fabric, rot(0, 0, -8)),
					B(0, 4.4, -2.6, 2.4, 2.8, 1.4, C(70, 48, 36), Fabric, rot(24, 0, 0)),
					Cy(0, 13.8, 0.6, 2, 2.6, GOLD, Metal),
					B(0, 15.6, 0.6, 1.2, 2, 1.2, RED, Plastic),
				}
			end),
		},
		{
			Id = "Scarab",
			Name = "Golden Scarab",
			Description = "A big shiny scarab beetle, symbol of the rising sun, on a carved plinth.",
			Pad = Vector2.new(14, -41),
			Yaw = -30,
			PriceSeconds = 471,
			Pieces = P(14, -52, function()
				return {
					B(0, 1, 0, 11, 2, 9, STONE_D, Sandstone),
					Ball(0, 4.8, 0.6, 9, 4.6, 6.8, LAPIS, Plastic),
					Ball(0, 4.8, -3.2, 5, 3.6, 3, TURQ, Plastic),
					B(0, 5.6, 3.8, 2.6, 2, 1.8, GOLD, Metal),
					B(-4.6, 3.4, 2.6, 2.8, 0.7, 0.7, GOLD, Metal, rot(0, -30, 0)),
					B(4.6, 3.4, 2.6, 2.8, 0.7, 0.7, GOLD, Metal, rot(0, 30, 0)),
					B(-4.8, 3.4, 0, 2.8, 0.7, 0.7, GOLD, Metal),
					B(4.8, 3.4, 0, 2.8, 0.7, 0.7, GOLD, Metal),
					B(-4.4, 3.4, -2.4, 2.8, 0.7, 0.7, GOLD, Metal, rot(0, 30, 0)),
					B(4.4, 3.4, -2.4, 2.8, 0.7, 0.7, GOLD, Metal, rot(0, -30, 0)),
					Ball(0, 8.6, 0.6, 3.2, 3.2, 3.2, GOLD, Metal),
				}
			end),
		},
		{
			Id = "Village",
			Name = "Mudbrick Houses",
			Description = "Three flat-roofed mudbrick houses with a roof ladder, drying pots and a woven mat.",
			Pad = Vector2.new(72, 38),
			Yaw = -8,
			PriceSeconds = 542,
			Pieces = P(82, 36, function()
				return {
					B(-6, 3, -3, 9, 6, 8, MUD, Brick),
					B(5, 2.5, 4, 7, 5, 7, C(196, 150, 104), Brick),
					B(7.5, 4.5, -4.5, 6, 9, 6, MUD, Brick),
					B(-6, 6.3, -3, 9.6, 0.6, 8.6, STONE_D, Sandstone),
					B(5, 5.3, 4, 7.6, 0.6, 7.6, STONE_D, Sandstone),
					B(7.5, 9.3, -4.5, 6.6, 0.6, 6.6, STONE_D, Sandstone),
					B(-6, 2.4, 1.1, 2.4, 4.4, 0.4, BLACK, Rock),
					B(5, 2, 7.6, 2, 3.6, 0.4, BLACK, Rock),
					B(1.8, 3, 4.6, 0.5, 6.4, 0.5, WOOD, Wood, rot(0, 0, 12)),
					Cy(-1.6, 0.9, 3.4, 1.8, 1.8, C(196, 110, 76), Brick),
					B(-5, 0.15, 5.5, 5, 0.3, 3, RED, Fabric),
					B(-6, 7.3, -3, 3, 1.4, 3, LINEN, Fabric),
				}
			end),
		},
		{
			Id = "Shaduf",
			Name = "Shaduf Well",
			Description = "A simple lever well: a long pole with a clay counterweight and a bucket, watering the garden.",
			Pad = Vector2.new(-80, 6),
			Yaw = 20,
			PriceSeconds = 623,
			Pieces = P(-80, 0, function()
				return {
					B(0, 0.3, 0, 10, 0.6, 7, GRASS, Grass),
					B(-1, 3.4, 0, 2, 6.8, 2, MUD, Brick),
					B(0.6, 7, 0, 13, 0.6, 0.6, WOOD, Wood, rot(0, 0, 14)),
					Ball(5.8, 5.8, 0, 2.6, 2.6, 2.6, MUD, Brick),
					Cy(-5.8, 3.6, 0, 1.6, 1.8, WOOD, Wood),
					B(-5.8, 5.6, 0, 0.12, 3, 0.12, WOOD, Wood),
					B(-3, 0.9, 2.2, 3.4, 1.2, 2, WATER, Plastic),
					B(-3, 0.9, 2.2, 3.8, 1.2, 2.4, STONE_D, Sandstone),
				}
			end),
		},
		{
			Id = "Barge",
			Name = "Solar Barge",
			Description = "A golden royal boat with a tall prow and stern, a canopy and steering oars, afloat on a blue canal.",
			Pad = Vector2.new(-24, -22),
			Yaw = 16,
			PriceSeconds = 716,
			Pieces = P(-38, -30, function()
				return {
					B(0, 0.3, 0, 26, 0.6, 12, WATER, Plastic),
					B(0, 1.6, 0, 20, 2.4, 5, WOOD, Planks),
					B(-10.6, 3.8, 0, 2.6, 4.4, 1.6, GOLD, Metal, rot(0, 0, -18)),
					B(10.6, 3.8, 0, 2.6, 4.4, 1.6, GOLD, Metal, rot(0, 0, 18)),
					B(0, 2.9, 0, 20.6, 0.6, 5.6, GOLD, Metal),
					B(-1, 4.4, 0, 6.4, 3, 3.6, STONE_L, Fabric),
					B(-1, 6.4, 0, 8, 0.5, 4.8, RED, Fabric),
					Cy(-4.2, 5, 1.8, 0.4, 5, WOOD, Wood),
					Cy(2.2, 5, 1.8, 0.4, 5, WOOD, Wood),
					CyT(-11.5, 3, 3.8, 0.5, 8, -20, WOOD, Wood),
					CyT(11.5, 3, 3.8, 0.5, 8, 20, WOOD, Wood),
				}
			end),
		},
		{
			Id = "Sarcophagus",
			Name = "Golden Sarcophagus",
			Description = "A golden coffin of a pharaoh resting under a pillared canopy with two fire bowls.",
			Pad = Vector2.new(18, -22),
			Yaw = -22,
			PriceSeconds = 823,
			Pieces = P(28, -24, function()
				return {
					B(0, 0.6, 0, 12, 1.2, 8, STONE_D, Sandstone),
					B(0, 2.6, 0, 8, 2.6, 3, GOLD, Metal),
					B(-3.6, 4.4, 0, 2.2, 1.6, 2.6, LAPIS, Plastic),
					Ball(-3.6, 5.2, 0, 2.2, 2.2, 2.2, GOLD, Metal),
					Cy(-5, 4.4, -3, 0.9, 6.4, STONE_L, Sandstone),
					Cy(5, 4.4, -3, 0.9, 6.4, STONE_L, Sandstone),
					Cy(-5, 4.4, 3, 0.9, 6.4, STONE_L, Sandstone),
					Cy(5, 4.4, 3, 0.9, 6.4, STONE_L, Sandstone),
					B(0, 8, 0, 12, 0.8, 8.4, STONE, Sandstone),
					B(0, 8.6, 0, 10, 0.6, 7, LAPIS, Plastic),
					Cy(-7.4, 1.4, 4, 1.6, 2, STONE_D, Sandstone),
					B(-7.4, 2.8, 4, 1, 0.8, 1, RED, Plastic),
				}
			end),
		},
		{
			Id = "Queens",
			Name = "Queens Pyramids",
			Description = "Three small pyramids for the queens, linked by a sandstone causeway.",
			Pad = Vector2.new(58, 46),
			Yaw = 12,
			PriceSeconds = 947,
			Pieces = P(66, 54, function()
				return {
					B(-7, 2, -2, 12, 4, 12, STONE, Sandstone),
					B(-7, 5.5, -2, 8, 3, 8, STONE_L, Sandstone),
					B(-7, 8, -2, 4, 2, 4, STONE, Sandstone),
					B(-7, 9.4, -2, 1.6, 1, 1.6, GOLD, Metal),
					B(7, 1.8, -3, 9.6, 3.6, 9.6, STONE, Sandstone),
					B(7, 4.9, -3, 6.2, 2.6, 6.2, STONE_L, Sandstone),
					B(7, 7.1, -3, 3, 1.8, 3, STONE, Sandstone),
					B(2, 1.6, 4, 8.4, 3.2, 8.4, STONE, Sandstone),
					B(2, 4.4, 4, 5.2, 2.4, 5.2, STONE_L, Sandstone),
					B(2, 6.4, 4, 2.4, 1.6, 2.4, STONE, Sandstone),
					B(0, 0.3, 1, 3, 0.6, 12, STONE_D, Sandstone, rot(0, 40, 0)),
				}
			end),
		},
		{
			Id = "Pavilion",
			Name = "Royal Pavilion",
			Description = "A shady pavilion with striped silk curtains, a golden throne and two feather fans.",
			Pad = Vector2.new(54, 36),
			Yaw = -18,
			PriceSeconds = 1089,
			Pieces = P(54, 26, function()
				return {
					B(0, 0.6, 0, 14, 1.2, 11, STONE_D, Sandstone),
					Cy(-6, 5.4, -4.4, 0.9, 8.4, GOLD, Metal),
					Cy(6, 5.4, -4.4, 0.9, 8.4, GOLD, Metal),
					Cy(-6, 5.4, 4.4, 0.9, 8.4, GOLD, Metal),
					Cy(6, 5.4, 4.4, 0.9, 8.4, GOLD, Metal),
					B(0, 10.2, 0, 14, 1.2, 11.2, LAPIS, Fabric),
					B(0, 11.2, 0, 11, 0.8, 8.6, GOLD, Metal),
					B(0, 5.8, -5, 12, 7.2, 0.3, RED, Fabric),
					B(0, 2.8, -2.4, 3.2, 3.2, 3, GOLD, Metal),
					B(0, 5.6, -3.6, 3.2, 3.6, 0.8, GOLD, Metal),
					Cy(-4.4, 4, -2, 0.3, 6.4, WOOD, Wood),
					Ball(-4.4, 7.8, -2, 2, 3, 0.6, LINEN, Fabric),
					Cy(4.4, 4, -2, 0.3, 6.4, WOOD, Wood),
					Ball(4.4, 7.8, -2, 2, 3, 0.6, LINEN, Fabric),
				}
			end),
		},
		{
			Id = "Treasure",
			Name = "Treasure Vault",
			Description = "Open chests spilling gold coins, jewels and golden jars: the royal treasure.",
			Pad = Vector2.new(-2, -10),
			Yaw = 26,
			PriceSeconds = 1252,
			RewardMult = 1.4,
			Pieces = P(8, -8, function()
				return {
					B(0, 0.2, 0, 14, 0.4, 10, STONE_D, Sandstone),
					B(-3.5, 1.4, -1.5, 4.4, 2, 3, WOOD, Planks),
					B(-3.5, 3.2, -2.9, 4.4, 0.6, 3, WOOD, Planks, rot(-80, 0, 0)),
					Ball(-3.5, 2.6, -1.5, 4, 2, 2.6, GOLD, Metal),
					B(3.4, 1.2, 0.8, 4, 1.8, 2.8, WOOD, Planks),
					B(3.4, 3, -0.4, 4, 0.6, 2.8, WOOD, Planks, rot(-80, 0, 0)),
					Ball(3.4, 2.3, 0.8, 3.6, 1.8, 2.4, GOLD, Metal),
					Ball(0, 1, 3, 5, 2, 3, GOLD, Metal),
					Cy(-6, 1.8, 2.6, 2, 3.4, GOLD, Metal),
					Cy(6, 1.4, -2.8, 1.8, 2.6, GOLD, Metal),
					B(0, 2.2, 3, 1, 0.9, 1, RED, Plastic),
					B(-1.6, 1.6, 2.6, 0.9, 0.9, 0.9, TURQ, Plastic),
					Cy(0, 4.6, -3.6, 1.6, 0.4, GOLD, Metal),
				}
			end),
		},
		{
			Id = "Scales",
			Name = "Scales of Truth",
			Description = "A golden balance weighing a heart against the feather of truth.",
			Pad = Vector2.new(-58, 8),
			Yaw = -12,
			PriceSeconds = 1440,
			Pieces = P(-66, 6, function()
				return {
					B(0, 0.7, 0, 8, 1.4, 6, STONE_D, Sandstone),
					B(0, 8, 0, 1.4, 13.2, 1.4, GOLD, Metal),
					B(0, 14.4, 0, 14, 0.8, 0.8, GOLD, Metal),
					Ball(0, 15.4, 0, 2.2, 2.2, 2.2, RED, Plastic),
					B(-6.6, 11.2, 0, 0.2, 6, 0.2, GOLD, Metal),
					B(6.6, 11.2, 0, 0.2, 6, 0.2, GOLD, Metal),
					Cy(-6.6, 8, 0, 4.4, 0.5, GOLD, Metal),
					Cy(6.6, 8, 0, 4.4, 0.5, GOLD, Metal),
					Ball(-6.6, 9, 0, 1.8, 1.8, 1.8, RED, Plastic),
					B(6.6, 8.4, 0, 0.5, 2, 0.2, LINEN, Fabric),
					B(3.6, 1.8, 2.6, 2.4, 3.6, 1.4, BLACK, Plastic),
					B(3.6, 4.2, 3, 1.4, 1.6, 2.2, BLACK, Plastic),
				}
			end),
		},
		{
			Id = "Mask",
			Name = "Golden Pharaoh Mask",
			Description = "The showpiece: a giant golden death mask with blue striped headcloth on a stepped dais.",
			Pad = Vector2.new(30, -43),
			Yaw = 18,
			PriceSeconds = 1656,
			RewardMult = 2,
			Pieces = P(31, -54, function()
				return {
					B(0, 0.7, 0, 16, 1.4, 12, STONE_D, Sandstone),
					B(0, 2, 0, 12.4, 1.2, 9.4, STONE, Sandstone),
					B(0, 3.6, 0, 11, 2, 7, STONE_L, Sandstone),
					Ball(0, 10.2, 0, 7.6, 11.2, 5, GOLD, Metal),
					B(-4.8, 9.6, -0.4, 3, 12.4, 3.4, LAPIS, Plastic),
					B(4.8, 9.6, -0.4, 3, 12.4, 3.4, LAPIS, Plastic),
					B(0, 16.6, -0.4, 9.4, 2.4, 3.8, LAPIS, Plastic),
					B(0, 4.4, 1.8, 3.6, 3.6, 1.4, GOLD, Metal),
					B(0, 18.2, 1, 1.2, 1.8, 1.4, RED, Plastic),
					B(0, 9, 2.7, 1, 4, 1, GOLD, Metal),
				}
			end),
		},
	},
}

return theme
