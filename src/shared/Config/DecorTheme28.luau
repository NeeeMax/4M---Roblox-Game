--!strict
-- Theme of the Shiba of bay 28: Doge Altar (Config/DecorTypes -> Theme). 160 x 115: the Cheems God stands on a golden sun plaza in front of a
-- marble shrine wall; the walkway winds through a golden temple precinct: pillar gate and lanterns at the entrance, a coin fountain, koi pond,
-- sacred garden, treat stall and a column of holy light in the front, guardian statues, bells and banners in the middle, a pagoda, sun disc
-- and kennel on the right, a temple hall, altar steps and vault in the left back, golden bone pillars and the doge throne in the middle back,
-- and one giant seated golden Doge statue (the landmark) in the right back corner.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: flames, gems and coins are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }
-- A prop spot: position and height (or scale), with an optional colour.
type Spot = { x: number, z: number, h: number, color: Color3? }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local SAND = C(222, 204, 156)
local DSAND = C(190, 166, 118)
local MARBLE = C(238, 232, 214)
local STONE = C(170, 160, 146)
local DSTONE = C(112, 104, 96)
local GOLD = C(244, 196, 56)
local DGOLD = C(190, 140, 40)
local LGOLD = C(252, 226, 130)
local RED = C(186, 48, 52)
local LAPIS = C(52, 92, 176)
local GREEN = C(84, 140, 70)
local DGREEN = C(52, 104, 56)
local WOOD = C(122, 84, 52)
local DWOOD = C(84, 58, 40)
local CREAM = C(250, 238, 200)
local BONE = C(240, 232, 208)
local WATER = C(90, 170, 210)
local PINK = C(232, 130, 150)
local FUR = C(240, 170, 60)
local PALE = C(255, 236, 160)
local GLOW = C(255, 250, 222)

local Sandstone = Enum.Material.Sandstone
local Marble = Enum.Material.Marble
local Metal = Enum.Material.Metal
local Wood = Enum.Material.Wood
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Cobble = Enum.Material.Cobblestone
local Brick = Enum.Material.Brick
local Slate = Enum.Material.Slate
local Grass = Enum.Material.Grass
local Glass = Enum.Material.Glass

-- Block centred at (x, y, z), size (sx, sy, sz), optional Rotation in degrees.
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

-- Standing cylinder (axis up): diameter d, height h, centre y; optional tilt about X and Z in degrees.
local function Cy(
	x: number,
	y: number,
	z: number,
	d: number,
	h: number,
	color: Color3,
	mat: Enum.Material,
	tx: number?,
	tz: number?
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(tx or 0, 0, 90 + (tz or 0)),
	}
end

