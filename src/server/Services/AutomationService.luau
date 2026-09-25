--!strict
-- Automation (docs/GAME_DESIGN.md → Automation): the Bonk Basket and the Bonk Intern catch the player's sticks for
-- a share of their value. Upgrades "Basket" and "Intern" (level 0 = none, level n uses EconomyConfig.Automation's
-- entry n); look and tuning in Config/Automation. Everything is decided and paid here; clients only draw the catch
-- (AutomationCatch → AutomationController).
--
-- * Basket: a wicker basket (PropService "Prop_Basket") at the edge of the field. When a stick's collectable window
--   ends (ProjectilePath.GetCollectEndTime, + Basket.CatchDelay for late hand reports) and nobody caught it, the
--   basket rolls Basket.CatchChance once; on success it pays Basket.Payout × the stick value.
-- * Intern: an NPC on the island (built from parts, R6 proportions). Every Intern.TickInterval it picks an unpaid
--   stick whose first landing point it can reach at its WalkSpeed before the stick stops being collectable, preferring
--   sticks far from the player (the player gets first dibs: sticks near the character are left alone), and walks
--   there. A stick passing within its radius + CatchPadding of the intern bonks it: Intern.Payout × the stick value.
--   It moves with physics movers (AlignPosition / AlignOrientation, network owner = server, nothing collides), so it
--   never falls through the island or blocks the player; if anything goes wrong it is put back at its idle spot.
-- Both only work while the owner is on their island (like the Shibas).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Automation = require(ReplicatedStorage.Shared.Config.Automation)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local IslandService = require(script.Parent.IslandService)
local ProjectileService = require(script.Parent.ProjectileService)
local PropService = require(script.Parent.PropService)
local RewardService = require(script.Parent.RewardService)
local UpgradeService = require(script.Parent.UpgradeService)
local Signs = require(script.Parent.Parent.World.Signs)

local ISLAND = Gameplay.Island
local ECONOMY = EconomyConfig.Automation
local BASKET = Automation.Basket
local INTERN = Automation.Intern
local JOINTS = INTERN.Joints

type ProjectileInfo = ProjectileService.ProjectileInfo

type Intern = {
	Level: number,
	Model: Model,
	Root: BasePart,
	Mover: AlignPosition,
	Turner: AlignOrientation,
	Target: ProjectileInfo?,
	-- os.clock() until which it stands dazed after a bonk.
	StunnedUntil: number,
}

type Helpers = {
	Island: IslandService.Island,
	BasketLevel: number,
	Basket: Model?,
	Intern: Intern?,
}

local automationCatch = Net.Get(Net.AutomationCatch)
local helpers: { [Player]: Helpers } = {}
-- Projectiles the basket already rolled for. Weak keys: forgotten together with the projectile.
local rolled: { [ProjectileInfo]: boolean } = setmetatable({} :: any, { __mode = "k" })
local random = Random.new()

local AutomationService = {}

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

local function flat(vector: Vector3): Vector3
	return Vector3.new(vector.X, 0, vector.Z)
end

-- The owner's character root while they are alive and on their island (else nil: automation waits).
local function ownerRootAtHome(player: Player, island: IslandService.Island): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return nil
	end
	if flat(root.Position - island.Center).Magnitude > ISLAND.ActiveDistance then
		return nil
	end
	return root
end

-- Pays `share` of the stick's value (RewardService.GetStickValue: tier, rebirth, golden, passes, boosts, events).
local function pay(player: Player, info: ProjectileInfo, source: Types.AutomationSource, share: number): number
	local plan = info.Plan
	local value = RewardService.GetStickValue(player, plan.Def.BaseReward, plan.Golden, plan.Mega)
	local reward = math.max(1, math.floor(value * share))
	-- Tell the client before the Paid attribute changes, so AutomationController takes the drawn stick over for its
	-- catch effect before other controllers react to Paid (MagnetController pulls "Paid without a hand report"
	-- sticks into Auto-Catch owners).
	automationCatch:FireClient(player, source, info.Id, reward)
	ProjectileService.MarkPaid(info)
	EconomyService.AddAutomationPoints(player, reward)
	return reward
