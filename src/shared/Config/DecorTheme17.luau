--!strict
-- Theme of the Shiba of bay 17: Wizard Tower (Config/DecorTypes -> Theme). 190 x 130: Wizard Shiba stands in a runic circle in the
-- left middle, a crooked wizard tower rises in the back right, an observatory in the back left, a winding walkway links potion shop,
-- cauldron, library, portal and a floating sky island. Stage frame: +X right, -Z deeper, +Z toward the road.
-- No glow: crystals, runes and windows are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local MEADOW = C(98, 160, 100)
local MEADOW_D = C(78, 138, 92)
local FLAG = C(196, 190, 208)
local STONE = C(176, 170, 186)
local STONE_D = C(120, 114, 138)
local STONE_L = C(214, 210, 226)
local ROOF = C(96, 66, 160)
local ROOF_D = C(66, 46, 120)
local CYAN = C(96, 206, 232)
local PINK = C(226, 112, 190)
local PURPLE = C(150, 90, 214)
local GOLD = C(240, 192, 64)
local BRASS = C(196, 150, 64)
local WOOD = C(126, 86, 58)
local WOOD_D = C(84, 58, 42)
local WOOD_L = C(168, 124, 84)
local PARCH = C(234, 218, 178)
local RED = C(190, 56, 70)
local PLASTER = C(238, 226, 206)
local BREW = C(116, 214, 92)
local WATER = C(82, 170, 222)
local DOME = C(86, 164, 176)
local STRAW = C(222, 190, 100)
local CREAM = C(240, 228, 204)
local PUMPKIN = C(232, 132, 44)
local OWL = C(150, 116, 86)
local EGG = C(120, 200, 150)
local IRON = C(58, 58, 70)
local LEAF = C(84, 150, 84)
local WINDOW = C(250, 226, 130)

local Slate = Enum.Material.Slate
local Rock = Enum.Material.Rock
local Metal = Enum.Material.Metal
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Grass = Enum.Material.Grass
local Wood = Enum.Material.Wood
local Planks = Enum.Material.WoodPlanks

-- Block centred at (x, y, z), size (sx, sy, sz), optional rotation in degrees (x, y, z).
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

-- Cylinder tilted away from vertical by `tilt` degrees (positive leans toward -X).
local function CyT(
	x: number,
	y: number,
	z: number,
	d: number,
	h: number,
	tilt: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90 + tilt),
	}
end

-- Cylinder lying along Z (a target, a round window): diameter d, thickness len.
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

-- ---- the parts (every function builds one prop around its centre X, Z) -------------------------------------------------------

local function ground(): Pieces
	return {
		B(0, 0.15, 0, 190, 0.3, 130, MEADOW, Grass),
		B(-60, 0.35, -6, 38, 0.2, 34, FLAG, Slate),
		B(-20, 0.33, 14, 30, 0.2, 14, MEADOW_D, Grass),
		B(70, 0.33, 4, 34, 0.2, 18, MEADOW_D, Grass),
	}
end

-- A ring of runes round the Shiba: flat plates and six standing stones with crystals on the tallest.
local function circle(X: number, Z: number): Pieces
	local out: Pieces = {
		B(X, 0.2, Z, 34, 0.4, 34, STONE_D, Slate),
		B(X, 0.45, Z, 25, 0.2, 25, FLAG, Slate),
	}
	local stones = {
		{ 50, 8 },
		{ 92, 10 },
		{ 132, 8.5 },
		{ 228, 9 },
		{ 268, 10.5 },
		{ 312, 8 },
	}
	for i, s in stones do
		local a = math.rad(s[1])
		local sx, sz = X + 14 * math.cos(a), Z + 14 * math.sin(a)
		table.insert(out, B(sx, s[2] / 2, sz, 2.4, s[2], 1.8, STONE_L, Rock, rot(0, -s[1] + 90, 0)))
		if i == 2 or i == 5 or i == 4 then
			table.insert(out, B(sx, s[2] + 1.2, sz, 1.6, 2.4, 1.6, CYAN, Plastic, rot(0, 45, 0)))
		end
	end
	return out
end

local function tower(X: number, Z: number): Pieces
	return {
		B(X, 5, Z, 20, 10, 20, STONE_D, Rock),
		B(X, 17, Z, 15, 14, 15, STONE, Slate),
		B(X + 1, 30, Z, 12, 12, 12, STONE_L, Slate),
		B(X + 1, 36.4, Z, 16, 0.8, 16, STONE_D, Slate),
		Cy(X + 1, 40, Z, 13, 6, ROOF, Plastic),
		Cy(X + 1, 46, Z, 9, 6, ROOF_D, Plastic),
		Cy(X + 1, 51.5, Z, 5.5, 5, ROOF, Plastic),
		Cy(X + 1, 55, Z, 2.4, 2, GOLD, Metal),
		B(X, 3, Z + 9.8, 4.4, 6, 0.4, WOOD, Wood),
		B(X, 17, Z + 7.6, 2.4, 4, 0.3, WINDOW, Plastic),
		B(X + 1, 30, Z + 6.1, 2.6, 4, 0.3, WINDOW, Plastic),
	}
