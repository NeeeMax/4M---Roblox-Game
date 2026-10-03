--!strict
-- Theme of the Shiba of bay 24: Key Observatory (Config/DecorTypes -> Theme). 160 x 115: Galaxy Shiba stands in front of the Great Dome
-- (the big observatory in the back left) on a star medallion; a winding walkway passes telescope gardens, a planetarium, dish fields,
-- a rocket and a crater, and ends at the tall radio spire in the back right. Props sit in loose clusters, turned toward the path.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lamps, stars and crystals are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local NAVY = C(24, 30, 70)
local PAVE = C(44, 50, 92)
local INDIGO = C(60, 66, 140)
local PURPLE = C(118, 86, 186)
local LILAC = C(170, 146, 226)
local SILVER = C(200, 206, 222)
local STEEL = C(128, 138, 160)
local DARK = C(46, 50, 72)
local BRASS = C(196, 146, 58)
local GOLD = C(246, 204, 76)
local WHITE = C(238, 240, 250)
local TEAL = C(72, 190, 204)
local MOSS = C(58, 112, 98)
local STONE = C(146, 150, 168)
local ROCK = C(86, 80, 100)
local COPPER = C(190, 108, 72)
local RED = C(212, 72, 76)
local CREAM = C(236, 224, 198)
local WOOD = C(122, 86, 60)
local SOLAR = C(50, 90, 190)

local Concrete = Enum.Material.Concrete
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Granite = Enum.Material.Granite
local Wood = Enum.Material.Wood
local Glass = Enum.Material.Glass
local Grass = Enum.Material.Grass
local Slate = Enum.Material.Slate
local Fabric = Enum.Material.Fabric
local Marble = Enum.Material.Marble

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

-- Cylinder lying along Z (a ring or wheel facing the road): diameter d, thickness len.
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

-- Cylinder with its axis along X turned by rz degrees about Z (a telescope tube or a tilted dish): diameter d, length len.
local function Cr(
	x: number,
	y: number,
	z: number,
	d: number,
	len: number,
	color: Color3,
	mat: Enum.Material,
	rz: number
): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, rz),
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

local function R(y: number): Vector3
	return Vector3.new(0, y, 0)
end

-- ---- parts (centre x, z; everything below is relative to it) -------------------------------------------------------------

local function ground(): Pieces
	return {
		B(0, 0.15, 0, 160, 0.3, 115, PAVE, Concrete),
		B(-60, 0.3, 46, 34, 0.4, 18, MOSS, Grass),
		B(44, 0.3, 50, 30, 0.4, 12, MOSS, Grass),
		B(58, 0.3, -28, 26, 0.4, 20, MOSS, Grass),
		B(10, 0.3, 14, 30, 0.4, 22, MOSS, Grass),
		B(-34, 0.28, -14, 34, 0.3, 34, INDIGO, Concrete),
		B(-34, 0.33, -14, 26, 0.3, 26, PURPLE, Concrete),
		B(-34, 0.38, -14, 18, 0.3, 18, NAVY, Concrete),
		B(-34, 0.43, -14, 10, 0.3, 10, GOLD, Concrete),
	}
end

-- 22 x 3, 12 tall: board on two posts that reads OBSERVATORY seen from the road.
local function sign(x: number, z: number): Pieces
	return {
		B(x - 10, 0.4, z, 3, 0.8, 3, STONE, Granite),
		B(x + 10, 0.4, z, 3, 0.8, 3, STONE, Granite),
		Cy(x - 10, 4.8, z, 1.4, 8, DARK, Metal),
		Cy(x + 10, 4.8, z, 1.4, 8, DARK, Metal),
		B(x, 8.2, z, 22, 5, 1, NAVY, Plastic),
		B(x, 11.2, z, 22.6, 0.7, 1.6, GOLD, Metal),
		Ball(x - 10, 9.6, z, 1.8, 1.8, 1.8, GOLD, Metal),
		Ball(x + 10, 9.6, z, 1.8, 1.8, 1.8, GOLD, Metal),
	}
end

-- 10 x 9, 13 tall: brass-and-white refractor on a stone plinth, tube pointing up and to the left.
local function telescope(x: number, z: number): Pieces
	return {
		B(x, 0.4, z, 9, 0.8, 9, STONE, Granite),
		Cy(x + 0.8, 3.4, z, 2.4, 5.6, WHITE, Metal),
		B(x + 0.8, 6.6, z, 3, 2, 3, BRASS, Metal),
		Cr(x - 1.4, 9.4, z, 2.2, 11, WHITE, Metal, -35),
		Cr(x - 1.2, 11.6, z + 1.4, 0.9, 5.6, BRASS, Metal, -35),
		Ball(x + 3.8, 5.6, z, 2.2, 2.2, 2.2, DARK, Metal),
	}
end

-- 9 x 9, 5.5 tall: stone sundial with a brass plate.
local function sundial(x: number, z: number): Pieces
	return {
		B(x, 0.2, z, 9, 0.4, 9, STONE, Granite),
		Cy(x, 1.4, z, 2.6, 2.4, STONE, Granite),
		B(x, 2.9, z, 5.6, 0.5, 5.6, BRASS, Metal),
		B(x + 0.3, 4.3, z - 0.6, 0.5, 2.4, 3.2, GOLD, Metal),
	}
end

