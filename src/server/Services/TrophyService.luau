--!strict
-- Shows each player's trophies (Config/Shop → Trophies) on their island: a row of lit pedestals behind the field,
-- opposite the bridge, visible to everyone. Rebuilt whenever the owned set changes. Models: Trophy_<Id>
-- (PropService placeholders until Marco builds them). The Party trophy's sign counts the Bonk Parties finished
-- ("Bonk Party ×3").

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local DataService = require(script.Parent.DataService)
local IslandService = require(script.Parent.IslandService)
local PropService = require(script.Parent.PropService)
local Signs = require(script.Parent.Parent.World.Signs)

local ISLAND = Gameplay.Island
local DISTANCE = ISLAND.FieldRadius + 12
local SPACING_DEGREES = 11

local shown: { [Player]: string } = {}

local TrophyService = {}

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

local function rebuild(player: Player)
	local state = DataService.GetState(player)
	local island = IslandService.GetIsland(player)
	if not state or not island then
		return
	end
	local owned: { Shop.Trophy } = {}
	for _, trophy in Shop.Trophies do
		if state.Trophies[trophy.Id] then
			table.insert(owned, trophy)
		end
	end
	-- The party count is part of the key: a new party trophy renames the sign.
	local key = `{state.Party.Count};`
	for _, trophy in owned do
		key ..= trophy.Id .. ","
	end
	if shown[player] == key then
		return
	end
	shown[player] = key

	local old = island.Model:FindFirstChild("Trophies")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "Trophies"
	local back = island.HubAngle + math.pi
	for index, trophy in owned do
		local offset = (index - (#owned + 1) / 2) * math.rad(SPACING_DEGREES)
		local position = island.Center + direction(back + offset) * DISTANCE
		local facing = CFrame.lookAt(position, Vector3.new(island.Center.X, position.Y, island.Center.Z))
		local pedestal = Instance.new("Part")
		pedestal.Name = "Pedestal"
		pedestal.Size = Vector3.new(3.4, 2, 3.4)
		pedestal.CFrame = facing * CFrame.new(0, 1, 0)
		pedestal.Anchored = true
		pedestal.Color = Color3.fromRGB(45, 42, 60)
		pedestal.Material = Enum.Material.Marble
		pedestal.Parent = folder
		local glow = Instance.new("PointLight")
		glow.Color = trophy.Color
		glow.Range = 10
		glow.Brightness = 2
		glow.Parent = pedestal
		local builder = if trophy.Id == "BonkBuddies"
			then PropService.BuddiesTrophyBuilder(trophy.Color)
			else PropService.TrophyBuilder(trophy.Color)
		PropService.Place(`Trophy_{trophy.Id}`, facing * CFrame.new(0, 2, 0), 4, builder, folder)
		local title = if trophy.Id == "Party" and state.Party.Count > 1
			then `{trophy.DisplayName} ×{state.Party.Count}`
			else trophy.DisplayName
		Signs.Billboard(pedestal, title, trophy.Color, Vector2.new(160, 24), 5.8, 60)
	end
	folder.Parent = island.Model
end

function TrophyService.Start()
	DataService.OnReplicated(rebuild)
	Players.PlayerRemoving:Connect(function(player)
		shown[player] = nil
	end)
end

return TrophyService
