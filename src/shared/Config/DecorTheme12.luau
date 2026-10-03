--!strict
-- Theme of the Shiba of bay 12: Samurai Shrine (Config/DecorTypes -> Theme). 190 x 130: the Samurai Shiba stands in the front left
-- garden below a tall five-storey pagoda, a vermilion torii spans the walkway, the path winds through a sakura and rock garden to a
-- koi pond with an arched bridge on the right and ends at the great shrine hall, the colossal samurai statue and the temple bell in the back.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lanterns, fire and lamps are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local GRASS = C(104, 154, 78)
local MOSS = C(78, 124, 66)
local GRAVEL = C(216, 208, 186)
local STONE = C(152, 152, 150)
local DARK_STONE = C(96, 98, 104)
local VERMILION = C(206, 54, 38)
local DARK_RED = C(150, 38, 34)
local ROOF = C(60, 64, 76)
local WOOD = C(124, 86, 54)
local DARK_WOOD = C(74, 50, 38)
local PLASTER = C(238, 232, 214)
local INDIGO = C(44, 62, 112)
local GOLD = C(238, 190, 62)
local BRONZE = C(150, 112, 62)
local PINK = C(248, 178, 202)
local PINK_DARK = C(236, 140, 176)
local WATER = C(72, 150, 184)
local KOI = C(238, 120, 44)
local LEAF = C(112, 166, 76)
local EARTH = C(128, 98, 70)
local WARM = C(250, 214, 130)
local BLACK = C(36, 36, 44)
local STEEL = C(184, 190, 200)
local SKIN = C(226, 184, 146)

local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Slate = Enum.Material.Slate
local Rock = Enum.Material.Rock
local Granite = Enum.Material.Granite
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass
local Pebble = Enum.Material.Pebble
local Metal = Enum.Material.Metal
local Ground = Enum.Material.Ground

-- Block by extents (x0..x1, y0..y1, z0..z1), optional rotation in degrees about its own centre.
local function Bx(
	x0: number,
	x1: number,
	y0: number,
	y1: number,
	z0: number,
	z1: number,
	color: Color3,
	mat: Enum.Material,
	rot: Vector3?
): Piece
	return {
		Size = Vector3.new(x1 - x0, y1 - y0, z1 - z0),
		Offset = Vector3.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
		Rotation = rot,
	}
end

