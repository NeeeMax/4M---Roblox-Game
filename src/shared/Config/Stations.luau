--!strict
-- Island layout v2: upgrade stalls, the rebirth shrine, zone signs, the path ring and the tree grove on every player
-- island (docs/GAME_DESIGN.md → World → Island layout; every distance is checked in docs/economy/LAYOUT.md).
-- StationService builds the stalls, IslandService the signs, path and trees, StationController draws the stalls'
-- billboards and hints.
--
-- Positions are polar, relative to the island: Angle = degrees clockwise (seen from above) from the direction toward
-- the bridge (HubAngle; 90 = right of the bridge when looking from the field toward it), Radius = studs from the
-- centre; direction(a) = (sin a, 0, −cos a), the same convention as StationService and NPCShooterService.
-- The field is radius 30, the Shibas stand at 56 (the Giant Shiba's barrier reaches 67), the island edge is 80:
-- the path runs at 70 just behind the Shibas, the stalls stand right behind the path (74) facing the island centre,
-- the zone signs behind the stalls (78.5), high enough to read over them. Walking clockwise from the spawn (90) =
-- later in the game. The sector from the rebirth shrine (270) back to the bridge (360) is free for the tree grove.
export type Zone = {
	Id: string,
	-- Text on the zone sign.
	Title: string,
	Angle: number,
	Radius: number,
	Color: Color3,
}

export type Stall = {
	-- "Upgrade": the upgrade stand of `Upgrade`; "Rebirth": the rebirth shrine (RebirthService).
	Kind: string,
	Upgrade: string?,
	Zone: string,
	Angle: number,
	Radius: number,
}

return {
	-- Themed zones, each with a sign (behind the middle of its stalls). Early zones sit next to the spawn, later ones
	-- further round the island.
	Zones = {
		{ Id = "ShibaShop", Title = "SHIBA SHOP", Angle = 90, Radius = 78.5, Color = Color3.fromRGB(255, 140, 60) },
		{ Id = "Throwables", Title = "THROWABLES", Angle = 150, Radius = 78.5, Color = Color3.fromRGB(255, 200, 40) },
		{ Id = "SpeedGym", Title = "SPEED GYM", Angle = 30, Radius = 78.5, Color = Color3.fromRGB(80, 200, 255) },
		{
			Id = "Automation",
			Title = "AUTOMATION",
			Angle = 202.5,
			Radius = 78.5,
			Color = Color3.fromRGB(90, 200, 160),
		},
		{ Id = "Rebirth", Title = "REBIRTH", Angle = 270, Radius = 78.5, Color = Color3.fromRGB(200, 110, 255) },
	} :: { Zone },
	Stalls = {
		{ Kind = "Upgrade", Upgrade = "ShooterTier", Zone = "ShibaShop", Angle = 62, Radius = 74 },
		{ Kind = "Upgrade", Upgrade = "Shooters", Zone = "ShibaShop", Angle = 118, Radius = 74 },
		{ Kind = "Upgrade", Upgrade = "ProjectileTier", Zone = "Throwables", Angle = 150, Radius = 74 },
		{ Kind = "Upgrade", Upgrade = "MoveSpeed", Zone = "SpeedGym", Angle = 30, Radius = 74 },
		{ Kind = "Upgrade", Upgrade = "Basket", Zone = "Automation", Angle = 185, Radius = 74 },
		{ Kind = "Upgrade", Upgrade = "Intern", Zone = "Automation", Angle = 220, Radius = 74 },
		{ Kind = "Rebirth", Zone = "Rebirth", Angle = 270, Radius = 74 },
	} :: { Stall },
	-- No two stalls (and no stall and the spawn) closer than this.
	MinStallDistance = 30,
	-- Brand-new players (no purchase yet) spawn here, facing the island centre: the NEW SHIBA pad (first purchase,
	-- where the second Shiba will stand at Angle 90 on the Shiba ring) is right in front of them.
	NewPlayerSpawn = { Angle = 90, Radius = 72 },
	-- Name of the rebirth shrine's prompt part (Island_<UserId>.Stations.<RebirthAnchorName>).
	RebirthAnchorName = "Station_Rebirth",
	-- Hold the rebirth prompt this long (it resets everything, so no accidental presses).
	RebirthHoldSeconds = 3,
	-- Starts with UpgradePromptPrefix, so other players' clients hide it like the stands' prompts (StationController).
	RebirthPromptName = "UpgradeStand_Rebirth",
	-- Prop_RebirthShrine in ReplicatedStorage.Assets replaces the part-built shrine; this tall.
	RebirthPropName = "Prop_RebirthShrine",
	RebirthHeight = 9,
	-- Server-side limit: one rebirth prompt trigger per player per this many seconds.
	RebirthCooldown = 2,

	-- Attributes on every anchor part (Station_<UpgradeId>, Station_Rebirth), set by the server, read by the client
	-- (docs/NETWORK.md): Kind ("Upgrade" / "Rebirth"), Locked (upgrade: the owner's Shiba Tier is below UnlockAt;
	-- rebirth: RebirthService.CanRebirth is false) and UnlockAt (the ShooterTier level that unlocks it).
	KindAttribute = "Kind",
	LockedAttribute = "Locked",
	UnlockAtAttribute = "UnlockAt",
	-- Locked stalls get a grey shutter with a padlock (a model with this name inside the Stations folder, named
	-- <LockName>_<UpgradeId>) in front of the counter; their prompts are disabled.
	LockName = "Lock",
	LockColor = Color3.fromRGB(120, 124, 132),
	PadlockColor = Color3.fromRGB(255, 200, 60),

	-- Zone signs: a board on two wooden posts, its centre this high above the island surface (over the stall
	-- billboards, which end about 11.5 studs up), facing the island centre.
	ZoneSign = {
		BoardSize = Vector3.new(16, 3.4, 0.5),
		BoardHeight = 14,
		PostWidth = 0.8,
		-- Posts under the board ends, this far from the board centre.
		PostOffset = 6.5,
		BoardColor = Color3.fromRGB(45, 32, 28),
		PostColor = Color3.fromRGB(110, 80, 55),
	},

	-- The path ring: flat segments from the bridge (FromAngle) clockwise to the rebirth shrine (ToAngle), plus a link
	-- from where the bridge arrives (LinkFrom … LinkTo radius, at angle 0). Visual only (no collisions): the tops are
	-- TopHeight above the island surface, every second segment TopStep higher so overlapping corners never flicker.
	PathRing = {
		Radius = 70,
		Width = 4,
		FromAngle = 0,
		ToAngle = 270,
		SegmentDegrees = 6,
		TopHeight = 0.2,
		TopStep = 0.06,
		Thickness = 0.4,
		LinkFrom = 72,
		LinkTo = 79,
		LinkWidth = 7,
		Colors = { Color3.fromRGB(222, 196, 140), Color3.fromRGB(205, 178, 124) },
		Material = Enum.Material.Cobblestone,
	},

	-- Trees stand in this free sector (no stall, sign or path there), alternating between the two radii; flowers
	-- FlowerAngle degrees further round and FlowerInset studs further in than each tree.
	Grove = {
		FromAngle = 290,
		ToAngle = 342,
		Radii = { 73.5, 77 },
		FlowerAngle = 4,
		FlowerInset = 3.5,
	},

	-- Prop_UpgradeStand_<UpgradeId> in ReplicatedStorage.Assets replaces the part-built stand; this tall.
	StandHeight = 7,
	PropPrefix = "Prop_UpgradeStand_",
	-- Names the client relies on: Island_<UserId>.Stations.Station_<UpgradeId> (invisible part holding the prompts,
	-- the billboard sits above it) and Island_<UserId>.Stations.ShibaPad.
	FolderName = "Stations",
	AnchorPrefix = "Station_",
	PadName = "ShibaPad",
	-- ProximityPrompt names: the E prompt (server buys a level) and the F prompt (client sends ShopBuy).
	UpgradePromptPrefix = "UpgradeStand_",
	RobuxPromptPrefix = "BuyRobux_",
	-- Developer product sold by the F prompt: "Instant" .. UpgradeId (Config/Shop).
	RobuxProductPrefix = "Instant",
	PromptDistance = 10,

	-- With the Stack Upgrade pass one press buys as many levels as affordable, up to this many.
	StackMax = 10,
	-- Server-side limit for stand presses and pad touches per player.
	MaxPressesPerSecond = 5,
	PadCooldown = 2,
	PadSize = Vector3.new(7, 0.6, 7),
	PadColor = Color3.fromRGB(60, 230, 90),

	-- Client hints.
	BillboardMaxDistance = 90,
	-- "Show me" path from the character to a stand lasts this long (or until the player arrives).
	PathSeconds = 8,
	PathArriveDistance = 9,
	PopupSeconds = 10,
}
