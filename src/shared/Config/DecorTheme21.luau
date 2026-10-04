--!strict
-- Theme of the Shiba of bay 21: Volcano (Config/DecorTypes -> Theme). 160 x 115: Magma Shiba guards the foot of a smoking volcano in the
-- back right, a winding ash path leads past lava rivers, steam vents, a tiki camp, a fossil garden, a mine and an obsidian temple.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lava, fire and embers are plain coloured blocks.
-- Every part is written in local coordinates around its own centre and shifted into place by place().

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local ASH = C(66, 58, 62)
local BASALT = C(52, 48, 58)
local DBASALT = C(34, 32, 42)
local ROCK = C(104, 80, 70)
local LAVA = C(255, 102, 24)
local GLOW = C(255, 190, 64)
local EMBER = C(206, 52, 24)
local BONE = C(228, 216, 188)
local WOOD = C(130, 88, 54)
local DWOOD = C(84, 56, 38)
local THATCH = C(204, 164, 74)
local TEAL = C(70, 190, 190)
local STEAM = C(232, 234, 240)
local OBS = C(22, 22, 32)
local RED = C(180, 44, 40)
local STEEL = C(130, 136, 150)
local DSTEEL = C(76, 80, 94)
local GREEN = C(62, 138, 72)
local RUBY = C(214, 48, 68)

local Slate = Enum.Material.Slate
local Basalt = Enum.Material.Basalt
local Concrete = Enum.Material.Concrete
local Wood = Enum.Material.Wood
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass

local OX, OZ = 0, 0

-- Runs `build` with the part's centre (cx, cz) as the origin of its local coordinates.
local function place(cx: number, cz: number, build: () -> Pieces): Pieces
	OX, OZ = cx, cz
	return build()
end

local function rot(rx: number?, ry: number?, rz: number?): Vector3?
	if (rx or 0) == 0 and (ry or 0) == 0 and (rz or 0) == 0 then
		return nil
	end
	return Vector3.new(rx or 0, ry or 0, rz or 0)
end

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
	ry: number?,
	rz: number?,
	rx: number?
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x + OX, y, z + OZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
		Rotation = rot(rx, ry, rz),
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

-- Cylinder lying along Z (a dish facing the road): diameter d, thickness len.
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

