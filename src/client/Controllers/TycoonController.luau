--!strict
-- Client side of the tycoon "Shiba Workers" (docs/decisions/0006, docs/TYCOON_HANDOFF.md). Everything here is
-- cosmetic or a request; the server decides all income. Inert until state.Tycoon.Enabled is true:
-- - TycoonPayout: rising "+1.2K" numbers above the lane.
-- - Belt items: small parts travelling Shiba side -> Mill on Belt_<slot>, rate from the lane's income (pooled).
-- - HatchResults: reveal cards (UI/TycoonPanels).
-- - Collection panel "Shibas" (UI/TycoonPanels), key B, TycoonController.OpenCollection() for the HUD.
-- - Golden Crates: CrateSpawned puts a crate on the belt; click/tap/touch fires CollectCrate once.
-- World names it reads (Workspace/Islands/Island_<UserId>/Tycoon): Mill, Lane_<slot>, Belt_<slot>. All optional.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local TycoonConfig = require(ReplicatedStorage.Shared.Config.Tycoon)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local Types = require(ReplicatedStorage.Shared.Types)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local TycoonPanels = require(script.Parent.Parent.UI.TycoonPanels)

type TycoonState = Types.TycoonState

local MAX_POPUPS = 12
local POPUP_SECONDS = 1.2
local POPUP_RISE = 5
local MAX_BELT_ITEMS = 60
local MAX_ITEMS_PER_LANE_PER_SECOND = 3
local MIN_ITEMS_PER_LANE_PER_SECOND = 0.5
-- Income (per second) at which a lane spawns the maximum rate; below it the rate follows log10.
local RATE_LOG_CEILING = 6
local BELT_START_RADIUS = 50
local BELT_SPEED = 14 -- studs per second
local VISIBLE_DISTANCE = 320
local GEOMETRY_TTL = 2
local CRATE_MAX = 20
local CRATE_REACH = 7
local CRATE_SIZE = 3
local GOLD = Color3.fromRGB(255, 205, 40)
local BONK_RED = Color3.fromRGB(255, 90, 70)
local VARIANT_IDS: { [string]: boolean } = { Normal = true, Shiny = true, Rainbow = true, Huge = true }

type BeltGeometry = { Start: Vector3, Finish: Vector3, Length: number, Mid: Vector3, At: number }

type BeltItem = { Part: Part, Slot: number, Alpha: number, Speed: number, Geometry: BeltGeometry }

type Popup = { Anchor: Part, Alive: boolean }

type Crate = {
	Id: number,
	Part: Part,
	Slot: number,
	StartedAt: number,
	EndsAt: number,
	Geometry: BeltGeometry,
	Collected: boolean,
	Click: ClickDetector,
}

local player = Players.LocalPlayer

local active = false
local streetMode = false
local started = false
local heartbeat: RBXScriptConnection? = nil
local worldFolder: Folder? = nil

local popups: { Popup } = {}
local pool: { Part } = {}
local items: { BeltItem } = {}
local crates: { [number]: Crate } = {}
local crateCount = 0
local geometryCache: { [number]: BeltGeometry } = {}
local laneRate: { [number]: number } = {}
local laneColor: { [number]: Color3 } = {}
local spawnAccumulator: { [number]: number } = {}
local cachedIncome = 0
local tycoonFolder: Instance? = nil
local tycoonFolderAt = 0

local TycoonController = {}

-- ==== state ======================================================================================================

local function currentTycoon(): TycoonState?
	local state = State.Get()
	local tycoon = if state then state.Tycoon else nil
	if tycoon and tycoon.Enabled then
		return tycoon
	end
	return nil
end

function TycoonController.IsEnabled(): boolean
	return currentTycoon() ~= nil
end

-- Raw income per second of the whole ring (no pass / boost / event / friend multipliers: the server adds those).
function TycoonController.GetIncomePerSecond(): number
	return cachedIncome
end

function TycoonController.OpenCollection()
	if currentTycoon() and not streetMode then
		TycoonPanels.OpenCollection()
	end
end

-- ==== world lookup ===============================================================================================

local function findTycoonFolder(): Instance?
	local now = os.clock()
	if tycoonFolder and tycoonFolder.Parent and now - tycoonFolderAt < 5 then
		return tycoonFolder
	end
	tycoonFolder = nil
	local islands = Workspace:FindFirstChild("Islands")
	local island = if islands then islands:FindFirstChild(`Island_{player.UserId}`) else nil
	local folder = if island then island:FindFirstChild("Tycoon") else nil
	tycoonFolder = folder
	tycoonFolderAt = now
	return folder
