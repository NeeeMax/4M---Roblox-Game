--!strict
-- Tycoon menus built in code: the Shibas collection panel (equip / unequip / merge) and the hatch reveal
-- (docs/decisions/0006). Driven by TycoonController, which passes the current TycoonState in; nothing here
-- awards anything, every button only fires a remote and the server decides.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Net = require(ReplicatedStorage.Shared.Net)
local TycoonConfig = require(ReplicatedStorage.Shared.Config.Tycoon)
local Types = require(ReplicatedStorage.Shared.Types)

local Theme = require(script.Parent.Theme)
local Widgets = require(script.Parent.Widgets)

type TycoonState = Types.TycoonState
type HatchResult = Types.HatchResult

local PANEL_NAME = "Shibas"
local ACCENT = Color3.fromRGB(255, 170, 60)
local RARITY_NAMES = { "Common", "Uncommon", "Rare", "Epic", "Legendary" }
local RARITY_COLORS = {
	Color3.fromRGB(190, 190, 200),
	Color3.fromRGB(90, 220, 110),
	Color3.fromRGB(70, 160, 255),
	Color3.fromRGB(190, 100, 255),
	Color3.fromRGB(255, 200, 40),
}
local VARIANT_COLORS: { [string]: Color3 } = {
	Normal = Theme.Muted,
	Shiny = Color3.fromRGB(255, 226, 90),
	Rainbow = Color3.fromRGB(255, 120, 220),
	Huge = Color3.fromRGB(255, 140, 50),
}
local SINGLE_SECONDS = 2.6
local GRID_SECONDS = 3.6
local GRID_COLUMNS = 5

local TycoonPanels = {}

-- ==== helpers ====================================================================================================

local function shibaDef(tier: number): EconomyConfig.ShibaDef?
	return EconomyConfig.Shibas[tier + 1]
end

local function shibaName(tier: number): string
	local def = shibaDef(tier)
	return if def then def.Name else `Shiba {tier + 1}`
end

local function shibaColor(tier: number): Color3
	local def = shibaDef(tier)
	return if def then def.Color else Theme.Muted
end