end

local function cauldron(X: number, Z: number): Pieces
	return {
		Ball(X, 5.2, Z, 12, 9, 12, IRON, Metal),
		Cy(X, 9.6, Z, 12.4, 0.9, STONE_D, Metal),
		Cy(X, 9.9, Z, 10.6, 0.3, BREW, Plastic),
		Ball(X - 1.6, 10.8, Z + 0.8, 3, 2.4, 3, BREW, Plastic),
		Ball(X + 2, 11.2, Z - 1.4, 2.4, 2.4, 2.4, BREW, Plastic),
		Ball(X + 0.4, 11.4, Z + 2.2, 2, 2, 2, BREW, Plastic),
		B(X - 4.4, 1.1, Z + 3.2, 1.6, 2.2, 1.6, IRON, Metal),
		B(X + 4.4, 1.1, Z + 3.2, 1.6, 2.2, 1.6, IRON, Metal),
		B(X, 1.1, Z - 5, 1.6, 2.2, 1.6, IRON, Metal),
		B(X, 0.9, Z, 11, 1.2, 1.6, WOOD_D, Wood, rot(0, 35, 0)),
		B(X, 0.9, Z, 11, 1.2, 1.6, WOOD, Wood, rot(0, -35, 0)),
		B(X - 6.4, 7.5, Z, 1.2, 1.6, 1.2, IRON, Metal),
		B(X + 6.4, 7.5, Z, 1.2, 1.6, 1.2, IRON, Metal),
	}
end

local function shop(X: number, Z: number): Pieces
	return {
		B(X, 0.5, Z, 20, 1, 14, STONE_D, Rock),
		B(X, 6.5, Z, 16, 11, 11, PLASTER, Plastic),
		B(X, 15, Z + 3.5, 19, 0.8, 9.2, ROOF, Plastic, rot(40.6, 0, 0)),
		B(X, 15, Z - 3.5, 19, 0.8, 9.2, ROOF_D, Plastic, rot(-40.6, 0, 0)),
		B(X, 18.2, Z, 19, 0.8, 0.8, ROOF_D, Plastic),
		B(X + 5.5, 15.5, Z - 2.5, 2.6, 7, 2.6, STONE, Rock),
		B(X - 2, 4.5, Z + 5.6, 3.4, 7, 0.4, WOOD, Wood),
		B(X + 4.2, 7, Z + 5.6, 3, 3, 0.4, WINDOW, Plastic),
		Cy(X + 7.4, 1.8, Z + 5.4, 2, 1.6, WOOD_L, Wood),
		B(X - 7.4, 1.6, Z + 5.2, 2.4, 1.6, 2.4, WOOD_L, Planks),
	}
end

local function well(X: number, Z: number): Pieces
	return {
		Cy(X, 1.4, Z, 8.4, 2.8, STONE, Rock),
		Cy(X, 2.65, Z, 5.6, 0.2, WATER, Plastic),
		B(X - 3.4, 5.6, Z, 0.9, 5.6, 0.9, WOOD_D, Wood),
		B(X + 3.4, 5.6, Z, 0.9, 5.6, 0.9, WOOD_D, Wood),
		B(X - 2.3, 9, Z, 5.2, 0.6, 8.6, ROOF, Plastic, rot(0, 0, 36)),
		B(X + 2.3, 9, Z, 5.2, 0.6, 8.6, ROOF_D, Plastic, rot(0, 0, -36)),
		B(X, 6.2, Z, 7, 0.4, 0.4, WOOD, Wood),
		Cy(X + 1.4, 4.4, Z + 1.0, 1.4, 1.4, WOOD_L, Wood),
	}
end

local function mushrooms(X: number, Z: number): Pieces
	return {
		Cy(X - 3, 3.2, Z, 3.6, 6.4, CREAM, Plastic),
		Ball(X - 3, 8, Z, 12, 8, 12, RED, Plastic),
		Cy(X + 5, 2.2, Z + 2.5, 2.4, 4.4, CREAM, Plastic),
		Ball(X + 5, 5.6, Z + 2.5, 8, 5, 8, PURPLE, Plastic),
		Cy(X + 0.5, 1.4, Z + 5, 1.6, 2.8, CREAM, Plastic),
		Ball(X + 0.5, 3.4, Z + 5, 5, 3.4, 5, PINK, Plastic),
		Cy(X - 7, 1.2, Z - 4.6, 1.4, 2.4, CREAM, Plastic),
		Ball(X - 7, 2.9, Z - 4.6, 4.4, 2.8, 4.4, CYAN, Plastic),
		B(X + 6.6, 0.9, Z - 4, 3.6, 1.8, 3, STONE_D, Rock, rot(0, 30, 0)),
	}