end

-- Position and size of a Model, BasePart, or the first BasePart inside a Folder.
local function boundsOf(instance: Instance?): (CFrame?, Vector3?)
	if not instance then
		return nil
	end
	if instance:IsA("Model") then
		local ok, cframe, size = pcall(function()
			return instance:GetBoundingBox()
		end)
		if ok then
			return cframe :: CFrame, size :: Vector3
		end
		return nil
	elseif instance:IsA("BasePart") then
		return instance.CFrame, instance.Size
	end
	for _, descendant in instance:GetDescendants() do
		if descendant:IsA("BasePart") then
			return descendant.CFrame, descendant.Size
		end
	end
	return nil
end

local function flat(vector: Vector3): Vector3
	return Vector3.new(vector.X, 0, vector.Z)
end

-- Belt path of a slot: from the Shiba side (radius 50 around the Mill) to the Mill centre.
local function beltGeometry(slot: number): BeltGeometry?
	local cached = geometryCache[slot]
	local now = os.clock()
	if cached and now - cached.At < GEOMETRY_TTL then
		return cached
	end
	local folder = findTycoonFolder()
	if not folder then
		return nil
	end
	local millCFrame = boundsOf(folder:FindFirstChild("Mill"))
	local beltCFrame, beltSize = boundsOf(folder:FindFirstChild(`Belt_{slot}`))
	if not millCFrame or not beltCFrame or not beltSize then
		return cached
	end
	local millPosition = millCFrame.Position
	local direction = flat(beltCFrame.Position - millPosition)
	if direction.Magnitude < 0.1 then
		return cached
	end
	direction = direction.Unit
	local height = beltCFrame.Position.Y + beltSize.Y / 2 + 0.8
	local start = Vector3.new(millPosition.X, height, millPosition.Z) + direction * BELT_START_RADIUS
	local finish = Vector3.new(millPosition.X, height, millPosition.Z)
	local geometry: BeltGeometry = {
		Start = start,
		Finish = finish,
		Length = (start - finish).Magnitude,
		Mid = start:Lerp(finish, 0.5),
		At = now,
	}
	geometryCache[slot] = geometry
	return geometry
end

-- Where a popup for `slot` appears: above Lane_<slot>, else above the Mill.
local function popupPosition(slot: number): Vector3?
	local folder = findTycoonFolder()
	if not folder then
		return nil
	end
	local cframe, size = boundsOf(folder:FindFirstChild(`Lane_{slot}`))
	if not cframe or not size then
		cframe, size = boundsOf(folder:FindFirstChild("Mill"))
	end
	if not cframe or not size then
		return nil
	end
	return cframe.Position + Vector3.new(0, size.Y / 2 + 2, 0)
end

local function getWorldFolder(): Folder
	local folder = worldFolder
	if folder and folder.Parent then
		return folder
	end
	local created = Instance.new("Folder")
	created.Name = "TycoonClientVisuals"
	created.Parent = Workspace
	worldFolder = created
	return created
end

local function makeVisualPart(size: Vector3): Part
	local part = Instance.new("Part")
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Size = size
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	return part
end

-- ==== payout popups ==============================================================================================

local function destroyPopup(popup: Popup)
	popup.Alive = false
	popup.Anchor:Destroy()
	local index = table.find(popups, popup)
	if index then
		table.remove(popups, index)
	end
end

