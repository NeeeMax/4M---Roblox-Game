--!strict
-- Admin menu (only built for admins, Config/Admin): testing shortcuts. Every button sends AdminCommand; the server
-- checks admin rights again (AdminService). "RESET EVERYTHING" needs a second click to confirm.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Admin = require(ReplicatedStorage.Shared.Config.Admin)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local levelLabels: { [string]: TextLabel } = {}
-- Pass toggle buttons show green while the pass is on.
local passButtonsById: { [string]: TextButton } = {}
-- "Rebirths: 2 · income ×3" in the rebirth section.
local rebirthInfo: TextLabel? = nil
-- Shiba Variants tools: the slot the variant buttons act on, and its "Slot 3: Rainbow" label.
local variantSlot = 1
local variantSlotLabel: TextLabel? = nil

local AdminController = {}

local function refreshVariantSlot()
	local label = variantSlotLabel
	if not label then
		return
	end
	local state = State.Get()
	local variant = if state then state.Variants.Slots[tostring(variantSlot)] or "Normal" else "Normal"
	label.Text = `Slot {variantSlot}: {variant}`
end

local function send(command: string, argument: (string | number)?)
	Net.Get(Net.AdminCommand):FireServer(command, argument)
end

local function section(list: Instance, title: string, order: number): Frame
	local frame = Instance.new("Frame")
	frame.LayoutOrder = order
	frame.Size = UDim2.fromScale(1, 0)
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = list
	Widgets.Corner(frame, 10)
	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 8)
	padding.PaddingBottom = UDim.new(0, 10)
	padding.PaddingLeft = UDim.new(0, 10)
	padding.PaddingRight = UDim.new(0, 10)
	padding.Parent = frame
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = frame
	local label = Widgets.Label(frame, title, 18, Theme.Muted)
	label.Size = UDim2.new(1, 0, 0, 20)
	label.LayoutOrder = 0
	return frame
end

