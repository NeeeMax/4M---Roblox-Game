--!strict
-- Shiba Variants reveal (docs/GAME_DESIGN.md → Shiba Variants). The server sends VariantRolled(finderUserId,
-- finderName, slot, variant, shibaName) when a Shiba slot rolls a better variant:
-- - own find: a card pops in ("SHINY!" / "RAINBOW!!" / "HUGE!!!", "Samurai Shiba · Shiba #3 · ×3 sticks") with a sound;
--   several finds from one evolution queue up. A Huge also gets a full-screen rainbow splash.
-- - a Huge (anyone's, the server sends those to everybody): a system line in the chat ("Marco found a HUGE Samurai
--   Shiba!"), so the whole server sees it.
-- Purely visual: nothing is sent back.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local TextChatService = game:GetService("TextChatService")
local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local ShibaEffects = require(ReplicatedStorage.Shared.Config.ShibaEffects)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

-- Title and sound pitch per variant (the bonk sound, pitched: higher = rarer, Huge deep and loud).
local TITLES: { [string]: string } = { Shiny = "SHINY!", Rainbow = "RAINBOW!!", Huge = "HUGE!!!" }
local PITCH: { [string]: number } = { Shiny = 1.35, Rainbow = 1.6, Huge = 0.7 }
local CARD_SECONDS = 2.4
local SPLASH_SECONDS = 3.2
local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 70, 70)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(255, 200, 60)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(80, 230, 110)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(70, 170, 255)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(190, 90, 255)),
})

type Reveal = { Slot: number, Variant: string, ShibaName: string }

local queue: { Reveal } = {}
local showing = false

local card: Frame
local cardScale: UIScale
local cardStroke: UIStroke
local cardGradient: UIGradient
local titleLabel: TextLabel
local detailLabel: TextLabel
local splash: Frame
local splashGradient: UIGradient
local splashTitle: TextLabel
local splashDetail: TextLabel

local VariantController = {}

local function outlined(parent: Instance, text: string, size: number, color: Color3): TextLabel
	local label = Widgets.Label(parent, text, size, color)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextStrokeTransparency = 0
	label.TextStrokeColor3 = Theme.Stroke
	return label
end

local function build()
	local gui = Widgets.Screen("Variants", 7)

	card = Instance.new("Frame")
	card.Name = "Reveal"
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.Position = UDim2.fromScale(0.5, 0.3)
	card.Size = UDim2.fromOffset(460, 130)
	card.BackgroundColor3 = Theme.Background
	card.BackgroundTransparency = 0.05
	card.Visible = false
	card.Parent = gui
	Widgets.Corner(card, 18)
	cardStroke = Instance.new("UIStroke")
	cardStroke.Thickness = 5
	cardStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	cardStroke.Parent = card
	cardGradient = Instance.new("UIGradient")
	cardGradient.Color = RAINBOW
	cardGradient.Enabled = false
	cardGradient.Parent = cardStroke
	cardScale = Instance.new("UIScale")
	cardScale.Parent = card
	titleLabel = outlined(card, "", 58, Theme.Accent)
	titleLabel.Font = Theme.TitleFont
	titleLabel.Position = UDim2.fromOffset(0, 8)
	titleLabel.Size = UDim2.new(1, 0, 0, 70)
	detailLabel = outlined(card, "", 20, Theme.Text)
	detailLabel.Font = Theme.BodyFont
	detailLabel.Position = UDim2.fromOffset(12, 82)
	detailLabel.Size = UDim2.new(1, -24, 0, 36)
	detailLabel.TextWrapped = true

	-- Huge: a full-screen rainbow wash behind a giant title.
	splash = Instance.new("Frame")
	splash.Name = "HugeSplash"
	splash.Size = UDim2.fromScale(1, 1)
	splash.BackgroundColor3 = Color3.new(1, 1, 1)
	splash.BackgroundTransparency = 1
	splash.Visible = false
	splash.ZIndex = 0
	splash.Parent = gui
	splashGradient = Instance.new("UIGradient")
	splashGradient.Color = RAINBOW
	splashGradient.Rotation = 30
	splashGradient.Parent = splash
	splashTitle = outlined(splash, "HUGE!!!", 130, Color3.new(1, 1, 1))
	splashTitle.Font = Theme.TitleFont
	splashTitle.AnchorPoint = Vector2.new(0.5, 0.5)
	splashTitle.Position = UDim2.fromScale(0.5, 0.45)
	splashTitle.Size = UDim2.fromOffset(1000, 150)
	splashDetail = outlined(splash, "", 32, Color3.new(1, 1, 1))
	splashDetail.AnchorPoint = Vector2.new(0.5, 0)
	splashDetail.Position = UDim2.new(0.5, 0, 0.45, 80)
	splashDetail.Size = UDim2.fromOffset(1000, 40)
end

