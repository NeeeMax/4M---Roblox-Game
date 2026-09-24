--!strict
-- World layout (docs/GAME_DESIGN.md → World): a big hub island in the middle with the stations (daily spin,
-- coin flip, quests, leaderboard), and one bridge per player island around it, like tycoon plots.

return {
	Hub = {
		Center = Vector3.new(0, 100, 0),
		Radius = 70,
		Thickness = 6,
		-- Stations stand on this circle, between the bridges.
		StationRadius = 42,
		Color = Color3.fromRGB(120, 200, 110),
		Name = "Hub",
	},

	Plots = {
		-- One island per player; more players than plots wait on the hub.
		Count = 5,
		-- Distance from the hub centre to each island centre. Neighbouring shooter rings must not overlap.
		Distance = 230,
	},

	Bridge = {
		Width = 12,
		Thickness = 2,
		RailHeight = 2.5,
		Color = Color3.fromRGB(160, 120, 80),
		RailColor = Color3.fromRGB(110, 80, 55),
	},

	-- Island colours per plot (the owner's name floats above the island in the same colour).
	PlotColors = {
		Color3.fromRGB(90, 190, 80),
		Color3.fromRGB(80, 170, 200),
		Color3.fromRGB(210, 170, 70),
		Color3.fromRGB(200, 110, 190),
		Color3.fromRGB(230, 120, 80),
	},
}