-- 1 … 5: how rare the tier is inside its egg (the egg holds TiersPerZone tiers, common to rare).
local function rarityIndex(tier: number): number
	return math.clamp(tier % TycoonConfig.TiersPerZone + 1, 1, #RARITY_NAMES)
end

local function outlined(parent: Instance, text: string, size: number, color: Color3): TextLabel
	local label = Widgets.Label(parent, text, size, color)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextStrokeTransparency = 0
	label.Font = Theme.Font
	return label
end

-- ==== hatch reveal ===============================================================================================

local hatchGui: ScreenGui? = nil
local hatchQueue: { { HatchResult } } = {}
local hatchRunning = false
local hatchSkipped = false

local function ensureHatchGui(): ScreenGui
	local existing = hatchGui
	if existing and existing.Parent then
		return existing
	end
	local gui = Widgets.Screen("TycoonHatch", 40)
	gui.Enabled = false
	hatchGui = gui
	return gui
end

-- One reveal card: rarity-coloured, Shiba name, variant, NEW! / Duplicate -> merged.
local function buildResultCard(parent: Instance, result: HatchResult, size: Vector2, textScale: number): Frame
	local rarity = rarityIndex(result.Tier)
	local color = shibaColor(result.Tier)
	local card = Instance.new("Frame")
	card.BackgroundColor3 = Theme.Panel
	card.Size = UDim2.fromOffset(size.X, size.Y)
	card.Parent = parent
	Widgets.Corner(card, 16)
	Widgets.Stroke(card, 4, RARITY_COLORS[rarity])

	local icon = Instance.new("Frame")
	icon.AnchorPoint = Vector2.new(0.5, 0)
	icon.Position = UDim2.fromScale(0.5, 0.1)
	local iconSize = size.X * 0.42
	icon.Size = UDim2.fromOffset(iconSize, iconSize)
	icon.BackgroundColor3 = color
	icon.Parent = card
	Widgets.Corner(icon, iconSize / 2)
	Widgets.Stroke(icon, 3)
	Widgets.Gradient(icon, color)
	local initial = outlined(icon, string.sub(shibaName(result.Tier), 1, 1), math.floor(28 * textScale), Theme.Text)
	initial.Size = UDim2.fromScale(1, 1)

	local rarityLabel =
		outlined(card, string.upper(RARITY_NAMES[rarity]), math.floor(13 * textScale), RARITY_COLORS[rarity])
	rarityLabel.Position = UDim2.new(0, 0, 0.1, iconSize + 2)
	rarityLabel.Size = UDim2.new(1, 0, 0, math.floor(16 * textScale))

	local name = outlined(card, shibaName(result.Tier), math.floor(20 * textScale), Theme.Text)
	name.Position = UDim2.new(0, 4, 0.1, iconSize + math.floor(18 * textScale))
	name.Size = UDim2.new(1, -8, 0, math.floor(24 * textScale))
	name.TextWrapped = true
	name.TextScaled = false

	local variant =
		outlined(card, result.Variant, math.floor(15 * textScale), VARIANT_COLORS[result.Variant] or Theme.Muted)
	variant.Position = UDim2.new(0, 0, 0.1, iconSize + math.floor(42 * textScale))
	variant.Size = UDim2.new(1, 0, 0, math.floor(18 * textScale))

	local flag = outlined(
		card,
		if result.Duplicate then "Duplicate -> merged" else "NEW!",
		math.floor(16 * textScale),
		if result.Duplicate then Theme.Muted else Theme.Good
	)
	flag.AnchorPoint = Vector2.new(0, 1)
	flag.Position = UDim2.new(0, 0, 1, -6)
	flag.Size = UDim2.new(1, 0, 0, math.floor(20 * textScale))
	return card
end

-- Plays one hatch. Blocks until it is over or skipped by a click/tap.
local function playHatch(results: { HatchResult })
	if #results == 0 then
		return
	end
	local gui = ensureHatchGui()
	hatchSkipped = false

	local root = Instance.new("TextButton")
	root.Name = "Reveal"
	root.Text = ""
	root.AutoButtonColor = false
	root.BackgroundColor3 = Color3.new(0, 0, 0)
	root.BackgroundTransparency = 1
	root.Size = UDim2.fromScale(1, 1)
	root.Parent = gui
	local skipConnection = root.Activated:Connect(function()
		hatchSkipped = true
	end)

	local seconds = if #results == 1 then SINGLE_SECONDS else GRID_SECONDS
	local scales: { UIScale } = {}
	if #results == 1 then
		local card = buildResultCard(root, results[1], Vector2.new(240, 300), 1)
		card.AnchorPoint = Vector2.new(0.5, 0.5)
		card.Position = UDim2.fromScale(0.5, 0.5)
		local scale = Instance.new("UIScale")
		scale.Scale = 0.2
		scale.Parent = card
		table.insert(scales, scale)
	else
		local count = #results
		local columns = math.min(GRID_COLUMNS, count)
		local rows = math.ceil(count / columns)
		local cardSize = Vector2.new(150, 190)
		local grid = Instance.new("Frame")
		grid.BackgroundTransparency = 1
		grid.AnchorPoint = Vector2.new(0.5, 0.5)
		grid.Position = UDim2.fromScale(0.5, 0.5)
		grid.Size = UDim2.fromOffset(columns * (cardSize.X + 10), rows * (cardSize.Y + 10))
		grid.Parent = root
		local layout = Instance.new("UIGridLayout")
		layout.CellSize = UDim2.fromOffset(cardSize.X, cardSize.Y)
		layout.CellPadding = UDim2.fromOffset(10, 10)
		layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
		layout.VerticalAlignment = Enum.VerticalAlignment.Center
		layout.SortOrder = Enum.SortOrder.LayoutOrder
		layout.Parent = grid
		-- Wide grids shrink on small screens.
		local fit = Instance.new("UIScale")
		fit.Scale = if columns * (cardSize.X + 10) > 760 then 760 / (columns * (cardSize.X + 10)) else 1
		fit.Parent = grid
		for index, result in results do
			local cell = Instance.new("Frame")
			cell.BackgroundTransparency = 1
			cell.LayoutOrder = index
			cell.Parent = grid
			local card = buildResultCard(cell, result, cardSize, 0.8)
			local scale = Instance.new("UIScale")
			scale.Scale = 0.2
			scale.Parent = card
			table.insert(scales, scale)
		end
	end

	local hint = outlined(root, "Tap to continue", 16, Theme.Muted)
	hint.AnchorPoint = Vector2.new(0.5, 1)
	hint.Position = UDim2.new(0.5, 0, 1, -24)
	hint.Size = UDim2.fromOffset(300, 24)

	gui.Enabled = true
	TweenService:Create(root, TweenInfo.new(0.2), { BackgroundTransparency = 0.45 }):Play()
	for index, scale in scales do
		task.delay(math.min(index - 1, 9) * 0.05, function()
			if scale.Parent then
				TweenService:Create(scale, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = 1 }):Play()
			end
		end)
	end

	local elapsed = 0
	while elapsed < seconds and not hatchSkipped do
		elapsed += task.wait(0.05)
	end

	skipConnection:Disconnect()
	root:Destroy()
	gui.Enabled = false
