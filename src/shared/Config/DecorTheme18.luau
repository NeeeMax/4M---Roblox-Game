--!strict
-- Theme of the Shiba of bay 18: Vampire Crypt (Config/DecorTypes -> Theme). 190 x 130: a moonlit graveyard. The Vampire Shiba stands
-- on the left before a great gothic moon gate, a winding path leads past candles, coffins and a fountain of blood to the black crypt
-- hall in the back right, with a ruined chapel, a bat belfry and an ossuary around the dark left side.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: candles, lanterns and blood are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local NIGHT = C(44, 64, 58)
local COBBLE = C(96, 94, 110)
local STONE = C(116, 114, 130)
local DARK = C(64, 62, 78)
local BLACK = C(36, 34, 46)
local PURPLE = C(86, 58, 122)
local CRIM = C(160, 26, 46)
local BLOOD = C(200, 34, 54)
local BONE = C(232, 224, 206)
local IRON = C(40, 40, 50)
local WOOD = C(88, 58, 44)
local GOLD = C(214, 172, 66)
local MOON = C(240, 236, 208)
local DIRT = C(78, 60, 50)
local HEDGE = C(36, 74, 54)
local GREEN = C(120, 200, 120)

local Wood = Enum.Material.Wood
local Slate = Enum.Material.Slate
local Cobble = Enum.Material.Cobblestone
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass
local Pebble = Enum.Material.Pebble

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

-- Cylinder lying along Z (a wheel, a disc facing the road): diameter d, thickness len.
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

