--!strict
-- The daily wheel menu (Config/Hub → DailySpin): a real pie-chart wheel (segment size = its chance) with the odds
-- listed next to it. The server picks the prize (SpinResult); this spins the wheel so that segment ends under the
-- pointer, then shows what you won.
-- The pie is drawn from thin wedges (one per 2°) inside a CanvasGroup, which rotates as one picture.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local CONFIG = Hub.DailySpin
local WHEEL_SIZE = 320
local STEP_DEGREES = 2
local SPIN_TIME = 4.5
local SECONDS_PER_DAY = 24 * 60 * 60

local wheel: CanvasGroup
local spinButton: TextButton
local resultLabel: TextLabel
local spinsLabel: TextLabel
local spinning = false
-- True between asking the server and getting its answer.
local waiting = false
-- Where each segment's middle sits on the wheel (degrees clockwise from the top).
local segmentCenters: { number } = {}

local SpinController = {}

local function totalWeight(): number
	local total = 0
	for _, segment in CONFIG.Segments do
		total += segment.Weight
	end
	return total
end

local function spinsPerDay(): number
	local state = State.Get()
	return if state and state.Passes.VIP then Shop.Pass.VIPDailySpins else CONFIG.FreeSpins
end

-- Free spins left today (HudController shows a badge while there are any).
function SpinController.SpinsLeft(): number
	local state = State.Get()
	if not state then
		return 0
	end
	local today = Workspace:GetServerTimeNow() // SECONDS_PER_DAY
	local used = if state.SpinDay == today then state.SpinsUsed else 0
	return math.max(0, spinsPerDay() - used)
end

-- Wedge strips from the centre to the rim; together they form the pie.
local function drawPie()
	local radius = WHEEL_SIZE / 2
	local total = totalWeight()
	local stripWidth = math.ceil(2 * math.pi * radius * STEP_DEGREES / 360) + 2
	local start = 0
	for index, segment in CONFIG.Segments do
		local size = segment.Weight / total * 360
		segmentCenters[index] = start + size / 2
		local degrees = start
		while degrees < start + size do
			local middle = math.min(degrees + STEP_DEGREES / 2, start + size - 0.01)
			local radians = math.rad(middle)
			local strip = Instance.new("Frame")
			strip.AnchorPoint = Vector2.new(0.5, 0.5)
			strip.Size = UDim2.fromOffset(stripWidth, radius)
			strip.Position =
				UDim2.fromOffset(radius + math.sin(radians) * radius / 2, radius - math.cos(radians) * radius / 2)
			strip.Rotation = middle
			strip.BorderSizePixel = 0
			strip.BackgroundColor3 = segment.Color
			strip.Parent = wheel
			degrees += STEP_DEGREES
		end
		-- Thin divider line at the segment's start.
		local startRadians = math.rad(start)
		local divider = Instance.new("Frame")
		divider.AnchorPoint = Vector2.new(0.5, 0.5)
		divider.Size = UDim2.fromOffset(2, radius)
		divider.Position =
			UDim2.fromOffset(radius + math.sin(startRadians) * radius / 2, radius - math.cos(startRadians) * radius / 2)
		divider.Rotation = start
		divider.BorderSizePixel = 0
		divider.BackgroundColor3 = Theme.Stroke
		divider.ZIndex = 2
		divider.Parent = wheel
		-- Label along the segment's middle, reading outward.
		local centerRadians = math.rad(segmentCenters[index])
		local label = Widgets.Label(wheel, segment.Text, 15)
		label.AnchorPoint = Vector2.new(0.5, 0.5)
		label.Size = UDim2.fromOffset(radius * 0.62, 22)
		label.Position = UDim2.fromOffset(
			radius + math.sin(centerRadians) * radius * 0.6,
			radius - math.cos(centerRadians) * radius * 0.6
		)
		label.Rotation = segmentCenters[index] - 90
		label.TextXAlignment = Enum.TextXAlignment.Center
		label.TextScaled = true
		label.ZIndex = 3
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = 1.5
		stroke.Color = Theme.Stroke
		stroke.Parent = label
		start += size
	end
end

