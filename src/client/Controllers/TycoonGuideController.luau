--!strict
-- Walkthrough guide of the street tycoon (docs/GAME_DESIGN.md → Street, plots and buttons → Walkthrough guide). Purely
-- visual, client only: no remotes, nothing saved, the server decides everything.
-- - A bobbing, spinning white neon arrow over the floor pad of the current step (client parts in Workspace/TycoonGuideVisuals).
--   Hidden while the player stands closer than NEAR_DISTANCE to the pad.
-- - One objective line under the money pill / income line ("Step on the glowing pad: First Shiba" …).
-- Does nothing at all while Config/Features.Street is false (Start returns early) and only works while
-- state.Tycoon.Enabled and state.Tycoon.Street are true. The pads are built and destroyed by the server
-- (World/StreetPlot: folders `Pad_<stepId>` with the part `Pad` under Workspace/Islands/Island_<UserId>/Tycoon), so the
-- part is looked up again whenever it is missing, destroyed or the current step changes.
--
-- Current pad rule: of the pads TycoonSteps.Visible returns (Shibas, automation and the required decor), the first one
-- the player can afford (state.BonkPoints >= TycoonSteps.Price); when none is affordable, the first visible one.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Features = require(ReplicatedStorage.Shared.Config.Features)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Types = require(ReplicatedStorage.Shared.Types)
local TycoonSteps = require(ReplicatedStorage.Shared.Util.TycoonSteps)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

type TycoonState = Types.TycoonState
type Step = TycoonSteps.Step

-- The arrow hides when the player is this close (studs, horizontal) to the pad.
local NEAR_DISTANCE = 6
-- Arrow height above the pad (centre of the head), bob amplitude and speeds.
local ARROW_HEIGHT = 6
local BOB_AMPLITUDE = 0.6
local BOB_SPEED = 3
local SPIN_SPEED = 1.6
-- A missing pad part is searched again at most this often (seconds).
local LOOKUP_INTERVAL = 0.5
-- Objective line: top offset (pixels, under the money pill, income line and boosts), size and text size.
local LABEL_TOP = 138
local LABEL_WIDTH = 560
local LABEL_HEIGHT = 30
local LABEL_TEXT_SIZE = 22

local player = Players.LocalPlayer

local started = false
local active = false
local renderConnection: RBXScriptConnection? = nil
local gui: ScreenGui? = nil
local objectiveLabel: TextLabel? = nil
local visuals: Folder? = nil
local arrowStem: Part? = nil
local arrowHead: Part? = nil

-- The step the arrow points at and its found `Pad` part.
local targetId: string? = nil
local padPart: BasePart? = nil
local lastLookup = 0

local TycoonGuideController = {}

-- ==== state ======================================================================================================

local function streetTycoon(): TycoonState?
	local state = State.Get()
	local tycoon = if state then state.Tycoon else nil
	if tycoon and tycoon.Enabled and tycoon.Street == true then
		return tycoon
	end
	return nil
end

-- The step of the arrow: first affordable visible pad, else the first visible one, else nil (everything bought).
local function currentStep(tycoon: TycoonState, money: number): (Step?, boolean)
	local visible = TycoonSteps.Visible(tycoon)
	for _, step in visible do
		if money >= TycoonSteps.Price(step, tycoon) then
			return step, true
		end
	end
	return visible[1], false
end

local function hasUnautomatedShiba(tycoon: TycoonState): boolean
	for _, shiba in tycoon.Shibas do
		if shiba.Automated ~= true then
			return true
		end
	end
	return false
end

local function hasShiba(tycoon: TycoonState): boolean
	return next(tycoon.Shibas) ~= nil
end

-- The short objective for the current step; derived from TycoonSteps and the state only.
local function objectiveText(tycoon: TycoonState, step: Step, affordable: boolean): string
	local title = TycoonSteps.Title(step)
	local price = TycoonSteps.Price(step, tycoon)
	if affordable then
		if step.Kind == "Decor" then
			return `Build {title}: the next Shiba needs a finished {TycoonSteps.ShibaName(step.Bay)} surrounding`
		elseif step.Kind == "Automate" then
			return `Buy the {title}: {TycoonSteps.Description(step)}`
		elseif not hasShiba(tycoon) then
			return `Step on the glowing pad: {title}`
		end
		return `Expand your plot: {title}`
	end
	if hasUnautomatedShiba(tycoon) then
		return `Click your Shiba to earn money ({Format.Short(price)} for {title})`
	end
	return `Earn {Format.Short(price)} for: {title}`
end

-- ==== arrow ======================================================================================================

local function newArrowPart(name: string, size: Vector3): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.Neon
	part.Color = Color3.new(1, 1, 1)
	part.Size = size
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	return part
end

local function getVisuals(): Folder
	local folder = visuals
	if folder and folder.Parent then
		return folder
	end
	local created = Instance.new("Folder")
	created.Name = "TycoonGuideVisuals"
	created.Parent = Workspace
	visuals = created
	return created
end

-- Finds the `Pad` part of a step under the player's Tycoon folder (nil while not streamed in / not built).
local function findPad(id: string): BasePart?
	local islands = Workspace:FindFirstChild("Islands")
	local island = if islands then islands:FindFirstChild(`Island_{player.UserId}`) else nil
	local tycoonFolder = if island then island:FindFirstChild("Tycoon") else nil
	local padFolder = if tycoonFolder then tycoonFolder:FindFirstChild(`Pad_{id}`, true) else nil
	local part = if padFolder then padFolder:FindFirstChild("Pad") else nil
	if part and part:IsA("BasePart") then
		return part
	end
	return nil
