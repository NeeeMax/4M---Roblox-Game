--!strict
-- Upgrade stands on every player island (docs/GAME_DESIGN.md → Upgrades → Upgrade stands). StationService builds
-- them, StationController draws their billboards and hints.
-- Positions are relative to the island: `Along` = studs from the island centre toward the bridge (HubAngle),
-- `Side` = studs to the right (+) or left (−) of that path, looking from the field toward the bridge.

export type Spot = {
	Upgrade: string,
	Along: number,
	Side: number,
}

return {
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
