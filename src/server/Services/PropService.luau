--!strict
-- World props that should become real 3D models later (trees, lamps, rocks, clouds, trophies, hub machines …).
-- Place() uses ReplicatedStorage.Assets.<name> if it exists, scaled to the given height; otherwise it builds a
-- placeholder from parts. In Studio every placeholder gets a bright pink outline and a "MODEL: <name>" label, so
-- it is obvious what still needs a model (list: assets/README.md). The live game shows the plain placeholder.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)

local MARKER_COLOR = Color3.fromRGB(255, 0, 200)
local SHOW_MARKERS = RunService:IsStudio()

export type Builder = (model: Model, height: number) -> ()

local PropService = {}

local function part(
	model: Model,
	shape: Enum.PartType,
	size: Vector3,
	offset: CFrame,
	color: Color3,
	material: Enum.Material?
): Part
	local piece = Instance.new("Part")
	piece.Shape = shape
	piece.Size = size
	piece.CFrame = offset
	piece.Color = color
	piece.Material = material or Enum.Material.SmoothPlastic
	piece.Anchored = true
	piece.TopSurface = Enum.SurfaceType.Smooth
	piece.BottomSurface = Enum.SurfaceType.Smooth
	piece.Parent = model
	return piece
end
PropService.Part = part

local function marker(model: Model, name: string)
	local box = Instance.new("SelectionBox")
	box.Adornee = model
	box.Color3 = MARKER_COLOR
	box.LineThickness = 0.15
	box.SurfaceTransparency = 1
	box.Parent = model
	local _, size = model:GetBoundingBox()
	local anchor = model.PrimaryPart or model:FindFirstChildWhichIsA("BasePart")
	if not anchor then
		return
	end
	local label = Instance.new("BillboardGui")
	label.Name = "PlaceholderLabel"
	label.Size = UDim2.fromOffset(220, 26)
	label.StudsOffsetWorldSpace = Vector3.new(0, size.Y / 2 + 1.5, 0)
	label.Adornee = model
	label.MaxDistance = 120
	label.AlwaysOnTop = true
	label.Parent = model
	local text = Instance.new("TextLabel")
	text.Size = UDim2.fromScale(1, 1)
	text.BackgroundColor3 = MARKER_COLOR
	text.BackgroundTransparency = 0.2
	text.TextColor3 = Color3.new(1, 1, 1)
	text.Font = Enum.Font.GothamBold
	text.TextScaled = true
	text.Text = `MODEL: {name}`
	text.Parent = label
end

-- Places prop `name` so its bottom centre sits on `cframe` (facing its look vector), `height` studs tall.
function PropService.Place(name: string, cframe: CFrame, height: number, build: Builder, parent: Instance): Model
	local asset = Assets.CloneModel(name)
	local model: Model
	if asset then
		model = asset
		Assets.ScaleTo(model, height, true)
		Assets.MakeVisualOnly(model, true)
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				-- Props you can stand on/walk into keep collisions; visual-only was just for scaling safety.
				descendant.CanCollide = true
				descendant.CanQuery = true
			end
		end
		local box, size = model:GetBoundingBox()
		local bottom = box * CFrame.new(0, -size.Y / 2, 0)
		model:PivotTo(cframe * bottom:ToObjectSpace(model:GetPivot()))
	else
		model = Instance.new("Model")
		-- Placeholders are built around the origin, bottom at y = 0, then moved into place.
		build(model, height)
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				descendant.CFrame = cframe * descendant.CFrame
			end
		end
		model.PrimaryPart = model:FindFirstChildWhichIsA("BasePart")
		if SHOW_MARKERS then
			marker(model, name)
		end
	end
	model.Name = name
	model.Parent = parent
	return model
end

