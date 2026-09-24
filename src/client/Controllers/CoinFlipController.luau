--!strict
-- Coin flip menu (Config/Hub → CoinFlip, Duel): bet against the house, or challenge another player in this server
-- to a duel for a fixed stake. Also shows incoming duel invites. The server decides every flip; the coin animation
-- only plays the result.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Net = require(ReplicatedStorage.Shared.Net)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local FLIP = Hub.CoinFlip
local DUEL = Hub.Duel
local GOLD = Color3.fromRGB(255, 200, 40)
local SILVER = Color3.fromRGB(200, 205, 220)

local player = Players.LocalPlayer

local side: "Heads" | "Tails" = "Heads"
local stake = DUEL.Stakes[1]
local flipping = false

local coin: TextLabel
local resultLabel: TextLabel
local sideButtons: { [string]: TextButton } = {}
local betButtons: { TextButton } = {}
local stakeButtons: { TextButton } = {}
local playerList: ScrollingFrame

local CoinFlipController = {}

-- Spins the coin (squashing it flat and back a few times) and lands on `result`.
local function animate(result: "Heads" | "Tails", onDone: () -> ())
	flipping = true
	resultLabel.Text = ""
	local flips = 7
	local duration = FLIP.FlipTime / (flips * 2)
	task.spawn(function()
		for index = 1, flips do
			TweenService:Create(coin, TweenInfo.new(duration), { Size = UDim2.fromOffset(4, 120) }):Play()
			task.wait(duration)
			local showing = if index == flips then result elseif index % 2 == 0 then "Heads" else "Tails"
			coin.Text = if showing == "Heads" then "H" else "T"
			coin.BackgroundColor3 = if showing == "Heads" then GOLD else SILVER
			TweenService:Create(coin, TweenInfo.new(duration), { Size = UDim2.fromOffset(120, 120) }):Play()
			task.wait(duration)
		end
		flipping = false
		onDone()
	end)
end

local function refreshChoices()
	for name, button in sideButtons do
		Widgets.SetButtonColor(button, if name == side then Theme.Info else Theme.CardLight)
	end
	for index, button in stakeButtons do
		Widgets.SetButtonColor(button, if DUEL.Stakes[index] == stake then Theme.Info else Theme.CardLight)
	end
	local state = State.Get()
	local points = if state then state.BonkPoints else 0
	for index, button in betButtons do
		local fraction = FLIP.BetFractions[index]
		local label = if fraction == 1 then "ALL" else `{math.floor(fraction * 100)}%`
		button.Text = `{label}\n{Format.Number(math.floor(points * fraction))}`
	end
end

local function refreshPlayers()
	for _, child in playerList:GetChildren() do
		if child:IsA("Frame") then
			child:Destroy()
		end
	end
	local others = 0
	for _, other in Players:GetPlayers() do
		if other == player then
			continue
		end
		others += 1
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, 0, 0, 40)
		row.BackgroundColor3 = Theme.CardLight
		row.Parent = playerList
		Widgets.Corner(row, 8)
		local name = Widgets.Label(row, other.DisplayName, 18)
		name.Position = UDim2.fromOffset(10, 0)
		name.Size = UDim2.new(1, -120, 1, 0)
		local duel = Widgets.Button(row, "DUEL", Color3.fromRGB(255, 120, 40), 18)
		duel.AnchorPoint = Vector2.new(1, 0.5)
		duel.Position = UDim2.new(1, -6, 0.5, 0)
		duel.Size = UDim2.fromOffset(96, 32)
		duel.Activated:Connect(function()
			Net.Get(Net.DuelChallenge):FireServer(other.UserId, stake)
		end)
	end
	if others == 0 then
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, 0, 0, 40)
		row.BackgroundTransparency = 1
		row.Parent = playerList
		local empty = Widgets.Label(row, "No other players here yet", 16, Theme.Muted)
		empty.Size = UDim2.fromScale(1, 1)
		empty.TextXAlignment = Enum.TextXAlignment.Center
	end
