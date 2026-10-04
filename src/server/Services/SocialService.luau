--!strict
-- Friend Boost + invite rewards (EconomyConfig.Social, docs/GAME_DESIGN.md → Friends and invites).
-- * Friend Boost: +PerFriend income per Roblox friend in this server (at most MaxFriends). Friendship is checked with
--   Player:IsFriendsWithAsync (yields, rate limited) once per pair when someone joins and cached until one of the two
--   leaves. RewardService.GetStickValue multiplies by GetFriendMultiplier; the client learns its boost through
--   FriendBoostChanged (friends, multiplier).
-- * Invite rewards: a player who joins through a friend's invite (Player:GetJoinData().ReferredByPlayerId) for the
--   first time gets InviteReward (Bonk Rain + Bonk Buddies trophy); the inviter gets the same, at most
--   MaxInviteRewardsPerWeek per week. An offline inviter's reward waits in the PendingStoreName DataStore (key =
--   inviter UserId) and is granted on their next join; rewards over the weekly cap wait in
--   state.Social.PendingInviteRewards until next week.
-- The invite prompt itself runs on the client (SocialController); no remote needed.
-- Requires no gameplay service that requires it back (RewardService requires this module).

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Net = require(ReplicatedStorage.Shared.Net)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local NotifyService = require(script.Parent.NotifyService)

local SOCIAL = EconomyConfig.Social
local SECONDS_PER_WEEK = 7 * 24 * 60 * 60
-- A pending counter in the DataStore never grows past this (protects against a flood of fake invites).
local MAX_STORED_PENDING = 100

local friendBoostChanged = Net.Get(Net.FriendBoostChanged)

-- "<smaller UserId>:<bigger UserId>" → are friends. Only pairs of players who are both in the server.
local friendPairs: { [string]: boolean } = {}
-- Friends in the server per player (before the MaxFriends cap), and the last value sent to the client.
local friendCounts: { [Player]: number } = {}
local sentCounts: { [Player]: number } = {}
-- Admin testing: extra pretend friends per player (friends need two real accounts; Studio test players are never
-- Roblox friends).
local fakeFriends: { [Player]: number } = {}
local pendingStore: DataStore? = nil

local SocialService = {}

local function pairKey(a: number, b: number): string
	return if a < b then `{a}:{b}` else `{b}:{a}`
end

local function thisWeek(): number
	return os.time() // SECONDS_PER_WEEK
end

-- Friends that count for the boost (MaxFriends cap applied).
local function countedFriends(player: Player): number
	return math.min((friendCounts[player] or 0) + (fakeFriends[player] or 0), SOCIAL.MaxFriends)
end

-- Income multiplier from friends in this server: 1 + PerFriend × friends (at most MaxFriends).
function SocialService.GetFriendMultiplier(player: Player): number
	return 1 + SOCIAL.PerFriend * countedFriends(player)
end

local function recount()
	local players = Players:GetPlayers()
	for _, player in players do
		local count = 0
		for _, other in players do
			if other ~= player and friendPairs[pairKey(player.UserId, other.UserId)] then
				count += 1
			end
		end
		friendCounts[player] = count
		local counted = countedFriends(player)
		if sentCounts[player] ~= counted then
			sentCounts[player] = counted
			friendBoostChanged:FireClient(player, counted, SocialService.GetFriendMultiplier(player))
		end
	end
end

-- Asks Roblox about every pair (newcomer, other player) not cached yet, then recounts everyone.
local function checkFriends(newcomer: Player)
	for _, other in Players:GetPlayers() do
		if other == newcomer or newcomer.Parent == nil then
			continue
		end
		local key = pairKey(newcomer.UserId, other.UserId)
		if friendPairs[key] == nil then
			local ok, result = pcall(function()
				return newcomer:IsFriendsWithAsync(other.UserId)
			end)
			if ok then
				friendPairs[key] = result == true
			else
				warn(`[SocialService] IsFriendsWithAsync failed: {result}`)
			end
		end
	end
	recount()
end

-- Starts a new reward week when the week changed.
local function rollWeek(state: Types.PlayerState)
	local week = thisWeek()
	if state.Social.InviteRewardsWeek ~= week then
		state.Social.InviteRewardsWeek = week
		state.Social.InviteRewardsThisWeek = 0
	end
end

-- Hands out InviteReward once (Bonk Rains + trophy). Does not replicate.
local function giveReward(state: Types.PlayerState)
	state.BonkRains = math.min(state.BonkRains + SOCIAL.InviteReward.BonkRains, 999)
	state.Trophies[SOCIAL.InviteReward.Trophy] = true
end

-- Grants the player's pending inviter rewards, as many as this week's cap allows. `friendName` names the friend in
-- the message when known.
local function grantPending(player: Player, friendName: string?)
	local state = DataService.GetState(player)
	if not state or state.Social.PendingInviteRewards <= 0 then
		return
	end
	rollWeek(state)
	local granted = 0
	while
		state.Social.PendingInviteRewards > 0
		and state.Social.InviteRewardsThisWeek < SOCIAL.MaxInviteRewardsPerWeek
	do
		state.Social.PendingInviteRewards -= 1
		state.Social.InviteRewardsThisWeek += 1
		giveReward(state)
		granted += 1
	end
	DataService.Replicate(player)
	if granted == 0 then
		NotifyService.Send(player, "Invite rewards for this week are used up: more next week!", "Info")
		return
	end
	local who = if friendName
		then `{friendName} joined`
		else if granted > 1 then "Friends joined" else "A friend joined"
	NotifyService.Send(
		player,
		`+{granted * SOCIAL.InviteReward.BonkRains} Bonk Rain! {who} through your invite. Bonk Buddies!`,
		"Good"
	)
	DataService.SaveNow(player)
