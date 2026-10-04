--!strict
-- Theme of the Shiba of bay 26: Hell Gate (Config/DecorTypes -> Theme). 180 x 140: the tall Demon Shiba stands on a red-veined plaza
-- in front of its Demon Throne (back middle, inside a lava moat and a pair of giant bat wings); the walkway winds from the spiked
-- entrance past horned gate pillars, bone heaps, cages and a cauldron to the horned Gate Arch at the back, the obsidian spire in the
-- far left corner and the swirling Hellfire Portal on the right. Parts are loose clusters, turned toward the path.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No glow: lava and flames are plain coloured blocks.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local OBS = C(34, 30, 40)
local BLK = C(22, 20, 26)
local ROCK = C(62, 54, 60)
local RROCK = C(112, 40, 40)
local DRED = C(74, 22, 28)
local RED = C(178, 38, 38)
local LAVA = C(255, 104, 28)
local LAVAY = C(255, 178, 54)
local BONE = C(232, 222, 196)
local IRON = C(88, 90, 102)
local ASH = C(116, 112, 118)
local SULF = C(214, 196, 72)
local GREEN = C(112, 186, 72)
local WOOD = C(74, 52, 40)
local PURP = C(100, 40, 88)

local Basalt = Enum.Material.Basalt
local Slate = Enum.Material.Slate
local Metal = Enum.Material.Metal
local Concrete = Enum.Material.Concrete
local Plastic = Enum.Material.SmoothPlastic
local Wood = Enum.Material.Wood
local Granite = Enum.Material.Granite
local Rocky = Enum.Material.Rock

-- Shift of the piece constructors below (set by `at`).
local shiftX, shiftZ = 0, 0

-- Block centred at (x, y, z), size (sx, sy, sz); optional rotation in degrees.
local function B(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material,
	rx: number?,
	ry: number?,
	rz: number?
): Piece
	local piece: Piece = {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x + shiftX, y, z + shiftZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
	}
	if rx or ry or rz then
		piece.Rotation = Vector3.new(rx or 0, ry or 0, rz or 0)
	end
	return piece
end

