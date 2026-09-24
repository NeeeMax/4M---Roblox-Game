--!strict
-- Offline Shiba Bank (docs/GAME_DESIGN.md → Offline Shiba Bank, Config/Economy → OfflineBank).
-- While playing: every SampleSeconds the earned Bonk Points (EconomyService.TakeIncomeSample) are smoothed into
-- state.Bank.IncomePerMinute. Every save stamps Bank.LastSeenAt. On join: the time away (≥ MinSeconds, capped at
-- MaxHours) × IncomePerMinute × Share is added to Bank.Pending and the client gets OfflineEarnings.
-- ClaimOffline(false) pays Pending; ClaimOffline(true) opens the "DoubleOffline" Robux product, whose grant
-- (ShopService.Grant) pays 2× Pending.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)
local ShopService = require(script.Parent.ShopService)
local UpgradeService = require(script.Parent.UpgradeService)

local BANK = Economy.OfflineBank
local DOUBLE_PRODUCT = "DoubleOffline"

local offlineEarnings = Net.Get(Net.OfflineEarnings)
local claimLimiter = RateLimiter.New(2, 1)

local OfflineService = {}

-- Highest believable earnings per minute right now: every throw of every active Shiba caught for MaxBonksPerThrow
-- normal bonks. Caps samples so coin-flip wins or gifts don't inflate the offline rate.
local function maxPerMinute(player: Player): number
	local throwsPerMinute = 60 / UpgradeService.GetFireInterval(player) * UpgradeService.GetActiveShooters(player)
	return throwsPerMinute * RewardService.GetHitValue(player) * BANK.MaxBonksPerThrow
end

local function sampleIncome(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local points, elapsed = EconomyService.TakeIncomeSample(player, BANK.MinSampleSeconds)
	if elapsed <= 0 then
		return
	end
	local perMinute = math.min(points / elapsed * 60, maxPerMinute(player))
	local bank = state.Bank
	-- The first sample sets the rate directly; later ones move it by Smoothing.
	bank.IncomePerMinute = if bank.IncomePerMinute <= 0
		then perMinute
		else bank.IncomePerMinute + BANK.Smoothing * (perMinute - bank.IncomePerMinute)
end

-- On join: turn the time away into pending earnings and tell the client.
local function onLoaded(player: Player, state: Types.PlayerState)
	local bank = state.Bank
	local now = os.time()
	if bank.LastSeenAt > 0 then
		local away = math.min(now - bank.LastSeenAt, BANK.MaxHours * 3600)
		if away >= BANK.MinSeconds then
			local earned = math.floor(bank.IncomePerMinute * away / 60 * BANK.Share)
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
		NotifyService.Send(player, `Your Shibas earned {Format.Number(paid)} Bonk Points while you were away!`, "Good")
	end
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
