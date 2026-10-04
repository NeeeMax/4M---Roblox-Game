--!strict
-- Theme of the Shiba of bay 29: Clock Tower (Config/DecorTypes -> Theme). 160 x 115: the Eternal Shiba, a cosmic time god, stands on a
-- celestial dais with a gold zodiac ring. A winding walkway of star-white stone passes a clockwork garden (hour stones, cogs, sand
-- timers, grandfather clocks, a pendulum, an astrolabe), a cog gate and an eternal throne, and the giant Clock Tower rises in the back
-- left: base, shaft, big clock face with hands, a ring of floating gears and, above everything, a floating hourglass.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: faces, stars and sand are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local NAVY = C(26, 30, 74)
local MIDNIGHT = C(42, 48, 110)
local INDIGO = C(66, 72, 148)
local VIOLET = C(120, 92, 196)
local STARW = C(248, 248, 255)
local PEARL = C(228, 230, 246)
local GOLD = C(246, 200, 72)
local BRASS = C(204, 152, 62)
local DBRASS = C(150, 106, 44)
local COPPER = C(198, 112, 72)
local STONE = C(186, 188, 204)
local DSTONE = C(120, 124, 150)
local GLASS = C(176, 212, 250)
local SAND = C(255, 228, 150)
local CYAN = C(110, 206, 238)
local WOOD = C(130, 84, 56)
local DARK = C(36, 38, 62)

local Concrete = Enum.Material.Concrete
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Marble = Enum.Material.Marble
local Wood = Enum.Material.Wood
local Glass = Enum.Material.Glass
local Granite = Enum.Material.Granite

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

-- Disc facing sideways (axis along X): diameter d, thickness len.
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

-- Wedge: vertical back on the +Z side, sloping down toward -Z.
local function W(
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
		Shape = Enum.PartType.Wedge,
	}
end

-- Hour stone of the stone circle: a slab at clock position `hour` (12 = far side) around (cx, cz), turned to face the centre.
local function hourStone(cx: number, cz: number, radius: number, hour: number, h: number): Piece
	local a = math.rad(90 - hour * 30) -- 12 o'clock = deeper into the plot (-Z)
	local x = cx + radius * math.cos(a)
	local z = cz - radius * math.sin(a)
	local deg = math.deg(a)
	return B(x, h / 2, z, 2.2, h, 1.2, STONE, Marble, 0, -(deg + 90), 0)
end

-- Rune pillar of the rune circle at angle `deg`.
local function runePillar(cx: number, cz: number, radius: number, deg: number): { Piece }
	local a = math.rad(deg)
	local x = cx + radius * math.cos(a)
	local z = cz + radius * math.sin(a)
	return {
		B(x, 3, z, 1.8, 6, 1.8, DSTONE, Granite),
		B(x, 6.5, z, 2.4, 1, 2.4, GOLD, Metal),
	}
end

local function lamp(x: number, z: number): { Piece }
	return {
		Cy(x, 0.5, z, 2.4, 1, DBRASS, Metal),
		Cy(x, 5.5, z, 0.7, 9, GOLD, Metal),
		Ball(x, 10.9, z, 3, 3, 3, STARW, Plastic),
		Cy(x, 12.8, z, 0.7, 0.8, GOLD, Metal),
	}
end

local function bench(x: number, z: number): { Piece }
	return {
		B(x, 1.6, z, 7, 0.6, 2.4, STONE, Marble),
		B(x - 3, 0.65, z, 0.7, 1.3, 2, GOLD, Metal),
		B(x + 3, 0.65, z, 0.7, 1.3, 2, GOLD, Metal),
		B(x, 3.1, z + 1.1, 7, 2.4, 0.5, MIDNIGHT, Plastic),
		Cz(x, 3.1, z + 1.5, 2.2, 0.3, GOLD, Metal),
	}
end

local function grandfather(x: number, z: number, h: number): { Piece }
	return {
		B(x, h / 2 - 0.5, z, 3.6, h - 1, 2.6, WOOD, Wood),
		B(x, h - 1.2, z, 4.6, 2.4, 3.2, GOLD, Metal),
		Cz(x, h - 1.2, z + 1.7, 2.6, 0.3, STARW, Plastic),
		B(x, h + 0.6, z, 3.6, 1.2, 2.6, DBRASS, Metal),
	}
end

local function banner(x: number, z: number): { Piece }
	return {
		Cy(x, 7.5, z, 0.7, 15, GOLD, Metal),
		B(x, 14.6, z, 0.6, 0.6, 5.2, GOLD, Metal),
		B(x + 0.2, 10, z, 0.3, 8, 4, MIDNIGHT, Plastic),
		Cx(x + 0.5, 10.6, z, 2.8, 0.3, GOLD, Metal),
	}
end

local function obelisk(x: number, z: number, h: number): { Piece }
	return {
		B(x, 0.6, z, 4.2, 1.2, 4.2, STONE, Marble),
		B(x, 0.6 + h / 2, z, 2.4, h, 2.4, DARK, Granite),
		B(x, h + 1.6, z, 1.6, 1.6, 1.6, GOLD, Metal, 0, 45, 0),
	}