local function playSound(variant: string)
	local soundId = Gameplay.Bonk.SoundId
	if soundId == "" then
		return
	end
	local state = State.Get()
	local volume = if state then state.Settings.Effects else 1
	local sound = Instance.new("Sound")
	sound.SoundId = soundId
	sound.PlaybackSpeed = PITCH[variant] or 1
	sound.Volume = Gameplay.Bonk.SoundVolume * volume * (if variant == "Huge" then 1.5 else 1.1)
	sound.Parent = SoundService
	sound.Ended:Once(function()
		sound:Destroy()
	end)
	sound:Play()
	task.delay(5, function()
		if sound.Parent then
			sound:Destroy()
		end
	end)
end

local function showSplash(reveal: Reveal)
	splashDetail.Text =
		`{reveal.ShibaName} · ×{EconomyConfig.Variants.Multiplier.Huge} sticks · Shiba #{reveal.Slot}`
	splash.Visible = true
	splash.BackgroundTransparency = 0.35
	splashTitle.TextTransparency = 0
	splashTitle.TextStrokeTransparency = 0
	splashDetail.TextTransparency = 0
	splashDetail.TextStrokeTransparency = 0
	local startedAt = os.clock()
	task.spawn(function()
		while os.clock() - startedAt < SPLASH_SECONDS do
			splashGradient.Rotation = (splashGradient.Rotation + 3) % 360
			task.wait()
		end
		local fade = TweenInfo.new(0.5)
		TweenService:Create(splash, fade, { BackgroundTransparency = 1 }):Play()
		TweenService:Create(splashTitle, fade, { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
		TweenService:Create(splashDetail, fade, { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
		task.wait(0.5)
		splash.Visible = false
	end)
end

-- Shows the queued reveals one after another.
local function showNext()
	if showing then
		return
	end
	local reveal = table.remove(queue, 1)
	if not reveal then
		return
	end
	showing = true
	local look = ShibaEffects.Variants[reveal.Variant]
	local color = if look then look.Color else Theme.Accent
	local multiplier = EconomyConfig.Variants.Multiplier[reveal.Variant] or 1
	titleLabel.Text = TITLES[reveal.Variant] or reveal.Variant
	titleLabel.TextColor3 = color
	detailLabel.Text = `{reveal.Variant} {reveal.ShibaName} · Shiba #{reveal.Slot} · ×{multiplier} sticks`
	cardStroke.Color = if look and look.HueCycle then Color3.new(1, 1, 1) else color
	cardGradient.Enabled = look ~= nil and look.HueCycle
	card.Visible = true
	cardScale.Scale = 0.3
	TweenService:Create(cardScale, TweenInfo.new(0.4, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	playSound(reveal.Variant)
	if reveal.Variant == "Huge" then
		showSplash(reveal)
	end
	local startedAt = os.clock()
	task.spawn(function()
		while os.clock() - startedAt < CARD_SECONDS do
			cardGradient.Rotation = (cardGradient.Rotation + 4) % 360
			task.wait()
		end
		TweenService:Create(cardScale, TweenInfo.new(0.2), { Scale = 0 }):Play()
		task.wait(0.2)
		card.Visible = false
		showing = false
		showNext()
	end)
end

-- "Marco found a HUGE Samurai Shiba!" as a system line in the chat (TextChatService only; legacy chat shows nothing).
local function announceInChat(finderName: string, shibaName: string)
	if TextChatService.ChatVersion ~= Enum.ChatVersion.TextChatService then
		return
	end
	local channels = TextChatService:FindFirstChild("TextChannels")
	local general = if channels then channels:FindFirstChild("RBXGeneral") else nil
	if general and general:IsA("TextChannel") then
		local look = ShibaEffects.Variants.Huge
		local hex = if look then look.Color:ToHex() else "c080ff"
		-- Names are shown as plain text: escape what rich text would read as markup.
		local safeName = string.gsub(string.gsub(finderName, "<", "&lt;"), ">", "&gt;")
		local message = `<font color="#{hex}"><b>{safeName} found a HUGE {shibaName}!</b></font>`
		pcall(function()
			general:DisplaySystemMessage(message)
		end)
	end
end

local function onVariantRolled(
	finderUserId: unknown,
	finderName: unknown,
	slot: unknown,
	variant: unknown,
	shibaName: unknown
)
	if
		typeof(finderUserId) ~= "number"
		or typeof(finderName) ~= "string"
		or typeof(slot) ~= "number"
		or typeof(variant) ~= "string"
		or typeof(shibaName) ~= "string"
	then
		return
	end
	if variant == "Huge" then
		announceInChat(finderName, shibaName)
	end
	if finderUserId == Players.LocalPlayer.UserId then
		table.insert(queue, { Slot = slot, Variant = variant, ShibaName = shibaName })
		showNext()
	end
end

function VariantController.Init()
	build()
end

function VariantController.Start()
	State.Start()
	Net.Get(Net.VariantRolled).OnClientEvent:Connect(onVariantRolled)
end

return VariantController