end

local function runHatchQueue()
	if hatchRunning then
		return
	end
	hatchRunning = true
	task.spawn(function()
		while #hatchQueue > 0 do
			local results = table.remove(hatchQueue, 1)
			if results then
				local ok, err = pcall(function()
					playHatch(results)
				end)
				if not ok then
					warn(`[TycoonPanels] hatch reveal failed: {err}`)
					if hatchGui then
						hatchGui.Enabled = false
					end
				end
			end
		end
		hatchRunning = false
	end)
end

-- Queues a reveal for the results of one HatchResults event.
function TycoonPanels.ShowHatch(results: { HatchResult })
	-- Keep the queue short: a spammed hatch shows only the latest ones.
	if #hatchQueue >= 3 then
		table.remove(hatchQueue, 1)
	end
	table.insert(hatchQueue, results)
	runHatchQueue()
end

-- ==== collection panel ===========================================================================================

local panel: Widgets.Panel? = nil
local getTycoon: (() -> TycoonState?)? = nil
local counterLabel: TextLabel? = nil
local listFrame: ScrollingFrame? = nil
local pickerFrame: Frame? = nil
local lastSignature = ""

local function currentTycoon(): TycoonState?
	if getTycoon then
		return getTycoon()
	end
	return nil
end

local function hidePicker()
	if pickerFrame then
		pickerFrame:Destroy()
		pickerFrame = nil
	end
end

-- Equipped slot of a Shiba id, or nil.
local function slotOf(tycoon: TycoonState, shibaId: string): number?
	for key, id in tycoon.Equipped do
		if id == shibaId then
			return tonumber(key)
		end
	end
	return nil
end

local function firstEmptySlot(tycoon: TycoonState): number?
	for slot = 1, tycoon.EquipSlots do
		if not tycoon.Equipped[tostring(slot)] then
			return slot
		end
	end
	return nil
end