local theme: DecorTypes.Theme = {
	Key = "Volcano",
	Name = "Volcano",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(30, -12), Facing = 270 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(-34, 44),
		Vector2.new(-44, 18),
		Vector2.new(-10, 6),
		Vector2.new(26, -2),
		Vector2.new(-4, -28),
		Vector2.new(-36, -42),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(42, -4),
	AutoPad = Vector2.new(42, 6),
	Parts = {
		{
			Id = "AshGround",
			Name = "Ash Fields",
			Description = "Dark volcanic ash split by glowing lava cracks, with a basalt plate under the Magma Shiba.",
			Pad = Vector2.new(-4, 40),
			PriceSeconds = 53,
			Pieces = place(0, 0, function()
				return {
					B(0, 0.15, 0, 160, 0.3, 115, ASH, Slate),
					B(-30, 0.36, -14, 2.6, 0.12, 24, LAVA, Plastic),
					B(-26, 0.36, -2, 8, 0.12, 2.6, LAVA, Plastic),
					B(-22, 0.36, 8, 2.6, 0.12, 20, LAVA, Plastic),
					B(-52, 0.36, -34, 2.4, 0.12, 20, LAVA, Plastic),
					B(-46, 0.36, -24, 12, 0.12, 2.4, LAVA, Plastic),
					B(12, 0.36, 34, 2.6, 0.12, 26, LAVA, Plastic),
					B(18, 0.36, 22, 12, 0.12, 2.6, LAVA, Plastic),
					B(58, 0.36, 28, 2.4, 0.12, 18, LAVA, Plastic),
					B(63, 0.36, 18, 10, 0.12, 2.4, LAVA, Plastic),
					B(-8, 0.36, -44, 2.4, 0.12, 18, LAVA, Plastic),
					B(-2, 0.36, -35, 12, 0.12, 2.4, LAVA, Plastic),
					B(-66, 0.36, 22, 2.2, 0.12, 20, LAVA, Plastic),
					B(30, 0.34, -12, 16, 0.1, 16, DBASALT, Slate),
					B(30, 0.42, -12, 11, 0.1, 11, BASALT, Slate),
				}
			end),
		},
		{
			Id = "Volcano",
			Name = "The Volcano",
			Description = "A huge dark cone of stacked basalt with a glowing crater and lava stains running down its flanks.",
			Pad = Vector2.new(32, -44),
			PriceSeconds = 61,
			Pieces = place(58, -37, function()
				return {
					Cy(0, 4, 0, 38, 8, BASALT, Slate),
					Cy(0, 12, 0, 30, 8, DBASALT, Slate),
					Cy(0, 20, 0, 23, 8, BASALT, Slate),
					Cy(0, 28, 0, 17, 8, DBASALT, Slate),
					Cy(0, 34.5, 0, 11, 5, BASALT, Slate),
					Cy(0, 37.2, 0, 8, 0.6, LAVA, Plastic),
					Ball(-9, 3, 12, 12, 6, 9, ROCK, Slate),
					Ball(14, 2.5, 10, 10, 5, 8, ROCK, Slate),
					Ball(12, 2.5, -14, 12, 5, 10, DBASALT, Slate),
				}
			end),
		},
		{
			Id = "Sign",
			Name = "Get Bonked Sign",
			Description = "A scorched basalt board on two posts that reads GET BONKED with an ember-red top edge.",
			Yaw = -12,
			Pad = Vector2.new(6, 42),
			PriceSeconds = 70,
			Pieces = place(12, 50, function()
				return {
					B(-5, 3, 0, 0.8, 6, 0.8, DWOOD, Wood),
					B(5, 3, 0, 0.8, 6, 0.8, DWOOD, Wood),
					B(0, 6.8, 0, 12, 5, 0.8, DBASALT, Slate),
					B(0, 9.5, 0, 12.6, 0.5, 1.2, EMBER, Plastic),
					Ball(-7, 0.8, 1, 2.6, 1.6, 2, ROCK, Slate),
					Ball(7, 0.7, -1, 2.2, 1.4, 2, ROCK, Slate),
				}
			end),
		},
		{
			Id = "Basalt",
			Name = "Basalt Columns",
			Description = "A loose cluster of six-sided basalt columns of every height, like a giant's broken staircase.",
			Yaw = 14,
			Pad = Vector2.new(-52, 28),
			PriceSeconds = 81,
			Pieces = place(-62, 31, function()
				return {
					Cy(0, 6, 0, 4, 12, BASALT, Basalt),
					Cy(-4.5, 4.5, 1.5, 3.6, 9, DBASALT, Basalt),
					Cy(4.2, 3.5, -1, 3.4, 7, BASALT, Basalt),
					Cy(-2, 3, -4.5, 3, 6, DBASALT, Basalt),
					Cy(2.5, 2.5, 4, 3, 5, BASALT, Basalt),
					Cy(-7, 2, -3, 3, 4, BASALT, Basalt),
					Cy(7, 1.5, 3, 2.8, 3, DBASALT, Basalt),
				}
			end),
		},
		{
			Id = "Vents",
			Name = "Steam Vents",
			Description = "Three small rocky mounds hissing white steam, each puffing at its own pace.",
			Yaw = -20,
			Pad = Vector2.new(28, 24),
			PriceSeconds = 93,
			Pieces = place(37, 31, function()
				return {
					Cy(-5, 0.9, 0, 8, 1.8, ROCK, Slate),
					Cy(-5, 2.3, 0, 4.4, 1.2, DBASALT, Slate),
					Ball(-5, 5, 0, 3, 3.5, 3, STEAM, Plastic),
					Cy(4, 0.7, -3, 6, 1.4, ROCK, Slate),
					Cy(4, 1.8, -3, 3.4, 0.9, DBASALT, Slate),
					Ball(4, 4.2, -3, 2.4, 3, 2.4, STEAM, Plastic),
					Cy(0, 0.6, 5, 5, 1.2, ROCK, Slate),
					Cy(0, 1.5, 5, 3, 0.8, DBASALT, Slate),
					Ball(0, 3.5, 5, 2, 2.6, 2, STEAM, Plastic),
					Ball(5.5, 6.4, -3.5, 2, 2, 2, STEAM, Plastic),
				}
			end),
		},
		{
			Id = "LavaRiver",
			Name = "Lava River",
			Description = "A glowing river of lava winding down from the volcano and ending in a bubbling pool between dark banks.",
			Pad = Vector2.new(64, 24),
			PriceSeconds = 107,
			Pieces = place(73, -6, function()
				return {
					B(-3, 0.45, -14, 4, 0.2, 10, LAVA, Plastic),
					B(0.5, 0.45, -9, 11, 0.2, 4, LAVA, Plastic),
					B(4, 0.45, -2, 4, 0.2, 10, LAVA, Plastic),
					B(0, 0.45, 3.5, 12, 0.2, 4, LAVA, Plastic),
					B(-4, 0.45, 10, 4, 0.2, 10, LAVA, Plastic),
					B(-2, 0.45, 21, 10, 0.2, 10, LAVA, Plastic),
					B(3, 0.8, -12, 2, 1.6, 2.2, DBASALT, Slate, 20),
					B(-6, 0.8, 0, 2.4, 1.6, 2, DBASALT, Slate, -15),
					B(2, 0.7, 12, 2, 1.4, 2.4, DBASALT, Slate, 10),
					B(-7, 0.7, 20, 2.2, 1.4, 2, DBASALT, Slate, -25),
				}
			end),
		},
		{
			Id = "TikiHut",
			Name = "Tiki Hut",
			Description = "A thatched hut on four stilts with a little ladder, where the island guides rest.",
			Yaw = -18,
			Pad = Vector2.new(-50, 44),
			PriceSeconds = 123,
			Pieces = place(-62, 47, function()
				return {
					Cy(-5, 1.5, -5, 1, 3, DWOOD, Wood),
					Cy(5, 1.5, -5, 1, 3, DWOOD, Wood),
					Cy(-5, 1.5, 5, 1, 3, DWOOD, Wood),
					Cy(5, 1.5, 5, 1, 3, DWOOD, Wood),
					B(0, 3.2, 0, 12, 0.6, 12, WOOD, Wood),
					B(0, 6, 0, 9, 5.4, 9, DWOOD, Wood),
					B(0, 9.4, 0, 13, 2, 13, THATCH, Fabric),
					B(0, 11, 0, 9.5, 2, 9.5, THATCH, Fabric),
					B(0, 12.6, 0, 5.5, 1.8, 5.5, THATCH, Fabric),
					B(0, 0.8, 6.8, 2.4, 1.6, 2, WOOD, Wood),
				}
			end),
		},
		{
			Id = "HotSpring",
			Name = "Hot Spring",
			Description = "A steaming turquoise pool ringed with warm boulders.",
			Yaw = 10,
			Pad = Vector2.new(-5, 28),
			PriceSeconds = 141,
			Pieces = place(-16, 28, function()
				return {
					Cy(0, 0.5, 0, 15, 1, ROCK, Slate),
					Cy(0, 0.95, 0, 12, 0.3, TEAL, Plastic),
					Ball(-7, 1.4, 2, 3.5, 2.8, 3, ROCK, Slate),
					Ball(6, 1.2, -4, 3, 2.4, 3.4, ROCK, Slate),
					Ball(2, 1.5, 7, 4, 3, 3, ROCK, Slate),
					Ball(-3, 1.3, -7, 3.2, 2.6, 3, ROCK, Slate),
					Ball(-1, 4, 0, 4, 3, 4, STEAM, Plastic),
					Ball(2, 6.5, 1, 3, 3, 3, STEAM, Plastic),
				}
			end),
		},
		{
			Id = "Totems",
			Name = "Tiki Totems",
			Description = "Three carved wooden totem poles of different heights, grinning at everybody who passes.",
			Yaw = 12,
			Pad = Vector2.new(14, 17),
			PriceSeconds = 162,
			Pieces = place(12, 26, function()
				return {
					B(-4, 0.5, -1, 3.2, 1, 3.2, BASALT, Slate),
					B(-4, 4.5, -1, 2.4, 7, 2.4, WOOD, Wood),
					B(-4, 9, -1, 3.4, 2.2, 2.6, RED, Wood),
					B(-4, 10.6, -1, 2.6, 1.2, 2.6, GLOW, Wood),
					B(2, 0.5, 2, 3, 1, 3, BASALT, Slate),
					B(2, 3.5, 2, 2.2, 5, 2.2, DWOOD, Wood),
					B(2, 6.8, 2, 3.4, 1.8, 2, RED, Wood),
					B(6.5, 0.5, -2.5, 3, 1, 3, BASALT, Slate),
					B(6.5, 3.8, -2.5, 2.2, 5.6, 2.2, WOOD, Wood),
					B(6.5, 7.2, -2.5, 2.8, 1.6, 2.8, GLOW, Wood),
				}
			end),
		},
		{
			Id = "Forge",
			Name = "Obsidian Forge",
			Description = "A stone smithy with a glowing furnace, a tall chimney, an anvil and two cooling barrels.",
			Yaw = -15,
			Pad = Vector2.new(42, 50),
			PriceSeconds = 186,
			Pieces = place(52, 42, function()
				return {
					B(0, 5, 0, 18, 10, 12, BASALT, Slate),
					B(0, 10.6, 0, 20, 1.2, 14, DBASALT, Slate),
					B(5, 15, -2, 3.4, 9, 3.4, ROCK, Slate),
					B(5, 19.8, -2, 4.4, 0.8, 4.4, DBASALT, Slate),
					B(-4, 3, 6.1, 4, 4, 0.4, LAVA, Plastic),
					B(-8, 1, 9, 2.4, 2, 1.4, DSTEEL, Metal),
					B(-8, 2.2, 9, 3.6, 0.8, 1.6, STEEL, Metal),
					Cy(8, 1.2, 8, 2.4, 2.4, DWOOD, Wood),
					Cy(10.8, 1.2, 7, 2.4, 2.4, DWOOD, Wood),
					B(0, 8, 8, 20, 0.6, 4, DWOOD, Wood),
					Cy(-9, 4, 9.6, 0.8, 8, DWOOD, Wood),
					Cy(9, 4, 9.6, 0.8, 8, DWOOD, Wood),
				}
			end),
		},
		{
			Id = "Campsite",
			Name = "Explorer Camp",
			Description = "Two little tents round a crackling campfire with log seats.",
			Yaw = 22,
			Pad = Vector2.new(66, 24),
			PriceSeconds = 214,
			Pieces = place(68, 32, function()
				return {
					B(-4.6, 2.2, -2.2, 0.4, 5, 6, RED, Fabric, 0, 38),
					B(-1.4, 2.2, -2.2, 0.4, 5, 6, RED, Fabric, 0, -38),
					B(-4, 2.2, 3.4, 0.4, 4.6, 5, THATCH, Fabric, 0, 38),
					B(-0.8, 2.2, 3.4, 0.4, 4.6, 5, THATCH, Fabric, 0, -38),
					Cy(4.5, 0.4, 0.5, 3.4, 0.8, ROCK, Slate),
					Ball(4.5, 1.8, 0.5, 1.6, 2.4, 1.6, GLOW, Plastic),
					B(4.5, 0.5, 4.3, 3.6, 1, 0.9, DWOOD, Wood, 15),
					B(8, 0.5, -1.6, 0.9, 1, 3.6, DWOOD, Wood, 10),
					B(1, 0.7, -5, 1.4, 1.4, 1.4, WOOD, Wood, 20),
				}
			end),
		},
		{
			Id = "Torches",
			Name = "Tiki Torches",
			Description = "Five bamboo torches planted at different heights, each with a flickering flame.",
			Yaw = -16,
			Pad = Vector2.new(24, -34),
			PriceSeconds = 247,
			Pieces = place(14, -31, function()
				return {
					Cy(-4, 2.2, -2, 0.7, 4.4, DWOOD, Wood),
					Cy(-4, 4.7, -2, 1.8, 0.7, DSTEEL, Metal),
					Ball(-4, 5.9, -2, 1.5, 2.2, 1.5, GLOW, Plastic),
					Cy(0, 2.6, 3, 0.7, 5.2, DWOOD, Wood),
					Cy(0, 5.4, 3, 1.8, 0.7, DSTEEL, Metal),
					Ball(0, 6.6, 3, 1.5, 2.2, 1.5, LAVA, Plastic),
					Cy(5, 1.9, -1, 0.7, 3.8, DWOOD, Wood),
					Cy(5, 4, -1, 1.8, 0.7, DSTEEL, Metal),
					Ball(5, 5.2, -1, 1.5, 2.2, 1.5, GLOW, Plastic),
					Cy(8, 2.4, 4, 0.7, 4.8, DWOOD, Wood),
					Cy(8, 5, 4, 1.8, 0.7, DSTEEL, Metal),
					Ball(8, 6.2, 4, 1.5, 2.2, 1.5, LAVA, Plastic),
					Cy(-1.5, 1.7, -6.5, 0.7, 3.4, DWOOD, Wood),
					Cy(-1.5, 3.6, -6.5, 1.8, 0.7, DSTEEL, Metal),
					Ball(-1.5, 4.8, -6.5, 1.5, 2.2, 1.5, GLOW, Plastic),
				}
			end),
		},
		{
			Id = "Fossil",
			Name = "Fossil Garden",
			Description = "The huge ribcage and skull of an ancient lava beast half buried in the ash.",
			Yaw = -16,
			Pad = Vector2.new(-26, -17),
			PriceSeconds = 284,
			Pieces = place(-30, -24, function()
				return {
					B(-4, 3.2, 1.8, 0.7, 6.4, 0.7, BONE, Slate),
					B(-4, 3.2, -1.8, 0.7, 6.4, 0.7, BONE, Slate),
					B(-4, 6.5, 0, 0.7, 0.7, 4.3, BONE, Slate),
					B(-0.5, 3.2, 2, 0.7, 6.4, 0.7, BONE, Slate),
					B(-0.5, 3.2, -2, 0.7, 6.4, 0.7, BONE, Slate),
					B(-0.5, 6.9, 0, 0.7, 0.7, 4.7, BONE, Slate),
					B(3, 3, 1.8, 0.7, 6, 0.7, BONE, Slate),
					B(3, 3, -1.8, 0.7, 6, 0.7, BONE, Slate),
					B(3, 6.2, 0, 0.7, 0.7, 4.3, BONE, Slate),
					B(0, 7.2, 0, 17, 0.8, 0.8, BONE, Slate),
					Ball(-11, 2.6, 0, 6, 4.4, 4, BONE, Slate),
					B(-12.5, 0.9, 0, 4, 1.2, 3, BONE, Slate),
					B(9, 3.2, 0, 7, 2.2, 1, BONE, Slate),
				}
			end),
		},
		{
			Id = "Mine",
			Name = "Old Mine",
			Description = "A timber-framed mine entrance cut into a rocky hill, with rails and an ore cart waiting outside.",
			Yaw = 20,
			Pad = Vector2.new(-54, 4),
			PriceSeconds = 326,
			Pieces = place(-64, 8, function()
				return {
					Ball(0, 5, -2, 22, 10, 14, ROCK, Slate),
					Ball(9, 3, -4, 12, 6, 10, BASALT, Slate),
					B(0, 3.2, 4.9, 6, 6.4, 0.4, OBS, Slate),
					B(-4, 3.5, 5.4, 1, 7, 1, DWOOD, Wood),
					B(4, 3.5, 5.4, 1, 7, 1, DWOOD, Wood),
					B(0, 7.2, 5.4, 10, 1, 1.2, DWOOD, Wood),
					B(-0.9, 0.25, 11, 0.5, 0.3, 10, DSTEEL, Metal),
					B(0.9, 0.25, 11, 0.5, 0.3, 10, DSTEEL, Metal),
					B(0, 1.5, 10, 3.4, 1.6, 4.4, STEEL, Metal),
					Ball(0, 2.7, 10, 2.6, 1.6, 3, DBASALT, Slate),
					Ball(5.6, 6.2, 6.2, 1, 1, 1, GLOW, Plastic),
				}
			end),
		},
		{
			Id = "Crystals",
			Name = "Ruby Crystals",
			Description = "A cluster of sharp red and orange crystals pushing up between the rocks.",
			Yaw = -22,
			Pad = Vector2.new(17, -54),
			PriceSeconds = 375,
			Pieces = place(24, -50, function()
				return {
					B(0, 5, 0, 3, 10, 3, RUBY, Plastic, 20, 6),
					B(-3.5, 3.4, 1.5, 2.4, 6.8, 2.4, LAVA, Plastic, -10, -12),
					B(3.6, 3, -1.2, 2.2, 6, 2.2, RUBY, Plastic, 35, 10),
					B(-1.5, 2.2, -3.8, 1.8, 4.4, 1.8, GLOW, Plastic, 12, -8),
					B(1.8, 2, 3.6, 1.8, 4, 1.8, LAVA, Plastic, -25, 14),
					B(6, 1.4, 2, 1.4, 2.8, 1.4, RUBY, Plastic, 8, -16),
					B(-5.5, 0.9, -2, 3.4, 1.8, 3, DBASALT, Slate, 18),
					B(4, 0.8, -4.5, 3, 1.6, 2.6, BASALT, Slate, -22),
					B(0.5, 0.7, 3.8, 3.2, 1.4, 2.4, DBASALT, Slate, 30),
				}
			end),
		},
		{
			Id = "Station",
			Name = "Seismo Station",
			Description = "A small white research hut with a radio mast and satellite dish that watches the volcano for tremors.",
			Yaw = 14,
			Pad = Vector2.new(36, 12),
			PriceSeconds = 431,
			Pieces = place(42, 18, function()
				return {
					B(0, 2.5, 0, 10, 5, 7, BONE, Concrete),
					B(0, 5.4, 0, 11, 0.8, 8, RED, Metal),
					B(0, 2, 3.6, 2.4, 4, 0.3, DWOOD, Wood),
					B(3.4, 2.4, 3.6, 2.2, 1.6, 0.3, TEAL, Plastic),
					Cy(-3.5, 6.5, -1.5, 0.8, 13, STEEL, Metal),
					Cz(-3.5, 11, -0.4, 4.2, 0.8, BONE, Metal),
					Ball(-3.5, 13.2, -1.5, 1, 1, 1, EMBER, Plastic),
					B(5.4, 0.8, -2, 1.6, 1.6, 1.6, DSTEEL, Metal),
				}
			end),
		},
		{
			Id = "Watchtower",
			Name = "Lookout Tower",
			Description = "A wooden lookout on four tall legs with a little cabin and a red roof to spot eruptions early.",
			Yaw = 15,
			Pad = Vector2.new(-66, -12),
			PriceSeconds = 496,
			Pieces = place(-58, -22, function()
				return {
					Cy(-3, 7, -3, 1, 14, DWOOD, Wood),
					Cy(3, 7, -3, 1, 14, DWOOD, Wood),
					Cy(-3, 7, 3, 1, 14, DWOOD, Wood),
					Cy(3, 7, 3, 1, 14, DWOOD, Wood),
					B(0, 14.4, 0, 10, 0.8, 10, WOOD, Wood),
					B(0, 17.4, 0, 7, 5, 7, DWOOD, Wood),
					B(0, 20.6, 0, 10, 1.2, 10, RED, Wood),
					B(0, 5, 3.2, 6.6, 0.4, 0.4, DWOOD, Wood),
					B(0, 9, 3.2, 6.6, 0.4, 0.4, DWOOD, Wood),
					B(0, 6, 4.4, 1.8, 12, 0.5, WOOD, Wood),
				}
			end),
		},
		{
			Id = "Palms",
			Name = "Palm Grove",
			Description = "Four wind-bent palm trees with big green fronds growing on a warm patch of ground.",
			Yaw = 18,
			Pad = Vector2.new(22, 33),
			PriceSeconds = 570,
			Pieces = place(18, 40, function()
				return {
					B(-3.5, 4, -1.5, 1.2, 8, 1.2, WOOD, Wood, 0, 6),
					B(-3.9, 8.3, -1.5, 7, 0.3, 1.8, GREEN, Grass, 0),
					B(-3.9, 8.3, -1.5, 7, 0.3, 1.8, GREEN, Grass, 70),
					B(3, 3.5, 1, 1.2, 7, 1.2, WOOD, Wood, 0, -7),
					B(3.4, 7.3, 1, 6.4, 0.3, 1.8, GREEN, Grass, 25),
					B(3.4, 7.3, 1, 6.4, 0.3, 1.8, GREEN, Grass, 95),
					B(0.5, 3, -5, 1, 6, 1, WOOD, Wood, 0, 5),
					B(0.5, 6.3, -5, 5.6, 0.3, 1.6, GREEN, Grass, 40),
					B(0.5, 6.3, -5, 5.6, 0.3, 1.6, GREEN, Grass, 110),
					B(0, 2.4, 4.5, 0.9, 4.8, 0.9, WOOD, Wood, 0, -6),
					B(0, 5.1, 4.5, 4.6, 0.3, 1.4, GREEN, Grass, 15),
					B(0, 5.1, 4.5, 4.6, 0.3, 1.4, GREEN, Grass, 85),
				}
			end),
		},
		{
			Id = "Eggs",
			Name = "Dragon Nest",
			Description = "A nest of dark twigs holding four warm speckled dragon eggs of different colours.",
			Yaw = 25,
			Pad = Vector2.new(-12, -2),
			PriceSeconds = 656,
			Pieces = place(-14, -12, function()
				return {
					Cy(0, 0.4, 0, 10, 0.8, DWOOD, Wood),
					Cy(0, 0.85, 0, 7, 0.5, ASH, Slate),
					Ball(-1.6, 2.4, -0.6, 3.2, 4.2, 3.2, EMBER, Plastic),
					Ball(1.6, 2.2, 0.8, 3, 4, 3, GLOW, Plastic),
					Ball(0.2, 2, 2, 2.8, 3.6, 2.8, RUBY, Plastic),
					Ball(-0.4, 1.9, -2.2, 2.6, 3.4, 2.6, LAVA, Plastic),
					B(-5.6, 0.7, 0, 1.8, 1.4, 2.4, DBASALT, Slate, 20),
					B(5.4, 0.7, 1.4, 1.8, 1.4, 2.2, DBASALT, Slate, -20),
					B(1, 0.6, -5.2, 2.2, 1.2, 1.6, BASALT, Slate, 35),
				}
			end),
		},
		{
			Id = "Drill",
			Name = "Geothermal Drill",
			Description = "A steel derrick tower with a long drill pipe, a pump tank and a crown block on top.",
			Yaw = 14,
			Pad = Vector2.new(5, -34),
			PriceSeconds = 754,
			Pieces = place(8, -43, function()
				return {
					B(0, 0.6, 0, 10, 1.2, 10, DBASALT, Slate),
					Cy(-3, 12, -3, 0.8, 22, DSTEEL, Metal),
					Cy(3, 12, -3, 0.8, 22, DSTEEL, Metal),
					Cy(-3, 12, 3, 0.8, 22, DSTEEL, Metal),
					Cy(3, 12, 3, 0.8, 22, DSTEEL, Metal),
					Cy(0, 11, 0, 1.6, 20, STEEL, Metal),
					B(0, 23.2, 0, 6, 1.4, 6, STEEL, Metal),
					B(0, 7, 3.2, 6.6, 0.4, 0.4, DSTEEL, Metal),
					B(0, 14, 3.2, 6.6, 0.4, 0.4, DSTEEL, Metal),
					Cy(6.8, 2.8, 2.5, 3.6, 3.2, DWOOD, Metal),
					B(-5.8, 2, -3.4, 2.6, 2.2, 2.6, EMBER, Metal),
				}
			end),
		},
		{
			Id = "Dragon",
			Name = "Dragon Statue",
			Description = "A great lava-stone dragon with spread wings and a long tail on a pedestal, guarding the west.",
			Yaw = -18,
			Pad = Vector2.new(-35, 10),
			RewardMult = 1.5,
			PriceSeconds = 867,
			Pieces = place(-35, -8, function()
				return {
					B(0, 1.2, 0, 8, 2.4, 14, DBASALT, Slate),
					B(0, 5.2, 0, 5, 4.4, 9, BASALT, Slate),
					B(0, 8.8, 4.5, 2.8, 5, 2.8, BASALT, Slate, 0, 0, -12),
					B(0, 11.4, 6.6, 3.4, 2.6, 5, DBASALT, Slate),
					B(-5, 8.2, -0.5, 6, 0.6, 6, ROCK, Slate, 25, -22),
					B(5, 8.2, -0.5, 6, 0.6, 6, ROCK, Slate, -25, 22),
					B(0, 4, -7.5, 2.4, 1.8, 7, BASALT, Slate),
					B(0, 3.4, -11.5, 1.4, 1.2, 4, DBASALT, Slate),
					Ball(-0.9, 12, 8.6, 0.8, 0.8, 0.8, LAVA, Plastic),
					Ball(0.9, 12, 8.6, 0.8, 0.8, 0.8, LAVA, Plastic),
				}
			end),
		},
		{
			Id = "Temple",
			Name = "Obsidian Temple",
			Description = "A four-step stone ziggurat with a dark shrine on top, braziers at the corners and a wide stair to the road.",
			Yaw = 12,
			Pad = Vector2.new(-48, -38),
			RewardMult = 1.4,
			PriceSeconds = 998,
			Pieces = place(-60, -43, function()
				return {
					B(0, 1.5, 0, 24, 3, 24, DBASALT, Slate),
					B(0, 5.5, 0, 19, 5, 19, BASALT, Slate),
					B(0, 10.5, 0, 14, 5, 14, DBASALT, Slate),
					B(0, 15.5, 0, 9, 5, 9, BASALT, Slate),
					B(0, 19.4, 0, 6, 2.8, 6, OBS, Slate),
					B(0, 21.2, 0, 8, 0.8, 8, EMBER, Slate),
					B(0, 0.8, 13.2, 7, 1.6, 2.4, ROCK, Slate),
					B(0, 2.4, 11.6, 7, 1.6, 1.6, ROCK, Slate),
					B(0, 8, 9.9, 5, 4, 0.4, LAVA, Plastic),
					Cy(-10.5, 3.7, 10.5, 1.8, 1.4, DSTEEL, Metal),
					Cy(10.5, 3.7, 10.5, 1.8, 1.4, DSTEEL, Metal),
					Ball(-10.5, 5, 10.5, 1.6, 2, 1.6, GLOW, Plastic),
					Ball(10.5, 5, 10.5, 1.6, 2, 1.6, GLOW, Plastic),
				}
			end),
		},
		{
			Id = "Heart",
			Name = "Magma Heart",
			Description = "A great glowing crystal of molten rock on a round dais, with smaller shards and floating embers around it.",
			Yaw = 20,
			Pad = Vector2.new(52, -6),
			RewardMult = 1.5,
			PriceSeconds = 1147,
			Pieces = place(56, 4, function()
				return {
					Cy(0, 0.6, 0, 13, 1.2, DBASALT, Slate),
					Cy(0, 1.4, 0, 9.5, 0.4, EMBER, Plastic),
					B(0, 6.4, 0, 4.4, 10, 4.4, LAVA, Plastic, 45, 4),
					B(-3.4, 4, 1, 2.2, 6.4, 2.2, RUBY, Plastic, 20, 16),
					B(3.4, 3.6, -1, 2.2, 5.6, 2.2, EMBER, Plastic, -20, -14),
					B(1, 3.4, 3.6, 2, 5, 2, RUBY, Plastic, 10, -4, 14),
					B(-1, 3, -3.6, 2, 4.4, 2, EMBER, Plastic, 35, 6, -14),
					Ball(-3, 10.5, 2, 1.1, 1.1, 1.1, GLOW, Plastic),
					Ball(3.2, 12, -1, 1.2, 1.2, 1.2, GLOW, Plastic),
					Ball(0.5, 13.4, 3, 0.9, 0.9, 0.9, LAVA, Plastic),
					B(-5.6, 1.1, -3, 2, 2.2, 2.4, BASALT, Slate, 25),
					B(5.4, 1.1, 3, 2, 2.2, 2.4, BASALT, Slate, -25),
				}
			end),
		},
		{
			Id = "Throne",
			Name = "Obsidian Throne",
			Description = "A tall black throne with spiked back and ember red cushion on a round stone dais flanked by two braziers.",
			Yaw = -14,
			Pad = Vector2.new(71, 52),
			PriceSeconds = 1319,
			Pieces = place(72, 47, function()
				return {
					B(0, 0.8, 0, 10, 1.6, 9, DBASALT, Slate),
					B(0, 0.5, 5.8, 6, 1, 2.6, ROCK, Slate),
					B(0, 5.4, -3, 4.6, 7.6, 1.4, OBS, Slate),
					B(-2.1, 9.8, -3, 0.8, 2.6, 1.0, OBS, Slate, 0, 8),
					B(2.1, 9.8, -3, 0.8, 2.6, 1.0, OBS, Slate, 0, -8),
					B(0, 11, -3, 0.8, 3.4, 1.0, OBS, Slate),
					B(0, 2.9, -0.4, 4, 2.6, 4.4, OBS, Slate),
					B(0, 4.4, 0.4, 3.4, 0.8, 3, EMBER, Fabric),
					B(-2.8, 3.8, 0.4, 0.8, 1.8, 3.6, OBS, Slate),
					B(2.8, 3.8, 0.4, 0.8, 1.8, 3.6, OBS, Slate),
					Cy(-6.6, 2.4, 2.6, 1.4, 4.4, DSTEEL, Metal),
					Cy(6.6, 2.4, 2.6, 1.4, 4.4, DSTEEL, Metal),
					Ball(-6.6, 5.2, 2.6, 1.8, 2.2, 1.8, GLOW, Plastic),
					Ball(6.6, 5.2, 2.6, 1.8, 2.2, 1.8, GLOW, Plastic),
				}
			end),
		},
		{
			Id = "Eruption",
			Name = "Great Eruption",
			Description = "The crowning show: a column of fire rising from the crater into a billowing ash cloud, with flying lava bombs.",
			Pad = Vector2.new(35.5, -50),
			RewardMult = 2,
			PriceSeconds = 1517,
			Pieces = place(58, -37, function()
				return {
					Cy(0, 38, 0, 10, 1.2, EMBER, Plastic),
					Cy(0, 41.5, 0, 4.4, 5.6, GLOW, Plastic),
					Ball(0, 46, 0, 7, 8, 7, LAVA, Plastic),
					Ball(-4.4, 50, 2, 6.4, 5.6, 6.4, EMBER, Plastic),
					Ball(4.6, 51, -1.4, 8.4, 6.4, 8.4, DBASALT, Plastic),
					Ball(0, 53, 0.4, 7, 5, 7, BASALT, Plastic),
					Ball(-10, 44, -3, 2.2, 2.2, 2.2, LAVA, Plastic),
					Ball(11, 46, 3, 2.4, 2.4, 2.4, EMBER, Plastic),
					Ball(8, 40, -8, 1.8, 1.8, 1.8, GLOW, Plastic),
				}
			end),
		},
	},
}

return theme
