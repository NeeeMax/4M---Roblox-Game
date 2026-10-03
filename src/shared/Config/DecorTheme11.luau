--!strict
-- Theme of the Shiba of bay 11: Knight Castle (Config/DecorTypes -> Theme). 190 x 130: Knight Shiba stands in the front left on a
-- sand yard right before a twin-tower barbican gate; behind it, across a causeway and a drawbridge, a walled island keep sits in
-- a moat at the back left. A long winding walkway leads past a fountain, a round table, a tournament ground, a trebuchet and a
-- windmill on the right. Stage frame: +X right, -Z deeper, +Z toward the road. No glow: all plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local STONE = C(150, 152, 158)
local DARK_STONE = C(104, 108, 116)
local LIGHT_STONE = C(196, 198, 200)
local ROOF = C(46, 84, 150)
local RED = C(176, 42, 46)
local GOLD = C(232, 182, 52)
local WOOD = C(122, 86, 56)
local DARK_WOOD = C(80, 56, 40)
local IRON = C(60, 62, 70)
local STEEL = C(176, 184, 196)
local GRASS = C(92, 150, 66)
local HEDGE = C(52, 112, 56)
local WATER = C(60, 128, 176)
local SAND = C(214, 196, 150)
local CREAM = C(232, 224, 200)
local HAY = C(214, 180, 80)
local FUR = C(150, 104, 66)

local Slate = Enum.Material.Slate
local Cobble = Enum.Material.Cobblestone
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass
local Sand = Enum.Material.Sand

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

-- Cylinder lying along Z (a target, a hub): diameter d, thickness len.
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

local function merge(...: Pieces): Pieces
	local out: Pieces = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

