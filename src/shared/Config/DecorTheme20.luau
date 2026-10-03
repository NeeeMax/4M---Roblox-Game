--!strict
-- Theme of the Shiba of bay 20: Ice Palace (Config/DecorTypes -> Theme). 190 x 130: a frost palace in the back right with the Frost
-- Shiba standing in its forecourt inside a ring of aurora crystals, a frozen lake in the front right, an igloo village and a snowman
-- family on the left, a winding walkway between them. No glow: lamps, crystals and aurora are plain coloured blocks.
-- Stage frame: +X right, -Z deeper, +Z toward the road.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local SNOW = C(240, 246, 252)
local PALE = C(205, 235, 252)
local ICE = C(170, 225, 255)
local ICE_D = C(110, 170, 230)
local DEEP = C(70, 120, 200)
local STONE = C(130, 150, 178)
local DARK = C(50, 70, 100)
local CYAN = C(110, 230, 245)
local WOOD = C(130, 92, 62)
local WOOD_D = C(90, 62, 42)
local RED = C(205, 60, 60)
local GOLD = C(245, 205, 90)
local GREEN = C(80, 200, 150)
local PURPLE = C(170, 110, 230)
local BLACK = C(30, 36, 48)
local STEEL = C(176, 186, 200)
local TEAL = C(90, 200, 210)

local Ice = Enum.Material.Ice
local Glacier = Enum.Material.Glacier
local Snow = Enum.Material.Snow
local Rock = Enum.Material.Rock
local Slate = Enum.Material.Slate
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Metal = Enum.Material.Metal
local Fabric = Enum.Material.Fabric
local Plastic = Enum.Material.SmoothPlastic

-- Block centred at (x, y, z), size (sx, sy, sz), optional rotation in degrees (x, y, z).
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
		Offset = Vector3.new(x, y, z),
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
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
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
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
end

