--!strict
-- Draws every projectile on this client. The server only places an invisible marker that carries the planned path
-- (Util/ProjectilePath); this controller moves a local copy of the model along that path every frame, using the
-- synced server clock. That keeps flights and bounces perfectly smooth. BonkController reads the drawn positions
-- for its hit checks, so what the player sees is what counts. See docs/decisions/0004.

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
	-- Centre of the projectile this frame.
	Position: Vector3,
	-- False once the path has ended (the model is gone).
	Visible: boolean,
	Model: Model,
	-- Model pivot relative to the centre of its bounding box.
	PivotOffset: CFrame,
	SpinAxis: Vector3,
	SpinSpeed: number,
	-- Each part's own transparency, so a paid projectile can be faded on top of it.
	BaseTransparency: { [BasePart]: number },
	Faded: boolean,
}

local drawn: { [BasePart]: Drawn } = {}
local pending: { [BasePart]: boolean } = {}
local visualsFolder: Folder
local random = Random.new()

local ProjectileController = {}

local function buildModel(def: Projectiles.ProjectileDef?, diameter: number): Model
	local model = if def and def.AssetName then Assets.CloneModel(def.AssetName) else nil
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
	return model :: Model
end

-- Starts drawing a marker once its path attributes are readable. Returns false to retry next frame.
local function tryStart(marker: BasePart): boolean
	local path, launchTime, diameter = ProjectilePath.Read(marker)
	if not path then
		return false
	end
	local model = buildModel(Projectiles.Defs[marker.Name], diameter)
	local box = model:GetBoundingBox()
	local baseTransparency: { [BasePart]: number } = {}
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			baseTransparency[descendant] = descendant.Transparency
		end
	end
	local position = path.Segments[1].StartPosition
	drawn[marker] = {
		Marker = marker,
		Path = path,
		LaunchTime = launchTime,
		Radius = diameter / 2,
		Position = position,
		Visible = true,
		Model = model,
		PivotOffset = box:ToObjectSpace(model:GetPivot()),
		SpinAxis = random:NextUnitVector(),
		SpinSpeed = random:NextNumber(0.5, 1) * CONFIG.MaxSpin,
		BaseTransparency = baseTransparency,
		Faded = false,
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

local function fade(entry: Drawn)
	entry.Faded = true
	for part, transparency in entry.BaseTransparency do
		part.Transparency = math.max(transparency, CONFIG.PaidTransparency)
	end
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
		local elapsed = now - entry.LaunchTime
		if elapsed >= entry.Path.EndTime then
			-- Gone the moment it touches the ground after its last bounce (or has fallen below the island).
			entry.Visible = false
			entry.Model.Parent = nil
			continue
		end
		local position = ProjectilePath.GetState(entry.Path, elapsed)
		entry.Position = position
		local spin = CFrame.fromAxisAngle(entry.SpinAxis, entry.SpinSpeed * elapsed)
		entry.Model:PivotTo(CFrame.new(position) * spin * entry.PivotOffset)
		if not entry.Faded and marker:GetAttribute(ProjectilePath.Attribute.Paid) then
			fade(entry)
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

-- Every projectile currently drawn in `folder` (a player's island Projectiles folder).
function ProjectileController.GetVisibleIn(folder: Instance): { Drawn }
	local result: { Drawn } = {}
	for marker, entry in drawn do
		if entry.Visible and marker.Parent == folder then
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
