--!strict
-- The "unconscious tutorial" for brand-new players (Config/Tutorial, docs/GAME_DESIGN.md → Onboarding / first
-- minute). While Tutorial.IsGuiding (fewer than GuidedPurchases purchases, hints on) it always points at the ONE next
-- thing to do, without text walls or popups:
--   * something affordable → a glowing line from the character's feet to it, a pulsing highlight on it and a short
--     floating hint above it ("Step here!" on the NEW SHIBA pad, "Buy better sticks!" on a stall …);
--   * nothing affordable → "Catch the stick!" over the field (after the first catch: "Get more money!"), with a line
--     to the field only when the character is far from it.
-- A hint disappears as soon as its goal is done (the target changes). Purely visual: TutorialService (server) counts
-- the purchases in state.Tutorial.Step; stands and pad come from StationController.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local Stations = require(ReplicatedStorage.Shared.Config.Stations)
local Tutorial = require(ReplicatedStorage.Shared.Config.Tutorial)
local Types = require(ReplicatedStorage.Shared.Types)

local State = require(script.Parent.Parent.UI.State)
local StationController = require(script.Parent.StationController)
local Theme = require(script.Parent.Parent.UI.Theme)

local LOOP_SECONDS = 0.2
-- The line starts at the character's feet.
local FEET_OFFSET = Vector3.new(0, -2.6, 0)

type Target = {
	-- Identifies the target, so the hint only restarts its bounce when the target changes.
	Key: string,
	-- The billboard hangs above this part.
	Part: BasePart,
	-- Where the line ends (on the ground).
	Point: Vector3,
	-- Pulsing highlight on this (nil = none).
	Highlight: Instance?,
	Hint: string,
	HintOffset: number,
	-- Draw the line only when the character is farther than this.
	BeamFrom: number,
}

local player = Players.LocalPlayer

local folder: Folder
-- Invisible part over the island centre, for the field hint.
local fieldPart: Part
local fromAttachment: Attachment
local toAttachment: Attachment
local beam: Beam
local highlight: Highlight
local hintGui: BillboardGui
local hintLabel: TextLabel
local hintBounce: Tween? = nil
local currentKey: string? = nil
-- A stick was caught this session (switches the field hint from "Catch the stick!" to "Get more money!").
local caught = false

local TutorialController = {}

local function islandCenter(): Vector3?
	local islands = Workspace:FindFirstChild(Gameplay.Island.FolderName)
	local island = if islands then islands:FindFirstChild(`{Gameplay.Island.ModelPrefix}{player.UserId}`) else nil
	local center = if island then island:GetAttribute(Tutorial.IslandCenterAttribute) else nil
	return if typeof(center) == "Vector3" then center else nil
end

local function rootPart(): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