end

-- Adds one pending inviter reward for an offline player (DataStore, claimed on their next join).
local function storePending(userId: number)
	local store = pendingStore
	if not store then
		return
	end
	local ok, message = pcall(function()
		store:UpdateAsync(tostring(userId), function(old: unknown)
			local count = if typeof(old) == "number" then old else 0
			return math.min(count + 1, MAX_STORED_PENDING)
		end)
	end)
	if not ok then
		warn(`[SocialService] Could not store a pending invite reward: {message}`)
	end
end

-- Moves the player's stored pending rewards into their save (only when that save will be kept).
local function takeStoredPending(player: Player, state: Types.PlayerState)
	local store = pendingStore
	if not store or not DataService.CanSave(player) then
		return
	end
	local taken = 0
	local ok, message = pcall(function()
		store:UpdateAsync(tostring(player.UserId), function(old: unknown)
			if typeof(old) ~= "number" or old <= 0 then
				taken = 0
				-- Nothing waiting: cancel the write.
				return nil
			end
			taken = math.min(math.floor(old), MAX_STORED_PENDING)
			return 0
		end)
	end)
	if not ok then
		warn(`[SocialService] Could not read pending invite rewards: {message}`)
		return
	end
	if taken > 0 then
		state.Social.PendingInviteRewards += taken
		-- Saved right away, so the rewards are not lost if the server stops before the next autosave.
		DataService.SaveNow(player)
	end
end

-- Credits the inviter with one reward: now if they are in this server, else via the DataStore.
local function creditInviter(inviterId: number, friendName: string)
	local inviter = Players:GetPlayerByUserId(inviterId)
	local state = if inviter then DataService.GetState(inviter) else nil
	if inviter and state then
		state.Social.PendingInviteRewards += 1
		grantPending(inviter, friendName)
	else
		storePending(inviterId)
	end
end

-- The invited player's one-time reward.
local function rewardInvited(player: Player, state: Types.PlayerState, inviterName: string)
	state.Social.ReferralRewarded = true
	giveReward(state)
	DataService.Replicate(player)
	NotifyService.Send(
		player,
		`+{SOCIAL.InviteReward.BonkRains} Bonk Rain! You joined through {inviterName}'s invite. Bonk Buddies!`,
		"Good"
	)
	DataService.SaveNow(player)
end

local function handleReferral(player: Player, state: Types.PlayerState)
	if state.Social.ReferralRewarded then
		return
	end
	-- GetJoinData's type in the definitions file lacks ReferredByPlayerId (a documented field), hence `any`.
	local joinData = player:GetJoinData() :: any
	local referrerId = if typeof(joinData) == "table" then joinData.ReferredByPlayerId else nil
	if typeof(referrerId) ~= "number" or referrerId <= 0 or referrerId == player.UserId then
		return
	end
	-- Only invites from real friends count (the invite prompt only offers friends anyway).
	local ok, isFriend = pcall(function()
		return player:IsFriendsWithAsync(referrerId)
	end)
	if not ok or isFriend ~= true or player.Parent == nil then
		return
	end
	local inviter = Players:GetPlayerByUserId(referrerId)
	local inviterName = if inviter then inviter.DisplayName else "a friend"
	rewardInvited(player, state, inviterName)
	creditInviter(referrerId, player.DisplayName)
end

local function onLoaded(player: Player, state: Types.PlayerState)
	rollWeek(state)
	takeStoredPending(player, state)
	grantPending(player, nil)
	handleReferral(player, state)
end

-- Admin testing: cycles the pretend friends 0 → 1 → … → MaxFriends → 0. Returns the new number.
function SocialService.CycleFakeFriends(player: Player): number
	local count = ((fakeFriends[player] or 0) + 1) % (SOCIAL.MaxFriends + 1)
	fakeFriends[player] = count
	recount()
	return count
end

-- Admin testing: plays both sides of an invite on the admin (invited reward + one inviter reward), ignoring the
-- once-per-account rule (the weekly inviter cap still applies).
function SocialService.FakeInvite(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	rewardInvited(player, state, "Test Friend")
	state.Social.PendingInviteRewards += 1
	grantPending(player, "Test Friend")
end

function SocialService.Init()
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(SOCIAL.PendingStoreName)
	end)
	if ok then
		pendingStore = result
	else
		warn(`[SocialService] DataStores unavailable, offline invite rewards are not kept: {result}`)
	end
end

function SocialService.Start()
	local function onPlayerAdded(player: Player)
		-- Everyone starts at no friends; the client hears it once the pairs are checked.
		friendCounts[player] = 0
		friendBoostChanged:FireClient(player, 0, 1)
		sentCounts[player] = 0
		checkFriends(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end
	Players.PlayerRemoving:Connect(function(player)
		friendCounts[player] = nil
		sentCounts[player] = nil
		fakeFriends[player] = nil
		for _, other in Players:GetPlayers() do
			friendPairs[pairKey(player.UserId, other.UserId)] = nil
		end
		-- PlayerRemoving fires while the player is still listed: recount without them.
		task.defer(recount)
	end)
	DataService.OnLoaded(onLoaded)
end

return SocialService
