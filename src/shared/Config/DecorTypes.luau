--!strict
-- Types of the Shiba themes (Config/TycoonDecor and Config/DecorThemesA/B/C). Pure types, no values.

export type Piece = {
	Size: Vector3,
	-- Position in the STAGE frame (see below).
	Offset: Vector3,
	Color: Color3,
	Material: Enum.Material?,
	Shape: Enum.PartType?,
	-- Degrees, applied to the piece around its own centre. A Cylinder's axis is its X axis, so a standing pole uses
	-- Rotation (0, 0, 90).
	Rotation: Vector3?,
}

-- One decor pad: what appears on the plot when it is bought.
export type Part = {
	-- Unique inside the theme; part of the step id `Decor<bay>_<Id>` and of the optional asset name.
	Id: string,
	Name: string,
	Description: string,
	-- Price = TierIncome(bay - 1) * PriceSeconds (placeholders, calibrated by the economy simulation).
	PriceSeconds: number,
	Pieces: { Piece },
}

-- A theme belongs to the Shiba of bay n (Shiba n, tier n - 1).
--
-- STAGE FRAME (all Offsets): origin = the middle of the Shiba's stage on the path's centre line (on the ground); +X = to the
-- right when facing away from the road, -Z = deeper into the plot (away from the road), +Z = toward the road, +Y = up.
-- The Shiba stands at (-16, 0, 0) on a platform of radius 5, facing +X (the path). The Bonk Intern stands at (-10, 0, 0).
-- Keep these free: the path |X| < 7 over the whole stage depth, the Shiba platform, and the Intern spot. The stage is
-- Area.X wide (X from -Area.X/2 to Area.X/2) and Area.Y deep (Z from -Area.Y/2 to Area.Y/2); nothing may stick out of it.
export type Theme = {
	-- Used in the optional asset name Decor_<Key>_<PartId>: letters and digits only.
	Key: string,
	Name: string,
	Area: Vector2,
	-- In pad order: 10 parts for bays 1 to 3, 15 for 4 to 8, 20 for 9 to 14, 25 for 15 to 21, 30 for 22 to 30. The parts are
	-- bought in TWO parallel chains (odd and even parts), so parts 1 and 2 are available first, then 3 and 4, and so on.
	Parts: { Part },
}

return {}
