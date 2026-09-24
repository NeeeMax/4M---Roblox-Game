--!strict
-- Makes the world pretty (Config/World → Ocean, Decor): warm lighting with atmosphere and bloom, an ocean of real
-- terrain water far below, clouds, and small floating islands in the distance. Everything is decoration only;
-- clouds and small islands are props Marco can replace with models (PropService).

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local World = require(ReplicatedStorage.Shared.Config.World)

local PropService = require(script.Parent.PropService)

local OCEAN = World.Ocean
local DECOR = World.Decor
local HUB = World.Hub

local DecorService = {}

local function setupLighting()
	Lighting.ClockTime = 14.5
	Lighting.Brightness = 2.6
	Lighting.EnvironmentDiffuseScale = 1
	Lighting.EnvironmentSpecularScale = 1
	Lighting.OutdoorAmbient = Color3.fromRGB(150, 150, 170)
	Lighting.Ambient = Color3.fromRGB(90, 90, 110)
	Lighting.GlobalShadows = true

	local function effect(className: string, name: string): Instance
		local existing = Lighting:FindFirstChild(name)
		if existing then
			existing:Destroy()
		end
		local instance = Instance.new(className)
		instance.Name = name
		instance.Parent = Lighting
		return instance
	end

	local atmosphere = effect("Atmosphere", "BonkAtmosphere") :: Atmosphere
	atmosphere.Density = 0.28
	atmosphere.Offset = 0.2
	atmosphere.Color = Color3.fromRGB(200, 220, 255)
	atmosphere.Decay = Color3.fromRGB(120, 150, 210)
	atmosphere.Glare = 0.3
	atmosphere.Haze = 1.2

	local bloom = effect("BloomEffect", "BonkBloom") :: BloomEffect
	bloom.Intensity = 0.6
	bloom.Size = 30
	bloom.Threshold = 1.4

	local color = effect("ColorCorrectionEffect", "BonkColor") :: ColorCorrectionEffect
	color.Saturation = 0.15
	color.Contrast = 0.08
	color.Brightness = 0.02

	local rays = effect("SunRaysEffect", "BonkSunRays") :: SunRaysEffect
	rays.Intensity = 0.06
	rays.Spread = 0.8
end

local function setupOcean()
	local terrain = Workspace.Terrain
	terrain.WaterColor = Color3.fromRGB(40, 150, 200)
	terrain.WaterTransparency = 0.6
	terrain.WaterWaveSize = 0.25
	terrain.WaterWaveSpeed = 8
	terrain.WaterReflectance = 0.6
	local center = Vector3.new(HUB.Center.X, OCEAN.SurfaceY - OCEAN.Depth / 2, HUB.Center.Z)
	terrain:FillBlock(CFrame.new(center), Vector3.new(OCEAN.Size, OCEAN.Depth, OCEAN.Size), Enum.Material.Water)
	-- The template's baseplate would stick out of the water; hide it (not deleted, it's part of Max's place).
	local baseplate = Workspace:FindFirstChild("Baseplate")
	if baseplate and baseplate:IsA("BasePart") then
		baseplate.Transparency = 1
		baseplate.CanCollide = false
	end
end

local function smallIsland(model: Model, height: number)
	local radius = height * 1.2
	PropService.Part(
		model,
		Enum.PartType.Cylinder,
		Vector3.new(2, radius * 2, radius * 2),
		CFrame.new(0, -1, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(95, 185, 85),
		Enum.Material.Grass
	)
	PropService.Builders.IslandRock(model, radius)
	for _, piece in model:GetChildren() do
		if piece:IsA("BasePart") and piece.Material == Enum.Material.Slate then
			piece.CFrame += Vector3.new(0, -2, 0)
		end
	end
	PropService.Builders.Tree(model, height)
end

function DecorService.Init()
	setupLighting()
	setupOcean()

	local folder = Instance.new("Folder")
	folder.Name = "Decor"
	local random = Random.new(7)
	for _ = 1, DECOR.Clouds do
		local angle = random:NextNumber(0, 2 * math.pi)
		local distance = random:NextNumber(100, 750)
		local height = random:NextNumber(DECOR.CloudHeight[1], DECOR.CloudHeight[2])
		local position = HUB.Center
			+ Vector3.new(math.cos(angle) * distance, height - HUB.Center.Y, math.sin(angle) * distance)
		PropService.Place(
			"Prop_Cloud",
			CFrame.new(position) * CFrame.Angles(0, random:NextNumber(0, 6.28), 0),
			random:NextNumber(12, 22),
			PropService.Builders.Cloud,
			folder
		)
	end
	for index = 1, DECOR.SmallIslands do
		local angle = (index + random:NextNumber(-0.3, 0.3)) / DECOR.SmallIslands * 2 * math.pi
		local distance = random:NextNumber(470, 650)
		local position = HUB.Center
			+ Vector3.new(math.cos(angle) * distance, random:NextNumber(-40, 50), math.sin(angle) * distance)
		PropService.Place("Prop_SmallIsland", CFrame.new(position), random:NextNumber(10, 18), smallIsland, folder)
	end
	folder.Parent = Workspace
end

return DecorService
