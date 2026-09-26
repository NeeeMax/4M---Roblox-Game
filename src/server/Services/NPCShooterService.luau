--!strict
-- NPC shooters around each island. They never aim at the player: every shot targets a random point on the island,
-- and its whole path (flight + bounces) must stay away from where the player stands, so standing still earns
-- nothing (docs/decisions/0002). Shooters take turns: with n shooters, one fires every interval / n seconds.
-- The interval comes from the Shiba tier (and the fire-rate boost, StickStorm), held to the stick density cap
-- (UpgradeService.GetThrowRate, Gameplay.Shooters.MaxThrowsPerSecond): above it the ring throws at the cap and every
-- stick carries ValueMultiplier = natural ÷ capped rate, so income stays the same. Each shooter turns toward its
-- target AimTime before it fires. Shooters only fire while their owner is on (or next to) their island. The ring
-- leaves a gap where the bridge from the hub arrives.
-- Looks: the ShooterTier's model from ReplicatedStorage.Assets (see Config/Gameplay → Shooters.Tiers), else a lower
-- tier's model with an outline in the tier colour, else a red block. Shiny / Mythic editions use their base model
-- with an outline and a light aura in the tier colour (Config/ShibaEffects → Editions). Each Shiba stands on its tier's platform
-- (Config/ShibaPlatforms) inside an invisible wall, and holds the player's current projectile in its paw.
-- Shiba Variants: shooter n is ring slot n; its variant (VariantService) adds a look (Config/ShibaEffects → Variants,
-- attribute Variant on the model, Huge = HugeScale× taller + platform ring) and multiplies its sticks' value.
-- The server places a custom model once and then only publishes where it should face (attribute
-- Shooters.Motion.AimYawAttribute); clients turn it smoothly (Controllers/ShibaController). Throw points are
-- computed from the aim, never read from the (client-turned) model.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Assets = require(ReplicatedStorage.Shared.Util.Assets)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Projectiles = require(ReplicatedStorage.Shared.Config.Projectiles)
local ShibaEffects = require(ReplicatedStorage.Shared.Config.ShibaEffects)
local ShibaPlatforms = require(ReplicatedStorage.Shared.Config.ShibaPlatforms)

local IslandService = require(script.Parent.IslandService)
local ProjectileService = require(script.Parent.ProjectileService)
local UpgradeService = require(script.Parent.UpgradeService)
local VariantService = require(script.Parent.VariantService)

local CONFIG = Gameplay.Shooters
local ISLAND = Gameplay.Island
local HAND = CONFIG.HandProjectile
local MOTION = CONFIG.Motion
local BODY_SIZE = Vector3.new(2, 4, 2)
local BARREL_SIZE = Vector3.new(0.8, 0.8, CONFIG.BarrelLength)
-- Without a Muzzle attachment, custom models throw from this fraction of their height, a bit in front of them.
local MODEL_THROW_HEIGHT = 0.8
local MODEL_THROW_FORWARD = 1.5
local AXES = { Vector3.xAxis, Vector3.yAxis, Vector3.zAxis }

