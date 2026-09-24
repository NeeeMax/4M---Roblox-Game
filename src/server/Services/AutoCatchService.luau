--!strict
-- Auto-Catch game pass (Config/Shop → Passes "AutoCatch", Shop.Pass.AutoCatchRadius / AutoCatchInterval).
-- Every AutoCatchInterval seconds, for each owner: their live, unpaid projectiles whose current position on the
-- planned path is within AutoCatchRadius studs of the character are paid out like a Normal bonk (no head bonus,
-- combo counts) through BonkService.AwardHit. Only the server's own path and character position are used.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local BonkService = require(script.Parent.BonkService)
local IslandService = require(script.Parent.IslandService)
local ProjectileService = require(script.Parent.ProjectileService)
local RewardService = require(script.Parent.RewardService)

local PASS_ID = "AutoCatch"
local ID_ATTRIBUTE = Gameplay.Projectiles.IdAttribute
-- Auto-catches are gentle: no knockback direction (the client only does its small hop).
local NO_KNOCKBACK = Vector3.zero

local AutoCatchService = {}

local function normalQuality(): Economy.HitQualityDef
	for _, quality in Economy.HitQualities do
		if quality.Name == "Normal" then
			return quality
		end
	end
	return Economy.HitQualities[1]
end

local NORMAL = normalQuality()

local function catchFor(player: Player)
	local island = IslandService.GetIsland(player)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not island or not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return
	end
	local now = os.clock()
	for _, marker in island.ProjectileFolder:GetChildren() do
		local id = marker:GetAttribute(ID_ATTRIBUTE)
		local info = if typeof(id) == "number" then ProjectileService.GetById(id) else nil
		if info and info.Owner == player and not info.Paid then
			local age = now - info.LaunchedAt
			-- Only while it can still be collected by hand (flight, bounces, settling hops).
			if age <= ProjectilePath.GetCollectEndTime(info.Plan.Path) then
				local position = ProjectileService.GetState(info.Plan, age)
				if (position - root.Position).Magnitude <= Shop.Pass.AutoCatchRadius then
					BonkService.AwardHit(player, info, NORMAL, false, NO_KNOCKBACK)
				end
			end
		end
	end
end

function AutoCatchService.Start()
	task.spawn(function()
		while true do
			task.wait(Shop.Pass.AutoCatchInterval)
			for _, player in Players:GetPlayers() do
				if RewardService.HasPass(player, PASS_ID) then
					catchFor(player)
				end
			end
		end
	end)
end

return AutoCatchService
