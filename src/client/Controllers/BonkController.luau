--!strict
-- Detects when a projectile touches this player's character (as seen on screen) and reports it; the server
-- validates the report and decides about points and the catch quality (docs/decisions/0003, 0005). When the server
-- confirms a hit, plays the bonk effects (Gameplay.Bonk): a popup per quality ("BONK +X", "AIR BONK! +X",
-- "PERFECT BONK!! +X"), sound pitched per quality, stars from the head, a coin burst from the character, an impact
-- burst in the projectile's tier colour, camera shake on better catches, the combo meter with tier names, the
-- first-bonk splash, and knockback (the client simulates its own character).

local ContentProvider = game:GetService("ContentProvider")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)
local ShibaEffects = require(ReplicatedStorage.Shared.Config.ShibaEffects)

local ProjectileController = require(script.Parent.ProjectileController)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local BONK = Gameplay.Bonk
local COINS = BONK.Coins
local COMBO = Gameplay.Combo
local HITS = Gameplay.Hits
local IMPACT = BONK.Impact
local ISLAND = Gameplay.Island
local KNOCKBACK = Gameplay.Knockback
local PROJECTILES = Gameplay.Projectiles
local STAR_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"
-- The popup floats this far above the head.
local POPUP_OFFSET = 2.5

type Juice = typeof(BONK.Qualities.Normal)

-- The projectile this client reported last, for the impact burst when the server confirms it.
type Reported = {
	Position: Vector3,
	Id: string,
	Golden: boolean,
	At: number,
}

