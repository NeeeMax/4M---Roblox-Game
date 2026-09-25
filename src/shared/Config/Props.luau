--!strict
-- World props (PropService): trees, lamps, rocks, clouds, hub machines, upgrade stands, trophies …
-- Models: ReplicatedStorage.Assets.<name> (assets/README.md → Props, built by assets/models/build_props.py).
-- Without a model PropService builds a placeholder from parts.

export type Light = {
	Range: number,
	Brightness: number,
	Color: Color3,
}

return {
	-- Studio only: a pink outline and a "MODEL: <name>" label on every placeholder. Off by default; missing
	-- models are listed in Output instead (ReportMissing).
	ShowPlaceholderMarkers = false,
	-- Prints one Output warning listing the props that still use a placeholder (again for names seen later).
	ReportMissing = true,

	-- Props whose model hangs down from the given point (its top sits there) instead of standing on it.
	Hanging = {
		Prop_IslandRock = true,
	} :: { [string]: boolean },
	-- Props you walk through (no collisions), like their placeholders.
	NoCollide = {
		Prop_Flowers = true,
		Prop_Cloud = true,
	} :: { [string]: boolean },

	-- Parts of a model named like this glow (Neon, no collisions); the first one also holds the prop's light.
	GlowPartName = "Glow",
	-- Lights put into a model's glow part (the placeholder lamp has the same light in its bulb).
	Lights = {
		Prop_Lamp = { Range = 18, Brightness = 1.5, Color = Color3.fromRGB(255, 210, 150) },
	} :: { [string]: Light },
}
