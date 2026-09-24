--!strict
-- World, shooter, projectile, hit and bonk-effect tuning (docs/GAME_DESIGN.md). Distances in studs, times in seconds.

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
		PlatformDiameter = 8,
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

		-- Shiba tiers (ShooterTier level n = Tiers[n + 1]). Each tier throws faster (FireInterval: seconds between two
		-- throws of one Shiba) and pays more (RewardMultiplier). Model: ReplicatedStorage.Assets.<AssetName>, scaled to
		-- Height studs, bottom on the platform. A tier without its own model uses the next lower tier's model (then
		-- LegacyAssetName) with an outline in its Color. To add a tier: add a line (the upgrade follows automatically).
		Tiers = {
			{
				Name = "Shiba",
				AssetName = "Shiba",
				FireInterval = 5,
				RewardMultiplier = 1,
				Color = Color3.fromRGB(255, 170, 60),
			},
			-- Tiers 2-10: FireInterval and RewardMultiplier spread geometrically over the same range as before
			-- (5 s -> 1.3 s, x1 -> x60), so the endgame balance is unchanged.
			{
				Name = "Shades Shiba",
				AssetName = "ShadesShiba",
				FireInterval = 4.3,
				RewardMultiplier = 1.6,
				Color = Color3.fromRGB(160, 160, 185),
			},
			{
				Name = "Buff Shiba",
				AssetName = "BuffShiba",
				FireInterval = 3.7,
				RewardMultiplier = 2.5,
				Color = Color3.fromRGB(255, 110, 90),
			},
			{
				Name = "Chef Shiba",
				AssetName = "ChefShiba",
				FireInterval = 3.2,
				RewardMultiplier = 3.9,
				Color = Color3.fromRGB(250, 250, 250),
			},
			{
				Name = "Police Shiba",
				AssetName = "PoliceShiba",
				FireInterval = 2.7,
				RewardMultiplier = 6.2,
				Color = Color3.fromRGB(70, 130, 255),
			},
			{
				Name = "Ninja Shiba",
				AssetName = "NinjaShiba",
				FireInterval = 2.4,
				RewardMultiplier = 9.7,
				Color = Color3.fromRGB(220, 40, 60),
			},
			{
				Name = "Gold Shiba",
				AssetName = "GoldShiba",
				FireInterval = 2,
				RewardMultiplier = 15,
				Color = Color3.fromRGB(255, 200, 40),
			},
			{
				Name = "Galaxy Shiba",
				AssetName = "GalaxyShiba",
				FireInterval = 1.8,
				RewardMultiplier = 24,
				Color = Color3.fromRGB(170, 90, 255),
			},
			{
				Name = "Giant Shiba",
				AssetName = "GiantShiba",
				FireInterval = 1.5,
				RewardMultiplier = 38,
				Color = Color3.fromRGB(255, 130, 40),
			},
			{
				Name = "Cheems God",
				AssetName = "CheemsGod",
				FireInterval = 1.3,
				RewardMultiplier = 60,
				Color = Color3.fromRGB(255, 240, 170),
			},
		},
		-- Older single-model name, still used when no tier model exists.
		LegacyAssetName = "Shooter",
		Height = 6,
		-- Turn the model by this many degrees if it doesn't face its target (try 90, 180 or 270).
		YawOffsetDegrees = 0,
		-- Optional parts inside the model: an Attachment where projectiles start, and the stick in its hand,
		-- which is hidden for HandStickHideTime after each throw.
		MuzzleName = "Muzzle",
		HandStickName = "Stick",
		HandStickHideTime = 0.4,
	},

	Projectiles = {
		LaunchAngleDegrees = 45,
		-- Launch speed varies by ± this fraction per shot.
		SpeedJitter = 0.1,
		-- Ground bounces before the projectile disappears (it disappears on the next ground contact).
		Bounces = 2,
		-- Vertical speed kept per bounce (0.5 = half as fast upward as it came down).
		BounceRestitution = 0.5,
		-- Horizontal speed kept per bounce.
		BounceFriction = 0.7,
		-- A projectile that bounces off the island edge is removed this far below the island surface.
		FallDespawnDepth = 20,
		-- Server cleanup delay after the path ends. Clients already hide the projectile the moment its path ends,
		-- so this only has to outlast the network delay.
		DespawnDelay = 0.5,
		-- The server keeps a projectile's path this long after it ended, so hit reports that arrive after the part is
		-- gone (network delay) can still be validated.
		ReportGracePeriod = 2,
		-- Safety net only; normal paths end much earlier.
		MaxLifetime = 15,
		MaxPerIsland = 60,
		-- Random spin in radians/s, purely visual.
		MaxSpin = 10,
		-- Golden projectiles: rarer, glow gold, pay GoldenMultiplier times as much (chance: Lucky Sticks pass raises it).
		GoldenChance = 0.05,
		GoldenMultiplier = 5,
		GoldenColor = Color3.fromRGB(255, 205, 40),
		GoldenAttribute = "Golden",
		-- A projectile that already paid out keeps flying (it passes through the player) at this transparency.
		PaidTransparency = 0.5,
		-- Attribute set on each projectile marker, read by the client (the path itself: Util/ProjectilePath).
		IdAttribute = "ProjectileId",
	},

	Hits = {
		ImmunityTime = 0.5,
		-- Player velocity used for hit quality is clamped to this vertically (and to WalkSpeed horizontally),
		-- so knockback or a spoofed client velocity can't inflate the quality.
		MaxVerticalPlayerSpeed = 50,
		-- Client: projectiles farther than projectile radius + this from the root part skip the exact overlap check.
		BroadPhaseDistance = 6,
		-- Server: a reported hit counts if the flight path passed within projectile radius + this of the root part.
		-- Covers body size plus network delay (docs/decisions/0003).
		HitTolerance = 6,
		-- A hit that touches the head pays HeadMultiplier times as much. The server accepts the client's head claim
		-- if the path passed within projectile radius + HeadTolerance of the server-side head.
		HeadMultiplier = 2,
		HeadTolerance = 4,
		-- Server: time step when searching the flight path for its closest point to the player.
		FlightSampleStep = 0.02,
		MaxReportsPerSecond = 10,
	},

	Character = {
		-- Matches MaxVerticalPlayerSpeed: the jump take-off speed.
		JumpPower = 50,
	},

	-- Hits in a row: each hit within the window adds Step to the multiplier (up to MaxMultiplier).
	-- Window = BaseWindow + ShotsWindow × time between two shots, so it stays fair with more or faster shooters.
	Combo = {
		BaseWindow = 2,
		ShotsWindow = 1.5,
		Step = 0.1,
		MaxMultiplier = 3,
	},

	Knockback = {
		-- About 4 studs sideways and a small hop.
		Duration = 0.25,
		HorizontalSpeed = 16,
		UpSpeed = 12,
	},

	Bonk = {
		PopupTime = 1,
		PopupRise = 4,
		-- Built-in Studio sound. Swap for any audio asset id ("rbxassetid://123...") you like better.
		SoundId = "rbxasset://sounds/action_jump_land.mp3",
		SoundVolume = 1,
		-- Playback speed goes up by this per hit-quality tier above Normal.
		PitchStepPerTier = 0.1,
		-- Stars bursting from the head: Stars at Normal, plus StarsPerTier per quality tier above it.
		Stars = 6,
		StarsPerTier = 6,
		-- Camera shake from this quality tier on (1 = Normal, 3 = Hard), stronger per tier above it.
		ShakeFromTier = 3,
		ShakeTime = 0.25,
		ShakeStrength = 0.25,
	},
}
