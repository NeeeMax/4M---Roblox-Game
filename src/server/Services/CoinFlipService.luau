--!strict
-- Coin flips on the hub (Config/Hub → CoinFlip, Duel).
-- Against the house: bet a share of your Bonk Points on heads or tails, 50:50, win doubles the bet.
-- Duels: challenge another player for a fixed stake; if they accept, both pay, a fair coin picks the winner, who
-- gets both stakes. The server decides everything; clients only animate the coin.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)

local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local QuestService = require(script.Parent.QuestService)

local FLIP = Hub.CoinFlip
local DUEL = Hub.Duel

type Duel = {
	Id: number,
	Challenger: Player,
	Target: Player,
	Stake: number,
	ExpiresAt: number,
}

local flipLimiter = RateLimiter.New(2, 1)
local duelLimiter = RateLimiter.New(2, 1)
local random = Random.new()
local duels: { [number]: Duel } = {}
local nextDuelId = 1

local coinFlipResult = Net.Get(Net.CoinFlipResult)
local duelInvite = Net.Get(Net.DuelInvite)
local duelResult = Net.Get(Net.DuelResult)

local CoinFlipService = {}

local function flip(): "Heads" | "Tails"
	return if random:NextInteger(0, 1) == 0 then "Heads" else "Tails"
end

local function onCoinFlip(player: Player, fraction: unknown, side: unknown)
	if not RateLimiter.Allow(flipLimiter, player) then
		return
	end
	if typeof(fraction) ~= "number" or not table.find(FLIP.BetFractions, fraction) then
		return
	end
	if side ~= "Heads" and side ~= "Tails" then
		return
	end
	local bet = math.floor(EconomyService.GetPoints(player) * fraction)
	if bet < FLIP.MinBet then
		NotifyService.Send(player, `You need at least {FLIP.MinBet} Bonk Points to bet`, "Bad")
		return
	end
	if not EconomyService.TrySpend(player, bet) then
		return
	end
	local result = flip()
	local won = result == side
	if won then
		-- Winnings are a transfer, not new earnings: only the profit counts for the leaderboard.
		EconomyService.AddPoints(player, bet, false)
		EconomyService.AddPoints(player, bet)
		QuestService.Record(player, "CoinWin", 1)
	end
	coinFlipResult:FireClient(player, won, result, bet)
end

local function closeDuel(duel: Duel)
	duels[duel.Id] = nil
end

local function hasOpenDuel(player: Player): boolean
	for _, duel in duels do
		if duel.Challenger == player or duel.Target == player then
			return true
		end
	end
	return false
end

local function onDuelChallenge(player: Player, targetUserId: unknown, stake: unknown)
	if not RateLimiter.Allow(duelLimiter, player) then
		return
	end
	if typeof(targetUserId) ~= "number" or typeof(stake) ~= "number" or not table.find(DUEL.Stakes, stake) then
		return
	end
	local target = Players:GetPlayerByUserId(targetUserId)
	if not target or target == player then
		return
	end
	if hasOpenDuel(player) or hasOpenDuel(target) then
		NotifyService.Send(player, "One of you already has an open duel", "Bad")
		return
	end
	if EconomyService.GetPoints(player) < stake then
		NotifyService.Send(player, "Not enough Bonk Points for that stake", "Bad")
		return
	end
	local duel: Duel = {
		Id = nextDuelId,
		Challenger = player,
		Target = target,
		Stake = stake,
		ExpiresAt = os.clock() + DUEL.InviteTimeout,
	}
	nextDuelId += 1
	duels[duel.Id] = duel
	duelInvite:FireClient(target, duel.Id, player.DisplayName, stake)
	NotifyService.Send(player, `Duel request sent to {target.DisplayName}`, "Info")
end

local function onDuelRespond(player: Player, duelId: unknown, accept: unknown)
	if not RateLimiter.Allow(duelLimiter, player) or typeof(duelId) ~= "number" then
		return
	end
	local duel = duels[duelId]
	if not duel or duel.Target ~= player then
		return
	end
	closeDuel(duel)
	local challenger = duel.Challenger
	if accept ~= true then
		NotifyService.Send(challenger, `{player.DisplayName} declined the duel`, "Bad")
		return
	end
	if challenger.Parent == nil or os.clock() > duel.ExpiresAt then
		NotifyService.Send(player, "That duel has expired", "Bad")
		return
	end
	if EconomyService.GetPoints(challenger) < duel.Stake or EconomyService.GetPoints(player) < duel.Stake then
		NotifyService.Send(player, "Someone can't afford the stake anymore", "Bad")
		NotifyService.Send(challenger, "Someone can't afford the stake anymore", "Bad")
		return
	end
	EconomyService.TrySpend(challenger, duel.Stake)
	EconomyService.TrySpend(player, duel.Stake)
	-- Heads = the challenger wins.
	local side = flip()
	local winner = if side == "Heads" then challenger else player
	local loser = if winner == challenger then player else challenger
	EconomyService.AddPoints(winner, duel.Stake, false)
	EconomyService.AddPoints(winner, duel.Stake)
	QuestService.Record(winner, "CoinWin", 1)
	duelResult:FireClient(winner, true, loser.DisplayName, duel.Stake, side)
	duelResult:FireClient(loser, false, winner.DisplayName, duel.Stake, side)
	NotifyService.Send(winner, `You won {Format.Number(duel.Stake)} from {loser.DisplayName}!`, "Good")
end

function CoinFlipService.Start()
	Net.Get(Net.CoinFlip).OnServerEvent:Connect(onCoinFlip)
	Net.Get(Net.DuelChallenge).OnServerEvent:Connect(onDuelChallenge)
	Net.Get(Net.DuelRespond).OnServerEvent:Connect(onDuelRespond)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(flipLimiter, player)
		RateLimiter.Remove(duelLimiter, player)
		for _, duel in duels do
			if duel.Challenger == player or duel.Target == player then
				closeDuel(duel)
			end
		end
	end)
	-- Expired invites.
	task.spawn(function()
		while true do
			task.wait(1)
			local now = os.clock()
			for _, duel in duels do
				if now > duel.ExpiresAt then
					closeDuel(duel)
					NotifyService.Send(duel.Challenger, `{duel.Target.DisplayName} didn't answer the duel`, "Bad")
				end
			end
		end
	end)
end

return CoinFlipService
