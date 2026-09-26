--!strict
-- Owns every player's saved state: loads it on join, saves it on leave / every AutosaveInterval / on shutdown,
-- and sends it to the owning client (StateChanged). EconomyService and UpgradeService change the state;
-- nothing else does.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)
local Net = require(ReplicatedStorage.Shared.Net)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

type PlayerState = Types.PlayerState

type Session = {
	State: PlayerState,
	-- False when loading failed: the player can still play, but we never save,
	-- so a temporary DataStore outage can't overwrite their real progress with defaults.
	CanSave: boolean,
}

-- 2: economy rework (Rebirths, Tutorial, Bank.AutomationPerMinute, Basket/Intern levels). Version-1 saves are
-- migrated in stateFromSaved: nothing is lost, levels and Bonk Dollars are kept as they are.
-- 3: additive fields only (Social, Party: feat/social-party), filled with defaults for older saves; no logic depends on
-- the number.
-- 3: additive fields only, each with a default for older saves (no code depends on the number):
--    Shiba Variants: `Variants` (slots Normal, counters 0).
local SAVE_VERSION = 3

local stateChanged = Net.Get(Net.StateChanged)

local store: DataStore? = nil
local sessions: { [Player]: Session } = {}
local loadedCallbacks: { (Player, PlayerState) -> () } = {}
local replicatedCallbacks: { (Player) -> () } = {}
local savingCallbacks: { (Player, PlayerState) -> () } = {}

local DataService = {}

local function defaultState(): PlayerState
	local levels: { [string]: number } = {}
	for _, id in Upgrades.Order do
		levels[id] = 0
	end
	return {
		-- Exactly the price of the first purchase (EconomyConfig.StartingMoney): the NEW SHIBA pad in front of the spawn.
		BonkPoints = EconomyConfig.StartingMoney,
		TotalEarned = 0,
		UpgradeLevels = levels,
		ActiveShooters = Upgrades.GetValue("Shooters", 0),
		SpinDay = 0,
		SpinsUsed = 0,
		Boosts = {},
		Quests = { Day = 0, Ids = {}, Progress = {}, Claimed = {} },
		Streak = { Day = 0, Count = 0, ClaimedDay = 0 },
		Playtime = { Day = 0, Seconds = 0, Claimed = {} },
		Trophies = {},
		BonkRains = 0,
		FirstJoinAt = os.time(),
		StarterPackBought = false,
		Passes = {},
		Receipts = {},
		Bank = { LastSeenAt = 0, IncomePerMinute = 0, Pending = 0, PendingSeconds = 0, AutomationPerMinute = 0 },
		Obby = { LastRewardAt = 0, BestTime = 0 },
		Index = { Seen = {}, Claimed = {} },
		Settings = { Music = 0.5, Effects = 1, Hints = true },
		Rebirths = 0,
		Tutorial = { Step = 0, FirstBonkDone = false },
		-- Social + Bonk Party (feat/social-party).
		Social = {
			ReferralRewarded = false,
			InviteRewardsWeek = 0,
			InviteRewardsThisWeek = 0,
			PendingInviteRewards = 0,
		},
		Party = { Id = 0, Catches = 0, Claimed = false, Count = 0 },
		-- ===== Shiba Variants (save v3) =====
		Variants = { Slots = {}, RollsSinceRainbow = 0, RollsSinceHuge = 0, TotalRolls = 0 },
		-- ===== end Shiba Variants =====
	}
end

-- A copy of a saved-state table (nested tables copied too), for saving and for the client.
local function deepCopy<T>(value: T): T
	if typeof(value) ~= "table" then
		return value
	end
	local copy = {}
	for key, item in value :: any do
		copy[key] = deepCopy(item)
	end
	return copy :: any
end

local function isNumber(value: unknown): boolean
	-- `value == value` rejects NaN.
	return typeof(value) == "number" and value == value and value ~= math.huge and value ~= -math.huge
end

