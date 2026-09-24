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
		-- Delay before a freshly placed ring of shooters fires for the first time.
		FirstShotDelay = 1,
		-- Anti-farm: the whole path (flight + bounces) must stay at least projectile radius + this far away from
		-- where the player stands at fire time, so standing still never gets hit.
		MinDistanceFromPlayer = 6,
		TargetTries = 30,
		-- Fallback shooter (red block with a barrel) when there is no ReplicatedStorage.Assets.Shooter model.
		BarrelLength = 3,

		-- Custom shooter model: ReplicatedStorage.Assets.<AssetName>. Scaled to Height studs, bottom on the platform.
		AssetName = "Shooter",
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
		-- Server cleanup delay after the path ends. Clients already hide the projectile the moment they see it land
		-- for the last time, so this only has to outlast the network delay.
		DespawnDelay = 0.5,
		-- The server keeps a projectile's path this long after it ended, so hit reports that arrive after the part is
		-- gone (network delay) can still be validated.
		ReportGracePeriod = 2,
		-- Client: a ground contact is detected when the projectile's bottom comes this close to the island surface.
		GroundTolerance = 1,
		-- Safety net only; normal paths end much earlier.
		MaxLifetime = 15,
		MaxPerIsland = 60,
		-- Random spin in radians/s, purely visual.
		MaxSpin = 10,
		-- A projectile that already paid out keeps flying (it passes through the player) at this transparency.
		PaidTransparency = 0.5,
		-- Attribute set on each projectile part, read by the client.
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
		-- Server: time step when searching the flight path for its closest point to the player.
		FlightSampleStep = 0.02,
		MaxReportsPerSecond = 10,
	},

	Character = {
		-- Matches MaxVerticalPlayerSpeed: the jump take-off speed.
		JumpPower = 50,
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
	},
}
