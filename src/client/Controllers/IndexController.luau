--!strict
-- Shiba-Index menu (Config/Index): a grid of cards, one per entry. Unseen entries are a dark "???" silhouette, seen
-- ones show their name and colour, and a CLAIM button pays the one-time discovery reward (ClaimIndex). A bar on top
-- shows the completion ("12/31") and the completion bonus. Opened with Widgets.Open("Index") (HUD button).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Index = require(ReplicatedStorage.Shared.Config.Index)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local ACCENT = Color3.fromRGB(255, 150, 60)
local CARD_SIZE = Vector2.new(124, 158)
local KIND_TAGS: { [Index.Kind]: string } = {
	Shiba = "SHIBA",
	Projectile = "STICK",
	Golden = "GOLDEN",
	Trophy = "TROPHY",
}

type Card = {
	Entry: Index.Entry,
	Frame: Frame,
	Icon: Frame,
	IconGradient: UIGradient,
	IconText: TextLabel,
	Name: TextLabel,
	Button: TextButton,
}

local cards: { Card } = {}
local countLabel: TextLabel
local fill: Frame
local bonusButton: TextButton

local IndexController = {}

local function claim(id: string)
	Net.Get(Net.ClaimIndex):FireServer(id)
end

local function buildCard(parent: Instance, entry: Index.Entry, order: number): Card
	local frame = Instance.new("Frame")
	frame.Name = entry.Id
	frame.LayoutOrder = order
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = parent
	Widgets.Corner(frame, 12)
	Widgets.Stroke(frame, 2)

	local tag = Widgets.Label(frame, KIND_TAGS[entry.Kind], 11, Theme.Muted)
	tag.Font = Theme.BodyFont
	tag.Position = UDim2.fromOffset(0, 4)
	tag.Size = UDim2.new(1, 0, 0, 14)
	tag.TextXAlignment = Enum.TextXAlignment.Center

	local icon = Instance.new("Frame")
	icon.AnchorPoint = Vector2.new(0.5, 0)
	icon.Position = UDim2.new(0.5, 0, 0, 20)
	icon.Size = UDim2.fromOffset(64, 64)
	icon.BackgroundColor3 = Color3.new(1, 1, 1)
	icon.Parent = frame
	Widgets.Corner(icon, 32)
	Widgets.Stroke(icon, 3)
	local iconGradient = Instance.new("UIGradient")
	iconGradient.Rotation = 90
	iconGradient.Parent = icon
	local iconText = Widgets.Label(icon, "", 26, Theme.Text)
	iconText.Size = UDim2.fromScale(1, 1)
	iconText.TextXAlignment = Enum.TextXAlignment.Center
	iconText.TextStrokeTransparency = 0

	local name = Widgets.Label(frame, "", 14, Theme.Text)
	name.Position = UDim2.fromOffset(4, 88)
	name.Size = UDim2.new(1, -8, 0, 30)
	name.TextXAlignment = Enum.TextXAlignment.Center
	name.TextWrapped = true
	name.TextStrokeTransparency = 0.5

	local button = Widgets.Button(frame, "", Theme.Disabled, 15)
	button.AnchorPoint = Vector2.new(0.5, 1)
	button.Position = UDim2.new(0.5, 0, 1, -6)
	button.Size = UDim2.new(1, -16, 0, 28)
	button.Activated:Connect(function()
		claim(entry.Id)
	end)

	return {
		Entry = entry,
		Frame = frame,
		Icon = icon,
		IconGradient = iconGradient,
		IconText = iconText,
		Name = name,
		Button = button,
	}
end

