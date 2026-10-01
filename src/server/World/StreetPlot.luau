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
local Workspace = game:GetService("Workspace")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ShibaPlatforms = require(ReplicatedStorage.Shared.Config.ShibaPlatforms)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local TycoonDecor = require(ReplicatedStorage.Shared.Config.TycoonDecor)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local StreetLayout = require(ReplicatedStorage.Shared.Util.StreetLayout)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
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
	-- The Shiba's platform (Config/ShibaPlatforms, built per tier), its invisible barrier, and what moves with its height.
	PlatformKey: string?,
	PlatformFolder: Instance?,
	Anchor: Part,
	SwingPart: Part,
	Belt: Part,
	-- Height of the standing surface above the ground and the barrier's radius (the Intern stands outside it).
	Top: number,
	Radius: number,
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
	-- False until the first Refresh is done: what exists then was there before (a rejoin), only later things pop in.
	Ready: boolean,
	-- The street slot and how many stages the walled cell covers (StreetService.SetReach).
	Slot: number,
	WallReach: number,
	Folder: Folder,
	Actions: Actions,
	-- Where the plot meets the road (on the centre line), the direction away from the road and the owner's right.
	RoadEnd: Vector3,
	Back: Vector3,
	Right: Vector3,
	-- Per bay: the height of its terrace above the plot's ground.
	Elev: { [number]: number },
	-- Built terraces by group number (Refresh).
	Terrain: { [number]: Folder },
	-- Per bay: how far from RoadEnd its stage starts and how deep it is (the theme's Area plus the margin).
	Starts: { [number]: number },
	Depths: { [number]: number },
	Bays: { [number]: BayRefs },
	Paths: { [number]: Folder },
	Pads: { [string]: PadRefs },
	-- Built decor parts by step id (the ones whose step is bought).
	Decor: { [string]: Model },
}

local plots: { [Player]: Plot } = {}

local StreetPlot = {}

local PAD_AFFORDABLE = Color3.fromRGB(255, 220, 60)
local PAD_TOO_DEAR = Color3.fromRGB(125, 125, 135)
local PAD_BASE = Color3.fromRGB(40, 40, 48)
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

-- Where the Shiba of a bay stands and which way it faces (Config/DecorTypes → ShibaSpot).
local function shibaSpot(bay: number): TycoonDecor.ShibaSpot
	local theme = TycoonDecor.Themes[bay]
	local spot = if theme then theme.Shiba else nil
	return spot or { Position = Vector2.new(-LAYOUT.ShibaX, 0), Facing = 0 }
end

local function facingVector(degrees: number): Vector3
	local radians = math.rad(degrees)
	return Vector3.new(math.cos(radians), 0, -math.sin(radians))
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

-- The plot rises in terraces (one per group of Shibas) joined by stairs. They grow with the player: group `number` (2 and up)
-- appears when its first Shiba becomes available, so the pad of that Shiba stands on its terrace (Refresh decides when).
local function groupCount(): number
	return math.ceil(TycoonSteps.Bays / LAYOUT.GroupSize)
end

