--!strict
-- Shiba-Index (docs/GAME_DESIGN.md → Shiba-Index): a collection book. One entry per Shiba tier, projectile tier,
-- the golden stick and each trophy, built from their configs, so a new tier or trophy shows up here by itself, plus
-- one entry per Shiba tier and variant (Shiny / Rainbow / Huge, the VARIANTS tab, docs → Shiba Variants).
-- An entry is "seen" once the player owns / reaches it (IndexService); each seen entry pays a one-time discovery
-- reward of `RewardHits` normal bonks (RewardService.Hits). Seeing every entry that CountsForCompletion unlocks the
-- completion bonus: Robux-only trophies (Shop.Trophy.RobuxOnly) and variant entries are shown but never required
-- (variants have their own progress in the VARIANTS tab).

local EconomyConfig = require(script.Parent.EconomyConfig)
local Gameplay = require(script.Parent.Gameplay)
local Projectiles = require(script.Parent.Projectiles)
local ShibaEffects = require(script.Parent.ShibaEffects)
local Shop = require(script.Parent.Shop)

export type Kind = "Shiba" | "Projectile" | "Golden" | "Trophy" | "Variant"

export type Entry = {
	-- "Shiba_<AssetName>" (the ten originals), "Shiba_<Edition><AssetName>" (Shiny/Mythic editions, e.g.
	-- "Shiba_ShinyShiba"), "Projectile_<Id>", "Golden", "Trophy_<Id>" or "Variant_<Variant>_<AssetName>" (e.g.
	-- "Variant_Rainbow_SamuraiShiba"). Saved in state.Index: never rename.
	Id: string,
	Kind: Kind,
	DisplayName: string,
	Color: Color3,
	-- Discovery reward in normal bonks (RewardService.Hits).
	RewardHits: number,
	-- For Shiba / Projectile / Variant: the upgrade level that reaches it (0 = start). Else 0.
	Level: number,
	-- For Trophy: the trophy id. Else "".
	Trophy: string,
	-- For Variant: the VariantId ("Shiny", "Rainbow", "Huge"). Else "".
	Variant: string,
	-- Robux-only trophy: shown, marked "exclusive", not needed for the completion bonus.
	Exclusive: boolean,
}

-- Shiba n pays SHIBA_HITS_BASE + SHIBA_HITS_PER_TIER × (n − 1) bonks (20 … 310 for the 30 Shibas). Bonks are worth
-- the current stick value, so a late entry still pays about a minute of income.
local SHIBA_HITS_BASE = 20
local SHIBA_HITS_PER_TIER = 10
local PROJECTILE_HITS_BASE = 15
local PROJECTILE_HITS_PER_TIER = 5
local GOLDEN_HITS = 50
local TROPHY_HITS: { [string]: number } = {
	Common = 25,
	Rare = 50,
	Epic = 100,
	Legendary = 200,
	Exclusive = 300,
}
-- Variant entries, in tab order (worst first).
local VARIANT_ORDER = { "Shiny", "Rainbow", "Huge" }

local GOLDEN_ID = "Golden"
-- ClaimIndex(COMPLETE_ID) claims the completion bonus.
local COMPLETE_ID = "Complete"

local entries: { Entry } = {}
local byId: { [string]: Entry } = {}

local function add(entry: Entry)
	assert(byId[entry.Id] == nil, `duplicate Shiba-Index id {entry.Id}`)
	table.insert(entries, entry)
	byId[entry.Id] = entry
end

-- Entry id of a Shiba tier. The ten originals keep their old ids (saves from before the editions stay valid); the
-- Shiny/Mythic editions reuse a model, so their id adds the edition.
local function shibaEntryId(tier: typeof(Gameplay.Shooters.Tiers[1])): string
	return `Shiba_{tier.Edition or ""}{tier.AssetName}`
end

local function variantEntryId(variant: string, tier: typeof(Gameplay.Shooters.Tiers[1])): string
	return `Variant_{variant}_{tier.Edition or ""}{tier.AssetName}`
end

