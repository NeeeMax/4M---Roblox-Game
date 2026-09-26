--!strict
-- Draws every projectile on this client. The server only places an invisible marker that carries the planned path
-- (Util/ProjectilePath); this controller moves a local copy of the model along that path every frame, using the
-- synced server clock. That keeps flights and bounces perfectly smooth. After its last settling hop the projectile
-- lies still and fades out over the path's FadeTime. BonkController reads the drawn positions for its hit checks, so
-- what the player sees is what counts. See docs/decisions/0004.
-- For the local player's own projectiles it also draws a landing ring where each will first touch the ground,
-- shrinking until it lands and gold during the Perfect window (Gameplay.LandingRing, docs/decisions/0005).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local ISLAND = Gameplay.Island
local CONFIG = Gameplay.Projectiles
local HITS = Gameplay.Hits
local RING = Gameplay.LandingRing
local VALUE_TAG = CONFIG.ValueTag
local GRIP_NAME = Gameplay.Shooters.HandProjectile.GripName
-- Turns a cylinder adornment (axis along its Z) so it lies flat on the ground.
local FLAT = CFrame.Angles(math.rad(90), 0, 0)

-- A landing ring: the shrinking outline and the faint target disc under it. Pooled and reused.
type Ring = {
	Outline: CylinderHandleAdornment,
	Target: CylinderHandleAdornment,
}

export type Drawn = {
	Marker: BasePart,
	Path: ProjectilePath.Path,
	LaunchTime: number,
	Radius: number,
	-- Centre of the projectile's hit sphere this frame (on the path; near the ground the model sits a bit lower).
	-- See place.
	Position: Vector3,
	-- False once the landing fade has ended (the model is gone).
	Visible: boolean,
	-- True while it can still be collected (ProjectilePath.GetCollectEndTime); BonkController only checks these.
	Collectable: boolean,
	Model: Model,
	-- Model pivot relative to the centre of its bounding box, and the bounding box size.
	PivotOffset: CFrame,
	BoxSize: Vector3,
	SpinAxis: Vector3,
	SpinSpeed: number,
	-- Orientation it settles into: lying flat, its longest side along its last direction of travel.
	RestRotation: CFrame,
	-- Each part's / decal's own transparency, so the paid look and the landing fade are applied on top of it.
	BaseParts: { [BasePart]: number },
	BaseDecals: { [Decal]: number },
	Highlight: Highlight?,
	-- The "×N" tag of a stick worth several throws (stick density cap), if any.
	ValueLabel: TextLabel?,
	-- What is currently applied: Paid attribute seen, landing fade progress (0..1).
	Paid: boolean,
	FadeAlpha: number,
	-- Own projectiles that land on the island: first landing (seconds after launch), the ground point under it and
	-- the ring colour. The ring itself only while it is shown.
	LandingTime: number?,
	LandingGround: Vector3?,
	RingColor: Color3,
	Ring: Ring?,
}

local drawn: { [BasePart]: Drawn } = {}
local pending: { [BasePart]: boolean } = {}
local visualsFolder: Folder
local ringFolder: Folder
local freeRings: { Ring } = {}
-- The local player's island Projectiles folder (only its projectiles get a landing ring).
local ownFolder: Instance? = nil
local random = Random.new()

local ProjectileController = {}

local function biggestPart(model: Model): BasePart?
	local biggest: BasePart? = nil
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") and (not biggest or descendant.Size.Magnitude > biggest.Size.Magnitude) then
			biggest = descendant
		end
	end
	return biggest
end

-- A trail in the def's colour behind the model's biggest part, `lifetime` seconds long (default 0.2).
local function addTrail(model: Model, color: Color3, diameter: number, lifetime: number?)
	local biggest = biggestPart(model)
	if not biggest then
		return
	end
	local top = Instance.new("Attachment")
	top.Position = Vector3.new(0, diameter * 0.12, 0)
	top.Parent = biggest
	local bottom = Instance.new("Attachment")
	bottom.Position = Vector3.new(0, -diameter * 0.12, 0)
	bottom.Parent = biggest
	local trail = Instance.new("Trail")
	trail.Attachment0 = top
	trail.Attachment1 = bottom
	trail.Color = ColorSequence.new(color)
	trail.Transparency = NumberSequence.new(0.3, 1)
	trail.WidthScale = NumberSequence.new(1, 0)
	trail.Lifetime = lifetime or 0.2
	trail.LightEmission = 0.6
	trail.FaceCamera = true
	trail.Parent = biggest