local function showPopup(slot: number, amount: number, source: string)
	local position = popupPosition(slot)
	if not position then
		return
	end
	while #popups >= MAX_POPUPS do
		destroyPopup(popups[1])
	end

	local anchor = makeVisualPart(Vector3.new(0.2, 0.2, 0.2))
	anchor.Transparency = 1
	anchor.Position = position + Vector3.new(math.random(-15, 15) / 10, 0, math.random(-15, 15) / 10)
	anchor.Parent = getWorldFolder()
	local popup: Popup = { Anchor = anchor, Alive = true }
	table.insert(popups, popup)

	local gui = Instance.new("BillboardGui")
	gui.Adornee = anchor
	gui.AlwaysOnTop = true
	gui.Size = UDim2.fromOffset(160, 40)
	gui.MaxDistance = 260
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false
	gui.Parent = anchor

	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Theme.Font
	label.Text = `+{Format.Short(amount)}`
	label.TextSize = 28
	label.TextColor3 = if source == "Crate" then GOLD elseif source == "Bonk" then BONK_RED else Theme.Money
	label.TextStrokeColor3 = Theme.Stroke
	label.TextStrokeTransparency = 0
	label.Parent = gui

	TweenService:Create(
		anchor,
		TweenInfo.new(POPUP_SECONDS, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ Position = anchor.Position + Vector3.new(0, POPUP_RISE, 0) }
	):Play()
	TweenService:Create(
		label,
		TweenInfo.new(
			POPUP_SECONDS * 0.45,
			Enum.EasingStyle.Linear,
			Enum.EasingDirection.In,
			0,
			false,
			POPUP_SECONDS * 0.55
		),
		{ TextTransparency = 1, TextStrokeTransparency = 1 }
	):Play()
	task.delay(POPUP_SECONDS + 0.1, function()
		if popup.Alive then
			destroyPopup(popup)
		end
	end)
end

-- ==== belt items =================================================================================================

local function takeItemPart(): Part?
	local part = table.remove(pool)
	if part then
		return part
	end
	if #items >= MAX_BELT_ITEMS then
		return nil
	end
	local created = makeVisualPart(Vector3.new(1.3, 1.3, 1.3))
	created.Shape = Enum.PartType.Ball
	created.Material = Enum.Material.SmoothPlastic
	created.Name = "BeltItem"
	return created
end

local function releaseItem(index: number)
	local item = items[index]
	table.remove(items, index)
	item.Part.Parent = nil
	table.insert(pool, item.Part)
end

local function clearItems()
	for index = #items, 1, -1 do
		releaseItem(index)
	end
	for _, part in pool do
		part:Destroy()
	end
	table.clear(pool)
end

-- Items per second of a lane: log-scaled income, at most 3.
local function itemRate(income: number): number
	if income <= 0 then
		return 0
	end
	local share = math.clamp(math.log10(income + 1) / RATE_LOG_CEILING, 0, 1)
	return MIN_ITEMS_PER_LANE_PER_SECOND + (MAX_ITEMS_PER_LANE_PER_SECOND - MIN_ITEMS_PER_LANE_PER_SECOND) * share
end

local function spawnItem(slot: number, geometry: BeltGeometry)
	if #items >= MAX_BELT_ITEMS then
		return
	end
	local part = takeItemPart()
	if not part then
		return
	end
	part.Color = laneColor[slot] or Theme.Accent
	part.Position = geometry.Start
	part.Parent = getWorldFolder()
	table.insert(items, {
		Part = part,
		Slot = slot,
		Alpha = 0,
		Speed = BELT_SPEED / math.max(geometry.Length, 1),
		Geometry = geometry,
	})
end

-- Recomputes the per-lane rates and colours from the saved tycoon state (display only).
local function refreshLanes(tycoon: TycoonState)
	table.clear(laneRate)
	table.clear(laneColor)
	local ok, total = pcall(TycoonMath.TotalIncome, tycoon)
	cachedIncome = if ok and typeof(total) == "number" then total else 0
	for slot = 1, tycoon.EquipSlots do
		local okLane, income = pcall(TycoonMath.LaneIncome, tycoon, slot)
		if okLane and typeof(income) == "number" and income > 0 then
			laneRate[slot] = itemRate(income)
			local id = tycoon.Equipped[tostring(slot)]
			local shiba = if id then tycoon.Shibas[id] else nil
			local def = if shiba then EconomyConfig.Shibas[shiba.Tier + 1] else nil
			if def then
				laneColor[slot] = def.Color
			end
		end
	end
end

-- ==== golden crates ==============================================================================================

local function cratePosition(crate: Crate, alpha: number, now: number): Vector3
	local base = crate.Geometry.Start:Lerp(crate.Geometry.Finish, alpha)
	return base + Vector3.new(0, CRATE_SIZE / 2 + math.sin(now * 4 + crate.Id) * 0.3, 0)
end

local function removeCrate(crate: Crate)
	if crates[crate.Id] == crate then
		crates[crate.Id] = nil
		crateCount -= 1
	end
	crate.Part:Destroy()
end

