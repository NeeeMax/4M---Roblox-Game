--!strict
-- "WELCOME BACK!" popup for the offline Shiba Bank (docs/GAME_DESIGN.md → Offline Shiba Bank).
-- Shows what the Shibas earned while the player was away (OfflineEarnings, or Bank.Pending in the state if that
-- event came before this controller listened). OKAY claims it (ClaimOffline false); DOUBLE IT! asks the server for the
-- "DoubleOffline" Robux purchase (ClaimOffline true). The popup closes once the server has paid (Bank.Pending = 0).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local FRAME_GREEN = Color3.fromRGB(120, 230, 110)
local MONEY_GREEN = Color3.fromRGB(70, 255, 90)
local OKAY_GREY = Color3.fromRGB(215, 215, 222)
local DOUBLE_GREEN = Color3.fromRGB(40, 215, 90)
-- If the Robux prompt is closed without buying, the DOUBLE button becomes usable again after this long.
local DOUBLE_RETRY_SECONDS = 2

local gui: ScreenGui? = nil
-- Pending amount the open popup shows (to spot when the server has paid it).
local shownAmount = 0
local shownThisSession = false

local WelcomeBackController = {}

local function close()
	if gui then
		gui:Destroy()
		gui = nil
	end
end

local function claim(double: boolean)
	Net.Get(Net.ClaimOffline):FireServer(double)
end

local function show(amount: number, seconds: number)
	if amount <= 0 then
		return
	end
	shownThisSession = true
	shownAmount = amount
	close()

	local screen = Widgets.Screen("WelcomeBack", 40)
	gui = screen

	-- Thick light-green frame around a dark inner panel.
	local outer = Instance.new("Frame")
	outer.AnchorPoint = Vector2.new(0.5, 0.5)
	outer.Position = UDim2.fromScale(0.5, 0.5)
	outer.Size = UDim2.fromOffset(560, 340)
	outer.BackgroundColor3 = Color3.new(1, 1, 1)
	outer.Parent = screen
	Widgets.Corner(outer, 26)
	Widgets.Stroke(outer, 3)
	Widgets.Gradient(outer, FRAME_GREEN)

	local inner = Instance.new("Frame")
	inner.Position = UDim2.fromOffset(16, 16)
	inner.Size = UDim2.new(1, -32, 1, -32)
	inner.BackgroundColor3 = Theme.Background
	inner.Parent = outer
	Widgets.Corner(inner, 18)

	local title = Widgets.Label(inner, "WELCOME BACK!", 44)
	title.Position = UDim2.fromOffset(0, 10)
	title.Size = UDim2.new(1, 0, 0, 50)
	title.TextXAlignment = Enum.TextXAlignment.Center
	title.TextStrokeTransparency = 0.2

	local subtitle =
		Widgets.Label(inner, `Your Shibas worked while you were away ({Widgets.Duration(seconds)}) and earned…`, 19)
	subtitle.Position = UDim2.fromOffset(16, 62)
	subtitle.Size = UDim2.new(1, -32, 0, 26)
	subtitle.TextXAlignment = Enum.TextXAlignment.Center
	subtitle.TextScaled = true
	local subtitleLimit = Instance.new("UITextSizeConstraint")
	subtitleLimit.MaxTextSize = 19
	subtitleLimit.Parent = subtitle

	local amountBox = Instance.new("Frame")
	amountBox.AnchorPoint = Vector2.new(0.5, 0)
	amountBox.Position = UDim2.new(0.5, 0, 0, 96)
	amountBox.Size = UDim2.new(1, -60, 0, 92)
	amountBox.BackgroundColor3 = Theme.Panel
	amountBox.Parent = inner
	Widgets.Corner(amountBox, 46)
	local amountLabel = Widgets.Label(amountBox, Format.Number(amount), 54, MONEY_GREEN)
	amountLabel.Position = UDim2.fromOffset(0, 4)
	amountLabel.Size = UDim2.new(1, 0, 0, 58)
	amountLabel.TextXAlignment = Enum.TextXAlignment.Center
	amountLabel.TextStrokeTransparency = 0
	local unit = Widgets.Label(amountBox, "Bonk Points", 22, MONEY_GREEN)
	unit.Position = UDim2.fromOffset(0, 60)
	unit.Size = UDim2.new(1, 0, 0, 26)
	unit.TextXAlignment = Enum.TextXAlignment.Center
	unit.TextStrokeTransparency = 0.2

	local okay = Widgets.Button(inner, "OKAY", OKAY_GREY, 30)
	okay.AnchorPoint = Vector2.new(1, 0)
	okay.Position = UDim2.new(0.5, -10, 0, 212)
	okay.Size = UDim2.new(0.5, -30, 0, 58)
	okay.TextStrokeTransparency = 0.2
	okay.Activated:Connect(function()
		claim(false)
		close()
	end)

	local double = Widgets.Button(inner, "DOUBLE IT!", DOUBLE_GREEN, 30)
	double.Position = UDim2.new(0.5, 10, 0, 212)
	double.Size = UDim2.new(0.5, -30, 0, 58)
	double.TextStrokeTransparency = 0.2
	local x2 = Widgets.Label(double, "x2", 26)
	x2.AnchorPoint = Vector2.new(0.5, 0.5)
	x2.Position = UDim2.new(0.5, 0, 0, -2)
	x2.Size = UDim2.fromOffset(60, 28)
	x2.TextXAlignment = Enum.TextXAlignment.Center
	x2.TextStrokeTransparency = 0
	x2.ZIndex = 2

	local product = Shop.GetProduct("DoubleOffline")
	local price = Widgets.Label(inner, if product then `R$ {product.Robux}` else "", 18, Theme.Muted)
	price.Position = UDim2.new(0.5, 10, 0, 272)
	price.Size = UDim2.new(0.5, -30, 0, 22)
	price.TextXAlignment = Enum.TextXAlignment.Center

	local waiting = false
	double.Activated:Connect(function()
		if waiting then
			return
		end
		waiting = true
		double.Text = "…"
		claim(true)
		-- Bought: the server pays and the popup closes (State.Changed). Not bought: let them try again or press OKAY.
		task.delay(DOUBLE_RETRY_SECONDS, function()
			waiting = false
			if double.Parent then
				double.Text = "DOUBLE IT!"
			end
		end)
	end)

	local scale = Instance.new("UIScale")
	scale.Scale = 0.8
	scale.Parent = outer
	TweenService:Create(scale, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end

local function onStateChanged()
	local state = State.Get()
	if not state then
		return
	end
	local pending = state.Bank.Pending
	if gui and pending <= 0 then
		-- Claimed or doubled.
		close()
	elseif (gui and pending ~= shownAmount) or (not gui and not shownThisSession and pending > 0) then
		-- The amount changed, or the OfflineEarnings event came before we listened.
		show(pending, state.Bank.PendingSeconds)
	end
end

function WelcomeBackController.Start()
	State.Start()
	Net.Get(Net.OfflineEarnings).OnClientEvent:Connect(function(amount: unknown, seconds: unknown)
		if typeof(amount) == "number" and typeof(seconds) == "number" then
			show(amount, seconds)
		end
	end)
	State.Changed:Connect(onStateChanged)
	onStateChanged()
end

return WelcomeBackController
