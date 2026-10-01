--!strict
-- Theme of the Shiba of bay 5: DJ Stage (Config/DecorTypes → Theme). Wide winding walkway, props spread over the whole plot.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lights, lasers and screens are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local black = C(22, 22, 30)
local dark = C(45, 45, 60)
local metal = C(150, 155, 168)
local pink = C(255, 70, 165)
local cyan = C(50, 205, 255)
local purple = C(150, 80, 230)
local yellow = C(255, 215, 60)
local white = C(240, 240, 245)
local red = C(200, 40, 60)
local gold = C(255, 195, 40)
local wood = C(130, 90, 55)

local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Slate = Enum.Material.Slate
local Wood = Enum.Material.Wood

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

-- Cylinder lying along Z (a woofer, a wheel, a drum facing the road): diameter d, length len.
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

local function speakerStack(x: number, z: number): { Piece }
	return {
		B(x, 3, z, 6, 6, 6, black, Plastic),
		B(x, 8.5, z, 5.4, 5, 5.4, dark, Plastic),
		B(x, 12.2, z, 4.6, 2.4, 4.6, black, Plastic),
		Cz(x, 3, z + 3.1, 4, 0.4, metal, Metal),
		Cz(x, 8.5, z + 2.9, 3.4, 0.4, metal, Metal),
		Cz(x, 12.2, z + 2.5, 1.6, 0.4, pink, Plastic),
		B(x, 1.2, z + 3.1, 5.2, 0.3, 0.3, pink, Plastic),
	}
end

local function sofa(x: number, z: number, color: Color3): { Piece }
	return {
		B(x, 1, z, 10, 2, 3.6, color, Fabric),
		B(x, 3, z - 1.6, 10, 3.4, 0.9, color, Fabric),
		B(x - 5.2, 1.8, z, 1, 3.6, 3.6, dark, Fabric),
		B(x + 5.2, 1.8, z, 1, 3.6, 3.6, dark, Fabric),
	}
end

local function stairStep(x: number, z: number, h: number): Piece
	return B(x, h / 2, z, 8, h, 2, metal, Metal)
end

local function danceTiles(): { Piece }
	local tiles: { Piece } = {}
	local colors = { pink, cyan, purple, yellow }
	for i = 0, 3 do
		for j = 0, 2 do
			table.insert(
				tiles,
				B(18.5 + i * 11, 0.15, 34 + j * 10, 10.6, 0.3, 9.6, colors[(i + j) % 4 + 1] :: Color3, Plastic)
			)
		end
	end
	return tiles
end

