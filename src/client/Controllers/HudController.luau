--!strict
-- Always-on HUD: Bonk Points, running boosts, the menu buttons on the left (with "!" badges when something can be
-- bought or claimed), short server messages (Notify), and opening hub menus from their ProximityPrompts.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local player = Players.LocalPlayer

local pointsLabel: TextLabel
local boostLabel: TextLabel
local toastHolder: Frame
local badges: { [string]: TextLabel } = {}
local shownPoints = 0
-- Bumped per update so an older count-up animation stops when a newer one starts.
local countVersion = 0

local HudController = {}

local function badge(button: TextButton): TextLabel
	local dot = Widgets.Label(button, "!", 18)
	dot.AnchorPoint = Vector2.new(0.5, 0.5)
	dot.Position = UDim2.new(1, -4, 0, 4)
	dot.Size = UDim2.fromOffset(24, 24)
	dot.BackgroundTransparency = 0
	dot.BackgroundColor3 = Theme.Bad
	dot.TextXAlignment = Enum.TextXAlignment.Center
	dot.ZIndex = 3
	dot.Visible = false
	Widgets.Corner(dot, 12)
	Widgets.Stroke(dot, 2)
	return dot
end

local function sideButton(parent: Instance, text: string, color: Color3, order: number, panel: string): TextButton
	local button = Widgets.Button(parent, text, color, 22)
	button.Size = UDim2.fromOffset(150, 50)
	button.LayoutOrder = order
	button.Activated:Connect(function()
		Widgets.Toggle(panel)
	end)
	badges[panel] = badge(button)
	return button
end

local function build()
	local gui = Widgets.Screen("Hud")

	-- Points, top centre.
	local pointsFrame = Instance.new("Frame")
	pointsFrame.AnchorPoint = Vector2.new(0.5, 0)
	pointsFrame.Position = UDim2.new(0.5, 0, 0, 10)
	pointsFrame.Size = UDim2.fromOffset(340, 52)
	pointsFrame.BackgroundColor3 = Theme.Background
	pointsFrame.BackgroundTransparency = 0.1
	pointsFrame.Parent = gui
	Widgets.Corner(pointsFrame, 14)
	Widgets.Stroke(pointsFrame, 3, Theme.Accent)
	pointsLabel = Widgets.Label(pointsFrame, "0 BONK POINTS", 26, Theme.Accent)
	pointsLabel.Size = UDim2.fromScale(1, 1)
	pointsLabel.TextXAlignment = Enum.TextXAlignment.Center
	pointsLabel.TextStrokeTransparency = 0.5

	boostLabel = Widgets.Label(gui, "", 18, Color3.fromRGB(255, 230, 120))
	boostLabel.AnchorPoint = Vector2.new(0.5, 0)
	boostLabel.Position = UDim2.new(0.5, 0, 0, 66)
	boostLabel.Size = UDim2.fromOffset(500, 22)
	boostLabel.TextXAlignment = Enum.TextXAlignment.Center
	boostLabel.TextStrokeTransparency = 0.3

	-- Menu buttons, left.
	local column = Instance.new("Frame")
	column.AnchorPoint = Vector2.new(0, 0.5)
	column.Position = UDim2.new(0, 14, 0.5, 0)
	column.Size = UDim2.fromOffset(160, 300)
	column.BackgroundTransparency = 1
	column.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 10)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Parent = column
	sideButton(column, "UPGRADES", Color3.fromRGB(255, 150, 30), 1, "Upgrades")
	sideButton(column, "QUESTS", Color3.fromRGB(70, 190, 90), 2, "Quests")
	sideButton(column, "SPIN", Color3.fromRGB(255, 190, 40), 3, "DailySpin")
	if Admin.IsAdmin(player.UserId) then
		sideButton(column, "ADMIN", Theme.Admin, 4, "Admin")
	end

	-- Messages, bottom centre (newest at the bottom).
	toastHolder = Instance.new("Frame")
	toastHolder.AnchorPoint = Vector2.new(0.5, 1)
	toastHolder.Position = UDim2.new(0.5, 0, 1, -110)
	toastHolder.Size = UDim2.fromOffset(520, 200)
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
	local toast = Widgets.Label(toastHolder, message, 20)
	toast.Size = UDim2.fromOffset(500, 36)
	toast.BackgroundTransparency = 0.1
	toast.BackgroundColor3 = Theme.Background
	toast.TextXAlignment = Enum.TextXAlignment.Center
	toast.LayoutOrder = toastCount
	Widgets.Corner(toast, 10)
	Widgets.Stroke(toast, 2, color)
	task.delay(3, function()
		TweenService:Create(toast, TweenInfo.new(0.4), { TextTransparency = 1, BackgroundTransparency = 1 }):Play()
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
			pointsLabel.Text = `{Format.Number(shownPoints)} BONK POINTS`
			RunService.RenderStepped:Wait()
		end
		if version == countVersion then
			shownPoints = target
			pointsLabel.Text = `{Format.Number(target)} BONK POINTS`
		end
	end)

	local canBuy = false
	for _, id in Upgrades.Order do
		local level = state.UpgradeLevels[id] or 0
		if level < Upgrades.Defs[id].MaxLevel and state.BonkPoints >= Upgrades.GetCost(id, level) then
			canBuy = true
		end
	end
	badges.Upgrades.Visible = canBuy

	local claimable = false
	for index, id in state.Quests.Ids do
		for _, def in Hub.Quests.Pool do
			if def.Id == id and not state.Quests.Claimed[index] and (state.Quests.Progress[index] or 0) >= def.Goal then
				claimable = true
			end
		end
	end
	badges.Quests.Visible = claimable
end

-- Boost timers and the spin badge tick every second.
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
	badges.DailySpin.Visible = now >= state.LastSpinAt + Hub.DailySpin.Cooldown
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