end

-- "×3.5" (whole numbers without the decimal: "×4").
local function multiplierText(multiplier: number): string
	local rounded = math.floor(multiplier * 10 + 0.5) / 10
	if rounded == math.floor(rounded) then
		return `×{math.floor(rounded)}`
	end
	return string.format("×%.1f", rounded)
end

-- Stick density cap (Gameplay.Projectiles.ValueTag): a stick worth `multiplier` throws gets a small "×N" tag above it
-- (in world space, so it doesn't spin with the stick) and a trail in `color` that grows with N. Returns the label, so
-- the paid look and the landing fade can fade it.
local function addValueLook(model: Model, multiplier: number, color: Color3, diameter: number): TextLabel?
	local strength = math.clamp((multiplier - 1) / math.max(VALUE_TAG.FullAt - 1, 1e-3), 0, 1)
	addTrail(
		model,
		color,
		diameter * (VALUE_TAG.WidthMin + (VALUE_TAG.WidthMax - VALUE_TAG.WidthMin) * strength),
		VALUE_TAG.LifetimeMin + (VALUE_TAG.LifetimeMax - VALUE_TAG.LifetimeMin) * strength
	)
	local anchor = biggestPart(model)
	if not anchor then
		return nil
	end
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "ValueTag"
	billboard.Size = UDim2.fromScale(VALUE_TAG.Width, VALUE_TAG.Height)
	billboard.StudsOffsetWorldSpace = Vector3.new(0, diameter * VALUE_TAG.Offset, 0)
	billboard.LightInfluence = 0
	billboard.MaxDistance = VALUE_TAG.MaxDistance
	billboard.Adornee = anchor
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.Text = multiplierText(multiplier)
	label.TextColor3 = VALUE_TAG.Color
	label.TextStrokeColor3 = VALUE_TAG.StrokeColor
	label.TextStrokeTransparency = 0
	label.Parent = billboard
	billboard.Parent = anchor
	return label
end

local function cloneFirst(names: { string }): Model?
	for _, name in names do
		local model = Assets.CloneModel(name)
		if model then
			return model
		end
	end
	return nil
end

local function buildModel(def: Projectiles.ProjectileDef?, diameter: number): Model
	local model = if def then cloneFirst(Projectiles.AssetCandidates(def.Id)) else nil
	if model then
		Assets.ScaleTo(model, diameter)
		-- The Grip marker only tells the Shiba's paw where to hold it: never visible (before BaseParts is read, so
		-- the paid look and the landing fade keep it at 1).
		Assets.HideMarkers(model, GRIP_NAME)
	else
		model = Instance.new("Model")
		local ball = Instance.new("Part")
		ball.Shape = Enum.PartType.Ball
		ball.Size = Vector3.one * diameter
		ball.Color = if def then def.Color else Color3.new(1, 1, 1)
		ball.Material = if def then def.Material else Enum.Material.SmoothPlastic
		ball.TopSurface = Enum.SurfaceType.Smooth
		ball.BottomSurface = Enum.SurfaceType.Smooth
		ball.Parent = model
	end
	Assets.MakeVisualOnly(model :: Model, true)
	if def and def.Trail then
		addTrail(model :: Model, def.Color, diameter)
	end
	return model :: Model
end

-- Orientation of a box of `size` lying flat on the ground: thinnest side up, longest side along `travel`.
local function restRotation(size: Vector3, travel: Vector3): CFrame
	local flat = Vector3.new(travel.X, 0, travel.Z)
	local forward = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local sizes = { size.X, size.Y, size.Z }
	local order = { 1, 2, 3 }
	table.sort(order, function(a: number, b: number): boolean
		return sizes[a] < sizes[b]
	end)
	-- World direction of each box axis (X, Y, Z).
	local axes = { Vector3.xAxis, Vector3.yAxis, Vector3.zAxis }
	axes[order[1]] = Vector3.yAxis
	axes[order[3]] = forward
	axes[order[2]] = forward:Cross(Vector3.yAxis)
	if axes[1]:Cross(axes[2]):Dot(axes[3]) < 0 then
		-- Keep it a proper rotation (right-handed), not a mirror image.
		axes[order[2]] = -axes[order[2]]
	end
	return CFrame.fromMatrix(Vector3.zero, axes[1], axes[2], axes[3])
end

