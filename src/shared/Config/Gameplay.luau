--!strict
-- World, shooter, projectile, hit and bonk-effect tuning (docs/GAME_DESIGN.md). Distances in studs, times in seconds.

return {
	Island = {
		-- Names the client relies on to find its own island: Workspace.<FolderName>.<ModelPrefix><UserId>.Projectiles
		FolderName = "Islands",
		ModelPrefix = "Island_",
		-- Islands sit on a grid so one player's projectiles can never reach another island.
		GridSpacing = 500,
		GridColumns = 8,
		SurfaceY = 100,
		Radius = 30,
		Thickness = 4,
		-- Shots land inside this radius (2-stud margin to the edge).
		TargetRadius = 28,
		-- Below this height the character is put back on its island.
		FallOffY = 50,
		SpawnHeight = 4,
		FallCheckInterval = 0.5,
	},

	Shooters = {
		RingRadius = 60,
		PlatformDiameter = 8,
		-- The shooter turns toward its target this long before firing.
		AimTime = 0.5,
		-- Random extra delay per shooter so several shooters don't fire in sync.
		StartOffsetMax = 1,
		-- Delay before a freshly placed shooter aims for the first time.
		FirstShotDelay = 1,
		-- Anti-farm: a target must be at least projectile radius + this far from the player.
		MinDistanceFromPlayer = 8,
		TargetTries = 10,
		BarrelLength = 3,
	},

	Projectiles = {
		LaunchAngleDegrees = 45,
		-- Launch speed varies by ± this fraction per shot.
		SpeedJitter = 0.1,
		LifetimeAfterContact = 1.5,
		MaxLifetime = 8,
		MaxPerIsland = 60,
		-- Random spin in radians/s, purely visual.
		MaxSpin = 10,
		LandedTransparency = 0.5,
		-- Attributes set on each projectile part, read by the client.
		IdAttribute = "ProjectileId",
		LandedAttribute = "Landed",
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
		-- Server: time step when searching the flight path for its closest point to the player.
		FlightSampleStep = 0.02,
		MaxReportsPerSecond = 10,
	},

	Character = {
		-- Matches MaxVerticalPlayerSpeed: the jump take-off speed.
		JumpPower = 50,
	},

	Knockback = {
		Duration = 0.4,
		HorizontalSpeed = 40,
		UpSpeed = 30,
	},

	Bonk = {
		PopupTime = 1,
		PopupRise = 4,
		-- Built-in Studio sound. Swap for any audio asset id ("rbxassetid://123...") you like better.
		SoundId = "rbxasset://sounds/action_jump_land.mp3",
		SoundVolume = 1,
		-- Playback speed goes up by this per hit-quality tier above Normal.
		PitchStepPerTier = 0.1,
	},
}
