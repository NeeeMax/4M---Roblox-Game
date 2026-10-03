--!strict
-- Theme of the Shiba of bay 25: Cloud Temple (Config/DecorTypes -> Theme). 160 x 115: Angel Shiba stands on a gold-ringed cloud plaza with
-- winged backdrop in front of the marble Sky Temple; the walkway winds through a heaven garden: pearly gate and signpost at the
-- entrance, a wishing well, harp, pond and flower meadow in the middle, a rainbow arch near the exit, and a tall bell spire in the
-- back left corner. Parts are loose clusters at different angles.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lanterns and halos are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local WHITE = C(246, 248, 253)
local CLOUD = C(216, 228, 246)
local SKY = C(140, 196, 242)
local MARBLE = C(238, 232, 220)
local STONE = C(196, 190, 184)
local GOLD = C(238, 190, 64)
local PINK = C(248, 196, 210)
local ROSE = C(232, 130, 150)
local LAV = C(186, 172, 226)
local MINT = C(168, 222, 198)
local GREEN = C(120, 190, 130)
local SUN = C(255, 226, 120)
local WOOD = C(176, 130, 90)
local CREAM = C(250, 240, 214)
local RAIN1 = C(236, 100, 108)
local RAIN2 = C(250, 220, 90)
local RAIN3 = C(130, 210, 150)
local RAIN4 = C(110, 170, 235)
local SKIN = C(252, 218, 196)

local Concrete = Enum.Material.Concrete
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Marble = Enum.Material.Marble
local Wood = Enum.Material.Wood
local Glass = Enum.Material.Glass
local Grass = Enum.Material.Grass
local Fabric = Enum.Material.Fabric

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
local function Cy(
	x: number,
	y: number,
	z: number,
	d: number,
	h: number,
	color: Color3,
	mat: Enum.Material,
	ry: number?
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, ry or 0, 90),
	}
end

