--!strict
-- Theme of the Shiba of bay 16: Gold Vault (Config/DecorTypes -> Theme). 190 x 130: a steel bank vault chamber and a round vault door
-- in the back left, the Gold Shiba standing in front of a golden halo arch in the left middle, a winding walkway past gold
-- stacks, laser gates, an armoured truck, a gold coin fountain and a golden piggy bank. Stage frame: +X right, -Z deeper, +Z toward the
-- road. No glow: lasers, lamps and gems are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local GOLD = C(240, 190, 52)
local DGOLD = C(190, 140, 36)
local STEEL = C(150, 158, 172)
local DSTEEL = C(72, 78, 90)
local CHAR = C(42, 46, 56)
local RED = C(200, 48, 52)
local VELVET = C(150, 30, 44)
local MARBLE = C(226, 222, 214)
local DMARBLE = C(70, 66, 74)
local GREEN = C(70, 150, 90)
local GLASS = C(150, 200, 230)
local AMBER = C(226, 170, 40)
local PINK = C(240, 150, 170)
local WATER = C(80, 170, 230)
local WOOD = C(120, 80, 50)
local ORANGE = C(236, 140, 30)
local CREAM = C(250, 236, 190)
local WHITE = C(240, 244, 250)

local Metal = Enum.Material.Metal
local Plate = Enum.Material.DiamondPlate
local Marble = Enum.Material.Marble
local Plastic = Enum.Material.SmoothPlastic
local Fabric = Enum.Material.Fabric
local Glass = Enum.Material.Glass
local Wood = Enum.Material.Wood

