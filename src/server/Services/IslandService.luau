--!strict
-- The player islands around the hub (Config/World): builds all plots with their bridges once, gives each joining
-- player a free plot (tycoon style), spawns them on it (brand-new players in front of the NEW SHIBA pad, see
-- Config/Tutorial), puts fallen characters back, and frees the plot when they leave. Players without a plot (server full) stay on the hub. The hub itself is built by HubService.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Stations = require(ReplicatedStorage.Shared.Config.Stations)
local Tutorial = require(ReplicatedStorage.Shared.Config.Tutorial)
local World = require(ReplicatedStorage.Shared.Config.World)

local DataService = require(script.Parent.DataService)
local PropService = require(script.Parent.PropService)
local Signs = require(script.Parent.Parent.World.Signs)

local ISLAND = Gameplay.Island
local HUB = World.Hub
local PLOTS = World.Plots
local BRIDGE = World.Bridge
local DECOR = World.Decor

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

-- Plank bridge with rails and lamps from the hub edge to the island edge.
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
	-- Lamps on alternating sides.
	for index = 1, DECOR.LampsPerBridge do
		local along = -length / 2 + length * (index - 0.5) / DECOR.LampsPerBridge
		local side = if index % 2 == 0 then 1 else -1
		PropService.Place(
			"Prop_Lamp",
			base * CFrame.new(side * (BRIDGE.Width / 2 + 0.6), 0, along),
			7,
			PropService.Builders.Lamp,
			model
		)
	end
	model.Parent = parent
end

