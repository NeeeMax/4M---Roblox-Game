--!strict
-- The street's Bonk Interns are R15 Roblox characters (built by World/StreetPlot, model "Intern" with the attribute
-- StreetIntern). This controller makes them alive, all on the client (the server pays nothing for it):
-- * idle: a small breathing bob, a slow look around and arms swaying a little (Motor6D Transform of Waist, Neck, shoulders);
-- * flinch: when TycoonController ducks an intern (it sets the local attribute BonkedAt) it also leans forward and throws
--   its arms up for a moment;
-- * speech: every intern says a line from Config/InternLines every 8-25 s (jittered per intern), only when the local player
--   is within Automation.Chat.SpeakDistance, never all at once, as a rounded bubble over its head that fades in and out.
--   A bonk is answered with a reaction line (sometimes), and the first approach with a greeting.
-- Only active with Features.Street. Island-mode interns (AutomationController) are not touched.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Automation = require(ReplicatedStorage.Shared.Config.Automation)
local Features = require(ReplicatedStorage.Shared.Config.Features)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local InternLines = require(ReplicatedStorage.Shared.Config.InternLines)

local CHAT = Automation.Chat
local GREETING_DISTANCE = 30
local BUBBLE_PADDING = Vector2.new(22, 14)
local BUBBLE_FONT = Enum.Font.GothamBold
-- A reaction line is not repeated sooner than this per intern.
local REACTION_COOLDOWN = 6

type Intern = {
	Model: Model,
	Head: BasePart,
	Phase: number,
	NextSpeak: number,
	LastBubbleAt: number,
	BonkedAt: number,
	Greeted: boolean,
	Bubble: BillboardGui?,
	LastLine: { [string]: number },
	NextJointScan: number,
	Waist: Motor6D?,
	Neck: Motor6D?,
	LeftShoulder: Motor6D?,
	RightShoulder: Motor6D?,
}

local rng = Random.new()
local interns: { [Model]: Intern } = {}
local lastBubbleStart = 0

local InternChatController = {}

-- ==== helpers ====================================================================================================

local function localPosition(): Vector3?
	local character = Players.LocalPlayer.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if root and root:IsA("BasePart") then
		return root.Position
	end
	local camera = Workspace.CurrentCamera
	return if camera then camera.CFrame.Position else nil
end

local function distanceTo(intern: Intern, from: Vector3): number
	return (intern.Head.Position - from).Magnitude
end

