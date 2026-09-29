--!strict
-- Always-on HUD, kept uncluttered (docs/GAME_DESIGN.md → UI). Top centre: the money pill (drawn cash icon + the
-- plain number "260.8K", counts up, the icon bounces when it rises) with a green income-per-second line under it
-- (only while an estimate is set, HudController.SetIncome). Left side: a 2-column grid of big colourful tiles:
-- MENU (folds the other tiles away), MANAGE (the upgrade menu with the Manage pass, else the shop to buy it), SHOP,
-- GIFTS, QUESTS, SPIN, INDEX, INVITE, SETTINGS, ADMIN. A tile can show a red notification dot
-- (HudController.SetTileDot) and a "Limited!" tag. Below the pill: running boosts.
-- Also: the Bonk Rain button, short server messages (Notify), and opening hub menus from their ProximityPrompts.
-- After the first rebirth a small pill under the menu buttons shows the rebirths and the income multiplier.
-- Friend Boost (SocialController): "FRIENDS +20%" joins the boost pill while Roblox friends are on the server; the
-- INVITE menu entry opens Roblox's invite dialog.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Icons = require(ReplicatedStorage.Shared.Config.Icons)
local Net = require(ReplicatedStorage.Shared.Net)

local SocialController = require(script.Parent.SocialController)
local TycoonController = require(script.Parent.TycoonController)
local UpgradeController = require(script.Parent.UpgradeController)
local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local PILL_WIDTH = 340
local PILL_HEIGHT = 64
local ICON_SIZE = 64
local INCOME_HEIGHT = 20
-- Left tile grid: distance from the screen edge and from the top (clear of Roblox's top bar and the thumbstick).
local GRID_LEFT = 12
local GRID_TOP = 96
local GRID_COLUMNS = 2

type Entry = {
	Text: string,
	Panel: string,
	Icon: Icons.IconName,
	Color: Color3,
	-- Done instead of opening `Panel`: "Invite" opens Roblox's invite dialog.
	Action: ("Invite" | "Collection")?,
	-- Shows the red "Limited!" tag (limited-time features, e.g. the Weekend Bonk Party).
	Limited: boolean?,
}

-- The menu list, top to bottom. ADMIN is added for admins.
local ENTRIES: { Entry } = {
	-- Tycoon only (the tile is hidden while state.Tycoon is disabled): the Shiba collection and equip panel.
	{ Text = "SHIBAS", Panel = "", Icon = "Paw", Color = Color3.fromRGB(255, 120, 60), Action = "Collection" },
	{ Text = "SHOP", Panel = "Shop", Icon = "Shop", Color = Color3.fromRGB(60, 200, 90) },
	{ Text = "GIFTS", Panel = "Gifts", Icon = "Gift", Color = Color3.fromRGB(255, 110, 150) },
	{ Text = "QUESTS", Panel = "Quests", Icon = "Quest", Color = Color3.fromRGB(70, 170, 235) },
	{ Text = "SPIN", Panel = "DailySpin", Icon = "Spin", Color = Color3.fromRGB(255, 190, 40) },
	{ Text = "INDEX", Panel = "Index", Icon = "Index", Color = Color3.fromRGB(160, 110, 255) },
	{
		Text = "INVITE",
		Panel = "",
		Icon = "Paw",
		Color = Color3.fromRGB(255, 150, 60),
		Action = "Invite",
	},
	{ Text = "SETTINGS", Panel = "Settings", Icon = "Settings", Color = Color3.fromRGB(150, 150, 160) },
}

local player = Players.LocalPlayer

local pointsLabel: TextLabel
local moneyIcon: Frame
local incomeLabel: TextLabel
local tileGrid: Frame
local tiles: { [string]: TextButton } = {}
-- Tiles that fold away with the MENU tile (everything but MENU and MANAGE).
local foldTiles: { TextButton } = {}
local tilesOpen = true
local lastPoints = -1
local boostLabel: TextLabel
local rebirthLabel: TextLabel
local toastHolder: Frame
local rainButton: TextButton
local rainLabel: TextLabel
local rainBanner: TextLabel
local shownPoints = 0
-- Bumped per update so an older count-up animation stops when a newer one starts.
local countVersion = 0

local HudController = {}

-- MENU folds the tile grid: only MENU and MANAGE stay while it is closed.
local function setMenuOpen(open: boolean)
	tilesOpen = open
	for _, tile in foldTiles do
		tile.Visible = open
	end
end

local function buildTiles(gui: ScreenGui)
	local entries = table.clone(ENTRIES)
	if Admin.IsAdmin(player.UserId) then
		table.insert(entries, { Text = "ADMIN", Panel = "Admin", Icon = "Settings", Color = Theme.Admin })
	end

	tileGrid = Instance.new("Frame")
	tileGrid.Name = "Tiles"
	tileGrid.Position = UDim2.fromOffset(GRID_LEFT, GRID_TOP)
	tileGrid.Size = UDim2.fromOffset(GRID_COLUMNS * (Theme.TileSize + Theme.TileGap), 0)
	tileGrid.AutomaticSize = Enum.AutomaticSize.Y
	tileGrid.BackgroundTransparency = 1
	tileGrid.Parent = gui
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.fromOffset(Theme.TileSize, Theme.TileSize)
	layout.CellPadding = UDim2.fromOffset(Theme.TileGap, Theme.TileGap)
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.FillDirectionMaxCells = GRID_COLUMNS
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = tileGrid

	local order = 0
	local function addTile(text: string, icon: Icons.IconName, color: Color3, folds: boolean): TextButton
		order += 1
		local tile = Widgets.HudTile(tileGrid, text, icon, color, Theme.TileSize)
		tile.LayoutOrder = order
		tiles[text] = tile
		if folds then
			table.insert(foldTiles, tile)
		end
		return tile
	end

	local menuTile = addTile("MENU", "Menu", Theme.MenuButton, false)
	menuTile.Activated:Connect(function()
		setMenuOpen(not tilesOpen)
	end)

	local manageTile = addTile("MANAGE", "Clipboard", Theme.ManageButton, false)
	manageTile.Activated:Connect(function()
		if Widgets.IsOpen("Upgrades") then
			Widgets.CloseAll()
		else
			UpgradeController.OpenManage()
		end
	end)

	for _, entry in entries do
		local tile = addTile(entry.Text, entry.Icon, entry.Color, true)
		if entry.Limited then
			Widgets.LimitedTag(tile)
		end
		tile.Activated:Connect(function()
			if entry.Action == "Collection" then
				TycoonController.OpenCollection()
			elseif entry.Action == "Invite" then
				task.spawn(function()
					local ok, message = SocialController.PromptInvite()
					if not ok and message then
						HudController.Toast(message, "Info")
					end
				end)
			elseif Widgets.HasPanel(entry.Panel) then
				Widgets.Toggle(entry.Panel)
			else
				HudController.Toast(`{entry.Text} is coming soon!`, "Info")
			end
		end)
	end
end

local function build()
	local gui = Widgets.Screen("Hud")

	-- Top centre: the money pill.
	local top = Instance.new("Frame")
	top.Name = "TopBar"
	top.AnchorPoint = Vector2.new(0.5, 0)
	top.Position = UDim2.new(0.5, 0, 0, 6)
	top.Size = UDim2.fromOffset(PILL_WIDTH, PILL_HEIGHT)
	top.BackgroundTransparency = 1
	top.Parent = gui

	local money = Instance.new("Frame")
	money.Name = "Money"
	money.Size = UDim2.fromScale(1, 1)
	money.BackgroundColor3 = Theme.MoneyPillFill
	money.BackgroundTransparency = 0.25
	money.Parent = top
	Widgets.Corner(money, PILL_HEIGHT // 2)
	Widgets.Stroke(money, 5, Theme.MoneyPillStroke)
	-- The drawn cash icon is the only currency mark; the number next to it is plain.
	moneyIcon = Widgets.MoneyIcon(ICON_SIZE, money)
	moneyIcon.AnchorPoint = Vector2.new(0.5, 0.5)
	moneyIcon.Position = UDim2.new(0, 38, 0.5, 0)
	moneyIcon.ZIndex = 3
	pointsLabel = Widgets.Label(money, "0", 44, Theme.Text)
	pointsLabel.Name = "Points"
	pointsLabel.Font = Theme.TitleFont
	pointsLabel.Position = UDim2.fromOffset(76, 4)
	pointsLabel.Size = UDim2.new(1, -98, 1, -8)
	pointsLabel.TextXAlignment = Enum.TextXAlignment.Center
	pointsLabel.TextStrokeTransparency = 1
	pointsLabel.TextScaled = true
	local maxSize = Instance.new("UITextSizeConstraint")
	maxSize.MaxTextSize = 46
	maxSize.Parent = pointsLabel
	Widgets.Outline(pointsLabel, 3)

	-- Income per second: a small green line under the pill (hidden without an estimate).
	incomeLabel = Widgets.Label(top, "", 18, Theme.Income)
	incomeLabel.Name = "Income"
	incomeLabel.Font = Theme.TitleFont
	incomeLabel.Position = UDim2.fromOffset(0, PILL_HEIGHT + 4)
	incomeLabel.Size = UDim2.fromOffset(PILL_WIDTH, INCOME_HEIGHT)
	incomeLabel.TextXAlignment = Enum.TextXAlignment.Center
	incomeLabel.TextStrokeTransparency = 1
	incomeLabel.Visible = false
	Widgets.Outline(incomeLabel, 2)

	-- Rebirths and their income multiplier: a small pink pill under the menu buttons (only after the first rebirth).
	rebirthLabel = Widgets.Label(top, "", 16, Color3.fromRGB(255, 150, 215))
	rebirthLabel.Name = "Rebirths"
	rebirthLabel.Position = UDim2.fromOffset(0, PILL_HEIGHT + 14)
	rebirthLabel.Size = UDim2.fromOffset(0, 28)
	rebirthLabel.AutomaticSize = Enum.AutomaticSize.X
	rebirthLabel.BackgroundColor3 = Theme.Background
	rebirthLabel.BackgroundTransparency = 0.15
	rebirthLabel.Visible = false
	Widgets.Corner(rebirthLabel, 10)
	local rebirthPadding = Instance.new("UIPadding")
	rebirthPadding.PaddingLeft = UDim.new(0, 12)
	rebirthPadding.PaddingRight = UDim.new(0, 12)
	rebirthPadding.Parent = rebirthLabel

	buildTiles(gui)

	-- Running boosts, a small pill under the bar.
	boostLabel = Widgets.Label(gui, "", 20, Theme.Accent)
	boostLabel.Name = "Boosts"
	boostLabel.AnchorPoint = Vector2.new(0.5, 0)
	boostLabel.Position = UDim2.new(0.5, 0, 0, PILL_HEIGHT + 14)
	boostLabel.Size = UDim2.fromOffset(0, 32)
	boostLabel.AutomaticSize = Enum.AutomaticSize.X
	boostLabel.TextXAlignment = Enum.TextXAlignment.Center
	boostLabel.BackgroundColor3 = Theme.Background
	boostLabel.BackgroundTransparency = 0.15
	boostLabel.Visible = false
	Widgets.Corner(boostLabel, 10)
	local boostPadding = Instance.new("UIPadding")
	boostPadding.PaddingLeft = UDim.new(0, 14)
	boostPadding.PaddingRight = UDim.new(0, 14)
	boostPadding.Parent = boostLabel

	-- Bonk Rain: a big blue button (right side) while the player has some, and a banner while one falls.
	rainButton = Widgets.Button(gui, "", Theme.Info, 24)
	rainButton.Name = "BonkRain"
	rainButton.AnchorPoint = Vector2.new(1, 1)
	rainButton.Position = UDim2.new(1, -20, 1, -150)
	rainButton.Size = UDim2.fromOffset(220, 70)
	rainButton.Visible = false
	rainButton.Activated:Connect(function()
		Net.Get(Net.UseBonkRain):FireServer()
	end)
	local rainIcon = Widgets.Icon(rainButton, "BonkRain", 52)
	rainIcon.AnchorPoint = Vector2.new(0, 0.5)
	rainIcon.Position = UDim2.new(0, 8, 0.5, 0)
	rainLabel = Widgets.Label(rainButton, "", 24)
	rainLabel.Position = UDim2.fromOffset(66, 0)
	rainLabel.Size = UDim2.new(1, -72, 1, 0)
	rainLabel.TextXAlignment = Enum.TextXAlignment.Center
	rainLabel.TextStrokeTransparency = 0.2
	rainLabel.Font = Theme.TitleFont

	rainBanner = Widgets.Title(gui, "", 44, Color3.fromRGB(120, 210, 255))
	rainBanner.AnchorPoint = Vector2.new(0.5, 0)
	rainBanner.Position = UDim2.new(0.5, 0, 0, PILL_HEIGHT + 56)
	rainBanner.Size = UDim2.fromOffset(640, 52)
	rainBanner.Visible = false

	-- Messages, bottom centre above the big round button (newest at the bottom).
	toastHolder = Instance.new("Frame")
	toastHolder.AnchorPoint = Vector2.new(0.5, 1)
	toastHolder.Position = UDim2.new(0.5, 0, 1, -150)
	toastHolder.Size = UDim2.fromOffset(560, 220)
	toastHolder.BackgroundTransparency = 1
	toastHolder.Parent = gui
	local toastLayout = Instance.new("UIListLayout")
	toastLayout.Padding = UDim.new(0, 6)
	toastLayout.VerticalAlignment = Enum.VerticalAlignment.Bottom
	toastLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	toastLayout.SortOrder = Enum.SortOrder.LayoutOrder
	toastLayout.Parent = toastHolder
end

local toastCount = 0
function HudController.Toast(message: string, kind: string)
	toastCount += 1
	local color = if kind == "Good" then Theme.Good elseif kind == "Bad" then Theme.Bad else Theme.Info
	-- A frame sized to its text; server messages carry plain numbers ("+1.2K"), no currency text.
	local toast = Instance.new("Frame")
	toast.Name = "Toast"
	toast.Size = UDim2.fromOffset(0, 40)
	toast.AutomaticSize = Enum.AutomaticSize.X
	toast.BackgroundTransparency = 0.08
	toast.BackgroundColor3 = Theme.Background
	toast.LayoutOrder = toastCount
	toast.Parent = toastHolder
	Widgets.Corner(toast, 12)
	Widgets.Stroke(toast, 3, color)
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, 18)
	padding.PaddingRight = UDim.new(0, 18)
	padding.Parent = toast
	local layout = Instance.new("UIListLayout")
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Parent = toast
	Widgets.MoneyText(toast, message, 22, Theme.Text, { StrokeTransparency = 0.3 })
	task.delay(3, function()
		Widgets.FadeOut(toast, 0.4)
		task.wait(0.4)
		toast:Destroy()
	end)
	-- At most 4 on screen.
	local children = {}
	for _, child in toastHolder:GetChildren() do
		if child:IsA("Frame") then
			table.insert(children, child)
		end
	end
	table.sort(children, function(a, b)
		return a.LayoutOrder < b.LayoutOrder
	end)
	for index = 1, #children - 4 do
		children[index]:Destroy()
	end
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	-- Count up to the new value instead of jumping.
	local target = state.BonkPoints
	local start = shownPoints
	if lastPoints >= 0 and target > lastPoints then
		Widgets.PopMoneyIcon(moneyIcon)
	end
	lastPoints = target
	local started = os.clock()
	countVersion += 1
	local version = countVersion
	task.spawn(function()
		while os.clock() - started < 0.35 and version == countVersion do
			local alpha = (os.clock() - started) / 0.35
			shownPoints = start + (target - start) * alpha
			pointsLabel.Text = Format.Short(shownPoints)
			RunService.RenderStepped:Wait()
		end
		if version == countVersion then
			shownPoints = target
			pointsLabel.Text = Format.Short(target)
		end
	end)

	-- Tycoon: the SHIBAS tile and the income line only exist while the tycoon is on.
	local tycoonOn = state.Tycoon ~= nil and state.Tycoon.Enabled
	local shibasTile = tiles["SHIBAS"]
	if shibasTile then
		shibasTile.Visible = tycoonOn
	end
	HudController.SetIncome(if tycoonOn then TycoonController.GetIncomePerSecond() else nil)

	rainButton.Visible = state.BonkRains > 0
	rainLabel.Text = `BONK RAIN ×{state.BonkRains}`

	rebirthLabel.Visible = state.Rebirths > 0
	rebirthLabel.Text = `REBIRTH {state.Rebirths} · ×{EconomyConfig.RebirthMultiplier(state.Rebirths)} INCOME`
end

local function showRain(seconds: number)
	rainBanner.Visible = true
	local endsAt = os.clock() + seconds
	task.spawn(function()
		while os.clock() < endsAt do
			rainBanner.Text = `BONK RAIN! {math.ceil(endsAt - os.clock())}s`
			task.wait(0.2)
		end
		rainBanner.Visible = false
	end)
end

-- Boost timers tick every second.
local function tick()
	local state = State.Get()
	if not state then
		return
	end
	local now = Workspace:GetServerTimeNow()
	local parts = {}
	local pointsLeft = (state.Boosts.Points or 0) - now
	if pointsLeft > 0 then
		table.insert(parts, `2× DOLLARS {Widgets.Duration(pointsLeft)}`)
	end
	local fireLeft = (state.Boosts.FireRate or 0) - now
	if fireLeft > 0 then
		table.insert(parts, `2× FIRE RATE {Widgets.Duration(fireLeft)}`)
	end
	local magnetLeft = (state.Boosts.Magnet or 0) - now
	if magnetLeft > 0 then
		table.insert(parts, `MAGNET {Widgets.Duration(magnetLeft)}`)
	end
	local _, friendMultiplier = SocialController.GetBoost()
	if friendMultiplier > 1 then
		table.insert(parts, `FRIENDS +{math.round((friendMultiplier - 1) * 100)}%`)
	end
	boostLabel.Text = table.concat(parts, "   ·   ")
	boostLabel.Visible = #parts > 0
end

-- Income per second under the money pill; nil hides the line. The current game has no income estimate in the
-- HUD, so nothing sets it yet (the tycoon controller can call this with TycoonMath.TotalIncome).
function HudController.SetIncome(perSecond: number?)
	if perSecond and perSecond > 0 then
		incomeLabel.Text = `+{Format.Short(perSecond)}/s`
		incomeLabel.Visible = true
	else
		incomeLabel.Visible = false
	end
	boostLabel.Position = UDim2.new(0.5, 0, 0, PILL_HEIGHT + (if incomeLabel.Visible then 14 + INCOME_HEIGHT else 14))
end

-- Red notification dot on a tile ("SHOP", "GIFTS", "QUESTS", "SPIN", "INDEX", "INVITE", "SETTINGS", "MANAGE" …).
function HudController.SetTileDot(name: string, visible: boolean)
	local tile = tiles[name]
	if tile then
		Widgets.SetTileDot(tile, visible)
	end
end

function HudController.Init()
	State.Start()
	build()
end

function HudController.Start()
	State.Changed:Connect(refresh)
	refresh()
	Net.Get(Net.Notify).OnClientEvent:Connect(function(message: string, kind: string)
		HudController.Toast(message, kind)
	end)
	Net.Get(Net.BonkRainStarted).OnClientEvent:Connect(showRain)
	-- Hub stations: each prompt is named after the menu it opens.
	ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt)
		Widgets.Open(prompt.Name)
	end)
	task.spawn(function()
		while true do
			tick()
			task.wait(1)
		end
	end)
end

return HudController
