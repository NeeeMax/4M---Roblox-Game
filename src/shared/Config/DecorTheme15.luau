--!strict
-- Theme of the Shiba of bay 15: Hero HQ (Config/DecorTypes -> Theme). 190 x 130: Superhero Shiba stands in the middle of the plot on a big
-- red and blue emblem plaza, backed by a giant emblem wall; a looping walkway circles it past the hero city: HQ tower in the back right,
-- jet and mech on the right, training grounds and garage on the left, a statue park inside the loop.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: beams, lamps and crystals are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local BLUE = C(40, 80, 200)
local NAVY = C(28, 44, 100)
local RED = C(214, 44, 52)
local YELLOW = C(250, 205, 50)
local WHITE = C(238, 240, 246)
local STEEL = C(160, 168, 182)
local DARK = C(58, 62, 78)
local CYAN = C(120, 215, 240)
local PAVE = C(96, 106, 132)
local GRASS = C(88, 150, 84)
local STONE = C(150, 152, 160)
local WOOD = C(130, 92, 58)
local WATER = C(90, 180, 240)
local ROCK = C(90, 84, 98)
local CREAM = C(232, 220, 190)
local ORANGE = C(240, 140, 40)

local Concrete = Enum.Material.Concrete
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Granite = Enum.Material.Granite
local Fabric = Enum.Material.Fabric
local Wood = Enum.Material.Wood
local Glass = Enum.Material.Glass
local Grass = Enum.Material.Grass
local Slate = Enum.Material.Slate

