--!strict
-- Shiba-Index (Config/Index, docs/GAME_DESIGN.md → Shiba-Index): marks entries as seen in state.Index.Seen once the
-- player reaches them, and pays each entry's one-time discovery reward when the player claims it (ClaimIndex).
-- * Shiba / projectile tiers: seen up to the current ShooterTier / ProjectileTier level (checked after every state
--   change, so tier skips, admin levels and old saves count too).
-- * Trophies: seen once owned.
-- * Golden stick: seen on the first golden catch (BonkService calls DiscoverGolden).
-- Seeing every entry unlocks the completion bonus (ClaimIndex(Index.CompleteId)).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Index = require(ReplicatedStorage.Shared.Config.Index)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)

local claimLimiter = RateLimiter.New(Index.MaxClaimsPerSecond, 1)

local IndexService = {}

local function isReached(state: Types.PlayerState, entry: Index.Entry): boolean
	if entry.Kind == "Shiba" then
		return (state.UpgradeLevels.ShooterTier or 0) >= entry.Level
	elseif entry.Kind == "Projectile" then
		return (state.UpgradeLevels.ProjectileTier or 0) >= entry.Level
	elseif entry.Kind == "Trophy" then
		return state.Trophies[entry.Trophy] == true
	end
	-- Golden: only DiscoverGolden marks it.
	return false
end

local function allSeen(state: Types.PlayerState): boolean
	for _, entry in Index.Entries do
		if not state.Index.Seen[entry.Id] then
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
	for _, entry in Index.Entries do
		if not state.Index.Seen[entry.Id] and isReached(state, entry) then
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
	NotifyService.Send(player, `{name}: +{Format.Number(amount)} Bonk Points`, "Good")
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