local function buildGroup(plot: Plot, number: number): Folder
	local folder = Instance.new("Folder")
	folder.Name = `Terrain{number}`
	local first = (number - 1) * LAYOUT.GroupSize + 1
	local last = math.min(TycoonSteps.Bays, number * LAYOUT.GroupSize)
	local height = plot.Elev[first]
	local stairs = math.floor(LAYOUT.Rise / LAYOUT.StairRise + 0.5)
	local ramp = stairs * LAYOUT.StairRun
	local to = plot.Starts[last] + plot.Depths[last]

	plotBox(
		plot,
		"Terrace",
		(plot.Starts[first] + to) / 2,
		0,
		to - plot.Starts[first],
		Street.PlotWidth,
		-1,
		height,
		LAYOUT.TerraceColor,
		folder
	)
	for step = 1, stairs do
		plotBox(
			plot,
			`Stair{step}`,
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
	for _, part in folder:GetChildren() do
		if part:IsA("BasePart") then
			part.Material = LAYOUT.TerraceMaterial
		end
	end
	folder.Parent = plot.Folder
	return folder
end

-- Builds the terrain of every group that is reached (`reached` = the highest Shiba available) and removes the rest.
local function refreshTerrain(plot: Plot, reached: number)
	for number = 2, groupCount() do
		local built = plot.Terrain[number]
		if reached >= (number - 1) * LAYOUT.GroupSize + 1 then
			if not built then
				plot.Terrain[number] = buildGroup(plot, number)
			end
		elseif built then
			built:Destroy()
			plot.Terrain[number] = nil
		end
	end
end

-- ==== bays =============================================================================================================

local function buildBay(plot: Plot, bay: number): BayRefs
	local owner = plot.Owner
	local actions = plot.Actions
	local frame = stageFrame(plot, bay)
	local spot = shibaSpot(bay)
	local ground = frame:PointToWorldSpace(Vector3.new(spot.Position.X, 0, spot.Position.Y))
	local inward = frame:VectorToWorldSpace(facingVector(spot.Facing))

	local folder = Instance.new("Folder")
	folder.Name = `Lane_{bay}`

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
		PlatformKey = nil,
		PlatformFolder = nil,
		Anchor = anchor,
		SwingPart = swingPart,
		Belt = belt,
		Top = LANE.PlatformTop,
		Radius = LAYOUT.PlatformDiameter / 2,
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
	local base = bay.Ground + bay.Inward * (bay.Radius + LAYOUT.InternGap)
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

-- The platform's pieces around `frame` (on the ground, -Z = the way the Shiba faces).
local function buildPlatformParts(platform: ShibaPlatforms.Platform, frame: CFrame, parent: Instance): Model
	local folder = Instance.new("Model")
	folder.Name = "Platform"
	for index, piece in platform.Pieces do
		local cframe = frame * CFrame.new(piece.Offset) * CFrame.Angles(0, math.rad(piece.Yaw or 0), 0)
		local size = piece.Size
		local part = newPart(`Piece{index}`, size, cframe, piece.Color, folder)
		if piece.Shape == "Cylinder" then
			-- A cylinder's axis is its X axis, so lay the height along X and stand it up.
			part.Shape = Enum.PartType.Cylinder
			part.Size = Vector3.new(size.Y, size.X, size.X)
			part.CFrame = cframe * CFrame.Angles(0, 0, math.rad(90))
		elseif piece.Shape == "Ball" then
			part.Shape = Enum.PartType.Ball
			part.Size = Vector3.new(size.X, size.X, size.X)
		end
		part.Material = flat(piece.Material)
		part.Transparency = piece.Transparency or 0
	end
	folder.Parent = parent
	return folder
end

-- A Platform_<AssetName> model instead of the parts: scaled so its StandPoint marker ends `top` above the ground and its bottom
-- ModelSink below it, the marker right above `frame`'s position.
local function placePlatformModel(asset: Model, top: number, frame: CFrame, parent: Instance): Model
	Assets.MakeVisualOnly(asset, true)
	local marker = asset:FindFirstChild(ShibaPlatforms.StandMarkerName, true)
	local standPart: BasePart? = if marker and marker:IsA("BasePart") then marker else nil
	local function measure(): (CFrame, Vector3)
		local box, size = asset:GetBoundingBox()
		local bottom = box * CFrame.new(0, -size.Y / 2, 0)
		local stand = if standPart then bottom:PointToObjectSpace(standPart.Position) else Vector3.new(0, size.Y, 0)
		return bottom, stand
	end
	local _, stand = measure()
	if stand.Y > 0 then
		asset:ScaleTo(asset:GetScale() * (top + ShibaPlatforms.ModelSink) / stand.Y)
	end
	local bottom, scaled = measure()
	local target = frame * CFrame.new(-scaled.X, -ShibaPlatforms.ModelSink, -scaled.Z)
	asset:PivotTo(target * bottom:ToObjectSpace(asset:GetPivot()))
	if standPart then
		standPart.Transparency = 1
		standPart.CastShadow = false
	end
	asset.Name = "Platform"
	asset.Parent = parent
	return asset
end

-- Gives the bay the platform of its Shiba's tier (nil = no Shiba: no platform) and moves everything that stands on it.
local function applyPlatform(bay: BayRefs, assetName: string?, shibaHeight: number, animate: boolean)
	if assetName == bay.PlatformKey then
		return
	end
	bay.PlatformKey = assetName
	if bay.PlatformFolder then
		bay.PlatformFolder:Destroy()
		bay.PlatformFolder = nil
	end
	local top = LANE.PlatformTop
	local radius = LAYOUT.PlatformDiameter / 2
	local swing = bay.SwingPart
	if assetName then
		local platform = ShibaPlatforms.Platforms[assetName] or ShibaPlatforms.Default
		local frame = CFrame.lookAt(bay.Ground, bay.Ground + bay.Inward)
		local model = Assets.CloneModel(`{ShibaPlatforms.ModelPrefix}{assetName}`)
		top =
			math.max(if model then platform.ModelTop or platform.Top else platform.Top, Gameplay.Shooters.PlatformLift)
		bay.PlatformFolder = if model
			then placePlatformModel(model, top, frame, bay.Folder)
			else buildPlatformParts(platform, frame, bay.Folder)
		if animate and bay.PlatformFolder then
			bay.PlatformFolder:SetAttribute("SpawnedAt", Workspace:GetServerTimeNow())
		end
		-- The click part is also the invisible wall around platform and Shiba (so nobody walks through it): the mouse hits
		-- it first, so the ClickDetector has to sit on this very part. Only characters collide with it.
		local padding = Gameplay.Shooters.Barrier.Padding
		radius = platform.Diameter / 2 + padding
		local sink = Gameplay.Shooters.Barrier.Sink
		local tall = sink + top + shibaHeight + Gameplay.Shooters.Barrier.ExtraHeight
		swing.Shape = Enum.PartType.Cylinder
		swing.Size = Vector3.new(tall, radius * 2, radius * 2)
		swing.CFrame = CFrame.new(bay.Ground + Vector3.new(0, tall / 2 - sink, 0)) * CFrame.Angles(0, 0, math.rad(90))
		swing.CanCollide = true
	else
		swing.Shape = Enum.PartType.Block
		swing.Size = LANE.SwingBoxSize
		swing.CFrame = CFrame.new(bay.Ground + Vector3.new(0, LANE.PlatformTop + LANE.SwingBoxSize.Y / 2, 0))
		swing.CanCollide = false
	end
	bay.Top = top
	bay.Radius = radius
	local stand = bay.Ground + Vector3.new(0, top, 0)
	bay.Anchor.CFrame = CFrame.new(stand)
	bay.Belt.CFrame = CFrame.lookAt(stand, stand + bay.Inward)
end

-- `animate`: the plot is already loaded, so what is built now pops in (Controllers/SpawnController).
local function refreshBay(bay: BayRefs, tycoon: Types.TycoonState, index: number, animate: boolean)
	local id = tycoon.Equipped[tostring(index)]
	local shiba = if id then tycoon.Shibas[id] else nil
	local def = if shiba then EconomyConfig.Shibas[shiba.Tier + 1] else nil
	local active = shiba ~= nil and id ~= nil and def ~= nil

	applyPlatform(bay, if def then def.AssetName else nil, if def then def.Height else 0, animate)

	-- Shiba visual: swap only when (id, tier, variant) changed.
	local key = if shiba and id then `{id}:{shiba.Tier}:{shiba.Variant}` else nil
	if key ~= bay.VisualKey then
		if bay.Visual then
			bay.Visual:Destroy()
			bay.Visual = nil
		end
		bay.VisualKey = key
		if shiba then
			-- The Shiba stands on the platform: BuildShibaVisual adds LANE.PlatformTop to the ground it gets.
			local lane = {
				Ground = bay.Ground + Vector3.new(0, bay.Top - LANE.PlatformTop, 0),
				Inward = bay.Inward,
				Folder = bay.Folder,
			}
			local visual = TycoonPlot.BuildShibaVisual(lane, shiba)
			bay.Visual = visual
			if animate then
				visual:SetAttribute("SpawnedAt", Workspace:GetServerTimeNow())
			end
		end
	end

	-- Clicks are accepted while the Shiba exists (the server ignores them for automated Shibas).
	bay.SwingClick.MaxActivationDistance = if active then LAYOUT.ClickDistance else 0

	-- The Intern stands there as long as the Shiba is automated.
	local automated = active and shiba ~= nil and shiba.Automated == true
	if automated and not bay.Intern then
		local intern = buildIntern(bay)
		bay.Intern = intern
		if animate then
			intern:SetAttribute("SpawnedAt", Workspace:GetServerTimeNow())
		end
	elseif not automated and bay.Intern then
		bay.Intern:Destroy()
		bay.Intern = nil
	end
end

-- The walkway through the stage of `bay`: a polyline (Theme.Path, else straight) from the stage's front to its back, joined to the
-- road (stage 1) or to the neighbouring stages by straight pieces over the margins.
local function ensurePath(plot: Plot, bay: number)
	if plot.Paths[bay] then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = `Path{bay}`
	local frame = stageFrame(plot, bay)
	local area = areaOf(bay)
	local theme = TycoonDecor.Themes[bay]
	local waypoints: { Vector2 } = if theme and theme.Path
		then theme.Path
		else { Vector2.new(0, area.Y / 2), Vector2.new(0, -area.Y / 2) }
	local lift = Vector3.new(0, 0.05, 0)
	local from = if bay == 1 then 0 else plot.Starts[bay]
	local to = plot.Starts[bay] + plot.Depths[bay]
	local points: { Vector3 } = {}
	table.insert(points, plot.RoadEnd + plot.Back * from + Vector3.new(0, plot.Elev[bay], 0) + lift)
	for _, waypoint in waypoints do
		table.insert(points, frame:PointToWorldSpace(Vector3.new(waypoint.X, 0, waypoint.Y)) + lift)
	end
	table.insert(points, plot.RoadEnd + plot.Back * to + Vector3.new(0, plot.Elev[bay], 0) + lift)
	local width = LAYOUT.PathWidth
	for index = 1, #points - 1 do
		local a, b = points[index], points[index + 1]
		local length = (b - a).Magnitude
		if length > 0.1 then
			local middle = (a + b) / 2
			newPart("Path", Vector3.new(width, 0.1, length), CFrame.lookAt(middle, b), LAYOUT.PathColor, folder)
		end
		if index > 1 then
			-- A square at every joint fills the corner.
			newPart("PathJoint", Vector3.new(width, 0.1, width), CFrame.new(a), LAYOUT.PathColor, folder)
		end
	end
	folder.Parent = plot.Folder
	plot.Paths[bay] = folder
end

-- ==== decor ============================================================================================================

-- Marks a model that appeared after the plot was loaded: the client (Controllers/SpawnController) lets it pop in.
local function announce(plot: Plot, model: Instance)
	if plot.Ready then
		model:SetAttribute("SpawnedAt", Workspace:GetServerTimeNow())
	end
end

-- The union box (centre, size) of a part's pieces in the stage frame.
local function piecesBox(pieces: { TycoonDecor.Piece }): (Vector3, Vector3)
	local low = Vector3.new(math.huge, math.huge, math.huge)
	local high = Vector3.new(-math.huge, -math.huge, -math.huge)
	for _, piece in pieces do
		local rotation = piece.Rotation or Vector3.zero
		local cframe = CFrame.new(piece.Offset)
			* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
		local half = piece.Size / 2
		for _, x in { -1, 1 } do
			for _, y in { -1, 1 } do
				for _, z in { -1, 1 } do
					local corner = cframe:PointToWorldSpace(Vector3.new(x * half.X, y * half.Y, z * half.Z))
					low = low:Min(corner)
					high = high:Max(corner)
				end
			end
		end
	end
	return (low + high) / 2, high - low
end

-- A Decor_<Key>_<PartId> model is made to the size and place of the part's pieces, whatever scale it was imported at.
local function fitToPieces(model: Model, frame: CFrame, pieces: { TycoonDecor.Piece })
	local center, size = piecesBox(pieces)
	model:PivotTo(CFrame.new())
	local _, modelSize = model:GetBoundingBox()
	local longest = math.max(modelSize.X, modelSize.Y, modelSize.Z)
	if longest > 0 then
		model:ScaleTo(model:GetScale() * math.max(size.X, size.Y, size.Z) / longest)
	end
	local box = model:GetBoundingBox()
	model:PivotTo(frame * CFrame.new(center - box.Position))
end

-- Props the player could walk into are solid (floors, rugs and things high above the head are not).
local function isSolid(piece: TycoonDecor.Piece): boolean
	local reach = if piece.Rotation then math.max(piece.Size.X, piece.Size.Y, piece.Size.Z) / 2 else piece.Size.Y / 2
	return piece.Offset.Y + reach > 0.6 and piece.Offset.Y - reach < 7
end

-- A bought decor part: a cloned Decor_<Key>_<PartId> model if the asset exists (the pieces then only serve as invisible
-- colliders), else the part's primitive pieces.
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
		fitToPieces(model, frame, part.Pieces)
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				descendant.Material = flat(descendant.Material)
			end
		end
		for number, piece in part.Pieces do
			if isSolid(piece) then
				local rotation = piece.Rotation or Vector3.zero
				local cframe = frame
					* CFrame.new(piece.Offset)
					* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
				local collider = newPart(`Collider{number}`, piece.Size, cframe, Color3.new(1, 1, 1), model)
				collider.Shape = piece.Shape or Enum.PartType.Block
				collider.Transparency = 1
				collider.CanCollide = true
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
			instance.CanCollide = isSolid(piece)
		end
	end
	model.Name = `Decor_{step.Id}`
	model.Parent = plot.Folder
	announce(plot, model)
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
	local theme = TycoonDecor.Themes[step.Bay]
	local front = area.Y / 2 - LAYOUT.PadFrontInset
	local function at(spot: Vector2): Vector3
		return frame:PointToWorldSpace(Vector3.new(spot.X, 0, spot.Y))
	end
	if step.Kind == "Bay" then
		return if theme and theme.BayPad then at(theme.BayPad) else frame:PointToWorldSpace(Vector3.new(0, 0, front))
	elseif step.Kind == "Automate" then
		if theme and theme.AutoPad then
			return at(theme.AutoPad)
		end
		return frame:PointToWorldSpace(Vector3.new(0, 0, area.Y / 2 - LAYOUT.AutoPadInset))
	end
	if step.Kind == "Ascend" then
		local elev = plot.Elev[1] or 0
		local aside = plot.RoadEnd + plot.Back * LAYOUT.AscendPadDepth + plot.Right * LAYOUT.AscendPadLateral
		return aside + Vector3.new(0, elev, 0)
	end
	local index = step.PartIndex or 1
	local own = if theme and step.PartIndex then theme.Parts[step.PartIndex] else nil
	if own and own.Pad then
		return at(own.Pad)
	end
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
	if step.Kind == "Ascend" then
		-- Resets the run: a hold prompt (like the island's Ascension shrine) instead of a touch, so it is never stepped on by accident.
		-- BuyStep validates everything again; the prompt only asks.
		part.CanTouch = false
		local prompt = Instance.new("ProximityPrompt")
		prompt.Name = "Tycoon_Ascend"
		prompt.ActionText = "Ascend"
		prompt.ObjectText = "Start over with more income"
		prompt.KeyboardKeyCode = Enum.KeyCode.E
		prompt.GamepadKeyCode = Enum.KeyCode.ButtonX
		prompt.HoldDuration = LAYOUT.AscendHoldSeconds
		prompt.MaxActivationDistance = LAYOUT.AscendPromptDistance
		prompt.RequiresLineOfSight = false
		prompt.Parent = part
		prompt.Triggered:Connect(function(triggerer: Player)
			if triggerer == owner and not pad.Busy then
				pad.Busy = true
				plot.Actions.BuyStep(owner, step.Id)
				task.delay(LAYOUT.PadCooldown, function()
					pad.Busy = false
				end)
			end
		end)
	end
	part.Touched:Connect(function(hit: BasePart)
		if pad.Busy or step.Kind == "Ascend" then
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
	if step.Kind == "Ascend" then
		-- The next multiplier instead of a price; always available while it is shown.
		local multiplier = TycoonMath.AscensionMultiplier(tycoon.Ascensions + 1)
		setText(pad.Price, `income x{string.format("%g", multiplier)}`)
		pad.Part.Color = LAYOUT.AscendColor
		return
	end
	setText(pad.Price, if price <= 0 then "FREE" else Format.Money(price))
	pad.Part.Color = if money >= price then PAD_AFFORDABLE else PAD_TOO_DEAR
end

-- ==== public ===========================================================================================================

function StreetPlot.Destroy(player: Player)
	local plot = plots[player]
	plots[player] = nil
	if plot then
		plot.Folder:Destroy()
		-- The white wall only had to reach as far as this plot's owner did (a rebuilt plot after an Ascension starts at bay 1).
		StreetService.SetReach(plot.Slot, 1)
	end
end

-- Creates the plot's (still empty) folder under island.Model; call Refresh with the state afterwards.
function StreetPlot.Build(player: Player, island: StreetService.Island, actions: Actions)
	StreetPlot.Destroy(player)
	local folder = Instance.new("Folder")
	folder.Name = TycoonWorld.FolderName
	local towardRoad = direction(island.HubAngle)
	local back = -towardRoad

	-- The stages follow each other from the road (Util/StreetLayout).
	local layout = StreetLayout.Compute()

	plots[player] = {
		Owner = player,
		Slot = island.Slot,
		WallReach = 1,
		Ready = false,
		Folder = folder,
		Actions = actions,
		RoadEnd = island.Center + towardRoad * (Street.PlotDepth / 2),
		Back = back,
		Right = back:Cross(Vector3.yAxis),
		Elev = layout.Elev,
		Terrain = {},
		Starts = layout.Starts,
		Depths = layout.Depths,
		Bays = {},
		Paths = {},
		Pads = {},
		Decor = {},
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
		ensurePath(plot, index)
		refreshBay(bay, tycoon, index, plot.Ready)
	end

	refreshDecor(plot, tycoon)

	-- The pads of the flow (Util/TycoonSteps): Shibas, required decor and the optional interns.
	local wanted: { [string]: boolean } = {}
	local visible = TycoonSteps.Visible(tycoon)
	local reached = tycoon.EquipSlots
	for _, step in visible do
		if step.Kind == "Bay" then
			reached = math.max(reached, step.Bay)
		end
	end
	refreshTerrain(plot, reached)
	-- The white wall around the street reaches back as far as the furthest owner (StreetService).
	reached = math.max(reached, 1)
	if plot.WallReach ~= reached then
		plot.WallReach = reached
		StreetService.SetReach(plot.Slot, reached)
	end

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
	plot.Ready = true
end

-- Where the Shiba of bay `slot` stands and which way it faces (the hit zone is in front of it), for the server's hit check.
function StreetPlot.GetLaneAim(player: Player, slot: number): { Origin: Vector3, Forward: Vector3 }?
	local plot = plots[player]
	local bay = if plot then plot.Bays[slot] else nil
	if not bay then
		return nil
	end
	return { Origin = bay.Ground + Vector3.new(0, bay.Top, 0), Forward = bay.Inward }
end

return StreetPlot
