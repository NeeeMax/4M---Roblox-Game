--!strict
-- The upgrade stands on your own island (built by StationService, Config/Stations): a floating billboard above each
-- stand (name, current value, level badge, level bar, UPGRADE button look with cost and E key hint, and a money bar
-- "your Bonk Dollars / next cost"), the "NEW SHIBA" billboard on the Shiba pad, a grey LOCKED look on stands that
-- unlock with a later Shiba (EconomyConfig.UnlockAtShibaTier, or the server's `Locked` attribute on the anchor), the
-- REBIRTH shrine's billboard, and the next Shiba as a slowly turning black silhouette with its price and a money bar
-- next to the Shiba Tier stand. Hints: a bouncing NEW arrow over stands you can afford, a "You can afford a new
-- upgrade!" popup once per upgrade level with SHOW ME (a path from your character to the stand), and the big yellow
-- button at the bottom that shows the way to the cheapest affordable upgrade. Hints follow Settings.Hints; while the
-- guided tutorial runs (TutorialController) the popup stays away, the tutorial points the way instead.
-- The F prompt ("Buy with R$") sends ShopBuy for the stand's Instant<UpgradeId> product; the server decides.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local Stations = require(ReplicatedStorage.Shared.Config.Stations)
local Tutorial = require(ReplicatedStorage.Shared.Config.Tutorial)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local HudController = require(script.Parent.HudController)
local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

local LOOP_SECONDS = 0.25
local BOARD_OFFSET = Vector3.new(0, 5.6, 0)
local ARROW_OFFSET = Vector3.new(0, 11.2, 0)
local AFFORDABLE = Color3.fromRGB(70, 255, 110)
local UNAFFORDABLE = Color3.fromRGB(170, 170, 180)
local LOCKED = Color3.fromRGB(120, 120, 128)
local BUTTON_READY = Color3.fromRGB(80, 210, 90)
local BUTTON_IDLE = Color3.fromRGB(140, 140, 150)
local GOLD = Color3.fromRGB(255, 205, 50)
local REBIRTH_COLOR = Color3.fromRGB(200, 110, 255)
-- The server may set these on a stand's anchor part (layout rework); they win over the client's own rule.
local LOCKED_ATTRIBUTE = "Locked"

local player = Players.LocalPlayer

-- A thin rounded bar with a fill and a text on top (money / cost, levels …).
type Bar = {
	Frame: Frame,
	Fill: Frame,
	Text: TextLabel,
}

type Board = {
	Id: string,
	Anchor: BasePart,
	Gui: BillboardGui,
	Name: TextLabel,
	Value: TextLabel,
	Badge: TextLabel,
	Level: Bar,
	Button: Frame,
	ButtonText: TextLabel,
	Cost: TextLabel,
	KeyHint: Frame,
	Money: Bar,
	Arrow: BillboardGui,
	Bounce: Tween,
}

type RebirthBoard = {
	Anchor: BasePart,
	Gui: BillboardGui,
	Count: TextLabel,
	Action: TextLabel,
	Progress: Bar,
}

type Silhouette = {
	-- Shibas index shown (EconomyConfig.Shibas).
	Index: number,
	-- The stand anchor it was placed next to.
	Anchor: BasePart,
	Model: Model,
	-- Invisible part above the model holding the billboard.
	Holder: Part,
	Gui: BillboardGui,
	Title: TextLabel,
	Name: TextLabel,
	Price: TextLabel,
	Money: Bar,
	-- Ground point under the model and the pivot relative to "bottom centre" (so it turns in place).
	Ground: Vector3,
	PivotOffset: CFrame,
	Angle: number,
}

type Path = {
	Id: string,
	Beam: Beam,
	From: Attachment,
	To: Attachment,
	EndsAt: number,
}

local boards: { [string]: Board } = {}
local rebirthBoard: RebirthBoard? = nil
local silhouette: Silhouette? = nil
local localFolder: Folder
local padGui: BillboardGui
local padCost: TextLabel
local padMoney: Bar
local padPart: BasePart? = nil
-- UpgradeId → the level the "you can afford" popup was last shown for.
local popupShownFor: { [string]: number } = {}
local popup: Frame
local popupName: TextLabel
local popupTarget: string? = nil
local popupHideAt = 0
local path: Path? = nil

local StationController = {}

local function stationsFolder(): Instance?
	local islands = Workspace:FindFirstChild(Gameplay.Island.FolderName)
	local island = if islands then islands:FindFirstChild(`{Gameplay.Island.ModelPrefix}{player.UserId}`) else nil
	return if island then island:FindFirstChild(Stations.FolderName) else nil
end

-- A label that fills its box (sizes are fractions of the billboard), white with a dark outline.
local function text(parent: Instance, value: string, position: UDim2, size: UDim2, color: Color3?): TextLabel
	local label = Widgets.Label(parent, value, 20, color)
	label.Position = position
	label.Size = size
	label.TextScaled = true
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextStrokeTransparency = 0
	label.TextStrokeColor3 = Theme.Stroke
	return label
end

local function round(instance: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(radius, 0)
	corner.Parent = instance
end

local function box(parent: Instance, position: UDim2, size: UDim2, color: Color3): Frame
	local frame = Instance.new("Frame")
	frame.Position = position
	frame.Size = size
	frame.BackgroundColor3 = color
	frame.BorderSizePixel = 0
	frame.Parent = parent
	return frame
end

local function bar(parent: Instance, position: UDim2, size: UDim2, color: Color3): Bar
	local frame = box(parent, position, size, Theme.Background)
	frame.BackgroundTransparency = 0.15
	round(frame, 0.5)
	local stroke = Instance.new("UIStroke")
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Thickness = 2
	stroke.Color = Theme.Stroke
	stroke.Parent = frame
	local fill = box(frame, UDim2.fromScale(0, 0), UDim2.fromScale(0, 1), color)
	round(fill, 0.5)
	local label = text(frame, "", UDim2.fromScale(0, 0.05), UDim2.fromScale(1, 0.9))
	label.ZIndex = 2
	return { Frame = frame, Fill = fill, Text = label }
end

-- Fills a money bar with money / cost ("almost there"); full and READY! once affordable.
local function setMoneyBar(moneyBar: Bar, money: number, cost: number)
	local share = if cost > 0 then math.clamp(money / cost, 0, 1) else 1
	moneyBar.Fill.Size = UDim2.fromScale(share, 1)
	moneyBar.Fill.BackgroundColor3 = if share >= 1 then AFFORDABLE else GOLD
	moneyBar.Text.Text = if share >= 1 then "READY!" else `{math.floor(share * 100)}%`
end

-- A white arrow built from frames (shaft + a diamond head). `up` points it up, else down.
local function arrowShape(parent: Instance, color: Color3, up: boolean): Frame
	local holder = box(parent, UDim2.fromScale(0, 0), UDim2.fromScale(1, 1), color)
	holder.BackgroundTransparency = 1
	local shaft = box(holder, UDim2.fromScale(0.5, if up then 0.62 else 0.38), UDim2.fromScale(0.26, 0.42), color)
	shaft.AnchorPoint = Vector2.new(0.5, 0.5)
	local head = box(holder, UDim2.fromScale(0.5, if up then 0.36 else 0.64), UDim2.fromScale(0.5, 0.5), color)
	head.AnchorPoint = Vector2.new(0.5, 0.5)
	head.Rotation = 45
	local aspect = Instance.new("UIAspectRatioConstraint")
	aspect.Parent = head
	for _, piece in { shaft, head } do
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = 2
		stroke.Color = Theme.Stroke
		stroke.Parent = piece
	end
	return holder
end

local function valueText(id: string, level: number): string
	local value = Upgrades.FormatValue(id, level)
	if id == "Shooters" then
		return `{value} Shiba{if value == "1" then "" else "s"}`
	elseif id == "MoveSpeed" then
		return `Speed {value}`
	end
	return value
end

local function valueColor(id: string, level: number): Color3
	local def = Upgrades.Defs[id]
	return if def.ValueColors then def.ValueColors[level + 1] or Theme.Text else AFFORDABLE
end

local function hintsOn(state: Types.PlayerState): boolean
	return state.Settings == nil or state.Settings.Hints ~= false
end

-- Name of the Shiba at ShooterTier level `level` ("Galaxy Shiba"), or "?" past the list.
local function shibaName(level: number): string
	local shiba = EconomyConfig.Shibas[level + 1]
	return if shiba then shiba.Name else "?"
end

-- The ShooterTier level upgrade `id` unlocks at, if it is still locked for this player (else nil). The server's
-- `Locked` attribute on the stand's anchor wins when it is set.
local function lockedUntil(state: Types.PlayerState, id: string): number?
	local unlockAt = EconomyConfig.UnlockAtShibaTier[id] or 0
	local board = boards[id]
	local attribute = if board then board.Anchor:GetAttribute(LOCKED_ATTRIBUTE) else nil
	if attribute == false then
		return nil
	end
	local tier = state.UpgradeLevels.ShooterTier or 0
	if attribute == true or tier < unlockAt then
		return math.max(unlockAt, tier + 1)
	end
	return nil
end

-- How many levels one press buys now (1, or up to StackMax with the Stack Upgrade pass) and what they cost.
-- Returns 0 levels (and the next level's cost) when the player can't afford one or it is locked.
local function purchasable(state: Types.PlayerState, id: string): (number, number, boolean)
	local level = state.UpgradeLevels[id] or 0
	local maxLevel = Upgrades.GetMaxLevel(id, state.Passes)
	if level >= maxLevel then
		return 0, 0, true
	end
	if lockedUntil(state, id) then
		return 0, Upgrades.GetCost(id, level), false
	end
	local limit = if state.Passes.StackUpgrade then Stations.StackMax else 1
	local count, total = 0, 0
	while count < limit and level + count < maxLevel do
		local cost = Upgrades.GetCost(id, level + count)
		if total + cost > state.BonkPoints then
			break
		end
		count += 1
		total += cost
	end
	if count == 0 then
		return 0, Upgrades.GetCost(id, level), false
	end
	return count, total, false
end

local function buildBoard(id: string, anchor: BasePart): Board
	local def = Upgrades.Defs[id]
	local playerGui = player:WaitForChild("PlayerGui")

	local gui = Instance.new("BillboardGui")
	gui.Name = `StationBoard_{id}`
	gui.Adornee = anchor
	-- Sized in studs, so it shrinks with distance like a real sign.
	gui.Size = UDim2.fromScale(7, 5.6)
	gui.StudsOffset = BOARD_OFFSET
	gui.LightInfluence = 0
	gui.MaxDistance = Stations.BillboardMaxDistance
	gui.ResetOnSpawn = false
	gui.Parent = playerGui

	local name = text(gui, def.DisplayName, UDim2.fromScale(0.05, 0), UDim2.fromScale(0.9, 0.15))
	local value = text(gui, "", UDim2.fromScale(0.05, 0.15), UDim2.fromScale(0.66, 0.17))
	local badge = text(gui, "", UDim2.fromScale(0.73, 0.14), UDim2.fromScale(0.22, 0.17))
	badge.BackgroundTransparency = 0
	badge.BackgroundColor3 = GOLD
	round(badge, 0.3)
	local badgeStroke = Instance.new("UIStroke")
	badgeStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	badgeStroke.Thickness = 2
	badgeStroke.Color = Theme.Stroke
	badgeStroke.Parent = badge

	-- Level bar.
	local levelBar = bar(gui, UDim2.fromScale(0.08, 0.35), UDim2.fromScale(0.84, 0.11), def.Color)

	-- UPGRADE button look (the prompt's E does the buying) with the cost under it and an E key hint.
	local button = box(gui, UDim2.fromScale(0.14, 0.5), UDim2.fromScale(0.72, 0.21), BUTTON_IDLE)
	round(button, 0.35)
	local buttonStroke = Instance.new("UIStroke")
	buttonStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	buttonStroke.Thickness = 3
	buttonStroke.Color = Theme.Stroke
	buttonStroke.Parent = button
	local shade = Instance.new("UIGradient")
	shade.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(175, 175, 175))
	shade.Rotation = 90
	shade.Parent = button
	local buttonText = text(button, "UPGRADE", UDim2.fromScale(0.08, 0.08), UDim2.fromScale(0.84, 0.84))
	local cost = text(gui, "", UDim2.fromScale(0.1, 0.72), UDim2.fromScale(0.8, 0.14))

	local keyHint = box(gui, UDim2.fromScale(0.83, 0.62), UDim2.fromScale(0.1, 0.12), Color3.new(1, 1, 1))
	round(keyHint, 0.2)
	local keyStroke = Instance.new("UIStroke")
	keyStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	keyStroke.Thickness = 2
	keyStroke.Color = Theme.Stroke
	keyStroke.Parent = keyHint
	local keyText = text(keyHint, "E", UDim2.fromScale(0, 0), UDim2.fromScale(1, 1), Theme.Stroke)
	keyText.TextStrokeTransparency = 1

	-- Money bar: how close you are to the next level.
	local moneyBar = bar(gui, UDim2.fromScale(0.14, 0.88), UDim2.fromScale(0.72, 0.1), GOLD)

	-- Bouncing NEW arrow above the board.
	local arrow = Instance.new("BillboardGui")
	arrow.Name = `StationArrow_{id}`
	arrow.Adornee = anchor
	arrow.Size = UDim2.fromOffset(90, 96)
	arrow.StudsOffset = ARROW_OFFSET
	arrow.AlwaysOnTop = true
	arrow.LightInfluence = 0
	arrow.Enabled = false
	arrow.ResetOnSpawn = false
	arrow.Parent = playerGui
	text(arrow, "NEW", UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.4))
	local arrowBody = arrowShape(arrow, Color3.new(1, 1, 1), false)
	arrowBody.Position = UDim2.fromScale(0.2, 0.4)
	arrowBody.Size = UDim2.fromScale(0.6, 0.6)
	local bounce = TweenService:Create(
		arrow,
		TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{ StudsOffset = ARROW_OFFSET + Vector3.new(0, 1.2, 0) }
	)
	bounce:Play()

	return {
		Id = id,
		Anchor = anchor,
		Gui = gui,
		Name = name,
		Value = value,
		Badge = badge,
		Level = levelBar,
		Button = button,
		ButtonText = buttonText,
		Cost = cost,
		KeyHint = keyHint,
		Money = moneyBar,
		Arrow = arrow,
		Bounce = bounce,
	}
end

local function destroyBoard(board: Board)
	board.Bounce:Cancel()
	board.Gui:Destroy()
	board.Arrow:Destroy()
end

local function buildRebirthBoard(anchor: BasePart): RebirthBoard
	local gui = Instance.new("BillboardGui")
	gui.Name = "StationBoard_Rebirth"
	gui.Adornee = anchor
	gui.Size = UDim2.fromScale(7, 4.4)
	gui.StudsOffset = BOARD_OFFSET
	gui.LightInfluence = 0
	gui.MaxDistance = Stations.BillboardMaxDistance
	gui.ResetOnSpawn = false
	gui.Parent = player:WaitForChild("PlayerGui")

	text(gui, "REBIRTH", UDim2.fromScale(0.05, 0), UDim2.fromScale(0.9, 0.26), REBIRTH_COLOR)
	local count = text(gui, "", UDim2.fromScale(0.05, 0.27), UDim2.fromScale(0.9, 0.17))
	local action = text(gui, "", UDim2.fromScale(0.03, 0.47), UDim2.fromScale(0.94, 0.22))
	local progress = bar(gui, UDim2.fromScale(0.12, 0.75), UDim2.fromScale(0.76, 0.16), REBIRTH_COLOR)
	return { Anchor = anchor, Gui = gui, Count = count, Action = action, Progress = progress }
end

local function refreshRebirthBoard(board: RebirthBoard, state: Types.PlayerState)
	local rebirths = state.Rebirths or 0
	local current = EconomyConfig.RebirthMultiplier(rebirths)
	board.Count.Text = if rebirths > 0 then `Rebirths: {rebirths} · ×{current} income` else "Rebirths: 0"
	local tier = state.UpgradeLevels.ShooterTier or 0
	local needed = EconomyConfig.Rebirth.MinShibaTier
	if tier >= needed then
		board.Action.Text = `Hold E: ×{EconomyConfig.RebirthMultiplier(rebirths + 1)} income forever`
		board.Action.TextColor3 = AFFORDABLE
		board.Progress.Fill.Size = UDim2.fromScale(1, 1)
		board.Progress.Text.Text = "READY!"
	else
		board.Action.Text = `Needs {shibaName(needed)}`
		board.Action.TextColor3 = UNAFFORDABLE
		board.Progress.Fill.Size = UDim2.fromScale(if needed > 0 then tier / needed else 1, 1)
		board.Progress.Text.Text = `Shiba {tier + 1} / {needed + 1}`
	end
end

local function buildPadBoard()
	padGui = Instance.new("BillboardGui")
	padGui.Name = "StationShibaPad"
	padGui.Size = UDim2.fromScale(8, 4.3)
	padGui.StudsOffset = Vector3.new(0, 3.6, 0)
	padGui.LightInfluence = 0
	padGui.MaxDistance = Stations.BillboardMaxDistance
	padGui.Enabled = false
	padGui.ResetOnSpawn = false
	padGui.Parent = player:WaitForChild("PlayerGui")
	text(padGui, "NEW SHIBA", UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.3))
	text(padGui, "step on the pad: another Shiba joins", UDim2.fromScale(0.05, 0.3), UDim2.fromScale(0.9, 0.17), GOLD)
	padCost = text(padGui, "", UDim2.fromScale(0.1, 0.48), UDim2.fromScale(0.8, 0.3))
	padMoney = bar(padGui, UDim2.fromScale(0.2, 0.82), UDim2.fromScale(0.6, 0.14), GOLD)
end

-- Next-Shiba silhouette -------------------------------------------------------------------------------------------

-- A plain dog shape from parts, for when the Shiba's model is missing (black anyway).
local function fallbackShiba(): Model
	local model = Instance.new("Model")
	model.Name = "ShibaSilhouette"
	local function piece(size: Vector3, offset: Vector3)
		local part = Instance.new("Part")
		part.Size = size
		part.CFrame = CFrame.new(offset)
		part.Parent = model
	end
	piece(Vector3.new(2.2, 2, 3.6), Vector3.new(0, 2.2, 0))
	piece(Vector3.new(2.2, 2, 2), Vector3.new(0, 3.9, -1.9))
	piece(Vector3.new(0.6, 0.9, 0.4), Vector3.new(-0.7, 5.3, -1.9))
	piece(Vector3.new(0.6, 0.9, 0.4), Vector3.new(0.7, 5.3, -1.9))
	piece(Vector3.new(1, 0.8, 1), Vector3.new(0, 3.5, -3.3))
	piece(Vector3.new(0.6, 0.6, 1.4), Vector3.new(0, 3.4, 2.2))
	for _, x in { -0.7, 0.7 } do
		for _, z in { -1.2, 1.2 } do
			piece(Vector3.new(0.6, 1.4, 0.6), Vector3.new(x, 0.7, z))
		end
	end
	return model
end

-- A black copy of the Shiba's model: no textures, effects, sounds or scripts; parts that were hidden stay hidden.
local function silhouetteModel(shiba: EconomyConfig.ShibaDef): Model
	local model = Assets.CloneModel(shiba.AssetName) or fallbackShiba()
	local remove: { Instance } = {}
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.Color = Color3.new(0, 0, 0)
			descendant.Material = Enum.Material.SmoothPlastic
			descendant.Reflectance = 0
			descendant.CastShadow = false
			if descendant:IsA("MeshPart") then
				descendant.TextureID = ""
			end
		elseif descendant:IsA("SpecialMesh") then
			descendant.TextureId = ""
		elseif
			descendant:IsA("Decal")
			or descendant:IsA("SurfaceAppearance")
			or descendant:IsA("ParticleEmitter")
			or descendant:IsA("Light")
			or descendant:IsA("Beam")
			or descendant:IsA("Trail")
			or descendant:IsA("Sound")
			or descendant:IsA("LayerCollector")
			or descendant:IsA("LuaSourceContainer")
			or descendant:IsA("Humanoid")
			or descendant:IsA("Highlight")
		then
			table.insert(remove, descendant)
		end
	end
	for _, instance in remove do
		instance:Destroy()
	end
	Assets.HideMarkers(model, "Grip")
	Assets.MakeVisualOnly(model, true)
	Assets.ScaleTo(model, Tutorial.SilhouetteHeight, true)
	local highlight = Instance.new("Highlight")
	highlight.FillColor = Color3.new(0, 0, 0)
	highlight.FillTransparency = 0
	-- Outline in the Shiba's colour (edition colour for Shiny / Mythic): a teaser of what is coming.
	highlight.OutlineColor = shiba.Color
	highlight.OutlineTransparency = 0.2
	highlight.DepthMode = Enum.HighlightDepthMode.Occluded
	highlight.Parent = model
	return model
end

local function destroySilhouette()
	local current = silhouette
	if current then
		silhouette = nil
		current.Model:Destroy()
		current.Holder:Destroy()
		current.Gui:Destroy()
	end
end

-- The ground under a point, found by a ray down (ignoring characters and our own local parts).
local function groundBelow(point: Vector3, fallbackY: number): Vector3
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ignore: { Instance } = { localFolder }
	for _, other in Players:GetPlayers() do
		if other.Character then
			table.insert(ignore, other.Character)
		end
	end
	params.FilterDescendantsInstances = ignore
	local result = Workspace:Raycast(point + Vector3.new(0, 6, 0), Vector3.new(0, -30, 0), params)
	return if result then result.Position else Vector3.new(point.X, fallbackY, point.Z)
end

local function buildSilhouette(index: number, anchor: BasePart): Silhouette
	local shiba = EconomyConfig.Shibas[index]
	local model = silhouetteModel(shiba)
	-- Beside the Shiba Tier stand (stand-local X), standing on the ground.
	local side = anchor.CFrame * CFrame.new(Tutorial.SilhouetteSide, 0, 0)
	local ground = groundBelow(side.Position, anchor.Position.Y - Stations.StandHeight * 0.55)
	local boxCFrame, size = model:GetBoundingBox()
	local bottom = boxCFrame * CFrame.new(0, -size.Y / 2, 0)
	local pivotOffset = bottom:ToObjectSpace(model:GetPivot())
	model.Parent = localFolder

	local holder = Instance.new("Part")
	holder.Name = "NextShibaHolder"
	holder.Size = Vector3.one
	holder.Transparency = 1
	holder.Anchored = true
	holder.CanCollide = false
	holder.CanQuery = false
	holder.CanTouch = false
	holder.CFrame = CFrame.new(ground + Vector3.new(0, size.Y + 0.5, 0))
	holder.Parent = localFolder

	local gui = Instance.new("BillboardGui")
	gui.Name = "NextShibaBoard"
	gui.Adornee = holder
	gui.Size = UDim2.fromScale(6, 3.4)
	gui.StudsOffset = Vector3.new(0, 1.9, 0)
	gui.LightInfluence = 0
	gui.MaxDistance = Stations.BillboardMaxDistance
	gui.ResetOnSpawn = false
	gui.Parent = player:WaitForChild("PlayerGui")
	local title = text(gui, "NEXT:", UDim2.fromScale(0.05, 0), UDim2.fromScale(0.9, 0.26), GOLD)
	local name = text(gui, "???", UDim2.fromScale(0.05, 0.26), UDim2.fromScale(0.9, 0.24))
	local price = text(gui, "", UDim2.fromScale(0.1, 0.5), UDim2.fromScale(0.8, 0.24))
	local moneyBar = bar(gui, UDim2.fromScale(0.12, 0.78), UDim2.fromScale(0.76, 0.18), GOLD)

	return {
		Index = index,
		Anchor = anchor,
		Model = model,
		Holder = holder,
		Gui = gui,
		Title = title,
		Name = name,
		Price = price,
		Money = moneyBar,
		Ground = ground,
		PivotOffset = pivotOffset,
		Angle = 0,
	}
end

local function turnSilhouette(deltaTime: number)
	local current = silhouette
	if not current then
		return
	end
	current.Angle = (current.Angle + deltaTime * Tutorial.SilhouetteSpin) % (2 * math.pi)
	current.Model:PivotTo(CFrame.new(current.Ground) * CFrame.Angles(0, current.Angle, 0) * current.PivotOffset)
end

-- Shows the next Shiba (ShooterTier level + 2 in EconomyConfig.Shibas) next to the Shiba Tier stand.
local function refreshSilhouette(state: Types.PlayerState)
	local board = boards.ShooterTier
	local level = state.UpgradeLevels.ShooterTier or 0
	local index = level + 2
	local maxed = level >= Upgrades.GetMaxLevel("ShooterTier", state.Passes)
	if not board or maxed or not EconomyConfig.Shibas[index] then
		destroySilhouette()
		return
	end
	local current = silhouette
	if not current or current.Index ~= index or current.Anchor ~= board.Anchor then
		destroySilhouette()
		current = buildSilhouette(index, board.Anchor)
		silhouette = current
	end
	assert(current, "silhouette was just built")
	local shiba = EconomyConfig.Shibas[index]
	local cost = Upgrades.GetCost("ShooterTier", level)
	local affordable = state.BonkPoints >= cost
	-- The name is a surprise until you can afford it.
	current.Name.Text = if affordable then shiba.Name else "???"
	current.Name.TextColor3 = if affordable then shiba.Color else Theme.Text
	current.Price.TextColor3 = if affordable then AFFORDABLE else UNAFFORDABLE
	Widgets.SetMoneyText(current.Price, Format.Money(cost))
	setMoneyBar(current.Money, state.BonkPoints, cost)
end

-- Hints ------------------------------------------------------------------------------------------------------------

local function clearPath()
	local current = path
	if not current then
		return
	end
	path = nil
	current.Beam:Destroy()
	current.From:Destroy()
	current.To:Destroy()
end

-- Draws a glowing line from the character to a stand for a few seconds (and shows its arrow meanwhile).
local function showPath(id: string)
	clearPath()
	local board = boards[id]
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not board or not root or not root:IsA("BasePart") then
		return
	end
	local from = Instance.new("Attachment")
	from.Name = "StationPathFrom"
	from.Position = Vector3.new(0, -2, 0)
	from.Parent = root
	local to = Instance.new("Attachment")
	to.Name = "StationPathTo"
	to.Position = Vector3.new(0, -2.5, 0)
	to.Parent = board.Anchor
	local beam = Instance.new("Beam")
	beam.Attachment0 = from
	beam.Attachment1 = to
	beam.Width0 = 1.6
	beam.Width1 = 1.6
	beam.FaceCamera = true
	beam.LightEmission = 1
	beam.Color = ColorSequence.new(GOLD, AFFORDABLE)
	beam.Transparency = NumberSequence.new(0.15)
	beam.Parent = board.Anchor
	path = { Id = id, Beam = beam, From = from, To = to, EndsAt = os.clock() + Stations.PathSeconds }
end

-- The cheapest upgrade the player can buy right now (not locked), or nil.
local function cheapestAffordable(state: Types.PlayerState): string?
	local best: string? = nil
	local bestCost = math.huge
	for _, id in Upgrades.Order do
		local count = purchasable(state, id)
		local nextCost = if count > 0 then Upgrades.GetCost(id, state.UpgradeLevels[id] or 0) else math.huge
		if nextCost < bestCost then
			best = id
			bestCost = nextCost
		end
	end
	return best
end

local function onShowMeButton()
	local state = State.Get()
	local id = if state then cheapestAffordable(state) else nil
	if not id then
		HudController.Toast("Nothing affordable yet", "Info")
	elseif not boards[id] then
		HudController.Toast("Your upgrade stands are on your island", "Info")
	else
		showPath(id)
	end
end

local function hidePopup()
	popupTarget = nil
	popup.Visible = false
end

local function showPopup(id: string)
	popupTarget = id
	popupHideAt = os.clock() + Stations.PopupSeconds
	popupName.Text = Upgrades.Defs[id].DisplayName
	popupName.TextColor3 = Upgrades.Defs[id].Color
	popup.Visible = true
	local scale = popup:FindFirstChildOfClass("UIScale") or Instance.new("UIScale")
	scale.Parent = popup
	scale.Scale = 0.8
	TweenService:Create(scale, TweenInfo.new(0.2, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end

local function buildScreen()
	local gui = Widgets.Screen("StationHints", 5)

	-- Big round yellow button at the bottom centre: "show me the way to something I can buy".
	local showMe = Instance.new("TextButton")
	showMe.Name = "ShowUpgrade"
	showMe.AnchorPoint = Vector2.new(0.5, 1)
	showMe.Position = UDim2.new(0.5, 0, 1, -12)
	showMe.Size = UDim2.fromOffset(84, 84)
	showMe.BackgroundColor3 = Color3.fromRGB(255, 225, 40)
	showMe.AutoButtonColor = true
	showMe.Text = ""
	showMe.Parent = gui
	round(showMe, 0.5)
	Widgets.Stroke(showMe, 5, Color3.fromRGB(40, 36, 30))
	local arrow = arrowShape(showMe, Color3.fromRGB(40, 36, 30), true)
	arrow.Position = UDim2.fromScale(0.25, 0.18)
	arrow.Size = UDim2.fromScale(0.5, 0.64)
	showMe.Activated:Connect(onShowMeButton)

	-- "You can afford a new upgrade!" popup.
	popup = Instance.new("Frame")
	popup.Name = "AffordPopup"
	popup.AnchorPoint = Vector2.new(0.5, 0.5)
	popup.Position = UDim2.fromScale(0.5, 0.36)
	popup.Size = UDim2.fromOffset(440, 210)
	popup.BackgroundColor3 = Color3.fromRGB(14, 14, 18)
	popup.Visible = false
	popup.Parent = gui
	Widgets.Corner(popup, 18)
	Widgets.Stroke(popup, 6, Color3.fromRGB(60, 220, 90))
	local title = Widgets.Label(popup, "New upgrade!", 36, AFFORDABLE)
	title.Position = UDim2.fromOffset(0, 10)
	title.Size = UDim2.new(1, 0, 0, 44)
	title.TextXAlignment = Enum.TextXAlignment.Center
	title.TextStrokeTransparency = 0.4
	local line = Widgets.Label(popup, "You can afford a new upgrade!", 24)
	line.Position = UDim2.fromOffset(0, 56)
	line.Size = UDim2.new(1, 0, 0, 30)
	line.TextXAlignment = Enum.TextXAlignment.Center
	popupName = Widgets.Label(popup, "", 26)
	popupName.Position = UDim2.fromOffset(0, 88)
	popupName.Size = UDim2.new(1, 0, 0, 30)
	popupName.TextXAlignment = Enum.TextXAlignment.Center
	popupName.TextStrokeTransparency = 0.3
	local showButton = Widgets.Button(popup, "SHOW ME", Theme.Good, 28)
	showButton.AnchorPoint = Vector2.new(0.5, 1)
	showButton.Position = UDim2.new(0.5, 0, 1, -16)
	showButton.Size = UDim2.fromOffset(220, 56)
	showButton.Activated:Connect(function()
		local id = popupTarget
		hidePopup()
		if id then
			showPath(id)
		end
	end)
	local close = Widgets.Button(popup, "X", Theme.Bad, 26)
	close.AnchorPoint = Vector2.new(0.5, 0.5)
	close.Position = UDim2.new(1, -6, 0, 6)
	close.Size = UDim2.fromOffset(46, 46)
	close.Activated:Connect(hidePopup)
end

local function refreshBoard(board: Board, state: Types.PlayerState, hints: boolean)
	local id = board.Id
	local def = Upgrades.Defs[id]
	local level = state.UpgradeLevels[id] or 0
	local maxLevel = Upgrades.GetMaxLevel(id, state.Passes)
	local count, total, maxed = purchasable(state, id)
	local unlockAt = if maxed then nil else lockedUntil(state, id)

	board.Name.TextColor3 = if unlockAt then LOCKED else Theme.Text
	board.Value.Text = valueText(id, level)
	board.Value.TextColor3 = if unlockAt then LOCKED else valueColor(id, level)
	board.Badge.Text = `x{level}`
	board.Badge.BackgroundColor3 = if unlockAt then LOCKED else GOLD
	board.Level.Fill.Size = UDim2.fromScale(if maxLevel > 0 then level / maxLevel else 1, 1)
	board.Level.Fill.BackgroundColor3 = if unlockAt then LOCKED else def.Color
	board.Level.Text.Text = if maxed then "MAX" else `Level {level} / {maxLevel}`

	board.KeyHint.Visible = not maxed and unlockAt == nil
	board.Money.Frame.Visible = not maxed and unlockAt == nil
	if maxed then
		board.Button.BackgroundColor3 = GOLD
		board.ButtonText.Text = "MAXED"
		Widgets.SetMoneyText(board.Cost, "")
	elseif unlockAt then
		board.Button.BackgroundColor3 = LOCKED
		board.ButtonText.Text = "LOCKED"
		board.Cost.TextColor3 = UNAFFORDABLE
		Widgets.SetMoneyText(board.Cost, `unlocks with {shibaName(unlockAt)}`)
	elseif count > 0 then
		board.Button.BackgroundColor3 = BUTTON_READY
		board.ButtonText.Text = if count > 1 then `UPGRADE ×{count}` else "UPGRADE"
		board.Cost.TextColor3 = AFFORDABLE
		Widgets.SetMoneyText(board.Cost, Format.Money(total))
		setMoneyBar(board.Money, state.BonkPoints, Upgrades.GetCost(id, level))
	else
		board.Button.BackgroundColor3 = BUTTON_IDLE
		board.ButtonText.Text = "UPGRADE"
		board.Cost.TextColor3 = UNAFFORDABLE
		Widgets.SetMoneyText(board.Cost, Format.Money(total))
		setMoneyBar(board.Money, state.BonkPoints, total)
	end

	local pathHere = path ~= nil and path.Id == id
	board.Arrow.Enabled = pathHere or (hints and count > 0)
end

local function refresh()
	local state = State.Get()
	if not state then
		return
	end
	local hints = hintsOn(state)
	for _, board in boards do
		refreshBoard(board, state, hints)
	end
	local shrine = rebirthBoard
	if shrine then
		refreshRebirthBoard(shrine, state)
	end
	refreshSilhouette(state)

	local shooterCount, shooterCost, shootersMaxed = purchasable(state, "Shooters")
	if not shootersMaxed then
		local nextCost = if shooterCount > 0
			then Upgrades.GetCost("Shooters", state.UpgradeLevels.Shooters or 0)
			else shooterCost
		padCost.TextColor3 = if shooterCount > 0 then AFFORDABLE else UNAFFORDABLE
		Widgets.SetMoneyText(padCost, Format.Money(nextCost))
		setMoneyBar(padMoney, state.BonkPoints, nextCost)
	end

	-- While the guided tutorial runs it points the way itself (no popups over the screen).
	if not hints or Tutorial.IsGuiding(state) then
		if popupTarget then
			hidePopup()
		end
		return
	end
	if popupTarget then
		return
	end
	-- Once per upgrade level: pop up for the cheapest newly affordable one and count the others as shown too,
	-- so several affordable upgrades don't queue up a chain of popups.
	local newlyAffordable: { string } = {}
	for _, id in Upgrades.Order do
		local level = state.UpgradeLevels[id] or 0
		if boards[id] and popupShownFor[id] ~= level and (purchasable(state, id)) > 0 then
			table.insert(newlyAffordable, id)
		end
	end
	if #newlyAffordable == 0 then
		return
	end
	local target: string? = nil
	local targetCost = math.huge
	for _, id in newlyAffordable do
		popupShownFor[id] = state.UpgradeLevels[id] or 0
		local cost = Upgrades.GetCost(id, state.UpgradeLevels[id] or 0)
		if cost < targetCost then
			target = id
			targetCost = cost
		end
	end
	-- Standing right at the stand already: no need to point at it.
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if target and root and root:IsA("BasePart") then
		local distance = (root.Position - boards[target].Anchor.Position).Magnitude
		if distance > Stations.PromptDistance + 4 then
			showPopup(target)
		end
	end
end

-- Finds the stands of your island (they appear once your save is loaded and are rebuilt after a reset).
local function sync()
	local folder = stationsFolder()
	for id, board in boards do
		if not folder or board.Anchor.Parent ~= folder then
			if path and path.Id == id then
				clearPath()
			end
			destroyBoard(board)
			boards[id] = nil
		end
	end
	local shrine = rebirthBoard
	if shrine and (not folder or shrine.Anchor.Parent ~= folder) then
		shrine.Gui:Destroy()
		rebirthBoard = nil
	end
	if folder then
		for _, child in folder:GetChildren() do
			local name = child.Name
			if not child:IsA("BasePart") then
				continue
			end
			if name == Stations.RebirthAnchorName then
				if not rebirthBoard then
					rebirthBoard = buildRebirthBoard(child)
				end
			elseif string.sub(name, 1, #Stations.AnchorPrefix) == Stations.AnchorPrefix then
				local id = string.sub(name, #Stations.AnchorPrefix + 1)
				if Upgrades.Defs[id] and not boards[id] then
					boards[id] = buildBoard(id, child)
				end
			end
		end
	end
	local pad = if folder then folder:FindFirstChild(Stations.PadName) else nil
	if pad and pad:IsA("BasePart") then
		padPart = pad
		padGui.Adornee = pad
		padGui.Enabled = true
	else
		-- Maxed out (the server removes the pad) or no island.
		padPart = nil
		padGui.Enabled = false
	end
end

local function tick()
	sync()
	local current = path
	if current then
		local character = player.Character
		local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
		local board = boards[current.Id]
		local arrived = root ~= nil
			and root:IsA("BasePart")
			and board ~= nil
			and (root.Position - board.Anchor.Position).Magnitude < Stations.PathArriveDistance
		if os.clock() > current.EndsAt or arrived or not root or current.From.Parent ~= root then
			clearPath()
		end
	end
	if popupTarget and os.clock() > popupHideAt then
		hidePopup()
	end
	refresh()
end

local function isOwnPrompt(prompt: ProximityPrompt): boolean
	local folder = stationsFolder()
	return folder ~= nil and prompt:IsDescendantOf(folder)
end

local function startsWith(value: string, prefix: string): boolean
	return string.sub(value, 1, #prefix) == prefix
end

-- A prompt of any island's stands, pad or rebirth shrine (Islands.Island_<UserId>.Stations …).
local function isStationPrompt(prompt: ProximityPrompt): boolean
	if startsWith(prompt.Name, Stations.UpgradePromptPrefix) or startsWith(prompt.Name, Stations.RobuxPromptPrefix) then
		return true
	end
	local folder = prompt:FindFirstAncestor(Stations.FolderName)
	local island = if folder then folder.Parent else nil
	local islands = if island then island.Parent else nil
	return islands ~= nil and islands.Name == Gameplay.Island.FolderName
end

-- For TutorialController ------------------------------------------------------------------------------------------

-- The cheapest upgrade the player can buy right now (locked stands skipped), or nil.
function StationController.CheapestAffordable(state: Types.PlayerState): string?
	return cheapestAffordable(state)
end

-- The invisible prompt part of upgrade `id`'s stand on your island (the billboard sits above it), or nil.
function StationController.GetAnchor(id: string): BasePart?
	local board = boards[id]
	return if board then board.Anchor else nil
end

-- The NEW SHIBA pad on your island, or nil (maxed / no island).
function StationController.GetPad(): BasePart?
	return padPart
end

-- The visible stand of upgrade `id` (its prop model next to the anchor), for highlighting; the anchor if not found.
function StationController.GetStand(id: string): Instance?
	local board = boards[id]
	local folder = stationsFolder()
	if not board or not folder then
		return nil
	end
	local named = folder:FindFirstChild(`{Stations.PropPrefix}{id}`)
	if named then
		return named
	end
	local best: Instance = board.Anchor
	local bestDistance = 12
	for _, child in folder:GetChildren() do
		if child:IsA("Model") then
			local distance = (child:GetPivot().Position - board.Anchor.Position).Magnitude
			if distance < bestDistance then
				best = child
				bestDistance = distance
			end
		end
	end
	return best
end

function StationController.Init()
	localFolder = Instance.new("Folder")
	localFolder.Name = "LocalStationVisuals"
	localFolder.Parent = Workspace
	buildPadBoard()
	buildScreen()
end

function StationController.Start()
	State.Start()
	State.Changed:Connect(refresh)
	RunService.RenderStepped:Connect(turnSilhouette)

	-- Other players' stands are theirs: hide their prompts on this client (the server ignores them anyway).
	ProximityPromptService.PromptShown:Connect(function(prompt: ProximityPrompt)
		if isStationPrompt(prompt) and not isOwnPrompt(prompt) then
			prompt.Enabled = false
		end
	end)
	-- F on a stand: buy the next level with Robux (ShopService prompts the purchase and grants it).
	ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt)
		if startsWith(prompt.Name, Stations.RobuxPromptPrefix) and isOwnPrompt(prompt) then
			local id = string.sub(prompt.Name, #Stations.RobuxPromptPrefix + 1)
			if Upgrades.Defs[id] then
				Net.Get(Net.ShopBuy):FireServer(`{Stations.RobuxProductPrefix}{id}`)
			end
		end
	end)

	task.spawn(function()
		while true do
			tick()
			task.wait(LOOP_SECONDS)
		end
	end)
end

return StationController