-- 17 x 8, 9 tall: a grove of four lamp posts of different heights with a stone bench between them.
local function lamps(x: number, z: number): Pieces
	return {
		Cy(x - 7, 3.4, z - 1.5, 0.6, 6, DARK, Metal),
		B(x - 7, 7, z - 1.5, 1.6, 1.6, 1.6, CREAM, Plastic),
		Cy(x - 1, 4.2, z + 2.5, 0.6, 7.5, DARK, Metal),
		B(x - 1, 8.6, z + 2.5, 1.8, 1.8, 1.8, CREAM, Plastic),
		Cy(x + 5, 3.2, z - 2.5, 0.6, 5.5, DARK, Metal),
		B(x + 5, 6.4, z - 2.5, 1.6, 1.6, 1.6, CREAM, Plastic),
		Cy(x + 8.4, 3.6, z + 1.5, 0.6, 6.5, DARK, Metal),
		B(x + 8.4, 7.4, z + 1.5, 1.6, 1.6, 1.6, CREAM, Plastic),
		B(x + 2.2, 0.9, z - 1, 5, 1.2, 1.4, STONE, Granite, R(15)),
	}
end

-- 7 x 6, 6 tall: moon rover with a solar panel, mast and dish.
local function rover(x: number, z: number): Pieces
	return {
		B(x, 2.4, z, 5.2, 1.8, 3.6, WHITE, Metal),
		B(x - 1.2, 3.8, z, 3.8, 0.3, 3.2, SOLAR, Plastic, Vector3.new(0, 0, 10)),
		Cz(x - 2.2, 1.1, z - 2.3, 2.2, 0.8, DARK, Plastic),
		Cz(x + 2.2, 1.1, z - 2.3, 2.2, 0.8, DARK, Plastic),
		Cz(x - 2.2, 1.1, z + 2.3, 2.2, 0.8, DARK, Plastic),
		Cz(x + 2.2, 1.1, z + 2.3, 2.2, 0.8, DARK, Plastic),
		Cy(x + 1.6, 4.4, z - 0.6, 0.4, 3.6, STEEL, Metal),
		Cr(x + 1.6, 6.1, z - 0.6, 2, 0.4, GOLD, Metal, 60),
	}
end

-- 14 x 8, 3.5 tall: three stargazing loungers at different angles.
local function loungers(x: number, z: number): Pieces
	return {
		B(x - 4.6, 1, z + 0.5, 5.6, 0.8, 2.2, WOOD, Wood, R(22)),
		B(x - 6.6, 2, z + 0.9, 2.4, 0.4, 2.2, PURPLE, Fabric, Vector3.new(0, 22, 40)),
		B(x + 0.2, 1, z - 1.6, 5.6, 0.8, 2.2, WOOD, Wood, R(-14)),
		B(x - 1.9, 2, z - 1.9, 2.4, 0.4, 2.2, INDIGO, Fabric, Vector3.new(0, -14, 40)),
		B(x + 5, 1, z + 1.2, 5.6, 0.8, 2.2, WOOD, Wood, R(30)),
		B(x + 3, 2, z + 2.4, 2.4, 0.4, 2.2, PURPLE, Fabric, Vector3.new(0, 30, 40)),
		B(x + 0.6, 0.8, z + 2.6, 1.8, 1.6, 1.8, STONE, Granite),
	}
end

-- 9 x 6, 8 tall: the Cosmic Cafe cart with a striped awning and a star sign.
local function cart(x: number, z: number): Pieces
	return {
		B(x, 2, z, 7, 3, 4, PURPLE, Wood),
		B(x, 3.7, z + 2.1, 7.4, 0.5, 1.2, CREAM, Wood),
		Cy(x - 3.2, 4.6, z + 2.6, 0.4, 4.4, STEEL, Metal),
		Cy(x + 3.2, 4.6, z + 2.6, 0.4, 4.4, STEEL, Metal),
		B(x - 2.3, 7, z + 1.6, 2.4, 0.4, 3.4, RED, Fabric, Vector3.new(-14, 0, 0)),
		B(x + 0.1, 7, z + 1.6, 2.4, 0.4, 3.4, WHITE, Fabric, Vector3.new(-14, 0, 0)),
		B(x + 2.5, 7, z + 1.6, 2.4, 0.4, 3.4, RED, Fabric, Vector3.new(-14, 0, 0)),
		Cz(x - 2.6, 0.9, z + 2.2, 1.8, 0.6, DARK, Plastic),
		Cz(x + 2.6, 0.9, z + 2.2, 1.8, 0.6, DARK, Plastic),
		B(x - 1.5, 5.4, z - 1.2, 1.6, 2, 1.6, STEEL, Metal),
	}
end

-- 22 x 14, 3.5 tall: a meteor crater with a raised rim of rocks and the burnt meteor in the middle.
local function crater(x: number, z: number): Pieces
	return {
		B(x, 0.2, z, 22, 0.4, 14, ROCK, Slate),
		B(x - 8.4, 1.3, z + 1, 4, 2.6, 5.4, ROCK, Slate, R(20)),
		B(x - 5.6, 1.6, z + 5.2, 4.6, 3.2, 3, ROCK, Slate, R(-14)),
		B(x + 0.4, 1.2, z + 5.8, 4, 2.4, 2.6, STONE, Slate, R(8)),
		B(x + 6, 1.7, z + 4.8, 4.4, 3.4, 3.2, ROCK, Slate, R(-24)),
		B(x + 8.8, 1.2, z - 0.4, 3.4, 2.4, 5, ROCK, Slate, R(12)),
		B(x + 5.4, 1.5, z - 5.2, 4.4, 3, 2.8, STONE, Slate, R(26)),
		B(x - 2.6, 1.3, z - 5.6, 5, 2.6, 2.6, ROCK, Slate, R(-8)),
		B(x - 7, 1.2, z - 4, 3.4, 2.4, 3.4, STONE, Slate, R(30)),
		B(x + 0.2, 1.3, z - 0.2, 3.4, 2.6, 3.2, DARK, Slate, Vector3.new(0, 20, 14)),
	}