local function collectCrate(crate: Crate)
	if crate.Collected then
		return
	end
	crate.Collected = true
	Net.Get(Net.CollectCrate):FireServer(crate.Id)
	-- Pop out quickly; the payout number comes from the server (TycoonPayout).
	crate.Click.MaxActivationDistance = 0
	TweenService:Create(
		crate.Part,
		TweenInfo.new(0.2, Enum.EasingStyle.Back, Enum.EasingDirection.In),
		{ Size = Vector3.new(0.1, 0.1, 0.1), Transparency = 1 }
	):Play()
	task.delay(0.25, function()
		removeCrate(crate)
	end)
end

local function spawnCrate(crateId: number, slot: number, endsAt: number)
	if crates[crateId] or crateCount >= CRATE_MAX then
		return
	end
	local geometry = beltGeometry(slot)
	local now = Workspace:GetServerTimeNow()
	if not geometry or endsAt <= now + 0.2 then
		return
	end

	local part = makeVisualPart(Vector3.new(CRATE_SIZE, CRATE_SIZE, CRATE_SIZE))
	part.Name = "GoldenCrate"
	part.Color = GOLD
	part.Material = Enum.Material.Neon
	part.CanQuery = true -- click detectors need to be hit by the mouse ray
	part.CanTouch = true
	part.Position = geometry.Start
	part.Parent = getWorldFolder()

	local click = Instance.new("ClickDetector")
	click.MaxActivationDistance = 400
	click.Parent = part

	local gui = Instance.new("BillboardGui")
	gui.Adornee = part
	gui.AlwaysOnTop = true
	gui.Size = UDim2.fromOffset(120, 30)
	gui.StudsOffset = Vector3.new(0, 3, 0)
	gui.MaxDistance = 300
	gui.LightInfluence = 0
	gui.Parent = part
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Size = UDim2.fromScale(1, 1)
	text.Font = Theme.Font
	text.Text = "TAP!"
	text.TextSize = 24
	text.TextColor3 = GOLD
	text.TextStrokeColor3 = Theme.Stroke
	text.TextStrokeTransparency = 0
	text.Parent = gui

	local crate: Crate = {
		Id = crateId,
		Part = part,
		Slot = slot,
		StartedAt = now,
		EndsAt = endsAt,
		Geometry = geometry,
		Collected = false,
		Click = click,
	}
	crates[crateId] = crate
	crateCount += 1
	click.MouseClick:Connect(function()
		collectCrate(crate)
	end)
	part.Touched:Connect(function(other: BasePart)
		local character = player.Character
		if character and other:IsDescendantOf(character) then
			collectCrate(crate)
		end
	end)
end

local function updateCrates(now: number)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local rootPosition = if root and root:IsA("BasePart") then root.Position else nil
	local clock = os.clock()
	for _, crate in crates do
		if crate.Collected then
			continue
		end
		local span = math.max(crate.EndsAt - crate.StartedAt, 0.1)
		local alpha = (now - crate.StartedAt) / span
		if alpha >= 1 then
			removeCrate(crate)
			continue
		end
		local position = cratePosition(crate, math.max(alpha, 0), clock)
		crate.Part.CFrame = CFrame.new(position) * CFrame.Angles(0, clock * 2, 0)
		if rootPosition and (rootPosition - position).Magnitude <= CRATE_REACH then
			collectCrate(crate)
		end
	end
end

-- ==== frame update ===============================================================================================

local function onHeartbeat(dt: number)
	if not active then
		return
	end
	local camera = Workspace.CurrentCamera
	local focus = if camera then camera.CFrame.Position else nil

	-- Move items and return the ones that reached the Mill.
	for index = #items, 1, -1 do
		local item = items[index]
		item.Alpha += dt * item.Speed
		if item.Alpha >= 1 then
			releaseItem(index)
		else
			item.Part.Position = item.Geometry.Start:Lerp(item.Geometry.Finish, item.Alpha)
		end
	end

	-- Spawn new ones per lane.
	for slot, rate in laneRate do
		if streetMode then
			-- The street has no belts: the swing and the popups are the feedback.
			break
		end
		local geometry = beltGeometry(slot)
		if geometry and (not focus or (geometry.Mid - focus).Magnitude < VISIBLE_DISTANCE) then
			local accumulated = math.min((spawnAccumulator[slot] or 0) + dt * rate, 2)
			while accumulated >= 1 do
				accumulated -= 1
				spawnItem(slot, geometry)
			end
			spawnAccumulator[slot] = accumulated
		end
	end

	updateCrates(Workspace:GetServerTimeNow())