-- Disc facing the road (axis along Z): diameter d, thickness len.
local function Cz(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
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

local theme: DecorTypes.Theme = {
	Key = "CloudTemple",
	Name = "Cloud Temple",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(20, -14), Facing = 270 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(-32, 44),
		Vector2.new(12, 30),
		Vector2.new(50, 14),
		Vector2.new(16, 0),
		Vector2.new(-36, -8),
		Vector2.new(-50, -38),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(4, -9),
	AutoPad = Vector2.new(4, -19),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Cloud Plaza",
			Description = "Soft pale cloud floor with white drifts, a sky-blue patch and a gold-ringed marble plaza under the Angel Shiba.",
			Pad = Vector2.new(-10, 53),
			PriceSeconds = 62,
			Pieces = {
				B(0, 0.15, 0, 160, 0.3, 115, CLOUD, Concrete),
				B(20, 0.4, -14, 26, 0.2, 26, WHITE, Marble),
				B(20, 0.48, -14, 17, 0.2, 17, GOLD, Metal),
				Ball(-48, 0.3, 26, 34, 0.5, 20, WHITE, Concrete),
				Ball(56, 0.3, -30, 30, 0.5, 18, WHITE, Concrete),
				Ball(-30, 0.3, -40, 28, 0.5, 14, WHITE, Concrete),
				Ball(36, 0.3, 44, 26, 0.5, 12, WHITE, Concrete),
				Ball(-10, 0.3, 5, 20, 0.5, 10, WHITE, Concrete),
				Ball(62, 0.3, 6, 16, 0.5, 10, SKY, Concrete),
				Ball(-62, 0.3, -10, 22, 0.5, 14, WHITE, Concrete),
				B(-62, 0.4, -4, 20, 0.2, 20, MARBLE, Marble),
			},
		},
		-- 2
		{
			Id = "PearlyGate",
			Yaw = 17.5,
			Name = "Pearly Gate",
			Description = "Two marble pillars with gold caps and a lintel stand across the walkway, with the gold gate swung open on cloud puffs.",
			Pad = Vector2.new(-18, 46),
			PriceSeconds = 71,
			Pieces = {
				B(-2, 0.9, 24, 4.2, 1.8, 4.2, STONE, Marble),
				B(-2, 0.9, 45, 4.2, 1.8, 4.2, STONE, Marble),
				Cy(-2, 8, 24, 3.2, 12.4, MARBLE, Marble),
				Cy(-2, 8, 45, 3.2, 12.4, MARBLE, Marble),
				B(-2, 14.6, 24, 4.4, 1.2, 4.4, GOLD, Metal),
				B(-2, 14.6, 45, 4.4, 1.2, 4.4, GOLD, Metal),
				B(-2, 16.2, 34.5, 3.2, 2.2, 26, MARBLE, Marble),
				Ball(-2, 18.6, 24, 2.4, 2.4, 2.4, GOLD, Metal),
				Ball(-2, 18.6, 45, 2.4, 2.4, 2.4, GOLD, Metal),
				Ball(-2, 1.2, 21, 6, 2.4, 4.4, WHITE, Concrete),
				B(-4.2, 5.5, 25.6, 3.8, 9, 0.5, GOLD, Metal),
				B(0.2, 5.5, 43.4, 3.8, 9, 0.5, GOLD, Metal),
			},
		},
		-- 3
		{
			Id = "HeavenSign",
			Yaw = 14,
			Name = "Heaven Signpost",
			Description = "A sky-blue signboard in a gold frame on two marble posts, welcoming everybody to Heaven.",
			Pad = Vector2.new(-30, 38),
			PriceSeconds = 82,
			Pieces = {
				Ball(-37, 0.7, 32, 13, 1.4, 5, WHITE, Concrete),
				Cy(-41, 4, 32, 0.9, 7, MARBLE, Marble),
				Cy(-33, 4, 32, 0.9, 7, MARBLE, Marble),
				B(-37, 7.4, 32, 11, 4, 0.8, SKY, Plastic),
				B(-37, 7.4, 31.55, 11.8, 4.8, 0.5, GOLD, Metal),
				Ball(-41, 8.4, 32, 1.6, 1.6, 1.6, GOLD, Metal),
				Ball(-33, 8.4, 32, 1.6, 1.6, 1.6, GOLD, Metal),
				B(-34.5, 3.4, 32.7, 5, 1.6, 0.5, PINK, Plastic),
			},
		},
		-- 4
		{
			Id = "CloudMounds",
			Yaw = -10,
			Name = "Cloud Mounds",
			Description = "A heap of fluffy cloud mounds of different sizes, soft enough to bounce on.",
			Pad = Vector2.new(19, 35),
			PriceSeconds = 94,
			Pieces = {
				Ball(20, 2.6, 47, 10, 5.2, 8.5, WHITE, Concrete),
				Ball(27, 3.6, 45, 13, 7.2, 10, WHITE, Concrete),
				Ball(34, 2.2, 48, 8.5, 4.4, 7, CLOUD, Concrete),
				Ball(29, 1.6, 52, 7, 3.2, 6, WHITE, Concrete),
				Ball(25, 6.6, 45, 6, 4, 5, WHITE, Concrete),
			},
		},
		-- 5
		{
			Id = "GoldenLamps",
			Yaw = 0,
			Name = "Golden Lamps",
			Description = "Three golden lamp posts with warm yellow lanterns scattered through the meadow.",
			Pad = Vector2.new(-12, 4),
			PriceSeconds = 108,
			Pieces = {
				Cy(-6, 0.5, 10, 2.2, 1, STONE, Marble),
				Cy(-6, 4.5, 10, 0.7, 8, GOLD, Metal),
				Ball(-6, 9.4, 10, 2.6, 2.6, 2.6, SUN, Plastic),
				Cy(-18, 0.5, 6.5, 2.2, 1, STONE, Marble),
				Cy(-18, 4.5, 6.5, 0.7, 8, GOLD, Metal),
				Ball(-18, 9.4, 6.5, 2.6, 2.6, 2.6, SUN, Plastic),
				Cy(-30, 0.5, -19, 2.2, 1, STONE, Marble),
				Cy(-30, 4.5, -19, 0.7, 8, GOLD, Metal),
				Ball(-30, 9.4, -19, 2.6, 2.6, 2.6, SUN, Plastic),
			},
		},
		-- 6
		{
			Id = "WishingWell",
			Yaw = -22,
			Name = "Wishing Well",
			Description = "A marble wishing well with sky water, two posts and a little pink roof, sitting on cloud puffs.",
			Pad = Vector2.new(-12, 11),
			PriceSeconds = 125,
			Pieces = {
				Cy(-16, 1.3, 16, 6.6, 2.6, MARBLE, Marble),
				Cy(-16, 2.65, 16, 4.8, 0.3, SKY, Glass),
				B(-18.4, 5.2, 16, 0.8, 5.2, 0.8, WOOD, Wood),
				B(-13.6, 5.2, 16, 0.8, 5.2, 0.8, WOOD, Wood),
				B(-16, 8.2, 16, 7.4, 0.7, 5.4, PINK, Plastic),
				B(-16, 9, 16, 4, 0.8, 3.2, PINK, Plastic),
				Ball(-16, 10, 16, 1.4, 1.4, 1.4, GOLD, Metal),
				Ball(-19.5, 0.9, 18, 4, 1.8, 3, WHITE, Concrete),
				Ball(-12.5, 0.8, 13.5, 3.6, 1.6, 3, WHITE, Concrete),
			},
		},
		-- 7
		{
			Id = "FlowerBeds",
			Name = "Flower Beds",
			Description = "Three tilted garden beds full of pink, gold and lavender blossoms.",
			Pad = Vector2.new(-30, 12),
			PriceSeconds = 143,
			Pieces = {
				B(-42, 0.8, 12, 8, 1.6, 3.2, GREEN, Grass, 0, 20, 0),
				B(-35, 0.8, 8, 7, 1.6, 3, GREEN, Grass, 0, -15, 0),
				B(-39, 0.8, 4, 6, 1.6, 2.8, GREEN, Grass, 0, 30, 0),
				Ball(-44, 2.3, 12.5, 1.8, 1.8, 1.8, PINK, Plastic),
				Ball(-41.5, 2.4, 11.5, 1.8, 1.8, 1.8, LAV, Plastic),
				Ball(-39.8, 2.3, 12.8, 1.8, 1.8, 1.8, SUN, Plastic),
				Ball(-36.8, 2.3, 8.4, 1.8, 1.8, 1.8, ROSE, Plastic),
				Ball(-34.8, 2.4, 7.8, 1.8, 1.8, 1.8, SUN, Plastic),
				Ball(-33.4, 2.3, 8.6, 1.8, 1.8, 1.8, PINK, Plastic),
				Ball(-40.6, 2.3, 4.2, 1.8, 1.8, 1.8, LAV, Plastic),
				Ball(-38.8, 2.4, 3.6, 1.8, 1.8, 1.8, ROSE, Plastic),
				Ball(-37.4, 2.3, 4.6, 1.8, 1.8, 1.8, SUN, Plastic),
			},
		},
		-- 8
		{
			Id = "CloudFountain",
			Yaw = 16,
			Name = "Cloud Fountain",
			Description = "A two-tier marble fountain with sky-blue water and a gold ball on top, floating on a cloud.",
			Pad = Vector2.new(50, 44),
			PriceSeconds = 165,
			Pieces = {
				Ball(60, 1, 38, 18, 2, 18, WHITE, Concrete),
				Cy(60, 2.2, 38, 13, 2.4, MARBLE, Marble),
				Cy(60, 3.5, 38, 11.4, 0.3, SKY, Glass),
				Cy(60, 5.5, 38, 3, 4, MARBLE, Marble),
				Cy(60, 8, 38, 7, 1.2, MARBLE, Marble),
				Cy(60, 8.7, 38, 6, 0.2, SKY, Glass),
				Cy(60, 10, 38, 1.6, 2.4, MARBLE, Marble),
				Ball(60, 12, 38, 2.6, 2.6, 2.6, GOLD, Metal),
			},
		},
		-- 9
		{
			Id = "CloudTrees",
			Yaw = -18,
			Name = "Cloud Trees",
			Description = "Three round-crowned trees in mint and blossom pink on slim trunks.",
			Pad = Vector2.new(-38, 20),
			PriceSeconds = 190,
			Pieces = {
				Cy(-46, 3.5, 24, 1.4, 7, WOOD, Wood),
				Ball(-46, 9, 24, 9, 8, 9, MINT, Grass),
				Ball(-48, 7.5, 26, 6, 5, 6, MINT, Grass),
				Cy(-52, 2.6, 30, 1.2, 5.2, WOOD, Wood),
				Ball(-52, 7, 30, 7, 6.4, 7, PINK, Grass),
				Cy(-40, 2.3, 20, 1.1, 4.6, WOOD, Wood),
				Ball(-40, 6.6, 20, 6.4, 5.6, 6.4, MINT, Grass),
				Ball(-42, 5.4, 22, 4, 3.4, 4, PINK, Grass),
			},
		},
		-- 10
		{
			Id = "Benches",
			Yaw = 20,
			Name = "Cloud Benches",
			Description = "Two marble benches and a small round table, turned toward the walkway.",
			Pad = Vector2.new(58, 18),
			PriceSeconds = 218,
			Pieces = {
				B(66.5, 2.2, 14, 2.2, 0.7, 6, MARBLE, Marble),
				B(68.2, 3.6, 14, 0.7, 2.6, 6, MARBLE, Marble),
				B(66.5, 1, 12, 1.8, 1.4, 0.8, STONE, Marble),
				B(66.5, 1, 16, 1.8, 1.4, 0.8, STONE, Marble),
				B(64, 2.2, 24, 2.2, 0.7, 6, MARBLE, Marble, 0, 15, 0),
				B(65.7, 3.6, 24, 0.7, 2.6, 6, MARBLE, Marble, 0, 15, 0),
				B(64, 1, 22, 1.8, 1.4, 0.8, STONE, Marble),
				B(64, 1, 26, 1.8, 1.4, 0.8, STONE, Marble),
				Cy(61, 1.3, 19, 3, 2.6, MARBLE, Marble),
				Cy(61, 2.7, 19, 4, 0.3, PINK, Plastic),
			},
		},
		-- 11
		{
			Id = "AngelStatues",
			Name = "Angel Statues",
			Description = "A small family of marble angels on pedestals, a tall one, a smaller one and a kneeling one.",
			Pad = Vector2.new(-54, -4),
			PriceSeconds = 251,
			Pieces = {
				B(-62, 1.2, -10, 4.4, 2.4, 4.4, STONE, Marble, 0, 25, 0),
				Cy(-62, 5.4, -10, 2.8, 6, MARBLE, Marble),
				Ball(-62, 9.4, -10, 2.4, 2.4, 2.4, WHITE, Marble),
				B(-63.6, 7.4, -11.6, 2.4, 4.6, 0.5, WHITE, Marble, 0, 0, 18),
				B(-60.4, 7.4, -11.6, 2.4, 4.6, 0.5, WHITE, Marble, 0, 0, -18),
				B(-67, 1, -2, 3.6, 2, 3.6, STONE, Marble, 0, -20, 0),
				Cy(-67, 4.4, -2, 2.3, 4.8, MARBLE, Marble),
				Ball(-67, 7.6, -2, 2, 2, 2, WHITE, Marble),
				B(-68.3, 6, -3.3, 2, 3.8, 0.45, WHITE, Marble, 0, 0, 18),
				B(-65.7, 6, -3.3, 2, 3.8, 0.45, WHITE, Marble, 0, 0, -18),
				B(-58, 0.8, -3, 3, 1.6, 3, STONE, Marble, 0, 35, 0),
				Cy(-58, 3, -3, 2, 2.8, MARBLE, Marble),
				Ball(-58, 5, -3, 1.7, 1.7, 1.7, WHITE, Marble),
				B(-58, 3.6, -4.4, 3.2, 3, 0.4, WHITE, Marble),
			},
		},
		-- 12
		{
			Id = "HarpGarden",
			Yaw = 20,
			Name = "Giant Harp",
			Description = "A golden harp taller than the Shiba, standing on a marble base with white strings.",
			Pad = Vector2.new(-22, 28),
			RewardMult = 1.25,
			PriceSeconds = 288,
			Pieces = {
				B(-28, 0.6, 22, 8, 1.2, 4, STONE, Marble),
				B(-31.2, 7, 22, 1.2, 12, 1.2, GOLD, Metal),
				B(-24.8, 6, 22, 1.8, 10, 1.4, GOLD, Metal),
				B(-28, 12.6, 22, 9, 1.2, 1.2, GOLD, Metal, 0, 0, -12),
				B(-30, 6.5, 22, 0.15, 9, 0.15, WHITE, Plastic),
				B(-29, 6.5, 22, 0.15, 8.4, 0.15, WHITE, Plastic),
				B(-28, 6.5, 22, 0.15, 7.8, 0.15, WHITE, Plastic),
				B(-27, 6.5, 22, 0.15, 7.2, 0.15, WHITE, Plastic),
				B(-26, 6.5, 22, 0.15, 6.6, 0.15, WHITE, Plastic),
				Ball(-32.5, 1.2, 24, 5, 2.4, 4, WHITE, Concrete),
				Ball(-23.5, 1, 20, 4.4, 2, 3.6, WHITE, Concrete),
			},
		},
		-- 13
		{
			Id = "CloudCottage",
			Yaw = 18,
			Name = "Cloud Cottage",
			Description = "A cosy cream cottage with a stacked pink roof, a gold door and a little chimney, floating on a big cloud.",
			Pad = Vector2.new(-52, 40),
			PriceSeconds = 332,
			Pieces = {
				Ball(-64, 1.4, 38, 24, 2.8, 20, WHITE, Concrete),
				B(-64, 6.5, 38, 13, 10, 10, CREAM, Concrete),
				B(-64, 12.5, 38, 15.6, 2, 12, ROSE, Plastic),
				B(-64, 14.5, 38, 11.4, 2, 8.6, ROSE, Plastic),
				B(-64, 16.5, 38, 6.4, 2, 5.6, ROSE, Plastic),
				Ball(-64, 18.2, 38, 2, 2, 2, GOLD, Metal),
				B(-64, 4.6, 43.1, 2.8, 4.4, 0.4, GOLD, Metal),
				B(-68.4, 7.4, 43.1, 2, 2, 0.3, SKY, Glass),
				B(-59.6, 7.4, 43.1, 2, 2, 0.3, SKY, Glass),
				B(-60, 15.4, 36, 1.6, 3, 1.6, STONE, Concrete),
			},
		},
		-- 14
		{
			Id = "Pavilion",
			Yaw = -14,
			Name = "Garden Pavilion",
			Description = "An open round pavilion with six slim marble columns and a layered rose roof.",
			Pad = Vector2.new(-49, 6),
			PriceSeconds = 381,
			Pieces = {
				Cy(-58, 0.5, 16, 13, 1, MARBLE, Marble),
				Cy(-58, 5.2, 21.2, 1.1, 8.4, MARBLE, Marble),
				Cy(-53.5, 5.2, 18.6, 1.1, 8.4, MARBLE, Marble),
				Cy(-53.5, 5.2, 13.4, 1.1, 8.4, MARBLE, Marble),
				Cy(-58, 5.2, 10.8, 1.1, 8.4, MARBLE, Marble),
				Cy(-62.5, 5.2, 13.4, 1.1, 8.4, MARBLE, Marble),
				Cy(-62.5, 5.2, 18.6, 1.1, 8.4, MARBLE, Marble),
				Cy(-58, 10.4, 16, 13.5, 1, ROSE, Plastic),
				Cy(-58, 11.5, 16, 8, 1.2, ROSE, Plastic),
				Cy(-58, 12.6, 16, 3, 1, ROSE, Plastic),
				Ball(-58, 13.8, 16, 1.6, 1.6, 1.6, GOLD, Metal),
				Cy(-58, 1.6, 16, 2.4, 1.2, STONE, Marble),
			},
		},
		-- 15
		{
			Id = "RuinColumns",
			Yaw = 12,
			Name = "Marble Ruins",
			Description = "Broken marble columns of different heights, a fallen one and a weathered lintel on two tall columns.",
			Pad = Vector2.new(54, 6),
			PriceSeconds = 439,
			Pieces = {
				B(62, 0.4, -4, 15, 0.8, 9, STONE, Marble),
				Cy(55, 6.6, -4, 2.2, 12.4, MARBLE, Marble),
				Cy(63, 6.6, -4, 2.2, 12.4, MARBLE, Marble),
				B(59, 13.4, -4, 11, 1.4, 2.4, MARBLE, Marble),
				Cy(67, 3.8, -2, 2.2, 6.6, MARBLE, Marble),
				Cy(70, 2.6, -6, 2.2, 4.2, MARBLE, Marble),
				Cx(60, 1.6, 0, 2.2, 9, MARBLE, Marble, 25),
				B(69, 1.1, 1, 2.6, 1.6, 2.6, STONE, Marble, 0, 30, 0),
				B(54, 1, -8, 2, 1.4, 2.4, STONE, Marble, 0, -20, 0),
			},
		},
		-- 16
		{
			Id = "CloudPond",
			Yaw = -12,
			Name = "Sky Pond",
			Description = "A round sky-blue pond with cloud rocks, floating lily pads and a little marble arch bridge.",
			Pad = Vector2.new(24, 18),
			PriceSeconds = 504,
			Pieces = {
				B(6, 0.45, 15, 16, 0.3, 16, SKY, Glass),
				B(7, 0.45, 15, 12, 0.3, 19, SKY, Glass),
				Ball(-0.5, 1, 15, 4, 2, 3.6, WHITE, Concrete),
				Ball(6, 1, 22, 4.4, 2, 3.4, WHITE, Concrete),
				Ball(12.5, 1, 14, 3.8, 2, 3.6, WHITE, Concrete),
				Ball(4, 1, 8.5, 3.6, 1.8, 3.2, WHITE, Concrete),
				B(3, 0.55, 12, 2.4, 0.15, 2.4, MINT, Grass),
				B(9, 0.55, 17.5, 2, 0.15, 2, MINT, Grass),
				B(6, 2.6, 15, 12, 0.8, 3.2, MARBLE, Marble),
				B(1, 1.3, 15, 2, 2.6, 3.2, MARBLE, Marble),
				B(11, 1.3, 15, 2, 2.6, 3.2, MARBLE, Marble),
				B(6, 3.7, 13.5, 12, 0.7, 0.5, GOLD, Metal),
				B(6, 3.7, 16.5, 12, 0.7, 0.5, GOLD, Metal),
			},
		},
		-- 17
		{
			Id = "Banners",
			Yaw = -10,
			Name = "Heaven Banners",
			Description = "Three tall banner poles with flags in sky blue, gold and pink, flying at different angles.",
			Pad = Vector2.new(33, 29),
			PriceSeconds = 580,
			Pieces = {
				Cy(29, 0.5, 36, 2.2, 1, STONE, Marble),
				Cy(29, 6.5, 36, 0.6, 12, MARBLE, Marble),
				B(31.6, 10.2, 36, 4.6, 3, 0.3, SKY, Fabric, 0, 20, 0),
				Ball(29, 12.9, 36, 1.2, 1.2, 1.2, GOLD, Metal),
				Cy(36, 0.5, 33, 2.2, 1, STONE, Marble),
				Cy(36, 5.5, 33, 0.6, 10, MARBLE, Marble),
				B(38.6, 8.4, 33, 4.6, 3, 0.3, GOLD, Fabric, 0, -22, 0),
				Ball(36, 10.9, 33, 1.2, 1.2, 1.2, GOLD, Metal),
				Cy(43, 0.5, 27, 2.2, 1, STONE, Marble),
				Cy(43, 6, 27, 0.6, 11, MARBLE, Marble),
				B(45.6, 9.4, 27, 4.6, 3, 0.3, PINK, Fabric, 0, 14, 0),
				Ball(43, 11.9, 27, 1.2, 1.2, 1.2, GOLD, Metal),
			},
		},
		-- 18
		{
			Id = "RainbowArch",
			Yaw = -68.7,
			Name = "Rainbow Arch",
			Description = "A tall rainbow arch standing across the walkway on two striped pillars with cloud puffs at their feet.",
			Pad = Vector2.new(-30, -48),
			PriceSeconds = 667,
			Pieces = {
				B(-49.6, 4.5, -43, 1.2, 9, 2.4, RAIN1, Plastic),
				B(-48.4, 4.5, -43, 1.2, 9, 2.4, RAIN2, Plastic),
				B(-47.2, 4.5, -43, 1.2, 9, 2.4, RAIN3, Plastic),
				B(-46, 4.5, -43, 1.2, 9, 2.4, RAIN4, Plastic),
				B(-28, 4.5, -43, 1.2, 9, 2.4, RAIN4, Plastic),
				B(-26.8, 4.5, -43, 1.2, 9, 2.4, RAIN3, Plastic),
				B(-25.6, 4.5, -43, 1.2, 9, 2.4, RAIN2, Plastic),
				B(-24.4, 4.5, -43, 1.2, 9, 2.4, RAIN1, Plastic),
				B(-37, 9.6, -43, 19.2, 1.2, 2.4, RAIN4, Plastic),
				B(-37, 10.8, -43, 21.6, 1.2, 2.4, RAIN3, Plastic),
				B(-37, 12, -43, 24, 1.2, 2.4, RAIN2, Plastic),
				B(-37, 13.2, -43, 26.4, 1.2, 2.4, RAIN1, Plastic),
				Ball(-48.5, 1.1, -43, 5, 2.2, 4, WHITE, Concrete),
				Ball(-25.5, 1.1, -43, 5, 2.2, 4, WHITE, Concrete),
			},
		},
		-- 19
		{
			Id = "WingsBackdrop",
			Name = "Angel Wings Backdrop",
			Description = "A pair of big white feathered wings spread behind the Angel Shiba on a golden shaft with a halo.",
			Pad = Vector2.new(34, -22),
			PriceSeconds = 767,
			Pieces = {
				B(20, 0.5, -26, 22, 1, 3.4, CLOUD, Concrete),
				B(20, 5.5, -26, 2.4, 9, 1.6, GOLD, Metal),
				Cz(20, 12.4, -26, 4.4, 0.6, GOLD, Metal),
				B(25, 9.6, -26, 7, 1.4, 0.9, WHITE, Marble, 0, 0, 28),
				B(26.4, 7.4, -26, 8.6, 1.4, 0.9, WHITE, Marble, 0, 0, 18),
				B(27.4, 5.4, -26, 9.4, 1.4, 0.9, WHITE, Marble, 0, 0, 9),
				B(27.4, 3.4, -26, 8.6, 1.4, 0.9, WHITE, Marble, 0, 0, 0),
				B(15, 9.6, -26, 7, 1.4, 0.9, WHITE, Marble, 0, 0, -28),
				B(13.6, 7.4, -26, 8.6, 1.4, 0.9, WHITE, Marble, 0, 0, -18),
				B(12.6, 5.4, -26, 9.4, 1.4, 0.9, WHITE, Marble, 0, 0, -9),
				B(12.6, 3.4, -26, 8.6, 1.4, 0.9, WHITE, Marble, 0, 0, 0),
			},
		},
		-- 20
		{
			Id = "SkyTemple",
			Yaw = 0,
			Name = "Sky Temple",
			Description = "The marble Cloud Temple behind the Shiba: six columns, a stepped golden pediment and a cella with a gold door.",
			Pad = Vector2.new(38, -26),
			RewardMult = 1.4,
			PriceSeconds = 882,
			Pieces = {
				B(26, 1, -42, 36, 2, 22, MARBLE, Marble),
				Cy(12, 8, -34, 2.4, 12, MARBLE, Marble),
				Cy(17.6, 8, -34, 2.4, 12, MARBLE, Marble),
				Cy(23.2, 8, -34, 2.4, 12, MARBLE, Marble),
				Cy(28.8, 8, -34, 2.4, 12, MARBLE, Marble),
				Cy(34.4, 8, -34, 2.4, 12, MARBLE, Marble),
				Cy(40, 8, -34, 2.4, 12, MARBLE, Marble),
				B(26, 14.8, -36, 32, 1.6, 10, MARBLE, Marble),
				B(26, 16.4, -36, 30, 1.6, 9, PINK, Marble),
				B(26, 18, -36, 22, 1.6, 7, MARBLE, Marble),
				B(26, 19.6, -36, 12, 1.6, 5, GOLD, Metal),
				B(26, 8.2, -47, 26, 12.4, 10, CREAM, Marble),
				B(26, 15.2, -47, 28, 2, 12, GOLD, Metal),
				B(26, 5.2, -41.8, 5, 6.4, 0.5, GOLD, Metal),
				Ball(26, 21.8, -36, 2.6, 2.6, 2.6, GOLD, Metal),
			},
		},
		-- 21
		{
			Id = "StarLanterns",
			Yaw = -16,
			Name = "Star Lanterns",
			Description = "Three tall posts with star-shaped golden lanterns, each a different height, standing beside the temple.",
			Pad = Vector2.new(51, -38),
			PriceSeconds = 1015,
			Pieces = {
				Cy(53, 0.6, -52, 2.4, 1.2, STONE, Marble),
				Cy(53, 7, -52, 0.8, 12, MARBLE, Marble),
				B(53, 13.4, -52, 3.6, 0.7, 0.7, GOLD, Metal),
				Ball(53, 15.2, -52, 3, 3, 3, SUN, Plastic),
				Cy(60, 0.6, -46, 2.4, 1.2, STONE, Marble),
				Cy(60, 5.4, -46, 0.8, 9, MARBLE, Marble),
				B(60, 10.6, -46, 3.4, 0.7, 0.7, GOLD, Metal),
				Ball(60, 12.4, -46, 3, 3, 3, SUN, Plastic),
				Cy(49, 0.6, -42, 2.4, 1.2, STONE, Marble),
				Cy(49, 4.8, -42, 0.8, 8, MARBLE, Marble),
				B(49, 9.2, -42, 3.2, 0.7, 0.7, GOLD, Metal),
				Ball(49, 10.9, -42, 2.8, 2.8, 2.8, SUN, Plastic),
			},
		},
		-- 22
		{
			Id = "DawnGong",
			Yaw = 26,
			Name = "Gong of Dawn",
			Description = "A golden gong hanging in a white frame, with a little mallet beside it.",
			Pad = Vector2.new(40, -2),
			PriceSeconds = 1167,
			Pieces = {
				B(42, 0.6, -8, 3, 1.2, 3, STONE, Marble),
				B(50, 0.6, -8, 3, 1.2, 3, STONE, Marble),
				Cy(42, 6.4, -8, 1.1, 10.4, MARBLE, Marble),
				Cy(50, 6.4, -8, 1.1, 10.4, MARBLE, Marble),
				B(46, 11.6, -8, 10, 1, 1.2, GOLD, Metal),
				Cz(46, 7.2, -8, 6.6, 0.6, GOLD, Metal),
				Cz(46, 7.2, -8.4, 7.6, 0.4, STONE, Metal),
				Cz(46, 7.2, -7.6, 3, 0.4, SUN, Metal),
				B(51.4, 1.6, -5, 0.5, 3.2, 0.5, WOOD, Wood, 0, 0, 20),
			},
		},
		-- 23
		{
			Id = "CherubPerches",
			Yaw = 10,
			Name = "Cherub Perches",
			Description = "Three little cherubs perched on cloud puffs, each a different height and facing a different way.",
			Pad = Vector2.new(-12, -12),
			PriceSeconds = 1342,
			Pieces = {
				Ball(-18, 1.2, -18, 6, 2.4, 5, WHITE, Concrete),
				Ball(-18, 3.6, -18, 2.6, 3, 2.6, SKIN, Plastic),
				Ball(-18, 5.8, -18, 2.2, 2.2, 2.2, SKIN, Plastic),
				B(-19.3, 4.6, -18.9, 1.8, 2.6, 0.4, WHITE, Marble, 0, 0, 20),
				B(-16.7, 4.6, -18.9, 1.8, 2.6, 0.4, WHITE, Marble, 0, 0, -20),
				Ball(-25, 2.2, -22, 6.4, 3.4, 5.4, WHITE, Concrete),
				Ball(-25, 5.4, -22, 2.8, 3.2, 2.8, SKIN, Plastic),
				Ball(-25, 7.6, -22, 2.3, 2.3, 2.3, SKIN, Plastic),
				B(-26.4, 6.6, -22.9, 2, 2.8, 0.4, WHITE, Marble, 0, 0, 20),
				B(-23.6, 6.6, -22.9, 2, 2.8, 0.4, WHITE, Marble, 0, 0, -20),
				Ball(-11, 1, -25, 5, 2, 4.4, WHITE, Concrete),
				Ball(-11, 3, -25, 2.3, 2.6, 2.3, SKIN, Plastic),
				Ball(-11, 4.9, -25, 2, 2, 2, SKIN, Plastic),
				B(-12.2, 4, -25.8, 1.6, 2.2, 0.4, WHITE, Marble, 0, 0, 20),
				B(-9.8, 4, -25.8, 1.6, 2.2, 0.4, WHITE, Marble, 0, 0, -20),
			},
		},
		-- 24
		{
			Id = "HaloMonument",
			Yaw = -12,
			Name = "Halo Monument",
			Description = "A tall marble stele carrying a big golden halo ring with four little gems.",
			Pad = Vector2.new(-36, -21),
			PriceSeconds = 1543,
			Pieces = {
				B(-30, 1, -30, 9, 2, 6, STONE, Marble),
				B(-30, 3, -30, 6, 2, 4, MARBLE, Marble),
				Cy(-30, 10, -30, 3, 12, MARBLE, Marble),
				Cz(-30, 19, -30, 13, 1.2, GOLD, Metal),
				Cz(-30, 19, -29.6, 9.6, 1.4, SKY, Glass),
				Ball(-30, 25.6, -30, 1.6, 1.6, 1.6, GOLD, Metal),
				Ball(-30, 13.9, -29.2, 1.4, 1.4, 1.4, ROSE, Plastic),
				Ball(-23.9, 19, -29.2, 1.4, 1.4, 1.4, ROSE, Plastic),
				Ball(-36.1, 19, -29.2, 1.4, 1.4, 1.4, ROSE, Plastic),
				Ball(-30, 24.1, -29.2, 1.4, 1.4, 1.4, ROSE, Plastic),
			},
		},
		-- 25
		{
			Id = "Observatory",
			Yaw = 22,
			Name = "Star Observatory",
			Description = "A round white observatory with a gold band, a rose dome and a telescope poking out of the slit.",
			Pad = Vector2.new(64, -32),
			PriceSeconds = 1775,
			Pieces = {
				Cy(68, 0.5, -42, 17, 1, STONE, Marble),
				Cy(68, 5, -42, 13, 8, CREAM, Marble),
				Cy(68, 9.4, -42, 14, 1, GOLD, Metal),
				Ball(68, 9.5, -42, 13.4, 11, 13.4, ROSE, Plastic),
				B(68, 5, -35.4, 3, 5, 0.5, GOLD, Metal),
				B(68, 11.5, -36.2, 1.6, 6, 1, SKY, Glass),
				Cy(70, 14, -37.6, 1.4, 8, STONE, Metal, 0),
				Ball(68, 15.6, -42, 1.6, 1.6, 1.6, GOLD, Metal),
			},
		},
		-- 26
		{
			Id = "ChoirRiser",
			Yaw = 8,
			Name = "Choir Risers",
			Description = "Three marble risers with a row of little singing angels and a golden music stand in front.",
			Pad = Vector2.new(-2, -22),
			PriceSeconds = 2041,
			Pieces = {
				B(0, 0.6, -30, 14, 1.2, 8, MARBLE, Marble),
				B(0, 1.8, -32, 11, 1.2, 5.5, MARBLE, Marble),
				B(0, 3, -33.5, 8, 1.2, 3, MARBLE, Marble),
				Cy(-4, 4, -31, 2, 3.2, WHITE, Fabric),
				Ball(-4, 6.2, -31, 1.8, 1.8, 1.8, SKIN, Plastic),
				Cy(-0.6, 4, -32, 2, 3.2, WHITE, Fabric),
				Ball(-0.6, 6.2, -32, 1.8, 1.8, 1.8, SKIN, Plastic),
				Cy(2.8, 4, -31, 2, 3.2, WHITE, Fabric),
				Ball(2.8, 6.2, -31, 1.8, 1.8, 1.8, SKIN, Plastic),
				Cy(-2, 6, -33.5, 2, 3.2, WHITE, Fabric),
				Ball(-2, 8.2, -33.5, 1.8, 1.8, 1.8, SKIN, Plastic),
				B(1, 2.6, -27, 1.2, 2.4, 0.6, GOLD, Metal),
				B(1, 3.9, -27, 2.6, 0.3, 1.4, GOLD, Metal, -25, 0, 0),
			},
		},
		-- 27
		{
			Id = "HeavenBell",
			Yaw = -20,
			Name = "Heaven Bell",
			Description = "A golden bell hanging in a white open frame under a little pink roof.",
			Pad = Vector2.new(-8, -43),
			PriceSeconds = 2347,
			Pieces = {
				B(-14, 0.5, -37, 10, 1, 5, STONE, Marble),
				Cy(-17.4, 6, -37, 1.2, 10, MARBLE, Marble),
				Cy(-10.6, 6, -37, 1.2, 10, MARBLE, Marble),
				B(-14, 11.2, -37, 10.6, 1, 3.6, ROSE, Plastic),
				B(-14, 12.4, -37, 6, 1.2, 2.4, ROSE, Plastic),
				Cy(-14, 6.4, -37, 4.4, 3.4, GOLD, Metal),
				Cy(-14, 8.4, -37, 2.8, 1, GOLD, Metal),
				Ball(-14, 4.3, -37, 1.4, 1.4, 1.4, STONE, Metal),
			},
		},
		-- 28
		{
			Id = "CloudThrone",
			Yaw = -12,
			Name = "Cloud Throne",
			Description = "A golden throne with white wings and a rose cushion on a two-tier cloud dais.",
			Pad = Vector2.new(50, -35),
			RewardMult = 1.5,
			PriceSeconds = 2699,
			Pieces = {
				Cy(52, 0.8, -25, 11, 1.6, WHITE, Marble),
				Cy(52, 2.1, -25, 8, 1, MARBLE, Marble),
				B(52, 3.9, -25, 5, 2.6, 4.6, GOLD, Metal),
				B(52, 8, -27, 5.4, 8, 1, GOLD, Metal),
				B(52, 5, -25, 4, 0.9, 3.6, ROSE, Fabric),
				B(49.3, 5, -25, 0.7, 2, 4, GOLD, Metal),
				B(54.7, 5, -25, 0.7, 2, 4, GOLD, Metal),
				B(48.2, 9, -27.6, 3.4, 6.6, 0.6, WHITE, Marble, 0, 0, 22),
				B(55.8, 9, -27.6, 3.4, 6.6, 0.6, WHITE, Marble, 0, 0, -22),
				Ball(52, 12.6, -27, 1.8, 1.8, 1.8, GOLD, Metal),
				Ball(46.6, 1.2, -23, 5, 2.4, 4, WHITE, Concrete),
				Ball(57.6, 1, -28, 4.6, 2, 4, WHITE, Concrete),
			},
		},
		-- 29
		{
			Id = "SkySpire",
			Yaw = 12,
			Name = "Sky Spire",
			Description = "The tall bell spire of the heavens: a stepped marble tower with gold bands, a belfry and a golden needle.",
			Pad = Vector2.new(-56, -22),
			RewardMult = 1.5,
			PriceSeconds = 3104,
			Pieces = {
				B(-66, 1.2, -22, 15, 2.4, 15, STONE, Marble),
				B(-66, 8.4, -22, 11.4, 12, 11.4, MARBLE, Marble),
				B(-66, 15, -22, 13, 1.2, 13, GOLD, Metal),
				B(-66, 26, -22, 8.8, 20, 8.8, CREAM, Marble),
				B(-66, 36.4, -22, 12, 1.6, 12, GOLD, Metal),
				B(-66, 41.8, -22, 7.6, 9.2, 7.6, CLOUD, Marble),
				B(-66, 47, -22, 10, 1.2, 10, ROSE, Plastic),
				B(-66, 49.4, -22, 6.4, 3.6, 6.4, ROSE, Plastic),
				Cy(-66, 53.1, -22, 1, 3.8, GOLD, Metal),
				Ball(-70, 1.4, -17, 6, 2.8, 5, WHITE, Concrete),
				Ball(-61.5, 1.2, -27, 5, 2.4, 4.4, WHITE, Concrete),
			},
		},
		-- 30
		{
			Id = "Stairway",
			Yaw = 0,
			Name = "Stairway to Heaven",
			Description = "A spiral of floating marble steps winding around a golden pole up into the sky.",
			Pad = Vector2.new(62, -14),
			RewardMult = 1.5,
			PriceSeconds = 3570,
			Pieces = {
				Cy(70, 11, -22, 1.2, 22, GOLD, Metal),
				B(72.8, 1.6, -22, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 0, 0),
				B(72.2, 3.4, -19.4, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 60, 0),
				B(70, 5.2, -17.8, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 120, 0),
				B(67.4, 7, -17.8, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 180, 0),
				B(65.2, 8.8, -19.4, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 240, 0),
				B(64.4, 10.6, -22, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 300, 0),
				B(65.2, 12.4, -24.6, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 0, 0),
				B(67.4, 14.2, -26.2, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 60, 0),
				B(70, 16, -26.2, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 120, 0),
				B(72.2, 17.8, -24.6, 4.6, 0.9, 2.6, MARBLE, Marble, 0, 180, 0),
				Ball(70, 1.2, -22, 9, 2.4, 8, WHITE, Concrete),
				Ball(70, 23.4, -22, 5, 3.4, 5, WHITE, Concrete),
			},
		},
	},
}

return theme
