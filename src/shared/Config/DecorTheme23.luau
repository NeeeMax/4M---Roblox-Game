--!strict
-- Theme of the Shiba of bay 23: Mecha Hangar (Config/DecorTypes -> Theme). 160 x 115: Mecha Shiba stands on a hazard-ringed launch
-- turntable in the right middle of the plot, a giant mecha colossus towers behind it; a winding walkway snakes past the hangar,
-- workshop and dropship on the right, the repair bays, walkers and barracks on the left and the reactor and control tower in the back.
-- Stage frame: +X right, -Z deeper, +Z toward the road. Every part is written in local coordinates around its centre, set with part(cx, cz, ...).
-- No glow: lenses, screens and cores are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local STEEL = C(110, 130, 160)
local PANEL = C(150, 168, 195)
local DARK = C(44, 54, 72)
local HAZ = C(255, 200, 0)
local BLK = C(24, 26, 32)
local HOLO = C(80, 210, 255)
local RED = C(230, 50, 50)
local WHITE = C(232, 236, 244)
local ORANGE = C(240, 130, 40)
local FLOOR = C(84, 94, 110)
local CONC = C(124, 128, 138)

local Metal = Enum.Material.Metal
local Plate = Enum.Material.DiamondPlate
local Concrete = Enum.Material.Concrete
local Plastic = Enum.Material.SmoothPlastic
local Glass = Enum.Material.Glass

local ox, oz = 0, 0

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
		Offset = Vector3.new(x + ox, y, z + oz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
	}
end

