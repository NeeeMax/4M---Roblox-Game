--!strict
-- Daily quests menu (Config/Hub → Quests): today's quests with a progress bar each and a CLAIM button once done.
-- The server tracks progress and pays the reward (ClaimQuest).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local SECONDS_PER_DAY = 24 * 60 * 60

type Row = {
	Title: TextLabel,
	Progress: TextLabel,
	Fill: Frame,
	Button: TextButton,
}

local rows: { Row } = {}
local resetLabel: TextLabel

local QuestController = {}

local function findDef(id: string): Hub.QuestDef?
	for _, def in Hub.Quests.Pool do
		if def.Id == id then
			return def
		end
	end
	return nil
end

local function build()
	local panel = Widgets.Panel("Quests", "DAILY QUESTS", Vector2.new(560, 470), Color3.fromRGB(70, 190, 90))
	local content = panel.Content

	resetLabel = Widgets.Label(content, "", 16, Theme.Muted)
	resetLabel.Size = UDim2.new(1, 0, 0, 22)

	for index = 1, Hub.Quests.PerDay do
		local frame = Instance.new("Frame")
		frame.Position = UDim2.fromOffset(0, 30 + (index - 1) * 116)
		frame.Size = UDim2.new(1, 0, 0, 106)
		frame.BackgroundColor3 = Theme.Card
		frame.Parent = content
		Widgets.Corner(frame, 12)
		Widgets.Stroke(frame, 2)

		local title = Widgets.Label(frame, "", 22)
		title.Position = UDim2.fromOffset(14, 8)
		title.Size = UDim2.new(1, -170, 0, 30)

		local bar = Instance.new("Frame")
		bar.Position = UDim2.fromOffset(14, 50)
		bar.Size = UDim2.new(1, -170, 0, 22)
		bar.BackgroundColor3 = Theme.Background
		bar.Parent = frame
		Widgets.Corner(bar, 11)
		local fill = Instance.new("Frame")
		fill.Size = UDim2.fromScale(0, 1)
		fill.BackgroundColor3 = Color3.new(1, 1, 1)
		fill.Parent = bar
		Widgets.Corner(fill, 11)
		Widgets.Gradient(fill, Theme.Good)
		local progress = Widgets.Label(bar, "", 15)
		progress.Size = UDim2.fromScale(1, 1)
		progress.TextXAlignment = Enum.TextXAlignment.Center
		progress.TextStrokeTransparency = 0.4
		progress.ZIndex = 2

		local button = Widgets.Button(frame, "", Theme.Disabled, 20)
		button.AnchorPoint = Vector2.new(1, 0.5)
		button.Position = UDim2.new(1, -14, 0.5, 0)
		button.Size = UDim2.fromOffset(136, 56)
		button.Activated:Connect(function()
			Net.Get(Net.ClaimQuest):FireServer(index)
		end)

		table.insert(rows, { Title = title, Progress = progress, Fill = fill, Button = button })
	end
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	local quests = state.Quests
	for index, row in rows do
		local def = findDef(quests.Ids[index] or "")
		if not def then
			row.Title.Text = "—"
			row.Progress.Text = ""
			row.Fill.Size = UDim2.fromScale(0, 1)
			row.Button.Visible = false
			continue
		end
		local value = math.min(quests.Progress[index] or 0, def.Goal)
		local done = value >= def.Goal
		local claimed = quests.Claimed[index] == true
		row.Title.Text = (string.gsub(def.Text, "{n}", tostring(def.Goal)))
		row.Progress.Text = `{value} / {def.Goal}`
		row.Fill.Size = UDim2.fromScale(value / def.Goal, 1)
		row.Button.Visible = true
		if claimed then
			row.Button.Text = "DONE ✓"
			Widgets.SetButtonColor(row.Button, Theme.Disabled)
		elseif done then
			row.Button.Text = "CLAIM!"
			Widgets.SetButtonColor(row.Button, Theme.Good)
		else
			row.Button.Text = `{def.RewardHits} bonks`
			Widgets.SetButtonColor(row.Button, Theme.CardLight)
		end
	end
end

local function tick()
	local now = Workspace:GetServerTimeNow()
	local nextDay = (now // SECONDS_PER_DAY + 1) * SECONDS_PER_DAY
	resetLabel.Text = `New quests in {Widgets.Duration(nextDay - now)} · rewards grow with your upgrades`
end

function QuestController.Init()
	build()
end

function QuestController.Start()
	State.Changed:Connect(refresh)
	refresh()
	task.spawn(function()
		while true do
			tick()
			task.wait(1)
		end
	end)
end

return QuestController
