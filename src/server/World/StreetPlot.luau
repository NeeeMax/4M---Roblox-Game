--!strict
-- The tycoon on a street plot (docs/GAME_DESIGN.md → Street, plots and buttons, "One Shiba per expansion"). Built under
-- island.Model/Tycoon for the plot's owner only (the island tycoon's TycoonPlot is used without the street):
-- - Bays: two per row, left and right of a path that leads away from the road. Bay n holds Shiba n (tier n - 1). A bay is
--   built when its Shiba exists; the rows appear one after another, so the plot grows backward.
-- - Pads: glowing floor ovals, at most Street.MaxPads at a time (Util/TycoonSteps): the next expansion at the end of the
--   path and the Cash Register (automation) beside each Shiba. Stepping on one asks TycoonService to buy it.
-- - On a Shiba: click / tap / Q swings, E levels up (F = 10 levels). The client draws the swing (TycoonController) and
--   finds Lane_<n>/Shiba and Belt_<n> (an invisible part whose LookVector is the direction the Shiba faces).
-- Everything is visual or a request; TycoonService validates every action and decides all money.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local TycoonConfig = require(ReplicatedStorage.Shared.Config.Tycoon)
local TycoonDecor = require(ReplicatedStorage.Shared.Config.TycoonDecor)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local TycoonSteps = require(ReplicatedStorage.Shared.Util.TycoonSteps)
local Types = require(ReplicatedStorage.Shared.Types)

local StreetService = require(script.Parent.Parent.Services.StreetService)
local TycoonPlot = require(script.Parent.TycoonPlot)

local LANE = TycoonWorld.Lane
local LAYOUT = TycoonWorld.Street
local TEXT = TycoonWorld.Text

export type Actions = {
	UpgradeShiba: (player: Player, slot: number, quantity: number) -> (),
	SwingShiba: (player: Player, slot: number) -> (),
	BuyStep: (player: Player, stepId: string) -> (),
}

type BayRefs = {
	Folder: Folder,
	Ground: Vector3,
	Inward: Vector3,
	Platform: Part,
	Gui: BillboardGui,
	Title: TextLabel,
	Sub: TextLabel,
	Hint: TextLabel,
	SwingClick: ClickDetector,
	SwingPrompt: ProximityPrompt,
	LevelPrompt: ProximityPrompt,
	BigLevelPrompt: ProximityPrompt,
	Visual: Model?,
	VisualKey: string?,
}

type PadRefs = {
	Folder: Folder,
	Part: Part,
	Title: TextLabel,
	Desc: TextLabel,
	Price: TextLabel,
	Busy: boolean,
}

type Plot = {
	Owner: Player,
	Folder: Folder,
	Actions: Actions,
	-- Where the plot meets the road (on the centre line), the direction away from the road and the owner's right.
	RoadEnd: Vector3,
	Back: Vector3,
	Right: Vector3,
	Bays: { [number]: BayRefs },
	Paths: { [number]: Part },
	Pads: { [string]: PadRefs },
	-- Built decor parts by step id, and the last set of "near" themed bays (see NearDecorBays) as a string.
	Decor: { [string]: Model },
	NearKey: string,
}

local plots: { [Player]: Plot } = {}

local StreetPlot = {}

local PAD_AFFORDABLE = Color3.fromRGB(255, 220, 60)
local PAD_TOO_DEAR = Color3.fromRGB(125, 125, 135)
local PAD_BASE = Color3.fromRGB(40, 40, 48)
local PLATFORM_COLOR = Color3.fromRGB(95, 90, 110)

-- ==== small helpers ====================================================================================================

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

