--!strict
-- Theme of the Shiba of bay 10: Viking Longhouse (Config/DecorTypes -> Theme). 190 x 130: a great longhouse in the back left with
-- the Viking Shiba standing before its door, a fjord with a longship along the right edge, a winding walkway between the two.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: fire, runes and lanterns are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local TIMBER = C(110, 76, 50)
local DARK_TIMBER = C(72, 50, 36)
local TURF = C(86, 132, 62)
local GRASS = C(98, 150, 72)
local STONE = C(130, 132, 130)
local DARK_STONE = C(86, 90, 96)
local STEEL = C(176, 182, 192)
local IRON = C(54, 56, 62)
local RED = C(190, 48, 42)
local BONE = C(236, 228, 208)
local GOLD = C(236, 184, 56)
local BLUE = C(48, 92, 150)
local WATER = C(52, 120, 168)
local GRAVEL = C(168, 156, 130)
local SAND = C(214, 196, 150)
local FIRE = C(238, 130, 40)
local FUR = C(150, 118, 88)

local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Slate = Enum.Material.Slate
local Rock = Enum.Material.Rock
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass

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

-- Cylinder tilted away from vertical by `tilt` degrees (positive leans toward -X).
local function CyT(
	x: number,
	y: number,
	z: number,
	d: number,
	h: number,
	tilt: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90 + tilt),
	}
end

-- Cylinder lying along Z (a shield facing the road, a target): diameter d, thickness len.
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

-- One raven banner: pole, crossbar, cloth and a gold knob, standing at (x, z).
local function banner(x: number, z: number, cloth: Color3): Pieces
	return {
		Cy(x, 6.5, z, 0.7, 13, DARK_TIMBER, Wood),
		B(x, 12.2, z, 4.4, 0.4, 0.4, DARK_TIMBER, Wood),
		B(x, 8.6, z, 3.4, 6.4, 0.2, cloth, Fabric),
		Ball(x, 13.4, z, 1.2, 1.2, 1.2, GOLD, Metal),
	}
end

-- A standing stone of the rune circle.
local function runeStone(x: number, z: number, h: number): Piece
	return B(x, h / 2, z, 2.2, h, 1.4, STONE, Rock)
end

-- A fence of the horse paddock (rails as one block).
local function rail(x: number, z: number, sx: number, sz: number): Piece
	return B(x, 1.5, z, sx, 2, sz, TIMBER, Planks)
end

local BODY_BACK = -60.4

