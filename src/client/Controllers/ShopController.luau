--!strict
-- The shop menu (Config/Shop): tabs for POWERS (the gameplay passes, big cards with yellow Robux prices), other
-- game passes, items (Robux products) and trophies (Bonk Dollars or Robux), plus the starter-pack offer popup for new
-- players. Every button sends ShopBuy; the server prompts the Roblox purchase or checks the Bonk Dollars, and grants
-- the item. Other code opens a tab with ShopController.OpenTab("POWERS").

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local ROBUX = "R$"
local CARD_HEIGHT = 150
local POWER_HEIGHT = 132
local TAB_NAMES = { "POWERS", "PASSES", "ITEMS", "TROPHIES" }
local PRICE_YELLOW = Color3.fromRGB(255, 214, 40)
local PRICE_TEXT = Color3.fromRGB(40, 30, 0)

-- The POWERS tab, in this order: icon and the "before → after" line (nil = none). Effects: AutoCatchService
-- (AutoCatch), UpgradeService (RunFaster, StackUpgrade), HudController (Manage).
type PowerInfo = { Icon: string, Change: string? }
local POWER_ORDER = { "Manage", "RunFaster", "StackUpgrade", "AutoCatch" }
local POWERS: { [string]: PowerInfo } = {
	Manage = { Icon = "📋" },
	RunFaster = { Icon = "🏃", Change = "x1 → x1.5" },
	StackUpgrade = { Icon = "⏫", Change = "x1 → x10" },
	AutoCatch = { Icon = "🧲", Change = `0 → {Shop.Pass.AutoCatchRadius} studs` },
}

type Card = {
	Button: TextButton,
	-- Returns the button text and colour (and optionally the text colour) for the current state.
	Refresh: () -> (string, Color3, Color3?),
}

local cards: { Card } = {}
local tabs: { [string]: ScrollingFrame } = {}
local tabButtons: { [string]: TextButton } = {}
local offerShown = false
local currentTab = TAB_NAMES[1]

local ShopController = {}

local function buy(itemId: string)
	Net.Get(Net.ShopBuy):FireServer(itemId)
end

local function card(
	list: Instance,
	order: number,
	title: string,
	description: string,
	color: Color3,
	badge: string?
): TextButton
	local frame = Instance.new("Frame")
	frame.LayoutOrder = order
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = list
	Widgets.Corner(frame, 12)
	Widgets.Stroke(frame, 2, color)

	local icon = Instance.new("Frame")
	icon.Position = UDim2.fromOffset(10, 10)
	icon.Size = UDim2.fromOffset(64, 64)
	icon.BackgroundColor3 = Color3.new(1, 1, 1)
	icon.Parent = frame
	Widgets.Corner(icon, 32)
	Widgets.Stroke(icon, 2)
	Widgets.Gradient(icon, color)
	local iconText = Widgets.Label(icon, badge or string.sub(title, 1, 1), 26)
	iconText.Size = UDim2.fromScale(1, 1)
	iconText.TextXAlignment = Enum.TextXAlignment.Center

	local name = Widgets.Label(frame, title, 19)
	name.Position = UDim2.fromOffset(84, 8)
	name.Size = UDim2.new(1, -92, 0, 24)
	name.TextTruncate = Enum.TextTruncate.AtEnd
	local text = Widgets.Label(frame, description, 13, Theme.Muted)
	text.Font = Theme.BodyFont
	text.Position = UDim2.fromOffset(84, 34)
	text.Size = UDim2.new(1, -92, 0, 50)
	text.TextWrapped = true
	text.TextYAlignment = Enum.TextYAlignment.Top

	local button = Widgets.Button(frame, "", Theme.Good, 20)
	button.AnchorPoint = Vector2.new(0.5, 1)
	button.Position = UDim2.new(0.5, 0, 1, -10)
	button.Size = UDim2.new(1, -20, 0, 44)
	return button
end

