--!strict
-- Upgrade stalls and the rebirth shrine on every player island (Config/Stations → Stalls, docs/GAME_DESIGN.md →
-- World → Island layout and Upgrades → Upgrade stands). Every stall stands at its polar spot on the outer ring,
-- its front toward the island centre, so its billboard reads from the field.
-- Upgrade stalls are PropService props (Prop_UpgradeStand_<UpgradeId>) with an invisible part above the counter
-- (Station_<UpgradeId>) that holds two ProximityPrompts:
--   E "Upgrade"      → the server buys a level (up to Config/Stations.StackMax with the Stack Upgrade pass),
--   F "Buy with R$"  → the owner's client sends ShopBuy for the matching Instant<UpgradeId> product.
-- A stall whose EconomyConfig.UnlockAtShibaTier is above the owner's Shiba Tier is locked: grey shutter with a
-- padlock, prompts off, until that tier is reached.
-- The rebirth shrine (Prop_RebirthShrine, anchor Station_Rebirth) has one hold prompt calling
-- RebirthService.TryRebirth; it is enabled only while RebirthService.CanRebirth.
-- Anchors carry the attributes Kind, Locked and UnlockAt for the client (docs/NETWORK.md).
-- "More Shibas" also gets a glowing pad on the Shiba ring where the next Shiba will stand; stepping on it buys it.
-- Only the island owner can use them. Billboards and hints are drawn by the owner's client (StationController).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)
local Stations = require(ReplicatedStorage.Shared.Config.Stations)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local IslandService = require(script.Parent.IslandService)
local PropService = require(script.Parent.PropService)
local RebirthService = require(script.Parent.RebirthService)
local UpgradeService = require(script.Parent.UpgradeService)

local RING_RADIUS = Gameplay.Shooters.RingRadius
local ISLAND_WAIT_SECONDS = 10

type Stand = {
	Anchor: Part,
	-- Disabled at max level and while locked.
	Prompts: { ProximityPrompt },
	-- Shutter and padlock, parented to the Stations folder while locked.
	Lock: Model,
	UnlockAt: number,
}

type Shrine = {
	Anchor: Part,
	Prompt: ProximityPrompt,
	-- The glowing orb of the part-built shrine (nil with an imported model that has none).
	Orb: BasePart?,
}

type Built = {
	Folder: Folder,
	-- UpgradeId → its stall.
	Stands: { [string]: Stand },
	Shrine: Shrine?,
	Pad: Part,
	-- Owned Shibas the pad was last placed for (−1 = not placed yet).
	PadFor: number,
}

local built: { [Player]: Built } = {}
local pressLimiter = RateLimiter.New(Stations.MaxPressesPerSecond, 1)
local lastPadBuy: { [Player]: number } = {}
local lastRebirth: { [Player]: number } = {}

local StationService = {}

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

-- Where a stall stands on the island surface, its front (−Z, the look vector) toward the island centre.
local function stallFrame(island: IslandService.Island, stall: Stations.Stall): CFrame
	local position = island.Center + direction(island.HubAngle + math.rad(stall.Angle)) * stall.Radius
	return CFrame.lookAt(position, island.Center)
end

-- A colourful market-stall counter in the upgrade's colour, bottom centre at the origin, front toward −Z.
local function standBuilder(color: Color3): PropService.Builder
	return function(model: Model, height: number)
		local scale = height / 7
		local function block(size: Vector3, offset: CFrame, partColor: Color3, material: Enum.Material?): Part
			return PropService.Part(model, Enum.PartType.Block, size * scale, offset, partColor, material)
		end
		local white = Color3.fromRGB(250, 248, 240)
		local wood = Color3.fromRGB(170, 115, 65)
		-- Cabinet with a white stripe on the front.
		block(Vector3.new(7, 3, 3.2), CFrame.new(0, 1.5 * scale, 0), color)
		block(Vector3.new(7.1, 0.6, 3.3), CFrame.new(0, 2.3 * scale, 0), white)
		-- Counter top.
		block(Vector3.new(7.6, 0.4, 3.8), CFrame.new(0, 3.2 * scale, -0.1 * scale), wood, Enum.Material.WoodPlanks)
		-- Posts at the back and a striped awning leaning forward.
		for _, x in { -3.4, 3.4 } do
			block(Vector3.new(0.4, 3.6, 0.4), CFrame.new(x * scale, 5.1 * scale, 1.3 * scale), wood, Enum.Material.Wood)
		end
		for index = 0, 5 do
			local x = (-3.25 + index * 1.3) * scale
			local stripe = block(
				Vector3.new(1.3, 0.3, 4.2),
				CFrame.new(x, 6.8 * scale, -0.2 * scale) * CFrame.Angles(math.rad(12), 0, 0),
				if index % 2 == 0 then color else white
			)
			stripe.CanCollide = false
		end
		-- A glowing orb on the counter: "something to buy here".
		local orb = PropService.Part(
			model,
			Enum.PartType.Ball,
			Vector3.one * 1.2 * scale,
			CFrame.new(0, 4 * scale, 0.4 * scale),
			color,
			Enum.Material.Neon
		)
		orb.CanCollide = false
	end