end

-- 7 x 7, 6 tall: a big meteorite on a stone plinth.
local function meteorite(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 7, 1, 7, STONE, Granite),
		B(x, 1.2, z, 5, 0.5, 5, DARK, Granite),
		Ball(x, 3.6, z, 5.2, 4.6, 5, ROCK, Slate),
		Ball(x + 1.6, 5.4, z - 0.4, 2.4, 1.8, 2.4, DARK, Slate),
		B(x + 2.2, 1.6, z + 2.6, 1.4, 1, 1.4, ROCK, Slate, R(25)),
	}
end

-- 14 x 14, 8 tall: brass orrery, a golden sun and planets on arms above a stone disc.
local function orrery(x: number, z: number): Pieces
	return {
		Cy(x, 0.6, z, 14, 1.2, STONE, Granite),
		Cy(x, 2.6, z, 2.4, 3.2, BRASS, Metal),
		Ball(x, 5.2, z, 3.4, 3.4, 3.4, GOLD, Metal),
		Cy(x, 4.4, z, 8, 0.25, BRASS, Metal),
		Cy(x, 4.4, z, 12.4, 0.25, BRASS, Metal),
		Ball(x + 4, 5.2, z, 1.6, 1.6, 1.6, TEAL, Plastic),
		Ball(x - 1.8, 5.2, z + 5.5, 2.2, 2.2, 2.2, COPPER, Plastic),
		Ball(x - 4.8, 5.2, z - 3.6, 1.4, 1.4, 1.4, LILAC, Plastic),
		Ball(x + 5.6, 5.6, z - 3.4, 2.6, 2.6, 2.6, PURPLE, Plastic),
	}
end

-- 18 x 18, 8.5 tall: a ring of standing stones with lintels around a low altar.
local function henge(x: number, z: number): Pieces
	return {
		B(x + 7.2, 3.2, z, 1.6, 6.4, 2.6, STONE, Granite, R(0)),
		B(x + 5, 3.8, z - 5.2, 1.6, 7.6, 2.6, STONE, Granite, R(36)),
		B(x - 1, 3.4, z - 7.4, 1.6, 6.8, 2.6, ROCK, Granite, R(78)),
		B(x - 6.4, 4.2, z - 3.6, 1.6, 8.4, 2.6, STONE, Granite, R(-40)),
		B(x - 7.4, 3.2, z + 2.2, 1.6, 6.4, 2.6, ROCK, Granite, R(-80)),
		B(x - 3, 3.6, z + 6.6, 1.6, 7.2, 2.6, STONE, Granite, R(-24)),
		B(x + 3.4, 3, z + 6.4, 1.6, 6, 2.6, ROCK, Granite, R(24)),
		B(x + 6.2, 6.9, z - 2.6, 1.4, 1.2, 6.4, STONE, Granite, R(0)),
		B(x - 2.4, 8, z - 5.6, 6.6, 1, 1.5, STONE, Granite, R(60)),
		B(x, 0.5, z, 6, 1, 4, DARK, Granite, R(20)),
		B(x + 1, 1.3, z + 0.4, 1.4, 1, 1.4, GOLD, Metal),
	}
end

-- 10 x 10, 8 tall: lunar lander with gold foil body, a grey cabin and four splayed legs.
local function lander(x: number, z: number): Pieces
	return {
		B(x, 4.2, z, 5, 3.2, 5, GOLD, Metal),
		B(x, 6.6, z, 3.6, 1.8, 3.6, STEEL, Metal),
		B(x - 3.4, 2.6, z - 3.4, 0.7, 5.6, 0.7, STEEL, Metal, Vector3.new(-18, 0, 18)),
		B(x + 3.4, 2.6, z - 3.4, 0.7, 5.6, 0.7, STEEL, Metal, Vector3.new(-18, 0, -18)),
		B(x - 3.4, 2.6, z + 3.4, 0.7, 5.6, 0.7, STEEL, Metal, Vector3.new(18, 0, 18)),
		B(x + 3.4, 2.6, z + 3.4, 0.7, 5.6, 0.7, STEEL, Metal, Vector3.new(18, 0, -18)),
		B(x - 4.4, 0.3, z - 4.4, 2, 0.6, 2, DARK, Metal),
		B(x + 4.4, 0.3, z - 4.4, 2, 0.6, 2, DARK, Metal),
		B(x - 4.4, 0.3, z + 4.4, 2, 0.6, 2, DARK, Metal),
		B(x + 4.4, 0.3, z + 4.4, 2, 0.6, 2, DARK, Metal),
		B(x + 3.2, 5, z, 0.5, 2.2, 1.4, STEEL, Metal),
	}
end

