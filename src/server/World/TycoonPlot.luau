--!strict
-- The tycoon world of one island (docs/decisions/0006, layout in Config/TycoonWorld): a folder "Tycoon" under
-- Island_<UserId> with
--   Lane_<n>   (n = 1 … MaxEquipSlots, every ring position): Platform, Anchor (billboard), LockPlate, Plate (level
--              prompts), Belt_<n> (the conveyor Part, see Config/TycoonWorld → Belt), Arch1 / Arch2, and "Shiba" (the
--              visual, only while the slot holds one);
--   Mill       the Bonk Mill in the centre with the Sorter / Polisher / Refinery rings;
--   Vault      the chest next to it (Chest holds the collect prompt);
--   Egg_<zone> one egg stand per zone on the outer ring (only unlocked zones and the next one show);
--   Ascension  the altar with the hold prompt.
-- Everything is anchored, visual only (no collisions except the Mill, Vault and egg bases) and built once by Build;
-- Refresh only changes texts, transparency, prompt state and swaps a Shiba visual when its (id, tier, variant) changes.
-- ProximityPrompts (named Tycoon_<Something>) call `actions` for the island owner only; the server (TycoonService)
-- validates every action again. Items riding the belts are drawn by the client.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local ShibaEffects = require(ReplicatedStorage.Shared.Config.ShibaEffects)
local Stations = require(ReplicatedStorage.Shared.Config.Stations)
local Tycoon = require(ReplicatedStorage.Shared.Config.Tycoon)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local Types = require(ReplicatedStorage.Shared.Types)

local IslandService = require(script.Parent.Parent.Services.IslandService)
local PropService = require(script.Parent.Parent.Services.PropService)
local Signs = require(script.Parent.Signs)

local LANE = TycoonWorld.Lane
local BELT = TycoonWorld.Belt
local ARCH = TycoonWorld.Arch
local MILL = TycoonWorld.Mill
local VAULT = TycoonWorld.Vault
local EGGS = TycoonWorld.Eggs
local SHRINE = TycoonWorld.Shrine
local TEXT = TycoonWorld.Text
local MAX_SLOTS = Tycoon.MaxEquipSlots

export type Actions = {
	UpgradeShiba: (player: Player, slot: number, quantity: number) -> (),
	HatchEgg: (player: Player, eggId: string, count: number) -> (),
	BuyPad: (player: Player, padId: string) -> (),
	UpgradeLane: (player: Player, kind: string, slot: number) -> (),
	CollectVault: (player: Player) -> (),
	BoopLane: (player: Player, slot: number) -> (),
	SwingShiba: (player: Player, slot: number) -> (),
	BuyAutomation: (player: Player, slot: number) -> (),
}

type ArchRefs = {
	Parts: { Part },
	Prompt: ProximityPrompt,
}

type LaneRefs = {
	Folder: Folder,
	Ground: Vector3,
	Inward: Vector3,
	Platform: Part,
	Ring: Part,
	Anchor: Part,
	Gui: BillboardGui,
	Title: TextLabel,
	Sub: TextLabel,
	Hint: TextLabel,
	LockPlate: Part,
	SlotPrompt: ProximityPrompt,
	Plate: Part,
	PlateGui: BillboardGui,
	LevelPrompt: ProximityPrompt,
	BigLevelPrompt: ProximityPrompt,
	SwingPart: Part,
	SwingClick: ClickDetector,
	SwingPrompt: ProximityPrompt,
	AutoPrompt: ProximityPrompt,
	Belt: Part,
	Dashes: { Part },
	Arches: { ArchRefs },
	Visual: Model?,
	VisualKey: string?,
}

type RingRefs = {
	Part: Part,
	OwnedColor: Color3,
}

type EggRefs = {
	Model: Model,
	Parts: { Part },
	Egg: Part,
	Spots: { Part },
	Gui: BillboardGui,
	Title: TextLabel,
	Price: TextLabel,
	Odds: TextLabel,
	OddsText: string,
	Hatch1: ProximityPrompt,
	Hatch3: ProximityPrompt,
	Unlock: ProximityPrompt,
	Mode: string,
}

type MillRefs = {
	Rings: { RingRefs },
	Prompts: { ProximityPrompt },
}

type VaultRefs = {
	Pile: { Part },
	Gui: BillboardGui,
	Amount: TextLabel,
	Prompt: ProximityPrompt,
}

type ShrineRefs = {
	Prompt: ProximityPrompt,
	Gui: BillboardGui,
	Sub: TextLabel,
}

type Plot = {
	Folder: Folder,
	Center: Vector3,
	Lanes: { LaneRefs },
	Mill: MillRefs,
	Vault: VaultRefs,
	Eggs: { EggRefs },
	Shrine: ShrineRefs,
}

local plots: { [Player]: Plot } = {}

local TycoonPlot = {}

-- ===== small helpers =================================================================================================

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

