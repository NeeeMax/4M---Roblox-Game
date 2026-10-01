--!strict
-- Theme of the Shiba of bay 1 (Config/DecorTypes → Theme): "Little House". The Shiba stands inside a big cottage in the
-- back-right of a wide stage; the walkway winds from the front-left to the cottage door and back to the exit.

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

-- A car wheel with its axis along Z.
local function wheel(x: number, z: number): DecorTypes.Piece
	return piece(
		Vector3.new(1.2, 3.4, 3.4),
		Vector3.new(x, 1.7, z),
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
local gold = Color3.fromRGB(240, 190, 50)

-- The cottage stands around the Shiba at (67, -26), open toward -X (the walkway side). Interior x 50.5..84.5 (34 wide),
-- z -41..-11 (30 deep), walls 14 high, doorway z -35..-17 (18 wide).
local HX, HZ = 67, -26

local theme: DecorTypes.Theme = {
	Key = "LittleHouse",
	Name = "Little House",
	Area = Vector2.new(180, 110),
	Shiba = { Position = Vector2.new(HX, HZ), Facing = 180 },
	Path = {
		Vector2.new(0, 55),
		Vector2.new(-40, 36),
		Vector2.new(-6, 12),
		Vector2.new(40, -8),
		Vector2.new(30, -36),
		Vector2.new(0, -55),
	},
	BayPad = Vector2.new(46, -2),
	AutoPad = Vector2.new(60, -37),
	Parts = {
		{
			Id = "Flooring",
			Name = "Garden Flooring",
			Description = "A flagstone patio at the gate and a warm wooden floor inside the big cottage.",
			Pad = Vector2.new(18, 44),
			PriceSeconds = 10,
			Pieces = {
				slab(18, 0.25, 47, 28, 0.4, 14, stone, Enum.Material.Slate),
				slab(HX, 0.25, HZ, 35, 0.4, 31, wood, Enum.Material.WoodPlanks),
				slab(44, 0.25, HZ, 8, 0.4, 20, Color3.fromRGB(120, 120, 126), Enum.Material.Cobblestone),
				slab(36, 0.25, 36, 8, 0.4, 8, stone, Enum.Material.Slate),
			},
		},
		{
			Id = "LittleHouse",
			Name = "Little House",
			Description = "A big cosy brick cottage with a red roof, built right around the Shiba.",
			Pad = Vector2.new(44, -26),
			PriceSeconds = 15,
			RewardMult = 2,
			Pieces = {
				-- back wall, side walls, front wall pieces left and right of the doorway
				block(85, HZ, 1, 14, 31, brick, Enum.Material.Brick),
				block(67.5, -41.5, 36, 14, 1, plaster, Enum.Material.SmoothPlastic),
				block(67.5, -10.5, 36, 14, 1, plaster, Enum.Material.SmoothPlastic),
				block(50, -38, 1, 14, 6, brick, Enum.Material.Brick),
				block(50, -14, 1, 14, 6, brick, Enum.Material.Brick),
				-- stepped roof, all above 7 studs
				slab(HX, 14.5, HZ, 40, 1, 36, roofRed, Enum.Material.Slate),
				slab(HX, 15.5, HZ, 34, 1, 30, roofRed, Enum.Material.Slate),
				slab(HX, 16.5, HZ, 26, 1, 24, roofRed, Enum.Material.Slate),
				slab(HX, 17.5, HZ, 18, 1, 16, roofRed, Enum.Material.Slate),
				slab(HX, 18.5, HZ, 10, 1, 8, roofRed, Enum.Material.Slate),
				-- chimney and doorstep
				block(80, -38, 4, 22, 4, brick, Enum.Material.Brick),
				slab(80, 22.3, -38, 5, 0.6, 5, stone, Enum.Material.Concrete),
				slab(47.5, 0.3, HZ, 4, 0.5, 18, stone, Enum.Material.Slate),
			},
		},
		{
			Id = "BonkedSign",
			Name = "Get Bonked Sign",
			Description = "A big yellow signboard so everybody knows what happens here.",
			Pad = Vector2.new(36, 35),
			PriceSeconds = 20,
			Pieces = {
				pole(26, 28, 1.6, 12, wood, Enum.Material.Wood),
				pole(46, 28, 1.6, 12, wood, Enum.Material.Wood),
				slab(36, 9.5, 28, 24, 9, 1.2, Color3.fromRGB(250, 200, 60), Enum.Material.WoodPlanks),
				slab(36, 13.6, 28.7, 24, 0.9, 0.6, roofRed, Enum.Material.Wood),
				slab(36, 5.4, 28.7, 24, 0.9, 0.6, roofRed, Enum.Material.Wood),
				slab(31, 9.5, 28.7, 4.5, 1.8, 0.6, white, Enum.Material.SmoothPlastic),
				slab(41, 9.5, 28.7, 4.5, 1.8, 0.6, white, Enum.Material.SmoothPlastic),
				slab(36, 9.5, 28.7, 3, 3.6, 0.6, white, Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Garage",
			Name = "Garage with Car",
			Description = "A roomy garage with a little blue car parked inside.",
			Pad = Vector2.new(-68, 46),
			PriceSeconds = 25,
			RewardMult = 1.25,
			Pieces = {
				block(-68, 14, 36, 12, 1, brick, Enum.Material.Brick),
				block(-85.5, 26, 1, 12, 25, plaster, Enum.Material.SmoothPlastic),
				block(-50.5, 26, 1, 12, 25, plaster, Enum.Material.SmoothPlastic),
				slab(-68, 12.5, 26, 38, 1, 27, Color3.fromRGB(90, 90, 100), Enum.Material.Slate),
				slab(-68, 3, 26, 14, 3, 6.5, Color3.fromRGB(60, 120, 200), Enum.Material.SmoothPlastic),
				slab(-69, 5.8, 26, 7, 2.6, 6, Color3.fromRGB(170, 210, 240), Enum.Material.Glass),
				wheel(-72.6, 22.2),
				wheel(-63.4, 22.2),
				wheel(-72.6, 29.8),
				wheel(-63.4, 29.8),
			},
		},
		{
			Id = "Mailbox",
			Name = "Mailbox",
			Description = "A red mailbox with its little flag up. Someone wrote to the Shiba!",
			Pad = Vector2.new(62, 50),
			PriceSeconds = 35,
			Pieces = {
				pole(62, 44, 1.2, 6, wood, Enum.Material.Wood),
				slab(62, 7, 44, 4, 2.6, 2.6, Color3.fromRGB(200, 50, 50), Enum.Material.Metal),
				slab(64.4, 8.2, 44, 0.5, 2, 0.5, Color3.fromRGB(250, 220, 60), Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Fence",
			Name = "White Picket Fence",
			Description = "A tall white fence closes off the front garden.",
			Pad = Vector2.new(77, 46),
			PriceSeconds = 45,
			RewardMult = 1.1,
			Pieces = {
				block(66, 38, 1.2, 6.6, 1.2, white, Enum.Material.Wood),
				block(71.5, 38, 1.2, 6.6, 1.2, white, Enum.Material.Wood),
				block(77, 38, 1.2, 6.6, 1.2, white, Enum.Material.Wood),
				block(82.5, 38, 1.2, 6.6, 1.2, white, Enum.Material.Wood),
				block(88, 38, 1.2, 6.6, 1.2, white, Enum.Material.Wood),
				slab(77, 2.2, 38, 23, 0.8, 0.8, white, Enum.Material.Wood),
				slab(77, 5, 38, 23, 0.8, 0.8, white, Enum.Material.Wood),
				slab(77, 3.6, 38.5, 22, 4.4, 0.4, white, Enum.Material.WoodPlanks),
			},
		},
		{
			Id = "Garden",
			Name = "Flower Beds",
			Description = "Two long beds full of red, yellow and pink flowers.",
			Pad = Vector2.new(-44, 14),
			PriceSeconds = 60,
			RewardMult = 1.2,
			Pieces = {
				block(-44, 2, 22, 1.6, 7, Color3.fromRGB(92, 64, 44), Enum.Material.Ground),
				block(-44, -10, 22, 1.6, 7, Color3.fromRGB(92, 64, 44), Enum.Material.Ground),
				ball(-51, 2.8, 2, 2.4, Color3.fromRGB(230, 60, 70), Enum.Material.SmoothPlastic),
				ball(-47, 2.8, 2, 2.4, Color3.fromRGB(250, 210, 60), Enum.Material.SmoothPlastic),
				ball(-43, 2.8, 2, 2.4, Color3.fromRGB(240, 120, 190), Enum.Material.SmoothPlastic),
				ball(-39, 2.8, 2, 2.4, Color3.fromRGB(250, 250, 250), Enum.Material.SmoothPlastic),
				ball(-51, 2.8, -10, 2.4, Color3.fromRGB(250, 210, 60), Enum.Material.SmoothPlastic),
				ball(-47, 2.8, -10, 2.4, Color3.fromRGB(240, 120, 190), Enum.Material.SmoothPlastic),
				ball(-43, 2.8, -10, 2.4, Color3.fromRGB(230, 60, 70), Enum.Material.SmoothPlastic),
				ball(-39, 2.8, -10, 2.4, Color3.fromRGB(150, 110, 230), Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Tree",
			Name = "Big Oak Tree",
			Description = "A huge oak that gives the whole yard some shade.",
			Pad = Vector2.new(-62, -18),
			PriceSeconds = 80,
			RewardMult = 1.2,
			Pieces = {
				pole(-62, -30, 4.5, 18, Color3.fromRGB(110, 76, 44), Enum.Material.Wood),
				ball(-62, 26, -30, 26, Color3.fromRGB(70, 150, 70), Enum.Material.Grass),
				ball(-72, 21, -34, 16, Color3.fromRGB(80, 165, 80), Enum.Material.Grass),
				ball(-52, 21, -26, 16, Color3.fromRGB(60, 140, 66), Enum.Material.Grass),
			},
		},
		{
			Id = "DoghouseBench",
			Name = "Doghouse and Bench",
			Description = "A snug doghouse and a wooden bench to watch the bonking from.",
			Pad = Vector2.new(8, -12),
			PriceSeconds = 110,
			RewardMult = 1.3,
			Pieces = {
				block(0, -24, 8, 6, 8, Color3.fromRGB(190, 70, 60), Enum.Material.WoodPlanks),
				slab(0, 6.5, -24, 10, 1, 10, roofRed, Enum.Material.Wood),
				slab(0, 2, -19.8, 3.2, 4, 0.4, Color3.fromRGB(40, 28, 24), Enum.Material.SmoothPlastic),
				slab(18, 3.2, -26, 12, 1, 3.5, wood, Enum.Material.WoodPlanks),
				slab(18, 5.6, -27.6, 12, 3.4, 0.6, wood, Enum.Material.WoodPlanks),
				block(13, -26, 1, 3, 3, Color3.fromRGB(60, 60, 66), Enum.Material.Metal),
				block(23, -26, 1, 3, 3, Color3.fromRGB(60, 60, 66), Enum.Material.Metal),
			},
		},
		{
			Id = "Fountain",
			Name = "Golden Bone Fountain",
			Description = "The showpiece: a stone fountain crowned with a shining golden bone.",
			Pad = Vector2.new(-24, -22),
			PriceSeconds = 150,
			RewardMult = 1.5,
			Pieces = {
				piece(
					Vector3.new(3, 22, 22),
					Vector3.new(-24, 1.5, -38),
					stone,
					Enum.Material.Cobblestone,
					Enum.PartType.Cylinder,
					Vector3.new(0, 0, 90)
				),
				piece(
					Vector3.new(0.4, 19, 19),
					Vector3.new(-24, 2.8, -38),
					Color3.fromRGB(90, 170, 230),
					Enum.Material.Glass,
					Enum.PartType.Cylinder,
					Vector3.new(0, 0, 90)
				),
				pole(-24, -38, 4, 9, stone, Enum.Material.Slate),
				slab(-24, 11, -38, 10, 2, 2, gold, Enum.Material.Metal),
				ball(-29, 11, -39, 3, gold, Enum.Material.Metal),
				ball(-29, 11, -37, 3, gold, Enum.Material.Metal),
				ball(-19, 11, -39, 3, gold, Enum.Material.Metal),
				ball(-19, 11, -37, 3, gold, Enum.Material.Metal),
			},
		},
	},
}

return theme