-- Block standing on y0 (bottom), centred at (x, z), optional rotation in degrees.
local function B(
	x: number,
	y0: number,
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
		Offset = Vector3.new(x, y0 + sy / 2, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
		Rotation = rot,
	}
end

-- Standing cylinder on y0: diameter d, height h.
local function Cs(x: number, y0: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y0 + h / 2, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Cylinder lying along X (a beam, a halo disc facing +X): centre y, diameter d, length len.
local function Cx(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
	}
end

-- Cylinder lying along Z (a coin or a wheel facing the road).
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

local function merge(...: Pieces): Pieces
	local out: Pieces = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

-- A gold stack of 2 or 3 tiers at (x, z).
local function stackOf(x: number, z: number, w: number, d: number, tiers: number): Pieces
	local out: Pieces = {}
	for i = 1, tiers do
		local k = 1 - (i - 1) * 0.3
		table.insert(out, B(x, (i - 1) * 2.4, z, w * k, 2.4, d, if i % 2 == 1 then GOLD else DGOLD, Metal))
	end
	return out
end

-- One security camera on a pole at (x, z), its head turned by `turn` degrees.
local function camera(x: number, z: number, turn: number): Pieces
	return {
		Cs(x, 0, z, 2.4, 0.8, DSTEEL, Metal),
		Cs(x, 0.8, z, 0.8, 9, STEEL, Metal),
		B(x, 9.2, z, 3.6, 1.6, 1.8, CHAR, Metal, rot(0, turn, 0)),
	}
end

-- One gold floor lamp at (x, z).
local function lamp(x: number, z: number): Pieces
	return {
		Cs(x, 0, z, 2.6, 0.8, DGOLD, Metal),
		Cs(x, 0.8, z, 0.7, 8, GOLD, Metal),
		Cs(x, 8.4, z, 3.4, 2.2, CREAM, Plastic),
		Ball(x, 10.9, z, 1.6, 1.6, 1.6, AMBER, Plastic),
	}
end

-- One display case with a jewel.
local function vitrine(x: number, z: number, jewel: Color3): Pieces
	return {
		B(x, 0, z, 5, 2.8, 5, DSTEEL, Metal),
		B(x, 2.8, z, 4.6, 3.6, 4.6, GLASS, Glass),
		Ball(x, 4.6, z, 1.6, 1.6, 1.6, jewel, Plastic),
	}
end

-- A treasure chest with a gold heap at (x, z).
local function chest(x: number, z: number, w: number, d: number): Pieces
	return {
		B(x, 0, z, w, 2.6, d, WOOD, Wood),
		B(x, 2.6, z, w + 0.2, 1.2, d + 0.2, DGOLD, Metal),
		Ball(x, 3.0, z, w * 0.8, 1.2, d * 0.7, GOLD, Metal),
	}
end

local theme: DecorTypes.Theme = {
	Key = "GoldVault",
	Name = "Gold Vault",
	Area = Vector2.new(190, 130),
	Shiba = { Position = Vector2.new(-40, 6), Facing = 0 },
	Path = {
		Vector2.new(0, 65),
		Vector2.new(50, 48),
		Vector2.new(20, 26),
		Vector2.new(-14, 6),
		Vector2.new(30, -12),
		Vector2.new(44, -30),
		Vector2.new(12, -48),
		Vector2.new(0, -65),
	},
	BayPad = Vector2.new(-40, 18),
	AutoPad = Vector2.new(-40, -6),
	Parts = {
		{
			Id = "Floor",
			Name = "Vault Floor",
			Description = "Dark diamond-plate steel with gold edging, a gold coin medallion and a polished marble yard.",
			Pad = Vector2.new(-14, 58),
			PriceSeconds = 60,
			Pieces = {
				B(0, 0, 0, 190, 0.3, 130, DSTEEL, Plate),
				B(0, 0.3, -63.5, 190, 0.12, 3, GOLD, Metal),
				B(0, 0.3, 63.5, 190, 0.12, 3, GOLD, Metal),
				B(-93.5, 0.3, 0, 3, 0.12, 130, GOLD, Metal),
				B(93.5, 0.3, 0, 3, 0.12, 130, GOLD, Metal),
				B(-40, 0.3, 6, 24, 0.14, 24, GOLD, Metal),
				B(-40, 0.44, 6, 16, 0.1, 16, DGOLD, Metal),
				B(-68, 0.3, -28, 40, 0.14, 14, MARBLE, Marble),
				B(80, 0.3, 11, 28, 0.12, 22, AMBER, Metal),
			},
		},
		{
			Id = "Chamber",
			Yaw = 5,
			Name = "Vault Chamber",
			Description = "A thick steel strongroom with a roof of vents and a gold VAULT sign above the open doorway.",
			Pad = Vector2.new(-68, -31),
			PriceSeconds = 69,
			Pieces = {
				B(-68, 0, -60.5, 44, 12, 3, STEEL, Metal),
				B(-88.5, 0, -49, 3, 12, 26, STEEL, Metal),
				B(-47.5, 0, -49, 3, 12, 26, STEEL, Metal),
				B(-82, 0, -37.5, 16, 12, 3, STEEL, Metal),
				B(-54, 0, -37.5, 16, 12, 3, STEEL, Metal),
				B(-68, 9, -37.5, 12, 3, 3, DSTEEL, Metal),
				B(-68, 12, -49, 46, 1.2, 28, DSTEEL, Metal),
				B(-68, 13.2, -35.8, 46, 0.8, 0.8, GOLD, Metal),
				B(-68, 13.2, -37, 14, 4, 1, CHAR, Metal),
				Cs(-80, 13.2, -52, 6, 2.2, STEEL, Metal),
				Cs(-56, 13.2, -52, 6, 2.2, STEEL, Metal),
			},
		},
		{
			Id = "VaultDoor",
			Yaw = -8,
			Name = "Round Vault Door",
			Description = "A huge round steel door with a gold turning wheel, set in a heavy frame with hinges and bolts.",
			Pad = Vector2.new(-30, -34),
			PriceSeconds = 79,
			Pieces = {
				B(-30, 0, -43, 26, 1, 8, DSTEEL, Metal),
				B(-30, 1, -45, 24, 19, 3, STEEL, Metal),
				Cz(-30, 10.5, -43.2, 18.4, 1.6, DGOLD, Metal),
				Cz(-30, 10.5, -42.4, 16, 2.8, STEEL, Metal),
				Cz(-30, 10.5, -40.4, 6, 1.6, GOLD, Metal),
				B(-30, 9.9, -39.8, 13, 1.2, 1.2, GOLD, Metal),
				B(-30, 3.9, -39.8, 1.2, 13, 1.2, GOLD, Metal),
			},
		},
		{
			Id = "Arch",
			Yaw = 6,
			Name = "Golden Halo Arch",
			Description = "A marble and gold arch behind the Gold Shiba with a shining halo, so everyone knows who owns the vault.",
			Pad = Vector2.new(-52, -14),
			PriceSeconds = 91,
			RewardMult = 1.25,
			Pieces = {
				B(-54, 0, -6, 6, 1.2, 6, DMARBLE, Marble),
				B(-54, 0, 18, 6, 1.2, 6, DMARBLE, Marble),
				B(-54, 1.2, -6, 3.4, 14.8, 3.4, MARBLE, Marble),
				B(-54, 1.2, 18, 3.4, 14.8, 3.4, MARBLE, Marble),
				B(-54, 16, 6, 4, 3, 28, GOLD, Metal),
				B(-55.5, 1.2, 6, 2, 8, 20, DGOLD, Metal),
				Cx(-54.2, 23, 6, 10, 2, GOLD, Metal),
				Ball(-52.8, 23, 6, 3.4, 3.4, 3.4, RED, Plastic),
			},
		},
		{
			Id = "GoldStacks",
			Yaw = 22,
			Name = "Gold Bar Stacks",
			Description = "Three pyramids of shiny gold bars, stacked high and not a single one missing.",
			Pad = Vector2.new(-72, 36),
			PriceSeconds = 104,
			Pieces = merge(stackOf(-84, 18, 8, 5, 2), stackOf(-73, 17, 8, 5, 2), stackOf(-79, 29, 10, 6, 3), {
				B(-70, 0, 26, 3, 0.8, 1.6, GOLD, Metal, rot(0, 30, 0)),
				B(-88, 0, 27, 3, 0.8, 1.6, DGOLD, Metal, rot(0, -20, 0)),
			}),
		},
		{
			Id = "CoinHeap",
			Yaw = -14,
			Name = "Coin Mountain",
			Description = "A glittering mountain of gold coins with a few loose towers of coins around it.",
			Pad = Vector2.new(-66, -23),
			PriceSeconds = 120,
			Pieces = {
				Ball(-78, 4, -12, 22, 8, 16, GOLD, Metal),
				Ball(-70, 2.5, -8, 10, 5, 9, DGOLD, Metal),
				Ball(-87, 2, -14, 9, 4, 9, DGOLD, Metal),
				Cs(-71, 0, -18, 3.4, 2.4, GOLD, Metal),
				Cs(-88, 0, -6, 3.4, 1.8, GOLD, Metal),
			},
		},
		{
			Id = "Lasers",
			Yaw = 10,
			Name = "Laser Gates",
			Description = "Three security gates with red laser beams across the floor. Do not touch!",
			Pad = Vector2.new(62, 12),
			PriceSeconds = 138,
			Pieces = {
				B(80, 0, 11, 22, 0.4, 22, AMBER, Metal),
				B(71, 0, 3, 2, 9, 2, DSTEEL, Metal),
				B(89, 0, 3, 2, 9, 2, DSTEEL, Metal),
				B(71, 0, 11, 2, 9, 2, DSTEEL, Metal),
				B(89, 0, 11, 2, 9, 2, DSTEEL, Metal),
				B(71, 0, 19, 2, 9, 2, DSTEEL, Metal),
				B(89, 0, 19, 2, 9, 2, DSTEEL, Metal),
				Cx(80, 2, 3, 0.5, 16, RED, Plastic),
				Cx(80, 6, 3, 0.5, 16, RED, Plastic),
				Cx(80, 3.5, 11, 0.5, 16, RED, Plastic),
				Cx(80, 7, 11, 0.5, 16, RED, Plastic),
				Cx(80, 2.5, 19, 0.5, 16, RED, Plastic),
				Cx(80, 5.5, 19, 0.5, 16, RED, Plastic),
			},
		},
		{
			Id = "Truck",
			Yaw = -22,
			Name = "Armoured Truck",
			Description = "A heavy armoured truck with a gold stripe and a gold back door, parked to unload.",
			Pad = Vector2.new(54, 60),
			PriceSeconds = 159,
			Pieces = {
				B(71.5, 1.6, 50, 22, 1, 8, DSTEEL, Metal),
				B(66, 2.6, 50, 14, 7.4, 8.8, STEEL, Metal),
				B(66, 6.4, 50, 14.2, 1, 8.9, GOLD, Metal),
				B(59.2, 3, 50, 0.5, 6, 6, GOLD, Metal),
				B(77.5, 2.6, 50, 8, 5, 8.4, STEEL, Metal),
				Cz(62, 1.8, 50, 3.6, 9.6, CHAR, Metal),
				Cz(70, 1.8, 50, 3.6, 9.6, CHAR, Metal),
				Cz(78.5, 1.8, 50, 3.6, 9.6, CHAR, Metal),
			},
		},
		{
			Id = "Desk",
			Yaw = 14,
			Name = "Guard Desk",
			Description = "A guard desk with a glass screen, three monitors and a chair for the night watch.",
			Pad = Vector2.new(-16, 56),
			PriceSeconds = 182,
			Pieces = {
				B(-26, 0, 48, 14, 3.2, 4, DSTEEL, Metal),
				B(-26, 3.2, 48, 15, 0.5, 5, MARBLE, Marble),
				B(-26, 3.7, 50.2, 15, 4, 0.3, GLASS, Glass),
				B(-30, 3.7, 47, 2.6, 2, 0.4, CHAR, Plastic),
				B(-26, 3.7, 47, 2.6, 2, 0.4, CHAR, Plastic),
				B(-22, 3.7, 47, 2.6, 2, 0.4, CHAR, Plastic),
				B(-26, 0, 43.6, 3, 2.2, 3, VELVET, Fabric),
				B(-26, 2.2, 42.4, 3, 3.4, 0.6, VELVET, Fabric),
			},
		},
		{
			Id = "Statue",
			Yaw = -12,
			Name = "Gold Shiba Statue",
			Description = "A golden Shiba statue on a marble plinth with a ruby collar. Its tail wags in the sun.",
			Pad = Vector2.new(70, -54),
			PriceSeconds = 210,
			RewardMult = 1.3,
			Pieces = {
				B(82, 0, -52, 14, 3, 14, DMARBLE, Marble),
				B(82, 3, -52, 10, 2, 10, MARBLE, Marble),
				Ball(82, 10, -52, 7, 9, 6.4, GOLD, Metal),
				Ball(82, 16.4, -51, 6.4, 5.6, 5.8, GOLD, Metal),
				B(82, 15, -48.5, 2.6, 2, 2.4, DGOLD, Metal),
				B(80.4, 18.4, -51.6, 1.6, 2.4, 1.2, DGOLD, Metal),
				B(83.6, 18.4, -51.6, 1.6, 2.4, 1.2, DGOLD, Metal),
				Ball(86, 8, -55, 3, 6, 3, DGOLD, Metal),
				B(80.6, 5, -49.4, 1.8, 5, 1.8, GOLD, Metal),
				B(83.4, 5, -49.4, 1.8, 5, 1.8, GOLD, Metal),
				B(82, 13.4, -50.5, 7.2, 1, 6.4, RED, Plastic),
			},
		},
		{
			Id = "CrownCase",
			Name = "Crown Jewels Case",
			Description = "The royal crown on a velvet cushion inside a glass case, behind two gold rope posts.",
			Pad = Vector2.new(56, -48),
			PriceSeconds = 241,
			Pieces = {
				B(56, 0, -56, 7, 4, 7, DMARBLE, Marble),
				B(56, 4, -56, 6, 6, 6, GLASS, Glass),
				B(56, 4, -56, 3.8, 1.2, 3.8, VELVET, Fabric),
				Cs(56, 5.2, -56, 3.4, 1.6, GOLD, Metal),
				Ball(56, 7.4, -56, 1.6, 1.6, 1.6, RED, Plastic),
				B(56, 10, -56, 6.6, 0.5, 6.6, GOLD, Metal),
				Cs(51, 0, -52, 0.8, 3.2, GOLD, Metal),
				Cs(61, 0, -52, 0.8, 3.2, GOLD, Metal),
				B(56, 2.6, -52, 10, 0.3, 0.3, VELVET, Fabric),
			},
		},
		{
			Id = "Trolley",
			Yaw = 28,
			Name = "Money Trolley",
			Description = "A trolley piled with bundles of cash and a gold bar on top.",
			Pad = Vector2.new(-50, 58),
			PriceSeconds = 277,
			Pieces = {
				B(-58, 1.6, 52, 10, 0.6, 6, STEEL, Metal),
				Cz(-62, 0.8, 49, 1.6, 0.8, CHAR, Metal),
				Cz(-54, 0.8, 49, 1.6, 0.8, CHAR, Metal),
				Cz(-62, 0.8, 55, 1.6, 0.8, CHAR, Metal),
				Cz(-54, 0.8, 55, 1.6, 0.8, CHAR, Metal),
				B(-60, 2.2, 52, 3.6, 2.6, 4, GREEN, Fabric),
				B(-56.4, 2.2, 52, 3.2, 3.4, 4, GREEN, Fabric),
				B(-58, 4.8, 52, 4, 1, 1.8, GOLD, Metal),
				B(-62.8, 2.2, 49.6, 0.5, 5, 0.5, STEEL, Metal),
				B(-62.8, 2.2, 54.4, 0.5, 5, 0.5, STEEL, Metal),
				B(-62.8, 7.2, 52, 0.5, 0.5, 5, STEEL, Metal),
			},
		},
		{
			Id = "Diamond",
			Yaw = -18,
			Name = "Giant Diamond",
			Description = "A huge sparkling diamond on a marble pedestal.",
			Pad = Vector2.new(-10, -46),
			PriceSeconds = 319,
			Pieces = {
				B(-13, 0, -57, 9, 1.6, 9, DMARBLE, Marble),
				B(-13, 1.6, -57, 6, 2.4, 6, MARBLE, Marble),
				B(-13, 4, -57, 6.4, 8, 6.4, GLASS, Glass, rot(0, 45, 0)),
				Ball(-13, 12.6, -57, 3, 3, 3, WHITE, Glass),
			},
		},
		{
			Id = "Safe",
			Yaw = 16,
			Name = "Giant Safe",
			Description = "A giant combination safe with a gold dial and spoked wheel, big enough to hide a whole Shiba.",
			Pad = Vector2.new(-72, 56),
			PriceSeconds = 367,
			Pieces = {
				B(-88, 0, 50, 3, 1.5, 9, DSTEEL, Metal),
				B(-80, 0, 50, 3, 1.5, 9, DSTEEL, Metal),
				B(-84, 1.5, 50, 14, 14, 11, DSTEEL, Metal),
				B(-84, 2.7, 56, 12, 12.6, 0.8, STEEL, Metal),
				Cz(-84, 8, 57, 5, 1, GOLD, Metal),
				B(-84, 7.6, 57.4, 8, 0.8, 0.8, GOLD, Metal),
				B(-84, 4, 57.4, 0.8, 8, 0.8, GOLD, Metal),
				B(-90.5, 4, 56, 1, 2, 1, GOLD, Metal),
				B(-90.5, 10, 56, 1, 2, 1, GOLD, Metal),
			},
		},
		{
			Id = "Mint",
			Yaw = -12,
			Name = "Coin Mint Press",
			Description = "A big stamping press that mints gold coins and drops them onto a conveyor belt.",
			Pad = Vector2.new(75, -38),
			PriceSeconds = 422,
			RewardMult = 1.4,
			Pieces = {
				B(84, 0, -30, 16, 4, 10, DSTEEL, Metal),
				B(78.5, 4, -30, 3, 10, 4, STEEL, Metal),
				B(89.5, 4, -30, 3, 10, 4, STEEL, Metal),
				B(84, 12, -30, 14, 3.2, 5, STEEL, Metal),
				Cs(84, 8, -30, 3, 4, DGOLD, Metal),
				B(84, 4, -30, 6, 1, 5, GOLD, Metal),
				B(84, 15.2, -30, 5, 3, 5, DGOLD, Metal),
				B(84, 2, -23.5, 14, 1, 3, CHAR, Metal),
				Ball(90, 3.6, -23.5, 4, 2.6, 3, GOLD, Metal),
			},
		},
		{
			Id = "Cameras",
			Name = "Security Cameras",
			Description = "Three cameras on tall poles, watching the path and the gold at all times.",
			Pad = Vector2.new(56, 31),
			PriceSeconds = 485,
			Pieces = merge(camera(52, 22, 20), camera(62, 31, -30), camera(55, 40, 25)),
		},
		{
			Id = "Lamps",
			Name = "Gold Floor Lamps",
			Description = "Three tall gold lamps with cream shades that make the whole vault glow warm.",
			Pad = Vector2.new(-29, 34),
			PriceSeconds = 558,
			Pieces = merge(lamp(-36, 25), lamp(-29, 29), lamp(-22, 24)),
		},
		{
			Id = "Piggy",
			Yaw = 24,
			Name = "Golden Piggy Bank",
			Description = "A giant golden piggy bank with a coin on its way into the slot. Every hit makes it jingle.",
			Pad = Vector2.new(68, 34),
			PriceSeconds = 642,
			RewardMult = 1.5,
			Pieces = {
				Ball(82, 6.2, 32, 15, 11.6, 10.4, GOLD, Metal),
				Ball(88.4, 7, 32, 6.4, 6, 6, GOLD, Metal),
				Cx(90.4, 6.2, 32, 3.6, 1.4, PINK, Plastic),
				B(88, 9.2, 30.2, 1.6, 2, 1.2, PINK, Plastic),
				B(88, 9.2, 33.8, 1.6, 2, 1.2, PINK, Plastic),
				Cs(77.4, 0, 29.2, 2.4, 3.4, DGOLD, Metal),
				Cs(77.4, 0, 34.8, 2.4, 3.4, DGOLD, Metal),
				Cs(86.2, 0, 29.2, 2.4, 3.4, DGOLD, Metal),
				Cs(86.2, 0, 34.8, 2.4, 3.4, DGOLD, Metal),
				B(74.2, 7.6, 32, 1.6, 1.6, 1.6, DGOLD, Metal),
				B(82, 11.8, 32, 5, 0.4, 1, CHAR, Metal),
				Cz(82.4, 12.6, 32, 4, 0.8, GOLD, Metal),
			},
		},
		{
			Id = "Chests",
			Yaw = -18,
			Name = "Treasure Chests",
			Description = "Three wooden treasure chests with gold bands, overflowing with coins, inside the strongroom.",
			Pad = Vector2.new(-68, -44),
			PriceSeconds = 738,
			Pieces = merge(chest(-72, -52, 5, 3.4), chest(-60, -54, 5, 3.4), chest(-66, -58, 7, 4.4), {
				Ball(-66, 1, -49.6, 6, 2, 3, GOLD, Metal),
			}),
		},
		{
			Id = "Scale",
			Yaw = 10,
			Name = "Giant Gold Scale",
			Description = "A giant golden balance scale. The gold side is much heavier than the feather side.",
			Pad = Vector2.new(-46, 42),
			PriceSeconds = 849,
			Pieces = {
				B(-46, 0, 34, 9, 1.2, 5, DGOLD, Metal),
				Cs(-46, 1.2, 34, 1.6, 12, GOLD, Metal),
				Ball(-46, 13.6, 34, 2.4, 2.4, 2.4, GOLD, Metal),
				B(-46, 13.4, 34, 18, 0.8, 1, GOLD, Metal, rot(0, 0, 6)),
				Cs(-54, 5.2, 34, 6.4, 0.6, DGOLD, Metal),
				Cs(-38, 8.4, 34, 6.4, 0.6, DGOLD, Metal),
				B(-54, 5.8, 34, 0.3, 7.4, 0.3, DGOLD, Metal),
				B(-38, 9, 34, 0.3, 4.4, 0.3, DGOLD, Metal),
				Ball(-54, 7.2, 34, 4.4, 3, 3.4, GOLD, Metal),
				B(-38, 9, 34, 1.6, 1.6, 1.6, WHITE, Plastic),
			},
		},
		{
			Id = "Forklift",
			Yaw = -26,
			Name = "Gold Forklift",
			Description = "A little orange forklift carrying a pallet piled high with gold bars.",
			Pad = Vector2.new(40, 12),
			PriceSeconds = 976,
			Pieces = {
				B(53, 1, 6, 8, 3, 5, ORANGE, Plastic),
				B(50.2, 4, 4.2, 0.5, 4, 0.5, CHAR, Metal),
				B(50.2, 4, 7.8, 0.5, 4, 0.5, CHAR, Metal),
				B(52, 8, 6, 6, 0.5, 5, CHAR, Metal),
				B(47.8, 0, 6, 0.8, 9, 4, STEEL, Metal),
				B(44.5, 0.8, 4.6, 5, 0.4, 0.7, STEEL, Metal),
				B(44.5, 0.8, 7.4, 5, 0.4, 0.7, STEEL, Metal),
				B(44.6, 1.2, 6, 6, 0.6, 5, WOOD, Wood),
				B(44.6, 1.8, 6, 5.4, 2.4, 4.6, GOLD, Metal),
				B(44.6, 4.2, 6, 3.6, 1.6, 4.6, DGOLD, Metal),
				Cz(55, 1.2, 3.2, 2.4, 0.8, CHAR, Metal),
				Cz(55, 1.2, 8.8, 2.4, 0.8, CHAR, Metal),
				Cz(50.4, 1.2, 3.2, 2.4, 0.8, CHAR, Metal),
				Cz(50.4, 1.2, 8.8, 2.4, 0.8, CHAR, Metal),
			},
		},
		{
			Id = "Fountain",
			Name = "Gold Coin Fountain",
			Description = "A marble fountain with gold bowls and a big coin on top, spraying sparkling water.",
			Pad = Vector2.new(-4, -24),
			PriceSeconds = 1122,
			Pieces = {
				Cs(2, 0, -32, 15, 1.6, MARBLE, Marble),
				Cs(2, 1.0, -32, 12.6, 0.8, WATER, Plastic),
				Cs(2, 1.6, -32, 3, 4, GOLD, Metal),
				Cs(2, 5, -32, 8, 0.9, GOLD, Metal),
				Cs(2, 5.9, -32, 1.8, 3, GOLD, Metal),
				Cz(2, 11.2, -32, 4.6, 0.8, GOLD, Metal),
			},
		},
		{
			Id = "Vitrines",
			Yaw = 15,
			Name = "Jewel Display Cases",
			Description = "Three glass display cases on a red carpet, each with a big jewel inside.",
			Pad = Vector2.new(0, 50),
			PriceSeconds = 1291,
			Pieces = merge({
				B(-4, 0, 40, 20, 0.2, 8, VELVET, Fabric),
			}, vitrine(-12, 42, RED), vitrine(-4, 36, GREEN), vitrine(4, 43, GLASS)),
		},
		{
			Id = "Throne",
			Yaw = -8,
			Name = "Golden Throne",
			Description = "A tall golden throne on a marble dais with a red carpet leading up to it.",
			Pad = Vector2.new(66, -9),
			PriceSeconds = 1484,
			Pieces = {
				B(66, 0, -24, 14, 1.6, 12, DMARBLE, Marble),
				B(66, 1.6, -26, 9, 1.6, 7, MARBLE, Marble),
				B(66, 3.2, -27, 4, 2.2, 3.8, VELVET, Fabric),
				B(66, 3.2, -29.2, 5, 10, 1.4, GOLD, Metal),
				Ball(66, 14.2, -29.2, 4.4, 2.6, 1.4, DGOLD, Metal),
				B(63.6, 3.2, -27, 0.9, 2, 3.6, GOLD, Metal),
				B(68.4, 3.2, -27, 0.9, 2, 3.6, GOLD, Metal),
				Ball(63.4, 13.6, -29.2, 1.4, 1.4, 1.4, GOLD, Metal),
				Ball(68.6, 13.6, -29.2, 1.4, 1.4, 1.4, GOLD, Metal),
				B(66, 0, -17, 4, 0.15, 6, VELVET, Fabric),
			},
		},
		{
			Id = "MegaCoin",
			Yaw = 6,
			Name = "Mega Gold Coin",
			Description = "The showpiece: a giant gold coin with a dollar sign, standing in a steel cradle with a ruby on top.",
			Pad = Vector2.new(34, -48),
			PriceSeconds = 1707,
			RewardMult = 1.75,
			Pieces = {
				B(34, 0, -56, 16, 1.6, 6, DSTEEL, Metal),
				B(27, 1.6, -56, 2, 6, 3, DGOLD, Metal),
				B(41, 1.6, -56, 2, 6, 3, DGOLD, Metal),
				Cz(34, 11.8, -56, 16, 2.4, GOLD, Metal),
				Cz(34, 11.8, -56, 17.2, 1.6, DGOLD, Metal),
				Ball(34, 21, -56, 2.6, 2.6, 2.6, RED, Plastic),
			},
		},
	},
}

return theme
