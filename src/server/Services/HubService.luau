--!strict
-- Builds the hub island in the middle (Config/World → Hub) with its stations between the bridges. Each station has
-- a ProximityPrompt named after the menu it opens (HudController opens it). The leaderboard board is filled by
-- LeaderboardService. The centre is the jump and run tower (ObbyService builds it). Machines and trees are props
-- (PropService) that Marco can replace with models.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local World = require(ReplicatedStorage.Shared.Config.World)

local PropService = require(script.Parent.PropService)
local Signs = require(script.Parent.Parent.World.Signs)

local HUB = World.Hub
local PLOTS = World.Plots

type StationDef = {
	Id: string,
	Title: string,
	Subtitle: string,
	Color: Color3,
	-- True: a ProximityPrompt opens the menu with this Id.
	Prompt: boolean,
}

-- One station per gap between two bridges, clockwise from north-east.
local STATIONS: { StationDef } = {
	{
		Id = "DailySpin",
		Title = "DAILY SPIN",
		Subtitle = "Free spin every day!",
		Color = Color3.fromRGB(255, 200, 40),
		Prompt = true,
	},
	{
		Id = "CoinFlip",
		Title = "COIN FLIP",
		Subtitle = "Double or nothing · Duels",
		Color = Color3.fromRGB(255, 150, 40),
		Prompt = true,
	},
	{
		Id = "Shop",
		Title = "SHOP",
		Subtitle = "Passes · Boosts · Trophies",
		Color = Color3.fromRGB(90, 220, 140),
		Prompt = true,
	},
	{
		Id = "Quests",
		Title = "DAILY QUESTS",
		Subtitle = "New quests every day",
		Color = Color3.fromRGB(120, 230, 120),
		Prompt = true,
	},
	{
		Id = "Leaderboard",
		Title = "TOP BONKERS",
		Subtitle = "Most Bonk Points earned",
		Color = Color3.fromRGB(120, 200, 255),
		Prompt = false,
	},
}

local HOW_TO = table.concat({
	"1. Walk over a bridge to YOUR island.",
	"2. Shibas throw sticks onto your field: catch them with your body!",
	"3. HEAD hits pay x2, running + jumping in pays up to x50, golden sticks x5.",
	"4. Upgrade your Shibas, sticks and speed.",
	"5. Come back for the daily spin, quests, gifts and coin flips!",
}, "\n")

local stationParts: { [string]: BasePart } = {}

local HubService = {}

local function newPart(name: string, size: Vector3, cframe: CFrame, color: Color3, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.Color = color
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

local function cylinder(
	name: string,
	radius: number,
	height: number,
	cframe: CFrame,
	color: Color3,
	parent: Instance
): Part
	local part = newPart(
		name,
		Vector3.new(height, radius * 2, radius * 2),
		cframe * CFrame.Angles(0, 0, math.rad(90)),
		color,
		parent
	)
	part.Shape = Enum.PartType.Cylinder
	return part
end

-- An upright disc whose flat side faces the same way as `cframe`'s front.
local function disc(
	name: string,
	radius: number,
	thickness: number,
	cframe: CFrame,
	color: Color3,
	parent: Instance
): Part
	local part = newPart(
		name,
		Vector3.new(thickness, radius * 2, radius * 2),
		cframe * CFrame.Angles(0, math.rad(90), 0),
		color,
		parent
	)
	part.Shape = Enum.PartType.Cylinder
	return part
end

-- Placeholder machines (Prop_<Id>Machine) standing on each station's pedestal, front toward the hub centre.
local MACHINE_BUILDERS: { [string]: PropService.Builder } = {
	DailySpin = function(model, height)
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(2, height * 0.55, 2),
			CFrame.new(0, height * 0.275, 0),
			Color3.fromRGB(60, 50, 70),
			Enum.Material.Metal
		)
		local wheel =
			disc("Wheel", height * 0.35, 0.8, CFrame.new(0, height * 0.62, -1.2), Color3.fromRGB(255, 200, 40), model)
		wheel.Material = Enum.Material.Neon
		disc("Cap", height * 0.08, 1.2, CFrame.new(0, height * 0.62, -1.4), Color3.fromRGB(255, 80, 80), model)
	end,
	CoinFlip = function(model, height)
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(6, height * 0.3, 4),
			CFrame.new(0, height * 0.15, 0),
			Color3.fromRGB(120, 40, 40),
			Enum.Material.Wood
		)
		local coin =
			disc("Coin", height * 0.25, 0.6, CFrame.new(0, height * 0.65, 0), Color3.fromRGB(255, 200, 40), model)
		coin.Material = Enum.Material.Foil
	end,
	Shop = function(model, height)
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(10, height * 0.4, 4),
			CFrame.new(0, height * 0.2, 0),
			Color3.fromRGB(150, 100, 60),
			Enum.Material.WoodPlanks
		)
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(11, 0.6, 5),
			CFrame.new(0, height * 0.95, 0),
			Color3.fromRGB(90, 220, 140),
			Enum.Material.SmoothPlastic
		)
		for _, x in { -4.8, 4.8 } do
			PropService.Part(
				model,
				Enum.PartType.Block,
				Vector3.new(0.5, height * 0.55, 0.5),
				CFrame.new(x, height * 0.67, 0),
				Color3.fromRGB(110, 75, 45),
				Enum.Material.Wood
			)
		end
		for index = -1, 1 do
			PropService.Part(
				model,
				Enum.PartType.Ball,
				Vector3.one * 1.4,
				CFrame.new(index * 3, height * 0.4 + 0.7, 0),
				Color3.fromHSV((index + 1) / 3, 0.7, 1),
				Enum.Material.Neon
			)
		end
	end,
	Quests = function(model, height)
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(9, height * 0.6, 0.5),
			CFrame.new(0, height * 0.55, 0),
			Color3.fromRGB(140, 100, 60),
			Enum.Material.WoodPlanks
		)
		for _, x in { -4, 4 } do
			PropService.Part(
				model,
				Enum.PartType.Block,
				Vector3.new(0.6, height * 0.85, 0.6),
				CFrame.new(x, height * 0.425, 0.4),
				Color3.fromRGB(100, 70, 45),
				Enum.Material.Wood
			)
		end
		for index = -1, 1 do
			PropService.Part(
				model,
				Enum.PartType.Block,
				Vector3.new(2, 2.4, 0.1),
				CFrame.new(index * 2.6, height * 0.55, -0.3),
				Color3.fromRGB(245, 240, 220),
				Enum.Material.SmoothPlastic
			)
		end
	end,
}

