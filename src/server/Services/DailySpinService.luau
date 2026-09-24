--!strict
-- The daily wheel (Config/Hub → DailySpin): FreeSpins per UTC day (VIP: Shop.Pass.VIPDailySpins). The server picks
-- the segment (weighted; the wheel shows every chance) and pays it out at once; the client only animates the wheel.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)
local Types = require(ReplicatedStorage.Shared.Types)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)

local CONFIG = Hub.DailySpin
local SECONDS_PER_DAY = 24 * 60 * 60

local spinLimiter = RateLimiter.New(2, 1)
local random = Random.new()
local spinResult = Net.Get(Net.SpinResult)

local DailySpinService = {}

local function today(): number
	return os.time() // SECONDS_PER_DAY
end

local function pickSegment(): number
	local total = 0
	for _, segment in CONFIG.Segments do
		total += segment.Weight
	end
	local roll = random:NextNumber(0, total)
	for index, segment in CONFIG.Segments do
		roll -= segment.Weight
		if roll <= 0 then
			return index
		end
	end
	return #CONFIG.Segments
end

function DailySpinService.SpinsPerDay(player: Player): number
	return if RewardService.HasPass(player, "VIP") then Shop.Pass.VIPDailySpins else CONFIG.FreeSpins
end

local function onRequestSpin(player: Player)
	if not RateLimiter.Allow(spinLimiter, player) then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	if state.SpinDay ~= today() then
		state.SpinDay = today()
		state.SpinsUsed = 0
	end
	if state.SpinsUsed >= DailySpinService.SpinsPerDay(player) then
		NotifyService.Send(player, "No spins left today, come back tomorrow!", "Bad")
		return
	end
	state.SpinsUsed += 1

	local index = pickSegment()
	local segment = CONFIG.Segments[index]
	local text: string
	if segment.Kind == "Boost" and segment.Boost and segment.Seconds then
		BoostService.Give(player, segment.Boost :: Types.BoostId, segment.Seconds)
		text = segment.Text
	elseif segment.Kind == "BonkRain" then
		state.BonkRains += 1
		text = "a Bonk Rain! Start it from your HUD"
	elseif segment.Kind == "Nothing" then
		text = "nothing this time"
	else
		local amount = RewardService.Hits(player, segment.Hits or 1)
		EconomyService.AddPoints(player, amount)
		text = `+{Format.Number(amount)} Bonk Points`
	end
	DataService.Replicate(player)
	spinResult:FireClient(player, index, text)
	QuestService.Record(player, "Spin", 1)
end

-- Admin testing tool.
function DailySpinService.ResetCooldown(player: Player)
	local state = DataService.GetState(player)
	if state then
		state.SpinsUsed = 0
		DataService.Replicate(player)
	end
end

function DailySpinService.Start()
	Net.Get(Net.RequestSpin).OnServerEvent:Connect(onRequestSpin)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(spinLimiter, player)
	end)
end

return DailySpinService
