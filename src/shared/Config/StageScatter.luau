--!strict
-- The organic dressing of the Shiba stages (World/StageScatter): trees, bushes, rocks, flowers, fence rows along the winding
-- path, tufts along the stage edge. Pure data. Every stage gets a deterministic scatter (seeded by plot slot and bay), built
-- once when the stage becomes available and removed with it; it appears silently (no pop-in) and never touches the walkway,
-- the pads, the Shiba zone, the Intern spot or the solid pieces of the theme.
--
-- MODELS: a prop `<Name>` is the model ReplicatedStorage.Assets.Scatter_<Name> (assets/models/scatter, see its README.md). It is
-- fitted to the nominal size below (Height, or Width / Length, see `Fit`) whatever scale it was imported at, its bottom centre
-- stands on the ground. Without the model a simple primitive prop (`Kind`) is built instead, so everything works without assets.
-- Names the code expects (they must match assets/models/scatter/README.md):
--   Trees:    OakA OakB Birch Pine PineSnow PalmA PalmB SakuraTree DeadTree
--   Bushes:   Bush BushFlowers Hedge Beachgrass BambooClump
--   Flowers:  FlowerPatch
--   Rocks:    RockA RockB RockC RockRed ShellRock ZenRock RuneStoneSmall
--   Ground:   GrassTuft
--   Fences (long axis = X, one segment): PicketFenceSegment ChainFenceSegment WoodFenceSegment LowFenceSegment ShieldFence
--   Misc:     LampPost StreetLamp StumpLog LogPile GardenGnome Driftwood Towel SandcastleSmall Crate TrafficCone Barrel Dumpster
--             PlanterBox Hydrant Cactus Haystack Tumbleweed RopeCoil Anchor Net StoneLantern
--
-- Props are anchored, not collidable and not queryable (clicks pass through), except a small invisible collider for the trunk
-- of big trees (`Collide = "Trunk"`) and for boulders over 4 studs (`Collide = "Boulder"`).

export type Prop = {
	-- Fallback shape: Oak Birch Pine Palm DeadTree Bush Flowers Hedge Rock Tuft Blades Stump LogPile Log Lamp Crate Barrel Cone
	-- Dumpster Planter Hydrant Cactus Haystack Ball Rope Anchor Net Bamboo Lantern Towel Sandcastle Gnome Standing
	-- FencePicket FenceChain FenceWood FenceLow FenceShield
	Kind: string,
	-- Nominal height and footprint diameter at scale 1 (studs), and for fences the length of one segment.
	Height: number,
	Width: number,
	Length: number?,
	-- Which side the model is fitted by: "Height" (default), "Width" (longest horizontal side) or "Length" (X, fences).
	Fit: string?,
	-- Main colour (leaves, stone, wood) and a second one (trunk, flowers, details).
	Color: Color3,
	Color2: Color3?,
	-- "Trunk" (invisible collider of Trunk studs across, only when the prop is 8+ studs tall) or "Boulder" (a ball collider when
	-- the prop is more than 4 studs tall).
	Collide: string?,
	Trunk: number?,
	-- Random lean in degrees (rocks, logs, fences).
	Tilt: number?,
}

-- Prop name -> weight (a heavier entry is picked more often).
export type Entries = { [string]: number }

export type FenceStyle = {
	-- The fence prop (a segment `Length` studs long, long axis = X).
	Name: string,
	-- Share of the path that is fenced (0 to 1; the rest are gaps) and how far outside the path's edge the row stands.
	Coverage: number,
	Offset: number,
}

export type Biome = {
	-- Multiplies the number of clusters, fence segments and edge props (about 40 to 90 props per stage at 1).
	Density: number,
	Trees: Entries?,
	Bushes: Entries?,
	Rocks: Entries?,
	Flowers: Entries?,
	Misc: Entries?,
	-- The small ground cover used for tufts along the path and the stage edge (and inside clusters).
	Cover: string,
	Fence: FenceStyle?,
	-- Weight of each cluster type (Trees, Rocks, Bushes, Flowers, Misc); missing = default.
	Mix: { Trees: number?, Rocks: number?, Bushes: number?, Flowers: number?, Misc: number? }?,
}