end

-- Grey roll shutter over the stall's opening (counter to awning) with a gold padlock on it, around `cframe` (the
-- stall's bottom centre). Not parented: updateStations shows it while the stall is locked.
local function buildLock(id: string, cframe: CFrame): Model
	local model = Instance.new("Model")
	model.Name = `{Stations.LockName}_{id}`
	local scale = Stations.StandHeight / 7
	local function piece(size: Vector3, x: number, y: number, z: number, color: Color3, material: Enum.Material)
		local lockPart = PropService.Part(
			model,
			Enum.PartType.Block,
			size * scale,
			cframe * CFrame.new(x * scale, y * scale, z * scale),
			color,
			material
		)
		lockPart.CanCollide = false
		lockPart.CanQuery = false
		lockPart.CanTouch = false
	end
	piece(Vector3.new(7.2, 3, 0.2), 0, 4.9, -1, Stations.LockColor, Enum.Material.DiamondPlate)
	piece(Vector3.new(1.4, 1.2, 0.5), 0, 4.4, -1.35, Stations.PadlockColor, Enum.Material.Foil)
	piece(Vector3.new(0.25, 0.8, 0.25), -0.45, 5.3, -1.35, Stations.LockColor, Enum.Material.Metal)
	piece(Vector3.new(0.25, 0.8, 0.25), 0.45, 5.3, -1.35, Stations.LockColor, Enum.Material.Metal)
	piece(Vector3.new(1.15, 0.25, 0.25), 0, 5.7, -1.35, Stations.LockColor, Enum.Material.Metal)
	return model
end