type Shooter = {
	-- Holds everything of this shooter (platform and barrier included); destroyed when the ring is rebuilt.
	Model: Model,
	-- Custom model only: the imported model inside Model. Clients turn only this, so the platform stays put.
	Visual: Model?,
	-- Point on top of the platform where the shooter stands.
	Ground: Vector3,
	-- Model height in studs (the tier's Height).
	Height: number,
	-- Custom model: height of its pivot above its bottom. Fallback block: nil (uses Body and Barrel).
	PivotHeight: number?,
	-- Custom model with a Muzzle attachment: its position relative to the model's pivot.
	MuzzleOffset: Vector3?,
	Body: BasePart?,
	Barrel: BasePart?,
	NextFireAt: number,
	Plan: ProjectileService.ShotPlan?,
	-- Shiba Variants: the slot's variant the model was built with (VariantService; a change rebuilds the ring).
	Variant: string,
}

type Ring = {
	Shooters: { Shooter },
	-- Seconds between two throws of one shooter (after the density cap).
	Interval: number,
	-- What every stick of this ring is worth in throws (density cap; 1 below the cap).
	ValueMultiplier: number,
	-- ShooterTier and ProjectileTier levels the models were built for.
	Tier: number,
	ProjectileTier: number,
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

-- Yaw of a custom model's pivot facing `target` from `ground`: CFrame.Angles(0, yaw, 0) looks along the flat
-- direction, turned by YawOffsetDegrees.
local function aimYaw(ground: Vector3, target: Vector3): number
	local direction = flatDirection(ground, target)
	return math.atan2(-direction.X, -direction.Z) + math.rad(CONFIG.YawOffsetDegrees)
end

-- The custom model's pivot while it faces `target`.
local function pivotFrame(ground: Vector3, pivotHeight: number, target: Vector3): CFrame
	return CFrame.new(ground + Vector3.new(0, pivotHeight, 0)) * CFrame.Angles(0, aimYaw(ground, target), 0)
end

-- Turns the shooter toward `target`: a custom model gets the new yaw (clients turn it), the fallback block snaps.
local function faceTarget(shooter: Shooter, target: Vector3)
	local ground = shooter.Ground
	local visual = shooter.Visual
	if visual then
		visual:SetAttribute(MOTION.AimYawAttribute, aimYaw(ground, target))
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

-- Where the projectile starts when the shooter faces `target`. Pure math: it doesn't depend on how the model is
-- currently turned (clients turn it smoothly, the server never does).
local function throwPoint(shooter: Shooter, target: Vector3): Vector3
	local muzzleOffset, pivotHeight = shooter.MuzzleOffset, shooter.PivotHeight
	if muzzleOffset and pivotHeight then
		return pivotFrame(shooter.Ground, pivotHeight, target) * muzzleOffset
	end
	if shooter.Barrel then
		-- The barrel's tip: it starts at the top of the body and points along the launch direction.
		local pivot = shooter.Ground + Vector3.new(0, BODY_SIZE.Y, 0)
		return pivot + ProjectileService.GetLaunchDirection(pivot, target) * CONFIG.BarrelLength
	end
	return shooter.Ground
		+ Vector3.new(0, shooter.Height * MODEL_THROW_HEIGHT, 0)
		+ flatDirection(shooter.Ground, target) * MODEL_THROW_FORWARD * shooter.Height / CONFIG.Height
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
		local plan = ProjectileService.Plan(player, throwPoint(shooter, target), target)
		if plan and isSafeFromStandingPlayer(plan, playerPosition) then
			faceTarget(shooter, target)
			return plan
		end
	end
	return nil
end

local function hideMarker(model: Model, name: string)
	local marker = model:FindFirstChild(name, true)
	if marker and marker:IsA("BasePart") then
		marker.Transparency = 1
	end
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

-- The model of the projectile fired at this ProjectileTier level (else a lower tier's), or nil if none exists.
local function cloneProjectileModel(level: number): Model?
	for _, name in Projectiles.AssetCandidates(Projectiles.ForTier(level).Id) do
		if Assets.Has(name) then
			return Assets.CloneModel(name)
		end
	end
	return nil
end

local function component(vector: Vector3, index: number): number
	return if index == 1 then vector.X elseif index == 2 then vector.Y else vector.Z
end

local function longestAxis(size: Vector3): number
	if size.X >= size.Y and size.X >= size.Z then
		return 1
	end
	return if size.Y >= size.Z then 2 else 3
end

-- The paw's grip point (the stick's lower end, where it meets the paw), the stick's axis pointing up, and its length.
local function pawGrip(stick: BasePart): (Vector3, Vector3, number)
	local stickAxis = longestAxis(stick.Size)
	local stickLength = component(stick.Size, stickAxis)
	local up = stick.CFrame:VectorToWorldSpace(AXES[stickAxis])
	if up.Y < 0 then
		up = -up
	end
	return stick.Position - up * stickLength / 2, up, stickLength
end

-- Which axis of the projectile's box (in the model's own orientation) is its long axis. With a Grip marker it is
-- model-local Y by contract (assets/README.md); if Y is clearly not long, the export went wrong: use the longest.
local function handAxis(projectile: Model, size: Vector3, hasGrip: boolean): number
	local longest = longestAxis(size)
	if not hasGrip or size.Y >= component(size, longest) * 0.6 then
		return if hasGrip then 2 else longest
	end
	warn(`[4M] {projectile.Name}: its Grip model is not long along Y, using its longest side instead`)
	return longest
end

-- Puts `projectile` into the paw of a model facing `facing`, where `stick` is: LengthScale × the stick's length,
-- its long axis along the stick (pointing away from the paw), its grip point on the stick's lower end and its
-- model-local X along the model's right.
-- Grip point: the projectile's Grip marker if it has one (hidden here), else the negative end (GripAtNegativeEnd) of
-- the centre line of its longest bounding-box side. The Grip is read after scaling, so it is exactly where the
-- scaled model has it.
local function placeInPaw(projectile: Model, stick: BasePart, facing: CFrame)
	local paw, up, stickLength = pawGrip(stick)
	local grip = Assets.HideMarkers(projectile, HAND.GripName)

	local _, size = projectile:GetBoundingBox()
	local axis = handAxis(projectile, size, grip ~= nil)
	local length = component(size, axis)
	if length <= 0 then
		return
	end
	projectile:ScaleTo(projectile:GetScale() * stickLength * HAND.LengthScale / length)
	-- The box has the model's own orientation (its pivot's), so its axes are the model-local axes.
	local box, scaledSize = projectile:GetBoundingBox()
	local side = box:VectorToWorldSpace(if axis == 1 then Vector3.zAxis else Vector3.xAxis)
	local along = box:VectorToWorldSpace(AXES[axis])
	local gripPoint: Vector3
	if grip then
		gripPoint = grip.Position
		-- From the grip toward the rest of the item (the bulk of the box), whichever way model-local Y points.
		if (box.Position - gripPoint):Dot(along) < 0 then
			along = -along
			side = -side
		end
	else
		along *= if HAND.GripAtNegativeEnd then 1 else -1
		gripPoint = box.Position - along * component(scaledSize, axis) / 2
	end
	local from = CFrame.fromMatrix(gripPoint, side, along)

	local right = facing.RightVector - up * facing.RightVector:Dot(up)
	if right.Magnitude < 1e-3 then
		-- The stick points sideways: roll by the model's forward instead.
		right = facing.LookVector - up * facing.LookVector:Dot(up)
	end
	local to = CFrame.fromMatrix(paw, right.Unit, up)
	projectile:PivotTo(to * from:ToObjectSpace(projectile:GetPivot()))
