--!strict
-- The tycoon on a street plot (docs/GAME_DESIGN.md → "Gameplay flow"). Built under island.Model/Tycoon for the plot's owner:
-- - Stages: one per Shiba, one after the other away from the road. Stage n is as deep as its theme's Area (Config/TycoonDecor)
--   plus a margin, with a path through its middle. Shiba n stands at the stage-local point (-ShibaX, 0, 0) facing the path
--   (the stage frame is defined in Config/DecorTypes).
-- - A bay (Lane_<n>): a platform, the visual-only Shiba, an invisible click box (StreetGameService handles the click) and,
--   once automated, the Bonk Intern standing in front of the Shiba. The client draws the Shiba's menu, the swing and the
--   intern's ducking; there are no prompts or billboards on the Shiba.
-- - Decor: the pieces of every bought decor pad, built in the stage frame.
-- - Path and scatter: the curved walkway and the silent organic dressing of every stage (World/StageScatter).
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
local StageScatter = require(script.Parent.StageScatter)
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
	-- The Intern is built asynchronously (CreateHumanoidModelFromDescription yields): true while one is being built, and
	-- whether the Shiba still wants one when the build is done.
	InternPending: boolean,
	InternWanted: boolean,
}

type PadRefs = {
	Folder: Folder,
	Part: Part,
	Title: TextLabel,
	Desc: TextLabel,
	Price: TextLabel,
	Busy: boolean,
}