local theme: DecorTypes.Theme = {
	Key = "DJStage",
	Name = "DJ Stage",
	Area = Vector2.new(190, 126),
	Shiba = { Position = Vector2.new(-62, -22), Facing = 0 },
	Path = {
		Vector2.new(0, 63),
		Vector2.new(-45, 38),
		Vector2.new(40, 8),
		Vector2.new(-35, -28),
		Vector2.new(0, -63),
	},
	BayPad = Vector2.new(-72, -28),
	AutoPad = Vector2.new(-56, -30),
	Parts = {
		{
			Id = "Floor",
			Name = "Dance Floor",
			Description = "A big floor of coloured tiles right at the entrance.",
			Pad = Vector2.new(35, 57),
			PriceSeconds = 10,
			Pieces = danceTiles(),
		},
		{
			Id = "BigStage",
			Name = "Main Stage",
			Description = "A raised black stage with a tall back wall and a screen frame.",
			Pad = Vector2.new(35, -21),
			PriceSeconds = 15,
			Pieces = {
				B(50, 1.25, -40, 50, 2.5, 30, black, Metal),
				B(50, 9.5, -54.5, 50, 14, 1, dark, Slate),
				B(50, 9.5, -53.8, 34, 8, 0.4, purple, Plastic),
				B(50, 9.5, -53.5, 30, 1.2, 0.3, cyan, Plastic),
				B(50, 6.5, -53.5, 30, 1.2, 0.3, pink, Plastic),
				Cy(27, 11.5, -50, 1.4, 18, metal, Metal),
				Cy(73, 11.5, -50, 1.4, 18, metal, Metal),
				B(50, 21, -50, 48, 1.2, 1.2, metal, Metal),
				B(26, 2.75, -26.4, 2, 0.5, 2, pink, Plastic),
				B(74, 2.75, -26.4, 2, 0.5, 2, cyan, Plastic),
			},
		},
		{
			Id = "BonkSign",
			Name = "Get Bonked Sign",
			Description = "A huge black board with the party name in bright colours.",
			Pad = Vector2.new(-60, 53),
			PriceSeconds = 25,
			Pieces = {
				B(-70, 5, 48, 1.4, 10, 1.4, metal, Metal),
				B(-50, 5, 48, 1.4, 10, 1.4, metal, Metal),
				B(-60, 12.5, 48, 26, 9, 0.8, black, Slate),
				B(-60, 17.4, 48, 26.4, 0.8, 1, pink, Plastic),
				B(-60, 7.6, 48, 26.4, 0.8, 1, cyan, Plastic),
				B(-67, 12.5, 48.6, 4, 5.5, 0.4, pink, Plastic),
				B(-63, 12.5, 48.6, 4, 5.5, 0.4, yellow, Plastic),
				B(-59, 12.5, 48.6, 4, 5.5, 0.4, cyan, Plastic),
				B(-55, 12.5, 48.6, 4, 5.5, 0.4, white, Plastic),
				B(-70, 0.3, 48, 3, 0.6, 3, black, Slate),
				B(-50, 0.3, 48, 3, 0.6, 3, black, Slate),
			},
		},
		{
			Id = "Speakers",
			Name = "Speaker Stacks",
			Description = "Two towers of speakers on both sides of the stage.",
			Pad = Vector2.new(83, -24),
			PriceSeconds = 35,
			Pieces = merge(speakerStack(18, -32), speakerStack(83, -32)),
		},
		{
			Id = "Booth",
			Name = "DJ Booth",
			Description = "A DJ desk with two turntables, a laptop and the DJ.",
			Pad = Vector2.new(-25, 14),
			PriceSeconds = 50,
			Pieces = {
				B(-25, 1.7, 8, 14, 3.4, 4.5, black, Metal),
				B(-25, 3.5, 8, 14.4, 0.2, 4.9, pink, Plastic),
				Cy(-29, 3.7, 8, 3.2, 0.3, metal, Metal),
				Cy(-21, 3.7, 8, 3.2, 0.3, metal, Metal),
				B(-25, 3.9, 8, 2.4, 0.6, 1.8, cyan, Plastic),
				B(-25, 5.4, 5, 2, 3.4, 1.4, purple, Fabric),
				Ball(-25, 7.6, 5, 1.6, C(230, 190, 150), Plastic),
				B(-25, 6, 1.5, 14, 8, 0.6, dark, Plastic),
				B(-25, 6, 1.9, 12, 6, 0.3, cyan, Plastic),
				B(-32.5, 2, 8, 2.5, 4, 2.5, black, Plastic),
				B(-17.5, 2, 8, 2.5, 4, 2.5, black, Plastic),
			},
		},
		{
			Id = "Bar",
			Name = "Party Bar",
			Description = "A long counter with a bottle shelf and three round stools.",
			Pad = Vector2.new(74, 23),
			PriceSeconds = 65,
			Pieces = {
				B(74, 2, 14, 18, 4, 3, wood, Wood),
				B(74, 4.15, 14, 18.6, 0.3, 3.6, black, Slate),
				B(74, 5, 9.6, 18, 10, 1, dark, Wood),
				B(74, 6, 10.4, 16, 0.4, 0.8, wood, Wood),
				B(74, 8.4, 10.4, 16, 0.4, 0.8, wood, Wood),
				B(69, 7.2, 10.4, 1, 1.6, 1, cyan, Plastic),
				B(72.5, 7.2, 10.4, 1, 1.6, 1, pink, Plastic),
				B(76, 7.2, 10.4, 1, 1.6, 1, yellow, Plastic),
				B(79, 7.2, 10.4, 1, 1.6, 1, red, Plastic),
				Cy(68, 1.3, 18.5, 2, 2.6, red, Plastic),
				Cy(74, 1.3, 18.5, 2, 2.6, red, Plastic),
				Cy(80, 1.3, 18.5, 2, 2.6, red, Plastic),
			},
		},
		{
			Id = "Lounge",
			Name = "Lounge Sofas",
			Description = "Two sofas around a coffee table on a soft rug.",
			Pad = Vector2.new(-74, 21),
			PriceSeconds = 85,
			Pieces = merge(sofa(-82, 8, red), sofa(-66, 8, purple), {
				B(-74, 0.1, 13, 20, 0.2, 7, dark, Fabric),
				B(-74, 1.6, 13, 5, 0.4, 3, black, Metal),
				B(-74, 0.7, 13, 3, 1.4, 1.6, metal, Metal),
				Cy(-88, 5, 12, 0.5, 10, metal, Metal),
				B(-88, 10.4, 12, 2.4, 1.4, 2.4, yellow, Plastic),
			}),
		},
		{
			Id = "LightTruss",
			Name = "Light Truss",
			Description = "A steel frame over the dance floor full of coloured lamps.",
			Pad = Vector2.new(35, 27),
			PriceSeconds = 105,
			Pieces = {
				Cy(11, 9, 31, 1.4, 18, metal, Metal),
				Cy(59, 9, 31, 1.4, 18, metal, Metal),
				B(11, 0.4, 31, 3, 0.8, 3, black, Metal),
				B(59, 0.4, 31, 3, 0.8, 3, black, Metal),
				B(35, 17.5, 31, 50, 1.2, 1.2, metal, Metal),
				B(17, 15.8, 31, 1.8, 1.8, 1.8, pink, Plastic),
				B(26, 15.8, 31, 1.8, 1.8, 1.8, cyan, Plastic),
				B(35, 15.8, 31, 1.8, 1.8, 1.8, yellow, Plastic),
				B(44, 15.8, 31, 1.8, 1.8, 1.8, purple, Plastic),
				B(53, 15.8, 31, 1.8, 1.8, 1.8, pink, Plastic),
			},
		},
		{
			Id = "MirrorBall",
			Name = "Mirror Ball",
			Description = "A big silver ball on a tall pole in the middle of the floor.",
			Pad = Vector2.new(30, 44),
			PriceSeconds = 130,
			Pieces = {
				B(35, 0.6, 44, 4, 1.2, 4, black, Metal),
				Cy(35, 6, 44, 1.2, 12, metal, Metal),
				Ball(35, 15.5, 44, 8, C(205, 210, 225), Metal),
				B(35, 15.5, 48.1, 1.4, 1.4, 0.3, white, Plastic),
				B(39.1, 15.5, 44, 0.3, 1.4, 1.4, cyan, Plastic),
				B(30.9, 15.5, 44, 0.3, 1.4, 1.4, pink, Plastic),
				B(35, 19.6, 44, 1.4, 0.3, 1.4, yellow, Plastic),
			},
		},
		{
			Id = "VipRope",
			Name = "VIP Rope Fence",
			Description = "Golden posts with red ropes around a red carpet.",
			Pad = Vector2.new(-76, 35),
			PriceSeconds = 155,
			Pieces = {
				Cy(-88, 1.5, 30, 0.8, 3, gold, Metal),
				Cy(-82, 1.5, 30, 0.8, 3, gold, Metal),
				Cy(-76, 1.5, 30, 0.8, 3, gold, Metal),
				Cy(-70, 1.5, 30, 0.8, 3, gold, Metal),
				Cy(-64, 1.5, 30, 0.8, 3, gold, Metal),
				B(-85, 2.4, 30, 5.2, 0.3, 0.3, red, Fabric),
				B(-79, 2.4, 30, 5.2, 0.3, 0.3, red, Fabric),
				B(-67, 2.4, 30, 5.2, 0.3, 0.3, red, Fabric),
				B(-76, 0.1, 36, 24, 0.2, 10, red, Fabric),
			},
		},
		{
			Id = "FogMachine",
			Name = "Fog Machine",
			Description = "A fog machine puffing out big white clouds.",
			Pad = Vector2.new(76, -8),
			PriceSeconds = 185,
			Pieces = {
				B(84, 1.5, -8, 6, 3, 4, dark, Metal),
				B(84, 3.2, -8, 6.2, 0.4, 4.2, metal, Metal),
				Cz(84, 1.8, -5.5, 1.4, 1.4, black, Metal),
				Ball(84, 2.2, -3, 3.6, C(225, 225, 235), Plastic),
				Ball(86, 2.8, 0, 5, C(235, 235, 242), Plastic),
				Ball(82, 2.4, 1.5, 4, C(215, 215, 228), Plastic),
				Ball(88, 2, 4, 4.4, C(228, 228, 238), Plastic),
				Ball(84, 2.6, 5, 3.4, C(240, 240, 246), Plastic),
			},
		},
		{
			Id = "Stairs",
			Name = "Stage Stairs",
			Description = "Three wide steps with rails that lead up onto the stage.",
			Pad = Vector2.new(50, -14),
			PriceSeconds = 215,
			Pieces = {
				stairStep(50, -20, 0.8),
				stairStep(50, -22, 1.6),
				stairStep(50, -24, 2.4),
				B(45.6, 2.2, -22, 0.4, 0.4, 6, gold, Metal),
				B(54.4, 2.2, -22, 0.4, 0.4, 6, gold, Metal),
				Cy(45.6, 1.1, -19.2, 0.4, 2.2, gold, Metal),
				Cy(54.4, 1.1, -19.2, 0.4, 2.2, gold, Metal),
			},
		},
		{
			Id = "Drums",
			Name = "Drum Kit",
			Description = "A red drum kit on its own little riser with shiny cymbals.",
			Pad = Vector2.new(8, -36),
			PriceSeconds = 250,
			Pieces = {
				B(8, 0.2, -44, 14, 0.4, 10, dark, Slate),
				Cz(8, 2.4, -45, 4, 3, red, Plastic),
				Cy(4.2, 3.6, -43.2, 2.6, 0.9, white, Plastic),
				Cy(6, 5.2, -46.5, 2, 1.2, red, Plastic),
				Cy(10, 5.2, -46.5, 2, 1.2, red, Plastic),
				Cy(12, 2.6, -43, 2.6, 2.2, red, Plastic),
				Cy(2, 3.3, -46, 0.3, 6.6, metal, Metal),
				Cy(2, 6.8, -46, 3.4, 0.15, gold, Metal),
				Cy(13, 3.3, -47, 0.3, 6.6, metal, Metal),
				Cy(13, 6.8, -47, 3.4, 0.15, gold, Metal),
				Cy(8, 1.3, -40.6, 1.6, 1.8, black, Plastic),
			},
		},
		{
			Id = "FoodTruck",
			Name = "Snack Truck",
			Description = "A yellow snack truck with a serving window and a pink awning.",
			Pad = Vector2.new(78, 54),
			PriceSeconds = 285,
			Pieces = {
				B(80, 1.9, 45, 16, 3, 8, dark, Metal),
				B(79, 5.6, 45, 13, 4.4, 8, yellow, Plastic),
				B(87, 4, 45, 4, 4, 7.4, yellow, Plastic),
				B(88.1, 5, 45, 1.8, 1.6, 6, cyan, Plastic),
				B(78, 5.8, 49.05, 8, 2.2, 0.2, black, Plastic),
				B(78, 3.9, 49.8, 8.4, 0.4, 1.4, metal, Metal),
				B(78, 7.5, 50.4, 10, 0.3, 3, pink, Fabric),
				Cz(74, 1.4, 41.4, 3, 0.8, black, Plastic),
				Cz(74, 1.4, 48.6, 3, 0.8, black, Plastic),
				Cz(86, 1.4, 41.4, 3, 0.8, black, Plastic),
				Cz(86, 1.4, 48.6, 3, 0.8, black, Plastic),
			},
		},
		{
			Id = "GoldHammer",
			Name = "Golden Bonk Monument",
			Description = "A giant golden bonk hammer on a tall pedestal with colourful corner lamps.",
			Pad = Vector2.new(-70, -39),
			PriceSeconds = 320,
			Pieces = {
				B(-70, 1, -50, 15, 2, 15, black, Slate),
				B(-70, 3, -50, 11, 2, 11, metal, Metal),
				B(-70, 11.5, -50, 1.8, 15, 1.8, wood, Wood),
				B(-70, 19.5, -50, 10, 5, 5, gold, Metal),
				B(-70, 19.5, -47.4, 6, 3, 0.3, yellow, Metal),
				Ball(-76, 3.2, -44, 2.4, pink, Plastic),
				Ball(-64, 3.2, -44, 2.4, cyan, Plastic),
				Ball(-76, 3.2, -56, 2.4, purple, Plastic),
				Ball(-64, 3.2, -56, 2.4, yellow, Plastic),
			},
		},
	},
}

return theme
