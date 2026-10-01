--!strict
-- Theme of the Shiba of bay 1 (Config/DecorTypes → Theme): "Little House". The Shiba stands inside its own little house in the
-- back-right corner of a wide stage; the walkway winds from the front-left to the back-right and back to the exit.

local DecorTypes = require(script.Parent.DecorTypes)

local function piece(
	size: Vector3,
	offset: Vector3,
	color: Color3,
	material: Enum.Material?,
	shape: Enum.PartType?,
	rotation: Vector3?
): DecorTypes.Piece
	return {
		Size = size,
		Offset = offset,
		Color = color,
		Material = material,
		Shape = shape,
		Rotation = rotation,
	}
end

-- A block standing on the ground: x, z = centre, h = height.
local function block(
	x: number,
	z: number,
	w: number,
	h: number,
	d: number,
	color: Color3,
	material: Enum.Material
): DecorTypes.Piece
	return piece(Vector3.new(w, h, d), Vector3.new(x, h / 2, z), color, material, nil, nil)
end

-- A block at a given height (y = centre).
local function slab(
	x: number,
	y: number,
	z: number,
	w: number,
	h: number,
	d: number,
	color: Color3,
	material: Enum.Material
): DecorTypes.Piece
	return piece(Vector3.new(w, h, d), Vector3.new(x, y, z), color, material, nil, nil)
end

-- A standing pole (cylinder with a vertical axis).
local function pole(
	x: number,
	z: number,
	diameter: number,
	h: number,
	color: Color3,
	material: Enum.Material
): DecorTypes.Piece
	return piece(
		Vector3.new(h, diameter, diameter),
		Vector3.new(x, h / 2, z),
		color,
		material,
		Enum.PartType.Cylinder,
		Vector3.new(0, 0, 90)
	)
end

local function ball(
	x: number,
	y: number,
	z: number,
	d: number,
	color: Color3,
	material: Enum.Material
): DecorTypes.Piece
	return piece(Vector3.new(d, d, d), Vector3.new(x, y, z), color, material, Enum.PartType.Ball, nil)
end

-- A wheel with its axis along Z.
local function wheel(x: number, z: number): DecorTypes.Piece
	return piece(
		Vector3.new(0.9, 2.2, 2.2),
		Vector3.new(x, 1.1, z),
		Color3.fromRGB(30, 30, 34),
		Enum.Material.SmoothPlastic,
		Enum.PartType.Cylinder,
		Vector3.new(0, 90, 0)
	)
end

local plaster = Color3.fromRGB(246, 232, 200)
local brick = Color3.fromRGB(176, 88, 66)
local roofRed = Color3.fromRGB(150, 60, 56)
local wood = Color3.fromRGB(150, 104, 62)
local white = Color3.fromRGB(245, 245, 240)
local stone = Color3.fromRGB(150, 150, 156)

-- The house stands around the Shiba at (58, -20), open toward -X.
local HX, HZ = 58, -20