-- 12 x 9, 5.5 tall: a wooden deck with three small telescopes on tripods looking at different parts of the sky.
local function terrace(x: number, z: number): Pieces
	return {
		B(x, 0.3, z, 12, 0.6, 9, WOOD, Wood),
		B(x - 3.8, 1.9, z - 1.4, 0.9, 2.6, 0.9, DARK, Metal),
		Cr(x - 3.8, 3.6, z - 1.4, 1, 4.6, WHITE, Metal, 40),
		B(x + 0.2, 1.9, z + 1.6, 0.9, 2.6, 0.9, DARK, Metal),
		Cr(x + 0.2, 3.6, z + 1.6, 1, 4.6, BRASS, Metal, 62),
		B(x + 4, 1.9, z - 1.8, 0.9, 2.6, 0.9, DARK, Metal),
		Cr(x + 4, 3.6, z - 1.8, 1, 4.6, WHITE, Metal, 28),
	}
end

-- 10 x 8, 10 tall: a cluster of violet crystals on a rocky base.
local function crystals(x: number, z: number): Pieces
	return {
		B(x, 0.6, z, 10, 1.2, 7, ROCK, Slate),
		B(x - 0.4, 5.6, z, 2.6, 9.2, 2.6, PURPLE, Glass, Vector3.new(0, 30, 6)),
		B(x - 3.2, 4, z - 1, 2, 6.4, 2, LILAC, Glass, Vector3.new(0, 10, -12)),
		B(x + 2.8, 4.6, z + 0.6, 2.2, 7.6, 2.2, INDIGO, Glass, Vector3.new(0, 55, 10)),
		B(x + 0.6, 3.4, z + 2.4, 1.6, 5, 1.6, LILAC, Glass, Vector3.new(8, 20, 0)),
		B(x - 1.6, 3, z - 2.4, 1.8, 4.6, 1.8, PURPLE, Glass, Vector3.new(-8, 40, 0)),
		B(x + 4, 2.6, z - 1.2, 1.4, 3.6, 1.4, TEAL, Glass, Vector3.new(0, 15, 14)),
	}
end

-- 12 x 4, 10 tall: a comet sculpture, golden head and a tail of fading balls, on a stone plinth.
local function comet(x: number, z: number): Pieces
	return {
		B(x, 0.6, z, 12, 1.2, 4, STONE, Granite),
		Cy(x + 3.4, 3.6, z, 0.7, 4.8, DARK, Metal),
		Cy(x - 2, 2.8, z, 0.5, 3.2, DARK, Metal),
		Ball(x + 3.4, 7.4, z, 4.4, 4.4, 4.4, GOLD, Metal),
		Ball(x + 0.6, 6.2, z, 3.2, 3.2, 3.2, CREAM, Plastic),
		Ball(x - 1.8, 5.2, z, 2.6, 2.6, 2.6, LILAC, Plastic),
		Ball(x - 3.8, 4.4, z, 2, 2, 2, TEAL, Plastic),
		Ball(x - 5.4, 3.8, z, 1.4, 1.4, 1.4, INDIGO, Plastic),
	}
end

-- 15 x 9, 9 tall: a satellite on a display stand, gold body, blue solar wings and a dish.
local function satellite(x: number, z: number): Pieces
	return {
		B(x, 0.4, z, 9, 0.8, 9, STONE, Granite),
		Cy(x, 2.8, z, 1.6, 4, STEEL, Metal),
		B(x, 6.2, z, 3.6, 3.4, 3.6, GOLD, Metal),
		B(x - 5.6, 6.4, z, 7, 0.3, 3.2, SOLAR, Plastic, Vector3.new(0, 0, 10)),
		B(x + 5.6, 6.4, z, 7, 0.3, 3.2, SOLAR, Plastic, Vector3.new(0, 0, -10)),
		Cr(x + 0.4, 8.8, z + 1.4, 2.6, 0.5, WHITE, Metal, 50),
		Cy(x - 1, 8.8, z - 1, 0.3, 2, STEEL, Metal),
	}
end

-- 20 x 12, 10.5 tall: three radio dishes of different sizes on masts, one equipment shed.
local function dishes(x: number, z: number): Pieces
	return {
		B(x - 0.5, 1.2, z + 4.4, 5, 2.4, 3.4, WHITE, Concrete),
		Cy(x - 7, 2.6, z - 2, 1.2, 5.2, STEEL, Metal),
		Cr(x - 7, 6.8, z - 2, 8, 0.9, WHITE, Metal, 62),
		Cy(x + 3.4, 2.2, z - 0.4, 1, 4.4, STEEL, Metal),
		Cr(x + 3.4, 5.8, z - 0.4, 6, 0.8, SILVER, Metal, 52),
		Cy(x + 8, 1.8, z - 3.6, 0.9, 3.6, STEEL, Metal),
		Cr(x + 8, 4.6, z - 3.6, 4.6, 0.7, WHITE, Metal, 70),
		B(x - 7, 0.4, z - 2, 3, 0.8, 3, STONE, Concrete),
		B(x + 3.4, 0.4, z - 0.4, 2.6, 0.8, 2.6, STONE, Concrete),
	}
end

-- 9 x 9, 17 tall: a white rocket with a red nose and fins on a launch stand with a steel gantry.
local function rocket(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 9, 1, 9, DARK, Concrete),
		Cy(x - 0.6, 6.8, z, 3.8, 9.6, WHITE, Metal),
		Ball(x - 0.6, 13.6, z, 3.8, 6.4, 3.8, RED, Metal),
		B(x - 0.6, 3.6, z, 7.4, 3.6, 0.7, RED, Metal),
		B(x - 0.6, 3.6, z, 0.7, 3.6, 7.4, RED, Metal),
		B(x + 3.4, 7.5, z, 1.4, 13, 1.4, STEEL, Metal),
		B(x + 2.2, 10.5, z, 3.2, 0.7, 1, STEEL, Metal),
		B(x + 2.2, 5.5, z, 3.2, 0.7, 1, STEEL, Metal),
	}