local player = Players.LocalPlayer
local sound: Sound
-- Settings → Master × Effects (SettingsController).
local volumeScale = 1
local immuneUntil = 0
local comboScale: UIScale
local comboLabel: TextLabel
local comboTierLabel: TextLabel
local comboBar: Frame
local comboTier = 0
-- Bumped by every combo update, so an older countdown knows it was replaced.
local comboVersion = 0
local coinFolder: Folder
local liveCoins = 0
local lastReported: Reported? = nil
-- Projectiles already reported. Weak keys: removed markers drop out on their own.
local reported: { [BasePart]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local overlapParams = OverlapParams.new()
overlapParams.FilterType = Enum.RaycastFilterType.Include

local BonkController = {}

-- Returns the quality's definition and its juice (Gameplay.Bonk.Qualities); unknown names are Normal.
local function findQuality(name: string): (Economy.HitQualityDef, Juice)
	local qualities = BONK.Qualities :: { [string]: Juice }
	for _, quality in Economy.HitQualities do
		if quality.Name == name then
			return quality, qualities[quality.Name] or BONK.Qualities.Normal
		end
	end
	return Economy.HitQualities[1], BONK.Qualities.Normal
end

local function getHead(): BasePart?
	local character = player.Character
	local head = if character then character:FindFirstChild("Head") else nil
	return if head and head:IsA("BasePart") then head else nil
end

local function getRoot(): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

local function showPopup(reward: number, quality: Economy.HitQualityDef, juice: Juice, onHead: boolean, golden: boolean)
	local head = getHead()
	if not head then
		return
	end
	local size = UDim2.fromOffset(BONK.PopupWidth * juice.PopupScale, BONK.PopupHeight * juice.PopupScale)
	local billboard = Instance.new("BillboardGui")
	billboard.Adornee = head
	billboard.AlwaysOnTop = true
	billboard.Size = size
	billboard.StudsOffset = Vector3.new(0, POPUP_OFFSET, 0)

	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = if golden then PROJECTILES.GoldenColor else quality.Color
	label.TextStrokeTransparency = 0
	label.Parent = billboard
	-- "BONK" / "AIR BONK" / "PERFECT BONK"; head hits say HEADBONK.
	local name = if onHead then (string.gsub(quality.Label, "BONK", "HEADBONK")) else quality.Label
	local prefix = if golden then "GOLDEN " else ""
	-- The amount shows the Bonk Dollars symbol.
	Widgets.SetMoneyText(label, `{prefix}{name}{juice.Punctuation} +{Format.Money(reward)}`)
	-- In PlayerGui so only this player sees it.
	billboard.Parent = player:WaitForChild("PlayerGui")

	if juice.Bounce then
		-- Pops in big and springs back to its size.
		billboard.Size = UDim2.fromOffset(size.X.Offset * BONK.BounceScale, size.Y.Offset * BONK.BounceScale)
		TweenService:Create(
			billboard,
			TweenInfo.new(BONK.BounceTime, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			{ Size = size }
		):Play()
	end
	local tweenInfo = TweenInfo.new(BONK.PopupTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(billboard, tweenInfo, { StudsOffset = Vector3.new(0, POPUP_OFFSET + BONK.PopupRise, 0) }):Play()
	Widgets.FadeOut(label, BONK.PopupTime)
	task.delay(BONK.PopupTime, function()
		billboard:Destroy()
	end)
end

-- Plays a fresh copy of the bonk sound (Gameplay.Bonk.SoundId), so hits in quick succession overlap instead of
-- restarting (or re-pitching) one playing sound. Parented to SoundService: heard only here, not positional.
local function playSound(pitch: number)
	if BONK.SoundId == "" then
		return
	end
	local copy = sound:Clone()
	copy.PlaybackSpeed = pitch
	copy.Parent = SoundService
	copy.Ended:Once(function()
		copy:Destroy()
	end)
	copy:Play()
	-- Safety net if Ended never fires (asset failed to load); the sound is about 1 s long.
	task.delay(5, function()
		if copy.Parent then
			copy:Destroy()
		end
	end)
end

-- A one-shot particle burst of `count` particles at `parent` (an Attachment), cleaned up afterwards.
local function emitBurst(
	parent: Attachment,
	texture: string,
	color: Color3,
	count: number,
	size: number,
	speed: number,
	lifetime: number
)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = texture
	emitter.Color = ColorSequence.new(color)
	emitter.LightEmission = 0.8
	emitter.Size = NumberSequence.new(size, 0)
	emitter.Lifetime = NumberRange.new(lifetime * 0.6, lifetime)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-200, 200)
	emitter.Enabled = false
	emitter.Parent = parent
	emitter:Emit(count)
	task.delay(lifetime + 0.5, function()
		parent:Destroy()
	end)
end

-- Stars bursting from the head, more for better catches.
local function burstStars(color: Color3, count: number)
	local head = getHead()
	if not head or count <= 0 then
		return
	end
	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(0, head.Size.Y / 2, 0)
	attachment.Parent = head
	emitBurst(attachment, STAR_TEXTURE, color, count, 0.6, 14, 0.8)
end

-- Gold coins flying out of the character (local parts, simulated by this client), more for better catches.
local function burstCoins(count: number)
	local root = getRoot()
	if not root then
		return
	end
	local random = Random.new()
	for _ = 1, math.min(count, COINS.MaxCoins - liveCoins) do
		local coin = Instance.new("Part")
		coin.Name = "Coin"
		coin.Shape = Enum.PartType.Cylinder
		coin.Size = Vector3.new(COINS.Thickness, COINS.Diameter, COINS.Diameter)
		coin.Color = COINS.Color
		coin.Material = Enum.Material.Neon
		coin.CanCollide = false
		coin.CanQuery = false
		coin.CanTouch = false
		coin.CastShadow = false
		coin.Massless = true
		coin.CFrame = CFrame.new(root.Position + Vector3.new(0, 1, 0)) * CFrame.Angles(0, random:NextNumber(0, 6.28), 0)
		local out = Vector3.new(random:NextNumber(-1, 1), 0, random:NextNumber(-1, 1))
		out = if out.Magnitude > 1e-3 then out.Unit else Vector3.xAxis
		coin.AssemblyLinearVelocity = out * COINS.OutSpeed * random:NextNumber(0.4, 1)
			+ Vector3.yAxis * COINS.UpSpeed * random:NextNumber(0.6, 1)
		coin.AssemblyAngularVelocity = random:NextUnitVector() * 20
		coin.Parent = coinFolder
		liveCoins += 1
		TweenService:Create(
			coin,
			TweenInfo.new(COINS.Lifetime, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
			{ Transparency = 1 }
		):Play()
		task.delay(COINS.Lifetime, function()
			liveCoins -= 1
			coin:Destroy()
		end)
	end
end

-- The built-in particle texture (ShibaEffects.Textures) named in Gameplay.Bonk.Impact.Textures for this projectile.
local function impactTexture(projectileId: string): string
	local name = IMPACT.Textures[projectileId] or "Sparkles"
	for key, texture in ShibaEffects.Textures do
		if key == name then
			return texture
		end
	end
	return STAR_TEXTURE
end

-- Burst where the projectile hit, in its tier colour, bigger for better throwables (Gameplay.Bonk.Impact).
local function burstImpact(hit: Reported)
	local tier = table.find(Projectiles.Tiers, hit.Id) or 1
	local def = Projectiles.Defs[hit.Id]
	local color = if hit.Golden then PROJECTILES.GoldenColor elseif def then def.Color else Color3.new(1, 1, 1)
	local texture = impactTexture(hit.Id)
	local attachment = Instance.new("Attachment")
	attachment.Position = hit.Position
	attachment.Parent = Workspace.Terrain
	emitBurst(
		attachment,
		texture,
		color,
		IMPACT.Particles + IMPACT.PerTier * (tier - 1),
		IMPACT.Size + IMPACT.SizePerTier * (tier - 1),
		IMPACT.Speed,
		IMPACT.Lifetime
	)
end

-- A short camera shake of `strength` studs, fading out over ShakeTime.
local function shakeCamera(strength: number)
	if strength <= 0 then
		return
	end
	local character = player.Character
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not humanoid then
		return
	end
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

local function newLabel(name: string, parent: Instance): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = BONK.ComboColor
	label.TextStrokeTransparency = 0
	label.Parent = parent
	return label
end

local function buildComboDisplay()
	local gui = Instance.new("ScreenGui")
	gui.Name = "Combo"
	gui.ResetOnSpawn = false
	gui.Parent = player:WaitForChild("PlayerGui")

	local meter = Instance.new("Frame")
	meter.Name = "ComboMeter"
	meter.AnchorPoint = Vector2.new(0.5, 0)
	meter.Position = UDim2.new(0.5, 0, 0, 90)
	meter.Size = UDim2.fromOffset(380, 84)
	meter.BackgroundTransparency = 1
	meter.Visible = false
	meter.Parent = gui
	comboScale = Instance.new("UIScale")
	comboScale.Parent = meter

	comboLabel = newLabel("Count", meter)
	comboLabel.Size = UDim2.new(1, 0, 0, 44)

	local track = Instance.new("Frame")
	track.AnchorPoint = Vector2.new(0.5, 0)
	track.Position = UDim2.new(0.5, 0, 0, 46)
	track.Size = UDim2.new(0.8, 0, 0, 8)
	track.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
	track.BorderSizePixel = 0
	track.Parent = meter
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(1, 0)
	corner.Parent = track

	comboBar = Instance.new("Frame")
	comboBar.Size = UDim2.fromScale(1, 1)
	comboBar.BackgroundColor3 = BONK.ComboColor
	comboBar.BorderSizePixel = 0
	comboBar.Parent = track
	corner:Clone().Parent = comboBar

	comboTierLabel = newLabel("Tier", meter)
	comboTierLabel.Position = UDim2.fromOffset(0, 56)
	comboTierLabel.Size = UDim2.new(1, 0, 0, 28)
	comboTierLabel.Visible = false
end

-- The highest combo tier (Gameplay.Bonk.ComboTiers) reached at this multiplier: its index (0 = none) and def.
local function findComboTier(multiplier: number): (number, typeof(BONK.ComboTiers[1])?)
	local index = 0
	for candidate, tier in BONK.ComboTiers do
		if multiplier >= tier.Multiplier - 1e-6 then
			index = candidate
		end
	end
	return index, BONK.ComboTiers[index]
end

-- Shows "COMBO xN ×M" (and the tier name) with a bar that runs out when the combo ends (same rule as the server).
local function showCombo(combo: number, window: number)
	comboVersion += 1
	local version = comboVersion
	local meter = comboLabel.Parent :: Frame
	if combo < 2 then
		meter.Visible = false
		comboTier = 0
		return
	end
	local multiplier = math.min(1 + COMBO.Step * (combo - 1), COMBO.MaxMultiplier)
	local tierIndex, tier = findComboTier(multiplier)
	local color = if tier then tier.Color else BONK.ComboColor
	comboLabel.Text = string.format("COMBO x%d  ×%.1f", combo, multiplier)
	comboLabel.TextColor3 = color
	comboBar.BackgroundColor3 = color
	comboTierLabel.Visible = tier ~= nil
	if tier then
		comboTierLabel.Text = `{tier.Name}!`
		comboTierLabel.TextColor3 = color
	end
	meter.Visible = true
	if tierIndex > comboTier then
		-- New tier: punch the meter.
		comboScale.Scale = BONK.ComboPunchScale
		TweenService:Create(
			comboScale,
			TweenInfo.new(BONK.ComboPunchTime, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			{ Scale = 1 }
		):Play()
	end
	comboTier = tierIndex
	comboBar.Size = UDim2.fromScale(1, 1)
	TweenService:Create(comboBar, TweenInfo.new(window, Enum.EasingStyle.Linear), { Size = UDim2.fromScale(0, 1) })
		:Play()
	task.delay(window, function()
		if comboVersion == version then
			meter.Visible = false
			comboTier = 0
		end
	end)
end

-- "FIRST BONK! ×10" in the middle of the screen: pops in, holds, fades out.
local function showFirstBonk()
	local config = BONK.FirstBonk
	local gui = Instance.new("ScreenGui")
	gui.Name = "FirstBonk"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 20
	local label = Instance.new("TextLabel")
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5, 0.38)
	label.Size = UDim2.fromScale(0.7, 0.16)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = config.Color
	label.TextStrokeTransparency = 0
	label.Text = `{config.Text} ×{EconomyConfig.Bonk.FirstBonkMultiplier}`
	label.Parent = gui
	local scale = Instance.new("UIScale")
	scale.Scale = 0.2
	scale.Parent = label
	gui.Parent = player:WaitForChild("PlayerGui")
	TweenService:Create(scale, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
		:Play()
	local fadeTime = math.min(0.6, config.Time / 3)
	task.delay(config.Time - fadeTime, function()
		Widgets.FadeOut(label, fadeTime)
	end)
	task.delay(config.Time, function()
		gui:Destroy()
	end)
end

local function knockback(direction: Vector3)
	local root = getRoot()
	if not root then
		return
	end
	local attachment = Instance.new("Attachment")
	attachment.Parent = root
	local velocity = direction * KNOCKBACK.HorizontalSpeed + Vector3.yAxis * KNOCKBACK.UpSpeed
	if velocity.Magnitude < 1e-3 then
		attachment:Destroy()
		return
	end
	-- Only along the push direction: movement across it stays free, so the nudge never stops the player's walk.
	local push = Instance.new("LinearVelocity")
	push.Attachment0 = attachment
	push.RelativeTo = Enum.ActuatorRelativeTo.World
	push.VelocityConstraintMode = Enum.VelocityConstraintMode.Line
	push.LineDirection = velocity.Unit
	push.LineVelocity = velocity.Magnitude
	push.MaxForce = math.huge
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
	lastReported = {
		Position = entry.Position,
		Id = entry.Marker.Name,
		Golden = entry.Marker:GetAttribute(PROJECTILES.GoldenAttribute) == true,
		At = os.clock(),
	}
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

local function onBonkHit(
	reward: number,
	qualityName: string,
	direction: Vector3,
	onHead: boolean,
	combo: number,
	window: number,
	golden: boolean,
	firstBonk: boolean?
)
	local quality, juice = findQuality(qualityName)
	local isGolden = golden == true
	showPopup(reward, quality, juice, onHead, isGolden)
	playSound(juice.Pitch)
	burstStars(if isGolden then PROJECTILES.GoldenColor else quality.Color, juice.Stars)
	burstCoins(juice.Coins)
	-- Impact burst only for hand catches this client just reported (auto-catches are pulled in by the magnet).
	local hit = lastReported
	if hit and os.clock() - hit.At <= HITS.ImmunityTime + 1 then
		lastReported = nil
		burstImpact(hit)
	end
	local shake = juice.Shake
		* (if onHead then BONK.HeadShakeScale else 1)
		* (if isGolden then BONK.GoldenShakeScale else 1)
	shakeCamera(shake)
	showCombo(combo, window)
	if firstBonk == true then
		showFirstBonk()
	end
	knockback(direction)
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
	coinFolder = Instance.new("Folder")
	coinFolder.Name = "BonkCoins"
	coinFolder.Parent = Workspace
	buildComboDisplay()
	-- Load the (uploaded) sound up front, so the first bonk isn't silent while it downloads.
	task.spawn(function()
		ContentProvider:PreloadAsync({ sound })
	end)
end

-- True if this client reported a hit on the projectile (a hand catch). MagnetController uses it to tell auto-catches
-- (paid without a report) apart.
function BonkController.WasReported(marker: BasePart): boolean
	return reported[marker] == true
end

function BonkController.Start()
	Net.Get(Net.BonkHit).OnClientEvent:Connect(onBonkHit)

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
