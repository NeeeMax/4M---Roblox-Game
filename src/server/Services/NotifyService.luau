--!strict
-- Short on-screen messages for one player ("Not enough Bonk Points", "Duel declined", …). Shown by HudController.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = require(ReplicatedStorage.Shared.Net)

local notify = Net.Get(Net.Notify)

local NotifyService = {}

function NotifyService.Send(player: Player, message: string, kind: ("Info" | "Good" | "Bad")?)
	notify:FireClient(player, message, kind or "Info")
end

return NotifyService
