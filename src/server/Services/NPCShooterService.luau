--!strict
-- NPC shooters around each island. They never aim at the player: every shot targets a random point on the island,
-- and its whole path (flight + bounces) must stay away from where the player stands, so standing still earns
-- nothing (docs/decisions/0002). Shooters take turns: with n shooters, one fires every interval / n seconds.
-- Each shooter turns toward its target AimTime before it fires.
-- Looks: the ShooterTier's model from ReplicatedStorage.Assets (see Config/Gameplay → Shooters.Tiers), else a lower
-- tier's model with an outline in the tier colour, else a red block.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)

local IslandService = require(script.Parent.IslandService)
local ProjectileService = require(script.Parent.ProjectileService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Shooters
local ISLAND = Gameplay.Island
local BODY_SIZE = Vector3.new(2, 4, 2)
local BARREL_SIZE = Vector3.new(0.8, 0.8, CONFIG.BarrelLength)
-- Without a Muzzle attachment, custom models throw from this fraction of their height, a bit in front of them.
local MODEL_THROW_HEIGHT = 0.8
local MODEL_THROW_FORWARD = 1.5

type Shooter = {
	-- Holds everything of this shooter (platform included); destroyed when the ring shrinks.
	Model: Model,
	-- Custom model only: the imported model inside Model. Only this turns when aiming, so the platform stays put.
	Visual: Model?,
	-- Point on the island-surface height where the shooter stands.
	Ground: Vector3,
	-- Custom model: height of its pivot above its bottom. Fallback block: nil (uses Body and Barrel).
	PivotHeight: number?,
	Body: BasePart?,
	Barrel: BasePart?,
	Muzzle: Attachment?,
	-- The stick in the model's hand and its normal transparency, hidden for a moment after each throw.
	HandStick: { [BasePart]: number },
	NextFireAt: number,
	Plan: ProjectileService.ShotPlan?,
}

type Ring = {
	Shooters: { Shooter },
	Interval: number,
	-- ShooterTier level the models were built for.
	Tier: number,
}

local rings: { [Player]: Ring } = {}
local random = Random.new()

local NPCShooterService = {}

-- Shooters are decoration for physics: nothing collides with them, touches them or hits them in queries.
local function newShooterPart(name: string, size: Vector3, color: Color3, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.Color = color
	part.Anchored = true
	part.CanCollide = false
	part.CanTouch = false
	part.CanQuery = false
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

local function getRoot(player: Player): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

local function flatDirection(from: Vector3, to: Vector3): Vector3
	local flat = Vector3.new(to.X - from.X, 0, to.Z - from.Z)
	return if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
end

local function aimAt(shooter: Shooter, target: Vector3)
	local ground = shooter.Ground
	local pivotHeight, visual = shooter.PivotHeight, shooter.Visual
	if pivotHeight and visual then
		local pivot = ground + Vector3.new(0, pivotHeight, 0)
		local facing = CFrame.lookAt(pivot, pivot + flatDirection(ground, target))
		visual:PivotTo(facing * CFrame.Angles(0, math.rad(CONFIG.YawOffsetDegrees), 0))
		return
	end
	local body, barrel = shooter.Body, shooter.Barrel
	if body and barrel then
		local bodyPosition = ground + Vector3.new(0, BODY_SIZE.Y / 2, 0)
		body.CFrame = CFrame.lookAt(bodyPosition, bodyPosition + flatDirection(ground, target))
		local pivot = bodyPosition + Vector3.new(0, BODY_SIZE.Y / 2, 0)
		local direction = ProjectileService.GetLaunchDirection(pivot, target)
		local barrelCenter = pivot + direction * (CONFIG.BarrelLength / 2)
		barrel.CFrame = CFrame.lookAt(barrelCenter, barrelCenter + direction)
	end
end

-- Where the projectile starts, for the shooter's current aim at `target`.
local function throwPoint(shooter: Shooter, target: Vector3): Vector3
	local muzzle = shooter.Muzzle
	if muzzle then
		return muzzle.WorldPosition
	end
	local barrel = shooter.Barrel
	if barrel then
		return barrel.Position + barrel.CFrame.LookVector * (CONFIG.BarrelLength / 2)
	end
	return shooter.Ground
		+ Vector3.new(0, CONFIG.Height * MODEL_THROW_HEIGHT, 0)
		+ flatDirection(shooter.Ground, target) * MODEL_THROW_FORWARD
end

local function isSafeFromStandingPlayer(plan: ProjectileService.ShotPlan, playerPosition: Vector3): boolean
	local distance = ProjectileService.ClosestApproach(plan, playerPosition)
	return distance >= plan.Radius + CONFIG.MinDistanceFromPlayer
end

-- Aims the shooter at a random island point whose whole path stays clear of the player. Returns the plan,
-- or nil if no such point was found this time.
local function findShot(
	player: Player,
	shooter: Shooter,
	center: Vector3,
	playerPosition: Vector3
): ProjectileService.ShotPlan?
	local radius = ProjectileService.GetDiameter(player) / 2
	for _ = 1, CONFIG.TargetTries do
		-- sqrt spreads points evenly over the disc's area instead of bunching them in the middle.
		local distance = ISLAND.TargetRadius * math.sqrt(random:NextNumber())
		local angle = random:NextNumber() * 2 * math.pi
		local target = center + Vector3.new(math.cos(angle) * distance, radius, math.sin(angle) * distance)
		aimAt(shooter, target)
		local plan = ProjectileService.Plan(player, throwPoint(shooter, target), target)
		if plan and isSafeFromStandingPlayer(plan, playerPosition) then
			return plan
		end
	end
	return nil
end

-- Hides the stick in the shooter's hand for a moment, so it looks like that stick was thrown.
local function hideHandStick(shooter: Shooter)
	for part in shooter.HandStick do
		part.Transparency = 1
	end
	task.delay(CONFIG.HandStickHideTime, function()
		for part, transparency in shooter.HandStick do
			part.Transparency = transparency
		end
	end)
end

local function collectHandStick(model: Model): { [BasePart]: number }
	local parts: { [BasePart]: number } = {}
	local stick = model:FindFirstChild(CONFIG.HandStickName, true)
	if stick and stick:IsA("BasePart") then
		parts[stick] = stick.Transparency
	elseif stick then
		for _, descendant in stick:GetDescendants() do
			if descendant:IsA("BasePart") then
				parts[descendant] = descendant.Transparency
			end
		end
	end
	return parts
end

-- The best model for this tier: its own, else a lower tier's (then the legacy name). Second result: true if it
-- is the tier's own model.
local function cloneTierModel(tier: number): (Model?, boolean)
	for index = tier + 1, 1, -1 do
		local candidate = CONFIG.Tiers[index]
		if candidate and Assets.Has(candidate.AssetName) then
			return Assets.CloneModel(candidate.AssetName), index == tier + 1
		end
	end
	return Assets.CloneModel(CONFIG.LegacyAssetName), false
end

local function buildShooter(parent: Instance, center: Vector3, angle: number, tier: number): Shooter
	-- Angle 0 is north (−Z), then clockwise.
	local ground = center + Vector3.new(math.sin(angle), 0, -math.cos(angle)) * CONFIG.RingRadius

	local model = Instance.new("Model")
	local asset, isOwnModel = cloneTierModel(tier)
	local shooter: Shooter
	if asset and not isOwnModel and tier > 0 then
		-- Placeholder look until the tier has its own model: an outline in the tier colour.
		local outline = Instance.new("Highlight")
		outline.FillTransparency = 0.75
		outline.FillColor = CONFIG.Tiers[tier + 1].Color
		outline.OutlineColor = CONFIG.Tiers[tier + 1].Color
		outline.Parent = asset
	end
	if asset then
		Assets.ScaleTo(asset, CONFIG.Height, true)
		Assets.MakeVisualOnly(asset, true)
		local box, size = asset:GetBoundingBox()
		local muzzle = asset:FindFirstChild(CONFIG.MuzzleName, true)
		asset.Parent = model
		shooter = {
			Model = model,
			Visual = asset,
			Ground = ground,
			PivotHeight = asset:GetPivot().Position.Y - (box.Position.Y - size.Y / 2),
			Muzzle = if muzzle and muzzle:IsA("Attachment") then muzzle else nil,
			HandStick = collectHandStick(asset),
			NextFireAt = 0,
		}
	else
		local body = newShooterPart("Body", BODY_SIZE, Color3.fromRGB(220, 50, 50), model)
		local barrel = newShooterPart("Barrel", BARREL_SIZE, Color3.fromRGB(40, 40, 40), model)
		-- A face on the front so you can see where it is looking.
		local face = Instance.new("SurfaceGui")
		face.Face = Enum.NormalId.Front
		face.Parent = body
		local faceText = Instance.new("TextLabel")
		faceText.Size = UDim2.fromScale(1, 0.5)
		faceText.BackgroundTransparency = 1
		faceText.Text = ">:)"
		faceText.TextScaled = true
		faceText.Font = Enum.Font.FredokaOne
		faceText.TextColor3 = Color3.fromRGB(255, 255, 255)
		faceText.Parent = face
		shooter = {
			Model = model,
			Ground = ground,
			Body = body,
			Barrel = barrel,
			HandStick = {},
			NextFireAt = 0,
		}
	end
	model.Name = "Shooter"

	local platform = newShooterPart(
		"Platform",
		Vector3.new(1, CONFIG.PlatformDiameter, CONFIG.PlatformDiameter),
		Color3.fromRGB(120, 120, 130),
		model
	)
	platform.Shape = Enum.PartType.Cylinder
	platform.CFrame = CFrame.new(ground - Vector3.new(0, 0.5, 0)) * CFrame.Angles(0, 0, math.rad(90))

	model.Parent = parent
	aimAt(shooter, center)
	return shooter
end

-- Spreads the shooters' turns evenly over one interval.
local function schedule(ring: Ring, now: number)
	local count = #ring.Shooters
	for index, shooter in ring.Shooters do
		shooter.NextFireAt = now + CONFIG.FirstShotDelay + (index - 1) * ring.Interval / count
		shooter.Plan = nil
	end
end

-- Keeps the ring in sync with the active-shooter count and the fire interval. Returns the player's ring.
local function syncRing(player: Player, island: IslandService.Island, now: number): Ring
	local wanted = UpgradeService.GetActiveShooters(player)
	local interval = UpgradeService.GetValue(player, "FireRate")
	local tier = UpgradeService.GetLevel(player, "ShooterTier")
	local ring = rings[player]
	if ring and #ring.Shooters == wanted and ring.Tier == tier then
		if ring.Interval ~= interval then
			ring.Interval = interval
			schedule(ring, now)
		end
		return ring
	end
	if ring then
		for _, shooter in ring.Shooters do
			shooter.Model:Destroy()
		end
	end
	local rebuilt: Ring = { Shooters = {}, Interval = interval, Tier = tier }
	for index = 1, wanted do
		local angle = (index - 1) / wanted * 2 * math.pi
		table.insert(rebuilt.Shooters, buildShooter(island.ShooterFolder, island.Center, angle, tier))
	end
	schedule(rebuilt, now)
	rings[player] = rebuilt
	return rebuilt
end

local function updatePlayer(player: Player, now: number)
	local island = IslandService.GetIsland(player)
	if not island or not UpgradeService.IsReady(player) then
		return
	end
	local ring = syncRing(player, island, now)

	-- No character (dead or respawning): shooters wait.
	local root = getRoot(player)
	if not root then
		return
	end

	for _, shooter in ring.Shooters do
		if not shooter.Plan and now >= shooter.NextFireAt - CONFIG.AimTime then
			local plan = findShot(player, shooter, island.Center, root.Position)
			shooter.Plan = plan
			if not plan then
				-- Nowhere safe to throw right now: skip this turn.
				shooter.NextFireAt += ring.Interval
			end
		end
		local plan = shooter.Plan
		if plan and now >= shooter.NextFireAt then
			-- The player may have moved during the aim time: re-check the anti-farm rule.
			if not isSafeFromStandingPlayer(plan, root.Position) then
				plan = findShot(player, shooter, island.Center, root.Position)
			end
			if plan then
				ProjectileService.Fire(player, plan)
				hideHandStick(shooter)
			end
			shooter.Plan = nil
			-- Keep the turn order even if a frame was late.
			repeat
				shooter.NextFireAt += ring.Interval
			until shooter.NextFireAt > now
		end
	end
end

function NPCShooterService.Start()
	-- Tells whoever playtests which custom models are in place (docs: assets/README.md).
	local modelNames: { string } = {}
	for _, tier in CONFIG.Tiers do
		table.insert(modelNames, tier.AssetName)
	end
	table.insert(modelNames, CONFIG.LegacyAssetName)
	for _, id in Projectiles.Tiers do
		local assetName = Projectiles.Defs[id].AssetName
		if assetName then
			table.insert(modelNames, assetName)
		end
	end
	local found: { string } = {}
	local missing: { string } = {}
	for _, name in modelNames do
		table.insert(if Assets.Has(name) then found else missing, name)
	end
	print(`[4M] Models found: {table.concat(found, ", ")}`)
	print(`[4M] Models missing (placeholders used): {table.concat(missing, ", ")}`)

	Players.PlayerRemoving:Connect(function(player)
		-- The models go with the island; only forget the bookkeeping.
		rings[player] = nil
	end)

	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for _, player in Players:GetPlayers() do
			updatePlayer(player, now)
		end
	end)
end

return NPCShooterService