-- An upright cylinder between two heights (relative to `at`, whose Y is the island surface).
local function newDisc(
	name: string,
	diameter: number,
	bottom: number,
	top: number,
	at: Vector3,
	color: Color3,
	parent: Instance
): Part
	local part = newPart(
		name,
		Vector3.new(top - bottom, diameter, diameter),
		CFrame.new(at + Vector3.new(0, (bottom + top) / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		parent
	)
	part.Shape = Enum.PartType.Cylinder
	return part
end

local function newBall(name: string, diameter: number, position: Vector3, color: Color3, parent: Instance): Part
	local part = newPart(name, Vector3.one * diameter, CFrame.new(position), color, parent)
	part.Shape = Enum.PartType.Ball
	return part
end

-- Invisible anchor for prompts and billboards.
local function newAnchor(name: string, cframe: CFrame, parent: Instance): Part
	local part = newPart(name, Vector3.one, cframe, Color3.new(1, 1, 1), parent)
	part.Transparency = 1
	return part
end

-- Assigns only when the value differs (no needless replication).
local function setTransparency(part: BasePart, value: number)
	if part.Transparency ~= value then
		part.Transparency = value
	end
end

local function setColor(part: BasePart, color: Color3)
	if part.Color ~= color then
		part.Color = color
	end
end

local function setText(label: TextLabel, text: string)
	if label.Text ~= text then
		label.Text = text
	end
end

local function setEnabled(prompt: ProximityPrompt, enabled: boolean)
	if prompt.Enabled ~= enabled then
		prompt.Enabled = enabled
	end
end

local function setPrompt(prompt: ProximityPrompt, enabled: boolean, actionText: string?)
	if actionText and prompt.ActionText ~= actionText then
		prompt.ActionText = actionText
	end
	setEnabled(prompt, enabled)
end

local function setGuiEnabled(gui: BillboardGui, enabled: boolean)
	if gui.Enabled ~= enabled then
		gui.Enabled = enabled
	end
end

-- A plain number: 12 → "12", 1.5 → "1.5", 1234 → "1.23K". Money and income never carry a currency text.
local function number(value: number): string
	if value < 100 and value ~= math.floor(value) then
		local text = string.format("%.1f", value)
		text = string.gsub(text, "%.0$", "")
		return text
	end
	return Format.Short(value)
end

-- A ProximityPrompt that only reacts to the island owner. Starts disabled; Refresh switches it on.
local function newPrompt(
	owner: Player,
	parent: Instance,
	name: string,
	key: Enum.KeyCode,
	gamepadKey: Enum.KeyCode,
	objectText: string,
	holdSeconds: number,
	distance: number,
	onTriggered: () -> ()
): ProximityPrompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = name
	prompt.ActionText = "..."
	prompt.ObjectText = objectText
	prompt.KeyboardKeyCode = key
	prompt.GamepadKeyCode = gamepadKey
	prompt.HoldDuration = holdSeconds
	prompt.MaxActivationDistance = distance
	prompt.RequiresLineOfSight = false
	prompt.Enabled = false
	prompt.Parent = parent
	prompt.Triggered:Connect(function(triggerer: Player)
		if triggerer == owner then
			onTriggered()
		end
	end)
	return prompt
end

type LineSpec = { Name: string, Height: number, TextSize: number, Color: Color3 }

-- A billboard with one outlined text line per spec, stacked top to bottom. Returns the gui and the labels by name.
local function newBillboard(
	adornee: BasePart,
	width: number,
	offsetY: number,
	maxDistance: number,
	lines: { LineSpec }
): (BillboardGui, { [string]: TextLabel })
	local total = 0
	for _, line in lines do
		total += line.Height
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "Info"
	gui.Size = UDim2.fromOffset(width, total)
	gui.StudsOffset = Vector3.new(0, offsetY, 0)
	gui.MaxDistance = maxDistance
	gui.LightInfluence = 0
	gui.Enabled = false
	gui.Parent = adornee
	local layout = Instance.new("UIListLayout")
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Bottom
	layout.Parent = gui
	local labels: { [string]: TextLabel } = {}
	for index, line in lines do
		local label = Instance.new("TextLabel")
		label.Name = line.Name
		label.LayoutOrder = index
		label.Size = UDim2.new(1, 0, 0, line.Height)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.FredokaOne
		label.TextSize = line.TextSize
		label.TextColor3 = line.Color
		label.Text = ""
		label.Parent = gui
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = 2
		stroke.Color = Color3.fromRGB(15, 12, 25)
		stroke.Parent = label
		labels[line.Name] = label
	end
	return gui, labels
end

local function shibaAt(tycoon: Types.TycoonState, slot: number): (Types.OwnedShiba?, string?)
	local id = tycoon.Equipped[tostring(slot)]
	if not id then
		return nil, nil
	end
	return tycoon.Shibas[id], id
end

-- ===== lanes =========================================================================================================

local function buildLane(
	player: Player,
	island: IslandService.Island,
	slot: number,
	parent: Folder,
	actions: Actions
): LaneRefs
	local angle = island.HubAngle + (slot - 0.5) / MAX_SLOTS * 2 * math.pi
	local outward = direction(angle)
	local inward = -outward
	local ground = island.Center + outward * LANE.RingRadius
	local folder = Instance.new("Folder")
	folder.Name = `Lane_{slot}`

	-- Platform with a glowing rim.
	local platform =
		newDisc("Platform", LANE.PlatformDiameter, -0.4, LANE.PlatformTop, ground, Color3.fromRGB(95, 90, 110), folder)
	platform.Material = Enum.Material.Slate
	local ring = newDisc("Rim", LANE.PlatformDiameter + 0.8, -0.4, 0.9, ground, Color3.fromRGB(120, 120, 140), folder)
	ring.Material = Enum.Material.Neon

	-- Info billboard above the Shiba.
	local standPoint = ground + Vector3.new(0, LANE.PlatformTop, 0)
	local anchor = newAnchor("Anchor", CFrame.new(standPoint), folder)
	local gui, labels = newBillboard(anchor, 240, 8, LANE.BillboardDistance, {
		{ Name = "Title", Height = 24, TextSize = 22, Color = TEXT.Title },
		{ Name = "Sub", Height = 20, TextSize = 18, Color = TEXT.Income },
		{ Name = "Hint", Height = 16, TextSize = 14, Color = TEXT.Hint },
	})

	-- Locked slot: a red plate with the buy prompt (only the next slot's prompt is enabled).
	local lockPlate = newDisc("LockPlate", 7, LANE.PlatformTop, LANE.PlatformTop + 0.25, ground, TEXT.Locked, folder)
	lockPlate.Material = Enum.Material.Neon
	lockPlate.Transparency = 1
	local slotPrompt = newPrompt(
		player,
		lockPlate,
		"Tycoon_Slot",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		"Shiba slot",
		0,
		LANE.PromptDistance,
		function()
			actions.BuyPad(player, `Slot{slot}`)
		end
	)

	-- Level plate beside the belt's start, with the two level prompts (E = 1 level, F = 10).
	local sideways = direction(angle + math.pi / 2)
	local platePosition = island.Center + outward * LANE.PlateRadius + sideways * LANE.PlateOffset
	local plate = newPart(
		"Plate",
		LANE.PlateSize,
		CFrame.lookAt(platePosition + Vector3.new(0, 0.2, 0), platePosition + Vector3.new(0, 0.2, 0) + inward),
		Color3.fromRGB(90, 230, 120),
		folder
	)
	plate.Material = Enum.Material.Neon
	plate.Transparency = 1
	local plateLabel = Signs.Billboard(plate, "LEVEL UP", TEXT.Income, Vector2.new(110, 24), 1.6, 40)
	local plateGui = plateLabel.Parent :: BillboardGui
	plateGui.Enabled = false
	local levelPrompt = newPrompt(
		player,
		plate,
		"Tycoon_LevelUp",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		"Shiba",
		LANE.LevelHoldSeconds,
		LANE.PromptDistance,
		function()
			actions.UpgradeShiba(player, slot, 1)
		end
	)
	local bigLevelPrompt = newPrompt(
		player,
		plate,
		"Tycoon_LevelUp10",
		Enum.KeyCode.F,
		Enum.KeyCode.ButtonY,
		"Shiba",
		LANE.LevelHoldSeconds,
		LANE.PromptDistance,
		function()
			actions.UpgradeShiba(player, slot, LANE.BigLevelStep)
		end
	)

	-- The Shiba itself: click/tap it (or press Q) to swing its stick. An invisible box around it takes the click, because
	-- the model is visual only. Automating the Shiba (R on the level plate) makes it swing by itself.
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
	local swingClick = Instance.new("ClickDetector")
	swingClick.MaxActivationDistance = 0
	swingClick.Parent = swingPart
	swingClick.MouseClick:Connect(function(clicker: Player)
		if clicker == player then
			actions.SwingShiba(player, slot)
		end
	end)
	local swingPrompt = newPrompt(
		player,
		swingPart,
		"Tycoon_Swing",
		Enum.KeyCode.Q,
		Enum.KeyCode.ButtonR1,
		"Shiba",
		0,
		LANE.PromptDistance,
		function()
			actions.SwingShiba(player, slot)
		end
	)
	local autoPrompt = newPrompt(
		player,
		plate,
		"Tycoon_Automate",
		Enum.KeyCode.R,
		Enum.KeyCode.ButtonL1,
		"Shiba",
		LANE.LevelHoldSeconds,
		LANE.PromptDistance,
		function()
			actions.BuyAutomation(player, slot)
		end
	)

	-- Belt spoke into the Mill: dark strip with a few glowing dashes (the client draws the items on top).
	local length = BELT.From - BELT.To
	local middle = island.Center + outward * ((BELT.From + BELT.To) / 2)
	local beltPosition = Vector3.new(middle.X, island.Center.Y + BELT.Top - BELT.Height / 2, middle.Z)
	local beltFrame = CFrame.lookAt(beltPosition, beltPosition + inward)
	local belt = newPart(`Belt_{slot}`, Vector3.new(BELT.Width, BELT.Height, length), beltFrame, BELT.Color, folder)
	belt.Transparency = 1
	local dashes: { Part } = {}
	for index = 1, BELT.DashCount do
		local along = -length / 2 + length * (index - 0.5) / BELT.DashCount
		local dash = newPart(
			"Dash",
			Vector3.new(BELT.Width * 0.6, 0.06, 1.2),
			beltFrame * CFrame.new(0, BELT.Height / 2 + 0.03, along),
			BELT.DashColor,
			belt
		)
		dash.Material = Enum.Material.Neon
		dash.Transparency = 1
		table.insert(dashes, dash)
	end

	-- Arch frames over the belt (built = solid, not yet built = ghost with a buy prompt).
	local arches: { ArchRefs } = {}
	for index, radius in ARCH.Radii do
		local at = island.Center + outward * radius
		local frame = CFrame.lookAt(at, at + inward)
		local model = Instance.new("Model")
		model.Name = `Arch{index}`
		local color = ARCH.OwnedColors[index] or ARCH.OwnedColors[1]
		local parts: { Part } = {}
		for _, side in { -1, 1 } do
			local post = newPart(
				"Post",
				Vector3.new(ARCH.Thickness, ARCH.Height, ARCH.Thickness),
				frame * CFrame.new(side * ARCH.Width / 2, ARCH.Height / 2 - 0.1, 0),
				color,
				model
			)
			table.insert(parts, post)
		end
		local beam = newPart(
			"Beam",
			Vector3.new(ARCH.Width + ARCH.Thickness, ARCH.Thickness, ARCH.Thickness),
			frame * CFrame.new(0, ARCH.Height - 0.1 + ARCH.Thickness / 2, 0),
			color,
			model
		)
		table.insert(parts, beam)
		for _, archPart in parts do
			archPart.Material = Enum.Material.Neon
			archPart.Transparency = 1
		end
		model.Parent = folder
		local prompt = newPrompt(
			player,
			beam,
			`Tycoon_Arch{index}`,
			Enum.KeyCode.E,
			Enum.KeyCode.ButtonX,
			"Lane arch",
			0,
			ARCH.PromptDistance,
			function()
				actions.UpgradeLane(player, "Arch", slot)
			end
		)
		table.insert(arches, { Parts = parts, Prompt = prompt })
	end

	folder.Parent = parent
	return {
		Folder = folder,
		Ground = ground,
		Inward = inward,
		Platform = platform,
		Ring = ring,
		Anchor = anchor,
		Gui = gui,
		Title = labels.Title,
		Sub = labels.Sub,
		Hint = labels.Hint,
		LockPlate = lockPlate,
		SlotPrompt = slotPrompt,
		Plate = plate,
		PlateGui = plateGui,
		LevelPrompt = levelPrompt,
		BigLevelPrompt = bigLevelPrompt,
		SwingPart = swingPart,
		SwingClick = swingClick,
		SwingPrompt = swingPrompt,
		AutoPrompt = autoPrompt,
		Belt = belt,
		Dashes = dashes,
		Arches = arches,
		Visual = nil,
		VisualKey = nil,
	}
end

-- The Shiba on a platform: its model (scaled, visual only), or a coloured block with the name as a fallback.
-- Returns the visual and its height in studs.
local function buildVisual(
	lane: { Ground: Vector3, Inward: Vector3, Folder: Folder },
	shiba: Types.OwnedShiba
): (Model, number)
	local def = EconomyConfig.Shibas[shiba.Tier + 1]
	local scale = if shiba.Variant == "Huge" then EconomyConfig.Variants.HugeScale else 1
	local height = (if def then def.Height else 6) * scale
	local standPoint = lane.Ground + Vector3.new(0, LANE.PlatformTop, 0)

	local cloned: Model? = nil
	if def and Assets.Has(def.AssetName) then
		cloned = Assets.CloneModel(def.AssetName)
	end
	local model: Model
	if cloned then
		model = cloned
		-- Clients pose the whole model, so it has to stream in one piece.
		model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
		Assets.ScaleTo(model, height, true)
		Assets.MakeVisualOnly(model, true)
		local box, size = model:GetBoundingBox()
		local pivotHeight = model:GetPivot().Position.Y - (box.Position.Y - size.Y / 2)
		local at = standPoint + Vector3.new(0, pivotHeight, 0)
		model:PivotTo(CFrame.lookAt(at, at + lane.Inward))
	else
		local fallback = Instance.new("Model")
		fallback.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
		local width = height * 0.6
		local color = if def then def.Color else Color3.fromRGB(255, 170, 60)
		local body = newPart(
			"Body",
			Vector3.new(width, height, width),
			CFrame.lookAt(
				standPoint + Vector3.new(0, height / 2, 0),
				standPoint + Vector3.new(0, height / 2, 0) + lane.Inward
			),
			color,
			fallback
		)
		Signs.Text(body, Enum.NormalId.Front, if def then def.Name else "Shiba", Color3.new(1, 1, 1), 60)
		fallback.PrimaryPart = body
		model = fallback
	end
	model.Name = "Shiba"

	-- Shiny / Rainbow / Huge: an outline in the variant's colour (clients cycle the hue of Rainbow and Huge).
	local look = ShibaEffects.Variants[shiba.Variant]
	if look then
		model:SetAttribute(ShibaEffects.VariantAttribute, shiba.Variant)
		local outline = Instance.new("Highlight")
		outline.Name = ShibaEffects.EditionOutlineName
		outline.FillColor = look.FillColor
		outline.FillTransparency = look.FillTransparency
		outline.OutlineColor = look.OutlineColor
		outline.OutlineTransparency = look.OutlineTransparency
		outline.DepthMode = Enum.HighlightDepthMode.Occluded
		outline.Parent = model
	end
	model.Parent = lane.Folder
	return model, height
end

local function milestoneHint(level: number, cap: number): string
	if level >= cap then
		return "Level cap reached"
	end
	local milestones = Tycoon.Lane.Milestones
	for _, milestone in milestones do
		if level < milestone then
			local left = milestone - level
			return `{left} more {if left == 1 then "level" else "levels"} until x{Tycoon.Lane.MilestoneMult}`
		end
	end
	local last = milestones[#milestones]
	local step = Tycoon.Lane.BeyondStep
	local nextAt = last + (math.floor((level - last) / step) + 1) * step
	local left = nextAt - level
	return `{left} more {if left == 1 then "level" else "levels"} until x{Tycoon.Lane.BeyondMult}`
end

local function refreshLane(lane: LaneRefs, tycoon: Types.TycoonState, slot: number)
	local unlocked = slot <= tycoon.EquipSlots
	local shiba, shibaId = shibaAt(tycoon, slot)
	if not unlocked then
		shiba, shibaId = nil, nil
	end
	local active = shiba ~= nil and shibaId ~= nil

	-- Platform and rim colours.
	local def = if shiba then EconomyConfig.Shibas[shiba.Tier + 1] else nil
	setColor(lane.Platform, if unlocked then Color3.fromRGB(95, 90, 110) else Color3.fromRGB(60, 52, 66))
	setColor(lane.Ring, if def then def.Color else Color3.fromRGB(120, 120, 140))

	-- Locked plate and the buy prompt of the next slot.
	setTransparency(lane.LockPlate, if unlocked then 1 else 0.2)
	local price = Tycoon.SlotPrices[slot]
	local isNext = slot == tycoon.EquipSlots + 1 and price ~= nil
	setPrompt(lane.SlotPrompt, isNext, if price then `Unlock slot {slot} - {number(price)}` else nil)

	-- Shiba visual: swap only when (id, tier, variant) changed.
	local key = if shiba and shibaId then `{shibaId}:{shiba.Tier}:{shiba.Variant}` else nil
	if key ~= lane.VisualKey then
		if lane.Visual then
			lane.Visual:Destroy()
			lane.Visual = nil
		end
		lane.VisualKey = key
		if shiba then
			local visual, height = buildVisual(lane, shiba)
			lane.Visual = visual
			lane.Gui.StudsOffset = Vector3.new(0, height + LANE.BillboardGap, 0)
		else
			lane.Gui.StudsOffset = Vector3.new(0, 6, 0)
		end
	end

	-- Billboard texts.
	setGuiEnabled(lane.Gui, true)
	local level = 0
	local cap = TycoonMath.LevelCap(tycoon.Ascensions)
	if shiba and def then
		level = shiba.Level
		local income = TycoonMath.LaneIncome(tycoon, slot) * TycoonMath.GlobalMultiplier(tycoon)
		local name = def.Name
		if shiba.Variant ~= "Normal" then
			name = `{shiba.Variant} {name}`
		end
		if shiba.Automated == true then
			name = `{name} [AUTO]`
		end
		setText(lane.Title, name)
		setText(lane.Sub, `Lv {level}  |  {number(income)}/s`)
		local hint = milestoneHint(level, cap)
		setText(lane.Hint, if shiba.Automated == true then hint else `Click me!  {hint}`)
	elseif unlocked then
		setText(lane.Title, "Empty")
		setText(lane.Sub, "Equip a Shiba")
		setText(lane.Hint, "")
	else
		setText(lane.Title, "Locked")
		setText(lane.Sub, if price then `Slot {slot}: {number(price)}` else `Slot {slot}`)
		setText(lane.Hint, if isNext then "" else `Unlock slot {slot - 1} first`)
	end

	-- Level plate and prompts.
	setTransparency(lane.Plate, if active then 0.1 else 1)
	setGuiEnabled(lane.PlateGui, active)
	if shiba and active then
		local oneCost = TycoonMath.LevelCost(shiba.Tier, level)
		local canLevel = level < cap
		setPrompt(lane.LevelPrompt, canLevel, if canLevel then `Level {level + 1} - {number(oneCost)}` else "Max level")
		local levels, spent = TycoonMath.LevelUpPlan(shiba.Tier, level, LANE.BigLevelStep, math.huge, cap)
		setPrompt(lane.BigLevelPrompt, levels > 1, if levels > 1 then `+{levels} levels - {number(spent)}` else nil)
	else
		setEnabled(lane.LevelPrompt, false)
		setEnabled(lane.BigLevelPrompt, false)
	end

	-- Swing (click / Q) and automation (R). An automated Shiba swings by itself.
	local manual = shiba ~= nil and active and shiba.Automated ~= true
	setPrompt(lane.SwingPrompt, manual, if manual then "Bonk!" else nil)
	lane.SwingClick.MaxActivationDistance = if manual then LANE.PromptDistance + 6 else 0
	if shiba and manual then
		local automationPrice = TycoonMath.AutomationPrice(shiba.Tier, TycoonMath.AutomatedCount(tycoon))
		setPrompt(lane.AutoPrompt, true, `Automate - {number(automationPrice)}`)
	else
		setEnabled(lane.AutoPrompt, false)
	end

	-- Belt.
	local beltTransparency = if active then 0 else 1
	setTransparency(lane.Belt, beltTransparency)
	for _, dash in lane.Dashes do
		setTransparency(dash, beltTransparency)
	end

	-- Arches.
	local built = tycoon.Arches[tostring(slot)] or 0
	for index, arch in lane.Arches do
		local color = ARCH.OwnedColors[index] or ARCH.OwnedColors[1]
		local transparency = 1
		if active then
			transparency = if index <= built then 0 else ARCH.GhostTransparency
		end
		for _, archPart in arch.Parts do
			setTransparency(archPart, transparency)
			setColor(archPart, if index <= built then color else ARCH.GhostColor)
		end
		local canBuy = active and shiba ~= nil and index == built + 1
		if canBuy and shiba then
			setPrompt(
				arch.Prompt,
				true,
				`Build arch {index} (x{Tycoon.Arch.Mult}) - {number(TycoonMath.ArchPrice(shiba.Tier, index))}`
			)
		else
			setEnabled(arch.Prompt, false)
		end
	end
end

-- ===== Mill and Vault ================================================================================================

local function buildMill(player: Player, island: IslandService.Island, parent: Folder, actions: Actions): MillRefs
	local model = Instance.new("Model")
	model.Name = "Mill"
	local center = island.Center
	local base = newDisc("Base", MILL.BaseRadius * 2, -0.4, MILL.BaseHeight, center, MILL.BaseColor, model)
	base.Material = Enum.Material.Slate
	base.CanCollide = true
	base.CanQuery = true
	local core = newDisc("Core", MILL.CoreRadius * 2, MILL.BaseHeight, MILL.CoreTop, center, MILL.BaseColor, model)
	core.Material = Enum.Material.Metal
	local orb = newBall("Orb", 3.6, center + Vector3.new(0, MILL.CoreTop + 1.4, 0), MILL.CoreColor, model)
	orb.Material = Enum.Material.Neon

	local anchor = newAnchor("PromptAnchor", CFrame.new(center + Vector3.new(0, 4, 0)), model)
	local rings: { RingRefs } = {}
	local prompts: { ProximityPrompt } = {}
	for index, def in MILL.Rings do
		local ringDef = Tycoon.Rings[index]
		local part = newDisc(ringDef.Id, def.Radius * 2, def.Bottom, def.Top, center, MILL.GhostColor, model)
		part.Transparency = MILL.GhostTransparency
		part.Material = Enum.Material.Metal
		table.insert(rings, { Part = part, OwnedColor = def.Color })
		local prompt = newPrompt(
			player,
			anchor,
			`Tycoon_Ring{ringDef.Id}`,
			Enum.KeyCode.E,
			Enum.KeyCode.ButtonX,
			"Bonk Mill",
			0,
			MILL.PromptDistance,
			function()
				actions.BuyPad(player, ringDef.Id)
			end
		)
		table.insert(prompts, prompt)
	end
	model.Parent = parent
	return { Rings = rings, Prompts = prompts }
end

local function buildVault(player: Player, island: IslandService.Island, parent: Folder, actions: Actions): VaultRefs
	local model = Instance.new("Model")
	model.Name = "Vault"
	local angle = island.HubAngle + math.rad(VAULT.Angle)
	local outward = direction(angle)
	local at = island.Center + outward * VAULT.Radius
	local frame = CFrame.lookAt(at, at - outward)
	local chest = newPart("Chest", Vector3.new(5, 2.6, 3.4), frame * CFrame.new(0, 1.3, 0), VAULT.Color, model)
	chest.Material = Enum.Material.Wood
	chest.CanCollide = true
	chest.CanQuery = true
	local lid = newPart("Lid", Vector3.new(5.2, 0.8, 3.6), frame * CFrame.new(0, 3, 0), VAULT.Color, model)
	lid.Material = Enum.Material.Wood
	local band = newPart("Band", Vector3.new(5.3, 0.3, 0.6), frame * CFrame.new(0, 2.65, -1.7), VAULT.GoldColor, model)
	band.Material = Enum.Material.Foil
	-- Glowing gold pile on the lid, only while something is stored.
	local pile: { Part } = {}
	local spots =
		{ Vector3.new(-1.2, 0, 0.3), Vector3.new(0.3, 0, -0.5), Vector3.new(1.3, 0, 0.4), Vector3.new(0, 0.9, 0) }
	for index, offset in spots do
		local ball = newBall(
			"Gold",
			if index == 4 then 1.8 else 2.2,
			(frame * CFrame.new(offset + Vector3.new(0, 4.2, 0))).Position,
			VAULT.GoldColor,
			model
		)
		ball.Material = Enum.Material.Neon
		ball.Transparency = 1
		table.insert(pile, ball)
	end
	local gui, labels = newBillboard(chest, 200, 4.2, 90, {
		{ Name = "Title", Height = 22, TextSize = 20, Color = TEXT.Title },
		{ Name = "Amount", Height = 24, TextSize = 22, Color = VAULT.GoldColor },
	})
	setText(labels.Title, "Vault")
	local prompt = newPrompt(
		player,
		chest,
		"Tycoon_Collect",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		"Vault",
		0,
		VAULT.PromptDistance,
		function()
			actions.CollectVault(player)
		end
	)
	model.Parent = parent
	return { Pile = pile, Gui = gui, Amount = labels.Amount, Prompt = prompt }
end

local function refreshMill(plot: Plot, tycoon: Types.TycoonState)
	local nextRing: number? = nil
	for index, ringDef in Tycoon.Rings do
		if not tycoon.Pads[ringDef.Id] then
			nextRing = index
			break
		end
	end
	for index, ring in plot.Mill.Rings do
		local ringDef = Tycoon.Rings[index]
		local owned = tycoon.Pads[ringDef.Id] == true
		setTransparency(ring.Part, if owned then 0 else MILL.GhostTransparency)
		setColor(ring.Part, if owned then ring.OwnedColor else MILL.GhostColor)
		local prompt = plot.Mill.Prompts[index]
		setPrompt(prompt, index == nextRing, `Buy {ringDef.Id} (x{ringDef.Mult} all lanes) - {number(ringDef.Price)}`)
	end
end

local function refreshVault(plot: Plot, tycoon: Types.TycoonState)
	local stored = tycoon.VaultStored
	local has = stored >= 1
	local vault = plot.Vault
	for _, ball in vault.Pile do
		setTransparency(ball, if has then 0 else 1)
	end
	setGuiEnabled(vault.Gui, true)
	setText(vault.Amount, number(math.floor(stored)))
	setPrompt(vault.Prompt, has, `Collect {number(math.floor(stored))}`)
end

-- ===== eggs ==========================================================================================================

local function oddsText(zone: number): string
	local lines: { string } = {}
	for index, weight in Tycoon.EggWeights do
		local def = EconomyConfig.Shibas[zone * Tycoon.TiersPerZone + index]
		table.insert(lines, `{if def then def.Name else "?"}  {weight}%`)
	end
	local chances = EconomyConfig.Variants.OneIn
	table.insert(lines, `Shiny 1/{chances.Shiny}  Rainbow 1/{chances.Rainbow}  Huge 1/{chances.Huge}`)
	return table.concat(lines, "\n")
end

local function buildEgg(
	player: Player,
	island: IslandService.Island,
	zone: number,
	parent: Folder,
	actions: Actions
): EggRefs
	local zoneDef = Tycoon.Zones[zone + 1]
	local angle = island.HubAngle + math.rad(EGGS.Angles[zone + 1] or 180)
	local at = island.Center + direction(angle) * EGGS.Radius
	local frame = CFrame.lookAt(at, Vector3.new(island.Center.X, at.Y, island.Center.Z))
	local model = Instance.new("Model")
	model.Name = `Egg_{zone}`
	local parts: { Part } = {}

	local base = newDisc("Base", EGGS.BaseDiameter, -0.4, 0.8, at, Color3.fromRGB(95, 90, 110), model)
	base.Material = Enum.Material.Slate
	base.CanCollide = true
	base.CanQuery = true
	table.insert(parts, base)
	local eggCenter = frame * CFrame.new(0, 0.8 + EGGS.EggSize.Y / 2, 0)
	local egg = newPart("Egg", EGGS.EggSize, eggCenter, EGGS.ZoneColors[zone + 1] or EGGS.ZoneColors[1], model)
	egg.Material = Enum.Material.SmoothPlastic
	local mesh = Instance.new("SpecialMesh")
	mesh.MeshType = Enum.MeshType.Sphere
	mesh.Parent = egg
	table.insert(parts, egg)

	local spots: { Part } = {}
	for _, offset in { Vector3.new(1.5, 1, -2.5), Vector3.new(-1.6, -1.5, -2.3), Vector3.new(0.3, 2.8, -1.9) } do
		local spot =
			newBall("Spot", 1.3, (eggCenter * CFrame.new(offset)).Position, Color3.fromRGB(255, 255, 255), model)
		spot.Transparency = 1
		table.insert(spots, spot)
		table.insert(parts, spot)
	end

	local gui, labels = newBillboard(egg, 230, EGGS.EggSize.Y / 2 + 4, 100, {
		{ Name = "Title", Height = 24, TextSize = 22, Color = TEXT.Title },
		{ Name = "Price", Height = 22, TextSize = 20, Color = TEXT.Hint },
		{ Name = "Odds", Height = 104, TextSize = 14, Color = TEXT.Muted },
	})
	labels.Odds.TextYAlignment = Enum.TextYAlignment.Top
	local price = TycoonMath.EggPrice(zone)
	local hatch1 = newPrompt(
		player,
		egg,
		"Tycoon_Hatch1",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		`{zoneDef.Name} Egg`,
		EGGS.HatchHoldSeconds,
		EGGS.PromptDistance,
		function()
			actions.HatchEgg(player, `Egg{zone}`, 1)
		end
	)
	hatch1.ActionText = `Hatch x1 - {number(price)}`
	local hatch3 = newPrompt(
		player,
		egg,
		"Tycoon_Hatch3",
		Enum.KeyCode.F,
		Enum.KeyCode.ButtonY,
		`{zoneDef.Name} Egg`,
		EGGS.HatchHoldSeconds,
		EGGS.PromptDistance,
		function()
			actions.HatchEgg(player, `Egg{zone}`, 3)
		end
	)
	hatch3.ActionText = `Hatch x3 - {number(price * 3)}`
	local unlock = newPrompt(
		player,
		egg,
		"Tycoon_Zone",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		`{zoneDef.Name} zone`,
		0,
		EGGS.PromptDistance,
		function()
			actions.BuyPad(player, `Zone{zone}`)
		end
	)
	unlock.ActionText = `Unlock {zoneDef.Name} - {number(zoneDef.Price)}`

	for _, hidden in parts do
		hidden.Transparency = 1
	end
	model.Parent = parent
	return {
		Model = model,
		Parts = parts,
		Egg = egg,
		Spots = spots,
		Gui = gui,
		Title = labels.Title,
		Price = labels.Price,
		Odds = labels.Odds,
		OddsText = oddsText(zone),
		Hatch1 = hatch1,
		Hatch3 = hatch3,
		Unlock = unlock,
		Mode = "hidden",
	}
end

local function refreshEgg(egg: EggRefs, zone: number, tycoon: Types.TycoonState)
	local mode = "hidden"
	if zone <= tycoon.Zone then
		mode = "open"
	elseif zone == tycoon.Zone + 1 and zone <= Tycoon.MaxZone then
		mode = "next"
	end
	if mode == egg.Mode then
		return
	end
	egg.Mode = mode
	local zoneDef = Tycoon.Zones[zone + 1]
	local shown = mode ~= "hidden"
	for _, part in egg.Parts do
		setTransparency(part, if shown then 0 else 1)
	end
	setGuiEnabled(egg.Gui, shown)
	setPrompt(egg.Hatch1, mode == "open", nil)
	setPrompt(egg.Hatch3, mode == "open", nil)
	setPrompt(egg.Unlock, mode == "next", nil)
	if mode == "open" then
		setColor(egg.Egg, EGGS.ZoneColors[zone + 1] or EGGS.ZoneColors[1])
		setTransparency(egg.Egg, 0)
		for _, spot in egg.Spots do
			setTransparency(spot, 0)
		end
		setText(egg.Title, `{zoneDef.Name} Egg`)
		setText(egg.Price, number(TycoonMath.EggPrice(zone)))
		setText(egg.Odds, egg.OddsText)
	elseif mode == "next" then
		-- A dark silhouette, price of the zone on the sign.
		setColor(egg.Egg, EGGS.LockedColor)
		setTransparency(egg.Egg, EGGS.LockedTransparency)
		for _, spot in egg.Spots do
			setTransparency(spot, 1)
		end
		setText(egg.Title, `{zoneDef.Name} zone`)
		setText(egg.Price, `Unlock: {number(zoneDef.Price)}`)
		setText(egg.Odds, "Locked")
	end
end

-- ===== shrine ========================================================================================================

local function buildShrine(player: Player, island: IslandService.Island, parent: Folder, actions: Actions): ShrineRefs
	local angle = island.HubAngle + math.rad(SHRINE.Angle)
	local at = island.Center + direction(angle) * SHRINE.Radius
	local frame = CFrame.lookAt(at, Vector3.new(island.Center.X, at.Y, island.Center.Z))
	local shrine =
		PropService.Place(Stations.RebirthPropName, frame, SHRINE.Height, PropService.Builders.RebirthShrine, parent)
	shrine.Name = "Ascension"
	local anchor = newAnchor("PromptAnchor", frame * CFrame.new(0, SHRINE.Height * 0.45, -2), shrine)
	local gui, labels = newBillboard(anchor, 220, 5, 100, {
		{ Name = "Title", Height = 24, TextSize = 22, Color = TEXT.Title },
		{ Name = "Sub", Height = 20, TextSize = 16, Color = TEXT.Hint },
	})
	setText(labels.Title, "Ascension")
	local prompt = newPrompt(
		player,
		anchor,
		"Tycoon_Ascend",
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		"Ascension Shrine",
		SHRINE.HoldSeconds,
		SHRINE.PromptDistance,
		function()
			actions.BuyPad(player, "Ascend")
		end
	)
	return { Prompt = prompt, Gui = gui, Sub = labels.Sub }
end

local function refreshShrine(plot: Plot, tycoon: Types.TycoonState)
	local ready = tycoon.Zone >= Tycoon.Ascension.MinZone
	local multiplier = TycoonMath.AscensionMultiplier(tycoon.Ascensions + 1)
	local shrine = plot.Shrine
	setGuiEnabled(shrine.Gui, true)
	if ready then
		setText(shrine.Sub, `Resets progress, income x{string.format("%g", multiplier)}`)
	else
		local zoneDef = Tycoon.Zones[Tycoon.Ascension.MinZone + 1]
		setText(shrine.Sub, `Needs the {if zoneDef then zoneDef.Name else "last"} zone`)
	end
	setPrompt(shrine.Prompt, ready, `Ascend - income x{string.format("%g", multiplier)}`)
end

-- ===== public API ====================================================================================================

function TycoonPlot.Destroy(player: Player)
	local plot = plots[player]
	plots[player] = nil
	if plot then
		plot.Folder:Destroy()
	end
end

-- Builds the whole plot (everything hidden / disabled) under island.Model; call Refresh with the state afterwards.
function TycoonPlot.Build(player: Player, island: IslandService.Island, actions: Actions)
	TycoonPlot.Destroy(player)
	local folder = Instance.new("Folder")
	folder.Name = TycoonWorld.FolderName
	local lanes: { LaneRefs } = {}
	for slot = 1, MAX_SLOTS do
		table.insert(lanes, buildLane(player, island, slot, folder, actions))
	end
	local mill = buildMill(player, island, folder, actions)
	local vault = buildVault(player, island, folder, actions)
	local eggs: { EggRefs } = {}
	for zone = 0, Tycoon.MaxZone do
		table.insert(eggs, buildEgg(player, island, zone, folder, actions))
	end
	local shrine = buildShrine(player, island, folder, actions)
	folder.Parent = island.Model
	plots[player] = {
		Folder = folder,
		Center = island.Center,
		Lanes = lanes,
		Mill = mill,
		Vault = vault,
		Eggs = eggs,
		Shrine = shrine,
	}
end

-- Brings everything in line with state.Tycoon. Idempotent and cheap: only changed properties are written.
function TycoonPlot.Refresh(player: Player, state: Types.PlayerState)
	local plot = plots[player]
	local tycoon = state.Tycoon
	if not plot or not tycoon then
		return
	end
	if plot.Folder.Parent == nil then
		-- The island is gone (the player left): drop the plot.
		plots[player] = nil
		return
	end
	for slot, lane in plot.Lanes do
		refreshLane(lane, tycoon, slot)
	end
	refreshMill(plot, tycoon)
	refreshVault(plot, tycoon)
	for index, egg in plot.Eggs do
		refreshEgg(egg, index - 1, tycoon)
	end
	refreshShrine(plot, tycoon)
end

-- Where the belt of lane `slot` starts (Shiba side), a little above the belt.
function TycoonPlot.GetLaneAnchor(player: Player, slot: number): Vector3?
	local plot = plots[player]
	local lane = if plot then plot.Lanes[slot] else nil
	if not plot or not lane then
		return nil
	end
	local outward = -lane.Inward
	local point = plot.Center + outward * BELT.From
	return Vector3.new(point.X, plot.Center.Y + BELT.Top + 0.5, point.Z)
end

-- Where the Shiba of lane `slot` stands and which way it faces (toward the Mill), for the server's hit check.
function TycoonPlot.GetLaneAim(player: Player, slot: number): { Origin: Vector3, Forward: Vector3 }?
	local plot = plots[player]
	local lane = if plot then plot.Lanes[slot] else nil
	if not lane then
		return nil
	end
	return { Origin = lane.Ground + Vector3.new(0, LANE.PlatformTop, 0), Forward = lane.Inward }
end

-- Used by StreetPlot (the street's plot), so both plots draw prompts, billboards and Shibas the same way.
TycoonPlot.NewPrompt = newPrompt
TycoonPlot.NewBillboard = newBillboard
TycoonPlot.BuildShibaVisual = buildVisual

return TycoonPlot
