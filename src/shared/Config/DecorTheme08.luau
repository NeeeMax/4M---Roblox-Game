--!strict
-- Theme of the Shiba of bay 8: Pirate Ship (Config/DecorTypes -> Theme). 190 x 130 pirate cove: a lagoon on the left with a full
-- galleon moored along the shore, the Shiba at the foot of its gangplank, a tavern at the back, a treasure beach, a camp and
-- palms on the right and a winding walkway between them all. Stage frame: +X right, -Z deeper, +Z toward the road.
-- No glow: lanterns, fire and gold are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local SAND = C(235, 215, 160)
local WET = C(205, 185, 130)
local DIRT = C(190, 165, 115)
local SEA = C(40, 130, 200)
local GRASS = C(90, 150, 70)
local HULL = C(110, 70, 40)
local DARK = C(80, 50, 30)
local BOARD = C(70, 45, 30)
local DECK = C(160, 110, 60)
local CREAM = C(240, 230, 200)
local RED = C(170, 40, 40)
local GOLD = C(255, 200, 40)
local IRON = C(30, 30, 35)
local STONE = C(120, 120, 130)
local BONE = C(235, 230, 215)
local TRUNK = C(150, 110, 70)
local LEAF = C(60, 150, 70)
local ORANGE = C(230, 120, 40)
local PURPLE = C(120, 55, 140)
local YELLOW = C(255, 225, 90)

local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks
local Plastic = Enum.Material.SmoothPlastic
local Metal = Enum.Material.Metal
local Fabric = Enum.Material.Fabric
local Rock = Enum.Material.Slate
local Sand = Enum.Material.Sand
local Grass = Enum.Material.Grass
local Glass = Enum.Material.Glass

-- Block standing on y0 (bottom), centred at (x, z).
local function box(
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
	}
end

-- Block turned around the vertical axis (yaw) or leaning (roll), centred at (x, y, z).
local function tilted(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material,
	yaw: number,
	roll: number
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
		Rotation = Vector3.new(0, yaw, roll),
	}
end

