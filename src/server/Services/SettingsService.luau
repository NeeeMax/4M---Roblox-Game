--!strict
-- Saves the settings menu (Net.SaveSettings → state.Settings). Look and sound only, but still validated:
-- music and effects must be numbers 0..1, hints a boolean; a few saves per second at most.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)

local DataService = require(script.Parent.DataService)

-- The client saves at most once per change (debounced), so this only stops spam.
local saveLimiter = RateLimiter.New(5, 3)

local SettingsService = {}

local function isVolume(value: unknown): boolean
	-- value == value rules out NaN.
	return typeof(value) == "number" and value == value and value >= 0 and value <= 1
end

local function onSave(player: Player, music: unknown, effects: unknown, hints: unknown)
	if not RateLimiter.Allow(saveLimiter, player) then
		return
	end
	if not isVolume(music) or not isVolume(effects) or typeof(hints) ~= "boolean" then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Settings = {
		Music = music :: number,
		Effects = effects :: number,
		Hints = hints :: boolean,
	}
	DataService.Replicate(player)
end

function SettingsService.Start()
	Net.Get(Net.SaveSettings).OnServerEvent:Connect(onSave)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(saveLimiter, player)
	end)
end

return SettingsService
