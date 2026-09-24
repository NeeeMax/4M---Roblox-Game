--!strict
-- NPC shooters around each island. They never aim at the player: every shot targets a random point on the
-- island that is far enough from the player, so standing still earns nothing (docs/decisions/0002).
-- Each shooter turns toward its target AimTime before it fires.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local IslandService = require(script.Parent.IslandService)
local ProjectileService = require(script.Parent.ProjectileService)
local UpgradeService = require(script.Parent.UpgradeService)

local CONFIG = Gameplay.Shooters
local ISLAND = Gameplay.Island
local BODY_SIZE = Vector3.new(2, 4, 2)
local BARREL_SIZE = Vector3.new(0.8, 0.8, CONFIG.BarrelLength)

type Shooter = {
	Model: Model,
	Body: BasePart,
	Barrel: BasePart,
	-- Centre of the body; the barrel pivots on top of it.
	BodyPosition: Vector3,
	NextAimAt: number,
	FireAt: number?,
	Target: Vector3?,
}

local shootersByPlayer: { [Player]: { Shooter } } = {}
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

local function barrelMouth(shooter: Shooter): Vector3
	return shooter.Barrel.Position + shooter.Barrel.CFrame.LookVector * (CONFIG.BarrelLength / 2)
end

local function aimAt(shooter: Shooter, target: Vector3)
	local bodyPosition = shooter.BodyPosition
	shooter.Body.CFrame = CFrame.lookAt(bodyPosition, Vector3.new(target.X, bodyPosition.Y, target.Z))
	local pivot = bodyPosition + Vector3.new(0, BODY_SIZE.Y / 2, 0)
	local direction = ProjectileService.GetLaunchDirection(pivot, target)
	local barrelCenter = pivot + direction * (CONFIG.BarrelLength / 2)
	shooter.Barrel.CFrame = CFrame.lookAt(barrelCenter, barrelCenter + direction)
end

local function isFarEnough(target: Vector3, playerPosition: Vector3, projectileRadius: number): boolean
	local flatDistance = Vector3.new(target.X - playerPosition.X, 0, target.Z - playerPosition.Z).Magnitude
	return flatDistance >= projectileRadius + CONFIG.MinDistanceFromPlayer
end

-- A random landing point on the island (projectile centre height) far enough from the player, or nil.
local function pickTarget(center: Vector3, playerPosition: Vector3, projectileRadius: number): Vector3?
	for _ = 1, CONFIG.TargetTries do
		-- sqrt spreads points evenly over the disc's area instead of bunching them in the middle.
		local distance = ISLAND.TargetRadius * math.sqrt(random:NextNumber())
		local angle = random:NextNumber() * 2 * math.pi
		local target = center + Vector3.new(math.cos(angle) * distance, projectileRadius, math.sin(angle) * distance)
		if isFarEnough(target, playerPosition, projectileRadius) then
			return target
		end
	end
	return nil
end

local function buildShooter(parent: Instance, center: Vector3, angle: number, now: number): Shooter
	-- Angle 0 is north (−Z), then clockwise.
	local ground = center + Vector3.new(math.sin(angle), 0, -math.cos(angle)) * CONFIG.RingRadius

	local model = Instance.new("Model")
	model.Name = "Shooter"

	local platform = newShooterPart(
		"Platform",
		Vector3.new(1, CONFIG.PlatformDiameter, CONFIG.PlatformDiameter),
		Color3.fromRGB(120, 120, 130),
		model
	)
	platform.Shape = Enum.PartType.Cylinder
	platform.CFrame = CFrame.new(ground - Vector3.new(0, 0.5, 0)) * CFrame.Angles(0, 0, math.rad(90))

	local bodyPosition = ground + Vector3.new(0, BODY_SIZE.Y / 2, 0)
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

	model.PrimaryPart = body
	model.Parent = parent

	local shooter: Shooter = {
		Model = model,
		Body = body,
		Barrel = barrel,
		BodyPosition = bodyPosition,
		NextAimAt = now + CONFIG.FirstShotDelay + random:NextNumber() * CONFIG.StartOffsetMax,
	}
	aimAt(shooter, center)
	return shooter
end

-- Rebuilds the ring when the active-shooter count changed. Returns the player's shooters.
local function syncShooterCount(player: Player, island: IslandService.Island, now: number): { Shooter }
	local wanted = UpgradeService.GetActiveShooters(player)
	local shooters = shootersByPlayer[player]
	if shooters and #shooters == wanted then
		return shooters
	end
	if shooters then
		for _, shooter in shooters do
			shooter.Model:Destroy()
		end
	end
	local rebuilt: { Shooter } = {}
	for index = 1, wanted do
		local angle = (index - 1) / wanted * 2 * math.pi
		table.insert(rebuilt, buildShooter(island.ShooterFolder, island.Center, angle, now))
	end
	shootersByPlayer[player] = rebuilt
	return rebuilt
end

local function updatePlayer(player: Player, now: number)
	local island = IslandService.GetIsland(player)
	if not island or not UpgradeService.IsReady(player) then
		return
	end
	local shooters = syncShooterCount(player, island, now)

	-- No character (dead or respawning): shooters wait.
	local root = getRoot(player)
	if not root then
		return
	end
	local interval = UpgradeService.GetValue(player, "FireRate")
	local radius = ProjectileService.GetDiameter(player) / 2

	for _, shooter in shooters do
		local fireAt = shooter.FireAt
		if not fireAt then
			if now >= shooter.NextAimAt then
				local target = pickTarget(island.Center, root.Position, radius)
				if target then
					shooter.Target = target
					shooter.FireAt = now + CONFIG.AimTime
					aimAt(shooter, target)
				else
					shooter.NextAimAt = now + interval
				end
			end
		elseif now >= fireAt then
			-- The player may have walked onto the target during the aim time: re-check the anti-farm rule.
			local target = shooter.Target
			if target and not isFarEnough(target, root.Position, radius) then
				target = pickTarget(island.Center, root.Position, radius)
				if target then
					aimAt(shooter, target)
				end
			end
			if target then
				ProjectileService.Fire(player, barrelMouth(shooter), target)
			end
			shooter.FireAt = nil
			shooter.Target = nil
			shooter.NextAimAt = now + math.max(interval - CONFIG.AimTime, 0)
		end
	end
end

function NPCShooterService.Start()
	Players.PlayerRemoving:Connect(function(player)
		-- The models go with the island; only forget the bookkeeping.
		shootersByPlayer[player] = nil
	end)

	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for _, player in Players:GetPlayers() do
			updatePlayer(player, now)
		end
	end)
end

return NPCShooterService