local function pickLine(intern: Intern, kind: string): string
	local list: { string } = (InternLines :: any)[kind]
	local index = rng:NextInteger(1, #list)
	if #list > 1 and index == intern.LastLine[kind] then
		index = index % #list + 1
	end
	intern.LastLine[kind] = index
	return list[index]
end

local function bubbleCount(): number
	local count = 0
	for _, intern in interns do
		if intern.Bubble and intern.Bubble.Parent then
			count += 1
		end
	end
	return count
end

local function scanJoints(intern: Intern)
	for _, descendant in intern.Model:GetDescendants() do
		if descendant:IsA("Motor6D") then
			local name = descendant.Name
			if name == "Waist" then
				intern.Waist = descendant
			elseif name == "Neck" then
				intern.Neck = descendant
			elseif name == "LeftShoulder" then
				intern.LeftShoulder = descendant
			elseif name == "RightShoulder" then
				intern.RightShoulder = descendant
			end
		end
	end
end

-- ==== speech bubble ==============================================================================================

local function fade(gui: BillboardGui, transparency: number, seconds: number)
	local info = TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local frame = gui:FindFirstChild("Bubble")
	if not frame or not frame:IsA("Frame") then
		return
	end
	TweenService:Create(frame, info, { BackgroundTransparency = transparency }):Play()
	local stroke = frame:FindFirstChildOfClass("UIStroke")
	if stroke then
		TweenService:Create(stroke, info, { Transparency = transparency }):Play()
	end
	local label = frame:FindFirstChildOfClass("TextLabel")
	if label then
		TweenService:Create(label, info, { TextTransparency = transparency }):Play()
	end
end

local function clearBubble(intern: Intern)
	if intern.Bubble then
		intern.Bubble:Destroy()
		intern.Bubble = nil
	end
end

local function say(intern: Intern, text: string)
	clearBubble(intern)
	local maxWidth = CHAT.MaxTextWidth
	local measured = TextService:GetTextSize(text, CHAT.TextSize, BUBBLE_FONT, Vector2.new(maxWidth, 1000))
	local textSize = Vector2.new(math.ceil(measured.X) + 2, math.ceil(measured.Y) + 2)
	local size = textSize + BUBBLE_PADDING

	local gui = Instance.new("BillboardGui")
	gui.Name = "InternBubbleGui"
	gui.Adornee = intern.Head
	gui.Size = UDim2.fromOffset(size.X, size.Y)
	gui.StudsOffsetWorldSpace = Vector3.new(0, CHAT.BubbleHeight, 0)
	gui.AlwaysOnTop = false
	gui.LightInfluence = 0
	gui.MaxDistance = CHAT.SpeakDistance + 30
	gui.Active = false

	local frame = Instance.new("Frame")
	frame.Name = "Bubble"
	frame.Size = UDim2.fromScale(1, 1)
	frame.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
	frame.BackgroundTransparency = 1
	frame.BorderSizePixel = 0
	frame.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 12)
	corner.Parent = frame
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromRGB(40, 40, 55)
	stroke.Thickness = 2
	stroke.Transparency = 1
	stroke.Parent = frame
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = BUBBLE_FONT
	label.TextSize = CHAT.TextSize
	label.TextColor3 = Color3.fromRGB(35, 35, 50)
	label.TextWrapped = true
	label.TextTransparency = 1
	label.Text = text
	label.Parent = frame

	gui.Parent = intern.Head
	intern.Bubble = gui
	intern.LastBubbleAt = os.clock()
	lastBubbleStart = intern.LastBubbleAt
	fade(gui, 0, CHAT.FadeTime)
	task.delay(math.max(CHAT.BubbleTime - CHAT.FadeTime, 0.5), function()
		if gui.Parent then
			fade(gui, 1, CHAT.FadeTime)
		end
	end)
	task.delay(CHAT.BubbleTime, function()
		gui:Destroy()
		if intern.Bubble == gui then
			intern.Bubble = nil
		end
	end)
end

-- ==== registering interns ========================================================================================

local function onBonked(intern: Intern)
	local now = os.clock()
	intern.BonkedAt = now
	local from = localPosition()
	if not from or distanceTo(intern, from) > CHAT.SpeakDistance then
		return
	end
	if
		rng:NextNumber() < CHAT.ReactionChance
		and now - intern.LastBubbleAt >= REACTION_COOLDOWN
		and bubbleCount() < CHAT.MaxBubbles
		and now - lastBubbleStart >= CHAT.MinGap
	then
		say(intern, pickLine(intern, "Bonked"))
		intern.NextSpeak = math.max(intern.NextSpeak, now + CHAT.MinInterval)
	end
end

local function register(model: Model)
	if interns[model] or model.Name ~= "Intern" or model:GetAttribute("StreetIntern") ~= true then
		return
	end
	-- Wait for the parts (a second call for the same model is dropped by the check after the wait).
	task.spawn(function()
		local head = model:WaitForChild("Head", 10)
		if interns[model] or not head or not head:IsA("BasePart") or not model.Parent then
			return
		end
		local now = os.clock()
		local intern: Intern = {
			Model = model,
			Head = head,
			Phase = rng:NextNumber(0, math.pi * 2),
			NextSpeak = now + rng:NextNumber(CHAT.MinInterval, CHAT.MaxInterval),
			LastBubbleAt = 0,
			BonkedAt = -100,
			Greeted = false,
			Bubble = nil,
			LastLine = {},
			NextJointScan = 0,
			Waist = nil,
			Neck = nil,
			LeftShoulder = nil,
			RightShoulder = nil,
		}
		interns[model] = intern
		model:GetAttributeChangedSignal("BonkedAt"):Connect(function()
			onBonked(intern)
		end)
		model.Destroying:Connect(function()
			clearBubble(intern)
			interns[model] = nil
		end)
	end)
end

-- ==== idle animation and flinch (every frame, only near the camera) ================================================

