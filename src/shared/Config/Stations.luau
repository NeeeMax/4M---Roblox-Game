--!strict
-- Upgrade stands on every player island (docs/GAME_DESIGN.md → Upgrades → Upgrade stands). StationService builds
-- them, StationController draws their billboards and hints.
-- Positions are relative to the island: `Along` = studs from the island centre toward the bridge (HubAngle),
-- `Side` = studs to the right (+) or left (−) of that path, looking from the field toward the bridge.

-- Island layout v2 (docs/GAME_DESIGN.md → World → Island layout). Positions are polar, relative to the island:
-- Angle = degrees clockwise (seen from above) from the direction toward the bridge (HubAngle; 90 = right of the path
-- when looking from the field toward the bridge, the same side as Spot.Side > 0), Radius = studs from the centre.
-- The field is radius 30, the Shibas stand at 56 (the Giant Shiba's rock reaches 66.5), the island edge is 80:
-- stalls stand on the outer ring behind the Shibas, so the play field stays free.
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

export type Spot = {
	Upgrade: string,
	Along: number,
	Side: number,
}

return {
	-- Themed zones, each with a sign. Early zones sit next to the spawn, later ones further round the island.
	Zones = {
		{ Id = "ShibaShop", Title = "SHIBA SHOP", Angle = 90, Radius = 76, Color = Color3.fromRGB(255, 140, 60) },
		{ Id = "Throwables", Title = "THROWABLES", Angle = 150, Radius = 76, Color = Color3.fromRGB(255, 200, 40) },
		{ Id = "SpeedGym", Title = "SPEED GYM", Angle = 30, Radius = 76, Color = Color3.fromRGB(80, 200, 255) },
		{ Id = "Automation", Title = "AUTOMATION", Angle = 202, Radius = 76, Color = Color3.fromRGB(90, 200, 160) },
		{ Id = "Rebirth", Title = "REBIRTH", Angle = 270, Radius = 76, Color = Color3.fromRGB(200, 110, 255) },
	} :: { Zone },
	Stalls = {
		{ Kind = "Upgrade", Upgrade = "ShooterTier", Zone = "ShibaShop", Angle = 62, Radius = 70 },
		{ Kind = "Upgrade", Upgrade = "Shooters", Zone = "ShibaShop", Angle = 118, Radius = 70 },
		{ Kind = "Upgrade", Upgrade = "ProjectileTier", Zone = "Throwables", Angle = 150, Radius = 70 },
		{ Kind = "Upgrade", Upgrade = "MoveSpeed", Zone = "SpeedGym", Angle = 30, Radius = 70 },
		{ Kind = "Upgrade", Upgrade = "Basket", Zone = "Automation", Angle = 185, Radius = 70 },
		{ Kind = "Upgrade", Upgrade = "Intern", Zone = "Automation", Angle = 220, Radius = 70 },
		{ Kind = "Rebirth", Zone = "Rebirth", Angle = 270, Radius = 70 },
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

	-- OLD layout (v1), still read by StationService until the layout rework replaces it. TODO(layout): remove.
	-- One stand per upgrade, on both sides of the path from the bridge to the field (field radius 30, Shiba ring 56).
	Spots = {
		{ Upgrade = "ShooterTier", Along = 38, Side = -8.5 },
		{ Upgrade = "ProjectileTier", Along = 38, Side = 8.5 },
		{ Upgrade = "Shooters", Along = 47, Side = -8.5 },
		{ Upgrade = "MoveSpeed", Along = 47, Side = 8.5 },
	} :: { Spot },

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