local function build()
	local panel = Widgets.Panel("DailySpin", "DAILY SPIN", Vector2.new(640, 540), Color3.fromRGB(255, 190, 40))
	local content = panel.Content

	-- Rim behind the wheel.
	local rim = Instance.new("Frame")
	rim.Position = UDim2.fromOffset(4, 26)
	rim.Size = UDim2.fromOffset(WHEEL_SIZE + 16, WHEEL_SIZE + 16)
	rim.BackgroundColor3 = Theme.Accent
	rim.Parent = content
	Widgets.Corner(rim, (WHEEL_SIZE + 16) // 2)
	Widgets.Stroke(rim, 4)

	wheel = Instance.new("CanvasGroup")
	wheel.AnchorPoint = Vector2.new(0.5, 0.5)
	wheel.Position = UDim2.fromScale(0.5, 0.5)
	wheel.Size = UDim2.fromOffset(WHEEL_SIZE, WHEEL_SIZE)
	wheel.BackgroundColor3 = Theme.Background
	wheel.Parent = rim
	Widgets.Corner(wheel, WHEEL_SIZE // 2)
	drawPie()

	local cap = Instance.new("Frame")
	cap.AnchorPoint = Vector2.new(0.5, 0.5)
	cap.Position = UDim2.fromScale(0.5, 0.5)
	cap.Size = UDim2.fromOffset(54, 54)
	cap.BackgroundColor3 = Theme.Accent
	cap.ZIndex = 5
	cap.Parent = rim
	Widgets.Corner(cap, 27)
	Widgets.Stroke(cap, 3)

	local pointer = Widgets.Label(content, "▼", 46, Theme.Bad)
	pointer.AnchorPoint = Vector2.new(0.5, 0)
	pointer.Position = UDim2.fromOffset(12 + WHEEL_SIZE / 2, -6)
	pointer.Size = UDim2.fromOffset(50, 44)
	pointer.TextXAlignment = Enum.TextXAlignment.Center
	pointer.ZIndex = 6
	local pointerStroke = Instance.new("UIStroke")
	pointerStroke.Thickness = 2
	pointerStroke.Parent = pointer

	-- Right column: odds, spins left, result, button.
	local side = Instance.new("Frame")
	side.AnchorPoint = Vector2.new(1, 0)
	side.Position = UDim2.fromScale(1, 0)
	side.Size = UDim2.new(1, -(WHEEL_SIZE + 36), 1, 0)
	side.BackgroundColor3 = Theme.Card
	side.Parent = content
	Widgets.Corner(side, 12)
	local oddsTitle = Widgets.Label(side, "CHANCES", 18, Theme.Accent)
	oddsTitle.Position = UDim2.fromOffset(12, 6)
	oddsTitle.Size = UDim2.new(1, -24, 0, 24)
	local total = totalWeight()
	for index, segment in CONFIG.Segments do
		local row = Widgets.Label(side, segment.Text, 15)
		row.Position = UDim2.fromOffset(34, 8 + index * 24)
		row.Size = UDim2.new(1, -90, 0, 22)
		local dot = Instance.new("Frame")
		dot.Position = UDim2.fromOffset(12, 12 + index * 24)
		dot.Size = UDim2.fromOffset(14, 14)
		dot.BackgroundColor3 = segment.Color
		dot.Parent = side
		Widgets.Corner(dot, 7)
		local chance = Widgets.Label(side, string.format("%.0f%%", segment.Weight / total * 100), 15, Theme.Muted)
		chance.AnchorPoint = Vector2.new(1, 0)
		chance.Position = UDim2.new(1, -12, 0, 8 + index * 24)
		chance.Size = UDim2.fromOffset(50, 22)
		chance.TextXAlignment = Enum.TextXAlignment.Right
	end

	spinsLabel = Widgets.Label(side, "", 16, Theme.Text)
	spinsLabel.Position = UDim2.new(0, 12, 1, -150)
	spinsLabel.Size = UDim2.new(1, -24, 0, 22)
	spinsLabel.TextXAlignment = Enum.TextXAlignment.Center

	resultLabel = Widgets.Label(side, "", 18, Theme.Accent)
	resultLabel.Position = UDim2.new(0, 8, 1, -124)
	resultLabel.Size = UDim2.new(1, -16, 0, 50)
	resultLabel.TextWrapped = true
	resultLabel.TextXAlignment = Enum.TextXAlignment.Center

	spinButton = Widgets.Button(side, "SPIN!", Theme.Good, 26)
	spinButton.AnchorPoint = Vector2.new(0.5, 1)
	spinButton.Position = UDim2.new(0.5, 0, 1, -10)
	spinButton.Size = UDim2.new(1, -24, 0, 56)
	spinButton.Activated:Connect(function()
		if spinning or SpinController.SpinsLeft() <= 0 then
			return
		end
		spinning = true
		waiting = true
		Widgets.SetMoneyText(resultLabel, "")
		Net.Get(Net.RequestSpin):FireServer()
		task.delay(3, function()
			if waiting then
				waiting = false
				spinning = false
			end
		end)
	end)
end

local function spinTo(index: number, text: string)
	wheel.Rotation %= 360
	-- Turn the wheel back by the segment's angle (plus a random spot inside it) to put it under the pointer.
	local halfWidth = CONFIG.Segments[index].Weight / totalWeight() * 180 * 0.7
	local target = 360 * 6 - segmentCenters[index] + (math.random() * 2 - 1) * halfWidth
	local tween = TweenService:Create(
		wheel,
		TweenInfo.new(SPIN_TIME, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Rotation = target }
	)
	tween:Play()
	tween.Completed:Wait()
	local segment = CONFIG.Segments[index]
	resultLabel.TextColor3 = if segment.Kind == "Nothing" then Theme.Muted else Theme.Accent
	-- "+B$ 1,234" (from the server) shows the Bonk Dollars symbol.
	Widgets.SetMoneyText(
		resultLabel,
		if segment.Kind == "Nothing" then "Nothing this time… try again tomorrow!" else `You won {text}!`
	)
	spinning = false
end

local function tick()
	if spinning then
		return
	end
	local left = SpinController.SpinsLeft()
	spinsLabel.Text = `Spins left today: {left}/{spinsPerDay()}`
	if left > 0 then
		spinButton.Text = "SPIN!"
		spinButton.TextSize = 26
		Widgets.SetButtonColor(spinButton, Theme.Good)
	else
		local now = Workspace:GetServerTimeNow()
		local nextDay = (now // SECONDS_PER_DAY + 1) * SECONDS_PER_DAY
		spinButton.Text = `Next in {Widgets.Duration(nextDay - now)}`
		spinButton.TextSize = 18
		Widgets.SetButtonColor(spinButton, Theme.Disabled)
	end
end

function SpinController.Init()
	build()
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
