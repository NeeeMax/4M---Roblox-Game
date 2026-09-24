--!strict
-- HUD (Bonk Points + menu button) and the upgrade menu. Built in code for the prototype so nothing has to be
-- set up in Studio; can move to a Studio-built layout later. Shows only what the server sent (StateChanged);
-- every purchase is validated on the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local COLOR_PANEL = Color3.fromRGB(30, 30, 40)
local COLOR_ROW = Color3.fromRGB(45, 45, 60)
local COLOR_TEXT = Color3.fromRGB(255, 255, 255)
local COLOR_MUTED = Color3.fromRGB(170, 170, 190)
local COLOR_BUY = Color3.fromRGB(60, 180, 90)
local COLOR_DISABLED = Color3.fromRGB(80, 80, 90)
local COLOR_ACCENT = Color3.fromRGB(255, 170, 0)
local FONT = Enum.Font.FredokaOne
local ROW_HEIGHT = 76

type Row = {
	Detail: TextLabel,
	Button: TextButton,
	CanBuy: boolean,
}

local player = Players.LocalPlayer

local points = 0
local levels: { [string]: number } = {}
local activeShooters = 1

local rows: { [string]: Row } = {}
local pointsLabel: TextLabel
local menu: Frame
local shooterCountLabel: TextLabel

local UIController = {}