local function invisiblePart(name: string, size: Vector3, cframe: CFrame, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Transparency = 1
	part.Parent = parent
	return part
end

local function newPrompt(
	name: string,
	actionText: string,
	objectText: string,
	key: Enum.KeyCode,
	gamepadKey: Enum.KeyCode,
	parent: Instance
): ProximityPrompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = name
	prompt.ActionText = actionText
	prompt.ObjectText = objectText
	prompt.KeyboardKeyCode = key
	prompt.GamepadKeyCode = gamepadKey
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = Stations.PromptDistance
	prompt.RequiresLineOfSight = false
	prompt.Parent = parent
	return prompt
end

-- Sets the anchor's Locked attribute only when it changes (no needless replication).
local function setLocked(anchor: Part, locked: boolean)
	if anchor:GetAttribute(Stations.LockedAttribute) ~= locked then
		anchor:SetAttribute(Stations.LockedAttribute, locked)
	end
end

local function onStandPressed(owner: Player, player: Player, upgradeId: string)
	if player ~= owner or not RateLimiter.Allow(pressLimiter, player) then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	-- The prompt is off while locked, but never trust that alone.
	if (state.UpgradeLevels.ShooterTier or 0) < (EconomyConfig.UnlockAtShibaTier[upgradeId] or 0) then
		return
	end
	local count = if state.Passes.StackUpgrade then Stations.StackMax else 1
	UpgradeService.TryPurchase(player, upgradeId, count)
end

local function onRebirthTriggered(owner: Player, player: Player)
	if player ~= owner then
		return
	end
	local now = os.clock()
	if now - (lastRebirth[player] or -math.huge) < Stations.RebirthCooldown then
		return
	end
	lastRebirth[player] = now
	RebirthService.TryRebirth(player)
end

local function buildStand(owner: Player, stall: Stations.Stall, island: IslandService.Island, into: Built)
	local def = if stall.Upgrade then Upgrades.Defs[stall.Upgrade] else nil
	if not def then
		warn(`[StationService] Unknown upgrade "{stall.Upgrade}" in Config/Stations`)
		return
	end
	local cframe = stallFrame(island, stall)
	PropService.Place(
		`{Stations.PropPrefix}{def.Id}`,
		cframe,
		Stations.StandHeight,
		standBuilder(def.Color),
		into.Folder
	)

	-- Holds the prompts; the client puts the billboard above it.
	local anchor = invisiblePart(
		`{Stations.AnchorPrefix}{def.Id}`,
		Vector3.new(2, 2, 2),
		cframe * CFrame.new(0, Stations.StandHeight * 0.55, -1),
		into.Folder
	)
	local unlockAt = EconomyConfig.UnlockAtShibaTier[def.Id] or 0
	anchor:SetAttribute(Stations.KindAttribute, "Upgrade")
	anchor:SetAttribute(Stations.UnlockAtAttribute, unlockAt)
	anchor:SetAttribute(Stations.LockedAttribute, false)

	local upgradePrompt = newPrompt(
		`{Stations.UpgradePromptPrefix}{def.Id}`,
		"Upgrade",
		def.DisplayName,
		Enum.KeyCode.E,
		Enum.KeyCode.ButtonX,
		anchor
	)
	upgradePrompt.Triggered:Connect(function(player)
		onStandPressed(owner, player, def.Id)
	end)
	local prompts = { upgradePrompt }

	local product = Shop.GetProduct(`{Stations.RobuxProductPrefix}{def.Id}`)
	if product then
		local robuxPrompt = newPrompt(
			`{Stations.RobuxPromptPrefix}{def.Id}`,
			"Buy with R$",
			`{product.DisplayName} · R$ {product.Robux}`,
			Enum.KeyCode.F,
			Enum.KeyCode.ButtonY,
			anchor
		)
		-- Below the E prompt instead of on top of it.
		robuxPrompt.UIOffset = Vector2.new(0, 80)
		table.insert(prompts, robuxPrompt)
	end
	into.Stands[def.Id] = { Anchor = anchor, Prompts = prompts, Lock = buildLock(def.Id, cframe), UnlockAt = unlockAt }
end

local function buildShrine(owner: Player, stall: Stations.Stall, island: IslandService.Island, into: Built)
	local cframe = stallFrame(island, stall)
	local model = PropService.Place(
		Stations.RebirthPropName,
		cframe,
		Stations.RebirthHeight,
		PropService.Builders.RebirthShrine,
		into.Folder
	)
	local orb = model:FindFirstChild("Orb", true)

	-- In front of the altar, at chest height; the client puts its billboard above it.
	local anchor = invisiblePart(
		Stations.RebirthAnchorName,
		Vector3.new(2, 2, 2),
		cframe * CFrame.new(0, Stations.RebirthHeight * 0.45, -2),
		into.Folder
	)
	anchor:SetAttribute(Stations.KindAttribute, "Rebirth")
	anchor:SetAttribute(Stations.UnlockAtAttribute, EconomyConfig.Rebirth.MinShibaTier)
	anchor:SetAttribute(Stations.LockedAttribute, true)

	local prompt =
		newPrompt(Stations.RebirthPromptName, "Rebirth", "Rebirth Shrine", Enum.KeyCode.E, Enum.KeyCode.ButtonX, anchor)
	prompt.HoldDuration = Stations.RebirthHoldSeconds
	prompt.Enabled = false
	prompt.Triggered:Connect(function(player)
		onRebirthTriggered(owner, player)
	end)
	into.Shrine = {
		Anchor = anchor,
		Prompt = prompt,
		Orb = if orb and orb:IsA("BasePart") then orb else nil,
	}
end

-- Where the next Shiba will stand: one of the positions of the ring with one more Shiba, the one farthest from the
-- Shibas standing now (NPCShooterService spaces them evenly, the bridge side exactly between two).
local function nextShibaAngle(hubAngle: number, active: number, owned: number): number
	local nextCount = owned + 1
	local bestAngle = hubAngle + (nextCount - 0.5) / nextCount * 2 * math.pi
	local bestGap = -1
	for index = 1, nextCount do
		local angle = hubAngle + (index - 0.5) / nextCount * 2 * math.pi
		local gap = math.huge
		for current = 1, active do
			local other = hubAngle + (current - 0.5) / active * 2 * math.pi
			gap = math.min(gap, math.abs(math.atan2(math.sin(angle - other), math.cos(angle - other))))
		end
		if gap > bestGap then
			bestGap = gap
			bestAngle = angle
		end
	end
	return bestAngle
end

-- Locks/unlocks the stalls, turns the prompts on and off, and moves the pad to the next Shiba's spot (or hides it
-- when More Shibas is maxed).
local function updateStations(player: Player)
	local stations = built[player]
	local state = DataService.GetState(player)
	local island = IslandService.GetIsland(player)
	if not stations or not state or not island then
		return
	end
	local tier = state.UpgradeLevels.ShooterTier or 0
	for id, stand in stations.Stands do
		local locked = tier < stand.UnlockAt
		local open = not locked and (state.UpgradeLevels[id] or 0) < Upgrades.GetMaxLevel(id, state.Passes)
		for _, prompt in stand.Prompts do
			prompt.Enabled = open
		end
		setLocked(stand.Anchor, locked)
		stand.Lock.Parent = if locked then stations.Folder else nil
	end

	local shrine = stations.Shrine
	if shrine then
		local canRebirth = RebirthService.CanRebirth(player)
		shrine.Prompt.Enabled = canRebirth
		setLocked(shrine.Anchor, not canRebirth)
		local orb = shrine.Orb
		if orb then
			-- Dim until the player can rebirth.
			orb.Transparency = if canRebirth then 0 else 0.6
			local light = orb:FindFirstChildOfClass("PointLight")
			if light then
				light.Enabled = canRebirth
			end
		end
	end

	local level = state.UpgradeLevels.Shooters or 0
	local maxed = level >= Upgrades.GetMaxLevel("Shooters", state.Passes)
	local owned = Upgrades.GetValue("Shooters", level)
	local placeFor = if maxed then 0 else owned * 100 + state.ActiveShooters
	if stations.PadFor == placeFor then
		return
	end
	stations.PadFor = placeFor
	local pad = stations.Pad
	if maxed then
		pad.Parent = nil
		return
	end
	local angle = nextShibaAngle(island.HubAngle, state.ActiveShooters, owned)
	local position = island.Center + direction(angle) * RING_RADIUS
	-- Upright cylinder (its axis is X), half sunk so it looks like a pad on the grass.
	pad.CFrame = CFrame.new(position + Vector3.new(0, Stations.PadSize.Y / 4, 0)) * CFrame.Angles(0, 0, math.rad(90))
	pad.Parent = stations.Folder
