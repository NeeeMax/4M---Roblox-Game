--!strict
-- Automation look and tuning (docs/GAME_DESIGN.md → Automation): where the Bonk Basket stands, how the Bonk Intern
-- looks and moves, and the client catch effects. Economy numbers (catch chance, payout, walk speed, names) live in
-- Config/EconomyConfig → Automation, not here. Server: AutomationService, client: AutomationController.

return {
	-- Names the client uses to find the models inside Workspace.Islands.Island_<UserId>.
	BasketName = "Prop_Basket",
	InternName = "BonkIntern",

	Basket = {
		-- Where it stands: this many degrees clockwise from the bridge direction (island.HubAngle), just outside the
		-- field border, `Gap` studs from it. 150° keeps it off the bridge path and in front of the trophy row
		-- (trophies stand FieldRadius + 12 behind the field; even the level-6 basket ends ~1 stud before their pedestals).
		AngleDegrees = 150,
		Gap = 0.6,
		-- Height of the basket at level 1, + per level above 1 (it grows a little).
		Height = 3.6,
		HeightPerLevel = 0.3,
		-- Width = Height × WidthRatio; the body is BodyShare of the height (the handle arches over the rest). Caught
		-- sticks fly into the opening at the top of the body.
		WidthRatio = 1.25,
		BodyShare = 0.6,
		-- Rim colour per level (level 1 = plain wicker).
		RimColors = {
			Color3.fromRGB(150, 100, 55),
			Color3.fromRGB(90, 190, 90),
			Color3.fromRGB(70, 150, 255),
			Color3.fromRGB(180, 90, 255),
			Color3.fromRGB(255, 150, 40),
			Color3.fromRGB(255, 215, 60),
		},
		-- The basket takes a stick this many seconds after it stopped being collectable, so a hand catch reported
		-- right at the end of the window (network delay) still wins. CatchDelay + CheckInterval + ping must stay below
		-- Gameplay.Projectiles.LandingFadeTime (0.6 s), or the stick is no longer drawn when the client hears of the
		-- catch (it then only gets the sparkles and the popup, no flight into the basket).
		CatchDelay = 0.2,
		-- How often the server checks for sticks the basket can take.
		CheckInterval = 0.15,
	},

	Intern = {
		-- How often the server picks a target and checks catches (a few players × this is cheap).
		TickInterval = 0.2,
		-- Gets bonked when the stick is within projectile radius + CatchPadding of its root.
		CatchPadding = 3,
		-- Path samples between two ticks for the catch check (fast sticks can't slip through).
		CatchSampleStep = 0.05,
		-- The player gets first dibs: the intern ignores sticks within this distance of the player's character.
		PlayerDibsRadius = 12,
		-- Keeps inside this radius from the island centre (inside the Shiba ring).
		MaxRoamRadius = 36,
		-- Where it waits without a target: this far from the centre, toward the basket.
		IdleDistance = 14,
		-- After a bonk it stands dazed for this long (the client wobble plays meanwhile).
		StunTime = 0.9,
		-- A new target must be this many "score studs" better than the current one to switch (no dithering).
		TargetStickiness = 8,
		-- Root height above the island surface (R6 proportions: legs 2, torso 2, head 1.2 = 5.2 studs tall).
		RootHeight = 3,
		-- Turn and acceleration feel of the physics movers.
		TurnResponsiveness = 25,
		MoveResponsiveness = 60,
		-- Put back at the idle spot if it ends up this far below the island surface.
		FallBelow = 10,
		SkinColor = Color3.fromRGB(255, 205, 160),
		-- Per level: shirt, trousers.
		ShirtColors = {
			Color3.fromRGB(90, 200, 120),
			Color3.fromRGB(255, 140, 50),
			Color3.fromRGB(70, 140, 255),
			Color3.fromRGB(160, 90, 230),
			Color3.fromRGB(245, 245, 245),
			Color3.fromRGB(30, 30, 38),
		},
		PantsColors = {
			Color3.fromRGB(60, 80, 140),
			Color3.fromRGB(60, 80, 140),
			Color3.fromRGB(50, 55, 70),
			Color3.fromRGB(50, 55, 70),
			Color3.fromRGB(35, 35, 45),
			Color3.fromRGB(25, 25, 32),
		},
		NameColor = Color3.fromRGB(90, 230, 170),
		-- Accessories: hard hat from this level (until the crown), tie from TieFromLevel, crown at CrownFromLevel.
		HardHatFromLevel = 2,
		TieFromLevel = 5,
		CrownFromLevel = 6,
		HardHatColor = Color3.fromRGB(255, 210, 40),
		TieColor = Color3.fromRGB(215, 40, 50),
		CeoTieColor = Color3.fromRGB(255, 200, 40),
		CrownColor = Color3.fromRGB(255, 200, 40),
		-- Motor6D names (the client swings them while walking and tips the body over on a bonk).
		Joints = {
			Waist = "Waist",
			Neck = "Neck",
			LeftShoulder = "LeftShoulder",
			RightShoulder = "RightShoulder",
			LeftHip = "LeftHip",
			RightHip = "RightHip",
		},
	},

	-- Client effects (AutomationController).
	Effects = {
		-- Coin popup "+B$ X" above the basket / intern.
		PopupTime = 1.3,
		PopupRise = 3,
		PopupColor = Color3.fromRGB(255, 225, 90),
		-- A basket catch: the stick flies from where it lay into the basket over this arc.
		BasketFlyTime = 0.55,
		BasketArcHeight = 7,
		BasketFlyEndScale = 0.6,
		BasketSparkles = 12,
		-- Walk animation: limb swing amplitude (degrees) and steps per stud walked.
		WalkSwingDegrees = 35,
		StepsPerStud = 0.35,
		-- A bonk on the intern: it tips over and wobbles back up.
		WobbleTime = 0.9,
		WobbleDegrees = 55,
		BonkStars = 10,
		StarColor = Color3.fromRGB(255, 230, 90),
		-- The caught stick bounces off the intern's head and fades.
		BounceOffTime = 0.45,
		-- Speech bubble with a random line.
		BubbleTime = 1.7,
		VoiceLines = {
			"OW!",
			"Worth it!",
			"My pension!",
			"Bonk accepted.",
			"Is this in my contract?",
			"Again!",
			"Right in the career!",
			"I felt that in my resume.",
			"Overtime bonk!",
			"Tell HR I'm fine.",
			"Ten out of ten.",
			"Bonk received. Thanks!",
		},
		-- At most this many flying sticks at once (extra catches only get the popup).
		MaxFlights = 6,
	},
}
