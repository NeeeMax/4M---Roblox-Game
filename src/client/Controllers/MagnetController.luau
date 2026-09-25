--!strict
-- Auto-Catch pass look, purely visual (the catching itself is AutoCatchService on the server). While the local player
-- owns the pass (State → Passes.AutoCatch) a small low-poly magnet (red U, silver tips, built from parts) circles the
-- character and bobs. When the server auto-catches one of this player's projectiles, its marker's Paid attribute
-- turns true although this client never reported a hit on it (BonkController.WasReported): that is the server's
-- catch moment, arriving together with the BonkHit popup. The drawn stick is then taken over from
-- ProjectileController and pulled into the player (accelerating, spinning, shrinking, with a trail and a beam from
-- the magnet's tips), sparkles pop where it arrives and the magnet turns toward it and wiggles.
-- Tuning: Config/Gameplay → Magnet. Nothing is sent to the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)

local BonkController = require(script.Parent.BonkController)
local ProjectileController = require(script.Parent.ProjectileController)
local State = require(script.Parent.Parent.UI.State)

local CONFIG = Gameplay.Magnet
local ISLAND = Gameplay.Island
-- The magnet is a timed boost (Types.BoostId "Magnet"): shown until state.Boosts.Magnet (Unix time) runs out.
local BOOST_ID = "Magnet"
local activeUntil = 0
local RED = Color3.fromRGB(215, 40, 45)
local SILVER = Color3.fromRGB(215, 220, 230)
local SPARKLE_TEXTURE = "rbxasset://textures/particles/sparkles_main.dds"
-- Farther than this from its circle point (respawn, teleport) the magnet jumps there instead of flying.
local SNAP_DISTANCE = 20

type Pull = {
	Model: Model,
	-- Model pivot relative to its box centre when it was taken over, and the model scale then.
	PivotOffset: CFrame,
	StartScale: number,
	Start: Vector3,
	Rotation: CFrame,
	Started: number,
	Position: Vector3,
	Beam: Beam,
}

local player = Players.LocalPlayer
local visualsFolder: Folder
local magnet: Model
-- Where the beam starts: between the silver tips.
local tipAttachment: Attachment
local tipSparkles: ParticleEmitter
local active = false
local magnetFrame: CFrame? = nil
local wiggleStarted = -math.huge
local pulls: { Pull } = {}
-- Sparkles where caught sticks arrive, on the current character's root.
local arrivalSparkles: ParticleEmitter? = nil
local arrivalRoot: BasePart? = nil

local MagnetController = {}

local function sparkleEmitter(color: Color3, size: number, parent: Attachment): ParticleEmitter
	local emitter = Instance.new("ParticleEmitter")
	emitter.Texture = SPARKLE_TEXTURE
	emitter.Color = ColorSequence.new(color)
	emitter.LightEmission = 0.9
	emitter.Size = NumberSequence.new(size, 0)
	emitter.Lifetime = NumberRange.new(0.25, 0.5)
	emitter.Speed = NumberRange.new(4, 9)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-200, 200)
	emitter.Enabled = false
	emitter.Parent = parent
	return emitter
end

-- The magnet, built around its centre with the U's opening (the silver tips) facing its -Z (LookVector).
local function buildMagnet(): Model
	local scale = CONFIG.Scale
	local model = Instance.new("Model")
	model.Name = "AutoCatchMagnet"
	local function piece(name: string, size: Vector3, offset: Vector3, color: Color3, material: Enum.Material): Part
		local part = Instance.new("Part")
		part.Name = name
		part.Size = size * scale
		part.CFrame = CFrame.new(offset * scale)
		part.Color = color
		part.Material = material
		part.Anchored = true
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
		part.CastShadow = false
		part.Massless = true
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.Parent = model
		return part
	end
	local base = piece("Base", Vector3.new(0.95, 0.3, 0.3), Vector3.new(0, 0, 0.35), RED, Enum.Material.SmoothPlastic)
	for _, side in { -1, 1 } do
		piece("Leg", Vector3.new(0.3, 0.3, 0.85), Vector3.new(0.325 * side, 0, 0.075), RED, Enum.Material.SmoothPlastic)
		piece("Tip", Vector3.new(0.3, 0.3, 0.25), Vector3.new(0.325 * side, 0, -0.475), SILVER, Enum.Material.Metal)
	end
	-- Pivot at the U's centre (the parts were built around the origin), so it turns around its middle.
	model.WorldPivot = CFrame.identity
	tipAttachment = Instance.new("Attachment")
	tipAttachment.Name = "Tips"
	tipAttachment.Position = Vector3.new(0, 0, -0.95) * scale
	tipAttachment.Parent = base
	tipSparkles = sparkleEmitter(CONFIG.BeamColor, 0.35, tipAttachment)
	return model
