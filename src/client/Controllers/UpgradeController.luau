--!strict
-- The upgrade menu: one card per upgrade (Config/Upgrades) with its level progress, what the next level gives,
-- and a buy button. The "More Shibas" card also sets how many of your Shibas are active. Purchases are validated
-- on the server; this only shows the state the server sent.
-- Opening it anywhere needs the Manage pass (the HUD clipboard button); without it the shop opens on the pass
-- instead. Upgrades are normally bought at the stands on the island.
-- Upgrades that unlock with a later Shiba (EconomyConfig.UnlockAtShibaTier: basket, intern …) show as LOCKED with the
-- Shiba they need (the server refuses them too). At the bottom a REBIRTH card shows the rebirth count, the income
-- multiplier, what the next rebirth needs and gives (rebirthing itself happens at the shrine on the island).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local ShopController = require(script.Parent.ShopController)
local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local CARD_HEIGHT = 128
-- More levels than this: the dots share the row width instead of a fixed size (Shiba Tier has 29).
local FIXED_DOTS_UP_TO = 10
local AUTOMATION = EconomyConfig.Automation
local REBIRTH = EconomyConfig.Rebirth
local LOCKED_COLOR = Color3.fromRGB(140, 140, 150)

type RebirthCard = {
	Count: TextLabel,
	Need: TextLabel,
	Status: TextLabel,
}

local rebirthCard: RebirthCard? = nil

type Card = {
	Id: string,
	Level: TextLabel,
	Value: TextLabel,
	Detail: TextLabel,
	Dots: { Frame },
	Button: TextButton,
	CanBuy: boolean,
	ActiveLabel: TextLabel?,
}

local cards: { Card } = {}

local UpgradeController = {}

-- What a level gives, in words (shown under the name).
local function percent(share: number): string
	return `{math.floor(share * 100 + 0.5)}%`
end

local function describe(id: string, level: number): string
	if id == "ShooterTier" then
		local tier = Gameplay.Shooters.Tiers[level + 1]
		return string.format(
			"throws every %.1fs · ×%s dollars",
			tier.FireInterval,
			Format.Short(tier.RewardMultiplier)
		)
	elseif id == "ProjectileTier" then
		return `{Format.Money(Projectiles.ForTier(level).BaseReward)} per bonk`
	elseif id == "Shooters" then
		local count = Upgrades.GetValue(id, level)
		return `{count} Shiba{if count == 1 then "" else "s"} around your island`
	elseif id == "Basket" then
		if level <= 0 then
			return "no basket yet"
		end
		local basket = AUTOMATION.Basket
		return `catches {percent(basket.CatchChance[level])} of missed · pays {percent(basket.Payout[level])} · offline {basket.OfflineHours[level]} h`
	elseif id == "Intern" then
		if level <= 0 then
			return "no intern yet"
		end
		local intern = AUTOMATION.Intern
		return `runs at speed {intern.WalkSpeed[level]} · pays {percent(intern.Payout[level])} per stick`
	end
	return `WalkSpeed {Upgrades.GetValue(id, level)}`
end

-- The Shiba tier level an upgrade needs before it can be bought (0 = from the start).
local function unlockTier(id: string): number
	return EconomyConfig.UnlockAtShibaTier[id] or 0
end

local function valueColor(id: string, level: number): Color3
	local def = Upgrades.Defs[id]
	return if def.ValueColors then def.ValueColors[level + 1] or Theme.Text else Theme.Text
end