-- Pedestal + machine + title sign + prompt, facing the hub centre.
local function buildStation(def: StationDef, angle: number, parent: Instance)
	local dir = Vector3.new(math.sin(angle), 0, -math.cos(angle))
	local position = HUB.Center + dir * HUB.StationRadius
	local facing = CFrame.lookAt(position, Vector3.new(HUB.Center.X, position.Y, HUB.Center.Z))

	local model = Instance.new("Model")
	model.Name = def.Id
	local pedestal = cylinder("Pedestal", 8, 1, facing * CFrame.new(0, 0.5, 0), Color3.fromRGB(70, 68, 85), model)
	pedestal.Material = Enum.Material.Slate
	local ring = cylinder("Ring", 8.4, 0.6, facing * CFrame.new(0, 0.3, 0), def.Color, model)
	ring.Material = Enum.Material.Neon

	if def.Id == "Leaderboard" then
		local board =
			newPart("Board", Vector3.new(16, 18, 0.6), facing * CFrame.new(0, 11, 1), Color3.fromRGB(30, 28, 42), model)
		local frame = newPart("Frame", Vector3.new(17, 19, 0.4), facing * CFrame.new(0, 11, 1.4), def.Color, model)
		frame.Material = Enum.Material.Neon
		stationParts[def.Id] = board
	else
		local machine =
			PropService.Place(`Prop_{def.Id}Machine`, facing * CFrame.new(0, 1, 2), 12, MACHINE_BUILDERS[def.Id], model)
		stationParts[def.Id] = machine.PrimaryPart :: BasePart
	end

	-- Title sign above everything, readable from both sides.
	local signHeight = if def.Id == "Leaderboard" then 23 else 17
	local sign = newPart(
		"Sign",
		Vector3.new(15, 3.6, 0.6),
		facing * CFrame.new(0, signHeight, 0),
		Color3.fromRGB(25, 22, 36),
		model
	)
	local signFrame =
		newPart("SignFrame", Vector3.new(15.8, 4.4, 0.4), facing * CFrame.new(0, signHeight, 0.3), def.Color, model)
	signFrame.Material = Enum.Material.Neon
	local title = Signs.Text(sign, Enum.NormalId.Front, def.Title, def.Color)
	Signs.Mirror(sign, title)
	Signs.Billboard(sign, def.Subtitle, Color3.fromRGB(240, 240, 250), Vector2.new(280, 30), -3, 90)

	if def.Prompt then
		local prompt = Instance.new("ProximityPrompt")
		prompt.Name = def.Id
		prompt.ActionText = "Open"
		prompt.ObjectText = def.Title
		prompt.HoldDuration = 0
		prompt.MaxActivationDistance = 16
		prompt.RequiresLineOfSight = false
		prompt.Parent = pedestal
	end

	model.Parent = parent
