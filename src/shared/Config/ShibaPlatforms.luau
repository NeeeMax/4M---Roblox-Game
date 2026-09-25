--!strict
-- The platform every Shiba stands on, per tier, keyed by the tier's AssetName (Config/Gameplay → Shooters.Tiers).
-- NPCShooterService uses the model ReplicatedStorage.Assets.Platform_<AssetName> if it exists (assets/models/
-- build_props.py; scaled so its StandPoint marker is `ModelTop` or `Top` above the surface and its bottom ModelSink
-- below it), otherwise it builds the platform from these plain parts. `Default` is used for anything without its own
-- entry (the fallback block, the legacy `Shooter` model).
--
-- Rules that keep platforms looking right:
-- - Pieces that touch the island start below its surface (bottom < 0) and must not end exactly at 0: two faces at
--   the same height flicker (z-fighting). For the same reason, overlapping pieces never end at the same height.
-- - `Top` (where the Shiba stands) is at least Shooters.PlatformLift above the island surface.
-- - Diameter ≤ 21: the ring (radius 56) must stay clear of the trophy pedestals (radius 42) and the trees (66+).

export type PieceShape = "Block" | "Cylinder" | "Ball"

export type Piece = {
	Shape: PieceShape,
	-- Studs. Block: X × Y × Z. Cylinder (upright): X = diameter, Y = height. Ball: X = diameter.
	Size: Vector3,
	-- Centre of the piece relative to the island surface point under the Shiba. The platform faces the island
	-- centre: −Z points inward, +X to the right (seen from the centre looking out: left).
	Offset: Vector3,
	-- Turn about the vertical axis, in degrees.
	Yaw: number?,
	Color: Color3,
	Material: Enum.Material,
	Transparency: number?,
}

export type Platform = {
	-- Height of the standing surface above the island surface (studs).
	Top: number,
	-- Footprint; the invisible barrier (Shooters.Barrier) around the Shiba is this wide plus its padding.
	Diameter: number,
	-- Standing height when the Platform_<AssetName> model is used (default Top).
	ModelTop: number?,
	Pieces: { Piece },
}

local function cylinder(
	diameter: number,
	bottom: number,
	top: number,
	color: Color3,
	material: Enum.Material,
	x: number?,
	z: number?
): Piece
	return {
		Shape = "Cylinder",
		Size = Vector3.new(diameter, top - bottom, diameter),
		Offset = Vector3.new(x or 0, (bottom + top) / 2, z or 0),
		Color = color,
		Material = material,
	}
end

local function block(
	width: number,
	depth: number,
	bottom: number,
	top: number,
	color: Color3,
	material: Enum.Material,
	x: number?,
	z: number?,
	yaw: number?
): Piece
	return {
		Shape = "Block",
		Size = Vector3.new(width, top - bottom, depth),
		Offset = Vector3.new(x or 0, (bottom + top) / 2, z or 0),
		Yaw = yaw,
		Color = color,
		Material = material,
	}
end

local function ball(diameter: number, x: number, y: number, z: number, color: Color3, material: Enum.Material): Piece
	return {
		Shape = "Ball",
		Size = Vector3.new(diameter, diameter, diameter),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = material,
	}
end

-- Ground pieces reach this far into the island, so no gap shows at their foot.
local SINK = -0.5

