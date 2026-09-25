--!strict
-- Onboarding (docs/GAME_DESIGN.md → Onboarding / first minute): the "unconscious tutorial" that guides a brand-new
-- player through their first purchases without text walls or popups. TutorialService (server) counts the guided
-- purchases in state.Tutorial.Step; TutorialController (client) draws a glowing line, a pulsing highlight and a short
-- floating hint at the next thing to do. Economy numbers stay in EconomyConfig; this file only tunes the guidance.

local Types = require(script.Parent.Parent.Types)

-- Hints are at most four words (short, big, readable in one glance).
local HINTS = {
	-- The NEW SHIBA pad (buying More Shibas by stepping on it).
	Pad = "Step here!",
	-- Nothing affordable yet and no stick caught this session: over the field.
	Catch = "Catch the stick!",
	-- Nothing affordable, but the player already caught sticks: over the field.
	MoreMoney = "Get more money!",
	-- Per upgrade stall (UpgradeId → hint); unknown upgrades use Upgrade.
	Upgrade = "Upgrade here!",
	Stalls = {
		ShooterTier = "Upgrade your Shibas!",
		ProjectileTier = "Buy better sticks!",
		Shooters = "More Shibas here!",
		MoveSpeed = "Run faster here!",
		Basket = "Get a basket!",
		Intern = "Hire an intern!",
	} :: { [string]: string },
}

local Tutorial = {
	-- The guided hints run until the player has made this many purchases (state.Tutorial.Step counts them).
	GuidedPurchases = 6,
	Hints = HINTS,
	-- Attribute on Islands.Island_<UserId> (set by IslandService): the island's centre (Vector3). The client points
	-- at the field with it.
	IslandCenterAttribute = "IslandCenter",

	-- Line from the character's feet to the target (a Beam). Texture scrolls toward the target; swap in an arrow
	-- texture here once one is uploaded.
	BeamTexture = "rbxasset://textures/particles/sparkles_main.dds",
	BeamTextureLength = 3,
	BeamTextureSpeed = 1.5,
	BeamWidth = 1.4,
	BeamColor = Color3.fromRGB(255, 225, 40),
	BeamEndColor = Color3.fromRGB(70, 255, 110),
	-- No line when the character is already this close to the target.
	BeamHideDistance = 8,

	-- Pulsing Highlight on the target stall / pad.
	HighlightColor = Color3.fromRGB(255, 235, 90),
	HighlightFillMin = 0.35,
	HighlightFillMax = 0.85,
	HighlightPulseSeconds = 0.6,

	-- Floating hint: size in pixels (it stays readable at any distance) and height above the target.
	HintSize = Vector2.new(300, 64),
	HintColor = Color3.fromRGB(255, 225, 40),
	HintOffsetPad = 8,
	HintOffsetStall = 13.5,
	-- Over the field centre.
	HintOffsetField = 9,
	-- The "go to the field" line only shows when the character is farther than this from the island centre.
	FieldBeamDistance = 34,

	-- Next-Shiba silhouette next to the Shiba Tier stall (StationController): its height, offset from the stall's
	-- anchor (stall-local: X to the side), and how fast it turns (radians per second).
	SilhouetteHeight = 5.5,
	SilhouetteSide = 7.5,
	SilhouetteSpin = 0.6,
}

-- Whether the guided hints run for this state: a new player below GuidedPurchases, with hints switched on.
function Tutorial.IsGuiding(state: Types.PlayerState): boolean
	local hints = state.Settings == nil or state.Settings.Hints ~= false
	return hints and state.Tutorial ~= nil and state.Tutorial.Step < Tutorial.GuidedPurchases
end

-- Brand-new (or freshly reset) player: nothing bought yet and the tutorial not started. They spawn in front of the
-- NEW SHIBA pad (IslandService).
function Tutorial.IsFresh(state: Types.PlayerState): boolean
	if state.Tutorial == nil or state.Tutorial.Step ~= 0 then
		return false
	end
	for _, level in state.UpgradeLevels do
		if level ~= 0 then
			return false
		end
	end
	return true
end

return Tutorial
