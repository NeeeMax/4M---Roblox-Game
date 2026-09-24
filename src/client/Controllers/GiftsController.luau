--!strict
-- GIFTS menu: the 7-day login streak (Config/Hub → LoginStreak) and today's playtime gifts (Config/Hub → Playtime).
-- The server tracks both; this shows them and sends ClaimStreak / ClaimPlaytime.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local STREAK = Hub.LoginStreak.Rewards
local GIFTS = Hub.Playtime.Gifts
local SECONDS_PER_DAY = 24 * 60 * 60

local dayFrames: { Frame } = {}
local streakButton: TextButton
local giftRows: { { Button: TextButton, Fill: Frame, Status: TextLabel } } = {}

local GiftsController = {}

local function today(): number
	return Workspace:GetServerTimeNow() // SECONDS_PER_DAY
end

-- True if something can be claimed right now (HudController shows a badge).
function GiftsController.HasClaimable(): boolean
	local state = State.Get()
	if not state then
		return false
	end
	if state.Streak.ClaimedDay ~= state.Streak.Day and state.Streak.Count > 0 then
		return true
	end
	if state.Playtime.Day == today() then
		for index, gift in GIFTS do
			if not state.Playtime.Claimed[index] and state.Playtime.Seconds >= gift.Minutes * 60 then
				return true
			end
		end
	end
	return false
end