local function chooseTarget(state: Types.PlayerState): Target?
	if not Tutorial.IsGuiding(state) then
		return nil
	end
	local id = StationController.CheapestAffordable(state)
	local pad = StationController.GetPad()
	if id == "Shooters" and pad then
		return {
			Key = "Pad",
			Part = pad,
			Point = pad.Position,
			Highlight = pad :: Instance,
			Hint = Tutorial.Hints.Pad,
			HintOffset = Tutorial.HintOffsetPad,
			BeamFrom = Tutorial.BeamHideDistance,
		}
	end
	local anchor = if id then StationController.GetAnchor(id) else nil
	if id and anchor then
		return {
			Key = `Stall_{id}`,
			Part = anchor,
			Point = anchor.Position - Vector3.new(0, Stations.StandHeight * 0.55, 0),
			Highlight = StationController.GetStand(id),
			Hint = Tutorial.Hints.Stalls[id] or Tutorial.Hints.Upgrade,
			HintOffset = Tutorial.HintOffsetStall,
			BeamFrom = Tutorial.BeamHideDistance,
		}
	end
	-- Nothing to buy (or its stand isn't there): catch sticks on the field.
	local center = islandCenter()
	if not center then
		return nil
	end
	fieldPart.Position = center
	return {
		Key = if caught then "FieldMore" else "Field",
		Part = fieldPart :: BasePart,
		Point = center,
		Highlight = nil,
		Hint = if caught then Tutorial.Hints.MoreMoney else Tutorial.Hints.Catch,
		HintOffset = Tutorial.HintOffsetField,
		BeamFrom = Tutorial.FieldBeamDistance,
	}
end

local function hide()
	currentKey = nil
	beam.Enabled = false
	highlight.Enabled = false
	hintGui.Enabled = false
	local bounce = hintBounce
	if bounce then
		bounce:Cancel()
		hintBounce = nil
	end
end

local function show(target: Target, root: BasePart?)
	if target.Key ~= currentKey then
		currentKey = target.Key
		hintLabel.Text = target.Hint
		hintGui.Adornee = target.Part
		local base = Vector3.new(0, target.HintOffset, 0)
		hintGui.StudsOffset = base
		local bounce = hintBounce
		if bounce then
			bounce:Cancel()
		end
		local newBounce = TweenService:Create(
			hintGui,
			TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
			{ StudsOffset = base + Vector3.new(0, 1, 0) }
		)
		newBounce:Play()
		hintBounce = newBounce
	end
	hintGui.Enabled = true

	local highlighted = target.Highlight
	highlight.Adornee = highlighted
	highlight.Enabled = highlighted ~= nil

	toAttachment.WorldPosition = target.Point + Vector3.new(0, 0.4, 0)
	if root and fromAttachment.Parent ~= root then
		fromAttachment.Parent = root
	end
	local far = false
	if root then
		local offset = root.Position - target.Point
		far = Vector3.new(offset.X, 0, offset.Z).Magnitude > target.BeamFrom
	end
	beam.Enabled = far and fromAttachment.Parent == root
end

local function update()
	local state = State.Get()
	local target = if state then chooseTarget(state) else nil
	if not target then
		if currentKey ~= nil or beam.Enabled or hintGui.Enabled then
			hide()
		end
		return
	end
	show(target, rootPart())
end

local function build()
	folder = Instance.new("Folder")
	folder.Name = "LocalTutorial"
	folder.Parent = Workspace

	fieldPart = Instance.new("Part")
	fieldPart.Name = "TutorialField"
	fieldPart.Size = Vector3.one
	fieldPart.Transparency = 1
	fieldPart.Anchored = true
	fieldPart.CanCollide = false
	fieldPart.CanQuery = false
	fieldPart.CanTouch = false
	fieldPart.Parent = folder

	fromAttachment = Instance.new("Attachment")
	fromAttachment.Name = "TutorialFrom"
	fromAttachment.Position = FEET_OFFSET
	-- World-space end point (attachments in Terrain are positioned in world coordinates).
	toAttachment = Instance.new("Attachment")
	toAttachment.Name = "TutorialTo"
	toAttachment.Parent = Workspace.Terrain

	beam = Instance.new("Beam")
	beam.Name = "TutorialBeam"
	beam.Attachment0 = fromAttachment
	beam.Attachment1 = toAttachment
	beam.Width0 = Tutorial.BeamWidth
	beam.Width1 = Tutorial.BeamWidth
	beam.FaceCamera = true
	beam.LightEmission = 1
	beam.LightInfluence = 0
	beam.Color = ColorSequence.new(Tutorial.BeamColor, Tutorial.BeamEndColor)
	beam.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.6),
		NumberSequenceKeypoint.new(0.15, 0.1),
		NumberSequenceKeypoint.new(1, 0.1),
	})
	beam.Texture = Tutorial.BeamTexture
	beam.TextureMode = Enum.TextureMode.Wrap
	beam.TextureLength = Tutorial.BeamTextureLength
	beam.TextureSpeed = Tutorial.BeamTextureSpeed
	beam.Segments = 12
	beam.Enabled = false
	beam.Parent = folder

	highlight = Instance.new("Highlight")
	highlight.Name = "TutorialHighlight"
	highlight.FillColor = Tutorial.HighlightColor
	highlight.OutlineColor = Tutorial.HighlightColor
	highlight.FillTransparency = Tutorial.HighlightFillMax
	highlight.OutlineTransparency = 0
	highlight.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
	highlight.Enabled = false
	highlight.Parent = folder
	TweenService:Create(
		highlight,
		TweenInfo.new(Tutorial.HighlightPulseSeconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{ FillTransparency = Tutorial.HighlightFillMin }
	):Play()

	hintGui = Instance.new("BillboardGui")
	hintGui.Name = "TutorialHint"
	hintGui.Size = UDim2.fromOffset(Tutorial.HintSize.X, Tutorial.HintSize.Y)
	hintGui.AlwaysOnTop = true
	hintGui.LightInfluence = 0
	hintGui.Enabled = false
	hintGui.ResetOnSpawn = false
	hintGui.Parent = player:WaitForChild("PlayerGui")
	hintLabel = Instance.new("TextLabel")
	hintLabel.BackgroundTransparency = 1
	hintLabel.Size = UDim2.fromScale(1, 1)
	hintLabel.Font = Theme.TitleFont
	hintLabel.TextScaled = true
	hintLabel.TextColor3 = Tutorial.HintColor
	hintLabel.Text = ""
	hintLabel.Parent = hintGui
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 4
	stroke.Color = Theme.Stroke
	stroke.LineJoinMode = Enum.LineJoinMode.Round
	stroke.Parent = hintLabel
end

function TutorialController.Init()
	build()
end

function TutorialController.Start()
	State.Start()
	State.Changed:Connect(update)
	-- Our own listener: the first catch switches the field hint (BonkController plays the bonk itself).
	Net.Get(Net.BonkHit).OnClientEvent:Connect(function()
		caught = true
	end)
	task.spawn(function()
		while true do
			update()
			task.wait(LOOP_SECONDS)
		end
	end)
end

return TutorialController
