--!strict
-- Theme of the Shiba of bay 14: Launch Pad (Config/DecorTypes -> Theme). 190 x 130: Astronaut Shiba stands on the mission-control
-- forecourt at the front left, a zig-zag walkway leads past a lunar rover, a dome observatory, a lander and a space shuttle to the
-- big launch platform at the back right with rocket and gantry. Parts are loose groups, most of them turned a little.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lamps and flames are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local GRASS = C(118, 156, 92)
local CONCRETE = C(152, 156, 162)
local DGREY = C(72, 78, 92)
local GRAVEL = C(172, 162, 140)
local ASPHALT = C(60, 62, 72)
local WHITE = C(238, 240, 246)
local OFFW = C(208, 213, 224)
local NAVY = C(30, 48, 100)
local ORANGE = C(240, 128, 36)
local RED = C(214, 52, 48)
local YELLOW = C(250, 205, 50)
local GOLD = C(226, 178, 66)
local SOLAR = C(38, 64, 136)
local RUST = C(176, 98, 62)
local MOON = C(176, 178, 184)
local MOONDARK = C(130, 132, 142)

local Plastic = Enum.Material.SmoothPlastic
local Metal = Enum.Material.Metal
local Concrete = Enum.Material.Concrete
local Grass = Enum.Material.Grass
local Slate = Enum.Material.Slate
local Rock = Enum.Material.Rock
local Pebble = Enum.Material.Pebble
local Foil = Enum.Material.Foil
local Glass = Enum.Material.Glass
local Fabric = Enum.Material.Fabric

-- Block centred at (x, y, z) with size (sx, sy, sz).
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

