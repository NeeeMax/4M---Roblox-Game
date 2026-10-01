--!strict
-- Things that appear on a plot after it was loaded pop in instead of just being there: decor props, the Shiba with its platform
-- and the Bonk Intern. The server (World/StreetPlot) marks such a model with the attribute SpawnedAt (server time); this
-- controller scales it from almost nothing to full size with a little overshoot, growing from the model's own bottom centre,
-- the same way for every model. While it runs the model has the attribute Spawning (the swing animation and the Intern's
-- ducking wait for it). Models that were there when the plot loaded have no SpawnedAt and just stand there. Purely visual.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local ISLAND = Gameplay.Island
-- Seconds of the pop, the size it starts at, and how far it overshoots (see easeOutBack).
local DURATION = 0.55
local START_SCALE = 0.03
local OVERSHOOT = 1.9
-- A model marked longer ago than this (it streamed in late) just appears.
local MAX_AGE = 3
-- Seconds to wait before the pop, so the parts of the model have arrived.
local ARRIVAL_WAIT = 0.06

local played: { [Instance]: boolean } = setmetatable({}, { __mode = "k" }) :: any

local SpawnController = {}

-- 0 -> 1 with a short overshoot past 1 and a settle back.
local function easeOutBack(t: number): number
	local c3 = OVERSHOOT + 1
	return 1 + c3 * (t - 1) ^ 3 + OVERSHOOT * (t - 1) ^ 2
end

local function play(model: Model)
	if not model.Parent then
		return
	end
	local base = model:GetScale()
	local box, size = model:GetBoundingBox()
	-- Scale around the middle of the model's underside.
	model.WorldPivot = CFrame.new(box.Position.X, box.Position.Y - size.Y / 2, box.Position.Z)
	model:SetAttribute("Spawning", true)
	model:ScaleTo(base * START_SCALE)
	local started = os.clock()
	local connection: RBXScriptConnection? = nil
	connection = RunService.RenderStepped:Connect(function()
		if not model.Parent then
			if connection then
				connection:Disconnect()
			end
			return
		end
		local alpha = math.min((os.clock() - started) / DURATION, 1)
		if alpha >= 1 then
			model:ScaleTo(base)
			model:SetAttribute("Spawning", nil)
			if connection then
				connection:Disconnect()
			end
			return
		end
		model:ScaleTo(base * math.max(easeOutBack(alpha), START_SCALE))
	end)
end

local function consider(model: Model)
	if played[model] then
		return
	end
	local at = model:GetAttribute("SpawnedAt")
	if typeof(at) ~= "number" then
		return
	end
	played[model] = true
	if Workspace:GetServerTimeNow() - at > MAX_AGE then
		return
	end
	task.delay(ARRIVAL_WAIT, play, model)
end

local function watch(instance: Instance)
	if not instance:IsA("Model") then
		return
	end
	consider(instance)
	instance:GetAttributeChangedSignal("SpawnedAt"):Connect(function()
		consider(instance)
	end)
end

function SpawnController.Start()
	task.spawn(function()
		local islands = Workspace:WaitForChild(ISLAND.FolderName)
		islands.DescendantAdded:Connect(watch)
		for _, descendant in islands:GetDescendants() do
			watch(descendant)
		end
	end)
end

return SpawnController
