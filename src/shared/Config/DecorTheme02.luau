--!strict
-- Theme of the Shiba of bay 2: "Beach Bar" (Config/DecorTypes → Theme). A winding boardwalk across a sandy beach, a bar hut on the
-- left, the sea along the right edge and the Shiba standing at the water.

local DecorTypes = require(script.Parent.DecorTypes)

local function piece(
	size: Vector3,
	offset: Vector3,
	color: Color3,
	material: Enum.Material?,
	shape: Enum.PartType?,
	rotation: Vector3?
): DecorTypes.Piece
	return { Size = size, Offset = offset, Color = color, Material = material, Shape = shape, Rotation = rotation }
end

local BLOCK = Enum.PartType.Block
local CYL = Enum.PartType.Cylinder
local BALL = Enum.PartType.Ball
local WOOD = Enum.Material.Wood
local PLANK = Enum.Material.WoodPlanks
local SAND = Enum.Material.Sand
local PLASTIC = Enum.Material.SmoothPlastic
local FABRIC = Enum.Material.Fabric

local TRUNK = Color3.fromRGB(139, 101, 62)
local LEAF = Color3.fromRGB(46, 139, 70)
local WHITE = Color3.fromRGB(245, 245, 240)
local RED = Color3.fromRGB(214, 62, 54)
local TEAL = Color3.fromRGB(32, 178, 170)
local YELLOW = Color3.fromRGB(250, 205, 70)
local THATCH = Color3.fromRGB(196, 160, 96)
local DARKWOOD = Color3.fromRGB(110, 76, 46)
local DECK = Color3.fromRGB(160, 116, 70)

-- A standing pole (cylinder with a vertical axis) from the ground up.
local function pole(
	x: number,
	z: number,
	height: number,
	thickness: number,
	color: Color3,
	material: Enum.Material?
): DecorTypes.Piece
	return piece(
		Vector3.new(height, thickness, thickness),
		Vector3.new(x, height / 2, z),
		color,
		material,
		CYL,
		Vector3.new(0, 0, 90)
	)
end

-- A palm tree: trunk, three crossing fronds and a coconut ball.
local function palm(pieces: { DecorTypes.Piece }, x: number, z: number, height: number, yaw: number)
	table.insert(pieces, pole(x, z, height, 1.8, TRUNK, WOOD))
	for k = 0, 2 do
		table.insert(
			pieces,
			piece(
				Vector3.new(13, 0.6, 3.5),
				Vector3.new(x, height + 0.6, z),
				LEAF,
				FABRIC,
				BLOCK,
				Vector3.new(0, yaw + k * 60, 0)
			)
		)
	end
	table.insert(pieces, piece(Vector3.new(2.2, 2.2, 2.2), Vector3.new(x, height - 1.2, z), DARKWOOD, PLASTIC, BALL))
end

-- A parasol: pole and a flat round canopy above head height.
local function parasol(pieces: { DecorTypes.Piece }, x: number, z: number, color: Color3)
	table.insert(pieces, pole(x, z, 14, 0.8, WHITE, PLASTIC))
	table.insert(
		pieces,
		piece(Vector3.new(0.8, 12, 12), Vector3.new(x, 14.4, z), color, FABRIC, CYL, Vector3.new(0, 0, 90))
	)
end

-- A sun lounger (long along Z): base and a tilted backrest.
local function lounger(pieces: { DecorTypes.Piece }, x: number, z: number, color: Color3)
	table.insert(pieces, piece(Vector3.new(3, 0.8, 6.5), Vector3.new(x, 1, z), color, FABRIC, BLOCK))
	table.insert(
		pieces,
		piece(Vector3.new(3, 0.6, 3), Vector3.new(x, 2, z - 3.6), color, FABRIC, BLOCK, Vector3.new(-30, 0, 0))
	)
end

-- A tiki torch (plain, no glow).
local function torch(pieces: { DecorTypes.Piece }, x: number, z: number)
	table.insert(pieces, pole(x, z, 7, 0.8, DARKWOOD, WOOD))
	table.insert(
		pieces,
		piece(Vector3.new(1.4, 1.4, 1.4), Vector3.new(x, 7.7, z), Color3.fromRGB(232, 120, 40), PLASTIC, BLOCK)
	)
end

