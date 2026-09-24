--!strict
-- Detects when a projectile touches this player's character (as seen on screen) and reports it; the server
-- validates the report and decides about points (docs/decisions/0003). When the server confirms a hit, plays
-- the bonk effects: "+X BONK" popup, sound, and knockback (the client simulates its own character).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)

local ProjectileController = require(script.Parent.ProjectileController)

local BONK = Gameplay.Bonk
local COMBO = Gameplay.Combo
local HITS = Gameplay.Hits
local ISLAND = Gameplay.Island
local KNOCKBACK = Gameplay.Knockback
local PROJECTILES = Gameplay.Projectiles

local player = Players.LocalPlayer
local sound: Sound
-- Settings → Master × Effects (SettingsController).
local volumeScale = 1
local immuneUntil = 0
local comboLabel: TextLabel
local comboBar: Frame
-- Bumped by every combo update, so an older countdown knows it was replaced.
local comboVersion = 0
-- Projectiles already reported. Weak keys: removed markers drop out on their own.
local reported: { [BasePart]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include

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

local function showPopup(reward: number, quality: Economy.HitQualityDef, onHead: boolean, golden: boolean)
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
	local bonk = if onHead then "HEADBONK" else "BONK"
	local prefix = if golden then "GOLDEN " else ""
	if quality.Name ~= "Normal" then
		prefix ..= `{string.upper(quality.Name)} `
	end
	label.Text = if prefix == "" and not onHead
		then `+{Format.Number(reward)} BONK`
		else `{prefix}{bonk}! +{Format.Number(reward)}`
	if golden then
		label.TextColor3 = PROJECTILES.GoldenColor
	end
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

-- Stars bursting from the head, more for better hits.
local function burstStars(quality: Economy.HitQualityDef, tier: number)
	local character = player.Character
	local head = if character then character:FindFirstChild("Head") else nil
	if not head or not head:IsA("BasePart") then
		return
	end
	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(0, head.Size.Y / 2, 0)
	attachment.Parent = head
	local stars = Instance.new("ParticleEmitter")
	stars.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	stars.Color = ColorSequence.new(quality.Color)
	stars.LightEmission = 0.8
	stars.Size = NumberSequence.new(0.6, 0)
	stars.Lifetime = NumberRange.new(0.4, 0.8)
	stars.Speed = NumberRange.new(8, 14)
	stars.SpreadAngle = Vector2.new(180, 180)
	stars.Rotation = NumberRange.new(0, 360)
	stars.RotSpeed = NumberRange.new(-200, 200)
	stars.Enabled = false
	stars.Parent = attachment
	stars:Emit(BONK.Stars + BONK.StarsPerTier * (tier - 1))
	task.delay(1, function()
		attachment:Destroy()
	end)
end

-- A short camera shake for hard hits.
local function shakeCamera(tier: number)
	if tier < BONK.ShakeFromTier then
		return
	end
	local character = player.Character
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not humanoid then
		return
	end
	local strength = BONK.ShakeStrength * (tier - BONK.ShakeFromTier + 1)
	local started = os.clock()
	local connection: RBXScriptConnection
	connection = RunService.RenderStepped:Connect(function()
		local left = 1 - (os.clock() - started) / BONK.ShakeTime
		if left <= 0 or humanoid.Parent == nil then
			humanoid.CameraOffset = Vector3.zero
			connection:Disconnect()
			return
		end
		local amount = strength * left
		humanoid.CameraOffset = Vector3.new(math.random() * 2 - 1, math.random() * 2 - 1, math.random() * 2 - 1)
			* amount
	end)
end

local function buildComboDisplay()
	local gui = Instance.new("ScreenGui")
	gui.Name = "Combo"
	gui.ResetOnSpawn = false
	gui.Parent = player:WaitForChild("PlayerGui")

	comboLabel = Instance.new("TextLabel")
	comboLabel.AnchorPoint = Vector2.new(0.5, 0)
	comboLabel.Position = UDim2.new(0.5, 0, 0, 94)
	comboLabel.Size = UDim2.fromOffset(300, 36)
	comboLabel.BackgroundTransparency = 1
	comboLabel.Font = Enum.Font.FredokaOne
	comboLabel.TextScaled = true
	comboLabel.TextColor3 = Color3.fromRGB(255, 120, 60)
	comboLabel.TextStrokeTransparency = 0
	comboLabel.Visible = false
	comboLabel.Parent = gui

	local track = Instance.new("Frame")
	track.AnchorPoint = Vector2.new(0.5, 0)
	track.Position = UDim2.new(0.5, 0, 1, 2)
	track.Size = UDim2.new(0.8, 0, 0, 6)
	track.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
	track.BorderSizePixel = 0
	track.Parent = comboLabel

	comboBar = Instance.new("Frame")
	comboBar.Size = UDim2.fromScale(1, 1)
	comboBar.BackgroundColor3 = Color3.fromRGB(255, 120, 60)
	comboBar.BorderSizePixel = 0
	comboBar.Parent = track
end

-- Shows "COMBO xN ×M" with a bar that runs out when the combo ends (same rule as the server).
local function showCombo(combo: number, window: number)
	comboVersion += 1
	local version = comboVersion
	if combo < 2 then
		comboLabel.Visible = false
		return
	end
	local multiplier = math.min(1 + COMBO.Step * (combo - 1), COMBO.MaxMultiplier)
	comboLabel.Text = string.format("COMBO x%d  ×%.1f", combo, multiplier)
	comboLabel.Visible = true
	comboBar.Size = UDim2.fromScale(1, 1)
	TweenService:Create(comboBar, TweenInfo.new(window, Enum.EasingStyle.Linear), { Size = UDim2.fromScale(0, 1) })
		:Play()
	task.delay(window, function()
		if comboVersion == version then
			comboLabel.Visible = false
		end
	end)
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

-- True if this projectile can hit the local character right now (alive, not immune).
local function getHittableCharacter(): (Model?, BasePart?)
	if os.clock() < immuneUntil then
		return nil, nil
	end
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not character or not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return nil, nil
	end
	return character, root
end

-- Reports a touch if the drawn projectile overlaps the character. Returns true if it reported.
local function tryReport(
	entry: ProjectileController.Drawn,
	character: Model,
	root: BasePart,
	reportHit: RemoteEvent
): boolean
	local id = entry.Marker:GetAttribute(PROJECTILES.IdAttribute)
	-- Pickup sphere: the projectile's hit radius plus PickupPadding (the server adds the same padding).
	local pickupRadius = entry.Radius + HITS.PickupPadding
	if
		typeof(id) ~= "number"
		or (entry.Position - root.Position).Magnitude > pickupRadius + HITS.BroadPhaseDistance
	then
		return false
	end
	overlapParams.FilterDescendantsInstances = { character }
	local touching = Workspace:GetPartBoundsInRadius(entry.Position, pickupRadius, overlapParams)
	if #touching == 0 then
		return false
	end
	local onHead = false
	for _, part in touching do
		if part.Name == "Head" then
			onHead = true
		end
	end
	-- Same immunity as the server, so we don't report hits it would reject anyway.
	immuneUntil = os.clock() + HITS.ImmunityTime
	reportHit:FireServer(id, onHead)
	return true
end

local function update(projectileFolder: Instance, reportHit: RemoteEvent)
	local character, root = getHittableCharacter()
	if not character or not root then
		return
	end
	for _, entry in ProjectileController.GetCollectableIn(projectileFolder) do
		if not reported[entry.Marker] and tryReport(entry, character, root, reportHit) then
			reported[entry.Marker] = true
			-- One hit per check: immunity starts now.
			return
		end
	end
end

-- 0..1, scales the bonk sound (Settings menu).
function BonkController.SetVolumeScale(scale: number)
	volumeScale = math.clamp(scale, 0, 1)
	if sound then
		sound.Volume = BONK.SoundVolume * volumeScale
	end
end

function BonkController.Init()
	sound = Instance.new("Sound")
	sound.Name = "Bonk"
	sound.SoundId = BONK.SoundId
	sound.Volume = BONK.SoundVolume * volumeScale
	sound.Parent = SoundService
	buildComboDisplay()
end

function BonkController.Start()
	Net.Get(Net.BonkHit).OnClientEvent:Connect(
		function(
			reward: number,
			qualityName: string,
			direction: Vector3,
			onHead: boolean,
			combo: number,
			window: number,
			golden: boolean
		)
			local quality, tier = findQuality(qualityName)
			showPopup(reward, quality, onHead, golden == true)
			playSound(tier)
			burstStars(quality, tier)
			shakeCamera(tier)
			showCombo(combo, window)
			knockback(direction)
		end
	)

	task.spawn(function()
		local reportHit = Net.Get(Net.ReportHit)
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		local island = islands:WaitForChild(`{ISLAND.ModelPrefix}{player.UserId}`)
		local projectileFolder = island:WaitForChild("Projectiles")
		RunService.Heartbeat:Connect(function()
			update(projectileFolder, reportHit)
		end)
	end)
end

return BonkController