-- `count` blocks evenly around a circle of `radius` (their width along the circle), the first at `startDegrees`
-- (0 = +X, 90 = +Z, i.e. away from the island centre), colours taken in turn from `colors`.
local function blockRing(
	count: number,
	radius: number,
	width: number,
	depth: number,
	bottom: number,
	top: number,
	colors: { Color3 },
	material: Enum.Material,
	startDegrees: number?
): { Piece }
	local pieces = {}
	for index = 1, count do
		local angle = (startDegrees or 0) + (index - 1) * 360 / count
		local rad = math.rad(angle)
		local color = colors[(index - 1) % #colors + 1]
		-- Yaw turns +X toward -Z, so -(angle + 90) lays the block's width along the circle.
		table.insert(
			pieces,
			block(
				width,
				depth,
				bottom,
				top,
				color,
				material,
				radius * math.cos(rad),
				radius * math.sin(rad),
				-(angle + 90)
			)
		)
	end
	return pieces
end

-- A list of pieces followed by more lists of pieces, as one list.
local function concat(...: { Piece }): { Piece }
	local out = {}
	for _, list in { ... } do
		for _, piece in list do
			table.insert(out, piece)
		end
	end
	return out
end

local WOOD = Color3.fromRGB(125, 85, 50)
local WOOD_LIGHT = Color3.fromRGB(215, 170, 110)
local WOOD_DARK = Color3.fromRGB(90, 60, 35)
local BLACK = Color3.fromRGB(25, 25, 30)
local GOLD = Color3.fromRGB(255, 200, 60)
local GOLD_DARK = Color3.fromRGB(225, 165, 35)
local WHITE = Color3.fromRGB(245, 245, 250)
local POLICE_BLUE = Color3.fromRGB(40, 80, 200)
local STONE = Color3.fromRGB(45, 45, 52)
local STONE_LIGHT = Color3.fromRGB(62, 62, 70)
local NINJA_RED = Color3.fromRGB(190, 25, 35)
local SPACE_ROCK = Color3.fromRGB(62, 34, 92)
local SPACE_ROCK_DARK = Color3.fromRGB(40, 22, 62)
local ROCK = Color3.fromRGB(120, 108, 98)
local ROCK_LIGHT = Color3.fromRGB(145, 132, 116)
local CRACK = Color3.fromRGB(55, 45, 40)
local CLOUD = Color3.fromRGB(250, 250, 255)
local MARBLE_GOLD = Color3.fromRGB(240, 215, 135)
-- Shibas 11-30.
local ROPE = Color3.fromRGB(220, 190, 130)
local HAY = Color3.fromRGB(235, 195, 90)
local TWINE = Color3.fromRGB(120, 75, 40)
local CACTUS = Color3.fromRGB(80, 170, 80)
local RED = Color3.fromRGB(200, 35, 40)
local BLUE = Color3.fromRGB(40, 80, 180)
local CREAM = Color3.fromRGB(245, 235, 205)
local BOOK_BLUE = Color3.fromRGB(55, 60, 175)
local BOOK_PURPLE = Color3.fromRGB(120, 50, 160)
local BOOK_RED = Color3.fromRGB(170, 40, 50)
local RUNE = Color3.fromRGB(90, 230, 255)
local MOON = Color3.fromRGB(185, 185, 195)
local MOON_DARK = Color3.fromRGB(120, 120, 132)
local STEEL = Color3.fromRGB(150, 158, 172)
local STEEL_DARK = Color3.fromRGB(62, 66, 78)
local HAZARD = Color3.fromRGB(250, 200, 40)
local CYAN = Color3.fromRGB(70, 240, 255)
local BRASS = Color3.fromRGB(215, 165, 60)
local VERMILION = Color3.fromRGB(220, 60, 35)
local TATAMI = Color3.fromRGB(205, 200, 125)
local SOIL = Color3.fromRGB(62, 46, 52)
local COFFIN = Color3.fromRGB(75, 38, 42)
local COFFIN_LID = Color3.fromRGB(48, 24, 30)
local SILVER = Color3.fromRGB(200, 200, 215)
local SAND = Color3.fromRGB(225, 190, 120)
local SAND_DARK = Color3.fromRGB(200, 165, 105)
local ROCK_DARK = Color3.fromRGB(70, 60, 58)
local NEON_PINK = Color3.fromRGB(255, 60, 200)
local CASTLE = Color3.fromRGB(165, 162, 172)
local CASTLE_DARK = Color3.fromRGB(115, 112, 125)
local FACADE = Color3.fromRGB(90, 110, 160)
local ROOF = Color3.fromRGB(150, 150, 158)
local ICE = Color3.fromRGB(160, 220, 245)
local SNOW = Color3.fromRGB(250, 252, 255)
local BASALT = Color3.fromRGB(45, 40, 42)
local LAVA = Color3.fromRGB(255, 110, 20)
local OBSIDIAN = Color3.fromRGB(34, 20, 40)
local HELLFIRE = Color3.fromRGB(255, 50, 20)
local NIGHT = Color3.fromRGB(40, 40, 110)
local MARBLE = Color3.fromRGB(248, 244, 232)
local VOID = Color3.fromRGB(12, 8, 22)
local VOID_PURPLE = Color3.fromRGB(150, 60, 255)

local platforms: { [string]: Platform } = {
	-- Tree stump with roots.
	Shiba = {
		Top = 1.4,
		Diameter = 8,
		Pieces = {
			cylinder(7, SINK, 1.3, WOOD, Enum.Material.Wood),
			cylinder(6.2, 1.3, 1.4, WOOD_LIGHT, Enum.Material.Wood),
			block(1.2, 2.4, SINK, 0.5, WOOD_DARK, Enum.Material.Wood, 3.2, 0, 90),
			block(1.2, 2.4, SINK, 0.45, WOOD_DARK, Enum.Material.Wood, -1.6, 2.8, -30),
			block(1.2, 2.4, SINK, 0.55, WOOD_DARK, Enum.Material.Wood, -1.6, -2.8, 30),
		},
	},
	-- Black podium with gold bands.
	ShadesShiba = {
		Top = 2,
		Diameter = 8,
		Pieces = {
			cylinder(7.6, SINK, 1.2, BLACK, Enum.Material.SmoothPlastic),
			cylinder(7.9, 0.4, 0.7, GOLD, Enum.Material.Foil),
			cylinder(7, 1.2, 1.9, GOLD, Enum.Material.Foil),
			cylinder(6.4, 1.9, 2, BLACK, Enum.Material.Glass),
		},
	},
	-- Gym weight plate lying flat.
	BuffShiba = {
		Top = 1.05,
		Diameter = 9,
		Pieces = {
			cylinder(8.6, SINK, 0.9, Color3.fromRGB(35, 35, 40), Enum.Material.SmoothPlastic),
			cylinder(8.8, 0.3, 0.5, Color3.fromRGB(200, 40, 40), Enum.Material.SmoothPlastic),
			cylinder(6.6, 0.9, 1, Color3.fromRGB(60, 60, 66), Enum.Material.SmoothPlastic),
			cylinder(2, 1, 1.05, Color3.fromRGB(200, 200, 210), Enum.Material.Metal),
		},
	},
	-- Kitchen counter with a cutting board.
	ChefShiba = {
		Top = 2.9,
		Diameter = 10.8,
		Pieces = {
			block(7, 7, SINK, 2.3, WHITE, Enum.Material.SmoothPlastic),
			block(7.6, 7.6, 2.3, 2.6, Color3.fromRGB(200, 200, 205), Enum.Material.Marble),
			block(5, 4, 2.6, 2.9, Color3.fromRGB(190, 130, 70), Enum.Material.Wood),
			-- Two cabinet doors with handles on the side facing the field.
			block(3.1, 0.1, 0.2, 2, Color3.fromRGB(215, 215, 210), Enum.Material.SmoothPlastic, -1.7, -3.55),
			block(3.1, 0.1, 0.2, 2, Color3.fromRGB(215, 215, 210), Enum.Material.SmoothPlastic, 1.7, -3.55),
			block(0.2, 0.2, 1.4, 1.8, Color3.fromRGB(170, 170, 180), Enum.Material.Metal, -0.5, -3.7),
			block(0.2, 0.2, 1.4, 1.8, Color3.fromRGB(170, 170, 180), Enum.Material.Metal, 0.5, -3.7),
		},
	},
	-- Blue and white striped pedestal with siren lights. The model is a small police car: the Shiba stands on its roof.
	PoliceShiba = {
		Top = 1.8,
		ModelTop = 3,
		Diameter = 8,
		Pieces = {
			cylinder(7.4, SINK, 0.3, POLICE_BLUE, Enum.Material.SmoothPlastic),
			cylinder(7.4, 0.3, 0.7, WHITE, Enum.Material.SmoothPlastic),
			cylinder(7.4, 0.7, 1.1, POLICE_BLUE, Enum.Material.SmoothPlastic),
			cylinder(7.4, 1.1, 1.5, WHITE, Enum.Material.SmoothPlastic),
			cylinder(7.4, 1.5, 1.8, POLICE_BLUE, Enum.Material.SmoothPlastic),
			ball(0.7, 3.1, 2, 0, Color3.fromRGB(255, 40, 40), Enum.Material.Neon),
			ball(0.7, -3.1, 2, 0, Color3.fromRGB(60, 120, 255), Enum.Material.Neon),
		},
	},
	-- Dark stone with a red trim.
	NinjaShiba = {
		Top = 1.6,
		Diameter = 8.5,
		Pieces = {
			cylinder(8, SINK, 1, STONE, Enum.Material.Slate),
			cylinder(8.2, 1, 1.2, NINJA_RED, Enum.Material.SmoothPlastic),
			cylinder(7.4, 1.2, 1.6, STONE_LIGHT, Enum.Material.Slate),
		},
	},
	-- Uneven stack of gold coins.
	GoldShiba = {
		Top = 2,
		Diameter = 9,
		Pieces = {
			cylinder(7.6, SINK, 0.35, GOLD, Enum.Material.Foil),
			cylinder(7.2, 0.35, 0.75, GOLD_DARK, Enum.Material.Foil, 0.3, 0),
			cylinder(7.4, 0.75, 1.15, GOLD, Enum.Material.Foil, -0.25, 0.2),
			cylinder(7, 1.15, 1.55, GOLD_DARK, Enum.Material.Foil, 0, -0.3),
			cylinder(7.2, 1.55, 2, GOLD, Enum.Material.Foil, 0.15, 0),
		},
	},
	-- Purple space rock floating over a glowing ring.
	GalaxyShiba = {
		Top = 3.2,
		Diameter = 8,
		Pieces = {
			{
				Shape = "Cylinder",
				Size = Vector3.new(6, 0.6, 6),
				Offset = Vector3.new(0, -0.1, 0),
				Color = Color3.fromRGB(140, 80, 255),
				Material = Enum.Material.Neon,
				Transparency = 0.7,
			},
			cylinder(1.8, 0.8, 1.2, SPACE_ROCK_DARK, Enum.Material.Slate),
			cylinder(3.6, 1.2, 1.8, SPACE_ROCK_DARK, Enum.Material.Slate),
			cylinder(5.4, 1.8, 2.4, SPACE_ROCK, Enum.Material.Slate),
			cylinder(7, 2.4, 3.2, SPACE_ROCK, Enum.Material.Slate),
			ball(0.8, 3.3, 1.6, 0.5, Color3.fromRGB(120, 220, 255), Enum.Material.Neon),
			ball(0.6, -2.9, 2, 1.6, Color3.fromRGB(255, 130, 230), Enum.Material.Neon),
		},
	},
	-- Cracked rock plateau with boulders.
	GiantShiba = {
		Top = 1.8,
		Diameter = 21,
		Pieces = {
			cylinder(20, SINK, 1.4, ROCK, Enum.Material.Rock),
			cylinder(18, 1.4, 1.8, ROCK_LIGHT, Enum.Material.Rock),
			block(0.4, 8, 1.8, 1.85, CRACK, Enum.Material.Slate, 3, 2, 30),
			block(0.4, 6, 1.8, 1.87, CRACK, Enum.Material.Slate, -3.5, -2.5, -50),
			ball(3, 6.5, 0.6, 5.5, ROCK, Enum.Material.Rock),
			ball(2.4, -7, 0.4, 5, ROCK_LIGHT, Enum.Material.Rock),
		},
	},
	-- Tall golden temple column on a cloud.
	CheemsGod = {
		Top = 10,
		Diameter = 14,
		Pieces = {
			cylinder(10, SINK, 1.2, CLOUD, Enum.Material.SmoothPlastic),
			ball(6, 4, 0.8, 0, CLOUD, Enum.Material.SmoothPlastic),
			ball(5.5, 1.2, 0.6, 3.8, CLOUD, Enum.Material.SmoothPlastic),
			ball(6, -3.2, 0.7, 2.4, CLOUD, Enum.Material.SmoothPlastic),
			ball(5.5, -3.2, 0.5, -2.4, CLOUD, Enum.Material.SmoothPlastic),
			ball(6, 1.2, 0.9, -3.8, CLOUD, Enum.Material.SmoothPlastic),
			cylinder(5.4, 1.2, 2.4, GOLD, Enum.Material.Foil),
			cylinder(4, 2.4, 9.2, MARBLE_GOLD, Enum.Material.Marble),
			block(0.4, 0.4, 2.6, 9, GOLD, Enum.Material.Foil, 1.95, 0),
			block(0.4, 0.4, 2.6, 9, GOLD, Enum.Material.Foil, -1.95, 0),
			block(0.4, 0.4, 2.6, 9, GOLD, Enum.Material.Foil, 0, 1.95),
			block(0.4, 0.4, 2.6, 9, GOLD, Enum.Material.Foil, 0, -1.95),
			cylinder(5, 9.2, 9.6, GOLD, Enum.Material.Foil),
			block(5.6, 5.6, 9.6, 10, GOLD_DARK, Enum.Material.Foil),
		},
	},

	-- Shibas 11-20. Each part-built platform is a simple version of its Platform_<AssetName> model (same Top).

	-- Round ship's deck with a rope rim, a treasure barrel, an open chest and a Jolly Roger.
	PirateShiba = {
		Top = 1.6,
		Diameter = 9.5,
		Pieces = {
			cylinder(8.6, SINK, 1.35, WOOD_DARK, Enum.Material.Wood),
			cylinder(8.2, 1.35, 1.6, WOOD_LIGHT, Enum.Material.WoodPlanks),
			cylinder(8.9, 1.2, 1.5, ROPE, Enum.Material.Fabric),
			cylinder(1.8, SINK, 1.3, WOOD, Enum.Material.Wood, 3, -2.6),
			ball(1.3, 3, 1.4, -2.6, GOLD, Enum.Material.Foil),
			block(1.6, 1, SINK, 0.7, WOOD_DARK, Enum.Material.Wood, -3.1, -2.4, 30),
			ball(1.1, -3.1, 0.75, -2.4, GOLD, Enum.Material.Foil),
			block(0.2, 0.2, 1.45, 6.8, WOOD_DARK, Enum.Material.Wood, 2.6, 3.3),
			block(1.9, 0.1, 5.55, 6.75, BLACK, Enum.Material.Fabric, 3.55, 3.3),
		},
	},
	-- Round hay bale with twine, a cactus and a crate.
	CowboyShiba = {
		Top = 2,
		Diameter = 10,
		Pieces = {
			cylinder(7.2, SINK, 2, HAY, Enum.Material.Fabric),
			cylinder(7.4, 0.5, 0.65, TWINE, Enum.Material.Fabric),
			cylinder(7.4, 1.3, 1.45, TWINE, Enum.Material.Fabric),
			cylinder(0.9, SINK, 3.6, CACTUS, Enum.Material.Grass, -3.4, 3.1),
			ball(0.9, -3.4, 3.6, 3.1, CACTUS, Enum.Material.Grass),
			block(1.3, 1.3, SINK, 0.85, WOOD, Enum.Material.WoodPlanks, 3, -2.9, 17),
		},
	},
	-- Planked round deck with a ring of painted shields and a tall carved prow at the back.
	VikingShiba = {
		Top = 1.5,
		Diameter = 9.5,
		Pieces = concat({
			cylinder(8.4, SINK, 1.3, WOOD_DARK, Enum.Material.Wood),
			cylinder(8, 1.3, 1.5, WOOD_LIGHT, Enum.Material.WoodPlanks),
			block(0.9, 0.9, 1.4, 8.6, WOOD_DARK, Enum.Material.Wood, -3.2, 3.6),
			block(0.8, 1.4, 8.1, 8.9, WOOD_DARK, Enum.Material.Wood, -3.2, 3.1),
		}, blockRing(10, 4.4, 1.5, 0.25, 0.05, 1.65, { RED, CREAM, BLUE, GOLD }, Enum.Material.SmoothPlastic, 18)),
	},
	-- Stack of three giant spell books with four standing rune stones.
	WizardShiba = {
		Top = 2.4,
		Diameter = 10.5,
		Pieces = concat(
			{
				block(7, 5.4, SINK, 0.8, BOOK_BLUE, Enum.Material.SmoothPlastic),
				block(6.8, 0.1, 0.1, 0.7, CREAM, Enum.Material.SmoothPlastic, 0.1, -2.72),
				block(6.4, 5, 0.8, 1.6, BOOK_PURPLE, Enum.Material.SmoothPlastic, 0, 0, 16),
				block(5.8, 4.6, 1.6, 2.4, BOOK_RED, Enum.Material.SmoothPlastic, 0, 0, -9),
			},
			blockRing(4, 4.55, 1, 0.7, SINK, 2.2, { STONE_LIGHT }, Enum.Material.Slate, 45),
			{
				ball(1.1, 2.9, 5.2, 3, RUNE, Enum.Material.Neon),
			}
		),
	},
	-- Grey moon rock with craters, a flag and a small rocket.
	AstronautShiba = {
		Top = 2,
		Diameter = 11,
		Pieces = {
			cylinder(8.4, SINK, 1.4, MOON_DARK, Enum.Material.Slate),
			cylinder(7.2, 1.4, 2, MOON, Enum.Material.Slate),
			cylinder(1.3, 2, 2.05, MOON_DARK, Enum.Material.Slate, 2.3, -1.6),
			block(0.15, 0.15, 1.8, 6.6, SILVER, Enum.Material.Metal, -2.5, 2.3),
			block(1.8, 0.1, 5.5, 6.55, WHITE, Enum.Material.Fabric, -1.6, 2.3),
			cylinder(1.2, SINK, 3.2, WHITE, Enum.Material.SmoothPlastic, 3.7, 3.1),
			ball(1.1, 3.7, 3.4, 3.1, RED, Enum.Material.SmoothPlastic),
		},
	},
	-- Steel pad with hazard stripes, a glowing ring and brass gears at the back.
	RobotShiba = {
		Top = 1.6,
		Diameter = 9.5,
		Pieces = {
			cylinder(8.4, SINK, 1.3, STEEL, Enum.Material.DiamondPlate),
			cylinder(8.7, 0.5, 0.95, HAZARD, Enum.Material.SmoothPlastic),
			cylinder(7.6, 1.3, 1.6, STEEL_DARK, Enum.Material.Metal),
			cylinder(6.4, 1.6, 1.65, CYAN, Enum.Material.Neon),
			cylinder(5.8, 1.6, 1.68, STEEL_DARK, Enum.Material.Metal),
			block(4.4, 0.5, SINK, 3.8, BRASS, Enum.Material.Metal, -0.9, 3.8),
			block(2.3, 0.45, SINK, 3.5, BRASS, Enum.Material.Metal, 2.3, 3.4, 45),
		},
	},
	-- Dark wooden base with tatami mats, a vermilion torii gate behind, a stone lantern.
	SamuraiShiba = {
		Top = 1.4,
		Diameter = 11,
		Pieces = {
			block(7.4, 7.4, SINK, 1.1, WOOD_DARK, Enum.Material.Wood),
			block(6.8, 6.8, 1.1, 1.4, TATAMI, Enum.Material.Fabric),
			cylinder(0.6, SINK, 6.8, VERMILION, Enum.Material.SmoothPlastic, -2.6, 3.2),
			cylinder(0.6, SINK, 6.8, VERMILION, Enum.Material.SmoothPlastic, 2.6, 3.2),
			block(6.6, 0.35, 5.2, 5.6, VERMILION, Enum.Material.SmoothPlastic, 0, 3.2),
			block(7, 0.5, 6.4, 6.75, VERMILION, Enum.Material.SmoothPlastic, 0, 3.2),
			block(7.4, 0.62, 6.75, 7.15, BLACK, Enum.Material.SmoothPlastic, 0, 3.2),
			cylinder(0.5, SINK, 1.3, STONE_LIGHT, Enum.Material.Slate, -3.1, -3),
			block(0.8, 0.8, 1.3, 1.85, Color3.fromRGB(255, 220, 110), Enum.Material.Neon, -3.1, -3),
			block(1.4, 1.4, 1.85, 2.2, STONE, Enum.Material.Slate, -3.1, -3, 45),
		},
	},
	-- Coffin lying on a grave with tombstones behind.
	VampireShiba = {
		Top = 2,
		Diameter = 10,
		Pieces = {
			cylinder(9.2, SINK, 0.18, SOIL, Enum.Material.Ground),
			block(3.6, 7, SINK, 1.7, COFFIN, Enum.Material.Wood),
			block(3.8, 7.2, 1.7, 2, COFFIN_LID, Enum.Material.Wood),
			block(3.9, 7.3, 1.55, 1.65, SILVER, Enum.Material.Metal),
			block(1.3, 0.4, SINK, 1.7, STONE_LIGHT, Enum.Material.Slate, -3, 3.2, -20),
			block(1.1, 0.4, SINK, 1.3, STONE_LIGHT, Enum.Material.Slate, 3.2, 2.6, 23),
			ball(0.5, -2.6, 1.1, -2.9, Color3.fromRGB(255, 140, 30), Enum.Material.Neon),
		},
	},
	-- Stepped sandstone pyramid with a gold top and two obelisks.
	PharaohShiba = {
		Top = 2.5,
		Diameter = 12,
		Pieces = {
			block(8.2, 8.2, SINK, 0.8, SAND, Enum.Material.Sandstone),
			block(6.8, 6.8, 0.8, 1.6, SAND_DARK, Enum.Material.Sandstone),
			block(5.4, 5.4, 1.6, 2.4, SAND, Enum.Material.Sandstone),
			block(4.8, 4.8, 2.3, 2.5, GOLD, Enum.Material.Foil),
			block(1, 1, SINK, 4.8, SAND, Enum.Material.Sandstone, -3.55, 3.55),
			block(1, 1, SINK, 4.8, SAND, Enum.Material.Sandstone, 3.55, 3.55),
			ball(0.9, -3.55, 5, 3.55, GOLD, Enum.Material.Foil),
			ball(0.9, 3.55, 5, 3.55, GOLD, Enum.Material.Foil),
		},
	},
	-- Dark rock under a heap of gold coins with gems and dark crags behind.
	DragonShiba = {
		Top = 2.6,
		Diameter = 10.5,
		Pieces = {
			cylinder(9.2, SINK, 1.35, ROCK_DARK, Enum.Material.Rock),
			cylinder(7.6, 1.2, 1.9, GOLD_DARK, Enum.Material.Foil),
			cylinder(5.4, 1.9, 2.35, GOLD, Enum.Material.Foil),
			cylinder(4, 2.35, 2.6, GOLD_DARK, Enum.Material.Foil),
			ball(0.6, 3.1, 2.2, 0.9, Color3.fromRGB(230, 30, 60), Enum.Material.Glass),
			ball(0.6, -1.0, 2.3, 2.6, Color3.fromRGB(40, 200, 90), Enum.Material.Glass),
			cylinder(1.6, SINK, 2.9, ROCK_DARK, Enum.Material.Rock, -2.6, 3.9),
			cylinder(1.3, SINK, 1.9, ROCK_DARK, Enum.Material.Rock, 3.9, 2.7),
		},
	},

	-- Shibas 21-30 (their models come from a separate pass; platforms keyed by the same AssetNames).

	-- Round stage with a glowing dance floor, speaker stacks and a DJ deck.
	DJShiba = {
		Top = 1.4,
		Diameter = 11,
		Pieces = {
			cylinder(9.2, SINK, 1.2, BLACK, Enum.Material.SmoothPlastic),
			cylinder(9.3, 0.85, 1.05, NEON_PINK, Enum.Material.Neon),
			cylinder(7.8, 1.2, 1.4, CYAN, Enum.Material.Neon),
			block(1.8, 1.3, SINK, 3.1, BLACK, Enum.Material.SmoothPlastic, -3.6, 2.5, 20),
			block(1.8, 1.3, SINK, 3.1, BLACK, Enum.Material.SmoothPlastic, 3.6, 2.5, -20),
			block(3.2, 1.2, 1.2, 2.5, STEEL_DARK, Enum.Material.Metal, 0, 3.55),
			ball(1.3, 0, 7.4, 3.2, SILVER, Enum.Material.Foil),
			block(0.2, 0.2, 1.3, 7.9, SILVER, Enum.Material.Metal, 0, 4.25),
		},
	},
	-- Round stone tower top with battlements and banners.
	KnightShiba = {
		Top = 2.8,
		Diameter = 9.5,
		Pieces = concat({
			cylinder(7.8, SINK, 2.4, CASTLE_DARK, Enum.Material.Cobblestone),
			cylinder(8.7, 2.4, 2.8, CASTLE, Enum.Material.Cobblestone),
			block(1.4, 0.1, 0.25, 2.15, RED, Enum.Material.Fabric, 0, -3.97),
			block(0.2, 0.2, 2.7, 11, WOOD, Enum.Material.Wood, -3.1, 2.7),
			block(0.2, 0.2, 2.7, 11, WOOD, Enum.Material.Wood, 3.1, 2.7),
		}, blockRing(10, 4, 1.3, 0.7, 2.7, 3.75, { CASTLE }, Enum.Material.Cobblestone, 18)),
	},
	-- City rooftop with a hero emblem on the facade and a water tower.
	SuperheroShiba = {
		Top = 2.6,
		Diameter = 11.5,
		Pieces = {
			block(8, 8, SINK, 2.5, FACADE, Enum.Material.Concrete),
			block(7.6, 7.6, 2.5, 2.6, ROOF, Enum.Material.Concrete),
			block(8.2, 0.3, 2.45, 3, SILVER, Enum.Material.Concrete, 0, -3.9),
			block(8.2, 0.3, 2.45, 3, SILVER, Enum.Material.Concrete, 0, 3.9),
			block(2.6, 0.2, 0.4, 1.7, RED, Enum.Material.SmoothPlastic, 0, -4.05),
			block(0.3, 0.3, 2.55, 4.25, STEEL_DARK, Enum.Material.Metal, 2.6, 2.6),
			cylinder(1.9, 4.2, 6, WOOD, Enum.Material.Wood, 2.6, 2.6),
		},
	},
	-- Ice chunk with a snow cap and crystal spikes.
	FrostShiba = {
		Top = 2.3,
		Diameter = 10.5,
		Pieces = {
			cylinder(8.4, SINK, 2, ICE, Enum.Material.Glacier),
			cylinder(7.6, 2, 2.3, SNOW, Enum.Material.Snow),
			block(0.6, 0.6, SINK, 3.6, ICE, Enum.Material.Ice, 1.6, 4.3, 30),
			block(0.5, 0.5, SINK, 2.6, ICE, Enum.Material.Ice, -0.6, 4.4, -20),
			block(0.5, 0.5, SINK, 1.8, ICE, Enum.Material.Ice, -4.3, -1.5, 15),
		},
	},
	-- Basalt rock with a lava moat and two small vents.
	MagmaShiba = {
		Top = 2.4,
		Diameter = 12.5,
		Pieces = {
			cylinder(10.4, SINK, 0.05, LAVA, Enum.Material.Neon),
			cylinder(8.4, SINK, 2.4, BASALT, Enum.Material.Basalt),
			cylinder(6.8, 2.4, 2.45, Color3.fromRGB(70, 30, 20), Enum.Material.CrackedLava),
			cylinder(2.6, SINK, 4.6, BASALT, Enum.Material.Basalt, -2.9, 3.3),
			cylinder(1, 4.6, 4.7, LAVA, Enum.Material.Neon, -2.9, 3.3),
		},
	},
	-- Hex tech pad with glowing lines under a hangar gantry.
	MechaShiba = {
		Top = 1.8,
		Diameter = 11,
		Pieces = {
			cylinder(9.2, SINK, 1.5, STEEL, Enum.Material.DiamondPlate),
			cylinder(9.3, 0.7, 1.35, HAZARD, Enum.Material.SmoothPlastic),
			cylinder(8, 1.5, 1.8, STEEL_DARK, Enum.Material.Metal),
			cylinder(7, 1.8, 1.84, CYAN, Enum.Material.Neon),
			cylinder(6.6, 1.8, 1.86, STEEL_DARK, Enum.Material.Metal),
			block(1, 1, SINK, 8, STEEL, Enum.Material.Metal, -3.5, 2.9),
			block(1, 1, SINK, 8, STEEL, Enum.Material.Metal, 3.5, 2.9),
			block(8.2, 1.1, 7.9, 8.7, STEEL_DARK, Enum.Material.Metal, 0, 2.9),
		},
	},
	-- Cloud with a golden disc and white wings at the sides.
	AngelShiba = {
		Top = 2.2,
		Diameter = 12,
		Pieces = {
			cylinder(9, SINK, 1.5, CLOUD, Enum.Material.SmoothPlastic),
			ball(3, 4.3, 0.6, 0.8, CLOUD, Enum.Material.SmoothPlastic),
			ball(3, -4.3, 0.6, 0.8, CLOUD, Enum.Material.SmoothPlastic),
			ball(2.8, 1.5, 0.5, -4, CLOUD, Enum.Material.SmoothPlastic),
			ball(2.8, -1.5, 0.5, -4, CLOUD, Enum.Material.SmoothPlastic),
			ball(2.8, 0, 0.5, 4.2, CLOUD, Enum.Material.SmoothPlastic),
			cylinder(7.4, 1.3, 2.05, GOLD, Enum.Material.Foil),
			cylinder(6.5, 2.05, 2.2, MARBLE, Enum.Material.Marble),
			block(0.3, 3.4, 2, 4.8, WHITE, Enum.Material.SmoothPlastic, 4.6, 1.4, -8),
			block(0.3, 3.4, 2, 4.8, WHITE, Enum.Material.SmoothPlastic, -4.6, 1.4, 8),
		},
	},
	-- Obsidian rock with glowing cracks, spikes, two huge horns and hellfire.
	DemonShiba = {
		Top = 2,
		Diameter = 11.5,
		Pieces = concat({
			cylinder(8.6, SINK, 2, OBSIDIAN, Enum.Material.Basalt),
			cylinder(8.9, 0.6, 0.75, HELLFIRE, Enum.Material.Neon),
			block(0.9, 0.9, 0.5, 8.8, Color3.fromRGB(110, 20, 28), Enum.Material.SmoothPlastic, -4.2, 2.8, 20),
			block(0.9, 0.9, 0.5, 8.8, Color3.fromRGB(110, 20, 28), Enum.Material.SmoothPlastic, 4.2, 2.8, -20),
		}, blockRing(9, 4.9, 0.5, 0.5, SINK, 1.4, { HELLFIRE, LAVA }, Enum.Material.Neon, 30)),
	},
	-- Celestial dais in tiers with a golden clock face on top and a giant clock standing behind.
	EternalShiba = {
		Top = 5,
		Diameter = 15,
		Pieces = {
			cylinder(13.2, SINK, 0.6, NIGHT, Enum.Material.SmoothPlastic),
			cylinder(13.6, 0.6, 0.9, GOLD, Enum.Material.Foil),
			cylinder(10.6, 0.9, 2.4, MARBLE, Enum.Material.Marble),
			cylinder(11, 2.4, 2.7, GOLD, Enum.Material.Foil),
			cylinder(8.4, 2.7, 4.75, GOLD_DARK, Enum.Material.Foil),
			cylinder(8.2, 4.75, 5, CREAM, Enum.Material.SmoothPlastic),
			block(9.4, 0.4, 6.4, 15.6, GOLD, Enum.Material.Foil, 0, 4.4),
			block(8.6, 0.5, 7.2, 14.8, NIGHT, Enum.Material.SmoothPlastic, 0, 4.4),
			block(1, 1, 0.7, 8.4, GOLD, Enum.Material.Foil, -5.2, 3.8),
			block(1, 1, 0.7, 8.4, GOLD, Enum.Material.Foil, 5.2, 3.8),
		},
	},
	-- Black hole: a wide black disc with a glowing rim, a dark vortex up to the stand and a void portal behind.
	VoidShiba = {
		Top = 6,
		Diameter = 20.5,
		Pieces = {
			cylinder(18.6, SINK, 0.3, VOID, Enum.Material.SmoothPlastic),
			cylinder(19.4, SINK, 0.1, VOID_PURPLE, Enum.Material.Neon),
			cylinder(3.2, 0.05, 2.8, VOID, Enum.Material.SmoothPlastic),
			cylinder(5.4, 2.8, 5.85, VOID, Enum.Material.SmoothPlastic),
			cylinder(7.4, 5.85, 6, VOID_PURPLE, Enum.Material.Neon),
			cylinder(7, 5.85, 6.02, VOID, Enum.Material.SmoothPlastic),
			block(10.4, 0.5, 5.8, 16.2, VOID_PURPLE, Enum.Material.Neon, 0, 5.2),
			block(9.6, 0.6, 6.6, 15.4, VOID, Enum.Material.SmoothPlastic, 0, 5.2),
		},
	},
}

-- Plain grey disc, as before the per-tier platforms.
local default: Platform = {
	Top = 0.2,
	Diameter = 8,
	Pieces = {
		cylinder(8, -0.8, 0.2, Color3.fromRGB(120, 120, 130), Enum.Material.SmoothPlastic),
	},
}

return {
	Platforms = platforms,
	Default = default,
	-- Platform models: ReplicatedStorage.Assets.<ModelPrefix><AssetName>, with a tiny part named StandMarkerName at the
	-- centre of the standing surface (hidden in the game). The model reaches ModelSink studs into the island.
	ModelPrefix = "Platform_",
	StandMarkerName = "StandPoint",
	ModelSink = 0.5,
}