local function build()
	local panel = Widgets.Panel("Index", "SHIBA-INDEX", Vector2.new(720, 540), ACCENT)
	local content = panel.Content

	-- Completion bar and bonus.
	local bar = Instance.new("Frame")
	bar.Size = UDim2.new(1, -190, 0, 34)
	bar.BackgroundColor3 = Theme.Background
	bar.Parent = content
	Widgets.Corner(bar, 17)
	Widgets.Stroke(bar, 2)
	fill = Instance.new("Frame")
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = Color3.new(1, 1, 1)
	fill.Parent = bar
	Widgets.Corner(fill, 17)
	Widgets.Gradient(fill, ACCENT)
	countLabel = Widgets.Label(bar, "", 20)
	countLabel.Size = UDim2.fromScale(1, 1)
	countLabel.TextXAlignment = Enum.TextXAlignment.Center
	countLabel.TextStrokeTransparency = 0.2
	countLabel.ZIndex = 2

	bonusButton = Widgets.Button(content, "", Theme.Disabled, 16)
	bonusButton.AnchorPoint = Vector2.new(1, 0)
	bonusButton.Position = UDim2.new(1, 0, 0, -2)
	bonusButton.Size = UDim2.fromOffset(176, 38)
	bonusButton.Activated:Connect(function()
		claim(Index.CompleteId)
	end)

	-- Card grid.
	local list = Instance.new("ScrollingFrame")
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 6
	list.ScrollBarImageColor3 = Theme.Muted
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Position = UDim2.fromOffset(0, 46)
	list.Size = UDim2.new(1, 0, 1, -46)
	list.Parent = content
	local grid = Instance.new("UIGridLayout")
	grid.CellSize = UDim2.fromOffset(CARD_SIZE.X, CARD_SIZE.Y)
	grid.CellPadding = UDim2.fromOffset(10, 10)
	grid.SortOrder = Enum.SortOrder.LayoutOrder
	grid.HorizontalAlignment = Enum.HorizontalAlignment.Center
	grid.Parent = list
	local pad = Instance.new("UIPadding")
	pad.PaddingTop = UDim.new(0, 4)
	pad.PaddingBottom = UDim.new(0, 4)
	pad.PaddingRight = UDim.new(0, 8)
	pad.Parent = list

	for order, entry in Index.Entries do
		table.insert(cards, buildCard(list, entry, order))
	end
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	local seen, claimed = state.Index.Seen, state.Index.Claimed
	-- Counts only entries needed for the completion bonus (Optional trophies still show and pay their reward).
	local seenCount = 0
	local total = 0
	for _, card in cards do
		local entry = card.Entry
		local isSeen = seen[entry.Id] == true
		if entry.Required then
			total += 1
			if isSeen then
				seenCount += 1
			end
		end
		if isSeen then
			local h, s, v = entry.Color:ToHSV()
			card.IconGradient.Color = ColorSequence.new(entry.Color, Color3.fromHSV(h, s, v * 0.7))
			card.IconText.Text = string.upper(string.sub(entry.DisplayName, 1, 1))
			card.Name.Text = entry.DisplayName
			card.Name.TextColor3 = entry.Color
			card.Frame.BackgroundColor3 = Theme.CardLight
		else
			-- A dark silhouette with only a hint of the entry's colour.
			local dark = entry.Color:Lerp(Theme.Stroke, 0.8)
			card.IconGradient.Color = ColorSequence.new(dark, Theme.Stroke)
			card.IconText.Text = "???"
			card.Name.Text = "???"
			card.Name.TextColor3 = Theme.Muted
			card.Frame.BackgroundColor3 = Theme.Card
		end
		if isSeen and not claimed[entry.Id] then
			card.Button.Text = "CLAIM!"
			Widgets.SetButtonColor(card.Button, Theme.Good)
			card.Button.Active = true
		elseif isSeen then
			card.Button.Text = "FOUND ✓"
			Widgets.SetButtonColor(card.Button, Theme.Disabled)
			card.Button.Active = false
		else
			card.Button.Text = `{entry.RewardHits} bonks`
			Widgets.SetButtonColor(card.Button, Theme.Card)
			card.Button.Active = false
		end
	end

	countLabel.Text = `{seenCount}/{total} found`
	fill.Size = UDim2.fromScale(if total > 0 then seenCount / total else 0, 1)
	fill.Visible = seenCount > 0
	if claimed[Index.CompleteId] then
		bonusButton.Text = "BONUS ✓"
		Widgets.SetButtonColor(bonusButton, Theme.Disabled)
	elseif seenCount >= total then
		bonusButton.Text = "CLAIM BONUS!"
		Widgets.SetButtonColor(bonusButton, Theme.Good)
	else
		bonusButton.Text = `100%: {Index.CompleteRewardHits} bonks`
		Widgets.SetButtonColor(bonusButton, Theme.Card)
	end
end

function IndexController.Init()
	build()
end

function IndexController.Start()
	State.Start()
	State.Changed:Connect(refresh)
	refresh()
end

return IndexController
