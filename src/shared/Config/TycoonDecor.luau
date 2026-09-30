--!strict
-- Shiba themes: decoration the player unlocks part by part (docs/GAME_DESIGN.md → Street, plots and buttons → "Shiba themes
-- and decor (implementation)"). Pure data, no requires. Adding a theme = adding one entry to Themes, keyed by the bay
-- number of its Shiba (bay n holds Shiba n, tier n - 1). Every part becomes the floor-pad step `Decor<bay>_<partId>`
-- (Util/TycoonSteps), needs the Shiba's bay and the previous part of the same theme, and is drawn by World/StreetPlot once
-- bought. If ReplicatedStorage.Assets has a model `Decor_<Key>_<PartId>` it is used instead of the Pieces.
--
-- Piece geometry is relative to the theme anchor: X = the plot's right, Y = up from the ground, Z = away from the road,
-- the bow of a ship points to +Z. Rotation is in degrees, applied to the piece around its own centre. A Cylinder's
-- axis is its X axis, so a standing pole uses Rotation (0, 0, 90).
-- Prices are placeholders (open): TierIncome(bay - 1) * PriceSeconds, see TycoonSteps.Price.

export type Piece = {
	Size: Vector3,
	Offset: Vector3,
	Color: Color3,
	Material: Enum.Material?,
	Shape: Enum.PartType?,
	Rotation: Vector3?,
}

export type Part = {
	-- Unique inside the theme; part of the step id and the asset name.
	Id: string,
	Name: string,
	Description: string,
	PriceSeconds: number,
	Pieces: { Piece },
}

export type Theme = {
	-- Used in the asset name Decor_<Key>_<PartId>.
	Key: string,
	Name: string,
	-- The anchor stands beside the Shiba's bay: Outward studs further from the path than the Shiba (same row depth
	-- plus Depth studs).
	Outward: number,
	Depth: number,
	-- Where the pad stands, relative to the anchor: X = further out, Z = further back.
	PadOffset: Vector3,
	Parts: { Part },
}

local WOOD = Color3.fromRGB(120, 78, 42)
local DARK_WOOD = Color3.fromRGB(85, 52, 28)
local PLANK = Color3.fromRGB(170, 125, 75)
local IRON = Color3.fromRGB(45, 45, 52)
local GOLD = Color3.fromRGB(255, 205, 60)
local CANVAS = Color3.fromRGB(245, 240, 225)