local function grid(parent: Instance): ScrollingFrame
	local list = Instance.new("ScrollingFrame")
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 6
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Position = UDim2.fromOffset(0, 54)
	list.Size = UDim2.new(1, 0, 1, -54)
	list.Visible = false
	list.Parent = parent
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.new(0.5, -8, 0, CARD_HEIGHT)
	layout.CellPadding = UDim2.fromOffset(8, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	local padding = Instance.new("UIPadding")
	padding.PaddingRight = UDim.new(0, 10)
	padding.Parent = list
	return list
end

-- A vertical list for the wide POWERS cards.
local function powerList(parent: Instance): ScrollingFrame
	local list = Widgets.List(parent, 10)
	list.Position = UDim2.fromOffset(0, 54)
	list.Size = UDim2.new(1, 0, 1, -54)
	list.Visible = false
	return list
end

-- A wide card in the style of the POWERS menu: title, description, optional yellow "x1 → x1.5" line, a big
-- yellow Robux price pill bottom left and a round icon on the right. Returns the price pill.
local function powerCard(list: Instance, order: number, pass: Shop.Pass, info: PowerInfo): TextButton
	local frame = Instance.new("Frame")
	frame.LayoutOrder = order
	frame.Size = UDim2.new(1, 0, 0, POWER_HEIGHT)
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = list
	Widgets.Corner(frame, 14)
	Widgets.Stroke(frame, 2, pass.Color)

	local icon = Instance.new("Frame")
	icon.AnchorPoint = Vector2.new(1, 0.5)
	icon.Position = UDim2.new(1, -14, 0.5, 0)
	icon.Size = UDim2.fromOffset(96, 96)
	icon.BackgroundColor3 = Color3.new(1, 1, 1)
	icon.Parent = frame
	Widgets.Corner(icon, 48)
	Widgets.Stroke(icon, 3)
	Widgets.Gradient(icon, pass.Color)
	local iconText = Widgets.Label(icon, info.Icon, 52)
	iconText.Size = UDim2.fromScale(1, 1)
	iconText.TextXAlignment = Enum.TextXAlignment.Center

	local title = Widgets.Label(frame, string.upper(pass.DisplayName), 28)
	title.Position = UDim2.fromOffset(16, 8)
	title.Size = UDim2.new(1, -140, 0, 32)
	title.TextStrokeTransparency = 0.4
	title.TextTruncate = Enum.TextTruncate.AtEnd
	local text = Widgets.Label(frame, pass.Description, 15, Theme.Muted)
	text.Font = Theme.BodyFont
	text.Position = UDim2.fromOffset(16, 40)
	text.Size = UDim2.new(1, -140, 0, 36)
	text.TextWrapped = true
	text.TextYAlignment = Enum.TextYAlignment.Top

	local change = info.Change
	if change then
		local line = Widgets.Label(frame, change, 24, PRICE_YELLOW)
		line.AnchorPoint = Vector2.new(0, 1)
		line.Position = UDim2.new(0, 190, 1, -14)
		line.Size = UDim2.new(1, -330, 0, 40)
		line.TextStrokeTransparency = 0.3
		line.TextScaled = true
		local limit = Instance.new("UITextSizeConstraint")
		limit.MaxTextSize = 24
		limit.Parent = line
	end

	local price = Widgets.Button(frame, "", PRICE_YELLOW, 26)
	price.AnchorPoint = Vector2.new(0, 1)
	price.Position = UDim2.new(0, 14, 1, -12)
	price.Size = UDim2.fromOffset(160, 46)
	price.TextStrokeTransparency = 1
	price.Activated:Connect(function()
		buy(pass.Id)
	end)
	return price
end

local function showTab(name: string)
	if not tabs[name] then
		return
	end
	currentTab = name
	for tabName, list in tabs do
		list.Visible = tabName == name
		Widgets.SetButtonColor(tabButtons[tabName], if tabName == name then Theme.Info else Theme.CardLight)
	end
end

local function build()
	local panel = Widgets.Panel("Shop", "SHOP", Vector2.new(680, 600), Color3.fromRGB(70, 200, 120))
	local content = panel.Content

	local tabCount = #TAB_NAMES
	for index, name in TAB_NAMES do
		local button = Widgets.Button(content, name, Theme.CardLight, 20)
		button.Position = UDim2.new((index - 1) / tabCount, if index == 1 then 0 else 4, 0, 0)
		button.Size = UDim2.new(1 / tabCount, -6, 0, 44)
		button.Activated:Connect(function()
			showTab(name)
		end)
		tabButtons[name] = button
		tabs[name] = if name == "POWERS" then powerList(content) else grid(content)
	end

	for order, id in POWER_ORDER do
		local pass = Shop.GetPass(id)
		if pass then
			local price = powerCard(tabs.POWERS, order, pass, POWERS[id])
			table.insert(cards, {
				Button = price,
				Refresh = function()
					local state = State.Get()
					if state and state.Passes[pass.Id] then
						return "OWNED", Theme.Good, Theme.Text
					end
					return `{ROBUX} {pass.Robux}`, PRICE_YELLOW, PRICE_TEXT
				end,
			})
		end
	end

	for index, pass in Shop.Passes do
		if POWERS[pass.Id] then
			-- Shown on the POWERS tab.
			continue
		end
		local button = card(tabs.PASSES, index, pass.DisplayName, pass.Description, pass.Color)
		button.Activated:Connect(function()
			buy(pass.Id)
		end)
		table.insert(cards, {
			Button = button,
			Refresh = function()
				local state = State.Get()
				if state and state.Passes[pass.Id] then
					return "OWNED", Theme.Disabled
				end
				return `{ROBUX} {pass.Robux}`, Theme.Good
			end,
		})
	end

	for index, product in Shop.Products do
		if product.Kind == "DoubleOffline" then
			-- Only offered in the "Welcome back" popup (WelcomeBackController), when there is something to double.
			continue
		end
		local button = card(tabs.ITEMS, index, product.DisplayName, product.Description, product.Color)
		button.Activated:Connect(function()
			buy(product.Id)
		end)
		table.insert(cards, {
			Button = button,
			Refresh = function()
				local state = State.Get()
				if state and product.Kind == "StarterPack" and state.StarterPackBought then
					return "OWNED", Theme.Disabled
				end
				if state and product.Kind == "Trophy" and product.Trophy and state.Trophies[product.Trophy] then
					return "OWNED", Theme.Disabled
				end
				return `{ROBUX} {product.Robux}`, Theme.Good
			end,
		})
	end

	local order = 0
	for _, trophy in Shop.Trophies do
		order += 1
		local how = if trophy.Points
			then `{trophy.Rarity} · shows on your island`
			else `{trophy.Rarity} · from the shop, VIP, streak or starter pack`
		local button = card(tabs.TROPHIES, order, trophy.DisplayName, how, trophy.Color, "🏆")
		if trophy.Points then
			button.Activated:Connect(function()
				buy(`Trophy_{trophy.Id}`)
			end)
		end
		table.insert(cards, {
			Button = button,
			Refresh = function()
				local state = State.Get()
				if state and state.Trophies[trophy.Id] then
					return "OWNED", Theme.Disabled
				end
				if trophy.Points then
					local canBuy = state ~= nil and state.BonkPoints >= trophy.Points
					return Format.Money(trophy.Points), if canBuy then Theme.Good else Theme.CardLight
				end
				return "EXCLUSIVE", Theme.CardLight
			end,
		})
	end

	panel.OnOpen = function()
		ShopController.Refresh()
	end
	showTab(currentTab)
end

function ShopController.Refresh()
	for _, entry in cards do
		local text, color, textColor = entry.Refresh()
		entry.Button.TextColor3 = textColor or Theme.Text
		-- Bonk Dollars prices ("B$ 5,000") show the symbol.
		Widgets.SetMoneyText(entry.Button, text)
		Widgets.SetButtonColor(entry.Button, color)
	end
end

-- Opens the shop (if it isn't open) on a tab: "POWERS", "PASSES", "ITEMS" or "TROPHIES".
function ShopController.OpenTab(name: string)
	if not Widgets.IsOpen("Shop") then
		Widgets.Open("Shop")
	end
	showTab(name)
end

-- Starter pack popup: once per session for players who joined within OfferHours and haven't bought it.
local function showOffer()
	local state = State.Get()
	if offerShown or not state or state.StarterPackBought then
		return
	end
	local endsAt = state.FirstJoinAt + Shop.StarterPack.OfferHours * 3600
	if Workspace:GetServerTimeNow() >= endsAt then
		return
	end
	offerShown = true
	local product = Shop.GetProduct("StarterPack")
	if not product then
		return
	end
	local gui = Widgets.Screen("StarterOffer", 30)
	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.5)
	frame.Size = UDim2.fromOffset(420, 300)
	frame.BackgroundColor3 = Theme.Panel
	frame.Parent = gui
	Widgets.Corner(frame, 16)
	Widgets.Stroke(frame, 4, product.Color)
	local title = Widgets.Label(frame, "STARTER PACK", 34, product.Color)
	title.Position = UDim2.fromOffset(0, 12)
	title.Size = UDim2.new(1, 0, 0, 40)
	title.TextXAlignment = Enum.TextXAlignment.Center
	local text = Widgets.Label(frame, product.Description, 20)
	text.Position = UDim2.fromOffset(20, 60)
	text.Size = UDim2.new(1, -40, 0, 80)
	text.TextWrapped = true
	text.TextXAlignment = Enum.TextXAlignment.Center
	local timer = Widgets.Label(frame, "", 18, Theme.Bad)
	timer.Position = UDim2.fromOffset(0, 146)
	timer.Size = UDim2.new(1, 0, 0, 24)
	timer.TextXAlignment = Enum.TextXAlignment.Center
	local buyButton = Widgets.Button(frame, `BUY  {ROBUX} {product.Robux}`, Theme.Good, 24)
	buyButton.AnchorPoint = Vector2.new(0.5, 0)
	buyButton.Position = UDim2.new(0.5, 0, 0, 180)
	buyButton.Size = UDim2.fromOffset(260, 54)
	buyButton.Activated:Connect(function()
		buy(product.Id)
		gui:Destroy()
	end)
	local later = Widgets.Button(frame, "Maybe later", Theme.CardLight, 16)
	later.AnchorPoint = Vector2.new(0.5, 0)
	later.Position = UDim2.new(0.5, 0, 0, 244)
	later.Size = UDim2.fromOffset(160, 36)
	later.Activated:Connect(function()
		gui:Destroy()
	end)
	task.spawn(function()
		while gui.Parent do
			timer.Text = `Offer ends in {Widgets.Duration(endsAt - Workspace:GetServerTimeNow())}`
			task.wait(1)
		end
	end)
end

function ShopController.Init()
	build()
end

function ShopController.Start()
	State.Changed:Connect(ShopController.Refresh)
	ShopController.Refresh()
	-- Give new players a moment to look around before the offer pops up.
	task.delay(20, showOffer)
end

return ShopController
