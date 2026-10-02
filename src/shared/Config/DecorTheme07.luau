--!strict
-- Theme of the Shiba of bay 7: Wild West Saloon (Config/DecorTypes -> Theme). 190 x 130 frontier town, the Cowboy Shiba stands
-- on the porch of the big saloon at the back right, the walkway lassos from the town gate past the horses to the saloon front
-- and on through camp and mine country. Stage frame: +X right, -Z deeper, +Z toward the road.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local SAND = C(214, 178, 120)
local SAND2 = C(198, 158, 102)
local PLANK = C(184, 138, 88)
local WOOD = C(140, 96, 60)
local DWOOD = C(92, 62, 40)
local CREAM = C(238, 222, 186)
local RED = C(172, 54, 42)
local BRICK = C(150, 70, 52)
local STONE = C(176, 160, 140)
local SANDSTONE = C(204, 176, 134)
local ROCK = C(190, 98, 62)
local ROCK2 = C(214, 128, 80)
local ROCKD = C(150, 72, 48)
local IRON = C(66, 68, 76)
local STEEL = C(150, 154, 164)
local GOLD = C(240, 190, 50)
local GREEN = C(86, 140, 72)
local BLACK = C(34, 30, 32)
local HORSE1 = C(130, 82, 48)
local HORSE2 = C(236, 230, 220)
local ORANGE = C(236, 120, 40)
local YELLOW = C(250, 210, 70)

local Sand = Enum.Material.Sand
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Brick = Enum.Material.Brick
local Sandstone = Enum.Material.Sandstone
local Cobble = Enum.Material.Cobblestone
local Metal = Enum.Material.Metal
local Fabric = Enum.Material.Fabric
local Rock = Enum.Material.Rock
local Plastic = Enum.Material.SmoothPlastic

-- Block standing on y0 (its bottom), centred on x, z.
local function B(
	x: number,
	y0: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y0 + sy / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Block,
	}
end