end

local function hourglassSmall(x: number, z: number): { Piece }
	return {
		Cy(x, 1.2, z, 3.6, 2.4, STONE, Marble),
		Cy(x, 2.7, z, 3, 0.6, GOLD, Metal),
		Cy(x, 5.2, z, 2.2, 4.4, GLASS, Glass),
		Cy(x, 7.9, z, 3, 0.6, GOLD, Metal),
	}
end

local function concat(...: { Piece }): { Piece }
	local out: { Piece } = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

local theme: DecorTypes.Theme = {
	Key = "ClockTower",
	Name = "Clock Tower",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(-30, -6), Facing = 0 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(34, 44),
		Vector2.new(-12, 32),
		Vector2.new(-48, 20),
		Vector2.new(-16, -2),
		Vector2.new(22, -10),
		Vector2.new(52, -28),
		Vector2.new(20, -44),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(-24, 6),
	AutoPad = Vector2.new(-33, -19),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Chrono Plaza",
			Description = "Midnight flagstones with star-white inlays, a gold zodiac ring around the Eternal Shiba's dais and gold circles on the plazas.",
			Pad = Vector2.new(-6, 52),
			PriceSeconds = 62,
			Pieces = {
				B(0, 0.15, 0, 160, 0.3, 115, NAVY, Concrete),
				B(-30, 0.35, -6, 30, 0.2, 30, MIDNIGHT, Marble),
				B(-30, 0.45, -6, 22, 0.2, 22, GOLD, Metal),
				B(-30, 0.5, -6, 12, 0.1, 12, PEARL, Marble),
				B(-50, 0.25, -34, 34, 0.5, 34, MIDNIGHT, Marble),
				B(-50, 0.4, -34, 28, 0.2, 28, GOLD, Metal),
				B(14, 0.25, 16, 36, 0.5, 22, INDIGO, Concrete),
				B(48, 0.25, 12, 30, 0.5, 24, INDIGO, Concrete),
				B(-48, 0.25, 40, 36, 0.5, 26, INDIGO, Concrete),
				B(-18, 0.25, -36, 28, 0.5, 40, INDIGO, Concrete),
				B(66, 0.25, -38, 26, 0.5, 30, MIDNIGHT, Marble),
				B(62, 0.25, 38, 28, 0.5, 28, INDIGO, Concrete),
			},
		},
		-- 2
		{
			Id = "StarLamps",
			Name = "Star Lamps",
			Description = "Three tall gold lamp posts with star-white lanterns that light the walkway.",
			Pad = Vector2.new(-4, 41),
			PriceSeconds = 71,
			Pieces = concat(lamp(-6, 46), lamp(4, 24), lamp(46, 52)),
		},
		-- 3
		{
			Id = "TimeSign",
			Name = "Time Signpost",
			Description = "A midnight-blue signboard in a gold frame with a golden clock, on two brass posts.",
			Pad = Vector2.new(-19, 43),
			PriceSeconds = 82,
			Pieces = {
				B(-19, 0.5, 50, 14, 1, 4, STONE, Marble),
				Cy(-24, 5.5, 50, 0.9, 9, BRASS, Metal),
				Cy(-14, 5.5, 50, 0.9, 9, BRASS, Metal),
				B(-19, 8.4, 50, 13, 5.2, 0.8, MIDNIGHT, Plastic),
				B(-19, 8.4, 49.55, 14, 6, 0.5, GOLD, Metal),
				Cz(-19, 8.4, 50.6, 4.4, 0.4, STARW, Plastic),
				Ball(-24, 10.4, 50, 1.6, 1.6, 1.6, GOLD, Metal),
				Ball(-14, 10.4, 50, 1.6, 1.6, 1.6, GOLD, Metal),
			},
		},
		-- 4
		{
			Id = "CogGarden",
			Name = "Cog Garden",
			Description = "Brass and gold cogwheels of every size, half sunk into the plaza like a garden of turning flowers.",
			Pad = Vector2.new(-54, 40),
			PriceSeconds = 94,
			Pieces = {
				Cy(-66, 0.9, 50, 10, 1.8, BRASS, Metal),
				Cy(-66, 1.2, 50, 2.4, 2.4, GOLD, Metal),
				Cy(-58, 0.8, 47, 7, 1.6, DBRASS, Metal),
				Cy(-58, 1.1, 47, 1.8, 2.2, GOLD, Metal),
				Cy(-60, 0.7, 54, 6, 1.4, GOLD, Metal),
				Cy(-71, 0.8, 44, 7, 1.6, COPPER, Metal),
				Cy(-71, 1.1, 44, 1.8, 2.2, GOLD, Metal),
				Cy(-61.5, 0.6, 49.2, 3.4, 1.2, STONE, Metal),
			},
		},
		-- 5
		{
			Id = "SandBenches",
			Name = "Sandglass Benches",
			Description = "Two stone benches with gold legs and midnight backrests, each with a little clock.",
			Pad = Vector2.new(-40, 35),
			PriceSeconds = 108,
			Pieces = concat(bench(-42, 41), bench(-34, 45)),
		},
		-- 6
		{
			Id = "HourStones",
			Name = "Hour Stones",
			Description = "Twelve standing stones in a circle mark the hours around a gold sun slab.",
			Pad = Vector2.new(-45, 26),
			PriceSeconds = 125,
			Pieces = concat({ B(-64, 0.25, 30, 6, 0.5, 6, GOLD, Metal) }, {
				hourStone(-64, 30, 6.5, 1, 4.2),
				hourStone(-64, 30, 6.5, 2, 3.6),
				hourStone(-64, 30, 6.5, 3, 4.6),
				hourStone(-64, 30, 6.5, 4, 3.6),
				hourStone(-64, 30, 6.5, 5, 4.2),
				hourStone(-64, 30, 6.5, 6, 5.2),
				hourStone(-64, 30, 6.5, 7, 4.2),
				hourStone(-64, 30, 6.5, 8, 3.6),
				hourStone(-64, 30, 6.5, 9, 4.6),
				hourStone(-64, 30, 6.5, 10, 3.6),
				hourStone(-64, 30, 6.5, 11, 4.2),
				hourStone(-64, 30, 6.5, 12, 5.6),
			}, { B(-64, 1.2, 30, 0.9, 2.4, 0.9, STARW, Marble) }),
		},
		-- 7
		{
			Id = "SandTimers",
			Name = "Sand Timers",
			Description = "Three glass hourglasses with golden sand stand on stone pedestals.",
			Pad = Vector2.new(50, 28),
			PriceSeconds = 143,
			Pieces = concat(hourglassSmall(42, 38), hourglassSmall(50, 34), hourglassSmall(58, 40)),
		},
		-- 8
		{
			Id = "Pendulum",
			Name = "Pendulum Frame",
			Description = "A brass frame holds a long golden pendulum with a big round bob, always swinging in the mind's eye.",
			Pad = Vector2.new(14, 11),
			PriceSeconds = 165,
			Pieces = {
				B(14, 0.5, 20, 12, 1, 5, DSTONE, Granite),
				B(9.5, 6.5, 20, 1, 11, 1.2, BRASS, Metal),
				B(18.5, 6.5, 20, 1, 11, 1.2, BRASS, Metal),
				B(14, 12.4, 20, 11, 1, 1.6, GOLD, Metal),
				B(14, 7.2, 20, 0.4, 9.2, 0.4, GOLD, Metal),
				Cz(14, 2.4, 20, 4.4, 1, GOLD, Metal),
				Cz(14, 2.4, 20.6, 2.4, 0.4, STARW, Plastic),
				Ball(9.5, 13.2, 20, 1.6, 1.6, 1.6, GOLD, Metal),
				Ball(18.5, 13.2, 20, 1.6, 1.6, 1.6, GOLD, Metal),
			},
		},
		-- 9
		{
			Id = "Astrolabe",
			Name = "Astrolabe",
			Description = "Nested gold rings turn around a violet core on a brass column.",
			Pad = Vector2.new(28, 14),
			PriceSeconds = 190,
			Pieces = {
				Cy(36, 1.2, 22, 5.6, 2.4, STONE, Marble),
				Cy(36, 4.2, 22, 1.6, 3.6, BRASS, Metal),
				Cz(36, 9.6, 22, 10, 0.5, GOLD, Metal),
				Cz(36, 9.6, 22, 7.6, 0.3, PEARL, Plastic),
				Cx(36, 9.6, 22, 9, 0.5, BRASS, Metal),
				B(36, 9.6, 22, 11, 0.5, 0.5, GOLD, Metal, 0, 0, 40),
				Ball(36, 9.6, 22, 3.2, 3.2, 3.2, VIOLET, Plastic),
				Ball(36, 14.9, 22, 1.4, 1.4, 1.4, GOLD, Metal),
			},
		},
		-- 10
		{
			Id = "GrandfatherClocks",
			Name = "Grandfather Clocks",
			Description = "Three tall dark-wood grandfather clocks with gold heads and star-white faces.",
			Pad = Vector2.new(64, 22),
			PriceSeconds = 218,
			Pieces = concat(grandfather(58, 30, 12), grandfather(64, 30, 14), grandfather(70, 30, 12)),
		},
		-- 11
		{
			Id = "StarObelisks",
			Name = "Star Obelisks",
			Description = "Three dark obelisks with golden capstones that point at the stars.",
			Pad = Vector2.new(66, 40),
			PriceSeconds = 251,
			Pieces = concat(obelisk(68, 46, 15), obelisk(60, 52, 11), obelisk(74, 38, 11)),
		},
		-- 12
		{
			Id = "GearFountain",
			Name = "Gear Fountain",
			Description = "A two-tier stone fountain with a brass gear on top and two cogs turning at its sides.",
			Pad = Vector2.new(40, -6),
			PriceSeconds = 288,
			Pieces = {
				Cy(40, 1, 2, 14, 2, STONE, Marble),
				Cy(40, 1.9, 2, 12, 0.3, CYAN, Glass),
				Cy(40, 4.5, 2, 3, 5, BRASS, Metal),
				Cy(40, 7.4, 2, 9, 0.8, GOLD, Metal),
				Cy(40, 8.0, 2, 6, 0.4, CYAN, Glass),
				Cy(40, 9.6, 2, 1.4, 2.8, BRASS, Metal),
				Ball(40, 11.6, 2, 2.4, 2.4, 2.4, GOLD, Metal),
				Cz(46, 4, 2, 5, 0.8, BRASS, Metal),
				Cz(34, 4, 2, 5, 0.8, BRASS, Metal),
			},
		},
		-- 13
		{
			Id = "TimeBanners",
			Name = "Time Banners",
			Description = "Three gold poles carry midnight banners with a golden clock sign.",
			Pad = Vector2.new(-77, 24),
			PriceSeconds = 332,
			Pieces = concat(banner(-74, 20), banner(-74, 28), banner(-74, 36)),
		},
		-- 14
		{
			Id = "CuckooHouse",
			Name = "Cuckoo House",
			Description = "A tiny walnut cottage with a gold roof, a clock on the gable and a little bird in the window.",
			Pad = Vector2.new(-38, 53),
			PriceSeconds = 381,
			Pieces = {
				B(-44, 3.5, 50, 8, 7, 7, WOOD, Wood),
				B(-46.3, 8.5, 50, 5.6, 0.7, 8.6, GOLD, Metal, 0, 0, 36),
				B(-41.7, 8.5, 50, 5.6, 0.7, 8.6, GOLD, Metal, 0, 0, -36),
				Cz(-44, 7.8, 53.7, 3, 0.4, STARW, Plastic),
				B(-44, 2.4, 53.55, 2.4, 4.4, 0.4, DBRASS, Wood),
				B(-44, 4.9, 54, 2.8, 0.4, 1.4, GOLD, Metal),
				Ball(-44, 5.7, 54, 1.2, 1.2, 1.2, CYAN, Plastic),
				Cy(-41.4, 1.6, 53.8, 0.6, 3, GOLD, Metal),
				Cy(-46.6, 1.6, 53.8, 0.6, 3, GOLD, Metal),
				Ball(-41.4, 0.5, 53.8, 1.2, 1.4, 1.2, BRASS, Metal),
				Ball(-46.6, 0.5, 53.8, 1.2, 1.4, 1.2, BRASS, Metal),
			},
		},
		-- 15
		{
			Id = "StarPond",
			Name = "Starlight Pond",
			Description = "A still pond of deep blue water with a gold rim and floating gold clocks.",
			Pad = Vector2.new(66, -8),
			PriceSeconds = 439,
			Pieces = {
				B(68, 0.3, 4, 20, 0.5, 13, MIDNIGHT, Concrete),
				B(68, 0.4, 4, 18, 0.2, 11, INDIGO, Glass),
				B(68, 0.75, -2.5, 20.4, 1.5, 1.2, GOLD, Metal),
				B(68, 0.75, 10.5, 20.4, 1.5, 1.2, GOLD, Metal),
				B(57.8, 0.75, 4, 1.2, 1.5, 13, GOLD, Metal),
				B(78.2, 0.75, 4, 1.2, 1.5, 13, GOLD, Metal),
				B(64, 0.5, 2, 3, 0.1, 3, GOLD, Metal),
				B(71, 0.5, 6, 3.6, 0.1, 3.6, GOLD, Metal),
				B(68, 0.5, 3, 2.2, 0.1, 2.2, STARW, Plastic),
				B(63, 0.5, 7, 2.2, 0.1, 2.2, STARW, Plastic),
			},
		},
		-- 16
		{
			Id = "ZodiacWheel",
			Name = "Zodiac Wheel",
			Description = "A tall wheel of the twelve signs turns on a brass stand: gold rim, midnight face and a golden hub.",
			Pad = Vector2.new(50, 21),
			RewardMult = 1.2,
			PriceSeconds = 504,
			Pieces = {
				B(48, 0.6, 14, 11, 1.2, 5, DSTONE, Granite),
				B(42.6, 6, 14, 0.9, 10, 1.2, BRASS, Metal),
				B(53.4, 6, 14, 0.9, 10, 1.2, BRASS, Metal),
				Cz(48, 10.5, 14, 16, 1.2, GOLD, Metal),
				Cz(48, 10.5, 14.5, 13.4, 0.8, MIDNIGHT, Plastic),
				Cz(48, 10.5, 15, 3.2, 0.8, GOLD, Metal),
				B(48, 10.5, 15.2, 12, 0.5, 0.4, GOLD, Metal, 0, 0, 0),
				B(48, 10.5, 15.2, 12, 0.5, 0.4, GOLD, Metal, 0, 0, 60),
				B(48, 10.5, 15.2, 12, 0.5, 0.4, GOLD, Metal, 0, 0, 120),
				Ball(42.6, 12, 14, 1.6, 1.6, 1.6, GOLD, Metal),
				Ball(53.4, 12, 14, 1.6, 1.6, 1.6, GOLD, Metal),
			},
		},
		-- 17
		{
			Id = "RuneCircle",
			Name = "Rune Circle",
			Description = "Six rune pillars with gold caps stand round a gold seal; a small star floats above it.",
			Pad = Vector2.new(-58, 8),
			PriceSeconds = 580,
			Pieces = concat(
				{
					B(-58, 0.25, -4, 19, 0.5, 19, MIDNIGHT, Marble),
					B(-58, 0.45, -4, 8, 0.2, 8, GOLD, Metal),
					Ball(-58, 9.5, -4, 3, 3, 3, STARW, Plastic),
				},
				runePillar(-58, -4, 7, 0),
				runePillar(-58, -4, 7, 60),
				runePillar(-58, -4, 7, 120),
				runePillar(-58, -4, 7, 180),
				runePillar(-58, -4, 7, 240),
				runePillar(-58, -4, 7, 300)
			),
		},
		-- 18
		{
			Id = "CogGate",
			Name = "Cog Gate",
			Description = "Two stone pillars and a gold lintel form a gate over the walkway, crowned by a huge turning cog.",
			Pad = Vector2.new(-12, 22),
			Yaw = -18.4,
			PriceSeconds = 667,
			Pieces = {
				B(-22, 1, 17.7, 4.4, 2, 4.4, STONE, Marble),
				B(-22, 1, 39.7, 4.4, 2, 4.4, STONE, Marble),
				B(-22, 8.5, 17.7, 2.6, 13, 2.6, DARK, Granite),
				B(-22, 8.5, 39.7, 2.6, 13, 2.6, DARK, Granite),
				B(-22, 15.4, 17.7, 3.4, 1.2, 3.4, GOLD, Metal),
				B(-22, 15.4, 39.7, 3.4, 1.2, 3.4, GOLD, Metal),
				B(-22, 17.2, 28.7, 2.4, 2.2, 25, GOLD, Metal),
				Cx(-22, 22, 28.7, 12, 1.6, BRASS, Metal),
				Cx(-22, 22, 28.7, 3.4, 2.2, GOLD, Metal),
				Ball(-22, 12, 17.7, 2, 2, 2, STARW, Plastic),
				Ball(-22, 12, 39.7, 2, 2, 2, STARW, Plastic),
			},
		},
		-- 19
		{
			Id = "BellArch",
			Name = "Chime Bells",
			Description = "Three golden bells of different sizes hang from a brass arch and ring out the hours.",
			Pad = Vector2.new(-72, 4),
			PriceSeconds = 767,
			Pieces = {
				B(-72, 0.4, 12, 12, 0.8, 4, STONE, Marble),
				B(-76, 5.8, 12, 1.4, 10, 1.4, BRASS, Metal),
				B(-68, 5.8, 12, 1.4, 10, 1.4, BRASS, Metal),
				B(-72, 11.2, 12, 10.4, 1.4, 1.6, GOLD, Metal),
				Ball(-76, 12.4, 12, 1.8, 1.8, 1.8, GOLD, Metal),
				Ball(-68, 12.4, 12, 1.8, 1.8, 1.8, GOLD, Metal),
				Ball(-74.6, 7.8, 12, 2.6, 3.4, 2.6, GOLD, Metal),
				Ball(-72, 7.2, 12, 3.4, 4.2, 3.4, BRASS, Metal),
				Ball(-69.4, 7.8, 12, 2.6, 3.4, 2.6, GOLD, Metal),
				Ball(-74.6, 5.8, 12, 0.8, 0.8, 0.8, DBRASS, Metal),
				Ball(-72, 4.9, 12, 1, 1, 1, DBRASS, Metal),
				Ball(-69.4, 5.8, 12, 0.8, 0.8, 0.8, DBRASS, Metal),
			},
		},
		-- 20
		{
			Id = "Sentinel",
			Name = "Clockwork Sentinel",
			Description = "A brass automaton guards the plaza: a clock in its chest, a cog on its back and a starry eye.",
			Pad = Vector2.new(58, -16),
			PriceSeconds = 882,
			Pieces = {
				B(68, 0.7, -18, 9, 1.4, 9, STONE, Marble),
				B(66.4, 3.4, -18, 1.8, 4, 2, DBRASS, Metal),
				B(69.6, 3.4, -18, 1.8, 4, 2, DBRASS, Metal),
				B(68, 8, -18, 5.4, 5.2, 3.6, BRASS, Metal),
				Cz(68, 8.4, -16.1, 3.2, 0.4, STARW, Plastic),
				B(64.4, 8.4, -18, 1.4, 4.4, 1.6, DBRASS, Metal),
				B(71.6, 8.4, -18, 1.4, 4.4, 1.6, DBRASS, Metal),
				Ball(68, 12.6, -18, 3.8, 3.4, 3.4, GOLD, Metal),
				B(68, 12.8, -16.3, 2.8, 0.7, 0.4, CYAN, Plastic),
				Cz(68, 8.6, -20, 5, 0.8, GOLD, Metal),
				Cy(68, 14.8, -18, 0.5, 1.4, GOLD, Metal),
			},
		},
		-- 21
		{
			Id = "GiantSundial",
			Name = "Giant Sundial",
			Description = "A broad stone dial with twelve hour marks and a golden gnomon that casts the hours across the plaza.",
			Pad = Vector2.new(-6, -51),
			PriceSeconds = 1015,
			Pieces = concat(
				{
					Cy(-18, 0.5, -51, 12, 1, STONE, Marble),
					Cy(-18, 1.1, -51, 10.6, 0.3, PEARL, Marble),
					W(-18, 3.1, -51, 0.8, 4, 4.4, GOLD, Metal),
				},
				(function()
					local ticks: { Piece } = {}
					for i = 0, 11 do
						local a = math.rad(i * 30)
						table.insert(
							ticks,
							B(-18 + 4.6 * math.cos(a), 1.4, -51 + 4.6 * math.sin(a), 0.7, 0.7, 0.7, DARK, Granite)
						)
					end
					return ticks
				end)()
			),
		},
		-- 22
		{
			Id = "TimeThrone",
			Name = "Eternal Throne",
			Description = "A three-tier pearl dais carries the golden throne of time, with a clock halo behind it and two star pillars.",
			Pad = Vector2.new(56, -42),
			RewardMult = 1.3,
			PriceSeconds = 1167,
			Pieces = {
				Cy(68, 0.8, -42, 18, 1.6, PEARL, Marble),
				Cy(68, 2.4, -42, 13, 1.6, STARW, Marble),
				Cy(68, 4, -42, 8, 1.6, PEARL, Marble),
				B(68, 5.8, -43, 4.6, 2, 4.4, GOLD, Metal),
				B(68, 10, -45.2, 5, 8.4, 1.2, DBRASS, Metal),
				Cz(68, 12.6, -46.2, 9, 0.8, GOLD, Metal),
				Cz(68, 12.6, -45.7, 6.4, 0.6, STARW, Plastic),
				B(65.3, 7.4, -43, 0.8, 2, 4.2, GOLD, Metal),
				B(70.7, 7.4, -43, 0.8, 2, 4.2, GOLD, Metal),
				Cy(59.4, 6, -42, 1.2, 12, GOLD, Metal),
				Cy(76.6, 6, -42, 1.2, 12, GOLD, Metal),
				Ball(59.4, 12.8, -42, 2.2, 2.2, 2.2, STARW, Plastic),
				Ball(76.6, 12.8, -42, 2.2, 2.2, 2.2, STARW, Plastic),
			},
		},
		-- 23
		{
			Id = "Orrery",
			Name = "Celestial Orrery",
			Description = "A golden sun on a brass column with two gold orbit rings and five little planets.",
			Pad = Vector2.new(-6, -38),
			PriceSeconds = 1342,
			Pieces = {
				Cy(-18, 1, -37.5, 8, 2, STONE, Marble),
				Cy(-18, 4.5, -37.5, 2, 5, BRASS, Metal),
				Ball(-18, 8.6, -37.5, 4.4, 4.4, 4.4, GOLD, Metal),
				B(-18, 8.6, -37.5, 12.6, 0.3, 12.6, GOLD, Metal),
				B(-18, 9.4, -37.5, 8.2, 0.3, 8.2, BRASS, Metal),
				Ball(-12.6, 9, -37.5, 1.8, 1.8, 1.8, VIOLET, Plastic),
				Ball(-22.6, 9, -34, 1.5, 1.5, 1.5, CYAN, Plastic),
				Ball(-15, 9.8, -42, 1.3, 1.3, 1.3, STARW, Plastic),
				Ball(-24, 9.8, -39, 1.6, 1.6, 1.6, COPPER, Plastic),
				Ball(-18, 10.2, -33, 1.2, 1.2, 1.2, PEARL, Plastic),
			},
		},
		-- 24
		{
			Id = "Engine",
			Name = "Mainspring Engine",
			Description = "A brass engine house with giant meshing gears on its front, copper pipes and a chimney: the heart of time.",
			Pad = Vector2.new(-4, -24),
			RewardMult = 1.4,
			PriceSeconds = 1543,
			Pieces = {
				B(-16, 1, -22, 14, 2, 11, DSTONE, Granite),
				B(-16, 6, -22, 12, 8, 9, DARK, Metal),
				B(-16, 10.4, -22, 13, 0.8, 10, GOLD, Metal),
				Cz(-18.4, 6.4, -17.2, 8, 1, BRASS, Metal),
				Cz(-18.4, 6.4, -16.6, 2.4, 1.6, GOLD, Metal),
				Cz(-12.2, 8.4, -17.2, 5, 1, GOLD, Metal),
				Cz(-12.2, 4, -17.2, 4, 1, COPPER, Metal),
				Cy(-20.4, 13, -24, 2.4, 5, COPPER, Metal),
				Cy(-20.4, 15.8, -24, 3, 0.8, GOLD, Metal),
				Cy(-11, 12.6, -25, 1.6, 4, BRASS, Metal),
				Cy(-11, 15, -25, 2.4, 0.8, GOLD, Metal),
				B(-22.6, 3, -22, 1.6, 2.4, 4, COPPER, Metal),
				Cx(-9.4, 3.6, -22, 1.4, 1.8, BRASS, Metal),
			},
		},
		-- 25
		{
			Id = "ClockBase",
			Name = "Clock Base",
			Description = "The foot of the Clock Tower: a pearl plinth, a stepped midnight hall with a gold door and corner pillars.",
			Pad = Vector2.new(-62, -16),
			PriceSeconds = 1775,
			Pieces = {
				B(-50, 1, -34, 26, 2, 26, STONE, Marble),
				B(-50, 3, -34, 22, 2, 22, PEARL, Marble),
				B(-50, 9, -34, 16, 10, 16, MIDNIGHT, Concrete),
				B(-50, 14.5, -34, 18, 1, 18, GOLD, Metal),
				B(-57.6, 9.5, -41.6, 2.4, 9, 2.4, STARW, Marble),
				B(-42.4, 9.5, -41.6, 2.4, 9, 2.4, STARW, Marble),
				B(-57.6, 9.5, -26.4, 2.4, 9, 2.4, STARW, Marble),
				B(-42.4, 9.5, -26.4, 2.4, 9, 2.4, STARW, Marble),
				B(-50, 8, -25.7, 6.6, 8, 0.6, GOLD, Metal),
				B(-50, 7.2, -25.4, 4.4, 6.4, 0.6, WOOD, Wood),
				Ball(-54.2, 6.4, -24.6, 1.6, 1.6, 1.6, STARW, Plastic),
				Ball(-45.8, 6.4, -24.6, 1.6, 1.6, 1.6, STARW, Plastic),
			},
		},
		-- 26
		{
			Id = "TowerShaft",
			Name = "Tower Shaft",
			Description = "A tall midnight shaft with gold bands, pearl corner ribs and star-white windows.",
			Pad = Vector2.new(-57, -16),
			RewardMult = 1.4,
			PriceSeconds = 2041,
			Pieces = {
				B(-50, 25, -34, 10, 20, 10, MIDNIGHT, Concrete),
				B(-50, 17.4, -34, 11.4, 0.8, 11.4, GOLD, Metal),
				B(-50, 25, -34, 11.4, 0.8, 11.4, GOLD, Metal),
				B(-50, 34.4, -34, 11.4, 1.2, 11.4, GOLD, Metal),
				B(-55.2, 25.2, -39.2, 1.2, 19.6, 1.2, PEARL, Marble),
				B(-44.8, 25.2, -39.2, 1.2, 19.6, 1.2, PEARL, Marble),
				B(-55.2, 25.2, -28.8, 1.2, 19.6, 1.2, PEARL, Marble),
				B(-44.8, 25.2, -28.8, 1.2, 19.6, 1.2, PEARL, Marble),
				B(-50, 21, -28.8, 2.6, 4.4, 0.5, STARW, Plastic),
				B(-50, 29.6, -28.8, 2.6, 4.4, 0.5, STARW, Plastic),
				B(-44.8, 21, -34, 0.5, 4.4, 2.6, STARW, Plastic),
				B(-55.2, 21, -34, 0.5, 4.4, 2.6, STARW, Plastic),
				B(-44.8, 29.6, -34, 0.5, 4.4, 2.6, STARW, Plastic),
				B(-55.2, 29.6, -34, 0.5, 4.4, 2.6, STARW, Plastic),
			},
		},
		-- 27
		{
			Id = "ClockFace",
			Name = "Clock Face",
			Description = "The big clock case with a white face and a gold bezel on all four sides, topped by a stepped roof and a golden needle.",
			Pad = Vector2.new(-52, -16),
			PriceSeconds = 2347,
			Pieces = {
				B(-50, 35.8, -34, 12, 1.6, 12, GOLD, Metal),
				B(-50, 37.4, -34, 14, 1.6, 14, PEARL, Marble),
				B(-50, 45, -34, 16, 14, 16, INDIGO, Concrete),
				Cz(-50, 44, -25.7, 12.8, 0.6, GOLD, Metal),
				Cz(-50, 44, -25.5, 11.4, 0.6, STARW, Plastic),
				Cz(-50, 44, -42.3, 12.8, 0.6, GOLD, Metal),
				Cz(-50, 44, -42.5, 11.4, 0.6, STARW, Plastic),
				Cx(-41.7, 44, -34, 12.8, 0.6, GOLD, Metal),
				Cx(-41.5, 44, -34, 11.4, 0.6, STARW, Plastic),
				Cx(-58.3, 44, -34, 12.8, 0.6, GOLD, Metal),
				Cx(-58.5, 44, -34, 11.4, 0.6, STARW, Plastic),
				B(-50, 52, -34, 18, 1.4, 18, GOLD, Metal),
				B(-50, 54.2, -34, 13, 3, 13, DARK, Metal),
				B(-50, 57, -34, 8, 2.6, 8, NAVY, Metal),
				Cy(-50, 60.6, -34, 1.2, 4.6, GOLD, Metal),
				Ball(-50, 63.4, -34, 2, 2, 2, STARW, Plastic),
			},
		},
		-- 28
		{
			Id = "ClockHands",
			Name = "Clock Hands",
			Description = "Long gold hour and minute hands on every face, always showing ten past ten.",
			Pad = Vector2.new(-47, -16),
			RewardMult = 1.5,
			PriceSeconds = 2699,
			Pieces = {
				B(-51.13, 44.65, -24.9, 4.6, 0.9, 0.5, GOLD, Metal, 0, 0, 150),
				B(-48.27, 45, -24.9, 6, 0.7, 0.5, GOLD, Metal, 0, 0, 30),
				Cz(-50, 44, -24.9, 1.4, 0.6, BRASS, Metal),
				B(-48.87, 44.65, -43.1, 4.6, 0.9, 0.5, GOLD, Metal, 0, 0, 30),
				B(-51.73, 45, -43.1, 6, 0.7, 0.5, GOLD, Metal, 0, 0, 150),
				Cz(-50, 44, -43.1, 1.4, 0.6, BRASS, Metal),
				B(-40.9, 44.65, -32.87, 0.5, 0.9, 4.6, GOLD, Metal, -30, 0, 0),
				B(-40.9, 45, -35.73, 0.5, 0.7, 6, GOLD, Metal, 30, 0, 0),
				Cx(-40.9, 44, -34, 1.4, 0.6, BRASS, Metal),
				B(-59.1, 44.65, -35.13, 0.5, 0.9, 4.6, GOLD, Metal, 30, 0, 0),
				B(-59.1, 45, -32.27, 0.5, 0.7, 6, GOLD, Metal, -30, 0, 0),
				Cx(-59.1, 44, -34, 1.4, 0.6, BRASS, Metal),
			},
		},
		-- 29
		{
			Id = "GearRing",
			Name = "Gear Ring",
			Description = "A huge ring of brass cogs floats around the tower, with small gold gears circling above it.",
			Pad = Vector2.new(-42, -16),
			PriceSeconds = 3104,
			Pieces = {
				B(-50, 24, -34, 35, 1.4, 35, BRASS, Metal),
				Cy(-60.4, 27.6, -34, 8, 1.2, GOLD, Metal),
				Cy(-39.6, 27.6, -34, 8, 1.2, GOLD, Metal),
				Cy(-50, 27.6, -44.4, 8, 1.2, GOLD, Metal),
				Cy(-50, 27.6, -23.6, 8, 1.2, GOLD, Metal),
				Cy(-60.4, 28.4, -34, 2.4, 1.2, DBRASS, Metal),
				Cy(-39.6, 28.4, -34, 2.4, 1.2, DBRASS, Metal),
				Cy(-50, 28.4, -44.4, 2.4, 1.2, DBRASS, Metal),
				Cy(-50, 28.4, -23.6, 2.4, 1.2, DBRASS, Metal),
			},
		},
		-- 30
		{
			Id = "Hourglass",
			Name = "Floating Hourglass",
			Description = "A gold-framed hourglass of star-white sand floats high above the tower, the last grains falling forever.",
			Pad = Vector2.new(-37, -16),
			RewardMult = 1.5,
			PriceSeconds = 3570,
			Pieces = {
				Cy(-50, 68.4, -34, 12, 0.8, GOLD, Metal),
				Cy(-50, 89.6, -34, 12, 0.8, GOLD, Metal),
				Ball(-50, 73.6, -34, 9, 9.6, 9, GLASS, Glass),
				Ball(-50, 84.4, -34, 9, 9.6, 9, GLASS, Glass),
				Cy(-50, 79, -34, 1.4, 3, GLASS, Glass),
				B(-53.9, 79, -37.9, 0.9, 21, 0.9, GOLD, Metal),
				B(-46.1, 79, -37.9, 0.9, 21, 0.9, GOLD, Metal),
				B(-53.9, 79, -30.1, 0.9, 21, 0.9, GOLD, Metal),
				B(-46.1, 79, -30.1, 0.9, 21, 0.9, GOLD, Metal),
				Ball(-50, 71.4, -34, 6.4, 3.8, 6.4, SAND, Plastic),
				Ball(-50, 86.6, -34, 6.4, 3.4, 6.4, STARW, Plastic),
				Cy(-50, 78, -34, 0.4, 5, SAND, Plastic),
				Ball(-50, 92.4, -34, 2.2, 2.2, 2.2, GOLD, Metal),
				Ball(-58.4, 82, -34, 1.6, 1.6, 1.6, STARW, Plastic),
				Ball(-41.6, 76, -34, 1.6, 1.6, 1.6, STARW, Plastic),
			},
		},
	},
}

return theme
