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
	-- Where the floor pad of this part stands (stage frame, X and Z): where the prop will appear, so the player buys it on the
	-- spot. Optional; without it the pad stands in one of two lanes on the path (old themes).
	Pad: Vector2?,
	-- Optional: degrees, turns the whole part (pieces, model, colliders) around the vertical axis through the centre of the union box
	-- of its pieces (positive = counter-clockwise seen from above, like CFrame.Angles(0, yaw, 0) in the stage frame). The piece
	-- offsets and rotations are written unyawed; the layout rules (Area, solid, walkway, pads) apply to the turned part.
	Yaw: number?,
	-- Optional: uniform scale (0.3 to 3, default 1) of the whole part (pieces, model, colliders) about the centre of the union box of
	-- its pieces. Applied first, then Yaw (about the same centre), then Nudge. The layout rules apply to the scaled part.
	Scale: number?,
	-- Optional: offset of the whole part in the stage frame, in UNSCALED theme units (multiplied by StageScale like every other
	-- coordinate), applied after Scale and Yaw (not turned by Yaw). Y = lift above the floor. The part's Pad stays where it is.
	-- Normally filled in by pasting the output of docs/tools/studio_tuner.luau (see docs/TUNING.md).
	Nudge: Vector3?,
	-- Optional: once this part is bought, the Shiba of the theme pays this many times more cash per hit and per second (1 to 2;
	-- the bonuses of all bought parts multiply, the whole theme at most 8). No visual effect is spawned for it; the pad text names it.
	RewardMult: number?,
	-- Price = TierIncome(bay - 1) * PriceSeconds (placeholders, calibrated by the economy simulation).
	PriceSeconds: number,
	Pieces: { Piece },
}

-- Where the Shiba stands and which way it faces. Facing is a yaw in degrees in the stage frame: 0 = +X (to the right), 90 = -Z
-- (deeper into the plot), 180 = -X, 270 = +Z (toward the road). The hit zone, the Bonk Intern and the player stand in front.
export type ShibaSpot = {
	Position: Vector2,
	Facing: number,
}

-- A theme belongs to the Shiba of bay n (Shiba n, tier n - 1).
--
-- STAGE FRAME (all Offsets): origin = the middle of the Shiba's stage on the path's centre line (on the ground); +X = to the
-- right when facing away from the road, -Z = deeper into the plot (away from the road), +Z = toward the road, +Y = up.
-- The Shiba stands at (-16, 0, 0) on a platform of radius 5, facing +X (the path). The Bonk Intern stands at (-10, 0, 0).
-- (Themes with a Shiba spot and a Path of their own use those instead.) Keep these free: the walkway, the Shiba platform, the
-- area in front of the Shiba and the Intern spot. Props taller than 0.6 studs are solid: the player cannot walk through them. The stage is
-- Area.X wide (X from -Area.X/2 to Area.X/2) and Area.Y deep (Z from -Area.Y/2 to Area.Y/2); nothing may stick out of it.
export type Theme = {
	-- Used in the optional asset name Decor_<Key>_<PartId>: letters and digits only.
	Key: string,
	Name: string,
	Area: Vector2,
	-- Optional (defaults give the old straight layout): where the Shiba stands (default (-16, 0) facing +X), the walkway as a
	-- polyline of waypoints in the stage frame (default a straight line along X = 0; it has to start at (0, Area.Y / 2) and end
	-- at (0, -Area.Y / 2) so neighbouring stages join), and where the pads of the Shiba itself and of its Bonk Intern stand.
	Shiba: ShibaSpot?,
	Path: { Vector2 }?,
	BayPad: Vector2?,
	AutoPad: Vector2?,
	-- In pad order: 10 parts for bays 1 to 3, 15 for 4 to 8, 20 for 9 to 14, 25 for 15 to 21, 30 for 22 to 30. The parts are
	-- bought in TWO parallel chains (odd and even parts), so parts 1 and 2 are available first, then 3 and 4, and so on.
	Parts: { Part },
}

return {}
