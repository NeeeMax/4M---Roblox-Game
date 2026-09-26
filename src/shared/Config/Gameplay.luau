--!strict
-- World, shooter, projectile, hit and bonk-effect tuning (docs/GAME_DESIGN.md). Distances in studs, times in seconds.

local EconomyConfig = require(script.Parent.EconomyConfig)

return {
	Island = {
		-- Names the client relies on to find its own island: Workspace.<FolderName>.<ModelPrefix><UserId>.Projectiles
		FolderName = "Islands",
		ModelPrefix = "Island_",
		SurfaceY = 100,
		-- The whole island: the Shibas stand on it, the field is in the middle. Sticks bounce anywhere on it.
		Radius = 80,
		Thickness = 6,
		-- The field in the middle (sand with painted target rings and a rope border, Config/FieldDecor). Shots land
		-- inside TargetRadius.
		FieldRadius = 30,
		TargetRadius = 28,
		-- The field's sand top is this far above the island surface (the paint plate and the landing ring float
		-- above it).
		FieldTop = 0.05,
		-- Room kept for the rope border round the field (Config/FieldDecor → Border); the Bonk Basket stands outside it.
		BorderWidth = 2,
		-- Below this height the character is put back on its island (or the hub).
		FallOffY = 50,
		-- Shooters only fire while the owner is within this distance of their island's centre (not on the hub).
		ActiveDistance = 80,
		SpawnHeight = 4,
		FallCheckInterval = 0.5,
	},

	Shooters = {
		RingRadius = 56,
		-- Each tier stands on its own platform (Config/ShibaPlatforms). Its top is at least this far above the island
		-- surface (equal heights flicker: z-fighting); the Shiba stands on it and throws from there.
		PlatformLift = 0.2,
		-- Invisible wall (a cylinder around platform and Shiba) so players can't walk through a Shiba: platform
		-- Diameter + 2 × Padding wide, platform Top + Shiba height + ExtraHeight tall. It only blocks characters:
		-- CanQuery and CanTouch are off, and projectiles fly on computed paths.
		Barrier = {
			Padding = 0.5,
			ExtraHeight = 6,
			-- It starts this far under the island surface, so there is no gap at its foot.
			Sink = 0.5,
		},
		-- Stick density cap: the whole ring throws at most this many sticks per second (Shibas take turns, so each
		-- Shiba throws every Shibas / MaxThrowsPerSecond seconds when capped). Above the cap every stick carries the
		-- value of natural ÷ capped throws (ValueMultiplier, "×N" tag on the stick), so income is unchanged. Defined
		-- in Config/EconomyConfig → StickDensity (the pricing model needs it); the StickStorm event raises it by
		-- Events.StickStorm.MaxThrowsMultiplier.
		MaxThrowsPerSecond = EconomyConfig.StickDensity.MaxThrowsPerSecond,
		-- The shooter turns toward its target this long before firing.
		AimTime = 0.5,
		-- Delay before a freshly placed ring of shooters fires for the first time.
		FirstShotDelay = 1,
		-- Anti-farm: the whole path (flight + bounces) must stay at least projectile radius + this far away from
		-- where the player stands at fire time, so standing still never gets hit.
		MinDistanceFromPlayer = 6,
		TargetTries = 30,
		-- Fallback shooter (red block with a barrel) when there is no ReplicatedStorage.Assets.Shooter model.
		BarrelLength = 3,

		-- Shiba tiers (ShooterTier level n = Tiers[n + 1]), defined in Config/EconomyConfig → Shibas (names, models,
		-- heights, colours, FireInterval, RewardMultiplier). Model: ReplicatedStorage.Assets.<AssetName>, scaled to the
		-- tier's Height in studs, bottom on its platform (Config/ShibaPlatforms); effects and motion in Config/ShibaEffects.
		-- Mythic editions reuse a base model with an outline and aura in their Color; a missing model falls back to
		-- the next lower tier's model (then LegacyAssetName) with an outline in its Color.
		Tiers = EconomyConfig.Shibas,
		-- Older single-model name, still used when no tier model exists.
		LegacyAssetName = "Shooter",
		Height = 6,
		-- Turn the model by this many degrees if it doesn't face its target (try 90, 180 or 270).
		YawOffsetDegrees = 0,
		-- Optional parts inside the model: an Attachment where projectiles start, and the stick in its paw.
		MuzzleName = "Muzzle",
		HandStickName = "Stick",
		-- The paw holds the player's current projectile (ProjectileTier): a copy of its model, named Name, replaces the
		-- model's own stick (which stays hidden), LengthScale × the stick's length. The paw's grip point is the stick's
		-- lower end (where the stick meets the paw); the item's long axis lies along the stick.
		-- Projectile models (assets/README.md) have their long axis along model-local Y and a tiny marker part named
		-- GripName at the exact point the paw holds: that point goes on the paw's grip point, the rest of the item
		-- points along the stick, and the marker is always hidden (in the paw and in flight). Models without a Grip
		-- marker fall back to their longest bounding-box side with the grip at its negative end (set
		-- GripAtNegativeEnd false if those show upside down). Without any projectile model the stick stays.
		-- Clients hide whatever is in the paw from the release (Throw.ThrowAtAttribute) for HandStickHideTime seconds,
		-- so it looks thrown, then show it again (Controllers/ShibaController).
		HandProjectile = {
			Name = "HandProjectile",
			GripName = "Grip",
			LengthScale = 0.75,
			GripAtNegativeEnd = true,
		},
		HandStickHideTime = 0.4,
		-- Client-side motion (Controllers/ShibaController). The server writes the yaw the model should face to
		-- AimYawAttribute (radians; pivot rotation CFrame.Angles(0, yaw, 0), YawOffsetDegrees included) and never moves
		-- the model after building it; clients turn it there smoothly: exponential smoothing at TurnSharpness (1/s),
		-- at most MaxTurnDegreesPerSecond. A model may contain an OrbitName part that spins around an OrbitCenterName
		-- marker (made invisible); spin speed and axis, and floating, per model in Config/ShibaEffects.
		Motion = {
			AimYawAttribute = "AimYaw",
			TurnSharpness = 12,
			MaxTurnDegreesPerSecond = 540,
			OrbitName = "Orbit",
			OrbitCenterName = "OrbitCenter",
			-- Invisible part the server puts at the model's pivot (its PrimaryPart): the rest pose clients turn from.
			PivotName = "ShibaPivot",
		},
		-- Throw animation (client, Controllers/ShibaController). Models with a ThrowArmName part and a ShoulderName
		-- marker swing that arm (with what is in the paw) around the shoulder: back during AimTime, forward to
		-- ReleaseDegrees in SwingTime when the projectile leaves the paw, then back to rest in ReturnTime. The server
		-- sets ThrowAtAttribute on the shooter model to the release time (Workspace:GetServerTimeNow()) when it starts
		-- aiming.
		Throw = {
			ThrowArmName = "ThrowArm",
			ShoulderName = "Shoulder",
			ThrowAtAttribute = "ThrowAt",
			WindupDegrees = 50,
			ReleaseDegrees = 110,
			SwingTime = 0.12,
			ReturnTime = 0.5,
		},
	},

	Projectiles = {
		LaunchAngleDegrees = 45,
		-- Launch speed varies by ± this fraction per shot.
		SpeedJitter = 0.1,
		-- Landing (all planned in Util/ProjectilePath, so client and server agree): after the flight it bounces `Bounces`
		-- times, then makes the small settling hops, then lies still and fades out over LandingFadeTime.
		Bounces = 2,
		-- Vertical speed kept per bounce (0.5 = half as fast upward as it came down).
		BounceRestitution = 0.5,
		-- Horizontal speed kept per bounce.
		BounceFriction = 0.7,
		-- Small hops after the bounces, as apex heights in studs above the ground. Fixed heights, so they stay visible
		-- whatever the shot's gravity; each is capped at the previous hop's height. {} = no settling hops.
		SettleHopHeights = { 0.7, 0.3 },
		-- Horizontal speed kept per settling hop; after the last one the projectile lies still.
		SettleFriction = 0.45,
		-- Seconds the landed projectile lies on the ground fading out before it is gone.
		LandingFadeTime = 0.6,
		-- Whether a landed projectile can still be collected while it fades. false: only until it comes to rest
		-- (flight, bounces and settling hops). The client check and the server validation both follow this.
		CollectableWhileFading = false,
		-- A projectile that bounces off the island edge is removed this far below the island surface (no fade).
		FallDespawnDepth = 20,
		-- Server cleanup delay after the landing fade ends (path EndTime + FadeTime). Clients stop drawing the
		-- projectile when their fade ends, so this only has to outlast the network delay.
		DespawnDelay = 0.5,
		-- The server accepts hit reports up to this long after the collectable window ended
		-- (ProjectilePath.GetCollectEndTime) and keeps the path that long, so reports delayed by the network still count.
		ReportGracePeriod = 2,
		-- Safety net only; normal paths end much earlier.
		MaxLifetime = 15,
		MaxPerIsland = 60,
		-- Random spin in radians/s, purely visual.
		MaxSpin = 10,
		-- Golden projectiles: rarer, glow gold, pay GoldenMultiplier times as much (chance: Lucky Sticks pass raises it).
		GoldenChance = 0.05,
		GoldenMultiplier = EconomyConfig.Bonk.GoldenMultiplier,
		GoldenColor = Color3.fromRGB(255, 205, 40),
		GoldenAttribute = "Golden",
		-- Fill transparency of the gold outline (before the landing fade).
		GoldenFillTransparency = 0.55,
		-- A projectile that already paid out keeps flying (it passes through the player) at this transparency.
		PaidTransparency = 0.5,
		-- Attribute set on each projectile marker, read by the client (the path itself: Util/ProjectilePath).
		IdAttribute = "ProjectileId",
		-- Stick density cap (Shooters.MaxThrowsPerSecond): a stick worth several throws carries its ValueMultiplier
		-- (number, only set when > 1) in this marker attribute. Clients show it (Controllers/ProjectileController):
		-- from MinShown on, a small "×N" tag above the stick (N with one decimal) and a trail in the tier colour that
		-- gets wider and longer with N, up to WidthMax × the diameter and LifetimeMax seconds at N = FullAt.
		ValueMultiplierAttribute = "ValueMultiplier",
		ValueTag = {
			MinShown = 1.05,
			FullAt = 6,
			Color = Color3.fromRGB(255, 235, 140),
			StrokeColor = Color3.fromRGB(60, 35, 10),
			-- Tag size in studs (it scales with distance like the stick) and height above the stick's centre, in
			-- diameters. Hidden beyond MaxDistance studs.
			Width = 3,
			Height = 1.2,
			Offset = 0.9,
			MaxDistance = 140,
			WidthMin = 1.2,
			WidthMax = 2.2,
			LifetimeMin = 0.25,
			LifetimeMax = 0.45,
		},
	},

	-- Landing ring (Controllers/ProjectileController, only for your own projectiles): a flat ring on the ground where
	-- the projectile will first land, in its tier colour (also for golden ones: gold means Perfect). It starts StartRadius wide at launch
	-- and shrinks evenly until, at the landing, it matches the pickup sphere (projectile radius + Hits.PickupPadding),
	-- drawn as a faint filled disc underneath. During the Perfect window (Hits.PerfectWindow) it turns PerfectColor
	-- and thicker. It disappears at the landing or when the projectile is caught.
	LandingRing = {
		StartRadius = 10,
		-- The ring always starts at least this much wider than its end size (giant sticks).
		MinShrink = 3,
		Thickness = 0.5,
		PerfectThicknessScale = 1.8,
		-- Height of the flat cylinders and how far above the ground they float: over the field's paint plate
		-- (Island.FieldTop 0.05 + FieldDecor.Paint.Lift 0.04), so the ring always draws on top of the paint.
		Height = 0.1,
		GroundOffset = 0.16,
		Transparency = 0.2,
		TargetTransparency = 0.72,
		-- Fades in over this many seconds after launch.
		FadeInTime = 0.25,
		-- The tier colour is mixed this much toward white, so dark tiers (the wooden stick) show on the grass.
		Brighten = 0.35,
		PerfectColor = Color3.fromRGB(255, 205, 40),
	},

	Hits = {
		ImmunityTime = 0.5,
		-- Extra pickup reach in studs around every projectile, so they are easier to collect without bigger models.
		-- Client: the overlap sphere is projectile radius + PickupPadding. Server: HitTolerance / HeadTolerance are added
		-- on top of radius + PickupPadding, so both sides stay consistent. Keep it well below
		-- Shooters.MinDistanceFromPlayer, or the anti-farm rule no longer keeps standing players at 0.
		PickupPadding = 2,
		-- Catch quality by timing (BonkService, docs/decisions/0005): the catch moment is compared with the moment the
		-- projectile first touches the ground (ProjectilePath.GetFirstLandingTime).
		--   caught after it touched the ground                      → Normal  ("BONK")
		--   caught in the air, within PerfectWindow s of the landing → Perfect ("PERFECT BONK", ring turns gold)
		--   caught earlier in the air                               → Good    ("AIR BONK")
		-- A stick comes down at ~25 studs/s, so a standing player gets it about 0.15 s (right on the landing spot)
		-- to 0.3 s (a few studs in front of it) before it lands; earlier catches need a jump. 0.25 = "be inside the
		-- ring when it closes". Raise it to make Perfect easier.
		PerfectWindow = 0.25,
		-- Catch moment = the first time the path came within projectile radius + PickupPadding + ContactBodyRadius of
		-- the character's body line: from ContactLegLength below the root part up to the head (what the client saw
		-- touch). If the path never came that close (network delay), the time of its closest approach to the root.
		ContactBodyRadius = 1,
		ContactLegLength = 3,
		-- The catch moment is only searched in the last (player ping + ReportLookbackSlack) seconds before the report
		-- arrived, at most ReportLookbackMax: the client reports right when it sees the touch. Without this bound a
		-- player who reaches the landing spot late (the descent passed through it earlier) would get Perfect.
		ReportLookbackSlack = 0.12,
		ReportLookbackMax = 0.6,
		-- Client: projectiles farther than projectile radius + PickupPadding + this from the root part skip the exact
		-- overlap check.
		BroadPhaseDistance = 6,
		-- Server: a reported hit counts if the path passed within projectile radius + PickupPadding + this of the root
		-- part. Covers body size plus network delay (docs/decisions/0003).
		HitTolerance = 6,
		-- A hit that touches the head pays HeadMultiplier times as much. The server accepts the client's head claim
		-- if the path passed within projectile radius + PickupPadding + HeadTolerance of the server-side head.
		HeadMultiplier = EconomyConfig.Bonk.HeadMultiplier,
		HeadTolerance = 4,
		-- Server: time step when searching the flight path for its closest point to the player.
		FlightSampleStep = 0.02,
		MaxReportsPerSecond = 10,
	},

	Character = {
		-- The jump take-off speed.
		JumpPower = 50,
	},

	-- Hits in a row: each hit within the window adds Step to the multiplier (up to MaxMultiplier).
	-- Window = BaseWindow + ShotsWindow × time between two shots, so it stays fair with more or faster shooters.
	Combo = {
		BaseWindow = 2,
		ShotsWindow = 1.5,
		Step = EconomyConfig.Bonk.ComboStep,
		MaxMultiplier = EconomyConfig.Bonk.ComboMax,
	},

	-- Only a small nudge (was 0.25 s at 16 / 12 studs/s, about 4 studs): under a stud sideways and a tiny hop, so the
	-- player keeps control while collecting.
	Knockback = {
		Duration = 0.12,
		HorizontalSpeed = 6,
		UpSpeed = 4,
	},

	Bonk = {
		PopupTime = 1,
		PopupRise = 4,
		-- Bonk hit sound (Controllers/BonkController): custom cartoon "bonk" (assets/audio/Bonk.mp3, ≈ 0.9 s). To swap it,
		-- paste another "rbxassetid://<id>" here. If it ever stays silent in the published game, the audio's
		-- permissions (Creator Hub → Audio → Permissions) must allow this experience. Every hit plays its own copy,
		-- so quick hits overlap instead of cutting each other off.
		SoundId = "rbxassetid://92393279714658",
		SoundVolume = 0.8,
		-- Juice per catch quality (Economy.HitQualities names; docs/GAME_DESIGN.md → Feedback). The popup reads
		-- "<Label><Punctuation> +X" ("AIR BONK! +50"; head hits say HEADBONK instead of BONK), PopupScale × the
		-- base popup size; Bounce = it pops in at BounceScale and springs back. Pitch = bonk sound playback speed
		-- (kept close to 1 so the cartoon bonk still sounds like itself). Coins = gold coins bursting from the
		-- character, Stars = stars from the head, Shake = camera shake strength in studs (0 = none).
		Qualities = {
			Normal = { Punctuation = "", PopupScale = 1, Bounce = false, Pitch = 1, Coins = 4, Stars = 6, Shake = 0 },
			Good = {
				Punctuation = "!",
				PopupScale = 1.2,
				Bounce = false,
				Pitch = 1.08,
				Coins = 8,
				Stars = 10,
				Shake = 0.08,
			},
			Perfect = {
				Punctuation = "!!",
				PopupScale = 1.6,
				Bounce = true,
				Pitch = 1.18,
				Coins = 16,
				Stars = 18,
				Shake = 0.35,
			},
		},
		-- Popup base size in pixels, and the bounce: starts at BounceScale × its size, back to 1 in BounceTime.
		PopupWidth = 320,
		PopupHeight = 60,
		BounceScale = 1.8,
		BounceTime = 0.35,
		-- Head hits and golden sticks shake this much harder (multiplied).
		HeadShakeScale = 1.3,
		GoldenShakeScale = 1.3,
		ShakeTime = 0.25,
		-- Coins bursting from the character (local, visual-only parts): thin gold discs flying up and out, spinning,
		-- gone after Lifetime. At most MaxCoins alive at once (quick hits don't pile up).
		Coins = {
			Diameter = 0.9,
			Thickness = 0.15,
			Color = Color3.fromRGB(255, 205, 40),
			OutSpeed = 12,
			UpSpeed = 22,
			Lifetime = 0.8,
			MaxCoins = 40,
		},
		-- Combo meter (below the top bar): "COMBO xN ×M" plus a name once the multiplier reaches a tier, in its colour.
		-- The meter punches (grows briefly) when a new tier is reached.
		ComboTiers = {
			{ Multiplier = 1.5, Name = "ON FIRE", Color = Color3.fromRGB(255, 140, 40) },
			{ Multiplier = 2, Name = "BONKTASTIC", Color = Color3.fromRGB(255, 70, 160) },
			{ Multiplier = 3, Name = "MAX BONK", Color = Color3.fromRGB(255, 215, 40) },
		},
		ComboColor = Color3.fromRGB(255, 120, 60),
		ComboPunchScale = 1.35,
		ComboPunchTime = 0.3,
		-- A new player's very first caught stick: a big splash in the middle of the screen,
		-- "<Text> ×<EconomyConfig.Bonk.FirstBonkMultiplier>", for Time seconds.
		FirstBonk = {
			Text = "FIRST BONK!",
			Color = Color3.fromRGB(255, 215, 40),
			Time = 2.5,
		},
		-- Impact burst where the projectile hit, in its tier colour (Config/Projectiles Color; golden: GoldenColor):
		-- Particles + PerTier × (tier − 1) particles, Size + SizePerTier × (tier − 1) studs, so better throwables
		-- burst bigger. Textures picks a built-in particle look per projectile Id (default Sparkles).
		Impact = {
			Particles = 8,
			PerTier = 3,
			Size = 0.5,
			SizePerTier = 0.08,
			Speed = 14,
			Lifetime = 0.5,
			Textures = {
				Newspaper = "Smoke",
				Baguette = "Smoke",
				GiantBone = "Smoke",
				BonkSign = "Fire",
				NeonStick = "Sparkles",
				LegendaryStick = "Fire",
			} :: { [string]: string },
		},
	},

	-- Auto-Catch pass look (Controllers/MagnetController, purely visual; the catching itself is AutoCatchService with
	-- Shop.Pass.AutoCatchRadius / AutoCatchInterval). A small red/silver magnet circles the owner; when the server
	-- catches a stick (its Paid attribute turns true without a hand report) the stick is pulled into the player.
	Magnet = {
		-- Size of the magnet (1 = about 1 stud long).
		Scale = 1.1,
		-- Circle around the character's root: radius, height above the root, speed (radians per second).
		OrbitRadius = 3,
		OrbitHeight = 1.2,
		OrbitSpeed = 1.6,
		-- Gentle bobbing on top of the circle.
		BobHeight = 0.3,
		BobPeriod = 1.4,
		-- How quickly the magnet follows its circle point (1/s; higher = snappier).
		FollowSharpness = 14,
		-- A caught stick flies from where it was into the player in PullTime seconds, shrinking to PullEndScale.
		PullTime = 0.22,
		PullEndScale = 0.35,
		-- The magnet wiggles by up to WiggleDegrees for WiggleTime after each catch.
		WiggleTime = 0.35,
		WiggleDegrees = 28,
		-- Sparkles where the stick arrives.
		Sparkles = 10,
		BeamColor = Color3.fromRGB(140, 210, 255),
		-- At most this many pulls animate at once (extra catches only wiggle the magnet).
		MaxPulls = 6,
	},
}