-- A modal list inside the panel: `title`, one button per option, Cancel.
local function showPicker(title: string, options: { { Text: string, Color: Color3, OnPick: () -> () } })
	local current = panel
	if not current then
		return
	end
	hidePicker()
	local overlay = Instance.new("Frame")
	overlay.Name = "Picker"
	overlay.BackgroundColor3 = Color3.new(0, 0, 0)
	overlay.BackgroundTransparency = 0.25
	overlay.Size = UDim2.fromScale(1, 1)
	overlay.ZIndex = 20
	overlay.Active = true
	overlay.Parent = current.Content
	pickerFrame = overlay

	local box = Instance.new("Frame")
	box.AnchorPoint = Vector2.new(0.5, 0.5)
	box.Position = UDim2.fromScale(0.5, 0.5)
	box.Size = UDim2.fromOffset(420, 380)
	box.BackgroundColor3 = Theme.Card
	box.ZIndex = 21
	box.Parent = overlay
	Widgets.Corner(box, 16)
	Widgets.Stroke(box, 3)

	local heading = outlined(box, title, 22, Theme.Text)
	heading.Position = UDim2.fromOffset(0, 6)
	heading.Size = UDim2.new(1, 0, 0, 30)
	heading.ZIndex = 22

	local scroller = Instance.new("ScrollingFrame")
	scroller.BackgroundTransparency = 1
	scroller.BorderSizePixel = 0
	scroller.ScrollBarThickness = 6
	scroller.AutomaticCanvasSize = Enum.AutomaticSize.Y
	scroller.CanvasSize = UDim2.new()
	scroller.Position = UDim2.fromOffset(12, 42)
	scroller.Size = UDim2.new(1, -24, 1, -98)
	scroller.ZIndex = 22
	scroller.Parent = box
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = scroller

	for index, option in options do
		local button = Widgets.Button(scroller, option.Text, option.Color, 16)
		button.LayoutOrder = index
		button.Size = UDim2.new(1, -8, 0, 34)
		button.ZIndex = 23
		button.Activated:Connect(function()
			hidePicker()
			option.OnPick()
		end)
	end

	local cancel = Widgets.Button(box, "Cancel", Theme.Disabled, 18)
	cancel.AnchorPoint = Vector2.new(0.5, 1)
	cancel.Position = UDim2.new(0.5, 0, 1, -10)
	cancel.Size = UDim2.fromOffset(160, 38)
	cancel.ZIndex = 22
	cancel.Activated:Connect(hidePicker)
end

local function chooseEquipSlot(shibaId: string)
	local tycoon = currentTycoon()
	if not tycoon then
		return
	end
	local preferred = firstEmptySlot(tycoon)
	local options = {}
	for slot = 1, tycoon.EquipSlots do
		local occupant = tycoon.Equipped[tostring(slot)]
		local occupantShiba = if occupant then tycoon.Shibas[occupant] else nil
		local label = if occupantShiba
			then `Slot {slot}: replaces {shibaName(occupantShiba.Tier)}`
			else `Slot {slot}: empty`
		table.insert(options, {
			Text = label,
			Color = if slot == preferred then Theme.Good else Theme.MenuButton,
			OnPick = function()
				Net.Get(Net.EquipShiba):FireServer(shibaId, slot)
			end,
		})
	end
	showPicker("Choose a slot", options)
end

local function chooseMergeSource(targetId: string)
	local tycoon = currentTycoon()
	local target = if tycoon then tycoon.Shibas[targetId] else nil
	if not tycoon or not target then
		return
	end
	local options = {}
	local ids: { string } = {}
	for id, shiba in tycoon.Shibas do
		-- The server refuses equipped sources, so only offer free duplicates of the same tier.
		if id ~= targetId and shiba.Tier == target.Tier and not slotOf(tycoon, id) then
			table.insert(ids, id)
		end
	end
	table.sort(ids, function(a, b)
		local sa, sb = tycoon.Shibas[a], tycoon.Shibas[b]
		if sa.Level ~= sb.Level then
			return sa.Level < sb.Level
		end
		return a < b
	end)
	for _, id in ids do
		local source = tycoon.Shibas[id]
		table.insert(options, {
			Text = `Lv {source.Level} {source.Variant} (consumed)`,
			Color = Theme.MenuButton,
			OnPick = function()
				Net.Get(Net.MergeShibas):FireServer(targetId, id)
			end,
		})
	end
	if #options == 0 then
		return
	end
	showPicker(`Merge into Lv {target.Level} {shibaName(target.Tier)}`, options)
end