local function newPart(name: string, size: Vector3, cframe: CFrame, color: Color3, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

local function setText(label: TextLabel, text: string)
	if label.Text ~= text then
		label.Text = text
	end
end

local function setPrompt(prompt: ProximityPrompt, enabled: boolean, actionText: string?)
	if actionText and prompt.ActionText ~= actionText then
		prompt.ActionText = actionText
	end
	if prompt.Enabled ~= enabled then
		prompt.Enabled = enabled
	end
end

local function position(plot: Plot, depth: number, lateral: number): Vector3
	return plot.RoadEnd + plot.Back * depth + plot.Right * lateral
end

local function rowOf(bay: number): number
	return math.ceil(bay / 2)
end

local function rowDepth(row: number): number
	return LAYOUT.FirstRowDepth + (row - 1) * LAYOUT.RowPitch
end

-- Odd bays stand left of the path, even ones right.
local function sideOf(bay: number): number
	return if bay % 2 == 1 then -1 else 1
end

-- ==== bays =============================================================================================================

local function buildBay(plot: Plot, bay: number): BayRefs
	local owner = plot.Owner
	local actions = plot.Actions
	local side = sideOf(bay)
	local depth = rowDepth(rowOf(bay))
	local ground = position(plot, depth, side * LAYOUT.ShibaOffset)
	local inward = (position(plot, depth, 0) - ground).Unit

	local folder = Instance.new("Folder")
	folder.Name = `Lane_{bay}`

	local platform = newPart(
		"Platform",
		Vector3.new(LANE.PlatformTop, LAYOUT.PlatformDiameter, LAYOUT.PlatformDiameter),
		CFrame.new(ground + Vector3.new(0, LANE.PlatformTop / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		PLATFORM_COLOR,
		folder
	)
	platform.Shape = Enum.PartType.Cylinder
	platform.Material = Enum.Material.Slate
	platform.Transparency = 1

	-- Info billboard above the Shiba.
	local standPoint = ground + Vector3.new(0, LANE.PlatformTop, 0)
	local anchor = newPart("Anchor", Vector3.new(0.2, 0.2, 0.2), CFrame.new(standPoint), Color3.new(1, 1, 1), folder)
	anchor.Transparency = 1
	local gui, labels = TycoonPlot.NewBillboard(anchor, 240, 8, LANE.BillboardDistance, {
		{ Name = "Title", Height = 24, TextSize = 22, Color = TEXT.Title },
		{ Name = "Sub", Height = 20, TextSize = 18, Color = TEXT.Income },
		{ Name = "Hint", Height = 16, TextSize = 14, Color = TEXT.Hint },
	})

	-- The Shiba itself: an invisible box takes the click (the model is visual only); Q swings, E / F level up.
	local boxSize = LANE.SwingBoxSize
	local swingPart = newPart(
		"SwingPart",
		boxSize,
		CFrame.new(standPoint + Vector3.new(0, boxSize.Y / 2, 0)),
		Color3.new(1, 1, 1),
		folder
	)
	swingPart.Transparency = 1
	swingPart.CanQuery = true
	local click = Instance.new("ClickDetector")
	click.MaxActivationDistance = 0
	click.Parent = swingPart
	click.MouseClick:Connect(function(clicker: Player)
		if clicker == owner then
			actions.SwingShiba(owner, bay)
		end
	end)
	local swingPrompt = TycoonPlot.NewPrompt(
		owner,
		swingPart,
		"Tycoon_Swing",
		Enum.KeyCode.Q,
		Enum.KeyCode.ButtonR1,
		"Shiba",
		0,
		LANE.PromptDistance,
		function()
			actions.SwingShiba(owner, bay)
		end
	)
	local levelPrompt = TycoonPlot.NewPrompt(
		owner,
		swingPart,
		"Tycoon_LevelUp",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		"Shiba",
		LANE.LevelHoldSeconds,
		LANE.PromptDistance,
		function()
			actions.UpgradeShiba(owner, bay, 1)
		end
	)
	local bigLevelPrompt = TycoonPlot.NewPrompt(
		owner,
		swingPart,
		"Tycoon_LevelUp10",
		Enum.KeyCode.F,
		Enum.KeyCode.ButtonY,
		"Shiba",
		LANE.LevelHoldSeconds,
		LANE.PromptDistance,
		function()
			actions.UpgradeShiba(owner, bay, LANE.BigLevelStep)
		end
	)

	-- For the client's swing animation: Belt_<n> is an invisible part looking the way the Shiba faces.
	local belt = newPart(
		`Belt_{bay}`,
		Vector3.new(1, 0.2, 1),
		CFrame.lookAt(standPoint, standPoint + inward),
		Color3.new(1, 1, 1),
		plot.Folder
	)
	belt.Transparency = 1

	folder.Parent = plot.Folder
	return {
		Folder = folder,
		Ground = ground,
		Inward = inward,
		Platform = platform,
		Gui = gui,
		Title = labels.Title,
		Sub = labels.Sub,
		Hint = labels.Hint,
		SwingClick = click,
		SwingPrompt = swingPrompt,
		LevelPrompt = levelPrompt,
		BigLevelPrompt = bigLevelPrompt,
		Visual = nil,
		VisualKey = nil,
	}
end

local function refreshBay(bay: BayRefs, tycoon: Types.TycoonState, index: number)
	local id = tycoon.Equipped[tostring(index)]
	local shiba = if id then tycoon.Shibas[id] else nil
	local def = if shiba then EconomyConfig.Shibas[shiba.Tier + 1] else nil
	local active = shiba ~= nil and id ~= nil and def ~= nil

	bay.Platform.Transparency = if active then 0 else 1
	if def then
		bay.Platform.Color = def.Color
	end

	-- Shiba visual: swap only when (id, tier, variant) changed.
	local key = if shiba and id then `{id}:{shiba.Tier}:{shiba.Variant}` else nil
	if key ~= bay.VisualKey then
		if bay.Visual then
			bay.Visual:Destroy()
			bay.Visual = nil
		end
		bay.VisualKey = key
		if shiba then
			local visual, height = TycoonPlot.BuildShibaVisual(bay, shiba)
			bay.Visual = visual
			bay.Gui.StudsOffset = Vector3.new(0, height + LANE.BillboardGap, 0)
		end
	end
	bay.Gui.Enabled = active

	if shiba and def then
		local name = def.Name
		if shiba.Variant ~= "Normal" then
			name = `{shiba.Variant} {name}`
		end
		if shiba.Automated == true then
			name = `{name} [AUTO]`
		end
		local income = TycoonMath.LaneIncome(tycoon, index) * TycoonMath.GlobalMultiplier(tycoon)
		setText(bay.Title, name)
		setText(
			bay.Sub,
			`Lv {shiba.Level}  |  {Format.Money(income)}/s  |  {string.format("%.1f", TycoonMath.SwingTimer(shiba.Tier))}s`
		)
		setText(bay.Hint, if shiba.Automated == true then "" else "Click me!")

		local cap = TycoonMath.LevelCap(tycoon.Ascensions)
		local level = shiba.Level
		local canLevel = level < cap
		setPrompt(
			bay.LevelPrompt,
			canLevel,
			if canLevel
				then `Level {level + 1} - {Format.Money(TycoonMath.LevelCost(shiba.Tier, level))}`
				else "Max level"
		)
		local levels, spent = TycoonMath.LevelUpPlan(shiba.Tier, level, LANE.BigLevelStep, math.huge, cap)
		setPrompt(
			bay.BigLevelPrompt,
			levels > 1,
			if levels > 1 then `+{levels} levels - {Format.Money(spent)}` else nil
		)
	else
		setPrompt(bay.LevelPrompt, false, nil)
		setPrompt(bay.BigLevelPrompt, false, nil)
	end

	local manual = active and shiba ~= nil and shiba.Automated ~= true
	setPrompt(bay.SwingPrompt, manual, if manual then "Bonk!" else nil)
	bay.SwingClick.MaxActivationDistance = if manual then LANE.PromptDistance + 6 else 0
end

-- The stretch of path in front of the bays of `row` (row 1 also covers the way from the road).
local function ensurePath(plot: Plot, row: number)
	if plot.Paths[row] then
		return
	end
	local from = if row == 1 then 0 else rowDepth(row) - LAYOUT.RowPitch / 2
	local to = rowDepth(row) + LAYOUT.RowPitch / 2
	local middle = position(plot, (from + to) / 2, 0) + Vector3.new(0, 0.05, 0)
	plot.Paths[row] = newPart(
		`Path{row}`,
		Vector3.new(LAYOUT.PathWidth, 0.1, to - from),
		CFrame.lookAt(middle, middle + plot.Back),
		LAYOUT.PathColor,
		plot.Folder
	)
end

-- ==== pads =============================================================================================================

-- Ground point of a theme's anchor: beside the Shiba's bay, away from the path, on the bay's row depth.
local function decorAnchor(plot: Plot, bay: number): Vector3?
	local theme = TycoonDecor.Themes[bay]
	if not theme then
		return nil
	end
	local depth = rowDepth(rowOf(bay)) + theme.Depth
	return position(plot, depth, sideOf(bay) * (LAYOUT.ShibaOffset + theme.Outward))
end

local function padPosition(plot: Plot, step: TycoonSteps.Step): Vector3
	local row = rowOf(step.Bay)
	if step.Kind == "Decor" then
		local theme = TycoonDecor.Themes[step.Bay]
		local anchor = decorAnchor(plot, step.Bay)
		if theme and anchor then
			return anchor + plot.Right * (sideOf(step.Bay) * theme.PadOffset.X) + plot.Back * theme.PadOffset.Z
		end
		return position(plot, rowDepth(row), 0)
	end
	if step.Kind == "Bay" then
		-- The next expansion: on the path just before the new row.
		return position(plot, rowDepth(row) - LAYOUT.RowPitch / 2, 0)
	end
	-- The Cash Register: on the path beside its Shiba.
	return position(plot, rowDepth(row), sideOf(step.Bay) * LAYOUT.AutoPadOffset)
end

local function buildPad(plot: Plot, step: TycoonSteps.Step): PadRefs
	local owner = plot.Owner
	local at = padPosition(plot, step)
	local folder = Instance.new("Folder")
	folder.Name = `Pad_{step.Id}`
	local rotation = CFrame.Angles(0, 0, math.rad(90))

	local base = newPart(
		"PadBase",
		Vector3.new(0.3, LAYOUT.PadBaseDiameter, LAYOUT.PadBaseDiameter),
		CFrame.new(at + Vector3.new(0, 0.2, 0)) * rotation,
		PAD_BASE,
		folder
	)
	base.Shape = Enum.PartType.Cylinder

	local part = newPart(
		"Pad",
		Vector3.new(LAYOUT.PadHeight, LAYOUT.PadDiameter, LAYOUT.PadDiameter),
		CFrame.new(at + Vector3.new(0, 0.35 + LAYOUT.PadHeight / 2, 0)) * rotation,
		PAD_TOO_DEAR,
		folder
	)
	part.Shape = Enum.PartType.Cylinder
	part.Material = Enum.Material.Neon
	part.CanTouch = true

	local gui, labels = TycoonPlot.NewBillboard(part, 260, 5, LAYOUT.PadBillboardDistance, {
		{ Name = "Title", Height = 26, TextSize = 22, Color = TEXT.Title },
		{ Name = "Desc", Height = 18, TextSize = 15, Color = TEXT.Muted },
		{ Name = "Price", Height = 26, TextSize = 22, Color = TEXT.Income },
	})
	gui.Enabled = true

	local pad: PadRefs = {
		Folder = folder,
		Part = part,
		Title = labels.Title,
		Desc = labels.Desc,
		Price = labels.Price,
		Busy = false,
	}
	part.Touched:Connect(function(hit: BasePart)
		if pad.Busy then
			return
		end
		local character = hit.Parent
		local toucher = if character then Players:GetPlayerFromCharacter(character) else nil
		if toucher ~= owner then
			return
		end
		pad.Busy = true
		plot.Actions.BuyStep(owner, step.Id)
		task.delay(LAYOUT.PadCooldown, function()
			pad.Busy = false
		end)
	end)

	folder.Parent = plot.Folder
	return pad
end

local function refreshPad(pad: PadRefs, step: TycoonSteps.Step, tycoon: Types.TycoonState, money: number)
	local price = TycoonSteps.Price(step, tycoon)
	setText(pad.Title, TycoonSteps.Title(step))
	setText(pad.Desc, TycoonSteps.Description(step))
	setText(pad.Price, if price <= 0 then "FREE" else Format.Money(price))
	local affordable = money >= price
	pad.Part.Color = if affordable then PAD_AFFORDABLE else PAD_TOO_DEAR
end

-- ==== decor ============================================================================================================

-- A bought decor part: a cloned Decor_<Key>_<PartId> model if the asset exists, else the part's primitive pieces.
local function buildDecor(plot: Plot, step: TycoonSteps.Step): Model?
	local theme = TycoonDecor.Themes[step.Bay]
	local index = step.PartIndex
	local part = if theme and index then theme.Parts[index] else nil
	local anchor = decorAnchor(plot, step.Bay)
	if not theme or not part or not anchor then
		return nil
	end
	local frame = CFrame.lookAt(anchor, anchor + plot.Back)
	local assetName = `Decor_{theme.Key}_{part.Id}`
	local model: Model
	local cloned = if Assets.Has(assetName) then Assets.CloneModel(assetName) else nil
	if cloned then
		model = cloned
		Assets.MakeVisualOnly(model, true)
		model:PivotTo(frame)
	else
		model = Instance.new("Model")
		for number, piece in part.Pieces do
			local rotation = piece.Rotation or Vector3.zero
			local cframe = frame
				* CFrame.new(piece.Offset)
				* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
			local instance = newPart(`Piece{number}`, piece.Size, cframe, piece.Color, model)
			instance.Material = piece.Material or Enum.Material.SmoothPlastic
			instance.Shape = piece.Shape or Enum.PartType.Block
		end
	end
	model.Name = `Decor_{step.Id}`
	model.Parent = plot.Folder
	return model
end

-- Decor parts of the bought steps exist, all others are removed.
local function refreshDecor(plot: Plot, tycoon: Types.TycoonState)
	for _, step in TycoonSteps.DecorList do
		local built = plot.Decor[step.Id]
		if TycoonSteps.IsBought(tycoon, step.Id) then
			if not built then
				local model = buildDecor(plot, step)
				if model then
					plot.Decor[step.Id] = model
				end
			end
		elseif built then
			built:Destroy()
			plot.Decor[step.Id] = nil
		end
	end
end

-- The themed bays whose anchor the owner's character is within Street.DecorShowDistance of (only bays already bought).
local function nearDecorBays(plot: Plot, tycoon: Types.TycoonState): { [number]: boolean }
	local near: { [number]: boolean } = {}
	local character = plot.Owner.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not root or not root:IsA("BasePart") then
		return near
	end
	local limit = TycoonConfig.Street.DecorShowDistance
	for bay in TycoonDecor.Themes do
		local anchor = decorAnchor(plot, bay)
		if anchor and TycoonSteps.IsBought(tycoon, `Bay{bay}`) and (root.Position - anchor).Magnitude <= limit then
			near[bay] = true
		end
	end
	return near
end

local function nearKey(near: { [number]: boolean }): string
	local bays: { number } = {}
	for bay in near do
		table.insert(bays, bay)
	end
	table.sort(bays)
	return table.concat(bays, ",")
end

-- ==== public ===========================================================================================================

-- Which themed bays the owner is near right now (the rule that shows decor pads), for TycoonService.BuyStep.
function StreetPlot.NearDecorBays(player: Player, state: Types.PlayerState): { [number]: boolean }
	local plot = plots[player]
	local tycoon = state.Tycoon
	if not plot or not tycoon then
		return {}
	end
	return nearDecorBays(plot, tycoon)
end

-- True when the set of near themed bays differs from the one the last Refresh drew (cheap: a few distance checks), so the
-- caller only calls Refresh when a decor pad has to appear or vanish.
function StreetPlot.DecorProximityChanged(player: Player, state: Types.PlayerState): boolean
	local plot = plots[player]
	local tycoon = state.Tycoon
	if not plot or not tycoon or plot.Folder.Parent == nil then
		return false
	end
	return nearKey(nearDecorBays(plot, tycoon)) ~= plot.NearKey
end

function StreetPlot.Destroy(player: Player)
	local plot = plots[player]
	plots[player] = nil
	if plot then
		plot.Folder:Destroy()
	end
end

-- Creates the plot's (still empty) folder under island.Model; call Refresh with the state afterwards.
function StreetPlot.Build(player: Player, island: StreetService.Island, actions: Actions)
	StreetPlot.Destroy(player)
	local folder = Instance.new("Folder")
	folder.Name = TycoonWorld.FolderName
	local towardRoad = direction(island.HubAngle)
	local back = -towardRoad
	plots[player] = {
		Owner = player,
		Folder = folder,
		Actions = actions,
		RoadEnd = island.Center + towardRoad * (Street.PlotDepth / 2),
		Back = back,
		Right = back:Cross(Vector3.yAxis),
		Bays = {},
		Paths = {},
		Pads = {},
		Decor = {},
		NearKey = "",
	}
	folder.Parent = island.Model
end

function StreetPlot.Refresh(player: Player, state: Types.PlayerState)
	local plot = plots[player]
	local tycoon = state.Tycoon
	if not plot or not tycoon then
		return
	end
	if plot.Folder.Parent == nil then
		-- The island is gone (the player left): drop the plot.
		return
	end

	for index = 1, tycoon.EquipSlots do
		local bay = plot.Bays[index]
		if not bay then
			bay = buildBay(plot, index)
			plot.Bays[index] = bay
		end
		ensurePath(plot, rowOf(index))
		refreshBay(bay, tycoon, index)
	end

	refreshDecor(plot, tycoon)
	local near = nearDecorBays(plot, tycoon)
	plot.NearKey = nearKey(near)

	-- Walkthrough pads (max Street.MaxPads) plus the decor pads of the themes the owner is near.
	local visible = TycoonSteps.Visible(tycoon)
	for _, step in TycoonSteps.VisibleDecor(tycoon, near) do
		table.insert(visible, step)
	end
	local wanted: { [string]: boolean } = {}
	for _, step in visible do
		wanted[step.Id] = true
		local pad = plot.Pads[step.Id]
		if not pad then
			pad = buildPad(plot, step)
			plot.Pads[step.Id] = pad
		end
		refreshPad(pad, step, tycoon, state.BonkPoints)
	end
	for id, pad in plot.Pads do
		if not wanted[id] then
			pad.Folder:Destroy()
			plot.Pads[id] = nil
		end
	end
end

-- Where the Shiba of bay `slot` stands and which way it faces, for the server's Bonk hit check.
function StreetPlot.GetLaneAim(player: Player, slot: number): { Origin: Vector3, Forward: Vector3 }?
	local plot = plots[player]
	local bay = if plot then plot.Bays[slot] else nil
	if not bay then
		return nil
	end
	return { Origin = bay.Ground + Vector3.new(0, LANE.PlatformTop, 0), Forward = bay.Inward }
end

return StreetPlot
