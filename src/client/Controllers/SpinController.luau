--!strict
-- The daily wheel menu (Config/Hub → DailySpin). The server picks the prize (SpinResult); this spins the wheel so
-- that segment ends under the pointer, then shows what you won.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local CONFIG = Hub.DailySpin
local WHEEL_SIZE = 330
local SPOKE_WIDTH = 58
-- From just outside the centre cap to just inside the rim.
local SPOKE_LENGTH = WHEEL_SIZE / 2 - 10 - 34
local SPIN_TIME = 4

local wheel: Frame
-- One card per segment, laid out around the wheel by layout(); `angle` is the wheel's current rotation in degrees.
local spokes: { Frame } = {}
local angle = Instance.new("NumberValue")
local spinButton: TextButton
local resultLabel: TextLabel
local spinning = false
-- True between asking the server and getting its answer.
local waiting = false

local SpinController = {}

local function build()
	local panel = Widgets.Panel("DailySpin", "DAILY SPIN", Vector2.new(460, 560), Color3.fromRGB(255, 190, 40))
	local content = panel.Content

	wheel = Instance.new("Frame")
	wheel.AnchorPoint = Vector2.new(0.5, 0)
	wheel.Position = UDim2.new(0.5, 0, 0, 20)
	wheel.Size = UDim2.fromOffset(WHEEL_SIZE, WHEEL_SIZE)
	wheel.BackgroundColor3 = Theme.Background
	wheel.Parent = content
	Widgets.Corner(wheel, WHEEL_SIZE // 2)
	Widgets.Stroke(wheel, 5, Theme.Accent)

	for _, segment in CONFIG.Segments do
		local spoke = Instance.new("Frame")
		spoke.AnchorPoint = Vector2.new(0.5, 0.5)
		spoke.Size = UDim2.fromOffset(SPOKE_WIDTH, SPOKE_LENGTH)
		spoke.BackgroundColor3 = segment.Color
		spoke.Parent = wheel
		table.insert(spokes, spoke)
		Widgets.Corner(spoke, 10)
		Widgets.Stroke(spoke, 2)
		local text = Widgets.Label(spoke, segment.Text, 14)
		text.Size = UDim2.new(1, -6, 1, -10)
		text.Position = UDim2.fromOffset(3, 5)
		text.TextWrapped = true
		text.TextScaled = true
		text.TextXAlignment = Enum.TextXAlignment.Center
		text.TextYAlignment = Enum.TextYAlignment.Top
		text.TextStrokeTransparency = 0.3
	end
	local hubCap = Instance.new("Frame")
	hubCap.AnchorPoint = Vector2.new(0.5, 0.5)
	hubCap.Position = UDim2.fromScale(0.5, 0.5)
	hubCap.Size = UDim2.fromOffset(56, 56)
	hubCap.BackgroundColor3 = Theme.Accent
	hubCap.Parent = wheel
	Widgets.Corner(hubCap, 28)
	Widgets.Stroke(hubCap, 3)

	-- Pointer above the wheel.
	local pointer = Widgets.Label(content, "▼", 44, Theme.Bad)
	pointer.AnchorPoint = Vector2.new(0.5, 0)
	pointer.Position = UDim2.new(0.5, 0, 0, -12)
	pointer.Size = UDim2.fromOffset(50, 44)
	pointer.TextXAlignment = Enum.TextXAlignment.Center
	pointer.TextStrokeTransparency = 0
	pointer.ZIndex = 5

	resultLabel = Widgets.Label(content, "", 24, Theme.Accent)
	resultLabel.AnchorPoint = Vector2.new(0.5, 0)
	resultLabel.Position = UDim2.new(0.5, 0, 0, WHEEL_SIZE + 30)
	resultLabel.Size = UDim2.new(1, 0, 0, 30)
	resultLabel.TextXAlignment = Enum.TextXAlignment.Center
	resultLabel.TextStrokeTransparency = 0.4

	spinButton = Widgets.Button(content, "SPIN!", Theme.Good, 28)
	spinButton.AnchorPoint = Vector2.new(0.5, 1)
	spinButton.Position = UDim2.new(0.5, 0, 1, -4)
	spinButton.Size = UDim2.fromOffset(260, 58)
	spinButton.Activated:Connect(function()
		local state = State.Get()
		if spinning or not state then
			return
		end
		if Workspace:GetServerTimeNow() < state.LastSpinAt + CONFIG.Cooldown then
			return
		end
		spinning = true
		waiting = true
		resultLabel.Text = ""
		Net.Get(Net.RequestSpin):FireServer()
		-- If the server refuses (it sends a message instead), stop waiting.
		task.delay(3, function()
			if waiting then
				waiting = false
				spinning = false
			end
		end)
	end)
end

-- Places every card at its angle around the centre (0° = under the pointer at the top, clockwise).
local function layout()
	local radius = WHEEL_SIZE / 2
	local distance = radius - 10 - SPOKE_LENGTH / 2
	for index, spoke in spokes do
		local degrees = angle.Value + (index - 1) * 360 / #spokes
		local radians = math.rad(degrees)
		spoke.Position = UDim2.fromOffset(radius + math.sin(radians) * distance, radius - math.cos(radians) * distance)
		spoke.Rotation = degrees
	end
end

local function spinTo(index: number, text: string)
	local count = #CONFIG.Segments
	angle.Value %= 360
	-- Card `index` sits at (index - 1) * step; turn the wheel back by that to put it under the pointer.
	local target = 360 * 6 - (index - 1) * 360 / count
	local tween = TweenService:Create(
		angle,
		TweenInfo.new(SPIN_TIME, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Value = target }
	)
	tween:Play()
	tween.Completed:Wait()
	resultLabel.Text = `You won: {text}!`
	spinning = false
end

-- Button text: "SPIN!" or the time until the next free spin.
local function tick()
	local state = State.Get()
	if not state or spinning then
		return
	end
	local left = state.LastSpinAt + CONFIG.Cooldown - Workspace:GetServerTimeNow()
	if left > 0 then
		spinButton.Text = `Next spin in {Widgets.Duration(left)}`
		spinButton.TextSize = 20
		Widgets.SetButtonColor(spinButton, Theme.Disabled)
	else
		spinButton.Text = "SPIN!"
		spinButton.TextSize = 28
		Widgets.SetButtonColor(spinButton, Theme.Good)
	end
end

function SpinController.Init()
	build()
	angle.Changed:Connect(layout)
	layout()
end

function SpinController.Start()
	Net.Get(Net.SpinResult).OnClientEvent:Connect(function(index: number, text: string)
		waiting = false
		spinning = true
		task.spawn(spinTo, index, text)
	end)
	task.spawn(function()
		while true do
			tick()
			task.wait(0.5)
		end
	end)
end

return SpinController
