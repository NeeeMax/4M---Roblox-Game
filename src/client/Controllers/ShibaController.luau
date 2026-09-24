--!strict
-- Shiba poses on this client, in one pass per frame for every shooter model (the models in Workspace.Islands that
-- carry the attribute Gameplay.Shooters.Motion.AimYawAttribute):
-- - Turning: the server only publishes the yaw a Shiba should face; the model turns there smoothly.
-- - Floating and orbit spin, for models whose Config/ShibaEffects entry (keyed by the model's name) asks for it.
-- - Throw animation: the server sets the release time (attribute Shooters.Throw.ThrowAtAttribute, server clock); the
--   throwing arm with what is in the paw turns around the shoulder: back during the aim time, a fast swing forward at
--   the release, then back to rest. Only models with a ThrowArm part and a Shoulder marker swing (assets/README.md).
-- The server places each model once and never moves it, so every pose is computed from that rest pivot, and parts
-- that stream in later are fitted into the current pose. Purely visual, nothing is sent back.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local ShibaEffects = require(ReplicatedStorage.Shared.Config.ShibaEffects)

local ISLAND = Gameplay.Island
local SHOOTERS = Gameplay.Shooters
local THROW = SHOOTERS.Throw
local MOTION = SHOOTERS.Motion
local HAND_NAME = SHOOTERS.HandProjectile.Name
-- Below this many radians off its target yaw a Shiba just snaps the rest of the way.
local SETTLED_YAW = 1e-3
local FULL_TURN = 2 * math.pi

type Rig = {
	-- Where the server put the model; every offset below is relative to it.
	RestPivot: CFrame,
	RestYaw: number,
	-- Yaw currently shown, and the pivot currently shown.
	Yaw: number,
	Shown: CFrame,
	-- Every part of the model and its offset from RestPivot.
	Parts: { [BasePart]: CFrame },
	-- Parts that swing with the throwing arm (ThrowArm, Stick, hand projectile).
	Swing: { [BasePart]: boolean },
	HasArm: boolean,
	Shoulder: Vector3?,
	Orbit: BasePart?,
	OrbitCenter: Vector3?,
	Effect: ShibaEffects.Effect?,
	-- 0…1: where in its float cycle this Shiba starts, so a ring doesn't bob in sync.
	Phase: number,
	-- True while the pose must be refreshed even if nothing moves (the arm is away from rest, or a new rig).
	Posed: boolean,
}

local rigs: { [Model]: Rig } = {}

local ShibaController = {}

local function yawOf(frame: CFrame): number
	local look = frame.LookVector
	return math.atan2(-look.X, -look.Z)
end

-- Shortest signed angle from 0 to `angle`, in -π … π.
local function wrapAngle(angle: number): number
	return (angle + math.pi) % FULL_TURN - math.pi
end

local function isInHand(model: Model, part: BasePart): boolean
	local hand = model:FindFirstChild(HAND_NAME)
	return hand ~= nil and part:IsDescendantOf(hand)
end

-- Adds a part to the rig. It is where the server put it, so it is moved into the pose currently shown.
local function addPart(model: Model, rig: Rig, part: BasePart)
	local offset = rig.RestPivot:ToObjectSpace(part.CFrame)
	rig.Parts[part] = offset
	local name = part.Name
	if name == THROW.ThrowArmName then
		rig.HasArm = true
		rig.Swing[part] = true
	elseif name == SHOOTERS.HandStickName or isInHand(model, part) then
		rig.Swing[part] = true
	elseif name == THROW.ShoulderName then
		rig.Shoulder = offset.Position
	elseif name == MOTION.OrbitName then
		rig.Orbit = part
	elseif name == MOTION.OrbitCenterName then
		rig.OrbitCenter = offset.Position
	end
	if rig.Shown ~= rig.RestPivot then
		part.CFrame = rig.Shown * offset
	end
end

local function tryRig(model: Model)
	if rigs[model] or not model.Parent or model:GetAttribute(MOTION.AimYawAttribute) == nil then
		return
	end
	-- The rest pose comes from the pivot part; until it has arrived, wait (onDescendantAdded tries again).
	local pivotPart = model:FindFirstChild(MOTION.PivotName)
	if not (pivotPart and pivotPart:IsA("BasePart")) then
		return
	end
	local restPivot = pivotPart.CFrame
	local restYaw = yawOf(restPivot)
	local aimYaw = model:GetAttribute(MOTION.AimYawAttribute)
	local rig: Rig = {
		RestPivot = restPivot,
		RestYaw = restYaw,
		-- A client joining mid-game shows the current aim right away.
		Yaw = if typeof(aimYaw) == "number" then aimYaw else restYaw,
		Shown = restPivot,
		Parts = {},
		Swing = {},
		HasArm = false,
		Effect = ShibaEffects.Effects[model.Name],
		Phase = restYaw / FULL_TURN,
		-- Pose it on the first frame (it may already have to face elsewhere).
		Posed = true,
	}
	rigs[model] = rig
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			addPart(model, rig, descendant)
		end
	end
end

local function onDescendantAdded(descendant: Instance)
	if descendant:IsA("Model") then
		if descendant:GetAttribute(MOTION.AimYawAttribute) ~= nil then
			-- Let the rest of the model arrive first (anything later is added by the branch below).
			task.defer(tryRig, descendant)
		end
		return
	end
	if not descendant:IsA("BasePart") then
		return
	end
	local parent = descendant.Parent
	if descendant.Name == MOTION.PivotName and parent and parent:IsA("Model") then
		task.defer(tryRig, parent)
		return
	end
	-- A part streaming into a model that is already posed.
	local ancestor = descendant.Parent
	while ancestor and ancestor ~= Workspace do
		if ancestor:IsA("Model") then
			local rig = rigs[ancestor]
			if rig then
				addPart(ancestor, rig, descendant)
				return
			end
		end
		ancestor = ancestor.Parent
	end
end

local function easeOut(k: number): number
	return 1 - (1 - k) * (1 - k)
end

-- Arm angle in degrees at `t` seconds after the release (negative t: still aiming). Positive swings forward.
local function swingAngle(t: number): number
	local aim = SHOOTERS.AimTime
	if t < -aim or t >= THROW.SwingTime + THROW.ReturnTime then
		return 0
	end
	if t < 0 then
		return -THROW.WindupDegrees * easeOut((t + aim) / aim)
	end
	if t < THROW.SwingTime then
		local k = t / THROW.SwingTime
		return -THROW.WindupDegrees + (THROW.WindupDegrees + THROW.ReleaseDegrees) * k * k
	end
	local k = (t - THROW.SwingTime) / THROW.ReturnTime
	return THROW.ReleaseDegrees * (1 - k * k * (3 - 2 * k))
end

-- Rotation by `angle` radians about `axis` through `point` (all in world space).
local function turnAround(point: Vector3, axis: Vector3, angle: number): CFrame
	return CFrame.new(point) * CFrame.fromAxisAngle(axis, angle) * CFrame.new(-point)
end

-- Turns the rig toward its target yaw. Returns true if it moved.
local function turnToward(model: Model, rig: Rig, dt: number): boolean
	local target = model:GetAttribute(MOTION.AimYawAttribute)
	if typeof(target) ~= "number" then
		return false
	end
	local difference = wrapAngle(target - rig.Yaw)
	if difference == 0 then
		return false
	end
	if math.abs(difference) <= SETTLED_YAW then
		rig.Yaw = target
		return true
	end
	local step = difference * (1 - math.exp(-MOTION.TurnSharpness * dt))
	local maxStep = math.rad(MOTION.MaxTurnDegreesPerSecond) * dt
	rig.Yaw = wrapAngle(rig.Yaw + math.clamp(step, -maxStep, maxStep))
	return true
end

-- Adds this frame's pose of one rig to `parts`/`frames`, if anything about it changed.
local function poseRig(model: Model, rig: Rig, now: number, dt: number, parts: { BasePart }, frames: { CFrame })
	local turned = turnToward(model, rig, dt)
	local effect = rig.Effect
	local float = if effect then effect.Float else nil
	local orbit = if effect and rig.Orbit and rig.OrbitCenter then effect.Orbit else nil
	local throwAt = model:GetAttribute(THROW.ThrowAtAttribute)
	local angle = if rig.HasArm and rig.Shoulder and typeof(throwAt) == "number" then swingAngle(now - throwAt) else 0
	if not (turned or float or orbit or angle ~= 0 or rig.Posed) then
		return
	end
	rig.Posed = angle ~= 0

	local rest = rig.RestPivot
	-- Floats between its platform and Height above it, so it never sinks in.
	local bob = if float then float.Height * (0.5 - 0.5 * math.cos(FULL_TURN * (now / float.Period + rig.Phase))) else 0
	local shown = CFrame.new(rest.Position + Vector3.new(0, bob, 0))
		* CFrame.Angles(0, rig.Yaw - rig.RestYaw, 0)
		* rest.Rotation
	rig.Shown = shown

	local swing = CFrame.identity
	local shoulder = rig.Shoulder
	if angle ~= 0 and shoulder then
		-- About the Shiba's own right axis (it faces its pivot's LookVector).
		swing = turnAround(shown * shoulder, shown.RightVector, math.rad(angle))
	end
	local spin = CFrame.identity
	local orbitCenter = rig.OrbitCenter
	if orbit and orbitCenter then
		local axis = shown:VectorToWorldSpace(if orbit.Axis then orbit.Axis.Unit else Vector3.yAxis)
		spin = turnAround(shown * orbitCenter, axis, math.rad((now * orbit.DegreesPerSecond) % 360))
	end

	for part, offset in rig.Parts do
		if not part.Parent then
			-- Streamed out or removed on its own.
			rig.Parts[part] = nil
			continue
		end
		local frame = shown * offset
		if rig.Swing[part] then
			frame = swing * frame
		elseif part == rig.Orbit then
			frame = spin * frame
		end
		table.insert(parts, part)
		table.insert(frames, frame)
	end
end

local function update(dt: number)
	local now = Workspace:GetServerTimeNow()
	local parts: { BasePart } = {}
	local frames: { CFrame } = {}
	for model, rig in rigs do
		if not model.Parent then
			rigs[model] = nil
			continue
		end
		poseRig(model, rig, now, dt, parts, frames)
	end
	if #parts > 0 then
		Workspace:BulkMoveTo(parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
	end
end

function ShibaController.Start()
	RunService:BindToRenderStep("PoseShibas", Enum.RenderPriority.Camera.Value + 2, update)
	task.spawn(function()
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		islands.DescendantAdded:Connect(onDescendantAdded)
		for _, descendant in islands:GetDescendants() do
			onDescendantAdded(descendant)
		end
	end)
end

return ShibaController
