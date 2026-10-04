--!strict
-- Theme of the Shiba of bay 6: Police Station (Config/DecorTypes -> Theme). 190 x 130. Police Shiba stands on a blue badge circle in the
-- courtyard of a big U-shaped police headquarters at the back right; a winding walkway leads past the courtyard.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: sirens and lamps are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local white = C(232, 236, 244)
local navy = C(24, 40, 90)
local blue = C(36, 90, 180)
local glass = C(130, 185, 235)
local metal = C(150, 156, 170)
local dgrey = C(70, 74, 86)
local asphalt = C(52, 54, 62)
local concrete = C(168, 170, 180)
local black = C(26, 26, 34)
local yellow = C(250, 205, 45)
local red = C(205, 45, 55)
local gold = C(255, 195, 40)
local orange = C(245, 130, 35)
local pink = C(245, 150, 190)
local cream = C(250, 225, 190)
local brown = C(120, 80, 50)
local earth = C(110, 90, 70)
local rust = C(150, 80, 50)
local roofDark = C(60, 64, 80)

local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Concrete = Enum.Material.Concrete
local Slate = Enum.Material.Slate
local Wood = Enum.Material.Wood
local Glass = Enum.Material.Glass

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

-- Standing cylinder (axis up): diameter d, height h.
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

-- Cylinder lying along Z (a wheel, a badge facing the road): diameter d, length len.
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