end

-- 14 x 14, 8.5 tall: a round fountain with a column, a bowl, and orbiting planets on rings.
local function fountain(x: number, z: number): Pieces
	return {
		Cy(x, 0.7, z, 14, 1.4, STONE, Granite),
		Cy(x, 1.5, z, 12.4, 0.3, TEAL, Plastic),
		Cy(x, 3.2, z, 2, 3.6, STONE, Granite),
		Cy(x, 5.2, z, 5.6, 0.7, STONE, Granite),
		Cy(x, 6.2, z, 10, 0.25, BRASS, Metal),
		Ball(x, 6.6, z, 2.8, 2.8, 2.8, GOLD, Metal),
		Ball(x + 4.8, 6.4, z, 1.6, 1.6, 1.6, LILAC, Plastic),
		Ball(x - 3.2, 6.4, z - 3.6, 1.4, 1.4, 1.4, TEAL, Plastic),
		Ball(x - 2, 7.6, z + 4.4, 1.8, 1.8, 1.8, COPPER, Plastic),
	}
end

-- 8 x 6, 14 tall: an astronaut statue on a stone pedestal, one arm raised.
local function astronaut(x: number, z: number): Pieces
	return {
		B(x, 1, z, 7, 2, 6, STONE, Granite),
		B(x - 1, 4.6, z, 1.6, 3.6, 1.8, WHITE, Fabric),
		B(x + 1, 4.6, z, 1.6, 3.6, 1.8, WHITE, Fabric),
		B(x, 8, z, 4, 3.6, 2.6, WHITE, Fabric),
		B(x, 8.2, z - 2, 2.8, 3, 1.4, STEEL, Metal),
		Ball(x, 11.2, z, 3.6, 3.6, 3.6, WHITE, Metal),
		B(x, 11.2, z + 1.5, 2.6, 1.8, 0.5, GOLD, Glass),
		B(x - 2.8, 8, z, 1.4, 3.2, 1.6, WHITE, Fabric),
		B(x + 3, 10.4, z, 1.4, 3.4, 1.6, WHITE, Fabric, Vector3.new(0, 0, -25)),
		B(x - 3.6, 8.4, z + 2.6, 0.4, 10.4, 0.4, STEEL, Metal),
		B(x - 2.6, 12.6, z + 2.6, 2.4, 1.4, 0.2, RED, Fabric),
	}
end

-- 22 x 9, 8.5 tall: a glass greenhouse with a stepped roof and rows of night flowers.
local function greenhouse(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 22, 1, 9, STONE, Granite),
		B(x, 4.2, z, 20, 6.4, 7.4, TEAL, Glass),
		B(x, 8, z, 15, 1.4, 5.4, TEAL, Glass),
		B(x, 8.8, z, 18, 0.5, 1, STEEL, Metal),
		B(x - 9.6, 4.2, z, 0.8, 6.4, 7.6, STEEL, Metal),
		B(x + 9.6, 4.2, z, 0.8, 6.4, 7.6, STEEL, Metal),
		B(x - 4, 1.6, z, 6, 1.2, 2, MOSS, Grass),
		B(x + 5, 1.6, z, 6, 1.2, 2, MOSS, Grass),
		B(x + 0.4, 2, z + 3.6, 3, 2, 0.4, PURPLE, Plastic),
	}
end

-- 14 x 12, 16 tall: the Great Dish, a big radio dish on a tower with a cabin at its foot.
local function bigDish(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 14, 1, 12, STONE, Concrete),
		B(x + 3.6, 2.6, z + 2.8, 5, 3.2, 4, WHITE, Concrete),
		Cy(x - 1, 5, z - 1.4, 3.6, 8, STEEL, Metal),
		Cr(x - 1, 10.4, z - 1.4, 13, 1.3, WHITE, Metal, 62),
		B(x + 0.4, 14, z - 1.4, 0.7, 5.4, 0.7, STEEL, Metal, Vector3.new(0, 0, -28)),
		B(x + 1.2, 15.2, z - 1.4, 1.2, 1.2, 1.2, RED, Metal),
	}
end

-- 16 x 16, 22 tall: a silver dome tower with an open slit and a small entrance.
local function silverDome(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 16, 1, 16, STONE, Granite),
		Cy(x, 7.5, z, 12, 13, SILVER, Metal),
		Ball(x, 14, z, 12.4, 11, 12.4, WHITE, Metal),
		B(x, 15.5, z + 4.5, 2, 6, 3, DARK, Metal),
		Cy(x, 20.2, z, 0.8, 3.6, STEEL, Metal),
		B(x, 3, z + 7, 4.4, 6, 3.4, SILVER, Concrete),
		B(x - 6.8, 7, z + 4, 1.2, 12, 1.2, STEEL, Metal),
		B(x + 6.8, 7, z + 4, 1.2, 12, 1.2, STEEL, Metal),
	}
end

