--!strict
-- Theme of the Shiba of bay 9: Ninja Dojo (Config/DecorTypes -> Theme). 190 x 130, a big pagoda dojo with the Ninja Shiba standing
-- inside its open front hall, a red gate over the first stretch of the walkway, gardens and training grounds all over the plot.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lamps and the moon are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local WOOD_D = C(70, 48, 40)
local WOOD_M = C(122, 84, 54)
local RED = C(190, 40, 45)
local BLACK = C(32, 32, 40)
local PAPER = C(240, 232, 205)
local ROOF = C(52, 58, 80)
local STONE = C(140, 140, 150)
local STONE_D = C(96, 98, 110)
local SAND = C(224, 210, 172)
local GOLD = C(255, 205, 70)
local STEEL = C(190, 195, 205)
local STRAW = C(214, 182, 110)
local PINK = C(255, 170, 200)
local GREEN = C(70, 130, 70)
local BAMBOO = C(112, 172, 82)
local WATER = C(70, 140, 190)
local ORANGE = C(240, 130, 50)
local WHITE = C(245, 245, 245)
local WARM = C(255, 214, 140)

local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Slate = Enum.Material.Slate
local Pebble = Enum.Material.Pebble
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass
local Sandy = Enum.Material.Sand
local Plastic = Enum.Material.SmoothPlastic
local Metal = Enum.Material.Metal
local Concrete = Enum.Material.Concrete