end

local function brooms(X: number, Z: number): Pieces
	return {
		B(X, 0.4, Z, 10, 0.8, 5, WOOD_D, Planks),
		B(X - 4.4, 4, Z, 0.8, 8, 0.8, WOOD, Wood),
		B(X + 4.4, 4, Z, 0.8, 8, 0.8, WOOD, Wood),
		B(X, 7.6, Z, 10, 0.6, 0.7, WOOD, Wood),
		B(X, 3, Z, 10, 0.5, 0.7, WOOD, Wood),
		B(X - 1.6, 4.4, Z + 1.0, 0.5, 8, 0.5, WOOD_L, Wood, rot(0, 0, 8)),
		B(X + 1.2, 4.4, Z + 1.0, 0.5, 8, 0.5, WOOD_L, Wood, rot(0, 0, -6)),
		B(X - 2.1, 1.8, Z + 1.0, 1.8, 3, 1.8, STRAW, Fabric, rot(0, 0, 8)),
		B(X + 1.6, 1.8, Z + 1.0, 1.8, 3, 1.8, STRAW, Fabric, rot(0, 0, -6)),
		Cy(X, 8.9, Z, 3.6, 2.2, ROOF, Plastic),
	}
end

local function garden(X: number, Z: number): Pieces
	return {
		B(X - 5.5, 0.9, Z + 2.5, 7, 1.8, 4.6, WOOD_D, Planks),
		B(X + 3.5, 0.9, Z + 3.2, 7, 1.8, 4.6, WOOD_D, Planks),
		B(X - 1, 0.9, Z - 3.8, 7, 1.8, 4.6, WOOD_D, Planks),
		Ball(X - 6, 2.9, Z + 2.5, 3.2, 2.2, 3.2, PUMPKIN, Plastic),
		Ball(X + 3, 3.2, Z + 3.2, 3.4, 2.6, 3.4, PURPLE, Plastic),
		Cy(X - 1, 3.4, Z - 3.8, 2.4, 3.2, PINK, Plastic),
		B(X + 7.6, 3.4, Z - 4.2, 0.7, 6.8, 0.7, WOOD, Wood),
		B(X + 7.6, 5.2, Z - 4.2, 5, 0.5, 0.5, WOOD, Wood),
		Ball(X + 7.6, 7, Z - 4.2, 1.8, 1.8, 1.8, STRAW, Fabric),
		Cy(X + 7.6, 7.6, Z - 4.2, 1.8, 1.2, ROOF, Plastic),
	}
end

local function crystals(X: number, Z: number): Pieces
	return {
		B(X, 1.2, Z, 12, 2.4, 11, STONE_D, Rock),
		B(X - 3, 3, Z - 2, 5, 3.6, 5, STONE, Rock, rot(0, 25, 0)),
		B(X, 9, Z, 3.6, 14, 3.6, CYAN, Plastic, rot(0, 30, 5)),
		B(X - 3.8, 6.5, Z + 1, 2.6, 9, 2.6, PURPLE, Plastic, rot(0, 15, -14)),
		B(X + 3.6, 6, Z - 1, 2.8, 9, 2.8, PINK, Plastic, rot(0, 50, 12)),
		B(X + 1.5, 4.8, Z + 3.4, 2, 6, 2, CYAN, Plastic, rot(10, 0, 0)),
		B(X - 2, 4.2, Z - 3.6, 2, 5.4, 2, PURPLE, Plastic, rot(-10, 0, 6)),
	}
end

local function library(X: number, Z: number): Pieces
	return {
		B(X, 0.5, Z, 26, 1, 16, STONE_D, Rock),
		B(X + 2, 7, Z, 18, 12, 11, STONE_L, Slate),
		B(X + 2, 16, Z + 3.1, 19, 0.8, 8.6, ROOF, Plastic, rot(44, 0, 0)),
		B(X + 2, 16, Z - 3.1, 19, 0.8, 8.6, ROOF_D, Plastic, rot(-44, 0, 0)),
		B(X - 9, 10.5, Z, 6.4, 19, 6.4, STONE, Slate),
		Cy(X - 9, 21.5, Z, 5.6, 3, ROOF, Plastic),
		Cy(X - 9, 24.5, Z, 3.4, 3, ROOF_D, Plastic),
		B(X + 2, 3.5, Z + 5.7, 4, 5.4, 0.4, WOOD, Wood),
		B(X + 2, 10.5, Z + 5.6, 4, 4, 0.4, WINDOW, Plastic),
		B(X - 3, 4.4, Z + 6.4, 1.4, 7, 1.6, STONE, Rock),
		B(X + 7, 4.4, Z + 6.4, 1.4, 7, 1.6, STONE, Rock),
		B(X + 11.4, 3, Z + 2.2, 2.4, 4, 2.4, WOOD_L, Planks),
	}
