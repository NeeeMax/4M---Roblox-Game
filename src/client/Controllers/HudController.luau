--!strict
-- Always-on HUD, kept uncluttered (docs/GAME_DESIGN.md → UI). Top centre: menu button (opens a small list: SHOP,
-- GIFTS, QUESTS, SPIN, INDEX, SETTINGS, ADMIN), clipboard button (MANAGE: the upgrade menu with the Manage pass,
-- else the shop to buy it) and the Bonk Points counter ("324.316 quadrillion"). Below it: running boosts. "!" badges
-- sit on the menu button and its entries when something can be claimed (hidden with Settings → Hints off).
-- Also: the Bonk Rain button, short server messages (Notify), and opening hub menus from their ProximityPrompts.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Icons = require(ReplicatedStorage.Shared.Config.Icons)
local Net = require(ReplicatedStorage.Shared.Net)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local GiftsController = require(script.Parent.GiftsController)
local SpinController = require(script.Parent.SpinController)
local UpgradeController = require(script.Parent.UpgradeController)
local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local BUTTON = 64
local GAP = 8
local MONEY_WIDTH = 470
local ENTRY_HEIGHT = 52

type Entry = {
	Text: string,
	Panel: string,
	Icon: Icons.IconName,
	Color: Color3,
}

-- The menu list, top to bottom. ADMIN is added for admins.
local ENTRIES: { Entry } = {
	{ Text = "SHOP", Panel = "Shop", Icon = "Shop", Color = Color3.fromRGB(60, 200, 90) },
	{ Text = "GIFTS", Panel = "Gifts", Icon = "Gift", Color = Color3.fromRGB(255, 110, 150) },
	{ Text = "QUESTS", Panel = "Quests", Icon = "Quest", Color = Color3.fromRGB(70, 170, 235) },
	{ Text = "SPIN", Panel = "DailySpin", Icon = "Spin", Color = Color3.fromRGB(255, 190, 40) },
	{ Text = "INDEX", Panel = "Index", Icon = "Index", Color = Color3.fromRGB(160, 110, 255) },
	{ Text = "SETTINGS", Panel = "Settings", Icon = "Settings", Color = Color3.fromRGB(150, 150, 160) },
}

local player = Players.LocalPlayer

local pointsLabel: TextLabel
local boostLabel: TextLabel
local toastHolder: Frame
local menuList: Frame
local rainButton: TextButton
local rainLabel: TextLabel
local rainBanner: TextLabel
local menuBadge: TextLabel
local manageBadge: TextLabel
-- Panel name → "!" on its menu entry.
local badges: { [string]: TextLabel } = {}
-- Panel name → wants a "!" (before the Hints setting is applied).
local wanted: { [string]: boolean } = {}
local shownPoints = 0
-- Bumped per update so an older count-up animation stops when a newer one starts.
local countVersion = 0

local HudController = {}

local function hintsOn(): boolean
	local state = State.Get()
	return not state or state.Settings.Hints ~= false
end

-- Applies `wanted` to the badges (entry, menu button, clipboard).
local function showBadges()
	local hints = hintsOn()
	local any = false
	for panel, badge in badges do
		local show = hints and wanted[panel] == true
		badge.Visible = show
		any = any or show
	end
	menuBadge.Visible = any
	manageBadge.Visible = hints and wanted.Upgrades == true
end

local function setMenuOpen(open: boolean)
	menuList.Visible = open
end