local theme: DecorTypes.Theme = {
	Key = "VikingLonghouse",
	Name = "Viking Longhouse",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-60, -26), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(52, 46),
		Vector2.new(0, 26),
		Vector2.new(-60, -2),
		Vector2.new(-6, -26),
		Vector2.new(48, -42),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-71, -26),
	AutoPad = Vector2.new(-49, -26),
	Parts = {
		{
			Id = "Ground",
			Name = "Fjord Meadow",
			Description = "A green meadow, a pebble yard before the hall and a cold blue fjord along the shore.",
			Pad = Vector2.new(-12, 57),
			PriceSeconds = 24,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, GRASS, Grass),
				B(77, 0.3, -27, 36, 0.5, 70, WATER, Plastic),
				B(58.5, 0.28, -27, 3, 0.2, 70, SAND, Enum.Material.Sand),
				B(-60, 0.25, -17, 46, 0.2, 38, GRAVEL, Enum.Material.Pebble),
			},
		},
		{
			Id = "Longhouse",
			Name = "Great Longhouse",
			Description = "The chieftain's hall: dark timber walls, a turf roof and dragon heads on the gables.",
			Pad = Vector2.new(-80, -30),
			PriceSeconds = 28,
			RewardMult = 1.3,
			Pieces = {
				B(-60, 4, BODY_BACK, 56, 8, 1.2, TIMBER, Planks),
				B(-87.4, 4, -49, 1.2, 8, 24, TIMBER, Planks),
				B(-32.6, 4, -49, 1.2, 8, 24, TIMBER, Planks),
				B(-76.5, 4, -37.6, 23, 8, 1.2, TIMBER, Planks),
				B(-43.5, 4, -37.6, 23, 8, 1.2, TIMBER, Planks),
				B(-60, 6.9, -37.6, 10, 2.2, 1.2, DARK_TIMBER, Wood),
				B(-65.2, 4.4, -37.6, 1.4, 8.8, 1.4, DARK_TIMBER, Wood),
				B(-54.8, 4.4, -37.6, 1.4, 8.8, 1.4, DARK_TIMBER, Wood),
				B(-60, 11.7, -55.2, 60, 0.8, 14.2, TURF, Grass, rot(-29.5, 0, 0)),
				B(-60, 11.7, -42.8, 60, 0.8, 14.2, TURF, Grass, rot(29.5, 0, 0)),
				B(-60, 15.2, -49, 60, 0.9, 0.9, DARK_TIMBER, Wood),
				Ball(-90.4, 16.2, -49, 2.4, 2.8, 2.4, GOLD, Metal),
				Ball(-29.6, 16.2, -49, 2.4, 2.8, 2.4, GOLD, Metal),
			},
		},
		{
			Id = "Smithy",
			Name = "Rune Forge",
			Description = "A stone forge with a tall chimney, a glowing hearth, a heavy anvil and a water barrel.",
			Pad = Vector2.new(-80, 44),
			PriceSeconds = 32,
			Pieces = {
				B(-80, 0.2, 34, 16, 0.4, 12, DARK_STONE, Slate),
				B(-80, 3.5, 28.6, 16, 7, 1.2, STONE, Rock),
				B(-87.4, 3.5, 34, 1.2, 7, 12, STONE, Rock),
				B(-84, 2, 31, 5, 4, 4, DARK_STONE, Rock),
				B(-84, 9, 30.4, 3, 10, 2.4, STONE, Rock),
				B(-77, 1.6, 34, 2.4, 3.2, 1.4, IRON, Metal),
				B(-80, 7, 34, 17.5, 0.7, 12.2, TIMBER, Planks, rot(9.5, 0, 0)),
				Cy(-87.4, 3.4, 39.4, 0.9, 6.8, DARK_TIMBER, Wood),
				Cy(-72.6, 3.4, 39.4, 0.9, 6.8, DARK_TIMBER, Wood),
				Cy(-74, 1.2, 30.6, 2, 2.4, TIMBER, Wood),
				B(-80, 1, 31, 3, 2, 2, IRON, Metal),
			},
		},
		{
			Id = "FirePit",
			Name = "Bonfire Circle",
			Description = "A ring of stones around a roaring fire and a cauldron, with log stumps to sit on.",
			Pad = Vector2.new(28, 16),
			PriceSeconds = 37,
			Pieces = merge({
				Cy(28, 0.2, 4, 13, 0.4, DARK_STONE, Slate),
				B(28, 2.2, 4, 3, 3.6, 3, FIRE, Plastic),
				B(28, 0.9, 4, 5, 1.2, 1.4, DARK_TIMBER, Wood, rot(0, 40, 0)),
				Ball(28, 4.8, 4, 3.4, 3, 3.4, IRON, Metal),
				Cy(22, 0.7, 4, 2.4, 1.4, TIMBER, Wood),
				Cy(34, 0.7, 4, 2.4, 1.4, TIMBER, Wood),
				Cy(28, 0.7, -2, 2.4, 1.4, TIMBER, Wood),
				Cy(28, 0.7, 10, 2.4, 1.4, TIMBER, Wood),
			}, {
				B(23.5, 0.6, 4, 1.4, 1.2, 1.4, STONE, Rock),
				B(32.5, 0.6, 4, 1.4, 1.2, 1.4, STONE, Rock),
				B(28, 0.6, -0.5, 1.4, 1.2, 1.4, STONE, Rock),
				B(28, 0.6, 8.5, 1.4, 1.2, 1.4, STONE, Rock),
			}),
		},
		{
			Id = "Longship",
			Name = "Dragon Longship",
			Description = "A mighty longship with a dragon prow, a red striped sail and a row of round shields.",
			Pad = Vector2.new(58, -30),
			PriceSeconds = 42,
			RewardMult = 1.4,
			Pieces = {
				B(78, 2.2, -30, 9.6, 4.4, 28, TIMBER, Planks),
				B(78, 4.8, -45.5, 4, 9.6, 3.5, TIMBER, Planks),
				B(78, 3.8, -14.5, 4, 7.6, 3.5, TIMBER, Planks),
				Ball(78, 11, -47.5, 3.2, 3.4, 3.2, RED, Wood),
				B(78, 6.6, -12.8, 0.8, 3.6, 1.2, RED, Wood),
				Cy(78, 13, -30, 1, 22, DARK_TIMBER, Wood),
				B(78, 16, -30, 10, 9, 0.5, RED, Fabric),
				B(78, 20.8, -30, 11.6, 0.7, 0.7, DARK_TIMBER, Wood),
				B(73.2, 4.3, -36, 0.4, 1.8, 1.8, BLUE, Wood),
				B(73.2, 4.3, -24, 0.4, 1.8, 1.8, BONE, Wood),
				B(82.8, 4.3, -36, 0.4, 1.8, 1.8, BONE, Wood),
				B(82.8, 4.3, -24, 0.4, 1.8, 1.8, BLUE, Wood),
				B(73.2, 4.3, -30, 0.4, 1.8, 1.8, GOLD, Wood),
				B(82.8, 4.3, -30, 0.4, 1.8, 1.8, GOLD, Wood),
			},
		},
		{
			Id = "Feast",
			Name = "Feast Table",
			Description = "A long table with roast boar and mugs, two benches and a barrel of mead.",
			Pad = Vector2.new(14, -5),
			PriceSeconds = 48,
			Pieces = {
				B(14, 2.9, -14, 18, 0.6, 4, TIMBER, Planks),
				B(8, 1.4, -14, 1, 2.8, 3.4, DARK_TIMBER, Wood),
				B(20, 1.4, -14, 1, 2.8, 3.4, DARK_TIMBER, Wood),
				B(14, 1.2, -17.8, 18, 0.6, 1.6, TIMBER, Planks),
				B(14, 1.2, -10.2, 18, 0.6, 1.6, TIMBER, Planks),
				B(9, 0.6, -17.8, 0.8, 1.2, 1.2, DARK_TIMBER, Wood),
				B(19, 0.6, -17.8, 0.8, 1.2, 1.2, DARK_TIMBER, Wood),
				B(9, 0.6, -10.2, 0.8, 1.2, 1.2, DARK_TIMBER, Wood),
				B(19, 0.6, -10.2, 0.8, 1.2, 1.2, DARK_TIMBER, Wood),
				Ball(14, 4.2, -14, 4, 1.8, 2.2, FUR, Plastic),
				Cy(10, 3.7, -13, 0.9, 1, STEEL, Metal),
				Cy(18.5, 3.7, -15, 0.9, 1, STEEL, Metal),
				Cy(25.4, 1.5, -14, 2.4, 3, TIMBER, Wood),
				Cy(25.4, 3.2, -14, 2.2, 0.4, IRON, Metal),
			},
		},
		{
			Id = "Jetty",
			Name = "Fjord Jetty",
			Description = "A wooden jetty reaching out into the fjord, with barrels, crates and a lantern post.",
			Pad = Vector2.new(54, -2),
			PriceSeconds = 55,
			Pieces = {
				B(72, 1.4, -2, 28, 0.5, 5, TIMBER, Planks),
				Cy(62, 0.9, -4.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(62, 0.9, 0.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(72, 0.9, -4.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(72, 0.9, 0.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(82, 0.9, -4.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(82, 0.9, 0.2, 0.9, 3, DARK_TIMBER, Wood),
				Cy(66, 2.75, -3, 2.2, 2.2, TIMBER, Wood),
				Cy(68.6, 2.75, -3.4, 2.2, 2.2, TIMBER, Wood),
				B(77, 2.4, -0.6, 2.4, 1.5, 2.4, DARK_TIMBER, Planks),
				B(77.6, 3.9, -0.8, 1.6, 1.4, 1.6, TIMBER, Planks),
				Cy(85, 3.5, -2, 0.6, 4, DARK_TIMBER, Wood),
				B(85, 6, -2, 1.2, 1.2, 1.2, FIRE, Plastic),
			},
		},
		{
			Id = "ShieldWall",
			Name = "Shield Wall",
			Description = "A timber wall hung with round painted shields and crowned with spears.",
			Pad = Vector2.new(-75, 60),
			PriceSeconds = 63,
			Pieces = merge({
				B(-75, 2, 55, 29, 4, 1, TIMBER, Planks),
				Cy(-89, 3.2, 55, 1.4, 6.4, DARK_TIMBER, Wood),
				Cy(-61, 3.2, 55, 1.4, 6.4, DARK_TIMBER, Wood),
				Cy(-82, 3.2, 55, 1.2, 6.4, DARK_TIMBER, Wood),
				Cy(-68, 3.2, 55, 1.2, 6.4, DARK_TIMBER, Wood),
			}, {
				Cz(-86, 2.3, 55.7, 3.2, 0.4, RED, Wood),
				Cz(-81, 2.3, 55.7, 3.2, 0.4, BONE, Wood),
				Cz(-76, 2.3, 55.7, 3.2, 0.4, BLUE, Wood),
				Cz(-71, 2.3, 55.7, 3.2, 0.4, GOLD, Wood),
				Cz(-66, 2.3, 55.7, 3.2, 0.4, RED, Wood),
				Cz(-62.5, 2.3, 55.7, 2.6, 0.4, BONE, Wood),
				Cy(-75, 5.4, 55, 0.4, 2.8, STEEL, Metal),
			}),
		},
		{
			Id = "Storehouse",
			Name = "Stilt Storehouse",
			Description = "A little food store on stilts with a turf roof, so the mice cannot get in.",
			Pad = Vector2.new(-66, 12),
			PriceSeconds = 73,
			Pieces = {
				Cy(-82.5, 1.2, 7.5, 1, 2.4, DARK_TIMBER, Wood),
				Cy(-73.5, 1.2, 7.5, 1, 2.4, DARK_TIMBER, Wood),
				Cy(-82.5, 1.2, 16.5, 1, 2.4, DARK_TIMBER, Wood),
				Cy(-73.5, 1.2, 16.5, 1, 2.4, DARK_TIMBER, Wood),
				B(-78, 5, 12, 11, 5.2, 11, TIMBER, Planks),
				B(-78, 9.9, 15.2, 12.4, 0.7, 7.6, TURF, Grass, rot(35, 0, 0)),
				B(-78, 9.9, 8.8, 12.4, 0.7, 7.6, TURF, Grass, rot(-35, 0, 0)),
				B(-78, 12.4, 12, 12.4, 0.7, 0.7, DARK_TIMBER, Wood),
				B(-78, 4.4, 17.7, 2.6, 3.6, 0.3, DARK_TIMBER, Wood),
				B(-78, 1.4, 19.8, 3, 2.8, 2.4, TIMBER, Planks, rot(30, 0, 0)),
			},
		},
		{
			Id = "Watchtower",
			Name = "Lookout Tower",
			Description = "A tall timber tower on four legs with a roofed lookout and a ladder.",
			Pad = Vector2.new(66, 42),
			PriceSeconds = 84,
			Pieces = {
				Cy(74.4, 7.2, 38.4, 1.2, 14.4, DARK_TIMBER, Wood),
				Cy(81.6, 7.2, 38.4, 1.2, 14.4, DARK_TIMBER, Wood),
				Cy(74.4, 7.2, 45.6, 1.2, 14.4, DARK_TIMBER, Wood),
				Cy(81.6, 7.2, 45.6, 1.2, 14.4, DARK_TIMBER, Wood),
				B(78, 6, 45.6, 10, 0.5, 0.5, TIMBER, Wood, rot(0, 0, 36)),
				B(78, 6, 45.6, 10, 0.5, 0.5, TIMBER, Wood, rot(0, 0, -36)),
				B(78, 14.6, 42, 10.4, 0.8, 10.4, TIMBER, Planks),
				B(78, 18, 42, 8, 6, 8, TIMBER, Planks),
				B(73.6, 20.4, 42, 7.6, 0.8, 10, TURF, Grass, rot(0, 0, 38)),
				B(82.4, 20.4, 42, 7.6, 0.8, 10, TURF, Grass, rot(0, 0, -38)),
				B(78, 24, 42, 0.8, 0.8, 10, DARK_TIMBER, Wood),
				B(78, 7.5, 47.8, 1.6, 15, 0.5, DARK_TIMBER, Wood),
				B(78, 18.4, 46.2, 3, 2, 0.3, DARK_TIMBER, Wood),
			},
		},
		{
			Id = "FishRacks",
			Name = "Fish Drying Racks",
			Description = "Two racks of silver fish drying in the wind and an upturned rowing boat.",
			Pad = Vector2.new(62, 22),
			PriceSeconds = 97,
			Pieces = {
				Cy(64, 3, 18, 0.7, 6, DARK_TIMBER, Wood),
				Cy(80, 3, 18, 0.7, 6, DARK_TIMBER, Wood),
				B(72, 5.8, 18, 17, 0.5, 0.5, TIMBER, Wood),
				B(72, 4.4, 18, 15, 2, 0.3, STEEL, Plastic),
				Cy(64, 3, 26, 0.7, 6, DARK_TIMBER, Wood),
				Cy(80, 3, 26, 0.7, 6, DARK_TIMBER, Wood),
				B(72, 5.8, 26, 17, 0.5, 0.5, TIMBER, Wood),
				B(72, 4.4, 26, 15, 2, 0.3, STEEL, Plastic),
				B(72, 1.1, 22, 10, 2.2, 3.8, DARK_TIMBER, Planks),
				B(72, 2.5, 22, 8, 0.6, 2.4, TIMBER, Planks),
				Cy(83, 1, 22, 2, 2, TIMBER, Wood),
			},
		},
		{
			Id = "AxeRange",
			Name = "Axe Throwing Range",
			Description = "Three round targets on posts and a line to throw from. Bonk, thunk, bullseye!",
			Pad = Vector2.new(-40, 57),
			PriceSeconds = 111,
			Pieces = {
				B(-48, 2.4, 46, 0.8, 4.8, 0.8, DARK_TIMBER, Wood),
				B(-40, 2.4, 46, 0.8, 4.8, 0.8, DARK_TIMBER, Wood),
				B(-32, 2.4, 46, 0.8, 4.8, 0.8, DARK_TIMBER, Wood),
				Cz(-48, 5.2, 46.6, 4.6, 0.6, BONE, Wood),
				Cz(-40, 5.2, 46.6, 4.6, 0.6, BONE, Wood),
				Cz(-32, 5.2, 46.6, 4.6, 0.6, BONE, Wood),
				Cz(-48, 5.2, 47, 1.8, 0.4, RED, Wood),
				Cz(-40, 5.2, 47, 1.8, 0.4, RED, Wood),
				Cz(-32, 5.2, 47, 1.8, 0.4, RED, Wood),
				B(-40, 0.15, 53, 22, 0.3, 10, GRAVEL, Enum.Material.Pebble),
				B(-40, 0.35, 57.6, 20, 0.3, 0.8, RED, Wood),
				Cy(-27, 0.9, 54, 2.4, 1.8, TIMBER, Wood),
				B(-27, 2.2, 54, 0.4, 1.6, 0.5, STEEL, Metal, rot(0, 0, 30)),
			},
		},
		{
			Id = "RuneStones",
			Name = "Rune Stone Circle",
			Description = "Seven tall standing stones carved with runes around a flat altar stone.",
			Pad = Vector2.new(-19, -37),
			PriceSeconds = 128,
			RewardMult = 1.3,
			Pieces = {
				Cy(-19, 0.2, -47, 17, 0.4, DARK_STONE, Slate),
				B(-19, 4.5, -47, 3, 9, 1.8, STONE, Rock),
				B(-19, 9.4, -47, 1.6, 0.8, 1.9, RED, Plastic),
				runeStone(-25.5, -47, 5),
				runeStone(-22.2, -52.4, 6.4),
				runeStone(-15.8, -52.4, 5.4),
				runeStone(-12.5, -47, 6),
				runeStone(-15.8, -41.6, 4.8),
				runeStone(-22.2, -41.6, 5.8),
				B(-19, 0.5, -44, 3, 1, 1.6, DARK_STONE, Rock),
			},
		},
		{
			Id = "Banners",
			Name = "Raven Banners",
			Description = "Four tall banners with the raven of the clan flapping before the longhouse.",
			Pad = Vector2.new(-36, -30),
			PriceSeconds = 147,
			Pieces = merge(
				banner(-84, -34.5, RED),
				banner(-68, -34.5, BLUE),
				banner(-52, -34.5, BLUE),
				banner(-36, -34.5, RED)
			),
		},
		{
			Id = "Sauna",
			Name = "Turf Sauna",
			Description = "A log sauna hut with a turf roof, a stone chimney and clouds of steam.",
			Pad = Vector2.new(47, 10),
			PriceSeconds = 169,
			Pieces = {
				B(47, 0.25, 22, 13, 0.5, 11, DARK_STONE, Slate),
				B(47, 3, 22, 10, 5.4, 8, TIMBER, Wood),
				B(47, 2.4, 26.1, 2.4, 4.4, 0.3, DARK_TIMBER, Wood),
				B(47, 7.4, 24.2, 11.4, 0.7, 5.8, TURF, Grass, rot(30, 0, 0)),
				B(47, 7.4, 19.8, 11.4, 0.7, 5.8, TURF, Grass, rot(-30, 0, 0)),
				B(47, 9.7, 22, 11.4, 0.7, 0.7, DARK_TIMBER, Wood),
				Cy(51.5, 6.5, 20, 1.8, 11, STONE, Rock),
				Ball(51.5, 13.4, 20, 2.6, 2, 2.6, BONE, Plastic),
				Ball(52.6, 15.6, 19.6, 3.4, 2.4, 3.4, BONE, Plastic),
				B(47, 1, 27.6, 7, 0.8, 1.4, TIMBER, Planks),
				Cy(43, 1.1, 27.6, 1.6, 1.6, TIMBER, Wood),
			},
		},
		{
			Id = "Throne",
			Name = "Chieftain Throne",
			Description = "A carved wooden throne with horns on a stone dais, guarded by two fire bowls.",
			Pad = Vector2.new(-44, 34),
			PriceSeconds = 195,
			RewardMult = 1.3,
			Pieces = {
				B(-44, 1.2, 24, 10, 2.4, 10, STONE, Rock),
				B(-44, 0.5, 29.8, 8, 1, 2, DARK_STONE, Rock),
				B(-44, 3.5, 23, 3.8, 2.2, 3.8, TIMBER, Wood),
				B(-44, 7, 21.6, 3.8, 6.4, 1, DARK_TIMBER, Wood),
				B(-46.2, 4.6, 23, 0.7, 1.4, 3.6, DARK_TIMBER, Wood),
				B(-41.8, 4.6, 23, 0.7, 1.4, 3.6, DARK_TIMBER, Wood),
				CyT(-45.2, 11, 21.6, 0.8, 3.4, 20, BONE, Wood),
				CyT(-42.8, 11, 21.6, 0.8, 3.4, -20, BONE, Wood),
				Cy(-48.2, 3.4, 20.2, 2.6, 2, IRON, Metal),
				Cy(-39.8, 3.4, 20.2, 2.6, 2, IRON, Metal),
				B(-48.2, 4.8, 20.2, 1.6, 1, 1.6, FIRE, Plastic),
				B(-39.8, 4.8, 20.2, 1.6, 1, 1.6, FIRE, Plastic),
				B(-44, 2.65, 26.6, 5, 0.3, 3.4, FUR, Fabric),
			},
		},
		{
			Id = "Totem",
			Name = "Raven Totem",
			Description = "A carved totem pole of faces with a big black raven on top.",
			Pad = Vector2.new(10, 37),
			PriceSeconds = 224,
			Pieces = {
				B(10, 0.8, 46, 5, 1.6, 5, STONE, Rock),
				B(10, 3.6, 46, 2.6, 4, 2.6, TIMBER, Wood),
				B(10, 7.4, 46, 2.8, 3.6, 2.8, RED, Wood),
				B(10, 11, 46, 2.8, 3.6, 2.8, BLUE, Wood),
				B(10, 14.8, 46, 2.6, 4, 2.6, TIMBER, Wood),
				Ball(10, 18.2, 46, 3.2, 3, 4.4, IRON, Plastic),
				Ball(10, 19.8, 47.6, 1.8, 1.8, 1.8, IRON, Plastic),
				B(10, 19.4, 49, 0.7, 0.7, 1.6, GOLD, Plastic),
				B(10, 18.8, 46, 9, 0.6, 2.4, IRON, Plastic),
				B(10, 17.6, 43.6, 1.6, 1.4, 2.4, IRON, Plastic),
			},
		},
		{
			Id = "Stables",
			Name = "Horse Paddock",
			Description = "A fenced paddock with a stable shed, hay bales and a sturdy shaggy pony.",
			Pad = Vector2.new(62, 48),
			PriceSeconds = 257,
			Pieces = {
				rail(76, 51.3, 28, 0.6),
				rail(62.3, 56.5, 0.6, 10.4),
				rail(89.7, 56.5, 0.6, 10.4),
				rail(66, 61.7, 7.6, 0.6),
				rail(83, 61.7, 13.6, 0.6),
				B(84.6, 3, 54, 8, 6, 5, TIMBER, Planks),
				B(84.6, 7.1, 54, 9.4, 0.8, 6.4, TURF, Grass, rot(0, 0, 8)),
				B(79, 0.9, 58.6, 2.6, 1.8, 1.6, SAND, Grass),
				B(71, 0.5, 52.8, 4, 1, 1.2, DARK_TIMBER, Wood),
				B(72, 3, 57, 4.6, 2.2, 1.6, FUR, Fabric),
				B(70.4, 1.1, 57, 0.8, 2.2, 1.4, DARK_TIMBER, Wood),
				B(73.6, 1.1, 57, 0.8, 2.2, 1.4, DARK_TIMBER, Wood),
				B(69.4, 4.2, 57, 1.6, 2.6, 1.2, FUR, Fabric, rot(0, 0, 25)),
				B(68.2, 5.2, 57, 1.8, 1.2, 1.2, FUR, Fabric),
			},
		},
		{
			Id = "Hoard",
			Name = "Dragon Hoard",
			Description = "A rocky cave full of gold coins, a treasure chest and shiny crowns.",
			Pad = Vector2.new(-58, 50),
			PriceSeconds = 296,
			Pieces = {
				B(-58, 3, 37.5, 15, 6, 4, DARK_STONE, Rock),
				B(-64.5, 2.4, 41, 4, 4.8, 6, STONE, Rock),
				B(-51.5, 2.4, 41, 4, 4.8, 6, STONE, Rock),
				B(-58, 5.6, 41, 9.6, 1.4, 5, STONE, Rock),
				B(-58, 1.1, 40.4, 3.6, 2.2, 2.4, TIMBER, Wood),
				B(-58, 2.5, 40.4, 3.8, 0.8, 2.6, DARK_TIMBER, Wood),
				Ball(-61.8, 1, 42.6, 3.6, 2, 3.6, GOLD, Metal),
				Ball(-54.4, 1, 42.8, 4, 2.2, 3.6, GOLD, Metal),
				Ball(-58, 0.9, 43.4, 3, 1.8, 2.4, GOLD, Metal),
				B(-56.6, 3.4, 41, 1.4, 0.9, 1.4, GOLD, Metal),
				B(-60, 3.4, 41, 1.2, 0.8, 1.2, RED, Plastic),
				Cy(-66.4, 4.8, 43.8, 0.4, 3, STEEL, Metal),
			},
		},
		{
			Id = "Helmet",
			Name = "Giant Horned Helmet",
			Description = "The showpiece: a giant horned helmet of steel and gold on a stone plinth.",
			Pad = Vector2.new(-2, -34),
			PriceSeconds = 344,
			RewardMult = 2,
			Pieces = {
				B(-2, 1, -45, 14, 2, 14, STONE, Rock),
				B(-2, 2.6, -45, 10.4, 1.2, 10.4, DARK_STONE, Rock),
				Ball(-2, 10.2, -45, 12, 11, 12, STEEL, Metal),
				Cy(-2, 6.6, -45, 12.8, 1.2, GOLD, Metal),
				B(-2, 8, -39.4, 1.4, 6, 0.8, STEEL, Metal),
				B(-2, 12.2, -45, 1.4, 1.2, 12.4, GOLD, Metal),
				CyT(-8, 14.6, -45, 2.2, 8.4, 25, BONE, Wood),
				CyT(4, 14.6, -45, 2.2, 8.4, -25, BONE, Wood),
				Ball(-10.2, 19.4, -45, 1.8, 1.8, 1.8, BONE, Wood),
				Ball(6.2, 19.4, -45, 1.8, 1.8, 1.8, BONE, Wood),
			},
		},
	},
}

return theme
