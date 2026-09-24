--!strict
-- Builds the hub island in the middle (Config/World → Hub) with its stations between the bridges. Each station has
-- a ProximityPrompt named after it; the client opens the matching menu when it is triggered (HudController).
-- The leaderboard station's board is filled by LeaderboardService.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local World = require(ReplicatedStorage.Shared.Config.World)

local HUB = World.Hub
local PLOTS = World.Plots

type StationDef = {
	Id: string,
	Title: string,
	Subtitle: string,
	Color: Color3,
	-- True: a ProximityPrompt opens a menu with this Id. False: just a board to read.
	Prompt: boolean,
}

-- One station per gap between two bridges, clockwise from north-east.
local STATIONS: { StationDef } = {
	{
		Id = "DailySpin",
		Title = "DAILY SPIN",
		Subtitle = "1 free spin every day",
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
		Id = "Leaderboard",
		Title = "TOP BONKERS",
		Subtitle = "Most Bonk Points earned",
		Color = Color3.fromRGB(120, 200, 255),
		Prompt = false,
	},
	{
		Id = "Quests",
		Title = "DAILY QUESTS",
		Subtitle = "New quests every day",
		Color = Color3.fromRGB(120, 230, 120),
		Prompt = true,
	},
	{ Id = "HowTo", Title = "HOW TO PLAY", Subtitle = "", Color = Color3.fromRGB(230, 120, 255), Prompt = false },
}

