--!strict
-- Bonk Rain (Config/Shop → BonkRain): for a few seconds sticks drop from the sky all over the owner's field.
-- Players collect Bonk Rains (shop, wheel, login streak, playtime gifts) and start one with UseBonkRain while they
-- stand on their island. Rain sticks follow the normal rules (bounces, golden chance, hit validation).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local DataService = require(script.Parent.DataService)
local IslandService = require(script.Parent.IslandService)
local NotifyService = require(script.Parent.NotifyService)
local ProjectileService = require(script.Parent.ProjectileService)

local CONFIG = Shop.BonkRain
local ISLAND = Gameplay.Island

local limiter = RateLimiter.New(2, 1)
local raining: { [Player]: boolean } = {}
local random = Random.new()
local rainStarted = Net.Get(Net.BonkRainStarted)

local RainService = {}

local function isOnOwnIsland(player: Player): boolean
	local island = IslandService.GetIsland(player)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not island or not root or not root:IsA("BasePart") then
		return false
	end
	local offset = root.Position - island.Center
	return Vector3.new(offset.X, 0, offset.Z).Magnitude <= ISLAND.ActiveDistance
end

local function rain(player: Player)
	raining[player] = true
	rainStarted:FireClient(player, CONFIG.Seconds)
	local total = math.floor(CONFIG.Seconds * CONFIG.Rate)
	for _ = 1, total do
		local island = IslandService.GetIsland(player)
		if not island or player.Parent == nil then
			break
		end
		local distance = ISLAND.TargetRadius * math.sqrt(random:NextNumber())
		local angle = random:NextNumber(0, 2 * math.pi)
		local radius = ProjectileService.GetDiameter(player) / 2
		local target = island.Center + Vector3.new(math.cos(angle) * distance, radius, math.sin(angle) * distance)
		local plan = ProjectileService.PlanDrop(player, target, CONFIG.DropHeight)
		if plan then
			ProjectileService.Fire(player, plan)
		end
		task.wait(1 / CONFIG.Rate)
	end
	raining[player] = nil
end

-- Starts one of the player's Bonk Rains if they are on their island and none is running. Returns whether it did.
function RainService.TryStart(player: Player): boolean
	local state = DataService.GetState(player)
	if not state or state.BonkRains <= 0 then
		return false
	end
	if raining[player] then
		NotifyService.Send(player, "A Bonk Rain is already falling!", "Info")
		return false
	end
	if not isOnOwnIsland(player) then
		NotifyService.Send(player, "Go to your island to start the Bonk Rain!", "Info")
		return false
	end
	state.BonkRains -= 1
	DataService.Replicate(player)
	task.spawn(rain, player)
	return true
end

-- Admin testing tool.
function RainService.Give(player: Player)
	local state = DataService.GetState(player)
	if state then
		state.BonkRains += 1
		DataService.Replicate(player)
	end
end

function RainService.Start()
	Net.Get(Net.UseBonkRain).OnServerEvent:Connect(function(player)
		if RateLimiter.Allow(limiter, player) then
			RainService.TryStart(player)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		raining[player] = nil
		RateLimiter.Remove(limiter, player)
	end)
end

return RainService