end

-- Replaces the model's stick with the current projectile (named HAND.Name, a direct child of the model, which is how
-- ShibaController finds it). Without a projectile model, or with a stick that is not a single part, the stick stays.
local function equipHandProjectile(asset: Model, projectileLevel: number)
	local stick = asset:FindFirstChild(CONFIG.HandStickName, true)
	local stickPart = if stick and stick:IsA("BasePart") then stick else nil
	local projectile = if stickPart then cloneProjectileModel(projectileLevel) else nil
	if not (stickPart and projectile) then
		return
	end
	Assets.MakeVisualOnly(projectile, true)
	placeInPaw(projectile, stickPart, asset:GetPivot())
	projectile.Name = HAND.Name
	projectile.Parent = asset
	stickPart.Transparency = 1
end

-- An invisible, non-physical part that particles and light come from.
local function effectPart(name: string, cframe: CFrame, size: Vector3, parent: Instance): Part
	local part = newShooterPart(name, size, Color3.new(1, 1, 1), parent)
	part.Transparency = 1
	part.CastShadow = false
	part.Massless = true
	part.CFrame = cframe
	return part
end

-- Glow and particles for the higher tiers (Config/ShibaEffects), sized to the model. Added after the model is scaled,
-- so the parts turn with it when it aims.
local function addEffects(model: Model, effect: ShibaEffects.Effect?, height: number)
	if not effect then
		return
	end
	local scale = height / CONFIG.Height
	local box, size = model:GetBoundingBox()
	local body = effectPart("EffectBody", box, size * 1.1, model)
	local feet = effectPart(
		"EffectFeet",
		box - Vector3.new(0, size.Y / 2 - 0.1, 0),
		Vector3.new(size.X * 1.1, 0.2, size.Z * 1.1),
		model
	)
	local light = effect.Light
	if light then
		local pointLight = Instance.new("PointLight")
		pointLight.Color = light.Color
		pointLight.Brightness = light.Brightness
		pointLight.Range = light.Range * scale
		pointLight.Shadows = false
		pointLight.Parent = body
	end
	for _, particles in effect.Particles do
		local emitter = Instance.new("ParticleEmitter")
		emitter.Texture = ShibaEffects.Textures[particles.Texture]
		local colorKeys = {}
		for index, color in particles.Colors do
			local time = if #particles.Colors == 1 then 0 else (index - 1) / (#particles.Colors - 1)
			table.insert(colorKeys, ColorSequenceKeypoint.new(time, color))
		end
		if #colorKeys == 1 then
			table.insert(colorKeys, ColorSequenceKeypoint.new(1, particles.Colors[1]))
		end
		emitter.Color = ColorSequence.new(colorKeys)
		local particleSize = particles.Size * scale
		emitter.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, particleSize),
			NumberSequenceKeypoint.new(0.6, particleSize),
			NumberSequenceKeypoint.new(1, 0),
		})
		-- Fade in and out instead of popping.
		emitter.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.15, particles.Transparency),
			NumberSequenceKeypoint.new(0.8, particles.Transparency),
			NumberSequenceKeypoint.new(1, 1),
		})
		emitter.Rate = particles.Rate
		emitter.Lifetime = NumberRange.new(particles.Lifetime * 0.7, particles.Lifetime)
		emitter.Speed = NumberRange.new(particles.Speed * scale)
		emitter.SpreadAngle = Vector2.new(180, 180)
		emitter.Acceleration = Vector3.new(0, particles.Rise * scale, 0)
		emitter.LightEmission = particles.LightEmission
		emitter.Rotation = NumberRange.new(0, 360)
		emitter.RotSpeed = NumberRange.new(-40, 40)
		emitter.Parent = if particles.Area == "Feet" then feet else body
	end
