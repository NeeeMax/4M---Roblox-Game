--!strict
-- One island per player: assigns a grid slot on join, builds the island, spawns the character on it,
-- puts fallen characters back, and removes the island (with everything on it) when the player leaves.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local ISLAND = Gameplay.Island

export type Island = {
	Slot: number,
	-- Centre of the island's top surface.
	Center: Vector3,
	Model: Model,
	-- Projectiles and shooters are parented here so they are destroyed together with the island.
	ProjectileFolder: Folder,
	ShooterFolder: Folder,
}

local islandsFolder: Folder
local islands: { [Player]: Island } = {}
local usedSlots: { [number]: boolean } = {}

local IslandService = {}

local function slotCenter(slot: number): Vector3
	local column = slot % ISLAND.GridColumns
	local row = slot // ISLAND.GridColumns
	return Vector3.new(column * ISLAND.GridSpacing, ISLAND.SurfaceY, row * ISLAND.GridSpacing)
end

local function buildIsland(player: Player, slot: number): Island
	local center = slotCenter(slot)

	local model = Instance.new("Model")
	model.Name = `Island_{player.UserId}`

	-- A cylinder's axis is its X axis, so rotate it upright.
	local ground = Instance.new("Part")
	ground.Name = "Ground"
	ground.Shape = Enum.PartType.Cylinder
	ground.Size = Vector3.new(ISLAND.Thickness, ISLAND.Radius * 2, ISLAND.Radius * 2)
	ground.CFrame = CFrame.new(center - Vector3.new(0, ISLAND.Thickness / 2, 0)) * CFrame.Angles(0, 0, math.rad(90))
	ground.Anchored = true
	ground.Material = Enum.Material.Grass
	ground.Color = Color3.fromRGB(90, 190, 80)
	ground.TopSurface = Enum.SurfaceType.Smooth
	ground.BottomSurface = Enum.SurfaceType.Smooth
	ground.Parent = model

	local projectileFolder = Instance.new("Folder")
	projectileFolder.Name = "Projectiles"
	projectileFolder.Parent = model

	local shooterFolder = Instance.new("Folder")
	shooterFolder.Name = "Shooters"
	shooterFolder.Parent = model

	model.PrimaryPart = ground
	model.Parent = islandsFolder

	return {
		Slot = slot,
		Center = center,
		Model = model,
		ProjectileFolder = projectileFolder,
		ShooterFolder = shooterFolder,
	}
end

local function spawnOnIsland(player: Player)
	local island = islands[player]
	local character = player.Character
	if island and character then
		character:PivotTo(CFrame.new(island.Center + Vector3.new(0, ISLAND.SpawnHeight, 0)))
	end
end

local function onCharacterAdded(player: Player, character: Model)
	character:WaitForChild("HumanoidRootPart", 10)
	-- Let the default spawn finish placing the character first, otherwise it can override our position.
	task.wait()
	if player.Character == character then
		spawnOnIsland(player)
	end
end

local function onPlayerAdded(player: Player)
	local slot = 0
	while usedSlots[slot] do
		slot += 1
	end
	usedSlots[slot] = true
	islands[player] = buildIsland(player, slot)

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
	usedSlots[island.Slot] = nil
	island.Model:Destroy()
end

function IslandService.GetIsland(player: Player): Island?
	return islands[player]
end

function IslandService.Init()
	islandsFolder = Instance.new("Folder")
	islandsFolder.Name = "Islands"
	islandsFolder.Parent = Workspace
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
		for player in islands do
			local character = player.Character
			local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
			if root and root:IsA("BasePart") and root.Position.Y < ISLAND.FallOffY then
				spawnOnIsland(player)
			end
		end
	end)
end

return IslandService