-- A row of equally wide buttons.
local function buttonRow(parent: Instance, order: number, buttons: { { string } }, color: Color3): { TextButton }
	local row = Instance.new("Frame")
	row.LayoutOrder = order
	row.Size = UDim2.new(1, 0, 0, 40)
	row.BackgroundTransparency = 1
	row.Parent = parent
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 6)
	layout.Parent = row
	local created: { TextButton } = {}
	for _, entry in buttons do
		local button = Widgets.Button(row, entry[1], color, 16)
		button.Size = UDim2.new(1 / #buttons, -6, 1, 0)
		table.insert(created, button)
	end
	return created
end

local function build()
	local panel = Widgets.Panel("Admin", "ADMIN", Vector2.new(560, 620), Theme.Admin)
	local list = Widgets.List(panel.Content, 10)

	local points = section(list, Format.CurrencyName, 1)
	-- "+1K" … "+1Dc", PointButtonsPerRow per row.
	local rows = math.ceil(#Admin.PointAmounts / Admin.PointButtonsPerRow)
	for row = 1, rows do
		local amounts: { { string } } = {}
		local first = (row - 1) * Admin.PointButtonsPerRow
		for index = first + 1, math.min(first + Admin.PointButtonsPerRow, #Admin.PointAmounts) do
			table.insert(amounts, { `+{Format.Short(Admin.PointAmounts[index])}` })
		end
		for offset, button in buttonRow(points, row, amounts, Theme.Good) do
			local amount = Admin.PointAmounts[first + offset]
			button.Activated:Connect(function()
				send("AddPoints", amount)
			end)
		end
	end
	buttonRow(points, rows + 1, { { "Set to 0" } }, Theme.Disabled)[1].Activated:Connect(function()
		send("ClearPoints")
	end)

	local upgrades = section(list, "Upgrades", 2)
	for index, id in Upgrades.Order do
		local row = Instance.new("Frame")
		row.LayoutOrder = index
		row.Size = UDim2.new(1, 0, 0, 36)
		row.BackgroundTransparency = 1
		row.Parent = upgrades
		local name = Widgets.Label(row, Upgrades.Defs[id].DisplayName, 18)
		name.Size = UDim2.new(1, -200, 1, 0)
		local level = Widgets.Label(row, "", 16, Theme.Accent)
		level.AnchorPoint = Vector2.new(1, 0)
		level.Position = UDim2.new(1, -90, 0, 0)
		level.Size = UDim2.fromOffset(110, 36)
		level.TextXAlignment = Enum.TextXAlignment.Right
		levelLabels[id] = level
		local minus = Widgets.Button(row, "−", Theme.CardLight, 20)
		minus.AnchorPoint = Vector2.new(1, 0)
		minus.Position = UDim2.new(1, -44, 0, 0)
		minus.Size = UDim2.fromOffset(38, 36)
		minus.Activated:Connect(function()
			send("UpgradeDown", id)
		end)
		local plus = Widgets.Button(row, "+", Theme.CardLight, 20)
		plus.AnchorPoint = Vector2.new(1, 0)
		plus.Position = UDim2.fromScale(1, 0)
		plus.Size = UDim2.fromOffset(38, 36)
		plus.Activated:Connect(function()
			send("UpgradeUp", id)
		end)
	end
	buttonRow(upgrades, #Upgrades.Order + 1, { { "MAX ALL" } }, Theme.Accent)[1].Activated:Connect(function()
		send("MaxUpgrades")
	end)

	-- Rebirth (RebirthService): count and multiplier, rebirth now (no Shiba needed), +1, back to 0.
	local rebirth = section(list, "Rebirth", 3)
	local rebirthLabel = Widgets.Label(rebirth, "", 16, Theme.Accent)
	rebirthLabel.LayoutOrder = 1
	rebirthLabel.Size = UDim2.new(1, 0, 0, 20)
	rebirthInfo = rebirthLabel
	local rebirthButtons = buttonRow(
		rebirth,
		2,
		{ { "Rebirth now" }, { "+1 rebirth" }, { "Reset rebirths" } },
		Color3.fromRGB(255, 120, 200)
	)
	rebirthButtons[1].Activated:Connect(function()
		send("RebirthNow")
	end)
	rebirthButtons[2].Activated:Connect(function()
		send("RebirthAdd")
	end)
	rebirthButtons[3].Activated:Connect(function()
		send("RebirthReset")
	end)

	local hub = section(list, "Daily spin · Quests", 4)
	local hubButtons = buttonRow(hub, 1, { { "Reset spin" }, { "New quests" }, { "Finish quests" } }, Theme.Info)
	hubButtons[1].Activated:Connect(function()
		send("ResetSpin")
	end)
	hubButtons[2].Activated:Connect(function()
		send("ResetQuests")
	end)
	hubButtons[3].Activated:Connect(function()
		send("CompleteQuests")
	end)

	local boosts = section(list, "Boosts (10 min)", 5)
	local boostButtons = buttonRow(
		boosts,
		1,
		{ { "2× Dollars" }, { "2× Fire rate" }, { "Magnet 5m" }, { "Clear" } },
		Color3.fromRGB(255, 170, 40)
	)
	boostButtons[1].Activated:Connect(function()
		send("BoostPoints")
	end)
	boostButtons[2].Activated:Connect(function()
		send("BoostFireRate")
	end)
	boostButtons[3].Activated:Connect(function()
		send("BoostMagnet")
	end)
	boostButtons[4].Activated:Connect(function()
		send("ClearBoosts")
	end)

	local shop = section(list, "Shop · Gifts (Studio tests)", 6)
	local passButtons =
		buttonRow(shop, 1, { { "2× Dollars" }, { "VIP" }, { "Lucky" }, { "+2 Shibas" } }, Color3.fromRGB(70, 200, 120))
	for index, passId in { "DoublePoints", "VIP", "LuckySticks", "ExtraShibas" } do
		passButtons[index].Activated:Connect(function()
			send("TogglePass", passId)
		end)
		passButtonsById[passId] = passButtons[index]
	end
	-- POWERS passes (the magnet is a timed boost: Boosts → "Magnet 5m", Clear removes it).
	local powerButtons =
		buttonRow(shop, 2, { { "Manage" }, { "Run Faster" }, { "Stack" } }, Color3.fromRGB(70, 200, 120))
	for index, passId in { "Manage", "RunFaster", "StackUpgrade" } do
		powerButtons[index].Activated:Connect(function()
			send("TogglePass", passId)
		end)
		passButtonsById[passId] = powerButtons[index]
	end
	local shopButtons =
		buttonRow(shop, 3, { { "+1 Bonk Rain" }, { "Start rain" }, { "All trophies" } }, Color3.fromRGB(60, 170, 255))
	shopButtons[1].Activated:Connect(function()
		send("GiveRain")
	end)
	shopButtons[2].Activated:Connect(function()
		send("StartRain")
	end)
	shopButtons[3].Activated:Connect(function()
		send("AllTrophies")
	end)
	local giftButtons =
		buttonRow(shop, 4, { { "Unlock gifts" }, { "Starter offer again" } }, Color3.fromRGB(255, 110, 150))
	giftButtons[1].Activated:Connect(function()
		send("ResetGifts")
	end)
	giftButtons[2].Activated:Connect(function()
		send("ResetStarter")
	end)

	local world = section(list, "World", 7)
	local worldButtons =
		buttonRow(world, 1, { { "To hub" }, { "To my island" }, { "All Shibas fire" } }, Color3.fromRGB(120, 110, 220))
	worldButtons[1].Activated:Connect(function()
		send("TeleportHub")
	end)
	worldButtons[2].Activated:Connect(function()
		send("TeleportIsland")
	end)
	worldButtons[3].Activated:Connect(function()
		send("FireNow")
	end)

	local events = section(list, "Server events · Offline", 8)
	local eventIds = { "GoldenMinute", "MegaStick", "DoublePoints", "StickStorm" }
	local eventButtons =
		buttonRow(events, 1, { { "Golden" }, { "Mega" }, { "Double" }, { "Storm" } }, Color3.fromRGB(255, 170, 40))
	for index, eventId in eventIds do
		eventButtons[index].Activated:Connect(function()
			send("StartEvent", eventId)
		end)
	end
	local eventTools =
		buttonRow(events, 2, { { "Stop event" }, { "Simulate 1 h offline" } }, Color3.fromRGB(120, 110, 220))
	eventTools[1].Activated:Connect(function()
		send("StopEvent")
	end)
	eventTools[2].Activated:Connect(function()
		send("SimulateOffline")
	end)

	-- ==== Social + Bonk Party (feat/social-party) ====
	local social = section(list, "Bonk Party · Friends", 9)
	local partyButtons = buttonRow(
		social,
		1,
		{ { "Start party (10 min)" }, { "End party" }, { "Finish party quest" } },
		Color3.fromRGB(255, 90, 200)
	)
	partyButtons[1].Activated:Connect(function()
		send("StartParty")
	end)
	partyButtons[2].Activated:Connect(function()
		send("StopParty")
	end)
	partyButtons[3].Activated:Connect(function()
		send("CompletePartyQuest")
	end)
	local friendButtons = buttonRow(
		social,
		2,
		{ { "Pretend friend +1 (cycles 0-4)" }, { "Fake invite reward" } },
		Color3.fromRGB(255, 150, 60)
	)
	friendButtons[1].Activated:Connect(function()
		send("FakeFriend")
	end)
	friendButtons[2].Activated:Connect(function()
		send("FakeInvite")
	end)
	-- ==== end Social + Bonk Party ====
	-- ===== Shiba Variants (VariantService): pick a slot, force a variant on it, roll all, luck ×10, reset.
	local variants = section(list, "Shiba Variants", 10)
	local slotRow = Instance.new("Frame")
	slotRow.LayoutOrder = 1
	slotRow.Size = UDim2.new(1, 0, 0, 36)
	slotRow.BackgroundTransparency = 1
	slotRow.Parent = variants
	local slotLabel = Widgets.Label(slotRow, "", 18)
	slotLabel.Size = UDim2.new(1, -90, 1, 0)
	variantSlotLabel = slotLabel
	local slotMinus = Widgets.Button(slotRow, "−", Theme.CardLight, 20)
	slotMinus.AnchorPoint = Vector2.new(1, 0)
	slotMinus.Position = UDim2.new(1, -44, 0, 0)
	slotMinus.Size = UDim2.fromOffset(38, 36)
	local slotPlus = Widgets.Button(slotRow, "+", Theme.CardLight, 20)
	slotPlus.AnchorPoint = Vector2.new(1, 0)
	slotPlus.Position = UDim2.fromScale(1, 0)
	slotPlus.Size = UDim2.fromOffset(38, 36)
	slotMinus.Activated:Connect(function()
		variantSlot = math.max(1, variantSlot - 1)
		refreshVariantSlot()
	end)
	slotPlus.Activated:Connect(function()
		variantSlot = math.min(Admin.MaxVariantSlot, variantSlot + 1)
		refreshVariantSlot()
	end)
	local variantIds = { "Shiny", "Rainbow", "Huge", "Normal" }
	local setButtons =
		buttonRow(variants, 2, { { "Shiny" }, { "Rainbow" }, { "Huge" }, { "Normal" } }, Color3.fromRGB(255, 110, 210))
	for index, variantId in variantIds do
		setButtons[index].Activated:Connect(function()
			send("VariantSet", `{variantSlot}:{variantId}`)
		end)
	end
	local variantTools = buttonRow(
		variants,
		3,
		{ { "Roll all now" }, { `Luck ×{Admin.VariantLuck}` }, { "Reset variants" } },
		Color3.fromRGB(120, 110, 220)
	)
	variantTools[1].Activated:Connect(function()
		send("VariantRoll")
	end)
	variantTools[2].Activated:Connect(function()
		send("VariantLuck")
	end)
	variantTools[3].Activated:Connect(function()
		send("VariantReset")
	end)
	-- ===== end Shiba Variants

	local danger = section(list, "Danger zone", 10)
	local reset = buttonRow(danger, 1, { { "RESET EVERYTHING" } }, Theme.Bad)[1]
	local armedAt = 0
	reset.Activated:Connect(function()
		if os.clock() - armedAt < 3 then
			armedAt = 0
			reset.Text = "RESET EVERYTHING"
			send("ResetAll")
		else
			armedAt = os.clock()
			reset.Text = "CLICK AGAIN TO CONFIRM"
			task.delay(3, function()
				if os.clock() - armedAt >= 3 then
					reset.Text = "RESET EVERYTHING"
				end
			end)
		end
	end)
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	for passId, button in passButtonsById do
		Widgets.SetButtonColor(button, if state.Passes[passId] then Theme.Good else Theme.Disabled)
	end
	for id, label in levelLabels do
		local level = state.UpgradeLevels[id] or 0
		label.Text = `Lv {level}/{Upgrades.GetMaxLevel(id, state.Passes)}`
	end
	if rebirthInfo then
		rebirthInfo.Text = `Rebirths: {state.Rebirths} · income ×{EconomyConfig.RebirthMultiplier(state.Rebirths)}`
	end
	refreshVariantSlot()
end

function AdminController.Init()
	if Admin.IsAdmin(Players.LocalPlayer.UserId) then
		build()
	end
end

function AdminController.Start()
	State.Changed:Connect(refresh)
	refresh()
end

return AdminController
