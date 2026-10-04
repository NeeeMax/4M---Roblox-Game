--!strict
-- Shiba-Index (Config/Index, docs/GAME_DESIGN.md → Shiba-Index): marks entries as seen in state.Index.Seen once the
-- player reaches them, and pays each entry's one-time discovery reward when the player claims it (ClaimIndex).
-- * Shiba / projectile tiers: seen up to the current ShooterTier / ProjectileTier level (checked after every state
--   change, so tier skips, admin levels and old saves count too). 30 Shibas (10 originals + 10 new designs + Mythic
--   editions, Config/Index ids); a rebirth resets the levels but never the book (seen and claimed stay).
-- * Trophies: seen once owned.
-- * Golden stick: seen on the first golden catch (BonkService calls DiscoverGolden).
-- * Variants ("Rainbow Samurai Shiba"): seen while an owned Shiba slot has that variant and the ring is at that tier
--   (VariantService rolls the slots; checked after every state change like the tiers).
-- Seeing every entry that counts (Index.CountsForCompletion: no Robux-only trophies, no variants) unlocks the
-- completion bonus (ClaimIndex(Index.CompleteId)).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Index = require(ReplicatedStorage.Shared.Config.Index)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)

local claimLimiter = RateLimiter.New(Index.MaxClaimsPerSecond, 1)

local IndexService = {}

-- Variants the player's owned Shiba slots have right now (VariantId → true).
local function ownedVariants(state: Types.PlayerState): { [string]: boolean }
	local present: { [string]: boolean } = {}
	local owned = Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters or 0)
	for slot = 1, owned do
		local variant = state.Variants.Slots[tostring(slot)]
		if variant then
			present[variant] = true
		end
	end
	return present
end

local function isReached(state: Types.PlayerState, entry: Index.Entry, variants: { [string]: boolean }): boolean
	if entry.Kind == "Shiba" then
		return (state.UpgradeLevels.ShooterTier or 0) >= entry.Level
	elseif entry.Kind == "Projectile" then
		return (state.UpgradeLevels.ProjectileTier or 0) >= entry.Level
	elseif entry.Kind == "Trophy" then
		return state.Trophies[entry.Trophy] == true
	elseif entry.Kind == "Variant" then
		-- "Rainbow Samurai Shiba": a Rainbow slot while the ring is at the Samurai tier (exact variant; evolving a
		-- variant slot fills that variant's page tier by tier).
		return (state.UpgradeLevels.ShooterTier or 0) == entry.Level and variants[entry.Variant] == true
	end
	-- Golden: only DiscoverGolden marks it.
	return false
end

-- Every entry the completion bonus needs is seen (Robux-only trophies and variants never count, Config/Index).
local function allSeen(state: Types.PlayerState): boolean
	for _, entry in Index.Entries do
		if Index.CountsForCompletion(entry) and not state.Index.Seen[entry.Id] then
			return false
		end
	end
	return true
end

-- Marks `ids` as seen, tells the player and re-sends the state (deferred: this may run inside a Replicate).
local function markSeen(player: Player, state: Types.PlayerState, ids: { string })
	if #ids == 0 then
		return
	end
	for _, id in ids do
		state.Index.Seen[id] = true
	end
	local first = Index.Get(ids[1])
	local name = if first then first.DisplayName else ids[1]
	local more = if #ids > 1 then ` (+{#ids - 1} more)` else ""
	NotifyService.Send(player, `New in your Shiba-Index: {name}{more}! Claim your reward.`, "Good")
	-- Its own scan finds nothing new: the entries are already marked.
	task.defer(DataService.Replicate, player)
end

local function scan(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local newIds: { string } = {}
	local variants = ownedVariants(state)
	for _, entry in Index.Entries do
		if not state.Index.Seen[entry.Id] and isReached(state, entry, variants) then
			table.insert(newIds, entry.Id)
		end
	end
	markSeen(player, state, newIds)
end

-- BonkService: the player caught a golden stick.
function IndexService.DiscoverGolden(player: Player)
	local state = DataService.GetState(player)
	if state and not state.Index.Seen[Index.GoldenId] then
		markSeen(player, state, { Index.GoldenId })
	end
end

local function onClaimIndex(player: Player, entryId: unknown)
	if not RateLimiter.Allow(claimLimiter, player) or typeof(entryId) ~= "string" then
		return
	end
	local state = DataService.GetState(player)
	if not state or state.Index.Claimed[entryId] then
		return
	end
	local hits: number
	local name: string
	if entryId == Index.CompleteId then
		if not allSeen(state) then
			return
		end
		hits = Index.CompleteRewardHits
		name = "Shiba-Index complete"
	else
		local entry = Index.Get(entryId)
		if not entry or not state.Index.Seen[entryId] then
			return
		end
		hits = entry.RewardHits
		name = entry.DisplayName
	end
	state.Index.Claimed[entryId] = true
	local amount = RewardService.Hits(player, hits)
	-- AddPoints replicates the state (Claimed included).
	EconomyService.AddPoints(player, amount)
	NotifyService.Send(player, `{name}: +{Format.Money(amount)}`, "Good")
end

function IndexService.Start()
	Net.Get(Net.ClaimIndex).OnServerEvent:Connect(onClaimIndex)
	DataService.OnLoaded(function(player)
		scan(player)
	end)
	DataService.OnReplicated(scan)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(claimLimiter, player)
	end)
end

return IndexService
