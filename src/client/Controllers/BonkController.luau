--!strict
-- Client-side bonk effects when the server confirms a hit: "+X BONK" popup, sound, and knockback.
-- Knockback runs here because the client simulates its own character; points are decided on the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)

local BONK = Gameplay.Bonk
local KNOCKBACK = Gameplay.Knockback

local player = Players.LocalPlayer
local sound: Sound

local BonkController = {}

-- Returns the quality's definition and its tier (1 = Normal).
local function findQuality(name: string): (Economy.HitQualityDef, number)
	for index, quality in Economy.HitQualities do
		if quality.Name == name then
			return quality, index
		end
	end
	return Economy.HitQualities[1], 1
end

local function showPopup(reward: number, quality: Economy.HitQualityDef)
	local character = player.Character
	local head = if character then character:FindFirstChild("Head") else nil
	if not head or not head:IsA("BasePart") then
		return
	end

	local billboard = Instance.new("BillboardGui")
	billboard.Adornee = head
	billboard.AlwaysOnTop = true
	billboard.Size = UDim2.fromOffset(320, 60)
	billboard.StudsOffset = Vector3.new(0, 2.5, 0)

	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = quality.Color
	label.TextStrokeTransparency = 0
	label.Text = if quality.Name == "Normal"
		then `+{Format.Number(reward)} BONK`
		else `{string.upper(quality.Name)} BONK! +{Format.Number(reward)}`
	label.Parent = billboard
	-- In PlayerGui so only this player sees it.
	billboard.Parent = player:WaitForChild("PlayerGui")

	local tweenInfo = TweenInfo.new(BONK.PopupTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(billboard, tweenInfo, { StudsOffset = Vector3.new(0, 2.5 + BONK.PopupRise, 0) }):Play()
	TweenService:Create(label, tweenInfo, { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
	task.delay(BONK.PopupTime, function()
		billboard:Destroy()
	end)
end

local function playSound(tier: number)
	sound.PlaybackSpeed = 1 + BONK.PitchStepPerTier * (tier - 1)
	SoundService:PlayLocalSound(sound)
end

local function knockback(direction: Vector3)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not root or not root:IsA("BasePart") then
		return
	end
	local attachment = Instance.new("Attachment")
	attachment.Parent = root
	local push = Instance.new("LinearVelocity")
	push.Attachment0 = attachment
	push.RelativeTo = Enum.ActuatorRelativeTo.World
	push.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
	push.MaxForce = math.huge
	push.VectorVelocity = direction * KNOCKBACK.HorizontalSpeed + Vector3.yAxis * KNOCKBACK.UpSpeed
	push.Parent = root
	task.delay(KNOCKBACK.Duration, function()
		push:Destroy()
		attachment:Destroy()
	end)
end

function BonkController.Init()
	sound = Instance.new("Sound")
	sound.Name = "Bonk"
	sound.SoundId = BONK.SoundId
	sound.Volume = BONK.SoundVolume
	sound.Parent = SoundService
end

function BonkController.Start()
	Net.Get(Net.BonkHit).OnClientEvent:Connect(function(reward: number, qualityName: string, direction: Vector3)
		local quality, tier = findQuality(qualityName)
		showPopup(reward, quality)
		playSound(tier)
		knockback(direction)
	end)
end

return BonkController