-- Standing cylinder (axis up): diameter d, height h, centre y.
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x + shiftX, y, z + shiftZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Disc facing the road (axis along Z): diameter d, thickness len.
local function Cz(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x + shiftX, y, z + shiftZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

-- Cylinder lying along X.
local function Cx(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x + shiftX, y, z + shiftZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
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
		Offset = Vector3.new(x + shiftX, y, z + shiftZ),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
end

local function join(...: Pieces): Pieces
	local out: Pieces = {}
	for _, list in { ... } do
		for _, p in list do
			table.insert(out, p)
		end
	end
	return out
end

-- Builds the pieces of `build` moved by (dx, dz) in the plane (every constructor adds the current shift).
local function at(dx: number, dz: number, build: () -> Pieces): Pieces
	shiftX, shiftZ = dx, dz
	local list = build()
	shiftX, shiftZ = 0, 0
	return list
end

-- 2. a fire brazier on a black column
local function brazier(x: number, z: number): Pieces
	return {
		B(x, 0.7, z, 3.6, 1.4, 3.6, ROCK, Basalt),
		Cy(x, 4.4, z, 2.4, 6, BLK, Basalt),
		Cy(x, 8, z, 4.8, 1.2, IRON, Metal),
		Ball(x, 10.2, z, 3.4, 4.2, 3.4, RED, Plastic),
		Ball(x, 10.8, z, 2, 3.2, 2, LAVA, Plastic),
	}
end

-- 11. an imp on a pedestal
local function imp(x: number, z: number): Pieces
	return {
		B(x, 1, z, 5, 2, 5, ROCK, Basalt),
		B(x, 4.4, z, 2.4, 3.6, 2, PURP, Slate),
		Ball(x, 7.2, z, 2.2, 2.2, 2.2, PURP, Slate),
		B(x - 0.8, 8.8, z, 0.5, 1.6, 0.5, BONE, Plastic, 0, 0, 14),
		B(x + 0.8, 8.8, z, 0.5, 1.6, 0.5, BONE, Plastic, 0, 0, -14),
		B(x - 2.2, 5.6, z - 0.8, 0.4, 3.4, 2, DRED, Slate, 0, 0, 20),
		B(x + 2.2, 5.6, z - 0.8, 0.4, 3.4, 2, DRED, Slate, 0, 0, -20),
	}
end

-- 12. a horned gate pillar
local function pillar(x: number, z: number): Pieces
	return {
		B(x, 1, z, 6.4, 2, 6.4, ROCK, Basalt),
		B(x, 11, z, 4.4, 18, 4.4, OBS, Basalt),
		B(x, 20.6, z, 6.2, 1.8, 6.2, RROCK, Basalt),
		B(x - 2, 23.4, z, 1.2, 4.6, 1.2, BONE, Plastic, 0, 0, 22),
		B(x + 2, 23.4, z, 1.2, 4.6, 1.2, BONE, Plastic, 0, 0, -22),
		Ball(x, 14, z + 2.4, 2.6, 2.8, 1.6, BONE, Plastic),
	}
end

local ground: Pieces = {
	B(0, 0.15, 0, 180, 0.3, 140, OBS, Basalt),
	B(-58, 0.33, 34, 46, 0.1, 30, RROCK, Slate),
	B(60, 0.33, 30, 40, 0.1, 36, DRED, Slate),
	B(-20, 0.33, -30, 44, 0.1, 34, DRED, Slate),
	B(26, 0.33, -52, 52, 0.1, 30, RROCK, Slate),
	B(20, 0.38, -14, 26, 0.16, 26, ROCK, Granite),
	B(20, 0.46, -14, 20, 0.14, 20, DRED, Slate),
	B(20, 0.53, -14, 12, 0.1, 12, RED, Slate),
	B(-40, 0.34, -50, 40, 0.1, 3, LAVA, Plastic),
	B(54, 0.34, 40, 3, 0.1, 34, LAVA, Plastic),
	B(-72, 0.34, 4, 3, 0.1, 30, LAVA, Plastic),
	B(36, 0.34, 8, 26, 0.1, 3, LAVA, Plastic),
}

local theme: DecorTypes.Theme = {
	Key = "HellGate",
	Name = "Hell Gate",
	Area = Vector2.new(180, 140),
	Shiba = { Position = Vector2.new(20, -14), Facing = 270 },
	Path = {
		Vector2.new(0, 70),
		Vector2.new(-30, 54),
		Vector2.new(22, 38),
		Vector2.new(54, 16),
		Vector2.new(18, 0),
		Vector2.new(-36, -10),
		Vector2.new(-52, -40),
		Vector2.new(0, -70),
	},
	BayPad = Vector2.new(4, -9),
	AutoPad = Vector2.new(4, -19),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Obsidian Ground",
			Description = "Black glassy rock veined with red, glowing lava cracks and a red-ringed plaza under the Demon Shiba.",
			Pad = Vector2.new(-5, 67),
			PriceSeconds = 100,
			Pieces = ground,
		},
		-- 2
		{
			Id = "Braziers",
			Name = "Entrance Braziers",
			Description = "Two black columns with iron bowls and roaring red fire greet everybody at the gate.",
			Pad = Vector2.new(-12, 63.5),
			PriceSeconds = 115,
			Pieces = join(brazier(14, 62), brazier(-34, 66)),
		},
		-- 3
		{
			Id = "HellSign",
			Yaw = 8,
			Name = "Hell Sign",
			Description = "A blood-red signboard in a black horned frame on two posts, topped with a skull.",
			Pad = Vector2.new(-24, 52),
			PriceSeconds = 132,
			Pieces = at(-18, 6, function()
				return {
					B(-52, 0.4, 56, 22, 0.8, 4, ROCK, Basalt),
					B(-59, 5, 56, 1.4, 9.2, 1.4, BLK, Basalt),
					B(-45, 5, 56, 1.4, 9.2, 1.4, BLK, Basalt),
					B(-52, 8.4, 56.1, 20, 6, 0.8, BLK, Slate),
					B(-52, 8.4, 56.6, 18, 4.6, 0.5, RED, Plastic),
					B(-60, 12.4, 56, 1, 4.4, 1, BONE, Plastic, 0, 0, 28),
					B(-44, 12.4, 56, 1, 4.4, 1, BONE, Plastic, 0, 0, -28),
					Ball(-52, 12.6, 56, 3.2, 3, 2.6, BONE, Plastic),
				}
			end),
		},
		-- 4
		{
			Id = "SpikeFence",
			Name = "Spike Fence",
			Description = "A long black iron fence of spear points along the road edge, between two skull-topped stone posts.",
			Pad = Vector2.new(20, 61),
			PriceSeconds = 152,
			Pieces = join({
				B(41, 1.6, 65, 42, 0.6, 0.6, IRON, Metal),
				B(41, 4.6, 65, 42, 0.6, 0.6, IRON, Metal),
				B(21, 4, 65, 3, 8, 3, ROCK, Basalt),
				B(61, 4, 65, 3, 8, 3, ROCK, Basalt),
				Ball(21, 9.4, 65, 2.4, 2.4, 2.4, BONE, Plastic),
				Ball(61, 9.4, 65, 2.4, 2.4, 2.4, BONE, Plastic),
			}, {
				B(27, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
				B(33, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
				B(39, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
				B(45, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
				B(51, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
				B(57, 3.4, 65, 0.8, 7, 0.8, BLK, Metal),
			}),
		},
		-- 5
		{
			Id = "BoneHeap",
			Yaw = 20,
			Name = "Bone Heap",
			Description = "A mound of skulls, ribs and thigh bones with a spear and a grinning skull on top.",
			Pad = Vector2.new(-55, 45),
			PriceSeconds = 175,
			Pieces = {
				Ball(-62, 2.4, 40, 14, 4.8, 12, BONE, Plastic),
				Ball(-60, 5, 40, 8, 4, 7, BONE, Plastic),
				Ball(-66, 1.8, 36, 4, 3.6, 4, BONE, Plastic),
				Ball(-57, 1.6, 44, 3.6, 3.2, 3.4, BONE, Plastic),
				B(-62, 7, 40, 0.5, 12, 0.5, IRON, Metal),
				Ball(-62, 13.4, 40, 3, 2.8, 2.6, BONE, Plastic),
				B(-66.6, 5, 41, 0.8, 8, 0.8, BONE, Plastic, 0, 0, 24),
				B(-57.4, 5, 40.4, 0.8, 8, 0.8, BONE, Plastic, 0, 0, -24),
				B(-62, 4.4, 45, 0.8, 8, 0.8, BONE, Plastic, 38, 0, 0),
				Cx(-60, 1.2, 46, 1, 8, BONE, Plastic),
			},
		},
		-- 6
		{
			Id = "LavaPools",
			Name = "Lava Pools",
			Description = "Three bubbling pools of orange lava ringed with dark rock, with jagged boulders around them.",
			Pad = Vector2.new(-60, 28),
			PriceSeconds = 201,
			Pieces = at(-3, 3, function()
				return {
					B(-76, 0.25, 24, 14, 0.5, 14, BLK, Basalt),
					B(-76, 0.4, 24, 11.4, 0.3, 11.4, LAVA, Plastic),
					B(-66, 0.25, 13, 11, 0.5, 11, BLK, Basalt),
					B(-66, 0.4, 13, 8.6, 0.3, 8.6, LAVAY, Plastic),
					B(-81, 0.25, 10, 9, 0.5, 9, BLK, Basalt),
					B(-81, 0.4, 10, 6.6, 0.3, 6.6, LAVA, Plastic),
					Ball(-83, 2.2, 30, 4.4, 4.4, 4, ROCK, Rocky),
					Ball(-70, 2, 31, 3.6, 4, 3.6, ROCK, Rocky),
					Ball(-60, 1.8, 17, 3.4, 3.6, 3.4, ROCK, Rocky),
					Ball(-72, 2.4, 6, 4, 4.8, 4, ROCK, Rocky),
				}
			end),
		},
		-- 7
		{
			Id = "ObsidianShards",
			Yaw = -15,
			Name = "Obsidian Shards",
			Description = "A cluster of tall black glass spikes jutting out of the ground, a few veined red.",
			Pad = Vector2.new(68, 44),
			PriceSeconds = 231,
			Pieces = {
				B(76, 0.5, 48, 18, 1, 14, ROCK, Basalt),
				B(76, 8, 48, 3.6, 16, 3.6, BLK, Slate, 4, 20, 8),
				B(71, 6, 51, 3, 12, 3, OBS, Slate, -8, 45, -10),
				B(81, 5.4, 52, 3, 11, 3, BLK, Slate, 6, 10, 12),
				B(80, 4, 44, 3.4, 8, 3.4, OBS, Slate, 10, 60, 6),
				B(72, 4.2, 44, 2.6, 8.4, 2.6, BLK, Slate, -6, 30, -14),
				B(84, 3, 48, 2.4, 6, 2.4, RED, Slate, 0, 15, 18),
				B(68, 2.8, 48, 2.2, 5.6, 2.2, RED, Slate, 8, 50, -16),
				B(76, 2.4, 55, 2.6, 4.8, 2.6, BLK, Slate, 14, 0, 4),
			},
		},
		-- 8
		{
			Id = "DeadTrees",
			Name = "Charred Trees",
			Description = "Three burnt black trees with bare, clawing branches and glowing embers at their feet.",
			Pad = Vector2.new(-64, 2),
			PriceSeconds = 266,
			Pieces = {
				Cy(-74, 5.5, -2, 1.8, 11, BLK, Wood),
				B(-71.4, 10.6, -2, 5.4, 0.8, 0.8, BLK, Wood, 0, 0, 38),
				B(-77, 8.8, -1.6, 5, 0.8, 0.8, BLK, Wood, 0, 0, -34),
				B(-74, 12.4, -2.4, 3.6, 0.7, 0.7, BLK, Wood, 0, 30, 60),
				Cy(-82, 4.5, 6, 1.4, 9, BLK, Wood),
				B(-79.8, 8, 6, 4.4, 0.7, 0.7, BLK, Wood, 0, 0, 40),
				B(-84, 7, 6, 3.6, 0.7, 0.7, BLK, Wood, 0, 0, -38),
				Cy(-66, 4, -8, 1.6, 8, BLK, Wood),
				B(-63.8, 7.2, -8, 4, 0.7, 0.7, BLK, Wood, 0, 0, 36),
				B(-68, 6.2, -8, 3.6, 0.7, 0.7, BLK, Wood, 0, 0, -40),
				Ball(-74, 0.3, 2, 6, 0.6, 5, RED, Plastic),
				Ball(-80, 0.3, -6, 5, 0.6, 4, LAVA, Plastic),
			},
		},
		-- 9
		{
			Id = "Cauldron",
			Yaw = -24,
			Name = "Witch Cauldron",
			Description = "A huge black cauldron of bubbling green brew on three legs over a crackling fire, bones at its feet.",
			Pad = Vector2.new(-42, 20),
			PriceSeconds = 306,
			Pieces = {
				Ball(-48, 1.4, 22, 7, 3, 7, RED, Plastic),
				B(-50.4, 0.9, 20.6, 0.9, 1.8, 6, WOOD, Wood, 0, 20, 0),
				B(-45.6, 0.9, 20.6, 0.9, 1.8, 6, WOOD, Wood, 0, -20, 0),
				B(-50.4, 2.6, 24.4, 1, 5.2, 1, BLK, Metal, 10, 0, 18),
				B(-45.6, 2.6, 24.4, 1, 5.2, 1, BLK, Metal, 10, 0, -18),
				B(-48, 2.6, 19, 1, 5.2, 1, BLK, Metal, -14, 0, 0),
				Ball(-48, 6.4, 22, 10, 7.6, 10, BLK, Metal),
				Cy(-48, 9.8, 22, 9, 1.2, IRON, Metal),
				Cy(-48, 9.6, 22, 7.6, 0.8, GREEN, Plastic),
				Ball(-46.4, 10.6, 22.8, 2, 1.4, 2, GREEN, Plastic),
				Cx(-53.6, 0.6, 24.4, 1, 5, BONE, Plastic),
				Ball(-43, 0.9, 26.4, 2.2, 1.8, 2.2, BONE, Plastic),
			},
		},
		-- 10
		{
			Id = "SulfurVents",
			Name = "Sulfur Vents",
			Description = "Three yellow-crusted smoking vents that hiss grey brimstone clouds.",
			Pad = Vector2.new(-7, 11),
			PriceSeconds = 352,
			Pieces = {
				Cy(-4, 1.2, 16, 7, 2.4, ROCK, Rocky),
				Cy(-4, 3.2, 16, 4.4, 1.6, SULF, Concrete),
				Ball(-4, 7.4, 16, 4, 5, 4, ASH, Concrete),
				Cy(-12, 0.9, 22, 5.6, 1.8, ROCK, Rocky),
				Cy(-12, 2.5, 22, 3.4, 1.4, SULF, Concrete),
				Ball(-12, 5.8, 22, 3, 3.6, 3, ASH, Concrete),
				Cy(-2, 1, 26, 6, 2, ROCK, Rocky),
				Cy(-2, 2.7, 26, 3.6, 1.4, SULF, Concrete),
				Ball(-2, 6.2, 26, 3.2, 4, 3.2, ASH, Concrete),
				B(-6, 0.2, 21, 18, 0.4, 18, SULF, Concrete),
			},
		},
		-- 11
		{
			Id = "ImpStatues",
			Yaw = 30,
			Name = "Imp Statues",
			Description = "Two grinning purple imps on rock pedestals, horns up and little wings spread.",
			Pad = Vector2.new(68, 26),
			PriceSeconds = 405,
			Pieces = join(imp(72, 24), imp(81, 20)),
		},
		-- 12
		{
			Id = "GatePillars",
			RewardMult = 1.25,
			Yaw = -73,
			Name = "Gate Pillars",
			Description = "Two giant horned pillars stand either side of the walkway, a heavy iron chain hanging between them.",
			Pad = Vector2.new(6, 43),
			PriceSeconds = 466,
			Pieces = join(pillar(-6, 43), pillar(18, 43), {
				B(6, 14.6, 43, 24, 0.6, 0.6, IRON, Metal),
				B(6, 13.2, 43, 16, 0.6, 0.6, IRON, Metal),
			}),
		},
		-- 13
		{
			Id = "SkullTotems",
			Yaw = -20,
			Name = "Skull Totems",
			Description = "Three tall iron poles stacked with bleached skulls and crowned with horns.",
			Pad = Vector2.new(70, -10),
			PriceSeconds = 536,
			Pieces = {
				B(78, 0.5, -14, 14, 1, 6, ROCK, Basalt),
				Cy(74, 8, -14, 1.2, 16, IRON, Metal),
				Ball(74, 4, -14, 2.8, 2.6, 2.6, BONE, Plastic),
				Ball(74, 8, -14, 2.8, 2.6, 2.6, BONE, Plastic),
				Ball(74, 12, -14, 2.8, 2.6, 2.6, BONE, Plastic),
				Cy(78, 10, -14, 1.2, 20, IRON, Metal),
				Ball(78, 5, -14, 3, 2.8, 2.8, BONE, Plastic),
				Ball(78, 10, -14, 3, 2.8, 2.8, BONE, Plastic),
				Ball(78, 15, -14, 3, 2.8, 2.8, BONE, Plastic),
				B(78, 21.4, -14, 5, 0.8, 0.8, BONE, Plastic, 0, 0, 12),
				Cy(82, 7, -14, 1.2, 14, IRON, Metal),
				Ball(82, 4, -14, 2.8, 2.6, 2.6, BONE, Plastic),
				Ball(82, 9, -14, 2.8, 2.6, 2.6, BONE, Plastic),
				Ball(82, 14.6, -14, 2.4, 2.2, 2.2, RED, Plastic),
			},
		},
		-- 14
		{
			Id = "HellKennel",
			Yaw = -30,
			Name = "Hell Kennel",
			Description = "A spiked black doghouse with a glowing red doorway, a bone-filled bowl and a chain on a stake.",
			Pad = Vector2.new(38, -2),
			PriceSeconds = 616,
			Pieces = {
				B(44, 2.9, -8, 8, 5.8, 7, OBS, Basalt),
				B(44, 2.4, -4.4, 3.4, 4.2, 0.4, RED, Plastic),
				B(41.6, 7.2, -8, 5.6, 0.6, 8, BLK, Slate, 0, 0, 36),
				B(46.4, 7.2, -8, 5.6, 0.6, 8, BLK, Slate, 0, 0, -36),
				B(44, 9.4, -8, 1, 1.6, 8.4, RROCK, Slate),
				B(44, 10.6, -5, 0.8, 2.6, 0.8, BONE, Plastic),
				B(44, 10.6, -11, 0.8, 2.6, 0.8, BONE, Plastic),
				Cy(48.6, 0.5, -3, 3, 1, IRON, Metal),
				Ball(48.6, 1.4, -3, 2.4, 1.2, 2.4, BONE, Plastic),
				B(40, 1.2, -3.4, 0.7, 2.4, 0.7, IRON, Metal),
				Cx(40, 0.3, -2.2, 0.4, 3.6, IRON, Metal),
			},
		},
		-- 15
		{
			Id = "IronCages",
			Yaw = 12,
			Name = "Iron Cages",
			Description = "A black gallows frame with three iron cages hanging on chains, each holding a skull.",
			Pad = Vector2.new(22, 12),
			PriceSeconds = 708,
			Pieces = at(-12, -2, function()
				return {
					B(26, 0.5, 22, 18, 1, 6, ROCK, Basalt),
					B(18, 7.5, 22, 1.2, 14, 1.2, BLK, Wood),
					B(34, 7.5, 22, 1.2, 14, 1.2, BLK, Wood),
					B(26, 14.6, 22, 17, 1.2, 1.2, BLK, Wood),
					B(21, 13.6, 22, 5, 0.8, 0.6, BLK, Wood, 0, 0, 40),
					B(31, 13.6, 22, 5, 0.8, 0.6, BLK, Wood, 0, 0, -40),
					B(21, 11.4, 22, 0.3, 4.4, 0.3, IRON, Metal),
					B(26, 11.4, 22, 0.3, 4.4, 0.3, IRON, Metal),
					B(31, 11.4, 22, 0.3, 4.4, 0.3, IRON, Metal),
					B(21, 7.6, 22, 3.2, 4.4, 3.2, IRON, Metal),
					B(26, 7.2, 22, 3.6, 5, 3.6, IRON, Metal),
					B(31, 7.6, 22, 3.2, 4.4, 3.2, IRON, Metal),
					Ball(26, 6.4, 22, 1.8, 1.8, 1.8, BONE, Plastic),
				}
			end),
		},
		-- 16
		{
			Id = "RitualCircle",
			Name = "Ritual Circle",
			Description = "A blood-red summoning circle on the ground, five black standing stones and a bone altar with a skull.",
			Pad = Vector2.new(-12, 11),
			PriceSeconds = 814,
			Pieces = join({
				B(-24, 0.2, 10, 22, 0.4, 22, DRED, Slate),
				B(-24, 0.35, 10, 17, 0.3, 17, RED, Plastic),
				B(-24, 0.45, 10, 13.6, 0.3, 13.6, BLK, Slate),
				B(-24, 0.6, 10, 12, 0.2, 1, LAVA, Plastic, 0, 20, 0),
				B(-24, 0.6, 10, 12, 0.2, 1, LAVA, Plastic, 0, 92, 0),
				B(-24, 0.6, 10, 12, 0.2, 1, LAVA, Plastic, 0, 164, 0),
				B(-24, 1.2, 10, 5, 1.6, 3, BLK, Basalt),
				Ball(-24, 3, 10, 1.8, 1.8, 1.6, BONE, Plastic),
			}, {
				B(-24, 3.2, 18.5, 2, 6.4, 2, OBS, Slate, 6, 0, 4),
				B(-15.9, 3, 12.5, 2, 6, 2, OBS, Slate, 0, 72, -6),
				B(-18.9, 3.4, 2.9, 2, 6.8, 2, OBS, Slate, 4, 144, 5),
				B(-29.1, 3, 2.9, 2, 6, 2, OBS, Slate, -5, 216, 4),
				B(-32.1, 3.2, 12.5, 2, 6.4, 2, OBS, Slate, 0, 288, 6),
			}),
		},
		-- 17
		{
			Id = "WarBanners",
			Yaw = 15,
			Name = "War Banners",
			Description = "Three tall spiked war standards flying tattered blood-red banners.",
			Pad = Vector2.new(36, 44),
			PriceSeconds = 936,
			Pieces = {
				B(40, 0.6, 50, 3, 1.2, 3, ROCK, Basalt),
				Cy(40, 9, 50, 0.8, 16, IRON, Metal),
				B(42.4, 12.4, 50, 4.4, 6, 0.3, RED, Plastic),
				Ball(40, 17.6, 50, 1.4, 2.4, 1.4, BONE, Plastic),
				B(46, 0.6, 54, 3, 1.2, 3, ROCK, Basalt),
				Cy(46, 10, 54, 0.8, 18, IRON, Metal),
				B(48.4, 14, 54, 4.4, 6.4, 0.3, DRED, Plastic),
				Ball(46, 19.6, 54, 1.4, 2.4, 1.4, BONE, Plastic),
				B(50, 0.6, 46, 3, 1.2, 3, ROCK, Basalt),
				Cy(50, 8, 46, 0.8, 14, IRON, Metal),
				B(52.4, 11, 46, 4.4, 5.4, 0.3, RED, Plastic),
				Ball(50, 15.6, 46, 1.4, 2.4, 1.4, BONE, Plastic),
			},
		},
		-- 18
		{
			Id = "LavaFountain",
			Name = "Lava Fountain",
			Description = "A round rock basin of molten lava with a black spire in the middle, spouting orange lava into the air.",
			Pad = Vector2.new(-55, -22),
			PriceSeconds = 1076,
			Pieces = at(-2, 6, function()
				return {
					Cy(-68, 1, -28, 17, 2, ROCK, Rocky),
					Cy(-68, 2.1, -28, 14, 0.4, LAVA, Plastic),
					Cy(-68, 4, -28, 6, 5, BLK, Basalt),
					Cy(-68, 8.4, -28, 2.4, 6, LAVA, Plastic),
					Ball(-68, 12.4, -28, 3, 3, 3, LAVAY, Plastic),
					Ball(-72, 9, -28, 1.8, 1.8, 1.8, LAVA, Plastic),
					Ball(-64, 9, -28, 1.8, 1.8, 1.8, LAVA, Plastic),
					Ball(-68, 9, -32, 1.8, 1.8, 1.8, LAVA, Plastic),
					Ball(-75, 2.4, -28, 3.4, 4, 3.4, ROCK, Rocky),
					Ball(-61, 2.4, -28, 3.4, 4, 3.4, ROCK, Rocky),
					Ball(-68, 2.4, -35, 3.4, 4, 3.4, ROCK, Rocky),
					Ball(-68, 2.2, -21, 3.2, 3.6, 3.2, ROCK, Rocky),
				}
			end),
		},
		-- 19
		{
			Id = "BoneBridge",
			Name = "Bone Bridge",
			Description = "A humped bridge of bone planks and rib railings across a river of lava, skulls on the posts.",
			Pad = Vector2.new(-38, 48),
			PriceSeconds = 1238,
			Pieces = {
				B(-44, 0.25, 37, 8, 0.5, 24, LAVA, Plastic),
				B(-49.5, 0.3, 37, 3, 0.6, 24, BLK, Basalt),
				B(-38.5, 0.3, 37, 3, 0.6, 24, BLK, Basalt),
				B(-44, 2.4, 37, 18, 0.8, 4.4, BONE, Plastic),
				B(-49.4, 1.6, 37, 4, 0.8, 4.4, BONE, Plastic, 0, 0, 12),
				B(-38.6, 1.6, 37, 4, 0.8, 4.4, BONE, Plastic, 0, 0, -12),
				B(-52, 2.2, 34.6, 1.2, 4.4, 1.2, BONE, Plastic),
				B(-52, 2.2, 39.4, 1.2, 4.4, 1.2, BONE, Plastic),
				B(-36, 2.2, 34.6, 1.2, 4.4, 1.2, BONE, Plastic),
				B(-36, 2.2, 39.4, 1.2, 4.4, 1.2, BONE, Plastic),
				B(-44, 4.2, 34.6, 18, 0.6, 0.6, BONE, Plastic),
				B(-44, 4.2, 39.4, 18, 0.6, 0.6, BONE, Plastic),
				Ball(-52, 5.2, 34.6, 2, 2, 2, BONE, Plastic),
				Ball(-36, 5.2, 34.6, 2, 2, 2, BONE, Plastic),
			},
		},
		-- 20
		{
			Id = "RuinedWall",
			Name = "Ruined Fortress Wall",
			Description = "The broken black wall of an old demon fortress with crumbled towers and rubble.",
			Pad = Vector2.new(64, -21),
			PriceSeconds = 1424,
			Pieces = at(8, 0, function()
				return {
					B(49, 5.5, -28, 8, 11, 2.6, ROCK, Basalt),
					B(56, 3, -28, 6, 6, 2.6, OBS, Basalt),
					B(63, 6.5, -28, 7, 13, 2.6, ROCK, Basalt),
					B(69, 2.2, -28, 5, 4.4, 2.6, OBS, Basalt),
					B(49, 11.6, -28, 8.4, 1.2, 3, BLK, Basalt),
					B(63, 13.6, -28, 7.4, 1.2, 3, BLK, Basalt),
					B(53, 1, -25.6, 3, 2, 2.6, ROCK, Rocky),
					B(60, 0.8, -25.4, 2.4, 1.6, 2.2, OBS, Rocky),
					B(66, 1, -25.8, 2.8, 2, 2.4, ROCK, Rocky),
					B(56, 5, -28, 1.6, 2.4, 0.6, RED, Plastic),
					B(63, 8, -26.6, 2.2, 3.2, 0.4, DRED, Plastic),
					B(46, 4, -28, 1.8, 8, 3.4, OBS, Basalt),
				}
			end),
		},
		-- 21
		{
			Id = "Watchtower",
			Yaw = -20,
			Name = "Dark Watchtower",
			Description = "A tall black watchtower with glowing red windows, a spiked battlement and a horned roof.",
			Pad = Vector2.new(70, 8),
			PriceSeconds = 1637,
			Pieces = {
				B(78, 0.8, 4, 11, 1.6, 11, ROCK, Basalt),
				B(78, 9.6, 4, 7, 16, 7, OBS, Basalt),
				B(78, 18.4, 4, 11, 1.2, 11, ROCK, Basalt),
				B(78, 22, 4, 7.4, 6, 7.4, BLK, Basalt),
				B(78, 25.6, 4, 9.6, 1, 9.6, DRED, Slate),
				B(78, 29, 4, 1.6, 6, 1.6, BONE, Plastic),
				B(73.6, 19.6, -0.6, 1.4, 1.4, 1.4, ROCK, Basalt),
				B(82.4, 19.6, -0.6, 1.4, 1.4, 1.4, ROCK, Basalt),
				B(73.6, 19.6, 8.6, 1.4, 1.4, 1.4, ROCK, Basalt),
				B(82.4, 19.6, 8.6, 1.4, 1.4, 1.4, ROCK, Basalt),
				B(78, 11, 7.6, 1.6, 2.6, 0.3, RED, Plastic),
				B(78, 22, 7.8, 2, 2.4, 0.3, RED, Plastic),
				B(73, 27.4, 4, 0.8, 3.4, 0.8, BONE, Plastic, 0, 0, 24),
				B(83, 27.4, 4, 0.8, 3.4, 0.8, BONE, Plastic, 0, 0, -24),
			},
		},
		-- 22
		{
			Id = "DemonStatue",
			Yaw = 40,
			Name = "Demon Statue",
			Description = "A colossal black stone demon with curled horns, folded bat wings and a great sword planted in front of him.",
			Pad = Vector2.new(-62, -38),
			PriceSeconds = 1883,
			Pieces = {
				B(-72, 1.5, -44, 16, 3, 14, ROCK, Basalt),
				B(-75, 8.5, -44, 3.8, 11, 4.4, OBS, Basalt),
				B(-69, 8.5, -44, 3.8, 11, 4.4, OBS, Basalt),
				B(-72, 19, -44, 10, 10, 6, OBS, Basalt),
				B(-72, 14.4, -44, 11, 1.6, 6.6, DRED, Slate),
				B(-79, 18, -44, 3.6, 10, 3.6, OBS, Basalt, 0, 0, 12),
				B(-65, 18, -44, 3.6, 10, 3.6, OBS, Basalt, 0, 0, -12),
				Ball(-72, 26.4, -44, 5.6, 5.6, 5.4, OBS, Basalt),
				B(-75.4, 31, -44, 1.4, 5.4, 1.4, BONE, Plastic, 0, 0, 30),
				B(-68.6, 31, -44, 1.4, 5.4, 1.4, BONE, Plastic, 0, 0, -30),
				B(-79, 26, -46.6, 9, 14, 0.8, DRED, Slate, 0, 0, 22),
				B(-65, 26, -46.6, 9, 14, 0.8, DRED, Slate, 0, 0, -22),
				B(-72, 8, -40, 1.2, 14, 0.6, IRON, Metal),
				B(-72, 15.4, -40, 5, 0.8, 0.8, IRON, Metal),
				B(-72.0, 25.6, -41.9, 4.6, 1.4, 0.6, RED, Plastic),
			},
		},
		-- 23
		{
			Id = "FireAltar",
			Yaw = 24,
			Name = "Fire Altar",
			Description = "Three stepped black platforms around a great iron fire bowl blazing red, a spike at each corner.",
			Pad = Vector2.new(-43, -4),
			PriceSeconds = 2165,
			Pieces = at(8, 22, function()
				return {
					B(-60, 0.6, -16, 11, 1.2, 11, ROCK, Basalt),
					B(-60, 1.8, -16, 8.4, 1.2, 8.4, OBS, Basalt),
					B(-60, 3, -16, 6, 1.2, 6, RROCK, Basalt),
					Cy(-60, 4.6, -16, 5.4, 2, IRON, Metal),
					Ball(-60, 7.6, -16, 4.4, 6.4, 4.4, RED, Plastic),
					Ball(-60, 8.4, -16, 2.6, 5, 2.6, LAVA, Plastic),
					B(-64.4, 3.4, -20.4, 1, 6, 1, BLK, Metal),
					B(-55.6, 3.4, -20.4, 1, 6, 1, BLK, Metal),
					B(-64.4, 3.4, -11.6, 1, 6, 1, BLK, Metal),
					B(-55.6, 3.4, -11.6, 1, 6, 1, BLK, Metal),
					Ball(-64.4, 6.8, -20.4, 1.8, 1.8, 1.8, BONE, Plastic),
					Ball(-55.6, 6.8, -20.4, 1.8, 1.8, 1.8, BONE, Plastic),
					Ball(-64.4, 6.8, -11.6, 1.8, 1.8, 1.8, BONE, Plastic),
					Ball(-55.6, 6.8, -11.6, 1.8, 1.8, 1.8, BONE, Plastic),
				}
			end),
		},
		-- 24
		{
			Id = "LavaMoat",
			RewardMult = 1.3,
			Name = "Lava Moat",
			Description = "A glowing lava channel with black rock banks running round three sides of the throne ground.",
			Pad = Vector2.new(26, -30),
			PriceSeconds = 2490,
			Pieces = {
				B(10, 0.25, -47.75, 5, 0.5, 29.5, LAVA, Plastic),
				B(26, 0.25, -60, 32, 0.5, 5, LAVA, Plastic),
				B(42, 0.25, -47.75, 5, 0.5, 29.5, LAVA, Plastic),
				B(13.1, 0.6, -47.75, 1.2, 1.2, 29.5, BLK, Basalt),
				B(6.9, 0.6, -47.75, 1.2, 1.2, 29.5, BLK, Basalt),
				B(38.9, 0.6, -47.75, 1.2, 1.2, 29.5, BLK, Basalt),
				B(45.1, 0.6, -47.75, 1.2, 1.2, 29.5, BLK, Basalt),
				B(26, 0.6, -56.9, 25, 1.2, 1.2, BLK, Basalt),
				B(26, 0.6, -63.1, 39, 1.2, 1.2, BLK, Basalt),
				Ball(9, 1.6, -33, 3.2, 3.2, 3.2, ROCK, Rocky),
				Ball(43, 1.6, -33, 3.2, 3.2, 3.2, ROCK, Rocky),
				Ball(9.5, 1.4, -63, 3, 2.8, 3, ROCK, Rocky),
				Ball(42.5, 1.4, -63, 3, 2.8, 3, ROCK, Rocky),
			},
		},
		-- 25
		{
			Id = "SkullMountain",
			Name = "Skull Mountain",
			Description = "A mountain of black rock studded with skulls and crowned by one enormous horned skull.",
			Pad = Vector2.new(2, -27),
			PriceSeconds = 2863,
			Pieces = at(4, 0, function()
				return {
					Ball(-22, 4, -30, 26, 8, 22, ROCK, Rocky),
					Ball(-22, 9, -30, 17, 8, 14, OBS, Rocky),
					Ball(-22, 13.4, -30, 10, 6, 8, ROCK, Rocky),
					Ball(-22, 19, -30, 9, 7.6, 8, BONE, Plastic),
					B(-22, 15.8, -27.4, 6.4, 2, 4.4, BONE, Plastic),
					B(-24.2, 19.6, -26.2, 2.4, 2.4, 0.8, BLK, Slate),
					B(-19.8, 19.6, -26.2, 2.4, 2.4, 0.8, BLK, Slate),
					B(-26.6, 25, -30, 1.6, 6.4, 1.6, BONE, Plastic, 0, 0, 30),
					B(-17.4, 25, -30, 1.6, 6.4, 1.6, BONE, Plastic, 0, 0, -30),
					Ball(-31, 3.6, -24, 3.4, 3.2, 3.2, BONE, Plastic),
					Ball(-13, 3.2, -24, 3.2, 3, 3, BONE, Plastic),
					Ball(-27, 8, -23, 2.8, 2.6, 2.6, BONE, Plastic),
					Ball(-17, 8.4, -23, 2.8, 2.6, 2.6, BONE, Plastic),
				}
			end),
		},
		-- 26
		{
			Id = "GateArch",
			RewardMult = 1.4,
			Yaw = -60,
			Name = "Gate Arch",
			Description = "A towering horned arch of black and red rock spanning the walkway, a great skull on its keystone.",
			Pad = Vector2.new(-27.4, -54.2),
			PriceSeconds = 3293,
			Pieces = {
				B(-40.9, 1, -54.2, 6, 2, 6, ROCK, Basalt),
				B(-13.9, 1, -54.2, 6, 2, 6, ROCK, Basalt),
				B(-40.9, 12, -54.2, 4.4, 20, 4.4, OBS, Basalt),
				B(-13.9, 12, -54.2, 4.4, 20, 4.4, OBS, Basalt),
				B(-27.4, 22.2, -54.2, 31, 3.6, 5.2, RROCK, Basalt),
				B(-34.4, 26.4, -54.2, 13.6, 2.4, 4.4, OBS, Basalt, 0, 0, 22),
				B(-20.4, 26.4, -54.2, 13.6, 2.4, 4.4, OBS, Basalt, 0, 0, -22),
				Ball(-27.4, 24, -51.8, 5, 5, 3, BONE, Plastic),
				B(-42.9, 25, -54.2, 1.4, 6, 1.4, BONE, Plastic, 0, 0, 26),
				B(-11.9, 25, -54.2, 1.4, 6, 1.4, BONE, Plastic, 0, 0, -26),
				B(-40.9, 22.6, -51.4, 3.2, 2.4, 0.5, RED, Plastic),
				B(-13.9, 22.6, -51.4, 3.2, 2.4, 0.5, RED, Plastic),
				B(-27.4, 29.6, -54.2, 1.6, 4, 1.6, BONE, Plastic),
			},
		},
		-- 27
		{
			Id = "WingBackdrop",
			Name = "Wing Backdrop",
			Description = "Two giant black bat wings with bone fingers and blood-red membranes spread behind the throne.",
			Pad = Vector2.new(2.5, -62),
			PriceSeconds = 3787,
			Pieces = {
				B(26, 17, -66.5, 3.2, 34, 2.4, BLK, Basalt),
				B(16.5, 29, -66.5, 18, 1.2, 1.4, BONE, Plastic, 0, 0, 22),
				B(35.5, 29, -66.5, 18, 1.2, 1.4, BONE, Plastic, 0, 0, -22),
				B(15, 20, -66.5, 16, 1, 1.2, BONE, Plastic, 0, 0, 8),
				B(37, 20, -66.5, 16, 1, 1.2, BONE, Plastic, 0, 0, -8),
				B(13, 12, -66.5, 12, 1, 1.2, BONE, Plastic, 0, 0, -14),
				B(39, 12, -66.5, 12, 1, 1.2, BONE, Plastic, 0, 0, 14),
				B(16, 22, -66.8, 16, 14, 0.6, DRED, Plastic),
				B(36, 22, -66.8, 16, 14, 0.6, DRED, Plastic),
				B(13, 11, -66.8, 10, 8, 0.6, RED, Plastic),
				B(39, 11, -66.8, 10, 8, 0.6, RED, Plastic),
			},
		},
		-- 28
		{
			Id = "DemonThrone",
			RewardMult = 1.5,
			Name = "Demon Throne",
			Description = "A black spiked throne on a stepped red dais, a skull on its tall back and a bone spike on each side.",
			Pad = Vector2.new(26, -37),
			PriceSeconds = 4355,
			Pieces = {
				B(26, 0.6, -48, 22, 1.2, 16, ROCK, Basalt),
				B(26, 1.8, -49, 17, 1.2, 12, RROCK, Basalt),
				B(26, 3.6, -50, 9, 2.4, 7, BLK, Basalt),
				B(26, 11, -52.8, 9, 14, 1.8, OBS, Basalt),
				B(21.4, 6.2, -50, 1.4, 4, 7, BLK, Basalt),
				B(30.6, 6.2, -50, 1.4, 4, 7, BLK, Basalt),
				B(26, 18.4, -52.8, 11, 1.6, 2.4, RROCK, Basalt),
				Ball(26, 20.8, -52.4, 3.6, 3.4, 2.8, BONE, Plastic),
				B(22, 19.6, -52.8, 1.2, 5, 1.2, BONE, Plastic, 0, 0, 18),
				B(30, 19.6, -52.8, 1.2, 5, 1.2, BONE, Plastic, 0, 0, -18),
				B(26, 20.4, -52.8, 1.2, 6, 1.2, BONE, Plastic),
				B(17.4, 4.6, -42.4, 1, 7, 1, BONE, Plastic),
				B(34.6, 4.6, -42.4, 1, 7, 1, BONE, Plastic),
				Ball(17.4, 8.6, -42.4, 2.2, 2.2, 2.2, BONE, Plastic),
				Ball(34.6, 8.6, -42.4, 2.2, 2.2, 2.2, BONE, Plastic),
			},
		},
		-- 29
		{
			Id = "HellfireSpire",
			Name = "Hellfire Spire",
			Description = "A very tall tapering obsidian tower with red-lit balconies, crowned by a spiked iron cage of blazing fire.",
			Pad = Vector2.new(-64, -61),
			PriceSeconds = 5008,
			Pieces = {
				B(-78, 1, -62, 14, 2, 14, ROCK, Basalt),
				B(-78, 8, -62, 9, 12, 9, OBS, Basalt),
				B(-78, 14.6, -62, 12, 1.2, 12, RROCK, Basalt),
				B(-78, 21, -62, 7, 12, 7, BLK, Basalt),
				B(-78, 27.6, -62, 10, 1.2, 10, RROCK, Basalt),
				B(-78, 34, -62, 5, 12, 5, OBS, Basalt),
				B(-78, 41.4, -62, 3.2, 3, 3.2, IRON, Metal),
				Cy(-78, 44, -62, 7, 1.6, IRON, Metal),
				Ball(-78, 47.6, -62, 5.4, 7.2, 5.4, RED, Plastic),
				Ball(-78, 48.6, -62, 3.2, 5.4, 3.2, LAVA, Plastic),
				B(-82.6, 4.4, -66.6, 1.6, 8, 1.6, OBS, Basalt, 0, 0, 14),
				B(-73.4, 4.4, -66.6, 1.6, 8, 1.6, OBS, Basalt, 0, 0, -14),
				B(-82.6, 4.4, -57.4, 1.6, 8, 1.6, OBS, Basalt, 0, 0, 14),
				B(-73.4, 4.4, -57.4, 1.6, 8, 1.6, OBS, Basalt, 0, 0, -14),
			},
		},
		-- 30
		{
			Id = "HellfirePortal",
			RewardMult = 1.8,
			Yaw = -25,
			Name = "Hellfire Portal",
			Description = "A huge ring of horned black rock holding a swirling red whirlpool of hellfire.",
			Pad = Vector2.new(66, -40),
			PriceSeconds = 5759,
			Pieces = {
				B(68, 1, -50, 30, 2, 12, ROCK, Basalt),
				Cz(68, 16, -50, 24, 3.2, OBS, Basalt),
				Cz(68, 16, -49.6, 18, 3.6, RED, Plastic),
				Cz(68, 16, -49.4, 13, 3.8, DRED, Plastic),
				Cz(68, 16, -49.2, 8.4, 4, LAVA, Plastic),
				Cz(68, 16, -49, 4, 4.2, LAVAY, Plastic),
				B(60, 8, -50, 3.4, 14, 3.4, BLK, Basalt),
				B(76, 8, -50, 3.4, 14, 3.4, BLK, Basalt),
				B(68, 29, -50, 1.6, 5.4, 1.6, BONE, Plastic),
				B(60.6, 26, -50, 1.6, 6, 1.6, BONE, Plastic, 0, 0, 28),
				B(75.4, 26, -50, 1.6, 6, 1.6, BONE, Plastic, 0, 0, -28),
				Ball(68, 28.4, -50, 4, 3.6, 3, BONE, Plastic),
				B(53.4, 1, -50, 3, 2, 3, RROCK, Basalt),
				B(82.6, 1, -50, 3, 2, 3, RROCK, Basalt),
			},
		},
	},
}

return theme