end

local function fountain(X: number, Z: number): Pieces
	return {
		Cy(X, 1.2, Z, 16, 2.4, STONE, Rock),
		Cy(X, 2.1, Z, 13.6, 0.2, WATER, Plastic),
		Cy(X, 4.4, Z, 2.6, 4.4, STONE_L, Slate),
		Cy(X, 6.9, Z, 8, 1, STONE, Rock),
		Cy(X, 8.9, Z, 2, 3, STONE_L, Slate),
		Ball(X, 11.3, Z, 3.6, 3.6, 3.6, GOLD, Metal),
		Cy(X, 12.3, Z, 0.8, 1.4, WATER, Plastic),
	}
end

local function owl(X: number, Z: number): Pieces
	return {
		Cy(X, 0.8, Z, 8, 1.6, WOOD_D, Wood),
		CyT(X, 10.5, Z, 3.4, 20, 4, WOOD_D, Wood),
		B(X + 3.6, 13.5, Z, 6.8, 0.9, 0.9, WOOD_D, Wood, rot(0, 0, 18)),
		B(X - 3.4, 17, Z, 6.4, 0.8, 0.8, WOOD_D, Wood, rot(0, 0, -22)),
		Ball(X + 4, 16, Z, 5.2, 5.2, 4.2, OWL, Plastic),
		Ball(X + 4, 19.6, Z, 3.8, 3.2, 3.8, OWL, Plastic),
		Cy(X + 4, 22.6, Z, 2.6, 2.8, ROOF, Plastic),
		Ball(X - 5.4, 19.4, Z, 2.4, 2.4, 2.4, OWL, Plastic),
	}
end

local function alchemy(X: number, Z: number): Pieces
	return {
		B(X, 3.2, Z, 16, 0.6, 6, WOOD, Planks),
		B(X - 7, 1.5, Z, 0.9, 3, 5, WOOD_D, Wood),
		B(X + 7, 1.5, Z, 0.9, 3, 5, WOOD_D, Wood),
		B(X, 6.4, Z - 3.6, 15, 0.5, 1.6, WOOD, Planks),
		B(X - 7, 4.5, Z - 3.6, 0.8, 9, 0.8, WOOD_D, Wood),
		B(X + 7, 4.5, Z - 3.6, 0.8, 9, 0.8, WOOD_D, Wood),
		Ball(X - 4, 5, Z + 0.6, 3.4, 3.4, 3.4, BREW, Plastic),
		Cy(X - 4, 7, Z + 0.6, 1, 2, STONE_L, Plastic),
		Ball(X + 1, 4.9, Z, 2.8, 2.8, 2.8, PURPLE, Plastic),
		Cy(X + 5, 5, Z - 0.4, 2.2, 3, CYAN, Plastic),
		B(X - 1.5, 6.9, Z, 6, 0.4, 0.4, BRASS, Metal),
		Cy(X - 4, 7.6, Z - 3.6, 1.4, 2, RED, Plastic),
	}
end

local function range(X: number, Z: number): Pieces
	return {
		B(X, 0.15, Z, 24, 0.3, 7, IRON, Slate),
		B(X - 8, 2.8, Z, 0.8, 5.6, 0.8, WOOD_D, Wood),
		Cz(X - 8, 5.6, Z + 0.6, 5, 0.6, CREAM, Wood),
		B(X + 8, 2.8, Z, 0.8, 5.6, 0.8, WOOD_D, Wood),
		Cz(X + 8, 5.6, Z + 0.6, 5, 0.6, CREAM, Wood),
		B(X, 3.5, Z, 0.9, 7, 0.9, WOOD, Wood),
		B(X, 5, Z, 5, 0.6, 0.6, WOOD, Wood),
		Ball(X, 5, Z, 3, 3.6, 2.2, STRAW, Fabric),
		Ball(X, 7.4, Z, 2.2, 2.2, 2.2, STRAW, Fabric),
		Cy(X, 9.1, Z, 2.4, 1.6, ROOF, Plastic),
		B(X, 0.5, Z + 3.0, 22, 0.4, 0.8, RED, Wood),
	}
end

