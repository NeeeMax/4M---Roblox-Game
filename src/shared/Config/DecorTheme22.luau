--!strict
-- Theme of the Shiba of bay 22: Dragon Lair (Config/DecorTypes -> Theme). 160 x 115: Dragon Shiba stands on a gold plaza in front of a
-- huge dragon cave in the left of the plot (a giant green dragon is perched on its roof); a winding walkway leads through a skull gate
-- past the hatchery, the forge, a ruined tower, the dragon keep and a smoking volcano, with bone piles, crystals and loot in loose groups.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lava, fire and gems are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local FLOOR = C(54, 48, 60)
local PATHC = C(104, 94, 104)
local ROCK = C(84, 76, 90)
local DROCK = C(56, 50, 64)
local OBS = C(30, 26, 38)
local LAVA = C(238, 96, 28)
local EMBER = C(255, 168, 52)
local GOLD = C(240, 190, 52)
local DGOLD = C(186, 136, 36)
local BONE = C(232, 224, 198)
local SCALE = C(58, 152, 82)
local DSCALE = C(30, 100, 62)
local EMER = C(84, 224, 170)
local RUBY = C(214, 52, 64)
local WOOD = C(112, 78, 50)
local DWOOD = C(80, 56, 38)
local IRON = C(118, 122, 136)
local DIRON = C(62, 64, 76)
local CLOTH = C(176, 42, 52)
local STONE = C(150, 144, 152)
local HAY = C(176, 146, 86)
local PURPLE = C(140, 100, 230)
local CREAM = C(228, 232, 214)

local Basalt = Enum.Material.Basalt
local Slate = Enum.Material.Slate
local Granite = Enum.Material.Granite
local Metal = Enum.Material.Metal
local Wood = Enum.Material.Wood
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Glass = Enum.Material.Glass
local Cobble = Enum.Material.Cobblestone

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

