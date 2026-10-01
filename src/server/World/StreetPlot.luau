--!strict
-- The tycoon on a street plot (docs/GAME_DESIGN.md → "Gameplay flow"). Built under island.Model/Tycoon for the plot's owner:
-- - Stages: one per Shiba, one after the other away from the road. Stage n is as deep as its theme's Area (Config/TycoonDecor)
--   plus a margin, with a path through its middle. Shiba n stands at the stage-local point (-ShibaX, 0, 0) facing the path
--   (the stage frame is defined in Config/DecorTypes).
-- - A bay (Lane_<n>): a platform, the visual-only Shiba, an invisible click box (StreetGameService handles the click) and,
--   once automated, the Bonk Intern standing in front of the Shiba. The client draws the Shiba's menu, the swing and the
--   intern's ducking; there are no prompts or billboards on the Shiba.
-- - Decor: the pieces of every bought decor pad, built in the stage frame.
-- - Pads: glowing floor ovals (Util/TycoonSteps). The Shiba pad stands on the path at the front of its stage, the decor pads
--   in two lanes on the path, the Intern pad just before the Shiba pad. Stepping on one asks StreetGameService to buy it.
-- Everything here is visual or a request; StreetGameService validates every action and decides all money.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local TycoonDecor = require(ReplicatedStorage.Shared.Config.TycoonDecor)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local TycoonSteps = require(ReplicatedStorage.Shared.Util.TycoonSteps)
local Types = require(ReplicatedStorage.Shared.Types)

local StreetService = require(script.Parent.Parent.Services.StreetService)
local TycoonPlot = require(script.Parent.TycoonPlot)

local LANE = TycoonWorld.Lane
local LAYOUT = TycoonWorld.Street
local TEXT = TycoonWorld.Text

export type Actions = {
	SwingShiba: (player: Player, slot: number) -> (),
	BuyStep: (player: Player, stepId: string) -> (),
}

