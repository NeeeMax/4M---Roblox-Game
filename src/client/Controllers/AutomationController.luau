--!strict
-- Automation look, purely visual (the catching and paying is AutomationService on the server).
-- * AutomationCatch "Basket": the caught stick is taken over from ProjectileController and flies in an arc from where
--   it lay into the basket's opening; sparkles pop there and a "+B$ X" coin popup rises above the basket.
-- * AutomationCatch "Intern": the intern gets bonked: it tips over and wobbles back up, stars burst from its head,
--   the stick bounces off and fades, a speech bubble says a random line and the coin popup rises.
-- * Every client animates every intern's walk (swinging arms and legs by its speed); the server only moves the root.
-- Tuning: Config/Automation → Effects. Nothing is sent to the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Automation = require(ReplicatedStorage.Shared.Config.Automation)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)

local ProjectileController = require(script.Parent.ProjectileController)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local EFFECTS = Automation.Effects
local JOINTS = Automation.Intern.Joints
local ISLAND = Gameplay.Island
local ID_ATTRIBUTE = Gameplay.Projectiles.IdAttribute
local SPARKLE_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"

type Flight = {
	Model: Model,
	-- Model pivot relative to its box centre when it was taken over, and the model scale then.
	PivotOffset: CFrame,
	StartScale: number,
	EndScale: number,
	Start: Vector3,
	Target: Vector3,
	ArcHeight: number,
	Rotation: CFrame,
	Started: number,
	Duration: number,
	-- Parts faded out over the flight (bounce-off), with their own transparency.
	Fade: { [BasePart]: number }?,
	OnArrive: (() -> ())?,
}

-- Per intern model: its joints, walk phase and when it was last bonked.
type Rig = {
	Root: BasePart,
	Waist: Motor6D?,
	LeftShoulder: Motor6D?,
	RightShoulder: Motor6D?,
	LeftHip: Motor6D?,
	RightHip: Motor6D?,
	Phase: number,
	BonkedAt: number,
}

local player = Players.LocalPlayer
local islandsFolder: Instance? = nil
local flights: { Flight } = {}
-- Weak keys: destroyed interns drop out.
local rigs: { [Model]: Rig } = setmetatable({} :: any, { __mode = "k" })
local random = Random.new()

local AutomationController = {}

local function ownIsland(): Instance?
	local folder = islandsFolder
	return if folder then folder:FindFirstChild(`{ISLAND.ModelPrefix}{player.UserId}`) else nil
end

local function findMarker(island: Instance, projectileId: number): BasePart?
	local folder = island:FindFirstChild("Projectiles")
	if not folder then
		return nil
	end
	for _, child in folder:GetChildren() do
		if child:IsA("BasePart") and child:GetAttribute(ID_ATTRIBUTE) == projectileId then
			return child
		end
	end
	return nil
end

-- An invisible world-space anchor for particles and popups (removed after `lifetime` seconds).
local function anchorAt(position: Vector3, lifetime: number): Attachment
	local attachment = Instance.new("Attachment")
	attachment.Name = "AutomationEffect"
	attachment.WorldPosition = position
	attachment.Parent = Workspace.Terrain
	task.delay(lifetime, function()
		attachment:Destroy()
	end)
	return attachment
end

local function burst(parent: Attachment, color: Color3, count: number, size: number, speed: number)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = SPARKLE_TEXTURE
	emitter.Color = ColorSequence.new(Color3.new(1, 1, 1), color)
	emitter.LightEmission = 0.8
	emitter.Size = NumberSequence.new(size, 0)
	emitter.Lifetime = NumberRange.new(0.35, 0.7)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-200, 200)
	emitter.Enabled = false
	emitter.Parent = parent
	emitter:Emit(count)
end