-- Ready-made placeholder builders. Colours are the ones the real models should roughly have.
PropService.Builders = {
	Tree = function(model: Model, height: number)
		local trunk = height * 0.45
		part(
			model,
			Enum.PartType.Cylinder,
			Vector3.new(trunk, 1.4, 1.4),
			CFrame.new(0, trunk / 2, 0) * CFrame.Angles(0, 0, math.rad(90)),
			Color3.fromRGB(110, 75, 45),
			Enum.Material.Wood
		)
		local crown = height * 0.6
		part(
			model,
			Enum.PartType.Ball,
			Vector3.one * crown,
			CFrame.new(0, trunk + crown * 0.35, 0),
			Color3.fromRGB(70, 170, 70),
			Enum.Material.Grass
		)
		part(
			model,
			Enum.PartType.Ball,
			Vector3.one * crown * 0.7,
			CFrame.new(crown * 0.3, trunk + crown * 0.6, 0.4),
			Color3.fromRGB(90, 190, 80),
			Enum.Material.Grass
		)
	end :: Builder,

	Lamp = function(model: Model, height: number)
		part(
			model,
			Enum.PartType.Block,
			Vector3.new(0.5, height, 0.5),
			CFrame.new(0, height / 2, 0),
			Color3.fromRGB(50, 50, 60),
			Enum.Material.Metal
		)
		local bulb = part(
			model,
			Enum.PartType.Ball,
			Vector3.one * 1.3,
			CFrame.new(0, height + 0.4, 0),
			Color3.fromRGB(255, 220, 140),
			Enum.Material.Neon
		)
		local light = Instance.new("PointLight")
		light.Range = 18
		light.Brightness = 1.5
		light.Color = Color3.fromRGB(255, 210, 150)
		light.Parent = bulb
	end :: Builder,

	-- A rocky cone hanging under a floating island (height = how far it reaches down; built upside down).
	IslandRock = function(model: Model, height: number)
		local layers = 5
		for layer = 0, layers - 1 do
			local t = layer / layers
			local radius = height * 0.9 * (1 - t) + 2
			local thickness = height / layers
			local y = -thickness * (layer + 0.5)
			local shade = 95 - layer * 10
			part(
				model,
				Enum.PartType.Cylinder,
				Vector3.new(thickness, radius * 2, radius * 2),
				CFrame.new(0, y, 0) * CFrame.Angles(0, 0, math.rad(90)),
				Color3.fromRGB(shade + 20, shade, shade - 10),
				Enum.Material.Slate
			)
		end
	end :: Builder,

	Cloud = function(model: Model, height: number)
		for index = 1, 4 do
			local size = height * (0.7 + (index % 2) * 0.35)
			local puff = part(
				model,
				Enum.PartType.Ball,
				Vector3.one * size,
				CFrame.new((index - 2.5) * height * 0.55, size / 2, (index % 2) * 2),
				Color3.new(1, 1, 1),
				Enum.Material.SmoothPlastic
			)
			puff.Transparency = 0.15
			puff.CanCollide = false
			puff.CastShadow = false
		end
	end :: Builder,

	Rock = function(model: Model, height: number)
		part(
			model,
			Enum.PartType.Ball,
			Vector3.new(height * 1.4, height, height * 1.1),
			CFrame.new(0, height * 0.4, 0),
			Color3.fromRGB(120, 115, 110),
			Enum.Material.Slate
		)
	end :: Builder,

	Flowers = function(model: Model, height: number)
		local colors = { Color3.fromRGB(255, 90, 120), Color3.fromRGB(255, 220, 60), Color3.fromRGB(150, 120, 255) }
		for index = 1, 5 do
			local angle = index * 1.3
			part(
				model,
				Enum.PartType.Ball,
				Vector3.one * height * 0.5,
				CFrame.new(math.cos(angle) * height * 0.6, height * 0.25, math.sin(angle) * height * 0.6),
				colors[index % 3 + 1],
				Enum.Material.SmoothPlastic
			).CanCollide =
				false
		end
	end :: Builder,
}

-- A trophy cup placeholder in the trophy's colour (Trophy_<Id> models replace it).
function PropService.TrophyBuilder(color: Color3): Builder
	return function(model: Model, height: number)
		local material = Enum.Material.Foil
		part(
			model,
			Enum.PartType.Block,
			Vector3.new(height * 0.5, height * 0.15, height * 0.5),
			CFrame.new(0, height * 0.075, 0),
			Color3.fromRGB(60, 50, 40),
			Enum.Material.Wood
		)
		part(
			model,
			Enum.PartType.Cylinder,
			Vector3.new(height * 0.3, height * 0.12, height * 0.12),
			CFrame.new(0, height * 0.3, 0) * CFrame.Angles(0, 0, math.rad(90)),
			color,
			material
		)
		part(
			model,
			Enum.PartType.Cylinder,
			Vector3.new(height * 0.45, height * 0.45, height * 0.45),
			CFrame.new(0, height * 0.7, 0) * CFrame.Angles(0, 0, math.rad(90)),
			color,
			material
		)
		part(
			model,
			Enum.PartType.Ball,
			Vector3.one * height * 0.2,
			CFrame.new(0, height * 0.97, 0),
			color,
			Enum.Material.Neon
		)
	end
end

return PropService
