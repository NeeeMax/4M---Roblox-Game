--!strict
-- The latest copy of this player's saved state, as sent by the server (StateChanged). Menus read it and redraw on
-- Changed. Started by HudController; shows nothing the server didn't send.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = require(ReplicatedStorage.Shared.Net)
local Types = require(ReplicatedStorage.Shared.Types)

local changed = Instance.new("BindableEvent")
local current: Types.PlayerState? = nil
local started = false

local State = {
	Changed = changed.Event,
}

function State.Get(): Types.PlayerState?
	return current
end

-- Connects to StateChanged once (safe to call from several controllers).
function State.Start()
	if started then
		return
	end
	started = true
	Net.Get(Net.StateChanged).OnClientEvent:Connect(function(state: Types.PlayerState)
		current = state
		changed:Fire()
	end)
end

return State
