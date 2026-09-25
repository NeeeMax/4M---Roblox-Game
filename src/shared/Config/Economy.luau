--!strict
-- Rewards, hit quality, purchases and saving (docs/GAME_DESIGN.md → Hits, Economy, Saving).

local EconomyConfig = require(script.Parent.EconomyConfig)
local Types = require(script.Parent.Parent.Types)

export type HitQualityDef = {
	Name: Types.HitQuality,
	-- Popup text ("BONK", "AIR BONK", "PERFECT BONK").
	Label: string,
	-- From EconomyConfig.Bonk.QualityMultipliers.
	Multiplier: number,
	-- Popup text colour.
	Color: Color3,
}

-- From worst to best (docs/GAME_DESIGN.md → Hits): which one a catch gets depends on WHEN it was caught
-- (BonkService): after the stick touched the ground = Normal, in the air = Good, in the air within
-- Gameplay.Hits.PerfectWindow seconds before it lands = Perfect.
local multipliers = EconomyConfig.Bonk.QualityMultipliers
local hitQualities: { HitQualityDef } = {
	{ Name = "Normal", Label = "BONK", Multiplier = multipliers.Normal, Color = Color3.fromRGB(255, 255, 255) },
	{ Name = "Good", Label = "AIR BONK", Multiplier = multipliers.Good, Color = Color3.fromRGB(120, 255, 120) },
	{ Name = "Perfect", Label = "PERFECT BONK", Multiplier = multipliers.Perfect, Color = Color3.fromRGB(255, 200, 0) },
}

return {
	-- What players see (docs/GAME_DESIGN.md → Economy). The saved field stays `BonkPoints`; only the display changed.
	-- Menus draw the symbol as a bold B with a vertical bar through it (Widgets.MoneySymbol / MoneyText /
	-- SetMoneyText, which replace every `Symbol` in a string with the drawn symbol). `Symbol` is the plain-text form
	-- for strings that can't hold a UI element (leaderstats, 3D boards, chat); notifications are drawn by the HUD.
	Currency = {
		Name = "Bonk Dollars",
		Symbol = "B$",
	},

	HitQualities = hitQualities,

	-- Per player, for RequestPurchase and SetActiveShooters each.
	MaxRequestsPerSecond = 5,

	-- Bump the version suffix only if the saved format changes incompatibly.
	DataStoreName = "PlayerData_v1",
	AutosaveInterval = 60,
	DataStoreAttempts = 3,

	-- Shiba Bank (docs/GAME_DESIGN.md → Offline Shiba Bank): while the player is away, their Shibas keep earning
	-- Share × their recent Bonk Points per minute, for at most MaxHours. Shorter absences than MinSeconds pay nothing.
	OfflineBank = {
		Share = 0.1,
		MaxHours = 8,
		MinSeconds = 60,
		-- The income rate is sampled every SampleSeconds of play and smoothed: rate += Smoothing × (sample − rate).
		-- Samples shorter than MinSampleSeconds (a player who just joined or is leaving) are skipped.
		SampleSeconds = 60,
		MinSampleSeconds = 30,
		Smoothing = 0.3,
		-- A sample counts at most this many normal bonks per Shiba throw (quality, head, combo, golden, boosts and
		-- passes fit below it), so a big coin-flip win can't blow up the offline rate.
		MaxBonksPerThrow = 8,
	},
}