local function buildCard(list: Instance, id: string, order: number)
	local def = Upgrades.Defs[id]
	local requestPurchase = Net.Get(Net.RequestPurchase)

	local frame = Instance.new("Frame")
	frame.Name = id
	frame.LayoutOrder = order
	frame.Size = UDim2.new(1, 0, 0, CARD_HEIGHT)
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = list
	Widgets.Corner(frame, 12)
	Widgets.Stroke(frame, 2)

	-- Coloured badge with the level on the left.
	local icon = Instance.new("Frame")
	icon.Position = UDim2.fromOffset(12, 12)
	icon.Size = UDim2.fromOffset(78, 78)
	icon.BackgroundColor3 = Color3.new(1, 1, 1)
	icon.Parent = frame
	Widgets.Corner(icon, 39)
	Widgets.Stroke(icon, 3)
	Widgets.Gradient(icon, def.Color)
	local levelLabel = Widgets.Label(icon, "", 22)
	levelLabel.Size = UDim2.fromScale(1, 1)
	levelLabel.TextXAlignment = Enum.TextXAlignment.Center
	levelLabel.TextStrokeTransparency = 0.3

	local name = Widgets.Label(frame, def.DisplayName, 24)
	name.Position = UDim2.fromOffset(104, 8)
	name.Size = UDim2.new(1, -250, 0, 28)

	local value = Widgets.Label(frame, "", 18, Theme.Accent)
	value.Position = UDim2.fromOffset(104, 36)
	value.Size = UDim2.new(1, -250, 0, 22)
	value.RichText = true

	local detail = Widgets.Label(frame, "", 14, Theme.Muted)
	detail.Font = Theme.BodyFont
	detail.Position = UDim2.fromOffset(104, 58)
	detail.Size = UDim2.new(1, -250, 0, 18)
	detail.TextTruncate = Enum.TextTruncate.AtEnd

	-- One dot per level (tiers show their colours).
	local dotRow = Instance.new("Frame")
	dotRow.Position = UDim2.fromOffset(104, 84)
	dotRow.Size = UDim2.new(1, -250, 0, 14)
	dotRow.BackgroundTransparency = 1
	dotRow.Parent = frame
	local dotLayout = Instance.new("UIListLayout")
	dotLayout.FillDirection = Enum.FillDirection.Horizontal
	dotLayout.Padding = UDim.new(0, 5)
	dotLayout.Parent = dotRow
	local dots: { Frame } = {}
	-- Dots up to the highest level any player can reach (More Shibas: +2 with the pass; extra dots hide without it).
	local dotCount = Upgrades.GetMaxLevel(id, { ExtraShibas = true })
	if dotCount > FIXED_DOTS_UP_TO then
		dotLayout.Padding = UDim.new(0, 2)
	end
	for level = 1, dotCount do
		local dot = Instance.new("Frame")
		dot.Size = if dotCount > FIXED_DOTS_UP_TO
			then UDim2.new(1 / dotCount, -2, 0, 12)
			else UDim2.fromOffset(if dotCount > 8 then 16 else 26, 12)
		dot.BackgroundColor3 = valueColor(id, level)
		dot.Parent = dotRow
		Widgets.Corner(dot, 6)
		Widgets.Stroke(dot, 1)
		table.insert(dots, dot)
	end

	local description = Widgets.Label(frame, def.Description, 13, Theme.Muted)
	description.Font = Theme.BodyFont
	description.Position = UDim2.fromOffset(12, 102)
	description.Size = UDim2.new(1, -170, 0, 18)
	description.TextTruncate = Enum.TextTruncate.AtEnd

	local button = Widgets.Button(frame, "", Theme.Disabled, 22)
	button.AnchorPoint = Vector2.new(1, 0)
	button.Position = UDim2.new(1, -12, 0, 14)
	button.Size = UDim2.fromOffset(130, 56)

	local card: Card = {
		Id = id,
		Level = levelLabel,
		Value = value,
		Detail = detail,
		Dots = dots,
		Button = button,
		CanBuy = false,
	}
	button.Activated:Connect(function()
		if card.CanBuy then
			requestPurchase:FireServer(id)
		end
	end)

	if id == "Shooters" then
		-- Active Shibas: − n/m +
		local setActive = Net.Get(Net.SetActiveShooters)
		local minus = Widgets.Button(frame, "−", Theme.CardLight, 22)
		minus.AnchorPoint = Vector2.new(1, 0)
		minus.Position = UDim2.new(1, -106, 0, 80)
		minus.Size = UDim2.fromOffset(34, 34)
		local active = Widgets.Label(frame, "", 16, Theme.Text)
		active.AnchorPoint = Vector2.new(1, 0)
		active.Position = UDim2.new(1, -46, 0, 80)
		active.Size = UDim2.fromOffset(60, 34)
		active.TextXAlignment = Enum.TextXAlignment.Center
		local plus = Widgets.Button(frame, "+", Theme.CardLight, 22)
		plus.AnchorPoint = Vector2.new(1, 0)
		plus.Position = UDim2.new(1, -12, 0, 80)
		plus.Size = UDim2.fromOffset(34, 34)
		card.ActiveLabel = active
		minus.Activated:Connect(function()
			local state = State.Get()
			if state and state.ActiveShooters > 1 then
				setActive:FireServer(state.ActiveShooters - 1)
			end
		end)
		plus.Activated:Connect(function()
			local state = State.Get()
			if state and state.ActiveShooters < Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters or 0) then
				setActive:FireServer(state.ActiveShooters + 1)
			end
		end)
		description.Size = UDim2.new(1, -250, 0, 18)
	end

	table.insert(cards, card)
