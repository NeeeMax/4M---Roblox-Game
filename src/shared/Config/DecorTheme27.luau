--!strict
-- Theme of the Shiba of bay 27: Beanstalk and Stone Circle (Config/DecorTypes -> Theme). 180 x 130: the Giant Shiba (16 studs tall)
-- stands on a slate plaza in a green giant's meadow. The walkway winds past a signpost and a field wall at the entrance, a cottage,
-- cow, oak and well, giant things lying about (boots, cauldron, table, stool, a club stuck in the earth), a ring of standing stones
-- in the west and, in the back right corner, the huge beanstalk: roots, a twisting stem 74 studs tall, big leaves around it, and the
-- golden goose in its nest on top. A castle floats on a cloud in the back. Parts are loose clusters, no part touches the walkway.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: gold is plain coloured metal blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local GRASS = C(112, 176, 84)
local GRASS2 = C(86, 148, 70)
local DIRT = C(146, 110, 74)
local DDIRT = C(110, 80, 56)
local STONE = C(150, 152, 158)
local DSTONE = C(110, 112, 120)
local LSTONE = C(188, 190, 192)
local MOSS = C(100, 138, 78)
local WOOD = C(156, 108, 66)
local DWOOD = C(108, 72, 46)
local LWOOD = C(196, 150, 96)
local THATCH = C(222, 184, 92)
local CREAM = C(244, 232, 204)
local RED = C(206, 72, 60)
local ROOFRED = C(184, 92, 70)
local BEAN = C(96, 180, 70)
local DBEAN = C(56, 132, 62)
local PBEAN = C(150, 96, 170)
local LBEAN = C(158, 214, 104)
local GOLD = C(244, 198, 58)
local DGOLD = C(200, 148, 40)
local LGOLD = C(255, 228, 130)
local WHITE = C(248, 248, 244)
local BLACK = C(46, 44, 52)
local IRON = C(84, 88, 98)
local WATER = C(110, 176, 228)
local HAY = C(232, 196, 92)
local BROWN = C(140, 92, 60)
local COWBROWN = C(168, 104, 66)
local PINK = C(240, 170, 170)
local TAN = C(214, 184, 130)
local SKY = C(150, 200, 238)
local CASTLE = C(236, 228, 214)
local SLATEBLUE = C(92, 112, 176)
local ORANGE = C(240, 150, 50)

local Grass = Enum.Material.Grass
local Slate = Enum.Material.Slate
local Granite = Enum.Material.Granite
local Cobble = Enum.Material.Cobblestone
local Rock = Enum.Material.Rock
local Ground = Enum.Material.Ground
local Mud = Enum.Material.Mud
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Fabric = Enum.Material.Fabric
local Metal = Enum.Material.Metal
local Concrete = Enum.Material.Concrete
local Plastic = Enum.Material.SmoothPlastic

-- Block centred at (x, y, z), size (sx, sy, sz); optional rotation in degrees.
local function B(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material,
	rx: number?,
	ry: number?,
	rz: number?
): Piece
	local piece: Piece = {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
	}
	if rx or ry or rz then
		piece.Rotation = Vector3.new(rx or 0, ry or 0, rz or 0)
	end
	return piece
end

-- Standing cylinder (axis up): diameter d, height h, centre y.
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along X, optionally turned about the vertical axis.
local function Cx(
	x: number,
	y: number,
	z: number,
	d: number,
	len: number,
	color: Color3,
	mat: Enum.Material,
	ry: number?
): Piece
	local piece: Piece = {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
	}
	if ry then
		piece.Rotation = Vector3.new(0, ry, 0)
	end
	return piece
end