-- A sphere of smooth Terrain this plot put into the world (Terrain has no parent, so it is cleared by hand).
type Fill = { Center: Vector3, Radius: number }

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
	-- Built hillsides (slope, floor slab, rocks) by bay (Refresh), and the Terrain regions each of them filled (to clear again).
	Terrain: { [number]: Folder },
	Fills: { [number]: { Fill } },
	-- Per bay: how far from RoadEnd its stage starts, how deep it is (the theme's scaled Area plus the margin) and how long
	-- the slope before it is.
	Starts: { [number]: number },
	Depths: { [number]: number },
	Ramp: { [number]: number },
	Bays: { [number]: BayRefs },
	Paths: { [number]: Folder },
	-- The organic scatter (trees, fences, rocks, ...) of every reached stage (World/StageScatter), built silently with the stage.
	Scatter: { [number]: Folder },
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

-- The theme files are written unscaled: every coordinate taken from them (Area, Shiba spot, path, pads, pieces) is multiplied by
-- STAGE_SCALE so the props sit closer together. Sizes the player deals with (Shiba, platform, barrier, path width, pads) are not.
local STAGE_SCALE = LAYOUT.StageScale

-- The stage's Area after scaling.
local function areaOf(bay: number): Vector2
	return StreetLayout.AreaOf(bay)
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
	local own = if theme then theme.Shiba else nil
	local spot: TycoonDecor.ShibaSpot = own or { Position = Vector2.new(-LAYOUT.ShibaX, 0), Facing = 0 }
	return { Position = spot.Position * STAGE_SCALE, Facing = spot.Facing }
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

-- The first GroupSize stages lie on the flat plot ground; every later stage stands higher than the one before and is reached
-- over a wide, eased grassy slope (Util/StreetLayout has the heights and lengths). Stage `bay` appears when its Shiba becomes
-- available, so the pad of that Shiba stands on its floor (Refresh decides when). What is built per stage:
--   - Slope1..n: collidable grass slabs following the eased profile across the whole width between two plots, plus the soil
--     boxes under them (nobody sees these; the slabs are the safe, exact walking surface), and the path laid over the slope;
--   - Floor: the flat, solid grass slab at the stage's height (tinted per stage) that the theme's props and floors stand on;
--   - smooth Terrain mounds and rocky outcrops beside the walkway and along both flanks, boulders and shrubs (deterministic per
--     stage). The Terrain fills are tracked per stage (Plot.Fills) and cleared with Air when the stage or the plot goes away.
local TERRAIN_FIRST = LAYOUT.GroupSize + 1
-- The soil boxes under the slabs start this far above the plot ground's bottom and end this far under the slab's top.
local SOIL_BOTTOM = -1
local SOIL_INSET = 1.5
-- Slope slabs are at most about this long along the path.
local SLOPE_PIECE = 5
-- Mounds, rocks, boulders and shrubs on a slope keep the walkway lane (half the path plus this) free.
local LANE_MARGIN = 12

local terrainReady = false

-- A point of the plot: `depth` away from the road, `lateral` to the right of the path, `height` above the plot's ground.
local function pointAt(plot: Plot, depth: number, lateral: number, height: number): Vector3
	return plot.RoadEnd + plot.Back * depth + plot.Right * lateral + Vector3.new(0, height, 0)
end

-- Height of the walking surface on the slope before stage `bay` at `depth` (eased from the previous stage's floor).
local function slopeHeight(plot: Plot, bay: number, depth: number): number
	local low, high = plot.Elev[bay - 1], plot.Elev[bay]
	local length = plot.Ramp[bay]
	if length <= 0 then
		return high
	end
	return low + (high - low) * StreetLayout.Ease((depth - (plot.Starts[bay] - length)) / length)
end

-- A solid grass slab whose top surface is the straight line from (depthA, heightA) to (depthB, heightB) along the path.
local function slab(
	plot: Plot,
	name: string,
	depthA: number,
	heightA: number,
	depthB: number,
	heightB: number,
	color: Color3,
	parent: Instance
): Part
	local from = pointAt(plot, depthA, 0, heightA)
	local to = pointAt(plot, depthB, 0, heightB)
	local thick = LAYOUT.ShelfThickness
	local frame = CFrame.lookAt((from + to) / 2, to) * CFrame.new(0, -thick / 2, 0)
	local part = solid(name, Vector3.new(Street.PlotPitch, thick, (to - from).Magnitude), frame, color, parent)
	part.Material = LAYOUT.GrassMaterial
	return part
end

-- Soil under a slab (never seen, it only keeps the hillside from being hollow): from the plot ground up to just under the slab.
local function soil(plot: Plot, depthA: number, depthB: number, lowTop: number, parent: Instance)
	local top = lowTop - SOIL_INSET
	if top <= SOIL_BOTTOM + 0.5 then
		return
	end
	local box = plotBox(
		plot,
		"Soil",
		(depthA + depthB) / 2,
		0,
		depthB - depthA,
		Street.PlotPitch - 2,
		SOIL_BOTTOM,
		top,
		LAYOUT.SoilColor,
		parent
	)
	box.Material = Enum.Material.Ground
end

-- Terrain has no parent: remember what was filled so it can be cleared again.
local function fillBall(plot: Plot, bay: number, center: Vector3, radius: number, material: Enum.Material)
	Workspace.Terrain:FillBall(center, radius, material)
	local list = plot.Fills[bay]
	if not list then
		list = {}
		plot.Fills[bay] = list
	end
	table.insert(list, { Center = center, Radius = radius })
end

local function clearFills(plot: Plot, bay: number)
	local list = plot.Fills[bay]
	if list then
		for _, fill in list do
			Workspace.Terrain:FillBall(fill.Center, fill.Radius + 2, Enum.Material.Air)
		end
		plot.Fills[bay] = nil
	end
end

local function clearAllFills(plot: Plot)
	for bay in plot.Fills do
		clearFills(plot, bay)
	end
end

local function buildStage(plot: Plot, bay: number): Folder
	local folder = Instance.new("Folder")
	folder.Name = `Terrain{bay}`
	if not terrainReady then
		terrainReady = true
		local terrain = Workspace.Terrain
		terrain:SetMaterialColor(Enum.Material.Grass, LAYOUT.TerrainGrass)
		terrain:SetMaterialColor(Enum.Material.Ground, LAYOUT.SoilColor)
		terrain:SetMaterialColor(Enum.Material.Rock, LAYOUT.RockColor)
	end
	local random = Random.new(bay * 7919 + 17)
	local high = plot.Elev[bay]
	local ramp = plot.Ramp[bay]
	local floorFrom = plot.Starts[bay]
	local floorTo = floorFrom + plot.Depths[bay]
	local rampFrom = floorFrom - ramp
	local tint = LAYOUT.GrassTints[(bay - 1) % #LAYOUT.GrassTints + 1]
	local half = Street.PlotPitch / 2

	-- The slope: slabs along the eased profile, the path on top of it.
	local pieces = math.max(3, math.ceil(ramp / SLOPE_PIECE))
	local lift = 0.05
	for index = 1, pieces do
		local depthA = rampFrom + ramp * (index - 1) / pieces
		local depthB = rampFrom + ramp * index / pieces
		local heightA = slopeHeight(plot, bay, depthA)
		local heightB = slopeHeight(plot, bay, depthB)
		slab(plot, `Slope{index}`, depthA, heightA, depthB, heightB, tint, folder)
		soil(plot, depthA, depthB, heightA, folder)
		local a = pointAt(plot, depthA, 0, heightA + lift)
		local b = pointAt(plot, depthB, 0, heightB + lift)
		newPart(
			"Path",
			Vector3.new(LAYOUT.PathWidth, 0.1, (b - a).Magnitude),
			CFrame.lookAt((a + b) / 2, b),
			LAYOUT.PathColor,
			folder
		)
	end

	-- The stage's floor.
	slab(plot, "Floor", floorFrom, high, floorTo, high, tint, folder)
	soil(plot, floorFrom, floorTo, high, folder)

	-- Beside the walkway on the slope: Terrain mounds and rocky outcrops, boulders and shrubs.
	local lane = LAYOUT.PathWidth / 2 + LANE_MARGIN
	local function spot(): (number, number)
		local side = if random:NextNumber() < 0.5 then -1 else 1
		return rampFrom + ramp * random:NextNumber(), side * (lane + (half - 10 - lane) * random:NextNumber())
	end
	for _ = 1, 6 do
		local depth, lateral = spot()
		local radius = random:NextNumber(6, 11)
		local material = if random:NextNumber() < 0.8 then Enum.Material.Grass else Enum.Material.Ground
		fillBall(
			plot,
			bay,
			pointAt(plot, depth, lateral, slopeHeight(plot, bay, depth) - radius * 0.7),
			radius,
			material
		)
	end
	for _ = 1, 2 do
		local depth, lateral = spot()
		local radius = random:NextNumber(5, 8)
		fillBall(
			plot,
			bay,
			pointAt(plot, depth, lateral, slopeHeight(plot, bay, depth) - radius * 0.45),
			radius,
			Enum.Material.Rock
		)
	end
	for _ = 1, 4 do
		local depth, lateral = spot()
		local size = random:NextNumber(2, 4.5)
		local boulder = solid(
			"Boulder",
			Vector3.new(size, size, size),
			CFrame.new(pointAt(plot, depth, lateral, slopeHeight(plot, bay, depth) + size * 0.25)),
			LAYOUT.RockColor:Lerp(LAYOUT.SoilColor, random:NextNumber(0, 0.4)),
			folder
		)
		boulder.Shape = Enum.PartType.Ball
		boulder.Material = Enum.Material.Rock
		boulder.CanQuery = false
	end
	for _ = 1, 8 do
		local depth, lateral = spot()
		local size = random:NextNumber(2.5, 4.5)
		local shrub = newPart(
			"Shrub",
			Vector3.new(size, size, size),
			CFrame.new(pointAt(plot, depth, lateral, slopeHeight(plot, bay, depth) + size * 0.3)),
			Color3.fromRGB(
				50 + random:NextInteger(0, 30),
				130 + random:NextInteger(0, 40),
				55 + random:NextInteger(0, 25)
			),
			folder
		)
		shrub.Shape = Enum.PartType.Ball
		shrub.Material = Enum.Material.LeafyGrass
	end

	-- The flanks of the stage: rounded rocky hills along both sides, beside the white wall (themes keep their props inside
	-- their Area, which ends well before them).
	for _, side in { -1, 1 } do
		for _ = 1, 2 do
			local depth = floorFrom + (floorTo - floorFrom) * random:NextNumber(0.1, 0.9)
			local radius = random:NextNumber(6, 11)
			local lateral = side * (half - 14 + random:NextNumber(-1, 1))
			local material = if random:NextNumber() < 0.5 then Enum.Material.Rock else Enum.Material.Grass
			fillBall(plot, bay, pointAt(plot, depth, lateral, high - radius * 0.5), radius, material)
		end
	end

	folder.Parent = plot.Folder
	return folder
end

-- Builds the hillside of every stage that is reached (`reached` = the highest Shiba available) and removes the rest.
local function refreshTerrain(plot: Plot, reached: number)
	for bay = TERRAIN_FIRST, TycoonSteps.Bays do
		local built = plot.Terrain[bay]
		if reached >= bay then
			if not built then
				plot.Terrain[bay] = buildStage(plot, bay)
			end
		elseif built then
			built:Destroy()
			clearFills(plot, bay)
			plot.Terrain[bay] = nil
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
		InternPending = false,
		InternWanted = false,
	}
end

-- The Bonk Intern fallback (when the R15 character cannot be built): a simple NPC made of blocks, standing in front of the
-- Shiba and facing it. Visual only; the client makes it duck when the stick lands. Returned without a parent.
local function buildFallbackIntern(bay: BayRefs): Model
	local model = Instance.new("Model")
	model.Name = "Intern"
	model:SetAttribute("StreetIntern", true)
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
	return model
end

-- Outfits of the R15 interns (body colours instead of catalog clothes: no asset ids needed): skin, shirt, trousers.
local INTERN_OUTFITS = {
	{ Skin = Color3.fromRGB(255, 214, 170), Shirt = Color3.fromRGB(90, 200, 120), Pants = Color3.fromRGB(60, 80, 140) },
	{ Skin = Color3.fromRGB(224, 172, 125), Shirt = Color3.fromRGB(255, 140, 50), Pants = Color3.fromRGB(50, 55, 70) },
	{ Skin = Color3.fromRGB(141, 95, 66), Shirt = Color3.fromRGB(70, 140, 255), Pants = Color3.fromRGB(35, 35, 45) },
	{ Skin = Color3.fromRGB(255, 205, 160), Shirt = Color3.fromRGB(160, 90, 230), Pants = Color3.fromRGB(80, 80, 95) },
	{ Skin = Color3.fromRGB(198, 134, 92), Shirt = Color3.fromRGB(235, 70, 80), Pants = Color3.fromRGB(60, 80, 140) },
	{ Skin = Color3.fromRGB(240, 190, 150), Shirt = Color3.fromRGB(245, 245, 245), Pants = Color3.fromRGB(45, 50, 80) },
	{ Skin = Color3.fromRGB(110, 75, 55), Shirt = Color3.fromRGB(250, 205, 60), Pants = Color3.fromRGB(50, 55, 70) },
}
local INTERN_HATS = { "HardHat", "Headband", "Cap", "None" }
local INTERN_SCALE = 1.2

-- Welds a decoration to the head at `offset` (relative to the head).
local function attachToHead(head: BasePart, part: BasePart, offset: CFrame)
	part.Anchored = false
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Massless = true
	part.CastShadow = false
	part.CFrame = head.CFrame * offset
	local weld = Instance.new("Weld")
	weld.Part0 = head
	weld.Part1 = part
	weld.C0 = offset
	weld.Parent = part
	part.Parent = head.Parent
end

local function headPiece(name: string, size: Vector3, color: Color3, shape: Enum.PartType?): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	if shape then
		part.Shape = shape
	end
	return part
end

-- The Bonk Intern: a real Roblox character (R15 blocky avatar from a HumanoidDescription), standing in front of the Shiba
-- and facing it. Visual only: the root is anchored, the rest hangs on its Motor6Ds so the client can animate them (idle bob,
-- flinch, see Controllers/InternChatController) and duck it when the stick lands. Yields; returned without a parent.
local function buildIntern(bay: BayRefs): Model
	local base = bay.Ground + bay.Inward * (bay.Radius + LAYOUT.InternGap)
	local frame = CFrame.lookAt(base, base - bay.Inward)
	-- Varied but deterministic look per bay.
	local seed = 0
	for _, code in { string.byte(bay.Folder.Name, 1, -1) } do
		seed = seed * 31 + code
	end
	local outfit = INTERN_OUTFITS[seed % #INTERN_OUTFITS + 1]
	local hat = INTERN_HATS[(seed // #INTERN_OUTFITS) % #INTERN_HATS + 1]

	local okBuild, built = pcall(function()
		local description = Instance.new("HumanoidDescription")
		description.HeadColor = outfit.Skin
		description.LeftArmColor = outfit.Skin
		description.RightArmColor = outfit.Skin
		description.TorsoColor = outfit.Shirt
		description.LeftLegColor = outfit.Pants
		description.RightLegColor = outfit.Pants
		local character = Players:CreateHumanoidModelFromDescription(description, Enum.HumanoidRigType.R15)
		description:Destroy()
		return character
	end)
	if not okBuild or typeof(built) ~= "Instance" or not built:IsA("Model") then
		return buildFallbackIntern(bay)
	end
	local model: Model = built
	local humanoid = model:FindFirstChildOfClass("Humanoid")
	local root = model:FindFirstChild("HumanoidRootPart")
	local head = model:FindFirstChild("Head")
	if not humanoid or not root or not root:IsA("BasePart") or not head or not head:IsA("BasePart") then
		model:Destroy()
		return buildFallbackIntern(bay)
	end

	model.Name = "Intern"
	model:SetAttribute("StreetIntern", true)
	humanoid.WalkSpeed = 0
	humanoid.JumpPower = 0
	humanoid.JumpHeight = 0
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	humanoid.NameDisplayDistance = 0
	humanoid.HealthDisplayDistance = 0
	humanoid.DisplayName = ""
	humanoid.BreakJointsOnDeath = false

	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.CanCollide = false
			descendant.CanQuery = false
			descendant.CanTouch = false
			descendant.CastShadow = false
			-- Only the root is anchored: the limbs hang on their Motor6Ds so they can be animated.
			descendant.Anchored = descendant == root
			descendant.Massless = descendant ~= root
		elseif descendant:IsA("Decal") and descendant.Parent == head then
			-- The default face decal is replaced by simple parts below (no asset ids).
			descendant:Destroy()
		end
	end

	-- Stand it on the ground facing the Shiba (its pivot is the root; measure the feet first).
	model:ScaleTo(INTERN_SCALE)
	model:PivotTo(CFrame.new())
	local box, size = model:GetBoundingBox()
	local feet = box.Position.Y - size.Y / 2
	model:PivotTo(frame * CFrame.new(0, -feet, 0))

	-- Face: two eyes and a mouth on the front of the head (-Z).
	local hs = head.Size
	local dark = Color3.fromRGB(30, 30, 35)
	for _, side in { -1, 1 } do
		local eye = headPiece("Eye", Vector3.new(hs.X * 0.1, hs.Y * 0.2, 0.05), dark)
		attachToHead(head, eye, CFrame.new(side * hs.X * 0.2, hs.Y * 0.08, -hs.Z / 2 - 0.02))
	end
	local mouth = headPiece("Mouth", Vector3.new(hs.X * 0.36, hs.Y * 0.07, 0.05), dark)
	attachToHead(head, mouth, CFrame.new(0, -hs.Y * 0.2, -hs.Z / 2 - 0.02))

	-- Hard hat, headband or cap (simple parts, no catalog assets).
	if hat == "HardHat" then
		local dome =
			headPiece("HardHat", Vector3.new(hs.X * 1.1, hs.Y * 0.55, hs.Z * 1.1), Color3.fromRGB(255, 210, 40))
		attachToHead(head, dome, CFrame.new(0, hs.Y * 0.5, 0))
		local rim =
			headPiece("HardHatRim", Vector3.new(hs.X * 1.25, hs.Y * 0.12, hs.Z * 1.35), Color3.fromRGB(240, 190, 30))
		attachToHead(head, rim, CFrame.new(0, hs.Y * 0.28, -hs.Z * 0.1))
	elseif hat == "Headband" then
		local band =
			headPiece("Headband", Vector3.new(hs.X * 1.06, hs.Y * 0.16, hs.Z * 1.06), Color3.fromRGB(215, 50, 50))
		attachToHead(head, band, CFrame.new(0, hs.Y * 0.28, 0))
		local knot =
			headPiece("HeadbandKnot", Vector3.new(hs.X * 0.2, hs.Y * 0.2, hs.Z * 0.2), Color3.fromRGB(215, 50, 50))
		attachToHead(head, knot, CFrame.new(hs.X * 0.5, hs.Y * 0.28, hs.Z * 0.3))
	elseif hat == "Cap" then
		local crown = headPiece("Cap", Vector3.new(hs.X * 1.08, hs.Y * 0.4, hs.Z * 1.08), Color3.fromRGB(35, 40, 70))
		attachToHead(head, crown, CFrame.new(0, hs.Y * 0.45, 0))
		local brim = headPiece("CapBrim", Vector3.new(hs.X * 0.9, hs.Y * 0.1, hs.Z * 0.6), Color3.fromRGB(35, 40, 70))
		attachToHead(head, brim, CFrame.new(0, hs.Y * 0.3, -hs.Z * 0.7))
	end
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
	bay.InternWanted = automated
	if automated and not bay.Intern and not bay.InternPending then
		-- The R15 character takes a moment to build (it yields); the bay takes it over when it is done.
		bay.InternPending = true
		task.spawn(function()
			local intern = buildIntern(bay)
			bay.InternPending = false
			if not bay.InternWanted or bay.Intern or not bay.Folder.Parent then
				intern:Destroy()
				return
			end
			if animate then
				intern:SetAttribute("SpawnedAt", Workspace:GetServerTimeNow())
			end
			intern.Parent = bay.Folder
			bay.Intern = intern
		end)
	elseif not automated and bay.Intern then
		bay.Intern:Destroy()
		bay.Intern = nil
	end
end

-- The walkway through the stage of `bay`: the smooth curve of World/StageScatter.PathFor (the theme's waypoints, Theme.Path, else
-- straight) from the stage's front to its back, which joins the road (stage 1) or the neighbouring stages at the stage ends. Many
-- short overlapping segments with a round joint at every point, the width varies slightly (+-8%, the walkway keeps its gameplay width
-- of Config/TycoonWorld.Street.PathWidth on average).
local function ensurePath(plot: Plot, bay: number)
	if plot.Paths[bay] then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = `Path{bay}`
	local frame = stageFrame(plot, bay)
	local data = StageScatter.PathFor(bay)
	local lift = Vector3.new(0, 0.05, 0)
	local points: { Vector2 } = {}
	local widths: { number } = {}
	if bay == 1 then
		-- Stage 1's walkway starts at the road, a straight bit before the stage.
		local front = data.Points[1].Y
		local z = plot.Starts[1] + plot.Depths[1] / 2
		while z > front + 1 do
			table.insert(points, Vector2.new(0, z))
			table.insert(widths, 1)
			z -= 3
		end
	end
	for index, point in data.Points do
		table.insert(points, point)
		table.insert(widths, data.Widths[index])
	end

	local width = LAYOUT.PathWidth
	local standing = CFrame.Angles(0, 0, math.rad(90))
	for index, point in points do
		local here = frame:PointToWorldSpace(Vector3.new(point.X, 0, point.Y)) + lift
		local across = width * widths[index]
		-- The round joint: a flat disc (a cylinder's axis is X, so it is stood up).
		local disc = newPart(
			"PathJoint",
			Vector3.new(0.1, across, across),
			CFrame.new(here) * standing,
			LAYOUT.PathColor,
			folder
		)
		disc.Shape = Enum.PartType.Cylinder
		local nextPoint = points[index + 1]
		if nextPoint then
			local there = frame:PointToWorldSpace(Vector3.new(nextPoint.X, 0, nextPoint.Y)) + lift
			local length = (there - here).Magnitude
			if length > 0.1 then
				local narrow = width * math.min(widths[index], widths[index + 1])
				newPart(
					"Path",
					Vector3.new(narrow, 0.1, length + 0.3),
					CFrame.lookAt((here + there) / 2, there),
					LAYOUT.PathColor,
					folder
				)
			end
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
	-- Scaled with the stage (StageScale): the box the pieces get after scaling.
	return (low + high) / 2 * STAGE_SCALE, (high - low) * STAGE_SCALE
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
	-- The part's own frame: the stage frame turned by its Yaw around the vertical axis through the centre of its pieces.
	local stage = stageFrame(plot, step.Bay)
	local middle = piecesBox(part.Pieces)
	local frame = stage * CFrame.new(middle) * CFrame.Angles(0, math.rad(part.Yaw or 0), 0) * CFrame.new(-middle)
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
					* CFrame.new(piece.Offset * STAGE_SCALE)
					* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
				local collider =
					newPart(`Collider{number}`, piece.Size * STAGE_SCALE, cframe, Color3.new(1, 1, 1), model)
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
				* CFrame.new(piece.Offset * STAGE_SCALE)
				* CFrame.Angles(math.rad(rotation.X), math.rad(rotation.Y), math.rad(rotation.Z))
			local instance = newPart(`Piece{number}`, piece.Size * STAGE_SCALE, cframe, piece.Color, model)
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
	if step.Kind == "Ascend" then
		-- Beside the entrance of the plot (no stage of its own: its Bay is 0).
		local elev = plot.Elev[1] or 0
		local aside = plot.RoadEnd + plot.Back * LAYOUT.AscendPadDepth + plot.Right * LAYOUT.AscendPadLateral
		return aside + Vector3.new(0, elev, 0)
	end
	local frame = stageFrame(plot, step.Bay)
	local area = areaOf(step.Bay)
	local theme = TycoonDecor.Themes[step.Bay]
	local front = area.Y / 2 - LAYOUT.PadFrontInset
	local function at(spot: Vector2): Vector3
		-- Spots from the theme are unscaled (the pad itself keeps its size).
		return frame:PointToWorldSpace(Vector3.new(spot.X * STAGE_SCALE, 0, spot.Y * STAGE_SCALE))
	end
	if step.Kind == "Bay" then
		return if theme and theme.BayPad then at(theme.BayPad) else frame:PointToWorldSpace(Vector3.new(0, 0, front))
	elseif step.Kind == "Automate" then
		if theme and theme.AutoPad then
			return at(theme.AutoPad)
		end
		return frame:PointToWorldSpace(Vector3.new(0, 0, area.Y / 2 - LAYOUT.AutoPadInset))
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

-- The scatter of every stage that is reached (`reached` = the highest Shiba available): built once, silently (no SpawnedAt), removed
-- again when the stage goes away. A failure only costs the scatter, never the plot.
local function refreshScatter(plot: Plot, reached: number)
	for bay = 1, TycoonSteps.Bays do
		local built = plot.Scatter[bay]
		if reached >= bay then
			if not built then
				ensurePath(plot, bay)
				local frame = stageFrame(plot, bay)
				local pads: { Vector2 } = {}
				for _, step in TycoonSteps.List do
					if step.Bay == bay then
						local spot = frame:PointToObjectSpace(padPosition(plot, step))
						table.insert(pads, Vector2.new(spot.X, spot.Z))
					end
				end
				local ok, result = pcall(function()
					return StageScatter.Build({
						Bay = bay,
						Slot = plot.Slot,
						Frame = frame,
						Pads = pads,
						Parent = plot.Folder,
					})
				end)
				if ok then
					plot.Scatter[bay] = result
				else
					warn(`StageScatter bay {bay}: {result}`)
				end
			end
		elseif built then
			built:Destroy()
			plot.Scatter[bay] = nil
		end
	end
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
		clearAllFills(plot)
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
		Fills = {},
		Starts = layout.Starts,
		Depths = layout.Depths,
		Ramp = layout.Ramp,
		Bays = {},
		Paths = {},
		Scatter = {},
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
		-- The island is gone (the player left): drop the plot (its Terrain regions too, Terrain has no parent).
		clearAllFills(plot)
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
	refreshScatter(plot, reached)
	-- This plot's part of the white wall reaches back as far as its owner (StreetService).
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