-- Half the vertical extent of a box of `size` turned by `rotation`: how far its lowest point is below its centre.
local function halfHeight(rotation: CFrame, size: Vector3): number
	return 0.5
		* (
			math.abs(rotation.XVector.Y) * size.X
			+ math.abs(rotation.YVector.Y) * size.Y
			+ math.abs(rotation.ZVector.Y) * size.Z
		)
end

-- Starts drawing a marker once its path attributes are readable. Returns false to retry next frame.
local function tryStart(marker: BasePart): boolean
	local path, launchTime, diameter = ProjectilePath.Read(marker)
	if not path then
		return false
	end
	local def = Projectiles.Defs[marker.Name]
	local model = buildModel(def, diameter)
	local highlight: Highlight? = nil
	local golden = marker:GetAttribute(CONFIG.GoldenAttribute) == true
	if golden then
		-- Golden projectile: gold outline and a gold trail (it pays GoldenMultiplier times as much).
		local outline = Instance.new("Highlight")
		outline.FillColor = CONFIG.GoldenColor
		outline.FillTransparency = CONFIG.GoldenFillTransparency
		outline.OutlineColor = CONFIG.GoldenColor
		outline.DepthMode = Enum.HighlightDepthMode.Occluded
		outline.Parent = model
		highlight = outline
		addTrail(model, CONFIG.GoldenColor, diameter * 1.6)
	end
	-- Stick density cap: this stick stands for several throws.
	local valueMultiplier = marker:GetAttribute(CONFIG.ValueMultiplierAttribute)
	local valueLabel: TextLabel? = nil
	if typeof(valueMultiplier) == "number" and valueMultiplier >= VALUE_TAG.MinShown then
		local tierColor = if def then def.Color else Color3.new(1, 1, 1)
		local trailColor = if golden then CONFIG.GoldenColor else tierColor:Lerp(Color3.new(1, 1, 1), RING.Brighten)
		valueLabel = addValueLook(model, valueMultiplier, trailColor, diameter)
	end
	local box, boxSize = model:GetBoundingBox()
	local baseParts: { [BasePart]: number } = {}
	local baseDecals: { [Decal]: number } = {}
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			baseParts[descendant] = descendant.Transparency
		elseif descendant:IsA("Decal") then
			baseDecals[descendant] = descendant.Transparency
		end
	end
	local position = path.Segments[1].StartPosition
	local lastVelocity = path.Segments[#path.Segments].StartVelocity
	-- Landing ring: own projectiles whose flight ends on the island (a path without bounces fell off the edge).
	local landingTime: number? = nil
	local landingGround: Vector3? = nil
	if ownFolder and marker.Parent == ownFolder and #path.Segments >= 2 then
		landingTime = ProjectilePath.GetFirstLandingTime(path)
		landingGround = ProjectilePath.GetFirstLandingPosition(path) - Vector3.new(0, diameter / 2, 0)
	end
	local tierColor = if def then def.Color else Color3.new(1, 1, 1)
	drawn[marker] = {
		Marker = marker,
		Path = path,
		LaunchTime = launchTime,
		Radius = diameter / 2,
		Position = position,
		Visible = true,
		Collectable = true,
		Model = model,
		PivotOffset = box:ToObjectSpace(model:GetPivot()),
		BoxSize = boxSize,
		SpinAxis = random:NextUnitVector(),
		SpinSpeed = random:NextNumber(0.5, 1) * CONFIG.MaxSpin,
		RestRotation = restRotation(boxSize, lastVelocity),
		BaseParts = baseParts,
		BaseDecals = baseDecals,
		Highlight = highlight,
		ValueLabel = valueLabel,
		Paid = false,
		FadeAlpha = 0,
		LandingTime = landingTime,
		LandingGround = landingGround,
		RingColor = tierColor:Lerp(Color3.new(1, 1, 1), RING.Brighten),
		Ring = nil,
	}
	model:PivotTo(CFrame.new(position) * box:ToObjectSpace(model:GetPivot()))
	model.Parent = visualsFolder
	return true
end

local function newRingPiece(name: string): CylinderHandleAdornment
	local piece = Instance.new("CylinderHandleAdornment")
	piece.Name = name
	piece.Adornee = Workspace.Terrain
	piece.Height = RING.Height
	piece.AlwaysOnTop = false
	piece.Visible = false
	piece.Parent = ringFolder
	return piece
end

-- A landing ring from the pool (new ones only when all are in use), placed at `ground`.
local function acquireRing(ground: Vector3): Ring
	local ring: Ring = table.remove(freeRings)
		or { Outline = newRingPiece("LandingRing"), Target = newRingPiece("LandingTarget") }
	local frame = CFrame.new(ground + Vector3.new(0, RING.GroundOffset + RING.Height / 2, 0)) * FLAT
	ring.Outline.CFrame = frame
	-- The target disc a hair lower and thinner, so the outline is drawn over it.
	ring.Target.CFrame = frame - Vector3.new(0, RING.Height / 4, 0)
	ring.Target.Height = RING.Height / 2
	ring.Target.InnerRadius = 0
	ring.Target.Transparency = 1
	ring.Outline.Transparency = 1
	ring.Outline.Visible = true
	ring.Target.Visible = true
	return ring
end

local function releaseRing(entry: Drawn)
	local ring = entry.Ring
	if ring then
		entry.Ring = nil
		ring.Outline.Visible = false
		ring.Target.Visible = false
		table.insert(freeRings, ring)
	end
end

-- Shows, updates or removes the entry's landing ring for this frame (`elapsed` seconds after launch).
local function updateRing(entry: Drawn, elapsed: number)
	local landingTime = entry.LandingTime
	local ground = entry.LandingGround
	if not landingTime or not ground or entry.Paid or elapsed >= landingTime or landingTime <= 0 then
		releaseRing(entry)
		return
	end
	local ring = entry.Ring or acquireRing(ground)
	entry.Ring = ring
	local remaining = landingTime - elapsed
	local endRadius = entry.Radius + HITS.PickupPadding
	local startRadius = math.max(RING.StartRadius, endRadius + RING.MinShrink)
	local radius = endRadius + (startRadius - endRadius) * math.clamp(remaining / landingTime, 0, 1)
	local perfect = remaining <= HITS.PerfectWindow
	local color = if perfect then RING.PerfectColor else entry.RingColor
	local thickness = RING.Thickness * (if perfect then RING.PerfectThicknessScale else 1)
	local fadeIn = math.clamp(elapsed / RING.FadeInTime, 0, 1)
	ring.Outline.Radius = radius
	ring.Outline.InnerRadius = math.max(radius - thickness, 0)
	ring.Outline.Color3 = color
	ring.Outline.Transparency = 1 - (1 - RING.Transparency) * fadeIn
	ring.Target.Radius = endRadius
	ring.Target.Color3 = color
	ring.Target.Transparency = 1 - (1 - RING.TargetTransparency) * fadeIn
end

local function stop(marker: BasePart)
	pending[marker] = nil
	local entry = drawn[marker]
	if entry then
		drawn[marker] = nil
		releaseRing(entry)
		entry.Model:Destroy()
	end
end

-- `start` transparency, faded toward invisible by the landing fade progress.
local function faded(start: number, alpha: number): number
	return start + (1 - start) * alpha
end

-- Applies the paid look (PaidTransparency) and the landing fade on top of each part's own transparency.
local function applyTransparency(entry: Drawn)
	local alpha = entry.FadeAlpha
	local minimum = if entry.Paid then CONFIG.PaidTransparency else 0
	for part, base in entry.BaseParts do
		part.Transparency = faded(math.max(base, minimum), alpha)
	end
	for decal, base in entry.BaseDecals do
		decal.Transparency = faded(math.max(base, minimum), alpha)
	end
	local highlight = entry.Highlight
	if highlight then
		highlight.FillTransparency = faded(CONFIG.GoldenFillTransparency, alpha)
		highlight.OutlineTransparency = faded(0, alpha)
	end
	local valueLabel = entry.ValueLabel
	if valueLabel then
		local transparency = faded(minimum, alpha)
		valueLabel.TextTransparency = transparency
		valueLabel.TextStrokeTransparency = transparency
	end
end

-- Places the model for this frame. In flight it spins freely; during the settling hops it turns to lie flat
-- (RestRotation) and holds still while it fades. Near the ground it is lowered so its lowest point, not its hit
-- sphere, touches the ground (otherwise a flat stick would bounce and rest in mid-air, a radius above the ground).
local function place(entry: Drawn, elapsed: number)
	local path = entry.Path
	local position = entry.Position
	local spin = CFrame.fromAxisAngle(entry.SpinAxis, entry.SpinSpeed * math.min(elapsed, path.EndTime))
	local settleDuration = path.EndTime - path.SettleTime
	local settle = if settleDuration > 0
		then math.clamp((elapsed - path.SettleTime) / settleDuration, 0, 1)
		elseif elapsed >= path.EndTime then 1
		else 0
	-- Ease out: it turns quickly at first and eases into its resting pose.
	local rotation = spin:Lerp(entry.RestRotation, 1 - (1 - settle) ^ 2)
	local heightAboveGround = position.Y - entry.Radius - ISLAND.SurfaceY
	local nearGround = 1 - math.clamp(heightAboveGround / entry.Radius, 0, 1)
	local drop = math.max(entry.Radius - halfHeight(rotation, entry.BoxSize), 0) * nearGround
	entry.Model:PivotTo(CFrame.new(position - Vector3.new(0, drop, 0)) * rotation * entry.PivotOffset)
end

local function update()
	for marker in pending do
		if tryStart(marker) then
			pending[marker] = nil
		end
	end
	local now = Workspace:GetServerTimeNow()
	for marker, entry in drawn do
		if not entry.Visible then
			continue
		end
		local path = entry.Path
		local elapsed = now - entry.LaunchTime
		if elapsed >= ProjectilePath.GetVisibleEndTime(path) then
			-- Landing fade finished (or it has fallen below the island, which has no fade).
			entry.Visible = false
			entry.Collectable = false
			entry.Model.Parent = nil
			releaseRing(entry)
			continue
		end
		entry.Collectable = elapsed < ProjectilePath.GetCollectEndTime(path)
		-- GetState holds the resting position after EndTime, while it fades.
		entry.Position = ProjectilePath.GetState(path, elapsed)
		place(entry, elapsed)
		local paid = marker:GetAttribute(ProjectilePath.Attribute.Paid) == true
		local fadeAlpha = if path.FadeTime > 0 then math.clamp((elapsed - path.EndTime) / path.FadeTime, 0, 1) else 0
		if paid ~= entry.Paid or fadeAlpha ~= entry.FadeAlpha then
			entry.Paid = paid
			entry.FadeAlpha = fadeAlpha
			applyTransparency(entry)
		end
		updateRing(entry, elapsed)
	end
end

local function watchFolder(folder: Instance)
	folder.ChildAdded:Connect(function(child)
		if child:IsA("BasePart") then
			pending[child] = true
		end
	end)
	folder.ChildRemoved:Connect(function(child)
		if child:IsA("BasePart") then
			stop(child)
		end
	end)
	for _, child in folder:GetChildren() do
		if child:IsA("BasePart") then
			pending[child] = true
		end
	end
end

local function watchIsland(island: Instance)
	task.spawn(function()
		local folder = island:WaitForChild("Projectiles", 30)
		if folder then
			if island.Name == `{ISLAND.ModelPrefix}{Players.LocalPlayer.UserId}` then
				ownFolder = folder
			end
			watchFolder(folder)
		end
	end)
end

-- Every projectile in `folder` (a player's island Projectiles folder) that is drawn and can still be collected.
function ProjectileController.GetCollectableIn(folder: Instance): { Drawn }
	local result: { Drawn } = {}
	for marker, entry in drawn do
		if entry.Visible and entry.Collectable and marker.Parent == folder then
			table.insert(result, entry)
		end
	end
	return result
end

-- Hands a drawn projectile over to another controller (MagnetController pulls auto-caught sticks into the player):
-- this controller stops drawing it and the caller owns (and must destroy) the returned entry's Model. Each part is
-- reset to its own transparency. nil if it is not drawn (not started yet, or already gone).
function ProjectileController.Detach(marker: BasePart): Drawn?
	local entry = drawn[marker]
	if not entry or not entry.Visible then
		return nil
	end
	drawn[marker] = nil
	releaseRing(entry)
	entry.Visible = false
	entry.Collectable = false
	entry.Paid = false
	entry.FadeAlpha = 0
	applyTransparency(entry)
	return entry
end

function ProjectileController.Init()
	visualsFolder = Instance.new("Folder")
	visualsFolder.Name = "ProjectileVisuals"
	visualsFolder.Parent = Workspace
	ringFolder = Instance.new("Folder")
	ringFolder.Name = "LandingRings"
	ringFolder.Parent = visualsFolder
end

function ProjectileController.Start()
	task.spawn(function()
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		islands.ChildAdded:Connect(watchIsland)
		for _, island in islands:GetChildren() do
			watchIsland(island)
		end
	end)
	RunService:BindToRenderStep("DrawProjectiles", Enum.RenderPriority.Camera.Value + 1, update)
end

return ProjectileController