end

-- Shiny / Mythic edition look (Config/ShibaEffects → Editions): an outline and a light aura in the tier's `color`,
-- on top of the base model's own effects.
local function addEditionLook(model: Model, look: ShibaEffects.EditionLook, color: Color3, height: number)
	local outline = Instance.new("Highlight")
	outline.Name = ShibaEffects.EditionOutlineName
	outline.FillColor = color
	outline.FillTransparency = look.FillTransparency
	outline.OutlineColor = color
	outline.OutlineTransparency = look.OutlineTransparency
	outline.DepthMode = Enum.HighlightDepthMode.Occluded
	outline.Parent = model
	local particles: { ShibaEffects.Particles } = {}
	for _, entry in look.Particles do
		local copy = table.clone(entry)
		if #copy.Colors == 0 then
			copy.Colors = { color, color:Lerp(Color3.new(1, 1, 1), 0.6) }
		end
		table.insert(particles, copy)
	end
	local light = look.Light
	addEffects(model, {
		Light = if light then { Color = color, Brightness = light.Brightness, Range = light.Range } else nil,
		Particles = particles,
	}, height)
end

-- ===== Shiba Variants: the slot's look (Config/ShibaEffects → Variants) on top of the tier's own effects. The outline
-- shares the edition outlines' name (and so their Highlight budget on the client); the model carries the attribute
-- ShibaEffects.VariantAttribute, and clients cycle the colours of Rainbow / Huge (ShibaController).
local function addVariantLook(model: Model, variant: string, height: number)
	local look = ShibaEffects.Variants[variant]
	if not look then
		return
	end
	model:SetAttribute(ShibaEffects.VariantAttribute, variant)
	-- Replaces a placeholder outline: a model shows one Highlight.
	for _, child in model:GetChildren() do
		if child:IsA("Highlight") then
			child:Destroy()
		end
	end
	local outline = Instance.new("Highlight")
	outline.Name = ShibaEffects.EditionOutlineName
	outline.FillColor = look.FillColor
	outline.FillTransparency = look.FillTransparency
	outline.OutlineColor = look.OutlineColor
	outline.OutlineTransparency = look.OutlineTransparency
	outline.DepthMode = Enum.HighlightDepthMode.Occluded
	outline.Parent = model
	local particles: { ShibaEffects.Particles } = {}
	for _, entry in look.Particles do
		local copy = table.clone(entry)
		if #copy.Colors == 0 then
			copy.Colors = { look.OutlineColor, look.OutlineColor:Lerp(Color3.new(1, 1, 1), 0.6) }
		end
		table.insert(particles, copy)
	end
	addEffects(model, { Light = look.Light, Particles = particles }, height)
end

