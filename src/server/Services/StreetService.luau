--!strict
-- The street world (docs/GAME_DESIGN.md → Street, plots and buttons). With Config/Features.Street (and the tycoon) on it
-- replaces the islands: it builds one road with 10 plots (5 left, 5 right, Config/Street), gives each joining player a free
-- plot, spawns them on the road in front of it, puts fallen characters back and frees the plot when they leave.
-- IslandService stays untouched and returns early while this is on; its GetIsland/SpawnOnIsland delegate here, so
-- TycoonService and the others find the player's plot through the same Island record (Center, HubAngle, Model).
-- Phase 1: the plot is an empty lawn with an entrance mat and a name sign; the tycoon content follows in later phases.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Features = require(ReplicatedStorage.Shared.Config.Features)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local Tutorial = require(ReplicatedStorage.Shared.Config.Tutorial)
local World = require(ReplicatedStorage.Shared.Config.World)

local Signs = require(script.Parent.Parent.World.Signs)

local ISLAND = Gameplay.Island
local ROAD = Street.Road
local PLOT = Street.Plot

-- The same shape as IslandService.Island (structural typing), so the rest of the server needs no change.
export type Island = {
	Slot: number,
	-- Centre of the plot's top surface.
	Center: Vector3,
	-- Angle (0 = north/-Z, clockwise) of the direction from the plot toward the road.
	HubAngle: number,
	Color: Color3,
	-- Island_<UserId> in Workspace/Islands: what the client looks for.
	Model: Model,
	ProjectileFolder: Folder,
	ShooterFolder: Folder,
}

type Plot = {
	Slot: number,
	-- -1 = left of the road (-Z), 1 = right (+Z).
	Side: number,
	-- X of the plot's centre line.
	X: number,
	Center: Vector3,
	Color: Color3,
	NameLabel: TextLabel,
	Owner: Player?,
}

local ENABLED = Features.Street and Features.Tycoon

local islandsFolder: Folder
local plots: { Plot } = {}
local islands: { [Player]: Island } = {}

local StreetService = {}

local function newPart(
	name: string,
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	parent: Instance,
	solid: boolean
): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.CanCollide = solid
	part.CanQuery = solid
	part.CanTouch = false
	part.CastShadow = false
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

-- Distance from the road centre to where the plots start (road edge plus the sidewalk).
local function plotEdge(): number
	return ROAD.Width / 2 + ROAD.SidewalkWidth
end

local function buildRoad(parent: Instance)
	local origin = Street.Origin
	local length = Street.PlotsPerSide * Street.PlotPitch + ROAD.Margin * 2
	local below = Vector3.new(0, ROAD.Thickness / 2, 0)
	newPart(
		"Road",
		Vector3.new(length, ROAD.Thickness, ROAD.Width),
		CFrame.new(origin - below),
		ROAD.Color,
		parent,
		true
	)
	for _, side in { -1, 1 } do
		local z = side * (ROAD.Width / 2 + ROAD.SidewalkWidth / 2)
		newPart(
			"Sidewalk",
			Vector3.new(length, ROAD.Thickness, ROAD.SidewalkWidth),
			CFrame.new(origin + Vector3.new(0, 0, z) - below),
			ROAD.SidewalkColor,
			parent,
			true
		)
	end
	local step = ROAD.DashLength + ROAD.DashGap
	local x = -length / 2 + ROAD.DashLength
	while x < length / 2 - ROAD.DashLength do
		newPart(
			"Dash",
			Vector3.new(ROAD.DashLength, 0.1, 0.6),
			CFrame.new(origin + Vector3.new(x, 0.05, 0)),
			ROAD.DashColor,
			parent,
			false
		)
		x += step
	end
end