local function rot(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
end

-- A tombstone block of the graveyard.
local function stone(x: number, z: number, w: number, h: number, color: Color3): Piece
	return B(x, h / 2, z, w, h, 1.2, color, Slate)
end

local theme: DecorTypes.Theme = {
	Key = "VampireCrypt",
	Name = "Vampire Crypt",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-60, 4), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-34, 46),
		Vector2.new(30, 30),
		Vector2.new(-32, 6),
		Vector2.new(44, -12),
		Vector2.new(-12, -36),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-71, 4),
	AutoPad = Vector2.new(-60, 16),
	Parts = {
		{
			Id = "Ground",
			Name = "Moonlit Graveyard",
			Description = "Dark grass under a pale moon, a cobbled court before the crypt, a red carpet and muddy graves.",
			Pad = Vector2.new(-12, 57),
			PriceSeconds = 38,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, NIGHT, Grass),
				B(60, 0.3, -42, 44, 0.4, 30, COBBLE, Cobble),
				B(60, 0.3, -16, 5, 0.3, 30, CRIM, Fabric),
				B(-60, 0.3, 4, 28, 0.4, 28, COBBLE, Cobble),
				B(-66, 0.3, 40, 34, 0.4, 22, DIRT, Pebble),
			},
		},
		{
			Id = "Gate",
			Name = "Moon Gate",
			Description = "A tall gothic arch of black stone with gargoyles, open iron gates and a crescent moon on top.",
			Pad = Vector2.new(-80, 27),
			PriceSeconds = 44,
			Pieces = {
				B(-82, 9, -8.2, 4, 18, 4, STONE, Slate),
				B(-82, 9, 16.2, 4, 18, 4, STONE, Slate),
				B(-82, 20, 4, 2.6, 3, 24.4, STONE, Slate),
				B(-82, 24.5, 4, 2.4, 5, 3, DARK, Slate),
			},
		},
		{
			Id = "Crypt",
			Name = "Crypt Hall",
			Description = "The vampire's black stone hall: a pillared porch, a red door and a pointed roof with a spire.",
			Pad = Vector2.new(60, -24),
			Yaw = -6,
			PriceSeconds = 50,
			RewardMult = 1.25,
			Pieces = {
				B(60, 5, -55, 36, 10, 2, BLACK, Cobble),
				B(43, 5, -45, 2, 10, 22, BLACK, Cobble),
				B(77, 5, -45, 2, 10, 22, BLACK, Cobble),
				B(41, 4, -45, 2, 8, 5, BLACK, Cobble),
				B(79, 4, -45, 2, 8, 5, BLACK, Cobble),
				B(49.5, 5, -35, 15, 10, 2, BLACK, Cobble),
				B(70.5, 5, -35, 15, 10, 2, BLACK, Cobble),
				B(60, 9, -35, 6, 2, 2, DARK, Slate),
				B(60, 13, -50.5, 38, 0.8, 11.2, DARK, Slate, rot(-26.6, 0, 0)),
				B(60, 13, -39.5, 38, 0.8, 11.2, DARK, Slate, rot(26.6, 0, 0)),
				B(60, 18.5, -45, 6, 5, 6, BLACK, Cobble),
				B(60, 23, -45, 2.6, 6, 2.6, DARK, Slate),
				B(54, 4.5, -31, 1.8, 9, 1.8, STONE, Slate),
				B(66, 4.5, -31, 1.8, 9, 1.8, STONE, Slate),
				B(60, 9.8, -32.6, 16, 0.8, 5.4, DARK, Slate),
			},
		},
		{
			Id = "Graves",
			Name = "Tombstone Field",
			Description = "Crooked tombstones, crosses and a weeping angel on a muddy graveyard plot.",
			Pad = Vector2.new(-58, 24),
			Yaw = 14,
			PriceSeconds = 57,
			Pieces = {
				stone(-78.6, 34, 2.2, 4, STONE),
				stone(-72, 38, 2.4, 6, DARK),
				stone(-65, 35, 2.2, 3.6, STONE),
				stone(-58, 34.5, 2.4, 5.2, DARK),
				stone(-53.1, 38, 2.2, 4, STONE),
				stone(-76, 44, 2.2, 3.2, STONE),
				B(-68, 3.6, 45, 3, 7.2, 1.4, DARK, Slate),
				stone(-60, 43.5, 2.4, 4, DARK),
				stone(-54.4, 46, 2.2, 3.6, STONE),
			},
		},
		{
			Id = "Lamps",
			Name = "Gas Lamps",
			Description = "Three tall iron lamps that glow a ghostly green along the road to the crypt.",
			Pad = Vector2.new(50, 46),
			Yaw = -18,
			PriceSeconds = 65,
			Pieces = {
				B(34, 5.6, 57, 0.7, 11.2, 0.7, IRON, Metal),
				B(34, 11.8, 57, 2, 2.4, 2, GREEN, Plastic),
				B(34, 0.6, 57, 2.4, 1.2, 2.4, IRON, Metal),
				B(50, 5.6, 53, 0.7, 11.2, 0.7, IRON, Metal),
				B(50, 11.8, 53, 2, 2.4, 2, GREEN, Plastic),
				B(50, 0.6, 53, 2.4, 1.2, 2.4, IRON, Metal),
				B(66, 5.6, 57, 0.7, 11.2, 0.7, IRON, Metal),
				B(66, 11.8, 57, 2, 2.4, 2, GREEN, Plastic),
				B(66, 0.6, 57, 2.4, 1.2, 2.4, IRON, Metal),
			},
		},
		{
			Id = "Tree",
			Name = "Haunted Dead Tree",
			Description = "A gnarled leafless tree with long claw-like branches, a crow and hanging bats.",
			Pad = Vector2.new(30, -38),
			Yaw = 20,
			PriceSeconds = 75,
			Pieces = {
				Cy(30, 1, -52, 5, 2, DARK, Slate),
				B(30, 6, -52, 2.6, 8, 2.6, IRON, Wood, rot(0, 0, 6)),
				B(26.4, 11, -52, 8, 0.9, 0.9, IRON, Wood, rot(0, 0, 25)),
				B(34.8, 12.2, -52, 9, 0.9, 0.9, IRON, Wood, rot(0, 0, -30)),
				B(30.6, 12.6, -55.6, 0.9, 0.9, 8, IRON, Wood, rot(25, 0, 0)),
				B(30.4, 13.4, -48.6, 0.9, 0.9, 7, IRON, Wood, rot(-25, 0, 0)),
				B(29.4, 15.2, -52, 3, 0.8, 0.8, IRON, Wood, rot(0, 0, 35)),
			},
		},
		{
			Id = "Coffin",
			Name = "Open Coffin",
			Description = "A black coffin with a red velvet bed and a gold cross, the lid leaning open on a stone dais.",
			Pad = Vector2.new(34, 22),
			Yaw = -22,
			PriceSeconds = 86,
			Pieces = {
				B(34, 0.6, 12, 14, 1.2, 9, STONE, Slate),
				B(34, 2.4, 12, 10, 2.4, 4, BLACK, Wood),
				B(34, 3.8, 8.9, 9, 0.5, 4, BLACK, Wood, rot(-62, 0, 0)),
				Cy(28.2, 2.4, 15.6, 0.8, 2.4, BONE, Plastic),
				Cy(39.8, 2.4, 15.6, 0.8, 2.4, BONE, Plastic),
			},
		},
		{
			Id = "Fountain",
			Name = "Blood Fountain",
			Description = "A three-tier stone fountain, brimming with deep red blood, with a bat on top.",
			Pad = Vector2.new(62, 10),
			PriceSeconds = 99,
			RewardMult = 1.4,
			Pieces = {
				Cy(66, 0.8, -4, 16, 1.6, STONE, Slate),
				Cy(66, 1.7, -4, 14, 0.5, BLOOD, Plastic),
				Cy(66, 3.6, -4, 9, 1.2, STONE, Slate),
				Cy(66, 5.2, -4, 2.6, 4, DARK, Slate),
				Cy(66, 8, -4, 5, 0.8, STONE, Slate),
				B(66, 10.4, -4, 1.4, 3.6, 1.4, IRON, Metal),
			},
		},
		{
			Id = "Gargoyles",
			Name = "Gargoyle Perches",
			Description = "Three stone gargoyles with bat wings crouching on pedestals, watching everyone who passes.",
			Pad = Vector2.new(18, 44),
			Yaw = 16,
			PriceSeconds = 114,
			Pieces = {
				B(10, 2, 58, 3.2, 4, 3.2, DARK, Slate),
				B(10, 5.4, 58, 2.4, 2.8, 2.4, STONE, Slate),
				B(10, 6.4, 58, 5.6, 0.7, 1, BLACK, Slate, rot(0, 0, 18)),
				B(20, 3, 52, 3.2, 6, 3.2, DARK, Slate),
				B(20, 7.4, 52, 2.4, 2.8, 2.4, STONE, Slate),
				B(20, 8.4, 52, 5.6, 0.7, 1, BLACK, Slate, rot(0, 0, -18)),
				B(28, 1.5, 59, 3.2, 3, 3.2, DARK, Slate),
				B(28, 4.4, 59, 2.4, 2.8, 2.4, STONE, Slate),
				B(28, 5.4, 59, 5.6, 0.7, 1, BLACK, Slate, rot(0, 0, 18)),
			},
		},
		{
			Id = "Hearse",
			Name = "Funeral Carriage",
			Description = "A black hearse carriage with a canopy, a coffin, green lanterns and big spoked wheels.",
			Pad = Vector2.new(66, 20),
			Yaw = -24,
			PriceSeconds = 131,
			Pieces = {
				B(65, 2.6, 36, 16, 1, 5.4, BLACK, Wood),
				B(64, 4.6, 36, 12, 3, 4, WOOD, Wood),
				B(64, 9.2, 36, 14, 0.8, 6.4, BLACK, Wood),
				B(58.2, 6.4, 33.4, 0.7, 6, 0.7, IRON, Metal),
				B(58.2, 6.4, 38.6, 0.7, 6, 0.7, IRON, Metal),
				B(69.8, 6.4, 33.4, 0.7, 6, 0.7, IRON, Metal),
				B(69.8, 6.4, 38.6, 0.7, 6, 0.7, IRON, Metal),
				Cz(59, 2.8, 31.2, 5.6, 0.8, IRON, Wood),
				Cz(59, 2.8, 40.8, 5.6, 0.8, IRON, Wood),
				Cz(70, 2.2, 31.2, 4.4, 0.8, IRON, Wood),
				Cz(70, 2.2, 40.8, 4.4, 0.8, IRON, Wood),
				B(74.6, 2.6, 36, 6.8, 0.5, 0.5, WOOD, Wood),
				B(71.4, 7, 36, 0.8, 1.6, 0.8, GREEN, Plastic),
			},
		},
		{
			Id = "Candles",
			Name = "Candelabra Circle",
			Description = "Four tall iron candelabras around a stone altar with a skull and an old book.",
			Pad = Vector2.new(9, 10),
			Yaw = 0,
			PriceSeconds = 150,
			Pieces = {
				Cy(3, 4.5, 6, 0.9, 9, IRON, Metal),
				B(3, 9.4, 6, 3, 0.5, 0.5, GOLD, Metal),
				Cy(14.6, 4.5, 5.4, 0.9, 9, IRON, Metal),
				B(14.6, 9.4, 5.4, 3, 0.5, 0.5, GOLD, Metal),
				Cy(3.4, 4.5, 11.6, 0.9, 9, IRON, Metal),
				B(3.4, 9.4, 11.6, 3, 0.5, 0.5, GOLD, Metal),
				Cy(15, 4.5, 12, 0.9, 9, IRON, Metal),
				B(15, 9.4, 12, 3, 0.5, 0.5, GOLD, Metal),
				B(9, 0.9, 10, 5, 1.8, 3.4, STONE, Slate),
				Ball(9.4, 2.4, 10, 1.4, 1.3, 1.4, BONE, Plastic),
			},
		},
		{
			Id = "Chapel",
			Name = "Ruined Chapel",
			Description = "A crumbling chapel front with a pointed doorway, a broken gable and fallen stones.",
			Pad = Vector2.new(-52, -26),
			Yaw = 10,
			PriceSeconds = 173,
			Pieces = {
				B(-68, 6, -40, 10, 12, 2, STONE, Slate),
				B(-52, 5, -40, 10, 10, 2, STONE, Slate),
				B(-60, 10.5, -40, 6, 3, 2, STONE, Slate),
				B(-60, 14.2, -40, 10, 4.4, 2, DARK, Slate),
				B(-72.5, 5, -37, 2.2, 10, 4, DARK, Slate),
				B(-47.5, 4, -37, 2.2, 8, 4, DARK, Slate),
				B(-74, 3.5, -43, 1.8, 7, 8, STONE, Slate),
				B(-46.4, 2, -43, 1.8, 4, 8, STONE, Slate),
				Ball(-56, 0.8, -36.4, 3, 1.6, 2.4, DARK, Slate),
				Ball(-65, 0.7, -36.4, 2.4, 1.4, 2, STONE, Slate),
			},
		},
		{
			Id = "Cellar",
			Name = "Blood Wine Cellar",
			Description = "Big oak barrels, a bottle rack and a table with goblets of the vampire's favourite red drink.",
			Pad = Vector2.new(-22, 39),
			Yaw = -10,
			PriceSeconds = 199,
			Pieces = {
				Cy(-27, 2, 24.6, 3.4, 4, WOOD, Wood),
				Cy(-23.4, 2, 25.4, 3.4, 4, WOOD, Wood),
				Cy(-25.4, 2, 29, 3.4, 4, WOOD, Wood),
				Cy(-25.4, 4.9, 29, 3, 1.8, WOOD, Wood),
				Cz(-20, 2.6, 30.4, 5, 6, WOOD, Wood),
				B(-15.6, 2.5, 25.4, 2, 5, 6.4, WOOD, Wood),
				B(-19, 2.3, 24, 4, 0.4, 2.6, WOOD, Wood),
			},
		},
		{
			Id = "Mirror",
			Name = "Mirror of No Reflection",
			Description = "A tall gothic mirror with a black carved frame. Vampires have no reflection, so it shows nothing!",
			Pad = Vector2.new(6, -6),
			Yaw = 26,
			PriceSeconds = 229,
			Pieces = {
				B(4, 7.5, -16, 8, 15, 1.4, BLACK, Wood),
				B(4, 0.7, -16, 6, 1.4, 3.6, BLACK, Wood),
				B(4, 15.6, -16, 3, 1.6, 1.4, GOLD, Metal),
			},
		},
		{
			Id = "Cauldron",
			Name = "Brew Cauldron",
			Description = "A big iron cauldron of bubbling green brew over a fire, with a ladle and a pile of bones.",
			Pad = Vector2.new(-44, 38),
			PriceSeconds = 263,
			Pieces = {
				Ball(-44, 4.2, 28, 8, 6, 8, IRON, Metal),
				Cy(-44, 6.9, 28, 8.4, 0.8, IRON, Metal),
				Cy(-44, 7.1, 28, 6.8, 0.5, GREEN, Plastic),
				B(-47.6, 2, 28, 0.8, 4.2, 0.8, IRON, Metal, rot(0, 0, 25)),
				B(-40.4, 2, 28, 0.8, 4.2, 0.8, IRON, Metal, rot(0, 0, -25)),
				B(-44, 2, 31.6, 0.8, 4.2, 0.8, IRON, Metal, rot(-25, 0, 0)),
				B(-44, 0.8, 24.4, 6, 1.4, 2, WOOD, Wood),
				B(-39.4, 3, 32.4, 0.5, 6, 0.5, WOOD, Wood, rot(0, 0, 15)),
			},
		},
		{
			Id = "Hunter",
			Name = "Hunter's Handcart",
			Description = "A vampire hunter's cart piled with sharp wooden stakes, garlic and a crossbow. Brave, or silly?",
			Pad = Vector2.new(-58, 56),
			Yaw = -16,
			PriceSeconds = 302,
			Pieces = {
				B(-73, 3.6, 57, 9, 0.8, 5, WOOD, Wood),
				B(-73, 4.9, 54.6, 9, 1.8, 0.5, WOOD, Wood),
				B(-73, 4.9, 59.4, 9, 1.8, 0.5, WOOD, Wood),
				B(-77.6, 4.9, 57, 0.5, 1.8, 5, WOOD, Wood),
				Cz(-75, 2.2, 53.6, 4.4, 0.6, IRON, Wood),
				Cz(-75, 2.2, 60.4, 4.4, 0.6, IRON, Wood),
				B(-66.4, 3.2, 57, 7.6, 0.4, 0.4, WOOD, Wood, rot(0, 0, -12)),
				B(-73, 6.6, 57, 0.4, 4.8, 0.4, WOOD, Wood, rot(0, 0, 28)),
				B(-75.6, 6.4, 57.4, 0.4, 4.4, 0.4, WOOD, Wood, rot(0, 0, -20)),
				Ball(-70, 5.4, 57, 2.4, 1.8, 2.4, BONE, Fabric),
			},
		},
		{
			Id = "Ossuary",
			Name = "Skull Ossuary",
			Description = "A wall of stacked skulls and bones with a dark alcove, bone columns and little candles.",
			Pad = Vector2.new(-24, -44),
			Yaw = -8,
			PriceSeconds = 347,
			Pieces = {
				B(-24, 4, -56.5, 20, 8, 2, STONE, Slate),
				B(-33, 3.5, -54.2, 2, 7, 2, BONE, Plastic),
				B(-15, 3.5, -54.2, 2, 7, 2, BONE, Plastic),
				B(-24, 2.8, -54.6, 6, 5.6, 1.6, BLACK, Slate),
				Ball(-29.6, 0.9, -53.2, 2.8, 1.8, 2.4, BONE, Plastic),
				Ball(-18.6, 0.9, -53, 3, 1.8, 2.4, BONE, Plastic),
				Ball(-24, 0.8, -52.8, 2.4, 1.6, 1.6, BONE, Plastic),
			},
		},
		{
			Id = "Belfry",
			Name = "Bat Belfry",
			Description = "A tall dark bell tower with a golden bell, a purple spire and bats hanging all around.",
			Pad = Vector2.new(-86, -34),
			Yaw = 8,
			PriceSeconds = 399,
			Pieces = {
				B(-86, 7, -52, 9, 14, 9, DARK, Cobble),
				B(-86, 17, -52, 7, 6, 7, BLACK, Cobble),
				Ball(-86, 17, -52, 3, 3.6, 3, GOLD, Metal),
				B(-86, 20.4, -52, 9, 0.8, 9, STONE, Slate),
				B(-86, 25, -52, 5.2, 8.4, 5.2, PURPLE, Slate),
				B(-86, 31.5, -52, 1.8, 5, 1.8, IRON, Metal),
			},
		},
		{
			Id = "Hedge",
			Name = "Bat Topiary Garden",
			Description = "Dark green hedge walls trimmed into pointed towers, with a bat cut out of the hedge.",
			Pad = Vector2.new(73, -24),
			Yaw = 8,
			PriceSeconds = 459,
			Pieces = {
				B(82.5, 2.5, -14, 2.4, 5, 24, HEDGE, Grass),
				B(90.5, 2.5, -14, 2.4, 5, 24, HEDGE, Grass),
				B(86.5, 2.5, -25.6, 10.4, 5, 2.4, HEDGE, Grass),
				Cy(82.5, 6.4, -25.6, 2.6, 3.4, HEDGE, Grass),
				Cy(90.5, 6.4, -25.6, 2.6, 3.4, HEDGE, Grass),
				B(86.5, 6.8, -25.6, 3.6, 4, 1.4, HEDGE, Grass),
				Cy(86.5, 1.2, -9, 2.4, 2.4, STONE, Slate),
			},
		},
		{
			Id = "Tomb",
			Name = "Angel Tomb",
			Description = "A little family tomb of grey stone with urns and a weeping angel keeping watch on its roof.",
			Pad = Vector2.new(12, -38),
			Yaw = -10,
			PriceSeconds = 528,
			Pieces = {
				B(10, 4, -51, 8, 8, 6, STONE, Slate),
				B(10, 8.6, -51, 9.4, 1, 7.4, DARK, Slate),
				B(10, 0.6, -46.4, 6, 1.2, 2.6, STONE, Slate),
				B(10, 11.4, -51, 2, 4.4, 1.6, BONE, Slate),
				B(10, 12, -51, 5.6, 3, 0.6, BONE, Slate),
				Cy(5, 1.6, -47, 2, 3.2, DARK, Slate),
				Cy(15, 1.6, -47, 2, 3.2, DARK, Slate),
			},
		},
		{
			Id = "Moon",
			Name = "Blood Moon Totem",
			Description = "A great pale moon in an iron ring on two tall posts, crowned with spikes.",
			Pad = Vector2.new(-40, -54),
			Yaw = 24,
			PriceSeconds = 607,
			Pieces = {
				B(-50.6, 6, -57, 1.2, 12, 1.2, IRON, Metal),
				B(-41.4, 6, -57, 1.2, 12, 1.2, IRON, Metal),
				Cz(-46, 15.5, -57, 10, 1.2, MOON, Plastic),
				Cz(-46, 15.5, -57, 11.6, 0.8, IRON, Metal),
				B(-46, 21.8, -57, 0.8, 2.4, 0.8, IRON, Metal),
				B(-46, 0.4, -57, 12, 0.8, 2.8, DARK, Slate),
			},
		},
		{
			Id = "Organ",
			Name = "Gothic Organ",
			Description = "A huge pipe organ with seven gleaming pipes, a black console, a bench and two flickering candles.",
			Pad = Vector2.new(84, 42),
			Yaw = -9,
			PriceSeconds = 698,
			RewardMult = 1.3,
			Pieces = {
				B(86, 2.5, 54, 14, 5, 4, BLACK, Wood),
				Cy(80, 8, 51.5, 1.6, 12, GOLD, Metal),
				Cy(82.2, 9, 51.5, 1.6, 14, GOLD, Metal),
				Cy(84.4, 10, 51.5, 1.6, 16, GOLD, Metal),
				Cy(86.6, 10.5, 51.5, 1.6, 17, GOLD, Metal),
				Cy(88.8, 10, 51.5, 1.6, 16, GOLD, Metal),
				Cy(91, 9, 51.5, 1.6, 14, GOLD, Metal),
				Cy(93.2, 8, 51.5, 1.6, 12, GOLD, Metal),
				B(86, 1.2, 57, 5, 1.2, 1.6, WOOD, Wood),
				B(86, 5.4, 54, 15, 0.8, 4.4, DARK, Slate),
			},
		},
		{
			Id = "Throne",
			Name = "Vampire Throne",
			Description = "A tall black throne with bat wings and a red velvet seat on a stone dais, between two torches.",
			Pad = Vector2.new(-38, -12),
			Yaw = 7,
			PriceSeconds = 802,
			RewardMult = 1.4,
			Pieces = {
				B(-38, 0.6, -24, 14, 1.2, 12, DARK, Slate),
				B(-38, 1.8, -25, 8, 1.2, 8, STONE, Slate),
				B(-38, 3.6, -25, 3.6, 2.4, 3.4, CRIM, Fabric),
				B(-38, 9.5, -27.2, 4, 11, 1, BLACK, Wood),
				B(-41.8, 12, -27.2, 3.4, 5, 0.8, PURPLE, Fabric, rot(0, 0, 25)),
				B(-34.2, 12, -27.2, 3.4, 5, 0.8, PURPLE, Fabric, rot(0, 0, -25)),
				B(-40.3, 4.6, -25, 0.8, 1.6, 3.4, BLACK, Wood),
				B(-35.7, 4.6, -25, 0.8, 1.6, 3.4, BLACK, Wood),
				Cy(-44, 3.6, -20, 0.8, 6.4, IRON, Metal),
				B(-44, 7.2, -20, 1.6, 1.4, 1.6, BLOOD, Plastic),
				Cy(-32, 3.6, -20, 0.8, 6.4, IRON, Metal),
				B(-32, 7.2, -20, 1.6, 1.4, 1.6, BLOOD, Plastic),
			},
		},
		{
			Id = "Gibbet",
			Name = "Hanging Cages",
			Description = "A gallows frame with two iron cages on chains, a skeleton inside and a crow keeping watch.",
			Pad = Vector2.new(86, -34),
			Yaw = -22,
			PriceSeconds = 922,
			Pieces = {
				B(91, 7, -48, 1.4, 14, 1.4, WOOD, Wood),
				B(87.5, 13.4, -48, 8.6, 0.8, 0.8, WOOD, Wood),
				B(88.4, 10.8, -48, 3.4, 0.6, 0.6, WOOD, Wood, rot(0, 0, 45)),
				B(84.8, 8.8, -48, 2.6, 5, 2.6, IRON, Metal),
				B(89, 8.4, -48, 2.6, 5, 2.6, IRON, Metal),
				B(87.5, 0.25, -46, 9.5, 0.5, 9, DIRT, Pebble),
			},
		},
		{
			Id = "Statue",
			Name = "Giant Bat Statue",
			Description = "The showpiece: a huge stone bat-demon with spread wings and red eyes crouching on a plinth.",
			Pad = Vector2.new(-68, -6),
			Yaw = 6,
			PriceSeconds = 1060,
			RewardMult = 2,
			Pieces = {
				B(-70, 1.4, -18, 12, 2.8, 12, DARK, Slate),
				B(-70, 3.4, -18, 9, 1.2, 9, STONE, Slate),
				B(-70, 8.4, -18, 5, 8.6, 4, STONE, Slate),
				Ball(-70, 14, -18, 3.8, 3.4, 3.4, STONE, Slate),
				B(-75.6, 17, -18, 10, 0.8, 5, BLACK, Slate, rot(0, 0, 35)),
				B(-64.4, 17, -18, 10, 0.8, 5, BLACK, Slate, rot(0, 0, -35)),
				B(-71.4, 17, -18, 0.8, 3, 0.8, STONE, Slate, rot(0, 0, 20)),
				B(-68.6, 17, -18, 0.8, 3, 0.8, STONE, Slate, rot(0, 0, -20)),
			},
		},
	},
}

return theme
