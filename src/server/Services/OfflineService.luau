--!strict
-- Offline Shiba Bank (docs/GAME_DESIGN.md → Offline Shiba Bank, Config/Economy → OfflineBank, EconomyConfig →
-- Automation). While playing: every SampleSeconds the Bonk Points earned by the player and by their automation
-- (EconomyService.TakeIncomeSample) are smoothed into state.Bank.IncomePerMinute and Bank.AutomationPerMinute.
-- Every save stamps Bank.LastSeenAt. On join: minutes away (≥ MinSeconds, capped at the basket's OfflineHours, or
-- NoBasketHours without a basket) × (OfflineShare × AutomationPerMinute + BaseOfflineShare × IncomePerMinute) is
-- added to Bank.Pending and the client gets OfflineEarnings.
-- ClaimOffline(false) pays Pending; ClaimOffline(true) opens the "DoubleOffline" Robux product, whose grant
-- (ShopService.Grant) pays 2× Pending.
-- Street mode (Features.Tycoon and Features.Street) has no popup and no basket: on join the time away (at most
-- EconomyConfig.Automation.StreetOfflineSeconds) is paid at StreetOfflineShare of the sampled income straight to the balance
-- (EconomyService.PayOffline) and the player gets a "Welcome back" toast through NotifyService. Bank.Pending stays 0.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Features = require(ReplicatedStorage.Shared.Config.Features)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)
local ShopService = require(script.Parent.ShopService)
local UpgradeService = require(script.Parent.UpgradeService)

local BANK = Economy.OfflineBank
local AUTOMATION = EconomyConfig.Automation
local DOUBLE_PRODUCT = "DoubleOffline"
local STREET = Features.Tycoon and Features.Street
-- The "Welcome back" toast waits this long after the load so the client's notify listener exists (seconds).
local WELCOME_DELAY = 4

local offlineEarnings = Net.Get(Net.OfflineEarnings)
local claimLimiter = RateLimiter.New(2, 1)

local OfflineService = {}