local function buildMenu(parent: Instance)
	local entries = table.clone(ENTRIES)
	if Admin.IsAdmin(player.UserId) then
		table.insert(entries, { Text = "ADMIN", Panel = "Admin", Icon = "Settings", Color = Theme.Admin })
	end

	menuList = Instance.new("Frame")
	menuList.Name = "MenuList"
	menuList.Position = UDim2.fromOffset(0, BUTTON + 10)
	menuList.Size = UDim2.fromOffset(236, 16 + #entries * (ENTRY_HEIGHT + 8))
	menuList.BackgroundColor3 = Theme.Panel
	menuList.Visible = false
	menuList.ZIndex = 10
	menuList.Parent = parent
	Widgets.Corner(menuList, 16)
	Widgets.Stroke(menuList, 5, Theme.BorderGreen)
	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 10)
	padding.PaddingLeft = UDim.new(0, 10)
	padding.PaddingRight = UDim.new(0, 10)
	padding.Parent = menuList
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = menuList

	for index, entry in entries do
		local button = Widgets.Button(menuList, entry.Text, entry.Color, 24)
		button.LayoutOrder = index
		button.Size = UDim2.new(1, 0, 0, ENTRY_HEIGHT)
		button.TextXAlignment = Enum.TextXAlignment.Left
		button.ZIndex = 11
		local textPadding = Instance.new("UIPadding")
		textPadding.PaddingLeft = UDim.new(0, 58)
		textPadding.Parent = button
		local icon = Widgets.Icon(button, entry.Icon, 38)
		icon.AnchorPoint = Vector2.new(0, 0.5)
		icon.Position = UDim2.new(0, -50, 0.5, 0)
		icon.ZIndex = 12
		badges[entry.Panel] = Widgets.Badge(button)
		button.Activated:Connect(function()
			setMenuOpen(false)
			if Widgets.HasPanel(entry.Panel) then
				Widgets.Toggle(entry.Panel)
			else
				HudController.Toast(`{entry.Text} is coming soon!`, "Info")
			end
		end)
	end
end