local function buildOwnedRow(list: ScrollingFrame, tycoon: TycoonState, id: string, order: number)
	local shiba = tycoon.Shibas[id]
	local slot = slotOf(tycoon, id)
	local row = Widgets.Card(list, 56)
	row.LayoutOrder = order

	local color = shibaColor(shiba.Tier)
	local dot = Instance.new("Frame")
	dot.Position = UDim2.fromOffset(8, 8)
	dot.Size = UDim2.fromOffset(40, 40)
	dot.BackgroundColor3 = color
	dot.Parent = row
	Widgets.Corner(dot, 20)
	Widgets.Stroke(dot, 2)

	local name = Widgets.Label(row, shibaName(shiba.Tier), 17, Theme.Text)
	name.Position = UDim2.fromOffset(56, 4)
	name.Size = UDim2.fromOffset(230, 24)
	name.TextTruncate = Enum.TextTruncate.AtEnd

	local info = `Lv {shiba.Level}  ·  {shiba.Variant}  ·  ` .. (if slot then `Slot {slot}` else "not equipped")
	local detail = Widgets.Label(row, info, 13, if slot then Theme.Good else Theme.Muted)
	detail.Font = Theme.BodyFont
	detail.Position = UDim2.fromOffset(56, 29)
	detail.Size = UDim2.fromOffset(260, 20)

	local mergeCount = 0
	for otherId, other in tycoon.Shibas do
		if otherId ~= id and other.Tier == shiba.Tier and not slotOf(tycoon, otherId) then
			mergeCount += 1
		end
	end

	local right = 8
	local mergeButton = Widgets.Button(row, "Merge", if mergeCount > 0 then Theme.Info else Theme.Disabled, 15)
	mergeButton.AnchorPoint = Vector2.new(1, 0.5)
	mergeButton.Position = UDim2.new(1, -right, 0.5, 0)
	mergeButton.Size = UDim2.fromOffset(78, 36)
	mergeButton.Activated:Connect(function()
		if mergeCount > 0 then
			chooseMergeSource(id)
		end
	end)
	right += 86

	local equipButton =
		Widgets.Button(row, if slot then "Unequip" else "Equip", if slot then Theme.Bad else Theme.Good, 15)
	equipButton.AnchorPoint = Vector2.new(1, 0.5)
	equipButton.Position = UDim2.new(1, -right, 0.5, 0)
	equipButton.Size = UDim2.fromOffset(92, 36)
	equipButton.Activated:Connect(function()
		if slot then
			Net.Get(Net.UnequipShiba):FireServer(slot)
			return
		end
		local latest = currentTycoon()
		local empty = if latest then firstEmptySlot(latest) else nil
		if empty then
			Net.Get(Net.EquipShiba):FireServer(id, empty)
		else
			chooseEquipSlot(id)
		end
	end)
	right += 100

	-- Second equip button: pick the slot by hand.
	if not slot and tycoon.EquipSlots > 1 then
		local pick = Widgets.Button(row, "Slot…", Theme.MenuButton, 14)
		pick.AnchorPoint = Vector2.new(1, 0.5)
		pick.Position = UDim2.new(1, -right, 0.5, 0)
		pick.Size = UDim2.fromOffset(66, 36)
		pick.Activated:Connect(function()
			chooseEquipSlot(id)
		end)
	end
end

local function signatureOf(tycoon: TycoonState): string
	local parts: { string } = { tostring(tycoon.EquipSlots) }
	local ids: { string } = {}
	for id in tycoon.Shibas do
		table.insert(ids, id)
	end
	table.sort(ids)
	for _, id in ids do
		local shiba = tycoon.Shibas[id]
		table.insert(parts, `{id}:{shiba.Tier}:{shiba.Level}:{shiba.Variant}`)
	end
	for slot = 1, tycoon.EquipSlots do
		table.insert(parts, tycoon.Equipped[tostring(slot)] or "-")
	end
	return table.concat(parts, "|")
end