-- Cylinder lying along X (a disc facing sideways): diameter d, length len.
local function Cx(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
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

local function Ry(a: number): Vector3
	return Vector3.new(0, a, 0)
end

local function build(fn: ((Piece) -> ()) -> ()): Pieces
	local t: Pieces = {}
	fn(function(p: Piece)
		table.insert(t, p)
	end)
	return t
end

local theme: DecorTypes.Theme = {
	Key = "DogeAltar",
	Name = "Doge Altar",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(28, -10), Facing = 180 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(0, 45),
		Vector2.new(-26, 32),
		Vector2.new(10, 22),
		Vector2.new(42, 10),
		Vector2.new(4, -4),
		Vector2.new(-32, -22),
		Vector2.new(-10, -42),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(34, -24),
	AutoPad = Vector2.new(26, -24),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Sun Temple Floor",
			Description = "Warm sandstone paving with a golden sun mosaic under the Cheems God and marble tiles along the winding path.",
			Pad = Vector2.new(-3, 52),
			PriceSeconds = 100,
			Pieces = build(function(add)
				add(B(0, 0.15, 0, 160, 0.3, 115, SAND, Sandstone))
				-- The sun mosaic: stacked flat slabs, none taller than 0.6 studs (so they never count as solid).
				add(B(28, 0.32, -10, 30, 0.3, 30, DGOLD, Metal))
				add(B(28, 0.38, -10, 22, 0.3, 22, GOLD, Metal))
				add(B(28, 0.44, -10, 12, 0.3, 12, CREAM, Marble))
				local tiles = {
					{ 0, 52 },
					{ 0, 45 },
					{ -26, 32 },
					{ 10, 22 },
					{ 42, 10 },
					{ 4, -4 },
					{ -32, -22 },
					{ -10, -42 },
					{ 0, -52 },
				}
				for _, t in tiles do
					add(B(t[1], 0.35, t[2], 9, 0.2, 9, STONE, Cobble))
				end
				add(B(-58, 0.3, -2, 14, 0.2, 14, DSAND, Cobble))
				add(B(50, 0.3, 30, 16, 0.2, 10, DSAND, Cobble))
			end),
		},
		-- 2
		{
			Id = "Gate",
			Name = "Pillar Gate",
			Description = "A tall gate of marble pillars with golden capitals and dog ears across the entrance.",
			Pad = Vector2.new(15, 52),
			PriceSeconds = 115,
			Pieces = build(function(add)
				for _, s in { -1, 1 } do
					add(B(s * 10, 1, 54, 5.6, 2, 5.6, STONE, Slate))
					add(Cy(s * 10, 8.5, 54, 3.4, 13, MARBLE, Marble))
					add(B(s * 10, 15.4, 54, 5, 1.2, 5, GOLD, Metal))
					add(B(s * 10.4, 17.6, 54, 1.8, 3.4, 1.6, GOLD, Metal, Vector3.new(0, 0, -s * 14)))
				end
				add(B(0, 12.4, 54, 24, 2.4, 3.2, MARBLE, Marble))
				add(B(0, 14.3, 54, 26, 1.4, 3.8, GOLD, Metal))
				add(B(0, 11.1, 54.4, 8, 1.2, 0.6, LAPIS, Plastic))
			end),
		},
		-- 3
		{
			Id = "Lanterns",
			Name = "Stone Lanterns",
			Description = "Four stone lanterns of different heights with golden roofs standing beside the entrance.",
			Pad = Vector2.new(-21, 45),
			PriceSeconds = 132,
			Pieces = build(function(add)
				local spots: { Spot } = {
					{ x = -24, z = 48.5, h = 8 },
					{ x = -19, z = 53, h = 6 },
					{ x = -19, z = 47, h = 5 },
					{ x = -31, z = 51, h = 7 },
				}
				for _, s in spots do
					add(Cy(s.x, s.h / 2, s.z, 1.6, s.h, STONE, Slate))
					add(B(s.x, s.h + 1.2, s.z, 3.2, 2.4, 3.2, CREAM, Plastic))
					add(B(s.x, s.h + 3, s.z, 4.4, 1.2, 4.4, GOLD, Metal))
				end
			end),
		},
		-- 4
		{
			Id = "Stall",
			Name = "Treat Stall",
			Description = "A striped market stall selling golden dog treats, with crates of bones beside it.",
			Pad = Vector2.new(-58, 40),
			PriceSeconds = 152,
			Pieces = build(function(add)
				add(B(-60, 1.6, 48, 12, 3.2, 5, WOOD, Wood))
				for _, sx in { -1, 1 } do
					add(Cy(-60 + sx * 6, 5, 45.4, 0.9, 10, DWOOD, Wood))
					add(Cy(-60 + sx * 6, 5, 51, 0.9, 10, DWOOD, Wood))
				end
				add(B(-60, 10.4, 48, 14, 1, 8, RED, Fabric, Vector3.new(-12, 0, 0)))
				add(B(-60, 9.4, 51.4, 14, 0.6, 1.6, CREAM, Fabric))
				add(B(-53.6, 1.4, 51.4, 3, 2.8, 3, WOOD, Wood, Ry(20)))
				add(B(-66, 1.2, 52, 3.4, 2.4, 3, WOOD, Wood, Ry(-25)))
				add(Ball(-60, 3.8, 47.6, 5, 1.6, 2.4, GOLD, Metal))
			end),
		},
		-- 5
		{
			Id = "Coins",
			Name = "Coin Hoards",
			Description = "Glittering heaps of golden coins of all sizes with a treasure chest and a giant standing coin.",
			Pad = Vector2.new(-54, 9),
			PriceSeconds = 175,
			Pieces = build(function(add)
				add(Ball(-62, 3, 12, 14, 6.4, 12, GOLD, Metal))
				add(Ball(-55, 2, 17, 9, 4, 8, DGOLD, Metal))
				add(Ball(-68, 2, 6, 8, 4, 8, GOLD, Metal))
				add(B(-57, 1.2, 8, 4, 2.4, 2.8, WOOD, Wood, Ry(25)))
				add(B(-57, 2.6, 8, 4, 0.8, 2.8, DGOLD, Metal, Ry(25)))
				add(Cx(-70, 5.4, 14, 8, 1.2, GOLD, Metal))
				add(Cy(-52, 1.2, 11, 2.6, 2.4, GOLD, Metal))
				add(Cy(-51, 0.8, 14, 2.2, 1.6, DGOLD, Metal))
			end),
		},
		-- 6
		{
			Id = "Fountain",
			Name = "Coin Fountain",
			Description = "A round marble fountain with a golden bone on top, spraying coins into a clear basin.",
			Pad = Vector2.new(28, 31),
			PriceSeconds = 201,
			Pieces = build(function(add)
				add(Cy(28, 1, 40, 16, 2, STONE, Slate))
				add(Cy(28, 2.1, 40, 13.4, 0.4, WATER, Glass))
				add(Cy(28, 5, 40, 2.8, 8, MARBLE, Marble))
				add(Cy(28, 8.6, 40, 8, 1.2, MARBLE, Marble))
				add(Cy(28, 9.6, 40, 6.6, 0.4, WATER, Glass))
				add(Cy(28, 11.2, 40, 1.6, 3, GOLD, Metal))
				add(Ball(28, 13.4, 40, 3.4, 3.4, 3.4, GOLD, Metal))
				add(Ball(23, 3, 38, 2.4, 2, 2.4, GOLD, Metal))
				add(Ball(32, 2.8, 43, 2.2, 1.8, 2.2, GOLD, Metal))
			end),
		},
		-- 7
		{
			Id = "Hall",
			Name = "Temple Hall",
			Description = "The great marble hall of the altar: a stepped base, a colonnade, a golden gabled roof and a dome on top.",
			Pad = Vector2.new(-62, -29),
			PriceSeconds = 231,
			Pieces = build(function(add)
				add(B(-62, 1, -45, 32, 2, 22, STONE, Slate))
				add(B(-62, 3, -45, 28, 2, 18, MARBLE, Marble))
				add(B(-62, 11, -48, 22, 16, 12, MARBLE, Marble))
				for k = 0, 5 do
					add(Cy(-71 + k * 4, 11, -39.5, 2.4, 16, CREAM, Marble))
				end
				add(B(-62, 20, -44.5, 28, 2, 17, GOLD, Metal))
				add(B(-62, 23.6, -46, 22, 3, 12, DGOLD, Metal))
				add(B(-62, 26, -47, 12, 3, 8, GOLD, Metal))
				add(Ball(-62, 29, -47, 9, 8, 9, GOLD, Metal))
				add(B(-62, 7, -41.9, 7, 10, 0.8, DWOOD, Wood))
			end),
		},
		-- 8
		{
			Id = "Torches",
			Yaw = -12,
			Name = "Torch Pillars",
			Description = "Tall stone pillars of different heights crowned with golden fire bowls.",
			Pad = Vector2.new(36, 20),
			PriceSeconds = 266,
			Pieces = build(function(add)
				local spots: { Spot } = {
					{ x = 40, z = 22, h = 9 },
					{ x = 46, z = 27, h = 7 },
					{ x = 49.5, z = 20.5, h = 10 },
					{ x = 43, z = 31, h = 6 },
				}
				for _, s in spots do
					add(Cy(s.x, s.h / 2, s.z, 1.8, s.h, STONE, Slate))
					add(Cy(s.x, s.h + 0.5, s.z, 3.8, 1, GOLD, Metal))
					add(B(s.x, s.h + 2.2, s.z, 2, 2.6, 2, RED, Plastic, Ry(30)))
				end
			end),
		},
		-- 9
		{
			Id = "Wall",
			Yaw = -10,
			Name = "Altar Wall",
			Description = "The shrine wall behind the Cheems God, with a golden sun niche and gilded pillars. The Shiba earns more.",
			Pad = Vector2.new(40, -4),
			RewardMult = 1.25,
			PriceSeconds = 306,
			Pieces = build(function(add)
				add(B(45, 1, -12, 9, 2, 22, STONE, Slate))
				add(B(47, 9, -12, 5, 16, 20, MARBLE, Marble))
				add(B(46.4, 18.2, -12, 7, 2, 22, GOLD, Metal))
				add(Cx(43.6, 10, -12, 11, 1.2, GOLD, Metal))
				add(Cx(43.4, 10, -12, 7, 1.4, CREAM, Marble))
				for _, s in { -1, 1 } do
					add(Cy(43.5, 8.5, -12 + s * 9, 2.4, 15, DGOLD, Metal))
					add(B(43.5, 16.4, -12 + s * 9, 3.4, 1.2, 3.4, GOLD, Metal))
					add(B(45.4, 6, -12 + s * 5, 2.8, 8, 0.8, LAPIS, Plastic))
				end
			end),
		},
		-- 10
		{
			Id = "Pond",
			Yaw = 8,
			Name = "Koi Pond",
			Description = "A calm pond of golden koi with lily pads, a stone rim and a little arched bridge.",
			Pad = Vector2.new(46, 38),
			PriceSeconds = 352,
			Pieces = build(function(add)
				add(B(56, 0.3, 47, 26, 0.3, 14, WATER, Glass))
				add(B(56, 0.9, 40, 28, 1.2, 1.4, STONE, Slate))
				add(B(56, 0.9, 54, 28, 1.2, 1.4, STONE, Slate))
				add(B(42.4, 0.9, 47, 1.4, 1.2, 16, STONE, Slate))
				add(B(69.6, 0.9, 47, 1.4, 1.2, 16, STONE, Slate))
				add(B(51, 1.9, 47, 5, 0.8, 4, WOOD, Wood, Vector3.new(0, 0, 14)))
				add(B(56, 2.5, 47, 6, 0.8, 4, WOOD, Wood))
				add(B(61, 1.9, 47, 5, 0.8, 4, WOOD, Wood, Vector3.new(0, 0, -14)))
				add(B(56, 3.6, 45.2, 15, 0.5, 0.6, RED, Wood))
				add(Cy(48, 0.5, 50, 3.4, 0.3, GREEN, Plastic))
				add(Cy(63, 0.5, 43, 3, 0.3, GREEN, Plastic))
				add(Ball(52, 0.6, 43, 3, 1, 1.4, FUR, Plastic))
			end),
		},
		-- 11
		{
			Id = "Pagoda",
			Yaw = -14,
			Name = "Doge Pagoda",
			Description = "A three-storey pagoda with red curved roofs and a golden spire.",
			Pad = Vector2.new(57, 6),
			PriceSeconds = 405,
			Pieces = build(function(add)
				add(B(68, 0.8, 8, 16, 1.6, 16, STONE, Slate))
				add(B(68, 4.8, 8, 8, 6.4, 8, CREAM, Plastic))
				add(B(68, 8.65, 8, 14.4, 1.3, 14.4, RED, Plastic))
				add(B(68, 12, 8, 6.1, 5.4, 6.1, CREAM, Plastic))
				add(B(68, 15.25, 8, 11.2, 1.1, 11.2, RED, Plastic))
				add(B(68, 18.2, 8, 4.3, 4.8, 4.3, CREAM, Plastic))
				add(B(68, 21.15, 8, 8, 1.1, 8, RED, Plastic))
				add(Cy(68, 24.1, 8, 0.8, 4.8, GOLD, Metal))
				add(Ball(68, 27.5, 8, 2, 2, 2, GOLD, Metal))
				add(B(68, 3.6, 12.2, 2.7, 4, 0.4, DWOOD, Wood))
			end),
		},
		-- 12
		{
			Id = "Guardians",
			Yaw = 25,
			Name = "Guardian Statues",
			Description = "Two marble dog statues of different sizes sit guard on stone bases, with golden collars and ears.",
			Pad = Vector2.new(-12, 0),
			PriceSeconds = 465,
			Pieces = build(function(add)
				local spots: { Spot } = { { x = -17, z = 6, h = 1 }, { x = -8, z = 13, h = 0.85 } }
				for _, s in spots do
					local x, z, k = s.x, s.z, s.h
					add(B(x, 1, z, 6 * k, 2, 6 * k, STONE, Slate))
					add(B(x, 6.5 * k + 1, z, 4 * k, 9 * k, 3.6 * k, MARBLE, Marble))
					add(B(x, 13 * k + 1, z, 4.6 * k, 3.6 * k, 4 * k, MARBLE, Marble))
					add(B(x - 1.6 * k, 16 * k + 1, z, 1.2 * k, 2.4 * k, 0.8 * k, GOLD, Metal))
					add(B(x + 1.6 * k, 16 * k + 1, z, 1.2 * k, 2.4 * k, 0.8 * k, GOLD, Metal))
					add(B(x, 10.6 * k + 1, z, 4.4 * k, 0.8, 4 * k, GOLD, Metal))
				end
			end),
		},
		-- 13
		{
			Id = "Banners",
			Yaw = -20,
			Name = "Wow Banners",
			Description = "Three tall cloth banners of different heights on gold-capped poles.",
			Pad = Vector2.new(-44, -6),
			PriceSeconds = 535,
			Pieces = build(function(add)
				local spots: { Spot } = {
					{ x = -48, z = 3, h = 16, color = RED },
					{ x = -43, z = -1, h = 13, color = LAPIS },
					{ x = -40, z = 5, h = 15, color = RED },
				}
				for _, s in spots do
					add(B(s.x, 0.6, s.z, 2.4, 1.2, 2.4, STONE, Slate))
					add(Cy(s.x, s.h / 2, s.z, 0.7, s.h, DWOOD, Wood))
					add(B(s.x, s.h - 4.4, s.z + 1.9, 3.4, 7, 0.3, s.color or RED, Fabric))
					add(Ball(s.x, s.h + 0.6, s.z, 1.4, 1.4, 1.4, GOLD, Metal))
				end
			end),
		},
		-- 14
		{
			Id = "BoneArch",
			Yaw = 12,
			Name = "Bone Arch",
			Description = "A huge arch made of two giant bones with a golden skull charm on top.",
			Pad = Vector2.new(-60, -4),
			PriceSeconds = 615,
			Pieces = build(function(add)
				add(Cy(-73, 9, -12, 3.4, 18, BONE, Slate))
				add(Cy(-59, 9, -12, 3.4, 18, BONE, Slate))
				add(Cx(-66, 18.4, -12, 3.4, 18, BONE, Slate))
				for _, x in { -73, -59 } do
					add(Ball(x, 1.2, -13.4, 3.4, 3.4, 3.4, BONE, Slate))
					add(Ball(x, 1.2, -10.6, 3.4, 3.4, 3.4, BONE, Slate))
				end
				add(Ball(-75, 19.6, -13.4, 3.4, 3.4, 3.4, BONE, Slate))
				add(Ball(-75, 19.6, -10.6, 3.4, 3.4, 3.4, BONE, Slate))
				add(Ball(-57, 19.6, -13.4, 3.4, 3.4, 3.4, BONE, Slate))
				add(Ball(-57, 19.6, -10.6, 3.4, 3.4, 3.4, BONE, Slate))
				add(Ball(-66, 21.6, -12, 3.4, 3.4, 3.4, GOLD, Metal))
			end),
		},
		-- 15
		{
			Id = "BonePillars",
			Name = "Golden Bone Pillars",
			Description = "Three tall golden pillars shaped like giant bones, each with knobbed ends, rising from a marble slab.",
			Pad = Vector2.new(9, -35),
			PriceSeconds = 708,
			Pieces = build(function(add)
				add(B(18, 0.6, -38, 14, 1.2, 14, MARBLE, Marble))
				local pillars: { Spot } = {
					{ x = 14, z = -34, h = 14 },
					{ x = 22, z = -34, h = 18 },
					{ x = 18, z = -42, h = 22 },
				}
				for _, s in pillars do
					local top = 1.2 + s.h
					add(Cy(s.x, 1.2 + s.h / 2, s.z, 2.4, s.h, GOLD, Metal))
					add(Ball(s.x - 0.9, top, s.z, 2.4, 2.4, 2.4, LGOLD, Metal))
					add(Ball(s.x + 0.9, top, s.z, 2.4, 2.4, 2.4, LGOLD, Metal))
					add(Ball(s.x - 0.9, 2.3, s.z, 2.4, 2.4, 2.4, LGOLD, Metal))
					add(Ball(s.x + 0.9, 2.3, s.z, 2.4, 2.4, 2.4, LGOLD, Metal))
				end
			end),
		},
		-- 16
		{
			Id = "Garden",
			Name = "Sacred Garden",
			Description = "Trimmed hedges, flower beds and three blossoming trees around a small stone path.",
			Pad = Vector2.new(-38, 21),
			PriceSeconds = 814,
			Pieces = build(function(add)
				add(B(-50, 2, 24, 12, 4, 2.6, DGREEN, Grass))
				add(B(-38, 2, 24, 8, 4, 2.6, DGREEN, Grass))
				add(B(-34, 1.5, 28, 2.6, 3, 8, DGREEN, Grass))
				add(B(-48, 0.8, 28.5, 8, 1.6, 5, GREEN, Grass))
				add(Ball(-50, 2, 28, 2, 2, 2, PINK, Plastic))
				add(Ball(-47, 2, 29.6, 2, 2, 2, GOLD, Plastic))
				add(Ball(-46, 2, 27.4, 2, 2, 2, PINK, Plastic))
				add(Cy(-40, 3, 32.5, 1.6, 6, WOOD, Wood))
				add(Ball(-40, 8, 32.5, 7, 6, 7, GREEN, Grass))
				add(Cy(-54, 3.4, 31.5, 1.8, 6.8, WOOD, Wood))
				add(Ball(-54, 9, 31.5, 8, 7, 7, DGREEN, Grass))
				add(Cy(-44, 3.8, 21, 1.6, 7.6, WOOD, Wood))
				add(Ball(-44, 9.6, 21, 7.4, 6.4, 7.4, PINK, Grass))
				add(B(-43, 0.4, 29, 3, 0.2, 16, STONE, Cobble))
			end),
		},
		-- 17
		{
			Id = "Tablets",
			Yaw = 20,
			Name = "Meme Tablets",
			Description = "Three tall stone tablets carved with golden doge glyphs on a low slab.",
			Pad = Vector2.new(-43, -11),
			PriceSeconds = 936,
			Pieces = build(function(add)
				add(B(-47, 0.5, -17, 16, 1, 7, STONE, Slate))
				add(B(-52, 5.5, -17, 4.6, 9, 1.2, MARBLE, Marble, Ry(12)))
				add(B(-47, 7, -17, 5.4, 12, 1.4, MARBLE, Marble))
				add(B(-42, 5, -18, 4.2, 8, 1.2, MARBLE, Marble, Ry(-14)))
				add(B(-52, 6.4, -16.3, 2.6, 2.2, 0.4, GOLD, Metal, Ry(12)))
				add(B(-47, 8, -16.2, 3, 2.6, 0.4, GOLD, Metal))
				add(B(-42, 5.6, -17.3, 2.4, 2, 0.4, GOLD, Metal, Ry(-14)))
				add(B(-47, 13.4, -17, 6, 0.8, 1.8, GOLD, Metal))
			end),
		},
		-- 18
		{
			Id = "Throne",
			Yaw = -10,
			Name = "Doge Throne",
			Description = "A golden throne with dog ears on top, a red cushion and a lapis gem, standing on marble steps. The Shiba earns more.",
			Pad = Vector2.new(10, -50),
			RewardMult = 1.4,
			PriceSeconds = 1238,
			Pieces = build(function(add)
				add(B(20, 0.6, -48.5, 15, 1.2, 12, STONE, Slate))
				add(B(20, 1.8, -48.5, 12, 1.2, 9.4, MARBLE, Marble))
				add(B(20, 4.2, -48.5, 7, 3.6, 6, GOLD, Metal))
				add(B(23, 10, -48.5, 2, 14, 8, GOLD, Metal))
				add(B(20, 6.4, -51.9, 6, 1.8, 1.4, DGOLD, Metal))
				add(B(20, 6.4, -45.1, 6, 1.8, 1.4, DGOLD, Metal))
				add(B(19.4, 6.2, -48.5, 4.6, 1, 4.8, RED, Fabric))
				add(B(23, 17.6, -51.5, 1.4, 3.6, 1.6, GOLD, Metal))
				add(B(23, 17.6, -45.5, 1.4, 3.6, 1.6, GOLD, Metal))
				add(Ball(23, 15.4, -48.5, 2, 2, 2, LAPIS, Glass))
			end),
		},
		-- 19
		{
			Id = "AltarTable",
			Name = "Altar Table",
			Description = "A marble altar table with a red and gold cloth, golden bowls, a treat cake and two candlesticks, with a bench on each side.",
			Pad = Vector2.new(-26, 13),
			PriceSeconds = 1238,
			Pieces = build(function(add)
				add(B(-24, 3.4, 16, 14, 1.2, 6, MARBLE, Marble))
				for _, sx in { -1, 1 } do
					for _, sz in { -1, 1 } do
						add(B(-24 + sx * 6, 1.4, 16 + sz * 2, 1.2, 2.8, 1.2, DGOLD, Metal))
					end
				end
				add(B(-24, 4.1, 16, 14.4, 0.3, 2.8, RED, Fabric))
				add(Cy(-28, 5.2, 16, 3.2, 1.6, GOLD, Metal))
				add(Cy(-24, 5.6, 16, 3.4, 2.4, CREAM, Plastic))
				add(Ball(-24, 7.2, 16, 2, 1.6, 2, PINK, Plastic))
				for _, sx in { -1, 1 } do
					add(Cy(-24 + sx * 5.4, 6.2, 16, 0.8, 4, GOLD, Metal))
					add(B(-24 + sx * 5.4, 8.7, 16, 0.9, 1.2, 0.9, RED, Plastic))
				end
				add(B(-24, 1.6, 11.4, 13, 0.8, 1.8, MARBLE, Marble))
				add(B(-24, 1.6, 20.6, 13, 0.8, 1.8, MARBLE, Marble))
			end),
		},
		-- 20
		{
			Id = "Kennel",
			Name = "Golden Kennel",
			Description = "A cosy wooden kennel with a gold roof, a bone sign and a golden food bowl.",
			Pad = Vector2.new(54, -24),
			PriceSeconds = 1423,
			Pieces = build(function(add)
				add(B(62, 0.4, -22, 12, 0.8, 12, DWOOD, Wood))
				add(B(62, 4.8, -22, 10, 8, 10, WOOD, Wood))
				add(B(62, 11.4, -25.4, 12, 0.8, 6.6, GOLD, Metal, Vector3.new(-35, 0, 0)))
				add(B(62, 11.4, -18.6, 12, 0.8, 6.6, GOLD, Metal, Vector3.new(35, 0, 0)))
				add(B(56.9, 3.4, -22, 0.4, 6.4, 5, DSTONE, Slate))
				add(Cy(53.5, 0.7, -17, 3.4, 1.4, GOLD, Metal))
				add(B(56.4, 7.6, -22, 0.5, 2.2, 5, CREAM, Wood))
				add(Cx(52.5, 0.6, -20, 1, 3.6, BONE, Slate))
			end),
		},
		-- 21
		{
			Id = "Bells",
			Name = "Shrine Bells",
			Description = "A red wooden frame with a golden roof from which three big bronze bells hang.",
			Pad = Vector2.new(-28, -4),
			PriceSeconds = 1637,
			Pieces = build(function(add)
				add(B(-28, 0.5, 4, 17, 1, 5, STONE, Slate))
				add(Cy(-34, 8, 4, 1.6, 15, RED, Wood))
				add(Cy(-22, 8, 4, 1.6, 15, RED, Wood))
				add(B(-28, 15.2, 4, 15, 1.6, 1.8, RED, Wood))
				add(B(-28, 16.8, 4, 17, 1, 3.4, GOLD, Metal))
				add(Ball(-31, 11, 4, 3.4, 4, 3.4, GOLD, Metal))
				add(Ball(-28, 10.4, 4, 4.4, 5, 4.4, DGOLD, Metal))
				add(Ball(-25, 11, 4, 3.4, 4, 3.4, GOLD, Metal))
			end),
		},
		-- 22
		{
			Id = "Sun",
			Yaw = -12,
			Name = "Sun Disc",
			Description = "A giant golden sun disc with eight rays on a marble stand, facing the Shiba. The Shiba earns more.",
			Pad = Vector2.new(64, -8),
			RewardMult = 1.4,
			PriceSeconds = 1882,
			Pieces = build(function(add)
				add(B(73, 1, -10, 8, 2, 20, STONE, Slate))
				add(B(73, 4, -10, 4, 4, 6, MARBLE, Marble))
				add(Cx(71.4, 15, -10, 20, 2, GOLD, Metal))
				add(Cx(70.4, 15, -10, 13, 1.2, CREAM, Marble))
				add(Ball(69.8, 15, -10, 5, 5, 5, RED, Plastic))
				for k = 0, 7 do
					local a = k * 45
					local r = 12.4
					add(
						B(
							71.4,
							15 + r * math.cos(math.rad(a)),
							-10 + r * math.sin(math.rad(a)),
							1.6,
							4,
							1.8,
							GOLD,
							Metal,
							Vector3.new(a, 0, 0)
						)
					)
				end
			end),
		},
		-- 23
		{
			Id = "Crown",
			Yaw = 15,
			Name = "Crown Monument",
			Description = "A giant golden crown with red and blue jewels resting on a marble pillar. The Shiba earns more.",
			Pad = Vector2.new(-4, -35),
			RewardMult = 1.5,
			PriceSeconds = 2164,
			Pieces = build(function(add)
				add(B(0, 1, -26, 10, 2, 10, STONE, Slate))
				add(Cy(0, 7, -26, 4, 10, MARBLE, Marble))
				add(Cy(0, 13.5, -26, 10, 3, GOLD, Metal))
				for k = 0, 4 do
					local a = math.rad(k * 72)
					add(B(3.9 * math.cos(a), 17.6, -26 + 3.9 * math.sin(a), 1.8, 5, 1.8, GOLD, Metal))
				end
				add(Ball(0, 15.4, -26, 3, 3, 3, RED, Glass))
				add(Ball(0, 19, -26, 2.4, 2.4, 2.4, LAPIS, Glass))
			end),
		},
		-- 24
		{
			Id = "Cheems",
			Yaw = 10,
			Name = "Cheems Statue",
			Description = "A seated golden Cheems statue with a red collar on a stone base.",
			Pad = Vector2.new(40, -34),
			PriceSeconds = 2489,
			Pieces = build(function(add)
				add(B(38, 1, -46, 12, 2, 12, STONE, Slate))
				add(Ball(39.4, 6.6, -46, 8, 8, 6.4, GOLD, Metal))
				add(B(37, 10, -46, 5, 8, 5, GOLD, Metal))
				add(Ball(36.4, 16, -46, 6.6, 6, 6, GOLD, Metal))
				add(B(34.2, 15.2, -46, 2.6, 2.2, 2.6, CREAM, Plastic))
				add(B(37, 19.8, -48.4, 1.4, 3.4, 1.2, DGOLD, Metal))
				add(B(37, 19.8, -43.6, 1.4, 3.4, 1.2, DGOLD, Metal))
				add(Ball(43, 5, -46, 3.4, 5, 2, GOLD, Metal))
				add(B(36.8, 12.8, -46, 5.6, 1, 5.6, RED, Fabric))
			end),
		},
		-- 25
		{
			Id = "AltarSteps",
			Yaw = 8,
			Name = "Altar Steps",
			Description = "White-gold marble steps in four broad tiers with gold bands, a front stair, two fire bowls and a golden altar block on top.",
			Pad = Vector2.new(-30, -38),
			PriceSeconds = 2862,
			Pieces = build(function(add)
				add(B(-35, 1.2, -50, 18, 2.4, 11, MARBLE, Marble))
				add(B(-35, 2.6, -50, 18.8, 0.4, 11.8, GOLD, Metal))
				add(B(-35, 4.4, -50, 14, 3.2, 8.8, MARBLE, Marble))
				add(B(-35, 6.2, -50, 14.8, 0.4, 9.6, GOLD, Metal))
				add(B(-35, 8, -50, 10, 3.2, 6.6, MARBLE, Marble))
				add(B(-35, 9.8, -50, 10.8, 0.4, 7.4, GOLD, Metal))
				add(B(-35, 12, -50, 6, 4, 4, CREAM, Marble))
				add(B(-35, 14.3, -50, 7, 0.6, 5, GOLD, Metal))
				for _, s in { -1, 1 } do
					add(Cy(-35 + s * 4.2, 11.2, -47.6, 1.4, 2.4, DGOLD, Metal))
					add(B(-35 + s * 4.2, 13, -47.6, 1.2, 1.6, 1.2, RED, Plastic))
				end
				add(B(-35, 0.4, -43.1, 8, 0.8, 2.8, MARBLE, Marble))
				add(B(-35, 0.8, -43.8, 8, 1.6, 1.4, MARBLE, Marble))
			end),
		},
		-- 26
		{
			Id = "HaloArch",
			Name = "Halo Arch",
			Description = "A great golden halo ring held up by two marble pillars with golden caps.",
			Pad = Vector2.new(60, 22),
			PriceSeconds = 3291,
			Pieces = build(function(add)
				for _, s in { -1, 1 } do
					add(B(67 + s * 9, 1.2, 27, 4.4, 2.4, 4, MARBLE, Marble))
					add(Cy(67 + s * 9, 10.9, 27, 2.6, 17, MARBLE, Marble))
					add(B(67 + s * 9, 19.8, 27, 3.4, 0.8, 3.4, GOLD, Metal))
				end
				-- The ring: ten gold segments around (67, 19.5), radius 9; its lowest point is 10.5 studs up, so players walk under it.
				for k = 0, 9 do
					local phi = 18 + k * 36
					local rad = math.rad(phi)
					add(
						B(
							67 + 9 * math.cos(rad),
							19.5 + 9 * math.sin(rad),
							27,
							6,
							1.5,
							2.4,
							if k % 2 == 0 then GOLD else LGOLD,
							Metal,
							Vector3.new(0, 0, phi + 90)
						)
					)
				end
			end),
		},
		-- 27
		{
			Id = "Vault",
			Yaw = 15,
			Name = "Treasure Vault",
			Description = "A stone vault with a golden door, marble pillars and stacks of coins in front.",
			Pad = Vector2.new(-74, 40),
			PriceSeconds = 3785,
			Pieces = build(function(add)
				add(B(-71, 6, 28, 12, 12, 10, STONE, Brick))
				add(B(-71, 12.8, 28, 14, 1.6, 12, DGOLD, Metal))
				add(B(-64.8, 4, 28, 0.4, 7, 5, GOLD, Metal))
				add(B(-64.5, 4.6, 28, 0.8, 8.4, 6.6, DSTONE, Slate))
				add(Cy(-65.6, 5, 24.6, 1.6, 10, MARBLE, Marble))
				add(Cy(-65.6, 5, 31.4, 1.6, 10, MARBLE, Marble))
				add(Ball(-71, 15, 28, 3, 3, 3, GOLD, Metal))
				add(Cy(-63, 1, 24, 3, 2, GOLD, Metal))
				add(Cy(-62, 1, 32, 3, 2, GOLD, Metal))
			end),
		},
		-- 28
		{
			Id = "WishTree",
			Name = "Wish Tree",
			Description = "A blossoming wish tree hung with red and golden ribbons.",
			Pad = Vector2.new(-33, 38),
			PriceSeconds = 4353,
			Pieces = build(function(add)
				add(Cy(-43, 5, 49.5, 3.6, 10, WOOD, Wood))
				add(Cy(-46, 10, 49.5, 1.4, 6, WOOD, Wood, 0, 30))
				add(Cy(-40, 10, 49.5, 1.4, 6, WOOD, Wood, 0, -30))
				add(Ball(-43, 14, 49.5, 14, 8, 13, PINK, Fabric))
				add(Ball(-38, 12, 51.5, 8, 6, 8, CREAM, Fabric))
				add(Ball(-48, 12, 47.5, 8, 6, 8, PINK, Fabric))
				add(B(-37, 8.4, 46.5, 0.5, 6, 0.5, RED, Fabric))
				add(B(-40.5, 8.6, 55.5, 0.5, 6, 0.5, GOLD, Fabric))
				add(B(-47, 8.8, 44.5, 0.5, 6, 0.5, RED, Fabric))
				add(B(-49, 9, 52.5, 0.5, 6, 0.5, GOLD, Fabric))
			end),
		},
		-- 29
		{
			Id = "HolyLight",
			Name = "Holy Light",
			Description = "A towering column of warm golden light rising from a marble dais, ringed by three floating halo discs and a shining star.",
			Pad = Vector2.new(9, 28.5),
			PriceSeconds = 5006,
			Pieces = build(function(add)
				add(Cy(14, 0.6, 36, 10, 1.2, MARBLE, Marble))
				add(Cy(14, 1.4, 36, 8, 0.4, GOLD, Metal))
				add(Cy(14, 2.2, 36, 6, 1.2, CREAM, Marble))
				add(Cy(14, 16, 36, 4.6, 26, PALE, Plastic))
				add(Cy(14, 17, 36, 2.2, 28, GLOW, Plastic))
				add(Cy(14, 10, 36, 9, 0.5, GOLD, Metal))
				add(Cy(14, 18, 36, 7, 0.5, GOLD, Metal))
				add(Cy(14, 26, 36, 5.4, 0.5, GOLD, Metal))
				add(Ball(14, 31.5, 36, 3.2, 3.2, 3.2, GLOW, Plastic))
				for _, c in { { -1, -1 }, { -1, 1 }, { 1, -1 }, { 1, 1 } } do
					add(B(14 + c[1] * 3.6, 21, 36 + c[2] * 3.6, 1.4, 3, 1.4, LGOLD, Metal, Ry(45)))
				end
			end),
		},
		-- 30
		{
			Id = "Colossus",
			Yaw = -15,
			Name = "Giant Doge Statue",
			Description = "The giant seated golden Doge guarding the altar, with a cream snoot, a red collar and tall ears. The Shiba earns much more.",
			Pad = Vector2.new(50, -34),
			RewardMult = 1.7,
			PriceSeconds = 5757,
			Pieces = build(function(add)
				add(B(60, 1, -43, 22, 2, 20, STONE, Slate))
				add(B(60, 3, -43, 18, 2, 16, MARBLE, Marble))
				add(Ball(62, 11, -43, 16, 16, 15, GOLD, Metal))
				add(B(59, 22, -43, 10, 24, 11, GOLD, Metal))
				add(B(54.2, 13, -47, 3.6, 18, 3.6, GOLD, Metal))
				add(B(54.2, 13, -39, 3.6, 18, 3.6, GOLD, Metal))
				add(B(52.4, 5.4, -47, 5, 2.6, 4.2, CREAM, Plastic))
				add(B(52.4, 5.4, -39, 5, 2.6, 4.2, CREAM, Plastic))
				add(Ball(56, 38, -43, 15, 14, 13, GOLD, Metal))
				add(B(49.6, 36, -43, 7, 5, 6, CREAM, Plastic))
				add(B(46, 37, -43, 1.6, 1.6, 2.4, DSTONE, Slate))
				add(B(60, 47.5, -48.6, 3, 7, 3, DGOLD, Metal))
				add(B(60, 47.5, -37.4, 3, 7, 3, DGOLD, Metal))
				add(B(70.6, 8, -43, 3, 10, 5, GOLD, Metal, Vector3.new(0, 0, -20)))
				add(B(56.4, 28.8, -43, 3.8, 3, 14, RED, Fabric))
			end),
		},
	},
}

return theme