-- The field in the middle of an island: a sandy disc with a low border, open toward the bridge.
local function buildField(center: Vector3, hubAngle: number, parent: Instance)
	local field = newPart(
		"Field",
		Vector3.new(0.3, ISLAND.FieldRadius * 2, ISLAND.FieldRadius * 2),
		CFrame.new(center + Vector3.new(0, -0.1, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(235, 215, 160),
		parent
	)
	field.Shape = Enum.PartType.Cylinder
	field.Material = Enum.Material.Sand

	-- The border: short blocks around the circle, leaving a gap toward the hub.
	local segments = 40
	local radius = ISLAND.FieldRadius + ISLAND.BorderWidth / 2
	local segmentLength = 2 * math.pi * radius / segments + 0.3
	local halfGap = math.rad(ISLAND.BorderGapDegrees) / 2
	for index = 0, segments - 1 do
		local angle = index / segments * 2 * math.pi
		local fromGap = math.abs(math.atan2(math.sin(angle - hubAngle), math.cos(angle - hubAngle)))
		if fromGap < halfGap then
			continue
		end
		local position = center + direction(angle) * radius + Vector3.new(0, ISLAND.BorderHeight / 2, 0)
		local block = newPart(
			"Border",
			Vector3.new(ISLAND.BorderWidth, ISLAND.BorderHeight, segmentLength),
			CFrame.lookAt(position, position + direction(angle + math.pi / 2)),
			Color3.fromRGB(245, 245, 250),
			parent
		)
		block.Material = Enum.Material.SmoothPlastic
	end
end

-- Island-relative polar spot (Config/Stations: degrees clockwise from the bridge, studs from the centre).
local function polar(center: Vector3, hubAngle: number, angleDegrees: number, radius: number): Vector3
	return center + direction(hubAngle + math.rad(angleDegrees)) * radius
end

-- One wooden sign per zone behind its stalls, the title in the zone colour, facing the island centre and high
-- enough to read over the stalls and their billboards.
local function buildZoneSigns(center: Vector3, hubAngle: number, parent: Instance)
	local sign = Stations.ZoneSign
	local boardBottom = sign.BoardHeight - sign.BoardSize.Y / 2
	-- Posts reach from under the surface into the board, behind it so they don't cover the text.
	local postBottom = -0.5
	local postTop = boardBottom + 0.7
	for _, zone in Stations.Zones do
		local position = polar(center, hubAngle, zone.Angle, zone.Radius)
		local facing = CFrame.lookAt(position, Vector3.new(center.X, position.Y, center.Z))
		local signModel = Instance.new("Model")
		signModel.Name = `ZoneSign_{zone.Id}`
		for _, side in { -1, 1 } do
			local post = newPart(
				"Post",
				Vector3.new(sign.PostWidth, postTop - postBottom, sign.PostWidth),
				facing
					* CFrame.new(
						side * sign.PostOffset,
						(postBottom + postTop) / 2,
						sign.BoardSize.Z / 2 + sign.PostWidth / 2
					),
				sign.PostColor,
				signModel
			)
			post.Material = Enum.Material.Wood
		end
		local board =
			newPart("Board", sign.BoardSize, facing * CFrame.new(0, sign.BoardHeight, 0), sign.BoardColor, signModel)
		board.Material = Enum.Material.WoodPlanks
		Signs.Text(board, Enum.NormalId.Front, zone.Title, zone.Color)
		signModel.Parent = parent
	end
end

-- The path ring (Config/Stations → PathRing): flat, non-colliding segments at the path radius from the bridge
-- clockwise to the rebirth shrine, and a link from where the bridge arrives. Every second segment sits a little
-- higher, so the overlapping corners never flicker.
local function buildPath(center: Vector3, hubAngle: number, parent: Instance)
	local path = Stations.PathRing
	local model = Instance.new("Model")
	model.Name = "PathRing"
	local function slab(size: Vector3, position: Vector3, along: Vector3, top: number, color: Color3): Part
		local y = center.Y + top - path.Thickness / 2
		local at = Vector3.new(position.X, y, position.Z)
		local piece = newPart("Path", size, CFrame.lookAt(at, at + along), color, model)
		piece.Material = path.Material
		piece.CanCollide = false
		piece.CanQuery = false
		piece.CanTouch = false
		piece.CastShadow = false
		return piece
	end

	local span = path.ToAngle - path.FromAngle
	local count = math.ceil(span / path.SegmentDegrees)
	local step = span / count
	-- Long enough to close the gap at the outer edge of the curve.
	local length = 2 * (path.Radius + path.Width / 2) * math.tan(math.rad(step) / 2) + 0.1
	for index = 0, count - 1 do
		local middle = path.FromAngle + (index + 0.5) * step
		local tangent = direction(hubAngle + math.rad(middle + 90))
		slab(
			Vector3.new(path.Width, path.Thickness, length),
			polar(center, hubAngle, middle, path.Radius),
			tangent,
			path.TopHeight + (index % 2) * path.TopStep,
			path.Colors[index % #path.Colors + 1]
		)
	end

	-- From the bridge's end to the ring, along the bridge direction.
	local linkLength = path.LinkTo - path.LinkFrom
	slab(
		Vector3.new(path.LinkWidth, path.Thickness, linkLength),
		polar(center, hubAngle, 0, (path.LinkFrom + path.LinkTo) / 2),
		direction(hubAngle),
		path.TopHeight + 2 * path.TopStep,
		path.Colors[1]
	)
	model.Parent = parent
end

-- Trees and flowers in the grove (Config/Stations → Grove): the sector between the rebirth shrine and the bridge,
-- where no stall, sign or path stands, so they never block a stall or the view between the zones.
local function buildGrove(center: Vector3, hubAngle: number, slot: number, parent: Instance)
	local grove = Stations.Grove
	local random = Random.new(slot)
	local count = DECOR.TreesPerIsland
	for index = 1, count do
		local angle = grove.FromAngle + (index - 0.5) / count * (grove.ToAngle - grove.FromAngle)
		local radius = grove.Radii[(index - 1) % #grove.Radii + 1]
		PropService.Place(
			"Prop_Tree",
			CFrame.new(polar(center, hubAngle, angle, radius)) * CFrame.Angles(0, random:NextNumber(0, 2 * math.pi), 0),
			random:NextNumber(11, 15),
			PropService.Builders.Tree,
			parent
		)
		local flowerPosition = polar(center, hubAngle, angle + grove.FlowerAngle, radius - grove.FlowerInset)
		PropService.Place("Prop_Flowers", CFrame.new(flowerPosition), 1.5, PropService.Builders.Flowers, parent)
	end
end

local function buildPlot(slot: number, parent: Instance): Plot
	local angle = (slot - 1) / PLOTS.Count * 2 * math.pi
	local center = HUB.Center + direction(angle) * PLOTS.Distance
	local color = World.PlotColors[(slot - 1) % #World.PlotColors + 1]
	local hubAngle = angle + math.pi

	local model = Instance.new("Model")
	model.Name = `Plot{slot}`
	-- A cylinder's axis is its X axis, so rotate it upright.
	local ground = newPart(
		"Ground",
		Vector3.new(ISLAND.Thickness, ISLAND.Radius * 2, ISLAND.Radius * 2),
		CFrame.new(center - Vector3.new(0, ISLAND.Thickness / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(95, 185, 85),
		model
	)
	ground.Shape = Enum.PartType.Cylinder
	ground.Material = Enum.Material.Grass
	-- A coloured rim so every island has its own colour.
	local rim = newPart(
		"Rim",
		Vector3.new(ISLAND.Thickness + 0.4, ISLAND.Radius * 2 + 2, ISLAND.Radius * 2 + 2),
		CFrame.new(center - Vector3.new(0, ISLAND.Thickness / 2 + 0.3, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		model
	)
	rim.Shape = Enum.PartType.Cylinder

	buildField(center, hubAngle, model)

	-- Floating-island rock underneath.
	PropService.Place(
		"Prop_IslandRock",
		CFrame.new(center - Vector3.new(0, ISLAND.Thickness, 0)),
		ISLAND.Radius * 0.9,
		PropService.Builders.IslandRock,
		model
	)

	-- The same for every owner, so built once per plot: zone signs, the path ring and the tree grove
	-- (Config/Stations; the stalls themselves are per player, StationService).
	buildZoneSigns(center, hubAngle, model)
	buildPath(center, hubAngle, model)
	buildGrove(center, hubAngle, slot, model)

	-- Owner name on a sign post where the bridge arrives.
	local signPosition = center + direction(hubAngle) * (ISLAND.Radius - 8) + direction(hubAngle + math.pi / 2) * 9
	local post = newPart(
		"SignPost",
		Vector3.new(0.8, 9, 0.8),
		CFrame.new(signPosition + Vector3.new(0, 4.5, 0)),
		Color3.fromRGB(110, 80, 55),
		model
	)
	post.Material = Enum.Material.Wood
	local board = newPart(
		"SignBoard",
		Vector3.new(14, 3.4, 0.5),
		CFrame.lookAt(signPosition + Vector3.new(0, 9, 0), signPosition + Vector3.new(0, 9, 0) + direction(hubAngle)),
		Color3.fromRGB(35, 30, 45),
		model
	)
	local label = Signs.Text(board, Enum.NormalId.Front, "Free Island", color)
	-- Readable from the other side as well.
	Signs.Mirror(board, label)

	model.Parent = parent
	buildBridge(angle, parent)
	return { Slot = slot, Center = center, Angle = angle, Color = color, NameLabel = label }
end

local function hubSpawn(): CFrame
	-- In front of the how-to-play board, looking at it and the statue behind it.
	local position = HUB.Center + Vector3.new(0, ISLAND.SpawnHeight, 32)
	return CFrame.lookAt(position, HUB.Center + Vector3.new(0, ISLAND.SpawnHeight, 0))
end

function IslandService.GetIsland(player: Player): Island?
	return islands[player]
end

-- Brand-new players (Tutorial.IsFresh) spawn at Stations.NewPlayerSpawn facing the island centre, so the NEW SHIBA
-- pad (their first purchase, on the Shiba ring at the same angle) is right in front of them.
local function newPlayerSpawn(island: Island): CFrame
	local spot = Stations.NewPlayerSpawn
	local up = Vector3.new(0, ISLAND.SpawnHeight, 0)
	local position = island.Center + direction(island.HubAngle + math.rad(spot.Angle)) * spot.Radius + up
	return CFrame.lookAt(position, island.Center + up)
end

local function isFresh(player: Player): boolean
	local state = DataService.GetState(player)
	return state ~= nil and Tutorial.IsFresh(state)
end

-- Puts the character on its island (or the hub without one).
function IslandService.SpawnOnIsland(player: Player)
	local island = islands[player]
	local character = player.Character
	if not character then
		return
	end
	if island and isFresh(player) then
		character:PivotTo(newPlayerSpawn(island))
	elseif island then
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
	Signs.SetText(plot.NameLabel, `{player.DisplayName}'s Island`)

	local model = Instance.new("Model")
	model.Name = `{ISLAND.ModelPrefix}{player.UserId}`
	-- The client's guidance (TutorialController) points at the field with it: the model has no parts to take it from.
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
	Signs.SetText(plot.NameLabel, "Free Island")
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
	-- The save usually loads after the first spawn (and an admin reset makes a fresh save): once the player is known
	-- to be brand-new, move the character to the new-player spawn in front of the NEW SHIBA pad.
	DataService.OnLoaded(function(player)
		if player.Character and islands[player] and isFresh(player) then
			IslandService.SpawnOnIsland(player)
		end
	end)

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
