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
		-- The field in the middle (with a low border around it). Shots land inside TargetRadius.
		FieldRadius = 30,
		TargetRadius = 28,
		BorderHeight = 1.5,
		BorderWidth = 2,
		-- Gap in the border toward the bridge, in degrees.
		BorderGapDegrees = 30,
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
		-- Shiny/Mythic editions reuse a base model with an outline and aura in their Color; a missing model falls back to
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
		-- Playback speed goes up by this per hit-quality tier above Normal (Legendary: 1.2); kept small so the cartoon
		-- bonk still sounds like itself.
		PitchStepPerTier = 0.05,
		-- Stars bursting from the head: Stars at Normal, plus StarsPerTier per quality tier above it.
		Stars = 6,
		StarsPerTier = 6,
		-- Camera shake from this quality tier on (1 = Normal, 3 = Hard), stronger per tier above it.
		ShakeFromTier = 3,
		ShakeTime = 0.25,
		ShakeStrength = 0.25,
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