end

-- The part a station shows its content on (the leaderboard board, the machine …).
function HubService.GetStationPart(id: string): BasePart?
	return stationParts[id]
end

function HubService.Init()
	local folder = Instance.new("Folder")
	folder.Name = HUB.Name

	local ground = cylinder(
		"Ground",
		HUB.Radius,
		HUB.Thickness,
		CFrame.new(HUB.Center - Vector3.new(0, HUB.Thickness / 2, 0)),
		HUB.Color,
		folder
	)
	ground.Material = Enum.Material.Grass
	local rim = cylinder(
		"Rim",
		HUB.Radius + 1,
		HUB.Thickness + 0.4,
		CFrame.new(HUB.Center - Vector3.new(0, HUB.Thickness / 2 + 0.3, 0)),
		Color3.fromRGB(255, 190, 40),
		folder
	)
	rim.Material = Enum.Material.SmoothPlastic
	local plaza = cylinder(
		"Plaza",
		24,
		0.4,
		CFrame.new(HUB.Center + Vector3.new(0, 0.2, 0)),
		Color3.fromRGB(210, 200, 180),
		folder
	)
	plaza.Material = Enum.Material.Cobblestone
	-- Paths from the plaza to each bridge.
	for slot = 1, PLOTS.Count do
		local angle = (slot - 1) / PLOTS.Count * 2 * math.pi
		local dir = Vector3.new(math.sin(angle), 0, -math.cos(angle))
		local middle = HUB.Center + dir * (24 + (HUB.Radius - 24) / 2) + Vector3.new(0, 0.15, 0)
		local path = newPart(
			"Path",
			Vector3.new(10, 0.3, HUB.Radius - 22),
			CFrame.lookAt(middle, middle + dir),
			Color3.fromRGB(200, 190, 170),
			folder
		)
		path.Material = Enum.Material.Cobblestone
	end

	PropService.Place(
		"Prop_IslandRock",
		CFrame.new(HUB.Center - Vector3.new(0, HUB.Thickness, 0)),
		HUB.Radius,
		PropService.Builders.IslandRock,
		folder
	)

	-- The hub centre is the jump and run tower (ObbyService); the Shiba statue stands on its top.

	-- How-to-play board on the plaza, right of the obby entrance, facing the spawn point (the best-times board
	-- of ObbyService stands on the left).
	local boardCenter = HUB.Center + Vector3.new(8, 6, 19)
	local boardCFrame = CFrame.lookAt(boardCenter, boardCenter + Vector3.new(0, 0, 20))
	local howTo = newPart("HowTo", Vector3.new(10, 8, 0.5), boardCFrame, Color3.fromRGB(30, 28, 42), folder)
	local howToFrame = newPart(
		"HowToFrame",
		Vector3.new(10.8, 8.8, 0.3),
		boardCFrame * CFrame.new(0, 0, 0.3),
		Color3.fromRGB(230, 120, 255),
		folder
	)
	howToFrame.Material = Enum.Material.Neon
	for _, x in { -4.2, 4.2 } do
		newPart(
			"Leg",
			Vector3.new(0.6, 6, 0.6),
			CFrame.new(boardCenter + Vector3.new(x, -4.5, 0.4)),
			Color3.fromRGB(60, 55, 70),
			folder
		)
	end
	local text = Signs.Text(howTo, Enum.NormalId.Front, HOW_TO, Color3.fromRGB(245, 245, 255), 40, Enum.Font.GothamBold)
	text.TextXAlignment = Enum.TextXAlignment.Left
	Signs.Billboard(howToFrame, "HOW TO PLAY", Color3.fromRGB(230, 120, 255), Vector2.new(260, 40), 5.6, 120)

	for index, def in STATIONS do
		-- Halfway between bridge `index` and the next one.
		local angle = (index - 0.5) / PLOTS.Count * 2 * math.pi
		buildStation(def, angle, folder)
	end

	-- Trees on the rim, halfway between each bridge and the next station (never on a path).
	local random = Random.new(42)
	for index = 1, PLOTS.Count * 2 do
		local angle = (index - 0.5) / (PLOTS.Count * 2) * 2 * math.pi
		local position = HUB.Center + Vector3.new(math.sin(angle), 0, -math.cos(angle)) * (HUB.Radius - 7)
		PropService.Place(
			"Prop_Tree",
			CFrame.new(position) * CFrame.Angles(0, random:NextNumber(0, 6.28), 0),
			random:NextNumber(12, 16),
			PropService.Builders.Tree,
			folder
		)
	end

	folder.Parent = Workspace
end

return HubService