-- Standing cylinder (axis up) from y0: height h, diameter d.
local function Cy(x: number, y0: number, z: number, h: number, d: number, color: Color3, material: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y0 + h / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along X (a log, a train axle), centred at y: diameter d, length len.
local function Cx(
	x: number,
	y: number,
	z: number,
	d: number,
	len: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Cylinder lying along Z (a boiler, a wheel): diameter d, length len.
local function Cz(
	x: number,
	y: number,
	z: number,
	d: number,
	len: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

local function Ball(x: number, y: number, z: number, d: number, color: Color3, material: Enum.Material): Piece
	return {
		Size = Vector3.new(d, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Ball,
	}
end

local function merge(...: { Piece }): { Piece }
	local out: { Piece } = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

-- A horse standing at x = cx facing dir (1 = +X, -1 = -X) on the line z: body, leg pairs, neck and head (5 pieces).
local function horse(cx: number, z: number, dir: number, color: Color3): { Piece }
	return {
		B(cx, 2.4, z, 6, 2.4, 2.2, color, Plastic),
		B(cx + dir * 2.2, 0, z, 1.1, 2.4, 1.6, color, Plastic),
		B(cx - dir * 2.2, 0, z, 1.1, 2.4, 1.6, color, Plastic),
		B(cx + dir * 3.3, 4.4, z, 1.4, 2.6, 1.4, color, Plastic),
		B(cx + dir * 4.6, 6, z, 2.4, 1.2, 1.2, color, Plastic),
	}
end

-- A saguaro cactus: trunk of height h and two arms (5 pieces).
local function saguaro(x: number, z: number, h: number): { Piece }
	return {
		Cy(x, 0, z, h, 2.2, GREEN, Plastic),
		B(x - 2.4, h * 0.42, z, 3.4, 1.2, 1.2, GREEN, Plastic),
		Cy(x - 3.4, h * 0.42, z, 4.6, 1.2, GREEN, Plastic),
		B(x + 2.4, h * 0.6, z, 3.4, 1.2, 1.2, GREEN, Plastic),
		Cy(x + 3.4, h * 0.6, z, 3.8, 1.2, GREEN, Plastic),
	}
end

local theme: DecorTypes.Theme = {
	Key = "WesternSaloon",
	Name = "Wild West Saloon",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(52, -14), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(0, 50),
		Vector2.new(44, 40),
		Vector2.new(50, 12),
		Vector2.new(12, -4),
		Vector2.new(-30, -20),
		Vector2.new(-34, -46),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(63, -13),
	AutoPad = Vector2.new(41, -13),
	Parts = {
		{
			Id = "Floor",
			Name = "Dusty Main Street",
			Description = "Sun-baked desert dust over the whole town with wooden boardwalks in front of the buildings.",
			Pad = Vector2.new(30, 56),
			PriceSeconds = 13,
			Pieces = {
				B(0, 0, 0, 188, 0.06, 128, SAND, Sand),
				B(-64, 0, 54, 30, 0.3, 4, PLANK, Planks),
				B(-63, 0, 4, 28, 0.3, 4, PLANK, Planks),
				B(52, 0, -5, 64, 0.3, 5, PLANK, Planks),
				B(20, 0.06, 30, 40, 0.03, 26, SAND2, Sand),
				B(-30, 0.06, -40, 50, 0.03, 30, SAND2, Sand),
			},
		},
		{
			Id = "Saloon",
			Name = "Rusty Spur Saloon",
			Description = "Two floors of weathered planks with swinging doors, a balcony and a tall false front. The Cowboy Shiba guards the porch.",
			Pad = Vector2.new(72, -16),
			RewardMult = 2,
			PriceSeconds = 20,
			Pieces = {
				B(52, 0, -19.5, 60, 0.5, 23, PLANK, Planks),
				B(52, 0.5, -46, 56, 9.5, 32, WOOD, Planks),
				B(52, 10, -46, 54, 8, 32, WOOD, Planks),
				B(52, 18.7, -30, 54, 8, 1.2, PLANK, Planks),
				B(52, 9.8, -27, 52, 0.4, 6, PLANK, Planks),
				B(52, 10.2, -24.2, 52, 1.6, 0.4, DWOOD, Wood),
				Cy(28, 0.5, -25.5, 9.5, 0.8, DWOOD, Wood),
				Cy(40, 0.5, -25.5, 9.5, 0.8, DWOOD, Wood),
				Cy(64, 0.5, -25.5, 9.5, 0.8, DWOOD, Wood),
				Cy(76, 0.5, -25.5, 9.5, 0.8, DWOOD, Wood),
				B(52, 18, -47, 58, 0.7, 33, DWOOD, Planks),
				B(68, 18.7, -56, 4, 5, 4, BRICK, Brick),
				B(52, 19.5, -29.2, 40, 5.5, 0.4, CREAM, Plastic),
			},
		},
		{
			Id = "Gate",
			Name = "Bonk Town Gate",
			Description = "A tall log gate over the entrance with a hanging BONK TOWN sign and a longhorn skull on top.",
			Pad = Vector2.new(16, 57),
			PriceSeconds = 33,
			Pieces = {
				B(-10.5, 0, 58, 3.6, 0.8, 3, STONE, Cobble),
				B(10.5, 0, 58, 3.6, 0.8, 3, STONE, Cobble),
				B(-10.5, 0.8, 58, 1.6, 15.2, 1.6, WOOD, Wood),
				B(10.5, 0.8, 58, 1.6, 15.2, 1.6, WOOD, Wood),
				B(0, 16, 58, 25, 1.6, 1.8, DWOOD, Wood),
				B(0, 10, 58, 19, 6, 0.6, PLANK, Planks),
				Ball(0, 18.4, 58, 2.8, CREAM, Plastic),
				B(0, 18.1, 58, 7, 0.6, 0.6, CREAM, Plastic),
			},
		},
		{
			Id = "Jail",
			Name = "Sheriff's Office",
			Description = "A plank office with a stone jail cell on the side, a tin star and a JAIL board.",
			Pad = Vector2.new(-64, 57.5),
			PriceSeconds = 46,
			Pieces = {
				B(-68, 0, 45, 16, 8, 14, PLANK, Planks),
				B(-55, 0, 45, 10, 7, 12, STONE, Cobble),
				B(-68, 8, 45, 17.5, 0.6, 15.5, DWOOD, Planks),
				B(-55, 7, 45, 11, 0.6, 13, DWOOD, Planks),
				B(-68, 8.6, 51.6, 16, 3.4, 0.8, PLANK, Planks),
				B(-72, 8.6, 41, 2, 3.5, 2, BRICK, Brick),
				B(-68, 9.2, 52.2, 10, 2.4, 0.4, CREAM, Plastic),
			},
		},
		{
			Id = "Horses",
			Name = "Hitching Rail",
			Description = "Two saddle horses, one brown and one white, tied up at a rail with a water trough.",
			Pad = Vector2.new(74, 13),
			PriceSeconds = 65,
			Pieces = merge(horse(68, 8.6, 1, HORSE1), horse(81, 8.6, -1, HORSE2), {
				B(62, 0, 5, 0.7, 3.4, 0.7, DWOOD, Wood),
				B(75, 0, 5, 0.7, 3.4, 0.7, DWOOD, Wood),
				B(88, 0, 5, 0.7, 3.4, 0.7, DWOOD, Wood),
				B(75, 2.7, 5, 27, 0.5, 0.5, WOOD, Wood),
				B(75, 0, 2.2, 6, 1.4, 1.6, WOOD, Planks),
			}),
		},
		{
			Id = "Well",
			Name = "Town Well",
			Description = "A round stone well with a little shingle roof, a crank and a wooden bucket.",
			Pad = Vector2.new(-8, 34),
			PriceSeconds = 85,
			Pieces = {
				Cy(-8, 0, 26, 3.4, 7.2, STONE, Cobble),
				B(-11.2, 3.4, 26, 0.8, 6.8, 0.8, DWOOD, Wood),
				B(-4.8, 3.4, 26, 0.8, 6.8, 0.8, DWOOD, Wood),
				B(-8, 8.4, 26, 6.4, 0.5, 0.5, WOOD, Wood),
				B(-8, 10.2, 26, 9.6, 0.6, 6.8, DWOOD, Planks),
				B(-8, 10.8, 26, 3, 1.4, 5, DWOOD, Planks),
				B(-6.5, 4.6, 26, 1.2, 1.2, 1.2, WOOD, Wood),
			},
		},
		{
			Id = "Wagon",
			Name = "Covered Wagon",
			Description = "A canvas-topped prairie wagon with big wooden wheels, a driver's seat and a pair of barrels.",
			Pad = Vector2.new(-48, 29),
			PriceSeconds = 110,
			Pieces = {
				B(-48, 1.8, 19, 16, 0.8, 7.4, WOOD, Planks),
				Cz(-52, 2.3, 15, 4.6, 0.7, DWOOD, Wood),
				Cz(-44, 2.3, 15, 4.6, 0.7, DWOOD, Wood),
				Cz(-52, 2.3, 23, 4.6, 0.7, DWOOD, Wood),
				Cz(-44, 2.3, 23, 4.6, 0.7, DWOOD, Wood),
				B(-47, 2.6, 19, 14, 4, 7, CREAM, Fabric),
				B(-47, 6.6, 19, 14, 1.6, 5.2, CREAM, Fabric),
				B(-47, 8.2, 19, 14, 0.7, 3, CREAM, Fabric),
				B(-59, 1.2, 19, 6, 0.5, 0.6, DWOOD, Wood),
				B(-55.6, 2.6, 19, 2.4, 2.2, 6, WOOD, Planks),
				Cy(-41, 2.6, 17, 2.6, 2, DWOOD, Wood),
				Cy(-41, 2.6, 21, 2.6, 2, DWOOD, Wood),
			},
		},
		{
			Id = "Bank",
			Name = "Gold Bank",
			Description = "A sandstone bank with four columns, a golden vault door and a BANK sign over the portico.",
			Pad = Vector2.new(-63, 10.5),
			RewardMult = 1.5,
			PriceSeconds = 137,
			Pieces = {
				B(-63, 0, -5, 22, 12, 14, SANDSTONE, Sandstone),
				B(-63, 0, 3.6, 24, 0.5, 3.2, STONE, Cobble),
				Cy(-72, 0.5, 3.6, 9.5, 1.4, CREAM, Sandstone),
				Cy(-66, 0.5, 3.6, 9.5, 1.4, CREAM, Sandstone),
				Cy(-60, 0.5, 3.6, 9.5, 1.4, CREAM, Sandstone),
				Cy(-54, 0.5, 3.6, 9.5, 1.4, CREAM, Sandstone),
				B(-63, 10, 3.6, 25, 2.6, 3.6, CREAM, Sandstone),
				B(-63, 12.6, 3.6, 20, 1.2, 3, CREAM, Sandstone),
				B(-63, 13.8, 3.6, 12, 1.2, 2.6, CREAM, Sandstone),
				B(-63, 12, -5, 24, 0.6, 15, DWOOD, Planks),
			},
		},
		{
			Id = "Cacti",
			Name = "Cactus Garden",
			Description = "Two tall saguaros with raised arms, round barrel cacti and a few sun-warmed rocks.",
			Pad = Vector2.new(75, 26),
			PriceSeconds = 170,
			Pieces = merge(saguaro(65, 22, 15), saguaro(86, 27, 12), {
				Ball(76, 1.6, 20, 3.2, GREEN, Plastic),
				Ball(91, 1.6, 31, 3.2, GREEN, Plastic),
				B(72, 0, 28, 4, 2, 3, ROCK, Rock),
				B(70, 0, 26.8, 2.4, 1.2, 2.2, ROCKD, Rock),
			}),
		},
		{
			Id = "WaterTower",
			Name = "Water Tower",
			Description = "A tall wooden water tank on four legs with braces, a ladder and a pointed roof.",
			Pad = Vector2.new(12, -31),
			RewardMult = 1.25,
			PriceSeconds = 202,
			Pieces = {
				Cy(12, 14, -42, 7, 9, WOOD, Wood),
				B(12, 13.6, -42, 10, 0.4, 10, DWOOD, Planks),
				B(8.4, 0, -45.6, 1, 14, 1, DWOOD, Wood),
				B(15.6, 0, -45.6, 1, 14, 1, DWOOD, Wood),
				B(8.4, 0, -38.4, 1, 14, 1, DWOOD, Wood),
				B(15.6, 0, -38.4, 1, 14, 1, DWOOD, Wood),
				B(12, 5, -45.6, 7.2, 0.4, 0.4, WOOD, Wood),
				B(12, 5, -38.4, 7.2, 0.4, 0.4, WOOD, Wood),
				B(8.4, 9, -42, 0.4, 0.4, 7.2, WOOD, Wood),
				B(15.6, 9, -42, 0.4, 0.4, 7.2, WOOD, Wood),
				Cy(12, 21, -42, 0.8, 10.4, DWOOD, Planks),
				Cy(12, 21.8, -42, 1.2, 6, DWOOD, Planks),
				B(12, 0, -36.6, 1.6, 13.6, 0.3, WOOD, Wood),
			},
		},
		{
			Id = "Windmill",
			Name = "Wind Pump",
			Description = "A steel lattice windmill with a big blade wheel and tail vane, pumping water into a trough.",
			Pad = Vector2.new(-18, 47),
			PriceSeconds = 240,
			Pieces = {
				B(-24.4, 0, 37.6, 0.8, 16, 0.8, STEEL, Metal),
				B(-19.6, 0, 37.6, 0.8, 16, 0.8, STEEL, Metal),
				B(-24.4, 0, 42.4, 0.8, 16, 0.8, STEEL, Metal),
				B(-19.6, 0, 42.4, 0.8, 16, 0.8, STEEL, Metal),
				B(-22, 5, 37.6, 4.8, 0.4, 0.4, STEEL, Metal),
				B(-22, 5, 42.4, 4.8, 0.4, 0.4, STEEL, Metal),
				B(-24.4, 9, 40, 0.4, 0.4, 4.8, STEEL, Metal),
				B(-19.6, 9, 40, 0.4, 0.4, 4.8, STEEL, Metal),
				B(-22, 16, 40, 5, 0.5, 5, DWOOD, Planks),
				B(-22, 16.5, 40, 2.4, 2.4, 5, IRON, Metal),
				B(-22, 14.6, 43.6, 1, 9.8, 0.5, STEEL, Metal),
				B(-22, 19.2, 43.6, 9.8, 0.6, 0.5, STEEL, Metal),
				B(-22, 19.3, 37.4, 0.5, 0.5, 5, STEEL, Metal),
				B(-22, 18.4, 34.5, 0.4, 3, 3.5, RED, Plastic),
				B(-15.5, 0, 40, 5, 1.6, 2.6, WOOD, Planks),
			},
		},
		{
			Id = "Mine",
			Name = "Gold Mine",
			Description = "A rocky hillside with a timber-framed mine shaft, an ore cart on rails and a pile of gold nuggets.",
			Pad = Vector2.new(-73, -30),
			RewardMult = 1.3,
			PriceSeconds = 280,
			Pieces = {
				B(-73, 0, -52, 34, 8, 20, ROCK, Rock),
				B(-76, 8, -54, 24, 6, 15, ROCK2, Rock),
				B(-82, 14, -55, 12, 4, 11, ROCK, Rock),
				B(-60.5, 8, -50, 7, 4, 8, ROCKD, Rock),
				B(-77.5, 0, -41.6, 1.2, 8.4, 1.2, DWOOD, Wood),
				B(-68.5, 0, -41.6, 1.2, 8.4, 1.2, DWOOD, Wood),
				B(-73, 8.4, -41.6, 11, 1.2, 1.2, DWOOD, Wood),
				B(-73, 10, -41.4, 8, 2, 0.5, PLANK, Planks),
				B(-73, 0, -37.8, 3.4, 0.2, 7, DWOOD, Wood),
				B(-73, 0.6, -36.4, 3.2, 2, 2.4, IRON, Metal),
				B(-66.5, 0, -39, 3.6, 1.6, 3, ROCKD, Rock),
				Ball(-66.5, 1.8, -39, 1.4, GOLD, Metal),
			},
		},
		{
			Id = "Train",
			Name = "Steam Locomotive",
			Description = "A black steam engine with a tall funnel, a coal tender and a red freight car on a track along the town edge.",
			Pad = Vector2.new(-77, 12),
			RewardMult = 1.25,
			PriceSeconds = 325,
			Pieces = {
				B(-89, 0, -4, 10, 0.5, 52, DWOOD, Wood),
				B(-89, 0.9, 10, 7, 1.4, 24, IRON, Metal),
				Cz(-89, 5.6, 13, 5.4, 15, IRON, Metal),
				B(-89, 2.3, 3.2, 7.4, 8.6, 7.2, RED, Planks),
				B(-89, 10.9, 3.2, 8.2, 0.5, 8.2, IRON, Metal),
				Cy(-89, 8.2, 18.5, 5, 1.6, IRON, Metal),
				B(-89, 0.5, 22.7, 6.4, 1.6, 1.4, STEEL, Metal),
				Cx(-89, 1.9, 8.5, 3.8, 7.6, STEEL, Metal),
				Cx(-89, 1.9, 13.5, 3.8, 7.6, STEEL, Metal),
				Cx(-89, 1.3, 19.5, 2.6, 7.4, STEEL, Metal),
				B(-89, 0.9, -8, 7, 3.9, 12, IRON, Metal),
				B(-89, 4.8, -8, 6, 1.4, 10, BLACK, Rock),
				B(-89, 0.9, -22, 7, 6.5, 12, RED, Planks),
				B(-89, 7.4, -22, 7.6, 0.5, 12.6, DWOOD, Planks),
			},
		},
		{
			Id = "Camp",
			Name = "Cowboy Camp",
			Description = "A teepee, a crackling campfire between log seats, a crate of supplies and a rolled-up bed.",
			Pad = Vector2.new(-52, -17),
			PriceSeconds = 370,
			Pieces = {
				B(-61, 0, -30, 6.4, 2.4, 6.4, CREAM, Fabric),
				B(-61, 2.4, -30, 4.8, 2.4, 4.8, CREAM, Fabric),
				B(-61, 4.8, -30, 3.2, 2.4, 3.2, CREAM, Fabric),
				B(-61, 7.2, -30, 1.6, 2.4, 1.6, CREAM, Fabric),
				Cy(-53, 0, -27, 0.7, 4.2, STONE, Cobble),
				B(-53, 0.7, -27, 1.4, 1.6, 1.4, ORANGE, Plastic),
				B(-53, 2.3, -27, 0.8, 1.2, 0.8, YELLOW, Plastic),
				Cx(-53, 0.8, -23.2, 1.4, 4.4, DWOOD, Wood),
				Cz(-56.8, 0.8, -27, 1.4, 4.4, DWOOD, Wood),
				Cx(-53, 0.8, -30.8, 1.4, 4.4, DWOOD, Wood),
				B(-48, 0, -30, 2.4, 2, 2.4, WOOD, Planks),
				Cz(-58, 0.7, -23.5, 1.4, 3.4, RED, Fabric),
			},
		},
		{
			Id = "Mesa",
			Name = "Red Rock Mesa",
			Description = "A huge layered red-rock butte with a giant cowboy hat balanced on its flat top.",
			Pad = Vector2.new(79, 32),
			PriceSeconds = 420,
			Pieces = {
				B(79, 0, 50, 26, 9, 24, ROCK, Rock),
				B(78, 9, 50, 20, 8, 18, ROCK2, Rock),
				B(78, 17, 50, 16, 4, 14, ROCK, Rock),
				B(78, 21, 50, 12, 2, 10, ROCK2, Rock),
				B(62.5, 0, 44, 7, 13, 8, ROCKD, Rock),
				Cy(78, 23, 50, 0.8, 10, DWOOD, Fabric),
				Cy(78, 23.8, 50, 3, 5.6, WOOD, Fabric),
				B(72, 0, 36, 4, 3, 3.6, ROCKD, Rock),
				B(86, 0, 35.4, 5, 2.4, 3.4, ROCK, Rock),
			},
		},
	},
}

return theme