end

local function getRoot(): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

local function burstAt(root: BasePart)
	if arrivalRoot ~= root or not (arrivalSparkles and arrivalSparkles.Parent) then
		local attachment = Instance.new("Attachment")
		attachment.Name = "MagnetSparkles"
		attachment.Parent = root
		arrivalSparkles = sparkleEmitter(Color3.fromRGB(255, 255, 255), 0.5, attachment)
		arrivalRoot = root
	end
	local emitter = arrivalSparkles
	if emitter then
		emitter.Color = ColorSequence.new(Color3.new(1, 1, 1), CONFIG.BeamColor)
		emitter:Emit(CONFIG.Sparkles)
	end
end

local function addTrail(model: Model): BasePart?
	local biggest: BasePart? = nil
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") and (not biggest or descendant.Size.Magnitude > biggest.Size.Magnitude) then
			biggest = descendant
		end
	end
	if not biggest then
		return nil
	end
	local width = math.max(biggest.Size.X, biggest.Size.Y, biggest.Size.Z) * 0.25
	local top = Instance.new("Attachment")
	top.Position = Vector3.new(0, width, 0)
	top.Parent = biggest
	local bottom = Instance.new("Attachment")
	bottom.Position = Vector3.new(0, -width, 0)
	bottom.Parent = biggest
	local trail = Instance.new("Trail")
	trail.Attachment0 = top
	trail.Attachment1 = bottom
	trail.Color = ColorSequence.new(CONFIG.BeamColor)
	trail.Transparency = NumberSequence.new(0.2, 1)
	trail.WidthScale = NumberSequence.new(1, 0)
	trail.Lifetime = 0.15
	trail.LightEmission = 0.8
	trail.FaceCamera = true
	trail.Parent = biggest
	return biggest
end

-- Takes the auto-caught stick over from ProjectileController and starts pulling it in.
local function startPull(marker: BasePart)
	wiggleStarted = os.clock()
	tipSparkles:Emit(4)
	if #pulls >= CONFIG.MaxPulls or not magnetFrame then
		return
	end
	local entry = ProjectileController.Detach(marker)
	if not entry then
		return
	end
	local model = entry.Model
	local biggest = addTrail(model)
	local target = Instance.new("Attachment")
	target.Parent = biggest or model:FindFirstChildWhichIsA("BasePart", true)
	local beam = Instance.new("Beam")
	beam.Attachment0 = tipAttachment
	beam.Attachment1 = target
	beam.Color = ColorSequence.new(CONFIG.BeamColor)
	beam.LightEmission = 1
	beam.Transparency = NumberSequence.new(0.1, 0.6)
	beam.Width0 = 0.35 * CONFIG.Scale
	beam.Width1 = 0.12 * CONFIG.Scale
	beam.FaceCamera = true
	beam.Segments = 8
	beam.CurveSize0 = 1
	beam.Parent = tipAttachment
	local boxRotation = model:GetPivot() * entry.PivotOffset:Inverse()
	table.insert(pulls, {
		Model = model,
		PivotOffset = entry.PivotOffset,
		StartScale = model:GetScale(),
		Start = entry.Position,
		Rotation = boxRotation.Rotation,
		Started = os.clock(),
		Position = entry.Position,
		Beam = beam,
	})
end

local function endPull(pull: Pull)
	pull.Beam:Destroy()
	pull.Model:Destroy()
end

-- Moves one pull along; returns false once it has arrived (or the character is gone).
local function stepPull(pull: Pull, root: BasePart?, now: number, dt: number): boolean
	if not root then
		endPull(pull)
		return false
	end
	local k = math.clamp((now - pull.Started) / CONFIG.PullTime, 0, 1)
	if k >= 1 then
		endPull(pull)
		burstAt(root)
		return false
	end
	-- Accelerates into the player (magnetic snap) over a small arc; the root moves, so aim at it every frame.
	local eased = k * k
	local position = pull.Start:Lerp(root.Position, eased) + Vector3.yAxis * math.sin(math.pi * k) * 1.2
	pull.Position = position
	pull.Rotation = pull.Rotation * CFrame.Angles(0, dt * 18, dt * 6)
	local scale = 1 + (CONFIG.PullEndScale - 1) * eased
	pull.Model:ScaleTo(pull.StartScale * scale)
	local offset = pull.PivotOffset
	pull.Model:PivotTo(CFrame.new(position) * pull.Rotation * CFrame.new(offset.Position * scale) * offset.Rotation)
	return true
