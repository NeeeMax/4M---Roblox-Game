--!strict
-- Jump and run in the hub centre (Config/Obby, docs/GAME_DESIGN.md → Obby): builds a spiral tower of platforms with
-- the Shiba statue on top, times each player's climb and pays a reward at most every RewardCooldown seconds.
-- Start, progress and finish are detected on the server from the character's position (10 times a second):
-- stepping off the start pad starts a run (ObbyStarted), reaching the top after MinTime seconds with enough
-- platforms passed (invisible zones above every platform) finishes it (ObbyFinished). No checkpoints: landing back on
-- the plaza after climbing drops the run (start over from the START pad). The FASTEST CLIMBERS board next to the start
-- shows the top 10 times of all servers (OrderedDataStore; this server's players when DataStores are unavailable).

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Net = require(ReplicatedStorage.Shared.Net)
local Obby = require(ReplicatedStorage.Shared.Config.Obby)
local World = require(ReplicatedStorage.Shared.Config.World)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local PropService = require(script.Parent.PropService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)
local Signs = require(script.Parent.Parent.World.Signs)

local HUB = World.Hub
local COURSE = Obby.Course
local BOARD = Obby.Board
local THICKNESS = COURSE.Thickness
local POLL_INTERVAL = 0.1
-- How high above a pad's top the character's root may be and still count as "on it" (root sits ~3 studs up).
local ZONE_HEIGHT = 8
-- Extra studs around a platform's footprint that still count as passing it.
local STAGE_MARGIN = 0.5

local TOWER_COLORS = { Color3.fromRGB(95, 215, 60), Color3.fromRGB(255, 210, 40) }
local START_COLOR = Color3.fromRGB(95, 230, 60)
local FINISH_COLOR = Color3.fromRGB(255, 200, 40)
local BOARD_COLOR = Color3.fromRGB(255, 150, 40)

type Zone = { Top: Vector3, Radius: number }

-- Invisible progress zone above one platform; follows the platform when it moves.
type StageZone = {
	Part: Part,
	Round: boolean,
	-- Half the footprint across (X) and along the path (Z); a pad's radius in both.
	HalfWidth: number,
	HalfLength: number,
}

type Mover = {
	Part: Part,
	Base: CFrame,
	Axis: Vector3,
	Amplitude: number,
	Speed: number,
}

type Run = {
	StartedAt: number,
	-- Platforms (index in Course.Stages) passed since the start.
	Passed: { [number]: boolean },
	PassedCount: number,
	-- Stood on a floor above Obby.FallHeight: landing below it again drops the run.
	Climbed: boolean,
}

type Row = { Name: string, Value: number }

local startZone: Zone
local finishZone: Zone
local stageZones: { StageZone } = {}
local movers: { Mover } = {}

local runs: { [Player]: Run } = {}
local onStartPad: { [Player]: boolean } = {}

local store: OrderedDataStore? = nil
-- UserId → best time in tenths of a second, still to be written to the OrderedDataStore.
local pendingTimes: { [number]: number } = {}
local nameCache: { [number]: string } = {}
local rowLabels: { TextLabel } = {}
local boardFooter: TextLabel? = nil

local startedRemote = Net.Get(Net.ObbyStarted)
local finishedRemote = Net.Get(Net.ObbyFinished)

local ObbyService = {}

-- Unit vector from the hub centre toward `degrees` (clockwise from north, like HubService's stations).
local function direction(degrees: number): Vector3
	local radians = math.rad(degrees)
	return Vector3.new(math.sin(radians), 0, -math.cos(radians))
end

local function newPart(name: string, size: Vector3, cframe: CFrame, color: Color3, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

-- An upright round pad whose top is at `top`.
local function pad(name: string, radius: number, top: Vector3, color: Color3, parent: Instance): Part
	local part = newPart(
		name,
		Vector3.new(THICKNESS, radius * 2, radius * 2),
		CFrame.new(top - Vector3.new(0, THICKNESS / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		parent
	)
	part.Shape = Enum.PartType.Cylinder
	return part
end

-- A coloured trim ring just under a round pad's edge (plastic, not Neon: the hub centre glowed too much).
local function rim(radius: number, top: Vector3, color: Color3, parent: Instance)
	local ring = newPart(
		"Rim",
		Vector3.new(THICKNESS * 0.6, radius * 2 + 1, radius * 2 + 1),
		CFrame.new(top - Vector3.new(0, THICKNESS * 0.7, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		parent
	)
	ring.Shape = Enum.PartType.Cylinder
end

-- A sign board with a coloured frame; `cframe` faces the readers (text on the front, mirrored on the back).
local function signBoard(name: string, size: Vector2, cframe: CFrame, text: string, color: Color3, parent: Instance)
	local board = newPart(name, Vector3.new(size.X, size.Y, 0.5), cframe, Color3.fromRGB(25, 22, 36), parent)
	newPart(`{name}Frame`, Vector3.new(size.X + 0.8, size.Y + 0.8, 0.3), cframe * CFrame.new(0, 0, 0.3), color, parent)
	local label = Signs.Text(board, Enum.NormalId.Front, text, color)
	Signs.Mirror(board, label)
	return board
end

local function statueBuilder(model: Model, _height: number)
	PropService.Part(
		model,
		Enum.PartType.Cylinder,
		Vector3.new(3, 12, 12),
		CFrame.new(0, 1.5, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(80, 78, 95),
		Enum.Material.Slate
	)
	PropService.Part(
		model,
		Enum.PartType.Ball,
		Vector3.new(7, 8, 7),
		CFrame.new(0, 7, 0),
		Color3.fromRGB(255, 170, 60),
		Enum.Material.SmoothPlastic
	)
	PropService.Part(
		model,
		Enum.PartType.Ball,
		Vector3.one * 5.5,
		CFrame.new(0, 12.5, -1),
		Color3.fromRGB(255, 170, 60),
		Enum.Material.SmoothPlastic
	)
	for _, x in { -1.6, 1.6 } do
		PropService.Part(
			model,
			Enum.PartType.Block,
			Vector3.new(1.3, 2.2, 0.6),
			CFrame.new(x, 15.4, -1) * CFrame.Angles(0, 0, math.rad(x * 8)),
			Color3.fromRGB(230, 140, 40),
			Enum.Material.SmoothPlastic
		)
	end
	PropService.Part(
		model,
		Enum.PartType.Cylinder,
		Vector3.new(9, 0.8, 0.8),
		CFrame.new(3.5, 12, 0) * CFrame.Angles(0, 0, math.rad(60)),
		Color3.fromRGB(150, 100, 60),
		Enum.Material.Wood
	)
end

-- The tower in the middle: stacked green/yellow rings (Prop_ObbyTower).
local function towerBuilder(model: Model, height: number)
	local segments = math.max(1, math.round(height / 4))
	local segment = height / segments
	for index = 1, segments do
		PropService.Part(
			model,
			Enum.PartType.Cylinder,
			Vector3.new(segment, COURSE.TowerRadius * 2, COURSE.TowerRadius * 2),
			CFrame.new(0, (index - 0.5) * segment, 0) * CFrame.Angles(0, 0, math.rad(90)),
			TOWER_COLORS[index % 2 + 1],
			Enum.Material.SmoothPlastic
		)
	end
end

local function buildStage(index: number, stage: Obby.Stage, parent: Instance)
	local degrees = COURSE.StartAngle - stage.Angle
	local outward = direction(degrees)
	local radians = math.rad(degrees)
	-- Direction the path continues in (toward larger `Angle`).
	local along = -Vector3.new(math.cos(radians), 0, math.sin(radians))
	local top = HUB.Center + outward * (stage.Radius or COURSE.Radius) + Vector3.new(0, stage.Height, 0)

	local part: Part
	if stage.Shape == "Pad" then
		part = pad(`Stage{index}`, stage.Length / 2, top, stage.Color, parent)
	else
		local center = top - Vector3.new(0, THICKNESS / 2, 0)
		part = newPart(
			`Stage{index}`,
			Vector3.new(stage.Width, THICKNESS, stage.Length),
			CFrame.lookAt(center, center + along),
			stage.Color,
			parent
		)
	end
	part.Material = Enum.Material.Plastic
	part.TopSurface = Enum.SurfaceType.Studs

	stageZones[index] = {
		Part = part,
		Round = stage.Shape == "Pad",
		HalfWidth = (if stage.Shape == "Pad" then stage.Length else stage.Width) / 2,
		HalfLength = stage.Length / 2,
	}

	local move = stage.Move
	if move then
		local axis = if move.Axis == "Radial" then outward elseif move.Axis == "Tangent" then along else Vector3.yAxis
		table.insert(movers, {
			Part = part,
			Base = part.CFrame,
			Axis = axis,
			Amplitude = move.Distance / 2,
			Speed = 2 * math.pi / move.Period,
		})
	end
end

local function buildBoard(parent: Instance)
	-- Left of the obby entrance, facing the spawn point (the how-to board of HubService stands on the right).
	local center = HUB.Center + Vector3.new(-8, 6, 19)
	local facing = CFrame.lookAt(center, center + Vector3.new(0, 0, 20))
	local board = newPart("TimesBoard", Vector3.new(10, 8, 0.5), facing, Color3.fromRGB(30, 28, 42), parent)
	local frame =
		newPart("TimesBoardFrame", Vector3.new(10.8, 8.8, 0.3), facing * CFrame.new(0, 0, 0.3), BOARD_COLOR, parent)
	for _, x in { -4.2, 4.2 } do
		newPart(
			"Leg",
			Vector3.new(0.6, 6, 0.6),
			CFrame.new(center + Vector3.new(x, -4.5, 0.4)),
			Color3.fromRGB(60, 55, 70),
			parent
		)
	end
	Signs.Billboard(frame, "FASTEST CLIMBERS", BOARD_COLOR, Vector2.new(300, 40), 5.6, 120)

	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 40
	gui.LightInfluence = 0
	gui.Parent = board
	local list = Instance.new("Frame")
	list.Size = UDim2.fromScale(0.9, 0.84)
	list.Position = UDim2.fromScale(0.05, 0.04)
	list.BackgroundTransparency = 1
	list.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0.01, 0)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	for rank = 1, BOARD.Size do
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1 / BOARD.Size - 0.01)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.FredokaOne
		label.TextScaled = true
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextColor3 = if rank == 1
			then Color3.fromRGB(255, 210, 60)
			elseif rank == 2 then Color3.fromRGB(210, 210, 225)
			elseif rank == 3 then Color3.fromRGB(230, 150, 80)
			else Color3.fromRGB(235, 235, 245)
		label.Text = `{rank}.  —`
		label.LayoutOrder = rank
		label.Parent = list
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = 2
		stroke.Color = Color3.fromRGB(15, 12, 25)
		stroke.Parent = label
		table.insert(rowLabels, label)
	end
	local footer = Instance.new("TextLabel")
	footer.Size = UDim2.fromScale(0.9, 0.07)
	footer.Position = UDim2.fromScale(0.05, 0.9)
	footer.BackgroundTransparency = 1
	footer.Font = Enum.Font.GothamBold
	footer.TextScaled = true
	footer.TextColor3 = Color3.fromRGB(160, 160, 180)
	footer.Text = ""
	footer.Parent = gui
	boardFooter = footer
end

local function build()
	local folder = Instance.new("Folder")
	folder.Name = "Obby"
	local startDirection = direction(COURSE.StartAngle)

	-- Start pad on the plaza, facing the spawn point, with the START sign on the tower behind it.
	local startTop = HUB.Center + startDirection * COURSE.StartPad.Radius + Vector3.new(0, COURSE.StartPad.Height, 0)
	local startPad = pad("StartPad", COURSE.StartPad.PadRadius, startTop, START_COLOR, folder)
	startPad.Material = Enum.Material.Plastic
	startPad.TopSurface = Enum.SurfaceType.Studs
	rim(COURSE.StartPad.PadRadius, startTop, Color3.fromRGB(255, 255, 255), folder)
	startZone = { Top = startTop, Radius = COURSE.StartPad.PadRadius + 0.5 }
	Signs.Billboard(startPad, "Climb to the top!", Color3.fromRGB(245, 245, 255), Vector2.new(240, 34), 4.5, 90)
	local signPosition = HUB.Center + startDirection * (COURSE.TowerRadius + 0.6) + Vector3.new(0, 7, 0)
	signBoard(
		"StartSign",
		Vector2.new(8, 3.2),
		CFrame.lookAt(signPosition, signPosition + startDirection),
		"START",
		START_COLOR,
		folder
	)

	-- Tower from the plaza up to the finish pad.
	local plazaTop = 0.4
	PropService.Place(
		"Prop_ObbyTower",
		CFrame.new(HUB.Center + Vector3.new(0, plazaTop, 0)),
		COURSE.FinishHeight - THICKNESS - plazaTop,
		towerBuilder,
		folder
	)

	for index, stage in COURSE.Stages do
		buildStage(index, stage, folder)
	end

	-- Finish pad on top of the tower with the Shiba statue (facing the spawn point) and a FINISH banner where the
	-- last platform arrives.
	local finishTop = HUB.Center + Vector3.new(0, COURSE.FinishHeight, 0)
	local finishPad = pad("FinishPad", COURSE.FinishRadius, finishTop, FINISH_COLOR, folder)
	finishPad.Material = Enum.Material.Plastic
	finishPad.TopSurface = Enum.SurfaceType.Studs
	rim(COURSE.FinishRadius, finishTop, Color3.fromRGB(255, 120, 40), folder)
	finishZone = { Top = finishTop, Radius = COURSE.FinishRadius + 0.5 }

	local statue = PropService.Place(
		"Prop_ShibaStatue",
		CFrame.lookAt(finishTop, finishTop + startDirection),
		16,
		statueBuilder,
		folder
	)
	Signs.Billboard(
		statue.PrimaryPart :: BasePart,
		"GET BONKED",
		Color3.fromRGB(255, 190, 40),
		Vector2.new(520, 110),
		22,
		700
	)

	local stages = COURSE.Stages
	local last = stages[#stages]
	local arrival = direction(COURSE.StartAngle - last.Angle)
	local bannerBase = finishTop + arrival * (COURSE.FinishRadius - 1.5)
	local bannerFacing = CFrame.lookAt(bannerBase, bannerBase + arrival)
	signBoard("FinishSign", Vector2.new(9, 2.6), bannerFacing * CFrame.new(0, 8, 0), "FINISH", FINISH_COLOR, folder)
	for _, x in { -4.8, 4.8 } do
		newPart(
			"Post",
			Vector3.new(0.6, 9.4, 0.6),
			bannerFacing * CFrame.new(x, 4.7, 0),
			Color3.fromRGB(60, 55, 70),
			folder
		)
	end

	buildBoard(folder)
	folder.Parent = Workspace
end

local function inZone(position: Vector3, zone: Zone): boolean
	local offset = position - zone.Top
	if offset.Y < -0.5 or offset.Y > ZONE_HEIGHT then
		return false
	end
	return Vector3.new(offset.X, 0, offset.Z).Magnitude <= zone.Radius
end

local function inStage(position: Vector3, zone: StageZone): boolean
	local part = zone.Part
	-- Platforms are centred THICKNESS / 2 below their top surface.
	local offset = position - (part.Position + Vector3.new(0, THICKNESS / 2, 0))
	if offset.Y < -0.5 or offset.Y > ZONE_HEIGHT then
		return false
	end
	local flat = Vector3.new(offset.X, 0, offset.Z)
	if zone.Round then
		return flat.Magnitude <= zone.HalfLength + STAGE_MARGIN
	end
	-- Blocks only turn around the vertical axis: local X is across the path, local Z along it.
	local localOffset = part.CFrame:VectorToObjectSpace(flat)
	return math.abs(localOffset.X) <= zone.HalfWidth + STAGE_MARGIN
		and math.abs(localOffset.Z) <= zone.HalfLength + STAGE_MARGIN
end

local floorParams = RaycastParams.new()
floorParams.FilterType = Enum.RaycastFilterType.Exclude
floorParams.RespectCanCollide = true

-- Height above the hub ground of the floor the character stands on, nil while in the air.
local function floorHeight(character: Model, root: BasePart, humanoid: Humanoid): number?
	floorParams.FilterDescendantsInstances = { character }
	-- Root to feet: HipHeight + half the root (R15); R6 has HipHeight 0 and ~3 studs of legs and root.
	local reach = math.max(humanoid.HipHeight + root.Size.Y / 2, 3) + 1.2
	local result = Workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), floorParams)
	return if result then result.Position.Y - HUB.Center.Y else nil
end

local function formatTime(seconds: number): string
	return string.format("%.1f s", seconds)
end

local function finish(player: Player, run: Run)
	runs[player] = nil
	local elapsed = os.clock() - run.StartedAt
	local needed = math.ceil(#stageZones * Obby.MinStageShare)
	if elapsed < Obby.MinTime or run.PassedCount < needed then
		NotifyService.Send(player, "That run didn't count: climb all the way up from the START pad!", "Bad")
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local time = math.floor(elapsed * 10 + 0.5) / 10
	local obby = state.Obby
	if obby.BestTime <= 0 or time < obby.BestTime then
		obby.BestTime = time
		pendingTimes[player.UserId] = math.floor(time * 10 + 0.5)
	end

	local reward = 0
	local now = os.time()
	if now - obby.LastRewardAt >= Obby.RewardCooldown then
		reward = RewardService.Hits(player, Obby.RewardHits)
		EconomyService.AddPoints(player, reward)
		BoostService.Give(player, "Points", Obby.BoostSeconds)
		obby.LastRewardAt = now
	end
	QuestService.Record(player, "Obby", 1)
	DataService.Replicate(player)
	finishedRemote:FireClient(player, time, reward, obby.BestTime, obby.LastRewardAt + Obby.RewardCooldown)
end

local function updatePlayer(player: Player)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not character or not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		runs[player] = nil
		onStartPad[player] = nil
		return
	end
	local position = root.Position

	if inZone(position, startZone) then
		-- The run starts when the player steps off the pad.
		onStartPad[player] = true
		runs[player] = nil
		return
	end
	if onStartPad[player] then
		onStartPad[player] = nil
		runs[player] = { StartedAt = os.clock(), Passed = {}, PassedCount = 0, Climbed = false }
		startedRemote:FireClient(player)
		return
	end

	local run = runs[player]
	if not run then
		return
	end
	local fromCenter = position - HUB.Center
	if
		os.clock() - run.StartedAt > Obby.MaxRunTime
		or Vector3.new(fromCenter.X, 0, fromCenter.Z).Magnitude > Obby.LeaveRadius
	then
		runs[player] = nil
		return
	end
	-- No checkpoints: back on the plaza after climbing means starting over.
	local floor = floorHeight(character, root, humanoid)
	if floor then
		if floor > Obby.FallHeight then
			run.Climbed = true
		elseif run.Climbed then
			runs[player] = nil
			NotifyService.Send(player, "You fell! Start again from the START pad.", "Info")
			return
		end
	end
	for index, zone in stageZones do
		if not run.Passed[index] and inStage(position, zone) then
			run.Passed[index] = true
			run.PassedCount += 1
		end
	end
	if inZone(position, finishZone) then
		finish(player, run)
	end
end

local function updateMovers()
	local now = os.clock()
	for _, mover in movers do
		local phase = now * mover.Speed
		mover.Part.CFrame = mover.Base + mover.Axis * (mover.Amplitude * math.sin(phase))
		-- Anchored parts with a velocity carry the characters standing on them.
		mover.Part.AssemblyLinearVelocity = mover.Axis * (mover.Amplitude * mover.Speed * math.cos(phase))
	end
end

local function nameOf(userId: number): string
	local cached = nameCache[userId]
	if cached then
		return cached
	end
	local ok, name = pcall(function()
		return Players:GetNameFromUserIdAsync(userId)
	end)
	local result = if ok and typeof(name) == "string" then name else `Player {userId}`
	nameCache[userId] = result
	return result
end

local function serverRows(): { Row }
	local rows: { Row } = {}
	for _, player in Players:GetPlayers() do
		local state = DataService.GetState(player)
		if state and state.Obby.BestTime > 0 then
			table.insert(rows, { Name = player.DisplayName, Value = state.Obby.BestTime })
		end
	end
	table.sort(rows, function(a, b)
		return a.Value < b.Value
	end)
	return rows
end

-- Writes new best times (keeping the smaller one), then reads the global top list. Nil if the store isn't reachable.
local function globalRows(): { Row }?
	local currentStore = store
	if not currentStore then
		return nil
	end
	-- A copy: new best times can arrive while UpdateAsync yields.
	for userId, tenths in table.clone(pendingTimes) do
		local ok = pcall(function()
			-- The stored value is an integer (tenths of a second); a better stored time is kept.
			currentStore:UpdateAsync(tostring(userId), function(old: number?): number
				if old and old > 0 and old <= tenths then
					return old
				end
				return tenths
			end)
		end)
		if ok and pendingTimes[userId] == tenths then
			pendingTimes[userId] = nil
		end
	end
	local ok, pages = pcall(function()
		return currentStore:GetSortedAsync(true, BOARD.Size, 1)
	end)
	if not ok then
		return nil
	end
	local rows: { Row } = {}
	for _, entry in (pages :: DataStorePages):GetCurrentPage() do
		local userId = tonumber(entry.key)
		if userId then
			table.insert(rows, { Name = nameOf(userId), Value = entry.value / 10 })
		end
	end
	return rows
end

local function refreshBoard()
	local footer = boardFooter
	if not footer then
		return
	end
	local rows = globalRows()
	footer.Text = if rows then "All servers · updates every minute" else "This server · updates every minute"
	local shown = rows or serverRows()
	for rank, label in rowLabels do
		local row = shown[rank]
		label.Text = if row then `{rank}.  {row.Name}  ·  {formatTime(row.Value)}` else `{rank}.  —`
	end
end

function ObbyService.Init()
	build()
	local ok, result = pcall(function()
		return DataStoreService:GetOrderedDataStore(BOARD.StoreName)
	end)
	if ok then
		store = result
	end
end

function ObbyService.Start()
	-- Best times saved before (or whose board write failed) go to the board on the next refresh.
	DataService.OnLoaded(function(player, state)
		if state.Obby.BestTime > 0 then
			pendingTimes[player.UserId] = math.floor(state.Obby.BestTime * 10 + 0.5)
		end
	end)

	local function onPlayerAdded(player: Player)
		player.CharacterAdded:Connect(function()
			runs[player] = nil
			onStartPad[player] = nil
		end)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		runs[player] = nil
		onStartPad[player] = nil
	end)

	local sincePoll = 0
	RunService.Heartbeat:Connect(function(deltaTime)
		updateMovers()
		sincePoll += deltaTime
		if sincePoll < POLL_INTERVAL then
			return
		end
		sincePoll = 0
		for _, player in Players:GetPlayers() do
			updatePlayer(player)
		end
	end)

	task.spawn(function()
		-- First fill once the players' data had time to load.
		task.wait(5)
		while true do
			refreshBoard()
			task.wait(BOARD.RefreshInterval)
		end
	end)
end

return ObbyService