-- Saved data is never trusted blindly: unknown fields are dropped, numbers are clamped to valid ranges.
local function stateFromSaved(saved: unknown): PlayerState
	local state = defaultState()
	if typeof(saved) ~= "table" then
		return state
	end
	local data = saved :: { [string]: any }

	if isNumber(data.BonkPoints) then
		state.BonkPoints = math.max(0, math.floor(data.BonkPoints))
	end
	if isNumber(data.TotalEarned) then
		state.TotalEarned = math.max(0, math.floor(data.TotalEarned))
	end
	if isNumber(data.SpinDay) and isNumber(data.SpinsUsed) then
		state.SpinDay = data.SpinDay
		state.SpinsUsed = math.max(0, math.floor(data.SpinsUsed))
	end
	local streak = data.Streak
	if
		typeof(streak) == "table"
		and isNumber(streak.Day)
		and isNumber(streak.Count)
		and isNumber(streak.ClaimedDay)
	then
		state.Streak =
			{ Day = streak.Day, Count = math.clamp(math.floor(streak.Count), 0, 7), ClaimedDay = streak.ClaimedDay }
	end
	local playtime = data.Playtime
	if typeof(playtime) == "table" and isNumber(playtime.Day) and isNumber(playtime.Seconds) then
		local claimed = {}
		if typeof(playtime.Claimed) == "table" then
			for index, value in playtime.Claimed do
				if typeof(index) == "number" then
					claimed[index] = value == true
				end
			end
		end
		state.Playtime = { Day = playtime.Day, Seconds = math.max(0, playtime.Seconds), Claimed = claimed }
	end
	if typeof(data.Trophies) == "table" then
		for id, owned in data.Trophies do
			if typeof(id) == "string" and owned == true then
				state.Trophies[id] = true
			end
		end
	end
	if isNumber(data.BonkRains) then
		state.BonkRains = math.clamp(math.floor(data.BonkRains), 0, 999)
	end
	if isNumber(data.FirstJoinAt) then
		state.FirstJoinAt = data.FirstJoinAt
	end
	state.StarterPackBought = data.StarterPackBought == true
	-- Passes are re-checked with Roblox on join (ShopService); the saved copy only matters for Studio tests.
	if typeof(data.Passes) == "table" then
		for id, owned in data.Passes do
			if typeof(id) == "string" and owned == true then
				state.Passes[id] = true
			end
		end
	end
	local bank = data.Bank
	if typeof(bank) == "table" then
		state.Bank = {
			LastSeenAt = if isNumber(bank.LastSeenAt) then bank.LastSeenAt else 0,
			IncomePerMinute = if isNumber(bank.IncomePerMinute) then math.max(0, bank.IncomePerMinute) else 0,
			Pending = if isNumber(bank.Pending) then math.max(0, math.floor(bank.Pending)) else 0,
			PendingSeconds = if isNumber(bank.PendingSeconds) then math.max(0, bank.PendingSeconds) else 0,
			AutomationPerMinute = if isNumber(bank.AutomationPerMinute)
				then math.max(0, bank.AutomationPerMinute)
				else 0,
		}
	end
	local obby = data.Obby
	if typeof(obby) == "table" then
		state.Obby = {
			LastRewardAt = if isNumber(obby.LastRewardAt) then obby.LastRewardAt else 0,
			BestTime = if isNumber(obby.BestTime) then math.max(0, obby.BestTime) else 0,
		}
	end
	local savedIndex = data.Index
	if typeof(savedIndex) == "table" then
		if typeof(savedIndex.Seen) == "table" then
			for id, value in savedIndex.Seen do
				if typeof(id) == "string" and value == true then
					state.Index.Seen[id] = true
				end
			end
		end
		if typeof(savedIndex.Claimed) == "table" then
			for id, value in savedIndex.Claimed do
				if typeof(id) == "string" and value == true then
					state.Index.Claimed[id] = true
				end
			end
		end
	end
	local settings = data.Settings
	if typeof(settings) == "table" then
		state.Settings = {
			Music = if isNumber(settings.Music) then math.clamp(settings.Music, 0, 1) else 0.5,
			Effects = if isNumber(settings.Effects) then math.clamp(settings.Effects, 0, 1) else 1,
			Hints = settings.Hints ~= false,
		}
	end
	if typeof(data.Receipts) == "table" then
		for _, receipt in data.Receipts do
			if typeof(receipt) == "string" then
				table.insert(state.Receipts, receipt)
			end
		end
	end
	if typeof(data.Boosts) == "table" then
		for id, expiresAt in data.Boosts do
			if typeof(id) == "string" and isNumber(expiresAt) then
				state.Boosts[id] = expiresAt
			end
		end
	end
	local quests = data.Quests
	if typeof(quests) == "table" and isNumber(quests.Day) and typeof(quests.Ids) == "table" then
		local ids, progress, claimed = {}, {}, {}
		for index, id in quests.Ids do
			if typeof(id) == "string" then
				table.insert(ids, id)
				local value = if typeof(quests.Progress) == "table" then quests.Progress[index] else nil
				table.insert(progress, if isNumber(value) then math.max(0, value) else 0)
				table.insert(claimed, typeof(quests.Claimed) == "table" and quests.Claimed[index] == true)
			end
		end
		state.Quests = { Day = quests.Day, Ids = ids, Progress = progress, Claimed = claimed }
	end
	if typeof(data.UpgradeLevels) == "table" then
		for _, id in Upgrades.Order do
			local level = data.UpgradeLevels[id]
			if isNumber(level) then
				-- Shooters may go past MaxLevel with the +2 Shiba Slots pass.
				local bonus = if id == "Shooters" then Shop.Pass.ExtraShibas else 0
				state.UpgradeLevels[id] = math.clamp(math.floor(level), 0, Upgrades.Defs[id].MaxLevel + bonus)
			end
		end
	end
	if isNumber(data.Rebirths) then
		state.Rebirths = math.max(0, math.floor(data.Rebirths))
	end
	local tutorial = data.Tutorial
	if typeof(tutorial) == "table" then
		state.Tutorial = {
			Step = if isNumber(tutorial.Step) then math.max(0, math.floor(tutorial.Step)) else 0,
			FirstBonkDone = tutorial.FirstBonkDone == true,
		}
	elseif data.Version == nil or data.Version < 2 then
		-- Migration from version 1: players from before the rework already know the game, so no tutorial.
		state.Tutorial = { Step = 1000, FirstBonkDone = true }
	end
	-- ==== Social + Bonk Party (feat/social-party) ====
	local social = data.Social
	if typeof(social) == "table" then
		state.Social = {
			ReferralRewarded = social.ReferralRewarded == true,
			InviteRewardsWeek = if isNumber(social.InviteRewardsWeek) then math.floor(social.InviteRewardsWeek) else 0,
			InviteRewardsThisWeek = if isNumber(social.InviteRewardsThisWeek)
				then math.max(0, math.floor(social.InviteRewardsThisWeek))
				else 0,
			PendingInviteRewards = if isNumber(social.PendingInviteRewards)
				then math.clamp(math.floor(social.PendingInviteRewards), 0, 1000)
				else 0,
		}
	end
	local party = data.Party
	if typeof(party) == "table" then
		state.Party = {
			Id = if isNumber(party.Id) then math.floor(party.Id) else 0,
			Catches = if isNumber(party.Catches) then math.max(0, math.floor(party.Catches)) else 0,
			Claimed = party.Claimed == true,
			Count = if isNumber(party.Count) then math.max(0, math.floor(party.Count)) else 0,
		}
	end
	-- ==== end Social + Bonk Party ====
	-- ===== Shiba Variants (save v3; older saves keep the default: every slot Normal) =====
	local variants = data.Variants
	if typeof(variants) == "table" then
		if typeof(variants.Slots) == "table" then
			for slot, variant in variants.Slots do
				local index = if typeof(slot) == "string" then tonumber(slot) else nil
				local rank = if typeof(variant) == "string" then EconomyConfig.Variants.Rank[variant] else nil
				-- Slots 1 … 99 with a known, better-than-Normal variant (99: room for more slot passes later).
				if index and index == math.floor(index) and index >= 1 and index <= 99 and rank and rank > 0 then
					state.Variants.Slots[tostring(index)] = variant :: Types.VariantId
				end
			end
		end
		local function counter(value: unknown): number
			return if isNumber(value) then math.max(0, math.floor(value :: number)) else 0
		end
		state.Variants.RollsSinceRainbow = counter(variants.RollsSinceRainbow)
		state.Variants.RollsSinceHuge = counter(variants.RollsSinceHuge)
		state.Variants.TotalRolls = counter(variants.TotalRolls)
	end
	-- ===== end Shiba Variants =====
	local owned = Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters)
	state.ActiveShooters = owned
	if isNumber(data.ActiveShooters) then
		state.ActiveShooters = math.clamp(math.floor(data.ActiveShooters), 1, owned)
	end
	return state