local function animate(intern: Intern, now: number)
	if
		now >= intern.NextJointScan
		and not (intern.Waist and intern.Neck and intern.LeftShoulder and intern.RightShoulder)
	then
		intern.NextJointScan = now + 2
		scanJoints(intern)
	end
	local t = now + intern.Phase
	local bob = math.sin(t * CHAT.BobSpeed) * CHAT.BobAmount
	local look = math.sin(t * CHAT.LookSpeed)
		* CHAT.LookAmount
		* math.clamp(math.sin(t * CHAT.LookSpeed * 0.5) * 2, -1, 1)
	local sway = math.sin(t * CHAT.BobSpeed + 1) * 0.06

	-- Flinch: 1 right after the bonk, easing to 0.
	local flinch = math.clamp(1 - (now - intern.BonkedAt) / CHAT.FlinchTime, 0, 1)
	flinch = flinch * flinch
	local lean = math.rad(CHAT.FlinchDegrees) * flinch
	local shake = math.sin(now * 40) * 0.12 * flinch

	local waist = intern.Waist
	if waist then
		-- Positive X leans back, negative forward (the character faces -Z).
		waist.Transform = CFrame.Angles(bob - lean, 0, 0)
	end
	local neck = intern.Neck
	if neck then
		neck.Transform = CFrame.Angles(-bob * 0.5 - lean * 0.6, look + shake, 0)
	end
	local left = intern.LeftShoulder
	if left then
		left.Transform = CFrame.Angles(sway + math.rad(70) * flinch, 0, -0.03 - bob)
	end
	local right = intern.RightShoulder
	if right then
		right.Transform = CFrame.Angles(-sway + math.rad(70) * flinch, 0, 0.03 + bob)
	end
end

local function step()
	local camera = Workspace.CurrentCamera
	if not camera then
		return
	end
	local origin = camera.CFrame.Position
	local now = os.clock()
	for model, intern in interns do
		if not model.Parent then
			interns[model] = nil
		elseif not model:GetAttribute("Spawning") and distanceTo(intern, origin) <= CHAT.AnimateDistance then
			animate(intern, now)
		end
	end
end

-- ==== speech scheduler (a couple of times per second) ============================================================

local function scheduleTick()
	local from = localPosition()
	if not from then
		return
	end
	local now = os.clock()
	local active = bubbleCount()
	for model, intern in interns do
		if not model.Parent or model:GetAttribute("Spawning") then
			continue
		end
		local distance = distanceTo(intern, from)
		local canSpeak = active < CHAT.MaxBubbles and now - lastBubbleStart >= CHAT.MinGap
		if not intern.Greeted and distance <= GREETING_DISTANCE then
			intern.Greeted = true
			if canSpeak and rng:NextNumber() < CHAT.GreetingChance then
				say(intern, pickLine(intern, "Greeting"))
				active += 1
				canSpeak = false
				intern.NextSpeak = now + rng:NextNumber(CHAT.MinInterval, CHAT.MaxInterval)
			end
		elseif now >= intern.NextSpeak then
			if distance > CHAT.SpeakDistance then
				-- Out of earshot: try again soon, so it does not talk the moment the player arrives from afar.
				intern.NextSpeak = now + rng:NextNumber(2, 6)
			elseif canSpeak then
				say(intern, pickLine(intern, "Idle"))
				active += 1
				intern.NextSpeak = now + rng:NextNumber(CHAT.MinInterval, CHAT.MaxInterval)
			else
				intern.NextSpeak = now + rng:NextNumber(0.5, 2)
			end
		end
	end
end

function InternChatController.Start()
	if not Features.Street then
		return
	end
	task.spawn(function()
		local islands = Workspace:WaitForChild(Gameplay.Island.FolderName)
		islands.DescendantAdded:Connect(function(descendant: Instance)
			if descendant:IsA("Model") then
				register(descendant)
			end
		end)
		for _, descendant in islands:GetDescendants() do
			if descendant:IsA("Model") then
				register(descendant)
			end
		end
	end)
	RunService.RenderStepped:Connect(step)
	task.spawn(function()
		while true do
			task.wait(0.5)
			scheduleTick()
		end
	end)
end

return InternChatController
