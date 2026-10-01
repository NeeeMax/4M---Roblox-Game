--!strict
-- Theme of the Shiba of bay 3 (Config/DecorTypes -> Theme): the Gym. A walled gym hall on the left, a boxing ring on the right,
-- a winding walkway and the Shiba in the far right corner. Stage 184 x 104.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local Mat = Enum.Material
local C = Color3.fromRGB

local RED = C(200, 40, 40)
local RUBBER = C(40, 40, 46)
local STEEL = C(150, 150, 160)
local DARK_STEEL = C(60, 60, 70)
local GOLD = C(255, 200, 40)
local WHITE = C(240, 240, 240)
local CONCRETE = C(78, 78, 90)
local WOOD = C(120, 80, 45)

-- Box: (x, bottom y, z) and size.
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
	}
end

-- Cylinder lying along X, centred at height yc.
local function CylX(
	x: number,
	yc: number,
	z: number,
	length: number,
	diameter: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(length, diameter, diameter),
		Offset = Vector3.new(x, yc, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Standing cylinder (axis up), bottom at y0.
local function CylV(
	x: number,
	y0: number,
	z: number,
	diameter: number,
	height: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(height, diameter, diameter),
		Offset = Vector3.new(x, y0 + height / 2, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

local function append(target: { Piece }, items: { Piece })
	for _, item in items do
		table.insert(target, item)
	end
end

local function bench(x: number, z: number): { Piece }
	return {
		B(x, 0.3, z, 2, 1.2, 5, RUBBER, Mat.Fabric),
		B(x - 1.6, 0.3, z, 0.4, 3, 0.4, STEEL, Mat.Metal),
		B(x + 1.6, 0.3, z, 0.4, 3, 0.4, STEEL, Mat.Metal),
		CylX(x, 3.4, z, 7, 0.4, C(190, 190, 200), Mat.Metal),
		CylX(x - 3.2, 3.4, z, 0.6, 2.4, RUBBER, Mat.Metal),
		CylX(x + 3.2, 3.4, z, 0.6, 2.4, RUBBER, Mat.Metal),
	}
end

local function dumbbell(x: number, y: number, z: number): { Piece }
	return {
		CylX(x, y, z, 2.4, 0.3, STEEL, Mat.Metal),
		CylX(x - 1.1, y, z, 0.5, 1.2, RED, Mat.Metal),
		CylX(x + 1.1, y, z, 0.5, 1.2, RED, Mat.Metal),
	}
end

local function treadmill(x: number, z: number): { Piece }
	return {
		B(x, 0.3, z, 3, 0.8, 7, DARK_STEEL, Mat.Metal),
		B(x, 1.1, z - 3.3, 2.4, 3.4, 0.4, RUBBER, Mat.Metal),
		B(x, 3.4, z - 3.1, 2.2, 1.1, 0.3, C(30, 70, 90), Mat.Glass),
	}
end

-- ---- parts
local floor: { Piece } = {
	B(-62, 0, 25, 48, 0.3, 42, RUBBER, Mat.Slate),
	B(-62, 0.3, 25, 36, 0.1, 30, RED, Mat.Slate),
	B(30, 0, 44, 30, 0.3, 14, RUBBER, Mat.Slate),
	B(30, 0.3, 44, 20, 0.1, 8, RED, Mat.Slate),
	B(58, 0, 6, 28, 0.3, 28, RUBBER, Mat.Slate),
	B(36, 0, -16, 28, 0.3, 24, RUBBER, Mat.Slate),
	B(-62, 0, -32, 30, 0.3, 28, C(60, 60, 68), Mat.Slate),
}

local hall: { Piece } = {
	B(-85.25, 0, 25, 1.5, 12, 42, CONCRETE, Mat.Concrete),
	B(-77.5, 0, 45.25, 17, 12, 1.5, CONCRETE, Mat.Concrete),
	B(-46.5, 0, 45.25, 17, 12, 1.5, CONCRETE, Mat.Concrete),
	B(-77.5, 0, 4.75, 17, 12, 1.5, CONCRETE, Mat.Concrete),
	B(-46.5, 0, 4.75, 17, 12, 1.5, CONCRETE, Mat.Concrete),
	B(-38.75, 0, 11, 1.5, 12, 14, CONCRETE, Mat.Concrete),
	B(-38.75, 0, 39, 1.5, 12, 14, CONCRETE, Mat.Concrete),
	B(-62, 12, 25, 50, 1, 44, C(90, 90, 100), Mat.Metal),
	B(-62, 13, 25, 50, 0.4, 6, RED, Mat.Metal),
	B(-62, 8.5, 46.2, 48, 2.5, 0.5, RED, Mat.Metal),
	B(-62, 10.5, 15, 30, 0.5, 1, WHITE, Mat.SmoothPlastic),
	B(-62, 10.5, 35, 30, 0.5, 1, WHITE, Mat.SmoothPlastic),
}

local sign: { Piece } = {
	B(60, 0, 38, 1, 8, 1, DARK_STEEL, Mat.Metal),
	B(80, 0, 38, 1, 8, 1, DARK_STEEL, Mat.Metal),
	B(70, 6, 38, 24, 9, 1, RUBBER, Mat.SmoothPlastic),
	B(70, 15, 38, 25, 0.8, 1.4, GOLD, Mat.Metal),
	B(70, 5.4, 38, 25, 0.8, 1.4, GOLD, Mat.Metal),
}
for i = 0, 3 do
	local x = 62.5 + i * 5
	table.insert(sign, B(x, 7.5, 38.6, 3.6, 6, 0.4, RED, Mat.SmoothPlastic))
	table.insert(sign, B(x, 9.5, 38.9, 1.2, 2, 0.3, RUBBER, Mat.SmoothPlastic))
end

local benches: { Piece } = {}
append(benches, bench(-78, 36))
append(benches, bench(-68, 36))

local racks: { Piece } = {
	B(-82.2, 0.3, 15, 3, 0.4, 14, DARK_STEEL, Mat.Metal),
	B(-82.2, 2.4, 15, 3, 0.4, 14, DARK_STEEL, Mat.Metal),
	B(-82.2, 0.3, 8.3, 3, 3.6, 0.4, DARK_STEEL, Mat.Metal),
	B(-82.2, 0.3, 15, 3, 3.6, 0.4, DARK_STEEL, Mat.Metal),
	B(-82.2, 0.3, 21.7, 3, 3.6, 0.4, DARK_STEEL, Mat.Metal),
}
for i = 0, 2 do
	append(racks, dumbbell(-82.2, 3.2, 11.5 + i * 3.5))
end

local treadmills: { Piece } = {}
for i = 0, 2 do
	append(treadmills, treadmill(-54 + i * 5.5, 10))
end

local ring: { Piece } = {
	B(58, 0, 6, 20, 1.5, 20, DARK_STEEL, Mat.Metal),
	B(58, 1.5, 6, 19, 0.2, 19, RED, Mat.Fabric),
}
for _, sx in { -9.4, 9.4 } do
	for _, sz in { -9.4, 9.4 } do
		table.insert(ring, CylV(58 + sx, 1.7, 6 + sz, 0.8, 4.6, DARK_STEEL, Mat.Metal))
	end
end
for _, h in { 3.2, 4.8 } do
	table.insert(ring, B(58, h, 6 - 9.4, 18, 0.25, 0.25, WHITE, Mat.Fabric))
	table.insert(ring, B(58, h, 6 + 9.4, 18, 0.25, 0.25, WHITE, Mat.Fabric))
	table.insert(ring, B(58 - 9.4, h, 6, 0.25, 0.25, 18, RED, Mat.Fabric))
	table.insert(ring, B(58 + 9.4, h, 6, 0.25, 0.25, 18, RED, Mat.Fabric))
end

local bags: { Piece } = {
	B(23, 0, -20, 0.8, 7, 0.8, DARK_STEEL, Mat.Metal),
	B(45, 0, -20, 0.8, 7, 0.8, DARK_STEEL, Mat.Metal),
	B(34, 7, -20, 24, 0.6, 0.6, STEEL, Mat.Metal),
	B(25, 0, -32, 0.8, 9, 0.8, DARK_STEEL, Mat.Metal),
	B(37, 0, -32, 0.8, 9, 0.8, DARK_STEEL, Mat.Metal),
	B(31, 8.4, -32, 13, 0.4, 0.4, STEEL, Mat.Metal),
}
for i = 0, 2 do
	local x = 28 + i * 6
	table.insert(bags, CylV(x, 6.4, -20, 0.2, 0.6, STEEL, Mat.Metal))
	table.insert(bags, CylV(x, 1, -20, 2.6, 5.4, RED, Mat.Fabric))
end

local bar: { Piece } = {
	B(-62, 0, -30, 20, 3.6, 4, WOOD, Mat.Wood),
	B(-62, 3.6, -30, 20.6, 0.4, 4.8, C(40, 30, 25), Mat.Wood),
	B(-62, 0, -36, 20, 8, 1, C(60, 60, 75), Mat.Concrete),
}
for i = 0, 3 do
	table.insert(bar, CylV(-69 + i * 4.6, 4, -30, 1.6, 2, if i % 2 == 0 then RED else GOLD, Mat.Plastic))
end
for i = 0, 1 do
	table.insert(bar, CylV(-66 + i * 8, 0, -26.5, 1.6, 2.6, RED, Mat.Fabric))
end
for i = 0, 4 do
	table.insert(
		bar,
		B(-86 + i * 3.6, 0, -47, 3.2, 7, 2, if i % 2 == 0 then C(50, 90, 160) else C(170, 50, 50), Mat.Metal)
	)
end

local showpiece: { Piece } = {
	B(20, 0, -46, 16, 1.2, 7, C(40, 30, 25), Mat.Wood),
	B(20, 1.2, -46, 12, 1.2, 5, C(70, 55, 40), Mat.Wood),
	CylV(15, 2.4, -46, 1.4, 4.4, GOLD, Mat.Metal),
	CylV(25, 2.4, -46, 1.4, 4.4, GOLD, Mat.Metal),
	CylX(20, 7, -46, 16, 0.9, GOLD, Mat.Metal),
	CylX(12.2, 7, -46, 1.2, 6, GOLD, Mat.Metal),
	CylX(10.8, 7, -46, 1.2, 4.6, GOLD, Mat.Metal),
	CylX(27.8, 7, -46, 1.2, 6, GOLD, Mat.Metal),
	CylX(29.2, 7, -46, 1.2, 4.6, GOLD, Mat.Metal),
	B(20, 2.4, -43.2, 6, 1.4, 0.3, GOLD, Mat.Metal),
}

local theme: DecorTypes.Theme = {
	Key = "GymHall",
	Name = "Gym",
	Area = Vector2.new(184, 104),
	Shiba = { Position = Vector2.new(68, -30), Facing = 180 },
	Path = {
		Vector2.new(0, 52),
		Vector2.new(45, 30),
		Vector2.new(10, 0),
		Vector2.new(-40, -20),
		Vector2.new(0, -52),
	},
	BayPad = Vector2.new(68, -20),
	AutoPad = Vector2.new(62, -40),
	Parts = {
		{
			Id = "Floor",
			Name = "Rubber Gym Floor",
			Description = "Black rubber flooring with red tiles under the hall, the ring and the trail.",
			Pad = Vector2.new(25, 48),
			PriceSeconds = 10,
			Pieces = floor,
		},
		{
			Id = "Hall",
			Name = "Gym Hall",
			Description = "Tall concrete walls with wide doorways and a steel roof with a red stripe.",
			Pad = Vector2.new(-62, 49),
			PriceSeconds = 18,
			Pieces = hall,
		},
		{
			Id = "Sign",
			Name = "Get Bonked Sign",
			Description = "A big black board with red letters and a gold trim.",
			Pad = Vector2.new(70, 47),
			PriceSeconds = 30,
			Pieces = sign,
		},
		{
			Id = "Benches",
			Name = "Bench Presses",
			Description = "Two padded benches with loaded barbells.",
			Pad = Vector2.new(-73, 28),
			PriceSeconds = 48,
			Pieces = benches,
		},
		{
			Id = "Racks",
			Name = "Dumbbell Rack",
			Description = "A long rack with chunky red dumbbells.",
			Pad = Vector2.new(-76, 15),
			PriceSeconds = 70,
			Pieces = racks,
		},
		{
			Id = "Treadmills",
			Name = "Treadmills",
			Description = "Three treadmills in a row with little screens.",
			Pad = Vector2.new(-48.5, 21),
			PriceSeconds = 95,
			Pieces = treadmills,
		},
		{
			Id = "Ring",
			Name = "Boxing Ring",
			Description = "A raised ring with a red canvas and solid ropes.",
			Pad = Vector2.new(58, 21),
			PriceSeconds = 125,
			Pieces = ring,
		},
		{
			Id = "Bags",
			Name = "Bags and Pull-up Bars",
			Description = "Three heavy bags on a beam and a pull-up rig.",
			Pad = Vector2.new(34, -13),
			PriceSeconds = 155,
			Pieces = bags,
		},
		{
			Id = "Bar",
			Name = "Protein Bar and Lockers",
			Description = "A wooden protein bar with tubs and stools, and a row of lockers.",
			Pad = Vector2.new(-62, -24),
			PriceSeconds = 185,
			Pieces = bar,
		},
		{
			Id = "Trophy",
			Name = "Golden Barbell",
			Description = "The showpiece: a giant golden barbell on a pedestal.",
			Pad = Vector2.new(20, -37),
			PriceSeconds = 220,
			Pieces = showpiece,
		},
	},
}

return theme
