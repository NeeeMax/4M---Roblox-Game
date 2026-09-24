--!strict
-- Server events (Config/Events): a big banner with the event's name and a countdown at the top of the screen while
-- one runs, a splash in the middle of the screen when it starts, and a small "Next event in mm:ss" line otherwise.
-- The server sends ServerEvent(eventId, time): time = when the event ends, or (eventId "") when the next one starts.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Events = require(ReplicatedStorage.Shared.Config.Events)
local Net = require(ReplicatedStorage.Shared.Net)

local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

-- Below the points counter and boost line of the HUD.
local BANNER_TOP = 92
local SPLASH_SECONDS = 2.5

local currentId = ""
-- Server clock: when the running event ends, or when the next one starts.
local targetTime = 0

local banner: Frame
local bannerStroke: UIStroke
local bannerScale: UIScale
local titleLabel: TextLabel
local descriptionLabel: TextLabel
local timerLabel: TextLabel
local nextLabel: TextLabel
local splash: TextLabel
local splashScale: UIScale

local EventController = {}

-- 83 → "1:23"
local function clock(seconds: number): string
	local total = math.max(0, math.ceil(seconds))
	return string.format("%d:%02d", total // 60, total % 60)
end

local function outlinedLabel(parent: Instance, text: string, size: number, color: Color3): TextLabel
	local label = Widgets.Label(parent, text, size, color)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextStrokeTransparency = 0
	label.TextStrokeColor3 = Theme.Stroke
	return label
end

local function build()
	local gui = Widgets.Screen("Events", 5)

	banner = Instance.new("Frame")
	banner.Name = "Banner"
	banner.AnchorPoint = Vector2.new(0.5, 0)
	banner.Position = UDim2.new(0.5, 0, 0, BANNER_TOP)
	banner.Size = UDim2.fromOffset(470, 76)
	banner.BackgroundColor3 = Theme.Background
	banner.BackgroundTransparency = 0.1
	banner.Visible = false
	banner.Parent = gui
	Widgets.Corner(banner, 14)
	bannerStroke = Instance.new("UIStroke")
	bannerStroke.Thickness = 4
	bannerStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	bannerStroke.Parent = banner
	bannerScale = Instance.new("UIScale")
	bannerScale.Parent = banner

	titleLabel = outlinedLabel(banner, "", 32, Theme.Accent)
	titleLabel.TextXAlignment = Enum.TextXAlignment.Left
	titleLabel.Position = UDim2.fromOffset(18, 4)
	titleLabel.Size = UDim2.new(1, -130, 0, 40)

	descriptionLabel = Widgets.Label(banner, "", 16, Theme.Text)
	descriptionLabel.Font = Theme.BodyFont
	descriptionLabel.Position = UDim2.fromOffset(18, 44)
	descriptionLabel.Size = UDim2.new(1, -130, 0, 24)
	descriptionLabel.TextTruncate = Enum.TextTruncate.AtEnd

	local timerBox = Instance.new("Frame")
	timerBox.AnchorPoint = Vector2.new(1, 0.5)
	timerBox.Position = UDim2.new(1, -12, 0.5, 0)
	timerBox.Size = UDim2.fromOffset(100, 52)
	timerBox.BackgroundColor3 = Theme.Card
	timerBox.Parent = banner
	Widgets.Corner(timerBox, 10)
	Widgets.Stroke(timerBox, 2)
	timerLabel = outlinedLabel(timerBox, "", 30, Theme.Text)
	timerLabel.Size = UDim2.fromScale(1, 1)

	nextLabel = outlinedLabel(gui, "", 16, Theme.Muted)
	nextLabel.AnchorPoint = Vector2.new(0.5, 0)
	nextLabel.Position = UDim2.new(0.5, 0, 0, BANNER_TOP)
	nextLabel.Size = UDim2.fromOffset(300, 20)
	nextLabel.TextStrokeTransparency = 0.3
	nextLabel.Visible = false

	splash = outlinedLabel(gui, "", 64, Theme.Accent)
	splash.AnchorPoint = Vector2.new(0.5, 0.5)
	splash.Position = UDim2.fromScale(0.5, 0.36)
	splash.Size = UDim2.fromOffset(900, 90)
	splash.Visible = false
	splashScale = Instance.new("UIScale")
	splashScale.Parent = splash
end

local function showSplash(def: Events.EventDef)
	splash.Text = `{def.DisplayName}!`
	splash.TextColor3 = def.Color
	splash.TextTransparency = 0
	splash.TextStrokeTransparency = 0
	splash.Visible = true
	splashScale.Scale = 0.3
	TweenService:Create(splashScale, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	local shownText = splash.Text
	task.delay(SPLASH_SECONDS, function()
		if splash.Text ~= shownText then
			return
		end
		local fade = TweenInfo.new(0.4)
		TweenService:Create(splash, fade, { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
		task.delay(0.4, function()
			if splash.Text == shownText then
				splash.Visible = false
			end
		end)
	end)
end

local function onServerEvent(eventId: unknown, time: unknown)
	if typeof(eventId) ~= "string" or typeof(time) ~= "number" then
		return
	end
	local isNew = eventId ~= "" and eventId ~= currentId
	currentId = eventId
	targetTime = time
	local def = Events.Defs[eventId]
	banner.Visible = def ~= nil
	nextLabel.Visible = def == nil
	if not def then
		return
	end
	titleLabel.Text = def.DisplayName
	titleLabel.TextColor3 = def.Color
	descriptionLabel.Text = def.Description
	bannerStroke.Color = def.Color
	if isNew then
		bannerScale.Scale = 0.6
		TweenService:Create(bannerScale, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		showSplash(def)
	end
end

local function tick()
	local left = targetTime - Workspace:GetServerTimeNow()
	if banner.Visible then
		timerLabel.Text = clock(left)
		-- Hurry: the last 10 seconds turn red.
		timerLabel.TextColor3 = if left <= 10 then Theme.Bad else Theme.Text
	elseif nextLabel.Visible then
		nextLabel.Text = if left > 0 then `Next event in {clock(left)}` else "Next event starting…"
	end
end

function EventController.Init()
	build()
end

function EventController.Start()
	Net.Get(Net.ServerEvent).OnClientEvent:Connect(onServerEvent)
	task.spawn(function()
		while true do
			tick()
			task.wait(0.25)
		end
	end)
end

return EventController
