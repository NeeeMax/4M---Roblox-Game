--!strict
-- The drop zone's look (docs/GAME_DESIGN.md → World → Field look): painted target rings, the paw emblem and the
-- "GET BONKED" lettering in the sand, sand patches and pebbles, the rope border with posts and bunting, mini BONK
-- signs, small beach props round the edge, soft lights and a faint sand glitter. IslandService builds it once per
-- plot. Everything is visual only: no collisions, no queries, no touches, so it never blocks walking, sticks
-- (projectiles fly on computed paths) or the landing ring.
--
-- Angles like Config/Stations: degrees clockwise (seen from above) from the direction toward the bridge, radii in
-- studs from the island centre. Keep decor out of the bridge gap (−15 … 15), the Bonk Basket / Bonk Intern (150) and
-- the trophy row behind the field (180 ± 25); the landing ring and the sticks must stay the clearest thing on the
-- field, so the paint is soft and flat and the props stand outside the field.

export type Ring = {
	-- Inner radius of the painted band and its width (studs).
	Radius: number,
	Width: number,
	Color: Color3,
	Transparency: number,
}

export type Blob = {
	-- Canvas offset from the field centre: X to the right, Y toward the far side (seen from the field centre looking
	-- at the bridge, the bridge is "up" = negative Y).
	X: number,
	Y: number,
	Width: number,
	Height: number,
	Rotation: number,
}

export type Lettering = {
	Text: string,
	-- Centre of the text on the canvas (same axes as Blob) and its box.
	X: number,
	Y: number,
	Width: number,
	Height: number,
	-- Degrees; 0 reads upright for someone standing in the field centre looking at the bridge.
	Rotation: number,
}