end

-- ==== activation =================================================================================================

local function deactivate()
	if not active then
		return
	end
	active = false
	if heartbeat then
		heartbeat:Disconnect()
		heartbeat = nil
	end
	clearItems()
	for _, crate in crates do
		removeCrate(crate)
	end
	for index = #popups, 1, -1 do
		destroyPopup(popups[index])
	end
	table.clear(spawnAccumulator)
	table.clear(geometryCache)
	TycoonPanels.CloseCollection()
end

local function activate()
	if active then
		return
	end
	active = true
	TycoonPanels.BuildCollection(currentTycoon)
	heartbeat = RunService.Heartbeat:Connect(onHeartbeat)
end

local function onStateChanged()
	local tycoon = currentTycoon()
	if not tycoon then
		cachedIncome = 0
		deactivate()
		return
	end
	activate()
	streetMode = tycoon.Street == true
	refreshLanes(tycoon)
	TycoonPanels.RefreshCollection(false)
end

-- ==== remotes ====================================================================================================

local function onPayout(slot: unknown, amount: unknown, source: unknown)
	if not active or typeof(slot) ~= "number" or typeof(amount) ~= "number" then
		return
	end
	if amount ~= amount or amount <= 0 or amount == math.huge then
		return
	end
	showPopup(math.floor(slot), amount, if typeof(source) == "string" then source else "")
end

local function onCrateSpawned(crateId: unknown, slot: unknown, endsAt: unknown)
	if not active or typeof(crateId) ~= "number" or typeof(slot) ~= "number" or typeof(endsAt) ~= "number" then
		return
	end
	spawnCrate(crateId, math.floor(slot), endsAt)
end

local function onHatchResults(eggId: unknown, results: unknown)
	if not active or typeof(eggId) ~= "string" or typeof(results) ~= "table" then
		return
	end
	local clean: { Types.HatchResult } = {}
	for _, entry in results :: { unknown } do
		if typeof(entry) == "table" then
			local row = entry :: { [string]: unknown }
			local tier, variant, shibaId = row.Tier, row.Variant, row.ShibaId
			if
				typeof(tier) == "number"
				and typeof(variant) == "string"
				and VARIANT_IDS[variant]
				and typeof(shibaId) == "string"
				and EconomyConfig.Shibas[tier + 1] ~= nil
			then
				table.insert(clean, {
					ShibaId = shibaId,
					Tier = tier,
					Variant = variant :: Types.VariantId,
					Duplicate = row.Duplicate == true,
				})
			end
		end
		if #clean >= 10 then
			break
		end
	end
	if #clean > 0 then
		TycoonPanels.ShowHatch(clean)
	end
end

-- A prompt of any island's tycoon plot (Islands.Island_<UserId>.Tycoon …) that is not ours: the server only forwards the
-- owner's trigger, so the others' prompts are hidden on this client.
local function isForeignTycoonPrompt(prompt: ProximityPrompt): boolean
	local plot = prompt:FindFirstAncestor(TycoonWorld.FolderName)
	local island = if plot then plot.Parent else nil
	local islands = if island then island.Parent else nil
	if island == nil or islands == nil or islands.Name ~= Gameplay.Island.FolderName then
		return false
	end
	return island.Name ~= `{Gameplay.Island.ModelPrefix}{player.UserId}`
end

-- ==== swing (ShibaSwung / PlayerBonked) ==========================================================================
-- Visual only: a stick swings over the Shiba like the "Bonk" meme (wind-up, strike, recovery), timed to the Shiba's cooldown
-- (docs/GAME_DESIGN.md → Swing, click and Bonk hit). Manual Shibas also show a faint red hit zone; automated Shibas show
-- none and their Bonk Intern (Lane_<n>/Intern) ducks when the stick lands. The server decides the hit and the money.

