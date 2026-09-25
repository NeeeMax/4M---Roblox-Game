--!strict
-- Leaderboards (Config/Hub → Leaderboard): "Bonk Dollars" in the Roblox player list (leaderstats), and the
-- TOP BONKERS board on the hub, ranked by TotalEarned across all servers (OrderedDataStore). Without DataStore
-- access (Studio without API access) the board ranks the players in this server instead.
-- Big numbers: an OrderedDataStore only keeps whole numbers below 2^63 (~9.2e18) and an IntValue overflows there too,
-- but totals reach 1e33 and more. So the store keeps log10(total + 1) × LOG_SCALE (1e33 → 3.3e15; order kept), and the
-- player list shows the amount as short text in a StringValue ("1.5Dc").

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)

local DataService = require(script.Parent.DataService)
local HubService = require(script.Parent.HubService)

local CONFIG = Hub.Leaderboard
-- Stored value = floor(log10(total + 1) × LOG_SCALE). 1e14 keeps it below 2^53 (exact in a double) up to totals of
-- 1e90, and gives ~14 significant digits back.
local LOG_SCALE = 1e14

type Row = { Name: string, Value: number }

local store: OrderedDataStore? = nil
local nameCache: { [number]: string } = {}
local rowLabels: { TextLabel } = {}
local footer: TextLabel

local LeaderboardService = {}

-- Total earned → the whole number kept in the OrderedDataStore (same order as the totals).
function LeaderboardService.Encode(total: number): number
	-- `total ~= total` = NaN.
	if total ~= total or total <= 0 then
		return 0
	end
	return math.floor(math.log10(total + 1) * LOG_SCALE)
end

-- The OrderedDataStore number → total earned (rounded; big totals are only shown short anyway).
function LeaderboardService.Decode(value: number): number
	return math.max(0, math.floor(10 ^ (value / LOG_SCALE) - 1 + 0.5))
end

local function buildBoard()
	local board = HubService.GetStationPart("Leaderboard")
	if not board then
		return
	end
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 30
	gui.Parent = board
	local list = Instance.new("Frame")
	list.Size = UDim2.fromScale(0.92, 0.86)
	list.Position = UDim2.fromScale(0.04, 0.04)
	list.BackgroundTransparency = 1
	list.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0.01, 0)
	layout.Parent = list
	for rank = 1, CONFIG.Size do
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1 / CONFIG.Size - 0.01)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.FredokaOne
		label.TextScaled = true
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextColor3 = if rank == 1
			then Color3.fromRGB(255, 210, 60)
			elseif rank == 2 then Color3.fromRGB(210, 210, 225)
			elseif rank == 3 then Color3.fromRGB(230, 150, 80)
			else Color3.fromRGB(235, 235, 245)
		label.Text = `{rank}.  —`
		label.LayoutOrder = rank
		label.Parent = list
		table.insert(rowLabels, label)
	end
	footer = Instance.new("TextLabel")
	footer.Size = UDim2.fromScale(0.92, 0.06)
	footer.Position = UDim2.fromScale(0.04, 0.92)
	footer.BackgroundTransparency = 1
	footer.Font = Enum.Font.Gotham
	footer.TextScaled = true
	footer.TextColor3 = Color3.fromRGB(160, 160, 180)
	footer.Text = ""
	footer.Parent = gui
end

local function nameOf(userId: number): string
	local cached = nameCache[userId]
	if cached then
		return cached
	end
	local ok, name = pcall(function()
		return Players:GetNameFromUserIdAsync(userId)
	end)
	local result = if ok and typeof(name) == "string" then name else `Player {userId}`
	nameCache[userId] = result
	return result
end

local function serverRows(): { Row }
	local rows: { Row } = {}
	for _, player in Players:GetPlayers() do
		local state = DataService.GetState(player)
		if state then
			table.insert(rows, { Name = player.DisplayName, Value = state.TotalEarned })
		end
	end
	table.sort(rows, function(a, b)
		return a.Value > b.Value
	end)
	return rows
end

-- Saves this server's players, then reads the global top list. Returns nil if the DataStore isn't reachable.
local function globalRows(): { Row }?
	local currentStore = store
	if not currentStore then
		return nil
	end
	for _, player in Players:GetPlayers() do
		local state = DataService.GetState(player)
		if state then
			pcall(function()
				currentStore:SetAsync(tostring(player.UserId), LeaderboardService.Encode(state.TotalEarned))
			end)
		end
	end
	local ok, pages = pcall(function()
		return currentStore:GetSortedAsync(false, CONFIG.Size)
	end)
	if not ok then
		return nil
	end
	local rows: { Row } = {}
	for _, entry in (pages :: DataStorePages):GetCurrentPage() do
		local userId = tonumber(entry.key)
		if userId then
			table.insert(rows, { Name = nameOf(userId), Value = LeaderboardService.Decode(entry.value) })
		end
	end
	return rows
end

local function refreshBoard()
	if #rowLabels == 0 then
		return
	end
	local rows = globalRows()
	footer.Text = if rows then "All servers · updates every minute" else "This server · updates every minute"
	rows = rows or serverRows()
	for rank, label in rowLabels do
		local row = (rows :: { Row })[rank]
		label.Text = if row then `{rank}.  {row.Name}  ·  {Format.Money(row.Value)}` else `{rank}.  —`
	end
end

local function onPlayerAdded(player: Player)
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	-- Text, not an IntValue: amounts pass 9.2e18 (IntValue's limit). The player list sorts it as text.
	local points = Instance.new("StringValue")
	points.Name = Format.CurrencyName
	points.Value = "0"
	points.Parent = leaderstats
	leaderstats.Parent = player
	LeaderboardService.UpdatePlayer(player)
end

-- Keeps the player-list value in sync (called on every state change).
function LeaderboardService.UpdatePlayer(player: Player)
	local state = DataService.GetState(player)
	local leaderstats = player:FindFirstChild("leaderstats")
	local points = if leaderstats then leaderstats:FindFirstChild(Format.CurrencyName) else nil
	if state and points and points:IsA("StringValue") then
		local text = Format.Short(state.BonkPoints)
		-- Replicate runs on every change; only touch the value when the text changes.
		if points.Value ~= text then
			points.Value = text
		end
	end
end

function LeaderboardService.Init()
	local ok, result = pcall(function()
		return DataStoreService:GetOrderedDataStore(CONFIG.StoreName)
	end)
	if ok then
		store = result
	end
end

function LeaderboardService.Start()
	buildBoard()
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	DataService.OnReplicated(LeaderboardService.UpdatePlayer)
	task.spawn(function()
		-- First fill once the players' data had time to load.
		task.wait(5)
		while true do
			refreshBoard()
			task.wait(CONFIG.RefreshInterval)
		end
	end)
end

return LeaderboardService