local function rebuild(tycoon: TycoonState)
	local list = listFrame
	if not list then
		return
	end
	for _, child in list:GetChildren() do
		if not child:IsA("UIListLayout") and not child:IsA("UIPadding") then
			child:Destroy()
		end
	end

	local ids: { string } = {}
	local ownedTiers: { [number]: boolean } = {}
	for id, shiba in tycoon.Shibas do
		table.insert(ids, id)
		ownedTiers[shiba.Tier] = true
	end
	table.sort(ids, function(a, b)
		local sa, sb = tycoon.Shibas[a], tycoon.Shibas[b]
		if sa.Tier ~= sb.Tier then
			return sa.Tier > sb.Tier
		end
		if sa.Level ~= sb.Level then
			return sa.Level > sb.Level
		end
		return a < b
	end)

	local typesOwned = 0
	for _ in ownedTiers do
		typesOwned += 1
	end
	if counterLabel then
		counterLabel.Text = `Owned {#ids} Shibas  ·  {typesOwned} / {TycoonConfig.TierCount} types`
	end

	local order = 0
	for _, id in ids do
		order += 1
		buildOwnedRow(list, tycoon, id, order)
	end
	if #ids == 0 then
		local empty = Widgets.Label(list, "No Shibas yet. Hatch an egg!", 18, Theme.Muted)
		empty.Size = UDim2.new(1, 0, 0, 40)
		empty.TextXAlignment = Enum.TextXAlignment.Center
		empty.LayoutOrder = 1
		order = 1
	end

	-- Silhouettes of the types not found yet.
	local header = Widgets.Label(list, "Not found yet", 16, Theme.Muted)
	header.LayoutOrder = order + 1
	header.Size = UDim2.new(1, 0, 0, 28)
	local grid = Instance.new("Frame")
	grid.BackgroundTransparency = 1
	grid.AutomaticSize = Enum.AutomaticSize.Y
	grid.Size = UDim2.fromScale(1, 0)
	grid.LayoutOrder = order + 2
	grid.Parent = list
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.fromOffset(76, 60)
	layout.CellPadding = UDim2.fromOffset(6, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = grid
	for tier = 0, TycoonConfig.TierCount - 1 do
		if not ownedTiers[tier] then
			local cell = Instance.new("Frame")
			cell.LayoutOrder = tier
			cell.BackgroundColor3 = Theme.Background
			cell.Parent = grid
			Widgets.Corner(cell, 10)
			Widgets.Stroke(cell, 2)
			local mark = outlined(cell, "???", 16, Theme.Disabled)
			mark.Size = UDim2.fromScale(1, 0.6)
			local number = outlined(cell, `#{tier + 1}`, 12, Theme.Disabled)
			number.AnchorPoint = Vector2.new(0, 1)
			number.Position = UDim2.fromScale(0, 1)
			number.Size = UDim2.fromScale(1, 0.4)
		end
	end
end

-- Redraws the list when the collection changed (or `force`). Cheap when the panel is closed.
function TycoonPanels.RefreshCollection(force: boolean)
	local tycoon = currentTycoon()
	if not tycoon or not panel then
		return
	end
	if not force and not Widgets.IsOpen(PANEL_NAME) then
		return
	end
	local signature = signatureOf(tycoon)
	if not force and signature == lastSignature then
		return
	end
	lastSignature = signature
	hidePicker()
	rebuild(tycoon)
end

-- Builds the collection panel once. `getState` returns the latest TycoonState.
function TycoonPanels.BuildCollection(getState: () -> TycoonState?)
	if panel then
		return
	end
	getTycoon = getState
	local built = Widgets.Panel(PANEL_NAME, "SHIBAS", Vector2.new(720, 540), ACCENT)
	panel = built
	local content = built.Content

	local counter = Widgets.Label(content, "", 18, Theme.Text)
	counter.Font = Theme.BodyFont
	counter.Size = UDim2.new(1, 0, 0, 30)
	counter.TextStrokeTransparency = 0.5
	counterLabel = counter

	local holder = Instance.new("Frame")
	holder.BackgroundTransparency = 1
	holder.Position = UDim2.fromOffset(0, 36)
	holder.Size = UDim2.new(1, 0, 1, -36)
	holder.Parent = content
	listFrame = Widgets.List(holder, 6)

	built.OnOpen = function()
		TycoonPanels.RefreshCollection(true)
	end
end

function TycoonPanels.OpenCollection()
	if panel then
		Widgets.Toggle(PANEL_NAME)
	end
end

function TycoonPanels.CloseCollection()
	if panel and Widgets.IsOpen(PANEL_NAME) then
		Widgets.CloseAll()
	end
end

return TycoonPanels
