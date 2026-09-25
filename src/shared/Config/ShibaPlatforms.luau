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