end

-- The REBIRTH card: rebirths so far and the income multiplier, what the next rebirth needs and gives, and where to
-- do it. Info only: the rebirth itself happens at the shrine on the island (RebirthService.TryRebirth).
local function buildRebirthCard(list: Instance, order: number)
	local color = Color3.fromRGB(255, 120, 200)
	local frame = Instance.new("Frame")
	frame.Name = "Rebirth"
	frame.LayoutOrder = order
	frame.Size = UDim2.new(1, 0, 0, CARD_HEIGHT)
	frame.BackgroundColor3 = Theme.Card
	frame.Parent = list
	Widgets.Corner(frame, 12)
	Widgets.Stroke(frame, 3, color)

	local icon = Instance.new("Frame")
	icon.Position = UDim2.fromOffset(12, 12)
	icon.Size = UDim2.fromOffset(78, 78)
	icon.BackgroundColor3 = Color3.new(1, 1, 1)
	icon.Parent = frame
	Widgets.Corner(icon, 39)
	Widgets.Stroke(icon, 3)
	Widgets.Gradient(icon, color)
	local count = Widgets.Label(icon, "", 22)
	count.Size = UDim2.fromScale(1, 1)
	count.TextXAlignment = Enum.TextXAlignment.Center
	count.TextStrokeTransparency = 0.3

	local name = Widgets.Label(frame, "REBIRTH", 24, color)
	name.Position = UDim2.fromOffset(104, 8)
	name.Size = UDim2.new(1, -250, 0, 28)

	local need = Widgets.Label(frame, "", 16, Theme.Accent)
	need.Position = UDim2.fromOffset(104, 38)
	need.Size = UDim2.new(1, -116, 0, 40)
	need.TextWrapped = true
	need.TextYAlignment = Enum.TextYAlignment.Top

	local description = Widgets.Label(
		frame,
		"Resets Bonk Dollars and all upgrades; keeps passes, trophies and the Shiba-Index.",
		13,
		Theme.Muted
	)
	description.Font = Theme.BodyFont
	description.Position = UDim2.fromOffset(12, 102)
	description.Size = UDim2.new(1, -24, 0, 18)
	description.TextTruncate = Enum.TextTruncate.AtEnd

	local status = Widgets.Label(frame, "", 18)
	status.AnchorPoint = Vector2.new(1, 0)
	status.Position = UDim2.new(1, -12, 0, 8)
	status.Size = UDim2.fromOffset(240, 28)
	status.TextXAlignment = Enum.TextXAlignment.Right

	rebirthCard = { Count = count, Need = need, Status = status }
end