local SWING = TycoonConfig.Swing
-- The Shiba's own arm does the swing (the stick is the one in its paw); only a model without an arm gets the extra stick below.
local SHOOTERS = Gameplay.Shooters
local THROW = SHOOTERS.Throw
local STICK_LENGTH = 5
local STICK_THICKNESS = 0.55
local STICK_COLOR = Color3.fromRGB(150, 100, 60)
local REST_ANGLE = math.rad(-20)
local WINDUP_ANGLE = math.rad(115)
local STRIKE_ANGLE = math.rad(-35)
-- The swing always takes the same time, however short the Shiba's cooldown is: a Shiba that is ready again while the arm is
-- still moving starts its next swing when the arm is back (the money does not wait for the animation). Wind-up plus strike
-- add up to about Swing.HitDelay, the moment the server checks the hit.
local WINDUP_SECONDS = 0.3
local STRIKE_SECONDS = 0.2
local RECOVER_SECONDS = 0.45
-- The stick in the paw is tilted this far further forward while the arm is raised and chopping (the arm's own pose leaves it
-- pointing up and back); it eases in during the wind-up and out in the recovery.
local STICK_TILT = math.rad(40)
local ZONE_COLOR = Color3.fromRGB(255, 70, 60)
local ZONE_WINDUP_TRANSPARENCY = 0.93
local ZONE_STRIKE_TRANSPARENCY = 0.8
-- Bonk Intern: dips this deep (studs) in DUCK_DOWN seconds and rises again in DUCK_UP seconds; only when closer than
-- DUCK_VISIBLE_DISTANCE to the camera.
local DUCK_DEPTH = 1.2
local DUCK_DOWN = 0.07
local DUCK_UP = 0.13
local DUCK_VISIBLE_DISTANCE = 140
-- The fling of a bonked owner is small: speed is clamped, the humanoid stays under control (no PlatformStand).
local MAX_LAUNCH_SPEED = 40

local swinging: { [number]: boolean } = {}
local ducking: { [Model]: boolean } = {}
local internHome: { [Model]: CFrame } = {}