local function rot(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
end

-- A heraldic banner on a pole standing at (x, z).
local function banner(x: number, z: number, cloth: Color3): Pieces
	return {
		Cy(x, 7.5, z, 0.7, 15, DARK_WOOD, Wood),
		B(x, 10.5, z, 3.8, 7, 0.3, cloth, Fabric),
	}
end

local theme: DecorTypes.Theme = {
	Key = "KnightCastle",
	Name = "Knight Castle",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-60, 22), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(50, 50),
		Vector2.new(-4, 36),
		Vector2.new(-40, 30),
		Vector2.new(-14, 8),
		Vector2.new(40, -12),
		Vector2.new(60, -40),
		Vector2.new(24, -50),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-71, 22),
	AutoPad = Vector2.new(-49, 22),
	Parts = {
		{
			Id = "Ground",
			Name = "Castle Grounds",
			Description = "A green lawn, a sand yard before the gate and a flagstone island in a deep blue moat.",
			Pad = Vector2.new(10, 52),
			PriceSeconds = 27,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, GRASS, Grass),
				B(-60, 0.3, -42, 42, 0.6, 32, LIGHT_STONE, Cobble),
				B(-60, 0.22, -61, 54, 0.4, 6, WATER, Plastic),
				B(-60, 0.22, -23, 54, 0.4, 6, WATER, Plastic),
				B(-84, 0.22, -42, 6, 0.4, 32, WATER, Plastic),
				B(-36, 0.22, -42, 6, 0.4, 32, WATER, Plastic),
				B(-60, 0.25, 24, 36, 0.2, 18, SAND, Sand),
			},
		},
		{
			Id = "Gatehouse",
			Name = "Barbican Gate",
			Description = "Twin round towers with blue roofs and a high arch: the Knight Shiba guards the castle gate.",
			Pad = Vector2.new(-84, 16),
			PriceSeconds = 31,
			Pieces = {
				B(-80, 5, 5, 12, 10, 8, STONE, Cobble),
				B(-40, 5, 5, 12, 10, 8, STONE, Cobble),
				Cy(-69, 11, 5, 10, 22, STONE, Cobble),
				Cy(-51, 11, 5, 10, 22, STONE, Cobble),
				Cy(-69, 25.5, 5, 11.4, 7, ROOF, Slate),
				Cy(-51, 25.5, 5, 11.4, 7, ROOF, Slate),
				B(-60, 15, 5, 10, 8, 16, STONE, Cobble),
				B(-60, 19.7, 5, 12, 1.4, 17, DARK_STONE, Cobble),
				Cy(-69, 32.5, 5, 0.6, 7, DARK_WOOD, Wood),
				Cy(-51, 32.5, 5, 0.6, 7, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Banners",
			Yaw = 10,
			Name = "Heraldic Banners",
			Description = "Four tall banners of the royal house, red and blue, flapping around the knight's yard.",
			Pad = Vector2.new(-60, 44),
			PriceSeconds = 36,
			Pieces = merge(banner(-78, 35, RED), banner(-72, 42, ROOF), banner(-52, 46, ROOF), banner(-47, 42, RED)),
		},
		{
			Id = "Drawbridge",
			Name = "Drawbridge",
			Description = "A heavy plank drawbridge on iron chains between two gate posts, over the moat.",
			Pad = Vector2.new(-72, -12),
			PriceSeconds = 42,
			Pieces = {
				B(-60, 0.3, -22, 10, 0.5, 12, WOOD, Planks),
				Cy(-66.4, 5, -14.5, 1.6, 10, DARK_WOOD, Wood),
				Cy(-53.6, 5, -14.5, 1.6, 10, DARK_WOOD, Wood),
				Ball(-66.4, 10.6, -14.5, 2, 2, 2, GOLD, Metal),
				Ball(-53.6, 10.6, -14.5, 2, 2, 2, GOLD, Metal),
				B(-65.7, 5, -21.2, 0.4, 0.4, 16.2, IRON, Metal, rot(-33.7, 0, 0)),
				B(-54.3, 5, -21.2, 0.4, 0.4, 16.2, IRON, Metal, rot(-33.7, 0, 0)),
			},
		},
		{
			Id = "Market",
			Yaw = -12,
			Name = "Village Market",
			Description = "Three striped stalls, a hand cart, barrels and crates: the village sells apples and swords.",
			Pad = Vector2.new(8, -32),
			PriceSeconds = 48,
			Pieces = {
				B(-14, 1.6, -35, 6, 3.2, 2.6, WOOD, Planks),
				B(-14, 6, -35, 7.2, 0.6, 5.4, RED, Fabric),
				B(-6, 1.6, -35, 6, 3.2, 2.6, WOOD, Planks),
				B(-6, 6, -35, 7.2, 0.6, 5.4, ROOF, Fabric),
				B(2, 1.6, -35, 6, 3.2, 2.6, WOOD, Planks),
				B(2, 6, -35, 7.2, 0.6, 5.4, GOLD, Fabric),
				B(-9, 1.4, -30, 5, 1.6, 2.8, DARK_WOOD, Planks),
				Cz(-11.4, 1.1, -30, 2.2, 0.4, WOOD, Wood),
				Cz(-6.6, 1.1, -30, 2.2, 0.4, WOOD, Wood),
				Cy(0, 1.2, -30.5, 2, 2.4, WOOD, Wood),
				Cy(2.4, 1.2, -29.5, 2, 2.4, WOOD, Wood),
				B(-15, 0.9, -30, 1.8, 1.8, 1.8, HAY, Planks),
				B(-13, 0.9, -29.2, 1.8, 1.8, 1.8, WOOD, Planks),
			},
		},
		{
			Id = "Walls",
			Name = "Curtain Walls",
			Description = "Thick grey walls with corner towers and a gate arch ring the island: the keep waits inside.",
			Pad = Vector2.new(-28, -32),
			PriceSeconds = 55,
			Pieces = {
				B(-60, 4, -56.5, 42, 8, 3, STONE, Cobble),
				B(-79.5, 4, -42, 3, 8, 32, STONE, Cobble),
				B(-40.5, 4, -42, 3, 8, 32, STONE, Cobble),
				B(-73.5, 4, -27.5, 15, 8, 3, STONE, Cobble),
				B(-46.5, 4, -27.5, 15, 8, 3, STONE, Cobble),
				Cy(-78, 7, -56, 8, 14, STONE, Cobble),
				Cy(-42, 7, -56, 8, 14, STONE, Cobble),
				Cy(-78, 7, -28, 8, 14, STONE, Cobble),
				Cy(-42, 7, -28, 8, 14, STONE, Cobble),
				Cy(-78, 17, -56, 9, 6, ROOF, Slate),
				Cy(-42, 17, -56, 9, 6, ROOF, Slate),
				Cy(-78, 17, -28, 9, 6, ROOF, Slate),
				Cy(-42, 17, -28, 9, 6, ROOF, Slate),
				Cy(-66, 5.5, -27.5, 6, 11, STONE, Cobble),
				Cy(-54, 5.5, -27.5, 6, 11, STONE, Cobble),
			},
		},
		{
			Id = "Armory",
			Yaw = 14,
			Name = "Royal Armory",
			Description = "A stone smithy with a chimney, a glowing forge, an anvil and racks of swords and shields.",
			Pad = Vector2.new(-4, 54),
			PriceSeconds = 63,
			Pieces = {
				B(-20, 0.2, 54, 16, 0.4, 12, DARK_STONE, Slate),
				B(-20, 3.5, 48.9, 16, 7, 1.4, STONE, Cobble),
				B(-27.3, 3.5, 54, 1.4, 7, 12, STONE, Cobble),
				B(-12.7, 3.5, 54, 1.4, 7, 12, STONE, Cobble),
				B(-20, 7.5, 54, 18, 0.8, 13, ROOF, Slate, rot(-12, 0, 0)),
				B(-24, 9.5, 50, 3, 5, 3, DARK_STONE, Cobble),
				B(-24.5, 1.5, 51.5, 3.5, 3, 3, DARK_STONE, Cobble),
				B(-19, 1.4, 55, 3, 2.2, 1.6, IRON, Metal),
				B(-17, 2.7, 49.8, 8, 4.4, 0.5, DARK_WOOD, Wood),
				Cy(-14.5, 1.4, 58, 2.2, 2.8, WOOD, Wood),
			},
		},
		{
			Id = "Stables",
			Yaw = -18,
			Name = "Royal Stables",
			Description = "A timber barn with hay and a trough, a brown war horse and a fenced yard.",
			Pad = Vector2.new(-66, 52),
			PriceSeconds = 73,
			Pieces = {
				B(-80, 3, 50.8, 20, 6, 1.2, WOOD, Planks),
				B(-89.4, 3, 56, 1.2, 6, 12, WOOD, Planks),
				B(-70.6, 3, 53, 1.2, 6, 6, WOOD, Planks),
				B(-80, 6.6, 55.5, 21, 0.8, 13, RED, Planks, rot(-14, 0, 0)),
				Ball(-85, 1.6, 54, 4, 3.2, 3.6, HAY, Grass),
				B(-76, 1, 58.5, 6, 1.4, 1.4, DARK_WOOD, Wood),
				B(-80, 3, 59.5, 5, 2.6, 2, FUR, Fabric),
				B(-77, 4.4, 59.5, 1.6, 2.4, 1.4, FUR, Fabric, rot(0, 0, -25)),
				B(-80, 0.9, 61.6, 20, 1.2, 0.4, WOOD, Planks),
				Cy(-90, 1.8, 61.6, 0.8, 3.6, DARK_WOOD, Wood),
				Cy(-70, 1.8, 61.6, 0.8, 3.6, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Training",
			Yaw = 12,
			Name = "Training Yard",
			Description = "Straw dummies with wooden shields, hay bales, a practice target and a rack of wooden swords.",
			Pad = Vector2.new(-34, 56),
			PriceSeconds = 85,
			Pieces = {
				Cy(-53, 2.5, 52, 0.9, 5, WOOD, Wood),
				B(-53, 3.8, 52, 3, 0.5, 0.6, WOOD, Wood),
				Cy(-47, 2.5, 57, 0.9, 5, WOOD, Wood),
				B(-47, 3.8, 57, 3, 0.5, 0.6, WOOD, Wood),
				Cy(-42, 2.5, 51, 0.9, 5, WOOD, Wood),
				B(-42, 3.8, 51, 3, 0.5, 0.6, WOOD, Wood),
				B(-55, 1, 57, 2.4, 1.8, 1.8, HAY, Planks),
				B(-52.4, 1, 58.4, 2.4, 1.8, 1.8, HAY, Planks),
				B(-40.5, 1, 56, 1.8, 1.8, 2.4, HAY, Planks),
				B(-48, 1.4, 49, 7, 2.8, 0.6, DARK_WOOD, Wood),
				Cz(-41, 3.2, 59, 3.6, 0.5, RED, Wood),
				Cy(-41, 1.6, 59, 0.6, 3.2, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Fountain",
			Name = "Courtyard Fountain",
			Description = "A round stone fountain with a stone knight on top, four little pillars and clear blue water.",
			Pad = Vector2.new(6, 20),
			PriceSeconds = 98,
			Pieces = {
				Cy(18, 1, 20, 14, 2, LIGHT_STONE, Cobble),
				Cy(18, 1.9, 20, 12.2, 0.4, WATER, Plastic),
				Cy(18, 5, 20, 3.4, 6, STONE, Cobble),
				Cy(18, 8.4, 20, 7.5, 1.2, LIGHT_STONE, Cobble),
				Cy(18, 11, 20, 1.6, 4, STONE, Cobble),
				B(18, 14.5, 20, 2.4, 5, 1.8, STEEL, Metal),
				Ball(18, 17.6, 20, 2, 2, 2, STEEL, Metal),
				Cy(11.6, 2.2, 13.6, 1, 4.4, STONE, Cobble),
				Cy(24.4, 2.2, 13.6, 1, 4.4, STONE, Cobble),
				Cy(11.6, 2.2, 26.4, 1, 4.4, STONE, Cobble),
				Cy(24.4, 2.2, 26.4, 1, 4.4, STONE, Cobble),
			},
		},
		{
			Id = "Pavilion",
			Yaw = -20,
			Name = "Royal Pavilion",
			Description = "A striped tent with a golden pole and a pennant, a throne inside and a red rug.",
			Pad = Vector2.new(62, 44),
			PriceSeconds = 113,
			Pieces = {
				B(78, 2.5, 42, 14, 5, 0.8, CREAM, Fabric),
				B(71, 2.5, 48, 0.8, 5, 12, CREAM, Fabric),
				B(85, 2.5, 48, 0.8, 5, 12, CREAM, Fabric),
				B(74, 8.5, 48, 10.6, 0.6, 13, RED, Fabric, rot(0, 0, 41)),
				B(82, 8.5, 48, 10.6, 0.6, 13, ROOF, Fabric, rot(0, 0, -41)),
				Cy(78, 16, 48, 0.7, 10, GOLD, Metal),
				B(79.4, 19.5, 48, 2.8, 1.8, 0.2, RED, Fabric),
				B(78, 2, 44, 3, 4, 2, GOLD, Metal),
				B(78, 0.2, 50, 6, 0.4, 8, RED, Fabric),
				B(74, 1.4, 50, 3, 1.6, 2, WOOD, Planks),
			},
		},
		{
			Id = "Archery",
			Yaw = 10,
			Name = "Archery Range",
			Description = "Three round targets before a hay backstop, a rope line to shoot from and a quiver rack.",
			Pad = Vector2.new(62, 6),
			PriceSeconds = 130,
			Pieces = {
				B(78, 1.8, -12, 22, 3.6, 1.6, HAY, Planks),
				B(70, 2.6, -9.2, 0.8, 5.2, 0.8, DARK_WOOD, Wood),
				B(78, 2.6, -9.2, 0.8, 5.2, 0.8, DARK_WOOD, Wood),
				B(86, 2.6, -9.2, 0.8, 5.2, 0.8, DARK_WOOD, Wood),
				Cz(70, 5.4, -8.4, 5, 0.6, CREAM, Wood),
				Cz(78, 5.4, -8.4, 5, 0.6, CREAM, Wood),
				Cz(86, 5.4, -8.4, 5, 0.6, CREAM, Wood),
				Cz(78, 5.4, -8, 1.8, 0.4, RED, Wood),
				B(78, 0.7, 1, 20, 0.5, 0.4, WOOD, Wood),
				Cy(68, 1.2, 1, 0.6, 2.4, DARK_WOOD, Wood),
				Cy(88, 1.2, 1, 0.6, 2.4, DARK_WOOD, Wood),
				B(66.5, 1.6, -3, 1.2, 3.2, 3, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Garden",
			Yaw = -14,
			Name = "Rose Garden",
			Description = "Clipped green hedges around red and yellow rose beds, a white rose arch and a stone bench.",
			Pad = Vector2.new(12, -26),
			PriceSeconds = 150,
			Pieces = {
				B(24, 1.8, -35, 16, 3.6, 1.6, HEDGE, Grass),
				B(16.8, 1.8, -30, 1.6, 3.6, 10, HEDGE, Grass),
				B(31.2, 1.8, -30, 1.6, 3.6, 10, HEDGE, Grass),
				B(18.5, 1.8, -24.8, 5, 3.6, 1.6, HEDGE, Grass),
				B(29.5, 1.8, -24.8, 5, 3.6, 1.6, HEDGE, Grass),
				B(21.2, 2.4, -24.8, 0.8, 4.8, 0.8, CREAM, Wood),
				B(26.8, 2.4, -24.8, 0.8, 4.8, 0.8, CREAM, Wood),
				B(24, 5.2, -24.8, 6.8, 0.8, 0.8, CREAM, Wood),
				B(24, 0.5, -30.5, 6, 1, 5, RED, Grass),
				Cy(24, 1.8, -30.5, 2, 3.6, STONE, Cobble),
				B(19.5, 1, -33, 3.4, 1, 1.4, LIGHT_STONE, Cobble),
			},
		},
		{
			Id = "Chapel",
			Yaw = 8,
			Name = "Castle Chapel",
			Description = "A little stone chapel with a blue roof, a round apse, a tall bell tower and a golden cross.",
			Pad = Vector2.new(0, -46),
			PriceSeconds = 173,
			Pieces = {
				B(-12, 4.5, -49, 10, 9, 10, CREAM, Cobble),
				B(-15, 11.5, -49, 7.8, 0.6, 11.4, ROOF, Slate, rot(0, 0, 40)),
				B(-9, 11.5, -49, 7.8, 0.6, 11.4, ROOF, Slate, rot(0, 0, -40)),
				B(-12, 10, -43.5, 4.6, 20, 4.6, STONE, Cobble),
				Cy(-12, 23.5, -43.5, 4.6, 7, ROOF, Slate),
				B(-12, 28.5, -43.5, 0.4, 2.4, 0.4, GOLD, Metal),
				Cy(-12, 3.5, -54, 7, 7, CREAM, Cobble),
				B(-12, 3, -40.6, 3, 5, 0.6, DARK_WOOD, Wood),
				B(-17.4, 3, -49, 1, 6, 1.4, STONE, Cobble),
				B(-6.6, 3, -49, 1, 6, 1.4, STONE, Cobble),
			},
		},
		{
			Id = "Lists",
			Yaw = 14,
			RewardMult = 1.6,
			Name = "Tournament Lists",
			Description = "A striped jousting barrier in a sand arena, a covered grandstand and lances in a rack.",
			Pad = Vector2.new(62, 34),
			PriceSeconds = 200,
			Pieces = {
				B(76, 0.2, 24, 28, 0.4, 12, SAND, Sand),
				B(76, 1.8, 24, 26, 3.6, 0.7, RED, Planks),
				Cy(63.5, 6, 24, 0.6, 12, DARK_WOOD, Wood),
				Cy(88.5, 6, 24, 0.6, 12, DARK_WOOD, Wood),
				B(65.2, 10.8, 24, 2.8, 1.8, 0.2, RED, Fabric),
				B(86.8, 10.8, 24, 2.8, 1.8, 0.2, ROOF, Fabric),
				B(76, 1.5, 19.5, 24, 3, 3, WOOD, Planks),
				B(76, 6.5, 19.5, 24, 0.6, 4.5, ROOF, Fabric),
				B(64.4, 3.2, 18.3, 0.7, 6.4, 0.7, DARK_WOOD, Wood),
				B(87.6, 3.2, 18.3, 0.7, 6.4, 0.7, DARK_WOOD, Wood),
				B(76, 4.6, 19, 4, 3.2, 2.4, GOLD, Metal),
				B(70, 3, 28.5, 0.3, 6, 0.3, WOOD, Wood, rot(0, 0, 14)),
				B(72, 3, 28.5, 0.3, 6, 0.3, WOOD, Wood, rot(0, 0, -14)),
			},
		},
		{
			Id = "Keep",
			RewardMult = 1.3,
			Name = "Great Keep",
			Description = "The king's tall stone keep with four round corner turrets, blue roofs and a royal flag on top.",
			Pad = Vector2.new(-28, -52),
			PriceSeconds = 230,
			Pieces = {
				B(-60, 12, -44, 24, 24, 20, STONE, Cobble),
				B(-60, 24.7, -44, 26, 1.4, 22, DARK_STONE, Cobble),
				Cy(-72, 16, -54, 6.4, 32, STONE, Cobble),
				Cy(-48, 16, -54, 6.4, 32, STONE, Cobble),
				Cy(-72, 16, -34, 6.4, 32, STONE, Cobble),
				Cy(-48, 16, -34, 6.4, 32, STONE, Cobble),
				Cy(-72, 35.5, -54, 7.4, 7, ROOF, Slate),
				Cy(-48, 35.5, -54, 7.4, 7, ROOF, Slate),
				Cy(-72, 35.5, -34, 7.4, 7, ROOF, Slate),
				Cy(-48, 35.5, -34, 7.4, 7, ROOF, Slate),
				B(-60, 31, -46, 10, 12, 10, STONE, Cobble),
				Cy(-60, 39.5, -46, 11, 5, ROOF, Slate),
				Cy(-60, 45, -46, 0.5, 7, DARK_WOOD, Wood),
				B(-60, 3, -33.5, 6, 6, 1.5, DARK_WOOD, Wood),
				B(-60, 0.6, -32, 9, 1.2, 2, DARK_STONE, Cobble),
			},
		},
		{
			Id = "Windmill",
			Yaw = 12,
			Name = "Village Windmill",
			Description = "A stone windmill with a blue cap and big wooden sails, flour sacks by the door.",
			Pad = Vector2.new(66, -50),
			PriceSeconds = 266,
			Pieces = {
				B(80, 3, -54, 12, 6, 10, STONE, Cobble),
				Cy(80, 13, -54, 8, 14, CREAM, Cobble),
				Cy(80, 21.5, -54, 9.4, 3, ROOF, Slate),
				Cz(80, 19.5, -48.4, 2.4, 2, IRON, Metal),
				B(80, 19.5, -47.6, 20, 1.6, 0.5, WOOD, Planks, rot(0, 0, 35)),
				B(80, 19.5, -47.6, 20, 1.6, 0.5, WOOD, Planks, rot(0, 0, -55)),
				B(80, 2.4, -48.6, 2.6, 4.4, 0.4, DARK_WOOD, Wood),
				B(75, 1, -48.8, 1.6, 2, 1.4, HAY, Fabric),
				B(85, 1, -48.8, 1.6, 2, 1.4, CREAM, Fabric),
			},
		},
		{
			Id = "RoundTable",
			Yaw = 20,
			Name = "Round Table Hall",
			Description = "An open pavilion on four pillars with a golden roof, a big round table and four knight chairs.",
			Pad = Vector2.new(32, 10),
			PriceSeconds = 306,
			Pieces = {
				Cy(44, 2.6, 24, 9, 1.2, WOOD, Wood),
				Cy(44, 1, 24, 3, 2, DARK_WOOD, Wood),
				Cy(37, 5, 17, 1.4, 10, STONE, Cobble),
				Cy(51, 5, 17, 1.4, 10, STONE, Cobble),
				Cy(37, 5, 31, 1.4, 10, STONE, Cobble),
				Cy(51, 5, 31, 1.4, 10, STONE, Cobble),
				Cy(44, 11.5, 24, 17, 2.4, ROOF, Slate),
				Cy(44, 13.8, 24, 6, 2.2, GOLD, Metal),
				Cy(44, 17, 24, 0.5, 4, IRON, Metal),
				B(45.4, 18, 24, 2.8, 1.8, 0.2, RED, Fabric),
				B(38.5, 1.6, 24, 1.6, 3.2, 1.6, DARK_WOOD, Wood),
				B(49.5, 1.6, 24, 1.6, 3.2, 1.6, DARK_WOOD, Wood),
				B(44, 1.6, 18.5, 1.6, 3.2, 1.6, DARK_WOOD, Wood),
				B(44, 1.6, 29.5, 1.6, 3.2, 1.6, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Trebuchet",
			Yaw = -16,
			RewardMult = 1.5,
			Name = "Siege Trebuchet",
			Description = "A huge wooden trebuchet with a stone counterweight and a pile of boulders ready to fly.",
			Pad = Vector2.new(66, -24),
			PriceSeconds = 353,
			Pieces = {
				B(78, 0.6, -33, 20, 1.2, 1.2, DARK_WOOD, Wood),
				B(78, 0.6, -23, 20, 1.2, 1.2, DARK_WOOD, Wood),
				B(72, 0.6, -28, 1.2, 1.2, 12, DARK_WOOD, Wood),
				B(84, 0.6, -28, 1.2, 1.2, 12, DARK_WOOD, Wood),
				B(75.5, 7.5, -23, 1, 15.8, 1, WOOD, Wood, rot(0, 0, -18.4)),
				B(80.5, 7.5, -23, 1, 15.8, 1, WOOD, Wood, rot(0, 0, 18.4)),
				B(75.5, 7.5, -33, 1, 15.8, 1, WOOD, Wood, rot(0, 0, -18.4)),
				B(80.5, 7.5, -33, 1, 15.8, 1, WOOD, Wood, rot(0, 0, 18.4)),
				Cy(78, 15, -28, 1.2, 12, IRON, Metal),
				B(80, 15, -28, 24, 1.2, 1.2, WOOD, Wood, rot(0, 0, 25)),
				B(72.5, 8, -28, 4.4, 4.4, 5, DARK_STONE, Cobble),
				Ball(89.6, 19.6, -28, 2.4, 2.4, 2.4, STONE, Cobble),
				Ball(86, 1.2, -29, 2.6, 2.4, 2.6, STONE, Cobble),
				Ball(88, 1, -26, 2.2, 2, 2.2, STONE, Cobble),
			},
		},
		{
			Id = "Excalibur",
			Yaw = 10,
			RewardMult = 2,
			Name = "Sword in the Stone",
			Description = "The showpiece: a giant sword of steel and gold stuck in a mossy rock, waiting for the true king.",
			Pad = Vector2.new(2, -18),
			PriceSeconds = 408,
			Pieces = {
				Ball(-12, 3, -17, 13, 6, 13, STONE, Cobble),
				Ball(-14.5, 2, -13.5, 6, 4, 6, DARK_STONE, Cobble),
				Ball(-8, 1.6, -13, 5, 3.2, 5, STONE, Cobble),
				B(-12, 15, -17, 1.8, 18, 0.5, STEEL, Metal),
				B(-12, 24.5, -17, 7, 1.2, 1, GOLD, Metal),
				Cy(-12, 27, -17, 0.9, 3.4, DARK_WOOD, Wood),
				Ball(-12, 29, -17, 1.8, 1.8, 1.8, GOLD, Metal),
				B(-12, 0.4, -10.6, 8, 0.8, 1.6, LIGHT_STONE, Cobble),
				B(-12, 0.4, -9.6, 11, 0.8, 1.4, LIGHT_STONE, Cobble),
				Ball(-18, 0.8, -20, 2.4, 1.6, 2.4, STONE, Cobble),
				Ball(-6, 0.8, -21, 2.4, 1.6, 2.4, STONE, Cobble),
			},
		},
	},
}

return theme
