--!strict
-- Jump and run on the hub (Config/Obby): a timer at the top while a run is going (ObbyStarted) and a popup when the
-- player reaches the top (ObbyFinished) with the time, the reward or the best time, and when the next reward comes.
-- The server times the run; the timer here is only for show and stops when the run can no longer count.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local Obby = require(ReplicatedStorage.Shared.Config.Obby)
local World = require(ReplicatedStorage.Shared.Config.World)

local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local ACCENT = Color3.fromRGB(95, 230, 60)
local POPUP_SECONDS = 7

local player = Players.LocalPlayer

local timerFrame: Frame
local timerLabel: TextLabel
local popup: Frame
local popupScale: UIScale
local timeLabel: TextLabel
local rewardLabel: TextLabel
local nextLabel: TextLabel

-- os.clock() when the running timer started; nil while no run is going.
local startedAt: number? = nil
-- Stood above Obby.FallHeight during this run (landing lower again ends it).
local climbed = false

local floorParams = RaycastParams.new()
floorParams.FilterType = Enum.RaycastFilterType.Exclude
floorParams.RespectCanCollide = true
local nextRewardAt = 0
local popupToken = 0

local ObbyController = {}

-- "29:59"
local function clock(seconds: number): string
	local total = math.max(0, math.ceil(seconds))
	return string.format("%d:%02d", total // 60, total % 60)
end

local function outlined(label: TextLabel, thickness: number)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = thickness
	stroke.Color = Theme.Stroke
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label
end

local function centered(
	parent: Instance,
	text: string,
	size: number,
	color: Color3,
	y: number,
	height: number
): TextLabel
	local label = Widgets.Label(parent, text, size, color)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.Size = UDim2.new(1, -24, 0, height)
	label.Position = UDim2.fromOffset(12, y)
	outlined(label, 2.5)
	return label
end

local function build()
	local gui = Widgets.Screen("Obby", 6)

	timerFrame = Instance.new("Frame")
	timerFrame.Name = "Timer"
	timerFrame.AnchorPoint = Vector2.new(0.5, 0)
	timerFrame.Position = UDim2.new(0.5, 0, 0, 96)
	timerFrame.Size = UDim2.fromOffset(230, 58)
	timerFrame.BackgroundColor3 = Theme.Background
	timerFrame.Visible = false
	timerFrame.Parent = gui
	Widgets.Corner(timerFrame, 14)
	Widgets.Stroke(timerFrame, 5, ACCENT)
	timerLabel = Widgets.Label(timerFrame, "0.0", 34, Theme.Text)
	timerLabel.TextXAlignment = Enum.TextXAlignment.Center
	timerLabel.Size = UDim2.fromScale(1, 1)
	outlined(timerLabel, 2.5)
	local caption = Widgets.Label(timerFrame, "OBBY", 18, ACCENT)
	caption.TextXAlignment = Enum.TextXAlignment.Center
	caption.AnchorPoint = Vector2.new(0.5, 0.5)
	caption.Position = UDim2.fromScale(0.5, 0)
	caption.Size = UDim2.fromOffset(80, 22)
	outlined(caption, 2)

	popup = Instance.new("Frame")
	popup.Name = "Finished"
	popup.AnchorPoint = Vector2.new(0.5, 0.5)
	popup.Position = UDim2.fromScale(0.5, 0.32)
	popup.Size = UDim2.fromOffset(440, 222)
	popup.BackgroundColor3 = Theme.Background
	popup.Visible = false
	popup.Parent = gui
	Widgets.Corner(popup, 18)
	Widgets.Stroke(popup, 7, ACCENT)
	popupScale = Instance.new("UIScale")
	popupScale.Parent = popup

	local title = centered(popup, "FINISHED!", 48, ACCENT, 12, 56)
	title.TextStrokeTransparency = 1
	timeLabel = centered(popup, "", 36, Theme.Text, 70, 44)
	rewardLabel = centered(popup, "", 24, Theme.Accent, 120, 32)
	nextLabel = centered(popup, "", 20, Theme.Muted, 160, 28)
	nextLabel.Font = Theme.BodyFont
end

local function stopTimer()
	startedAt = nil
	timerFrame.Visible = false
end

-- Height above the hub ground of the floor the character stands on, nil while in the air (same ray as ObbyService).
local function floorHeight(character: Model, root: BasePart, humanoid: Humanoid): number?
	floorParams.FilterDescendantsInstances = { character }
	local reach = math.max(humanoid.HipHeight + root.Size.Y / 2, 3) + 1.2
	local result = Workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), floorParams)
	return if result then result.Position.Y - World.Hub.Center.Y else nil
end

-- Mirrors the server's rules for dropping a run: too long, walked away from the hub centre, or fell back down to the
-- plaza after climbing (no checkpoints: start over).
local function runStillCounts(elapsed: number): boolean
	if elapsed > Obby.MaxRunTime then
		return false
	end
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not character or not root or not root:IsA("BasePart") or not humanoid then
		return false
	end
	local offset = root.Position - World.Hub.Center
	if Vector3.new(offset.X, 0, offset.Z).Magnitude > Obby.LeaveRadius then
		return false
	end
	local floor = floorHeight(character, root, humanoid)
	if floor then
		if floor > Obby.FallHeight then
			climbed = true
		elseif climbed then
			return false
		end
	end
	return true
end

local function updateNextLabel()
	local left = nextRewardAt - Workspace:GetServerTimeNow()
	nextLabel.Text = if left > 0 then `next reward in {clock(left)}` else "reward ready: climb again!"
end

local function onStarted()
	startedAt = os.clock()
	climbed = false
	timerLabel.Text = "0.0"
	timerFrame.Visible = true
end

local function onFinished(time: unknown, reward: unknown, bestTime: unknown, nextAt: unknown)
	if
		typeof(time) ~= "number"
		or typeof(reward) ~= "number"
		or typeof(bestTime) ~= "number"
		or typeof(nextAt) ~= "number"
	then
		return
	end
	stopTimer()
	nextRewardAt = nextAt
	timeLabel.Text = string.format("%.1f s", time)
	if reward > 0 then
		Widgets.SetMoneyText(rewardLabel, `+{Format.Money(reward)} · 2× dollars {Obby.BoostSeconds // 60} min`)
	elseif bestTime >= time then
		Widgets.SetMoneyText(rewardLabel, "NEW BEST TIME!")
	else
		Widgets.SetMoneyText(rewardLabel, string.format("Best: %.1f s", bestTime))
	end
	updateNextLabel()

	popupToken += 1
	local token = popupToken
	popup.Visible = true
	popupScale.Scale = 0.6
	TweenService:Create(popupScale, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	task.delay(POPUP_SECONDS, function()
		if popupToken == token then
			popup.Visible = false
		end
	end)
end

function ObbyController.Start()
	build()
	Net.Get(Net.ObbyStarted).OnClientEvent:Connect(onStarted)
	Net.Get(Net.ObbyFinished).OnClientEvent:Connect(onFinished)
	player.CharacterAdded:Connect(stopTimer)

	RunService.RenderStepped:Connect(function()
		local started = startedAt
		if started then
			local elapsed = os.clock() - started
			if runStillCounts(elapsed) then
				timerLabel.Text = string.format("%.1f", elapsed)
			else
				stopTimer()
			end
		end
		if popup.Visible then
			updateNextLabel()
		end
	end)
end

return ObbyController