-- Block standing on y0 (bottom), centred on (cx, cz).
local function Bx(
	cx: number,
	y0: number,
	cz: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(cx, y0 + sy / 2, cz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
	}
end

-- Standing cylinder on y0: diameter d, height h.
local function Cy(cx: number, y0: number, cz: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(cx, y0 + h / 2, cz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along Z (a drum, a target): centre (cx, cy, cz), diameter d, length len.
local function Cz(cx: number, cy: number, cz: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(cx, cy, cz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

local function Bl(
	cx: number,
	cy: number,
	cz: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(cx, cy, cz),
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

local function dummy(x: number, z: number): Pieces
	return {
		Cy(x, 0, z, 0.9, 5.6, WOOD_D, Wood),
		Cy(x, 1.2, z, 2.2, 3.2, STRAW, Fabric),
		Bx(x, 3.4, z, 5.2, 0.6, 0.8, WOOD_M, Wood),
		Bl(x, 6.6, z, 1.9, 1.9, 1.9, STRAW, Fabric),
	}
end

local function lantern(x: number, z: number): Pieces
	return {
		Cy(x, 0, z, 2, 0.8, STONE, Slate),
		Cy(x, 0.8, z, 0.9, 2.6, STONE, Slate),
		Bx(x, 3.4, z, 1.7, 1.4, 1.7, WARM, Plastic),
		Bx(x, 4.8, z, 3, 0.6, 3, ROOF, Slate),
	}
end

local function banner(x: number): Pieces
	return {
		Bx(x, 0, -51, 2.4, 1, 2.4, STONE, Slate),
		Cy(x, 1, -51, 0.7, 11, WOOD_D, Wood),
		Bx(x, 11.2, -50.6, 5, 0.5, 0.5, WOOD_D, Wood),
		Bx(x, 3, -50.6, 3.8, 8.2, 0.2, RED, Fabric),
		Bl(x, 7.4, -50.4, 2.4, 2.4, 0.2, WHITE, Fabric),
	}
end

local function cherry(x: number, z: number): Pieces
	return {
		Cy(x, 0, z, 1.8, 4.8, WOOD_D, Wood),
		Bl(x, 7.4, z, 10, 6.4, 10, PINK, Grass),
		Bl(x - 2.4, 9.4, z + 0.6, 6, 4, 6, C(255, 190, 215), Grass),
	}
end

local function target(x: number): Pieces
	return {
		Cy(x, 0, 0, 0.8, 3.2, WOOD_D, Wood),
		Cz(x, 5, 0, 5.2, 0.7, STRAW, Fabric),
		Cz(x, 5, 0.5, 3.4, 0.2, RED, Plastic),
		Cz(x, 5, 0.62, 1.4, 0.15, GOLD, Plastic),
	}
end

local function bambooStalks(): Pieces
	local list = {
		{ 83, 16, 15 },
		{ 87, 15, 18 },
		{ 90, 18, 13 },
		{ 84, 21, 19 },
		{ 88, 23, 16 },
		{ 91, 26, 14 },
		{ 82.5, 26, 12 },
		{ 86, 28, 20 },
		{ 90, 31, 17 },
		{ 83.5, 32, 14 },
		{ 88, 34, 19 },
		{ 85, 36, 15 },
		{ 91, 37, 12 },
		{ 82.5, 38, 17 },
	}
	local out: Pieces = { Bx(86.5, 0, 26, 12, 0.3, 26, C(60, 100, 60), Grass) }
	for _, s in list do
		table.insert(out, Cy(s[1] :: number, 0.3, s[2] :: number, 0.9, (s[3] :: number) - 0.3, BAMBOO, Wood))
	end
	return out
end

local function shuriken(x: number, y: number, z: number, size: number): Pieces
	return {
		Bx(x, y - size / 2, z, size, size * 0.1, 0.5, STEEL, Metal),
		Bx(x, y - size / 2, z, size * 0.1, size, 0.5, STEEL, Metal),
		Bl(x, y, z, size * 0.3, size * 0.3, 0.8, RED, Plastic),
	}
end

local theme: DecorTypes.Theme = {
	Key = "NinjaDojo",
	Name = "Ninja Dojo",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(61, -34), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(0, 48),
		Vector2.new(-52, 34),
		Vector2.new(40, 16),
		Vector2.new(-44, -6),
		Vector2.new(36, -18),
		Vector2.new(0, -48),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(84, -34),
	AutoPad = Vector2.new(40, -30),
	Parts = {
		{
			Id = "Floor",
			Name = "Dojo Grounds",
			Description = "Dark stone, raked gravel and wooden decks: the training grounds of the whole dojo.",
			Pad = Vector2.new(24, 58),
			PriceSeconds = 14,
			Pieces = {
				Bx(0, 0, 0, 176, 0.3, 120, C(58, 66, 70), Slate),
				Bx(0, 0.3, 30, 150, 0.1, 50, C(176, 176, 182), Pebble),
				Bx(-45, 0.3, -30, 76, 0.1, 52, C(176, 176, 182), Pebble),
				Bx(61, 0.3, -36, 36, 0.3, 36, WOOD_M, Planks),
				Bx(-78, 0.3, 50, 20, 0.3, 16, WOOD_M, Planks),
				Bx(0, 0.3, 56, 20, 0.2, 16, STONE, Concrete),
				Bx(-84, 0.3, -50, 8, 0.1, 20, GREEN, Grass),
				Bx(86, 0.3, -50, 10, 0.1, 28, GREEN, Grass),
			},
		},
		{
			Id = "Hall",
			Name = "Main Dojo",
			Description = "A three-tier pagoda dojo with dark walls and red doorposts. The Ninja Shiba trains inside!",
			Pad = Vector2.new(61, -14),
			RewardMult = 1.4,
			PriceSeconds = 16,
			Pieces = {
				Bx(61, 0, -50.4, 30, 10, 1.2, WOOD_D, Wood),
				Bx(46.6, 0, -36, 1.2, 10, 30, WOOD_D, Wood),
				Bx(75.4, 0, -36, 1.2, 10, 30, WOOD_D, Wood),
				Cy(47.2, 0, -21.8, 1.6, 10, RED, Wood),
				Cy(74.8, 0, -21.8, 1.6, 10, RED, Wood),
				Cy(54, 0, -21.8, 1.6, 10, RED, Wood),
				Cy(68, 0, -21.8, 1.6, 10, RED, Wood),
				Bx(61, 8.1, -22.4, 30, 1, 1.4, RED, Wood),
				Bx(61, 0, -19.2, 14, 0.5, 2.6, STONE, Slate),
				Bx(61, 9.2, -36, 38, 1.6, 38, ROOF, Slate),
				Bx(61, 12.4, -36, 28, 1.4, 28, ROOF, Slate),
				Bx(61, 15.4, -36, 18, 1.4, 18, ROOF, Slate),
				Cy(61, 16.8, -36, 0.8, 4.4, GOLD, Metal),
				Bl(61, 22, -36, 1.8, 1.8, 1.8, GOLD, Metal),
			},
		},
		{
			Id = "Gate",
			Name = "Red Gate",
			Description = "A tall red torii gate that spans the walkway at the entrance of the dojo.",
			Pad = Vector2.new(14, 50),
			RewardMult = 1.25,
			PriceSeconds = 18,
			Pieces = {
				Cy(-8, 0, 56, 1.9, 11, RED, Wood),
				Cy(8, 0, 56, 1.9, 11, RED, Wood),
				Bx(-8, 0, 56, 3, 0.9, 3, STONE, Slate),
				Bx(8, 0, 56, 3, 0.9, 3, STONE, Slate),
				Bx(0, 11.2, 56, 27, 1.3, 2.8, BLACK, Wood),
				Bx(0, 8.2, 56, 19, 0.9, 1.2, RED, Wood),
				Bx(0, 9.1, 56, 1, 2.1, 1, RED, Wood),
				Bx(0, 9.3, 56.9, 3.2, 1.8, 0.3, GOLD, Plastic),
			},
		},
		{
			Id = "Dummies",
			Yaw = 20,
			Name = "Training Dummies",
			Description = "Three straw dummies on a post that wait to be bonked with a mean headband.",
			Pad = Vector2.new(-74, 14),
			RewardMult = 1.3,
			PriceSeconds = 21,
			Pieces = merge({ Bx(-74, 0, 22, 24, 0.3, 8, SAND, Sandy) }, dummy(-82, 22), dummy(-74, 22), dummy(-66, 22)),
		},
		{
			Id = "Lanterns",
			Yaw = 10,
			Name = "Stone Lanterns",
			Description = "Four stone lanterns with a warm light that guard the doorstep of the dojo.",
			Pad = Vector2.new(61, -6),
			PriceSeconds = 24,
			Pieces = merge(lantern(46, -12), lantern(54, -12), lantern(68, -12), lantern(74, -12)),
		},
		{
			Id = "Zen",
			Yaw = -12,
			Name = "Zen Garden",
			Description = "Raked sand in a stone frame, three round rocks and a tiny pine tree.",
			Pad = Vector2.new(60, 31),
			PriceSeconds = 28,
			Pieces = {
				Bx(60, 0, 45, 36, 0.4, 24, SAND, Sandy),
				Bx(60, 0, 33.6, 37.2, 0.5, 1.2, STONE, Slate),
				Bx(60, 0, 56.4, 37.2, 0.5, 1.2, STONE, Slate),
				Bx(42.6, 0, 45, 1.2, 0.5, 24, STONE, Slate),
				Bx(77.4, 0, 45, 1.2, 0.5, 24, STONE, Slate),
				Bl(54, 1.5, 41, 5, 3.2, 4.2, STONE_D, Slate),
				Bl(66, 1.1, 51, 3.6, 2.4, 3.4, STONE_D, Slate),
				Bl(70, 0.8, 39, 2.4, 1.8, 2.4, STONE_D, Slate),
				Bl(48, 0.7, 52, 2, 1.4, 2, STONE_D, Slate),
				Cy(72, 0.4, 52, 0.7, 2.2, WOOD_D, Wood),
				Bl(72, 3.4, 52, 4.4, 2.4, 4.4, GREEN, Grass),
			},
		},
		{
			Id = "Bamboo",
			Yaw = 4,
			Name = "Bamboo Grove",
			Description = "Fourteen tall green bamboo stalks that rustle when a ninja sneaks by.",
			Pad = Vector2.new(87, 10),
			PriceSeconds = 32,
			Pieces = bambooStalks(),
		},
		{
			Id = "Cherry",
			Yaw = -4,
			Name = "Cherry Trees",
			Description = "Three cherry trees in full pink bloom with a carpet of petals below.",
			Pad = Vector2.new(-42, 50),
			PriceSeconds = 37,
			Pieces = merge(
				{ Bx(-42, 0.3, 57.5, 40, 0.1, 10, C(255, 205, 225), Grass) },
				cherry(-28, 57),
				cherry(-42, 59),
				cherry(-56, 56)
			),
		},
		{
			Id = "Weapons",
			Yaw = 14,
			Name = "Katana Rack",
			Description = "A wooden rack with shiny katanas, ready for a surprise attack.",
			Pad = Vector2.new(-76, 38),
			PriceSeconds = 42,
			Pieces = {
				Bx(-82, 0, 33, 1.4, 0.6, 4, WOOD_D, Wood),
				Bx(-70, 0, 33, 1.4, 0.6, 4, WOOD_D, Wood),
				Bx(-82, 0.6, 33, 0.9, 6.2, 0.9, WOOD_D, Wood),
				Bx(-70, 0.6, 33, 0.9, 6.2, 0.9, WOOD_D, Wood),
				Bx(-76, 6.4, 33, 14.4, 0.8, 1.1, WOOD_M, Wood),
				Bx(-76, 2, 33, 12, 0.5, 1, WOOD_M, Wood),
				Bx(-76, 4.2, 33, 12, 0.5, 1, WOOD_M, Wood),
				Bx(-76, 2.5, 33.5, 11.4, 0.35, 0.5, BLACK, Metal),
				Bx(-76, 4.7, 33.5, 11.4, 0.35, 0.5, STEEL, Metal),
			},
		},
		{
			Id = "Banners",
			Yaw = 8,
			Name = "War Banners",
			Description = "Three tall red banners with a white moon fluttering behind the dojo.",
			Pad = Vector2.new(31, -44),
			PriceSeconds = 49,
			Pieces = merge(banner(22), banner(31), banner(40)),
		},
		{
			Id = "Pond",
			Name = "Koi Pond",
			Description = "A stone-rimmed pond with lily pads and two fat orange koi.",
			Pad = Vector2.new(-55, -24),
			PriceSeconds = 56,
			Pieces = {
				Bx(-70, 0, -24, 24, 0.4, 12, WATER, Plastic),
				Bx(-70, 0, -30.6, 26.4, 0.5, 1.2, STONE, Slate),
				Bx(-70, 0, -17.4, 26.4, 0.5, 1.2, STONE, Slate),
				Bx(-82.6, 0, -24, 1.2, 0.5, 12, STONE, Slate),
				Bx(-57.4, 0, -24, 1.2, 0.5, 12, STONE, Slate),
				Bl(-80, 1.1, -19.5, 3.6, 2.4, 3, STONE_D, Slate),
				Bl(-60, 0.9, -28.5, 2.8, 2, 2.6, STONE_D, Slate),
				Bl(-78, 0.8, -29, 2.2, 1.6, 2, STONE_D, Slate),
				Cy(-64, 0.4, -22, 2.4, 0.1, GREEN, Plastic),
				Cy(-76, 0.4, -26, 2, 0.1, GREEN, Plastic),
				Bx(-72, 0.4, -21, 1.6, 0.15, 0.6, ORANGE, Plastic),
				Bx(-66, 0.4, -26.5, 1.4, 0.15, 0.55, WHITE, Plastic),
			},
		},
		{
			Id = "Teahouse",
			Yaw = 8,
			Name = "Tea House",
			Description = "A tiny open tea house with a low table, two cushions and a hip roof.",
			Pad = Vector2.new(-78, 61),
			PriceSeconds = 64,
			Pieces = {
				Bx(-78, 0.6, 43.6, 14, 7.4, 0.8, PAPER, Wood),
				Bx(-85.4, 0.6, 50, 0.8, 7.4, 12, WOOD_D, Wood),
				Bx(-70.6, 0.6, 50, 0.8, 7.4, 12, WOOD_D, Wood),
				Cy(-84.4, 0.6, 55.4, 1, 7.4, RED, Wood),
				Cy(-71.6, 0.6, 55.4, 1, 7.4, RED, Wood),
				Bx(-78, 8, 50, 18, 1.2, 16, ROOF, Slate),
				Bx(-78, 9.2, 50, 11, 1.2, 9, ROOF, Slate),
				Bl(-78, 11.2, 50, 1.6, 1.6, 1.6, GOLD, Metal),
				Bx(-78, 0.6, 49, 4, 1, 3, WOOD_M, Wood),
				Bx(-81.5, 0.6, 49, 2, 0.4, 2, RED, Fabric),
				Bx(-74.5, 0.6, 49, 2, 0.4, 2, RED, Fabric),
			},
		},
		{
			Id = "Tower",
			Yaw = 15,
			Name = "Ninja Watchtower",
			Description = "A tall wooden watchtower with a lookout nest and a two-tier roof.",
			Pad = Vector2.new(-36, -36),
			RewardMult = 1.35,
			PriceSeconds = 74,
			Pieces = {
				Cy(-39.6, 0, -49.6, 1.4, 12, WOOD_D, Wood),
				Cy(-32.4, 0, -49.6, 1.4, 12, WOOD_D, Wood),
				Cy(-39.6, 0, -42.4, 1.4, 12, WOOD_D, Wood),
				Cy(-32.4, 0, -42.4, 1.4, 12, WOOD_D, Wood),
				Bx(-36, 12, -46, 11, 1, 11, WOOD_M, Planks),
				Cy(-40.6, 13, -50.6, 0.8, 6, RED, Wood),
				Cy(-31.4, 13, -50.6, 0.8, 6, RED, Wood),
				Cy(-40.6, 13, -41.4, 0.8, 6, RED, Wood),
				Cy(-31.4, 13, -41.4, 0.8, 6, RED, Wood),
				Bx(-36, 19, -46, 15, 1.2, 15, ROOF, Slate),
				Bx(-36, 20.2, -46, 9, 1.1, 9, ROOF, Slate),
				Cy(-36, 21.3, -46, 0.5, 3, GOLD, Metal),
				Bx(-36, 13, -50.4, 9, 5, 0.3, PAPER, Wood),
				Bx(-36, 0, -41.6, 2, 12, 0.5, WOOD_M, Wood),
				Bx(-36, 4, -49.6, 7.2, 0.5, 0.5, WOOD_D, Wood),
			},
		},
		{
			Id = "Taiko",
			Yaw = -22,
			Name = "Taiko Drum",
			Description = "A giant war drum on a wooden stand with two mallets. Boom!",
			Pad = Vector2.new(22, 30),
			PriceSeconds = 85,
			Pieces = {
				Bx(22, 0, 38, 11, 0.8, 5, WOOD_D, Wood),
				Bx(17.6, 0.8, 38, 0.8, 6.2, 2.6, WOOD_M, Wood),
				Bx(26.4, 0.8, 38, 0.8, 6.2, 2.6, WOOD_M, Wood),
				Cz(22, 5.2, 38, 6.6, 4.2, C(150, 50, 40), Wood),
				Cz(22, 5.2, 40.2, 6.2, 0.3, PAPER, Fabric),
				Cz(22, 5.2, 35.8, 6.2, 0.3, PAPER, Fabric),
				Cz(22, 5.2, 38, 6.9, 0.5, GOLD, Metal),
				Cy(18.5, 0.8, 41, 0.4, 3.2, WOOD_M, Wood),
				Cy(25.5, 0.8, 41, 0.4, 3.2, WOOD_M, Wood),
			},
		},
		{
			Id = "Bridge",
			Name = "Arched Bridge",
			Description = "A red wooden bridge that arches over the koi pond.",
			Pad = Vector2.new(-70, -11),
			PriceSeconds = 98,
			Pieces = {
				Bx(-70, 2, -24, 4.4, 0.6, 6, WOOD_M, Planks),
				Bx(-70, 1.3, -28.6, 4.4, 0.6, 3.2, WOOD_M, Planks),
				Bx(-70, 1.3, -19.4, 4.4, 0.6, 3.2, WOOD_M, Planks),
				Bx(-70, 0.6, -31.6, 4.4, 0.6, 2.8, WOOD_M, Planks),
				Bx(-70, 0.6, -16.4, 4.4, 0.6, 2.8, WOOD_M, Planks),
				Bx(-72, 3.5, -24, 0.3, 0.4, 18, RED, Wood),
				Bx(-68, 3.5, -24, 0.3, 0.4, 18, RED, Wood),
				Bx(-72, 1.2, -32, 0.4, 2.7, 0.4, RED, Wood),
				Bx(-72, 2.6, -24, 0.4, 1.3, 0.4, RED, Wood),
				Bx(-72, 1.2, -16, 0.4, 2.7, 0.4, RED, Wood),
				Bx(-68, 1.2, -32, 0.4, 2.7, 0.4, RED, Wood),
				Bx(-68, 2.6, -24, 0.4, 1.3, 0.4, RED, Wood),
				Bx(-68, 1.2, -16, 0.4, 2.7, 0.4, RED, Wood),
			},
		},
		{
			Id = "Course",
			Yaw = -10,
			Name = "Obstacle Course",
			Description = "A climbing wall, a balance beam, jumping stumps and a pull-up bar for sneaky training.",
			Pad = Vector2.new(-83, -6),
			PriceSeconds = 112,
			Pieces = {
				Bx(-76, 0.3, 2, 26, 0.2, 12, SAND, Sandy),
				Bx(-88.4, 0.5, 2, 1.2, 7, 9, WOOD_M, Planks),
				Bx(-83, 0.5, 2, 0.9, 1.8, 1.6, WOOD_D, Wood),
				Bx(-77, 0.5, 2, 0.9, 1.8, 1.6, WOOD_D, Wood),
				Bx(-80, 2.3, 2, 9, 0.7, 1.4, WOOD_M, Planks),
				Cy(-72, 0.5, 0, 1.8, 1, WOOD_D, Wood),
				Cy(-69, 0.5, 4, 1.8, 1.6, WOOD_D, Wood),
				Cy(-66, 0.5, 0, 1.8, 2.2, WOOD_D, Wood),
				Cy(-63.5, 0.5, 5, 1.8, 2.8, WOOD_D, Wood),
				Cy(-81, 0.5, 6.5, 0.7, 4.5, WOOD_D, Wood),
				Cy(-75, 0.5, 6.5, 0.7, 4.5, WOOD_D, Wood),
				Bx(-78, 4.6, 6.5, 6.6, 0.4, 0.4, STEEL, Metal),
			},
		},
		{
			Id = "Targets",
			Yaw = 14,
			Name = "Shuriken Targets",
			Description = "Three round straw targets with red rings and golden bullseyes.",
			Pad = Vector2.new(76, 8),
			PriceSeconds = 129,
			Pieces = merge({ Bx(76, 0, 0, 26, 0.2, 6, C(150, 140, 125), Pebble) }, target(68), target(76), target(84)),
		},
		{
			Id = "Totem",
			Yaw = 20,
			Name = "Shuriken Totem",
			Description = "A carved totem pole with two giant steel shuriken, a real eye-catcher.",
			Pad = Vector2.new(88, -14),
			RewardMult = 1.3,
			PriceSeconds = 148,
			Pieces = merge({
				Bx(88, 0, -22, 6, 1, 6, STONE, Slate),
				Bx(88, 1, -22, 4.2, 1, 4.2, STONE_D, Slate),
				Cy(88, 2, -22, 1.6, 14, WOOD_D, Wood),
				Cy(88, 16, -22, 2.2, 1.4, GOLD, Metal),
			}, shuriken(88, 12.5, -20.6, 7.2), shuriken(88, 6.5, -20.6, 4.8)),
		},
		{
			Id = "Statue",
			Yaw = -18,
			Name = "Ninja Shiba Statue",
			Description = "A stone Shiba with a red headband sits proudly on its plinth.",
			Pad = Vector2.new(-16, -20),
			PriceSeconds = 170,
			Pieces = {
				Bx(-16, 0, -30, 9, 1.6, 9, STONE, Slate),
				Bx(-16, 1.6, -30, 7, 1, 7, STONE_D, Slate),
				Bl(-16, 5.6, -30.5, 4.8, 6, 4.4, STONE, Slate),
				Bl(-16, 10, -30.2, 5, 4.4, 4.6, STONE, Slate),
				Bx(-17.6, 12.1, -30.2, 1.1, 1.6, 0.7, STONE, Slate),
				Bx(-14.4, 12.1, -30.2, 1.1, 1.6, 0.7, STONE, Slate),
				Bx(-16, 8.9, -27.9, 2, 1.4, 1.6, STONE, Slate),
				Bx(-16, 9.6, -26.9, 0.8, 0.6, 0.5, BLACK, Plastic),
				Bx(-16, 10.5, -30.2, 5.2, 0.9, 4.8, RED, Fabric),
				Bx(-16, 10.5, -33, 1.4, 1, 1.4, RED, Fabric),
				Bx(-17.2, 2.6, -28.2, 1.3, 4, 1.4, STONE, Slate),
				Bx(-14.8, 2.6, -28.2, 1.3, 4, 1.4, STONE, Slate),
				Bl(-16, 5, -33.4, 3, 3.4, 3, STONE, Slate),
			},
		},
		{
			Id = "Moon",
			Yaw = 12,
			Name = "Giant Moon",
			Description = "A huge glowing-white moon hangs between two red pillars: the pride of every ninja.",
			Pad = Vector2.new(-68, -44),
			RewardMult = 1.5,
			PriceSeconds = 196,
			Pieces = {
				Bx(-68, 0, -54, 30, 1.2, 10, STONE, Slate),
				Bx(-68, 0, -48.2, 10, 0.6, 2.2, STONE, Slate),
				Cy(-81, 1.2, -54, 1.8, 22, RED, Wood),
				Cy(-55, 1.2, -54, 1.8, 22, RED, Wood),
				Bx(-68, 23.2, -54, 30, 1.2, 2, BLACK, Wood),
				Cz(-68, 13.2, -54, 19, 1.2, C(250, 244, 214), Plastic),
				Cz(-72, 15, -53.3, 4, 0.3, C(226, 218, 182), Plastic),
				Cz(-64, 11, -53.3, 3, 0.3, C(226, 218, 182), Plastic),
				Cz(-66, 17.5, -53.3, 2.4, 0.3, C(226, 218, 182), Plastic),
			},
		},
	},
}

return theme
