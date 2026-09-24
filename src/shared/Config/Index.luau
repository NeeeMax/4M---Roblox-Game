--!strict
-- Shiba-Index (docs/GAME_DESIGN.md → Shiba-Index): a collection book. One entry per Shiba tier, projectile tier,
-- the golden stick and each trophy, built from their configs, so a new tier or trophy shows up here by itself.
-- An entry is "seen" once the player owns / reaches it (IndexService); each seen entry pays a one-time discovery
-- reward of `RewardHits` normal bonks (RewardService.Hits), and seeing all of them unlocks the completion bonus.

local Gameplay = require(script.Parent.Gameplay)
local Projectiles = require(script.Parent.Projectiles)
local Shop = require(script.Parent.Shop)

export type Kind = "Shiba" | "Projectile" | "Golden" | "Trophy"

export type Entry = {
	-- "Shiba_<AssetName>", "Projectile_<Id>", "Golden" or "Trophy_<Id>".
	Id: string,
	Kind: Kind,
	DisplayName: string,
	Color: Color3,
	-- Discovery reward in normal bonks (RewardService.Hits).
	RewardHits: number,
	-- For Shiba / Projectile: the upgrade level that reaches it (0 = start). Else 0.
	Level: number,
	-- For Trophy: the trophy id. Else "".
	Trophy: string,
}

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

local GOLDEN_ID = "Golden"
-- ClaimIndex(COMPLETE_ID) claims the completion bonus.
local COMPLETE_ID = "Complete"

local entries: { Entry } = {}
local byId: { [string]: Entry } = {}

local function add(entry: Entry)
	table.insert(entries, entry)
	byId[entry.Id] = entry
end

for index, tier in Gameplay.Shooters.Tiers do
	add({
		Id = `Shiba_{tier.AssetName}`,
		Kind = "Shiba",
		DisplayName = tier.Name,
		Color = tier.Color,
		RewardHits = SHIBA_HITS_BASE + SHIBA_HITS_PER_TIER * (index - 1),
		Level = index - 1,
		Trophy = "",
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
	})
end

local Index = {
	-- Every entry, in book order: Shibas, projectiles, golden stick, trophies.
	Entries = entries,
	GoldenId = GOLDEN_ID,
	CompleteId = COMPLETE_ID,
	-- Completion bonus in normal bonks, claimable once every entry is seen.
	CompleteRewardHits = 1000,
	-- Section titles in the menu, per kind.
	KindNames = {
		Shiba = "SHIBAS",
		Projectile = "STICKS",
		Golden = "STICKS",
		Trophy = "TROPHIES",
	} :: { [Kind]: string },
	-- ClaimIndex requests per second per player.
	MaxClaimsPerSecond = 5,
}

function Index.Get(id: string): Entry?
	return byId[id]
end

function Index.ShibaId(level: number): string?
	local tier = Gameplay.Shooters.Tiers[level + 1]
	return if tier then `Shiba_{tier.AssetName}` else nil
end

function Index.ProjectileId(level: number): string?
	local id = Projectiles.Tiers[level + 1]
	return if id then `Projectile_{id}` else nil
end

function Index.TrophyId(trophyId: string): string
	return `Trophy_{trophyId}`
end

return Index