end

-- Studio without API access or an unpublished place fails the same way every time; retrying only delays play.
local function isPermanentError(message: string): boolean
	return string.find(message, "403", 1, true) ~= nil
		or string.find(message, "publish", 1, true) ~= nil
		or string.find(message, "StudioAccessToApisNotAllowed", 1, true) ~= nil
		or string.find(message, "Studio access to APIs is not allowed", 1, true) ~= nil
end

-- Calls `attempt` up to DataStoreAttempts times with 1 s, 2 s, ... backoff. Returns success and the result.
local function withRetries(description: string, attempt: () -> unknown): (boolean, unknown)
	for try = 1, Economy.DataStoreAttempts do
		local ok, result = pcall(attempt)
		if ok then
			return true, result
		end
		local message = tostring(result)
		warn(`[DataService] {description} failed (try {try}): {message}`)
		if isPermanentError(message) or try == Economy.DataStoreAttempts then
			break
		end
		task.wait(2 ^ (try - 1))
	end
	return false, nil
end

local function save(player: Player, session: Session)
	local currentStore = store
	if not session.CanSave or not currentStore then
		return
	end
	for _, callback in savingCallbacks do
		callback(player, session.State)
	end
	local data = deepCopy(session.State) :: any
	data.Version = SAVE_VERSION
	withRetries(`Saving {player.Name}`, function()
		-- No session locking in MVP: the latest save wins.
		return currentStore:UpdateAsync(tostring(player.UserId), function()
			return data
		end)
	end)