local function build()
	local panel = Widgets.Panel("Gifts", "DAILY GIFTS", Vector2.new(680, 560), Color3.fromRGB(255, 110, 150))
	local content = panel.Content

	local streakTitle = Widgets.Label(content, "LOGIN STREAK · come back every day!", 18, Theme.Accent)
	streakTitle.Size = UDim2.new(1, 0, 0, 22)
	local row = Instance.new("Frame")
	row.Position = UDim2.fromOffset(0, 28)
	row.Size = UDim2.new(1, 0, 0, 120)
	row.BackgroundTransparency = 1
	row.Parent = content
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 6)
	layout.Parent = row
	for day, reward in STREAK do
		local frame = Instance.new("Frame")
		frame.Size = UDim2.new(1 / #STREAK, -6, 1, 0)
		frame.BackgroundColor3 = Theme.Card
		frame.Parent = row
		Widgets.Corner(frame, 10)
		Widgets.Stroke(frame, 2)
		local dayLabel = Widgets.Label(frame, `DAY {day}`, 16, Theme.Muted)
		dayLabel.Size = UDim2.new(1, 0, 0, 26)
		dayLabel.TextXAlignment = Enum.TextXAlignment.Center
		local text = Widgets.Label(frame, reward.Text, 14)
		text.Position = UDim2.fromOffset(4, 30)
		text.Size = UDim2.new(1, -8, 1, -36)
		text.TextWrapped = true
		text.TextXAlignment = Enum.TextXAlignment.Center
		table.insert(dayFrames, frame)
	end
	streakButton = Widgets.Button(content, "", Theme.Good, 22)
	streakButton.Position = UDim2.fromOffset(0, 156)
	streakButton.Size = UDim2.new(1, 0, 0, 48)
	streakButton.Activated:Connect(function()
		Net.Get(Net.ClaimStreak):FireServer()
	end)

	local giftTitle = Widgets.Label(content, "PLAYTIME GIFTS · today", 18, Theme.Accent)
	giftTitle.Position = UDim2.fromOffset(0, 218)
	giftTitle.Size = UDim2.new(1, 0, 0, 22)
	for index, gift in GIFTS do
		local frame = Instance.new("Frame")
		frame.Position = UDim2.fromOffset(0, 246 + (index - 1) * 50)
		frame.Size = UDim2.new(1, 0, 0, 44)
		frame.BackgroundColor3 = Theme.Card
		frame.Parent = content
		Widgets.Corner(frame, 10)
		local minutes = Widgets.Label(frame, `{gift.Minutes} min`, 17, Theme.Accent)
		minutes.Position = UDim2.fromOffset(10, 0)
		minutes.Size = UDim2.fromOffset(70, 44)
		local text = Widgets.Label(frame, gift.Reward.Text, 17)
		text.Position = UDim2.fromOffset(84, 0)
		text.Size = UDim2.fromScale(0.4, 1)
		local bar = Instance.new("Frame")
		bar.AnchorPoint = Vector2.new(1, 0.5)
		bar.Position = UDim2.new(1, -140, 0.5, 0)
		bar.Size = UDim2.new(0.28, 0, 0, 16)
		bar.BackgroundColor3 = Theme.Background
		bar.Parent = frame
		Widgets.Corner(bar, 8)
		local fill = Instance.new("Frame")
		fill.Size = UDim2.fromScale(0, 1)
		fill.BackgroundColor3 = Theme.Good
		fill.Parent = bar
		Widgets.Corner(fill, 8)
		local status = Widgets.Label(bar, "", 12)
		status.Size = UDim2.fromScale(1, 1)
		status.TextXAlignment = Enum.TextXAlignment.Center
		status.ZIndex = 2
		local button = Widgets.Button(frame, "", Theme.CardLight, 16)
		button.AnchorPoint = Vector2.new(1, 0.5)
		button.Position = UDim2.new(1, -8, 0.5, 0)
		button.Size = UDim2.fromOffset(120, 34)
		button.Activated:Connect(function()
			Net.Get(Net.ClaimPlaytime):FireServer(index)
		end)
		table.insert(giftRows, { Button = button, Fill = fill, Status = status })
	end
	panel.OnOpen = function()
		GiftsController.Refresh()
	end
end

function GiftsController.Refresh()
	local state = State.Get()
	if not state then
		return
	end
	local streak = state.Streak
	for day, frame in dayFrames do
		local stroke = frame:FindFirstChildOfClass("UIStroke")
		local reached = day <= streak.Count
		frame.BackgroundColor3 = if day == streak.Count
			then Theme.CardLight
			elseif reached then Theme.Card
			else Theme.Background
		if stroke then
			stroke.Color = if day == streak.Count then Theme.Accent else Theme.Stroke
			stroke.Thickness = if day == streak.Count then 3 else 2
		end
	end
	if streak.ClaimedDay == streak.Day then
		streakButton.Text = `Day {streak.Count} claimed ✓ · come back tomorrow for day {streak.Count % #STREAK + 1}`
		streakButton.TextSize = 17
		Widgets.SetButtonColor(streakButton, Theme.Disabled)
	else
		streakButton.Text = `CLAIM DAY {streak.Count}: {STREAK[math.max(streak.Count, 1)].Text}`
		streakButton.TextSize = 20
		Widgets.SetButtonColor(streakButton, Theme.Good)
	end

	local seconds = if state.Playtime.Day == today() then state.Playtime.Seconds else 0
	for index, gift in GIFTS do
		local row = giftRows[index]
		local needed = gift.Minutes * 60
		row.Fill.Size = UDim2.fromScale(math.clamp(seconds / needed, 0, 1), 1)
		local claimed = state.Playtime.Day == today() and state.Playtime.Claimed[index] == true
		if claimed then
			row.Button.Text = "CLAIMED ✓"
			row.Status.Text = "done"
			Widgets.SetButtonColor(row.Button, Theme.Disabled)
		elseif seconds >= needed then
			row.Button.Text = "CLAIM!"
			row.Status.Text = "ready"
			Widgets.SetButtonColor(row.Button, Theme.Good)
		else
			row.Button.Text = Widgets.Duration(needed - seconds)
			row.Status.Text = `{math.floor(seconds / 60)} / {gift.Minutes} min`
			Widgets.SetButtonColor(row.Button, Theme.CardLight)
		end
	end
end

function GiftsController.Init()
	build()
end

function GiftsController.Start()
	State.Changed:Connect(GiftsController.Refresh)
	GiftsController.Refresh()
end

return GiftsController