-- Cylinder lying along X: diameter d, length len.
local function Cx(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Cylinder lying along Z (a wheel seen from the side): diameter d, length len.
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
	Key = "LaunchPad",
	Name = "Launch Pad",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-60, 22), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(44, 50),
		Vector2.new(-4, 34),
		Vector2.new(-30, 20),
		Vector2.new(24, 2),
		Vector2.new(56, -22),
		Vector2.new(14, -46),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-60, 34),
	AutoPad = Vector2.new(-60, 10),
	Parts = {
		{
			Id = "Ground",
			Name = "Spaceport Grounds",
			Description = "Green field, a concrete launch apron, a crawler road, a landing target and a parking apron.",
			Pad = Vector2.new(-2, 54),
			PriceSeconds = 36,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, GRASS, Grass),
				B(62, 0.4, -44, 48, 0.2, 40, CONCRETE, Concrete),
				B(22, 0.4, -50, 52, 0.2, 9, GRAVEL, Pebble),
				B(-66, 0.4, 22, 26, 0.2, 42, CONCRETE, Concrete),
				B(0, 0.4, -24, 22, 0.2, 22, ASPHALT, Slate),
				B(76, 0.4, 52, 26, 0.2, 18, ASPHALT, Slate),
			},
		},
		{
			Id = "Control",
			Yaw = 6,
			Name = "Mission Control",
			Description = "The control centre behind the Shiba: big windows, a flight tower, a dish and a tall antenna.",
			Pad = Vector2.new(-72, 46),
			PriceSeconds = 41,
			RewardMult = 1.3,
			Pieces = {
				B(-81, 5.3, 22, 14, 10, 30, WHITE, Plastic),
				B(-73, 3.3, 22, 2.6, 6, 18, NAVY, Glass),
				B(-81, 10.6, 22, 15, 0.6, 31, NAVY, Plastic),
				Cy(-84, 15.9, 12, 5.6, 10, WHITE, Plastic),
				Cy(-84, 21.5, 12, 6.6, 1.2, NAVY, Plastic),
				Cy(-79, 12.5, 30, 1.6, 3.2, DGREY, Metal),
				Cx(-78, 16, 30, 9, 1.2, WHITE, Metal),
				Cy(-86, 21, 32, 0.9, 20.2, DGREY, Metal),
				B(-71.5, 5.8, 22, 3.4, 0.5, 12, ORANGE, Plastic),
			},
		},
		{
			Id = "Platform",
			Name = "Launch Platform",
			Description = "A round concrete launch platform with a blast wall, two floodlight masts and cable cabinets.",
			Pad = Vector2.new(76, -30),
			PriceSeconds = 48,
			Pieces = {
				B(62, 0.44, -44, 28, 0.28, 28, CONCRETE, Concrete),
				B(62, 2, -61, 22, 3.4, 1.6, CONCRETE, Concrete),
				Cy(49, 13.3, -58, 1.4, 26, DGREY, Metal),
				B(49, 27, -58, 4.4, 1.4, 1.6, YELLOW, Plastic),
				Cy(75, 13.3, -58, 1.4, 26, DGREY, Metal),
				B(75, 27, -58, 4.4, 1.4, 1.6, YELLOW, Plastic),
				B(54, 1.5, -57, 3, 2.4, 2, ORANGE, Metal),
				B(70, 1.5, -57, 3, 2.4, 2, ORANGE, Metal),
			},
		},
		{
			Id = "Rocket",
			Name = "Big Red Rocket",
			Description = "The star of the show: a tall white rocket with red fins, a red nose cone and a ring of black engines.",
			Pad = Vector2.new(50, -31),
			PriceSeconds = 55,
			RewardMult = 1.4,
			Pieces = {
				Cy(62, 2.2, -44, 7.6, 3.2, DGREY, Metal),
				B(62, 5, -44, 14, 6, 0.8, RED, Plastic),
				B(62, 5, -44, 0.8, 6, 14, RED, Plastic),
				Cy(62, 15, -44, 9, 22, WHITE, Plastic),
				Cy(62, 26.5, -44, 9.4, 1, NAVY, Plastic),
				Cy(62, 33, -44, 8, 12, WHITE, Plastic),
				Cy(62, 41, -44, 6.4, 4, RED, Plastic),
				Cy(62, 44.5, -44, 3.6, 3, RED, Plastic),
				Cy(62, 47, -44, 0.8, 2, DGREY, Metal),
			},
		},
		{
			Id = "Sign",
			Yaw = -14,
			Name = "Countdown Board",
			Description = "A big scoreboard sign that counts down to the next bonk. T minus ten!",
			Pad = Vector2.new(-24, 61),
			PriceSeconds = 63,
			Pieces = {
				B(-33, 3.8, 52, 1.4, 7, 1.4, DGREY, Metal),
				B(-15, 3.8, 52, 1.4, 7, 1.4, DGREY, Metal),
				B(-24, 12.3, 52, 26, 10, 1.4, NAVY, Plastic),
				B(-24, 18, 52, 28, 0.8, 2.4, ORANGE, Plastic),
				B(-34, 19.4, 52, 1.6, 1.2, 1.6, YELLOW, Plastic),
				B(-14, 19.4, 52, 1.6, 1.2, 1.6, YELLOW, Plastic),
			},
		},
		{
			Id = "Gantry",
			Name = "Service Gantry",
			Description = "An orange steel tower with three platforms, swing arms that reach the rocket and a beacon on top.",
			Pad = Vector2.new(38, -50),
			PriceSeconds = 72,
			Pieces = {
				B(50, 0.9, -44, 9, 0.8, 9, CONCRETE, Concrete),
				B(47, 20.8, -47, 0.9, 39, 0.9, ORANGE, Metal),
				B(53, 20.8, -47, 0.9, 39, 0.9, ORANGE, Metal),
				B(47, 20.8, -41, 0.9, 39, 0.9, ORANGE, Metal),
				B(53, 20.8, -41, 0.9, 39, 0.9, ORANGE, Metal),
				B(50, 13, -44, 7.4, 0.5, 7.4, DGREY, Metal),
				B(50, 25, -44, 7.4, 0.5, 7.4, DGREY, Metal),
				B(50, 37, -44, 7.4, 0.5, 7.4, DGREY, Metal),
				B(55.2, 14.2, -44, 5.6, 1.2, 1.8, ORANGE, Metal),
				B(55.2, 26.2, -44, 5.6, 1.2, 1.8, ORANGE, Metal),
				B(55.2, 36.2, -44, 5.6, 1.2, 1.8, ORANGE, Metal),
				Cy(50, 43, -44, 0.6, 5, DGREY, Metal),
			},
		},
		{
			Id = "Rover",
			Yaw = 28,
			Name = "Moon Rover",
			Description = "A six-wheel-style moon buggy with a cargo box, a mast and a little dish.",
			Pad = Vector2.new(-56, 42),
			PriceSeconds = 83,
			Pieces = {
				B(-48, 2.9, 44, 9, 1.2, 5.4, OFFW, Plastic),
				Cz(-51.5, 1.9, 40.9, 3.2, 1.2, DGREY, Plastic),
				Cz(-44.5, 1.9, 40.9, 3.2, 1.2, DGREY, Plastic),
				Cz(-51.5, 1.9, 47.1, 3.2, 1.2, DGREY, Plastic),
				Cz(-44.5, 1.9, 47.1, 3.2, 1.2, DGREY, Plastic),
				B(-50, 4.4, 44, 3, 1.8, 3.2, ORANGE, Plastic),
				Cy(-45, 5.8, 44, 0.5, 4.6, DGREY, Metal),
				Ball(-45, 8.6, 44, 3.2, 0.9, 3.2, WHITE, Metal),
			},
		},
		{
			Id = "Tanks",
			Yaw = -12,
			Name = "Fuel Tanks",
			Description = "Two big white fuel spheres on stands, a long bullet tank and an orange pipe between them.",
			Pad = Vector2.new(-16, -26),
			PriceSeconds = 95,
			Pieces = {
				Cy(-43, 2, -21, 4, 3.4, DGREY, Metal),
				Cy(-29, 2, -21, 4, 3.4, DGREY, Metal),
				Ball(-43, 9.2, -21, 11, 11, 11, WHITE, Metal),
				Ball(-29, 9.2, -21, 11, 11, 11, WHITE, Metal),
				Cx(-36, 3, -21, 0.9, 10, ORANGE, Metal),
				Cx(-36, 2.6, -31, 4.6, 20, WHITE, Metal),
				B(-41, 1.4, -31, 1.6, 2.2, 5, DGREY, Metal),
				B(-31, 1.4, -31, 1.6, 2.2, 5, DGREY, Metal),
			},
		},
		{
			Id = "Radar",
			Yaw = 18,
			Name = "Dish Array",
			Description = "Two big radar dishes that listen to the stars, plus a small control cabin and a mast.",
			Pad = Vector2.new(-68, -5),
			PriceSeconds = 109,
			Pieces = {
				B(-82, 0.44, -8, 11, 0.28, 11, CONCRETE, Concrete),
				Cy(-82, 4.4, -8, 3, 7.6, WHITE, Metal),
				B(-82, 9, -8, 5, 1.6, 2.4, DGREY, Metal),
				Cx(-82, 13.4, -8, 11, 1.2, WHITE, Metal),
				B(-70, 0.44, -22, 9, 0.28, 9, CONCRETE, Concrete),
				Cy(-70, 3.8, -22, 2.6, 6.4, WHITE, Metal),
				B(-70, 7.7, -22, 4.4, 1.4, 2.2, DGREY, Metal),
				Cx(-70, 11.4, -22, 9, 1.2, WHITE, Metal),
				B(-84, 2.6, -22, 6, 4.6, 5, OFFW, Plastic),
				Ball(-84, 6.2, -22, 2.6, 0.8, 2.6, WHITE, Metal),
				Cy(-76, 6, -14, 0.5, 11.4, DGREY, Metal),
			},
		},
		{
			Id = "Cafe",
			Yaw = -22,
			Name = "Astro Cafe",
			Description = "A little diner with a red roof, three umbrella tables and a rocket sign on a pole.",
			Pad = Vector2.new(62, 56),
			PriceSeconds = 126,
			Pieces = {
				B(76, 3.2, 50, 14, 5.8, 8, WHITE, Plastic),
				B(76, 6.5, 50, 15, 0.8, 9, RED, Plastic),
				B(76, 5.4, 55.4, 12, 0.4, 3, ORANGE, Fabric),
				Cy(70, 2.6, 58.5, 0.5, 4.6, DGREY, Metal),
				Cy(76, 2.6, 58.5, 0.5, 4.6, DGREY, Metal),
				Cy(82, 2.6, 58.5, 0.5, 4.6, DGREY, Metal),
				Cy(70, 5, 58.5, 5, 0.4, RED, Fabric),
				Cy(76, 5, 58.5, 5, 0.4, ORANGE, Fabric),
				Cy(82, 5, 58.5, 5, 0.4, RED, Fabric),
				Cy(84.5, 4.55, 46, 0.6, 8.5, DGREY, Metal),
				Cy(84.5, 11.5, 46, 2.4, 5.4, WHITE, Plastic),
				Cy(84.5, 15.1, 46, 1.2, 1.8, RED, Plastic),
			},
		},
		{
			Id = "Lander",
			Yaw = 15,
			Name = "Lunar Lander",
			Description = "A gold-foil moon lander on four legs with a white crew cabin, two fuel tanks and an antenna.",
			Pad = Vector2.new(-12, -12),
			PriceSeconds = 144,
			Pieces = {
				Cy(-6, 0.55, -30, 2.8, 0.5, DGREY, Metal),
				Cy(6, 0.55, -30, 2.8, 0.5, DGREY, Metal),
				Cy(-6, 0.55, -18, 2.8, 0.5, DGREY, Metal),
				Cy(6, 0.55, -18, 2.8, 0.5, DGREY, Metal),
				Cy(-3.3, 3, -27.3, 0.9, 5.4, OFFW, Metal),
				Cy(3.3, 3, -27.3, 0.9, 5.4, OFFW, Metal),
				Cy(-3.3, 3, -20.7, 0.9, 5.4, OFFW, Metal),
				Cy(3.3, 3, -20.7, 0.9, 5.4, OFFW, Metal),
				B(0, 7.2, -24, 8, 3, 8, GOLD, Foil),
				B(0, 11, -24, 5.6, 4.6, 5.6, WHITE, Plastic),
				Ball(-3.9, 10.6, -24, 3, 3, 3, GOLD, Foil),
				Ball(3.9, 10.6, -24, 3, 3, 3, GOLD, Foil),
				Cy(0, 14.6, -24, 0.4, 2.6, DGREY, Metal),
			},
		},
		{
			Id = "Dome",
			Yaw = -8,
			Name = "Dome Observatory",
			Description = "A white observatory with a round dome, a slit for the big telescope, an annex and a porch.",
			Pad = Vector2.new(-54, -2),
			PriceSeconds = 166,
			Pieces = {
				Cy(-40, 3.9, 0, 14, 7.2, WHITE, Plastic),
				Ball(-40, 7.5, 0, 14, 14, 14, OFFW, Plastic),
				B(-32, 2.5, 0, 4, 4.4, 6, OFFW, Plastic),
				B(-40, 0.9, 7.3, 4, 1.2, 2.6, CONCRETE, Concrete),
				Cy(-32, 6.5, 0, 0.5, 3.6, DGREY, Metal),
			},
		},
		{
			Id = "Solar",
			Yaw = 26,
			Name = "Solar Field",
			Description = "Three long rows of blue solar panels with a battery box and a power hut.",
			Pad = Vector2.new(62, 36),
			PriceSeconds = 191,
			Pieces = {
				B(78, 2.4, 24.2, 18, 4.2, 4.4, SOLAR, Glass),
				B(78, 2.4, 30, 18, 4.2, 4.4, SOLAR, Glass),
				B(78, 2.4, 35.8, 18, 4.2, 4.4, SOLAR, Glass),
				B(85.5, 1.8, 19.5, 3, 3, 3, OFFW, Plastic),
				B(70.5, 1.2, 19.5, 3, 2, 2.4, YELLOW, Plastic),
			},
		},
		{
			Id = "Hangar",
			Yaw = -7,
			Name = "Assembly Hangar",
			Description = "A huge white hangar with a giant door, a navy roof, a little office and a flag.",
			Pad = Vector2.new(4, -38),
			PriceSeconds = 219,
			Pieces = {
				B(-22, 11.3, -50, 28, 22, 17, WHITE, Plastic),
				B(-22, 22.8, -50, 29, 1, 18, NAVY, Plastic),
				B(-22, 9.3, -41, 12, 18, 0.8, DGREY, Metal),
				B(-12.5, 3.3, -41, 8, 6, 3.6, OFFW, Plastic),
				B(-30, 24, -50, 4, 1.2, 4, DGREY, Metal),
				B(-14, 24, -50, 4, 1.2, 4, DGREY, Metal),
				Cy(-10, 27, -54, 0.5, 7.4, DGREY, Metal),
				B(-8.6, 29.4, -54, 2.4, 1.6, 0.2, RED, Fabric),
			},
		},
		{
			Id = "Capsule",
			Yaw = 24,
			Name = "Return Capsule",
			Description = "A scorched crew capsule that just landed, with its big striped parachute lying on the grass.",
			Pad = Vector2.new(16, -9),
			PriceSeconds = 252,
			Pieces = {
				Ball(16, 0.44, -21, 14, 0.28, 11, WHITE, Fabric),
				Ball(16, 0.5, -21, 9, 0.16, 7, ORANGE, Fabric),
				Cy(25, 0.95, -18, 6.4, 1.3, DGREY, Metal),
				Cy(25, 3.1, -18, 5.6, 3, WHITE, Plastic),
				Cy(25, 5.5, -18, 2.8, 1.8, WHITE, Plastic),
				Cy(25, 7.2, -18, 0.3, 1.6, DGREY, Metal),
			},
		},
		{
			Id = "Centrifuge",
			Yaw = -10,
			Name = "Training Centrifuge",
			Description = "A tall whirling arm with a crew gondola and a counterweight. Hold on to your helmet!",
			Pad = Vector2.new(46, 10),
			PriceSeconds = 290,
			Pieces = {
				B(45, 0.44, 25, 26, 0.28, 26, CONCRETE, Concrete),
				Cy(45, 2, 25, 9, 2.4, DGREY, Metal),
				Cy(45, 10.2, 25, 4.6, 14, WHITE, Plastic),
				Cy(45, 18.4, 25, 6.4, 2.4, NAVY, Plastic),
				B(45, 20.3, 25, 24, 1.4, 1.8, ORANGE, Metal),
				B(35.8, 17.6, 25, 4.6, 3.6, 3.6, WHITE, Plastic),
				B(55.4, 18, 25, 3.4, 3.4, 3.4, RED, Metal),
			},
		},
		{
			Id = "Habitat",
			Yaw = 9,
			Name = "Mars Habitat",
			Description = "Two white domes joined by a tunnel on rusty red ground, with an airlock, tanks and red rocks.",
			Pad = Vector2.new(68, -11),
			PriceSeconds = 333,
			RewardMult = 1.4,
			Pieces = {
				B(78, 0.44, 2, 24, 0.28, 24, RUST, Slate),
				Ball(72, 4.1, 2, 11, 7.6, 11, WHITE, Plastic),
				Ball(85, 3.7, 2, 9, 6.8, 9, WHITE, Plastic),
				B(78.8, 2.4, 2, 6, 3.6, 3.2, OFFW, Plastic),
				B(78.5, 2.5, -5, 4, 4.4, 4, DGREY, Metal),
				Cy(72, 10.1, 2, 0.4, 4.4, DGREY, Metal),
				Ball(68, 1, 9, 2.6, 1.8, 2.2, RUST, Rock),
				Ball(88, 1.1, -6, 3, 2, 2.6, RUST, Rock),
				Ball(82, 0.9, 10, 2, 1.4, 2, RUST, Rock),
				Cy(71.5, 2, -4, 2, 3.4, WHITE, Metal),
				Cy(74, 2, -4.4, 2, 3.4, ORANGE, Metal),
			},
		},
		{
			Id = "Crater",
			Yaw = -12,
			Name = "Moon Garden",
			Description = "A grey moon crater with big boulders and a small flag planted in the middle.",
			Pad = Vector2.new(84, -34),
			PriceSeconds = 383,
			Pieces = {
				B(85, 0.4, -48, 14, 0.2, 14, MOON, Slate),
				B(85, 0.54, -48, 9, 0.08, 9, MOONDARK, Slate),
				Ball(80, 1.4, -44, 3.4, 2.6, 3, MOON, Rock),
				Ball(90, 1.6, -52, 3.8, 3, 3.4, MOON, Rock),
				Ball(81.5, 1.2, -53, 2.4, 1.8, 2.4, MOONDARK, Rock),
				Ball(88.5, 1, -43.5, 2, 1.6, 2, MOON, Rock),
				Cy(85, 8, -48, 0.4, 15.4, WHITE, Metal),
				B(86.6, 14, -48, 3.2, 2.2, 0.2, ORANGE, Fabric),
				Ball(85, 16, -48, 0.9, 0.9, 0.9, GOLD, Metal),
			},
		},
		{
			Id = "Shuttle",
			Yaw = 11,
			Name = "Space Shuttle",
			Description = "A white space shuttle resting on its stand, with delta wings, a tail fin and three engines.",
			Pad = Vector2.new(-60, -26),
			PriceSeconds = 440,
			RewardMult = 1.4,
			Pieces = {
				B(-62, 1.1, -47, 24, 1.6, 10, DGREY, Concrete),
				Cy(-67, 2.75, -47, 2.4, 1.7, DGREY, Metal),
				Cy(-56, 2.75, -47, 2.4, 1.7, DGREY, Metal),
				Cx(-63.5, 6.6, -47, 6, 25, WHITE, Plastic),
				Ball(-50.5, 6.6, -47, 8, 5.6, 5.6, DGREY, Plastic),
				B(-62, 5.6, -47, 13, 0.8, 26, WHITE, Plastic),
				B(-73, 12.8, -47, 6, 6.4, 0.9, WHITE, Plastic),
				Cx(-77.4, 7.4, -47, 2.4, 2.8, DGREY, Metal),
				Cx(-77.4, 5.4, -45.2, 2.4, 2.8, DGREY, Metal),
				Cx(-77.4, 5.4, -48.8, 2.4, 2.8, DGREY, Metal),
			},
		},
		{
			Id = "Station",
			Yaw = -16,
			Name = "Orbital Station",
			Description = "The showpiece: a model of a space station high on a pylon, with long modules and four solar wings.",
			Pad = Vector2.new(22, 14),
			PriceSeconds = 506,
			RewardMult = 1.7,
			Pieces = {
				Cy(14, 1, 24, 10, 1.4, CONCRETE, Concrete),
				Cy(14, 10.7, 24, 3, 18, WHITE, Plastic),
				Ball(14, 21, 24, 5, 5, 5, OFFW, Metal),
				Cx(14, 21, 24, 4, 26, WHITE, Metal),
				Cz(14, 21, 24, 3.6, 14, GOLD, Foil),
				B(14, 24.2, 24, 32, 0.9, 0.9, DGREY, Metal),
				B(3.5, 24.2, 24, 5, 0.3, 12, SOLAR, Glass),
				B(9.5, 24.2, 24, 5, 0.3, 12, SOLAR, Glass),
				B(18.5, 24.2, 24, 5, 0.3, 12, SOLAR, Glass),
				B(24.5, 24.2, 24, 5, 0.3, 12, SOLAR, Glass),
			},
		},
	},
}

return theme