-- 26 x 22, 25 tall: the Planetarium, a white hall with a big dome, a portico with columns and a golden finial.
local function planetarium(x: number, z: number): Pieces
	return {
		B(x, 0.4, z, 26, 0.8, 22, STONE, Granite),
		B(x, 6.8, z - 1, 22, 12, 18, CREAM, Concrete),
		Ball(x, 13, z - 1, 17, 14, 17, WHITE, Metal),
		Cy(x, 22.6, z - 1, 0.9, 5, GOLD, Metal),
		B(x, 5, z + 10, 8.6, 9.4, 3.2, CREAM, Concrete),
		B(x, 9.9, z + 10.4, 10, 0.8, 4, INDIGO, Metal),
		Cy(x - 4.2, 4.6, z + 11.4, 1.2, 8.6, WHITE, Marble),
		Cy(x + 4.2, 4.6, z + 11.4, 1.2, 8.6, WHITE, Marble),
		B(x - 10.2, 4, z - 1, 1.6, 7.2, 1.6, STEEL, Metal),
		B(x + 10.2, 4, z - 1, 1.6, 7.2, 1.6, STEEL, Metal),
	}
end

-- 26 x 16, 20 tall: Mission Control, a white block with a stepped control room and a mast with a dish.
local function control(x: number, z: number): Pieces
	return {
		B(x, 0.5, z, 26, 1, 16, STONE, Concrete),
		B(x - 1.6, 6.8, z, 22, 11.6, 12, WHITE, Concrete),
		B(x - 4, 14.4, z - 1, 12, 3.6, 8, STEEL, Concrete),
		B(x - 1.6, 5, z + 6.2, 18, 3.6, 0.5, TEAL, Glass),
		B(x + 6.4, 4.4, z + 6.4, 3.6, 8.8, 0.6, DARK, Metal),
		B(x + 9, 12, z - 2.6, 4, 3, 4, SILVER, Concrete),
		Cy(x + 9, 17.2, z - 2.6, 0.8, 5, STEEL, Metal),
		Cr(x + 9, 18.6, z - 2.6, 4, 0.5, WHITE, Metal, 55),
		B(x - 4, 17, z - 1, 10, 0.6, 7, DARK, Metal),
		Cy(x - 11, 5, z + 7, 0.6, 8, DARK, Metal),
	}
end

-- 12 x 12, 15 tall: an armillary sphere of brass rings around a golden star on a stone base.
local function armillary(x: number, z: number): Pieces
	return {
		B(x, 0.6, z, 8, 1.2, 8, STONE, Granite),
		Cy(x, 2.6, z, 1.8, 2.8, BRASS, Metal),
		Ball(x, 8.8, z, 3.4, 3.4, 3.4, GOLD, Metal),
		Cy(x, 8.8, z, 12, 0.5, BRASS, Metal),
		Cz(x, 8.8, z, 12, 0.5, BRASS, Metal),
		Cr(x, 8.8, z, 11, 0.5, COPPER, Metal, 50),
		B(x, 15, z, 0.5, 1.6, 0.5, GOLD, Metal),
	}
end

-- 26 x 28, 32 tall: the Great Dome, a silver observatory dome on a stone drum with a pointing telescope in the slit.
local function greatDome(x: number, z: number): Pieces
	return {
		B(x, 0.8, z, 26, 1.6, 26, STONE, Granite),
		Cy(x, 8.6, z, 22, 14, SILVER, Metal),
		Ball(x, 15.6, z, 22, 24, 22, WHITE, Metal),
		B(x, 20, z + 9, 4, 12, 4, DARK, Metal),
		Cr(x, 22, z + 10, 3, 9, COPPER, Metal, 55),
		Cy(x, 29.6, z, 1, 5, STEEL, Metal),
		B(x, 5, z + 12.4, 9, 9, 4.4, CREAM, Concrete),
		B(x - 8, 8, z + 8, 1.8, 14, 1.8, STONE, Granite),
		B(x + 8, 8, z + 8, 1.8, 14, 1.8, STONE, Granite),
		B(x, 3, z + 15, 7, 1.2, 2.2, STONE, Granite),
	}
end

-- 14 x 14, 52 tall: the Beacon Spire, the one landmark: a slim lattice tower with an observation deck and a mast.
local function spire(x: number, z: number): Pieces
	return {
		B(x, 0.6, z, 14, 1.2, 14, STONE, Concrete),
		B(x - 4.4, 9, z - 4.4, 1.2, 16, 1.2, STEEL, Metal),
		B(x + 4.4, 9, z - 4.4, 1.2, 16, 1.2, STEEL, Metal),
		B(x - 4.4, 9, z + 4.4, 1.2, 16, 1.2, STEEL, Metal),
		B(x + 4.4, 9, z + 4.4, 1.2, 16, 1.2, STEEL, Metal),
		B(x, 17.6, z, 11, 1.2, 11, DARK, Metal),
		B(x, 28, z, 3.4, 19, 3.4, STEEL, Metal),
		Cy(x, 39, z, 9, 3.6, SILVER, Metal),
		Cy(x, 42.4, z, 6, 3.2, NAVY, Metal),
		Ball(x, 45, z, 6.4, 3.4, 6.4, WHITE, Metal),
		Cy(x, 49, z, 0.8, 6, STEEL, Metal),
		B(x, 52, z, 1.2, 1.2, 1.2, RED, Metal),
	}
end

