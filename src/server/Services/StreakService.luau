--!strict
-- Reasons to come back and to stay (Config/Hub → LoginStreak, Playtime):
-- * Login streak: joining on consecutive UTC days moves through a 7-day reward cycle; missing a day starts over.
--   Each login day's reward is claimed once (ClaimStreak).
-- * Playtime gifts: minutes played per UTC day unlock gifts (ClaimPlaytime).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)

local STREAK = Hub.LoginStreak.Rewards
local GIFTS = Hub.Playtime.Gifts
local SECONDS_PER_DAY = 24 * 60 * 60
local TICK = 5

local claimLimiter = RateLimiter.New(5, 1)

local StreakService = {}

local function today(): number
	return os.time() // SECONDS_PER_DAY
end

local function freshPlaytime(day: number): Types.PlaytimeState
	local claimed = {}
	for index in GIFTS do
		claimed[index] = false
	end
	return { Day = day, Seconds = 0, Claimed = claimed }
end

-- Moves the streak on for today's login. Returns true if anything changed.
local function updateStreak(state: Types.PlayerState): boolean
	local day = today()
	local streak = state.Streak
	if streak.Day == day then
		return false
	end
	if streak.Day == day - 1 and streak.Count < #STREAK then
		streak.Count += 1
	else
		-- Missed a day, first login ever, or the 7-day cycle is complete.
		streak.Count = 1
	end
	streak.Day = day
	return true
end

local function onClaimStreak(player: Player)
	if not RateLimiter.Allow(claimLimiter, player) then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	updateStreak(state)
	local streak = state.Streak
	if streak.ClaimedDay == streak.Day then
		return
	end
	streak.ClaimedDay = streak.Day
	local got = RewardService.Give(player, STREAK[streak.Count])
	DataService.Replicate(player)
	NotifyService.Send(player, `Day {streak.Count} reward: {got}`, "Good")
end

local function onClaimPlaytime(player: Player, index: unknown)
	if not RateLimiter.Allow(claimLimiter, player) or typeof(index) ~= "number" then
		return
	end
	local state = DataService.GetState(player)
	local gift = GIFTS[index]
	if not state or not gift then
		return
	end
	local playtime = state.Playtime
	if playtime.Day ~= today() or playtime.Claimed[index] or playtime.Seconds < gift.Minutes * 60 then
		return
	end
	playtime.Claimed[index] = true
	local got = RewardService.Give(player, gift.Reward)
	DataService.Replicate(player)
	NotifyService.Send(player, `Playtime gift: {got}`, "Good")
end

-- Counts play time and tells the player when a gift unlocks.
local function tick()
	local day = today()
	for _, player in Players:GetPlayers() do
		local state = DataService.GetState(player)
		if not state then
			continue
		end
		local changed = updateStreak(state)
		if state.Playtime.Day ~= day then
			state.Playtime = freshPlaytime(day)
			changed = true
		end
		local before = state.Playtime.Seconds
		state.Playtime.Seconds += TICK
		for _, gift in GIFTS do
			local unlockAt = gift.Minutes * 60
			if before < unlockAt and state.Playtime.Seconds >= unlockAt then
				NotifyService.Send(player, `Playtime gift unlocked: {gift.Reward.Text}! Open GIFTS`, "Good")
				changed = true
			end
		end
		-- Replicate at least once a minute so the gift timers on the client stay right.
		if changed or state.Playtime.Seconds % 60 == 0 then
			DataService.Replicate(player)
		end
	end
end

-- Admin testing tool: unlocks all gifts and makes the streak reward claimable again.
function StreakService.Reset(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Playtime = freshPlaytime(today())
	state.Playtime.Seconds = GIFTS[#GIFTS].Minutes * 60
	state.Streak.ClaimedDay = 0
	DataService.Replicate(player)
end

function StreakService.Start()
	Net.Get(Net.ClaimStreak).OnServerEvent:Connect(onClaimStreak)
	Net.Get(Net.ClaimPlaytime).OnServerEvent:Connect(onClaimPlaytime)
	DataService.OnLoaded(function(player, state)
		local changed = updateStreak(state)
		if state.Playtime.Day ~= today() then
			state.Playtime = freshPlaytime(today())
			changed = true
		end
		if changed then
			DataService.Replicate(player)
		end
		if state.Streak.ClaimedDay ~= state.Streak.Day then
			NotifyService.Send(player, `Login streak day {state.Streak.Count}! Claim your gift in GIFTS`, "Good")
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(claimLimiter, player)
	end)
	task.spawn(function()
		while true do
			task.wait(TICK)
			tick()
		end
	end)
end

return StreakService