local function Ball(x: number, y: number, z: number, d: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(d, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
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

-- A patrol car parked nose toward the road (+Z): undercarriage, white body, dark cabin, light bar.
local function patrolCar(x: number, z: number): { Piece }
	return {
		B(x, 0.7, z, 4.6, 1.0, 9.6, black, Plastic),
		B(x, 1.9, z, 5.2, 1.8, 10.4, white, Plastic),
		B(x, 3.4, z - 0.6, 4.4, 1.4, 5.2, navy, Glass),
		B(x, 4.4, z - 0.6, 3.6, 0.5, 1, blue, Plastic),
	}
end

-- A road barrier: foot bar, white plank, red plank.
local function barrier(x: number, z: number): { Piece }
	return {
		B(x, 0.4, z, 7, 0.8, 1.6, dgrey, Metal),
		B(x, 1.7, z, 7, 0.9, 0.4, white, Plastic),
		B(x, 2.7, z, 7, 0.9, 0.4, red, Plastic),
	}
end

-- A parked police motorbike facing the road: wheel block, white body, blue top box.
local function bike(x: number): { Piece }
	return {
		B(x, 0.9, 58, 0.9, 1.8, 5.6, black, Plastic),
		B(x, 2.2, 58.2, 1.6, 1.4, 3.4, white, Plastic),
		B(x, 3.3, 59, 1.8, 1, 1.8, blue, Plastic),
	}
end

local theme: DecorTypes.Theme = {
	Key = "PoliceStation",
	Name = "Police Station",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(58, -37), Facing = 270 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-45, 44),
		Vector2.new(30, 22),
		Vector2.new(62, -8),
		Vector2.new(-8, -34),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(72, -33),
	AutoPad = Vector2.new(44, -33),
	Parts = {
		{
			Id = "Floor",
			Name = "Asphalt and Plaza",
			Description = "A parking lot with white lines, a blue badge plaza and a sidewalk along the road.",
			Pad = Vector2.new(-60, 57),
			PriceSeconds = 10,
			Pieces = {
				B(-74, 0.15, 44, 36, 0.3, 28, asphalt, Slate),
				B(-80, 0.32, 42.5, 0.4, 0.1, 13, white, Plastic),
				B(-68, 0.32, 42.5, 0.4, 0.1, 13, white, Plastic),
				B(-74, 0.32, 36, 36, 0.1, 0.4, white, Plastic),
				B(63, 0.15, -40, 60, 0.3, 48, concrete, Concrete),
				B(58, 0.36, -37, 17, 0.32, 17, blue, Plastic),
				B(63, 0.35, -16.4, 60, 0.1, 0.8, yellow, Plastic),
				B(-75, 0.15, -12, 34, 0.3, 24, C(120, 114, 102), Slate),
				B(-77, 0.15, -50, 30, 0.3, 26, C(130, 134, 146), Concrete),
				B(-24, 0.15, 0, 26, 0.3, 26, C(190, 192, 200), Concrete),
				B(-24, 0.35, 0, 18, 0.1, 18, blue, Plastic),
				B(28, 0.15, -2, 22, 0.3, 14, C(200, 200, 208), Concrete),
				B(0, 0.15, 63, 190, 0.3, 4, C(205, 205, 212), Concrete),
				B(-40, 0.15, -48, 28, 0.3, 28, dgrey, Concrete),
				B(71, 0.15, 33, 40, 0.3, 24, C(140, 142, 154), Concrete),
				B(30, 0.15, 54, 30, 0.3, 10, asphalt, Slate),
			},
		},
		{
			Id = "Station",
			Name = "Police Headquarters",
			Description = "A big white and blue station with two wings, a clock tower and a flag. Police Shiba guards the courtyard.",
			Pad = Vector2.new(68, -44),
			PriceSeconds = 17,
			RewardMult = 1.5,
			Pieces = {
				B(63, 7, -55, 54, 14, 14, white, Concrete),
				B(41.5, 6, -51, 11, 12, 22, white, Concrete),
				B(84.5, 6, -51, 11, 12, 22, white, Concrete),
				B(63, 14.4, -55, 55, 0.8, 15, roofDark, Slate),
				B(41.5, 12.4, -51, 12, 0.8, 23, roofDark, Slate),
				B(84.5, 12.4, -51, 12, 0.8, 23, roofDark, Slate),
				B(63, 19.5, -55, 14, 10, 10, white, Concrete),
				B(63, 25, -55, 15.5, 1.2, 11.5, navy, Metal),
				B(63, 10.5, -47.85, 52, 2.2, 0.3, blue, Plastic),
				B(63, 7.6, -45.8, 16, 0.5, 4, blue, Plastic),
				B(63, 3, -47.85, 6, 6, 0.3, glass, Glass),
				B(50, 5, -47.85, 10, 3.4, 0.3, glass, Glass),
				B(76, 5, -47.85, 10, 3.4, 0.3, glass, Glass),
				B(63, 20.5, -49.7, 10, 3, 0.4, blue, Plastic),
				Cy(87, 20, -58, 0.5, 10, metal, Metal),
				B(88.6, 23.6, -58, 3, 1.8, 0.2, red, Plastic),
			},
		},
		{
			Id = "Cars",
			Yaw = 12,
			Name = "Patrol Cars",
			Description = "Three white patrol cars with light bars, parked nose out in the lot.",
			Pad = Vector2.new(-74, 52),
			PriceSeconds = 28,
			Pieces = merge(patrolCar(-86, 42), patrolCar(-74, 42), patrolCar(-62, 42)),
		},
		{
			Id = "Cells",
			Yaw = 6,
			Name = "Holding Cells",
			Description = "A grey cell block with barred windows, a fenced yard and a guard tower.",
			Pad = Vector2.new(-77, -33),
			PriceSeconds = 40,
			Pieces = {
				B(-77, 5, -53, 26, 10, 18, C(150, 152, 162), Concrete),
				B(-77, 10.4, -53, 27.5, 0.8, 19.5, roofDark, Slate),
				B(-91, 8, -42, 4, 16, 4, C(150, 152, 162), Concrete),
				B(-91, 17, -42, 6, 3, 6, navy, Metal),
				B(-91, 18.8, -42, 7, 0.6, 7, roofDark, Slate),
				B(-86, 6, -43.8, 4, 4.5, 0.3, black, Metal),
				B(-81, 6, -43.8, 4, 4.5, 0.3, black, Metal),
				B(-73, 6, -43.8, 4, 4.5, 0.3, black, Metal),
				B(-68, 6, -43.8, 4, 4.5, 0.3, black, Metal),
				B(-77, 2.8, -43.8, 4, 5.6, 0.3, navy, Metal),
				B(-77, 9, -43.7, 12, 1.6, 0.3, blue, Plastic),
				B(-86, 2.5, -38, 10, 5, 0.5, metal, Metal),
				B(-68, 2.5, -38, 10, 5, 0.5, metal, Metal),
			},
		},
		{
			Id = "Donuts",
			Yaw = 15,
			Name = "Donut Shop",
			Description = "A pink donut shop with a giant donut on the roof. Every cop's favourite stop.",
			Pad = Vector2.new(28, -11),
			PriceSeconds = 57,
			Pieces = {
				B(28, 3, -2, 14, 6, 8, cream, Concrete),
				B(28, 6.3, -2, 15, 0.6, 9, pink, Plastic),
				B(28, 5.2, 3, 13, 0.4, 3, pink, Plastic),
				B(28, 1.8, 2.7, 10, 0.4, 1.4, brown, Wood),
				B(28, 3.6, 2.05, 8, 2.6, 0.3, glass, Glass),
				B(32.5, 2.4, 2.05, 2.4, 4.8, 0.3, brown, Wood),
				Cy(28, 8.4, -2, 7, 2.2, C(225, 170, 100), Plastic),
				Cy(28, 9.7, -2, 6.4, 0.4, C(240, 80, 150), Plastic),
				Cy(24, 1, 5.5, 1.6, 2, red, Plastic),
				Cy(30, 1, 5.5, 1.6, 2, red, Plastic),
				B(34, 8, -4.5, 2, 3, 2, brown, Concrete),
			},
		},
		{
			Id = "Beacon",
			Yaw = 20,
			Name = "Siren Tower",
			Description = "A tall steel tower with a red and blue siren on top that you can see from the whole plot.",
			Pad = Vector2.new(6, 2),
			PriceSeconds = 74,
			RewardMult = 1.4,
			Pieces = {
				B(6, 0.5, 10, 9, 1, 9, concrete, Concrete),
				Cy(3.5, 13, 7.5, 0.8, 24, metal, Metal),
				Cy(8.5, 13, 7.5, 0.8, 24, metal, Metal),
				Cy(3.5, 13, 12.5, 0.8, 24, metal, Metal),
				Cy(8.5, 13, 12.5, 0.8, 24, metal, Metal),
				B(6, 8, 10, 6, 0.5, 6, dgrey, Metal),
				B(6, 16, 10, 6, 0.5, 6, dgrey, Metal),
				B(6, 25.2, 10, 7, 0.6, 7, dgrey, Metal),
				B(6, 27.3, 10, 4.6, 3.6, 4.6, white, Plastic),
				Ball(4.3, 30.4, 10, 3, red, Plastic),
				Ball(7.7, 30.4, 10, 3, blue, Plastic),
				Cy(6, 34, 10, 0.4, 5, metal, Metal),
			},
		},
		{
			Id = "Range",
			Yaw = -12,
			Name = "Shooting Range",
			Description = "Four target lanes with a wooden bench and a dirt wall. Bonk practice, of course.",
			Pad = Vector2.new(56, 45),
			PriceSeconds = 97,
			Pieces = {
				B(71, 3, 23.8, 36, 6, 2.4, earth, Slate),
				Cz(59, 4.5, 27, 4.6, 0.4, white, Plastic),
				Cz(67, 4.5, 27, 4.6, 0.4, white, Plastic),
				Cz(75, 4.5, 27, 4.6, 0.4, white, Plastic),
				Cz(83, 4.5, 27, 4.6, 0.4, white, Plastic),
				Cy(59, 2.2, 27, 0.5, 4.4, brown, Wood),
				Cy(67, 2.2, 27, 0.5, 4.4, brown, Wood),
				Cy(75, 2.2, 27, 0.5, 4.4, brown, Wood),
				Cy(83, 2.2, 27, 0.5, 4.4, brown, Wood),
				B(71, 1.7, 40, 34, 0.4, 2.6, brown, Wood),
				B(55, 0.85, 40, 1, 1.7, 2, dgrey, Metal),
				B(87, 0.85, 40, 1, 1.7, 2, dgrey, Metal),
				B(63, 2, 36.5, 0.4, 4, 8, brown, Wood),
				B(71, 2, 36.5, 0.4, 4, 8, brown, Wood),
				B(79, 2, 36.5, 0.4, 4, 8, brown, Wood),
			},
		},
		{
			Id = "Kennel",
			Yaw = -14,
			Name = "K-9 Kennel",
			Description = "Three doghouses in a fenced run for the police dogs, with food bowls and a big K-9 sign.",
			Pad = Vector2.new(82, 0),
			PriceSeconds = 120,
			Pieces = {
				B(76, 2, 12, 5, 4, 5, white, Wood),
				B(76, 4.3, 12, 5.8, 0.6, 6, red, Wood),
				B(82, 2, 12, 5, 4, 5, C(200, 160, 110), Wood),
				B(82, 4.3, 12, 5.8, 0.6, 6, blue, Wood),
				B(88, 2, 12, 5, 4, 5, white, Wood),
				B(88, 4.3, 12, 5.8, 0.6, 6, red, Wood),
				B(82, 1.5, 16.6, 20, 3, 0.4, white, Metal),
				B(72.2, 1.5, 10, 0.4, 3, 13.6, white, Metal),
				B(91.8, 1.5, 10, 0.4, 3, 13.6, white, Metal),
				B(79, 0.3, 5.5, 2, 0.6, 2, metal, Metal),
				B(85, 0.3, 5, 2, 0.5, 2, red, Plastic),
				B(82, 7, 16.5, 10, 2.4, 0.3, blue, Plastic),
				Cy(77.5, 3.5, 16.5, 0.5, 7, metal, Metal),
				Cy(86.5, 3.5, 16.5, 0.5, 7, metal, Metal),
			},
		},
		{
			Id = "Heli",
			Yaw = 25,
			Name = "Police Helicopter",
			Description = "The showpiece: a blue police helicopter waiting on its helipad.",
			Pad = Vector2.new(-40, -37),
			PriceSeconds = 148,
			RewardMult = 1.5,
			Pieces = {
				B(-40, 0.25, -48, 24, 0.5, 24, C(90, 94, 108), Concrete),
				B(-44, 0.55, -48, 1.4, 0.1, 11, yellow, Plastic),
				B(-36, 0.55, -48, 1.4, 0.1, 11, yellow, Plastic),
				B(-40, 0.55, -48, 8, 0.1, 1.4, yellow, Plastic),
				B(-40, 3.4, -49, 5.6, 3.6, 8, blue, Plastic),
				Ball(-40, 3.2, -44, 4.4, blue, Plastic),
				B(-40, 4.2, -56, 1.6, 1.6, 8, blue, Plastic),
				B(-40, 5.8, -59.5, 0.4, 3, 2.2, navy, Plastic),
				B(-42.4, 0.9, -48.5, 0.5, 0.5, 9, dgrey, Metal),
				B(-37.6, 0.9, -48.5, 0.5, 0.5, 9, dgrey, Metal),
				B(-42, 1.9, -46.5, 0.4, 1.8, 0.4, dgrey, Metal),
				B(-38, 1.9, -46.5, 0.4, 1.8, 0.4, dgrey, Metal),
				Cy(-40, 6.5, -49, 0.9, 3, dgrey, Metal),
				B(-40, 8, -49, 24, 0.3, 1.4, dgrey, Metal),
				B(-40, 8, -49, 1.4, 0.3, 24, dgrey, Metal),
			},
		},
		{
			Id = "Roadblock",
			Yaw = 8,
			Name = "Roadblock",
			Description = "Red and white barriers, orange cones, a stop sign and a spike strip across the road.",
			Pad = Vector2.new(30, 45),
			PriceSeconds = 177,
			Pieces = merge(barrier(20, 52), barrier(30, 52), barrier(40, 52), {
				Cy(17, 1.2, 55, 1.6, 2.4, orange, Plastic),
				Cy(25, 1.2, 55, 1.6, 2.4, orange, Plastic),
				Cy(35, 1.2, 55, 1.6, 2.4, orange, Plastic),
				Cy(43, 1.2, 55, 1.6, 2.4, orange, Plastic),
				B(30, 0.2, 56.5, 14, 0.4, 1.4, black, Metal),
				Cy(45, 2.5, 50, 0.4, 5, metal, Metal),
				B(45, 5.6, 50, 2.4, 2.4, 0.3, red, Plastic),
			}),
		},
		{
			Id = "Swat",
			Yaw = -20,
			Name = "SWAT Van",
			Description = "A tough armoured van with a ram on the roof and a roof light bar.",
			Pad = Vector2.new(22, -46),
			PriceSeconds = 211,
			Pieces = {
				B(23, 1.4, -55, 18, 1.2, 6.8, black, Plastic),
				B(20, 4.4, -55, 12, 5.6, 7, dgrey, Metal),
				B(29, 3.8, -55, 6, 4.4, 6.8, dgrey, Metal),
				B(32.1, 4.9, -55, 0.3, 2, 5.6, glass, Glass),
				B(29, 4.9, -51.55, 3, 1.8, 0.3, glass, Glass),
				B(29, 6.4, -55, 2, 0.5, 5, blue, Plastic),
				B(20, 7.8, -55, 6, 0.8, 4, black, Metal),
				Cz(16.5, 1.7, -58.7, 3.4, 1, black, Plastic),
				Cz(16.5, 1.7, -51.3, 3.4, 1, black, Plastic),
				Cz(28.5, 1.7, -58.7, 3.4, 1, black, Plastic),
				Cz(28.5, 1.7, -51.3, 3.4, 1, black, Plastic),
				B(20, 5, -51.45, 12, 1.2, 0.2, yellow, Plastic),
			},
		},
		{
			Id = "Wanted",
			Yaw = 10,
			Name = "Wanted Board",
			Description = "A huge WANTED poster on two posts. Somebody is up to no good.",
			Pad = Vector2.new(-55, 8),
			PriceSeconds = 245,
			RewardMult = 1.4,
			Pieces = {
				Cy(-63, 5.5, 16, 1.2, 11, dgrey, Metal),
				Cy(-47, 5.5, 16, 1.2, 11, dgrey, Metal),
				B(-55, 11, 16.1, 20, 10, 1, navy, Plastic),
				B(-55, 11, 16.7, 18.4, 8.4, 0.3, C(235, 220, 170), Plastic),
				B(-55, 16.6, 16, 16, 0.6, 1.6, roofDark, Metal),
				B(-63, 0.5, 16, 3, 1, 3, concrete, Concrete),
				B(-47, 0.5, 16, 3, 1, 3, concrete, Concrete),
			},
		},
		{
			Id = "Impound",
			Yaw = 5,
			Name = "Impound Yard",
			Description = "A fenced yard with a yellow tow truck, wrecked cars and a pile of old tyres.",
			Pad = Vector2.new(-75, 0),
			PriceSeconds = 285,
			Pieces = {
				B(-75, 1.6, -24, 34, 3.2, 0.4, metal, Metal),
				B(-92, 1.6, -12, 0.4, 3.2, 24, metal, Metal),
				B(-58, 1.6, -12, 0.4, 3.2, 24, metal, Metal),
				B(-86, 1.6, 0, 12, 3.2, 0.4, metal, Metal),
				B(-64, 1.6, 0, 12, 3.2, 0.4, metal, Metal),
				B(-77, 0.8, -19, 13, 1.2, 4, black, Plastic),
				B(-80, 2.3, -19, 9, 1, 4.6, yellow, Metal),
				B(-72, 3.4, -19, 4.4, 3.4, 4.6, yellow, Metal),
				B(-80, 5, -19, 0.8, 3.5, 0.8, dgrey, Metal),
				B(-82, 6.5, -19, 6, 0.6, 0.6, dgrey, Metal),
				B(-86, 1.4, -8, 9, 2, 4.4, rust, Metal),
				B(-86, 3, -8, 4.5, 1.2, 3.8, C(125, 70, 45), Metal),
				B(-68, 1.4, -6, 4.4, 2, 9, C(110, 118, 135), Metal),
				B(-68, 3, -6.5, 3.8, 1.2, 4.5, C(95, 100, 115), Metal),
				Cy(-64, 0.8, -20, 2.6, 1.6, black, Plastic),
				Cy(-64, 2.2, -20, 2.6, 1.2, black, Plastic),
			},
		},
		{
			Id = "Bikes",
			Yaw = -6,
			Name = "Bike Patrol",
			Description = "A covered stand with three police motorbikes ready to roll.",
			Pad = Vector2.new(80, 50),
			PriceSeconds = 325,
			Pieces = merge({
				B(72, 3, 61.7, 24, 6, 0.6, white, Concrete),
				B(72, 6.4, 58.3, 25, 0.6, 8.4, navy, Metal),
				Cy(60.5, 3, 54.8, 0.8, 6, metal, Metal),
				Cy(83.5, 3, 54.8, 0.8, 6, metal, Metal),
			}, bike(66), bike(72), bike(78)),
		},
		{
			Id = "Monument",
			Yaw = 15,
			Name = "Golden Badge Monument",
			Description = "A giant golden police badge on a tall navy pedestal, with four lamps around the plaza.",
			Pad = Vector2.new(-24, 14),
			PriceSeconds = 365,
			RewardMult = 1.4,
			Pieces = {
				B(-24, 0.6, 0, 15, 1.2, 15, C(190, 192, 200), Concrete),
				B(-24, 1.7, 0, 11, 1, 11, C(150, 152, 162), Concrete),
				B(-24, 6, 0, 6, 8, 6, navy, Metal),
				B(-24, 10.4, 0, 7.4, 0.8, 7.4, gold, Metal),
				Cz(-24, 17.5, 0, 13, 1.2, gold, Metal),
				Cz(-24, 17.5, 0.9, 10, 0.6, blue, Plastic),
				B(-24, 17.5, 1.4, 5, 5, 0.4, gold, Metal),
				Cy(-32, 2.5, -8, 0.6, 5, dgrey, Metal),
				Cy(-16, 2.5, -8, 0.6, 5, dgrey, Metal),
				Cy(-32, 2.5, 8, 0.6, 5, dgrey, Metal),
				Cy(-16, 2.5, 8, 0.6, 5, dgrey, Metal),
				Ball(-32, 5.6, -8, 1.6, yellow, Plastic),
				Ball(-16, 5.6, -8, 1.6, yellow, Plastic),
				Ball(-32, 5.6, 8, 1.6, yellow, Plastic),
				Ball(-16, 5.6, 8, 1.6, yellow, Plastic),
			},
		},
	},
}

return theme