-- Standing cylinder (axis up): centre (x, z), from y0 to y1, diameter d.
local function Cy(x: number, z: number, y0: number, y1: number, d: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(y1 - y0, d, d),
		Offset = Vector3.new(x, (y0 + y1) / 2, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along Z (a drum or target facing the road): diameter d, length len.
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

-- A stone lantern (toro) of scale s standing at (x, z): base, post, light box, roof, finial.
local function toro(x: number, z: number, s: number): Pieces
	return {
		Cy(x, z, 0, 0.7 * s, 3 * s, DARK_STONE, Granite),
		Cy(x, z, 0.7 * s, 3.2 * s, 1 * s, STONE, Granite),
		Bx(x - 0.9 * s, x + 0.9 * s, 3.2 * s, 5 * s, z - 0.9 * s, z + 0.9 * s, WARM, Plastic),
		Bx(x - 2.1 * s, x + 2.1 * s, 5 * s, 6 * s, z - 2.1 * s, z + 2.1 * s, DARK_STONE, Granite),
		Ball(x, 6.5 * s, z, 1.2 * s, 1.2 * s, 1.2 * s, STONE, Granite),
	}
end

-- One nobori war banner: pole, top arm and the tall cloth hanging from it.
local function nobori(x: number, z: number, h: number, cloth: Color3): Pieces
	return {
		Cy(x, z, 0, h, 0.6, DARK_WOOD, Wood),
		Bx(x, x + 3.6, h - 0.6, h, z - 0.2, z + 0.2, DARK_WOOD, Wood),
		Bx(x + 0.4, x + 3.2, h - 11, h - 0.6, z - 0.15, z + 0.15, cloth, Fabric),
	}
end

-- A stone rock of the gardens.
local function rock(x: number, z: number, sx: number, sy: number, sz: number, yaw: number, color: Color3): Piece
	return Bx(x - sx / 2, x + sx / 2, 0, sy, z - sz / 2, z + sz / 2, color, Rock, rot(0, yaw, 0))
end

-- One komainu (guardian lion-dog) on a stone pedestal at (x, z).
local function komainu(x: number, z: number): Pieces
	return {
		Bx(x - 2.2, x + 2.2, 0, 2.2, z - 2.2, z + 2.2, DARK_STONE, Granite),
		Bx(x - 1.5, x + 1.5, 2.2, 4.4, z - 1.6, z + 1.2, STONE, Granite),
		Bx(x - 1.1, x + 1.1, 3, 6.6, z + 0.2, z + 1.8, STONE, Granite),
		Ball(x, 7, z + 0.6, 2.6, 2.4, 2.6, STONE, Granite),
		Bx(x - 0.5, x + 0.5, 3.2, 4.8, z - 2.2, z - 1.4, STONE, Granite, rot(35, 0, 0)),
	}
end

local theme: DecorTypes.Theme = {
	Key = "SamuraiShrine",
	Name = "Samurai Shrine",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-64, 30), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(38, 48),
		Vector2.new(-28, 34),
		Vector2.new(-34, 6),
		Vector2.new(10, -10),
		Vector2.new(46, -24),
		Vector2.new(30, -46),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-75, 30),
	AutoPad = Vector2.new(-53, 30),
	Parts = {
		{
			Id = "Ground",
			Name = "Shrine Grounds",
			Description = "A green garden with raked gravel courts, mossy patches and neat stone plazas.",
			Pad = Vector2.new(24, 58),
			PriceSeconds = 30,
			Pieces = {
				Bx(-95, 95, 0, 0.3, -65, 65, GRASS, Grass),
				Bx(-77, -47, 0.3, 0.5, 19, 41, GRAVEL, Pebble),
				Bx(-92, -64, 0.3, 0.5, 38, 65, GRAVEL, Pebble),
				Bx(-21, 5, 0.3, 0.5, -53, -27, GRAVEL, Pebble),
				Bx(54, 82, 0.3, 0.5, -36, -23, GRAVEL, Pebble),
				Bx(-24, 0, 0.3, 0.5, -28, -12, MOSS, Grass),
				Bx(30, 52, 0.3, 0.5, 20, 34, MOSS, Grass),
			},
		},
		{
			Id = "Pagoda",
			Yaw = 6,
			Name = "Five-Storey Pagoda",
			Description = "A tall vermilion pagoda with five curving tile roofs and a golden spire watches over the Samurai Shiba.",
			Pad = Vector2.new(-62, 50),
			PriceSeconds = 35,
			Pieces = {
				Bx(-88, -68, 0, 1.4, 42, 62, STONE, Granite),
				Bx(-86.5, -69.5, 1.4, 2.2, 43.5, 60.5, DARK_STONE, Slate),
				Bx(-82.8, -73.2, 2.2, 5.2, 47.2, 56.8, VERMILION, Wood),
				Bx(-86, -70, 5.2, 5.7, 44, 60, ROOF, Slate),
				Bx(-82.2, -73.8, 5.7, 8.7, 47.8, 56.2, PLASTER, Plastic),
				Bx(-85, -71, 8.7, 9.2, 45, 59, ROOF, Slate),
				Bx(-81.6, -74.4, 9.2, 12.2, 48.4, 55.6, VERMILION, Wood),
				Bx(-84, -72, 12.2, 12.7, 46, 58, ROOF, Slate),
				Bx(-81, -75, 12.7, 15.7, 49, 55, PLASTER, Plastic),
				Bx(-83, -73, 15.7, 16.2, 47, 57, ROOF, Slate),
				Bx(-80.4, -75.6, 16.2, 19.2, 49.6, 54.4, VERMILION, Wood),
				Bx(-82, -74, 19.2, 19.7, 48, 56, ROOF, Slate),
				Cy(-78, 52, 19.7, 28, 0.8, GOLD, Metal),
				Ball(-78, 28.4, 52, 1.4, 1.4, 1.4, GOLD, Metal),
			},
		},
		{
			Id = "Torii",
			Yaw = 12,
			Name = "Vermilion Torii",
			Description = "A tall red torii gate with a black crown beam stands over the walkway, welcoming every visitor.",
			Pad = Vector2.new(-31, 20),
			PriceSeconds = 40,
			Pieces = {
				Cy(-40.5, 20, 1, 13, 2.2, VERMILION, Wood),
				Cy(-21.5, 20, 1, 13, 2.2, VERMILION, Wood),
				Cy(-40.5, 20, 0, 1, 3.2, BLACK, Granite),
				Cy(-21.5, 20, 0, 1, 3.2, BLACK, Granite),
				Bx(-42.5, -19.5, 9.2, 10.4, 19.4, 20.6, VERMILION, Wood),
				Bx(-43.5, -18.5, 12.2, 13.2, 19, 21, VERMILION, Wood),
				Bx(-44.5, -17.5, 13.2, 14.4, 18.4, 21.6, BLACK, Wood),
				Bx(-46, -43, 14.4, 15.4, 19, 21, BLACK, Wood, rot(0, 0, -14)),
				Bx(-19, -16, 14.4, 15.4, 19, 21, BLACK, Wood, rot(0, 0, 14)),
				Bx(-32.2, -29.8, 10.4, 12.2, 19.5, 20.5, GOLD, Wood),
			},
		},
		{
			Id = "Lanterns",
			Yaw = 22,
			Name = "Stone Lantern Garden",
			Description = "Three mossy stone toro of different heights, glowing softly beside the walkway.",
			Pad = Vector2.new(-20, 45),
			PriceSeconds = 46,
			Pieces = merge(toro(-28, 52, 1.1), toro(-20, 58, 0.8), toro(-12, 51.5, 1.3)),
		},
		{
			Id = "Teahouse",
			Yaw = -9,
			Name = "Tea House",
			Description = "A little wooden tea house on a raised deck with a tiled roof, a blue curtain, a bench and a red parasol.",
			Pad = Vector2.new(50, 36),
			PriceSeconds = 53,
			Pieces = {
				Bx(57, 79, 0, 1, 28, 44, WOOD, Planks),
				Bx(59, 77, 1, 6.5, 30.2, 30.8, PLASTER, Plastic),
				Bx(59, 59.6, 1, 6.5, 30.8, 41.4, PLASTER, Plastic),
				Bx(76.4, 77, 1, 6.5, 30.8, 41.4, PLASTER, Plastic),
				Cy(59.4, 41.6, 1, 6.5, 0.9, DARK_WOOD, Wood),
				Cy(76.6, 41.6, 1, 6.5, 0.9, DARK_WOOD, Wood),
				Cy(59.4, 30.6, 1, 6.5, 0.9, DARK_WOOD, Wood),
				Cy(76.6, 30.6, 1, 6.5, 0.9, DARK_WOOD, Wood),
				Bx(57, 79, 6.5, 7.3, 28, 44, ROOF, Slate),
				Bx(60, 76, 7.3, 8.4, 30.5, 41.5, ROOF, Slate),
				Bx(63, 73, 8.4, 9.2, 33, 39, DARK_STONE, Slate),
				Bx(62, 74, 4.3, 6.3, 41.7, 42, INDIGO, Fabric),
				Bx(66, 72, 1, 2, 38, 40, WOOD, Planks),
				Cy(61, 43, 1, 6.2, 0.4, DARK_WOOD, Wood),
				Cy(61, 43, 5.6, 6.2, 6, VERMILION, Fabric),
			},
		},
		{
			Id = "Nobori",
			Yaw = -18,
			Name = "Nobori War Banners",
			Description = "Four tall banners of the clan, red, white and blue, snapping in the wind on tall poles.",
			Pad = Vector2.new(-36, -10),
			PriceSeconds = 61,
			Pieces = merge(
				nobori(-44, -20, 15, VERMILION),
				nobori(-39, -25, 13.5, PLASTER),
				nobori(-33.5, -21, 15.5, INDIGO),
				nobori(-28, -26.5, 14, VERMILION)
			),
		},
		{
			Id = "KoiPond",
			Yaw = 15,
			Name = "Koi Pond",
			Description = "A winding pond of blue water ringed by mossy rocks, with water lilies and orange koi.",
			Pad = Vector2.new(44, 6),
			PriceSeconds = 70,
			RewardMult = 1.4,
			Pieces = {
				Bx(55, 81, 0.1, 0.6, 0, 20, WATER, Plastic),
				rock(56, 1.5, 4.2, 2, 4, 20, STONE),
				rock(62, 0, 3.6, 1.6, 3, -15, DARK_STONE),
				rock(73, -0.2, 4.4, 1.8, 3.2, 25, STONE),
				rock(80, 2, 4, 2, 4, -30, DARK_STONE),
				rock(81, 12.5, 3.2, 1.4, 4.4, 10, STONE),
				rock(79, 19, 4.4, 1.8, 3.6, 18, DARK_STONE),
				rock(70, 20, 3.6, 1.6, 3, -12, STONE),
				rock(60, 19, 4.2, 2, 4, 28, DARK_STONE),
				rock(55, 10.5, 3.4, 1.6, 4.4, -8, STONE),
				Cy(63, 6, 0.6, 0.8, 3, LEAF, Grass),
				Cy(74, 14, 0.6, 0.8, 3.6, LEAF, Grass),
				Ball(67, 0.7, 12, 2.2, 0.6, 0.9, KOI, Plastic),
				Ball(71, 0.7, 6, 2, 0.6, 0.8, PLASTER, Plastic),
			},
		},
		{
			Id = "Dojo",
			Yaw = 8,
			Name = "Training Dojo",
			Description = "A wide wooden dojo with a tiled roof, paper doors and straw dummies where the samurai train every day.",
			Pad = Vector2.new(-47, -40),
			PriceSeconds = 81,
			RewardMult = 1.25,
			Pieces = {
				Bx(-81, -51, 0, 0.8, -54, -34, DARK_STONE, Granite),
				Bx(-80, -52, 0.8, 1.4, -53, -35, WOOD, Planks),
				Bx(-79, -53, 1.4, 8.4, -53, -52.2, PLASTER, Plastic),
				Bx(-79, -78.2, 1.4, 8.4, -52.2, -37, PLASTER, Plastic),
				Bx(-53.8, -53, 1.4, 8.4, -52.2, -37, PLASTER, Plastic),
				Cy(-78.6, -37, 1.4, 8.4, 1, DARK_WOOD, Wood),
				Cy(-71, -37, 1.4, 8.4, 1, DARK_WOOD, Wood),
				Cy(-61, -37, 1.4, 8.4, 1, DARK_WOOD, Wood),
				Cy(-53.4, -37, 1.4, 8.4, 1, DARK_WOOD, Wood),
				Bx(-77, -69, 1.4, 7.4, -45.2, -44.8, PLASTER, Plastic),
				Bx(-63, -55, 1.4, 7.4, -45.2, -44.8, PLASTER, Plastic),
				Bx(-81, -51, 8.4, 9.2, -54, -34, ROOF, Slate),
				Bx(-78, -54, 9.2, 10.4, -51.5, -36.5, ROOF, Slate),
				Bx(-75, -57, 10.4, 11.4, -48, -40, DARK_STONE, Slate),
			},
		},
		{
			Id = "Temizuya",
			Yaw = -25,
			Name = "Purification Basin",
			Description = "A stone water basin under a small roof where visitors rinse their hands with a bamboo ladle.",
			Pad = Vector2.new(-10, 28),
			PriceSeconds = 93,
			Pieces = {
				Bx(-12.8, -7.2, 0, 1.8, 16.8, 21.2, STONE, Granite),
				Bx(-12, -8, 1.8, 2.1, 17.6, 20.4, WATER, Plastic),
				Cy(-14, 15.8, 0, 5.5, 0.7, DARK_WOOD, Wood),
				Cy(-6, 15.8, 0, 5.5, 0.7, DARK_WOOD, Wood),
				Cy(-14, 22.2, 0, 5.5, 0.7, DARK_WOOD, Wood),
				Cy(-6, 22.2, 0, 5.5, 0.7, DARK_WOOD, Wood),
				Bx(-14.8, -5.2, 5.5, 6.5, 15, 23, ROOF, Slate),
				Bx(-13, -7, 6.5, 7.4, 16.6, 21.4, DARK_STONE, Slate),
				Bx(-10.5, -9.5, 3.2, 3.5, 16.2, 18.4, WOOD, Wood),
			},
		},
		{
			Id = "Archery",
			Yaw = 14,
			Name = "Kyudo Archery Range",
			Description = "Three straw targets before an earth bank and a roofed line to loose long bows from. Bonk, thwack, bullseye!",
			Pad = Vector2.new(-46, -6),
			PriceSeconds = 107,
			Pieces = {
				Bx(-73, -51, 0, 3.4, -16, -14, EARTH, Ground),
				Cz(-67, 4.6, -13.6, 4.8, 0.6, PLASTER, Fabric),
				Cz(-62, 4.6, -13.6, 4.8, 0.6, PLASTER, Fabric),
				Cz(-57, 4.6, -13.6, 4.8, 0.6, PLASTER, Fabric),
				Cy(-67, -13.6, 0, 3, 0.6, DARK_WOOD, Wood),
				Cy(-62, -13.6, 0, 3, 0.6, DARK_WOOD, Wood),
				Cy(-57, -13.6, 0, 3, 0.6, DARK_WOOD, Wood),
				Bx(-73, -51, 7.6, 8.2, -16, -11, ROOF, Slate),
				Cy(-72, -12, 0, 7.6, 0.8, DARK_WOOD, Wood),
				Cy(-52, -12, 0, 7.6, 0.8, DARK_WOOD, Wood),
				Bx(-72, -52, 0, 0.5, -5.5, -2, WOOD, Planks),
				Cy(-70, -3, 0, 4.4, 0.6, DARK_WOOD, Wood),
				Cy(-64, -3, 0, 4.4, 0.6, DARK_WOOD, Wood),
				Bx(-71, -63, 3.6, 4.1, -3.3, -2.7, WOOD, Wood),
			},
		},
		{
			Id = "Bridge",
			Yaw = 15,
			Name = "Arched Red Bridge",
			Description = "A high red bridge with curved rails that carries visitors over the koi pond.",
			Pad = Vector2.new(44, 18),
			PriceSeconds = 123,
			Pieces = {
				Bx(64, 72, 3.6, 4.2, 7.5, 12.5, VERMILION, Wood),
				Bx(56.85, 64.35, 1.5, 2.1, 7.5, 12.5, VERMILION, Wood, rot(0, 0, 23)),
				Bx(71.65, 79.15, 1.5, 2.1, 7.5, 12.5, VERMILION, Wood, rot(0, 0, -23)),
				Cy(64.4, 8, 4.2, 5.8, 0.6, DARK_RED, Wood),
				Cy(64.4, 12, 4.2, 5.8, 0.6, DARK_RED, Wood),
				Cy(71.6, 8, 4.2, 5.8, 0.6, DARK_RED, Wood),
				Cy(71.6, 12, 4.2, 5.8, 0.6, DARK_RED, Wood),
				Bx(64.4, 71.6, 5.4, 5.8, 7.7, 8.3, DARK_RED, Wood),
				Bx(64.4, 71.6, 5.4, 5.8, 11.7, 12.3, DARK_RED, Wood),
				Cy(57.6, 8, 0.4, 2.4, 0.6, DARK_RED, Wood),
				Cy(57.6, 12, 0.4, 2.4, 0.6, DARK_RED, Wood),
				Cy(78.4, 8, 0.4, 2.4, 0.6, DARK_RED, Wood),
				Cy(78.4, 12, 0.4, 2.4, 0.6, DARK_RED, Wood),
			},
		},
		{
			Id = "RockGarden",
			Yaw = -20,
			Name = "Zen Rock Garden",
			Description = "Raked white gravel in calm waves around mossy rocks, a bonsai pine and a tiny lantern.",
			Pad = Vector2.new(22, 17),
			PriceSeconds = 141,
			Pieces = {
				Bx(11, 33, 0, 0.3, -2, 14, GRAVEL, Pebble),
				rock(18, 3, 4, 3.2, 3.4, 20, STONE),
				rock(22.5, 7.5, 2.6, 2, 2.4, -25, DARK_STONE),
				rock(27, 2, 3.2, 2.4, 3, 35, STONE),
				rock(28.5, 10, 2, 1.4, 2, 10, DARK_STONE),
				rock(16, 10.5, 1.8, 1.2, 1.8, 0, STONE),
				Cy(14, 11.5, 0, 3.6, 1, DARK_WOOD, Wood),
				Bx(11.6, 16.4, 3.2, 4.4, 9.5, 13.5, LEAF, Grass, rot(0, 15, 0)),
				Bx(12.4, 15.4, 4.4, 5.4, 10.4, 12.6, LEAF, Grass),
				Cy(31, 12, 0, 1.2, 2, DARK_STONE, Granite),
				Cy(31, 12, 1.2, 2.4, 0.8, STONE, Granite),
				Bx(29.6, 32.4, 2.4, 3.4, 10.6, 13.4, STONE, Granite),
			},
		},
		{
			Id = "Sakura",
			Yaw = 30,
			Name = "Great Sakura Tree",
			Description = "An old cherry tree in full bloom, with a carpet of fallen pink petals around its twisted trunk.",
			Pad = Vector2.new(14, 30),
			PriceSeconds = 162,
			RewardMult = 1.5,
			Pieces = {
				Bx(-1, 17, 0.3, 0.5, 13, 31, PINK, Grass),
				Cy(8, 22, 0, 9.5, 2.6, DARK_WOOD, Wood),
				Bx(4.6, 5.8, 9.5, 15.5, 21.4, 22.6, DARK_WOOD, Wood, rot(0, 0, 30)),
				Bx(10.2, 11.4, 9.5, 15.5, 21.4, 22.6, DARK_WOOD, Wood, rot(0, 0, -30)),
				Ball(8, 15, 22, 14, 9, 14, PINK, Grass),
				Ball(1.5, 14, 25, 10, 7, 10, PINK_DARK, Grass),
				Ball(15, 16, 18, 11, 7.5, 11, PINK, Grass),
				Ball(9, 19.5, 23, 9, 6, 9, PINK_DARK, Grass),
			},
		},
		{
			Id = "Taiko",
			Yaw = 28,
			Name = "Festival Taiko",
			Description = "A huge taiko drum in a wooden cradle beside a small drum, ready to boom out the Bonk beat.",
			Pad = Vector2.new(-56, 19),
			PriceSeconds = 187,
			Pieces = {
				Bx(-59, -45, 0, 0.6, 7, 13, WOOD, Planks),
				Cz(-54, 4, 10, 6.8, 4.8, DARK_RED, Wood),
				Bx(-58.8, -57.2, 0.6, 3.2, 8, 12, DARK_WOOD, Wood),
				Bx(-50.8, -49.2, 0.6, 3.2, 8, 12, DARK_WOOD, Wood),
				Bx(-48, -46, 0.6, 1.2, 9, 11, DARK_WOOD, Wood),
				Cz(-47, 3.2, 10, 4, 3, DARK_RED, Wood),
			},
		},
		{
			Id = "BellTower",
			Yaw = -10,
			Name = "Temple Bell Pavilion",
			Description = "A tiled pavilion with a great bronze bell and a log striker that rings out over the whole shrine.",
			Pad = Vector2.new(-24, -34),
			PriceSeconds = 215,
			RewardMult = 1.5,
			Pieces = {
				Bx(-40, -28, 0, 1, -48, -36, DARK_STONE, Granite),
				Cy(-38.6, -46.6, 1, 8, 1.1, VERMILION, Wood),
				Cy(-29.4, -46.6, 1, 8, 1.1, VERMILION, Wood),
				Cy(-38.6, -37.4, 1, 8, 1.1, VERMILION, Wood),
				Cy(-29.4, -37.4, 1, 8, 1.1, VERMILION, Wood),
				Bx(-40, -28, 8, 8.8, -48, -36, ROOF, Slate),
				Bx(-38, -30, 8.8, 10, -46, -38, ROOF, Slate),
				Bx(-36, -32, 10, 10.8, -44.5, -39.5, DARK_STONE, Slate),
				Cy(-34, -42, 3.2, 7.8, 4.2, BRONZE, Metal),
				Cz(-34, 4.8, -41, 1, 6.4, DARK_WOOD, Wood),
			},
		},
		{
			Id = "Armor",
			Yaw = -22,
			Name = "Armour Stand",
			Description = "A full suit of red samurai armour with a golden crescent helmet, guarded on its little platform.",
			Pad = Vector2.new(-70, 6),
			PriceSeconds = 247,
			Pieces = {
				Bx(-87, -77, 0, 0.8, 2, 10, DARK_WOOD, Planks),
				Bx(-82.4, -81.6, 0.8, 3, 5.6, 6.4, DARK_WOOD, Wood),
				Bx(-85, -79, 1.8, 3.8, 4.2, 7.8, INDIGO, Fabric),
				Bx(-84.2, -79.8, 3.8, 7.8, 4.6, 7.4, VERMILION, Metal),
				Bx(-86.6, -84.4, 5.6, 7.8, 4.4, 7.6, DARK_RED, Metal),
				Bx(-79.6, -77.4, 5.6, 7.8, 4.4, 7.6, DARK_RED, Metal),
				Bx(-83.4, -80.6, 7.8, 9, 4.8, 7.2, INDIGO, Fabric),
				Ball(-82, 9.8, 6, 3.6, 2.8, 3.6, STEEL, Metal),
				Bx(-84.4, -83.2, 11, 13.6, 5.8, 6.2, GOLD, Metal, rot(0, 0, 25)),
				Bx(-80.8, -79.6, 11, 13.6, 5.8, 6.2, GOLD, Metal, rot(0, 0, -25)),
			},
		},
		{
			Id = "ShrineHall",
			Yaw = -6,
			Name = "Great Shrine Hall",
			Description = "The main hall: a stone terrace, red pillars, white walls and a mighty tiered roof with golden crossed finials.",
			Pad = Vector2.new(48, -46),
			PriceSeconds = 284,
			Pieces = {
				Bx(51, 81, 0, 1.6, -59, -39, STONE, Granite),
				Bx(60, 72, 0, 0.6, -37, -35, STONE, Granite),
				Bx(60.5, 71.5, 0, 1.1, -39, -37, STONE, Granite),
				Bx(54, 78, 1.6, 9, -58, -57.2, PLASTER, Plastic),
				Bx(54, 54.8, 1.6, 9, -57.2, -42, PLASTER, Plastic),
				Bx(77.2, 78, 1.6, 9, -57.2, -42, PLASTER, Plastic),
				Cy(55, -41.5, 1.6, 9, 1.4, VERMILION, Wood),
				Cy(62, -41.5, 1.6, 9, 1.4, VERMILION, Wood),
				Cy(70, -41.5, 1.6, 9, 1.4, VERMILION, Wood),
				Cy(77, -41.5, 1.6, 9, 1.4, VERMILION, Wood),
				Bx(62, 70, 1.6, 7.4, -56, -55.4, DARK_RED, Wood),
				Bx(51, 81, 9, 10, -59, -39, ROOF, Slate),
				Bx(54, 78, 10, 11.6, -57, -41, ROOF, Slate),
				Bx(58, 74, 11.6, 13, -55, -43, ROOF, Slate),
				Bx(60, 72, 13, 14.2, -51, -47, DARK_STONE, Slate),
			},
		},
		{
			Id = "Komainu",
			Yaw = 16,
			Name = "Guardian Lion-Dogs",
			Description = "A pair of stone komainu on pedestals, one with open mouth and one with closed, guarding the shrine hall.",
			Pad = Vector2.new(66, -28),
			PriceSeconds = 327,
			Pieces = merge(komainu(58, -28), komainu(74, -28)),
		},
		{
			Id = "EmaWall",
			Yaw = -30,
			Name = "Wishing Plaque Rack",
			Description = "A little roofed rack hung with wooden ema plaques, each with a wish for a better Bonk.",
			Pad = Vector2.new(14, -27),
			PriceSeconds = 376,
			Pieces = {
				Cy(8, -36, 0, 6.6, 1, DARK_WOOD, Wood),
				Cy(14, -36, 0, 6.6, 1, DARK_WOOD, Wood),
				Cy(20, -36, 0, 6.6, 1, DARK_WOOD, Wood),
				Bx(8.6, 13.4, 2.2, 4.2, -36.3, -35.7, WOOD, Planks),
				Bx(14.6, 19.4, 2.2, 4.2, -36.3, -35.7, WOOD, Planks),
				Bx(8.6, 13.4, 4.4, 6.2, -36.3, -35.7, PLASTER, Planks),
				Bx(14.6, 19.4, 4.4, 6.2, -36.3, -35.7, PLASTER, Planks),
				Bx(7, 21, 6.6, 7.4, -38, -34, ROOF, Slate),
				Bx(9, 19, 7.4, 8.2, -37.2, -34.8, DARK_STONE, Slate),
			},
		},
		{
			Id = "Statue",
			Yaw = 5,
			Name = "Colossal Samurai",
			Description = "The showpiece: a giant samurai in red armour and a crescent helmet leaning on his great sword.",
			Pad = Vector2.new(-8, -26),
			PriceSeconds = 432,
			RewardMult = 1.5,
			Pieces = {
				Bx(-17, 1, 0, 2.4, -49, -31, STONE, Granite),
				Bx(-14, -2, 2.4, 4.2, -46, -34, DARK_STONE, Granite),
				Bx(-12.5, -9.5, 4.2, 11, -43.5, -40.5, INDIGO, Fabric),
				Bx(-6.5, -3.5, 4.2, 11, -43.5, -40.5, INDIGO, Fabric),
				Bx(-13.5, -2.5, 10.5, 14.2, -44, -39, INDIGO, Fabric),
				Bx(-12.5, -3.5, 14.2, 20.8, -43.2, -39.8, VERMILION, Metal),
				Bx(-15.8, -12.6, 17, 21.4, -44.2, -38.8, DARK_RED, Metal),
				Bx(-3.4, -0.2, 17, 21.4, -44.2, -38.8, DARK_RED, Metal),
				Ball(-8, 23.2, -41.5, 4.4, 4.6, 4.4, SKIN, Plastic),
				Bx(-10.4, -5.6, 24.4, 26.4, -43.4, -39.6, DARK_STONE, Metal),
				Bx(-10.4, -9.2, 26.4, 31, -41.8, -41.2, GOLD, Metal, rot(0, 0, 25)),
				Bx(-6.8, -5.6, 26.4, 31, -41.8, -41.2, GOLD, Metal, rot(0, 0, -25)),
				Bx(-8.4, -7.6, 4.2, 18, -37.4, -36.6, STEEL, Metal),
				Bx(-9.8, -6.2, 18, 18.8, -37.6, -36.4, GOLD, Metal),
				Bx(-8.5, -7.5, 18.8, 21, -37.3, -36.7, BLACK, Fabric),
			},
		},
	},
}

return theme