-- Street mode: highest believable income per minute right now: what the equipped Shibas earn per second (TycoonMath.TotalIncome
-- with the player's multipliers) × 60 × StreetSampleCap. Payments that are not Shiba income (quests, spins, gifts) can't inflate
-- the offline rate beyond it, and neither can a spike before the player leaves.
local function streetMaxPerMinute(player: Player, state: Types.PlayerState): number
	local tycoon = state.Tycoon
	if not tycoon then
		return 0
	end
	local perSecond = TycoonMath.TotalIncome(tycoon) * RewardService.GetIncomeMultiplier(player)
	return perSecond * 60 * AUTOMATION.StreetSampleCap
end

-- Highest believable earnings per minute right now: every throw of every active Shiba caught for MaxBonksPerThrow
-- normal bonks. Caps samples so coin-flip wins or gifts don't inflate the offline rate. Throws are counted before
-- the stick density cap (capped throws × their ValueMultiplier), which is what they pay.
local function maxPerMinute(player: Player): number
	if STREET then
		local state = DataService.GetState(player)
		return if state then streetMaxPerMinute(player, state) else 0
	end
	local throwsPerSecond, valueMultiplier = UpgradeService.GetThrowRate(player)
	local throwsPerMinute = 60 * throwsPerSecond * valueMultiplier
	return throwsPerMinute * RewardService.GetHitValue(player) * BANK.MaxBonksPerThrow
end

-- The first sample sets a rate directly; later ones move it by Smoothing.
local function smooth(rate: number, sample: number): number
	return if rate <= 0 then sample else rate + BANK.Smoothing * (sample - rate)
end

local function sampleIncome(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local points, automation, elapsed = EconomyService.TakeIncomeSample(player, BANK.MinSampleSeconds)
	if elapsed <= 0 then
		return
	end
	local cap = maxPerMinute(player)
	local bank = state.Bank
	bank.IncomePerMinute = smooth(bank.IncomePerMinute, math.min(points / elapsed * 60, cap))
	bank.AutomationPerMinute = smooth(bank.AutomationPerMinute, math.min(automation / elapsed * 60, cap))
end

-- Longest absence that still pays, in hours: the basket's OfflineHours (EconomyConfig → Automation).
local function offlineHours(state: Types.PlayerState): number
	local basket = state.UpgradeLevels.Basket or 0
	return if basket > 0
		then AUTOMATION.Basket.OfflineHours[basket] or AUTOMATION.NoBasketHours
		else AUTOMATION.NoBasketHours
end

-- Bonk Points per minute away: mostly the automation's rate, plus a small share of the player's own.
local function offlinePerMinute(state: Types.PlayerState): number
	return AUTOMATION.OfflineShare * state.Bank.AutomationPerMinute
		+ AUTOMATION.BaseOfflineShare * state.Bank.IncomePerMinute
end

-- Street mode, on join: pays the time away once and stamps the new LastSeenAt. The away time is clamped to [0, StreetOfflineSeconds]
-- (a LastSeenAt in the future or a stale one can't pay more), and the rate to what the Shibas can earn now. A Pending left over
-- from the days when the street could not pay it is dropped, not paid (it was filled with the old island numbers).
local function payAwayStreet(player: Player, state: Types.PlayerState)
	local bank = state.Bank
	local now = os.time()
	local lastSeen = bank.LastSeenAt
	-- Counted from now on: a rejoin can only be paid for the time since this stamp, and the stamp is saved with the payout.
	bank.LastSeenAt = now
	bank.Pending = 0
	bank.PendingSeconds = 0
	local away = 0
	if lastSeen > 0 then
		away = math.clamp(now - lastSeen, 0, AUTOMATION.StreetOfflineSeconds)
	end
	local earned = 0
	if away >= BANK.MinSeconds then
		local rate = math.min(bank.IncomePerMinute, streetMaxPerMinute(player, state))
		earned = math.floor(AUTOMATION.StreetOfflineShare * rate * away / 60)
	end
	if earned > 0 then
		bank.Pending = earned
		bank.PendingSeconds = away
		local paid = EconomyService.PayOffline(player, 1)
		if paid > 0 then
			task.delay(WELCOME_DELAY, function()
				if player.Parent == Players then
					NotifyService.Send(player, `Welcome back! +{Format.Money(paid)} while you were away`, "Good")
				end
			end)
		end
	end
	DataService.Replicate(player)
	if earned > 0 then
		-- Saved right away so a crash or a quick rejoin can't pay the same absence twice.
		DataService.SaveNow(player)
	end
end

-- On join: turn the time away into pending earnings and tell the client.
local function onLoaded(player: Player, state: Types.PlayerState)
	if STREET then
		payAwayStreet(player, state)
		return
	end
	local bank = state.Bank
	local now = os.time()
	if bank.LastSeenAt > 0 then
		local away = math.min(now - bank.LastSeenAt, offlineHours(state) * 3600)
		if away >= BANK.MinSeconds then
			local earned = math.floor(offlinePerMinute(state) * away / 60)
			if earned > 0 then
				bank.Pending += earned
				bank.PendingSeconds += away
			end
		end
	end
	-- Counted from now on, so a rejoin within the same session can't earn the same time twice.
	bank.LastSeenAt = now
	DataService.Replicate(player)
	if bank.Pending > 0 then
		offlineEarnings:FireClient(player, bank.Pending, bank.PendingSeconds)
	end
end

local function onClaimOffline(player: Player, double: unknown)
	if not RateLimiter.Allow(claimLimiter, player) or typeof(double) ~= "boolean" then
		return
	end
	local state = DataService.GetState(player)
	if not state or state.Bank.Pending <= 0 then
		return
	end
	if double then
		-- Pays 2× in ShopService.Grant once Roblox confirms the purchase; Pending stays until then.
		ShopService.BuyProduct(player, DOUBLE_PRODUCT)
		return
	end
	local paid = EconomyService.PayOffline(player, 1)
	if paid > 0 then
		NotifyService.Send(player, `Your Shibas earned {Format.Money(paid)} while you were away!`, "Good")
	end
end

-- Admin testing tool: pretends the player was away for `seconds` (with at least 10 bonks per minute of own income
-- and 5 of automation income), so the Welcome Back popup shows without leaving the game.
function OfflineService.SimulateAway(player: Player, seconds: number)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Bank.IncomePerMinute = math.max(state.Bank.IncomePerMinute, RewardService.Hits(player, 10))
	state.Bank.AutomationPerMinute = math.max(state.Bank.AutomationPerMinute, RewardService.Hits(player, 5))
	state.Bank.LastSeenAt = os.time() - seconds
	onLoaded(player, state)
end

function OfflineService.Start()
	Net.Get(Net.ClaimOffline).OnServerEvent:Connect(onClaimOffline)
	DataService.OnLoaded(onLoaded)
	DataService.OnSaving(function(_player, state)
		state.Bank.LastSeenAt = os.time()
	end)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(claimLimiter, player)
	end)
	task.spawn(function()
		while true do
			task.wait(BANK.SampleSeconds)
			for _, player in Players:GetPlayers() do
				sampleIncome(player)
			end
		end
	end)
end

return OfflineService