end

local function setArrowVisible(visible: boolean)
	local stem, head = arrowStem, arrowHead
	if not stem or not head then
		return
	end
	local parent = if visible then getVisuals() else nil
	if stem.Parent ~= parent then
		stem.Parent = parent
	end
	if head.Parent ~= parent then
		head.Parent = parent
	end
end

local function destroyArrow()
	if arrowStem then
		arrowStem:Destroy()
		arrowStem = nil
	end
	if arrowHead then
		arrowHead:Destroy()
		arrowHead = nil
	end
	if visuals then
		visuals:Destroy()
		visuals = nil
	end
	padPart = nil
end

local function ensureArrow()
	if arrowStem and arrowHead then
		return
	end
	-- Down arrow: a stem and a block turned 45 degrees (a diamond whose lower tip points at the pad).
	arrowStem = newArrowPart("GuideArrowStem", Vector3.new(0.9, 2.2, 0.9))
	arrowHead = newArrowPart("GuideArrowHead", Vector3.new(2.2, 2.2, 0.9))
end

local function onRender()
	if not active then
		return
	end
	local id = targetId
	local stem, head = arrowStem, arrowHead
	if not id or not stem or not head then
		setArrowVisible(false)
		return
	end

	local pad = padPart
	if not pad or not pad.Parent or not pad:IsDescendantOf(Workspace) then
		padPart = nil
		local now = os.clock()
		if now - lastLookup >= LOOKUP_INTERVAL then
			lastLookup = now
			padPart = findPad(id)
		end
		pad = padPart
	end
	if not pad then
		setArrowVisible(false)
		return
	end

	local padPosition = pad.Position
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if root and root:IsA("BasePart") then
		local offset = root.Position - padPosition
		if Vector3.new(offset.X, 0, offset.Z).Magnitude < NEAR_DISTANCE then
			setArrowVisible(false)
			return
		end
	end

	local clock = os.clock()
	local centre = padPosition + Vector3.new(0, ARROW_HEIGHT + math.sin(clock * BOB_SPEED) * BOB_AMPLITUDE, 0)
	local base = CFrame.new(centre) * CFrame.Angles(0, clock * SPIN_SPEED, 0)
	stem.CFrame = base * CFrame.new(0, 1.6, 0)
	head.CFrame = base * CFrame.new(0, -0.4, 0) * CFrame.Angles(0, 0, math.rad(45))
	setArrowVisible(true)
end

-- ==== objective line =============================================================================================

local function ensureLabel(): TextLabel
	local label = objectiveLabel
	if label and label.Parent then
		return label
	end
	local screen = Widgets.Screen("TycoonGuide")
	gui = screen
	local created = Widgets.Label(screen, "", LABEL_TEXT_SIZE, Theme.Accent)
	created.Name = "Objective"
	created.Font = Theme.TitleFont
	created.AnchorPoint = Vector2.new(0.5, 0)
	created.Position = UDim2.new(0.5, 0, 0, LABEL_TOP)
	created.Size = UDim2.fromOffset(LABEL_WIDTH, LABEL_HEIGHT)
	created.TextXAlignment = Enum.TextXAlignment.Center
	created.TextStrokeTransparency = 1
	created.TextScaled = true
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = LABEL_TEXT_SIZE
	limit.Parent = created
	Widgets.Outline(created, 2)
	objectiveLabel = created
	return created
end

-- ==== activation =================================================================================================

local function refresh()
	local tycoon = streetTycoon()
	local state = State.Get()
	if not tycoon or not state then
		return
	end
	local step, affordable = currentStep(tycoon, state.BonkPoints)
	if not step then
		-- Nothing to buy: no arrow. Either a Shiba has to level up first (say so) or everything visible is bought.
		targetId = nil
		padPart = nil
		setArrowVisible(false)
		local waiting = TycoonSteps.Waiting(tycoon)
		local gate = if waiting then waiting.LevelGate else nil
		if waiting and gate then
			local label = ensureLabel()
			label.Text =
				`Level up {TycoonSteps.ShibaName(waiting.Bay)} to Lv {gate} (hold E at the Shiba): {TycoonSteps.Title(
					waiting
				)} unlocks`
			label.Visible = true
		elseif objectiveLabel then
			objectiveLabel.Visible = false
		end
		return
	end
	if step.Id ~= targetId then
		targetId = step.Id
		padPart = nil
		lastLookup = 0
	end
	ensureArrow()
	local label = ensureLabel()
	label.Text = objectiveText(tycoon, step, affordable)
	label.Visible = true
end

local function deactivate()
	if not active then
		return
	end
	active = false
	if renderConnection then
		renderConnection:Disconnect()
		renderConnection = nil
	end
	targetId = nil
	destroyArrow()
	arrowStem = nil
	arrowHead = nil
	if gui then
		gui:Destroy()
		gui = nil
	end
	objectiveLabel = nil
end

local function activate()
	if active then
		return
	end
	active = true
	renderConnection = RunService.RenderStepped:Connect(onRender)
end

local function onStateChanged()
	if streetTycoon() == nil then
		deactivate()
		return
	end
	activate()
	refresh()
end

function TycoonGuideController.Init()
	-- Nothing to set up before Start.
end

function TycoonGuideController.Start()
	if started or not Features.Street then
		return
	end
	started = true
	State.Start()
	State.Changed:Connect(onStateChanged)
	-- The state may have arrived before this controller started.
	onStateChanged()
end

return TycoonGuideController