type BayRefs = {
	Folder: Folder,
	Ground: Vector3,
	Inward: Vector3,
	Platform: Part,
	SwingClick: ClickDetector,
	Visual: Model?,
	VisualKey: string?,
	Intern: Model?,
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
	-- Per bay: the height of its terrace above the plot's ground.
	Elev: { [number]: number },
	-- Per bay: how far from RoadEnd its stage starts and how deep it is (the theme's Area plus the margin).
	Starts: { [number]: number },
	Depths: { [number]: number },
	Bays: { [number]: BayRefs },
	Paths: { [number]: Part },
	Pads: { [string]: PadRefs },
	-- Built decor parts by step id (the ones whose step is bought).
	Decor: { [string]: Model },
}

local plots: { [Player]: Plot } = {}

local StreetPlot = {}

local PAD_AFFORDABLE = Color3.fromRGB(255, 220, 60)
local PAD_TOO_DEAR = Color3.fromRGB(125, 125, 135)
local PAD_BASE = Color3.fromRGB(40, 40, 48)
local PLATFORM_COLOR = Color3.fromRGB(95, 90, 110)
local SKIN = Color3.fromRGB(255, 214, 170)

-- Nothing on the plot glows (glow is for special effects only): Neon and ForceField are drawn as plain plastic.
local function flat(material: Enum.Material?): Enum.Material
	if material == nil or material == Enum.Material.Neon or material == Enum.Material.ForceField then
		return Enum.Material.SmoothPlastic
	end
	return material
end

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

local function areaOf(bay: number): Vector2
	local theme = TycoonDecor.Themes[bay]
	return if theme then theme.Area else LAYOUT.DefaultArea
end

-- The stage frame of a bay (Config/DecorTypes): origin on the path's centre line in the middle of the stage, +X = the plot's
-- right, -Z = deeper into the plot, +Y = up.
local function stageFrame(plot: Plot, bay: number): CFrame
	local middle = plot.Starts[bay] + plot.Depths[bay] / 2
	local at = plot.RoadEnd + plot.Back * middle + Vector3.new(0, plot.Elev[bay], 0)
	return CFrame.lookAt(at, at + plot.Back)
end

-- ==== terraces, stairs and walls =======================================================================================

local function solid(name: string, size: Vector3, cframe: CFrame, color: Color3, parent: Instance): Part
	local part = newPart(name, size, cframe, color, parent)
	part.CanCollide = true
	part.CanQuery = true
	return part
end

-- A box on the plot: `depth` away from the road, `lateral` to the right of the path, its bottom at `bottom` and top at `top`
-- (heights above the plot's ground), `length` along the plot and `width` across.
local function plotBox(
	plot: Plot,
	name: string,
	depth: number,
	lateral: number,
	length: number,
	width: number,
	bottom: number,
	top: number,
	color: Color3,
	parent: Instance
): Part
	local at = plot.RoadEnd + plot.Back * depth + plot.Right * lateral + Vector3.new(0, (bottom + top) / 2, 0)
	return solid(name, Vector3.new(width, top - bottom, length), CFrame.lookAt(at, at + plot.Back), color, parent)
end

-- The plot rises in terraces (one per group of Shibas) joined by stairs, and a privacy wall surrounds everything. All of it
-- is static, so it is built once with the plot.
local function buildTerrain(plot: Plot)
	local folder = Instance.new("Folder")
	folder.Name = "Terrain"
	folder.Parent = plot.Folder
	local group = LAYOUT.GroupSize
	local groups = math.ceil(TycoonSteps.Bays / group)
	local stairs = math.floor(LAYOUT.Rise / LAYOUT.StairRise + 0.5)
	local ramp = stairs * LAYOUT.StairRun
	local half = Street.PlotWidth / 2
	local thick = LAYOUT.WallThickness

	for number = 1, groups do
		local first = (number - 1) * group + 1
		local last = math.min(TycoonSteps.Bays, number * group)
		local height = plot.Elev[first]
		local from = if number == 1 then 0 else plot.Starts[first] - ramp
		local to = if number == groups then Street.PlotDepth else plot.Starts[last] + plot.Depths[last]

		if number > 1 then
			-- The terrace under this group's stages, and the stairs up to it.
			plotBox(
				plot,
				`Terrace{number}`,
				(plot.Starts[first] + plot.Starts[last] + plot.Depths[last]) / 2,
				0,
				plot.Starts[last] + plot.Depths[last] - plot.Starts[first],
				Street.PlotWidth,
				-1,
				height,
				LAYOUT.TerraceColor,
				folder
			)
			for step = 1, stairs do
				plotBox(
					plot,
					`Stair{number}_{step}`,
					plot.Starts[first] - ramp + (step - 0.5) * LAYOUT.StairRun,
					0,
					LAYOUT.StairRun,
					LAYOUT.StairWidth,
					-1,
					height - LAYOUT.Rise + step * LAYOUT.StairRise,
					LAYOUT.StairColor,
					folder
				)
			end
		end

		-- Side walls rise with the terrace.
		for _, side in { -1, 1 } do
			plotBox(
				plot,
				`Wall{number}_{if side < 0 then "L" else "R"}`,
				(from + to) / 2,
				side * (half - thick / 2),
				to - from,
				thick,
				-1,
				height + LAYOUT.WallHeight,
				LAYOUT.WallColor,
				folder
			)
		end
		if number == groups then
			plotBox(
				plot,
				"WallBack",
				Street.PlotDepth - thick / 2,
				0,
				thick,
				Street.PlotWidth,
				-1,
				height + LAYOUT.WallHeight,
				LAYOUT.WallColor,
				folder
			)
		end
	end

	-- Front wall with the entrance in the middle.
	local opening = LAYOUT.OpeningWidth / 2
	local wing = half - opening
	for _, side in { -1, 1 } do
		plotBox(
			plot,
			`WallFront{if side < 0 then "L" else "R"}`,
			LAYOUT.FrontWallDepth,
			side * (opening + wing / 2),
			thick,
			wing,
			-1,
			LAYOUT.WallHeight,
			LAYOUT.WallColor,
			folder
		)
	end
end

-- ==== bays =============================================================================================================

local function buildBay(plot: Plot, bay: number): BayRefs
	local owner = plot.Owner
	local actions = plot.Actions
	local frame = stageFrame(plot, bay)
	local ground = frame:PointToWorldSpace(Vector3.new(-LAYOUT.ShibaX, 0, 0))
	-- The Shiba faces the path (+X of the stage frame).
	local inward = frame.RightVector

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

	-- The client hangs the Shiba's menu on this point.
	local standPoint = ground + Vector3.new(0, LANE.PlatformTop, 0)
	local anchor = newPart("Anchor", Vector3.new(0.2, 0.2, 0.2), CFrame.new(standPoint), Color3.new(1, 1, 1), folder)
	anchor.Transparency = 1

	-- The click: an invisible box around the Shiba (the model is visual only). The server validates the click.
	local box = LANE.SwingBoxSize
	local swingPart =
		newPart("SwingPart", box, CFrame.new(standPoint + Vector3.new(0, box.Y / 2, 0)), Color3.new(1, 1, 1), folder)
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

	-- For the client's animation: Belt_<n> is an invisible part looking the way the Shiba faces.
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
		SwingClick = click,
		Visual = nil,
		VisualKey = nil,
		Intern = nil,
	}
end

-- The Bonk Intern: a simple NPC made of blocks, standing in front of the Shiba and facing it. Visual only; the client makes
-- it duck when the stick lands.
local function buildIntern(bay: BayRefs): Model
	local model = Instance.new("Model")
	model.Name = "Intern"
	local base = bay.Ground + bay.Inward * LAYOUT.InternDistance
	local frame = CFrame.lookAt(base, base - bay.Inward)
	local function piece(name: string, size: Vector3, offset: Vector3, color: Color3, shape: Enum.PartType?): Part
		local part = newPart(name, size, frame * CFrame.new(offset), color, model)
		if shape then
			part.Shape = shape
		end
		return part
	end
	piece("Legs", Vector3.new(1.8, 1.6, 1), Vector3.new(0, 0.8, 0), Color3.fromRGB(50, 55, 80))
	local body = piece("Body", Vector3.new(2.2, 2.2, 1.2), Vector3.new(0, 2.7, 0), Color3.fromRGB(245, 245, 250))
	piece("Tie", Vector3.new(0.35, 1.4, 0.15), Vector3.new(0, 2.9, -0.65), Color3.fromRGB(215, 50, 50))
	piece("Head", Vector3.new(1.9, 1.9, 1.9), Vector3.new(0, 4.5, 0), SKIN, Enum.PartType.Ball)
	piece("Cap", Vector3.new(2, 0.5, 2), Vector3.new(0, 5.35, 0), Color3.fromRGB(35, 40, 70))
	model.PrimaryPart = body
	model.Parent = bay.Folder
	return model
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
			local visual = TycoonPlot.BuildShibaVisual(bay, shiba)
			bay.Visual = visual
		end
	end

	-- Clicks are accepted while the Shiba exists (the server ignores them for automated Shibas).
	bay.SwingClick.MaxActivationDistance = if active then LAYOUT.ClickDistance else 0

	-- The Intern stands there as long as the Shiba is automated.
	local automated = active and shiba ~= nil and shiba.Automated == true
	if automated and not bay.Intern then
		bay.Intern = buildIntern(bay)
	elseif not automated and bay.Intern then
		bay.Intern:Destroy()
		bay.Intern = nil
	end
end

-- The path through the stage of `bay` (stage 1 also covers the way from the road).
local function ensurePath(plot: Plot, bay: number)
	if plot.Paths[bay] then
		return
	end
	local from = if bay == 1 then 0 else plot.Starts[bay]
	local to = plot.Starts[bay] + plot.Depths[bay]
	local middle = plot.RoadEnd + plot.Back * ((from + to) / 2) + Vector3.new(0, 0.05 + plot.Elev[bay], 0)
	plot.Paths[bay] = newPart(
		`Path{bay}`,
		Vector3.new(LAYOUT.PathWidth, 0.1, to - from),
		CFrame.lookAt(middle, middle + plot.Back),
		LAYOUT.PathColor,
		plot.Folder
	)
end

-- ==== decor ============================================================================================================

-- A bought decor part: a cloned Decor_<Key>_<PartId> model if the asset exists, else the part's primitive pieces.
local function buildDecor(plot: Plot, step: TycoonSteps.Step): Model?
	local theme = TycoonDecor.Themes[step.Bay]
	local index = step.PartIndex
	local part = if theme and index then theme.Parts[index] else nil
	if not theme or not part then
		return nil
	end
	local frame = stageFrame(plot, step.Bay)
	local assetName = `Decor_{theme.Key}_{part.Id}`
	local model: Model
	local cloned = if Assets.Has(assetName) then Assets.CloneModel(assetName) else nil
	if cloned then
		model = cloned
		Assets.MakeVisualOnly(model, true)
		model:PivotTo(frame)
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				descendant.Material = flat(descendant.Material)
			end
		end
	else
		model = Instance.new("Model")
		for number, piece in part.Pieces do
			local rotation = piece.Rotation or Vector3.zero
			local cframe = frame
				* CFrame.new(piece.Offset)
				* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
			local instance = newPart(`Piece{number}`, piece.Size, cframe, piece.Color, model)
			instance.Material = flat(piece.Material)
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

-- ==== pads =============================================================================================================

-- Where a pad stands, in the stage frame of its bay: the Shiba pad at the front of the stage on the path, the decor pads in
-- two lanes on the path (one per chain) from the front to the back, the Intern pad just before the Shiba pad.
local function padPosition(plot: Plot, step: TycoonSteps.Step): Vector3
	local frame = stageFrame(plot, step.Bay)
	local area = areaOf(step.Bay)
	local front = area.Y / 2 - LAYOUT.PadFrontInset
	if step.Kind == "Bay" then
		return frame:PointToWorldSpace(Vector3.new(0, 0, front))
	elseif step.Kind == "Automate" then
		return frame:PointToWorldSpace(Vector3.new(0, 0, area.Y / 2 - LAYOUT.AutoPadInset))
	end
	local index = step.PartIndex or 1
	local theme = TycoonDecor.Themes[step.Bay]
	local count = if theme then #theme.Parts else index
	local chain = (index - 1) % 2
	local row = math.floor((index - 1) / 2)
	local rows = math.ceil(count / 2)
	local span = area.Y - 2 * LAYOUT.PadFrontInset
	local z = if rows <= 1 then front else front - row * span / (rows - 1)
	return frame:PointToWorldSpace(Vector3.new(LAYOUT.DecorPadX[chain + 1], 0, z))
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
	pad.Part.Color = if money >= price then PAD_AFFORDABLE else PAD_TOO_DEAR
end

-- ==== public ===========================================================================================================

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

	-- The stages follow each other from the road: stage n is as deep as its theme plus the margin.
	local starts: { [number]: number } = {}
	local depths: { [number]: number } = {}
	-- Every GroupSize-th Shiba stands on the next terrace: a staircase is inserted before its stage.
	local elev: { [number]: number } = {}
	local ramp = math.floor(LAYOUT.Rise / LAYOUT.StairRise + 0.5) * LAYOUT.StairRun
	local depth = LAYOUT.FirstStageDepth
	for bay = 1, TycoonSteps.Bays do
		if bay > 1 and (bay - 1) % LAYOUT.GroupSize == 0 then
			depth += ramp
		end
		starts[bay] = depth
		elev[bay] = math.floor((bay - 1) / LAYOUT.GroupSize) * LAYOUT.Rise
		depths[bay] = areaOf(bay).Y + LAYOUT.StageMargin
		depth += depths[bay]
	end

	plots[player] = {
		Owner = player,
		Folder = folder,
		Actions = actions,
		RoadEnd = island.Center + towardRoad * (Street.PlotDepth / 2),
		Back = back,
		Right = back:Cross(Vector3.yAxis),
		Elev = elev,
		Starts = starts,
		Depths = depths,
		Bays = {},
		Paths = {},
		Pads = {},
		Decor = {},
	}
	buildTerrain(plots[player])
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
		ensurePath(plot, index)
		refreshBay(bay, tycoon, index)
	end

	refreshDecor(plot, tycoon)

	-- The pads of the flow (Util/TycoonSteps): Shibas, required decor and the optional interns.
	local wanted: { [string]: boolean } = {}
	for _, step in TycoonSteps.Visible(tycoon) do
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

-- Where the Shiba of bay `slot` stands and which way it faces (the hit zone is in front of it), for the server's hit check.
function StreetPlot.GetLaneAim(player: Player, slot: number): { Origin: Vector3, Forward: Vector3 }?
	local plot = plots[player]
	local bay = if plot then plot.Bays[slot] else nil
	if not bay then
		return nil
	end
	return { Origin = bay.Ground + Vector3.new(0, LANE.PlatformTop, 0), Forward = bay.Inward }
end

return StreetPlot