for index, tier in Gameplay.Shooters.Tiers do
	add({
		Id = shibaEntryId(tier),
		Kind = "Shiba",
		DisplayName = tier.Name,
		Color = tier.Color,
		RewardHits = SHIBA_HITS_BASE + SHIBA_HITS_PER_TIER * (index - 1),
		Level = index - 1,
		Trophy = "",
		Variant = "",
		Exclusive = false,
	})
end
for index, id in Projectiles.Tiers do
	local def = Projectiles.Defs[id]
	add({
		Id = `Projectile_{id}`,
		Kind = "Projectile",
		DisplayName = def.DisplayName,
		Color = def.Color,
		RewardHits = PROJECTILE_HITS_BASE + PROJECTILE_HITS_PER_TIER * (index - 1),
		Level = index - 1,
		Trophy = "",
		Variant = "",
		Exclusive = false,
	})
end
add({
	Id = GOLDEN_ID,
	Kind = "Golden",
	DisplayName = "Golden Stick",
	Color = Gameplay.Projectiles.GoldenColor,
	RewardHits = GOLDEN_HITS,
	Level = 0,
	Trophy = "",
	Variant = "",
	Exclusive = false,
})
for _, trophy in Shop.Trophies do
	add({
		Id = `Trophy_{trophy.Id}`,
		Kind = "Trophy",
		DisplayName = trophy.DisplayName,
		Color = trophy.Color,
		RewardHits = TROPHY_HITS[trophy.Rarity] or TROPHY_HITS.Common,
		Level = 0,
		Trophy = trophy.Id,
		Variant = "",
		Exclusive = trophy.RobuxOnly == true,
	})
end
-- Variant entries: grouped by variant (all Shiny Shibas, then Rainbow, then Huge), each in tier order.
for _, variant in VARIANT_ORDER do
	for index, tier in Gameplay.Shooters.Tiers do
		add({
			Id = variantEntryId(variant, tier),
			Kind = "Variant",
			DisplayName = `{variant} {tier.Name}`,
			Color = ShibaEffects.Variants[variant].Color,
			RewardHits = EconomyConfig.Variants.IndexReward[variant],
			Level = index - 1,
			Trophy = "",
			Variant = variant,
			Exclusive = false,
		})
	end
end

local Index = {
	-- Every entry, in book order: Shibas, projectiles, golden stick, trophies, variants.
	Entries = entries,
	GoldenId = GOLDEN_ID,
	CompleteId = COMPLETE_ID,
	-- Completion bonus in normal bonks, claimable once every entry that CountsForCompletion is seen.
	CompleteRewardHits = 1000,
	-- Variant entries, worst first (the VARIANTS tab shows one progress bar each).
	VariantOrder = VARIANT_ORDER,
	-- Section titles in the menu, per kind.
	KindNames = {
		Shiba = "SHIBAS",
		Projectile = "STICKS",
		Golden = "STICKS",
		Trophy = "TROPHIES",
		Variant = "VARIANTS",
	} :: { [Kind]: string },
	-- ClaimIndex requests per second per player.
	MaxClaimsPerSecond = 5,
}

function Index.Get(id: string): Entry?
	return byId[id]
end

-- True if the completion bonus needs this entry: not a Robux-only trophy and not a variant (idea #4 in
-- docs/research/ROBLOX_PACING.md: a bonus only payers can reach feels like a paywall; variants are pure luck).
function Index.CountsForCompletion(entry: Entry): boolean
	return not entry.Exclusive and entry.Kind ~= "Variant"
end

function Index.ShibaId(level: number): string?
	local tier = Gameplay.Shooters.Tiers[level + 1]
	return if tier then shibaEntryId(tier) else nil
end

-- Entry id of the Shiba at ShooterTier `level` in `variant` ("Shiny", "Rainbow", "Huge"), or nil.
function Index.VariantId(variant: string, level: number): string?
	local tier = Gameplay.Shooters.Tiers[level + 1]
	return if tier and ShibaEffects.Variants[variant] then variantEntryId(variant, tier) else nil
end

function Index.ProjectileId(level: number): string?
	local id = Projectiles.Tiers[level + 1]
	return if id then `Projectile_{id}` else nil
end

function Index.TrophyId(trophyId: string): string
	return `Trophy_{trophyId}`
end

return Index