local function egg(X: number, Z: number): Pieces
	return {
		Cy(X, 0.9, Z, 14, 1.8, WOOD_D, Wood),
		B(X, 1.7, Z, 13, 0.8, 1.2, WOOD, Wood, rot(0, 30, 0)),
		B(X, 1.7, Z, 13, 0.8, 1.2, WOOD_L, Wood, rot(0, -30, 0)),
		Ball(X, 6.3, Z, 8.4, 10, 8.4, EGG, Plastic),
		Ball(X, 12.2, Z, 3, 2.6, 3, PURPLE, Plastic),
		Ball(X - 5, 3, Z + 3.4, 3.6, 4, 3.6, PINK, Plastic),
		Ball(X + 4.8, 2.8, Z - 3.2, 3.2, 3.6, 3.2, CYAN, Plastic),
		Cy(X + 5, 2.2, Z + 4, 2.2, 0.5, GOLD, Metal),
	}
end

local function bridge(X: number, Z: number): Pieces
	return {
		B(X, 0.3, Z, 24, 0.4, 12, WATER, Plastic),
		B(X - 10, 1.2, Z, 4, 2.4, 5.6, STONE, Rock),
		B(X + 10, 1.2, Z, 4, 2.4, 5.6, STONE, Rock),
		B(X - 6, 3.4, Z, 8.4, 0.8, 4.6, STONE_L, Slate, rot(0, 0, 24)),
		B(X + 6, 3.4, Z, 8.4, 0.8, 4.6, STONE_L, Slate, rot(0, 0, -24)),
		B(X, 5.2, Z, 6, 0.8, 4.6, STONE_L, Slate),
		Cy(X - 9.4, 4.4, Z + 3, 0.8, 4.4, STONE_D, Slate),
		Cy(X + 9.4, 4.4, Z + 3, 0.8, 4.4, STONE_D, Slate),
		B(X - 9.4, 7.2, Z + 3, 1.4, 1.4, 1.4, GOLD, Plastic),
		B(X + 9.4, 7.2, Z + 3, 1.4, 1.4, 1.4, GOLD, Plastic),
		B(X, 6.4, Z + 2.2, 7, 0.4, 0.4, STONE_D, Slate),
		B(X, 6.4, Z - 2.2, 7, 0.4, 0.4, STONE_D, Slate),
	}
end

local function spellbook(X: number, Z: number): Pieces
	return {
		Cy(X, 0.5, Z, 6.8, 1, STONE_D, Rock),
		Cy(X, 3.4, Z, 2.2, 5.8, WOOD_D, Wood),
		B(X, 6.8, Z, 9, 0.8, 6, WOOD, Wood, rot(22, 0, 0)),
		B(X, 7.6, Z, 11, 0.5, 7.2, RED, Fabric, rot(22, 0, 0)),
		B(X - 2.7, 8.2, Z, 5, 0.4, 6.4, PARCH, Fabric, rot(22, 0, 8)),
		B(X + 2.7, 8.2, Z, 5, 0.4, 6.4, PARCH, Fabric, rot(22, 0, -8)),
		B(X + 4, 11, Z - 1, 0.5, 2.4, 0.5, PARCH, Fabric, rot(0, 0, -20)),
		Ball(X - 3.6, 11.4, Z - 1, 1.6, 1.6, 1.6, GOLD, Metal),
	}
end

local function pavilion(X: number, Z: number): Pieces
	return {
		Cy(X, 0.5, Z, 12, 1, STONE, Rock),
		Cy(X - 4.2, 3.8, Z - 4.2, 1.2, 5.6, STONE_L, Slate),
		Cy(X + 4.2, 3.8, Z - 4.2, 1.2, 5.6, STONE_L, Slate),
		Cy(X - 4.2, 3.8, Z + 4.2, 1.2, 5.6, STONE_L, Slate),
		Cy(X + 4.2, 3.8, Z + 4.2, 1.2, 5.6, STONE_L, Slate),
		Cy(X, 6.9, Z, 12.4, 0.8, ROOF_D, Plastic),
		Cy(X, 8.4, Z, 9, 2.4, ROOF, Plastic),
		Cy(X, 10.4, Z, 5.4, 2, ROOF_D, Plastic),
		Cy(X, 12, Z, 1.6, 2, GOLD, Metal),
		Cy(X, 2, Z, 2.4, 2, STONE_D, Rock),
		Ball(X, 3.7, Z, 3.6, 3.6, 3.6, CYAN, Plastic),
	}
end

local function statue(X: number, Z: number): Pieces
	return {
		B(X, 2, Z, 10, 4, 10, STONE_D, Rock),
		B(X, 4.4, Z, 8, 0.8, 8, STONE, Slate),
		Cy(X, 9.4, Z, 6.4, 10, STONE_L, Rock),
		Ball(X, 14.8, Z, 6, 3.2, 4.4, STONE_L, Rock),
		Ball(X, 17.8, Z, 3.4, 3.6, 3.4, STONE_L, Rock),
		B(X, 15.8, Z + 1.4, 2, 3, 1.2, STONE, Rock),
		Cy(X, 20.2, Z, 5.2, 0.6, STONE_D, Rock),
		Cy(X, 22.5, Z, 3.4, 4, STONE_D, Rock),
		Cy(X + 0.6, 25, Z, 1.6, 2, STONE_D, Rock),
		B(X + 3.6, 12, Z + 1.2, 0.7, 15, 0.7, WOOD, Wood),
		Ball(X + 3.6, 20, Z + 1.2, 2.2, 2.2, 2.2, CYAN, Plastic),
		B(X + 3, 13.4, Z + 1.4, 2.4, 0.9, 0.9, STONE_L, Rock),
	}
