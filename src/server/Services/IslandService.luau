--!strict
-- The player islands around the hub (Config/World): builds all plots with their bridges once, gives each joining
-- player a free plot (tycoon style), spawns them on it, puts fallen characters back, and frees the plot when they
-- leave. Players without a plot (server full) stay on the hub. The hub itself is built by HubService.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local World = require(ReplicatedStorage.Shared.Config.World)

local ISLAND = Gameplay.Island
local HUB = World.Hub
local PLOTS = World.Plots
local BRIDGE = World.Bridge

export type Island = {
	Slot: number,
	-- Centre of the island's top surface.
	Center: Vector3,
	-- Direction from the island toward the hub, as an angle (0 = north/−Z, clockwise). The bridge arrives here,
	-- so the shooter ring leaves a gap on this side.
	HubAngle: number,
	Color: Color3,
	-- Island_<UserId>: projectiles and shooters live inside, so they go away together with the claim.
	Model: Model,
	ProjectileFolder: Folder,
	ShooterFolder: Folder,
}

type Plot = {
	Slot: number,
	Center: Vector3,
	Angle: number,
	Color: Color3,
	NameLabel: TextLabel,
	Owner: Player?,
}

local islandsFolder: Folder
local plots: { Plot } = {}
local islands: { [Player]: Island } = {}

local IslandService = {}

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

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

-- Plank bridge with rails from the hub edge to the island edge.
local function buildBridge(angle: number, parent: Instance)
	local dir = direction(angle)
	local startDistance = HUB.Radius - 2
	local endDistance = PLOTS.Distance - ISLAND.Radius + 2
	local length = endDistance - startDistance
	local middle = HUB.Center + dir * (startDistance + length / 2)
	local base = CFrame.lookAt(middle, middle + dir)

	local model = Instance.new("Model")
	model.Name = "Bridge"
	local deck = newPart(
		"Deck",
		Vector3.new(BRIDGE.Width, BRIDGE.Thickness, length),
		base * CFrame.new(0, -BRIDGE.Thickness / 2, 0),
		BRIDGE.Color,
		model
	)
	deck.Material = Enum.Material.WoodPlanks
	for _, side in { -1, 1 } do
		local rail = newPart(
			"Rail",
			Vector3.new(0.6, BRIDGE.RailHeight, length),
			base * CFrame.new(side * (BRIDGE.Width / 2 - 0.3), BRIDGE.RailHeight / 2, 0),
			BRIDGE.RailColor,
			model
		)
		rail.Material = Enum.Material.Wood
	end
	model.Parent = parent
end

local function buildPlot(slot: number, parent: Instance): Plot
	local angle = (slot - 1) / PLOTS.Count * 2 * math.pi
	local center = HUB.Center + direction(angle) * PLOTS.Distance
	local color = World.PlotColors[(slot - 1) % #World.PlotColors + 1]

	local model = Instance.new("Model")
	model.Name = `Plot{slot}`
	-- A cylinder's axis is its X axis, so rotate it upright.
	local ground = newPart(
		"Ground",
		Vector3.new(ISLAND.Thickness, ISLAND.Radius * 2, ISLAND.Radius * 2),
		CFrame.new(center - Vector3.new(0, ISLAND.Thickness / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		model
	)
	ground.Shape = Enum.PartType.Cylinder
	ground.Material = Enum.Material.Grass

	-- Owner name floating above the island.
	local anchor = newPart("NameAnchor", Vector3.one, CFrame.new(center + Vector3.new(0, 22, 0)), color, model)
	anchor.Transparency = 1
	anchor.CanCollide = false
	anchor.CanQuery = false
	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(400, 60)
	billboard.MaxDistance = 400
	billboard.Parent = anchor
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = color
	label.TextStrokeTransparency = 0
	label.Text = "Free Island"
	label.Parent = billboard

	model.Parent = parent
	buildBridge(angle, parent)
	return { Slot = slot, Center = center, Angle = angle, Color = color, NameLabel = label }
end

local function hubSpawn(): CFrame
	return CFrame.new(HUB.Center + Vector3.new(0, ISLAND.SpawnHeight, 12))
end

function IslandService.GetIsland(player: Player): Island?
	return islands[player]
end

-- Puts the character on its island (or the hub without one).
function IslandService.SpawnOnIsland(player: Player)
	local island = islands[player]
	local character = player.Character
	if not character then
		return
	end
	if island then
		-- Facing the hub, so the way back is obvious.
		local position = island.Center + Vector3.new(0, ISLAND.SpawnHeight, 0)
		character:PivotTo(CFrame.lookAt(position, position + direction(island.HubAngle)))
	else
		character:PivotTo(hubSpawn())
	end
end

function IslandService.TeleportToHub(player: Player)
	local character = player.Character
	if character then
		character:PivotTo(hubSpawn())
	end
end

local function onCharacterAdded(player: Player, character: Model)
	character:WaitForChild("HumanoidRootPart", 10)
	-- Let the default spawn finish placing the character first, otherwise it can override our position.
	task.wait()
	if player.Character == character then
		IslandService.SpawnOnIsland(player)
	end
end

local function claim(player: Player, plot: Plot)
	plot.Owner = player
	plot.NameLabel.Text = `{player.DisplayName}'s Island`

	local model = Instance.new("Model")
	model.Name = `{ISLAND.ModelPrefix}{player.UserId}`
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
		HubAngle = plot.Angle + math.pi,
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
	plot.NameLabel.Text = "Free Island"
	island.Model:Destroy()
end

function IslandService.Init()
	islandsFolder = Instance.new("Folder")
	islandsFolder.Name = ISLAND.FolderName
	islandsFolder.Parent = Workspace

	local plotsFolder = Instance.new("Folder")
	plotsFolder.Name = "Plots"
	for slot = 1, PLOTS.Count do
		table.insert(plots, buildPlot(slot, plotsFolder))
	end
	plotsFolder.Parent = Workspace
end

function IslandService.Start()
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	local sinceCheck = 0
	RunService.Heartbeat:Connect(function(deltaTime)
		sinceCheck += deltaTime
		if sinceCheck < ISLAND.FallCheckInterval then
			return
		end
		sinceCheck = 0
		for _, player in Players:GetPlayers() do
			local character = player.Character
			local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
			if root and root:IsA("BasePart") and root.Position.Y < ISLAND.FallOffY then
				IslandService.SpawnOnIsland(player)
			end
		end
	end)
end

return IslandService