end

local function build()
	local panel = Widgets.Panel("CoinFlip", "COIN FLIP", Vector2.new(620, 600), Color3.fromRGB(255, 150, 40))
	local content = panel.Content

	-- Left: against the house.
	local house = Instance.new("Frame")
	house.Size = UDim2.new(0.5, -6, 1, 0)
	house.BackgroundColor3 = Theme.Card
	house.Parent = content
	Widgets.Corner(house, 12)
	local houseTitle = Widgets.Label(house, "VS HOUSE · double or nothing", 17, Theme.Accent)
	houseTitle.Position = UDim2.fromOffset(12, 6)
	houseTitle.Size = UDim2.new(1, -24, 0, 26)

	coin = Widgets.Label(house, "H", 64, Color3.fromRGB(110, 70, 0))
	coin.AnchorPoint = Vector2.new(0.5, 0.5)
	coin.Position = UDim2.new(0.5, 0, 0, 110)
	coin.Size = UDim2.fromOffset(120, 120)
	coin.BackgroundTransparency = 0
	coin.BackgroundColor3 = GOLD
	coin.TextXAlignment = Enum.TextXAlignment.Center
	Widgets.Corner(coin, 60)
	Widgets.Stroke(coin, 4, Color3.fromRGB(150, 100, 0))

	resultLabel = Widgets.Label(house, "", 20, Theme.Text)
	resultLabel.Position = UDim2.fromOffset(8, 176)
	resultLabel.Size = UDim2.new(1, -16, 0, 26)
	resultLabel.TextXAlignment = Enum.TextXAlignment.Center

	for index, name in { "Heads", "Tails" } do
		local button = Widgets.Button(house, string.upper(name), Theme.CardLight, 18)
		button.Position = UDim2.new((index - 1) * 0.5, if index == 1 then 10 else 4, 0, 212)
		button.Size = UDim2.new(0.5, -14, 0, 40)
		button.Activated:Connect(function()
			side = name :: "Heads" | "Tails"
			refreshChoices()
		end)
		sideButtons[name] = button
	end

	local betTitle = Widgets.Label(house, "Bet (tap to flip):", 15, Theme.Muted)
	betTitle.Position = UDim2.fromOffset(12, 258)
	betTitle.Size = UDim2.new(1, -24, 0, 20)
	for index, fraction in FLIP.BetFractions do
		local column = (index - 1) % 2
		local rowIndex = (index - 1) // 2
		local button = Widgets.Button(house, "", Theme.Good, 16)
		button.Position = UDim2.new(column * 0.5, if column == 0 then 10 else 4, 0, 282 + rowIndex * 62)
		button.Size = UDim2.new(0.5, -14, 0, 54)
		button.Activated:Connect(function()
			if not flipping then
				Net.Get(Net.CoinFlip):FireServer(fraction, side)
			end
		end)
		table.insert(betButtons, button)
	end

	-- Right: duels.
	local duels = Instance.new("Frame")
	duels.AnchorPoint = Vector2.new(1, 0)
	duels.Position = UDim2.fromScale(1, 0)
	duels.Size = UDim2.new(0.5, -6, 1, 0)
	duels.BackgroundColor3 = Theme.Card
	duels.Parent = content
	Widgets.Corner(duels, 12)
	local duelTitle = Widgets.Label(duels, "DUEL · winner takes both", 17, Theme.Accent)
	duelTitle.Position = UDim2.fromOffset(12, 6)
	duelTitle.Size = UDim2.new(1, -24, 0, 26)
	local stakeTitle = Widgets.Label(duels, "Stake:", 15, Theme.Muted)
	stakeTitle.Position = UDim2.fromOffset(12, 36)
	stakeTitle.Size = UDim2.new(1, -24, 0, 20)
	for index, amount in DUEL.Stakes do
		local column = (index - 1) % 2
		local rowIndex = (index - 1) // 2
		local button = Widgets.Button(duels, Format.Number(amount), Theme.CardLight, 16)
		button.Position = UDim2.new(column * 0.5, if column == 0 then 10 else 4, 0, 60 + rowIndex * 44)
		button.Size = UDim2.new(0.5, -14, 0, 38)
		button.Activated:Connect(function()
			stake = amount
			refreshChoices()
		end)
		table.insert(stakeButtons, button)
	end
	local listHolder = Instance.new("Frame")
	listHolder.Position = UDim2.fromOffset(10, 156)
	listHolder.Size = UDim2.new(1, -20, 1, -166)
	listHolder.BackgroundTransparency = 1
	listHolder.Parent = duels
	playerList = Widgets.List(listHolder, 6)

	panel.OnOpen = function()
		refreshChoices()
		refreshPlayers()
	end
