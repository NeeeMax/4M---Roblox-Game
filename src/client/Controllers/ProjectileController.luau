--!strict
-- Draws every projectile on this client. The server only places an invisible marker that carries the planned path
-- (Util/ProjectilePath); this controller moves a local copy of the model along that path every frame, using the
-- synced server clock. That keeps flights and bounces perfectly smooth. After its last settling hop the projectile
-- lies still and fades out over the path's FadeTime. BonkController reads the drawn positions for its hit checks, so
-- what the player sees is what counts. See docs/decisions/0004.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local ISLAND = Gameplay.Island
local CONFIG = Gameplay.Projectiles

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
	-- What is currently applied: Paid attribute seen, landing fade progress (0..1).
	Paid: boolean,
	FadeAlpha: number,
}

local drawn: { [BasePart]: Drawn } = {}
local pending: { [BasePart]: boolean } = {}
local visualsFolder: Folder
local random = Random.new()

local ProjectileController = {}

-- A trail in the def's colour behind the model's biggest part.
local function addTrail(model: Model, color: Color3, diameter: number)
	local biggest: BasePart? = nil
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") and (not biggest or descendant.Size.Magnitude > biggest.Size.Magnitude) then
			biggest = descendant
		end
	end
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
	trail.Lifetime = 0.2
	trail.LightEmission = 0.6
	trail.FaceCamera = true
	trail.Parent = biggest
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
	local model = buildModel(Projectiles.Defs[marker.Name], diameter)
	local highlight: Highlight? = nil
	if marker:GetAttribute(CONFIG.GoldenAttribute) == true then
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
		Paid = false,
		FadeAlpha = 0,
	}
	model:PivotTo(CFrame.new(position) * box:ToObjectSpace(model:GetPivot()))
	model.Parent = visualsFolder
	return true
end

local function stop(marker: BasePart)
	pending[marker] = nil
	local entry = drawn[marker]
	if entry then
		drawn[marker] = nil
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

function ProjectileController.Init()
	visualsFolder = Instance.new("Folder")
	visualsFolder.Name = "ProjectileVisuals"
	visualsFolder.Parent = Workspace
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
