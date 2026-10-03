--!strict
-- Theme of the Shiba of bay 13: Robot Factory (Config/DecorTypes -> Theme). 190 x 130: Robot Shiba stands on a round steel turntable in
-- the middle of the plot, an assembly hall and a smokestack fill the back right, a giant robot guards the back left, a winding walkway
-- passes the turntable and runs under a pipe gateway. Stage frame: +X right, -Z deeper, +Z toward the road.
-- No glow: lamps, screens and sparks are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local FLOOR = C(86, 90, 98)
local PLATE = C(108, 112, 120)
local STEEL = C(150, 160, 176)
local DARK = C(52, 58, 70)
local CONCRETE = C(122, 124, 130)
local YELLOW = C(255, 200, 30)
local ORANGE = C(255, 120, 30)
local CYAN = C(110, 215, 240)
local GLASS = C(150, 210, 232)
local BRICK = C(150, 82, 62)
local WHITE = C(226, 230, 238)
local RUST = C(150, 92, 56)
local DIRT = C(104, 88, 70)
local CRATE = C(196, 154, 92)
local RED = C(214, 60, 52)

local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Concrete = Enum.Material.Concrete
local Brick = Enum.Material.Brick
local Diamond = Enum.Material.DiamondPlate
local Glass = Enum.Material.Glass
local Corroded = Enum.Material.CorrodedMetal
local Planks = Enum.Material.WoodPlanks

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

