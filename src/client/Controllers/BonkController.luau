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

local BONK = Gameplay.Bonk
local HITS = Gameplay.Hits
local ISLAND = Gameplay.Island
local KNOCKBACK = Gameplay.Knockback
local PROJECTILES = Gameplay.Projectiles

local player = Players.LocalPlayer
local sound: Sound
local immuneUntil = 0
-- Per-projectile client state. Weak keys: destroyed projectiles drop out on their own.
type Tracked = {
	Reported: boolean,
	Hidden: boolean,
	LastY: number?,
	Falling: boolean,
	-- Bounces seen on this client so far.
	Bounces: number,
}
local tracked: { [BasePart]: Tracked } = setmetatable({}, { __mode = "k" }) :: any
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

-- Reports a touch if the projectile overlaps the character. Returns true if it reported.
local function tryReport(part: BasePart, character: Model, root: BasePart, reportHit: RemoteEvent): boolean
	local id = part:GetAttribute(PROJECTILES.IdAttribute)
	local radius = part.Size.X / 2
	if typeof(id) ~= "number" or (part.Position - root.Position).Magnitude > radius + HITS.BroadPhaseDistance then
		return false
	end
	overlapParams.FilterDescendantsInstances = { character }
	if #Workspace:GetPartBoundsInRadius(part.Position, radius, overlapParams) == 0 then
		return false
	end
	-- Same immunity as the server, so we don't report hits it would reject anyway.
	immuneUntil = os.clock() + HITS.ImmunityTime
	reportHit:FireServer(id)
	return true
end

local function hide(part: BasePart)
	part.LocalTransparencyModifier = 1
	for _, descendant in part:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.LocalTransparencyModifier = 1
		end
	end
end

-- Counts bounces as this client sees them (a low point near the ground where the projectile starts rising again)
-- and hides the projectile the moment it reaches the ground after its last bounce, or drops below the island.
local function updateVisibility(part: BasePart, state: Tracked)
	local y = part.Position.Y
	local bottom = y - part.Size.Y / 2
	local lastY = state.LastY
	if lastY then
		local nearGround = lastY - part.Size.Y / 2 <= ISLAND.SurfaceY + PROJECTILES.GroundTolerance
		if state.Falling and y > lastY and nearGround then
			state.Bounces += 1
		end
		state.Falling = y < lastY
	end
	state.LastY = y

	local landedForGood = state.Bounces >= PROJECTILES.Bounces
		and bottom <= ISLAND.SurfaceY + PROJECTILES.GroundTolerance
	if landedForGood or bottom < ISLAND.SurfaceY - PROJECTILES.GroundTolerance then
		state.Hidden = true
		hide(part)
	end
end

local function update(projectileFolder: Instance, reportHit: RemoteEvent)
	local character, root = getHittableCharacter()
	for _, part in projectileFolder:GetChildren() do
		if not part:IsA("BasePart") then
			continue
		end
		local state = tracked[part]
		if not state then
			state = { Reported = false, Hidden = false, Falling = true, Bounces = 0 }
			tracked[part] = state
		end
		if state.Hidden then
			continue
		end
		-- Hit check first, so a projectile landing right at the player's feet still counts. The server only
		-- accepts hits on the path the projectile has really travelled.
		if not state.Reported and character and root and tryReport(part, character, root, reportHit) then
			state.Reported = true
			character, root = nil, nil
		end
		updateVisibility(part, state)
	end
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