export type EdgeProp = {
	Name: string,
	Angle: number,
	Radius: number,
	Height: number,
	-- Extra turn in degrees (the prop's front faces the field centre at 0).
	Yaw: number,
}

return {
	-- The paint lies on a SurfaceGui on a flat invisible plate just above the sand: no stacked parts, so nothing can
	-- flicker (z-fighting), and the sand texture shows through the half-transparent paint. The landing ring
	-- (Gameplay.LandingRing.GroundOffset) floats above the plate.
	Paint = {
		-- Plate top above the field's top (the field's top is 0.05 above the island surface).
		Lift = 0.04,
		PixelsPerStud = 16,
		-- The whole canvas turned by this many degrees. The canvas top should point at the bridge (the plate faces it);
		-- if "GET BONKED" does not read upright from the field centre looking at the bridge, try 180 (or 90 / 270).
		CanvasRotation = 0,
		-- Painted bands (outlined circles; later entries draw over earlier ones). The landing rings are warm (tier
		-- colour mixed toward white: tan, cream, red, pink, gold), so the target lines are a cool teal and the middle
		-- band a soft mint: brown sticks, white and warm rings all stay clearly apart from the paint.
		Rings = {
			-- The mint middle band, the teal target lines (bullseye rim, 12, 20, 28), the orange edge curb.
			{ Radius = 12, Width = 8, Color = Color3.fromRGB(150, 210, 215), Transparency = 0.62 },
			{ Radius = 6.2, Width = 0.5, Color = Color3.fromRGB(60, 165, 200), Transparency = 0.35 },
			{ Radius = 12, Width = 0.5, Color = Color3.fromRGB(60, 165, 200), Transparency = 0.45 },
			{ Radius = 20, Width = 0.5, Color = Color3.fromRGB(60, 165, 200), Transparency = 0.45 },
			{ Radius = 27.6, Width = 0.55, Color = Color3.fromRGB(60, 165, 200), Transparency = 0.4 },
			{ Radius = 29.1, Width = 0.9, Color = Color3.fromRGB(255, 176, 70), Transparency = 0.3 },
		} :: { Ring },
		-- The bullseye disc and the paw print on it.
		Bullseye = { Radius = 6.2, Color = Color3.fromRGB(95, 190, 215), Transparency = 0.5 },
		PawColor = Color3.fromRGB(255, 250, 235),
		PawTransparency = 0.1,
		Paw = {
			{ X = 0, Y = 1.25, Width = 5.3, Height = 4.5, Rotation = 0 },
			{ X = -3.15, Y = -2.2, Width = 1.85, Height = 2.4, Rotation = -25 },
			{ X = -1.1, Y = -3.7, Width = 1.95, Height = 2.6, Rotation = -8 },
			{ X = 1.1, Y = -3.7, Width = 1.95, Height = 2.6, Rotation = 8 },
			{ X = 3.15, Y = -2.2, Width = 1.85, Height = 2.4, Rotation = 25 },
		} :: { Blob },
		-- Lettering in the tinted middle band, reading upright from the field centre.
		LetteringColor = Color3.fromRGB(255, 132, 48),
		LetteringStroke = Color3.fromRGB(255, 250, 235),
		LetteringTransparency = 0.12,
		Lettering = {
			{ Text = "GET BONKED", X = 0, Y = -16, Width = 22, Height = 5, Rotation = 0 },
			{ Text = "BONK ZONE", X = 0, Y = 16, Width = 20, Height = 4.6, Rotation = 180 },
		} :: { Lettering },
		-- Darker and lighter sand patches (rounded blobs) and pebbles, placed at random per plot (seeded, so every
		-- plot keeps its look). Patches stay inside PatchRadius, pebbles inside PebbleRadius.
		Patches = {
			Count = 9,
			PatchRadius = 26,
			Size = { 3, 7 },
			Aspect = { 0.45, 0.8 },
			Colors = { Color3.fromRGB(205, 175, 115), Color3.fromRGB(250, 236, 196) },
			Transparency = 0.6,
			Pebbles = 22,
			PebbleRadius = 28.5,
			PebbleSize = { 0.3, 0.7 },
			PebbleColors = {
				Color3.fromRGB(175, 150, 120),
				Color3.fromRGB(245, 240, 230),
				Color3.fromRGB(255, 175, 160),
			},
			PebbleTransparency = 0.25,
		},
	},

	-- Rope border just outside the field: wooden posts with coloured caps, a sagging rope between them and a string of
	-- pennants on every span. Arcs of degrees (the gaps are the bridge side and the basket).
	Border = {
		Radius = 31,
		Arcs = { { 15, 138 }, { 162, 345 } },
		-- Every span is at most this many degrees (posts are spread evenly per arc).
		MaxSpanDegrees = 27,
		PostHeight = 2.3,
		PostWidth = 0.45,
		PostColor = Color3.fromRGB(150, 105, 65),
		CapSize = 0.75,
		CapColors = {
			Color3.fromRGB(255, 140, 60),
			Color3.fromRGB(255, 210, 60),
			Color3.fromRGB(80, 200, 220),
			Color3.fromRGB(255, 110, 150),
		},
		RopeHeight = 1.85,
		RopeSag = 0.55,
		RopeWidth = 0.2,
		RopeColor = Color3.fromRGB(235, 215, 175),
		-- Pennants hang from the rope at these fractions of every span.
		FlagSpots = { 1 / 3, 2 / 3 },
		FlagSize = Vector2.new(1.1, 1.25),
		FlagColors = {
			Color3.fromRGB(255, 90, 80),
			Color3.fromRGB(255, 205, 60),
			Color3.fromRGB(70, 185, 255),
			Color3.fromRGB(120, 220, 110),
			Color3.fromRGB(255, 140, 200),
		},
		-- Warm lights in the caps of every Nth post (soft, no shadows).
		LightEvery = 3,
		LightRange = 11,
		LightBrightness = 0.7,
		LightColor = Color3.fromRGB(255, 205, 140),
	},

	-- Mini signs hung on border posts (post number, counted from the first arc's first post, 1-based).
	Signs = {
		BoardSize = Vector3.new(2.6, 1.15, 0.18),
		BoardHeight = 1.05,
		BoardColor = Color3.fromRGB(255, 245, 225),
		TextColor = Color3.fromRGB(255, 110, 50),
		Posts = {
			{ Post = 3, Text = "BONK!" },
			{ Post = 11, Text = "BONK ZONE" },
			{ Post = 13, Text = "CATCH!" },
		},
	},

	-- Small beach props just outside the rope (PropService; placeholders until the models are imported). All of
	-- them are in Config/Props → NoCollide.
	EdgeProps = {
		{ Name = "Prop_Sandcastle", Angle = 55, Radius = 35, Height = 4, Yaw = 0 },
		{ Name = "Prop_BeachBall", Angle = 98, Radius = 33.6, Height = 2.3, Yaw = 30 },
		{ Name = "Prop_BeachUmbrella", Angle = 114, Radius = 36.5, Height = 6.5, Yaw = 25 },
		{ Name = "Prop_BucketSpade", Angle = 243, Radius = 34, Height = 2.5, Yaw = -20 },
		{ Name = "Prop_BoneToy", Angle = 28, Radius = 33.2, Height = 0.85, Yaw = 60 },
		{ Name = "Prop_BoneToy", Angle = 300, Radius = 33.8, Height = 0.85, Yaw = -35 },
		{ Name = "Prop_GrassTuft", Angle = 78, Radius = 32.6, Height = 1.5, Yaw = 0 },
		{ Name = "Prop_GrassTuft", Angle = 255, Radius = 33, Height = 1.4, Yaw = 40 },
		{ Name = "Prop_GrassTuft", Angle = 327, Radius = 32.8, Height = 1.6, Yaw = 80 },
	} :: { EdgeProp },

	-- A faint glitter rising from the sand (one emitter per field).
	Sparkles = {
		Rate = 3,
		Lifetime = { 1.4, 2.4 },
		Speed = { 0.4, 1 },
		Size = 0.28,
		Color = Color3.fromRGB(255, 240, 190),
		LightEmission = 0.6,
		Texture = "rbxasset://textures/particles/sparkles_main.dds",
	},
}