-- Huge: a glowing neon ring on the platform, around the Shiba's feet (clients cycle its colour).
local function addVariantRing(variant: string, ground: Vector3, height: number, parent: Instance)
	local look = ShibaEffects.Variants[variant]
	if not (look and look.PlatformRing) then
		return
	end
	local diameter = math.max(4, height * 0.7)
	local ring =
		newShooterPart(ShibaEffects.VariantRingName, Vector3.new(0.3, diameter, diameter), look.OutlineColor, parent)
	ring.Shape = Enum.PartType.Cylinder
	ring.Material = Enum.Material.Neon
	ring.Transparency = 0.35
	ring.CastShadow = false
	ring.CFrame = CFrame.new(ground + Vector3.new(0, 0.1, 0)) * CFrame.Angles(0, 0, math.rad(90))
end
-- ===== end Shiba Variants

-- Builds the platform's pieces around `frame` (on the island surface, facing the island centre).
local function buildPlatform(platform: ShibaPlatforms.Platform, frame: CFrame, parent: Instance)
	local folder = Instance.new("Model")
	folder.Name = "Platform"
	for index, piece in platform.Pieces do
		local cframe = frame * CFrame.new(piece.Offset) * CFrame.Angles(0, math.rad(piece.Yaw or 0), 0)
		local size = piece.Size
		local part = newShooterPart(`Piece{index}`, size, piece.Color, folder)
		if piece.Shape == "Cylinder" then
			-- A cylinder's axis is its X axis, so lay the height along X and stand it up.
			part.Shape = Enum.PartType.Cylinder
			part.Size = Vector3.new(size.Y, size.X, size.X)
			cframe *= CFrame.Angles(0, 0, math.rad(90))
		elseif piece.Shape == "Ball" then
			part.Shape = Enum.PartType.Ball
			part.Size = Vector3.new(size.X, size.X, size.X)
		end
		part.Material = piece.Material
		part.Transparency = piece.Transparency or 0
		part.CFrame = cframe
	end
	folder.Parent = parent
end

-- Places a Platform_<AssetName> model (Config/ShibaPlatforms) instead of the parts: scaled so its StandPoint marker
-- (else its top) ends `top` above the island surface and its bottom ModelSink below it, the marker right above the
-- surface point. Visual only, like the parts (the barrier keeps players out).
local function placePlatformModel(asset: Model, top: number, frame: CFrame, parent: Instance)
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
end

-- Invisible wall around platform and Shiba, so players can't walk through it. Only characters collide with it:
-- no touches, no spatial queries (hit checks, camera), no shadow.
local function buildBarrier(
	platform: ShibaPlatforms.Platform,
	top: number,
	surface: Vector3,
	height: number,
	parent: Instance
)
	local diameter = platform.Diameter + 2 * CONFIG.Barrier.Padding
	-- From a little under the surface (no gap to squeeze through) up past the Shiba's head.
	local sink = CONFIG.Barrier.Sink
	local tall = sink + top + height + CONFIG.Barrier.ExtraHeight
	local barrier = newShooterPart("Barrier", Vector3.new(tall, diameter, diameter), Color3.new(1, 1, 1), parent)
	barrier.Shape = Enum.PartType.Cylinder
	barrier.Transparency = 1
	barrier.CastShadow = false
	barrier.CanCollide = true
	barrier.CFrame = CFrame.new(surface + Vector3.new(0, tall / 2 - sink, 0)) * CFrame.Angles(0, 0, math.rad(90))
end