-- Standing cylinder (pole, barrel) on y0: height h, diameter d.
local function pole(
	x: number,
	y0: number,
	z: number,
	h: number,
	d: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y0 + h / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along X (a cannon barrel, a half round lid): diameter d, length len, centre y.
local function lying(
	x: number,
	y: number,
	z: number,
	len: number,
	d: number,
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

local function ball(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
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

-- Part 8: three cannons on each side of the deck (ship centre line X = -62, deck at Y = 7.4).
local function cannon(side: number, z: number): Pieces
	return {
		box(-62 + side * 7.8, 7.4, z, 2.2, 1, 2.4, DARK, Wood),
		lying(-62 + side * 8.6, 8.7, z, 4, 1.3, IRON, Metal),
	}
end

-- Part 11: a palm with three fronds and a coconut.
local function palm(x: number, z: number, h: number): Pieces
	return {
		pole(x, 0, z, h, 1.4, TRUNK, Wood),
		tilted(x, h, z, 12, 0.4, 2.2, LEAF, Grass, 0, 0),
		tilted(x, h, z, 12, 0.4, 2.2, LEAF, Grass, 60, 0),
		tilted(x, h, z, 12, 0.4, 2.2, LEAF, Grass, 120, 0),
		ball(x + 0.6, h - 0.9, z + 0.4, 1.3, 1.3, 1.3, DARK, Wood),
	}
end

-- Part 15: one kraken tentacle (thick lower part, thin upper part, round tip).
local function tentacle(x: number, z: number, lower: number, upper: number, lean: number): Pieces
	return {
		pole(x, 0, z, lower, 3.4, PURPLE, Plastic),
		pole(x + lean, lower, z, upper, 2.4, PURPLE, Plastic),
		ball(x + lean, lower + upper, z, 2.4, 2.4, 2.4, PURPLE, Plastic),
	}
end

local theme: DecorTypes.Theme = {
	Key = "PirateShip",
	Name = "Pirate Ship",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-34, -30), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(48, 44),
		Vector2.new(-22, 20),
		Vector2.new(42, -8),
		Vector2.new(-20, -30),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-34, -18),
	AutoPad = Vector2.new(-26, -18),
	Parts = {
		{
			Id = "Floor",
			Name = "Cove Sand and Lagoon",
			Description = "Golden sand all over the cove and a blue lagoon with a wet shore for the ship.",
			Pad = Vector2.new(-18, 52),
			PriceSeconds = 10,
			Pieces = {
				box(0, 0, 0, 190, 0.3, 130, SAND, Sand),
				box(-68.5, 0.3, -31.5, 47, 0.1, 67, WET, Sand),
				box(-68.5, 0.3, -33, 43, 0.2, 62, SEA, Glass),
				box(30, 0.3, 56, 16, 0.1, 10, GRASS, Grass),
				box(-70, 0.3, 30, 18, 0.1, 12, GRASS, Grass),
				box(60, 0.3, 58, 14, 0.1, 8, GRASS, Grass),
				box(38, 0.3, -43, 32, 0.1, 28, DIRT, Sand),
				box(76, 0.3, -8, 24, 0.1, 20, WET, Sand),
			},
		},
		{
			Id = "Hull",
			Name = "Galleon Hull",
			Description = "A huge dark wood galleon with a pointed bow, planked decks, rails and a tall stern castle.",
			Pad = Vector2.new(-43, -12),
			PriceSeconds = 16,
			RewardMult = 1.35,
			Pieces = {
				box(-62, 0, -27, 20, 7, 42, HULL, Wood),
				box(-62, 0, -52.5, 16, 7, 9, HULL, Wood),
				box(-62, 0, -59.5, 10, 7, 5, HULL, Wood),
				box(-62, 7, -27, 18.6, 0.4, 42, DECK, Planks),
				box(-62, 7, -52.5, 14.6, 0.4, 9, DECK, Planks),
				box(-62, 7, -59.5, 8.6, 0.4, 5, DECK, Planks),
				box(-62, 7.4, -11.2, 19, 5.2, 9.8, HULL, Wood),
				box(-62, 12.6, -11.2, 20, 0.5, 10.4, DECK, Planks),
				box(-62, 7.4, -54, 14, 3.6, 8, HULL, Wood),
				box(-62, 11, -54, 15, 0.4, 9, DECK, Planks),
				box(-71.7, 7.4, -33, 0.6, 1.4, 33, DARK, Wood),
				box(-52.3, 7.4, -33, 0.6, 1.4, 33, DARK, Wood),
				box(-62, 8.6, -6.15, 14, 2.4, 0.3, GOLD, Metal),
				pole(-70.5, 13.1, -7.5, 2.4, 0.5, GOLD, Metal),
				pole(-53.5, 13.1, -7.5, 2.4, 0.5, GOLD, Metal),
			},
		},
		{
			Id = "Sign",
			Yaw = 8,
			Name = "Get Bonked Sign",
			Description = "A big black board on two posts, a skull on top and GET BONKED in bone white letters.",
			Pad = Vector2.new(-52, 48),
			PriceSeconds = 24,
			Pieces = {
				pole(-60.5, 0, 54, 15, 1.2, DARK, Wood),
				pole(-43.5, 0, 54, 15, 1.2, DARK, Wood),
				box(-52, 5.2, 54, 18.4, 9, 0.8, BOARD, Wood),
				box(-52, 14.2, 54, 21, 0.8, 1.4, HULL, Wood),
				box(-52, 4.4, 54, 20, 0.8, 1.2, HULL, Wood),
				ball(-52, 16.3, 54, 3, 2.8, 1.6, BONE, Plastic),
				box(-52, 14.9, 54, 1.8, 0.9, 1.2, BONE, Plastic),
				ball(-60.5, 15.5, 54, 1.6, 1.6, 1.6, GOLD, Metal),
				ball(-43.5, 15.5, 54, 1.6, 1.6, 1.6, GOLD, Metal),
				box(-52, 10.2, 54.5, 6.8, 3.1, 0.3, CREAM, Plastic),
				box(-52, 6.3, 54.5, 14.3, 3.1, 0.3, CREAM, Plastic),
				tilted(-52, 16.3, 53.6, 5, 0.5, 0.6, BONE, Plastic, 0, 25),
				tilted(-52, 16.3, 53.6, 5, 0.5, 0.6, BONE, Plastic, 0, -25),
			},
		},
		{
			Id = "Masts",
			Name = "Masts and Yards",
			Description = "A tall main mast with a crow's nest, a fore mast, a mizzen mast and a bowsprit.",
			Pad = Vector2.new(-44, -56),
			PriceSeconds = 34,
			Pieces = {
				pole(-62, 7.4, -32, 30, 1.4, HULL, Wood),
				box(-62, 16, -32, 18, 0.8, 0.8, DARK, Wood),
				box(-62, 25, -32, 14, 0.8, 0.8, DARK, Wood),
				box(-62, 31.6, -32, 10, 0.8, 0.8, DARK, Wood),
				pole(-62, 27, -32, 1.6, 3.8, DARK, Wood),
				pole(-62, 37.4, -32, 5, 0.8, HULL, Wood),
				pole(-62, 7.4, -50, 24, 1.2, HULL, Wood),
				box(-62, 15.1, -50, 14, 0.8, 0.8, DARK, Wood),
				box(-62, 22.1, -50, 11, 0.8, 0.8, DARK, Wood),
				pole(-62, 12.6, -14, 18, 1, HULL, Wood),
				box(-62, 23.6, -13, 0.7, 0.7, 8, DARK, Wood),
				box(-62, 9.4, -61.5, 0.8, 1.2, 5, DARK, Wood),
			},
		},
		{
			Id = "Pier",
			Name = "Gangplank Pier",
			Description = "A wooden pier from the ship to the Shiba with mooring posts, ropes, barrels and a lantern.",
			Pad = Vector2.new(-45.5, -30),
			PriceSeconds = 46,
			Pieces = {
				box(-45.5, 0.3, -30, 13, 0.28, 5, DECK, Planks),
				box(-41, 0.3, -30, 3.4, 0.28, 6.5, DECK, Planks),
				pole(-50.5, 0.3, -32.9, 2.4, 0.9, DARK, Wood),
				pole(-50.5, 0.3, -27.1, 2.4, 0.9, DARK, Wood),
				pole(-44.5, 0.3, -32.9, 2.4, 0.9, DARK, Wood),
				pole(-44.5, 0.3, -27.1, 2.4, 0.9, DARK, Wood),
				box(-47.5, 1.8, -32.9, 6, 0.14, 0.14, CREAM, Fabric),
				box(-47.5, 1.8, -27.1, 6, 0.14, 0.14, CREAM, Fabric),
				pole(-47.4, 0.3, -31.2, 2, 1.8, HULL, Wood),
				box(-49, 0.3, -28.6, 1.6, 1.6, 1.6, DECK, Wood),
				ball(-44.5, 3.1, -27.1, 0.9, 0.9, 0.9, ORANGE, Plastic),
			},
		},
		{
			Id = "Sails",
			Name = "Cream Sails",
			Description = "Big cream sails with red stripes on all three masts and a jib at the bow.",
			Pad = Vector2.new(-44, -48),
			PriceSeconds = 62,
			Pieces = {
				box(-62, 9.4, -32.6, 16.4, 6.6, 0.6, CREAM, Fabric),
				box(-62, 12.2, -32.9, 16.5, 1, 0.2, RED, Fabric),
				box(-62, 16.9, -32.6, 12.6, 8, 0.6, CREAM, Fabric),
				box(-62, 25.8, -32.6, 8.6, 5.8, 0.6, CREAM, Fabric),
				box(-62, 28, -32.9, 8.7, 0.8, 0.2, RED, Fabric),
				box(-62, 8.6, -50.6, 12.6, 6.4, 0.6, CREAM, Fabric),
				box(-62, 15.9, -50.6, 9.6, 6, 0.6, CREAM, Fabric),
				box(-62, 11.4, -51, 12.7, 0.9, 0.2, RED, Fabric),
				box(-62, 13.5, -14, 0.5, 10, 8, CREAM, Fabric),
				box(-62, 10, -58, 0.5, 11, 7, CREAM, Fabric),
			},
		},
		{
			Id = "Tavern",
			Yaw = -8,
			Name = "Rum Tavern",
			Description = "A two storey pirate tavern with a red roof, a porch, rum barrels and a hanging sign.",
			Pad = Vector2.new(38, -26),
			PriceSeconds = 82,
			Pieces = {
				box(38, 0, -43, 28, 0.5, 26, STONE, Rock),
				box(38, 0.5, -48.5, 22, 8, 15, HULL, Wood),
				box(38, 8.5, -48, 24, 0.5, 16, DECK, Planks),
				box(38, 9, -48.5, 19, 5.5, 13, DARK, Wood),
				box(38, 14.5, -48.5, 24, 0.9, 16.4, RED, Plastic),
				box(38, 15.4, -48.5, 16, 0.9, 11, RED, Plastic),
				pole(28.5, 0.5, -33.4, 7.5, 0.8, DARK, Wood),
				pole(47.5, 0.5, -33.4, 7.5, 0.8, DARK, Wood),
				box(38, 8, -37, 24.5, 0.5, 8.6, DECK, Planks),
				pole(50.4, 0.5, -31.2, 2.8, 2.4, HULL, Wood),
				pole(26.5, 0.5, -31.6, 2.8, 2.4, HULL, Wood),
				box(47.5, 6.5, -33.4, 4, 0.4, 0.4, DARK, Wood),
				box(48.5, 4.2, -33.4, 2.8, 2.2, 0.3, GOLD, Wood),
				box(46, 14, -52, 3, 6, 3, STONE, Rock),
			},
		},
		{
			Id = "Cannons",
			Name = "Deck Cannons",
			Description = "Six black cannons on wooden carriages, three along each side, plus a pile of cannonballs.",
			Pad = Vector2.new(-42, -20),
			PriceSeconds = 106,
			RewardMult = 1.4,
			Pieces = merge(
				cannon(1, -24),
				cannon(1, -33),
				cannon(1, -42),
				cannon(-1, -24),
				cannon(-1, -33),
				cannon(-1, -42),
				{
					ball(-61, 8.3, -28, 1, 1, 1, IRON, Metal),
					ball(-62.2, 8.3, -28.4, 1, 1, 1, IRON, Metal),
					ball(-61.6, 9.1, -28.2, 1, 1, 1, IRON, Metal),
				}
			),
		},
		{
			Id = "Camp",
			Yaw = 22,
			Name = "Pirate Camp",
			Description = "A cream tent, a campfire with log seats, barrels and a stack of crates on the beach.",
			Pad = Vector2.new(76, 27),
			PriceSeconds = 136,
			Pieces = {
				tilted(67.95, 1.73, 37.5, 5.4, 0.3, 8, CREAM, Fabric, 0, 40),
				tilted(72.05, 1.73, 37.5, 5.4, 0.3, 8, CREAM, Fabric, 0, -40),
				pole(78, 0, 42, 0.5, 3, STONE, Rock),
				tilted(78, 0.7, 42, 2.2, 0.4, 0.5, HULL, Wood, 30, 0),
				tilted(78, 0.7, 42, 2.2, 0.4, 0.5, HULL, Wood, -30, 0),
				ball(78, 1.5, 42, 1.3, 1.8, 1.3, ORANGE, Plastic),
				box(78, 0, 46.5, 4.2, 0.9, 1.2, HULL, Wood),
				box(73.5, 0, 42, 1.2, 0.9, 3.6, HULL, Wood),
				pole(85, 0, 36, 2.6, 2.2, HULL, Wood),
				pole(87.3, 0, 37.4, 2.4, 2, HULL, Wood),
				box(82.5, 0, 31.5, 2.6, 2.6, 2.6, DECK, Wood),
				box(85.6, 0, 31.2, 2.2, 2.2, 2.2, DECK, Wood),
				box(84, 2.6, 31.5, 1.8, 1.8, 1.8, DARK, Wood),
			},
		},
		{
			Id = "Flag",
			Name = "Jolly Roger",
			Description = "A black skull and crossbones flag on the top of the main mast and red pennants on the other masts.",
			Pad = Vector2.new(-41, -40),
			PriceSeconds = 172,
			Pieces = {
				pole(-62, 42.4, -32, 4, 0.5, DARK, Wood),
				box(-58.5, 41.6, -32, 7, 4.4, 1, IRON, Fabric),
				ball(-58.3, 43.8, -32, 2.4, 2.2, 1.4, BONE, Plastic),
				tilted(-58.3, 43.8, -32, 4.4, 0.5, 1.2, BONE, Plastic, 0, 30),
				tilted(-58.3, 43.8, -32, 4.4, 0.5, 1.2, BONE, Plastic, 0, -30),
				ball(-62, 46.6, -32, 0.9, 0.9, 0.9, GOLD, Metal),
				pole(-62, 31.4, -50, 3, 0.4, DARK, Wood),
				box(-59.6, 32.2, -50, 5, 1.5, 0.8, RED, Fabric),
				pole(-62, 30.6, -14, 3, 0.4, DARK, Wood),
				box(-59.6, 31.4, -14, 5, 1.5, 0.8, RED, Fabric),
			},
		},
		{
			Id = "Palms",
			Yaw = 15,
			Name = "Palm Grove",
			Description = "Three leaning palm trees with coconuts on the right side of the beach.",
			Pad = Vector2.new(74, 12),
			PriceSeconds = 216,
			Pieces = merge(palm(64, 10, 14.5), palm(78, 18, 16.5), palm(88, 8, 13.5)),
		},
		{
			Id = "Rowboat",
			Yaw = -30,
			Name = "Beached Rowboat",
			Description = "A little rowboat pulled up on the sand with two oars and a rusty anchor.",
			Pad = Vector2.new(-33, -47),
			PriceSeconds = 270,
			Pieces = {
				box(-33, 0.3, -56, 10, 1, 4, HULL, Wood),
				box(-33, 1.3, -58.2, 10, 0.9, 0.5, HULL, Wood),
				box(-33, 1.3, -53.8, 10, 0.9, 0.5, HULL, Wood),
				box(-38.4, 0.3, -56, 1.8, 1.6, 2.8, HULL, Wood),
				box(-27.7, 0.3, -56, 0.6, 1.9, 3.6, DARK, Wood),
				box(-35, 1.3, -56, 0.8, 0.4, 3.6, DECK, Planks),
				box(-31, 1.3, -56, 0.8, 0.4, 3.6, DECK, Planks),
				box(-28, 0.3, -61.2, 6, 0.28, 0.5, DECK, Wood),
				box(-28, 0.3, -60.2, 6, 0.28, 0.5, DECK, Wood),
				pole(-24.5, 0.3, -58, 4, 0.6, IRON, Metal),
				box(-24.5, 3.0, -58, 3.2, 0.5, 0.5, IRON, Metal),
			},
		},
		{
			Id = "Chest",
			Yaw = 25,
			Name = "Treasure Hoard",
			Description = "A giant chest with a round lid and gold bands, piles of gold coins, a goblet and a skull.",
			Pad = Vector2.new(74, -20),
			PriceSeconds = 335,
			RewardMult = 1.6,
			Pieces = {
				box(74, 0, -8, 20, 0.5, 16, WET, Sand),
				box(74, 0.5, -8, 8, 3.4, 5, HULL, Wood),
				lying(74, 3.9, -8, 8, 5, DARK, Wood),
				box(70.5, 0.5, -8, 0.8, 3.5, 5.2, GOLD, Metal),
				box(77.5, 0.5, -8, 0.8, 3.5, 5.2, GOLD, Metal),
				box(74, 2.1, -5.4, 1.2, 1.6, 0.4, GOLD, Metal),
				ball(68.5, 1.1, -5, 5.6, 2.6, 4.6, GOLD, Metal),
				ball(80.5, 1, -5, 5, 2.4, 4.2, GOLD, Metal),
				ball(78, 0.9, -3.4, 4, 1.8, 3.2, GOLD, Metal),
				ball(70.5, 1, -11, 2, 2, 2, BONE, Plastic),
				pole(80, 0.5, -11, 2, 1, GOLD, Metal),
			},
		},
		{
			Id = "SkullRock",
			Yaw = 12,
			Name = "Skull Rock",
			Description = "A grey rock in the lagoon shaped like a giant skull with dark eyes, a toothy grin and a pirate hat.",
			Pad = Vector2.new(-92, -50),
			PriceSeconds = 410,
			Pieces = {
				box(-82, 0, -52, 13, 4.5, 12, STONE, Rock),
				box(-86.5, 0, -55, 3.2, 9, 3.2, STONE, Rock),
				box(-76.8, 0, -56, 3, 7, 3, STONE, Rock),
				box(-82, 4.5, -50.2, 8.4, 3, 6, BONE, Rock),
				ball(-82, 10.6, -52, 10, 8.4, 9, BONE, Rock),
				box(-84.4, 8.4, -47.6, 2.6, 2.8, 0.8, IRON, Rock),
				box(-79.6, 8.4, -47.6, 2.6, 2.8, 0.8, IRON, Rock),
				box(-82, 7.5, -47.6, 1.2, 1.6, 0.8, IRON, Rock),
				box(-82, 4.6, -46.9, 6.4, 1, 0.5, CREAM, Rock),
				box(-82, 14.3, -52, 8, 0.6, 7, IRON, Fabric),
				box(-82, 14.9, -52, 4.6, 2.2, 4.2, IRON, Fabric),
			},
		},
		{
			Id = "Kraken",
			Name = "The Kraken",
			Description = "A purple sea monster with big yellow eyes and four huge tentacles rising out of the lagoon.",
			Pad = Vector2.new(-84, 2),
			PriceSeconds = 500,
			RewardMult = 2,
			Pieces = merge(
				{
					ball(-82, 6, -8, 10, 9, 9, PURPLE, Plastic),
					ball(-84.5, 7.8, -3.9, 2.2, 2.6, 1.4, YELLOW, Plastic),
					ball(-79.5, 7.8, -3.9, 2.2, 2.6, 1.4, YELLOW, Plastic),
				},
				tentacle(-87.5, -10, 10, 7, -0.4),
				tentacle(-76.5, -9, 9, 6.5, 0.5),
				tentacle(-86, -16, 8, 8, -0.6),
				tentacle(-78, -16, 7, 8, 0.6)
			),
		},
	},
}

return theme
