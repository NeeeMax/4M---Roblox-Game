--!strict
-- Jump and run on the hub (docs/GAME_DESIGN.md → Obby): a spiral tower of platforms in the hub centre, built by
-- ObbyService. Stepping off the start pad starts the timer, reaching the top (statue) finishes it.

export type Move = {
	-- "Radial": in/out from the tower, "Tangent": back and forth along the path, "Up": up and down.
	Axis: "Radial" | "Tangent" | "Up",
	-- Full travel in studs.
	Distance: number,
	-- Seconds for one full back-and-forth.
	Period: number,
}

export type Stage = {
	-- Degrees along the spiral from the start pad (the tower turns clockwise seen from above).
	Angle: number,
	-- Top surface in studs above the hub ground.
	Height: number,
	-- Distance of the platform's centre from the hub centre (default Course.Radius).
	Radius: number?,
	-- "Block": a box, `Length` along the path × `Width` across. "Pad": a round pad, `Length` = diameter.
	Shape: "Block" | "Pad",
	Length: number,
	Width: number,
	Color: Color3,
	Move: Move?,
	-- Checkpoints count toward a valid run (see MinCheckpointShare).
	Checkpoint: boolean?,
}

local GREEN = Color3.fromRGB(95, 215, 60)
local YELLOW = Color3.fromRGB(255, 210, 40)
local ORANGE = Color3.fromRGB(255, 145, 35)
local CHECKPOINT = Color3.fromRGB(60, 200, 255)

-- Easy at the bottom, narrower and moving parts further up. Gaps are 2–5 studs, every step 2–3 studs up.
local stages: { Stage } = {
	{ Angle = 42, Height = 3, Shape = "Block", Length = 6, Width = 6, Color = GREEN },
	{ Angle = 80, Height = 6, Shape = "Block", Length = 6, Width = 6, Color = YELLOW },
	{ Angle = 117, Height = 9, Shape = "Block", Length = 5, Width = 5, Color = ORANGE },
	{ Angle = 153, Height = 11.5, Shape = "Block", Length = 5, Width = 5, Color = GREEN },
	{ Angle = 194, Height = 14, Shape = "Pad", Length = 8, Width = 8, Color = CHECKPOINT, Checkpoint = true },
	{ Angle = 234, Height = 16.5, Shape = "Block", Length = 4, Width = 4, Color = YELLOW },
	{ Angle = 269, Height = 19, Shape = "Block", Length = 3, Width = 3, Color = ORANGE },
	{ Angle = 311, Height = 21, Shape = "Block", Length = 12, Width = 2.5, Color = GREEN },
	{ Angle = 357, Height = 23.5, Shape = "Block", Length = 5, Width = 5, Color = YELLOW },
	{ Angle = 397, Height = 26, Shape = "Pad", Length = 8, Width = 8, Color = CHECKPOINT, Checkpoint = true },
	{
		Angle = 439,
		Height = 26.5,
		Shape = "Block",
		Length = 5,
		Width = 5,
		Color = ORANGE,
		Move = { Axis = "Radial", Distance = 5, Period = 4 },
	},
	{
		Angle = 478,
		Height = 29,
		Shape = "Block",
		Length = 5,
		Width = 5,
		Color = GREEN,
		Move = { Axis = "Up", Distance = 4, Period = 3.5 },
	},
	{ Angle = 517, Height = 31.5, Shape = "Block", Length = 10, Width = 1.6, Color = YELLOW },
	{ Angle = 556, Height = 34, Shape = "Block", Length = 3, Width = 3, Color = ORANGE },
	{
		Angle = 594,
		Height = 36.5,
		Shape = "Block",
		Length = 3.5,
		Width = 3.5,
		Color = GREEN,
		Move = { Axis = "Tangent", Distance = 5, Period = 4 },
	},
	{
		Angle = 632,
		Height = 39,
		Radius = 15,
		Shape = "Pad",
		Length = 6,
		Width = 6,
		Color = CHECKPOINT,
		Checkpoint = true,
	},
}

return {
	-- Seconds between two rewarded finishes per player. Set it to e.g. 20 to test the reward in Studio.
	RewardCooldown = 30 * 60,
	-- Reward = this many normal bonks' worth of Bonk Points (RewardService.Hits) …
	RewardHits = 40,
	-- … plus a 2× points boost for this many seconds.
	BoostSeconds = 5 * 60,

	-- Anti-cheat: a finish only counts after at least this many seconds …
	MinTime = 8,
	-- … and if the player passed at least this share of the checkpoints since the start.
	MinCheckpointShare = 0.5,
	-- A run is dropped after this many seconds or when the player moves this far from the hub centre.
	MaxRunTime = 10 * 60,
	LeaveRadius = 30,

	-- Top-10 fastest times board next to the start (all servers; this server's players without DataStores).
	Board = {
		Size = 10,
		RefreshInterval = 60,
		-- OrderedDataStore; values are tenths of a second, smaller is better.
		StoreName = "ObbyTimes_v1",
	},

	Course = {
		-- Where the spiral starts, in degrees clockwise from north (180 = south, facing the spawn point).
		StartAngle = 180,
		-- Default distance of the platforms from the hub centre.
		Radius = 14,
		StartPad = { Radius = 13, PadRadius = 4.5, Height = 0.8 },
		-- The tower in the middle; its top is the finish pad with the Shiba statue.
		TowerRadius = 5,
		FinishHeight = 42,
		FinishRadius = 10,
		Thickness = 1.4,
		Stages = stages,
	},
}
