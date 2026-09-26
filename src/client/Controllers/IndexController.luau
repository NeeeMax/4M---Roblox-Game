--!strict
-- Shiba-Index menu (Config/Index): a grid of cards, one per entry. Unseen entries are a dark "???" silhouette, seen
-- ones show their name and colour, and a CLAIM button pays the one-time discovery reward (ClaimIndex). Two tabs:
-- - COLLECTION: Shibas, sticks, golden stick, trophies. The bar on top shows the completion ("12/41") and the
--   completion bonus; Robux-only trophies are marked EXCLUSIVE and never needed for it (Index.CountsForCompletion).
-- - VARIANTS: one card per Shiba and variant (Shiny / Rainbow / Huge, docs → Shiba Variants), its own progress
--   ("7/90", and per variant), no completion bonus.
-- Opened with Widgets.Open("Index") (HUD button).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Index = require(ReplicatedStorage.Shared.Config.Index)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local ACCENT = Color3.fromRGB(255, 150, 60)
local VARIANT_ACCENT = Color3.fromRGB(255, 110, 210)
local CARD_SIZE = Vector2.new(124, 158)
local KIND_TAGS: { [Index.Kind]: string } = {
	Shiba = "SHIBA",
	Projectile = "STICK",
	Golden = "GOLDEN",
	Trophy = "TROPHY",
	Variant = "VARIANT",
}

type Tab = "Collection" | "Variants"

type Card = {
	Entry: Index.Entry,
	Tab: Tab,
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
local fillGradient: UIGradient
local bar: Frame
local bonusButton: TextButton
local variantLabel: TextLabel
local tabButtons: { [Tab]: TextButton } = {}
local currentTab: Tab = "Collection"
local refresh: () -> ()

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

	local tagText = if entry.Exclusive then "EXCLUSIVE" else KIND_TAGS[entry.Kind]
	local tag = Widgets.Label(frame, tagText, 11, if entry.Exclusive then Theme.Price else Theme.Muted)
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
		Tab = if entry.Kind == "Variant" then "Variants" else "Collection",
		Frame = frame,
		Icon = icon,
		IconGradient = iconGradient,
		IconText = iconText,
		Name = name,
		Button = button,
	}
end

local function selectTab(tab: Tab)
	currentTab = tab
	refresh()
end

local function build()
	local panel = Widgets.Panel("Index", "SHIBA-INDEX", Vector2.new(720, 540), ACCENT)
	local content = panel.Content

	-- Tabs.
	for index, tab: Tab in { "Collection" :: Tab, "Variants" :: Tab } do
		local button = Widgets.Button(content, string.upper(tab), Theme.Card, 16)
		button.Position = UDim2.fromOffset((index - 1) * 150, 0)
		button.Size = UDim2.fromOffset(142, 32)
		button.Activated:Connect(function()
			selectTab(tab)
		end)
		tabButtons[tab] = button
	end
	variantLabel = Widgets.Label(content, "", 14, Theme.Muted)
	variantLabel.Font = Theme.BodyFont
	variantLabel.Position = UDim2.fromOffset(310, 0)
	variantLabel.Size = UDim2.new(1, -310, 0, 32)
	variantLabel.TextXAlignment = Enum.TextXAlignment.Right

	-- Completion bar and bonus.
	bar = Instance.new("Frame")
	bar.Position = UDim2.fromOffset(0, 42)
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
	fillGradient = Instance.new("UIGradient")
	fillGradient.Rotation = 90
	fillGradient.Parent = fill
	countLabel = Widgets.Label(bar, "", 20)
	countLabel.Size = UDim2.fromScale(1, 1)
	countLabel.TextXAlignment = Enum.TextXAlignment.Center
	countLabel.TextStrokeTransparency = 0.2
	countLabel.ZIndex = 2

	bonusButton = Widgets.Button(content, "", Theme.Disabled, 16)
	bonusButton.AnchorPoint = Vector2.new(1, 0)
	bonusButton.Position = UDim2.new(1, 0, 0, 40)
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
	list.Position = UDim2.fromOffset(0, 88)
	list.Size = UDim2.new(1, 0, 1, -88)
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

local function drawCard(card: Card, seen: { [string]: boolean }, claimed: { [string]: boolean })
	local entry = card.Entry
	local isSeen = seen[entry.Id] == true
	if isSeen then
		local h, s, v = entry.Color:ToHSV()
		card.IconGradient.Color = ColorSequence.new(entry.Color, Color3.fromHSV(h, s, v * 0.7))
		card.IconText.Text = string.upper(string.sub(entry.DisplayName, 1, 1))
		card.Name.Text = entry.DisplayName
		card.Name.TextColor3 = entry.Color
		card.Frame.BackgroundColor3 = Theme.CardLight
	else
		-- A dark silhouette with only a hint of the entry's colour. Variant cards keep their variant's name.
		local dark = entry.Color:Lerp(Theme.Stroke, 0.8)
		card.IconGradient.Color = ColorSequence.new(dark, Theme.Stroke)
		card.IconText.Text = "???"
		card.Name.Text = if entry.Kind == "Variant" then `{entry.Variant} ???` else "???"
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

function refresh()
	local state = State.Get()
	if not state then
		return
	end
	local seen, claimed = state.Index.Seen, state.Index.Claimed
	-- Collection: entries the completion bonus needs. Variants: per variant.
	local required, requiredSeen = 0, 0
	local variantTotal, variantSeen = 0, 0
	local perVariant: { [string]: number } = {}
	local perVariantTotal: { [string]: number } = {}
	for _, card in cards do
		local entry = card.Entry
		local isSeen = seen[entry.Id] == true
		card.Frame.Visible = card.Tab == currentTab
		if card.Frame.Visible then
			drawCard(card, seen, claimed)
		end
		if Index.CountsForCompletion(entry) then
			required += 1
			requiredSeen += if isSeen then 1 else 0
		elseif entry.Kind == "Variant" then
			variantTotal += 1
			variantSeen += if isSeen then 1 else 0
			perVariantTotal[entry.Variant] = (perVariantTotal[entry.Variant] or 0) + 1
			perVariant[entry.Variant] = (perVariant[entry.Variant] or 0) + (if isSeen then 1 else 0)
		end
	end

	for tab, button in tabButtons do
		Widgets.SetButtonColor(button, if tab == currentTab then ACCENT else Theme.Card)
	end
	local variants = currentTab == "Variants"
	bonusButton.Visible = not variants
	variantLabel.Visible = variants
	bar.Size = if variants then UDim2.new(1, 0, 0, 34) else UDim2.new(1, -190, 0, 34)
	local color = if variants then VARIANT_ACCENT else ACCENT
	local h, s, v = color:ToHSV()
	fillGradient.Color = ColorSequence.new(color, Color3.fromHSV(h, s, v * 0.75))

	local found = if variants then variantSeen else requiredSeen
	local total = if variants then variantTotal else required
	countLabel.Text = if variants then `{found}/{total} variants found` else `{found}/{total} found`
	fill.Size = UDim2.fromScale(if total > 0 then found / total else 0, 1)
	fill.Visible = found > 0
	if variants then
		local parts: { string } = {}
		for _, variant in Index.VariantOrder do
			table.insert(parts, `{variant} {perVariant[variant] or 0}/{perVariantTotal[variant] or 0}`)
		end
		variantLabel.Text = table.concat(parts, " · ")
		return
	end
	if claimed[Index.CompleteId] then
		bonusButton.Text = "BONUS ✓"
		Widgets.SetButtonColor(bonusButton, Theme.Disabled)
	elseif requiredSeen >= required then
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