end

local function observatory(X: number, Z: number): Pieces
	return {
		B(X, 0.6, Z, 20, 1.2, 20, STONE_D, Rock),
		Cy(X, 6.6, Z, 16, 10.8, STONE, Slate),
		Cy(X, 12.4, Z, 17.4, 1, STONE_D, Rock),
		Ball(X, 17, Z, 16.4, 13, 16.4, DOME, Metal),
		B(X, 3.6, Z + 7.8, 3.6, 5, 0.6, WOOD, Wood),
		CyT(X + 2.6, 23.6, Z + 1, 2.6, 9, -18, BRASS, Metal),
		Ball(X - 5.5, 7.5, Z + 4.5, 2.4, 2.4, 2.4, GOLD, Metal),
		B(X + 6.8, 1.8, Z + 7.8, 3.4, 1.2, 3.4, STONE, Slate),
	}
end

local function griffin(X: number, Z: number): Pieces
	return {
		B(X, 1.5, Z, 12, 3, 6, STONE_D, Rock),
		B(X, 5.4, Z, 8, 3.4, 3.4, STONE_L, Slate),
		Ball(X + 3.2, 6.6, Z, 4.4, 5, 3.6, STONE_L, Slate),
		Ball(X + 4.4, 9.8, Z, 3, 2.8, 2.6, STONE_L, Slate),
		B(X + 6, 9.4, Z, 1.6, 0.9, 1, GOLD, Metal),
		B(X - 1.6, 9.6, Z + 2.2, 5.6, 6.4, 0.6, STONE, Slate, rot(0, 0, -18)),
		B(X - 1.6, 9.6, Z - 2.2, 5.6, 6.4, 0.6, STONE, Slate, rot(0, 0, -18)),
		B(X + 3, 4.1, Z + 1, 1.2, 2.2, 1.2, STONE_L, Slate),
		B(X + 3, 4.1, Z - 1, 1.2, 2.2, 1.2, STONE_L, Slate),
		B(X - 4.4, 5.4, Z, 3, 0.8, 0.8, STONE_L, Slate, rot(0, 0, 25)),
		B(X + 1, 12.4, Z, 3.6, 3, 0.6, STONE, Slate, rot(0, 0, -30)),
	}
end

local function portal(X: number, Z: number): Pieces
	return {
		B(X, 0.5, Z, 16, 1, 6, STONE_D, Rock),
		B(X - 6, 8.5, Z, 3, 15, 3.6, STONE, Slate),
		B(X + 6, 8.5, Z, 3, 15, 3.6, STONE, Slate),
		B(X - 4.2, 16.4, Z, 4.6, 2.6, 3.6, STONE, Slate, rot(0, 0, 34)),
		B(X + 4.2, 16.4, Z, 4.6, 2.6, 3.6, STONE, Slate, rot(0, 0, -34)),
		B(X, 18.6, Z, 4.6, 2.8, 3.6, STONE_L, Slate),
		B(X, 21, Z, 1.6, 2, 1.6, PINK, Plastic, rot(0, 45, 0)),
		Cz(X, 9.6, Z, 9.4, 0.6, PURPLE, Plastic),
		B(X - 6, 15.8, Z + 2.1, 1.4, 1.4, 0.8, GOLD, Metal),
		B(X + 6, 15.8, Z + 2.1, 1.4, 1.4, 0.8, GOLD, Metal),
	}
end

-- A rock island floating high above the path: the pieces all start above 7 studs, so people walk under it.
local function skyIsle(X: number, Z: number): Pieces
	return {
		Cy(X, 10.5, Z, 6, 3, STONE_D, Rock),
		Cy(X, 13.2, Z, 12, 3.2, STONE, Rock),
		Cy(X, 16.4, Z, 18, 3.8, STONE_D, Rock),
		Cy(X, 19, Z, 22, 1.4, MEADOW, Grass),
		B(X - 3, 22.8, Z - 2, 6, 7.6, 6, STONE_L, Slate),
		Cy(X - 3, 28.4, Z - 2, 7, 3.6, ROOF, Plastic),
		Cy(X - 3, 31.6, Z - 2, 4, 3, ROOF_D, Plastic),
		Cy(X - 3, 34, Z - 2, 1.6, 2, GOLD, Metal),
		Cy(X + 5.5, 21, Z + 4, 1, 3.8, WOOD, Wood),
		Ball(X + 5.5, 24.6, Z + 4, 6, 5, 6, LEAF, Grass),
	}