local function refreshRebirth(state: Types.PlayerState)
	local card = rebirthCard
	if not card then
		return
	end
	local needed = EconomyConfig.Shibas[REBIRTH.MinShibaTier + 1]
	local now = EconomyConfig.RebirthMultiplier(state.Rebirths)
	local nextMultiplier = EconomyConfig.RebirthMultiplier(state.Rebirths + 1)
	card.Count.Text = `×{now}`
	local ready = (state.UpgradeLevels.ShooterTier or 0) >= REBIRTH.MinShibaTier
	card.Need.Text =
		`Rebirths: {state.Rebirths} · income ×{now}\nNeeds the {needed.Name} (Shiba {REBIRTH.MinShibaTier + 1}) · next: income ×{nextMultiplier}`
	card.Status.Text = if ready then "READY! Go to the shrine" else "not yet"
	card.Status.TextColor3 = if ready then Theme.Good else Theme.Muted
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	for _, card in cards do
		local id = card.Id
		local level = state.UpgradeLevels[id] or 0
		local maxLevel = Upgrades.GetMaxLevel(id, state.Passes)
		card.Level.Text = if level >= maxLevel then "MAX" else `Lv {level}`
		local current = Upgrades.FormatValue(id, level)
		local currentColor = valueColor(id, level):ToHex()
		local needTier = unlockTier(id)
		if (state.UpgradeLevels.ShooterTier or 0) < needTier then
			-- Locked until the player owns the Shiba it comes with.
			local shiba = EconomyConfig.Shibas[needTier + 1]
			card.Level.Text = "🔒"
			card.Value.Text = `<font color="#{LOCKED_COLOR:ToHex()}">LOCKED</font>`
			Widgets.SetMoneyText(card.Detail, `Unlocks with {shiba.Name}`)
			Widgets.SetMoneyText(card.Button, "LOCKED")
			card.CanBuy = false
			Widgets.SetButtonColor(card.Button, Theme.Disabled)
		elseif level >= maxLevel then
			card.Value.Text = `<font color="#{currentColor}">{current}</font>`
			Widgets.SetMoneyText(card.Detail, describe(id, level))
			Widgets.SetMoneyText(card.Button, "MAX")
			card.CanBuy = false
			Widgets.SetButtonColor(card.Button, Theme.Accent)
		else
			local nextText = Upgrades.FormatValue(id, level + 1)
			local nextColor = valueColor(id, level + 1):ToHex()
			card.Value.Text =
				`<font color="#{currentColor}">{current}</font>  →  <font color="#{nextColor}">{nextText}</font>`
			Widgets.SetMoneyText(card.Detail, `Next: {describe(id, level + 1)}`)
			local cost = Upgrades.GetCost(id, level)
			Widgets.SetMoneyText(card.Button, Format.MoneyShort(cost))
			card.CanBuy = state.BonkPoints >= cost
			Widgets.SetButtonColor(card.Button, if card.CanBuy then Theme.Good else Theme.Disabled)
		end
		for index, dot in card.Dots do
			dot.Visible = index <= maxLevel
			dot.BackgroundTransparency = if index <= level then 0 else 0.75
		end
		if card.ActiveLabel then
			card.ActiveLabel.Text = `{state.ActiveShooters}/{Upgrades.GetValue("Shooters", level)} on`
		end
	end
	refreshRebirth(state)
end

-- The shop on its POWERS tab (Manage and other time savers). ShopController.OpenTab is added by the shop
-- feature; until it exists the shop opens on its first tab.
function UpgradeController.OpenPowers()
	-- Cast: OpenTab is optional (not in every version of ShopController), so its key may be missing from the type.
	local shop = ShopController :: any
	if shop.OpenTab then
		shop.OpenTab("POWERS")
	else
		Widgets.Open("Shop")
	end
end

-- The HUD clipboard button: the upgrade menu with the Manage pass, else the shop to buy it.
function UpgradeController.OpenManage()
	local state = State.Get()
	if state and state.Passes.Manage then
		Widgets.Open("Upgrades")
	else
		UpgradeController.OpenPowers()
	end
end

function UpgradeController.Init()
	local panel = Widgets.Panel("Upgrades", "MANAGE", Vector2.new(640, 600), Color3.fromRGB(255, 190, 60))
	local list = Widgets.List(panel.Content, 10)
	for index, id in Upgrades.Order do
		buildCard(list, id, index)
	end
	buildRebirthCard(list, #Upgrades.Order + 1)
	panel.OnOpen = function()
		local state = State.Get()
		if not (state and state.Passes.Manage) then
			-- Locked: show where to get the pass instead.
			UpgradeController.OpenPowers()
			return
		end
		refresh()
	end
end

function UpgradeController.Start()
	State.Changed:Connect(refresh)
	refresh()
end

return UpgradeController