local function Ball(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material,
	ry: number?
): Piece
	local piece: Piece = {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
	if ry then
		piece.Rotation = Vector3.new(0, ry, 0)
	end
	return piece
end

local theme: DecorTypes.Theme = {
	Key = "Beanstalk",
	Name = "Beanstalk and Stone Circle",
	Area = Vector2.new(180, 130),
	Shiba = { Position = Vector2.new(28, -24), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-34, 48),
		Vector2.new(6, 34),
		Vector2.new(48, 18),
		Vector2.new(28, -2),
		Vector2.new(-18, -8),
		Vector2.new(-50, -26),
		Vector2.new(-30, -48),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(10, -14),
	AutoPad = Vector2.new(10, -26),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Giant's Meadow",
			Description = "A wide green meadow with a slate plaza under the Giant Shiba, a ring of bare earth for the stones and a dark patch where the beanstalk will grow.",
			Pad = Vector2.new(8, 57),
			PriceSeconds = 62,
			Pieces = {
				B(0, 0.15, 0, 180, 0.3, 130, GRASS, Grass),
				B(28, 0.4, -24, 28, 0.2, 28, STONE, Slate),
				B(28, 0.49, -24, 20, 0.2, 20, LSTONE, Slate),
				Ball(-52, 0.33, 28, 46, 0.5, 46, DIRT, Ground),
				Ball(-52, 0.38, 28, 30, 0.4, 30, MOSS, Grass),
				Ball(62, 0.33, -44, 34, 0.5, 34, DDIRT, Ground),
				Ball(-10, 0.33, -52, 30, 0.5, 16, GRASS2, Grass),
				Ball(60, 0.33, 30, 34, 0.5, 20, GRASS2, Grass),
				Ball(-26, 0.33, 40, 26, 0.5, 14, GRASS2, Grass),
			},
		},
		-- 2
		{
			Id = "Signpost",
			Name = "Giant Signpost",
			Description = "A tall wooden signboard on two posts that warns every traveller about the GIANTS ahead.",
			Pad = Vector2.new(14, 46),
			PriceSeconds = 71,
			Pieces = {
				B(7.2, 0.5, 52, 3, 1, 3, STONE, Cobble),
				B(20.8, 0.5, 52, 3, 1, 3, STONE, Cobble),
				Cy(7.2, 6, 52, 1.6, 11, DWOOD, Wood),
				Cy(20.8, 6, 52, 1.6, 11, DWOOD, Wood),
				B(14, 9.6, 52, 17, 6, 1.6, WOOD, Planks),
				B(14, 13, 52, 18.4, 1, 2, DWOOD, Wood),
				B(11, 4.6, 52, 8, 2.6, 0.8, WOOD, Planks),
			},
		},
		-- 3
		{
			Id = "FieldWall",
			Name = "Field Wall",
			Description = "A mossy drystone wall with a gate standing open into the giant's pasture.",
			Pad = Vector2.new(70, 50),
			PriceSeconds = 82,
			Pieces = {
				B(61, 1.6, 58, 12, 3.2, 2.6, STONE, Cobble),
				B(83, 1.6, 58, 10, 3.2, 2.6, STONE, Cobble),
				B(86.7, 1.6, 51, 2.6, 3.2, 12, STONE, Cobble),
				B(68.2, 2.8, 58, 2.4, 5.6, 2.4, DSTONE, Granite),
				B(77.6, 2.8, 58, 2.4, 5.6, 2.4, DSTONE, Granite),
				B(71, 3.6, 56.6, 5.2, 3.4, 0.5, WOOD, Planks, 0, 50, 0),
				B(61, 3.5, 58, 12.6, 0.6, 3.2, LSTONE, Granite),
				B(83, 3.5, 58, 10.6, 0.6, 3.2, LSTONE, Granite),
				B(86.7, 3.5, 51, 3.2, 0.6, 12.6, LSTONE, Granite),
			},
		},
		-- 4
		{
			Id = "Boulders",
			Name = "Mossy Boulders",
			Description = "A tumble of big grey boulders, one wearing a green moss cap.",
			Pad = Vector2.new(-80, 45),
			PriceSeconds = 94,
			Pieces = {
				Ball(-84, 3.2, 57, 9, 6.4, 8, STONE, Rock),
				Ball(-76, 2.4, 54, 6.4, 4.8, 6, DSTONE, Rock),
				Ball(-80, 2, 60, 7, 4, 5.6, STONE, Rock),
				Ball(-72, 1.5, 60, 4.4, 3, 4, LSTONE, Rock),
				Ball(-86, 1.8, 50, 5, 3.6, 4.4, DSTONE, Rock),
				Ball(-84, 6.1, 57, 6, 2.4, 5.2, MOSS, Grass),
				Ball(-70, 0.8, 53.6, 2.4, 1.6, 2.2, STONE, Rock),
			},
		},
		-- 5
		{
			Id = "Daisies",
			Name = "Giant Daisies",
			Description = "Three daisies as tall as houses, white petals around a golden eye.",
			Pad = Vector2.new(74, 33),
			PriceSeconds = 108,
			Pieces = {
				Cy(72, 5, 40, 0.9, 10, GRASS2, Grass),
				Ball(72, 10.6, 40, 8, 1.4, 8, WHITE, Plastic),
				Ball(72, 11.2, 40, 3.6, 1.6, 3.6, GOLD, Plastic),
				Cy(80, 6, 46, 0.9, 12, GRASS2, Grass),
				Ball(80, 12.6, 46, 8, 1.4, 8, WHITE, Plastic),
				Ball(80, 13.2, 46, 3.6, 1.6, 3.6, GOLD, Plastic),
				Cy(66, 4, 46, 0.9, 8, GRASS2, Grass),
				Ball(66, 8.6, 46, 8, 1.4, 8, WHITE, Plastic),
				Ball(66, 9.2, 46, 3.6, 1.6, 3.6, GOLD, Plastic),
				Ball(74.4, 1.4, 40.6, 3.6, 1, 1.4, GRASS2, Grass),
				Ball(78, 1.4, 45.4, 3.6, 1, 1.4, GRASS2, Grass),
			},
		},
		-- 6
		{
			Id = "HayBales",
			Name = "Hay Bales",
			Description = "Round and square hay bales piled by the barn with a pitchfork leaning on them.",
			Pad = Vector2.new(66, -16),
			PriceSeconds = 125,
			Pieces = {
				Cx(74, 3, -12, 6, 8, HAY, Fabric),
				Cx(82, 3, -12, 6, 8, HAY, Fabric),
				Cx(78, 8.6, -12.2, 6, 8, HAY, Fabric),
				B(76, 1.7, -20, 5, 3.4, 3.6, HAY, Fabric),
				B(80.6, 1.7, -19.4, 5, 3.4, 3.6, HAY, Fabric, 0, 20, 0),
				Cy(86, 5.4, -17, 0.5, 10.8, DWOOD, Wood),
				B(86, 10.8, -17, 2.4, 0.4, 0.4, IRON, Metal),
			},
		},
		-- 7
		{
			Id = "Beans",
			Name = "Magic Beans",
			Description = "A sack of magic beans spilled across the grass, one of them already sprouting.",
			Pad = Vector2.new(44, -25),
			PriceSeconds = 143,
			Pieces = {
				Ball(40, 2.4, -14, 6, 4.8, 5, TAN, Fabric),
				Ball(40, 4.9, -14, 2.2, 1.4, 2.2, BROWN, Fabric),
				Ball(45, 0.8, -11, 2.8, 1.6, 1.8, BEAN, Plastic),
				Ball(47.6, 0.8, -13, 2.8, 1.6, 1.8, PBEAN, Plastic),
				Ball(44.4, 0.8, -15.8, 2.8, 1.6, 1.8, LBEAN, Plastic),
				Ball(42.6, 0.8, -9.6, 2.8, 1.6, 1.8, PBEAN, Plastic),
				Ball(37.6, 0.8, -9.4, 2.8, 1.6, 1.8, BEAN, Plastic),
				Ball(49.6, 0.8, -9.8, 2.8, 1.6, 1.8, LBEAN, Plastic),
				Ball(43.4, 0.8, -18.8, 2.8, 1.6, 1.8, BEAN, Plastic),
				Cy(48, 2.4, -17.4, 0.6, 4.8, BEAN, Grass),
				Ball(49.6, 5, -17.4, 3, 0.6, 1.6, LBEAN, Grass),
				Ball(46.4, 4.2, -17.4, 3, 0.6, 1.6, LBEAN, Grass),
			},
		},
		-- 8
		{
			Id = "Cottage",
			Name = "Jack's Cottage",
			Description = "A small cream cottage with a thatched roof, green shutters and a stone chimney.",
			Pad = Vector2.new(-72, 6),
			PriceSeconds = 165,
			Pieces = {
				B(-72, 3.9, -6, 13.6, 5.8, 10.6, CREAM, Concrete),
				B(-72, 0.5, -6, 14.6, 1, 11.6, STONE, Cobble),
				B(-72, 9, -2.8, 15.6, 0.8, 7.8, THATCH, Fabric, 35, 0, 0),
				B(-72, 9, -9.2, 15.6, 0.8, 7.8, THATCH, Fabric, -35, 0, 0),
				B(-67, 10.6, -9, 2.2, 6.4, 2.2, STONE, Cobble),
				B(-72, 3.2, -0.45, 2.6, 4.2, 0.5, WOOD, Planks),
				B(-76.5, 4.6, -0.45, 2.2, 2.2, 0.5, SKY, Plastic),
				B(-67.5, 4.6, -0.45, 2.2, 2.2, 0.5, SKY, Plastic),
				B(-72, 0.4, 1.2, 4, 0.8, 2.4, STONE, Slate),
			},
		},
		-- 9
		{
			Id = "OakTree",
			Name = "Old Oak",
			Description = "A broad old oak with a thick trunk, wide roots and a crown of layered green leaves.",
			Pad = Vector2.new(-70, -30),
			PriceSeconds = 190,
			Pieces = {
				Cy(-80, 5, -30, 3.6, 10, DWOOD, Wood),
				Ball(-80, 0.7, -30, 6, 1.4, 6, DWOOD, Wood),
				Ball(-80, 15, -30, 14, 9, 13, GRASS2, Grass),
				Ball(-84, 13, -33, 10, 7, 9, GRASS, Grass),
				Ball(-76, 13.5, -27, 10, 7, 9, GRASS2, Grass),
				Ball(-80, 19.5, -30, 9, 6, 8.4, GRASS, Grass),
				Ball(-85, 14.2, -27, 8, 6, 7.4, GRASS2, Grass),
			},
		},
		-- 10
		{
			Id = "Well",
			Name = "Stone Well",
			Description = "A round stone well with a wooden crank, a bucket on a rope and a little red roof.",
			Pad = Vector2.new(-26, -21),
			PriceSeconds = 218,
			Pieces = {
				Cy(-26, 2.4, -30, 8.6, 4.8, STONE, Cobble),
				Cy(-26, 4.9, -30, 6.4, 0.5, WATER, Plastic),
				B(-29.6, 8.4, -30, 0.8, 7.2, 0.8, WOOD, Wood),
				B(-22.4, 8.4, -30, 0.8, 7.2, 0.8, WOOD, Wood),
				B(-26, 12.6, -28.2, 9, 0.6, 4.6, ROOFRED, Wood, 35, 0, 0),
				B(-26, 12.6, -31.8, 9, 0.6, 4.6, ROOFRED, Wood, -35, 0, 0),
				Cx(-26, 10.4, -30, 0.7, 7.6, WOOD, Wood),
				Cy(-26, 6.6, -30, 1.8, 1.6, DWOOD, Wood),
				Cy(-26, 8.6, -30, 0.25, 3, TAN, Fabric),
			},
		},
		-- 11
		{
			Id = "Cow",
			Name = "Daisy the Cow",
			Description = "A fat brown and cream cow chewing grass, the one Jack is supposed to sell.",
			Pad = Vector2.new(-6, -43),
			PriceSeconds = 251,
			Pieces = {
				B(-6, 6.4, -34, 11, 5.4, 5.6, CREAM, Fabric),
				B(-8, 9.2, -34, 3.4, 0.4, 3.6, COWBROWN, Fabric),
				B(-3.4, 6.4, -31.1, 3, 3, 0.4, COWBROWN, Fabric),
				B(1.4, 7.6, -34, 3.6, 3.4, 3.4, CREAM, Fabric),
				B(3.4, 6.8, -34, 1.4, 1.8, 2.6, PINK, Fabric),
				B(1.6, 9.6, -35.4, 0.6, 1.4, 0.6, WHITE, Plastic),
				B(1.6, 9.6, -32.6, 0.6, 1.4, 0.6, WHITE, Plastic),
				B(-10.2, 2.4, -36.4, 1.5, 4.8, 1.5, CREAM, Fabric),
				B(-10.2, 2.4, -31.6, 1.5, 4.8, 1.5, CREAM, Fabric),
				B(-1.8, 2.4, -36.4, 1.5, 4.8, 1.5, CREAM, Fabric),
				B(-1.8, 2.4, -31.6, 1.5, 4.8, 1.5, CREAM, Fabric),
				B(-12, 6.4, -34, 0.5, 4.4, 0.5, COWBROWN, Fabric),
			},
		},
		-- 12
		{
			Id = "Footprints",
			Name = "Giant Footprints",
			Description = "A trail of three enormous muddy footprints, each with five toes, stomping across the meadow.",
			Pad = Vector2.new(17, 14),
			PriceSeconds = 288,
			Pieces = {
				Ball(12, 0.33, 8, 5.6, 0.5, 9.4, DDIRT, Mud),
				Ball(12, 0.33, 13.6, 5.2, 0.5, 3, DDIRT, Mud),
				Ball(10.4, 0.33, 15.2, 2.2, 0.5, 2.2, DDIRT, Mud),
				Ball(13.8, 0.33, 15.2, 3.4, 0.5, 2.2, DDIRT, Mud),
				Ball(22, 0.33, 22, 5.6, 0.5, 9.4, DDIRT, Mud),
				Ball(22, 0.33, 27.6, 5.2, 0.5, 3, DDIRT, Mud),
				Ball(20.4, 0.33, 29.2, 2.2, 0.5, 2.2, DDIRT, Mud),
				Ball(23.8, 0.33, 29.2, 3.4, 0.5, 2.2, DDIRT, Mud),
				Ball(32, 0.33, 36, 5.6, 0.5, 9.4, DDIRT, Mud),
				Ball(32, 0.33, 41.6, 5.2, 0.5, 3, DDIRT, Mud),
				Ball(30.4, 0.33, 43.2, 2.2, 0.5, 2.2, DDIRT, Mud),
				Ball(33.8, 0.33, 43.2, 3.4, 0.5, 2.2, DDIRT, Mud),
			},
		},
		-- 13
		{
			Id = "Toadstools",
			Name = "Toadstool Ring",
			Description = "Three giant red toadstools with white spots growing in a fairy ring.",
			Pad = Vector2.new(-14, 8),
			PriceSeconds = 332,
			Pieces = {
				Cy(-22, 3, 20, 3.2, 6, CREAM, Concrete),
				Ball(-22, 7, 20, 11, 6, 11, RED, Plastic),
				Cy(-14, 2.2, 16, 2.4, 4.4, CREAM, Concrete),
				Ball(-14, 5.6, 16, 8, 4.4, 8, RED, Plastic),
				Cy(-17, 1.6, 24, 1.8, 3.2, CREAM, Concrete),
				Ball(-17, 4.2, 24, 6, 3.4, 6, RED, Plastic),
				Ball(-23.5, 9.4, 19, 1.8, 0.8, 1.8, WHITE, Plastic),
				Ball(-20.5, 9.6, 21, 1.6, 0.8, 1.6, WHITE, Plastic),
				Ball(-14.5, 7.6, 16, 1.4, 0.6, 1.4, WHITE, Plastic),
			},
		},
		-- 14
		{
			Id = "Scarecrow",
			Name = "Scarecrow",
			Description = "A blue-shirted scarecrow in a floppy hat with a crow sitting on its arm.",
			Pad = Vector2.new(76, -26),
			PriceSeconds = 381,
			Pieces = {
				Cy(82, 7, -28, 1.2, 14, DWOOD, Wood),
				Cx(82, 9.4, -28, 1, 12, DWOOD, Wood),
				B(82, 8.4, -28, 4, 4.6, 2.2, SLATEBLUE, Fabric),
				Ball(82, 12.6, -28, 3.8, 3.8, 3.8, TAN, Fabric),
				Cy(82, 14.2, -28, 5.4, 0.4, DWOOD, Wood),
				Cy(82, 15.4, -28, 3, 2.2, DWOOD, Wood),
				Ball(76.6, 9.4, -28, 1.8, 1.6, 1.8, HAY, Fabric),
				Ball(87.4, 9.4, -28, 1.8, 1.6, 1.8, HAY, Fabric),
				Ball(82, 5.6, -28, 4.4, 2, 2.8, HAY, Fabric),
				Ball(86.4, 10.8, -28, 1.6, 1.4, 2.4, BLACK, Plastic),
				Ball(82, 0.5, -28, 5, 1, 5, DIRT, Ground),
			},
		},
		-- 15
		{
			Id = "Boots",
			Name = "Giant Boots",
			Description = "A pair of enormous leather boots the giant kicked off, toes pointing at the Shiba.",
			Pad = Vector2.new(-4, -12),
			PriceSeconds = 439,
			Pieces = {
				B(-5, 0.5, -27.5, 13.6, 1, 6.2, DWOOD, Wood),
				B(-5, 3.1, -27.5, 13, 5.2, 5.8, BROWN, Fabric),
				B(-8, 10.4, -27.5, 6, 9, 5.4, BROWN, Fabric),
				B(-8, 15, -27.5, 6.8, 1.4, 6.2, LWOOD, Fabric),
				B(-3.5, 0.5, -20.5, 13.6, 1, 6.2, DWOOD, Wood),
				B(-3.5, 3.1, -20.5, 13, 5.2, 5.8, BROWN, Fabric),
				B(-6.5, 10.4, -20.5, 6, 9, 5.4, BROWN, Fabric),
				B(-6.5, 15, -20.5, 6.8, 1.4, 6.2, LWOOD, Fabric),
			},
		},
		-- 16
		{
			Id = "Cauldron",
			Name = "Giant Cauldron",
			Description = "A huge iron cauldron of bubbling green soup over a log fire, with a ladle sticking out.",
			Pad = Vector2.new(14, -38),
			PriceSeconds = 504,
			Pieces = {
				Cy(14, 5.5, -48, 13, 8, IRON, Metal),
				Cy(14, 9.4, -48, 14.2, 1, DSTONE, Metal),
				Cy(14, 9.2, -48, 12, 0.4, LBEAN, Plastic),
				B(9.4, 0.9, -52, 1.8, 1.8, 1.8, IRON, Metal),
				B(18.6, 0.9, -52, 1.8, 1.8, 1.8, IRON, Metal),
				B(14, 0.9, -43.2, 1.8, 1.8, 1.8, IRON, Metal),
				Cx(14, 0.8, -47, 1.6, 10, DWOOD, Wood),
				Cx(14, 0.8, -47, 1.6, 10, WOOD, Wood, 60),
				Cx(14, 0.8, -47, 1.6, 10, DWOOD, Wood, -60),
				B(18.6, 12.2, -45, 0.5, 6.4, 0.5, WOOD, Wood, 0, 0, -25),
				Ball(19.6, 9.8, -45, 2, 1, 2, IRON, Metal),
			},
		},
		-- 17
		{
			Id = "Harp",
			Name = "Golden Harp",
			Description = "The giant's magic golden harp, its strings shining in the sun, on a little stone stand.",
			Pad = Vector2.new(-58, -12),
			PriceSeconds = 580,
			Pieces = {
				B(-65, 0.3, -20, 10, 0.6, 6, STONE, Slate),
				B(-66, 0.9, -20, 8, 1.2, 4.4, DGOLD, Metal),
				B(-69, 7.5, -20, 1.4, 13, 1.6, GOLD, Metal),
				B(-65.6, 13.4, -20, 8, 1.2, 1.6, GOLD, Metal, 0, 0, -12),
				B(-61.4, 7, -20, 1.8, 12.6, 2.2, DGOLD, Metal, 0, 0, -8),
				B(-66.8, 7.4, -20, 0.15, 10, 0.15, WHITE, Plastic),
				B(-65.2, 7.4, -20, 0.15, 10, 0.15, WHITE, Plastic),
				B(-63.6, 7.2, -20, 0.15, 10, 0.15, WHITE, Plastic),
				Ball(-69, 14.4, -20, 2, 2, 2, GOLD, Metal),
			},
		},
		-- 18
		{
			Id = "GoldHoard",
			Name = "Gold Hoard",
			Description = "A heap of gold coins and jewels around an open treasure chest.",
			Pad = Vector2.new(74, -3),
			PriceSeconds = 667,
			Pieces = {
				Ball(82, 2.8, 6, 13, 5.6, 11, GOLD, Metal),
				Ball(79, 2, 2, 8, 4, 7, LGOLD, Metal),
				Ball(86, 1.8, 9, 7, 3.6, 6, GOLD, Metal),
				B(76, 2.2, 10.5, 5.6, 4, 3.6, WOOD, Wood),
				B(76, 5.4, 12.6, 5.6, 0.8, 3, DWOOD, Wood, -65, 0, 0),
				Cy(84.6, 5.6, 5, 3.4, 0.6, GOLD, Metal),
				Cy(79.6, 5.8, 4.8, 3.4, 0.6, LGOLD, Metal),
				Ball(84.6, 5.8, 9.2, 2.2, 2.2, 2.2, RED, Plastic),
				Ball(79.4, 6.4, 8.6, 2, 2, 2, WATER, Plastic),
				Ball(82.4, 6.4, 6, 2, 2, 2, LBEAN, Plastic),
			},
		},
		-- 19
		{
			Id = "Dolmen",
			Name = "Dolmen",
			Description = "Three grey stones holding up a giant capstone: an ancient stone doorway grown over with moss.",
			Pad = Vector2.new(36, 46),
			PriceSeconds = 767,
			Pieces = {
				B(36, 0.35, 54, 18, 0.5, 12, DSTONE, Slate),
				B(30, 5.8, 54, 3.6, 11.6, 5.6, STONE, Granite),
				B(42, 5.8, 54, 3.6, 11.6, 5.6, STONE, Granite),
				B(36, 4.6, 56.6, 8, 9.2, 2.6, DSTONE, Granite),
				B(36, 12.9, 54, 16, 2.8, 8.4, LSTONE, Granite, 0, 0, -3),
				B(36, 14.4, 54, 9, 0.6, 5, MOSS, Grass),
				B(26.4, 1.6, 50.4, 2.4, 3.2, 2.2, STONE, Granite),
				B(45.6, 1.2, 57.6, 2.4, 2.4, 2.2, STONE, Granite),
			},
		},
		-- 20
		{
			Id = "Obelisk",
			Name = "Rune Obelisk",
			Description = "A tall tapering obelisk carved with pale blue runes and a golden tip.",
			Pad = Vector2.new(-38, 14),
			PriceSeconds = 882,
			Pieces = {
				B(-38, 0.8, 4, 10, 1.6, 10, STONE, Granite),
				B(-38, 2.4, 4, 7.6, 1.6, 7.6, LSTONE, Granite),
				B(-38, 15, 4, 5, 24, 5, DSTONE, Granite),
				B(-38, 8, 4, 5.4, 0.8, 5.4, LBEAN, Slate),
				B(-38, 14, 4, 5.3, 0.7, 5.3, WATER, Slate),
				B(-38, 20, 4, 5.2, 0.7, 5.2, LBEAN, Slate),
				B(-38, 28.2, 4, 3.6, 2.8, 3.6, GOLD, Metal),
			},
		},
		-- 21
		{
			Id = "Table",
			Name = "Giant Table",
			Description = "A table big enough for a giant's supper: a plate, a wedge of cheese, a goblet and a fresh loaf.",
			Pad = Vector2.new(-62, -41),
			PriceSeconds = 1015,
			Pieces = {
				B(-62, 13.2, -52, 24, 1.6, 14, WOOD, Planks),
				B(-72.4, 6.2, -57.2, 2.4, 12.4, 2.4, DWOOD, Wood),
				B(-51.6, 6.2, -57.2, 2.4, 12.4, 2.4, DWOOD, Wood),
				B(-72.4, 6.2, -46.8, 2.4, 12.4, 2.4, DWOOD, Wood),
				B(-51.6, 6.2, -46.8, 2.4, 12.4, 2.4, DWOOD, Wood),
				B(-62, 3.4, -46.8, 18, 1.2, 1.2, DWOOD, Wood),
				B(-62, 3.4, -57.2, 18, 1.2, 1.2, DWOOD, Wood),
				B(-62, 14.2, -52, 24.4, 0.2, 5, RED, Fabric),
				B(-66, 14.6, -52, 7, 0.5, 7, WHITE, Plastic),
				B(-66, 16.2, -52, 4, 3, 3.6, GOLD, Plastic),
				Cy(-55, 16.2, -50, 2.4, 3.4, DGOLD, Metal),
				Ball(-58.4, 15.6, -55, 5, 2.8, 3, TAN, Fabric),
			},
		},
		-- 22
		{
			Id = "StandingStones",
			Name = "Standing Stones",
			Description = "A circle of eight huge grey standing stones, two pairs capped with lintels, around a rune slab.",
			Pad = Vector2.new(-52, 28),
			RewardMult = 1.25,
			PriceSeconds = 1167,
			Pieces = {
				B(-38.14, 6.5, 33.74, 5, 13, 3.4, STONE, Granite, 0, -112.5, 0),
				B(-46.26, 7, 41.86, 5, 14, 3.4, DSTONE, Granite, 0, -157.5, 0),
				B(-57.74, 7, 41.86, 5, 14, 3.4, STONE, Granite, 0, 157.5, 0),
				B(-65.86, 7, 33.74, 5, 14, 3.4, DSTONE, Granite, 0, 112.5, 0),
				B(-65.86, 7.5, 22.26, 5, 15, 3.4, STONE, Granite, 0, 67.5, 0),
				B(-57.74, 6.5, 14.14, 5, 13, 3.4, DSTONE, Granite, 0, 22.5, 0),
				B(-46.26, 7, 14.14, 5, 14, 3.4, STONE, Granite, 0, -22.5, 0),
				B(-38.14, 7, 22.26, 5, 14, 3.4, DSTONE, Granite, 0, -67.5, 0),
				B(-61.8, 14.9, 37.8, 13.6, 1.8, 3.4, LSTONE, Granite, 0, 135, 0),
				B(-42.2, 14.9, 18.2, 13.6, 1.8, 3.4, LSTONE, Granite, 0, -45, 0),
				B(-52, 0.5, 28, 9, 0.2, 9, DSTONE, Slate),
			},
		},
		-- 23
		{
			Id = "GiantStool",
			Name = "Giant Stool",
			Description = "A three-legged wooden stool with a fat red cushion, tall enough to seat a giant.",
			Pad = Vector2.new(58, 24),
			PriceSeconds = 1343,
			Pieces = {
				B(70, 14.6, 24, 19, 2.8, 19, WOOD, Wood),
				B(70, 6.6, 30.8, 3.2, 13.2, 3.2, DWOOD, Wood),
				B(64.1, 6.6, 20.6, 3.2, 13.2, 3.2, DWOOD, Wood),
				B(75.9, 6.6, 20.6, 3.2, 13.2, 3.2, DWOOD, Wood),
				Ball(70, 16.6, 24, 12, 2, 12, RED, Fabric),
			},
		},
		-- 24
		{
			Id = "GiantClub",
			Name = "Giant Club",
			Description = "A gigantic spiked wooden club stuck in the earth, with iron bands and studs, still cracking the ground around it.",
			Pad = Vector2.new(62, 10),
			RewardMult = 1.4,
			PriceSeconds = 1544,
			Pieces = {
				Ball(62, 0.33, -4, 18, 0.5, 18, DDIRT, Ground),
				Ball(57, 1.2, -1, 4, 2.4, 3.6, STONE, Rock),
				Ball(67, 1, -7, 3.6, 2, 3.4, STONE, Rock),
				Cy(62, 7, -4, 3, 14, WOOD, Wood),
				Cy(62, 18, -4, 5.4, 8, WOOD, Wood),
				Cy(62, 26, -4, 8, 8, WOOD, Wood),
				Cy(62, 33, -4, 9.6, 6, DWOOD, Wood),
				Ball(62, 37.2, -4, 8, 4, 8, WOOD, Wood),
				Cy(62, 22, -4, 6.4, 1, IRON, Metal),
				Cy(62, 29.5, -4, 9.4, 1, IRON, Metal),
				Ball(66.4, 31, -4, 1.6, 1.6, 1.6, IRON, Metal),
				Ball(57.6, 31, -4, 1.6, 1.6, 1.6, IRON, Metal),
				Ball(62, 31, 0.4, 1.6, 1.6, 1.6, IRON, Metal),
				Ball(62, 31, -8.4, 1.6, 1.6, 1.6, IRON, Metal),
			},
		},
		-- 25
		{
			Id = "Roots",
			Name = "Beanstalk Roots",
			Description = "A mound of churned earth where the bean has taken hold, with a fat green bulb and six thick roots crawling away.",
			Pad = Vector2.new(62, -22),
			PriceSeconds = 1775,
			Pieces = {
				Ball(62, 2.4, -44, 20, 4.8, 20, DIRT, Ground),
				Ball(62, 4.4, -44, 10, 8.8, 10, BEAN, Grass),
				Ball(70.21, 1.9, -46.2, 13, 3.6, 4, DBEAN, Grass, 15),
				Ball(64.2, 1.9, -52.21, 13, 3.6, 4, DBEAN, Grass, 75),
				Ball(55.99, 1.9, -50.01, 13, 3.6, 4, DBEAN, Grass, 135),
				Ball(53.79, 1.9, -41.8, 13, 3.6, 4, DBEAN, Grass, 195),
				Ball(59.8, 1.9, -35.79, 13, 3.6, 4, DBEAN, Grass, 255),
				Ball(68.01, 1.9, -37.99, 13, 3.6, 4, DBEAN, Grass, 315),
				Ball(51, 1.2, -50, 3.6, 2.4, 3.2, STONE, Rock),
				Ball(73, 1, -50, 3.2, 2, 3, STONE, Rock),
			},
		},
		-- 26
		{
			Id = "GooseCoop",
			Name = "Goose Coop",
			Description = "A little red coop with a straw yard and two ordinary white geese, who have no idea what lives at the top of the stalk.",
			Pad = Vector2.new(0, 28),
			PriceSeconds = 2041,
			Pieces = {
				Ball(0, 0.33, 16, 16, 0.5, 13, HAY, Grass),
				B(-2.6, 3.2, 12.4, 6, 5.4, 5, RED, Wood),
				B(-2.6, 7, 14.2, 7, 0.6, 3.6, DWOOD, Wood, 30, 0, 0),
				B(-2.6, 7, 10.6, 7, 0.6, 3.6, DWOOD, Wood, -30, 0, 0),
				B(-2.6, 2.4, 14.95, 1.6, 2.8, 0.4, DWOOD, Wood),
				B(-6.4, 2.2, 21.2, 0.6, 4.4, 0.6, WOOD, Wood),
				B(6.4, 2.2, 21.2, 0.6, 4.4, 0.6, WOOD, Wood),
				B(0, 3.2, 21.2, 13.4, 0.4, 0.4, WOOD, Wood),
				Ball(2, 2.2, 17, 3.6, 2.8, 2.2, WHITE, Plastic),
				B(3.2, 3.9, 17, 0.7, 2.6, 0.7, WHITE, Plastic),
				Ball(3.4, 5.4, 17, 1.4, 1.2, 1.2, WHITE, Plastic),
				Ball(-3.4, 2.2, 18.4, 3.6, 2.8, 2.2, WHITE, Plastic),
				B(-4.6, 3.9, 18.4, 0.7, 2.6, 0.7, WHITE, Plastic),
				Ball(-4.8, 5.4, 18.4, 1.4, 1.2, 1.2, WHITE, Plastic),
			},
		},
		-- 27
		{
			Id = "Stem",
			Name = "Beanstalk Stem",
			Description = "The beanstalk itself: a thick green stem that twists up 74 studs into the clouds, wrapped in a curling tendril.",
			Pad = Vector2.new(82, -46),
			PriceSeconds = 2347,
			Pieces = {
				Cy(62.9, 3.1, -44, 8.4, 6.2, BEAN, Grass),
				Cy(62.4, 9.3, -43.2, 8, 6.2, DBEAN, Grass),
				Cy(61.5, 15.5, -43, 7.6, 6.2, BEAN, Grass),
				Cy(60.9, 21.7, -43.8, 7.2, 6.2, DBEAN, Grass),
				Cy(61.2, 27.9, -44.9, 6.8, 6.2, BEAN, Grass),
				Cy(62, 34.1, -45.4, 6.4, 6.2, DBEAN, Grass),
				Cy(62.9, 40.3, -44.9, 6, 6.2, BEAN, Grass),
				Cy(63.4, 46.5, -43.8, 5.6, 6.2, DBEAN, Grass),
				Cy(63.1, 52.7, -43, 5.2, 6.2, BEAN, Grass),
				Cy(62.4, 58.9, -43.2, 4.8, 6.2, DBEAN, Grass),
				Cy(61.7, 65.1, -44.1, 4.4, 6.2, BEAN, Grass),
				Cy(61.3, 71.3, -45, 4, 6.2, DBEAN, Grass),
			},
		},
		-- 28
		{
			Id = "Leaves",
			Name = "Beanstalk Leaves",
			Description = "Ten huge veined leaves spiralling up the stalk, big enough to walk on, with two fat bean pods hanging between them.",
			Pad = Vector2.new(42, -54),
			RewardMult = 1.5,
			PriceSeconds = 2699,
			Pieces = {
				B(71.33, 15.93, -47.4, 14, 0.8, 7.7, BEAN, Grass, 0, 20, 16),
				B(52.99, 22.07, -49.2, 15, 0.8, 8.25, LBEAN, Grass, 0, 150, 16),
				B(62.95, 28.21, -33.15, 16, 0.8, 8.8, BEAN, Grass, 0, 275, 16),
				B(67.45, 34.21, -53.43, 16, 0.8, 8.8, LBEAN, Grass, 0, 60, 16),
				B(51.32, 40.34, -40.11, 17, 0.8, 9.35, BEAN, Grass, 0, 200, 16),
				B(70.34, 46.21, -37, 16, 0.8, 8.8, LBEAN, Grass, 0, 320, 16),
				B(58.44, 52.07, -53.78, 15, 0.8, 8.25, BEAN, Grass, 0, 110, 16),
				B(56.31, 57.93, -35.87, 14, 0.8, 7.7, LBEAN, Grass, 0, 235, 16),
				B(71.13, 63.79, -46.45, 13, 0.8, 7.15, BEAN, Grass, 0, 15, 16),
				B(55.5, 68.52, -49.46, 11, 0.8, 6.05, LBEAN, Grass, 0, 140, 16),
				Ball(56, 33, -47.4, 3.2, 8, 3.2, DBEAN, Grass),
				Ball(68, 47, -42, 3.2, 8, 3.2, PBEAN, Grass),
			},
		},
		-- 29
		{
			Id = "CloudCastle",
			Name = "Cloud Castle",
			Description = "The giant's castle floating on a cloud high above the meadow: a cream keep, four round towers and blue roofs.",
			Pad = Vector2.new(28, -38),
			PriceSeconds = 3104,
			Pieces = {
				Ball(26, 55, -50, 34, 9, 24, WHITE, Plastic),
				Ball(15, 52.5, -46, 14, 7, 12, WHITE, Plastic),
				Ball(36, 52.8, -54, 16, 7, 12, WHITE, Plastic),
				B(26, 66, -51, 12, 12, 10, CASTLE, Concrete),
				B(15, 67, -44, 5, 16, 5, CASTLE, Concrete),
				B(37, 67, -44, 5, 16, 5, CASTLE, Concrete),
				B(15, 67, -58, 5, 16, 5, CASTLE, Concrete),
				B(37, 67, -58, 5, 16, 5, CASTLE, Concrete),
				B(15, 77.5, -44, 6, 5, 6, SLATEBLUE, Concrete),
				B(37, 77.5, -44, 6, 5, 6, SLATEBLUE, Concrete),
				B(15, 77.5, -58, 6, 5, 6, SLATEBLUE, Concrete),
				B(37, 77.5, -58, 6, 5, 6, SLATEBLUE, Concrete),
				B(26, 74.5, -51, 12.6, 4, 10.6, SLATEBLUE, Concrete),
				B(26, 62.4, -45.4, 3.4, 4.4, 0.5, DWOOD, Wood),
			},
		},
		-- 30
		{
			Id = "Nest",
			Name = "Golden Goose Nest",
			Description = "A great woven nest on top of the beanstalk where the golden goose sits proudly on her golden eggs.",
			Pad = Vector2.new(74, -60),
			RewardMult = 1.9,
			PriceSeconds = 3570,
			Pieces = {
				Ball(62, 76, -44, 18, 5, 18, DWOOD, Wood),
				B(69, 77, -44, 7, 1.1, 1.1, WOOD, Wood, 0, 90, 0),
				B(65.5, 77, -50.06, 7, 1.1, 1.1, WOOD, Wood, 0, 150, 0),
				B(58.5, 77, -50.06, 7, 1.1, 1.1, WOOD, Wood, 0, 210, 0),
				B(55, 77, -44, 7, 1.1, 1.1, WOOD, Wood, 0, 270, 0),
				B(58.5, 77, -37.94, 7, 1.1, 1.1, WOOD, Wood, 0, 330, 0),
				B(65.5, 77, -37.94, 7, 1.1, 1.1, WOOD, Wood, 0, 30, 0),
				Ball(60, 78.4, -40, 4, 5.2, 4, GOLD, Metal),
				Ball(64.5, 78, -39.5, 4, 5.2, 4, LGOLD, Metal),
				Ball(62, 82.2, -45, 9, 6.4, 5.4, GOLD, Metal),
				B(65.4, 85.6, -45, 1.6, 4.4, 1.6, GOLD, Metal),
				Ball(66.2, 88.4, -45, 3, 2.6, 2.6, GOLD, Metal),
				B(68.2, 88.2, -45, 1.8, 0.7, 1.1, ORANGE, Plastic),
				B(58.2, 82.6, -45, 3.4, 2.4, 1.2, DGOLD, Metal),
				B(62, 83, -48.2, 7, 3.2, 1.4, LGOLD, Metal, 0, 0, -10),
			},
		},
	},
}

return theme