local theme: DecorTypes.Theme = {
	Key = "LittleHouse",
	Name = "Little House",
	Area = Vector2.new(160, 86),
	Shiba = { Position = Vector2.new(HX, HZ), Facing = 180 },
	Path = {
		Vector2.new(0, 43),
		Vector2.new(-32, 27),
		Vector2.new(-4, 8),
		Vector2.new(34, -10),
		Vector2.new(26, -30),
		Vector2.new(0, -43),
	},
	BayPad = Vector2.new(41, -4),
	AutoPad = Vector2.new(40, -32),
	Parts = {
		{
			Id = "Flooring",
			Name = "Garden Flooring",
			Description = "A flagstone patio at the gate and a warm wooden floor inside the little house.",
			Pad = Vector2.new(14, 34),
			PriceSeconds = 10,
			Pieces = {
				slab(14, 0.25, 36, 18, 0.4, 12, stone, Enum.Material.Slate),
				slab(HX, 0.25, HZ, 23, 0.4, 23, wood, Enum.Material.WoodPlanks),
				slab(37, 0.25, -20, 6, 0.4, 14, Color3.fromRGB(120, 120, 126), Enum.Material.Cobblestone),
				slab(24, 0.25, 22, 5, 0.4, 5, stone, Enum.Material.Slate),
			},
		},
		{
			Id = "LittleHouse",
			Name = "Little House",
			Description = "A cosy brick cottage with a red roof, built right around the Shiba.",
			Pad = Vector2.new(38, -20),
			PriceSeconds = 15,
			Pieces = {
				-- back wall, side walls, front wall pieces left and right of the doorway
				block(70, HZ, 1, 8, 24, brick, Enum.Material.Brick),
				block(58, -32, 24, 8, 1, plaster, Enum.Material.SmoothPlastic),
				block(58, -8, 24, 8, 1, plaster, Enum.Material.SmoothPlastic),
				block(46, -29.5, 1, 8, 5, brick, Enum.Material.Brick),
				block(46, -10.5, 1, 8, 5, brick, Enum.Material.Brick),
				slab(46, 7.5, HZ, 1, 1, 14, wood, Enum.Material.Wood),
				-- stepped roof
				slab(HX, 8.5, HZ, 27, 1, 27, roofRed, Enum.Material.Slate),
				slab(HX, 9.5, HZ, 22, 1, 22, roofRed, Enum.Material.Slate),
				slab(HX, 10.5, HZ, 16, 1, 16, roofRed, Enum.Material.Slate),
				slab(HX, 11.5, HZ, 10, 1, 10, roofRed, Enum.Material.Slate),
				slab(HX, 12.5, HZ, 4, 1, 4, roofRed, Enum.Material.Slate),
				-- chimney and doorstep
				block(66, -29, 3, 14, 3, brick, Enum.Material.Brick),
				slab(66, 14.3, -29, 4, 0.6, 4, stone, Enum.Material.Concrete),
				slab(43.5, 0.3, HZ, 3, 0.5, 14, stone, Enum.Material.Slate),
			},
		},
		{
			Id = "BonkedSign",
			Name = "Get Bonked Sign",
			Description = "A big yellow signboard so everybody knows what happens here.",
			Pad = Vector2.new(30, 26),
			PriceSeconds = 20,
			Pieces = {
				pole(24, 21, 1, 8, wood, Enum.Material.Wood),
				pole(36, 21, 1, 8, wood, Enum.Material.Wood),
				slab(30, 6.5, 21, 16, 6, 0.8, Color3.fromRGB(250, 200, 60), Enum.Material.WoodPlanks),
				slab(30, 8.9, 21.5, 16, 0.6, 0.4, roofRed, Enum.Material.Wood),
				slab(30, 4.1, 21.5, 16, 0.6, 0.4, roofRed, Enum.Material.Wood),
				slab(27.5, 6.5, 21.5, 3, 1.2, 0.4, white, Enum.Material.SmoothPlastic),
				slab(32.5, 6.5, 21.5, 3, 1.2, 0.4, white, Enum.Material.SmoothPlastic),
				slab(30, 6.5, 21.5, 2, 2.4, 0.4, white, Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Garage",
			Name = "Garage with Car",
			Description = "A tidy garage with a little blue car parked inside.",
			Pad = Vector2.new(-58, 34),
			PriceSeconds = 25,
			Pieces = {
				block(-58, 12.5, 24, 8, 1, brick, Enum.Material.Brick),
				block(-69.5, 20, 1, 8, 16, plaster, Enum.Material.SmoothPlastic),
				block(-46.5, 20, 1, 8, 16, plaster, Enum.Material.SmoothPlastic),
				slab(-58, 8.5, 20.5, 28, 1, 19, Color3.fromRGB(90, 90, 100), Enum.Material.Slate),
				slab(-58, 2, 18, 9, 2, 4.5, Color3.fromRGB(60, 120, 200), Enum.Material.SmoothPlastic),
				slab(-58.5, 3.9, 18, 4.5, 1.8, 4, Color3.fromRGB(170, 210, 240), Enum.Material.Glass),
				wheel(-61, 15.8),
				wheel(-55, 15.8),
				wheel(-61, 20.2),
				wheel(-55, 20.2),
			},
		},
		{
			Id = "Mailbox",
			Name = "Mailbox",
			Description = "A red mailbox with its little flag up. Someone wrote to the Shiba!",
			Pad = Vector2.new(50, 37),
			PriceSeconds = 35,
			Pieces = {
				pole(50, 32, 0.8, 4, wood, Enum.Material.Wood),
				slab(50, 4.6, 32, 2.6, 1.8, 1.8, Color3.fromRGB(200, 50, 50), Enum.Material.Metal),
				slab(51.5, 5.4, 32, 0.3, 1.4, 0.3, Color3.fromRGB(250, 220, 60), Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Fence",
			Name = "White Picket Fence",
			Description = "A cheerful white fence closes off the front garden.",
			Pad = Vector2.new(67, 33),
			PriceSeconds = 45,
			Pieces = {
				block(58, 27, 0.8, 4.4, 0.8, white, Enum.Material.Wood),
				block(62.5, 27, 0.8, 4.4, 0.8, white, Enum.Material.Wood),
				block(67, 27, 0.8, 4.4, 0.8, white, Enum.Material.Wood),
				block(71.5, 27, 0.8, 4.4, 0.8, white, Enum.Material.Wood),
				block(76, 27, 0.8, 4.4, 0.8, white, Enum.Material.Wood),
				slab(67, 1.5, 27, 18.8, 0.5, 0.5, white, Enum.Material.Wood),
				slab(67, 3.3, 27, 18.8, 0.5, 0.5, white, Enum.Material.Wood),
				slab(67, 2.4, 27.3, 18, 3, 0.25, white, Enum.Material.WoodPlanks),
			},
		},
		{
			Id = "Garden",
			Name = "Flower Beds",
			Description = "Two beds full of red, yellow and pink flowers.",
			Pad = Vector2.new(-34, 8),
			PriceSeconds = 60,
			Pieces = {
				block(-34, 0, 16, 1.2, 5, Color3.fromRGB(92, 64, 44), Enum.Material.Ground),
				block(-34, -10, 16, 1.2, 5, Color3.fromRGB(92, 64, 44), Enum.Material.Ground),
				ball(-39, 2, 0, 1.6, Color3.fromRGB(230, 60, 70), Enum.Material.SmoothPlastic),
				ball(-36, 2, 0, 1.6, Color3.fromRGB(250, 210, 60), Enum.Material.SmoothPlastic),
				ball(-33, 2, 0, 1.6, Color3.fromRGB(240, 120, 190), Enum.Material.SmoothPlastic),
				ball(-30, 2, 0, 1.6, Color3.fromRGB(250, 250, 250), Enum.Material.SmoothPlastic),
				ball(-39, 2, -10, 1.6, Color3.fromRGB(250, 210, 60), Enum.Material.SmoothPlastic),
				ball(-36, 2, -10, 1.6, Color3.fromRGB(240, 120, 190), Enum.Material.SmoothPlastic),
				ball(-33, 2, -10, 1.6, Color3.fromRGB(230, 60, 70), Enum.Material.SmoothPlastic),
				ball(-30, 2, -10, 1.6, Color3.fromRGB(150, 110, 230), Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Tree",
			Name = "Big Oak Tree",
			Description = "A tall oak that gives the whole yard some shade.",
			Pad = Vector2.new(-45, -14),
			PriceSeconds = 80,
			Pieces = {
				pole(-45, -25, 3.2, 12, Color3.fromRGB(110, 76, 44), Enum.Material.Wood),
				ball(-45, 16, -25, 17, Color3.fromRGB(70, 150, 70), Enum.Material.Grass),
				ball(-51, 14, -28, 11, Color3.fromRGB(80, 165, 80), Enum.Material.Grass),
				ball(-39, 14, -22, 11, Color3.fromRGB(60, 140, 66), Enum.Material.Grass),
			},
		},
		{
			Id = "DoghouseBench",
			Name = "Doghouse and Bench",
			Description = "A snug doghouse and a wooden bench to watch the bonking from.",
			Pad = Vector2.new(7, -10),
			PriceSeconds = 110,
			Pieces = {
				block(0, -16, 5, 3.6, 5, Color3.fromRGB(190, 70, 60), Enum.Material.WoodPlanks),
				slab(0, 4, -16, 6.4, 0.6, 6.4, roofRed, Enum.Material.Wood),
				slab(0, 1.2, -13.4, 2, 2.2, 0.3, Color3.fromRGB(40, 28, 24), Enum.Material.SmoothPlastic),
				slab(14, 2, -16, 7, 0.6, 2, wood, Enum.Material.WoodPlanks),
				slab(14, 3.6, -17, 7, 2, 0.4, wood, Enum.Material.WoodPlanks),
				block(11, -16, 0.6, 2, 1.6, Color3.fromRGB(60, 60, 66), Enum.Material.Metal),
				block(17, -16, 0.6, 2, 1.6, Color3.fromRGB(60, 60, 66), Enum.Material.Metal),
			},
		},
		{
			Id = "Fountain",
			Name = "Golden Bone Fountain",
			Description = "The showpiece: a stone fountain crowned with a shining golden bone.",
			Pad = Vector2.new(-12, -17),
			PriceSeconds = 150,
			Pieces = {
				piece(
					Vector3.new(2, 15, 15),
					Vector3.new(-12, 1, -28),
					stone,
					Enum.Material.Cobblestone,
					Enum.PartType.Cylinder,
					Vector3.new(0, 0, 90)
				),
				piece(
					Vector3.new(0.3, 13, 13),
					Vector3.new(-12, 1.9, -28),
					Color3.fromRGB(90, 170, 230),
					Enum.Material.Glass,
					Enum.PartType.Cylinder,
					Vector3.new(0, 0, 90)
				),
				pole(-12, -28, 2.4, 6, stone, Enum.Material.Slate),
				slab(-12, 7.5, -28, 6, 1.2, 1.2, Color3.fromRGB(240, 190, 50), Enum.Material.Metal),
				ball(-15, 7.1, -28.5, 1.8, Color3.fromRGB(240, 190, 50), Enum.Material.Metal),
				ball(-15, 7.1, -27.5, 1.8, Color3.fromRGB(240, 190, 50), Enum.Material.Metal),
				ball(-9, 7.1, -28.5, 1.8, Color3.fromRGB(240, 190, 50), Enum.Material.Metal),
				ball(-9, 7.1, -27.5, 1.8, Color3.fromRGB(240, 190, 50), Enum.Material.Metal),
			},
		},
	},
}

return theme