-- Block centred at (x, y, z), size (sx, sy, sz).
local function B(
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
		Shape = Enum.PartType.Block,
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

-- Cylinder lying along Z (a shield or dish facing the road): diameter d, thickness len.
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

local theme: DecorTypes.Theme = {
	Key = "HeroHQ",
	Name = "Hero HQ",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(20, -4), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(46, 46),
		Vector2.new(10, 24),
		Vector2.new(-44, 16),
		Vector2.new(-58, -22),
		Vector2.new(-10, -44),
		Vector2.new(36, -34),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(34, -10),
	AutoPad = Vector2.new(34, 2),
	Parts = {
		{
			Id = "Ground",
			Name = "Hero City Plaza",
			Description = "Blue-grey city paving, a lawn park and a huge red hero emblem under the Shiba.",
			Pad = Vector2.new(-58, 60),
			PriceSeconds = 36,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, PAVE, Concrete),
				B(20, 0.25, -4, 36, 0.3, 36, NAVY, Concrete),
				B(20, 0.3, -4, 29, 0.3, 29, RED, Plastic),
				B(20, 0.35, -4, 21, 0.3, 21, YELLOW, Plastic),
				B(-18, 0.3, 2, 58, 0.4, 36, GRASS, Grass),
				B(-60, 0.3, -2, 30, 0.4, 24, GRASS, Grass),
			},
		},
		{
			Id = "EmblemWall",
			Yaw = 0,
			Name = "Hero Emblem Wall",
			Description = "A giant shield wall with the hero emblem and two swept wings standing behind the Superhero Shiba.",
			Pad = Vector2.new(8, -14),
			PriceSeconds = 41,
			Pieces = {
				B(20, 1, -22, 36, 2, 6, STEEL, Concrete),
				B(20, 10, -22, 16, 16, 3, BLUE, Metal),
				B(7, 7, -22, 6, 10, 3, NAVY, Metal),
				B(33, 7, -22, 6, 10, 3, NAVY, Metal),
				B(20, 19, -22, 8, 2, 3, YELLOW, Metal),
			},
		},
		{
			Id = "Tower",
			Yaw = 8,
			Name = "HQ Tower",
			Description = "The stepped blue headquarters of the heroes with a helipad crown and a tall radio spire.",
			Pad = Vector2.new(60, -28),
			RewardMult = 1.25,
			PriceSeconds = 47,
			Pieces = {
				B(76, 6, -46, 26, 12, 24, NAVY, Concrete),
				B(76, 19, -46, 20, 14, 18, BLUE, Concrete),
				B(76, 29.5, -46, 14, 7, 14, BLUE, Concrete),
				B(76, 33.4, -46, 17, 0.8, 17, STEEL, Metal),
				Cy(76, 39.4, -46, 1, 11.2, STEEL, Metal),
			},
		},
		{
			Id = "Billboard",
			Yaw = -12,
			Name = "Hero Billboard",
			Description = "A roadside billboard on two steel legs that shouts HERO HQ to everybody passing by.",
			Pad = Vector2.new(-78, 47),
			PriceSeconds = 54,
			Pieces = {
				B(-78, 15, 56, 24, 10, 1.4, BLUE, Plastic),
				Cy(-85, 5, 56, 1.6, 10, STEEL, Metal),
				Cy(-71, 5, 56, 1.6, 10, STEEL, Metal),
				B(-78, 10.2, 57.2, 24, 0.5, 2.4, DARK, Metal),
				B(-78, 20.8, 56.6, 24, 0.8, 2.4, DARK, Metal),
			},
		},
		{
			Id = "Jet",
			Yaw = -28,
			Name = "Hero Jet",
			Description = "A white and blue jet with a red nose parked on its landing apron.",
			Pad = Vector2.new(54, 41),
			PriceSeconds = 62,
			Pieces = {
				B(72, 0.25, 28, 24, 0.5, 20, DARK, Concrete),
				B(70, 4.2, 28, 20, 3.6, 4, WHITE, Metal),
				B(70, 4, 28, 7, 0.7, 17, BLUE, Metal),
				B(61.5, 8.2, 28, 4, 5, 0.8, RED, Metal),
				B(62, 5.2, 28, 3.4, 0.6, 7, BLUE, Metal),
				Ball(80, 4.2, 28, 5, 3.6, 3.6, RED, Metal),
				B(76, 1.1, 28, 1.2, 2, 1.2, DARK, Metal),
				B(66, 1.1, 24.5, 1.2, 2, 1.2, DARK, Metal),
				B(66, 1.1, 31.5, 1.2, 2, 1.2, DARK, Metal),
			},
		},
		{
			Id = "Garage",
			Yaw = 12,
			Name = "Hero Garage",
			Description = "An open workshop with a red roof and the blue sports car of the hero inside.",
			Pad = Vector2.new(-46, 58),
			PriceSeconds = 71,
			Pieces = {
				B(-46, 0.25, 44, 22, 0.5, 18, DARK, Concrete),
				B(-46, 5, 37.6, 20, 10, 1.2, STEEL, Metal),
				B(-55.4, 5, 43, 1.2, 10, 12, STEEL, Metal),
				B(-36.6, 5, 43, 1.2, 10, 12, STEEL, Metal),
				B(-46, 10.4, 43.6, 22, 0.8, 14, RED, Metal),
				B(-46, 1.9, 45, 6, 2.2, 11, BLUE, Plastic),
				B(-46, 3.6, 45, 4.6, 1.2, 5, CYAN, Glass),
			},
		},
		{
			Id = "Course",
			Yaw = -18,
			Name = "Training Course",
			Description = "A rubber training yard with a wall, a pull-up bar, a balance beam, tyres and a punching bag.",
			Pad = Vector2.new(-66, 46),
			PriceSeconds = 81,
			Pieces = {
				B(-80, 0.15, 34, 24, 0.3, 16, RED, Plastic),
				B(-89, 1.6, 36, 2, 3.2, 6, YELLOW, Wood),
				B(-84, 3, 28, 0.8, 6, 0.8, STEEL, Metal),
				B(-76, 3, 28, 0.8, 6, 0.8, STEEL, Metal),
				B(-80, 6, 28, 9, 0.6, 0.6, STEEL, Metal),
				B(-72, 0.9, 38, 10, 0.8, 1.4, WOOD, Wood),
				Cy(-84, 0.7, 33, 3, 1.4, DARK, Fabric),
				Cy(-81, 0.7, 36, 3, 1.4, DARK, Fabric),
				Cy(-70, 2.6, 30, 1.8, 3.6, ORANGE, Fabric),
				B(-70, 5.2, 30, 0.6, 0.6, 0.6, STEEL, Metal),
			},
		},
		{
			Id = "Lab",
			Yaw = 15,
			Name = "Gadget Lab",
			Description = "A white lab with a big observatory dome, a water tank and a radio antenna.",
			Pad = Vector2.new(-58, 4),
			PriceSeconds = 93,
			Pieces = {
				B(-70, 2.5, 10, 16, 5, 14, WHITE, Concrete),
				Ball(-70, 5, 10, 13, 10, 13, STEEL, Metal),
				Cy(-70, 13, 10, 0.8, 6, STEEL, Metal),
				B(-77, 2, 15, 5, 4, 5, BLUE, Concrete),
				Cy(-64, 3.5, 16, 3.4, 7, DARK, Metal),
			},
		},
		{
			Id = "Fountain",
			Yaw = 15,
			Name = "Hero Fountain",
			Description = "A round fountain with a tall spray and two benches to rest on between rescues.",
			Pad = Vector2.new(-6, -9),
			PriceSeconds = 106,
			Pieces = {
				Cy(-6, 0.6, 2, 18, 1.2, STONE, Granite),
				Cy(-6, 1.3, 2, 15, 0.3, WATER, Plastic),
				Cy(-6, 3.8, 2, 2.6, 5.4, STONE, Granite),
				Cy(-6, 6.4, 2, 7, 0.8, STONE, Granite),
				Ball(-6, 8.6, 2, 3, 4, 3, WATER, Plastic),
				B(-17.5, 0.7, 2, 1.6, 1.4, 8, WOOD, Wood),
				B(5.5, 0.7, 2, 1.6, 1.4, 8, WOOD, Wood),
			},
		},
		{
			Id = "Banners",
			Yaw = -10,
			Name = "Hero Banners",
			Description = "Four tall flagpoles with red and blue hero banners flapping in the wind.",
			Pad = Vector2.new(10, 36),
			PriceSeconds = 122,
			Pieces = {
				Cy(-6, 7, 44, 0.7, 14, STEEL, Metal),
				B(-4.2, 11, 44, 3.4, 5, 0.2, RED, Fabric),
				Cy(0, 7, 41, 0.7, 14, STEEL, Metal),
				B(1.8, 11, 41, 3.4, 5, 0.2, BLUE, Fabric),
				Cy(5, 7, 43, 0.7, 14, STEEL, Metal),
				B(6.8, 11, 43, 3.4, 5, 0.2, RED, Fabric),
				Cy(10, 7, 40.5, 0.7, 14, STEEL, Metal),
				B(11.8, 11, 40.5, 3.4, 5, 0.2, BLUE, Fabric),
			},
		},
		{
			Id = "Comic",
			Yaw = 10,
			Name = "Comic Shop",
			Description = "A yellow comic book shop with a striped awning and a big speech bubble sign.",
			Pad = Vector2.new(-8, 58),
			PriceSeconds = 139,
			Pieces = {
				B(-24, 4, 56, 14, 8, 10, YELLOW, Concrete),
				B(-24, 8.4, 56, 15.4, 0.8, 11.4, RED, Metal),
				B(-24, 5.6, 62, 12, 0.5, 3, BLUE, Fabric),
				B(-24, 11, 56.6, 10, 4, 0.8, WHITE, Plastic),
			},
		},
		{
			Id = "Truck",
			Yaw = 24,
			Name = "Snack Truck",
			Description = "A yellow snack truck with a striped awning where the sidekicks grab their lunch.",
			Pad = Vector2.new(44, 19),
			PriceSeconds = 160,
			Pieces = {
				B(46, 1.3, 10, 15, 1.2, 5.2, DARK, Metal),
				B(44, 4.4, 10, 10, 5, 6, YELLOW, Metal),
				B(52, 3.4, 10, 4.4, 3.6, 5.6, BLUE, Metal),
				B(44, 7, 13.8, 8, 0.4, 2.6, RED, Fabric),
				B(44, 8, 10, 6, 1.4, 0.8, WHITE, Plastic),
				Cz(41.5, 1.2, 7.2, 2.4, 0.8, DARK, Plastic),
				Cz(41.5, 1.2, 12.8, 2.4, 0.8, DARK, Plastic),
				Cz(51, 1.2, 7.2, 2.4, 0.8, DARK, Plastic),
				Cz(51, 1.2, 12.8, 2.4, 0.8, DARK, Plastic),
			},
		},
		{
			Id = "Ring",
			Yaw = 18,
			Name = "Sparring Ring",
			Description = "A boxing ring with blue corner posts and red ropes for the sidekicks to train in.",
			Pad = Vector2.new(-20, 27),
			PriceSeconds = 183,
			Pieces = {
				B(-20, 0.75, 38, 13, 1.5, 13, NAVY, Plastic),
				B(-25.8, 4, 32.2, 0.8, 5, 0.8, BLUE, Metal),
				B(-14.2, 4, 32.2, 0.8, 5, 0.8, BLUE, Metal),
				B(-25.8, 4, 43.8, 0.8, 5, 0.8, RED, Metal),
				B(-14.2, 4, 43.8, 0.8, 5, 0.8, RED, Metal),
				B(-20, 4.4, 32.2, 11.6, 0.4, 0.4, RED, Fabric),
				B(-20, 4.4, 43.8, 11.6, 0.4, 0.4, RED, Fabric),
				B(-25.8, 4.4, 38, 0.4, 0.4, 11.6, RED, Fabric),
				B(-14.2, 4.4, 38, 0.4, 0.4, 11.6, RED, Fabric),
			},
		},
		{
			Id = "Searchlight",
			Yaw = 14,
			Name = "Signal Searchlight",
			Description = "A steel lattice tower holding a giant searchlight that calls the hero.",
			Pad = Vector2.new(-20, -22),
			PriceSeconds = 209,
			Pieces = {
				B(-8, 0.5, -28, 8, 1, 8, STEEL, Concrete),
				B(-10.4, 8.5, -30.4, 0.8, 15, 0.8, DARK, Metal),
				B(-5.6, 8.5, -30.4, 0.8, 15, 0.8, DARK, Metal),
				B(-10.4, 8.5, -25.6, 0.8, 15, 0.8, DARK, Metal),
				B(-5.6, 8.5, -25.6, 0.8, 15, 0.8, DARK, Metal),
				B(-8, 16.4, -28, 8, 0.8, 8, STEEL, Metal),
				B(-8, 19.4, -28, 5, 5, 5, DARK, Metal),
				Cz(-8, 19.4, -25, 4.6, 1.2, YELLOW, Plastic),
			},
		},
		{
			Id = "Dishes",
			Yaw = 10,
			Name = "Satellite Array",
			Description = "A control cabin with three satellite dishes that listen for calls for help.",
			Pad = Vector2.new(-48, -45),
			PriceSeconds = 240,
			Pieces = {
				B(-48, 2.5, -58, 9, 5, 6, WHITE, Concrete),
				Cy(-52.4, 3, -53, 1.4, 6, STEEL, Metal),
				Cz(-52.4, 7, -53, 5.4, 1.4, WHITE, Metal),
				Cy(-43.6, 3, -53, 1.4, 6, STEEL, Metal),
				Cz(-43.6, 7, -53, 5.4, 1.4, WHITE, Metal),
				Cy(-48, 6, -61, 1.4, 12, STEEL, Metal),
				Cz(-48, 11.5, -61, 5, 1.2, RED, Metal),
			},
		},
		{
			Id = "Newsroom",
			Yaw = -8,
			Name = "Daily Bonk Newsroom",
			Description = "A tall cream newspaper office with a news banner and a giant spinning globe on the roof.",
			Pad = Vector2.new(-87, 8),
			PriceSeconds = 274,
			Pieces = {
				B(-86, 9, -8, 12, 18, 12, CREAM, Concrete),
				B(-86, 20.5, -8, 9, 5, 9, STONE, Concrete),
				Ball(-86, 26.5, -8, 8, 8, 8, BLUE, Plastic),
				Cy(-86, 33, -8, 0.6, 5, STEEL, Metal),
				B(-86, 12, -1.6, 10, 3, 0.6, NAVY, Plastic),
				B(-86, 4.6, -0.6, 8, 0.4, 2, RED, Fabric),
			},
		},
		{
			Id = "Heli",
			Yaw = 20,
			Name = "Rescue Helicopter",
			Description = "A red and white rescue helicopter on a round helipad, ready for the next emergency.",
			Pad = Vector2.new(46, -16),
			PriceSeconds = 314,
			Pieces = {
				B(60, 0.25, -10, 22, 0.5, 22, DARK, Concrete),
				Ball(59, 4.2, -10, 10, 5, 5, RED, Metal),
				B(66.5, 4.8, -10, 8, 1, 1, RED, Metal),
				B(70, 6, -10, 0.6, 3, 1.6, WHITE, Metal),
				Cy(59, 7, -10, 0.8, 1.6, STEEL, Metal),
				B(59, 7.7, -10, 18, 0.3, 1.2, STEEL, Metal),
				B(59, 0.6, -12.2, 8, 0.4, 0.4, DARK, Metal),
				B(59, 0.6, -7.8, 8, 0.4, 0.4, DARK, Metal),
			},
		},
		{
			Id = "Coil",
			Yaw = 12,
			Name = "Lightning Coil",
			Description = "A tall power coil with glowing rings, a ball on top and four short pylons.",
			Pad = Vector2.new(76, -6),
			PriceSeconds = 360,
			Pieces = {
				B(86, 1, 4, 10, 2, 10, DARK, Concrete),
				Cy(86, 9, 4, 3.4, 14, STEEL, Metal),
				Cy(86, 6, 4, 7, 1.2, YELLOW, Metal),
				Cy(86, 10, 4, 6, 1.2, YELLOW, Metal),
				Cy(86, 14, 4, 5, 1.2, YELLOW, Metal),
				Ball(86, 18.5, 4, 6, 6, 6, CYAN, Plastic),
				B(82, 3, 0, 1.2, 6, 1.2, STEEL, Metal),
				B(90, 3, 8, 1.2, 6, 1.2, STEEL, Metal),
			},
		},
		{
			Id = "Vault",
			Yaw = -10,
			Name = "Villain Vault",
			Description = "A dark steel prison bunker with a huge round door, barred windows and watch posts.",
			Pad = Vector2.new(-30, -46),
			PriceSeconds = 412,
			Pieces = {
				B(-30, 4.5, -57, 16, 9, 12, DARK, Metal),
				B(-30, 9.4, -57, 17, 0.8, 13, STEEL, Metal),
				Cz(-30, 4, -50.7, 6.4, 0.8, STEEL, Metal),
				B(-36, 6, -50.8, 2.6, 2.6, 0.4, CYAN, Glass),
				B(-24, 6, -50.8, 2.6, 2.6, 0.4, CYAN, Glass),
				Cy(-38, 7, -51, 1.4, 14, STEEL, Metal),
				Cy(-22, 7, -51, 1.4, 14, STEEL, Metal),
				B(-38, 14.4, -51, 3, 1, 3, YELLOW, Plastic),
				B(-22, 14.4, -51, 3, 1, 3, YELLOW, Plastic),
			},
		},
		{
			Id = "Rocket",
			Yaw = -14,
			Name = "Hero Rocket",
			Description = "A rocket on its launch pad with swept fins and a steel gantry, ready to carry the hero to space.",
			Pad = Vector2.new(68, -27),
			PriceSeconds = 472,
			Pieces = {
				B(84, 0.4, -22, 14, 0.8, 14, DARK, Concrete),
				Cy(84, 11, -22, 5, 20, WHITE, Metal),
				Ball(84, 23.5, -22, 5, 6, 5, RED, Metal),
				B(84, 3.5, -22, 11, 5, 1, BLUE, Metal),
				B(84, 3.5, -22, 1, 5, 11, BLUE, Metal),
				B(79, 12, -22, 2.4, 24, 2.4, STEEL, Metal),
				B(81.4, 16, -22, 4, 0.8, 1.2, STEEL, Metal),
			},
		},
		{
			Id = "Statue",
			Yaw = 12,
			Name = "Hero Statue",
			Description = "A huge statue of the hero with a flowing red cape and a raised fist on a stone pedestal.",
			Pad = Vector2.new(-30, 8),
			RewardMult = 1.3,
			PriceSeconds = 540,
			Pieces = {
				B(-30, 1.5, -6, 14, 3, 14, STONE, Granite),
				B(-30, 5, -6, 9, 4, 9, STEEL, Granite),
				B(-30, 11, -6, 6, 8, 3.4, BLUE, Fabric),
				B(-30, 19.5, -6, 7, 9, 4.4, BLUE, Fabric),
				Ball(-30, 26, -6, 3.6, 3.6, 3.6, C(255, 205, 160), Plastic),
				B(-25.2, 26.5, -6, 1.8, 6.5, 1.8, BLUE, Fabric),
				Ball(-25.2, 31, -6, 2.2, 2.2, 2.2, C(255, 205, 160), Plastic),
				B(-30, 19.5, -8.6, 8, 10, 0.8, RED, Fabric),
			},
		},
		{
			Id = "Hall",
			Yaw = 6,
			Name = "Hall of Heroes",
			Description = "A grand stone hall with four columns, a dome and a statue gallery for the greatest heroes.",
			Pad = Vector2.new(-60, -44),
			RewardMult = 1.3,
			PriceSeconds = 618,
			Pieces = {
				B(-72, 0.6, -54, 30, 1.2, 18, STONE, Granite),
				B(-72, 6.8, -57, 24, 11.2, 10, WHITE, Concrete),
				Cy(-83, 6.8, -49.5, 1.8, 10.4, WHITE, Granite),
				Cy(-76, 6.8, -49.5, 1.8, 10.4, WHITE, Granite),
				Cy(-68, 6.8, -49.5, 1.8, 10.4, WHITE, Granite),
				Cy(-61, 6.8, -49.5, 1.8, 10.4, WHITE, Granite),
				B(-72, 12.6, -50, 28, 1.6, 5, BLUE, Granite),
				Ball(-72, 16, -57, 10, 8, 10, YELLOW, Metal),
			},
		},
		{
			Id = "Crystal",
			Yaw = 20,
			Name = "Power Crystal",
			Description = "A meteor crater with a cluster of huge blue power crystals that give the hero his strength.",
			Pad = Vector2.new(46, -42),
			RewardMult = 1.4,
			PriceSeconds = 708,
			Pieces = {
				Cy(50, 0.4, -54, 15, 0.8, ROCK, Slate),
				B(50, 7, -54, 3.6, 14, 3.6, CYAN, Glass),
				B(46, 4.5, -52, 2.6, 9, 2.6, BLUE, Glass),
				B(54, 5, -56, 3, 10, 3, CYAN, Glass),
				B(47, 2.2, -57, 2, 4.4, 2, BLUE, Glass),
				B(53, 2, -51, 1.8, 4, 1.8, CYAN, Glass),
				B(45, 1.2, -57, 3.2, 2.4, 3, ROCK, Slate),
				B(55, 1.4, -52, 3, 2.8, 3.4, ROCK, Slate),
			},
		},
		{
			Id = "Mech",
			Yaw = -22,
			Name = "Guardian Mech",
			Description = "A giant blue and yellow battle robot standing guard with shoulder cannons and glowing eyes.",
			Pad = Vector2.new(66, 52),
			PriceSeconds = 811,
			Pieces = {
				B(76.5, 1.2, 52, 4, 2.4, 6, DARK, Metal),
				B(83.5, 1.2, 52, 4, 2.4, 6, DARK, Metal),
				B(76.5, 6.5, 52, 2.4, 8.4, 2.4, STEEL, Metal),
				B(83.5, 6.5, 52, 2.4, 8.4, 2.4, STEEL, Metal),
				B(80, 11.4, 52, 9, 2.4, 5, DARK, Metal),
				B(80, 16.5, 52, 12, 8, 7, BLUE, Metal),
				B(73.5, 18.5, 52, 3.4, 4, 4.4, YELLOW, Metal),
				B(86.5, 18.5, 52, 3.4, 4, 4.4, YELLOW, Metal),
				B(72.4, 13.5, 52, 2.2, 8, 2.4, STEEL, Metal),
				B(87.6, 13.5, 52, 2.2, 8, 2.4, STEEL, Metal),
				B(80, 22.6, 52, 5, 3.2, 4.4, STEEL, Metal),
				B(80, 25.6, 52, 0.6, 3, 0.6, RED, Metal),
			},
		},
		{
			Id = "Shield",
			Yaw = 10,
			Name = "Mighty Shield",
			Description = "The showpiece: a gigantic round shield of red, white and blue with a golden star, standing on a rock.",
			Pad = Vector2.new(-66, -24),
			RewardMult = 2,
			PriceSeconds = 928,
			Pieces = {
				B(-80, 1.2, -30, 16, 2.4, 10, ROCK, Granite),
				B(-80, 4.2, -30, 6, 3.6, 4, STEEL, Metal),
				Cz(-80, 15, -30, 20, 2.2, RED, Metal),
				Cz(-80, 15, -29.2, 15, 2.8, WHITE, Metal),
				Cz(-80, 15, -28.4, 10, 3.4, BLUE, Metal),
				B(-80, 15, -27.4, 6, 6, 1.2, YELLOW, Metal),
			},
		},
	},
}

return theme