end

local function orrery(X: number, Z: number): Pieces
	return {
		Cy(X, 0.7, Z, 20, 1.4, STONE_D, Rock),
		Cy(X, 1.9, Z, 13, 1, STONE, Slate),
		Cy(X, 6, Z, 3, 8, BRASS, Metal),
		Ball(X, 12.4, Z, 6, 6, 6, GOLD, Metal),
		Cy(X, 12.4, Z, 17, 0.3, BRASS, Metal),
		Ball(X + 7, 12.4, Z + 2, 3.4, 3.4, 3.4, CYAN, Plastic),
		Ball(X - 5, 12.4, Z + 5, 2.6, 2.6, 2.6, RED, Plastic),
		Ball(X - 3, 12.4, Z - 7.4, 4, 4, 4, PINK, Plastic),
		B(X, 19, Z, 0.8, 12, 0.8, BRASS, Metal),
		Ball(X, 25, Z, 2, 2, 2, GOLD, Metal),
	}
end

-- ---- the theme ---------------------------------------------------------------------------------------------------------------

local theme: DecorTypes.Theme = {
	Key = "WizardTower",
	Name = "Wizard Tower",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-60, -6), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(-40, 46),
		Vector2.new(14, 26),
		Vector2.new(-38, 0),
		Vector2.new(34, -18),
		Vector2.new(-14, -44),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-71, -6),
	AutoPad = Vector2.new(-49, -6),
	Parts = {
		{
			Id = "Ground",
			Name = "Moonlit Meadow",
			Description = "A soft green meadow of enchanted grass with a flagstone plaza for the Wizard Shiba.",
			Pad = Vector2.new(-8, 58),
			PriceSeconds = 30,
			Pieces = ground(),
		},
		{
			Id = "Circle",
			Name = "Arcane Circle",
			Description = "A great rune circle with six standing stones and crystals. The Wizard Shiba's magic source.",
			Pad = Vector2.new(-60, -26),
			PriceSeconds = 35,
			RewardMult = 1.3,
			Pieces = circle(-60, -6),
		},
		{
			Id = "Tower",
			Yaw = 7,
			Name = "Crooked Wizard Tower",
			Description = "A tall stone tower with a wobbly top and a pointy purple hat of a roof. Wizards live here.",
			Pad = Vector2.new(31, -36),
			PriceSeconds = 40,
			RewardMult = 1.3,
			Pieces = tower(46, -46),
		},
		{
			Id = "Cauldron",
			Yaw = 20,
			Name = "Bubbling Cauldron",
			Description = "A giant iron cauldron full of green brew, bubbling over a crackling fire.",
			Pad = Vector2.new(-24, -14),
			PriceSeconds = 47,
			Pieces = cauldron(-24, -26),
		},
		{
			Id = "Shop",
			Yaw = -9,
			Name = "Potion Shop",
			Description = "A crooked little cottage that sells bottles of every colour, with a barrel at the door.",
			Pad = Vector2.new(-50, 36),
			PriceSeconds = 54,
			Pieces = shop(-60, 44),
		},
		{
			Id = "Well",
			Yaw = 14,
			Name = "Wishing Well",
			Description = "A mossy stone well with a tiny roof. Throw in a coin and make a wish!",
			Pad = Vector2.new(-46, 13),
			PriceSeconds = 63,
			Pieces = well(-46, 22),
		},
		{
			Id = "Mushrooms",
			Yaw = -16,
			Name = "Fairy Mushrooms",
			Description = "Giant spotted mushrooms in a fairy ring. The biggest one has a little round door.",
			Pad = Vector2.new(-72, 21),
			PriceSeconds = 73,
			Pieces = mushrooms(-82, 24),
		},
		{
			Id = "Brooms",
			Yaw = 24,
			Name = "Broom Rack",
			Description = "A rack of flying brooms and a pointy hat, ready for a quick ride.",
			Pad = Vector2.new(-18, 28),
			PriceSeconds = 85,
			Pieces = brooms(-26, 22),
		},
		{
			Id = "Garden",
			Yaw = 11,
			Name = "Potion Garden",
			Description = "Raised beds of magic pumpkins, purple cabbages and star flowers, guarded by a scarecrow wizard.",
			Pad = Vector2.new(-84, 40),
			PriceSeconds = 98,
			Pieces = garden(-84, 50),
		},
		{
			Id = "Crystals",
			Yaw = -22,
			Name = "Crystal Cluster",
			Description = "A rocky heap of sparkling blue, purple and pink crystals that hum when you walk by.",
			Pad = Vector2.new(-74, -32),
			PriceSeconds = 114,
			Pieces = crystals(-84, -38),
		},
		{
			Id = "Library",
			Yaw = 9,
			Name = "Spell Library",
			Description = "A gothic library with a pointy tower, stained glass and a thousand spell books.",
			Pad = Vector2.new(60, 24),
			PriceSeconds = 132,
			Pieces = library(74, 14),
		},
		{
			Id = "Fountain",
			Name = "Starlight Fountain",
			Description = "A tiered stone fountain with a golden star on top and clear blue water.",
			Pad = Vector2.new(52, 42),
			PriceSeconds = 153,
			Pieces = fountain(52, 54),
		},
		{
			Id = "Owl",
			Yaw = 18,
			Name = "Owl Roost",
			Description = "A gnarled old tree with a wise owl that wears its own tiny wizard hat.",
			Pad = Vector2.new(18, -46),
			PriceSeconds = 177,
			Pieces = owl(18, -56),
		},
		{
			Id = "Alchemy",
			Yaw = -14,
			Name = "Alchemy Bench",
			Description = "A workbench with bubbling flasks, copper pipes and a shelf of strange bottles.",
			Pad = Vector2.new(78, -51),
			PriceSeconds = 206,
			Pieces = alchemy(78, -58),
		},
		{
			Id = "Range",
			Yaw = -12,
			Name = "Spell Range",
			Description = "Two round targets and a straw dummy in a pointy hat. Practice your zaps here!",
			Pad = Vector2.new(24, 44),
			PriceSeconds = 239,
			Pieces = range(24, 52),
		},
		{
			Id = "Egg",
			Yaw = -28,
			Name = "Dragon Egg Nest",
			Description = "A twig nest with a giant green egg that wobbles, and a few smaller eggs and gold coins.",
			Pad = Vector2.new(71, -4),
			PriceSeconds = 277,
			Pieces = egg(82, -10),
		},
		{
			Id = "Bridge",
			Yaw = 10,
			Name = "Moon Bridge",
			Description = "A humped stone bridge over a lily pond, with golden lanterns at both ends.",
			Pad = Vector2.new(82, 40),
			PriceSeconds = 321,
			Pieces = bridge(82, 54),
		},
		{
			Id = "Spellbook",
			Yaw = 28,
			Name = "Giant Spellbook",
			Description = "A huge open spell book on a stone lectern, with a quill that writes by itself.",
			Pad = Vector2.new(44, 24),
			PriceSeconds = 372,
			Pieces = spellbook(36, 32),
		},
		{
			Id = "Pavilion",
			Yaw = -10,
			Name = "Crystal Ball Pavilion",
			Description = "A round pavilion with a purple roof, where a big crystal ball shows the future.",
			Pad = Vector2.new(18, -8),
			PriceSeconds = 432,
			Pieces = pavilion(18, 4),
		},
		{
			Id = "Statue",
			Yaw = -8,
			Name = "Founder Statue",
			Description = "A tall stone statue of the first great wizard, with a long beard and a glowing staff.",
			Pad = Vector2.new(54, 33),
			PriceSeconds = 501,
			Pieces = statue(64, 38),
		},
		{
			Id = "Observatory",
			Yaw = 6,
			Name = "Star Observatory",
			Description = "A round tower with a copper dome that opens to the sky and a big brass telescope.",
			Pad = Vector2.new(-46, -33),
			PriceSeconds = 581,
			RewardMult = 1.3,
			Pieces = observatory(-50, -48),
		},
		{
			Id = "Griffin",
			Yaw = -20,
			Name = "Griffin Statue",
			Description = "A proud stone griffin with spread wings, guarding the road to the tower.",
			Pad = Vector2.new(36, -9),
			PriceSeconds = 674,
			Pieces = griffin(36, 2),
		},
		{
			Id = "Portal",
			Yaw = 18,
			Name = "Magic Portal",
			Description = "A stone archway with a swirling purple gate to somewhere far, far away.",
			Pad = Vector2.new(58, -2),
			PriceSeconds = 782,
			RewardMult = 1.4,
			Pieces = portal(58, -12),
		},
		{
			Id = "SkyIsle",
			Yaw = 15,
			Name = "Floating Sky Isle",
			Description = "A rock island that floats high above the path with a tiny castle and a tree on top.",
			Pad = Vector2.new(6, -30),
			PriceSeconds = 907,
			Pieces = skyIsle(10, -24),
		},
		{
			Id = "Orrery",
			Yaw = 10,
			Name = "Grand Orrery",
			Description = "The showpiece: a golden sun, spinning planets and brass rings on a stone plinth. Pure wizard power!",
			Pad = Vector2.new(66, -36),
			PriceSeconds = 1052,
			RewardMult = 2,
			Pieces = orrery(80, -34),
		},
	},
}

return theme
