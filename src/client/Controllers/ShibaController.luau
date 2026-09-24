--!strict
-- Throw animation: swings every Shiba's throwing arm (and the stick in its paw) on this client. The server only
-- sets the release time on the shooter model (attribute Gameplay.Shooters.Throw.ThrowAtAttribute, server clock);
-- this controller turns the arm around the shoulder every frame: back during the aim time, a fast swing forward
-- when the stick leaves the paw, then back to rest. Only models with a ThrowArm part and a Shoulder marker are
-- animated (see assets/README.md). Purely visual, nothing is sent back.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local ISLAND = Gameplay.Island
local SHOOTERS = Gameplay.Shooters
local THROW = SHOOTERS.Throw

type Rig = {
	Arm: BasePart,
	Body: BasePart,
	Stick: BasePart?,
	-- Rest pose relative to the body, taken before any swing.
	ArmOffset: CFrame,
	StickOffset: CFrame?,
	ShoulderOffset: Vector3,
	-- True while the arm is away from its rest pose.
	Posed: boolean,
}

local rigs: { [Model]: Rig } = {}

local ShibaController = {}

local function findPart(model: Model, name: string): BasePart?
	local found = model:FindFirstChild(name, true)
	return if found and found:IsA("BasePart") then found else nil
end

local function tryRig(model: Model)
	if rigs[model] then
		return
	end
	local arm = findPart(model, THROW.ThrowArmName)
	local shoulder = findPart(model, THROW.ShoulderName)
	local body = findPart(model, "Body")
	if not (arm and shoulder and body) then
		return
	end
	local stick = findPart(model, SHOOTERS.HandStickName)
	local bodyFrame = body.CFrame
	rigs[model] = {
		Arm = arm,
		Body = body,
		Stick = stick,
		ArmOffset = bodyFrame:ToObjectSpace(arm.CFrame),
		StickOffset = if stick then bodyFrame:ToObjectSpace(stick.CFrame) else nil,
		ShoulderOffset = bodyFrame:PointToObjectSpace(shoulder.Position),
		Posed = false,
	}
end

local function onDescendantAdded(descendant: Instance)
	local name = descendant.Name
	if name ~= THROW.ThrowArmName and name ~= THROW.ShoulderName and name ~= "Body" then
		return
	end
	local model = descendant.Parent
	if model and model:IsA("Model") then
		tryRig(model)
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

local function pose(rig: Rig, turn: CFrame)
	local bodyFrame = rig.Body.CFrame
	rig.Arm.CFrame = turn * bodyFrame * rig.ArmOffset
	local stick, stickOffset = rig.Stick, rig.StickOffset
	if stick and stickOffset then
		stick.CFrame = turn * bodyFrame * stickOffset
	end
end

local function update()
	local now = Workspace:GetServerTimeNow()
	for model, rig in rigs do
		if not model.Parent or not rig.Arm.Parent or not rig.Body.Parent then
			rigs[model] = nil
			continue
		end
		local throwAt = model:GetAttribute(THROW.ThrowAtAttribute)
		local angle = if typeof(throwAt) == "number" then swingAngle(now - throwAt) else 0
		if angle == 0 then
			if rig.Posed then
				pose(rig, CFrame.identity)
				rig.Posed = false
			end
			continue
		end
		-- Turn around the shoulder, about the Shiba's own right axis (it faces its pivot's LookVector).
		local shoulder = rig.Body.CFrame:PointToWorldSpace(rig.ShoulderOffset)
		local axis = model:GetPivot().RightVector
		local turn = CFrame.new(shoulder) * CFrame.fromAxisAngle(axis, math.rad(angle)) * CFrame.new(-shoulder)
		pose(rig, turn)
		rig.Posed = true
	end
end

function ShibaController.Start()
	RunService:BindToRenderStep("SwingShibaArms", Enum.RenderPriority.Camera.Value + 2, update)
	task.spawn(function()
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		islands.DescendantAdded:Connect(onDescendantAdded)
		for _, descendant in islands:GetDescendants() do
			onDescendantAdded(descendant)
		end
	end)
end

return ShibaController