end

-- "X challenges you" popup with accept/decline, closes itself after the invite timeout.
local function showInvite(duelId: number, challenger: string, amount: number)
	local gui = Widgets.Screen("DuelInvite", 20)
	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(0.5, 0)
	frame.Position = UDim2.new(0.5, 0, 0, 110)
	frame.Size = UDim2.fromOffset(440, 130)
	frame.BackgroundColor3 = Theme.Panel
	frame.Parent = gui
	Widgets.Corner(frame, 14)
	Widgets.Stroke(frame, 3, Color3.fromRGB(255, 120, 40))
	local text = Widgets.Label(frame, `{challenger} challenges you to a coin flip for {Format.Number(amount)}!`, 20)
	text.Position = UDim2.fromOffset(14, 8)
	text.Size = UDim2.new(1, -28, 0, 56)
	text.TextWrapped = true
	text.TextXAlignment = Enum.TextXAlignment.Center
	local function answer(accept: boolean)
		Net.Get(Net.DuelRespond):FireServer(duelId, accept)
		gui:Destroy()
	end
	local accept = Widgets.Button(frame, "ACCEPT", Theme.Good, 20)
	accept.Position = UDim2.new(0, 14, 1, -56)
	accept.Size = UDim2.new(0.5, -20, 0, 44)
	accept.Activated:Connect(function()
		answer(true)
	end)
	local decline = Widgets.Button(frame, "DECLINE", Theme.Bad, 20)
	decline.Position = UDim2.new(0.5, 6, 1, -56)
	decline.Size = UDim2.new(0.5, -20, 0, 44)
	decline.Activated:Connect(function()
		answer(false)
	end)
	task.delay(DUEL.InviteTimeout, function()
		if gui.Parent then
			gui:Destroy()
		end
	end)
end

function CoinFlipController.Init()
	build()
end

function CoinFlipController.Start()
	State.Changed:Connect(refreshChoices)
	Players.PlayerAdded:Connect(refreshPlayers)
	Players.PlayerRemoving:Connect(function()
		task.defer(refreshPlayers)
	end)
	Net.Get(Net.CoinFlipResult).OnClientEvent:Connect(function(won: boolean, result: "Heads" | "Tails", amount: number)
		animate(result, function()
			resultLabel.Text = if won then `WON +{Format.Number(amount)}!` else `Lost {Format.Number(amount)}`
			resultLabel.TextColor3 = if won then Theme.Good else Theme.Bad
		end)
	end)
	Net.Get(Net.DuelInvite).OnClientEvent:Connect(showInvite)
	Net.Get(Net.DuelResult).OnClientEvent
		:Connect(function(won: boolean, opponent: string, amount: number, result: "Heads" | "Tails")
			Widgets.Open("CoinFlip")
			animate(result, function()
				resultLabel.Text = if won
					then `Beat {opponent}! +{Format.Number(amount)}`
					else `{opponent} won {Format.Number(amount)}`
				resultLabel.TextColor3 = if won then Theme.Good else Theme.Bad
			end)
		end)
end

return CoinFlipController