-- "+B$ X" rising from `adornee` (seen only by this player).
local function coinPopup(adornee: Instance, reward: number, offsetY: number)
	local billboard = Instance.new("BillboardGui")
	billboard.Adornee = adornee
	billboard.AlwaysOnTop = true
	billboard.Size = UDim2.fromOffset(220, 46)
	billboard.StudsOffset = Vector3.new(0, offsetY, 0)
	billboard.LightInfluence = 0
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = EFFECTS.PopupColor
	label.TextStrokeTransparency = 0
	label.Parent = billboard
	Widgets.SetMoneyText(label, `+{Format.Money(reward)}`)
	billboard.Parent = player:WaitForChild("PlayerGui")
	local info = TweenInfo.new(EFFECTS.PopupTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(billboard, info, { StudsOffset = Vector3.new(0, offsetY + EFFECTS.PopupRise, 0) }):Play()
	Widgets.FadeOut(label, EFFECTS.PopupTime)
	task.delay(EFFECTS.PopupTime, function()
		billboard:Destroy()
	end)
end

-- A white speech bubble with a random voice line over the intern's head.
local function speechBubble(head: BasePart)
	local lines = EFFECTS.VoiceLines
	local billboard = Instance.new("BillboardGui")
	billboard.Adornee = head
	billboard.AlwaysOnTop = true
	billboard.Size = UDim2.fromOffset(190, 46)
	billboard.StudsOffset = Vector3.new(0, 5, 0)
	billboard.LightInfluence = 0
	billboard.MaxDistance = 120
	local bubble = Instance.new("Frame")
	bubble.AnchorPoint = Vector2.new(0.5, 0.5)
	bubble.Position = UDim2.fromScale(0.5, 0.5)
	bubble.Size = UDim2.fromScale(1, 1)
	bubble.BackgroundColor3 = Color3.new(1, 1, 1)
	bubble.Parent = billboard
	Widgets.Corner(bubble, 14)
	Widgets.Stroke(bubble, 2, Color3.fromRGB(30, 30, 40))
	local scale = Instance.new("UIScale")
	scale.Scale = 0.2
	scale.Parent = bubble
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Position = UDim2.fromOffset(8, 4)
	text.Size = UDim2.new(1, -16, 1, -8)
	text.Font = Enum.Font.FredokaOne
	text.TextScaled = true
	text.TextColor3 = Color3.fromRGB(30, 30, 40)
	text.Text = lines[random:NextInteger(1, #lines)]
	text.Parent = bubble
	billboard.Parent = player:WaitForChild("PlayerGui")
	TweenService:Create(scale, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
		:Play()
	local fadeTime = 0.3
	task.delay(EFFECTS.BubbleTime - fadeTime, function()
		Widgets.FadeOut(bubble, fadeTime)
	end)
	task.delay(EFFECTS.BubbleTime, function()
		billboard:Destroy()
	end)
end

-- Takes the drawn stick of `marker` over from ProjectileController and flies it to `target`. Returns false if it
-- is not drawn (or too many flights run); the caller then just shows the effect at the end.
local function startFlight(
	marker: BasePart?,
	target: (start: Vector3) -> Vector3,
	duration: number,
	arcHeight: number,
	endScale: number,
	fade: boolean,
	onArrive: (() -> ())?
): boolean
	if not marker then
		return false
	end
	local entry = ProjectileController.Detach(marker)
	if not entry then
		return false
	end
	if #flights >= EFFECTS.MaxFlights then
		entry.Model:Destroy()
		return false
	end
	local model = entry.Model
	local fadeParts: { [BasePart]: number }? = nil
	if fade then
		local parts: { [BasePart]: number } = {}
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				parts[descendant] = descendant.Transparency
			end
		end
		fadeParts = parts
	end
	local boxRotation = model:GetPivot() * entry.PivotOffset:Inverse()
	table.insert(flights, {
		Model = model,
		PivotOffset = entry.PivotOffset,
		StartScale = model:GetScale(),
		EndScale = endScale,
		Start = entry.Position,
		Target = target(entry.Position),
		ArcHeight = arcHeight,
		Rotation = boxRotation.Rotation,
		Started = os.clock(),
		Duration = duration,
		Fade = fadeParts,
		OnArrive = onArrive,
	})
	return true
end

-- Moves one flight along; returns false once it has arrived.
local function stepFlight(flight: Flight, now: number, dt: number): boolean
	local k = math.clamp((now - flight.Started) / flight.Duration, 0, 1)
	if k >= 1 then
		flight.Model:Destroy()
		local onArrive = flight.OnArrive
		if onArrive then
			onArrive()
		end
		return false
	end
	local position = flight.Start:Lerp(flight.Target, k) + Vector3.yAxis * math.sin(math.pi * k) * flight.ArcHeight
	flight.Rotation = flight.Rotation * CFrame.Angles(dt * 9, dt * 4, 0)
	local scale = 1 + (flight.EndScale - 1) * k
	flight.Model:ScaleTo(flight.StartScale * scale)
	local offset = flight.PivotOffset
	flight.Model:PivotTo(CFrame.new(position) * flight.Rotation * CFrame.new(offset.Position * scale) * offset.Rotation)
	local fade = flight.Fade
	if fade then
		for part, base in fade do
			part.Transparency = base + (1 - base) * k
		end
	end
	return true
end

local function onBasketCatch(island: Instance, projectileId: number, reward: number)
	local basket = island:FindFirstChild(Automation.BasketName)
	if not basket or not basket:IsA("Model") then
		return
	end
	local box, size = basket:GetBoundingBox()
	local opening = (box * CFrame.new(0, -size.Y / 2 + size.Y * Automation.Basket.BodyShare, 0)).Position
	local function arrive()
		local anchor = anchorAt(opening, 2)
		burst(anchor, Automation.Basket.RimColors[#Automation.Basket.RimColors], EFFECTS.BasketSparkles, 0.6, 10)
		coinPopup(anchor, reward, 1.5)
	end
	local flying = startFlight(findMarker(island, projectileId), function()
		return opening
	end, EFFECTS.BasketFlyTime, EFFECTS.BasketArcHeight, EFFECTS.BasketFlyEndScale, false, arrive)
	if not flying then
		arrive()
	end
end

local function onInternCatch(island: Instance, projectileId: number, reward: number)
	local intern = island:FindFirstChild(Automation.InternName)
	local head = if intern then intern:FindFirstChild("Head") else nil
	if not intern or not intern:IsA("Model") or not head or not head:IsA("BasePart") then
		return
	end
	local rig = rigs[intern]
	if rig then
		rig.BonkedAt = os.clock()
	end
	-- The stick bounces off the head, up and away, fading.
	startFlight(findMarker(island, projectileId), function(start: Vector3): Vector3
		local away = Vector3.new(start.X - head.Position.X, 0, start.Z - head.Position.Z)
		local side = if away.Magnitude > 0.1 then away.Unit else Vector3.new(random:NextNumber(-1, 1), 0, 1).Unit
		return head.Position + side * 5 + Vector3.new(0, 1, 0)
	end, EFFECTS.BounceOffTime, 3, 1, true, nil)

	local stars = Instance.new("Attachment")
	stars.Position = Vector3.new(0, head.Size.Y / 2, 0)
	stars.Parent = head
	burst(stars, EFFECTS.StarColor, EFFECTS.BonkStars, 0.7, 12)
	task.delay(1, function()
		stars:Destroy()
	end)
	speechBubble(head)
	coinPopup(head, reward, 2.5)
end

local function onAutomationCatch(source: unknown, projectileId: unknown, reward: unknown)
	if typeof(projectileId) ~= "number" or typeof(reward) ~= "number" then
		return
	end
	local island = ownIsland()
	if not island then
		return
	end
	if source == "Basket" then
		onBasketCatch(island, projectileId, reward)
	elseif source == "Intern" then
		onInternCatch(island, projectileId, reward)
	end
end

------------------------------------------------------------------------------------------------------------------------
-- Intern walk and wobble (every intern on every island)

local function findMotor(parent: Instance?, name: string): Motor6D?
	local joint = if parent then parent:FindFirstChild(name) else nil
	return if joint and joint:IsA("Motor6D") then joint else nil
end

local function getRig(model: Model): Rig?
	local rig = rigs[model]
	if rig and rig.Root.Parent == model then
		return rig
	end
	local root = model:FindFirstChild("Root")
	local torso = model:FindFirstChild("Torso")
	if not root or not root:IsA("BasePart") then
		return nil
	end
	local newRig: Rig = {
		Root = root,
		Waist = findMotor(root, JOINTS.Waist),
		LeftShoulder = findMotor(torso, JOINTS.LeftShoulder),
		RightShoulder = findMotor(torso, JOINTS.RightShoulder),
		LeftHip = findMotor(torso, JOINTS.LeftHip),
		RightHip = findMotor(torso, JOINTS.RightHip),
		Phase = 0,
		BonkedAt = -math.huge,
	}
	rigs[model] = newRig
	return newRig
end

local function setTransform(joint: Motor6D?, transform: CFrame)
	if joint then
		joint.Transform = transform
	end
end

local function animateRig(rig: Rig, dt: number, now: number)
	local velocity = rig.Root.AssemblyLinearVelocity
	local speed = Vector3.new(velocity.X, 0, velocity.Z).Magnitude
	-- One step = half a swing cycle.
	rig.Phase = (rig.Phase + speed * dt * EFFECTS.StepsPerStud * math.pi) % (2 * math.pi)
	local amount = math.clamp(speed / 6, 0, 1)
	local swing = math.sin(rig.Phase) * math.rad(EFFECTS.WalkSwingDegrees) * amount

	local sinceBonk = now - rig.BonkedAt
	if sinceBonk < EFFECTS.WobbleTime then
		-- Tips back and wobbles upright again (around the feet), arms flailing.
		local k = sinceBonk / EFFECTS.WobbleTime
		local tilt = math.rad(EFFECTS.WobbleDegrees) * math.sin(k * math.pi * 2.5) * (1 - k)
		local feet = Automation.Intern.RootHeight
		setTransform(rig.Waist, CFrame.new(0, -feet, 0) * CFrame.Angles(tilt, 0, tilt * 0.3) * CFrame.new(0, feet, 0))
		local flail = math.rad(140) * (1 - k) + math.sin(sinceBonk * 30) * math.rad(20) * (1 - k)
		setTransform(rig.LeftShoulder, CFrame.Angles(0, 0, -flail))
		setTransform(rig.RightShoulder, CFrame.Angles(0, 0, flail))
		setTransform(rig.LeftHip, CFrame.identity)
		setTransform(rig.RightHip, CFrame.identity)
		return
	end
	setTransform(rig.Waist, CFrame.identity)
	setTransform(rig.LeftShoulder, CFrame.Angles(-swing, 0, 0))
	setTransform(rig.RightShoulder, CFrame.Angles(swing, 0, 0))
	setTransform(rig.LeftHip, CFrame.Angles(swing, 0, 0))
	setTransform(rig.RightHip, CFrame.Angles(-swing, 0, 0))
end

local function update(dt: number)
	local now = os.clock()
	for index = #flights, 1, -1 do
		if not stepFlight(flights[index], now, dt) then
			table.remove(flights, index)
		end
	end
	local folder = islandsFolder
	if not folder then
		return
	end
	for _, island in folder:GetChildren() do
		local intern = island:FindFirstChild(Automation.InternName)
		if intern and intern:IsA("Model") then
			local rig = getRig(intern)
			if rig then
				animateRig(rig, dt, now)
			end
		end
	end
end

function AutomationController.Start()
	Net.Get(Net.AutomationCatch).OnClientEvent:Connect(onAutomationCatch)
	-- Joint transforms are set before each physics step (no Animator overrides them).
	RunService.PreSimulation:Connect(update)
	task.spawn(function()
		islandsFolder = Workspace:WaitForChild(ISLAND.FolderName)
	end)
end

return AutomationController
