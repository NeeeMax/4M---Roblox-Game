--!strict
-- Friend Boost + invites on the client (docs/GAME_DESIGN.md → Friends and invites): remembers the Friend Boost the
-- server sends (FriendBoostChanged) for the HUD pill, and opens Roblox's invite dialog for the INVITE menu entry.
-- The invite reward itself is decided on the server (SocialService, via the invited player's join data).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SocialService = game:GetService("SocialService")

local Net = require(ReplicatedStorage.Shared.Net)

local INVITE_MESSAGE = "Come bonk with me! Friends on the same server earn more."

local player = Players.LocalPlayer
local friends = 0
local multiplier = 1
local changed = Instance.new("BindableEvent")
local prompting = false

local SocialController = {}

-- Fires after the Friend Boost changed.
SocialController.Changed = changed.Event

-- Friends in the server that count for the boost, and the income multiplier.
function SocialController.GetBoost(): (number, number)
	return friends, multiplier
end

-- Opens Roblox's invite dialog. Returns false and a message for the player when inviting is not possible here
-- (Studio, privacy settings, …).
function SocialController.PromptInvite(): (boolean, string?)
	if prompting then
		return true, nil
	end
	prompting = true
	local ok, canSend = pcall(function()
		return SocialService:CanSendGameInviteAsync(player)
	end)
	if not ok or not canSend then
		prompting = false
		return false, "Invites are not available here (Studio or your privacy settings)."
	end
	local options = Instance.new("ExperienceInviteOptions")
	options.PromptMessage = INVITE_MESSAGE
	local shown, message = pcall(function()
		SocialService:PromptGameInvite(player, options)
	end)
	prompting = false
	if not shown then
		warn(`[SocialController] PromptGameInvite failed: {message}`)
		return false, "Could not open the invite dialog."
	end
	return true, nil
end

function SocialController.Start()
	Net.Get(Net.FriendBoostChanged).OnClientEvent:Connect(function(count: unknown, value: unknown)
		if typeof(count) ~= "number" or typeof(value) ~= "number" then
			return
		end
		friends = count
		multiplier = value
		changed:Fire()
	end)
end

return SocialController