end

local function update(dt: number)
	local root = getRoot()
	local now = os.clock()
	for index = #pulls, 1, -1 do
		if not stepPull(pulls[index], root, now, dt) then
			table.remove(pulls, index)
		end
	end
	active = Workspace:GetServerTimeNow() < activeUntil
	if not (active and root) then
		magnet.Parent = nil
		magnetFrame = nil
		return
	end

	local clock = Workspace:GetServerTimeNow()
	local angle = clock * CONFIG.OrbitSpeed
	local bob = CONFIG.BobHeight * math.sin(2 * math.pi * clock / CONFIG.BobPeriod)
	local goal = root.Position
		+ Vector3.new(
			math.cos(angle) * CONFIG.OrbitRadius,
			CONFIG.OrbitHeight + bob,
			math.sin(angle) * CONFIG.OrbitRadius
		)
	local previous = magnetFrame
	local position = if previous and (previous.Position - goal).Magnitude < SNAP_DISTANCE
		then previous.Position:Lerp(goal, 1 - math.exp(-CONFIG.FollowSharpness * dt))
		else goal
	-- Tips out, away from the player; toward the newest stick while one is being pulled in.
	local newest = pulls[#pulls]
	local lookAt = if newest
		then newest.Position
		else position + Vector3.new(position.X - root.Position.X, 0, position.Z - root.Position.Z)
	local facing = if (lookAt - position).Magnitude > 1e-3
		then CFrame.lookAt(position, lookAt)
		else CFrame.new(position)
	local rotation = if previous
		then previous.Rotation:Lerp(facing.Rotation, 1 - math.exp(-(if newest then 30 else 8) * dt))
		else facing.Rotation
	local frame = CFrame.new(position) * rotation
	magnetFrame = frame

	local sinceCatch = now - wiggleStarted
	if sinceCatch < CONFIG.WiggleTime then
		local left = 1 - sinceCatch / CONFIG.WiggleTime
		local wiggle = math.rad(CONFIG.WiggleDegrees) * math.sin(sinceCatch * 45) * left
		frame *= CFrame.Angles(0, wiggle * 0.6, wiggle)
	end
	magnet:PivotTo(frame)
	if magnet.Parent ~= visualsFolder then
		magnet.Parent = visualsFolder
	end
end

local function watchMarker(marker: Instance)
	if not marker:IsA("BasePart") then
		return
	end
	marker:GetAttributeChangedSignal(ProjectilePath.Attribute.Paid):Connect(function()
		-- Paid without a hand report from here: AutoCatchService caught it.
		if
			active
			and marker:GetAttribute(ProjectilePath.Attribute.Paid) == true
			and not BonkController.WasReported(marker)
		then
			startPull(marker)
		end
	end)
end

local function refreshActive()
	local state = State.Get()
	activeUntil = if state then state.Boosts[BOOST_ID] or 0 else 0
	active = Workspace:GetServerTimeNow() < activeUntil
end

function MagnetController.Init()
	visualsFolder = Instance.new("Folder")
	visualsFolder.Name = "MagnetVisual"
	visualsFolder.Parent = Workspace
	magnet = buildMagnet()
end

function MagnetController.Start()
	State.Start()
	State.Changed:Connect(refreshActive)
	refreshActive()
	-- After the projectiles are drawn (DrawProjectiles runs at Camera + 1).
	RunService:BindToRenderStep("AutoCatchMagnet", Enum.RenderPriority.Camera.Value + 3, update)
	task.spawn(function()
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		local island = islands:WaitForChild(`{ISLAND.ModelPrefix}{player.UserId}`)
		local folder = island:WaitForChild("Projectiles")
		folder.ChildAdded:Connect(watchMarker)
		for _, marker in folder:GetChildren() do
			watchMarker(marker)
		end
	end)
end

return MagnetController