local HOW_TO = table.concat({
	"1. Walk over a bridge to YOUR island.",
	"2. Shibas throw sticks at it: run and catch them with your body.",
	"3. Head hits pay x2, running + jumping into sticks pays up to x50, hits in a row build a combo.",
	"4. Spend Bonk Points on upgrades: better Shibas, better sticks, more Shibas, speed.",
	"5. Come back here for your daily spin, quests and coin flips!",
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

local function addText(
	part: BasePart,
	face: Enum.NormalId,
	text: string,
	color: Color3,
	pixelsPerStud: number
): TextLabel
	local gui = Instance.new("SurfaceGui")
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = pixelsPerStud
	gui.Parent = part
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextWrapped = true
	label.TextColor3 = color
	label.TextStrokeTransparency = 0
	label.Text = text
	label.Parent = gui
	return label
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

-- An upright disc whose flat side faces the same way as `cframe`'s front (its +X face points there).
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

-- Pedestal + sign + decoration + prompt, facing the hub centre.
local function buildStation(def: StationDef, angle: number, parent: Instance)
	local dir = Vector3.new(math.sin(angle), 0, -math.cos(angle))
	local position = HUB.Center + dir * HUB.StationRadius
	local facing = CFrame.lookAt(position, Vector3.new(HUB.Center.X, position.Y, HUB.Center.Z))

	local model = Instance.new("Model")
	model.Name = def.Id
	local pedestal = cylinder("Pedestal", 7, 1, facing * CFrame.new(0, 0.5, 0), Color3.fromRGB(70, 70, 85), model)
	pedestal.Material = Enum.Material.Slate

	if def.Id == "DailySpin" then
		-- A big wheel standing upright, facing the hub.
		local wheel = disc("Wheel", 5, 0.8, facing * CFrame.new(0, 7, 0), def.Color, model)
		wheel.Material = Enum.Material.Neon
		stationParts[def.Id] = wheel
	elseif def.Id == "CoinFlip" then
		local coin = disc("Coin", 3.5, 0.6, facing * CFrame.new(0, 6, 0), Color3.fromRGB(255, 200, 40), model)
		coin.Material = Enum.Material.Foil
		addText(coin, Enum.NormalId.Right, "B", Color3.fromRGB(120, 80, 0), 40)
		stationParts[def.Id] = coin
	else
		-- A board: text on the side facing the hub (the part's front).
		local height = if def.Id == "Leaderboard" then 16 else 11
		local board = newPart(
			"Board",
			Vector3.new(14, height, 0.6),
			facing * CFrame.new(0, 1 + height / 2 + 1, 0),
			Color3.fromRGB(35, 35, 45),
			model
		)
		if def.Id == "HowTo" then
			local gui = Instance.new("SurfaceGui")
			gui.Face = Enum.NormalId.Front
			gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			gui.PixelsPerStud = 30
			gui.Parent = board
			local text = Instance.new("TextLabel")
			text.Size = UDim2.fromScale(0.92, 0.72)
			text.Position = UDim2.fromScale(0.04, 0.24)
			text.BackgroundTransparency = 1
			text.Font = Enum.Font.GothamBold
			text.TextScaled = true
			text.TextWrapped = true
			text.TextXAlignment = Enum.TextXAlignment.Left
			text.TextYAlignment = Enum.TextYAlignment.Top
			text.TextColor3 = Color3.fromRGB(240, 240, 250)
			text.Text = HOW_TO
			text.Parent = gui
		end
		stationParts[def.Id] = board
	end

	-- Title sign above everything.
	local sign =
		newPart("Sign", Vector3.new(14, 3, 0.6), facing * CFrame.new(0, 17.5, 0), Color3.fromRGB(25, 25, 35), model)
	addText(sign, Enum.NormalId.Front, def.Title, def.Color, 30)
	if def.Subtitle ~= "" then
		local subtitle = Instance.new("BillboardGui")
		subtitle.Size = UDim2.fromOffset(260, 30)
		subtitle.StudsOffset = Vector3.new(0, -2.4, 0)
		subtitle.MaxDistance = 90
		subtitle.Parent = sign
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.FredokaOne
		label.TextScaled = true
		label.TextColor3 = Color3.fromRGB(230, 230, 240)
		label.TextStrokeTransparency = 0.3
		label.Text = def.Subtitle
		label.Parent = subtitle
	end

	if def.Prompt then
		local prompt = Instance.new("ProximityPrompt")
		prompt.Name = def.Id
		prompt.ActionText = "Open"
		prompt.ObjectText = def.Title
		prompt.HoldDuration = 0
		prompt.MaxActivationDistance = 14
		prompt.RequiresLineOfSight = false
		prompt.Parent = pedestal
	end

	model.Parent = parent
end

-- The part a station shows its content on (the leaderboard board, the wheel, the coin …).
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
	local plaza = cylinder(
		"Plaza",
		18,
		0.4,
		CFrame.new(HUB.Center + Vector3.new(0, 0.2, 0)),
		Color3.fromRGB(200, 190, 170),
		folder
	)
	plaza.Material = Enum.Material.Cobblestone

	-- Title pillar in the middle.
	local pillar = newPart(
		"Pillar",
		Vector3.new(4, 14, 4),
		CFrame.new(HUB.Center + Vector3.new(0, 7, 0)),
		Color3.fromRGB(60, 60, 75),
		folder
	)
	pillar.Material = Enum.Material.Slate
	local title = Instance.new("BillboardGui")
	title.Size = UDim2.fromOffset(500, 110)
	title.StudsOffset = Vector3.new(0, 11, 0)
	title.MaxDistance = 600
	title.Parent = pillar
	local titleLabel = Instance.new("TextLabel")
	titleLabel.Size = UDim2.fromScale(1, 1)
	titleLabel.BackgroundTransparency = 1
	titleLabel.Font = Enum.Font.FredokaOne
	titleLabel.TextScaled = true
	titleLabel.TextColor3 = Color3.fromRGB(255, 190, 40)
	titleLabel.TextStrokeTransparency = 0
	titleLabel.Text = "GET BONKED"
	titleLabel.Parent = title

	for index, def in STATIONS do
		-- Halfway between bridge `index` and the next one.
		local angle = (index - 0.5) / PLOTS.Count * 2 * math.pi
		buildStation(def, angle, folder)
	end

	folder.Parent = Workspace
end

return HubService