-- A hand-placed prop (see Pins below): the prop `Name`, its place in the stage frame in UNSCALED theme units (multiplied by
-- StageScale like the theme coordinates), Yaw in degrees (default 0) and Scale (default 1 = the prop's nominal size).
export type Pin = {
	Name: string,
	X: number,
	Z: number,
	Yaw: number?,
	Scale: number?,
}

local function c(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local LEAF = c(78, 148, 62)
local LEAF_DARK = c(52, 112, 56)
local BARK = c(112, 80, 52)
local STONE = c(142, 142, 148)
local STONE_DARK = c(104, 106, 114)
local WOOD = c(150, 108, 66)
local WOOD_DARK = c(108, 78, 50)
local METAL = c(110, 116, 128)

local Props: { [string]: Prop } = {
	-- Trees
	OakA = { Kind = "Oak", Height = 16, Width = 10, Color = LEAF, Color2 = BARK, Collide = "Trunk", Trunk = 1.6 },
	OakB = {
		Kind = "Oak",
		Height = 13,
		Width = 9,
		Color = c(96, 160, 58),
		Color2 = c(100, 74, 50),
		Collide = "Trunk",
		Trunk = 1.4,
	},
	Birch = {
		Kind = "Oak",
		Height = 15,
		Width = 7,
		Color = c(140, 186, 76),
		Color2 = c(232, 228, 214),
		Collide = "Trunk",
		Trunk = 1,
	},
	Pine = {
		Kind = "Pine",
		Height = 18,
		Width = 8,
		Color = LEAF_DARK,
		Color2 = c(90, 64, 44),
		Collide = "Trunk",
		Trunk = 1.2,
	},
	PineSnow = {
		Kind = "Pine",
		Height = 18,
		Width = 8,
		Color = c(70, 120, 92),
		Color2 = c(236, 242, 248),
		Collide = "Trunk",
		Trunk = 1.2,
	},
	PalmA = { Kind = "Palm", Height = 15, Width = 11, Color = c(70, 160, 70), Color2 = c(150, 118, 78) },
	PalmB = { Kind = "Palm", Height = 12, Width = 9, Color = c(96, 170, 64), Color2 = c(138, 106, 70) },
	SakuraTree = {
		Kind = "Oak",
		Height = 14,
		Width = 11,
		Color = c(246, 168, 196),
		Color2 = c(92, 64, 56),
		Collide = "Trunk",
		Trunk = 1.4,
	},
	DeadTree = { Kind = "DeadTree", Height = 12, Width = 7, Color = c(98, 84, 74), Collide = "Trunk", Trunk = 1.2 },

	-- Bushes, flowers, hedges
	Bush = { Kind = "Bush", Height = 3.2, Width = 4.5, Color = LEAF },
	BushFlowers = {
		Kind = "Flowers",
		Height = 3.2,
		Width = 4.5,
		Color = c(70, 140, 60),
		Color2 = c(255, 120, 160),
	},
	FlowerPatch = {
		Kind = "Flowers",
		Height = 1.2,
		Width = 5,
		Color = c(84, 156, 66),
		Color2 = c(255, 214, 70),
		Fit = "Width",
	},
	Hedge = { Kind = "Hedge", Height = 3.4, Width = 7, Color = c(58, 122, 58), Fit = "Width" },
	Beachgrass = { Kind = "Blades", Height = 3.2, Width = 3.2, Color = c(160, 176, 84) },
	BambooClump = { Kind = "Bamboo", Height = 11, Width = 3.5, Color = c(120, 168, 74) },
	GrassTuft = { Kind = "Tuft", Height = 1.4, Width = 1.8, Color = c(88, 160, 70) },

	-- Rocks
	RockA = { Kind = "Rock", Height = 2.4, Width = 3.4, Color = STONE, Tilt = 14 },
	RockB = { Kind = "Rock", Height = 3.6, Width = 4.8, Color = STONE_DARK, Tilt = 14 },
	RockC = { Kind = "Rock", Height = 6, Width = 7.5, Color = c(124, 126, 134), Collide = "Boulder", Tilt = 10 },
	RockRed = { Kind = "Rock", Height = 4.4, Width = 5.8, Color = c(176, 98, 66), Collide = "Boulder", Tilt = 12 },
	ShellRock = { Kind = "Rock", Height = 2, Width = 3, Color = c(232, 200, 190), Tilt = 14 },
	ZenRock = { Kind = "Rock", Height = 3.2, Width = 4.2, Color = c(96, 102, 108), Tilt = 8 },
	RuneStoneSmall = {
		Kind = "Standing",
		Height = 5,
		Width = 2.8,
		Color = c(118, 120, 128),
		Color2 = c(90, 190, 255),
		Tilt = 6,
	},

	-- Wood, street and camp props
	StumpLog = { Kind = "Stump", Height = 1.8, Width = 3, Color = WOOD, Color2 = c(200, 164, 112) },
	LogPile = { Kind = "LogPile", Height = 3, Width = 6, Color = WOOD_DARK, Color2 = c(200, 164, 112), Fit = "Width" },
	Driftwood = { Kind = "Log", Height = 1.4, Width = 7, Color = c(184, 168, 148), Fit = "Width", Tilt = 5 },
	LampPost = { Kind = "Lamp", Height = 9, Width = 1.6, Color = c(40, 46, 52), Color2 = c(255, 232, 160) },
	StreetLamp = { Kind = "Lamp", Height = 12, Width = 1.8, Color = c(86, 94, 104), Color2 = c(255, 240, 190) },
	GardenGnome = { Kind = "Gnome", Height = 2.4, Width = 1.4, Color = c(220, 52, 52), Color2 = c(70, 110, 200) },
	Towel = {
		Kind = "Towel",
		Height = 0.2,
		Width = 5,
		Color = c(240, 90, 120),
		Color2 = c(255, 255, 255),
		Fit = "Width",
	},
	SandcastleSmall = { Kind = "Sandcastle", Height = 3, Width = 4, Color = c(232, 206, 150) },
	Crate = { Kind = "Crate", Height = 3, Width = 3, Color = WOOD, Color2 = WOOD_DARK },
	TrafficCone = { Kind = "Cone", Height = 2.6, Width = 1.8, Color = c(255, 128, 30), Color2 = c(250, 250, 250) },
	Barrel = { Kind = "Barrel", Height = 3.4, Width = 2.6, Color = c(150, 98, 56), Color2 = METAL },
	Dumpster = {
		Kind = "Dumpster",
		Height = 4,
		Width = 6,
		Color = c(54, 112, 78),
		Color2 = c(40, 80, 58),
		Fit = "Width",
	},
	PlanterBox = { Kind = "Planter", Height = 3.6, Width = 6, Color = c(196, 190, 176), Color2 = LEAF, Fit = "Width" },
	Hydrant = { Kind = "Hydrant", Height = 3, Width = 1.8, Color = c(212, 44, 44), Color2 = c(240, 200, 60) },
	Cactus = { Kind = "Cactus", Height = 7, Width = 2.2, Color = c(74, 150, 86) },
	Haystack = { Kind = "Haystack", Height = 4.6, Width = 5, Color = c(222, 186, 84) },
	Tumbleweed = { Kind = "Ball", Height = 2.2, Width = 2.2, Color = c(190, 154, 100) },
	RopeCoil = { Kind = "Rope", Height = 0.8, Width = 3, Color = c(196, 166, 110), Fit = "Width" },
	Anchor = { Kind = "Anchor", Height = 5, Width = 3, Color = c(60, 64, 72) },
	Net = { Kind = "Net", Height = 0.5, Width = 6, Color = c(176, 150, 104), Fit = "Width" },
	StoneLantern = { Kind = "Lantern", Height = 4.6, Width = 2.2, Color = c(152, 154, 160), Color2 = c(255, 224, 150) },

	-- Fence segments: long axis X, `Length` studs per segment.
	PicketFenceSegment = {
		Kind = "FencePicket",
		Height = 3.2,
		Width = 1,
		Length = 6,
		Fit = "Length",
		Color = c(248, 246, 240),
		Tilt = 2.5,
	},
	ChainFenceSegment = {
		Kind = "FenceChain",
		Height = 4.4,
		Width = 1,
		Length = 6,
		Fit = "Length",
		Color = c(150, 156, 166),
		Tilt = 2,
	},
	WoodFenceSegment = {
		Kind = "FenceWood",
		Height = 3.4,
		Width = 1,
		Length = 6,
		Fit = "Length",
		Color = WOOD,
		Tilt = 3.5,
	},
	LowFenceSegment = {
		Kind = "FenceLow",
		Height = 1.8,
		Width = 1,
		Length = 5,
		Fit = "Length",
		Color = c(120, 86, 58),
		Tilt = 2.5,
	},
	ShieldFence = {
		Kind = "FenceShield",
		Height = 3.6,
		Width = 1,
		Length = 6,
		Fit = "Length",
		Color = c(116, 82, 54),
		Color2 = c(200, 60, 60),
		Tilt = 2,
	},
}

-- ---- biomes ---------------------------------------------------------------------------------------------------------------

local Default: Biome = {
	Density = 1,
	Trees = { OakA = 3, OakB = 3, Birch = 2 },
	Bushes = { Bush = 4, BushFlowers = 2 },
	Rocks = { RockA = 3, RockB = 2 },
	Flowers = { FlowerPatch = 3 },
	Misc = { StumpLog = 1 },
	Cover = "GrassTuft",
}

local Biomes: { [number]: Biome } = {
	-- 1 Little House: a suburban park with picket fences.
	[1] = {
		Density = 1,
		Trees = { OakA = 3, OakB = 3, Birch = 3 },
		Bushes = { Bush = 3, BushFlowers = 3, Hedge = 1 },
		Rocks = { RockA = 1, RockB = 1 },
		Flowers = { FlowerPatch = 4 },
		Misc = { StumpLog = 1, GardenGnome = 0.5, LampPost = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "PicketFenceSegment", Coverage = 0.6, Offset = 2.2 },
	},
	-- 2 Beach Bar: palms, beach grass, driftwood.
	[2] = {
		Density = 0.95,
		Trees = { PalmA = 3, PalmB = 3 },
		Bushes = { Beachgrass = 5 },
		Rocks = { ShellRock = 3, RockB = 1 },
		Misc = { Driftwood = 3, Towel = 1, SandcastleSmall = 1 },
		Cover = "Beachgrass",
		Mix = { Trees = 3, Bushes = 3, Rocks = 1.5, Misc = 2, Flowers = 0 },
	},
	-- 3 Gym: concrete, chain fences, cones, barrels.
	[3] = {
		Density = 0.9,
		Trees = { Birch = 1 },
		Bushes = { Hedge = 2 },
		Rocks = { RockA = 2 },
		Misc = { TrafficCone = 4, Barrel = 3, Dumpster = 1, StreetLamp = 2, Hydrant = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.6, Offset = 2.4 },
		Mix = { Trees = 0.6, Bushes = 1, Rocks = 1, Misc = 4, Flowers = 0 },
	},
	-- 4 Food Truck Plaza: planters and lamps.
	[4] = {
		Density = 0.85,
		Trees = { OakB = 2, Birch = 2 },
		Bushes = { Bush = 2, BushFlowers = 2 },
		Rocks = { RockA = 1 },
		Flowers = { FlowerPatch = 3 },
		Misc = { PlanterBox = 4, StreetLamp = 3, Hydrant = 0.5 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.4, Offset = 2.2 },
		Mix = { Trees = 1.5, Bushes = 2, Rocks = 0.5, Misc = 4, Flowers = 1.5 },
	},
	-- 5 DJ stage: lamps, barrels, crates.
	[5] = {
		Density = 0.85,
		Trees = { Birch = 1 },
		Bushes = { Bush = 2 },
		Rocks = { RockA = 1 },
		Misc = { StreetLamp = 3, Barrel = 3, Crate = 3 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.4, Offset = 2.4 },
		Mix = { Trees = 0.6, Bushes = 1, Rocks = 0.8, Misc = 4, Flowers = 0 },
	},
	-- 6 Police: chain fences and cones.
	[6] = {
		Density = 0.9,
		Trees = { Birch = 1 },
		Bushes = { Hedge = 1, Bush = 1 },
		Rocks = { RockA = 1 },
		Misc = { TrafficCone = 4, StreetLamp = 2, Hydrant = 1, Barrel = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.7, Offset = 2.4 },
		Mix = { Trees = 0.6, Bushes = 1, Rocks = 0.8, Misc = 4, Flowers = 0 },
	},
	-- 7 Western: cactus, haystacks, wooden fences.
	[7] = {
		Density = 0.95,
		Trees = { DeadTree = 2 },
		Bushes = { Tumbleweed = 3 },
		Rocks = { RockRed = 3, RockA = 1 },
		Misc = { Cactus = 4, Haystack = 2, Crate = 2, Barrel = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "WoodFenceSegment", Coverage = 0.65, Offset = 2.4 },
		Mix = { Trees = 1, Bushes = 1.5, Rocks = 2, Misc = 4, Flowers = 0 },
	},
	-- 8 Pirate: crates, barrels, ropes, palms.
	[8] = {
		Density = 0.95,
		Trees = { PalmA = 2, PalmB = 2 },
		Bushes = { Beachgrass = 2 },
		Rocks = { RockB = 2, ShellRock = 1 },
		Misc = { Crate = 3, Barrel = 3, RopeCoil = 2, Anchor = 1, Net = 1, Driftwood = 2 },
		Cover = "Beachgrass",
		Fence = { Name = "WoodFenceSegment", Coverage = 0.35, Offset = 2.4 },
		Mix = { Trees = 2, Bushes = 1, Rocks = 1.5, Misc = 4, Flowers = 0 },
	},
	-- 9 Ninja: bamboo, sakura, lanterns, a low fence.
	[9] = {
		Density = 0.95,
		Trees = { SakuraTree = 3, Pine = 1 },
		Bushes = { BambooClump = 4, Bush = 1 },
		Rocks = { ZenRock = 3, RockA = 1 },
		Flowers = { FlowerPatch = 1 },
		Misc = { StoneLantern = 3, StumpLog = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.6, Offset = 2.2 },
		Mix = { Trees = 3, Bushes = 3, Rocks = 2, Misc = 2, Flowers = 0.5 },
	},
	-- 10 Viking: pines, logs, rune stones.
	[10] = {
		Density = 1,
		Trees = { Pine = 4, PineSnow = 1 },
		Bushes = { Bush = 1 },
		Rocks = { RockB = 2, RockC = 1, RuneStoneSmall = 2 },
		Misc = { StumpLog = 2, LogPile = 2, Barrel = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "ShieldFence", Coverage = 0.5, Offset = 2.4 },
		Mix = { Trees = 4, Bushes = 0.8, Rocks = 3, Misc = 2, Flowers = 0 },
	},
	-- 11 Knight
	[11] = {
		Density = 0.95,
		Trees = { OakA = 2, OakB = 2 },
		Bushes = { Bush = 2, Hedge = 2 },
		Rocks = { RockB = 2, RockC = 1 },
		Misc = { LampPost = 2, LogPile = 1, Barrel = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "ShieldFence", Coverage = 0.5, Offset = 2.4 },
	},
	-- 12 Samurai
	[12] = {
		Density = 0.95,
		Trees = { SakuraTree = 3 },
		Bushes = { BambooClump = 3, Bush = 1 },
		Rocks = { ZenRock = 3, RockA = 1 },
		Misc = { StoneLantern = 3 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.6, Offset = 2.2 },
	},
	-- 13 Robot
	[13] = {
		Density = 0.85,
		Bushes = { Hedge = 1 },
		Rocks = { RockA = 2, RockC = 1 },
		Misc = { Barrel = 3, Crate = 3, Dumpster = 1, StreetLamp = 3 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.5, Offset = 2.4 },
		Mix = { Trees = 0, Bushes = 0.5, Rocks = 1.5, Misc = 4, Flowers = 0 },
	},
	-- 14 Astronaut
	[14] = {
		Density = 0.8,
		Rocks = { RockC = 2, RockB = 3, RockA = 3 },
		Misc = { Crate = 2, StreetLamp = 2, Barrel = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.35, Offset = 2.4 },
		Mix = { Trees = 0, Bushes = 0, Rocks = 4, Misc = 2, Flowers = 0 },
	},
	-- 15 Superhero
	[15] = {
		Density = 0.9,
		Trees = { Birch = 2, OakB = 1 },
		Bushes = { Bush = 2 },
		Rocks = { RockA = 1 },
		Misc = { StreetLamp = 3, Hydrant = 1, Dumpster = 1, PlanterBox = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.5, Offset = 2.4 },
		Mix = { Trees = 1, Bushes = 1, Rocks = 0.8, Misc = 4, Flowers = 0 },
	},
	-- 16 Gold
	[16] = {
		Density = 0.9,
		Trees = { OakA = 2, Birch = 2 },
		Bushes = { Bush = 2, BushFlowers = 2, Hedge = 1 },
		Rocks = { RockA = 1 },
		Flowers = { FlowerPatch = 3 },
		Misc = { LampPost = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.5, Offset = 2.2 },
	},
	-- 17 Wizard
	[17] = {
		Density = 1,
		Trees = { Pine = 2, Birch = 2, DeadTree = 1 },
		Bushes = { Bush = 2 },
		Rocks = { RuneStoneSmall = 3, ZenRock = 2, RockB = 1 },
		Flowers = { FlowerPatch = 1 },
		Misc = { StoneLantern = 2, StumpLog = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.4, Offset = 2.2 },
	},
	-- 18 Vampire
	[18] = {
		Density = 0.95,
		Trees = { DeadTree = 4, Pine = 1 },
		Bushes = { Bush = 1 },
		Rocks = { RockA = 2, RockB = 1, RuneStoneSmall = 2 },
		Misc = { StumpLog = 2, StoneLantern = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "WoodFenceSegment", Coverage = 0.5, Offset = 2.4 },
	},
	-- 19 Pharaoh
	[19] = {
		Density = 0.9,
		Trees = { PalmA = 2, DeadTree = 1 },
		Bushes = { Tumbleweed = 2, Beachgrass = 2 },
		Rocks = { RockRed = 3, RockA = 1 },
		Misc = { Cactus = 3, Crate = 2, Barrel = 1 },
		Cover = "Beachgrass",
	},
	-- 20 Frost
	[20] = {
		Density = 0.95,
		Trees = { PineSnow = 4, Pine = 1 },
		Bushes = { Bush = 1 },
		Rocks = { RockC = 2, ZenRock = 2, RockB = 1 },
		Misc = { StumpLog = 2, LogPile = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "WoodFenceSegment", Coverage = 0.4, Offset = 2.4 },
		Mix = { Trees = 4, Bushes = 0.5, Rocks = 3, Misc = 1.5, Flowers = 0 },
	},
	-- 21 Magma
	[21] = {
		Density = 0.85,
		Trees = { DeadTree = 2 },
		Rocks = { RockRed = 4, RockB = 2, RockC = 1 },
		Misc = { Barrel = 1 },
		Cover = "GrassTuft",
		Mix = { Trees = 1, Bushes = 0, Rocks = 5, Misc = 0.8, Flowers = 0 },
	},
	-- 22 Dragon
	[22] = {
		Density = 0.95,
		Trees = { Pine = 3, DeadTree = 1 },
		Bushes = { Bush = 1 },
		Rocks = { RuneStoneSmall = 2, RockB = 2, RockRed = 2 },
		Misc = { StumpLog = 1 },
		Cover = "GrassTuft",
	},
	-- 23 Mecha
	[23] = {
		Density = 0.85,
		Rocks = { RockA = 2, RockC = 1 },
		Misc = { Dumpster = 1, Barrel = 3, Crate = 3, StreetLamp = 3, TrafficCone = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "ChainFenceSegment", Coverage = 0.5, Offset = 2.4 },
		Mix = { Trees = 0, Bushes = 0, Rocks = 1.5, Misc = 4, Flowers = 0 },
	},
	-- 24 Galaxy
	[24] = {
		Density = 0.8,
		Rocks = { ZenRock = 3, RuneStoneSmall = 2, RockC = 1 },
		Misc = { StoneLantern = 2 },
		Cover = "GrassTuft",
		Mix = { Trees = 0, Bushes = 0, Rocks = 4, Misc = 1.5, Flowers = 0 },
	},
	-- 25 Angel
	[25] = {
		Density = 0.95,
		Trees = { Birch = 3, OakB = 1, SakuraTree = 1 },
		Bushes = { BushFlowers = 3, Bush = 1 },
		Rocks = { RockA = 1 },
		Flowers = { FlowerPatch = 4 },
		Misc = { StoneLantern = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "LowFenceSegment", Coverage = 0.5, Offset = 2.2 },
	},
	-- 26 Demon
	[26] = {
		Density = 0.9,
		Trees = { DeadTree = 3 },
		Rocks = { RockRed = 3, RuneStoneSmall = 2, RockC = 1 },
		Misc = { StumpLog = 1 },
		Cover = "GrassTuft",
		Fence = { Name = "ShieldFence", Coverage = 0.4, Offset = 2.4 },
		Mix = { Trees = 2, Bushes = 0, Rocks = 4, Misc = 1, Flowers = 0 },
	},
	-- 27 Giant
	[27] = {
		Density = 0.85,
		Trees = { OakA = 3, OakB = 2 },
		Bushes = { Bush = 2 },
		Rocks = { RockC = 3, RockB = 1 },
		Misc = { StumpLog = 2, LogPile = 2 },
		Cover = "GrassTuft",
		Fence = { Name = "WoodFenceSegment", Coverage = 0.5, Offset = 2.4 },
	},
}

-- ---- hand tuning (docs/TUNING.md; filled in by pasting the output of docs/tools/studio_tuner.luau) ----------------------------

-- Pins[bay]: props placed by hand in addition to the random ones (no collision rejection, not counted in MaxProps).
local Pins: { [number]: { Pin } } = {
	-- [1] = { { Name = "OakA", X = 12, Z = -30, Yaw = 40, Scale = 1.2 } },
}

-- Skip[bay][index] = true: the random prop with that index (its place in the stage's generation order, shown by the tuner as
-- TuneIndex) is not built. Everything else stays exactly where it is.
local Skip: { [number]: { [number]: boolean } } = {
	-- [1] = { [17] = true, [23] = true },
}

return {
	-- Hard cap of props per stage and the playable half width of the floor the scatter may use.
	MaxProps = 110,
	MaxHalfWidth = 80,
	-- Clearances (studs): from the path's centre line (the walkway is 12 wide), from a pad, the Shiba (its platform and the zone in
	-- front of it), and from the solid pieces of the theme.
	PathClear = 7,
	PadClear = 6,
	ShibaClear = 9,
	ShibaZoneLength = 20,
	SolidMargin = 3,
	-- Scale of every prop: a random value in this range (fences are fitted to their row instead).
	ScaleMin = 0.8,
	ScaleMax = 1.4,
	-- Number of clusters (trees/bushes/rocks/flowers) at density 1, and of edge props along the Area border and the path edges.
	Clusters = 9,
	ClusterSpacing = 20,
	EdgeProps = 12,
	PathEdgeProps = 8,
	Props = Props,
	Biomes = Biomes,
	Default = Default,
	Pins = Pins,
	Skip = Skip,
}