local function build()
	local gui = Widgets.Screen("Hud")

	-- Top centre: [menu] [manage] [ money ].
	local top = Instance.new("Frame")
	top.Name = "TopBar"
	top.AnchorPoint = Vector2.new(0.5, 0)
	top.Position = UDim2.new(0.5, 0, 0, 6)
	top.Size = UDim2.fromOffset(BUTTON * 2 + GAP * 2 + MONEY_WIDTH, BUTTON)
	top.BackgroundTransparency = 1
	top.Parent = gui

	local menuButton = Widgets.IconButton(top, "Menu", Theme.MenuButton, BUTTON)
	menuButton.Name = "Menu"
	menuBadge = Widgets.Badge(menuButton)
	menuButton.Activated:Connect(function()
		setMenuOpen(not menuList.Visible)
	end)

	local manageButton = Widgets.IconButton(top, "Clipboard", Theme.ManageButton, BUTTON)
	manageButton.Name = "Manage"
	manageButton.Position = UDim2.fromOffset(BUTTON + GAP, 0)
	manageBadge = Widgets.Badge(manageButton)
	manageButton.Activated:Connect(function()
		setMenuOpen(false)
		if Widgets.IsOpen("Upgrades") then
			Widgets.CloseAll()
		else
			UpgradeController.OpenManage()
		end
	end)

	local money = Instance.new("Frame")
	money.Name = "Money"
	money.Position = UDim2.fromOffset((BUTTON + GAP) * 2, 0)
	money.Size = UDim2.fromOffset(MONEY_WIDTH, BUTTON)
	money.BackgroundColor3 = Theme.Background
	money.BackgroundTransparency = 0.12
	money.ClipsDescendants = true
	money.Parent = top
	Widgets.Corner(money, 12)
	Widgets.DotPattern(money, Color3.new(0, 0, 0), 22, 0.55)
	local cash = Widgets.Icon(money, "Cash", 44)
	cash.AnchorPoint = Vector2.new(0, 0.5)
	cash.Position = UDim2.new(0, 10, 0.5, 0)
	pointsLabel = Widgets.Label(money, "0", 44, Theme.Money)
	pointsLabel.Name = "Points"
	pointsLabel.Position = UDim2.fromOffset(62, 4)
	pointsLabel.Size = UDim2.new(1, -72, 1, -8)
	pointsLabel.TextStrokeTransparency = 1
	pointsLabel.TextScaled = true
	local maxSize = Instance.new("UITextSizeConstraint")
	maxSize.MaxTextSize = 46
	maxSize.Parent = pointsLabel
	Widgets.Outline(pointsLabel, 3)

	buildMenu(top)

	-- Running boosts, a small pill under the bar.
	boostLabel = Widgets.Label(gui, "", 20, Theme.Accent)
	boostLabel.Name = "Boosts"
	boostLabel.AnchorPoint = Vector2.new(0.5, 0)
	boostLabel.Position = UDim2.new(0.5, 0, 0, BUTTON + 14)
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
	rainBanner.Position = UDim2.new(0.5, 0, 0, BUTTON + 56)
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
	local toast = Widgets.Label(toastHolder, message, 22)
	toast.Size = UDim2.fromOffset(0, 40)
	toast.AutomaticSize = Enum.AutomaticSize.X
	toast.BackgroundTransparency = 0.08
	toast.BackgroundColor3 = Theme.Background
	toast.TextXAlignment = Enum.TextXAlignment.Center
	toast.TextStrokeTransparency = 0.3
	toast.LayoutOrder = toastCount
	Widgets.Corner(toast, 12)
	Widgets.Stroke(toast, 3, color)
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0, 18)
	padding.PaddingRight = UDim.new(0, 18)
	padding.Parent = toast
	task.delay(3, function()
		TweenService:Create(
			toast,
			TweenInfo.new(0.4),
			{ TextTransparency = 1, TextStrokeTransparency = 1, BackgroundTransparency = 1 }
		):Play()
		task.wait(0.4)
		toast:Destroy()
	end)
	-- At most 4 on screen.
	local children = {}
	for _, child in toastHolder:GetChildren() do
		if child:IsA("TextLabel") then
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
	local started = os.clock()
	countVersion += 1
	local version = countVersion
	task.spawn(function()
		while os.clock() - started < 0.35 and version == countVersion do
			local alpha = (os.clock() - started) / 0.35
			shownPoints = start + (target - start) * alpha
			pointsLabel.Text = Format.Abbreviate(shownPoints)
			RunService.RenderStepped:Wait()
		end
		if version == countVersion then
			shownPoints = target
			pointsLabel.Text = Format.Abbreviate(target)
		end
	end)

	-- Something to buy in the upgrade menu (only with the Manage pass: without it the menu doesn't open).
	local canBuy = false
	if state.Passes.Manage then
		for _, id in Upgrades.Order do
			local level = state.UpgradeLevels[id] or 0
			if level < Upgrades.GetMaxLevel(id, state.Passes) and state.BonkPoints >= Upgrades.GetCost(id, level) then
				canBuy = true
			end
		end
	end
	wanted.Upgrades = canBuy

	local claimable = false
	for index, id in state.Quests.Ids do
		for _, def in Hub.Quests.Pool do
			if def.Id == id and not state.Quests.Claimed[index] and (state.Quests.Progress[index] or 0) >= def.Goal then
				claimable = true
			end
		end
	end
	wanted.Quests = claimable
	wanted.Gifts = GiftsController.HasClaimable()
	showBadges()

	rainButton.Visible = state.BonkRains > 0
	rainLabel.Text = `BONK RAIN ×{state.BonkRains}`
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

-- Boost timers and the spin / gift badges tick every second.
local function tick()
	local state = State.Get()
	if not state then
		return
	end
	local now = Workspace:GetServerTimeNow()
	local parts = {}
	local pointsLeft = (state.Boosts.Points or 0) - now
	if pointsLeft > 0 then
		table.insert(parts, `2× POINTS {Widgets.Duration(pointsLeft)}`)
	end
	local fireLeft = (state.Boosts.FireRate or 0) - now
	if fireLeft > 0 then
		table.insert(parts, `2× FIRE RATE {Widgets.Duration(fireLeft)}`)
	end
	boostLabel.Text = table.concat(parts, "   ·   ")
	boostLabel.Visible = #parts > 0
	wanted.DailySpin = SpinController.SpinsLeft() > 0
	wanted.Gifts = GiftsController.HasClaimable()
	showBadges()
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
		setMenuOpen(false)
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