-- 18 x 18, 15 tall: the showpiece, a gold spiral galaxy turning on a plinth.
local function galaxy(x: number, z: number): Pieces
	return {
		B(x, 0.8, z, 18, 1.6, 18, DARK, Granite),
		Cy(x, 3.6, z, 7, 4, STONE, Granite),
		Cy(x, 6, z, 16, 1, INDIGO, Metal),
		Ball(x, 8.8, z, 6, 6, 6, GOLD, Metal),
		B(x + 5, 7.4, z + 1.8, 7, 0.8, 2.4, LILAC, Metal, R(-20)),
		B(x - 5, 7.4, z - 1.8, 7, 0.8, 2.4, LILAC, Metal, R(-20)),
		B(x - 1.8, 7.4, z + 5, 2.4, 0.8, 7, PURPLE, Metal, R(-20)),
		B(x + 1.8, 7.4, z - 5, 2.4, 0.8, 7, PURPLE, Metal, R(-20)),
		B(x, 13.4, z, 0.8, 4, 0.8, GOLD, Metal),
		Ball(x, 15.2, z, 1.6, 1.6, 1.6, WHITE, Metal),
	}
end

local theme: DecorTypes.Theme = {
	Key = "Observatory",
	Name = "Key Observatory",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(-34, -14), Facing = 0 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(-24, 43),
		Vector2.new(6, 30),
		Vector2.new(34, 16),
		Vector2.new(-10, -4),
		Vector2.new(22, -26),
		Vector2.new(-4, -44),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(-22, -2),
	AutoPad = Vector2.new(-12, -12),
	Parts = {
		{
			Id = "Ground",
			Name = "Starfield Plaza",
			Description = "Deep-blue night paving with moss lawns and a gold star medallion under the Galaxy Shiba.",
			Pad = Vector2.new(2, 50),
			PriceSeconds = 80,
			Pieces = ground(),
		},
		{
			Id = "Sign",
			Yaw = 8,
			Name = "Observatory Sign",
			Description = "A navy board on two posts that spells OBSERVATORY in gold block letters for everyone on the road.",
			Pad = Vector2.new(-45, 50),
			PriceSeconds = 92,
			Pieces = sign(-40, 54),
		},
		{
			Id = "Telescope",
			Yaw = 18,
			Name = "Garden Refractor",
			Description = "A white and brass refractor telescope on a stone plinth, tube raised to the stars.",
			Pad = Vector2.new(14, 45),
			PriceSeconds = 106,
			Pieces = telescope(14, 46),
		},
		{
			Id = "Sundial",
			Yaw = -12,
			Name = "Star Sundial",
			Description = "A stone sundial with a brass plate and a golden pointer, set between the winding paths.",
			Pad = Vector2.new(-4, -28),
			PriceSeconds = 122,
			Pieces = sundial(-4, -28),
		},
		{
			Id = "Lamps",
			Yaw = 22,
			Name = "Lamp Grove",
			Description = "Four lamp posts of different heights with warm lanterns and a stone bench between them.",
			Pad = Vector2.new(36, 52),
			PriceSeconds = 140,
			Pieces = lamps(36, 53),
		},
		{
			Id = "Rover",
			Yaw = -20,
			Name = "Moon Rover",
			Description = "A white moon rover with four wheels, a blue solar panel, a mast and a small dish.",
			Pad = Vector2.new(16, -6),
			PriceSeconds = 161,
			Pieces = rover(16, -6),
		},
		{
			Id = "Loungers",
			Yaw = 12,
			Name = "Stargazer Loungers",
			Description = "Three wooden loungers with purple cushions tipped back at different angles for watching the sky.",
			Pad = Vector2.new(-34, 6),
			PriceSeconds = 185,
			Pieces = loungers(-34, 6),
		},
		{
			Id = "Cart",
			Yaw = 16,
			Name = "Cosmic Cafe",
			Description = "A purple coffee cart with a red and white striped awning serving star-shaped cookies.",
			Pad = Vector2.new(-36, 44),
			PriceSeconds = 213,
			Pieces = cart(-36, 44),
		},
		{
			Id = "Crater",
			Yaw = -10,
			Name = "Meteor Crater",
			Description = "A wide crater ringed with grey rocks and a burnt meteor lying in the middle.",
			Pad = Vector2.new(66, 48),
			PriceSeconds = 245,
			Pieces = crater(66, 48),
		},
		{
			Id = "Meteorite",
			Yaw = 24,
			Name = "Meteorite Plinth",
			Description = "A huge dark meteorite resting on a stone plinth with a smaller chunk beside it.",
			Pad = Vector2.new(42, 4),
			PriceSeconds = 282,
			Pieces = meteorite(42, 4),
		},
		{
			Id = "Orrery",
			Yaw = -14,
			Name = "Brass Orrery",
			Description = "A brass model of the solar system with a golden sun and coloured planets on turning rings.",
			Pad = Vector2.new(-52, 10),
			PriceSeconds = 324,
			Pieces = orrery(-52, 10),
		},
		{
			Id = "Henge",
			Yaw = 10,
			Name = "Star Henge",
			Description = "A ring of tall standing stones with lintels around a low altar that marks the solstice.",
			Pad = Vector2.new(-70, 6),
			PriceSeconds = 372,
			Pieces = henge(-70, 6),
		},
		{
			Id = "Lander",
			Yaw = 26,
			Name = "Lunar Lander",
			Description = "A gold-foil lunar lander with four splayed legs and a ladder, parked on the plaza.",
			Pad = Vector2.new(30, -8),
			PriceSeconds = 428,
			Pieces = lander(30, -8),
		},
		{
			Id = "Terrace",
			Yaw = -18,
			Name = "Telescope Terrace",
			Description = "A wooden deck with three small telescopes on tripods, each aimed at another corner of the sky.",
			Pad = Vector2.new(28, 40),
			RewardMult = 1.25,
			PriceSeconds = 492,
			Pieces = terrace(28, 40),
		},
		{
			Id = "Crystals",
			Yaw = 8,
			Name = "Moon Crystals",
			Description = "A cluster of tall violet crystals of different sizes growing out of a rocky base.",
			Pad = Vector2.new(-44, -51),
			PriceSeconds = 566,
			Pieces = crystals(-44, -51),
		},
		{
			Id = "Comet",
			Yaw = -22,
			Name = "Comet Sculpture",
			Description = "A golden comet head with a tail of fading coloured balls streaking across a stone plinth.",
			Pad = Vector2.new(-28, 27),
			PriceSeconds = 651,
			Pieces = comet(-28, 27),
		},
		{
			Id = "Satellite",
			Yaw = 20,
			Name = "Satellite Display",
			Description = "A gold satellite with blue solar wings and a dish, shown on a stone display stand.",
			Pad = Vector2.new(20, -51),
			PriceSeconds = 749,
			Pieces = satellite(20, -51),
		},
		{
			Id = "Dishes",
			Yaw = -16,
			Name = "Dish Field",
			Description = "Three radio dishes of different sizes on masts, all listening to a different part of the sky.",
			Pad = Vector2.new(64, 8),
			PriceSeconds = 861,
			Pieces = dishes(64, 8),
		},
		{
			Id = "Rocket",
			Yaw = 14,
			Name = "Launch Rocket",
			Description = "A white rocket with a red nose and fins on its stand, a steel gantry beside it.",
			Pad = Vector2.new(73, 31),
			PriceSeconds = 990,
			Pieces = rocket(73, 31),
		},
		{
			Id = "Fountain",
			Yaw = 12,
			Name = "Planet Fountain",
			Description = "A round stone fountain with a golden sun on a column and little planets circling on brass rings.",
			Pad = Vector2.new(-14, 16),
			PriceSeconds = 1139,
			Pieces = fountain(-14, 16),
		},
		{
			Id = "Astronaut",
			Yaw = -24,
			Name = "Astronaut Statue",
			Description = "A white astronaut on a stone pedestal, one arm raised, a red flag planted behind.",
			Pad = Vector2.new(38, -24),
			PriceSeconds = 1310,
			Pieces = astronaut(38, -24),
		},
		{
			Id = "Greenhouse",
			Yaw = 6,
			Name = "Moon Greenhouse",
			Description = "A glass greenhouse with a stepped roof and rows of purple night flowers.",
			Pad = Vector2.new(-62, -51),
			RewardMult = 1.25,
			PriceSeconds = 1506,
			Pieces = greenhouse(-62, -51),
		},
		{
			Id = "Dish",
			Yaw = -14,
			Name = "Great Dish",
			Description = "A big white radio dish on a steel tower that swings over a little control cabin.",
			Pad = Vector2.new(58, 26),
			PriceSeconds = 1732,
			Pieces = bigDish(58, 26),
		},
		{
			Id = "SilverDome",
			Yaw = 16,
			Name = "Silver Dome",
			Description = "A tall silver dome tower with an open slit, a small entrance and a thin lightning mast on top.",
			Pad = Vector2.new(42, -44),
			RewardMult = 1.4,
			PriceSeconds = 1992,
			Pieces = silverDome(42, -46),
		},
		{
			Id = "Planetarium",
			Yaw = 6,
			Name = "Planetarium",
			Description = "A white hall with a big dome, a pillared entrance and a golden finial where the stars are shown.",
			Pad = Vector2.new(-62, 38),
			PriceSeconds = 2291,
			Pieces = planetarium(-62, 32),
		},
		{
			Id = "Control",
			Yaw = -10,
			Name = "Mission Control",
			Description = "A white control building with a glass front, a stepped control room and a mast with a dish.",
			Pad = Vector2.new(62, -12),
			RewardMult = 1.5,
			PriceSeconds = 2635,
			Pieces = control(62, -14),
		},
		{
			Id = "Armillary",
			Yaw = 20,
			Name = "Armillary Sphere",
			Description = "A golden star held inside three crossing brass rings on a stone base.",
			Pad = Vector2.new(-17, -27),
			PriceSeconds = 3030,
			Pieces = armillary(-17, -27),
		},
		{
			Id = "GreatDome",
			Yaw = 18,
			Name = "Great Dome",
			Description = "The main observatory: a huge silver dome on a stone drum with a telescope aimed out of the slit.",
			Pad = Vector2.new(-56, -6),
			PriceSeconds = 3485,
			Pieces = greatDome(-62, -22),
		},
		{
			Id = "Spire",
			Yaw = -8,
			Name = "Beacon Spire",
			Description = "A tall slim lattice tower with an observation deck, a silver pod and a red-tipped mast.",
			Pad = Vector2.new(62, -46),
			PriceSeconds = 4008,
			Pieces = spire(62, -46),
		},
		{
			Id = "Galaxy",
			Yaw = 14,
			Name = "Spiral Galaxy",
			Description = "The showpiece: a golden spiral galaxy with violet arms turning above a dark plinth.",
			Pad = Vector2.new(-24, -44),
			RewardMult = 1.9,
			PriceSeconds = 4609,
			Pieces = galaxy(-24, -46),
		},
	},
}

return theme