-- Cylinder lying along X: length len, diameter d.
local function Cx(x: number, y: number, z: number, len: number, d: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Cylinder lying along Z (a gear wheel facing the road): diameter d, thickness len.
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

-- Where the Shiba's turntable is.
local SX, SZ = -4, -14

local theme: DecorTypes.Theme = {
	Key = "RobotFactory",
	Name = "Robot Factory",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(SX, SZ), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(52, 46),
		Vector2.new(6, 14),
		Vector2.new(-44, -14),
		Vector2.new(-34, -48),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-16, -14),
	AutoPad = Vector2.new(8, -14),
	Parts = {
		{
			Id = "Floor",
			Name = "Factory Floor",
			Description = "Dark concrete with hazard lines, steel plates and a big round turntable for the Robot Shiba.",
			Pad = Vector2.new(-30, 58),
			PriceSeconds = 32,
			Pieces = {
				B(0, 0.15, 0, 190, 0.3, 130, FLOOR, Concrete),
				B(SX, 0.36, SZ, 26, 0.12, 26, STEEL, Metal),
				B(SX, 0.48, SZ, 17, 0.12, 17, YELLOW, Plastic),
				B(60, 0.36, -40, 56, 0.12, 40, PLATE, Concrete),
				B(20, 0.36, -34, 26, 0.12, 22, PLATE, Concrete),
				B(-76, 0.36, -12, 30, 0.12, 30, PLATE, Concrete),
				B(-58, 0.36, 10, 28, 0.12, 22, DIRT, Concrete),
				B(76, 0.36, 20, 24, 0.12, 24, PLATE, Concrete),
			},
		},
		{
			Id = "Hall",
			Name = "Assembly Hall",
			Description = "A big steel hall with a saw-tooth roof, glass skylights and a wide roller door.",
			Pad = Vector2.new(60, -22),
			Yaw = 8,
			PriceSeconds = 37,
			RewardMult = 1.3,
			Pieces = {
				B(60, 7, -55.4, 46, 14, 1.2, STEEL, Metal),
				B(37.6, 7, -42, 1.2, 14, 28, STEEL, Metal),
				B(82.4, 7, -42, 1.2, 14, 28, STEEL, Metal),
				B(43.5, 7, -28.6, 13, 14, 1.2, STEEL, Metal),
				B(74.5, 7, -28.6, 17, 14, 1.2, STEEL, Metal),
				B(58, 12, -28.6, 16, 4, 1.2, DARK, Metal),
				B(60, 14.4, -42, 46.8, 0.8, 28.8, DARK, Metal),
				B(46, 16.2, -42, 10, 3.6, 26, GLASS, Glass),
				B(60, 16.2, -42, 10, 3.6, 26, GLASS, Glass),
				B(74, 16.2, -42, 10, 3.6, 26, GLASS, Glass),
				B(80, 16.4, -52, 3.6, 4, 3.6, STEEL, Metal),
			},
		},
		{
			Id = "Sign",
			Name = "Get Bonked Sign",
			Description = "A giant dark billboard with bright BONK letters, standing on two steel legs.",
			Pad = Vector2.new(-60, 58),
			Yaw = -12,
			PriceSeconds = 42,
			Pieces = {
				B(-72.5, 0.5, 50, 3, 1, 3, CONCRETE, Concrete),
				B(-47.5, 0.5, 50, 3, 1, 3, CONCRETE, Concrete),
				Cy(-72.5, 5.5, 50, 1.4, 9, STEEL, Metal),
				Cy(-47.5, 5.5, 50, 1.4, 9, STEEL, Metal),
				B(-60, 8.6, 50, 28, 0.4, 2.4, DARK, Diamond),
				B(-60, 13.5, 50, 30, 9, 1.2, DARK, Metal),
				B(-60, 18.4, 50, 31, 0.8, 1.6, YELLOW, Metal),
			},
		},
		{
			Id = "Conveyor",
			Name = "Conveyor Line",
			Description = "A long belt with yellow rails that carries crates and little robots away from the hall.",
			Pad = Vector2.new(44, 4),
			Yaw = 18,
			PriceSeconds = 49,
			Pieces = {
				B(44, 1.3, -8, 36, 0.8, 4, DARK, Metal),
				B(44, 1.8, -8, 36, 0.3, 3.2, PLATE, Plastic),
				B(44, 2.4, -6, 36, 0.7, 0.5, YELLOW, Metal),
				B(44, 2.4, -10, 36, 0.7, 0.5, YELLOW, Metal),
				B(28.5, 0.5, -8, 1.2, 1, 3.6, DARK, Metal),
				B(44, 0.5, -8, 1.2, 1, 3.6, DARK, Metal),
				B(59.5, 0.5, -8, 1.2, 1, 3.6, DARK, Metal),
				B(33, 3.4, -8, 2.6, 2.6, 2.6, CRATE, Planks),
				B(39, 3.4, -8, 2.6, 2.6, 2.6, ORANGE, Planks),
				B(50, 3.5, -8, 2, 2.8, 2, STEEL, Metal),
				B(56, 3.5, -8, 2, 2.8, 2, STEEL, Metal),
			},
		},
		{
			Id = "Welder",
			Name = "Robot Arm Cell",
			Description = "A yellow robot arm inside a safety cage, welding sparks off a steel table.",
			Pad = Vector2.new(64, 22),
			Yaw = -22,
			PriceSeconds = 56,
			Pieces = {
				B(76, 0.2, 20, 14, 0.4, 14, DARK, Diamond),
				Cy(69.3, 4.5, 13.3, 0.7, 9, STEEL, Metal),
				Cy(82.7, 4.5, 13.3, 0.7, 9, STEEL, Metal),
				Cy(69.3, 4.5, 26.7, 0.7, 9, STEEL, Metal),
				Cy(82.7, 4.5, 26.7, 0.7, 9, STEEL, Metal),
				B(76, 9.3, 13.3, 14, 0.6, 0.6, YELLOW, Metal),
				B(76, 9.3, 26.7, 14, 0.6, 0.6, YELLOW, Metal),
				B(69.3, 9.3, 20, 0.6, 0.6, 14, YELLOW, Metal),
				B(82.7, 9.3, 20, 0.6, 0.6, 14, YELLOW, Metal),
				Cy(76, 1.4, 17, 4, 2.4, DARK, Metal),
				Cy(76, 4, 17, 1.8, 3.6, YELLOW, Metal),
				B(76, 6.4, 18.4, 1.3, 1.3, 5, YELLOW, Metal, rot(-35, 0, 0)),
				B(76, 7.2, 21.6, 1.1, 1.1, 4, YELLOW, Metal, rot(25, 0, 0)),
				B(76, 2.2, 23.6, 5, 3.6, 3, STEEL, Metal),
			},
		},
		{
			Id = "Smokestack",
			Name = "Smokestack",
			Description = "A tall brick chimney with white and red bands puffing grey smoke.",
			Pad = Vector2.new(31, -53),
			Yaw = 6,
			PriceSeconds = 65,
			Pieces = {
				B(18, 1.5, -54, 10, 3, 10, CONCRETE, Concrete),
				Cy(18, 16.5, -54, 5, 27, BRICK, Brick),
				Cy(18, 30.4, -54, 6.4, 1.2, DARK, Metal),
				Ball(18, 34, -54, 6, 5, 6, C(170, 172, 178), Plastic),
				Ball(20, 39, -54, 7, 5.6, 7, C(190, 192, 198), Plastic),
			},
		},
		{
			Id = "Silos",
			Name = "Storage Tanks",
			Description = "Two tall tanks with hazard bands, a ladder walkway and a round gas sphere on legs.",
			Pad = Vector2.new(-76, 6),
			Yaw = 14,
			PriceSeconds = 75,
			Pieces = {
				Cy(-82, 7.5, -5, 7, 15, STEEL, Metal),
				Cy(-82, 7.5, -19, 7, 15, STEEL, Metal),
				B(-82, 15.4, -12, 1, 0.5, 14, DARK, Diamond),
				Ball(-69, 9, -12, 10, 10, 10, WHITE, Metal),
				Cy(-72.2, 2.2, -15.2, 0.9, 4.4, DARK, Metal),
				Cy(-65.8, 2.2, -15.2, 0.9, 4.4, DARK, Metal),
				Cy(-72.2, 2.2, -8.8, 0.9, 4.4, DARK, Metal),
				Cy(-65.8, 2.2, -8.8, 0.9, 4.4, DARK, Metal),
				Cy(-75, 7.5, -12, 0.8, 15, ORANGE, Metal),
			},
		},
		{
			Id = "Booth",
			Name = "Control Booth",
			Description = "A glass booth on stilts where the foreman watches the line, with a little staircase.",
			Pad = Vector2.new(-76, 34),
			Yaw = -16,
			PriceSeconds = 86,
			Pieces = {
				Cy(-83, 2, 20, 1, 4, DARK, Metal),
				Cy(-73, 2, 20, 1, 4, DARK, Metal),
				Cy(-83, 2, 28, 1, 4, DARK, Metal),
				Cy(-73, 2, 28, 1, 4, DARK, Metal),
				B(-78, 4.25, 24, 12, 0.5, 10, DARK, Diamond),
				B(-78, 6.8, 24, 10, 4.6, 8, GLASS, Glass),
				B(-78, 9.4, 24, 11.4, 0.6, 9.4, YELLOW, Metal),
				Cy(-80, 11.5, 24, 0.4, 3.4, STEEL, Metal),
				B(-70.6, 2.3, 24, 1.8, 4.6, 4, STEEL, Metal),
				B(-69.6, 1.5, 24, 1.8, 3, 4, STEEL, Metal),
				B(-68.6, 0.7, 24, 1.8, 1.4, 4, STEEL, Metal),
			},
		},
		{
			Id = "Gears",
			Name = "Giant Cogwheels",
			Description = "Two huge meshing cogwheels standing on a concrete plinth, turning slowly for show.",
			Pad = Vector2.new(-36, 42),
			Yaw = 20,
			PriceSeconds = 99,
			Pieces = {
				B(-36, 1, 32, 24, 2, 6, CONCRETE, Concrete),
				B(-40, 5, 32, 2.4, 6, 3, DARK, Metal),
				B(-29, 5, 32, 2.4, 6, 3, DARK, Metal),
				Cz(-40, 9.8, 32, 14.4, 2, STEEL, Metal),
				Cz(-28.5, 7.4, 32, 8.4, 2, YELLOW, Metal),
				Cz(-40, 9.8, 33.4, 3, 1, DARK, Metal),
				Cz(-28.5, 7.4, 33.4, 2, 1, DARK, Metal),
			},
		},
		{
			Id = "Statue",
			Name = "Robot Statue",
			Description = "A friendly steel robot waving from its plinth in front of the factory.",
			Pad = Vector2.new(6, 53),
			Yaw = -12,
			PriceSeconds = 114,
			Pieces = {
				B(12, 1.5, 44, 10, 3, 10, CONCRETE, Concrete),
				B(10, 5.5, 44, 2.6, 5, 3.2, DARK, Metal),
				B(14, 5.5, 44, 2.6, 5, 3.2, DARK, Metal),
				B(12, 11.4, 44, 8, 6.8, 5, STEEL, Metal),
				B(12, 17.2, 44, 5, 4.4, 4.4, STEEL, Metal),
				B(6.8, 11.6, 44, 2, 6.2, 2.4, STEEL, Metal),
				B(17.2, 13, 44, 2, 6.2, 2.4, STEEL, Metal),
				Cy(12, 21, 44, 0.5, 3, DARK, Metal),
			},
		},
		{
			Id = "Generator",
			Name = "Tesla Coil Yard",
			Description = "Three humming generator towers topped with big shiny spheres and a control box.",
			Pad = Vector2.new(50, 34),
			Yaw = 6,
			PriceSeconds = 131,
			RewardMult = 1.5,
			Pieces = {
				B(50, 0.6, 24, 14, 1.2, 10, DARK, Diamond),
				Cy(45, 5, 24, 2.4, 8, STEEL, Metal),
				Cy(50, 7, 24, 2.8, 12, STEEL, Metal),
				Cy(55, 5, 24, 2.4, 8, STEEL, Metal),
				Ball(45, 10.4, 24, 4.4, 4.4, 4.4, CYAN, Plastic),
				Ball(50, 14.4, 24, 5.4, 5.4, 5.4, CYAN, Plastic),
				Ball(55, 10.4, 24, 4.4, 4.4, 4.4, CYAN, Plastic),
				B(55.8, 2.7, 27, 3, 3, 2.4, YELLOW, Metal),
			},
		},
		{
			Id = "Forklift",
			Name = "Forklift Depot",
			Description = "A yellow forklift with a loaded pallet, a stack of crates and some oil drums.",
			Pad = Vector2.new(-10, 52),
			Yaw = 30,
			PriceSeconds = 151,
			Pieces = {
				B(-14, 2.4, 38, 6, 2.6, 3.6, YELLOW, Metal),
				B(-15, 6.4, 38, 3.6, 0.4, 3.4, DARK, Metal),
				Cy(-16.4, 4.4, 36.4, 0.4, 3.6, DARK, Metal),
				Cy(-16.4, 4.4, 39.6, 0.4, 3.6, DARK, Metal),
				B(-10.6, 4.6, 38, 0.8, 9.2, 3, DARK, Metal),
				B(-9, 0.7, 38, 3.2, 0.5, 3, DARK, Metal),
				B(-8.4, 2.2, 38, 2.4, 2.4, 2.4, CRATE, Planks),
				B(-3, 1.2, 33.4, 3, 2.4, 3, CRATE, Planks),
				B(-3, 3.6, 33.4, 3, 2.4, 3, ORANGE, Planks),
				B(-3.5, 1.2, 42.6, 2.4, 2.4, 2.4, CRATE, Planks),
				Cy(-17.5, 1.6, 33, 2.2, 3.2, RED, Metal),
				Cy(-15, 1.6, 32.4, 2.2, 3.2, RED, Metal),
			},
		},
		{
			Id = "Pipes",
			Name = "Pipe Gateway",
			Description = "A great pipe bridge arching over the walkway on two steel legs, with valve wheels.",
			Pad = Vector2.new(-26, -30),
			Yaw = -16,
			PriceSeconds = 173,
			Pieces = {
				B(-49, 7, -31, 2, 14, 2.4, STEEL, Metal),
				B(-29, 7, -31, 2, 14, 2.4, STEEL, Metal),
				B(-49, 0.5, -31, 3.4, 1, 3.4, CONCRETE, Concrete),
				B(-29, 0.5, -31, 3.4, 1, 3.4, CONCRETE, Concrete),
				B(-39, 14.4, -31, 22, 1.4, 2.8, DARK, Metal),
				Cx(-39, 11.4, -32.4, 22, 1.8, ORANGE, Metal),
				Cx(-39, 11.4, -29.6, 22, 1.8, STEEL, Metal),
				Cx(-39, 9, -31, 22, 1.2, YELLOW, Metal),
			},
		},
		{
			Id = "Crane",
			Name = "Gantry Crane",
			Description = "A tall gantry crane on four legs lifting a red container with a swinging hook.",
			Pad = Vector2.new(80, 5.5),
			Yaw = 9,
			PriceSeconds = 199,
			Pieces = {
				B(72.8, 9, -20, 1.6, 18, 1.6, YELLOW, Metal),
				B(87.2, 9, -20, 1.6, 18, 1.6, YELLOW, Metal),
				B(72.8, 9, 0, 1.6, 18, 1.6, YELLOW, Metal),
				B(87.2, 9, 0, 1.6, 18, 1.6, YELLOW, Metal),
				B(72.8, 18.6, -10, 1.6, 1.6, 22, YELLOW, Metal),
				B(87.2, 18.6, -10, 1.6, 1.6, 22, YELLOW, Metal),
				B(80, 19.2, -10, 16, 1.4, 1.6, DARK, Metal),
				B(80, 17.8, -6, 3, 1.6, 3, DARK, Metal),
				Cy(80, 13, -6, 0.3, 9, DARK, Metal),
				B(80, 7.4, -6, 1.6, 1.4, 1.6, DARK, Metal),
				B(80, 4, -6, 6, 3, 4, RED, Corroded),
			},
		},
		{
			Id = "Charging",
			Name = "Robot Charging Bay",
			Description = "Three little robots resting in their charging stalls under a shared roof.",
			Pad = Vector2.new(70, 48),
			Yaw = 28,
			PriceSeconds = 229,
			Pieces = {
				Cy(61.5, 4, 37.5, 0.8, 8, DARK, Metal),
				Cy(78.5, 4, 37.5, 0.8, 8, DARK, Metal),
				B(70, 8.3, 38.6, 19, 0.6, 5, YELLOW, Metal),
				B(63.5, 3.2, 37.6, 4.4, 6.4, 0.8, DARK, Metal),
				B(70, 3.2, 37.6, 4.4, 6.4, 0.8, DARK, Metal),
				B(76.5, 3.2, 37.6, 4.4, 6.4, 0.8, DARK, Metal),
				B(63.5, 1.7, 40.2, 3, 3.4, 2.6, STEEL, Metal),
				B(70, 1.7, 40.2, 3, 3.4, 2.6, STEEL, Metal),
				B(76.5, 1.7, 40.2, 3, 3.4, 2.6, STEEL, Metal),
				B(63.5, 4.2, 40.2, 2.2, 1.6, 2, STEEL, Metal),
				B(70, 4.2, 40.2, 2.2, 1.6, 2, STEEL, Metal),
				B(76.5, 4.2, 40.2, 2.2, 1.6, 2, STEEL, Metal),
			},
		},
		{
			Id = "Press",
			Name = "Hydraulic Press",
			Description = "A mighty orange press that stamps steel plates, with a stack of finished sheets.",
			Pad = Vector2.new(24, -22),
			Yaw = -26,
			PriceSeconds = 263,
			Pieces = {
				B(20, 1.5, -34, 14, 3, 10, DARK, Diamond),
				B(14.5, 9.5, -34, 2.4, 14, 6, ORANGE, Metal),
				B(25.5, 9.5, -34, 2.4, 14, 6, ORANGE, Metal),
				B(20, 17, -34, 14, 3, 8, ORANGE, Metal),
				Cy(20, 13.5, -34, 4, 4, STEEL, Metal),
				Cy(20, 9.5, -34, 2, 4.4, STEEL, Metal),
				B(20, 6.6, -34, 8, 1.4, 5, DARK, Metal),
				B(20, 3.9, -34, 8, 1.8, 5, STEEL, Metal),
				B(28.6, 1.2, -29.4, 3, 2.4, 2.4, PLATE, Metal),
			},
		},
		{
			Id = "Drones",
			Name = "Drone Dock",
			Description = "A tall landing mast with a round platform where four little drones perch.",
			Pad = Vector2.new(84, 45),
			Yaw = 22,
			PriceSeconds = 303,
			Pieces = {
				Cy(84, 1, 56, 8, 2, CONCRETE, Concrete),
				Cy(84, 7, 56, 1.8, 12, STEEL, Metal),
				Cy(84, 13.3, 56, 10, 0.7, DARK, Metal),
				B(81.5, 14.7, 54.5, 2.4, 1, 2.4, WHITE, Plastic),
				B(86.5, 14.7, 54.5, 2.4, 1, 2.4, WHITE, Plastic),
				B(81.5, 14.7, 57.5, 2.4, 1, 2.4, WHITE, Plastic),
				B(86.5, 14.7, 57.5, 2.4, 1, 2.4, WHITE, Plastic),
				Cy(84, 15.9, 56, 0.4, 3, STEEL, Metal),
			},
		},
		{
			Id = "Scrap",
			Name = "Scrap Heap",
			Description = "A rusty mountain of scrapped robot parts with a magnet crane and a crushed cube.",
			Pad = Vector2.new(-56, 24),
			Yaw = -28,
			PriceSeconds = 348,
			Pieces = {
				Ball(-58, 3.4, 10, 18, 7, 12, RUST, Corroded),
				Ball(-63, 4.4, 8, 10, 8.4, 9, DIRT, Corroded),
				Ball(-53, 3.2, 12, 9, 6, 8, RUST, Corroded),
				B(-66, 2.2, 14, 4.4, 4.4, 4.4, STEEL, Corroded),
				B(-60, 5.4, 7, 3, 3, 3, STEEL, Metal),
				Cy(-70, 6.5, 4, 1.2, 13, YELLOW, Metal),
				B(-65.4, 13.2, 4, 10.4, 0.9, 1.2, YELLOW, Metal),
				Cy(-61, 9.8, 4, 0.2, 5, DARK, Metal),
				Cy(-61, 7, 4, 3, 0.8, DARK, Metal),
			},
		},
		{
			Id = "Lab",
			Name = "Brain Lab",
			Description = "A glass dome on a steel ring with a glowing artificial brain floating inside.",
			Pad = Vector2.new(0, -27),
			Yaw = 4,
			PriceSeconds = 400,
			RewardMult = 1.5,
			Pieces = {
				Cy(0, 0.8, -40, 19, 1.6, CONCRETE, Concrete),
				Ball(0, 6.5, -40, 17.4, 13, 17.4, GLASS, Glass),
				Cy(0, 2.4, -40, 5, 4.8, DARK, Metal),
			},
		},
		{
			Id = "GiantRobot",
			Name = "Giant Robot",
			Description = "The showpiece: a huge steel guardian with glowing eyes, big fists and a chest light.",
			Pad = Vector2.new(-72, -30),
			Yaw = 12,
			PriceSeconds = 460,
			RewardMult = 2,
			Pieces = {
				B(-76.5, 1.5, -44, 6.4, 3, 9.4, DARK, Metal),
				B(-67.5, 1.5, -44, 6.4, 3, 9.4, DARK, Metal),
				B(-76.5, 8.5, -44, 3.6, 10, 4.4, STEEL, Metal),
				B(-67.5, 8.5, -44, 3.6, 10, 4.4, STEEL, Metal),
				B(-72, 15, -44, 15, 3.4, 7, DARK, Metal),
				B(-72, 23, -44, 17, 12.6, 9, STEEL, Metal),
				B(-72, 31.5, -44, 8, 5.4, 6.4, STEEL, Metal),
				B(-83.4, 22, -44, 4.6, 12, 5, STEEL, Metal),
				B(-60.6, 22, -44, 4.6, 12, 5, STEEL, Metal),
				B(-83.4, 14.4, -44, 5.4, 4.4, 5.4, YELLOW, Metal),
				B(-60.6, 14.4, -44, 5.4, 4.4, 5.4, YELLOW, Metal),
				Cy(-72, 36, -44, 0.7, 3.6, DARK, Metal),
			},
		},
	},
}

return theme