local PIRATE: Theme = {
	Key = "Pirate",
	Name = "Pirate Ship",
	Outward = 11,
	Depth = 0,
	PadOffset = Vector3.new(0, 0, -12),
	Parts = {
		{
			Id = "Hull",
			Name = "Ship's Hull",
			Description = "the pirate ship's hull",
			PriceSeconds = 30,
			Pieces = {
				{
					Size = Vector3.new(7, 3, 13),
					Offset = Vector3.new(0, 1.5, 0),
					Color = DARK_WOOD,
					Material = Enum.Material.Wood,
				},
				{
					Size = Vector3.new(9, 2, 13),
					Offset = Vector3.new(0, 4, 0),
					Color = WOOD,
					Material = Enum.Material.Wood,
				},
				{
					Size = Vector3.new(9, 4, 4),
					Offset = Vector3.new(0, 3, 8.5),
					Color = WOOD,
					Material = Enum.Material.Wood,
					Shape = Enum.PartType.Wedge,
					Rotation = Vector3.new(0, 180, 0),
				},
				{
					Size = Vector3.new(9, 2.5, 3),
					Offset = Vector3.new(0, 6.25, -5),
					Color = WOOD,
					Material = Enum.Material.Wood,
				},
				{
					Size = Vector3.new(8, 0.3, 10),
					Offset = Vector3.new(0, 5.15, 1),
					Color = PLANK,
					Material = Enum.Material.WoodPlanks,
				},
			},
		},
		{
			Id = "Mast",
			Name = "Mast",
			Description = "a tall mast",
			PriceSeconds = 20,
			Pieces = {
				{
					Size = Vector3.new(14, 1, 1),
					Offset = Vector3.new(0, 12.3, 1),
					Color = DARK_WOOD,
					Material = Enum.Material.Wood,
					Shape = Enum.PartType.Cylinder,
					Rotation = Vector3.new(0, 0, 90),
				},
				{
					Size = Vector3.new(8.5, 0.6, 0.6),
					Offset = Vector3.new(0, 17, 1),
					Color = DARK_WOOD,
					Material = Enum.Material.Wood,
					Shape = Enum.PartType.Cylinder,
				},
			},
		},
		{
			Id = "Sail",
			Name = "Main Sail",
			Description = "a big white sail",
			PriceSeconds = 25,
			Pieces = {
				{
					Size = Vector3.new(7.5, 8.5, 0.3),
					Offset = Vector3.new(0, 12.6, 1.6),
					Color = CANVAS,
					Material = Enum.Material.Fabric,
				},
			},
		},
		{
			Id = "Flag",
			Name = "Jolly Roger",
			Description = "a pirate flag on top",
			PriceSeconds = 10,
			Pieces = {
				{
					Size = Vector3.new(0.2, 2.2, 4),
					Offset = Vector3.new(0, 18.8, 3),
					Color = Color3.fromRGB(25, 25, 30),
					Material = Enum.Material.Fabric,
				},
				{
					Size = Vector3.new(0.3, 0.9, 0.9),
					Offset = Vector3.new(0, 18.9, 3),
					Color = Color3.fromRGB(245, 245, 245),
					Shape = Enum.PartType.Ball,
				},
			},
		},
		{
			Id = "Cannons",
			Name = "Cannons",
			Description = "four cannons on deck",
			PriceSeconds = 35,
			Pieces = {
				{
					Size = Vector3.new(3.4, 1.3, 1.3),
					Offset = Vector3.new(4.7, 5.9, -1.5),
					Color = IRON,
					Material = Enum.Material.Metal,
					Shape = Enum.PartType.Cylinder,
				},
				{
					Size = Vector3.new(3.4, 1.3, 1.3),
					Offset = Vector3.new(4.7, 5.9, 3.5),
					Color = IRON,
					Material = Enum.Material.Metal,
					Shape = Enum.PartType.Cylinder,
				},
				{
					Size = Vector3.new(3.4, 1.3, 1.3),
					Offset = Vector3.new(-4.7, 5.9, -1.5),
					Color = IRON,
					Material = Enum.Material.Metal,
					Shape = Enum.PartType.Cylinder,
				},
				{
					Size = Vector3.new(3.4, 1.3, 1.3),
					Offset = Vector3.new(-4.7, 5.9, 3.5),
					Color = IRON,
					Material = Enum.Material.Metal,
					Shape = Enum.PartType.Cylinder,
				},
			},
		},
		{
			Id = "Wheel",
			Name = "Ship's Wheel",
			Description = "to steer the ship",
			PriceSeconds = 20,
			Pieces = {
				{
					Size = Vector3.new(0.6, 2, 0.6),
					Offset = Vector3.new(0, 8.4, -3),
					Color = DARK_WOOD,
					Material = Enum.Material.Wood,
				},
				{
					Size = Vector3.new(0.4, 3.2, 3.2),
					Offset = Vector3.new(0, 10, -3),
					Color = WOOD,
					Material = Enum.Material.Wood,
					Shape = Enum.PartType.Cylinder,
					Rotation = Vector3.new(0, 90, 0),
				},
			},
		},
		{
			Id = "Chest",
			Name = "Treasure Chest",
			Description = "full of gold",
			PriceSeconds = 40,
			Pieces = {
				{
					Size = Vector3.new(2.6, 1.4, 1.8),
					Offset = Vector3.new(2.3, 5.8, 4),
					Color = WOOD,
					Material = Enum.Material.Wood,
				},
				{
					Size = Vector3.new(2.6, 1.8, 1.8),
					Offset = Vector3.new(2.3, 6.5, 4),
					Color = DARK_WOOD,
					Material = Enum.Material.Wood,
					Shape = Enum.PartType.Cylinder,
				},
				{
					Size = Vector3.new(1.8, 0.3, 1.2),
					Offset = Vector3.new(2.3, 6.6, 4),
					Color = GOLD,
					Material = Enum.Material.Metal,
				},
			},
		},
	},
}

return {
	-- Themes by bay number (the Shiba the theme belongs to). Only these bays have decor.
	Themes = {
		[8] = PIRATE,
	} :: { [number]: Theme },
}
