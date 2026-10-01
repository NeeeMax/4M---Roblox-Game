--!strict
-- The street (docs/GAME_DESIGN.md → Street, plots and buttons): one straight road along X with 10 plots, 5 on each side,
-- mirrored, facing the road. Pure data; the world is built by Services/StreetService when Config/Features.Street is on.
-- Coordinates: the road runs along X, the plots extend along +Z (right side) and -Z (left side) away from it.

return {
	-- Centre of the road's surface. Far away from the old hub island (World.Hub) so both can exist while the flag is off.
	Origin = Vector3.new(1500, 100, 0),

	-- 10 plots: slot 1, 3, 5 … on the left (-Z), slot 2, 4, 6 … on the right (+Z); a pair shares the same X.
	PlotCount = 10,
	PlotsPerSide = 5,
	-- Distance between neighbouring plot centres along the road.
	PlotPitch = 210,
	-- A plot is long and narrow: it grows backward (away from the road) as the player progresses.
	PlotWidth = 200,
	PlotDepth = 2400,
	PlotThickness = 4,

	Road = {
		Width = 28,
		Thickness = 2,
		-- Extra road beyond the first and last plot on each end.
		Margin = 30,
		Color = Color3.fromRGB(45, 45, 52),
		DashColor = Color3.fromRGB(240, 200, 60),
		DashLength = 6,
		DashGap = 8,
		SidewalkWidth = 5,
		SidewalkColor = Color3.fromRGB(190, 190, 195),
	},

	-- Character spawn on the road in front of the plot: this far from the road centre (towards the owner's side).
	SpawnOffset = 7,
	SpawnHeight = 4,
	-- Requests from the client (swing, vault, …) are accepted this far outside the plot's rectangle (studs) and up to
	-- ReachHeight above or below its surface.
	ReachMargin = 30,
	ReachHeight = 60,
	-- Below this height the character is put back on the street.
	FallOffY = 50,
	FallCheckInterval = 0.5,

	Plot = {
		GroundColor = Color3.fromRGB(95, 185, 85),
		-- Entrance mat in the plot's own colour (World.PlotColors).
		EntranceDepth = 10,
		SignHeight = 9,
		SignSize = Vector3.new(14, 3.4, 0.5),
		FreeText = "Free Plot",
	},
}
