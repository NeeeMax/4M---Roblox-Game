--!strict
-- World props that can be real 3D models (trees, lamps, rocks, clouds, trophies, hub machines …, list:
-- assets/README.md → Props; built by assets/models/build_props.py). Place() uses ReplicatedStorage.Assets.<name>
-- if it exists, scaled to the given height; otherwise it builds a placeholder from parts. Props still using a
-- placeholder are listed in Output (Config/Props → ReportMissing); Config/Props → ShowPlaceholderMarkers also
-- puts a pink "MODEL: <name>" label on them in Studio.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Props = require(ReplicatedStorage.Shared.Config.Props)

local MARKER_COLOR = Color3.fromRGB(255, 0, 200)
local SHOW_MARKERS = Props.ShowPlaceholderMarkers and RunService:IsStudio()
-- Seconds to collect missing names before printing them in one line.
local REPORT_DELAY = 3

export type Builder = (model: Model, height: number) -> ()

local PropService = {}

local missing: { [string]: boolean } = {}
local reported: { [string]: boolean } = {}
local reportScheduled = false

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

-- Lists props without a model in Output, a few seconds after the first one (the world is built by then).
local function reportMissing(name: string)
	if not Props.ReportMissing or reported[name] then
		return
	end
	reported[name] = true
	missing[name] = true
	if reportScheduled then
		return
	end
	reportScheduled = true
	task.delay(REPORT_DELAY, function()
		reportScheduled = false
		local names: { string } = {}
		for missingName in missing do
			table.insert(names, missingName)
		end
		table.clear(missing)
		table.sort(names)
		local list = table.concat(names, ", ")
		warn(`[PropService] No model in ReplicatedStorage.Assets for {#names} prop(s), placeholders used: {list}`)
	end)
end

-- Prepares an imported model: collisions (Config/Props → NoCollide), glowing parts and the prop's light.
local function prepareAsset(name: string, model: Model)
	local solid = not Props.NoCollide[name]
	local light: Props.Light? = Props.Lights[name]
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			-- Props you can stand on/walk into keep collisions; visual-only was just for scaling safety.
			descendant.CanCollide = solid
			descendant.CanQuery = solid
			if descendant.Name == Props.GlowPartName then
				descendant.Material = Enum.Material.Neon
				descendant.CanCollide = false
				descendant.CastShadow = false
				if light then
					local pointLight = Instance.new("PointLight")
					pointLight.Range = light.Range
					pointLight.Brightness = light.Brightness
					pointLight.Color = light.Color
					pointLight.Parent = descendant
					light = nil
				end
			end
		end
	end
end

-- Places prop `name` so its bottom centre sits on `cframe` (facing its look vector), `height` studs tall. Hanging
-- props (Config/Props → Hanging) hang from `cframe` instead: their top centre sits there.
function PropService.Place(name: string, cframe: CFrame, height: number, build: Builder, parent: Instance): Model
	local asset = Assets.CloneModel(name)
	local model: Model
	if asset then
		model = asset
		Assets.ScaleTo(model, height, true)
		Assets.MakeVisualOnly(model, true)
		prepareAsset(name, model)
		local box, size = model:GetBoundingBox()
		local side = if Props.Hanging[name] then size.Y / 2 else -size.Y / 2
		local anchor = box * CFrame.new(0, side, 0)
		model:PivotTo(cframe * anchor:ToObjectSpace(model:GetPivot()))
		-- Callers anchor signs to the PrimaryPart (e.g. the statue's billboard); set after placing, since it changes
		-- the bounding box orientation.
		if not model.PrimaryPart then
			local body = model:FindFirstChild("Body", true)
			model.PrimaryPart = if body and body:IsA("BasePart")
				then body
				else model:FindFirstChildWhichIsA("BasePart", true)
		end
	else
		reportMissing(name)
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

	-- The rebirth shrine on every player island (Config/Stations → Stalls, Kind "Rebirth"): a purple stone altar
	-- under a golden arch with a glowing orb, front toward −Z, about 7 × 5.4 studs. The orb is named "Orb"
	-- (StationService dims it while the player can't rebirth yet).
	RebirthShrine = function(model: Model, height: number)
		local scale = height / 9
		local stone = Color3.fromRGB(70, 40, 110)
		local marble = Color3.fromRGB(125, 75, 185)
		local gold = Color3.fromRGB(255, 200, 60)
		local function block(size: Vector3, y: number, z: number, color: Color3, material: Enum.Material): Part
			return part(model, Enum.PartType.Block, size * scale, CFrame.new(0, y * scale, z * scale), color, material)
		end
		-- Base slab (reaches into the island, so no gap shows) with a gold band, then a step and the altar.
		block(Vector3.new(7, 0.9, 5.4), 0.15, 0, stone, Enum.Material.Slate)
		block(Vector3.new(7.2, 0.2, 5.6), 0.4, 0, gold, Enum.Material.Foil)
		block(Vector3.new(5, 0.5, 3.8), 0.85, 0.2, marble, Enum.Material.Marble)
		block(Vector3.new(2.6, 2.4, 1.8), 2.3, 0.4, marble, Enum.Material.Marble)
		block(Vector3.new(3, 0.3, 2.2), 3.65, 0.4, gold, Enum.Material.Foil)
		-- Golden arch behind the altar.
		for _, x in { -2.8, 2.8 } do
			part(
				model,
				Enum.PartType.Cylinder,
				Vector3.new(6.3, 0.9, 0.9) * scale,
				CFrame.new(x * scale, 4.25 * scale, 1.4 * scale) * CFrame.Angles(0, 0, math.rad(90)),
				gold,
				Enum.Material.Foil
			)
		end
		block(Vector3.new(6.6, 0.6, 1.1), 7.7, 1.4, gold, Enum.Material.Foil)
		local gem = part(
			model,
			Enum.PartType.Ball,
			Vector3.one * 0.9 * scale,
			CFrame.new(0, 8.45 * scale, 1.4 * scale),
			gold,
			Enum.Material.Neon
		)
		gem.CanCollide = false
		-- The orb floating over the altar.
		local orb = part(
			model,
			Enum.PartType.Ball,
			Vector3.one * 1.8 * scale,
			CFrame.new(0, 5.2 * scale, 0.4 * scale),
			Color3.fromRGB(200, 110, 255),
			Enum.Material.Neon
		)
		orb.Name = "Orb"
		orb.CanCollide = false
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(200, 110, 255)
		light.Range = 14
		light.Brightness = 1.5
		light.Parent = orb
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