local function buildShooter(
	parent: Instance,
	center: Vector3,
	angle: number,
	tier: number,
	projectileLevel: number,
	variant: string
): Shooter
	local def = CONFIG.Tiers[tier + 1]
	-- Shiba Variants: a Huge Shiba is HugeScale times taller (its throw point and barrier follow the height).
	local sizeScale = if variant == "Huge" then EconomyConfig.Variants.HugeScale else 1
	local height = (if def then def.Height else CONFIG.Height) * sizeScale
	local platform = (if def then ShibaPlatforms.Platforms[def.AssetName] else nil) or ShibaPlatforms.Default
	local platformModel = if def then Assets.CloneModel(`{ShibaPlatforms.ModelPrefix}{def.AssetName}`) else nil
	local top = if platformModel then platform.ModelTop or platform.Top else platform.Top
	-- Angle 0 is north (−Z), then clockwise. The Shiba stands on top of its platform, which ends at least
	-- PlatformLift above the island surface (equal heights flicker).
	local surface = center + Vector3.new(math.sin(angle), 0, -math.cos(angle)) * CONFIG.RingRadius
	local ground = surface + Vector3.new(0, math.max(CONFIG.PlatformLift, top), 0)

	local model = Instance.new("Model")
	local asset, isOwnModel = cloneTierModel(tier)
	local editionLook = if def and def.Edition then ShibaEffects.Editions[def.Edition] else nil
	local shooter: Shooter
	if asset and not isOwnModel and tier > 0 and not editionLook then
		-- Placeholder look until the tier has its own model: an outline in the tier colour.
		local outline = Instance.new("Highlight")
		outline.FillTransparency = 0.75
		outline.FillColor = CONFIG.Tiers[tier + 1].Color
		outline.OutlineColor = CONFIG.Tiers[tier + 1].Color
		outline.Parent = asset
	end
	if asset then
		-- Clients pose the whole model every frame: it has to arrive (and leave) in one piece.
		asset.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
		Assets.ScaleTo(asset, height, true)
		Assets.MakeVisualOnly(asset, true)
		local box, size = asset:GetBoundingBox()
		local pivotHeight = asset:GetPivot().Position.Y - (box.Position.Y - size.Y / 2)
		addEffects(asset, if def then ShibaEffects.Effects[def.AssetName] else nil, height)
		-- Shiny / Mythic editions: the base model with an outline and aura in the tier colour.
		if def and editionLook then
			addEditionLook(asset, editionLook, def.Color, height)
		end
		-- Shiba Variants: Shiny / Rainbow / Huge look of this slot.
		addVariantLook(asset, variant, height)
		-- Markers only tell the client where the throwing arm turns and what the orbit spins around.
		hideMarker(asset, CONFIG.Throw.ShoulderName)
		hideMarker(asset, MOTION.OrbitCenterName)
		-- An invisible part at the pivot (and the model's PrimaryPart): clients read the rest pose from its CFrame,
		-- which replicates reliably (unlike a Model's WorldPivot).
		asset.PrimaryPart = effectPart(MOTION.PivotName, asset:GetPivot(), Vector3.one * 0.2, asset)
		asset:PivotTo(pivotFrame(ground, pivotHeight, center))
		asset:SetAttribute(MOTION.AimYawAttribute, aimYaw(ground, center))
		-- After the model is scaled and placed, so the paw is measured where it really is.
		equipHandProjectile(asset, projectileLevel)
		local muzzle = asset:FindFirstChild(CONFIG.MuzzleName, true)
		shooter = {
			Model = model,
			Visual = asset,
			Ground = ground,
			Height = height,
			PivotHeight = pivotHeight,
			MuzzleOffset = if muzzle and muzzle:IsA("Attachment")
				then asset:GetPivot():PointToObjectSpace(muzzle.WorldPosition)
				else nil,
			NextFireAt = 0,
			Variant = variant,
		}
		asset.Parent = model
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
			Height = CONFIG.Height,
			Body = body,
			Barrel = barrel,
			NextFireAt = 0,
			Variant = variant,
		}
		faceTarget(shooter, center)
	end
	model.Name = "Shooter"

	local platformFrame = CFrame.lookAt(surface, Vector3.new(center.X, surface.Y, center.Z))
	if platformModel then
		placePlatformModel(platformModel, top, platformFrame, model)
	else
		buildPlatform(platform, platformFrame, model)
	end
	buildBarrier(platform, top, surface, shooter.Height, model)
	addVariantRing(variant, ground, shooter.Height, model)

	model.Parent = parent
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

-- Keeps the ring in sync with the active-shooter count, the tiers and the fire interval. Returns the player's ring.
local function syncRing(player: Player, island: IslandService.Island, now: number): Ring
	local wanted = UpgradeService.GetActiveShooters(player)
	-- Tier interval, fire-rate boost and StickStorm, held to the stick density cap. The shooters take turns, so each
	-- one throws every `wanted` / throws-per-second seconds.
	local throwsPerSecond, valueMultiplier = UpgradeService.GetThrowRate(player)
	local interval = if throwsPerSecond > 0 then wanted / throwsPerSecond else math.huge
	local tier = UpgradeService.GetLevel(player, "ShooterTier")
	local projectileTier = UpgradeService.GetLevel(player, "ProjectileTier")
	local ring = rings[player]
	-- Shiba Variants: shooter n is ring slot n; a slot whose variant changed rebuilds the ring (rare: purchases/admin).
	local variantsMatch = ring ~= nil
	if ring then
		for index, shooter in ring.Shooters do
			if shooter.Variant ~= VariantService.GetVariant(player, index) then
				variantsMatch = false
				break
			end
		end
	end
	if
		ring
		and variantsMatch
		and #ring.Shooters == wanted
		and ring.Tier == tier
		and ring.ProjectileTier == projectileTier
	then
		ring.ValueMultiplier = valueMultiplier
		-- Tolerance: the interval is recomputed from a division every frame.
		if math.abs(ring.Interval - interval) > 1e-6 then
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
	local rebuilt: Ring = {
		Shooters = {},
		Interval = interval,
		ValueMultiplier = valueMultiplier,
		Tier = tier,
		ProjectileTier = projectileTier,
	}
	for index = 1, wanted do
		-- Evenly spaced, with the bridge side (HubAngle) exactly between two shooters.
		local angle = island.HubAngle + (index - 0.5) / wanted * 2 * math.pi
		local variant = VariantService.GetVariant(player, index)
		table.insert(
			rebuilt.Shooters,
			buildShooter(island.ShooterFolder, island.Center, angle, tier, projectileTier, variant)
		)
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

	-- No character (dead or respawning) or away from the island (on the hub): shooters wait.
	local root = getRoot(player)
	if not root then
		return
	end
	local offset = root.Position - island.Center
	if Vector3.new(offset.X, 0, offset.Z).Magnitude > ISLAND.ActiveDistance then
		for _, shooter in ring.Shooters do
			shooter.Plan = nil
			shooter.NextFireAt = math.max(shooter.NextFireAt, now + CONFIG.FirstShotDelay)
		end
		return
	end

	for _, shooter in ring.Shooters do
		if not shooter.Plan and now >= shooter.NextFireAt - CONFIG.AimTime then
			local plan = findShot(player, shooter, island.Center, root.Position)
			shooter.Plan = plan
			if not plan then
				-- Nowhere safe to throw right now: skip this turn.
				shooter.NextFireAt += ring.Interval
			elseif shooter.Visual then
				-- Clients swing the throwing arm toward this moment (Controllers/ShibaController).
				local releaseIn = math.max(0, shooter.NextFireAt - now)
				shooter.Visual:SetAttribute(CONFIG.Throw.ThrowAtAttribute, Workspace:GetServerTimeNow() + releaseIn)
			end
		end
		local plan = shooter.Plan
		if plan and now >= shooter.NextFireAt then
			-- The player may have moved during the aim time: re-check the anti-farm rule.
			if not isSafeFromStandingPlayer(plan, root.Position) then
				plan = findShot(player, shooter, island.Center, root.Position)
			end
			if plan then
				-- Density cap: this stick stands for ValueMultiplier throws (read at release, so a boost or event
				-- that starts during the aim counts right away).
				-- Shiba Variants: × the throwing slot's variant multiplier (Shiny 1.5, Rainbow 3, Huge 6), so every
				-- payout of this stick (bonk, basket, intern, magnet) gets it through GetStickValue.
				plan.VariantMultiplier = EconomyConfig.Variants.Multiplier[shooter.Variant] or 1
				plan.ValueMultiplier = ring.ValueMultiplier * plan.VariantMultiplier
				-- Clients hide what is in the paw at the release themselves (ShibaController, from ThrowAt).
				ProjectileService.Fire(player, plan)
			elseif shooter.Visual then
				-- No safe shot after all: don't let clients swing the arm for a throw that never happens.
				shooter.Visual:SetAttribute(CONFIG.Throw.ThrowAtAttribute, nil)
			end
			shooter.Plan = nil
			-- Keep the turn order even if a frame was late.
			repeat
				shooter.NextFireAt += ring.Interval
			until shooter.NextFireAt > now
		end
	end
end

-- Admin testing tool: every shooter of this player fires as soon as it has aimed.
function NPCShooterService.FireNow(player: Player)
	local ring = rings[player]
	if not ring then
		return
	end
	local now = os.clock()
	for index, shooter in ring.Shooters do
		shooter.Plan = nil
		shooter.NextFireAt = now + CONFIG.AimTime + (index - 1) * 0.15
	end
end

function NPCShooterService.Start()
	-- Tells whoever playtests which custom models are in place (docs: assets/README.md).
	local modelNames: { string } = {}
	for _, tier in CONFIG.Tiers do
		table.insert(modelNames, tier.AssetName)
		table.insert(modelNames, `{ShibaPlatforms.ModelPrefix}{tier.AssetName}`)
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