local function sandFloor(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	local wet = Color3.fromRGB(214, 190, 128)
	table.insert(
		p,
		piece(Vector3.new(160, 0.3, 96), Vector3.new(-8, 0.15, 0), Color3.fromRGB(238, 214, 150), SAND, BLOCK)
	)
	table.insert(p, piece(Vector3.new(6, 0.4, 96), Vector3.new(67, 0.2, 0), Color3.fromRGB(200, 176, 118), SAND, BLOCK))
	table.insert(p, piece(Vector3.new(2.5, 0.5, 96), Vector3.new(71.25, 0.25, 0), WHITE, PLASTIC, BLOCK))
	table.insert(
		p,
		piece(
			Vector3.new(16, 0.5, 96),
			Vector3.new(80, 0.25, 0),
			Color3.fromRGB(46, 150, 214),
			Enum.Material.Glass,
			BLOCK
		)
	)
	table.insert(p, piece(Vector3.new(6, 0.3, 4), Vector3.new(-30, 0.35, 34), wet, SAND, BLOCK))
	table.insert(p, piece(Vector3.new(7, 0.3, 5), Vector3.new(24, 0.35, -14), wet, SAND, BLOCK))
	return p
end

local function barHut(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	table.insert(p, piece(Vector3.new(26, 0.8, 18), Vector3.new(-62, 0.4, 10), DECK, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(1, 9, 16), Vector3.new(-73.5, 5, 10), TEAL, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(24, 9, 1), Vector3.new(-62, 5, 2.5), TEAL, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(24, 9, 1), Vector3.new(-62, 5, 17.5), TEAL, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(1.6, 4, 14), Vector3.new(-51, 2.4, 10), DARKWOOD, WOOD, BLOCK))
	table.insert(
		p,
		piece(Vector3.new(2.6, 0.5, 15), Vector3.new(-51, 4.6, 10), Color3.fromRGB(235, 220, 190), PLASTIC, BLOCK)
	)
	table.insert(p, piece(Vector3.new(0.6, 0.6, 12), Vector3.new(-72, 6, 10), DARKWOOD, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(30, 1.2, 22), Vector3.new(-62, 10.4, 10), THATCH, FABRIC, BLOCK))
	table.insert(
		p,
		piece(Vector3.new(24, 1.2, 16), Vector3.new(-62, 11.6, 10), Color3.fromRGB(176, 140, 80), FABRIC, BLOCK)
	)
	for k = -1, 1 do
		table.insert(
			p,
			piece(
				Vector3.new(2.2, 0.5, 2.2),
				Vector3.new(-47.5, 3.2, 10 + k * 4.5),
				RED,
				PLASTIC,
				CYL,
				Vector3.new(0, 0, 90)
			)
		)
		table.insert(
			p,
			piece(
				Vector3.new(3.2, 0.8, 0.8),
				Vector3.new(-47.5, 1.6, 10 + k * 4.5),
				WHITE,
				PLASTIC,
				CYL,
				Vector3.new(0, 0, 90)
			)
		)
	end
	return p
end

local function kiosk(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	table.insert(p, piece(Vector3.new(14, 0.6, 10), Vector3.new(30, 0.3, 40), DECK, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(14, 7, 0.8), Vector3.new(30, 4, 44.6), YELLOW, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(0.8, 7, 9), Vector3.new(23.4, 4, 40), YELLOW, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(0.8, 7, 9), Vector3.new(36.6, 4, 40), YELLOW, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(14, 1.4, 1.6), Vector3.new(30, 2.1, 35.4), RED, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(16, 0.8, 12), Vector3.new(30, 9.4, 40), RED, FABRIC, BLOCK))
	table.insert(p, piece(Vector3.new(16, 0.8, 3), Vector3.new(30, 9, 34.2), WHITE, FABRIC, BLOCK))
	table.insert(p, piece(Vector3.new(3, 2.4, 3), Vector3.new(26, 1.8, 37), TEAL, PLASTIC, BLOCK))
	return p
end

local function palms(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	palm(p, -42, -8, 18, 10)
	palm(p, -56, -15, 21, 40)
	palm(p, -34, -23, 17, 70)
	return p
end

local function parasols(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	parasol(p, 54, 26, RED)
	parasol(p, 62, 16, YELLOW)
	lounger(p, 47, 22, TEAL)
	lounger(p, 53, 20, WHITE)
	lounger(p, 59, 22, RED)
	return p
end

local function surfboards(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	table.insert(p, piece(Vector3.new(11, 0.8, 0.8), Vector3.new(64, 3.4, -26), DARKWOOD, WOOD, BLOCK))
	local colors = { RED, YELLOW, TEAL, WHITE }
	for k = 0, 3 do
		table.insert(
			p,
			piece(
				Vector3.new(2, 11, 0.6),
				Vector3.new(60 + k * 2.8, 5.5, -26.6),
				colors[k + 1],
				PLASTIC,
				BLOCK,
				Vector3.new(0, 0, (k - 1.5) * 4)
			)
		)
	end
	table.insert(p, piece(Vector3.new(1.2, 3.5, 1.2), Vector3.new(58.5, 1.8, -26), DARKWOOD, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(1.2, 3.5, 1.2), Vector3.new(69.5, 1.8, -26), DARKWOOD, WOOD, BLOCK))
	return p
end

local function volleyball(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	table.insert(p, piece(Vector3.new(1, 10, 1), Vector3.new(-22, 5, -36), DARKWOOD, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(1, 10, 1), Vector3.new(-2, 5, -36), DARKWOOD, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(20, 3, 0.3), Vector3.new(-12, 7.6, -36), WHITE, FABRIC, BLOCK))
	table.insert(p, piece(Vector3.new(20, 0.5, 0.5), Vector3.new(-12, 9.3, -36), RED, FABRIC, BLOCK))
	table.insert(p, piece(Vector3.new(26, 0.1, 0.4), Vector3.new(-12, 0.35, -30), WHITE, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(26, 0.1, 0.4), Vector3.new(-12, 0.35, -42), WHITE, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(0.4, 0.1, 12), Vector3.new(-25, 0.35, -36), WHITE, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(0.4, 0.1, 12), Vector3.new(1, 0.35, -36), WHITE, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(2.2, 2.2, 2.2), Vector3.new(-7, 1.1, -32), YELLOW, PLASTIC, BALL))
	return p
end

local function boat(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	local hull = Color3.fromRGB(150, 98, 56)
	table.insert(p, piece(Vector3.new(8, 2.4, 18), Vector3.new(79, 1.2, 32), hull, WOOD, BLOCK))
	table.insert(p, piece(Vector3.new(8.6, 0.8, 18.6), Vector3.new(79, 2.5, 32), RED, PLASTIC, BLOCK))
	table.insert(
		p,
		piece(Vector3.new(5.7, 2.4, 5.7), Vector3.new(79, 1.2, 42.4), hull, WOOD, BLOCK, Vector3.new(0, 45, 0))
	)
	table.insert(p, piece(Vector3.new(6.5, 0.4, 1.4), Vector3.new(79, 3.2, 30), DARKWOOD, WOOD, BLOCK))
	table.insert(p, pole(79, 33, 17, 0.8, DARKWOOD, WOOD))
	table.insert(p, piece(Vector3.new(0.4, 10, 7), Vector3.new(79.3, 12, 35.5), WHITE, FABRIC, BLOCK))
	table.insert(p, piece(Vector3.new(0.5, 2, 2), Vector3.new(79.3, 7.5, 31.8), RED, FABRIC, BLOCK))
	return p
end

local function tikiCooler(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	torch(p, -70, -26)
	torch(p, -58, -26)
	torch(p, -70, -40)
	torch(p, -58, -40)
	table.insert(p, piece(Vector3.new(6, 3.6, 3.6), Vector3.new(-64, 1.8, -33), TEAL, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(6.4, 0.6, 4), Vector3.new(-64, 3.9, -33), WHITE, PLASTIC, BLOCK))
	table.insert(p, piece(Vector3.new(1.4, 0.5, 2.6), Vector3.new(-64, 4.4, -33), RED, PLASTIC, BLOCK))
	return p
end

local function lifeguard(): { DecorTypes.Piece }
	local p: { DecorTypes.Piece } = {}
	for _, dx in { -4, 4 } do
		for _, dz in { -4, 4 } do
			table.insert(p, piece(Vector3.new(1.2, 8, 1.2), Vector3.new(60 + dx, 4, -40 + dz), WHITE, WOOD, BLOCK))
		end
	end
	table.insert(p, piece(Vector3.new(11, 0.8, 11), Vector3.new(60, 8.4, -40), DECK, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(11, 5, 0.6), Vector3.new(60, 11.2, -45), RED, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(0.6, 5, 11), Vector3.new(55, 11.2, -40), RED, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(0.6, 5, 11), Vector3.new(65, 11.2, -40), RED, PLANK, BLOCK))
	table.insert(p, piece(Vector3.new(14, 0.8, 14), Vector3.new(60, 14.4, -40), WHITE, PLASTIC, BLOCK))
	table.insert(
		p,
		piece(Vector3.new(2.4, 8.6, 0.5), Vector3.new(60, 4.2, -34), DARKWOOD, WOOD, BLOCK, Vector3.new(-20, 0, 0))
	)
	table.insert(p, pole(66.5, -45, 11, 0.5, WHITE, PLASTIC))
	table.insert(p, piece(Vector3.new(5, 2.8, 0.3), Vector3.new(69, 18.5, -45), YELLOW, FABRIC, BLOCK))
	table.insert(
		p,
		piece(Vector3.new(2.6, 0.7, 2.6), Vector3.new(52, 1, -37), RED, PLASTIC, CYL, Vector3.new(0, 0, 90))
	)
	return p
end

local theme: DecorTypes.Theme = {
	Key = "BeachBar",
	Name = "Beach Bar",
	Area = Vector2.new(176, 96),
	Shiba = { Position = Vector2.new(56, -4), Facing = 180 },
	Path = {
		Vector2.new(0, 48),
		Vector2.new(-35, 28),
		Vector2.new(25, 6),
		Vector2.new(-20, -16),
		Vector2.new(35, -32),
		Vector2.new(0, -48),
	},
	BayPad = Vector2.new(56, 6),
	AutoPad = Vector2.new(49, -12),
	Parts = {
		{
			Id = "SandFloor",
			Name = "Beach Sand",
			Description = "Soft golden sand with a white surf line and a clear blue sea at the edge.",
			Pad = Vector2.new(14, 38),
			PriceSeconds = 10,
			Pieces = sandFloor(),
		},
		{
			Id = "BarHut",
			RewardMult = 2,
			Name = "Beach Bar Hut",
			Description = "A teal bar hut with a thatched roof, a counter and three red stools.",
			Pad = Vector2.new(-42, 10),
			PriceSeconds = 15,
			Pieces = barHut(),
		},
		{
			Id = "Kiosk",
			Name = "Beach Kiosk",
			Description = "A sunny yellow kiosk with a red awning that sells ice cream and drinks.",
			RewardMult = 1.2,
			Pad = Vector2.new(30, 32),
			PriceSeconds = 25,
			Pieces = kiosk(),
		},
		{
			Id = "PalmTrees",
			Name = "Palm Trees",
			Description = "Three tall palms with big green fronds and a coconut each.",
			Pad = Vector2.new(-46, -2),
			PriceSeconds = 35,
			Pieces = palms(),
		},
		{
			Id = "Parasols",
			RewardMult = 1.2,
			Name = "Parasols and Loungers",
			Description = "Red and yellow parasols over three sun loungers.",
			Pad = Vector2.new(44, 14),
			PriceSeconds = 50,
			Pieces = parasols(),
		},
		{
			Id = "Surfboards",
			Name = "Surfboard Rack",
			Description = "A wooden rack with four colourful surfboards.",
			Pad = Vector2.new(63, -19),
			PriceSeconds = 65,
			Pieces = surfboards(),
		},
		{
			Id = "Volleyball",
			RewardMult = 1.1,
			Name = "Volleyball Court",
			Description = "A sand court with a high net, white lines and a yellow ball.",
			Pad = Vector2.new(-12, -28),
			PriceSeconds = 80,
			Pieces = volleyball(),
		},
		{
			Id = "Boat",
			RewardMult = 1.3,
			Name = "Little Sailboat",
			Description = "A red and brown sailboat moored at the edge of the sea.",
			Pad = Vector2.new(67, 32),
			PriceSeconds = 100,
			Pieces = boat(),
		},
		{
			Id = "TikiCooler",
			Name = "Tiki Torches and Cooler",
			Description = "Four plain tiki torches around a big teal cooler box.",
			Pad = Vector2.new(-64, -22),
			PriceSeconds = 140,
			Pieces = tikiCooler(),
		},
		{
			Id = "Lifeguard",
			RewardMult = 1.5,
			Name = "Lifeguard Tower",
			Description = "A tall red and white lifeguard tower with a ladder, a flag and a rescue buoy.",
			Pad = Vector2.new(52, -30),
			PriceSeconds = 180,
			Pieces = lifeguard(),
		},
	},
}

return theme
