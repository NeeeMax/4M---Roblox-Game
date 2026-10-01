--!strict
-- Theme of the Shiba of bay 4: Food Truck Plaza (Config/DecorTypes -> Theme). 190 x 116, winding walkway, Shiba beside the fountain.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local WHITE = C(245, 245, 245)
local RED = C(205, 50, 45)
local YELLOW = C(255, 205, 60)
local TEAL = C(60, 170, 165)
local ORANGE = C(235, 135, 45)
local STEEL = C(170, 175, 185)
local DARK = C(45, 48, 55)
local WOOD = C(150, 105, 65)
local DARK_WOOD = C(95, 65, 40)
local GLASS = C(120, 170, 215)
local SLATE = C(35, 55, 45)
local GREEN = C(70, 150, 70)

-- Block standing on y0 (bottom).
local function box(
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

-- Standing cylinder (pole, drum, disc) on y0.
local function pole(
	x: number,
	y0: number,
	z: number,
	height: number,
	diameter: number,
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

local function ball(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	material: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
		Shape = Enum.PartType.Ball,
	}
end

local function wheel(x: number, z: number): Piece
	return {
		Size = Vector3.new(0.9, 2.4, 2.4),
		Offset = Vector3.new(x, 1.2, z),
		Color = DARK,
		Material = Enum.Material.Rubber,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

-- A food truck 16 long (x) and 7 deep (z): the serving window and awning face +z (the road side).
local function truck(cx: number, cz: number, body: Color3, stripe: Color3, awningA: Color3, awningB: Color3): Pieces
	local pieces: Pieces = {
		box(cx - 3, 1.2, cz, 10, 6, 7, body, Enum.Material.Metal),
		box(cx + 5, 1.2, cz, 6, 3.6, 7, body, Enum.Material.Metal),
		box(cx + 8, 2.6, cz, 0.2, 1.8, 5.4, GLASS, Enum.Material.Glass),
		box(cx - 3, 2.2, cz + 3.55, 10.2, 0.8, 0.15, stripe, Enum.Material.Metal),
		wheel(cx - 6, cz + 3.7),
		wheel(cx - 6, cz - 3.7),
		wheel(cx + 5, cz + 3.7),
		wheel(cx + 5, cz - 3.7),
		box(cx - 3, 3.4, cz + 3.55, 5, 2, 0.15, DARK, Enum.Material.Glass),
		box(cx - 3, 3.0, cz + 4.2, 5.6, 0.25, 1.3, STEEL, Enum.Material.Metal),
		box(cx - 3, 7.2, cz, 6, 1.4, 0.5, stripe, Enum.Material.SmoothPlastic),
		box(cx + 8.2, 1.0, cz, 0.7, 0.6, 7.4, STEEL, Enum.Material.Metal),
	}
	for i = 1, 4 do
		table.insert(
			pieces,
			box(
				cx - 5.4 + (i - 1) * 2.4,
				5.6,
				cz + 4.7,
				2.4,
				0.3,
				2.8,
				if i % 2 == 1 then awningA else awningB,
				Enum.Material.Fabric
			)
		)
	end
	return pieces
end

local function picnic(x: number, z: number): Pieces
	return {
		box(x, 2.6, z, 6, 0.3, 3.2, WOOD, Enum.Material.WoodPlanks),
		box(x - 2, 0, z, 0.5, 2.6, 3, DARK_WOOD, Enum.Material.Wood),
		box(x + 2, 0, z, 0.5, 2.6, 3, DARK_WOOD, Enum.Material.Wood),
		box(x, 0, z - 3, 6, 1.6, 1.2, WOOD, Enum.Material.WoodPlanks),
		box(x, 0, z + 3, 6, 1.6, 1.2, WOOD, Enum.Material.WoodPlanks),
	}
end

local function umbrellaSet(x: number, z: number, canopy: Color3): Pieces
	return {
		pole(x, 0, z, 2.5, 0.8, STEEL, Enum.Material.Metal),
		pole(x, 2.5, z, 0.3, 4, WHITE, Enum.Material.SmoothPlastic),
		pole(x, 2.8, z, 5, 0.3, STEEL, Enum.Material.Metal),
		box(x, 7.8, z, 9, 0.4, 9, canopy, Enum.Material.Fabric),
		box(x, 8.2, z, 5, 0.4, 5, WHITE, Enum.Material.Fabric),
		pole(x - 3, 0, z, 1.4, 1.4, canopy, Enum.Material.SmoothPlastic),
		pole(x + 3, 0, z, 1.4, 1.4, canopy, Enum.Material.SmoothPlastic),
	}
end

local function menuBoard(x: number, z: number): Pieces
	return {
		box(x, 1.2, z, 5, 3.6, 0.4, SLATE, Enum.Material.Slate),
		box(x, 4.8, z, 5.4, 0.3, 0.7, WOOD, Enum.Material.Wood),
		box(x - 2, 0, z, 0.4, 1.2, 0.4, WOOD, Enum.Material.Wood),
		box(x + 2, 0, z, 0.4, 1.2, 0.4, WOOD, Enum.Material.Wood),
		box(x, 3.8, z + 0.25, 3.6, 0.25, 0.1, WHITE, Enum.Material.SmoothPlastic),
		box(x, 3.0, z + 0.25, 3.0, 0.25, 0.1, YELLOW, Enum.Material.SmoothPlastic),
		box(x, 2.2, z + 0.25, 3.4, 0.25, 0.1, WHITE, Enum.Material.SmoothPlastic),
	}
end

local function planter(x: number, z: number): Pieces
	return {
		box(x, 0, z, 6, 1.6, 2.4, C(165, 90, 60), Enum.Material.Brick),
		box(x, 1.6, z, 5.6, 0.3, 2, C(70, 45, 30), Enum.Material.Grass),
		ball(x - 1.8, 2.6, z, 1.4, 1.4, 1.4, RED, Enum.Material.SmoothPlastic),
		ball(x, 2.8, z, 1.6, 1.6, 1.6, YELLOW, Enum.Material.SmoothPlastic),
		ball(x + 1.8, 2.6, z, 1.4, 1.4, 1.4, C(220, 110, 190), Enum.Material.SmoothPlastic),
	}
end

local function merge(...: Pieces): Pieces
	local out: Pieces = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

-- Part 1: plaza paving, a 5 x 3 checker of tiles.
local paving: Pieces = {}
for column = 0, 4 do
	for row = 0, 2 do
		table.insert(
			paving,
			box(
				5 + column * 6 + 3,
				0,
				36 + row * 6 + 3,
				6,
				0.2,
				6,
				if (column + row) % 2 == 0 then C(225, 215, 195) else C(190, 70, 60),
				Enum.Material.Concrete
			)
		)
	end
end

-- Part 6: string-light poles (plain bulbs).
local lights: Pieces = {
	pole(-46, 0, 14, 8, 0.6, DARK_WOOD, Enum.Material.Wood),
	pole(-46, 0, -8, 8, 0.6, DARK_WOOD, Enum.Material.Wood),
	box(-46, 7.6, 3, 0.2, 0.2, 22, DARK, Enum.Material.Metal),
}
for i = 0, 5 do
	table.insert(lights, ball(-46, 7.1, 11.5 - i * 3.9, 0.9, 0.9, 0.9, C(255, 225, 150), Enum.Material.SmoothPlastic))
end

-- Part 7: fountain.
local fountain: Pieces = {
	pole(62, 0, -34, 1.4, 16, C(190, 190, 195), Enum.Material.Concrete),
	pole(62, 1.4, -34, 0.3, 14, C(110, 175, 220), Enum.Material.Glass),
	pole(62, 1.4, -34, 3, 3, C(190, 190, 195), Enum.Material.Concrete),
	pole(62, 4.4, -34, 0.8, 7, C(190, 190, 195), Enum.Material.Concrete),
	pole(62, 5.2, -34, 0.2, 6, C(110, 175, 220), Enum.Material.Glass),
	pole(62, 5.2, -34, 2.2, 1.2, C(190, 190, 195), Enum.Material.Concrete),
	ball(62, 7.8, -34, 1.8, 1.8, 1.8, C(110, 175, 220), Enum.Material.Glass),
}

-- Part 14: stage corner.
local stage: Pieces = {
	box(-70, 0, -48, 22, 1.2, 14, DARK_WOOD, Enum.Material.WoodPlanks),
	box(-70, 1.2, -54.6, 22, 8, 0.5, RED, Enum.Material.SmoothPlastic),
	box(-70, 6.2, -54.2, 14, 1.8, 0.3, YELLOW, Enum.Material.SmoothPlastic),
	pole(-80, 1.2, -52, 7, 0.6, STEEL, Enum.Material.Metal),
	pole(-60, 1.2, -52, 7, 0.6, STEEL, Enum.Material.Metal),
	box(-70, 8.2, -52, 21, 0.4, 0.6, STEEL, Enum.Material.Metal),
	box(-78, 1.2, -44, 2, 3.5, 2, DARK, Enum.Material.SmoothPlastic),
	box(-62, 1.2, -44, 2, 3.5, 2, DARK, Enum.Material.SmoothPlastic),
	pole(-70, 1.2, -49, 1.2, 3, TEAL, Enum.Material.SmoothPlastic),
	pole(-67, 1.2, -49, 2, 0.3, STEEL, Enum.Material.Metal),
	box(-73, 1.2, -50, 3, 1.5, 1.4, DARK, Enum.Material.SmoothPlastic),
}

-- Part 15: giant burger on a plinth.
local bx, bz = 78, -49
local burger: Pieces = {
	pole(bx, 0, bz, 0.8, 14, STEEL, Enum.Material.Metal),
	pole(bx, 0.8, bz, 2, 12, C(215, 150, 70), Enum.Material.SmoothPlastic),
	pole(bx, 2.8, bz, 1.4, 12.4, C(95, 55, 35), Enum.Material.SmoothPlastic),
	box(bx, 4.2, bz, 12.8, 0.4, 12.8, YELLOW, Enum.Material.SmoothPlastic),
	pole(bx, 4.6, bz, 0.8, 13, GREEN, Enum.Material.Fabric),
	pole(bx, 5.4, bz, 0.8, 11.5, RED, Enum.Material.SmoothPlastic),
	ball(bx, 8.6, bz, 12, 6.4, 12, C(220, 155, 75), Enum.Material.SmoothPlastic),
	ball(bx - 2.5, 11.5, bz - 1, 0.9, 0.5, 0.5, C(255, 240, 200), Enum.Material.SmoothPlastic),
	ball(bx + 1, 11.8, bz + 2, 0.9, 0.5, 0.5, C(255, 240, 200), Enum.Material.SmoothPlastic),
	ball(bx + 2.5, 11.2, bz - 2, 0.9, 0.5, 0.5, C(255, 240, 200), Enum.Material.SmoothPlastic),
	ball(bx - 1, 11.9, bz + 1.5, 0.9, 0.5, 0.5, C(255, 240, 200), Enum.Material.SmoothPlastic),
	ball(bx, 12.2, bz - 0.5, 0.9, 0.5, 0.5, C(255, 240, 200), Enum.Material.SmoothPlastic),
}

local theme: DecorTypes.Theme = {
	Key = "FoodTruck",
	Name = "Food Truck Plaza",
	Area = Vector2.new(190, 116),
	Shiba = { Position = Vector2.new(60, -5), Facing = 180 },
	Path = {
		Vector2.new(0, 58),
		Vector2.new(-38, 34),
		Vector2.new(28, 8),
		Vector2.new(-30, -24),
		Vector2.new(0, -58),
	},
	BayPad = Vector2.new(60, 6),
	AutoPad = Vector2.new(50, 3),
	Parts = {
		{
			Id = "Paving",
			Name = "Plaza Paving",
			Description = "A checkerboard of cream and red tiles at the entrance of the plaza.",
			Pad = Vector2.new(20, 46),
			PriceSeconds = 10,
			Pieces = paving,
		},
		{
			Id = "TruckBurger",
			Name = "Burger Truck",
			Description = "A white food truck with a red-white awning and a serving window.",
			Pad = Vector2.new(-68, 31),
			PriceSeconds = 15,
			Pieces = truck(-65, 22, WHITE, RED, RED, WHITE),
		},
		{
			Id = "BonkSign",
			Name = "Get Bonked Sign",
			Description = "A huge red board with yellow letters on two sturdy posts.",
			Pad = Vector2.new(-48, 45),
			PriceSeconds = 22,
			Pieces = {
				box(-56, 0, 52, 0.8, 5, 0.8, DARK_WOOD, Enum.Material.Wood),
				box(-40, 0, 52, 0.8, 5, 0.8, DARK_WOOD, Enum.Material.Wood),
				box(-48, 5, 52, 20, 7, 0.8, RED, Enum.Material.SmoothPlastic),
				box(-48, 11.6, 52, 20.6, 0.5, 1.2, DARK_WOOD, Enum.Material.Wood),
				box(-48, 9.4, 52.5, 14, 1.4, 0.2, YELLOW, Enum.Material.SmoothPlastic),
				box(-48, 7.2, 52.5, 11, 1.4, 0.2, YELLOW, Enum.Material.SmoothPlastic),
				box(-48, 5.6, 52.5, 16, 0.5, 0.2, WHITE, Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "TruckTaco",
			Name = "Taco Truck",
			Description = "A teal taco truck with a yellow stripe and an orange awning.",
			Pad = Vector2.new(67, 29),
			PriceSeconds = 30,
			Pieces = truck(70, 20, TEAL, YELLOW, ORANGE, WHITE),
		},
		{
			Id = "Tables",
			Name = "Picnic Tables",
			Description = "Two wooden picnic tables with benches.",
			Pad = Vector2.new(-24, 12),
			PriceSeconds = 40,
			Pieces = merge(picnic(-18, 4), picnic(-30, 4)),
		},
		{
			Id = "Lights",
			Name = "String Light Poles",
			Description = "Two tall poles with a wire of round bulbs between them.",
			Pad = Vector2.new(-42, 3),
			PriceSeconds = 52,
			Pieces = lights,
		},
		{
			Id = "Fountain",
			Name = "Plaza Fountain",
			Description = "A two-tier stone fountain next to the Shiba.",
			Pad = Vector2.new(62, -23),
			PriceSeconds = 66,
			Pieces = fountain,
		},
		{
			Id = "Umbrellas",
			Name = "Umbrella Tables",
			Description = "Two round tables with big umbrellas and stools.",
			Pad = Vector2.new(29, -6),
			PriceSeconds = 82,
			Pieces = merge(umbrellaSet(24, -12, ORANGE), umbrellaSet(34, -16, TEAL)),
		},
		{
			Id = "TruckPizza",
			Name = "Pizza Truck",
			Description = "A red pizza truck with a white stripe, parked at the left edge.",
			Pad = Vector2.new(-73, -6),
			PriceSeconds = 100,
			Pieces = truck(-70, -15, RED, WHITE, GREEN, WHITE),
		},
		{
			Id = "Planters",
			Name = "Flower Planters",
			Description = "Three brick planters full of red, yellow and pink flowers.",
			Pad = Vector2.new(-49, -34),
			PriceSeconds = 120,
			Pieces = merge(planter(-56, -40), planter(-49, -40), planter(-42, -40)),
		},
		{
			Id = "Bins",
			Name = "Trash Cans",
			Description = "Two trash cans and a blue recycling bin.",
			Pad = Vector2.new(14, -25),
			PriceSeconds = 145,
			Pieces = {
				pole(10, 0, -30, 3, 2.4, STEEL, Enum.Material.Metal),
				pole(10, 3, -30, 0.4, 2.7, DARK, Enum.Material.Metal),
				pole(14, 0, -30, 3, 2.4, STEEL, Enum.Material.Metal),
				pole(14, 3, -30, 0.4, 2.7, DARK, Enum.Material.Metal),
				box(18, 0, -30, 2.6, 3.4, 2.6, C(50, 110, 200), Enum.Material.SmoothPlastic),
				box(18, 3.4, -30, 2.9, 0.4, 2.9, C(30, 70, 150), Enum.Material.SmoothPlastic),
			},
		},
		{
			Id = "Menus",
			Name = "Menu Boards",
			Description = "Two chalkboard menus with the daily specials.",
			Pad = Vector2.new(-30, -6),
			PriceSeconds = 170,
			Pieces = merge(menuBoard(-33, -12), menuBoard(-27, -12)),
		},
		{
			Id = "TruckDessert",
			Name = "Dessert Truck",
			Description = "A pink ice cream truck with a big orange awning.",
			Pad = Vector2.new(32, -36),
			PriceSeconds = 200,
			Pieces = truck(35, -45, C(250, 190, 205), C(200, 90, 130), ORANGE, WHITE),
		},
		{
			Id = "Stage",
			Name = "Stage Corner",
			Description = "A small stage with a red backdrop, speakers and a light truss.",
			Pad = Vector2.new(-70, -37),
			PriceSeconds = 240,
			Pieces = stage,
		},
		{
			Id = "GiantBurger",
			Name = "Giant Burger",
			Description = "A giant burger monument with sesame seeds, cheese and lettuce.",
			Pad = Vector2.new(78, -38),
			PriceSeconds = 280,
			Pieces = burger,
		},
	},
}

return theme