local function buildPlot(slot: number, parent: Instance): Plot
	local origin = Street.Origin
	local side = if slot % 2 == 1 then -1 else 1
	local index = math.ceil(slot / 2)
	local x = origin.X + (index - (Street.PlotsPerSide + 1) / 2) * Street.PlotPitch
	local edge = plotEdge()
	local centerZ = origin.Z + side * (edge + Street.PlotDepth / 2)
	local center = Vector3.new(x, origin.Y, centerZ)
	local color = World.PlotColors[(slot - 1) % #World.PlotColors + 1]

	local model = Instance.new("Model")
	model.Name = `Plot{slot}`
	local ground = newPart(
		"Ground",
		Vector3.new(Street.PlotWidth, Street.PlotThickness, Street.PlotDepth),
		CFrame.new(center - Vector3.new(0, Street.PlotThickness / 2, 0)),
		PLOT.GroundColor,
		model,
		true
	)
	ground.Material = Enum.Material.Grass

	-- Entrance mat at the road end of the plot, in the plot's own colour.
	newPart(
		"EntranceMat",
		Vector3.new(Street.PlotWidth, 0.2, PLOT.EntranceDepth),
		CFrame.new(Vector3.new(x, origin.Y + 0.1, origin.Z + side * (edge + PLOT.EntranceDepth / 2))),
		color,
		model,
		false
	)

	-- Name sign at the road end, facing the road.
	local signX = x + Street.PlotWidth / 2 - 4
	local signZ = origin.Z + side * (edge + 2)
	local post = newPart(
		"SignPost",
		Vector3.new(0.8, PLOT.SignHeight, 0.8),
		CFrame.new(Vector3.new(signX, origin.Y + PLOT.SignHeight / 2, signZ)),
		Color3.fromRGB(110, 80, 55),
		model,
		false
	)
	post.Material = Enum.Material.Wood
	local boardAt = Vector3.new(signX, origin.Y + PLOT.SignHeight, signZ)
	local board = newPart(
		"SignBoard",
		PLOT.SignSize,
		CFrame.lookAt(boardAt, boardAt + Vector3.new(0, 0, -side)),
		Color3.fromRGB(35, 30, 45),
		model,
		false
	)
	local label = Signs.Text(board, Enum.NormalId.Front, PLOT.FreeText, color)
	Signs.Mirror(board, label)

	model.Parent = parent
	return { Slot = slot, Side = side, X = x, Center = center, Color = color, NameLabel = label }
end

-- ==== players ==========================================================================================================

function StreetService.IsEnabled(): boolean
	return ENABLED
end

function StreetService.GetIsland(player: Player): Island?
	return islands[player]
end

-- The plot the player owns (spawn and later phases), nil without one.
local function plotOf(player: Player): Plot?
	local island = islands[player]
	return if island then plots[island.Slot] else nil
end

-- Puts the character on the road in front of its plot (the middle of the road without a plot, server full).
function StreetService.SpawnOnStreet(player: Player)
	local character = player.Character
	if not character then
		return
	end
	local origin = Street.Origin
	local plot = plotOf(player)
	if plot then
		local position = Vector3.new(plot.X, origin.Y + Street.SpawnHeight, origin.Z + plot.Side * Street.SpawnOffset)
		character:PivotTo(CFrame.lookAt(position, position + Vector3.new(0, 0, plot.Side)))
	else
		local position = origin + Vector3.new(0, Street.SpawnHeight, 0)
		character:PivotTo(CFrame.lookAt(position, position + Vector3.new(1, 0, 0)))
	end
end

local function onCharacterAdded(player: Player, character: Model)
	character:WaitForChild("HumanoidRootPart", 10)
	-- Let the default spawn finish first, otherwise it can override our position.
	task.wait()
	if player.Character == character then
		StreetService.SpawnOnStreet(player)
	end
end

local function claim(player: Player, plot: Plot)
	plot.Owner = player
	Signs.SetText(plot.NameLabel, `{player.DisplayName}'s Plot`)

	local model = Instance.new("Model")
	model.Name = `{ISLAND.ModelPrefix}{player.UserId}`
	model:SetAttribute(Tutorial.IslandCenterAttribute, plot.Center)
	local projectileFolder = Instance.new("Folder")
	projectileFolder.Name = "Projectiles"
	projectileFolder.Parent = model
	local shooterFolder = Instance.new("Folder")
	shooterFolder.Name = "Shooters"
	shooterFolder.Parent = model
	model.Parent = islandsFolder

	islands[player] = {
		Slot = plot.Slot,
		Center = plot.Center,
		-- The road is on the other side of the owner's plot: north (0) for the right side, south (pi) for the left.
		HubAngle = if plot.Side > 0 then 0 else math.pi,
		Color = plot.Color,
		Model = model,
		ProjectileFolder = projectileFolder,
		ShooterFolder = shooterFolder,
	}
end

local function onPlayerAdded(player: Player)
	for _, plot in plots do
		if not plot.Owner then
			claim(player, plot)
			break
		end
	end
	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
	if player.Character then
		task.spawn(onCharacterAdded, player, player.Character)
	end
end

local function onPlayerRemoving(player: Player)
	local island = islands[player]
	if not island then
		return
	end
	islands[player] = nil
	local plot = plots[island.Slot]
	plot.Owner = nil
	Signs.SetText(plot.NameLabel, PLOT.FreeText)
	island.Model:Destroy()
end

function StreetService.Init()
	if not ENABLED then
		return
	end
	islandsFolder = Instance.new("Folder")
	islandsFolder.Name = ISLAND.FolderName
	islandsFolder.Parent = Workspace

	local streetFolder = Instance.new("Folder")
	streetFolder.Name = "Street"
	buildRoad(streetFolder)
	for slot = 1, Street.PlotCount do
		table.insert(plots, buildPlot(slot, streetFolder))
	end
	streetFolder.Parent = Workspace
end

function StreetService.Start()
	if not ENABLED then
		return
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	local sinceCheck = 0
	RunService.Heartbeat:Connect(function(deltaTime)
		sinceCheck += deltaTime
		if sinceCheck < Street.FallCheckInterval then
			return
		end
		sinceCheck = 0
		for _, player in Players:GetPlayers() do
			local character = player.Character
			local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
			if root and root:IsA("BasePart") and root.Position.Y < Street.FallOffY then
				StreetService.SpawnOnStreet(player)
			end
		end
	end)
end

return StreetService