-- Cylinder lying along Z (a wheel facing sideways): diameter d, thickness len.
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
	Key = "DragonLair",
	Name = "Dragon Lair",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(-30, -6), Facing = 0 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(-24, 40),
		Vector2.new(16, 26),
		Vector2.new(46, 6),
		Vector2.new(6, -10),
		Vector2.new(-8, -34),
		Vector2.new(30, -44),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(-31, 7),
	AutoPad = Vector2.new(-23, 7),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Lair Floor",
			Description = "Dark volcanic rock with lava streams, glowing path plates and a golden plaza under the Dragon Shiba.",
			Pad = Vector2.new(-8, 50),
			PriceSeconds = 54,
			Pieces = build(function(add)
				add(B(0, 0.15, 0, 160, 0.3, 115, FLOOR, Basalt))
				add(B(-30, 0.3, -6, 26, 0.3, 26, DGOLD, Metal))
				add(B(-30, 0.4, -6, 18, 0.3, 18, GOLD, Metal))
				add(B(-60, 0.3, -52, 34, 0.3, 5, LAVA, Plastic))
				add(B(66, 0.3, -14, 6, 0.3, 28, LAVA, Plastic))
				add(B(-47, 0.3, -27, 5, 0.3, 14, LAVA, Plastic))
				add(B(0, 0.35, 52, 9, 0.2, 9, PATHC, Cobble))
				add(B(-24, 0.35, 40, 9, 0.2, 9, PATHC, Cobble))
				add(B(16, 0.35, 26, 9, 0.2, 9, PATHC, Cobble))
				add(B(46, 0.35, 6, 9, 0.2, 9, PATHC, Cobble))
				add(B(6, 0.35, -10, 9, 0.2, 9, PATHC, Cobble))
				add(B(-8, 0.35, -34, 9, 0.2, 9, PATHC, Cobble))
				add(B(30, 0.35, -44, 9, 0.2, 9, PATHC, Cobble))
				add(B(0, 0.35, -52, 9, 0.2, 9, PATHC, Cobble))
			end),
		},
		-- 2
		{
			Id = "Cave",
			Yaw = -8,
			Name = "Dragon Cave",
			Description = "A huge rock mountain with a fanged cave mouth, the home of the Dragon Shiba.",
			Pad = Vector2.new(-50, -24),
			PriceSeconds = 62,
			Pieces = build(function(add)
				add(B(-68, 13, -8, 16, 26, 32, ROCK, Basalt))
				add(B(-60.5, 8, -19.5, 9, 16, 10, DROCK, Basalt, Ry(14)))
				add(B(-61, 7, 5, 8, 14, 11, DROCK, Basalt, Ry(-16)))
				add(B(-59.4, 6.5, -9.5, 1.6, 13, 12, OBS, Slate))
				add(B(-58.2, 8, -16.8, 3.2, 16, 3.4, ROCK, Basalt))
				add(B(-58.2, 8, -2.2, 3.2, 16, 3.4, ROCK, Basalt))
				add(B(-58, 16.8, -9.5, 3.6, 3.4, 18.6, DROCK, Granite))
				add(B(-57.6, 13.7, -14, 1.2, 2.8, 1.2, BONE, Slate))
				add(B(-57.6, 13.7, -9.5, 1.2, 2.8, 1.2, BONE, Slate))
				add(B(-57.6, 13.7, -5, 1.2, 2.8, 1.2, BONE, Slate))
				add(B(-59, 3, -9.5, 1.2, 5, 8, LAVA, Plastic))
				add(Ball(-69, 26, -10, 17, 10, 24, ROCK, Basalt))
				add(B(-74, 27, -20, 5, 10, 5, DROCK, Basalt, Vector3.new(8, 30, -6)))
				add(B(-73, 28, 3, 4.4, 9, 4.4, DROCK, Basalt, Vector3.new(-6, -24, 5)))
			end),
		},
		-- 3
		{
			Id = "Hoard",
			Yaw = 12,
			Name = "Gold Hoard",
			Description = "A glittering heap of gold, gems and chests spilling out of the cave mouth.",
			Pad = Vector2.new(-44, 2),
			PriceSeconds = 71,
			Pieces = build(function(add)
				add(Ball(-48, 3, -8, 13, 7, 12, GOLD, Metal))
				add(Ball(-47, 2, -1.5, 8, 5, 8, DGOLD, Metal))
				add(Ball(-51, 2.2, -14, 8, 5, 7, GOLD, Metal))
				add(Ball(-44, 1.4, -13, 5, 3, 5, GOLD, Metal))
				add(B(-45.5, 1.2, -17, 4, 2.4, 2.8, WOOD, Wood, Ry(25)))
				add(B(-45.5, 2.6, -17, 4, 0.8, 2.8, DGOLD, Metal, Ry(25)))
				add(B(-52.5, 1.2, -3, 3.4, 2.4, 2.4, WOOD, Wood, Ry(-30)))
				add(Cy(-43, 1.4, -5, 1.2, 2.8, GOLD, Metal))
				add(Ball(-49, 6.8, -9, 1.6, 1.6, 1.6, RUBY, Glass))
				add(Ball(-46, 5.8, -6, 1.3, 1.3, 1.3, EMER, Glass))
				add(Ball(-51.5, 4.6, -11.5, 1.2, 1.2, 1.2, EMER, Glass))
				add(B(-48, 7.9, -8, 2.6, 1.2, 2.6, GOLD, Metal))
			end),
		},
		-- 4
		{
			Id = "Braziers",
			Yaw = 15,
			Name = "Fire Braziers",
			Description = "Three iron fire bowls of different heights burning beside the entrance.",
			Pad = Vector2.new(11, 47),
			PriceSeconds = 82,
			Pieces = build(function(add)
				local spots = { { 10, 52, 9, 0 }, { 17, 46, 7, 25 }, { 5, 44, 6, -20 } }
				for _, s in spots do
					local x, z, h, a = s[1], s[2], s[3], s[4]
					add(B(x, 0.4, z, 3.4, 0.8, 3.4, ROCK, Basalt, Ry(a + 20)))
					add(Cy(x, h / 2, z, 0.9, h, DIRON, Metal))
					add(Cy(x, h + 0.5, z, 4, 1, IRON, Metal))
					add(B(x, h + 2.2, z, 2.2, 3, 2.2, LAVA, Plastic, Ry(a)))
				end
				add(Ball(13.5, 0.8, 49.5, 3.4, 1.6, 3, DROCK, Basalt))
				add(Ball(8, 0.7, 47.5, 2.4, 1.4, 2.4, ROCK, Basalt))
			end),
		},
		-- 5
		{
			Id = "Hatchery",
			Yaw = -14,
			Name = "Dragon Nest",
			Description = "A twig nest on a bed of hay with three speckled dragon eggs.",
			Pad = Vector2.new(-52, 37),
			PriceSeconds = 94,
			Pieces = build(function(add)
				add(Cy(-50, 0.7, 47, 13, 1.4, HAY, Fabric))
				for k = 0, 7 do
					local a = math.rad(k * 45 + 10)
					local x, z = -50 + 7.4 * math.cos(a), 47 + 7.4 * math.sin(a)
					add(B(x, 1.4, z, 6.4, 2.2, 1.4, WOOD, Wood, Ry(math.deg(math.atan2(-math.cos(a), -math.sin(a))))))
				end
				add(Ball(-50.5, 4, 47.5, 5.4, 7.6, 5.4, SCALE, Plastic))
				add(Ball(-47, 3.3, 50, 4.6, 6.2, 4.6, DSCALE, Plastic))
				add(Ball(-53, 3.1, 44.5, 4.4, 6, 4.4, GOLD, Plastic))
				add(Ball(-49, 5.6, 45.2, 0.9, 0.9, 0.9, EMBER, Plastic))
				add(Ball(-51.8, 6.4, 49, 0.9, 0.9, 0.9, EMBER, Plastic))
			end),
		},
		-- 6
		{
			Id = "Stalagmites",
			Yaw = 12,
			Name = "Rock Spikes",
			Description = "Jagged rock spikes of all sizes growing out of the cave floor.",
			Pad = Vector2.new(-22, -43),
			PriceSeconds = 108,
			Pieces = build(function(add)
				local spikes = {
					{ -22, -49, 4.6, 17, 10 },
					{ -27, -47, 3.8, 12, -20 },
					{ -18, -46, 3.4, 9, 35 },
					{ -30, -51, 3, 7, 0 },
					{ -15, -50, 2.6, 6, 25 },
				}
				for _, s in spikes do
					local x, z, w, h, r = s[1], s[2], s[3], s[4], s[5]
					add(B(x, h * 0.3, z, w, h * 0.6, w, ROCK, Basalt, Ry(r)))
					add(B(x, h * 0.6 + h * 0.2, z, w * 0.55, h * 0.5, w * 0.55, DROCK, Basalt, Ry(r + 15)))
				end
				add(Ball(-20, 1.6, -49, 9, 3.2, 8, DROCK, Basalt))
				add(Ball(-28, 1.2, -44, 6, 2.4, 6, ROCK, Basalt))
			end),
		},
		-- 7
		{
			Id = "Ribs",
			Yaw = -20,
			Name = "Dragon Ribs",
			Description = "The huge rib cage and skull of an ancient dragon lying in the dust.",
			Pad = Vector2.new(60, 19),
			PriceSeconds = 124,
			Pieces = build(function(add)
				add(B(64, 1.4, 10, 19, 1.2, 1.5, BONE, Slate))
				local heights = { 10.4, 10, 9.2, 8, 6.4 }
				for i = 1, 5 do
					local x = 57.5 + 3.4 * (i - 1)
					add(B(x, heights[i] / 2 + 0.4, 6.4, 0.9, heights[i], 0.9, BONE, Slate, Vector3.new(20, 0, 0)))
					add(B(x, heights[i] / 2 + 0.4, 13.6, 0.9, heights[i], 0.9, BONE, Slate, Vector3.new(-20, 0, 0)))
				end
				add(Ball(54.6, 2.3, 10, 4.4, 3.4, 3.2, BONE, Slate))
			end),
		},
		-- 8
		{
			Id = "LavaPool",
			Yaw = 10,
			Name = "Lava Pool",
			Description = "A bubbling pool of lava ringed by dark rocks.",
			Pad = Vector2.new(24, -13),
			PriceSeconds = 143,
			Pieces = build(function(add)
				add(B(24, 0.25, -24, 16, 0.5, 12, LAVA, Plastic))
				for k = 0, 9 do
					local a = math.rad(k * 36)
					local x, z = 24 + 9.5 * math.cos(a), -24 + 7.4 * math.sin(a)
					add(B(x, 1.3, z, 4, 2 + (k % 3) * 0.8, 3.4, ROCK, Basalt, Ry(-math.deg(a))))
				end
				add(Ball(23, 0.9, -24, 2.4, 1.2, 2.4, EMBER, Plastic))
				add(Ball(27, 0.8, -22.5, 1.8, 1, 1.8, EMBER, Plastic))
			end),
		},
		-- 9
		{
			Id = "SkullGate",
			Yaw = -71,
			Name = "Skull Gate",
			Description = "A gate of giant bones with skulls arching over the walkway.",
			Pad = Vector2.new(8, 28.8),
			PriceSeconds = 164,
			Pieces = build(function(add)
				add(Cy(-4, 4.5, 28.8, 3.4, 9, BONE, Slate))
				add(Cy(20, 4.5, 28.8, 3.4, 9, BONE, Slate))
				add(B(-4, 0.7, 28.8, 5.6, 1.4, 5.6, ROCK, Basalt, Ry(10)))
				add(B(20, 0.7, 28.8, 5.6, 1.4, 5.6, ROCK, Basalt, Ry(-12)))
				add(B(8, 9.9, 28.8, 28, 2.4, 3, BONE, Slate))
				add(Ball(8, 12.8, 28.8, 4.6, 4.6, 4, BONE, Slate))
				add(Ball(-1.5, 11.9, 28.8, 3, 2.6, 3, BONE, Slate))
				add(Ball(17.5, 11.9, 28.8, 3, 2.6, 3, BONE, Slate))
				add(B(3, 13.4, 28.8, 0.9, 4, 0.9, BONE, Slate, Vector3.new(0, 0, 25)))
				add(B(13, 13.4, 28.8, 0.9, 4, 0.9, BONE, Slate, Vector3.new(0, 0, -25)))
				add(Ball(3, 8, 28.8, 1.4, 1.8, 1.4, EMBER, Plastic))
				add(Ball(13, 8, 28.8, 1.4, 1.8, 1.4, EMBER, Plastic))
			end),
		},
		-- 10
		{
			Id = "Crystals",
			Yaw = -20,
			Name = "Emerald Crystals",
			Description = "A cluster of tall green crystals with one ruby among them.",
			Pad = Vector2.new(-66, 41),
			PriceSeconds = 189,
			Pieces = build(function(add)
				add(Ball(-66, 1.6, 50, 14, 3.4, 10, DROCK, Basalt))
				add(B(-66, 8, 50, 3.6, 14, 3.6, EMER, Glass, Vector3.new(4, 0, -6)))
				add(B(-70, 5.5, 51, 2.8, 9.4, 2.8, EMER, Glass, Vector3.new(-6, 20, 10)))
				add(B(-62, 5, 48.5, 3, 8.6, 3, EMER, Glass, Vector3.new(8, 35, -8)))
				add(B(-68, 3.4, 46.5, 2.2, 5.6, 2.2, EMER, Glass, Vector3.new(-10, 10, 14)))
				add(B(-63, 3.2, 53, 2, 5, 2, EMER, Glass, Vector3.new(6, 0, -18)))
				add(B(-72, 2.6, 47, 1.8, 4, 1.8, EMER, Glass, Vector3.new(-8, 40, 12)))
				add(B(-59, 2.2, 51, 1.6, 3.4, 1.6, EMER, Glass, Vector3.new(10, 15, -20)))
				add(B(-65.5, 2.4, 53.5, 1.6, 3.8, 1.6, RUBY, Glass, Vector3.new(-4, 0, 16)))
			end),
		},
		-- 11
		{
			Id = "Armory",
			Yaw = 16,
			Name = "Knight Armor Graveyard",
			Description = "Dented armor of brave knights left standing and lying around, with a broken shield and spear.",
			Pad = Vector2.new(-62, 28),
			PriceSeconds = 217,
			Pieces = build(function(add)
				local stands = { { -75, 25, -15 }, { -71, 30, 10 } }
				for _, s in stands do
					local x, z, r = s[1], s[2], s[3]
					add(Cy(x, 3, z, 0.6, 6, DIRON, Metal))
					add(B(x, 4.4, z, 2.6, 3, 1.6, IRON, Metal, Ry(r)))
					add(B(x, 5.9, z, 3.8, 0.9, 1.4, IRON, Metal, Ry(r)))
					add(Ball(x, 7.4, z, 1.9, 2.1, 1.9, IRON, Metal))
				end
				add(B(-67, 1.3, 25.5, 2.6, 3, 1.6, IRON, Metal, Vector3.new(0, 20, 85)))
				add(Ball(-64.4, 1, 26.5, 1.9, 2.1, 1.9, IRON, Metal))
				add(Cy(-72, 0.5, 26.4, 3.6, 0.4, DGOLD, Metal))
				add(Cy(-72.5, 4, 32.5, 0.4, 8, WOOD, Wood, 8, 10))
				add(B(-68.5, 0.6, 29.5, 4, 1.2, 3, DIRON, Metal, Ry(35)))
			end),
		},
		-- 12
		{
			Id = "Chests",
			Yaw = -12,
			Name = "Treasure Chests",
			Description = "Three chests of different sizes with gold spilling out of them.",
			Pad = Vector2.new(-44, 21),
			PriceSeconds = 250,
			Pieces = build(function(add)
				local cs = { { -46, 26.5, 5, 3.2, 20 }, { -41.5, 30, 3.8, 2.6, -30 }, { -42.5, 24.8, 3, 2.2, 12 } }
				for _, c in cs do
					local x, z, w, h, r = c[1], c[2], c[3], c[4], c[5]
					add(B(x, h / 2, z, w, h, w * 0.7, WOOD, Wood, Ry(r)))
					add(B(x, h + 0.4, z, w, 0.8, w * 0.7, DWOOD, Wood, Ry(r)))
					add(B(x, h / 2, z, 0.8, h + 0.2, w * 0.72, GOLD, Metal, Ry(r)))
				end
				add(Ball(-44.5, 0.9, 29.5, 3, 1.8, 3, GOLD, Metal))
				add(Ball(-48.5, 0.8, 24.5, 2.6, 1.6, 2.6, GOLD, Metal))
				add(Cy(-39.5, 0.3, 27, 1.4, 0.5, GOLD, Metal))
				add(Cy(-40, 0.3, 33, 1.4, 0.5, GOLD, Metal))
			end),
		},
		-- 13
		{
			Id = "Swords",
			Yaw = 12,
			Name = "Swords in the Rubble",
			Description = "Six swords of fallen heroes stuck in a heap of rubble at different angles.",
			Pad = Vector2.new(26, 43.5),
			PriceSeconds = 287,
			Pieces = build(function(add)
				add(B(26, 0.5, 49, 12, 1, 6, ROCK, Basalt))
				add(Ball(25, 1, 48, 5, 2, 4, DROCK, Basalt))
				local sw = {
					{ 22, 47.5, 9, 5, -8 },
					{ 25, 51, 7.4, -6, 6 },
					{ 29, 47, 10, 4, 10 },
					{ 27, 53, 6, -8, -5 },
					{ 20, 51.5, 6.6, 7, 4 },
					{ 31, 51, 8, -4, -12 },
				}
				for _, s in sw do
					local x, z, h, tx, tz = s[1], s[2], s[3], s[4], s[5]
					add(B(x, h / 2 + 0.6, z, 0.7, h, 0.25, IRON, Metal, Vector3.new(tx, 0, tz)))
					add(B(x, h * 0.45 + 0.9, z, 3, 0.5, 0.7, DGOLD, Metal, Vector3.new(tx, 0, tz)))
				end
			end),
		},
		-- 14
		{
			Id = "Forge",
			Yaw = 9,
			Name = "Dragonsmith Forge",
			Description = "A stone smithy with a glowing furnace, a tall chimney, an anvil and a barrel of coal.",
			Pad = Vector2.new(40, 38),
			PriceSeconds = 330,
			Pieces = build(function(add)
				add(B(46, 4.5, 48, 14, 9, 10, STONE, Granite))
				add(B(46, 9.6, 48, 16.4, 1.2, 12, DIRON, Metal))
				add(B(51.5, 12, 50.5, 3, 16, 3, ROCK, Basalt))
				add(B(46, 2.6, 42.9, 5, 4.2, 0.6, LAVA, Plastic))
				add(B(41, 3, 42.9, 3, 6, 0.6, DWOOD, Wood))
				add(B(36.5, 0.9, 43.5, 2.6, 1.8, 2.4, DWOOD, Wood))
				add(B(36.5, 2.2, 43.5, 3.8, 0.9, 1.8, DIRON, Metal))
				add(Ball(55, 1, 45, 3.6, 2, 3.6, DIRON, Basalt))
				add(Cy(54.8, 1.6, 50.5, 2.4, 3.2, WOOD, Wood))
				add(B(51, 0.8, 43.4, 3.4, 1.6, 2, DWOOD, Wood, Ry(15)))
				add(B(39, 0.7, 53.5, 2.6, 1.4, 2.6, IRON, Metal, Ry(-20)))
			end),
		},
		-- 15
		{
			Id = "Banners",
			Yaw = -16,
			Name = "Dragon Banners",
			Description = "Four tall poles with red and green dragon banners flapping in the heat.",
			Pad = Vector2.new(28, 32),
			PriceSeconds = 380,
			Pieces = build(function(add)
				local ps = { { 22, 37, 12, 0 }, { 26, 40, 14, 1 }, { 30, 37, 10, 0 }, { 33, 40.5, 13, 1 } }
				for _, p in ps do
					local x, z, h, c = p[1], p[2], p[3], p[4]
					add(Cy(x, h / 2, z, 0.7, h, WOOD, Wood))
					add(B(x + 1.9, h - 2.8, z, 3.4, 5, 0.25, if c == 1 then SCALE else CLOTH, Fabric))
					add(Ball(x, h + 0.6, z, 1.2, 1.2, 1.2, GOLD, Metal))
				end
				add(Ball(24, 0.8, 38.5, 3.4, 1.6, 3, ROCK, Basalt))
				add(Ball(31.5, 0.7, 39, 3, 1.4, 2.6, DROCK, Basalt))
			end),
		},
		-- 16
		{
			Id = "Tower",
			Yaw = 8,
			Name = "Ruined Watchtower",
			Description = "A crumbling stone watchtower with a broken top, a tattered banner and a glowing window.",
			Pad = Vector2.new(62, -5),
			PriceSeconds = 437,
			Pieces = build(function(add)
				add(B(68, 4, -14, 11, 8, 11, ROCK, Cobble))
				add(B(68, 14, -14, 9, 12, 9, DROCK, Cobble))
				add(B(68, 21.6, -14, 11.4, 3.2, 11.4, ROCK, Granite))
				add(B(64, 24.4, -18, 2.6, 2.4, 2.6, ROCK, Granite))
				add(B(72, 24.4, -18, 2.6, 2.4, 2.6, ROCK, Granite))
				add(B(72, 24.4, -10, 2.6, 2.4, 2.6, ROCK, Granite))
				add(B(68, 13, -8.4, 1.8, 3.4, 0.5, LAVA, Plastic))
				add(B(68, 3, -8.4, 2.6, 5, 0.5, DWOOD, Wood))
				add(B(72.2, 1.6, -8, 4, 3.2, 3.4, ROCK, Basalt, Ry(30)))
				add(B(63.5, 1.2, -9, 3, 2.4, 3, DROCK, Basalt, Ry(-20)))
				add(B(72.7, 16, -11.5, 0.3, 5, 2.4, CLOTH, Fabric))
			end),
		},
		-- 17
		{
			Id = "Baby",
			Yaw = -18,
			Name = "Baby Dragon",
			Description = "A little green dragon with tiny wings and horns napping on a rock.",
			Pad = Vector2.new(-34, 44),
			PriceSeconds = 502,
			Pieces = build(function(add)
				add(B(-36, 0.8, 51, 10, 1.6, 8, ROCK, Basalt))
				add(Ball(-36, 4, 51, 6.4, 4.8, 4.6, SCALE, Plastic))
				add(Ball(-32.4, 5.8, 51, 3.8, 3.4, 3.4, SCALE, Plastic))
				add(B(-30.3, 5.2, 51, 2, 1.4, 2, SCALE, Plastic))
				add(B(-32.6, 7.6, 50, 0.6, 1.6, 0.6, BONE, Slate))
				add(B(-32.6, 7.6, 52, 0.6, 1.6, 0.6, BONE, Slate))
				add(B(-36.5, 6.4, 48, 4.6, 0.4, 3.4, DSCALE, Plastic, Vector3.new(0, 10, -25)))
				add(B(-36.5, 6.4, 54, 4.6, 0.4, 3.4, DSCALE, Plastic, Vector3.new(0, -10, 25)))
				add(B(-39.8, 3.2, 51.5, 3.2, 1.8, 1.8, SCALE, Plastic))
				add(B(-42, 2.4, 52.4, 2.6, 1.3, 1.3, SCALE, Plastic))
				add(B(-43.8, 1.9, 53, 2, 0.9, 0.9, DSCALE, Plastic))
				add(B(-34.4, 1.6, 49.6, 1.2, 2.6, 1.2, DSCALE, Plastic))
				add(B(-34.4, 1.6, 52.4, 1.2, 2.6, 1.2, DSCALE, Plastic))
			end),
		},
		-- 18
		{
			Id = "Throne",
			Yaw = 12,
			Name = "Bone Throne",
			Description = "A throne of dragon bones on a stone dais with skulls on the armrests and a golden crown.",
			Pad = Vector2.new(-4, 17),
			RewardMult = 1.25,
			PriceSeconds = 576,
			Pieces = build(function(add)
				add(B(-6, 0.7, 8, 10, 1.4, 9, ROCK, Granite))
				add(B(-6, 0.35, 13, 7, 0.7, 2.4, DROCK, Granite))
				add(B(-6, 2.9, 8, 5, 3, 4.6, BONE, Slate))
				add(B(-6, 7.6, 5.8, 5.6, 8, 1.4, BONE, Slate))
				add(B(-8.3, 12.4, 5.8, 0.9, 3.4, 0.9, BONE, Slate, Vector3.new(0, 0, 12)))
				add(B(-3.7, 12.4, 5.8, 0.9, 3.4, 0.9, BONE, Slate, Vector3.new(0, 0, -12)))
				add(B(-8.9, 4.6, 8, 1.4, 2.4, 4, BONE, Slate))
				add(B(-3.1, 4.6, 8, 1.4, 2.4, 4, BONE, Slate))
				add(Ball(-8.9, 6.2, 6.6, 2, 1.8, 2, BONE, Slate))
				add(Ball(-3.1, 6.2, 6.6, 2, 1.8, 2, BONE, Slate))
				add(B(-6, 4.7, 8.2, 4, 0.8, 3.6, CLOTH, Fabric))
				add(B(-6, 12.1, 5.8, 2.4, 1, 1, GOLD, Metal))
				add(Ball(-6, 9, 5.1, 1.6, 1.6, 1.2, RUBY, Glass))
			end),
		},
		-- 19
		{
			Id = "Coins",
			Yaw = -10,
			Name = "Coin Towers",
			Description = "Four towers of stacked gold coins with a ruby on top and loose coins around.",
			Pad = Vector2.new(55, -18),
			PriceSeconds = 664,
			Pieces = build(function(add)
				local st = { { 44, -26, 9 }, { 48, -23, 6 }, { 40, -23.5, 4.6 }, { 47, -30, 7.4 } }
				for _, s in st do
					add(Cy(s[1], s[3] / 2, s[2], 4.4, s[3], GOLD, Metal))
					add(Cy(s[1], s[3] * 0.5, s[2], 4.7, 0.8, DGOLD, Metal))
				end
				add(Cy(52, 0.3, -26, 3.6, 0.5, GOLD, Metal))
				add(Cy(51, 0.3, -21.5, 3, 0.5, DGOLD, Metal))
				add(Cy(40.5, 2, -28, 3.4, 0.5, GOLD, Metal, 0, 60))
				add(Ball(44, 9.8, -26, 1.6, 1.6, 1.6, RUBY, Glass))
			end),
		},
		-- 20
		{
			Id = "Runes",
			Yaw = 14,
			Name = "Rune Circle",
			Description = "A ring of tilted standing stones around a glowing purple rune stone.",
			Pad = Vector2.new(-22, -15),
			PriceSeconds = 764,
			Pieces = build(function(add)
				add(B(-22, 0.2, -24, 14, 0.4, 14, DROCK, Granite))
				add(B(-22, 0.3, -24, 9, 0.4, 9, PURPLE, Plastic))
				local hs = { 7, 5.4, 6.4, 8, 5, 6, 7.4 }
				for k = 0, 6 do
					local a = math.rad(k * 51.4 + 8)
					local x, z = -22 + 6.2 * math.cos(a), -24 + 6.2 * math.sin(a)
					add(
						B(
							x,
							hs[k + 1] / 2,
							z,
							1.8,
							hs[k + 1],
							1,
							ROCK,
							Granite,
							Vector3.new(if k % 2 == 0 then 5 else -5, -math.deg(a), if k % 3 == 0 then 6 else -4)
						)
					)
				end
				add(Ball(-22, 2, -24, 2.6, 2.6, 2.6, PURPLE, Glass))
			end),
		},
		-- 21
		{
			Id = "Wings",
			Yaw = 12,
			Name = "Wing Arches",
			Description = "Two giant dragon wings of bone and green membrane rising from the rocks.",
			Pad = Vector2.new(66, 38),
			PriceSeconds = 878,
			Pieces = build(function(add)
				for _, s in { -1, 1 } do
					add(B(66 + s * 5.5, 11, 46, 1.4, 22, 1.4, BONE, Slate, Vector3.new(0, 0, -s * 10)))
					add(B(66 + s * 8.4, 7.5, 46, 1, 15, 1, BONE, Slate, Vector3.new(0, 0, -s * 22)))
					add(B(66 + s * 10, 4.6, 46, 0.9, 9.5, 0.9, BONE, Slate, Vector3.new(0, 0, -s * 38)))
					add(B(66 + s * 7.7, 7, 46, 4.2, 13, 0.3, SCALE, Plastic, Vector3.new(0, 0, -s * 16)))
					add(B(66 + s * 9.8, 3.6, 46, 3, 7, 0.3, DSCALE, Plastic, Vector3.new(0, 0, -s * 30)))
					add(B(66 + s * 6, 0.9, 46, 8, 1.8, 6, ROCK, Basalt, Ry(s * 12)))
				end
			end),
		},
		-- 22
		{
			Id = "Skull",
			Yaw = -14,
			Name = "Giant Dragon Skull",
			Description = "A huge dragon skull with horns and fangs that stares toward the road.",
			Pad = Vector2.new(-28, 30),
			RewardMult = 1.3,
			PriceSeconds = 1010,
			Pieces = build(function(add)
				add(B(-24, 0.8, 20, 16, 1.6, 12, ROCK, Basalt))
				add(Ball(-24, 6, 16, 10, 9, 9, BONE, Slate))
				add(B(-24, 4.2, 23.5, 5.6, 3.6, 7, BONE, Slate))
				add(B(-24, 1.9, 24, 4.8, 1.6, 6.4, BONE, Slate))
				add(B(-26.6, 7, 20, 2.2, 2.4, 1.4, OBS, Slate))
				add(B(-21.4, 7, 20, 2.2, 2.4, 1.4, OBS, Slate))
				add(Ball(-26.6, 7, 20.4, 1.2, 1.2, 1.2, LAVA, Plastic))
				add(Ball(-21.4, 7, 20.4, 1.2, 1.2, 1.2, LAVA, Plastic))
				add(B(-29.6, 10.4, 16, 1, 6, 1, BONE, Slate, Vector3.new(0, 0, 40)))
				add(B(-18.4, 10.4, 16, 1, 6, 1, BONE, Slate, Vector3.new(0, 0, -40)))
				add(B(-25.4, 2.8, 27.2, 0.6, 1.4, 0.6, BONE, Slate))
				add(B(-22.6, 2.8, 27.2, 0.6, 1.4, 0.6, BONE, Slate))
				add(B(-24, 4.7, 27.2, 1.6, 0.8, 0.6, OBS, Slate))
			end),
		},
		-- 23
		{
			Id = "Spires",
			Yaw = 20,
			Name = "Obsidian Spires",
			Description = "Tall black glass spires of different heights growing out of a rocky mound.",
			Pad = Vector2.new(-68, -36),
			PriceSeconds = 1161,
			Pieces = build(function(add)
				add(Ball(-70, 1.6, -47, 16, 3.2, 12, DROCK, Basalt))
				local sp = {
					{ -70, -46, 6, 28, 10 },
					{ -65.5, -51, 4.4, 20, -15 },
					{ -74, -52, 4, 16, 30 },
					{ -64, -43, 3.6, 13, 0 },
					{ -73, -41, 3.4, 10, 20 },
				}
				for _, s in sp do
					local x, z, w, h, r = s[1], s[2], s[3], s[4], s[5]
					add(B(x, h * 0.31, z, w, h * 0.62, w, OBS, Slate, Ry(r)))
					add(B(x, h * 0.62 + h * 0.19, z, w * 0.55, h * 0.5, w * 0.55, DROCK, Slate, Ry(r + 20)))
				end
			end),
		},
		-- 24
		{
			Id = "Keep",
			Yaw = -6,
			Name = "Dragon Keep",
			Description = "A dark stone castle with four round towers, green scale roofs, a dragon head over the gate and a lava window.",
			Pad = Vector2.new(-48, -32),
			RewardMult = 1.3,
			PriceSeconds = 1335,
			Pieces = build(function(add)
				add(B(-48, 9, -47, 22, 18, 12, DROCK, Granite))
				add(B(-48, 25, -47, 12, 14, 9, ROCK, Granite))
				add(B(-48, 33.2, -47, 14, 2.4, 11, DSCALE, Plastic))
				add(B(-48, 35.4, -47, 9, 2.2, 7, SCALE, Plastic))
				add(B(-48, 37.4, -47, 4, 2, 3.4, DSCALE, Plastic))
				for _, t in { { -58.5, -52.5 }, { -37.5, -52.5 }, { -58.5, -41.5 }, { -37.5, -41.5 } } do
					add(Cy(t[1], 11, t[2], 6, 22, ROCK, Granite))
					add(Cy(t[1], 23.4, t[2], 7, 2.4, DSCALE, Plastic))
				end
				add(B(-48, 3.6, -40.6, 5, 7.2, 0.8, DWOOD, Wood))
				add(Ball(-48, 11.8, -40.2, 4.4, 3.6, 3.2, SCALE, Plastic))
				add(B(-48, 22, -42.4, 2, 3.4, 0.6, LAVA, Plastic))
			end),
		},
		-- 25
		{
			Id = "Catapult",
			Yaw = -16,
			Name = "Siege Catapult",
			Description = "A wooden catapult with a stone counterweight, its last boulder still in the bucket.",
			Pad = Vector2.new(58, 34),
			PriceSeconds = 1535,
			Pieces = build(function(add)
				add(B(64, 1.2, 28, 10, 1.2, 5.6, WOOD, Wood))
				add(Cz(60.2, 1.8, 24.9, 3.6, 0.8, DWOOD, Wood))
				add(Cz(60.2, 1.8, 31.1, 3.6, 0.8, DWOOD, Wood))
				add(Cz(67.8, 1.8, 24.9, 3.6, 0.8, DWOOD, Wood))
				add(Cz(67.8, 1.8, 31.1, 3.6, 0.8, DWOOD, Wood))
				add(B(63, 4.4, 25.6, 0.9, 5.2, 0.9, DWOOD, Wood))
				add(B(63, 4.4, 30.4, 0.9, 5.2, 0.9, DWOOD, Wood))
				add(B(63, 6.9, 28, 0.8, 0.8, 5.6, DWOOD, Wood))
				add(B(64.6, 7.6, 28, 11, 0.9, 1, WOOD, Wood, Vector3.new(0, 0, -28)))
				add(B(69.2, 10.2, 28, 2.6, 1.6, 2.8, DWOOD, Wood))
				add(B(59, 4.4, 28, 2.6, 2.6, 3, ROCK, Granite))
				add(Ball(69.8, 11.6, 28, 2.4, 2.4, 2.4, ROCK, Granite))
			end),
		},
		-- 26
		{
			Id = "Statue",
			Yaw = 14,
			Name = "Slayer Statue",
			Description = "A mossy stone statue of a dragon slayer holding up his sword on a pedestal.",
			Pad = Vector2.new(-12, -39),
			PriceSeconds = 1765,
			Pieces = build(function(add)
				add(B(-12, 1.2, -47, 7, 2.4, 7, STONE, Granite))
				add(B(-13, 4.4, -47, 1.6, 4, 1.6, STONE, Granite))
				add(B(-11, 4.4, -47, 1.6, 4, 1.6, STONE, Granite))
				add(B(-12, 9, -47, 4, 4.8, 2.4, STONE, Granite))
				add(Ball(-12, 12.5, -47, 2.6, 2.8, 2.6, STONE, Granite))
				add(B(-9.6, 10.6, -47, 1.2, 4, 1.2, STONE, Granite, Vector3.new(0, 0, -20)))
				add(B(-14.6, 8.6, -47, 1.2, 3.8, 1.2, STONE, Granite))
				add(B(-8.4, 14.6, -47, 0.6, 4.4, 0.3, IRON, Metal))
				add(B(-15.3, 8.6, -46.2, 0.8, 3.6, 2.8, STONE, Granite))
				add(B(-12, 2.6, -45, 5, 0.4, 3, DSCALE, Fabric))
				add(Ball(-17, 0.9, -49, 3.4, 1.8, 3.2, DROCK, Basalt))
				add(Ball(-7, 0.8, -49.5, 2.6, 1.6, 2.4, ROCK, Basalt))
			end),
		},
		-- 27
		{
			Id = "Volcano",
			Name = "Smoking Volcano",
			Description = "A small volcano of stacked rock with a lava crater, two lava streams and flying embers.",
			Pad = Vector2.new(60, -25),
			RewardMult = 1.4,
			PriceSeconds = 2030,
			Pieces = build(function(add)
				add(Cy(60, 4.5, -42, 28, 9, DROCK, Basalt))
				add(Cy(60, 12.5, -42, 21, 8, ROCK, Basalt))
				add(Cy(60, 19.5, -42, 15, 6, DROCK, Basalt))
				add(Cy(60, 24, -42, 10, 3, OBS, Slate))
				add(Cy(60, 25.8, -42, 6.8, 0.8, LAVA, Plastic))
				add(B(56, 14, -31.4, 2.4, 16, 0.8, LAVA, Plastic))
				add(B(64.5, 9, -29.5, 2, 12, 0.8, LAVA, Plastic))
				add(Ball(60, 29, -42, 3, 3, 3, EMBER, Plastic))
				add(Ball(62.5, 32, -43, 2, 2, 2, EMBER, Plastic))
				add(Ball(49, 2, -33, 8, 4, 6, DROCK, Basalt))
				add(Ball(71, 2, -34, 7, 3.6, 6, ROCK, Basalt))
			end),
		},
		-- 28
		{
			Id = "Wagon",
			Yaw = 20,
			Name = "Loot Wagon",
			Description = "A wooden wagon heaped with gold that a brave thief never got away with.",
			Pad = Vector2.new(36, -5),
			PriceSeconds = 2334,
			Pieces = build(function(add)
				add(B(40, 2.6, -14, 10, 1, 5.4, WOOD, Wood))
				add(B(40, 3.9, -16.6, 10, 1.6, 0.5, DWOOD, Wood))
				add(B(40, 3.9, -11.4, 10, 1.6, 0.5, DWOOD, Wood))
				add(B(35.2, 3.9, -14, 0.5, 1.6, 5.4, DWOOD, Wood))
				add(B(44.8, 3.9, -14, 0.5, 1.6, 5.4, DWOOD, Wood))
				add(Cz(36.5, 2, -17.4, 4, 0.7, DWOOD, Wood))
				add(Cz(36.5, 2, -10.6, 4, 0.7, DWOOD, Wood))
				add(Cz(43.5, 2, -17.4, 4, 0.7, DWOOD, Wood))
				add(Cz(43.5, 2, -10.6, 4, 0.7, DWOOD, Wood))
				add(Ball(40, 5.4, -14, 8, 3.6, 4.8, GOLD, Metal))
				add(B(47.5, 2, -14, 5, 0.6, 0.6, WOOD, Wood))
				add(Ball(40, 7.3, -14, 1.6, 1.6, 1.6, RUBY, Glass))
			end),
		},
		-- 29
		{
			Id = "Mushrooms",
			Yaw = -15,
			Name = "Cave Mushrooms",
			Description = "Tall cave mushrooms with teal and purple caps growing around a mossy rock.",
			Pad = Vector2.new(-37, -14),
			PriceSeconds = 2684,
			Pieces = build(function(add)
				add(Ball(-37, 0.8, -21.5, 5, 1.6, 4, DROCK, Basalt))
				local ms = {
					{ -37, -23, 8, 5.2 },
					{ -41, -20, 5.4, 3.6 },
					{ -33, -19.5, 4.4, 3 },
					{ -40, -26, 3.2, 2.4 },
					{ -34, -26, 6.2, 4 },
					{ -43, -23.5, 2.4, 1.8 },
				}
				for i, m in ms do
					add(Cy(m[1], m[3] / 2, m[2], 1.3, m[3], CREAM, Plastic))
					add(
						Ball(
							m[1],
							m[3] + 0.2,
							m[2],
							m[4],
							m[4] * 0.6,
							m[4],
							if i % 3 == 0 then PURPLE else EMER,
							Plastic
						)
					)
				end
			end),
		},
		-- 30
		{
			Id = "GreatDragon",
			Yaw = -8,
			Name = "The Great Dragon",
			Description = "The landmark: a giant green dragon with spread wings perched on top of the cave, breathing fire at the sky.",
			Pad = Vector2.new(-50, 9),
			RewardMult = 2,
			PriceSeconds = 3087,
			Pieces = build(function(add)
				add(Ball(-66, 37, -10, 18, 8, 8, SCALE, Plastic))
				add(Ball(-59, 38.5, -10, 8, 9, 7.2, SCALE, Plastic))
				add(B(-55.5, 46, -10, 3.4, 10, 3.4, SCALE, Plastic, Vector3.new(0, 0, -35)))
				add(Ball(-50, 50.5, -10, 6.4, 4.2, 4.2, SCALE, Plastic))
				add(B(-46.5, 49.8, -10, 4.6, 2.4, 3, SCALE, Plastic))
				add(B(-47, 47.8, -10, 4, 1, 2.6, DSCALE, Plastic))
				add(B(-52.5, 53.5, -11.6, 0.9, 4, 0.9, BONE, Slate, Vector3.new(0, 0, 35)))
				add(B(-52.5, 53.5, -8.4, 0.9, 4, 0.9, BONE, Slate, Vector3.new(0, 0, 35)))
				add(B(-66, 46, -3, 1.4, 1.4, 15, BONE, Slate, Vector3.new(-35, 0, 0)))
				add(B(-66, 46, -17, 1.4, 1.4, 15, BONE, Slate, Vector3.new(35, 0, 0)))
				add(B(-65, 44.6, -4.2, 8, 0.4, 11, DSCALE, Plastic, Vector3.new(-30, 0, 0)))
				add(B(-65, 44.6, -15.8, 8, 0.4, 11, DSCALE, Plastic, Vector3.new(30, 0, 0)))
				add(B(-75, 34.6, -10, 6, 2, 2, SCALE, Plastic))
				add(B(-64, 33.6, -13, 3, 3, 2, DSCALE, Plastic))
				add(B(-64, 33.6, -7, 3, 3, 2, DSCALE, Plastic))
				add(Ball(-41, 49.4, -10, 5, 2.4, 2.4, LAVA, Plastic))
			end),
		},
	},
}

return theme
