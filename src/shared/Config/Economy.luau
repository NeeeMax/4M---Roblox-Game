--!strict
-- Rewards, hit quality, purchases and saving (docs/GAME_DESIGN.md → Hits, Economy, Saving).

local Types = require(script.Parent.Parent.Types)

export type HitQualityDef = {
	Name: Types.HitQuality,
	-- Lowest impact-speed ratio (relative impact speed / launch speed) that gives this quality.
	MinRatio: number,
	Multiplier: number,
	-- Popup text colour.
	Color: Color3,
}

-- Sorted from lowest to highest MinRatio; the last entry the ratio reaches wins.
local hitQualities: { HitQualityDef } = {
	{ Name = "Normal", MinRatio = 0, Multiplier = 1, Color = Color3.fromRGB(255, 255, 255) },
	{ Name = "Good", MinRatio = 1.2, Multiplier = 2, Color = Color3.fromRGB(120, 255, 120) },
	{ Name = "Hard", MinRatio = 1.5, Multiplier = 5, Color = Color3.fromRGB(80, 180, 255) },
	{ Name = "Massive", MinRatio = 1.8, Multiplier = 10, Color = Color3.fromRGB(200, 100, 255) },
	{ Name = "Legendary", MinRatio = 2.2, Multiplier = 50, Color = Color3.fromRGB(255, 200, 0) },
}

return {
	StartingPoints = 0,
	HitQualities = hitQualities,

	-- Per player, for RequestPurchase and SetActiveShooters each.
	MaxRequestsPerSecond = 5,

	-- Bump the version suffix only if the saved format changes incompatibly.
	DataStoreName = "PlayerData_v1",
	AutosaveInterval = 60,
	DataStoreAttempts = 3,
}