local function rot(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
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

-- A crystal of the halo around the Shiba: stands at (x, z) on the ground, `h` tall, leaning outward by `a` degrees along (ux, uz).
local function crystal(
	x: number,
	z: number,
	w: number,
	h: number,
	a: number,
	ux: number,
	uz: number,
	color: Color3
): Piece
	return B(x, h / 2, z, w, h, w, color, Ice, rot(a * uz, 0, -a * ux))
end

local function snowman3(x: number, z: number, d: number): Pieces
	return {
		Ball(x, d * 0.5, z, d, d * 0.86, d, SNOW, Snow),
		Ball(x, d * 1.2, z, d * 0.72, d * 0.66, d * 0.72, SNOW, Snow),
		Ball(x, d * 1.76, z, d * 0.52, d * 0.5, d * 0.52, SNOW, Snow),
	}
end

local theme: DecorTypes.Theme = {
	Key = "IcePalace",
	Name = "Ice Palace",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(6, -22), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-44, 50),
		Vector2.new(6, 32),
		Vector2.new(-38, 12),
		Vector2.new(-40, -16),
		Vector2.new(-24, -44),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(14, -34),
	AutoPad = Vector2.new(14, -10),
	Parts = {
		{
			Id = "Ground",
			Name = "Frozen Plain",
			Description = "Fresh snow, a big frozen lake in the front right and a pale ice forecourt before the palace.",
			Pad = Vector2.new(28, 61),
			PriceSeconds = 48,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, SNOW, Snow),
				B(64, 0.35, 28, 56, 0.2, 34, ICE, Ice),
				B(52, 0.35, 46, 32, 0.2, 10, ICE, Ice),
				B(86, 0.35, 12, 14, 0.2, 18, ICE_D, Ice),
				B(60, 0.3, -45, 50, 0.2, 38, PALE, Ice),
				B(30, 0.3, -46, 14, 0.2, 10, PALE, Ice),
			},
		},
		{
			Id = "Palace",
			Yaw = 5,
			Name = "Frost Palace",
			Description = "The ice palace itself: a great glacier hall with a crowned central keep and four slender corner towers.",
			Pad = Vector2.new(44, -30),
			PriceSeconds = 55,
			RewardMult = 1.25,
			Pieces = {
				B(67, 1, -47, 44, 2, 28, STONE, Rock),
				B(67, 8, -47, 34, 12, 20, ICE, Glacier),
				B(48, 5, -47, 6, 6, 10, DEEP, Ice),
				Cy(67, 19, -49, 14, 18, PALE, Ice),
				Ball(67, 29.5, -49, 12, 9, 12, DEEP, Ice),
				Cy(49, 12, -37, 7, 22, ICE, Ice),
				Cy(85, 12, -37, 7, 22, ICE, Ice),
				Cy(49, 12, -57, 7, 22, ICE, Ice),
				Cy(85, 12, -57, 7, 22, ICE, Ice),
				Ball(49, 24.5, -37, 8, 6, 8, DEEP, Ice),
				Ball(85, 24.5, -37, 8, 6, 8, DEEP, Ice),
				Ball(49, 24.5, -57, 8, 6, 8, DEEP, Ice),
				Ball(85, 24.5, -57, 8, 6, 8, DEEP, Ice),
			},
		},
		{
			Id = "Halo",
			Name = "Aurora Crystal Halo",
			Description = "A great ring of aurora crystals rising behind the Frost Shiba, leaning out like the petals of a flower.",
			Pad = Vector2.new(-1, -22),
			PriceSeconds = 63,
			RewardMult = 1.3,
			Pieces = {
				crystal(2.25, -36, 2.6, 12, 12, 0.26, -0.97, ICE),
				crystal(-3.32, -33.1, 2.6, 16, 12, -0.64, -0.77, CYAN),
				crystal(-7.14, -28.13, 2.6, 11, 12, -0.91, -0.42, ICE),
				crystal(-8.5, -22, 2.6, 18, 12, -1, 0, PURPLE),
				crystal(-7.14, -15.87, 2.6, 11, 12, -0.91, 0.42, ICE),
				crystal(-3.32, -10.9, 2.6, 16, 12, -0.64, 0.77, CYAN),
				crystal(2.25, -8, 2.6, 12, 12, 0.26, 0.97, ICE),
				crystal(-8.28, -32.96, 1.6, 6, 14, -0.79, -0.61, GREEN),
				crystal(-11.57, -25.9, 1.6, 6, 14, -0.98, -0.22, GREEN),
				crystal(-11.57, -18.1, 1.6, 6, 14, -0.98, 0.22, GREEN),
				crystal(-8.28, -11.04, 1.6, 6, 14, -0.79, 0.61, GREEN),
			},
		},
		{
			Id = "Gate",
			Yaw = -8,
			Name = "Glacier Gate",
			Description = "A tall ice gateway before the palace, crowned with a crystal spire and flanked by snow banks.",
			Pad = Vector2.new(31, -47),
			PriceSeconds = 73,
			Pieces = {
				B(38, 7, -53, 3, 14, 3, ICE, Glacier),
				B(38, 7, -41, 3, 14, 3, ICE, Glacier),
				B(38, 13.5, -47, 3.4, 3, 15.4, DEEP, Ice),
				B(38, 16.6, -47, 2, 3.2, 8, ICE, Ice),
				B(38, 19.4, -47, 1.4, 3, 1.4, CYAN, Ice),
				B(36.5, 0.25, -47, 7, 0.5, 11, PALE, Ice),
				Ball(38, 1.5, -57.5, 5, 3, 5, SNOW, Snow),
				Ball(38, 1.5, -36.5, 5, 3, 5, SNOW, Snow),
			},
		},
		{
			Id = "Igloo",
			Yaw = 20,
			Name = "Igloo Village",
			Description = "Two round snow igloos with tunnel doors, a stack of ice blocks and a little red flag.",
			Pad = Vector2.new(-68, 34),
			PriceSeconds = 84,
			Pieces = {
				Ball(-79, 4.5, 24, 15, 9, 15, SNOW, Snow),
				B(-71, 2, 24, 7, 4, 4.6, SNOW, Snow),
				B(-67.7, 1.5, 24, 0.6, 3, 3.2, DARK, Slate),
				Ball(-72, 3.2, 34, 10, 6.4, 10, SNOW, Snow),
				B(-67.2, 1.5, 34, 5, 3, 3.6, SNOW, Snow),
				B(-84, 1.2, 34, 3.6, 2.4, 3, ICE, Glacier),
				B(-84.4, 3.2, 34, 2.4, 1.6, 2.4, PALE, Glacier),
				Cy(-64, 4.5, 28, 0.6, 9, WOOD, Wood),
				B(-62.8, 8, 28, 2.4, 1.6, 0.2, RED, Fabric),
			},
		},
		{
			Id = "Rink",
			Yaw = -8,
			Name = "Skating Rink",
			Description = "A little skating rink with a wooden rim, a bench and two lamps, right on the frozen lake.",
			Pad = Vector2.new(46, 48),
			PriceSeconds = 97,
			Pieces = {
				B(54, 0.35, 34, 28, 0.3, 16, PALE, Ice),
				B(54, 0.8, 25.6, 29.6, 1.4, 0.8, WOOD, Planks),
				B(39.6, 0.8, 34, 0.8, 1.4, 16.8, WOOD, Planks),
				B(68.4, 0.8, 34, 0.8, 1.4, 16.8, WOOD, Planks),
				B(45.6, 0.8, 42.4, 12.8, 1.4, 0.8, WOOD, Planks),
				B(62.4, 0.8, 42.4, 12.8, 1.4, 0.8, WOOD, Planks),
				Cy(41, 3.5, 27.5, 0.6, 7, DARK, Metal),
				Cy(67, 3.5, 27.5, 0.6, 7, DARK, Metal),
				B(54, 1.2, 27, 6, 1, 1.6, WOOD, Planks),
				B(54, 0.55, 34, 8, 0.1, 8, ICE_D, Ice),
			},
		},
		{
			Id = "Snowmen",
			Yaw = 22,
			Name = "Snowman Family",
			Description = "A big, a middle and a small snowman with top hats, scarves, carrot noses and stick arms.",
			Pad = Vector2.new(-62, 2),
			PriceSeconds = 111,
			Pieces = merge(
				snowman3(-62, -6, 7),
				{
					B(-62, 12.8, -6, 3.4, 0.4, 3.4, BLACK, Fabric),
					B(-62, 14, -6, 2.2, 2.2, 2.2, BLACK, Fabric),
					B(-65.6, 8.2, -6, 3.6, 0.35, 0.35, WOOD, Wood, rot(0, 0, 20)),
					B(-58.4, 8.2, -6, 3.6, 0.35, 0.35, WOOD, Wood, rot(0, 0, -20)),
				},
				snowman3(-54, -2, 5.4),
				snowman3(-57, -12, 4),
				{
					B(-57, 7.6, -12, 2, 0.9, 2, RED, Fabric),
				}
			),
		},
		{
			Id = "Sled",
			Yaw = 28,
			Name = "Sled and Presents",
			Description = "A red sled stacked high with wrapped presents, a sack of toys and a little striped tree.",
			Pad = Vector2.new(16, 40),
			PriceSeconds = 128,
			Pieces = {
				B(24, 1.6, 36, 10, 0.8, 4.6, RED, Wood),
				B(24, 0.7, 34, 11.4, 0.5, 0.5, DARK, Metal),
				B(24, 0.7, 38, 11.4, 0.5, 0.5, DARK, Metal),
				B(19.2, 3.2, 36, 0.8, 3.2, 4.6, RED, Wood),
				B(22, 3.4, 36, 3.2, 2.6, 3, GREEN, Fabric),
				B(25.2, 3.2, 35.4, 3.6, 2.2, 3.4, PURPLE, Fabric),
				B(23.6, 5.4, 36.4, 2.4, 1.8, 2.4, GOLD, Fabric),
				Ball(27.4, 3.4, 37.4, 3.2, 3.2, 3.2, WOOD, Fabric),
				Cy(30.2, 3.4, 34.6, 1.6, 6.8, GREEN, Wood),
			},
		},
		{
			Id = "Fountain",
			Name = "Frozen Fountain",
			Description = "A fountain frozen solid mid-splash, with a crown of ice spikes around its icy bowl.",
			Pad = Vector2.new(34, 25),
			PriceSeconds = 147,
			Pieces = {
				Cy(30, 1, 14, 15, 2, STONE, Rock),
				Cy(30, 2.1, 14, 13, 0.4, ICE_D, Ice),
				Cy(30, 5, 14, 3, 6, PALE, Ice),
				Cy(30, 8, 14, 8, 1.2, ICE, Ice),
				Cy(30, 10, 14, 2, 3, PALE, Ice),
				Ball(30, 12, 14, 3, 3.4, 3, CYAN, Ice),
				B(23.6, 3.4, 14, 0.9, 4, 0.9, ICE, Ice, rot(0, 0, 18)),
				B(36.4, 3.4, 14, 0.9, 4, 0.9, ICE, Ice, rot(0, 0, -18)),
				B(30, 3.4, 7.6, 0.9, 4, 0.9, ICE, Ice, rot(-18, 0, 0)),
				B(30, 3.4, 20.4, 0.9, 4, 0.9, ICE, Ice, rot(18, 0, 0)),
			},
		},
		{
			Id = "Cabin",
			Yaw = -10,
			Name = "Snowy Cabin",
			Description = "A cosy log cabin under a deep snow roof, with a smoking chimney, a porch and a pile of firewood.",
			Pad = Vector2.new(-70, -22),
			PriceSeconds = 169,
			Pieces = {
				B(-80, 4, -14, 14, 8, 10, WOOD, Planks),
				B(-80, 11, -17.4, 16, 0.8, 6.6, SNOW, Snow, rot(-33, 0, 0)),
				B(-80, 11, -10.6, 16, 0.8, 6.6, SNOW, Snow, rot(33, 0, 0)),
				B(-84.6, 11.5, -16.5, 2, 7, 2, STONE, Rock),
				B(-80, 0.25, -7.6, 8, 0.5, 3, WOOD_D, Planks),
				B(-83.5, 2.5, -7, 0.6, 5, 0.6, WOOD_D, Wood),
				B(-76.5, 2.5, -7, 0.6, 5, 0.6, WOOD_D, Wood),
				B(-74, 1.2, -12, 3, 2.4, 4, WOOD_D, Wood),
			},
		},
		{
			Id = "Spires",
			Yaw = 15,
			Name = "Frost Spires",
			Description = "Three tall slender ice spires rising out of a snow mound, each leaning its own way.",
			Pad = Vector2.new(50, -8),
			PriceSeconds = 194,
			Pieces = {
				B(49, 9, -18, 3.2, 18, 3.2, ICE_D, Glacier, rot(4, 0, -5)),
				B(52.5, 13, -15, 3.6, 26, 3.6, ICE, Glacier, rot(-4, 0, 3)),
				B(47, 6, -13, 2.6, 12, 2.6, PALE, Ice, rot(5, 0, 6)),
				B(54.6, 3, -18, 1.6, 6, 1.6, CYAN, Ice, rot(0, 0, -14)),
				B(51, 1.4, -15, 10, 2.8, 9, SNOW, Snow),
			},
		},
		{
			Id = "Sculptures",
			Yaw = -14,
			Name = "Ice Sculpture Garden",
			Description = "Carved ice on snowy pedestals: a tiny Shiba, a swan and a giant snowflake.",
			Pad = Vector2.new(-58, -34),
			PriceSeconds = 223,
			Pieces = {
				B(-66, 1.2, -46, 5, 2.4, 5, STONE, Rock),
				B(-66, 4.4, -46, 3.4, 4, 2.6, ICE, Ice),
				B(-62.6, 5.6, -46, 2, 2, 2, ICE, Ice),
				B(-58, 1.2, -48, 5, 2.4, 5, STONE, Rock),
				B(-58, 4.6, -48, 2.2, 4.6, 3.6, PALE, Ice),
				B(-58, 8.4, -48, 1.6, 3, 1.6, PALE, Ice),
				B(-50, 1.2, -45, 5, 2.4, 5, STONE, Rock),
				B(-50, 6.6, -45, 7, 7, 0.9, ICE, Ice),
				B(-50, 6.6, -45, 7, 0.9, 0.9, PALE, Ice, rot(0, 0, 60)),
				B(-50, 6.6, -45, 7, 0.9, 0.9, PALE, Ice, rot(0, 0, -60)),
			},
		},
		{
			Id = "Slide",
			Yaw = 10,
			Name = "Great Ice Slide",
			Description = "A tall ice tower with steps up the front and a long smooth slide down the side.",
			Pad = Vector2.new(80, 60),
			PriceSeconds = 257,
			Pieces = {
				B(88, 11.5, 46, 6, 1, 6, ICE, Glacier),
				B(85.5, 5.5, 43.5, 1.2, 11, 1.2, ICE_D, Glacier),
				B(90.5, 5.5, 43.5, 1.2, 11, 1.2, ICE_D, Glacier),
				B(85.5, 5.5, 48.5, 1.2, 11, 1.2, ICE_D, Glacier),
				B(90.5, 5.5, 48.5, 1.2, 11, 1.2, ICE_D, Glacier),
				B(88, 5.6, 51.8, 4.2, 0.6, 11.4, PALE, Ice, rot(49, 0, 0)),
				B(79, 5.6, 46, 15, 0.6, 3.6, ICE, Ice, rot(0, 0, 42)),
				B(79, 6.4, 44, 15, 0.8, 0.4, PALE, Ice, rot(0, 0, 42)),
				B(79, 6.4, 48, 15, 0.8, 0.4, PALE, Ice, rot(0, 0, 42)),
				Ball(72, 1, 46, 5, 2, 5, SNOW, Snow),
			},
		},
		{
			Id = "Penguins",
			Yaw = 25,
			Name = "Penguin Colony",
			Description = "A little iceberg crowded with waddling penguins, all pretending not to watch the Shiba.",
			Pad = Vector2.new(-16, 10),
			PriceSeconds = 295,
			Pieces = {
				B(-16, 1.2, 2, 12, 2.4, 9, ICE, Glacier),
				B(-18, 3.6, 1, 6, 2.4, 5, PALE, Glacier),
				Ball(-12, 4.1, 4, 1.8, 3.4, 1.8, BLACK, Plastic),
				Ball(-14.5, 4.1, 5.5, 1.8, 3.4, 1.8, BLACK, Plastic),
				Ball(-10.5, 4.1, 1, 1.8, 3.4, 1.8, BLACK, Plastic),
				Ball(-18, 6.3, 1, 1.8, 3.4, 1.8, BLACK, Plastic),
				Ball(-20, 4.1, 4, 1.8, 3.4, 1.8, BLACK, Plastic),
				B(-12.5, 2.9, -1, 2.4, 1, 1.4, ICE_D, Ice),
			},
		},
		{
			Id = "FishHut",
			Yaw = -20,
			Name = "Ice Fishing Hut",
			Description = "A tiny blue fishing hut on the lake with a hole in the ice, a bucket of fish and a crate.",
			Pad = Vector2.new(80, 26),
			PriceSeconds = 339,
			Pieces = {
				B(74, 3.2, 14, 7, 6.4, 6, DEEP, Wood),
				B(74, 7, 14, 8.6, 0.8, 7.2, SNOW, Snow),
				B(74, 0.4, 19.5, 4, 0.2, 4, DARK, Ice),
				B(78.6, 1, 17.5, 2, 2, 2, WOOD, Wood),
				B(70.2, 0.9, 17.8, 1.6, 1.8, 1.6, RED, Plastic),
				B(74, 3.6, 19.5, 0.4, 7.2, 0.4, WOOD_D, Wood, rot(-14, 0, 0)),
				B(77.2, 1.4, 11, 3, 2.8, 2, SNOW, Snow),
			},
		},
		{
			Id = "Cannon",
			Yaw = 18,
			Name = "Snow Cannon",
			Description = "A snow-making machine on a steel frame, puffing out a fluffy white cloud.",
			Pad = Vector2.new(40, 51),
			PriceSeconds = 390,
			Pieces = {
				B(40, 0.6, 58, 6, 1.2, 5, DARK, Metal),
				Cy(40, 3, 58, 4, 3.6, STEEL, Metal),
				B(43.5, 4, 58, 4, 2.4, 2.4, DARK, Metal, rot(0, 0, 12)),
				B(38.6, 2.6, 58, 0.5, 4, 3.6, DARK, Metal),
				Ball(48, 5, 58, 3, 3, 3, SNOW, Snow),
				Ball(50.6, 5.6, 57.6, 4, 4, 4, SNOW, Snow),
				Ball(53.4, 6.4, 58, 5, 5, 5, SNOW, Snow),
				Ball(50, 1.2, 58.6, 10, 2.4, 6, SNOW, Snow),
			},
		},
		{
			Id = "Crystals",
			Yaw = 15,
			Name = "Crystal Cluster",
			Description = "A burst of seven big crystals growing out of a blue rock, leaning in all directions.",
			Pad = Vector2.new(-52, 32),
			PriceSeconds = 449,
			Pieces = {
				Ball(-56, 1, 22, 12, 2, 11, STONE, Rock),
				B(-56, 7, 22, 3.6, 14, 3.6, CYAN, Ice, rot(0, 0, 6)),
				B(-51, 4.5, 22, 2.6, 9, 2.6, ICE, Ice, rot(0, 0, -20)),
				B(-53.5, 3.5, 26.3, 2.6, 7, 2.6, PURPLE, Ice, rot(17.3, 0, -10)),
				B(-58.5, 4, 26.3, 2.6, 8, 2.6, ICE, Ice, rot(17.3, 0, 10)),
				B(-61, 3, 22, 2.6, 6, 2.6, GREEN, Ice, rot(0, 0, 20)),
				B(-58.5, 4.5, 17.7, 2.6, 9, 2.6, ICE, Ice, rot(-17.3, 0, 10)),
				B(-53.5, 3.5, 17.7, 2.6, 7, 2.6, PURPLE, Ice, rot(-17.3, 0, -10)),
			},
		},
		{
			Id = "SnowFort",
			Yaw = -16,
			Name = "Snow Fort",
			Description = "A snowball-fight fort with crenellated walls and neat piles of ready-made snowballs.",
			Pad = Vector2.new(50, 6.5),
			PriceSeconds = 516,
			Pieces = {
				B(50, 2.2, -0.5, 14, 4.4, 2.4, SNOW, Snow),
				B(43.5, 2.2, 4, 2.4, 4.4, 11, SNOW, Snow),
				B(56.5, 2.2, 4, 2.4, 4.4, 11, SNOW, Snow),
				B(45.5, 5.1, -0.5, 2.2, 1.4, 2.4, SNOW, Snow),
				B(50, 5.1, -0.5, 2.2, 1.4, 2.4, SNOW, Snow),
				B(54.5, 5.1, -0.5, 2.2, 1.4, 2.4, SNOW, Snow),
				B(43.5, 5.1, 2, 2.4, 1.4, 2.2, SNOW, Snow),
				B(56.5, 5.1, 2, 2.4, 1.4, 2.2, SNOW, Snow),
				B(50, 1.2, 9, 6, 2.4, 1.2, SNOW, Snow),
				Ball(46.5, 1, 3, 2.6, 2.2, 2.6, PALE, Snow),
				Ball(53.4, 1, 3, 2.6, 2.2, 2.6, PALE, Snow),
				Ball(50, 1, 2.4, 2.2, 2, 2.2, PALE, Snow),
			},
		},
		{
			Id = "HotSpring",
			Yaw = 22,
			Name = "Steaming Hot Spring",
			Description = "A warm rocky spring pool wrapped in steam, with a bench and a rack for the towels.",
			Pad = Vector2.new(-70, 6),
			PriceSeconds = 594,
			Pieces = {
				Cy(-80, 0.7, 4, 12, 1.4, STONE, Rock),
				Cy(-80, 1.5, 4, 10, 0.2, TEAL, Plastic),
				Ball(-85.4, 1.4, 1, 3.4, 2.8, 3, STONE, Rock),
				Ball(-74.4, 1.4, 0.4, 3, 2.6, 3, STONE, Rock),
				Ball(-74, 1.2, 6.6, 3, 2.4, 3.4, STONE, Rock),
				Ball(-86, 1.2, 7, 3.2, 2.4, 3, STONE, Rock),
				Ball(-82, 4, 3, 3.4, 3, 3.4, SNOW, Snow),
				Ball(-77.6, 5.4, 5, 3.2, 3.4, 3.2, SNOW, Snow),
				B(-72.5, 1, 10.4, 4, 2, 1.6, WOOD, Planks),
				B(-85.4, 2.6, 11, 3, 5.2, 0.5, WOOD_D, Wood),
			},
		},
		{
			Id = "Glacier",
			Yaw = 6,
			Name = "Glacier Cliff",
			Description = "A towering blue glacier cliff with sharp spurs and a snow cap, guarding the end of the lake.",
			Pad = Vector2.new(74, 0),
			PriceSeconds = 683,
			Pieces = {
				B(85, 5, -4, 12, 10, 24, ICE, Glacier),
				B(86, 12, -8, 8, 8, 14, ICE_D, Glacier, rot(0, 0, 6)),
				B(84, 15, -2, 4, 14, 4, PALE, Glacier, rot(4, 0, -8)),
				B(80.6, 2, 6, 5, 4, 6, SNOW, Snow),
				B(87, 17.4, -10, 5, 3, 7, SNOW, Snow),
				B(89, 3.5, 5, 4, 7, 5, ICE_D, Glacier),
			},
		},
		{
			Id = "Observatory",
			Yaw = 8,
			Name = "Frost Observatory",
			Description = "A round stone tower with a blue dome and a long brass-and-ice telescope aimed at the aurora.",
			Pad = Vector2.new(-76, -34),
			PriceSeconds = 785,
			Pieces = {
				B(-82, 0.5, -42, 14, 1, 14, STONE, Rock),
				Cy(-82, 5, -42, 11, 9, PALE, Ice),
				Ball(-82, 10.5, -42, 12, 9, 12, DEEP, Ice),
				B(-82, 13.4, -39.6, 1.6, 1.6, 9, STEEL, Metal, rot(-35, 0, 0)),
				B(-82, 1, -34.5, 4, 2, 4, SNOW, Snow),
				Ball(-88, 1.5, -36, 6, 3, 6, SNOW, Snow),
			},
		},
		{
			Id = "Throne",
			Yaw = -12,
			Name = "Ice Throne",
			Description = "A spiky ice throne on a frosty dais between two crystal pillars: the seat of the Frost Queen.",
			Pad = Vector2.new(18, -48),
			PriceSeconds = 903,
			RewardMult = 1.25,
			Pieces = {
				B(18, 0.8, -58, 12, 1.6, 10, PALE, Ice),
				B(18, 0.4, -52.2, 9, 0.8, 1.8, PALE, Ice),
				B(18, 3, -59, 3.4, 2.8, 3.4, ICE, Ice),
				B(18, 8, -60.8, 4, 10, 1.2, ICE, Ice),
				B(15.6, 3.8, -59, 1, 1.6, 3.6, ICE_D, Ice),
				B(20.4, 3.8, -59, 1, 1.6, 3.6, ICE_D, Ice),
				B(16.2, 14.4, -60.8, 1, 5, 1, CYAN, Ice),
				B(18, 15.4, -60.8, 1, 6.6, 1, CYAN, Ice),
				B(19.8, 14.4, -60.8, 1, 5, 1, CYAN, Ice),
				B(12.8, 5, -55, 1.4, 10, 1.4, ICE_D, Glacier),
				B(23.2, 5, -55, 1.4, 10, 1.4, ICE_D, Glacier),
			},
		},
		{
			Id = "Obelisk",
			Yaw = 14,
			Name = "Aurora Obelisk",
			Description = "A tall crystal obelisk wrapped in floating rings of green and purple aurora light.",
			Pad = Vector2.new(-38, -47),
			PriceSeconds = 1038,
			RewardMult = 1.3,
			Pieces = {
				B(-38, 0.8, -57, 10, 1.6, 10, STONE, Slate),
				B(-38, 2.2, -57, 7, 1.2, 7, PALE, Ice),
				B(-38, 13, -57, 4, 22, 4, PURPLE, Ice),
				B(-38, 26, -57, 2.4, 4, 2.4, CYAN, Ice),
				Cy(-38, 10, -57, 11, 0.4, GREEN, Ice),
				Cy(-38, 17, -57, 9, 0.4, CYAN, Ice),
				B(-42.2, 8, -57, 0.4, 7, 3, GREEN, Ice),
				B(-33.8, 8, -57, 0.4, 7, 3, GREEN, Ice),
			},
		},
		{
			Id = "Drake",
			Yaw = 12,
			Name = "Frost Drake",
			Description = "A huge ice dragon carved from the glacier, wings half open and a long neck stretched toward the walkway.",
			Pad = Vector2.new(-66, 45),
			PriceSeconds = 1194,
			RewardMult = 1.3,
			Pieces = {
				B(-76, 1.2, 54, 18, 2.4, 10, ICE_D, Glacier),
				B(-76, 4.8, 54, 9, 4.4, 4.4, ICE, Glacier),
				B(-70.6, 8, 54, 3, 5.5, 2.6, ICE, Glacier, rot(0, 0, -20)),
				B(-68.2, 10.8, 54, 4.6, 2.4, 2.4, PALE, Glacier),
				B(-78, 10.5, 50.4, 9, 0.6, 6, PALE, Ice, rot(30, 0, 8)),
				B(-78, 10.5, 57.6, 9, 0.6, 6, PALE, Ice, rot(-30, 0, 8)),
				B(-83, 4, 54, 6, 1.6, 1.8, ICE, Glacier, rot(0, 0, 12)),
				B(-73, 2.8, 52, 1.8, 3, 1.8, ICE_D, Glacier),
				B(-73, 2.8, 56, 1.8, 3, 1.8, ICE_D, Glacier),
			},
		},
		{
			Id = "Crown",
			Yaw = 6,
			Name = "Giant Ice Crown",
			Description = "The showpiece: a giant crown of clear ice and gold on a stone plinth, set with a huge red jewel.",
			Pad = Vector2.new(12, 61),
			PriceSeconds = 1373,
			RewardMult = 1.8,
			Pieces = {
				B(12, 1, 50, 12, 2, 12, STONE, Rock),
				Cy(12, 4, 50, 9.4, 4, ICE, Ice),
				Cy(12, 6.4, 50, 9.8, 1, GOLD, Metal),
				B(12, 10, 54.2, 1.8, 6, 1.8, ICE, Ice, rot(12, 0, 0)),
				B(12, 10, 45.8, 1.8, 6, 1.8, ICE, Ice, rot(-12, 0, 0)),
				B(16.2, 10, 50, 1.8, 6, 1.8, ICE, Ice, rot(0, 0, -12)),
				B(7.8, 10, 50, 1.8, 6, 1.8, ICE, Ice, rot(0, 0, 12)),
				B(12, 11.6, 50, 2, 9, 2, CYAN, Ice),
				Ball(12, 5, 54.2, 1.6, 1.6, 1.6, RED, Ice),
				Ball(12, 12.4, 50, 3, 3, 3, RED, Ice),
			},
		},
	},
}

return theme