end

local function onPlayerAdded(player: Player)
	local currentStore = store
	local loaded, saved = false, nil
	if currentStore then
		loaded, saved = withRetries(`Loading {player.Name}`, function()
			return currentStore:GetAsync(tostring(player.UserId))
		end)
	end
	if player.Parent == nil then
		-- Left while we were loading.
		return
	end
	if not loaded then
		warn(`[DataService] Playing without saving for {player.Name} this session.`)
	end

	local session: Session = {
		State = if loaded then stateFromSaved(saved) else defaultState(),
		CanSave = loaded,
	}
	sessions[player] = session
	DataService.Replicate(player)
	for _, callback in loadedCallbacks do
		task.spawn(callback, player, session.State)
	end
end

local function onPlayerRemoving(player: Player)
	local session = sessions[player]
	sessions[player] = nil
	if session then
		save(player, session)
	end
end

-- The player's state, or nil while it is still loading (or after they left).
-- Callers may change fields and must then call DataService.Replicate.
function DataService.GetState(player: Player): PlayerState?
	local session = sessions[player]
	return if session then session.State else nil
end

-- Runs `callback` once per player as soon as their data is loaded, including players already loaded.
function DataService.OnLoaded(callback: (Player, PlayerState) -> ())
	table.insert(loadedCallbacks, callback)
	for player, session in sessions do
		task.spawn(callback, player, session.State)
	end
end

-- Sends the player's current state to their client.
function DataService.Replicate(player: Player)
	local session = sessions[player]
	if not session then
		return
	end
	stateChanged:FireClient(player, deepCopy(session.State))
	for _, callback in replicatedCallbacks do
		callback(player)
	end
end

-- Runs `callback` after every state change of any player (e.g. to update the player list).
function DataService.OnReplicated(callback: (Player) -> ())
	table.insert(replicatedCallbacks, callback)
end

-- Runs `callback` right before every save of a player (leave, autosave, shutdown, SaveNow), so it can stamp fields
-- such as Bank.LastSeenAt. It must not yield.
function DataService.OnSaving(callback: (Player, PlayerState) -> ())
	table.insert(savingCallbacks, callback)
end

-- Saves right away (after Robux purchases), in the background.
function DataService.SaveNow(player: Player)
	local session = sessions[player]
	if session then
		task.spawn(save, player, session)
	end
end

-- ==== Social + Bonk Party (feat/social-party) ====
-- Whether this player's state will be saved (false while loading failed): SocialService only takes pending invite
-- rewards out of their DataStore key when they can be kept.
function DataService.CanSave(player: Player): boolean
	local session = sessions[player]
	return session ~= nil and session.CanSave and store ~= nil
end
-- ==== end Social + Bonk Party ====

-- Admin testing tool: puts the player back to a brand-new save (keeps TotalEarned for the leaderboard).
function DataService.Reset(player: Player)
	local session = sessions[player]
	if not session then
		return
	end
	local fresh = defaultState()
	fresh.TotalEarned = session.State.TotalEarned
	-- Robux purchases survive a reset: owned passes stay, and handled receipts must never be granted again.
	fresh.Passes = session.State.Passes
	fresh.Receipts = session.State.Receipts
	session.State = fresh
	DataService.Replicate(player)
	for _, callback in loadedCallbacks do
		task.spawn(callback, player, fresh)
	end
end

function DataService.Init()
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(Economy.DataStoreName)
	end)
	if ok then
		store = result
	else
		warn(`[DataService] DataStores unavailable, progress will not be saved: {result}`)
	end
end

function DataService.Start()
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end

	task.spawn(function()
		while true do
			task.wait(Economy.AutosaveInterval)
			for player, session in sessions do
				task.spawn(save, player, session)
			end
		end
	end)

	game:BindToClose(function()
		local pending = 0
		for player, session in sessions do
			pending += 1
			task.spawn(function()
				save(player, session)
				pending -= 1
			end)
		end
		while pending > 0 do
			task.wait()
		end
	end)
end

return DataService
