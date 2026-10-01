--!strict
-- Layout of the tycoon plot on an island (src/server/World/TycoonPlot.luau, docs/decisions/0006). Pure data, no
-- requires. Angles are measured like the Shiba ring: 0 = north (-Z), then clockwise; "Bridge degrees" are relative to
-- the island's HubAngle (the bridge side, always kept free). All distances are studs from the island centre.
-- Equip slot n (1 … MaxEquipSlots) stands at HubAngle + (n - 0.5) / MaxEquipSlots × 360°, so positions never move.

return {
	-- Name of the folder under Island_<UserId> that holds everything.
	FolderName = "Tycoon",

	-- Equip slots (lanes).
	Lane = {
		-- Radius of the Shiba platforms (same as the old ring, Gameplay → Shooters.RingRadius).
		RingRadius = 56,
		PlatformDiameter = 12,
		-- Height of the platform's standing surface above the island surface.
		PlatformTop = 1.2,
		-- Level plate: beside the belt's start, sideways by PlateOffset.
		PlateRadius = 49,
		PlateOffset = 6.5,
		PlateSize = Vector3.new(6, 0.5, 4),
		-- Distance between the billboard and the top of the Shiba.
		BillboardGap = 2.5,
		BillboardDistance = 110,
		LevelHoldSeconds = 0.3,
		-- Levels bought by the second (F) level prompt.
		BigLevelStep = 10,
		PromptDistance = 11,
		-- Invisible box around a Shiba that takes the click (the model itself is visual only).
		SwingBoxSize = Vector3.new(6, 7, 6),
	},

	-- Street plot (StreetPlot): one stage per Shiba along a path that leads away from the road. Positions are in the stage
	-- frame (Config/DecorTypes): origin = the stage's middle on the path, +X right, -Z deeper, +Z toward the road.
	Street = {
		-- Depth (from the road end of the plot) where the first stage starts, and the free margin added to every stage's Area.
		FirstStageDepth = 20,
		StageMargin = 10,
		-- Stage size of a bay whose theme is missing.
		DefaultArea = Vector2.new(80, 80),
		-- The Shiba stands this far left of the path, facing it.
		ShibaX = 16,
		PlatformDiameter = 10,
		-- The click works up to this distance (studs) from the Shiba.
		ClickDistance = 24,
		-- The Bonk Intern stands this far in front of the Shiba (toward the path).
		InternDistance = 6,
		PathWidth = 12,
		PathColor = Color3.fromRGB(205, 198, 185),
		-- Floor pads: oval, with a dark base. The Shiba pad is on the path at the front of the stage, the Intern pad beside the
		-- Shiba and the decor pads in two lanes right of the path (X of each lane), PadFrontInset from the stage's ends.
		PadDiameter = 7,
		PadBaseDiameter = 8.6,
		PadHeight = 0.5,
		PadFrontInset = 12,
		AutoPad = Vector3.new(-16, 0, 11),
		DecorPadX = { 14, 26 },
		PadBillboardDistance = 140,
		-- Seconds before the same pad can be triggered again.
		PadCooldown = 1,
	},

	-- Conveyor spokes: from BeltFrom (Shiba side) to BeltTo (Mill side). Client: Belt_<n> is a Part whose LookVector
	-- points toward the Mill, Size.Z = its length and its top face is at Position.Y + Size.Y / 2.
	Belt = {
		From = 50,
		To = 12,
		Width = 3.6,
		Height = 0.7,
		-- Top of the belt above the island surface.
		Top = 0.5,
		Color = Color3.fromRGB(45, 45, 55),
		DashCount = 4,
		DashColor = Color3.fromRGB(255, 220, 90),
	},

	-- Arch frames over the belt (Config/Tycoon → Arch): radius of each, size and colours.
	Arch = {
		Radii = { 42, 34 },
		Width = 9,
		Height = 7,
		Thickness = 1,
		OwnedColors = { Color3.fromRGB(255, 200, 60), Color3.fromRGB(120, 230, 255) },
		GhostColor = Color3.fromRGB(230, 235, 255),
		GhostTransparency = 0.7,
		PromptDistance = 14,
	},

	-- Bonk Mill in the centre: three rings from the outside in (Config/Tycoon → Rings, same order).
	Mill = {
		BaseRadius = 10,
		BaseHeight = 1,
		-- Radius, bottom, top of each ring layer.
		Rings = {
			{ Radius = 9, Bottom = 1, Top = 3, Color = Color3.fromRGB(120, 200, 255) },
			{ Radius = 7, Bottom = 3, Top = 5.5, Color = Color3.fromRGB(255, 170, 70) },
			{ Radius = 5, Bottom = 5.5, Top = 8, Color = Color3.fromRGB(255, 90, 140) },
		},
		CoreRadius = 2.5,
		CoreTop = 11,
		BaseColor = Color3.fromRGB(70, 65, 85),
		CoreColor = Color3.fromRGB(255, 240, 170),
		GhostColor = Color3.fromRGB(200, 205, 225),
		GhostTransparency = 0.72,
		PromptDistance = 18,
	},

	-- Vault next to the Mill, toward the bridge.
	Vault = {
		Angle = 0,
		Radius = 18,
		PromptDistance = 10,
		Color = Color3.fromRGB(120, 75, 40),
		GoldColor = Color3.fromRGB(255, 205, 60),
	},

	-- Egg stands on the outer ring, one per zone (Config/Tycoon → Zones). Bridge degrees: all between two lanes, in
	-- the free arc opposite the bridge.
	Eggs = {
		Radius = 66,
		Angles = { 72, 108, 144, 180, 216, 252 },
		BaseDiameter = 9,
		EggSize = Vector3.new(6, 8, 6),
		PromptDistance = 12,
		HatchHoldSeconds = 0,
		-- Colour per zone (index = zone + 1).
		ZoneColors = {
			Color3.fromRGB(120, 220, 110),
			Color3.fromRGB(255, 220, 120),
			Color3.fromRGB(60, 170, 90),
			Color3.fromRGB(170, 190, 220),
			Color3.fromRGB(150, 90, 255),
			Color3.fromRGB(255, 240, 170),
		},
		LockedColor = Color3.fromRGB(35, 30, 45),
		LockedTransparency = 0.35,
	},

	-- Ascension shrine (Config/Tycoon → Ascension).
	Shrine = {
		Angle = 288,
		Radius = 74,
		Height = 9,
		HoldSeconds = 3,
		PromptDistance = 12,
	},

	-- Colours of the texts.
	Text = {
		Title = Color3.fromRGB(255, 255, 255),
		Income = Color3.fromRGB(120, 255, 140),
		Hint = Color3.fromRGB(255, 225, 120),
		Muted = Color3.fromRGB(190, 190, 205),
		Locked = Color3.fromRGB(255, 130, 130),
	},
}