end

local function buildPad(owner: Player, parent: Folder): Part
	local pad = Instance.new("Part")
	pad.Name = Stations.PadName
	pad.Shape = Enum.PartType.Cylinder
	-- A cylinder's axis is its X axis (updateStations places and rotates it upright).
	pad.Size = Vector3.new(Stations.PadSize.Y, Stations.PadSize.X, Stations.PadSize.Z)
	pad.Color = Stations.PadColor
	pad.Material = Enum.Material.Neon
	pad.Anchored = true
	pad.CanCollide = false
	pad.CanQuery = false
	pad.CanTouch = true
	pad.Parent = parent
	local light = Instance.new("PointLight")
	light.Color = Stations.PadColor
	light.Range = 12
	light.Brightness = 1.5
	light.Parent = pad

	pad.Touched:Connect(function(hit)
		local character = owner.Character
		if not character or not hit:IsDescendantOf(character) then
			return
		end
		local now = os.clock()
		if now - (lastPadBuy[owner] or 0) < Stations.PadCooldown then
			return
		end
		lastPadBuy[owner] = now
		UpgradeService.TryPurchase(owner, "Shooters", 1)
	end)
	return pad
end

local function build(player: Player)
	local island = IslandService.GetIsland(player)
	local deadline = os.clock() + ISLAND_WAIT_SECONDS
	while not island and player.Parent and os.clock() < deadline do
		task.wait(0.2)
		island = IslandService.GetIsland(player)
	end
	if not island or not player.Parent then
		-- No free island (server full): the player uses the upgrade menu instead.
		return
	end
	local old = built[player]
	if old then
		old.Folder:Destroy()
		for _, stand in old.Stands do
			stand.Lock:Destroy()
		end
	end

	local folder = Instance.new("Folder")
	folder.Name = Stations.FolderName
	local stations: Built = { Folder = folder, Stands = {}, Pad = buildPad(player, folder), PadFor = -1 }
	for _, stall in Stations.Stalls do
		if stall.Kind == "Upgrade" then
			buildStand(player, stall, island, stations)
		elseif stall.Kind == "Rebirth" then
			buildShrine(player, stall, island, stations)
		else
			warn(`[StationService] Unknown stall kind "{stall.Kind}" in Config/Stations`)
		end
	end
	folder.Parent = island.Model
	built[player] = stations
	updateStations(player)
end

function StationService.Start()
	-- Built once the save is loaded (it decides the pad's place); again after an admin reset.
	DataService.OnLoaded(function(player)
		build(player)
	end)
	DataService.OnReplicated(updateStations)
	Players.PlayerRemoving:Connect(function(player)
		-- The folder lives in the island model, which IslandService destroys; unparented locks go with the table.
		local stations = built[player]
		if stations then
			for _, stand in stations.Stands do
				stand.Lock:Destroy()
			end
		end
		built[player] = nil
		lastPadBuy[player] = nil
		lastRebirth[player] = nil
		RateLimiter.Remove(pressLimiter, player)
	end)
end

return StationService