-- Standing cylinder (axis up): diameter d, height h, centre y.
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x + ox, y, z + oz),
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
		Offset = Vector3.new(x + ox, y, z + oz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Cylinder lying along Z (a dish or wheel facing the road): diameter d, thickness len.
local function Cz(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x + ox, y, z + oz),
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
		Offset = Vector3.new(x + ox, y, z + oz),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
end

-- Turns a block about the vertical axis (degrees).
local function Y(piece: Piece, deg: number): Piece
	piece.Rotation = Vector3.new(0, deg, 0)
	return piece
end

-- A part is written in local coordinates around its centre (cx, cz): every constructor adds the current origin.
local function part(cx: number, cz: number, build: () -> Pieces): Pieces
	ox, oz = cx, cz
	local list = build()
	ox, oz = 0, 0
	return list
end

local theme: DecorTypes.Theme = {
	Key = "MechaHangar",
	Name = "Mecha Hangar",
	Area = Vector2.new(160, 115),
	Shiba = { Position = Vector2.new(22, 4), Facing = 180 },
	Path = {
		Vector2.new(0, 57.5),
		Vector2.new(28, 42),
		Vector2.new(-8, 26),
		Vector2.new(-36, 8),
		Vector2.new(-2, 0),
		Vector2.new(32, -24),
		Vector2.new(6, -42),
		Vector2.new(0, -57.5),
	},
	BayPad = Vector2.new(18, 19),
	AutoPad = Vector2.new(22, -10),
	Parts = {
		{
			Id = "Floor",
			Name = "Hangar Floor",
			Description = "Dark diamond-plate steel with yellow hazard lanes and lighter concrete patches.",
			Pad = Vector2.new(-4, 54),
			PriceSeconds = 58,
			Pieces = part(0, 0, function()
				return {
					B(0, 0.15, 0, 158, 0.3, 113, FLOOR, Plate),
					B(-50, 0.35, -28, 24, 0.2, 18, CONC, Concrete),
					B(60, 0.35, 22, 24, 0.2, 20, CONC, Concrete),
					B(-8, 0.35, 14, 18, 0.2, 14, CONC, Concrete),
					B(-50, 0.4, 12, 2, 0.2, 30, HAZ, Plastic),
					B(44, 0.4, -34, 2, 0.2, 26, HAZ, Plastic),
					B(10, 0.4, 48, 26, 0.2, 2, HAZ, Plastic),
					B(-22, 0.4, -10, 2, 0.2, 20, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "Turntable",
			Name = "Launch Turntable",
			Description = "A round hazard-ringed launch turntable where Mecha Shiba stands, with yellow guide bars.",
			Pad = Vector2.new(31, -12),
			PriceSeconds = 67,
			Pieces = part(22, 4, function()
				return {
					B(0, 0.15, 0, 25, 0.3, 25, DARK, Concrete),
					B(0, 0.4, 0, 21, 0.2, 21, HAZ, Plastic),
					B(0, 0.48, 0, 18.6, 0.2, 18.6, DARK, Metal),
					B(0, 0.54, 0, 12, 0.1, 12, STEEL, Plate),
					B(11.7, 0.38, 0, 1.2, 0.2, 5, HAZ, Plastic),
					B(-11.7, 0.38, 0, 1.2, 0.2, 5, HAZ, Plastic),
					B(0, 0.38, 11.7, 5, 0.2, 1.2, HAZ, Plastic),
					B(0, 0.38, -11.7, 5, 0.2, 1.2, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "Hangar",
			Yaw = -8,
			Name = "Mecha Hangar",
			Description = "A big steel hangar with a hazard-striped roof beam and two half-open blast doors.",
			Pad = Vector2.new(46, -26),
			PriceSeconds = 77,
			Pieces = part(60, -36, function()
				return {
					B(0, 10, -11.5, 34, 20, 3, STEEL, Metal),
					B(-15.5, 10, 0, 3, 20, 22, STEEL, Metal),
					B(15.5, 10, 0, 3, 20, 22, STEEL, Metal),
					B(0, 21, 0, 36, 2, 28, DARK, Metal),
					B(0, 23.5, 0, 30, 3, 22, PANEL, Metal),
					B(0, 18.5, 13, 34, 3, 1.6, HAZ, Plastic),
					Cy(-16, 9.5, 13, 2.4, 19, PANEL, Metal),
					Cy(16, 9.5, 13, 2.4, 19, PANEL, Metal),
					B(-11.5, 8, 12.4, 8, 16, 1, DARK, Metal),
					B(11.5, 8, 12.4, 8, 16, 1, DARK, Metal),
					B(0, 0.5, 11.5, 26, 1, 2, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "BonkSign",
			Yaw = -10,
			Name = "Get Bonked Sign",
			Description = "A steel billboard on two posts that reads GET BONKED.",
			Pad = Vector2.new(-26, 54),
			PriceSeconds = 88,
			Pieces = part(-30, 50, function()
				return {
					Cy(-8, 5, 0, 1.2, 10, STEEL, Metal),
					Cy(8, 5, 0, 1.2, 10, STEEL, Metal),
					B(0, 8, 0, 22, 6, 1, DARK, Metal),
					B(0, 11.2, 0, 22.6, 0.8, 1.6, HAZ, Plastic),
					B(0, 4.8, 0, 22.6, 0.8, 1.6, HAZ, Plastic),
					B(-8, 0.4, 0, 4, 0.8, 3, CONC, Concrete),
					B(8, 0.4, 0, 4, 0.8, 3, CONC, Concrete),
				}
			end),
		},
		{
			Id = "Crates",
			Yaw = 14,
			Name = "Supply Crates",
			Description = "A loose pile of steel and orange cargo crates stacked at different angles.",
			Pad = Vector2.new(-58, 34),
			PriceSeconds = 101,
			Pieces = part(-70, 32, function()
				return {
					Y(B(-2.5, 2.5, -1, 5, 5, 5, ORANGE, Plate), 18),
					Y(B(-2, 7.2, -1, 4, 4.4, 4, STEEL, Plate), -25),
					Y(B(3.5, 2, 2.5, 4, 4, 4, STEEL, Plate), -24),
					Y(B(4, 1.5, -3.5, 3, 3, 3, ORANGE, Plate), 30),
					Y(B(-4, 1.5, 4, 3, 3, 3, HAZ, Plastic), 12),
					Y(B(6.5, 0.8, 5, 2, 1.6, 2, RED, Plate), -10),
				}
			end),
		},
		{
			Id = "Drums",
			Yaw = -22,
			Name = "Fuel Drums",
			Description = "Seven colourful fuel drums on a pallet, one rolled onto its side.",
			Pad = Vector2.new(-46, 36),
			PriceSeconds = 117,
			Pieces = part(-51, 45, function()
				return {
					B(-1.5, 0.3, -1.5, 8, 0.6, 5, DARK, Concrete),
					Cy(-3.2, 2.3, -1.6, 2.4, 3.4, RED, Metal),
					Cy(-0.6, 2.3, -2.2, 2.4, 3.4, STEEL, Metal),
					Cy(2, 2.3, -1.2, 2.4, 3.4, HAZ, Metal),
					Cy(-2, 2.3, 1, 2.4, 3.4, ORANGE, Metal),
					Cy(0.8, 2.3, 0.4, 2.4, 3.4, RED, Metal),
					Cy(4.4, 1.7, 2.4, 2.4, 3.4, STEEL, Metal),
					Cy(-4.6, 1.7, 2.6, 2.4, 3.4, DARK, Metal),
					Y(Cx(1, 1.2, 4.6, 2.4, 3.4, ORANGE, Metal), 35),
				}
			end),
		},
		{
			Id = "Floodlights",
			Yaw = 18,
			Name = "Floodlights",
			Description = "Three steel floodlight masts of different heights that light up the hangar yard.",
			Pad = Vector2.new(30, 52),
			PriceSeconds = 134,
			Pieces = part(40, 52, function()
				return {
					B(-4, 0.25, 0, 2.4, 0.5, 2.4, DARK, Concrete),
					Cy(-4, 6.5, 0, 0.8, 13, STEEL, Metal),
					Y(B(-4, 13.2, 0.6, 3.4, 1.6, 1.4, DARK, Metal), 15),
					B(2, 0.25, -3, 2.4, 0.5, 2.4, DARK, Concrete),
					Cy(2, 5, -3, 0.8, 10, STEEL, Metal),
					Y(B(2, 10.2, -2.4, 3.4, 1.6, 1.4, DARK, Metal), -20),
					B(5.5, 0.25, 2.5, 2.4, 0.5, 2.4, DARK, Concrete),
					Cy(5.5, 6, 2.5, 0.8, 12, STEEL, Metal),
					Y(B(5.5, 12.2, 3.1, 3.4, 1.6, 1.4, DARK, Metal), 30),
				}
			end),
		},
		{
			Id = "Console",
			Yaw = 24,
			Name = "Mission Console",
			Description = "A curved control desk with three holo screens and a swivel chair for the mission controller.",
			Pad = Vector2.new(-8, -10),
			PriceSeconds = 154,
			Pieces = part(-14, -16, function()
				return {
					B(0, 0.2, 1, 13, 0.4, 9, DARK, Concrete),
					B(0, 1.5, 0, 10, 3, 3.2, STEEL, Metal),
					Y(B(-6.2, 1.5, 2, 4, 3, 3, STEEL, Metal), -35),
					Y(B(6.2, 1.5, 2, 4, 3, 3, STEEL, Metal), 35),
					B(0, 4.7, -0.8, 5, 3, 0.5, HOLO, Glass),
					Y(B(-6.4, 4.2, 0.6, 3.6, 2.4, 0.5, HOLO, Glass), -35),
					Y(B(6.4, 4.2, 0.6, 3.6, 2.4, 0.5, HOLO, Glass), 35),
					Cy(0, 1.2, 4.4, 1.8, 2.4, DARK, Plastic),
					B(0, 3.2, 5.2, 2, 2, 0.5, DARK, Plastic),
				}
			end),
		},
		{
			Id = "Workshop",
			Yaw = -10,
			Name = "Mecha Workshop",
			Description = "An open workshop with a yellow roof, a long workbench, a barrel and a smoking chimney.",
			Pad = Vector2.new(52, 44),
			PriceSeconds = 177,
			Pieces = part(66, 48, function()
				return {
					B(0, 5, -4.5, 20, 10, 1.4, STEEL, Metal),
					B(-9.3, 5, 0, 1.4, 10, 10, STEEL, Metal),
					B(9.3, 5, 0, 1.4, 10, 10, STEEL, Metal),
					B(0, 10.4, 0, 22, 1.2, 12, HAZ, Metal),
					B(0, 9.4, 5.6, 20, 1.4, 0.8, DARK, Metal),
					B(0, 1.5, 2.2, 10, 3, 2.4, PANEL, Metal),
					B(-5, 3.4, 2.2, 1.4, 0.8, 1.4, DARK, Metal),
					Cy(6.5, 1.7, 2, 2.4, 3.4, RED, Metal),
					Cy(-6.5, 13, -2, 1.6, 5, DARK, Metal),
					B(0, 0.25, 0.6, 18, 0.5, 8, DARK, Concrete),
				}
			end),
		},
		{
			Id = "FuelTanks",
			Yaw = -14,
			Name = "Fuel Tanks",
			Description = "A fat horizontal tank on saddles and a tall vertical tank joined by a pipe.",
			Pad = Vector2.new(-48, 5),
			PriceSeconds = 204,
			Pieces = part(-48, -4, function()
				return {
					B(0, 0.25, 0, 17, 0.5, 11, DARK, Concrete),
					B(-4.4, 1.4, 1, 1.2, 2, 5, DARK, Metal),
					B(2.6, 1.4, 1, 1.2, 2, 5, DARK, Metal),
					Cx(-1, 3.8, 1, 5, 11, PANEL, Metal),
					Cy(5.8, 5.4, -3, 4.4, 10.8, STEEL, Metal),
					Cy(5.8, 11, -3, 3, 0.8, HAZ, Metal),
					Cx(2.4, 2.4, -3, 0.8, 7, DARK, Metal),
					B(-1, 6.6, 1, 1.4, 0.8, 1.4, HAZ, Plastic),
					B(-5.5, 3, -3.5, 0.8, 6, 0.8, DARK, Metal),
				}
			end),
		},
		{
			Id = "Radar",
			Yaw = 12,
			Name = "Radar Tower",
			Description = "A steel mast on a concrete base holding a big white radar dish that watches the sky.",
			Pad = Vector2.new(-64, 53),
			PriceSeconds = 235,
			Pieces = part(-68, 48, function()
				return {
					B(0, 0.8, 0, 9, 1.6, 9, DARK, Concrete),
					B(0, 6, 0, 2.4, 9, 2.4, STEEL, Metal),
					B(0, 11.4, 0, 4, 2.4, 4, PANEL, Metal),
					Cz(0, 14.4, 1.4, 9, 1.2, WHITE, Metal),
					B(0, 14.4, 3.8, 0.6, 0.6, 3, STEEL, Metal),
					Ball(0, 14.4, 5.4, 1.4, 1.4, 1.4, RED, Metal),
					B(5.6, 1.6, -2, 3, 3.2, 3, STEEL, Metal),
					Cy(-3.4, 3, 2.4, 0.5, 6, DARK, Metal),
				}
			end),
		},
		{
			Id = "Barracks",
			Yaw = 10,
			Name = "Pilot Barracks",
			Description = "A low steel barracks for the pilots with a hazard door, glowing windows and a vent stack.",
			Pad = Vector2.new(-60, -37),
			PriceSeconds = 270,
			Pieces = part(-64, -47, function()
				return {
					B(0, 4, 0, 20, 8, 13, PANEL, Metal),
					B(0, 8.8, 0, 21.4, 1.6, 14.4, DARK, Metal),
					B(0, 10.2, 0, 18, 1.2, 4, STEEL, Metal),
					B(-3, 2.2, 6.7, 3, 4.4, 0.4, HAZ, Plastic),
					B(4, 5, 6.7, 2.4, 1.6, 0.4, HOLO, Glass),
					B(8, 5, 6.7, 2.4, 1.6, 0.4, HOLO, Glass),
					B(-8, 5, 6.7, 2.4, 1.6, 0.4, HOLO, Glass),
					B(-3, 0.3, 8.6, 5, 0.6, 3, CONC, Concrete),
					Cy(6.5, 11, -3, 1.6, 3, DARK, Metal),
				}
			end),
		},
		{
			Id = "MissileRack",
			Yaw = -16,
			Name = "Missile Rack",
			Description = "A steel rack holding three white missiles with red nose cones.",
			Pad = Vector2.new(38, -14),
			PriceSeconds = 310,
			Pieces = part(46, -14, function()
				return {
					B(0, 0.5, 0, 12, 1, 5, DARK, Concrete),
					B(-4.5, 4, 0, 0.8, 7, 3, STEEL, Metal),
					B(4.5, 4, 0, 0.8, 7, 3, STEEL, Metal),
					Cx(0, 2.4, 0, 1.6, 9.6, WHITE, Metal),
					Cx(0, 4.4, 0, 1.6, 9.6, WHITE, Metal),
					Cx(0, 6.4, 0, 1.6, 9.6, WHITE, Metal),
					Ball(5.4, 2.4, 0, 2.4, 1.6, 1.6, RED, Metal),
					Ball(5.4, 4.4, 0, 2.4, 1.6, 1.6, RED, Metal),
					Ball(5.4, 6.4, 0, 2.4, 1.6, 1.6, RED, Metal),
					B(0, 7.7, 0, 10, 0.6, 3.4, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "DronePad",
			Yaw = 20,
			Name = "Drone Pad",
			Description = "A round pad with three little quad drones parked on short stands.",
			Pad = Vector2.new(-18, 30),
			PriceSeconds = 357,
			Pieces = part(-28, 34, function()
				return {
					B(0, 0.15, 0, 13, 0.3, 13, DARK, Concrete),
					B(0, 0.4, 0, 11, 0.2, 11, HAZ, Plastic),
					Cy(-2.6, 1.6, -1.6, 0.6, 2.6, STEEL, Metal),
					Y(B(-2.6, 3.2, -1.6, 2.2, 1, 2.2, PANEL, Metal), 20),
					Y(B(-2.6, 3.8, -1.6, 5.6, 0.2, 0.7, DARK, Plastic), 20),
					Y(B(-2.6, 3.8, -1.6, 5.6, 0.2, 0.7, DARK, Plastic), 110),
					Cy(2.8, 1.6, -2, 0.6, 2.6, STEEL, Metal),
					Y(B(2.8, 3.2, -2, 2.2, 1, 2.2, PANEL, Metal), -25),
					Y(B(2.8, 3.8, -2, 5.6, 0.2, 0.7, DARK, Plastic), -25),
					Y(B(2.8, 3.8, -2, 5.6, 0.2, 0.7, DARK, Plastic), 65),
					Cy(0, 1.6, 3, 0.6, 2.6, STEEL, Metal),
					Y(B(0, 3.2, 3, 2.2, 1, 2.2, HAZ, Metal), 10),
					Y(B(0, 3.8, 3, 5.6, 0.2, 0.7, DARK, Plastic), 10),
					Y(B(0, 3.8, 3, 5.6, 0.2, 0.7, DARK, Plastic), 100),
				}
			end),
		},
		{
			Id = "RepairArm",
			Yaw = -18,
			Name = "Repair Gantry",
			Description = "A yellow gantry with a robotic repair arm working on a mecha leg in its cradle.",
			Pad = Vector2.new(-62, 20),
			PriceSeconds = 410,
			Pieces = part(-68, 13, function()
				return {
					B(0, 0.5, 0, 16, 1, 12, DARK, Concrete),
					B(-7, 7.5, -4, 1.6, 13, 1.6, HAZ, Metal),
					B(7, 7.5, -4, 1.6, 13, 1.6, HAZ, Metal),
					B(0, 14.4, -4, 16, 1.4, 1.8, HAZ, Metal),
					Ball(2, 12.4, -4, 2, 2, 2, STEEL, Metal),
					B(2.4, 9.6, -3, 1.2, 5, 1.2, PANEL, Metal),
					Ball(2.8, 6.8, -2, 1.6, 1.6, 1.6, STEEL, Metal),
					B(2.8, 5.4, 0, 1, 1, 4.2, PANEL, Metal),
					B(-1, 1.6, 3, 5, 1.2, 5, DARK, Metal),
					B(-1, 3.4, 3, 3.4, 3.6, 3.4, STEEL, Metal),
					B(-1, 6.2, 3, 4.4, 2, 4.4, PANEL, Metal),
				}
			end),
		},
		{
			Id = "Transport",
			Yaw = -28,
			Name = "Mecha Transport",
			Description = "An orange hauler truck carrying a spare mecha arm on its long flatbed.",
			Pad = Vector2.new(-40, 33),
			PriceSeconds = 472,
			Pieces = part(-48, 26, function()
				return {
					B(-3.5, 2.6, 0, 13, 0.8, 4.4, DARK, Metal),
					B(6.4, 3.8, 0, 5, 5, 4.6, ORANGE, Metal),
					B(8.2, 4.8, 0, 1.6, 1.8, 3.6, HOLO, Glass),
					Cz(7, 1.3, 2.4, 2.6, 0.8, BLK, Plastic),
					Cz(7, 1.3, -2.4, 2.6, 0.8, BLK, Plastic),
					Cz(-1, 1.3, 2.4, 2.6, 0.8, BLK, Plastic),
					Cz(-1, 1.3, -2.4, 2.6, 0.8, BLK, Plastic),
					Cz(-6.4, 1.3, 2.4, 2.6, 0.8, BLK, Plastic),
					Cz(-6.4, 1.3, -2.4, 2.6, 0.8, BLK, Plastic),
					Cx(-3, 4.4, 0, 2.4, 9, STEEL, Metal),
					B(-8, 4.6, 0, 2.6, 2.6, 2.6, PANEL, Metal),
				}
			end),
		},
		{
			Id = "PartsRack",
			Yaw = 22,
			Name = "Spare Parts Rack",
			Description = "A tall shelf rack stocked with spare mecha arms, a boot and a helmet.",
			Pad = Vector2.new(-62, -2),
			PriceSeconds = 543,
			Pieces = part(-70, -2, function()
				return {
					B(-6, 4, 0, 0.8, 8, 3, STEEL, Metal),
					B(-2, 4, 0, 0.8, 8, 3, STEEL, Metal),
					B(2, 4, 0, 0.8, 8, 3, STEEL, Metal),
					B(6, 4, 0, 0.8, 8, 3, STEEL, Metal),
					B(0, 2.4, 0, 13, 0.6, 3.4, PANEL, Metal),
					B(0, 5.2, 0, 13, 0.6, 3.4, PANEL, Metal),
					B(0, 8.2, 0, 13, 0.6, 3.4, DARK, Metal),
					Cx(-4, 3.6, 0, 1.8, 7, ORANGE, Metal),
					Cx(3.4, 3.6, 0, 1.8, 6, ORANGE, Metal),
					B(-4, 6.6, 0, 3, 2.2, 2.4, STEEL, Metal),
					Ball(4, 6.8, 0, 2.8, 2.6, 2.6, WHITE, Metal),
					B(0, 0.7, 0, 3.4, 1.4, 2.6, DARK, Metal),
				}
			end),
		},
		{
			Id = "Walkers",
			Yaw = -18,
			Name = "Scout Walkers",
			Description = "Two small two-legged scout walkers standing guard at different angles.",
			Pad = Vector2.new(-34, -18),
			PriceSeconds = 624,
			Pieces = part(-33, -26, function()
				return {
					Y(B(-3, 1.7, 0, 1.4, 3.4, 1.4, DARK, Metal), 25),
					Y(B(-0.4, 1.7, 1.2, 1.4, 3.4, 1.4, DARK, Metal), 25),
					Y(B(-1.7, 4.8, 0.6, 4.6, 2.6, 3.6, STEEL, Metal), 25),
					Y(B(-1.7, 6.9, 0.6, 3.2, 1.8, 2.6, HOLO, Glass), 25),
					Y(B(-1.2, 5, -1.6, 4, 0.8, 0.8, ORANGE, Metal), 25),
					Y(B(4.6, 2.2, 3, 1.8, 4.4, 1.8, DARK, Metal), -35),
					Y(B(7.4, 2.2, 1.6, 1.8, 4.4, 1.8, DARK, Metal), -35),
					Y(B(6, 6, 2.3, 5.6, 3.2, 4.4, ORANGE, Metal), -35),
					Y(B(6, 8.6, 2.3, 3.8, 2, 3, HOLO, Glass), -35),
					Y(B(4.4, 6.4, 0, 0.8, 0.8, 5, STEEL, Metal), -35),
				}
			end),
		},
		{
			Id = "Range",
			Yaw = 20,
			Name = "Target Range",
			Description = "Three round targets on posts behind a sandbag wall where the pilots practise their aim.",
			Pad = Vector2.new(-50, -16),
			PriceSeconds = 718,
			Pieces = part(-52, -25, function()
				return {
					Cy(-6, 3, -4, 0.6, 6, STEEL, Metal),
					Cz(-6, 5.8, -3.6, 3.6, 0.4, WHITE, Plastic),
					Cz(-6, 5.8, -3.3, 1.8, 0.4, RED, Plastic),
					Cy(0, 3, -6, 0.6, 6, STEEL, Metal),
					Cz(0, 5.8, -5.6, 3.6, 0.4, WHITE, Plastic),
					Cz(0, 5.8, -5.3, 1.8, 0.4, RED, Plastic),
					Cy(6, 3, -3, 0.6, 6, STEEL, Metal),
					Cz(6, 5.8, -2.6, 3.6, 0.4, WHITE, Plastic),
					Cz(6, 5.8, -2.3, 1.8, 0.4, RED, Plastic),
					B(-2, 0.8, 5, 10, 1.6, 2.4, CONC, Concrete),
					B(-4, 2.2, 5, 5, 1.2, 2.2, CONC, Concrete),
					B(5.5, 0.8, 4.4, 3, 1.6, 2.4, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "Barriers",
			Yaw = -25,
			Name = "Jersey Barriers",
			Description = "Five concrete barriers with yellow stripes, scattered like a blockade.",
			Pad = Vector2.new(12, 27),
			PriceSeconds = 825,
			Pieces = part(4, 17, function()
				return {
					Y(B(-5, 1.5, 0, 4.4, 3, 1.6, CONC, Concrete), 5),
					Y(B(-5, 3.2, 0, 4.4, 0.4, 1.7, HAZ, Plastic), 5),
					Y(B(0, 1.5, 1.5, 4.4, 3, 1.6, CONC, Concrete), -20),
					Y(B(0, 3.2, 1.5, 4.4, 0.4, 1.7, HAZ, Plastic), -20),
					Y(B(5, 1.5, 0, 4.4, 3, 1.6, CONC, Concrete), 25),
					Y(B(5, 3.2, 0, 4.4, 0.4, 1.7, HAZ, Plastic), 25),
					Y(B(-2, 1.5, -3.4, 4.4, 3, 1.6, CONC, Concrete), -8),
					Y(B(3, 1.5, -3.8, 4.4, 3, 1.6, CONC, Concrete), 60),
				}
			end),
		},
		{
			Id = "Silos",
			Yaw = 8,
			Name = "Ammo Silos",
			Description = "Two tall grey silos with domed tops, hazard bands and ladders.",
			Pad = Vector2.new(68, -2),
			PriceSeconds = 949,
			Pieces = part(72, -12, function()
				return {
					B(0, 0.4, 0, 13, 0.8, 9, DARK, Concrete),
					Cy(-3.2, 8, -1, 6, 14.4, PANEL, Metal),
					Cy(3.2, 8, 1, 6, 14.4, PANEL, Metal),
					Ball(-3.2, 15.2, -1, 6, 5, 6, STEEL, Metal),
					Ball(3.2, 15.2, 1, 6, 5, 6, STEEL, Metal),
					Cy(-3.2, 5, -1, 6.4, 1.2, HAZ, Plastic),
					Cy(3.2, 5, 1, 6.4, 1.2, HAZ, Plastic),
					B(-3.2, 8, 2.2, 0.8, 14, 0.4, DARK, Metal),
					B(3.2, 8, 4.2, 0.8, 14, 0.4, DARK, Metal),
				}
			end),
		},
		{
			Id = "Tower",
			Yaw = 8,
			Name = "Control Tower",
			Description = "A tall control tower with a wide glass cab, a hazard roof and a blinking antenna.",
			Pad = Vector2.new(-10, -40),
			PriceSeconds = 1092,
			Pieces = part(-20, -44, function()
				return {
					B(0, 3, 0, 9, 6, 9, PANEL, Metal),
					B(0, 12.5, 0, 4, 13, 4, STEEL, Metal),
					B(0, 21.5, 0, 10, 5, 10, DARK, Metal),
					B(0, 21.5, 0, 10.6, 2.4, 10.6, HOLO, Glass),
					B(0, 24.8, 0, 12, 1.2, 12, HAZ, Metal),
					Cy(0, 29, 0, 0.5, 7, STEEL, Metal),
					Ball(0, 32.8, 0, 1.4, 1.4, 1.4, RED, Metal),
					B(0, 0.4, 6.4, 5, 0.8, 4, CONC, Concrete),
				}
			end),
		},
		{
			Id = "Dropship",
			Yaw = 16,
			Name = "Dropship",
			Description = "A grey VTOL dropship with two engine pods, a glass cockpit and a hazard tail fin, parked on its pad.",
			Pad = Vector2.new(44, 28),
			PriceSeconds = 1255,
			Pieces = part(58, 25, function()
				return {
					B(0, 0.25, 0, 22, 0.5, 18, DARK, Concrete),
					B(0, 4.2, 0, 16, 3.4, 4.4, PANEL, Metal),
					B(-1, 3.8, 0, 6, 0.8, 17, STEEL, Metal),
					Cy(-1, 5.2, 7.2, 3.2, 3.6, DARK, Metal),
					Cy(-1, 5.2, -7.2, 3.2, 3.6, DARK, Metal),
					B(-7.4, 7.2, 0, 3.4, 4.6, 0.8, HAZ, Metal),
					B(7, 5.4, 0, 4.2, 1.4, 3.2, HOLO, Glass),
					Cy(5, 1.5, 1.6, 0.8, 2, STEEL, Metal),
					Cy(5, 1.5, -1.6, 0.8, 2, STEEL, Metal),
					Cy(-5, 1.5, 0, 0.8, 2, STEEL, Metal),
				}
			end),
		},
		{
			Id = "Scrap",
			Yaw = -30,
			Name = "Scrap Heap",
			Description = "A heap of broken armour plates, a bent leg, a big gear and a flattened drum.",
			Pad = Vector2.new(-66, -10),
			PriceSeconds = 1444,
			Pieces = part(-72, -20, function()
				return {
					Y(B(0, 1, 0, 8, 2, 6, DARK, Plate), 12),
					Y(B(-1, 2.8, 0.5, 6, 1.6, 4.4, STEEL, Plate), -28),
					Y(B(1.4, 4.4, -0.4, 4, 1.6, 3, ORANGE, Plate), 40),
					Y(B(-4.4, 1.2, 3.4, 3.4, 2.4, 3.4, STEEL, Metal), 20),
					Y(B(4.6, 1.6, 3, 3, 3.2, 2.4, ORANGE, Plate), -50),
					Y(Cx(-1, 1, -4.4, 1.6, 7, DARK, Metal), 25),
					Cz(5, 2.6, -3, 4.4, 0.8, PANEL, Metal),
					Y(B(-5, 3.8, -1, 0.8, 5, 0.8, HAZ, Metal), 15),
					Y(Cx(3, 0.9, 5, 1.8, 3.4, RED, Metal), -20),
					Y(B(-3, 5.2, 0, 2.4, 1.2, 2.4, STEEL, Metal), 30),
				}
			end),
		},
		{
			Id = "StrategyTable",
			Yaw = -20,
			Name = "Strategy Table",
			Description = "A round briefing table with a floating holo map and four stools.",
			Pad = Vector2.new(8, -14),
			PriceSeconds = 1660,
			Pieces = part(4, -22, function()
				return {
					Cy(0, 0.9, 0, 2.4, 1.8, DARK, Metal),
					Cy(0, 2.4, 0, 7, 1.2, STEEL, Metal),
					Cy(0, 3.4, 0, 5, 0.8, HOLO, Glass),
					Cy(0, 4.6, 0, 3, 1.2, HOLO, Glass),
					Cy(-5, 0.7, 0, 1.8, 1.4, HAZ, Plastic),
					Cy(5, 0.7, 0.8, 1.8, 1.4, HAZ, Plastic),
					Cy(0.6, 0.7, 5, 1.8, 1.4, HAZ, Plastic),
					Cy(-0.4, 0.7, -5, 1.8, 1.4, HAZ, Plastic),
				}
			end),
		},
		{
			Id = "Generator",
			Yaw = 12,
			Name = "Power Generator",
			Description = "A heavy steel generator block with two coil towers, a tall exhaust and a hazard-banded base.",
			Pad = Vector2.new(28, -44),
			PriceSeconds = 1909,
			RewardMult = 1.3,
			Pieces = part(28, -50, function()
				return {
					B(0, 0.4, 0, 12, 0.8, 9, DARK, Concrete),
					B(0, 3.4, 0, 9, 5.2, 6.4, STEEL, Metal),
					B(0, 0.9, 4.6, 12, 0.4, 0.8, HAZ, Plastic),
					Cy(-2.6, 8.6, -1, 2.6, 6, PANEL, Metal),
					Cy(2.6, 8.6, -1, 2.6, 6, PANEL, Metal),
					Cy(-2.6, 8.8, -1, 3.4, 0.8, HAZ, Metal),
					Cy(2.6, 8.8, -1, 3.4, 0.8, HAZ, Metal),
					Ball(-2.6, 12.2, -1, 3, 3, 3, HOLO, Glass),
					Ball(2.6, 12.2, -1, 3, 3, 3, HOLO, Glass),
					Cy(5.2, 6, -2.4, 1.2, 12, DARK, Metal),
					Cx(0, 3.6, 3.6, 0.8, 8, DARK, Metal),
				}
			end),
		},
		{
			Id = "ChargeDock",
			Yaw = -20,
			Name = "Charging Dock",
			Description = "A charging dock with two yellow pylons, glowing battery panels and a heavy power plug.",
			Pad = Vector2.new(34, 34),
			PriceSeconds = 2196,
			RewardMult = 1.4,
			Pieces = part(34, 24, function()
				return {
					B(0, 0.4, 0, 9, 0.8, 7, DARK, Concrete),
					Cy(-3.6, 6, 0, 1.6, 10.4, HAZ, Metal),
					Cy(3.6, 6, 0, 1.6, 10.4, HAZ, Metal),
					B(0, 11.8, 0, 9, 1.2, 1.4, DARK, Metal),
					B(-3.6, 8, 1, 1.6, 3.4, 0.4, HOLO, Glass),
					B(3.6, 8, 1, 1.6, 3.4, 0.4, HOLO, Glass),
					B(0, 4, 0, 3.2, 4, 2.4, STEEL, Metal),
					B(0, 5, 1.4, 1.6, 1.6, 0.6, RED, Plastic),
					Cx(0, 2, 3.2, 0.8, 6, BLK, Plastic),
					B(2.6, 1.2, 3.2, 1.6, 1.6, 1.6, PANEL, Metal),
				}
			end),
		},
		{
			Id = "MechaHead",
			Yaw = -14,
			Name = "Shiba Head Monument",
			Description = "A giant steel Shiba head on a pedestal with pointed ears and a glowing visor.",
			Pad = Vector2.new(-2, 39),
			PriceSeconds = 2525,
			Pieces = part(-11, 44, function()
				return {
					B(0, 1.5, 0, 10, 3, 10, CONC, Concrete),
					B(0, 3.3, 0, 8.4, 0.6, 8.4, HAZ, Plastic),
					Cy(0, 4.6, 0, 3.4, 2.4, DARK, Metal),
					B(0, 9, 0, 8, 6.4, 7, PANEL, Metal),
					B(-2.8, 13.4, 0, 2.2, 3.6, 1.6, STEEL, Metal),
					B(2.8, 13.4, 0, 2.2, 3.6, 1.6, STEEL, Metal),
					B(0, 9.8, 3.6, 6.4, 1.6, 0.6, HOLO, Glass),
					B(0, 7.4, 4.2, 3.6, 3, 2.4, WHITE, Metal),
					Ball(0, 8.2, 5.6, 1.4, 1.2, 1.2, BLK, Metal),
				}
			end),
		},
		{
			Id = "Colossus",
			Yaw = -12,
			Name = "Mecha Colossus",
			Description = "The showpiece: a giant steel robot with a Shiba head, glowing cockpit eyes and shoulder cannons.",
			Pad = Vector2.new(36, 2),
			PriceSeconds = 2904,
			RewardMult = 1.6,
			Pieces = part(50, 0, function()
				return {
					B(0, 0.5, 0, 22, 1, 16, DARK, Concrete),
					B(-4.4, 2.4, 0.4, 5, 2.8, 8, DARK, Metal),
					B(4.4, 2.4, 0.4, 5, 2.8, 8, DARK, Metal),
					B(-4.4, 8.4, 0, 3.6, 9.6, 3.6, STEEL, Metal),
					B(4.4, 8.4, 0, 3.6, 9.6, 3.6, STEEL, Metal),
					B(0, 14.6, 0, 12, 3.2, 7, DARK, Metal),
					B(0, 21.6, 0, 12, 11, 8, PANEL, Metal),
					B(0, 22.6, 4.2, 6, 3.6, 0.6, HOLO, Glass),
					Ball(-7.6, 25.4, 0, 5, 5, 5, STEEL, Metal),
					Ball(7.6, 25.4, 0, 5, 5, 5, STEEL, Metal),
					B(-8.8, 18.4, 0, 2.6, 9, 2.6, STEEL, Metal),
					B(8.8, 18.4, 0, 2.6, 9, 2.6, STEEL, Metal),
					B(0, 30.8, 0.4, 8, 6.4, 7, WHITE, Metal),
					B(-2.8, 35.4, 0.4, 2.2, 3.4, 1.6, ORANGE, Metal),
					B(2.8, 35.4, 0.4, 2.2, 3.4, 1.6, ORANGE, Metal),
					B(0, 31.2, 4.2, 6, 1.4, 0.6, HOLO, Glass),
				}
			end),
		},
		{
			Id = "Reactor",
			Yaw = 10,
			Name = "Plasma Reactor",
			Description = "A round reactor with a glowing glass dome, four coil pylons and hazard rings that powers the whole hangar.",
			Pad = Vector2.new(-34, -38),
			PriceSeconds = 3339,
			RewardMult = 2,
			Pieces = part(-40, -47, function()
				return {
					Cy(0, 1, 0, 17, 2, DARK, Concrete),
					Cy(0, 7, 0, 9, 10, STEEL, Metal),
					Cy(0, 4.4, 0, 10.4, 1, HAZ, Plastic),
					Cy(0, 9.4, 0, 10.4, 1, HAZ, Plastic),
					Ball(0, 12.4, 0, 9, 7, 9, HOLO, Glass),
					B(-6.4, 5, -6.4, 1.6, 6, 1.6, PANEL, Metal),
					B(6.4, 5, -6.4, 1.6, 6, 1.6, PANEL, Metal),
					B(-6.4, 5, 6.4, 1.6, 6, 1.6, PANEL, Metal),
					B(6.4, 5, 6.4, 1.6, 6, 1.6, PANEL, Metal),
					Ball(-6.4, 8.6, -6.4, 2.2, 2.2, 2.2, RED, Metal),
					Ball(6.4, 8.6, -6.4, 2.2, 2.2, 2.2, RED, Metal),
					Ball(-6.4, 8.6, 6.4, 2.2, 2.2, 2.2, RED, Metal),
					Ball(6.4, 8.6, 6.4, 2.2, 2.2, 2.2, RED, Metal),
				}
			end),
		},
	},
}

return theme