end

------------------------------------------------------------------------------------------------------------------------
-- Basket

local function basketHeight(level: number): number
	return BASKET.Height + BASKET.HeightPerLevel * (level - 1)
end

local function buildBasket(helper: Helpers, level: number)
	local old = helper.Basket
	if old then
		old:Destroy()
		helper.Basket = nil
	end
	helper.BasketLevel = level
	if level <= 0 then
		return
	end
	local island = helper.Island
	local height = basketHeight(level)
	local width = height * BASKET.WidthRatio
	local angle = island.HubAngle + math.rad(BASKET.AngleDegrees)
	local distance = ISLAND.FieldRadius + ISLAND.BorderWidth + BASKET.Gap + width / 2
	local position = island.Center + direction(angle) * distance
	-- Facing the field, so its handle spans across the view from the middle.
	local facing = CFrame.lookAt(position, Vector3.new(island.Center.X, position.Y, island.Center.Z))
	local rimColor = BASKET.RimColors[math.min(level, #BASKET.RimColors)]
	helper.Basket = PropService.Place(
		Automation.BasketName,
		facing,
		height,
		PropService.BasketBuilder(rimColor, BASKET.WidthRatio, BASKET.BodyShare),
		island.Model
	)
end

-- Sticks whose collectable window ended (+ CatchDelay) unpaid get one roll each.
local function checkBasket(player: Player, helper: Helpers, now: number)
	local level = helper.BasketLevel
	if level <= 0 then
		return
	end
	local home = ownerRootAtHome(player, helper.Island) ~= nil
	local chance = ECONOMY.Basket.CatchChance[level]
	local share = ECONOMY.Basket.Payout[level]
	for _, info in ProjectileService.GetOwned(player) do
		if info.Paid or rolled[info] then
			continue
		end
		local age = now - info.LaunchedAt
		if age < ProjectilePath.GetCollectEndTime(info.Plan.Path) + BASKET.CatchDelay then
			continue
		end
		rolled[info] = true
		if home and random:NextNumber() < chance then
			pay(player, info, "Basket", share)
		end
	end
end

------------------------------------------------------------------------------------------------------------------------
-- Intern: the model

local function bodyPart(model: Model, name: string, size: Vector3, cframe: CFrame, color: Color3): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Anchored = false
	-- Never blocks anyone; only the root carries mass (the movers hold it up).
	part.CanCollide = false
	part.CanTouch = false
	part.CanQuery = false
	part.Massless = true
	part.Parent = model
	return part
end

local function motor(name: string, part0: BasePart, part1: BasePart, c0: CFrame, c1: CFrame)
	local joint = Instance.new("Motor6D")
	joint.Name = name
	joint.Part0 = part0
	joint.Part1 = part1
	joint.C0 = c0
	joint.C1 = c1
	joint.Parent = part0
end

-- Accessories keep their built offset to `to`.
local function attach(part: BasePart, to: BasePart)
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = to
	weld.Part1 = part
	weld.Parent = part
end

-- Builds the intern for `level` standing at `rootFrame` (its root's CFrame). Parts are laid out around the origin
-- first (feet at y = 0, facing −Z), then the model is moved into place.
local function buildInternModel(level: number, rootFrame: CFrame, parent: Instance): (Model, BasePart)
	local shirt = INTERN.ShirtColors[math.min(level, #INTERN.ShirtColors)]
	local pants = INTERN.PantsColors[math.min(level, #INTERN.PantsColors)]
	local skin = INTERN.SkinColor
	local suit = level >= INTERN.TieFromLevel
	local rootY = INTERN.RootHeight

	local model = Instance.new("Model")
	model.Name = Automation.InternName

	local root = bodyPart(model, "Root", Vector3.new(2, 2, 1), CFrame.new(0, rootY, 0), shirt)
	root.Transparency = 1
	root.Massless = false
	root.RootPriority = 127
	local torso = bodyPart(model, "Torso", Vector3.new(2, 2, 1), CFrame.new(0, rootY, 0), shirt)
	local head = bodyPart(model, "Head", Vector3.new(1.25, 1.2, 1.2), CFrame.new(0, rootY + 1.6, 0), skin)
	local face = Instance.new("Decal")
	face.Name = "Face"
	face.Texture = "rbxasset://textures/face.png"
	face.Face = Enum.NormalId.Front
	face.Parent = head
	-- Short sleeves for the interns, long ones from the manager on.
	local armColor = if suit then shirt else skin
	local leftArm = bodyPart(model, "LeftArm", Vector3.new(1, 2, 1), CFrame.new(-1.5, rootY, 0), armColor)
	local rightArm = bodyPart(model, "RightArm", Vector3.new(1, 2, 1), CFrame.new(1.5, rootY, 0), armColor)
	local leftLeg = bodyPart(model, "LeftLeg", Vector3.new(1, 2, 1), CFrame.new(-0.5, rootY - 2, 0), pants)
	local rightLeg = bodyPart(model, "RightLeg", Vector3.new(1, 2, 1), CFrame.new(0.5, rootY - 2, 0), pants)

	motor(JOINTS.Waist, root, torso, CFrame.identity, CFrame.identity)
	motor(JOINTS.Neck, torso, head, CFrame.new(0, 1, 0), CFrame.new(0, -0.6, 0))
	motor(JOINTS.LeftShoulder, torso, leftArm, CFrame.new(-1.5, 0.5, 0), CFrame.new(0, 0.5, 0))
	motor(JOINTS.RightShoulder, torso, rightArm, CFrame.new(1.5, 0.5, 0), CFrame.new(0, 0.5, 0))
	motor(JOINTS.LeftHip, torso, leftLeg, CFrame.new(-0.5, -1, 0), CFrame.new(0, 1, 0))
	motor(JOINTS.RightHip, torso, rightLeg, CFrame.new(0.5, -1, 0), CFrame.new(0, 1, 0))

	local headTop = rootY + 2.2
	if level >= INTERN.CrownFromLevel then
		local crown = bodyPart(
			model,
			"Crown",
			Vector3.new(0.4, 1.35, 1.35),
			CFrame.new(0, headTop + 0.15, 0) * CFrame.Angles(0, 0, math.rad(90)),
			INTERN.CrownColor
		)
		crown.Shape = Enum.PartType.Cylinder
		crown.Material = Enum.Material.Foil
		attach(crown, head)
		for index = 1, 5 do
			local angle = index / 5 * 2 * math.pi
			local spike = bodyPart(
				model,
				"CrownSpike",
				Vector3.new(0.25, 0.45, 0.25),
				CFrame.Angles(0, angle, 0) * CFrame.new(0, headTop + 0.55, -0.55),
				INTERN.CrownColor
			)
			spike.Material = Enum.Material.Foil
			attach(spike, head)
		end
	elseif level >= INTERN.HardHatFromLevel then
		local dome = bodyPart(
			model,
			"HardHat",
			Vector3.new(0.55, 1.4, 1.4),
			CFrame.new(0, headTop + 0.25, 0) * CFrame.Angles(0, 0, math.rad(90)),
			INTERN.HardHatColor
		)
		dome.Shape = Enum.PartType.Cylinder
		attach(dome, head)
		local brim = bodyPart(
			model,
			"HardHatBrim",
			Vector3.new(0.12, 1.9, 1.9),
			CFrame.new(0, headTop + 0.02, -0.1) * CFrame.Angles(0, 0, math.rad(90)),
			INTERN.HardHatColor
		)
		brim.Shape = Enum.PartType.Cylinder
		attach(brim, head)
	end
	if suit then
		local tieColor = if level >= INTERN.CrownFromLevel then INTERN.CeoTieColor else INTERN.TieColor
		if level >= INTERN.CrownFromLevel then
			-- The CEO wears a dark suit: a white shirt shows behind the tie.
			local collar = bodyPart(
				model,
				"Shirt",
				Vector3.new(0.8, 1, 0.08),
				CFrame.new(0, rootY + 0.5, -0.52),
				Color3.fromRGB(245, 245, 245)
			)
			attach(collar, torso)
		end
		local knot =
			bodyPart(model, "TieKnot", Vector3.new(0.4, 0.3, 0.12), CFrame.new(0, rootY + 0.85, -0.56), tieColor)
		attach(knot, torso)
		local tie = bodyPart(model, "Tie", Vector3.new(0.32, 1.2, 0.1), CFrame.new(0, rootY + 0.1, -0.56), tieColor)
		attach(tie, torso)
	end

	-- Name tag (EconomyConfig.Automation.Intern.Names).
	local names = ECONOMY.Intern.Names
	Signs.Billboard(head, names[math.min(level, #names)], INTERN.NameColor, Vector2.new(200, 30), 2.1, 90)

	model.PrimaryPart = root
	model:PivotTo(rootFrame)
	model.Parent = parent
	return model, root
end

local function idleSpot(island: IslandService.Island): Vector3
	local angle = island.HubAngle + math.rad(BASKET.AngleDegrees)
	return island.Center + direction(angle) * INTERN.IdleDistance + Vector3.new(0, INTERN.RootHeight, 0)
end

local function faceCenter(island: IslandService.Island, position: Vector3): CFrame
	local center = Vector3.new(island.Center.X, position.Y, island.Center.Z)
	if flat(center - position).Magnitude < 1e-3 then
		return CFrame.identity
	end
	return CFrame.lookAt(position, center).Rotation
end

local function removeIntern(helper: Helpers)
	local intern = helper.Intern
	if intern then
		intern.Model:Destroy()
		helper.Intern = nil
	end
end

local function buildIntern(helper: Helpers, level: number)
	local old = helper.Intern
	local island = helper.Island
	-- A new look keeps its place; a new hire starts at the idle spot.
	local frame = if old and old.Model.Parent
		then old.Root.CFrame
		else CFrame.new(idleSpot(island)) * faceCenter(island, idleSpot(island))
	removeIntern(helper)
	if level <= 0 then
		return
	end
	local model, root = buildInternModel(level, frame, island.Model)
	local attachment = Instance.new("Attachment")
	attachment.Name = "Mover"
	attachment.Parent = root
	local mover = Instance.new("AlignPosition")
	mover.Mode = Enum.PositionAlignmentMode.OneAttachment
	mover.Attachment0 = attachment
	mover.MaxForce = math.huge
	mover.MaxVelocity = ECONOMY.Intern.WalkSpeed[level]
	mover.Responsiveness = INTERN.MoveResponsiveness
	mover.Position = frame.Position
	mover.Parent = root
	local turner = Instance.new("AlignOrientation")
	turner.Mode = Enum.OrientationAlignmentMode.OneAttachment
	turner.Attachment0 = attachment
	turner.MaxTorque = math.huge
	turner.Responsiveness = INTERN.TurnResponsiveness
	turner.CFrame = frame.Rotation
	turner.Parent = root
	-- The server moves it: no client can push it around.
	root:SetNetworkOwner(nil)
	helper.Intern = {
		Level = level,
		Model = model,
		Root = root,
		Mover = mover,
		Turner = turner,
		Target = nil,
		StunnedUntil = 0,
	}
end

------------------------------------------------------------------------------------------------------------------------
-- Intern: the brain

-- Where the intern should stand for this stick: its first landing point while it is still in the air, afterwards
-- slightly ahead of where it is now. At root height.
local function goalFor(island: IslandService.Island, path: ProjectilePath.Path, age: number): Vector3
	local landing = path.Segments[2]
	local point = if landing and age < landing.StartTime
		then landing.StartPosition
		else ProjectilePath.GetState(path, age + INTERN.TickInterval)
	return Vector3.new(point.X, island.Center.Y + INTERN.RootHeight, point.Z)
end

-- Did any stick pass the intern since the last tick? Pays the first one found and returns true.
local function tryCatch(
	player: Player,
	intern: Intern,
	playerPosition: Vector3,
	owned: { ProjectileInfo },
	now: number,
	since: number
): boolean
	local rootPosition = intern.Root.Position
	for _, info in owned do
		if info.Paid then
			continue
		end
		local path = info.Plan.Path
		local toAge = math.min(now - info.LaunchedAt, ProjectilePath.GetCollectEndTime(path))
		local fromAge = math.max(since - info.LaunchedAt, 0)
		if toAge < fromAge then
			continue
		end
		local reach = info.Plan.Radius + INTERN.CatchPadding
		local age = fromAge
		while true do
			local position = ProjectilePath.GetState(path, age)
			if
				(position - rootPosition).Magnitude <= reach
				-- First dibs: never snatch a stick right next to the player.
				and flat(position - playerPosition).Magnitude > INTERN.PlayerDibsRadius
			then
				pay(player, info, "Intern", ECONOMY.Intern.Payout[intern.Level])
				return true
			end
			if age >= toAge then
				break
			end
			age = math.min(age + INTERN.CatchSampleStep, toAge)
		end
	end
	return false
end

-- The best stick to run for, and where to stand for it.
local function pickTarget(
	helper: Helpers,
	intern: Intern,
	playerPosition: Vector3,
	owned: { ProjectileInfo },
	now: number
): (ProjectileInfo?, Vector3?)
	local island = helper.Island
	local speed = ECONOMY.Intern.WalkSpeed[intern.Level]
	local rootPosition = intern.Root.Position
	local best: ProjectileInfo? = nil
	local bestGoal: Vector3? = nil
	local bestScore = -math.huge
	for _, info in owned do
		if info.Paid then
			continue
		end
		local path = info.Plan.Path
		local age = now - info.LaunchedAt
		local timeLeft = ProjectilePath.GetCollectEndTime(path) - age
		if timeLeft <= 0 then
			continue
		end
		local goal = goalFor(island, path, age)
		local fromPlayer = flat(goal - playerPosition).Magnitude
		local walk = flat(goal - rootPosition).Magnitude
		if
			flat(goal - island.Center).Magnitude > INTERN.MaxRoamRadius
			or fromPlayer < INTERN.PlayerDibsRadius
			or walk / speed > timeLeft
		then
			continue
		end
		-- Far from the player first (they get the near ones), then close to the intern.
		local score = fromPlayer - walk * 0.5 + (if info == intern.Target then INTERN.TargetStickiness else 0)
		if score > bestScore then
			best, bestGoal, bestScore = info, goal, score
		end
	end
	return best, bestGoal
end

local function moveTo(intern: Intern, goal: Vector3, faceToward: Vector3?)
	intern.Mover.Position = goal
	local root = intern.Root.Position
	local look = faceToward or goal
	if flat(look - root).Magnitude > 0.5 then
		intern.Turner.CFrame = CFrame.lookAt(root, Vector3.new(look.X, root.Y, look.Z)).Rotation
	end
end

local function tickIntern(player: Player, helper: Helpers, intern: Intern, now: number, since: number)
	local island = helper.Island
	local root = intern.Root
	local height = island.Center.Y + INTERN.RootHeight
	-- Safety net: fell through or wandered off the island somehow → back to the idle spot.
	if
		root.Position.Y < island.Center.Y - INTERN.FallBelow
		or flat(root.Position - island.Center).Magnitude > ISLAND.Radius
	then
		local spot = idleSpot(island)
		intern.Model:PivotTo(CFrame.new(spot) * faceCenter(island, spot))
		root.AssemblyLinearVelocity = Vector3.zero
		root.AssemblyAngularVelocity = Vector3.zero
		intern.Mover.Position = spot
	end
	local here = Vector3.new(root.Position.X, height, root.Position.Z)
	if now < intern.StunnedUntil then
		intern.Mover.Position = here
		return
	end
	local ownerRoot = ownerRootAtHome(player, island)
	if not ownerRoot then
		intern.Target = nil
		moveTo(intern, idleSpot(island), island.Center)
		return
	end
	local owned = ProjectileService.GetOwned(player)
	if tryCatch(player, intern, ownerRoot.Position, owned, now, since) then
		intern.Target = nil
		intern.StunnedUntil = now + INTERN.StunTime
		intern.Mover.Position = here
		return
	end
	local target, goal = pickTarget(helper, intern, ownerRoot.Position, owned, now)
	intern.Target = target
	if target and goal then
		moveTo(intern, goal)
	else
		local spot = idleSpot(island)
		-- At the idle spot it watches the field.
		moveTo(intern, spot, if flat(spot - here).Magnitude < 1 then island.Center else nil)
	end
end

-- A failing tick must not stop the loop for everyone.
local function reportError(message: unknown)
	warn(`[AutomationService] {message}`, debug.traceback())
end

------------------------------------------------------------------------------------------------------------------------

-- Builds, rebuilds or removes the basket and the intern to match the player's levels. Cheap when nothing changed
-- (it runs after every state change).
local function sync(player: Player)
	local island = IslandService.GetIsland(player)
	if not island or not DataService.GetState(player) then
		return
	end
	local existing = helpers[player]
	local helper: Helpers
	if existing and existing.Island == island then
		helper = existing
	else
		helper = { Island = island, BasketLevel = 0, Basket = nil, Intern = nil }
		helpers[player] = helper
	end
	local basketLevel = math.clamp(UpgradeService.GetLevel(player, "Basket"), 0, #ECONOMY.Basket.CatchChance)
	local basket = helper.Basket
	if basketLevel ~= helper.BasketLevel or (basketLevel > 0 and not (basket and basket.Parent)) then
		buildBasket(helper, basketLevel)
	end
	local internLevel = math.clamp(UpgradeService.GetLevel(player, "Intern"), 0, #ECONOMY.Intern.Payout)
	local intern = helper.Intern
	local currentLevel = if intern and intern.Model.Parent then intern.Level else 0
	if internLevel ~= currentLevel then
		buildIntern(helper, internLevel)
	end
end

function AutomationService.Start()
	DataService.OnLoaded(function(player)
		sync(player)
	end)
	DataService.OnReplicated(sync)
	Players.PlayerRemoving:Connect(function(player)
		-- The models live in the island model, which IslandService destroys.
		helpers[player] = nil
	end)

	-- Basket (and a periodic sync: the island may be claimed after the data loaded).
	task.spawn(function()
		while true do
			task.wait(BASKET.CheckInterval)
			local now = os.clock()
			for _, player in Players:GetPlayers() do
				sync(player)
				local helper = helpers[player]
				if helper then
					xpcall(checkBasket, reportError, player, helper, now)
				end
			end
		end
	end)

	-- Intern.
	task.spawn(function()
		local since = os.clock()
		while true do
			task.wait(INTERN.TickInterval)
			local now = os.clock()
			for player, helper in helpers do
				local intern = helper.Intern
				if intern and intern.Model.Parent then
					xpcall(tickIntern, reportError, player, helper, intern, now, since)
				end
			end
			since = now
		end
	end)
end

return AutomationService