local function round(instance: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = instance
end

local function newLabel(parent: Instance, text: string, textSize: number, color: Color3): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Font = FONT
	label.Text = text
	label.TextSize = textSize
	label.TextColor3 = color
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Parent = parent
	return label
end

local function newButton(parent: Instance, text: string, color: Color3): TextButton
	local button = Instance.new("TextButton")
	button.BackgroundColor3 = color
	button.Font = FONT
	button.Text = text
	button.TextSize = 22
	button.TextColor3 = COLOR_TEXT
	button.Parent = parent
	round(button, 8)
	return button
end

local function formatValue(def: Upgrades.UpgradeDef, value: number): string
	if def.Format == "Multiplier" then
		return string.format("×%.2f", value)
	elseif def.Format == "Seconds" then
		return string.format("%.2f s", value)
	end
	return tostring(math.floor(value + 0.5))
end

local function ownedShooters(): number
	return Upgrades.GetValue("Shooters", levels.Shooters or 0)
end

local function refresh()
	pointsLabel.Text = `{Format.Number(points)} BONK POINTS`

	for id, row in rows do
		local def = Upgrades.Defs[id]
		local level = levels[id] or 0
		local current = Upgrades.GetValue(def.Id, level)
		if level >= def.MaxLevel then
			row.Detail.Text = `Lv {level}/{def.MaxLevel}  ·  {formatValue(def, current)}`
			row.Button.Text = "MAX"
			row.CanBuy = false
		else
			local nextValue = Upgrades.GetValue(def.Id, level + 1)
			local cost = Upgrades.GetCost(def.Id, level)
			row.Detail.Text =
				`Lv {level}/{def.MaxLevel}  ·  {formatValue(def, current)} → {formatValue(def, nextValue)}`
			row.Button.Text = Format.Number(cost)
			row.CanBuy = points >= cost
		end
		row.Button.BackgroundColor3 = if row.CanBuy then COLOR_BUY else COLOR_DISABLED
		row.Button.AutoButtonColor = row.CanBuy
	end

	shooterCountLabel.Text = `{activeShooters} / {ownedShooters()}`
end

local function buildUpgradeRow(parent: Instance, id: string, order: number)
	local def = Upgrades.Defs[id]
	local requestPurchase = Net.Get(Net.RequestPurchase)

	local frame = Instance.new("Frame")
	frame.Name = id
	frame.LayoutOrder = order
	frame.Size = UDim2.new(1, 0, 0, ROW_HEIGHT)
	frame.BackgroundColor3 = COLOR_ROW
	frame.Parent = parent
	round(frame, 10)

	local name = newLabel(frame, def.DisplayName, 22, COLOR_TEXT)
	name.Position = UDim2.fromOffset(12, 6)
	name.Size = UDim2.new(1, -140, 0, 24)

	local detail = newLabel(frame, "", 16, COLOR_ACCENT)
	detail.Position = UDim2.fromOffset(12, 30)
	detail.Size = UDim2.new(1, -140, 0, 18)

	local description = newLabel(frame, def.Description, 13, COLOR_MUTED)
	description.Position = UDim2.fromOffset(12, 50)
	description.Size = UDim2.new(1, -140, 0, 18)
	description.TextTruncate = Enum.TextTruncate.AtEnd

	local button = newButton(frame, "", COLOR_DISABLED)
	button.AnchorPoint = Vector2.new(1, 0.5)
	button.Position = UDim2.new(1, -10, 0.5, 0)
	button.Size = UDim2.fromOffset(116, 46)

	local row: Row = { Detail = detail, Button = button, CanBuy = false }
	rows[id] = row

	button.Activated:Connect(function()
		if row.CanBuy then
			requestPurchase:FireServer(id)
		end
	end)
end

local function buildShooterRow(parent: Instance, order: number)
	local setActiveShooters = Net.Get(Net.SetActiveShooters)

	local frame = Instance.new("Frame")
	frame.Name = "ActiveShooters"
	frame.LayoutOrder = order
	frame.Size = UDim2.new(1, 0, 0, 56)
	frame.BackgroundColor3 = COLOR_ROW
	frame.Parent = parent
	round(frame, 10)

	local label = newLabel(frame, "Active shooters", 20, COLOR_TEXT)
	label.Position = UDim2.fromOffset(12, 0)
	label.Size = UDim2.new(1, -180, 1, 0)

	local minus = newButton(frame, "−", COLOR_DISABLED)
	minus.AnchorPoint = Vector2.new(1, 0.5)
	minus.Position = UDim2.new(1, -126, 0.5, 0)
	minus.Size = UDim2.fromOffset(40, 40)

	shooterCountLabel = newLabel(frame, "", 20, COLOR_ACCENT)
	shooterCountLabel.AnchorPoint = Vector2.new(1, 0.5)
	shooterCountLabel.Position = UDim2.new(1, -56, 0.5, 0)
	shooterCountLabel.Size = UDim2.fromOffset(66, 40)
	shooterCountLabel.TextXAlignment = Enum.TextXAlignment.Center

	local plus = newButton(frame, "+", COLOR_DISABLED)
	plus.AnchorPoint = Vector2.new(1, 0.5)
	plus.Position = UDim2.new(1, -10, 0.5, 0)
	plus.Size = UDim2.fromOffset(40, 40)

	minus.Activated:Connect(function()
		if activeShooters > 1 then
			setActiveShooters:FireServer(activeShooters - 1)
		end
	end)
	plus.Activated:Connect(function()
		if activeShooters < ownedShooters() then
			setActiveShooters:FireServer(activeShooters + 1)
		end
	end)
end

function UIController.Init()
	local gui = Instance.new("ScreenGui")
	gui.Name = "BonkUI"
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- HUD: points at the top, menu button on the left.
	local hud = Instance.new("Frame")
	hud.AnchorPoint = Vector2.new(0.5, 0)
	hud.Position = UDim2.new(0.5, 0, 0, 10)
	hud.Size = UDim2.fromOffset(340, 54)
	hud.BackgroundColor3 = COLOR_PANEL
	hud.BackgroundTransparency = 0.15
	hud.Parent = gui
	round(hud, 12)

	pointsLabel = newLabel(hud, "loading…", 28, COLOR_ACCENT)
	pointsLabel.Size = UDim2.fromScale(1, 1)
	pointsLabel.TextXAlignment = Enum.TextXAlignment.Center

	local openButton = newButton(gui, "UPGRADES", COLOR_ACCENT)
	openButton.AnchorPoint = Vector2.new(0, 0.5)
	openButton.Position = UDim2.new(0, 16, 0.5, 0)
	openButton.Size = UDim2.fromOffset(150, 54)
	openButton.TextSize = 24

	-- Upgrade menu.
	menu = Instance.new("Frame")
	menu.Name = "UpgradeMenu"
	menu.Visible = false
	menu.AnchorPoint = Vector2.new(0.5, 0.5)
	menu.Position = UDim2.fromScale(0.5, 0.5)
	menu.Size = UDim2.fromScale(0.92, 0.8)
	menu.BackgroundColor3 = COLOR_PANEL
	menu.Parent = gui
	round(menu, 14)

	local sizeLimit = Instance.new("UISizeConstraint")
	sizeLimit.MaxSize = Vector2.new(520, 540)
	sizeLimit.Parent = menu

	local title = newLabel(menu, "UPGRADES", 30, COLOR_ACCENT)
	title.Position = UDim2.fromOffset(16, 8)
	title.Size = UDim2.new(1, -80, 0, 40)

	local closeButton = newButton(menu, "X", Color3.fromRGB(200, 60, 60))
	closeButton.AnchorPoint = Vector2.new(1, 0)
	closeButton.Position = UDim2.new(1, -10, 0, 10)
	closeButton.Size = UDim2.fromOffset(40, 40)

	local list = Instance.new("ScrollingFrame")
	list.Position = UDim2.fromOffset(12, 58)
	list.Size = UDim2.new(1, -24, 1, -70)
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 6
	list.CanvasSize = UDim2.new()
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.Parent = menu

	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list

	for index, id in Upgrades.Order do
		buildUpgradeRow(list, id, index)
	end
	buildShooterRow(list, #Upgrades.Order + 1)

	openButton.Activated:Connect(function()
		menu.Visible = not menu.Visible
	end)
	closeButton.Activated:Connect(function()
		menu.Visible = false
	end)

	refresh()
	pointsLabel.Text = "loading…"
	gui.Parent = player:WaitForChild("PlayerGui")
end

function UIController.Start()
	Net.Get(Net.StateChanged).OnClientEvent
		:Connect(function(newPoints: number, newLevels: { [string]: number }, newActiveShooters: number)
			points = newPoints
			levels = newLevels
			activeShooters = newActiveShooters
			refresh()
		end)
end

return UIController