-- The Intern ducks and pops back up like a bonk on the head (local animation of the anchored model).
local function duckIntern(lane: Instance)
	local intern = lane:FindFirstChild("Intern")
	if not intern or not intern:IsA("Model") or ducking[intern] or intern:GetAttribute("Spawning") then
		return
	end
	local camera = Workspace.CurrentCamera
	local ok, pivot = pcall(function()
		return intern:GetPivot()
	end)
	if not ok then
		return
	end
	local home = internHome[intern]
	if not home then
		home = pivot :: CFrame
		internHome[intern] = home
	end
	if camera and (camera.CFrame.Position - home.Position).Magnitude > DUCK_VISIBLE_DISTANCE then
		return
	end
	ducking[intern] = true
	-- Local marker: InternChatController flinches the R15 rig and may answer with a line.
	intern:SetAttribute("BonkedAt", os.clock())
	task.spawn(function()
		local startedAt = os.clock()
		local total = DUCK_DOWN + DUCK_UP
		while intern.Parent do
			local elapsed = os.clock() - startedAt
			if elapsed >= total then
				break
			end
			local depth: number
			if elapsed < DUCK_DOWN then
				depth = TweenService:GetValue(elapsed / DUCK_DOWN, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
			else
				depth = 1
					- TweenService:GetValue(
						(elapsed - DUCK_DOWN) / DUCK_UP,
						Enum.EasingStyle.Back,
						Enum.EasingDirection.Out
					)
			end
			intern:PivotTo((home :: CFrame) - Vector3.new(0, DUCK_DEPTH * depth, 0))
			RunService.RenderStepped:Wait()
		end
		if intern.Parent then
			intern:PivotTo(home :: CFrame)
		end
		ducking[intern] = nil
	end)
end

-- ThrowArm and what is in the paw (the model's Stick) turn around the Shoulder marker like in Controllers/ShibaController
-- (positive angles raise the paw forward and up, 180 = straight overhead). Nil if the model has no arm or no Shoulder.
type ArmRig = { Shoulder: Vector3, Parts: { [BasePart]: CFrame }, Paw: { [BasePart]: boolean }, Grip: Vector3? }

local function armRig(model: Model): ArmRig?
	local shoulder: BasePart? = nil
	local hasArm = false
	local parts: { [BasePart]: CFrame } = {}
	local paw: { [BasePart]: boolean } = {}
	local lowest: number? = nil
	local sumX, sumZ, count = 0, 0, 0
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			local name = descendant.Name
			if name == THROW.ShoulderName then
				shoulder = descendant
			elseif name == THROW.ThrowArmName then
				hasArm = true
				parts[descendant] = descendant.CFrame
			else
				local stick = descendant:FindFirstAncestor(SHOOTERS.HandStickName)
				if name == SHOOTERS.HandStickName or (stick ~= nil and stick:IsDescendantOf(model)) then
					parts[descendant] = descendant.CFrame
					paw[descendant] = true
					-- The stick turns around its lower end (where it is held): lowest point and the middle of its parts.
					local half = descendant.Size / 2
					local frame = descendant.CFrame
					local reach = math.abs(frame.UpVector.Y) * half.Y
						+ math.abs(frame.RightVector.Y) * half.X
						+ math.abs(frame.LookVector.Y) * half.Z
					local bottom = descendant.Position.Y - reach
					lowest = if lowest then math.min(lowest, bottom) else bottom
					sumX += descendant.Position.X
					sumZ += descendant.Position.Z
					count += 1
				end
			end
		end
	end
	if not shoulder or not hasArm then
		return nil
	end
	local grip = if lowest and count > 0 then Vector3.new(sumX / count, lowest, sumZ / count) else nil
	return { Shoulder = shoulder.Position, Parts = parts, Paw = paw, Grip = grip }
end

-- `tilt` (radians, 0 = none) turns the stick forward around its lower end first, then the arm swings everything.
local function poseArm(rig: ArmRig, axis: Vector3, angle: number, tilt: number)
	local turn = CFrame.new(rig.Shoulder) * CFrame.fromAxisAngle(axis, angle) * CFrame.new(-rig.Shoulder)
	local grip = rig.Grip
	local tiltTurn = if grip and tilt ~= 0
		then CFrame.new(grip) * CFrame.fromAxisAngle(axis, -tilt) * CFrame.new(-grip)
		else CFrame.identity
	for part, rest in rig.Parts do
		if part.Parent then
			part.CFrame = turn * (if rig.Paw[part] then tiltTurn * rest else rest)
		end
	end
end

local function restoreArm(rig: ArmRig)
	for part, rest in rig.Parts do
		if part.Parent then
			part.CFrame = rest
		end
	end
end

local function playSwing(slot: number, automated: boolean)
	if swinging[slot] then
		return
	end
	local folder = findTycoonFolder()
	local lane = if folder then folder:FindFirstChild(`Lane_{slot}`) else nil
	local shiba = if lane then lane:FindFirstChild("Shiba") else nil
	local belt = if folder then folder:FindFirstChild(`Belt_{slot}`) else nil
	if not lane or not shiba or not shiba:IsA("Model") or not belt or not belt:IsA("BasePart") then
		return
	end
	if shiba:GetAttribute("Spawning") then
		-- Still popping in (Controllers/SpawnController): its parts are being scaled.
		return
	end
	local look = belt.CFrame.LookVector
	local flatLook = Vector3.new(look.X, 0, look.Z)
	if flatLook.Magnitude < 0.01 then
		return
	end
	local forward = flatLook.Unit
	local up = Vector3.yAxis
	local right = forward:Cross(up)
	local box, size = shiba:GetBoundingBox()
	local handle = box.Position + up * (size.Y * 0.1) + right * (size.X * 0.45)
	local floor = box.Position - up * (size.Y / 2 - 0.2)

	local windup = WINDUP_SECONDS
	local strikeSeconds = STRIKE_SECONDS
	local recover = RECOVER_SECONDS

	swinging[slot] = true
	local parent = getWorldFolder()
	local rig = armRig(shiba)
	local restAngle, windupAngle, strikeAngle = REST_ANGLE, WINDUP_ANGLE, STRIKE_ANGLE
	local stick: Part? = nil
	if rig then
		restAngle, windupAngle, strikeAngle = 0, math.rad(THROW.WindupDegrees), math.rad(THROW.ReleaseDegrees)
	else
		local created = Instance.new("Part")
		created.Name = "BonkStick"
		created.Size = Vector3.new(STICK_THICKNESS, STICK_THICKNESS, STICK_LENGTH)
		created.Color = STICK_COLOR
		created.Material = Enum.Material.Wood
		created.Anchored = true
		created.CanCollide = false
		created.CanQuery = false
		created.CanTouch = false
		created.CastShadow = false
		created.Parent = parent
		stick = created
	end
	local zone: Part? = nil
	if not automated then
		local created = Instance.new("Part")
		created.Name = "BonkZone"
		created.Size = Vector3.new(2 * SWING.HitRange * math.sin(math.rad(SWING.HitHalfAngle)), 0.15, SWING.HitRange)
		created.CFrame = CFrame.lookAt(floor + forward * (SWING.HitRange / 2), floor + forward * SWING.HitRange)
		created.Color = ZONE_COLOR
		created.Material = Enum.Material.SmoothPlastic
		created.Anchored = true
		created.CanCollide = false
		created.CanQuery = false
		created.CanTouch = false
		created.CastShadow = false
		created.Transparency = 1
		created.Parent = parent
		zone = created
	end

	task.spawn(function()
		local start = os.clock()
		local strikeEnd = windup + strikeSeconds
		local total = strikeEnd + recover
		local landed = false
		while (stick == nil or stick.Parent) and (rig == nil or shiba.Parent ~= nil) and (zone == nil or zone.Parent) do
			local elapsed = os.clock() - start
			if elapsed >= total then
				break
			end
			local angle: number
			local zoneTransparency: number
			local tiltFactor = 1
			if elapsed < windup then
				local alpha = TweenService:GetValue(elapsed / windup, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
				angle = restAngle + (windupAngle - restAngle) * alpha
				tiltFactor = alpha
				zoneTransparency = ZONE_WINDUP_TRANSPARENCY
			elseif elapsed < strikeEnd then
				local alpha = TweenService:GetValue(
					(elapsed - windup) / strikeSeconds,
					Enum.EasingStyle.Quad,
					Enum.EasingDirection.In
				)
				angle = windupAngle + (strikeAngle - windupAngle) * alpha
				zoneTransparency = ZONE_STRIKE_TRANSPARENCY
			else
				if not landed then
					landed = true
					duckIntern(lane)
				end
				local alpha = (elapsed - strikeEnd) / recover
				angle = strikeAngle + (restAngle - strikeAngle) * alpha
				tiltFactor = 1 - alpha
				zoneTransparency = ZONE_STRIKE_TRANSPARENCY + (1 - ZONE_STRIKE_TRANSPARENCY) * alpha
			end
			if stick then
				local direction = forward * math.cos(angle) + up * math.sin(angle)
				stick.CFrame = CFrame.lookAt(handle + direction * (STICK_LENGTH / 2), handle + direction * STICK_LENGTH)
			elseif rig then
				poseArm(rig, right, angle, STICK_TILT * tiltFactor)
			end
			if zone then
				zone.Transparency = zoneTransparency
			end
			RunService.RenderStepped:Wait()
		end
		if stick then
			stick:Destroy()
		end
		if rig then
			restoreArm(rig)
		end
		if zone then
			zone:Destroy()
		end
		swinging[slot] = nil
	end)
end

local function onShibaSwung(slot: unknown, _serverTime: unknown, automated: unknown)
	if not active or typeof(slot) ~= "number" then
		return
	end
	playSwing(math.floor(slot), automated == true)
end

-- The owner stood in a swing's hit zone: a small fling of the own character (the bonus was already paid by the server).
local function onPlayerBonked(_slot: unknown, launch: unknown)
	if not active or typeof(launch) ~= "Vector3" then
		return
	end
	local speed = launch.Magnitude
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if speed ~= speed or speed == math.huge or not root or not root:IsA("BasePart") or not humanoid then
		return
	end
	if speed > MAX_LAUNCH_SPEED then
		launch = launch.Unit * MAX_LAUNCH_SPEED
	end
	humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
	root.AssemblyLinearVelocity = launch
end

function TycoonController.Init()
	-- Nothing to set up before Start: everything waits for state.Tycoon.Enabled.
end

function TycoonController.Start()
	if started then
		return
	end
	started = true
	State.Start()
	State.Changed:Connect(onStateChanged)

	ProximityPromptService.PromptShown:Connect(function(prompt: ProximityPrompt)
		if isForeignTycoonPrompt(prompt) then
			prompt.Enabled = false
		end
	end)

	Net.Get(Net.TycoonPayout).OnClientEvent:Connect(onPayout)
	Net.Get(Net.ShibaSwung).OnClientEvent:Connect(onShibaSwung)
	Net.Get(Net.PlayerBonked).OnClientEvent:Connect(onPlayerBonked)
	Net.Get(Net.CrateSpawned).OnClientEvent:Connect(onCrateSpawned)
	Net.Get(Net.HatchResults).OnClientEvent:Connect(onHatchResults)

	UserInputService.InputBegan:Connect(function(input: InputObject, processed: boolean)
		if processed or input.KeyCode ~= Enum.KeyCode.B then
			return
		end
		TycoonController.OpenCollection()
	end)

	-- The state may have arrived before this controller started.
	onStateChanged()
end

return TycoonController
