--!strict
-- Street mode: hold Left Shift to sprint (Config/Gameplay → Character: StreetWalkSpeed, StreetSprintSpeed). The server sets the
-- walking speed when the character spawns (UpgradeService.applyMovement); this controller raises it while Shift is held and
-- moving, and puts it back afterwards. Off outside the street mode; there is no sprint key on touch screens.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Features = require(ReplicatedStorage.Shared.Config.Features)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local STREET_MODE = Features.Tycoon and Features.Street
local CHARACTER = Gameplay.Character

local player = Players.LocalPlayer

local SprintController = {}

local function sprinting(humanoid: Humanoid): boolean
	return UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) and humanoid.MoveDirection.Magnitude > 0.1
end

function SprintController.Start()
	if not STREET_MODE then
		return
	end
	RunService.Heartbeat:Connect(function()
		local character = player.Character
		local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
		if not humanoid or humanoid.Health <= 0 then
			return
		end
		local target = if sprinting(humanoid) then CHARACTER.StreetSprintSpeed else CHARACTER.StreetWalkSpeed
		if humanoid.WalkSpeed ~= target then
			humanoid.WalkSpeed = target
		end
	end)
end

return SprintController
