--!strict
-- The daily wheel on the hub (Config/Hub → DailySpin): one free spin per Cooldown. The server picks the segment
-- (weighted) and pays it out at once; the client only animates the wheel to that segment.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)

local CONFIG = Hub.DailySpin

local spinLimiter = RateLimiter.New(2, 1)
local random = Random.new()
local spinResult = Net.Get(Net.SpinResult)

local DailySpinService = {}

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

local function onRequestSpin(player: Player)
	if not RateLimiter.Allow(spinLimiter, player) then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local now = os.time()
	local readyAt = state.LastSpinAt + CONFIG.Cooldown
	if now < readyAt then
		local minutes = math.ceil((readyAt - now) / 60)
		NotifyService.Send(player, `Next spin in {minutes // 60} h {minutes % 60} min`, "Bad")
		return
	end
	state.LastSpinAt = now

	local index = pickSegment()
	local segment = CONFIG.Segments[index]
	local text: string
	if segment.Kind == "Boost" and segment.Boost and segment.Seconds then
		BoostService.Give(player, segment.Boost :: Types.BoostId, segment.Seconds)
		text = segment.Text
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
		state.LastSpinAt = 0
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
